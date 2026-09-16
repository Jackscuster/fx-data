import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""MEASURED COST TABLES BY ENTRY HOUR (audit item 17, 16 Sep).

The shipped cost_table.csv charges majors 1.95 pips (published ThinkMarkets x1.5)
and EVERY cross a flat 4.2 -- right on average for a 19:00 entry and wrong per
pair by up to 2x both ways (GBPNZD pays 7.8, NZDJPY 2.6). results/spread_by_hour
.csv holds the measured OANDA bid/ask spread, per pair, per NY hour, per era.
This writes one table per hour in the same schema, so a run picks its entry
hour with FX_COST_TABLE=results/cost_table_h22.csv and the log names it.

Round trip = the quoted spread once (buy the ask, sell the bid), no markup: the
measurement is the broker's own quote, not a published headline. Level = the
2016-2020 median (the trade years of every book in this repo); the 2004-2015
and 2021-2026 medians are carried as columns for reference.
"""
import pandas as pd, numpy as np

SRC = os.path.join(ROOTOUT, 'spread_by_hour.csv')
OLD = os.path.join(ROOTOUT, 'cost_table.csv')
MAJORS = ('EURUSD', 'GBPUSD', 'AUDUSD', 'NZDUSD', 'USDCAD', 'USDCHF', 'USDJPY')


def build(hour, era='2016-2020'):
    d = pd.read_csv(SRC)
    old = pd.read_csv(OLD).set_index('pair')
    x = d[(d.hour_ny == hour) & (d.era == era)].set_index('pair')
    assert len(x) == 28 and x.index.nunique() == 28, 'spread_by_hour: %d pairs at %02d:00 %s' % (len(x), hour, era)
    rows = []
    for p in sorted(x.index):
        r = x.loc[p]
        ref = {e: float(d[(d.hour_ny == hour) & (d.era == e) & (d.pair == p)].spread_bp_median.iloc[0]) if ((d.hour_ny == hour) & (d.era == e) & (d.pair == p)).any() else np.nan
               for e in ('2004-2015', '2021-2026')}
        rows.append(dict(pair=p, source_url='results/spread_by_hour.csv',
                         provenance='OANDA hourly bid/ask, median spread at %02d:00 NY, %s, n=%d' % (hour, era, int(r.n)),
                         raw_spread_pips=round(float(r.spread_pips_median), 2), markup=1.0,
                         marked_up_pips=round(float(r.spread_pips_median), 2),
                         pip_size=float(old.loc[p, 'pip_size']), median_price=float(old.loc[p, 'median_price']),
                         cost_frac_roundtrip=float(r.spread_bp_median) / 1e4, cost_bp_roundtrip=round(float(r.spread_bp_median), 3),
                         fetch_date='2026-09-16', crisis_multiplier=float(old.loc[p, 'crisis_multiplier']), swap='EXCLUDED',
                         group='major' if p in MAJORS else 'cross', entry_hour_ny=hour,
                         bp_2004_2015=round(ref['2004-2015'], 3), bp_2021_2026=round(ref['2021-2026'], 3),
                         old_flat_bp=round(float(old.loc[p, 'cost_bp_roundtrip']), 3)))
    return pd.DataFrame(rows)


def main():
    for h in (17, 19, 22):
        t = build(h)
        out = os.path.join(ROOTOUT, 'cost_table_h%02d.csv' % h)
        t.to_csv(out, index=False)
        print('%s: majors median %.2f bp, crosses median %.2f bp, %d distinct costs, max/old ratio %.2f (%s), min %.2f (%s)'
              % (os.path.basename(out), t[t.group == 'major'].cost_bp_roundtrip.median(), t[t.group == 'cross'].cost_bp_roundtrip.median(),
                 t.cost_frac_roundtrip.round(8).nunique(), (t.cost_bp_roundtrip / t.old_flat_bp).max(), t.loc[(t.cost_bp_roundtrip / t.old_flat_bp).idxmax(), 'pair'],
                 (t.cost_bp_roundtrip / t.old_flat_bp).min(), t.loc[(t.cost_bp_roundtrip / t.old_flat_bp).idxmin(), 'pair']), flush=True)


if __name__ == '__main__':
    main()
