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
run('ninebox.py'); run('mtf.py')
run('pairtrend.py')          # per-pair trendiness, and whether gate 4 over-kills
if os.path.exists(os.path.join(R, 'results', 'survivor_composite.csv')):
    run('entry.py')          # Task 3: does the regime read predict excursion shape
run('termstruct.py')         # Tasks 4-6: term structure, confluence, per-pair shape
if os.path.exists(os.path.join(R, 'results', 'entry_events.csv')):
    run('scale.py')          # Task 8: scale x straightness, the four states
    run('duration.py')       # Task 9: state age, hazard, and its null
# Horizon sweep: rebuilds 6 signal modules across 28 pairs and runs a 20-shift null
# at four horizons, ~50 min, so it is opt-in. The committed CSVs regenerate the tables.
if os.environ.get('FX_RUN_HORIZON'):
    run('horizon.py')
elif os.path.exists(os.path.join(R, 'results', 'horizon_signals.csv')):
    print('\n=== horizon.py --report-only ===', flush=True)
    subprocess.run([sys.executable, os.path.join(C, 'horizon.py'),
                    '--report-only'], check=True)
# The selection-inflation null: 50 circular shifts of the target panel, the whole
# gauntlet rerun against each. Gated like sc6/sc7 -- a cold pass rescores all 28
# pairs against every signal and its 2.2 GB of accumulators are gitignored, so
# Actions only recomputes the correction from the committed inflation_runs.csv.
# External data. The fetch hits Yahoo and the scoring rebuilds six signal modules
# against 19 series, ~25 min, so it is opt-in like sc6/sc7. The committed CSVs are
# enough to regenerate the retention tables, which is what --report-only does.
# Reachability probe, always. Seconds, and it is the only way to tell a blocked
# host from a dead one: fred.stlouisfed.org refuses the dev sandbox while every
# other central bank answers, so "unreachable" must be recorded per network
# rather than concluded from one vantage point. Never fails the build.
print('\n=== extdata.py --probe ===', flush=True)
subprocess.run([sys.executable, os.path.join(C, 'extdata.py'), '--probe'], check=False)
if os.environ.get('FX_RUN_EXTERNAL'):
    run('extdata.py'); run('extsig.py')
    run('rates.py'); run('carrysig.py')
else:
    for _m, _f in (('extsig.py', 'ext_signals.csv'),
                   ('carrysig.py', 'carry_signals.csv')):
        if os.path.exists(os.path.join(R, 'results', _f)):
            print('\n=== %s --report-only ===' % _m, flush=True)
            subprocess.run([sys.executable, os.path.join(C, _m),
                            '--report-only'], check=True)
if os.environ.get('FX_RUN_INFLATION'):
    run('inflation.py')
    run('subsetnull.py')      # same accumulator dependency, so same gate
elif os.path.exists(os.path.join(R, 'results', 'inflation_runs.csv')):
    print('\n=== inflation.py --adjust-only ===', flush=True)
    subprocess.run([sys.executable, os.path.join(C, 'inflation.py'),
                    '--adjust-only'], check=True)
# The four validation tests, permanent. Shuffled labels and persistence are cheap;
# synthetic ground truth and refit stability each rebuild the composite, so they
# are gated the same way sc6/sc7 are and run on demand.
if os.environ.get('FX_FULL_VALIDATION'):
    run('validate.py')
else:
    subprocess.run([sys.executable, os.path.join(C, 'validate.py'),
                    '--no-synth', '--no-refit'], check=True)
run('bundle.py')
for _f in ('app_data.json','app_signals.json'):
    shutil.copy(os.path.join(R,'results',_f),os.path.join(R,_f))
print('\napp_data.json refreshed at repo root')
