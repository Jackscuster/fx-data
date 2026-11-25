#!/bin/bash
# ITEM 2c + 2d, Jack 25 Nov: the quiet-entry rule as a RULE -- the fixed-Q
# curve for its shape, Q chosen walk-forward on each step's tuning years, the
# paired test against the same candidate without it, and the cross with the
# per-pair floor at off / 1% / 5%.
cd "$(dirname "$0")/../.." || exit 1
export FX_COST_TABLE=results/cost_table_h22.csv
LOG=results/chainlogs/quiet2c.log
say(){ echo "[$(date +%H:%M:%S)] $*" | tee -a $LOG; }
say "START quiet2c"
say "START 2c fixed-Q curve, 10% to 100%"
python3 code/nnfxquiet.py --stage fixedq >>$LOG 2>&1 && say "OK fixedq" || { say "FAIL fixedq"; exit 1; }
say "START 2c walk-forward Q + paired test"
python3 code/nnfxquiet.py --stage walkq >>$LOG 2>&1 && say "OK walkq+paired" || { say "FAIL walkq"; exit 1; }
say "START 2d floor cross"
python3 code/nnfxquiet.py --stage floorcross >>$LOG 2>&1 && say "OK floorcross" || { say "FAIL floorcross"; exit 1; }
say "DONE quiet2c"
