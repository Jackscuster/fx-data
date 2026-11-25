#!/bin/bash
# SOURCE 2 -- ten hand-built algorithms through PROTOCOL.md. Do NOT edit while running.
cd /Users/jackcuster/fx-data
export FX_COST_TABLE=results/cost_table_h22.csv
LOG=results/chainlogs/src2.log
ts(){ date "+[%H:%M:%S]"; }
echo "$(ts) START src2" >> $LOG
python3 code/nnfxsrc2.py --nulls 200 >> $LOG 2>&1 && echo "$(ts) OK src2" >> $LOG || echo "$(ts) FAIL src2" >> $LOG
echo "$(ts) DONE src2" >> $LOG
