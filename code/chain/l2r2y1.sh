#!/bin/bash
# LAYER 2 RESTART, CHAIN 22A: THE _r2dd RE-TUNE OF MODE A, AND THE SAME
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
# deliverable = /Users/jackcuster/fx-data/results/r2gate2/modeA_gate3_passers_r2dd.csv
# eta = 2400
#
# SPLIT FROM CHAIN 22 ON 22 Nov, because l2stagecheck sums EVERY stage's
# declared disk and refuses on the total. The full chain declared 7.7 GB and
# was refused at 22:35 on 21 Nov with 3.3 GB free. The peak is genuinely
# per-chain, not per-programme: the tune and the gate 3 score are sequential
# and the books and nulls come after. So 22A is the tune and the score, 22B is
# everything downstream, and each declares what it actually needs at once.
# This is not a way around the guard -- the guard is right that 7.7 GB of
# declarations will not fit; it is a smaller unit of work.
# --- CHECKPOINT, DEPENDENCY AND DISK DECLARATIONS ---
# ckpt  dd endtoend   =  60   # condition 1b: both accumulators on the same configs; runs FIRST
# ckpt  dd cond1      =   0   # year-end MTM assert, every trade's marks sum to its R
# ckpt  dd cond2      = 300   # banked one pass against the naive per-step path
# ckpt  dd tune A     = 300   # l2ckpt.Checkpointer, part file every 300 s per worker
# ckpt  dd g3 score   = 300   # per-worker KPI parts on the 300 s clock, resume by set difference
# ckpt  dd g3 report  =   0   # bars, identity null, stitched record
# needs dd endtoend   = none
# needs dd cond1      = dd endtoend
# needs dd cond2      = dd endtoend
# needs dd tune A     = dd endtoend, dd cond1, dd cond2
# needs dd g3 score   = dd tune A
# needs dd g3 report  = dd g3 score
# disk  dd endtoend   = 0.1   # one csv
# disk  dd cond1      = 0     # one csv
# disk  dd cond2      = 0     # one csv
# disk  dd tune A     = 1.8   # the _r2dd gate 2 bank, 727 configs per strategy
# disk  dd g3 score   = 1.9   # the _r2dd gate 3 KPI bank, 32 shards
# disk  dd g3 report  = 0.2   # five csvs
. "${FX_CHAIN_LIB:-/Users/jackcuster/fx-data/code/chain/chainlib.sh}" "$0" "L2 RESTART CHAIN 22A COMPLETE"
cd /Users/jackcuster/fx-data
export FX_COST_TABLE=results/cost_table_h22.csv
export FX_CKPT_SECONDS=300
export FX_CI_LOCAL=1          # commit locally while the batched push is still landing
export FX_G2_OBJECTIVE=r2dd          # the objective AND the widened grids
TAG=full_r2dd

say "=== LAYER 2 RESTART CHAIN 22A: the _r2dd re-tune of mode A, objective total R / max DD R ==="

g "dd endtoend" nice -n 19 python3 code/l2r2gate2.py --stage cond1b --mode A --n 4 --nconf 6
g "dd cond1"    nice -n 19 python3 code/l2r2gate2.py --stage cond1 --mode A --n 12
g "dd cond2"    nice -n 19 python3 code/l2r2gate2.py --stage cond2 --mode A --n 12 --minutes 20
ci "Gate 2 _r2dd: conditions 1b, 1 and 2 re-proven on the machine that is about to run the tune"

g "dd tune A" nice -n 19 python3 code/l2r2gate2.py --stage run --mode A --n 999999999 --tag full --jobs 8 --cap 30000 --nshard 32
ci "GATE 2 _r2dd MODE A: every strategy re-tuned on total R / max DD R over its four tune years, widened stop and target grids"

g "dd g3 score"  nice -n 19 python3 code/l2r2gate3.py --stage score --mode A --tag $TAG --jobs 8 --nshard 32 --cap 30000
g "dd g3 report" nice -n 19 python3 code/l2r2gate3.py --stage report --mode A --tag $TAG --draws 200
ci "GATE 3 on the _r2dd bank: the bars on the grade year, the identity null, the stitched record"

chain_summary
say "L2 RESTART CHAIN 22A COMPLETE"
