import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""STAGE GUARD — every chain stage must prove it produced something.

Three stages have now reported success while doing nothing: the cut read a stale
verdicts file, the agreement study found no roster, and the agreement study
found a roster with no settings. Each printed a cheerful line and exited zero,
and the chain recorded a completed stage.

The pattern is always the same -- a fallback where a failure belonged. This
checks the OUTPUT instead of trusting the exit code:

    exists          the file is there
    non-empty       more than a header
    min_rows        at least this many rows, declared per stage
    fresher_than    written during THIS run, not left over from a previous one

A stage that fails any of these writes results/CHAIN_HALT.marker and exits
non-zero, which halts the chain. The marker names the stage and the reason.
"""
import argparse, time
import datetime as dt
import pandas as pd

MARKER = os.path.join(ROOTOUT, 'CHAIN_HALT.marker')

# stage -> (path, minimum rows)
STAGES = {
    'readopt':  ('gate3ft_adoptions_v2.csv', 4000),
    'w3score':  ('gate2_w3only_scores_00.csv', 1000),
    'cut':      ('gate3_costed_verdicts.csv', 50),
    'team':     ('team1{L}_roster.csv', 5),
    'teamkpi':  ('team_kpis{L}.csv', 2),
    'agree':    ('agreement_levels_team1.csv', 3),
    'checks':   ('team_checks{L}.csv', 1),
}



def no_silenced_errors():
    """NO SILENCED ERRORS. Refuses to start a chain while any silencing pattern
    is unmarked in code/.

    On 2026-09-11 `git stash pop -q 2>/dev/null` hid the one message saying the
    uncommitted l2walkfwd.py was still in a stash; six chain stages then ran
    against a binary with no --suffix and exited in a second each. The chain's
    own guards printed all six failures -- it was the git error I suppressed
    that cost the two hours. A failure that cannot print surfaces somewhere
    else, later, looking like something it is not.
    """
    import subprocess
    r = subprocess.run([sys.executable, os.path.join(ROOTLIB, 'l2nosilence.py')],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout, flush=True)
        return False, 'silenced-error sites found; see output above'
    return True, r.stdout.strip().splitlines()[-1] if r.stdout.strip() else 'clean'

def halt(stage, reason):
    msg = ('CHAIN HALTED at stage "%s"\n%s\n\n%s\n'
           % (stage, dt.datetime.now().strftime('%F %T'), reason))
    with open(MARKER, 'w') as f:
        f.write(msg)
    print(msg, flush=True)
    raise SystemExit(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('stage')
    ap.add_argument('--label', default='')
    ap.add_argument('--since', type=float, default=0.0,
                    help='epoch seconds; output must be newer than this')
    a = ap.parse_args()
    if a.stage not in STAGES:
        halt(a.stage, 'unknown stage name -- the guard itself is misconfigured')
    rel, minrows = STAGES[a.stage]
    path = os.path.join(ROOTOUT, rel.replace('{L}', a.label))
    if not os.path.exists(path):
        halt(a.stage, 'expected output does not exist: %s' % path)
    if os.path.getsize(path) < 64:
        halt(a.stage, 'output is empty or header-only: %s (%d bytes)'
             % (path, os.path.getsize(path)))
    if a.since and os.path.getmtime(path) < a.since:
        halt(a.stage,
             'output is STALE. %s was last written %s, before this stage began '
             '(%s). The stage read an old file and reported success -- exactly '
             'the fault this guard exists to catch.'
             % (path, dt.datetime.fromtimestamp(os.path.getmtime(path)).strftime('%F %T'),
                dt.datetime.fromtimestamp(a.since).strftime('%F %T')))
    try:
        n = len(pd.read_csv(path, low_memory=False))
    except Exception as e:
        halt(a.stage, 'output is unreadable: %s (%s)' % (path, str(e)[:120]))
    if n < minrows:
        halt(a.stage, 'output has %d rows, below the declared minimum of %d for '
                      'this stage: %s' % (n, minrows, path))
    print('  stage OK: %s -> %s, %d rows' % (a.stage, os.path.basename(path), n),
          flush=True)


if __name__ == '__main__':
    main()
