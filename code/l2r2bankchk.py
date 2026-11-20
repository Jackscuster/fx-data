import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""IS A MODE'S GATE 3 KPI BANK COMPLETE? Exits non-zero if not.

A STAGE FILE, NOT AN INLINE HEREDOC. The same check written inline inside a
driver has to survive two layers of shell quoting, and on 20 Nov a generated
driver was mangled exactly there. A stage that asserts something belongs in a
file that can be run on its own and read in a diff.

    python3 code/l2r2bankchk.py --mode B
"""
import glob
import numpy as np

import l2r2gate1 as G
import l2r2book as BK

NSHARD = 32


def main():
    mode = G.opt('--mode', str, 'B')
    tag = G.opt('--tag', str, 'full')
    nshard = G.opt('--nshard', int, NSHARD)
    z = np.load(BK._bank_slice_file(mode, tag), allow_pickle=True)
    n = int(z['n']); del z
    d = os.path.join(ROOTOUT, 'r2gate2', 'mode%s_gate3parts' % mode)
    fs = sorted(glob.glob(os.path.join(d, 'g3_*_of%d.npz' % nshard)))
    tot = 0
    bad = []
    for f in fs:
        try:
            tot += len(np.load(f, allow_pickle=True)['idx'])
        except Exception as e:
            bad.append('%s (%s)' % (os.path.basename(f), type(e).__name__))
    print('  MODE %s GATE 3 BANK: %s of %s strategies in %d of %d part files'
          % (mode, f'{tot:,}', f'{n:,}', len(fs), nshard), flush=True)
    if bad:
        print('  UNREADABLE PARTS: %s' % ', '.join(bad), flush=True)
    if len(fs) != nshard or tot != n or bad:
        print('  the bank is INCOMPLETE -- the stage that builds it has not landed; '
              'everything downstream of this reads a partial field and would report '
              'numbers for a smaller universe without saying so', flush=True)
        return 1
    print('  complete', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
