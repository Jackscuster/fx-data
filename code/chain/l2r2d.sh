#!/bin/bash
# LAYER 2 RESTART, CHAIN 4 (HANDOFF 0l, 16 Nov). RECOVERY + the mode C curve.
# Chain 3 banked all 10,677,420 mode C combinations in 77 min and then DIED
# reading them back: load_bank concatenated every shard and cast to float64 --
# 15.9 GB, doubled to 31.8 GB by the concatenate, on a 16 GB machine. The bank
# is intact. stage_curve now streams one role-set at a time in float64 and
# reproduces the mode A curve EXACTLY (every column to 1e-9), so the rewrite is
# proven on a known answer before it is trusted on a new one.
#   1  mode C curve from the bank already on disk
#   2  mode B curve re-run on the streamed path (regression, must not move)
#   3  app wiring + node --check
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

say "=== LAYER 2 RESTART CHAIN 4: the mode C curve, streamed ==="
say "free space: $(df -h /System/Volumes/Data | tail -1 | awk '{print $4}')  |  .git $(du -sh .git | cut -f1)"

g "r2d curve C" nice -n 19 python3 code/l2r2gate1.py --stage curve --mode C --tag full || say "!!! mode C curve FAILED -- the bank is intact, nothing to re-bank"
ci "Layer 2 restart STEP 4b: the mode C gate 1 curve. stage_curve now STREAMS the bank one role-set at a time -- chain 3 banked all 10,677,420 combinations and then died casting them to float64 (31.8 GB on a 16 GB box). The streamed path reproduces the mode A curve exactly, column for column, before being trusted on C"

g "r2d curve B" nice -n 19 python3 code/l2r2gate1.py --stage curve --mode B --tag full || say "!! mode B curve FAILED"
g "r2d app"  nice -n 19 python3 code/r2app.py --stage app || say "!! app wiring failed"
g "r2d node" node --check app_ui.js || say "!! app_ui.js syntax"
ci "Mode B and C gate 1 curves wired into the app"
say "free space after: $(df -h /System/Volumes/Data | tail -1 | awk '{print $4}')"
say "L2 RESTART CHAIN 4 COMPLETE"
