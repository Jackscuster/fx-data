import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""HAND-CHECKED VERIFICATION OF THE GATE 2 LEG-2 MECHANICS.

Every case below is built so that each level is computable on paper, and the
EXPECTED value is written out longhand before the engine is asked. A test whose
expectation is derived from the engine's own output proves only that the engine
is consistent with itself.

The synthetic series feeds run_bars directly with hand-made signal arrays, so
no indicator, no registry and no data file is involved -- only the mechanics.

WHAT IS BEING CHECKED, and why each one can silently be wrong:
  1  frozen base      the close and ATR are taken from the PREVIOUS bar at the
                      moment TP1 hits, not this bar's. Off by one here is
                      invisible in aggregate and changes every trail.
  2  frozen ATR       a volatility expansion AFTER TP1 must not widen the trail.
                      The old engine used current ATR and would.
  3  breakeven gate   TP1 tagged but not exceeded by X% must NOT set breakeven.
  4  precedence       once breakeven is set the stop is max(BE, trail); a trail
                      computed below entry must not drag the stop down.
  5  one-way          stops never retreat, even as best_close stalls.
  6  next-bar rule    a stop moved on bar i cannot also fill on bar i.
"""
import numpy as np
import l2engine as E

ATR = 1.0            # constant ATR everywhere except case 2
N = 40


def _blank(n):
    """Flat signal arrays: no entries, no exits, nothing confirms."""
    z = lambda dt=bool: np.zeros(n, dt)
    return dict(c1_lt=z(), c1_st=z(), c1_lc=z(), c1_sc=z(),
                c2_lc=z(), c2_sc=z(), v_ok_l=z(), v_ok_s=z(),
                x_el=z(), x_es=z(), suspect=z())


def run(o, h, l, c, atr, bl, sig, plan=2, **kw):
    n = len(c)
    cap = 4 * n + 8
    t = {k: np.zeros(cap, np.int64) for k in
         ('entry_bar', 'exit_bar', 'dir', 'leg', 'reason', 'route')}
    for k in ('entry_px', 'exit_px', 'units', 'r'):
        t[k] = np.zeros(cap, np.float64)
    p = dict(atr_mult=1.0, tp_mult=1.5, trail_mult=1.0, trail_start_mult=1.0,
             be_pct=0.05, max_atr_dist=1e9, bridge_bars=10 ** 6,
             use_base_cross=True, use_c1_flip=True, use_continuation=False,
             exit_on_c1_flip=False, exit_on_base_cross=False,
             exit_on_exit_ind=False, one_candle_rule=False,
             block_suspect=True, bridge_all_routes=True, risk_dollars=100.0)
    p.update(kw)
    nt, both, late, stale = E.run_bars(
        o, h, l, c, atr, bl,
        sig['c1_lt'], sig['c1_st'], sig['c1_lc'], sig['c1_sc'],
        sig['c2_lc'], sig['c2_sc'], sig['v_ok_l'], sig['v_ok_s'],
        sig['x_el'], sig['x_es'], sig['suspect'],
        False, False,
        p['use_base_cross'], p['use_c1_flip'], p['use_continuation'],
        p['exit_on_c1_flip'], p['exit_on_base_cross'], p['exit_on_exit_ind'],
        p['one_candle_rule'], int(plan), float(p['risk_dollars']),
        float(p['atr_mult']), float(p['tp_mult']), float(p['trail_mult']),
        float(p['trail_start_mult']), float(p['be_pct']),
        float(p['max_atr_dist']), int(p['bridge_bars']),
        bool(p['block_suspect']), bool(p['bridge_all_routes']),
        t['entry_bar'], t['exit_bar'], t['dir'], t['leg'], t['entry_px'],
        t['exit_px'], t['units'], t['r'], t['reason'], t['route'])
    return {k: v[:nt] for k, v in t.items()}


def long_entry_at(sig, bar):
    """A baseline-cross long on `bar`: everything confirms on that bar only."""
    for k in ('c1_lt', 'c1_lc', 'c2_lc', 'v_ok_l'):
        sig[k][bar] = True


CASES = []


def case(fn):
    CASES.append(fn)
    return fn


# ==========================================================================
@case
def case1_frozen_base_is_previous_bar():
    """TP1 hits on bar 6. The frozen close must be bar 5's close, NOT bar 6's.

    Entry  bar 3 at 100.0, ATR 1.0, stop 99.0, TP1 = 100 + 1.5*1 = 101.5
    bar 5 closes at 100.4   <- this is the frozen close
    bar 6 high 101.51 -> TP1 fills at 101.5. NOTE the high must stay under the
        breakeven threshold below, or breakeven fires on this same bar --
        which is legal and correct, and was an error in the first draft of
        this test rather than in the engine.
    Arming M=1.0 -> needs high >= frozen_close + 1.0*ATR = 101.4
    Breakeven X=0.05% of 101.5 = 0.050750 -> needs high >= 101.550750

    Bar 7 high 101.56 clears breakeven (101.5508) and also clears arming
    (101.4), so both fire on bar 7 and the trail seeds at bar 7's close.
    Bar 7 close 101.50 -> best_close 101.50, trail = 101.50 - 1.0 = 100.50
    Breakeven floor is entry 100.0, so effective stop = max(100.0, 100.50)
                                                     = 100.50, live on bar 8.
    Bar 8 low 100.40 takes it -> exit at 100.50, reason = trail stop.
    R = (100.50 - 100.0) * units / 100, units = 50/1.0 = 50 -> 0.25 R
    """
    n = 12
    c = np.full(n, 100.0); o = c.copy(); h = c.copy(); l = c.copy()
    bl = np.full(n, 99.5)
    c[5] = 100.4; h[5] = 100.45; l[5] = 100.0
    h[6] = 101.51; c[6] = 101.45; l[6] = 100.3      # fills TP1, under the X gate
    h[7] = 101.56; c[7] = 101.50; l[7] = 101.0
    h[8] = 101.00; c[8] = 100.45; l[8] = 100.40
    sig = _blank(n); long_entry_at(sig, 3)
    r = run(o, h, l, c, np.full(n, ATR), bl, sig,
            trail_mult=1.0, trail_start_mult=1.0, be_pct=0.05)
    leg2 = [i for i in range(len(r['leg'])) if r['leg'][i] == 2]
    assert leg2, 'no leg 2 recorded'
    i = leg2[0]
    got_px, got_reason, got_r = r['exit_px'][i], r['reason'][i], r['r'][i]
    exp_px, exp_reason, exp_r = 100.50, E.STOP_TRAIL, 0.25
    ok = (abs(got_px - exp_px) < 1e-9 and got_reason == exp_reason
          and abs(got_r - exp_r) < 1e-9)
    return ok, ('exit %.6f (exp %.6f), reason %s (exp %s), R %.6f (exp %.6f)'
                % (got_px, exp_px, E.REASON.get(got_reason), E.REASON.get(exp_reason),
                   got_r, exp_r))


@case
def case2_atr_expansion_after_tp1_is_ignored():
    """Identical to case 1 except ATR EXPLODES to 5.0 from bar 6 onward.

    Because the ATR is frozen at bar 5's value (1.0), every level must be
    unchanged: trail still 100.50, exit still 100.50, R still 0.25.
    The old engine trailed on CURRENT atr and would have used 5.0, putting the
    trail at 101.50 - 5.0 = 96.50, below breakeven, and the trade would have
    survived bar 8 entirely. A silent, large difference.
    """
    n = 12
    c = np.full(n, 100.0); o = c.copy(); h = c.copy(); l = c.copy()
    bl = np.full(n, 99.5)
    c[5] = 100.4; h[5] = 100.45; l[5] = 100.0
    h[6] = 101.51; c[6] = 101.45; l[6] = 100.3      # fills TP1, under the X gate
    h[7] = 101.56; c[7] = 101.50; l[7] = 101.0
    h[8] = 101.00; c[8] = 100.45; l[8] = 100.40
    atr = np.full(n, ATR); atr[6:] = 5.0
    sig = _blank(n); long_entry_at(sig, 3)
    r = run(o, h, l, c, atr, bl, sig,
            trail_mult=1.0, trail_start_mult=1.0, be_pct=0.05)
    leg2 = [i for i in range(len(r['leg'])) if r['leg'][i] == 2]
    assert leg2, 'no leg 2 recorded'
    i = leg2[0]
    ok = (abs(r['exit_px'][i] - 100.50) < 1e-9
          and r['reason'][i] == E.STOP_TRAIL and abs(r['r'][i] - 0.25) < 1e-9)
    return ok, ('exit %.6f (exp 100.500000 -- unchanged by the ATR jump), R %.6f'
                % (r['exit_px'][i], r['r'][i]))


@case
def case3_breakeven_requires_X_beyond_tp1():
    """TP1 is tagged and price stalls just under the X% threshold.

    TP1 = 101.5, X = 0.05% -> breakeven needs high >= 101.550750.
    Every later high is 101.54, which is ABOVE TP1 but BELOW the threshold, so
    breakeven must never be set and leg 2 must still be on its INITIAL stop of
    99.0. Bar 9 low 98.9 takes it: exit 99.0, reason plain 'stop', R = -0.5
    (half the risk, because leg 2 is half the position).

    Under the old rule breakeven was automatic the moment leg 1 banked, so this
    trade would have scratched at 100.0 for 0 R instead of losing.
    """
    n = 12
    c = np.full(n, 100.0); o = c.copy(); h = c.copy(); l = c.copy()
    bl = np.full(n, 99.5)
    h[6] = 101.52; c[6] = 101.20; l[6] = 100.3      # tags TP1, under the X gate
    for b in (7, 8):
        h[b] = 101.54; c[b] = 101.00; l[b] = 100.5
    h[9] = 100.20; c[9] = 99.00; l[9] = 98.90
    sig = _blank(n); long_entry_at(sig, 3)
    r = run(o, h, l, c, np.full(n, ATR), bl, sig,
            trail_mult=1.0, trail_start_mult=1.0, be_pct=0.05)
    leg2 = [i for i in range(len(r['leg'])) if r['leg'][i] == 2]
    assert leg2, 'no leg 2 recorded'
    i = leg2[0]
    ok = (abs(r['exit_px'][i] - 99.0) < 1e-9 and r['reason'][i] == E.STOP
          and abs(r['r'][i] - (-0.5)) < 1e-9)
    return ok, ('exit %.6f (exp 99.000000), reason %s (exp stop), R %.6f (exp -0.500000)'
                % (r['exit_px'][i], E.REASON.get(r['reason'][i]), r['r'][i]))


@case
def case4_breakeven_is_the_floor_under_a_low_trail():
    """Armed, but the trail level sits BELOW entry.

    D = 3.0 and the frozen ATR is 1.0, so trail = best_close - 3.0. With
    best_close 101.50 that is 98.50 -- below the entry of 100.0 and below even
    the initial stop of 99.0. Precedence says the effective stop is
    max(breakeven, trail) = max(100.0, 98.50) = 100.0.

    So bar 9's low of 99.5 must take the trade out at 100.0 for 0 R, flagged as
    a breakeven stop. If precedence were wrong the stop would have been dragged
    to 98.50 and the bar would not have touched it at all.
    """
    n = 12
    c = np.full(n, 100.0); o = c.copy(); h = c.copy(); l = c.copy()
    bl = np.full(n, 99.5)
    c[5] = 100.4; h[5] = 100.45; l[5] = 100.0
    h[6] = 101.51; c[6] = 101.45; l[6] = 100.3
    h[7] = 101.56; c[7] = 101.50; l[7] = 101.0
    h[8] = 101.20; c[8] = 101.10; l[8] = 100.8
    h[9] = 100.90; c[9] = 99.80; l[9] = 99.50
    sig = _blank(n); long_entry_at(sig, 3)
    r = run(o, h, l, c, np.full(n, ATR), bl, sig,
            trail_mult=3.0, trail_start_mult=1.0, be_pct=0.05)
    leg2 = [i for i in range(len(r['leg'])) if r['leg'][i] == 2]
    assert leg2, 'no leg 2 recorded'
    i = leg2[0]
    ok = (abs(r['exit_px'][i] - 100.0) < 1e-9 and abs(r['r'][i]) < 1e-9
          and r['reason'][i] in (E.STOP_BE, E.STOP_TRAIL))
    return ok, ('exit %.6f (exp 100.000000 = breakeven floor), R %.6f (exp 0), reason %s'
                % (r['exit_px'][i], r['r'][i], E.REASON.get(r['reason'][i])))


@case
def case5_stop_never_retreats():
    """best_close peaks, then closes fall back. The stop must hold its high.

    Trail D = 1.0 on frozen ATR 1.0.
      bar 7 close 101.50 -> best 101.50, trail 100.50
      bar 8 close 102.50 -> best 102.50, trail 101.50   <- the high-water stop
      bar 9 close 101.00 -> best UNCHANGED at 102.50, trail still 101.50
    Bar 10 low 101.40 must therefore fill at 101.50, not at anything lower.
    R = (101.50 - 100.0) * 50 / 100 = 0.75
    """
    n = 14
    c = np.full(n, 100.0); o = c.copy(); h = c.copy(); l = c.copy()
    bl = np.full(n, 99.5)
    c[5] = 100.4; h[5] = 100.45; l[5] = 100.0
    h[6] = 101.51; c[6] = 101.45; l[6] = 100.3
    h[7] = 101.56; c[7] = 101.50; l[7] = 101.0
    h[8] = 102.60; c[8] = 102.50; l[8] = 101.4
    h[9] = 102.55; c[9] = 101.00; l[9] = 100.9
    h[10] = 101.90; c[10] = 101.45; l[10] = 101.40
    sig = _blank(n); long_entry_at(sig, 3)
    r = run(o, h, l, c, np.full(n, ATR), bl, sig,
            trail_mult=1.0, trail_start_mult=1.0, be_pct=0.05)
    leg2 = [i for i in range(len(r['leg'])) if r['leg'][i] == 2]
    assert leg2, 'no leg 2 recorded'
    i = leg2[0]
    ok = (abs(r['exit_px'][i] - 101.50) < 1e-9 and abs(r['r'][i] - 0.75) < 1e-9)
    return ok, ('exit %.6f (exp 101.500000 = high-water trail), R %.6f (exp 0.750000)'
                % (r['exit_px'][i], r['r'][i]))


@case
def case6_moved_stop_cannot_fill_on_the_same_bar():
    """The stop set on bar 7 is 100.50, and bar 7's own low is 100.45.

    A stop amended during a bar goes live on the NEXT bar, so bar 7 must NOT
    fill it. Bar 8's low of 100.40 does. The trade must therefore exit on bar 8
    at 100.50 -- not on bar 7. Getting this wrong reads as a slightly better
    fill and is nearly impossible to spot in aggregate.
    """
    n = 12
    c = np.full(n, 100.0); o = c.copy(); h = c.copy(); l = c.copy()
    bl = np.full(n, 99.5)
    c[5] = 100.4; h[5] = 100.45; l[5] = 100.0
    h[6] = 101.51; c[6] = 101.45; l[6] = 100.3      # fills TP1, under the X gate
    h[7] = 101.56; c[7] = 101.50; l[7] = 100.45     # dips below the new stop
    h[8] = 101.00; c[8] = 100.45; l[8] = 100.40
    sig = _blank(n); long_entry_at(sig, 3)
    r = run(o, h, l, c, np.full(n, ATR), bl, sig,
            trail_mult=1.0, trail_start_mult=1.0, be_pct=0.05)
    leg2 = [i for i in range(len(r['leg'])) if r['leg'][i] == 2]
    assert leg2, 'no leg 2 recorded'
    i = leg2[0]
    ok = (r['exit_bar'][i] == 8 and abs(r['exit_px'][i] - 100.50) < 1e-9)
    return ok, ('exit bar %d (exp 8, NOT 7), price %.6f (exp 100.500000)'
                % (r['exit_bar'][i], r['exit_px'][i]))


def main():
    print('GATE 2 LEG-2 MECHANICS -- hand-checked cases\n' + '=' * 70)
    fails = 0
    for fn in CASES:
        try:
            ok, detail = fn()
        except Exception as e:
            ok, detail = False, 'EXCEPTION %r' % (e,)
        print('%-4s %-46s %s' % ('PASS' if ok else 'FAIL',
                                 fn.__name__, detail))
        fails += (not ok)
    print('=' * 70)
    print('%d/%d passed' % (len(CASES) - fails, len(CASES)))
    if fails:
        raise SystemExit('LEG-2 MECHANICS NOT VERIFIED -- tuning must not start')
    return True


if __name__ == '__main__':
    main()
