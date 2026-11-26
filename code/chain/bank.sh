#!/bin/bash
# DO NOT EDIT WHILE RUNNING -- bash reads a script incrementally as it executes.
# ITEM 1's searched bank: 384,334 algorithms x 28 pairs, 7 shards of 4 pairs.
set -u
cd /Users/jackcuster/fx-data
L=results/chainlogs
echo "[$(date +%H:%M:%S)] START bank"
seq 0 6 | xargs -P 7 -I{} sh -c \
  'python3 code/nnfxsleeves.py --shard {} --nshards 7 > results/chainlogs/bank_shard_{}.log 2>&1'
echo "[$(date +%H:%M:%S)] shards done"
python3 code/nnfxsleeves.py --merge --nshards 7 >> $L/bank.log 2>&1 && echo "[$(date +%H:%M:%S)] OK merge" || echo "[$(date +%H:%M:%S)] FAIL merge"
echo "[$(date +%H:%M:%S)] DONE bank"
