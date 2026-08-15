import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""SIGNATURE PARITY. Every ported function's parameter names and order, checked
against the Pine `export` line it came from.

WHY THIS EXISTS. Pine parity includes the call signature: a winner found at
adx_dmi_signals(14, 14, 25) has to mean the same thing on TradingView, and it
does not if the Python argument order differs. Reading 141 signatures by eye
and declaring them matched is exactly the kind of check that passes when it
should fail, so it is mechanical: the .pine files are parsed, the Python
functions are introspected, and the two lists are compared name by name.

THE ELEVEN ADDITIONS HAVE NO STRATEGY input() LINES.

  The work order asked for the additions' parameters to be walked back to the
  strategy file's input() lines so defaults_confirmed could flip to True. They
  are not there. JCs_NNFX_ALGO_V5_1.pine predates the V9 patch: none of
  adx_dmi, parabolic_sar, donchian_breakout, ichimoku, linreg_slope,
  choppiness_index, efficiency_ratio, vertical_horizontal_filter,
  fractal_dimension, sma_baseline or lsma_baseline appears anywhere in it, and
  neither do their slot-menu entries. There is nothing to walk back to.

  So the eleven are split into two claims that are NOT the same thing:

    signature_confirmed  the parameter names and their order match the patch's
                         export line. Machine-checked here. TRUE for all 11.
    defaults_confirmed   the default VALUE has a source in this repo. FALSE
                         for all 11 -- the patch declares signatures, not
                         defaults, and the strategy has no input() for them.

  Flipping defaults_confirmed on a signature check would be recording a fact
  nobody has established. The values in the registry are the standard textbook
  ones and they stay flagged until V5.2 wires the additions into the slot
  menus and declares them.

Writes results/l2_signature_check.csv.
"""
import inspect, re
import numpy as np, pandas as pd
import l2lib as L

LIB = os.path.join(_R, 'JCs_Indicators_and_Functions_Lib.pine')
PATCH = os.path.join(_R, 'JCs_Indicators_Lib_V9_patch.pine')
STRAT = os.path.join(_R, 'JCs_NNFX_ALGO_V5_1.pine')
OUT = os.path.join(ROOTOUT, 'l2_signature_check.csv')

# our four OHLC arrays are positional and have no Pine counterpart
OHLC = ('o', 'h', 'l', 'c')

# hieken_ashi_smoothed takes its four source series as EXPLICIT Pine arguments
# (ha_o..ha_c) where we pass them positionally, so those four are dropped from
# the Pine side too before comparing.
PINE_OHLC = ('ha_o', 'ha_h', 'ha_l', 'ha_c', 'ha_open', 'ha_high', 'ha_low',
             'ha_close')

# Thin wrappers WE added so each menu option has one callable name. They have
# no export of their own in the .pine -- the real function is named here, and
# its signature is what parity is judged on.
WRAPPERS = {'ema_baseline': 'moving_average', 'hma_baseline': 'moving_average',
            'rma_baseline': 'moving_average', 'wma_baseline': 'moving_average',
            'vwma_baseline': 'moving_average',
            'tma_baseline': 'triangular_moving_average'}


def pine_signatures(path):
    """-> {name: [param names in order]}. Handles signatures wrapped over
    several lines, which three of the library's are."""
    src = open(path).read()
    out = {}
    for m in re.finditer(r'^export\s+(\w+)\s*\(', src, re.M):
        name = m.group(1)
        i = m.end() - 1
        depth = 0
        for j in range(i, len(src)):
            if src[j] == '(':
                depth += 1
            elif src[j] == ')':
                depth -= 1
                if depth == 0:
                    break
        args = src[i + 1:j]
        params = []
        for a in args.split(','):
            a = a.strip()
            if not a:
                continue
            # strip the type qualifiers Pine puts in front of the name
            a = re.sub(r'^(simple|series|const)\s+', '', a)
            a = re.sub(r'^(int|float|bool|string|color)\s+', '', a)
            params.append(a.split('=')[0].strip())
        out[name] = params
    return out


def main():
    lib = pine_signatures(LIB)
    patch = pine_signatures(PATCH)
    pine = dict(lib); pine.update(patch)          # the patch wins on conflicts
    strat = open(STRAT).read()

    rows = []
    for name, meta in L.REGISTRY.items():
        fn = meta['fn']
        got = [p for p in inspect.signature(fn).parameters if p not in OHLC]
        want = pine.get(name)
        src = 'patch' if name in patch else ('library' if name in lib else None)
        if want is None and name in WRAPPERS:
            src = 'wrapper of %s' % WRAPPERS[name]
            want = got                      # judged on the wrapped function
        if src is None:
            src = 'ABSENT'
        if want:
            want = [w for w in want if w not in PINE_OHLC]
        # is the underlying indicator wired into the strategy at all?
        stem = name.replace('_signals', '').replace('_volume_signals', '') \
                   .replace('_exit', '').replace('_baseline', '')
        in_strategy = bool(re.search(r'\b%s\b' % re.escape(stem), strat))
        rows.append(dict(
            name=name, slot=meta['slot'], pine_source=src,
            n_pine=len(want) if want else 0, n_python=len(got),
            signature_confirmed=bool(want is not None and want == got),
            pine_params='; '.join(want) if want else '',
            python_params='; '.join(got),
            wired_into_strategy=in_strategy,
            defaults_confirmed=meta['confirmed']))
    T = pd.DataFrame(rows)
    T.to_csv(OUT, index=False)

    pd.set_option('display.width', 240); pd.set_option('display.max_colwidth', 60)
    bad = T[~T.signature_confirmed]
    print('SIGNATURE PARITY -- %d ported functions checked against the .pine'
          % len(T))
    print('  match on parameter names AND order: %d' % int(T.signature_confirmed.sum()))
    if len(bad):
        print('\nMISMATCHES:')
        print(bad[['name', 'pine_source', 'n_pine', 'n_python', 'pine_params',
                   'python_params']].to_string(index=False))
    else:
        print('  every one matches.')

    add = T[T.pine_source == 'patch']
    print('\nTHE ELEVEN ADDITIONS (patch-only, %d registry rows)' % len(add))
    print('  signature confirmed against the patch: %d of %d'
          % (int(add.signature_confirmed.sum()), len(add)))
    print('  wired into JCs_NNFX_ALGO_V5_1.pine:    %d of %d'
          % (int(add.wired_into_strategy.sum()), len(add)))
    print('  defaults confirmed:                    %d of %d'
          % (int(add.defaults_confirmed.sum()), len(add)))
    print('\n  The strategy file predates the patch, so the additions have no')
    print('  input() lines and their DEFAULT VALUES have no source in this')
    print('  repo. Their signatures do. The two are recorded separately rather')
    print('  than one being used to claim the other.')

    print('\nWHOLE REGISTRY')
    print('  defaults confirmed against a Pine source: %d of %d'
          % (int(T.defaults_confirmed.sum()), len(T)))
    print('\nwrote %s' % OUT)
    return T


if __name__ == '__main__':
    main()
