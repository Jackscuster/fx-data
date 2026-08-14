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
    dict(driver='6 CFTC positioning (COT)', status='DEAD',
         good_for='nothing that survives',
         decided_by='separation -- sign flips on every reading',
         evidence='All four readings flip. |4-week change| is the sharpest: '
                  'ranging +0.246 in-sample (p=0.020) reverses to -0.193 on the '
                  'holdout (p=0.078) -- beats its null in BOTH halves with '
                  'OPPOSITE signs, which is a real magnitude attached to an '
                  'unreliable sign. The declared crowded-trade cell (top decile '
                  '|net| vs P(acute crisis in 20 bars)) held direction, x1.32 '
                  'in-sample and x1.21 on the holdout, but fails its null in '
                  'both (p=0.196, p=0.412) -- the same shape as commodities. '
                  'Reaches 7 of 28 pairs, no crosses; NZD ends 2022-02-01.',
         files='cot_separation.csv; cot_subperiod.csv; cot_forward.csv; '
               'cot_coverage.csv'),
    dict(driver='5b NZD commodities (dairy, coal)', status='UNTESTABLE',
         good_for='unknown -- no free data exists',
         decided_by='data availability, before any test',
         evidence='Dairy (GDT auction) and coal are not free. Iron ore TIO=F IS '
                  'free but only from 2010-10-14 and is scoped to AUD, which '
                  'gold already covers. Recorded as untestable rather than '
                  'tested badly.',
         files='driver_separation_e.txt'),
]

CONCLUSION = """THE DRIVER PROGRAMME, CLOSED -- THE FREE UNIVERSE IS NOW FULLY TESTED
==============================================================================

WHAT WAS TESTED. Six external drivers against the regime classifier, each on the
same terms: does it read differently across trending, ranging and crisis days,
now. Lag one bar, in-sample 1999-2015 chooses, holdout 2016-2026 is read once,
episodes not bars, circular-shift null with 50 draws, and a sub-period split of
the holdout run BEFORE any pass is reported.

THE RESULT. One keeper out of six.

  1 rate differential momentum   DEAD        sub-period sign flip
  2 MOVE bond volatility         KEEPER      held sign everywhere
  3 equity correlation           DEAD        sign flip between halves
  4 yield curve shape            DEAD        sign flip, halves and sub-periods
  5 commodities (oil, gold)      DEAD        sub-period sign flip
  5b NZD commodities             UNTESTABLE  no free data exists
  6 CFTC positioning (COT)       DEAD        sign flips on every reading

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

POSITIONING WAS THE LAST FREE GAP, AND IT IS NOW CLOSED. Drivers 1-5 were all
prices of other assets. The standing objection was that predictive value, if it
existed anywhere free, would live in POSITIONING rather than realised prices.
CFTC COT tested that directly and it died like the rest -- and it died on the
same fault, not a new one: every reading reverses between blocks or sub-periods.

Three things are worth keeping from that run rather than just the verdict.

  The lag is what would have faked it. COT reports Tuesday positions on Friday
  afternoon, so a Tuesday reading is not usable until the following Monday --
  seven calendar days, not two. Anyone quoting a positioning result should be
  asked which date they used.

  Weekly data against a daily classifier costs less than expected, and coverage
  costs more. The binding limit is not frequency: it is that CME FX futures are
  quoted against USD, so COT reaches 7 of 28 pairs and NO CROSS AT ALL, and NZD
  stops being reported after 2022-02-01.

  The one result that looked real is the clearest example of the programme's
  characteristic failure. |4-week change| separates ranging at +0.246 in-sample,
  p=0.020, and REVERSES to -0.193 on the holdout at p=0.078. It beats its null
  in both halves with opposite signs. That is a real magnitude attached to a
  sign that cannot be relied on, which is worse than noise, because noise does
  not look significant twice.

WHAT IS LEFT, AND IT IS ALL PAID:

  FX options risk reversals     The clearest measure of what the market pays for
                                protection -- the thing MOVE only approximates.
  Dealer / bank flow            Mostly not redistributable.
  Order book depth              Paid.

So the honest position is this: the free external universe has now been worked
through end to end, and it yields ONE confirmation signal and NO forecast.
Anything further requires paid options data. Layer 1 remains what it always was:
a view of the current regime, never judged on prediction.
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
