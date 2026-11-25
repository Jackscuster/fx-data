#!/bin/bash
# ITEM 3a, Jack 25 Nov: the per-pair, per-direction, per-unseen-year bank over
# all 39 C1 alone, the 3 picked baselines both ways, and candidates A and B.
cd "$(dirname "$0")/../.." || exit 1
export FX_COST_TABLE=results/cost_table_h22.csv
LOG=results/chainlogs/bank3a.log
say(){ echo "[$(date +%H:%M:%S)] $*" | tee -a $LOG; }
say "START bank3a"
python3 code/nnfxbank.py >>$LOG 2>&1 && say "OK bank3a" || { say "FAIL bank3a"; exit 1; }
say "DONE bank3a"
