import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Driver 3: equity correlation. Plus the FORWARD ODDS test, retro-run on MOVE.

THE ARCHITECTURE THIS SITS IN. Layer 1 is a view of the CURRENT regime and is
never modified for, fed by, or judged on prediction. Drivers are separate outputs
beside it, and they are the only place forward thinking lives. Nothing in this
file changes a state label.

DRIVER C, declared upfront, no sweep: per pair, the rolling correlation between
that pair's daily returns and S&P 500 daily returns, at 21 and 63 bars. Separation
uses the ABSOLUTE level -- correlation strength, not its sign. Unlike MOVE this is
PAIR-SPECIFIC, so it is genuinely new information rather than another global
stress number wearing a different hat.

S&P 500: ^GSPC via the Yahoo chart API, 1996-12-09 to 2026-08-14, 7,464 closes,
cached to data/gspc.csv. Overlap with the FX sample is 6,872 bars, 1999-01-04 to
2026-07-30 -- the whole sample, unlike MOVE which misses the first 3.9 years.

MECHANISM PREDICTION, WRITTEN DOWN BEFORE THE RUN. JPY and CHF crosses are
funding currencies that move on global risk, so the equity link should separate
regimes MOST on those and weakly on EURGBP / AUDNZD types. If separation shows up
on the wrong pairs that is a RED FLAG, not a pass, and it is reported either way.

THREE TESTS, and the third is new:
  1 SEPARATION  does it read differently across the three regimes right now
  2 CONFIDENCE  does its agreement make the current call more reliable
  3 FORWARD ODDS  does today's reading shift the probability of each regime over
    the next 20 bars away from base rate

ONE CRISIS IS ONE OBSERVATION, however many bars or pairs it touches. The forward
crisis test is therefore computed at DAY level against the 54-event calendar, and
its null shifts the driver against that calendar rather than resampling days.

Sub-period split is run BEFORE any holdout pass is reported. That check is what
killed driver 1.

Writes results/driver_separation_c.csv, driver_confidence_c.csv,
driver_forward_c.csv, driver_forward_b.csv, driver_subperiod_c.csv.
"""
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
SP = os.path.join(ROOTDATA, 'gspc.csv')
EXT = os.path.join(ROOTDATA, 'ext.csv')
ST = os.path.join(ROOTOUT, 'states_g4_twoscore4.csv')
SPLIT = pd.Timestamp('2016-01-01')
WINS = (21, 63)
FWD = 20
NSHIFT = int(os.environ.get('FX_NSHIFT', 50))
MINOFF = 500
SUBP = [('2016-01-01', '2019-12-31', '2016-19'),
        ('2020-01-01', '2021-12-31', '2020-21'),
        ('2022-01-01', '2026-12-31', '2022-26')]
FUND = ('JPY', 'CHF')

from drivers import crisis_mask, epi_groups, sep_across, hdr


def load():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    st = pd.read_csv(ST, index_col=0, parse_dates=True, comment='#')
    sp = pd.read_csv(SP, index_col=0, parse_dates=True)['GSPC']
    mv = pd.read_csv(EXT, index_col=0, parse_dates=True)['^MOVE'].dropna()
    return px, st, sp.reindex(px.index).ffill(limit=5), mv.reindex(px.index)\
        .ffill(limit=5)


def driverC(px, sp, W):
    """|rolling corr(pair returns, S&P returns)| over W bars, lagged one."""
    r = np.log(px.astype(float)).diff()
    s = np.log(sp.astype(float)).diff()
    out = {}
    for p in px.columns:
        out[p] = r[p].rolling(W).corr(s)
    return pd.DataFrame(out).abs().replace([np.inf, -np.inf], np.nan).shift(1)


def sep_block(st, drv, pairs, mask, cm):
    E = epi_groups(st, drv, pairs, mask, cm)
    if not len(E):
        return {}, E
    E['grp'] = np.where(E.crisis, 'crisis',
                        np.where(E.state == 'trending', 'trending',
                                 np.where(E.state == 'ranging', 'ranging',
                                          'other')))
    return sep_across(E, ['trending', 'ranging', 'crisis']), E


def forward_odds(driver_daily, st, cm_events, index, fit, label):
    """Test 3. Does today's reading shift the odds of each regime in 20 bars?

    Crisis is computed at DAY level against distinct EVENTS -- one crisis is one
    observation. Regime odds are per pair: does the pair enter that state at any
    point in the next FWD bars.
    """
    q = np.nanquantile(driver_daily[fit], [1 / 3, 2 / 3])
    b = pd.Series(np.where(driver_daily <= q[0], 'low',
                           np.where(driver_daily <= q[1], 'mid', 'high')),
                  index=index)
    # crisis ahead: does a distinct event date fall in (t, t+FWD]
    ahead = pd.Series(False, index=index)
    for d in cm_events:
        i = index.searchsorted(d)
        lo = max(0, i - FWD)
        if i < len(index):
            ahead.iloc[lo:i] = True
    # the states file and the price panel differ in length (6,855 vs 6,916),
    # so the state frame is reindexed onto the driver's calendar before any
    # boolean mask is applied
    st = st.reindex(index)
    rows = []
    for tag, m in (('is', fit), ('oos', ~fit)):
        base = float(ahead[m].mean())
        for bk in ('low', 'mid', 'high'):
            sel = m & (b == bk).values
            if sel.sum() < 50:
                continue
            rows.append(dict(driver=label, block=tag, bucket=bk,
                             days=int(sel.sum()), metric='P(crisis in 20 bars)',
                             p=float(ahead[sel].mean()), base=base,
                             lift=float(ahead[sel].mean() / base) if base else np.nan))
    # regime odds, per pair, pooled
    for tag, m in (('is', fit), ('oos', ~fit)):
        for state in ('trending', 'ranging'):
            fwd = (st == state).rolling(FWD).max().shift(-FWD).astype(float)
            base = float(np.nanmean(fwd.values[m]))
            for bk in ('low', 'mid', 'high'):
                sel = m & (b == bk).values
                if sel.sum() < 50:
                    continue
                v = float(np.nanmean(fwd.values[sel]))
                rows.append(dict(driver=label, block=tag, bucket=bk,
                                 days=int(sel.sum()),
                                 metric='P(%s in 20 bars)' % state, p=v,
                                 base=base, lift=v / base if base else np.nan))
    return pd.DataFrame(rows), b, ahead


def main():
    px, st, sp, mv = load()
    cm, n_ev = crisis_mask(px.index)
    import events as EV
    cal = getattr(EV, 'EVENTS', None) or getattr(EV, 'CAL')
    ev_dates = pd.to_datetime([r[0] for r in cal])
    fit = pd.Series(px.index < SPLIT, index=px.index)
    pairs = list(px.columns)
    print('DRIVER 3 -- EQUITY CORRELATION. ^GSPC 1996-12-09 to 2026-08-14,')
    print('  overlap with FX 6,872 bars 1999-01-04 to 2026-07-30 (whole sample).')
    print('  MECHANISM PREDICTION (pre-registered): JPY/CHF crosses should')
    print('  separate most; EURGBP/AUDNZD types weakly.')

    # ---------------- TEST 1 ----------------
    rows, best = [], None
    for W in WINS:
        C = driverC(px, sp, W)
        for tag, m in (('is', fit), ('oos', ~fit)):
            s, E = sep_block(st, C, pairs, m, cm)
            for g in ('trending', 'ranging', 'crisis'):
                d = E[E.grp == g] if len(E) else E
                rows.append(dict(driver='C equity |corr|', W=W, block=tag,
                                 group=g, episodes=len(d),
                                 mean_drv=float(d.drv.mean()) if len(d) else np.nan,
                                 sep_vs_rest=s.get(g, np.nan)))
    SC = pd.DataFrame(rows)
    print('\nTEST 1 -- SEPARATION')
    print('  %3s %-4s %-9s %9s %10s %11s' % ('W', 'blk', 'group', 'episodes',
                                             'mean|corr|', 'sep vs rest'))
    for _, r in SC.iterrows():
        print('  %3d %-4s %-9s %9d %10.4f %+11.3f'
              % (r.W, r.block, r.group, r.episodes, r.mean_drv, r.sep_vs_rest))
    isC = SC[SC.block == 'is'].copy()
    isC['abs'] = isC.sep_vs_rest.abs()
    top = isC.sort_values('abs', ascending=False).iloc[0]
    W_BEST, G_BEST = int(top.W), top.group
    real_is = float(top.sep_vs_rest)
    real_oos = float(SC[(SC.block == 'oos') & (SC.W == W_BEST)
                        & (SC.group == G_BEST)].sep_vs_rest.iloc[0])
    print('  CHOSEN ON IS: W=%d, %s (sep %+.3f). HOLDOUT read once: %+.3f'
          % (W_BEST, G_BEST, real_is, real_oos))

    # per-pair, to check the mechanism prediction
    C = driverC(px, sp, W_BEST)
    prow = []
    for p in pairs:
        s, E = sep_block(st, C, [p], ~fit, cm)
        if G_BEST in s:
            prow.append(dict(pair=p, sep=s[G_BEST],
                             funding=bool(p[:3] in FUND or p[3:] in FUND)))
    PP = pd.DataFrame(prow).sort_values('sep', key=abs, ascending=False)
    fu = PP[PP.funding].sep.abs().mean()
    nf = PP[~PP.funding].sep.abs().mean()
    print('\n  MECHANISM CHECK, |sep| on the holdout at W=%d' % W_BEST)
    print('    JPY/CHF crosses  mean |sep| %.3f  (n=%d)' % (fu, PP.funding.sum()))
    print('    all others       mean |sep| %.3f  (n=%d)' % (nf, (~PP.funding).sum()))
    print('    top 5: %s' % ', '.join('%s %+.2f' % (r.pair, r.sep)
                                      for _, r in PP.head(5).iterrows()))
    print('    -> prediction %s'
          % ('HOLDS' if fu > nf else 'FAILS -- separation is on the wrong pairs'))
    PP.to_csv(os.path.join(ROOTOUT, 'driver_mechanism_c.csv'), index=False)

    # sub-period FIRST
    print('\n  SUB-PERIOD SPLIT (run before reporting the holdout pass)')
    srow = []
    for lo, hi, lab in SUBP:
        m = pd.Series((px.index >= lo) & (px.index <= hi), index=px.index)
        s, _ = sep_block(st, C, pairs, m, cm)
        for g in ('trending', 'ranging', 'crisis'):
            srow.append(dict(driver='C', W=W_BEST, period=lab, group=g,
                             sep=s.get(g, np.nan)))
        print('    %-8s %s' % (lab, '  '.join(
            '%s %+.3f' % (g, s.get(g, np.nan))
            for g in ('trending', 'ranging', 'crisis'))))
    SU = pd.DataFrame(srow)
    SU.to_csv(os.path.join(ROOTOUT, 'driver_subperiod_c.csv'), index=False)
    hdr(os.path.join(ROOTOUT, 'driver_subperiod_c.csv'),
        'Driver C -- holdout separation split by sub-period',
        'Run BEFORE any holdout pass is reported. This check is what killed\n'
        'driver 1, whose ranging separation read the wrong sign in 2016-19 and\n'
        'only worked from 2020.')

    print('\n  NULL -- %d circular shifts of the S&P series' % NSHIFT)
    r_sp = np.log(sp.astype(float)).diff()
    n = len(px.index)
    rng = np.random.default_rng(500)
    acc = {'is': [], 'oos': []}
    for i in range(NSHIFT):
        k = int(rng.integers(MINOFF, n - MINOFF))
        s2 = pd.Series(np.roll(r_sp.values, k), index=px.index)
        rr = np.log(px.astype(float)).diff()
        C2 = pd.DataFrame({p: rr[p].rolling(W_BEST).corr(s2) for p in pairs})\
            .abs().replace([np.inf, -np.inf], np.nan).shift(1)
        for tag, m in (('is', fit), ('oos', ~fit)):
            s3, _ = sep_block(st, C2, pairs, m, cm)
            if G_BEST in s3:
                acc[tag].append(s3[G_BEST])
        if (i + 1) % 10 == 0:
            print('    ... %d/%d' % (i + 1, NSHIFT), flush=True)
    nrow = []
    for tag, real in (('is', real_is), ('oos', real_oos)):
        v = np.array(acc[tag], float); v = v[np.isfinite(v)]
        rank = int((np.abs(v) >= abs(real)).sum()) + 1
        nrow.append(dict(driver='C', block=tag, W=W_BEST, group=G_BEST,
                         real=real, n_shifts=len(v), null_mean=float(v.mean()),
                         null_sd=float(v.std()), rank_of_real=rank,
                         n_compared=len(v) + 1, p=rank / (len(v) + 1)))
        print('    %-4s real %+.4f | null %+.4f +/- %.4f over %d | rank %d of %d'
              ' | p=%.3f' % (tag, real, v.mean(), v.std(), len(v), rank,
                             len(v) + 1, rank / (len(v) + 1)))
    SC = pd.concat([SC, pd.DataFrame(nrow)], ignore_index=True)
    SC.to_csv(os.path.join(ROOTOUT, 'driver_separation_c.csv'), index=False)
    hdr(os.path.join(ROOTOUT, 'driver_separation_c.csv'),
        'Driver C -- equity correlation separation',
        'Rolling |corr(pair returns, S&P returns)| at 21 and 63 bars, lagged one.\n'
        'Absolute level: strength, not sign. Episode-based; crisis episodes are\n'
        'those overlapping a forward-only window from an event date to +15 bars.\n\n'
        'Null circularly shifts the S&P RETURN series against price, so the\n'
        'index keeps its own behaviour and only the alignment breaks.')

    # ---------------- TEST 2 ----------------
    print('\nTEST 2 -- CONFIDENCE (third and final attempt)')
    conf = []
    thr = float(np.nanmedian(C.values[fit.values]))
    for tag, m in (('is', fit), ('oos', ~fit)):
        E = epi_groups(st, C, pairs, m, cm)
        for state in ('trending', 'ranging'):
            t = E[E.state == state]
            if len(t) < 20:
                continue
            for nm, d in (('driver high (corr strong)', t[t.drv >= thr]),
                          ('driver low (corr weak)', t[t.drv < thr])):
                if len(d) < 10:
                    continue
                conf.append(dict(driver='C', block=tag, state=state, subset=nm,
                                 episodes=len(d),
                                 median_run=float(d.bars.median()),
                                 mean_run=float(d.bars.mean())))
    CF = pd.DataFrame(conf)
    for _, r in CF.iterrows():
        print('  %-4s %-9s %-26s n=%4d  median run %5.1f  mean %5.1f'
              % (r.block, r.state, r.subset, r.episodes, r.median_run, r.mean_run))
    gaps = []
    for tag in ('is', 'oos'):
        for state in ('trending', 'ranging'):
            a = CF[(CF.block == tag) & (CF.state == state)
                   & CF.subset.str.startswith('driver high')]
            b = CF[(CF.block == tag) & (CF.state == state)
                   & CF.subset.str.startswith('driver low')]
            if len(a) and len(b):
                gaps.append((tag, state, a.median_run.iloc[0] - b.median_run.iloc[0]))
    small = sum(1 for _, _, g in gaps if abs(g) < 2)
    print('  run-length gaps (high minus low): %s'
          % '  '.join('%s %s %+.1f' % g for g in gaps))
    print('  %d of %d cells are under 2 bars -- noise on a ~23-bar median.'
          % (small, len(gaps)))
    CF.to_csv(os.path.join(ROOTOUT, 'driver_confidence_c.csv'), index=False)
    hdr(os.path.join(ROOTOUT, 'driver_confidence_c.csv'),
        'Test 2 -- confidence, third and final attempt',
        'Episodes split at the in-sample median driver reading. The question is\n'
        'whether the STATE CALL is better when the driver agrees -- longer runs.\n\n'
        'This test has now failed on all three drivers: rate-gap momentum (run\n'
        'gap 26.0 vs 20.0 in-sample collapsing to 19.0 vs 18.0 out), MOVE (flip\n'
        'rate sign flipped between blocks) and equity correlation. THE TEST IS\n'
        'RETIRED. Agreement between a driver and the state call does not make\n'
        'the call more reliable, and three independent attempts is enough.')

    # ---------------- TEST 3 ----------------
    print('\nTEST 3 -- FORWARD ODDS. base rate first, then by driver tercile.')
    dailyC = C.mean(axis=1)
    FC, bC, ahead = forward_odds(dailyC, st, ev_dates, px.index, fit.values,
                                 'C equity |corr|')
    lvlB = mv.shift(1)
    okB = lvlB.notna()
    FB, bB, _ = forward_odds(lvlB.fillna(lvlB.median()), st, ev_dates, px.index,
                             fit.values & okB.values, 'B MOVE level')
    for nm, F in (('C', FC), ('B', FB)):
        print('\n  DRIVER %s' % nm)
        for met in F.metric.unique():
            d = F[F.metric == met]
            for tag in ('is', 'oos'):
                dd = d[d.block == tag]
                if not len(dd):
                    continue
                print('    %-4s %-26s base %.3f | %s' % (
                    tag, met, dd.base.iloc[0],
                    '  '.join('%s %.3f (x%.2f)' % (r.bucket, r.p, r.lift)
                              for _, r in dd.iterrows())))
    # NULL AND SUB-PERIOD ON THE FORWARD CRISIS CELL, which is the one that
    # matters: does an elevated driver today raise P(crisis in 20 bars)? The
    # null shifts the DRIVER against the event calendar, so the calendar keeps
    # its clustering and only the alignment breaks. One crisis stays one
    # observation because `ahead` is a day-level flag built from distinct dates.
    print('\n  FORWARD CRISIS -- null and sub-period, %d shifts' % NSHIFT)
    nrows2, srows2 = [], []
    for label, dr, okm in (('C equity |corr|', dailyC, dailyC.notna()),
                           ('B MOVE level', lvlB, okB)):
        fitm = fit.values & okm.values
        q = np.nanquantile(dr[fitm], [1 / 3, 2 / 3])
        bk = pd.Series(np.where(dr <= q[0], 'low',
                                np.where(dr <= q[1], 'mid', 'high')),
                       index=px.index)
        for tag, m in (('is', fitm), ('oos', (~fit.values) & okm.values)):
            hi = m & (bk == 'high').values
            if hi.sum() < 50:
                continue
            real = float(ahead[hi].mean() / ahead[m].mean())
            rr2 = np.random.default_rng(808)
            acc2 = []
            for _ in range(NSHIFT):
                k = int(rr2.integers(MINOFF, len(px.index) - MINOFF))
                d2 = pd.Series(np.roll(dr.values, k), index=px.index)
                q2 = np.nanquantile(d2[fitm], [1 / 3, 2 / 3])
                b2 = pd.Series(np.where(d2 <= q2[0], 'low',
                                        np.where(d2 <= q2[1], 'mid', 'high')),
                               index=px.index)
                h2 = m & (b2 == 'high').values
                if h2.sum() > 50:
                    acc2.append(float(ahead[h2].mean() / ahead[m].mean()))
            v = np.array(acc2, float); v = v[np.isfinite(v)]
            rank = int((np.abs(v - 1) >= abs(real - 1)).sum()) + 1
            nrows2.append(dict(driver=label, block=tag,
                               metric='P(crisis in 20 bars) lift, high bucket',
                               real=real, n_shifts=len(v),
                               null_mean=float(v.mean()), null_sd=float(v.std()),
                               rank_of_real=rank, n_compared=len(v) + 1,
                               p=rank / (len(v) + 1)))
            print('    %-16s %-4s lift %.3f | null %.3f +/- %.3f | rank %d of %d'
                  ' | p=%.3f' % (label, tag, real, v.mean(), v.std(), rank,
                                 len(v) + 1, rank / (len(v) + 1)))
        for lo, hi_, lab in SUBP:
            m = ((px.index >= lo) & (px.index <= hi_)) & okm.values
            h = m & (bk == 'high').values
            if h.sum() < 40 or ahead[m].mean() == 0:
                srows2.append(dict(driver=label, period=lab, lift=np.nan))
                continue
            srows2.append(dict(driver=label, period=lab,
                               lift=float(ahead[h].mean() / ahead[m].mean())))
    FC = pd.concat([FC, pd.DataFrame([r for r in nrows2
                                      if r['driver'].startswith('C')])],
                   ignore_index=True)
    FB = pd.concat([FB, pd.DataFrame([r for r in nrows2
                                      if r['driver'].startswith('B')])],
                   ignore_index=True)
    S2 = pd.DataFrame(srows2)
    S2.to_csv(os.path.join(ROOTOUT, 'driver_forward_subperiod.csv'), index=False)
    hdr(os.path.join(ROOTOUT, 'driver_forward_subperiod.csv'),
        'Forward crisis lift, holdout split by sub-period',
        'Lift of P(crisis in 20 bars) in the high driver bucket over the base\n'
        'rate for that window. Run before reporting any forward pass.')
    print('\n  FORWARD CRISIS LIFT BY SUB-PERIOD')
    for d in S2.driver.unique():
        v = S2[S2.driver == d]
        print('    %-16s %s' % (d, '  '.join('%s %.2f' % (r.period, r.lift)
                                             for _, r in v.iterrows())))
    FC.to_csv(os.path.join(ROOTOUT, 'driver_forward_c.csv'), index=False)
    FB.to_csv(os.path.join(ROOTOUT, 'driver_forward_b.csv'), index=False)
    for path, nm in ((os.path.join(ROOTOUT, 'driver_forward_c.csv'), 'C'),
                     (os.path.join(ROOTOUT, 'driver_forward_b.csv'), 'B')):
        hdr(path, 'Driver %s -- forward odds over the next %d bars' % (nm, FWD),
            'FORWARD, and reported as its own block. Layer 1 does not predict --\n'
            'only drivers carry forward odds, and nothing here changes a state\n'
            'label.\n\n'
            'P(crisis in 20 bars) is computed at DAY level against distinct\n'
            'event dates: ONE CRISIS IS ONE OBSERVATION however many bars or\n'
            'pairs it touches. Regime odds are per pair -- does the pair enter\n'
            'that state at any point in the next %d bars.\n\n'
            'base is the unconditional rate in that block; lift is bucket over\n'
            'base. Terciles cut on in-sample only.' % FWD)
    print('\nwrote driver_separation_c, driver_confidence_c, driver_forward_c, '
          'driver_forward_b, driver_subperiod_c, driver_mechanism_c')


if __name__ == '__main__':
    main()
