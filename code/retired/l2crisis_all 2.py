import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Crisis split + concentration over EVERY mode B crosser. Chunked and resumable.

~2,653 configurations x 28 pairs on ONE core, roughly 17 hours. It is chunked at
25 so an interruption costs one chunk, not the pass -- this machine has lost
power twice and had a watcher kill its own side-work three times, and a
seventeen-hour job with no checkpoints would eventually be started for the
fourth time.

Ranks on the CRISIS-EXCLUDED book; crisis P&L is carried in its own columns and
never enters the ranking. See l2crisis.py for why, and for the overlap rule.
"""
import glob, json, time
import numpy as np, pandas as pd
import l2crisis as C

CK = os.path.join(ROOTOUT, 'crisis_all')
CHUNK = 25


def crossers():
    D = pd.read_csv(os.path.join(ROOTOUT, 'gate2_tuned_modeB.csv'), low_memory=False)
    D = D[(D.crosses_label == True) & D.ip2.notna()].reset_index(drop=True)
    return D


def main():
    os.makedirs(CK, exist_ok=True)
    D = crossers()
    n = len(D)
    todo = [i for i in range(0, n, CHUNK)
            if not os.path.exists(os.path.join(CK, 'c_%05d.csv' % i))]
    print('crossers %d, chunks %d total, %d to do' % (n, (n + CHUNK - 1) // CHUNK, len(todo)), flush=True)
    t0 = time.time()
    for k, lo in enumerate(todo, 1):
        rows = D.iloc[lo:lo + CHUNK].to_dict('records')
        out = C.run(rows, mode='B', jobs=1)
        out.to_csv(os.path.join(CK, 'c_%05d.csv' % lo), index=False)
        el = time.time() - t0
        print('  chunk %d/%d (rows %d-%d)  %.0f s elapsed, ~%.1f h remaining'
              % (k, len(todo), lo, lo + len(rows) - 1, el,
                 (el / k) * (len(todo) - k) / 3600), flush=True)
    fs = sorted(glob.glob(os.path.join(CK, 'c_*.csv')))
    A = pd.concat([pd.read_csv(f) for f in fs], ignore_index=True)
    A.to_csv(os.path.join(ROOTOUT, 'gate2_crisis_split_modeB_all.csv'), index=False)
    print('wrote gate2_crisis_split_modeB_all.csv (%d rows)' % len(A), flush=True)
    print('DONE', flush=True)


if __name__ == '__main__':
    main()
