#!/bin/bash
# RE-RUN everything the mode bug touched, on the fixed code.
#
# l2trades.run_pair hardcoded mode B, so every mode A and C configuration ran
# with B's exit rule. Each study below reads its configurations through
# run_pair, so each inherited it. The gate 3 cut and the W3-only leaderboards
# do NOT appear here: they go through l2tune's Scorer, which always passed the
# real mode.
#
# LOW PRIORITY BY DESIGN. Waits for the main chain to finish, then runs one
# study at a time on one core at nice 19, so it can never compete with mode C
# once the chain relaunches it.
PIDF=/tmp/.l2rerun.pid
if [ -f "$PIDF" ] && kill -0 "$(cat "$PIDF" 2>/dev/null)" 2>/dev/null; then exit 0; fi
echo $$ > "$PIDF"; trap 'rm -f "$PIDF"' EXIT
cd /Users/jackcuster/Documents/fx-data
LOG=results/rerun.log
say(){ echo "$(date '+%F %T') $*" >> "$LOG"; }
say "armed: waiting for the main chain"
while pgrep -f l2chain2.sh >/dev/null || pgrep -f "l2gate3ft.py --shard" >/dev/null; do sleep 300; done
say "chain finished; re-running the affected studies on fixed code"
run(){ say "  -> $1"; nice -n 19 /usr/bin/python3 "$@" >> "$LOG" 2>&1 || say "     WARN $1 failed"; }
run code/l2crisis_all.py --mode A --slice trend --src results/gate2_tuned_modeA_trend.csv
run code/l2crisis_all.py --mode A --slice chop  --src results/gate2_tuned_modeA_chop.csv
run code/l2suppvol.py
run code/l2entrytime.py
run code/l2calendar.py
run code/l2agree.py
run code/l2tripwire.py
say "re-runs done; committing"
git add -A
git commit -q -m "Re-run the mode-bug-affected studies on fixed code" || true
git fetch -q origin && git rebase -q origin/main >/dev/null 2>&1 && git push -q origin main || true
say "RERUN COMPLETE"
