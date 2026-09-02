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
[ -n "$KIDS" ] && kill $KIDS 2>/dev/null
sleep 5
kill "$PARENT" 2>/dev/null
sleep 5
LEFT=$(pgrep -P "$PARENT" 2>/dev/null | tr '\n' ' ')
for k in $KIDS; do ps -p "$k" >/dev/null 2>&1 && LEFT="$LEFT $k"; done
if [ -n "$(echo $LEFT | tr -d ' ')" ]; then
  echo "second pass on survivors: $LEFT"; kill -9 $LEFT 2>/dev/null; sleep 3
fi
echo "pool $PARENT stopped; stragglers: $(for k in $KIDS; do ps -p $k >/dev/null 2>&1 && echo -n "$k "; done)"
