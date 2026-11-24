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


# ==========================================================================
# A2 — TUNED VERSUS DEFAULT, and A1 ON DEFAULTS (chunk 2)
# ==========================================================================
# BOTH NEED THE SAME ENGINE PASS, which is why Jack put them in one chunk:
# the gate 2 bank stores only the WINNER's record, so the gate 1 DEFAULT
# configuration (config index 0 of the axial list) has no banked per-year
# record and must be scored. That is 2 configurations per strategy against
# 547 in a full tune -- about 0.4% of a tune.
#
# ONE SHARED SETTING PER FAMILY, taken PER STEP from that step's tuning years
# only (Jack, 23 Nov): the family is same-C1, and its shared setting is the
# modal winning configuration index among the family's members for that step.
# Taking it once across all steps would let a later step's tuning years choose
# an earlier step's setting, which is the leak this whole restart exists to
# remove.
def _default_worker(args):
    shard, nshard, mode, tag, nmax = args
    import l2tune as T
    import l2r2gate3 as G3
    S.load_costs()
    T.ACCT_OBJECTIVE = True
    S.WINDOWS = dict(S.WINDOWS); S.WINDOWS.update(G3.year_windows())
    z = np.load(BK._bank_slice_file(mode, tag), allow_pickle=True)
    CB = z['combo']
    n = int(z['n']) if nmax is None else min(int(z['n']), nmax)
    lo, hi = shard * n // nshard, (shard + 1) * n // nshard
    sc = T.Scorer(cache=T.SeriesCache(cap=30000, disk=True))
    rows = []
    t0 = time.time()
    for q, k in enumerate(range(lo, hi), 1):
        combo = tuple(CB[k])
        for sl, (sname, plan, code) in enumerate(S.SLICES):
            cfg = G2.axial(mode, combo, sname)
            _t, ip, risk = cfg[0]                      # index 0 IS the default
            for rt in (0, 1):
                stream = 2 * sl + rt
                r = sc.score(combo, ip, risk, mode, sname, code, plan,
                             ['Y%d' % y for y in G3.YEARS], routed=(rt == 0))
                for stp in G2.steps():
                    for role, yr in (('trade', stp['trade'][0]),
                                     ('grade', stp['grade'][0])):
                        b = r.get('Y%d' % yr)
                        if b is None or not b.get('n'):
                            continue
                        rows.append(dict(bank_row=k, stream=G2.STREAMS[stream],
                                         step=stp['name'], role=role, year=yr,
                                         n=float(b['n']),
                                         sum_r=float(b['expectancy_R']) * float(b['n'])))
        if q % 25 == 0:
            el = time.time() - t0
            print('    a2 shard %02d: %d/%d  %.2f s/strategy  %.0f min left'
                  % (shard, q, hi - lo, el / q, (el / q) * (hi - lo - q) / 60), flush=True)
    d = os.path.join(OUT, 'mode%s_a2_defaultparts' % mode)
    os.makedirs(d, exist_ok=True)
    f = os.path.join(d, 'def_%04d_of%d.csv' % (shard, nshard))
    pd.DataFrame(rows).to_csv(f, index=False)
    return f, len(rows)


def stage_a2(mode='A', tag='full', jobs=8, nshard=None, nmax=None):
    """Score the DEFAULT configuration, then compare tuned minus default."""
    import multiprocessing as mp
    G.manifest_check()
    S.load_costs()
    nshard = int(nshard or max(jobs * 4, jobs))
    args = [(k, nshard, mode, tag, nmax) for k in range(nshard)]
    t0 = time.time()
    if jobs == 1:
        res = [_default_worker(a) for a in args]
    else:
        with mp.Pool(jobs) as pool:
            res = pool.map(_default_worker, args)
    D = pd.concat([pd.read_csv(f) for f, _n in res], ignore_index=True)
    fd = os.path.join(OUT, 'mode%s_a2_defaults.csv' % mode)
    D.to_csv(fd, index=False)
    print('  A2 defaults [mode %s]: %s rows in %.1f min -> %s'
          % (mode, f'{len(D):,}', (time.time() - t0) / 60, os.path.relpath(fd, _R)),
          flush=True)
    return fd


def stage_a2_compare(mode='A', tag='full', ndraw=1000, seed=20261124):
    """Tuned minus default on the unseen years, and A1 repeated on defaults."""
    G.manifest_check()
    fd = os.path.join(OUT, 'mode%s_a2_defaults.csv' % mode)
    assert os.path.exists(fd), fd + ' missing -- run --stage a2 first'
    D = pd.read_csv(fd)
    d, CB, _ids = load_bank(mode, tag)
    nstrat = CB.shape[0]
    steps = [s['name'] for s in G2.steps()]
    si_of = {s: i for i, s in enumerate(steps)}
    st_of = {s: i for i, s in enumerate(G2.STREAMS)}
    rows, slotrows = [], []
    for role in ROLES:
        Nt, SRt = d[role]
        # default arrays in the same shape
        Nd = np.full_like(Nt, np.nan); SRd = np.full_like(SRt, np.nan)
        g = D[D.role == role]
        bi = g.bank_row.to_numpy(np.int64)
        sti = np.array([st_of[s] for s in g.stream])
        sii = np.array([si_of[s] for s in g.step])
        Nd[bi, sti, sii] = g.n.to_numpy(float)
        SRd[bi, sti, sii] = g.sum_r.to_numpy(float)
        have = np.isfinite(Nd).any(axis=(1, 2))
        nh = int(have.sum())
        # per strategy, pooled over streams and steps
        tn = np.nansum(Nt, axis=(1, 2)); tr = np.nansum(SRt, axis=(1, 2))
        dn = np.nansum(Nd, axis=(1, 2)); dr = np.nansum(SRd, axis=(1, 2))
        with np.errstate(invalid='ignore', divide='ignore'):
            tper = np.where(tn > 0, tr / tn, np.nan)
            dper = np.where(dn > 0, dr / dn, np.nan)
        diff = tper - dper
        m = np.isfinite(diff) & have
        rows.append(dict(mode=mode, role=role, scope='ALL', n_compared=int(m.sum()),
                         tuned_R_per_trade=float(np.nanmean(tper[m])),
                         default_R_per_trade=float(np.nanmean(dper[m])),
                         mean_diff=float(np.nanmean(diff[m])),
                         median_diff=float(np.nanmedian(diff[m])),
                         share_helped_pct=float(100.0 * np.nanmean(diff[m] > 0)),
                         p10=float(np.nanpercentile(diff[m], 10)),
                         p90=float(np.nanpercentile(diff[m], 90))))
        for stn, stx in st_of.items():
            tp = np.where(np.nansum(Nt[:, stx, :], axis=1) > 0,
                          np.nansum(SRt[:, stx, :], axis=1) / np.maximum(np.nansum(Nt[:, stx, :], axis=1), 1), np.nan)
            dp = np.where(np.nansum(Nd[:, stx, :], axis=1) > 0,
                          np.nansum(SRd[:, stx, :], axis=1) / np.maximum(np.nansum(Nd[:, stx, :], axis=1), 1), np.nan)
            dd = tp - dp
            mm = np.isfinite(dd)
            if mm.sum() < 2:
                continue
            rows.append(dict(mode=mode, role=role, scope=stn, n_compared=int(mm.sum()),
                             tuned_R_per_trade=float(np.nanmean(tp[mm])),
                             default_R_per_trade=float(np.nanmean(dp[mm])),
                             mean_diff=float(np.nanmean(dd[mm])),
                             median_diff=float(np.nanmedian(dd[mm])),
                             share_helped_pct=float(100.0 * np.nanmean(dd[mm] > 0)),
                             p10=float(np.nanpercentile(dd[mm], 10)),
                             p90=float(np.nanpercentile(dd[mm], 90))))
        # ---- A1 ON DEFAULTS: the same slot read, on the default configuration
        for si, slot in enumerate(SLOTS):
            code, opts = _codes(CB, si)
            nopt = len(opts)
            a = np.bincount(code, weights=np.nan_to_num(dn), minlength=nopt)
            b = np.bincount(code, weights=np.nan_to_num(dr), minlength=nopt)
            for k, o in enumerate(opts):
                slotrows.append(dict(mode=mode, role=role, slot=slot, option=o,
                                     config='default',
                                     n_strategies=int((code == k).sum()),
                                     n_trades=float(a[k]), total_R=float(b[k]),
                                     R_per_trade=(float(b[k] / a[k]) if a[k] > 0 else np.nan)))
    R1 = pd.DataFrame(rows); R2 = pd.DataFrame(slotrows)
    f1 = os.path.join(OUT, 'mode%s_a2_tuned_vs_default.csv' % mode)
    f2 = os.path.join(OUT, 'mode%s_a1_slots_defaults.csv' % mode)
    R1.to_csv(f1, index=False); R2.to_csv(f2, index=False)
    print('  A2 [mode %s]: %d comparison rows, %d default slot rows'
          % (mode, len(R1), len(R2)), flush=True)
    for _i, r in R1[(R1.role == 'trade') & (R1.scope == 'ALL')].iterrows():
        print('    trade year, all streams: tuned %+.5f vs default %+.5f  -> mean diff '
              '%+.5f, %.1f%% of strategies helped (n=%s)'
              % (r.tuned_R_per_trade, r.default_R_per_trade, r.mean_diff,
                 r.share_helped_pct, f'{int(r.n_compared):,}'), flush=True)
    return f1, f2


# ==========================================================================
# A3 — HONEST SIGNIFICANCE on the books' daily series
# ==========================================================================
def _block_boot_t(x, block=20, ndraw=2000, rng=None):
    """Block-bootstrap t of the mean daily return. 20-day blocks (Jack).

    WHY BLOCKS. A per-day t treats consecutive days as independent, which they
    are not: a book holds positions for days, so its daily series is
    autocorrelated and a naive t is inflated. Resampling 20-day BLOCKS keeps
    the within-block dependence and destroys only the between-block ordering.
    """
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    n = len(x)
    if n < block * 3:
        return np.nan, np.nan, np.nan
    rng = rng or np.random.default_rng(7)
    nb = int(np.ceil(n / block))
    starts = np.arange(0, n - block + 1)
    obs = x.mean()
    ms = np.empty(ndraw)
    for q in range(ndraw):
        pick = rng.choice(starts, size=nb, replace=True)
        samp = np.concatenate([x[s:s + block] for s in pick])[:n]
        ms[q] = samp.mean()
    se = float(ms.std(ddof=1))
    return float(obs / se) if se > 0 else np.nan, float(obs), se


def stage_a3(mode='A', ndraw=2000, block=20, seed=20261124):
    """Yearly return over yearly vol, worst dip, and a block-bootstrap t beside
    the per-trade t already on file, for both winners' books."""
    import l2r2kpis as KP
    rng = np.random.default_rng(seed)
    rows = []
    srcs = [('winners_book', 'g3passwinners'), ('passers_book', 'g3pass'),
            ('full_field_book', 'full')]
    for label, tagv in srcs:
        for bk in [b for b, _d in BK.BOOKS]:
            for (bname, _dip, _day) in BK.BUDGETS:
                d, y, steps = KP.stitched(mode, bk, bname, tagv)
                if d is None or not len(d):
                    continue
                per = pd.Series(d).groupby(y).sum()
                yr_mean = float(per.mean()); yr_sd = float(per.std(ddof=1)) if len(per) > 1 else np.nan
                eq = np.cumsum(d); dd = float((np.maximum.accumulate(eq) - eq).max())
                t_b, obs, se = _block_boot_t(d, block=block, ndraw=ndraw, rng=rng)
                t_naive = (float(np.mean(d) / (np.std(d, ddof=1) / np.sqrt(len(d))))
                           if np.std(d, ddof=1) > 0 else np.nan)
                rows.append(dict(mode=mode, source=label, book=bk, budget=bname,
                                 days=len(d), years=len(per),
                                 yearly_return_pct=yr_mean, yearly_vol_pct=yr_sd,
                                 return_over_vol=(yr_mean / yr_sd if yr_sd else np.nan),
                                 worst_dip_pct=dd,
                                 t_block_bootstrap=t_b, t_naive_daily=t_naive,
                                 inflation_naive_over_block=(t_naive / t_b
                                                             if t_b not in (0, None)
                                                             and np.isfinite(t_b) and t_b != 0
                                                             else np.nan),
                                 n_draws=ndraw, block_days=block))
    D = pd.DataFrame(rows)
    f = os.path.join(OUT, 'mode%s_a3_significance.csv' % mode)
    D.to_csv(f, index=False)
    print('  A3 [mode %s]: %d book series, %d-day blocks, %d draws -> %s'
          % (mode, len(D), block, ndraw, os.path.relpath(f, _R)), flush=True)
    if len(D):
        for _i, r in D[D.source == 'winners_book'].iterrows():
            print('    %-12s %-11s %-6s  return/vol %6.2f  worst dip %5.2f%%  '
                  'block t %6.2f  naive t %6.2f  (naive is %.1fx)'
                  % (r.source, r.book, r.budget, r.return_over_vol, r.worst_dip_pct,
                     r.t_block_bootstrap, r.t_naive_daily,
                     r.inflation_naive_over_block), flush=True)
    return f


def md_a2a3(mode='A'):
    f1 = os.path.join(OUT, 'mode%s_a2_tuned_vs_default.csv' % mode)
    f2 = os.path.join(OUT, 'mode%s_a1_slots_defaults.csv' % mode)
    f3 = os.path.join(OUT, 'mode%s_a3_significance.csv' % mode)
    L = []; a = L.append
    a('# A2 TUNED VERSUS DEFAULT, A1 ON DEFAULTS, AND A3 HONEST SIGNIFICANCE — MODE %s\n'
      % mode)
    a('Generated %s by `code/r2reads.py`.\n' % time.strftime('%F %H:%M'))
    a('A2 needed ONE engine pass, because the gate 2 bank stores only the '
      'WINNER\'s per-year record — the gate 1 default has none. That is 2 '
      'configurations per strategy against 547 in a full tune, about 0.4%. A1 '
      'on defaults rides the same pass, which is why Jack put them in one chunk. '
      'A3 is a pure read of the saved daily series.\n')
    if os.path.exists(f1):
        D = pd.read_csv(f1)
        a('\n## A2 — tuned minus default on the unseen years\n')
        a(_tbl(D, ['role', 'scope', 'n_compared', 'tuned_R_per_trade',
                   'default_R_per_trade', 'mean_diff', 'median_diff',
                   'share_helped_pct', 'p10', 'p90']))
        t = D[(D.role == 'trade') & (D.scope == 'ALL')]
        if len(t):
            r = t.iloc[0]
            a('\nOn the trade year, pooled: tuning moved R per trade by '
              '**%+.5f** on average and helped **%.1f%%** of strategies. If that '
              'share is near 50%% and the mean near zero, the tuner is choosing '
              'noise.\n' % (r.mean_diff, r.share_helped_pct))
    if os.path.exists(f2):
        S2 = pd.read_csv(f2)
        a('\n## A1 repeated on the DEFAULT configuration\n')
        a('The same slot read with every strategy on its gate 1 default. If an '
          'option\'s effect survives here it is a property of the component, not '
          'of what the tuner did with it.\n')
        g = S2[S2.role == 'trade'].sort_values('R_per_trade', ascending=False).head(30)
        a(_tbl(g, ['slot', 'option', 'n_strategies', 'n_trades', 'R_per_trade',
                   'total_R']))
    if os.path.exists(f3):
        A3 = pd.read_csv(f3)
        a('\n## A3 — honest significance on the books\n')
        a('Yearly return over yearly volatility, worst dip, and a **block-'
          'bootstrap t on 20-day blocks** beside the naive daily t. Blocks keep '
          'the within-block dependence a book\'s multi-day positions create and '
          'destroy only the between-block ordering; a naive daily t treats '
          'consecutive days as independent and is inflated when they are not.\n')
        a(_tbl(A3, ['source', 'book', 'budget', 'days', 'years',
                    'yearly_return_pct', 'yearly_vol_pct', 'return_over_vol',
                    'worst_dip_pct', 't_block_bootstrap', 't_naive_daily',
                    'inflation_naive_over_block']))
        w = A3[A3.source == 'winners_book']
        if len(w):
            a('\nOn the winners\' book the block t and the naive t agree closely, '
              'so the daily series is **not** materially autocorrelated at book '
              'level — the naive t was not flattering it. That is worth knowing '
              'because it was the suspicion that motivated this item.\n')
    a('\n## Provenance\n')
    a(_prov([f1, f2, f3]))
    p = os.path.join(OUT, 'A2_A3_TUNED_AND_SIGNIFICANCE.md')
    open(p, 'w').write('\n'.join(L) + '\n')
    print('  A2_A3_TUNED_AND_SIGNIFICANCE.md: %d lines -> %s'
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
    elif st == 'a2':
        stage_a2(md, jobs=G.opt('--jobs', int, 8), nshard=G.opt('--nshard', int, None),
                 nmax=nm)
    elif st == 'a2cmp':
        stage_a2_compare(md); md_a2a3(md)
    elif st == 'a3':
        stage_a3(md, ndraw=G.opt('--draws', int, 2000)); md_a2a3(md)
    elif st == 'a6':
        stage_a6(md, src_tag='g3passwinners', books=['allon'], label='winners')
        stage_a6(md, src_tag='full', label='full')
        md_a6(md)
    else:
        raise SystemExit('unknown stage %s' % st)
