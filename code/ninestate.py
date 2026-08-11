import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""The nine-state grid, and the per-pair feed the explorer screen reads.

A NOTE ON WHAT THIS IS. No nine-state classifier existed before this file. The
Task 10 classifier is three-state (low/mid/high on a weighted score). Nine states
are built here as the 3x3 of the two axes that actually measured something --
straightness x scale -- which follows the pattern of the project's existing
ninebox.py and gives every cell a plain meaning:

                     strong         medium         weak
  trend (straight)   strong trend   medium trend   weak trend
  transitional       strong trans.  medium trans.  weak trans.
  chop               strong chop    medium chop    weak chop

TWO WORDS, TWO AXES, AND THEY ARE NOT THE SAME THING.

  strong / medium / weak   SIZE. How far the pair is moving, in its own vol units.
                           NOT confidence in the reading.
  trend / transitional /   CLEANLINESS. How straight the travel was.
  chop

So "strong chop" is a pair thrashing a long way, and "weak trend" is a pair
drifting a short way in a straight line. Neither word says anything about how
sure the classifier is.

Both axes are trailing over 20 bars and lagged one, cut at each pair's own
in-sample terciles with hysteresis, so a reading sitting on a boundary does not
flip the label every other bar.

THE RIBBON SHIPS AT 7 / 28 / 128. The 4-200 sweep in windowsweep.py pointed at
19 / 105 / 188 on separation and non-duplication; both are computed so the
difference stays visible.

The previous 60-bar slow window is gone and that matters: 60 equals VOLWIN, so
scale = sum|r|_60 / (sd_60 * sqrt(60)) collapsed toward sqrt(2/pi) and the axis
stopped moving. It was the worst single window in the whole 4-200 range -- churn
92.7 against ~143 either side, separation 0.0187 against 0.0408 at L=105. 128 is
clear of it.

Writes results/nine_*.csv and app_explorer.json, which is a SEPARATE feed file
like app_signals.json -- 28 pairs of daily series would push app_data.json from
0.2 MB to several MB, and the whole point of the earlier split was to keep the
main feed small.
"""
import json
import numpy as np, pandas as pd
from classifier import hyst, fit_frac

PX = os.path.join(ROOTDATA, 'px28.csv')
EV = os.path.join(ROOTOUT, 'entry_events.csv')
CRISIS = os.path.join(ROOTOUT, 'crisis_events.csv')
OUT = os.path.join(ROOTOUT, 'app_explorer.json')
SPLIT = pd.Timestamp('2016-01-01')
# W is the MEDIUM ribbon window. The base grid, the transition matrix, the
# excursion profiles and the per-pair stats are all computed on it, so the
# headline numbers and the chart describe the same object. It was 20, which was
# not one of the ribbon windows at all.
W, VOLWIN, BAND = 28, 60, .25
SAX = ['chop', 'mid', 'straight']
CAX = ['small', 'mid', 'large']
SNAME = {'straight': 'trend', 'mid': 'transitional', 'chop': 'chop'}
CNAME = {'large': 'strong', 'mid': 'medium', 'small': 'weak'}
NAME = {(a, b): '%s %s' % (CNAME[b], SNAME[a]) for a in SNAME for b in CNAME}
# trend first, then transitional, then chop; strong to weak inside each row
STATES = [NAME[(s, c)] for s in ('straight', 'mid', 'chop')
          for c in ('large', 'mid', 'small')]


def raw_axes(px, L=W):
    lp = np.log(px.astype(float)); rr = lp.diff()
    net = (lp - lp.shift(L)).abs()
    path = rr.abs().rolling(L).sum()
    vol = rr.rolling(VOLWIN).std()
    inf = [np.inf, -np.inf]
    straight = (net / path).replace(inf, np.nan)
    e5 = ((lp - lp.shift(5)).abs() / rr.abs().rolling(5).sum()).replace(inf, np.nan)
    return dict(straight=straight.shift(1),
                scale=(path / (vol * np.sqrt(L))).replace(inf, np.nan).shift(1),
                persist=(straight - e5).shift(1))


def tercile(x, fit, band=BAND):
    """-> 0/1/2 with hysteresis at both boundaries."""
    frac = fit_frac(x, fit)
    lo = hyst((frac - 1 / 3 + .5).clip(0, 1), band)
    hi = hyst((frac - 2 / 3 + .5).clip(0, 1), band)
    return (lo.fillna(0) + hi.fillna(0)).where(frac.notna())


def nine(px, fit):
    A = raw_axes(px)
    s = tercile(A['straight'], fit)
    c = tercile(A['scale'], fit)
    lab = pd.DataFrame(np.where(s.notna() & c.notna(),
                                [[NAME[(SAX[int(si)], CAX[int(ci)])]
                                  if np.isfinite(si) and np.isfinite(ci) else None
                                  for si, ci in zip(sr, cr)]
                                 for sr, cr in zip(s.values, c.values)], None),
                       index=px.index, columns=px.columns)
    return lab, A


def runs_of(lab):
    out = []
    for p in lab.columns:
        v = lab[p].dropna()
        if not len(v):
            continue
        gid = (v != v.shift()).cumsum()
        for _, g in v.groupby(gid):
            out.append((p, g.iloc[0], len(g)))
    return pd.DataFrame(out, columns=['pair', 'state', 'len'])


def age_of(lab):
    A = pd.DataFrame(index=lab.index, columns=lab.columns, dtype=float)
    for p in lab.columns:
        v = lab[p]; m = v.notna()
        gid = (v != v.shift()).where(m).cumsum()
        A[p] = v.groupby(gid).cumcount().where(m) + 1
    return A


def transitions(lab):
    M = pd.DataFrame(0.0, index=STATES, columns=STATES)
    for p in lab.columns:
        v = lab[p].dropna()
        for a, b in zip(v.values[:-1], v.values[1:]):
            M.loc[a, b] += 1
    return M.div(M.sum(1).replace(0, np.nan), axis=0)


def validate(px, lab, fit):
    """The same battery the three-state classifier got, on the grid.

    The question this exists to answer: do "strong trend" and "strong chop" --
    both large moves, one straight and one thrashing -- actually differ? If they
    do not, cleanliness is not carrying anything and the second axis is
    decoration.
    """
    import numpy as np
    from classifier import realised_props, separation, persistence

    print('\nVALIDATION OF THE GRID')
    P = persistence(lab)
    print('  persistence  median run %.1f, mean %.2f, %.0f%% under 5, diagonal %.3f'
          % (P['median_run'], P['mean_run'], 100 * P['under5'], P['diagonal']))
    props = realised_props(px)
    S = grid_separation(lab, props)
    print('  separation (gap in sd units of each property)')
    print(S.to_string(index=False, float_format=lambda v: '%.4f' % v))

    lab20, _ = nine(px, px.index < pd.Timestamp('2021-01-01'))
    pre = px.index < SPLIT
    j = pd.concat([lab[pre].stack().rename('a'), lab20[pre].stack().rename('b')],
                  axis=1).dropna()
    print('  refit stability  %.1f%% of %d pre-2016 pair-days keep their label'
          % (100 * (j.a == j.b).mean(), len(j)))

    rr = np.log(px.astype(float)).diff()
    rng = np.random.default_rng(9)
    NS = int(os.environ.get('FX_NSHUF', 200))
    print('  null, %d draws per surrogate' % NS)
    for tag in ('A sign-randomised', 'B IID permutation'):
        pers, seps = [], []
        for _ in range(NS):
            if tag.startswith('A'):
                sg = pd.DataFrame(rng.choice([-1., 1.], size=rr.shape),
                                  index=rr.index, columns=rr.columns)
                r2 = rr.abs() * sg
            else:
                r2 = pd.DataFrame({p: rng.permutation(rr[p].dropna().values.copy())
                                   for p in rr.columns},
                                  index=rr.dropna(how='all').index).reindex(rr.index)
            l2, _ = nine_from_returns(px, r2, fit)
            pers.append(persistence(l2)['median_run'])
            seps.append(grid_separation(l2, props).gap_over_sd.mean())
        pers, seps = np.array(pers), np.array(seps)
        print('     %-18s median run %.2f +/- %.2f (real %.2f)  separation %.4f'
              ' +/- %.4f (real %.4f)  p=%.3f'
              % (tag, pers.mean(), pers.std(), P['median_run'], seps.mean(),
                 seps.std(), S.gap_over_sd.mean(),
                 (1 + int((seps >= S.gap_over_sd.mean()).sum())) / (len(seps) + 1)))
    return P, S


def grid_separation(lab, props):
    """separation() in classifier.py reindexes to its own three labels and returns
    NaN on a nine-state grid. Same measure, the grid's states."""
    rows = []
    for name, P in props.items():
        d = pd.DataFrame({'s': lab.stack(), 'v': P.stack()}).dropna()
        g = d.groupby('s').v.mean().reindex(STATES)
        rows.append(dict(prop=name, gap=g.max() - g.min(),
                         gap_over_sd=(g.max() - g.min()) / d.v.std()))
    return pd.DataFrame(rows)


def nine_from_returns(px, r, fit):
    """The grid rebuilt on surrogate returns."""
    lp = r.cumsum()
    net = (lp - lp.shift(W)).abs()
    path = r.abs().rolling(W).sum()
    vol = r.rolling(VOLWIN).std()
    inf = [np.inf, -np.inf]
    st = (net / path).replace(inf, np.nan).shift(1)
    sc = (path / (vol * np.sqrt(W))).replace(inf, np.nan).shift(1)
    a, b = tercile(st, fit), tercile(sc, fit)
    lab = pd.DataFrame(np.where(a.notna() & b.notna(),
                                [[NAME[(SAX[int(x)], CAX[int(y)])]
                                  if np.isfinite(x) and np.isfinite(y) else None
                                  for x, y in zip(ar, br)]
                                 for ar, br in zip(a.values, b.values)], None),
                       index=px.index, columns=px.columns)
    return lab, None


def big_test(lab):
    """strong trend against strong chop: the whole case for a second axis."""
    if not os.path.exists(EV):
        return
    E = pd.read_csv(EV); E['date'] = pd.to_datetime(E.date)
    L = lab.stack().rename('state').reset_index()
    L.columns = ['date', 'pair', 'state']
    X = E.merge(L, on=['date', 'pair'], how='left')
    X = X[X.oos & X.state.notna()]
    print('\nSTRONG TREND vs STRONG CHOP -- same size, opposite cleanliness')
    a = X[X.state == 'strong trend']; b = X[X.state == 'strong chop']
    for nm, d in (('strong trend', a), ('strong chop', b)):
        print('  %-13s n=%4d  mfe %.4f  mae %.4f  ratio %.3f  bars %.2f  eff %.4f'
              % (nm, len(d), d.mfe.mean(), d.mae.mean(),
                 d.mfe.mean() / abs(d.mae.mean()), d.bars_to_peak.mean(),
                 d.path_eff.mean()))
    for col in ('path_eff', 'bars_to_peak', 'mfe', 'mae'):
        x, y = a[col].dropna(), b[col].dropna()
        d = y.mean() - x.mean()
        se = np.sqrt(x.var() / len(x) + y.var() / len(y))
        print('    %-13s chop minus trend %+.4f  t %+.2f' % (col, d, d / se))
    # and the same cut at small scale, as a control
    c = X[X.state == 'weak trend']; e = X[X.state == 'weak chop']
    if len(c) > 100 and len(e) > 100:
        d = e.path_eff.mean() - c.path_eff.mean()
        se = np.sqrt(c.path_eff.var() / len(c) + e.path_eff.var() / len(e))
        print('  control at WEAK size: path eff chop minus trend %+.4f  t %+.2f'
              % (d, d / se))


MULTI = (7, 28, 128)


def grid_at(px, L, fit):
    """The nine-state grid at an arbitrary window, plus which side of the
    straightness midpoint each bar leans (for the 6-state collapse)."""
    lp = np.log(px.astype(float)); rr = lp.diff()
    net = (lp - lp.shift(L)).abs()
    path = rr.abs().rolling(L).sum()
    vol = rr.rolling(VOLWIN).std()
    inf = [np.inf, -np.inf]
    st = (net / path).replace(inf, np.nan).shift(1)
    sc = (path / (vol * np.sqrt(L))).replace(inf, np.nan).shift(1)
    a, b = tercile(st, fit), tercile(sc, fit)
    lab = pd.DataFrame(np.where(a.notna() & b.notna(),
                                [[NAME[(SAX[int(x)], CAX[int(y)])]
                                  if np.isfinite(x) and np.isfinite(y) else None
                                  for x, y in zip(ar, br)]
                                 for ar, br in zip(a.values, b.values)], None),
                       index=px.index, columns=px.columns)
    lean = (fit_frac(st, fit) > .5)
    return lab, lean


TIERS = ['established', 'transition starting', 'transition confirming',
         'unresolved']


def tiers_from(multi):
    """Agreement tiers from the three ribbon grids, compared at FAMILY level
    (trend / transitional / chop) -- the size word is not what a window
    disagreement is about."""
    ls = sorted(multi)
    fam = [multi[L][0].apply(lambda c: c.str.split().str[-1]) for L in ls]
    f, m, s2 = fam
    ok = f.notna() & m.notna() & s2.notna()
    return pd.DataFrame(np.where(ok, np.where((f == m) & (m == s2), TIERS[0],
                                 np.where((f != m) & (m == s2), TIERS[1],
                                 np.where((f == m) & (m != s2), TIERS[2], TIERS[3]))),
                                 None), index=f.index, columns=f.columns)


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    fit = px.index < SPLIT
    lab, A = nine(px, fit)
    age = age_of(lab)

    R = runs_of(lab)
    occ = lab.stack().value_counts(normalize=True).reindex(STATES).fillna(0)
    dur = R.groupby('state').len.median().reindex(STATES)
    st = pd.DataFrame({'share': occ, 'median_len': dur,
                       'runs': R.groupby('state').len.size().reindex(STATES)})

    # excursion profile per state
    prof = pd.DataFrame()
    if os.path.exists(EV):
        E = pd.read_csv(EV); E['date'] = pd.to_datetime(E.date)
        L = lab.stack().rename('state').reset_index()
        L.columns = ['date', 'pair', 'state']
        X = E.merge(L, on=['date', 'pair'], how='left')
        X = X[X.oos & X.state.notna()]
        prof = X.groupby('state').agg(
            n=('mfe', 'size'), mfe=('mfe', 'mean'), mae=('mae', 'mean'),
            bars=('bars_to_peak', 'mean'), gb=('giveback', 'mean'),
            eff=('path_eff', 'mean'), fav20=('fav_20', 'mean')).reindex(STATES)
        prof['retrace_pct'] = 100 * prof.gb / prof.mfe
        prof['ratio'] = prof.mfe / prof.mae.abs()
        prof.to_csv(os.path.join(ROOTOUT, 'nine_excursion.csv'))
        sp = prof.eff.max() - prof.eff.min()
        print('excursion spread in path efficiency across the nine: %.4f' % sp)

    TM = transitions(lab)
    TM.to_csv(os.path.join(ROOTOUT, 'nine_transitions.csv'))
    st.to_csv(os.path.join(ROOTOUT, 'nine_states.csv'))
    per = pd.DataFrame({p: lab[p].value_counts(normalize=True).reindex(STATES)
                        for p in px.columns}).T.fillna(0)
    perdur = pd.DataFrame({s: R[R.state == s].groupby('pair').len.median()
                           for s in STATES}).reindex(px.columns)
    per.to_csv(os.path.join(ROOTOUT, 'nine_per_pair.csv'))
    perdur.to_csv(os.path.join(ROOTOUT, 'nine_per_pair_dur.csv'))
    print('\nSTATE OCCUPANCY AND DURATION')
    print(st.to_string(float_format=lambda v: '%.3f' % v))
    print('\ntransition diagonal (stay probability): min %.3f max %.3f'
          % (np.diag(TM).min(), np.diag(TM).max()))

    validate(px, lab, fit)
    big_test(lab)

    # ---- the ribbon, at the measured lengths and at the requested ones ----
    from ribbon import label_at
    rib = {}
    for tag, ls in (('shipped', MULTI), ('sweep-selected', (19, 105, 188))):
        rib[tag] = [label_at(px, L, fit) for L in ls]
        f, m, s2 = rib[tag]
        agree = ((f == m) & (m == s2)).where(f.notna()).stack().mean()
        print('ribbon %-9s %s  all-three-agree %.3f' % (tag, ls, agree))

    multi = {L: grid_at(px, L, fit) for L in MULTI}
    T = tiers_from(multi)
    T.to_csv(os.path.join(ROOTOUT, 'nine_tiers.csv'))
    print('\nAGREEMENT TIERS at %s (family level)' % str(MULTI))
    for tag, msk in (('is', fit), ('oos', ~fit)):
        v = T[msk].stack().value_counts(normalize=True).reindex(TIERS)
        print('  %-4s %s' % (tag, '  '.join('%s %.3f' % (k[:11], v[k]) for k in TIERS)))
    if os.path.exists(EV):
        Ev = pd.read_csv(EV); Ev['date'] = pd.to_datetime(Ev.date)
        Lt = T.stack().rename('tier').reset_index()
        Lt.columns = ['date', 'pair', 'tier']
        Xt = Ev.merge(Lt, on=['date', 'pair'], how='left')
        Xt = Xt[Xt.oos & Xt.tier.notna()]
        gt = Xt.groupby('tier').agg(n=('mfe', 'size'), mfe=('mfe', 'mean'),
                                    mae=('mae', 'mean'),
                                    bars=('bars_to_peak', 'mean'),
                                    eff=('path_eff', 'mean')).reindex(TIERS)
        gt['ratio'] = gt.mfe / gt.mae.abs()
        gt.to_csv(os.path.join(ROOTOUT, 'nine_tier_excursion.csv'))
        print(gt[['n', 'mfe', 'ratio', 'bars', 'eff']]
              .to_string(float_format=lambda v: '%.4f' % v))
        print('  established vs transition-starting path eff: %.4f vs %.4f'
              % (gt.eff.iloc[0], gt.eff.iloc[1]))
    write_feed(px, lab, A, age, rib['shipped'], st, prof, TM, per, perdur, multi)


def write_feed(px, lab, A, age, rib, st, prof, TM, per, perdur, multi=None):
    code = {s: i for i, s in enumerate(STATES)}
    rcode = {'low': 0, 'mid': 1, 'high': 2}
    dates = [d.strftime('%Y-%m-%d') for d in px.index]
    pairs = {}
    for p in px.columns:
        def arr(s, nd):
            return [None if not np.isfinite(v) else round(float(v), nd) for v in s]
        pairs[p] = dict(
            px=arr(px[p].values, 6),
            st=[None if v is None or (isinstance(v, float) and not np.isfinite(v))
                else code.get(v) for v in lab[p].values],
            rf=[rcode.get(v) for v in rib[0][p].values],
            rm=[rcode.get(v) for v in rib[1][p].values],
            rs=[rcode.get(v) for v in rib[2][p].values],
            straight=arr(A['straight'][p].values, 4),
            scale=arr(A['scale'][p].values, 3),
            persist=arr(A['persist'][p].values, 4),
            age=[None if not np.isfinite(v) else int(v) for v in age[p].values])
        # the grid at each ribbon window, so the chart can be coloured by any of
        # them, plus which way each transitional bar leans for the 6-state view
        for L, (lb, ln) in (multi or {}).items():
            pairs[p]['st%d' % L] = [None if v is None or (isinstance(v, float)
                                    and not np.isfinite(v)) else code.get(v)
                                    for v in lb[p].values]
            pairs[p]['ln%d' % L] = [None if not np.isfinite(v) else int(v)
                                    for v in ln[p].astype(float).values]
    ev = []
    if os.path.exists(CRISIS):
        C = pd.read_csv(CRISIS)
        if 'date' in C:
            seen = set()
            for _, r in C.iterrows():
                d = str(r['date'])[:10]
                if d in seen:
                    continue
                seen.add(d)
                ev.append(dict(date=d, type=str(r.get('type', '')),
                               ccy=str(r.get('ccy', ''))))
    out = dict(dates=dates, pairs=pairs, states=STATES, events=ev,
               split='2016-01-01',
               state_stats=json.loads(st.reset_index().rename(
                   columns={'index': 'state'}).to_json(orient='records')),
               excursion=json.loads(prof.reset_index().rename(
                   columns={'index': 'state'}).to_json(orient='records'))
               if len(prof) else [],
               transitions=[[None if not np.isfinite(TM.iloc[i, j])
                             else round(float(TM.iloc[i, j]), 4)
                             for j in range(9)] for i in range(9)],
               per_pair=json.loads(per.reset_index().rename(
                   columns={'index': 'pair'}).to_json(orient='records')),
               per_pair_dur=json.loads(perdur.reset_index().rename(
                   columns={'index': 'pair'}).to_json(orient='records')))
    with open(OUT, 'w') as f:
        json.dump(out, f, separators=(',', ':'))
    print('\nwrote %s  %.1f MB' % (os.path.basename(OUT),
                                   os.path.getsize(OUT) / 1048576))


if __name__ == '__main__':
    main()
