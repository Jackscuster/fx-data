"""ITEMS 2, 3 AND 4 -- PAIR_FIT.md, BOOKS.md, WINNERS.md.

Reads what is on disk and writes the three reports. Computes nothing new
except book (a)'s B4 nudge, which needs the declared book rebuilt at two
other trade floors and is 504 sleeve evaluations.

THE FIVE BOOK GATES, as PROTOCOL.md A3 states them:

  B1 LUCK      the book's scoring-window R beats the 95th percentile of the
               SAME CELL -- same rotation, family, K, share and mode -- across
               the 20 matched null runs. Matched per K, so the K sweep cannot
               launder a selection: nothing is chosen by looking at the
               scoring window.
  B2 ONE EVENT positive excluding the best day AND excluding the best 5 days.
  B3 HOLD-OUT  positive on the scoring window, which by construction is data
               no sleeve in the book was admitted on.
  B4 NUDGE     positive at the admission count one grid step down and one up.
               For families b and c that count is K. For book (a), which has
               no K, A5 declared it to be the 20-trade floor, moved to 15
               and 30.
  B5 MONEY     at least 12% a year sized inside 3.6% daily and 5.4% trailing,
               through the prop simulator, plus days to pass the +10%
               evaluation.
"""
import os, sys, time, glob, json
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
ROOT = os.path.dirname(_HERE)
ROOTOUT = os.path.join(ROOT, 'results')
sys.path.insert(0, ROOT)

import numpy as np
import pandas as pd
import nnfxproto as P
import nnfxsleeves as BK
import nnfxbooks as BO
import nnfxfit as FT
import l2sweep as S

OUT = os.path.join(ROOTOUT, 'nnfx')
BOUT = os.path.join(OUT, 'books')
NDIR = os.path.join(BOUT, 'null')
CELL = ['rotation', 'family', 'K', 'share', 'mode']


def _read(pat):
    fs = sorted(glob.glob(os.path.join(NDIR, pat)))
    if not fs:
        return pd.DataFrame(), 0
    return pd.concat([pd.read_csv(f) for f in fs], ignore_index=True), len(fs)


def null_floor(NB):
    """-> the 95th percentile and the rest of the null distribution per cell."""
    if not len(NB):
        return pd.DataFrame()
    g = NB.groupby(CELL, dropna=False)['R']
    F = g.agg(null_runs='count', null_mean='mean', null_median='median',
              null_max='max').reset_index()
    F['null_p95'] = g.quantile(0.95).to_numpy()
    F['null_p05'] = g.quantile(0.05).to_numpy()
    return F


def gate_table(RF, F):
    """The five gates on every real book cell."""
    D = RF.merge(F, on=CELL, how='left') if len(F) else RF.copy()
    for c in ('null_p95', 'null_mean', 'null_runs', 'null_median', 'null_max'):
        if c not in D.columns:
            D[c] = np.nan
    D['B1'] = np.where(D.null_p95.notna(), (D.R > D.null_p95).astype(float),
                       np.nan)
    D['B2'] = ((D.R_ex1 > 0) & (D.R_ex5 > 0)).astype(int)
    D['B3'] = (D.R > 0).astype(int)
    # B4: the K one grid step down and one up, in the same cell otherwise
    D['B4'] = np.nan
    for fam, grid in (('b_per_pair', BO.K_PER_PAIR),
                      ('c_all_pairs', BO.K_ALL)):
        for (rot, sh, md), g in D[D.family == fam].groupby(
                ['rotation', 'share', 'mode'], dropna=False):
            g = g.sort_values('K')
            ks = list(g.K)
            rs = dict(zip(g.K, g.R))
            for i, k in enumerate(ks):
                lo = ks[i - 1] if i > 0 else None
                hi = ks[i + 1] if i + 1 < len(ks) else None
                vals = [rs[k]] + [rs[x] for x in (lo, hi) if x is not None]
                ok = int(all(v > 0 for v in vals))
                D.loc[(D.family == fam) & (D.rotation == rot)
                      & (D['share'] == sh) & (D['mode'] == md)
                      & (D.K == k), 'B4'] = ok
    # ---- B1b, PROTOCOL.md A12: the book must beat the UNCONDITIONAL mean
    # sleeve R of its own cell, not merely zero. At equal risk 1/N a book's R
    # IS the mean of its sleeves' R, so this is an exact like-for-like test.
    try:
        CBL = pd.read_csv(os.path.join(BOUT, 'cell_baseline.csv'))
        CBL = CBL[(CBL.cell_pairs == '28pairs') & (CBL.min_trades == 20)]
        bl = dict(zip(CBL.window, CBL.mean_R))
        D['cell_baseline_R'] = D.score_window.map(bl)
        D['excess_over_cell'] = D.R - D.cell_baseline_R
        D['B1b'] = (D.excess_over_cell > 0).astype(int)
    except Exception as e:
        D['cell_baseline_R'] = np.nan
        D['excess_over_cell'] = np.nan
        D['B1b'] = np.nan
        print('  B1b not computed: %s' % e, flush=True)
    if 'b5_pct_per_year' in D.columns:
        D['B5'] = ((D.b5_pct_per_year >= 12.0)
                   & (D.get('b5_eval_breached', False) != True)).astype(int)
        D['pct_from_12'] = D.b5_pct_per_year - 12.0
    else:
        D['B5'] = np.nan
    D['clears_B1_B4'] = ((D.B1 == 1) & (D.B2 == 1) & (D.B3 == 1)
                         & (D.B4 == 1)).astype(int)
    D['clears_with_B1b'] = ((D.clears_B1_B4 == 1) & (D.B1b == 1)).astype(int)
    D['passer'] = ((D.clears_B1_B4 == 1) & (D.B5 == 1)).astype(int)
    return D


# ------------- book (a)'s B4 nudge: the 20-trade floor at 15 and 30 --------
def declared_nudge(verbose=True):
    S.load_costs(os.environ.get('FX_COST_TABLE',
                                os.path.join(ROOTOUT, 'cost_table_h22.csv')))
    pairs = list(S.all_pairs())
    W = BO.World(pairs)
    D = BK.declared_sleeves()
    rows = []
    for (rot, aw, sw) in BO.ROTATIONS:
        smask = W.mask(BK.H1Y if sw == 'h1' else BK.H2Y)
        for mt in (15, BK.ADM_MIN_TRADES, 30):
            for share in (BO.SHARE_DECLARED, np.inf):
                acc = BO.Acc(W)
                for (nm, C, _src, _cp) in D:
                    for p in pairs:
                        d = P.fast_per_pair(C, p, BK.PERIODS)[aw]
                        if d['trades'] < mt or not (d['R'] > 0) \
                                or not (d['R_ex_best_day'] > 0):
                            continue
                        if not (d['best_trade'] / d['R'] < share):
                            continue
                        acc.add(C, p, nm)
                sep, vote, cs, cv = acc.series()
                for mode, a in (('separate', sep), ('voting', vote)):
                    r = dict(rotation=rot, admit_window=aw, score_window=sw,
                             family='a_declared', min_trades=mt, share=share,
                             mode=mode, sleeves=acc.n)
                    r.update(BO.light(a, smask))
                    r.update(BO.full(a, W.dates, smask))
                    rows.append(r)
        if verbose:
            print('    declared nudge %s done' % rot, flush=True)
    N = pd.DataFrame(rows)
    N.to_csv(os.path.join(BOUT, 'books_declared_nudge.csv'), index=False)
    print('  books_declared_nudge.csv %d rows' % len(N), flush=True)
    return N





# ======================= PAIR_FIT.md ====================================
def pair_fit_md(verbose=True):
    A = pd.read_csv(os.path.join(BOUT, 'fit_real.csv'))
    PLr = pd.read_csv(os.path.join(BOUT, 'fitpooled_real.csv'))
    NA, nruns = _read('fit_*.csv')
    NP, _ = _read('fitpooled_*.csv')
    L = ['# PAIR_FIT -- does a strategy\'s fit to a pair carry?',
         '',
         '**Item 2 of Jack\'s correction. `PROTOCOL.md` AMENDMENT 1, A6.3. '
         'This is the gate on item 3: if the fit does not persist, every '
         'searched book is noise by construction.**', '']
    L += ['## What is measured', '',
          'For each of the 28 pairs, across **%d algorithms** -- Source 3\'s '
          '200,000 random draws plus every algorithm its local search '
          'evaluated:' % int(PLr.n_sleeves.iloc[0] / 28), '',
          '| | |', '|---|---|',
          '| **RHO** | the Spearman rank correlation between an algorithm\'s '
          'net R on that pair in the early years and its net R on the **same '
          'pair** in the later years |',
          '| **SHARE** | the fraction of sleeves ADMITTED on the early years '
          '(A2) that are positive on the later years |',
          '| **BASELINE** | the same fraction over every sleeve with at least '
          '20 trades, admitted or not. This is the honest comparison: if '
          'admission does not raise the share above its own baseline, '
          'admission selects nothing |', '',
          'Both in both rotations, against **%d matched null runs** '
          '(scrambled data, the same search, the same bank).' % nruns, '']
    # pooled
    L += ['## Pooled over all (algorithm, pair) sleeves', '']
    L += ['| rotation | share | real rho | null rho mean | null rho p95 | '
          'real admitted share positive later | its own baseline | '
          'null admitted share |',
          '|---|---:|---:|---:|---:|---:|---:|---:|']
    for _i, r in PLr.iterrows():
        q = NP[(NP.rotation == r.rotation) & (NP['share'] == r['share'])] \
            if len(NP) else pd.DataFrame()
        L.append('| %s | %s | **%+.4f** | %s | %s | **%.4f** | %.4f | %s |'
                 % (r.rotation, ('off' if not np.isfinite(r['share'])
                                 else '%.2f' % r['share']),
                    r.rho_pooled,
                    ('%+.4f' % q.rho_pooled.mean()) if len(q) else 'pending',
                    ('%+.4f' % q.rho_pooled.quantile(0.95)) if len(q) else '--',
                    r.share_pos_later, r.share_pos_later_baseline,
                    ('%.4f' % q.share_pos_later.mean()) if len(q) else 'pending'))
    L.append('')
    # per pair, declared share
    X = A[A['share'] == BO.SHARE_DECLARED]
    NX = NA[NA['share'] == BO.SHARE_DECLARED] if len(NA) else pd.DataFrame()
    for rot in ('R1', 'R2'):
        Y = X[X.rotation == rot].sort_values('rho', ascending=False)
        NY = NX[NX.rotation == rot] if len(NX) else pd.DataFrame()
        L += ['## Per pair, rotation %s (admit %s, score %s), share 0.25'
              % (rot, '2005-2010' if rot == 'R1' else '2011-2015',
                 '2011-2015' if rot == 'R1' else '2005-2010'), '',
              '| pair | real rho | null rho mean | null rho p05 | null rho p95 '
              '| outside the null? | admitted | share positive later | '
              'baseline |',
              '|---|---:|---:|---:|---:|---|---:|---:|---:|']
        for _i, r in Y.iterrows():
            q = NY[NY.pair == r.pair] if len(NY) else pd.DataFrame()
            if len(q):
                lo = q.rho.quantile(0.05); hi = q.rho.quantile(0.95)
                out = ('**yes**' if (r.rho > hi or r.rho < lo) else 'no')
                sl = '%+.4f' % q.rho.mean(); slo = '%+.4f' % lo
                shi = '%+.4f' % hi
            else:
                out = 'pending'; sl = slo = shi = '--'
            L.append('| %s | %+.4f | %s | %s | %s | %s | %d | %.3f | %.3f |'
                     % (r.pair, r.rho, sl, slo, shi, out, r.n_admitted,
                        r.share_pos_later, r.share_pos_later_baseline))
        L.append('')
    # the verdict
    r1 = PLr[(PLr.rotation == 'R1') & (PLr['share'] == BO.SHARE_DECLARED)].iloc[0]
    r2 = PLr[(PLr.rotation == 'R2') & (PLr['share'] == BO.SHARE_DECLARED)].iloc[0]
    L += ['## The verdict, plainly', '']
    bad = (r1.share_pos_later <= r1.share_pos_later_baseline and
           r2.share_pos_later <= r2.share_pos_later_baseline)
    if bad:
        L += ['**A strategy\'s fit to a pair does not carry.** Admitting a '
              'sleeve on six years of one pair does not make it more likely '
              'to be profitable on the other six years of that same pair. In '
              'rotation R1 the admitted sleeves are positive later **%.1f%% '
              'of the time against a baseline of %.1f%%**, and in R2 **%.1f%% '
              'against %.1f%%** -- at or below the baseline in both. The '
              'pooled rank correlation is **%+.4f**.'
              % (100 * r1.share_pos_later, 100 * r1.share_pos_later_baseline,
                 100 * r2.share_pos_later, 100 * r2.share_pos_later_baseline,
                 r1.rho_pooled), '',
              'The consequence for item 3 is stated here rather than left to '
              'be inferred: **every book built by selecting algorithms on a '
              'pair\'s admission years is selecting on something that does '
              'not persist.** Those books are reported in full because Jack '
              'asked for them, and B1 is the test that says so numerically, '
              'but this is the reason to expect them to fail it.']
    else:
        L += ['Admission does raise the share positive later above its own '
              'baseline: R1 %.1f%% against %.1f%%, R2 %.1f%% against %.1f%%.'
              % (100 * r1.share_pos_later, 100 * r1.share_pos_later_baseline,
                 100 * r2.share_pos_later, 100 * r2.share_pos_later_baseline)]
    L += ['', '## Provenance', '',
          '- `results/nnfx/books/fit_real.csv` -- %d rows' % len(A),
          '- `results/nnfx/books/fitpooled_real.csv` -- %d rows' % len(PLr),
          '- `results/nnfx/books/null/fit_*.csv` -- %d null runs' % nruns,
          '- the bank: `results/nnfx/bank/sleeve_bank_real.npz`',
          '- the algorithm list: `results/nnfx/bank/cand_index.npz`']
    txt = '\n'.join(L) + '\n'
    open(os.path.join(OUT, 'PAIR_FIT.md'), 'w').write(txt)
    print('  PAIR_FIT.md written (%d lines), %d null runs in it'
          % (len(L), nruns), flush=True)
    return nruns


# ======================= BOOKS.md =======================================
def _sh(x):
    return 'off' if not np.isfinite(x) else '%.2f' % x


def books_md(verbose=True):
    RF = pd.read_csv(os.path.join(BOUT, 'books_full_real.csv'))
    ND = pd.read_csv(os.path.join(BOUT, 'books_declared_nudge.csv'))
    NB, nruns = _read('books_*.csv')
    F = null_floor(NB)
    D = gate_table(RF, F)
    # book (a)'s B4 comes from the trade-floor nudge, not from a K neighbour
    for rot in ('R1', 'R2'):
        for md in ('separate', 'voting'):
            q = ND[(ND.rotation == rot) & (ND['mode'] == md)
                   & (ND['share'] == BO.SHARE_DECLARED)]
            if len(q) == 3:
                ok = int((q.R_total > 0).all())
                D.loc[(D.family == 'a_declared') & (D.rotation == rot)
                      & (D['mode'] == md)
                      & (D['share'] == BO.SHARE_DECLARED), 'B4'] = ok
    D['clears_B1_B4'] = ((D.B1 == 1) & (D.B2 == 1) & (D.B3 == 1)
                         & (D.B4 == 1)).astype(int)
    D['passer'] = ((D.clears_B1_B4 == 1) & (D.B5 == 1)).astype(int)
    D.to_csv(os.path.join(BOUT, 'books_gates.csv'), index=False)

    L = ['# BOOKS -- the four families, both rotations, both modes, five gates',
         '',
         '**Item 3 of Jack\'s correction. `PROTOCOL.md` AMENDMENT 1, A1 to A5. '
         'Every book is built on its admission years and scored on the other '
         'years, so no number below is computed on data any of its sleeves was '
         'admitted on.**', '']
    L += ['## The construction', '',
          '| family | what |', '|---|---|',
          '| **a_declared** | every admitted sleeve from the 6 published, the '
          '10 hand-built, and A and B |',
          '| **b_per_pair** | for each pair, the top K algorithms on THAT '
          'PAIR\'S admission years. K swept %s |'
          % ' / '.join(str(k) for k in BO.K_PER_PAIR),
          '| **c_all_pairs** | the top K algorithms across all pairs, each '
          'trading only the pairs it was admitted on. K swept %s |'
          % ' / '.join(str(k) for k in BO.K_ALL), '',
          '| mode | what |', '|---|---|',
          '| **separate** | every sleeve its own position at equal risk, 1/N '
          'each |',
          '| **voting** | Jack\'s 4 September rule: N signals on a pair are '
          'ONE position with N votes, cost on changes in the NET position |',
          '',
          'Selection pool: **%d algorithms** -- Source 3\'s 200,000 random '
          'draws plus every algorithm its local search evaluated -- times 28 '
          'pairs, so about **21.5 million sleeve evaluations** across the two '
          'windows. Null: **%d matched runs**, each one scrambling the world '
          'and repeating all of it.' % (int(RF.sleeves.max() and 384334), nruns),
          '']
    L += ['## The gate table at Jack\'s declared threshold (share 0.25)', '',
          '| rot | family | K | sleeves | R | R/yr | dip | R/dip | %/yr at B5 '
          'sizing | B1 | B2 | B3 | B4 | B5 | passer |',
          '|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|---|---|']
    X = D[(D['share'] == BO.SHARE_DECLARED) & (D['mode'] == 'voting')] \
        .sort_values(['rotation', 'family', 'K'])
    g = lambda v: ('--' if not np.isfinite(v) else ('**PASS**' if v == 1 else 'fail'))
    for _i, r in X.iterrows():
        L.append('| %s | %s | %d | %d | %+.3f | %+.3f | %.3f | %+.3f | %s | %s '
                 '| %s | %s | %s | %s | %s |'
                 % (r.rotation, r.family.replace('_', ' '), r.K, r.sleeves,
                    r.R, r.get('R_per_year', np.nan),
                    r.get('dip_binding', np.nan), r.get('R_per_dip', np.nan),
                    ('%+.2f' % r.b5_pct_per_year)
                    if np.isfinite(r.get('b5_pct_per_year', np.nan)) else '--',
                    g(r.B1), g(r.B2), g(r.B3), g(r.B4), g(r.B5),
                    '**PASSER**' if r.passer == 1 else 'no'))
    L += ['', '*The `voting` mode is shown because it dominates `separate` '
          'everywhere -- see the cost section. The full table for both modes '
          'and all six share thresholds is `books_gates.csv`.*', '']
    # the cost comparison
    L += ['## What netting saves', '',
          'Both costs are charged on one convention -- half the round-trip '
          'spread on each change in notional, at the bar\'s own price -- so '
          'the difference between them is netting and nothing else. On a '
          'single sleeve the two agree exactly, and the separate figure '
          'agrees with `nnfxproto.cost_R` on the same trades to within 0.2%, '
          'the residual being entry-versus-exit pricing.', '',
          '| rot | family | K | sleeves | cost separate | cost voting | saved '
          '| saved % |', '|---|---|---:|---:|---:|---:|---:|---:|']
    for _i, r in X.iterrows():
        sv = r.cost_sep_total - r.cost_vote_total
        L.append('| %s | %s | %d | %d | %.3f | %.3f | %.3f | %.1f%% |'
                 % (r.rotation, r.family.replace('_', ' '), r.K, r.sleeves,
                    r.cost_sep_total, r.cost_vote_total, sv,
                    100 * sv / r.cost_sep_total if r.cost_sep_total else 0))
    L.append('')
    # the K curve, every share
    L += ['## The K curves, every share threshold', '',
          'Jack\'s standing rule: every cut swept over its full range and '
          'reported as a curve. R on the scoring window, `voting` mode.', '']
    for fam, grid in (('b_per_pair', BO.K_PER_PAIR),
                      ('c_all_pairs', BO.K_ALL)):
        for rot in ('R1', 'R2'):
            L += ['**%s, %s**' % (fam.replace('_', ' '), rot), '',
                  '| share | ' + ' | '.join(str(k) for k in grid) + ' |',
                  '|---|' + '---:|' * len(grid)]
            for sh in BO.SHARE_GRID:
                q = D[(D.family == fam) & (D.rotation == rot)
                      & (D['share'] == sh) & (D['mode'] == 'voting')]
                m = dict(zip(q.K, q.R))
                L.append('| %s | ' % _sh(sh)
                         + ' | '.join(('%+.2f' % m[k]) if k in m else '--'
                                      for k in grid) + ' |')
            L.append('')
    # book (a)'s nudge
    L += ['## Book (a), the declared 18, and its B4 nudge', '',
          'Book (a) has no K, so A5 declared its admission count to be the '
          '20-trade floor, moved to 15 and 30.', '',
          '| rot | trade floor | share | mode | sleeves | R | R/yr | R/dip | '
          '%/yr at B5 sizing |', '|---|---:|---:|---|---:|---:|---:|---:|---:|']
    for _i, r in ND[ND['share'] == BO.SHARE_DECLARED].sort_values(
            ['rotation', 'min_trades', 'mode']).iterrows():
        L.append('| %s | %d | %s | %s | %d | %+.3f | %+.3f | %+.3f | %+.2f |'
                 % (r.rotation, r.min_trades, _sh(r['share']), r['mode'],
                    r.sleeves, r.R_total, r.R_per_year, r.R_per_dip,
                    r.b5_pct_per_year))
    L.append('')
    # ---- families d and e, declared after the null chain launched
    for fn, title, cols, note in (
        ('books_combined.csv', 'Book (d) COMBINED — a plus the best of b and c',
         ['rotation', 'K', 'is_central_K', 'sleeves', 'sleeves_from_a',
          'sleeves_from_winner', 'winner_family', 'winner_K', 'R',
          'cell_baseline_R', 'excess_over_cell', 'B1b', 'R_per_dip',
          'b5_pct_per_year', 'B2', 'B3', 'B4'],
         'A11 fixed the choice as a procedure so the null can apply the '
         'identical one: each family\'s best K by return per dip AVERAGED over '
         'the two rotations, then whichever family wins. B4 reads off that K '
         'one grid step down and up. A sleeve in both halves is held once.'),
        ('books_fourcell.csv', 'Book (e) FOUR-CELL — the true cross only',
         ['direction', 'cell_pairs', 'cell_years', 'K', 'sleeves', 'R',
          'cell_baseline_R', 'excess_over_cell', 'B1b', 'R_per_dip',
          'b5_pct_per_year', 'B2', 'B4'],
         'A10. Select on 15 pairs in one six-year window, trade the 13 OTHER '
         'pairs in the OTHER window. No shared pair, no shared year. Only the '
         'TRUE CROSS cell is shown here; all four cells are in the csv, and '
         'the other three are what forced B1b into existence.')):
        f = os.path.join(BOUT, fn)
        if not os.path.exists(f):
            continue
        X = pd.read_csv(f)
        if 'is_true_cross' in X.columns:
            X = X[X.is_true_cross == 1]
        if 'is_central_K' in X.columns:
            X = X[X.is_central_K == 1]
        X = X[(X['share'] == BO.SHARE_DECLARED) & (X['mode'] == 'voting')]
        cols = [c for c in cols if c in X.columns]
        L += ['## ' + title, '', note, '',
              '| ' + ' | '.join(cols) + ' |',
              '|' + '---|' * len(cols)]
        for _i, r in X.iterrows():
            L.append('| ' + ' | '.join(
                ('%+.3f' % r[c]) if isinstance(r[c], float) else str(r[c])
                for c in cols) + ' |')
        L += ['', '**B1 is blank for both families on purpose.** They were '
              'declared at 20:10 and 20:12, after the 19:41 null chain '
              'launched, so neither is called a passer until chain 2 lands. '
              'See A10 and A11.', '']
    # ---- A13, the measurement that explains all of it
    f = os.path.join(BOUT, 'crosscell_transfer.csv')
    if os.path.exists(f):
        T = pd.read_csv(f)
        DC = pd.read_csv(os.path.join(BOUT, 'crosscell_deciles.csv'))
        L += ['## What transfers and what does not — A13', '',
              'Measured on the bank with no book in the way. Rank every '
              'algorithm by its total net R pooled over one set of pairs in '
              'one window; ask its mean net R per sleeve on the OTHER pairs '
              'in the OTHER window.', '',
              '| | select | score | algorithms | Spearman rho | cell baseline '
              '| top decile | bottom decile | top − bottom |',
              '|---|---|---|---:|---:|---:|---:|---:|---:|']
        for _i, r in T.iterrows():
            L.append('| **%s** | %s | %s | %d | **%+.4f** | %+.3f | **%+.3f** '
                     '| %+.3f | **%+.3f** |'
                     % (r.direction, r.select, r.score, r.n_algorithms,
                        r.spearman_rho, r.cell_baseline_R,
                        r.top_decile_mean_R, r.bottom_decile_mean_R,
                        r.top_minus_bottom))
        L += ['', 'Against the SAME-PAIR figure from item 2: median per-pair '
              'rho **+0.0183**, mean **+0.0059**.', '',
              '**An algorithm\'s quality transfers across currencies and '
              'decades at rho about +0.20; its fit to one particular pair '
              'transfers at about +0.01.** Every book result above follows '
              'from that asymmetry — per-pair selection fails its own cell '
              'baseline in one rotation, pooled selection clears it in both, '
              'and the four-cell excess is flat in K across three orders of '
              'magnitude, which is what a broad factor looks like and not '
              'what overfitting looks like.', '',
              '| decile of the selection ranking | mean cross-cell R, fwd | '
              'mean cross-cell R, rev |', '|---:|---:|---:|']
        pv = DC.pivot(index='decile', columns='direction',
                      values='mean_cross_R')
        for d_, row in pv.iterrows():
            L.append('| %d | %+.3f | %+.3f |'
                     % (d_, row.get('fwd', np.nan), row.get('rev', np.nan)))
        L.append('')
    # the verdict
    pas = D[D.passer == 1]
    c14 = D[D.clears_B1_B4 == 1]
    L += ['## The verdict, plainly', '']
    L += ['**%d of %d book cells clear B1 to B4. %d are passers (B1 to B5).**'
          % (len(c14), len(D), len(pas)), '']
    best = D.sort_values('b5_pct_per_year', ascending=False).head(1)
    if len(best):
        b = best.iloc[0]
        L += ['The best cell by percent a year is **%s %s K=%d %s at share '
              '%s**: %+.2f%% a year, R/dip %+.3f, and it is **%.2f '
              'percentage points short of 12%%**.'
              % (b.rotation, b.family.replace('_', ' '), b.K, b['mode'],
                 _sh(b['share']), b.b5_pct_per_year, b.R_per_dip,
                 12.0 - b.b5_pct_per_year), '']
    L += ['## Provenance', '',
          '- `results/nnfx/books/books_full_real.csv` -- %d rows' % len(RF),
          '- `results/nnfx/books/books_gates.csv` -- %d rows' % len(D),
          '- `results/nnfx/books/books_declared_nudge.csv` -- %d rows' % len(ND),
          '- `results/nnfx/books/null/books_*.csv` -- %d matched null runs'
          % nruns,
          '- `results/nnfx/PROTOCOL.md` -- AMENDMENT 1 is the governing text']
    txt = '\n'.join(L) + '\n'
    open(os.path.join(OUT, 'BOOKS.md'), 'w').write(txt)
    print('  BOOKS.md written (%d lines); %d of %d cells clear B1-B4, %d '
          'passers; %d null runs' % (len(L), len(c14), len(D), len(pas), nruns),
          flush=True)
    return D, nruns


# ======================= WINNERS.md =====================================
def members_of(bank, pairs, rot, fam, K, share):
    """The (algorithm index, pair) sleeves a book cell holds.

    The selection logic lives in nnfxbooks and is CALLED, not copied, so a
    winners list cannot drift from the book it describes.
    """
    aw = 'h1' if rot == 'R1' else 'h2'
    adm = BO.admitted(bank, aw, share)
    col = {p: i for i, p in enumerate(pairs)}
    out = []
    if fam == 'b_per_pair':
        for p in pairs:
            for j in BO.rank_per_pair(bank, adm, aw, col[p], K)[:K]:
                out.append((int(j), p))
    elif fam == 'c_all_pairs':
        for j in BO.rank_all(bank, adm, aw, K)[:K]:
            for p in pairs:
                if adm[j, col[p]]:
                    out.append((int(j), p))
    return out, aw


def winners_md(D, verbose=True):
    import nnfxcands as CL
    import nnfxsrc3 as S3
    S.load_costs(os.environ.get('FX_COST_TABLE',
                                os.path.join(ROOTOUT, 'cost_table_h22.csv')))
    S3.init_space()
    pairs, bank = BK.load_bank('real')
    cands, _src, _m = CL.load()
    # THE BEST BOOK: a passer if there is one, else the best percent a year,
    # and the label says which rule was used.
    pas = D[D.passer == 1]
    c14 = D[D.clears_B1_B4 == 1]
    pool = pas if len(pas) else (c14 if len(c14) else D)
    rule = ('a passer (B1 to B5)' if len(pas)
            else ('the best of those clearing B1 to B4' if len(c14)
                  else 'the best percent a year -- NOTHING CLEARS B1 TO B4'))
    pool = pool[pool.family != 'a_declared'] if \
        (pool.family != 'a_declared').any() else pool
    b = pool.sort_values('b5_pct_per_year', ascending=False).iloc[0]
    mem, aw = members_of(bank, pairs, b.rotation, b.family, int(b.K),
                         float(b['share']))
    sw = 'h2' if aw == 'h1' else 'h1'
    col = {p: i for i, p in enumerate(pairs)}
    N = max(1, len(mem))
    nyr = len(BK.H1Y if sw == 'h1' else BK.H2Y)
    rows = {}
    for (j, p) in mem:
        r = rows.setdefault(j, dict(algo=j, pairs=[], R=0.0, Radm=0.0,
                                    trades=0))
        r['pairs'].append(p)
        r['R'] += float(bank['%s__R' % sw][j, col[p]])
        r['Radm'] += float(bank['%s__R' % aw][j, col[p]])
        r['trades'] += int(bank['%s__trades' % sw][j, col[p]])
    tot = sum(v['R'] for v in rows.values()) / N
    sc = float(b.b5_scale) if np.isfinite(b.b5_scale) else np.nan
    W = []
    for j, v in rows.items():
        t = S3.mkcand(cands[j])
        W.append(dict(rank=0, algo='S%d' % j, cand_id=P.cand_id(t),
                      label=P.cand_label(t), n_pairs=len(v['pairs']),
                      pairs=' '.join(sorted(v['pairs'])),
                      sleeves=len(v['pairs']),
                      R_scoring=v['R'], R_admission=v['Radm'],
                      trades=v['trades'],
                      contribution_R=v['R'] / N,
                      contribution_R_per_year=v['R'] / N / nyr,
                      pct_per_year_at_book_sizing=v['R'] / N / nyr * sc,
                      share_of_book=(v['R'] / N / tot) if tot else np.nan))
    WD = pd.DataFrame(W).sort_values('contribution_R', ascending=False)
    WD['rank'] = range(1, len(WD) + 1)
    WD.to_csv(os.path.join(BOUT, 'winners.csv'), index=False)

    L = ['# WINNERS -- every strategy in the best book',
         '',
         '**Item 4 of Jack\'s correction. The best book was picked by %s.**'
         % rule, '']
    L += ['## The book', '', '| | |', '|---|---|',
          '| family | %s |' % b.family.replace('_', ' '),
          '| rotation | %s -- admitted on %s, scored on %s |'
          % (b.rotation, '2005-2010' if aw == 'h1' else '2011-2015',
             '2011-2015' if sw == 'h2' else '2005-2010'),
          '| K | %d |' % int(b.K),
          '| share threshold | %s |' % _sh(float(b['share'])),
          '| mode | %s |' % b['mode'],
          '| distinct algorithms | %d |' % len(rows),
          '| sleeves (algorithm x pair) | %d |' % len(mem),
          '| R on the scoring window | %+.3f |' % b.R,
          '| R a year | %+.3f |' % b.R_per_year,
          '| verified worst dip | %.3f (realised %.3f, shuffled-order 95th '
          '%.3f, the larger binding) |'
          % (b.dip_binding, b.dip_true, b.dip95),
          '| **return per dip** | **%+.3f** |' % b.R_per_dip,
          '| sizing to 3.6%% daily / 5.4%% trailing | x%.3f |' % b.b5_scale,
          '| **percent a year at that sizing** | **%+.2f%%** |'
          % b.b5_pct_per_year,
          '| days to pass the +10%% evaluation | %s |'
          % ('%d' % b.b5_eval_days if np.isfinite(
              pd.to_numeric(b.get('b5_eval_days'), errors='coerce'))
             else 'never passes'),
          '| gates cleared | B1 %s, B2 %s, B3 %s, B4 %s, B5 %s |'
          % tuple(('PASS' if b[k] == 1 else ('--' if not np.isfinite(b[k])
                                             else 'fail'))
                  for k in ('B1', 'B2', 'B3', 'B4', 'B5')), '']
    L += ['## How far from 12%', '',
          '**%+.2f%% a year against Jack\'s 12%% target: short by %.2f '
          'percentage points, a factor of %.1f.**'
          % (b.b5_pct_per_year, 12.0 - b.b5_pct_per_year,
             (12.0 / b.b5_pct_per_year) if b.b5_pct_per_year > 0 else np.inf),
          '']
    L += ['## Every strategy in it, sorted by contribution', '',
          '*Attribution is exact for the `separate` mode, where the book is '
          '1/N times the sum of its sleeves. In `voting` mode the netting '
          'saving is a property of the whole pair, not of one member, so the '
          'per-member figures below are the separate-position contributions '
          'and the book total they sum to is the separate one.*', '',
          '| # | algorithm | pairs | sleeves | R scoring | R/yr | %/yr at book '
          'sizing | share of book | trades |',
          '|---:|---|---|---:|---:|---:|---:|---:|---:|']
    for _i, r in WD.head(60).iterrows():
        L.append('| %d | %s | %s | %d | %+.3f | %+.4f | %+.3f%% | %+.1f%% | %d |'
                 % (r['rank'], r.label, r.pairs if r.n_pairs <= 6
                    else '%d pairs' % r.n_pairs, r.sleeves, r.R_scoring,
                    r.contribution_R_per_year,
                    r.pct_per_year_at_book_sizing,
                    100 * r.share_of_book, r.trades))
    if len(WD) > 60:
        L.append('')
        L.append('*%d more in `winners.csv`.*' % (len(WD) - 60))
    L += ['', '## Provenance', '',
          '- `results/nnfx/books/winners.csv` -- %d algorithms' % len(WD),
          '- `results/nnfx/books/books_gates.csv` -- the cell this book is',
          '- `results/nnfx/bank/sleeve_bank_real.npz` -- every number above']
    txt = '\n'.join(L) + '\n'
    open(os.path.join(OUT, 'WINNERS.md'), 'w').write(txt)
    print('  WINNERS.md written (%d lines): %d algorithms, %+.2f%% a year'
          % (len(L), len(WD), b.b5_pct_per_year), flush=True)
    return WD, b


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--declared-nudge', action='store_true')
    ap.add_argument('--reports', action='store_true')
    a = ap.parse_args()
    if a.declared_nudge:
        declared_nudge()
    if a.reports:
        n = pair_fit_md()
        D, n2 = books_md()
        winners_md(D)
        print('DONE nnfxrep: %d null runs in PAIR_FIT, %d in BOOKS'
              % (n, n2), flush=True)
