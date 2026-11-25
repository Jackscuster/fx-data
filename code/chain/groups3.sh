#!/bin/bash
# ITEM 3b/3c/3d, Jack 25 Nov: the three declared groupings and their stability,
# the assignment test with a 1,000-draw label-shuffle null, and the daily P&L
# correlations between strategies and between groups.
cd "$(dirname "$0")/../.." || exit 1
export FX_COST_TABLE=results/cost_table_h22.csv
LOG=results/chainlogs/groups3.log
say(){ echo "[$(date +%H:%M:%S)] $*" | tee -a $LOG; }
say "START groups3"
say "START 3b groupings + stability"
python3 code/nnfxgroups.py --stage groups >>$LOG 2>&1 && say "OK groups" || { say "FAIL groups"; exit 1; }
say "START 3c assignment, 1000-draw label shuffle"
python3 code/nnfxgroups.py --stage assign --nshuf 1000 >>$LOG 2>&1 && say "OK assign" || { say "FAIL assign"; exit 1; }
say "START 3d daily P&L correlations"
python3 code/nnfxgroups.py --stage corr >>$LOG 2>&1 && say "OK corr" || { say "FAIL corr"; exit 1; }
say "DONE groups3"
