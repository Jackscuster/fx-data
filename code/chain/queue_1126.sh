#!/bin/bash
# THE 26 NOVEMBER QUEUE. One stage at a time, in priority order, because the
# machine has 2048 MB of swap now where it had 7680 MB on the 25th and seven
# concurrent workers already cost one killed task.
#
#   1. bankev       -- 4 of 7 shards left, 5.5 min each, 3 workers. Item 5
#                      needs it and item 5 is now TRIGGERED: c_all_pairs
#                      K=50 share=0.25 voting clears B1, B2, B3 and B4 in
#                      BOTH rotations once chain 1's floors are read in.
#   2. the reports  -- PAIR_FIT.md, BOOKS.md, WINNERS.md with B1 filled.
#   3. nnfxfinal    -- item 5, the 2005-2015 admission book, then B5.
#   4. booknull2b   -- the matched null for families d and e, ~6 h. Last
#                      because it is the longest and nothing else waits on it.
#
# STOP WITH: bash code/chain/stop_chain.sh $(cat results/chainlogs/queue_1126.pgid)
set -u
cd /Users/jackcuster/fx-data
export FX_COST_TABLE=results/cost_table_h22.csv
LOG=results/chainlogs/queue_1126.log
ts(){ date "+[%H:%M:%S]"; }

echo "$(ts) START queue_1126" >> $LOG

# ---- 0. nothing starts while midcheck still holds the real bank in memory.
# It is the check that decides whether stage 4 may run at all: does the new
# 'mid' emit tier pick the SAME family d winner the full tier picked?
while pgrep -f scratchpad/midcheck.py >/dev/null 2>&1; do sleep 30; done
echo "$(ts) midcheck has exited" >> $LOG

# ---- 1. the eleven-year admission bank
NS=$(ls results/nnfx/bank/shardev_real_*.npz 2>/dev/null | wc -l | tr -d ' ')
if [ "$NS" -lt 7 ]; then
  echo "$(ts) bankev: $NS of 7 shards on disk, resuming" >> $LOG
  bash code/chain/bankev.sh >> $LOG 2>&1
  NS=$(ls results/nnfx/bank/shardev_real_*.npz 2>/dev/null | wc -l | tr -d ' ')
  echo "$(ts) bankev: $NS of 7 shards on disk now" >> $LOG
else
  echo "$(ts) bankev: all 7 shards already on disk" >> $LOG
fi

# ---- 2. the reports, with B1 filled from chain 1's 20 matched runs
echo "$(ts) reports START" >> $LOG
python3 code/nnfxrep.py --reports > results/chainlogs/rep_1126.log 2>&1 \
  && echo "$(ts) reports OK" >> $LOG \
  || echo "$(ts) reports FAILED -- see results/chainlogs/rep_1126.log" >> $LOG

# ---- 3. item 5
echo "$(ts) nnfxfinal START" >> $LOG
python3 code/nnfxfinal.py > results/chainlogs/final_1126.log 2>&1 \
  && echo "$(ts) nnfxfinal OK" >> $LOG \
  || echo "$(ts) nnfxfinal FAILED -- see results/chainlogs/final_1126.log" >> $LOG

# ---- 4. the long one, on its own, AND ONLY ON A GOOD MIDCHECK VERDICT.
# The sentinel is written by hand after reading midcheck's output, so a
# winner that moved cannot start six hours of compute while nobody is looking.
if [ ! -f results/chainlogs/midcheck.ok ]; then
  echo "$(ts) booknull2b NOT STARTED -- results/chainlogs/midcheck.ok is absent, so the mid tier is unverified" >> $LOG
  echo "$(ts) DONE queue_1126 (stage 4 withheld)" >> $LOG
  exit 0
fi
echo "$(ts) booknull2b START -- expect ~6 h" >> $LOG
bash code/chain/booknull2b.sh
echo "$(ts) DONE queue_1126" >> $LOG
