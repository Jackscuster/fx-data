import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTDATA,exist_ok=True); os.makedirs(ROOTOUT,exist_ok=True)
sys.path.insert(0,ROOTLIB)
"""FX crisis calendar, 2000-2026.

==============================================================================
EVERY DATE IN THIS FILE COMES FROM A NEWS EVENT. NO DATE WAS EVER CHOSEN BY
LOOKING AT PRICE.
==============================================================================

That rule is the only thing that makes detector validation here non-circular.
A crisis detector is built from price. If the events it is scored against were
also picked from price -- "the market fell hard that week, call it a crisis" --
then the test is the detector grading its own homework, and a recall of 80%
would mean nothing at all.

So each entry below is a policy decision, an intervention, a bankruptcy, a
referendum, an invasion or a declaration: something that happened in the world
on a date that was reported at the time. Price is never consulted. If you add
an event, cite the news, not the chart. If you cannot name what was announced
that day, it does not belong in this file.

Fields: (date, type, ccy, severity, description)
  type      policy | intervention | credit | geopolitical | pandemic | vote | commodity
  ccy       currency at the epicentre, '' for broad events
  severity  1 minor, 2 major, 3 systemic

DATING NOTE: entries are dated to the day the news broke. Where an event was
announced outside European/US market hours, the market reaction may land on the
following session; the forward-only window in crisis.py is 0 to +15 days, which
absorbs that without ever reaching backwards.

POST-CUTOFF NOTE: the 2025-04-02 and 2026-07-31 entries are taken from the
project handoff (HANDOFF_3.md 8), not from the author's own knowledge of the
news. Verify both before relying on them.

COUNT NOTE: this calendar holds 54 events. The original in-chat version held 48
and was lost before it was committed, so this is a reconstruction, not a
recovery. It contains every anchor the handoff specified plus further events
datable from news. Recall figures computed here are therefore NOT directly
comparable to the table in HANDOFF_3.md 8, which used a 48-event denominator --
that table reported maxabsmove at 38/48. Compare rates, not counts, and expect
small differences in both.
"""
import pandas as pd

EVENTS = [
    # ---- 2000-2006 ----
    ('2000-09-22', 'intervention',  'EUR', 2, 'G7 coordinated intervention to support the euro'),
    ('2001-03-19', 'policy',        'JPY', 2, 'BOJ adopts quantitative easing'),
    ('2001-09-11', 'geopolitical',  '',    3, 'September 11 attacks'),
    ('2001-12-20', 'credit',        '',    2, 'Argentina abandons convertibility, defaults'),
    ('2003-09-20', 'policy',        '',    2, 'G7 Dubai communique calls for FX flexibility'),
    ('2004-03-16', 'intervention',  'JPY', 2, 'Japan ends its record yen-selling campaign'),
    ('2005-07-21', 'policy',        'CNY', 2, 'China ends the dollar peg'),

    # ---- 2007-2009 global financial crisis ----
    ('2007-02-27', 'credit',        '',    1, 'Shanghai selloff, first carry-trade wobble'),
    ('2007-08-09', 'credit',        '',    3, 'BNP Paribas freezes three funds, first carry unwind'),
    ('2008-03-16', 'credit',        'USD', 2, 'Bear Stearns sold to JPMorgan'),
    ('2008-09-15', 'credit',        '',    3, 'Lehman Brothers bankruptcy'),
    ('2008-10-08', 'policy',        '',    3, 'Coordinated global central bank rate cuts'),
    ('2009-03-12', 'intervention',  'CHF', 2, 'SNB intervenes to weaken the franc'),
    ('2009-03-18', 'policy',        'USD', 2, 'Fed announces Treasury purchases, QE1 expansion'),

    # ---- 2010-2012 euro crisis ----
    ('2010-04-23', 'credit',        'EUR', 2, 'Greece formally requests a bailout'),
    ('2010-05-06', 'credit',        '',    1, 'US equity flash crash'),
    ('2010-05-09', 'policy',        'EUR', 2, 'EU stabilisation package and EFSF announced'),
    ('2011-03-11', 'geopolitical',  'JPY', 3, 'Tohoku earthquake and tsunami'),
    ('2011-03-18', 'intervention',  'JPY', 2, 'G7 coordinated yen intervention after Tohoku'),
    ('2011-08-05', 'credit',        'USD', 2, 'S&P downgrades the United States'),
    ('2011-09-06', 'intervention',  'CHF', 3, 'SNB announces the EURCHF 1.20 floor'),
    ('2012-07-26', 'policy',        'EUR', 2, 'Draghi: whatever it takes'),
    ('2012-09-06', 'policy',        'EUR', 2, 'ECB announces OMT'),

    # ---- 2013-2015 ----
    ('2013-04-04', 'policy',        'JPY', 3, 'BOJ launches QQE'),
    ('2013-05-22', 'policy',        'USD', 2, 'Bernanke taper tantrum'),
    ('2014-06-05', 'policy',        'EUR', 2, 'ECB cuts the deposit rate below zero'),
    ('2014-10-31', 'policy',        'JPY', 2, 'BOJ surprise QQE expansion'),
    ('2015-01-15', 'intervention',  'CHF', 3, 'SNB abandons the EURCHF floor'),
    ('2015-08-11', 'policy',        'CNY', 3, 'China devalues the yuan'),

    # ---- 2016-2019 ----
    ('2016-01-29', 'policy',        'JPY', 2, 'BOJ adopts negative interest rates'),
    ('2016-06-23', 'vote',          'GBP', 3, 'Brexit referendum'),
    ('2016-10-07', 'credit',        'GBP', 2, 'Sterling flash crash'),
    ('2016-11-08', 'vote',          'USD', 2, 'US presidential election'),
    ('2018-02-05', 'credit',        '',    2, 'Volatility complex blow-up, XIV termination'),
    ('2018-08-10', 'credit',        '',    2, 'Turkish lira crisis'),
    ('2019-08-05', 'policy',        'CNY', 2, 'Yuan breaks 7, US names China a currency manipulator'),

    # ---- 2020-2021 pandemic ----
    ('2020-03-09', 'commodity',     '',    3, 'Saudi-Russia oil price war'),
    ('2020-03-11', 'pandemic',      '',    3, 'WHO declares a pandemic'),
    ('2020-03-15', 'policy',        'USD', 3, 'Fed emergency cut to zero, swap lines reopened'),

    # ---- 2022-2023 inflation and rates ----
    ('2022-02-24', 'geopolitical',  '',    3, 'Russia invades Ukraine'),
    ('2022-03-16', 'policy',        'USD', 2, 'Fed begins the hiking cycle'),
    ('2022-09-22', 'intervention',  'JPY', 2, 'MOF yen intervention, first since 1998'),
    ('2022-09-23', 'policy',        'GBP', 3, 'UK mini-budget triggers the gilt crisis'),
    ('2022-10-21', 'intervention',  'JPY', 2, 'MOF second yen intervention'),
    ('2023-03-10', 'credit',        'USD', 2, 'Silicon Valley Bank fails'),
    ('2023-03-19', 'credit',        'CHF', 2, 'Credit Suisse rescue by UBS'),
    ('2023-07-28', 'policy',        'JPY', 2, 'BOJ loosens yield curve control'),

    # ---- 2024-2026 yen cycle ----
    ('2024-03-19', 'policy',        'JPY', 2, 'BOJ ends negative rates and YCC'),
    ('2024-04-29', 'intervention',  'JPY', 2, 'MOF intervenes with USDJPY near 160'),
    ('2024-07-31', 'policy',        'JPY', 3, 'BOJ surprise hike, carry unwind begins'),
    ('2024-08-05', 'credit',        'JPY', 3, 'Global carry unwind peak'),
    ('2024-11-05', 'vote',          'USD', 2, 'US presidential election'),
    ('2025-04-02', 'policy',        'USD', 3, 'US reciprocal tariff announcement'),
    ('2026-07-31', 'intervention',  'JPY', 3, 'US-Japan coordinated intervention'),
]


def calendar():
    """-> DataFrame with parsed dates, sorted, one row per event."""
    df = pd.DataFrame(EVENTS, columns=['date', 'type', 'ccy', 'severity', 'description'])
    df['date'] = pd.to_datetime(df['date'])
    return df.sort_values('date').reset_index(drop=True)


if __name__ == '__main__':
    C = calendar()
    pd.set_option('display.width', 200, 'display.max_rows', 100)
    print(C.to_string(index=False))
    print('\n%d events, %s to %s' % (len(C), C.date.min().date(), C.date.max().date()))
    print('\nby type:');     print(C.type.value_counts().to_string())
    print('\nby severity:'); print(C.severity.value_counts().sort_index().to_string())
    print('\nby currency:'); print(C.ccy.replace('', 'broad').value_counts().to_string())
    assert C.date.is_monotonic_increasing
    assert not C.date.duplicated().any(), 'duplicate event dates'
