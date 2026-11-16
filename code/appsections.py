import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""RE-INJECT THE RESEARCH SECTIONS INTO app_data.json AFTER bundle.py (16 Nov).

WHY THIS EXISTS. bundle.py rebuilds app_data.json from results/ and signals.json.
It knows nothing about the November research sections -- dc_axis, trend_round2,
trend_quality, crisis_witnesses -- so every cold run of pipeline.py SILENTLY
DELETED all four, taking their app tabs down with them. The 16 Nov close-out
audit caught it: four sections with 0 keys, and the clone audit agreed.

That was my own rule broken: a framework is wired into app_ui.js, app_data.json
AND the pipeline. The first two were done by hand and the third was missing, so
the hand-written half survived only until the next rebuild. This module is the
third place, and pipeline.py calls it immediately after bundle.py.

Each section is rebuilt from its own dated results files by the module that
owns it, so there is one definition of each section and no copy drifts.

    python3 code/appsections.py          # after bundle.py; pipeline.py runs it
"""
import json, subprocess, time

OWNERS = (('dc_axis', 'dcroute', 'the directional-change trend axis (round 1, rejected)'),
          ('trend_round2', 'trendt12report', 'the trend failure anatomy and T1/T2 (round 2, rejected)'),
          ('trend_quality', 'trendqual', 'the label-time quality flag (round 3, SHIPPED)'),
          ('crisis_witnesses', 'witness', 'panel turbulence and Roll illiquidity (rejected)'),
          ('l2_restart', 'r2app', 'the Layer 2 restart and the honest gate 1 (HANDOFF 0l)'))


def main():
    t0 = time.time()
    root = os.path.join(_R, 'app_data.json')
    before = set(json.load(open(root))) if os.path.exists(root) else set()
    missing = [k for k, _, _ in OWNERS if k not in before]
    print('app_data.json sections before: %d keys; research sections missing: %s'
          % (len(before), missing or 'none'), flush=True)
    for key, mod, what in OWNERS:
        r = subprocess.run([sys.executable, os.path.join(ROOTLIB, '%s.py' % mod), '--stage', 'app'],
                           cwd=_R, capture_output=True, text=True)
        ok = r.returncode == 0
        print('  %-18s <- code/%s.py --stage app   %s   %s'
              % (key, mod, 'ok' if ok else 'FAILED', what), flush=True)
        if not ok:
            print((r.stderr or r.stdout)[-300:], flush=True)
    after = json.load(open(root))
    have = [k for k, _, _ in OWNERS if k in after and after[k]]
    print('app_data.json sections after: %d keys; research sections present: %s (%.0f s)'
          % (len(after), have, time.time() - t0), flush=True)
    bad = [k for k, _, _ in OWNERS if k not in after or not after[k]]
    if bad:
        raise SystemExit('appsections: %s still missing from app_data.json' % bad)
    print('APP SECTIONS COMPLETE', flush=True)


if __name__ == '__main__':
    main()
