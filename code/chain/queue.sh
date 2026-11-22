#!/bin/bash
# RUN CHAINS BACK TO BACK IN ONE PROCESS (Jack, 21 Nov: "nothing idles").
#
#   nohup bash code/chain/queue.sh code/chain/a.sh code/chain/b.sh ... &
#
# WHY THIS REPLACES CHAINING arm_next INSTANCES. A detached poller per handoff
# failed twice in one evening. At 13:59 one gave up on a 20 h timeout while
# the chain ahead still had 80 minutes to run. At 21:20 another printed
# "marker seen", "marker landed as the chain exited" and "the chain ahead DIED
# without its marker" in the SAME SECOND and launched nothing -- three
# mutually exclusive branches, so more than one process was writing to that
# log and the pid check belonged to a chain that was not the one it was
# waiting for. Between them the machine sat idle for just over two hours.
#
# One process, one queue, no inter-process handoff: this launches a chain,
# waits for ITS pid to exit, checks ITS marker, and only then starts the next.
# There is no window in which nobody owns the handoff.
#
# A REFUSED LAUNCH IS NOT A DEAD QUEUE. launch.sh refuses on a dirty tree or
# on disk; that is the guard working. The queue records it, pushes, and moves
# to the next driver rather than stopping -- a later driver may need less
# space than the one that was refused.
set -uo pipefail
L="$HOME/fx-data-logs"
R="/Users/jackcuster/fx-data"
LOG="$L/queue.log"
say(){ echo "$(date '+%F %T') queue: $*" | tee -a "$LOG"; }
push(){
  [ -f "$L/ntfy_topic" ] || return 0
  printf '%s' "$2" | curl -s -o /dev/null --max-time 20 \
    -H "Title: $1" -H "Priority: high" -H "Tags: gear" \
    -d @- "https://ntfy.sh/$(tr -d '[:space:]' < "$L/ntfy_topic")" || true
}
trap 'say "QUEUE EXITING rc=$? (line ${BASH_LINENO[0]:-?})"' EXIT

cd "$R"
say "queue of $#: $*"
for D in "$@"; do
  B=$(basename "$D")
  MARK=$(grep -oE 'say "[^"]*COMPLETE"' "$D" | tail -1 | sed 's/^say "//; s/"$//')
  BEFORE=$(grep -cF "$MARK" "$L/batch1.log" 2>/dev/null | head -1); BEFORE=${BEFORE:-0}
  FREE=$(df -g /System/Volumes/Data | tail -1 | awk '{print $4}')
  say "--- $B  (marker \"$MARK\", seen $BEFORE times, $FREE GB free)"
  if [ -n "$(git status --porcelain 2>/dev/null | head -1)" ]; then
    say "$B SKIPPED: the working tree is dirty, launch.sh guard 1a would refuse"
    push "fx-data: $B not launched, dirty tree" "The queue skipped $B because the tree has uncommitted changes."
    continue
  fi
  OUT=$(bash code/chain/launch.sh "$D" 2>&1); RC=$?
  echo "$OUT" >> "$LOG"
  if [ "$RC" != 0 ]; then
    say "$B REFUSED by launch.sh (rc=$RC) -- moving to the next driver"
    push "fx-data: $B refused" "$(echo "$OUT" | grep -iE 'refused|only .* free' | head -3)"
    continue
  fi
  PID=$(grep -oE 'pid [0-9]+' <<<"$OUT" | head -1 | awk '{print $2}')
  say "$B launched, pid ${PID:-?}"
  nohup caffeinate -dimsu -w "$PID" >/dev/null 2>&1 &
  while kill -0 "$PID" 2>/dev/null; do sleep 60; done
  sleep 15
  AFTER=$(grep -cF "$MARK" "$L/batch1.log" 2>/dev/null | head -1); AFTER=${AFTER:-0}
  FREE=$(df -g /System/Volumes/Data | tail -1 | awk '{print $4}')
  if [ "$AFTER" -gt "$BEFORE" ]; then
    say "$B COMPLETE ($FREE GB free)"
  else
    say "$B EXITED WITHOUT ITS MARKER ($FREE GB free) -- continuing to the next driver anyway"
    push "fx-data: $B ended without its marker" "$B's pid exited but \"$MARK\" never appeared. The queue is continuing."
  fi
done
say "QUEUE DONE"
