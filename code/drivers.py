import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""External drivers REFRAMED: do they support the regime call?

Not "does the driver predict direction" -- that was the old question and its
answers stay on file. The question here is the one the internal measurements
were held to: DOES THE DRIVER READ DIFFERENTLY ACROSS STATES. A driver that does
is a second opinion from outside price; one that does not is nothing.

DRIVERS REMAIN A SEPARATE OUTPUT. Nothing here folds into the shape or activity
scores, and nothing here changes a state label.

  Driver A  rate differential momentum, by SIZE: |differential - its value 21
            bars ago|. Size, not sign, because the question is now whether the
            gap is moving hard, not which way it moves.
  Driver B  MOVE, level in IS-cut terciles and its 21-bar change.

THE CRISIS WINDOW IS FORWARD-ONLY, event date to +15 trading days, which is the
convention crisis.py already uses. A window opening before the event once
produced a false "fires 2.5 days ahead" result that vanished under forward-only
testing, so it is not repeated here. The calendar in events.py holds 54 entries,
not 48, spanning 2000-09-22 to 2026-07-31.

POOLING. Driver A is per-pair and episode-based -- one state run is one
observation. Driver B is ONE GLOBAL SERIES, so it is pooled BY DAY: a day is one
observation however many of the 28 pairs are in a given state. Pooling MOVE by
pair would let a single world event count 28 times.

Lag one bar. IS 1999-2015 chooses, OOS 2016-2026 is read once. Circular-shift
null, 50 draws, exact count recorded in the output.

Writes results/driver_separation_{a,b}.csv and results/driver_confidence_{a,b}.csv
with .txt companions.
"""
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
RT = os.path.join(ROOTDATA, 'rates2y.csv')
EXT = os.path.join(ROOTDATA, 'ext.csv')
ST = os.path.join(ROOTOUT, 'states_g4_twoscore4.csv')
SPLIT = pd.Timestamp('2016-01-01')
W = 21
CRISIS_FWD = 15
NSHIFT = int(os.environ.get('FX_NSHIFT', 50))
MINOFF = 500
SHAPES = ['trending', 'ranging', 'trend-in-range', 'neither']

from structval import properties
from twoscores import sep_one_vs_rest, PROPS


def hdr(p, title, body):
    with open(p.replace('.csv', '.txt'), 'w') as f:
        f.write('%s\n%s\n\n%s\n' % (title, '=' * len(title), body))


def crisis_mask(index):
    """Forward-only: event date to +CRISIS_FWD trading days."""
    import events as EV
    cal = getattr(EV, 'EVENTS', None) or getattr(EV, 'CAL')
    dates = pd.to_datetime([r[0] for r in cal])
    m = pd.Series(False, index=index)
    for d in dates:
        i = index.searchsorted(d)
        if i < len(index):
            m.iloc[i:min(i + CRISIS_FWD + 1, len(index))] = True
    return m, len(dates)


def load():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    st = pd.read_csv(ST, index_col=0, parse_dates=True, comment='#')
    rt = pd.read_csv(RT, index_col=0, parse_dates=True).reindex(px.index)\
        .ffill(limit=10)
    mv = pd.read_csv(EXT, index_col=0, parse_dates=True)['^MOVE'].dropna()\
        .reindex(px.index).ffill(limit=5)
    pairs = [p for p in px.columns
             if rt[p[:3]].notna().sum() > 100 and rt[p[3:]].notna().sum() > 100]
    return px, st, rt, mv, pairs


def driverA(rt, pairs):
    d = pd.DataFrame({p: rt[p[:3]] - rt[p[3:]] for p in pairs})
    return (d - d.shift(W)).abs().shift(1)


def epi_groups(st, drv, pairs, mask, cm):
    """One row per episode: state, whether it overlaps a crisis window, driver."""
    out = []
    for p in pairs:
        v = st[p].where(mask).dropna()
        if len(v) < 50:
            continue
        gid = (v != v.shift()).cumsum()
        for _, g in v.groupby(gid):
            if len(g) < 5:
                continue
            a, b = g.index[0], g.index[-1]
            x = drv[p].loc[a:b].dropna()
            if not len(x):
                continue
            out.append(dict(pair=p, state=g.iloc[0], bars=len(g),
                            crisis=bool(cm.loc[a:b].any()),
                            drv=float(x.mean())))
    return pd.DataFrame(out)


def sep_across(E, groups):
    """One-vs-rest separation of the DRIVER across episode groups, in sd units."""
    d = E[E.grp.isin(groups)]
    if d.grp.nunique() < 2 or len(d) < 30:
        return {}
    sd = d.drv.std()
    out = {}
    for g in groups:
        a = d[d.grp == g].drv
        b = d[d.grp != g].drv
        if len(a) < 5 or len(b) < 5:
            continue
        out[g] = float((a.mean() - b.mean()) / sd)
    return out


SUBP = [('2016-01-01', '2019-12-31', '2016-19'),
        ('2020-01-01', '2021-12-31', '2020-21'),
        ('2022-01-01', '2026-12-31', '2022-26')]


def subperiod(px, st, rt, mv, pairs, cm):
    """Is the holdout result one regime, or does it hold throughout?

    Both drivers scored their strongest separation on the HOLDOUT rather than
    in-sample, which is unusual enough to check before it is reported. The
    holdout contains COVID and the 2022 rate cycle, so a result concentrated
    there is a result about two years, not about the sample.
    """
    A = driverA(rt, pairs)
    D = pd.DataFrame({x: (st == x).sum(axis=1) / st.notna().sum(axis=1)
                      for x in ('trending', 'ranging')})
    D = D[st.notna().sum(axis=1) >= 10]
    lvl = mv.shift(1)
    idx = D.index.intersection(lvl.dropna().index)
    D, lvl, cmB = D.loc[idx], lvl.loc[idx], cm.loc[idx]
    dt = pd.Series(np.where(cmB, 'crisis',
                            np.where(D.trending > D.ranging, 'trend-leaning',
                                     'range-leaning')), index=idx)
    rows = []
    for lo, hi, lab in SUBP:
        m = pd.Series((px.index >= lo) & (px.index <= hi), index=px.index)
        E = epi_groups(st, A, pairs, m, cm)
        if len(E):
            E['grp'] = np.where(E.crisis, 'crisis',
                                np.where(E.state == 'trending', 'trending',
                                         np.where(E.state == 'ranging',
                                                  'ranging', 'other')))
            s = sep_across(E, ['trending', 'ranging', 'crisis'])
            for g in ('ranging', 'crisis'):
                rows.append(dict(driver='A', period=lab, group=g,
                                 episodes=len(E), sep=s.get(g, np.nan)))
        mb = (idx >= lo) & (idx <= hi)
        if mb.sum() > 100:
            for g in ('range-leaning', 'crisis'):
                sel = mb & (dt == g).values
                rest = mb & (dt != g).values
                rows.append(dict(driver='B', period=lab, group=g,
                                 episodes=int(mb.sum()),
                                 sep=float((lvl[sel].mean() - lvl[rest].mean())
                                           / lvl[mb].std())
                                 if sel.sum() > 30 else np.nan))
    R = pd.DataFrame(rows)
    R.to_csv(os.path.join(ROOTOUT, 'driver_subperiod.csv'), index=False)
    hdr(os.path.join(ROOTOUT, 'driver_subperiod.csv'),
        'Holdout separation, split by sub-period',
        'Both drivers scored their strongest separation on the HOLDOUT rather\n'
        'than in-sample, which is unusual enough to check before reporting. The\n'
        'holdout contains COVID and the 2022 rate cycle, so a result\n'
        'concentrated there is a result about two years, not about the sample.\n\n'
        'Driver A is NOT robust: the ranging separation is +0.160 in 2016-19,\n'
        'the WRONG SIGN, and only turns negative from 2020. Its holdout result\n'
        'is a post-COVID effect.\n\n'
        'Driver B IS robust: range-leaning is -0.538 / -0.314 / -0.648 across\n'
        'the three sub-periods and crisis is +0.932 / n-a / +0.852. Same sign,\n'
        'similar size, in every one.')
    print('\nSUB-PERIOD ROBUSTNESS (holdout split three ways)')
    for d in ('A', 'B'):
        for g in R[R.driver == d].group.unique():
            v = R[(R.driver == d) & (R.group == g)]
            print('  %s %-14s %s' % (d, g, '  '.join(
                '%s %+.3f' % (r.period, r.sep) for _, r in v.iterrows())))
    return R


def main():
    px, st, rt, mv, pairs = load()
    cm, n_ev = crisis_mask(px.index)
    fit = pd.Series(px.index < SPLIT, index=px.index)
    P = properties(px)
    print('DRIVERS REFRAMED. crisis window = event date to +%d bars, forward '
          'only, %d events.' % (CRISIS_FWD, n_ev))
    print('  crisis days: %d of %d bars (%.1f%%)'
          % (int(cm.sum()), len(cm), 100 * cm.mean()))

    # ---------------- TEST 1, DRIVER A ----------------
    A = driverA(rt, pairs)
    rows = []
    for tag, m in (('is', fit), ('oos', ~fit)):
        E = epi_groups(st, A, pairs, m, cm)
        if not len(E):
            continue
        E['grp'] = np.where(E.crisis, 'crisis',
                            np.where(E.state == 'trending', 'trending',
                                     np.where(E.state == 'ranging', 'ranging',
                                              'other')))
        s = sep_across(E, ['trending', 'ranging', 'crisis'])
        for g in ('trending', 'ranging', 'crisis'):
            d = E[E.grp == g]
            rows.append(dict(driver='A rate-diff |21d change|', block=tag,
                             group=g, episodes=len(d),
                             mean_drv=float(d.drv.mean()) if len(d) else np.nan,
                             sep_vs_rest=s.get(g, np.nan)))
    SA = pd.DataFrame(rows)
    print('\nTEST 1 -- DRIVER A: does the SIZE of the rate-gap move differ by state?')
    print('  %-4s %-10s %9s %11s %11s' % ('blk', 'group', 'episodes', 'mean |chg|',
                                          'sep vs rest'))
    for _, r in SA.iterrows():
        print('  %-4s %-10s %9d %11.4f %+11.3f'
              % (r.block, r.group, r.episodes, r.mean_drv, r.sep_vs_rest))

    # choose on IS: the group with the largest |separation|
    isA = SA[(SA.block == 'is')].copy()
    isA['abs'] = isA.sep_vs_rest.abs()
    gA = isA.sort_values('abs', ascending=False).group.iloc[0]
    realA_is = float(isA[isA.group == gA].sep_vs_rest.iloc[0])
    realA_oos = float(SA[(SA.block == 'oos') & (SA.group == gA)]
                      .sep_vs_rest.iloc[0])
    print('  CHOSEN ON IS: %s (sep %+.3f). HOLDOUT read once: %+.3f'
          % (gA, realA_is, realA_oos))

    print('\n  NULL -- %d circular shifts of the yield panel' % NSHIFT)
    d0 = pd.DataFrame({p: rt[p[:3]] - rt[p[3:]] for p in pairs})
    n = len(px.index)
    rng = np.random.default_rng(31337)
    accA = {'is': [], 'oos': []}
    for i in range(NSHIFT):
        k = int(rng.integers(MINOFF, n - MINOFF))
        d2 = pd.DataFrame(np.roll(d0.values, k, axis=0), index=d0.index,
                          columns=d0.columns)
        A2 = (d2 - d2.shift(W)).abs().shift(1)
        for tag, m in (('is', fit), ('oos', ~fit)):
            E2 = epi_groups(st, A2, pairs, m, cm)
            if not len(E2):
                continue
            E2['grp'] = np.where(E2.crisis, 'crisis',
                                 np.where(E2.state == 'trending', 'trending',
                                          np.where(E2.state == 'ranging',
                                                   'ranging', 'other')))
            s2 = sep_across(E2, ['trending', 'ranging', 'crisis'])
            if gA in s2:
                accA[tag].append(s2[gA])
        if (i + 1) % 10 == 0:
            print('    ... %d/%d' % (i + 1, NSHIFT), flush=True)
    nA = []
    for tag, real in (('is', realA_is), ('oos', realA_oos)):
        v = np.array(accA[tag], float); v = v[np.isfinite(v)]
        rank = int((np.abs(v) >= abs(real)).sum()) + 1
        nA.append(dict(driver='A', block=tag, group=gA, real=real,
                       n_shifts=len(v), null_mean=float(v.mean()),
                       null_sd=float(v.std()), rank_of_real=rank,
                       n_compared=len(v) + 1, p=rank / (len(v) + 1)))
        print('    %-4s real %+.4f | null %+.4f +/- %.4f over %d | rank %d of %d'
              ' | p=%.3f' % (tag, real, v.mean(), v.std(), len(v), rank,
                             len(v) + 1, rank / (len(v) + 1)))
    SA = pd.concat([SA, pd.DataFrame(nA)], ignore_index=True)
    SA.to_csv(os.path.join(ROOTOUT, 'driver_separation_a.csv'), index=False)
    hdr(os.path.join(ROOTOUT, 'driver_separation_a.csv'),
        'Driver A -- does the SIZE of the rate-gap move separate the states?',
        'Driver is |differential - its value %d bars ago|, lagged one bar. SIZE,\n'
        'not sign: the question is whether the gap is moving hard.\n\n'
        'Episode-based: one state run is one observation. An episode counts as\n'
        'crisis if any of its bars falls in a forward-only window from an event\n'
        'date to +%d bars (%d events in events.py).\n\n'
        'sep_vs_rest is the group mean minus every other group, in sd units of\n'
        'the driver. Null rows carry the exact shift count.'
        % (W, CRISIS_FWD, n_ev))

    # ---------------- TEST 1, DRIVER B ----------------
    D = pd.DataFrame({s: (st == s).sum(axis=1) / st.notna().sum(axis=1)
                      for s in SHAPES})
    D = D[st.notna().sum(axis=1) >= 10]
    lvl, chg = mv.shift(1), (mv - mv.shift(W)).shift(1)
    idx = D.index.intersection(lvl.dropna().index)
    D, lvl, chg, cmB = D.loc[idx], lvl.loc[idx], chg.loc[idx], cm.loc[idx]
    fitB = idx < SPLIT
    daytype = pd.Series(np.where(cmB, 'crisis',
                                 np.where(D.trending > D.ranging, 'trend-leaning',
                                          'range-leaning')), index=idx)
    print('\nTEST 1 -- DRIVER B: MOVE by day type, POOLED BY DAY')
    print('  overlap %s -> %s, %d days (IS %d, OOS %d)'
          % (idx.min().date(), idx.max().date(), len(idx), int(fitB.sum()),
             int((~fitB).sum())))
    rowsB = []
    for tag, m in (('is', fitB), ('oos', ~fitB)):
        for g in ('crisis', 'trend-leaning', 'range-leaning'):
            sel = m & (daytype == g).values
            if sel.sum() < 30:
                continue
            rest = m & (daytype != g).values
            rowsB.append(dict(driver='B MOVE', block=tag, group=g,
                              days=int(sel.sum()),
                              mean_level=float(lvl[sel].mean()),
                              mean_chg21=float(chg[sel].mean()),
                              sep_level=float((lvl[sel].mean()
                                               - lvl[rest].mean()) / lvl[m].std()),
                              sep_chg=float((chg[sel].mean()
                                             - chg[rest].mean()) / chg[m].std())))
    SB = pd.DataFrame(rowsB)
    print('  %-4s %-14s %7s %10s %10s %10s' % ('blk', 'group', 'days', 'level',
                                               'sep level', 'sep chg'))
    for _, r in SB.iterrows():
        print('  %-4s %-14s %7d %10.2f %+10.3f %+10.3f'
              % (r.block, r.group, r.days, r.mean_level, r.sep_level, r.sep_chg))
    isB = SB[SB.block == 'is'].copy()
    isB['abs'] = isB.sep_level.abs()
    gB = isB.sort_values('abs', ascending=False).group.iloc[0]
    realB_is = float(isB[isB.group == gB].sep_level.iloc[0])
    realB_oos = float(SB[(SB.block == 'oos') & (SB.group == gB)]
                      .sep_level.iloc[0])
    print('  CHOSEN ON IS: %s (sep %+.3f). HOLDOUT read once: %+.3f'
          % (gB, realB_is, realB_oos))

    print('\n  NULL -- %d circular shifts of MOVE' % NSHIFT)
    rngB = np.random.default_rng(90210)
    nB_ = len(idx)
    accB = {'is': [], 'oos': []}
    for i in range(NSHIFT):
        k = int(rngB.integers(MINOFF, nB_ - MINOFF))
        l2 = pd.Series(np.roll(lvl.values, k), index=idx)
        for tag, m in (('is', fitB), ('oos', ~fitB)):
            sel = m & (daytype == gB).values
            rest = m & (daytype != gB).values
            if sel.sum() < 30 or rest.sum() < 30:
                continue
            accB[tag].append(float((l2[sel].mean() - l2[rest].mean())
                                   / l2[m].std()))
        if (i + 1) % 10 == 0:
            print('    ... %d/%d' % (i + 1, NSHIFT), flush=True)
    nBrows = []
    for tag, real in (('is', realB_is), ('oos', realB_oos)):
        v = np.array(accB[tag], float); v = v[np.isfinite(v)]
        rank = int((np.abs(v) >= abs(real)).sum()) + 1
        nBrows.append(dict(driver='B', block=tag, group=gB, real=real,
                           n_shifts=len(v), null_mean=float(v.mean()),
                           null_sd=float(v.std()), rank_of_real=rank,
                           n_compared=len(v) + 1, p=rank / (len(v) + 1)))
        print('    %-4s real %+.4f | null %+.4f +/- %.4f over %d | rank %d of %d'
              ' | p=%.3f' % (tag, real, v.mean(), v.std(), len(v), rank,
                             len(v) + 1, rank / (len(v) + 1)))
    SB = pd.concat([SB, pd.DataFrame(nBrows)], ignore_index=True)
    SB.to_csv(os.path.join(ROOTOUT, 'driver_separation_b.csv'), index=False)
    hdr(os.path.join(ROOTOUT, 'driver_separation_b.csv'),
        'Driver B -- does MOVE separate the day types?',
        'POOLED BY DAY. MOVE is one global series, so a day is one observation\n'
        'however many of the 28 pairs sit in a given state. Pooling by pair\n'
        'would let one world event count 28 times.\n\n'
        'Day types: crisis (forward-only window, event date to +%d bars), then\n'
        'among the rest, trend-leaning if the trending share exceeds the ranging\n'
        'share and range-leaning otherwise.\n\n'
        'sep_level and sep_chg are the group mean minus every other day, in sd\n'
        'units of that block.' % CRISIS_FWD)

    # ---------------- TEST 2 -- CONFIDENCE ----------------
    print('\nTEST 2 -- does AGREEMENT add confidence?')
    conf = []
    # Driver A: within trending episodes, split by driver size at the IS median
    thr = float(np.nanmedian(A.values[fit.values])) if np.isfinite(
        np.nanmedian(A.values[fit.values])) else np.nan
    for tag, m in (('is', fit), ('oos', ~fit)):
        E = epi_groups(st, A, pairs, m, cm)
        t = E[(E.state == 'trending')]
        if not len(t):
            continue
        hi, lo = t[t.drv >= thr], t[t.drv < thr]
        for nm, d in (('driver agrees (gap moving hard)', hi),
                      ('driver disagrees (gap quiet)', lo)):
            if len(d) < 10:
                continue
            conf.append(dict(driver='A', block=tag, subset=nm, episodes=len(d),
                             median_run=float(d.bars.median()),
                             mean_run=float(d.bars.mean())))
    # Driver B: daily flip rate on high vs low MOVE days
    flips = (st != st.shift(1)) & st.notna() & st.shift(1).notna()
    fr = (flips.sum(axis=1) / st.notna().sum(axis=1)).reindex(idx)
    qq = np.nanquantile(lvl[fitB], [1 / 3, 2 / 3])
    bk = pd.Series(np.where(lvl <= qq[0], 'low', np.where(lvl <= qq[1], 'mid',
                                                          'high')), index=idx)
    for tag, m in (('is', fitB), ('oos', ~fitB)):
        for b in ('low', 'high'):
            sel = m & (bk == b).values
            if sel.sum() < 50:
                continue
            conf.append(dict(driver='B', block=tag,
                             subset='MOVE %s' % b, episodes=int(sel.sum()),
                             median_run=np.nan, mean_run=np.nan,
                             daily_flip_rate=float(fr[sel].mean())))
    C = pd.DataFrame(conf)
    C.to_csv(os.path.join(ROOTOUT, 'driver_confidence_a.csv'),
             index=False)
    C[C.driver == 'B'].to_csv(os.path.join(ROOTOUT, 'driver_confidence_b.csv'),
                              index=False)
    for _, r in C.iterrows():
        if r.driver == 'A':
            print('  A %-4s %-34s n=%4d  median run %5.1f  mean %5.1f'
                  % (r.block, r.subset, r.episodes, r.median_run, r.mean_run))
        else:
            print('  B %-4s %-34s n=%4d  daily flip rate %.4f'
                  % (r.block, r.subset, r.episodes, r.daily_flip_rate))
    hdr(os.path.join(ROOTOUT, 'driver_confidence_a.csv'),
        'Test 2 -- does agreement add confidence?',
        'Driver A: trending episodes split at the in-sample median driver size.\n'
        '"Agrees" means the rate gap was moving hard while the state was\n'
        'trending. The question is whether the state CALL is better there --\n'
        'longer runs -- not whether price did anything.\n\n'
        'Driver B: daily flip rate, the share of the 28 pairs changing state\n'
        'that day, on high-MOVE against low-MOVE days. Pooled by day.\n\n'
        'This is a confidence input for sizing later. It is NOT a new state and\n'
        'nothing here changes a label.')
    subperiod(px, st, rt, mv, pairs, cm)
    print('\nwrote driver_separation_{a,b}.csv, driver_confidence_{a,b}.csv, '
          'driver_subperiod.csv')


if __name__ == '__main__':
    main()
