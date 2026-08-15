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
                              pine_line=v['pine_line'], source=v['source'])
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


if __name__ == '__main__':
    main()
