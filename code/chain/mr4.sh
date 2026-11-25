#!/bin/bash
# ITEM 4, Jack 25 Nov: declared mean reversion, 3 variants, no search,
# conditional on an OU half-life AND a Dickey-Fuller stationarity test, with
# and without Layer 1's RANGING gate, on all 28 pairs and the range-prone
# group, plus the daily correlation to candidate A.
cd "$(dirname "$0")/../.." || exit 1
export FX_COST_TABLE=results/cost_table_h22.csv
LOG=results/chainlogs/mr4.log
say(){ echo "[$(date +%H:%M:%S)] $*" | tee -a $LOG; }
say "START mr4"
say "START condition report"
python3 code/nnfxmr.py --stage cond >>$LOG 2>&1 && say "OK cond" || { say "FAIL cond"; exit 1; }
say "START run: 3 variants x conditional x ranging gate"
python3 code/nnfxmr.py --stage run >>$LOG 2>&1 && say "OK run" || { say "FAIL run"; exit 1; }
say "DONE mr4"
