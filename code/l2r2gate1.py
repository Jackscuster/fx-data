import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""LAYER 2 RESTART -- HONEST GATE 1 (`_r2`).  Jack, 16 Nov.

WHY THE RESTART.  The gate 1 on disk is not usable as a gate.  Its score was
taken over W2+W3 = 2011-01-01 to 2020-12-31 (l2sweep.score_combo), which is
every year Layer 2 later called blind.  The survivors were therefore chosen on
the same years their record was then reported on.  Four further contaminations
touched it and are listed in HANDOFF 0l.  Nothing is deleted: the old files
keep their names, get a SUPERSEDED BY 0l header, and everything here is `_r2`.

WHAT IS HONEST HERE.
  * Every combination is scored at DEFAULTS, costs ON, one-bar lag, 28 pairs,
    sealed at 2020-12-31.
  * Trades are attributed to the calendar year of their ENTRY bar, and the
    bank keeps PER YEAR counts and sums.  Tune, grade and trade years are
    therefore kept separately by construction and cannot be pooled by accident.
  * THE CUT READS TUNE-YEAR SCORES ONLY.  Grade and trade years are banked and
    reported; they never enter the selection.
  * Four streams per combination, every one of them measured, none selected
    on: trend-routed, trend-always-on, chop-routed, chop-always-on.  Routing is
    a mask on one engine pass, so always-on costs nothing extra and regime
    dependence is measured per combination rather than assumed.
  * No arbitrary threshold.  The cut is one number -- tune-year expectancy in R
    -- swept over its whole observed range and reported as a curve.

THE BANK.  results/r2gate1/mode<M>/shard_XXXX.npz, one row per combination,
array `stat` of shape (n_combo, 4, NYEAR, 5):
    axis 1  0 trend-routed  1 trend-always-on  2 chop-routed  3 chop-always-on
    axis 2  calendar year, YEAR0..YEAR0+NYEAR-1
    axis 3  n, sum_r, gain, loss, n_win
Every window/role aggregation in the programme is derivable from this without
rerunning the engine, which is the whole reason it is banked this way: the five
rolling windows are masks over one pass, not five passes.

    python3 code/l2r2gate1.py --stage probe   --mode A
    python3 code/l2r2gate1.py --stage smoke   --mode A --n 10000
    python3 code/l2r2gate1.py --stage curve   --mode A --tag smoke10k
    python3 code/l2r2gate1.py --stage parity  --mode A
"""
import time, json, hashlib, itertools
import numpy as np, pandas as pd
from numba import njit
import l2sweep as S
import l2lib as L

# ---------------------------------------------------------------- the contract
# Layer 1 is consumed exactly as shipped.  The md5 of every file read is
# asserted against the manifest on EVERY load (LAYER1_INTERFACE.md rule 3).
MANIFEST = os.path.join(ROOTOUT, 'layer1_interface_manifest_2026-11-16.csv')
L1_FILES = ('results/layer1_states.csv', 'results/layer1_trend_quality_series.csv')


def manifest_check(paths=L1_FILES):
    M = pd.read_csv(MANIFEST).set_index('path')
    for p in paths:
        want = str(M.loc[p, 'md5'])
        got = hashlib.md5(open(os.path.join(_R, p), 'rb').read()).hexdigest()
        assert got.startswith(want), 'LAYER 1 INTERFACE md5 MISMATCH %s: manifest %s, file %s' % (p, want, got[:12])
    print('  layer 1 interface: %d files, md5 matches the manifest' % len(paths), flush=True)
    return True


# ---------------------------------------------------------------- the windows
# HANDOFF 0f, unchanged: tune years 1-4, grade year 5 REPORTED NEVER USED,
# trade year 6.  Five of them, rolling one year.
WINDOWS_SPEC = '2011-2014:2015:2016,2012-2015:2016:2017,2013-2016:2017:2018,2014-2017:2018:2019,2015-2018:2019:2020'
# 2005..2020, the whole sealed panel.  `--years 2011-2020` narrows the bank to
# exactly the years the five windows use; it is a STORAGE choice and nothing
# else, because no window in 0f touches a year before 2011.  Mode C needs it:
# the full 16-year bank measures 6.4 GB compressed against 5.3 GB of free disk,
# and 10 years measures 4.0 GB.  Every bank records its own range, so a curve
# read from one can never silently use the wrong years.
YEAR0, NYEAR = 2005, 16
STREAMS = ('trend-routed', 'trend-allon', 'chop-routed', 'chop-allon')
NSTAT = 5                        # n, sum_r, gain, loss, n_win


def windows():
    out = []
    for part in WINDOWS_SPEC.split(','):
        b, g, t = part.split(':')
        b0, b1 = (int(x) for x in b.split('-'))
        out.append(dict(name='%d-%d' % (b0, b1), tune=(b0, b1), grade=(int(g), int(g)), trade=(int(t), int(t))))
    return out


# ---------------------------------------------------------------- the family rule
# DECLARED BEFORE THE RUN (HANDOFF 0l).  A FAMILY is the ORDERED confirmation
# pair (c1, c2) within one mode and one slice -- 39 x 39 = 1,521 families.
# Ordered, not unordered: in mode A the C1 flip is the exit, so c1 and c2 are
# not interchangeable and folding them together would merge two different
# machines.  vol and base are filters over that pair, not the signal.
# A family PASSES a cut if at least one of its combinations passes.
# A LONE SURVIVOR is a family passing with exactly one combination.  Lone
# survivors are FLAGGED, never killed -- whether one is luck is a question the
# nulls answer, not a question the cut gets to answer by fiat.
def family_of(c1, c2):
    return '%s|%s' % (c1, c2)


# ---------------------------------------------------------------- the kernel
# cache=False DELIBERATELY. numba's on-disk cache pickles the module environment
# of whichever process compiled it first; a worker compiles it as `__mp_main__`,
# and the next single-process run then dies on ModuleNotFoundError trying to
# rebuild that environment. The function compiles in well under a second, so the
# cache buys nothing and costs a dead chain.
@njit(cache=False)
def _accumulate(r, eb, nt, ybar, reg, code, acc, s_routed, s_allon):
    """Per-year accumulation for one pair, one plan, both routings.

    ybar[bar] is the year index of that bar, or -1 outside [YEAR0, YEAR0+NYEAR).
    `code` is the Layer 1 regime code this slice routes on; routing is a mask on
    the SAME trades, so the engine runs once and both streams come out of it.
    """
    for i in range(nt):
        b = eb[i]
        y = ybar[b]
        if y < 0:
            continue
        v = r[i]
        rt = reg[b] == code
        for k in range(2):
            if k == 0:
                if not rt:
                    continue
                s = s_routed
            else:
                s = s_allon
            acc[s, y, 0] += 1.0
            acc[s, y, 1] += v
            if v > 0.0:
                acc[s, y, 2] += v
                acc[s, y, 4] += 1.0
            else:
                acc[s, y, 3] -= v


def crisis_mult_bars(pair, dates):
    """Per-BAR crisis cost multiplier, built once per pair.

    S._cost_R does this per trade with a Python loop over 50 calendar windows,
    which at ~28,000 trade-dates per combination is 85% of the cost of a gate 1
    evaluation. The multiplier depends only on (pair, bar), so it is hoisted
    here. `--stage parity` proves the result is identical to the shipped path
    trade for trade; nothing about the cost CONVENTION changes.
    """
    m = np.ones(len(dates), np.float64)
    if not S._CRISIS_WIN:
        return m
    d = pd.DatetimeIndex(dates)
    for a, z, ccy, _ in S._CRISIS_WIN:
        if ccy and ccy not in (pair[:3], pair[3:]):
            continue
        m[(d >= a) & (d <= z)] = S.CRISIS_MULT
    return m


def year_bars(P):
    """bar -> year index, -1 outside the banked range."""
    yr = P['dates'].year.values.astype(np.int64)
    y = yr - YEAR0
    y[(y < 0) | (y >= NYEAR)] = -1
    return y.astype(np.int64)


def score_r2(PD, combo, BUF, kwm):
    """One combination, all four streams, per year.  -> (4, NYEAR, 5) float64.

    The engine is run once per (pair, plan).  `plan` is a property of the slice
    candidate -- trend is the two-leg run, chop the one-leg run (GAUNTLET) --
    so there are two engine passes per pair, exactly as the original gate 1 had,
    and the always-on stream is free.
    """
    c1, c2, vol, base, ex = combo
    acc = np.zeros((4, NYEAR, NSTAT), np.float64)
    for sname, plan, code in S.SLICES:
        sr, sa = (0, 1) if sname == 'trend' else (2, 3)
        for pair, P in PD.items():
            buf = BUF[pair]
            nt = S.run_combo(P, c1, c2, vol, base, ex, buf, plan=plan, **kwm)
            if nt == 0:
                continue
            r = buf['r'][:nt].copy()
            eb = buf['entry_bar'][:nt]
            if S.COSTS and P['_cfrac']:
                # FAULT #27.  At gate 1 every combination runs at atr_mult=1.0,
                # so the restatement factor is 1.0 -- but it is written out
                # rather than assumed, because the same expression is reused
                # when the multiples move.  Identical to S._cost_R by
                # construction and proven so by --stage parity.
                r = r - (float(kwm.get('atr_mult', S.ATR_MULT)) * P['_cfrac']
                         * P['_cmult'][eb] * np.abs(buf['entry_px'][:nt])
                         * np.abs(buf['units'][:nt]) / S.RISK)
            _accumulate(r, eb, nt, P['_yb'], P['regime'], code, acc, sr, sa)
    return acc


# ---------------------------------------------------------------- aggregation
def agg(stat):
    """(..., 5) -> dict of KPIs.  n, expectancy_R, total_R, profit_factor,
    win_rate.  Composable across years BY CONSTRUCTION, which is why the bank
    stores sums rather than KPIs."""
    n = stat[..., 0]
    tot = stat[..., 1]
    gain = stat[..., 2]
    loss = stat[..., 3]
    win = stat[..., 4]
    with np.errstate(divide='ignore', invalid='ignore'):
        e = np.where(n > 0, tot / np.maximum(n, 1), np.nan)
        pf = np.where(loss > 0, gain / np.maximum(loss, 1e-12), np.where(gain > 0, np.inf, np.nan))
        wr = np.where(n > 0, win / np.maximum(n, 1), np.nan)
    return dict(n=n, expectancy_R=e, total_R=tot, profit_factor=pf, win_rate=wr)


def role_slice(stat, y0, y1):
    """Sum the bank over calendar years [y0, y1] inclusive."""
    a, b = y0 - YEAR0, y1 - YEAR0 + 1
    return stat[..., max(a, 0):min(b, NYEAR), :].sum(axis=-2)


# ---------------------------------------------------------------- enumeration
def stratified(opts, n, seed=20261116):
    """n combinations, MARGINALLY BALANCED in every slot.

    A plain uniform sample leaves a 39-option slot with a +-16 count wobble at
    n=10,000, which is enough to make a slot look weak because it was drawn
    less.  Here each slot gets its options tiled to length n and shuffled with
    its own seed, then the slots are zipped: every option appears n/m times to
    within one, and the joint draw is still random.
    """
    rng = np.random.default_rng(seed)
    cols = {}
    for k in S.SLOTS:
        m = opts[k]
        if len(m) == 1:
            cols[k] = np.zeros(n, int)
            continue
        v = np.tile(np.arange(len(m)), int(np.ceil(n / len(m))))[:n]
        rng.shuffle(v)
        cols[k] = v
    out, seen = [], set()
    for i in range(n):
        cb = tuple(opts[k][cols[k][i]] for k in S.SLOTS)
        if cb in seen:
            continue
        seen.add(cb)
        out.append(cb)
    return out


def build_pairdata(opts):
    pairs = S.all_pairs()
    PD, BUF = {}, {}
    for p in pairs:
        P = S.precompute(p, opts)
        P['_yb'] = year_bars(P)
        P['_cfrac'] = (S.COSTS or {}).get(p, 0.0)
        P['_cmult'] = crisis_mult_bars(p, P['dates'])
        PD[p] = P
        BUF[p] = S.make_buffers(len(P['c']))
    return PD, BUF


# ---------------------------------------------------------------- stages
def stage_probe(mode, n=200, jobs=1):
    """Seconds per combination, cache warm, one scoring pass 2011-2020 over 28
    pairs, routed and always-on.  The number STEP 1 is costed from."""
    manifest_check()
    S.load_costs()
    opts = S.mode_opts(S.slot_options(), mode)
    t0 = time.time()
    PD, BUF = build_pairdata(opts)
    t_pre = time.time() - t0
    kwm = S.mode_kw(mode)
    combos = stratified(opts, n + 20, seed=7)
    # warm the jit and the caches on the first 20, then measure the rest
    for cb in combos[:20]:
        score_r2(PD, cb, BUF, kwm)
    t1 = time.time()
    for cb in combos[20:20 + n]:
        score_r2(PD, cb, BUF, kwm)
    el = time.time() - t1
    per = el / n
    print('  probe mode %s: precompute %.0f s (28 pairs, once per worker); '
          '%d combinations in %.1f s = %.1f ms/combination (one core, four streams)'
          % (mode, t_pre, n, el, 1000 * per), flush=True)
    return dict(mode=mode, n=n, seconds=el, per_combo_s=per, precompute_s=t_pre)


def _shard_worker(args):
    shard, nshard, mode, combos, outdir, years = args
    set_years(years)
    f = os.path.join(outdir, 'shard_%04d.npz' % shard)
    if os.path.exists(f):
        return dict(shard=shard, n=0, skipped=True, seconds=0.0)
    S.load_costs()
    opts = S.mode_opts(S.slot_options(), mode)
    kwm = S.mode_kw(mode)
    PD, BUF = build_pairdata(opts)
    mine = [cb for i, cb in enumerate(combos) if i % nshard == shard]
    t0 = time.time()
    stat = np.zeros((len(mine), 4, NYEAR, NSTAT), np.float32)
    for j, cb in enumerate(mine):
        stat[j] = score_r2(PD, cb, BUF, kwm)
        if (j + 1) % 500 == 0:
            el = time.time() - t0
            print('    shard %03d: %6d/%6d  %.1f ms/combo  %.0f min left'
                  % (shard, j + 1, len(mine), 1000 * el / (j + 1),
                     (el / (j + 1)) * (len(mine) - j - 1) / 60), flush=True)
    if free_gb() < DISK_FLOOR_GB:
        print('    shard %03d: HALTING, %.1f GB free (floor %.1f) -- the bank is resumable, rerun when there is room'
              % (shard, free_gb(), DISK_FLOOR_GB), flush=True)
        raise SystemExit('disk floor hit at shard %d' % shard)
    np.savez_compressed(f, stat=stat, year0=YEAR0, nyear=NYEAR,
                        combo=np.array([['%s' % x for x in cb] for cb in mine], dtype=object),
                        idx=np.array([i for i, _ in enumerate(combos) if i % nshard == shard]))
    return dict(shard=shard, n=len(mine), skipped=False, seconds=time.time() - t0)


def set_years(spec):
    global YEAR0, NYEAR
    a, z = (int(x) for x in spec.split('-'))
    YEAR0, NYEAR = a, z - a + 1
    print('  bank years: %d..%d (%d)' % (YEAR0, YEAR0 + NYEAR - 1, NYEAR), flush=True)


def free_gb():
    st = os.statvfs(ROOTOUT)
    return st.f_bavail * st.f_frsize / 1024 ** 3


def stage_run(mode, combos, tag, jobs=None, nshard=None):
    """Bank `combos` for `mode`, sharded and RESUMABLE -- a shard file that
    exists is never recomputed, so a killed run resumes where it stopped."""
    import multiprocessing as mp
    manifest_check()
    outdir = os.path.join(ROOTOUT, 'r2gate1', 'mode%s_%s' % (mode, tag))
    os.makedirs(outdir, exist_ok=True)
    jobs = jobs or max(1, (os.cpu_count() or 2) - 2)
    nshard = nshard or jobs
    with open(os.path.join(outdir, 'combos.json'), 'w') as fh:
        json.dump([list(c) for c in combos], fh)
    years = '%d-%d' % (YEAR0, YEAR0 + NYEAR - 1)
    with open(os.path.join(outdir, 'years.txt'), 'w') as fh:
        fh.write(years)
    if free_gb() < DISK_FLOOR_GB:
        raise SystemExit('refusing to start: %.1f GB free, floor is %.1f GB' % (free_gb(), DISK_FLOOR_GB))
    args = [(k, nshard, mode, combos, outdir, years) for k in range(nshard)]
    t0 = time.time()
    if jobs == 1:
        res = [_shard_worker(a) for a in args]
    else:
        with mp.Pool(jobs) as pool:
            res = pool.map(_shard_worker, args)
    done = sum(r['n'] for r in res)
    print('  banked %d combinations (%d shards, %d skipped as already present) in %.1f min -> %s'
          % (done, nshard, sum(r['skipped'] for r in res), (time.time() - t0) / 60, outdir), flush=True)
    return outdir


def load_bank(mode, tag):
    outdir = os.path.join(ROOTOUT, 'r2gate1', 'mode%s_%s' % (mode, tag))
    yf = os.path.join(outdir, 'years.txt')
    if os.path.exists(yf):
        set_years(open(yf).read().strip())
    fs = sorted(__import__('glob').glob(os.path.join(outdir, 'shard_*.npz')))
    assert fs, 'no bank at %s' % outdir
    stats, combos, idx = [], [], []
    for f in fs:
        z = np.load(f, allow_pickle=True)
        stats.append(z['stat']); combos.append(z['combo']); idx.append(z['idx'])
    stat = np.concatenate(stats); cb = np.concatenate(combos); ix = np.concatenate(idx)
    o = np.argsort(ix)
    return stat[o].astype(np.float64), cb[o], outdir


# ---------------------------------------------------------------- the curve
MIN_TUNE_TRADES = 40     # DECLARED: 10 per year x 4 tune years, per stream, per window.
                         # Below it the combination is UNTESTED, which is not the
                         # same thing as failed, and it is reported as such.
NCUT = 120
NULL_DRAWS = 200         # the identity null at every 10th cut
DISK_FLOOR_GB = 1.0      # halt rather than fill the volume; the bank is resumable


def stage_curve(mode, tag, out=None):
    """GATE 1 CURVE.  The cut is tune-year expectancy in R, swept over its full
    observed range.  Reported at every cut, per stream, per window and pooled:
    combinations passing, families passing, lone-survivor families, the GRADE
    and TRADE year record of passers vs non-passers, and the rank correlation
    tune -> trade.  Nothing here selects; it is the curve Jack picks from."""
    from scipy.stats import spearmanr
    stat, cb, outdir = load_bank(mode, tag)
    wins = windows()
    rows, corr = [], []
    c1 = np.array([c[0] for c in cb]); c2 = np.array([c[1] for c in cb])
    fam = np.array([family_of(a, b) for a, b in zip(c1, c2)])
    famcode, _ = pd.factorize(fam)
    nfam_all = famcode.max() + 1
    for w in wins:
        tu = agg(role_slice(stat, *w['tune']))
        gr = agg(role_slice(stat, *w['grade']))
        tr = agg(role_slice(stat, *w['trade']))
        for si, sname in enumerate(STREAMS):
            elig = tu['n'][:, si] >= MIN_TUNE_TRADES
            e = tu['expectancy_R'][:, si]
            if elig.sum() < 2:
                continue
            lo, hi = np.nanmin(e[elig]), np.nanmax(e[elig])
            cuts = np.linspace(lo, hi, NCUT)
            ee = e[elig]; ff = famcode[elig]
            gte = gr['expectancy_R'][elig, si]; gtn = gr['n'][elig, si]
            tte = tr['expectancy_R'][elig, si]; ttn = tr['n'][elig, si]
            ok = np.isfinite(ee) & np.isfinite(tte) & (ttn > 0)
            rho, p = (spearmanr(ee[ok], tte[ok]) if ok.sum() > 3 else (np.nan, np.nan))
            corr.append(dict(mode=mode, window=w['name'], stream=sname,
                             n_eligible=int(elig.sum()), n_with_trade_trades=int(ok.sum()),
                             spearman_tune_to_trade=float(rho), p=float(p),
                             tune_min=float(lo), tune_max=float(hi)))
            for x in cuts:
                m = ee > x
                npass = int(m.sum())
                # bincount, not a per-family scan: the obvious
                #   sum(1 for f in fp if (ff[m]==f).sum()==1)
                # is O(families x passers) and at 1,521 families against 240,000
                # passers it is 365M operations PER CUT -- it ran fine on the
                # smoke and stalled the full bank.
                fc = np.bincount(ff[m], minlength=nfam_all) if npass else np.zeros(nfam_all, int)
                nfam_pass = int((fc > 0).sum()); lone = int((fc == 1).sum())
                def _rec(vals, ns, mask):
                    v = vals[mask]; n = ns[mask]
                    g = np.isfinite(v) & (n > 0)
                    return (float(np.average(v[g], weights=n[g])) if g.any() else np.nan,
                            int(n[g].sum()), int(g.sum()))
                ge_p, gn_p, gc_p = _rec(gte, gtn, m)
                ge_f, gn_f, gc_f = _rec(gte, gtn, ~m)
                te_p, tn_p, tc_p = _rec(tte, ttn, m)
                te_f, tn_f, tc_f = _rec(tte, ttn, ~m)
                rows.append(dict(mode=mode, window=w['name'], stream=sname, cut_tune_R=float(x),
                                 n_eligible=int(elig.sum()), n_pass=npass,
                                 pct_pass=100.0 * npass / max(elig.sum(), 1),
                                 n_families=nfam_pass, n_families_possible=int(nfam_all),
                                 n_lone_survivor_families=lone,
                                 grade_R_pass=ge_p, grade_trades_pass=gn_p, grade_n_pass=gc_p,
                                 grade_R_fail=ge_f, grade_trades_fail=gn_f, grade_n_fail=gc_f,
                                 trade_R_pass=te_p, trade_trades_pass=tn_p, trade_n_pass=tc_p,
                                 trade_R_fail=te_f, trade_trades_fail=tn_f, trade_n_fail=tc_f))
    # ---- POOLED OVER THE FIVE WINDOWS, and the IDENTITY NULL -------------
    # The pooled view sums each combination's tune years across all five
    # windows and its trade years across all five, so the curve is read on the
    # whole programme rather than on one window at a time.  Overlapping tune
    # windows mean a trade can be counted more than once on the tune side; the
    # trade side cannot, because the five trade years are disjoint.
    tu_p = np.zeros((stat.shape[0], 4, NSTAT)); tr_p = np.zeros_like(tu_p); gr_p = np.zeros_like(tu_p)
    for w in wins:
        tu_p += role_slice(stat, *w['tune']); gr_p += role_slice(stat, *w['grade']); tr_p += role_slice(stat, *w['trade'])
    TU, GR, TR = agg(tu_p), agg(gr_p), agg(tr_p)
    prows, nrows = [], []
    rng = np.random.default_rng(20261116)
    for si, sname in enumerate(STREAMS):
        elig = TU['n'][:, si] >= MIN_TUNE_TRADES * len(wins)
        if elig.sum() < 2:
            continue
        e = TU['expectancy_R'][elig, si]; ff = famcode[elig]
        trv = TR['expectancy_R'][elig, si]; trn = TR['n'][elig, si]
        grv = GR['expectancy_R'][elig, si]; grn = GR['n'][elig, si]
        good = np.isfinite(trv) & (trn > 0)
        cuts = np.linspace(np.nanmin(e), np.nanmax(e), NCUT)
        # ---- THE IDENTITY NULL, 200 draws, computed once for the whole curve.
        # A cut of size k selects k combinations. The null asks what a RANDOM k
        # from the same eligible pool would have scored on the trade years. One
        # shuffle of the pool answers it for EVERY k at once through a prefix
        # sum, so 200 draws cost 200 shuffles rather than 200 per cut.
        null_ks, null_at = [], {}
        gi = np.flatnonzero(good)
        if len(gi) > 10:
            vn = (trv[gi] * trn[gi]).astype(np.float64); nn = trn[gi].astype(np.float64)
            ks = sorted({int(min((e > x).sum(), len(gi))) for ci, x in enumerate(cuts) if ci % 10 == 0}
                        - {0})
            if ks:
                mat = np.empty((NULL_DRAWS, len(ks)))
                kk = np.array(ks) - 1
                for d_ in range(NULL_DRAWS):
                    o = rng.permutation(len(gi))
                    cv = np.cumsum(vn[o]); cn = np.cumsum(nn[o])
                    mat[d_] = cv[kk] / cn[kk]
                null_at = {k: mat[:, j] for j, k in enumerate(ks)}
            null_ks = ks
        for ci, x in enumerate(cuts):
            m = e > x
            npass = int(m.sum())
            fc = np.bincount(ff[m], minlength=famcode.max() + 1) if npass else np.zeros(1, int)
            nfam_pass = int((fc > 0).sum()); lone = int((fc == 1).sum())
            def wavg(v, n, msk):
                g = msk & np.isfinite(v) & (n > 0)
                return float(np.average(v[g], weights=n[g])) if g.any() else np.nan
            row = dict(mode=mode, stream=sname, cut_tune_R=float(x), n_eligible=int(elig.sum()),
                       n_pass=npass, pct_pass=100.0 * npass / max(elig.sum(), 1),
                       n_families=nfam_pass, n_lone_survivor_families=lone,
                       grade_R_pass=wavg(grv, grn, m), grade_R_fail=wavg(grv, grn, ~m),
                       trade_R_pass=wavg(trv, trn, m), trade_R_fail=wavg(trv, trn, ~m),
                       trade_trades_pass=int(trn[m & good].sum()))
            # THE IDENTITY NULL.  A cut is a selection, so it gets a null: draw
            # the SAME NUMBER of combinations uniformly at random from the same
            # eligible pool and read the same trade-year number.  If the cut's
            # passers sit inside this band the cut has selected nothing.
            k = min(npass, len(gi))
            if k in null_at:
                draws = null_at[k]
                row.update(null_draws=NULL_DRAWS, null_trade_R_mean=float(draws.mean()),
                           null_trade_R_p5=float(np.percentile(draws, 5)),
                           null_trade_R_p95=float(np.percentile(draws, 95)),
                           null_p_one_sided=float((draws >= row['trade_R_pass']).mean()))
            prows.append(row)
    P = pd.DataFrame(prows)
    pout = (out or os.path.join(ROOTOUT, 'r2gate1_curve_mode%s_%s.csv' % (mode, tag))).replace('_curve_', '_pooled_')
    P.to_csv(pout, index=False)
    print('  pooled curve + identity null: %d rows -> %s' % (len(P), os.path.basename(pout)), flush=True)
    for sname in STREAMS:
        g = P[(P.stream == sname) & P.null_trade_R_mean.notna()] if 'null_trade_R_mean' in P else P.iloc[:0]
        if len(g):
            r = g.iloc[len(g) // 2]
            print('    %-13s cut %+.3f -> %6d pass (%.2f%%), trade R %+.4f vs non-passers %+.4f; '
                  'identity null %+.4f [%+.4f, %+.4f], p=%.3f'
                  % (sname, r.cut_tune_R, r.n_pass, r.pct_pass, r.trade_R_pass, r.trade_R_fail,
                     r.null_trade_R_mean, r.null_trade_R_p5, r.null_trade_R_p95, r.null_p_one_sided), flush=True)

    D = pd.DataFrame(rows); C = pd.DataFrame(corr)
    out = out or os.path.join(ROOTOUT, 'r2gate1_curve_mode%s_%s.csv' % (mode, tag))
    D.to_csv(out, index=False)
    C.to_csv(out.replace('_curve_', '_rankcorr_'), index=False)
    print('  curve: %d rows -> %s' % (len(D), os.path.basename(out)), flush=True)
    print('  rank correlation tune -> trade, per window and stream:', flush=True)
    for _, r in C.iterrows():
        print('    %-9s %-12s n=%5d  rho=%+.4f (p=%.3g)  tune R range %+.4f .. %+.4f'
              % (r.window, r.stream, r.n_eligible, r.spearman_tune_to_trade, r.p, r.tune_min, r.tune_max), flush=True)
    return D, C


# ---------------------------------------------------------------- parity
def stage_parity(mode, n=8, out=None):
    """HAND CHECK ON THE `_r2` CODE PATH.  score_r2 runs the engine once per
    (pair, plan) and masks for routing; l2tune.Scorer runs it per call.  They
    must agree trade for trade.  Any mismatch halts."""
    import l2tune as T
    import l2refit as RF
    manifest_check()
    S.load_costs()
    wins = RF.parse_windows(WINDOWS_SPEC)
    S.WINDOWS = dict(S.WINDOWS); S.WINDOWS.update(RF.windows_table(wins))
    opts = S.mode_opts(S.slot_options(), mode)
    kwm = S.mode_kw(mode)
    PD, BUF = build_pairdata(opts)
    sc = T.Scorer()
    REG = T.registry()
    rows = []
    for cb in stratified(opts, n, seed=99)[:n]:
        a = score_r2(PD, cb, BUF, kwm)
        dip = {k: dict(REG[nm]) for k, nm in zip(('c1', 'c2', 'vol', 'base', 'exit_ind'), cb)}
        drisk = dict(atr_len=S.ATR_LEN, atr_mult=S.ATR_MULT, tp_mult=S.TP_MULT,
                     trail_mult=S.TRAIL_MULT, trail_arm=S.TRAIL_ARM, be_pct=S.BE_PCT)
        for sname, plan, code in S.SLICES:
            for routed in (True, False):
                si = {('trend', True): 0, ('trend', False): 1,
                      ('chop', True): 2, ('chop', False): 3}[(sname, routed)]
                for w in wins:
                    key = 'B' + w['name']
                    r = sc.score(cb, dip, drisk, mode, sname, code, plan, [key], routed=routed)[key]
                    mine = agg(role_slice(a, *w['build']))
                    nmine = float(mine['n'][si]); emine = float(mine['expectancy_R'][si])
                    nthem = 0.0 if r is None else float(r['n'])
                    ethem = np.nan if r is None else float(r['expectancy_R'])
                    bad = (abs(nmine - nthem) > 0.5) or (nthem > 0 and abs(emine - ethem) > 1e-9)
                    rows.append(dict(mode=mode, combo='|'.join(cb), slice=sname, routed=routed,
                                     window=w['name'], n_r2=nmine, n_scorer=nthem,
                                     R_r2=emine, R_scorer=ethem, mismatch=int(bad)))
    D = pd.DataFrame(rows)
    out = out or os.path.join(ROOTOUT, 'r2gate1_parity_mode%s.csv' % mode)
    D.to_csv(out, index=False)
    nb = int(D.mismatch.sum())
    print('  PARITY mode %s: %d comparisons, %d mismatches -> %s'
          % (mode, len(D), nb, os.path.basename(out)), flush=True)
    assert nb == 0, 'PARITY FAILED on the _r2 code path: %d mismatches' % nb
    return D


def opt(flag, cast=str, default=None):
    return cast(sys.argv[sys.argv.index(flag) + 1]) if flag in sys.argv else default


if __name__ == '__main__':
    stage = opt('--stage', str, 'probe')
    mode = opt('--mode', str, 'A')
    tag = opt('--tag', str, 'smoke10k')
    if '--years' in sys.argv:
        set_years(opt('--years', str))
    if stage == 'probe':
        r = stage_probe(mode, n=opt('--n', int, 200))
        pd.DataFrame([r]).to_csv(os.path.join(ROOTOUT, 'r2gate1_probe_mode%s.csv' % mode), index=False)
    elif stage == 'smoke':
        n = opt('--n', int, 10000)
        S.load_costs()
        opts = S.mode_opts(S.slot_options(), mode)
        total = S.n_combos(opts)
        if n >= total:
            # the full run: the deterministic enumeration order, so a shard is a
            # contiguous slice of it and a resumed run reproduces itself exactly
            combos = list(S.combo_iter(opts))
            print('  FULL enumeration: all %d mode %s combinations; per-slot coverage:'
                  % (len(combos), mode), flush=True)
        else:
            combos = stratified(opts, n)
            print('  stratified %d of %d mode %s combinations; per-slot coverage:'
                  % (len(combos), total, mode), flush=True)
        for k in S.SLOTS:
            if len(opts[k]) > 1:
                v = pd.Series([c[S.SLOTS.index(k)] for c in combos]).value_counts()
                print('    %-9s %2d options, %d..%d draws each' % (k, len(opts[k]), v.min(), v.max()), flush=True)
        stage_run(mode, combos, tag, jobs=opt('--jobs', int, None))
        stage_curve(mode, tag)
    elif stage == 'curve':
        stage_curve(mode, tag)
    elif stage == 'parity':
        stage_parity(mode, n=opt('--n', int, 8))
    else:
        raise SystemExit('unknown stage %s' % stage)
