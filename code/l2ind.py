import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""SUPERSEDED by l2lib.py. Kept, not deleted, because its numbers are quoted
in commit 8d01e52 and in results/l2_indicator_registry.csv as it stood then.

This file was written from the WORK ORDER'S PROSE, before the Pine sources were
in the repo. When they arrived the patch disagreed with it in five places --
adx_dmi collapsed two lengths into one, its triggers came from the state rather
than the DI cross, ichimoku ignored the tenkan/kijun condition, fractal_dimension
rejected odd lengths the source truncates, and nothing latched. Use l2lib.py.

THE INDICATOR LIBRARY. Vectorised over OHLC arrays, one call per pair, feeding
boolean and float arrays to the Numba bar loop in l2engine.py.

SCOPE, AND WHAT IS MISSING. This file holds THE ELEVEN ADDITIONS ONLY -- the
indicators the work order specifies by name rather than by Pine source. The 36
C1 / 36 C2 / 12 volume / 14 baseline / 36 exit slots ported from
AJs_Indicators_and_Functions_Lib ARE NOT HERE: that library is not in the repo
and has never been committed, so there is nothing to port from. A description of
a bug fix ("J_TPO summed the wrong variable") specifies the fix, not the
function. Everything here is built to receive them -- same contracts, same
registry -- so dropping the port in later adds rows, not rewrites.

DEFAULT PARAMETERS ARE NOT CONFIRMED. Pine parity is the point of this exercise,
and parity includes defaults: a winner found at ADX(14, 25) that TradingView
runs at ADX(14, 20) is not the same strategy. The V9 patch file is the authority
and is also not in the repo, so every default below is the standard textbook
value and every registry entry carries confirmed=False. Confirm them against V9
before any sweep, not after.

THE CONTRACTS, identical to the Pine helpers:

  confirmation  -> (long_trig, short_trig, long_conf, short_conf)   4 x bool
  volume        -> (ok_long, ok_short)                              2 x bool
  exit          -> (exit_long, exit_short)                          2 x bool
  baseline      -> float array

  *_conf is the STATE: what this indicator says the market is doing on this bar.
  *_trig is the EVENT: the bar the state flipped into being. trig implies conf.

BINARY vs TERNARY, and why the tag is machine-readable. A binary indicator is
always long or short -- it has no opinion to withhold. A ternary one can decline
both directions, and a bar where a ternary confirmation is neutral BLOCKS entry
rather than voting. The entry rule needs to know which it is holding, so it is a
field, not a docstring: KIND[name] == 'TERNARY'.

WARM-UP IS FALSE, NEVER NaN. Every boolean array is False until the indicator
has enough history. NaN in a boolean context is True in numpy, which would open
trades on bar 3 of the sample. Baselines are the one exception -- they stay NaN
during warm-up because a float has no false -- and the engine treats a NaN
baseline as "no trade", asserted in l2engine.py.

LAG. Nothing here reads forward. Where a value is only knowable after the bar
(the Donchian channel that the current bar is being compared against, the
Ichimoku cloud) it is shifted explicitly and the shift is commented. The engine
then evaluates on the close of the bar and fills at that close, which is
process_orders_on_close: the one place the project's usual .shift(1) is NOT
applied, because Jack trades the close he sees.

Writes results/l2_indicator_registry.csv.
"""
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view as _swv

# --------------------------------------------------------------------------
# primitives
# --------------------------------------------------------------------------


def _roll(a, n):
    """(len(a), n) windows, NaN-padded at the front so index i is the window
    ENDING at i. Everything rolling below goes through this, so the alignment
    is wrong in one place or right in all of them."""
    a = np.asarray(a, float)
    if n <= 0:
        raise ValueError('window must be positive')
    pad = np.full(n - 1, np.nan)
    return _swv(np.concatenate([pad, a]), n)


def shift(a, k=1):
    """Move forward k bars. shift(x, 1)[i] is x[i-1]."""
    a = np.asarray(a, float)
    out = np.full_like(a, np.nan)
    if k > 0:
        out[k:] = a[:-k]
    elif k < 0:
        out[:k] = a[-k:]
    else:
        out[:] = a
    return out


# These use the PROPAGATING reductions, not the nan* ones. _roll pads the front
# with NaN, so nanmean would happily average a one-bar window and report an
# SMA(20) on bar 0 -- which then gives a partial Donchian channel, a baseline
# during warm-up, and entries in the first fortnight of the sample. Pine returns
# na until the window is full and so does this.
def sma(a, n):
    return _roll(a, n).mean(axis=1) if n > 1 else np.asarray(a, float)


def stdev(a, n):
    return _roll(a, n).std(axis=1, ddof=0)


def highest(a, n):
    return _roll(a, n).max(axis=1)


def lowest(a, n):
    return _roll(a, n).min(axis=1)


def rolling_sum(a, n):
    return _roll(a, n).sum(axis=1)


def ema(a, n):
    """Pine's ta.ema: seeded with the first valid value, alpha = 2/(n+1)."""
    a = np.asarray(a, float)
    out = np.full(a.shape, np.nan)
    k = 2.0 / (n + 1.0)
    prev = np.nan
    for i in range(a.size):
        x = a[i]
        if not np.isfinite(x):
            continue
        prev = x if not np.isfinite(prev) else prev + k * (x - prev)
        out[i] = prev
    return out


def rma(a, n):
    """Wilder's smoothing -- ta.rma. Seeded with the first n-bar SMA, which is
    what Pine does; seeding with the first value instead shifts ADX for the
    first few hundred bars and is the usual source of an ADX parity failure."""
    a = np.asarray(a, float)
    out = np.full(a.shape, np.nan)
    k = 1.0 / n
    prev, seen, acc = np.nan, 0, 0.0
    for i in range(a.size):
        x = a[i]
        if not np.isfinite(x):
            continue
        if not np.isfinite(prev):
            seen += 1; acc += x
            if seen == n:
                prev = acc / n; out[i] = prev
            continue
        prev = prev + k * (x - prev)
        out[i] = prev
    return out


def wma(a, n):
    w = np.arange(1, n + 1, dtype=float)
    W = _roll(a, n)
    return (W * w).sum(axis=1) / w.sum()


def linreg(a, n, offset=0):
    """Pine's ta.linreg -- the fitted value at the END of the window (LSMA)."""
    W = _roll(a, n)
    x = np.arange(n, dtype=float)
    xm = x.mean()
    xd = x - xm
    ym = W.mean(axis=1)
    slope = (W * xd).sum(axis=1) / (xd * xd).sum()
    return ym + slope * (n - 1 - xm - offset)


def linreg_slope_r2(a, n):
    """Slope per bar and the fit's R^2, together -- the slope alone cannot tell
    a clean trend from a noisy one with the same drift."""
    W = _roll(a, n)
    x = np.arange(n, dtype=float)
    xd = x - x.mean()
    ym = W.mean(axis=1)
    yd = W - ym[:, None]
    sxx = (xd * xd).sum()
    slope = (yd * xd).sum(axis=1) / sxx
    ssr = (slope ** 2) * sxx
    sst = (yd * yd).sum(axis=1)
    with np.errstate(invalid='ignore', divide='ignore'):
        r2 = np.where(sst > 0, ssr / sst, 0.0)
    return slope, r2


def true_range(h, l, c):
    pc = shift(c, 1)
    tr = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))
    tr[0] = h[0] - l[0]
    return tr


def atr(h, l, c, n=14):
    return rma(true_range(h, l, c), n)


def _F(x):
    """NaN -> False, and the result is a real bool array."""
    return np.nan_to_num(np.asarray(x, float), nan=0.0).astype(bool) \
        if x.dtype != bool else x


def _state(long_c, short_c):
    """conf pair -> the full 4-array confirmation contract. A trigger is the bar
    a state becomes true having not been true on the previous bar."""
    lc = np.asarray(long_c, bool); sc = np.asarray(short_c, bool)
    lt = lc & ~np.concatenate([[False], lc[:-1]])
    st = sc & ~np.concatenate([[False], sc[:-1]])
    return lt, st, lc, sc


def _latch(up, dn):
    """Hold the last decisive signal. A Donchian channel says nothing while
    price sits inside it -- that is 'still long', not 'neutral'."""
    n = up.size
    out = np.zeros(n, np.int8)
    cur = 0
    for i in range(n):
        if up[i]:
            cur = 1
        elif dn[i]:
            cur = -1
        out[i] = cur
    return out == 1, out == -1


# --------------------------------------------------------------------------
# confirmation slot (C1 / C2 / exit)
# --------------------------------------------------------------------------


def adx_dmi(o, h, l, c, length=14, threshold=25.0):
    """TERNARY. Direction from DI, permission from ADX: below the threshold the
    indicator declines both directions and blocks entry."""
    pc = shift(c, 1)
    up, dn = h - shift(h, 1), shift(l, 1) - l
    plus = np.where((up > dn) & (up > 0), up, 0.0)
    minus = np.where((dn > up) & (dn > 0), dn, 0.0)
    tr = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))
    tr[0] = h[0] - l[0]
    atr_ = rma(tr, length)
    with np.errstate(invalid='ignore', divide='ignore'):
        pdi = 100.0 * rma(plus, length) / atr_
        mdi = 100.0 * rma(minus, length) / atr_
        dx = 100.0 * np.abs(pdi - mdi) / (pdi + mdi)
    adx = rma(dx, length)
    ok = np.isfinite(adx) & (adx > threshold)
    return _state(ok & (pdi > mdi), ok & (mdi > pdi))


def parabolic_sar(o, h, l, c, start=0.02, inc=0.02, maxaf=0.2):
    """BINARY. Always on one side of price."""
    n = c.size
    long_c = np.zeros(n, bool)
    if n < 2:
        return _state(long_c, ~long_c & False)
    sar = np.empty(n); isl = np.empty(n, bool)
    up = c[1] >= c[0]
    af = start
    ep = h[1] if up else l[1]
    sar[0] = sar[1] = l[0] if up else h[0]
    isl[0] = isl[1] = up
    for i in range(2, n):
        s = sar[i - 1] + af * (ep - sar[i - 1])
        if up:
            # the SAR may never enter the prior two bars' range
            s = min(s, l[i - 1], l[i - 2])
            if l[i] < s:
                up = False; s = ep; ep = l[i]; af = start
            elif h[i] > ep:
                ep = h[i]; af = min(af + inc, maxaf)
        else:
            s = max(s, h[i - 1], h[i - 2])
            if h[i] > s:
                up = True; s = ep; ep = h[i]; af = start
            elif l[i] < ep:
                ep = l[i]; af = min(af + inc, maxaf)
        sar[i] = s; isl[i] = up
    return _state(isl, ~isl)


def donchian_breakout(o, h, l, c, length=20):
    """BINARY (latching). The channel is shifted one bar: the current bar cannot
    break out of a channel it helped define."""
    up = highest(h, length); dn = lowest(l, length)
    pu, pd = shift(up, 1), shift(dn, 1)
    lc, sc = _latch(np.nan_to_num(c > pu, nan=0).astype(bool),
                    np.nan_to_num(c < pd, nan=0).astype(bool))
    warm = ~np.isfinite(pu)
    lc = lc & ~warm; sc = sc & ~warm
    return _state(lc, sc)


def ichimoku(o, h, l, c, tenkan=9, kijun=26, senkou=52):
    """TERNARY. Price inside the cloud is no opinion.

    The cloud is plotted kijun bars AHEAD, so the cloud governing THIS bar was
    computed kijun bars ago -- shift(+kijun), a lag. Reading the plotted value
    at the current index instead would be a look-ahead of 26 bars."""
    mid = lambda a, b, n: (highest(a, n) + lowest(b, n)) / 2.0
    tk = mid(h, l, tenkan); kj = mid(h, l, kijun)
    a = shift((tk + kj) / 2.0, kijun)
    b = shift(mid(h, l, senkou), kijun)
    top, bot = np.maximum(a, b), np.minimum(a, b)
    ok = np.isfinite(top)
    return _state(ok & (c > top), ok & (c < bot))


def linreg_slope(o, h, l, c, length=14, min_r2=0.20):
    """TERNARY. Direction from the slope, permission from the fit: a slope with
    no R^2 behind it is drift through noise, and declines both directions."""
    sl, r2 = linreg_slope_r2(c, length)
    ok = np.isfinite(sl) & (r2 >= min_r2)
    return _state(ok & (sl > 0), ok & (sl < 0))


# --------------------------------------------------------------------------
# volume slot -- ALL VOLATILITY / RANGE MEASURES.
# Spot FX has no volume (see l2data.py); nothing in this slot may read one.
# --------------------------------------------------------------------------


def choppiness_index(o, h, l, c, length=14, threshold=61.8):
    """Low = trending = pass. 61.8 and 38.2 are the conventional Fibonacci
    bands; only the upper one gates entry."""
    tr = true_range(h, l, c)
    rng = highest(h, length) - lowest(l, length)
    with np.errstate(invalid='ignore', divide='ignore'):
        ci = 100.0 * np.log10(rolling_sum(tr, length) / rng) / np.log10(length)
    ok = np.isfinite(ci) & (ci < threshold)
    return ok, ok


def efficiency_ratio(o, h, l, c, length=10, threshold=0.30):
    """Kaufman. Net travel over gross travel -- 1.0 is a straight line."""
    net = np.abs(c - shift(c, length))
    gross = rolling_sum(np.abs(np.diff(c, prepend=np.nan)), length)
    with np.errstate(invalid='ignore', divide='ignore'):
        er = np.where(gross > 0, net / gross, np.nan)
    ok = np.isfinite(er) & (er > threshold)
    return ok, ok


def vertical_horizontal_filter(o, h, l, c, length=28, threshold=0.35):
    """VHF. Same idea as the efficiency ratio but the numerator is the range of
    closes rather than the net move, so a round trip still scores."""
    rng = highest(c, length) - lowest(c, length)
    gross = rolling_sum(np.abs(np.diff(c, prepend=np.nan)), length)
    with np.errstate(invalid='ignore', divide='ignore'):
        v = np.where(gross > 0, rng / gross, np.nan)
    ok = np.isfinite(v) & (v > threshold)
    return ok, ok


def fractal_dimension(o, h, l, c, length=30, threshold=1.5):
    """Ehlers' fractal dimension. 1.0 is a straight line, 2.0 fills the plane;
    below 1.5 is trending. length MUST be even -- the measure compares two half
    windows against the whole, and an odd split makes them different sizes."""
    if length % 2:
        raise ValueError('fractal_dimension length must be even, got %d' % length)
    hn = length // 2
    n1 = (highest(h, hn) - lowest(l, hn)) / hn
    n2 = shift((highest(h, hn) - lowest(l, hn)) / hn, hn)
    n3 = (highest(h, length) - lowest(l, length)) / length
    with np.errstate(invalid='ignore', divide='ignore'):
        d = np.where((n1 + n2 > 0) & (n3 > 0),
                     (np.log(n1 + n2) - np.log(n3)) / np.log(2.0), np.nan)
    ok = np.isfinite(d) & (d < threshold)
    return ok, ok


# --------------------------------------------------------------------------
# baseline slot -- float array, NaN during warm-up
# --------------------------------------------------------------------------


def baseline_sma(o, h, l, c, length=20):
    return sma(c, length)


def baseline_lsma(o, h, l, c, length=20, offset=0):
    """Least-squares MA: the linear regression's value at the end of the window.
    Turns earlier than an SMA because it fits a slope instead of averaging."""
    return linreg(c, length, offset)


# --------------------------------------------------------------------------
# registry
# --------------------------------------------------------------------------

# slot, kind, defaults. confirmed=False everywhere until the V9 patch file
# arrives -- see the module docstring. 'kind' is what the entry rule branches on.
REGISTRY = {
    'adx_dmi':            dict(fn=adx_dmi, slot='confirmation', kind='TERNARY',
                               defaults=dict(length=14, threshold=25.0)),
    'parabolic_sar':      dict(fn=parabolic_sar, slot='confirmation', kind='BINARY',
                               defaults=dict(start=.02, inc=.02, maxaf=.2)),
    'donchian_breakout':  dict(fn=donchian_breakout, slot='confirmation', kind='BINARY',
                               defaults=dict(length=20)),
    'ichimoku':           dict(fn=ichimoku, slot='confirmation', kind='TERNARY',
                               defaults=dict(tenkan=9, kijun=26, senkou=52)),
    'linreg_slope':       dict(fn=linreg_slope, slot='confirmation', kind='TERNARY',
                               defaults=dict(length=14, min_r2=.20)),
    'choppiness_index':   dict(fn=choppiness_index, slot='volume', kind='FILTER',
                               defaults=dict(length=14, threshold=61.8)),
    'efficiency_ratio':   dict(fn=efficiency_ratio, slot='volume', kind='FILTER',
                               defaults=dict(length=10, threshold=.30)),
    'vertical_horizontal_filter': dict(fn=vertical_horizontal_filter, slot='volume',
                               kind='FILTER', defaults=dict(length=28, threshold=.35)),
    'fractal_dimension':  dict(fn=fractal_dimension, slot='volume', kind='FILTER',
                               defaults=dict(length=30, threshold=1.5)),
    'baseline_sma':       dict(fn=baseline_sma, slot='baseline', kind='BASELINE',
                               defaults=dict(length=20)),
    'baseline_lsma':      dict(fn=baseline_lsma, slot='baseline', kind='BASELINE',
                               defaults=dict(length=20, offset=0)),
}
KIND = {k: v['kind'] for k, v in REGISTRY.items()}
NARITY = {k: (2 if v['kind'] == 'BINARY' else 3) for k, v in REGISTRY.items()
          if v['slot'] == 'confirmation'}

NOUT = {'confirmation': 4, 'volume': 2, 'exit': 2, 'baseline': 1}


def compute(name, o, h, l, c, **kw):
    """Run one indicator with its defaults, overridden by kw."""
    r = REGISTRY[name]
    p = dict(r['defaults']); p.update(kw)
    out = r['fn'](o, h, l, c, **p)
    if r['slot'] == 'baseline':
        return np.asarray(out, float)
    return tuple(np.asarray(x, bool) for x in out)


def registry_frame():
    import pandas as pd
    rows = []
    for k, v in REGISTRY.items():
        rows.append(dict(name=k, slot=v['slot'], kind=v['kind'],
                         n_outputs=NOUT[v['slot']],
                         defaults='; '.join('%s=%s' % kv for kv in v['defaults'].items()),
                         defaults_confirmed=False,
                         source='addition (work order), not ported from Pine'))
    return pd.DataFrame(rows)


def main():
    import pandas as pd
    d = pd.read_csv(os.path.join(ROOTDATA, 'ohlc_clean', 'EURUSD.csv'),
                    index_col=0, parse_dates=True)
    o, h, l, c = (d[k].values.astype(float) for k in ('open', 'high', 'low', 'close'))
    R = registry_frame()
    R.to_csv(os.path.join(ROOTOUT, 'l2_indicator_registry.csv'), index=False)

    print('INDICATOR REGISTRY (%d built; the ~134 Pine ports are NOT here -- '
          'the library is not in the repo)' % len(REGISTRY))
    pd.set_option('display.width', 200); pd.set_option('display.max_colwidth', 46)
    print(R[['name', 'slot', 'kind', 'n_outputs', 'defaults']].to_string(index=False))

    print('\nCONTRACT AND WARM-UP CHECK on EURUSD (%d bars)' % len(d))
    rows = []
    for name, meta in REGISTRY.items():
        out = compute(name, o, h, l, c)
        if meta['slot'] == 'baseline':
            ok_shape = out.shape == c.shape
            first = int(np.argmax(np.isfinite(out)))
            rows.append(dict(name=name, outputs=1, shape_ok=ok_shape,
                             any_nan_in_bool='n/a', warmup_bars=first,
                             long_pct=np.nan, short_pct=np.nan, neutral_pct=np.nan))
            continue
        n = NOUT[meta['slot']]
        ok_shape = len(out) == n and all(x.shape == c.shape for x in out)
        allbool = all(x.dtype == bool for x in out)
        if meta['slot'] == 'confirmation':
            lt, st, lc, sc = out
            both = int((lc & sc).sum())
            neut = float((~lc & ~sc).mean())
            rows.append(dict(name=name, outputs=n, shape_ok=ok_shape and allbool,
                             any_nan_in_bool=both, warmup_bars=int(np.argmax(lc | sc)),
                             long_pct=round(100 * lc.mean(), 1),
                             short_pct=round(100 * sc.mean(), 1),
                             neutral_pct=round(100 * neut, 1)))
        else:
            a, b = out
            rows.append(dict(name=name, outputs=n, shape_ok=ok_shape and allbool,
                             any_nan_in_bool=0, warmup_bars=int(np.argmax(a)),
                             long_pct=round(100 * a.mean(), 1),
                             short_pct=round(100 * b.mean(), 1), neutral_pct=np.nan))
    T = pd.DataFrame(rows)
    print(T.to_string(index=False))

    print('\n  every output correctly shaped and typed: %s'
          % bool(T.shape_ok.all()))
    print('  long and short simultaneously true anywhere: %d'
          % sum(int(x) for x in T.any_nan_in_bool if x != 'n/a'))
    tern = [n for n in REGISTRY if KIND[n] == 'TERNARY']
    bina = [n for n in REGISTRY if KIND[n] == 'BINARY']
    print('  TERNARY neutral share: %s'
          % {n: float(T.set_index('name').loc[n, 'neutral_pct']) for n in tern})
    print('  BINARY  neutral share (must be ~0 after warm-up): %s'
          % {n: float(T.set_index('name').loc[n, 'neutral_pct']) for n in bina})
    print('\nDEFAULTS ARE UNCONFIRMED -- every row has defaults_confirmed=False. '
          'The V9 patch file is the authority and is not in the repo.')
    print('\nwrote results/l2_indicator_registry.csv')
    return T


if __name__ == '__main__':
    main()
