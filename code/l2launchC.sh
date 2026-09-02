#!/bin/bash
# STANDING ORDER: when mode A finishes, record A and launch mode C at full power.
#
# Runs unattended. Order is fixed and the priority is absolute -- mode C never
# loses a worker to anything else once it starts.
#
#   1. wait for l2chopfinish.sh to complete A's record (or for a timeout, so a
#      failure in that step cannot hold C hostage)
#   2. record A's measured rates and C's projection in GAUNTLET.md
#   3. launch C: main pool + additive --reverse pool, caffeinated
#   4. arm the persistent swap guard from minute one
#
# LAYOUT: 6 + 3 = 9 workers on 10 cores. That is what this machine was OBSERVED
# to sustain -- 8 tuning workers plus a scoring job held load near 10 for hours,
# while 13 processes drove it to 63 and cost throughput. One core stays free for
# CI and diagnostics, which is where the inversion test and the dashboard work
# go: on spare capacity, never at C's expense.
cd "$(dirname "$0")/.."
LOG=results/launchC.log
say(){ echo "$(date '+%F %T') $*" | tee -a "$LOG"; }

say "armed; waiting for mode A chop to complete"
DEADLINE=$(( $(date +%s) + 86400 ))
while true; do
  n=$(ls results/gate2/modeA_chop/chunk_*.csv 2>/dev/null | wc -l)
  grep -q "REDO DONE" /tmp/chopfinish.log 2>/dev/null && { say "chopfinish reported REDO DONE"; break; }
  if [ "$n" -ge 57 ]; then
    # chunks are all in but the finisher has not reported. Give it four hours,
    # then go anyway: C's start is not allowed to depend on a post-step.
    [ -z "$GRACE" ] && GRACE=$(( $(date +%s) + 14400 ))
    if [ "$(date +%s)" -gt "$GRACE" ]; then say "WARNING chunks complete but chopfinish silent; starting C anyway"; break; fi
  fi
  [ "$(date +%s)" -gt "$DEADLINE" ] && { say "WARNING 24h deadline; starting C anyway"; break; }
  sleep 120
done

# STOP MODE A'S POOLS BEFORE C STARTS. Their queues were planned once, so
# whatever they still hold is work another pool has already written -- and the
# fix for that (a dispatch-time re-check) is in the code but not in these
# already-running processes. Leaving them alive would put ~15 workers on 10
# cores the moment C launches, which is the oversubscription that drove load to
# 63 and COST throughput earlier. Children first, then parent, so nothing is
# orphaned.
for P in $(pgrep -f "l2tune.py --mode A" ); do
  say "stopping leftover mode A pool $P (its queue holds only already-written chunks)"
  code/l2stoppool.sh "$P" >> "$LOG" 2>&1
done
say "recording mode A and projecting mode C"
/usr/bin/python3 code/l2arecord.py >> "$LOG" 2>&1 || say "WARNING recorder failed; continuing"

say "launching mode C main pool (6 workers)"
nohup caffeinate -i -m -s /usr/bin/python3 code/l2tune.py --mode C --jobs 6 \
      --sorted --cap 6 --staged --seed-from A,B > results/gate2_run_C.log 2>&1 &
sleep 20
MAIN=$(pgrep -f "l2tune.py --mode C --jobs 6" | head -1)
say "main pool pid $MAIN"

say "launching mode C additive --reverse pool (3 workers)"
nohup caffeinate -i -m -s /usr/bin/python3 code/l2tune.py --mode C --jobs 3 \
      --sorted --cap 6 --staged --seed-from A,B --reverse > results/gate2_run_C_rev.log 2>&1 &
sleep 20
ADD=$(pgrep -f "l2tune.py --mode C --jobs 3" | head -1)
say "reverse pool pid $ADD"

nohup code/l2swapguard.sh "$MAIN" "$ADD" 400 200 >/dev/null 2>&1 &
say "swap guard armed: main=$MAIN protected, additive=$ADD sacrificed first"

git add -A
git commit -q -m "Mode A final record, mode C projected from it, mode C launched

Launched by code/l2launchC.sh under the standing order. C runs --sorted --cap 6
--staged --seed-from A,B, no disk cache, 6+3 workers across a main and an
additive --reverse pool, caffeinated, swap guard armed from minute one.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_0198PoFd8YbETkDPepLUiDzL" || true
git pull --rebase -q origin main || true
git push -q origin main || true
say "MODE C LAUNCHED"
