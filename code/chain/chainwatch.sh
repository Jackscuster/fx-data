#!/bin/bash
# CHAIN WATCHDOG (Jack, 17 Nov). Runs every 5 minutes under launchd.
#
# WHY IT EXISTS. On the night of 16-17 Nov a chain halted and nothing ran for
# 10.5 hours, because the only thing that noticed was Jack sending a message.
# A halt must announce itself, on Jack's phone.
#
# TWO CONDITIONS, either one pushes:
#   HALTED  the chain pid is gone and its FINAL MARKER is not in the log
#   STALLED a chain is registered but nothing has progressed for 10 minutes --
#           no worker process at all, or the workers' cumulative CPU and the
#           log have both stood still. A stuck chain is as expensive as a dead
#           one and used to look identical to a healthy one from outside.
#
# WHAT IT DOES. Writes ~/fx-data-logs/CHAIN_HALTED, posts a macOS notification,
# and POSTs a push to https://ntfy.sh/<topic> (the topic is in
# ~/fx-data-logs/ntfy_topic). Email is gone: Jack's call, 17 Nov -- postfix is
# down on this machine and Mail.app is blocked by TCC, so it was never more
# than a file on disk pretending to be a message.
#
# It notifies ONCE per halt and once per stall episode (stamp files), so a dead
# chain does not push every five minutes for a week.
set -u
L="$HOME/fx-data-logs"
STATE="$L/chain_current"
HALT="$L/CHAIN_HALTED"
SNAP="$L/.chain_progress"
TOPIC_FILE="$L/ntfy_topic"
STALL_SECONDS=600

push(){   # push <title> <priority> <tags> <body>
  local topic title prio tags body code
  [ -f "$TOPIC_FILE" ] || { echo "$(date '+%F %T') watchdog: no ntfy topic file" >> "$L/watchdog.log"; return 1; }
  topic=$(tr -d '[:space:]' < "$TOPIC_FILE")
  title="$1"; prio="$2"; tags="$3"; body="$4"
  code=$(printf '%s' "$body" | curl -s -o /dev/null -w '%{http_code}' --max-time 20 \
    -H "Title: $title" -H "Priority: $prio" -H "Tags: $tags" \
    -d @- "https://ntfy.sh/$topic")
  echo "$(date '+%F %T') watchdog: push \"$title\" -> ntfy HTTP $code" >> "$L/watchdog.log"
  [ "$code" = "200" ]
}

# "WAITING ON JACK" RE-PUSH, BEFORE THE NO-CHAIN EXIT. A wait is most likely
# and least visible exactly when no chain is registered -- on 19 Nov a built,
# guard-passing chain sat unlaunched for fourteen hours. waiting.sh itself
# decides whether 2 hours have passed, so this is cheap on every 300 s tick.
bash /Users/jackcuster/fx-data/code/chain/waiting.sh repush 2>/dev/null

[ -f "$STATE" ] || exit 0
# shellcheck disable=SC1090
. "$STATE"                       # CHAIN_PID CHAIN_DRIVER CHAIN_LOG CHAIN_MARKER CHAIN_START

FREEMB=$(df -m /System/Volumes/Data | tail -1 | awk '{print $4}')
if [ "${FREEMB:-99999}" -lt 2000 ]; then
  DSTAMP="$L/.disk_notified_$(( $(date +%s) / 3600 ))"
  if [ ! -f "$DSTAMP" ]; then
    : > "$DSTAMP" 2>/dev/null
    /usr/bin/curl -s --max-time 20 -H "Title: fx-data: DISK ALMOST FULL" -H "Priority: urgent" \
      -H "Tags: floppy_disk" -d "Only ${FREEMB} MB free on the data volume. A stage will fail with OSError 28 and the watchdog's own file writes fail too, so this push goes out BEFORE anything is written." \
      "https://ntfy.sh/$(tr -d '[:space:]' < "$TOPIC_FILE")" >/dev/null
  fi
fi

NOW=$(date +%s)
WHEN=$(date '+%F %T')
RAN=$(( (NOW - CHAIN_START) / 60 ))
TAIL10=$(tail -10 "$CHAIN_LOG" 2>/dev/null)
STAGE=$(grep -E "done in|FAILED|SKIP " "$CHAIN_LOG" 2>/dev/null | tail -1 | cut -c1-120)

report(){   # report <kind> <detail>
  {
    echo "CHAIN $1"
    echo "$WHEN"
    echo
    echo "driver       : $CHAIN_DRIVER"
    echo "pid          : $CHAIN_PID"
    echo "ran for      : $RAN min"
    echo "final marker : \"$CHAIN_MARKER\""
    echo "last stage   : $STAGE"
    echo "why          : $2"
    echo "log          : $CHAIN_LOG"
    echo
    echo "--- last 20 lines ---"
    tail -20 "$CHAIN_LOG" 2>/dev/null
  } > "$HALT"
}

# ---------------------------------------------------------------- HALTED
if ! kill -0 "$CHAIN_PID" 2>/dev/null; then
  if grep -qF "$CHAIN_MARKER" "$CHAIN_LOG" 2>/dev/null; then
    # FINISHED -- but did it produce what it was for? On the night of 17-18 Nov
    # nothing halted and nothing stalled: mode B tuning ran for nine hours while
    # the mode A deliverable sat unbuilt, and the watchdog had nothing to fire on
    # because it only ever watched LIVENESS. A chain now declares the file it is
    # supposed to produce, and a chain that finishes without it is reported.
    if [ -n "${CHAIN_DELIVERABLE:-}" ] && [ ! -f "$CHAIN_DELIVERABLE" ]; then
      STAMP="$L/.nodeliv_notified_${CHAIN_PID}"
      if [ ! -f "$STAMP" ]; then
        : > "$STAMP"
        report "FINISHED WITHOUT ITS DELIVERABLE" \
          "the final marker printed but $CHAIN_DELIVERABLE does not exist"
        /usr/bin/osascript -e "display notification \"$CHAIN_DRIVER finished but $(basename "$CHAIN_DELIVERABLE") was never written\" with title \"fx-data: NO DELIVERABLE\" subtitle \"$WHEN\" sound name \"Basso\"" 2>/dev/null
        push "fx-data: CHAIN FINISHED, NO DELIVERABLE" "urgent" "x" \
          "$CHAIN_DRIVER printed its final marker at $WHEN after $RAN min but never wrote $CHAIN_DELIVERABLE. Nothing is running.
--- last 10 log lines ---
$TAIL10"
      fi
      exit 0
    fi
    mv "$STATE" "$L/chain_last_completed" 2>/dev/null
    rm -f "$SNAP" "$L"/.stalled_notified_* 2>/dev/null
    exit 0
  fi
  STAMP="$L/.halted_notified_${CHAIN_PID}"
  [ -f "$STAMP" ] && exit 0
  : > "$STAMP"
  report "HALTED BEFORE ITS FINAL MARKER" "the pid is gone and the final marker is not in the log"
  /usr/bin/osascript -e "display notification \"$CHAIN_DRIVER died after $RAN min. See ~/fx-data-logs/CHAIN_HALTED\" with title \"fx-data: CHAIN HALTED\" subtitle \"$WHEN\" sound name \"Basso\"" 2>/dev/null
  push "fx-data CHAIN HALTED" "urgent" "rotating_light" \
    "$CHAIN_DRIVER halted at $WHEN after $RAN min. Last stage: $STAGE. Final marker \"$CHAIN_MARKER\" never printed. Nothing is running.
--- last 10 log lines ---
$TAIL10"
  exit 0
fi

# ---------------------------------------------------------------- ETA PASSED
# GUARD 4. A chain declares how long it should take. If the ETA passes and the
# deliverable is not there, that is reported WHILE the chain is still running --
# the failure mode of 17-18 Nov was a chain that looked perfectly healthy for
# nine hours while the thing it existed to produce did not exist.
if [ -n "${CHAIN_ETA_MIN:-}" ] && [ "${CHAIN_ETA_MIN:-0}" -gt 0 ] \
   && [ -n "${CHAIN_DELIVERABLE:-}" ] && [ ! -f "$CHAIN_DELIVERABLE" ] \
   && [ "$RAN" -gt "$CHAIN_ETA_MIN" ]; then
  ESTAMP="$L/.eta_notified_${CHAIN_PID}"
  if [ ! -f "$ESTAMP" ]; then
    push "fx-data: ETA PASSED, NO DELIVERABLE" "urgent" "hourglass" \
      "$CHAIN_DRIVER has run $RAN min against a declared ETA of $CHAIN_ETA_MIN min and $CHAIN_DELIVERABLE still does not exist. The chain is still alive.
--- last 10 log lines ---
$TAIL10"
    : > "$ESTAMP" 2>/dev/null
    report "ETA PASSED WITHOUT ITS DELIVERABLE" \
      "ran $RAN min against a declared $CHAIN_ETA_MIN min; $CHAIN_DELIVERABLE absent"
  fi
fi

# ---------------------------------------------------------------- STAGE FAILED
# A chain that loses a stage and carries on is INVISIBLE to a liveness watchdog:
# on 18 Nov `a8 books A` failed at 09:40, the dependency ledger correctly skipped
# the nulls and the report and ran the independent stages, the chain stayed alive
# and progressing -- and the failure sat unseen for an hour. Any new "!!! ...
# FAILED" line is now pushed as it appears.
FSNAP="$L/.chain_failcount"
nf=$(grep -c '!!!.*FAILED' "$CHAIN_LOG" 2>/dev/null | head -1); nf=${nf:-0}
pf0=0; [ -f "$FSNAP" ] && pf0=$(cat "$FSNAP" 2>/dev/null | head -1); pf0=${pf0:-0}
if [ "$nf" -gt "$pf0" ]; then
  echo "$nf" > "$FSNAP"
  NEWFAIL=$(grep '!!!.*FAILED' "$CHAIN_LOG" 2>/dev/null | tail -$(( nf - pf0 )) | cut -c1-200)
  push "fx-data: STAGE FAILED" "high" "warning" \
    "$CHAIN_DRIVER lost a stage at $WHEN (the chain is still running its independent stages):
$NEWFAIL
--- last 10 log lines ---
$TAIL10"
  report "STAGE FAILED, CHAIN CONTINUING" "$(echo "$NEWFAIL" | tr '\n' ';')"
  /usr/bin/osascript -e "display notification \"$(echo "$NEWFAIL" | tail -1 | cut -c1-120)\" with title \"fx-data: STAGE FAILED\" subtitle \"$WHEN\" sound name \"Basso\"" 2>/dev/null
fi
[ -f "$FSNAP" ] || echo "$nf" > "$FSNAP"

# ---------------------------------------------------------------- STALLED
# Cumulative CPU of every descendant, plus the log size. Both standing still
# for STALL_SECONDS means a registered chain is making no progress -- which
# from outside looks exactly like a healthy one, and is just as expensive.
KIDS=$(pgrep -P "$CHAIN_PID" 2>/dev/null | tr '\n' ' ')
ALL="$CHAIN_PID $KIDS"
for k in $KIDS; do ALL="$ALL $(pgrep -P "$k" 2>/dev/null | tr '\n' ' ')"; done
CPU=0
for p in $ALL; do
  [ -n "$p" ] || continue
  t=$(ps -o time= -p "$p" 2>/dev/null | tail -1 | tr -d ' ')
  [ -n "$t" ] || continue
  s=$(echo "$t" | awk -F: '{if(NF==3)print $1*3600+$2*60+$3; else if(NF==2)print $1*60+$2; else print $1}')
  CPU=$(( CPU + ${s%.*} ))
done
LOGSZ=$(wc -c < "$CHAIN_LOG" 2>/dev/null | tr -d ' '); LOGSZ=${LOGSZ:-0}
NWORK=$(echo "$ALL" | wc -w | tr -d ' ')

PREV_T=0; PREV_CPU=-1; PREV_SZ=-1
if [ -f "$SNAP" ]; then . "$SNAP"; fi
if [ "$PREV_CPU" = "$CPU" ] && [ "$PREV_SZ" = "$LOGSZ" ] && [ "$PREV_T" != "0" ]; then
  IDLE=$(( NOW - PREV_T ))
else
  IDLE=0
  printf 'PREV_T=%s\nPREV_CPU=%s\nPREV_SZ=%s\n' "$NOW" "$CPU" "$LOGSZ" > "$SNAP"
fi

# TEN MINUTES, ALWAYS. "No worker under the chain" is NOT an instant trigger:
# between two stages the driver legitimately has no python child for a moment,
# and the watchdog samples blind to that -- an immediate trigger there would
# push a false alarm to Jack's phone. A chain genuinely stuck with no worker
# also has a static log and static CPU, so the ten-minute snapshot catches it
# anyway, which is the condition Jack actually asked for.
if [ "$IDLE" -ge "$STALL_SECONDS" ]; then
  WHYS="workers' CPU and the log have both stood still for $(( IDLE / 60 )) min"
  [ "$NWORK" -le 1 ] && WHYS="$WHYS, and there is no worker process under the chain at all"
  STAMP="$L/.stalled_notified_${CHAIN_PID}_$(( NOW / STALL_SECONDS ))"
  [ -f "$STAMP" ] && exit 0
  : > "$STAMP"
  report "STALLED -- REGISTERED BUT NOT PROGRESSING" "$WHYS"
  /usr/bin/osascript -e "display notification \"$CHAIN_DRIVER has made no progress for $(( IDLE / 60 )) min. See ~/fx-data-logs/CHAIN_HALTED\" with title \"fx-data: CHAIN STALLED\" subtitle \"$WHEN\" sound name \"Basso\"" 2>/dev/null
  push "fx-data CHAIN STALLED" "urgent" "warning" \
    "$CHAIN_DRIVER stalled at $WHEN after $RAN min: $WHYS. Last stage: $STAGE.
--- last 10 log lines ---
$TAIL10"
fi
