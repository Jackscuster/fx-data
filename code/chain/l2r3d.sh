#!/bin/bash
# LAYER 2 RESTART, CHAIN 26: chunk 4, A4 currency netting.
#
# Jack, 24 Nov. Local-only commits while the batched push lands.
#
# approval = none   bank and data reads on the 10 winners plus report generation, specified by Jack on 23-24 Nov
#
# deliverable = /Users/jackcuster/fx-data/results/r2reads/modeA_a4_currency_legs.csv
# eta = 90
#
# A4 PROJECTS THE BOOK ONTO EIGHT CURRENCY LEGS. The saved daily series is one
# netted number a day and cannot show whether a 28-pair book is actually
# currency-diversified. The book's accumulator is rebuilt (8 members, ~90 s)
# and its per-(pair, day) signed positions are projected: a long AUDJPY is long
# AUD and short JPY. Smoked on mode A: the largest single leg carries 34.3% of
# total absolute exposure on average and 50% at worst.
#
# IT REBUILDS THE BOOK FIRST, because modeA_gate3bookparts was deleted on
# 22 Nov to reclaim disk when the volume hit 100%. A book rebuilds from the
# bank in about 90 seconds measured.
#
# --- CHECKPOINT, DEPENDENCY AND DISK DECLARATIONS ---
# ckpt  c4 endtoend  =  60   # the winners book rebuilt and A4 run on it; runs FIRST
# ckpt  c4 book A    = 300   # the winners book parts, 8 members, resume by set difference
# ckpt  c4 a4 A      =   0   # projection onto the currency legs, no engine
# ckpt  c4 book B    = 300   # the same on mode B's 2 winners
# ckpt  c4 a4 B      =   0   # the same projection
# ckpt  c4 app       =   0   # rewrites app_data.json and app_ui.js
# ckpt  c4 node      =   0   # node --check
# ckpt  c4 push      =   0   # pushes Jack's phone
# needs c4 endtoend  = none
# needs c4 book A    = none
# needs c4 a4 A      = c4 book A
# needs c4 book B    = none
# needs c4 a4 B      = c4 book B
# needs c4 app       = none
# needs c4 node      = c4 app
# needs c4 push      = none
# disk  c4 endtoend  = 0.2   # book parts for 8 members
# disk  c4 book A    = 0.3   # 16 shards x 5 steps, 8 members
# disk  c4 a4 A      = 0.1   # two csvs
# disk  c4 book B    = 0.3   # the same on mode B
# disk  c4 a4 B      = 0.1   # two csvs
# disk  c4 app       = 0.1   # rewrites app_data.json
# disk  c4 node      = 0     # node --check
# disk  c4 push      = 0     # one http request
. "${FX_CHAIN_LIB:-/Users/jackcuster/fx-data/code/chain/chainlib.sh}" "$0" "L2 RESTART CHAIN 26 COMPLETE"
cd /Users/jackcuster/fx-data
export FX_COST_TABLE=results/cost_table_h22.csv
export FX_CKPT_SECONDS=300
export FX_CI_LOCAL=1

say "=== LAYER 2 RESTART CHAIN 26: chunk 4, A4 currency netting ==="

g "c4 endtoend" bash -c '
set -e
nice -n 19 python3 code/r2hourly.py --stage a4 --mode A
test -s results/r2reads/modeA_a4_currency_legs.csv
echo "  END TO END: A4 wrote and read back the currency legs"'

g "c4 book A" nice -n 19 python3 code/l2r2gate3.py --stage book --mode A --rule winners --jobs 8 --nshard 16
g "c4 a4 A"   nice -n 19 python3 code/r2hourly.py --stage a4 --mode A
ci "A4 mode A: the winners book projected onto the eight currency legs"

g "c4 book B" nice -n 19 python3 code/l2r2gate3.py --stage book --mode B --rule winners --jobs 8 --nshard 16
g "c4 a4 B"   nice -n 19 python3 code/r2hourly.py --stage a4 --mode B
ci "A4 mode B: the same"

g "c4 app"  nice -n 19 python3 code/r2app.py --stage app
g "c4 node" node --check app_ui.js
ci "Chunk 4 wired into the app"

g "c4 push" nice -n 19 python3 code/l2r2push.py --what "chunk 4: A4 currency netting" \
   --file results/r2reads/modeA_a4_currency_legs.csv

chain_summary
say "L2 RESTART CHAIN 26 COMPLETE"
