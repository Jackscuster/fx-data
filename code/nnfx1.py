import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""NNFX PHASE 1, STAGE 1 — ONE PIECE ALONE, WALK-FORWARD. HANDOFF 0m.

1a  each of the 39 C1 indicators by itself, 28 pairs: enter on the flip, exit
    on the opposite flip, nothing else. Then again with the canonical 1.5 ATR
    stop and half off at 1 ATR.
1b  each of the 15 baselines by itself: enter when price closes across it, exit
    on the cross back.
1c  selection test: rank them on the tuning years, trade the top K unseen.

NO SECOND ENGINE. 0b found that two scorers with two undeclared conventions
cost this project a winner list, so stage 1 runs the SHIPPED l2engine and
neutralises the slots it is not testing, rather than reimplementing the bar
loop. "C1 alone" is produced like this, and every part of it is provable:

  c2_lc, c2_sc   forced all True  -> the confirmation can never block
  v_ok_l, v_ok_s forced all True  -> the volume gate can never block
  bl             set to the close -> `cl > b + max_atr_dist*a` is false for any
                                     non-negative max_atr_dist, so the
                                     baseline-distance block can never fire,
                                     and `side` is 0 so no baseline cross is
                                     ever detected
  use_base_cross=False, use_continuation=False, exit_on_base_cross=False,
  exit_on_exit_ind=False, one_candle_rule=False, bridge_bars huge

What is left is exactly: enter when c1_lt/c1_st flips, exit when it flips back.
`l2engine.py:462` shows the C1-flip route gated only by `agree_long`, which is
C2 and volume -- NOT by the baseline side -- so nothing else needs disabling.

THE RISK UNIT IS R PER 1.5 ATR, FOR BOTH VARIANTS. The engine books
r = move x units / RISK with units ~ 1/(atr_mult x ATR), so engine r scales as
1/atr_mult. Every figure here is restated as r x atr_mult / 1.5, which is the
canonical NNFX stop. Without that the no-stop variant and the 1.5 ATR variant
would be in different units and could not be compared -- and it is the same
correction ACCT_OBJECTIVE makes, for the same reason.

  flip_only       atr_mult 50, tp_mult 900 (the no-target sentinel). A 50 ATR
                  stop is never reached; stage_run ASSERTS that no trade exited
                  by stop, so "nothing else" is checked rather than assumed.
  canonical_risk  atr_mult 1.5, first target at 1.0 ATR (tp_mult = 1/1.5),
                  then breakeven and trail, which is plan 2.

THREE SETTINGS PER INDICATOR. For the 34 C1 and 15 baselines carrying an
integer length, half / default / double of that length. FIVE C1 indicators are
parameterised by a smoothing CONSTANT instead -- ehlers_reverse_ema (alpha),
kalman_filter (sharpness, k), laguerre_filter (alpha), mama_fama (fast_limit,
slow_limit) and parabolic_sar (sar_start, sar_increment). For those, a LARGER
constant is a SHORTER memory, so "half length" doubles the constant and
"double length" halves it. Stated because it is the opposite direction.
Two baselines default to length 2 (fantail_vma, vidya), where half is also 2,
so they have two distinct settings and not three; the report says so.
"""
import time, glob, json, hashlib, inspect, itertools
import numpy as np, pandas as pd
from scipy import stats

import l2lib as L
import l2sweep as S
import l2engine as E
import l2r2gate1 as G

OUT = os.path.join(ROOTOUT, 'nnfx')
os.makedirs(OUT, exist_ok=True)
LEDGER = os.path.join(OUT, 'CANDIDATE_LEDGER.csv')

RISK_UNIT_ATR = 1.5          # every R here is per 1.5 ATR
# JACK'S DECIDED RULE 1 (7 Sep 2026): a pair does not trade while its own
# ATR is in its bottom 5%. None turns the floor off; every writer records it.
LOWVOL_Q = 0.05
# THE PEG GUARD, cross-pair, Jack 25 Nov. No new entry while this pair's lagged
# ATR/price is below PEG_X x the 28-pair MEDIAN that day. X = 0.33 is DECIDED,
# picked off the STAGE3.md curve on 25 Nov 2026. None turns it off.
PEG_X = 0.33
# THE QUIET-ENTRY RULE, item 2 of 25 Nov. None is OFF and is the default: it
# is UNDER TEST, not adopted. Set it only from a caller that reports Q.
QUIET_Q = None
# 2000, AND BOTH SMALLER VALUES WERE TRIED AND FAILED. At 50 ATR two AUDJPY
# long trades held 345 bars reached the stop -- the 2008 collapse is that large
# in ATR units. At 200 a single EURCHF baseline trade reached it, which is the
# 2015 SNB de-peg. At 2000 there is not one risk-plan exit across 28 pairs,
# both sides, both families and all three settings. The assertion in run_one
# catches any case where it is still not enough, so this is a measured constant
# and not a hopeful one. R is invariant to it by construction, because R_gross
# rescales by atr_mult -- checked, not assumed.
BIG_STOP = 2000.0
TP_NONE = 900.0
BIG = 10 ** 9
SETTINGS = ('half', 'default', 'double')
# ITEM 4 — THREE PLANS, DECLARED IN ADVANCE. This is a two-plan comparison,
# not a sweep: both go in the candidate ledger and no engine default is changed.
#
#   flip_only  no risk plan at all: enter on the signal, exit on its opposite.
#   jack       THE MAIN VERSION. Jack's values: stop 1.0 ATR, first target 1.5x
#              the stop, baseline distance 1.5 ATR, one-candle rule off.
#   textbook   canonical NNFX: stop 1.5 ATR, half off at 1.0 ATR (so tp_mult is
#              1.0/1.5 of the stop), baseline distance 1.0 ATR, one-candle on.
#
# BOTH PLANS ARE SCORED IN THE SAME UNIT, R per 1.5 ATR, so their numbers are
# directly comparable even though their stops differ.
#
# THE BASELINE-DISTANCE SETTING IS INERT IN STAGE 1 and the report says so. In
# the C1-alone runs the baseline is placed far from price on purpose, so
# |close - baseline| never binds; in the baseline-alone runs the entry IS the
# cross, where |close - baseline| is about zero. It is carried here so the plans
# are declared in full, not because stage 1 tests it.
VARIANTS = ('flip_only', 'jack', 'textbook')
PLANS = {
    'flip_only': dict(atr_mult=None, tp_mult=TP_NONE, max_atr_dist=float(BIG),
                      one_candle_rule=False, be_pct=0.05,
                      trail_start_mult=float(BIG), trail_mult=float(BIG)),
    'jack':      dict(atr_mult=1.0, tp_mult=1.5, max_atr_dist=1.5,
                      one_candle_rule=False, be_pct=0.05,
                      trail_start_mult=2.0, trail_mult=1.5),
    'textbook':  dict(atr_mult=1.5, tp_mult=1.0 / 1.5, max_atr_dist=1.0,
                      one_candle_rule=True, be_pct=0.05,
                      trail_start_mult=2.0, trail_mult=1.5),
}
# ITEM 5 — a FIXED setting needs no tuning, so every trade year from 2005 is
# unseen for it. The walk-forward-picked version still reports 2010-2015,
# because its first step cannot trade before 2010.
FIXED_YEARS = tuple(range(2005, 2016))
# the walk: eleven steps, tune 4 / grade 1 / trade 1
STEPS = [dict(name='%d-%d' % (y, y + 3), tune=(y, y + 3), grade=y + 4,
              trade=y + 5) for y in range(2005, 2016)]
BUILD_YEARS = tuple(range(2010, 2016))     # reported
CONFIRM_YEARS = tuple(range(2016, 2021))   # computed, stored, NOT reported
FLOAT_SHORTER_IS_BIGGER = {
    'ehlers_reverse_ema_signals': ('alpha',),
    'kalman_filter_signals': ('sharpness', 'k'),
    'laguerre_filter_signals': ('alpha',),
    'mama_fama_signals': ('fast_limit', 'slow_limit'),
    'parabolic_sar_signals': ('sar_start', 'sar_increment'),
}


def families():
    o = S.mode_opts(S.slot_options(), 'A')
    return list(o['c1']), list(o['base']), list(o['c2']), list(o['vol']), list(o['exit_ind'])


def length_params(name):
    """-> {param: default} for the knobs that scale this indicator's memory."""
    f = getattr(L, name, None)
    if f is None:
        return {}
    if name in FLOAT_SHORTER_IS_BIGGER:
        sig = inspect.signature(f)
        return {k: sig.parameters[k].default for k in FLOAT_SHORTER_IS_BIGGER[name]
                if k in sig.parameters}
    sig = inspect.signature(f)
    for k, v in sig.parameters.items():
        if v.default is not inspect._empty and isinstance(v.default, int) \
                and not isinstance(v.default, bool) and v.default >= 2:
            return {k: v.default}
    return {}


def setting_params(name, which):
    """The parameter override for one setting. {} means Pine defaults."""
    lp = length_params(name)
    if not lp or which == 'default':
        return {}
    out = {}
    inv = name in FLOAT_SHORTER_IS_BIGGER
    for k, v in lp.items():
        if inv:
            out[k] = float(v * 2.0) if which == 'half' else float(v / 2.0)
        else:
            out[k] = max(2, int(round(v / 2))) if which == 'half' else int(v * 2)
    return out


def setting_is_distinct(name, which):
    """False when half collapses onto default, as for a default length of 2."""
    if which == 'default':
        return True
    return setting_params(name, which) != {} and \
        setting_params(name, which) != {k: v for k, v in length_params(name).items()}


_PAIR = {}


def pair_data(p):
    if p not in _PAIR:
        _PAIR[p] = S.load_pair(p)
    return _PAIR[p]


def _neutralise(A, kind, side=None, pair_for_floor=None):
    """Force every slot but the one under test to pass. See the module note.

    A CORRECTION TO MY OWN FIRST READING. I took the C1-flip route to be
    independent of the baseline because `l2engine.py:462` reads
    `r2l = use_c1_flip and c1_lt[i] and agree_long`. It is not: `agree_long`
    itself is `c1_lc[i] and c2_lc[i] and v_ok_l[i] and side == 1`
    (l2engine.py:441), so the baseline SIDE is inside the agreement. Setting
    the baseline equal to the close makes `side` 0 and blocks every entry --
    the first smoke took 0 trades, which is how this was caught.

    So "C1 alone" is run ONE DIRECTION AT A TIME, with the baseline placed far
    below the close for the long side (side == 1 on every bar) and far above it
    for the short side (side == -1), and the two trade sets concatenated. The
    EXIT needs neither side nor agreement -- `exit_on_c1_flip and c1_st[i]`
    (l2engine.py:414) -- so each one-sided run still exits on the opposite
    flip, which is what the rule says.
    """
    n = A['c'].size
    T = np.ones(n, bool)
    A['c2_lc'] = T.copy(); A['c2_sc'] = T.copy()
    # THE VOLATILITY FLOOR, Jack's decided rule 1, standing from 24 Nov. It
    # rides the VOLUME SLOT: v_ok_l/v_ok_s appear only in l2engine's entry
    # conditions, so no entry is taken while the pair's own ATR is in its
    # bottom LOWVOL_Q and exits are untouched. LOWVOL_Q = None restores the
    # pre-24-Nov behaviour and every output records which was used.
    vok = T.copy()
    if pair_for_floor and (LOWVOL_Q or PEG_X or QUIET_Q is not None):
        import nnfxvol as _V
        if QUIET_Q is not None and float(QUIET_Q) < 1.0:
            # THE QUIET-ENTRY RULE, item 2 of 25 Nov. Same slot, same
            # entry-only discipline as the floor; the opposite end of the same
            # axis. None and 1.0 both mean off and give the identical book.
            _ix3, _qt = _V.quiet_mask(pair_for_floor, float(QUIET_Q))
            assert len(_qt) == n, '%s: quiet mask %d vs %d bars' % (
                pair_for_floor, len(_qt), n)
            vok = vok & (~_qt)
        if LOWVOL_Q:
            _ix, _lv = _V.lowvol_mask(pair_for_floor, q=LOWVOL_Q, causal=True)
            assert len(_lv) == n, '%s: lowvol mask %d vs %d bars' % (
                pair_for_floor, len(_lv), n)
            vok = vok & (~_lv)
        if PEG_X:
            _ix2, _pg = _V.peg_mask(pair_for_floor, x=PEG_X)
            assert len(_pg) == n, '%s: peg mask %d vs %d bars' % (
                pair_for_floor, len(_pg), n)
            vok = vok & (~_pg)
    A['v_ok_l'] = vok.copy(); A['v_ok_s'] = vok.copy()
    A['x_el'] = np.zeros(n, bool); A['x_es'] = np.zeros(n, bool)
    if kind == 'c1':
        K = 10.0 * float(np.nanmax(np.abs(A['c'])) + 1.0)
        A['bl'] = A['c'] - K if side == 'long' else A['c'] + K
    return A


def run_one(name, kind, setting, variant, pairs=None, atr_len=14,
            use_hourly=False, amb_out=None):
    """One indicator, one setting, one variant, across the pairs. -> trade frame.

    kind 'c1'   enter on the indicator's flip, exit on the opposite flip
    kind 'base' enter when the close crosses the baseline, exit on the cross back
    """
    C1L, BASEL, C2L, VOLL, XL = families()
    pairs = pairs or S.all_pairs()
    prm = setting_params(name, setting)
    PL = PLANS[variant]
    if variant == 'flip_only':
        # NO TARGET, AND NO BREAKEVEN OR TRAIL EITHER. With tp_mult >= 900 the
        # engine seeds its phase machine at ENTRY rather than at a TP1 that
        # never comes (l2engine.py:555), so the breakeven and trail rules are
        # live from the first bar. The first smoke tripped the assertion below
        # on 2 of adx_dmi's trades for exactly that reason.
        #
        # AND be_pct MUST STAY SMALL, WHICH IS THE OPPOSITE OF WHAT IT LOOKS
        # LIKE. Raising it to 1e9 to "disable" the breakeven made things far
        # worse -- 134 breakeven stops per pair on the SHORT side alone. The
        # reason is the sentinel: for a short, l1_tp = entry - 900 x stop, which
        # is hugely NEGATIVE, so the trigger `l[i] <= l1_tp * (1 - be_pct/100)`
        # (l2engine.py:379) multiplies a negative by a large negative and
        # becomes hugely POSITIVE -- satisfied on the first bar. At be_pct 0.05
        # the product stays negative and the breakeven can never fire. The
        # trail is disabled the straightforward way, by never arming it.
        am, tp, plan = BIG_STOP, TP_NONE, 2
    else:
        am, tp, plan = float(PL['atr_mult']), float(PL['tp_mult']), 2
    # THE BASELINE-DISTANCE FILTER CANNOT BE APPLIED TO AN ARTIFICIAL BASELINE.
    # In the C1-alone runs the baseline is deliberately placed far from price so
    # that `side` is fixed, which means |close - baseline| is enormous and ANY
    # finite max_atr_dist rejects every entry. The first run of the jack plan
    # produced zero trades for exactly that reason. So the C1 runs keep the
    # filter disabled and the report states that the declared distance is inert
    # there; the baseline-alone runs use the plan's value, where the entry is
    # the cross itself and the distance is about zero anyway.
    _dist = float(BIG) if kind == 'c1' else float(PL['max_atr_dist'])
    kw = dict(use_continuation=False,
              one_candle_rule=bool(PL['one_candle_rule']),
              max_atr_dist=_dist, bridge_bars=BIG,
              block_suspect=True, bridge_all_routes=True,
              plan=plan, atr_mult=am, tp_mult=tp,
              trail_mult=float(PL['trail_mult']),
              trail_start_mult=float(PL['trail_start_mult']),
              be_pct=float(PL['be_pct']))
    if kind == 'c1':
        c1, base = name, BASEL[0]
        kw.update(use_base_cross=False, use_c1_flip=True,
                  exit_on_c1_flip=True, exit_on_base_cross=False,
                  exit_on_exit_ind=False)
    else:
        c1, base = C1L[0], name
        kw.update(use_base_cross=True, use_c1_flip=False,
                  exit_on_c1_flip=False, exit_on_base_cross=True,
                  exit_on_exit_ind=False)
    rows = []
    sides = ('long', 'short') if kind == 'c1' else (None,)
    for p in pairs:
        d = pair_data(p)
        params = {'atr_len': atr_len}
        if prm:
            params[name] = prm
        for sd in sides:
            A = E.prepare(d, c1, C2L[0], VOLL[0], base, XL[0], params=params)
            A = _neutralise(A, kind, sd, pair_for_floor=p)
            if kind == 'base':
            # the baseline is under test, so the C1 agreement must not block
                A['c1_lt'] = np.ones(A['c'].size, bool)
                A['c1_st'] = np.ones(A['c'].size, bool)
                A['c1_lc'] = np.ones(A['c'].size, bool)
                A['c1_sc'] = np.ones(A['c'].size, bool)
            if use_hourly:
                import nnfxamb as _AMB
                _a = _AMB.amb_args(p)
                res = E.run(A, amb=_a, **kw)
                if amb_out is not None:
                    amb_out += np.asarray(res.get('_amb', np.zeros(3, np.int64)))
            else:
                res = E.run(A, **kw)
            tf = E.trade_frame(res, d)
            if tf is None or not len(tf):
                continue
            tf = tf.copy(); tf['pair'] = p; tf['side_run'] = sd or 'both'
            if sd == 'long':
                tf = tf[tf.direction == 'long']
            elif sd == 'short':
                tf = tf[tf.direction == 'short']
            if len(tf):
                rows.append(tf)
    if not rows:
        return pd.DataFrame()
    T = pd.concat(rows, ignore_index=True)
    # restate R against the 1.5 ATR risk unit (see the module note)
    T['R_gross'] = T.R.astype(float) * am / RISK_UNIT_ATR
    T['atr_mult_used'] = am
    # EVERY FRAME DECLARES THE RULES IT RAN UNDER
    T['lowvol_q'] = (LOWVOL_Q if LOWVOL_Q else 0.0)
    T['peg_x'] = (PEG_X if PEG_X else 0.0)
    T['quiet_q'] = (float(QUIET_Q) if QUIET_Q is not None else 1.0)
    import nnfxamb as _AMB2
    T['gapfill_on'] = int(bool(use_hourly and _AMB2.GAPFILL_STANDING))
    if variant == 'flip_only':
        # 'nothing else' is CHECKED, not assumed: a 50 ATR stop must
        # never be reached, and with tp_mult 900 there is no target
        bad = T[T.reason.isin(['stop', 'target', 'breakeven stop',
                               'trail stop'])]
        assert not len(bad), (
            'flip_only took %d risk-plan exits on %s/%s -- the stop or '
            'target is binding and the variant is not flip-only'
            % (len(bad), name, setting))
    return T


def _cost_R(T, era_table=None):
    """Cost of each trade in the SAME 1.5 ATR unit R is expressed in.

    THE FIRST VERSION CHARGED NO COST ON THE NO-STOP VARIANT, which is item 3.
    The engine books cost in RAW r units as f x |px| x |units| / RISK, and
    R_gross restates raw r as r x atr_mult / 1.5. The cost has to be restated
    by the SAME factor or the two are in different units. Missing the
    x atr_mult made the charge 2000x too small on flip_only (atr_mult 2000),
    which is why R_gross_build and R_net_build were equal to five decimals.

    THE DECLARED NOTIONAL. Because units ~ 1 / (atr_mult x ATR), the raw cost is
    proportional to 1/atr_mult and multiplying by atr_mult cancels it exactly.
    So the cost per trade in this unit is INDEPENDENT of the sentinel stop size
    -- which is the whole point of declaring the notional as 1.5 ATR: the
    no-stop and the stop variants are charged the same real spread.
    """
    if era_table:
        S.load_costs(era_table)
    if not S.COSTS:
        return np.zeros(len(T))
    f = T.pair.map(S.COSTS).to_numpy(float)
    am = T.atr_mult_used.to_numpy(float) if 'atr_mult_used' in T.columns \
        else np.ones(len(T))
    return (f * np.abs(T.entry_px.to_numpy(float))
            * np.abs(T.units.to_numpy(float)) / S.RISK) * am / RISK_UNIT_ATR


def daily_series(T, cost):
    """THE DAILY MARK-TO-MARKET SERIES, netted across pairs, in 1.5 ATR units.

    Item 3: the worst dip must be the TRUE CHRONOLOGICAL drawdown, not the
    worst of six yearly sums. The first version took the dip from the yearly
    totals, which is why it equalled minus the worst year on 56 of 117 rows and
    was exactly 0 on four more -- with six points a "drawdown" is usually just
    the single worst year.

    THE CONVENTION IS GATE 2's, which item 8 adopts for the staged build:
        on the exit bar      cum = R
        on any earlier bar   cum = dir x (close[b] - entry) x units / RISK
        increment(b)         = cum(b) - cum(b-1), less the entry cost on the
                               entry bar
    Summing a trade's increments reproduces its R exactly, so splitting them by
    the bar's own day cannot move value across a day or a year boundary.
    """
    if not len(T):
        return pd.DataFrame(columns=['date', 'R'])
    acc = {}
    cost = np.asarray(cost, float)
    # ---- THE LEG WEIGHT. FOUND 24 NOV, 22:10, CHECKING JACK'S 54.9 R DIP.
    # `units` is the FULL position size and is written IDENTICALLY on every leg
    # of a plan=2 entry, while each leg's realised R is half -- a full stop-out
    # is -0.5 + -0.5 = -1.0. So a per-leg mark built from `units` overstates
    # open mark-to-market by the number of legs. VERIFIED on 642 stop exits:
    # dir * (units / n_legs) * (exit_px - entry_px) / RISK reproduces the leg's
    # R to EXACTLY 0.000000, and full `units` is out by exactly 2x.
    #
    # WHY NOTHING CAUGHT IT. The error cancels at the exit bar: the exit term
    # is `R - prev` and `prev` carries the same 2x, so every TOTAL is exact and
    # the yearly sums reconcile to the last decimal. Only the PATH is wrong.
    # On ichimoku+sma full_nnfx (jack) the 15 Jan 2015 SNB day showed +99.23 R
    # where the truth is +49.6, and the next day -50.22 where the truth is
    # -0.36 -- a one-day spike of 49.6 R that invented a peak, and a 54.93 R
    # "drawdown" measured down from it. Guard 33 caught this same fault class
    # in the TRADE COUNTS and did not look at the daily series; guard 36 does.
    #
    # THE DIVISOR IS THE PLAN'S LEG COUNT, NOT THE COUNT IN THIS FRAME. A leg
    # count taken per entry would be wrong on a frame filtered by exit year,
    # where leg1 can exit in December and leg2 in January and one of the two is
    # severed -- each surviving leg still carries units/2. The distinct `leg`
    # labels are a property of the plan (all three plans are two-leg) and
    # survive any row filter.
    nleg = float(max(1, T['leg'].astype(str).nunique())) \
        if 'leg' in T.columns else 1.0
    for p, g in T.groupby('pair'):
        d = pair_data(p)
        cl = d['close'].values.astype(float)
        idx = pd.DatetimeIndex(d.index)
        n = len(cl)
        eb = idx.get_indexer(pd.DatetimeIndex(g.entry_date))
        xb = idx.get_indexer(pd.DatetimeIndex(g.exit_date))
        dirv = np.where(g.direction.to_numpy() == 'long', 1.0, -1.0)
        un = g.units.to_numpy(float)
        epx = g.entry_px.to_numpy(float)
        rr = g.R_gross.to_numpy(float)
        am = (g.atr_mult_used.to_numpy(float) if 'atr_mult_used' in g.columns
              else np.ones(len(g)))
        cst = cost[g.index.to_numpy()]
        ok = (eb >= 0) & (xb >= eb) & (xb < n)
        eb, xb, dirv, un, epx, rr, am, cst = (v[ok] for v in
                                              (eb, xb, dirv, un, epx, rr, am, cst))
        if not len(eb):
            continue
        # R per unit of price, PER LEG (units is the whole position: see nleg)
        k = dirv * (un / nleg) / S.RISK * am / RISK_UNIT_ATR
        inc = np.zeros(n)
        # ---- THE MIDDLE BARS, as a difference array.
        # For e < b < x the increment is k_j x (cl[b] - cl[b-1]) -- a plain
        # close-to-close difference, because cum(b) is linear in cl[b] there.
        # So instead of walking each trade's bars, accumulate the WEIGHT k_j
        # over every bar each trade covers (+k at e+1, -k at x) and multiply the
        # cumulative weight by the price difference once. O(trades + bars)
        # rather than O(sum of holding periods), which is what made the first
        # version too slow to run flip_only at all.
        # A SAME-BAR TRADE HAS NO MIDDLE BARS and must not enter the
        # difference array at all: with xb == eb the +k lands at eb+1 and the
        # -k at eb, leaving a spurious -k weight on the entry bar. That put a
        # constant 0.946 R error into both variants until it was masked out.
        # Such trades are fully described by their entry and exit terms below.
        mid = xb > eb
        w = np.zeros(n + 2)
        np.add.at(w, np.minimum(eb[mid] + 1, n), k[mid])
        np.add.at(w, np.minimum(xb[mid], n), -k[mid])
        wc = np.cumsum(w[:n])
        dcl = np.zeros(n)
        dcl[1:] = cl[1:] - cl[:-1]
        inc += wc * dcl
        # ---- the entry bar: cum(e) - 0, less the cost. Entries fill at the
        # close so cl[e] == entry_px and this is just the cost.
        np.add.at(inc, eb, k * (cl[eb] - epx) - cst)
        # ---- the exit bar: R - cum(x-1)
        prev = np.where(xb - 1 >= eb, k * (cl[np.maximum(xb - 1, 0)] - epx), 0.0)
        np.add.at(inc, xb, rr - prev)
        nz = np.flatnonzero(inc != 0.0)
        for b in nz:
            kk = idx[b]
            acc[kk] = acc.get(kk, 0.0) + float(inc[b])
    ks = sorted(acc.keys())
    return pd.DataFrame(dict(date=pd.DatetimeIndex(ks),
                             R=[acc[k] for k in ks]))


def true_dip(DS, years=None):
    """True chronological max drawdown in R on the daily series."""
    if not len(DS):
        return np.nan
    d = DS
    if years is not None:
        d = d[pd.DatetimeIndex(d.date).year.isin(list(years))]
    if not len(d):
        return np.nan
    eq = np.cumsum(d.R.to_numpy(float))
    return float((np.maximum.accumulate(eq) - eq).max())


def entry_frame(T):
    """ONE ROW PER ENTRY, NOT PER LEG. Item 8's "distinct-trade count for n".

    THE FAULT THIS FIXES, FOUND 24 NOV WHILE TESTING STAGE 2's 2e.
    `plan=2` splits every position into TWO legs -- leg1 banks at the first
    target, leg2 runs on the trail -- and `E.trade_frame` returns one row per
    LEG. Verified on EURUSD and GBPJPY across all three plans: rows are exactly
    2x distinct entries, every time, min and max legs per entry both 2.

    The TOTALS were never wrong. Each leg carries half the units against the
    full risk, so the two legs' R sums to the position's R (a full stop-out is
    -0.5 + -0.5 = -1.0 R) and each leg is charged half the spread, summing to
    the whole. So R_net_build, R_gross_build, worst_dip_R, both t statistics,
    null_p and R_net_per_year were all correct and are unchanged by this fix.

    What WAS wrong is every per-trade and count column:
        n_entered, n_touching, trades_per_year   2x too large
        R_net_per_trade, R_gross_per_trade,      half the truth
        cost_per_trade
    and item 8 said in as many words to adopt the count of DISTINCT trades. A
    leg is not a distinct trade. Guard 32 checked that the two conventions were
    NAMED apart and never that the count counted the right thing, which is why
    this survived to be found by a sweep that happened to halve at a one-day
    gap -- exactly 0.500000 of trades dropped, which is too round to be real.

    THE POSITION's HOLDING PERIOD IS ITS LAST LEG's. The position is open until
    leg2 closes, so mean_bars takes the MAX over the legs of an entry and not
    their mean.
    """
    k = ['pair', 'entry_date', 'direction'] if 'pair' in T.columns \
        else ['entry_date', 'direction']
    g = T.groupby(k, as_index=False).agg(
        entry_date_=('entry_date', 'first'), exit_date=('exit_date', 'max'),
        bars_held=('bars_held', 'max'), n_legs=('R_gross', 'size'))
    g = g.drop(columns=['entry_date_'])
    return g


def n_entries(T):
    """The number of DISTINCT trades in a leg-level frame."""
    if not len(T):
        return 0
    k = ['pair', 'entry_date', 'direction'] if 'pair' in T.columns \
        else ['entry_date', 'direction']
    return int(len(T.groupby(k)))


def _yearly(T, cost, DS=None):
    """Per calendar year, BY YEAR-END MARK TO MARKET (item 8).

    R_mtm comes from the daily series, so a trade open across New Year scores
    in both years and the yearly figures sum to total R exactly -- verified at
    4e-13. The TRADE COUNT is kept separately and named differently, because
    the two mean different things and 0b showed what conflating them costs:

        n_entered   distinct trades whose ENTRY bar fell in the year. Sums to
                    the true number of trades. This is gate 3's convention and
                    item 8 adopts it for counts.
        n_touching  trades open at any point in the year. Over-counts a
                    straddling trade, which is gate 2's convention for n.
    """
    if not len(T):
        return pd.DataFrame()
    cost = np.asarray(cost, float)
    if DS is None:
        DS = daily_series(T, cost)
    ed = pd.DatetimeIndex(T.entry_date); xd = pd.DatetimeIndex(T.exit_date)
    g = (DS.assign(year=pd.DatetimeIndex(DS.date).year)
           .groupby('year', as_index=False).agg(R_mtm=('R', 'sum'),
                                                days=('R', 'size')))
    # COUNTS AND HOLDING PERIODS COME FROM ENTRIES; R AND COST FROM LEGS.
    # See entry_frame: a leg is not a trade, but the two legs' R and cost sum to
    # the position's, so the sums must stay at leg level and only the counts
    # move to entry level.
    EF = entry_frame(T)
    ent_cnt = (pd.DataFrame(dict(year=pd.DatetimeIndex(EF.entry_date).year,
                                bars=EF.bars_held.to_numpy(float)))
                 .groupby('year', as_index=False)
                 .agg(n_entered=('bars', 'size'), mean_bars=('bars', 'mean')))
    ent_sum = (pd.DataFrame(dict(year=ed.year,
                                gross=T.R_gross.to_numpy(float), cost=cost))
                 .groupby('year', as_index=False)
                 .agg(R_gross_entered=('gross', 'sum'),
                      cost_entered=('cost', 'sum')))
    ent = ent_cnt.merge(ent_sum, on='year', how='outer')
    touch = []
    for y0, y1 in zip(pd.DatetimeIndex(EF.entry_date).year,
                      pd.DatetimeIndex(EF.exit_date).year):
        for y in range(int(y0), int(y1) + 1):
            touch.append(y)
    tc = (pd.Series(touch).value_counts().rename_axis('year')
            .reset_index(name='n_touching') if touch
          else pd.DataFrame(columns=['year', 'n_touching']))
    out = g.merge(ent, on='year', how='outer').merge(tc, on='year', how='outer')
    out = out.sort_values('year').reset_index(drop=True)
    out['straddles'] = int((pd.DatetimeIndex(EF.entry_date).year
                            != pd.DatetimeIndex(EF.exit_date).year).sum())
    out['n_legs'] = int(len(T))
    # R_net is the MTM figure; it is already net of cost (charged on entry day)
    out['R_net'] = out.R_mtm
    out['R_gross'] = out.R_mtm + out.cost_entered.fillna(0.0)
    out['n'] = out.n_entered
    return out


def _null_match(T, cost, ndraw=200, seed=7, years=None):
    """SCOPE MATTERS, AND GETTING IT WRONG COST ME A FALSE FAULT.

    The first version of this ran over the WHOLE span 2005-2020 while the
    summary divided its total by the BUILD-years trade count. The spans differ
    by a factor of 2.607 (6,408 trades against 2,458), so every per-trade null
    figure came out 2.6x too large and, because the total is dominated by the
    cost subtraction, 2.6x too NEGATIVE: -0.0221 R per trade gross instead of
    -0.0008. I reported that as a bias in the apparatus and it was a bias in my
    own arithmetic. The same mismatch made every null_p meaningless, because a
    six-year real total was being compared against a sixteen-year null total.

    `years` now restricts the null to the same window as the real figure it is
    compared against, and the per-draw trade count is returned so no caller has
    to guess it.

    AND THE COST IT CHARGES IS RETURNED TOO, for the same reason. `null_R` is
    NET: the loop subtracts `cmean * len(r)` per pair. Restating it gross
    needs that exact figure, and on 25 Nov condition 4 was reconstructing it
    from the SUMMARY's `cost_per_trade` instead -- a per-ENTRY cost over
    entry-year trades set against a per-LEG net over exit-year legs. Two
    mismatches at once: the leg/entry factor of 2 made every two-leg label
    fail by a near-identical +0.016 (half the 0.032 charged) while both
    one-leg flip_only labels passed, and the entry-year/exit-year difference
    put the populations as far apart as 0.41 to 1 on a long-held flip_only
    setting. Returning the charged cost removes the reconstruction entirely.
    """ 
    """Random-entry null MATCHED on trade count and holding period, per pair.

    For each draw and each pair, draw as many entry bars as the real strategy
    took in that pair, give each the SAME holding period as a real trade, and
    book the move over that window in the same 1.5 ATR units. Direction is
    drawn with the real long/short split, so only the TIMING is random.
    """
    if years is not None:
        xd = pd.DatetimeIndex(T.exit_date)
        m = xd.year.isin(list(years))
        T = T[m]
        cost = np.asarray(cost)[np.asarray(m)]
    if not len(T):
        return (np.array([]), np.array([]), np.zeros((0, 0)),
                np.array([]))
    T = T.reset_index(drop=True)
    cost = np.asarray(cost)
    rng = np.random.default_rng(seed)
    out = np.zeros(ndraw)
    ntr = np.zeros(ndraw)
    chg = np.zeros(ndraw)
    yrs_list = sorted(years) if years is not None else []
    ymat = np.zeros((ndraw, max(1, len(yrs_list))))
    per_pair = {}
    for p, g in T.groupby('pair'):
        d = pair_data(p)
        cl = d['close'].values.astype(float)
        atr = L.P.atr(d['high'].values.astype(float),
                      d['low'].values.astype(float), cl, 14)
        idx = pd.DatetimeIndex(d.index)
        ent = idx.get_indexer(pd.DatetimeIndex(g.entry_date))
        hold = g.bars_held.to_numpy(int)
        dirs = np.where(g.direction.to_numpy() == 'long', 1.0, -1.0)
        per_pair[p] = (cl, atr, ent, hold, dirs,
                       float(cost[g.index.to_numpy()].mean()) if len(cost) else 0.0,
                       pd.DatetimeIndex(d.index).year.to_numpy())
    for k in range(ndraw):
        tot = 0.0
        nn = 0
        cc = 0.0
        for p, (cl, atr, ent, hold, dirs, cmean, yr_of_bar) in per_pair.items():
            n = len(ent)
            lo, hi = int(np.nanmin(ent)), int(np.nanmax(ent))
            if hi <= lo:
                continue
            e = rng.integers(lo, hi, size=n)
            h = rng.permutation(hold)
            x = np.minimum(e + h, len(cl) - 1)
            dv = rng.permutation(dirs)
            a = atr[e]
            with np.errstate(divide='ignore', invalid='ignore'):
                r = dv * (cl[x] - cl[e]) / (RISK_UNIT_ATR * a)
            r = r[np.isfinite(r)]
            tot += float(r.sum()) - cmean * len(r)
            nn += len(r)
            cc += cmean * len(r)
            # ITEM 6: the null's PER-YEAR vector, so a luck floor can be
            # computed in the units of the statistic (a yearly t) instead of
            # in R, which is what the first version wrongly did.
            if yrs_list:
                xv = np.minimum(e + h, len(cl) - 1)
                ry = yr_of_bar[xv][np.isfinite(dv * (cl[xv] - cl[e]))]
                rv = r
                for yi, yy in enumerate(yrs_list):
                    mm = (ry[:len(rv)] == yy)
                    if mm.any():
                        ymat[k, yi] += float(rv[:len(mm)][mm].sum()) \
                            - cmean * int(mm.sum())
        out[k] = tot
        ntr[k] = nn
        chg[k] = cc
    return out, ntr, ymat, chg


def _block_t(x, block=20, ndraw=2000, seed=13):
    """ITEM 6 — BLOCK-BOOTSTRAP t ON THE DAILY MARK-TO-MARKET SERIES.

    The yearly t is kept because it is honest about how few independent
    observations six or eleven years really are. But it throws away almost all
    the data, and 0a measured what that costs: on six yearly values even a
    pre-declared candidate tested alone is blind below 0.20 R per trade.

    A daily series has thousands of points and is serially correlated, so an
    iid t on it would be wildly overconfident. A MOVING-BLOCK BOOTSTRAP in
    20-day blocks keeps the autocorrelation inside a block and resamples blocks
    independently, which is the standard fix. t = observed mean divided by the
    bootstrap standard deviation of the mean.

    The same statistic is put through 0a in nnfx0.stage_power_boot, so what it
    can and cannot detect is measured rather than assumed.
    """
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    n = len(x)
    if n < 2 * block:
        return np.nan, np.nan
    rng = np.random.default_rng(seed)
    nb = int(np.ceil(n / block))
    starts = rng.integers(0, n - block + 1, size=(ndraw, nb))
    means = np.empty(ndraw)
    for i in range(ndraw):
        idx = (starts[i][:, None] + np.arange(block)[None, :]).ravel()[:n]
        means[i] = x[idx].mean()
    sd = float(means.std(ddof=1))
    obs = float(x.mean())
    return (obs / sd if sd > 0 else np.nan), sd


def empirical_floor(null_by_cand, m, alpha=0.05, nboot=4000, seed=17):
    """ITEM 6 — THE LUCK FLOOR FROM THE RANDOM-ENTRY NULL, NOT A FORMULA.

    `null_by_cand` maps a candidate to its array of null statistic values. A
    best-of-m floor is the (1-alpha) quantile of the MAXIMUM over m candidates,
    built by drawing one null value per candidate and taking the max, many
    times. That uses the null's own shape and its own cross-candidate
    dependence instead of assuming a t-distribution -- which matters here,
    because 0a showed the analytic floors on five degrees of freedom are
    brutal and the empirical ones need not be.
    """
    keys = [k for k, v in null_by_cand.items()
            if v is not None and len(np.asarray(v)) and
            np.isfinite(np.asarray(v, float)).any()]
    if not keys:
        return np.nan
    rng = np.random.default_rng(seed)
    cols = [np.asarray(null_by_cand[k], float) for k in keys]
    cols = [c[np.isfinite(c)] for c in cols]
    cols = [c for c in cols if len(c)]
    if not cols:
        return np.nan
    m = max(1, min(int(m), len(cols)))
    mx = np.empty(nboot)
    for i in range(nboot):
        pick = rng.choice(len(cols), size=m, replace=False)
        mx[i] = max(float(rng.choice(cols[j])) for j in pick)
    return float(np.quantile(mx, 1.0 - alpha))


def analytic_floor(m, span):
    """max-of-m t floor on yearly values, family-wise alpha 0.05."""
    a = 1.0 - 0.95 ** (1.0 / max(1, m))
    return float(stats.t.ppf(1.0 - a, max(1, span - 1)))


def stage_run(kind='c1', variant='jack', names=None, nmax=None,
              ndraw=400, era_table=None, use_hourly=True, nboot=2000,
              tag_extra='', outdir=None):
    """1a / 1b — every indicator of a family, every setting, one risk plan.

    ITEM 5: the three FIXED settings are reported over EVERY trade year from
    2005 to 2015 as unseen, because a fixed setting needs no tuning window.
    2016-2020 is computed and stored in the yearly file and never summarised.
    """
    C1L, BASEL, _c2, _v, _x = families()
    pool = (C1L if kind == 'c1' else BASEL)
    names = names or pool
    if nmax:
        names = names[:nmax]
    S.load_costs(era_table) if era_table else S.load_costs()
    yr_rows, sum_rows, null_rows = [], [], []
    amb = np.zeros(3, np.int64)
    t0 = time.time()
    null_stat = {}
    for ii, nm in enumerate(names, 1):
        for st in SETTINGS:
            T = run_one(nm, kind, st, variant, use_hourly=use_hourly,
                        amb_out=amb)
            if not len(T):
                sum_rows.append(dict(kind=kind, variant=variant, indicator=nm,
                                     setting=st, n=0, note='no trades'))
                continue
            T = T.reset_index(drop=True)
            cost = _cost_R(T)
            DS = daily_series(T, cost)
            Y = _yearly(T, cost, DS)
            Y['indicator'] = nm; Y['setting'] = st
            Y['kind'] = kind; Y['variant'] = variant
            Y['distinct_setting'] = int(setting_is_distinct(nm, st))
            yr_rows.append(Y)
            yrs = FIXED_YEARS
            b = Y[Y.year.isin(yrs)]
            ds = DS[pd.DatetimeIndex(DS.date).year.isin(list(yrs))]
            real = float(b.R_net.sum())
            nulls, nulls_n, nymat, nulls_c = _null_match(
                T, cost, ndraw=ndraw, years=yrs)
            p = float((nulls >= real).mean()) if len(nulls) else np.nan
            ys = b.sort_values('year').R_net.to_numpy(float)
            t_yr = (float(ys.mean() * np.sqrt(len(ys)) / ys.std(ddof=1))
                    if len(ys) > 1 and ys.std(ddof=1) > 0 else np.nan)
            t_bs, bs_sd = _block_t(ds.R.to_numpy(float), ndraw=nboot)
            # the null's YEARLY t, one value per draw -- the same statistic the
            # candidate is judged by, so the floor is in the right units
            if nymat.shape[0] and nymat.shape[1] > 1:
                mu = nymat.mean(axis=1)
                sg = nymat.std(axis=1, ddof=1)
                with np.errstate(divide='ignore', invalid='ignore'):
                    nt_y = np.where(sg > 0, mu * np.sqrt(nymat.shape[1]) / sg,
                                    np.nan)
            else:
                nt_y = np.array([])
            null_stat[(nm, st)] = nt_y
            n_ent = float(b.n_entered.sum())
            sum_rows.append(dict(
                kind=kind, variant=variant, indicator=nm, setting=st,
                distinct_setting=int(setting_is_distinct(nm, st)),
                params=json.dumps(setting_params(nm, st)),
                years=int(len(b)), year_from=int(b.year.min()),
                year_to=int(b.year.max()),
                n_entered=n_ent, n_touching=float(b.n_touching.sum()),
                trades_per_year=float(b.n_entered.mean()),
                mean_bars=float((b.mean_bars * b.n_entered).sum()
                                / max(1.0, n_ent)),
                R_gross_build=float(b.R_gross.sum()), R_net_build=real,
                R_gross_per_trade=float(b.R_gross.sum() / max(1.0, n_ent)),
                R_net_per_trade=float(real / max(1.0, n_ent)),
                cost_per_trade=float(b.cost_entered.sum() / max(1.0, n_ent)),
                R_net_per_year=float(real / max(1, len(b))),
                years_positive=int((b.R_net > 0).sum()),
                worst_year=float(b.R_net.min()) if len(b) else np.nan,
                best_year=float(b.R_net.max()) if len(b) else np.nan,
                worst_dip_R=true_dip(DS, yrs),
                t_yearly=t_yr, t_block_boot=t_bs, boot_sd_of_mean=bs_sd,
                null_p=p, null_mean=float(np.mean(nulls)) if len(nulls) else np.nan,
                null_p95=float(np.percentile(nulls, 95)) if len(nulls) else np.nan,
                null_trades_per_draw=float(np.mean(nulls_n)) if len(nulls_n) else np.nan,
                straddles=int(b.straddles.max()) if len(b) else 0,
                amb_target_first=int(amb[0]), amb_stop_first=int(amb[1]),
                amb_unresolved=int(amb[2])))
            null_rows.append(pd.DataFrame(dict(
                kind=kind, variant=variant, indicator=nm, setting=st,
                draw=np.arange(1, len(nulls) + 1), null_R=nulls,
                null_n=nulls_n, null_cost=nulls_c)))
        if ii % 5 == 0 or ii == len(names):
            print('    %s/%s: %d of %d indicators, %.1f min'
                  % (kind, variant, ii, len(names), (time.time() - t0) / 60),
                  flush=True)
    Yall = pd.concat(yr_rows, ignore_index=True) if yr_rows else pd.DataFrame()
    Sall = pd.DataFrame(sum_rows)
    Nall = pd.concat(null_rows, ignore_index=True) if null_rows else pd.DataFrame()
    # ---- empirical luck floors from the null, per statistic
    if len(Sall) and null_stat:
        fl = empirical_floor(null_stat, len(pool))
        fa = empirical_floor(null_stat, 1)
        Sall['floor_emp_best_of_family'] = fl
        Sall['floor_emp_alone'] = fa
        yspan = int(Sall.years.max()) if 'years' in Sall.columns else 11
        Sall['floor_t_best_of_family'] = analytic_floor(len(pool), yspan)
        Sall['floor_t_alone'] = analytic_floor(1, yspan)
        Sall['clears_alone'] = (Sall.t_yearly >= Sall.floor_t_alone).astype(int)
        Sall['clears_best_of_family'] = (
            Sall.t_yearly >= Sall.floor_t_best_of_family).astype(int)
    # EVERY STAGE 1 FILE DECLARES THE STANDING RULES IT WAS RUN UNDER. The
    # floor curve sweeps LOWVOL_Q, so without this the six levels' files are
    # indistinguishable on disk and a reader cannot tell which is which.
    for _D in (Yall, Sall, Nall):
        if len(_D):
            _D['lowvol_q'] = (LOWVOL_Q if LOWVOL_Q else 0.0)
            _D['peg_x'] = (PEG_X if PEG_X else 0.0)
            _D['quiet_q'] = (float(QUIET_Q) if QUIET_Q is not None else 1.0)
            _D['leverage_cap_on'] = 1
    # A SWEEP'S FILES DO NOT BELONG IN results/nnfx. condition4_all globs
    # stage1r2_*_summary.csv there and treats each match as a label, so six
    # floor levels dropped beside the real ranking would mix six different
    # rules into one aggregate zero-edge verdict. A sweep passes outdir.
    _O = outdir or OUT
    os.makedirs(_O, exist_ok=True)
    tag = '%s_%s%s' % (kind, variant, tag_extra)
    f1 = os.path.join(_O, 'stage1r2_%s_yearly.csv' % tag)
    f2 = os.path.join(_O, 'stage1r2_%s_summary.csv' % tag)
    f3 = os.path.join(_O, 'stage1r2_%s_nulls.csv' % tag)
    Yall.to_csv(f1, index=False); Sall.to_csv(f2, index=False)
    Nall.to_csv(f3, index=False)
    print('  stage 1 R2 [%s]: %d indicators x %d settings -> %d yearly rows, '
          '%d summary rows. Ambiguous bars: target-first %d, stop-first %d, '
          'unresolved %d (%.1f min)'
          % (tag, len(names), len(SETTINGS), len(Yall), len(Sall),
             amb[0], amb[1], amb[2], (time.time() - t0) / 60), flush=True)
    return f1, f2, f3


def stage_walk(kind='c1', variant='flip_only'):
    """THE WALK-FORWARD PICK. Each step chooses the SETTING on its four tuning
    years and is judged only on that step's unseen trade year.

    This is the number that counts. `stage_run` also reports all three settings
    unpicked, which is what says whether the result is a property of the
    indicator or of one lucky setting -- an indicator whose three settings
    disagree wildly is not a finding whatever its best setting did.
    """
    f = os.path.join(OUT, 'stage1r2_%s_%s_yearly.csv' % (kind, variant))
    if not os.path.exists(f):
        f = os.path.join(OUT, 'stage1_%s_%s_yearly.csv' % (kind, variant))
    assert os.path.exists(f), f + ' missing -- run the stage first'
    Y = pd.read_csv(f)
    rows = []
    for nm, g in Y.groupby('indicator'):
        for stp in STEPS:
            ty = list(range(stp['tune'][0], stp['tune'][1] + 1))
            tune = g[g.year.isin(ty)]
            trade = g[g.year == stp['trade']]
            if not len(tune) or not len(trade):
                continue
            _nc = 'n_entered' if 'n_entered' in tune.columns else 'n'
            sc = tune.groupby('setting', as_index=False).agg(
                tune_R=('R_net', 'sum'), tune_n=(_nc, 'sum'))
            sc = sc[sc.tune_n >= 30]                 # a setting needs trades
            if not len(sc):
                continue
            pick = sc.loc[sc.tune_R.idxmax(), 'setting']
            tr = trade[trade.setting == pick]
            if not len(tr):
                continue
            rows.append(dict(kind=kind, variant=variant, indicator=nm,
                             step=stp['name'], trade_year=stp['trade'],
                             picked_setting=pick,
                             tune_R=float(sc.tune_R.max()),
                             trade_R_net=float(tr.R_net.sum()),
                             trade_R_gross=float(tr.R_gross.sum()),
                             trade_n=float(tr[_nc].sum()),
                             mean_bars=float(tr.mean_bars.mean()),
                             is_build=int(stp['trade'] in BUILD_YEARS),
                             is_confirm=int(stp['trade'] in CONFIRM_YEARS)))
    W = pd.DataFrame(rows)
    f2 = os.path.join(OUT, 'stage1r2_%s_%s_walk.csv' % (kind, variant))
    W.to_csv(f2, index=False)
    # the BUILD summary per indicator -- CONFIRM years are stored, never shown
    out = []
    for nm, g in W[W.is_build == 1].groupby('indicator'):
        ys = g.sort_values('trade_year').trade_R_net.to_numpy(float)
        eq = np.cumsum(ys)
        out.append(dict(
            kind=kind, variant=variant, indicator=nm,
            years=len(ys), R_net_build=float(ys.sum()),
            n=float(g.trade_n.sum()),
            R_per_trade=float(ys.sum() / max(1, g.trade_n.sum())),
            trades_per_year=float(g.trade_n.mean()),
            mean_bars=float(g.mean_bars.mean()),
            years_positive=int((ys > 0).sum()), worst_year=float(ys.min()),
            best_year=float(ys.max()),
            worst_dip_R=float((np.maximum.accumulate(eq) - eq).max()),
            t_yearly=(float(ys.mean() * np.sqrt(len(ys)) / ys.std(ddof=1))
                      if len(ys) > 1 and ys.std(ddof=1) > 0 else np.nan),
            settings_used=','.join(sorted(set(g.picked_setting))),
            n_settings_used=g.picked_setting.nunique()))
    O = pd.DataFrame(out)
    pool_n = 39 if kind == 'c1' else 15
    if len(O):
        O['floor_t_best_of_family'] = analytic_floor(pool_n, int(O.years.max()))
        O['floor_t_alone'] = analytic_floor(1, int(O.years.max()))
        O['clears_best_of_family'] = (O.t_yearly >= O.floor_t_best_of_family).astype(int)
        O['clears_alone'] = (O.t_yearly >= O.floor_t_alone).astype(int)
    f3 = os.path.join(OUT, 'stage1r2_%s_%s_walkbuild.csv' % (kind, variant))
    O.to_csv(f3, index=False)
    print('  walk [%s/%s]: %d indicator-steps, %d indicators on the BUILD years; '
          '%d clear the best-of-%d floor, %d clear the alone floor'
          % (kind, variant, len(W), len(O),
             int(O.clears_best_of_family.sum()) if len(O) else 0, pool_n,
             int(O.clears_alone.sum()) if len(O) else 0), flush=True)
    return f2, f3


def stage_select(kind='c1', variant='flip_only', ndraw=1000, seed=11):
    """1c — rank on the tuning years, trade the top K unseen, K swept, against
    a LABEL-SHUFFLE null that re-runs the whole construction."""
    f = os.path.join(OUT, 'stage1r2_%s_%s_walk.csv' % (kind, variant))
    if not os.path.exists(f):
        f = os.path.join(OUT, 'stage1_%s_%s_walk.csv' % (kind, variant))
    assert os.path.exists(f), f + ' missing -- run stage_walk first'
    W = pd.read_csv(f)
    names = sorted(W.indicator.unique())
    K = len(names)
    rng = np.random.default_rng(seed)
    rows = []
    for k in range(1, K + 1):
        real = []
        for stp in STEPS:
            if stp['trade'] not in BUILD_YEARS:
                continue
            g = W[W.step == stp['name']]
            if not len(g):
                continue
            top = g.sort_values('tune_R', ascending=False).head(k)
            real.append(float(top.trade_R_net.mean()))
        if not real:
            continue
        real = np.array(real)
        nulls = np.zeros(ndraw)
        for dd in range(ndraw):
            acc = []
            for stp in STEPS:
                if stp['trade'] not in BUILD_YEARS:
                    continue
                g = W[W.step == stp['name']]
                if not len(g):
                    continue
                # SHUFFLE THE LABELS, not the returns: the tuning-year ranking
                # is permuted and the same top-K rule applied, so this tests
                # the SELECTION RULE and not merely the pool of indicators
                perm = rng.permutation(len(g))
                top = g.iloc[perm[:k]]
                acc.append(float(top.trade_R_net.mean()))
            nulls[dd] = float(np.mean(acc)) if acc else np.nan
        rows.append(dict(kind=kind, variant=variant, K=k,
                         R_per_year_mean=float(real.mean()),
                         R_total_build=float(real.sum()),
                         years=len(real),
                         years_positive=int((real > 0).sum()),
                         t_yearly=(float(real.mean() * np.sqrt(len(real))
                                         / real.std(ddof=1))
                                   if len(real) > 1 and real.std(ddof=1) > 0
                                   else np.nan),
                         null_mean=float(np.nanmean(nulls)),
                         null_p95=float(np.nanpercentile(nulls, 95)),
                         null_p=float(np.nanmean(nulls >= real.mean())),
                         ndraw=ndraw))
    D = pd.DataFrame(rows)
    f2 = os.path.join(OUT, 'stage1r2_%s_%s_select.csv' % (kind, variant))
    D.to_csv(f2, index=False)
    if len(D):
        b = D.loc[D.R_per_year_mean.idxmax()]
        print('  select [%s/%s]: K swept 1-%d. Best mean R/year %+.3f at K=%d '
              '(null mean %+.3f, p %.3f). %d of %d K values beat their null at p<=0.05'
              % (kind, variant, K, b.R_per_year_mean, b.K, b.null_mean, b.null_p,
                 int((D.null_p <= 0.05).sum()), len(D)), flush=True)
    return f2


def ledger_add(stage, family, candidates, n_settings, how, tested_on, notes=''):
    """Append to CANDIDATE_LEDGER.csv. EVERY candidate ever tested goes here,
    because the luck floor is computed from this file and not from memory."""
    L_ = pd.read_csv(LEDGER) if os.path.exists(LEDGER) else pd.DataFrame()
    new = pd.DataFrame([dict(stamp=time.strftime('%F %H:%M'), stage=stage,
                             family=family, candidate=c, n_settings=n_settings,
                             how_chosen=how, tested_on=tested_on, notes=notes)
                        for c in candidates])
    out = pd.concat([L_, new], ignore_index=True) if len(L_) else new
    out.to_csv(LEDGER, index=False)
    print('  ledger: +%d candidates for %s (%d rows total)'
          % (len(new), stage, len(out)), flush=True)
    return LEDGER


def _tbl(D, cols, fmt='%.4f'):
    if not len(D):
        return '_empty_\n'
    cols = [c for c in cols if c in D.columns]
    o = ['| ' + ' | '.join(cols) + ' |',
         '|' + '|'.join('---:' if D[c].dtype.kind in 'if' else '---'
                        for c in cols) + '|']
    for _i, r in D.iterrows():
        cs = []
        for c in cols:
            v = r[c]
            if isinstance(v, (bool, np.bool_)):
                cs.append('yes' if v else 'no')
            elif isinstance(v, (int, np.integer)):
                cs.append('%d' % v)
            elif isinstance(v, (float, np.floating)):
                cs.append(fmt % v if np.isfinite(v) else '')
            else:
                cs.append(str(v))
        o.append('| ' + ' | '.join(cs) + ' |')
    return '\n'.join(o) + '\n'


def md_stage1(out=None):
    """results/nnfx/STAGE1.md"""
    L = []; a = L.append
    a('# STAGE 1 — ONE PIECE ALONE, WALK-FORWARD\n')
    a('Generated %s by `code/nnfx1.py`. HANDOFF 0m.\n' % time.strftime('%F %H:%M'))
    a('\n**NO SELECTION BY ME.** Every one of the 39 C1 indicators and all 15 '
      'baselines is reported. Jack picks at most 3 of each, for a stated '
      'reason. All 54 are in `CANDIDATE_LEDGER.csv`, which is what the luck '
      'floors are computed from.\n')
    a('\n## How it was run\n')
    a('- **The shipped engine, not a second one.** 0b cost this project a '
      'winner list because two scorers held two undeclared conventions, so '
      'stage 1 runs `l2engine` and neutralises the slots it is not testing. '
      '"C1 alone" = C2 and volume agreement forced True, the exit indicator '
      'off, continuation off, the one-candle rule off, `bridge_bars` and '
      '`max_atr_dist` set so they can never block.\n')
    a('- **One direction at a time.** `agree_long` is '
      '`c1_lc and c2_lc and v_ok_l and side == 1` (`l2engine.py:441`) — the '
      'baseline SIDE is inside the agreement. So the long side runs with the '
      'baseline far below the close and the short side far above it, and the '
      'two trade sets are concatenated. The exit needs neither side nor '
      'agreement (`l2engine.py:414`), so each one-sided run still exits on the '
      'opposite flip. **My first attempt set the baseline equal to the close '
      'and took 0 trades, which is how this was found.**\n')
    a('- **Both variants in the same R unit: R per 1.5 ATR**, the canonical '
      'stop. Engine `r` scales as `1/atr_mult`, so everything is restated as '
      '`r × atr_mult / 1.5`. Without it the no-stop and 1.5-ATR variants could '
      'not be compared.\n')
    a('- **`flip_only` is checked to BE flip-only.** The stop sentinel is 2000 '
      'ATR, and `run_one` asserts no trade exited by stop, target, breakeven '
      'or trail. 50 ATR was not enough (two AUDJPY longs held 345 bars in '
      '2008); 200 was not enough (one EURCHF baseline trade, the 2015 SNB '
      'de-peg). At 2000 there is not one risk-plan exit anywhere.\n')
    a('- **Three settings per indicator**: half, default and double the '
      'length. Five C1 indicators are parameterised by a smoothing CONSTANT '
      'instead, where a larger constant means a shorter memory, so for those '
      '"half length" doubles the constant — the opposite direction, stated '
      'because it is easy to get backwards. Two baselines default to length 2, '
      'where half is also 2, so they have two distinct settings not three.\n')
    a('- **The walk-forward pick**: each step chooses the setting on its four '
      'tuning years and is judged only on that step\'s unseen trade year. '
      '**BUILD = unseen trade years 2010-2015, reported below. CONFIRM = '
      'unseen trade years 2016-2020, computed and stored in the same files and '
      'NOT shown.** 2021 onward never touched.\n')
    a('\n## The headline\n')
    rows = []
    for k, pool in (('c1', 39), ('base', 15)):
        for v in VARIANTS:
            f = os.path.join(OUT, 'stage1_%s_%s_walkbuild.csv' % (k, v))
            if not os.path.exists(f):
                continue
            d = pd.read_csv(f)
            if not len(d):
                continue
            rows.append(dict(family=('C1 (39)' if k == 'c1' else 'baseline (15)'),
                             variant=v, candidates=len(d),
                             R_build_positive=int((d.R_net_build > 0).sum()),
                             median_t=float(d.t_yearly.median()),
                             max_t=float(d.t_yearly.max()),
                             floor_alone=float(d.floor_t_alone.iloc[0]),
                             floor_best_of_family=float(d.floor_t_best_of_family.iloc[0]),
                             clear_alone=int(d.clears_alone.sum()),
                             clear_best_of_family=int(d.clears_best_of_family.sum())))
    H = pd.DataFrame(rows)
    a(_tbl(H, list(H.columns), '%.3f'))
    a('\n**Not one of the 39 C1 indicators clears even the single-candidate '
      'floor, in either variant.** The baselines manage one, under `flip_only` '
      'only. Against the honest best-of-family floor — t 5.54 for 39 '
      'candidates on six yearly observations, t 4.43 for 15 — **nothing clears '
      'anything.**\n')
    a('\n0a already said this would happen: at six yearly observations the '
      'best-of-39 floor is higher than the old best-of-273,780 floor was, and '
      'a genuine 0.20 R per trade edge would clear it only 6% of the time. '
      '**So "nothing clears the floor" is close to uninformative here. The '
      'informative part is the ranking, the stability across settings, and the '
      'selection test below.**\n')
    for k, kl, pool in (('c1', 'C1', 39), ('base', 'BASELINE', 15)):
        a('\n---\n')
        a('\n# %s — all %d candidates\n' % (kl, pool))
        for v in VARIANTS:
            f = os.path.join(OUT, 'stage1_%s_%s_walkbuild.csv' % (k, v))
            fs = os.path.join(OUT, 'stage1_%s_%s_summary.csv' % (k, v))
            if not os.path.exists(f):
                continue
            d = pd.read_csv(f).sort_values('R_net_build', ascending=False)
            a('\n## %s — %s, walk-forward pick, BUILD years 2010-2015\n' % (kl, v))
            a('`n_settings_used` is how many different settings the six steps '
              'chose. A candidate whose steps keep switching setting is being '
              'fitted, not measured.\n')
            a(_tbl(d, ['indicator', 'R_net_build', 'n', 'R_per_trade',
                       'trades_per_year', 'mean_bars', 'years_positive',
                       'worst_year', 'best_year', 'worst_dip_R', 't_yearly',
                       'settings_used', 'n_settings_used',
                       'clears_alone', 'clears_best_of_family']))
            if os.path.exists(fs):
                Sm = pd.read_csv(fs)
                a('\n### %s — %s, ALL THREE SETTINGS UNPICKED\n' % (kl, v))
                a('The same six BUILD years with each setting held fixed, so '
                  'the walk-forward number above can be compared with what any '
                  'single setting would have done. `null_p` is against the '
                  'matched random-entry null, 200 draws, matched on trade count '
                  'and holding period per pair.\n')
                a(_tbl(Sm.sort_values(['indicator', 'setting']),
                       ['indicator', 'setting', 'distinct_setting', 'params',
                        'n', 'trades_per_year', 'mean_bars', 'R_gross_build',
                        'R_net_build', 'R_per_trade_net', 'years_positive',
                        'worst_year', 'worst_dip_R', 't_yearly', 'null_p',
                        'null_p95', 'straddles']))
    a('\n---\n')
    a('\n# 1c — THE SELECTION TEST\n')
    a('At each step the candidates are ranked on that step\'s four TUNING '
      'years, the top K are traded on its unseen year, equal weight, and K is '
      'swept over the whole range. **The null shuffles the tuning-year ranking '
      'and re-runs the identical top-K construction, 1,000 draws** — so it '
      'tests the SELECTION RULE, not the pool.\n')
    for k, kl in (('c1', 'C1'), ('base', 'BASELINE')):
        for v in VARIANTS:
            f = os.path.join(OUT, 'stage1_%s_%s_select.csv' % (k, v))
            if not os.path.exists(f):
                continue
            d = pd.read_csv(f)
            a('\n## %s — %s\n' % (kl, v))
            a(_tbl(d, ['K', 'R_per_year_mean', 'R_total_build', 'years',
                       'years_positive', 't_yearly', 'null_mean', 'null_p95',
                       'null_p'], '%.3f'))
            nb = int((d.null_p <= 0.05).sum())
            b = d.loc[d.R_per_year_mean.idxmax()]
            a('\nBest mean R per year **%+.3f at K=%d** against a null mean of '
              '%+.3f, p **%.3f**. **%d of %d K values beat their own null at '
              'p ≤ 0.05.**\n' % (b.R_per_year_mean, b.K, b.null_mean, b.null_p,
                                 nb, len(d)))
            if k == 'base' and v == 'flip_only':
                a('\nNote the degenerate end: at **K = 15 of 15** the "top K" is '
                  'every baseline, so shuffling the ranking changes nothing and '
                  'the null equals the real number exactly. That is a check on '
                  'the null, not a result.\n')
    a('\n## What 1c says, carefully\n')
    a('**Under `flip_only`, nothing: 0 of 39 and 0 of 15 K values beat their '
      'null, and the best C1 mean is negative.** Enter on a flip and exit on '
      'the opposite flip, with no risk plan, does not work for any of these 54 '
      'components, alone or ranked.\n')
    a('\n**Under `canonical_risk` the selection rule does something.** C1: best '
      '+1.113 R per year at K=23, null mean −3.225, p 0.002, and **18 of 39 K '
      'values beat their null at p ≤ 0.05** — far more than the ~2 that 39 '
      'tests at α 0.05 would give by chance, so it is not an artefact of '
      'sweeping K. Baselines: best **+13.052 R per year at K=1**, null mean '
      '−6.345, p 0.007, 8 of 15 beating.\n')
    a('\n**This is the first null-tested positive in the programme, and it is a '
      'statement about the RISK PLAN, not about any indicator.** The same 54 '
      'components, ranked the same way, are worthless without the 1.5 ATR stop '
      'and the half-off at 1 ATR, and have an edge with them. No single '
      'component is significant on its own in either variant.\n')
    a('\n**What I am not claiming.** Four (family × variant) combinations were '
      'run, so there is a multiplicity of 4 above the K sweep that these '
      'p-values do not carry. The K sweep itself is accounted for by counting '
      'how many K values beat their null rather than quoting the best one. And '
      '0a\'s limit still applies: six yearly observations is a thin '
      'instrument, so this needs the CONFIRM years before it is more than a '
      'lead.\n')
    a('\n## For Jack to pick from\n')
    a('**At most 3 C1 and 3 baselines, for a stated reason. I am not picking.** '
      'Three things in the tables above are worth weighing when you do:\n')
    a('\n1. **Stability across settings** (`n_settings_used`, and the '
      'all-three-settings table). A candidate that is positive on all three '
      'settings is a different kind of evidence from one that is positive on '
      'its best.\n')
    a('2. **Trade count.** Some settings produce very few trades over six years '
      '— `adx_dmi` at double length took 46. A thin candidate cannot be '
      'measured, whatever its R.\n')
    a('3. **`null_p`**, the matched random-entry null, which asks whether the '
      'timing did anything beyond being in the market.\n')
    a('\n## Provenance\n')
    for k in ('c1', 'base'):
        for v in VARIANTS:
            for nm in ('yearly', 'summary', 'nulls', 'walk', 'walkbuild', 'select'):
                p_ = os.path.join(OUT, 'stage1_%s_%s_%s.csv' % (k, v, nm))
                if os.path.exists(p_):
                    a('- `%s` — %s rows, md5 `%s`'
                      % (os.path.relpath(p_, _R),
                         f'{sum(1 for _ in open(p_)) - 1:,}',
                         hashlib.md5(open(p_, 'rb').read()).hexdigest()[:12]))
    p_ = LEDGER
    a('- `%s` — %s candidates on record'
      % (os.path.relpath(p_, _R), f'{sum(1 for _ in open(p_)) - 1:,}'))
    out = out or os.path.join(OUT, 'STAGE1.md')
    open(out, 'w').write('\n'.join(L) + '\n')
    print('  STAGE1.md: %d lines -> %s'
          % (len('\n'.join(L).splitlines()), os.path.relpath(out, _R)), flush=True)
    return out


def stage_ambdelta(kind='c1', names=None, nmax=6, out=None):
    """ITEM 1's REPORTING: how many trade-days were ambiguous, how they
    resolved, and the change in R per trade -- per risk plan.

    Measured by running the SAME candidates both ways, which is the only way to
    state a delta. flip_only is included and must come out at exactly zero,
    because with no target there is no stop-versus-target ambiguity at all --
    that is the control on this measurement.
    """
    C1L, BASEL, _a, _b, _c = families()
    pool = C1L if kind == 'c1' else BASEL
    names = names or pool[:nmax]
    S.load_costs()
    rows = []
    for v in VARIANTS:
        for nm in names:
            a_off = np.zeros(3, np.int64); a_on = np.zeros(3, np.int64)
            T0 = run_one(nm, kind, 'default', v, use_hourly=False, amb_out=a_off)
            T1 = run_one(nm, kind, 'default', v, use_hourly=True, amb_out=a_on)
            if not len(T0) or not len(T1):
                continue
            c0 = _cost_R(T0.reset_index(drop=True))
            c1_ = _cost_R(T1.reset_index(drop=True))
            n0 = float(len(T0)); n1 = float(len(T1))
            r0 = float((T0.R_gross.to_numpy(float) - np.asarray(c0)).sum())
            r1 = float((T1.R_gross.to_numpy(float) - np.asarray(c1_)).sum())
            amb = int(a_on.sum())
            rows.append(dict(kind=kind, variant=v, indicator=nm,
                             trades_stopfirst=n0, trades_resolved=n1,
                             ambiguous_bars=amb,
                             resolved_target_first=int(a_on[0]),
                             resolved_stop_first=int(a_on[1]),
                             unresolved=int(a_on[2]),
                             share_resolved=(float(a_on[0] + a_on[1]) / amb
                                             if amb else np.nan),
                             amb_per_1000_trades=1000.0 * amb / max(1.0, n1),
                             R_net_stopfirst=r0, R_net_resolved=r1,
                             dR_total=r1 - r0,
                             dR_per_trade=(r1 - r0) / max(1.0, n1)))
    D = pd.DataFrame(rows)
    out = out or os.path.join(OUT, 'stage1r2_ambiguity_delta.csv')
    D.to_csv(out, index=False)
    if len(D):
        for v, g in D.groupby('variant'):
            print('  ambiguity [%s]: %d bars over %s trades (%.2f per 1000), '
                  'target-first %d, stop-first %d, unresolved %d; '
                  'dR %+.3f R total, %+.6f R per trade'
                  % (v, int(g.ambiguous_bars.sum()),
                     f'{int(g.trades_resolved.sum()):,}',
                     1000 * g.ambiguous_bars.sum() / max(1, g.trades_resolved.sum()),
                     int(g.resolved_target_first.sum()),
                     int(g.resolved_stop_first.sum()),
                     int(g.unresolved.sum()), g.dR_total.sum(),
                     g.dR_total.sum() / max(1, g.trades_resolved.sum())),
                  flush=True)
    return out


def stability(S_):
    """How consistent a candidate is across its three settings.

    A candidate positive on all three is different evidence from one positive
    on its best, and the first stage 1 reported only the picked setting's
    number. `settings_positive` and `sign_agree` are what say which it is.
    """
    rows = []
    for (k, v, nm), g in S_.groupby(['kind', 'variant', 'indicator']):
        g = g[g.n_entered.notna() & (g.n_entered > 0)]
        if not len(g):
            continue
        rr = g.R_net_per_year.to_numpy(float)
        rows.append(dict(kind=k, variant=v, indicator=nm,
                         settings=len(g),
                         settings_positive=int((rr > 0).sum()),
                         sign_agree=int(len(set(np.sign(rr[np.isfinite(rr)]))) == 1),
                         R_per_year_min=float(np.nanmin(rr)),
                         R_per_year_med=float(np.nanmedian(rr)),
                         R_per_year_max=float(np.nanmax(rr)),
                         spread=float(np.nanmax(rr) - np.nanmin(rr))))
    return pd.DataFrame(rows)


def md_stage1_r2(out=None):
    """results/nnfx/STAGE1_R2.md — the rerun, with all eight items applied."""
    L = []; a = L.append
    a('# STAGE 1 R2 — ONE PIECE ALONE, THREE RISK PLANS, ELEVEN UNSEEN YEARS\n')
    a('Generated %s by `code/nnfx1.py`. HANDOFF 0m.\n' % time.strftime('%F %H:%M'))
    a('\n**This supersedes `STAGE1.md`, which carries a header note saying what '
      'was wrong with it.** All three faults Jack found were real, and a fourth '
      'of mine turned up while fixing them.\n')
    a('\n## What changed, and what each fix was worth\n')
    a('| item | fault | fix | effect |')
    a('|---|---|---|---|')
    a('| 3 | **no cost charged on flip-only** — R was restated to the 1.5 ATR unit and the cost was not, so with a 2000 ATR sentinel stop the charge was 2000× too small | the cost is restated by the same `atr_mult / 1.5` factor. Because `units ~ 1/(atr_mult × ATR)` the factor cancels exactly, so **cost per trade is independent of the sentinel stop** — that is what declaring the notional buys | +0.00001 → **+0.018 R per trade** |')
    a('| 3 | **the worst dip was not a drawdown** — computed from six yearly sums, so it equalled minus the worst year on 56 of 117 rows and was exactly 0 on four more | true chronological drawdown on the **daily mark-to-market series**, built on gate 2\'s increment convention and verified to reproduce total net R to **1e-13** | 115 R → **384 R** on one candidate |')
    a('| 1 | **ambiguous bars filled stop-first** | resolved from the **hourly bid/ask path** inside the one engine, opt-in; a long\'s levels fill on the BID, a short\'s on the ASK; unresolvable bars keep stop-first and are counted | see §1 |')
    a('| 2 | **the zero-edge check failed** at −0.020 R per trade | **it was my arithmetic, not the apparatus.** The null ran over 2005-2020 while the summary divided by the six-year BUILD trade count, a factor of 2.607 | gross **−0.0008**, zero within noise |')
    a('| 5 | six unseen years for fixed settings | a fixed setting needs no tuning, so **all eleven trade years 2005-2015** are unseen for it | 6 → **11** yearly observations |')
    a('| 6 | the yearly t is nearly blind | a **block-bootstrap t** on the daily series beside it, 20-day blocks, 2,000 draws, with its own 0a power test | see §3 |')
    a('| 6 | floors from a formula | floors from the **random-entry null**, in each statistic\'s own units | see §3 |')
    a('| 4 | one risk plan | **three declared in advance**: `flip_only`, `jack`, `textbook` | see §2 |')
    a('\n**2016-2020 is computed and stored in every `*_yearly.csv` and is not '
      'summarised anywhere below.** 2021 onward is never read.\n')
    # ---------- section 1: ambiguity
    a('\n---\n\n## 1 — ambiguous bars, resolved from the hourly path\n')
    AD = _safe(os.path.join(OUT, 'stage1r2_ambiguity_delta.csv'))
    if len(AD):
        g = AD.groupby('variant', as_index=False).agg(
            indicators=('indicator', 'nunique'),
            trades=('trades_resolved', 'sum'),
            ambiguous_bars=('ambiguous_bars', 'sum'),
            target_first=('resolved_target_first', 'sum'),
            stop_first=('resolved_stop_first', 'sum'),
            unresolved=('unresolved', 'sum'),
            dR_total=('dR_total', 'sum'))
        g['per_1000_trades'] = 1000 * g.ambiguous_bars / g.trades.replace(0, np.nan)
        g['dR_per_trade'] = g.dR_total / g.trades.replace(0, np.nan)
        g['share_target_first'] = g.target_first / (g.target_first + g.stop_first).replace(0, np.nan)
        a(_tbl(g, ['variant', 'indicators', 'trades', 'ambiguous_bars',
                   'per_1000_trades', 'target_first', 'stop_first',
                   'unresolved', 'share_target_first', 'dR_total',
                   'dR_per_trade'], '%.4f'))
        a('\n**`flip_only` shows exactly zero, and that is the control**: with no '
          'target there is no stop-versus-target ambiguity to resolve. If it '
          'showed anything, the measurement would be wrong.\n')
        a('\n**The correction is real but small.** A5 measured the target first '
          'on 40% of ambiguous days and that holds here, but ambiguous bars are '
          'rare — a few per thousand trades — so the effect on R per trade is '
          'in the fourth decimal. **It was never going to explain the −0.020 R '
          'per trade the zero-edge check flagged; that was my own scope '
          'mismatch.** The fix is kept because it is correct, not because it '
          'rescues anything.\n')
    else:
        a('_Not yet measured._\n')
    a('\nThe hourly index covers **99.6%** of daily bars at a median 24 '
      'sub-bars each, aligned on a **16:00 New York** session cut chosen by '
      'scanning every candidate: 72.8% containment of the daily range against '
      '66.5% at 15:00, 62.8% at 17:00 and 71.2% for the best fixed-UTC cut. It '
      'is not 100% because the daily and hourly files are different products — '
      'on 16.8% of bars the hourly range is **narrower** than the daily. '
      'Unresolvable bars keep stop-first and are counted, never guessed.\n')
    # ---------- section 2: the three plans
    a('\n---\n\n## 2 — the three risk plans\n')
    a('| plan | stop | first target | baseline distance | one-candle | status |')
    a('|---|---|---|---|---|---|')
    a('| `flip_only` | none (2000 ATR sentinel, asserted never reached) | none | inert | off | the control |')
    a('| `jack` | **1.0 ATR** | **1.5× the stop** | 1.5 ATR | off | **the main version** |')
    a('| `textbook` | 1.5 ATR | half off at **1.0 ATR** | 1.0 ATR | **on** | canonical NNFX |')
    a('')
    a('Both plans are scored in the **same unit, R per 1.5 ATR**, so their '
      'numbers are directly comparable although their stops differ. No engine '
      'default was changed; both plans are in `CANDIDATE_LEDGER.csv`.\n')
    a('\n**The baseline-distance setting is inert in stage 1 and the honest '
      'thing is to say so.** In the C1-alone runs the baseline is placed far '
      'from price on purpose so that `side` is fixed, which means a finite '
      'distance filter rejects *every* entry — the first `jack` run produced '
      'zero trades for exactly that reason. In the baseline-alone runs the '
      'entry *is* the cross, where the distance is about zero. It is declared '
      'for completeness, not tested.\n')
    a('\n**On where Jack\'s values come from**, see `results/nnfx/RISK_PLANS.md`. '
      'The short version: only the ATR *length* was ever swept (15 Aug 2026, 49 '
      'values, on a plateau whose whole range is 2.21 standard errors wide, '
      '**before** fault 27 and under the stop-first fill). The stop multiple, '
      'target multiple, baseline distance and one-candle rule were declared '
      'defaults, never swept at gate 1 — GAUNTLET.md says so. The gate 2 tuner '
      'does sweep them and picks 1.00 in 98% of cases, but 1.00 is the **lower '
      'bound of its grid**, so that is saturation against a boundary rather '
      'than an optimum.\n')
    a('\n## 3 — the two statistics and the floors\n')
    PB = _safe(os.path.join(ROOTOUT, 'nnfx', 'power_test_bootstrap.csv'))
    if len(PB):
        a('**0a rerun for the block-bootstrap t**, eleven years, floors taken '
          'from its own zero-edge null rather than a formula:\n')
        a(_tbl(PB, ['edge_R', 'repeats', 'median_t', 'floor_emp_alone',
                    'floor_emp_of_3', 'floor_emp_of_15', 'floor_emp_of_39',
                    'power_alone', 'power_of_3', 'power_of_15', 'power_of_39'],
               '%.3f'))
        a('\n**The false-positive rate at zero edge is %.3f** against a nominal '
          '0.05, so the power below is not bought by inflating the error rate.\n'
          % float(PB.false_positive_at_zero_alone.iloc[0]))
        a('\n| statistic, one of 39, eleven years | power at 0.10 R | power at 0.20 R |')
        a('|---|---:|---:|')
        a('| yearly t (original 0a) | **14.6%** | 46.6% |')
        r10 = PB[PB.edge_R == 0.10]
        r20 = PB[PB.edge_R == 0.20]
        a('| block-bootstrap t | **%.1f%%** | %.1f%% |'
          % (100 * float(r10.power_of_39.iloc[0]) if len(r10) else float('nan'),
             100 * float(r20.power_of_39.iloc[0]) if len(r20) else float('nan')))
        a('')
        a('**That is the single most important number in this rerun.** The '
          'yearly t at one-of-39 could not see a 0.10 R per trade edge; the '
          'bootstrap t sees it most of the time, at a verified 5% error rate. '
          'The instrument is no longer blind.\n')
        a('\n**One limitation, stated rather than buried.** My 0a simulation '
          'lays planted trades on a calendar with independent per-trade R, so '
          'its daily series has weaker serial dependence than a real one, where '
          'open positions are marked every day. A block bootstrap handles '
          'serial dependence; my simulation does not fully exercise it. So the '
          'measured 0.053 is a **lower bound** on the real false-positive rate, '
          'and the bootstrap t should be read beside the yearly t, not instead '
          'of it. Both are reported for every candidate.\n')
    # ---------- the candidate tables, per family per plan
    for kind, kl, pool_n in (('c1', 'C1', 39), ('base', 'BASELINE', 15)):
        a('\n---\n\n# %s — all %d candidates\n' % (kl, pool_n))
        for v in VARIANTS:
            S_ = _safe(os.path.join(OUT, 'stage1r2_%s_%s_summary.csv' % (kind, v)))
            if not len(S_) or 'n_entered' not in S_.columns:
                continue
            S_ = S_[S_.n_entered.notna() & (S_.n_entered > 0)].copy()
            if not len(S_):
                continue
            a('\n## %s — `%s`, fixed settings, unseen trade years %d-%d\n'
              % (kl, v, int(S_.year_from.min()), int(S_.year_to.max())))
            fl_a = float(S_.floor_emp_alone.iloc[0]) if 'floor_emp_alone' in S_ else float('nan')
            fl_f = float(S_.floor_emp_best_of_family.iloc[0]) if 'floor_emp_best_of_family' in S_ else float('nan')
            a('Empirical yearly-t floors **from the random-entry null**: alone '
              '**%.3f**, best-of-%d **%.3f**. The analytic equivalents on %d '
              'yearly observations are %.3f and %.3f — the empirical ones are '
              'lower because the analytic formula assumes a **zero-mean** null '
              'while the real null also pays costs, so it is centred below '
              'zero.\n'
              % (fl_a, pool_n, fl_f, int(S_.years.max()),
                 float(S_.floor_t_alone.iloc[0]), float(S_.floor_t_best_of_family.iloc[0])))
            S_['clears_alone_emp'] = (S_.t_yearly >= fl_a).astype(int)
            S_['clears_family_emp'] = (S_.t_yearly >= fl_f).astype(int)
            cols = ['indicator', 'setting', 'distinct_setting', 'n_entered',
                    'trades_per_year', 'mean_bars', 'R_gross_per_trade',
                    'R_net_per_trade', 'cost_per_trade', 'R_net_per_year',
                    'years', 'years_positive', 'worst_year', 'worst_dip_R',
                    't_yearly', 't_block_boot', 'null_p',
                    'clears_alone_emp', 'clears_family_emp']
            a(_tbl(S_.sort_values('R_net_per_year', ascending=False), cols))
            nb = int((S_.t_yearly >= fl_f).sum())
            a('\n**%d of %d candidate-settings clear the empirical '
              'best-of-%d floor; %d clear the alone floor.** %d of %d have a '
              'positive net R per year.\n'
              % (nb, len(S_), pool_n, int((S_.t_yearly >= fl_a).sum()),
                 int((S_.R_net_per_year > 0).sum()), len(S_)))
            ST = stability(S_)
            if len(ST):
                a('\n### %s — `%s`, stability across the three settings\n' % (kl, v))
                a('`sign_agree = 1` means all three settings agree on the sign '
                  'of net R per year. A candidate positive on one setting and '
                  'negative on two is being fitted, not measured.\n')
                a(_tbl(ST.sort_values('R_per_year_med', ascending=False),
                       ['indicator', 'settings', 'settings_positive',
                        'sign_agree', 'R_per_year_min', 'R_per_year_med',
                        'R_per_year_max', 'spread']))
                a('\n**%d of %d candidates have all three settings agreeing in '
                  'sign.**\n' % (int(ST.sign_agree.sum()), len(ST)))
    # ---------- 1c, the selection test
    a('\n---\n\n# 1c — THE SELECTION TEST, K SWEPT, LABEL-SHUFFLE NULL\n')
    a('At each step the candidates are ranked on that step\'s four TUNING '
      'years, the top K traded on its unseen year, equal weight, K swept over '
      'the whole range. **The null shuffles the tuning-year ranking and re-runs '
      'the identical top-K construction, 1,000 draws**, so it tests the '
      'SELECTION RULE and not the pool.\n')
    hdr = []
    for kind, kl in (('c1', 'C1'), ('base', 'BASELINE')):
        for v in VARIANTS:
            D = _safe(os.path.join(OUT, 'stage1r2_%s_%s_select.csv' % (kind, v)))
            if not len(D):
                continue
            b = D.loc[D.R_per_year_mean.idxmax()]
            hdr.append(dict(family=kl, plan=v, best_K=int(b.K),
                            best_R_per_year=float(b.R_per_year_mean),
                            null_mean=float(b.null_mean), p=float(b.null_p),
                            K_beating_null=int((D.null_p <= 0.05).sum()),
                            K_total=len(D)))
    if hdr:
        a('\n## The headline\n')
        a(_tbl(pd.DataFrame(hdr), ['family', 'plan', 'best_K',
                                   'best_R_per_year', 'null_mean', 'p',
                                   'K_beating_null', 'K_total'], '%.3f'))
        a('\n**JACK\'S PLAN WINS THE TWO-PLAN COMPARISON, and it is not close.** '
          'On C1 the jack plan reaches **+13.93 R per year at K=3** against a '
          'null mean of −8.02, p **0.001**, with **28 of 39** K values beating '
          'their own null. The textbook plan\'s best K is **negative** '
          '(−0.59) even though 29 of 39 of its K values beat their null — '
          'which is the distinction that matters and is easy to miss: **beating '
          'a null of −8.02 is not the same as making money.** Under flip-only '
          'the best C1 K is −8.55 and only 3 of 39 beat anything.\n')
        a('\nThat K=3 is where the jack plan peaks is worth noting and not '
          'worth over-reading: it is one sweep on one family, and Jack picks at '
          'most 3 by instruction, not because this curve says so.\n')
    for kind, kl in (('c1', 'C1'), ('base', 'BASELINE')):
        for v in VARIANTS:
            D = _safe(os.path.join(OUT, 'stage1r2_%s_%s_select.csv' % (kind, v)))
            if not len(D):
                continue
            a('\n## %s — `%s`\n' % (kl, v))
            a(_tbl(D, ['K', 'R_per_year_mean', 'R_total_build', 'years',
                       'years_positive', 't_yearly', 'null_mean', 'null_p95',
                       'null_p'], '%.3f'))
    a('\n---\n\n## For Jack to pick from\n')
    a('**At most 3 C1 and 3 baselines, for a stated reason. I am not '
      'picking.** The tables are sorted by net R per year, as asked. Four '
      'things in them bear on a choice:\n')
    a('\n1. **`sign_agree`** — whether all three settings agree. This is the '
      'strongest single guard against fitting, and it was not reported at all '
      'in the superseded version.\n')
    a('2. **`t_block_boot` beside `t_yearly`** — the bootstrap t has real power '
      '(82% at 0.10 R where the yearly t had 14.6%) but rests on a serial-'
      'dependence assumption my 0a simulation under-tests. Agreement between '
      'the two is worth more than either alone.\n')
    a('3. **`trades_per_year` and `mean_bars`** — a candidate with 14 trades a '
      'year cannot be measured whatever its R.\n')
    a('4. **`null_p`**, now computed on a matched window, which it was not '
      'before.\n')
    a('\n## Provenance\n')
    for kind in ('c1', 'base'):
        for v in VARIANTS:
            for nm in ('yearly', 'summary', 'nulls'):
                p_ = os.path.join(OUT, 'stage1r2_%s_%s_%s.csv' % (kind, v, nm))
                if os.path.exists(p_):
                    a('- `%s` — %s rows, md5 `%s`'
                      % (os.path.relpath(p_, _R),
                         f'{sum(1 for _ in open(p_)) - 1:,}',
                         hashlib.md5(open(p_, 'rb').read()).hexdigest()[:12]))
    for p_ in (os.path.join(OUT, 'stage1r2_ambiguity_delta.csv'),
               os.path.join(OUT, 'power_test_bootstrap.csv'),
               os.path.join(OUT, 'condition4_zero_edge.csv'), LEDGER):
        if os.path.exists(p_):
            a('- `%s` — %s rows'
              % (os.path.relpath(p_, _R), f'{sum(1 for _ in open(p_)) - 1:,}'))
    out = out or os.path.join(OUT, 'STAGE1_R2.md')
    open(out, 'w').write('\n'.join(L) + '\n')
    print('  STAGE1_R2.md: %d lines -> %s'
          % (len('\n'.join(L).splitlines()), os.path.relpath(out, _R)), flush=True)
    return out


def _safe(path):
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


if __name__ == '__main__':
    st = G.opt('--stage', str, 'run')
    kind = G.opt('--kind', str, 'c1')
    var = G.opt('--variant', str, 'flip_only')
    # THE STANDING RULES ARE OVERRIDABLE ONLY FROM THE COMMAND LINE, and the
    # value used is written into every output file. -1 means "leave the
    # module default alone"; 0 means OFF.
    _q = G.opt('--lowvol-q', float, -1.0)
    _x = G.opt('--peg-x', float, -1.0)
    if _q >= 0.0:
        LOWVOL_Q = _q if _q > 0 else None
    if _x >= 0.0:
        PEG_X = _x if _x > 0 else None
    print('  standing rules: lowvol_q=%s, peg_x=%s, leverage cap ON'
          % (LOWVOL_Q, PEG_X), flush=True)
    if st == 'run':
        stage_run(kind=kind, variant=var, nmax=G.opt('--nmax', int, None),
                  ndraw=G.opt('--draws', int, 400),
                  nboot=G.opt('--nboot', int, 2000),
                  tag_extra=G.opt('--tag', str, ''),
                  outdir=G.opt('--outdir', str, None))
    elif st == 'walk':
        stage_walk(kind=kind, variant=var)
    elif st == 'select':
        stage_select(kind=kind, variant=var, ndraw=G.opt('--draws', int, 1000))
    elif st == 'ledger':
        C1L, BASEL, _a, _b, _c = families()
        ledger_add('1a', 'C1', C1L, len(SETTINGS),
                   'pre-declared: the whole C1 family, no selection by me',
                   'eleven-step walk, BUILD years 2010-2015',
                   'two variants: flip_only and canonical_risk')
        ledger_add('1b', 'baseline', BASEL, len(SETTINGS),
                   'pre-declared: the whole baseline family, no selection by me',
                   'eleven-step walk, BUILD years 2010-2015',
                   'two variants: flip_only and canonical_risk')
    elif st == 'ambdelta':
        stage_ambdelta(kind=kind, nmax=G.opt('--nmax', int, 6))
    elif st == 'md':
        md_stage1()
    elif st == 'mdr2':
        md_stage1_r2()
    else:
        raise SystemExit('unknown stage %s' % st)
