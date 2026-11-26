#!/bin/bash
# WIRE THE NEW NUMBERS INTO THE APP THE MOMENT ITEM 5 LANDS.
#
# queue_1126.sh runs four stages and stage 4 is six hours long, so waiting for
# the whole queue would leave the app stale all afternoon while the three
# reports and item 5 sat on disk. This waits for the queue's own "nnfxfinal"
# line and then rebuilds app_data.json -- CLAUDE.md's rule is that every
# framework is wired into all three places, and books_gates.csv has just
# grown a real B1 column.
#
# It runs EARLY in booknull2b's bank phase on purpose: the three null workers
# spend their first 36 minutes building banks and their memory climbs through
# it, so a two-minute app rebuild is cheapest at the start.
#
# STOP WITH: bash code/chain/stop_chain.sh $(cat results/chainlogs/appafter5.pgid)
set -u
cd /Users/jackcuster/fx-data
export FX_COST_TABLE=results/cost_table_h22.csv
LOG=results/chainlogs/appafter5.log
Q=results/chainlogs/queue_1126.log
ts(){ date "+[%H:%M:%S]"; }
echo "$(ts) appafter5 ARMED -- waiting for the queue's nnfxfinal line" >> $LOG

# bounded wait: 90 minutes is far beyond the ~35 the three stages need
for i in $(seq 1 180); do
  if grep -q "nnfxfinal OK\|nnfxfinal FAILED" "$Q" 2>/dev/null; then break; fi
  sleep 30
done
if ! grep -q "nnfxfinal OK\|nnfxfinal FAILED" "$Q" 2>/dev/null; then
  echo "$(ts) appafter5 GIVING UP -- no nnfxfinal line after 90 min" >> $LOG
  exit 2
fi
grep -E "reports|nnfxfinal|bankev" "$Q" >> $LOG

echo "$(ts) rebuilding app_data.json" >> $LOG
python3 code/r2app.py >> $LOG 2>&1 && python3 code/bundle.py >> $LOG 2>&1 \
  && cp results/app_data.json app_data.json \
  && echo "$(ts) app_data.json rebuilt, $(wc -c < app_data.json) bytes" >> $LOG \
  || echo "$(ts) APP REBUILD FAILED" >> $LOG
node --check app_ui.js \
  && echo "$(ts) node --check app_ui.js PASSES" >> $LOG \
  || echo "$(ts) node --check app_ui.js FAILS -- the interface would blank" >> $LOG
echo "$(ts) DONE appafter5" >> $LOG
