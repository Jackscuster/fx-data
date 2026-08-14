import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""The five-driver programme, closed. One row per driver, and the conclusion.

Assembles what the driver runs already wrote. It computes nothing new; every
figure here traces to a file named in the `files` column.
"""
import pandas as pd

ROWS = [
    dict(driver='1 rate differential momentum', status='DEAD',
         good_for='nothing that survives',
         decided_by='separation -- sub-period split',
         evidence='holdout ranging separation -0.319 (p=0.020) but +0.160 in '
                  '2016-19, the WRONG SIGN, turning negative only from 2020. A '
                  'post-COVID rate-cycle artefact.',
         files='driver_separation_a.csv; driver_subperiod.csv; '
               'ratediff_momentum_*.csv; ratediff_pre1999_result.csv'),
    dict(driver='2 MOVE (bond volatility)', status='KEEPER',
         good_for='confirming the CURRENT regime, crisis especially',
         decided_by='separation -- held sign in every sub-period',
         evidence='crisis days read ~0.9 sd above everything else; '
                  'range-leaning -0.538 / -0.314 / -0.648 across the three '
                  'holdout sub-periods, same sign and size throughout. '
                  'Holdout null p=0.020.',
         files='driver_separation_b.csv; driver_subperiod.csv; '
               'driver_forward_b.csv; move_*.csv'),
    dict(driver='3 equity correlation (S&P 500)', status='DEAD',
         good_for='nothing that survives',
         decided_by='separation -- sign flip between halves',
         evidence='crisis separation +0.172 in-sample (p=0.020) flips to -0.071 '
                  'on the holdout (p=0.647); sub-periods +0.112 / -0.105 / '
                  '-0.139. Mechanism check technically held (JPY/CHF |sep| '
                  '0.238 vs 0.199) but the largest single pair was EURAUD, not '
                  'a funding cross.',
         files='driver_separation_c.csv; driver_subperiod_c.csv; '
               'driver_mechanism_c.csv; driver_forward_c.csv'),
    dict(driver='4 yield curve shape (10y - 2y)', status='DEAD',
         good_for='nothing that survives',
         decided_by='separation -- sign flip between halves AND sub-periods',
         evidence='crisis separation -0.108 in-sample flips to +0.082 on the '
                  'holdout; sub-periods +0.073 / -0.650 / +0.224. Fails both '
                  'nulls (p=0.569, p=0.686). Only 10 of 28 pairs testable: AUD '
                  'and CAD have a 2y but no daily 10y, NZD has neither.',
         files='driver_separation_d.csv; driver_subperiod_d.csv; '
               'driver_forward_d.csv; rates10y_coverage.csv'),
    dict(driver='5 commodities (oil, gold)', status='DEAD',
         good_for='nothing that survives',
         decided_by='separation -- sub-period sign flip',
         evidence='trending separation -0.199 in-sample (p=0.039) holds sign on '
                  'the holdout (-0.107) but fails its null there (p=0.431), and '
                  'sub-periods flip: -0.122 / -0.532 / +0.150. Forward crisis '
                  'lift was x1.17 in BOTH halves -- the most consistent forward '
                  'number in the programme -- but fails its null in both '
                  '(p=0.255, p=0.235).',
         files='driver_separation_e.csv; driver_subperiod_e.csv; '
               'driver_forward_e.csv'),
    dict(driver='5b NZD commodities (dairy, coal)', status='UNTESTABLE',
         good_for='unknown -- no free data exists',
         decided_by='data availability, before any test',
         evidence='Dairy (GDT auction) and coal are not free. Iron ore TIO=F IS '
                  'free but only from 2010-10-14 and is scoped to AUD, which '
                  'gold already covers. Recorded as untestable rather than '
                  'tested badly.',
         files='driver_separation_e.txt'),
]

CONCLUSION = """THE FIVE-DRIVER PROGRAMME, CLOSED
=================================

WHAT WAS TESTED. Five external drivers against the regime classifier, each on the
same terms: does it read differently across trending, ranging and crisis days,
now. Lag one bar, in-sample 1999-2015 chooses, holdout 2016-2026 is read once,
episodes not bars, circular-shift null with 50 draws, and a sub-period split of
the holdout run BEFORE any pass is reported.

THE RESULT. One keeper out of five.

  1 rate differential momentum   DEAD        sub-period sign flip
  2 MOVE bond volatility         KEEPER      held sign everywhere
  3 equity correlation           DEAD        sign flip between halves
  4 yield curve shape            DEAD        sign flip, halves and sub-periods
  5 commodities (oil, gold)      DEAD        sub-period sign flip
  5b NZD commodities             UNTESTABLE  no free data exists

WHAT FREE EXTERNAL DATA CAN DO FOR THIS SYSTEM. One thing: bond volatility
confirms a crisis reading that price structure has already made. Crisis days
carry a MOVE level about 0.9 sd above everything else, and that holds in every
sub-period of the holdout. It is a second opinion on the present, and it is
worth having precisely because it comes from outside the price series the
classifier is built on.

WHAT IT CANNOT DO. Two things, both established rather than assumed.

  It cannot make the state call more reliable. The confidence test -- are runs
  longer and flips fewer when the driver agrees -- was run on three drivers and
  failed on all three. It is retired.

  It cannot see forward. Every forward-odds reading that looked like something
  either flipped sign between halves (equity x1.21 -> x0.61, MOVE x0.83 -> x1.66)
  or failed its null when tested (commodities x1.17 in both halves, p=0.255 and
  p=0.235). Nothing in the free external data raises the odds of a crisis in the
  next 20 bars in a way that survives.

WHY THE FAILURES LOOK THE WAY THEY DO. Four of the five died the same death: a
result that is real in one block or one sub-period and gone or reversed in
another. That is what a driver looks like when it tracks a regime of the world
rather than a property of the market -- 2020-21 dominates almost every one of
these tables. The sub-period split is what exposed it, and it is now standard.

WHERE PREDICTIVE VALUE WOULD HAVE TO COME FROM. Not from prices of other assets,
which is what all five of these are. The remaining candidates are all about
POSITIONING and EXPECTATIONS rather than realised prices:

  CFTC Commitments of Traders   FREE, weekly, and NOT YET TESTED. Speculative
                                positioning in FX futures. Weekly frequency is a
                                real limit against a daily classifier and the
                                data is US-exchange only, but it is free and it
                                is the one obvious gap left in the free universe.
  FX options risk reversals     PAID. The clearest measure of what the market is
                                paying for protection, which is the closest free
                                analogue MOVE only approximates.
  Dealer / bank flow            PAID, and mostly not redistributable.
  Order book depth              PAID.

So the honest position is this: the free external universe has been worked
through and it yields one confirmation signal and no forecast. Anything further
requires either the CFTC positioning data -- free, weekly, untested -- or paid
options data. Layer 1 remains what it always was: a view of the current regime,
never judged on prediction.
"""


def main():
    R = pd.DataFrame(ROWS)
    R.to_csv(os.path.join(ROOTOUT, 'driver_program_summary.csv'), index=False)
    with open(os.path.join(ROOTOUT, 'driver_program_summary.txt'), 'w') as f:
        f.write(CONCLUSION)
    print(CONCLUSION)
    missing = []
    for _, r in R.iterrows():
        for fn in [x.strip() for x in r.files.split(';')]:
            if '*' in fn:
                continue
            if not os.path.exists(os.path.join(ROOTOUT, fn)):
                missing.append(fn)
    print('\nreferenced files missing from results/: %s'
          % (', '.join(sorted(set(missing))) if missing else 'none'))
    print('wrote driver_program_summary.csv + .txt')


if __name__ == '__main__':
    main()
