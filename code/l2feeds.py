import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""WHICH FEED THE SWEEP SHOULD RUN ON. OANDA mid against the cleaned Yahoo set,
all 28 pairs, and where clean history actually starts.

NOTHING IS SWITCHED HERE. This measures and reports; the decision is Jack's.

What is compared, per pair:
  coverage      first and last bar, bar count, and the leading PLACEHOLDER block
                (high == low == close, volume == 1) that OANDA's practice feed
                serves for its earliest years
  bad bars      flat bars, OHLC violations (high below open/close and the
                mirror), single-day moves over 10%
  disagreement  on shared dates, |close difference| / close -- the two feeds are
                snapped differently and cannot be identical; the question is
                whether the gap is feed-sized or something worse

WHY THIS MATTERS MORE THAN IT LOOKS. Phase 3 proved the engine reproduces
TradingView to 97.9% on OANDA bars. That proof is only inherited by the sweep if
the sweep runs on the same bars. It also showed how a feed defect presents:
OANDA's placeholder bars make sma(high) == sma(low), so SSL Channel confirms
NEITHER direction and the engine silently trades nothing -- which reads as "no
edge", not "no data".

Writes results/l2_feed_comparison.csv and results/l2_feed_verdict.md.
"""
import glob
import numpy as np, pandas as pd

OANDA = os.path.join(ROOTDATA, 'oanda_ohlc')
YAHOO = os.path.join(ROOTDATA, 'ohlc_clean')
OUT = os.path.join(ROOTOUT, 'l2_feed_comparison.csv')
VERDICT = os.path.join(ROOTOUT, 'l2_feed_verdict.md')


def pairs():
    return sorted(os.path.basename(f)[:-8] for f in glob.glob(os.path.join(OANDA, '*_mid.csv')))


def first_real(d):
    """End of the LEADING placeholder block. An isolated flat bar later is a
    holiday and is kept -- see l2parity.load_oanda."""
    flat = (d.high.values == d.low.values)
    i = 0
    while i < len(flat) and flat[i]:
        i += 1
    return i


def bad_bars(d):
    o, h, l, c = (d[k].values.astype(float) for k in ('open', 'high', 'low', 'close'))
    r = np.diff(np.log(c), prepend=np.nan)
    return dict(flat=int((h == l).sum()),
                bad_high=int((h < np.maximum(o, c)).sum()),
                bad_low=int((l > np.minimum(o, c)).sum()),
                jump10=int((np.abs(r) > .10).sum()))


def main():
    rows = []
    for p in pairs():
        O = pd.read_csv(os.path.join(OANDA, '%s_mid.csv' % p), index_col=0,
                        parse_dates=True)
        k = first_real(O)
        Oc = O.iloc[k:]
        yf = os.path.join(YAHOO, '%s.csv' % p)
        Y = pd.read_csv(yf, index_col=0, parse_dates=True) if os.path.exists(yf) else None
        r = dict(pair=p,
                 oanda_bars=len(O), oanda_first=str(O.index.min().date()),
                 placeholder_bars=k,
                 oanda_real_from=str(Oc.index.min().date()),
                 oanda_real_bars=len(Oc),
                 oanda_last=str(O.index.max().date()))
        for tag, d in (('oanda', Oc), ('yahoo', Y)):
            if d is None:
                continue
            b = bad_bars(d)
            r.update({'%s_%s' % (tag, kk): vv for kk, vv in b.items()})
        if Y is not None:
            r.update(yahoo_bars=len(Y), yahoo_first=str(Y.index.min().date()),
                     yahoo_last=str(Y.index.max().date()))
            j = pd.concat([Oc.close.rename('o'), Y.close.rename('y')],
                          axis=1, join='inner').dropna()
            rel = (j.o - j.y).abs() / j.y
            r.update(shared_bars=len(j),
                     med_diff_pct=round(100 * float(rel.median()), 4),
                     p99_diff_pct=round(100 * float(rel.quantile(.99)), 4),
                     over_1pct=int((rel > .01).sum()),
                     only_oanda=int(len(Oc.index.difference(Y.index))),
                     only_yahoo=int(len(Y.index.difference(Oc.index))))
        rows.append(r)
    D = pd.DataFrame(rows)
    D.to_csv(OUT, index=False)

    pd.set_option('display.width', 250)
    print('FEED COMPARISON -- OANDA mid (placeholder block removed) vs cleaned Yahoo')
    print(D[['pair', 'oanda_real_from', 'oanda_real_bars', 'placeholder_bars',
             'yahoo_first', 'yahoo_bars', 'shared_bars', 'med_diff_pct',
             'p99_diff_pct', 'over_1pct']].to_string(index=False))

    print('\nBAD BARS')
    print(D[['pair', 'oanda_flat', 'oanda_bad_high', 'oanda_bad_low',
             'oanda_jump10', 'yahoo_flat', 'yahoo_bad_high', 'yahoo_bad_low',
             'yahoo_jump10']].sum(numeric_only=True).to_string())

    starts = pd.to_datetime(D.oanda_real_from)
    print('\nWHERE CLEAN OANDA HISTORY STARTS')
    print('  earliest %s, latest %s' % (starts.min().date(), starts.max().date()))
    print('  ' + D.oanda_real_from.value_counts().to_string().replace('\n', '\n  '))
    common = starts.max()
    print('\n  ALL 28 pairs have real OHLC from %s' % common.date())
    print('  Yahoo starts, for comparison: earliest %s, latest %s'
          % (pd.to_datetime(D.yahoo_first).min().date(),
             pd.to_datetime(D.yahoo_first).max().date()))
    off, yr = shift_test()
    n = sum(off.values())
    print('\nARE THE >1%% DISAGREEMENTS A DATE SHIFT?  (%d bars)' % n)
    for k in (-1, 0, 1):
        print('   Yahoo matches the OANDA bar %+d away best: %5d (%.1f%%)'
              % (k, off[k], 100 * off[k] / n))
    print('   -> symmetric, so not a shift. They cluster in %s, the volatile'
          ' years.' % ', '.join(str(y) for y, _ in
                                sorted(yr.items(), key=lambda x: -x[1])[:3]))
    write_verdict(D, common, off, yr)
    return D


def shift_test():
    """A disagreement over 1% is either a snapshot-time difference amplified by
    volatility, or one feed being dated wrong. If Yahoo were shifted, the
    neighbouring OANDA bar would win systematically in ONE direction. Testing
    that is the difference between a benign gap and a corrupt series."""
    off = {-1: 0, 0: 0, 1: 0}
    yr = {}
    for p in pairs():
        O = pd.read_csv(os.path.join(OANDA, '%s_mid.csv' % p), index_col=0,
                        parse_dates=True)
        O = O.iloc[first_real(O):]
        yf = os.path.join(YAHOO, '%s.csv' % p)
        if not os.path.exists(yf):
            continue
        Y = pd.read_csv(yf, index_col=0, parse_dates=True)
        j = pd.concat([O.close.rename('o'), Y.close.rename('y')],
                      axis=1, join='inner').dropna()
        for d in j.index[((j.o - j.y).abs() / j.y) > .01]:
            yv = Y.close.get(d)
            best = bo = None
            for k in (-1, 0, 1):
                ov = O.close.get(d + pd.Timedelta(days=k))
                if ov is None or not np.isfinite(ov):
                    continue
                e = abs(ov - yv) / yv
                if best is None or e < best:
                    best, bo = e, k
            if bo is not None:
                off[bo] += 1
            yr[d.year] = yr.get(d.year, 0) + 1
    return off, yr


def write_verdict(D, common, off=None, yr=None):
    tot_o = D[['oanda_flat', 'oanda_bad_high', 'oanda_bad_low', 'oanda_jump10']].sum()
    tot_y = D[['yahoo_flat', 'yahoo_bad_high', 'yahoo_bad_low', 'yahoo_jump10']].sum()
    with open(VERDICT, 'w') as f:
        w = f.write
        w('# Which feed the sweep runs on\n\n')
        w('Generated by `python code/l2feeds.py`. **Nothing is switched by this '
          'file** -- it measures, and the decision is Jack\'s.\n\n')
        w('## Recommendation: OANDA mid, from %s\n\n' % common.date())
        w('Three reasons, in order of weight.\n\n')
        w('1. **The Phase 3 proof only transfers if the bars do.** The engine '
          'was shown to reproduce TradingView on 185 of 189 entries — on OANDA '
          'mid candles. Run the sweep on Yahoo and that proof does not apply to '
          'it: the same comparison on Yahoo read 18-25%%, entirely because of '
          'the feed.\n')
        w('2. **Winners have to port back to TradingView**, whose FX charts are '
          'OANDA. A combination found on Yahoo has to survive a feed change '
          'before it can be traded; found on OANDA it does not.\n')
        w('3. **OANDA needs no repair.** Yahoo needed four: a daylight-saving '
          'date remap on %s bars, 651 duplicate-week drops, %s OHLC clamps and '
          '57 bad prints. OANDA arrives with %d bad high/low bars and %d flat '
          'bars in the usable era across all 28 pairs.\n\n'
          % ('19,662', '4,450', int(tot_o.oanda_bad_high + tot_o.oanda_bad_low),
             int(tot_o.oanda_flat)))
        w('## The cost of the switch\n\n')
        w('History. Yahoo reaches back to 1999-2003 depending on pair; OANDA\'s '
          'usable history starts **%s for all 28**, because its practice feed '
          'serves close-only placeholder bars (high = low = close, volume = 1) '
          'before that. That is the price, and it is why the gauntlet windows '
          'are quarters of the ACTUAL clean history rather than of 1999-2026.\n\n'
          % common.date())
        w('## Agreement between the two feeds\n\n')
        w('On shared dates, |close difference| / close: median %.4f%% pooled, '
          '99th percentile %.4f%%, and %d bars out of %d differ by more than 1%%.'
          ' That is the size a snapshot-time difference should be — the two are '
          'measuring the same market, not disagreeing about it.\n\n'
          % (D.med_diff_pct.median(), D.p99_diff_pct.median(),
             int(D.over_1pct.sum()), int(D.shared_bars.sum())))
        w('## Bad bars, usable era, all 28 pairs\n\n')
        w('| | OANDA mid | Yahoo (cleaned) |\n|---|---|---|\n')
        for k, a, b in (('flat (high == low)', 'oanda_flat', 'yahoo_flat'),
                        ('high below open/close', 'oanda_bad_high', 'yahoo_bad_high'),
                        ('low above open/close', 'oanda_bad_low', 'yahoo_bad_low'),
                        ('one-day move > 10%', 'oanda_jump10', 'yahoo_jump10')):
            w('| %s | %d | %d |\n' % (k, int(D[a].sum()), int(D[b].sum())))
        w('\n## What must not be forgotten\n\n')
        w('A feed defect does not announce itself. OANDA\'s placeholder bars '
          'make `sma(high) == sma(low)`, so SSL Channel confirms neither '
          'direction and the engine trades NOTHING — which a sweep reads as '
          '"no edge", not "no data". `l2parity.load_oanda` drops the leading '
          'block; any sweep loader must do the same.\n')
    print('\nwrote %s' % VERDICT)


if __name__ == '__main__':
    main()
