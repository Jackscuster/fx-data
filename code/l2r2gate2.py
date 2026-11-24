import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""GATE 2 ON THE `_r2` PATH — ONE PASS, BANKED BY CALENDAR YEAR (HANDOFF 0l).

NO CUT AT GATE 1 (Jack, 16 Nov). Every combination the enumeration produced
is tuned here: mode A 273,780, mode B 273,780, mode C 10,677,420.

THE ONE-PASS RULE. Every configuration is scored ONCE over 2011-2020 and its
record is banked per calendar year. Each of the five walk steps then reads its
tune pick (argmax over its own four tune years), its grade-year record and its
trade-year record out of that one pass. The engine is never re-run per step.

CONDITION 1 — NO YEAR'S RECORD CONTAINS ANOTHER YEAR'S PRICE. Trades are
marked to market DAILY and each daily increment is attributed to the calendar
year of its own bar, in the exact convention l2walkfwd.engine_one uses and
audit item 18 guards. A trade open across a boundary contributes its truncated
mark-to-market R to each year and counts once in each year it was open. Checked
in code: a trade's per-year marks sum to its full R, or the stage halts.

THE CONFIGURATION SET IS AXIAL — the default point plus every single-knob
deviation over each declared grid, every knob measured from the same default.
It is window-independent, which is what lets one pass serve five steps. The
joint product of the trend risk grid alone is 810,872,580 per strategy, and
l2tune's coordinate descent is window-dependent at every step, so neither can
satisfy the one-pass condition. See HANDOFF 0l for the arithmetic and for the
cost of what was excluded.

THE OBJECTIVE, identical across all three modes: ACCOUNT-NORMALISED R
(l2tune.ACCT_OBJECTIVE True, as l2refit sets it) -- every trade restated
against a fixed 1.0xATR risk unit with the cost restated with it (fault #27).
Trade-weighted expectancy over the step's four tune years, profit factor as
tiebreak, MIN_TRADES_PICK enforced. Picks are made SEPARATELY for the routed
and always-on streams.

PRECISION: float64 for every sum, int64 for every count, arithmetic indices
rather than strings. Those were the three traps of 16 Nov.

    python3 code/l2r2gate2.py --stage grid   --mode A
    python3 code/l2r2gate2.py --stage smoke  --mode A --n 2000
    python3 code/l2r2gate2.py --stage cond1  --mode A --n 40
    python3 code/l2r2gate2.py --stage cond2  --mode A --n 2000
    python3 code/l2r2gate2.py --stage run    --mode A --n 273780
"""
import time, json, glob
import numpy as np, pandas as pd
from numba import njit

import l2lib as L
import l2engine as E
import l2sweep as S
import l2tune as T
import l2r2gate1 as G

# THE WALK, SWITCHED BY ENVIRONMENT (Jack, 24 Nov). FX_WALK=ext11 extends the
# walk back to 2005: eleven rolling steps from tune 2005-2008 / grade 2009 /
# trade 2010 through tune 2015-2018 / grade 2019 / trade 2020, so 2010-2020 are
# all traded blind and 2021 onward stays sealed. Default is the five-step walk
# the shipped banks were built on, byte-identical.
#
# AN ENVIRONMENT VARIABLE, NOT AN ARGUMENT, for the reason FX_G2_OBJECTIVE is:
# macOS multiprocessing SPAWNS, so a worker re-imports this module and takes
# its module globals fresh. A walk threaded as a parameter would be right in
# the parent and the default in every child.
WALK = os.environ.get('FX_WALK', 'base5').strip().lower()
assert WALK in ('base5', 'ext11'), 'FX_WALK must be base5 or ext11, got %r' % WALK
if WALK == 'ext11':
    YEAR0, NYEAR = 2005, 16        # 2005..2020; 2021+ sealed
    _STEP_FIRST, _STEP_LAST = 2005, 2015
else:
    YEAR0, NYEAR = 2011, 10        # the years the five windows use
    _STEP_FIRST, _STEP_LAST = 2011, 2015
NSTAT = 5                          # n, sum_r, gain, loss, n_win
STREAMS = ('trend-routed', 'trend-allon', 'chop-routed', 'chop-allon')
NSTEP = len(range(_STEP_FIRST, _STEP_LAST + 1))
MIN_TUNE_TRADES = S.MIN_TRADES_PICK   # 100, l2tune's own rule

# ==========================================================================
# THE OBJECTIVE, AND THE WIDENED GRID (Jack, 20-21 Nov)
# ==========================================================================
# DRIVEN BY AN ENVIRONMENT VARIABLE, NOT AN ARGUMENT, and that is deliberate:
# macOS multiprocessing SPAWNS, so a pool worker re-imports this module and
# gets its MODULE GLOBALS fresh. An objective threaded as a function argument
# would be correct in the parent and default in every child -- which is fault
# "A POOL WORKER MUST PROVE IT LOADED THE PARENT'S FIELD" from 11 Sep, in a
# new place. An env var is inherited by the fork/spawn, so parent and children
# cannot disagree.
#
#   FX_G2_OBJECTIVE=expectancy   trade-weighted expectancy, PF tiebreak.
#                                The shipped objective; both banks on disk
#                                were tuned with it and it is the default.
#   FX_G2_OBJECTIVE=r2dd         total R / max DD R on the step's four tune
#                                years, MIN_TUNE_TRADES enforced, tiebreak on
#                                total R. Sortino and expectancy are recorded
#                                in the winner's per-year block exactly as
#                                before and are NEVER read while picking.
#
# THE WIDENED GRID RIDES WITH r2dd, because the point of the wider stop and
# target range is to let a drawdown objective find a shape the expectancy
# objective had no reason to look for. Widening it for the expectancy tune
# would invalidate both banks on disk for no gain.
OBJECTIVE = os.environ.get('FX_G2_OBJECTIVE', 'expectancy').strip().lower()
assert OBJECTIVE in ('expectancy', 'r2dd'), \
    'FX_G2_OBJECTIVE must be expectancy or r2dd, got %r' % OBJECTIVE

# Jack, 20 Nov: "widen the stop grid to 0.5-3.0 ATR and the target grid to
# 0.5-5.0 ATR at the same step sizes; keep every other grid." The stop grid
# has TWO step sizes -- 0.05 coarse plus a 0.01 fine band at 1.26-1.50 -- so
# "the same step sizes" keeps the fine band where it is and extends the coarse
# one over the new range. Recorded in HANDOFF 0l-NOW.
WIDE_STOP = (0.50, 3.00, 0.05)
WIDE_TP = (0.50, 5.00, 0.05)


def widen_grids():
    """Point l2tune's risk knobs at the wider stop and target ranges."""
    stop = sorted(set([round(v, 4) for v in T._rng(*WIDE_STOP)]
                      + [round(v, 4) for v in T._rng(1.26, 1.50, 0.01)]))
    tp = sorted(set(round(v, 4) for v in T._rng(*WIDE_TP)))
    T.GRID_STOP = stop
    T.GRID_TP = tp
    T.RISK_KNOBS_TREND = (('atr_len', T.GRID_ATR), ('atr_mult', stop),
                          ('tp_mult', tp), ('be_pct', T.GRID_BE),
                          ('trail_arm', T.GRID_ARM), ('trail_mult', T.GRID_TRAIL))
    T.RISK_KNOBS_CHOP = (('atr_len', T.GRID_ATR), ('atr_mult', stop),
                         ('tp_mult', tp))
    return stop, tp


if OBJECTIVE == 'r2dd':
    _ws, _wtp = widen_grids()
    print('  OBJECTIVE r2dd: total R / max DD R, min %d tune trades; stop grid %d values '
          '%.2f-%.2f, target grid %d values %.2f-%.2f'
          % (MIN_TUNE_TRADES, len(_ws), min(_ws), max(_ws), len(_wtp), min(_wtp),
             max(_wtp)), flush=True)


def bank_tag(tag):
    """The r2dd bank never shares a name with the expectancy bank."""
    if OBJECTIVE == 'r2dd' and not str(tag).endswith('_r2dd'):
        return '%s_r2dd' % tag
    return tag
# The shared disk series cache's budget FOR THIS STAGE. l2cache's own default is
# 10 GB, which is more than this volume can spare beside a 1.4 GB bank; mode A's
# axial set needs ~1.2 GB so 4 GB does not bind, and mode C can be raised when
# the disk allows it.
CACHE_BUDGET_GB = 4.0


def steps():
    """0f, unchanged in shape: tune years 1-4, grade year 5, trade year 6,
    rolling. The RANGE depends on FX_WALK -- five steps from 2011 by default,
    eleven from 2005 under ext11."""
    return [dict(name='%d-%d' % (a, a + 3), tune=(a, a + 3), grade=(a + 4, a + 4),
                 trade=(a + 5, a + 5))
            for a in range(_STEP_FIRST, _STEP_LAST + 1)]


# ==========================================================================
# THE AXIAL CONFIGURATION SET
# ==========================================================================
def axial(mode, combo, sname):
    """(tag, ip, risk) for every configuration, DEFAULT FIRST.

    `tag` is a short arithmetic-free label kept only for the record; the bank
    indexes configurations by POSITION in this list, which is deterministic
    given (mode, combo, sname), so a winner can always be resolved back.
    """
    reg = T.registry()
    slots = ('c1', 'c2', 'vol', 'base', 'exit_ind')
    dip = {k: dict(reg[n]) for k, n in zip(slots, combo)}
    drisk = dict(atr_len=S.ATR_LEN, atr_mult=S.ATR_MULT, tp_mult=S.TP_MULT,
                 trail_mult=S.TRAIL_MULT, trail_arm=S.TRAIL_ARM, be_pct=S.BE_PCT)
    out = [('default', dip, drisk)]
    knobs = T.RISK_KNOBS_TREND if sname == 'trend' else T.RISK_KNOBS_CHOP
    for kname, grid in knobs:
        for v in grid:
            if v == drisk[kname]:
                continue
            r2 = dict(drisk); r2[kname] = v
            out.append(('risk:%s=%s' % (kname, v), dip, r2))
    use = [s for s in T.SLOT_ORDER if s != 'exit_ind' or S.MODES[mode]['uses_exit_slot']]
    names = dict(zip(slots, combo))
    for slot in use:
        name = names[slot]
        for pname in T.tuned_params(name, cap=T.CAP_N):
            pdef = reg[name][pname]
            for v in T.ind_param_grid(pdef):
                if v == pdef:
                    continue
                ip2 = {k: dict(x) for k, x in dip.items()}
                ip2[slot][pname] = v
                out.append(('ind:%s.%s=%s' % (slot, pname, v), ip2, drisk))
    return out


# ==========================================================================
# CONDITION 1 — daily marks attributed to the bar's own calendar year
# ==========================================================================
@njit(cache=False)
def _year_marks(nt, eb, xb, dirv, epx, units, rtot, cst, am, risk,
                cl, ybar, reg, code, acc, s_routed, s_allon, tmp, touch):
    """Per-year record for one (pair, plan, configuration), both streams.

    acc is (2, NYEAR, NSTAT). `tmp` and `touch` are caller-owned scratch of
    length NYEAR so nothing is allocated inside the loop.

    The convention is l2walkfwd.engine_one's, which audit item 18 guards:
        cum(b) = R x am                       on the exit bar
        cum(b) = dir x (close[b] - entry) x units / RISK x am   otherwise
        increment(b) = cum(b) - cum(b-1), less the entry cost on the entry bar
    Summing a trade's increments reproduces its R exactly, so splitting them by
    the bar's own year cannot move price across a year boundary.
    """
    ny = acc.shape[1]
    worst = 0.0
    for j in range(nt):
        e = eb[j]
        x = xb[j]
        if x < 0 or x < e:
            continue
        rt = reg[e] == code
        for y in range(ny):
            tmp[y] = 0.0
            touch[y] = 0
        prev = 0.0
        tot_in = 0.0
        for b in range(e, x + 1):
            if b == x:
                cum = rtot[j] * am
            else:
                cum = dirv[j] * (cl[b] - epx[j]) * units[j] / risk * am
            inc = cum - prev
            if b == e:
                inc -= cst[j]
            prev = cum
            y = ybar[b]
            if y >= 0:
                tmp[y] += inc
                touch[y] = 1
                # the residual is measured on the BANKED bars only. A trade with
                # bars before 2011 or past 2020 legitimately loses those
                # increments -- truncating at the bank's edge is the SAME
                # operation condition 1 asks for at every other year boundary.
                # Comparing against the untruncated R made the check fail by the
                # size of the 2005-2010 tail, which is not an error.
                tot_in += inc
        got = 0.0
        for y in range(ny):
            got += tmp[y]
        d = got - tot_in
        if d < 0.0:
            d = -d
        if d > worst:
            worst = d
        for k in range(2):
            if k == 0:
                if not rt:
                    continue
                s = s_routed
            else:
                s = s_allon
            for y in range(ny):
                if touch[y] == 0:
                    continue
                v = tmp[y]
                acc[s, y, 0] += 1.0
                acc[s, y, 1] += v
                if v > 0.0:
                    acc[s, y, 2] += v
                    acc[s, y, 4] += 1.0
                else:
                    acc[s, y, 3] -= v
    return worst


@njit(cache=False)
def _year_marks_dd(nt, eb, xb, dirv, epx, units, rtot, cst, am, risk,
                   cl, ybar, dayi, reg, code, acc, accd, s_routed, s_allon,
                   tmp, touch):
    """_year_marks, plus a PER-DAY increment vector so drawdown is reachable.

    WHY A SECOND FUNCTION RATHER THAN A FLAG. _year_marks is the hot path of a
    13-hour stage that has already produced both shipped banks. It is left
    byte-identical so the expectancy-tuned banks stay reproducible, and the
    r2dd objective gets its own copy. The two are checked against each other
    by condition 1b below: on the same strategy they must return identical
    `acc` to 1e-12, or the copy has drifted.

    accd is (2, ndays) in GLOBAL day order, netted across pairs. That is what
    makes the drawdown a real one: increments from all 28 pairs land on the
    same calendar day before any cumulative sum is taken, so the curve is the
    strategy's own equity curve and not a per-pair artefact. `dayi` maps a
    pair's bar to its global day, -1 outside the banked window.
    """
    ny = acc.shape[1]
    worst = 0.0
    for j in range(nt):
        e = eb[j]
        x = xb[j]
        if x < 0 or x < e:
            continue
        rt = reg[e] == code
        for y in range(ny):
            tmp[y] = 0.0
            touch[y] = 0
        prev = 0.0
        tot_in = 0.0
        for b in range(e, x + 1):
            if b == x:
                cum = rtot[j] * am
            else:
                cum = dirv[j] * (cl[b] - epx[j]) * units[j] / risk * am
            inc = cum - prev
            if b == e:
                inc -= cst[j]
            prev = cum
            y = ybar[b]
            if y >= 0:
                tmp[y] += inc
                touch[y] = 1
                tot_in += inc
                di = dayi[b]
                if di >= 0:
                    if rt:
                        accd[s_routed, di] += inc
                    accd[s_allon, di] += inc
        got = 0.0
        for y in range(ny):
            got += tmp[y]
        d = got - tot_in
        if d < 0.0:
            d = -d
        if d > worst:
            worst = d
        for k in range(2):
            if k == 0:
                if not rt:
                    continue
                s = s_routed
            else:
                s = s_allon
            for y in range(ny):
                if touch[y] == 0:
                    continue
                v = tmp[y]
                acc[s, y, 0] += 1.0
                acc[s, y, 1] += v
                if v > 0.0:
                    acc[s, y, 2] += v
                    acc[s, y, 4] += 1.0
                else:
                    acc[s, y, 3] -= v
    return worst


class Years:
    """The Scorer's tables plus a per-year, condition-1 scoring pass.

    Built on l2tune.Scorer so the indicator cache, the cost table and the
    engine call are the shipped ones; what is new is the per-year attribution.
    """

    def __init__(self, cap=900):
        T.ACCT_OBJECTIVE = True      # the 0f objective; see HANDOFF 0l
        # DISK-BACKED SERIES CACHE. A disk hit is ~0.1 ms against an ~11.6 ms
        # recompute, and the axial set needs ~2,184 distinct variant series x 28
        # pairs at ~20 kB -- about 1.2 GB, paid ONCE and then shared by every
        # worker and every restart. Without it each cold worker recomputed the
        # lot, which is why one strategy took 481 s.
        self.sc = T.Scorer(cache=T.SeriesCache(cap=cap, disk=True))
        self.pairs = self.sc.pairs
        self.yb, self.cl = {}, {}
        for p in self.pairs:
            yr = pd.DatetimeIndex(self.sc.dates[p]).year.values.astype(np.int64)
            y = yr - YEAR0
            y[(y < 0) | (y >= NYEAR)] = -1
            self.yb[p] = y
            self.cl[p] = self.sc.arr[p][3]
        self.cmult = {p: G.crisis_mult_bars(p, pd.DatetimeIndex(self.sc.dates[p]))
                      for p in self.pairs}
        self.cfrac = {p: (S.COSTS or {}).get(p, 0.0) for p in self.pairs}
        self.tmp = np.zeros(NYEAR, np.float64)
        self.touch = np.zeros(NYEAR, np.int64)
        self.worst_cond1 = 0.0
        self.n_eval = 0
        # THE GLOBAL DAY INDEX, for the r2dd objective only. Bars are per-pair
        # positions, so accumulating increments by bar would add Monday on one
        # pair to Tuesday on another. The union of every pair's trading days
        # inside the banked window is the common axis; dayi maps a pair's bar
        # onto it and -1 outside.
        alld = set()
        for p in self.pairs:
            d = pd.DatetimeIndex(self.sc.dates[p])
            alld.update(d[(d.year >= YEAR0) & (d.year < YEAR0 + NYEAR)].values.tolist())
        self.days = np.array(sorted(alld))
        self.ndays = len(self.days)
        pos = {v: k for k, v in enumerate(self.days.tolist())}
        self.dayi = {}
        for p in self.pairs:
            d = pd.DatetimeIndex(self.sc.dates[p]).values
            self.dayi[p] = np.array([pos.get(v, -1) for v in d.tolist()], np.int64)
        dy = pd.DatetimeIndex(self.days).year.values.astype(np.int64) - YEAR0
        self.dayyear = dy
        # A TUNE WINDOW IS A CONTIGUOUS SLICE, because the day axis is sorted
        # and the window is a run of whole calendar years. Precomputed once so
        # the inner loop never builds a mask.
        self.winslice = {}
        for _s in steps():
            _y0, _y1 = _s['tune']
            _m = np.flatnonzero((dy >= _y0 - YEAR0) & (dy <= _y1 - YEAR0))
            self.winslice[(_y0, _y1)] = ((int(_m[0]), int(_m[-1]) + 1) if len(_m)
                                         else (0, 0))

    def score(self, combo, ip, risk, mode, sname, code, plan, want_dd=False):
        """-> (2, NYEAR, NSTAT) float64: routed, always-on.

        With want_dd the return is (acc, accd) and accd is (2, ndays) of
        per-day increments netted across pairs -- what the r2dd objective
        needs and the expectancy objective does not pay for.
        """
        self.n_eval += 1
        sc = self.sc
        c1, c2, vol, base, ex = combo
        kwm = S.mode_kw(mode)
        acc = np.zeros((2, NYEAR, NSTAT), np.float64)
        accd = np.zeros((2, self.ndays), np.float64) if want_dd else None
        alen = int(risk['atr_len'])
        am = float(risk['atr_mult'])
        t1 = L.KIND[c1] == 'TERNARY'
        t2 = L.KIND[c2] == 'TERNARY'
        for p in self.pairs:
            o, h, l, c = sc.arr[p]
            ak = (alen, p)
            atr = sc._atr.get(ak)
            if atr is None:
                atr = L.P.atr(h, l, c, alen)
                sc._atr[ak] = atr
            g = sc.cache.get
            lt, st, lc, scr = g(c1, ip['c1'], p, sc.arr[p])[:4]
            _, _, c2lc, c2sc = g(c2, ip['c2'], p, sc.arr[p])[:4]
            vl, vs = g(vol, ip['vol'], p, sc.arr[p])[:2]
            bl = g(base, ip['base'], p, sc.arr[p])
            bl = bl[0] if isinstance(bl, tuple) else bl
            el, es = g(ex, ip['exit_ind'], p, sc.arr[p])[:2]
            b = sc.buf[p]
            nt, _, _, _ = E.run_bars(
                o, h, l, c, atr, bl, lt, st, lc, scr, c2lc, c2sc, vl, vs,
                el, es, sc._nosus[p], t1, t2, True, True, True,
                kwm['exit_on_c1_flip'], kwm['exit_on_base_cross'],
                kwm['exit_on_exit_ind'], False, int(plan), S.RISK,
                am, float(risk['tp_mult']), float(risk['trail_mult']),
                float(risk['trail_arm']), float(risk['be_pct']), 1.5, 7, True, True,
                b['entry_bar'], b['exit_bar'], b['dir'], b['leg'],
                b['entry_px'], b['exit_px'], b['units'], b['r'],
                b['reason'], b['route'],
                *E._amb_off(len(c)))
            if nt == 0:
                continue
            eb = b['entry_bar'][:nt]
            # COST IN THE SAME UNIT AS R (fault #27): account-normalised R is
            # the move in 1.0xATR units, so the cost is restated with it.
            cst = (self.cfrac[p] * self.cmult[p][eb] * np.abs(b['entry_px'][:nt])
                   * np.abs(b['units'][:nt]) / S.RISK) * am
            if want_dd:
                w = _year_marks_dd(nt, eb, b['exit_bar'][:nt],
                                   b['dir'][:nt].astype(np.float64),
                                   b['entry_px'][:nt], b['units'][:nt], b['r'][:nt],
                                   cst, am, S.RISK, self.cl[p], self.yb[p],
                                   self.dayi[p], sc.reg[p], code,
                                   acc, accd, 0, 1, self.tmp, self.touch)
            else:
                w = _year_marks(nt, eb, b['exit_bar'][:nt], b['dir'][:nt].astype(np.float64),
                                b['entry_px'][:nt], b['units'][:nt], b['r'][:nt], cst,
                                am, S.RISK, self.cl[p], self.yb[p], sc.reg[p], code,
                                acc, 0, 1, self.tmp, self.touch)
            if w > self.worst_cond1:
                self.worst_cond1 = w
        return (acc, accd) if want_dd else acc


# ==========================================================================
# reading a step out of the bank
# ==========================================================================
def role_sum(acc, y0, y1):
    """Sum the per-year record over calendar years [y0, y1]. float64."""
    a, b = y0 - YEAR0, y1 - YEAR0 + 1
    return acc[..., max(a, 0):min(b, NYEAR), :].sum(axis=-2, dtype=np.float64)


@njit(cache=False)
def _dd_slice(x, lo, hi):
    """Max drawdown of cumsum(x[lo:hi]), no allocation."""
    # PEAK STARTS AT THE FIRST POINT, NOT AT ZERO. np.maximum.accumulate --
    # which l2tune and l2walkfwd both use -- makes eq[0] the first peak, so a
    # curve that opens by falling has no drawdown until it recovers above its
    # own first point. Starting the peak at 0.0 instead counted that opening
    # fall and disagreed with the reference by 9.38 R on the first check.
    peak = -1.7976931348623157e308
    eq = 0.0
    dd = 0.0
    for i in range(lo, hi):
        eq += x[i]
        if eq > peak:
            peak = eq
        d = peak - eq
        if d > dd:
            dd = d
    return dd


def role_dd_fast(accd, lo, hi):
    """role_dd over a PRECOMPUTED contiguous slice, for the inner loop.

    WHY THIS EXISTS. role_dd below builds a boolean mask over ~2,600 days and
    takes a cumsum, and the tuner calls it once per (configuration, step,
    stream) -- 727 x 5 x 2 = 7,270 times per strategy. Measured on condition 2
    that cost 7.28 s per strategy, which over 273,780 strategies is ~69 h
    against ~20 h for the pick itself. The day axis is sorted, so a tune
    window is a CONTIGUOUS slice and needs no mask at all; the drawdown is
    then one allocation-free pass. role_dd is kept as the readable reference
    and condition 1b asserts the two agree exactly.
    """
    return np.array([_dd_slice(accd[0], lo, hi), _dd_slice(accd[1], lo, hi)])


def role_dd(accd, dayyear, y0, y1):
    """True chronological max drawdown in R over calendar years [y0, y1].

    THE CURVE IS CUT TO THE ROLE'S YEARS AND THE DRAWDOWN RESTARTS THERE. A
    drawdown carried in from a year the tuner may not look at would make the
    objective depend on an unseen year, which is the fault this whole restart
    exists to remove.
    """
    a, b = y0 - YEAR0, y1 - YEAR0
    m = (dayyear >= a) & (dayyear <= b)
    out = np.zeros(accd.shape[0], np.float64)
    for s in range(accd.shape[0]):
        x = accd[s][m]
        if not len(x):
            out[s] = np.nan
            continue
        eq = np.cumsum(x)
        out[s] = float((np.maximum.accumulate(eq) - eq).max())
    return out


def pick_r2dd(totals, dds, ns, tot_tiebreak=True):
    """argmax of total R / max DD R, with MIN_TUNE_TRADES enforced.

    A ZERO DRAWDOWN DOES NOT WIN BY DIVISION. A configuration whose tune block
    never drew down has an infinite ratio and would beat every real one on a
    rounding artefact, so it is ranked by total R among the zero-DD set and
    only ahead of the rest if its total is positive. Nothing is divided by
    zero anywhere.
    """
    ok = np.asarray(ns) >= MIN_TUNE_TRADES
    if not ok.any():
        return -1
    t = np.asarray(totals, np.float64); d = np.asarray(dds, np.float64)
    with np.errstate(divide='ignore', invalid='ignore'):
        r = np.where(ok & np.isfinite(d) & (d > 0), t / np.where(d > 0, d, 1.0), -np.inf)
    # zero-drawdown blocks: rank them by total R, above everything finite only
    # if that total is positive
    zed = ok & np.isfinite(d) & (d <= 0) & (t > 0)
    if zed.any():
        r = np.where(zed, np.nanmax(r[np.isfinite(r)], initial=0.0) + t, r)
    if not np.isfinite(r).any():
        return -1
    best = float(np.nanmax(r))
    cand = np.flatnonzero(r >= best - 1e-12)
    if len(cand) == 1 or not tot_tiebreak:
        return int(cand[0])
    # TIEBREAK ON TOTAL R, not expectancy: expectancy is reported beside this
    # objective and never used, and a tiebreak is a use.
    return int(cand[int(np.argmax(t[cand]))])


def objective(block):
    """l2tune's objective on one role block (..., NSTAT): trade-weighted
    expectancy in account-normalised R, PF as tiebreak, n for the floor."""
    n = block[..., 0]
    e = np.where(n > 0, block[..., 1] / np.maximum(n, 1.0), -np.inf)
    gain = block[..., 2]; loss = block[..., 3]
    pf = np.where(loss > 0, gain / np.maximum(loss, 1e-12),
                  np.where(gain > 0, np.inf, 0.0))
    return n, e, pf


def pick(scores, ns, pfs):
    """argmax over configurations: expectancy, PF tiebreak, MIN_TUNE_TRADES
    enforced. Returns -1 when nothing clears the floor -- which is a result,
    not a failure, and is recorded as one."""
    ok = ns >= MIN_TUNE_TRADES
    if not ok.any():
        return -1
    e = np.where(ok, scores, -np.inf)
    best = float(e.max())
    cand = np.flatnonzero(e >= best - 1e-12)
    if len(cand) == 1:
        return int(cand[0])
    return int(cand[int(np.argmax(np.where(np.isfinite(pfs[cand]), pfs[cand], -np.inf)))])


# ==========================================================================
# the one-pass worker
# ==========================================================================
def strategy_jobs(mode, combo):
    """The deterministic (slice, configuration) job list for one strategy.

    Flat and ordered, so a strategy interrupted halfway can be resumed from a
    position index rather than from the beginning -- which is what the
    five-minute rule needs when ONE item is longer than the interval. A cold
    worker's first strategy took 481 s on 16 Nov: ~500 indicator variant series
    across 28 pairs, computed from nothing.
    """
    cfgs = {sn: axial(mode, combo, sn) for sn, _, _ in S.SLICES}
    jobs = [(sl, ci) for sl, (sn, _, _) in enumerate(S.SLICES)
            for ci in range(len(cfgs[sn]))]
    return cfgs, jobs


def new_state(nmax):
    return dict(pos=0,
                win=np.zeros((4, NSTEP, NYEAR, NSTAT), np.float64),
                tag=np.full((4, NSTEP), -1, np.int64),
                bestscore=np.full((4, NSTEP), -np.inf),
                bestpf=np.full((4, NSTEP), -np.inf),
                curve=np.full((nmax, 4), np.nan))


def tune_one_strategy(Y, mode, combo, state=None, on_tick=None, tick_every=None):
    """ONE PASS over the axial set for one strategy. All four streams, all five
    steps, out of a single engine pass per configuration.

    Returns
      win   (4, NSTEP, NYEAR, NSTAT) float64 -- each step's winner's FULL
            per-year record, per stream. Grade and trade years are in here but
            never read while picking.
      tag   (4, NSTEP) int64 -- the winning configuration's index, -1 if no
            configuration cleared MIN_TUNE_TRADES on that step
      curve (nconf, 4) float64 -- every configuration's tune score POOLED over
            all five tune windows, per stream: the whole axial surface, kept
      ncfg  (2,) int64 -- configurations enumerated for the trend and chop slices
    """
    ST = steps()
    slices = list(S.SLICES)                       # (name, plan, code)
    # pooled tune weight per year: a year inside two tune windows counts twice
    wt = np.zeros(NYEAR, np.float64)
    for s in ST:
        for y in range(s['tune'][0], s['tune'][1] + 1):
            wt[y - YEAR0] += 1.0

    cfgs, jobs = strategy_jobs(mode, combo)
    nmax = max(len(v) for v in cfgs.values())
    st = state if state is not None else new_state(nmax)
    win, tag = st['win'], st['tag']
    bestscore, bestpf, curve = st['bestscore'], st['bestpf'], st['curve']
    tnow = time.time()
    while st['pos'] < len(jobs):
        sl, ci = jobs[st['pos']]
        sname, plan, code = slices[sl]
        _tagname, ip, risk = cfgs[sname][ci]
        if OBJECTIVE == 'r2dd':
            acc, accd = Y.score(combo, ip, risk, mode, sname, code, plan, want_dd=True)
        else:
            acc = Y.score(combo, ip, risk, mode, sname, code, plan)  # (2, NYEAR, NSTAT)
            accd = None
        for rt in (0, 1):                      # 0 routed, 1 always-on
            stream = 2 * sl + rt               # 0 t-routed 1 t-allon 2 c-routed 3 c-allon
            a = acc[rt]
            pooled = (a * wt[:, None]).sum(axis=0, dtype=np.float64)
            pn, pe, _ = objective(pooled)
            curve[ci, stream] = pe if pn >= MIN_TUNE_TRADES * len(ST) else np.nan
            for si, sp in enumerate(ST):
                blk = role_sum(a, *sp['tune'])
                n, e, pf = objective(blk)
                if n < MIN_TUNE_TRADES:
                    continue
                if OBJECTIVE == 'r2dd':
                    # SCORE = total R / max DD R on THIS step's tune years.
                    # The drawdown is the real chronological one, from the
                    # per-day increments netted across all 28 pairs, cut to
                    # the tune years so no unseen year can move the pick.
                    tot = float(blk[1])
                    _lo, _hi = Y.winslice[tuple(sp['tune'])]
                    dd = float(role_dd_fast(accd, _lo, _hi)[rt])
                    if not np.isfinite(dd) or dd <= 0.0:
                        # a tune block with no drawdown does not win by
                        # division; it ranks by total R and only if positive
                        sc_ = (1e9 + tot) if tot > 0 else -np.inf
                    else:
                        sc_ = tot / dd
                    # TIEBREAK ON TOTAL R, never on expectancy: expectancy is
                    # reported beside this objective and a tiebreak is a use.
                    better = (sc_ > bestscore[stream, si] + 1e-12
                              or (abs(sc_ - bestscore[stream, si]) <= 1e-12
                                  and tot > bestpf[stream, si]))
                    if better:
                        bestscore[stream, si] = sc_
                        bestpf[stream, si] = tot
                        tag[stream, si] = ci
                        win[stream, si] = a
                    continue
                if e > bestscore[stream, si] + 1e-12 or (
                        abs(e - bestscore[stream, si]) <= 1e-12 and pf > bestpf[stream, si]):
                    bestscore[stream, si] = e
                    bestpf[stream, si] = pf
                    tag[stream, si] = ci
                    win[stream, si] = a
        st['pos'] += 1
        # CHECKPOINT INSIDE THE ITEM. The state is ~16 kB, so saving it costs
        # nothing and the five-minute rule holds even when one strategy is
        # longer than the interval.
        if on_tick is not None and tick_every and (time.time() - tnow) >= tick_every:
            on_tick(st)
            tnow = time.time()
    ncfg = np.array([len(cfgs['trend']), len(cfgs['chop'])], np.int64)
    return win, tag, curve, ncfg, bestscore, bestpf


# THE FIVE-MINUTE RULE (HANDOFF section 3). The cadence is TIME, not a count:
# a count is wrong the moment the per-item cost changes, and it changed by 30x
# between the contiguous and stratified draws on this very stage.
import l2ckpt


def _save_part(f, rows, idx, combos, worst, hits, misses):
    """One part file. The CURVE IS RAGGED and is stored flat with per-strategy
    lengths, never stacked.

    np.stack(curve) is what cost 2.3 hours on 16 Nov: the axial set is 227-512
    configurations depending on which indicators the strategy uses, so the
    per-strategy curve arrays have different shapes and the stack threw
    'all input arrays must have the same shape' AFTER every strategy in the
    shard had been scored and before anything was written. Flat plus offsets is
    exact and cannot be ragged-by-surprise; padding would have wasted 2 GB.
    """
    W = np.stack([r[0] for r in rows]).astype(np.float32)
    TG = np.stack([r[1] for r in rows])
    cflat = np.concatenate([r[2].reshape(-1) for r in rows]).astype(np.float32)
    cn = np.array([r[2].shape[0] for r in rows], np.int64)
    NC = np.stack([r[3] for r in rows])
    BS = np.stack([r[4] for r in rows]).astype(np.float32)
    BP = np.stack([r[5] for r in rows]).astype(np.float32)
    np.savez_compressed(
        f, win=W, tag=TG, curve_flat=cflat, curve_n=cn, ncfg=NC,
        tune_score=BS, tune_pf=BP,
        idx=np.array(idx, np.int64),
        combo=np.array([['%s' % x for x in cb] for cb in combos], dtype=object),
        year0=YEAR0, nyear=NYEAR, nstream=4, worst_cond1=worst,
        cache_hits=hits, cache_misses=misses)


def _worker(args):
    shard, nshard, mode, combos, outdir, cap = args
    S.load_costs()
    # CONTIGUOUS shards, not strided. The enumeration order is
    # product(c1, c2, vol, base) with base fastest, so a contiguous block holds
    # c1 and c2 nearly constant and the indicator variants of the inner slots
    # are computed once and reused across the whole block. Strided shards
    # (i % nshard) made every worker walk the same blocks and recompute the same
    # 512 variant series for a sixth as many strategies -- measured at 5.5 s per
    # strategy against 1.7 s contiguous.
    lo = shard * len(combos) // nshard
    hi = (shard + 1) * len(combos) // nshard
    mine = [(i, combos[i]) for i in range(lo, hi)]
    state = dict(Y=None, worst=0.0, hits=0, misses=0)

    def _save(path, ids, rows):
        _save_part(path, [r[0] for r in rows], ids, [r[1] for r in rows],
                   state['worst'], state['hits'], state['misses'])
        # Keep the shared disk series cache inside its budget. Nothing else
        # calls evict(), and an uncapped cache on a volume with 14 GB free is a
        # disk-full waiting to happen -- which already blocked this project once.
        if shard == 0:
            import l2cache as DCC
            freed = DCC.evict(budget_gb=CACHE_BUDGET_GB)
            if freed:
                print('    disk series cache: evicted %.2f GB to stay inside budget'
                      % (freed / 1024 ** 3), flush=True)

    ck = l2ckpt.Checkpointer(outdir, 'shard_%04d' % shard, save=_save)
    pf = os.path.join(outdir, 'shard_%04d_inflight.npz' % shard)

    def _save_partial(idx, cb, stt):
        tmp = pf + '.tmp.npz'
        np.savez(tmp, idx=np.int64(idx), combo=np.array(['%s' % x for x in cb], dtype=object),
                 pos=np.int64(stt['pos']), win=stt['win'], tag=stt['tag'],
                 bestscore=stt['bestscore'], bestpf=stt['bestpf'], curve=stt['curve'])
        os.replace(tmp, pf)
        ck.tick()

    def _load_partial(idx):
        if not os.path.exists(pf):
            return None
        try:
            z = np.load(pf, allow_pickle=True)
        except Exception as e:
            print('  ckpt: in-flight state unreadable (%s) -- that strategy restarts'
                  % type(e).__name__, flush=True)
            return None
        if int(z['idx']) != int(idx):
            return None
        return dict(pos=int(z['pos']), win=z['win'].astype(np.float64), tag=z['tag'],
                    bestscore=z['bestscore'].astype(np.float64),
                    bestpf=z['bestpf'].astype(np.float64),
                    curve=z['curve'].astype(np.float64))

    done = ck.completed()
    todo = [(i, cb) for i, cb in mine if i not in done]
    if not todo:
        return dict(shard=shard, n=0, skipped=True, seconds=0.0, worst_cond1=0.0,
                    evals=0, hits=0, misses=0, resumed=len(mine))
    if done:
        print('    g2 shard %02d: resuming, %d of %d strategies already on disk'
              % (shard, len(mine) - len(todo), len(mine)), flush=True)
    Y = Years(cap=cap)
    state['Y'] = Y
    t0 = time.time()
    every = l2ckpt.CKPT_SECONDS
    for ndone, (i, cb) in enumerate(todo, 1):
        st0 = _load_partial(i)
        if st0 is not None:
            print('    g2 shard %02d: resuming strategy %d from configuration %d'
                  % (shard, i, st0['pos']), flush=True)
        res = tune_one_strategy(Y, mode, cb, state=st0,
                                on_tick=lambda stt, _i=i, _cb=cb: _save_partial(_i, _cb, stt),
                                tick_every=every)
        state['worst'] = Y.worst_cond1
        state['hits'] = Y.sc.cache.hits
        state['misses'] = Y.sc.cache.misses
        ck.add(i, (res, cb))
        if ndone % 25 == 0:
            el = time.time() - t0
            print('    g2 shard %02d: %6d/%6d  %.2f s/strategy  %.0f evals  %.0f min left'
                  % (shard, ndone, len(todo), el / ndone, Y.n_eval / ndone,
                     (el / ndone) * (len(todo) - ndone) / 60), flush=True)
    ck.flush()
    return dict(shard=shard, n=len(todo), skipped=False, seconds=time.time() - t0,
                worst_cond1=float(Y.worst_cond1), evals=Y.n_eval,
                hits=Y.sc.cache.hits, misses=Y.sc.cache.misses,
                parts=ck.n_parts_written)


def banked_idx(mode, tag):
    """Every strategy index already on disk for this tag."""
    d = out_dir(mode, tag)
    done = set()
    for f in glob.glob(os.path.join(d, 'shard_*_part*.npz')):
        try:
            done.update(int(x) for x in np.load(f, allow_pickle=True)['idx'])
        except Exception as e:
            print('  bank: %s unreadable (%s)' % (os.path.basename(f), type(e).__name__), flush=True)
    return done


def _fill_worker(args):
    """Bank an explicit list of strategy indices. Used to fill a straggling
    shard's tail from the other end with the cores that would otherwise idle."""
    wid, njobs, mode, combos, idxs, outdir, cap, prefix = args
    S.load_costs()
    mine = [i for n, i in enumerate(idxs) if n % njobs == wid]
    state = dict(worst=0.0, hits=0, misses=0)

    def _save(path, ids, rows):
        _save_part(path, [r[0] for r in rows], ids, [r[1] for r in rows],
                   state['worst'], state['hits'], state['misses'])

    ck = l2ckpt.Checkpointer(outdir, '%s_%04d' % (prefix, wid), save=_save)
    done = ck.completed()
    todo = [i for i in mine if i not in done]
    if not todo:
        return dict(worker=wid, n=0, skipped=True)
    Y = Years(cap=cap)
    t0 = time.time()
    every = l2ckpt.CKPT_SECONDS
    for k, i in enumerate(todo, 1):
        cb = combos[i]
        res = tune_one_strategy(
            Y, mode, cb,
            on_tick=lambda stt: ck.tick(), tick_every=every)
        state['worst'] = Y.worst_cond1
        state['hits'] = Y.sc.cache.hits
        state['misses'] = Y.sc.cache.misses
        ck.add(i, (res, cb))
        if k % 25 == 0:
            el = time.time() - t0
            print('    fill %02d: %5d/%5d  %.2f s/strategy  %.0f min left'
                  % (wid, k, len(todo), el / k, (el / k) * (len(todo) - k) / 60), flush=True)
    ck.flush()
    return dict(worker=wid, n=len(todo), skipped=False, seconds=time.time() - t0)


def stage_fill(mode, tag, jobs=6, cap=30000, wait_for_free=0):
    """FILL WHATEVER IS MISSING FROM A TAG, from the end backwards.

    A straggling shard cannot be sped up from outside -- its worker fixed its
    own to-do list when it started -- but the BANK can be completed by someone
    else, and the bank is what the next stage waits on. Working backwards means
    the overlap with the straggler is bounded by where they meet.
    """
    G.manifest_check()
    S.load_costs()
    opts = S.mode_opts(S.slot_options(), mode)
    combos = list(S.combo_iter(opts))
    if wait_for_free:
        # do not oversubscribe: wait until the running pool has shrunk
        import subprocess
        while True:
            n = len(subprocess.run(['pgrep', '-f', 'l2r2gate2.py --stage run'],
                                   capture_output=True, text=True).stdout.split())
            if n <= wait_for_free:
                break
            print('    fill: waiting, %d tuning processes still up (want <= %d)'
                  % (n, wait_for_free), flush=True)
            time.sleep(120)
    missing = sorted(set(range(len(combos))) - banked_idx(mode, tag), reverse=True)
    print('  fill: %s of %s strategies missing from mode%s_%s; %d workers, from the END backwards'
          % (f'{len(missing):,}', f'{len(combos):,}', mode, tag, jobs), flush=True)
    if not missing:
        print('  fill: nothing missing', flush=True)
        return 0
    import multiprocessing as mp
    outdir = out_dir(mode, tag)
    args = [(k, jobs, mode, combos, missing, outdir, cap, 'shard_fill') for k in range(jobs)]
    t0 = time.time()
    with mp.Pool(jobs) as pool:
        res = pool.map(_fill_worker, args)
    n = sum(r['n'] for r in res)
    left = len(set(range(len(combos))) - banked_idx(mode, tag))
    print('  fill: banked %s in %.1f min; %s still missing'
          % (f'{n:,}', (time.time() - t0) / 60, f'{left:,}'), flush=True)
    return left


def cond_file(which, mode):
    """The condition record's path, CARRYING THE WALK.

    On 24 Nov an eleven-step condition run overwrote chain 22A's five-step
    records, because both wrote to r2gate2_cond2_modeA.csv with no walk in the
    name. The five-step walk keeps the unsuffixed name so the committed records
    and l2r2modearep.py are unaffected; every other walk is suffixed.
    """
    sfx = '' if WALK == 'base5' else '_' + WALK
    return os.path.join(ROOTOUT, 'r2gate2_%s_mode%s%s.csv' % (which, mode, sfx))


def out_dir(mode, tag):
    return os.path.join(ROOTOUT, 'r2gate2', 'mode%s_%s' % (mode, tag))


def run(mode, combos, tag, jobs=6, cap=900, nshard=None):
    """Banked, sharded, RESUMABLE. A shard present is never recomputed.

    JOBS ARE CAPPED BY RAM, not by cores (HANDOFF section 3, 12 Sep). Each
    worker holds the Scorer's 28-pair tables plus its indicator cache.
    """
    import multiprocessing as mp
    G.manifest_check()
    outdir = out_dir(mode, tag)
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, 'spec.json'), 'w') as fh:
        json.dump(dict(mode=mode, n=len(combos), jobs=jobs, cache_cap=cap,
                       years='%d-%d' % (YEAR0, YEAR0 + NYEAR - 1),
                       steps=[s['name'] for s in steps()],
                       objective='account-normalised R (ACCT_OBJECTIVE True), '
                                 'trade-weighted over the step tune years, PF tiebreak, '
                                 'MIN_TRADES_PICK=%d' % MIN_TUNE_TRADES,
                       config_set='axial: default + every single-knob deviation over each declared grid',
                       stamp=time.strftime('%F %T')), fh, indent=1)
    # MORE SHARDS THAN WORKERS. With nshard == jobs, one slow shard holds the
    # whole stage: on 17 Nov mode A's shard 06 drew strategies with 629
    # configurations against the field's 494 average and ran 2 hours past the
    # other seven, leaving 7 of 8 cores idle. Finer shards let the pool hand a
    # free worker the next piece instead.
    nshard = int(nshard or jobs)
    assert nshard >= jobs, 'nshard must be at least jobs'
    args = [(k, nshard, mode, combos, outdir, cap) for k in range(nshard)]
    t0 = time.time()
    if jobs == 1:
        res = [_worker(a) for a in args]
    else:
        with mp.Pool(jobs) as pool:
            res = pool.map(_worker, args)
    done = sum(r['n'] for r in res)
    worst = max(r['worst_cond1'] for r in res)
    el = time.time() - t0
    print('  gate 2: %d strategies in %.1f min (%d of %d shards skipped), %.3f s/strategy wall'
          % (done, el / 60, sum(r['skipped'] for r in res), nshard, el / max(done, 1)), flush=True)
    print('  CONDITION 1: worst |sum of a trade per-year marks - its R| = %.3g' % worst, flush=True)
    assert worst < 1e-9, 'CONDITION 1 FAILED: year-split marks do not reconstruct trade R (%.3g)' % worst
    sz = sum(os.path.getsize(x) for x in glob.glob(os.path.join(outdir, 'shard_*_part*.npz')))
    # SIZE AGAINST WHAT IS BANKED, NOT WHAT THIS RUN COMPUTED. A resumed run that
    # computed 3,070 of 273,780 divided the whole 1,252.9 MB directory by 3,070 and
    # printed "417.92 kB each -> 109.12 GB for all of mode B", which is 89x the
    # truth and exactly the kind of number that gets quoted later.
    nb = len(load(mode, tag)[1])
    print('  bank: %.1f MB compressed for %d strategies = %.2f kB each -> %.2f GB for all %s of mode %s'
          % (sz / 1024 ** 2, nb, sz / max(nb, 1) / 1024,
             sz / max(nb, 1) * S.n_combos(S.mode_opts(S.slot_options(), mode)) / 1024 ** 3,
             f'{S.n_combos(S.mode_opts(S.slot_options(), mode)):,}', mode), flush=True)
    return outdir, res


def bank_files(mode, tag):
    outdir = out_dir(mode, tag)
    fs = sorted(glob.glob(os.path.join(outdir, 'shard_*_part*.npz')))
    assert fs, 'no gate 2 bank at %s' % outdir
    return outdir, fs


def load(mode, tag, with_curve=False):
    """The bank, in enumeration order. The curve stays ragged -- a list of
    (nconf, 4) arrays -- because that is what it is."""
    outdir, fs = bank_files(mode, tag)
    W, TG, IX, CB, TS, CV = [], [], [], [], [], []
    for f in fs:
        z = np.load(f, allow_pickle=True)
        W.append(z['win']); TG.append(z['tag'])
        IX.append(z['idx']); CB.append(z['combo']); TS.append(z['tune_score'])
        if with_curve:
            flat = z['curve_flat']; cn = z['curve_n']; off = 0
            for m in cn:
                CV.append(flat[off:off + m * 4].reshape(int(m), 4)); off += m * 4
    ix = np.concatenate(IX)
    # DEDUPE BY idx. Two processes filling the same tag from different ends can
    # legitimately bank the same strategy twice; without this the duplicate
    # rows would both survive the sort and be counted as two strategies.
    o = np.argsort(ix, kind='stable')
    uniq = np.concatenate(([True], ix[o][1:] != ix[o][:-1]))
    o = o[uniq]
    out = (np.concatenate(W)[o].astype(np.float64), np.concatenate(TG)[o],
           np.concatenate(CB)[o], np.concatenate(TS)[o].astype(np.float64), outdir)
    if with_curve:
        return out + ([CV[i] for i in o],)
    return out


# ==========================================================================
# CONDITION 2 — the banked one pass equals the naive per-step path
# ==========================================================================
def per_step_reference(Y, mode, combo):
    """THE NAIVE PATH, deliberately written the slow way: for each of the five
    steps, re-run the engine over the whole axial set and read only that step's
    tune years. Five times the engine work, no banking.

    This is what condition 2 compares against. It tests THE BANKING -- that one
    pass reduced per year gives the same picks and the same grade and trade
    records as five independent passes. It is not a claim about coordinate
    descent, which is window-dependent and therefore cannot be one-passed at
    all (HANDOFF 0l).
    """
    ST = steps()
    tag = np.full((4, NSTEP), -1, np.int64)
    win = np.zeros((4, NSTEP, NYEAR, NSTAT), np.float64)
    for si, s in enumerate(ST):
        for sl, (sname, plan, code) in enumerate(S.SLICES):
            cfg = axial(mode, combo, sname)
            best = np.full(2, -np.inf); bpf = np.full(2, -np.inf)
            for ci, (_t, ip, risk) in enumerate(cfg):
                if OBJECTIVE == 'r2dd':
                    acc, accd = Y.score(combo, ip, risk, mode, sname, code, plan,
                                        want_dd=True)
                else:
                    acc = Y.score(combo, ip, risk, mode, sname, code, plan)
                    accd = None
                for rt in (0, 1):
                    stream = 2 * sl + rt
                    blk = role_sum(acc[rt], *s['tune'])
                    n, e, pf = objective(blk)
                    if n < MIN_TUNE_TRADES:
                        continue
                    if OBJECTIVE == 'r2dd':
                        tot = float(blk[1])
                        _lo, _hi = Y.winslice[tuple(s['tune'])]
                        dd = float(role_dd_fast(accd, _lo, _hi)[rt])
                        sc_ = (tot / dd if (np.isfinite(dd) and dd > 0)
                               else ((1e9 + tot) if tot > 0 else -np.inf))
                        if sc_ > best[rt] + 1e-12 or (abs(sc_ - best[rt]) <= 1e-12
                                                      and tot > bpf[rt]):
                            best[rt] = sc_; bpf[rt] = tot
                            tag[stream, si] = ci
                            win[stream, si] = acc[rt]
                        continue
                    if e > best[rt] + 1e-12 or (abs(e - best[rt]) <= 1e-12 and pf > bpf[rt]):
                        best[rt] = e; bpf[rt] = pf
                        tag[stream, si] = ci
                        win[stream, si] = acc[rt]
    return win, tag


def stage_cond2(mode, n, out=None, max_minutes=120):
    """Prove the banked path equals the per-step path, to 1e-9, on `n`
    strategies. If the full comparison would exceed `max_minutes` the subset is
    narrowed -- and the subset still spans every slot and both streams, because
    `stratified` draws each slot's options balanced by construction."""
    G.manifest_check()
    S.load_costs()
    opts = S.mode_opts(S.slot_options(), mode)
    combos = G.stratified(opts, n)
    Y = Years()
    # time one strategy on both paths, then decide how many fit
    t0 = time.time(); tune_one_strategy(Y, mode, combos[0]); t_bank = time.time() - t0
    t0 = time.time(); per_step_reference(Y, mode, combos[0]); t_ref = time.time() - t0
    per = t_bank + t_ref
    fits = int(max_minutes * 60 / max(per, 1e-9))
    use = combos[:min(len(combos), fits)]
    print('  condition 2: %.2f s banked + %.2f s per-step = %.2f s/strategy; %d fit in %d min, '
          'comparing %d of %d' % (t_bank, t_ref, per, fits, max_minutes, len(use), len(combos)), flush=True)
    rows = []
    for k, cb in enumerate(use):
        wb, tb, _cv, _nc, _bs, _bp = tune_one_strategy(Y, mode, cb)
        wr, tr = per_step_reference(Y, mode, cb)
        for stream in range(4):
            for si in range(NSTEP):
                dw = float(np.abs(wb[stream, si] - wr[stream, si]).max())
                rows.append(dict(combo='|'.join(cb), stream=STREAMS[stream],
                                 step=steps()[si]['name'],
                                 tag_banked=int(tb[stream, si]), tag_perstep=int(tr[stream, si]),
                                 tag_match=int(tb[stream, si] == tr[stream, si]),
                                 max_abs_record_diff=dw,
                                 record_match=int(dw < 1e-9)))
        if (k + 1) % 25 == 0:
            print('    cond2 %d/%d' % (k + 1, len(use)), flush=True)
    D = pd.DataFrame(rows)
    out = out or cond_file('cond2', mode)
    D.to_csv(out, index=False)
    nb = int((1 - D.tag_match).sum()); nr = int((1 - D.record_match).sum())
    print('  CONDITION 2: %d strategies x 4 streams x %d steps = %d comparisons; '
          'tune-pick mismatches %d, record mismatches %d (worst |diff| %.3g) -> %s'
          % (len(use), NSTEP, len(D), nb, nr, float(D.max_abs_record_diff.max()),
             os.path.basename(out)), flush=True)
    # slot and stream coverage of the subset, so the check cannot be narrow by accident
    cov = {s: len(set(c.split('|')[i] for c in D.combo.unique()))
           for i, s in enumerate(S.SLOTS)}
    print('  subset coverage: %s options per slot; streams %s'
          % (cov, sorted(D.stream.unique())), flush=True)
    assert nb == 0 and nr == 0, 'CONDITION 2 FAILED: %d pick and %d record mismatches' % (nb, nr)
    return D


def stage_cond1b(mode='A', n=8, nconf=12):
    """CONDITION 1b: the DD-carrying accumulator has not drifted from the
    shipped one.

    _year_marks_dd is a COPY of _year_marks with a per-day vector added. A copy
    can drift, and if it drifts the r2dd bank is tuned on numbers that no other
    stage would reproduce. So on the same strategies and the same
    configurations both are run and their `acc` must be IDENTICAL -- not close,
    identical, because the added code does not touch any term of it.

    It also checks the drawdown is a real one: the per-day vector summed over a
    role's years must equal that role's total R from `acc`, which is only true
    if every increment landed on exactly one day and none was dropped.
    """
    G.manifest_check()
    S.load_costs()
    opts = S.mode_opts(S.slot_options(), mode)
    combos = G.stratified(opts, n)
    Y = Years()
    rows = []
    worst_acc = 0.0
    worst_sum = 0.0
    worst_dd = 0.0
    for cb in combos:
        for sl, (sname, plan, code) in enumerate(S.SLICES):
            cfg = axial(mode, tuple(cb), sname)
            for ci, (_t, ip, risk) in enumerate(cfg[:nconf]):
                a1 = Y.score(tuple(cb), ip, risk, mode, sname, code, plan)
                a2, accd = Y.score(tuple(cb), ip, risk, mode, sname, code, plan,
                                   want_dd=True)
                da = float(np.abs(a1 - a2).max())
                worst_acc = max(worst_acc, da)
                # the day vector must reproduce each role's total R
                for sp in steps():
                    blk = role_sum(a2, *sp['tune'])
                    y0, y1 = sp['tune']
                    m = (Y.dayyear >= y0 - YEAR0) & (Y.dayyear <= y1 - YEAR0)
                    ref = role_dd(accd, Y.dayyear, y0, y1)
                    lo, hi = Y.winslice[(y0, y1)]
                    fast = role_dd_fast(accd, lo, hi)
                    worst_dd = max(worst_dd, float(np.abs(ref - fast).max()))
                    for rt in (0, 1):
                        ds = float(accd[rt][m].sum())
                        tt = float(blk[rt][1])
                        worst_sum = max(worst_sum, abs(ds - tt))
                rows.append(dict(combo='|'.join(cb), slice=sname, config=ci,
                                 max_abs_acc_diff=da))
    D = pd.DataFrame(rows)
    out = os.path.join(ROOTOUT, 'r2gate2_cond1b_mode%s.csv' % mode)
    D.to_csv(out, index=False)
    print('  CONDITION 1b: %d (strategy, slice, config) pairs scored both ways; '
          'worst |acc diff| %.3g, worst |day-vector sum - role total R| %.3g, '
          'worst |role_dd - role_dd_fast| %.3g -> %s'
          % (len(D), worst_acc, worst_sum, worst_dd, os.path.basename(out)), flush=True)
    assert worst_acc == 0.0, ('CONDITION 1b FAILED: the DD accumulator returns a '
                              'different per-year record, worst |diff| %.6g' % worst_acc)
    assert worst_sum < 1e-9, ('CONDITION 1b FAILED: the per-day vector does not sum to '
                              'the role total R, worst |diff| %.6g -- an increment was '
                              'dropped or double counted' % worst_sum)
    assert worst_dd < 1e-12, ('CONDITION 1b FAILED: the fast drawdown disagrees with '
                              'the reference by %.6g' % worst_dd)
    print('  condition 1b PASSED: the copy is identical, the day vector is complete, '
          'and the fast drawdown matches the reference', flush=True)
    return D


def stage_cond1(mode, n=40):
    """CONDITION 1 on its own: scored strategies, every trade's per-year marks
    must sum to its R. The kernel checks every trade; this reports the worst."""
    G.manifest_check()
    S.load_costs()
    opts = S.mode_opts(S.slot_options(), mode)
    Y = Years()
    for cb in G.stratified(opts, n)[:n]:
        for sname, plan, code in S.SLICES:
            cfg = axial(mode, cb, sname)
            for _t, ip, risk in (cfg[0], cfg[len(cfg) // 3], cfg[-1]):
                Y.score(cb, ip, risk, mode, sname, code, plan)
    print('  CONDITION 1: %d evaluations, worst |sum of per-year marks - trade R| = %.3g'
          % (Y.n_eval, Y.worst_cond1), flush=True)
    pd.DataFrame([dict(mode=mode, n_strategies=n, n_evaluations=Y.n_eval,
                       worst_abs_diff=Y.worst_cond1, pass_=int(Y.worst_cond1 < 1e-9))]
                 ).to_csv(cond_file('cond1', mode), index=False)
    assert Y.worst_cond1 < 1e-9, 'CONDITION 1 FAILED (%.3g)' % Y.worst_cond1
    return Y.worst_cond1


# ==========================================================================
# the grid report, and costing from measurement
# ==========================================================================
BOX_VCPU, BOX_RATE, MAC_CORES = 16, 0.10, 8


def stage_grid(mode='A'):
    """The declared grid and the axial set size, from the code that runs it."""
    rows = []
    for kname, grid in (('atr_len', T.GRID_ATR), ('atr_mult (stop)', T.GRID_STOP),
                        ('tp_mult', T.GRID_TP), ('be_pct', T.GRID_BE),
                        ('trail_arm', T.GRID_ARM), ('trail_mult', T.GRID_TRAIL)):
        rows.append(dict(knob=kname, n_values=len(grid), lo=min(grid), hi=max(grid),
                         in_trend=kname.split()[0] in [k for k, _ in T.RISK_KNOBS_TREND],
                         in_chop=kname.split()[0] in [k for k, _ in T.RISK_KNOBS_CHOP]))
    Gd = pd.DataFrame(rows)
    print('-- the declared risk grid, l2tune as it stands --', flush=True)
    print(Gd.to_string(index=False), flush=True)
    joint = 1
    for _, g in T.RISK_KNOBS_TREND:
        joint *= len(g)
    print('   joint product of the trend risk grid alone: %s configurations per strategy'
          % f'{joint:,}', flush=True)
    opts = S.mode_opts(S.slot_options(), mode)
    sample = G.stratified(opts, 300)
    nt = [len(axial(mode, cb, 'trend')) for cb in sample]
    nc = [len(axial(mode, cb, 'chop')) for cb in sample]
    tot = np.array(nt) + np.array(nc)
    print('   AXIAL set, measured over 300 stratified mode %s strategies: trend %d-%d (mean %.1f), '
          'chop %d-%d (mean %.1f), total mean %.1f per strategy'
          % (mode, min(nt), max(nt), np.mean(nt), min(nc), max(nc), np.mean(nc), tot.mean()), flush=True)
    # the parameters the declared grid does not move
    reg = T.registry()
    fr = []
    for slot in ('c1', 'vol', 'base', 'exit_ind'):
        for name in opts[slot]:
            allp = sorted(reg[name]); allowed = T.tuned_params(name, cap=T.CAP_N)
            frozen = [p for p in allp if p not in allowed]
            if frozen:
                fr.append(dict(slot=slot, indicator=name, n_params=len(allp),
                               tuned=len(allowed), frozen=len(frozen),
                               extra_axial=sum(max(0, len(T.ind_param_grid(reg[name][p])) - 1)
                                               for p in frozen)))
    F = pd.DataFrame(fr)
    print('\n-- parameters the library exposes that the declared grid does NOT move (CAP_N=%s) --'
          % ('None, uncapped' if T.CAP_N is None else T.CAP_N), flush=True)
    print((F.to_string(index=False) if len(F) else
           '   NONE -- every parameter the registry exposes is moved (Jack, 16 Nov)'), flush=True)
    Gd.to_csv(os.path.join(ROOTOUT, 'r2gate2_grid.csv'), index=False)
    F.to_csv(os.path.join(ROOTOUT, 'r2gate2_frozen_params.csv'), index=False)
    return Gd, F, float(tot.mean())


def costing(sec_per_strategy, bank_bytes_per_strategy):
    rows = []
    opts = S.slot_options()
    for m in S.MODE_ORDER:
        n = S.n_combos(S.mode_opts(opts, m))
        ch = n * sec_per_strategy / 3600.0
        rows.append(dict(mode=m, strategies=n, sec_per_strategy=sec_per_strategy,
                         core_hours=ch, mac_hours=ch / MAC_CORES, mac_days=ch / MAC_CORES / 24,
                         cloud3_hours=ch / (3 * BOX_VCPU), cloud3_cost_usd=3 * BOX_RATE * ch / (3 * BOX_VCPU),
                         cloud6_hours=ch / (6 * BOX_VCPU), cloud6_cost_usd=6 * BOX_RATE * ch / (6 * BOX_VCPU),
                         bank_gb=n * bank_bytes_per_strategy / 1024 ** 3))
    return pd.DataFrame(rows)


def stage_endtoend(mode='A', n=12, jobs=2):
    """THE CHEAP END-TO-END CHECK, and it goes FIRST in every chain.

    On 16 Nov the 2,000-strategy smoke scored every strategy and then died in
    np.stack on a ragged curve -- 2.3 hours of compute lost to a bug in the
    SAVE path, which single-strategy timing had never touched because it called
    tune_one_strategy directly and never went through the pool, the part files
    or the reader. Twelve strategies through run() and load() exercise all
    three in under a minute, so the save path can never again be first
    exercised by the expensive run.
    """
    G.manifest_check()
    S.load_costs()
    opts = S.mode_opts(S.slot_options(), mode)
    combos = G.stratified(opts, n)[:n]
    tag = 'endtoend'
    d = out_dir(mode, tag)
    if os.path.isdir(d):
        import shutil, datetime
        keep = d + '_prev_' + datetime.datetime.now().strftime('%H%M%S')
        shutil.move(d, keep)           # moved, never deleted
        print('  previous end-to-end bank kept at %s' % os.path.basename(keep), flush=True)
    run(mode, combos, tag, jobs=jobs, cap=8000)
    # HALF THE RULE IS RESTART. Run it again on the same tag: every shard must
    # skip, nothing may be recomputed, and the reader must still get all n.
    _od2, res2 = run(mode, combos, tag, jobs=jobs, cap=8000)
    redone = sum(r['n'] for r in res2)
    assert redone == 0, ('RESUME BROKEN: a second run recomputed %d strategies that were '
                         'already on disk' % redone)
    print('  RESUME: second run recomputed 0 of %d strategies -- every part on disk was skipped'
          % n, flush=True)
    W, TG, CB, TS, _od, CV = load(mode, tag, with_curve=True)
    assert W.shape == (n, 4, NSTEP, NYEAR, NSTAT), 'win shape %s' % (W.shape,)
    assert TG.shape == (n, 4, NSTEP), 'tag shape %s' % (TG.shape,)
    assert len(CV) == n and all(c.shape[1] == 4 for c in CV), 'ragged curve round-trip'
    widths = sorted({int(c.shape[0]) for c in CV})
    picked = int((TG >= 0).sum()); tot = TG.size
    # INTRA-ITEM RESUME, proven rather than assumed: interrupt one strategy
    # partway through its axial set, carry the state across, and require the
    # finished answer to be bit-identical to the uninterrupted one.
    Y = Years(cap=8000)
    cb = combos[min(1, n - 1)]
    w1, t1, c1, _n1, b1, _p1 = tune_one_strategy(Y, mode, cb)
    _cf, jobs = strategy_jobs(mode, cb)
    snap = {}

    def _tick(stt):
        if stt['pos'] >= len(jobs) // 3 and not snap:
            snap.update(pos=stt['pos'], win=stt['win'].copy(), tag=stt['tag'].copy(),
                        bestscore=stt['bestscore'].copy(), bestpf=stt['bestpf'].copy(),
                        curve=stt['curve'].copy())
            raise KeyboardInterrupt
    try:
        tune_one_strategy(Y, mode, cb, state=new_state(c1.shape[0]),
                          on_tick=_tick, tick_every=0.001)
    except KeyboardInterrupt:
        pass
    w2, t2, c2, _n2, b2, _p2 = tune_one_strategy(Y, mode, cb, state=dict(snap))
    same = (np.array_equal(w1, w2) and np.array_equal(t1, t2)
            and np.allclose(c1, c2, equal_nan=True) and np.allclose(b1, b2, equal_nan=True))
    print('  INTRA-ITEM RESUME: interrupted at configuration %d of %d and carried the state '
          'across -- records, picks, curve and tune scores %s (max |diff| %.3g)'
          % (snap['pos'], len(jobs), 'IDENTICAL' if same else 'DIFFER',
             float(np.abs(w1 - w2).max())), flush=True)
    assert same, 'INTRA-ITEM RESUME BROKEN: a resumed strategy does not match the uninterrupted one'

    print('  END TO END: %d strategies, win %s, tag %s, curve widths %s (THE ragged axis), '
          '%d of %d (stream, step) picks cleared MIN_TRADES_PICK=%d'
          % (n, W.shape, TG.shape, widths, picked, tot, MIN_TUNE_TRADES), flush=True)
    assert picked > 0, 'no pick anywhere cleared the trade floor -- the bank would be empty'
    print('END TO END COMPLETE', flush=True)
    return True


if __name__ == '__main__':
    stage = G.opt('--stage', str, 'grid')
    mode = G.opt('--mode', str, 'A')
    tag = G.opt('--tag', str, 'smoke2k')
    jobs = G.opt('--jobs', int, 6)
    if stage == 'endtoend':
        stage_endtoend(mode, n=G.opt('--n', int, 12), jobs=G.opt('--jobs', int, 2))
    elif stage == 'grid':
        stage_grid(mode)
    elif stage == 'fill':
        stage_fill(mode, G.opt('--tag', str, 'full'), jobs=G.opt('--jobs', int, 6),
                   cap=G.opt('--cap', int, 30000),
                   wait_for_free=G.opt('--wait-free', int, 0))
    elif stage == 'cond1b':
        stage_cond1b(G.opt('--mode', str, 'A'), n=G.opt('--n', int, 8),
                     nconf=G.opt('--nconf', int, 12))
    elif stage == 'cond1':
        stage_cond1(mode, n=G.opt('--n', int, 40))
    elif stage == 'cond2':
        stage_cond2(mode, n=G.opt('--n', int, 2000), max_minutes=G.opt('--minutes', int, 120))
    elif stage in ('smoke', 'run'):
        G.manifest_check()
        S.load_costs()
        n = G.opt('--n', int, 2000)
        opts = S.mode_opts(S.slot_options(), mode)
        total = S.n_combos(opts)
        if n >= total:
            combos = list(S.combo_iter(opts)); tag = G.opt('--tag', str, 'full')
            print('  FULL enumeration: all %s mode %s strategies' % (f'{len(combos):,}', mode), flush=True)
        else:
            combos = G.stratified(opts, n)
            print('  stratified %d of %s mode %s strategies' % (len(combos), f'{total:,}', mode), flush=True)
        # THE SUFFIX IS APPLIED HERE, NOT LEFT TO THE CALLER. A --tag full under
        # the r2dd objective would otherwise write a differently-tuned bank over
        # the shipped one, and the two are not interchangeable: same filenames,
        # different objective, no way to tell them apart afterwards.
        tag = bank_tag(tag)
        print('  bank tag: %s (objective %s)' % (tag, OBJECTIVE), flush=True)
        outdir, res = run(mode, combos, tag, jobs=jobs, cap=G.opt('--cap', int, 900),
                          nshard=G.opt('--nshard', int, None))
        sz = sum(os.path.getsize(x) for x in glob.glob(os.path.join(outdir, 'shard_*_part*.npz')))
        done = sum(r['n'] for r in res) or len(combos)
        wall = max(r['seconds'] for r in res)
        secs = wall * jobs / done           # core-seconds per strategy
        C = costing(secs, sz / done)
        C.to_csv(os.path.join(ROOTOUT, 'r2gate2_costing_from_mode%s_%s.csv' % (mode, tag)), index=False)
        print('\n-- cost of the full gate 2, from THIS measurement (%.3f core-s/strategy) --' % secs, flush=True)
        print(C.to_string(index=False, float_format=lambda x: '%.4g' % x), flush=True)
    else:
        raise SystemExit('unknown stage %s' % stage)
