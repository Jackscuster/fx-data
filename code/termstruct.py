import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Tasks 4-6. The term structure of efficiency as a second regime dimension.

The four horizons are dimensions of the regime read, not candidates for one slot.
5, 10, 15 and 20 days each describe the shape of a move differently, and two
pairs both reading high at 5 days are in different regimes if one holds that
reading at 20 days and the other does not.

EVERYTHING HERE IS BUILT FROM TRAILING DATA, LAGGED ONE BAR, and that is not a
stylistic choice. ACTIONABLE.md defines persistence as reading(20d)/reading(5d)
where the readings are forward efficiency -- which is the target. Built that way
it scores an OOS effect of 0.2460 at t=190 with all 28 pairs agreeing, roughly
ten times the best genuine survivor in the project. That is the target leaking
into the feature, not a discovery.

A CIRCULAR-SHIFT NULL DOES NOT CATCH THIS, which is the dangerous part. Shifting
the target while holding the feature fixed destroys the leaked alignment, so the
null reads near zero and the real-to-null ratio comes out around 40x -- the null
certifies the leak instead of exposing it. Nulls test for selection inflation.
They do not test for look-ahead. Only construction discipline does that.

So every feature below is computed from realised efficiency over the PAST H days
and shifted one bar, exactly like every other signal in the project.

  TASK 4  the features: levels, persistence, slope, curvature, dispersion,
          cross-horizon agreement -- each scored through the live scorer
  TASK 5  a trend read requiring confluence across N of 4 horizons, swept,
          alone and combined with persistence and with daily/weekly/monthly
  TASK 6  the typical term-structure shape per pair, and whether it persists

All of it null-tested against circularly shifted targets, with corrected effect
sizes reported alongside the raw ones.

Writes results/termstruct_signals.csv, termstruct_null.csv, termstruct_pairs.csv.
"""
import numpy as np, pandas as pd
import sc3
from carrysig import score_panel

PX = os.path.join(ROOTDATA, 'px28.csv')
SPLIT = pd.Timestamp('2016-01-01')
HS = [5, 10, 15, 20]
NSHIFT = int(os.environ.get('FX_NSHIFT', 50))   # project standard is 50
MINOFF = 1000
SEED = 23
MEDWIN = 250
G_T, G_S, G_A, G_M, G_D = 8., .0221, .893, .95, .6


def trail_eff(lp, H):
    """Realised |net| / path over the PAST H days, lagged one bar."""
    net = (lp - lp.shift(H)).abs()
    path = lp.diff().abs().rolling(H).sum()
    return (net / path).replace([np.inf, -np.inf], np.nan).shift(1)


def fwd_eff(lp, H):
    net = (lp.shift(-H) - lp).abs()
    path = lp.diff().abs().shift(-H).rolling(H).sum()
    return (net / path).replace([np.inf, -np.inf], np.nan)


def tf_eff(px, rule, n):
    """Same construction on weekly or monthly bars, mapped back to daily."""
    s = np.log(px.astype(float)).resample(rule).last()
    net = (s - s.shift(n)).abs()
    path = s.diff().abs().rolling(n).sum()
    e = (net / path).replace([np.inf, -np.inf], np.nan).shift(1)
    return e.reindex(px.index, method='ffill')


def features(px):
    """-> {name: DataFrame(dates x pairs)}. Task 4.1-4.3, all trailing."""
    lp = np.log(px.astype(float))
    E = {H: trail_eff(lp, H) for H in HS}
    F = {}
    for H in HS:
        F['eff_trail_%d' % H] = E[H]

    # 4.1 persistence. The ratio is unstable when the 5-day reading is near
    # zero, so the log and difference forms are carried alongside it.
    with np.errstate(invalid='ignore', divide='ignore'):
        F['persist_ratio'] = (E[20] / E[5]).replace([np.inf, -np.inf], np.nan)
        F['persist_log'] = np.log(E[20].clip(lower=1e-4) / E[5].clip(lower=1e-4))
    F['persist_diff'] = E[20] - E[5]

    # 4.2 slope and curvature across the four horizons
    h = np.array(HS, float)
    hc = h - h.mean()
    stack = np.stack([E[H].values for H in HS])                  # (4, T, P)
    F['ts_slope'] = pd.DataFrame(
        (stack * hc[:, None, None]).sum(0) / (hc ** 2).sum(),
        index=px.index, columns=px.columns)
    F['ts_curve'] = (E[5] + E[20]) / 2 - (E[10] + E[15]) / 2
    mu = pd.DataFrame(stack.mean(0), index=px.index, columns=px.columns)
    sd = pd.DataFrame(stack.std(0), index=px.index, columns=px.columns)
    F['ts_disp'] = sd / mu.replace(0, np.nan)

    # 4.3 cross-horizon agreement: how many horizons sit above their own
    # trailing median. "Direction" for a quantity with no sign means high or low
    # against its own history, which is what the gates read anyway.
    above = [(E[H] > E[H].rolling(MEDWIN).median()).astype(float)
             .where(E[H].notna()) for H in HS]
    F['xh_agree'] = sum(above)                                   # 0..4
    F['xh_ends'] = (above[0] == above[3]).astype(float).where(E[5].notna())

    # the existing multi-timeframe idea, same construction on other bar sizes
    F['mtf_agree'] = (
        (px > 0).astype(float) * 0
        + (trail_eff(lp, 20) > trail_eff(lp, 20).rolling(MEDWIN).median()).astype(float)
        + (tf_eff(px, 'W-FRI', 4) > tf_eff(px, 'W-FRI', 4).rolling(52).median()).astype(float)
        + (tf_eff(px, 'ME', 3) > tf_eff(px, 'ME', 3).rolling(24).median()).astype(float))
    return F


def confluence(F):
    """Task 5. Trend reads requiring agreement across N of 4 horizons."""
    out = {}
    for N in (2, 3, 4):
        out['conf_%dof4' % N] = (F['xh_agree'] >= N).astype(float)
    # persistence as a second condition, on top of full confluence
    pos = F['persist_diff'] > 0
    out['conf_4of4_and_persist'] = ((F['xh_agree'] >= 4) & pos).astype(float)
    out['conf_3of4_and_persist'] = ((F['xh_agree'] >= 3) & pos).astype(float)
    # and with the daily/weekly/monthly filter as a third dimension
    out['conf_3of4_and_mtf'] = ((F['xh_agree'] >= 3) & (F['mtf_agree'] >= 2)).astype(float)
    out['conf_all_three'] = ((F['xh_agree'] >= 3) & pos
                             & (F['mtf_agree'] >= 2)).astype(float)
    return out


def score_binary(name, F, Y, ins):
    """Two-group comparison for the confluence rules.

    A 0/1 rule cannot go through the quintile scorer -- pd.qcut needs five
    distinct values and returns None, which silently dropped every confluence
    feature on the first run. The right test for a rule is the one it implies:
    does forward efficiency differ when it is on, and do the pairs agree.
    """
    out = {}
    for tag, msk in (('i', ins), ('o', ~ins)):
        diffs, on_n, tot = [], 0, 0
        for p in F.columns:
            x = F[p][msk]
            y = Y[p][msk]
            ok = x.notna() & y.notna()
            if ok.sum() < 400:
                continue
            on, off = y[ok & (x > 0)], y[ok & (x == 0)]
            if len(on) < 100 or len(off) < 100:
                continue
            diffs.append(on.mean() - off.mean())
            on_n += len(on); tot += len(on) + len(off)
        if len(diffs) < 20:
            return None
        d = np.array(diffs)
        out[tag] = dict(sp=float(d.mean()), t=float(d.mean() / (d.std(ddof=1) / np.sqrt(len(d)))),
                        agree=float((np.sign(d) == np.sign(d.mean())).mean()),
                        on_rate=on_n / max(tot, 1))
    i, o = out['i'], out['o']
    # The gauntlet does not apply to a two-group rule: monotonicity across five
    # quintiles is undefined when there are two groups, and NaN is truthy, so an
    # earlier version displayed PASS for every confluence rule. Marked explicitly.
    return dict(signal=name, scorable=True, kind='binary', **{'pass': False},
                si=i['sp'], ti=i['t'], ai=i['agree'], mi=np.nan, cti=28,
                so=o['sp'], to=o['t'], ao=o['agree'], mo=np.nan, cto=28,
                on_rate=o['on_rate'],
                dec=abs(o['t']) / max(abs(i['t']), .01),
                held=bool(np.sign(i['sp']) == np.sign(o['sp'])))


def score_all(X, Y, ins):
    rows = []
    for name, F in X.items():
        if F.stack().dropna().nunique() <= 5:          # a rule, not a reading
            r = score_binary(name, F, Y, ins)
            if r is not None:
                rows.append(r)
            continue
        r = score_panel(F, Y, ins)
        if r is None:
            rows.append(dict(signal=name, scorable=False))
            continue
        r.update(signal=name, scorable=True, kind='quintile')
        r['pass'] = bool(np.sign(r['ti']) == np.sign(r['to']) and abs(r['to']) >= G_T
                         and abs(r['si']) >= G_S and r['ao'] >= G_A
                         and abs(r['mo']) >= G_M and r['dec'] >= G_D)
        rows.append(r)
    return pd.DataFrame(rows)


def run_null(X, lp, px, ins, H=20):
    """Circular shift of the target panel; the features are untouched."""
    rng = np.random.default_rng(SEED)
    offs = rng.integers(MINOFF, len(px) - MINOFF, NSHIFT)
    base = fwd_eff(lp, H)
    out = []
    for k, o in enumerate(offs):
        Y = {p: pd.Series(np.roll(base[p].values, int(o)), index=px.index)
             for p in px.columns}
        for name, F in X.items():
            r = (score_binary(name, F, Y, ins)
                 if F.stack().dropna().nunique() <= 5 else score_panel(F, Y, ins))
            if r is None:
                continue
            out.append(dict(signal=name, shift=int(o), si=r['si'], so=r['so'],
                            to=r['to'], ao=r['ao'], mo=r.get('mo')))
        print('  null shift %2d/%d' % (k + 1, NSHIFT), flush=True)
    return pd.DataFrame(out)


def task6(px, F):
    """Do some pairs habitually sustain and others burst, and does it persist?

    On "does normalising by each pair's own typical shape change anything": for
    the FINISHED feature, provably nothing. The scorer ranks the signal within
    each pair before quintiling, so any strictly-monotone per-pair transform
    leaves quintile membership identical and every statistic with it -- scaling
    and z-scoring ts_slope, persist_diff and ts_disp reproduce their effect,
    agreement, monotonicity and t to every digit. Normalising the COMPONENT
    horizons before combining them is a different operation and does change the
    feature, which is exactly what the median division below does.

    The RAW slope cannot answer this. Over a random walk the net move grows like
    sqrt(H) while the path grows like H, so trailing efficiency decays as
    1/sqrt(H) for every series alive -- the first run duly classified all 28
    pairs as "bursts", which is arithmetic, not a property of any pair. Each
    horizon is therefore divided by its OWN in-sample median for that pair before
    the slope is taken, so what is left is how a pair departs from the mechanical
    shape rather than the mechanical shape itself.
    """
    ins = px.index < SPLIT
    h = np.array(HS, float); hc = h - h.mean()
    norm = []
    for H in HS:
        e = F['eff_trail_%d' % H]
        norm.append(e / e[ins].median())
    NS = pd.DataFrame((np.stack([n.values for n in norm]) * hc[:, None, None]).sum(0)
                      / (hc ** 2).sum(), index=px.index, columns=px.columns)
    rows = []
    for p in px.columns:
        s_is = NS[p][ins].mean()
        s_oos = NS[p][~ins].mean()
        rows.append(dict(pair=p, slope_is=s_is, slope_oos=s_oos,
                         e5_is=F['eff_trail_5'][p][ins].mean(),
                         e20_is=F['eff_trail_20'][p][ins].mean(),
                         persist_is=F['persist_diff'][p][ins].mean(),
                         persist_oos=F['persist_diff'][p][~ins].mean(),
                         raw_slope_is=F['ts_slope'][p][ins].mean()))
    P = pd.DataFrame(rows)
    P['shape_is'] = np.where(P.slope_is > 0, 'sustains', 'bursts')
    P['shape_oos'] = np.where(P.slope_oos > 0, 'sustains', 'bursts')
    P['stable'] = P.shape_is == P.shape_oos
    return P


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    lp = np.log(px.astype(float))
    ins = np.asarray(px.index < SPLIT)
    T = sc3.target(px)
    Y = {p: T[p] for p in px.columns}

    F = features(px)
    X = dict(F)
    X.update(confluence(F))
    print('%d term-structure features, all trailing and lagged' % len(X))

    S = score_all(X, Y, ins)
    N = run_null(X, lp, px, ins)
    S.to_csv(os.path.join(ROOTOUT, 'termstruct_signals.csv'), index=False)
    N.to_csv(os.path.join(ROOTOUT, 'termstruct_null.csv'), index=False)
    P = task6(px, F)
    P.to_csv(os.path.join(ROOTOUT, 'termstruct_pairs.csv'), index=False)
    report(S, N, P)
    return S, N, P


def report(S, N, P):
    g = N.groupby('signal').agg(null_eff=('so', lambda x: x.abs().median()),
                                null_eff_p90=('so', lambda x: x.abs().quantile(.9)),
                                null_t=('to', lambda x: x.abs().median()),
                                null_agree=('ao', 'mean')).reset_index()
    M = S[S.scorable == True].merge(g, on='signal', how='left')       # noqa: E712
    M['abs_so'] = M.so.abs()
    M['corrected'] = M.abs_so - M.null_eff
    M['ratio'] = M.abs_so / M.null_eff
    M = M.sort_values('corrected', ascending=False)
    print('\nTASK 4/5 -- TERM-STRUCTURE FEATURES, null-corrected')
    print('%-24s %9s %8s %9s %7s %7s %7s %6s'
          % ('feature', 'OOS eff', 'null', 'corrected', 'ratio', 'agree', '|t|', 'pass'))
    for _, r in M.iterrows():
        print('%-24s %9.4f %8.4f %9.4f %6.2fx %7.3f %7.1f %6s'
              % (r.signal, r.abs_so, r.null_eff, r.corrected, r.ratio, r.ao,
                 abs(r.to), 'YES' if r['pass'] is True else
                 ('n/a' if r.get('kind') == 'binary' else '')))
    print('\ngate reference: effect >= %.4f, agree >= %.3f, |t| >= %.0f'
          % (G_S, G_A, G_T))
    best = M.iloc[0]
    print('strongest corrected effect: %s at %.4f' % (best.signal, best.corrected))
    q = M[M.kind != 'binary']
    print('features clearing the gauntlet: %d of %d readings'
          ' (the %d rules are two-group tests, so the gates do not apply)'
          % (int((q['pass'] == True).sum()), len(q), len(M) - len(q)))     # noqa: E712

    print('\nTASK 6 -- per-pair term-structure shape')
    print('  pairs whose slope sign holds IS to OOS: %d of %d'
          % (int(P.stable.sum()), len(P)))
    rho = float(pd.Series(P.slope_is).corr(pd.Series(P.slope_oos), method='spearman'))
    print('  IS/OOS rank correlation of the slope: %+.3f' % rho)
    print('  IS shapes: %s' % P.shape_is.value_counts().to_dict())
    print(P.sort_values('slope_is', ascending=False)
          [['pair', 'slope_is', 'slope_oos', 'shape_is', 'shape_oos', 'stable']]
          .head(8).to_string(index=False, float_format=lambda v: '%+.6f' % v))
    print('\nwrote termstruct_signals.csv, termstruct_null.csv, termstruct_pairs.csv')


if __name__ == '__main__':
    if '--report-only' in sys.argv:
        report(pd.read_csv(os.path.join(ROOTOUT, 'termstruct_signals.csv')),
               pd.read_csv(os.path.join(ROOTOUT, 'termstruct_null.csv')),
               pd.read_csv(os.path.join(ROOTOUT, 'termstruct_pairs.csv')))
    else:
        main()
