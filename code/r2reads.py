import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""CHUNK 1 — THREE BANK READS: A1 slot main effects, A1b walk-forward component
selection, A6 the prop simulator (Jack, 23-24 Nov).

ALL THREE ARE READS. Nothing here scores a strategy or runs the engine. A1 and
A1b read the gate 2 bank's `win` array and `combo`; A6 reads the daily series
the books stage already saved. If any of them needs an engine pass, that is a
bug, not a design choice.

WHAT `win` IS, because everything below depends on it:
    (n_strategies, 4 streams, 5 steps, 10 years, 5 stats)
    stats = n, sum_r, gain, loss, n_win      -- the WINNER's record only
So R per trade for a (strategy, stream, step, year) is sum_r / n, and the
TRADE year of step si is the year index of steps()[si]['trade'][0].

THE UNSEEN RECORDS. Trade year is PRIMARY (Jack, 23 Nov); the grade year is
reported separately as a second, independent unseen read. Significance is taken
on the FIVE YEARLY VALUES, not per trade -- five numbers, one per step, which is
the honest unit when the question is "does this option work across years".

    python3 code/r2reads.py --stage a1  --mode A
    python3 code/r2reads.py --stage a1b --mode A
    python3 code/r2reads.py --stage a6  --mode A
"""
import time, glob, json, hashlib
import numpy as np, pandas as pd

import l2sweep as S
import l2r2gate1 as G
import l2r2gate2 as G2
import l2r2book as BK

RD = os.path.join(ROOTOUT, 'r2gate2')
OUT = os.path.join(ROOTOUT, 'r2reads')
os.makedirs(OUT, exist_ok=True)
SLOTS = ('c1', 'c2', 'vol', 'base', 'exit_ind')
ROLES = ('trade', 'grade')


def _year_idx(role):
    """(step_name, calendar_year, year_index_into_win) per step for one role."""
    out = []
    for stp in G2.steps():
        y = stp['trade'][0] if role == 'trade' else stp['grade'][0]
        out.append((stp['name'], y, y - G2.YEAR0))
    return out


def load_bank(mode='A', tag='full'):
    """Stream the gate 2 bank into (nstrat, 4 streams, 5 steps) arrays.

    VECTORISED ASSIGNMENT, NOT A PER-STRATEGY LOOP. A dict write per
    (strategy, stream, step, role) is ~27 million operations on this bank and
    turns a 40-second read into tens of minutes. Fancy-indexed assignment from
    each part file's `idx` does the same thing in one call.

    Returns dict(role -> (N, SR)), the combo matrix, and the bank row ids.
    """
    d = G2.out_dir(mode, tag)
    fs = sorted(glob.glob(os.path.join(d, 'shard_*_part*.npz')))
    assert fs, 'no gate 2 bank at %s' % d
    z0 = np.load(BK._bank_slice_file(mode, tag), allow_pickle=True)
    nstrat = int(z0['n']); del z0
    out = {r: (np.full((nstrat, 4, 5), np.nan, np.float32),
               np.full((nstrat, 4, 5), np.nan, np.float32)) for r in ROLES}
    CB = np.empty((nstrat, 5), dtype=object)
    seen = np.zeros(nstrat, bool)
    yi = {r: [t[2] for t in _year_idx(r)] for r in ROLES}
    t0 = time.time()
    for k, f in enumerate(fs, 1):
        z = np.load(f, allow_pickle=True)
        idx = np.asarray(z['idx'], np.int64)
        if not len(idx):
            continue
        win = np.asarray(z['win'], np.float32)           # (m,4,5,10,5)
        CB[idx] = np.asarray(z['combo'], dtype=object)
        seen[idx] = True
        for r in ROLES:
            N, SR = out[r]
            for si in range(win.shape[2]):
                N[idx, :, si] = win[:, :, si, yi[r][si], 0]
                SR[idx, :, si] = win[:, :, si, yi[r][si], 1]
        del z, win
        if k % 250 == 0 or k == len(fs):
            print('    bank: %d of %d part files (%.1f min)'
                  % (k, len(fs), (time.time() - t0) / 60), flush=True)
    ns = int(seen.sum())
    print('  bank [mode %s]: %s of %s strategies carry a tuned record'
          % (mode, f'{ns:,}', f'{nstrat:,}'), flush=True)
    assert ns == nstrat, ('the bank covers %d strategies but only %d have a record -- '
                          'this read would describe a smaller field than it claims'
                          % (nstrat, ns))
    return out, CB, np.arange(nstrat)


# ==========================================================================
# A1 — SLOT MAIN EFFECTS
# ==========================================================================
def _codes(CB, si):
    """Integer codes and the option names for one slot."""
    col = np.asarray([str(x) for x in CB[:, si]])
    opts = sorted(set(col.tolist()))
    look = {o: k for k, o in enumerate(opts)}
    return np.array([look[x] for x in col], np.int64), opts


def _pooled(code, nopt, N, SR, stream=None):
    """Per option: summed n and summed R, pooled over the five steps and either
    one stream or all four. bincount, so a shuffle costs one call."""
    if stream is None:
        n = np.nansum(N, axis=(1, 2)); r = np.nansum(SR, axis=(1, 2))
    else:
        n = np.nansum(N[:, stream, :], axis=1); r = np.nansum(SR[:, stream, :], axis=1)
    sn = np.bincount(code, weights=n, minlength=nopt)
    sr = np.bincount(code, weights=r, minlength=nopt)
    return sn, sr


def stage_a1(mode='A', tag='full', ndraw=1000, seed=20261124, nmax=None):
    """Every option of every slot, and every C1 x C2 pair, on both unseen records.

    THE STATISTIC. For an option, the pooled R PER TRADE over the five unseen
    years of the role -- summed R divided by summed trades across the strategies
    that contain it. Reported per stream and pooled over streams, per year, with
    years-positive out of five.

    SIGNIFICANCE IS ON THE FIVE YEARLY VALUES (Jack, 23 Nov), not per trade:
    t = mean(yearly) / (sd(yearly)/sqrt(5)) over the five per-year R-per-trade
    figures. Five numbers is the honest unit for "does this option work across
    years"; a per-trade t over hundreds of thousands of trades answers a
    different and much easier question.

    THE NULL shuffles OPTION LABELS WITHIN THE SLOT across strategies, 1,000
    draws, and takes the BEST option's statistic each time. The p-value is
    therefore against best-of-slot -- the right comparison, because the thing a
    reader does with this table is look at its best row.
    """
    G.manifest_check()
    d, CB, ids = load_bank(mode, tag)
    if nmax:
        CB = CB[:nmax]
    rng = np.random.default_rng(seed)
    rows, nulls, cross = [], [], []
    steps = [s['name'] for s in G2.steps()]
    for role in ROLES:
        N, SR = d[role]
        if nmax:
            N, SR = N[:nmax], SR[:nmax]
        yrs = [t[1] for t in _year_idx(role)]
        for si, slot in enumerate(SLOTS):
            code, opts = _codes(CB, si)
            nopt = len(opts)
            # ---- observed, per stream and pooled
            for stream in list(range(4)) + [None]:
                sn, sr = _pooled(code, nopt, N, SR, stream)
                for k, o in enumerate(opts):
                    m = code == k
                    per_year, pos = [], 0
                    for st in range(5):
                        if stream is None:
                            nn = np.nansum(N[m, :, st]); rr = np.nansum(SR[m, :, st])
                        else:
                            nn = np.nansum(N[m, stream, st]); rr = np.nansum(SR[m, stream, st])
                        v = (rr / nn) if nn > 0 else np.nan
                        per_year.append(v)
                        pos += int(np.isfinite(v) and v > 0)
                    py = np.array(per_year, float)
                    fin = py[np.isfinite(py)]
                    t5 = (float(fin.mean() / (fin.std(ddof=1) / np.sqrt(len(fin))))
                          if len(fin) > 1 and fin.std(ddof=1) > 0 else np.nan)
                    r = dict(mode=mode, role=role, slot=slot, option=o,
                             stream=(G2.STREAMS[stream] if stream is not None else 'ALL'),
                             n_strategies=int(m.sum()), n_trades=float(sn[k]),
                             total_R=float(sr[k]),
                             R_per_trade=(float(sr[k] / sn[k]) if sn[k] > 0 else np.nan),
                             years_positive=pos, t_on_5_years=t5)
                    for y, v in zip(yrs, per_year):
                        r['R_%d' % y] = v
                    rows.append(r)
            # ---- the null, on the pooled-over-streams statistic
            sn, sr = _pooled(code, nopt, N, SR, None)
            obs = np.where(sn > 0, sr / np.maximum(sn, 1), -np.inf)
            obs_best = float(obs.max())
            obs_arg = opts[int(np.argmax(obs))]
            draws = np.empty(ndraw)
            n_all = np.nansum(N, axis=(1, 2)); r_all = np.nansum(SR, axis=(1, 2))
            for q in range(ndraw):
                c2 = rng.permutation(code)
                a = np.bincount(c2, weights=n_all, minlength=nopt)
                b = np.bincount(c2, weights=r_all, minlength=nopt)
                draws[q] = np.nanmax(np.where(a > 0, b / np.maximum(a, 1), -np.inf))
            nulls.append(dict(mode=mode, role=role, slot=slot, n_options=nopt,
                              best_option=obs_arg, best_R_per_trade=obs_best,
                              n_draws=ndraw, null_mean=float(draws.mean()),
                              null_p95=float(np.percentile(draws, 95)),
                              null_max=float(draws.max()),
                              p_best_of_slot=float((draws >= obs_best).mean())))
        # ---- the C1 x C2 cross
        c1, o1 = _codes(CB, 0); c2c, o2 = _codes(CB, 1)
        pair = c1 * len(o2) + c2c
        npair = len(o1) * len(o2)
        n_all = np.nansum(N, axis=(1, 2)); r_all = np.nansum(SR, axis=(1, 2))
        sn = np.bincount(pair, weights=n_all, minlength=npair)
        sr = np.bincount(pair, weights=r_all, minlength=npair)
        cnt = np.bincount(pair, minlength=npair)
        for k in range(npair):
            if cnt[k] == 0:
                continue
            cross.append(dict(mode=mode, role=role, c1=o1[k // len(o2)], c2=o2[k % len(o2)],
                              n_strategies=int(cnt[k]), n_trades=float(sn[k]),
                              total_R=float(sr[k]),
                              R_per_trade=(float(sr[k] / sn[k]) if sn[k] > 0 else np.nan)))
        obs_best = max((c['R_per_trade'] for c in cross
                        if c['role'] == role and np.isfinite(c['R_per_trade'])),
                       default=np.nan)
        draws = np.empty(ndraw)
        for q in range(ndraw):
            p2 = rng.permutation(c1) * len(o2) + rng.permutation(c2c)
            a = np.bincount(p2, weights=n_all, minlength=npair)
            b = np.bincount(p2, weights=r_all, minlength=npair)
            draws[q] = np.nanmax(np.where(a > 0, b / np.maximum(a, 1), -np.inf))
        nulls.append(dict(mode=mode, role=role, slot='c1_x_c2', n_options=npair,
                          best_option='(pair)', best_R_per_trade=obs_best,
                          n_draws=ndraw, null_mean=float(draws.mean()),
                          null_p95=float(np.percentile(draws, 95)),
                          null_max=float(draws.max()),
                          p_best_of_slot=float((draws >= obs_best).mean())))
    A = pd.DataFrame(rows); Nl = pd.DataFrame(nulls); Cr = pd.DataFrame(cross)
    fa = os.path.join(OUT, 'mode%s_a1_slots.csv' % mode)
    fn = os.path.join(OUT, 'mode%s_a1_nulls.csv' % mode)
    fc = os.path.join(OUT, 'mode%s_a1_c1xc2.csv' % mode)
    A.to_csv(fa, index=False); Nl.to_csv(fn, index=False); Cr.to_csv(fc, index=False)
    print('  A1 [mode %s]: %s option rows, %d null rows, %s c1xc2 cells'
          % (mode, f'{len(A):,}', len(Nl), f'{len(Cr):,}'), flush=True)
    for _i, r in Nl[Nl.role == 'trade'].iterrows():
        print('    %-10s best %-42s %+.5f R/trade   null p95 %+.5f   p=%.3f'
              % (r.slot, str(r.best_option)[:42], r.best_R_per_trade,
                 r.null_p95, r.p_best_of_slot), flush=True)
    return fa, fn, fc


# ==========================================================================
# A1b — WALK-FORWARD COMPONENT SELECTION
# ==========================================================================
# Jack, 23 Nov, replacing A7: "for each step, rank every slot option by its main
# effect on that step's four tuning years only; form the book of all strategies
# whose C1 and C2 are both in the top K options (K swept over the full range,
# and the same for C1 alone); trade that step's unseen trade year, everyone
# equal weight."
#
# THIS IS THE HONEST VERSION OF A7. A7 as first posed picked components on
# 2016-2020 and scored them on the same years. Here the ranking sees only the
# step's four TUNING years and the book is then traded on that step's unseen
# trade year, which is a walk forward.
def _tune_year_idx():
    """Year indices of each step's four tuning years."""
    return [[y - G2.YEAR0 for y in range(s['tune'][0], s['tune'][1] + 1)]
            for s in G2.steps()]


def load_bank_tune(mode='A', tag='full'):
    """(nstrat, 4, 5) summed n and summed R over each step's TUNING years."""
    d = G2.out_dir(mode, tag)
    fs = sorted(glob.glob(os.path.join(d, 'shard_*_part*.npz')))
    z0 = np.load(BK._bank_slice_file(mode, tag), allow_pickle=True)
    nstrat = int(z0['n']); del z0
    N = np.full((nstrat, 4, 5), np.nan, np.float32)
    SR = np.full((nstrat, 4, 5), np.nan, np.float32)
    tyi = _tune_year_idx()
    for f in fs:
        z = np.load(f, allow_pickle=True)
        idx = np.asarray(z['idx'], np.int64)
        if not len(idx):
            continue
        win = np.asarray(z['win'], np.float32)
        for si in range(win.shape[2]):
            N[idx, :, si] = np.nansum(win[:, :, si, tyi[si], 0], axis=-1)
            SR[idx, :, si] = np.nansum(win[:, :, si, tyi[si], 1], axis=-1)
        del z, win
    return N, SR


def stage_a1b(mode='A', tag='full', ndraw=1000, seed=20261124, nmax=None):
    """Rank options on each step's tuning years; trade the resulting book on
    that step's unseen trade year. K swept over the full range."""
    G.manifest_check()
    dtr, CB, _ids = load_bank(mode, tag)
    Ntu, SRtu = load_bank_tune(mode, tag)
    Ntr, SRtr = dtr['trade']
    if nmax:
        CB, Ntu, SRtu, Ntr, SRtr = CB[:nmax], Ntu[:nmax], SRtu[:nmax], Ntr[:nmax], SRtr[:nmax]
    rng = np.random.default_rng(seed)
    c1, o1 = _codes(CB, 0)
    c2, o2 = _codes(CB, 1)
    steps = [s['name'] for s in G2.steps()]
    rows = []

    def book(mask, si):
        """Equal-weight book of the masked strategies on step si's trade year."""
        if not mask.any():
            return dict(members=0, eq_R_per_trade=np.nan, tw_R_per_trade=np.nan,
                        total_R=np.nan, n_trades=0.0)
        n = np.nansum(Ntr[mask, :, si], axis=1)
        r = np.nansum(SRtr[mask, :, si], axis=1)
        per = np.where(n > 0, r / np.maximum(n, 1), np.nan)
        return dict(members=int(mask.sum()),
                    eq_R_per_trade=float(np.nanmean(per)) if np.isfinite(per).any() else np.nan,
                    tw_R_per_trade=(float(r.sum() / n.sum()) if n.sum() > 0 else np.nan),
                    total_R=float(np.nansum(r)), n_trades=float(np.nansum(n)))

    def rank_on_tune(code, nopt, si):
        n = np.nansum(Ntu[:, :, si], axis=1); r = np.nansum(SRtu[:, :, si], axis=1)
        a = np.bincount(code, weights=n, minlength=nopt)
        b = np.bincount(code, weights=r, minlength=nopt)
        sc = np.where(a > 0, b / np.maximum(a, 1), -np.inf)
        return np.argsort(sc)[::-1]

    for si, sname in enumerate(steps):
        ord1 = rank_on_tune(c1, len(o1), si)
        ord2 = rank_on_tune(c2, len(o2), si)
        for rule, Ks in (('c1_and_c2_in_topK', range(1, len(o1) + 1)),
                         ('c1_in_topK', range(1, len(o1) + 1))):
            for K in Ks:
                t1 = set(ord1[:K].tolist())
                if rule == 'c1_and_c2_in_topK':
                    t2 = set(ord2[:min(K, len(o2))].tolist())
                    m = np.isin(c1, list(t1)) & np.isin(c2, list(t2))
                else:
                    m = np.isin(c1, list(t1))
                b = book(m, si)
                rows.append(dict(mode=mode, step=sname, rule=rule, K=K,
                                 trade_year=G2.steps()[si]['trade'][0], **b))
        # ---- the null: same construction, option labels shuffled
        for K in (1, 2, 3, 5, 10, 20, len(o1)):
            if K > len(o1):
                continue
            dr = np.empty(ndraw)
            for q in range(ndraw):
                s1 = rng.permutation(c1); s2 = rng.permutation(c2)
                oo1 = rank_on_tune(s1, len(o1), si)
                oo2 = rank_on_tune(s2, len(o2), si)
                m = np.isin(s1, oo1[:K].tolist()) & np.isin(s2, oo2[:min(K, len(o2))].tolist())
                if not m.any():
                    dr[q] = np.nan; continue
                n = np.nansum(Ntr[m, :, si], axis=1); r = np.nansum(SRtr[m, :, si], axis=1)
                per = np.where(n > 0, r / np.maximum(n, 1), np.nan)
                dr[q] = float(np.nanmean(per)) if np.isfinite(per).any() else np.nan
            real = [x for x in rows if x['step'] == sname
                    and x['rule'] == 'c1_and_c2_in_topK' and x['K'] == K]
            rv = real[0]['eq_R_per_trade'] if real else np.nan
            rows.append(dict(mode=mode, step=sname, rule='NULL_c1_and_c2_in_topK', K=K,
                             trade_year=G2.steps()[si]['trade'][0],
                             members=np.nan, eq_R_per_trade=float(np.nanmean(dr)),
                             tw_R_per_trade=np.nan, total_R=np.nan, n_trades=np.nan,
                             null_p95=float(np.nanpercentile(dr, 95)),
                             real_eq_R_per_trade=rv, n_draws=ndraw,
                             p_one_sided=(float(np.nanmean(dr >= rv))
                                          if np.isfinite(rv) else np.nan)))
    D = pd.DataFrame(rows)
    f = os.path.join(OUT, 'mode%s_a1b_walkforward.csv' % mode)
    D.to_csv(f, index=False)
    real = D[D.rule == 'c1_and_c2_in_topK']
    print('  A1b [mode %s]: %s rows, K swept 1..%d over %d steps -> %s'
          % (mode, f'{len(D):,}', int(real.K.max()), real.step.nunique(),
             os.path.relpath(f, _R)), flush=True)
    g = real.groupby('K').eq_R_per_trade.mean()
    print('    equal-weight R/trade on the unseen trade year, averaged over the 5 steps:',
          flush=True)
    for K in [k for k in (1, 2, 3, 5, 10, 20, int(real.K.max())) if k in g.index]:
        nl = D[(D.rule == 'NULL_c1_and_c2_in_topK') & (D.K == K)]
        pm = float(nl.p_one_sided.mean()) if len(nl) else float('nan')
        print('      K=%-3d %+.5f   null p (mean over steps) %.3f' % (K, g[K], pm), flush=True)
    return f


# ==========================================================================
# A6 — THE PROP SIMULATOR, a standing stage
# ==========================================================================
# THE RULES, from the FundedTradingPlus profile Jack confirmed with the firm
# (researched 7 Sep; open-equity lines confirmed 23 Nov):
#   trailing floor   6% below the high-water mark, and it STOPS TRAILING
#                    PERMANENTLY once the floor reaches the starting balance.
#                    After equity has touched +6% once, the floor is $100k
#                    forever. It is NOT a start-of-day lock.
#   open equity      counts for the trailing line, rolling.
#   daily loss 4%    open equity is logged at each daily close and the 4% is
#                    measured from that; floating losses count; resets daily.
#   evaluation       profit target 10%, no time limit, no minimum days, no
#                    consistency rule. Then funded.
#   payout           80%, from day 0, every 7 days.
#   fee              $549. Evaluation accounts can be reset, funded cannot.
#   leverage         1:30.
#   internal         3.6% daily, 5.4% trailing (tighter than the firm's).
#
# WHAT THIS CANNOT SEE, stated because it bounds every number below. The input
# is a DAILY series, so "open equity" is only observable at the close. A rule
# measured on intraday open equity is therefore evaluated at day granularity
# and the breach counts are LOWER BOUNDS: an intraday excursion that breached
# and recovered before the close is invisible here. A5's hourly replay is what
# would tighten this.
START = 100000.0
FEE = 549.0
PAYOUT_SHARE = 0.80
PAYOUT_EVERY = 7
FIRM_DAILY = 0.04
FIRM_TRAIL = 0.06
EVAL_TARGET = 0.10
INT_DAILY = 0.036
INT_TRAIL = 0.054


def _floor_of(hwm, trail_frac):
    """The trailing floor: trail_frac below the high-water mark, never above
    the starting balance -- which is what "stops trailing permanently once the
    floor reaches the starting balance" means arithmetically."""
    return min(hwm - trail_frac * START, START)


def prop_run(daily_pct, phase='funded', size='fixed', size_frac=1.0,
             trail_frac=FIRM_TRAIL, daily_frac=FIRM_DAILY,
             payout=True, keep_cushion=0.0, target=EVAL_TARGET):
    """Mark-to-market daily equity through one phase. Returns the record.

    size 'fixed'     the series as given (already budget-scaled)
    size 'cushion'   size_frac x (equity - floor) / START, so risk shrinks as
                     the floor is approached -- the thing Jack asked to sweep
    """
    eq = START
    hwm = START
    paid = 0.0
    peak = START
    worst_dip = 0.0
    breach = None
    passed_day = None
    days = 0
    eq_curve = []
    for t, r in enumerate(np.asarray(daily_pct, float)):
        if not np.isfinite(r):
            continue
        prev_close = eq
        fl = _floor_of(hwm, trail_frac)
        mult = 1.0 if size == 'fixed' else max(0.0, size_frac * (eq - fl) / START)
        eq = eq + eq * (r / 100.0) * mult
        days += 1
        eq_curve.append(eq)
        hwm = max(hwm, eq)
        # daily loss, measured from the previous close as the rules state
        if eq <= prev_close * (1.0 - daily_frac):
            breach = ('daily', t); break
        if eq <= _floor_of(hwm, trail_frac):
            breach = ('trailing', t); break
        peak = max(peak, eq)
        worst_dip = max(worst_dip, (peak - eq) / peak)
        if phase == 'eval' and eq >= START * (1.0 + target):
            passed_day = t; break
        if phase == 'funded' and payout and days % PAYOUT_EVERY == 0:
            profit = eq - START - keep_cushion * START
            if profit > 0:
                take = profit * PAYOUT_SHARE
                paid += take
                eq -= take
    yrs = max(days / 252.0, 1e-9)
    return dict(days=days, years=yrs, equity_end=eq, high_water=hwm,
                breached=(breach[0] if breach else ''),
                breach_day=(breach[1] if breach else np.nan),
                passed_eval_day=(passed_day if passed_day is not None else np.nan),
                paid_out=paid, paid_out_per_year=paid / yrs,
                return_pct=100.0 * (eq + paid - START) / START,
                return_pct_per_year=100.0 * (eq + paid - START) / START / yrs,
                worst_dip_pct=100.0 * worst_dip)


def stage_a6(mode='A', src_tag='full', books=None, label='full', fracs=None,
             cushions=None):
    """Both phases, every sizing, every payout policy, on the saved daily series."""
    import l2r2kpis as KP
    books = books or [b for b, _d in BK.BOOKS]
    fracs = fracs or [0.25, 0.5, 0.75, 1.0, 1.5, 2.0]
    cushions = cushions if cushions is not None else [0.0, 0.02, 0.05, 0.10]
    rows = []
    for bk in books:
        for (bname, _dip, _day) in BK.BUDGETS:
            d, y, steps = KP.stitched(mode, bk, bname, src_tag)
            if d is None or not len(d):
                continue
            for rules, tf, df in (('firm', FIRM_TRAIL, FIRM_DAILY),
                                  ('internal', INT_TRAIL, INT_DAILY)):
                ev = prop_run(d, 'eval', 'fixed', trail_frac=tf, daily_frac=df)
                rows.append(dict(mode=mode, source=label, book=bk, budget=bname,
                                 rules=rules, phase='eval', sizing='fixed',
                                 size_frac=np.nan, keep_cushion=np.nan, **ev))
                for keep in cushions:
                    fu = prop_run(d, 'funded', 'fixed', trail_frac=tf, daily_frac=df,
                                  keep_cushion=keep)
                    rows.append(dict(mode=mode, source=label, book=bk, budget=bname,
                                     rules=rules, phase='funded', sizing='fixed',
                                     size_frac=np.nan, keep_cushion=keep, **fu))
                for fr in fracs:
                    fu = prop_run(d, 'funded', 'cushion', size_frac=fr,
                                  trail_frac=tf, daily_frac=df)
                    rows.append(dict(mode=mode, source=label, book=bk, budget=bname,
                                     rules=rules, phase='funded', sizing='cushion',
                                     size_frac=fr, keep_cushion=0.0, **fu))
    D = pd.DataFrame(rows)
    if len(D):
        D['fee_usd'] = FEE
        D['net_per_year_usd'] = D.paid_out_per_year - FEE / D.years.clip(lower=1e-9)
    f = os.path.join(OUT, 'mode%s_a6_propsim_%s.csv' % (mode, label))
    D.to_csv(f, index=False)
    print('  A6 [mode %s, %s]: %d runs -> %s'
          % (mode, label, len(D), os.path.relpath(f, _R)), flush=True)
    if len(D):
        e = D[(D.phase == 'eval') & (D.rules == 'firm')]
        print('    EVAL, firm rules: %d of %d runs passed the 10%% target, %d breached'
              % (int(e.passed_eval_day.notna().sum()), len(e),
                 int((e.breached != '').sum())), flush=True)
        g = D[(D.phase == 'funded') & (D.rules == 'firm')]
        print('    FUNDED, firm rules: %d of %d breached; best $/yr %.0f at %s'
              % (int((g.breached != '').sum()), len(g),
                 (g.paid_out_per_year.max() if len(g) else 0),
                 (str(g.loc[g.paid_out_per_year.idxmax(), ['book','budget','sizing']].to_dict())
                  if len(g) and g.paid_out_per_year.notna().any() else 'n/a')), flush=True)
    return f


# ==========================================================================
# THE THREE REPORTS
# ==========================================================================
def _tbl(d, cols=None):
    import l2r2gate3 as G3x
    return G3x.BK_tbl(d, cols)


def _prov(paths):
    L = ['| file | rows | md5 |', '|---|---|---|']
    for p in paths:
        if os.path.exists(p) and os.path.getsize(p) > 1:
            try:
                n = len(pd.read_csv(p))
            except Exception:
                n = 0
            L.append('| `%s` | %s | %s |'
                     % (os.path.relpath(p, _R), f'{n:,}',
                        hashlib.md5(open(p, 'rb').read()).hexdigest()[:12]))
    return '\n'.join(L)


def md_a1(mode='A'):
    fa = os.path.join(OUT, 'mode%s_a1_slots.csv' % mode)
    fn = os.path.join(OUT, 'mode%s_a1_nulls.csv' % mode)
    fc = os.path.join(OUT, 'mode%s_a1_c1xc2.csv' % mode)
    A = pd.read_csv(fa); N = pd.read_csv(fn); C = pd.read_csv(fc)
    L = []; a = L.append
    a('# A1 — SLOT MAIN EFFECTS, MODE %s\n' % mode)
    a('Generated %s by `code/r2reads.py`, a **pure read** of the gate 2 bank '
      '(`win` and `combo`). Nothing was scored and the engine was not run.\n'
      % time.strftime('%F %H:%M'))
    a('**Trade year is the primary unseen record**; the grade year is reported '
      'separately as a second independent read. **Significance is on the five '
      'yearly values**, not per trade: `t = mean/(sd/sqrt(5))` over the five '
      'per-year R-per-trade figures, which is the honest unit for "does this '
      'option work across years".\n')
    a('\n## Does any slot beat its own label-shuffle null?\n')
    a('The null shuffles option labels within the slot across strategies, '
      '%d draws, and takes the BEST option each time — so the p-value is '
      'against **best-of-slot**, which is what a reader actually looks at.\n'
      % int(N.n_draws.max()))
    for role in ROLES:
        a('\n**%s year**\n' % role.upper())
        a(_tbl(N[N.role == role], ['slot', 'n_options', 'best_option',
                                   'best_R_per_trade', 'null_mean', 'null_p95',
                                   'null_max', 'p_best_of_slot']))
    cl = N[(N.role == 'trade') & (N.p_best_of_slot <= 0.05)]
    a('\n**%d of %d slots clear p<=0.05 on the trade year.**\n'
      % (len(cl), len(N[N.role == 'trade'])))
    a('\n## Every option, trade year, pooled over the four streams\n')
    t = A[(A.role == 'trade') & (A.stream == 'ALL')].sort_values('R_per_trade',
                                                                 ascending=False)
    yrs = [c for c in A.columns if c.startswith('R_2')]
    a(_tbl(t, ['slot', 'option', 'n_strategies', 'n_trades', 'R_per_trade',
               'total_R', 'years_positive', 't_on_5_years'] + sorted(yrs)))
    a('\n## Per stream, trade year — top 10 options by R per trade in each\n')
    for s in list(G2.STREAMS):
        g = A[(A.role == 'trade') & (A.stream == s)].sort_values('R_per_trade',
                                                                 ascending=False).head(10)
        a('\n**%s**\n' % s)
        a(_tbl(g, ['slot', 'option', 'n_strategies', 'R_per_trade',
                   'years_positive', 't_on_5_years']))
    a('\n## Grade year, pooled — the second unseen read\n')
    gt = A[(A.role == 'grade') & (A.stream == 'ALL')].sort_values('R_per_trade',
                                                                  ascending=False).head(30)
    a(_tbl(gt, ['slot', 'option', 'n_strategies', 'R_per_trade', 'years_positive',
                't_on_5_years']))
    a('\n## C1 x C2 — top 30 pairs, trade year\n')
    cc = C[C.role == 'trade'].sort_values('R_per_trade', ascending=False).head(30)
    a(_tbl(cc, ['c1', 'c2', 'n_strategies', 'n_trades', 'R_per_trade', 'total_R']))
    a('\n## Provenance\n')
    a(_prov([fa, fn, fc]))
    p = os.path.join(OUT, 'A1_SLOTS.md')
    open(p, 'w').write('\n'.join(L) + '\n')
    print('  A1_SLOTS.md: %d lines -> %s'
          % (len('\n'.join(L).splitlines()), os.path.relpath(p, _R)), flush=True)
    return p


def md_a1b(mode='A'):
    f = os.path.join(OUT, 'mode%s_a1b_walkforward.csv' % mode)
    D = pd.read_csv(f)
    real = D[D.rule.isin(['c1_and_c2_in_topK', 'c1_in_topK'])]
    nl = D[D.rule.str.startswith('NULL')]
    L = []; a = L.append
    a('# A1b — WALK-FORWARD COMPONENT SELECTION, MODE %s\n' % mode)
    a('Generated %s by `code/r2reads.py`, a **pure read** of the gate 2 bank.\n'
      % time.strftime('%F %H:%M'))
    a('For each step, every slot option is ranked by its main effect on **that '
      'step\'s four TUNING years only**. The book is then all strategies whose '
      'C1 and C2 are both in the top K (and separately, C1 alone), traded on '
      '**that step\'s unseen trade year**, everyone equal weight. K is swept over '
      'its full range.\n')
    a('\n**This replaces A7, which was mis-posed.** A7 picked components on '
      '2016-2020 and scored them on the same years. Here the ranking sees only '
      'tuning years and the book is traded on an unseen one, so it is a walk '
      'forward rather than a restatement.\n')
    a('\n## The curve: equal-weight R per trade on the unseen trade year\n')
    g = real.groupby(['rule', 'K'], as_index=False).agg(
        mean_eq_R=('eq_R_per_trade', 'mean'), mean_tw_R=('tw_R_per_trade', 'mean'),
        mean_members=('members', 'mean'), steps=('step', 'nunique'))
    a(_tbl(g, ['rule', 'K', 'steps', 'mean_members', 'mean_eq_R', 'mean_tw_R']))
    a('\n## Against the label-shuffle null\n')
    if len(nl):
        gn = nl.groupby('K', as_index=False).agg(
            real=('real_eq_R_per_trade', 'mean'), null_mean=('eq_R_per_trade', 'mean'),
            null_p95=('null_p95', 'mean'), p=('p_one_sided', 'mean'),
            draws=('n_draws', 'max'))
        a(_tbl(gn, ['K', 'real', 'null_mean', 'null_p95', 'p', 'draws']))
        best = gn.loc[gn.p.idxmin()] if gn.p.notna().any() else None
        if best is not None:
            a('\nLowest null p is **%.3f at K=%d**. A component rule that beat '
              'chance would show p well under 0.05 across K, not at one value.\n'
              % (best.p, int(best.K)))
    a('\n## Per step, per K\n')
    a(_tbl(real.sort_values(['rule', 'step', 'K']),
           ['step', 'trade_year', 'rule', 'K', 'members', 'eq_R_per_trade',
            'tw_R_per_trade', 'total_R', 'n_trades']))
    a('\n## What this does NOT report, and why\n')
    a('Jack asked for this "at Team 1 through A6". **That is not a bank read.** '
      'A6 needs a daily equity series, and a component book of thousands of '
      'strategies has no saved daily series — producing one is a book pass '
      'through the engine, not a read. The figures above are therefore in R '
      'space. Putting this book through A6 is a chunk-2 or later item and is '
      'registered as such rather than faked here.\n')
    a('\n## Provenance\n')
    a(_prov([f]))
    p = os.path.join(OUT, 'A1B_WALKFORWARD.md')
    open(p, 'w').write('\n'.join(L) + '\n')
    print('  A1B_WALKFORWARD.md: %d lines -> %s'
          % (len('\n'.join(L).splitlines()), os.path.relpath(p, _R)), flush=True)
    return p


def md_a6(mode='A', labels=('winners', 'full')):
    fs = [os.path.join(OUT, 'mode%s_a6_propsim_%s.csv' % (mode, l)) for l in labels]
    fs = [f for f in fs if os.path.exists(f)]
    D = pd.concat([pd.read_csv(f) for f in fs], ignore_index=True) if fs else pd.DataFrame()
    L = []; a = L.append
    a('# A6 — THE PROP SIMULATOR, MODE %s\n' % mode)
    a('Generated %s by `code/r2reads.py`, a **pure read** of the saved daily '
      'series. Built as a standing stage: every later book runs through it.\n'
      % time.strftime('%F %H:%M'))
    a('\n## The rules as modelled\n')
    a('| rule | value |\n|---|---|')
    a('| trailing floor | 6%% below the high-water mark, **stops trailing permanently once the floor reaches the starting balance** — after equity touches +6%% once, the floor is $100k forever. Not a start-of-day lock. |')
    a('| open equity | counts for the trailing line, rolling |')
    a('| daily loss | 4%%, measured from the previous daily close; floating losses count; resets daily |')
    a('| evaluation | profit target 10%%, no time limit, no minimum days, no consistency rule |')
    a('| payout | 80%%, from day 0, every 7 days |')
    a('| fee | $549; evaluation resettable, funded not |')
    a('| leverage | 1:30 |')
    a('| internal budgets | 3.6%% daily, 5.4%% trailing — reported alongside the firm\'s |')
    a('\n**WHAT THIS CANNOT SEE.** The input is a DAILY series, so open equity is '
      'only observable at the close. Rules written on intraday open equity are '
      'evaluated at day granularity, which makes every breach count below a '
      '**LOWER BOUND**: an intraday excursion that breached and recovered before '
      'the close is invisible here. A5\'s hourly replay is what would tighten it.\n')
    if not len(D):
        a('\n_No runs on disk yet._\n')
    else:
        a('\n## Evaluation phase\n')
        e = D[D.phase == 'eval']
        a(_tbl(e, ['source', 'book', 'budget', 'rules', 'days', 'passed_eval_day',
                   'breached', 'equity_end', 'worst_dip_pct']))
        a('\n**%d of %d evaluation runs reached the 10%% target; %d breached.**\n'
          % (int(e.passed_eval_day.notna().sum()), len(e), int((e.breached.fillna('') != '').sum())))
        a('\n## Funded phase — fixed sizing, payout cushion swept\n')
        g = D[(D.phase == 'funded') & (D.sizing == 'fixed')]
        a(_tbl(g.sort_values('paid_out_per_year', ascending=False),
               ['source', 'book', 'budget', 'rules', 'keep_cushion', 'days',
                'breached', 'paid_out_per_year', 'return_pct_per_year',
                'worst_dip_pct', 'net_per_year_usd']))
        a('\n## Funded phase — sizing proportional to the cushion above the floor\n')
        c = D[(D.phase == 'funded') & (D.sizing == 'cushion')]
        a(_tbl(c.sort_values('paid_out_per_year', ascending=False),
               ['source', 'book', 'budget', 'rules', 'size_frac', 'days',
                'breached', 'paid_out_per_year', 'return_pct_per_year',
                'worst_dip_pct', 'net_per_year_usd']))
        nb = int((D[D.phase == 'funded'].breached.fillna('') != '').sum())
        a('\n**%d of %d funded runs breached.** Best payout is **$%.0f a year** '
          'before the $549 fee.\n'
          % (nb, len(D[D.phase == 'funded']),
             float(D[D.phase == 'funded'].paid_out_per_year.max())))
    a('\n## Provenance\n')
    a(_prov(fs))
    p = os.path.join(OUT, 'A6_PROPSIM.md')
    open(p, 'w').write('\n'.join(L) + '\n')
    print('  A6_PROPSIM.md: %d lines -> %s'
          % (len('\n'.join(L).splitlines()), os.path.relpath(p, _R)), flush=True)
    return p


if __name__ == '__main__':
    st = G.opt('--stage', str, 'a1')
    md = G.opt('--mode', str, 'A')
    nd = G.opt('--draws', int, 1000)
    nm = G.opt('--nmax', int, None)
    if st == 'a1':
        stage_a1(md, ndraw=nd, nmax=nm); md_a1(md)
    elif st == 'a1b':
        stage_a1b(md, ndraw=nd, nmax=nm); md_a1b(md)
    elif st == 'a6':
        stage_a6(md, src_tag='g3passwinners', books=['allon'], label='winners')
        stage_a6(md, src_tag='full', label='full')
        md_a6(md)
    else:
        raise SystemExit('unknown stage %s' % st)
