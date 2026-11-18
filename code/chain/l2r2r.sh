#!/bin/bash
# LAYER 2 RESTART, CHAIN 16 (HANDOFF 0l): GATE 3 ON MODE A, THEN MODE B BOOKS,
# THEN THE MODE B FINISH -- ONE LAUNCH so nothing idles between them.
#
# Jack, 18 Nov: "Queue the mode B books and mode B finish chains directly behind
# it in the same launch so nothing idles."
#
# THE B STAGES DO NOT DEPEND ON THE GATE 3 STAGES. If gate 3 loses a stage the
# ledger records it, its dependents are skipped, and mode B still runs -- which
# is the whole point of declaring dependencies rather than ordering by hope.
#
# WHY THIS SUPERSEDES THE THREE SEPARATE DRIVERS. Gate 3's scorer sharded on
# `jobs`, so one slow shard held the stage: measured on the first 125 strategies
# of each shard the rates spread 1.00-1.89 s/strategy and the slowest projected
# 1,385 min against the fastest's 568 -- 23 h for 8 h of work. nshard is now 4x
# jobs, the same fix gate 2 already carries.
#
# deliverable = /Users/jackcuster/fx-data/results/r2gate2/MODEB_REPORT.md
# eta = 900
#
# --- CHECKPOINT, DEPENDENCY AND DISK DECLARATIONS ---
# ckpt  g3 endtoend  =  60   # 8 strategies through score -> report -> md; runs FIRST
# ckpt  g3 score A   = 300   # per-worker KPI parts flushed on the 300 s clock, resume by set difference
# ckpt  g3 report A  =   0   # reads the KPI bank, applies the bars, writes the csvs and the md
# ckpt  g3 book A    = 300   # the passers' book, routed and always-on, part files on the clock
# ckpt  g3 md A      =   0   # regenerates MODEA_GATE3.md with the book section filled in
# ckpt  g3 app       =   0   # rewrites app_data.json and app_ui.js in one pass
# ckpt  g3 node      =   0   # node --check, seconds
# needs g3 endtoend  = none
# needs g3 score A   = g3 endtoend
# needs g3 report A  = g3 score A
# needs g3 book A    = g3 report A
# needs g3 md A      = g3 report A
# needs g3 app       = none
# needs g3 node      = g3 app
# disk  g3 endtoend  = 0.1   # 8 strategies of KPI parts
# disk  g3 score A   = 1.1   # (273,780 x 4 x 5 x 10 x 9) float32 KPI blocks, sharded
# disk  g3 report A  = 0.2   # five csvs and one markdown
# disk  g3 book A    = 1.2   # five steps of per-shard book parts for the passers only
# disk  g3 md A      = 0     # one markdown file
# disk  g3 app       = 0.1   # rewrites app_data.json
# disk  g3 node      = 0     # node --check
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
. "${FX_CHAIN_LIB:-/Users/jackcuster/fx-data/code/chain/chainlib.sh}" "$0" "L2 RESTART CHAIN 16 COMPLETE"
cd /Users/jackcuster/fx-data
export FX_COST_TABLE=results/cost_table_h22.csv
export FX_CKPT_SECONDS=300

say "=== LAYER 2 RESTART CHAIN 16: gate 3 mode A, then mode B books, then the mode B finish ==="

g "g3 endtoend" bash -c '
set -e
rm -rf results/r2gate2/modeA_gate3parts_e2e
nice -n 19 python3 code/l2r2gate3.py --stage score --mode A --jobs 2 --cap 8000 --n 8
nice -n 19 python3 code/l2r2gate3.py --stage report --mode A --draws 10
test -s results/r2gate2/MODEA_GATE3.md
echo "  END TO END: score -> report -> md all wrote, MODEA_GATE3.md $(wc -l < results/r2gate2/MODEA_GATE3.md) lines"'

g "g3 score A" nice -n 19 python3 code/l2r2gate3.py --stage score --mode A --jobs 8 --nshard 32 --cap 30000
ci "Gate 3 mode A: every gate 2 winner re-scored per calendar year through the shipped Scorer, so Sortino, Calmar and chronological max DD exist"

g "g3 report A" nice -n 19 python3 code/l2r2gate3.py --stage report --mode A --draws 200
ci "GATE 3 MODE A: the bars on the grade year, the identity null on the year roles, and the stitched 2016-2020 record"

g "g3 book A" nice -n 19 python3 code/l2r2gate3.py --stage book --mode A --jobs 8
ci "Gate 3 mode A: the passers' book, equal weight, routed and always-on, walked forward with the three nulls"

g "g3 md A" nice -n 19 python3 code/l2r2gate3.py --stage md --mode A
ci "MODEA_GATE3.md complete, every number quoted from a named file"

g "g3 app"  nice -n 19 python3 code/r2app.py --stage app
g "g3 node" node --check app_ui.js
ci "Gate 3 mode A wired into the app"


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
say "L2 RESTART CHAIN 16 COMPLETE"
