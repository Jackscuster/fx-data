#!/bin/bash
# THE FULL QUEUE, armed against the fine-tune's completion.
#   re-judge all banked rows W3-only -> gate 3 cut on ADOPTED settings ->
#   team builder (both teams) -> selection holdout + random-team null ->
#   agreement study -> mode C relaunch + swap guard
#
# Single instance via a pidfile. macOS has no flock, and matching our own name
# with pgrep also matches the nohup wrapper -- that mistake left an earlier
# guard exiting immediately while reporting success.
PIDF=/tmp/.l2chain2.pid
if [ -f "$PIDF" ] && kill -0 "$(cat "$PIDF" 2>/dev/null)" 2>/dev/null; then exit 0; fi  # NOSILENCE-OK: the process may already be gone, which is the goal, not a failure
echo $$ > "$PIDF"; trap 'rm -f "$PIDF"' EXIT
cd /Users/jackcuster/Documents/fx-data
LOG=results/chain2.log
say(){ echo "$(date '+%F %T') $*" >> "$LOG"; }
# EVERY STAGE MUST PROVE IT PRODUCED SOMETHING. A stage that exits zero having
# read a stale file, found no roster, or produced an empty frame has happened
# three times in this chain. check() verifies the OUTPUT -- exists, non-empty,
# minimum rows, and written DURING this stage -- and halts the whole chain on
# failure rather than carrying on with nothing.
check(){
  local stage="$1"; shift
  if ! /usr/bin/python3 code/l2stagecheck.py "$stage" "$@" >> "$LOG" 2>&1; then
    say "!!! CHAIN HALTED at $stage -- see results/CHAIN_HALT.marker"
    exit 1
  fi
}
rm -f results/CHAIN_HALT.marker
say "armed: waiting for the gate 3 fine-tune to bank ALL 5,135"
# WAIT FOR THE BANK, NOT FOR THE SHARDS. The previous condition was "no shards
# running", and a shard that DIED satisfied it: shard 5 fell over on a transient
# EmptyDataError at 96.2%, the chain read the absence of shards as completion,
# and everything downstream ran on a bank missing 194 strategies. Absence of a
# worker is not evidence of finished work.
while true; do
  n=$(/usr/bin/python3 - <<'PYX'
import glob,sys,pandas as pd
# COUNT THE UNREADABLE, NEVER SWALLOW THEM. Eight shards append to these files
# continuously so a read can land mid-write, which is why the try exists -- but
# a file that is unreadable on EVERY pass is a dead shard, and swallowing that
# is how a 96.2%-complete bank read as finished on 2026-09-10.
fs=glob.glob('results/gate3ft_costed_v4/*.csv')
s=set(); bad=0
for f in fs:
    try:
        s|=set(pd.read_csv(f,usecols=['sid'],low_memory=False).sid)
    except Exception as e:
        bad+=1
        print('  bank file unreadable this pass: %s: %s' % (f, str(e)[:60]),
              file=sys.stderr)
if bad:
    print('  WARNING %d of %d bank files unreadable this pass' % (bad, len(fs)),
          file=sys.stderr)
print(len(s))
PYX
)
  [ "${n:-0}" -ge 5135 ] && { say "bank complete: $n/5135"; break; }
  if ! pgrep -f "l2gate3ft.py --shard" >/dev/null; then
    say "WARNING no shards running but bank holds only ${n:-0}/5135 -- waiting"
  fi
  sleep 300
done
say "fine-tune finished"
say "1/5 re-judging every banked row on the W3-only basis"
T0=$(date +%s); nice -n 19 /usr/bin/python3 code/l2readopt.py >> "$LOG" 2>&1 || { say "!!! readopt FAILED"; exit 1; }
check readopt --since "$T0"
say "2/5 W3-only re-score, then the CUT on adopted settings"
T0=$(date +%s); nice -n 19 /usr/bin/python3 code/l2clean3.py >> "$LOG" 2>&1 || { say "!!! clean3 FAILED"; exit 1; }
T0=$(date +%s); nice -n 19 /usr/bin/python3 code/l2cut.py --settings adopted >> "$LOG" 2>&1 || { say "!!! cut FAILED"; exit 1; }
check cut --since "$T0"
say "3/5 team builder, both teams"
T0=$(date +%s)
TEAM_LABEL=_W3ONLY_ADOPTED TEAM_JOBS=9 nice -n 19 /usr/bin/python3 code/l2team.py >> "$LOG" 2>&1 || { say "!!! team FAILED"; exit 1; }
check team --label _W3ONLY_ADOPTED --since "$T0"
T0=$(date +%s)
TEAM_JOBS=9 nice -n 19 /usr/bin/python3 code/l2teamkpi.py --label _W3ONLY_ADOPTED >> "$LOG" 2>&1 || { say "!!! kpi FAILED"; exit 1; }
check teamkpi --label _W3ONLY_ADOPTED --since "$T0"
say "4/5 agreement study"
T0=$(date +%s)
TEAM_LABEL=_W3ONLY_ADOPTED nice -n 19 /usr/bin/python3 code/l2agree.py >> "$LOG" 2>&1 || { say "!!! agree FAILED"; exit 1; }
check agree --since "$T0"
/usr/bin/python3 code/appstamp.py >> "$LOG" 2>&1
git add -A
  if git diff --cached --quiet; then
    say "nothing new to commit"
  else
    git commit -m "Gate 3 adopted-settings cut, teams, checks and agreement study"
  fi
if ! git pull --rebase origin main; then say "pull failed (reported, not hidden)"; fi
  if ! git push origin main; then say "PUSH FAILED -- results are local only"; fi
# The B-trend ip1 recovery is NOT run here. At 216 s per strategy it is ~70 h
# on this machine and would hold mode C hostage for three days. It is packaged
# for a rented box instead -- see code/cloud_ip1.sh.
# MODE C IS NOT RELAUNCHED HERE. It stays paused until the full system is built
# and forward testing has started. Restart it deliberately, not as a side effect
# of a build finishing.
say "5/5 selection holdout + random-team null, ALL free cores"
T0=$(date +%s)
TEAM_JOBS=9 nice -n 19 /usr/bin/python3 code/l2teamcheck.py --label _W3ONLY_ADOPTED \
      >> results/teamcheck_adopted.log 2>&1 || { say "!!! checks FAILED"; exit 1; }
check checks --label _W3ONLY_ADOPTED --since "$T0"
say "checks done"
say "CHAIN COMPLETE"
