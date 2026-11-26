"""NNFX BEYOND FX -- Jack's item 3, parts a, b and c.

WHAT THIS IS. The data layer and the cost layer for running the amended
protocol on twelve non-FX instruments. Nothing about the method changes; what
changes is that the two things the FX work takes for granted -- a verified
price series and a MEASURED two-sided spread -- have to be established first.

`results/r2reads/C1_DATA_REPORT.md` already measured availability on 24 Nov
and reached three conclusions this module takes as its starting point: the
front-month futures ROLL, the indices cannot be traded as index levels, and
costs are not obtainable from the price endpoint at all. Jack's item 3b
settles the last one by instruction: a stated baseline from a named public
source, swept 1x to 5x, with the real MT5 spreads to be filled in.

THE SECOND SOURCE IS ONLY REACHABLE FOR THREE OF THE TWELVE, and that is
reported rather than papered over. See VERIFY below.
"""
import os, sys, time, json, random, urllib.request, urllib.parse
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
ROOT = os.path.dirname(_HERE)
ROOTOUT = os.path.join(ROOT, 'results')
ROOTDATA = os.path.join(ROOT, 'data')
sys.path.insert(0, ROOT)

import numpy as np
import pandas as pd
import l2data as LD

OUTDIR = os.path.join(ROOTDATA, 'other')
OUT = os.path.join(ROOTOUT, 'nnfx', 'mkt')
os.makedirs(OUTDIR, exist_ok=True)
os.makedirs(OUT, exist_ok=True)

UA = {'User-Agent': 'Mozilla/5.0 (Macintosh)', 'Accept': '*/*'}

# key, yahoo ticker, group, description, and the same-underlying proxy used
# for the weaker return check where no independent source is reachable
INSTRUMENTS = (
    ('gold',    'GC=F',     'metals_energy', 'COMEX gold future, front month',   'GLD'),
    ('silver',  'SI=F',     'metals_energy', 'COMEX silver future, front month', 'SLV'),
    ('wti',     'CL=F',     'metals_energy', 'NYMEX WTI future, front month',    'USO'),
    ('brent',   'BZ=F',     'metals_energy', 'ICE Brent future, front month',    'BNO'),
    ('spx',     '^GSPC',    'indices',       'S&P 500 index',                    'SPY'),
    ('ndx',     '^NDX',     'indices',       'Nasdaq 100 index',                 'QQQ'),
    ('dji',     '^DJI',     'indices',       'Dow Jones Industrial Average',     'DIA'),
    ('dax',     '^GDAXI',   'indices',       'DAX index',                        'EWG'),
    ('ftse',    '^FTSE',    'indices',       'FTSE 100 index',                   'EWU'),
    ('nikkei',  '^N225',    'indices',       'Nikkei 225 index',                 'EWJ'),
    ('btc',     'BTC-USD',  'crypto',        'Bitcoin in USD',                   None),
    ('eth',     'ETH-USD',  'crypto',        'Ether in USD',                     None),
)

# ---- item 3c, the calendar, unchanged from the amended protocol
EVIDENCE_TO = 2015           # everything learned stops here
COMPUTED_NOT_REPORTED = (2016, 2020)
SEALED_FROM = 2021


# ===================== 3a. fetch =======================================
def fetch_all(refresh=False, verbose=True):
    t0 = int(pd.Timestamp('1985-01-01').timestamp())
    t1 = int(pd.Timestamp.now().timestamp())
    rows = []
    for key, tk, grp, desc, _px in INSTRUMENTS:
        f = os.path.join(OUTDIR, '%s.csv' % key)
        if os.path.exists(f) and not refresh:
            d = pd.read_csv(f, index_col=0, parse_dates=True)
        else:
            try:
                d = LD.yahoo_ohlc(tk, t0, t1)
                d = d.drop(columns=[c for c in ('volume',) if c in d.columns])
                d.to_csv(f, float_format='%.6f')
            except Exception as e:
                if verbose:
                    print('  %-8s FETCH FAILED %r' % (key, e), flush=True)
                rows.append(dict(key=key, ticker=tk, group=grp,
                                 description=desc, rows=0, ok=0,
                                 error='%s: %s' % (type(e).__name__, e)))
                time.sleep(0.5)
                continue
            time.sleep(0.5)
        rows.append(dict(key=key, ticker=tk, group=grp, description=desc,
                         rows=len(d), ok=1, error='',
                         first=str(d.index.min().date()),
                         last=str(d.index.max().date()),
                         **gap_stats(d)))
        if verbose:
            r = rows[-1]
            print('  %-8s %5d bars  %s -> %s  evidence yrs %.1f  '
                  'worst gap %d cal days'
                  % (key, r['rows'], r['first'], r['last'],
                     r['evidence_years'], r['max_gap_days']), flush=True)
    return pd.DataFrame(rows)


def gap_stats(d):
    """History and gaps, Jack's 3a. A gap is calendar days between
    consecutive bars; weekends make 3 the normal maximum, so anything above
    that is a holiday or a hole and the count of holes over a week is the
    number that matters."""
    idx = pd.DatetimeIndex(d.index).sort_values()
    gd = np.diff(idx.values).astype('timedelta64[D]').astype(int)
    ev = idx[idx.year <= EVIDENCE_TO]
    return dict(
        evidence_bars=int(len(ev)),
        evidence_years=float(len(ev) / 252.0),
        evidence_first=(str(ev.min().date()) if len(ev) else ''),
        max_gap_days=int(gd.max()) if len(gd) else 0,
        gaps_over_3d=int((gd > 3).sum()),
        gaps_over_7d=int((gd > 7).sum()),
        gaps_over_30d=int((gd > 30).sum()),
        median_gap_days=float(np.median(gd)) if len(gd) else np.nan,
        bars_per_year=float(len(idx) / max(1e-9,
                            (idx.max() - idx.min()).days / 365.25)))


# ===================== 3a. the second source ============================
def _get_json(u):
    return json.loads(urllib.request.urlopen(
        urllib.request.Request(u, headers=UA), timeout=30).read().decode())


def coinbase_daily(product, t0, t1):
    """Independent second source for crypto. Coinbase Exchange public
    candles: [time, low, high, open, close, volume]."""
    u = ('https://api.exchange.coinbase.com/products/%s/candles'
         '?granularity=86400&start=%sT00:00:00Z&end=%sT00:00:00Z'
         % (product, t0, t1))
    j = _get_json(u)
    d = pd.DataFrame(j, columns=['t', 'low', 'high', 'open', 'close', 'vol'])
    d.index = pd.to_datetime(d.t, unit='s').dt.normalize()
    return d[['open', 'high', 'low', 'close']].sort_index()


def nasdaq_daily(symbol, d1, d2):
    """Independent second source for the Nasdaq indices. SPX and DJI are
    REFUSED by this endpoint (rCode 400) and commodities are not served, so
    it covers NDX only."""
    u = ('https://api.nasdaq.com/api/quote/%s/historical?assetclass=index'
         '&fromdate=%s&todate=%s&limit=9999' % (symbol, d1, d2))
    j = _get_json(u)
    rows = (j.get('data') or {}).get('tradesTable', {}).get('rows')
    if not rows:
        raise ValueError('nasdaq returned no rows (rCode %s)'
                         % j.get('status', {}).get('rCode'))
    def num(x):
        return float(str(x).replace(',', '').replace('$', ''))
    d = pd.DataFrame(dict(
        date=pd.to_datetime([r['date'] for r in rows]),
        open=[num(r['open']) for r in rows],
        high=[num(r['high']) for r in rows],
        low=[num(r['low']) for r in rows],
        close=[num(r['close']) for r in rows])).set_index('date').sort_index()
    return d


# the endpoints tried and refused, recorded so the limitation is auditable
REFUSED = (
    ('stooq.com / stooq.pl', 'returns a JavaScript anti-bot challenge '
     'instead of CSV for every symbol tried'),
    ('fred.stlouisfed.org fredgraph.csv', 'read timeout on SP500 and DJIA, '
     'retried'),
    ('financialmodelingprep.com', 'HTTP 401 without an API key'),
    ('api.statistiken.bundesbank.de (DAX)', 'HTTP 404 on the documented path'),
    ('api.nasdaq.com for SPX, DJI and commodities', 'rCode 400 -- the '
     'endpoint serves COMP and NDX only'),
)


def verify(n=10, seed=20261126, verbose=True):
    """Jack's 3a sanity check, on n random dates per instrument.

    TWO TIERS, AND THE TIER IS REPORTED PER INSTRUMENT.
      independent  a different provider quoting the same instrument. Only
                   BTC, ETH (Coinbase) and NDX (Nasdaq) are reachable.
      proxy        the same underlying through a DIFFERENT instrument from
                   the same provider -- a gold future against a gold ETF.
                   Levels cannot match, so this compares DAILY RETURNS. It
                   catches misalignment, a wrong scale and a corrupt series;
                   it does NOT catch an error the provider makes in both.
    """
    rng = random.Random(seed)
    rows = []
    for key, tk, grp, desc, proxy in INSTRUMENTS:
        f = os.path.join(OUTDIR, '%s.csv' % key)
        if not os.path.exists(f):
            continue
        d = pd.read_csv(f, index_col=0, parse_dates=True)
        tier, src, chk = 'none', '', []
        try:
            if key in ('btc', 'eth'):
                tier, src = 'independent', 'Coinbase Exchange public candles'
                # Coinbase caps a request at 300 candles, so sample a window
                dates = [x for x in d.index if x.year >= 2017]
                picks = sorted(rng.sample(dates, min(n, len(dates))))
                for p in picks:
                    cb = coinbase_daily('%s-USD' % key.upper(),
                                        str((p - pd.Timedelta('2D')).date()),
                                        str((p + pd.Timedelta('2D')).date()))
                    if p in cb.index:
                        chk.append((p, float(d.close.loc[p]),
                                    float(cb.close.loc[p])))
                    time.sleep(0.25)
            elif key == 'ndx':
                tier, src = 'independent', 'api.nasdaq.com historical (NDX)'
                nq = nasdaq_daily('NDX', '2005-01-01', '2015-12-31')
                common = [x for x in d.index if x in set(nq.index)]
                picks = sorted(rng.sample(common, min(n, len(common))))
                for p in picks:
                    chk.append((p, float(d.close.loc[p]),
                                float(nq.close.loc[p])))
            elif proxy:
                tier = 'proxy'
                src = 'same underlying via %s, DAILY RETURNS only' % proxy
                t0 = int(pd.Timestamp('1990-01-01').timestamp())
                t1 = int(pd.Timestamp.now().timestamp())
                pr = LD.yahoo_ohlc(proxy, t0, t1)
                time.sleep(0.5)
                a = d.close.pct_change()
                b = pr.close.pct_change()
                common = [x for x in a.index
                          if x in set(b.index) and np.isfinite(a.get(x, np.nan))
                          and np.isfinite(b.get(x, np.nan))]
                picks = sorted(rng.sample(common, min(n, len(common))))
                for p in picks:
                    chk.append((p, float(a.loc[p]) * 100.0,
                                float(b.loc[p]) * 100.0))
                both = pd.concat([a, b], axis=1, join='inner').dropna()
                rows.append(dict(key=key, tier=tier, source=src,
                                 n_dates=len(picks),
                                 worst_abs_diff=(max(abs(x - y)
                                                     for _p, x, y in chk)
                                                 if chk else np.nan),
                                 unit='percent daily return',
                                 return_corr=float(both.iloc[:, 0].corr(
                                     both.iloc[:, 1])),
                                 n_overlap=int(len(both)), error=''))
                if verbose:
                    print('  %-8s %-12s n=%2d  return corr %+.4f  worst '
                          'date diff %.3f pp'
                          % (key, tier, len(picks), rows[-1]['return_corr'],
                             rows[-1]['worst_abs_diff']), flush=True)
                continue
            if chk:
                wa = max(abs(x - y) for _p, x, y in chk)
                rel = max(abs(x - y) / abs(y) for _p, x, y in chk
                          if abs(y) > 1e-12)
                rows.append(dict(key=key, tier=tier, source=src,
                                 n_dates=len(chk), worst_abs_diff=wa,
                                 worst_rel_diff=rel, unit='close level',
                                 error=''))
                if verbose:
                    print('  %-8s %-12s n=%2d  worst |diff| %.4f  worst '
                          'relative %.2e'
                          % (key, tier, len(chk), wa, rel), flush=True)
            else:
                rows.append(dict(key=key, tier=tier, source=src, n_dates=0,
                                 error='no overlapping dates returned'))
        except Exception as e:
            rows.append(dict(key=key, tier=tier, source=src, n_dates=0,
                             error='%s: %s' % (type(e).__name__, e)))
            if verbose:
                print('  %-8s %-12s FAILED %s: %s'
                      % (key, tier, type(e).__name__, e), flush=True)
    return pd.DataFrame(rows)


# ===================== 3b. costs =======================================
# A STATED BASELINE FROM A NAMED PUBLIC SOURCE, as Jack's 3b instructs, swept
# 1x to 5x. Every row carries its source and a CONFIDENCE, because the
# published figures are quoted in instrument "points" and the point size is
# not always stated on the page. Where the unit is ambiguous the row says so
# and the sweep is the answer until the MT5 list settles it.
#
#   published                 a figure read off a named public page
#   published_unit_ambiguous  the figure is published, the point size is not
#   placeholder_group_median  no figure found; the median of the group's
#                             published figures, in basis points, is used and
#                             flagged in every table it touches
#   no_source                 no figure found and no defensible placeholder
#
# THE EXCHANGE MINIMUM TICK IS ALSO RECORDED as a hard floor: CME GC ticks at
# $0.10/oz, SI at $0.005/oz, CL at $0.01/bbl. A retail CFD account never pays
# the floor, so the floor is a sanity bound on the baseline and not a baseline.
SPREADS = (
    # key, published points, point size in price units, source, confidence
    ('gold',   0.50, 1.00,  'Pepperstone futures-based CFD table (XAUUSD-F), '
                            'spreads 01/07/2025-30/09/2025', 'published'),
    ('silver', 3.00, 0.001, 'Pepperstone futures-based CFD table (Silver), '
                            'point size not stated on the page',
                            'published_unit_ambiguous'),
    ('wti',    5.00, 0.01,  'Pepperstone futures-based CFD table (Crude), '
                            'point size not stated on the page',
                            'published_unit_ambiguous'),
    ('brent',  5.00, 0.01,  'no Brent figure published; WTI\'s figure reused',
                            'placeholder_group_median'),
    ('spx',    1.00, 1.00,  'Pepperstone futures-based CFD table (US500), '
                            'spreads 01/07/2025-30/09/2025', 'published'),
    ('ndx',    3.00, 1.00,  'Pepperstone futures-based CFD table (NAS100), '
                            'spreads 01/07/2025-30/09/2025', 'published'),
    ('dji',    5.00, 1.00,  'Pepperstone futures-based CFD table (US30), '
                            'spreads 01/07/2025-30/09/2025', 'published'),
    ('dax',    None, 1.00,  'no DAX figure found on any page checked',
                            'placeholder_group_median'),
    ('ftse',   None, 1.00,  'no FTSE 100 figure found on any page checked',
                            'placeholder_group_median'),
    ('nikkei', None, 1.00,  'no Nikkei 225 figure found on any page checked',
                            'placeholder_group_median'),
    ('btc',    None, 1.00,  'no figure found; crypto CFD spreads are far '
                            'wider than any index figure here',  'no_source'),
    ('eth',    None, 1.00,  'no figure found; crypto CFD spreads are far '
                            'wider than any index figure here',  'no_source'),
)

TICK_FLOOR = {'gold': 0.10, 'silver': 0.005, 'wti': 0.01, 'brent': 0.01}
TICK_SOURCE = ('CME Group contract specifications, corroborated by the AMP '
               'Futures spec table and the CITICS June 2026 futures sheet')
SPREAD_MULTIPLES = (1.0, 2.0, 3.0, 4.0, 5.0)


def cost_table(verbose=True):
    """-> one row per instrument: the baseline in basis points, the sweep, and
    the exchange tick floor where one exists."""
    grp = {k: g for k, _t, g, _d, _p in INSTRUMENTS}
    ref = {}
    for key, _t, _g, _d, _p in INSTRUMENTS:
        f = os.path.join(OUTDIR, '%s.csv' % key)
        if not os.path.exists(f):
            continue
        d = pd.read_csv(f, index_col=0, parse_dates=True)
        ev = d[d.index.year <= EVIDENCE_TO]
        ref[key] = dict(
            px_evidence=float(ev.close.median()) if len(ev) else np.nan,
            px_recent=float(d.close.tail(252).median()))
    rows = []
    for key, pts, psz, src, conf in SPREADS:
        if key not in ref:
            continue
        pxe, pxr = ref[key]['px_evidence'], ref[key]['px_recent']
        bp = (pts * psz / pxr * 10000.0
              if (pts is not None and np.isfinite(pxr)) else np.nan)
        rows.append(dict(key=key, group=grp[key], published_points=pts,
                         point_size=psz, px_evidence=pxe, px_recent=pxr,
                         baseline_bp=bp, confidence=conf, source=src,
                         tick_floor_price=TICK_FLOOR.get(key, np.nan),
                         tick_floor_bp=(TICK_FLOOR[key] / pxr * 10000.0
                                        if key in TICK_FLOOR and
                                        np.isfinite(pxr) else np.nan)))
    T = pd.DataFrame(rows)
    # the group median fills the placeholders, in BASIS POINTS not in points
    for g in T.group.unique():
        m = T[(T.group == g) & (T.confidence.isin(
            ('published', 'published_unit_ambiguous')))].baseline_bp
        if len(m):
            med = float(np.nanmedian(m))
            fill = (T.group == g) & (~np.isfinite(T.baseline_bp))
            T.loc[fill, 'baseline_bp'] = med
            T.loc[fill, 'confidence'] = 'placeholder_group_median'
    # THE EXCHANGE TICK IS A VALIDATOR ON THE UNIT, NOT JUST A FOOTNOTE.
    # A retail CFD spread cannot be TIGHTER than the underlying exchange's
    # minimum tick. Where it comes out tighter, the point size I read into
    # the published figure is wrong by a power of ten, and the floor says so
    # arithmetically. On the first run silver came out at 0.446 bp against a
    # tick floor of 0.743 bp, which is impossible: its published "3" is
    # 0.03 and not 0.003. The correction is applied here, by the factor the
    # floor implies, and the row is relabelled so nobody reads it as read
    # off a page.
    T['unit_corrected'] = 0
    bad = (np.isfinite(T.tick_floor_bp) & np.isfinite(T.baseline_bp)
           & (T.baseline_bp < T.tick_floor_bp))
    for i in T.index[bad]:
        f = 1.0
        while T.at[i, 'baseline_bp'] * f < T.at[i, 'tick_floor_bp']:
            f *= 10.0
        T.at[i, 'baseline_bp'] *= f
        T.at[i, 'point_size'] *= f
        T.at[i, 'unit_corrected'] = int(f)
        T.at[i, 'confidence'] = 'published_unit_corrected_by_tick_floor'
        T.at[i, 'source'] = (T.at[i, 'source'] +
                             '; point size corrected x%g because the '
                             'published figure fell below the exchange tick '
                             'floor' % f)
    for m in SPREAD_MULTIPLES:
        T['bp_x%g' % m] = T.baseline_bp * m
    T['mt5_actual_bp_FILL_IN'] = np.nan
    if verbose:
        print(T[['key', 'group', 'published_points', 'baseline_bp',
                 'tick_floor_bp', 'confidence']].to_string(index=False))
    return T
