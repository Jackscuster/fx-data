#!/bin/bash
# THE CLEAN FIELD, FOUR SLICES, ON RENTED BOXES.
#
#   ONE BOX:    export GH_TOKEN=...; curl -sL <raw>/code/cloud_field.sh | bash -s -- --box 0 --of 1
#   THREE BOXES: run on each, k = 0, 1, 2:
#               export GH_TOKEN=...; curl -sL <raw>/code/cloud_field.sh | bash -s -- --box k --of 3
#   MERGE:      from the Mac, once every box has pushed its shard:
#               python3 code/l2cleanfield.py --merge
#
# WHY THIS JOB. l2tune.crosses_label applies gate 2's bars to the STITCHED W2+W3
# blind book and requires n_w3 >= MIN_TRADES_BLIND. W3 is 2016-2020 -- the years
# the walk-forward trades -- so the field is chosen with sight of them and every
# absolute level built on it is inflated. This re-labels the FULL candidate set
# on W2 alone under ip1, which was tuned on W1 and has never seen W2.
#
# WHY IT NEEDS A BOX AT ALL. Three of the four slices cost 5.5 core-hours and
# run on the Mac in 36 minutes. B-trend does not: NONE of its 14,815 candidates
# has ip1, and the packaged cloud_ip1.sh recovers it only for the 1,650
# CROSSERS -- which is the wrong set, because the crosser list is the thing
# being rebuilt. Recovering ip1 for all 14,815 at the measured 216 s each is
# ~889 core-hours. That is the job. The W2 scoring on top is 9 core-hours, noise
# beside it.
#
# SHARDING IS BY md5(sid) % N, fixed for all time -- position-based sharding let
# restarted shards claim overlapping work on 2026-09-10 and burned 18.7 core
# hours on 228 duplicate runs. Every worker is resumable on sid, so a box that
# dies is restarted with the same --box and picks up where it stopped.
#
# CREDENTIALS: one GitHub token with write access, in GH_TOKEN. Nothing else.
set -euo pipefail
BOX=0; OF=1; LOCAL=0; LIMIT=""
while [ $# -gt 0 ]; do
  case "$1" in
    --box) BOX="$2"; shift 2;;
    --of)  OF="$2";  shift 2;;
    --limit) LIMIT="--limit $2"; shift 2;;
    # --local runs the two PYTHON steps in the current checkout and skips
    # provisioning, cloning and pushing. It exists so the sharding and merge can
    # be dry-run on the Mac before a box is rented -- the argument plumbing under
    # test is then the real script's, not a copy of it.
    --local) LOCAL=1; shift;;
    *) echo "unknown arg $1"; exit 2;;
  esac
done
REPO="${REPO:-Jackscuster/fx-data}"
if [ "$LOCAL" = "1" ]; then
  JOBS="${JOBS:-4}"
  echo "== LOCAL DRY RUN: box $BOX of $OF, $JOBS cores, no provisioning, no push"
  cd "$(dirname "$0")/.."
  python3 code/l2cleanfield.py --slices A-trend,A-chop,B-chop \
          --jobs "$JOBS" --box "$BOX" --of "$OF" --shard-only $LIMIT
  echo "== box $BOX shard written. Merge with: python3 code/l2cleanfield.py --merge $LIMIT"
  exit 0
fi
JOBS="${JOBS:-$(nproc)}"
: "${GH_TOKEN:?set GH_TOKEN to a GitHub token with write access to $REPO}"
echo "== box $BOX of $OF, $JOBS cores"

export DEBIAN_FRONTEND=noninteractive
sudo apt-get update -qq
sudo apt-get install -y -qq git python3 python3-pip python3-venv >/dev/null
rm -rf /opt/fx && git clone --depth 1 "https://x-access-token:${GH_TOKEN}@github.com/${REPO}.git" /opt/fx
cd /opt/fx
python3 -m venv .venv && . .venv/bin/activate
pip install -q --upgrade pip && pip install -q -r requirements.lock
mkdir -p results

# ---- 1. recover ip1 for every B-trend CANDIDATE this box owns
echo "== [1/2] B-trend ip1 recovery, box $BOX of $OF"
for i in $(seq 0 $((JOBS-1))); do
  nohup python3 code/l2recoverip1.py --which all --all-candidates \
        --box "$BOX" --of "$OF" --shard "$i" --shards "$JOBS" \
        > "results/field_ip1_b${BOX}_s${i}.log" 2>&1 &
done
wait

# ---- 2. score this box's candidates on W2 under ip1 and label them
echo "== [2/2] W2-only scoring and labelling, box $BOX of $OF"
python3 code/l2cleanfield.py --slices A-trend,A-chop,B-chop,B-trend \
        --jobs "$JOBS" --box "$BOX" --of "$OF" --shard-only $LIMIT

echo "== pushing shard $BOX"
git config user.name  "fx-cloud"
git config user.email "fx-cloud@users.noreply.github.com"
git add -f results/gate2_ip1_recovered_box*.csv results/gate2_w2only_scores_box*.csv results/field_ip1_b*.log
git commit -q -m "clean field: box ${BOX}/${OF} shard" || true
pushed=0
for try in 1 2 3 4 5; do
  git pull --rebase -q origin main || true
  if git push -q origin main; then pushed=1; break; fi
  echo "   push rejected (attempt $try); retrying in 30s"; sleep 30
done
if [ "$pushed" != "1" ]; then
  echo "!! PUSH FAILED. DO NOT DESTROY THIS BOX."
  echo "!! scp root@<ip>:/opt/fx/results/gate2_*box*.csv ."
  exit 1
fi
echo "== BOX $BOX DONE. Merge from the Mac: python3 code/l2cleanfield.py --merge"
