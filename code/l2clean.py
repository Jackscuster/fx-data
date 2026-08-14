import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""THE BACKTEST DATASET. Repairs four defects in the raw Yahoo download, counts
every one of them, and never touches the raw files.

  data/ohlc/       raw, exactly as downloaded by l2data.py -- never modified
  data/ohlc_clean/ what the engine reads

Each repair below was diagnosed against evidence, not assumed. The evidence is
recorded here because a later reader will otherwise re-derive it or, worse,
"fix" a repair that is load-bearing.

--------------------------------------------------------------------------
1. SUNDAY-STAMPED BARS ARE FRIDAY BARS, TWO DAYS LATE
--------------------------------------------------------------------------
Yahoo stamps the last bar of the FX week on Sunday during US daylight saving
and on Friday outside it: the Sunday share of end-of-week bars is 0% in
Nov-Feb and 100% in Apr-Sep, which is the DST calendar exactly. It is a
timestamp artifact, not a Sunday trading session.

The test that settles it: take each Sunday-stamped bar's close and compare it
to the H.10 noon rate on the PRECEDING FRIDAY and on the FOLLOWING MONDAY.
Across all 28 pairs, 28 of 28 match the preceding Friday better -- median
deviation 0.155% against 0.218% for Monday. For scale, an ordinary weekday
bar matched to its own H.10 date deviates 0.184%. So the Sunday bar sits
CLOSER to Friday's H.10 rate than a normal bar sits to its own: it is a
Friday bar wearing the wrong date.

This matters beyond tidiness. Layer 1's regime labels are dated Mon-Fri, so
joining on the raw dates would silently drop or misalign the end-of-week bar
in roughly three weeks out of five.

--------------------------------------------------------------------------
2. DST-TRANSITION WEEKS CARRY THE FRIDAY BAR TWICE
--------------------------------------------------------------------------
In the changeover week both stamps appear -- a Friday bar and a Sunday bar two
days later, 651 such weeks across the 28 pairs (~23 per pair, about one a
year). Against H.10's Friday close the two are indistinguishable: median
deviation 0.183% for the Friday-stamped bar, 0.177% for the Sunday-stamped
one, with the Sunday version closer in 49.5% of cases -- a coin flip. There is
no basis for preferring one, so the rule is the boring one: KEEP THE BAR
ALREADY STAMPED FRIDAY, drop the Sunday duplicate. 0.4% of bars.

--------------------------------------------------------------------------
3. THE HIGH IS SOMETIMES BELOW THE OPEN OR CLOSE
--------------------------------------------------------------------------
1.35% of bar-sides violate what an OHLC bar means. 38% of the violations are
under one pip and are plainly rounding between a 6dp close and a 4dp high, but
the tail is not: the 99th percentile is 70 pips and the worst is 999.

Repaired by clamping -- high := max(open, high, close), low := min(open, low,
close). The clamp can only WIDEN a bar, never narrow it, so it cannot invent a
stop or target fill that the raw feed rules out; it makes fills more likely,
and with stop-before-target tie-breaking that is the pessimistic direction.

--------------------------------------------------------------------------
4. BAD PRINTS: SPIKE AND REVERT
--------------------------------------------------------------------------
Some large one-day moves are real -- the 2015-01-16 CHF unpeg, the October
2008 carry unwind, Brexit. Others are feed errors that spike one day and undo
it the next: EURUSD 1.2717 -> 1.4918 -> 1.2926 in December 2008, EURGBP
0.87692 -> 0.97900 -> 0.87658 in October 2022. Neither level ever traded.

A real move persists; a bad print reverses. So a bar is flagged suspect when
|r_t| > JUMP and the two-day sum |r_t + r_t+1| < REVERT * |r_t| -- a big move
that gives back most of itself immediately. The CHF unpeg does not reverse and
survives the test, which is the point of testing reversion rather than size.

FLAGGED, NOT DELETED. Deleting breaks the bar chain and the flag is a result in
its own right. The row stays with suspect=True and the engine is told not to
open or close a position on a suspect bar.

Flat bars (high == low, a feed stall -- 353 of them, 264 in 2009 alone) are
flagged the same way: no range means no ATR contribution and no honest
intrabar fill.

Writes data/ohlc_clean/<PAIR>.csv and results/l2_clean_report.csv.
"""
import glob
import numpy as np, pandas as pd

RAW = os.path.join(ROOTDATA, 'ohlc')
OUT = os.path.join(ROOTDATA, 'ohlc_clean')
REP = os.path.join(ROOTOUT, 'l2_clean_report.csv')
PX = os.path.join(ROOTDATA, 'px28.csv')

JUMP = 0.05        # a one-day log move this big is examined
REVERT = 0.40      # ...and is a bad print if the 2-day sum keeps under this much of it


def clean_one(d):
    """-> cleaned frame, dict of counts. Order matters: remap, then dedup, then
    clamp, then flag -- clamping before dedup would repair a bar about to be
    dropped and inflate the clamp count."""
    n = dict(raw_bars=len(d))

    # 1. Sunday -> the preceding Friday
    sun = d.index.dayofweek == 6
    n['sunday_remapped'] = int(sun.sum())
    idx = d.index.where(~sun, d.index - pd.Timedelta(days=2))
    d = d.set_axis(pd.DatetimeIndex(idx)).sort_index()

    # anything still off the weekday grid is unexplained -- count it, never drop
    n['nonweekday_left'] = int((d.index.dayofweek >= 5).sum())

    # 2. collisions: the remap put two bars on one Friday. keep the first, which
    # is the one that was already stamped Friday (sort_index is stable)
    dup = d.index.duplicated(keep='first')
    n['collision_dropped'] = int(dup.sum())
    d = d[~dup]

    # 3. clamp the bar back to being a bar
    o, h, l, c = (d[k].values.copy() for k in ('open', 'high', 'low', 'close'))
    nh, nl = np.maximum.reduce([o, h, c]), np.minimum.reduce([o, l, c])
    n['clamped_high'] = int((nh > h).sum()); n['clamped_low'] = int((nl < l).sum())
    n['clamp_max_pips'] = float(1e4 * np.max(np.concatenate(
        [(nh - h) / c, (l - nl) / c]))) if len(d) else 0.0
    d = d.assign(high=nh, low=nl)

    # 4. flags
    r = np.diff(np.log(d.close.values), prepend=np.nan)
    nxt = np.roll(r, -1); nxt[-1] = np.nan
    big = np.abs(r) > JUMP
    reverted = np.abs(r + nxt) < REVERT * np.abs(r)
    bad = big & reverted & np.isfinite(nxt)
    # the reverting bar is as untradable as the spike, so flag the pair of them
    bad = bad | np.roll(bad, 1)
    flat = (d.high.values == d.low.values)
    d = d.assign(suspect=bad | flat, suspect_spike=bad, suspect_flat=flat)
    n['suspect_spike'] = int(bad.sum()); n['suspect_flat'] = int(flat.sum())
    n['suspect'] = int(d.suspect.sum())
    n['clean_bars'] = len(d)
    return d, n


def main():
    os.makedirs(OUT, exist_ok=True)
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    rows = []
    for f in sorted(glob.glob(os.path.join(RAW, '*.csv'))):
        p = os.path.basename(f)[:-4]
        d = pd.read_csv(f, index_col=0, parse_dates=True)
        cl, n = clean_one(d)
        cl.to_csv(os.path.join(OUT, '%s.csv' % p), float_format='%.6f')
        n['pair'] = p
        # did the remap improve date-matched agreement with the H.10 panel?
        if p in px.columns:
            for tag, fr in (('raw', d), ('clean', cl)):
                j = pd.concat([fr.close.rename('y'), px[p].rename('h')],
                              axis=1).dropna()
                n['med_diff_%s_pct' % tag] = round(
                    100 * float(((j.y - j.h).abs() / j.h).median()), 4)
                n['matched_%s' % tag] = len(j)
        rows.append(n)
    R = pd.DataFrame(rows).set_index('pair').reset_index()
    R.to_csv(REP, index=False)

    pd.set_option('display.width', 220)
    print('CLEANING REPORT')
    print(R[['pair', 'raw_bars', 'clean_bars', 'sunday_remapped',
             'collision_dropped', 'clamped_high', 'clamped_low',
             'suspect_spike', 'suspect_flat']].to_string(index=False))
    s = R[['sunday_remapped', 'collision_dropped', 'clamped_high', 'clamped_low',
           'suspect_spike', 'suspect_flat']].sum()
    print('\nTOTALS across 28 pairs: %s' % s.to_dict())
    print('worst single clamp: %.1f pips (%s)'
          % (R.clamp_max_pips.max(), R.loc[R.clamp_max_pips.idxmax(), 'pair']))
    print('suspect bars: %d of %d (%.3f%%)'
          % (R.suspect.sum(), R.clean_bars.sum(),
             100 * R.suspect.sum() / R.clean_bars.sum()))

    print('\nAGREEMENT WITH THE H.10 PANEL, date-matched -- the remap test')
    print('  median |Yahoo - H.10| / H.10 across pairs:  raw %.4f%%  clean %.4f%%'
          % (R.med_diff_raw_pct.median(), R.med_diff_clean_pct.median()))
    print('  dates matched to a Layer 1 label:           raw %d  clean %d  (+%.1f%%)'
          % (R.matched_raw.sum(), R.matched_clean.sum(),
             100 * (R.matched_clean.sum() / R.matched_raw.sum() - 1)))
    print('  improved on %d of %d pairs'
          % (int((R.med_diff_clean_pct < R.med_diff_raw_pct).sum()), len(R)))

    wk = []
    for f in sorted(glob.glob(os.path.join(OUT, '*.csv'))):
        d = pd.read_csv(f, index_col=0, parse_dates=True)
        iso = d.index.isocalendar()
        wk.append(pd.Series(list(zip(iso.year, iso.week))).value_counts()
                  .value_counts())
    W = pd.concat(wk, axis=1).sum(axis=1).sort_index()
    print('\nBARS PER WEEK after cleaning: %s' % W.to_dict())
    print('\nwrote data/ohlc_clean/<PAIR>.csv, results/l2_clean_report.csv')
    return R


if __name__ == '__main__':
    main()
