import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""LAYER 2's OWN DATASET. Daily OHLC for the 28 G8 pairs, from Yahoo.

WHY THIS EXISTS SEPARATELY FROM px28.csv. Layer 1's panel is the Fed H.10 noon
buying rate: one number a day, close-only. Layer 2 cannot run on it. The risk
plan sizes every trade off ATR, stops and targets fill intrabar against the
high and the low, and about a third of the NNFX indicator library reads the
high/low range directly. None of that exists in a close-only series.

The second reason is portability. A surviving combination has to be reproduced
in Pine on TradingView, which means it has to have been found on real OHLC bars
rather than on a synthetic range reconstructed from closes.

data/px28.csv IS NOT TOUCHED BY THIS FILE and never should be. Layer 1 is
frozen; the two datasets are separate by design and disagree by construction
(different sources, different snapshot times). See the cross-check below --
the disagreement is measured, not assumed away.

WHAT YAHOO GIVES, AND WHAT IT DOES NOT
  History is shorter than Layer 1's. Most pairs begin 2003-12-01, not 1999.
  That is reported per pair rather than padded; inventing pre-2003 bars would
  manufacture exactly the quiet early era the strategy search would then fit.

  THERE IS NO FX VOLUME. Spot FX has no central exchange and no consolidated
  tape, so the volume column comes back all zeros. It is dropped rather than
  carried as a column of zeros that some later indicator silently divides by.
  Every indicator in the NNFX 'volume' slot must therefore be a VOLATILITY or
  RANGE measure -- Choppiness, Efficiency Ratio, VHF, Fractal Dimension, ATR
  ratios. Nothing in that slot may read a volume series, because there is none.

  Yahoo's FX bars are dealer-feed snapshots. The daily bar's open is near the
  prior close by construction and the high/low are the feed's own extremes,
  not a consolidated market range. Treat them as representative, not exact --
  which is why Phase 3 compares against TradingView trade by trade rather than
  assuming the two feeds agree.

RESUMABLE. One CSV per pair under data/ohlc/. A pair that already has a file is
skipped unless --refresh is passed, so a killed run costs one pair.

  python code/l2data.py              # fetch what is missing, then report
  python code/l2data.py --refresh    # refetch every pair
  python code/l2data.py --report     # report only, fetch nothing

Writes data/ohlc/<PAIR>.csv, results/l2_ohlc_coverage.csv and
results/l2_ohlc_checks.csv.
"""
import io, json, time, urllib.request, urllib.parse, urllib.error
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
OUTDIR = os.path.join(ROOTDATA, 'ohlc')
COV = os.path.join(ROOTOUT, 'l2_ohlc_coverage.csv')
CHK = os.path.join(ROOTOUT, 'l2_ohlc_checks.csv')
UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
START = '1998-06-01'
GAPDAYS = 5          # a hole wider than this many TRADING days is flagged

# Spot checks. Levels a person can look up, quoted independently of this
# download, each tested INSIDE A DATE WINDOW rather than against the whole
# series -- two earlier versions of this test were wrong for that reason:
#
#   a global max is not a dated fact. USDJPY's quoted 2024 high was beaten in
#   2026, so testing the all-time max against a 2024 level failed on a series
#   that was perfectly correct.
#
#   a dealer feed does not print the interbank spike. USDCHF's famous 0.7071
#   was a momentary 2011 low; Yahoo's daily low is 0.7183 and the H.10 noon
#   rate is 0.7296. Yahoo landing between the two is right, not wrong. So the
#   band is wide enough to admit that and the DATE is what is tested tightly.
#
# (pair, max|min, level, +-days around the date, fractional tolerance, note)
SPOT = [('EURUSD', 'max', 1.6038, '2008-07-15', 5, .010, 'all-time high'),
        ('USDCHF', 'min', 0.7071, '2011-08-09', 5, .030, 'SNB-era low, spike vs feed'),
        ('USDJPY', 'max', 161.95, '2024-07-03', 5, .010, 'multi-decade high'),
        ('GBPUSD', 'min', 1.0327, '2022-09-26', 5, .020, 'mini-budget low'),
        # 0.9852 was in an earlier version of this list and is roughly where the
        # unpeg day CLOSED, not where it traded. EURCHF fell from 1.20 to the
        # mid-0.80s intraday on 2015-01-15 and different feeds print lows from
        # 0.85 down to 0.65 on that one day, which is a documented fact about
        # the day rather than a fault in any one of them. Hence the 10% band:
        # the test here is that the crash is PRESENT and correctly dated.
        ('EURCHF', 'min', 0.8500, '2015-01-15', 5, .100, 'SNB unpeg intraday low')]


def _get(u, tries=3):
    for i in range(tries):
        try:
            return urllib.request.urlopen(
                urllib.request.Request(u, headers=UA), timeout=30).read()
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(2 + 3 * i)


def yahoo_ohlc(ticker, t0, t1):
    """Daily OHLC from the v8 chart endpoint -- what yfinance wraps."""
    u = ('https://query1.finance.yahoo.com/v8/finance/chart/%s'
         '?period1=%d&period2=%d&interval=1d'
         % (urllib.parse.quote(ticker, safe=''), t0, t1))
    j = json.loads(_get(u))
    r = j['chart']['result'][0]
    q = r['indicators']['quote'][0]
    d = pd.DataFrame({k: q[k] for k in ('open', 'high', 'low', 'close', 'volume')},
                     index=pd.to_datetime(r['timestamp'], unit='s').normalize())
    d.index.name = 'date'
    # Yahoo re-sends the in-progress bar for today and duplicates some stamps;
    # the last observation for a calendar day is the settled one.
    d = d[~d.index.duplicated(keep='last')].sort_index()
    return d.dropna(subset=['open', 'high', 'low', 'close'])


def pairs():
    return list(pd.read_csv(PX, index_col=0, nrows=1).columns)


def fetch(refresh=False):
    os.makedirs(OUTDIR, exist_ok=True)
    t0 = int(pd.Timestamp(START).timestamp()); t1 = int(pd.Timestamp.now().timestamp())
    got, failed = [], []
    for p in pairs():
        f = os.path.join(OUTDIR, '%s.csv' % p)
        if os.path.exists(f) and not refresh:
            got.append(p); continue
        try:
            d = yahoo_ohlc('%s=X' % p, t0, t1)
            if len(d) < 500:
                raise ValueError('only %d bars' % len(d))
            # volume is identically zero for spot FX -- see the docstring
            d.drop(columns=['volume']).to_csv(f, float_format='%.6f')
            print('  %-7s %5d bars  %s -> %s'
                  % (p, len(d), d.index.min().date(), d.index.max().date()),
                  flush=True)
            got.append(p)
        except Exception as e:
            print('  %-7s FAILED %r' % (p, e), flush=True)
            failed.append(p)
        time.sleep(.4)
    return got, failed


CLEANDIR = os.path.join(ROOTDATA, 'ohlc_clean')


def load(p, clean=False):
    f = os.path.join(CLEANDIR if clean else OUTDIR, '%s.csv' % p)
    if not os.path.exists(f):
        return None
    return pd.read_csv(f, index_col=0, parse_dates=True)


def coverage():
    """One row per pair: span, bar count, holes, and agreement with Layer 1."""
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    rows = []
    for p in pairs():
        d = load(p)
        if d is None or not len(d):
            rows.append(dict(pair=p, ok=False)); continue
        # gaps measured in TRADING days: reindex onto the union business-day
        # calendar so a Christmas week is not read as a data failure
        bd = pd.bdate_range(d.index.min(), d.index.max())
        present = d.index.intersection(bd)
        miss = bd.difference(d.index)
        # longest consecutive run of absent business days
        longest, run, prev = 0, 0, None
        for x in miss:
            run = run + 1 if prev is not None and (x - prev).days <= 3 else 1
            longest = max(longest, run); prev = x
        # cross-source: Yahoo close vs the H.10 noon rate on shared dates. These
        # are different snapshot times so they cannot be equal; what matters is
        # that they track. A median gap above ~0.5% means the wrong ticker.
        j = pd.concat([d.close.rename('y'), px[p].rename('h')], axis=1).dropna()
        rel = ((j.y - j.h).abs() / j.h) if len(j) else pd.Series(dtype=float)
        rows.append(dict(
            pair=p, ok=True, bars=len(d),
            first=str(d.index.min().date()), last=str(d.index.max().date()),
            years=round((d.index.max() - d.index.min()).days / 365.25, 1),
            bdays=len(bd), present=len(present),
            missing_bd=len(miss), longest_gap_bd=int(longest),
            shared_with_h10=len(j),
            med_rel_diff_pct=round(100 * rel.median(), 4) if len(rel) else np.nan,
            p99_rel_diff_pct=round(100 * rel.quantile(.99), 4) if len(rel) else np.nan,
            corr_close=round(float(j.y.corr(j.h)), 6) if len(j) > 100 else np.nan))
    C = pd.DataFrame(rows)
    C['gap_over_%dbd' % GAPDAYS] = C.longest_gap_bd > GAPDAYS
    return C


def checks():
    """Structural integrity, one row per test per pair. Nothing here is fatal on
    its own -- the point is that every anomaly is COUNTED and visible."""
    rows = []
    for p in pairs():
        d = load(p)
        if d is None or not len(d):
            continue
        o, h, l, c = (d[k].values for k in ('open', 'high', 'low', 'close'))
        flat = (h == l)
        rows.append(dict(
            pair=p, bars=len(d),
            # a daily FX bar with high == low did not trade -- a feed stall
            flat_bars=int(flat.sum()),
            flat_pct=round(100 * flat.mean(), 3),
            # these are violations of what an OHLC bar MEANS, not oddities
            bad_high=int((h < np.maximum(o, c)).sum()),
            bad_low=int((l > np.minimum(o, c)).sum()),
            high_lt_low=int((h < l).sum(),),
            nonpositive=int((d[['open', 'high', 'low', 'close']].values <= 0).sum()),
            dup_dates=int(d.index.duplicated().sum()),
            # a one-day move above 10% in G8 FX is a bad print, not a market
            jump_gt_10pct=int((np.abs(np.diff(np.log(c))) > .10).sum()),
            weekend_bars=int((d.index.dayofweek >= 5).sum())))
    return pd.DataFrame(rows)


def spot_report(clean=False):
    """The extreme INSIDE the quoted window, against the quoted level."""
    rows = []
    for pair, how, level, when, days, tol, what in SPOT:
        d = load(pair, clean)
        if d is None:
            rows.append(dict(pair=pair, test=how, expected=level, got=np.nan,
                             note=what, ok=False)); continue
        t = pd.Timestamp(when); w = pd.Timedelta(days=days)
        s = d.loc[t - w:t + w]
        if not len(s):
            rows.append(dict(pair=pair, test=how, expected=level, got=np.nan,
                             note='NO BARS in window', ok=False)); continue
        got = float(s.high.max()) if how == 'max' else float(s.low.min())
        on = (s.high.idxmax() if how == 'max' else s.low.idxmin()).date()
        rel = abs(got - level) / level
        rows.append(dict(pair=pair, test=how, expected=level, got=round(got, 4),
                         window=when, on=str(on),
                         off_by_days=abs((pd.Timestamp(on) - t).days),
                         rel_pct=round(100 * rel, 3), tol_pct=100 * tol,
                         note=what, ok=bool(rel <= tol)))
    return pd.DataFrame(rows)


def main():
    argv = sys.argv[1:]
    if '--report' not in argv:
        print('FETCHING DAILY OHLC (Yahoo, 28 pairs)%s'
              % ('  --refresh' if '--refresh' in argv else ''))
        got, failed = fetch('--refresh' in argv)
        print('%d fetched/present, %d failed' % (len(got), len(failed)))
        if failed:
            print('FAILED: %s' % ', '.join(failed))

    C = coverage(); C.to_csv(COV, index=False)
    K = checks()
    S = spot_report(clean=os.path.isdir(CLEANDIR))
    K.to_csv(CHK, index=False)

    pd.set_option('display.width', 200)
    print('\nCOVERAGE (Yahoo daily OHLC vs the Layer 1 H.10 panel)')
    print(C[['pair', 'bars', 'first', 'last', 'years', 'missing_bd',
             'longest_gap_bd', 'med_rel_diff_pct', 'corr_close']]
          .to_string(index=False))
    print('\n  bars: min %d (%s), max %d (%s)'
          % (C.bars.min(), C.loc[C.bars.idxmin(), 'pair'],
             C.bars.max(), C.loc[C.bars.idxmax(), 'pair']))
    print('  start dates: %s' % C['first'].value_counts().to_dict())
    big = C[C['gap_over_%dbd' % GAPDAYS]]
    print('  pairs with a hole over %d business days: %d%s'
          % (GAPDAYS, len(big),
             (' -- ' + ', '.join('%s %d' % (r.pair, r.longest_gap_bd)
                                 for r in big.itertuples())) if len(big) else ''))
    print('  median |Yahoo - H.10| / H.10, worst pair: %.4f%% (%s)'
          % (C.med_rel_diff_pct.max(), C.loc[C.med_rel_diff_pct.idxmax(), 'pair']))

    print('\nSTRUCTURAL CHECKS (any nonzero in the last five columns is a defect)')
    print(K.to_string(index=False))
    print('\n  totals: flat bars %d, bad_high %d, bad_low %d, high<low %d, '
          'nonpositive %d, dup dates %d, >10%% jumps %d, weekend bars %d'
          % (K.flat_bars.sum(), K.bad_high.sum(), K.bad_low.sum(),
             K.high_lt_low.sum(), K.nonpositive.sum(), K.dup_dates.sum(),
             K.jump_gt_10pct.sum(), K.weekend_bars.sum()))

    print('\nSPOT CHECKS against levels quoted independently of this download'
          '%s' % ('  [on the CLEAN set]' if os.path.isdir(CLEANDIR) else ''))
    print(S.to_string(index=False))
    print('\nwrote data/ohlc/<PAIR>.csv, l2_ohlc_coverage.csv, l2_ohlc_checks.csv')
    return C, K, S


if __name__ == '__main__':
    main()
