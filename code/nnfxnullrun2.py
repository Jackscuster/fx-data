"""THE MATCHED NULL FOR FAMILIES (d) AND (e). PROTOCOL.md A10 and A11.

The 20 null runs launched at 19:41 build families a, b and c. Families d and
e were declared at 20:12 and 20:10, after that chain was already running, so
they get their own chain over THE SAME 20 SCRAMBLED WORLDS -- the seeds are
700000 + run and nnfxsrc3.zero_edge_frames is deterministic given a seed, so
this rebuilds the identical worlds rather than drawing 20 new ones. That
matters: d's construction reads the null run's OWN a/b/c sweep to pick its
winner, which only makes sense if it is the same world.

WHY THE BANK IS BUILT AGAIN RATHER THAN REUSED. 20 null banks are 6.8 GB and
this disk has about 3 GB free, so chain 1 never wrote them. Rebuilding one
costs the same 29 minutes it cost the first time. That is the price of the
disk, stated.

THE CONSTRUCTION FUNCTIONS ARE IMPORTED, NEVER COPIED -- nnfxcomb.build_d and
nnfxcell4.build_e are the same code that produced the real numbers. A null
that is built by a second implementation of the same rule is not a null of
that rule.

RESUMABLE BY RUN.
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
import nnfxnullrun as NR
import nnfxcomb as CB
import nnfxcell4 as C4
import l2sweep as S

NDIR = NR.NDIR


def one(k, verbose=True):
    S.load_costs(os.environ.get('FX_COST_TABLE',
                                os.path.join(ROOTOUT, 'cost_table_h22.csv')))
    S3.init_space(); S3.self_check()
    f_d = os.path.join(NDIR, 'comb_%03d.csv' % k)
    f_e = os.path.join(NDIR, 'cell4_%03d.csv' % k)
    if os.path.exists(f_d) and os.path.exists(f_e):
        print('  null2 %d already on disk' % k, flush=True)
        return
    f_abc = os.path.join(NDIR, 'books_%03d.csv' % k)
    assert os.path.exists(f_abc), \
        ('null2 run %d needs chain 1\'s books_%03d.csv to check that this '
         'world is the SAME world, and it is not on disk' % (k, k))
    chain1 = pd.read_csv(f_abc)
    t0 = time.time()
    seed = NR.SEED_BASE + k
    tag = 'bnull2_%03d' % k
    F = S3.zero_edge_frames(seed)
    S3.check_world(F)
    P.set_world(tag, F)
    try:
        disc, _repl = S3.pair_sets()
        pairs = list(S.all_pairs())
        rng = np.random.default_rng(seed)
        cands, _seen = S3.draw(rng, S3.N_RANDOM)
        od = S3.obj_many(cands, disc, S3.DISC_YEARS,
                         log_every=(50000 if verbose else 0), tag=tag)
        order = np.argsort(-od)
        starts = [(cands[i], od[i]) for i in order[:S3.TOP_LOCAL]]
        _b, used, evaluated = CL.replay_local(starts, disc, S3.DISC_YEARS,
                                              rng, verbose=False)
        have = set(P.cand_id(S3.mkcand(t)) for t in cands)
        allc = list(cands)
        for u in evaluated:
            kk = P.cand_id(S3.mkcand(u))
            if kk in have:
                continue
            have.add(kk); allc.append(u)
        print('  %s: %d algorithms, %.1f min'
              % (tag, len(allc), (time.time() - t0) / 60), flush=True)
        bank = NR.bank_in_memory(allc, pairs, verbose=verbose, tag=tag)
        W = BO.World(pairs)
        D = BK.declared_sleeves()

        # ---- FAMILY (e) FIRST, AND WRITTEN BEFORE (d) IS ATTEMPTED.
        # On 25 Nov this ran the other way round and all 20 runs died inside
        # build_d, which threw away family e too -- and e is the only book
        # anywhere near Jack's 12%. e reads the bank and nothing else, so it
        # has no business waiting behind d's winner lookup.
        if not os.path.exists(f_e):
            re_ = C4.build_e(bank, allc, W, pairs, verbose=False)
            Xe = pd.DataFrame(re_); Xe['run'] = k; Xe['seed'] = seed
            Xe.to_csv(f_e, index=False)
            print('  null2 %d family e: %d rows, %.1f min'
                  % (k, len(Xe), (time.time() - t0) / 60), flush=True)

        # ---- FAMILY (d). A11 picks its winner by R_per_dip averaged over
        # the rotations, so the sweep it reads must CARRY a dip. Chain 1's
        # books_%03d.csv is light() and does not, so the b/c sweep is rebuilt
        # here at the 'mid' tier on this same world. The assertion below is
        # the point of doing it rather than trusting it: same seed, same
        # zero_edge_frames, so every R must come back identical to chain 1's.
        if not os.path.exists(f_d):
            rows = BO.build(bank, allc, W, declared=D, light_only='mid')
            sweep = pd.DataFrame(rows)
            kcols = ['rotation', 'family', 'K', 'share', 'mode']
            # THE CHECK IS ON FAMILIES b AND c, WHICH ARE THE ONLY TWO
            # pick_winner READS. a_declared is deliberately left out of the
            # row-count assertion: its K is not a setting but a COUNT of how
            # many of the 18 declared algorithms were admitted, so keying it
            # on K is brittle by nature. Within one world it should still
            # agree, so it is checked and PRINTED rather than made fatal --
            # a mismatch there must not throw away 40 minutes of bank over
            # something family d never looks at.
            BC = ('b_per_pair', 'c_all_pairs')
            c1 = chain1[chain1.family.isin(BC)]
            sw = sweep[sweep.family.isin(BC)]
            j = c1.merge(sw, on=kcols, suffixes=('_c1', '_c2'))
            assert len(j) == len(c1), \
                ('rebuilt sweep has %d of chain 1\'s %d b/c rows on run %d'
                 % (len(j), len(c1), k))
            dR = float(np.nanmax(np.abs(j.R_c1 - j.R_c2)))
            assert dR < 1e-6, \
                ('run %d is NOT chain 1\'s world: worst R difference over '
                 '%d b/c book cells is %.3e' % (k, len(j), dR))
            ja = chain1[chain1.family == 'a_declared'].merge(
                sweep[sweep.family == 'a_declared'], on=kcols,
                suffixes=('_c1', '_c2'))
            dA = (float(np.nanmax(np.abs(ja.R_c1 - ja.R_c2)))
                  if len(ja) else np.nan)
            print('  null2 %d sweep matches chain 1 to %.2e over %d b/c '
                  'cells (a_declared: %d rows joined, worst %.2e), %.1f min'
                  % (k, dR, len(j), len(ja), dA, (time.time() - t0) / 60),
                  flush=True)
            rd = CB.build_d(bank, allc, W, pairs, D, sweep, verbose=False)
            Xd = pd.DataFrame(rd); Xd['run'] = k; Xd['seed'] = seed
            Xd.to_csv(f_d, index=False)
        print('  null2 %d DONE %.1f min'
              % (k, (time.time() - t0) / 60), flush=True)
    finally:
        P.set_world('real')
        P.drop_world(tag)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', type=int, required=True)
    a = ap.parse_args()
    one(a.run)
