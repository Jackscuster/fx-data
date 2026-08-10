import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Two-year government yields for the G8, and the 28 pair rate differentials.

In FX the rate differential IS the carry, and this has been blocked for the whole
project. FRED's keyless CSV host refuses this network, so every leg below comes
from the issuing central bank or treasury instead -- eight different institutions,
eight different formats, no API keys except NZD.

  USD  home.treasury.gov       per-year CSV, explicit '2 Yr' column
  EUR  ECB data portal         euro-area AAA spot curve, daily, from 2004-09
       + Bundesbank            German 2y listed securities, daily, from 1997,
                               used to fill everything before the ECB starts
  JPY  MOF jgbcm_all.csv       Shift-JIS, dates as Japanese era years (S/H/R)
  GBP  Bank of England         39 MB zip of xlsx, sheet '3. spot, short end'
  CAD  Bank of Canada Valet    clean CSV behind a terms-and-conditions preamble
  AUD  RBA f02dhist.xls        1995 to 2013-05, chained onto...
       + RBA f2-data.csv       ...the current file, which starts 2013-09
  CHF  SNB cube rendoblid      long format, maturity '2J'
  NZD  FRED api                the one leg that needs a key; api.stlouisfed.org
                               is reachable even though fred.stlouisfed.org is not

WHAT IS NOT DONE TO THIS DATA
  Nothing is padded, interpolated or back-filled. Where a source genuinely has no
  observation the cell stays NaN and the pair differential that depends on it is
  NaN too. Two real holes are known and deliberately left open: AUD has no 2y
  between 2013-05-21 and 2013-09-02, where the RBA archive stops before the
  current file starts, and CHF stops when the SNB cube stops. Filling either
  would invent a flat carry leg, which is exactly the kind of thing the duration
  constructions would read as signal.

  The EUR splice joins two different definitions -- euro-area AAA and German
  Bunds -- inside the in-sample period. The size of the step at the join is
  measured and reported rather than smoothed away.

CACHING. Raw downloads land in data/_ratecache/ (gitignored). Closed Treasury
years and the BoE zip never change, so they are fetched once; anything covering
the present is refetched when the cache is older than REFRESH_H.

Writes data/rates2y.csv (raw daily, own index), data/carry28.csv (28 pair
differentials on the px28 calendar) and results/rates_coverage.csv.
"""
import io, json, re, time, zipfile, hashlib
import urllib.request, urllib.error
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
CACHE = os.path.join(ROOTDATA, '_ratecache')
OUT_Y = os.path.join(ROOTDATA, 'rates2y.csv')
OUT_D = os.path.join(ROOTDATA, 'carry28.csv')
COV = os.path.join(ROOTOUT, 'rates_coverage.csv')
UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
REFRESH_H = 20
FFILL_LIMIT = 10                           # rows, i.e. about two calendar weeks
START = pd.Timestamp('1998-06-01')
CCY = ['EUR', 'GBP', 'AUD', 'NZD', 'USD', 'CAD', 'CHF', 'JPY']
ECB_FROM = pd.Timestamp('2004-09-06')      # first day the ECB AAA curve exists


def _fetch(url, timeout=240, tries=3):
    last = None
    for i in range(tries):
        try:
            return urllib.request.urlopen(
                urllib.request.Request(url, headers=UA), timeout=timeout).read()
        except Exception as e:                       # noqa: BLE001
            last = e
            time.sleep(2 * (i + 1))
    raise last


def cached(url, name=None, immutable=False, timeout=240):
    """Raw bytes, from disk when we already have them.

    immutable marks a resource that cannot change -- a closed Treasury year, the
    BoE archive -- so it is never refetched once present.
    """
    os.makedirs(CACHE, exist_ok=True)
    name = name or hashlib.sha1(url.encode()).hexdigest()[:16]
    f = os.path.join(CACHE, name)
    if os.path.exists(f):
        age_h = (time.time() - os.path.getmtime(f)) / 3600
        if immutable or age_h < REFRESH_H:
            with open(f, 'rb') as fh:
                return fh.read()
    b = _fetch(url, timeout=timeout)
    with open(f, 'wb') as fh:
        fh.write(b)
    return b


def _num(s):
    return pd.to_numeric(pd.Series(s).replace({'.': np.nan, '-': np.nan, '': np.nan}),
                         errors='coerce')


# ------------------------------------------------------------------ USD

def usd():
    """Treasury publishes one CSV per calendar year. Closed years never change."""
    now = pd.Timestamp.now()
    out = []
    for y in range(1999, now.year + 1):
        u = ('https://home.treasury.gov/resource-center/data-chart-center/'
             'interest-rates/daily-treasury-rates.csv/%d/all'
             '?type=daily_treasury_yield_curve&field_tdr_date_value=%d'
             '&page&_format=csv' % (y, y))
        try:
            b = cached(u, 'ust_%d.csv' % y, immutable=(y < now.year))
        except Exception as e:                       # noqa: BLE001
            print('    USD %d failed: %s' % (y, type(e).__name__))
            continue
        d = pd.read_csv(io.BytesIO(b))
        col = next((c for c in d.columns if c.strip() in ('2 Yr', '2 YR', '2Yr')), None)
        if col is None or 'Date' not in d.columns:
            continue
        s = pd.Series(_num(d[col]).values,
                      index=pd.to_datetime(d.Date, format='mixed', errors='coerce'))
        out.append(s.dropna())
    return pd.concat(out).sort_index() if out else pd.Series(dtype=float)


# ------------------------------------------------------------------ EUR

def eur_ecb():
    u = ('https://data-api.ecb.europa.eu/service/data/YC/'
         'B.U2.EUR.4F.G_N_A.SV_C_YM.SR_2Y?format=csvdata')
    d = pd.read_csv(io.BytesIO(cached(u, 'ecb_2y.csv')))
    return pd.Series(_num(d.OBS_VALUE).values,
                     index=pd.to_datetime(d.TIME_PERIOD, errors='coerce')).dropna().sort_index()


def eur_bundesbank():
    u = ('https://api.statistiken.bundesbank.de/rest/download/BBSIS/'
         'D.I.ZST.ZI.EUR.S1311.B.A604.R02XX.R.A.A._Z._Z.A?format=csv&lang=en')
    txt = cached(u, 'bbk_2y.csv').decode('utf-8', 'replace')
    rows = [l.split(',') for l in txt.splitlines()
            if re.match(r'^\d{4}-\d{2}-\d{2}', l)]
    return pd.Series(_num([r[1] for r in rows]).values,
                     index=pd.to_datetime([r[0] for r in rows],
                                          errors='coerce')).dropna().sort_index()


def eur():
    """ECB where it exists, Bundesbank before it. The join is measured, not hidden."""
    a, b = eur_ecb(), eur_bundesbank()
    s = pd.concat([b[b.index < ECB_FROM], a[a.index >= ECB_FROM]]).sort_index()
    ov = a.index.intersection(b.index)
    step = np.nan
    if len(ov) > 250:
        d = (a.reindex(ov) - b.reindex(ov)).dropna()
        step = float(d.mean())
        print('    EUR splice: ECB minus Bundesbank over %d shared days, '
              'mean %+.3f pp, sd %.3f' % (len(d), step, d.std()))
    return s, step


# ------------------------------------------------------------------ JPY

ERA = {'M': 1867, 'T': 1911, 'S': 1925, 'H': 1988, 'R': 2018}


def _era(s):
    m = re.match(r'^([MTSHR])(\d+)\.(\d+)\.(\d+)$', s.strip())
    if not m:
        return pd.NaT
    e, y, mo, da = m.groups()
    try:
        return pd.Timestamp(year=ERA[e] + int(y), month=int(mo), day=int(da))
    except ValueError:
        return pd.NaT


def jpy():
    """MOF ships Shift-JIS with Japanese era years: S49.9.24 is 1974-09-24."""
    u = ('https://www.mof.go.jp/jgbs/reference/interest_rate/data/jgbcm_all.csv')
    txt = cached(u, 'mof_jgb.csv').decode('shift_jis', 'replace')
    lines = [l for l in txt.splitlines() if l.strip()]
    hdr = next(i for i, l in enumerate(lines) if l.split(',')[0].strip() and
               re.match(r'^[MTSHR]\d+\.', lines[i + 1].split(',')[0].strip() or 'x'))
    rows = [l.split(',') for l in lines[hdr + 1:]]
    rows = [r for r in rows if len(r) > 2]
    idx = pd.DatetimeIndex([_era(r[0]) for r in rows])
    s = pd.Series(_num([r[2] for r in rows]).values, index=idx)
    return s[s.index.notna()].dropna().sort_index()


# ------------------------------------------------------------------ GBP

def gbp():
    """BoE ships a 39 MB zip of xlsx, one per era. Sheet '3. spot, short end'
    puts maturities in YEARS on row 3 and dates down column 0 from row 5."""
    u = ('https://www.bankofengland.co.uk/-/media/boe/files/statistics/'
         'yield-curves/glcnominalddata.zip')
    z = zipfile.ZipFile(io.BytesIO(cached(u, 'boe_glc.zip', immutable=False,
                                          timeout=600)))
    out = []
    for n in z.namelist():
        if not n.lower().endswith('.xlsx'):
            continue
        yrs = re.findall(r'(\d{4})', n)
        if yrs and int(yrs[-1]) < 1998 and 'present' not in n.lower():
            continue                                  # era ends before we need it
        try:
            x = pd.ExcelFile(io.BytesIO(z.read(n)))
            sh = next((s for s in x.sheet_names if 'spot' in s.lower()
                       and 'short' in s.lower()), None)
            if sh is None:
                continue
            raw = x.parse(sh, header=None)
        except Exception as e:                       # noqa: BLE001
            print('    GBP %s failed: %s' % (n, type(e).__name__))
            continue
        hdr = next((i for i in range(6)
                    if str(raw.iloc[i, 0]).strip().lower().startswith('years')), 3)
        mat = pd.to_numeric(raw.iloc[hdr, 1:], errors='coerce')
        if mat.notna().sum() == 0:
            continue
        col = int((mat - 2.0).abs().idxmin())
        if abs(float(mat[col]) - 2.0) > .04:
            continue
        body = raw.iloc[hdr + 1:, :]
        dt = pd.to_datetime(body.iloc[:, 0], errors='coerce')
        s = pd.Series(pd.to_numeric(body[col], errors='coerce').values, index=dt)
        out.append(s[s.index.notna()].dropna())
    return pd.concat(out).sort_index() if out else pd.Series(dtype=float)


# ------------------------------------------------------------------ CAD

def cad():
    u = ('https://www.bankofcanada.ca/valet/observations/BD.CDN.2YR.DQ.YLD/csv'
         '?start_date=1998-01-01')
    txt = cached(u, 'boc_2y.csv').decode('utf-8-sig')
    lines = txt.splitlines()
    i = next(k for k, l in enumerate(lines) if l.replace('"', '').strip() == 'OBSERVATIONS')
    d = pd.read_csv(io.StringIO('\n'.join(lines[i + 1:])))
    d.columns = [c.strip('"').strip() for c in d.columns]
    return pd.Series(_num(d.iloc[:, 1]).values,
                     index=pd.to_datetime(d.iloc[:, 0], errors='coerce')).dropna().sort_index()


# ------------------------------------------------------------------ AUD

def aud():
    """The current RBA file only starts 2013-09; the archive stops 2013-05.
    Both are used and the hole between them is left as a hole."""
    out = []
    try:
        b = cached('https://www.rba.gov.au/statistics/tables/xls-hist/f02dhist.xls',
                   'rba_hist.xls', immutable=True)
        x = pd.ExcelFile(io.BytesIO(b))
        raw = x.parse('Data', header=None)
        mn = next(i for i in range(raw.shape[0])
                  if str(raw.iloc[i, 0]).strip().lower() == 'mnemonic')
        col = next(j for j in range(1, raw.shape[1])
                   if str(raw.iloc[mn, j]).strip() == 'FCMYGBAG2D')
        body = raw.iloc[mn + 1:, :]
        dt = pd.to_datetime(body.iloc[:, 0], errors='coerce')
        s = pd.Series(pd.to_numeric(body[col], errors='coerce').values, index=dt)
        out.append(s[s.index.notna()].dropna())
    except Exception as e:                           # noqa: BLE001
        print('    AUD archive failed: %s' % type(e).__name__)
    try:
        txt = cached('https://www.rba.gov.au/statistics/tables/csv/f2-data.csv',
                     'rba_cur.csv').decode('utf-8-sig')
        lines = txt.splitlines()
        sid = next(i for i, l in enumerate(lines) if l.startswith('Series ID'))
        cols = lines[sid].split(',')
        col = cols.index('FCMYGBAG2D')
        rows = [l.split(',') for l in lines[sid + 1:] if l.strip()]
        rows = [r for r in rows if len(r) > col]
        s = pd.Series(_num([r[col] for r in rows]).values,
                      index=pd.to_datetime([r[0] for r in rows],
                                           format='%d-%b-%Y', errors='coerce'))
        out.append(s[s.index.notna()].dropna())
    except Exception as e:                           # noqa: BLE001
        print('    AUD current failed: %s' % type(e).__name__)
    if not out:
        return pd.Series(dtype=float)
    s = pd.concat(out).sort_index()
    return s[~s.index.duplicated(keep='last')]


# ------------------------------------------------------------------ CHF

def chf():
    u = 'https://data.snb.ch/api/cube/rendoblid/data/csv/en'
    txt = cached(u, 'snb_2y.csv').decode('utf-8-sig')
    lines = txt.splitlines()
    i = next(k for k, l in enumerate(lines) if l.replace('"', '').startswith('Date;'))
    d = pd.read_csv(io.StringIO('\n'.join(lines[i:])), sep=';')
    d.columns = [c.strip('"') for c in d.columns]
    d = d[d.D0.astype(str).str.strip() == '2J']
    return pd.Series(_num(d.Value).values,
                     index=pd.to_datetime(d.Date, errors='coerce')).dropna().sort_index()


# ------------------------------------------------------------------ NZD

NZ_CANDIDATES = ['IRLTLT01NZM156N',      # 10y monthly, OECD via FRED -- a fallback
                 'INTGSBNZM193N']        # long-term government bond yield, monthly


def nzd():
    """The only leg needing a key. api.stlouisfed.org is reachable from networks
    that cannot see fred.stlouisfed.org at all, so this is a key problem, not a
    routing one. Candidates are probed in order and what resolved is reported --
    FRED's daily 2y coverage outside the US is thin, so a monthly long rate may
    be the best available and must be labelled as such, never as a 2y."""
    empty = pd.Series(dtype=float, index=pd.DatetimeIndex([]))
    k = os.environ.get('FRED_API_KEY', '').strip()
    if not k:
        print('    NZD skipped: FRED_API_KEY not set in this environment')
        return empty, ''
    for sid in NZ_CANDIDATES:
        u = ('https://api.stlouisfed.org/fred/series/observations?series_id=%s'
             '&api_key=%s&file_type=json&observation_start=1998-01-01' % (sid, k))
        try:
            j = json.loads(cached(u, 'fred_%s.json' % sid))
            obs = j.get('observations', [])
            if not obs:
                continue
            s = pd.Series(_num([o['value'] for o in obs]).values,
                          index=pd.to_datetime([o['date'] for o in obs],
                                               errors='coerce')).dropna().sort_index()
            if len(s) > 100:
                print('    NZD from FRED %s: %d obs' % (sid, len(s)))
                return s, sid
        except Exception as e:                       # noqa: BLE001
            print('    NZD %s failed: %s' % (sid, type(e).__name__))
    return empty, ''


# ------------------------------------------------------------------ assembly

SOURCES = [('USD', 'home.treasury.gov', usd), ('EUR', 'ECB + Bundesbank', None),
           ('JPY', 'MOF', jpy), ('GBP', 'Bank of England', gbp),
           ('CAD', 'BoC Valet', cad), ('AUD', 'RBA archive + current', aud),
           ('CHF', 'SNB rendoblid', chf), ('NZD', 'FRED api (key)', None)]


def fetch_all():
    Y, meta = {}, []
    for ccy, src, fn in SOURCES:
        t0 = time.time()
        note = ''
        try:
            if ccy == 'EUR':
                s, step = eur()
                note = 'splice step %+.3f pp' % step if np.isfinite(step) else ''
            elif ccy == 'NZD':
                s, sid = nzd()
                note = ('FRED %s -- MONTHLY LONG RATE, not a 2y' % sid) if sid else 'no key'
            else:
                s = fn()
        except Exception as e:                       # noqa: BLE001
            print('  %-4s FAILED %s: %s' % (ccy, type(e).__name__, e))
            meta.append(dict(currency=ccy, source=src, ok=False, n=0, first='',
                             last='', note=type(e).__name__))
            continue
        if not isinstance(s.index, pd.DatetimeIndex):
            s = pd.Series(dtype=float, index=pd.DatetimeIndex([]))
        s = s[s.index >= START]
        Y[ccy] = s
        meta.append(dict(currency=ccy, source=src, ok=len(s) > 0, n=len(s),
                         first=str(s.index.min().date()) if len(s) else '',
                         last=str(s.index.max().date()) if len(s) else '', note=note))
        print('  %-4s %-24s %6d obs  %s .. %s  %.0fs %s'
              % (ccy, src, len(s), meta[-1]['first'], meta[-1]['last'],
                 time.time() - t0, note), flush=True)
    return Y, pd.DataFrame(meta)


def build():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    print('fetching 2y yields')
    Y, M = fetch_all()
    R = pd.DataFrame({c: Y[c] for c in CCY if c in Y}).sort_index()
    R.to_csv(OUT_Y)

    # onto the FX calendar: forward fill only, and never before a series begins
    A = pd.DataFrame(index=px.index)
    for c in R.columns:
        s = R[c].dropna()
        if not len(s):
            continue
        # FFILL_LIMIT rows bridges a holiday or a national closure. It does NOT
        # bridge the AUD hole of 2013 or the year CHF has been stale, both of
        # which an unlimited ffill quietly turned into flat carry -- a straight
        # line is exactly what the duration constructions read as signal.
        A[c] = (s.reindex(px.index.union(s.index)).ffill(limit=FFILL_LIMIT)
                 .reindex(px.index))
        A.loc[A.index < s.index.min(), c] = np.nan

    D = pd.DataFrame(index=px.index)
    for p in px.columns:
        b, q = p[:3], p[3:]
        if b in A.columns and q in A.columns:
            D[p] = A[b] - A[q]
    D.to_csv(OUT_D)

    M['coverage_on_px28'] = M.currency.map(
        {c: float(A[c].notna().mean()) for c in A.columns}).round(4)
    M.to_csv(COV, index=False)
    built = [p for p in px.columns if p in D.columns and D[p].notna().any()]
    print('\n%d of 28 pair differentials built; %d currencies with data'
          % (len(built), A.shape[1]))
    print(M.to_string(index=False))
    miss = [p for p in px.columns if p not in built]
    if miss:
        print('missing pairs: %s' % ', '.join(miss))
    print('coverage of the built differentials on the px28 calendar: %.3f'
          % D[built].notna().mean().mean())
    return R, D


if __name__ == '__main__':
    build()
