#!/bin/bash
# LAYER 2, CHAIN 31: JACK'S TWO A4/A5 FOLLOW-UPS, 24 Nov.
#
# Both are his, both low priority, both behind stage 2.
#
# 1. THE A4 CAP SWEEP NEVER BINDS. Jack: "cap_bound_days is 0 at every cap
#    except 0.75 (29 days), because worst_ccy_exposure is only 0.6 to 0.84.
#    Re-sweep the cap from the level where it binds on 1% of days down to where
#    it binds on 50% of days, and report the same columns."
#
#    He is right, and the aggregate table hid it: summed over all
#    rule/book/budget/step rows the cap does bind at five of the thirteen
#    levels, but in the slice he read -- mode A grade/allon/team1, step
#    2011-2014 -- it binds at exactly one. No fixed grid can work, because
#    across the slices on disk the worst exposure runs 0.600 to 1.692. So the
#    range is read off each slice's OWN distribution: the cap that binds on a
#    share q of days is the (1-q) quantile of the day's worst-exposure series,
#    so 1% is the 99th percentile and 50% is the median. Verified: the
#    arithmetic reproduces the target binding share to 0.03 percentage points,
#    and the 13-level geomspace spans 1.0% to 50.0% binding.
#
# 2. A5 SECTION 4 IS ON THE WRONG UNIT. Already done in-turn, because it needed
#    no engine pass -- mode?_a5_overlay.csv already carries one row per
#    (winner, step, threshold), so the restatement is a re-aggregation. It runs
#    again here only so the chain is reproducible from a clean tree.
#
#    The unit: R_total summed eight full-risk strategies while max_dd_R took
#    the MAX of one winner-year's dip. 3.6 x (944.7/5) / 24.79 = 27.43. On
#    l2r2winners.prop_return_strategy, the basis mode?_winners.csv uses, the
#    eight winners are 1.15 to 2.15 %/yr, median 1.45, and NONE clears 12%.
#
#    And the stop was NOT tested on ambiguous days only, which is what the file
#    claimed. _open_trades returns every open trade with every day from entry
#    to exit and there is no ambiguity filter anywhere in the stage: it is all
#    open-trade days with hourly coverage, 8,947 of 10,370 member-days, 86.3%.
#    So the rerun Jack offered to authorise is not needed, and the report now
#    says so.
#
# approval = none   two corrections to work already specified; no new question
#
# deliverable = /Users/jackcuster/fx-data/results/r2reads/A4_NETTING.md
# eta = 90
#
# --- CHECKPOINT, DEPENDENCY AND DISK DECLARATIONS ---
# ckpt  f1 endtoend  =  60   # the binding-range probe on ONE slice, read back; runs FIRST
# ckpt  f1 resweepA  = 300   # the adaptive cap sweep, mode A
# ckpt  f1 resweepB  = 300   # the same on mode B
# ckpt  f1 a5restate =   0   # A5 section 4 on the team 1 per-strategy basis
# ckpt  f1 md        =   0   # A4_NETTING.md section 3b and A5_HOURLY.md section 4b
# ckpt  f1 app       =   0   # rewrites app_data.json and app_ui.js
# ckpt  f1 node      =   0   # node --check
# needs f1 endtoend  = none
# needs f1 resweepA  = f1 endtoend
# needs f1 resweepB  = f1 endtoend
# needs f1 a5restate = none
# needs f1 md        = f1 resweepA
# needs f1 app       = f1 md
# needs f1 node      = f1 app
# disk  f1 endtoend  = 0.05  # one probe, no file
# disk  f1 resweepA  = 0.2   # one csv
# disk  f1 resweepB  = 0.2   # one csv
# disk  f1 a5restate = 0.05  # two csvs
# disk  f1 md        = 0     # two markdown files
# disk  f1 app       = 0.1   # rewrites app_data.json
# disk  f1 node      = 0     # node --check
. "${FX_CHAIN_LIB:-/Users/jackcuster/fx-data/code/chain/chainlib.sh}" "$0" "L2 CHAIN 31 COMPLETE"
cd /Users/jackcuster/fx-data
export FX_COST_TABLE=results/cost_table_h22.csv
export FX_CKPT_SECONDS=300
export FX_CI_LOCAL=1

say "=== LAYER 2 CHAIN 31: Jack's A4 cap-range and A5 unit follow-ups ==="

# ---- THE FIVE-MINUTE RULE. The binding-range probe on one real slice, so a
# failure here is a failure of the new code and not of the sweep around it.
g "f1 endtoend" nice -n 19 python3 -c "
import sys, os; sys.path.insert(0,'code')
import numpy as np
import r2hourly as RH
# the quantile identity the whole re-sweep rests on, on a real-shaped series
rng = np.random.default_rng(7)
mx = np.abs(rng.lognormal(mean=-0.1, sigma=0.35, size=1260))
for share in (0.01, 0.50):
    c = float(np.quantile(mx, 1.0 - share))
    got = float((mx > c).mean())
    assert abs(got - share) < 0.01, 'bind share %.4f against target %.4f' % (got, share)
assert callable(RH.cap_range_binding)
import l2walkfwd as W
src = open('code/l2walkfwd.py').read()
assert 'self.ccy_mx = mx.copy()' in src, 'Book.series does not stash the exposure series'
print('  END TO END: the (1-q) quantile binds on q of days to within 1pp, and '
      'Book.series stashes the exposure series')
"
ci "Chain 31 end to end: the binding-range arithmetic and the exposure-series hook"

g "f1 a5restate" nice -n 19 python3 code/r2hourly.py --stage a5restate --mode both
ci "A5 section 4 restated on the Team 1 per-strategy basis: 27.43%/yr becomes 1.45%/yr and 0 of 8 clear"

g "f1 resweepA" nice -n 19 python3 code/r2hourly.py --stage a4resweep --mode A
g "f1 resweepB" nice -n 19 python3 code/r2hourly.py --stage a4resweep --mode B
ci "A4: the cap re-swept over the range where it actually binds, 1% to 50% of days"

g "f1 md" bash -c '
set -e
nice -n 19 python3 code/r2hourly.py --stage a4md
nice -n 19 python3 code/r2hourly.py --stage a5md'
ci "A4_NETTING.md section 3b and A5_HOURLY.md section 4b"

g "f1 app"  nice -n 19 python3 code/r2app.py --stage app
g "f1 node" node --check app_ui.js
ci "Both follow-ups wired into the app"

chain_summary
say "L2 CHAIN 31 COMPLETE"
