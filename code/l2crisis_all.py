import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Crisis split + concentration over EVERY crosser of one mode/slice. Chunked
and resumable.

PARAMETERISED BY MODE AND SLICE so mode A runs the IDENTICAL code path mode B
ran -- re-implementing the rules for A would be a second chance to get them
different. Defaults reproduce the original mode B call exactly.

    python code/l2crisis_all.py                    # mode B, both slices (as before)
    python code/l2crisis_all.py --mode A --slice trend

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

CHUNK = 25


def tag(mode, sl):
    return 'mode%s%s' % (mode, '_' + sl if sl else '')


def ckdir(mode, sl):
    # mode B's original run wrote to results/crisis_all with no mode in the path.
    # That directory IS mode B's cache and is left exactly where it is.
    return os.path.join(ROOTOUT, 'crisis_all' if (mode, sl) == ('B', None)
                        else 'crisis_all_%s' % tag(mode, sl))


def crossers(mode='B', sl=None, src=None):
    f = src or os.path.join(ROOTOUT, 'gate2_tuned_mode%s.csv' % mode)
    D = pd.read_csv(f, low_memory=False)
    D = D[(D.crosses_label == True) & D.ip2.notna()]
    if sl:
        D = D[D.slice == sl]
    return D.reset_index(drop=True)


def main():
    a = sys.argv[1:]
    mode = a[a.index('--mode') + 1] if '--mode' in a else 'B'
    sl = a[a.index('--slice') + 1] if '--slice' in a else None
    src = a[a.index('--src') + 1] if '--src' in a else None
    CK = ckdir(mode, sl)
    os.makedirs(CK, exist_ok=True)
    D = crossers(mode, sl, src)
    n = len(D)
    todo = [i for i in range(0, n, CHUNK)
            if not os.path.exists(os.path.join(CK, 'c_%05d.csv' % i))]
    print('crossers %d, chunks %d total, %d to do' % (n, (n + CHUNK - 1) // CHUNK, len(todo)), flush=True)
    t0 = time.time()
    for k, lo in enumerate(todo, 1):
        rows = D.iloc[lo:lo + CHUNK].to_dict('records')
        out = C.run(rows, mode=mode, jobs=1)
        out.to_csv(os.path.join(CK, 'c_%05d.csv' % lo), index=False)
        el = time.time() - t0
        print('  chunk %d/%d (rows %d-%d)  %.0f s elapsed, ~%.1f h remaining'
              % (k, len(todo), lo, lo + len(rows) - 1, el,
                 (el / k) * (len(todo) - k) / 3600), flush=True)
    fs = sorted(glob.glob(os.path.join(CK, 'c_*.csv')))
    A = pd.concat([pd.read_csv(f) for f in fs], ignore_index=True)
    fout = 'gate2_crisis_split_%s_all.csv' % tag(mode, sl)
    A.to_csv(os.path.join(ROOTOUT, fout), index=False)
    print('wrote %s (%d rows)' % (fout, len(A)), flush=True)
    print('DONE', flush=True)


if __name__ == '__main__':
    main()
