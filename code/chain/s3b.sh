#!/bin/bash
# STAGE 3 report + md, re-run after the NaN control fix.
set -u
cd /Users/jackcuster/fx-data
export FX_COST_TABLE=$PWD/results/cost_table_h22.csv
L=$HOME/fx-data-logs/s3b.log
: > $L
say(){ echo "[$(date '+%H:%M:%S')] $*" | tee -a $L; }
run(){ local n=$1; shift
  say "START $n"
  if nice -n 10 python3 -W error::FutureWarning code/nnfx3.py "$@" >>$L 2>&1; then
    say "OK s3 $n"; else say "FAIL s3 $n"; return 1; fi
}
say "stage 3 report re-run on the fixed control"
run report --stage report || exit 1
run md     --stage md
say "DONE stage 3b"
