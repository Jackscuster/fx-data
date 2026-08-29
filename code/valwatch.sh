#!/bin/sh
# Keeps the pinned-environment validation running until it completes GREEN.
#
# WHY THIS EXISTS. The standing rule says side-work takes one core and never
# stops. Intent was not enough: the validation was killed three separate times
# by cleanup commands aimed at other processes, and each time it simply stayed
# dead until someone noticed. A rule that depends on remembering is not a rule,
# it is a hope. This is the backstop.
#
# The pgrep pattern matches code/pipeline.py, NOT the venv path: the venv python
# is a symlink to the system binary, so the resolved command line never contains
# "pin-venv" and matching on it spawned a duplicate every 60 seconds.
# It restarts only when the run is ABSENT, never when it is merely slow, and it
# stops for good once the log shows a clean pass -- so a green result is not
# overwritten by a needless rerun.
R=/Users/jackcuster/Documents/fx-data
LOG=$R/results/ci_pinned_validation.log
PY=/private/tmp/claude-501/-Users-jackcuster-Documents-fx-data/02556050-6b5b-4d3c-ae62-ce5c2508df92/scratchpad/pin-venv/bin/python
STATE=$R/results/ci_validation_state.txt

while :; do
  if [ -s "$LOG" ] && ! grep -q "Traceback" "$LOG" && grep -q "app_data.json" "$LOG"; then
    echo "GREEN $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$STATE"
    exit 0
  fi
  if ! pgrep -f "code/pipeline.py" >/dev/null 2>&1; then
    echo "RESTART $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$STATE"
    ( cd "$R" && nohup nice -n 19 "$PY" code/pipeline.py > "$LOG" 2>&1 & )
  fi
  sleep 60
done
