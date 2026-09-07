#!/bin/bash
# QUEUE: fine-tune -> costed cut -> TEAM BUILD -> then C relaunch.
# Mode C stays paused until the team build finishes.
cd "$(dirname "$0")/.."
LOG=results/teamchain.log
say(){ echo "$(date '+%F %T') $*" | tee -a "$LOG"; }
say "armed: waiting for the gate 3 fine-tune to finish"
while pgrep -f "l2gate3ft.py --shard" >/dev/null; do sleep 300; done
say "fine-tune done; re-evaluating adoptions under rule v2"
/usr/bin/python3 code/l2readopt.py >> "$LOG" 2>&1 || say "WARNING readopt failed"
say "running the costed gate 3 cut (Sharpe retired as a bar)"
nice -n 19 /usr/bin/python3 code/l2gate3.py --no-pace-check >> "$LOG" 2>&1 || say "WARNING cut failed"
say "BUILDING THE TEAMS"
nice -n 19 /usr/bin/python3 code/l2team.py >> "$LOG" 2>&1 || say "WARNING team build failed"
say "teams done; running the AGREEMENT STUDY"
nice -n 19 /usr/bin/python3 code/l2agree.py >> "$LOG" 2>&1 || say "WARNING agreement study failed"
say "agreement study done; committing"
/usr/bin/python3 code/appstamp.py >> "$LOG" 2>&1
git add -A
git commit -q -m "Gate 3 costed cut and the trading teams

Built by code/l2team.py under the queued chain.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_0198PoFd8YbETkDPepLUiDzL" || true
git pull --rebase -q origin main || true; git push -q origin main || true
say "RELAUNCHING MODE C"
nohup caffeinate -i -m -s /usr/bin/python3 code/l2tune.py --mode C --jobs 6 \
      --sorted --cap 6 --seed-from A,B >> results/gate2_run_C.log 2>&1 &
sleep 25; MAIN=$(pgrep -f "l2tune.py --mode C --jobs 6" | head -1)
nohup caffeinate -i -m -s /usr/bin/python3 code/l2tune.py --mode C --jobs 3 \
      --sorted --cap 6 --seed-from A,B --reverse >> results/gate2_run_C_rev.log 2>&1 &
sleep 25; ADD=$(pgrep -f "l2tune.py --mode C --jobs 3" | head -1)
nohup code/l2swapguard.sh "$MAIN" "$ADD" 400 200 >/dev/null 2>&1 &
say "C relaunched main=$MAIN add=$ADD; swap guard armed"
say "chunks on disk: $(ls results/gate2/modeC_*/chunk_*.csv 2>/dev/null | wc -l)"
say "CHAIN COMPLETE"
