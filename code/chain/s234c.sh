#!/bin/bash
# RUNS AFTER s234b. Two things s234b cannot do:
#   1. re-run the ATR buckets, which now carry ex-SNB columns. Without them
#      the bucket table says "the profit is concentrated in low-volatility
#      entries" when what it is actually saying is "ONE low-volatility trade
#      IS the profit" -- bucket 1 totals ~79.5 R and the EURCHF short through
#      the SNB peg break is +74.996 of it.
#   2. regenerate STAGE3.md afterwards, so the report reads the new buckets.
# Separate script on purpose: bash reads a script incrementally as it runs, so
# editing s234b.sh while it was executing could have corrupted it.
set -u
cd /Users/jackcuster/fx-data
export FX_COST_TABLE=$PWD/results/cost_table_h22.csv
L=$HOME/fx-data-logs/s234c.log
: > $L
say(){ echo "[$(date '+%H:%M:%S')] $*" | tee -a $L; }
run(){ local n=$1 m=$2; shift 2
  say "START $n"
  if nice -n 10 python3 -W error::FutureWarning "$m" "$@" >>$L 2>&1; then
    say "OK $n"; else say "FAIL $n"; echo "FAIL $n" >> $HOME/fx-data-logs/s234c.fail; return 1; fi
}
run "curves buckets" code/nnfxcurves.py --stage buckets || exit 1
run "curves floor1"  code/nnfxcurves.py --stage floor1
run "s3 md"          code/nnfx3.py --stage md || exit 1
run "s2 md"          code/nnfx2s.py --stage md
run "app"            code/r2app.py --stage app
say "DONE s234c"
