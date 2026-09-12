#!/bin/bash
# MEMORY GUARD: pause a process tree before the kernel panics.
#
#   bash code/l2memguard.sh <root pid> [pause_gb=3] [resume_gb=4] [poll_s=5] [max_pause_s=900]
#
# A PAUSE IS BOUNDED. On macOS a stopped process's pages go to the compressor,
# where they still count as used -- so once a big tree is paused, "available"
# cannot climb back on its own and the guard would wait forever. On 12 Sep the
# four-slice identity null sat paused from 16:13 to 17:26 that way. After
# max_pause_s without recovery the guard HALTS the stage (SIGTERM to the root,
# then SIGKILL) so the chain exits with its marker and can be relaunched with a
# smaller pool. A halt with a reason beats an hour of nothing.
#
# Watches available memory (free + inactive + speculative pages on macOS;
# MemAvailable on Linux). When it drops below pause_gb, every process under
# <root pid> gets SIGSTOP and the guard says so; when it climbs back above
# resume_gb they get SIGCONT. Exits when the root pid is gone.
#
# WHY. On 2026-09-11 23:33 and 2026-09-12 11:45 the Mac kernel-panicked --
# "watchdog timeout: no checkins from watchdogd in 94 seconds" -- because nine
# pool workers each paid a 6.9 GB transient at once and the compressor thrashed
# until userland could not check in. A paused stage costs minutes. A panic cost
# the run, twice. A stopped process holds its memory but stops allocating,
# which is what gives the compressor room to catch up and the operator time to
# see the message.
set -uo pipefail
ROOT="${1:?root pid}"; PAUSE_GB="${2:-3}"; RESUME_GB="${3:-4}"; POLL="${4:-5}"; MAX_PAUSE="${5:-900}"
avail_gb() {
  if [ -r /proc/meminfo ]; then
    awk '/MemAvailable/ {printf "%.2f", $2/1048576}' /proc/meminfo
  else
    vm_stat | awk -v ps="$(sysctl -n hw.pagesize)" '
      /Pages free/        {f=$3}  /Pages inactive/ {i=$3}  /Pages speculative/ {s=$3}
      END {gsub(/\./,"",f); gsub(/\./,"",i); gsub(/\./,"",s); printf "%.2f", (f+i+s)*ps/1073741824}'
  fi
}
tree() {  # every descendant of ROOT, deepest last
  local out=() q=("$ROOT")
  while [ ${#q[@]} -gt 0 ]; do
    local p="${q[0]}"; q=("${q[@]:1}")
    out+=("$p")
    for c in $(pgrep -P "$p" 2>/dev/null); do q+=("$c"); done  # NOSILENCE-OK: no children is the normal leaf case, not a failure
  done
  printf '%s\n' "${out[@]}"
}
paused=0; paused_at=0
while kill -0 "$ROOT" 2>/dev/null; do  # NOSILENCE-OK: kill -0 is the liveness probe; a dead root is the exit condition
  a=$(avail_gb)
  if [ "$paused" = 0 ] && awk -v a="$a" -v t="$PAUSE_GB" 'BEGIN{exit !(a<t)}'; then
    echo "$(date '+%F %T') MEMGUARD: available ${a} GB < ${PAUSE_GB} GB -- PAUSING tree under $ROOT"
    tree | xargs -n 50 kill -STOP 2>/dev/null  # NOSILENCE-OK: a child may exit between listing and signalling
    paused=1; paused_at=$(date +%s)
  elif [ "$paused" = 1 ] && [ $(( $(date +%s) - paused_at )) -ge "$MAX_PAUSE" ]; then
    echo "$(date '+%F %T') MEMGUARD: paused ${MAX_PAUSE}s and available is still ${a} GB -- HALTING the stage (relaunch with a smaller pool)"
    tree | xargs -n 50 kill -CONT 2>/dev/null  # NOSILENCE-OK: a child may exit between listing and signalling
    kill -TERM "$ROOT" 2>/dev/null; sleep 10  # NOSILENCE-OK: the root may already be gone
    tree | xargs -n 50 kill -KILL 2>/dev/null  # NOSILENCE-OK: whatever is left is meant to die
    paused=0
  elif [ "$paused" = 1 ] && awk -v a="$a" -v t="$RESUME_GB" 'BEGIN{exit !(a>t)}'; then
    echo "$(date '+%F %T') MEMGUARD: available ${a} GB > ${RESUME_GB} GB -- resuming"
    tree | xargs -n 50 kill -CONT 2>/dev/null  # NOSILENCE-OK: a child may exit between listing and signalling
    paused=0
  fi
  sleep "$POLL"
done
[ "$paused" = 1 ] && echo "$(date '+%F %T') MEMGUARD: root gone while paused"
echo "$(date '+%F %T') MEMGUARD: root $ROOT exited, guard done"
