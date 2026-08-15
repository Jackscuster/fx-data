import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""THE PORTED INDICATOR LIBRARY. JCs_Indicators_and_Functions_Lib.pine, with
JCs_Indicators_Lib_V9_patch.pine applied.

PATCH BEHAVIOUR FROM DAY ONE. Where the patch replaces a function, only the
patched version exists here. The buggy original is NOT ported for fidelity --
the .pine file in the repo is the record of what it was.

FUNCTION NAMES, PARAMETER NAMES AND DEFAULTS MATCH PINE. A winner has to be
reproducible on TradingView, so `ssl_channel_signals(len)` is called that here
too, and every default is read off the strategy file's input() line rather than
chosen. `PINE_LINE` on each registry row is where in the .pine the definition
lives, so any disagreement can be checked in seconds.

Signal contract, unchanged from the Pine helpers:
    *_signals(...)         -> (lt, st, lc, sc)
    *_volume_signals(...)  -> (pass_long, pass_short)
    *_exit(...)            -> (le, se)
    *_baseline(...) / MA   -> float array

BINARY vs TERNARY is taken from the patch's own words, not inferred. A ternary
confirmation can decline both directions and therefore blocks entry.

Writes results/l2_indicator_registry.csv.
"""
import numpy as np
import l2pine as P

# ==========================================================================
# THE DEFAULT COMBINATION -- C1 SSL, C2 DSPO, volume Variance, baseline TMA,
# exit SSL. These five are what Phase 3 compares against TradingView.
# ==========================================================================


def ssl_channel(h, l, c, ssl_length=10):
    """lib line 118. sslUp / sslDown, as a pair."""
    sma_hi = P.sma(h, ssl_length)
    sma_lo = P.sma(l, ssl_length)
    hlv = P.latch(P.F(np.asarray(c) > sma_hi), P.F(np.asarray(c) < sma_lo), init=0)
    warm = ~np.isfinite(sma_hi)
    down = np.where(hlv < 0, sma_hi, sma_lo)
    up = np.where(hlv < 0, sma_lo, sma_hi)
    up[warm] = np.nan; down[warm] = np.nan
    return up, down


def ssl_channel_signals(o, h, l, c, len=10):
    up, dn = ssl_channel(h, l, c, len)
    return (P.crossover(up, dn), P.crossunder(up, dn),
            P.F(up > dn), P.F(up < dn))


def ssl_channel_exit(o, h, l, c, len=10):
    up, dn = ssl_channel(h, l, c, len)
    return P.crossunder(up, dn), P.crossover(up, dn)


def detrended_synthetic_price_oscillator(h, l, c, dspo_length=14):
    """lib line 145. EMA(hl2, L) - EMA(hl2, 2L)."""
    hl2 = (np.asarray(h, float) + np.asarray(l, float)) / 2.0
    return P.ema(hl2, dspo_length) - P.ema(hl2, 2 * dspo_length)


def dspo_signals(o, h, l, c, len=14):
    """lib line 2098. Zero crossings, written as v[1]<0 and v>0 rather than
    ta.crossover -- which differs when v is exactly 0 on the prior bar."""
    v = detrended_synthetic_price_oscillator(h, l, c, len)
    pv = P.shift(v, 1)
    return P.F((pv < 0) & (v > 0)), P.F((pv > 0) & (v < 0)), P.F(v > 0), P.F(v < 0)


def dspo_exit(o, h, l, c, len=14):
    v = detrended_synthetic_price_oscillator(h, l, c, len)
    pv = P.shift(v, 1)
    return P.F((pv > 0) & (v < 0)), P.F((pv < 0) & (v > 0))


def variance(o, h, l, c, v_mode='Price', v_hline_filter=0.0,
             v_method='MA > Variance', v_lookback=20, v_filter_lookback=20,
             v_ema_lookback=10):
    """lib line ~. Returns the BOOLEAN gate, as Pine does.

    Note the variance is computed with ddof=1 (sum/(lookback-1)) while the
    z-score's stdev is ta.stdev, which is population. That mix is in the
    original and is preserved -- it is not a transcription slip."""
    c = np.asarray(c, float)
    if v_mode == 'Logarithmic Returns':
        src = np.log(c / P.shift(c, 1)) * 100.0
    elif v_mode == 'Price':
        src = c
    else:
        src = np.full(c.shape, np.nan)
    n = int(v_lookback)
    mean = P.sma(src, n)
    W = P._roll(src, n)
    var = ((W - mean[:, None]) ** 2).sum(axis=1) / (n - 1)
    sd = P.stdev(var, v_filter_lookback)
    vma = P.sma(var, v_filter_lookback)
    with np.errstate(invalid='ignore', divide='ignore'):
        z = np.where(sd > 0, (var - vma) / sd, np.nan)
    zema = P.ema(z, v_ema_lookback)
    if v_method == 'Variance':
        g = z > v_hline_filter
    elif v_method == 'Variance MA':
        g = zema > v_hline_filter
    else:                                   # 'MA > Variance'
        g = z > zema
    return P.F(g)


def variance_volume_signals(o, h, l, c, mode='Price', hline=0.0,
                            method='MA > Variance', lookback=20,
                            filter_lookback=20, ema_len=10):
    v = variance(o, h, l, c, mode, hline, method, lookback, filter_lookback,
                 ema_len)
    return v, v


def triangular_moving_average(o, h, l, c, tma_length=20):
    """lib line ~. sma(sma(close, ceil(L/2)), floor(L/2)+1).

    See l2pine.PINE_INT_DIV: whether ceil/floor do anything depends on whether
    Pine's int/int division truncates. For the default L=20 both readings give
    sma(sma(c,10),11), so the DEFAULT baseline is unaffected either way and the
    ambiguity cannot corrupt the Phase 3 comparison."""
    hl = P.idiv(int(tma_length), 2)
    return P.sma(P.sma(c, int(np.ceil(hl))), int(np.floor(hl)) + 1)


def tma_baseline(o, h, l, c, length=20):
    return triangular_moving_average(o, h, l, c, length)


# ==========================================================================
# SECTION B ADDITIONS -- the eleven, exactly as the patch defines them.
# An earlier version of these was written from the work order's prose before
# the patch existed; every place the patch disagreed, the patch won. The
# differences are noted per function because they are not cosmetic.
# ==========================================================================


def adx_dmi(o, h, l, c, di_length=14, adx_smoothing=14):
    """patch B1. TWO lengths -- di_length and adx_smoothing are separate, and
    the prose-built version collapsed them into one.

    Pine divides by `dsum == 0 ? 1 : dsum` rather than guarding after the fact,
    and wraps plus/minus in fixnan(), which carries the last good value through
    a zero true range instead of emitting na."""
    up = P.change(h)
    down = -P.change(l)
    plus_dm = np.where(np.isfinite(up), np.where((up > down) & (up > 0), up, 0.0), np.nan)
    minus_dm = np.where(np.isfinite(down), np.where((down > up) & (down > 0), down, 0.0), np.nan)
    trur = P.rma(P.tr(h, l, c), di_length)
    with np.errstate(invalid='ignore', divide='ignore'):
        plus = P.fixnan(100.0 * P.rma(plus_dm, di_length) / trur)
        minus = P.fixnan(100.0 * P.rma(minus_dm, di_length) / trur)
    dsum = plus + minus
    adx = 100.0 * P.rma(np.abs(plus - minus) / np.where(dsum == 0, 1.0, dsum),
                        adx_smoothing)
    return adx, plus, minus


def adx_dmi_signals(o, h, l, c, di_length=14, adx_smoothing=14, adx_threshold=25.0):
    """patch B1. lt is the DI CROSSOVER while strong -- NOT "became strong and
    long", which is what deriving triggers from the state gives. They differ on
    every bar where ADX rises through the threshold with +DI already on top."""
    adx, plus, minus = adx_dmi(o, h, l, c, di_length, adx_smoothing)
    strong = P.F(adx > adx_threshold)
    return (P.crossover(plus, minus) & strong, P.crossunder(plus, minus) & strong,
            P.F(plus > minus) & strong, P.F(minus > plus) & strong)


def adx_dmi_exit(o, h, l, c, di_length=14, adx_smoothing=14, adx_threshold=25.0):
    """patch B1. The exit does NOT consult the threshold -- deliberate in the
    patch: you leave on the DI cross whether or not the trend was strong."""
    adx, plus, minus = adx_dmi(o, h, l, c, di_length, adx_smoothing)
    return P.crossunder(plus, minus), P.crossover(plus, minus)


def parabolic_sar(o, h, l, c, sar_start=0.02, sar_increment=0.02, sar_maximum=0.2):
    return P.sar(h, l, sar_start, sar_increment, sar_maximum)


def parabolic_sar_signals(o, h, l, c, sar_start=0.02, sar_increment=0.02,
                          sar_maximum=0.2):
    s = P.sar(h, l, sar_start, sar_increment, sar_maximum)
    lc = P.F(np.asarray(c) > s); sc = P.F(np.asarray(c) < s)
    lt = lc & ~np.concatenate([[False], lc[:-1]])
    st = sc & ~np.concatenate([[False], sc[:-1]])
    return lt, st, lc, sc


def parabolic_sar_exit(o, h, l, c, sar_start=0.02, sar_increment=0.02,
                       sar_maximum=0.2):
    """patch B2. The exit is a CROSS of price and SAR using nz() fallbacks, not
    simply 'price is on the other side'."""
    s = P.sar(h, l, sar_start, sar_increment, sar_maximum)
    c = np.asarray(c, float)
    pc = P.nz(P.shift(c, 1), c); ps = P.nz(P.shift(s, 1), s)
    return P.F((c < s) & (pc > ps)), P.F((c > s) & (pc < ps))


def donchian_breakout(o, h, l, c, length=20):
    """patch B3. The channel is read from the PRIOR bar, with nz() falling back
    to today's own high/low on the first bar."""
    upper = P.nz(P.shift(P.highest(h, length), 1), h)
    lower = P.nz(P.shift(P.lowest(l, length), 1), l)
    return upper, lower, (upper + lower) / 2.0


def donchian_breakout_signals(o, h, l, c, length=20):
    upper, lower, mid = donchian_breakout(o, h, l, c, length)
    d = P.latch(P.F(np.asarray(c) > upper), P.F(np.asarray(c) < lower), init=0)
    pd_ = np.concatenate([[0], d[:-1]])
    return (P.F((d == 1) & (pd_ != 1)), P.F((d == -1) & (pd_ != -1)),
            P.F(d == 1), P.F(d == -1))


def donchian_breakout_exit(o, h, l, c, length=20):
    """patch B3. The exit is the MIDLINE cross, not the channel."""
    upper, lower, mid = donchian_breakout(o, h, l, c, length)
    return P.crossunder(c, mid), P.crossover(c, mid)


def ichimoku(o, h, l, c, conversion_len=9, base_len=26, span_b_len=52,
             displacement=26):
    tenkan = (P.highest(h, conversion_len) + P.lowest(l, conversion_len)) / 2.0
    kijun = (P.highest(h, base_len) + P.lowest(l, base_len)) / 2.0
    span_a = (tenkan + kijun) / 2.0
    span_b = (P.highest(h, span_b_len) + P.lowest(l, span_b_len)) / 2.0
    a = P.nz(P.shift(span_a, displacement), span_a)
    b = P.nz(P.shift(span_b, displacement), span_b)
    return tenkan, kijun, np.maximum(a, b), np.minimum(a, b)


def ichimoku_signals(o, h, l, c, conversion_len=9, base_len=26, span_b_len=52,
                     displacement=26):
    """patch B4. lc requires tenkan > kijun AS WELL AS price above the cloud --
    the prose-built version tested the cloud alone and was far too permissive."""
    tk, kj, top, bot = ichimoku(o, h, l, c, conversion_len, base_len,
                                span_b_len, displacement)
    c = np.asarray(c, float)
    return (P.crossover(tk, kj) & P.F(c > top), P.crossunder(tk, kj) & P.F(c < bot),
            P.F((c > top) & (tk > kj)), P.F((c < bot) & (tk < kj)))


def ichimoku_exit(o, h, l, c, conversion_len=9, base_len=26, span_b_len=52,
                  displacement=26):
    tk, kj, top, bot = ichimoku(o, h, l, c, conversion_len, base_len,
                                span_b_len, displacement)
    return P.crossunder(tk, kj), P.crossover(tk, kj)


def linreg_slope(o, h, l, c, length=14, r2_floor=0.20):
    """patch B5. The slope is linreg(0) - linreg(1), which equals the OLS slope
    coefficient exactly; R^2 is the SQUARE OF ta.correlation(close, bar_index),
    which also equals the regression R^2. Both were arrived at differently in
    the prose version and agree -- checked numerically in main()."""
    slope = P.linreg(c, length, 0) - P.linreg(c, length, 1)
    r = P.correlation(c, np.arange(len(np.asarray(c)), dtype=float), length)
    r2 = P.nz(r * r, 0.0)
    return slope, r2, P.F(r2 > r2_floor)


def linreg_slope_signals(o, h, l, c, length=14, r2_floor=0.20):
    slope, r2, fits = linreg_slope(o, h, l, c, length, r2_floor)
    lc = P.F(slope > 0) & fits
    sc = P.F(slope < 0) & fits
    lt = lc & ~np.concatenate([[False], lc[:-1]])
    st = sc & ~np.concatenate([[False], sc[:-1]])
    return lt, st, lc, sc


def linreg_slope_exit(o, h, l, c, length=14, r2_floor=0.20):
    slope, r2, fits = linreg_slope(o, h, l, c, length, r2_floor)
    z = np.zeros_like(slope)
    return P.crossunder(slope, z), P.crossover(slope, z)


def choppiness_index(o, h, l, c, length=14):
    """patch B6. Falls back to 50.0 (mid-range, no opinion) when the range is
    zero, rather than to na."""
    rng = P.highest(h, length) - P.lowest(l, length)
    s = P.msum(P.tr(h, l, c), length)
    with np.errstate(invalid='ignore', divide='ignore'):
        ci = 100.0 * np.log10(s / rng) / np.log10(length)
    return np.where((rng > 0) & (length > 1), ci, 50.0)


def choppiness_index_volume_signals(o, h, l, c, length=14, ci_threshold=61.8):
    t = P.F(choppiness_index(o, h, l, c, length) < ci_threshold)
    return t, t


def efficiency_ratio(o, h, l, c, length=10):
    c = np.asarray(c, float)
    direction = np.abs(c - P.nz(P.shift(c, length), c))
    vol = P.msum(np.abs(P.change(c)), length)
    with np.errstate(invalid='ignore', divide='ignore'):
        return np.where(vol != 0, direction / vol, 0.0)


def efficiency_ratio_volume_signals(o, h, l, c, length=10, er_threshold=0.30):
    t = P.F(efficiency_ratio(o, h, l, c, length) > er_threshold)
    return t, t


def vertical_horizontal_filter(o, h, l, c, length=28):
    num = P.highest(c, length) - P.lowest(c, length)
    den = P.msum(np.abs(P.change(c)), length)
    with np.errstate(invalid='ignore', divide='ignore'):
        return np.where(den != 0, num / den, 0.0)


def vertical_horizontal_filter_volume_signals(o, h, l, c, length=28,
                                              vhf_threshold=0.35):
    t = P.F(vertical_horizontal_filter(o, h, l, c, length) > vhf_threshold)
    return t, t


def fractal_dimension(o, h, l, c, length=30):
    """patch B9. half = int(length/2) TRUNCATES, so an odd length is legal --
    the prose version raised on odd lengths, which contradicts the source.

    The patch also LATCHES: when any of n1/n2/n3 is non-positive it holds the
    previous value, seeded at 1.5, rather than returning na."""
    half = int(int(length) // 2)
    hh1 = P.highest(h, half); ll1 = P.lowest(l, half)
    n1 = (hh1 - ll1) / half if half > 0 else np.zeros_like(hh1)
    hh2 = P.nz(P.shift(P.highest(h, half), half), hh1)
    ll2 = P.nz(P.shift(P.lowest(l, half), half), ll1)
    n2 = (hh2 - ll2) / half if half > 0 else np.zeros_like(hh2)
    n3 = (P.highest(h, length) - P.lowest(l, length)) / int(length)
    with np.errstate(invalid='ignore', divide='ignore'):
        raw = (np.log(n1 + n2) - np.log(n3)) / np.log(2.0)
    ok = (n1 > 0) & (n2 > 0) & (n3 > 0) & np.isfinite(raw)
    out = np.empty(raw.shape)
    prev = 1.5
    for i in range(raw.size):
        prev = raw[i] if ok[i] else prev
        out[i] = prev
    return out


def fractal_dimension_volume_signals(o, h, l, c, length=30, fd_threshold=1.5):
    t = P.F(fractal_dimension(o, h, l, c, length) < fd_threshold)
    return t, t


def sma_baseline(o, h, l, c, length=20):
    return P.sma(c, length)


def lsma_baseline(o, h, l, c, length=20, lsma_offset=0):
    return P.linreg(c, length, lsma_offset)


# ==========================================================================
# registry
# ==========================================================================
TERNARY = {'adx_dmi', 'ichimoku', 'linreg_slope', 'schaff_trend_cycle',
           'trend_direction_force_index', 'bears_bulls_impulse', 'glitch_index'}

REGISTRY = {}
UNAVAILABLE = set()      # needs a volume series; spot FX has none


def _reg(pine_name, fn, slot, defaults, pine_line, confirmed, kind=None,
         source='library'):
    REGISTRY[pine_name] = dict(fn=fn, slot=slot, defaults=defaults,
                               pine_line=pine_line, confirmed=confirmed,
                               source=source,
                               kind=kind or ('TERNARY' if pine_name.replace('_signals', '')
                                             in TERNARY else
                                             {'volume': 'FILTER',
                                              'baseline': 'BASELINE'}.get(slot, 'BINARY')))


_reg('ssl_channel_signals', ssl_channel_signals, 'confirmation',
     dict(len=10), 'lib 118 / strat 364', True)
_reg('ssl_channel_exit', ssl_channel_exit, 'exit', dict(len=10),
     'lib 128 / strat 828', True)
_reg('dspo_signals', dspo_signals, 'confirmation', dict(len=14),
     'lib 2098 / strat 426', True)
_reg('dspo_exit', dspo_exit, 'exit', dict(len=14), 'lib 2380', True)
_reg('variance_volume_signals', variance_volume_signals, 'volume',
     dict(mode='Price', hline=0.0, method='MA > Variance', lookback=20,
          filter_lookback=20, ema_len=10), 'lib / strat 626-631', True)
_reg('tma_baseline', tma_baseline, 'baseline', dict(length=20),
     'lib / strat 1485', True)

_reg('adx_dmi_signals', adx_dmi_signals, 'confirmation',
     dict(di_length=14, adx_smoothing=14, adx_threshold=25.0), 'patch B1', False)
_reg('adx_dmi_exit', adx_dmi_exit, 'exit',
     dict(di_length=14, adx_smoothing=14, adx_threshold=25.0), 'patch B1', False)
_reg('parabolic_sar_signals', parabolic_sar_signals, 'confirmation',
     dict(sar_start=.02, sar_increment=.02, sar_maximum=.2), 'patch B2', False)
_reg('parabolic_sar_exit', parabolic_sar_exit, 'exit',
     dict(sar_start=.02, sar_increment=.02, sar_maximum=.2), 'patch B2', False)
_reg('donchian_breakout_signals', donchian_breakout_signals, 'confirmation',
     dict(length=20), 'patch B3', False)
_reg('donchian_breakout_exit', donchian_breakout_exit, 'exit',
     dict(length=20), 'patch B3', False)
_reg('ichimoku_signals', ichimoku_signals, 'confirmation',
     dict(conversion_len=9, base_len=26, span_b_len=52, displacement=26),
     'patch B4', False)
_reg('ichimoku_exit', ichimoku_exit, 'exit',
     dict(conversion_len=9, base_len=26, span_b_len=52, displacement=26),
     'patch B4', False)
_reg('linreg_slope_signals', linreg_slope_signals, 'confirmation',
     dict(length=14, r2_floor=.20), 'patch B5', False)
_reg('linreg_slope_exit', linreg_slope_exit, 'exit',
     dict(length=14, r2_floor=.20), 'patch B5', False)
_reg('choppiness_index_volume_signals', choppiness_index_volume_signals,
     'volume', dict(length=14, ci_threshold=61.8), 'patch B6', False)
_reg('efficiency_ratio_volume_signals', efficiency_ratio_volume_signals,
     'volume', dict(length=10, er_threshold=.30), 'patch B7', False)
_reg('vertical_horizontal_filter_volume_signals',
     vertical_horizontal_filter_volume_signals, 'volume',
     dict(length=28, vhf_threshold=.35), 'patch B8', False)
_reg('fractal_dimension_volume_signals', fractal_dimension_volume_signals,
     'volume', dict(length=30, fd_threshold=1.5), 'patch B9', False)
_reg('sma_baseline', sma_baseline, 'baseline', dict(length=20), 'patch B10', False)
_reg('lsma_baseline', lsma_baseline, 'baseline',
     dict(length=20, lsma_offset=0), 'patch B11', False)

KIND = {k: v['kind'] for k, v in REGISTRY.items()}
NOUT = {'confirmation': 4, 'volume': 2, 'exit': 2, 'baseline': 1}


def compute(name, o, h, l, c, **kw):
    r = REGISTRY[name]
    p = dict(r['defaults']); p.update(kw)
    out = r['fn'](o, h, l, c, **p)
    if r['slot'] == 'baseline':
        return np.asarray(out, float)
    return tuple(np.asarray(x, bool) for x in out)


def registry_frame():
    import pandas as pd
    return pd.DataFrame([dict(name=k, slot=v['slot'], kind=v['kind'],
                              n_outputs=NOUT[v['slot']],
                              defaults='; '.join('%s=%s' % kv for kv in v['defaults'].items()),
                              defaults_confirmed=v['confirmed'],
                              pine_line=v['pine_line'], source=v['source'],
                              available=k not in UNAVAILABLE,
                              inert_at_defaults=k in globals().get('INERT_AT_DEFAULTS', set()),
                              inverted_vs_tradingview=k in INVERTED,
                              lookahead_if_nondefault=k in LOOKAHEAD_OPTION)
                         for k, v in REGISTRY.items()])


def main():
    import pandas as pd
    d = pd.read_csv(os.path.join(ROOTDATA, 'ohlc_clean', 'EURUSD.csv'),
                    index_col=0, parse_dates=True)
    o, h, l, c = (d[k].values.astype(float) for k in ('open', 'high', 'low', 'close'))
    R = registry_frame()
    R.to_csv(os.path.join(ROOTOUT, 'l2_indicator_registry.csv'), index=False)
    pd.set_option('display.width', 220); pd.set_option('display.max_colwidth', 52)
    print('PORTED REGISTRY -- %d entries (%d with defaults confirmed against '
          'the Pine source)' % (len(R), int(R.defaults_confirmed.sum())))
    print(R[['name', 'slot', 'kind', 'defaults', 'defaults_confirmed',
             'pine_line']].to_string(index=False))

    print('\nCONTRACT CHECK on EURUSD (%d bars)' % len(d))
    rows = []
    for name, meta in REGISTRY.items():
        out = compute(name, o, h, l, c)
        if meta['slot'] == 'baseline':
            rows.append(dict(name=name, ok=out.shape == c.shape,
                             warmup=int(np.argmax(np.isfinite(out))),
                             long_pct=np.nan, short_pct=np.nan, neutral_pct=np.nan))
            continue
        n = NOUT[meta['slot']]
        ok = len(out) == n and all(x.shape == c.shape and x.dtype == bool for x in out)
        if meta['slot'] == 'confirmation':
            lt, st, lc, sc = out
            # `ok` is SHAPE AND TYPE only. Confirming both directions is a
            # separate, known fault reported by both_directions_audit() -- it
            # must not be folded in here, or one indicator's documented bug
            # makes the structural check read False forever and stop meaning
            # anything.
            rows.append(dict(name=name, ok=ok,
                             both_pct=round(100 * (lc & sc).mean(), 2),
                             warmup=int(np.argmax(lc | sc)),
                             long_pct=round(100 * lc.mean(), 1),
                             short_pct=round(100 * sc.mean(), 1),
                             neutral_pct=round(100 * (~lc & ~sc).mean(), 1)))
        else:
            a, b = out
            rows.append(dict(name=name, ok=ok, warmup=int(np.argmax(a)),
                             long_pct=round(100 * a.mean(), 1),
                             short_pct=round(100 * b.mean(), 1), neutral_pct=np.nan))
    T = pd.DataFrame(rows)
    print(T.tail(24).to_string(index=False))
    print('\n  %d indicators; every contract correctly shaped and typed: %s'
          % (len(T), bool(T.ok.all())))
    A = both_directions_audit(o, h, l, c)
    A.to_csv(os.path.join(ROOTOUT, 'l2_both_directions_audit.csv'), index=False)
    bad = A[A.both_pct > 0]
    print('  confirmations audited for the A5 fault (confirms BOTH ways): %d'
          % len(A))
    if len(bad):
        print('  STILL FAULTY -- ported as written, flagged, not fixed:')
        print(bad.to_string(index=False))
    else:
        print('  none confirm both directions')

    # the two independent routes to the regression slope must agree
    sl_a = P.linreg(c, 14, 0) - P.linreg(c, 14, 1)
    W = P._roll(c, 14); x = np.arange(14.); xd = x - x.mean()
    sl_b = ((W - W.mean(axis=1, keepdims=True)) * xd).sum(axis=1) / (xd * xd).sum()
    m = np.isfinite(sl_a) & np.isfinite(sl_b)
    print('  linreg(0)-linreg(1) == the OLS slope: max diff %.3e' %
          np.abs(sl_a[m] - sl_b[m]).max())
    r = P.correlation(c, np.arange(len(c), dtype=float), 14)
    ssr = (sl_b ** 2) * (xd * xd).sum()
    sst = ((W - W.mean(axis=1, keepdims=True)) ** 2).sum(axis=1)
    with np.errstate(invalid='ignore'):
        r2b = ssr / sst
    m = np.isfinite(r) & np.isfinite(r2b)
    print('  correlation^2 == regression R^2:      max diff %.3e' %
          np.abs(r[m] ** 2 - r2b[m]).max())
    print('\nwrote results/l2_indicator_registry.csv')
    return T




# ==========================================================================
# BASELINE SLOT -- all 14. The baseline is the direction gate on every entry
# and the source of route 1's trigger, so a wrong one corrupts every
# combination that selects it, not just its own row.
#
# VWMA needs a volume series and spot FX has none; it is registered so the
# slot is complete and tagged UNAVAILABLE so the sweep can exclude it
# explicitly rather than silently scoring NaN.
# ==========================================================================


def moving_average(o, h, l, c, ma_type='EMA', ma_length=20, volume=None):
    """lib: the five ta.* wrappers behind one switch. Pine's default arm
    returns 0.0 for an unknown type -- kept, because a silent zero baseline is
    a thing a sweep could hit and it must look the same in both languages."""
    if ma_type == 'HMA':
        return P.hma(c, ma_length)
    if ma_type == 'EMA':
        return P.ema(c, ma_length)
    if ma_type == 'RMA':
        return P.rma(c, ma_length)
    if ma_type == 'WMA':
        return P.wma(c, ma_length)
    if ma_type == 'VWMA':
        if volume is None:
            return np.full(np.asarray(c).shape, np.nan)
        return P.vwma(c, volume, ma_length)
    return np.zeros(np.asarray(c).shape)


def ema_baseline(o, h, l, c, ma_length=20):
    return moving_average(o, h, l, c, 'EMA', ma_length)


def hma_baseline(o, h, l, c, ma_length=20):
    return moving_average(o, h, l, c, 'HMA', ma_length)


def rma_baseline(o, h, l, c, ma_length=20):
    return moving_average(o, h, l, c, 'RMA', ma_length)


def wma_baseline(o, h, l, c, ma_length=20):
    return moving_average(o, h, l, c, 'WMA', ma_length)


def vwma_baseline(o, h, l, c, ma_length=20):
    """UNAVAILABLE on spot FX -- no volume series exists."""
    return moving_average(o, h, l, c, 'VWMA', ma_length, volume=None)


def kama_baseline(o, h, l, c, length=10, fast_length=2, slow_length=30):
    """lib. Seeded with the source, NOT with an SMA -- `nz(kama[1], src)`."""
    c = np.asarray(c, float)
    chg = np.abs(c - P.shift(c, length))
    vol = P.msum(np.abs(c - P.shift(c, 1)), length)
    with np.errstate(invalid='ignore', divide='ignore'):
        er = np.where(vol != 0, chg / vol, 0.0)
    fsc, ssc = 2.0 / (fast_length + 1), 2.0 / (slow_length + 1)
    sc = (er * (fsc - ssc) + ssc) ** 2
    out = np.empty(c.shape); prev = np.nan
    for i in range(c.size):
        base = c[i] if not np.isfinite(prev) else prev
        s = sc[i] if np.isfinite(sc[i]) else 0.0
        prev = base + s * (c[i] - base)
        out[i] = prev
    return out


def alma_baseline(o, h, l, c, length=9, offset=0.85, sigma=6):
    return P.alma(c, length, offset, sigma)


def t3_baseline(o, h, l, c, length=10, volume_factor=0.7):
    b = volume_factor
    c1 = -b ** 3
    c2 = 3 * b * b + 3 * b ** 3
    c3 = -6 * b * b - 3 * b - 3 * b ** 3
    c4 = 1 + 3 * b + b ** 3 + 3 * b * b
    e = c
    es = []
    for _ in range(6):
        e = P.ema(e, length); es.append(e)
    return c1 * es[5] + c2 * es[4] + c3 * es[3] + c4 * es[2]


def super_smoother_2pole_baseline(o, h, l, c, cutoff_period=15):
    """ss := c1*(src + src[1])/2 + c2*ss[1] + c3*ss[2], all nz-seeded at 0."""
    c = np.asarray(c, float)
    a1 = np.exp(-1.414 * np.pi / cutoff_period)
    b1 = 2 * a1 * np.cos(1.414 * np.pi / cutoff_period)
    c2, c3 = b1, -a1 * a1
    c1 = 1 - c2 - c3
    out = np.empty(c.shape); p1 = p2 = 0.0
    for i in range(c.size):
        prev_src = c[i - 1] if i >= 1 else 0.0
        v = c1 * (c[i] + prev_src) / 2.0 + c2 * p1 + c3 * p2
        out[i] = v; p2 = p1; p1 = v
    return out


def frama_baseline(o, h, l, c, length=10):
    """lib. Note the latch is `nz(d_raw[1])` -- the PREVIOUS BAR'S RAW value,
    not the previous smoothed d, and nz() sends it to 0 rather than holding.
    That is what the source says; the patch's fractal_dimension does it
    differently on purpose and the two are not interchangeable."""
    c = np.asarray(c, float)
    half = int(P.idiv(int(length), 2))
    n1 = (P.highest(h, half) - P.lowest(l, half)) / half
    n2 = (P.shift(P.highest(h, half), half) - P.shift(P.lowest(l, half), half)) / half
    n3 = (P.highest(h, length) - P.lowest(l, length)) / int(length)
    with np.errstate(invalid='ignore', divide='ignore'):
        d_raw = (np.log(n1 + n2) - np.log(n3)) / np.log(2.0)
    ok = (n1 > 0) & (n2 > 0) & (n3 > 0)
    d = np.where(ok, d_raw, P.nz(P.shift(d_raw, 1), 0.0))
    alpha = np.clip(np.exp(-4.6 * (d - 1.0)), 0.01, 1.0)
    out = np.empty(c.shape); prev = np.nan
    for i in range(c.size):
        a = alpha[i] if np.isfinite(alpha[i]) else 1.0
        base = c[i] if not np.isfinite(prev) else prev
        prev = a * c[i] + (1 - a) * base
        out[i] = prev
    return out


def mcginley_dynamic_index(o, h, l, c, mci_length=14):
    """mg := na(mg[1]) ? ema : mg[1] + (src-mg[1]) / (len * (src/mg[1])^4)."""
    c = np.asarray(c, float)
    e = P.ema(c, mci_length)
    out = np.full(c.shape, np.nan); prev = np.nan
    for i in range(c.size):
        if not np.isfinite(prev):
            prev = e[i]
        else:
            r = c[i] / prev if prev != 0 else 1.0
            den = mci_length * (r ** 4)
            prev = prev + (c[i] - prev) / den if den != 0 else prev
        out[i] = prev
    return out


def vidya(o, h, l, c, vda_length=2, vda_fixed_cmo_length=True,
          vda_calculation_method=True):
    """patch A10 -- the dead col12/col32 assignments removed, nothing else."""
    c = np.asarray(c, float)
    pds = int(vda_length)
    alpha = 2.0 / (pds + 1)
    momm = P.change(c)
    m1 = np.where(momm >= 0, momm, 0.0)
    m2 = np.where(momm >= 0, 0.0, -momm)
    sm1 = P.msum(m1, 9 if vda_fixed_cmo_length else pds)
    sm2 = P.msum(m2, 9 if vda_fixed_cmo_length else pds)
    with np.errstate(invalid='ignore', divide='ignore'):
        cmo = P.nz(100.0 * ((sm1 - sm2) / (sm1 + sm2)), 0.0)
    k = np.abs(cmo) / 100.0 if vda_calculation_method else P.stdev(c, pds)
    out = np.empty(c.shape); prev = 0.0
    for i in range(c.size):
        v = k[i] if np.isfinite(k[i]) else 0.0
        term = alpha * v * c[i]
        prev = (0.0 if not np.isfinite(term) else term) + (1 - alpha * v) * prev
        out[i] = prev
    return out


def fantail_vma(o, h, l, c, fma_adx_length=2, fma_weighting=10.0,
                fma_ma_length=6):
    """lib, including its two CW fixes. Every recursion is `var`-scoped and
    seeded at 0 except VarMA, which seeds at close."""
    h = np.asarray(h, float); l = np.asarray(l, float); c = np.asarray(c, float)
    n = c.size
    w = float(fma_weighting)
    sPDI = sMDI = FSTR = ADX = 0.0
    adx_hist = np.empty(n)
    varma = np.empty(n)
    vm = c[0]
    for i in range(n):
        hi1 = h[i - 1] if i else h[i]
        lo1 = l[i - 1] if i else l[i]
        cl1 = c[i - 1] if i else c[i]
        fb1 = 0.5 * (abs(h[i] - hi1) + h[i] - hi1)
        fbe1 = 0.5 * (abs(lo1 - l[i]) + lo1 - l[i])
        fbears = 0.0 if fb1 >= fbe1 else fbe1
        fbulls = 0.0 if fb1 <= fbe1 else fb1
        tr_ = max(h[i] - l[i], h[i] - cl1)
        if i > 0:
            sPDI = (w * sPDI + fbulls) / (w + 1)
            sMDI = (w * sMDI + fbears) / (w + 1)
            FSTR = (w * FSTR + tr_) / (w + 1)
        else:
            FSTR = h[i] - l[i]
        pdi = sPDI / FSTR if FSTR > 0 else 0.0
        mdi = sMDI / FSTR if FSTR > 0 else 0.0
        dx = abs(pdi - mdi) / (pdi + mdi) if (pdi + mdi) > 0 else 0.0
        if i > 0:
            ADX = (w * ADX + dx) / (w + 1)
        adx_hist[i] = ADX
        lo_i = max(0, i - int(fma_adx_length) + 1)
        win = adx_hist[lo_i:i + 1]
        amin = min(1000000.0, win.min()); amax = max(-1.0, win.max())
        diff = amax - amin
        const = (ADX - amin) / diff if diff > 0 else 0.0
        if i > 0:
            vm = ((2 - const) * vm + const * c[i]) / 2.0
        varma[i] = vm
    return P.sma(varma, fma_ma_length)


# --- baselines. Defaults are the strategy file's input() lines, 1467-1510.
for _n, _f, _d, _ln in [
        ('ema_baseline', ema_baseline, dict(ma_length=20), 'strat 1469'),
        ('hma_baseline', hma_baseline, dict(ma_length=20), 'strat 1467'),
        ('rma_baseline', rma_baseline, dict(ma_length=20), 'strat 1471'),
        ('wma_baseline', wma_baseline, dict(ma_length=20), 'strat 1473'),
        ('vwma_baseline', vwma_baseline, dict(ma_length=20), 'strat 1475'),
        ('fantail_vma', fantail_vma,
         dict(fma_adx_length=2, fma_weighting=10.0, fma_ma_length=6), 'strat 1477-1480'),
        ('mcginley_dynamic_index', mcginley_dynamic_index,
         dict(mci_length=14), 'strat 1482'),
        ('vidya', vidya, dict(vda_length=2, vda_fixed_cmo_length=True,
                              vda_calculation_method=True), 'strat 1486-1489'),
        ('kama_baseline', kama_baseline,
         dict(length=10, fast_length=2, slow_length=30), 'strat 1491-1495'),
        ('alma_baseline', alma_baseline,
         dict(length=9, offset=0.85, sigma=6), 'strat 1497-1500'),
        ('t3_baseline', t3_baseline, dict(length=10, volume_factor=0.7),
         'strat 1502-1504'),
        ('super_smoother_2pole_baseline', super_smoother_2pole_baseline,
         dict(cutoff_period=15), 'strat 1506'),
        ('frama_baseline', frama_baseline, dict(length=10), 'strat 1509')]:
    _reg(_n, _f, 'baseline', _d, _ln, True)
UNAVAILABLE.add('vwma_baseline')      # needs a volume series; spot FX has none

KIND.update({k: v['kind'] for k, v in REGISTRY.items()})




# ==========================================================================
# VOLUME SLOT -- all 12. Despite the slot's name only FOUR of them actually
# read a volume series, and spot FX has none, so those four are UNAVAILABLE.
# The rest are volatility or range measures and work perfectly well here.
#
# The four that cannot run: Chaikin Oscillator (ta.accdist), Elders Force
# Index (change * volume), Normalized Volume, Volume Zone Oscillator. Pine
# itself calls runtime.error("No volume is provided by the data vendor.") in
# two of them, so this is the library's own verdict, not an outside opinion.
# ==========================================================================


def _novol(c):
    return np.full(np.asarray(c).shape, np.nan)


def chaikin_oscillator(o, h, l, c, fastlength=3, slowlength=10, volume=None):
    """UNAVAILABLE -- ta.accdist is a volume accumulation."""
    return _novol(c)


def chaikin_oscillator_volume_signals(o, h, l, c, fast_len=3, slow_len=10):
    """patch A1: was `not na(v)` on every bar. Now directional on the sign."""
    v = chaikin_oscillator(o, h, l, c, fast_len, slow_len)
    return P.F(v > 0), P.F(v < 0)


def chaikin_volatility(o, h, l, c, cv_length=10, roc_length=12):
    """Rate of change of the smoothed high-low range. NO VOLUME -- despite the
    name this one is a pure range measure and runs fine on FX."""
    rng = np.asarray(h, float) - np.asarray(l, float)
    e = P.ema(rng, cv_length)
    prev = P.shift(e, roc_length)
    with np.errstate(invalid='ignore', divide='ignore'):
        return np.where(prev != 0, 100.0 * (e - prev) / prev, np.nan)


def chaikin_volatility_volume_signals(o, h, l, c, cvi_len=10, roc_len=12):
    """patch A2: non-directional expansion filter -- trade only when the range
    is opening up."""
    t = P.F(chaikin_volatility(o, h, l, c, cvi_len, roc_len) > 0)
    return t, t


def elders_force_index(o, h, l, c, efi_length=10, volume=None):
    """UNAVAILABLE -- ta.change(close) * volume."""
    return _novol(c)


def elders_force_index_volume_signals(o, h, l, c, len=10):
    """patch A3: directional on the sign, was a no-op."""
    v = elders_force_index(o, h, l, c, len)
    return P.F(v > 0), P.F(v < 0)


def normalized_volume(o, h, l, c, nv_volume_period=10, volume=None):
    """UNAVAILABLE."""
    return _novol(c)


def normalized_volume_volume_signals(o, h, l, c, vol_period=10):
    t = P.F(normalized_volume(o, h, l, c, vol_period) > 0)
    return t, t


def volume_zone_oscillator(o, h, l, c, vzo_length=20, vzo_smooth_enabled_=True,
                           vzo_smooth_=20, vzo_nuetral_zone=10, volume=None):
    """UNAVAILABLE -- signed volume over total volume."""
    n = _novol(c)
    return n, n, n


def volume_zone_oscillator_volume_signals(o, h, l, c, len=20, smooth=True,
                                          smooth_len=20, neutral_zone=10):
    _, lc, sc = volume_zone_oscillator(o, h, l, c, len, smooth, smooth_len,
                                       neutral_zone)
    return P.F(lc == 1.0), P.F(sc == 1.0)


def waddah_attar_explosion(o, h, l, c, wea_sensetivity=150,
                           wea_fast_ema_length=20, wea_slow_length=40,
                           wea_bb_channel_length=20, wea_stdev_multiplier=2.0):
    """lib. NOTE Pine computes ta.ema(close[1], L) -- an EMA OF THE SHIFTED
    SERIES, not the shifted EMA. On a recursive average those are the same
    series offset by one bar only after warm-up; during warm-up they differ
    because each re-seeds at a different bar. Ported as ema(shift(close,k)),
    which is what is written."""
    c = np.asarray(c, float)
    f, s = wea_fast_ema_length, wea_slow_length
    d0 = P.ema(c, f) - P.ema(c, s)
    d1 = P.ema(P.shift(c, 1), f) - P.ema(P.shift(c, 1), s)
    d2 = P.ema(P.shift(c, 2), f) - P.ema(P.shift(c, 2), s)
    d3 = P.ema(P.shift(c, 3), f) - P.ema(P.shift(c, 3), s)
    t1 = d0 - d1 * wea_sensetivity
    dev = wea_stdev_multiplier * P.stdev(c, wea_bb_channel_length)
    e1 = 2.0 * dev                       # (basis+dev) - (basis-dev)
    up = np.where(t1 >= 0, t1, 0.0)
    dn = np.where(t1 < 0, -t1, 0.0)
    return e1, up, dn


def waddah_attar_explosion_volume_signals(o, h, l, c, sensitivity=150,
                                          fastEma=20, slowEma=40, bbLen=20,
                                          bbStd=2.0):
    e1, up, dn = waddah_attar_explosion(o, h, l, c, sensitivity, fastEma,
                                        slowEma, bbLen, bbStd)
    return P.F(up > e1), P.F(dn > e1)


def damiani_volatmeter(o, h, l, c, viscosity=7, sedimentation=50,
                       threshold=1.4, lag=1.4, use_lag=True):
    short = P.atr(h, l, c, viscosity)
    long_ = P.atr(h, l, c, sedimentation)
    with np.errstate(invalid='ignore', divide='ignore'):
        ratio = np.where(long_ != 0, short / long_, 0.0)
    vmeter = ratio - lag if use_lag else ratio
    return vmeter, threshold, P.F(vmeter > threshold)


def damiani_volatmeter_volume_signals(o, h, l, c, viscosity=7,
                                      sedimentation=50, threshold=1.4,
                                      lag=1.4, use_lag=True):
    _, _, t = damiani_volatmeter(o, h, l, c, viscosity, sedimentation,
                                 threshold, lag, use_lag)
    return t, t


def ttm_squeeze(o, h, l, c, bb_length=20, bb_mult=2.0, kc_length=20,
                kc_mult=1.5):
    basis = P.sma(c, bb_length)
    dev = bb_mult * P.stdev(c, bb_length)
    kc_basis = P.sma(c, kc_length)
    kc_range = P.sma(P.tr(h, l, c), kc_length)
    in_sq = P.F((basis + dev < kc_basis + kc_mult * kc_range) &
                (basis - dev > kc_basis - kc_mult * kc_range))
    return in_sq, ~in_sq


def ttm_squeeze_volume_signals(o, h, l, c, bb_length=20, bb_mult=2.0,
                               kc_length=20, kc_mult=1.5):
    """Passes when the squeeze is OFF -- the market has broken out of it."""
    _, out_sq = ttm_squeeze(o, h, l, c, bb_length, bb_mult, kc_length, kc_mult)
    return out_sq, out_sq


def williams_vix_fix(o, h, l, c, lookback=22, bb_length=20, bb_mult=2.0):
    hi = P.highest(c, lookback)
    with np.errstate(invalid='ignore', divide='ignore'):
        wvf = ((hi - np.asarray(l, float)) / hi) * 100.0
    upper = P.sma(wvf, bb_length) + bb_mult * P.stdev(wvf, bb_length)
    return wvf, upper, P.F(wvf >= upper)


def williams_vix_fix_volume_signals(o, h, l, c, lookback=22, bb_length=20,
                                    bb_mult=2.0):
    _, _, hv = williams_vix_fix(o, h, l, c, lookback, bb_length, bb_mult)
    return hv, hv


def volatility_ratio(o, h, l, c, length=14):
    t = P.tr(h, l, c)
    avg = P.sma(t, length)
    with np.errstate(invalid='ignore', divide='ignore'):
        vr = np.where(avg != 0, t / avg, 0.0)
    return vr, P.F(vr > 1.0)


def volatility_ratio_volume_signals(o, h, l, c, length=14):
    _, e = volatility_ratio(o, h, l, c, length)
    return e, e


def mass_index(o, h, l, c, length=25, ema_length=9):
    """lib. `bulge_break` compares RATIO against 26.5, not the mass index --
    ratio is an EMA quotient hovering near 1.0, so that term can never be true.
    Preserved: it is in the source, the patch does not touch it, and silently
    'fixing' it would change a shipped indicator's behaviour."""
    rng = np.asarray(h, float) - np.asarray(l, float)
    e1 = P.ema(rng, ema_length)
    e2 = P.ema(e1, ema_length)
    with np.errstate(invalid='ignore', divide='ignore'):
        ratio = np.where(e2 != 0, e1 / e2, 0.0)
    mi = P.msum(ratio, length)
    reversal = P.F(mi > 27.0)
    bulge = P.F((mi > 26.5) & (P.shift(mi, 1) >= 26.5) & (ratio < 26.5))
    return mi, reversal | bulge


def mass_index_volume_signals(o, h, l, c, length=25, ema_length=9):
    _, sig = mass_index(o, h, l, c, length, ema_length)
    return sig, sig


# --- volume slot. Defaults from the strategy input() lines 595-640.
for _n, _f, _d, _ln, _av in [
        ('chaikin_oscillator_volume_signals', chaikin_oscillator_volume_signals,
         dict(fast_len=3, slow_len=10), 'strat 595-596 / patch A1', False),
        ('chaikin_volatility_volume_signals', chaikin_volatility_volume_signals,
         dict(cvi_len=10, roc_len=12), 'strat 599-600 / patch A2', True),
        ('elders_force_index_volume_signals', elders_force_index_volume_signals,
         dict(len=10), 'strat 606 / patch A3', False),
        ('normalized_volume_volume_signals', normalized_volume_volume_signals,
         dict(vol_period=10), 'strat 609', False),
        ('volume_zone_oscillator_volume_signals',
         volume_zone_oscillator_volume_signals,
         dict(len=20, smooth=True, smooth_len=20, neutral_zone=10),
         'strat 631-634', False),
        ('waddah_attar_explosion_volume_signals',
         waddah_attar_explosion_volume_signals,
         dict(sensitivity=150, fastEma=20, slowEma=40, bbLen=20, bbStd=2.0),
         'strat 636-640', True),
        ('damiani_volatmeter_volume_signals', damiani_volatmeter_volume_signals,
         dict(viscosity=7, sedimentation=50, threshold=1.4, lag=1.4, use_lag=True),
         'strat 601-605', True),
        ('ttm_squeeze_volume_signals', ttm_squeeze_volume_signals,
         dict(bb_length=20, bb_mult=2.0, kc_length=20, kc_mult=1.5),
         'strat 617-620', True),
        ('williams_vix_fix_volume_signals', williams_vix_fix_volume_signals,
         dict(lookback=22, bb_length=20, bb_mult=2.0), 'strat 641-643', True),
        ('volatility_ratio_volume_signals', volatility_ratio_volume_signals,
         dict(length=14), 'strat 630', True),
        ('mass_index_volume_signals', mass_index_volume_signals,
         dict(length=25, ema_length=9), 'strat 607-608', True)]:
    _reg(_n, _f, 'volume', _d, _ln, True)
    if not _av:
        UNAVAILABLE.add(_n)

KIND.update({k: v['kind'] for k, v in REGISTRY.items()})


# ==========================================================================
# CONFIRMATION SLOT (C1 / C2 / exit). Batch A -- the oscillators and the
# structural ones whose maths is self-contained.
#
# The dominant idiom in this library's signal helpers is the ZERO CROSS
# written by hand as `v[1] < 0 and v > 0` rather than ta.crossover(v, 0).
# They differ when v is exactly 0 on the previous bar: ta.crossover requires
# prev <= 0, the hand-written form requires prev < 0. Kept as written.
# ==========================================================================


def _zero_cross(v):
    """The library's standard four-tuple off a single oscillator."""
    pv = P.shift(v, 1)
    return (P.F((pv < 0) & (v > 0)), P.F((pv > 0) & (v < 0)),
            P.F(v > 0), P.F(v < 0))


def _zero_cross_exit(v):
    pv = P.shift(v, 1)
    return P.F((pv > 0) & (v < 0)), P.F((pv < 0) & (v > 0))


def chaikin_money_flow(o, h, l, c, lookback=50, volume=None):
    """UNAVAILABLE -- the accumulation term is multiplied by volume."""
    return _novol(c)


def chaikin_money_flow_signals(o, h, l, c, lookback=50):
    return _zero_cross(chaikin_money_flow(o, h, l, c, lookback))


def chaikin_money_flow_exit(o, h, l, c, lookback=50):
    return _zero_cross_exit(chaikin_money_flow(o, h, l, c, lookback))


def coppock_curve(o, h, l, c, cc_smoothing_length=10, cc_long_roc_length=14,
                  cc_short_roc_length=11):
    return P.wma(P.roc(c, cc_long_roc_length) + P.roc(c, cc_short_roc_length),
                 cc_smoothing_length)


def coppock_curve_signals(o, h, l, c, smooth_len=10, long_roc=14, short_roc=11):
    return _zero_cross(coppock_curve(o, h, l, c, smooth_len, long_roc, short_roc))


def coppock_curve_exit(o, h, l, c, smooth_len=10, long_roc=14, short_roc=11):
    return _zero_cross_exit(coppock_curve(o, h, l, c, smooth_len, long_roc,
                                          short_roc))


def dpo(o, h, l, c, dpo_length=50, dpo_centered=False):
    """Detrended Price Oscillator. CENTERED IS A LOOK-AHEAD: it reads
    close[barsback], which is fine, but the UNcentred branch shifts the MA
    instead, and only the uncentred branch is causal. The strategy's default is
    centered=false, so the shipped configuration is safe; a sweep that turns it
    on is reading the future and the registry flags it."""
    barsback = int(P.idiv(int(dpo_length), 2)) + 1
    ma = P.sma(c, dpo_length)
    if dpo_centered:
        return P.shift(c, barsback) - ma
    return np.asarray(c, float) - P.shift(ma, barsback)


def dpo_signals(o, h, l, c, len=50, centered=False):
    return _zero_cross(dpo(o, h, l, c, len, centered))


def dpo_exit(o, h, l, c, len=50, centered=False):
    return _zero_cross_exit(dpo(o, h, l, c, len, centered))


def ease_of_movement(o, h, l, c, eom_length=14, eom_divisor=10000, volume=None):
    """UNAVAILABLE -- divides by volume."""
    return _novol(c)


def ease_of_movement_signals(o, h, l, c, len=14, divisor=10000):
    return _zero_cross(ease_of_movement(o, h, l, c, len, divisor))


def ease_of_movement_exit(o, h, l, c, len=14, divisor=10000):
    return _zero_cross_exit(ease_of_movement(o, h, l, c, len, divisor))


def kalman_filter(o, h, l, c, k_sharpness=1.0, kf_k=1.0):
    """lib. Both recursions seed off the source, not zero."""
    src = (np.asarray(o, float) + np.asarray(h, float) + np.asarray(l, float)
           + np.asarray(c, float)) / 4.0
    n = src.size
    vel = np.empty(n); filt = np.empty(n)
    pv, pf = 0.0, np.nan
    rt = np.sqrt(k_sharpness * kf_k / 100.0)
    for i in range(n):
        base = src[i] if not np.isfinite(pf) else pf
        dist = src[i] - base
        err = base + dist * rt
        pv = pv + dist * kf_k / 100.0
        pf = err + pv
        vel[i] = pv; filt[i] = pf
    return vel


def kalman_filter_signals(o, h, l, c, sharpness=1.0, k=1.0):
    v = kalman_filter(o, h, l, c, sharpness, k)
    pv = P.shift(v, 1)
    return (P.F((v > 0) & (pv < 0)), P.F((v < 0) & (pv > 0)),
            P.F(v > 0), P.F(v < 0))


def kalman_filter_exit(o, h, l, c, sharpness=1.0, k=1.0):
    return _zero_cross_exit(kalman_filter(o, h, l, c, sharpness, k))


def laguerre_filter(o, h, l, c, lf_alpha=0.2):
    """Four-stage Laguerre cascade, every stage nz-seeded at zero."""
    src = (np.asarray(h, float) + np.asarray(l, float)) / 2.0
    g = 1.0 - lf_alpha
    n = src.size
    out = np.empty(n)
    l0 = l1 = l2 = l3 = 0.0
    for i in range(n):
        p0, p1, p2 = l0, l1, l2
        l0 = (1 - g) * src[i] + g * l0
        l1 = -g * l0 + p0 + g * l1
        l2 = -g * l1 + p1 + g * l2
        l3 = -g * l2 + p2 + g * l3
        out[i] = (l0 + 2 * l1 + 2 * l2 + l3) / 6.0
    return out


def laguerre_filter_signals(o, h, l, c, alpha=0.2):
    v = laguerre_filter(o, h, l, c, alpha)
    col = P.F(v > P.shift(v, 1))
    prev = np.concatenate([[False], col[:-1]])
    return col & ~prev, ~col & prev, col, ~col


def laguerre_filter_exit(o, h, l, c, alpha=0.2):
    v = laguerre_filter(o, h, l, c, alpha)
    col = P.F(v > P.shift(v, 1))
    prev = np.concatenate([[False], col[:-1]])
    return ~col & prev, col & ~prev


def price_momentum_oscillator(o, h, l, c, pmo_1st_length=35, pmo_2nd_length=20,
                              pmo_signal_length=10):
    return P.ema(10.0 * P.ema(P.nz(P.roc(c, 1), 0.0), pmo_1st_length),
                 pmo_2nd_length)


def price_momentum_oscillator_signals(o, h, l, c, s1=35, s2=20, sig=10):
    return _zero_cross(price_momentum_oscillator(o, h, l, c, s1, s2, sig))


def price_momentum_oscillator_exit(o, h, l, c, s1=35, s2=20, sig=10):
    return _zero_cross_exit(price_momentum_oscillator(o, h, l, c, s1, s2, sig))


def relative_vigor_index(o, h, l, c, relative_vigor_length=10):
    num = P.msum(P.swma(np.asarray(c, float) - np.asarray(o, float)),
                 relative_vigor_length)
    den = P.msum(P.swma(np.asarray(h, float) - np.asarray(l, float)),
                 relative_vigor_length)
    with np.errstate(invalid='ignore', divide='ignore'):
        rvi = np.where(den != 0, num / den, np.nan)
    return rvi, P.swma(rvi)


def relative_vigor_index_signals(o, h, l, c, len=10):
    """NOTE the direction: lc is SIGNAL above VALUE, which is the opposite of
    the usual RVI reading. As written in the library."""
    v, sg = relative_vigor_index(o, h, l, c, len)
    return P.crossover(sg, v), P.crossunder(sg, v), P.F(sg > v), P.F(sg < v)


def relative_vigor_index_exit(o, h, l, c, len=10):
    v, sg = relative_vigor_index(o, h, l, c, len)
    return P.crossunder(sg, v), P.crossover(sg, v)


def supertrend_signals(o, h, l, c, factor=3.0, atr_period=10):
    """lib. THE DIRECTION IS READ BACKWARDS AND THE PATCH DOES NOT FIX IT.

    ta.supertrend returns -1 for an UP trend and +1 for a down trend. This
    helper sets lc = dir > 0, i.e. it confirms LONG while the supertrend says
    DOWN. Ported exactly as written, because the patch is the authority on what
    is a bug and it does not mention this one -- silently inverting it would
    make every TradingView comparison on Supertrend disagree. Flagged in the
    registry as inverted_vs_tradingview."""
    line, d = P.supertrend(h, l, c, factor, atr_period)
    pd_ = P.shift(d, 1)
    return (P.F((d > 0) & (pd_ < 0)), P.F((d < 0) & (pd_ > 0)),
            P.F(d > 0), P.F(d < 0))


def supertrend_exit(o, h, l, c, factor=3.0, atr_period=10):
    line, d = P.supertrend(h, l, c, factor, atr_period)
    pd_ = P.shift(d, 1)
    return P.F((d < 0) & (pd_ > 0)), P.F((d > 0) & (pd_ < 0))


def fisher_transform(o, h, l, c, length=10):
    src = (np.asarray(h, float) + np.asarray(l, float)) / 2.0
    hi, lo = P.highest(src, length), P.lowest(src, length)
    rng = hi - lo
    with np.errstate(invalid='ignore', divide='ignore'):
        raw = np.where(rng == 0, 0.0, 0.66 * ((src - lo) / rng - 0.5))
    n = src.size
    fish = np.empty(n); val = 0.0; f = 0.0
    for i in range(n):
        r = raw[i] if np.isfinite(raw[i]) else 0.0
        val = 0.67 * r + 0.33 * val
        cl = min(max(val, -0.999), 0.999)
        f = 0.5 * np.log((1 + cl) / (1 - cl)) + 0.5 * f
        fish[i] = f
    return fish, P.shift(fish, 1)


def fisher_transform_signals(o, h, l, c, length=10):
    f, t = fisher_transform(o, h, l, c, length)
    return P.crossover(f, t), P.crossunder(f, t), P.F(f > t), P.F(f < t)


def fisher_transform_exit(o, h, l, c, length=10):
    f, t = fisher_transform(o, h, l, c, length)
    return P.crossunder(f, t), P.crossover(f, t)


def aroon_updown(o, h, l, c, length=25):
    up = 100.0 * (length - (-P.highestbars(h, length + 1))) / length
    dn = 100.0 * (length - (-P.lowestbars(l, length + 1))) / length
    return up, dn


def aroon_signals(o, h, l, c, length=25):
    up, dn = aroon_updown(o, h, l, c, length)
    return P.crossover(up, dn), P.crossunder(up, dn), P.F(up > dn), P.F(up < dn)


def aroon_exit(o, h, l, c, length=25):
    up, dn = aroon_updown(o, h, l, c, length)
    return P.crossunder(up, dn), P.crossover(up, dn)


def center_of_gravity(o, h, l, c, length=10, signal_length=3):
    src = (np.asarray(h, float) + np.asarray(l, float)) / 2.0
    W = P._roll(src, length)                 # window ending at i, oldest first
    w = np.arange(length, 0, -1, dtype=float)   # (1+i) with i counting back
    num = (W * w).sum(axis=1)
    den = W.sum(axis=1)
    with np.errstate(invalid='ignore', divide='ignore'):
        cog = np.where(den != 0, -num / den + (length + 1) / 2.0, 0.0)
    return cog, P.sma(cog, signal_length)


def center_of_gravity_signals(o, h, l, c, length=10, signal_length=3):
    v, sg = center_of_gravity(o, h, l, c, length, signal_length)
    return P.crossover(v, sg), P.crossunder(v, sg), P.F(v > sg), P.F(v < sg)


def center_of_gravity_exit(o, h, l, c, length=10, signal_length=3):
    v, sg = center_of_gravity(o, h, l, c, length, signal_length)
    return P.crossunder(v, sg), P.crossover(v, sg)


# --- confirmation batch A. Defaults from strategy input() lines 176-262.
INVERTED = set()          # ported as written, but reads its source backwards
LOOKAHEAD_OPTION = set()  # has a non-default setting that reads the future

for _n, _f, _slot, _d, _ln in [
        ('chaikin_money_flow_signals', chaikin_money_flow_signals, 'confirmation',
         dict(lookback=50), 'strat 181'),
        ('chaikin_money_flow_exit', chaikin_money_flow_exit, 'exit',
         dict(lookback=50), 'strat 181'),
        ('coppock_curve_signals', coppock_curve_signals, 'confirmation',
         dict(smooth_len=10, long_roc=14, short_roc=11), 'strat 185-187'),
        ('coppock_curve_exit', coppock_curve_exit, 'exit',
         dict(smooth_len=10, long_roc=14, short_roc=11), 'strat 185-187'),
        ('dpo_signals', dpo_signals, 'confirmation',
         dict(len=50, centered=False), 'strat 190-191'),
        ('dpo_exit', dpo_exit, 'exit', dict(len=50, centered=False), 'strat 190-191'),
        ('ease_of_movement_signals', ease_of_movement_signals, 'confirmation',
         dict(len=14, divisor=10000), 'strat 195-196'),
        ('ease_of_movement_exit', ease_of_movement_exit, 'exit',
         dict(len=14, divisor=10000), 'strat 195-196'),
        ('kalman_filter_signals', kalman_filter_signals, 'confirmation',
         dict(sharpness=1.0, k=1.0), 'strat 258-259'),
        ('kalman_filter_exit', kalman_filter_exit, 'exit',
         dict(sharpness=1.0, k=1.0), 'strat 258-259'),
        ('laguerre_filter_signals', laguerre_filter_signals, 'confirmation',
         dict(alpha=0.2), 'strat 266'),
        ('laguerre_filter_exit', laguerre_filter_exit, 'exit',
         dict(alpha=0.2), 'strat 266'),
        ('price_momentum_oscillator_signals', price_momentum_oscillator_signals,
         'confirmation', dict(s1=35, s2=20, sig=10), 'strat 274-276'),
        ('price_momentum_oscillator_exit', price_momentum_oscillator_exit, 'exit',
         dict(s1=35, s2=20, sig=10), 'strat 274-276'),
        ('relative_vigor_index_signals', relative_vigor_index_signals,
         'confirmation', dict(len=10), 'strat 280'),
        ('relative_vigor_index_exit', relative_vigor_index_exit, 'exit',
         dict(len=10), 'strat 280'),
        ('supertrend_signals', supertrend_signals, 'confirmation',
         dict(factor=3.0, atr_period=10), 'strat 283-284'),
        ('supertrend_exit', supertrend_exit, 'exit',
         dict(factor=3.0, atr_period=10), 'strat 283-284'),
        ('fisher_transform_signals', fisher_transform_signals, 'confirmation',
         dict(length=10), 'strat 200'),
        ('fisher_transform_exit', fisher_transform_exit, 'exit',
         dict(length=10), 'strat 200'),
        ('aroon_signals', aroon_signals, 'confirmation', dict(length=25),
         'strat 177'),
        ('aroon_exit', aroon_exit, 'exit', dict(length=25), 'strat 177'),
        ('center_of_gravity_signals', center_of_gravity_signals, 'confirmation',
         dict(length=10, signal_length=3), 'strat 179-180'),
        ('center_of_gravity_exit', center_of_gravity_exit, 'exit',
         dict(length=10, signal_length=3), 'strat 179-180')]:
    _reg(_n, _f, _slot, _d, _ln, True)

for _n in ('chaikin_money_flow_signals', 'chaikin_money_flow_exit',
           'ease_of_movement_signals', 'ease_of_movement_exit'):
    UNAVAILABLE.add(_n)
INVERTED.update({'supertrend_signals', 'supertrend_exit'})
LOOKAHEAD_OPTION.update({'dpo_signals', 'dpo_exit'})   # only if centered=True

KIND.update({k: v['kind'] for k, v in REGISTRY.items()})



# ==========================================================================
# CONFIRMATION BATCH B -- the patch-replaced ones, plus three more from the
# library. Every function here that the patch touches exists ONLY in its
# patched form.
# ==========================================================================


def vortex(o, h, l, c, vx_length=14):
    h = np.asarray(h, float); l = np.asarray(l, float)
    vmp = P.msum(np.abs(h - P.shift(l, 1)), vx_length)
    vmm = P.msum(np.abs(l - P.shift(h, 1)), vx_length)
    strr = P.msum(P.atr(h, l, c, 1), vx_length)
    with np.errstate(invalid='ignore', divide='ignore'):
        return np.where(strr != 0, vmp / strr, np.nan), \
               np.where(strr != 0, vmm / strr, np.nan)


def vortex_signals(o, h, l, c, period=14):
    vip, vim = vortex(o, h, l, c, period)
    pvip, pvim = P.shift(vip, 1), P.shift(vim, 1)
    return (P.F((vip > vim) & (pvip < pvim)), P.F((vip < vim) & (pvip > pvim)),
            P.F(vip > vim), P.F(vip < vim))


def vortex_exit(o, h, l, c, period=14):
    vip, vim = vortex(o, h, l, c, period)
    return P.crossunder(vip, vim), P.crossover(vip, vim)


def trend_direction_force_index(o, h, l, c, tdfi_lookback=13,
                                tdfi_filter_high=0.05, tdfi_filter_low=-0.05):
    """lib. The `for i = 1 to Tpow - 1` loop with Tpow=3 runs TWICE (i = 1 and
    i = 2). On i=1 Tresult is seeded to Tnumber and then multiplied by it, on
    i=2 it is multiplied again -- so the result is Tnumber CUBED.

    Reading it as a square gives an always-positive numerator, and the
    indicator then never confirms short at all: the sanity pass showed 51.2%
    long and 0.0% short before this was corrected. An odd power preserves the
    sign, which is the whole point of a direction indicator."""
    mma = P.ema(np.asarray(c, float) * 1000.0, tdfi_lookback)
    smma = P.ema(mma, tdfi_lookback)
    imp1 = mma - P.shift(mma, 1)
    imp2 = smma - P.shift(smma, 1)
    divma = np.abs(mma - smma)
    aver = (imp1 + imp2) / 2.0
    result = aver * aver * aver
    tdf = divma * result
    denom = P.highest(np.abs(tdf), tdfi_lookback * 3)
    with np.errstate(invalid='ignore', divide='ignore'):
        return np.where(denom != 0, tdf / denom, np.nan)


def trend_direction_force_index_signals(o, h, l, c, lookback=13, fhigh=0.05,
                                        flow=-0.05):
    """TERNARY: between the two filter levels it confirms neither side."""
    v = trend_direction_force_index(o, h, l, c, lookback, fhigh, flow)
    fh = np.full(v.shape, fhigh); fl = np.full(v.shape, flow)
    return (P.crossover(v, fh), P.crossunder(v, fl), P.F(v > fhigh), P.F(v < flow))


def trend_direction_force_index_exit(o, h, l, c, lookback=13, fhigh=0.05,
                                     flow=-0.05):
    v = trend_direction_force_index(o, h, l, c, lookback, fhigh, flow)
    return (P.crossunder(v, np.full(v.shape, fhigh)),
            P.crossover(v, np.full(v.shape, flow)))


def halftrend(o, h, l, c, amplitude=50):
    """lib, with its var-scoped state. Returns (ht, buy, sell) where ht is 0.0
    for the up state and -1.0 for the down state."""
    h = np.asarray(h, float); l = np.asarray(l, float); c = np.asarray(c, float)
    n = c.size
    hi_price = np.empty(n); lo_price = np.empty(n)
    hb = P.highestbars(h, amplitude); lb = P.lowestbars(l, amplitude)
    for i in range(n):
        oh = int(abs(hb[i])) if np.isfinite(hb[i]) else 0
        ol = int(abs(lb[i])) if np.isfinite(lb[i]) else 0
        hi_price[i] = h[max(0, i - oh)]
        lo_price[i] = l[max(0, i - ol)]
    highma = P.sma(h, amplitude); lowma = P.sma(l, amplitude)
    trend = 0.0; nxt = 0
    max_low = l[0]; min_high = h[0]
    ht = np.empty(n); buy = np.zeros(n); sell = np.zeros(n)
    prev_trend = 0.0
    for i in range(n):
        pl = l[i - 1] if i else l[i]
        ph = h[i - 1] if i else h[i]
        if nxt == 1:
            max_low = max(lo_price[i], max_low)
            if np.isfinite(highma[i]) and highma[i] < max_low and c[i] < pl:
                trend = 1.0; nxt = 0; min_high = hi_price[i]
        else:
            min_high = min(hi_price[i], min_high)
            if np.isfinite(lowma[i]) and lowma[i] > min_high and c[i] > ph:
                trend = 0.0; nxt = 1; max_low = lo_price[i]
        ht[i] = 0.0 if trend == 0 else -1.0
        if i:
            if trend == 0 and prev_trend == 1:
                buy[i] = 1.0
            elif trend == 1 and prev_trend == 0:
                sell[i] = 1.0
        prev_trend = trend
    return ht, buy, sell


def halftrend_signals(o, h, l, c, amplitude=50):
    ht, buy, sell = halftrend(o, h, l, c, amplitude)
    return P.F(buy == 1.0), P.F(sell == 1.0), P.F(ht == 0), P.F(ht != 0)


def halftrend_exit(o, h, l, c, amplitude=50):
    ht, buy, sell = halftrend(o, h, l, c, amplitude)
    return P.F(sell == 1.0), P.F(buy == 1.0)


def coral(o, h, l, c, smoothing_period=10, constant_d=14):
    """patch A9 -- latches the previous state on a flat bar instead of na."""
    c = np.asarray(c, float)
    d = float(constant_d)
    di = (smoothing_period - 1.0) / 2.0 + 1.0
    c1 = 2.0 / (di + 1.0); c2 = 1.0 - c1
    c3 = 3.0 * (d * d + d ** 3)
    c4 = -3.0 * (2.0 * d * d + d + d ** 3)
    c5 = 3.0 * d + 1.0 + d ** 3 + 3.0 * d * d
    i1 = i2 = i3 = i4 = i5 = i6 = 0.0
    n = c.size
    bfr = np.empty(n)
    for k in range(n):
        i1 = c1 * c[k] + c2 * i1
        i2 = c1 * i1 + c2 * i2
        i3 = c1 * i2 + c2 * i3
        i4 = c1 * i3 + c2 * i4
        i5 = c1 * i4 + c2 * i5
        i6 = c1 * i5 + c2 * i6
        bfr[k] = -(d ** 3) * i6 + c3 * i5 + c4 * i4 + c5 * i3
    out = np.empty(n); state = 0.0
    for k in range(n):
        prev = bfr[k - 1] if k else 0.0
        state = 1.0 if bfr[k] > prev else (0.0 if bfr[k] < prev else state)
        out[k] = state
    return out


def coral_signals(o, h, l, c, smooth_period=10, const_d=14):
    v = coral(o, h, l, c, smooth_period, const_d)
    pv = P.shift(v, 1)
    return (P.F((pv == 0) & (v == 1)), P.F((pv == 1) & (v == 0)),
            P.F(v == 1), P.F(v == 0))


def coral_exit(o, h, l, c, smooth_period=10, const_d=14):
    v = coral(o, h, l, c, smooth_period, const_d)
    pv = P.shift(v, 1)
    return P.F((pv == 1) & (v == 0)), P.F((pv == 0) & (v == 1))


def didi_index(o, h, l, c, didi_medium=8, didi_long=20):
    """patch A10 -- the two dead avg_ assignments removed. Ratio around 1.0."""
    media = P.sma(c, didi_medium)
    with np.errstate(invalid='ignore', divide='ignore'):
        return np.where(media != 0, P.sma(c, didi_long) / media, np.nan)


def didi_index_signals(o, h, l, c, medium=8, long_p=20):
    """The pivot is 1.0, not 0, and BELOW one is long."""
    v = didi_index(o, h, l, c, medium, long_p)
    pv = P.shift(v, 1)
    return (P.F((pv >= 1) & (v < 1)), P.F((pv <= 1) & (v > 1)),
            P.F(v < 1), P.F(v > 1))


def didi_index_exit(o, h, l, c, medium=8, long_p=20):
    v = didi_index(o, h, l, c, medium, long_p)
    pv = P.shift(v, 1)
    return P.F((pv <= 1) & (v > 1)), P.F((pv >= 1) & (v < 1))


def kase_peak_oscillator(o, h, l, c, kpo_short_cycle=8, kpo_long_cycle=65,
                         kpo_sensitivity=40.0):
    """patch A10 -- x1/xs no longer read from the prior bar, and the divide by
    a zero average is guarded."""
    h = np.asarray(h, float); l = np.asarray(l, float); c = np.asarray(c, float)
    cclog = np.log(c / P.nz(P.shift(c, 1), c))
    avg = P.sma(P.stdev(cclog, 9), 30)
    n = c.size
    max1 = np.zeros(n); maxs = np.zeros(n)
    for k in range(kpo_short_cycle, kpo_long_cycle):
        lo_k = P.nz(P.shift(l, k), l); hi_k = P.nz(P.shift(h, k), h)
        with np.errstate(invalid='ignore', divide='ignore'):
            max1 = np.maximum(np.log(h / lo_k) / np.sqrt(k), max1)
            maxs = np.maximum(np.log(hi_k / l) / np.sqrt(k), maxs)
    with np.errstate(invalid='ignore', divide='ignore'):
        x1 = np.where(avg != 0, max1 / avg, 0.0)
        xs = np.where(avg != 0, maxs / avg, 0.0)
    return kpo_sensitivity * (P.sma(x1, 3) - P.sma(xs, 3))


def kase_peak_oscillator_signals(o, h, l, c, short_cycle=8, long_cycle=65,
                                 sharpness=40.0):
    return _zero_cross(kase_peak_oscillator(o, h, l, c, short_cycle,
                                            long_cycle, sharpness))


def kase_peak_oscillator_exit(o, h, l, c, short_cycle=8, long_cycle=65,
                              sharpness=40.0):
    return _zero_cross_exit(kase_peak_oscillator(o, h, l, c, short_cycle,
                                                 long_cycle, sharpness))


def qqe_mod(o, h, l, c, qqe_rsi_period2=6, qqe_rsi_smoothing2=5,
            qqe_fast_factor2=1.61):
    """patch A8 -- the ~50 dead lines of the first QQE block removed. Output is
    identical to the original by construction; nothing fed from that block."""
    c = np.asarray(c, float)
    wilders = qqe_rsi_period2 * 2 - 1
    rsi_ = P.rsi(c, qqe_rsi_period2)
    rsima = P.ema(rsi_, qqe_rsi_smoothing2)
    atrrsi = np.abs(P.shift(rsima, 1) - rsima)
    dar = P.ema(P.ema(atrrsi, wilders), wilders) * qqe_fast_factor2
    n = c.size
    longb = np.zeros(n); shortb = np.zeros(n); trend = np.ones(n)
    lb = sb = 0.0; tr = 1
    for i in range(n):
        r = rsima[i]; pr = rsima[i - 1] if i else np.nan
        d = dar[i] if np.isfinite(dar[i]) else 0.0
        if not np.isfinite(r):
            longb[i] = lb; shortb[i] = sb; trend[i] = tr; continue
        newsb = r + d; newlb = r - d
        plb, psb = lb, sb
        lb = max(plb, newlb) if (np.isfinite(pr) and pr > plb and r > plb) else newlb
        sb = min(psb, newsb) if (np.isfinite(pr) and pr < psb and r < psb) else newsb
        prr = rsima[i - 1] if i else r
        cross_up = (prr <= psb) and (r > psb)
        cross_dn = (plb >= prr) != (plb >= r)
        tr = 1 if cross_up else (-1 if cross_dn else tr)
        longb[i] = lb; shortb[i] = sb; trend[i] = tr
    return np.where(trend == 1, longb, shortb) - 50.0


def qqe_mod_signals(o, h, l, c, rsi_period=6, rsi_len=5, fast_factor=1.61):
    return _zero_cross(qqe_mod(o, h, l, c, rsi_period, rsi_len, fast_factor))


def qqe_mod_exit(o, h, l, c, rsi_period=6, rsi_len=5, fast_factor=1.61):
    return _zero_cross_exit(qqe_mod(o, h, l, c, rsi_period, rsi_len, fast_factor))


def schaff_trend_cycle(o, h, l, c, stc_macd_fast_length=23,
                       stc_macd_slow_length=50, stc_cycle_length=10,
                       stc_1st_d_length=3, stc_2nd_d_length=3,
                       stc_upper_hline=75, stc_lower_hline=25):
    macd = P.ema(c, stc_macd_fast_length) - P.ema(c, stc_macd_slow_length)
    k = P.nz(P.fixnan(P.stoch(macd, macd, macd, stc_cycle_length)), 0.0)
    d = P.ema(k, stc_1st_d_length)
    kd = P.nz(P.fixnan(P.stoch(d, d, d, stc_cycle_length)), 0.0)
    stc = np.clip(P.ema(kd, stc_2nd_d_length), 0.0, 100.0)
    return (stc,
            P.crossover(stc, np.full(stc.shape, float(stc_lower_hline))),
            P.crossunder(stc, np.full(stc.shape, float(stc_upper_hline))))


def schaff_trend_cycle_signals(o, h, l, c, macdFast=23, macdSlow=50,
                               cycleLen=10, d1=3, d2=3, upperBand=75,
                               lowerBand=25, stc_midline=50.0):
    """patch A5. lc/sc split on the MIDLINE and are now mutually exclusive; the
    original had both true anywhere between the bands, so as a confirmation it
    agreed with whatever C1 said across the middle of its range. The triggers
    are still the band crosses. SIGNATURE GAINED stc_midline -- 50 keeps the
    natural default, as the patch says."""
    stc, bsig, ssig = schaff_trend_cycle(o, h, l, c, macdFast, macdSlow,
                                         cycleLen, d1, d2, upperBand, lowerBand)
    return bsig, ssig, P.F(stc > stc_midline), P.F(stc < stc_midline)


def schaff_trend_cycle_exit(o, h, l, c, macdFast=23, macdSlow=50, cycleLen=10,
                            d1=3, d2=3, upperBand=75, lowerBand=25,
                            stc_midline=50.0):
    stc, bsig, ssig = schaff_trend_cycle(o, h, l, c, macdFast, macdSlow,
                                         cycleLen, d1, d2, upperBand, lowerBand)
    return ssig, bsig


def glitch_index(o, h, l, c, length=30, multiplier=5.0, smooth=3):
    """patch A7. Was a z-score whose multiplier could not change a trade
    because every read was sign-based. Now a normalised displacement measured
    in units of average range, with the multiplier as a REAL threshold."""
    src = (np.asarray(h, float) + np.asarray(l, float)) / 2.0
    ma = P.sma(src, length)
    rng = P.sma(np.asarray(h, float) - np.asarray(l, float), length)
    with np.errstate(invalid='ignore', divide='ignore'):
        disp = np.where(rng != 0, (src - ma) / rng, 0.0)
    return P.ema(disp, smooth), float(multiplier)


def glitch_index_signals(o, h, l, c, length=30, multiplier=5.0, smooth=3):
    """TERNARY -- inside the band it confirms neither side, which is what a
    glitch detector should do."""
    g, lvl = glitch_index(o, h, l, c, length, multiplier, smooth)
    return (P.crossover(g, np.full(g.shape, lvl)),
            P.crossunder(g, np.full(g.shape, -lvl)),
            P.F(g > lvl), P.F(g < -lvl))


def glitch_index_exit(o, h, l, c, length=30, multiplier=5.0, smooth=3):
    g, lvl = glitch_index(o, h, l, c, length, multiplier, smooth)
    return (P.crossunder(g, np.full(g.shape, lvl)),
            P.crossover(g, np.full(g.shape, -lvl)))


def ehlers_reverse_ema(o, h, l, c, alpha=0.1):
    """patch A6. The real S&C April 2017 cascade of eight reverse-weighted
    stages, not the dual-EMA cross that wore its name. `length` is gone: it had
    no role in the actual indicator.

    Each stage is re_k[i] = pow_k * re_{k-1}[i] + re_{k-1}[i-1] -- it feeds off
    the PREVIOUS STAGE's prior bar, not its own, so the cascade is eight plain
    passes and not eight recursions."""
    c = np.asarray(c, float)
    n = c.size
    if n == 0:
        return np.zeros(0)
    ev = P.recur_nz(c, alpha, seed=c[0])
    om = 1.0 - alpha
    stage = ev
    for k in range(1, 9):
        pw = om ** (2 ** (k - 1))
        stage = pw * stage + P.nz(P.shift(stage, 1), 0.0)
    return ev - alpha * stage


def ehlers_reverse_ema_signals(o, h, l, c, alpha=0.1):
    w = ehlers_reverse_ema(o, h, l, c, alpha)
    z = np.zeros_like(w)
    return P.crossover(w, z), P.crossunder(w, z), P.F(w > 0), P.F(w < 0)


def ehlers_reverse_ema_exit(o, h, l, c, alpha=0.1):
    w = ehlers_reverse_ema(o, h, l, c, alpha)
    z = np.zeros_like(w)
    return P.crossunder(w, z), P.crossover(w, z)


# --- confirmation batch B. Defaults from strategy input() lines 176-340.
for _n, _f, _slot, _d, _ln in [
        ('vortex_signals', vortex_signals, 'confirmation', dict(period=14), 'strat 295'),
        ('vortex_exit', vortex_exit, 'exit', dict(period=14), 'strat 295'),
        ('trend_direction_force_index_signals', trend_direction_force_index_signals,
         'confirmation', dict(lookback=13, fhigh=0.05, flow=-0.05), 'strat 288-290'),
        ('trend_direction_force_index_exit', trend_direction_force_index_exit,
         'exit', dict(lookback=13, fhigh=0.05, flow=-0.05), 'strat 288-290'),
        ('halftrend_signals', halftrend_signals, 'confirmation',
         dict(amplitude=50), 'strat 254'),
        ('halftrend_exit', halftrend_exit, 'exit', dict(amplitude=50), 'strat 254'),
        ('coral_signals', coral_signals, 'confirmation',
         dict(smooth_period=10, const_d=14), 'strat 188-189 / patch A9'),
        ('coral_exit', coral_exit, 'exit',
         dict(smooth_period=10, const_d=14), 'strat 188-189 / patch A9'),
        ('didi_index_signals', didi_index_signals, 'confirmation',
         dict(medium=8, long_p=20), 'strat 192-193 / patch A10'),
        ('didi_index_exit', didi_index_exit, 'exit',
         dict(medium=8, long_p=20), 'strat 192-193 / patch A10'),
        ('kase_peak_oscillator_signals', kase_peak_oscillator_signals,
         'confirmation', dict(short_cycle=8, long_cycle=65, sharpness=40.0),
         'strat 260-262 / patch A10'),
        ('kase_peak_oscillator_exit', kase_peak_oscillator_exit, 'exit',
         dict(short_cycle=8, long_cycle=65, sharpness=40.0),
         'strat 260-262 / patch A10'),
        ('qqe_mod_signals', qqe_mod_signals, 'confirmation',
         dict(rsi_period=6, rsi_len=5, fast_factor=1.61),
         'strat 277-279 / patch A8'),
        ('qqe_mod_exit', qqe_mod_exit, 'exit',
         dict(rsi_period=6, rsi_len=5, fast_factor=1.61),
         'strat 277-279 / patch A8'),
        ('schaff_trend_cycle_signals', schaff_trend_cycle_signals, 'confirmation',
         dict(macdFast=23, macdSlow=50, cycleLen=10, d1=3, d2=3, upperBand=75,
              lowerBand=25, stc_midline=50.0), 'patch A5'),
        ('schaff_trend_cycle_exit', schaff_trend_cycle_exit, 'exit',
         dict(macdFast=23, macdSlow=50, cycleLen=10, d1=3, d2=3, upperBand=75,
              lowerBand=25, stc_midline=50.0), 'patch A5'),
        ('glitch_index_signals', glitch_index_signals, 'confirmation',
         dict(length=30, multiplier=5.0, smooth=3), 'strat 249-251 / patch A7'),
        ('glitch_index_exit', glitch_index_exit, 'exit',
         dict(length=30, multiplier=5.0, smooth=3), 'strat 249-251 / patch A7'),
        ('ehlers_reverse_ema_signals', ehlers_reverse_ema_signals, 'confirmation',
         dict(alpha=0.1), 'strat 198 / patch A6'),
        ('ehlers_reverse_ema_exit', ehlers_reverse_ema_exit, 'exit',
         dict(alpha=0.1), 'strat 198 / patch A6')]:
    _reg(_n, _f, _slot, _d, _ln, True)

TERNARY.update({'trend_direction_force_index', 'glitch_index'})
KIND.update({k: ('TERNARY' if k.replace('_signals', '') in TERNARY and
                 v['slot'] == 'confirmation' else v['kind'])
             for k, v in REGISTRY.items()})
for _k in REGISTRY:
    REGISTRY[_k]['kind'] = KIND[_k]



# ==========================================================================
# CONFIRMATION BATCH C
# ==========================================================================


def chandelier_exit(o, h, l, c, atr_length=22, atr_multiplier=3.0,
                    close_for_Extremums=True):
    """lib, with its CW10003 fix: both highest/lowest variants are computed
    every bar so the ratcheting state stays consistent whichever the toggle."""
    c = np.asarray(c, float)
    ca = atr_multiplier * P.atr(h, l, c, atr_length)
    hi = P.highest(c, atr_length) if close_for_Extremums else P.highest(h, atr_length)
    lo = P.lowest(c, atr_length) if close_for_Extremums else P.lowest(l, atr_length)
    n = c.size
    ls = np.full(n, np.nan); ss = np.full(n, np.nan); dr = np.ones(n)
    pls = pss = np.nan; d = 1
    for i in range(n):
        raw_l = hi[i] - ca[i]; raw_s = lo[i] + ca[i]
        pl = pls if np.isfinite(pls) else raw_l
        ps = pss if np.isfinite(pss) else raw_s
        cur_l = max(raw_l, pl) if (i and c[i - 1] > pl) else raw_l
        cur_s = min(raw_s, ps) if (i and c[i - 1] < ps) else raw_s
        d = 1 if c[i] > ps else (-1 if c[i] < pl else d)
        ls[i] = cur_l; ss[i] = cur_s; dr[i] = d
        pls, pss = cur_l, cur_s
    return ls, ss, dr


def chandelier_exit_signals(o, h, l, c, atr_period=22, atr_mult=3.0,
                            use_close=True):
    ls, ss, d = chandelier_exit(o, h, l, c, atr_period, atr_mult, use_close)
    c = np.asarray(c, float)
    pd_ = np.concatenate([[1.0], d[:-1]])
    return (P.F((d == 1.0) & (pd_ != 1.0)), P.F((d == -1.0) & (pd_ != -1.0)),
            P.F(c > ls), P.F(c < ss))


def chandelier_exit_exit(o, h, l, c, atr_period=22, atr_mult=3.0,
                         use_close=True):
    ls, ss, d = chandelier_exit(o, h, l, c, atr_period, atr_mult, use_close)
    pd_ = np.concatenate([[1.0], d[:-1]])
    return P.F((d == -1.0) & (pd_ != -1.0)), P.F((d == 1.0) & (pd_ != 1.0))


def polychromatic_momentum(o, h, l, c, ply_length=14):
    c = np.asarray(c, float)
    mom = c - P.shift(c, ply_length)
    pdm = P.msum(np.maximum(mom, 0.0), ply_length)
    ndm = P.msum(np.maximum(-mom, 0.0), ply_length)
    tot = pdm + ndm
    with np.errstate(invalid='ignore', divide='ignore'):
        return np.where(tot != 0, 100.0 * (pdm - ndm) / tot, np.nan)


def polychromatic_momentum_signals(o, h, l, c, len=14):
    return _zero_cross(polychromatic_momentum(o, h, l, c, len))


def polychromatic_momentum_exit(o, h, l, c, len=14):
    return _zero_cross_exit(polychromatic_momentum(o, h, l, c, len))


def mama_fama(o, h, l, c, fast_limit=0.5, slow_limit=0.05):
    """Ehlers' MESA Adaptive MA. Everything is held until bar 6, exactly as the
    `if bar_index > 5` guard in the source does."""
    src = (np.asarray(h, float) + np.asarray(l, float)) / 2.0
    n = src.size
    sm = np.zeros(n); det = np.zeros(n); q1 = np.zeros(n); i1 = np.zeros(n)
    ji = np.zeros(n); jq = np.zeros(n); i2 = np.zeros(n); q2 = np.zeros(n)
    re = np.zeros(n); im = np.zeros(n); per = np.zeros(n); sper = np.zeros(n)
    ph = np.zeros(n); mama = np.zeros(n); fama = np.zeros(n)

    def g(a, i, k):
        return a[i - k] if i - k >= 0 else 0.0

    for i in range(n):
        if i <= 5:
            continue
        sm[i] = (4 * src[i] + 3 * g(src, i, 1) + 2 * g(src, i, 2) + g(src, i, 3)) / 10.0
        pf = 0.075 * per[i - 1] + 0.54
        det[i] = (.0962 * sm[i] + .5769 * g(sm, i, 2) - .5769 * g(sm, i, 4)
                  - .0962 * g(sm, i, 6)) * pf
        q1[i] = (.0962 * det[i] + .5769 * g(det, i, 2) - .5769 * g(det, i, 4)
                 - .0962 * g(det, i, 6)) * pf
        i1[i] = g(det, i, 3)
        ji[i] = (.0962 * i1[i] + .5769 * g(i1, i, 2) - .5769 * g(i1, i, 4)
                 - .0962 * g(i1, i, 6)) * pf
        jq[i] = (.0962 * q1[i] + .5769 * g(q1, i, 2) - .5769 * g(q1, i, 4)
                 - .0962 * g(q1, i, 6)) * pf
        a2 = i1[i] - jq[i]; b2 = q1[i] + ji[i]
        i2[i] = .2 * a2 + .8 * i2[i - 1]
        q2[i] = .2 * b2 + .8 * q2[i - 1]
        r = i2[i] * i2[i - 1] + q2[i] * q2[i - 1]
        m = i2[i] * q2[i - 1] - q2[i] * i2[i - 1]
        re[i] = .2 * r + .8 * re[i - 1]
        im[i] = .2 * m + .8 * im[i - 1]
        p = per[i - 1]
        if im[i] != 0 and re[i] != 0:
            p = 2 * np.pi / np.arctan(im[i] / re[i])
        if p > 1.5 * per[i - 1]:
            p = 1.5 * per[i - 1]
        if p < 0.67 * per[i - 1]:
            p = 0.67 * per[i - 1]
        p = max(6.0, min(50.0, p))
        per[i] = .2 * p + .8 * per[i - 1]
        sper[i] = .33 * per[i] + .67 * sper[i - 1]
        ph[i] = np.arctan(q1[i] / i1[i]) * 180 / np.pi if i1[i] != 0 else 0.0
        dp = max(1.0, ph[i - 1] - ph[i])
        al = min(max(fast_limit / dp, slow_limit), fast_limit)
        mama[i] = al * src[i] + (1 - al) * mama[i - 1]
        fama[i] = .5 * al * mama[i] + (1 - .5 * al) * fama[i - 1]
    return mama, fama


def mama_fama_signals(o, h, l, c, fast_limit=0.5, slow_limit=0.05):
    m, f = mama_fama(o, h, l, c, fast_limit, slow_limit)
    return P.crossover(m, f), P.crossunder(m, f), P.F(m > f), P.F(m < f)


def mama_fama_exit(o, h, l, c, fast_limit=0.5, slow_limit=0.05):
    m, f = mama_fama(o, h, l, c, fast_limit, slow_limit)
    return P.crossunder(m, f), P.crossover(m, f)


def kuskus_starlight(o, h, l, c, range_periods=30, price_smooth=0.7,
                     index_smooth=0.7):
    c = np.asarray(c, float)
    hi, lo = P.highest(h, range_periods), P.lowest(l, range_periods)
    rng = hi - lo
    with np.errstate(invalid='ignore', divide='ignore'):
        raw = np.where(rng == 0, 0.0, (c - lo) / rng - 0.5)
    n = c.size
    out = np.empty(n); sm = np.nan; st = np.nan
    for i in range(n):
        r = raw[i] if np.isfinite(raw[i]) else 0.0
        sm = r if not np.isfinite(sm) else price_smooth * r + (1 - price_smooth) * sm
        cl = min(max(sm, -0.499), 0.499)
        fr = 0.5 * np.log((1 + 2 * cl) / (1 - 2 * cl))
        st = fr if not np.isfinite(st) else index_smooth * fr + (1 - index_smooth) * st
        out[i] = st
    return out


def kuskus_starlight_signals(o, h, l, c, range_periods=30, price_smooth=0.7,
                             index_smooth=0.7):
    return _zero_cross(kuskus_starlight(o, h, l, c, range_periods,
                                        price_smooth, index_smooth))


def kuskus_starlight_exit(o, h, l, c, range_periods=30, price_smooth=0.7,
                          index_smooth=0.7):
    return _zero_cross_exit(kuskus_starlight(o, h, l, c, range_periods,
                                             price_smooth, index_smooth))


def bears_bulls_impulse(o, h, l, c, length=13):
    e = P.ema(c, length)
    return np.asarray(h, float) - e, np.asarray(l, float) - e


def bears_bulls_impulse_signals(o, h, l, c, length=13):
    """TERNARY, and asymmetric on purpose: long when the LOW clears the EMA,
    short when the HIGH fails to. Between those it confirms neither."""
    bulls, bears = bears_bulls_impulse(o, h, l, c, length)
    pbe, pbu = P.shift(bears, 1), P.shift(bulls, 1)
    return (P.F((pbe < 0) & (bears > 0)), P.F((pbu > 0) & (bulls < 0)),
            P.F(bears > 0), P.F(bulls < 0))


def bears_bulls_impulse_exit(o, h, l, c, length=13):
    bulls, bears = bears_bulls_impulse(o, h, l, c, length)
    pbe, pbu = P.shift(bears, 1), P.shift(bulls, 1)
    return P.F((pbu > 0) & (bulls < 0)), P.F((pbe < 0) & (bears > 0))


def fx_sniper_ergodic_cci(o, h, l, c, cci_length=14, ema1_length=5,
                          ema2_length=3, trigger_length=5):
    e2 = P.ema(P.ema(P.cci(c, cci_length), ema1_length), ema2_length)
    return e2, P.sma(e2, trigger_length)


def fx_sniper_ergodic_cci_signals(o, h, l, c, cci_length=14, ema1_length=5,
                                  ema2_length=3, trigger_length=5):
    m, t = fx_sniper_ergodic_cci(o, h, l, c, cci_length, ema1_length,
                                 ema2_length, trigger_length)
    return P.crossover(m, t), P.crossunder(m, t), P.F(m > t), P.F(m < t)


def fx_sniper_ergodic_cci_exit(o, h, l, c, cci_length=14, ema1_length=5,
                               ema2_length=3, trigger_length=5):
    m, t = fx_sniper_ergodic_cci(o, h, l, c, cci_length, ema1_length,
                                 ema2_length, trigger_length)
    return P.crossunder(m, t), P.crossover(m, t)


def lemantrend(o, h, l, c, slow_period=13, medium_period=21, fast_period=34,
               smooth=3):
    """NOTE THE PARAMETER ORDER. The strategy passes 13, 21, 34 into
    (slow, medium, fast), so the 'slow' EMA is the SHORTEST and the 'fast' one
    the longest -- the names are back to front relative to the values. Ported
    positionally, which is what the strategy actually calls."""
    slow = P.ema(c, slow_period)
    med = P.ema(c, medium_period)
    fast = P.ema(c, fast_period)
    return (P.ema((fast - med) + (med - slow), smooth),
            P.ema((slow - med) + (med - fast), smooth))


def lemantrend_signals(o, h, l, c, slow_period=13, medium_period=21,
                       fast_period=34, smooth=3):
    bulls, bears = lemantrend(o, h, l, c, slow_period, medium_period,
                              fast_period, smooth)
    return (P.crossover(bulls, bears), P.crossunder(bulls, bears),
            P.F(bulls > bears), P.F(bulls < bears))


def lemantrend_exit(o, h, l, c, slow_period=13, medium_period=21,
                    fast_period=34, smooth=3):
    bulls, bears = lemantrend(o, h, l, c, slow_period, medium_period,
                              fast_period, smooth)
    return P.crossunder(bulls, bears), P.crossover(bulls, bears)


def waddah_attar_explosion_signals(o, h, l, c, sensitivity=150, fastEma=20,
                                   slowEma=40, bbLen=20, bbStd=2.0):
    """NOTE: st is a CROSSOVER of wDown, not a crossunder -- both triggers fire
    on something rising through the explosion line. As written."""
    e1, up, dn = waddah_attar_explosion(o, h, l, c, sensitivity, fastEma,
                                        slowEma, bbLen, bbStd)
    return (P.crossover(up, e1), P.crossover(dn, e1),
            P.F(up > e1), P.F(dn > e1))


def waddah_attar_explosion_exit(o, h, l, c, sensitivity=150, fastEma=20,
                                slowEma=40, bbLen=20, bbStd=2.0):
    e1, up, dn = waddah_attar_explosion(o, h, l, c, sensitivity, fastEma,
                                        slowEma, bbLen, bbStd)
    return P.crossover(dn, e1), P.crossover(up, e1)


# --- confirmation batch C. Defaults from strategy input() lines 176-340.
for _n, _f, _slot, _d, _ln in [
        ('chandelier_exit_signals', chandelier_exit_signals, 'confirmation',
         dict(atr_period=22, atr_mult=3.0, use_close=True), 'strat 182-184'),
        ('chandelier_exit_exit', chandelier_exit_exit, 'exit',
         dict(atr_period=22, atr_mult=3.0, use_close=True), 'strat 182-184'),
        ('polychromatic_momentum_signals', polychromatic_momentum_signals,
         'confirmation', dict(len=14), 'strat 273'),
        ('polychromatic_momentum_exit', polychromatic_momentum_exit, 'exit',
         dict(len=14), 'strat 273'),
        ('mama_fama_signals', mama_fama_signals, 'confirmation',
         dict(fast_limit=0.5, slow_limit=0.05), 'strat 271-272'),
        ('mama_fama_exit', mama_fama_exit, 'exit',
         dict(fast_limit=0.5, slow_limit=0.05), 'strat 271-272'),
        ('kuskus_starlight_signals', kuskus_starlight_signals, 'confirmation',
         dict(range_periods=30, price_smooth=0.7, index_smooth=0.7),
         'strat 263-265'),
        ('kuskus_starlight_exit', kuskus_starlight_exit, 'exit',
         dict(range_periods=30, price_smooth=0.7, index_smooth=0.7),
         'strat 263-265'),
        ('bears_bulls_impulse_signals', bears_bulls_impulse_signals,
         'confirmation', dict(length=13), 'strat 178'),
        ('bears_bulls_impulse_exit', bears_bulls_impulse_exit, 'exit',
         dict(length=13), 'strat 178'),
        ('fx_sniper_ergodic_cci_signals', fx_sniper_ergodic_cci_signals,
         'confirmation', dict(cci_length=14, ema1_length=5, ema2_length=3,
                              trigger_length=5), 'strat 202-205'),
        ('fx_sniper_ergodic_cci_exit', fx_sniper_ergodic_cci_exit, 'exit',
         dict(cci_length=14, ema1_length=5, ema2_length=3, trigger_length=5),
         'strat 202-205'),
        ('lemantrend_signals', lemantrend_signals, 'confirmation',
         dict(slow_period=13, medium_period=21, fast_period=34, smooth=3),
         'strat 267-270'),
        ('lemantrend_exit', lemantrend_exit, 'exit',
         dict(slow_period=13, medium_period=21, fast_period=34, smooth=3),
         'strat 267-270'),
        ('waddah_attar_explosion_signals', waddah_attar_explosion_signals,
         'confirmation', dict(sensitivity=150, fastEma=20, slowEma=40, bbLen=20,
                              bbStd=2.0), 'strat 296-300'),
        ('waddah_attar_explosion_exit', waddah_attar_explosion_exit, 'exit',
         dict(sensitivity=150, fastEma=20, slowEma=40, bbLen=20, bbStd=2.0),
         'strat 296-300')]:
    _reg(_n, _f, _slot, _d, _ln, True)

TERNARY.update({'bears_bulls_impulse'})
for _k in REGISTRY:
    if REGISTRY[_k]['slot'] == 'confirmation':
        REGISTRY[_k]['kind'] = ('TERNARY'
                                if _k.replace('_signals', '') in TERNARY
                                else 'BINARY')
KIND.update({k: v['kind'] for k, v in REGISTRY.items()})


def both_directions_audit(o, h, l, c):
    """THE A5 CHECK, RUN OVER EVERY CONFIRMATION.

    The patch fixed Schaff Trend Cycle because lc and sc were both true across
    the middle of its range -- as a C2 that votes for whatever C1 says and
    filters nothing. Nothing checks the rest of the library for the same fault,
    so this does: any confirmation that confirms BOTH directions on any bar is
    reported with the share of bars it does it on.
    """
    import pandas as pd
    rows = []
    for k, v in REGISTRY.items():
        if v['slot'] != 'confirmation':
            continue
        lt, st, lc, sc = compute(k, o, h, l, c)
        both = lc & sc
        rows.append(dict(name=k, both_pct=round(100 * both.mean(), 2),
                         long_pct=round(100 * lc.mean(), 1),
                         short_pct=round(100 * sc.mean(), 1),
                         neutral_pct=round(100 * (~lc & ~sc).mean(), 1)))
    return pd.DataFrame(rows).sort_values('both_pct', ascending=False)



# ==========================================================================
# CONFIRMATION BATCH D -- Volatility Quality and J_TPO
# ==========================================================================


def volatility_quality(o, h, l, c, vq_ma_type='WMA', vq_source_smoothing=10,
                       vq_atr_percentage=7.5):
    """lib. Two things worth stating.

    The vqi recursion is written twice on consecutive lines: the first assigns
    a ratio, the SECOND immediately overwrites it with |vqi| times a price
    difference. So the first line's value is used only through its absolute
    value, and the ratio's sign is discarded. That is what the source does.

    inpFilter is a DEAD BAND, not a threshold: a new value is accepted only if
    it moves more than inpFilter x ATR from the last accepted one, otherwise
    the old value is held. At the default 7.5 that is a very wide band."""
    o = np.asarray(o, float); h = np.asarray(h, float)
    l = np.asarray(l, float); c = np.asarray(c, float)
    pcl_src = P.nz(P.shift(c, 1), 0.0)
    f = {'SMA': P.sma, 'EMA': P.ema, 'WMA': P.wma, 'RMA': P.rma}.get(vq_ma_type)
    if f is None:
        z = np.zeros(c.shape)
        chigh = clow = cclose = copen = pclose = z
    else:
        n = vq_source_smoothing
        chigh, clow = f(h, n), f(l, n)
        cclose, copen, pclose = f(c, n), f(o, n), f(pcl_src, n)
    tr_ = np.where(chigh > pclose, chigh, pclose) - np.where(clow < pclose, clow, pclose)
    rng = chigh - clow
    n = c.size
    val_raw = np.zeros(n); vqi = 0.0
    for i in range(n):
        ok = np.isfinite(rng[i]) and np.isfinite(tr_[i]) and rng[i] > 0 and tr_[i] > 0
        if ok:
            vqi = ((cclose[i] - pclose[i]) / tr_[i]
                   + (cclose[i] - copen[i]) / rng[i]) * 0.5
        elif i == 0:
            vqi = 0.0
        # else: hold the previous vqi
        if i > 0:
            vqi = (vqi if vqi > 0 else -vqi) * (cclose[i] - pclose[i]
                                                + cclose[i] - copen[i]) * 0.5
        else:
            vqi = 0.0
        val_raw[i] = vqi
    vqatr = P.atr(h, l, c, vq_source_smoothing)
    val = np.zeros(n); prev = 0.0
    for i in range(n):
        vr = val_raw[i]
        delta = abs(vr - prev)
        a = vqatr[i] if np.isfinite(vqatr[i]) else 0.0
        prev = prev if (vq_atr_percentage > 0 and i > 0 and delta < vq_atr_percentage * a) else vr
        val[i] = prev
    mid = np.zeros(n)
    return val, mid, P.crossover(val, mid), P.crossunder(val, mid)


def volatility_quality_signals(o, h, l, c, ma_type='WMA', smooth=10,
                               atr_pct=7.5):
    val, mid, lo_, sh = volatility_quality(o, h, l, c, ma_type, smooth, atr_pct)
    return lo_, sh, P.F(val > 0), P.F(val < 0)


def volatility_quality_exit(o, h, l, c, ma_type='WMA', smooth=10, atr_pct=7.5):
    val, mid, lo_, sh = volatility_quality(o, h, l, c, ma_type, smooth, atr_pct)
    return sh, lo_


try:
    from numba import njit as _njit
except ImportError:                                     # pragma: no cover
    def _njit(*a, **k):
        return (lambda f: f) if not a else a[0]


@_njit(cache=True)
def _jtpo_values(c, length):
    """patch A4's getValue, per bar.

    The original accumulated with `array.get(arr3, m)` and `array.get(arr2, m)`
    where m is FIXED after the preceding while loop, so it added the same
    product `length` times instead of summing across the series. Every J_TPO
    value in the project was wrong. This indexes with i, as the patch does.

    O(length^2) per bar, so it is njit-compiled -- at the default length 40
    over 5,869 bars that is ~9.4M inner iterations per pair."""
    n = c.size
    out = np.zeros(n)
    L = length
    half = (L + 1) * 0.5
    a1 = np.zeros(L + 2); a2 = np.zeros(L + 2); a3 = np.zeros(L + 2)
    for t in range(n):
        if t < L:
            continue
        for i in range(1, L + 1):
            a2[i] = i
            a3[i] = i
            a1[i] = c[t - (L - i)]
        for i in range(1, L):
            maxval = a1[i]; maxloc = i
            for j in range(i + 1, L + 1):
                if a1[j] < maxval:
                    maxval = a1[j]; maxloc = j
            t1 = a1[i]; a1[i] = a1[maxloc]; a1[maxloc] = t1
            t2 = a2[i]; a2[i] = a2[maxloc]; a2[maxloc] = t2
        m = 1
        while m < L - 1:
            j = m + 1
            flag = True
            accum = a3[m]
            while flag:
                if a1[m] != a1[j]:
                    if j - m > 1:
                        accum = accum / (j - m)
                        for q in range(m, j):
                            a3[q] = accum
                    flag = False
                else:
                    accum = accum + a3[j]
                    j = j + 1
                    if j >= L + 1:
                        flag = False
            m = j
        tot = 0.0
        for i in range(1, L + 1):
            tot += (a3[i] - half) * (a2[i] - half)
        out[t] = tot
    return out


def j_tpo_indicator(o, h, l, c, jtpo_len=40, jtpo_ema_length=200,
                    jtpo_emaf=False):
    c = np.asarray(c, float)
    L = int(jtpo_len)
    norm = 12.0 / (L * (L - 1) * (L + 1))
    rng = P.highest(c, L) - P.lowest(c, L)
    j = (norm * _jtpo_values(c, L)) * rng / L
    jema = P.ema(j, jtpo_ema_length)
    z = np.zeros_like(j)
    up = P.crossover(j, z); dn = P.crossunder(j, z)
    if jtpo_emaf:
        ls = up & P.F(jema > 0); ss = dn & P.F(jema < 0)
    else:
        ls, ss = up, dn
    return j, ls, ss


def j_tpo_signals(o, h, l, c, len=40, ema_len=200, ema_filter=False):
    j, ls, ss = j_tpo_indicator(o, h, l, c, len, ema_len, ema_filter)
    return ls, ss, P.F(j > 0), P.F(j < 0)


def j_tpo_exit(o, h, l, c, len=40, ema_len=200, ema_filter=False):
    j, ls, ss = j_tpo_indicator(o, h, l, c, len, ema_len, ema_filter)
    return ss, ls


# --- confirmation batch D.
for _n, _f, _slot, _d, _ln in [
        ('volatility_quality_signals', volatility_quality_signals, 'confirmation',
         dict(ma_type='WMA', smooth=10, atr_pct=7.5), 'strat 376-378'),
        ('volatility_quality_exit', volatility_quality_exit, 'exit',
         dict(ma_type='WMA', smooth=10, atr_pct=7.5), 'strat 376-378'),
        ('j_tpo_signals', j_tpo_signals, 'confirmation',
         dict(len=40, ema_len=200, ema_filter=False), 'strat 256-258 / patch A4'),
        ('j_tpo_exit', j_tpo_exit, 'exit',
         dict(len=40, ema_len=200, ema_filter=False), 'strat 256-258 / patch A4')]:
    _reg(_n, _f, _slot, _d, _ln, True)
KIND.update({k: v['kind'] for k, v in REGISTRY.items()})



# ==========================================================================
# CONFIRMATION BATCH E -- Heiken Ashi Smoothed and Rex Oscillator.
#
# These two are 1,062 of the library's 3,019 lines between them, because Pine
# computes ALL FOURTEEN moving-average types on ALL FOUR price series and then
# throws away thirteen of them with a chain of ternaries. `_ha_ma` below is
# that chain as a dispatcher: it computes only the arm that is selected. The
# OUTPUT is identical -- Pine's discarded arms cannot affect the chosen one,
# none of them carry state across the switch -- but this is 40 lines instead
# of 700, and where it differs from the Pine it differs by being narrower,
# never by being different.
#
# Four of the arms are not what their names say, and are ported as written:
#   TEMA  is ema(ema(ema(x))) -- triple-SMOOTHED, not 3*e1 - 3*e2 + e3.
#   TRIMA is sma(sma(x, L), L), not the ceil/floor construction that
#         triangular_moving_average (the baseline) uses under the same name.
#   AMA   seeds with `src*w*w + 1 - w*w`, which the missing parentheses make
#         `(src*w*w + 1) - w*w`, not the smoothing it looks like.
#   FAMA  takes its fractal dimension from HIGH and LOW whichever series is
#         being smoothed, so the dimension is shared and only the final
#         recursion differs per series.
# ==========================================================================


def _ha_ma(kind, src, hi, lo, length, vfac=0.82, alma_offset=0.85,
           alma_sigma=6, lsma_offset=0, ama_weight=0.181, frama_a=1,
           frama_b=168):
    """One arm of the fourteen-way switch. src is the series being smoothed;
    hi/lo are only used by FAMA, which reads them whatever src is."""
    src = np.asarray(src, float)
    n = int(length)
    if kind == 'SMA':
        return P.sma(src, n)
    if kind == 'EMA':
        return P.ema(src, n)
    if kind == 'WMA':
        return P.wma(src, n)
    if kind == 'ALMA':
        return P.alma(src, n, alma_offset, alma_sigma)
    if kind == 'LSMA':
        return P.linreg(src, n, lsma_offset)
    if kind == 'TRIMA':
        return P.sma(P.sma(src, n), n)
    if kind == 'HMA':
        return P.wma(2.0 * P.wma(src, P.idiv(n, 2)) - P.wma(src, n),
                     int(round(np.sqrt(n))))
    if kind == 'TEMA':
        return P.ema(P.ema(P.ema(src, n), n), n)
    if kind == 'DEMA':
        e1 = P.ema(src, n)
        return 2.0 * e1 - P.ema(e1, n)
    if kind == 'T3':
        b = vfac
        c1 = -b ** 3
        c2 = 3 * b * b + 3 * b ** 3
        c3 = -6 * b * b - 3 * b - 3 * b ** 3
        c4 = 1 + 3 * b + b ** 3 + 3 * b * b
        e = src; es = []
        for _ in range(6):
            e = P.ema(e, n); es.append(e)
        return c1 * es[5] + c2 * es[4] + c3 * es[3] + c4 * es[2]
    if kind == 'SMMA':
        seed = P.sma(src, n)
        out = np.full(src.shape, np.nan); prev = np.nan
        for i in range(src.size):
            prev = seed[i] if not np.isfinite(prev) else (prev * (n - 1) + src[i]) / n
            out[i] = prev
        return out
    if kind == 'VIDYA':
        d = P.change(src)
        up = P.msum(np.where(d >= 0, d, 0.0), n)
        dn = P.msum(np.where(d >= 0, 0.0, -d), n)
        with np.errstate(invalid='ignore', divide='ignore'):
            cmo = np.where((up + dn) != 0, (up - dn) / (up + dn), 0.0)
        f = 2.0 / (n + 1)
        k = f * np.abs(cmo)
        out = np.empty(src.shape); prev = 0.0
        for i in range(src.size):
            kk = k[i] if np.isfinite(k[i]) else 0.0
            x = src[i] if np.isfinite(src[i]) else 0.0
            prev = x * kk + prev * (1 - kk)
            out[i] = prev
        return out
    if kind == 'AMA':
        w = ama_weight
        ww = w * w
        out = np.empty(src.shape); prev = np.nan
        for i in range(src.size):
            if not np.isfinite(prev):
                prev = src[i] * ww + 1 - ww           # the source's precedence
            else:
                prev = src[i] * ww + (1 - ww) * prev
            out[i] = prev
        return out
    if kind == 'FAMA':
        half = int(P.idiv(n, 2))
        e = np.e
        lnw = np.log(2.0 / (frama_b + 1)) / np.log(e)
        n1 = (P.highest(hi, half) - P.lowest(lo, half)) / half
        n2 = (P.shift(P.highest(hi, half), half)
              - P.shift(P.lowest(lo, half), half)) / half
        n3 = (P.highest(hi, n) - P.lowest(lo, n)) / n
        with np.errstate(invalid='ignore', divide='ignore'):
            d1 = (np.log(n1 + n2) - np.log(n3)) / np.log(2.0)
        d2 = np.where((n1 > 0) & (n2 > 0) & (n3 > 0), d1,
                      P.nz(P.shift(d1, 1), 0.0))
        a_old = np.clip(np.exp(lnw * (d2 - 1.0)), 0.01, 1.0)
        np_old = (2 - a_old) / a_old
        np_ = (frama_b - frama_a) * (np_old - 1) / (frama_b - 1) + frama_a
        a2 = 2.0 / (np_ + 1)
        floor_ = 2.0 / (frama_b + 1)
        alpha = np.where(a2 < floor_, floor_, np.where(a2 > 1, 1.0, a2))
        out = np.empty(src.shape); prev = 0.0
        for i in range(src.size):
            a = alpha[i] if np.isfinite(alpha[i]) else 1.0
            x = src[i] if np.isfinite(src[i]) else prev
            prev = (1 - a) * prev + a * x
            out[i] = prev
        return out
    return src                                        # 'DEFAULT'


def hieken_ashi_smoothed(o, h, l, c, ha_ma1='T3', ha_ma1_length=8, ha_ma2='T3',
                         ha_ma2_length=8, ha_signal_smoothed=False,
                         ha_vfac_type_1=0.82, ha_offset_ALMA=0.85,
                         ha_sigma_ALMA=6, ha_LSMAO=0, ha_AMA_weight_v1=0.181,
                         ha_FAMA_i2=1, ha_FAMA_i3=168, ha_vfac_type_2=0.82,
                         ha_offset_ALMA2=0.85, ha_sigma_ALMA2=6, ha_LSMAO2=0,
                         ha_AMA_weight_v2=0.181, ha_FAMA_i4=1, ha_FAMA_i5=168):
    o = np.asarray(o, float); h = np.asarray(h, float)
    l = np.asarray(l, float); c = np.asarray(c, float)
    k1 = dict(length=ha_ma1_length, vfac=ha_vfac_type_1,
              alma_offset=ha_offset_ALMA, alma_sigma=ha_sigma_ALMA,
              lsma_offset=ha_LSMAO, ama_weight=ha_AMA_weight_v1,
              frama_a=ha_FAMA_i2, frama_b=ha_FAMA_i3)
    o1 = _ha_ma(ha_ma1, o, h, l, **k1)
    h1 = _ha_ma(ha_ma1, h, h, l, **k1)
    l1 = _ha_ma(ha_ma1, l, h, l, **k1)
    c1_ = _ha_ma(ha_ma1, c, h, l, **k1)
    # the Heiken Ashi transform
    c2 = (o1 + h1 + l1 + c1_) / 4.0
    o2 = (P.shift(o1, 1) + P.shift(c1_, 1)) / 2.0
    h2 = np.maximum(h1, np.maximum(o1, c1_))
    l2 = np.minimum(l1, np.minimum(o1, c1_))
    if ha_signal_smoothed:
        O, H, L, C = o2, h2, l2, c2
    else:
        k2 = dict(length=ha_ma2_length, vfac=ha_vfac_type_2,
                  alma_offset=ha_offset_ALMA2, alma_sigma=ha_sigma_ALMA2,
                  lsma_offset=ha_LSMAO2, ama_weight=ha_AMA_weight_v2,
                  frama_a=ha_FAMA_i4, frama_b=ha_FAMA_i5)
        O = _ha_ma(ha_ma2, o2, h2, l2, **k2)
        H = _ha_ma(ha_ma2, h2, h2, l2, **k2)
        L = _ha_ma(ha_ma2, l2, h2, l2, **k2)
        C = _ha_ma(ha_ma2, c2, h2, l2, **k2)
    pO, pC = P.shift(O, 1), P.shift(C, 1)
    return (P.F((pO > pC) & (O < C)), P.F((pO < pC) & (O > C)),
            P.F(O < C), P.F(O > C))


def hieken_ashi_smoothed_signals(o, h, l, c, ma_type1='T3', ma_len1=8,
                                 ma_type2='T3', ma_len2=8, single_smooth=False,
                                 vol_factor1=0.82, alma_offset1=0.85,
                                 alma_sigma1=6, lsma_offset1=0,
                                 ama_smooth1=0.181, frama_t1_a=1,
                                 frama_t1_b=168, vol_factor2=0.82,
                                 alma_offset2=0.85, alma_sigma2=6,
                                 lsma_offset2=0, ama_smooth2=0.181,
                                 frama_t2_a=1, frama_t2_b=168):
    return hieken_ashi_smoothed(o, h, l, c, ma_type1, ma_len1, ma_type2,
                                ma_len2, single_smooth, vol_factor1,
                                alma_offset1, alma_sigma1, lsma_offset1,
                                ama_smooth1, frama_t1_a, frama_t1_b,
                                vol_factor2, alma_offset2, alma_sigma2,
                                lsma_offset2, ama_smooth2, frama_t2_a,
                                frama_t2_b)


def hieken_ashi_smoothed_exit(o, h, l, c, **kw):
    lt, st, lc, sc = hieken_ashi_smoothed_signals(o, h, l, c, **kw)
    return st, lt


def _rex_ma(kind, tvb, h, l, smooth, alma_offset=0.85, alma_sigma=6,
            frama_fast=34, frama_slow=89, jma_phase=1, jma_power=1,
            ls_offset=0, mf_beta=0.8, mf_feedback=False, mf_weight=0.5,
            vol_lookback=10):
    """Rex's seventeen-way switch, one arm at a time. Three of its types have
    no analogue in the Heiken Ashi list:

      RDMA  a flat mean of six SMAs at 200/100/50/24/9/5 -- FIXED lengths, so
            rex_smooth does not touch it and every RDMA row in a parameter
            sweep is the same series.
      UMA   the same idea over eight Fibonacci lengths, also fixed.
      MF    Modular Filter -- a two-sided ratchet with an optional feedback
            term that mixes the previous output back into the input.
    """
    tvb = np.asarray(tvb, float)
    n = int(smooth)
    half = int(P.idiv(n, 2))
    if kind == 'SMA':
        return P.sma(tvb, n)
    if kind == 'EMA':
        return P.ema(tvb, n)
    if kind == 'RMA':
        return P.rma(tvb, n)
    if kind == 'WMA':
        return P.wma(tvb, n)
    if kind == 'ALMA':
        return P.alma(tvb, n, alma_offset, alma_sigma)
    if kind == 'LSMA':
        return P.linreg(tvb, n, ls_offset)
    if kind == 'HMA':
        return P.wma(2 * P.wma(tvb, half) - P.wma(tvb, n),
                     int(round(np.sqrt(n))))
    if kind == 'DEMA':
        e1 = P.ema(tvb, n)
        return 2 * e1 - P.ema(e1, n)
    if kind == 'TEMA':
        e1 = P.ema(tvb, n); e2 = P.ema(e1, n); e3 = P.ema(e2, n)
        return 3 * (e1 - e2) + e3          # the real TEMA, unlike the HA one
    if kind == 'T3':
        return _ha_ma('T3', tvb, h, l, length=n)
    if kind == 'TMA':
        return P.sma(P.sma(tvb, int(np.ceil(P.idiv(n, 2)))),
                     int(np.floor(P.idiv(n, 2))) + 1)
    if kind == 'FRAMA':
        return _ha_ma('FAMA', tvb, h, l, length=n, frama_a=frama_fast,
                      frama_b=frama_slow)
    if kind == 'RDMA':
        return sum(P.sma(tvb, k) for k in (200, 100, 50, 24, 9, 5)) / 6.0
    if kind == 'UMA':
        return sum(P.sma(tvb, k) for k in (144, 89, 55, 34, 21, 13, 8, 5)) / 8.0
    if kind == 'VAMA':
        mid = P.ema(tvb, n)
        dev = tvb - mid
        return mid + (P.highest(dev, vol_lookback)
                      + P.lowest(dev, vol_lookback)) / 2.0
    if kind == 'JMA':
        pr = 0.5 if jma_phase < -100 else (2.5 if jma_phase > 100
                                           else jma_phase / 100.0 + 1.5)
        beta = 0.45 * (n - 1) / (0.45 * (n - 1) + 2)
        alpha = beta ** jma_power
        out = np.empty(tvb.size); e0 = e1 = e2 = st = 0.0
        for i in range(tvb.size):
            x = tvb[i] if np.isfinite(tvb[i]) else 0.0
            e0 = (1 - alpha) * x + alpha * e0
            e1 = (x - e0) * (1 - beta) + beta * e1
            e2 = (e0 + pr * e1 - st) * (1 - alpha) ** 2 + alpha ** 2 * e2
            st = e2 + st
            out[i] = st
        return out
    if kind == 'MF':
        a = 2.0 / (n + 1)
        out = np.empty(tvb.size)
        ts = np.nan; b = np.nan; cc = np.nan; os_ = 0.0
        for i in range(tvb.size):
            x = tvb[i] if np.isfinite(tvb[i]) else 0.0
            ain = (mf_weight * x + (1 - mf_weight) * (ts if np.isfinite(ts) else x)
                   ) if mf_feedback else x
            pb = b if np.isfinite(b) else ain
            pc = cc if np.isfinite(cc) else ain
            cand_b = a * ain + (1 - a) * pb
            cand_c = a * ain + (1 - a) * pc
            b = ain if ain > cand_b else cand_b
            cc = ain if ain < cand_c else cand_c
            os_ = 1.0 if ain == b else (0.0 if ain == cc else os_)
            upper = mf_beta * b + (1 - mf_beta) * cc
            lower = mf_beta * cc + (1 - mf_beta) * b
            ts = os_ * upper + (1 - os_) * lower
            out[i] = ts
        return out
    return np.zeros(tvb.shape)


def rex_oscillator(o, h, l, c, rex_ma_type1='SMA', rex_smooth_length=13,
                   rex_alma_offset=0.85, rex_alma_sigma=6, rex_frama_fast=34,
                   rex_frama_slow=89, rex_jma_phase=1, rex_jma_power=1,
                   rex_least_squares_offset=0, rex_modular_filter_beta=0.8,
                   rex_modular_filter_feedback=False,
                   rex_modular_feedback_weight=0.5,
                   rex_volatility_lookback=10, rex_signal_ma_type='SMA',
                   rex_signal_smoothing=13, rex_signal_ma_alma_offset=0.85,
                   rex_signal_ma_alma_sigma=6, rex_signal_ma_frama_fast=34,
                   rex_signal_ma_frama_slow=89, rex_signal_ma_jma_phase=1,
                   rex_signal_ma_jma_power=1,
                   rex_signal_ma_least_squares_offset=0,
                   rex_signal_ma_modular_filter_beta=0.8,
                   rex_signal_ma_modular_filter_feedback=False,
                   rex_signal_ma_modular_feedback_weight=0.5,
                   rex_signal_ma_volatility_lookback=10):
    """tvb = close - low + close - open - (high - close), smoothed twice: once
    as the oscillator, once as its own signal line, each with an independently
    chosen moving average out of seventeen."""
    o = np.asarray(o, float); h = np.asarray(h, float)
    l = np.asarray(l, float); c = np.asarray(c, float)
    tvb = c - l + c - o - (h - c)
    rex = _rex_ma(rex_ma_type1, tvb, h, l, rex_smooth_length, rex_alma_offset,
                  rex_alma_sigma, rex_frama_fast, rex_frama_slow,
                  rex_jma_phase, rex_jma_power, rex_least_squares_offset,
                  rex_modular_filter_beta, rex_modular_filter_feedback,
                  rex_modular_feedback_weight, rex_volatility_lookback)
    # the SIGNAL line smooths tvb again -- it is not a smoothing of `rex`
    sig = _rex_ma(rex_signal_ma_type, tvb, h, l, rex_signal_smoothing,
                  rex_signal_ma_alma_offset, rex_signal_ma_alma_sigma,
                  rex_signal_ma_frama_fast, rex_signal_ma_frama_slow,
                  rex_signal_ma_jma_phase, rex_signal_ma_jma_power,
                  rex_signal_ma_least_squares_offset,
                  rex_signal_ma_modular_filter_beta,
                  rex_signal_ma_modular_filter_feedback,
                  rex_signal_ma_modular_feedback_weight,
                  rex_signal_ma_volatility_lookback)
    return rex, sig


def rex_oscillator_signals(o, h, l, c, maType='SMA', smooth=13,
                           almaOffset=0.85, almaSigma=6, framaFast=34,
                           framaSlow=89, jurikPhase=1, jurikPower=1, lsOffset=0,
                           modFilter=0.8, modFB=False, modFBW=0.5, volAdj=10,
                           sigMaType='SMA', sigSmooth=13, sigAlmaOff=0.85,
                           sigAlmaSig=6, sigFramaFast=34, sigFramaSlow=89,
                           sigJurikPhase=1, sigJurikPower=1, sigLsOff=0,
                           sigModFilter=0.8, sigModFB=False, sigModFBW=0.5,
                           sigVolAdj=10):
    rex, sig = rex_oscillator(o, h, l, c, maType, smooth, almaOffset, almaSigma,
                              framaFast, framaSlow, jurikPhase, jurikPower,
                              lsOffset, modFilter, modFB, modFBW, volAdj,
                              sigMaType, sigSmooth, sigAlmaOff, sigAlmaSig,
                              sigFramaFast, sigFramaSlow, sigJurikPhase,
                              sigJurikPower, sigLsOff, sigModFilter, sigModFB,
                              sigModFBW, sigVolAdj)
    return (P.crossover(rex, sig), P.crossunder(rex, sig),
            P.F(rex > sig), P.F(rex < sig))


def rex_oscillator_exit(o, h, l, c, **kw):
    lt, st, lc, sc = rex_oscillator_signals(o, h, l, c, **kw)
    return st, lt


# --- confirmation batch E, the two composites.
for _n, _f, _slot, _d, _ln in [
        ('hieken_ashi_smoothed_signals', hieken_ashi_smoothed_signals,
         'confirmation',
         dict(ma_type1='T3', ma_len1=8, ma_type2='T3', ma_len2=8,
              single_smooth=False, vol_factor1=0.82, alma_offset1=0.85,
              alma_sigma1=6, lsma_offset1=0, ama_smooth1=0.181, frama_t1_a=1,
              frama_t1_b=168, vol_factor2=0.82, alma_offset2=0.85,
              alma_sigma2=6, lsma_offset2=0, ama_smooth2=0.181, frama_t2_a=1,
              frama_t2_b=168), 'strat 258-276'),
        ('hieken_ashi_smoothed_exit', hieken_ashi_smoothed_exit, 'exit',
         dict(), 'strat 258-276'),
        ('rex_oscillator_signals', rex_oscillator_signals, 'confirmation',
         dict(maType='SMA', smooth=13, almaOffset=0.85, almaSigma=6,
              framaFast=34, framaSlow=89, jurikPhase=1, jurikPower=1,
              lsOffset=0, modFilter=0.8, modFB=False, modFBW=0.5, volAdj=10,
              sigMaType='SMA', sigSmooth=13, sigAlmaOff=0.85, sigAlmaSig=6,
              sigFramaFast=34, sigFramaSlow=89, sigJurikPhase=1,
              sigJurikPower=1, sigLsOff=0, sigModFilter=0.8, sigModFB=False,
              sigModFBW=0.5, sigVolAdj=10), 'strat 327-352'),
        ('rex_oscillator_exit', rex_oscillator_exit, 'exit', dict(),
         'strat 327-352')]:
    _reg(_n, _f, _slot, _d, _ln, True)
KIND.update({k: v['kind'] for k, v in REGISTRY.items()})

# Inert at the shipped defaults -- they run, they just never say anything.
# Each is verified in the commit message; a sweep that selects one gets zero
# trades, which reads as "no edge" rather than "misconfigured".
INERT_AT_DEFAULTS = {
    'damiani_volatmeter_volume_signals',   # passes 0.044% of bars
    'volatility_quality_signals',          # dead band 859x too wide; 0 triggers
    'rex_oscillator_signals',              # osc and its signal are one series
}


if __name__ == '__main__':
    main()
