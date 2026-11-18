#!/bin/bash
# LAYER 2 RESTART, CHAIN 13 (HANDOFF 0l): MODE B BOOKS.
# Mode A is delivered: results/r2gate2/MODEA_REPORT.md, 513 lines, 12 sources, 0
# missing, committed 5fca4cd. Mode B gate 2 tuning completed at 13:22 (chain 11,
# ledger 8 succeeded 0 failed 0 skipped), so B's bank is whole and its books can
# run on the identical pipeline.
#
# deliverable = /Users/jackcuster/fx-data/results/r2gate2/modeB_books_full.csv
# eta = 90
#
# --- CHECKPOINT, DEPENDENCY AND DISK DECLARATIONS ---
# ckpt  b1 endtoend  =  60   # the one-minute book save/read/resume test on mode B; runs FIRST
# ckpt  b1 bank chk  =   0   # asserts mode B's bank is complete; holds no compute
# ckpt  b1 books B   = 300   # per-worker part files on the 300 s clock, resume by set difference
# ckpt  b1 app       =   0   # rewrites app_data.json and app_ui.js in one pass
# ckpt  b1 node      =   0   # node --check, seconds
# needs b1 endtoend  = none
# needs b1 bank chk  = none
# needs b1 books B   = b1 endtoend, b1 bank chk
# needs b1 app       = none
# needs b1 node      = b1 app
# disk  b1 endtoend  = 0.2   # 16 strategies of book parts
# disk  b1 bank chk  = 0     # reads the bank index
# disk  b1 books B   = 1.2   # five steps of per-shard book parts, float64 sums
# disk  b1 app       = 0.1   # rewrites app_data.json
# disk  b1 node      = 0     # node --check
. "${FX_CHAIN_LIB:-/Users/jackcuster/fx-data/code/chain/chainlib.sh}"
cd /Users/jackcuster/fx-data
export FX_COST_TABLE=results/cost_table_h22.csv
export FX_CKPT_SECONDS=300

say "=== LAYER 2 RESTART CHAIN 13: MODE B BOOKS, ALL 8 WORKERS ==="

g "b1 endtoend" nice -n 19 python3 code/l2r2book.py --stage endtoend --mode B --tag full --n 16 --jobs 2

g "b1 bank chk" nice -n 19 python3 -c "
import sys; sys.path.insert(0,'code')
import l2sweep as S, l2r2gate2 as G2
tot=S.n_combos(S.mode_opts(S.slot_options(),'B'))
d=G2.banked_idx('B','full')
print('  MODE B BANK: %d of %d strategies (%.2f%%), %d missing'%(len(d),tot,100*len(d)/tot,tot-len(d)))
sys.exit(0 if len(d)==tot else 1)"

g "b1 books B" nice -n 19 python3 code/l2r2book.py --stage books --mode B --tag full --jobs 8 --out-tag full
ci "MODE B BOOKS: all 273,780 strategies through the four 0f routing variants, five steps, both budgets, streamed"

g "b1 app"  nice -n 19 python3 code/r2app.py --stage app
g "b1 node" node --check app_ui.js
ci "Mode B books wired into the app"

chain_summary
say "L2 RESTART CHAIN 13 COMPLETE"
