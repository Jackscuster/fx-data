#!/bin/bash
# LAYER 2 RESTART, CHAIN 27: CHUNK 2 RERUN, THEN B1-NARROW.
#
# Jack, 24 Nov, after the 02:04 power loss: re-arm any chunk 2-4 stage that did
# not complete in full, then B1-narrow, then 22A resume.
#
# WHAT DID NOT COMPLETE: only chunk 2. Chain 24 died in 6 seconds on a
# NameError of mine (the __main__ dispatch sat above the functions it called),
# so A2, A1-on-defaults and A3 never ran in full. Chunk 1 (chain 23, 9/0),
# chunk 3 (chain 25, 7/0) and chunk 4 (chain 26, 8/0) all COMPLETED and are not
# repeated.
#
# B1-NARROW RUNS THE SAMPLED UNIVERSE. Measured at 6.86 s/strategy on 8
# workers, the full 16,040-strategy universe is 30.6 h per mode. With the
# family sampled to 2,000 it is 4,010 per mode and 7.6 h per mode, which
# answers the same questions with a stated sampling error. The winners and the
# control are kept whole.
#
# approval = none   a rerun of stages Jack already specified, plus the narrow walk he specified on 24 Nov
#
# deliverable = /Users/jackcuster/fx-data/results/r2reads/B1_NARROW.md
# eta = 1200
#
# --- CHECKPOINT, DEPENDENCY AND DISK DECLARATIONS ---
# ckpt  c2 endtoend  =  60   # the A2 default pass on 20 strategies, saved and read back; runs FIRST
# ckpt  c2 a3        =   0   # block bootstrap on the saved daily series
# ckpt  c2 a2 A      = 300   # the default configuration scored, 32 shards
# ckpt  c2 cmp A     =   0   # tuned minus default plus A1 on defaults
# ckpt  c2 a2 B      = 300   # the same on mode B
# ckpt  c2 cmp B     =   0   # the same on mode B
# ckpt  b1 cond1     =   0   # year-end MTM assert on the ELEVEN-step walk
# ckpt  b1 cond2     = 300   # per-step equivalence on the eleven-step walk
# ckpt  b1 uni       =   0   # the sampled universe, read-only
# ckpt  b1 tune A    = 300   # eleven-step tune, part file every 300 s per worker
# ckpt  b1 tune B    = 300   # the same on mode B
# ckpt  b1 md        =   0   # B1_NARROW.md
# ckpt  c2 app       =   0   # rewrites app_data.json and app_ui.js
# ckpt  c2 node      =   0   # node --check
# ckpt  c2 push      =   0   # pushes Jack's phone
# needs c2 endtoend  = none
# needs c2 a3        = none
# needs c2 a2 A      = c2 endtoend
# needs c2 cmp A     = c2 a2 A
# needs c2 a2 B      = c2 endtoend
# needs c2 cmp B     = c2 a2 B
# needs b1 cond1     = none
# needs b1 cond2     = none
# needs b1 uni       = none
# needs b1 tune A    = b1 cond1, b1 cond2, b1 uni
# needs b1 tune B    = b1 cond1, b1 cond2, b1 uni
# needs b1 md        = b1 tune A
# needs c2 app       = none
# needs c2 node      = c2 app
# needs c2 push      = none
# disk  c2 endtoend  = 0.1   # one csv on a slice
# disk  c2 a3        = 0.1   # one csv
# disk  c2 a2 A      = 0.6   # 32 shard csvs then one concatenated
# disk  c2 cmp A     = 0.2   # two csvs and one markdown
# disk  c2 a2 B      = 0.6   # the same on mode B
# disk  c2 cmp B     = 0.2   # two csvs
# disk  b1 cond1     = 0     # one csv
# disk  b1 cond2     = 0     # one csv
# disk  b1 uni       = 0     # one csv
# disk  b1 tune A    = 0.2   # the eleven-step winner-only bank, 8.28 kB/strategy measured
# disk  b1 tune B    = 0.2   # the same on mode B
# disk  b1 md        = 0     # one markdown file
# disk  c2 app       = 0.1   # rewrites app_data.json
# disk  c2 node      = 0     # node --check
# disk  c2 push      = 0     # one http request
. "${FX_CHAIN_LIB:-/Users/jackcuster/fx-data/code/chain/chainlib.sh}" "$0" "L2 RESTART CHAIN 27 COMPLETE"
cd /Users/jackcuster/fx-data
export FX_COST_TABLE=results/cost_table_h22.csv
export FX_CKPT_SECONDS=300
export FX_CI_LOCAL=1

say "=== LAYER 2 RESTART CHAIN 27: chunk 2 rerun, then B1-narrow ==="

g "c2 endtoend" bash -c '
set -e
nice -n 19 python3 code/r2reads.py --stage a2 --mode A --jobs 2 --nshard 2 --nmax 20
test -s results/r2reads/modeA_a2_defaults.csv
echo "  END TO END: the default pass wrote and read back"'

g "c2 a3" nice -n 19 python3 code/r2reads.py --stage a3 --mode A --draws 2000
ci "A3: yearly return over vol, worst dip, 20-day block-bootstrap t beside the naive daily t"

g "c2 a2 A"  nice -n 19 python3 code/r2reads.py --stage a2 --mode A --jobs 8 --nshard 32
g "c2 cmp A" nice -n 19 python3 code/r2reads.py --stage a2cmp --mode A
ci "A2 mode A: tuned minus default on the unseen years, and A1 repeated on the defaults"

g "c2 a2 B"  nice -n 19 python3 code/r2reads.py --stage a2 --mode B --jobs 8 --nshard 32
g "c2 cmp B" nice -n 19 python3 code/r2reads.py --stage a2cmp --mode B
ci "A2 mode B: the same"

# ---- B1-NARROW on the eleven-step walk. FX_WALK is set per stage so chunk 2
# above runs on the five-step walk the existing banks were built on.
g "b1 cond1" env FX_WALK=ext11 nice -n 19 python3 code/l2r2gate2.py --stage cond1 --mode A --n 8
g "b1 cond2" env FX_WALK=ext11 nice -n 19 python3 code/l2r2gate2.py --stage cond2 --mode A --n 6 --minutes 25
ci "B1-narrow: both conditions re-proven on the eleven-step walk"

g "b1 uni" env FX_WALK=ext11 nice -n 19 python3 -c "
import sys; sys.path.insert(0,'code')
import b1narrow as B
for m in ('A','B'): B.universe_sampled(m, family_n=2000)"

g "b1 tune A" env FX_WALK=ext11 nice -n 19 python3 code/b1narrow.py --stage tune --mode A --jobs 8 --nshard 32
ci "B1-narrow mode A: the sampled universe tuned on the eleven-step walk"
g "b1 tune B" env FX_WALK=ext11 nice -n 19 python3 code/b1narrow.py --stage tune --mode B --jobs 8 --nshard 32
ci "B1-narrow mode B: the same"

g "b1 md" env FX_WALK=ext11 nice -n 19 python3 code/b1narrow.py --stage md
ci "B1_NARROW.md: the six never-seen years, per winner and as cohort distributions"

g "c2 app"  nice -n 19 python3 code/r2app.py --stage app
g "c2 node" node --check app_ui.js
ci "Chunk 2 and B1-narrow wired into the app"

g "c2 push" nice -n 19 python3 code/l2r2push.py --what "chunk 2 rerun and B1-narrow" \
   --file results/r2reads/A2_A3_TUNED_AND_SIGNIFICANCE.md

chain_summary
say "L2 RESTART CHAIN 27 COMPLETE"
