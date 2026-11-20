#!/bin/bash
# ARM ONE CHAIN BEHIND ANOTHER (Jack, 20 Nov: "Launch without waiting").
#
#   nohup bash code/chain/arm_next.sh "<marker of the running chain>" <next driver> &
#
# WHY THIS EXISTS. Two chains cannot run at once: launch.sh writes
# ~/fx-data-logs/chain_current unconditionally and chainwatch.sh sources that
# single file, so a second launch orphans the first chain from its own
# watchdog. Queueing is therefore the only way to run B after A, and a person
# sitting and watching for A to finish is exactly the silent wait Jack banned
# on 20 Nov.
#
# WHAT IT WAITS FOR. The marker line appearing in batch1.log AFTER this script
# started -- not anywhere in the file, because every previous run of that chain
# left its own marker behind and matching one of those would launch instantly.
# It also gives up if the running chain's pid disappears without a marker,
# which is a death rather than a completion, and pushes instead of launching.
#
# WHAT IT REFUSES TO DO. Launch on a dirty tree. launch.sh would refuse anyway
# (guard 1a), but failing here with a push to Jack's phone is more useful than
# failing silently in a detached process at three in the morning.
set -uo pipefail
L="$HOME/fx-data-logs"
R="/Users/jackcuster/fx-data"
MARKER="${1:?arm_next: pass the marker of the chain to wait for}"
DRIVER="${2:?arm_next: pass the next driver}"
APPROVED="${3:-}"
POLL=60
MAXWAIT="${MAXWAIT:-72000}"          # 20 h, then give up and say so
LOG="$L/arm_next.log"

say(){ echo "$(date '+%F %T') arm_next: $*" | tee -a "$LOG"; }

push(){
  [ -f "$L/ntfy_topic" ] || return 0
  printf '%s' "$2" | curl -s -o /dev/null -w '' --max-time 20 \
    -H "Title: $1" -H "Priority: high" -H "Tags: link" \
    -d @- "https://ntfy.sh/$(tr -d '[:space:]' < "$L/ntfy_topic")"
}

[ -f "$R/$DRIVER" ] || [ -f "$DRIVER" ] || { say "no such driver $DRIVER"; exit 2; }
count_marker(){ local c; c=$(grep -cF "$MARKER" "$L/batch1.log" 2>/dev/null | head -1); echo "${c:-0}"; }
PREV=$(count_marker)
WATCH_PID=$(grep CHAIN_PID "$L/chain_current" 2>/dev/null | cut -d= -f2)
say "waiting for \"$MARKER\" (seen $PREV times already; only a NEW one counts), then launching $DRIVER"
say "watching chain pid ${WATCH_PID:-unknown}"

T0=$(date +%s)
while :; do
  NOW=$(count_marker)
  if [ "$NOW" -gt "$PREV" ]; then
    say "marker seen; the chain ahead has finished"
    break
  fi
  if [ -n "$WATCH_PID" ] && ! kill -0 "$WATCH_PID" 2>/dev/null; then
    sleep 20                                  # let a final marker land
    NOW=$(count_marker)
    if [ "$NOW" -gt "$PREV" ]; then say "marker landed as the chain exited"; break; fi
    say "the chain ahead DIED without its marker -- not launching $DRIVER"
    push "fx-data: chain died, next chain NOT launched" \
      "The chain ahead of $DRIVER exited without \"$MARKER\". $DRIVER was not launched, because launching on top of a failure would bury it. Check the ledger."
    exit 1
  fi
  if [ $(( $(date +%s) - T0 )) -ge "$MAXWAIT" ]; then
    say "gave up after $(( MAXWAIT / 3600 )) h"
    push "fx-data: arm_next gave up" "Waited $(( MAXWAIT / 3600 )) h for \"$MARKER\" and it never came. $DRIVER was not launched."
    exit 1
  fi
  sleep "$POLL"
done

cd "$R"
DIRTY=$(git status --porcelain | head -3)
if [ -n "$DIRTY" ]; then
  say "REFUSING: the tree is dirty, so the snapshot would not match a commit"
  push "fx-data: next chain NOT launched, dirty tree" \
    "$DRIVER was ready but the working tree has uncommitted changes, so launch.sh guard 1a would refuse. Commit or stash, then launch it."
  exit 4
fi
say "free space $(df -g /System/Volumes/Data | tail -1 | awk '{print $4}') GB"
if [ -n "$APPROVED" ]; then
  say "launching $DRIVER --approved $APPROVED"
  bash code/chain/launch.sh "$DRIVER" --approved "$APPROVED" >> "$LOG" 2>&1
else
  say "launching $DRIVER (its own \"approval = none\" declaration carries guard 6)"
  bash code/chain/launch.sh "$DRIVER" >> "$LOG" 2>&1
fi
RC=$?
say "launch.sh exited $RC"
if [ "$RC" != 0 ]; then
  push "fx-data: next chain FAILED to launch" "$DRIVER did not launch; launch.sh exited $RC. See $LOG."
fi
exit "$RC"
