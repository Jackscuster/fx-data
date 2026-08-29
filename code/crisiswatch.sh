#!/bin/sh
# Keeps the full crisis pass running on one core until it completes.
# Same backstop as valwatch.sh and for the same reason: a seventeen-hour job
# that dies quietly gets restarted from zero by whoever notices first.
R=/Users/jackcuster/Documents/fx-data
LOG=$R/results/crisis_all.log
while :; do
  if [ -s "$LOG" ] && grep -q "^DONE" "$LOG"; then exit 0; fi
  if ! pgrep -f "l2crisis_all.py" >/dev/null 2>&1; then
    ( cd "$R" && nohup nice -n 19 /usr/bin/python3 code/l2crisis_all.py >> "$LOG" 2>&1 & )
  fi
  sleep 120
done
