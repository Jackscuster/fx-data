#!/bin/bash
# STAGE 4 PREVIEW — the volume slot, on A/B/C without any C2. Two candidates.
set -u
cd /Users/jackcuster/fx-data
export FX_COST_TABLE=$PWD/results/cost_table_h22.csv
L=$HOME/fx-data-logs/s4.log
: > $L
say(){ echo "[$(date '+%H:%M:%S')] $*" | tee -a $L; }
say "START stage4"
if nice -n 12 python3 -W error::FutureWarning code/nnfx3.py --stage stage4 >>$L 2>&1; then
  say "OK s4 preview"
else
  say "FAIL s4 preview"; echo "FAIL s4" >> $HOME/fx-data-logs/s4.fail
fi
say "DONE stage4"
