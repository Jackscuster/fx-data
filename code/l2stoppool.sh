#!/bin/bash
# Stop a multiprocessing pool WITHOUT orphaning it.
#
# Killing the parent alone leaves its workers running, reparented to launchd,
# computing results that no longer have a consumer. That has now happened twice
# in this project: once when the trend drain watcher killed 95527 a minute after
# it had started a chop pool, leaving six workers burning 362% CPU for half an
# hour, and again when the mode A chop reverse pool was stopped. Children first,
# then the parent, then verify.
PARENT=$1
[ -z "$PARENT" ] && { echo "usage: l2stoppool.sh <parent-pid>"; exit 1; }
ps -p "$PARENT" >/dev/null 2>&1 || { echo "pool $PARENT already gone"; exit 0; }
KIDS=$(pgrep -P "$PARENT" | tr '\n' ' ')
echo "stopping pool $PARENT (children: $KIDS)"
# PARENT FIRST. multiprocessing.Pool REPOPULATES workers that die unexpectedly,
# so killing children first makes the parent spawn replacements -- and killing
# the parent afterwards orphans those replacements. Observed on mode C: nine
# fresh workers at 99% CPU with ppid=1, none of them the pids that had just
# been killed. Kill the parent, THEN the children it can no longer replace.
kill "$PARENT" 2>/dev/null
sleep 3
[ -n "$KIDS" ] && kill $KIDS 2>/dev/null
# and anything the pool respawned before the parent died
NEW=$(pgrep -P 1 -f multiprocessing.spawn 2>/dev/null | tr '\n' ' ')
sleep 3
LEFT=$(pgrep -P "$PARENT" 2>/dev/null | tr '\n' ' ')
for k in $KIDS $NEW; do ps -p "$k" >/dev/null 2>&1 && LEFT="$LEFT $k"; done
if [ -n "$(echo $LEFT | tr -d ' ')" ]; then
  echo "second pass on survivors: $LEFT"; kill -9 $LEFT 2>/dev/null; sleep 3
fi
echo "pool $PARENT stopped; stragglers: $(for k in $KIDS; do ps -p $k >/dev/null 2>&1 && echo -n "$k "; done)"
