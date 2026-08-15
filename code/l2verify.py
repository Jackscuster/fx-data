import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""ENGINE VERIFICATION. Known-answer tests on synthetic bars, then a debug run.

WHY SYNTHETIC. Phase 3 compares the engine against TradingView trade by trade,
which tests the engine and the whole indicator library at once -- so when it
disagrees, it does not say which one is wrong. These tests drive run_bars with
hand-built indicator arrays on prices whose arithmetic is doable on paper. If
one fails, the engine is wrong; nothing else can be blamed.

Each case states the expected R before it runs, and the expectation is derived
from the risk rules, not from a previous run of this code.

  ATR is pinned at 1.0 and risk at 100 units throughout, so one ATR of adverse
  movement is exactly -1R on a one-leg plan and -0.5R on each leg of a two-leg
  plan. Every number below can be checked by hand.

Writes results/l2_engine_tests.csv and, for the debug run,
results/l2_debug_trades.csv.
"""
import numpy as np
import l2engine as E

N = 60
FAIL = []


CROSS = 8          # every fixture crosses its baseline here


def blank(n=N, price=100.0, bl_after=None):
    """A flat market with every gate open and no signal, EXCEPT that the
    baseline is crossed upward at bar CROSS.

    That cross is not decoration. Bridge Too Far blocks any entry more than
    `bridge_bars` after the last baseline cross, so a fixture with no cross at
    all has every entry correctly refused and tests nothing -- which is how the
    first version of this file failed against a working engine."""
    c = np.full(n, price)
    bl = np.full(n, price + 0.5)                  # price BELOW the baseline...
    bl[CROSS:] = price - 0.5 if bl_after is None else bl_after   # ...then above
    A = dict(o=c.copy(), h=c.copy(), l=c.copy(), c=c.copy(),
             atr=np.ones(n), bl=bl,
             c1_lt=np.zeros(n, bool), c1_st=np.zeros(n, bool),
             c1_lc=np.ones(n, bool), c1_sc=np.zeros(n, bool),
             c2_lc=np.ones(n, bool), c2_sc=np.zeros(n, bool),
             v_ok_l=np.ones(n, bool), v_ok_s=np.ones(n, bool),
             x_el=np.zeros(n, bool), x_es=np.zeros(n, bool),
             suspect=np.zeros(n, bool), c1_ternary=False, c2_ternary=False)
    return A


def bars(A, i, price, hi=None, lo=None):
    """Set bar i's close, and its high/low if the test needs a range."""
    A['c'][i] = price; A['o'][i] = price
    A['h'][i] = price if hi is None else hi
    A['l'][i] = price if lo is None else lo


def fire_c1_long(A, i):
    A['c1_lt'][i] = True


def check(name, got, want, tol=1e-9, note=''):
    ok = abs(got - want) <= tol if isinstance(want, float) else got == want
    print('  %-56s %-12s expected %-12s %s%s'
          % (name, _fmt(got), _fmt(want), 'PASS' if ok else '*** FAIL ***',
             ('   ' + note) if note else ''))
    if not ok:
        FAIL.append(name)
    return ok


def _fmt(v):
    return ('%.6g' % v) if isinstance(v, float) else str(v)


def go(A, **kw):
    kw.setdefault('risk_dollars', 100.0)
    kw.setdefault('use_base_cross', False)
    kw.setdefault('use_continuation', False)
    kw.setdefault('one_candle_rule', False)
    return E.run(A, **kw)


# --------------------------------------------------------------------------
def t_sizing_and_full_stop():
    """One leg, price falls one ATR below entry: exactly -1R. The stop is
    1xATR and the size is risk/stop, so this is the definition of R."""
    print('\n1. SIZING -- a 1xATR adverse move is exactly -1R (one-leg plan)')
    A = blank(); fire_c1_long(A, 10)
    for i in range(11, N):
        bars(A, i, 98.5, hi=98.5, lo=98.5)     # 1.5 below the 100.0 entry
    r = go(A, plan=1)
    check('trades', r['_n'], 1)
    check('R on a full stop', float(r['r'][0]), -1.0)
    check('units = risk / (1 x ATR)', float(r['units'][0]), 100.0)
    check('exit reason', E.REASON[r['reason'][0]], 'stop')


def t_two_leg_target():
    """Two legs, 50/50. Leg 1 targets 1.5xATR, so it banks +0.75R (half of
    1.5R). Leg 2 has no target and must still be open."""
    print('\n2. TWO-LEG PLAN -- leg 1 banks +0.75R at 1.5xATR, leg 2 runs on')
    A = blank(); fire_c1_long(A, 10)
    for i in range(11, N):
        bars(A, i, 101.5, hi=101.6, lo=101.4)
    r = go(A, plan=2)
    check('trade records (2 legs)', r['_n'], 2)
    check('leg 1 R at target', float(r['r'][0]), 0.75)
    check('leg 1 reason', E.REASON[r['reason'][0]], 'target')
    check('leg 2 still open at bar 11', bool(r['exit_bar'][1] > 11), True)


def t_leg2_breakeven():
    """The moment leg 1 banks, leg 2's stop goes to the entry price. Price then
    falls back through entry: leg 2 exits at exactly 0R, not at -0.5R."""
    print('\n3. LEG 2 -> BREAKEVEN the moment leg 1 banks')
    A = blank(); fire_c1_long(A, 10)
    bars(A, 11, 101.5, hi=101.6, lo=100.0)      # leg 1 target touched here
    for i in range(12, N):
        bars(A, i, 99.0, hi=100.2, lo=99.0)     # back through the entry
    r = go(A, plan=2)
    check('leg 1 R', float(r['r'][0]), 0.75)
    check('leg 2 R at breakeven', float(r['r'][1]), 0.0)
    check('leg 2 exit price == entry', float(r['exit_px'][1]), 100.0)


def t_leg2_trailing():
    """Leg 2 trails 1.5xATR behind the HIGHEST CLOSE, and only once the trade is
    2xATR in profit. Highest close 105 -> stop 103.5 -> +3.5 on a half leg is
    +1.75R."""
    print('\n4. LEG 2 -> TRAILING 1.5xATR behind the highest close, after 2xATR')
    A = blank(); fire_c1_long(A, 10)
    bars(A, 11, 101.5, hi=101.6, lo=100.0)      # leg 1 banks, leg 2 -> breakeven
    bars(A, 12, 103.0, hi=103.1, lo=101.4)      # 3.0 profit: past the 2xATR gate
    bars(A, 13, 105.0, hi=105.1, lo=102.9)      # highest close 105 -> trail 103.5
    for i in range(14, N):
        bars(A, i, 102.0, hi=104.0, lo=102.0)   # ...low 102 takes the trail out
    r = go(A, plan=2)
    check('leg 2 exit price = 105 - 1.5', float(r['exit_px'][1]), 103.5)
    check('leg 2 R', float(r['r'][1]), 1.75)
    check('leg 2 reason', E.REASON[r['reason'][1]], 'stop')


def t_stop_before_target():
    """A bar covering BOTH the stop and the target fills the stop. Daily bars
    cannot order the two, so the pessimistic one is taken and counted."""
    print('\n5. TIE-BREAK -- a bar covering both fills the STOP, and is counted')
    A = blank(); fire_c1_long(A, 10)
    bars(A, 11, 100.0, hi=102.0, lo=98.0)       # covers stop 99 and target 101.5
    for i in range(12, N):
        bars(A, i, 100.0, hi=100.1, lo=99.9)
    r = go(A, plan=1)
    check('R', float(r['r'][0]), -1.0)
    check('reason', E.REASON[r['reason'][0]], 'stop')
    check('both-touched counter', r['_both_touched'], 1)


def t_no_same_bar_stop():
    """The entry bar's own low must not stop the trade out: the position did not
    exist while that low was printing."""
    print('\n6. ENTRY BAR -- its own low cannot stop the trade out')
    A = blank(); fire_c1_long(A, 10)
    bars(A, 10, 100.0, hi=100.0, lo=90.0)       # a huge low ON the entry bar
    for i in range(11, N):
        bars(A, i, 100.0, hi=100.1, lo=99.9)
    r = go(A, plan=1)
    check('trades opened', r['_n'], 1)
    check('still open past the entry bar', bool(r['exit_bar'][0] > 10), True)


def t_reversal_resets_phase():
    """A reversal must rebuild every piece of phase state. If leg 2's trailing
    stop survived into the new short, the fresh trade would carry a stop from
    the old long -- the Pine bug this engine never had."""
    print('\n7. REVERSAL -- phase state is rebuilt, not inherited')
    A = blank(); fire_c1_long(A, 10)
    bars(A, 11, 103.0, hi=103.1, lo=100.0)
    bars(A, 12, 105.0, hi=105.1, lo=103.0)      # long is trailing by now
    # flip everything short on bar 13
    for i in range(13, N):
        A['c1_lc'][i] = False; A['c1_sc'][i] = True
        A['c2_lc'][i] = False; A['c2_sc'][i] = True
        A['bl'][i] = 106.0                       # price below baseline -> a DOWN cross
        bars(A, i, 105.0, hi=105.1, lo=104.9)
    A['c1_st'][13] = True
    for i in range(14, N):
        bars(A, i, 106.5, hi=106.6, lo=104.9)    # 1.5 against a 105 short entry
    r = go(A, plan=2)
    T = [(int(r['leg'][i]), E.REASON[r['reason'][i]], float(r['r'][i]))
         for i in range(r['_n'])]
    shorts = [i for i in range(r['_n']) if r['dir'][i] == -1]
    check('a short was opened', len(shorts) > 0, True)
    if shorts:
        i = shorts[0]
        check('short entry price', float(r['entry_px'][i]), 105.0)
        check('short leg 1 stopped at 1xATR = -0.5R', float(r['r'][i]), -0.5)
        check('short exit price = 105 + 1', float(r['exit_px'][i]), 106.0)


def t_bridge_blocks_continuation():
    """Bridge Too Far applies to the continuation route. The Pine version
    exempted it; if this test passes the exemption is absent."""
    print('\n8. BRIDGE TOO FAR -- applies to the CONTINUATION route too')

    def setup():
        # cross at bar 8, enter on the C1 flip at 10, exit on the indicator at
        # 12, then C1 flips AGAIN at 14. Pine's longcondition3 needs that second
        # trigger -- continuation is not "re-enter whenever onside". At bar 14
        # the cross is 6 bars old, so the bridge is the only thing left that can
        # refuse the re-entry.
        A = blank(); fire_c1_long(A, 10); A['x_el'][12] = True
        A['c1_lc'][13] = False            # drop the state so bar 14 is a flip
        fire_c1_long(A, 14)
        return A

    # the C1-flip route is switched OFF so that bar 14's flip can only be taken
    # by the continuation route -- otherwise longcondition2 claims it first and
    # the test passes while proving nothing about continuations.
    opt = dict(plan=1, use_base_cross=True, use_c1_flip=False,
               use_continuation=True)
    tight = go(setup(), bridge_bars=3, **opt)
    loose = go(setup(), bridge_bars=10000, **opt)
    check('continuation blocked as stale at bridge = 3',
          tight['_blocked_stale'] > 0, True)
    check('only the first entry survives', tight['_n'], 1)
    check('...and with the bridge disabled it re-enters', loose['_n'] > 1, True,
          note='same bars, %d trades vs %d' % (loose['_n'], tight['_n']))
    routes = [int(loose['route'][i]) for i in range(loose['_n'])]
    check('the extra entry IS the continuation route', 3 in routes, True)


def t_too_late_block():
    """Price more than 1.5xATR from the baseline is too late to join."""
    print('\n9. TOO LATE -- more than 1.5xATR from the baseline blocks entry')
    A = blank(bl_after=98.0); fire_c1_long(A, 10)   # 2.0 away, ATR 1.0
    r = go(A, plan=1)
    check('entries', r['_n'], 0)
    check('counted as too late', r['_blocked_late'], 1)
    A2 = blank(bl_after=99.0); fire_c1_long(A2, 10)  # 1.0 away, allowed
    check('...and 1.0xATR away does enter', go(A2, plan=1)['_n'], 1)


def t_ternary_blocks():
    """A neutral TERNARY confirmation blocks; a neutral BINARY cannot occur."""
    print('\n10. TERNARY neutral BLOCKS entry')
    A = blank(); fire_c1_long(A, 10)
    A['c2_lc'][:] = False                        # C2 says nothing at all
    A['c2_ternary'] = True
    check('entries with a neutral ternary C2', go(A, plan=1)['_n'], 0)
    B = blank(); fire_c1_long(B, 10)
    check('...and with C2 confirming', go(B, plan=1)['_n'], 1)


def t_suspect_bar():
    """No opening, closing or stop resolution on a flagged bar."""
    print('\n11. SUSPECT BARS -- no entry, and no stop filled against one')
    A = blank(); fire_c1_long(A, 10); A['suspect'][10] = True
    check('entry on a suspect bar', go(A, plan=1)['_n'], 0)
    B = blank(); fire_c1_long(B, 10)
    bars(B, 11, 100.0, hi=100.1, lo=90.0)        # would stop out
    B['suspect'][11] = True
    r = go(B, plan=1)
    check('stop filled against a suspect bar', bool(r['exit_bar'][0] == 11), False)


def t_no_lookahead():
    """THE STRUCTURAL TEST. Truncate the series and every trade that completed
    before the cut must be identical. A loop that peeks forward fails this even
    when every arithmetic test above passes."""
    print('\n12. NO LOOK-AHEAD -- truncation cannot change a completed trade')
    import l2engine as EE
    d = EE.load_pair('EURUSD')
    A = EE.prepare(d, **EE.DEFAULT_SLOTS)
    full = EE.run(A, plan=2)
    cut = int(0.7 * len(d))
    A2 = {k: (v[:cut] if isinstance(v, np.ndarray) else v) for k, v in A.items()}
    part = EE.run(A2, plan=2)
    # compare every trade that both opened AND closed before the cut
    m = (full['exit_bar'][:full['_n']] < cut - 1)
    keep = np.flatnonzero(m)
    m2 = (part['exit_bar'][:part['_n']] < cut - 1)
    keep2 = np.flatnonzero(m2)
    k = min(len(keep), len(keep2))
    same_n = len(keep) == len(keep2)
    same = all(full['entry_bar'][keep[i]] == part['entry_bar'][keep2[i]] and
               abs(full['r'][keep[i]] - part['r'][keep2[i]]) < 1e-12
               for i in range(k))
    check('completed trades before the cut', len(keep), len(keep2),
          note='%d compared' % k)
    check('every one identical', same and same_n, True)


def debug_run(pair='EURUSD', **kw):
    import pandas as pd
    d = E.load_pair(pair)
    slots = dict(E.DEFAULT_SLOTS)
    for k in list(slots):
        if k in kw:
            slots[k] = kw.pop(k)
    A = E.prepare(d, **slots)
    r = E.run(A, **kw)
    T = E.trade_frame(r, d)
    T.insert(0, 'pair', pair)
    return T, E.summary(r, label=pair)


def main():
    import pandas as pd
    print('ENGINE KNOWN-ANSWER TESTS (ATR pinned at 1.0, risk 100, so one ATR '
          'of adverse move is 1R)')
    for f in (t_sizing_and_full_stop, t_two_leg_target, t_leg2_breakeven,
              t_leg2_trailing, t_stop_before_target, t_no_same_bar_stop,
              t_reversal_resets_phase, t_bridge_blocks_continuation,
              t_too_late_block, t_ternary_blocks, t_suspect_bar, t_no_lookahead):
        f()
    print('\n%s' % ('ALL ENGINE TESTS PASS' if not FAIL
                    else 'FAILURES: %s' % ', '.join(FAIL)))

    rows, summ = [], []
    for p in ('EURUSD', 'GBPUSD', 'USDJPY'):
        T, s = debug_run(p, plan=2)
        rows.append(T); summ.append(s)
    D = pd.concat(rows, ignore_index=True)
    D.to_csv(os.path.join(ROOTOUT, 'l2_debug_trades.csv'), index=False)
    S = pd.DataFrame(summ)
    pd.set_option('display.width', 240)
    print('\nDEBUG RUN -- %s, two-leg plan'
          % ' / '.join('%s=%s' % kv for kv in E.DEFAULT_SLOTS.items()))
    print(S[['label', 'trades', 'expectancy_R', 'total_R', 'win_rate',
             'profit_factor', 'sortino', 'max_dd_R', 'both_touched',
             'blocked_late', 'blocked_stale']].to_string(index=False))
    print('\n  wrote results/l2_debug_trades.csv (%d leg records)' % len(D))
    pd.DataFrame([dict(test=k, passed=k not in FAIL)
                  for k in ['sizing', 'two_leg_target', 'leg2_breakeven',
                            'leg2_trailing', 'stop_before_target', 'entry_bar_low',
                            'reversal_reset', 'bridge_continuation', 'too_late',
                            'ternary_block', 'suspect_bar', 'no_lookahead']]
                 ).to_csv(os.path.join(ROOTOUT, 'l2_engine_tests.csv'), index=False)
    assert not FAIL, 'engine tests failed: %s' % FAIL
    return D, S


if __name__ == '__main__':
    main()
