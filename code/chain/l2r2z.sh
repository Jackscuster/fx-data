#!/bin/bash
# LAYER 2 RESTART, CHAIN 23: CHUNK 1 — THREE BANK READS, THEN CHAIN 22A.
#
# Jack, 23-24 Nov: chunk 1 is A1 (slot main effects on the tuned bank), A1b
# (walk-forward component selection, replacing the mis-posed A7) and A6 (the
# prop simulator, built as a standing stage). All three are READS: nothing here
# runs the engine. A1-on-defaults moves to chunk 2 with the config-0 pass.
#
# NO PUSH GATE (Jack, 24 Nov). Every stage here reads LOCAL banks, so nothing
# here has any reason to wait on a slow remote. The chain runs with
# FX_CI_LOCAL=1, so `ci` commits and does not pull or push; one push follows
# once the batcher lands. Nothing is skipped because the remote is behind.
#
# HAND-CHECKED BEFORE ARMING. A1's vol = williams_vix_fix_volume_signals cell
# was recomputed from the bank part files by independent code: 1,665
# strategies, 757,810 trades, +0.015178 R per trade -- identical to the table
# to 1e-9.
#
# approval = none   three bank reads and report generation; the amended guard 6 names report generation explicitly, and A1/A1b/A6 were specified in full by Jack on 23-24 Nov
#
# deliverable = /Users/jackcuster/fx-data/results/r2reads/A1_SLOTS.md
# eta = 180
#
# --- CHECKPOINT, DEPENDENCY AND DISK DECLARATIONS ---
# ckpt  c1 endtoend    =  60   # A1 on a 20,000-strategy slice with 50 draws, saved and read back; runs FIRST
# ckpt  c1 a1 A        = 300   # streamed bank read plus 1,000 label shuffles per slot
# ckpt  c1 a1 B        = 300   # the same on mode B
# ckpt  c1 a1b A       = 300   # per-step tuning-year ranking, K swept, 1,000-draw null
# ckpt  c1 a1b B       = 300   # the same on mode B
# ckpt  c1 a6          =   0   # arithmetic on the saved daily series
# ckpt  c1 app         =   0   # rewrites app_data.json and app_ui.js in one pass
# ckpt  c1 node        =   0   # node --check, seconds
# ckpt  c1 push        =   0   # pushes Jack's phone that chunk 1 landed
# needs c1 endtoend    = none
# needs c1 a1 A        = c1 endtoend
# needs c1 a1 B        = c1 endtoend
# needs c1 a1b A       = c1 endtoend
# needs c1 a1b B       = c1 endtoend
# needs c1 a6          = none
# needs c1 app         = none
# needs c1 node        = c1 app
# needs c1 push        = none
# disk  c1 endtoend    = 0.1   # three csvs on a slice
# disk  c1 a1 A        = 0.2   # option, null and c1xc2 csvs
# disk  c1 a1 B        = 0.2   # the same on mode B
# disk  c1 a1b A       = 0.1   # one csv
# disk  c1 a1b B       = 0.1   # one csv
# disk  c1 a6          = 0.1   # one csv per source
# disk  c1 app         = 0.1   # rewrites app_data.json
# disk  c1 node        = 0     # node --check
# disk  c1 push        = 0     # one http request
. "${FX_CHAIN_LIB:-/Users/jackcuster/fx-data/code/chain/chainlib.sh}" "$0" "L2 RESTART CHAIN 23 COMPLETE"
cd /Users/jackcuster/fx-data
export FX_COST_TABLE=results/cost_table_h22.csv
export FX_CKPT_SECONDS=300
export FX_CI_LOCAL=1          # commit locally; the batched push lands separately

say "=== LAYER 2 RESTART CHAIN 23: chunk 1, three bank reads ==="

g "c1 endtoend" bash -c '
set -e
nice -n 19 python3 code/r2reads.py --stage a1 --mode A --draws 50 --nmax 20000
test -s results/r2reads/modeA_a1_slots.csv
test -s results/r2reads/A1_SLOTS.md
echo "  END TO END: A1 on a 20,000-strategy slice wrote and read back, $(wc -l < results/r2reads/A1_SLOTS.md) md lines"'

g "c1 a1 A"  nice -n 19 python3 code/r2reads.py --stage a1 --mode A --draws 1000
g "c1 a1 B"  nice -n 19 python3 code/r2reads.py --stage a1 --mode B --draws 1000
ci "A1: slot main effects on both unseen records, 1,000-draw label-shuffle null, C1 x C2 cross"

g "c1 a1b A" nice -n 19 python3 code/r2reads.py --stage a1b --mode A --draws 1000
g "c1 a1b B" nice -n 19 python3 code/r2reads.py --stage a1b --mode B --draws 1000
ci "A1b: walk-forward component selection, K swept, with its label-shuffle null"

g "c1 a6"    nice -n 19 python3 code/r2reads.py --stage a6 --mode A
ci "A6: the prop simulator as a standing stage, both phases, sizing and payout swept"

g "c1 app"  nice -n 19 python3 code/r2app.py --stage app
g "c1 node" node --check app_ui.js
ci "Chunk 1 wired into the app"

g "c1 push" nice -n 19 python3 code/l2r2push.py --what "chunk 1: A1, A1b, A6" \
   --file results/r2reads/A1_SLOTS.md \
   --also results/r2reads/A6_PROPSIM.md

chain_summary
say "L2 RESTART CHAIN 23 COMPLETE"
