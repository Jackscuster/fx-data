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


# ===================== 3d. the engine wiring ============================
def frames(keys=None, verbose=False):
    """{instrument: OHLC frame} for nnfxproto.set_world.

    THE ENGINE IS ALREADY WORLD-PARAMETERISED and that is why item 3 needs no
    engine surgery: the 20 matched null runs feed it synthetic frames through
    set_world, so a frame of gold is the same kind of object as a frame of a
    scrambled EURUSD. Four columns, a DatetimeIndex, nothing else -- exactly
    what nnfxsrc3.zero_edge_frames produces.
    """
    keys = list(keys or [k for k, _t, _g, _d, _p in INSTRUMENTS])
    out = {}
    for k in keys:
        f = os.path.join(OUTDIR, '%s.csv' % k)
        d = pd.read_csv(f, index_col=0, parse_dates=True)
        d = d[['open', 'high', 'low', 'close']].astype(float).sort_index()
        d = d[np.isfinite(d.to_numpy()).all(axis=1)]
        # A BAR MUST CONTAIN ITS OWN OPEN AND CLOSE -- the same rule
        # check_world enforces on a synthetic world. Index levels from a
        # vendor occasionally violate it.
        hi = np.maximum.reduce([d.high.to_numpy(), d.open.to_numpy(),
                                d.close.to_numpy()])
        lo = np.minimum.reduce([d.low.to_numpy(), d.open.to_numpy(),
                                d.close.to_numpy()])
        nfix = int((hi > d.high.to_numpy() + 1e-12).sum()
                   + (lo < d.low.to_numpy() - 1e-12).sum())
        d['high'], d['low'] = hi, lo
        d.index.name = 'date'
        out[k] = d
        if verbose:
            print('  %-8s %5d bars  %s -> %s  geometry fixes %d'
                  % (k, len(d), d.index.min().date(), d.index.max().date(),
                     nfix), flush=True)
    return out


def write_cost_table(mult=1.0, path=None, verbose=True):
    """A cost table in the SAME SCHEMA l2sweep.load_costs reads, at `mult`
    times the baseline. The sweep Jack asked for is five of these."""
    T = cost_table(verbose=False)
    T = T[np.isfinite(T.baseline_bp)].copy()
    rows = []
    for _i, r in T.iterrows():
        bp = float(r.baseline_bp) * float(mult)
        rows.append(dict(
            pair=r.key, source_url='results/nnfx/mkt/cost_baseline.csv',
            provenance=('item 3b baseline x%g; %s' % (mult, r.source))[:400],
            raw_spread_pips=np.nan, markup=mult,
            marked_up_pips=np.nan, pip_size=np.nan,
            median_price=r.px_recent, cost_frac_roundtrip=bp / 1e4,
            cost_bp_roundtrip=bp, fetch_date='2026-11-26',
            crisis_multiplier=2.0, swap='EXCLUDED', group=r.group,
            entry_hour_ny=np.nan, bp_2004_2015=bp, bp_2021_2026=bp,
            old_flat_bp=bp, confidence=r.confidence))
    C = pd.DataFrame(rows)
    path = path or os.path.join(OUT, 'cost_table_mkt_x%g.csv' % mult)
    C.to_csv(path, index=False)
    if verbose:
        print('  %s: %d instruments, median %.2f bp round trip'
              % (os.path.basename(path), len(C),
                 C.cost_bp_roundtrip.median()), flush=True)
    return path, len(C), list(C.pair)


# ===================== 3d. the sleeve bank ==============================
# THE SAME WINDOWS AS THE FX WORK, ON PURPOSE. The indices carry evidence back
# to 1985 and could support a longer admission window, but item 3g asks for a
# COMBINED FX plus other-markets book, and a book whose two halves were
# admitted on different calendars is not one book. The extra history is
# measured and reported and deliberately not used.
H1Y = tuple(range(2005, 2011))
H2Y = tuple(range(2011, 2016))
PERIODS = (('h1', H1Y), ('h2', H2Y))
WORLD_TAG = 'mkt'


def declared_bank(mult=1.0, keys=None, verbose=True):
    """The 18 declared algorithms on the costed instruments, both windows."""
    import l2sweep as S
    import nnfxproto as P
    import nnfxsrc3 as S3
    import nnfxsleeves as BK
    path, n, insts = write_cost_table(mult, verbose=False)
    keys = list(keys or insts)
    S.load_costs(path, npairs=n)
    S3.init_space()
    F = frames(keys)
    P.set_world(WORLD_TAG, F)
    # A16: the peg guard's cross-section is the TRADED UNIVERSE of the
    # world being run. Left at its default it reaches for the 28 FX
    # pairs and raises KeyError('mkt','AUDCAD') -- which is guard 43
    # working, not a bug. What the rule means on a heterogeneous
    # universe is weaker than on FX, and A16 says so.
    peg_was = list(P.PEG_PAIRS)
    P.PEG_PAIRS = list(keys)
    try:
        D = BK.declared_sleeves()
        rows = []
        for (nm, C, src, cp) in D:
            for k in keys:
                try:
                    per = P.fast_per_pair(C, k, PERIODS)
                except Exception as e:
                    rows.append(dict(algo=nm, source=src, instrument=k,
                                     spread_mult=mult, error='%s: %s'
                                     % (type(e).__name__, e)))
                    continue
                for w, _yy in PERIODS:
                    d = dict(per[w])
                    rows.append(dict(
                        algo=nm, source=src, instrument=k, window=w,
                        spread_mult=mult, R=float(d['R']),
                        R_ex_best_day=float(d['R_ex_best_day']),
                        best_trade=float(d['best_trade']),
                        trades=int(d['trades']),
                        admitted=int(BK.adm_ok(d) and
                                     (d['best_trade'] / d['R'] < 0.25
                                      if d['R'] > 0 else False)),
                        error=''))
        B = pd.DataFrame(rows)
        if verbose and len(B):
            ok = (B[B.error == ''] if 'admitted' in B.columns
                  else B.iloc[0:0])
            nerr = int((B.error != '').sum())
            print('  x%g: %d rows, %d admitted of %d sleeve-windows, '
                  '%d errors'
                  % (mult, len(B),
                     int(ok.admitted.sum()) if len(ok) else 0,
                     len(ok), nerr), flush=True)
            if nerr:
                print('    first error: %s'
                      % B[B.error != ''].error.iloc[0], flush=True)
        return B
    finally:
        P.PEG_PAIRS = peg_was
        P.set_world('real')
        P.drop_world(WORLD_TAG)


# ===================== 3a-3d. the report ================================
def other_markets_md():
    """OTHER_MARKETS.md from the CSVs on disk.

    NOTE ON r['first'] AND r['last']. A pandas row is a Series, and Series
    inherits .first and .last from NDFrame, so r.first is a BOUND METHOD and
    not the column named 'first'. The first version of this report printed
    "<bound method NDFrame.first of key gold ...>" into the middle of a
    markdown table. Columns are read by subscript here for exactly that
    reason.
    """
    A = pd.read_csv(os.path.join(OUT, 'availability.csv'))
    V = pd.read_csv(os.path.join(OUT, 'verify.csv'))
    T = pd.read_csv(os.path.join(OUT, 'cost_baseline.csv'))
    M = pd.read_csv(os.path.join(OUT, 'declared_bank_x1.csv'))
    M = M[M.error.isna() | (M.error == '')]
    B = pd.read_csv(os.path.join(OUT, 'declared_bank_fx_reference.csv'))
    L = []
    def w(x=''):
        L.append(x)
    w('# OTHER_MARKETS \u2014 item 3, parts a to d')
    w()
    w('**Same protocol as amended. Nothing about the method changed except '
      'what `PROTOCOL.md` A16 declares**, and A16 exists because one engine '
      'standing rule \u2014 the peg guard \u2014 reaches for the 28 FX pairs '
      'by construction and had to be pointed at the traded universe instead.')
    w()
    w('Parts **e, f and g are NOT in this file.** What is missing and what it '
      'needs is stated at the end, plainly.')
    w()
    w('## 3a \u2014 history and gaps, every row fetched today')
    w()
    w('| instrument | ticker | group | bars | first | last | evidence bars '
      '(to 2015) | evidence yrs | worst gap (cal days) | gaps >7d |')
    w('|---|---|---|---:|---|---|---:|---:|---:|---:|')
    for _i, r in A.iterrows():
        w('| %s | `%s` | %s | %d | %s | %s | %d | %.1f | %d | %d |'
          % (r['key'], r['ticker'], r['group'], r['rows'], r['first'],
             r['last'], r['evidence_bars'], r['evidence_years'],
             r['max_gap_days'], r['gaps_over_7d']))
    w()
    w('**The indices reach further back than the 24 November data report '
      'assumed** \u2014 it fetched from 1990 and these were fetched from '
      '1985, so the S&P 500 and the FTSE 100 carry **31 years of evidence**, '
      'more than the FX data itself.')
    w()
    w('**ETH has zero evidence bars.** Its first bar is 2017-11-09, after the '
      'evidence period closes. BTC has **1.9 years**. Under Jack\'s calendar '
      'neither can be tuned at all, which is 3c\'s answer before any test is '
      'run.')
    w()
    w('### A data-quality finding the geometry check caught')
    w()
    w('A bar must contain its own open and close. The futures series violate '
      'it: **gold on 463 bars, silver on 244, Brent on 69, WTI on 7**. The '
      'six indices and both crypto series violate it on **zero**. The '
      'violations are repaired the way a synthetic world is repaired \u2014 '
      'high raised to max(high, open, close), low lowered to min \u2014 and '
      'the count is reported rather than silently fixed.')
    w()
    w('## 3a \u2014 the second source, on ten random dates each')
    w()
    w('**This is the weakest part of item 3, and it is weak for a reason '
      'outside my reach.** Only three of the twelve have a reachable '
      'independent source. Everything tried and refused is listed below so '
      'the limit is auditable.')
    w()
    w('| instrument | tier | source | n | worst difference | reading |')
    w('|---|---|---|---:|---:|---|')
    read = {
        'ndx': 'exact \u2014 3.6e-08 relative, the series is confirmed',
        'btc': '**2.37% relative** \u2014 crypto has no official close, so '
               'two venues disagree by this much on the same day',
        'eth': '**1.26% relative** \u2014 same reason',
        'spx': 'strong \u2014 returns track SPY at +0.984',
        'dji': 'strong \u2014 returns track DIA at +0.987',
        'gold': 'moderate \u2014 +0.888 against GLD',
        'silver': 'moderate \u2014 +0.897 against SLV',
        'brent': 'moderate \u2014 +0.912 against BNO',
        'wti': '**poor, +0.541** \u2014 USO is a known-bad tracker of WTI, so '
               'this says nothing about the price series and everything about '
               'the proxy',
        'dax': '**uninformative, +0.738** \u2014 EWG is USD-denominated and '
               'trades in US hours',
        'ftse': '**uninformative, +0.668** \u2014 EWU, same reason',
        'nikkei': '**uninformative, +0.427** \u2014 EWJ, same reason',
    }
    for _i, r in V.iterrows():
        wr = r.get('worst_rel_diff', np.nan)
        wd = ('%.2e relative' % wr if np.isfinite(wr)
              else '%.3f pp of daily return' % r['worst_abs_diff'])
        w('| %s | %s | %s | %d | %s | %s |'
          % (r['key'], r['tier'], r['source'], r['n_dates'], wd,
             read.get(r['key'], '')))
    w()
    w('**Endpoints tried and refused**, so this is a reach limit and not an '
      'omission:')
    w()
    for nm, why in REFUSED:
        w('- `%s` \u2014 %s' % (nm, why))
    w()
    w('**What this means for the result.** The S&P 500, Dow and Nasdaq 100 '
      'series are confirmed. Gold, silver and Brent are consistent with their '
      'ETFs. **WTI, DAX, FTSE and Nikkei are UNVERIFIED** \u2014 the only '
      'proxy available measures a different thing and no independent source '
      'was reachable. Any result on those four carries that caveat.')
    w()
    w('## 3b \u2014 costs: a stated baseline, swept 1x to 5x')
    w()
    w('| instrument | published points | point size | baseline (bp round '
      'trip) | exchange tick floor (bp) | confidence |')
    w('|---|---:|---:|---:|---:|---|')
    for _i, r in T.iterrows():
        w('| %s | %s | %g | %s | %s | %s |'
          % (r['key'],
             '--' if not np.isfinite(r['published_points'])
             else '%g' % r['published_points'],
             r['point_size'],
             '--' if not np.isfinite(r['baseline_bp'])
             else '%.3f' % r['baseline_bp'],
             '--' if not np.isfinite(r['tick_floor_bp'])
             else '%.3f' % r['tick_floor_bp'],
             r['confidence']))
    w()
    w('FX reference: **majors 1.5 bp, crosses 3.0 bp** round trip. The index '
      'CFDs come out comparable to an FX major; WTI comes out about four '
      'times one.')
    w()
    w('### The exchange tick turned out to be a validator, not a footnote')
    w()
    w('A retail CFD spread cannot be **tighter** than the underlying '
      'exchange\'s minimum tick. Silver\'s published figure read as **0.446 '
      'bp against a tick floor of 0.743 bp**, which is impossible, so the '
      'point size was wrong by a factor of ten. The correction is applied by '
      'the factor the floor implies and the row is relabelled '
      '`published_unit_corrected_by_tick_floor`. Every baseline now sits at '
      'or above its floor, checked arithmetically.')
    w()
    w('**BTC and ETH have no cost source, so they are not costed and not '
      'booked.** That leaves **ten** instruments. The five swept tables are '
      '`results/nnfx/mkt/cost_table_mkt_x{1,2,3,4,5}.csv`.')
    w()
    w('### For Jack to fill in \u2014 the MT5 symbol list')
    w()
    w('Every number above the sweep is a published headline, not a measured '
      'two-sided spread, and the FX work is costed from **measured OANDA '
      'hourly bid/ask**. These are not the same kind of number, and the sweep '
      'exists because of it.')
    w()
    w('| instrument | baseline used (bp) | your MT5 spread | ratio to '
      'baseline |')
    w('|---|---:|---|---|')
    for _i, r in T.iterrows():
        w('| %s | %s | | |'
          % (r['key'], '--' if not np.isfinite(r['baseline_bp'])
             else '%.3f' % r['baseline_bp']))
    w()
    w('## 3c \u2014 the calendar, unchanged')
    w()
    w('Evidence to **2015**. **2016-2020 computed and not reported.** **2021 '
      'onward sealed.** The admission and scoring windows are the same '
      '2005-2010 and 2011-2015 the FX work uses, on purpose: item 3g asks for '
      'a combined book, and a book whose halves were admitted on different '
      'calendars is not one book. The extra index history back to 1985 is '
      'measured above and deliberately not used.')
    w()
    w('**Crypto, reported separately as Jack asked.** It is not that short '
      'history is awkward \u2014 **ETH has no evidence period at all** and '
      'BTC has 1.9 years against the 5 to 6 every other instrument gets. '
      'Neither has a cost source. Neither is admitted, booked or scored '
      'anywhere in this file, and no amount of compute changes that: it would '
      'need a different calendar, which would make its results '
      'non-comparable with everything else here.')
    w()
    w('## 3d \u2014 the sleeve bank, the 18 declared algorithms')
    w()
    w('| | FX, 28 pairs | other markets, 10 instruments |')
    w('|---|---:|---:|')
    w('| sleeve-windows | %d | %d |' % (len(B), len(M)))
    w('| median trades | %.0f | %.0f |'
      % (B.trades.median(), M.trades.median()))
    w('| mean R per sleeve-window | **%+.3f** | **%+.3f** |'
      % (B.R.mean(), M.R.mean()))
    w('| share positive | %.3f | %.3f |'
      % ((B.R > 0).mean(), (M.R > 0).mean()))
    w('| admitted | %d (%.2f%%) | %d (%.2f%%) |'
      % (B.admitted.sum(), 100 * B.admitted.mean(),
         M.admitted.sum(), 100 * M.admitted.mean()))
    w()
    w('**The 18 declared algorithms are not worse off FX \u2014 they are '
      'mildly better.** Mean R per sleeve-window is **%+.3f** on the other '
      'instruments against **%+.3f** on FX. Both are close to zero and the '
      'admission rate is about 1%% either way, so this is not an edge; it is '
      'the absence of the penalty one might have expected.'
      % (M.R.mean(), B.R.mean()))
    w()
    w('**Trade counts are the same, which rules out the obvious artefact.** '
      'Median %.0f on FX and %.0f off it, with near-identical deciles, so the '
      'handful of admissions is the admission test being strict and not these '
      'instruments being untradeable.'
      % (B.trades.median(), M.trades.median()))
    w()
    w('**All five admissions fall in 2005-2010 and none in 2011-2015.**')
    w()
    w('| instrument | window | mean R | best R | admitted | median trades |')
    w('|---|---|---:|---:|---:|---:|')
    g = M.groupby(['instrument', 'window']).agg(
        mean_R=('R', 'mean'), best_R=('R', 'max'),
        adm=('admitted', 'sum'), med=('trades', 'median')).reset_index()
    for _i, r in g.iterrows():
        w('| %s | %s | %+.2f | %+.2f | %d | %.0f |'
          % (r['instrument'], r['window'], r['mean_R'], r['best_R'],
             r['adm'], r['med']))
    w()
    w('### A16, measured rather than assumed')
    w()
    w('A16 kept the peg guard switched on for sameness of method while '
      'warning that its cross-section is heterogeneous off FX. Measured: it '
      'blocks **0.3% of bars** across the ten instruments against **0.7% on '
      'the 28 FX pairs**. It barely binds, so no result here rests on it, and '
      'the low admission count is not its doing.')
    w()
    w('## What is NOT in this file')
    w()
    w('**3d, the Source 3 sample.** The 18 declared algorithms are done. The '
      '200,000-algorithm sample on ten instruments is the same shape of job '
      'as the FX bank and needs a clear run at the machine; three null '
      'workers hold it until about 18:00.')
    w()
    w('**3e, does fit carry here.** Needs the sample bank above, and a '
      'scrambled-data null built per instrument.')
    w()
    w('**3f, the books under the five gates**, including the '
      'instrument-group rotations. Needs 3d and 3e.')
    w()
    w('**3g, the combined FX plus other-markets book.** Needs 3f.')
    w()
    w('None of these is blocked on a decision \u2014 they are blocked on '
      'compute, and on the machine being busy with item 1. The engine wiring '
      'they need is built and tested: `nnfxmkt.frames` feeds `set_world`, the '
      'cost tables load, and the declared bank ran with **zero errors on 360 '
      'sleeve-windows**.')
    w()
    w('## Provenance')
    w()
    for f, n in (('availability.csv', len(A)), ('verify.csv', len(V)),
                 ('cost_baseline.csv', len(T)),
                 ('declared_bank_x1.csv', len(M)),
                 ('declared_bank_fx_reference.csv', len(B))):
        w('- `results/nnfx/mkt/%s` \u2014 %d rows' % (f, n))
    w('- `data/other/*.csv` \u2014 12 daily OHLC series, fetched 2026-11-26')
    w('- `code/nnfxmkt.py`; fetcher `code/l2data.py:yahoo_ohlc`')
    w('- `PROTOCOL.md` A16 \u2014 the peg guard off FX')
    w('- tick sizes: CME Group contract specifications, corroborated by the '
      'AMP Futures spec table and the CITICS June 2026 futures sheet')
    w('- spreads: Pepperstone published CFD spread tables '
      '(01/07/2025-30/09/2025) and Capital.com indicative September spreads')
    md = '\n'.join(L) + '\n'
    p = os.path.join(ROOTOUT, 'nnfx', 'OTHER_MARKETS.md')
    with open(p, 'w') as f:
        f.write(md)
    return p, len(L)
