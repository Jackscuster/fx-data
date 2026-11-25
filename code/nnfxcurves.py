import os,sys
_R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_R, 'code'))
os.chdir(_R)
ROOTOUT = os.path.join(_R, 'results')
"""THE CURVES JACK ASKED FOR ON 25 NOV, all at ACHIEVABLE SIZE.

  peg      the cross-pair peg guard swept over X, with the effect on A, B, C
  floor    the per-pair floor at 0 / 1 / 2.5 / 5 / 7.5 / 10 per cent, with
           total R, R per year, trades removed, and the average R of the
           REMOVED trades against the KEPT ones
  buckets  R per trade by ATR percentile at entry, ten buckets, which is what
           answers "is the profit concentrated in low-volatility entries"

Every figure here has the LEVERAGE CAP applied, because that is standing from
25 Nov: open positions summed, 1:30, new entries scaled down to fit.
"""
import time, hashlib
import numpy as np, pandas as pd

import l2sweep as S
import l2r2gate1 as G
import nnfx1 as N
import nnfx2s as S2
import nnfx3 as S3
import nnfxvol as VOL

OUT = os.path.join(ROOTOUT, 'nnfx')
BUILD = S2.BUILD_YEARS
FLOOR_CURVE = (0.0, 0.01, 0.025, 0.05, 0.075, 0.10)


def _stitch(c1, base, rs, v, lowvol_q, peg_x, years=BUILD):
    """The walk-forward stitch, exactly as stage 2 builds it, under one
    (floor, peg) setting."""
    W = pd.read_csv(os.path.join(OUT, 'stage2_picks_walk.csv'))
    w = W[(W.c1 == c1) & (W.base == base) & (W.variant == v)
          & (W.ruleset == rs)]
    acc = []
    for stp in S2.STEPS:
        if stp['trade'] not in years:
            continue
        r = w[w.step == stp['name']]
        if not len(r):
            continue
        T = S2.run_combo(c1, str(r.iloc[0].picked_c1_setting), base,
                         str(r.iloc[0].picked_base_setting), v, rs,
                         use_hourly=True,
                         lowvol_q=(lowvol_q or None), peg_x=(peg_x or None))
        if not len(T):
            continue
        Ty = T[pd.DatetimeIndex(T.exit_date).year == stp['trade']]
        if len(Ty):
            acc.append(Ty)
    return pd.concat(acc, ignore_index=True) if acc else pd.DataFrame()


def _fig(T, years=BUILD):
    """Headline figures at achievable size, plus the removed/kept split."""
    if not len(T):
        return dict(R_total=np.nan, R_per_year=np.nan, trades=0,
                    R_per_trade=np.nan, worst_dip_R=np.nan)
    M, _s = VOL.apply_leverage_cap(T)
    M = M.reset_index(drop=True)
    cost = N._cost_R(M)
    DS = N.daily_series(M, cost)
    Y = N._yearly(M, cost, DS)
    b = Y[Y.year.isin(list(years))]
    n = float(b.n_entered.sum()) if len(b) else 0.0
    tot = float(b.R_net.sum()) if len(b) else np.nan
    return dict(R_total=tot, R_per_year=(tot / max(1, len(b))),
                trades=n, R_per_trade=(tot / n if n else np.nan),
                worst_dip_R=N.true_dip(DS, years))


def _ekeys(D):
    """ONE key convention for an entry, used by both sides of the removed-
    versus-kept split. It has to be one function.

    It was two, and they disagreed: _entry_keys formatted the date through
    pd.DatetimeIndex(...).astype(str) ('2015-01-02') while _entry_R formatted
    the same date through str(pd.Timestamp(...)) ('2015-01-02 00:00:00'). No
    key ever matched, so `removed` came back as the WHOLE floor-off set and
    `kept` came back empty -- floor_curve_abc.csv read 866 trades removed and
    100.0% removed at every level including the floor-OFF level, with
    mean_R_kept NaN. The R_total and trades columns were never wrong; only the
    split was. Found and fixed 25 Nov 2026.
    """
    return list(zip(D.pair.astype(str),
                    pd.DatetimeIndex(D.entry_date).strftime('%Y-%m-%d %H:%M:%S'),
                    D.direction.astype(str)))


def _entry_keys(T):
    if not len(T):
        return set()
    return set(_ekeys(N.entry_frame(T)))


def _entry_R(T):
    """Net R per entry, in the REPORTED 1.5-ATR unit.

    `R` on a trade frame is the engine's raw r; `R_gross` is that restated to
    the declared notional, and every reported figure is in the R_gross unit.
    This summed the raw column and charged no cost, so the removed-versus-kept
    means were 1.5x too large and gross. Both sides carried the same error, so
    the COMPARISON held and only the absolute numbers were wrong.
    """
    if not len(T):
        return {}
    _T = T.copy()
    _T['_net'] = _T.R_gross.to_numpy(float) - N._cost_R(_T)
    g = (_T.groupby(['pair', 'entry_date', 'direction'], as_index=False)
         .agg(R=('_net', 'sum')))
    return dict(zip(_ekeys(g), g.R.astype(float)))


def stage_peg(verbose=True):
    """The peg-guard curve, and what each X does to A, B and C."""
    C = VOL.peg_curve()
    f = os.path.join(OUT, 'pegguard_curve.csv')
    S2._write_csv(C, f)
    if verbose:
        print('  peg curve -> %s' % os.path.relpath(f, _R), flush=True)
    rows = []
    for (lab, c1, base, rs) in S3.BASES:
        for v in ('jack', 'textbook'):
            for x in (0.0, 0.20, 0.33, 0.50):
                S2._RUNC = {} if hasattr(S2, '_RUNC') else None
                T = _stitch(c1, base, rs, v, VOL.LOWVOL_Q, x)
                fg = _fig(T)
                rows.append(dict(base=lab, variant=v, peg_X=x,
                                 floor_q=VOL.LOWVOL_Q, **fg))
                if verbose:
                    print('    peg %s/%s X=%.2f: R %8.2f, R/yr %7.2f, '
                          'trades %5.0f' % (lab, v, x, fg['R_total'],
                                            fg['R_per_year'], fg['trades']),
                          flush=True)
    D = pd.DataFrame(rows)
    S2._write_csv(D, os.path.join(OUT, 'pegguard_effect_abc.csv'))
    return D


def stage_floor(verbose=True):
    """The per-pair floor curve, with the removed-versus-kept split."""
    rows = []
    for (lab, c1, base, rs) in S3.BASES:
        for v in ('jack', 'textbook'):
            base_T = None
            base_R = {}
            for q in FLOOR_CURVE:
                T = _stitch(c1, base, rs, v, q, VOL.PEG_X_PLACEHOLDER)
                fg = _fig(T)
                if q == 0.0:
                    base_T = T
                    base_R = _entry_R(T)
                kept = _entry_keys(T)
                allk = set(base_R)
                removed = allk - kept
                # THE INVARIANT THAT WOULD HAVE CAUGHT THE KEY MISMATCH: at
                # the floor-OFF level the two sides are the same run, so
                # nothing can be removed. A key convention that disagrees
                # with itself fails here instead of shipping 100.0%.
                if q == 0.0:
                    assert not removed, (
                        '%s/%s floor OFF: %d of %d entries "removed" against '
                        'itself -- the entry key conventions disagree'
                        % (lab, v, len(removed), len(allk)))
                r_rem = [base_R[k] for k in removed]
                r_kep = [base_R[k] for k in (allk & kept)]
                rows.append(dict(
                    base=lab, variant=v, floor_q=q, peg_X=VOL.PEG_X_PLACEHOLDER,
                    **fg,
                    trades_removed=len(removed),
                    pct_trades_removed=(100.0 * len(removed) / len(allk)
                                        if allk else np.nan),
                    mean_R_removed=(float(np.mean(r_rem)) if r_rem else np.nan),
                    mean_R_kept=(float(np.mean(r_kep)) if r_kep else np.nan),
                    R_removed_total=(float(np.sum(r_rem)) if r_rem else 0.0)))
                if verbose:
                    print('    floor %s/%s q=%.3f: R %8.2f, R/yr %7.2f, '
                          'removed %4d, mean R removed %+7.3f vs kept %+7.3f'
                          % (lab, v, q, fg['R_total'], fg['R_per_year'],
                             len(removed), rows[-1]['mean_R_removed'],
                             rows[-1]['mean_R_kept']), flush=True)
    D = pd.DataFrame(rows)
    S2._write_csv(D, os.path.join(OUT, 'floor_curve_abc.csv'))
    return D


def stage_buckets(verbose=True):
    """R per trade by ATR percentile at entry, ten buckets, per base."""
    rows = []
    snb = []
    for (lab, c1, base, rs) in S3.BASES:
        for v in ('jack', 'textbook'):
            T = _stitch(c1, base, rs, v, 0.0, 0.0)   # NO floor, NO peg guard,
            if not len(T):                            # so every bucket exists
                continue
            M, _s = VOL.apply_leverage_cap(T)
            B = VOL.atr_buckets(M)
            if not len(B):
                continue
            B = B.assign(base=lab, variant=v)
            rows.append(B)
            # THE ONE TRADE, ON THE RECORD, IN BOTH UNITS AND BOTH SIZES.
            # It was quoted at +74.996 R for two days. That is the RAW r
            # column; every candidate total is in the restated 1.5-ATR unit,
            # where the same trade is +49.997 uncapped. Nobody should ever
            # have to derive that again, so it goes in a file.
            # PER ENTRY, NOT PER LEG, AND THE SINGLE BIGGEST ONE NAMED.
            # The first version summed every LEG exiting on the two SNB days,
            # which for A/jack is three legs across two different positions
            # and came out at 75.746 raw -- close enough to the 74.996 that
            # had been quoted for two days to look like the same number and
            # not be. The question is what ONE TRADE is worth.
            def _per_entry(X, cst):
                Y = X.assign(_c=cst)
                g = (Y.groupby(['pair', 'entry_date', 'direction'],
                               as_index=False)
                     .agg(raw=('R', 'sum'), gross=('R_gross', 'sum'),
                          cost=('_c', 'sum'), legs=('leg', 'size'),
                          xd=('exit_date', 'max'),
                          sc=('lev_scale', 'min') if 'lev_scale' in Y.columns
                          else ('R', 'size')))
                g['net'] = g.gross - g.cost
                return g[pd.DatetimeIndex(g.xd).normalize()
                         .isin(pd.DatetimeIndex(VOL.SNB_DAYS))]
            _gu = _per_entry(T, N._cost_R(T))
            _gc = _per_entry(M, N._cost_R(M))
            if len(_gu):
                _b = _gu.loc[_gu.net.idxmax()]
                _m = _gc[(_gc.pair == _b.pair)
                         & (pd.DatetimeIndex(_gc.entry_date)
                            == pd.Timestamp(_b.entry_date))]
                _m = _m.iloc[0] if len(_m) else None
                snb.append(dict(
                    base=lab, variant=v, pair=str(_b.pair),
                    entry_date=str(pd.Timestamp(_b.entry_date).date()),
                    direction=str(_b.direction), legs=int(_b.legs),
                    n_entries_exiting_on_SNB_days=int(len(_gu)),
                    R_raw_uncapped=float(_b.raw),
                    R_gross_uncapped=float(_b.gross),
                    R_net_uncapped=float(_b.net),
                    R_raw_capped=(float(_m.raw) if _m is not None else np.nan),
                    R_gross_capped=(float(_m.gross) if _m is not None
                                    else np.nan),
                    R_net_capped=(float(_m.net) if _m is not None else np.nan),
                    lev_scale=(float(_m.sc) if _m is not None else np.nan),
                    all_SNB_entries_R_net_uncapped=float(_gu.net.sum()),
                    all_SNB_entries_R_net_capped=float(_gc.net.sum()),
                    candidate_R_total_net_capped=float(B.R_total.sum())))
            if verbose:
                b1 = B[B.bucket <= 3].share_of_total_R.sum()
                print('    buckets %s/%s: bottom 3 deciles carry %.1f%% of R '
                      'from %.1f%% of trades'
                      % (lab, v, 100.0 * b1,
                         100.0 * B[B.bucket <= 3].n_trades.sum()
                         / B.n_trades.sum()), flush=True)
    D = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    S2._write_csv(D, os.path.join(OUT, 'atr_buckets_abc.csv'))
    S2._write_csv(pd.DataFrame(snb),
                  os.path.join(OUT, 'snb_trade_value.csv'))
    if verbose and snb:
        for r in snb:
            print('    SNB trade %s/%s: %s %s %s, %d legs -- raw %+.3f -> '
                  'reported %+.3f gross, %+.3f net uncapped; capped %+.3f net '
                  'at scale %.4f, against a candidate total of %+.3f'
                  % (r['base'], r['variant'], r['pair'], r['entry_date'],
                     r['direction'], r['legs'], r['R_raw_uncapped'],
                     r['R_gross_uncapped'], r['R_net_uncapped'],
                     r['R_net_capped'], r['lev_scale'],
                     r['candidate_R_total_net_capped']), flush=True)
    return D


FLOOR1_DIR = os.path.join(ROOTOUT, 'nnfx_floor')


def stage_floor1(verbose=True):
    """THE FLOOR CURVE OVER THE STAGE 1 C1 RANKING, Jack's item 3.

    The heavy part is done by the chain, which runs nnfx1's stage 1 at each
    of the six floor levels into results/nnfx_floor/ -- a separate directory
    so condition4_all's glob does not mix six different rules into one
    zero-edge aggregate. This function only reads those summaries.

    ONE HONEST LIMIT, STATED IN THE OUTPUT. For A, B and C the removed-versus-
    kept split is exact: floor_curve_abc.csv matches entries one by one and
    reads the R of the trades that disappeared. Here there are 117
    candidate-settings per plan and no per-trade frames were kept, so the
    removed trades' mean R is attributed BY DIFFERENCE -- the drop in total R
    divided by the drop in trade count. That is not the same thing, because
    the leverage cap is portfolio-wide: removing one entry leaves room for a
    later one to be placed at larger size, so the difference carries a second
    effect as well as the removed trades' own R. The column is named
    mean_R_removed_by_difference to keep that visible, and the exact figure
    for A, B and C is the one to quote.
    """
    import glob
    rows, lead = [], []
    for v in ('jack', 'textbook'):
        per_q = {}
        for q in FLOOR_CURVE:
            tg = 'q%s' % ('off' if q == 0.0 else ('%g' % (q * 100)).replace('.', 'p'))
            f_ = os.path.join(FLOOR1_DIR,
                              'stage1r2_c1_%s_%s_summary.csv' % (v, tg))
            if not os.path.exists(f_):
                if verbose:
                    print('    floor1 %s q=%.3f: MISSING %s'
                          % (v, q, os.path.basename(f_)), flush=True)
                continue
            S_ = pd.read_csv(f_)
            S_ = S_[S_.get('n_entered', pd.Series(dtype=float)).fillna(0) > 0]
            if not len(S_):
                continue
            per_q[q] = S_
        if 0.0 not in per_q:
            if verbose:
                print('    floor1 %s: no q=0 baseline on disk, skipped' % v,
                      flush=True)
            continue
        B0 = per_q[0.0].set_index(['indicator', 'setting'])
        for q in sorted(per_q):
            S_ = per_q[q]
            nt = float(S_.n_entered.sum())
            rt = float(S_.R_net_build.sum())
            n0 = float(per_q[0.0].n_entered.sum())
            r0 = float(per_q[0.0].R_net_build.sum())
            drem = n0 - nt
            rows.append(dict(
                scope='stage1_c1_ranking', variant=v, floor_q=q,
                peg_X=VOL.PEG_X_PLACEHOLDER, leverage_cap_on=1,
                n_candidate_settings=int(len(S_)),
                trades=nt, R_total=rt,
                R_per_year=float(S_.R_net_per_year.sum()),
                mean_R_kept=(rt / nt if nt else np.nan),
                trades_removed=drem,
                pct_trades_removed=(100.0 * drem / n0 if n0 else np.nan),
                mean_R_removed_by_difference=((r0 - rt) / drem
                                              if drem > 0 else np.nan),
                n_positive_candidates=int((S_.R_net_build > 0).sum()),
                n_clearing_alone=int(S_.get('clears_alone',
                                            pd.Series([0] * len(S_))).sum())))
            # THE LEADERBOARD AT THIS LEVEL, which is the question behind the
            # curve: does the floor change WHICH C1 leads, or only the size?
            T_ = S_.sort_values('R_net_build', ascending=False).head(10)
            for rk, (_i, r) in enumerate(T_.iterrows(), 1):
                k = (r.indicator, r.setting)
                lead.append(dict(
                    variant=v, floor_q=q, rank=rk, indicator=r.indicator,
                    setting=r.setting, R_total=float(r.R_net_build),
                    R_per_year=float(r.R_net_per_year),
                    n_entered=float(r.n_entered),
                    t_yearly=float(r.get('t_yearly', np.nan)),
                    R_total_at_floor_off=(float(B0.loc[k].R_net_build)
                                          if k in B0.index else np.nan)))
            if verbose:
                print('    floor1 %s q=%.3f: %d settings, %d trades, R %9.1f, '
                      'removed %6.0f, leader %s/%s'
                      % (v, q, len(S_), nt, rt, drem,
                         T_.iloc[0].indicator, T_.iloc[0].setting), flush=True)
    D = pd.DataFrame(rows)
    L = pd.DataFrame(lead)
    S2._write_csv(D, os.path.join(OUT, 'floor_curve_stage1.csv'))
    S2._write_csv(L, os.path.join(OUT, 'floor_leaders_stage1.csv'))
    return D, L


if __name__ == '__main__':
    st = G.opt('--stage', str, 'all')
    S.load_costs(os.environ.get('FX_COST_TABLE', 'results/cost_table_h22.csv'))
    if st in ('peg', 'all'):
        stage_peg()
    if st in ('buckets', 'all'):
        stage_buckets()
    if st in ('floor', 'all'):
        stage_floor()
    if st in ('floor1', 'all'):
        stage_floor1()
    if st not in ('peg', 'floor', 'floor1', 'buckets', 'all'):
        raise SystemExit('unknown stage %s' % st)
