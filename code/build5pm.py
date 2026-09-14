import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""THE 5PM BAR -- px28 from OANDA daily mid closes (17:00 New York).

WHY. Layer 1 was built on Fed H.10 noon fixes; Layer 2 trades OANDA 17:00 NY
bars. Five hours apart on every bar, so the regime and the strategies it routes
never shared a close. This builds the same 28-pair panel build.py builds, from
the same source Layer 2 trades.

HOW -- EXACTLY AS build.py, from seven USD legs. OANDA's direct cross quotes
start 2004-06 (and are single-quote days before 2005); the seven USD legs start
2002-06 (NZDUSD 2002-09-24). Triangulating every pair from the legs, in
build.py's base-priority order EUR GBP AUD NZD USD CAD CHF JPY, gives one method
and one seam-free series from 2002-09-24. Measured against OANDA's own cross
quotes after 2005: median gap 0.38 bp, max 0.92 bp.

WHAT THE PRE-2005 BARS ARE. Every OANDA daily bar before 2005-01-03 is flat --
open = high = low = close, volume 2 -- a single quote per day. They are closes
and they move: their daily returns correlate 0.856 with H.10 noon over
2002-06..2004-12, against 0.817 for 2005-2015 and 0.842 for 2016-2020, so they
behave exactly like the later bars do. Their 17:00 alignment cannot be
verified from intraday data because there is none; that is stated, not hidden.

SANITY -- the OANDA closes, not H.10's. build.py asserts EURUSD 1.601 / USDCHF
0.7296, the noon fixes. On 17:00 closes the same extremes are EURUSD 1.5991
(2008-04-22, same day as H.10's) and USDCHF 0.7209 (2011-08-09, one day before
H.10's 0.7296 and lower, because the SNB-era low printed after noon). If either
fails the rebuild is wrong -- stop, do not move the threshold.

Writes data/px28_5pm.csv (full length, to 2026-08-14). The Layer 1 build on
this series is validated on 2016-2020 ONLY, with 2021-2026 SEALED: the copy
the Layer 1 chain reads is truncated at 2020-12-31 so those years are absent
from every scorer's input, not merely masked.
"""
import itertools, numpy as np, pandas as pd
LEGS = {'EUR': ('EURUSD', False), 'GBP': ('GBPUSD', False), 'AUD': ('AUDUSD', False),
        'NZD': ('NZDUSD', False), 'CAD': ('USDCAD', True), 'CHF': ('USDCHF', True),
        'JPY': ('USDJPY', True)}
PRI = ['EUR', 'GBP', 'AUD', 'NZD', 'USD', 'CAD', 'CHF', 'JPY']
OUT = os.path.join(ROOTDATA, 'px28_5pm.csv')


def main():
    u = {}
    for c, (p, inv) in LEGS.items():
        d = pd.read_csv(os.path.join(ROOTDATA, 'oanda_ohlc', '%s_mid.csv' % p),
                        parse_dates=['date']).set_index('date').close.astype(float)
        u[c] = (1.0 / d) if inv else d          # USD per unit of c, as build.py's 1/x
    u = pd.DataFrame(u); u['USD'] = 1.0
    n0 = len(u); u = u.dropna()
    print('legs %d rows, %d complete (%s -> %s)' % (n0, len(u), u.index.min().date(), u.index.max().date()))
    px = pd.DataFrame(index=u.index)
    for a, b in itertools.combinations(PRI, 2):
        px[a + b] = u[a] / u[b]
    assert list(px.columns) == list(pd.read_csv(os.path.join(ROOTDATA, 'px28.csv'), index_col=0, nrows=1).columns), \
        'column order differs from px28.csv'
    px.index.name = 'Date'
    px.to_csv(OUT)
    print('px28_5pm', px.shape, px.index.min().date(), px.index.max().date())
    emax, cmin = px.EURUSD.max(), px.USDCHF.min()
    print('EURUSD close max %.4f on %s | USDCHF close min %.4f on %s'
          % (emax, px.EURUSD.idxmax().date(), cmin, px.USDCHF.idxmin().date()))
    assert abs(emax - 1.5991) < .01 and abs(cmin - 0.7209) < .01, 'OANDA 5pm sanity check failed'
    print('sanity checks passed')


if __name__ == '__main__':
    main()
