#!/bin/bash
# LAYER 2, CHAIN 30: STAGE 2 -- THE BASELINE ADDED TO C1, AND ENGINE AUDIT 2.
#
# Jack, 24 Nov: "QUEUE ORDER FIRST. Stage 2 below goes to the front." His picks
# from STAGE1_R2.md, with his reasons, are recorded in HANDOFF 0m and in
# CANDIDATE_LEDGER.csv. I did not choose them.
#
#   C1         ichimoku, schaff_trend_cycle, halftrend
#   C1 rule    ROLLING TOP 3, ranked on the four tuning years
#   baselines  sma, hma, t3
#   jack plan is the main version; textbook reported beside it.
#
# ORDER IS JACK'S: 2a, 2b, 2c, 2f, 2d, 2e, audit.
#
# WHY IT RUNS ALONE AND NOT BESIDE A BACK-OF-QUEUE CHAIN. Jack asked for
# parallel if the slowdown is under 20%. The machine has 10 cores (8
# performance, 2 efficiency) and the back-of-queue chains run 8 workers, so
# load is already 10.07 -- fully saturated. One extra nice-19 worker costs
# about 1/9, roughly 11%, which does pass his bar. But stage 2 measured at
# 1.3 s per engine run, so the WHOLE of it is about 2.5 h against the queue's
# ~24 h. Running it first costs the queue 2.5 h; running it in parallel makes
# stage 2 itself finish LATER, and stage 2 is the thing Jack is waiting on. So
# it goes first, alone, at full width. The 11% figure is reported to him so the
# choice is his to reverse.
#
# approval = none   the stage 2 work Jack specified on 24 Nov, on his own picks
#
# deliverable = /Users/jackcuster/fx-data/results/nnfx/STAGE2.md
# eta = 160
#
# --- CHECKPOINT, DEPENDENCY AND DISK DECLARATIONS ---
# ckpt  s2 endtoend  =  60   # one C1 x one baseline through grid, pick, control check and report; runs FIRST
# ckpt  s2 ledger    =   0   # Jack's picks into CANDIDATE_LEDGER.csv
# ckpt  s2 grid      = 300   # 2a: 3 C1 x 3 base x 9 setting pairs x 2 plans x 6 rulesets
# ckpt  s2 pool      = 300   # the 39-C1 pool the rolling rule ranks on, sharded
# ckpt  s2 pickA     =   0   # walk-forward setting pick, picks grid
# ckpt  s2 pickB     =   0   # the same on the pool grid
# ckpt  s2 paired    = 300   # 2b: the paired test and the rule attribution
# ckpt  s2 report    = 300   # 2c: nulls, both t statistics, true dip, prop simulator
# ckpt  s2 rolling   = 300   # 2f: K 1-10, turnover, picked set per year
# ckpt  s2 costcap   = 300   # 2d: cost/ATR cap swept
# ckpt  s2 fewer     = 300   # 2e: min gap and min signal age swept
# ckpt  s2 audfill   = 300   # audit 1: fill price against the hourly file
# ckpt  s2 audrest   = 300   # audit 2-4: financing, cost per R, tick volume
# ckpt  s2 md        =   0   # STAGE2.md and ENGINE_AUDIT_2.md
# ckpt  s2 app       =   0   # rewrites app_data.json and app_ui.js
# ckpt  s2 node      =   0   # node --check
# ckpt  s2 push      =   0   # pushes Jack's phone
# needs s2 endtoend  = none
# needs s2 ledger    = none
# needs s2 grid      = s2 endtoend
# needs s2 pool      = s2 endtoend
# needs s2 pickA     = s2 grid
# needs s2 pickB     = s2 pool
# needs s2 paired    = s2 pickA
# needs s2 report    = s2 pickA
# needs s2 rolling   = s2 pickB
# needs s2 costcap   = s2 endtoend
# needs s2 fewer     = s2 endtoend
# needs s2 audfill   = none
# needs s2 audrest   = none
# needs s2 md        = s2 report
# needs s2 app       = s2 md
# needs s2 node      = s2 app
# needs s2 push      = s2 md
# disk  s2 endtoend  = 0.05  # four small csvs
# disk  s2 ledger    = 0     # one csv append
# disk  s2 grid      = 0.1   # yearly and grid csvs, 6 rulesets
# disk  s2 pool      = 0.3   # 39 indicators of yearly rows plus shard parts
# disk  s2 pickA     = 0     # one csv
# disk  s2 pickB     = 0     # one csv
# disk  s2 paired    = 0.05  # one csv
# disk  s2 report    = 0.05  # two csvs
# disk  s2 rolling   = 0.05  # two csvs
# disk  s2 costcap   = 0.05  # one csv
# disk  s2 fewer     = 0.05  # one csv
# disk  s2 audfill   = 0.05  # one csv
# disk  s2 audrest   = 0.1   # four csvs
# disk  s2 md        = 0     # two markdown files
# disk  s2 app       = 0.1   # rewrites app_data.json
# disk  s2 node      = 0     # node --check
# disk  s2 push      = 0     # one http request
. "${FX_CHAIN_LIB:-/Users/jackcuster/fx-data/code/chain/chainlib.sh}" "$0" "L2 CHAIN 30 COMPLETE"
cd /Users/jackcuster/fx-data
export FX_COST_TABLE=results/cost_table_h22.csv
export FX_CKPT_SECONDS=300
export FX_CI_LOCAL=1

say "=== LAYER 2 CHAIN 30: stage 2, the baseline added to C1 ==="

# ---- THE FIVE-MINUTE RULE. One C1 x one baseline all the way through the save
# and read path, including the control check that gates every paired number.
g "s2 endtoend" nice -n 19 python3 code/nnfx2s.py --stage smoke
ci "Stage 2 end to end: one combination through grid, pick, control check and report"

g "s2 ledger" nice -n 19 python3 code/nnfx2s.py --stage ledger
ci "Jack's stage 2 picks recorded in CANDIDATE_LEDGER.csv and HANDOFF 0m"

# ---- 2a. All six rulesets on the three named C1 picks.
g "s2 grid" nice -n 19 python3 code/nnfx2s.py --stage grid
g "s2 pickA" nice -n 19 python3 code/nnfx2s.py --stage pick --tag picks
ci "2a: every C1 x baseline x setting pair x plan x ruleset, settings picked walk-forward"

# ---- the 39-C1 pool the ROLLING TOP 3 rule ranks on. Sharded: this is the
# only heavy stage in the chain.
g "s2 pool" nice -n 19 python3 code/nnfx2s.py --stage pool --jobs 6
g "s2 pickB" nice -n 19 python3 code/nnfx2s.py --stage pick --tag pool
ci "The 39-indicator pool for the rolling rule, tuned on the eleven-step walk"

# ---- 2b, 2c
g "s2 paired" nice -n 19 python3 code/nnfx2s.py --stage paired
ci "2b: the paired test on the same days, and which rule inside the baseline does the work"

g "s2 report" nice -n 19 python3 code/nnfx2s.py --stage report
ci "2c: each combination on the unseen years, both t statistics, true dip, prop simulator"

# ---- 2f, 2d, 2e, in Jack's order
g "s2 rolling" nice -n 19 python3 code/nnfx2s.py --stage rolling
ci "2f: the rolling top-K rule for K 1 to 10, with turnover and the picked set per year"

g "s2 costcap" nice -n 19 python3 code/nnfx2s.py --stage costcap
ci "2d: pairs capped by cost over ATR, known in advance, swept over the full range"

g "s2 fewer" nice -n 19 python3 code/nnfx2s.py --stage fewer
ci "2e: a minimum trade gap and a minimum signal age, each swept"

# ---- engine audit 2. Independent of everything above, so it declares no deps.
g "s2 audfill" nice -n 19 python3 code/nnfxaudit2.py --stage fill
g "s2 audrest" bash -c '
set -e
nice -n 19 python3 code/nnfxaudit2.py --stage fin
nice -n 19 python3 code/nnfxaudit2.py --stage cost
nice -n 19 python3 code/nnfxaudit2.py --stage vol'
ci "Engine audit 2: fill price, financing, cost per R by pair and year, tick volume"

g "s2 md" bash -c '
set -e
nice -n 19 python3 code/nnfx2s.py --stage md
nice -n 19 python3 code/nnfxaudit2.py --stage md'
ci "STAGE2.md and ENGINE_AUDIT_2.md"

g "s2 app"  nice -n 19 python3 code/r2app.py --stage app
g "s2 node" node --check app_ui.js
ci "Stage 2 wired into the app"

g "s2 push" nice -n 19 python3 code/l2r2push.py --what "stage 2: the baseline added to C1" \
   --file results/nnfx/STAGE2.md

chain_summary
say "L2 CHAIN 30 COMPLETE"
