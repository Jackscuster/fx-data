#!/bin/bash
# LAYER 2 RESTART, CHAIN 25: chunk 3, A5 the hourly path.
#
# Jack, 24 Nov. Local-only commits while the batched push lands.
#
# approval = none   bank and data reads on the 10 winners plus report generation, specified by Jack on 23-24 Nov
#
# deliverable = /Users/jackcuster/fx-data/results/r2reads/modeA_a5_hourly.csv
# eta = 120
#
# A5 REPLAYS THE AMBIGUOUS DAYS ONLY. A daily bar whose high reaches the target
# AND whose low reaches the stop is a guess; the hourly file settles it. On an
# unambiguous day hourly data cannot disagree, so replaying it would burn I/O
# to confirm arithmetic. Smoked on one winner: 11 ambiguous trade-days, all 11
# resolved -- 6 stop first, 5 target first.
#
# TWO-SIDED COVERAGE STARTS LATER THAN ONE PAIR SUGGESTS. Per pair, 11 pairs
# from 2002-05-06/07, NZDUSD 2002-09-23, and 17 pairs only from 2004-05-31. The
# BINDING date for a 28-pair strategy is 2004-05-31, which is what the project
# overview said; a check on EURUSD alone says 2002 and misleads.
#
# --- CHECKPOINT, DEPENDENCY AND DISK DECLARATIONS ---
# ckpt  c3 endtoend  =  60   # A5 on one winner, saved and read back; runs FIRST
# ckpt  c3 cover     =   0   # per-pair two-sided start dates
# ckpt  c3 a5 A      = 300   # the ambiguous-day replay on mode A's 8 winners
# ckpt  c3 a5 B      = 300   # the same on mode B's 2
# ckpt  c3 app       =   0   # rewrites app_data.json and app_ui.js
# ckpt  c3 node      =   0   # node --check
# ckpt  c3 push      =   0   # pushes Jack's phone
# needs c3 endtoend  = none
# needs c3 cover     = none
# needs c3 a5 A      = c3 endtoend
# needs c3 a5 B      = c3 endtoend
# needs c3 app       = none
# needs c3 node      = c3 app
# needs c3 push      = none
# disk  c3 endtoend  = 0.1   # one csv on one winner
# disk  c3 cover     = 0     # one small csv
# disk  c3 a5 A      = 0.2   # one csv
# disk  c3 a5 B      = 0.2   # one csv
# disk  c3 app       = 0.1   # rewrites app_data.json
# disk  c3 node      = 0     # node --check
# disk  c3 push      = 0     # one http request
. "${FX_CHAIN_LIB:-/Users/jackcuster/fx-data/code/chain/chainlib.sh}" "$0" "L2 RESTART CHAIN 25 COMPLETE"
cd /Users/jackcuster/fx-data
export FX_COST_TABLE=results/cost_table_h22.csv
export FX_CKPT_SECONDS=300
export FX_CI_LOCAL=1

say "=== LAYER 2 RESTART CHAIN 25: chunk 3, A5 the hourly path ==="

g "c3 endtoend" bash -c '
set -e
nice -n 19 python3 code/r2hourly.py --stage a5 --mode A --winners 1
test -s results/r2reads/modeA_a5_hourly.csv
echo "  END TO END: A5 on one winner wrote and read back"'

g "c3 cover" nice -n 19 python3 -c "
import sys; sys.path.insert(0,'code')
import pandas as pd
d = pd.read_csv('results/r2reads/hourly_coverage.csv')
print('  two-sided hourly coverage: %d pairs, earliest %s, LATEST %s (the binding date)'
      % (len(d), d.two_sided_start.min(), d.two_sided_start.max()))
"

g "c3 a5 A" nice -n 19 python3 code/r2hourly.py --stage a5 --mode A
g "c3 a5 B" nice -n 19 python3 code/r2hourly.py --stage a5 --mode B
ci "A5: the ambiguous stop-versus-target days replayed on two-sided hourly quotes"

g "c3 app"  nice -n 19 python3 code/r2app.py --stage app
g "c3 node" node --check app_ui.js
ci "Chunk 3 wired into the app"

g "c3 push" nice -n 19 python3 code/l2r2push.py --what "chunk 3: A5 hourly path" \
   --file results/r2reads/modeA_a5_hourly.csv

chain_summary
say "L2 RESTART CHAIN 25 COMPLETE"
