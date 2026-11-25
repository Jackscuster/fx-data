#!/bin/bash
# ITEM 6a follow-up: EXITS.md and the app, after exit6.sh has finished.
# A SEPARATE FILE because exit6.sh must not be edited while it runs.
cd "$(dirname "$0")/../.." || exit 1
export FX_COST_TABLE=results/cost_table_h22.csv
LOG=results/chainlogs/exit6b.log
say(){ echo "[$(date +%H:%M:%S)] $*" | tee -a $LOG; }
say "START exit6b"
python3 code/nnfxexit.py --stage md >>$LOG 2>&1 && say "OK EXITS.md" || { say "FAIL md"; exit 1; }
python3 code/r2app.py >>$LOG 2>&1 && say "OK app" || { say "FAIL app"; exit 1; }
python3 code/preflight.py >>$LOG 2>&1 && say "OK preflight" || say "PREFLIGHT NOT CLEAR -- read the log"
say "DONE exit6b"
