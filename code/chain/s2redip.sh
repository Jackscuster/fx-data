#!/bin/bash
# RECOMPUTE THE PATH-DEPENDENT HALF OF STAGE 2 ON THE FIXED ENGINE.
# Jack's check 1: worst_dip_R was wrong wherever plan=2 is used, because
# nnfx1.daily_series built each leg's mark from the FULL position size.
# Unaffected and NOT recomputed: grid, pool, pick (tune-year trade-level
# selection) and rolling (per-year R from the walk). Recomputed: paired (block
# bootstrap on the daily difference), report (2c + the prop simulator),
# costcap, fewer, then the report itself.
#
# THIS DELIBERATELY DOES NOT TOUCH chain_current. Chain 22A owns it, and
# rewriting it is what killed stage 2's own process group earlier today.
set -u
cd /Users/jackcuster/fx-data
export FX_COST_TABLE=$PWD/results/cost_table_h22.csv
L=$HOME/fx-data-logs/s2redip.log
: > $L
say(){ echo "[$(date '+%H:%M:%S')] $*" | tee -a $L; }
run(){ # run <name> <args...>
  local n=$1; shift
  say "START $n"
  if nice -n 10 python3 -W error::FutureWarning code/nnfx2s.py "$@" >>$L 2>&1; then
    say "OK $n"
  else
    say "FAIL $n"; echo "FAIL $n" >> $HOME/fx-data-logs/s2redip.fail
  fi
}
say "engine fix: nnfx1.daily_series now weights each leg by units/n_legs"
run paired   --stage paired
run report   --stage report
run costcap  --stage costcap
run fewer    --stage fewer
run md       --stage md
say "DONE"
