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

# pgrep -f takes an ERE, so alternation is `a|b` -- NOT `a\|b`. The escaped
# form matched nothing, the script reported success, and eight workers survived
# reparented to init and still writing shards. Found the hard way; the whole
# point of this script is that this cannot happen quietly.
#
# The children are also not reliably identifiable by command line: macOS spawns
# them as bare `python3 -c from multiprocessing...`, and after the parent dies
# their PPID is 1, so neither the pattern nor the process tree finds them on its
# own. Match on the interpreter running a multiprocessing bootstrap, then verify
# nothing is left rather than trusting the match.
PARENTS=$(pgrep -f 'l2sweep\.py' || true)
KIDS=$(pgrep -f 'multiprocessing' || true)

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
  LEFT=$(pgrep -f 'l2sweep\.py|multiprocessing' || true)
  [ -z "$LEFT" ] && break
  i=$((i + 1))
done

LEFT=$(pgrep -f 'l2sweep\.py|multiprocessing' || true)
if [ -n "$LEFT" ]; then
  echo "still alive after 10s, sending KILL: $LEFT"
  kill -9 $LEFT 2>/dev/null
  sleep 2
fi

# VERIFY, do not assume. A stop script that reports success while workers keep
# writing is worse than no stop script, because the next launch then mixes two
# configurations in one output directory.
LEFT=$(pgrep -f 'l2sweep\.py|multiprocessing' || true)
if [ -n "$LEFT" ]; then
  echo "FAILED: still running after KILL: $LEFT"
  exit 1
fi

echo "gate 1: stopped, verified none left. $(ls results/gate1/shard_*.csv 2>/dev/null | wc -l | tr -d ' ') shards banked."
