#!/bin/bash
# THE CLEAN-FIELD CHAIN — results/gate2_cleanfield.csv, 4,807 strategies.
#
#   engine -> structures -> identity null -> random-entry null -> three-way
#   sizing -> team-size sweep -> slice controls -> per-slice walks -> report
#
#   bash code/l2cfchain.sh [--jobs N] [--from STAGE] [--resume] [--limit N] [--suffix S]
#
#   --resume   skip every stage whose OUTPUT is already on disk and passes its
#              own check (see done_*). This is how a rented box picks up from
#              what the repo already carries: the engine pickles are never
#              committed, so the engine always runs unless its pickles exist.
#   --from     resume at a named stage regardless of what is on disk.
#   --limit N  DRY RUN: first N strategies per slice, suffix _cleanfield_dry,
#              every guard still armed. Proves the script, not the result.
#
# EVERY STAGE NAMES ITS FIELD. l2walkfwd.load_field prints the field file and
# the per-slice counts as its first line and halts if the loaded field does not
# match the file. The pre-flight below checks the same file before a minute is
# spent, because on 2026-09-11 a run's member counts were read off a stale log
# from a different run six hours earlier.
#
# THE YEAR-SHUFFLED NULL IS NOT RUN. It is superseded and confounded -- it
# permutes which years get TRADED and 2011-2015 is far richer than 2016-2020,
# so the null score rises with the number of rich years drawn. `--n-null 0`
# makes stage_walk return after the structures, and the two VALID nulls -- the
# identity null and the random-entry null -- run as their own stages.
#
# EVERY POOL STAGE IS CAPPED BY RAM, NOT BY CORES: workers = min(--jobs,
# 60% of physical RAM / that stage's measured per-worker GB). The random-entry
# null's workers peak at ~2 GB (2.5 budgeted -> 3 on 16 GB); nine of them with
# the old 6.9 GB init demanded ~70 GB from a 16 GB Mac, the compressor
# thrashed, watchdogd starved, and the kernel panicked -- twice, 2026-09-11
# 23:33 and 2026-09-12 11:45, both inside that stage. code/l2memguard.sh
# shadows every stage and SIGSTOPs it below 3 GB free, SIGCONT above 4 GB.
set -uo pipefail
cd "$(dirname "$0")/.."
source code/l2chainguard.sh

JOBS=9; FROM=""; RESUME=0; LIMIT=""; SUF=_cleanfield
FIELD=results/gate2_cleanfield.csv
SLICES='A-trend,A-chop,B-chop'
WANT="4807 A-trend=2960 A-chop=930 B-chop=917"
while [ $# -gt 0 ]; do
  case "$1" in
    --jobs)   JOBS="$2"; shift 2;;
    --field)  FIELD="$2"; shift 2;;
    --slices) SLICES="$2"; shift 2;;
    --want)   WANT="$2"; shift 2;;      # "<total> <slice>=<n> ..." the field file must match
    --from)   FROM="$2"; shift 2;;
    --resume) RESUME=1; shift;;
    --limit)  LIMIT="$2"; shift 2;;
    --suffix) SUF="$2"; shift 2;;
    *) echo "unknown arg $1"; exit 2;;
  esac
done

# CHAIN LOGS LIVE OUTSIDE results/ so a git operation on the repo cannot unlink
# a running job's stdout -- 2026-09-11, `git stash -u`, two hours. AND OUTSIDE
# THE SESSION SCRATCHPAD: that directory is wiped when the Claude session ends,
# and on 2026-09-11 23:36 it took a running chain's log with it. $HOME survives.
LOGDIR="${CF_LOGDIR:-$HOME/fx-data-logs}"
mkdir -p "$LOGDIR"
LOG="$LOGDIR/cfchain${SUF}.log"
say(){ echo "$(date '+%F %T') $*" | tee -a "$LOG"; }

# ---- dry run: a small field file derived from the real one, own suffix
if [ -n "$LIMIT" ]; then
  SUF="${SUF}_dry"; LOG="$LOGDIR/cfchain${SUF}.log"
  SRC_FIELD="$FIELD"; FIELD="${FIELD%.csv}_dry${LIMIT}.csv"
  WANT=$(/usr/bin/env python3 - "$LIMIT" "$FIELD" "$SRC_FIELD" "$SLICES" <<'PYD'
import sys, pandas as pd
n, out = int(sys.argv[1]), sys.argv[2]
d = pd.read_csv(sys.argv[3], low_memory=False)
lab = d.sid.map(lambda s: s.split('|')[0] if not s.startswith('B|') else 'B-' + s.split('|')[1])
keep = pd.concat([g.head(n) for _, g in d.groupby(lab, sort=False)])
keep.to_csv(out, index=False)
c = lab[keep.index].value_counts()
print('%d %s' % (len(keep), ' '.join('%s=%d' % (k, c.get(k, 0)) for k in sys.argv[4].split(','))))
PYD
)
  NNULL=3; NRAND=3
  say "DRY RUN: --limit $LIMIT per slice -> $FIELD ($WANT), suffix $SUF, $NNULL null draws"
  say "DRY RUN: the smallest limit that populates all four structures is 250 (STABLE step 2 has 1 member at 150)"
fi
NNULL="${NNULL:-25}"; NRAND="${NRAND:-25}"

STAGES="engine walk nullid nullre sizing size ctrl perslice report"
if [ -n "$FROM" ]; then
  case " $STAGES " in *" $FROM "*) ;; *) echo "unknown stage $FROM"; exit 2;; esac
fi
chain_pidfile "cf${SUF}"

# ---- RAM-derived caps: workers = min(JOBS, 60% of RAM / per-worker GB)
ram_gb=$(/usr/bin/env python3 -c "
import os
try: b = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')
except (ValueError, OSError): b = int(__import__('subprocess').check_output(['sysctl','-n','hw.memsize']))
print(b // 2**30)")
budget_gb=$(( ram_gb * 6 / 10 ))
cap(){  # cap <per-worker GB, may be fractional> -> workers
  local w; w=$(/usr/bin/env python3 -c "import math; print(max(1, min($JOBS, int($budget_gb / $1))))"); echo "$w"; }
# Per-worker GB, overridable per run (NULLID_GB=3 ...). The defaults are the
# three-slice measurements (4,807 strategies, 1,094-passer book). The book is
# what scales: on the four-slice field (8,235; 2,323 passers) six identity-null
# workers at the 1.5 GB budget drove the Mac under 3 GB free at spawn and the
# guard held the stage paused for 73 minutes. Budget 3 GB there.
ENGINE_JOBS=$(cap "${ENGINE_GB:-0.5}")   # engine workers: bars + one strategy's trades
NULLID_JOBS=$(cap "${NULLID_GB:-1.5}")   # _init_null: 1.0 GB tables + the walk's book
NULLRE_JOBS=$(cap "${NULLRE_GB:-2.5}")   # _init_rand: 1.3 GB init, 2.0 GB peak per draw (measured)
SIZE_JOBS=$(cap "${SIZE_GB:-1.5}")       # _init_size: as _init_null
say "=== PRE-FLIGHT === ${ram_gb} GB RAM, ${budget_gb} GB budget: engine=$ENGINE_JOBS nullid=$NULLID_JOBS nullre=$NULLRE_JOBS size=$SIZE_JOBS (--jobs $JOBS)  field=$FIELD suffix=$SUF"
if ! /usr/bin/env python3 code/l2nosilence.py 2>&1 | tee -a "$LOG" | tail -1 | grep -q "NO SILENCED ERRORS"; then
  say "!! HALT: silenced errors present"; exit 3
fi
need_flags code/l2walkfwd.py --stage --slices --jobs --suffix --field-file --structures --n-null --n-rand 2>&1 | tee -a "$LOG"
# shellcheck disable=SC2086
assert_field "$FIELD" $WANT 2>&1 | tee -a "$LOG"
say "pre-flight passed"

O(){ echo "results/$1${SUF}.$2"; }          # suffixed output path
# ---- done_<stage>: the OUTPUT exists and passes its own check
done_engine(){ [ -s "$(O wf_trades pkl)" ] && [ -s "$(O wf_marks pkl)" ] &&
  WF_TAG="$SUF" /usr/bin/env python3 - "$FIELD" <<'PYP'
import os, sys, pandas as pd
sys.path.insert(0, 'code'); import l2walkfwd as W
T = pd.read_pickle(W.OUT('wf_trades.pkl'))
cf = set(pd.read_csv(sys.argv[1], low_memory=False).sid)
sys.exit(0 if set(T.sid.unique()) == cf else 1)
PYP
}
done_walk(){ [ -s "$(O walkforward_structures_3slice csv)" ] && [ -s "$(O walkforward_daily_3slice csv)" ]; }
done_nullid(){ [ -s "$(O walkforward_null_identity_summary_3slice csv)" ] &&
  /usr/bin/env python3 - "$(O walkforward_null_identity_summary_3slice csv)" "$(O walkforward_structures_3slice csv)" <<'PYN'
import sys, pandas as pd
# the null's draws must carry the SAME field as the real: ALLPASS passer count equal
n = pd.read_csv(sys.argv[1], comment='#'); s = pd.read_csv(sys.argv[2], comment='#')
a = n[n.structure == 'ALLPASS'].mean_members_step1.iloc[0]
b = s[s.structure == 'ALLPASS'].members_step1.iloc[0]
sys.exit(0 if abs(a - b) < 0.5 else 1)
PYN
}
done_nullre(){ [ -s "$(O walkforward_null_randomentry_summary_3slice csv)" ]; }
done_sizing(){ [ -s "$(O walkforward_structures_sizing csv)" ]; }
done_size(){ [ -s "$(O walkforward_teamsize_verdict csv)" ]; }
done_ctrl(){ [ -s "$(O walkforward_slicecontrols_3slice csv)" ]; }
done_perslice(){ [ -s "$(O walkforward_perslice_3slice csv)" ]; }
done_report(){ false; }

started=0
# want <stage>: true when the stage should run
want(){
  local st="$1"
  if [ -n "$FROM" ]; then
    if [ "$started" = 1 ] || [ "$st" = "$FROM" ]; then started=1; return 0; fi
    say "skip $st (--from $FROM)"; return 1
  fi
  if [ "$RESUME" = 1 ] && "done_$st"; then
    say "skip $st (--resume: output present and checked)"; return 1
  fi
  return 0
}
# run <name> <jobs> <args...>
run(){
  local name="$1" jobs="$2"; shift 2
  local t0 t1; t0=$(date +%s)
  say "--- $name --- ($jobs workers)"
  nice -n 19 /usr/bin/env python3 code/l2walkfwd.py "$@" \
        --jobs "$jobs" --slices "$SLICES" --suffix "$SUF" --field-file "$FIELD" \
        >> "$LOG" 2>&1 &
  local py=$!
  bash code/l2memguard.sh "$py" 3 4 5 900 >> "$LOG" 2>&1 &
  local guard=$!
  if ! wait "$py"; then
    say "!!! CHAIN HALTED at $name"; echo "$name" > results/CHAIN_HALT.marker; wait "$guard"; exit 1
  fi
  wait "$guard"
  t1=$(date +%s)
  say "$name done in $(( (t1 - t0) / 60 )) min $(( (t1 - t0) % 60 )) s"
}
rm -f results/CHAIN_HALT.marker
T_ALL=$(date +%s)
want engine   && run engine  "$ENGINE_JOBS" --stage engine
want walk     && run walk    "$JOBS"        --stage walk   --n-null 0
want nullid   && run nullid  "$NULLID_JOBS" --stage nullid --n-null "$NNULL"
want nullre   && run nullre  "$NULLRE_JOBS" --stage nullre --n-null "$NNULL"
want sizing   && run sizing  "$JOBS"        --stage sizing
want size     && run size    "$SIZE_JOBS"   --stage size   --n-null "$NNULL" --n-rand "$NRAND"
want ctrl     && run ctrl    "$JOBS"        --stage ctrl
if want perslice; then
  t0=$(date +%s); say "--- perslice ---"
  nice -n 19 /usr/bin/env python3 code/l2cfperslice.py --suffix "$SUF" --field-file "$FIELD" --slices "$SLICES" >> "$LOG" 2>&1 &
  py=$!; bash code/l2memguard.sh "$py" 3 4 5 900 >> "$LOG" 2>&1 & guard=$!
  if ! wait "$py"; then
    say "!!! CHAIN HALTED at perslice"; echo perslice > results/CHAIN_HALT.marker; wait "$guard"; exit 1
  fi
  wait "$guard"
  say "perslice done in $(( ($(date +%s) - t0) / 60 )) min $(( ($(date +%s) - t0) % 60 )) s"
fi
say "--- report ---"
if ! /usr/bin/env python3 code/l2cfreport.py --suffix "$SUF" >> "$LOG" 2>&1; then
  say "!!! CHAIN HALTED at report"; echo report > results/CHAIN_HALT.marker; exit 1
fi
say "CHAIN COMPLETE in $(( ($(date +%s) - T_ALL) / 60 )) min"
