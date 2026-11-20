#!/bin/bash
# LAYER 2 RESTART, CHAIN 18: GATE 3 ON MODE B, PART 4 FOR BOTH MODES, AND THE
# MODE B KPI TABLE -- ONE LAUNCH.
#
# Jack, 19 Nov: "(1) gate 3 on mode B, identical to A, with MODEB_GATE3.md;
# (2) write and run part 4 for A and B: the passers' book (everyone who cleared
# the bars on the grade year, equal weight, routed and always-on, traded on the
# trade year, full KPI table in the MODEA_KPIS.md format, three nulls);
# (3) a KPI table for mode B in the MODEA_KPIS.md format, committed."
#
# THE CHEAP DELIVERABLES RUN FIRST, AND COMMIT, BEFORE THE 6.7-HOUR STAGE.
# Part 4 on mode A and both KPI tables are minutes of work on banks that are
# already complete. Gate 3 on mode B is ~6.7 h of scoring plus ~1.4 h of
# report. Putting the cheap work first means a failure overnight costs the mode
# B gate, not the three deliverables that were ready at 23:00.
#
# GATE 3 ON MODE B IS THE SAME CODE, NOT A COPY. Every stage in l2r2gate3.py
# takes --mode B unchanged: the bank, the bars, the four streams and the five
# steps are the same objects for both modes, and only the gate 2 winners
# differ. Nothing in this chain is mode A code with the letter changed.
#
# SHARDING AT 4x JOBS, as Jack asked and as gate 2 and gate 3 mode A already
# carry: with nshard == jobs one slow shard holds the whole stage. Measured on
# mode A the per-shard rates spread 1.00-2.07 s/strategy, so 8 shards would
# have run ~23 h for ~8 h of work. 32 shards on 8 workers cost 403 min.
#
# deliverable = /Users/jackcuster/fx-data/results/r2gate2/MODEB_GATE3.md
# eta = 660
#
# --- CHECKPOINT, DEPENDENCY AND DISK DECLARATIONS ---
# ckpt  g3b endtoend       =  60   # 8 strategies through score -> report -> md on MODE B; runs FIRST
# ckpt  a4 book A     = 300   # per-shard book parts on the 300 s clock, resume by set difference
# ckpt  a4 nulls A    = 300   # identity off the saved series, then two engine nulls per step
# ckpt  a4 md A       =   0   # regenerates MODEA_GATE3.md with part 4 filled in
# ckpt  kpi A         =   0   # reads the daily series and the books csv, writes one md
# ckpt  kpi B         =   0   # the same generator on mode B's files
# ckpt  mid app       =   0   # rewrites app_data.json and app_ui.js in one pass
# ckpt  mid node      =   0   # node --check, seconds
# ckpt  g3b score B   = 300   # per-worker KPI parts flushed on the 300 s clock, resume by set difference
# ckpt  g3b report B  =   0   # reads the KPI bank, applies the bars, writes the csvs
# ckpt  g3b passmask  =   0   # one bool array off the KPI bank, no engine pass
# ckpt  g3b book B    = 300   # the passers' book for mode B, parts on the clock
# ckpt  g3b nulls B   = 300   # the three nulls on mode B's passers book
# ckpt  g3b md B      =   0   # MODEB_GATE3.md, every number quoted from a named file
# ckpt  end app       =   0   # rewrites app_data.json and app_ui.js in one pass
# ckpt  end node      =   0   # node --check, seconds
# needs g3b endtoend       = none
# needs a4 book A     = none
# needs a4 nulls A    = a4 book A
# needs a4 md A       = a4 book A
# needs kpi A         = none
# needs kpi B         = none
# needs mid app       = none
# needs mid node      = mid app
# needs g3b score B   = g3b endtoend
# needs g3b report B  = g3b score B
# needs g3b passmask  = g3b score B
# needs g3b book B    = g3b passmask
# needs g3b nulls B   = g3b book B
# needs g3b md B      = g3b report B
# needs end app       = none
# needs end node      = end app
# disk  g3b endtoend       = 0.1   # 8 strategies of KPI parts
# disk  a4 book A     = 0.9   # 32 shards of per-step book parts, already on disk and resumed
# disk  a4 nulls A    = 0.6   # one step of null scratch at a time, deleted once summed
# disk  a4 md A       = 0     # one markdown file
# disk  kpi A         = 0     # one markdown file and one csv
# disk  kpi B         = 0     # one markdown file and one csv
# disk  mid app       = 0.1   # rewrites app_data.json
# disk  mid node      = 0     # node --check
# disk  g3b score B   = 1.9   # (273,780 x 4 x 5 x 10 x 9) float32 KPI blocks, 32 shards
# disk  g3b report B  = 0.2   # five csvs
# disk  g3b passmask  = 0.1   # one bool array, (273,780 x 4 x 5)
# disk  g3b book B    = 0.9   # 32 shards of per-step book parts
# disk  g3b nulls B   = 0.6   # one step of null scratch at a time, deleted once summed
# disk  g3b md B      = 0     # one markdown file
# disk  end app       = 0.1   # rewrites app_data.json
# disk  end node      = 0     # node --check
. "${FX_CHAIN_LIB:-/Users/jackcuster/fx-data/code/chain/chainlib.sh}" "$0" "L2 RESTART CHAIN 18 COMPLETE"
cd /Users/jackcuster/fx-data
export FX_COST_TABLE=results/cost_table_h22.csv
export FX_CKPT_SECONDS=300

say "=== LAYER 2 RESTART CHAIN 18: gate 3 on mode B, part 4 for A and B, the mode B KPI table ==="

# ---- MODE B's OWN END-TO-END TEST, FIRST. Eight strategies through score ->
# report -> md on mode B, so the mode B path is proven before the 6.7 h stage
# rather than after it. Chain 17 lost a night to a report bug that eight
# strategies would have caught.
g "g3b endtoend" bash -c '
set -e
nice -n 19 python3 code/l2r2gate3.py --stage score --mode B --jobs 2 --cap 8000 --n 8
nice -n 19 python3 code/l2r2gate3.py --stage report --mode B --draws 10
test -s results/r2gate2/MODEB_GATE3.md
echo "  END TO END (MODE B): score -> report -> md all wrote, MODEB_GATE3.md $(wc -l < results/r2gate2/MODEB_GATE3.md) lines"'

# ---- PART 4 ON MODE A. The bank and the pass mask are already complete, so
# this is minutes: the book stage resumes its part files by set difference.
g "a4 book A"  nice -n 19 python3 code/l2r2gate3.py --stage book --mode A --jobs 8 --nshard 32
g "a4 nulls A" nice -n 19 python3 code/l2r2gate3.py --stage booknulls --mode A --jobs 8 \
   --draws 20 --id-draws 200
g "a4 md A"    nice -n 19 python3 code/l2r2gate3.py --stage md --mode A
ci "GATE 3 PART 4, MODE A: the passers' book, equal weight, routed and always-on, with its three nulls"

# ---- THE TWO KPI TABLES. MODEA_KPIS.md was assembled by hand in chat on
# 18 Nov; this regenerates it from the files it cites and produces the mode B
# equivalent with the same code, so the two are comparable.
g "kpi A" nice -n 19 python3 code/l2r2kpis.py --mode A
g "kpi B" nice -n 19 python3 code/l2r2kpis.py --mode B
ci "MODEB_KPIS.md, and MODEA_KPIS.md regenerated by code: the hand-built table had total and max DD wrong"

g "mid app"  nice -n 19 python3 code/r2app.py --stage app
g "mid node" node --check app_ui.js
ci "Part 4 mode A and both KPI tables wired into the app"

# ---- GATE 3 ON MODE B. The long stage, last, with everything above banked.
g "g3b score B" nice -n 19 python3 code/l2r2gate3.py --stage score --mode B --jobs 8 --nshard 32 --cap 30000
ci "Gate 3 mode B: every gate 2 winner re-scored per calendar year through the shipped Scorer"

g "g3b report B" nice -n 19 python3 code/l2r2gate3.py --stage report --mode B --draws 200
ci "GATE 3 MODE B: the bars on the grade year, the identity null on the year roles, and the stitched 2016-2020 record"

g "g3b passmask" nice -n 19 python3 code/l2r2gate3.py --stage passmask --mode B
g "g3b book B"   nice -n 19 python3 code/l2r2gate3.py --stage book --mode B --jobs 8 --nshard 32
g "g3b nulls B"  nice -n 19 python3 code/l2r2gate3.py --stage booknulls --mode B --jobs 8 \
   --draws 20 --id-draws 200
ci "GATE 3 PART 4, MODE B: the passers' book and its three nulls"

g "g3b md B" nice -n 19 python3 code/l2r2gate3.py --stage md --mode B
ci "MODEB_GATE3.md complete, every number quoted from a named file"

g "end app"  nice -n 19 python3 code/r2app.py --stage app
g "end node" node --check app_ui.js
ci "Gate 3 mode B wired into the app"

chain_summary
say "L2 RESTART CHAIN 18 COMPLETE"
