#!/bin/bash
# LAYER 2 RESTART, CHAIN 1 (HANDOFF 0l, 16 Nov). ONE DRIVER, EVERY STEP, NO PAUSE.
#   1  supersede headers on the old gate 1 / gate 2 selection files (nothing deleted)
#   2  STEP 1: scope from code + MEASURED seconds per combination for A, B and C
#   3  parity: the _r2 code path against the shipped l2tune.Scorer, mode A
#   4  STEP 2 SMOKE: 10,000 stratified mode A combinations, bank -> gate 1 curve, end to end
#   5  PRE-FLIGHT: 27-item audit (dated), Layer 1 manifest md5, hand check per mode on _r2
#   6  gated on a clean pre-flight: the FULL mode A honest gate 1
#   7  app wiring + node --check, commit and push at every marker
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

say "=== LAYER 2 RESTART CHAIN 1 (HANDOFF 0l) ==="
say "free space: $(df -h /System/Volumes/Data | tail -1 | awk '{print $4}')"

# ---- 1. supersede, nothing deleted ---------------------------------------
g "r2 supersede" nice -n 19 python3 code/l2r2supersede.py || say "!! supersede blocked -- reported, see the table"
ci "Layer 2 restart (HANDOFF 0l): the parked 45,139 cloud run is cancelled and the old gate 1 is superseded, not deleted

The gate 1 on disk cut on W2+W3 pooled = 2011-2020, which is every year Layer 2 then called blind (faults #1 and #4), and it charged no costs at all. Its survivors and the field built from them are headed SUPERSEDED BY 0l and kept in full. Ten readers gained comment='#' so a header line cannot break them the way it broke freshness.py. Also recorded: refit_candidates_full.csv was 100 mode-A-trend combinations short of its own gate 1 (all c1=waddah_attar_explosion_signals, lost with an unfinished tuning shard) and nothing compared the counts."

# ---- 2. STEP 1 ------------------------------------------------------------
g "r2 step1" nice -n 19 python3 code/l2r2step1.py || exit 1
ci "Layer 2 restart STEP 1: library, mode enumeration, the original gate 1's actual rule, and MEASURED seconds per combination for A, B and C"

# ---- 3. parity on the _r2 path -------------------------------------------
g "r2 parity A" nice -n 19 python3 code/l2r2gate1.py --stage parity --mode A --n 6 || exit 1

# ---- 4. STEP 2 SMOKE, end to end -----------------------------------------
g "r2 smoke A 10k" nice -n 19 python3 code/l2r2gate1.py --stage smoke --mode A --n 10000 --tag smoke10k --jobs 8 || exit 1
ci "Layer 2 restart STEP 2 SMOKE: 10,000 stratified mode A combinations through the honest gate 1 end to end, cut on tune years only, curve swept over its full range"

# ---- 5. PRE-FLIGHT --------------------------------------------------------
PF=0
g "r2 preflight audit" nice -n 19 python3 code/preflight.py --out audit_$(date +%F).csv || { PF=1; say "!!! PRE-FLIGHT AUDIT FAILED"; }
g "r2 parity B" nice -n 19 python3 code/l2r2gate1.py --stage parity --mode B --n 6 || { PF=1; say "!!! mode B hand check FAILED"; }
g "r2 parity C" nice -n 19 python3 code/l2r2gate1.py --stage parity --mode C --n 6 || { PF=1; say "!!! mode C hand check FAILED"; }
g "r2 preflight summary" nice -n 19 python3 -c "
import os,sys,glob
sys.path.insert(0,'code')
import pandas as pd, l2r2gate1 as G
G.manifest_check()
f=sorted(glob.glob('results/audit_*.csv'))[-1]
A=pd.read_csv(f)
col=[c for c in A.columns if c.lower() in ('status','result','verdict','pass')][0]
nfail=int((A[col].astype(str).str.upper().str.contains('FAIL')).sum())
print('  audit %s: %d items, %d FAIL' % (os.path.basename(f), len(A), nfail))
tot=0; bad=0
for m in ('A','B','C'):
    p='results/r2gate1_parity_mode%s.csv'%m
    if os.path.exists(p):
        d=pd.read_csv(p); tot+=len(d); bad+=int(d.mismatch.sum())
        print('  hand check mode %s on the _r2 path: %d comparisons, %d mismatches' % (m,len(d),int(d.mismatch.sum())))
print('  PRE-FLIGHT: audit %d/%d PASS, hand checks %d comparisons %d mismatches' % (len(A)-nfail,len(A),tot,bad))
sys.exit(1 if (nfail or bad) else 0)" || { PF=1; say "!!! PRE-FLIGHT NOT CLEAR"; }
ci "Layer 2 restart PRE-FLIGHT: dated 27-item audit, Layer 1 manifest md5, and the hand check per mode on the _r2 code path"

# ---- 6. the full mode A honest gate 1, GATED on a clean pre-flight --------
if [ "$PF" = "0" ]; then
  say "PRE-FLIGHT CLEAR -- starting the FULL mode A honest gate 1"
  g "r2 gate1 A full" nice -n 19 python3 code/l2r2gate1.py --stage smoke --mode A --n 273780 --tag full --jobs 8 || say "!!! full mode A gate 1 FAILED"
  ci "Layer 2 restart STEP 2: the FULL honest gate 1 for mode A -- every combination scored at defaults, costs on, cut on tune years only, four streams, curve over the full range"
else
  say "PRE-FLIGHT NOT CLEAR -- the full mode A gate 1 is NOT started. Reported, not worked around."
fi

# ---- 7. app wiring --------------------------------------------------------
g "r2 node check" node --check app_ui.js || say "!! app_ui.js syntax"
ci "Layer 2 restart chain 1: results wired, app_ui.js checked"
say "L2 RESTART CHAIN 1 COMPLETE"
