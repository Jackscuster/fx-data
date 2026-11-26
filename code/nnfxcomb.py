"""FAMILY (d) COMBINED -- PROTOCOL.md AMENDMENT 1, A11.

Item 3d: "a plus the best of b and c". A11 fixes the choice as a PROCEDURE so
the null can apply the identical one to its own numbers:

  best K per family  = the K with the highest scoring-window return per dip
                       AVERAGED OVER THE TWO ROTATIONS
  the winner         = whichever of b or c has the higher averaged R/dip at
                       its own best K
  d                  = book (a)'s admitted sleeves UNION the winner's sleeves
                       at that K, equal risk 1/N over the union

A sleeve in both halves is held ONCE. The union is of sleeves, not a sum of
two books.

Importable: pick_winner() takes any sweep table -- real or a null run's -- so
the second null chain calls the same function on the same shape of input.
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
import nnfxrep as RP
import l2sweep as S

OUT = os.path.join(ROOTOUT, 'nnfx', 'books')


def pick_winner(sweep, share, mode, metric='R_per_dip'):
    """A11 steps 1-3. -> (family, K, averaged metric). `sweep` needs columns
    rotation, family, K, share, mode and the metric."""
    best = {}
    for fam in ('b_per_pair', 'c_all_pairs'):
        q = sweep[(sweep.family == fam) & (sweep['share'] == share)
                  & (sweep['mode'] == mode)]
        if not len(q):
            continue
        av = q.groupby('K')[metric].mean()          # average over rotations
        av = av[np.isfinite(av)]
        if not len(av):
            continue
        best[fam] = (int(av.idxmax()), float(av.max()))
    if not best:
        return None, None, np.nan
    fam = max(best, key=lambda f: best[f][1])
    return fam, best[fam][0], best[fam][1]


def build_d(bank, cands, W, pairs, declared, sweep, verbose=True):
    """-> rows for family d, every share and mode, both rotations."""
    col = {p: i for i, p in enumerate(pairs)}
    rows = []
    for share in BO.SHARE_GRID:
        for mode in ('separate', 'voting'):
            fam, K, avmetric = pick_winner(sweep, share, mode)
            if fam is None:
                continue
            # B4's count knob for family d IS the winner's K: A11 leaves d
            # without a grid of its own, but the count that selects half of it
            # is K, so d is built at K one grid step down and one up too and
            # B4 is read off those. Blank would have been the easy answer and
            # the wrong one.
            grid = list(BO.K_PER_PAIR if fam == 'b_per_pair' else BO.K_ALL)
            ki = grid.index(K)
            ks = [K]
            if ki > 0:
                ks.append(grid[ki - 1])
            if ki + 1 < len(grid):
                ks.append(grid[ki + 1])
            for Kuse in ks:
              for (rot, aw, sw) in BO.ROTATIONS:
                  smask = W.mask(BK.H1Y if sw == 'h1' else BK.H2Y)
                  seen = set()
                  acc = BO.Acc(W)
                  # --- book (a)'s admitted sleeves
                  for (nm, C, _src, _cp) in declared:
                      for p in pairs:
                          d = P.fast_per_pair(C, p, BK.PERIODS)[aw]
                          if not BK.adm_ok(dict(d)):
                              continue
                          if not (d['best_trade'] / d['R'] < share
                                  if d['R'] > 0 else False):
                              continue
                          key = (P.cand_id(C), p)
                          if key in seen:
                              continue
                          seen.add(key); acc.add(C, p, nm)
                  n_a = acc.n
                  # --- the winner's sleeves at its best K
                  mem, _aw = RP.members_of(bank, pairs, rot, fam, Kuse, share)
                  for (j, p) in mem:
                      C = S3.mkcand(cands[j])
                      key = (P.cand_id(C), p)
                      if key in seen:
                          continue
                      seen.add(key); acc.add(C, p, 'S%d' % j)
                  sep, vote, cs, cv = acc.series()
                  a = sep if mode == 'separate' else vote
                  r = dict(rotation=rot, admit_window=aw, score_window=sw,
                           family='d_combined', K=Kuse, share=share, mode=mode,
                           sleeves=acc.n, winner_family=fam, winner_K=K,
                           is_central_K=int(Kuse == K),
                           winner_avg_R_per_dip=avmetric,
                           sleeves_from_a=n_a, sleeves_from_winner=acc.n - n_a,
                           cost_sep_total=float(cs[smask].sum()),
                           cost_vote_total=float(cv[smask].sum()))
                  r.update(BO.light(a, smask))
                  r.update(BO.full(a, W.dates, smask))
                  rows.append(r)
            if verbose:
                print('    d: share=%s %s -> winner %s K=%d (avg R/dip %+.3f)'
                      % (share, mode, fam, K, avmetric), flush=True)
    return rows


def run(verbose=True):
    S.load_costs(os.environ.get('FX_COST_TABLE',
                                os.path.join(ROOTOUT, 'cost_table_h22.csv')))
    S3.init_space()
    pairs, bank = BK.load_bank('real')
    cands, _src, _m = CL.load()
    W = BO.World(pairs)
    D = BK.declared_sleeves()
    sweep = pd.read_csv(os.path.join(OUT, 'books_full_real.csv'))
    t0 = time.time()
    rows = build_d(bank, cands, W, pairs, D, sweep, verbose=verbose)
    X = pd.DataFrame(rows)
    X['B2'] = ((X.R_ex1 > 0) & (X.R_ex5 > 0)).astype(int)
    X['B3'] = (X.R > 0).astype(int)
    X['B1'] = np.nan            # A11: not matched by the 19:41 nulls
    X['B4'] = np.nan
    for key, g in X.groupby(['rotation', 'share', 'mode'], dropna=False):
        X.loc[g.index, 'B4'] = int((g.R > 0).all())
    X['B5'] = (X.b5_pct_per_year >= 12.0).astype(int)
    X.to_csv(os.path.join(OUT, 'books_combined.csv'), index=False)
    print('  books_combined.csv %d rows in %.1f min'
          % (len(X), (time.time() - t0) / 60), flush=True)
    return X


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', action='store_true')
    ap.parse_args()
    run()
