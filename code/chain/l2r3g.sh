#!/bin/bash
# LAYER 2, CHAIN 29: B1-NARROW FAMILY AND CONTROL, ON THE FIXED CODE.
#
# WHY THIS CHAIN EXISTS, AND IT IS A FAULT OF MINE.
#
# Chain 27 was launched at 09:39 from commit 6bd0bfd and launch.sh froze a copy
# of code/ into its run directory, which is the guard working as designed. But
# the two commits that FIXED b1narrow.py landed AFTER that snapshot:
#
#   167bc13  the 10 winners do not survive the six years
#   e879686  B1_WINNERS.md was wrong: I summed the four streams instead of
#            selecting the winner's own stream
#
# So chain 27's frozen copy still carries the stream bug Jack rejected
# B1_WINNERS.md for, and it has no condition3() at all. Its `b1 tune` and
# `b1 md` stages would have produced B1_NARROW.md from that code, with no
# cross-walk gate in front of it. Chain 27 is therefore stopped after its last
# chunk 2 marker ("OK c2 cmp B") and the B1 half runs here instead, on HEAD.
#
# WHAT ELSE MOVES HERE. Chain 27's `c2 app`, `c2 node` and `c2 push` stages sit
# after `b1 md` in its driver and would be skipped by the stop, so they run
# here. Nothing of chunk 2 is lost.
#
# CONDITION 3 IS THE FIRST GATE AND IT IS HARD. Jack, 24 Nov: "Nothing from
# 2010 to 2015 is quoted until it passes." b1narrow.py --stage cond3 raises
# SystemExit on failure, so the stage FAILS, and `needs` below makes every
# stage that would quote an ext11 number a dependent of it. A chain that cannot
# prove the cross-walk property writes no report.
#
# approval = none   the B1 family and control stage Jack specified, relaunched on fixed code
#
# deliverable = /Users/jackcuster/fx-data/results/r2reads/B1_NARROW.md
# eta = 1000
#
# --- CHECKPOINT, DEPENDENCY AND DISK DECLARATIONS ---
# ckpt  b1w endtoend =  60   # 20 strategies banked and read back UNDER ITS OWN TAG; runs FIRST
# ckpt  b1w cond3    =   0   # condition 3 on the winner bank already on disk; gates everything that quotes ext11
# ckpt  b1w cond1    =   0   # year-end MTM identity on the eleven-step walk
# ckpt  b1w cond2    = 300   # per-step equivalence on the eleven-step walk
# ckpt  b1w samp     =   0   # the sampled universe, read-only
# ckpt  b1w tune A   = 300   # eleven-step tune, part file every 300 s per worker
# ckpt  b1w tune B   = 300   # the same on mode B
# ckpt  b1w md       =   0   # B1_NARROW.md
# ckpt  b1w app      =   0   # rewrites app_data.json and app_ui.js
# ckpt  b1w node     =   0   # node --check
# ckpt  b1w push     =   0   # pushes Jack's phone
# needs b1w endtoend = none
# needs b1w cond3    = none
# needs b1w cond1    = none
# needs b1w cond2    = none
# needs b1w samp     = none
# needs b1w tune A   = b1w endtoend, b1w cond3, b1w cond1, b1w cond2, b1w samp
# needs b1w tune B   = b1w endtoend, b1w cond3, b1w cond1, b1w cond2, b1w samp
# needs b1w md       = b1w cond3, b1w tune A
# needs b1w app      = none
# needs b1w node     = b1w app
# needs b1w push     = b1w md
# disk  b1w endtoend = 0.1   # one throwaway shard pair under its own tag
# disk  b1w cond3    = 0     # one csv
# disk  b1w cond1    = 0     # one csv, walk-suffixed so it cannot overwrite 22A's
# disk  b1w cond2    = 0     # one csv, the same
# disk  b1w samp     = 0     # one csv per mode
# disk  b1w tune A   = 0.2   # the eleven-step bank, 8.28 kB/strategy measured
# disk  b1w tune B   = 0.2   # the same on mode B
# disk  b1w md       = 0     # one markdown file
# disk  b1w app      = 0.1   # rewrites app_data.json
# disk  b1w node     = 0     # node --check
# disk  b1w push     = 0     # one http request
. "${FX_CHAIN_LIB:-/Users/jackcuster/fx-data/code/chain/chainlib.sh}" "$0" "L2 CHAIN 29 COMPLETE"
cd /Users/jackcuster/fx-data
export FX_COST_TABLE=results/cost_table_h22.csv
export FX_CKPT_SECONDS=300
export FX_CI_LOCAL=1

say "=== LAYER 2 CHAIN 29: B1-narrow family and control, on the fixed code ==="

# ---- THE FIVE-MINUTE RULE, AND A TRAP IT NEARLY WALKED INTO.
#
# gate 2's run() resumes PER SHARD, not per strategy: "a shard present is never
# recomputed", and shard k holds the strided slice combos[k::nshard]. So a
# smoke run of 20 strategies at --nshard 2 would write shard_00 and shard_01
# into the REAL b1narrow directory, and the 32-shard full run would then see
# those two files present and skip them -- silently dropping about 250
# strategies per mode from the bank, with every downstream number computed on a
# universe quietly smaller than the one declared.
#
# So the end-to-end test banks under its OWN tag, b1narrow_smoke, and asserts
# the read-back. It exercises the identical save and read path and cannot touch
# the real bank.
g "b1w endtoend" env FX_WALK=ext11 nice -n 19 python3 -c "
import sys, os; sys.path.insert(0,'code')
import numpy as np, pandas as pd
import b1narrow as B, l2r2gate2 as G2, l2sweep as S
assert G2.WALK == 'ext11', G2.WALK
S.load_costs()
f = os.path.join(B.OUT, 'modeA_b1narrow_universe.csv')
if not os.path.exists(f): B.universe('A')
U = pd.read_csv(f).head(20)
combos = [tuple(x.split('|')) for x in U.sid]
od, _res = G2.run('A', combos, 'b1narrow_smoke', jobs=2, cap=30000, nshard=2)
# G2.load RETURNS FIVE ARRAYS, NOT THREE. The first version of this stage
# unpacked three and died on 'too many values to unpack' after banking all 20
# strategies correctly -- the smoke proved the save path and then failed on its
# own read-back. Unpack by index so the count is explicit.
_L = G2.load('A', 'b1narrow_smoke')
assert len(_L) >= 2, 'load returned %d arrays' % len(_L)
n_read = len(_L[1])
assert n_read == 20, 'banked and read back %d of 20' % n_read
assert float(np.abs(np.asarray(_L[1], float)).sum()) > 0, 'read back all zeros'
print('  END TO END: 20 strategies banked under b1narrow_smoke and read back '
      '(%d arrays, %d rows)' % (len(_L), n_read))
"

# ---- THE GATE. Runs on its own, so a failure is unambiguous.
g "b1w cond3" env FX_WALK=ext11 nice -n 19 python3 code/b1narrow.py --stage cond3
ci "Condition 3: the eleven-step walk reproduces the five-step bank on the shared years"

g "b1w cond1" env FX_WALK=ext11 nice -n 19 python3 code/l2r2gate2.py --stage cond1 --mode A --n 8
g "b1w cond2" env FX_WALK=ext11 nice -n 19 python3 code/l2r2gate2.py --stage cond2 --mode A --n 6 --minutes 25
ci "Conditions 1 and 2 re-proven on the eleven-step walk, into walk-suffixed files"

g "b1w samp" env FX_WALK=ext11 nice -n 19 python3 -c "
import sys; sys.path.insert(0,'code')
import b1narrow as B
for m in ('A','B'): B.universe_sampled(m, family_n=2000)"

g "b1w tune A" env FX_WALK=ext11 nice -n 19 python3 code/b1narrow.py --stage tune --mode A --jobs 8 --nshard 32
ci "B1-narrow mode A: the sampled family and the whole control tuned on the eleven-step walk"
g "b1w tune B" env FX_WALK=ext11 nice -n 19 python3 code/b1narrow.py --stage tune --mode B --jobs 8 --nshard 32
ci "B1-narrow mode B: the same"

g "b1w md" env FX_WALK=ext11 nice -n 19 python3 code/b1narrow.py --stage md
ci "B1_NARROW.md: the six never-seen years, per winner and as cohort distributions"

# ---- chunk 2's app wiring, which the stop of chain 27 skips
g "b1w app"  nice -n 19 python3 code/r2app.py --stage app
g "b1w node" node --check app_ui.js
ci "Chunk 2 and B1-narrow wired into the app"

g "b1w push" nice -n 19 python3 code/l2r2push.py --what "B1-narrow family and control, on fixed code" \
   --file results/r2reads/B1_NARROW.md

chain_summary
say "L2 CHAIN 29 COMPLETE"
