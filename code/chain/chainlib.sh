#!/bin/bash
# THE SHARED CHAIN LIBRARY (Jack, 17 Nov). Sourced by every driver:
#     . ~/fx-data-logs/chainlib.sh "$0" "<final marker>"
#
# WHAT IT GIVES A DRIVER
#   say   timestamped line to the log and to stdout
#   g     run one stage: memory-guarded, dependency-aware, NON-FATAL
#   ci    commit and push with the standard attribution
#   chain_summary   the stage ledger, printed before the final marker
#
# THE TWO RULES IT ENFORCES
#   1. THE FIVE-MINUTE RULE lives in code/l2ckpt.py and is checked before launch
#      by code/l2stagecheck.py chain, which launch.sh calls.
#   2. A FAILED STAGE DOES NOT STOP THE CHAIN. Until 17 Nov a halted assert
#      ended everything and nothing ran until Jack noticed -- 10.5 hours one
#      night. Now `g` records the failure and RETURNS 0; only stages that
#      DECLARE a dependency on the failed stage are skipped. Dependencies are
#      declared in the driver itself, one line per stage:
#          # needs <stage> = <dep>[,<dep>...]      or      = none
#      so the declaration and the behaviour cannot drift apart: `g` reads the
#      driver's own lines rather than taking an argument that could disagree.
set -uo pipefail
DRIVER_PATH="${1:?chainlib: pass \"\$0\"}"
FINAL_MARKER="${2:?chainlib: pass the final marker}"
L="$HOME/fx-data-logs/batch1.log"
LEDGER="$HOME/fx-data-logs/.chain_ledger_$$"
: > "$LEDGER"

say(){ echo "$(date '+%F %T') $*" | tee -a "$L"; }

# FREE SPACE AT EVERY MARKER (Jack, 20 Nov). An external drive is coming; until
# it does, the volume is the binding constraint and the number has to be in the
# log beside each stage rather than reconstructed afterwards. A stage that dies
# on OSError 28 is otherwise indistinguishable from one that died on its own.
freegb(){ df -g /System/Volumes/Data 2>/dev/null | tail -1 | awk '{print $4}'; }

# STAGE NAMES CONTAIN SPACES ("g2 full A"), so the dependency list is split on
# COMMAS, never on whitespace. Splitting on whitespace turned "t bad" into "t"
# and "bad" and silently matched neither, so a dependent stage ran after its
# dependency had failed -- found by the probe, not in production.
needs_of(){
  grep -E "^#[[:space:]]*needs[[:space:]]+$1[[:space:]]*=" "$DRIVER_PATH" 2>/dev/null \
    | head -1 | sed 's/.*=[[:space:]]*//' | sed 's/[[:space:]]*#.*//'
}

ledger_has(){ grep -qxF "$1" "$LEDGER" 2>/dev/null; }

g(){
  local n="$1"; shift
  local deps blocked d
  deps=$(needs_of "$n")
  blocked=""
  local oldifs="$IFS"
  IFS=','
  for d in $deps; do
    IFS="$oldifs"
    d=$(echo "$d" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')
    [ -z "$d" ] && { IFS=','; continue; }
    [ "$d" = "none" ] && { IFS=','; continue; }
    if ledger_has "FAILED $d" || ledger_has "SKIPPED $d"; then blocked="$d"; break; fi
    IFS=','
  done
  IFS="$oldifs"
  if [ -n "$blocked" ]; then
    echo "SKIPPED $n" >> "$LEDGER"
    say "SKIP $n -- it declares a dependency on \"$blocked\", which did not succeed"
    return 0
  fi
  local t0 py gd
  t0=$(date +%s)
  "$@" >> "$L" 2>&1 & py=$!
  bash /Users/jackcuster/fx-data/code/l2memguard.sh $py 2 3 5 3600 >> "$L" 2>&1 & gd=$!
  if ! wait $py; then
    wait $gd
    echo "FAILED $n" >> "$LEDGER"
    # NON-FATAL BY DESIGN. The ledger carries the failure; independent stages
    # keep running; dependents are skipped above with their reason named.
    say "!!! $n FAILED after $(( ($(date +%s)-t0)/60 )) min $(( ($(date +%s)-t0)%60 )) s -- recorded; independent stages continue [$(freegb) GB free]"
    return 0
  fi
  wait $gd
  echo "OK $n" >> "$LEDGER"
  say "$n done in $(( ($(date +%s)-t0)/60 )) min $(( ($(date +%s)-t0)%60 )) s [$(freegb) GB free]"
  return 0
}

# LOCAL-ONLY MODE (Jack, 24 Nov). With FX_CI_LOCAL=1 a stage COMMITS and does
# not pull or push. It exists because a batched push of rewritten history was
# still landing and chunk 1's stages only read LOCAL banks -- there is no reason
# for a read to wait on a slow remote. One push follows once the batcher lands.
# The default is unchanged: commit, pull --rebase, push.
ci(){
  cd /Users/jackcuster/fx-data
  git add -A code/ results/ HANDOFF.md .gitignore app_data.json app_ui.js >/dev/null 2>&1
  git commit -q -m "$1

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_016fb2CjHx3RvfiWm6g7bVgc" >/dev/null 2>&1 || echo 'nothing to commit' >> "$L"
  if [ "${FX_CI_LOCAL:-0}" = "1" ]; then
    say "committed LOCAL-ONLY: $(git log --oneline -1) [$(freegb) GB free]"
    return 0
  fi
  git pull -q --rebase origin main >> "$L" 2>&1
  git push -q origin main 2>&1 | grep -v 'GH001\|warning:' >> "$L"
  say "committed: $(git log --oneline -1) [$(freegb) GB free]"
}

stage_failed(){ ledger_has "FAILED $1"; }
any_failed(){ grep -q "^FAILED " "$LEDGER" 2>/dev/null; }

chain_summary(){
  local ok fa sk
  # grep -c prints 0 AND exits 1 when nothing matches, so `|| echo 0` appended a
  # second zero and the summary read "1 failed, 0\n0 skipped".
  ok=$(grep -c "^OK " "$LEDGER" 2>/dev/null | head -1); ok=${ok:-0}
  fa=$(grep -c "^FAILED " "$LEDGER" 2>/dev/null | head -1); fa=${fa:-0}
  sk=$(grep -c "^SKIPPED " "$LEDGER" 2>/dev/null | head -1); sk=${sk:-0}
  say "STAGE LEDGER: $ok succeeded, $fa failed, $sk skipped [$(freegb) GB free]"
  grep -E "^(FAILED|SKIPPED) " "$LEDGER" 2>/dev/null | while read -r line; do say "   $line"; done
  cp "$LEDGER" "$HOME/fx-data-logs/chain_ledger_last.txt" 2>/dev/null
}
