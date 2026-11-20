#!/bin/bash
# LAYER 2 RESTART, CHAIN 19: THE PASSERS' BOOKS ON MODE A UNDER ALL THREE
# MEMBERSHIP RULES, WITH MEMBER LISTS AND A RANDOM-PICK COMPARISON.
#
# Jack, 20 Nov: "Gate 3 passers' book, strict version, modes A and B ... Also
# run the 5-year version ... For each: members per step, equal weight, routed
# and always-on, both budgets, the full KPI table, the three nulls, and the
# list of every member with its settings and per-year R. Report alongside: how
# many strategies pass under each rule and what a random pick of the same size
# does. Launch without waiting; push my phone when it lands."
#
# MODE A RUNS NOW, MODE B RUNS IN CHAIN 20. Mode A's gate 3 bank is complete,
# so this is ~25 min of work and Jack has the answer today. Mode B's bank is
# being built by chain 18 right now and will not exist until ~17:00, so
# l2r2v.sh is armed to launch on chain 18's completion marker rather than
# running here and failing on a bank that is not there yet.
#
# FOUR WORKERS, NOT EIGHT. Chain 18 is using eight on its score stage; this
# chain's work is small and taking the other two cores would slow a 6.7-hour
# stage to save a couple of minutes here.
#
# approval = none   new membership rules, but Jack specified both in full on 20 Nov and said "launch without waiting" -- the approval is the instruction, not a hash
#
# deliverable = /Users/jackcuster/fx-data/results/r2gate2/MODEA_PASSERBOOKS.md
# eta = 45
#
# --- CHECKPOINT, DEPENDENCY AND DISK DECLARATIONS ---
# ckpt  pb endtoend     =  60   # the fiveyr book built from nothing, saved and read back; runs FIRST
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
# ckpt  pb md A         =   0   # MODEA_PASSERBOOKS.md, every number quoted from a named file
# ckpt  pb app          =   0   # rewrites app_data.json and app_ui.js in one pass
# ckpt  pb node         =   0   # node --check, seconds
# ckpt  pb push         =   0   # pushes Jack's phone that the deliverable landed
# needs pb endtoend     = none
# needs pb mask strict  = none
# needs pb mask fiveyr  = none
# needs pb book strict  = pb endtoend, pb mask strict
# needs pb book fiveyr  = pb endtoend, pb mask fiveyr
# needs pb nulls strict = pb book strict
# needs pb nulls fiveyr = pb book fiveyr
# needs pb mem grade    = none
# needs pb mem strict   = pb mask strict
# needs pb mem fiveyr   = pb mask fiveyr
# needs pb pick strict  = pb mask strict
# needs pb pick fiveyr  = pb mask fiveyr
# needs pb md A         = none
# needs pb app          = none
# needs pb node         = pb app
# needs pb push         = none
# disk  pb endtoend     = 0.1   # one rule's book parts at 8 shards
# disk  pb mask strict  = 0     # one bool array, (273,780 x 4 x 5)
# disk  pb mask fiveyr  = 0     # one bool array, (273,780 x 4 x 5)
# disk  pb book strict  = 0.1   # 16 shards x 4 steps, membership is 473 cells
# disk  pb book fiveyr  = 0.1   # 16 shards x 5 steps, membership is 1,211 cells
# disk  pb nulls strict = 0.4   # one step of null scratch at a time, deleted once summed
# disk  pb nulls fiveyr = 0.4   # one step of null scratch at a time, deleted once summed
# disk  pb mem grade    = 0.1   # one csv, 59,268 rows x 47 columns
# disk  pb mem strict   = 0     # one csv, 473 rows
# disk  pb mem fiveyr   = 0     # one csv, 1,211 rows
# disk  pb pick strict  = 0.1   # five draws, tiny membership
# disk  pb pick fiveyr  = 0.1   # five draws, tiny membership
# disk  pb md A         = 0     # one markdown file
# disk  pb app          = 0.1   # rewrites app_data.json
# disk  pb node         = 0     # node --check
# disk  pb push         = 0     # one http request
. "${FX_CHAIN_LIB:-/Users/jackcuster/fx-data/code/chain/chainlib.sh}" "$0" "L2 RESTART CHAIN 19 COMPLETE"
cd /Users/jackcuster/fx-data
export FX_COST_TABLE=results/cost_table_h22.csv
export FX_CKPT_SECONDS=300
J=4
NS=16
PD=5

say "=== LAYER 2 RESTART CHAIN 19: mode A passers' books, three membership rules ==="

# The fiveyr book has never been built, so building it IS the save/read test.
g "pb endtoend" bash -c '
set -e
nice -n 19 python3 code/l2r2gate3.py --stage passmask --mode A --rule fiveyr
nice -n 19 python3 code/l2r2gate3.py --stage book --mode A --rule fiveyr --jobs 2 --nshard 8
test -s results/r2gate2/modeA_gate3_passersbook_fiveyr.csv
echo "  END TO END: the fiveyr book saved and read back, $(wc -l < results/r2gate2/modeA_gate3_passersbook_fiveyr.csv) lines"'

g "pb mask strict" nice -n 19 python3 code/l2r2gate3.py --stage passmask --mode A --rule strict
g "pb mask fiveyr" nice -n 19 python3 code/l2r2gate3.py --stage passmask --mode A --rule fiveyr

g "pb book strict" nice -n 19 python3 code/l2r2gate3.py --stage book --mode A --rule strict --jobs $J --nshard $NS
g "pb book fiveyr" nice -n 19 python3 code/l2r2gate3.py --stage book --mode A --rule fiveyr --jobs $J --nshard $NS
ci "Mode A passers' books under the strict and 5-year rules"

g "pb nulls strict" nice -n 19 python3 code/l2r2gate3.py --stage booknulls --mode A --rule strict --jobs $J --draws 20 --id-draws 200
g "pb nulls fiveyr" nice -n 19 python3 code/l2r2gate3.py --stage booknulls --mode A --rule fiveyr --jobs $J --draws 20 --id-draws 200
ci "Mode A passers' books: the three nulls under both new rules"

g "pb mem grade"  nice -n 19 python3 code/l2r2gate3.py --stage members --mode A --rule grade
g "pb mem strict" nice -n 19 python3 code/l2r2gate3.py --stage members --mode A --rule strict
g "pb mem fiveyr" nice -n 19 python3 code/l2r2gate3.py --stage members --mode A --rule fiveyr
ci "Mode A member lists: every member with its resolved settings and per-year R, all three rules"

# THE GRADE RULE'S RANDOM PICK IS IN CHAIN 20, NOT HERE. Its books carry the
# full 24,296 members, so one draw's part files are ~0.9 GB -- the largest
# single disk peak in this work. Chain 18 is still writing its own parts and
# free space is 6 GB; filling the volume would take down a stage with 6.7 h
# invested in it, to save minutes here. The two new rules Jack asked about are
# tiny and run now.
g "pb pick strict" nice -n 19 python3 code/l2r2gate3.py --stage randompick --mode A --rule strict --jobs $J --nshard $NS --pick-draws $PD
g "pb pick fiveyr" nice -n 19 python3 code/l2r2gate3.py --stage randompick --mode A --rule fiveyr --jobs $J --nshard $NS --pick-draws $PD
ci "Mode A: what a random pick of the same size does, five draws per rule, sizes matched per (step, stream)"

g "pb md A" nice -n 19 python3 code/l2r2gate3.py --stage passerbooks --mode A
ci "MODEA_PASSERBOOKS.md: the three membership rules side by side"

g "pb app"  nice -n 19 python3 code/r2app.py --stage app
g "pb node" node --check app_ui.js
ci "Mode A passers' books wired into the app"

# ---- PUSH JACK'S PHONE, as asked. The watchdog pushes on a MISSING
# deliverable; this pushes on a PRESENT one, which is the thing Jack wanted to
# hear about and is not otherwise notified.
g "pb push" bash -c '
D=results/r2gate2/MODEA_PASSERBOOKS.md
T=$(tr -d "[:space:]" < "$HOME/fx-data-logs/ntfy_topic")
if [ -s "$D" ]; then
  B="MODEA_PASSERBOOKS.md is written: $(wc -l < $D) lines, three membership rules side by side. Free space $(df -g /System/Volumes/Data | tail -1 | awk "{print \$4}") GB. Mode B follows in chain 20 behind chain 18."
  printf "%s" "$B" | curl -s -o /dev/null -w "  push -> ntfy HTTP %{http_code}\n" --max-time 20 \
    -H "Title: fx-data: mode A passers books LANDED" -H "Priority: default" -H "Tags: books" \
    -d @- "https://ntfy.sh/$T"
else
  echo "  deliverable missing, not pushing a false landing"; exit 1
fi'

chain_summary
say "L2 RESTART CHAIN 19 COMPLETE"
