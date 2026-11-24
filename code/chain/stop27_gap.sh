#!/bin/bash
# STOP CHAIN 27 AFTER CHUNK 2 AND THEN STOP. LAUNCH NOTHING.
#
# Jack, 24 Nov: "Do this in the gap after chain 27 stops and before stage 2
# launches. No chain may be committing while it runs. Hold the stage 2 launch
# until step 6 passes."
#
# So this waiter does NOT start the queue. It stops chain 27, commits whatever
# chunk 2 left, and writes a marker. The history rewrite happens in that gap
# with nothing else touching the tree, and the queue is launched by hand once
# the push is confirmed.
set -uo pipefail
L="$HOME/fx-data-logs"
R="/Users/jackcuster/fx-data"
LOG="$L/queue.log"
LEDGER="$L/.chain_ledger_5568"
BATCH="$L/batch1.log"
GAP="$L/GAP_READY"
PG=5568
say(){ echo "$(date '+%F %T') gap: $*" | tee -a "$LOG"; }

cd "$R"
rm -f "$GAP"
say "armed: waiting for chunk 2's mode B commit, then stopping pgid $PG. LAUNCHES NOTHING."
MARKED=0
while kill -0 "$PG" 2>/dev/null; do
  if grep -qF 'A2 mode B: the same' "$BATCH" 2>/dev/null; then
    say "chunk 2 mode B committed -- stopping chain 27"
    break
  fi
  if grep -qxF 'OK c2 cmp B' "$LEDGER" 2>/dev/null; then
    MARKED=$((MARKED+1))
    if [ "$MARKED" -ge 6 ]; then
      say "OK c2 cmp B has stood 6 min with no commit line -- stopping and committing here"
      break
    fi
  fi
  sleep 30
done

if kill -0 "$PG" 2>/dev/null; then
  bash "$R/code/chain/stop_chain.sh" "$PG" 2>&1 | tee -a "$LOG"
else
  say "chain 27 had already exited on its own"
fi

sleep 20
# WAIT FOR EVERY WORKER TO BE GONE BEFORE DECLARING THE GAP OPEN. A history
# rewrite with a python worker still holding the tree is the one thing that
# must not happen here.
for i in $(seq 1 40); do
  n=$(pgrep -f 'code/r2reads.py|code/b1narrow.py|code/l2r2gate2.py' | wc -l | tr -d ' ')
  [ "$n" = "0" ] && break
  say "waiting for $n stage worker(s) to exit"
  sleep 15
done

if [ -n "$(git status --porcelain 2>/dev/null | head -1)" ]; then
  say "committing what chain 27 left behind"
  git add -A >>"$LOG" 2>&1
  git -c user.name=fx-local -c user.email=fx-local@localhost commit -q \
    -m "Chunk 2 mode B outputs, committed after chain 27 was stopped before its B1 half

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>" >>"$LOG" 2>&1 \
    && say "committed $(git rev-parse --short HEAD)" || say "nothing to commit"
fi

printf 'gap open %s\nHEAD %s\n' "$(date '+%F %T')" "$(git rev-parse HEAD)" > "$GAP"
say "GAP OPEN at $(git rev-parse --short HEAD). No chain is running and nothing is queued."
say "  the history rewrite runs now; the queue is launched by hand after the push is confirmed."
