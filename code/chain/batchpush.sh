#!/bin/bash
# PUSH LOCAL HISTORY TO ORIGIN A FEW COMMITS AT A TIME.
#
# WHY NOT ONE PUSH. The pack is 7 GiB. A single push of a long backlog has
# twice been killed by a timeout partway through, and GitHub rejects the retry
# until it finishes garbage collecting. Pushing <refspec>~n in steps keeps each
# transfer small enough to land and makes a failure cost one step, not all of
# them.
#
# SAFE ALONGSIDE A RUNNING CHAIN only while chains are in FX_CI_LOCAL=1, which
# makes `ci` commit without pulling or pushing. Check that before running this.
set -uo pipefail
cd /Users/jackcuster/fx-data
LOG="$HOME/fx-data-logs/push.log"
STEP="${1:-5}"
say(){ echo "$(date '+%F %T') $*" | tee -a "$LOG"; }
H=$(git rev-parse HEAD)
R=$(git ls-remote origin refs/heads/main 2>/dev/null | cut -f1)
[ -n "$R" ] || { say "batched push: cannot read the remote"; exit 1; }
N=$(git rev-list --count "$R..$H" 2>/dev/null || echo 0)
say "batched push: remote $(echo $R | cut -c1-8), $N commits behind, step $STEP"
while [ "$N" -gt 0 ]; do
  if [ "$N" -le "$STEP" ]; then T=$H; else T=$(git rev-parse "$H~$((N-STEP))"); fi
  if git push origin "+$T:refs/heads/main" >>"$LOG" 2>&1; then
    say "pushed to $(git rev-parse --short $T)"
  else
    say "batched push: step to $(git rev-parse --short $T) FAILED -- stopping, nothing is lost"
    exit 1
  fi
  R=$(git ls-remote origin refs/heads/main 2>/dev/null | cut -f1)
  N=$(git rev-list --count "$R..$H" 2>/dev/null || echo 0)
  say "behind by $N"
done
say "batched push done, remote $(git rev-parse --short HEAD)"
