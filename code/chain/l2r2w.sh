#!/bin/bash
# LAYER 2 RESTART, CHAIN 20: THE PASSERS' BOOKS ON MODE B UNDER ALL THREE
# MEMBERSHIP RULES, PLUS THE FULL-SIZE RANDOM PICKS HELD BACK FROM CHAIN 19.
#
# Jack, 20 Nov: "Gate 3 passers' book, strict version, modes A and B ... Also
# run the 5-year version ... Launch without waiting; push my phone when it
# lands."
#
# THIS CHAIN IS ARMED BEHIND CHAIN 18, not launched beside it. Mode B's gate 3
# KPI bank is exactly what chain 18 is building, so until its score stage lands
# there is nothing here to read. code/chain/arm_next.sh watches for chain 18's
# completion marker and launches this, so nobody has to sit and wait for it.
# Two chains cannot run at once in any case: launch.sh writes
# ~/fx-data-logs/chain_current unconditionally and chainwatch.sh sources that
# one file, so a second launch orphans the first chain from its own watchdog.
#
# IT ALSO CARRIES THE FULL-SIZE RANDOM PICKS for both modes under the `grade`
# rule. One draw of a 24,296-member book is ~0.9 GB of part files, which was
# the largest disk peak in this work; chain 18 was still writing and free space
# was 6 GB. By the time this runs chain 18 is done.
#
# approval = none   the same three rules Jack specified on 20 Nov, re-run on the other mode -- the amended guard 6 names "another mode" explicitly
#
# deliverable = /Users/jackcuster/fx-data/results/r2gate2/MODEB_PASSERBOOKS.md
# eta = 120
#
# --- CHECKPOINT, DEPENDENCY AND DISK DECLARATIONS ---
# ckpt  pb endtoend     =  60   # asserts mode B's bank is complete, then builds/saves/reads its fiveyr book; runs FIRST
# ckpt  pb mask strict  =   0   # one bool array off the KPI bank, no engine pass
# ckpt  pb mask fiveyr  =   0   # one bool array off the KPI bank, no engine pass
# ckpt  pb book strict  = 300   # per-shard book parts on the 300 s clock, resume by set difference
# ckpt  pb book fiveyr  = 300   # per-shard book parts on the 300 s clock, resume by set difference
# ckpt  pb nulls strict = 300   # identity off the saved series, then two engine nulls per step
# ckpt  pb nulls fiveyr = 300   # identity off the saved series, then two engine nulls per step
# ckpt  pb mem grade    =   0   # resolves winner indices to settings, reads the bank
# ckpt  pb mem strict   =   0   # resolves winner indices to settings, reads the bank
# ckpt  pb mem fiveyr   =   0   # resolves winner indices to settings, reads the bank
# ckpt  pb pick strict  = 300   # 5 random books of matched size, scratch deleted per draw
# ckpt  pb pick fiveyr  = 300   # 5 random books of matched size, scratch deleted per draw
# ckpt  pb pick full    = 300   # the full-size grade picks, both modes, scratch deleted per draw
# ckpt  pb md B         =   0   # MODEB_PASSERBOOKS.md, every number quoted from a named file
# ckpt  pb md A         =   0   # MODEA_PASSERBOOKS.md again, now its grade pick exists
# ckpt  pb app          =   0   # rewrites app_data.json and app_ui.js in one pass
# ckpt  pb node         =   0   # node --check, seconds
# ckpt  pb push         =   0   # pushes Jack's phone that the deliverable landed
# needs pb endtoend     = none
# needs pb mask strict  = pb endtoend
# needs pb mask fiveyr  = pb endtoend
# needs pb book strict  = pb endtoend, pb mask strict
# needs pb book fiveyr  = pb endtoend, pb mask fiveyr
# needs pb nulls strict = pb book strict
# needs pb nulls fiveyr = pb book fiveyr
# needs pb mem grade    = pb endtoend
# needs pb mem strict   = pb mask strict
# needs pb mem fiveyr   = pb mask fiveyr
# needs pb pick strict  = pb mask strict
# needs pb pick fiveyr  = pb mask fiveyr
# needs pb pick full    = pb endtoend
# needs pb md B         = none
# needs pb md A         = none
# needs pb app          = none
# needs pb node         = pb app
# needs pb push         = none
# disk  pb endtoend     = 0.1   # one rule's book parts at 8 shards
# disk  pb mask strict  = 0     # one bool array, (273,780 x 4 x 5)
# disk  pb mask fiveyr  = 0     # one bool array, (273,780 x 4 x 5)
# disk  pb book strict  = 0.1   # 32 shards x 4 steps, membership is small
# disk  pb book fiveyr  = 0.1   # 32 shards x 5 steps, membership is small
# disk  pb nulls strict = 0.4   # one step of null scratch at a time, deleted once summed
# disk  pb nulls fiveyr = 0.4   # one step of null scratch at a time, deleted once summed
# disk  pb mem grade    = 0.1   # one csv, tens of thousands of rows x 47 columns
# disk  pb mem strict   = 0     # one csv, hundreds of rows
# disk  pb mem fiveyr   = 0     # one csv,about a thousand rows
# disk  pb pick strict  = 0.1   # five draws, small membership
# disk  pb pick fiveyr  = 0.1   # five draws, small membership
# disk  pb pick full    = 0.9   # one draw of a full-size book at a time, deleted after each
# disk  pb md B         = 0     # one markdown file
# disk  pb md A         = 0     # one markdown file
# disk  pb app          = 0.1   # rewrites app_data.json
# disk  pb node         = 0     # node --check
# disk  pb push         = 0     # one http request
. "${FX_CHAIN_LIB:-/Users/jackcuster/fx-data/code/chain/chainlib.sh}" "$0" "L2 RESTART CHAIN 20 COMPLETE"
cd /Users/jackcuster/fx-data
export FX_COST_TABLE=results/cost_table_h22.csv
export FX_CKPT_SECONDS=300
J=8
NS=32
PD=5

say "=== LAYER 2 RESTART CHAIN 20: mode B passers' books, three membership rules ==="

# THE BANK CHECK LIVES INSIDE THE END-TO-END STAGE. The guard requires the
# end-to-end test to be the chain's FIRST stage, and the test cannot build a
# book without the bank, so the assert belongs here rather than in a stage
# ahead of it. Everything that reads the bank declares a dependency on this.
g "pb endtoend" bash -c '
set -e
nice -n 19 python3 code/l2r2bankchk.py --mode B
nice -n 19 python3 code/l2r2gate3.py --stage passmask --mode B --rule fiveyr
nice -n 19 python3 code/l2r2gate3.py --stage book --mode B --rule fiveyr --jobs 2 --nshard 8
test -s results/r2gate2/modeB_gate3_passersbook_fiveyr.csv
echo "  END TO END: mode B fiveyr book saved and read back"'

g "pb mask strict" nice -n 19 python3 code/l2r2gate3.py --stage passmask --mode B --rule strict
g "pb mask fiveyr" nice -n 19 python3 code/l2r2gate3.py --stage passmask --mode B --rule fiveyr

g "pb book strict" nice -n 19 python3 code/l2r2gate3.py --stage book --mode B --rule strict --jobs $J --nshard $NS
g "pb book fiveyr" nice -n 19 python3 code/l2r2gate3.py --stage book --mode B --rule fiveyr --jobs $J --nshard $NS
ci "Mode B passers' books under the strict and 5-year rules"

g "pb nulls strict" nice -n 19 python3 code/l2r2gate3.py --stage booknulls --mode B --rule strict --jobs $J --draws 20 --id-draws 200
g "pb nulls fiveyr" nice -n 19 python3 code/l2r2gate3.py --stage booknulls --mode B --rule fiveyr --jobs $J --draws 20 --id-draws 200
ci "Mode B passers' books: the three nulls under both new rules"

g "pb mem grade"  nice -n 19 python3 code/l2r2gate3.py --stage members --mode B --rule grade
g "pb mem strict" nice -n 19 python3 code/l2r2gate3.py --stage members --mode B --rule strict
g "pb mem fiveyr" nice -n 19 python3 code/l2r2gate3.py --stage members --mode B --rule fiveyr
ci "Mode B member lists: every member with its resolved settings and per-year R"

g "pb pick strict" nice -n 19 python3 code/l2r2gate3.py --stage randompick --mode B --rule strict --jobs $J --nshard $NS --pick-draws $PD
g "pb pick fiveyr" nice -n 19 python3 code/l2r2gate3.py --stage randompick --mode B --rule fiveyr --jobs $J --nshard $NS --pick-draws $PD

# THE FULL-SIZE PICKS, both modes, held back from chain 19 on disk grounds.
g "pb pick full" bash -c '
set -e
nice -n 19 python3 code/l2r2gate3.py --stage randompick --mode B --rule grade --jobs 8 --nshard 32 --pick-draws 5
nice -n 19 python3 code/l2r2gate3.py --stage randompick --mode A --rule grade --jobs 8 --nshard 32 --pick-draws 5'
ci "What a random pick of the same size does: five draws per rule per mode, sizes matched per (step, stream)"

g "pb md B" nice -n 19 python3 code/l2r2gate3.py --stage passerbooks --mode B
g "pb md A" nice -n 19 python3 code/l2r2gate3.py --stage passerbooks --mode A
ci "MODEB_PASSERBOOKS.md, and MODEA_PASSERBOOKS.md with its grade random pick filled in"

g "pb app"  nice -n 19 python3 code/r2app.py --stage app
g "pb node" node --check app_ui.js
ci "Both modes' passers' books wired into the app"

g "pb push" nice -n 19 python3 code/l2r2push.py --what "mode B passers books" \
   --file results/r2gate2/MODEB_PASSERBOOKS.md \
   --also results/r2gate2/MODEA_PASSERBOOKS.md

chain_summary
say "L2 RESTART CHAIN 20 COMPLETE"
