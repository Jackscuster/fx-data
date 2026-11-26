"""FAMILY (e) -- THE FOUR-CELL ROTATION APPLIED TO A BOOK.

PROTOCOL.md AMENDMENT 1, A4 and A10. A10 fixes every rule below and was
written at 20:10 EST on 25 November, before this file was run.

Select on 15 pairs in one six-year window; trade on the 13 OTHER pairs in the
OTHER six-year window. No shared pair and no shared year, so this does not
need a pair's fit to carry at all -- only for an algorithm chosen on one set
of currencies in one decade to work on different currencies in a different
decade. That is what Source 3 measured for a single algorithm; this asks it
for a book.

NO PER-PAIR ADMISSION ON THE SCORING SIDE. Choosing which of the 13 pairs to
trade would mean looking at them. Each selected algorithm trades all 13.

B1 IS LEFT BLANK AND THAT IS DELIBERATE. The 20 matched null runs were
already running when A10 was declared and they do not build this family, so
nothing here is called a passer. A matched null is the next armed stage.
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
import l2sweep as S

OUT = os.path.join(ROOTOUT, 'nnfx', 'books')
K_GRID = BO.K_ALL


def build_e(bank, cands, W, pairs, verbose=True):
    """Family (e) on ANY bank -- real or a scrambled world's.

    EXTRACTED SO THE NULL CANNOT DRIFT FROM THE REAL RUN. A null built by a
    second implementation of the same rule is not a null of that rule.
    """
    col = {p: i for i, p in enumerate(pairs)}
    cellA, cellB = BO.cells()          # 15 without JPY/CHF, 13 with
    assert len(cellA) == 15 and len(cellB) == 13
    idxA = [col[p] for p in cellA]
    idxB = [col[p] for p in cellB]
    mh1 = W.mask(BK.H1Y); mh2 = W.mask(BK.H2Y)
    rows = []
    t0 = time.time()
    DIRS = (('fwd', cellA, idxA, 'h1', cellB, 'h2'),
            ('rev', cellB, idxB, 'h2', cellA, 'h1'))
    for (tag, selp, seli, selw, scop, scow) in DIRS:
        for share in BO.SHARE_GRID:
            adm = BO.admitted(bank, selw, share)
            Rsel = bank['%s__R' % selw]
            # rank by total selection-window R over the SELECTION pairs the
            # algorithm was admitted on -- family (c)'s rule, restricted
            sub = adm[:, seli]
            sc = np.where(sub, Rsel[:, seli], 0.0).sum(axis=1)
            ok = np.nonzero(sub.sum(axis=1) > 0)[0]
            ranked = ok[np.argsort(-sc[ok])][:max(K_GRID)]
            accA = BO.Acc(W); accB = BO.Acc(W)
            for i, j in enumerate(ranked):
                C = S3.mkcand(cands[j])
                for p in cellA:
                    accA.add(C, p, 'S%d' % j)
                for p in cellB:
                    accB.add(C, p, 'S%d' % j)
                if (i + 1) not in K_GRID:
                    continue
                sA, vA, csA, cvA = accA.series()
                sB, vB, csB, cvB = accB.series()
                for cellname, s_, v_, cs_, cv_ in (('15pairs', sA, vA, csA, cvA),
                                                   ('13pairs', sB, vB, csB, cvB)):
                    for yrname, m in (('2005_2010', mh1), ('2011_2015', mh2)):
                        for mode, a in (('separate', s_), ('voting', v_)):
                            is_sel = (cellname == ('15pairs' if tag == 'fwd'
                                                   else '13pairs')
                                      and yrname == ('2005_2010'
                                                     if selw == 'h1'
                                                     else '2011_2015'))
                            is_cross = (cellname == ('13pairs' if tag == 'fwd'
                                                     else '15pairs')
                                        and yrname == ('2011_2015'
                                                       if scow == 'h2'
                                                       else '2005_2010'))
                            r = dict(direction=tag, family='e_fourcell',
                                     select_pairs=('15pairs' if tag == 'fwd'
                                                   else '13pairs'),
                                     select_years=selw, cell_pairs=cellname,
                                     cell_years=yrname, K=i + 1, share=share,
                                     mode=mode,
                                     sleeves=(accA.n if cellname == '15pairs'
                                              else accB.n),
                                     is_selection_cell=int(is_sel),
                                     is_true_cross=int(is_cross),
                                     cost_sep_total=float(cs_[m].sum()),
                                     cost_vote_total=float(cv_[m].sum()))
                            r.update(BO.light(a, m))
                            r.update(BO.full(a, W.dates, m))
                            rows.append(r)
            if verbose:
                print('    %s share=%s done, %.1f min'
                      % (tag, share, (time.time() - t0) / 60), flush=True)
    return rows


def run(verbose=True):
    S.load_costs(os.environ.get('FX_COST_TABLE',
                                os.path.join(ROOTOUT, 'cost_table_h22.csv')))
    S3.init_space()
    pairs, bank = BK.load_bank('real')
    cands, _src, _m = CL.load()
    W = BO.World(pairs)
    rows = build_e(bank, cands, W, pairs, verbose=verbose)
    t0 = time.time()
    D = pd.DataFrame(rows)
    D['B2'] = ((D.R_ex1 > 0) & (D.R_ex5 > 0)).astype(int)
    D['B3'] = (D.R > 0).astype(int)
    D['B1'] = np.nan          # A10: not matched, left blank on purpose
    # B4 on the K neighbours within the same cell
    D['B4'] = np.nan
    for key, g in D.groupby(['direction', 'cell_pairs', 'cell_years',
                             'share', 'mode'], dropna=False):
        g = g.sort_values('K'); ks = list(g.K); rs = dict(zip(g.K, g.R))
        for i, k in enumerate(ks):
            nb = [rs[k]]
            if i > 0:
                nb.append(rs[ks[i - 1]])
            if i + 1 < len(ks):
                nb.append(rs[ks[i + 1]])
            D.loc[(D.direction == key[0]) & (D.cell_pairs == key[1])
                  & (D.cell_years == key[2]) & (D['share'] == key[3])
                  & (D['mode'] == key[4]) & (D.K == k), 'B4'] = \
                int(all(v > 0 for v in nb))
    D['B5'] = ((D.b5_pct_per_year >= 12.0)).astype(int)
    D.to_csv(os.path.join(OUT, 'books_fourcell.csv'), index=False)
    print('  books_fourcell.csv %d rows in %.1f min'
          % (len(D), (time.time() - t0) / 60), flush=True)
    return D


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', action='store_true')
    a = ap.parse_args()
    run()
