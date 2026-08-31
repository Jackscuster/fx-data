#!/bin/bash
# SWAP GUARD for a two-pool tuning run. Committed rather than left in /tmp,
# because the two ad-hoc guards before it both had an EXIT CONDITION -- each
# stopped watching once the thing it was waiting for happened, and the main pool
# was then unprotected without anything saying so. This one runs until the pool
# it protects is gone, and never exits early.
#
#   l2swapguard.sh <MAIN_PID> <ADD_PID> [WARN_MB] [CRIT_MB]
#
# SACRIFICE ORDER, fixed: the ADDITIVE (--reverse) pool dies first. It holds no
# unique state -- chunks it has written stay written, and plan_chunks skips them
# -- so dropping it costs only work in flight. The MAIN pool is NEVER killed by
# this script: its chunks are hours deep and losing one costs more than the swap
# pressure does. Below CRIT with the additive pool already gone, it logs loudly
# and keeps watching; deciding to kill hours of work is a human's call.
MAIN=$1; ADD=$2; WARN=${3:-400}; CRIT=${4:-200}
LOG=/Users/jackcuster/Documents/fx-data/results/swapguard.log
say(){ echo "$(date '+%F %T') $*" >> "$LOG"; }
say "armed: main=$MAIN add=$ADD warn=${WARN}M crit=${CRIT}M"
killed=0
while ps -p "$MAIN" >/dev/null 2>&1; do
  free=$(sysctl -n vm.swapusage | sed 's/.*free = \([0-9.]*\)M.*/\1/'); free=${free%%.*}
  if [ "$killed" -eq 0 ] && [ -n "$ADD" ] && ps -p "$ADD" >/dev/null 2>&1 \
     && [ "$free" -lt "$WARN" ] 2>/dev/null; then
    say "swap free ${free}M < ${WARN}M -- stopping ADDITIVE pool $ADD (main $MAIN untouched)"
    pkill -TERM -P "$ADD" 2>/dev/null; kill "$ADD" 2>/dev/null; killed=1
  fi
  if [ "$free" -lt "$CRIT" ] 2>/dev/null; then
    say "CRITICAL: swap free ${free}M with the additive pool already gone. Main pool "
    say "  $MAIN left running deliberately -- killing it would discard chunks hours deep."
  fi
  sleep 60
done
say "main pool $MAIN gone; guard standing down"
