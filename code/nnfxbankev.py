"""THE ELEVEN-YEAR ADMISSION BANK, for item 5. PROTOCOL.md AMENDMENT 1, A7.

A7: "build the final version with admission on all of 2005 to 2015 at the
admission count that was best on average". Admission needs net R, net R
excluding the best day, the best single trade and the trade count over the
WHOLE 2005-2015 window. R and the trade count are additive across the two
six-year windows; R excluding the best day and the best single trade are NOT,
because the best day of eleven years is not the larger of the two windows'
best days. So this is a separate pass, not a sum.

A SEPARATE FILE RATHER THAN A FLAG ON nnfxsleeves, because nnfxsleeves is
imported by the null workers and 13 of the 20 had not started yet when this
was written. An edit would have reached those and not the others.
"""
import os, sys, time, argparse
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
ROOT = os.path.dirname(_HERE)
ROOTOUT = os.path.join(ROOT, 'results')
sys.path.insert(0, ROOT)

import numpy as np
import pandas as pd
import nnfxproto as P
import nnfxsrc3 as S3
import nnfxcands as CL
import nnfxsleeves as BK
import l2sweep as S

OUT = os.path.join(ROOTOUT, 'nnfx', 'bank')
EVY = tuple(range(2005, 2016))
PERIODS = (('ev', EVY),)
METRICS = BK.METRICS


def shard_path(w):
    return os.path.join(OUT, 'shardev_real_%02d.npz' % w)


def run_shard(w, nshards, verbose=True):
    S.load_costs(os.environ.get('FX_COST_TABLE',
                                os.path.join(ROOTOUT, 'cost_table_h22.csv')))
    S3.init_space()
    if os.path.exists(shard_path(w)):
        print('  shard %d already on disk' % w, flush=True)
        return
    allp = list(S.all_pairs())
    mine = allp[w::nshards]
    cands, _src, _m = CL.load()
    n = len(cands)
    A = {'ev__%s' % m: np.zeros((n, len(mine)),
                                np.int32 if m == 'trades' else np.float32)
         for m in METRICS}
    t0 = time.time()
    for pi, p in enumerate(mine):
        P.base_dict(p, int(P.RISK['atr_len']))
        for j, t in enumerate(cands):
            d = P.fast_per_pair(S3.mkcand(t), p, PERIODS)['ev']
            A['ev__R'][j, pi] = d['R']
            A['ev__R_ex_best_day'][j, pi] = d['R_ex_best_day']
            A['ev__best_trade'][j, pi] = d['best_trade']
            A['ev__trades'][j, pi] = d['trades']
        if verbose:
            print('    shardev %d pair %s done (%d of %d), %.1f min'
                  % (w, p, pi + 1, len(mine), (time.time() - t0) / 60),
                  flush=True)
    np.savez_compressed(shard_path(w), pairs=np.asarray(mine), n=n, **A)
    print('  shardev %d written in %.1f min' % (w, (time.time() - t0) / 60),
          flush=True)


def merge(nshards, verbose=True):
    S.load_costs(os.environ.get('FX_COST_TABLE',
                                os.path.join(ROOTOUT, 'cost_table_h22.csv')))
    allp = list(S.all_pairs())
    col = {p: i for i, p in enumerate(allp)}
    out, n, got = {}, None, set()
    for w in range(nshards):
        z = np.load(shard_path(w), allow_pickle=False)
        sp = [str(x) for x in z['pairs']]
        n = int(z['n']) if n is None else n
        assert int(z['n']) == n
        for m in METRICS:
            k = 'ev__%s' % m
            if k not in out:
                out[k] = np.zeros((n, len(allp)),
                                  np.int32 if m == 'trades' else np.float32)
            for pi, p in enumerate(sp):
                out[k][:, col[p]] = z[k][:, pi]
        got |= set(sp)
    assert got == set(allp), 'missing %s' % sorted(set(allp) - got)
    path = os.path.join(OUT, 'sleeve_bank_ev_real.npz')
    np.savez_compressed(path, pairs=np.asarray(allp), **out)
    # ---- the additive check: R and trades MUST equal h1 + h2
    pairs2, b2 = BK.load_bank('real')
    assert pairs2 == allp
    dR = float(np.abs(out['ev__R'].astype(np.float64)
                      - (b2['h1__R'].astype(np.float64)
                         + b2['h2__R'].astype(np.float64))).max())
    dT = int(np.abs(out['ev__trades'].astype(np.int64)
                    - (b2['h1__trades'].astype(np.int64)
                       + b2['h2__trades'].astype(np.int64))).max())
    print('  sleeve_bank_ev_real.npz: %d x 28, %.0f MB. ADDITIVE CHECK: '
          'max |R_ev - (R_h1 + R_h2)| = %.3g, max |trades difference| = %d'
          % (n, os.path.getsize(path) / 1e6, dR, dT), flush=True)
    assert dT == 0, ('the eleven-year trade count does not equal h1 + h2 on '
                     'every sleeve (max difference %d) -- a trade is counted '
                     'in the window its leg EXITS in, so this must be exact'
                     % dT)
    assert dR < 1e-2, 'eleven-year R is not h1 + h2 (max %.3g)' % dR
    return path


def load():
    z = np.load(os.path.join(OUT, 'sleeve_bank_ev_real.npz'),
                allow_pickle=False)
    return [str(x) for x in z['pairs']], {k: z[k] for k in z.files
                                          if '__' in k}


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--shard', type=int, default=None)
    ap.add_argument('--nshards', type=int, default=7)
    ap.add_argument('--merge', action='store_true')
    a = ap.parse_args()
    if a.shard is not None:
        run_shard(a.shard, a.nshards)
    if a.merge:
        merge(a.nshards)
