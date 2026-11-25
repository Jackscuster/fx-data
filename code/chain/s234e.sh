#!/bin/bash
# RUNS AFTER s234d. Three things s234d could not carry:
#   1. curves buckets again -- stage_buckets now also writes snb_trade_value.csv,
#      the one trade's R in BOTH units (raw r and the reported 1.5-ATR unit) at
#      BOTH sizes (uncapped and capped). It was quoted at +74.996 R for two days;
#      that is the raw column, and nobody should have to derive the real figure
#      twice.
#   2. dipcheck --stage snb. dipcheck_snb_by_pair.csv says EURCHF made +99.24 R
#      on 15 Jan 2015 and sums to +101.618 -- the pre-guard-36 doubled figure.
#      The current engine gives +49.87 for EURCHF alone and +51.29 for the whole
#      book that day, and dipcheck_snb_dependence.csv (same script, same run)
#      already agrees with that. The by-pair file is stale and STAGE3.md quotes
#      it, so it is rewritten rather than annotated.
#   3. the report and the app again, so both read the new files.
set -u
cd /Users/jackcuster/fx-data
export FX_COST_TABLE=$PWD/results/cost_table_h22.csv
L=$HOME/fx-data-logs/s234e.log
: > $L
say(){ echo "[$(date '+%H:%M:%S')] $*" | tee -a $L; }
run(){ local n=$1 m=$2; shift 2
  say "START $n"
  if nice -n 10 python3 -W error::FutureWarning "$m" "$@" >>$L 2>&1; then
    say "OK $n"; else say "FAIL $n"; echo "FAIL $n" >> $HOME/fx-data-logs/s234e.fail; return 1; fi
}
run "curves buckets" code/nnfxcurves.py --stage buckets || exit 1
run "dipcheck snb"   code/dipcheck.py   --stage snb     || exit 1
run "s3 md"          code/nnfx3.py      --stage md      || exit 1
run "app"            code/r2app.py      --stage app
say "DONE s234e"
