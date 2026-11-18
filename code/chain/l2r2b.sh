#!/bin/bash
# LAYER 2 RESTART, CHAIN 2 (HANDOFF 0l, 16 Nov). Straight on from chain 1, nothing idle.
#   1  PRE-FLIGHT SUMMARY, CORRECTED -- chain 1's glob picked audit_handcheck_*.csv (10 rows) instead of
#      the dated audit, so it reported "10/10 PASS". The verdict was right by luck and the evidence was
#      the wrong file. This names the dated file and asserts 27 items.
#   2  mode A pooled curve + the IDENTITY NULL on the cut (the full bank is already on disk)
#   3  FULL mode B honest gate 1, bank -> curve -> pooled + null
#   4  mode C STORAGE PROBE: one real shard of the 10,677,420, to size the bank from measurement
#   5  app wiring (code/r2app.py, now an appsections owner) + node --check
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

say "=== LAYER 2 RESTART CHAIN 2 ==="
say "free space: $(df -h /System/Volumes/Data | tail -1 | awk '{print $4}')"

# ---- 1. the corrected pre-flight summary ---------------------------------
g "r2b preflight summary" nice -n 19 python3 -c "
import os,sys; sys.path.insert(0,'code')
import pandas as pd, l2r2gate1 as G
G.manifest_check()
f='results/audit_$(date +%F).csv'
A=pd.read_csv(f)
assert len(A)==27, 'the dated audit has %d items, not 27: %s' % (len(A), f)
nfail=int(A.status.astype(str).str.upper().str.contains('FAIL').sum())
print('  audit %s: %d items, %d PASS, %d FAIL' % (os.path.basename(f), len(A), len(A)-nfail, nfail))
tot=bad=0
for m in ('A','B','C'):
    p='results/r2gate1_parity_mode%s.csv'%m
    d=pd.read_csv(p); tot+=len(d); bad+=int(d.mismatch.sum())
    print('  hand check mode %s on the _r2 path: %d comparisons, %d mismatches'%(m,len(d),int(d.mismatch.sum())))
print('  PRE-FLIGHT: audit %d/%d, hand checks %d comparisons %d mismatches'%(len(A)-nfail,len(A),tot,bad))
print('PRE-FLIGHT CLEAR' if not (nfail or bad) else 'PRE-FLIGHT NOT CLEAR')
sys.exit(1 if (nfail or bad) else 0)" || say "!!! PRE-FLIGHT NOT CLEAR"

# ---- 2. mode A pooled curve + identity null ------------------------------
g "r2b curve A full"  nice -n 19 python3 code/l2r2gate1.py --stage curve --mode A --tag full     || exit 1
g "r2b curve A smoke" nice -n 19 python3 code/l2r2gate1.py --stage curve --mode A --tag smoke10k || exit 1
ci "Layer 2 restart: the mode A gate 1 curve pooled over the five windows, with the identity null on the cut, and the corrected pre-flight summary (chain 1's glob read audit_handcheck_blind2_C.csv, not the dated audit)"

# ---- 3. full mode B -------------------------------------------------------
g "r2b gate1 B full" nice -n 19 python3 code/l2r2gate1.py --stage smoke --mode B --n 273780 --tag full --jobs 8 || exit 1
g "r2b curve B"      nice -n 19 python3 code/l2r2gate1.py --stage curve --mode B --tag full || exit 1
ci "Layer 2 restart STEP 4a: the FULL honest gate 1 for mode B -- all 273,780 combinations, cut on tune years only, four streams, curve and identity null over the full range"

# ---- 4. mode C storage probe ---------------------------------------------
g "r2b C probe" nice -n 19 python3 -c "
import os,sys,time,glob; sys.path.insert(0,'code')
import numpy as np, pandas as pd, l2sweep as S, l2r2gate1 as G
G.manifest_check(); S.load_costs()
opts=S.mode_opts(S.slot_options(),'C'); total=S.n_combos(opts)
combos=list(S.combo_iter(opts))[:40000]
out=G.stage_run('C', combos, 'probe40k', jobs=8, nshard=8)
sz=sum(os.path.getsize(f) for f in glob.glob(os.path.join(out,'shard_*.npz')))
stat,cb,_=G.load_bank('C','probe40k')
wins=G.windows(); tu=np.zeros((stat.shape[0],4,G.NSTAT))
for w in wins: tu+=G.role_slice(stat,*w['tune'])
el=(G.agg(tu)['n']>=G.MIN_TUNE_TRADES*len(wins))
print('  mode C storage probe: %d of %d combinations banked, %.1f MB compressed on disk' % (len(combos), total, sz/1024**2))
print('  -> full mode C bank would be %.1f GB compressed; free disk is %.1f GB'
      % (sz/1024**2*total/len(combos)/1024, os.statvfs('.').f_bavail*os.statvfs('.').f_frsize/1024**3))
print('  eligible in the pooled tune years, per stream: %s' % dict(zip(G.STREAMS,[int(x) for x in el.sum(0)])))
print('  eligible in at least one stream: %d of %d (%.1f%%)' % (int(el.any(1).sum()), len(combos), 100*el.any(1).mean()))
" || say "!! mode C probe failed"
ci "Layer 2 restart: mode C sized from a real 40,000-combination shard rather than from arithmetic -- compressed bank size and the eligible fraction measured"

# ---- 5. app wiring --------------------------------------------------------
g "r2b app" nice -n 19 python3 code/r2app.py --stage app || say "!! app wiring failed"
g "r2b node" node --check app_ui.js || say "!! app_ui.js syntax"
ci "Layer 2 restart wired into app_data.json and app_ui.js through code/appsections.py (code/r2app.py is now an owner, so a cold pipeline run rebuilds the tab instead of deleting it)"
say "L2 RESTART CHAIN 2 COMPLETE"
