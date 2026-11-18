#!/bin/bash
# LAYER 2 RESTART, CHAIN 9 (HANDOFF 0l): FINISH MODE A, THEN RESUME B.
# Runs after chain 8's books land. One task at a time at full power.
#
# deliverable = /Users/jackcuster/fx-data/results/r2gate2/MODEA_REPORT.md
#
# --- CHECKPOINT AND DEPENDENCY DECLARATIONS ---
# ckpt  a9 endtoend  =  60   # the one-minute book save/read/resume test; runs FIRST
# ckpt  a9 wait books=   0   # polls for chain 8's books csv; holds no compute
# ckpt  a9 nulls     = 300   # per-worker null part files, one per (step, shard)
# ckpt  a9 grade     = 300   # blind grade from the bank + the two Layer 1 splits
# ckpt  a9 report    =   0   # reads the csvs and writes MODEA_REPORT.md in one pass
# ckpt  a9 app       =   0   # rewrites app_data.json and app_ui.js in one pass
# ckpt  a9 node      =   0   # node --check, seconds
# ckpt  a9 resume B  = 300   # Checkpointer per worker, 32 shards, resumes by set difference
# needs a9 endtoend  = none
# needs a9 wait books= none
# needs a9 nulls     = a9 endtoend, a9 wait books
# needs a9 grade     = a9 endtoend
# needs a9 report    = a9 wait books
# needs a9 app       = none
# needs a9 node      = a9 app
# needs a9 resume B  = none
. "${FX_CHAIN_LIB:-/Users/jackcuster/fx-data/code/chain/chainlib.sh}" "$0" "L2 RESTART CHAIN 9 COMPLETE"
cd /Users/jackcuster/fx-data
export FX_COST_TABLE=results/cost_table_h22.csv
export FX_CKPT_SECONDS=300
B=results/r2gate2/modeA_books_full.csv

say "=== LAYER 2 RESTART CHAIN 9: finish mode A, then resume mode B ==="

g "a9 endtoend" nice -n 19 python3 code/l2r2book.py --stage endtoend --mode A --tag full --n 16 --jobs 2

g "a9 wait books" bash -c '
B=results/r2gate2/modeA_books_full.csv
for i in $(seq 1 480); do
  [ -f "$B" ] && { echo "  books present: $(wc -l < $B) lines"; exit 0; }
  pgrep -f l2r2h.sh >/dev/null || { echo "  !! chain 8 is gone and $B was never written"; exit 1; }
  sleep 60
done
echo "  !! waited 8 h for $B"; exit 1'

g "a9 nulls" nice -n 19 python3 code/l2r2null2.py --stage nulls --mode A --tag full --jobs 8 \
   --sizes 5000,20000 --draws 20 --id-draws 200
ci "Mode A books: the three nulls -- identity on the full field, regime-shuffle and random-entry on stratified samples at 5,000 and 20,000"

g "a9 grade" nice -n 19 python3 code/l2r2grade.py --mode A --tag full --n 4000
ci "Mode A books: the blind grade reported never used, plus the quality_tag and episode-third splits on the routed trend slice"

g "a9 report" nice -n 19 python3 code/l2r2modearep.py --mode A --tag full
ci "MODE A REPORT: results/r2gate2/MODEA_REPORT.md, every number quoted from a named file with its row count and md5"

g "a9 app"  nice -n 19 python3 code/r2app.py --stage app
g "a9 node" node --check app_ui.js
ci "Mode A books and report wired into the app"

g "a9 resume B" nice -n 19 python3 code/l2r2gate2.py --stage run --mode B --n 273780 --tag full --jobs 8 --nshard 32 --cap 30000
ci "GATE 2 MODE B resumed and complete: all 273,780 strategies tuned"

chain_summary
say "L2 RESTART CHAIN 9 COMPLETE"
