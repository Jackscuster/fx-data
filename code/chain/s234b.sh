#!/bin/bash
# RESUME + CLOSE THE GAPS. Jack, 25 Nov, items 1-5.
#   leverage cap ON  (open positions summed, 1:30, entries SCALED to fit)
#   per-pair floor   5% causal (decided rule 1)
#   peg guard        X = 0.33 PLACEHOLDER until he picks off the curve
#
# Why this re-runs stage 1 rather than resuming at s3 zeroedge:
#   1. the nulls needed a null_cost column before condition 4 could restate
#      a null gross honestly (leg-vs-entry, see nnfxcond)
#   2. the flip_only plans were never put on the standing-rules basis
#   3. item 3 wants the floor curve over the stage 1 C1 RANKING, which needs
#      the whole ranking re-run at each of the six levels
# Does not touch chain_current: 22A owns it.
set -u
cd /Users/jackcuster/fx-data
export FX_COST_TABLE=$PWD/results/cost_table_h22.csv
L=$HOME/fx-data-logs/s234b.log
: > $L
say(){ echo "[$(date '+%H:%M:%S')] $*" | tee -a $L; }
run(){ local n=$1 m=$2; shift 2
  say "START $n"
  if nice -n 10 python3 -W error::FutureWarning "$m" "$@" >>$L 2>&1; then
    say "OK $n"; else say "FAIL $n"; echo "FAIL $n" >> $HOME/fx-data-logs/s234b.fail; return 1; fi
}
say "cap ON, floor 5% causal, peg X=0.33 PLACEHOLDER"

# ---- 1. STAGE 1 R2 RANKING, all six labels, nulls now carrying null_cost
for kv in "c1 jack" "c1 textbook" "base jack" "base textbook" "c1 flip_only" "base flip_only"; do
  set -- $kv
  run "s1r2 $1/$2"      code/nnfx1.py --stage run  --kind $1 --variant $2 || exit 1
  run "s1r2 walk $1/$2" code/nnfx1.py --stage walk --kind $1 --variant $2 || exit 1
done
run "s1r2 md" code/nnfx1.py --stage mdr2

# ---- 2. STAGE 3 and 4, with the zero-edge harness fixed to carry the floor
run "s3 zeroedge" code/nnfx3.py --stage zeroedge || exit 1
run "s3 walk"     code/nnfx3.py --stage walk     || exit 1
run "s3 report"   code/nnfx3.py --stage report   || exit 1
run "s4 preview"  code/nnfx3.py --stage stage4

# ---- 3. THE CURVES. floor (A/B/C, exact removed-vs-kept) before the long one.
run "curves floor" code/nnfxcurves.py --stage floor

# ---- 4. ITEM 3's REMAINING PART: the floor curve over the stage 1 C1 ranking.
#        Six levels x two plans, into results/nnfx_floor/ so condition 4's glob
#        does not mix six rules into one zero-edge aggregate.
for v in jack textbook; do
  for qt in "0 qoff" "0.01 q1" "0.025 q2p5" "0.05 q5" "0.075 q7p5" "0.10 q10"; do
    set -- $qt
    run "s1 floor $v $2" code/nnfx1.py --stage run --kind c1 --variant $v \
        --lowvol-q $1 --peg-x 0.33 --tag _$2 --outdir results/nnfx_floor
  done
done
run "curves floor1" code/nnfxcurves.py --stage floor1

# ---- 5. THE REPORT LAST, so it reads finished files
run "s3 md" code/nnfx3.py --stage md
say "DONE s234b"
