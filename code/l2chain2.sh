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
if [ -f "$PIDF" ] && kill -0 "$(cat "$PIDF" 2>/dev/null)" 2>/dev/null; then exit 0; fi
echo $$ > "$PIDF"; trap 'rm -f "$PIDF"' EXIT
cd /Users/jackcuster/Documents/fx-data
LOG=results/chain2.log
say(){ echo "$(date '+%F %T') $*" >> "$LOG"; }
say "armed: waiting for the gate 3 fine-tune to bank ALL 5,135"
# WAIT FOR THE BANK, NOT FOR THE SHARDS. The previous condition was "no shards
# running", and a shard that DIED satisfied it: shard 5 fell over on a transient
# EmptyDataError at 96.2%, the chain read the absence of shards as completion,
# and everything downstream ran on a bank missing 194 strategies. Absence of a
# worker is not evidence of finished work.
while true; do
  n=$(/usr/bin/python3 - <<'PYX' 2>/dev/null
import glob,pandas as pd
fs=glob.glob('results/gate3ft_costed_v4/*.csv')
s=set()
for f in fs:
    try: s|=set(pd.read_csv(f,usecols=['sid'],low_memory=False).sid)
    except Exception: pass
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
say "1/6 re-judging every banked row on the W3-only basis"
nice -n 19 /usr/bin/python3 code/l2readopt.py >> "$LOG" 2>&1 || say "WARN readopt"
say "2/6 W3-only re-score, then the CUT on adopted settings"
nice -n 19 /usr/bin/python3 code/l2clean3.py >> "$LOG" 2>&1 || say "WARN clean3"
nice -n 19 /usr/bin/python3 code/l2cut.py --settings adopted >> "$LOG" 2>&1 || say "WARN cut"
say "3/6 team builder, both teams"
TEAM_LABEL=_W3ONLY_ADOPTED TEAM_JOBS=6 nice -n 19 /usr/bin/python3 code/l2team.py >> "$LOG" 2>&1 || say "WARN team"
TEAM_JOBS=6 nice -n 19 /usr/bin/python3 code/l2teamkpi.py --label _W3ONLY_ADOPTED >> "$LOG" 2>&1 || say "WARN kpi"
say "4/6 agreement study"
nice -n 19 /usr/bin/python3 code/l2agree.py >> "$LOG" 2>&1 || say "WARN agree"
/usr/bin/python3 code/appstamp.py >> "$LOG" 2>&1
git add -A; git commit -q -m "Gate 3 adopted-settings cut, teams, checks and agreement study" || true
git pull --rebase -q origin main || true; git push -q origin main || true
# The B-trend ip1 recovery is NOT run here. At 216 s per strategy it is ~70 h
# on this machine and would hold mode C hostage for three days. It is packaged
# for a rented box instead -- see code/cloud_ip1.sh.
say "5/6 relaunching mode C"
nohup caffeinate -i -m -s /usr/bin/python3 code/l2tune.py --mode C --jobs 6 \
      --sorted --cap 6 --seed-from A,B >> results/gate2_run_C.log 2>&1 &
sleep 25; MAIN=$(pgrep -f "l2tune.py --mode C --jobs 6" | head -1)
nohup caffeinate -i -m -s /usr/bin/python3 code/l2tune.py --mode C --jobs 3 \
      --sorted --cap 6 --seed-from A,B --reverse >> results/gate2_run_C_rev.log 2>&1 &
sleep 25; ADD=$(pgrep -f "l2tune.py --mode C --jobs 3" | head -1)
nohup code/l2swapguard.sh "$MAIN" "$ADD" 400 200 >/dev/null 2>&1 &
say "C relaunched main=$MAIN add=$ADD, guard armed; chunks $(ls results/gate2/modeC_*/chunk_*.csv 2>/dev/null|wc -l)"
# CHECKS LAST, AND IN THE BACKGROUND. They are read-only on banked data and
# block nothing, so they must never stand between mode C and the machine.
say "6/6 selection holdout + random-team null, background, lowest priority"
nohup nice -n 19 /usr/bin/python3 code/l2teamcheck.py --label _W3ONLY_ADOPTED \
      >> results/teamcheck_adopted.log 2>&1 &
say "CHAIN COMPLETE"
