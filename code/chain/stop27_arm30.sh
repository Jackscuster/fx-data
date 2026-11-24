#!/bin/bash
# STOP CHAIN 27 AFTER CHUNK 2, THEN RUN STAGE 2, THEN THE REST OF THE QUEUE.
#
# Jack, 24 Nov: "QUEUE ORDER FIRST. Stage 2 below goes to the front. Let chunk 2
# finish and chain 27 stop as armed. Then run the stage 2 work before chain 29
# (B1 family), chain 28, 22A and 22B. Those stay queued behind it, in that
# order, not cancelled."
#
# So the queue is: chain 30 (stage 2) -> chain 29 (B1) -> chain 28 -> 22A -> 22B.
# Nothing is cancelled and nothing is deleted.
#
# WHY. Chain 27 was snapshotted at commit 6bd0bfd, before the two commits that
# fixed b1narrow.py's stream bug and added condition3(). Its chunk 2 half is
# sound and must finish; its B1 half would rebuild the exact fault Jack
# rejected B1_WINNERS.md for. So: let chunk 2 land, stop the chain, and run
# B1-narrow from HEAD as chain 29.
#
# IT WAITS FOR THE COMMIT, NOT THE LEDGER MARKER. chainlib writes "OK c2 cmp B"
# to the ledger BEFORE the `ci` call that commits mode B's 32 part files.
# Stopping on the ledger line would kill the chain between the marker and the
# commit, losing the chunk 2 commit and leaving a dirty tree that queue.sh
# would then refuse. So the trigger is the commit line in batch1.log.
#
# FALLBACK. If the marker has been in the ledger for 6 minutes and no commit
# line has appeared, `ci` failed or was skipped. Stop anyway and commit here,
# so a failed commit cannot strand the queue.
set -uo pipefail
L="$HOME/fx-data-logs"
R="/Users/jackcuster/fx-data"
LOG="$L/queue.log"
LEDGER="$L/.chain_ledger_5568"
BATCH="$L/batch1.log"
PG=5568
say(){ echo "$(date '+%F %T') stop27b: $*" | tee -a "$LOG"; }

cd "$R"
say "armed: waiting for chunk 2's mode B commit, then stopping pgid $PG and running STAGE 2 first"
MARKED=0
while kill -0 "$PG" 2>/dev/null; do
  if grep -qF 'A2 mode B: the same' "$BATCH" 2>/dev/null; then
    say "chunk 2 mode B committed -- stopping chain 27 before its B1 half"
    break
  fi
  if grep -qxF 'OK c2 cmp B' "$LEDGER" 2>/dev/null; then
    MARKED=$((MARKED+1))
    if [ "$MARKED" -ge 6 ]; then
      say "OK c2 cmp B has stood 6 min with no commit line -- ci failed or was skipped; stopping and committing here"
      break
    fi
  fi
  sleep 60
done

if kill -0 "$PG" 2>/dev/null; then
  bash "$R/code/chain/stop_chain.sh" "$PG" 2>&1 | tee -a "$LOG"
else
  say "chain 27 had already exited on its own"
fi

sleep 20
if [ -n "$(git status --porcelain 2>/dev/null | head -1)" ]; then
  say "committing what chain 27 left behind so the queue is not refused on a dirty tree"
  git add -A >>"$LOG" 2>&1
  git -c user.name=fx-local -c user.email=fx-local@localhost commit -q \
    -m "Chunk 2 mode B outputs, committed after chain 27 was stopped before its B1 half

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>" >>"$LOG" 2>&1 \
    && say "committed $(git rev-parse --short HEAD)" || say "nothing to commit"
fi

say "starting the queue: chain 30 (STAGE 2, Jack 24 Nov), chain 29 (B1-narrow), chain 28, 22A, 22B"
exec bash "$R/code/chain/queue.sh" \
  "$R/code/chain/l2r3h.sh" \
  "$R/code/chain/l2r3g.sh" \
  "$R/code/chain/l2r3f.sh" \
  "$R/code/chain/l2r2y1.sh" \
  "$R/code/chain/l2r2y2.sh"
