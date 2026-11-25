#!/bin/bash
# STAGE 3 — a second confirmation added to Jack's carried-forward three.
# Runs BESIDE chain 22A. Measured: one nice'd process costs 22A +0.6% on its
# own s/strategy, far under Jack's 20% ceiling. DOES NOT TOUCH chain_current:
# chain 22A owns it and rewriting it is what killed stage 2's process group.
set -u
cd /Users/jackcuster/fx-data
export FX_COST_TABLE=$PWD/results/cost_table_h22.csv
L=$HOME/fx-data-logs/s3.log
: > $L
say(){ echo "[$(date '+%H:%M:%S')] $*" | tee -a $L; }
run(){ local n=$1; shift
  say "START $n"
  if nice -n 10 python3 -W error::FutureWarning code/nnfx3.py "$@" >>$L 2>&1; then
    say "OK s3 $n"
  else
    say "FAIL s3 $n"; echo "FAIL s3 $n" >> $HOME/fx-data-logs/s3.fail; return 1
  fi
}
say "stage 3 begins"
run ccy      --stage ccy      || exit 1
run zeroedge --stage zeroedge || exit 1   # gates everything below
run ledger   --stage ledger
run walk     --stage walk     || exit 1
run report   --stage report   || exit 1
run md       --stage md
say "DONE stage 3"
