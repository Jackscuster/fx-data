#!/bin/bash
# The eleven-year admission bank for item 5 (PROTOCOL.md A7). Three workers
# only: chain 1 is using seven and this is not on the critical path.
# DO NOT EDIT WHILE RUNNING.
set -u
cd /Users/jackcuster/fx-data
export FX_COST_TABLE=results/cost_table_h22.csv
L=results/chainlogs/bankev.log
ts(){ date "+[%H:%M:%S]"; }
echo "$(ts) START bankev" >> $L
seq 0 6 | xargs -P 3 -I{} sh -c \
  'FX_COST_TABLE=results/cost_table_h22.csv python3 code/nnfxbankev.py --shard {} --nshards 7 > results/chainlogs/bankev_{}.log 2>&1'
python3 code/nnfxbankev.py --merge --nshards 7 >> $L 2>&1 \
  && echo "$(ts) OK bankev" >> $L || echo "$(ts) FAIL bankev merge" >> $L
echo "$(ts) DONE bankev" >> $L
