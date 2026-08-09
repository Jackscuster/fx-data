import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""First non-price data in the project. Fetch only -- no signals are built here.

Everything upstream is FX closes predicting their own future shape. This pulls the
outside world so extsig.py can run the SURVIVING constructions over it unchanged.

ALIGNMENT, and the two ways this silently goes wrong
  US markets, commodity pits and the FX fixing keep different calendars. Every
  series is reindexed onto the px28 index and FORWARD-FILLED ONLY. A backfill
  would put Tuesday's VIX on Monday, which is a look-ahead that no amount of
  .shift(1) downstream can undo.

  Nothing is padded or interpolated at the front either. ^MOVE and ^VVIX start
  years after 1999; those rows stay NaN and the minimum-observation rule in the
  scorer decides what is usable. Inventing history to fill them would manufacture
  exactly the quiet early regime the duration constructions key on.

FRED IS NOT REACHABLE from every environment. fred.stlouisfed.org refuses the
connection from the dev sandbox while every other host resolves, so the rate
differentials -- the carry, and the reason this task exists -- cannot be built
there. The fetcher is written anyway and probes each series id, recording what
resolved in ext_coverage.csv, so a run with FRED access fills the gap without
any code change. Series ids below are UNVERIFIED against the live service; treat
a missing row in the coverage file as "not confirmed", never as "no such data".

Writes data/ext.csv (px28 index x series) and results/ext_coverage.csv.
"""
import io, json, time, urllib.request, urllib.parse, urllib.error
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
OUTF = os.path.join(ROOTDATA, 'ext.csv')
COV = os.path.join(ROOTOUT, 'ext_coverage.csv')
UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}

# group is carried through to the scorer so retention can be reported by source
YAHOO = [
    ('^VIX',      'equity-vol'),   ('^VIX3M',  'equity-vol'),
    ('^VVIX',     'equity-vol'),   ('^MOVE',   'rates-vol'),
    ('HYG',       'credit'),       ('LQD',     'credit'),
    ('TLT',       'bonds'),        ('SHY',     'bonds'),
    ('IEF',       'bonds'),
    ('CL=F',      'commodities'),  ('GC=F',    'commodities'),
    ('SI=F',      'commodities'),
    ('^TNX',      'us-yields'),    ('^FVX',    'us-yields'),
    ('^IRX',      'us-yields'),
    ('DX-Y.NYB',  'dollar'),
]

# Ratios the brief calls for by name. Built here rather than in the signal layer
# so the constructions see them as plain series like everything else.
RATIOS = [('HYG_LQD', 'HYG', 'LQD', 'credit'),      # credit stress
          ('TLT_SHY', 'TLT', 'SHY', 'bonds'),       # curve slope
          ('VIX_TS',  '^VIX3M', '^VIX', 'equity-vol')]   # vol term structure

# 2-year government yields, one per G8 currency. IDs UNVERIFIED -- see docstring.
FRED = {'USD': 'DGS2', 'EUR': 'IRLTLT01EZM156N', 'JPY': 'IRLTLT01JPM156N',
        'GBP': 'IRLTLT01GBM156N', 'CAD': 'IRLTLT01CAM156N',
        'AUD': 'IRLTLT01AUM156N', 'NZD': 'IRLTLT01NZM156N',
        'CHF': 'IRLTLT01CHM156N'}


def _get(url, timeout=30, tries=3):
    last = None
    for i in range(tries):
        try:
            return urllib.request.urlopen(
                urllib.request.Request(url, headers=UA), timeout=timeout).read()
        except Exception as e:                       # noqa: BLE001 - reported, not raised
            last = e
            time.sleep(1.5 * (i + 1))
    raise last


def yahoo(ticker, t0, t1):
    """Daily closes. The v8 chart endpoint, which is what yfinance wraps."""
    u = ('https://query1.finance.yahoo.com/v8/finance/chart/%s'
         '?period1=%d&period2=%d&interval=1d'
         % (urllib.parse.quote(ticker, safe=''), t0, t1))
    j = json.loads(_get(u))
    r = j['chart']['result'][0]
    q = r['indicators']['quote'][0]
    s = pd.Series(q['close'],
                  index=pd.to_datetime(r['timestamp'], unit='s').normalize())
    # Yahoo returns the in-progress bar for today and duplicate stamps on some
    # futures rolls; keep the last observation per calendar day.
    return s[~s.index.duplicated(keep='last')].dropna().sort_index()


def fred(sid):
    u = 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=%s' % sid
    d = pd.read_csv(io.BytesIO(_get(u)))
    d.columns = ['date', 'v']
    d['v'] = pd.to_numeric(d.v, errors='coerce')
    return (d.assign(date=pd.to_datetime(d.date)).set_index('date').v.dropna())


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    idx = px.index
    t0 = int(pd.Timestamp('1998-06-01').timestamp())
    t1 = int(pd.Timestamp.now().timestamp())
    raw, rows = {}, []

    for tk, grp in YAHOO:
        try:
            s = yahoo(tk, t0, t1)
            raw[tk] = s
            rows.append(dict(series=tk, source='yahoo', group=grp, ok=True,
                             first=str(s.index.min().date()),
                             last=str(s.index.max().date()), n_raw=len(s), note=''))
            print('  %-10s %5d bars  %s .. %s'
                  % (tk, len(s), s.index.min().date(), s.index.max().date()), flush=True)
        except Exception as e:                       # noqa: BLE001
            rows.append(dict(series=tk, source='yahoo', group=grp, ok=False,
                             first='', last='', n_raw=0, note=type(e).__name__))
            print('  %-10s FAILED %s' % (tk, e), flush=True)

    for name, a, b, grp in RATIOS:
        if a in raw and b in raw:
            r = (raw[a] / raw[b]).dropna()
            raw[name] = r
            rows.append(dict(series=name, source='derived', group=grp, ok=True,
                             first=str(r.index.min().date()),
                             last=str(r.index.max().date()), n_raw=len(r),
                             note='%s / %s' % (a, b)))

    print('FRED 2y yields (unverified ids; failure here is expected off-CI)', flush=True)
    for ccy, sid in FRED.items():
        try:
            s = fred(sid)
            raw['Y2_' + ccy] = s
            rows.append(dict(series='Y2_' + ccy, source='fred', group='yields-2y',
                             ok=True, first=str(s.index.min().date()),
                             last=str(s.index.max().date()), n_raw=len(s), note=sid))
            print('  %-8s %-22s %5d obs' % (ccy, sid, len(s)), flush=True)
        except Exception as e:                       # noqa: BLE001
            rows.append(dict(series='Y2_' + ccy, source='fred', group='yields-2y',
                             ok=False, first='', last='', n_raw=0,
                             note='%s: %s' % (sid, type(e).__name__)))
            print('  %-8s %-22s unreachable (%s)' % (ccy, sid, type(e).__name__), flush=True)

    # ---- align: reindex onto px28, forward fill only, never backfill ----
    E = pd.DataFrame(index=idx)
    for k, s in raw.items():
        E[k] = s.reindex(idx.union(s.index)).ffill().reindex(idx)
    # a forward fill cannot create data before the series began
    for k, s in raw.items():
        E.loc[E.index < s.index.min(), k] = np.nan

    C = pd.DataFrame(rows)
    cov = E.notna().mean()
    C['coverage_on_px28'] = C.series.map(cov).round(4)
    C['n_aligned'] = C.series.map(E.notna().sum())
    E.to_csv(OUTF)
    C.to_csv(COV, index=False)
    print('\nwrote %s  %d series x %d rows' % (os.path.basename(OUTF), E.shape[1], len(E)))
    print(C[C.ok][['series', 'source', 'group', 'first', 'coverage_on_px28']]
          .to_string(index=False))
    bad = C[~C.ok]
    if len(bad):
        print('\nUNAVAILABLE (%d):' % len(bad))
        print(bad[['series', 'source', 'note']].to_string(index=False))
    return E, C


if __name__ == '__main__':
    main()
