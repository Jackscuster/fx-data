#!/bin/bash
# LAYER 2 RESTART, CHAIN 3 (HANDOFF 0l, 16 Nov): the FULL mode C honest gate 1.
# 10,677,420 combinations, 39x modes A and B because the exit slot is live.
# Measured at 2.8 ms/combination: ~8.2 core-hours, ~1.0 h on 8 Mac cores.
# STORAGE IS THE CONSTRAINT, not time. The 16-year bank measures 6.4 GB
# compressed against 5.3 GB free, so mode C banks 2011-2020 only -- exactly the
# years the five windows use, 4.0 GB. The shards halt cleanly below 1 GB free
# and the bank is resumable, so a halt costs the shard in flight and nothing else.
set -uo pipefail; cd /Users/jackcuster/fx-data; L="$HOME/fx-data-logs/batch1.log"
export FX_COST_TABLE=results/cost_table_h22.csv
say(){ echo "$(date '+%F %T') $*" | tee -a "$L"; }
g(){ local n="$1"; shift; local t0=$(date +%s); "$@" >> "$L" 2>&1 & local py=$!; bash code/l2memguard.sh $py 2 3 5 1800 >> "$L" 2>&1 & local gd=$!
  if ! wait $py; then say "!!! $n FAILED"; wait $gd; return 1; fi; wait $gd; say "$n done in $(( ($(date +%s)-t0)/60 )) min $(( ($(date +%s)-t0)%60 )) s"; }
ci(){ git add -A code/ results/ HANDOFF.md app_data.json app_ui.js >/dev/null 2>&1
  git commit -q -m "$1

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_016fb2CjHx3RvfiWm6g7bVgc" >/dev/null 2>&1 || echo 'nothing to commit' >> "$L"
  git pull -q --rebase origin main >> "$L" 2>&1; git push -q origin main 2>&1 | grep -v 'GH001\|warning:' >> "$L"
  say "committed: $(git log --oneline -1)"; }

say "=== LAYER 2 RESTART CHAIN 3: the FULL mode C honest gate 1 ==="
say "free space before: $(df -h /System/Volumes/Data | tail -1 | awk '{print $4}')"
g "r2c gate1 C full" nice -n 19 python3 code/l2r2gate1.py --stage smoke --mode C --n 10677420 --tag full --years 2011-2020 --jobs 8 || say "!!! mode C gate 1 halted -- the bank is resumable, rerun the same line"
say "free space after: $(df -h /System/Volumes/Data | tail -1 | awk '{print $4}')"
ci "Layer 2 restart STEP 4b: the FULL honest gate 1 for mode C -- all 10,677,420 combinations, cut on tune years only, four streams, curve and identity null over the full range"
g "r2c app" nice -n 19 python3 code/r2app.py --stage app || say "!! app wiring failed"
g "r2c node" node --check app_ui.js || say "!! app_ui.js syntax"
ci "Mode C gate 1 wired into the app"
say "L2 RESTART CHAIN 3 COMPLETE"
