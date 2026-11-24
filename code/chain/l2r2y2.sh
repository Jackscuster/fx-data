#!/bin/bash
# LAYER 2 RESTART, CHAIN 22B: THE _r2dd RE-TUNE OF MODE A, AND THE SAME
# DOWNSTREAM AS THE EXPECTANCY TUNE.
#
# Jack, 20-21 Nov: "Re-tune mode A with the tuner picking each strategy's
# settings on total R divided by max drawdown R ... with a minimum of 100
# tuning trades; Sortino and expectancy reported beside it, never used. Same
# walk forward, same bank design, suffix _r2dd." Plus the widened stop and
# target grids, and then "the same downstream as the expectancy tune".
#
# THE OBJECTIVE TRAVELS IN THE ENVIRONMENT, not in an argument. macOS
# multiprocessing SPAWNS, so a pool worker re-imports l2r2gate2 and takes its
# module globals fresh; an objective passed as a parameter would be right in
# the parent and default in every child. FX_G2_OBJECTIVE is inherited, so the
# parent and the workers cannot disagree. The widened grid rides with it.
#
# THE BANK CANNOT COLLIDE WITH THE SHIPPED ONE. bank_tag() appends _r2dd to
# whatever tag is passed, so even `--tag full` writes modeA_full_r2dd. Two
# banks tuned on different objectives must never share a filename.
#
# WHAT WAS PROVEN BEFORE THIS WAS ARMED, on 21 Nov:
#   condition 1b  48 (strategy, slice, config) pairs scored through BOTH
#                 accumulators: worst |acc diff| 0, the per-day vector sums to
#                 each role's total R to 4.3e-13, and the fast drawdown equals
#                 the reference exactly. It caught a real bug first -- the fast
#                 path started its peak at zero instead of at the first point
#                 and disagreed by 9.38 R.
#   condition 1   72 evaluations, worst |per-year marks - trade R| 8.9e-16.
#   condition 2   240 comparisons on the fast path (and 800 before it): zero
#                 tune-pick mismatches, zero record mismatches, worst |diff| 0.
#   cost          r2dd costs 5.36 ms/config against expectancy's 6.33 on the
#                 same machine and the same contention -- no more expensive
#                 per configuration, so the run scales with the config count.
#
# approval = none   the objective and grids Jack specified in full on 20-21 Nov, with the three conditions passed and recorded above before arming
#
# deliverable = /Users/jackcuster/fx-data/results/r2gate2/MODEA_R2DD.md
# eta = 240
#
# SPLIT FROM CHAIN 22 ON 22 Nov; see l2r2y1.sh. This half assumes the _r2dd
# gate 2 bank and gate 3 KPI bank already exist, which is what 22A builds, and
# its end-to-end stage asserts the conditions still hold on this machine.
# --- CHECKPOINT, DEPENDENCY AND DISK DECLARATIONS ---
# ckpt  dd endtoend   =  60   # condition 1b: both accumulators on the same configs; runs FIRST
# ckpt  dd cond1      =   0   # year-end MTM assert, every trade's marks sum to its R
# ckpt  dd cond2      = 300   # banked one pass against the naive per-step path
# ckpt  dd books      = 300   # the four books, per-shard parts on the clock
# ckpt  dd nulls      = 300   # the three nulls on the books
# ckpt  dd universe   =   0   # streamed reduction of the KPI bank
# ckpt  dd floors     =   0   # analytic floor, closed form
# ckpt  dd nullstrat  = 300   # 2,000 strategies x 20 random-entry draws
# ckpt  dd floorb     =   0   # the extreme-value fit
# ckpt  dd winners    =   0   # the non-luck set and the floor ladder
# ckpt  dd family     =   0   # cousins of each winner
# ckpt  dd winbook    = 300   # the winners' book and its nulls
# ckpt  dd overlays   =   0   # the three overlay sweeps
# ckpt  dd prop       =   0   # prop return on every table
# ckpt  dd top30      =   0   # top 30 by t, by return/DD, by prop return
# ckpt  dd md         =   0   # MODEA_R2DD.md, side by side with the expectancy tune
# ckpt  dd app        =   0   # rewrites app_data.json and app_ui.js
# ckpt  dd node       =   0   # node --check
# ckpt  dd push       =   0   # pushes Jack's phone
# needs dd endtoend   = none
# needs dd cond1      = dd endtoend
# needs dd cond2      = dd endtoend
# needs dd books      = dd endtoend
# needs dd nulls      = dd books
# needs dd universe   = dd endtoend
# needs dd floors     = dd universe
# needs dd nullstrat  = dd endtoend
# needs dd floorb     = dd nullstrat
# needs dd winners    = dd floors, dd floorb
# needs dd family     = dd winners
# needs dd winbook    = dd winners
# needs dd overlays   = dd winbook
# needs dd prop       = dd winners
# needs dd top30      = dd prop
# needs dd md         = dd winners
# needs dd app        = none
# needs dd node       = dd app
# needs dd push       = none
# disk  dd endtoend   = 0.1   # one csv
# disk  dd cond1      = 0     # one csv
# disk  dd cond2      = 0     # one csv
# disk  dd books      = 1.2   # four books, per-shard parts
# disk  dd nulls      = 1.5   # one step of null scratch at a time, deleted once summed
# disk  dd universe   = 0.2   # one npz, ~150 MB
# disk  dd floors     = 0     # two csvs
# disk  dd nullstrat  = 0.2   # per-shard csvs
# disk  dd floorb     = 0     # two csvs
# disk  dd winners    = 0     # two csvs
# disk  dd family     = 0     # one csv
# disk  dd winbook    = 0.5   # book parts plus one step of null scratch
# disk  dd overlays   = 0     # one csv
# disk  dd prop       = 0     # rewrites csvs in place
# disk  dd top30      = 0     # three csvs
# disk  dd md         = 0     # one markdown file
# disk  dd app        = 0.1   # rewrites app_data.json
# disk  dd node       = 0     # node --check
# disk  dd push       = 0     # one http request
. "${FX_CHAIN_LIB:-/Users/jackcuster/fx-data/code/chain/chainlib.sh}" "$0" "L2 RESTART CHAIN 22B COMPLETE"
cd /Users/jackcuster/fx-data
export FX_COST_TABLE=results/cost_table_h22.csv
export FX_CKPT_SECONDS=300
export FX_CI_LOCAL=1          # commit locally while the batched push is still landing
export FX_G2_OBJECTIVE=r2dd          # the objective AND the widened grids
TAG=full_r2dd

say "=== LAYER 2 RESTART CHAIN 22B: the _r2dd re-tune of mode A, objective total R / max DD R ==="

g "dd endtoend" nice -n 19 python3 code/l2r2gate2.py --stage cond1b --mode A --n 4 --nconf 6
g "dd cond1"    nice -n 19 python3 code/l2r2gate2.py --stage cond1 --mode A --n 12
g "dd cond2"    nice -n 19 python3 code/l2r2gate2.py --stage cond2 --mode A --n 12 --minutes 20
ci "Gate 2 _r2dd: conditions 1b, 1 and 2 re-proven on the machine that is about to run the tune"

g "dd books" nice -n 19 python3 code/l2r2book.py --stage books --mode A --tag $TAG --jobs 8 --out-tag $TAG
g "dd nulls" nice -n 19 python3 code/l2r2null2.py --stage nulls --mode A --tag $TAG --jobs 8 \
   --sizes 5000,20000 --draws 20 --id-draws 200 --out-tag $TAG \
   --books results/r2gate2/modeA_books_$TAG.csv \
   --out results/r2gate2/modeA_books_${TAG}_nulls.csv
ci "The four _r2dd books and their three nulls"

g "dd universe"  nice -n 19 python3 code/l2r2winners.py --stage universe --mode A --tag $TAG
g "dd floors"    nice -n 19 python3 code/l2r2winners.py --stage floors --mode A
g "dd nullstrat" nice -n 19 python3 code/l2r2winners.py --stage nullstrat --mode A --tag $TAG --nsample 2000 --draws 20 --jobs 8
g "dd floorb"    nice -n 19 python3 code/l2r2winners.py --stage floorb --mode A
g "dd winners"   nice -n 19 python3 code/l2r2winners.py --stage winners --mode A --tag $TAG
g "dd family"    nice -n 19 python3 code/l2r2winners.py --stage family --mode A --tag $TAG
ci "_r2dd winners: the universe, both luck floors, the non-luck set and family support"

g "dd winbook"  nice -n 19 python3 code/l2r2winners.py --stage winbook --mode A --tag $TAG --jobs 8 --nshard 32
g "dd overlays" nice -n 19 python3 code/l2r2winners.py --stage overlays --mode A --label winners
g "dd prop"     nice -n 19 python3 code/l2r2winners.py --stage prop --mode A
g "dd top30"    nice -n 19 python3 code/l2r2winners.py --stage top30 --mode A
g "dd md"       nice -n 19 python3 code/l2r2winners.py --stage md --mode A
ci "_r2dd: the winners' book, the overlay curves, prop return and the write-up"

g "dd app"  nice -n 19 python3 code/r2app.py --stage app
g "dd node" node --check app_ui.js
ci "The _r2dd re-tune wired into the app"

g "dd push" nice -n 19 python3 code/l2r2push.py --what "mode A _r2dd re-tune" \
   --file results/r2gate2/modeA_books_full_r2dd.csv \
   --also results/r2gate2/modeA_winners.csv

chain_summary
say "L2 RESTART CHAIN 22B COMPLETE"
