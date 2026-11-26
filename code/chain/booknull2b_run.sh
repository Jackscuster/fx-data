#!/bin/bash
# ONE NULL-2 RUN. Called as: sh code/chain/booknull2b_run.sh <run>
#
# WHY THIS IS ITS OWN FILE AND NOT AN INLINE `xargs -I{} sh -c '...'`.
# BSD xargs (macOS) refuses a -I replacement command longer than 255 bytes:
# "xargs: command line cannot be assembled, too long". It does not run a
# single item and does not fail the pipeline -- booknull2b.sh reported
# "DONE ... 0 of 20" one second after starting and exited 0. The previous
# chain's inline body was one line and fitted; the fail-fast body did not.
# Keeping the body in a file keeps the xargs command line short for ever.
set -u
cd /Users/jackcuster/fx-data
K="$1"
LOG=results/chainlogs/booknull2b.log
ABORT=results/chainlogs/booknull2b.abort
RLOG="results/chainlogs/booknull2b_${K}.log"

if [ -f "$ABORT" ]; then
  echo "$(date +%H:%M:%S) SKIP run $K -- the chain has aborted" >> $LOG
  exit 0
fi

export FX_COST_TABLE=results/cost_table_h22.csv
if python3 code/nnfxnullrun2.py --run "$K" > "$RLOG" 2>&1; then
  echo "$(date +%H:%M:%S) OK run $K" >> $LOG
else
  touch "$ABORT"
  {
    echo "$(date +%H:%M:%S) FAIL run $K -- ABORTING THE CHAIN"
    echo "---- last 15 lines of $RLOG ----"
    tail -15 "$RLOG"
    echo "---- end ----"
  } >> $LOG
  exit 1
fi
