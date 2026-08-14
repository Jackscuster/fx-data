import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Daily 10-year yields, for the curve-slope driver. Coverage stated, not assumed.

FRED CANNOT DO THIS ON ITS OWN. Only DGS10 is daily; every other G8 country's
long-rate series on FRED is MONTHLY (IRLTLT01xxM156N, median gap 31 days), which
is useless against a daily FX panel. That was checked before anything was built,
because the 2-year file turned out to be missing NZD entirely.

So the 10-year comes from the same places the 2-year did:

  USD  FRED DGS10                          daily, 1962 onward
  EUR  Bundesbank BBSIS ... R10XX          daily, 1997-08-07 onward
  GBP  BoE GLC zip, 10y column of the      daily, 1979 onward
       nominal spot curve
  CHF  SNB cache, key '10J0'               daily, 1988 onward
  JPY  MoF JGB cache, column '10年',       daily
       shift-jis with Japanese era dates

  AUD  2-year exists, no daily 10-year     NOT AVAILABLE
  CAD  2-year exists, no daily 10-year     NOT AVAILABLE
  NZD  neither tenor exists anywhere       NOT AVAILABLE

A curve slope needs BOTH tenors, so the driver runs on the five currencies that
have both: EUR, GBP, USD, CHF, JPY -- ten pairs of the 28.

Writes data/rates10y.csv and results/rates10y_coverage.csv.
"""
import io, zipfile, urllib.request
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
CACHE = os.path.join(ROOTDATA, '_ratecache')
UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}


def fred(sid):
    u = 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=' + sid
    d = pd.read_csv(io.StringIO(urllib.request.urlopen(u, timeout=60)
                                .read().decode()))
    d.columns = ['date', 'v']
    d['v'] = pd.to_numeric(d.v, errors='coerce')
    d = d.dropna()
    return d.set_index(pd.to_datetime(d.date)).v


def bbk10():
    u = ('https://api.statistiken.bundesbank.de/rest/download/BBSIS/'
         'D.I.ZST.ZI.EUR.S1311.B.A604.R10XX.R.A.A._Z._Z.A?format=csv&lang=en')
    r = urllib.request.urlopen(urllib.request.Request(u, headers=UA),
                               timeout=90).read().decode('utf-8', 'ignore')
    d = pd.read_csv(io.StringIO(r), skiprows=4, on_bad_lines='skip')
    d = d.rename(columns={d.columns[0]: 'date', d.columns[1]: 'v'})
    d['v'] = pd.to_numeric(d.v, errors='coerce')
    d['date'] = pd.to_datetime(d.date, errors='coerce')
    d = d.dropna(subset=['date', 'v'])
    return d.set_index('date').v


def boe10():
    z = zipfile.ZipFile(os.path.join(CACHE, 'boe_glc.zip'))
    fr = []
    for n in z.namelist():
        if not n.endswith('.xlsx'):
            continue
        try:
            xl = pd.ExcelFile(io.BytesIO(z.read(n)))
            sh = [t for t in xl.sheet_names if 'spot curve' in t.lower()]
            if not sh:
                continue
            x = pd.read_excel(xl, sheet_name=sh[0], header=3)
        except Exception:
            continue
        x = x.rename(columns={x.columns[0]: 'date'})
        x['date'] = pd.to_datetime(x.date, errors='coerce')
        x = x.dropna(subset=['date'])
        col = [c for c in x.columns
               if isinstance(c, (int, float)) and abs(float(c) - 10.0) < 1e-6]
        if not col:
            continue
        v = pd.to_numeric(x.set_index('date')[col[0]], errors='coerce').dropna()
        if len(v):
            fr.append(v)
    return pd.concat(fr).sort_index() if fr else pd.Series(dtype=float)


def snb10():
    x = pd.read_csv(os.path.join(CACHE, 'snb_2y.csv'), sep=';',
                    skiprows=lambda i: i < 3, on_bad_lines='skip')
    x.columns = [str(c).strip() for c in x.columns]
    dc, kc, vc = x.columns[0], x.columns[1], x.columns[-1]
    x = x[x[kc].astype(str).str.strip() == '10J0']
    x[dc] = pd.to_datetime(x[dc], errors='coerce')
    x[vc] = pd.to_numeric(x[vc], errors='coerce')
    return x.dropna(subset=[dc, vc]).groupby(dc)[vc].mean()


def mof10():
    p = os.path.join(CACHE, 'mof_jgb.csv')
    m = pd.read_csv(p, encoding='shift_jis', skiprows=1, on_bad_lines='skip')
    dc = m.columns[0]
    col = [c for c in m.columns if str(c).strip() == '10年']
    if not col:
        return pd.Series(dtype=float)
    # Japanese era dates: R7.8.14 = Reiwa year 7. Western dates parse directly;
    # era-prefixed ones are converted by era start year.
    ERA = {'R': 2018, 'H': 1988, 'S': 1925}

    def conv(v):
        s = str(v).strip()
        try:
            return pd.Timestamp(s)
        except Exception:
            pass
        if s and s[0] in ERA:
            try:
                y, mo, d = s[1:].split('.')
                return pd.Timestamp(ERA[s[0]] + int(y), int(mo), int(d))
            except Exception:
                return pd.NaT
        return pd.NaT
    idx = m[dc].map(conv)
    v = pd.to_numeric(m[col[0]], errors='coerce')
    out = pd.Series(v.values, index=idx).dropna()
    return out[~out.index.isna()].sort_index()


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    print('DAILY 10-YEAR YIELDS. FRED is daily for USD only -- every other G8')
    print('long-rate series there is MONTHLY, so the rest come from the same')
    print('central-bank caches the 2-year file used.')
    src = [('USD', 'FRED DGS10', lambda: fred('DGS10')),
           ('EUR', 'Bundesbank R10XX', bbk10),
           ('GBP', 'BoE GLC 10y', boe10),
           ('CHF', 'SNB 10J0', snb10),
           ('JPY', 'MoF JGB 10y', mof10)]
    out, cov = {}, []
    for c, name, fn in src:
        try:
            s = fn()
            s = s[~s.index.duplicated(keep='last')].sort_index()
            out[c] = s
            print('  %-4s %-20s %s -> %s, %d obs'
                  % (c, name, s.index.min().date(), s.index.max().date(), len(s)))
            cov.append(dict(currency=c, source=name, obs=len(s),
                            first=str(s.index.min().date()),
                            last=str(s.index.max().date()), available=True))
        except Exception as e:
            print('  %-4s %-20s FAILED %s' % (c, name, str(e)[:50]))
            cov.append(dict(currency=c, source=name, obs=0, first='', last='',
                            available=False))
    for c, why in (('AUD', '2y exists, no daily 10y'),
                   ('CAD', '2y exists, no daily 10y'),
                   ('NZD', 'neither tenor exists anywhere')):
        cov.append(dict(currency=c, source=why, obs=0, first='', last='',
                        available=False))
        print('  %-4s %-20s NOT AVAILABLE' % (c, why))
    R = pd.DataFrame(out).reindex(px.index).ffill(limit=10)
    R.to_csv(os.path.join(ROOTDATA, 'rates10y.csv'))
    print('\n  coverage on the FX calendar:')
    for c in R.columns:
        print('    %-4s %.3f of %d bars' % (c, R[c].notna().mean(), len(R)))
    rt2 = pd.read_csv(os.path.join(ROOTDATA, 'rates2y.csv'), index_col=0,
                      parse_dates=True)
    both = [c for c in R.columns if c in rt2 and rt2[c].notna().sum() > 100]
    pairs = [p for p in px.columns if p[:3] in both and p[3:] in both]
    print('\n  currencies with BOTH tenors: %s' % ', '.join(both))
    print('  pairs with a full curve slope: %d of 28 -- %s'
          % (len(pairs), ', '.join(pairs)))
    C = pd.DataFrame(cov)
    C['pairs_constructible'] = len(pairs)
    C['pair_list'] = ', '.join(pairs)
    C.to_csv(os.path.join(ROOTOUT, 'rates10y_coverage.csv'), index=False)
    with open(os.path.join(ROOTOUT, 'rates10y_coverage.txt'), 'w') as f:
        f.write('Daily 10-year yield coverage\n============================\n\n'
                'FRED is daily for USD only. Every other G8 long-rate series\n'
                'there is MONTHLY (IRLTLT01xxM156N, median gap 31 days), which\n'
                'is useless against a daily FX panel. Checked before building,\n'
                'because the 2-year file turned out to be missing NZD entirely.\n\n'
                'A curve slope needs BOTH tenors. Available for %s.\n'
                'AUD and CAD have a 2-year but no daily 10-year; NZD has\n'
                'neither. The driver therefore runs on %d of 28 pairs:\n%s\n'
                % (', '.join(both), len(pairs), ', '.join(pairs)))
    print('\nwrote data/rates10y.csv and results/rates10y_coverage.csv + .txt')


if __name__ == '__main__':
    main()
