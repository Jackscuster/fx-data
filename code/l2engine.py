import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""THE STRATEGY ENGINE. One slot combination, one pair, the fixed V5.1 mechanics.

The bar loop is `run_bars`, an @njit function taking primitive arrays and
returning primitive arrays. No pandas, no dicts, no objects cross into it. Every
indicator is precomputed OUTSIDE it into bool/float arrays and the loop only
indexes them -- that is what makes millions of combinations feasible, because
the indicators for a pair are computed once and reused across every combination
that mentions them.

NO REGIME LOGIC HERE. The plan is a PARAMETER (plan=2 two-leg, plan=1 one-leg).
The join to Layer 1's labels is designed separately; the engine must not know
what a regime is.

------------------------------------------------------------------------
ORDER OF EVENTS WITHIN A BAR -- the thing that silently changes results
------------------------------------------------------------------------
  1. if in a position, resolve stops and targets INTRABAR against this bar's
     high and low;
  2. then read signals at the CLOSE and act on them, filling at that close.

Doing it the other way round lets a position opened on today's close be
stopped out by today's low, which is a bar the trade was never in.

A STOP MOVED DURING A BAR CANNOT ALSO FILL DURING THAT BAR. When leg 1 banks
its target, leg 2's stop jumps to breakeven -- but that move is a consequence of
something that happened somewhere inside the bar, and filling the new stop
against the same bar's low assumes the target was hit first. It also matches
Pine, where a stop order rests from the previous close and cannot be amended
mid-bar. The moved stop therefore goes live on the NEXT bar. (A synthetic test
whose bar had low exactly at breakeven is what surfaced this; see l2verify.py
case 4.)

TIE-BREAK: a bar whose range covers both the stop and the target fills the
STOP. Daily bars cannot say which came first, and assuming the good one is how
a backtest invents money. The rate is counted and reported -- if it is large,
daily resolution is the wrong instrument for that stop distance and that is
Jack's call to make, not something to average away.

------------------------------------------------------------------------
FILLS
------------------------------------------------------------------------
Entries fill AT the close of the signal bar (process_orders_on_close), which is
how Jack trades and what the Pine strategy is configured for. This is the one
place the project's usual one-bar lag is deliberately absent: the indicators are
computed from data through the close of the bar and the fill is at that same
close. Nothing reads a later bar.

Stops and targets fill at their own price, not at the close.

------------------------------------------------------------------------
THE THREE ENTRY ROUTES, and the two blocks that apply to ALL of them
------------------------------------------------------------------------
  baseline cross   price crosses the baseline and every confirmation agrees
  C1 flip          C1 changes direction and every confirmation agrees
  continuation     re-entry in the direction already held, with no baseline
                   re-cross since the last exit

  TOO LATE      |close - baseline| > 1.5 x ATR
  BRIDGE TOO FAR more than 7 bars since the baseline cross

The Pine version exempted continuation entries from Bridge Too Far. That is a
bug and it is fixed here from the first line rather than reproduced: the block
is applied in one place, to all three routes.

"Every confirmation agrees" means C1 and C2 both confirm the direction, the
volume filter passes, and price is on the correct side of the baseline. A
TERNARY confirmation that is neutral does not abstain -- it BLOCKS, because a
ternary indicator's neutral is a statement that there is no trend to trade.

THE ONE CANDLE RULE, stated once so it is consistent. When C1 flips but price
is on the wrong side of the baseline, the trigger is held for EXACTLY ONE bar.
If the next bar puts price on the correct side, the entry is taken -- and it is
evaluated against THE SIGNAL BAR'S confirmations, not the next bar's. The
alternative (re-reading confirmations on the entry bar) makes the rule a
one-bar-lagged ordinary entry and quietly drops every case where C1 flipped and
then flipped straight back.

------------------------------------------------------------------------
RISK -- fixed, never swept
------------------------------------------------------------------------
2% of account per trade. Size = risk$ / (atr_mult x ATR), so the dollar risk is
identical on every trade and R is exact.

  two-leg plan  legs 50/50. Leg 1 stop 1xATR, target 1.5xATR. Leg 2 no target;
                phase 0 fixed stop, phase 1 stop to breakeven the moment Leg 1
                banks, phase 2 trail 1.5xATR behind the highest close once the
                trade is 2xATR in profit.
  one-leg plan  one position, stop 1xATR, target 1.5xATR, no runner.

Phase state resets on EVERY entry, including a reversal. The Pine version
carried leg-phase across a reversal, so a fresh short could inherit the previous
long's trailing stop. Fixed here from the start.

RISK IS CONSTANT, NOT COMPOUNDED. Every trade risks the same dollar amount, so
expectancy in R is exact and a run's result does not depend on the order its
trades happened to fall in. A compounding curve is derived afterwards in Python
if it is wanted; it never feeds the loop.

------------------------------------------------------------------------
SUSPECT BARS
------------------------------------------------------------------------
l2clean.py flags bad prints and flat bars. The engine will not OPEN or CLOSE on
one, and will not resolve a stop or target against one, because a 20% spike that
never traded would otherwise fill every stop in the book. Real events -- the CHF
unpeg, Brexit -- are not flagged and are traded normally. Pass
block_suspect=False to disable.

------------------------------------------------------------------------
WHERE THIS DELIBERATELY DIFFERS FROM THE SHIPPED PINE
------------------------------------------------------------------------
Both are on the work order's instruction, and both will show up in a Phase 3
trade-by-trade comparison, so they are listed rather than discovered:

  BRIDGE TOO FAR ON CONTINUATIONS. Pine's longcondition3 / shortcondition3
  carry Ind_CON_Trig but NOT Ind_BTF_Conf, so continuation entries skip the
  bridge. That is the known bug; here the bridge applies to all three routes.
  Expect the engine to take FEWER continuation entries than TradingView.

  LEG PHASE ON REVERSAL. Pine resets nnfx_phase_* on entry_long / entry_short,
  which does cover reversals -- but its trail tracker is a `var` that is only
  reset to na, and long and short phases are tracked in separate variables that
  are cleared only when flat. This engine rebuilds every field on every entry.

Everything else follows the source, including the details the work order's
prose got wrong -- see the phase block and the continuation route.

Writes nothing on import. See l2verify.py for the debug-mode trade list.
"""
import numpy as np
from numba import njit

# exit reason codes, kept as ints so they cross into the loop
STOP, TARGET, EXIT_IND, BASE_CROSS, C1_FLIP, REVERSAL, END = 1, 2, 3, 4, 5, 6, 7
# Leg 2's stop is one variable that means three different things depending on
# how far the trade has progressed, and collapsing them under STOP hides the
# distinction that matters: an initial stop is a loss, a breakeven stop is a
# scratch, a trail stop is a banked win. DIAGNOSTIC ONLY -- no price, size or
# fill logic reads these, so splitting them cannot move a single trade or R.
STOP_BE, STOP_TRAIL = 8, 9
REASON = {STOP: 'stop', TARGET: 'target', EXIT_IND: 'exit indicator',
          BASE_CROSS: 'baseline cross', C1_FLIP: 'c1 flip', REVERSAL: 'reversal',
          END: 'end of data', STOP_BE: 'breakeven stop', STOP_TRAIL: 'trail stop'}
# leg 1 never moves its stop (set at entry, never reassigned) and plan 1 has no
# leg 2 at all, so a plan-1 trade can only ever close on stop / target / signal.
LEG1, LEG2, SINGLE = 1, 2, 0


@njit(cache=True)
def run_bars(o, h, l, c, atr,
             bl,
             c1_lt, c1_st, c1_lc, c1_sc,
             c2_lc, c2_sc,
             v_ok_l, v_ok_s,
             x_el, x_es,
             suspect,
             c1_ternary, c2_ternary,
             use_base_cross, use_c1_flip, use_continuation,
             exit_on_c1_flip, exit_on_base_cross, exit_on_exit_ind,
             one_candle_rule,
             plan, risk_dollars,
             atr_mult, tp_mult, trail_mult, trail_start_mult, be_pct,
             max_atr_dist, bridge_bars,
             block_suspect, bridge_all_routes,
             t_entry_bar, t_exit_bar, t_dir, t_leg, t_entry_px, t_exit_px,
             t_units, t_r, t_reason, t_route):
    """The bar loop. Returns (n_trades, n_both_touched, n_blocked_late,
    n_blocked_stale). Trade fields are written into the t_* output arrays."""
    n = c.size
    nt = 0
    both_touched = 0
    blocked_late = 0
    blocked_stale = 0

    pos = 0                 # 0 flat, +1 long, -1 short
    entry_px = 0.0
    entry_bar = -1
    entry_atr = 0.0
    route = 0
    l1_open = False
    l2_open = False
    l1_stop = 0.0
    l1_tp = 0.0
    l2_stop = 0.0
    # GATE 2 LEG-2 MECHANICS. Phases:
    #   0  initial stop, TP1 not yet hit
    #   1  TP1 hit; frozen_close / frozen_atr recorded; waiting for the
    #      breakeven trigger. The stop has NOT moved yet.
    #   2  breakeven set (stop = entry); waiting for the trail to arm
    #   3  armed; trailing D x FROZEN atr behind the highest close since arming
    l2_phase = 0
    frozen_close = 0.0      # last COMPLETED close at the moment TP1 hit
    frozen_atr = 0.0        # ATR as of that same close -- never re-read
    units_leg = 0.0
    best_close = 0.0        # highest/lowest close SINCE ARMING, not since entry
    l1_idx = -1             # row in t_* for the open leg-1 record
    l2_idx = -1

    # baseline state
    last_cross_bar = -10000
    last_cross_dir = 0
    prev_side = 0

    # one-candle-rule pending trigger: direction, the bar it was raised, and the
    # SIGNAL BAR's confirmation verdict, carried forward deliberately
    pend_dir = 0
    pend_bar = -1

    # continuation bookkeeping: has the baseline been re-crossed since the exit
    crossed_since_exit = True
    last_exit_dir = 0

    for i in range(n):
        cl = c[i]
        a = atr[i]
        b = bl[i]
        bad = block_suspect and suspect[i]
        ok_ctx = (a == a) and (a > 0.0) and (b == b)   # NaN-safe: x != x is NaN

        # ---- baseline side and cross bookkeeping -------------------------
        side = 0
        if ok_ctx:
            if cl > b:
                side = 1
            elif cl < b:
                side = -1
        if ok_ctx and side != 0 and prev_side != 0 and side != prev_side:
            last_cross_bar = i
            last_cross_dir = side
            crossed_since_exit = True
        if side != 0:
            prev_side = side

        # ================= 1. resolve the open position intrabar ==========
        # set when leg 2's stop is amended inside this bar; the amended stop
        # cannot also be filled by this bar's range
        l2_moved = False
        if pos != 0 and not bad:
            hi = h[i]
            lo = l[i]
            if pos == 1:
                l1_hit_stop = l1_open and lo <= l1_stop
                l1_hit_tp = l1_open and hi >= l1_tp
                if l1_hit_stop and l1_hit_tp:
                    both_touched += 1
                if l1_open and l1_hit_stop:
                    t_exit_bar[l1_idx] = i; t_exit_px[l1_idx] = l1_stop
                    t_r[l1_idx] = ((l1_stop - entry_px) * units_leg) / risk_dollars
                    t_reason[l1_idx] = STOP
                    l1_open = False
                elif l1_open and l1_hit_tp:
                    t_exit_bar[l1_idx] = i; t_exit_px[l1_idx] = l1_tp
                    t_r[l1_idx] = ((l1_tp - entry_px) * units_leg) / risk_dollars
                    t_reason[l1_idx] = TARGET
                    l1_open = False
                    if l2_open and l2_phase == 0:
                        # TP1 hit intrabar. The most recent COMPLETED close is
                        # the PREVIOUS bar's -- this bar has not closed yet.
                        # Both it and its ATR are frozen here and never re-read;
                        # the trail deliberately does not follow current ATR.
                        l2_phase = 1
                        if i > 0:
                            frozen_close = c[i - 1]
                            frozen_atr = atr[i - 1]
                        else:
                            frozen_close = cl
                            frozen_atr = a
                if l2_open and not l2_moved and lo <= l2_stop:
                    t_exit_bar[l2_idx] = i; t_exit_px[l2_idx] = l2_stop
                    t_r[l2_idx] = ((l2_stop - entry_px) * units_leg) / risk_dollars
                    if l2_phase <= 1:
                        t_reason[l2_idx] = STOP          # still the initial stop
                    elif l2_phase == 2:
                        t_reason[l2_idx] = STOP_BE
                    else:
                        t_reason[l2_idx] = STOP_TRAIL
                    l2_open = False
            else:
                hi = h[i]; lo = l[i]
                l1_hit_stop = l1_open and hi >= l1_stop
                l1_hit_tp = l1_open and lo <= l1_tp
                if l1_hit_stop and l1_hit_tp:
                    both_touched += 1
                if l1_open and l1_hit_stop:
                    t_exit_bar[l1_idx] = i; t_exit_px[l1_idx] = l1_stop
                    t_r[l1_idx] = ((entry_px - l1_stop) * units_leg) / risk_dollars
                    t_reason[l1_idx] = STOP
                    l1_open = False
                elif l1_open and l1_hit_tp:
                    t_exit_bar[l1_idx] = i; t_exit_px[l1_idx] = l1_tp
                    t_r[l1_idx] = ((entry_px - l1_tp) * units_leg) / risk_dollars
                    t_reason[l1_idx] = TARGET
                    l1_open = False
                    if l2_open and l2_phase == 0:
                        l2_phase = 1
                        if i > 0:
                            frozen_close = c[i - 1]
                            frozen_atr = atr[i - 1]
                        else:
                            frozen_close = cl
                            frozen_atr = a
                if l2_open and not l2_moved and hi >= l2_stop:
                    t_exit_bar[l2_idx] = i; t_exit_px[l2_idx] = l2_stop
                    t_r[l2_idx] = ((entry_px - l2_stop) * units_leg) / risk_dollars
                    if l2_phase <= 1:
                        t_reason[l2_idx] = STOP          # still the initial stop
                    elif l2_phase == 2:
                        t_reason[l2_idx] = STOP_BE
                    else:
                        t_reason[l2_idx] = STOP_TRAIL
                    l2_open = False

            if not l1_open and not l2_open:
                pos = 0
                last_exit_dir = 0
                crossed_since_exit = False

        # ---- leg 2 phase progression, GATE 2 SPEC ------------------------
        # THIS DELIBERATELY DIVERGES FROM PINE AND FROM THE PREVIOUS ENGINE. It
        # is the new specification, not a port, and the differences are the
        # point rather than an accident:
        #
        #   frozen base   arming and trail measure from the last COMPLETED close
        #                 at the moment TP1 hit, and from the ATR as of that same
        #                 close. Neither is ever re-read. The old loop trailed on
        #                 CURRENT ATR, so a volatility expansion after TP1 widened
        #                 the trail and gave back profit that had already been
        #                 made; freezing the base stops volatility that arrives
        #                 after the decision from rewriting it.
        #   breakeven     no longer automatic when TP1 banks. Price must travel
        #                 X% of PRICE beyond TP1 first, so a target that is
        #                 tagged and immediately rejected does not scratch the
        #                 runner.
        #   best_close    highest close SINCE ARMING, not since entry and not
        #                 seeded at TP1.
        #   precedence    once breakeven is set the effective stop is
        #                 max(breakeven, trail) for a long. The trail takes over
        #                 only when it passes breakeven, and never drags the stop
        #                 back down. Stops move one way only, always.
        #
        # Triggers read the bar's HIGH/LOW ("price reaches"), the trail tracker
        # reads CLOSES. Phases can cascade within one bar. Anything set here
        # goes live on the NEXT bar -- the intrabar block above has already run,
        # which is what keeps a stop from being moved and filled by the same bar.
        if pos != 0 and l2_open and not bad:
            if pos == 1:
                if l2_phase == 1 and h[i] >= l1_tp * (1.0 + be_pct / 100.0):
                    l2_phase = 2
                    if entry_px > l2_stop:
                        l2_stop = entry_px
                if l2_phase == 2 and h[i] >= frozen_close + trail_start_mult * frozen_atr:
                    l2_phase = 3
                    best_close = cl                 # seeded AT ARMING
                if l2_phase == 3:
                    if cl > best_close:
                        best_close = cl
                    trail = best_close - trail_mult * frozen_atr
                    if entry_px > trail:            # breakeven is the floor
                        trail = entry_px
                    if trail > l2_stop:
                        l2_stop = trail
            else:
                if l2_phase == 1 and l[i] <= l1_tp * (1.0 - be_pct / 100.0):
                    l2_phase = 2
                    if entry_px < l2_stop:
                        l2_stop = entry_px
                if l2_phase == 2 and l[i] <= frozen_close - trail_start_mult * frozen_atr:
                    l2_phase = 3
                    best_close = cl
                if l2_phase == 3:
                    if cl < best_close:
                        best_close = cl
                    trail = best_close + trail_mult * frozen_atr
                    if entry_px < trail:            # breakeven is the ceiling
                        trail = entry_px
                    if trail < l2_stop:
                        l2_stop = trail

        # ================= 2. signals at the close ========================
        if bad or not ok_ctx:
            continue

        # ---- full exits --------------------------------------------------
        # EXACTLY ONE signal-exit mode is active per test; they are never
        # combined. The exit indicator and the baseline cross used to be
        # unconditional, which meant every test ran all three at once and the
        # first to fire won -- measured, the baseline cross took 44% of trend
        # closes and the exit indicator only 7%, so the exit slot was being
        # judged on the leftovers. The risk plan (stop, target, breakeven,
        # trail) is NOT a signal exit and stays active in every mode.
        if pos != 0:
            reason = 0
            if pos == 1:
                if exit_on_exit_ind and x_el[i]:
                    reason = EXIT_IND
                elif exit_on_base_cross and side == -1 and last_cross_bar == i:
                    reason = BASE_CROSS
                elif exit_on_c1_flip and c1_st[i]:
                    reason = C1_FLIP
            else:
                if exit_on_exit_ind and x_es[i]:
                    reason = EXIT_IND
                elif exit_on_base_cross and side == 1 and last_cross_bar == i:
                    reason = BASE_CROSS
                elif exit_on_c1_flip and c1_lt[i]:
                    reason = C1_FLIP
            if reason != 0:
                if l1_open:
                    t_exit_bar[l1_idx] = i; t_exit_px[l1_idx] = cl
                    t_r[l1_idx] = ((cl - entry_px) if pos == 1 else
                                   (entry_px - cl)) * units_leg / risk_dollars
                    t_reason[l1_idx] = reason
                    l1_open = False
                if l2_open:
                    t_exit_bar[l2_idx] = i; t_exit_px[l2_idx] = cl
                    t_r[l2_idx] = ((cl - entry_px) if pos == 1 else
                                   (entry_px - cl)) * units_leg / risk_dollars
                    t_reason[l2_idx] = reason
                    l2_open = False
                pos = 0
                last_exit_dir = 0
                crossed_since_exit = False

        # ---- what does each confirmation say on this bar -----------------
        agree_long = c1_lc[i] and c2_lc[i] and v_ok_l[i] and side == 1
        agree_short = c1_sc[i] and c2_sc[i] and v_ok_s[i] and side == -1
        # a neutral ternary blocks; a binary is never neutral so this is a no-op
        if c1_ternary and not c1_lc[i] and not c1_sc[i]:
            agree_long = False; agree_short = False
        if c2_ternary and not c2_lc[i] and not c2_sc[i]:
            agree_long = False; agree_short = False

        # ---- which route, if any, fires ---------------------------------
        # PINE EVALUATES THE THREE CONDITIONS INDEPENDENTLY AND ORS THEM:
        #     entry_long = longcondition1 or longcondition2 or longcondition3
        # and they do not carry the same blocks -- longcondition3 has no
        # Ind_BTF_Conf. So a bar can fail route 2 on Bridge Too Far and still be
        # taken by route 3.
        #
        # An earlier version of this loop picked ONE route by precedence and
        # then applied the blocks to it. On a bar qualifying for both the C1
        # flip and the continuation it chose the flip, the bridge refused it,
        # and the trade was lost -- GBPUSD 2008-02-19, found by running against
        # TradingView on identical bars. Each route is now tested with its OWN
        # blocks and the entry fires if ANY of them survives.
        stale = i - last_cross_bar > bridge_bars
        r1l = use_base_cross and last_cross_bar == i and side == 1 and agree_long
        r1s = use_base_cross and last_cross_bar == i and side == -1 and agree_short
        r2l = use_c1_flip and c1_lt[i] and agree_long
        r2s = use_c1_flip and c1_st[i] and agree_short
        cont = use_continuation and not crossed_since_exit
        r3l = cont and c1_lt[i] and agree_long
        r3s = cont and c1_st[i] and agree_short
        # the bridge gates routes 1 and 2 always, and route 3 only when the
        # fix is enabled (bridge_all_routes); the 1.5xATR block gates all three
        if stale:
            r1l = r1s = r2l = r2s = False
            if bridge_all_routes:
                r3l = r3s = False
        want = 0
        rt = 0
        if r1l or r2l or r3l:
            want = 1
            rt = 1 if r1l else (2 if r2l else 3)
        elif r1s or r2s or r3s:
            want = -1
            rt = 1 if r1s else (2 if r2s else 3)
        if want == 0 and (stale and (agree_long or agree_short)):
            blocked_stale += 1

        # ---- the one candle rule ----------------------------------------
        if one_candle_rule:
            if want == 0 and pend_dir != 0 and i == pend_bar + 1:
                # the deferred trigger, judged on the SIGNAL bar's verdict but
                # only if the baseline has now come onside
                if pend_dir == 1 and side == 1:
                    want = 1; rt = 4
                elif pend_dir == -1 and side == -1:
                    want = -1; rt = 4
            newpend = 0
            if want == 0 and use_c1_flip:
                # C1 flipped but the baseline was the wrong side -> hold one bar
                if c1_lt[i] and c1_lc[i] and c2_lc[i] and v_ok_l[i] and side != 1:
                    newpend = 1
                elif c1_st[i] and c1_sc[i] and c2_sc[i] and v_ok_s[i] and side != -1:
                    newpend = -1
            if newpend != 0:
                pend_dir = newpend; pend_bar = i
            elif i > pend_bar + 1:
                pend_dir = 0

        if want == 0:
            continue

        # ---- the two blocks, applied to EVERY route ---------------------
        # Pine's rule is ONE-SIDED: close < baseline + 1.5*atr for a long,
        # close > baseline - 1.5*atr for a short. With the baseline direction
        # gate already requiring price on the correct side the two readings
        # coincide, but the one-sided form is what the source says.
        if (want == 1 and cl > b + max_atr_dist * a) or \
           (want == -1 and cl < b - max_atr_dist * a):
            blocked_late += 1
            continue
        if want == pos:
            continue                      # already in it

        # ---- reverse out of an opposing position ------------------------
        if pos != 0:
            if l1_open:
                t_exit_bar[l1_idx] = i; t_exit_px[l1_idx] = cl
                t_r[l1_idx] = ((cl - entry_px) if pos == 1 else
                               (entry_px - cl)) * units_leg / risk_dollars
                t_reason[l1_idx] = REVERSAL
                l1_open = False
            if l2_open:
                t_exit_bar[l2_idx] = i; t_exit_px[l2_idx] = cl
                t_r[l2_idx] = ((cl - entry_px) if pos == 1 else
                               (entry_px - cl)) * units_leg / risk_dollars
                t_reason[l2_idx] = REVERSAL
                l2_open = False
            pos = 0

        # ---- open. EVERY piece of phase state is rebuilt here ------------
        stop_dist = atr_mult * a
        if stop_dist <= 0.0:
            continue
        pos = want
        entry_px = cl
        entry_bar = i
        entry_atr = a
        route = rt
        best_close = cl
        l2_phase = 0
        frozen_close = 0.0
        frozen_atr = 0.0
        if plan == 2:
            units_leg = (0.5 * risk_dollars) / stop_dist
            l1_stop = entry_px - want * stop_dist
            l1_tp = entry_px + want * tp_mult * a
            l2_stop = l1_stop
            l1_idx = nt; l2_idx = nt + 1
            t_entry_bar[nt] = i; t_dir[nt] = want; t_leg[nt] = 1
            t_entry_px[nt] = entry_px; t_units[nt] = units_leg
            t_route[nt] = rt; t_exit_bar[nt] = -1; t_reason[nt] = 0
            nt += 1
            t_entry_bar[nt] = i; t_dir[nt] = want; t_leg[nt] = 2
            t_entry_px[nt] = entry_px; t_units[nt] = units_leg
            t_route[nt] = rt; t_exit_bar[nt] = -1; t_reason[nt] = 0
            nt += 1
            l1_open = True; l2_open = True
        else:
            units_leg = risk_dollars / stop_dist
            l1_stop = entry_px - want * stop_dist
            l1_tp = entry_px + want * tp_mult * a
            l1_idx = nt; l2_idx = -1
            t_entry_bar[nt] = i; t_dir[nt] = want; t_leg[nt] = 0
            t_entry_px[nt] = entry_px; t_units[nt] = units_leg
            t_route[nt] = rt; t_exit_bar[nt] = -1; t_reason[nt] = 0
            nt += 1
            l1_open = True; l2_open = False
        pend_dir = 0

    # ---- close whatever is still open at the last bar --------------------
    if pos != 0:
        i = n - 1
        cl = c[i]
        if l1_open:
            t_exit_bar[l1_idx] = i; t_exit_px[l1_idx] = cl
            t_r[l1_idx] = ((cl - entry_px) if pos == 1 else
                           (entry_px - cl)) * units_leg / risk_dollars
            t_reason[l1_idx] = END
        if l2_open:
            t_exit_bar[l2_idx] = i; t_exit_px[l2_idx] = cl
            t_r[l2_idx] = ((cl - entry_px) if pos == 1 else
                           (entry_px - cl)) * units_leg / risk_dollars
            t_reason[l2_idx] = END
    return nt, both_touched, blocked_late, blocked_stale


# ==========================================================================
# the Python side: build the arrays, call the loop, summarise
# ==========================================================================
import l2lib as L


def _conf(name, o, h, l, c, params=None, as_written_mode=False):
    lt, st, lc, sc = L.compute(name, o, h, l, c, as_written_mode=as_written_mode,
                               **(params or {}))
    return lt, st, lc, sc, L.KIND[name] == 'TERNARY'


PRIMARY_FEED = 'oanda'     # decided 2026-08-15; see results/l2_feed_verdict.md


def load_pair(pair, feed=None):
    """THE SWEEP'S FEED IS OANDA DAILY MID.

    Decided on the evidence in results/l2_feed_verdict.md: the engine's parity
    proof is a proof about OANDA bars (185 of 189 entries against TradingView),
    winners must port back to TradingView whose FX charts are OANDA, and OANDA
    needs none of the four repairs Yahoo needed. The cost is history -- clean
    OANDA starts 2005-01-03 for all 28 pairs.

    THE LEADING PLACEHOLDER BLOCK IS DROPPED. OANDA's practice feed serves
    close-only bars (high = low = close, volume = 1) for its earliest years.
    They are not neutral: sma(high) then equals sma(low), SSL Channel confirms
    neither direction, and the engine trades nothing -- which reads as "no edge"
    rather than "no data".

    feed='yahoo' reaches the cleaned Yahoo set, which stays in the repo FROZEN
    as a cross-check. It is never mixed into a sweep: two feeds in one result is
    two experiments in one number.
    """
    import pandas as pd
    import numpy as np
    f = feed or PRIMARY_FEED
    if f == 'yahoo':
        return pd.read_csv(os.path.join(ROOTDATA, 'ohlc_clean', '%s.csv' % pair),
                           index_col=0, parse_dates=True)
    if f == 'yahoo_raw':
        return pd.read_csv(os.path.join(ROOTDATA, 'ohlc', '%s.csv' % pair),
                           index_col=0, parse_dates=True)
    d = pd.read_csv(os.path.join(ROOTDATA, 'oanda_ohlc', '%s_mid.csv' % pair),
                    index_col=0, parse_dates=True)
    flat = (d.high.values == d.low.values)
    i = 0
    while i < len(flat) and flat[i]:
        i += 1
    d = d.iloc[i:].copy()
    d['suspect'] = False
    return d


def prepare(d, c1, c2, vol, base, exit_ind, params=None, as_written_mode=False):
    """Everything the loop needs, computed ONCE per pair per slot. A sweep
    caches this per (pair, indicator) and reuses it across every combination
    that mentions it -- which is the whole reason the loop takes arrays."""
    params = params or {}
    # as_written_mode reaches the pre-V9.1 functions. l2parity.py only.
    aw = dict(as_written_mode=as_written_mode)
    o, h, l, c = (d[k].values.astype(float) for k in ('open', 'high', 'low', 'close'))
    A = {}
    A['o'], A['h'], A['l'], A['c'] = o, h, l, c
    A['atr'] = L.P.atr(h, l, c, params.get('atr_len', 14))
    A['bl'] = L.compute(base, o, h, l, c, **aw, **params.get(base, {}))
    c1_lt, c1_st, c1_lc, c1_sc, c1_t = _conf(c1, o, h, l, c, params.get(c1), as_written_mode)
    c2_lt, c2_st, c2_lc, c2_sc, c2_t = _conf(c2, o, h, l, c, params.get(c2), as_written_mode)
    A.update(c1_lt=c1_lt, c1_st=c1_st, c1_lc=c1_lc, c1_sc=c1_sc,
             c2_lc=c2_lc, c2_sc=c2_sc, c1_ternary=c1_t, c2_ternary=c2_t)
    A['v_ok_l'], A['v_ok_s'] = L.compute(vol, o, h, l, c, **aw, **params.get(vol, {}))
    # the exit slot has its OWN Pine helper (*_exit) returning [le, se]; it is
    # not the confirmation read backwards. ssl_channel_exit and
    # ssl_channel_signals happen to coincide, but donchian_breakout_exit is a
    # midline cross while its signals are channel breaks -- different bars.
    A['x_el'], A['x_es'] = L.compute(exit_ind, o, h, l, c, **aw, **params.get(exit_ind, {}))
    A['suspect'] = (d['suspect'].values.astype(bool) if 'suspect' in d.columns
                    else np.zeros(len(d), bool))
    return A


def run(A, plan=2, risk_dollars=200.0, atr_mult=1.0, tp_mult=1.5,
        trail_mult=1.5, trail_start_mult=2.0, be_pct=0.05,
        max_atr_dist=1.5, bridge_bars=7,
        use_base_cross=True, use_c1_flip=True, use_continuation=True,
        exit_on_c1_flip=False, exit_on_base_cross=True, exit_on_exit_ind=True,
        one_candle_rule=False, block_suspect=True,
        bridge_all_routes=True):
    n = A['c'].size
    cap = 4 * n + 8                      # a hard ceiling on trade records
    t = {k: np.zeros(cap, dt) for k, dt in
         (('entry_bar', np.int64), ('exit_bar', np.int64), ('dir', np.int64),
          ('leg', np.int64), ('reason', np.int64), ('route', np.int64))}
    for k in ('entry_px', 'exit_px', 'units', 'r'):
        t[k] = np.zeros(cap, np.float64)
    nt, both, late, stale = run_bars(
        A['o'], A['h'], A['l'], A['c'], A['atr'], A['bl'],
        A['c1_lt'], A['c1_st'], A['c1_lc'], A['c1_sc'],
        A['c2_lc'], A['c2_sc'], A['v_ok_l'], A['v_ok_s'],
        A['x_el'], A['x_es'], A['suspect'],
        A['c1_ternary'], A['c2_ternary'],
        use_base_cross, use_c1_flip, use_continuation,
        exit_on_c1_flip, exit_on_base_cross, exit_on_exit_ind,
        one_candle_rule,
        int(plan), float(risk_dollars),
        float(atr_mult), float(tp_mult), float(trail_mult),
        float(trail_start_mult), float(be_pct),
        float(max_atr_dist), int(bridge_bars), bool(block_suspect),
        bool(bridge_all_routes),
        t['entry_bar'], t['exit_bar'], t['dir'], t['leg'], t['entry_px'],
        t['exit_px'], t['units'], t['r'], t['reason'], t['route'])
    out = {k: v[:nt] for k, v in t.items()}
    out['_n'] = nt; out['_both_touched'] = both
    out['_blocked_late'] = late; out['_blocked_stale'] = stale
    return out


def summary(res, dates=None, label=''):
    """Money metrics -- permitted here, this is Layer 2. Everything is in R, so
    it does not depend on account size or on the order the trades fell in."""
    r = res['r'][:res['_n']]
    n = len(r)
    if n == 0:
        return dict(label=label, trades=0)
    win = r > 0
    gains = r[win].sum(); losses = -r[~win].sum()
    eq = np.cumsum(r)
    peak = np.maximum.accumulate(eq)
    dd = peak - eq
    mdd = float(dd.max())
    dn = r[r < 0]
    sd = r.std(ddof=1) if n > 1 else 0.0
    dsd = dn.std(ddof=1) if dn.size > 1 else 0.0
    # ulcer index over the trade-indexed equity curve, in R
    ulcer = float(np.sqrt(np.mean(np.square(dd))))
    s = dict(label=label, trades=n,
             expectancy_R=float(r.mean()),
             total_R=float(r.sum()),
             win_rate=float(win.mean()),
             avg_win_R=float(r[win].mean()) if win.any() else 0.0,
             avg_loss_R=float(r[~win].mean()) if (~win).any() else 0.0,
             profit_factor=float(gains / losses) if losses > 0 else np.inf,
             sharpe=float(r.mean() / sd * np.sqrt(n)) if sd > 0 else 0.0,
             sortino=float(r.mean() / dsd * np.sqrt(n)) if dsd > 0 else 0.0,
             max_dd_R=mdd,
             calmar=float(r.sum() / mdd) if mdd > 0 else np.inf,
             ulcer_R=ulcer,
             both_touched=res['_both_touched'],
             blocked_late=res['_blocked_late'],
             blocked_stale=res['_blocked_stale'])
    return s


def trade_frame(res, d):
    """DEBUG MODE ONLY -- per-trade records. Never called at sweep scale."""
    import pandas as pd
    n = res['_n']
    idx = d.index
    T = pd.DataFrame(dict(
        leg=res['leg'][:n], direction=res['dir'][:n],
        entry_date=idx[res['entry_bar'][:n]],
        entry_px=res['entry_px'][:n],
        exit_date=idx[np.clip(res['exit_bar'][:n], 0, len(idx) - 1)],
        exit_px=res['exit_px'][:n],
        units=res['units'][:n], R=res['r'][:n],
        reason=[REASON.get(x, '?') for x in res['reason'][:n]],
        route=[{1: 'baseline cross', 2: 'c1 flip', 3: 'continuation',
                4: 'one candle rule'}.get(x, '?') for x in res['route'][:n]]))
    T['leg'] = T.leg.map({0: 'single', 1: 'leg1', 2: 'leg2'})
    T['direction'] = T.direction.map({1: 'long', -1: 'short'})
    T['bars_held'] = res['exit_bar'][:n] - res['entry_bar'][:n]
    return T


# The strategy file's own defaults: IND_1 SSL Channel, IND_2 DSPO, IND_3
# Variance, baseline Triangular Moving Average, IND_5 SSL Channel. This is the
# combination Phase 3 compares against TradingView.
DEFAULT_SLOTS = dict(c1='ssl_channel_signals', c2='dspo_signals',
                     vol='variance_volume_signals', base='tma_baseline',
                     exit_ind='ssl_channel_exit')


def run_all_pairs(slots=None, pairs=None, ckpt=None, params=None, **kw):
    """Every pair, one combination, with a per-pair checkpoint.

    RESUMABLE BY PAIR. A killed run costs the pair in flight, not the run: each
    finished pair is appended to the checkpoint CSV and skipped on restart. At
    0.09 ms a pair this is pointless for ONE combination -- it exists because
    the sweep will drive the same function across millions of them, and a
    resume mechanism bolted on afterwards is a resume mechanism that has never
    been tested."""
    import pandas as pd
    slots = dict(DEFAULT_SLOTS, **(slots or {}))
    pairs = pairs or sorted(x[:-4] for x in os.listdir(os.path.join(ROOTDATA, 'ohlc_clean'))
                            if x.endswith('.csv'))
    # THE CHECKPOINT IS KEYED ON THE COMBINATION, NOT JUST THE PAIR. Keying it
    # on the pair alone means resuming a DIFFERENT combination silently returns
    # the previous one's numbers -- which is what happened the first time this
    # ran, reporting an SSL/DSPO/Variance/TMA result that was actually PSAR's,
    # in 0.01s, with no error. At sweep scale that is a wrong answer that looks
    # like a fast one.
    sig = '|'.join('%s=%s' % (k, slots[k]) for k in sorted(slots))
    sig += '||' + '|'.join('%s=%s' % kv for kv in sorted(kw.items()))
    done, rows = set(), []
    if ckpt and os.path.exists(ckpt):
        old = pd.read_csv(ckpt)
        if 'combo' in old.columns and set(old.combo.unique()) == {sig}:
            rows = old.to_dict('records'); done = set(old.label)
        else:
            print('  checkpoint is for a different combination -- recomputing')
    for p in pairs:
        if p in done:
            continue
        d = load_pair(p)
        A = prepare(d, slots['c1'], slots['c2'], slots['vol'], slots['base'],
                    slots['exit_ind'], params)
        s = summary(run(A, **kw), label=p)
        s['bars'] = len(d); s['first'] = str(d.index.min().date())
        s['combo'] = sig
        rows.append(s)
        if ckpt:
            pd.DataFrame(rows).to_csv(ckpt, index=False)
    return pd.DataFrame(rows)


def pooled(P):
    """Pool the per-pair rows the way the funnel will: trade-weighted, plus the
    count of pairs that stand on their own. 'Positive on multiple pairs' is a
    stage-1 criterion, so the per-pair sign count is part of the output, not a
    diagnostic printed and thrown away."""
    n = P.trades.sum()
    return dict(pairs=len(P), trades=int(n),
                expectancy_R=float((P.expectancy_R * P.trades).sum() / n) if n else 0.0,
                total_R=float(P.total_R.sum()),
                pairs_positive=int((P.total_R > 0).sum()),
                worst_pair_R=float(P.total_R.min()),
                best_pair_R=float(P.total_R.max()),
                both_touched=int(P.both_touched.sum()),
                blocked_late=int(P.blocked_late.sum()),
                blocked_stale=int(P.blocked_stale.sum()))


def main():
    import pandas as pd, time
    ck = os.path.join(ROOTOUT, 'l2_engine_perpair.csv')
    t = time.time()
    P = run_all_pairs(ckpt=ck, plan=2)
    el = time.time() - t
    pd.set_option('display.width', 240)
    print('ENGINE ACROSS 28 PAIRS -- %s, two-leg plan'
          % ' / '.join('%s=%s' % kv for kv in DEFAULT_SLOTS.items()))
    print(P[['label', 'bars', 'first', 'trades', 'expectancy_R', 'total_R',
             'win_rate', 'profit_factor', 'sortino', 'max_dd_R',
             'blocked_late', 'blocked_stale']]
          .to_string(index=False, float_format=lambda v: '%.4f' % v))
    print('\nPOOLED: %s' % pooled(P))
    print('\n%d pairs in %.2fs (%.1f ms/pair including the CSV read)'
          % (len(P), el, 1000 * el / max(len(P), 1)))
    print('wrote %s' % ck)
    return P


if __name__ == '__main__':
    main()
