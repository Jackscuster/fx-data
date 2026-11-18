#!/bin/bash
# LAYER 2 RESTART, CHAIN 8 (HANDOFF 0l): MODE A BOOKS AT FULL POWER.
#
# Jack, 18 Nov: one task at a time at full power. Mode B tuning is only a
# filler; the moment the A book chain passes its end-to-end test, B is paused
# at its next checkpoint and the A chain gets all 8 workers until
# MODEA_REPORT.md is committed. The end-to-end test passed at 09:04.
#
# Mode B is STOPPED, not abandoned: it is 91.9% banked and checkpoints every
# 300 s, so it resumes by set difference losing at most five minutes.
#
# --- CHECKPOINT AND DEPENDENCY DECLARATIONS ---
# ckpt  a8 endtoend = 60   # the one-minute book save/read/resume test; runs FIRST
# ckpt  a8 stop B   = 0    # waits for B's next checkpoint then stops it; holds no compute
# ckpt  a8 books A  = 300  # per-worker part files flushed on the 300 s clock, resume by set difference
# needs a8 endtoend = none
# needs a8 stop B   = a8 endtoend
# needs a8 books A  = a8 endtoend, a8 stop B
. "${FX_CHAIN_LIB:-/Users/jackcuster/fx-data/code/chain/chainlib.sh}" "$0" "L2 RESTART CHAIN 8 COMPLETE"
cd /Users/jackcuster/fx-data
export FX_COST_TABLE=results/cost_table_h22.csv
export FX_CKPT_SECONDS=300

say "=== LAYER 2 RESTART CHAIN 8: MODE A BOOKS, ALL 8 WORKERS ==="

g "a8 endtoend" nice -n 19 python3 code/l2r2book.py --stage endtoend --mode A --tag full --n 16 --jobs 2

g "a8 stop B" bash -c '
L="$HOME/fx-data-logs/batch1.log"
if ! pgrep -f "l2r2g.sh" >/dev/null; then echo "  mode B is not running; nothing to stop"; exit 0; fi
n0=$(grep -c "ckpt shard_" "$L")
echo "  waiting for mode B to flush its next checkpoint (<= 300 s) so nothing is lost..."
for i in $(seq 1 40); do
  sleep 15
  n1=$(grep -c "ckpt shard_" "$L")
  if [ "$n1" -gt "$n0" ]; then echo "  mode B flushed a checkpoint; stopping it now"; break; fi
done
pkill -f "l2r2g.sh"
for p in $(pgrep -f "l2r2gate2.py --stage run"); do pkill -P $p 2>/dev/null; done
pkill -f "l2r2gate2.py --stage run"; sleep 4
pkill -9 -f "l2r2gate2.py --stage run" 2>/dev/null; sleep 2
if pgrep -f "l2r2gate2.py --stage run" >/dev/null; then echo "  !! mode B workers survived"; exit 1; fi
python3 -c "
import sys; sys.path.insert(0,\"code\")
import l2r2gate2 as G2
d=G2.banked_idx(\"B\",\"full\")
print(\"  mode B stopped cleanly at %d of 273,780 banked (%.1f%%); it resumes by set difference\"%(len(d),100*len(d)/273780))"
'

g "a8 books A" nice -n 19 python3 code/l2r2book.py --stage books --mode A --tag full --jobs 8 --out-tag full
ci "MODE A BOOKS: all 273,780 strategies through the four 0f routing variants, five steps, both budgets, streamed"

chain_summary
say "L2 RESTART CHAIN 8 COMPLETE"
