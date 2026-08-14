import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Assemble a pre-1999 sample, and report honestly what it can and cannot cover.

THE BRIEF ASSUMED 21 PAIRS OVER 1990-1998. It is 3, and the reason is the yields,
not the prices.

  FX          obtainable in full. The repo starts 1999-01-04, but H.10 is
              mirrored on FRED as the DEX* series back to 1971-01-04 and FRED is
              reachable from here. The Fed's own download endpoint returns 403,
              which is why the repo copy stops where it does.
  2y yields   USD  FRED DGS2, 1976 onward                        AVAILABLE
              GBP  BoE GLC zip, files from 1979 onward           AVAILABLE
              CHF  SNB cache, 1988 onward                        AVAILABLE
              JPY  MoF cache parses to zero rows                 NOT AVAILABLE
              CAD  Bank of Canada cache starts 2001-02-15        NOT AVAILABLE
              AUD  RBA current cache is a 31-row fragment        NOT AVAILABLE
              NZD  no data anywhere in the repo                  NOT AVAILABLE

So the confirmation runs on USD, GBP and CHF -- GBPUSD, USDCHF, GBPCHF.

AND THOSE THREE PAIRS ARE NOT THREE INDEPENDENT READS. Three currencies give
three pairs, and any one is the ratio of the other two: GBPCHF is GBPUSD divided
by USDCHF exactly. The effective sample is closer to two independent series than
three, and the confirmation is correspondingly weaker than the 21-pair original.
That is stated here rather than discovered later.

QUOTING CONVENTION. H.10 and its FRED mirror are foreign-per-USD for CHF, JPY and
CAD, and USD-per-foreign for GBP, AUD, NZD and EUR. The repo inverts everything
and then triangulates in base-priority order; the same rule is applied here, and
the rebuilt overlap with px28.csv is checked pair by pair before anything is run.

Writes data/pre1999_px.csv, data/pre1999_rates.csv and
results/pre1999_coverage.csv.
"""
import io
import urllib.request
import numpy as np, pandas as pd

START = pd.Timestamp('1990-01-01')
END = pd.Timestamp('1998-12-31')
CUR = ['USD', 'GBP', 'CHF']
PAIRS = ['GBPUSD', 'USDCHF', 'GBPCHF']
# FRED DEX series and whether the quote is USD-per-foreign (True) or
# foreign-per-USD (False)
FX = {'GBP': ('DEXUSUK', True), 'CHF': ('DEXSZUS', False)}


def fred(sid):
    u = 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=' + sid
    r = urllib.request.urlopen(u, timeout=60).read().decode()
    d = pd.read_csv(io.StringIO(r))
    d.columns = ['date', 'v']
    d['date'] = pd.to_datetime(d.date)
    d['v'] = pd.to_numeric(d.v, errors='coerce')
    return d.dropna().set_index('date').v


def build_fx():
    """USD-per-unit for each currency, then the three crosses."""
    usd = {}
    for c, (sid, is_usd_per) in FX.items():
        s = fred(sid)
        usd[c] = s if is_usd_per else 1.0 / s
    df = pd.DataFrame(usd).sort_index()
    out = pd.DataFrame(index=df.index)
    out['GBPUSD'] = df['GBP']
    out['USDCHF'] = 1.0 / df['CHF']
    out['GBPCHF'] = df['GBP'] / df['CHF']
    return out


def boe_2y():
    import zipfile
    z = zipfile.ZipFile(os.path.join(ROOTDATA, '_ratecache', 'boe_glc.zip'))
    frames = []
    for n in z.namelist():
        if not n.endswith('.xlsx'):
            continue
        # the sheet is '4. nominal spot curve', not '4. spot curve', and the
        # tenor header sits on row 3 with 'years:' in the first cell. The first
        # version guessed both and silently produced zero rows.
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
        cols = [c for c in x.columns
                if isinstance(c, (int, float)) and abs(float(c) - 2.0) < 1e-6]
        if not cols:
            continue
        v = pd.to_numeric(x.set_index('date')[cols[0]], errors='coerce').dropna()
        if len(v):
            frames.append(v.rename('GBP'))
    return pd.concat(frames).sort_index() if frames else pd.Series(dtype=float)


def snb_2y():
    p = os.path.join(ROOTDATA, '_ratecache', 'snb_2y.csv')
    x = pd.read_csv(p, sep=';', skiprows=lambda i: i < 3, on_bad_lines='skip')
    x.columns = [str(c).strip() for c in x.columns]
    dc, vc = x.columns[0], x.columns[-1]
    x[dc] = pd.to_datetime(x[dc], errors='coerce')
    x[vc] = pd.to_numeric(x[vc], errors='coerce')
    x = x.dropna(subset=[dc, vc])
    if len(x.columns) >= 3:
        key = x.columns[1]
        m = x[key].astype(str).str.contains('2', na=False)
        if m.any():
            x = x[m]
    return x.groupby(dc)[vc].mean().rename('CHF')


def main():
    print('PRE-1999 ASSEMBLY. Reporting coverage BEFORE any test is run.')
    print('\nFX from FRED (H.10 mirror, the Fed endpoint returns 403 here)')
    px = build_fx()
    px = px[(px.index >= START) & (px.index <= END)]
    print('  %s -> %s, %d bars, pairs %s'
          % (px.index.min().date(), px.index.max().date(), len(px),
             list(px.columns)))

    # sanity: rebuild overlaps the committed panel where they meet
    live = pd.read_csv(os.path.join(ROOTDATA, 'px28.csv'), index_col=0,
                       parse_dates=True)
    chk = build_fx()
    rows = []
    print('\n  SANITY CHECK against the committed panel, 1999 onward')
    for p in PAIRS:
        i = live.index.intersection(chk.index)
        a, b = live[p].reindex(i), chk[p].reindex(i)
        m = a.notna() & b.notna()
        if m.sum() < 100:
            print('    %-7s too little overlap' % p); continue
        rel = float((np.abs(a[m] - b[m]) / a[m]).median())
        print('    %-7s %6d shared bars, median relative difference %.5f  %s'
              % (p, int(m.sum()), rel, 'OK' if rel < 0.002 else 'MISMATCH'))
        rows.append(dict(pair=p, shared_bars=int(m.sum()), med_rel_diff=rel,
                         ok=rel < 0.002))

    print('\nYIELDS')
    y = {}
    try:
        y['USD'] = fred('DGS2')
        print('  USD  FRED DGS2      %s -> %s' % (y['USD'].index.min().date(),
                                                  y['USD'].index.max().date()))
    except Exception as e:
        print('  USD  FAILED %s' % str(e)[:50])
    try:
        g = boe_2y()
        if len(g):
            y['GBP'] = g
            print('  GBP  BoE GLC zip   %s -> %s' % (g.index.min().date(),
                                                     g.index.max().date()))
        else:
            print('  GBP  BoE zip parsed to zero rows')
    except Exception as e:
        print('  GBP  FAILED %s' % str(e)[:60])
    try:
        c = snb_2y()
        y['CHF'] = c
        print('  CHF  SNB cache     %s -> %s' % (c.index.min().date(),
                                                 c.index.max().date()))
    except Exception as e:
        print('  CHF  FAILED %s' % str(e)[:60])

    rt = pd.DataFrame(y).sort_index()
    rt = rt[(rt.index >= START) & (rt.index <= END)]
    print('\n  pre-1999 yield coverage on the FX calendar')
    rt = rt.reindex(px.index).ffill(limit=10)
    cov = []
    for c in CUR:
        v = rt[c].dropna() if c in rt else pd.Series(dtype=float)
        print('    %-4s %6.3f of %d FX bars%s'
              % (c, (rt[c].notna().mean() if c in rt else 0.0), len(px),
                 ('  %s -> %s' % (v.index.min().date(), v.index.max().date()))
                 if len(v) else '  NONE'))
        cov.append(dict(currency=c, coverage=float(rt[c].notna().mean())
                        if c in rt else 0.0, n_fx_bars=len(px)))

    ok = [p for p in PAIRS
          if p[:3] in rt and p[3:] in rt
          and rt[p[:3]].notna().sum() > 200 and rt[p[3:]].notna().sum() > 200]
    print('\n  PAIRS RUNNABLE PRE-1999: %d of 21 the brief assumed -- %s'
          % (len(ok), ', '.join(ok) if ok else 'none'))
    px.to_csv(os.path.join(ROOTDATA, 'pre1999_px.csv'))
    rt.to_csv(os.path.join(ROOTDATA, 'pre1999_rates.csv'))
    C = pd.DataFrame(cov)
    C['runnable_pairs'] = len(ok)
    C['pairs'] = ', '.join(ok)
    C.to_csv(os.path.join(ROOTOUT, 'pre1999_coverage.csv'), index=False)
    with open(os.path.join(ROOTOUT, 'pre1999_coverage.txt'), 'w') as f:
        f.write('Pre-1999 coverage\n=================\n\n'
                'The brief assumed 21 pairs over 1990-1998. It is %d, and the\n'
                'reason is the yields, not the prices.\n\n'
                'FX is obtainable in full: H.10 is mirrored on FRED as the DEX*\n'
                'series back to 1971 and FRED is reachable. The Fed download\n'
                'endpoint returns 403 from here, which is why the repo copy of\n'
                'px28.csv starts 1999-01-04.\n\n'
                '2-year yields pre-1999:\n'
                '  USD  FRED DGS2, 1976 onward                 AVAILABLE\n'
                '  GBP  BoE GLC zip, 1979 onward               AVAILABLE\n'
                '  CHF  SNB cache, 1988 onward                 AVAILABLE\n'
                '  JPY  MoF cache parses to zero rows          NOT AVAILABLE\n'
                '  CAD  Bank of Canada cache starts 2001-02-15 NOT AVAILABLE\n'
                '  AUD  RBA current cache is 31 rows           NOT AVAILABLE\n'
                '  NZD  no data anywhere in the repo           NOT AVAILABLE\n\n'
                'AND THE RUNNABLE PAIRS ARE NOT INDEPENDENT. Three currencies\n'
                'give three pairs and any one is the ratio of the other two --\n'
                'GBPCHF is GBPUSD divided by USDCHF exactly. The effective\n'
                'sample is nearer two independent series than three.\n'
                % len(ok))
    print('\nwrote data/pre1999_px.csv, data/pre1999_rates.csv, '
          'results/pre1999_coverage.csv + .txt')
    return len(ok)


if __name__ == '__main__':
    main()
