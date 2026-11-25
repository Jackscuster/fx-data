#!/bin/bash
# RERUN EVERYTHING AT ACHIEVABLE SIZE. Jack, 25 Nov:
#   leverage cap ON  (open positions summed, 1:30, new entries SCALED to fit)
#   per-pair floor   5% causal (his decided rule 1)
#   peg guard        X = 0.33 PLACEHOLDER until he picks off the curve
# All robustness and crisis columns. A, B and C all continue.
# Does not touch chain_current: 22A owns it.
set -u
cd /Users/jackcuster/fx-data
export FX_COST_TABLE=$PWD/results/cost_table_h22.csv
L=$HOME/fx-data-logs/s234full.log
: > $L
say(){ echo "[$(date '+%H:%M:%S')] $*" | tee -a $L; }
run(){ local n=$1 m=$2; shift 2
  say "START $n"
  if nice -n 10 python3 -W error::FutureWarning "$m" "$@" >>$L 2>&1; then
    say "OK $n"; else say "FAIL $n"; echo "FAIL $n" >> $HOME/fx-data-logs/s234full.fail; return 1; fi
}
say "cap ON, floor 5% causal, peg guard X=0.33 PLACEHOLDER"
# ---- STAGE 1 R2 RANKING, flag + peg + cap on. kind/variant pairs matter.
for kd in c1 base; do
  for vr in jack textbook; do
    run "s1r2 $kd/$vr" code/nnfx1.py --stage run  --kind $kd --variant $vr || exit 1
    run "s1r2 walk $kd/$vr" code/nnfx1.py --stage walk --kind $kd --variant $vr
  done
done
run "s1r2 md"     code/nnfx1.py --stage mdr2
run "curves peg"     code/nnfxcurves.py --stage peg
run "curves buckets" code/nnfxcurves.py --stage buckets
run "s2 grid"     code/nnfx2s.py --stage grid    || exit 1
run "s2 pick"     code/nnfx2s.py --stage pick    || exit 1
run "s2 paired"   code/nnfx2s.py --stage paired  || exit 1
run "s2 report"   code/nnfx2s.py --stage report  || exit 1
run "s2 costcap"  code/nnfx2s.py --stage costcap
run "s2 fewer"    code/nnfx2s.py --stage fewer
run "s2 md"       code/nnfx2s.py --stage md
run "s3 zeroedge" code/nnfx3.py --stage zeroedge || exit 1
run "s3 walk"     code/nnfx3.py --stage walk     || exit 1
run "s3 report"   code/nnfx3.py --stage report   || exit 1
run "s4 preview"  code/nnfx3.py --stage stage4
run "curves floor"   code/nnfxcurves.py --stage floor
run "s3 md"       code/nnfx3.py --stage md
say "DONE s234full"
