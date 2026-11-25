#!/bin/bash
# ITEM 1, Jack 25 Nov: realistic gap fills, measured before and after on A, B
# and C over all 28 pairs, plus the stop-out deciles. One core per cell is not
# worth it -- the whole thing is ~15 min single-threaded and chain 22A has just
# finished, so nothing is competing for the machine.
cd "$(dirname "$0")/../.." || exit 1
LOG=results/chainlogs/gap1.log
say(){ echo "[$(date +%H:%M:%S)] $*" | tee -a $LOG; }
say "START gap1 (item 1: realistic gap fills)"
say "START snb long"
python3 code/nnfxgap.py --stage snb >>$LOG 2>&1 && say "OK snb long" || { say "FAIL snb long"; exit 1; }
say "START effect + deciles, 28 pairs, 6 cells, gap fills off then on"
python3 code/nnfxgap.py --stage effect >>$LOG 2>&1 && say "OK effect + deciles" || { say "FAIL effect"; exit 1; }
say "DONE gap1"
