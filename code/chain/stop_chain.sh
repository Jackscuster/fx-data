#!/bin/bash
# GUARD 2 -- THE ONLY SANCTIONED WAY TO STOP A CHAIN.
#   bash code/chain/stop_chain.sh [pgid]
#
# WHY. On 17 Nov `pkill -f l2r2f.sh` killed a chain's parent and left its six
# pool workers running; one burned a full core and 741 MB for 89 minutes against
# the live run, and its death tracebacks in the shared log read like a crash in
# the new chain. Killing a process GROUP cannot leave an orphan.
#
# Every chain is launched as its own process-group leader by launch.sh, which
# records the pgid in ~/fx-data-logs/chain_current. This kills that group and
# then VERIFIES zero survivors, refusing to report success otherwise.
set -u
L="$HOME/fx-data-logs"
PG="${1:-}"
if [ -z "$PG" ]; then
  [ -f "$L/chain_current" ] || { echo "stop_chain: no chain registered"; exit 2; }
  . "$L/chain_current"
  PG="${CHAIN_PGID:-}"
  [ -n "$PG" ] || { echo "stop_chain: the registered chain has no pgid (launched before guard 2?)"; exit 2; }
fi
echo "stop_chain: stopping process group $PG"
kill -TERM -"$PG" 2>/dev/null
for i in $(seq 1 20); do
  sleep 1
  n=$(pgrep -g "$PG" 2>/dev/null | wc -l | tr -d ' ')
  [ "$n" = "0" ] && break
done
n=$(pgrep -g "$PG" 2>/dev/null | wc -l | tr -d ' ')
if [ "$n" != "0" ]; then
  echo "stop_chain: $n survived SIGTERM, sending SIGKILL to the group"
  kill -KILL -"$PG" 2>/dev/null; sleep 2
fi
n=$(pgrep -g "$PG" 2>/dev/null | wc -l | tr -d ' ')
if [ "$n" != "0" ]; then
  echo "stop_chain: FAILED -- $n processes still in group $PG:"; pgrep -lg "$PG" | head
  exit 1
fi
echo "stop_chain: group $PG stopped, ZERO survivors verified"
mv "$L/chain_current" "$L/chain_stopped" 2>/dev/null
exit 0
