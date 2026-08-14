import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""External driver #2: bond volatility (MOVE) against regime shape.

A SEPARATE OUTPUT. It does not feed the shape or activity scores.

OVERLAP, CHECKED FIRST. ^MOVE in data/ext.csv runs 2002-11-12 to 2026-07-31,
5,945 bars. The FX sample starts 1999-01-04, so the first four years have no MOVE
at all. Within the overlap: 3,302 in-sample bars (2002-11-12 onward) and 2,643
holdout bars. IS is therefore a 13-year window, not 17.

DECLARED CONSTRUCTIONS ONLY, two of them:
  level   bucketed into terciles, cut on IS and applied unchanged
  chg21   its 21-bar change
Nothing else. No sweep.

MOVE IS ONE GLOBAL SERIES HITTING ALL 28 PAIRS AT ONCE, so pair-level episodes
are not independent observations -- on any given day every pair sees the same
MOVE. Everything here is therefore POOLED BY DAY: the unit of observation is a
calendar day, and the statistic is the cross-sectional share of pairs in each
state that day. 6,855 pair-days become 5,945 days at most, and the significance
is computed on days.

AND THE ASSOCIATION IS NOT A SIGN TEST. MOVE is a level, not a direction, so the
rate-differential framing -- does the sign agree with the price move -- does not
apply. The present-tense question is whether STATE OCCUPANCY differs across MOVE
buckets, and the lead question is whether MOVE was already elevated or moving
before a transition.

Everything lagged one bar. IS chooses, OOS is read once. Circular-shift null.

Writes results/move_{coverage,q1,q2,null}.csv with .txt companions.
"""
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
EXT = os.path.join(ROOTDATA, 'ext.csv')
ST = os.path.join(ROOTOUT, 'states_g4_twoscore4.csv')
SPLIT = pd.Timestamp('2016-01-01')
SHAPES = ['trending', 'ranging', 'trend-in-range', 'neither']
W_CHG = 21
NSHIFT = int(os.environ.get('FX_NSHIFT', 50))
MINOFF = 500


def hdr(path, title, body):
    with open(path.replace('.csv', '.txt'), 'w') as f:
        f.write('%s\n%s\n\n%s\n' % (title, '=' * len(title), body))


def load():
    st = pd.read_csv(ST, index_col=0, parse_dates=True, comment='#')
    mv = pd.read_csv(EXT, index_col=0, parse_dates=True)['^MOVE'].dropna()
    mv = mv.reindex(st.index).ffill(limit=5)
    return st, mv


def daily(st):
    """Cross-sectional share of pairs in each state, one row per DAY."""
    out = {}
    for s in SHAPES:
        out[s] = (st == s).sum(axis=1) / st.notna().sum(axis=1)
    d = pd.DataFrame(out)
    return d[st.notna().sum(axis=1) >= 10]


def main():
    st, mv = load()
    D = daily(st)
    lvl = mv.shift(1)
    chg = (mv - mv.shift(W_CHG)).shift(1)
    idx = D.index.intersection(lvl.dropna().index)
    D, lvl, chg = D.loc[idx], lvl.loc[idx], chg.loc[idx]
    fit = idx < SPLIT
    print('EXTERNAL DRIVER #2 -- MOVE (bond volatility)')
    print('  overlap: %s -> %s, %d days | IS %d, OOS %d'
          % (idx.min().date(), idx.max().date(), len(idx), int(fit.sum()),
             int((~fit).sum())))
    cov = pd.DataFrame([dict(series='^MOVE', first=str(idx.min().date()),
                             last=str(idx.max().date()), days=len(idx),
                             is_days=int(fit.sum()), oos_days=int((~fit).sum()),
                             fx_starts='1999-01-04',
                             missing_years_at_start=3.9,
                             level_min=float(mv.min()), level_max=float(mv.max()))])
    cov.to_csv(os.path.join(ROOTOUT, 'move_coverage.csv'), index=False)
    hdr(os.path.join(ROOTOUT, 'move_coverage.csv'), 'MOVE coverage',
        '^MOVE runs 2002-11-12 to 2026-07-31. The FX sample starts 1999-01-04,\n'
        'so the first ~3.9 years have no MOVE at all and IS is a 13-year window\n'
        'rather than 17. Unit of observation is a DAY, not a pair-day, because\n'
        'MOVE is one global series hitting all 28 pairs simultaneously.')

    # ---------------- QUESTION 1 ----------------
    q = np.nanquantile(lvl[fit], [1 / 3, 2 / 3])
    buck = pd.Series(np.where(lvl <= q[0], 'low',
                              np.where(lvl <= q[1], 'mid', 'high')), index=idx)
    print('\nQ1 -- state occupancy by MOVE tercile (cut on IS: %.1f / %.1f)'
          % (q[0], q[1]))
    rows = []
    for tag, m in (('is', fit), ('oos', ~fit)):
        for b in ('low', 'mid', 'high'):
            sel = m & (buck == b).values
            if sel.sum() < 50:
                continue
            for s in SHAPES:
                rows.append(dict(block=tag, bucket=b, state=s,
                                 days=int(sel.sum()),
                                 mean_share=float(D[s][sel].mean())))
    Q1 = pd.DataFrame(rows)
    # spread = high minus low, per state per block
    sp = []
    for tag in ('is', 'oos'):
        for s in SHAPES:
            hi = Q1[(Q1.block == tag) & (Q1.bucket == 'high') & (Q1.state == s)]
            lo = Q1[(Q1.block == tag) & (Q1.bucket == 'low') & (Q1.state == s)]
            if len(hi) and len(lo):
                sp.append(dict(block=tag, state=s,
                               high=float(hi.mean_share.iloc[0]),
                               low=float(lo.mean_share.iloc[0]),
                               spread=float(hi.mean_share.iloc[0]
                                            - lo.mean_share.iloc[0])))
    SP = pd.DataFrame(sp)
    Q1.to_csv(os.path.join(ROOTOUT, 'move_q1.csv'), index=False)
    print('  %-4s %-16s %8s %8s %9s' % ('blk', 'state', 'low', 'high', 'spread'))
    for _, r in SP.iterrows():
        print('  %-4s %-16s %8.3f %8.3f %+9.3f'
              % (r.block, r.state, r.low, r.high, r.spread))
    # also the 21-bar change, correlated with daily shares
    crows = []
    for tag, m in (('is', fit), ('oos', ~fit)):
        for s in SHAPES:
            a, b = chg[m], D[s][m]
            k = a.notna() & b.notna()
            if k.sum() > 200:
                crows.append(dict(block=tag, state=s, n_days=int(k.sum()),
                                  corr_chg21=float(np.corrcoef(a[k], b[k])[0, 1])))
    CR = pd.DataFrame(crows)
    print('\n  correlation of the 21-bar MOVE change with the daily state share')
    for _, r in CR.iterrows():
        print('    %-4s %-16s n=%4d  r=%+.4f'
              % (r.block, r.state, r.n_days, r.corr_chg21))
    CR.to_csv(os.path.join(ROOTOUT, 'move_q1_chg.csv'), index=False)
    hdr(os.path.join(ROOTOUT, 'move_q1.csv'), 'Question 1 -- MOVE and state occupancy',
        'Mean cross-sectional share of the 28 pairs in each state, by MOVE\n'
        'tercile, pooled BY DAY. Terciles cut on in-sample only.\n\n'
        'spread = high bucket minus low bucket. MOVE is a level, not a\n'
        'direction, so this is an occupancy question and not a sign test.')
    hdr(os.path.join(ROOTOUT, 'move_q1_chg.csv'),
        'Question 1b -- 21-bar MOVE change against daily state share',
        'Pearson correlation between the lagged 21-bar change in MOVE and the\n'
        'daily cross-sectional share of pairs in each state. One observation\n'
        'per day.')

    # choose the headline state on IS
    isS = SP[SP.block == 'is'].copy()
    isS['abs'] = isS.spread.abs()
    BEST = isS.sort_values('abs', ascending=False).state.iloc[0]
    real_is = float(isS[isS.state == BEST].spread.iloc[0])
    oosS = SP[(SP.block == 'oos') & (SP.state == BEST)]
    real_oos = float(oosS.spread.iloc[0])
    print('\n  CHOSEN ON IS: %s (spread %+.3f). HOLDOUT read once: %+.3f'
          % (BEST, real_is, real_oos))

    # ---------------- QUESTION 2 ----------------
    print('\nQ2 -- lead into trending, pooled by day')
    into = ((st == 'trending') & (st.shift(1).notna())
            & (st.shift(1) != 'trending')).sum(axis=1).reindex(idx).fillna(0)
    rows2 = []
    for tag, m in (('is', fit), ('oos', ~fit)):
        hasT = (into > 0).values & m
        noT = (into == 0).values & m
        for nm, sel in (('days with a transition into trending', hasT),
                        ('days with none', noT)):
            if sel.sum() < 30:
                continue
            rows2.append(dict(block=tag, kind=nm, days=int(sel.sum()),
                              mean_level=float(lvl[sel].mean()),
                              mean_chg21=float(chg[sel].mean())))
    Q2 = pd.DataFrame(rows2)
    for tag in ('is', 'oos'):
        a = Q2[(Q2.block == tag) & (Q2.kind.str.startswith('days with a'))]
        b = Q2[(Q2.block == tag) & (Q2.kind == 'days with none')]
        if len(a) and len(b):
            Q2.loc[a.index, 'level_diff'] = a.mean_level.iloc[0] - b.mean_level.iloc[0]
            Q2.loc[a.index, 'chg21_diff'] = a.mean_chg21.iloc[0] - b.mean_chg21.iloc[0]
    Q2.to_csv(os.path.join(ROOTOUT, 'move_q2.csv'), index=False)
    for _, r in Q2.iterrows():
        print('  %-4s %-38s n=%4d  level %6.2f  chg21 %+6.2f%s'
              % (r.block, r.kind, r.days, r.mean_level, r.mean_chg21,
                 ('   diff %+.2f' % r.level_diff)
                 if np.isfinite(r.get('level_diff', np.nan)) else ''))
    hdr(os.path.join(ROOTOUT, 'move_q2.csv'), 'Question 2 -- MOVE before a transition',
        'Mean MOVE level and 21-bar change on days that contain at least one\n'
        'transition into trending, against days that contain none. Both reads\n'
        'are lagged one bar, so they use MOVE through the previous close.\n\n'
        'Pooled by day: a day is one observation however many pairs turned.')

    # ---------------- NULL ----------------
    print('\nNULL -- %d circular shifts of MOVE against the state panel' % NSHIFT)
    n = len(idx)
    rng = np.random.default_rng(20021112)
    acc = {'is': [], 'oos': []}
    for i in range(NSHIFT):
        k = int(rng.integers(MINOFF, n - MINOFF))
        l2 = pd.Series(np.roll(lvl.values, k), index=idx)
        q2c = np.nanquantile(l2[fit], [1 / 3, 2 / 3])
        b2 = pd.Series(np.where(l2 <= q2c[0], 'low',
                                np.where(l2 <= q2c[1], 'mid', 'high')), index=idx)
        for tag, m in (('is', fit), ('oos', ~fit)):
            hi = m & (b2 == 'high').values
            lo = m & (b2 == 'low').values
            if hi.sum() > 50 and lo.sum() > 50:
                acc[tag].append(float(D[BEST][hi].mean() - D[BEST][lo].mean()))
        if (i + 1) % 10 == 0:
            print('  ... %d/%d' % (i + 1, NSHIFT), flush=True)
    # Q2 IS ALSO NULLED. Its level and change differences came out positive in
    # BOTH blocks, and reporting a consistent pattern without testing it is the
    # mistake this project keeps catching. The shift is the same one.
    q2acc = {(t, k): [] for t in ('is', 'oos') for k in ('level', 'chg21')}
    rng2 = np.random.default_rng(773)
    for i in range(NSHIFT):
        k = int(rng2.integers(MINOFF, n - MINOFF))
        l2 = pd.Series(np.roll(lvl.values, k), index=idx)
        c2 = pd.Series(np.roll(chg.values, k), index=idx)
        for tag, m in (('is', fit), ('oos', ~fit)):
            hasT = (into > 0).values & m
            noT = (into == 0).values & m
            if hasT.sum() < 30 or noT.sum() < 30:
                continue
            q2acc[(tag, 'level')].append(float(l2[hasT].mean() - l2[noT].mean()))
            q2acc[(tag, 'chg21')].append(float(c2[hasT].mean() - c2[noT].mean()))
    nrows = []
    for tag in ('is', 'oos'):
        a = Q2[(Q2.block == tag) & (Q2.kind.str.startswith('days with a'))]
        if not len(a):
            continue
        for k, col in (('level', 'level_diff'), ('chg21', 'chg21_diff')):
            rv = float(a[col].iloc[0])
            v = np.array(q2acc[(tag, k)], float); v = v[np.isfinite(v)]
            if not len(v):
                continue
            rank = int((np.abs(v) >= abs(rv)).sum()) + 1
            nrows.append(dict(block=tag, state='transition days',
                              statistic='Q2 %s difference' % k, real=rv,
                              n_shifts=len(v), null_mean=float(v.mean()),
                              null_sd=float(v.std()), rank_of_real=rank,
                              n_compared=len(v) + 1, p=rank / (len(v) + 1)))
            print('  %-4s Q2 %-6s real %+.4f | null %+.4f +/- %.4f over %d | '
                  'rank %d of %d | p=%.3f'
                  % (tag, k, rv, v.mean(), v.std(), len(v), rank, len(v) + 1,
                     rank / (len(v) + 1)))
    for tag, real in (('is', real_is), ('oos', real_oos)):
        v = np.array(acc[tag], float); v = v[np.isfinite(v)]
        rank = int((np.abs(v) >= abs(real)).sum()) + 1
        nrows.append(dict(block=tag, state=BEST, statistic='high-low share spread',
                          real=real, n_shifts=len(v), null_mean=float(v.mean()),
                          null_sd=float(v.std()), rank_of_real=rank,
                          n_compared=len(v) + 1, p=rank / (len(v) + 1)))
        print('  %-4s real %+.4f | null %+.4f +/- %.4f over %d shifts | '
              'rank %d of %d | p=%.3f'
              % (tag, real, v.mean(), v.std(), len(v), rank, len(v) + 1,
                 rank / (len(v) + 1)))
    N = pd.DataFrame(nrows)
    N.to_csv(os.path.join(ROOTOUT, 'move_null.csv'), index=False)
    hdr(os.path.join(ROOTOUT, 'move_null.csv'),
        'Null -- circular shift of MOVE against the state panel',
        'MOVE is rolled by a random offset of at least %d days and the terciles\n'
        'recut on the shifted series. Rank is TWO-SIDED on |spread| because the\n'
        'headline state was chosen on the magnitude of its in-sample spread.\n\n'
        'n_shifts is the exact draw count run.' % MINOFF)
    print('\nwrote move_{coverage,q1,q1_chg,q2,null}.csv + .txt')


if __name__ == '__main__':
    main()
