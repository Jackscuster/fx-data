"""CHECK 1 — the worst dip on ichimoku + sma full_nnfx (jack), 2010-2015.

Jack, 24 Nov: worst_dip_R 54.9 against a worst YEAR of -3.78 and 147 trades a
year. Print the daily mark-to-market curve, the five deepest dips with dates
and depths, the positions open at each trough, and confirm the dip is this one
strategy's unseen years only. Say what caused it, or fix worst_dip_R.
"""
import os, sys
_R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_R, 'code'))
os.chdir(_R)
ROOTOUT = os.path.join(_R, 'results')

import numpy as np, pandas as pd
import nnfx1 as N, nnfx2s as S2, l2sweep as S

OUT = os.path.join(ROOTOUT, 'nnfx')
BUILD = tuple(range(2010, 2016))
C1, BASE, VAR, RS = 'ichimoku_signals', 'sma_baseline', 'jack', 'full_nnfx'


def build_frames():
    """Return (TT_as_stage_report_built_it, per-step frames)."""
    W = pd.read_csv(os.path.join(OUT, 'stage2_picks_walk.csv'))
    S.load_costs(os.environ.get('FX_COST_TABLE', 'results/cost_table_h22.csv'))
    per = {}
    for stp in S2.STEPS:
        if stp['trade'] not in BUILD:
            continue
        w = W[(W.c1 == C1) & (W.base == BASE) & (W.variant == VAR)
              & (W.ruleset == RS) & (W.step == stp['name'])]
        assert len(w), stp['name']
        w = w.iloc[0]
        T = S2.run_combo(C1, w.picked_c1_setting, BASE, w.picked_base_setting,
                         VAR, RS, use_hourly=True)
        T = T[pd.DatetimeIndex(T.exit_date).year == stp['trade']].copy()
        T['step'] = stp['name']; T['step_trade_year'] = stp['trade']
        T['picked_c1'] = w.picked_c1_setting
        T['picked_base'] = w.picked_base_setting
        per[stp['trade']] = T
        print('  step %s -> %d legs, c1 %s / base %s'
              % (stp['name'], len(T), w.picked_c1_setting,
                 w.picked_base_setting), flush=True)
    TT = pd.concat([per[y] for y in sorted(per)], ignore_index=True)
    return TT, per


def deepest_dips(DS, years, k=5):
    """The k deepest NON-OVERLAPPING peak-to-trough dips on the daily curve."""
    d = DS[pd.DatetimeIndex(DS.date).year.isin(list(years))].reset_index(drop=True)
    eq = np.cumsum(d.R.to_numpy(float))
    dt = pd.DatetimeIndex(d.date)
    runmax = np.maximum.accumulate(eq)
    dd = runmax - eq
    used = np.zeros(len(eq), bool)
    out = []
    for _ in range(k):
        cand = np.where(used, -1.0, dd)
        t = int(np.argmax(cand))
        if cand[t] <= 0:
            break
        # the peak that this trough draws down from
        p = int(np.argmax(eq[:t + 1]))
        # recovery: first bar after t reaching the peak again, else end
        after = np.where(eq[t:] >= eq[p])[0]
        rec = t + int(after[0]) if len(after) else len(eq) - 1
        out.append(dict(rank=len(out) + 1, peak_date=dt[p], trough_date=dt[t],
                        recover_date=dt[rec], depth_R=float(dd[t]),
                        peak_eq_R=float(eq[p]), trough_eq_R=float(eq[t]),
                        days_peak_to_trough=int((dt[t] - dt[p]).days),
                        days_to_recover=(int((dt[rec] - dt[t]).days)
                                         if len(after) else -1)))
        used[p:rec + 1] = True
    return pd.DataFrame(out), d, eq


def open_at(TT, day):
    """Positions open on `day`, one row per ENTRY (not per leg)."""
    E = N.entry_frame(TT)
    ed = pd.DatetimeIndex(E.entry_date); xd = pd.DatetimeIndex(E.exit_date)
    m = (ed <= day) & (xd >= day)
    return E[m]


def ccy_split(rows):
    """-> dict currency -> net signed count, from the pair's two currencies."""
    net = {}
    for _i, r in rows.iterrows():
        p = str(r.pair); s = 1 if str(r.direction) == 'long' else -1
        b, q = p[:3], p[3:6]
        net[b] = net.get(b, 0) + s
        net[q] = net.get(q, 0) - s
    return net


def stage_dip():
    print('building the six walk-forward steps', flush=True)
    TT, per = build_frames()
    E = N.entry_frame(TT)
    print('  %d legs, %d entries' % (len(TT), len(E)), flush=True)

    cost = N._cost_R(TT)
    DS = N.daily_series(TT, cost)
    Y = N._yearly(TT, cost, DS)
    b = Y[Y.year.isin(list(BUILD))]
    print('\nYEARLY, as the report has it:')
    print(b[['year', 'n_entered', 'R_net', 'R_gross']].to_string(index=False))
    print('  sum R_net %.4f  worst year %.4f  trades/yr %.1f'
          % (b.R_net.sum(), b.R_net.min(), b.n_entered.mean()))
    print('  true_dip over BUILD  = %.4f' % N.true_dip(DS, BUILD))
    print('  true_dip over ALL days in DS = %.4f' % N.true_dip(DS, None))
    dsy = sorted(set(pd.DatetimeIndex(DS.date).year))
    print('  DS spans years %s' % dsy)

    # ---- IS THE YEARLY TABLE ON THE SAME BASIS AS THE DAILY CURVE?
    dsx = DS.copy()
    dsx['year'] = pd.DatetimeIndex(dsx.date).year
    byyr = dsx.groupby('year', as_index=False).R.sum().rename(
        columns={'R': 'R_daily_mtm'})
    cmp_ = b[['year', 'R_net']].merge(byyr, on='year', how='outer').sort_values('year')
    cmp_['diff'] = cmp_.R_daily_mtm - cmp_.R_net
    print('\nTHE TWO BASES SIDE BY SIDE (R_net is exit-year trade R; '
          'R_daily_mtm is the daily curve summed over the year):')
    print(cmp_.to_string(index=False))
    print('  R_net total over BUILD     %.4f' % b.R_net.sum())
    print('  daily mtm total over BUILD %.4f'
          % float(dsx[dsx.year.isin(list(BUILD))].R.sum()))
    print('  daily mtm total over ALL   %.4f' % float(dsx.R.sum()))
    print('  worst mtm YEAR %.4f in %d'
          % (byyr[byyr.year.isin(list(BUILD))].R_daily_mtm.min(),
             int(byyr[byyr.year.isin(list(BUILD))].sort_values('R_daily_mtm')
                 .year.iloc[0])))
    out_of_window = float(dsx[~dsx.year.isin(list(BUILD))].R.abs().sum())
    print('  |R| on days OUTSIDE 2010-2015 that the dip filter drops: %.6f'
          % out_of_window)

    D, d, eq = deepest_dips(DS, BUILD, 5)
    dd = d.copy(); dd['eq'] = eq
    dd.to_csv(os.path.join(OUT, 'dipcheck_stitched_daily.csv'), index=False)
    print('\nTEN LARGEST SINGLE-DAY INCREMENTS:')
    print(dd.reindex(dd.R.abs().sort_values(ascending=False).index)
          .head(10).to_string(index=False))
    print('\nTHE CURVE AROUND THE JANUARY 2015 PEAK:')
    mw = (pd.DatetimeIndex(dd.date) >= '2014-12-15') & \
         (pd.DatetimeIndex(dd.date) <= '2015-01-30')
    print(dd[mw].to_string(index=False))
    pd.set_option('display.width', 220)
    print('\nTHE FIVE DEEPEST DIPS, 2010-2015:')
    print(D.to_string(index=False))

    print('\nPOSITIONS OPEN AT EACH TROUGH:')
    for _i, r in D.iterrows():
        o = open_at(TT, r.trough_date)
        st = o.groupby('step').size().to_dict() if 'step' in o.columns else {}
        net = ccy_split(o)
        top = sorted(net.items(), key=lambda kv: -abs(kv[1]))[:4]
        print('  dip %d  %s  depth %7.3f R  OPEN %3d entries  steps %s'
              % (r['rank'], r.trough_date.date(), r.depth_R, len(o), st))
        print('        pairs: %s' % ', '.join(
            '%s %s' % (x.pair, 'L' if x.direction == 'long' else 'S')
            for x in o.itertuples()))
        print('        largest net currency legs: %s'
              % ', '.join('%s %+d' % (c, n) for c, n in top))

    # ---- THE BOUNDARY TEST: do two different steps hold positions on the
    # same day? If they do, the stitched daily series sums increments from
    # two different parameter sets and shows exposure the strategy never had.
    E2 = E.merge(TT[['pair', 'entry_date', 'direction', 'step',
                     'step_trade_year']].drop_duplicates(),
                 on=['pair', 'entry_date', 'direction'], how='left')
    days = pd.date_range(d.date.iloc[0], d.date.iloc[-1], freq='D')
    ed = pd.DatetimeIndex(E2.entry_date); xd = pd.DatetimeIndex(E2.exit_date)
    rows = []
    for day in days:
        m = (ed <= day) & (xd >= day)
        if not m.any():
            continue
        g = E2[m]
        rows.append(dict(date=day, n_open=int(m.sum()),
                         n_steps=int(g.step_trade_year.nunique()),
                         steps=','.join(str(int(x)) for x in
                                        sorted(g.step_trade_year.unique()))))
    O = pd.DataFrame(rows)
    ov = O[O.n_steps > 1]
    print('\nTHE BOUNDARY TEST')
    print('  trading days with an open position: %d' % len(O))
    print('  days where positions from MORE THAN ONE step are open at once: '
          '%d (%.1f%%)' % (len(ov), 100.0 * len(ov) / max(1, len(O))))
    print('  max positions open on any day: %d (mean %.2f)'
          % (O.n_open.max(), O.n_open.mean()))
    if len(ov):
        print('  max open on an overlap day: %d; on a clean day: %d'
              % (ov.n_open.max(), O[O.n_steps == 1].n_open.max()))
        print(ov.sort_values('n_open', ascending=False)
              .head(12).to_string(index=False))
    O.to_csv(os.path.join(OUT, 'dipcheck_open_by_day.csv'), index=False)

    # ---- THE CORRECTED SERIES: each calendar year's DAYS come only from that
    # year's own step, so no day can carry two parameter sets.
    accs = []
    for y in sorted(per):
        Ty = per[y].reset_index(drop=True)
        if not len(Ty):
            continue
        cy = N._cost_R(Ty)
        dsy_ = N.daily_series(Ty, cy)
        dsy_ = dsy_[pd.DatetimeIndex(dsy_.date).year == y]
        accs.append(dsy_)
    DSC = (pd.concat(accs, ignore_index=True)
             .groupby('date', as_index=False).R.sum()
             .sort_values('date').reset_index(drop=True))
    print('\nTHE CORRECTED SERIES (each year only from its own step)')
    print('  days %d vs stitched %d' % (len(DSC), len(
        DS[pd.DatetimeIndex(DS.date).year.isin(list(BUILD))])))
    print('  sum R %.4f vs yearly sum %.4f' % (DSC.R.sum(), b.R_net.sum()))
    print('  true_dip CORRECTED = %.4f  (stitched %.4f)'
          % (N.true_dip(DSC, BUILD), N.true_dip(DS, BUILD)))
    DC, _dc, _ec = deepest_dips(DSC, BUILD, 5)
    print(DC.to_string(index=False))
    DSC.to_csv(os.path.join(OUT, 'dipcheck_corrected_daily.csv'), index=False)
    D.to_csv(os.path.join(OUT, 'dipcheck_dips_stitched.csv'), index=False)
    DC.to_csv(os.path.join(OUT, 'dipcheck_dips_corrected.csv'), index=False)
    print('\nwrote dipcheck_*.csv to results/nnfx', flush=True)



# ===================== THE SNB DAY, AND WHAT IT CARRIES =====================
# Jack's carried-forward three. 15 January 2015 is the Swiss National Bank
# abandoning the 1.20 EURCHF floor; EURCHF fell about 19% intraday. On a
# close-only daily mark that lands as a single enormous increment, and the
# "drawdown" that follows is measured from a peak that existed for one day.
CARRY = (('A', 'ichimoku_signals', 'sma_baseline', 'full_nnfx'),
         ('B', 'schaff_trend_cycle_signals', 'sma_baseline', 'side_xentry'),
         ('C', 'halftrend_signals', 'sma_baseline', 'full_nnfx'))
SNB = (pd.Timestamp('2015-01-15'), pd.Timestamp('2015-01-16'))


def stitch(c1, base, var, rs, lowvol_q=None, peg_x=None):
    """The walk-forward stitched trade frame, exactly as stage_report builds it.

    THE FLOOR AND THE PEG GUARD ARE OFF BY DEFAULT HERE, AND THAT IS DELIBERATE.
    This script asks how dependent a candidate is on the SNB day. Answering
    that needs the book that CONTAINS the day. On 25 Nov the floor and the peg
    guard became module defaults in nnfx2s/nnfxvol, so this stitch silently
    inherited them -- and the peg guard's whole effect is deleting the 2 Jan
    2015 EURCHF entry. The dependence table came back reading 745 entries and
    "1.4 R on the two SNB days, 3.7% of total", which is true of a book the
    guard had already removed the trade from and says nothing about the
    question. Both are now passed explicitly and written into the output.
    """
    W = pd.read_csv(os.path.join(OUT, 'stage2_picks_walk.csv'))
    acc = []
    for stp in S2.STEPS:
        if stp['trade'] not in BUILD:
            continue
        w = W[(W.c1 == c1) & (W.base == base) & (W.variant == var)
              & (W.ruleset == rs) & (W.step == stp['name'])]
        if not len(w):
            continue
        w = w.iloc[0]
        T = S2.run_combo(c1, w.picked_c1_setting, base, w.picked_base_setting,
                         var, rs, use_hourly=True,
                         lowvol_q=lowvol_q, peg_x=peg_x)
        if not len(T):
            continue
        T = T[pd.DatetimeIndex(T.exit_date).year == stp['trade']]
        if len(T):
            acc.append(T)
    if not acc:
        return pd.DataFrame()
    return pd.concat(acc, ignore_index=True)


def snb_day_detail(TT, cost, day):
    """Per-pair increment on one day, and the positions open."""
    rows = []
    for p, g in TT.groupby('pair'):
        gg = g.reset_index(drop=True)
        cp = N._cost_R(gg)
        ds = N.daily_series(gg, cp)
        m = pd.DatetimeIndex(ds.date) == day
        if m.any():
            rows.append(dict(pair=p, R_on_day=float(ds.R[m].sum())))
    P = pd.DataFrame(rows)
    return P.reindex(P.R_on_day.abs().sort_values(ascending=False).index) \
        if len(P) else P


def stage_snb():
    """How much of each carried-forward candidate is the SNB day."""
    S.load_costs(os.environ.get('FX_COST_TABLE', 'results/cost_table_h22.csv'))
    out = []
    for (lab, c1, base, rs) in CARRY:
        for var in ('jack', 'textbook'):
            TT = stitch(c1, base, var, rs)
            if not len(TT):
                print('  %s %s: no trades' % (lab, var), flush=True)
                continue
            cost = N._cost_R(TT)
            DS = N.daily_series(TT, cost)
            dsb = DS[pd.DatetimeIndex(DS.date).year.isin(list(BUILD))].copy()
            is_snb = pd.DatetimeIndex(dsb.date).isin(SNB)
            r_tot = float(dsb.R.sum())
            r_snb = float(dsb.R[is_snb].sum())
            ex = dsb[~is_snb].reset_index(drop=True)
            dip_all = N.true_dip(dsb, BUILD)
            dip_ex = N.true_dip(ex, BUILD)
            E = N.entry_frame(TT)
            n_ent = len(E)
            # positions open on the SNB day, and the net per currency
            o = open_at(TT, SNB[0])
            net = ccy_split(o)
            chf = net.get('CHF', 0)
            same_dir = max((sum(1 for x in o.itertuples()
                                if (x.pair[:3] == c or x.pair[3:6] == c))
                            for c in set(list(net))), default=0)
            row = dict(label=lab, c1=c1, base=base, ruleset=rs, variant=var,
                       lowvol_q=0.0, peg_x=0.0, leverage_cap_on=0,
                       n_entries=n_ent, R_total=r_tot,
                       R_per_year=r_tot / len(BUILD),
                       R_on_the_two_SNB_days=r_snb,
                       share_of_total_pct=(100.0 * r_snb / r_tot
                                           if abs(r_tot) > 1e-9 else np.nan),
                       R_total_ex_SNB=r_tot - r_snb,
                       R_per_year_ex_SNB=(r_tot - r_snb) / len(BUILD),
                       worst_dip_R=dip_all, worst_dip_R_ex_SNB=dip_ex,
                       R_per_year_per_dip=(r_tot / len(BUILD) / dip_all
                                           if dip_all > 1e-9 else np.nan),
                       R_per_year_per_dip_ex_SNB=(
                           (r_tot - r_snb) / len(BUILD) / dip_ex
                           if dip_ex > 1e-9 else np.nan),
                       positions_open_on_SNB_day=len(o),
                       net_CHF_legs_on_SNB_day=chf,
                       max_pairs_touching_one_ccy=same_dir)
            out.append(row)
            print('  %s %-8s %-12s: R %7.2f of which SNB %7.2f (%5.1f%%), '
                  'dip %6.2f -> %6.2f, open %2d, net CHF %+d'
                  % (lab, var, rs, r_tot, r_snb,
                     row['share_of_total_pct'], dip_all, dip_ex, len(o), chf),
                  flush=True)
            if lab == 'A' and var == 'jack':
                P = snb_day_detail(TT, cost, SNB[0])
                P.to_csv(os.path.join(OUT, 'dipcheck_snb_by_pair.csv'),
                         index=False)
                print('\n  THE +101.6 R, BY PAIR, ON 2015-01-15:')
                print(P.head(14).to_string(index=False))
                print('\n  POSITIONS OPEN ON 2015-01-15: %d' % len(o))
                for x in o.itertuples():
                    print('    %s %-5s entered %s exit %s'
                          % (x.pair, 'long' if x.direction == 'long' else 'short',
                             pd.Timestamp(x.entry_date).date(),
                             pd.Timestamp(x.exit_date).date()))
                print('  net per currency: %s' % ', '.join(
                    '%s %+d' % (c, n) for c, n in
                    sorted(net.items(), key=lambda kv: -abs(kv[1]))))
    D = pd.DataFrame(out)
    f = os.path.join(OUT, 'dipcheck_snb_dependence.csv')
    D.to_csv(f, index=False)
    print('\nwrote %s' % os.path.relpath(f, _R), flush=True)
    return D


if __name__ == '__main__':
    st = sys.argv[sys.argv.index('--stage') + 1] if '--stage' in sys.argv else 'dip'
    if st == 'dip':
        stage_dip()
    elif st == 'snb':
        stage_snb()
    else:
        raise SystemExit('unknown stage %s' % st)
