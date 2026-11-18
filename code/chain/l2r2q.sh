#!/bin/bash
# LAYER 2 RESTART, CHAIN 15 (HANDOFF 0l): GATE 3 ON MODE A, from the gate 2 bank.
#
# NO NEW TUNING. Every configuration here was chosen by gate 2; it is re-scored
# because the bank cannot give three of Jack's five bars -- Sortino needs the
# downside deviation of per-trade R, max DD and Calmar need the ordered equity
# curve, and the bank holds only n, sum_r, gain, loss and n_win per year. The
# re-score goes through the shipped l2tune.Scorer with one window per calendar
# year, so the KPIs come from _agg, the same aggregator every other result in
# this project used.
#
# MEASURED COST, not estimated: 0.841 s per strategy steady state, so the
# scoring stage is ~8.0 h on eight workers. Narrowing from ten calendar years
# to the six each step uses changed it by 2%, so the cost is the twenty engine
# passes per strategy and not the aggregation.
#
# deliverable = /Users/jackcuster/fx-data/results/r2gate2/MODEA_GATE3.md
# eta = 600
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
. "${FX_CHAIN_LIB:-/Users/jackcuster/fx-data/code/chain/chainlib.sh}" "$0" "L2 RESTART CHAIN 15 COMPLETE"
cd /Users/jackcuster/fx-data
export FX_COST_TABLE=results/cost_table_h22.csv
export FX_CKPT_SECONDS=300

say "=== LAYER 2 RESTART CHAIN 15: GATE 3 ON MODE A ==="

g "g3 endtoend" bash -c '
set -e
rm -rf results/r2gate2/modeA_gate3parts_e2e
nice -n 19 python3 code/l2r2gate3.py --stage score --mode A --jobs 2 --cap 8000 --n 8
nice -n 19 python3 code/l2r2gate3.py --stage report --mode A --draws 10
test -s results/r2gate2/MODEA_GATE3.md
echo "  END TO END: score -> report -> md all wrote, MODEA_GATE3.md $(wc -l < results/r2gate2/MODEA_GATE3.md) lines"'

g "g3 score A" nice -n 19 python3 code/l2r2gate3.py --stage score --mode A --jobs 8 --cap 30000
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

chain_summary
say "L2 RESTART CHAIN 15 COMPLETE"
