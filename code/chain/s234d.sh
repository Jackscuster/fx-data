#!/bin/bash
# THE UNIT FIX. A trade frame carries two R columns -- `R`, the engine's raw r,
# and `R_gross`, that restated to the declared 1.5-ATR notional -- and three
# reported paths were summing the raw one:
#   nnfxvol.robust_cols   best_trade_R / R_ex_best_trade / R_crisis / R_ex_crisis
#   nnfxvol.atr_buckets   every R column in the bucket table
#   nnfxcurves._entry_R   the floor curve's removed-versus-kept means
# Each used the raw column on both sides of its own ratio, so every SHARE was
# right and only the absolute numbers were 1.5x too large and gross of cost.
# Everything below is a table that carried one of those numbers.
set -u
cd /Users/jackcuster/fx-data
export FX_COST_TABLE=$PWD/results/cost_table_h22.csv
L=$HOME/fx-data-logs/s234d.log
: > $L
say(){ echo "[$(date '+%H:%M:%S')] $*" | tee -a $L; }
run(){ local n=$1 m=$2; shift 2
  say "START $n"
  if nice -n 10 python3 -W error::FutureWarning "$m" "$@" >>$L 2>&1; then
    say "OK $n"; else say "FAIL $n"; echo "FAIL $n" >> $HOME/fx-data-logs/s234d.fail; return 1; fi
}
run "curves buckets" code/nnfxcurves.py --stage buckets || exit 1
run "curves floor"   code/nnfxcurves.py --stage floor   || exit 1
run "curves peg"     code/nnfxcurves.py --stage peg     || exit 1
run "s2 report"      code/nnfx2s.py --stage report      || exit 1
run "s2 costcap"     code/nnfx2s.py --stage costcap
run "s2 fewer"       code/nnfx2s.py --stage fewer
run "s3 report"      code/nnfx3.py --stage report       || exit 1
run "s4 preview"     code/nnfx3.py --stage stage4
run "s2 md"          code/nnfx2s.py --stage md
run "s3 md"          code/nnfx3.py --stage md
run "app"            code/r2app.py --stage app
say "DONE s234d"
