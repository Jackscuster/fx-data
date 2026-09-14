import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""ENTRY COST, MEASURED: the OANDA hourly bid/ask, 2004-05-31 on, every hour
17:00-23:00 New York, per pair, majors vs crosses, by era.

  python3 code/l2spread.py --fetch     # H1 bid + ask for 28 pairs -> data/oanda_h1 (resumable)
  python3 code/l2spread.py             # measure + reconcile

THE SPREAD AT TIME T IS THE CANDLE LABELLED T-1: an H1 candle labelled hour h
closes at h+1, so the ask-bid at its close is the spread AT h+1 (the check that
caught the opposite reading was a nonzero 'drift' at the reference hour
itself; see l2entrytime.py). Reported in pips and in basis points of price,
round trip = ask - bid (one crossing pays the whole spread).

RECONCILIATION. Three numbers claimed to be the entry cost:
  cost_table.csv       published ThinkMarkets spreads x1.5 markup (crosses
                       'derived' as 2x the widest major), crisis x2
  entry_timing.csv     OANDA H1 at 19:00 NY, spread + adverse drift, on 15
                       graft members' entries, 2004-2015 and 2016-2026
  this file            OANDA H1 ask-bid at each hour, every bar, every pair
The engine charges cost_table. Whichever is right, the cost is what the
account will actually pay at the entry hour on the venue it trades -- that is
the measured OANDA spread here, and the table is right only where it matches it.
"""
import argparse, json, time, urllib.request, urllib.parse
import numpy as np, pandas as pd
import l2oanda as OA

H1 = os.path.join(ROOTDATA, 'oanda_h1'); os.makedirs(H1, exist_ok=True)
NY = 'America/New_York'
MAJORS = {'EURUSD', 'GBPUSD', 'AUDUSD', 'NZDUSD', 'USDCAD', 'USDCHF', 'USDJPY'}
HOURS = list(range(17, 24))
START = '2004-05-31'


def fetch_h1(inst, price, tok):
    rows, cursor, seen = [], pd.Timestamp(START, tz='UTC'), set()
    while True:
        q = urllib.parse.urlencode({'granularity': 'H1', 'price': price, 'count': OA.MAXCOUNT,
                                    'from': cursor.strftime('%Y-%m-%dT%H:%M:%SZ')})
        j = OA._get('%s/v3/instruments/%s/candles?%s' % (OA.HOST, inst, q), tok)
        cs = [c for c in j.get('candles', []) if c.get('complete')]
        if not cs:
            break
        new = 0
        for c in cs:
            t = c['time']
            if t in seen:
                continue
            seen.add(t); new += 1
            p = c['bid' if price == 'B' else 'ask']
            rows.append((t, float(p['o']), float(p['h']), float(p['l']), float(p['c'])))
        last = pd.Timestamp(cs[-1]['time'])
        if new == 0 or last <= cursor:
            break
        cursor = last + pd.Timedelta(seconds=1)
    d = pd.DataFrame(rows, columns=['time', 'o', 'h', 'l', 'c'])
    d['time'] = pd.to_datetime(d.time, utc=True)
    return d


def do_fetch():
    tok = OA.token()
    for pair, inst in OA.PAIRS.items():
        for price, tag in (('B', 'bid'), ('A', 'ask')):
            f = os.path.join(H1, '%s_%s.csv' % (pair, tag))
            if os.path.exists(f) and os.path.getsize(f) > 1000:
                continue
            t0 = time.time()
            d = fetch_h1(inst, price, tok)
            d.to_csv(f, index=False)
            print('  %s %s: %d candles %s -> %s  (%.0fs)' % (pair, tag, len(d), d.time.min().date() if len(d) else '-', d.time.max().date() if len(d) else '-', time.time() - t0), flush=True)


def measure():
    rows = []
    for pair in OA.PAIRS:
        fb, fa = os.path.join(H1, '%s_bid.csv' % pair), os.path.join(H1, '%s_ask.csv' % pair)
        if not (os.path.exists(fb) and os.path.getsize(fb) > 1000 and os.path.exists(fa) and os.path.getsize(fa) > 1000):
            print('  %s: no hourly data' % pair, flush=True); continue
        b = pd.read_csv(fb, parse_dates=['time']); a = pd.read_csv(fa, parse_dates=['time'])
        m = b[['time', 'c']].merge(a[['time', 'c']], on='time', suffixes=('_bid', '_ask'))
        m['ny'] = m.time.dt.tz_convert(NY); m['hour_at'] = (m.ny.dt.hour + 1) % 24   # the candle labelled h gives the price AT h+1
        m['spread'] = m.c_ask - m.c_bid; m['mid'] = (m.c_ask + m.c_bid) / 2
        m['year'] = m.ny.dt.year
        pp = 0.01 if pair.endswith('JPY') else 0.0001
        m = m[m.hour_at.isin(HOURS) & (m.ny.dt.weekday < 5)]
        m['era'] = np.where(m.year <= 2015, '2004-2015', np.where(m.year <= 2020, '2016-2020', '2021-2026'))
        for (era, h), g in m.groupby(['era', 'hour_at']):
            rows.append(dict(pair=pair, group='major' if pair in MAJORS else 'cross', era=era, hour_ny=h, n=len(g),
                             spread_pips_median=g.spread.median() / pp, spread_pips_mean=g.spread.mean() / pp,
                             spread_bp_median=1e4 * (g.spread / g.mid).median(), spread_bp_p90=1e4 * (g.spread / g.mid).quantile(.9)))
    O = pd.DataFrame(rows); O.to_csv(os.path.join(ROOTOUT, 'spread_by_hour.csv'), index=False)
    return O


def reconcile(O):
    tab = pd.read_csv(os.path.join(ROOTOUT, 'cost_table.csv')).set_index('pair')
    et = pd.read_csv(os.path.join(ROOTOUT, 'entry_timing.csv'))
    pd.set_option('display.width', 220)
    print('\n=== measured OANDA spread, median pips, by hour NY (2016-2020) ===', flush=True)
    piv = O[O.era == '2016-2020'].pivot_table(index='group', columns='hour_ny', values='spread_pips_median', aggfunc='median')
    print(piv.to_string(float_format=lambda v: '%6.2f' % v), flush=True)
    print('\n=== by era, at 17:00 and 19:00 (median pips over pairs) ===', flush=True)
    print(O[O.hour_ny.isin([17, 19])].pivot_table(index=['group', 'hour_ny'], columns='era', values='spread_pips_median', aggfunc='median').to_string(float_format=lambda v: '%6.2f' % v), flush=True)
    best = O[O.era == '2016-2020'].groupby('hour_ny').spread_bp_median.median().idxmin()
    print('\n  cheapest hour 2016-2020 (median bp over pairs): %02d:00 NY' % best, flush=True)
    # per pair: table vs measured at 17:00 and 19:00
    rows = []
    for p in tab.index:
        q = O[(O.pair == p) & (O.era == '2016-2020')].set_index('hour_ny')
        if not len(q): continue
        rows.append(dict(pair=p, group='major' if p in MAJORS else 'cross', table_raw_pips=tab.raw_spread_pips[p], table_marked_up_pips=tab.marked_up_pips[p],
                         oanda_17_pips=q.spread_pips_median.get(17, np.nan), oanda_19_pips=q.spread_pips_median.get(19, np.nan), oanda_best_pips=q.spread_pips_median.min(), oanda_best_hour=int(q.spread_pips_median.idxmin())))
    R = pd.DataFrame(rows); R.to_csv(os.path.join(ROOTOUT, 'spread_reconciliation.csv'), index=False)
    print('\n=== per pair: cost_table vs measured OANDA (2016-2020, median pips) ===', flush=True)
    print(R.to_string(index=False, float_format=lambda v: '%6.2f' % v), flush=True)
    e19 = et[(et.entry_time.str.startswith('19:00')) & (et.period.str.startswith('OOS'))].set_index('group')
    print('\n  entry_timing.csv at 19:00 (OOS 2016-2026): spread pips %s, total incl. drift %s' % (e19.spread_pips.round(2).to_dict(), e19.total_cost_pips.round(2).to_dict()), flush=True)
    g = R.groupby('group')[['table_raw_pips', 'table_marked_up_pips', 'oanda_17_pips', 'oanda_19_pips', 'oanda_best_pips']].median()
    print('\n=== group medians ===', flush=True); print(g.to_string(float_format=lambda v: '%6.2f' % v), flush=True)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--fetch', action='store_true'); a = ap.parse_args()
    t0 = time.time()
    if a.fetch:
        do_fetch(); print('fetch done in %.1f min' % ((time.time() - t0) / 60), flush=True)
    O = measure(); reconcile(O)
    print('done in %.1f min' % ((time.time() - t0) / 60), flush=True)


if __name__ == '__main__':
    main()
