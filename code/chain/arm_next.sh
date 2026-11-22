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
MAXWAIT="${MAXWAIT:-259200}"         # 72 h, then give up and say so
# 20 h WAS NOT ENOUGH AND IT COST A LAUNCH. On 21 Nov this gave up at 13:59
# while the chain ahead still had 80 minutes to run, because the 20 h default
# was set from an estimate of chain 18 that proved 2x short. A queue-arming
# timeout should be long enough to be wrong about the chain ahead; the thing it
# protects against is a chain that died silently, and the pid check already
# catches that in seconds.
LOG="$L/arm_next.log"

say(){ echo "$(date '+%F %T') arm_next: $*" | tee -a "$LOG"; }

# AN EXIT MUST LEAVE A LINE. On 21 Nov this process logged "marker seen" at
# 18:53:38 and then vanished -- no refusal, no launch, no error -- and the
# machine sat idle for an hour with a clean tree and a chain that would have
# passed its guard. Whatever killed it, the absence of any line made it
# undiagnosable. This trap guarantees the last thing in the log is why.
on_exit(){
  local rc=$?
  if [ "$rc" != 0 ] || [ "${ARM_LAUNCHED:-0}" != 1 ]; then
    echo "$(date '+%F %T') arm_next: EXITING rc=$rc at line ${BASH_LINENO[0]:-?} (launched=${ARM_LAUNCHED:-0})" >> "$LOG"
  fi
}
trap on_exit EXIT
trap 'echo "$(date '"'"'+%F %T'"'"') arm_next: KILLED by a signal" >> "$LOG"; exit 143' TERM HUP INT

push(){
  [ -f "$L/ntfy_topic" ] || return 0
  printf '%s' "$2" | curl -s -o /dev/null -w '' --max-time 20 \
    -H "Title: $1" -H "Priority: high" -H "Tags: link" \
    -d @- "https://ntfy.sh/$(tr -d '[:space:]' < "$L/ntfy_topic")"
}

[ -f "$R/$DRIVER" ] || [ -f "$DRIVER" ] || { say "no such driver $DRIVER"; exit 2; }
count_marker(){ local c; c=$(grep -cF "$MARKER" "$L/batch1.log" 2>/dev/null | head -1); echo "${c:-0}"; }
PREV=$(count_marker)
# CHAINING TWO DEEP NEEDS THE PID CHECK OFF. An arm_next started now to wait
# for chain 20's marker would read chain 18's pid out of chain_current, see it
# exit when chain 18 finishes, find no chain-20 marker, and refuse to launch --
# concluding "the chain ahead died" about a chain that had not started yet.
# FX_ARM_NOPID=1 waits on the marker alone, which is the right test when the
# chain ahead does not exist yet.
if [ "${FX_ARM_NOPID:-0}" = "1" ]; then
  WATCH_PID=""
else
  WATCH_PID=$(grep CHAIN_PID "$L/chain_current" 2>/dev/null | cut -d= -f2)
fi
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
DIRTY=$(git status --porcelain 2>/dev/null | head -3 || true)
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
ARM_LAUNCHED=1
say "launch.sh exited $RC"
if [ "$RC" != 0 ]; then
  push "fx-data: next chain FAILED to launch" "$DRIVER did not launch; launch.sh exited $RC. See $LOG."
fi
exit "$RC"
