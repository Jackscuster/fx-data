#!/bin/bash
# LAYER 2 RESTART, CHAIN 28: THE A4 AND A5 COMPLETION.
#
# Jack, 24 Nov: A4 and A5 were marked complete and their reports did not exist.
# Chains 25 and 26 reported 7/0 and 8/0 because the stages I DECLARED covered a
# fraction of what was specified. The winners'-book half of A4 and all four
# parts of A5 were built and run on 24 Nov; this chain carries the two pieces
# that need real compute:
#
#   1. THE GRADE-RULE BOOK PARTS, REBUILT. A4's whole-field half needs them and
#      the cache budget evicted them -- every one of the 81 part files in each
#      bookparts directory is pbook_winners_*. The grade book itself ran on
#      21 Nov and its csv is on record, but the cap sweep needs POSITIONS and
#      only the parts carry those; the 466 saved daily-series npz files carry R
#      alone. 12,450 members at step 1 of mode A, so this is a real book pass.
#
#   2. THE A5 OVERLAY AT FULL SIZE. The daily loss stop on hourly marks, swept
#      over 13 thresholds, all winners and all steps. Measured at 0.4 min per
#      winner-year on the smoke, so about 16 min per mode.
#
# approval = none   completing work already specified; no new question is asked
#
# deliverable = /Users/jackcuster/fx-data/results/r2reads/A4_NETTING.md
# eta = 420
#
# --- CHECKPOINT, DEPENDENCY AND DISK DECLARATIONS ---
# ckpt  a45 endtoend   =  60   # the cap sweep on the winners' book, which already works; runs FIRST
# ckpt  a45 pass A     =   0   # the grade pass mask, read-only off the KPI bank
# ckpt  a45 book A     = 300   # the grade-rule book parts, per-worker, resume by set difference
# ckpt  a45 pass B     =   0   # the same on mode B
# ckpt  a45 book B     = 300   # the same on mode B
# ckpt  a45 sweep A    = 300   # the cap sweep on winners AND whole field
# ckpt  a45 sweep B    = 300   # the same on mode B
# ckpt  a45 ov A       = 300   # the daily loss stop on hourly marks, swept
# ckpt  a45 ov B       = 300   # the same on mode B
# ckpt  a45 md         =   0   # A4_NETTING.md and A5_HOURLY.md
# ckpt  a45 app        =   0   # rewrites app_data.json and app_ui.js
# ckpt  a45 node       =   0   # node --check
# ckpt  a45 push       =   0   # pushes Jack's phone
# needs a45 endtoend   = none
# needs a45 pass A     = none
# needs a45 book A     = a45 pass A
# needs a45 pass B     = none
# needs a45 book B     = a45 pass B
# needs a45 sweep A    = a45 book A
# needs a45 sweep B    = a45 book B
# needs a45 ov A       = none
# needs a45 ov B       = none
# needs a45 md         = none
# needs a45 app        = none
# needs a45 node       = a45 app
# needs a45 push       = none
# disk  a45 endtoend   = 0.1   # two csvs on the winners' book
# disk  a45 pass A     = 0.1   # one npz mask
# disk  a45 book A     = 2.0   # the grade-rule book parts, 16 shards x 5 steps
# disk  a45 pass B     = 0.1   # one npz mask
# disk  a45 book B     = 2.0   # the same on mode B
# disk  a45 sweep A    = 0.3   # three csvs
# disk  a45 sweep B    = 0.3   # three csvs
# disk  a45 ov A       = 0.2   # two csvs
# disk  a45 ov B       = 0.2   # two csvs
# disk  a45 md         = 0     # two markdown files
# disk  a45 app        = 0.1   # rewrites app_data.json
# disk  a45 node       = 0     # node --check
# disk  a45 push       = 0     # one http request
. "${FX_CHAIN_LIB:-/Users/jackcuster/fx-data/code/chain/chainlib.sh}" "$0" "L2 RESTART CHAIN 28 COMPLETE"
cd /Users/jackcuster/fx-data
export FX_COST_TABLE=results/cost_table_h22.csv
export FX_CKPT_SECONDS=300
export FX_CI_LOCAL=1

say "=== LAYER 2 RESTART CHAIN 28: the A4 and A5 completion ==="

g "a45 endtoend" bash -c '
set -e
nice -n 19 python3 code/r2hourly.py --stage a4sweep --mode A
test -s results/r2reads/modeA_a4_capsweep.csv
test -s results/r2reads/modeA_a4_attribution.csv
echo "  END TO END: the cap sweep wrote and the attribution wrote"'

# ---- the grade-rule book parts, which the cache budget evicted
g "a45 pass A" nice -n 19 python3 code/l2r2gate3.py --stage passmask --mode A --rule grade
g "a45 book A" nice -n 19 python3 code/l2r2gate3.py --stage book --mode A --rule grade --jobs 8 --nshard 16
ci "A4: the grade-rule book parts rebuilt for mode A, which the cap sweep needs for positions"

g "a45 pass B" nice -n 19 python3 code/l2r2gate3.py --stage passmask --mode B --rule grade
g "a45 book B" nice -n 19 python3 code/l2r2gate3.py --stage book --mode B --rule grade --jobs 8 --nshard 16
ci "A4: the same on mode B"

g "a45 sweep A" nice -n 19 python3 code/r2hourly.py --stage a4sweep --mode A
g "a45 sweep B" nice -n 19 python3 code/r2hourly.py --stage a4sweep --mode B
ci "A4: the exposure cap swept over its full range on the winners' books AND the whole-field book"

# ---- the A5 overlay at full size
g "a45 ov A" nice -n 19 python3 code/r2hourly.py --stage a5ov --mode A
g "a45 ov B" nice -n 19 python3 code/r2hourly.py --stage a5ov --mode B
ci "A5: the daily loss stop on hourly marks, swept over 13 thresholds, all winners and all steps"

g "a45 md" bash -c '
set -e
nice -n 19 python3 code/r2hourly.py --stage a4md
nice -n 19 python3 code/r2hourly.py --stage a5md'
ci "A4_NETTING.md and A5_HOURLY.md regenerated on the full sweep"

g "a45 app"  nice -n 19 python3 code/r2app.py --stage app
g "a45 node" node --check app_ui.js
ci "A4 and A5 wired into the app"

g "a45 push" nice -n 19 python3 code/l2r2push.py --what "A4 and A5 completion" \
   --file results/r2reads/A4_NETTING.md

chain_summary
say "L2 RESTART CHAIN 28 COMPLETE"
