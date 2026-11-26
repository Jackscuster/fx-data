"""ONE FULLY MATCHED NULL RUN. PROTOCOL.md AMENDMENT 1, A5 and A6.2.

B1 asks whether a book beats the 95th percentile of THE SAME BOOK BUILT FROM
THE NULL. A null that does not repeat the SELECTION measures nothing about
selection, so this repeats all of it on a scrambled world:

  1. block-shuffle every pair's bars, 20-day blocks within the calendar year,
     each block's direction flipped with probability one half  (nnfxsrc3)
  2. draw 200,000 complete algorithms                          (nnfxsrc3.draw)
  3. the discovery objective on the null's 15 discovery pairs, 2005-2010
  4. the local search from the top 200, at the same cap
  5. the sleeve bank: every algorithm from 2 and 4, on all 28 pairs, both windows
  6. item 2's pair-fit statistics
  7. every book of item 3, both rotations, every K, every share threshold

Step 4 is what the first draft of the amendment proposed to skip. It is not
skipped: measured at 0.149 ms per candidate-pair, a matched run costs about
45 minutes, and that is affordable.

SEEDS ARE 700000 + run, DISTINCT from Source 3's own nulls (900000 + run), so
these are 20 fresh worlds and not a re-reading of worlds already looked at.

RESUMABLE BY RUN. A killed job costs that run, not the batch.
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
import nnfxbooks as BO
import nnfxfit as FT
import l2sweep as S

NDIR = os.path.join(ROOTOUT, 'nnfx', 'books', 'null')
os.makedirs(NDIR, exist_ok=True)
SEED_BASE = 700000


def bank_in_memory(cands, pairs, verbose=False, tag=''):
    """The sleeve bank for the current world, in memory. Never written.

    nnfxsleeves.run_shard writes an npz; 20 null banks would be 6.8 GB on a
    disk with 3.9 GB free, and nothing downstream needs them after the
    statistics are taken.
    """
    n = len(cands)
    A = {'%s__%s' % (w, m):
         np.zeros((n, len(pairs)), np.int32 if m == 'trades' else np.float32)
         for w, _y in BK.PERIODS for m in BK.METRICS}
    t0 = time.time()
    for pi, p in enumerate(pairs):
        P.base_dict(p, int(P.RISK['atr_len']))
        for j, t in enumerate(cands):
            r = P.fast_per_pair(S3.mkcand(t), p, BK.PERIODS)
            for w, _y in BK.PERIODS:
                d = r[w]
                A['%s__R' % w][j, pi] = d['R']
                A['%s__R_ex_best_day' % w][j, pi] = d['R_ex_best_day']
                A['%s__best_trade' % w][j, pi] = d['best_trade']
                A['%s__trades' % w][j, pi] = d['trades']
        if verbose:
            print('    %s bank pair %d/%d %s, %.1f min'
                  % (tag, pi + 1, len(pairs), p, (time.time() - t0) / 60),
                  flush=True)
    return A


def one(k, verbose=True):
    S.load_costs(os.environ.get('FX_COST_TABLE',
                                os.path.join(ROOTOUT, 'cost_table_h22.csv')))
    S3.init_space(); S3.self_check()
    f_book = os.path.join(NDIR, 'books_%03d.csv' % k)
    f_fit = os.path.join(NDIR, 'fit_%03d.csv' % k)
    if os.path.exists(f_book) and os.path.exists(f_fit):
        print('  null %d already on disk' % k, flush=True)
        return
    t0 = time.time()
    seed = SEED_BASE + k
    tag = 'bnull%03d' % k
    F = S3.zero_edge_frames(seed)
    S3.check_world(F)
    P.set_world(tag, F)
    try:
        disc, _repl = S3.pair_sets()
        pairs = list(S.all_pairs())
        rng = np.random.default_rng(seed)
        cands, _seen = S3.draw(rng, S3.N_RANDOM)
        od = S3.obj_many(cands, disc, S3.DISC_YEARS,
                         log_every=(50000 if verbose else 0),
                         tag='%s discovery' % tag)
        print('  %s: discovery done %.1f min, best %+.4f'
              % (tag, (time.time() - t0) / 60, float(np.nanmax(od))), flush=True)
        order = np.argsort(-od)
        starts = [(cands[i], od[i]) for i in order[:S3.TOP_LOCAL]]
        _best, used, evaluated = CL.replay_local(starts, disc, S3.DISC_YEARS,
                                                 rng, verbose=False)
        have = set(P.cand_id(S3.mkcand(t)) for t in cands)
        allc = list(cands)
        for u in evaluated:
            kk = P.cand_id(S3.mkcand(u))
            if kk in have:
                continue
            have.add(kk); allc.append(u)
        print('  %s: local search %d evaluations, %d algorithms in the bank '
              'list, %.1f min' % (tag, used, len(allc),
                                  (time.time() - t0) / 60), flush=True)
        bank = bank_in_memory(allc, pairs, verbose=verbose, tag=tag)
        print('  %s: bank done %.1f min' % (tag, (time.time() - t0) / 60),
              flush=True)
        # item 2
        frows, pooled = [], []
        for sh in BO.SHARE_GRID:
            a, b = FT.fit_stats(pairs, bank, share=sh, tag=tag, run=k)
            a['share'] = sh
            for x in b:
                x['share'] = sh
            frows.append(a); pooled += b
        FF = pd.concat(frows, ignore_index=True)
        FF.to_csv(f_fit, index=False)
        pd.DataFrame(pooled).to_csv(
            os.path.join(NDIR, 'fitpooled_%03d.csv' % k), index=False)
        # item 3
        W = BO.World(pairs)
        D = BK.declared_sleeves()
        rows = BO.build(bank, allc, W, declared=D, light_only=True)
        B = pd.DataFrame(rows)
        B['run'] = k; B['seed'] = seed; B['tag'] = tag
        B['n_algorithms'] = len(allc)
        B.to_csv(f_book, index=False)
        print('  null %d DONE %.1f min: %d book rows, %d fit rows'
              % (k, (time.time() - t0) / 60, len(B), len(FF)), flush=True)
    finally:
        P.set_world('real')
        P.drop_world(tag)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', type=int, required=True)
    a = ap.parse_args()
    one(a.run)
