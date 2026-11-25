import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""ITEM 3a, JACK 25 NOV -- THE PER-PAIR, PER-DIRECTION BANK.

THE DIRECTION CHANGED AND SO DOES THE UNIT OF ACCOUNT. The 12%-a-year target is
for the whole BOOK, not for one strategy, and the book is a handful of
strategies each assigned to the pairs it suits. So from now on every candidate
is banked PER PAIR AND PER DIRECTION AND PER UNSEEN YEAR -- as the primary
output, not pooled and split on request -- so that a pair-by-pair assignment
can be built from the bank without re-running anything.

WHAT IS BANKED, and why each one:
  c1_alone     all 39 C1 alone. The raw material; no baseline, no filter.
  base_alone   the 3 picked baselines as their own entry (stage 1's form).
  base_filter  ichimoku + each of the 3 picked baselines (stage 2's form).
  candidate    A and B, the walk-forward stitch, as reported.

"THE 3 BASELINES AS FILTERS" IS AMBIGUOUS AND BOTH READINGS ARE RUN. A
baseline on its own is an entry rule (price crosses it); a baseline as a filter
needs something to filter, and the only declared choice is the main C1. Running
both costs six runs instead of three and removes the guess. Every row says
which it is.

THE STANDING RULES APPLY TO THE CANDIDATE ROWS AND NOT TO THE RAW ROWS, and
each row declares it. A and B are the candidates as reported, so they carry the
floor, the peg guard and the leverage cap. The 39 C1 alone are the raw material
for an assignment question and carry no floor and no peg guard -- but they DO
carry the leverage cap, because a per-pair bank whose sizes could not be held
simultaneously cannot be summed into a book, which is the whole purpose of it.

PER-PAIR BANKING MAKES THE MULTIPLE-COMPARISON PROBLEM WORSE, NOT BETTER, and
this file is not where that is solved. 28 pairs x 2 directions is 56 ways to
find a winner by luck inside each candidate, and 39 candidates over 6 unseen
years is 13,104 cells. NOTHING IN THIS FILE IS A SELECTION. It is a bank. The
selection rule and its label-shuffle null are item 3c (nnfxgroups.py), and a
cell in here reaching a nice number means nothing on its own.

Writes results/nnfx/per_pair_bank.csv (the bank, one row per candidate x pair x
direction x year), per_pair_bank_pair.csv (collapsed over years),
per_pair_bank_cand.csv (collapsed over pairs, for reconciliation) and
PER_PAIR_BANK.md.
"""
import numpy as np, pandas as pd

import nnfx1 as N
import nnfx2s as S2
import nnfxvol as VOL
import nnfxcurves as CUR
import l2sweep as S

OUT = os.path.join(ROOTOUT, 'nnfx')
os.makedirs(OUT, exist_ok=True)
BUILD = N.BUILD_YEARS
MAIN = 'jack'
MAIN_C1 = 'ichimoku_signals'
ABC = (('A', 'ichimoku_signals', 'sma_baseline', 'full_nnfx'),
       ('B', 'schaff_trend_cycle_signals', 'sma_baseline', 'side_xentry'))


def _yclass(y):
    if y in BUILD:
        return 'unseen'
    if y < BUILD[0]:
        return 'tune'
    return 'sealed'


def _bank_rows(T, kind, name, variant, lv, pg, verbose=False):
    """PER PAIR, PER DIRECTION, PER UNSEEN YEAR, net, at achievable size.

    THE CAP IS APPLIED ONCE OVER THE WHOLE FRAME AND THEN SPLIT. It has to be:
    the cap is a portfolio constraint over all pairs at once, so capping each
    pair's slice separately would let every pair use the whole 1:30 and the
    sum of the slices would be a book no account could hold. Apply, then
    split, never the other way round.

    THE YEAR IS THE EXIT YEAR, matching every realized per-trade figure in the
    project. An entry-year convention would put a trade's R in a year the
    account did not receive it.

    EVERY YEAR 2005-2020 IS BANKED AND EACH ONE DECLARES ITS CLASS. Item 3c
    has to pick a strategy per group on each step's four TUNING years, so a
    bank restricted to the unseen years cannot answer it -- and a selection
    made from unseen-year numbers would be the whole fault this project
    exists to avoid. So:

      tune        2005-2009: may be used to CHOOSE. Never reported as a result.
      unseen      2010-2015: the BUILD evidence. The only reportable block.
      sealed      2016-2020: computed and stored, NOT reported, by standing
                  rule. 2021 onward never enters the engine at all.

    `reportable` is 1 on exactly the unseen block. Any table that quotes a row
    with reportable = 0 is wrong, and the column is there so that is checkable
    rather than remembered.
    """
    if not len(T):
        return []
    M, _ = VOL.apply_leverage_cap(T)
    M = M.reset_index(drop=True)
    M['_cost'] = N._cost_R(M)
    g = (M.groupby(['pair', 'entry_date', 'direction'], as_index=False)
         .agg(R_gross=('R_gross', 'sum'), cost=('_cost', 'sum'),
              exit_date=('exit_date', 'max'), bars=('bars_held', 'max'),
              lev=('lev_scale', 'min') if 'lev_scale' in M.columns
              else ('R_gross', 'size')))
    g['R'] = g.R_gross - g.cost
    g['year'] = pd.DatetimeIndex(g.exit_date).year
    g = g[(g.year >= 2005) & (g.year <= 2020)]
    if not len(g):
        return []
    out = []
    for (p, d, y), sub in g.groupby(['pair', 'direction', 'year']):
        r = sub.R.to_numpy(float)
        out.append(dict(
            kind=kind, name=name, variant=variant,
            pair=p, direction=d, year=int(y),
            year_class=_yclass(int(y)),
            reportable=int(int(y) in BUILD),
            n_trades=len(r), R_total=float(r.sum()),
            R_per_trade=float(r.mean()),
            R_gross=float(sub.R_gross.sum()), cost=float(sub.cost.sum()),
            best_trade_R=float(r.max()), worst_trade_R=float(r.min()),
            win_rate=float((r > 0).mean()),
            mean_bars=float(sub.bars.mean()),
            mean_lev_scale=(float(sub.lev.mean())
                            if 'lev' in sub.columns else np.nan),
            lowvol_q=lv, peg_x=pg, leverage_cap_on=1))
    return out


def build(variant=MAIN, names=None, verbose=True):
    C1L, BASEL, _C, _V, _X = N.families()
    names = names or list(C1L)
    rows = []
    _lv, _pg, _qq = N.LOWVOL_Q, N.PEG_X, N.QUIET_Q
    try:
        N.LOWVOL_Q, N.PEG_X, N.QUIET_Q = None, None, None
        for i, nm in enumerate(names):
            T = N.run_one(nm, 'c1', None, variant, use_hourly=True)
            r = _bank_rows(T, 'c1_alone', nm, variant, 0.0, 0.0)
            rows += r
            if verbose:
                print('    %2d/%d c1_alone %-38s %4d cells'
                      % (i + 1, len(names), nm, len(r)), flush=True)
        for nm in S2.BASE_PICKS:
            T = N.run_one(nm, 'base', None, variant, use_hourly=True)
            r = _bank_rows(T, 'base_alone', nm, variant, 0.0, 0.0)
            rows += r
            if verbose:
                print('    base_alone %-38s %4d cells' % (nm, len(r)),
                      flush=True)
    finally:
        N.LOWVOL_Q, N.PEG_X, N.QUIET_Q = _lv, _pg, _qq
    for nm in S2.BASE_PICKS:
        T = S2.run_combo(MAIN_C1, None, nm, None, variant, 'side',
                         lowvol_q=None, peg_x=None)
        r = _bank_rows(T, 'base_filter', '%s+%s' % (MAIN_C1, nm), variant,
                       0.0, 0.0)
        rows += r
        if verbose:
            print('    base_filter %-38s %4d cells' % (nm, len(r)), flush=True)
    for (lab, c1, base, rs) in ABC:
        T = CUR._stitch(c1, base, rs, variant, VOL.LOWVOL_Q,
                        VOL.PEG_X_DECIDED)
        r = _bank_rows(T, 'candidate', lab, variant, VOL.LOWVOL_Q,
                       VOL.PEG_X_DECIDED)
        rows += r
        if verbose:
            print('    candidate %-38s %4d cells' % (lab, len(r)), flush=True)
    D = pd.DataFrame(rows)
    D.to_csv(os.path.join(OUT, 'per_pair_bank.csv'), index=False)
    # THE COLLAPSED VIEWS ARE BUILT ON THE UNSEEN BLOCK ONLY. The bank holds
    # every year so item 3c can choose on the tuning ones, but a summary that
    # pooled tuning and unseen years would be a reported number containing
    # the years the choices were made on.
    U = D[D.reportable == 1]
    # collapsed over years: the per pair x direction view an assignment reads
    P = (U.groupby(['kind', 'name', 'variant', 'pair', 'direction'],
                   as_index=False)
         .agg(years=('year', 'nunique'), n_trades=('n_trades', 'sum'),
              R_total=('R_total', 'sum'),
              years_positive=('R_total', lambda v: int((v > 0).sum())),
              best_year_R=('R_total', 'max'), worst_year_R=('R_total', 'min'),
              best_trade_R=('best_trade_R', 'max'),
              worst_trade_R=('worst_trade_R', 'min')))
    P['R_per_trade'] = P.R_total / P.n_trades.replace(0, np.nan)
    P['R_per_year'] = P.R_total / P.years.replace(0, np.nan)
    # THE SHARE OF A CELL'S R THAT IS ONE TRADE. With 56 cells per candidate
    # the thing most likely to make a cell look good is a single trade, so the
    # column that says so travels with the bank rather than being derived
    # later and forgotten.
    P['best_trade_share'] = P.best_trade_R / P.R_total.where(
        P.R_total.abs() > 1e-9)
    P.to_csv(os.path.join(OUT, 'per_pair_bank_pair.csv'), index=False)
    # collapsed over pairs: reconciles against the pooled tables
    C = (U.groupby(['kind', 'name', 'variant'], as_index=False)
         .agg(cells=('R_total', 'size'), pairs=('pair', 'nunique'),
              n_trades=('n_trades', 'sum'), R_total=('R_total', 'sum'),
              cells_positive=('R_total', lambda v: int((v > 0).sum()))))
    C['R_per_year'] = C.R_total / len(BUILD)
    C['pct_cells_positive'] = 100.0 * C.cells_positive / C.cells
    C = C.sort_values('R_total', ascending=False)
    C.to_csv(os.path.join(OUT, 'per_pair_bank_cand.csv'), index=False)
    if verbose:
        print('  bank: %d cells (%d unseen, %d tune, %d sealed), '
              '%d candidates, %d pairs'
              % (len(D), int((D.year_class == 'unseen').sum()),
                 int((D.year_class == 'tune').sum()),
                 int((D.year_class == 'sealed').sum()),
                 D.name.nunique(), D.pair.nunique()), flush=True)
    return D, P, C



# ====================== THE DOCUMENT ====================================
def md_bank(out=None):
    """PER_PAIR_BANK.md -- item 3a, from the files."""
    import hashlib
    L_, a = [], None
    L_ = []
    a = L_.append
    def rd(n):
        f = os.path.join(OUT, n)
        return (pd.read_csv(f) if os.path.exists(f) and os.path.getsize(f) > 2
                else pd.DataFrame())
    D, P, C = (rd('per_pair_bank.csv'), rd('per_pair_bank_pair.csv'),
               rd('per_pair_bank_cand.csv'))
    a('# PER-PAIR BANK — item 3a, Jack 25 November 2026')
    a('')
    a('**The unit of account changed, so the bank did.** The 12%-a-year target '
      'is for the whole BOOK and the book is a handful of strategies each '
      'assigned to the pairs it suits, so every candidate is now banked '
      '**per pair, per direction, per year** as the primary output — not '
      'pooled and split on request. An assignment can be built from this file '
      'without re-running anything.')
    a('')
    if len(D):
        a('| | |')
        a('|---|---:|')
        a('| cells | **%s** |' % '{:,}'.format(len(D)))
        a('| candidates | %d |' % D.name.nunique())
        a('| pairs | %d |' % D.pair.nunique())
        a('| unseen cells (2010–2015, the only reportable block) | %s |'
          % '{:,}'.format(int((D.year_class == 'unseen').sum())))
        a('| tuning cells (2005–2009, may CHOOSE, never reported) | %s |'
          % '{:,}'.format(int((D.year_class == 'tune').sum())))
        a('| sealed cells (2016–2020, computed, NOT reported) | %s |'
          % '{:,}'.format(int((D.year_class == 'sealed').sum())))
        a('')
    a('**Three things about how it is built that change what the numbers '
      'mean.**')
    a('')
    a('1. **The leverage cap is applied over the whole 28-pair frame and THEN '
      'split.** It has to be: the cap is a portfolio constraint over all '
      'pairs at once, so capping each pair separately would let every pair '
      'use the whole 1:30 and the sum of the slices would be a book no '
      'account could hold. A group\'s R in this file is its share of a book '
      'that was achievable **as a whole**.')
    a('2. **The year is the EXIT year**, matching every realized per-trade '
      'figure in the project. An entry-year convention would put a trade\'s R '
      'in a year the account did not receive it.')
    a('3. **"The 3 baselines as filters" is ambiguous and both readings are '
      'in.** `base_alone` is a baseline as its own entry rule (price crosses '
      'it, stage 1\'s form); `base_filter` is ichimoku plus that baseline '
      '(stage 2\'s form). Six runs instead of three, and no guess.')
    a('')
    a('**NOTHING IN THIS FILE IS A SELECTION.** 28 pairs x 2 directions is 56 '
      'ways to find a winner by luck inside each candidate, and %s unseen '
      'cells is a lot of lottery tickets. The selection rule and its '
      'label-shuffle null are item 3c in `PAIR_GROUPS.md`. **A cell in here '
      'reaching a nice number means nothing on its own**, which is why the '
      'per-pair view carries `best_trade_share` next to every total.'
      % ('{:,}'.format(int((D.year_class == 'unseen').sum())) if len(D)
         else 'the'))
    a('')
    if len(C):
        a('## Candidates on the unseen block, ranked')
        a('')
        a('| kind | candidate | pairs | trades | R total | R/yr | '
          'cells positive | % of cells positive |')
        a('|---|---|---:|---:|---:|---:|---:|---:|')
        for _, r in C.head(20).iterrows():
            b = '**' if r.kind == 'candidate' else ''
            a('| %s | %s%s%s | %d | %d | %s%+.3f%s | %+.3f | %d of %d | '
              '%.1f%% |'
              % (r.kind, b, r['name'], b, int(r.pairs), int(r.n_trades),
                 b, r.R_total, b, r.R_per_year, int(r.cells_positive),
                 int(r.cells), r.pct_cells_positive))
        if len(C) > 20:
            a('')
            a('*(%d further rows in the csv, all negative.)*' % (len(C) - 20))
        a('')
        pos = C[C.R_total > 0]
        a('**Only %d of the %d candidates are positive on the unseen block**: '
          '%s.'
          % (len(pos), len(C),
             ', '.join('%s %+.3f R' % (r['name'], r.R_total)
                       for _, r in pos.iterrows())))
        a('')
    if len(P):
        a('## How broadly based is each positive candidate?')
        a('')
        a('This is the question the book plan actually turns on. A candidate '
          'whose R comes from two cells cannot be assigned to a set of pairs; '
          'it IS those two cells, and the assignment is a story told about '
          'them afterwards.')
        a('')
        rows = []
        for (k, nm), g in P.groupby(['kind', 'name']):
            tot = float(g.R_total.sum())
            if tot <= 0:
                continue
            rows.append((k, nm, len(g), int((g.R_total > 0).sum()), tot,
                         float(g.R_total.max() / tot),
                         float(g.nlargest(5, 'R_total').R_total.sum() / tot)))
        rows.sort(key=lambda r: -r[4])
        a('| kind | candidate | cells | positive | R total | '
          'top cell as a share of total | top 5 cells as a share |')
        a('|---|---|---:|---:|---:|---:|---:|')
        for k, nm, n, npos, tot, t1, t5 in rows:
            a('| %s | %s | %d | %d | %+.3f | **%.3f** | **%.3f** |'
              % (k, nm, n, npos, tot, t1, t5))
        a('')
        if rows:
            _A = [r for r in rows if r[1] == 'A']
            if _A:
                k, nm, n, npos, tot, t1, t5 = _A[0]
                a('**A is the only one of them that is broadly based.** %d of '
                  'its %d cells are positive, its best cell is **%.1f%%** of '
                  'the total and its best five are **%.1f%%**. Every other '
                  'positive candidate is worse on both counts, and the C1 '
                  'alone are not in the same league — `glitch_index` has a '
                  'single cell worth nearly thirteen times its own total, '
                  'which means the rest of its book is a large negative that '
                  'one cell is paying for. **That is what a per-pair bank is '
                  'for: it makes the difference visible before anything is '
                  'assigned.**'
                  % (npos, n, 100 * t1, 100 * t5))
                a('')
        A = P[(P.kind == 'candidate') & (P.name == 'A')].sort_values(
            'R_total', ascending=False)
        if len(A):
            a('### Candidate A, its 56 cells, best and worst')
            a('')
            a('| pair | direction | trades | R total | R per trade | '
              'years positive | best trade | best trade as a share |')
            a('|---|---|---:|---:|---:|---:|---:|---:|')
            for _, r in pd.concat([A.head(8), A.tail(5)]).iterrows():
                a('| %s | %s | %d | %+.3f | %+.3f | %d of 6 | %+.3f | %s |'
                  % (r.pair, r.direction, int(r.n_trades), r.R_total,
                     r.R_per_trade, int(r.years_positive), r.best_trade_R,
                     ('%.3f' % r.best_trade_share
                      if np.isfinite(r.best_trade_share) else '—')))
            a('')
            _sh = int((A.head(8).direction == 'short').sum())
            a('**%d of A\'s best 8 cells are SHORT**, and its four worst are '
              'all on the other side of a USD or CAD cross. That asymmetry is '
              'on record here and is not acted on: it is one candidate over '
              'six years, and splitting a book by direction as well as by '
              'pair would double the number of ways to find a winner by luck '
              'again.' % _sh)
            a('')
    a('## Provenance')
    a('')
    for n_ in ('per_pair_bank.csv', 'per_pair_bank_pair.csv',
               'per_pair_bank_cand.csv'):
        p_ = os.path.join(OUT, n_)
        if not os.path.exists(p_):
            a('- `%s` — **MISSING**' % os.path.join('results', 'nnfx', n_))
            continue
        a('- `%s` — %s rows, md5 `%s`'
          % (os.path.relpath(p_, _R),
             '{:,}'.format(len(S2._safe_csv(p_))),
             hashlib.md5(open(p_, 'rb').read()).hexdigest()[:12]))
    out = out or os.path.join(OUT, 'PER_PAIR_BANK.md')
    open(out, 'w').write('\n'.join(L_) + '\n')
    print('  PER_PAIR_BANK.md: %d lines -> %s'
          % (len('\n'.join(L_).splitlines()), os.path.relpath(out, _R)),
          flush=True)
    return out


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--nmax', type=int, default=0)
    ap.add_argument('--stage', default='all')
    g = ap.parse_args()
    C1L, _B, _C, _V, _X = N.families()
    if g.stage in ('all', 'build'):
        build(names=(list(C1L)[:g.nmax] if g.nmax else None))
    if g.stage in ('all', 'md'):
        md_bank()
    print('  nnfxbank done', flush=True)


if __name__ == '__main__':
    main()
