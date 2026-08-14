import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""CFTC Commitments of Traders positioning. The last untested free source.

THE RELEASE LAG IS THE THING THAT FAKES RESULTS HERE, so it is stated exactly.

  A COT report gives positions as of TUESDAY close.
  It is published the following FRIDAY at 15:30 ET.
  The brief's rule -- usable the following MONDAY at the earliest -- is applied.

  So each report is mapped to the first FX bar on or after report_date + 6
  calendar days, held constant until the next report arrives, and then shifted
  one further bar like every other signal in this project. Effective lag from
  the position snapshot to the first bar it can influence: SEVEN calendar days.

  Using the report date directly would look like a five-day head start on a
  weekly series, which is exactly the kind of error that manufactures a finding.
  The lag is a module constant (RELEASE_LAG_DAYS = 6) and is written into the
  output .txt so it can be checked rather than trusted.

COVERAGE. CME FX futures are quoted against USD only, so COT reaches 7 of the 28
pairs: EURUSD, GBPUSD, AUDUSD, NZDUSD, USDCAD, USDCHF, USDJPY. Everything else --
every cross -- has no positioning data at all. That is stated per currency in the
coverage output rather than assumed.

SIGN CONVENTION, which matters for the USD-quoted pairs. COT reports positions in
the FOREIGN currency contract: a long JPY future is short USDJPY. For pairs
written USDxxx the net is negated so that a positive reading always means
"speculators are long the pair as this project quotes it".

CONSTRUCTION, DECLARED, NO SWEEP. Two readings per currency:
  net_share  (noncommercial long - short) / open interest
  chg4       its 4-week change
Weekly, forward-filled to daily, lagged as above.

Writes data/cot.csv, results/cot_coverage.csv.
"""
import io, zipfile, urllib.request
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
OUT = os.path.join(ROOTDATA, 'cot.csv')
OUT4 = os.path.join(ROOTDATA, 'cot_chg4.csv')
RELEASE_LAG_DAYS = 6
# A weekly reading may be carried forward at most this many calendar days before
# it is treated as absent. Without this the forward-fill invents data: NZD's
# contract stops being reported after 2022-02-01, and a plain ffill carried that
# final reading to 2026 at 99.9% "coverage". It also covers the 2018-19 federal
# shutdown, when COT publication was suspended for months.
MAX_STALE_DAYS = 12
UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
YEARS = range(1999, 2027)
# MATCHED BY PREFIX ON THE STRIPPED NAME, not by equality. Contract names are not
# stable across 27 years and every instability here looked exactly like missing
# data until it was chased down:
#   trailing space   every file before 2024 pads the market name, so exact
#                    matching dropped those years and left history starting 2015
#   singular/plural  'AUSTRALIAN DOLLARS' and 'NEW ZEALAND DOLLARS' before 2004,
#                    singular after
#   pound, twice     'POUND STERLING' pre-2004, then 'BRITISH POUND STERLING',
#                    then 'BRITISH POUND' from 2022
# Prefixes also exclude the cross-rate contracts -- 'EURO FX/BRITISH POUND XRATE'
# is not a EUR-vs-USD position and must not be swept in. Note GBP therefore needs
# 'BRITISH POUND - ' with the separator, not a bare 'BRITISH POUND' substring.
CONTRACT = {
    'EUR': ('EURO FX - ',),
    'GBP': ('POUND STERLING - ', 'BRITISH POUND STERLING - ', 'BRITISH POUND - '),
    'JPY': ('JAPANESE YEN - ',),
    'CHF': ('SWISS FRANC - ',),
    'AUD': ('AUSTRALIAN DOLLAR - ', 'AUSTRALIAN DOLLARS - '),
    'NZD': ('NEW ZEALAND DOLLAR - ', 'NEW ZEALAND DOLLARS - '),
    'CAD': ('CANADIAN DOLLAR - ', 'CANADIAN DOLLARS - '),
}


def to_ccy(name):
    n = str(name).strip().upper()
    for c, pres in CONTRACT.items():
        if any(n.startswith(p) for p in pres):
            return c
    return None
# pair -> (currency, sign). +1 means a long foreign-currency future is long the
# pair as quoted here; -1 means it is short it.
PAIRMAP = {'EURUSD': ('EUR', +1), 'GBPUSD': ('GBP', +1), 'AUDUSD': ('AUD', +1),
           'NZDUSD': ('NZD', +1), 'USDCAD': ('CAD', -1), 'USDCHF': ('CHF', -1),
           'USDJPY': ('JPY', -1)}


def fetch_year(y):
    u = 'https://www.cftc.gov/files/dea/history/deacot%d.zip' % y
    b = urllib.request.urlopen(urllib.request.Request(u, headers=UA),
                               timeout=120).read()
    z = zipfile.ZipFile(io.BytesIO(b))
    n = z.namelist()[0]
    d = pd.read_csv(io.BytesIO(z.read(n)), low_memory=False)
    d.columns = [str(c).strip() for c in d.columns]
    name = d.columns[0]
    ccy = d[name].map(to_ccy)
    d = d[ccy.notna()]
    ccy = ccy[ccy.notna()]
    dt = pd.to_datetime(d['As of Date in Form YYYY-MM-DD'], errors='coerce') \
        if 'As of Date in Form YYYY-MM-DD' in d.columns else \
        pd.to_datetime(d['As of Date in Form YYMMDD'].astype(str)
                       .str.zfill(6), format='%y%m%d', errors='coerce')
    dt = dt[d.index]
    out = pd.DataFrame({
        'date': dt.values, 'ccy': ccy.values,
        'oi': pd.to_numeric(d['Open Interest (All)'], errors='coerce').values,
        'long': pd.to_numeric(d['Noncommercial Positions-Long (All)'],
                              errors='coerce').values,
        'short': pd.to_numeric(d['Noncommercial Positions-Short (All)'],
                               errors='coerce').values})
    return out.dropna(subset=['date'])


def to_daily(wide, idx):
    """Weekly -> daily on the FX calendar, with the release lag and a staleness
    cap. Each report is stamped to report_date + RELEASE_LAG_DAYS, held forward,
    dropped once older than MAX_STALE_DAYS, then shifted one bar like every
    other signal here.

    The staleness clock is PER CURRENCY, not per row. NZD stops being reported
    after 2022 while the other six continue, so its column simply goes NaN inside
    a frame whose index keeps advancing -- a shared clock never expires and the
    2022 reading gets carried to 2026 at 99.9% "coverage"."""
    u = wide.copy()
    u.index = u.index + pd.Timedelta(days=RELEASE_LAG_DAYS)
    full = u.index.union(idx)
    out = pd.DataFrame(index=idx, columns=u.columns, dtype=float)
    for c in u.columns:
        col = u[c].reindex(full)
        stamp = pd.Series(col.index.where(col.notna()), index=col.index)\
            .ffill().reindex(idx)
        v = col.ffill().reindex(idx)
        age = (pd.Series(idx, index=idx) - pd.to_datetime(stamp)).dt.days
        out[c] = v.mask(age > MAX_STALE_DAYS)
    return out.shift(1)


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    print('CFTC COT. Release lag: report is TUESDAY positions, published FRIDAY,')
    print('  usable the following MONDAY -- mapped to the first FX bar on or')
    print('  after report_date + %d days, then shifted one more bar.'
          % RELEASE_LAG_DAYS)
    frames = []
    for y in YEARS:
        try:
            frames.append(fetch_year(y))
        except Exception as e:
            print('  %d FAILED %s' % (y, str(e)[:45]))
    if not frames:
        # cftc.gov unreachable. This runs in CI, and a dead external host must
        # not halt the whole rebuild -- the existing file is stale, not wrong.
        print('  NO YEARS FETCHED -- cftc.gov unreachable. Keeping the existing')
        print('  data/cot.csv and leaving results untouched.')
        assert os.path.exists(OUT), 'no COT data and no cached file to fall back on'
        return
    raw = pd.concat(frames, ignore_index=True).drop_duplicates(['date', 'ccy'])
    raw['net_share'] = (raw['long'] - raw['short']) / raw['oi'].replace(0, np.nan)
    print('\n  coverage per currency (weekly reports):')
    cov = []
    for c in CONTRACT:
        d = raw[raw.ccy == c].dropna(subset=['net_share'])
        if not len(d):
            print('    %-4s NONE' % c)
            cov.append(dict(currency=c, reports=0, first='', last=''))
            continue
        print('    %-4s %5d reports  %s -> %s'
              % (c, len(d), d.date.min().date(), d.date.max().date()))
        cov.append(dict(currency=c, reports=len(d),
                        first=str(d.date.min().date()),
                        last=str(d.date.max().date())))
    for c in ('USD',):
        cov.append(dict(currency=c, reports=0, first='',
                        last='no contract -- USD is the quote side'))

    # weekly -> daily with the release lag
    wide = raw.pivot_table(index='date', columns='ccy', values='net_share',
                           aggfunc='last').sort_index()
    # chg4 is the 4-WEEK change, so it is differenced on the weekly grid before
    # any forward-fill -- differencing the daily series would give a 4-day change.
    chg4 = wide.diff(4)
    daily = to_daily(wide, px.index)
    d4 = to_daily(chg4, px.index)
    daily.to_csv(OUT)
    d4.to_csv(OUT4)
    C = pd.DataFrame(cov)
    C['release_lag_days'] = RELEASE_LAG_DAYS
    C['pairs_covered'] = len(PAIRMAP)
    C['pair_list'] = ', '.join(PAIRMAP)
    C.to_csv(os.path.join(ROOTOUT, 'cot_coverage.csv'), index=False)
    with open(os.path.join(ROOTOUT, 'cot_coverage.txt'), 'w') as f:
        f.write(
            'CFTC COT coverage and the release lag\n'
            '=====================================\n\n'
            'A COT report gives positions as of TUESDAY close and is published\n'
            'the following FRIDAY at 15:30 ET. Each report is mapped here to the\n'
            'first FX bar on or after report_date + %d calendar days -- the\n'
            'following Monday -- held until the next report, then shifted one\n'
            'further bar like every other signal in this project.\n\n'
            'Effective lag from position snapshot to first usable bar: SEVEN\n'
            'calendar days. Using the report date directly would look like a\n'
            'five-day head start on a weekly series, which is exactly the error\n'
            'that manufactures a finding.\n\n'
            'CME FX futures are quoted against USD only, so COT reaches 7 of 28\n'
            'pairs: %s. Every cross has no positioning data at all.\n\n'
            'SIGN: COT reports the FOREIGN contract, so a long JPY future is\n'
            'short USDJPY. For USDxxx pairs the net is negated, so a positive\n'
            'reading always means speculators are long the pair as quoted here.\n'
            % (RELEASE_LAG_DAYS, ', '.join(PAIRMAP)))
    print('\n  daily coverage on the FX calendar (staleness cap %d days):'
          % MAX_STALE_DAYS)
    for c in daily.columns:
        n = daily[c].notna()
        span = daily.index[n]
        print('    %-4s %.3f   %s -> %s'
              % (c, n.mean(), span.min().date(), span.max().date()))
    C['daily_coverage'] = C.currency.map(
        {c: round(float(daily[c].notna().mean()), 3) for c in daily.columns})
    C['max_stale_days'] = MAX_STALE_DAYS
    C.to_csv(os.path.join(ROOTOUT, 'cot_coverage.csv'), index=False)
    print('\n  pairs reachable: %d of 28 -- %s'
          % (len(PAIRMAP), ', '.join(PAIRMAP)))
    print('wrote data/cot.csv and results/cot_coverage.csv + .txt')


if __name__ == '__main__':
    main()
