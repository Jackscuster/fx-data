#!/bin/bash
# LAYER 2 RESTART, CHAIN 21: THE MODE B WINNERS PIPELINE, THE WRITE-UPS, AND
# THE PROP RETURN COLUMN EVERYWHERE.
#
# Jack, 21 Nov: "If the _r2dd code is not ready and tested by the time chain 20
# finishes, run instead, in this order: the MODEA_WINNERS.md write-up, the mode
# B winners pipeline (identical to A), the mode B KPI tables, then the re-tune
# when it is ready."
#
# THE _r2dd RE-TUNE IS NOT IN THIS CHAIN AND IS NOT ARMED. Its DD-carrying
# accumulator, its role_dd and its pick_r2dd are written and import clean, but
# the objective wiring, the widened-grid switch, the year-end MTM assert, the
# equivalence condition and the 2,000-strategy smoke are NOT built. An untested
# objective change in the hot path of a 20-hour stage is not something to leave
# running unattended, so it is excluded rather than promised.
#
# MODEA_WINNERS.md IS ALREADY WRITTEN (346 lines, before this chain was armed).
# It is regenerated at the end so it picks up the prop column.
#
# EVERY STAGE HERE HAS ALREADY RUN ON MODE A TODAY. Nothing in this chain is
# code exercised for the first time overnight.
#
# approval = none   the mode A winners pipeline re-run on mode B, plus report generation -- the amended guard 6 names "another mode" and "report generation" explicitly
#
# deliverable = /Users/jackcuster/fx-data/results/r2gate2/MODEB_WINNERS.md
# eta = 90
#
# --- CHECKPOINT, DEPENDENCY AND DISK DECLARATIONS ---
# ckpt  wn endtoend    =  60   # mode B's bank asserted complete, then its universe built and read back
# ckpt  wn floors B    =   0   # analytic floor, closed form
# ckpt  wn sweep B     =   0   # read-only reduction of the universe
# ckpt  wn nullstrat B = 300   # 2,000 strategies x 20 random-entry draws, part file per shard
# ckpt  wn floorb B    =   0   # the extreme-value fit on the null
# ckpt  wn winners B   =   0   # read-only, plus the floor ladder
# ckpt  wn family B    =   0   # cousins of each winner, read-only
# ckpt  wn winbook B   = 300   # the winners' book and its three nulls
# ckpt  wn overlays B  =   0   # three overlays swept on the book's daily series
# ckpt  wn prop B      =   0   # the prop return column on every mode B table
# ckpt  wn top30 B     =   0   # top 30 by t, by return/DD and by prop return
# ckpt  wn md B        =   0   # MODEB_WINNERS.md
# ckpt  wn kpi B       =   0   # MODEB_KPIS.md regenerated with the prop column
# ckpt  wn prop A      =   0   # the prop column on mode A's tables
# ckpt  wn top30 A     =   0   # mode A's three top-30 tables
# ckpt  wn md A        =   0   # MODEA_WINNERS.md regenerated with the prop column
# ckpt  wn kpi A       =   0   # MODEA_KPIS.md regenerated
# ckpt  wn app         =   0   # rewrites app_data.json and app_ui.js in one pass
# ckpt  wn node        =   0   # node --check, seconds
# ckpt  wn push        =   0   # pushes Jack's phone that the deliverables landed
# needs wn endtoend    = none
# needs wn floors B    = wn endtoend
# needs wn sweep B     = wn endtoend
# needs wn nullstrat B = wn endtoend
# needs wn floorb B    = wn nullstrat B
# needs wn winners B   = wn floors B, wn floorb B
# needs wn family B    = wn winners B
# needs wn winbook B   = wn winners B
# needs wn overlays B  = wn winbook B
# needs wn prop B      = wn winners B
# needs wn top30 B     = wn prop B
# needs wn md B        = wn winners B
# needs wn kpi B       = none
# needs wn prop A      = none
# needs wn top30 A     = wn prop A
# needs wn md A        = wn prop A
# needs wn kpi A       = none
# needs wn app         = none
# needs wn node        = wn app
# needs wn push        = none
# disk  wn endtoend    = 0.2   # the universe npz, ~150 MB
# disk  wn floors B    = 0     # two small csvs
# disk  wn sweep B     = 0     # one csv
# disk  wn nullstrat B = 0.2   # per-shard csvs, concatenated then kept
# disk  wn floorb B    = 0     # two small csvs
# disk  wn winners B   = 0     # two small csvs
# disk  wn family B    = 0     # one small csv
# disk  wn winbook B   = 0.5   # book parts plus one step of null scratch at a time
# disk  wn overlays B  = 0     # one csv
# disk  wn prop B      = 0     # rewrites existing csvs in place
# disk  wn top30 B     = 0     # three small csvs
# disk  wn md B        = 0     # one markdown file
# disk  wn kpi B       = 0     # one markdown file and one csv
# disk  wn prop A      = 0     # rewrites existing csvs in place
# disk  wn top30 A     = 0     # three small csvs
# disk  wn md A        = 0     # one markdown file
# disk  wn kpi A       = 0     # one markdown file and one csv
# disk  wn app         = 0.1   # rewrites app_data.json
# disk  wn node        = 0     # node --check
# disk  wn push        = 0     # one http request
. "${FX_CHAIN_LIB:-/Users/jackcuster/fx-data/code/chain/chainlib.sh}" "$0" "L2 RESTART CHAIN 21 COMPLETE"
cd /Users/jackcuster/fx-data
export FX_COST_TABLE=results/cost_table_h22.csv
export FX_CKPT_SECONDS=300
J=8

say "=== LAYER 2 RESTART CHAIN 21: mode B winners pipeline, the write-ups, prop return ==="

g "wn endtoend" bash -c '
set -e
nice -n 19 python3 code/l2r2bankchk.py --mode B
nice -n 19 python3 code/l2r2winners.py --stage universe --mode B
test -s results/r2gate2/modeB_winners_universe.npz
echo "  END TO END: mode B universe built, saved and read back"'

g "wn floors B"    nice -n 19 python3 code/l2r2winners.py --stage floors --mode B
g "wn sweep B"     nice -n 19 python3 code/l2r2winners.py --stage sweep --mode B
g "wn nullstrat B" nice -n 19 python3 code/l2r2winners.py --stage nullstrat --mode B --nsample 2000 --draws 20 --jobs $J
g "wn floorb B"    nice -n 19 python3 code/l2r2winners.py --stage floorb --mode B
ci "MODE B WINNERS: the universe, both luck floors, the floor sweep"

g "wn winners B"   nice -n 19 python3 code/l2r2winners.py --stage winners --mode B
g "wn family B"    nice -n 19 python3 code/l2r2winners.py --stage family --mode B
g "wn prop B"      nice -n 19 python3 code/l2r2winners.py --stage prop --mode B
g "wn top30 B"     nice -n 19 python3 code/l2r2winners.py --stage top30 --mode B
ci "MODE B WINNERS: the non-luck set, family support, prop return and the three top-30 tables"

g "wn winbook B"   nice -n 19 python3 code/l2r2winners.py --stage winbook --mode B --jobs $J --nshard 32
g "wn overlays B"  nice -n 19 python3 code/l2r2winners.py --stage overlays --mode B --label winners
ci "MODE B WINNERS: the winners' book with both nulls, and the overlay curves"

g "wn md B"  nice -n 19 python3 code/l2r2winners.py --stage md --mode B
g "wn kpi B" nice -n 19 python3 code/l2r2kpis.py --mode B
ci "MODEB_WINNERS.md and MODEB_KPIS.md"

g "wn prop A"  nice -n 19 python3 code/l2r2winners.py --stage prop --mode A
g "wn top30 A" nice -n 19 python3 code/l2r2winners.py --stage top30 --mode A
g "wn md A"    nice -n 19 python3 code/l2r2winners.py --stage md --mode A
g "wn kpi A"   nice -n 19 python3 code/l2r2kpis.py --mode A
ci "MODEA_WINNERS.md and MODEA_KPIS.md regenerated with the prop return column"

g "wn app"  nice -n 19 python3 code/r2app.py --stage app
g "wn node" node --check app_ui.js
ci "Both modes' winners wired into the app"

g "wn push" nice -n 19 python3 code/l2r2push.py --what "mode B winners pipeline" \
   --file results/r2gate2/MODEB_WINNERS.md \
   --also results/r2gate2/MODEA_WINNERS.md

chain_summary
say "L2 RESTART CHAIN 21 COMPLETE"
