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


def _entry_keys(T):
    if not len(T):
        return set()
    E = N.entry_frame(T)
    return set(zip(E.pair.astype(str),
                   pd.DatetimeIndex(E.entry_date).astype(str),
                   E.direction.astype(str)))


def _entry_R(T):
    if not len(T):
        return {}
    g = (T.groupby(['pair', 'entry_date', 'direction'], as_index=False)
         .agg(R=('R', 'sum')))
    return {(str(r.pair), str(pd.Timestamp(r.entry_date)), str(r.direction)):
            float(r.R) for r in g.itertuples()}


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
            if verbose:
                b1 = B[B.bucket <= 3].share_of_total_R.sum()
                print('    buckets %s/%s: bottom 3 deciles carry %.1f%% of R '
                      'from %.1f%% of trades'
                      % (lab, v, 100.0 * b1,
                         100.0 * B[B.bucket <= 3].n_trades.sum()
                         / B.n_trades.sum()), flush=True)
    D = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    S2._write_csv(D, os.path.join(OUT, 'atr_buckets_abc.csv'))
    return D


if __name__ == '__main__':
    st = G.opt('--stage', str, 'all')
    S.load_costs(os.environ.get('FX_COST_TABLE', 'results/cost_table_h22.csv'))
    if st in ('peg', 'all'):
        stage_peg()
    if st in ('buckets', 'all'):
        stage_buckets()
    if st in ('floor', 'all'):
        stage_floor()
    if st not in ('peg', 'floor', 'buckets', 'all'):
        raise SystemExit('unknown stage %s' % st)
