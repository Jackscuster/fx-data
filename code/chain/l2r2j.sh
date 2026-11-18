#!/bin/bash
# LAYER 2 RESTART, CHAIN 11 (HANDOFF 0l): FINISH MODE A. Books are on disk.
#
# Chain 9's `a9 wait books` failed because `a8 books A` failed at 09:40 on a
# filename mismatch I caused by editing l2r2book.py WHILE chain 8 was running
# it: macOS multiprocessing SPAWNS, so the pool's workers re-imported the edited
# module and wrote books_s4_of8_*.npz while the parent, holding the old module,
# looked for books_s4_*.npz. No compute was lost -- the parts were renamed to the
# new convention and the books re-summed, recomputing only the shard that had
# been quarantined earlier.
#
# deliverable = /Users/jackcuster/fx-data/results/r2gate2/MODEA_REPORT.md
#
# --- CHECKPOINT AND DEPENDENCY DECLARATIONS ---
# ckpt  aB endtoend  =  60   # the one-minute book save/read/resume test; runs FIRST
# ckpt  aB stop B    =   0   # waits for B's next checkpoint then stops it; holds no compute
# ckpt  aB books chk =   0   # asserts the books csv is present and complete; holds no compute
# ckpt  aB nulls     = 300   # per-worker null part files, one per (step, shard)
# ckpt  aB report    =   0   # reads the csvs and writes MODEA_REPORT.md in one pass
# ckpt  aB app       =   0   # rewrites app_data.json and app_ui.js in one pass
# ckpt  aB node      =   0   # node --check, seconds
# ckpt  aB resume B  = 300   # Checkpointer per worker, 32 shards, resumes by set difference
# needs aB endtoend  = none
# needs aB stop B    = none
# needs aB books chk = none
# needs aB nulls     = aB endtoend, aB stop B, aB books chk
# needs aB report    = aB books chk
# needs aB app       = none
# needs aB node      = aB app
# needs aB resume B  = none
. "${FX_CHAIN_LIB:-/Users/jackcuster/fx-data/code/chain/chainlib.sh}" "$0" "L2 RESTART CHAIN 11 COMPLETE"
cd /Users/jackcuster/fx-data
export FX_COST_TABLE=results/cost_table_h22.csv
export FX_CKPT_SECONDS=300

say "=== LAYER 2 RESTART CHAIN 11: finish mode A at full power, then resume B ==="

g "aB endtoend" nice -n 19 python3 code/l2r2book.py --stage endtoend --mode A --tag full --n 16 --jobs 2

g "aB stop B" bash -c '
L="$HOME/fx-data-logs/batch1.log"
if ! pgrep -f "l2r2gate2.py --stage run" >/dev/null; then echo "  mode B is not running"; exit 0; fi
n0=$(grep -c "ckpt shard_" "$L")
echo "  waiting for mode B to flush its next checkpoint (<= 300 s)..."
for i in $(seq 1 40); do
  sleep 15
  n1=$(grep -c "ckpt shard_" "$L")
  if [ "$n1" -gt "$n0" ]; then echo "  mode B flushed; stopping it"; break; fi
done
pkill -f "l2r2i.sh"
for p in $(pgrep -f "l2r2gate2.py --stage run"); do pkill -P $p 2>/dev/null; done
pkill -f "l2r2gate2.py --stage run"; sleep 4
pkill -9 -f "l2r2gate2.py --stage run" 2>/dev/null; sleep 2
python3 -c "
import sys; sys.path.insert(0,\"code\")
import l2r2gate2 as G2
d=G2.banked_idx(\"B\",\"full\")
print(\"  mode B stopped at %d of 273,780 banked (%.1f%%); resumes by set difference\"%(len(d),100*len(d)/273780))"'

g "aB books chk" nice -n 19 python3 -c "
import sys, os; sys.path.insert(0,'code')
import pandas as pd
f='results/r2gate2/modeA_books_full.csv'
assert os.path.exists(f), f+' is missing'
d=pd.read_csv(f)
print('  books: %d rows, %d steps, %d books, %d budgets, %d members'
      %(len(d), d.step.nunique(), d.book.nunique(), d.budget.nunique(), int(d.members.max())))
assert len(d)==40 and int(d.members.max())==273780, 'books csv is not the full field'"

g "aB nulls" nice -n 19 python3 code/l2r2null2.py --stage nulls --mode A --tag full --jobs 8 \
   --sizes 5000,20000 --draws 20 --id-draws 200
ci "Mode A books: the three nulls -- identity on the full field, regime-shuffle and random-entry on stratified samples at 5,000 and 20,000"

g "aB report" nice -n 19 python3 code/l2r2modearep.py --mode A --tag full
ci "MODE A REPORT: results/r2gate2/MODEA_REPORT.md, every number quoted from a named file with its row count and md5"

g "aB app"  nice -n 19 python3 code/r2app.py --stage app
g "aB node" node --check app_ui.js
ci "Mode A books and report wired into the app"

g "aB resume B" nice -n 19 python3 code/l2r2gate2.py --stage run --mode B --n 273780 --tag full --jobs 8 --nshard 32 --cap 30000
ci "GATE 2 MODE B resumed and complete: all 273,780 strategies tuned"

chain_summary
say "L2 RESTART CHAIN 11 COMPLETE"
