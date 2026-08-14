import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Chronic currency episodes, dated from the NEWS record. Not from the chart.

THE PRINCIPLE IS THE ONE THAT MADE events.py NON-CIRCULAR. Every start and end
date below is a policy announcement, a meeting outcome or an intervention -- a
thing that was reported on that day. If a date cannot be tied to something
announced, it does not belong here. Dating a "sustained depreciation" from where
the chart started falling would make the detector's later validation worthless,
because the detector reads the chart.

WHAT COUNTS AS CHRONIC: sustained, policy-driven, one-way currency movement over
quarters or years -- a central bank running policy that pushes its own currency
one way while the rest of the world goes the other, or explicitly fighting the
result. Not a shock. The signature is bleed without a spike.

DIRECTION IS RECORDED BUT THE PHENOMENON IS DIRECTION-AGNOSTIC. A currency ground
relentlessly higher by a policy divergence is the same structural object as one
ground lower; only the sign differs. CHF 2010-11 and USD 2014-15 are appreciation
episodes and are kept as such.

THE OVERLAP PROBLEM, STATED UP FRONT. EUR-down 2014-15 and USD-up 2014-15 are the
SAME macro event seen from two sides, as are JPY-down 2012-15 and USD-up in part.
They are listed separately because the detector runs per currency, but the
`macro_event` column groups them, and any count of INDEPENDENT episodes must use
that column, not the row count. Independent macro events here: 5.

Writes results/chronic_episodes.csv and .txt.
"""
import pandas as pd

# currency, direction (-1 weakening, +1 strengthening), start, end,
# macro_event group, what was announced on the start date, source type
EPISODES = [
    ('JPY', -1, '2013-04-04', '2015-06-10', 'boj_qqe',
     'BoJ announces Quantitative and Qualitative Easing under Kuroda: monetary '
     'base to double in two years. Ends when Kuroda tells the Diet (2015-06-10) '
     'the real effective rate is unlikely to fall further.',
     'BoJ policy statement; Diet testimony'),
    ('JPY', -1, '2022-04-28', '2024-07-31', 'boj_ycc_divergence',
     'BoJ reaffirms unlimited fixed-rate JGB purchases to defend yield curve '
     'control while the Fed and ECB tighten -- the explicit divergence decision. '
     'Ends when the BoJ raises its policy rate to 0.25% and announces taper.',
     'BoJ policy statement; MoF intervention record'),
    ('EUR', -1, '2014-06-05', '2015-03-09', 'ecb_neg_qe',
     'ECB cuts the deposit rate below zero for the first time; extended by the '
     '2015-01-22 QE announcement. Ends when asset purchases actually begin.',
     'ECB policy statement'),
    ('USD', +1, '2014-10-29', '2015-03-09', 'ecb_neg_qe',
     'Fed ends QE3 asset purchases, formalising the divergence with the ECB and '
     'BoJ. SAME MACRO EVENT as the EUR row above, seen from the other side.',
     'FOMC statement'),
    ('CHF', +1, '2010-03-11', '2011-09-06', 'chf_haven_bid',
     'SNB signals it will no longer act decisively against appreciation, and the '
     'franc is bid as a haven through the euro-area sovereign crisis. Ends the '
     'day the SNB imposes the 1.20 floor.',
     'SNB policy statements; SNB floor announcement'),
    ('GBP', -1, '2016-06-24', '2016-10-11', 'brexit',
     'EU referendum result announced. Kept because the drift continued for '
     'months on policy expectations, but flagged: this one begins with a shock, '
     'so it is part acute and is the least clean member of this list.',
     'Referendum result; BoE August 2016 stimulus package'),
]

COLS = ['currency', 'direction', 'start', 'end', 'macro_event', 'what_happened',
        'source_type']


def load():
    d = pd.DataFrame(EPISODES, columns=COLS)
    d['start'] = pd.to_datetime(d.start)
    d['end'] = pd.to_datetime(d.end)
    d['days'] = (d.end - d.start).dt.days
    return d


def main():
    d = load()
    n_rows, n_indep = len(d), d.macro_event.nunique()
    print('CHRONIC EPISODES, dated from the news record')
    print('  %d rows, %d INDEPENDENT macro events' % (n_rows, n_indep))
    print('  %-4s %-4s %-11s %-11s %5s  %s'
          % ('ccy', 'dir', 'start', 'end', 'days', 'macro event'))
    for _, r in d.iterrows():
        print('  %-4s %+4d %-11s %-11s %5d  %s'
              % (r.currency, r.direction, r.start.date(), r.end.date(), r.days,
                 r.macro_event))
    d.to_csv(os.path.join(ROOTOUT, 'chronic_episodes.csv'), index=False)
    warn = ('' if n_indep >= 4 else
            '\nFEWER THAN 4 INDEPENDENT EPISODES -- validation cannot claim much.\n')
    with open(os.path.join(ROOTOUT, 'chronic_episodes.txt'), 'w') as f:
        f.write(
            'Chronic currency episodes, dated from the news record\n'
            '=====================================================\n\n'
            'Every start and end date is a policy announcement, meeting outcome\n'
            'or intervention -- something reported on that day. Dating a\n'
            '"sustained depreciation" from where the chart started falling would\n'
            'make the detector\'s validation worthless, because the detector\n'
            'reads the chart. This is the same principle that made the 54-event\n'
            'acute calendar non-circular.\n\n'
            '%d rows, %d INDEPENDENT macro events.\n\n'
            'THE OVERLAP MATTERS. EUR-down 2014-15 and USD-up 2014-15 are the\n'
            'same divergence seen from two sides. They are listed separately\n'
            'because the detector runs per currency, but any count of\n'
            'independent episodes must use the macro_event column, not the row\n'
            'count.\n\n'
            'SIX ROWS IS A SMALL SAMPLE AND FIVE INDEPENDENT EVENTS IS SMALLER.\n'
            'What that costs: no in-sample/out-of-sample split of the episode\n'
            'list is meaningful -- three of the six start before 2016 and three\n'
            'after, so a split leaves two or three events a side. Separation can\n'
            'be measured and null-tested; a holdout confirmation on the episode\n'
            'list cannot. That limit is stated here rather than discovered in\n'
            'the results.\n\n'
            'GBP 2016 is the least clean member: it begins with a shock, so it\n'
            'is part acute. Kept and flagged rather than quietly dropped.\n%s'
            % (n_rows, n_indep, warn))
    print('\n  NOTE: 3 of 6 rows start before 2016 and 3 after, so an IS/OOS')
    print('  split of the EPISODE LIST leaves 2-3 events a side. Separation can')
    print('  be measured and nulled; a holdout confirmation on the list cannot.')
    print('\nwrote chronic_episodes.csv + .txt')
    return d


if __name__ == '__main__':
    main()
