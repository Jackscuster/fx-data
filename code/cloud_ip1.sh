#!/bin/bash
# B-TREND ip1 RECOVERY ON A RENTED BOX. One command, from a bare Ubuntu host.
#
#   curl -sL https://raw.githubusercontent.com/Jackscuster/fx-data/main/code/cloud_ip1.sh | bash
#
# WHY THIS JOB AND NOT ANOTHER. Mode B's TREND slice never banked ip1/risk1, so
# the walk-forward stitch cannot be reconstructed for those 1,650 crossers --
# W2 has to be scored with the FIRST tune, and it is missing. Recovering it means
# re-running gate 2 stage 1 for each. At 216 s each that is ~99 core-hours: three
# days on the Mac with mode C paused, or about two hours on 48 cores.
#
# MODE B RAN UNCAPPED, so l2recoverip1.py sweeps every indicator parameter
# rather than the top six. Capping would be ~10x faster and would produce a
# DIFFERENT ip1 from the one B actually used -- a silent re-tune wearing the
# name of a recovery. Do not add --cap here.
#
# CREDENTIALS: one GitHub token with write access to the repo, in GH_TOKEN.
# Nothing else. No OANDA token is needed -- every input is committed:
# data/oanda_ohlc (31 files), results/gate2_tuned_modeB.csv, cost_table.csv and
# gate2_param_impact.csv are all tracked.
set -euo pipefail
REPO="${REPO:-Jackscuster/fx-data}"
JOBS="${JOBS:-$(nproc)}"
: "${GH_TOKEN:?set GH_TOKEN to a GitHub token with write access to $REPO}"

echo "== installing"
export DEBIAN_FRONTEND=noninteractive
sudo apt-get update -qq
sudo apt-get install -y -qq git python3 python3-pip python3-venv >/dev/null

echo "== cloning (shallow: history is not needed, only the current inputs)"
rm -rf /opt/fx && git clone --depth 1 "https://x-access-token:${GH_TOKEN}@github.com/${REPO}.git" /opt/fx
cd /opt/fx

echo "== python deps, pinned to the same lockfile the Mac and CI use"
python3 -m venv .venv && . .venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.lock

echo "== recovering B-trend ip1 across $JOBS shards"
mkdir -p results
for i in $(seq 0 $((JOBS-1))); do
  nohup python3 code/l2recoverip1.py --which all --shard "$i" --shards "$JOBS" \
        > "results/ip1_cloud_$i.log" 2>&1 &
done
wait
echo "== merging shard banks"
python3 - <<'PY'
import glob, pandas as pd
fs = sorted(glob.glob('results/gate2_ip1_recovered_s*.csv')) + \
     (['results/gate2_ip1_recovered.csv'] if glob.glob('results/gate2_ip1_recovered.csv') else [])
parts = []
for f in fs:
    try:
        d = pd.read_csv(f); parts.append(d[d.sid != 'sid'])
    except Exception:
        pass
if parts:
    A = pd.concat(parts, ignore_index=True).drop_duplicates('sid')
    A.to_csv('results/gate2_ip1_recovered.csv', index=False)
    print('merged %d recovered strategies' % len(A))
PY

echo "== pushing the bank back"
# RETRY, BECAUSE THE PUSH IS THE ONLY COPY. Two hours of compute lives in these
# files and nowhere else; the scheduled CI run commits to main every weekday at
# 06:00 UTC, so a rejected push here is an ordinary event, not an exception.
# Failing out under `set -e` would leave the bank on a box about to be destroyed.
git config user.name  "fx-cloud"
git config user.email "fx-cloud@users.noreply.github.com"
git add -f results/gate2_ip1_recovered.csv results/gate2_ip1_recovered_s*.csv results/ip1_cloud_*.log
git commit -q -m "B-trend ip1 recovery, completed on a rented box" || true
pushed=0
for try in 1 2 3 4 5; do
  git pull --rebase -q origin main || true
  if git push -q origin main; then pushed=1; break; fi
  echo "   push rejected (attempt $try); retrying in 30s"
  sleep 30
done
if [ "$pushed" != "1" ]; then
  echo "!! PUSH FAILED. DO NOT DESTROY THIS BOX."
  echo "!! The recovered bank is at /opt/fx/results/gate2_ip1_recovered*.csv"
  echo "!! Copy it off first:  scp root@<ip>:/opt/fx/results/gate2_ip1_recovered*.csv ."
  exit 1
fi
echo "== DONE. Shut the box down."
