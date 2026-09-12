#!/bin/bash
# THE CLEAN-FIELD WALK-FORWARD CHAIN ON A RENTED BOX.
#
#   export GH_TOKEN=...; curl -sL https://raw.githubusercontent.com/Jackscuster/fx-data/main/code/cloud_walk.sh | bash
#
#   Dry run on the Mac (no provisioning, no push, 750-strategy field, 2 cores):
#       bash code/cloud_walk.sh --local --limit 250 --jobs 2
#
# WHY A BOX. An OPTION, not the default: the chain runs on the Mac under
# RAM caps and a memory guard (l2cfchain.sh, l2memguard.sh). This exists for
# the day the Mac is needed for something else. It resumes from whatever
# the repo already carries, so a run split between the two is fine.
#
# WHAT IT RUNS. code/l2cfchain.sh --resume: engine -> structures -> identity
# null -> random-entry null -> sizing -> team-size sweep -> slice controls ->
# per-slice walks -> report, on results/gate2_cleanfield.csv (4,807; A-trend
# 2,960 / A-chop 930 / B-chop 917). --resume skips every stage whose output is
# already in the clone and passes its own check; the engine pickles are never
# committed (264 MB), so the engine ALWAYS rebuilds unless a relaunch on the
# same box finds them parked in /opt/fx_bank.
#
# EVERY INPUT IS COMMITTED. data/oanda_ohlc (31 files, 9.7 MB), the three
# gate2_tuned_*.csv, gate2_cleanfield.csv, gate2_ip1_recovered*.csv,
# cost_table.csv. No OANDA token. The only credential is GH_TOKEN.
#
# RESULTS GO TO A BRANCH, walk-<date>, THEN MERGE TO MAIN. The push is only of
# results/*_cleanfield* and the chain log. No code is pushed from the box, so
# the code/** CI trigger never fires from here.
set -euo pipefail
LOCAL=0; LIMIT=""; JOBS_ARG=""
while [ $# -gt 0 ]; do
  case "$1" in
    --local) LOCAL=1; shift;;
    --limit) LIMIT="--limit $2"; shift 2;;
    --jobs)  JOBS_ARG="$2"; shift 2;;
    *) echo "unknown arg $1"; exit 2;;
  esac
done
REPO="${REPO:-Jackscuster/fx-data}"
BRANCH="walk-$(date -u +%Y%m%d)"

if [ "$LOCAL" = "1" ]; then
  JOBS="${JOBS_ARG:-2}"
  echo "== LOCAL DRY RUN: $JOBS cores, $LIMIT, no provisioning, no push"
  cd "$(dirname "$0")/.."
  # shellcheck disable=SC2086
  bash code/l2cfchain.sh --resume --jobs "$JOBS" $LIMIT
  echo "== local chain finished. On a box this would now push branch $BRANCH and merge."
  exit 0
fi

JOBS="${JOBS_ARG:-$(nproc)}"
: "${GH_TOKEN:?set GH_TOKEN to a GitHub token with write access to $REPO}"
echo "== clean-field walk-forward chain, $JOBS cores, branch $BRANCH"

export DEBIAN_FRONTEND=noninteractive
sudo apt-get update -qq
sudo apt-get install -y -qq git python3 python3-pip python3-venv >/dev/null
# PRESERVE THE ENGINE PICKLES ACROSS A RELAUNCH. The clone is shallow and
# destructive; the pickles are 264 MB and never committed, so on a relaunch
# they are parked outside /opt/fx and restored -- which is what lets --resume
# skip a 30-minute engine rebuild on the same box.
mkdir -p /opt/fx_bank
for f in /opt/fx/results/wf_trades_cleanfield.pkl /opt/fx/results/wf_marks_cleanfield.pkl \
         /opt/fx/results/wf_randk_cleanfield.pkl; do
  [ -e "$f" ] && cp -f "$f" /opt/fx_bank/
done
rm -rf /opt/fx && git clone --depth 1 "https://x-access-token:${GH_TOKEN}@github.com/${REPO}.git" /opt/fx
mkdir -p /opt/fx/results
restored=0
for f in /opt/fx_bank/*.pkl; do
  [ -e "$f" ] && cp -f "$f" /opt/fx/results/ && restored=$((restored+1))
done
echo "== restored $restored parked engine pickles"
cd /opt/fx
python3 -m venv .venv && . .venv/bin/activate
pip install -q --upgrade pip && pip install -q -r requirements.lock

# ---- the chain. Its log lives in $HOME/fx-data-logs (outside the repo).
export CF_LOGDIR="$HOME/fx-data-logs"
mkdir -p "$CF_LOGDIR"
t0=$(date +%s)
# shellcheck disable=SC2086
if ! bash code/l2cfchain.sh --resume --jobs "$JOBS" $LIMIT; then
  echo "!! CHAIN HALTED -- see results/CHAIN_HALT.marker and $CF_LOGDIR/cfchain_cleanfield.log"
  echo "!! Partial outputs are still pushed below so nothing finished is lost."
fi
echo "== chain wall time: $(( ($(date +%s) - t0) / 60 )) min"
cp -f "$CF_LOGDIR"/cfchain_cleanfield*.log results/ 2>/dev/null || true  # NOSILENCE-OK: the log is a courtesy copy; its absence is reported by the push list, not hidden

# ---- push results to walk-<date>, then merge into main
git config user.name  "fx-cloud"
git config user.email "fx-cloud@users.noreply.github.com"
git checkout -b "$BRANCH"
git add -f results/*_cleanfield*.csv results/cfchain_cleanfield*.log results/CHAIN_HALT.marker 2>/dev/null || true  # NOSILENCE-OK: the marker exists only on a halt; a missing courtesy log is not a failure
if git diff --cached --quiet; then
  echo "== nothing new to commit"
else
  git commit -m "clean-field walk-forward: $(ls results/*_cleanfield*.csv | wc -l) result files from $(hostname)"
fi
pushed=0
for try in 1 2 3; do
  if git push -u origin "$BRANCH"; then pushed=1; break; fi
  echo "   push of $BRANCH rejected (attempt $try); retrying in 30s"; sleep 30
done
if [ "$pushed" != "1" ]; then
  echo "!! PUSH FAILED. DO NOT DESTROY THIS BOX."
  echo "!! scp -r root@<ip>:/opt/fx/results/*_cleanfield* ."
  exit 1
fi
# merge to main -- main may have moved (CI, the field boxes). The clone is
# SHALLOW, so a true merge can fail for want of a merge base; the branch's one
# commit is cherry-picked onto the fresh origin/main instead, which needs only
# the commit's own parent -- the tip this clone started from. A failure here
# leaves walk-<date> pushed and says so.
SHA=$(git rev-parse HEAD)
merged=0
for try in 1 2 3 4 5; do
  git fetch --depth 1 origin main
  git checkout -B main origin/main
  if git cherry-pick "$SHA" && git push origin main; then merged=1; break; fi
  echo "   cherry-pick/push to main failed (attempt $try); retrying in 30s"
  git cherry-pick --abort 2>/dev/null || true  # NOSILENCE-OK: abort only applies if a pick is in progress
  sleep 30
done
if [ "$merged" != "1" ]; then
  echo "!! MERGE TO MAIN FAILED. Branch $BRANCH IS pushed; merge it from the Mac:"
  echo "!!   git fetch origin $BRANCH && git merge origin/$BRANCH && git push"
  exit 1
fi
echo "== DONE. Results on main via $BRANCH. Report: results/walkforward_report_3slice_cleanfield.csv"
