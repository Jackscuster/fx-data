#!/bin/bash
# RERUN STAGE 1 R2, STAGE 2, STAGE 3 AND STAGE 4 WITH THE VOLATILITY FLOOR ON.
# Jack's decided rule 1: no entry while the pair's own ATR is in its bottom 5%.
# A, B and C all continue (his instruction supersedes the earlier "drop C").
# Does not touch chain_current: 22A owns it.
set -u
cd /Users/jackcuster/fx-data
export FX_COST_TABLE=$PWD/results/cost_table_h22.csv
L=$HOME/fx-data-logs/s234flag.log
: > $L
say(){ echo "[$(date '+%H:%M:%S')] $*" | tee -a $L; }
run(){ local n=$1 m=$2; shift 2
  say "START $n"
  if nice -n 10 python3 -W error::FutureWarning "$m" "$@" >>$L 2>&1; then
    say "OK $n"; else say "FAIL $n"; echo "FAIL $n" >> $HOME/fx-data-logs/s234flag.fail; return 1; fi
}
say "volatility floor ON at q=0.05, causal (expanding percentile, one-bar lag)"
# ---- STAGE 2, flag on. The grid must be rebuilt: the trades change.
run "s2 grid"    code/nnfx2s.py --stage grid    || exit 1
run "s2 pick"    code/nnfx2s.py --stage pick    || exit 1
run "s2 paired"  code/nnfx2s.py --stage paired  || exit 1
run "s2 report"  code/nnfx2s.py --stage report  || exit 1
run "s2 costcap" code/nnfx2s.py --stage costcap
run "s2 fewer"   code/nnfx2s.py --stage fewer
run "s2 md"      code/nnfx2s.py --stage md
# ---- STAGE 3 and 4, flag on, all three bases
run "s3 zeroedge" code/nnfx3.py --stage zeroedge || exit 1
run "s3 walk"     code/nnfx3.py --stage walk     || exit 1
run "s3 report"   code/nnfx3.py --stage report   || exit 1
run "s4 preview"  code/nnfx3.py --stage stage4
run "s3 md"       code/nnfx3.py --stage md
say "DONE s234flag"
