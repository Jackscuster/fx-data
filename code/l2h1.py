import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""HOURLY OANDA CANDLES, BID AND ASK, for the execution studies.

Bid and ask are fetched separately rather than mid, because the spread IS the
measurement in study A -- a mid series cannot show what an entry costs.

THE TOKEN IS NEVER PRINTED OR COMMITTED. It comes from .oanda_token (mode 600,
gitignored) via l2oanda.token(). data/oanda_h1/ is gitignored for size.

RESUMABLE PER PAIR AND PRICE. Each (pair, price) writes its own CSV and is
skipped if the file already exists, so an interrupted fetch costs one file.
"""
import time, json, urllib.parse
import numpy as np, pandas as pd
import l2oanda as O

OUT = os.path.join(ROOTDATA, 'oanda_h1')
os.makedirs(OUT, exist_ok=True)
START = '2002-01-01'
MAXCOUNT = 5000


def fetch_h1(inst, price_key, tok):
    """price_key: 'bid' or 'ask'. Walks forward in <=5000-candle pages."""
    code = {'bid': 'B', 'ask': 'A'}[price_key]
    rows, cursor, seen = [], pd.Timestamp(START, tz='UTC'), set()
    while True:
        q = urllib.parse.urlencode({
            'granularity': 'H1', 'price': code, 'count': MAXCOUNT,
            'from': cursor.strftime('%Y-%m-%dT%H:%M:%SZ')})
        j = O._get('%s/v3/instruments/%s/candles?%s' % (O.HOST, inst, q), tok)
        cs = [c for c in j.get('candles', []) if c.get('complete')]
        if not cs:
            break
        new = 0
        for c in cs:
            t = c['time']
            if t in seen:
                continue
            seen.add(t); new += 1
            p = c[price_key]
            rows.append((t, float(p['o']), float(p['h']), float(p['l']),
                         float(p['c']), int(c.get('volume', 0))))
        last = pd.Timestamp(cs[-1]['time'])
        if new == 0 or last <= cursor:
            break
        cursor = last + pd.Timedelta(seconds=1)
    d = pd.DataFrame(rows, columns=['time', 'o', 'h', 'l', 'c', 'v'])
    if len(d):
        d['time'] = pd.to_datetime(d.time, utc=True)
        d = d.drop_duplicates('time').sort_values('time')
    return d


def main():
    tok = O.token()
    pairs = O.PAIRS if hasattr(O, 'PAIRS') else None
    if not pairs:
        import l2sweep as S
        pairs = {p: p[:3] + '_' + p[3:] for p in S.all_pairs()}
    t0 = time.time(); done = 0
    todo = [(p, inst, k) for p, inst in sorted(pairs.items()) for k in ('bid', 'ask')
            if not os.path.exists(os.path.join(OUT, '%s_%s.csv' % (p, k)))]
    print('H1 fetch: %d (pair,price) files to get' % len(todo), flush=True)
    for p, inst, k in todo:
        f = os.path.join(OUT, '%s_%s.csv' % (p, k))
        try:
            d = fetch_h1(inst, k, tok)
        except Exception as e:
            print('  %s %s FAILED: %s' % (p, k, str(e)[:90]), flush=True); continue
        if not len(d):
            print('  %s %s: no data' % (p, k), flush=True); continue
        d.to_csv(f, index=False)
        done += 1
        el = time.time() - t0
        print('  %s %s: %d bars %s..%s | %d/%d, %.1f min elapsed, ~%.0f min left'
              % (p, k, len(d), str(d.time.iloc[0])[:10], str(d.time.iloc[-1])[:10],
                 done, len(todo), el / 60, (el / done) * (len(todo) - done) / 60),
              flush=True)
    print('DONE in %.1f min' % ((time.time() - t0) / 60), flush=True)


if __name__ == '__main__':
    main()
