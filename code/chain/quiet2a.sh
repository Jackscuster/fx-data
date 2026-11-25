#!/bin/bash
# ITEM 2a + 2b, Jack 25 Nov: the decile table over all 39 C1 alone plus A and
# B, then the decile-matched random-entry null.
cd "$(dirname "$0")/../.." || exit 1
export FX_COST_TABLE=results/cost_table_h22.csv
LOG=results/chainlogs/quiet2a.log
say(){ echo "[$(date +%H:%M:%S)] $*" | tee -a $LOG; }
say "START quiet2a"
say "START blocked share"
python3 code/nnfxquiet.py --stage share >>$LOG 2>&1 && say "OK blocked share" || { say "FAIL share"; exit 1; }
say "START 2a deciles, 39 C1 alone + A + B"
python3 code/nnfxquiet.py --stage deciles >>$LOG 2>&1 && say "OK 2a deciles" || { say "FAIL deciles"; exit 1; }
say "START 2b decile-matched null, 200 draws"
python3 code/nnfxquiet.py --stage null --ndraw 200 >>$LOG 2>&1 && say "OK 2b null" || { say "FAIL null"; exit 1; }
say "DONE quiet2a"
