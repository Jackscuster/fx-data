#!/bin/bash
# THE BLIND-LABEL PROGRAMME'S TUNES ON RENTED BOXES (HANDOFF 0f, 21 Sep).
#
#   THREE BOXES, one command each, k = 0, 1, 2:
#     export GH_TOKEN=...; curl -sL https://raw.githubusercontent.com/Jackscuster/fx-data/main/code/cloud_refit.sh | bash -s -- --box k --of 3
#   MERGE on the Mac once every box has pushed:  python3 code/l2refit.py --stage report --suffix _blind_full --windows "$WIN"
#
# WHAT RUNS. code/l2refit.py --stage tune on results/refit_candidates_full.csv (45,142: modes A, B and C's 299
# chunks) for the five blind-label windows: tune on years 1-4, grade on year 5 (scored, reported, never used),
# trade year 6. Every strategy scored routed AND always-on. Costs: results/cost_table_h22.csv (measured OANDA
# spreads at 22:00 NY). Sharded by md5(sid) % 3 across boxes and md5(sid|w) % nproc within a box; every
# (sid, window) is banked as it completes, so a box that dies is relaunched with the same --box and resumes.
# The bank is parked outside the clone across a relaunch, exactly as cloud_field.sh does.
#
# CREDENTIALS: GH_TOKEN with write access. Nothing else. Every input is committed (data/oanda_ohlc, the
# candidate list, the cost tables, results/layer1_states.csv).
set -euo pipefail
BOX=0; OF=1; LOCAL=0; LIMIT=""
WIN="2011-2014:2015:2016,2012-2015:2016:2017,2013-2016:2017:2018,2014-2017:2018:2019,2015-2018:2019:2020"
SUF=_blind_full; CAND=results/refit_candidates_full.csv
while [ $# -gt 0 ]; do
  case "$1" in
    --box) BOX="$2"; shift 2;;
    --of)  OF="$2";  shift 2;;
    --local) LOCAL=1; shift;;
    *) echo "unknown arg $1"; exit 2;;
  esac
done
REPO="${REPO:-Jackscuster/fx-data}"
if [ "$LOCAL" = "1" ]; then
  JOBS="${JOBS:-4}"; echo "== LOCAL DRY RUN: box $BOX of $OF, $JOBS workers, no provisioning, no push"
  cd "$(dirname "$0")/.."
  FX_COST_TABLE=results/cost_table_h22.csv python3 code/l2refit.py --stage tune --candidates "$CAND" --windows "$WIN" --jobs "$JOBS" --suffix "$SUF" --box "$BOX" --of "$OF"
  exit 0
fi
JOBS="${JOBS:-$(nproc)}"
: "${GH_TOKEN:?set GH_TOKEN to a GitHub token with write access to $REPO}"
echo "== box $BOX of $OF, $JOBS workers"
export DEBIAN_FRONTEND=noninteractive
sudo apt-get update -qq
sudo apt-get install -y -qq git python3 python3-pip python3-venv >/dev/null
mkdir -p /opt/fx_bank
for f in /opt/fx/results/refit_settings${SUF}_b*_s*.csv; do [ -e "$f" ] && cp -f "$f" /opt/fx_bank/; done
rm -rf /opt/fx && git clone --depth 1 "https://x-access-token:${GH_TOKEN}@github.com/${REPO}.git" /opt/fx
mkdir -p /opt/fx/results; restored=0
for f in /opt/fx_bank/*.csv; do [ -e "$f" ] && cp -f "$f" /opt/fx/results/ && restored=$((restored+1)); done
echo "== restored $restored banked shard files"
cd /opt/fx
python3 -m venv .venv && . .venv/bin/activate
pip install -q --upgrade pip && pip install -q -r requirements.lock
t0=$(date +%s)
FX_COST_TABLE=results/cost_table_h22.csv python3 code/l2refit.py --stage tune --candidates "$CAND" --windows "$WIN" --jobs "$JOBS" --suffix "$SUF" --box "$BOX" --of "$OF" 2>&1 | tee "logs/refit_tune_b${BOX}.log"
echo "== tunes done in $(( ($(date +%s)-t0)/60 )) min"
git config user.name "fx-cloud"; git config user.email "fx-cloud@users.noreply.github.com"
git add -f results/refit_settings${SUF}_b*_s*.csv logs/refit_tune_b${BOX}.log
if git diff --cached --quiet; then echo "== nothing new to commit"; else git commit -m "blind-label tunes: box ${BOX}/${OF}"; fi
pushed=0
for try in 1 2 3 4 5; do
  if ! git pull --rebase origin main; then echo "   pull failed on attempt $try (reported, not hidden)"; fi
  if git push origin main; then pushed=1; break; fi
  echo "   push rejected (attempt $try); retrying in 30s"; sleep 30
done
if [ "$pushed" != "1" ]; then echo "!! PUSH FAILED. DO NOT DESTROY THIS BOX. scp root@<ip>:/opt/fx/results/refit_settings${SUF}_b*.csv ."; exit 1; fi
echo "== BOX $BOX DONE."
