"""THE CANDIDATE LIST THE SLEEVE BANK IS BUILT ON -- PROTOCOL.md AMENDMENT 1, item 1.

Jack's item 1 names "the 200,000 sampled plus local-search algorithms from
Source 3". Source 3 saved only the top 50 identities and the 200,000
objectives, not the 200,000 identities, so they are RECOVERED here rather
than re-drawn: `draw` is deterministic given `default_rng(20261125)`, and the
local search is deterministic given the same rng stream afterwards.

THE REPLAY IS CHECKED, NOT ASSUMED. Two assertions have to hold or this file
refuses to write:

  1. the 200,000 recovered tuples must reproduce src3_sample.csv's
     obj_discovery on a random 300 of them, to 1e-9;
  2. the replayed local search must end on the same best discovery objective
     Source 3 reported, +18.007580341220848.

If either fails the candidate list is not Source 3's and nothing downstream
means what it says.

The local-search set is every algorithm the hill climb EVALUATED, not just
the 200 it ended on. That is the honest count of what was looked at, and it
is what B1's selection null has to match.
"""
import os, sys, time, json
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
ROOT = os.path.dirname(_HERE)
ROOTOUT = os.path.join(ROOT, 'results')
sys.path.insert(0, ROOT)

import numpy as np
import pandas as pd
import nnfxproto as P
import nnfxsrc3 as S3
import l2sweep as S

OUT = os.path.join(ROOTOUT, 'nnfx', 'bank')
os.makedirs(OUT, exist_ok=True)
CAND_NPZ = os.path.join(OUT, 'cand_index.npz')
SEED = 20261125
BEST_LOCAL_DISC = 18.007580341220848     # SOURCE3.md, the number to reproduce


def _opt_index():
    """{slot: {(name,setting): i}} and the inverse, over the declared space."""
    fwd, inv = {}, {}
    for sl in P.SLOTS:
        fwd[sl] = {o: i for i, o in enumerate(S3.SPACE[sl])}
        inv[sl] = list(S3.SPACE[sl])
    return fwd, inv


def replay_local(starts, pairs, years, rng, cap=S3.N_LOCAL_CAP, verbose=True):
    """nnfxsrc3.local_search, line for line, but RECORDING every tuple.

    Kept as a separate function rather than a flag on the original because
    the original is what produced SOURCE3.md and must not be touched.
    """
    seen = {}
    order = []                       # insertion order of what was evaluated
    used = 0
    best = []
    t0 = time.time()
    for si, (t, o0) in enumerate(starts):
        cur, curo = t, o0
        improved = True
        while improved and used < cap:
            improved = False
            nb = S3.neighbours(cur)
            rng.shuffle(nb)
            for u in nb:
                if used >= cap:
                    break
                k = P.cand_id(S3.mkcand(u))
                if k in seen:
                    continue
                o, _n, _tot = P.fast_obj(S3.mkcand(u), pairs, years)
                seen[k] = o
                order.append(u)
                used += 1
                if o > curo:
                    cur, curo = u, o
                    improved = True
                    break
        best.append((cur, curo))
        if verbose and (si + 1) % 25 == 0:
            print('    replay %d/%d starts, %d evaluations, %.1f min'
                  % (si + 1, len(starts), used, (time.time() - t0) / 60),
                  flush=True)
    return best, used, order


def build(verbose=True):
    S.load_costs(os.environ.get('FX_COST_TABLE',
                                os.path.join(ROOTOUT, 'cost_table_h22.csv')))
    S3.init_space(); S3.self_check(); P.check_masks()
    disc, _repl = S3.pair_sets()
    fwd, _inv = _opt_index()

    rng = np.random.default_rng(SEED)
    t0 = time.time()
    cands, _seen = S3.draw(rng, S3.N_RANDOM)
    print('  recovered %d sampled algorithms in %.1f s'
          % (len(cands), time.time() - t0), flush=True)

    sm = pd.read_csv(os.path.join(ROOTOUT, 'nnfx', 'src3_sample.csv'))
    assert len(sm) == len(cands), \
        'src3_sample.csv has %d rows, the draw gave %d' % (len(sm), len(cands))
    od = sm.obj_discovery.to_numpy(float)

    # CHECK 1: the recovered tuples reproduce the saved objectives
    chk = np.random.default_rng(7).choice(len(cands), 300, replace=False)
    bad = []
    for i in chk:
        o, _n, _t = P.fast_obj(S3.mkcand(cands[int(i)]), disc, S3.DISC_YEARS)
        if not abs(o - od[int(i)]) < 1e-9:
            bad.append((int(i), o, od[int(i)]))
    assert not bad, ('the recovered draw is NOT Source 3\'s: %d of 300 '
                     'objectives differ, first %s' % (len(bad), bad[:3]))
    print('  CHECK 1 OK: 300 of the recovered tuples reproduce '
          'src3_sample.csv obj_discovery to 1e-9', flush=True)

    # the local search, replayed from the same rng stream
    order_i = np.argsort(-od)
    starts = [(cands[i], od[i]) for i in order_i[:S3.TOP_LOCAL]]
    best_local, used, evaluated = replay_local(starts, disc, S3.DISC_YEARS,
                                               rng, verbose=verbose)
    got = float(max(o for _t, o in best_local))
    assert abs(got - BEST_LOCAL_DISC) < 1e-9, \
        ('the replayed local search ended on %.12f, SOURCE3.md reports %.12f '
         '-- the replay is not faithful' % (got, BEST_LOCAL_DISC))
    print('  CHECK 2 OK: the replayed local search reproduces '
          'best discovery +%.6f on %d evaluations' % (got, used), flush=True)

    # the union, sample first so sample indices stay 0..199999
    rows = list(cands)
    src = [0] * len(cands)
    have = set(P.cand_id(S3.mkcand(t)) for t in cands)
    for u in evaluated:
        k = P.cand_id(S3.mkcand(u))
        if k in have:
            continue
        have.add(k)
        rows.append(u); src.append(1)
    idx = np.zeros((len(rows), len(P.SLOTS)), np.int16)
    for j, t in enumerate(rows):
        for k, sl in enumerate(P.SLOTS):
            idx[j, k] = fwd[sl][t[k]]
    np.savez_compressed(CAND_NPZ, idx=idx, src=np.asarray(src, np.int8),
                        obj_discovery=od, n_sample=len(cands),
                        n_local_eval=used, best_local_disc=got,
                        space=json.dumps({sl: [list(o) for o in S3.SPACE[sl]]
                                          for sl in P.SLOTS}))
    print('  %d algorithms in the bank list: %d sampled, %d from the local '
          'search that the sample did not already hold -> %s'
          % (len(rows), len(cands), len(rows) - len(cands), CAND_NPZ),
          flush=True)
    return len(rows)


def load():
    """-> (list of 5-tuples, src array). The one reader everything uses."""
    z = np.load(CAND_NPZ, allow_pickle=False)
    sp = json.loads(str(z['space']))
    idx = z['idx']
    cands = [tuple((sp[sl][int(idx[j, k])][0], sp[sl][int(idx[j, k])][1])
                   for k, sl in enumerate(P.SLOTS))
             for j in range(len(idx))]
    return cands, z['src'], dict(n_sample=int(z['n_sample']),
                                 n_local_eval=int(z['n_local_eval']),
                                 obj_discovery=z['obj_discovery'])


if __name__ == '__main__':
    t0 = time.time()
    n = build()
    print('DONE nnfxcands: %d algorithms in %.1f min'
          % (n, (time.time() - t0) / 60), flush=True)
