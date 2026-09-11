#!/bin/bash
# v3 -> open-floor pass -> the cut. Runs unattended after v3 finishes.
cd "$(dirname "$0")/.."
LOG=results/ftchain.log
say(){ echo "$(date '+%F %T') $*" | tee -a "$LOG"; }
say "armed; waiting for v3 (5135 strategies)"
while true; do
  n=$(/usr/bin/python3 -c "
import pandas as pd,glob
fs=glob.glob('results/gate3ft_costed_v3/*.csv')
print(sum(len(pd.read_csv(f,low_memory=False)) for f in fs) if fs else 0)" 2>/dev/null)  # NOSILENCE-OK: counting rows in files that may not exist yet
  [ "${n:-0}" -ge 5135 ] && { say "v3 complete: $n"; break; }
  pgrep -f "l2gate3ft.py --shard" >/dev/null || { say "v3 shards gone at $n rows"; break; }
  sleep 300
done
say "launching OPEN-FLOOR pass on v3's FLOOR_LIMITED strategies"
for i in $(seq 0 8); do
  FT_COSTED=1 FT_OPEN=1 FT_BANK=gate3ft_costed_v3_open \
    nohup nice -n 19 /usr/bin/python3 code/l2gate3ft.py --shard $i --shards 9 --no-pace-check \
    > results/gate3ftopen_s$i.log 2>&1 &
done
sleep 30
while pgrep -f "l2gate3ft.py --shard" >/dev/null; do sleep 300; done
say "open-floor pass done"
say "MERGE + CUT next (l2gate3 on the merged fine-tuned population)"
