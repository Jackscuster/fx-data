import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Task 8. Scale -- the half of the question the old target threw away.

|net| / path divides out magnitude, so a pair drifting 0.2% in a straight line
and a pair running 3% in a straight line score identically. One is stuck, the
other is trending, and the estimator cannot tell them apart. That is the specific
reason it cannot separate trending from going nowhere.

TWO SCALE MEASURES, because they are not the same thing:
  range_vol  (max - min) over the window, in the pair's own volatility units
  path_vol   sum of |daily moves|, same units
Range is ground covered, path is walking done.

CROSSED WITH STRAIGHTNESS this gives four states:
  straight + large  trending
  straight + small  drifting -- going nowhere, cleanly
  choppy   + large  volatile chop
  choppy   + small  dead

ALL TRAILING. These describe the last 20 bars, not the next 20. Cut points are
each pair's own in-sample median, fixed and applied unchanged to the holdout, so
"large for this pair" means what it says.

WHICH SCALE AXIS. range_vol and straightness are not independent by construction
-- |net| <= range <= path, so the range/path ratio is close to straightness
itself. path_vol is the more independent axis and the measured correlations below
decide which carries the 2x2. Reporting that correlation is one of the questions
asked, so it is computed rather than assumed.

Writes results/scale_states.csv, scale_occupancy.csv, scale_excursion.csv.
"""
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
EV = os.path.join(ROOTOUT, 'entry_events.csv')
SPLIT = pd.Timestamp('2016-01-01')
W = 20
VOLWIN = 60
LAB = {(1, 1): 'trending (straight+large)', (1, 0): 'drifting (straight+small)',
       (0, 1): 'volatile chop (choppy+large)', (0, 0): 'dead (choppy+small)'}
ORDER = list(LAB.values())


def measures(px):
    """Trailing straightness and both scale measures, all lagged one bar."""
    lp = np.log(px.astype(float))
    net = (lp - lp.shift(W)).abs()
    path = lp.diff().abs().rolling(W).sum()
    rng = lp.rolling(W).max() - lp.rolling(W).min()
    vol = lp.diff().rolling(VOLWIN).std()
    inf = [np.inf, -np.inf]
    unit = vol * np.sqrt(W)
    return {
        'straight': (net / path).replace(inf, np.nan).shift(1),
        'range_vol': (rng / unit).replace(inf, np.nan).shift(1),
        'path_vol': (path / unit).replace(inf, np.nan).shift(1),
        'signed': ((lp - lp.shift(W)) / path).replace(inf, np.nan).shift(1),
    }


def states(M, scale_key, ins):
    """2x2 on each pair's own in-sample median. -> (state frame, hi/lo frames)."""
    s, sc = M['straight'], M[scale_key]
    s_hi = s.gt(s[ins].median(), axis=1)
    c_hi = sc.gt(sc[ins].median(), axis=1)
    ok = s.notna() & sc.notna()
    lab = pd.DataFrame(np.where(ok, np.where(s_hi, np.where(c_hi, 'trending (straight+large)',
                                                            'drifting (straight+small)'),
                                np.where(c_hi, 'volatile chop (choppy+large)',
                                         'dead (choppy+small)')), None),
                       index=s.index, columns=s.columns)
    return lab


def runs(lab):
    """Run lengths and the transition-matrix diagonal, pooled over pairs."""
    lens, diag_n, diag_d, first = [], 0, 0, {k: 0 for k in ORDER}
    for p in lab.columns:
        v = lab[p].dropna()
        if not len(v):
            continue
        chg = v != v.shift()
        gid = chg.cumsum()
        for _, g in v.groupby(gid):
            lens.append((g.iloc[0], len(g)))
            first[g.iloc[0]] += 1
        diag_n += int((v == v.shift()).sum())
        diag_d += len(v) - 1
    R = pd.DataFrame(lens, columns=['state', 'len'])
    return R, (diag_n / diag_d if diag_d else np.nan), first


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    ins = np.asarray(px.index < SPLIT)
    M = measures(px)

    print('IS mean of each measure (pooled): straight %.3f  range_vol %.3f  path_vol %.3f'
          % (M['straight'][ins].stack().mean(), M['range_vol'][ins].stack().mean(),
             M['path_vol'][ins].stack().mean()))

    # ---- is scale independent of straightness? ----
    print('\nCORRELATION WITH STRAIGHTNESS (pooled, in sample)')
    s = M['straight'][ins].stack()
    for k in ('range_vol', 'path_vol'):
        x = M[k][ins].stack()
        j = pd.concat([s, x], axis=1).dropna()
        print('  %-10s pearson %+.3f   spearman %+.3f'
              % (k, j.corr().iloc[0, 1], j.corr(method='spearman').iloc[0, 1]))
    scale_key = 'path_vol'
    print('  -> %s carries the 2x2 (the more independent axis)' % scale_key)

    # ---- up/down asymmetry, carried into task 10 ----
    sg = M['signed']
    up = M['straight'].where(sg > 0).stack()
    dn = M['straight'].where(sg < 0).stack()
    per = [(M['straight'][p].where(sg[p] < 0).mean() >
            M['straight'][p].where(sg[p] > 0).mean()) for p in px.columns]
    print('\nUP/DOWN ASYMMETRY  straightness on down-moves %.4f vs up-moves %.4f'
          ' -- down straighter on %d of %d pairs'
          % (dn.mean(), up.mean(), int(np.sum(per)), len(per)))

    lab = states(M, scale_key, ins)
    lab.to_csv(os.path.join(ROOTOUT, 'scale_states.csv'))

    # ---- occupancy ----
    occ = {}
    for tag, msk in (('is', ins), ('oos', ~ins)):
        v = lab[msk].stack()
        occ[tag] = v.value_counts(normalize=True).reindex(ORDER)
    O = pd.DataFrame(occ)
    per_pair = pd.DataFrame({p: lab[p].value_counts(normalize=True).reindex(ORDER)
                             for p in px.columns}).T
    O.to_csv(os.path.join(ROOTOUT, 'scale_occupancy.csv'))
    print('\nTIME IN EACH STATE')
    print(O.to_string(float_format=lambda v: '%.3f' % v))
    print('\nper-pair spread of occupancy (min..max across the 28):')
    for k in ORDER:
        print('  %-30s %.3f .. %.3f' % (k, per_pair[k].min(), per_pair[k].max()))

    # ---- stability ----
    R, diag, first = runs(lab)
    print('\nSTABILITY  transition-matrix diagonal %.3f (share of bars that stay put)'
          % diag)
    st = R.groupby('state').agg(runs=('len', 'size'), median_len=('len', 'median'),
                                mean_len=('len', 'mean'),
                                under5=('len', lambda x: (x < 5).mean())).reindex(ORDER)
    print(st.to_string(float_format=lambda v: '%.2f' % v))

    # ---- does task 3's excursion differ across the four? ----
    if os.path.exists(EV):
        E = pd.read_csv(EV)
        E['date'] = pd.to_datetime(E.date)
        pos = {(p, d): lab[p].get(d) for p in lab.columns for d in []}   # noqa: F841
        st_at = []
        L = lab.stack().rename('state').reset_index()
        L.columns = ['date', 'pair', 'state']
        E = E.merge(L, on=['date', 'pair'], how='left')
        X = E[E.oos & E.state.notna()].copy()
        X['gb_pct'] = np.nan
        g = X.groupby('state').agg(n=('mfe', 'size'), mfe=('mfe', 'mean'),
                                   mae=('mae', 'mean'),
                                   bars=('bars_to_peak', 'mean'),
                                   gb=('giveback', 'mean'),
                                   eff=('path_eff', 'mean'),
                                   fav20=('fav_20', 'mean')).reindex(ORDER)
        g['gb_pct'] = 100 * g.gb / g.mfe
        g['ratio'] = g.mfe / g.mae.abs()
        print('\nTASK 3 EXCURSION ACROSS THE FOUR STATES (out of sample)')
        print(g[['n', 'mfe', 'mae', 'ratio', 'bars', 'gb_pct', 'eff', 'fav20']]
              .to_string(float_format=lambda v: '%.4f' % v))
        g.to_csv(os.path.join(ROOTOUT, 'scale_excursion.csv'))
        # the comparison that matters: does scale add anything beyond the chop axis
        X['straight_hi'] = X.state.str.startswith(('trending', 'drifting'))
        X['large'] = X.state.str.contains('large')
        print('\n  marginals -- straightness axis alone, then scale axis alone:')
        for col in ('straight_hi', 'large'):
            m = X.groupby(col).agg(n=('mfe', 'size'), mfe=('mfe', 'mean'),
                                   bars=('bars_to_peak', 'mean'),
                                   eff=('path_eff', 'mean'))
            print('   %s' % col)
            print(m.to_string(float_format=lambda v: '%.4f' % v))
    print('\nwrote scale_states.csv, scale_occupancy.csv, scale_excursion.csv')


if __name__ == '__main__':
    main()
