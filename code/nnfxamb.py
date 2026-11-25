import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""ITEM 1 — RESOLVING AMBIGUOUS BARS FROM THE HOURLY BID/ASK PATH.

l2engine fills the STOP whenever one daily bar covers both the stop and the
target, because a daily bar cannot say which came first. A5 measured the TARGET
first on 40% of such days. Condition 4 then showed what that costs: random
entries under the stop-and-target plan lose 0.0203 R per trade GROSS of costs,
where the same entries under a flip-only exit are unbiased. So the convention is
not conservative book-keeping, it is a measurable bias in the apparatus.

THE FIX IS IN THE ONE ENGINE, OPT-IN. l2engine.run_bars now takes
(hb_lo, hb_hi, ha_lo, ha_hi, hr_off, hr_on, amb_counts). With hr_on False it
behaves exactly as before -- verified by running the identical test on the
pre-patch commit and the patched tree and getting byte-identical trade counts,
R sums and holding periods on six pairs, three indicators and both variants.

THE QUOTE SIDE IS THE ONE THAT WOULD FILL: a long exits by selling, so its stop
and target both fill on the BID; a short exits by buying, so both fill on the
ASK. The mid would flatter both levels by half a spread.

THE DAILY-TO-HOURLY ALIGNMENT WAS MEASURED, NOT ASSUMED. The gauntlet's daily
feed is data/oanda_ohlc, which is NOT the 17:00 NY file HANDOFF describes for
Layer 1 (that is data/px28_5pm.csv from build5pm.py). Scanning every candidate
cut, the daily bar dated D is best matched by the window
(16:00 New York on D-1, 16:00 New York on D], DST handled:

    tz-aware NY cut   daily range contained in hourly   hourly NARROWER
      16:00                    72.8%                        16.8%
      15:00                    66.5%                        23.0%
      17:00                    62.8%                        27.8%
    best fixed-UTC cut 20:00:  71.2%

72.8% IS NOT 100%, AND THAT IS A PROPERTY OF THE DATA, NOT A BUG. The two feeds
are different products: on 16.8% of bars the hourly range is NARROWER than the
daily one, so the hourly file simply does not cover every tick the daily bar
saw. The resolver degrades correctly rather than guessing -- _amb_first returns
0 when its window cannot order the two levels, the engine keeps stop-first, and
the case is COUNTED. Every report says how many bars were ambiguous, how they
resolved, and how many could not be resolved.
"""
import time, glob, json, hashlib
import numpy as np, pandas as pd

import l2sweep as S
import l2engine as E
import l2r2gate1 as G

OUT = os.path.join(ROOTOUT, 'nnfx')
os.makedirs(OUT, exist_ok=True)
H1 = os.path.join(ROOTDATA, 'oanda_h1')
CUT_HOUR_NY = 16
_IDX = {}


def hourly_index(pair, dates=None):
    """-> (hb_lo, hb_hi, ha_lo, ha_hi, hr_off, hb_op, ha_op) aligned to
    `pair`'s daily bars.

    hr_off[i]:hr_off[i+1] slices the flat arrays to daily bar i's hourly
    sub-bars, in time order. Empty for a bar with no hourly coverage.

    THE OPENS ARE HERE FOR THE GAP FILLS (Jack item 1, 25 Nov). _amb_first
    only ever needed the hourly highs and lows -- which level was touched
    first. l2engine._gap_px needs the price that was actually QUOTED when the
    level was first breached, and that is the open of the hour that breached
    it. Loading them in the same pass costs one more column per file and
    keeps one alignment, one session cut and one cache for both uses.
    """
    key = pair
    if key in _IDX:
        return _IDX[key]
    fb = os.path.join(H1, '%s_bid.csv' % pair)
    fa = os.path.join(H1, '%s_ask.csv' % pair)
    d = S.load_pair(pair)
    n = len(d)
    if not (os.path.exists(fb) and os.path.exists(fa)):
        _z = E._amb_off(n)
        _IDX[key] = _z[:5] + (_z[0], _z[0])
        return _IDX[key]
    b = pd.read_csv(fb, parse_dates=['time'],
                    usecols=['time', 'o', 'h', 'l'])
    a = pd.read_csv(fa, parse_dates=['time'],
                    usecols=['time', 'o', 'h', 'l'])
    j = b.merge(a, on='time', suffixes=('_b', '_a')).sort_values('time')
    t = pd.DatetimeIndex(j.time.values)
    if t.tz is None:
        t = t.tz_localize('UTC')
    # which daily bar each hourly bar belongs to: the NY-16:00 session day
    ny = t.tz_convert('America/New_York')
    sess = (ny - pd.Timedelta(hours=CUT_HOUR_NY)).normalize()
    # a bar at or after 16:00 NY belongs to the NEXT session day
    sess = sess + pd.Timedelta(days=1)
    sess = pd.DatetimeIndex(sess).tz_localize(None).normalize()
    dd = pd.DatetimeIndex(d.index).normalize()
    pos = pd.Series(np.arange(n), index=dd)
    bar = sess.map(pos)
    ok = bar.notna() if hasattr(bar, 'notna') else ~pd.isna(bar)
    bar = np.asarray(bar, dtype=float)
    m = np.isfinite(bar)
    bar = bar[m].astype(np.int64)
    hb_lo = j.l_b.to_numpy(np.float64)[m]; hb_hi = j.h_b.to_numpy(np.float64)[m]
    ha_lo = j.l_a.to_numpy(np.float64)[m]; ha_hi = j.h_a.to_numpy(np.float64)[m]
    hb_op = j.o_b.to_numpy(np.float64)[m]; ha_op = j.o_a.to_numpy(np.float64)[m]
    o = np.argsort(bar, kind='stable')
    bar = bar[o]; hb_lo = hb_lo[o]; hb_hi = hb_hi[o]
    ha_lo = ha_lo[o]; ha_hi = ha_hi[o]
    hb_op = hb_op[o]; ha_op = ha_op[o]
    cnt = np.bincount(bar, minlength=n)
    hr_off = np.zeros(n + 1, np.int64)
    np.cumsum(cnt, out=hr_off[1:])
    _IDX[key] = (np.ascontiguousarray(hb_lo), np.ascontiguousarray(hb_hi),
                 np.ascontiguousarray(ha_lo), np.ascontiguousarray(ha_hi),
                 hr_off,
                 np.ascontiguousarray(hb_op), np.ascontiguousarray(ha_op))
    return _IDX[key]


# GAP FILLS ARE STANDING FROM 25 NOV 2026 (Jack item 1). amb_args turns them on
# wherever the pair has an hourly path; gapfill=False is for the before/after
# measurement in nnfxgap.py and for nothing else.
GAPFILL_STANDING = True


def gf_tol(pair):
    """The pair's round-trip cost as a fraction of price -- the threshold
    below which an hourly open beyond a mid stop is a SPREAD, not a gap.

    THE TABLE IS THE RUN'S OWN. If the caller has already loaded a cost table
    the tolerance uses THAT one, so the charge the gap fill declines to make
    twice is the charge the run is actually making. Only a bare call loads a
    table, and it loads the standing one -- cost_table_h22.csv, never the flat
    default, which would set the tolerance from a cost nothing is charging.
    """
    if not S.COSTS:
        S.load_costs(os.environ.get(
            'FX_COST_TABLE', os.path.join(ROOTOUT, 'cost_table_h22.csv')))
    return float(S.COSTS.get(pair, 0.0))


def amb_args(pair, gapfill=None):
    """The 12-tuple run_bars wants, with hourly ON for this pair.

    Returns (hb_lo, hb_hi, ha_lo, ha_hi, hr_off, hr_on, amb_counts,
             hb_op, ha_op, gf_on, gf_tol, gap_counts).
    """
    hb_lo, hb_hi, ha_lo, ha_hi, hr_off, hb_op, ha_op = hourly_index(pair)
    on = bool(hr_off[-1] > 0)
    gf = GAPFILL_STANDING if gapfill is None else bool(gapfill)
    return (hb_lo, hb_hi, ha_lo, ha_hi, hr_off, on, np.zeros(3, np.int64),
            hb_op, ha_op, bool(gf and on), gf_tol(pair),
            np.zeros(4, np.int64))


def coverage_report(out=None):
    """How much of each pair's daily span the hourly index actually covers."""
    rows = []
    for p in S.all_pairs():
        d = S.load_pair(p)
        hb_lo, hb_hi, ha_lo, ha_hi, hr_off, hb_op, ha_op = hourly_index(p)
        per = np.diff(hr_off)
        rows.append(dict(pair=p, daily_bars=len(d),
                         bars_with_hourly=int((per > 0).sum()),
                         share_covered=float((per > 0).mean()),
                         median_subbars=float(np.median(per[per > 0]))
                         if (per > 0).any() else 0.0,
                         hourly_rows=int(hr_off[-1])))
    D = pd.DataFrame(rows)
    out = out or os.path.join(OUT, 'amb_hourly_coverage.csv')
    D.to_csv(out, index=False)
    print('  hourly index: %d pairs, %.1f%% of daily bars have hourly sub-bars, '
          'median %.0f sub-bars per covered bar'
          % (len(D), 100 * D.share_covered.mean(), D.median_subbars.median()),
          flush=True)
    return D
