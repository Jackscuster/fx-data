import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Is 20 days the right horizon, or just the first one anybody picked?

Every effect in this project is measured against forward 20-day efficiency
because that was chosen at the start and never justified. Chop is a volatility
phenomenon and volatility clusters over days rather than weeks, so the estimator
may have been measured at the wrong horizon the whole time.

WHAT IS SCORED. The 111 signals that cleared the gauntlet at its old settings
(which contains the current 29 as a subset) plus the 731 that fail exactly one
gate today -- 791 in all. The near-misses are in deliberately: the question "does
anything that fails at 20 days pass at 5" cannot be answered from a population
that already passes at 20.

t-STATISTICS ARE NOT COMPARABLE ACROSS HORIZONS and the temptation to read them
that way is the trap in this whole exercise. A 5-day window over the same sample
holds about four times as many non-overlapping observations as a 20-day window,
so the same true effect produces a larger t purely from having more of them.
Effect size, agreement and monotonicity are scale-free and are the honest
comparison. To put a number on the rest, the null is run at every horizon: the
target panel is circularly shifted, the same signals rescored, and what comes
back is the t a zero effect earns at that horizon.

Writes results/horizon_signals.csv, horizon_summary.csv, horizon_null.csv.
"""
import json, time
import numpy as np, pandas as pd
import sc3
from extsig import split_variant, apply_variant, _frame, MOD
from carrysig import score_panel

PX = os.path.join(ROOTDATA, 'px28.csv')
SIG = os.path.join(ROOTOUT, 'signals.json')
SPLIT = pd.Timestamp('2016-01-01')
HS = [5, 10, 15, 20]
NSHIFT = 20
MINOFF = 1000
SEED = 11
G_T, G_S, G_A, G_M, G_D = 8., .0221, .893, .95, .6


def target_h(px, H):
    """sc3.target with the horizon exposed. Identical at H = sc3.H, asserted below."""
    p = np.log(px.astype(float))
    net = (p.shift(-H) - p).abs()
    path = p.diff().abs().shift(-H).rolling(H).sum()
    return (net / path).replace([np.inf, -np.inf], np.nan)


def candidates():
    """-> DataFrame of the 791, tagged by how they stand at 20 days."""
    D = pd.DataFrame(json.load(open(SIG)))
    d = D[D.ok.fillna(True)].copy()
    with np.errstate(invalid='ignore', divide='ignore'):
        d['dc'] = d.to.abs() / d.ti.abs().clip(lower=.01)
    g = {'sign': np.sign(d.ti) == np.sign(d.to), 't': d.to.abs() >= G_T,
         'eff': d.si.abs() >= G_S, 'agree': d.ao >= G_A,
         'mono': d.mo.abs() >= G_M, 'decay': d.dc >= G_D,
         'tsb': d.tsb.isna() | (d.tsb >= 4)}
    M = pd.DataFrame(g, index=d.index)
    old = M.assign(eff=d.si.abs() >= .02, agree=d.ao >= .85).all(1)
    npass = M.sum(1)
    keep = old | (npass == 6)
    c = d[keep].copy()
    c['surv_new'] = M.all(1)[keep]
    c['surv_old'] = old[keep]
    c['fails'] = [','.join(sorted(M.columns[~M.loc[i]])) for i in c.index]
    return c


def build_and_score(px, cand, Y):
    """Per module: build the 28-pair frames, pull the wanted columns, score.

    Panels are scored and dropped module by module. Holding all 791 at once is
    1.2 GB of float64 for no reason -- only the survivors are kept, because the
    null pass needs them again.
    """
    ins = np.asarray(px.index < SPLIT)
    rows, keep = [], {}
    surv = set(cand[cand.surv_old].s)
    for batch, grp in cand.groupby('b'):
        mod = MOD[batch]
        m = __import__(mod)
        ctx = m.context(px) if hasattr(m, 'context') else None
        want = []
        for _, r in grp.iterrows():
            base, spec = (split_variant(r.s) if mod in ('sig6', 'sig7') else (r.s, None))
            want.append((base, spec, r.s))
        panels = {n: {} for _, _, n in want}
        for pair in px.columns:
            t0 = time.time()
            try:
                F = _frame(m, mod, px, pair, ctx)
            except Exception as e:                   # noqa: BLE001
                print('  %-5s %-7s FAILED %s' % (mod, pair, e))
                continue
            for base, spec, name in want:
                if base in F.columns:
                    panels[name][pair] = apply_variant(
                        F[base].astype(float), spec).shift(1).astype(np.float32)
            del F
            print('  %-5s %-7s %4.0fs' % (mod, pair, time.time() - t0), flush=True)
        for name, cols in panels.items():
            if not cols:
                continue
            X = pd.DataFrame(cols, index=px.index)
            for H in HS:
                r = score_panel(X, Y[H], ins)
                if r is None:
                    continue
                r.update(signal=name, batch=batch, H=H)
                rows.append(r)
            if name in surv:
                keep[name] = X
        del panels
    return pd.DataFrame(rows), keep


def run_null(keep, px, rng):
    """Same signals, target panel circularly shifted. True effect is zero."""
    ins = np.asarray(px.index < SPLIT)
    T = len(px)
    offs = rng.integers(MINOFF, T - MINOFF, NSHIFT)
    out = []
    for H in HS:
        base = target_h(px, H)
        for k, o in enumerate(offs):
            Y = {p: pd.Series(np.roll(base[p].values, int(o)), index=px.index)
                 for p in px.columns}
            for name, X in keep.items():
                r = score_panel(X, Y, ins)
                if r is None:
                    continue
                out.append(dict(H=H, shift=int(o), signal=name,
                                to=r['to'], so=r['so'], ao=r['ao'], mo=r['mo']))
            print('  null H=%2d shift %2d/%d' % (H, k + 1, NSHIFT), flush=True)
    return pd.DataFrame(out)


def report(S, N, cand):
    tag = cand.set_index('s')
    S = S.join(tag[['surv_new', 'surv_old', 'fails']], on='signal')
    S['held'] = np.sign(S.si) == np.sign(S.so)
    S['chop'] = S.so < 0
    S['pass'] = ((np.sign(S.ti) == np.sign(S.to)) & (S.to.abs() >= G_T)
                 & (S.si.abs() >= G_S) & (S.ao >= G_A) & (S.mo.abs() >= G_M)
                 & (S.dec >= G_D))

    print('\nHORIZON SWEEP -- the 111 old survivors')
    O = S[S.surv_old]
    r = (O.groupby('H').agg(n=('signal', 'size'), eff_is=('si', lambda x: x.abs().median()),
                            eff_oos=('so', lambda x: x.abs().median()),
                            t_oos=('to', lambda x: x.abs().median()),
                            agree=('ao', 'mean'), mono=('mo', lambda x: x.abs().mean()),
                            retention=('held', 'mean'), passing=('pass', 'sum'))
         .reset_index())
    print(r.to_string(index=False, formatters={
        'eff_is': '{:.4f}'.format, 'eff_oos': '{:.4f}'.format, 't_oos': '{:.1f}'.format,
        'agree': '{:.3f}'.format, 'mono': '{:.3f}'.format, 'retention': '{:.3f}'.format}))

    print('\nchop signals against the rest (median |OOS effect|)')
    c = (O.groupby(['H', 'chop']).so.apply(lambda x: x.abs().median()).unstack()
         .rename(columns={True: 'chop', False: 'non-chop'}))
    print(c.to_string(float_format=lambda v: '%.4f' % v))

    if len(N):
        print('\nTHE NULL AT EACH HORIZON -- what a zero effect earns')
        n = (N.groupby('H').agg(null_t=('to', lambda x: x.abs().median()),
                                null_t_p90=('to', lambda x: x.abs().quantile(.9)),
                                null_eff=('so', lambda x: x.abs().median()),
                                null_agree=('ao', 'mean')).reset_index())
        n = n.merge(r[['H', 't_oos', 'eff_oos']], on='H')
        n['t_ratio'] = n.t_oos / n.null_t
        n['eff_ratio'] = n.eff_oos / n.null_eff
        print(n.to_string(index=False, formatters={
            'null_t': '{:.2f}'.format, 'null_t_p90': '{:.2f}'.format,
            'null_eff': '{:.4f}'.format, 'null_agree': '{:.3f}'.format,
            't_oos': '{:.1f}'.format, 'eff_oos': '{:.4f}'.format,
            't_ratio': '{:.2f}x'.format, 'eff_ratio': '{:.2f}x'.format}))
        print('t_ratio is the honest cross-horizon comparison: real t divided by'
              ' the t the same procedure gets from a shifted target.')
        r = r.merge(n[['H', 'null_t', 'null_eff', 't_ratio', 'eff_ratio']], on='H')

    print('\nDOES ANYTHING THAT FAILS AT 20 DAYS PASS AT A SHORTER ONE?')
    p20 = set(S[(S.H == 20) & S['pass']].signal)
    for H in HS[:-1]:
        ph = set(S[(S.H == H) & S['pass']].signal)
        new = ph - p20
        print('  H=%2d: %d pass, %d of them fail at 20d' % (H, len(ph), len(new)))
        if new:
            sub = S[(S.H == H) & S.signal.isin(new)]
            print('        %s' % ', '.join(sorted(new)[:8]))
            print('        their 20d failure: %s'
                  % sub.fails.value_counts().to_dict())
    return S, r


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    assert np.allclose(target_h(px, sc3.H).fillna(-9), sc3.target(px).fillna(-9)), \
        'target_h does not reproduce sc3.target at its own horizon'
    Y = {H: {p: target_h(px, H)[p] for p in px.columns} for H in HS}
    cand = candidates()
    print('%d candidates: %d old survivors (%d current), %d near-misses'
          % (len(cand), int(cand.surv_old.sum()), int(cand.surv_new.sum()),
             int((~cand.surv_old).sum())))
    S, keep = build_and_score(px, cand, Y)
    S.to_csv(os.path.join(ROOTOUT, 'horizon_signals.csv'), index=False)

    # sanity: at 20 days this must reproduce the published statistics
    pub = {d['s']: d for d in json.load(open(SIG))}
    chk = S[(S.H == 20) & S.signal.isin(pub)]
    dif = [abs(r.so - pub[r.signal]['so']) for _, r in chk.iterrows()
           if pub[r.signal].get('so') is not None]
    print('\nH=20 against published OOS spreads: %d signals, max diff %.2e'
          % (len(dif), max(dif) if dif else np.nan))

    rng = np.random.default_rng(SEED)
    print('\nnull: %d shifts x %d horizons on the %d old survivors'
          % (NSHIFT, len(HS), len(keep)))
    N = run_null(keep, px, rng)
    N.to_csv(os.path.join(ROOTOUT, 'horizon_null.csv'), index=False)
    S2, r = report(S, N, cand)
    r.to_csv(os.path.join(ROOTOUT, 'horizon_summary.csv'), index=False)
    print('\nwrote horizon_signals.csv, horizon_summary.csv, horizon_null.csv')
    return S2


def report_only():
    S = pd.read_csv(os.path.join(ROOTOUT, 'horizon_signals.csv'))
    f = os.path.join(ROOTOUT, 'horizon_null.csv')
    N = pd.read_csv(f) if os.path.exists(f) else pd.DataFrame()
    S2, r = report(S, N, candidates())
    r.to_csv(os.path.join(ROOTOUT, 'horizon_summary.csv'), index=False)
    return S2


if __name__ == '__main__':
    if '--report-only' in sys.argv:
        report_only()
    else:
        main()
