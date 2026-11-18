#!/bin/bash
# LAYER 2 RESTART, CHAIN 14 (HANDOFF 0l): MODE B NULLS, GRADE, SPLITS, REPORTS,
# AND THE EPISODE-BASED quality_tag SPLIT FOR BOTH MODES.
#
# Mode B's books land in chain 13. This is the identical finish mode A had, plus
# the fix to a defect of mine: the quality_tag split counted MARK ROWS
# (2,464,696 high against 4,320,044 low), which weights a long episode more than
# a short one and is not comparable to LAYER1_INTERFACE.md section 4's episode
# rates (54.5% high n=110, 38.3% low n=188). Section 4 is a claim about
# EPISODES, so the test is now one episode, one observation -- rerun for mode A
# as well as computed for mode B, so the two are comparable.
#
# deliverable = /Users/jackcuster/fx-data/results/r2gate2/MODEB_REPORT.md
# eta = 150
#
# --- CHECKPOINT, DEPENDENCY AND DISK DECLARATIONS ---
# ckpt  b2 endtoend   =  60   # the one-minute book save/read/resume test on mode B; runs FIRST
# ckpt  b2 books chk  =   0   # asserts mode B's books csv is present and full-field; holds no compute
# ckpt  b2 nulls B    = 300   # per-worker null parts, one step at a time, removed once summed
# ckpt  b2 grade B    = 300   # blind grade from the bank plus both splits, mark-row and episode
# ckpt  b2 episodes A = 300   # the episode-based splits recomputed for mode A so A and B compare
# ckpt  b2 report B   =   0   # reads the csvs and writes MODEB_REPORT.md in one pass
# ckpt  b2 top30 B    =   0   # read-only reduction of the mode B bank, then MODEB_TOP30.md
# ckpt  b2 app        =   0   # rewrites app_data.json and app_ui.js in one pass
# ckpt  b2 node       =   0   # node --check, seconds
# needs b2 endtoend   = none
# needs b2 books chk  = none
# needs b2 nulls B    = b2 endtoend, b2 books chk
# needs b2 grade B    = b2 endtoend
# needs b2 episodes A = b2 endtoend
# needs b2 report B   = b2 books chk
# needs b2 top30 B    = none
# needs b2 app        = none
# needs b2 node       = b2 app
# disk  b2 endtoend   = 0.2   # 16 strategies of book parts
# disk  b2 books chk  = 0     # reads one csv
# disk  b2 nulls B    = 1.5   # one step of per-shard scratch at a time, float32, deleted once summed
# disk  b2 grade B    = 0.1   # two csvs
# disk  b2 episodes A = 0.1   # one csv rewritten
# disk  b2 report B   = 0     # one markdown file
# disk  b2 top30 B    = 0.2   # five csvs plus one markdown
# disk  b2 app        = 0.1   # rewrites app_data.json
# disk  b2 node       = 0     # node --check
. "${FX_CHAIN_LIB:-/Users/jackcuster/fx-data/code/chain/chainlib.sh}" "$0" "L2 RESTART CHAIN 14 COMPLETE"
cd /Users/jackcuster/fx-data
export FX_COST_TABLE=results/cost_table_h22.csv
export FX_CKPT_SECONDS=300

say "=== LAYER 2 RESTART CHAIN 14: mode B nulls, grade, reports, and episode-based splits for A and B ==="

g "b2 endtoend" nice -n 19 python3 code/l2r2book.py --stage endtoend --mode B --tag full --n 16 --jobs 2

g "b2 books chk" nice -n 19 python3 -c "
import sys, os; sys.path.insert(0,'code')
import pandas as pd
f='results/r2gate2/modeB_books_full.csv'
assert os.path.exists(f), f+' is missing -- chain 13 has not landed'
d=pd.read_csv(f)
print('  mode B books: %d rows, %d steps, %d books, %d budgets, %d members'
      %(len(d), d.step.nunique(), d.book.nunique(), d.budget.nunique(), int(d.members.max())))
assert len(d)==40 and int(d.members.max())==273780, 'not the full field'"

g "b2 nulls B" nice -n 19 python3 code/l2r2null2.py --stage nulls --mode B --tag full --jobs 8 \
   --sizes 5000,20000 --draws 20 --id-draws 200
ci "Mode B books: the three nulls -- identity on the full field, regime-shuffle and random-entry on stratified samples at 5,000 and 20,000"

g "b2 grade B" nice -n 19 python3 code/l2r2grade.py --mode B --tag full --n 4000
ci "Mode B books: the blind grade reported never used, plus the quality_tag and episode-third splits, mark-row and episode-based"

g "b2 episodes A" nice -n 19 python3 code/l2r2grade.py --mode A --tag full --n 4000
ci "Mode A splits recomputed with the episode-based test: one episode one observation, comparable to LAYER1_INTERFACE.md section 4"

g "b2 report B" nice -n 19 python3 code/l2r2modearep.py --mode B --tag full
ci "MODE B REPORT: results/r2gate2/MODEB_REPORT.md, every number quoted from a named file with its row count and md5"

g "b2 top30 B" nice -n 19 python3 code/l2r2top30.py --mode B --tag full --top 30
ci "MODEB_TOP30.md: top 30, persistence against a coin flip, field share, and what was known in advance"

g "b2 app"  nice -n 19 python3 code/r2app.py --stage app
g "b2 node" node --check app_ui.js
ci "Mode B books, nulls and reports wired into the app"

chain_summary
say "L2 RESTART CHAIN 14 COMPLETE"
