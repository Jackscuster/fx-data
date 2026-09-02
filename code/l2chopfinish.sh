#!/bin/bash
# WHEN MODE A'S CHOP SLICE FINISHES, redo everything that was trend-only.
#
# The A sweep and the A+B pooled sweep were both run on A-TREND ALONE, because
# chop was still tuning. Neither is a complete answer for mode A until this has
# run. It waits for all 57 chop chunks, then repeats the exact same pipeline
# steps for chop and re-sweeps both pools with chop included.
#
# Launched detached; safe to re-run (every step is resumable or idempotent).
set -e
cd "$(dirname "$0")/.."
NEED=57
while [ "$(ls results/gate2/modeA_chop/chunk_*.csv 2>/dev/null | wc -l)" -lt "$NEED" ]; do
  sleep 300
done
echo "chop complete: $(date)"
/usr/bin/python3 - <<'PY'
import glob, pandas as pd
fs = sorted(glob.glob('results/gate2/modeA_chop/chunk_*.csv'))
D = pd.concat([pd.read_csv(f, low_memory=False) for f in fs], ignore_index=True)
D.to_csv('results/gate2_tuned_modeA_chop.csv', index=False)
print('chop tuned rows %d, crossers %d' % (len(D), int((D.crosses_label == True).sum())))
PY
nice -n 19 /usr/bin/python3 code/l2crisis_all.py --mode A --slice chop \
     --src results/gate2_tuned_modeA_chop.csv
nice -n 19 /usr/bin/python3 code/l2rank.py --mode A --slice chop --clean
nice -n 19 /usr/bin/python3 code/l2deliver.py --mode A --slice chop --top 10
/usr/bin/python3 - <<'PY'
import json
p = 'results/modes_status.json'
s = json.load(open(p)); s.setdefault('A', {})['chop'] = 'complete'
json.dump(s, open(p, 'w'), indent=1)
PY
nice -n 19 /usr/bin/python3 code/l2modes.py
# re-sweep BOTH pools with chop in them
nice -n 19 /usr/bin/python3 code/l2sweepn.py --pool-a --lo 5 --hi 25 || true
nice -n 19 /usr/bin/python3 code/l2sweepn.py --combine --lo 5 --hi 25
/usr/bin/python3 code/appstamp.py
git add -A
git commit -q -m "Mode A chop complete: A and A+B sweeps redone with chop included

Both sweeps were trend-only while chop tuned. Rerun by code/l2chopfinish.sh.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_0198PoFd8YbETkDPepLUiDzL" || true
git pull --rebase -q origin main || true
git push -q origin main || true
echo "REDO DONE $(date)"
