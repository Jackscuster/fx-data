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
                              available=k not in UNAVAILABLE)
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
            rows.append(dict(name=name, ok=ok and not (lc & sc).any(),
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
    print(T.to_string(index=False))
    print('\n  every contract shaped, typed and mutually exclusive: %s'
          % bool(T.ok.all()))

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


if __name__ == '__main__':
    main()
