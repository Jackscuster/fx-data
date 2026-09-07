#!/bin/bash
# SWAP GUARD for the gate 3 fine-tune shards.
#
# The earlier guard only ever protected mode C's pools and exited when they did
# (results/swapguard.log, 2026-09-06 22:43), leaving the nine shards unguarded.
# This one watches the shards themselves.
#
# HYSTERESIS, deliberately wide. Stop a shard below LOW, and do not bring one
# back until swap free is above HIGH. A single threshold would oscillate: the
# shard is killed, swap recovers by exactly the amount the shard was using, the
# shard restarts, and the machine thrashes on a loop.
#
# A stopped shard costs nothing but throughput. Banking is per strategy, so its
# finished work is on disk and its in-flight strategy is the only loss; the
# restart re-reads the bank and skips everything already done.
LOW=${1:-400}; HIGH=${2:-700}
LOG=/Users/jackcuster/Documents/fx-data/results/ftguard.log
cd /Users/jackcuster/Documents/fx-data
# SINGLE INSTANCE without flock, which macOS does not ship. Count our own
# siblings by name; if another is already running, exit quietly.
me=$$
others=$(pgrep -f "l2ftguard.sh" | grep -v "^${me}$" | wc -l | tr -d ' ')
[ "$others" -gt 0 ] && exit 0
say(){ echo "$(date '+%F %T') $*" >> "$LOG"; }
say "armed: low=${LOW}M high=${HIGH}M"
stopped=""
while true; do
  free=$(sysctl -n vm.swapusage | sed 's/.*free = \([0-9.]*\)M.*/\1/'); free=${free%%.*}
  live=$(pgrep -f "l2gate3ft.py --shard" | wc -l | tr -d ' ')
  [ "$live" -eq 0 ] && [ -z "$stopped" ] && { say "no shards left; standing down"; exit 0; }
  if [ "${free:-9999}" -lt "$LOW" ] && [ "$live" -gt 1 ]; then
    # stop the highest-numbered shard, parent first so nothing is orphaned
    victim=$(pgrep -f "l2gate3ft.py --shard" | tail -1)
    sh=$(ps -o command= -p "$victim" | sed -n 's/.*--shard \([0-9]*\).*/\1/p')
    say "swap free ${free}M < ${LOW}M -- stopping shard $sh (pid $victim)"
    kill "$victim" 2>/dev/null; sleep 3
    for k in $(pgrep -P "$victim" 2>/dev/null); do kill "$k" 2>/dev/null; done
    sleep 2
    ps -p "$victim" >/dev/null 2>&1 && kill -9 "$victim" 2>/dev/null
    stopped="$stopped $sh"
    say "stopped shards:$stopped ; live now $(pgrep -f 'l2gate3ft.py --shard' | wc -l | tr -d ' ')"
  elif [ "${free:-0}" -gt "$HIGH" ] && [ -n "$stopped" ]; then
    sh=$(echo $stopped | awk '{print $1}')
    stopped=$(echo $stopped | cut -s -d' ' -f2-)
    say "swap free ${free}M > ${HIGH}M -- restarting shard $sh (resumes from bank)"
    FT_COSTED=1 FT_BANK=gate3ft_costed_v4 nohup nice -n 19 /usr/bin/python3 \
      code/l2gate3ft.py --shard "$sh" --shards 9 --no-pace-check \
      >> results/gate3ftv4_s$sh.log 2>&1 &
  fi
  sleep 60
done
