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
import l2ckpt as L2CK

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
    """THE FIVE-MINUTE RULE (HANDOFF section 3). This worker used to hold its
    whole shard in memory and write once at the end -- on mode C that was 77
    minutes of unsaved compute per shard, and the stage after it then died
    reading the bank back. It now checkpoints on a clock and resumes by set
    difference on the combination index.
    """
    shard, nshard, mode, combos, outdir, years = args
    set_years(years)
    S.load_costs()
    opts = S.mode_opts(S.slot_options(), mode)
    kwm = S.mode_kw(mode)

    def _save(path, ids, rows):
        if free_gb() < DISK_FLOOR_GB:
            raise SystemExit('disk floor hit: %.1f GB free (floor %.1f); the bank is '
                             'resumable, rerun when there is room' % (free_gb(), DISK_FLOOR_GB))
        np.savez_compressed(path, stat=np.stack([r[0] for r in rows]).astype(np.float32),
                            year0=YEAR0, nyear=NYEAR,
                            combo=np.array([['%s' % x for x in r[1]] for r in rows], dtype=object),
                            idx=ids)

    ck = L2CK.Checkpointer(outdir, 'shard_%04d' % shard, save=_save)
    done = ck.completed()
    mine = [(i, combos[i]) for i in range(shard * len(combos) // nshard,
                                          (shard + 1) * len(combos) // nshard)]
    todo = [(i, cb) for i, cb in mine if i not in done]
    if not todo:
        return dict(shard=shard, n=0, skipped=True, seconds=0.0)
    if done:
        print('    shard %03d: resuming, %d of %d already on disk'
              % (shard, len(mine) - len(todo), len(mine)), flush=True)
    PD, BUF = build_pairdata(opts)
    t0 = time.time()
    for j, (i, cb) in enumerate(todo, 1):
        ck.add(i, (score_r2(PD, cb, BUF, kwm), cb))
        if j % 500 == 0:
            el = time.time() - t0
            print('    shard %03d: %6d/%6d  %.1f ms/combo  %.0f min left'
                  % (shard, j, len(todo), 1000 * el / j, (el / j) * (len(todo) - j) / 60), flush=True)
    ck.flush()
    return dict(shard=shard, n=len(todo), skipped=False, seconds=time.time() - t0)


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
    # The combination list is NOT written out: every shard already carries its
    # own `combo` and `idx` arrays, so the json was pure duplication -- and for
    # mode C it was 1.37 GB of it on a volume with 5 GB free. What is written is
    # the spec needed to reproduce the enumeration.
    with open(os.path.join(outdir, 'spec.json'), 'w') as fh:
        json.dump(dict(mode=mode, n=len(combos), years='%d-%d' % (YEAR0, YEAR0 + NYEAR - 1),
                       enumeration=('full deterministic l2sweep.combo_iter order'
                                    if len(combos) == S.n_combos(S.mode_opts(S.slot_options(), mode))
                                    else 'stratified, l2r2gate1.stratified seed 20261116'),
                       nshard=nshard, stamp=time.strftime('%F %T')), fh, indent=1)
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


def bank_dir(mode, tag):
    outdir = os.path.join(ROOTOUT, 'r2gate1', 'mode%s_%s' % (mode, tag))
    yf = os.path.join(outdir, 'years.txt')
    if os.path.exists(yf):
        set_years(open(yf).read().strip())
    fs = sorted(__import__('glob').glob(os.path.join(outdir, 'shard_*.npz')))
    assert fs, 'no bank at %s' % outdir
    return outdir, fs


def bank_index(mode, tag):
    """Total rows and the FAMILY of every combination, in bank order.

    Reads only the `combo` and `idx` arrays, never `stat`. Families are int16 --
    1,521 of them -- so the whole index is ~21 MB even for mode C's 10.7M rows.
    """
    outdir, fs = bank_dir(mode, tag)
    # Families WITHOUT building 10.7 million python strings: factorise the two
    # confirmation columns against a fixed menu and combine the codes, so the
    # family id is arithmetic on int16 and the whole index is ~21 MB.
    menu = S.slot_options()
    ix1 = {n: i for i, n in enumerate(menu['c1'])}
    ix2 = {n: i for i, n in enumerate(menu['c2'])}
    m2 = len(menu['c2'])
    codes, idx = [], []
    for f in fs:
        z = np.load(f, allow_pickle=True)
        cb = z['combo']
        a = np.array([ix1[x] for x in cb[:, 0]], np.int32)
        b = np.array([ix2[x] for x in cb[:, 1]], np.int32)
        codes.append((a * m2 + b).astype(np.int16))
        idx.append(z['idx'])
        del z, cb
    code = np.concatenate(codes); ix = np.concatenate(idx)
    out = np.empty(len(code), np.int16)
    out[ix] = code
    return outdir, fs, len(out), out


def reduce_bank(mode, tag, n_total, roles):
    """ONE STREAMING PASS over the shards for the given year roles.

    `roles` is {name: (y0, y1)} or {name: weights-by-year array}. Returns
    {name: (expectancy (n,4) f32, n_trades (n,4) f32)} and nothing else -- the
    raw bank is never held.

    WHY. load_bank concatenated every shard and cast to float64: for mode C
    that is 15.9 GB, doubled to 31.8 GB by the concatenate itself, on a 16 GB
    machine. It banked all 10,677,420 combinations in 77 minutes and then died
    reading them back. One pass per role-set, float32, is 0.95 GB.
    """
    outdir, fs = bank_dir(mode, tag)
    # expectancy in float64, trade counts in float32. The counts are exact
    # integers well inside float32; the expectancy is not, and rounding it to
    # float32 moved a combination across a cut boundary in the regression check
    # against the old loaded-bank path.
    out = {k: (np.full((n_total, 4), np.nan, np.float64), np.zeros((n_total, 4), np.float32))
           for k in roles}
    for f in fs:
        z = np.load(f, allow_pickle=True)
        st = z['stat']; ix = z['idx']
        for k, spec in roles.items():
            # ACCUMULATE IN float64. The bank is float32; summing years in
            # float32 and promoting afterwards shifted an expectancy by ~1e-7,
            # which moved one combination of 240,000 across a cut boundary in
            # the regression check. dtype= on the reduction costs nothing and
            # makes the streamed path bit-identical to the loaded one.
            if isinstance(spec, tuple):
                a, b = spec[0] - YEAR0, spec[1] - YEAR0 + 1
                blk = st[..., max(a, 0):min(b, NYEAR), :].sum(axis=-2, dtype=np.float64)
            else:
                w = np.asarray(spec, np.float64)
                blk = np.zeros(st.shape[:2] + st.shape[3:], np.float64)
                for j in range(NYEAR):
                    if w[j]:
                        blk += w[j] * st[:, :, j, :]
            n = blk[..., 0]
            with np.errstate(divide='ignore', invalid='ignore'):
                e = np.where(n > 0, blk[..., 1] / np.maximum(n, 1), np.nan)
            out[k][0][ix] = e.astype(np.float64)
            out[k][1][ix] = n.astype(np.float32)
        del z, st
    return outdir, out


def tune_weights(wins):
    """The POOLED tune years as a weight per banked year.

    The five tune windows overlap, so a year belongs to more than one of them
    and the pooled tune score weights it by how many -- 2011 once, 2014 and
    2015 four times each, 2018 once. Written as weights rather than as five
    separate slices so the pooled view costs one pass instead of five.
    """
    w = np.zeros(NYEAR, np.float32)
    for win in wins:
        for y in range(win['tune'][0], win['tune'][1] + 1):
            if YEAR0 <= y < YEAR0 + NYEAR:
                w[y - YEAR0] += 1.0
    return w


# ---------------------------------------------------------------- the curve
MIN_TUNE_TRADES = 40     # DECLARED: 10 per year x 4 tune years, per stream, per window.
                         # Below it the combination is UNTESTED, which is not the
                         # same thing as failed, and it is reported as such.
NCUT = 120
NULL_DRAWS = 200         # the identity null at every 10th cut
DISK_FLOOR_GB = 1.0      # halt rather than fill the volume; the bank is resumable


def _rec(v, n, mask):
    """Trade-weighted mean of `v` over `mask`, plus the trade and combination
    counts behind it. NaN when nothing qualifies -- never a silent zero."""
    g = mask & np.isfinite(v) & (n > 0)
    if not g.any():
        return np.nan, 0, 0
    # float64 on the aggregation: the per-combination trade counts are exact in
    # float32, their SUM is not -- 17 million trades is past a float32 mantissa
    # and the totals came out 20-66 short of the float64 path.
    w = n[g].astype(np.float64)
    return float(np.average(v[g], weights=w)), int(w.sum()), int(g.sum())


def _one_curve(e, trv, trn, grv, grn, fam, nfam_all, elig, min_trades, label):
    """The curve for one (window-or-pooled, stream): cut swept over its full
    observed range, with the identity null. Nothing here selects."""
    from scipy.stats import spearmanr
    if elig.sum() < 2:
        return [], None
    ee = e[elig]; ff = fam[elig].astype(np.int64)
    gte = grv[elig]; gtn = grn[elig]
    tte = trv[elig]; ttn = trn[elig]
    good = np.isfinite(tte) & (ttn > 0)
    lo, hi = float(np.nanmin(ee)), float(np.nanmax(ee))
    cuts = np.linspace(lo, hi, NCUT)
    rho, pv = (spearmanr(ee[good], tte[good]) if good.sum() > 3 else (np.nan, np.nan))
    # ---- THE IDENTITY NULL, 200 draws, one shuffle answering every k.
    # A cut of size k selects k combinations; the null asks what a RANDOM k from
    # the same eligible pool scored on the trade years. One permutation plus a
    # prefix sum gives every k at once, so the cost is 200 shuffles for the
    # whole curve instead of 200 per cut.
    null_at = {}
    gi = np.flatnonzero(good)
    if len(gi) > 10:
        rng = np.random.default_rng(20261116)
        vn = (tte[gi] * ttn[gi]).astype(np.float64); nn = ttn[gi].astype(np.float64)
        ks = sorted({int(min((ee > x).sum(), len(gi))) for ci, x in enumerate(cuts)
                     if ci % 10 == 0} - {0})
        if ks:
            kk = np.array(ks) - 1
            mat = np.empty((NULL_DRAWS, len(ks)))
            for d_ in range(NULL_DRAWS):
                o = rng.permutation(len(gi))
                mat[d_] = np.cumsum(vn[o])[kk] / np.cumsum(nn[o])[kk]
            null_at = {k: mat[:, j] for j, k in enumerate(ks)}
    rows = []
    for x in cuts:
        m = ee > x
        npass = int(m.sum())
        fc = np.bincount(ff[m], minlength=nfam_all) if npass else np.zeros(nfam_all, np.int64)
        ge_p, gn_p, gc_p = _rec(gte, gtn, m)
        ge_f, gn_f, gc_f = _rec(gte, gtn, ~m)
        te_p, tn_p, tc_p = _rec(tte, ttn, m)
        te_f, tn_f, tc_f = _rec(tte, ttn, ~m)
        row = dict(cut_tune_R=float(x), n_eligible=int(elig.sum()), n_pass=npass,
                   pct_pass=100.0 * npass / max(int(elig.sum()), 1),
                   n_families=int((fc > 0).sum()), n_families_possible=int(nfam_all),
                   n_lone_survivor_families=int((fc == 1).sum()),
                   grade_R_pass=ge_p, grade_trades_pass=gn_p, grade_n_pass=gc_p,
                   grade_R_fail=ge_f, grade_trades_fail=gn_f, grade_n_fail=gc_f,
                   trade_R_pass=te_p, trade_trades_pass=tn_p, trade_n_pass=tc_p,
                   trade_R_fail=te_f, trade_trades_fail=tn_f, trade_n_fail=tc_f)
        k = min(npass, len(gi))
        if k in null_at:
            d = null_at[k]
            row.update(null_draws=NULL_DRAWS, null_trade_R_mean=float(d.mean()),
                       null_trade_R_p5=float(np.percentile(d, 5)),
                       null_trade_R_p95=float(np.percentile(d, 95)),
                       null_p_one_sided=float((d >= (te_p if np.isfinite(te_p) else -np.inf)).mean()))
        rows.append(row)
    corr = dict(n_eligible=int(elig.sum()), n_with_trade_trades=int(good.sum()),
                spearman_tune_to_trade=float(rho), p=float(pv),
                tune_min=lo, tune_max=hi)
    return rows, corr


def stage_curve(mode, tag, out=None):
    """GATE 1 CURVE. The cut is tune-year expectancy in R, swept over its full
    observed range. Reported at every cut, per stream, per window and pooled:
    combinations passing, families passing, lone-survivor families, the GRADE
    and TRADE year record of passers vs non-passers, the identity null, and the
    rank correlation tune -> trade. Nothing here selects; it is the curve Jack
    picks from.

    STREAMED. One pass over the shards per role-set, float32, so mode C's
    10,677,420 combinations cost under 1 GB of RAM instead of the 31.8 GB the
    concatenate-everything version needed.
    """
    wins = windows()
    outdir, fs, ntot, fam = bank_index(mode, tag)
    _m = S.slot_options()
    nfam_all = len(_m['c1']) * len(_m['c2'])      # the DECLARED 39 x 39 = 1,521
    print('  bank %s: %d combinations in %d shards, %d families'
          % (os.path.basename(outdir), ntot, len(fs), nfam_all), flush=True)

    # ---- per window -------------------------------------------------------
    rows, corr = [], []
    for w in wins:
        _, R = reduce_bank(mode, tag, ntot, {'tune': w['tune'], 'grade': w['grade'],
                                             'trade': w['trade']})
        for si, sname in enumerate(STREAMS):
            e, en = R['tune'][0][:, si], R['tune'][1][:, si]
            elig = en >= MIN_TUNE_TRADES
            rr, cc = _one_curve(e, R['trade'][0][:, si], R['trade'][1][:, si],
                                R['grade'][0][:, si], R['grade'][1][:, si],
                                fam, nfam_all, elig, MIN_TUNE_TRADES,
                                '%s %s' % (w['name'], sname))
            for r in rr:
                r.update(mode=mode, window=w['name'], stream=sname)
            rows += rr
            if cc:
                cc.update(mode=mode, window=w['name'], stream=sname)
                corr.append(cc)
        del R
    D = pd.DataFrame(rows); C = pd.DataFrame(corr)
    out = out or os.path.join(ROOTOUT, 'r2gate1_curve_mode%s_%s.csv' % (mode, tag))
    D.to_csv(out, index=False)
    C.to_csv(out.replace('_curve_', '_rankcorr_'), index=False)
    print('  curve: %d rows -> %s' % (len(D), os.path.basename(out)), flush=True)
    print('  rank correlation tune -> trade, per window and stream:', flush=True)
    for _, r in C.iterrows():
        print('    %-9s %-12s n=%7d  rho=%+.4f (p=%.3g)  tune R range %+.4f .. %+.4f'
              % (r.window, r.stream, r.n_eligible, r.spearman_tune_to_trade, r.p,
                 r.tune_min, r.tune_max), flush=True)

    # ---- pooled over the five windows -------------------------------------
    # The pooled tune score weights each year by how many tune windows contain
    # it; the five trade years are disjoint so the trade side is a plain sum.
    _, P_ = reduce_bank(mode, tag, ntot, {'tune': tune_weights(wins),
                                          'grade': (wins[0]['grade'][0], wins[-1]['grade'][1]),
                                          'trade': (wins[0]['trade'][0], wins[-1]['trade'][1])})
    prows = []
    for si, sname in enumerate(STREAMS):
        elig = P_['tune'][1][:, si] >= MIN_TUNE_TRADES * len(wins)
        rr, _c = _one_curve(P_['tune'][0][:, si], P_['trade'][0][:, si], P_['trade'][1][:, si],
                            P_['grade'][0][:, si], P_['grade'][1][:, si],
                            fam, nfam_all, elig, MIN_TUNE_TRADES * len(wins), sname)
        for r in rr:
            r.update(mode=mode, stream=sname)
        prows += rr
    P = pd.DataFrame(prows)
    pout = out.replace('_curve_', '_pooled_')
    P.to_csv(pout, index=False)
    print('  pooled curve + identity null: %d rows -> %s' % (len(P), os.path.basename(pout)), flush=True)
    if 'null_trade_R_mean' in P:
        for sname in STREAMS:
            g = P[(P.stream == sname) & P.null_trade_R_mean.notna()]
            if len(g):
                r = g.iloc[len(g) // 2]
                print('    %-13s cut %+.3f -> %7d pass (%.2f%%), trade R %+.4f vs non-passers %+.4f; '
                      'identity null %+.4f [%+.4f, %+.4f], p=%.3f'
                      % (sname, r.cut_tune_R, r.n_pass, r.pct_pass, r.trade_R_pass,
                         r.trade_R_fail, r.null_trade_R_mean, r.null_trade_R_p5,
                         r.null_trade_R_p95, r.null_p_one_sided), flush=True)
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
