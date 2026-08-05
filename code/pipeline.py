"""Full rebuild. Run by GitHub Actions on a schedule."""
import os,sys,subprocess,shutil
R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C=os.path.join(R,'code')
def run(m):
    print('\n=== %s ==='%m,flush=True)
    subprocess.run([sys.executable,os.path.join(C,m)],check=True)
run('build.py')
for m in ('sc2.py','sc2.py','sc2.py','sc2.py','sc2.py'):   # resumable, idempotent
    run(m)
run('sc3.py'); run('sc3.py')
for _ in range(6): run('sc4.py')
for _ in range(8): run('sc5.py')
# sc6 is the v6 duration batch: ~107k signals/pair, ~4 min/pair, resumable per
# block. It is NOT run here -- a full pass is ~2 h and Actions times out at 180
# min with the rest of the pipeline still to go. Score it locally and commit
# results/scores6/; every later run then finds the .npz and skips.
if os.environ.get('FX_RUN_SC6'):
    for _ in range(3): run('sc6.py')
# sc7 is the v7 trend batch: ~48k signals/pair scored against THREE horizons, ~2.2 h.
# Same reason as sc6 -- Actions times out at 180 min. Its .npz are gitignored; what
# the repo carries is pool7.py's per-signal statistics, so this only needs rerunning
# when the signal definitions change.
if os.environ.get('FX_RUN_SC7'):
    for _ in range(3): run('sc7.py')
if os.path.isdir(os.path.join(R, 'results', 'scores7')):
    run('pool7.py')
run('rank2.py'); run('rank3.py'); run('prep.py'); run('dedup.py')
run('strat.py'); run('framework.py')
run('ladder.py'); run('funnel.py')   # both consume framework.py output / its hmm cache
run('crisis.py')                     # scores detectors against the events.py news calendar
# gate 7 for the pre-v6 batches, which were scored without block spreads. Costly
# (rebuilds each module's full frame per pair), so it is opt-in like sc6.
if os.environ.get('FX_RUN_STABILITY'):
    run('stability.py')
run('ninebox.py'); run('mtf.py'); run('bundle.py')
shutil.copy(os.path.join(R,'results','app_data.json'),os.path.join(R,'app_data.json'))
print('\napp_data.json refreshed at repo root')
