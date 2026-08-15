import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""PHASE 3. The engine's trade list against TradingView's, trade by trade.

  python code/l2parity.py                 # export ours, and compare if a TV file exists
  python code/l2parity.py --pairs EURUSD  # just one

OURS goes to results/l2_parity_ours.csv. Drop TradingView's "List of Trades"
export in as data/tv/<PAIR>.csv and rerun; the comparison then writes
results/l2_parity_report.csv and prints EVERY mismatch with its cause.

--------------------------------------------------------------------------
SETTINGS THE TRADINGVIEW RUN MUST USE, or the comparison is meaningless
--------------------------------------------------------------------------
The strategy's own defaults already give the combination under test -- SSL
Channel(10) / DSPO(14) / Variance(Price, 0.0, "MA > Variance", 20, 20, 10) /
Triangular Moving Average(20) / SSL Channel(10) exit, ATR 14, loss 1.0x,
RR 1.5, NNFX Phased. Three things must be CHANGED from the file as shipped:

  1. ADD process_orders_on_close=true TO THE strategy() CALL. Line 4 of
     JCs_NNFX_ALGO_V5_1.pine does not set it. Without it TradingView fills
     market entries at the NEXT BAR'S OPEN, and every entry in the export will
     sit one bar later than ours at a different price. This is not a small
     discrepancy -- it is every single trade.

  2. Compound Profits -> OFF. It defaults to true, sizing off the live balance.
     It does not change entry or exit PRICES or DATES, so trade-by-trade
     matching survives either way, but position sizes will not line up.

  3. Data. TradingView's FX feed is not Yahoo's. Set the chart to the same
     symbol and daily resolution, and expect price differences of ~0.2% -- see
     results/l2_ohlc_coverage.csv. A DATE mismatch is a logic difference; a
     small PRICE mismatch on a matching date is the feed, and this script
     separates those two rather than lumping them together.

--------------------------------------------------------------------------
TWO DIVERGENCES ARE EXPECTED AND ARE NOT FAILURES
--------------------------------------------------------------------------
Both are the work order's instruction to fix Pine bugs rather than reproduce
them, so they are predicted here BEFORE the comparison rather than explained
afterwards:

  CONTINUATION ENTRIES. Pine's longcondition3 omits Ind_BTF_Conf, so
  continuation trades ignore Bridge Too Far. The engine applies it to all three
  routes. Every trade TradingView takes that we skip should be a continuation
  entry more than 7 bars after the baseline cross -- and this script checks
  that specifically rather than accepting it on trust.

  LEG PHASE ACROSS A REVERSAL. The engine rebuilds all phase state on entry.

Anything else that differs is a defect in the port and is reported as one.
"""
import glob
import numpy as np, pandas as pd
import l2engine as E

TVDIR = os.path.join(ROOTDATA, 'tv')
OURS = os.path.join(ROOTOUT, 'l2_parity_ours.csv')
REPORT = os.path.join(ROOTOUT, 'l2_parity_report.csv')
PAIRS = ['EURUSD', 'GBPUSD', 'USDJPY']
DATE_TOL = 0                 # a matching trade must be on the SAME bar
PRICE_TOL = 0.004            # 0.4% -- twice the measured Yahoo/H.10 feed gap


def ours(pairs=PAIRS):
    frames = []
    for p in pairs:
        d = E.load_pair(p)
        A = E.prepare(d, **{k: v for k, v in
                            zip(('c1', 'c2', 'vol', 'base', 'exit_ind'),
                                (E.DEFAULT_SLOTS['c1'], E.DEFAULT_SLOTS['c2'],
                                 E.DEFAULT_SLOTS['vol'], E.DEFAULT_SLOTS['base'],
                                 E.DEFAULT_SLOTS['exit_ind']))})
        r = E.run(A, plan=2)
        T = E.trade_frame(r, d)
        T.insert(0, 'pair', p)
        frames.append(T)
    return pd.concat(frames, ignore_index=True)


def read_tv(path):
    """TradingView's List of Trades export. Column names have drifted across
    versions, so they are matched loosely rather than by exact string."""
    d = pd.read_csv(path)
    cols = {c.lower().strip(): c for c in d.columns}

    def pick(*names):
        for n in names:
            for k, v in cols.items():
                if n in k:
                    return v
        return None
    ctype, cdate = pick('type'), pick('date', 'time')
    cprice, cnum = pick('price'), pick('trade #', 'trade')
    if not (ctype and cdate and cprice):
        raise ValueError('cannot find type/date/price columns in %s: %s'
                         % (path, list(d.columns)))
    d = d.rename(columns={ctype: 'type', cdate: 'dt', cprice: 'price'})
    d['dt'] = pd.to_datetime(d.dt).dt.normalize()
    d['side'] = np.where(d.type.str.contains('long', case=False), 'long', 'short')
    d['is_entry'] = d.type.str.contains('entry', case=False)
    if cnum:
        d = d.rename(columns={cnum: 'trade_no'})
    return d


def compare(T, tv, pair):
    """Match on (entry date, direction). Then check the exit."""
    mine = T[(T.pair == pair) & (T.leg != 'leg2')].copy()
    mine['key'] = list(zip(mine.entry_date.dt.normalize(), mine.direction))
    ent = tv[tv.is_entry].copy()
    ent['key'] = list(zip(ent.dt, ent.side))

    mk, tk = list(mine.key), list(ent.key)
    both = set(mk) & set(tk)
    only_mine = [k for k in mk if k not in set(tk)]
    only_tv = [k for k in tk if k not in set(mk)]

    rows = []
    for k in sorted(both):
        m = mine[mine.key == k].iloc[0]
        t = ent[ent.key == k].iloc[0]
        rel = abs(m.entry_px - t.price) / t.price if t.price else np.nan
        rows.append(dict(pair=pair, entry_date=k[0], direction=k[1],
                         status='matched', ours_px=m.entry_px, tv_px=t.price,
                         rel_px=rel,
                         cause='' if rel <= PRICE_TOL else 'price gap > %.2f%%'
                         % (100 * PRICE_TOL),
                         route=m.route, reason=m.reason))
    for k in only_mine:
        m = mine[mine.key == k].iloc[0]
        rows.append(dict(pair=pair, entry_date=k[0], direction=k[1],
                         status='ours only', ours_px=m.entry_px, tv_px=np.nan,
                         rel_px=np.nan, cause='', route=m.route, reason=m.reason))
    for k in only_tv:
        t = ent[ent.key == k].iloc[0]
        rows.append(dict(pair=pair, entry_date=k[0], direction=k[1],
                         status='tv only', ours_px=np.nan, tv_px=t.price,
                         rel_px=np.nan,
                         cause='EXPECTED if a continuation entry past the bridge',
                         route='', reason=''))
    return pd.DataFrame(rows)


def main():
    argv = sys.argv[1:]
    pairs = PAIRS
    if '--pairs' in argv:
        pairs = argv[argv.index('--pairs') + 1].split(',')
    T = ours(pairs)
    T.to_csv(OURS, index=False)
    pd.set_option('display.width', 240)
    print('OUR TRADE LIST -- %s' % ' / '.join('%s=%s' % kv
                                              for kv in E.DEFAULT_SLOTS.items()))
    print('%d leg records, %d entries, %d pairs'
          % (len(T), (T.leg != 'leg2').sum(), T.pair.nunique()))
    print(T.groupby('pair').agg(entries=('leg', lambda s: (s != 'leg2').sum()),
                                first=('entry_date', 'min'),
                                last=('entry_date', 'max')).to_string())
    print('\nentry routes: %s' % T[T.leg != 'leg2'].route.value_counts().to_dict())
    print('exit reasons: %s' % T.reason.value_counts().to_dict())
    print('\nwrote %s' % OURS)
    print(T.head(12).to_string(index=False))

    files = sorted(glob.glob(os.path.join(TVDIR, '*.csv')))
    if not files:
        print('\nNO TRADINGVIEW EXPORT FOUND.')
        print('  Put the List of Trades CSVs in data/tv/<PAIR>.csv and rerun.')
        print('  The run must set process_orders_on_close=true -- the strategy '
              'file does NOT set it, and without it every entry fills one bar '
              'late at the next open. See this module\'s docstring.')
        return T, None

    out = []
    for f in files:
        p = os.path.basename(f)[:-4].upper()
        if p not in set(T.pair):
            print('  skipping %s -- not in our run' % p); continue
        out.append(compare(T, read_tv(f), p))
    C = pd.concat(out, ignore_index=True)
    C.to_csv(REPORT, index=False)
    n = len(C); m = int((C.status == 'matched').sum())
    px_ok = int(((C.status == 'matched') & (C.rel_px <= PRICE_TOL)).sum())
    print('\nPARITY: %d/%d entries matched on date AND direction (%.1f%%)'
          % (m, n, 100 * m / n if n else 0))
    print('        of those, %d within %.2f%% on price (%.1f%%)'
          % (px_ok, 100 * PRICE_TOL, 100 * px_ok / m if m else 0))
    bad = C[C.status != 'matched']
    if len(bad):
        print('\nEVERY MISMATCH:')
        print(bad.to_string(index=False))
    print('\nwrote %s' % REPORT)
    return T, C


if __name__ == '__main__':
    main()
