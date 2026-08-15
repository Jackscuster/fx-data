import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""PINE PRIMITIVES IN NUMPY. The ta.* and math.* functions the library calls.

PARITY LIVES OR DIES HERE. Every indicator in the library is a composition of
these, so an ema that seeds differently from Pine's is not a small error -- it
is a permanent offset injected into forty indicators at once. The seeding rules
below are the ones TradingView actually uses, not the textbook ones:

  ta.sma      na until `length` bars are available, then the plain mean.
  ta.ema      NOT seeded with the first value. Pine returns na for the first
              length-1 bars and seeds with the SMA of the first full window.
              Seeding with src[0] instead (the common shortcut) leaves a
              decaying error that takes ~5 x length bars to fall below a pip.
  ta.rma      Wilder. Same rule: seeded with the first full SMA, alpha = 1/len.
  ta.stdev    POPULATION (ddof=0), which is what Pine uses. numpy's default.
  ta.linreg   the fitted value at the end of the window, offset bars back.
  ta.change   src - src[length], na during warm-up.
  ta.tr(true) true range with the first bar falling back to high - low.
  ta.atr      rma(tr, length).
  ta.sar      Wilder's parabolic, with TradingView's exact initialisation --
              see the note on that function, it is the fiddliest thing here.

A SEPARATE RULE FOR HAND-ROLLED RECURSIONS. Several library functions do not
call ta.ema at all; they write `var float x = 0.0` and then
`x := alpha * src + (1-alpha) * nz(x[1])`. That seeds at ZERO on the first bar,
not with an SMA, and it produces a different series. Those are ported with
`recur_nz` rather than `ema`, and the distinction is preserved deliberately --
the patch's Ehlers cascade and Coral both depend on it.

INT DIVISION IS AN OPEN PARITY QUESTION. Pine's `/` on two ints is documented
ambiguously across versions, and triangular_moving_average does
`math.ceil(len/2)` and `math.floor(len/2)+1`. If `/` truncates, the ceil and
floor are no-ops and TMA(20) is sma(sma(c,10),11). If it returns a float they
are the same for even lengths and differ for odd. Both are implemented and
selectable; TMA is the DEFAULT BASELINE, so the Phase 3 parity run settles it
empirically rather than by argument. See PINE_INT_DIV.
"""
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view as _swv

# See the docstring. True = Pine's `/` truncates on int operands.
PINE_INT_DIV = False


def _a(x):
    return np.asarray(x, dtype=float)


def _roll(a, n):
    """(len(a), n) windows, NaN-padded at the front, so index i is the window
    ENDING at i. Warm-up rows contain NaN and the PROPAGATING reductions are
    used everywhere, which is how Pine returns na until a window is full."""
    a = _a(a)
    if n <= 0:
        raise ValueError('length must be >= 1, got %r' % n)
    return _swv(np.concatenate([np.full(n - 1, np.nan), a]), n)


def nz(a, repl=0.0):
    a = _a(a).copy()
    r = _a(repl) if np.ndim(repl) else repl
    m = ~np.isfinite(a)
    a[m] = (r[m] if np.ndim(repl) else repl)
    return a


def fixnan(a):
    """Pine's fixnan: carry the last non-na value forward."""
    a = _a(a).copy()
    good = np.isfinite(a)
    if not good.any():
        return a
    idx = np.where(good, np.arange(a.size), 0)
    np.maximum.accumulate(idx, out=idx)
    out = a[idx]
    out[:np.argmax(good)] = np.nan
    return out


def shift(a, k=1):
    """src[k]. Pine indexes backwards, so shift(x, 1)[i] == x[i-1]."""
    a = _a(a)
    out = np.full(a.shape, np.nan)
    if k > 0:
        out[k:] = a[:-k]
    elif k < 0:
        out[:k] = a[-k:]
    else:
        out[:] = a
    return out


def idiv(a, b):
    """Pine's `/` on two ints -- see PINE_INT_DIV."""
    return (a // b) if PINE_INT_DIV else (a / b)


# ---------------------------------------------------------------- averages
def sma(src, length):
    return _roll(src, int(length)).mean(axis=1)


def _seeded(src, length, alpha):
    """The shared body of ta.ema and ta.rma: na until the first full window,
    seeded there with that window's SMA, recursive after."""
    src = _a(src); n = int(length)
    out = np.full(src.shape, np.nan)
    if src.size < n:
        return out
    # the seed is the mean of the first n FINITE values, at their last index
    fin = np.flatnonzero(np.isfinite(src))
    if fin.size < n:
        return out
    s0 = fin[n - 1]
    prev = np.mean(src[fin[:n]])
    out[s0] = prev
    for i in range(s0 + 1, src.size):
        x = src[i]
        if np.isfinite(x):
            prev = prev + alpha * (x - prev)
        out[i] = prev
    return out


def ema(src, length):
    return _seeded(src, length, 2.0 / (int(length) + 1.0))


def rma(src, length):
    return _seeded(src, length, 1.0 / int(length))


def wma(src, length):
    n = int(length)
    w = np.arange(1, n + 1, dtype=float)
    return (_roll(src, n) * w).sum(axis=1) / w.sum()


def vwma(src, vol, length):
    """Volume-weighted. On spot FX the volume series is identically zero, which
    makes this 0/0 -- the caller must decide, this does not silently pretend."""
    n = int(length)
    num = _roll(_a(src) * _a(vol), n).sum(axis=1)
    den = _roll(vol, n).sum(axis=1)
    with np.errstate(invalid='ignore', divide='ignore'):
        return np.where(den != 0, num / den, np.nan)


def hma(src, length):
    n = int(length)
    return wma(2.0 * wma(src, max(1, n // 2)) - wma(src, n),
               max(1, int(round(np.sqrt(n)))))


def alma(src, length, offset, sigma):
    n = int(length)
    m = offset * (n - 1)
    s = n / float(sigma)
    w = np.exp(-((np.arange(n) - m) ** 2) / (2 * s * s))
    W = _roll(src, n)
    return (W * w).sum(axis=1) / w.sum()


def recur_nz(src, alpha, seed=0.0):
    """x := alpha*src + (1-alpha)*nz(x[1]) -- the hand-rolled recursion several
    library functions use INSTEAD of ta.ema. Seeds at `seed` on the first bar
    rather than with an SMA, and that difference is load-bearing."""
    src = _a(src)
    out = np.empty(src.shape)
    prev = seed
    for i in range(src.size):
        x = src[i]
        if not np.isfinite(x):
            x = 0.0
        prev = alpha * x + (1.0 - alpha) * prev
        out[i] = prev
    return out


# ------------------------------------------------------- range / dispersion
def stdev(src, length):
    """Pine's ta.stdev is POPULATION standard deviation."""
    return _roll(src, int(length)).std(axis=1, ddof=0)


def variance_(src, length):
    return _roll(src, int(length)).var(axis=1, ddof=0)


def highest(src, length):
    return _roll(src, int(length)).max(axis=1)


def lowest(src, length):
    return _roll(src, int(length)).min(axis=1)


def msum(src, length):
    return _roll(src, int(length)).sum(axis=1)


def change(src, length=1):
    return _a(src) - shift(src, int(length))


def correlation(a, b, length):
    n = int(length)
    A, B = _roll(a, n), _roll(b, n)
    am, bm = A.mean(axis=1, keepdims=True), B.mean(axis=1, keepdims=True)
    da, db = A - am, B - bm
    num = (da * db).sum(axis=1)
    den = np.sqrt((da * da).sum(axis=1) * (db * db).sum(axis=1))
    with np.errstate(invalid='ignore', divide='ignore'):
        return np.where(den > 0, num / den, np.nan)


def linreg(src, length, offset=0):
    """ta.linreg -- the regression's fitted value `offset` bars back from the
    end of the window."""
    n = int(length)
    W = _roll(src, n)
    x = np.arange(n, dtype=float)
    xd = x - x.mean()
    slope = (W * xd).sum(axis=1) / (xd * xd).sum()
    return W.mean(axis=1) + slope * (n - 1 - x.mean() - offset)


# ------------------------------------------------------------------ crosses
def crossover(a, b):
    a, b = _a(a), _a(b)
    return (a > b) & (shift(a, 1) <= shift(b, 1))


def crossunder(a, b):
    a, b = _a(a), _a(b)
    return (a < b) & (shift(a, 1) >= shift(b, 1))


def cross(a, b):
    return crossover(a, b) | crossunder(a, b)


# ------------------------------------------------------------------- ranges
def tr(h, l, c, handle_na=True):
    """ta.tr(true): the first bar falls back to high - low instead of na."""
    pc = shift(c, 1)
    out = np.maximum(_a(h) - _a(l),
                     np.maximum(np.abs(_a(h) - pc), np.abs(_a(l) - pc)))
    if handle_na:
        out[0] = _a(h)[0] - _a(l)[0]
    return out


def atr(h, l, c, length):
    return rma(tr(h, l, c), length)


def sar(h, l, start, inc, maximum):
    """ta.sar. TradingView seeds on the SECOND bar from the first two closes and
    forbids the SAR entering the previous two bars' range. Both details change
    the flip dates, which is what a confirmation slot is read for."""
    h, l = _a(h), _a(l)
    n = h.size
    out = np.full(n, np.nan)
    if n < 2:
        return out
    up = True
    af = start
    ep = h[1]
    s = l[0]
    out[1] = s
    for i in range(2, n):
        s = s + af * (ep - s)
        if up:
            s = min(s, l[i - 1], l[i - 2])
            if l[i] < s:
                up = False; s = ep; ep = l[i]; af = start
            elif h[i] > ep:
                ep = h[i]; af = min(af + inc, maximum)
        else:
            s = max(s, h[i - 1], h[i - 2])
            if h[i] > s:
                up = True; s = ep; ep = h[i]; af = start
            elif l[i] < ep:
                ep = l[i]; af = min(af + inc, maximum)
        out[i] = s
    return out


def falsy(n):
    return np.zeros(int(n), bool)


def F(x, n=None):
    """A boolean array with NaN read as False -- the contract every signal
    helper returns. numpy treats NaN as True in a boolean cast, which would
    open trades during warm-up."""
    a = np.asarray(x)
    if a.dtype == bool:
        return a
    return np.nan_to_num(_a(a), nan=0.0, posinf=0.0, neginf=0.0) != 0


def state_to_trig(lc, sc):
    """lt/st from lc/sc: the bar a state becomes true having not been."""
    lc, sc = F(lc), F(sc)
    lt = lc & ~np.concatenate([[False], lc[:-1]])
    st = sc & ~np.concatenate([[False], sc[:-1]])
    return lt, st, lc, sc


def latch(up, dn, init=0):
    """dir := up ? 1 : dn ? -1 : dir[1] -- Pine's `var` carry-forward."""
    up, dn = F(up), F(dn)
    out = np.empty(up.size, np.int8)
    cur = init
    for i in range(up.size):
        if up[i]:
            cur = 1
        elif dn[i]:
            cur = -1
        out[i] = cur
    return out


def roc(src, length):
    prev = shift(src, int(length))
    with np.errstate(invalid='ignore', divide='ignore'):
        return np.where(prev != 0, 100.0 * (_a(src) - prev) / prev, np.nan)


def swma(src):
    """ta.swma: the symmetrically weighted 4-bar average, weights 1/6 2/6 2/6
    1/6 with the OLDEST bar first."""
    s = _a(src)
    return (shift(s, 3) / 6.0 + shift(s, 2) * 2.0 / 6.0
            + shift(s, 1) * 2.0 / 6.0 + s / 6.0)


def highestbars(src, length):
    """Offset (<= 0) to the highest bar in the window. 0 means it is this bar."""
    W = _roll(src, int(length))
    idx = np.argmax(np.where(np.isnan(W), -np.inf, W), axis=1)
    out = (idx - (int(length) - 1)).astype(float)
    out[np.isnan(W).any(axis=1)] = np.nan
    return out


def lowestbars(src, length):
    W = _roll(src, int(length))
    idx = np.argmin(np.where(np.isnan(W), np.inf, W), axis=1)
    out = (idx - (int(length) - 1)).astype(float)
    out[np.isnan(W).any(axis=1)] = np.nan
    return out


def supertrend(h, l, c, factor, atr_period):
    """ta.supertrend -> (line, direction).

    DIRECTION IS -1 WHEN THE TREND IS UP and +1 when it is down. That is
    TradingView's convention, not a transcription error, and the library's
    own supertrend_signals reads it the other way round -- see l2lib."""
    h, l, c = _a(h), _a(l), _a(c)
    a = atr(h, l, c, atr_period)
    hl2 = (h + l) / 2.0
    n = c.size
    up = hl2 + factor * a
    dn = hl2 - factor * a
    line = np.full(n, np.nan); direction = np.full(n, np.nan)
    pu = pd_ = np.nan; pdir = 1
    for i in range(n):
        if not np.isfinite(a[i]):
            continue
        u, d = up[i], dn[i]
        if np.isfinite(pu):
            u = min(u, pu) if (c[i - 1] <= pu) else u
            d = max(d, pd_) if (c[i - 1] >= pd_) else d
        if not np.isfinite(pu):
            dirn = 1
        elif line[i - 1] == pu:
            dirn = -1 if c[i] > u else 1
        else:
            dirn = 1 if c[i] < d else -1
        line[i] = d if dirn == -1 else u
        direction[i] = dirn
        pu, pd_, pdir = u, d, dirn
    return line, direction
