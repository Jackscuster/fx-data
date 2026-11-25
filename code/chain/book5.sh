#!/bin/bash
# ITEM 5, Jack 25 Nov: THE BOOK. Equal risk per sleeve, the declared addition
# order from the brief, the marginal contribution of every sleeve to the A+B
# book, and every prefix through the prop simulator at the Team 1 budget.
cd "$(dirname "$0")/../.." || exit 1
export FX_COST_TABLE=results/cost_table_h22.csv
LOG=results/chainlogs/book5.log
say(){ echo "[$(date +%H:%M:%S)] $*" | tee -a $LOG; }
say "START book5"
python3 code/nnfxbook.py >>$LOG 2>&1 && say "OK book5" || { say "FAIL book5"; exit 1; }
say "DONE book5"
