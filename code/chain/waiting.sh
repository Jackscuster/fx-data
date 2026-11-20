#!/bin/bash
# "WAITING ON JACK" -- NO MORE SILENT WAITS (Jack, 20 Nov).
#
#   bash code/chain/waiting.sh set "<what I am waiting for>"
#   bash code/chain/waiting.sh clear
#   bash code/chain/waiting.sh status
#
# WHY. On 19 Nov a built, committed, guard-passing chain sat unlaunched for
# fourteen hours because the question "shall I launch?" was asked in a chat
# window Jack was not reading. The machine was idle the whole time. A wait that
# only exists in a transcript is indistinguishable from work in progress.
#
# `set` pushes to Jack's phone IMMEDIATELY and writes the flag file.
# chainwatch.sh re-pushes every 2 hours while the flag exists -- it runs every
# 300 s under launchd and the re-push check sits BEFORE its "no chain
# registered, exit" line, because having no chain running is exactly the state
# in which a wait is most likely and least visible.
# `clear` removes the flag. Call it the moment Jack answers, or the pushes keep
# coming and the alert stops meaning anything.
set -uo pipefail
L="$HOME/fx-data-logs"
FLAG="$L/waiting_on_jack"
STAMP="$L/.waiting_last_push"
TOPIC_FILE="$L/ntfy_topic"
REPEAT_SECONDS=7200

push_waiting(){   # push_waiting <text> <age_minutes>
  local topic code body
  [ -f "$TOPIC_FILE" ] || { echo "$(date '+%F %T') waiting: no ntfy topic file" >> "$L/watchdog.log"; return 1; }
  topic=$(tr -d '[:space:]' < "$TOPIC_FILE")
  if [ "${2:-0}" -gt 0 ]; then
    body="$1

Waiting $2 min so far. Nothing is running on this. Reply in the session to unblock it."
  else
    body="$1

Nothing is running on this. Reply in the session to unblock it."
  fi
  code=$(printf '%s' "$body" | curl -s -o /dev/null -w '%{http_code}' --max-time 20 \
    -H "Title: WAITING ON JACK: $1" -H "Priority: high" -H "Tags: raised_hand" \
    -d @- "https://ntfy.sh/$topic")
  echo "$(date '+%F %T') waiting: push \"$1\" -> ntfy HTTP $code" >> "$L/watchdog.log"
  date +%s > "$STAMP"
  [ "$code" = "200" ]
}

case "${1:-status}" in
  set)
    WHAT="${2:?waiting set: say what you are waiting for}"
    printf '%s\n%s\n' "$(date +%s)" "$WHAT" > "$FLAG"
    push_waiting "$WHAT" 0
    echo "waiting: flagged \"$WHAT\"; pushed now, repeats every $((REPEAT_SECONDS/3600)) h until cleared"
    ;;
  clear)
    if [ -f "$FLAG" ]; then
      WHAT=$(sed -n 2p "$FLAG")
      T0=$(sed -n 1p "$FLAG")
      echo "$(date '+%F %T') waiting: CLEARED after $(( ($(date +%s) - T0) / 60 )) min -- \"$WHAT\"" >> "$L/watchdog.log"
      rm -f "$FLAG" "$STAMP"
      echo "waiting: cleared \"$WHAT\""
    else
      echo "waiting: nothing was flagged"
    fi
    ;;
  repush)
    # called by chainwatch.sh every 300 s; pushes only once per REPEAT_SECONDS
    [ -f "$FLAG" ] || exit 0
    T0=$(sed -n 1p "$FLAG"); WHAT=$(sed -n 2p "$FLAG")
    LAST=$(cat "$STAMP" 2>/dev/null || echo 0)
    NOW=$(date +%s)
    if [ $(( NOW - LAST )) -ge "$REPEAT_SECONDS" ]; then
      push_waiting "$WHAT" $(( (NOW - T0) / 60 ))
    fi
    ;;
  status)
    if [ -f "$FLAG" ]; then
      T0=$(sed -n 1p "$FLAG"); WHAT=$(sed -n 2p "$FLAG")
      echo "WAITING ON JACK for $(( ($(date +%s) - T0) / 60 )) min: $WHAT"
    else
      echo "not waiting on anything"
    fi
    ;;
  *) echo "usage: waiting.sh set \"<what>\" | clear | status | repush"; exit 2;;
esac
