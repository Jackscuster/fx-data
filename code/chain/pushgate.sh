#!/bin/bash
# WAIT UNTIL THE REMOTE HOLDS LOCAL HEAD, then exit 0. Exit 1 on timeout.
#
# WHY A GATE AND NOT A CHECK. Every chain stage ends with `ci`, which runs
# `git pull --rebase origin main` and pushes. Doing that while a batched push
# is still landing a rewritten history risks rebasing onto a partial state. So
# the queue's first stage blocks until the remote and HEAD agree.
set -uo pipefail
cd /Users/jackcuster/fx-data
MAX="${1:-21600}"      # 6 h
T0=$(date +%s)
while :; do
  R=$(git ls-remote origin refs/heads/main 2>/dev/null | cut -f1)
  H=$(git rev-parse HEAD)
  if [ "$R" = "$H" ]; then
    echo "  push gate: remote main == local HEAD ($(git rev-parse --short HEAD)); proceeding"
    exit 0
  fi
  AHEAD=$(git rev-list --count "$R..$H" 2>/dev/null || echo "?")
  EL=$(( ($(date +%s) - T0) / 60 ))
  echo "  push gate: remote $(echo $R | cut -c1-8), local $(echo $H | cut -c1-8), $AHEAD commits behind, waited $EL min"
  if [ $(( $(date +%s) - T0 )) -ge "$MAX" ]; then
    echo "  push gate: GAVE UP after $(( MAX / 3600 )) h -- the remote never caught up"
    exit 1
  fi
  sleep 120
done
