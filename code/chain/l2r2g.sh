#!/bin/bash
# LAYER 2 RESTART, CHAIN 7 (HANDOFF 0l): FILL THE MODE A TAIL, THEN MODE B TUNING.
#
# WHY THIS EXISTS TONIGHT. Mode A's shard 06 drew strategies with 629
# configurations against the field's 494 average and runs ~2 h past the other
# seven, which would idle 7 of 8 cores from 23:38. The bank was 97.4% complete
# at 22:59 with 7,120 strategies missing, all inside shard 06's remaining
# range. `fill` completes the bank from the END backwards with the freed cores,
# so the bank is done ~23:30 instead of 01:23 and the mode A book chain is
# unblocked two hours earlier.
#
# ORDER. Jack, 17 Nov: mode A results come first, but if the book chain is not
# ready when tuning ends, start mode B tuning so nothing idles and run the mode
# A books ahead of B's BOOKS. The book chain is not ready, so mode B tuning
# runs here and the mode A books are launched over it the moment they are --
# mode B tuning checkpoints every 300 s, so interrupting it costs at most that.
#
# --- CHECKPOINT AND DEPENDENCY DECLARATIONS ---
# ckpt  g7 endtoend   =  60   # the one-minute save/read/resume test; runs FIRST
# ckpt  g7 fill A     = 300   # l2ckpt.Checkpointer per worker, resume by set difference
# ckpt  g7 bank check =   0   # counts banked indices, writes one line; holds no compute
# ckpt  g7 tune B     = 300   # Checkpointer per worker, 32 shards over 8 jobs so no straggler idles the box
# ckpt  g7 app        =   0   # rewrites app_data.json and app_ui.js in one pass
# ckpt  g7 node       =   0   # node --check, seconds
# needs g7 endtoend   = none
# needs g7 fill A     = none
# needs g7 bank check = none
# needs g7 tune B     = g7 endtoend
# needs g7 app        = none
# needs g7 node       = g7 app
. "${FX_CHAIN_LIB:-/Users/jackcuster/fx-data/code/chain/chainlib.sh}" "$0" "L2 RESTART CHAIN 7 COMPLETE"
cd /Users/jackcuster/fx-data
export FX_COST_TABLE=results/cost_table_h22.csv
export FX_CKPT_SECONDS=300

say "=== LAYER 2 RESTART CHAIN 7: fill the mode A tail, then mode B gate 2 tuning ==="
say "free space: $(df -h /System/Volumes/Data | tail -1 | awk '{print $4}')"

g "g7 endtoend" nice -n 19 python3 code/l2r2gate2.py --stage endtoend --mode A --n 12 --jobs 2

# 6 workers, and it waits until mode A's own pool has shrunk to 3 so the box is
# never oversubscribed. Nothing is deleted: it only banks what is missing.
g "g7 fill A" nice -n 19 python3 code/l2r2gate2.py --stage fill --mode A --tag full --jobs 6 --cap 30000 --wait-free 3

g "g7 bank check" nice -n 19 python3 -c "
import sys; sys.path.insert(0,'code')
import l2sweep as S, l2r2gate2 as G2
tot=S.n_combos(S.mode_opts(S.slot_options(),'A'))
d=G2.banked_idx('A','full')
print('  MODE A BANK: %d of %d strategies (%.2f%%), %d missing'%(len(d),tot,100*len(d)/tot,tot-len(d)))
sys.exit(0 if len(d)==tot else 1)"
ci "Mode A gate 2 bank completed by the tail filler: shard 06's 629-configuration strategies no longer hold the box"

g "g7 tune B" nice -n 19 python3 code/l2r2gate2.py --stage run --mode B --n 273780 --tag full --jobs 8 --nshard 32 --cap 30000
ci "GATE 2 MODE B: all 273,780 strategies tuned on the one-pass banked path, 32 shards over 8 workers so no straggler idles the box"

g "g7 app"  nice -n 19 python3 code/r2app.py --stage app
g "g7 node" node --check app_ui.js
ci "Mode B gate 2 wired into the app"

chain_summary
say "L2 RESTART CHAIN 7 COMPLETE"
