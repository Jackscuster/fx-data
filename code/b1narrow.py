import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""B1-NARROW — the eleven-step walk on a narrow universe (Jack, 24 Nov).

WHY NARROW. The full-field eleven-step walk was cancelled after A1: no slot
option is profitable, so spending ~104 Mac hours enumerating the whole field
again could not be justified. This asks a smaller and sharper question: do the
10 non-luck winners, and the family their components come from, survive on SIX
YEARS THEY WERE NEVER SELECTED ON?

THE UNIVERSE, as specified:
  (a) the 10 non-luck winners
  (b) the C1-ONLY family: every strategy whose C1 is lemantrend_signals or
      waddah_attar_explosion_signals -- 14,040 per mode
  (c) a 2,000-strategy stratified sample per mode as the CONTROL
  32,090 strategy-slots in total.

WHAT IS AND IS NOT BANKED. The winner's per-year record over all sixteen years
(0.42 GB) and, for the winners and the control ONLY, per pair and per direction
(2.94 GB). PER-CONFIG-PER-YEAR IS NOT BANKED: at 727 configurations x 11 steps
x 4 streams it is 19.1 GB against 10 GB free, and Jack ruled that no bank may
be deleted to make room. Nothing in this report needs it -- every figure below
reads the SELECTED configuration's record. Plateau selection and tuning-window
length DO need it and are registered in HANDOFF as still requiring their own
pass.

2010-2015 WERE NEVER SEEN AT SELECTION. The winners were chosen on the
five-step walk, whose earliest tuning year is 2011 and whose trade years are
2016-2020. The eleven-step walk's trade years 2010-2015 are therefore six
years no part of the original selection touched -- which is the whole point.

    FX_WALK=ext11 python3 code/b1narrow.py --stage universe --mode A
    FX_WALK=ext11 python3 code/b1narrow.py --stage tune --mode A --jobs 8
    FX_WALK=ext11 python3 code/b1narrow.py --stage md
"""
import time, glob, json, hashlib
import numpy as np, pandas as pd

import l2sweep as S
import l2r2gate1 as G
import l2r2gate2 as G2
import l2r2book as BK
import l2r2winners as WN

OUT = os.path.join(ROOTOUT, 'r2reads')
os.makedirs(OUT, exist_ok=True)
TAG = 'b1narrow'
FAMILY_C1 = ('lemantrend_signals', 'waddah_attar_explosion_signals')
NEW_YEARS = (2010, 2011, 2012, 2013, 2014, 2015)      # never seen at selection
OLD_YEARS = (2016, 2017, 2018, 2019, 2020)
CONTROL_N = 2000
CONTROL_SEED = 20261124


def universe(mode='A'):
    """-> DataFrame(bank_row, sid, cohort) for the three cohorts."""
    z = np.load(BK._bank_slice_file(mode, 'full'), allow_pickle=True)
    CB = np.asarray(z['combo'], dtype=object)
    n = int(z['n'])
    sid = np.array(['|'.join([str(x) for x in r]) for r in CB])
    c1 = np.array([str(r[0]) for r in CB])
    rows = []
    W = pd.read_csv(os.path.join(ROOTOUT, 'r2gate2', 'mode%s_winners.csv' % mode))
    win = set(int(x) for x in W.bank_row)
    for k in sorted(win):
        rows.append(dict(bank_row=k, sid=sid[k], cohort='winner'))
    fam = np.flatnonzero(np.isin(c1, FAMILY_C1))
    for k in fam:
        if int(k) in win:
            continue
        rows.append(dict(bank_row=int(k), sid=sid[k], cohort='family'))
    rng = np.random.default_rng(CONTROL_SEED)
    taken = set(r['bank_row'] for r in rows)
    pool = np.setdiff1d(np.arange(n), np.array(sorted(taken)))
    ctl = rng.choice(pool, size=min(CONTROL_N, len(pool)), replace=False)
    for k in sorted(ctl):
        rows.append(dict(bank_row=int(k), sid=sid[int(k)], cohort='control'))
    D = pd.DataFrame(rows)
    D['mode'] = mode
    f = os.path.join(OUT, 'mode%s_b1narrow_universe.csv' % mode)
    D.to_csv(f, index=False)
    print('  universe [mode %s]: %s rows -- %s' % (mode, f'{len(D):,}',
          ', '.join('%s %s' % (c, f'{int(v):,}')
                    for c, v in D.cohort.value_counts().items())), flush=True)
    return D, f


def stage_tune(mode='A', jobs=8, nshard=None, nmax=None):
    """Tune the narrow universe on the ELEVEN-step walk, expectancy objective."""
    assert G2.WALK == 'ext11', 'run with FX_WALK=ext11; got %r' % G2.WALK
    G.manifest_check()
    S.load_costs()
    f = os.path.join(OUT, 'mode%s_b1narrow_universe.csv' % mode)
    if not os.path.exists(f):
        universe(mode)
    U = pd.read_csv(f)
    if nmax:
        U = U.head(nmax)
    combos = [tuple(s.split('|')) for s in U.sid]
    print('  B1-narrow tune [mode %s]: %s strategies, %d steps, years %d-%d'
          % (mode, f'{len(combos):,}', G2.NSTEP, G2.YEAR0, G2.YEAR0 + G2.NYEAR - 1),
          flush=True)
    outdir, res = G2.run(mode, combos, TAG, jobs=jobs,
                         cap=30000, nshard=nshard or max(jobs * 4, jobs))
    sz = sum(os.path.getsize(x) for x in
             glob.glob(os.path.join(outdir, 'shard_*_part*.npz')))
    print('  B1-narrow bank [mode %s]: %.2f GB in %s'
          % (mode, sz / 1024 ** 3, os.path.relpath(outdir, _R)), flush=True)
    return outdir
