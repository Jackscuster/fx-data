#!/bin/bash
# LAYER 2 RESTART, CHAIN 6 (HANDOFF 0l): GATE 2, MODE A, ALL 273,780. NO CUT.
# Shards are CONTIGUOUS so the indicator cache amortises across each (c1,c2)
# block; the series cache is disk-backed so the ~1.2 GB of axial variants is
# paid once; every stage checkpoints on a 300 s clock and resumes by set
# difference, including INSIDE a single strategy.
#
# --- CHECKPOINT AND DEPENDENCY DECLARATIONS ---
# code/l2stagecheck.py chain refuses this driver without both lines per stage,
# and launch.sh calls that guard, so neither can be skipped.
# ckpt  g2 endtoend  =  60   # the one-minute save/read/resume test; runs FIRST
# ckpt  g2 grid      =   0   # reads the registry, writes two small CSVs; holds no compute
# ckpt  g2 cond1     =  60   # 40 strategies, one row out; its own work is the check
# ckpt  g2 smoke 2k  = 300   # l2ckpt.Checkpointer, part file every 300 s per worker
# ckpt  g2 cond2     = 300   # bounded run, compares strategy by strategy
# ckpt  g2 preflight =   0   # 27 mechanical checks, one dated CSV, seconds
# ckpt  g2 full A    = 300   # Checkpointer per worker, resume by set difference, intra-strategy state
# ckpt  g2 app       =   0   # rewrites app_data.json and app_ui.js in one pass
# ckpt  g2 node      =   0   # node --check, seconds
# needs g2 endtoend  = none
# needs g2 grid      = none
# needs g2 cond1     = g2 endtoend
# needs g2 smoke 2k  = g2 endtoend
# needs g2 cond2     = g2 endtoend
# needs g2 preflight = none
# needs g2 full A    = g2 endtoend, g2 cond1, g2 cond2, g2 preflight
# needs g2 app       = none
# needs g2 node      = g2 app
#
# WHAT IS INDEPENDENT, AND WHY IT MATTERS (Jack, 17 Nov): the grid report, the
# pre-flight audit and the app wiring do not depend on the tuner, so a failed
# tuning stage no longer takes them down with it. Only the FULL mode A run
# depends on both conditions -- which is the one place a halt must still bite.
. "${FX_CHAIN_LIB:-/Users/jackcuster/fx-data/code/chain/chainlib.sh}" "$0" "L2 RESTART CHAIN 6 COMPLETE"
cd /Users/jackcuster/fx-data
export FX_COST_TABLE=results/cost_table_h22.csv
export FX_CKPT_SECONDS=300

say "=== LAYER 2 RESTART CHAIN 6: GATE 2 MODE A, ALL 273,780, NO CUT (uncapped grid) ==="
say "free space: $(df -h /System/Volumes/Data | tail -1 | awk '{print $4}')"

g "g2 endtoend" nice -n 19 python3 code/l2r2gate2.py --stage endtoend --mode A --n 12 --jobs 2
g "g2 grid"     nice -n 19 python3 code/l2r2gate2.py --stage grid     --mode A
g "g2 cond1"    nice -n 19 python3 code/l2r2gate2.py --stage cond1    --mode A --n 40
ci "Gate 2 on the _r2 path: the declared grid, the axial set, and condition 1 (per-year marks reconstruct trade R)"

g "g2 smoke 2k" nice -n 19 python3 code/l2r2gate2.py --stage smoke --mode A --n 2000 --tag smoke2k --jobs 6 --cap 30000
ci "Gate 2 mode A smoke: 2,000 stratified strategies through the one-pass banked tuner, with the measured seconds per strategy, bank size and full-mode costing"

g "g2 cond2"    nice -n 19 python3 code/l2r2gate2.py --stage cond2 --mode A --n 2000 --minutes 120
ci "Gate 2 condition 2: the banked one pass against the naive per-step path, same picks and same grade and trade records to 1e-9"

g "g2 preflight" nice -n 19 python3 code/preflight.py --out audit_$(date +%F).csv

g "g2 full A" nice -n 19 python3 code/l2r2gate2.py --stage run --mode A --n 273780 --tag full --jobs 8 --cap 30000
ci "GATE 2 MODE A: all 273,780 strategies tuned on the one-pass banked path, four streams, five steps, no cut anywhere"

g "g2 app"  nice -n 19 python3 code/r2app.py --stage app
g "g2 node" node --check app_ui.js
ci "Gate 2 mode A wired into the app"

chain_summary
say "L2 RESTART CHAIN 6 COMPLETE"
