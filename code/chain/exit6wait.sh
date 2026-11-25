#!/bin/bash
# Waits for the exit6 sweep to finish, then runs exit6b (EXITS.md, app,
# pre-flight). A separate waiter so neither exit6.sh nor exit6b.sh is ever
# edited while it runs.
cd "$(dirname "$0")/../.." || exit 1
LOG=results/chainlogs/exit6wait.log
say(){ echo "[$(date +%H:%M:%S)] $*" | tee -a $LOG; }
say "START exit6wait -- waiting on the sweep"
for i in $(seq 1 240); do
  pgrep -f "nnfxexit.py --stage sweep" >/dev/null || break
  sleep 30
done
# COMPLETION IS VERIFIED FROM THE DATA, NOT FROM THE LOG. exit6.sh was edited
# while live at 11:45, so its own final log lines cannot be trusted; the row
# count can.
N=$(python3 -c "import pandas as pd;print(len(pd.read_csv('results/nnfx/exit_grid.csv')))" 2>/dev/null || echo 0)
say "sweep process gone; exit_grid.csv holds $N of 576 cells"
if [ "$N" -lt 576 ]; then
  say "INCOMPLETE -- rerunning exit6.sh, which resumes per cell"
  code/chain/exit6.sh
  N=$(python3 -c "import pandas as pd;print(len(pd.read_csv('results/nnfx/exit_grid.csv')))" 2>/dev/null || echo 0)
  say "after resume: $N of 576"
fi
code/chain/exit6b.sh
say "DONE exit6wait"
