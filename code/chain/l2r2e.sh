#!/bin/bash
# LAYER 2 RESTART, CHAIN 5 (HANDOFF 0l, 16 Nov): THE REGIME-SHUFFLE NULL ON GATE 1.
# All three modes' gate 1 are banked and curved. Both routed streams come out
# negative on the trade years, so before anything is read into that, routing
# itself gets null-tested: does routing on the REAL Layer 1 label do anything a
# circularly ROTATED label would not? The always-on streams are the control --
# they never read the label, so they must be identical on every draw.
# 10,000 stratified combinations x 200 draws per mode, draw 0 = the real label.
set -uo pipefail; cd /Users/jackcuster/fx-data; L="$HOME/fx-data-logs/batch1.log"
export FX_COST_TABLE=results/cost_table_h22.csv
say(){ echo "$(date '+%F %T') $*" | tee -a "$L"; }
g(){ local n="$1"; shift; local t0=$(date +%s); "$@" >> "$L" 2>&1 & local py=$!; bash code/l2memguard.sh $py 2 3 5 2400 >> "$L" 2>&1 & local gd=$!
  if ! wait $py; then say "!!! $n FAILED"; wait $gd; return 1; fi; wait $gd; say "$n done in $(( ($(date +%s)-t0)/60 )) min $(( ($(date +%s)-t0)%60 )) s"; }
ci(){ git add -A code/ results/ HANDOFF.md .gitignore app_data.json app_ui.js >/dev/null 2>&1
  git commit -q -m "$1

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_016fb2CjHx3RvfiWm6g7bVgc" >/dev/null 2>&1 || echo 'nothing to commit' >> "$L"
  git pull -q --rebase origin main >> "$L" 2>&1; git push -q origin main 2>&1 | grep -v 'GH001\|warning:' >> "$L"
  say "committed: $(git log --oneline -1)"; }

say "=== LAYER 2 RESTART CHAIN 5: the regime-shuffle null on gate 1 ==="
for M in A B C; do
  g "r2e shuffle $M" nice -n 19 python3 code/l2r2null.py --mode $M --n 10000 --draws 200 --jobs 8 \
    || say "!!! shuffle null mode $M FAILED"
  ci "Layer 2 restart: the regime-shuffle null on gate 1, mode $M -- 10,000 stratified combinations x 200 circularly rotated label draws, compared at a fixed selection size rather than a fixed cut, with the always-on stream as the must-not-move control"
done
g "r2e app"  nice -n 19 python3 code/r2app.py --stage app || say "!! app wiring failed"
g "r2e node" node --check app_ui.js || say "!! app_ui.js syntax"
ci "The gate 1 shuffle nulls wired into the app"
say "L2 RESTART CHAIN 5 COMPLETE"
