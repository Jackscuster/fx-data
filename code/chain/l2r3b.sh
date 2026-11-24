#!/bin/bash
# LAYER 2 RESTART, CHAIN 24: CHUNK 2 — A2 TUNED VS DEFAULT, A1 ON DEFAULTS, A3.
#
# Jack, 23-24 Nov. A2 and A1-on-defaults share ONE engine pass: the gate 2 bank
# stores only the winner's per-year record, so the gate 1 default has none and
# must be scored. 2 configurations per strategy against 547 in a tune, ~0.4%.
# A3 is a pure read of the saved daily series.
#
# LOCAL-ONLY COMMITS while the batched push of the rewritten history lands.
#
# approval = none   one small engine pass plus bank reads and report generation, all specified by Jack on 23-24 Nov
#
# deliverable = /Users/jackcuster/fx-data/results/r2reads/A2_A3_TUNED_AND_SIGNIFICANCE.md
# eta = 420
#
# --- CHECKPOINT, DEPENDENCY AND DISK DECLARATIONS ---
# ckpt  c2 endtoend  =  60   # A2 default pass on 40 strategies, saved and read back; runs FIRST
# ckpt  c2 a3        =   0   # block bootstrap on the saved daily series, no engine
# ckpt  c2 a2 A      = 300   # the default configuration scored, 32 shards, part csv per shard
# ckpt  c2 a2 B      = 300   # the same on mode B
# ckpt  c2 cmp A     =   0   # tuned minus default, plus A1 on defaults
# ckpt  c2 cmp B     =   0   # the same on mode B
# ckpt  c2 app       =   0   # rewrites app_data.json and app_ui.js
# ckpt  c2 node      =   0   # node --check
# ckpt  c2 push      =   0   # pushes Jack's phone
# needs c2 endtoend  = none
# needs c2 a3        = none
# needs c2 a2 A      = c2 endtoend
# needs c2 a2 B      = c2 endtoend
# needs c2 cmp A     = c2 a2 A
# needs c2 cmp B     = c2 a2 B
# needs c2 app       = none
# needs c2 node      = c2 app
# needs c2 push      = none
# disk  c2 endtoend  = 0.1   # one csv on a slice
# disk  c2 a3        = 0.1   # one csv
# disk  c2 a2 A      = 0.6   # 32 shard csvs then one concatenated csv
# disk  c2 a2 B      = 0.6   # the same on mode B
# disk  c2 cmp A     = 0.2   # two csvs and one markdown
# disk  c2 cmp B     = 0.2   # the same on mode B
# disk  c2 app       = 0.1   # rewrites app_data.json
# disk  c2 node      = 0     # node --check
# disk  c2 push      = 0     # one http request
. "${FX_CHAIN_LIB:-/Users/jackcuster/fx-data/code/chain/chainlib.sh}" "$0" "L2 RESTART CHAIN 24 COMPLETE"
cd /Users/jackcuster/fx-data
export FX_COST_TABLE=results/cost_table_h22.csv
export FX_CKPT_SECONDS=300
export FX_CI_LOCAL=1

say "=== LAYER 2 RESTART CHAIN 24: chunk 2, A2 tuned vs default, A1 on defaults, A3 ==="

g "c2 endtoend" bash -c '
set -e
nice -n 19 python3 code/r2reads.py --stage a2 --mode A --jobs 2 --nshard 2 --nmax 40
test -s results/r2reads/modeA_a2_defaults.csv
echo "  END TO END: the default pass wrote and read back, $(wc -l < results/r2reads/modeA_a2_defaults.csv) rows"'

g "c2 a3" nice -n 19 python3 code/r2reads.py --stage a3 --mode A --draws 2000
ci "A3: yearly return over vol, worst dip, and a 20-day block-bootstrap t beside the naive daily t"

g "c2 a2 A" nice -n 19 python3 code/r2reads.py --stage a2 --mode A --jobs 8 --nshard 32
g "c2 cmp A" nice -n 19 python3 code/r2reads.py --stage a2cmp --mode A
ci "A2 mode A: tuned minus default on the unseen years, and A1 repeated on the defaults"

g "c2 a2 B" nice -n 19 python3 code/r2reads.py --stage a2 --mode B --jobs 8 --nshard 32
g "c2 cmp B" nice -n 19 python3 code/r2reads.py --stage a2cmp --mode B
ci "A2 mode B: the same"

g "c2 app"  nice -n 19 python3 code/r2app.py --stage app
g "c2 node" node --check app_ui.js
ci "Chunk 2 wired into the app"

g "c2 push" nice -n 19 python3 code/l2r2push.py --what "chunk 2: A2, A1-on-defaults, A3" \
   --file results/r2reads/A2_A3_TUNED_AND_SIGNIFICANCE.md

chain_summary
say "L2 RESTART CHAIN 24 COMPLETE"
