#!/bin/bash
# THE FULL QUEUE, armed against the fine-tune's completion.
#   re-judge all banked rows W3-only -> gate 3 cut on ADOPTED settings ->
#   team builder (both teams) -> selection holdout + random-team null ->
#   agreement study -> mode C relaunch + swap guard
#
# Single instance via a pidfile. macOS has no flock, and matching our own name
# with pgrep also matches the nohup wrapper -- that mistake left an earlier
# guard exiting immediately while reporting success.
PIDF=/tmp/.l2chain2.pid
if [ -f "$PIDF" ] && kill -0 "$(cat "$PIDF" 2>/dev/null)" 2>/dev/null; then exit 0; fi
echo $$ > "$PIDF"; trap 'rm -f "$PIDF"' EXIT
cd /Users/jackcuster/Documents/fx-data
LOG=results/chain2.log
say(){ echo "$(date '+%F %T') $*" >> "$LOG"; }
say "armed: waiting for the gate 3 fine-tune"
while pgrep -f "l2gate3ft.py --shard" >/dev/null; do sleep 300; done
say "fine-tune finished"
say "1/6 re-judging every banked row on the W3-only basis"
nice -n 19 /usr/bin/python3 code/l2readopt.py >> "$LOG" 2>&1 || say "WARN readopt"
say "2/6 gate 3 cut on ADOPTED settings (W3ONLY)"
nice -n 19 /usr/bin/python3 code/l2clean3.py >> "$LOG" 2>&1 || say "WARN clean3"
say "3/6 team builder, both teams"
TEAM_LABEL=_W3ONLY_ADOPTED TEAM_JOBS=6 nice -n 19 /usr/bin/python3 code/l2team.py >> "$LOG" 2>&1 || say "WARN team"
TEAM_JOBS=6 nice -n 19 /usr/bin/python3 code/l2teamkpi.py --label _W3ONLY_ADOPTED >> "$LOG" 2>&1 || say "WARN kpi"
say "4/6 selection holdout + random-team null"
nice -n 19 /usr/bin/python3 code/l2teamcheck.py --label _W3ONLY_ADOPTED >> "$LOG" 2>&1 || say "WARN checks"
say "5/6 agreement study"
nice -n 19 /usr/bin/python3 code/l2agree.py >> "$LOG" 2>&1 || say "WARN agree"
/usr/bin/python3 code/appstamp.py >> "$LOG" 2>&1
git add -A; git commit -q -m "Gate 3 adopted-settings cut, teams, checks and agreement study" || true
git pull --rebase -q origin main || true; git push -q origin main || true
say "5b/6 resuming the B-trend ip1 recovery, now the machine is free"
nohup nice -n 19 /usr/bin/python3 code/l2recoverip1.py --which all \
      >> results/ip1_all.log 2>&1 &
say "6/6 relaunching mode C"
nohup caffeinate -i -m -s /usr/bin/python3 code/l2tune.py --mode C --jobs 6 \
      --sorted --cap 6 --seed-from A,B >> results/gate2_run_C.log 2>&1 &
sleep 25; MAIN=$(pgrep -f "l2tune.py --mode C --jobs 6" | head -1)
nohup caffeinate -i -m -s /usr/bin/python3 code/l2tune.py --mode C --jobs 3 \
      --sorted --cap 6 --seed-from A,B --reverse >> results/gate2_run_C_rev.log 2>&1 &
sleep 25; ADD=$(pgrep -f "l2tune.py --mode C --jobs 3" | head -1)
nohup code/l2swapguard.sh "$MAIN" "$ADD" 400 200 >/dev/null 2>&1 &
say "C relaunched main=$MAIN add=$ADD, guard armed; chunks $(ls results/gate2/modeC_*/chunk_*.csv 2>/dev/null|wc -l)"
say "CHAIN COMPLETE"
