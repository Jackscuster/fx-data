#!/bin/sh
# Stop a running gate 1 sweep.
#
# Children FIRST. Python multiprocessing spawns workers whose command line is
# the multiprocessing bootstrap, not l2sweep.py, so `pkill -f l2sweep` kills
# only the parent and leaves the pool alive -- still writing shard files, under
# the OLD shard count if the run is then relaunched with a different one. That
# silently mixes two shard schemes in results/gate1 and the checkpoints stop
# meaning anything. It happened twice during the first launch.
set -u

PARENTS=$(pgrep -f 'l2sweep.py' || true)
KIDS=$(pgrep -f 'multiprocessing.spawn_main\|multiprocessing.resource_tracker' || true)

if [ -z "$PARENTS$KIDS" ]; then
  echo "gate 1: nothing running"
  exit 0
fi

[ -n "$KIDS" ]    && echo "killing workers: $KIDS"  && kill $KIDS 2>/dev/null
[ -n "$PARENTS" ] && echo "killing parent:  $PARENTS" && kill $PARENTS 2>/dev/null

# give them a moment, then confirm
i=0
while [ $i -lt 10 ]; do
  sleep 1
  LEFT=$(pgrep -f 'l2sweep.py\|multiprocessing.spawn_main' || true)
  [ -z "$LEFT" ] && break
  i=$((i + 1))
done

LEFT=$(pgrep -f 'l2sweep.py\|multiprocessing.spawn_main' || true)
if [ -n "$LEFT" ]; then
  echo "still alive after 10s, sending KILL: $LEFT"
  kill -9 $LEFT 2>/dev/null
  sleep 1
fi

echo "gate 1: stopped. $(ls results/gate1/shard_*.csv 2>/dev/null | wc -l | tr -d ' ') shards banked."
