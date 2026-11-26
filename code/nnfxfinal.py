"""ITEM 5 -- THE FINAL BOOK. PROTOCOL.md AMENDMENT 1, A7.

A7, declared before any count was known: *if a book clears B1 to B4 in both
rotations*, build the final version with admission on ALL of 2005-2015 at the
admission count that was best **on average across the two rotations**, run B5,
then STOP and report.

THE AVERAGING RULE IS WHY THIS IS NOT CIRCULAR. A K that is best on one
rotation's scoring window has been chosen by that window. Averaging the two
is declared in advance in A7 and is the same rule A11 uses for family (d).

THE FINAL BOOK HAS NO HOLD-OUT AND SAYS SO. Admission uses all eleven years,
so there is nothing left to score it on: 2016-2020 is computed and not
reported and 2021 onward is sealed. Every figure in FINAL_BOOK.md is
in-sample by construction. That is what A7 asks for -- the candidate for the
one-time confirm, which is Jack's call -- and it is labelled on every line.

IF NOTHING CLEARS B1 TO B4 IN BOTH ROTATIONS, this writes FINAL_BOOK.md
saying exactly that and builds nothing. A final book assembled anyway would
be a number with no gate behind it.
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
import nnfxbankev as BEV
import nnfxrep as RP
import l2sweep as S

OUT = os.path.join(ROOTOUT, 'nnfx')
BOUT = os.path.join(OUT, 'books')


def qualifying(D):
    """Families x share x mode x K that clear B1-B4 in BOTH rotations."""
    keys = ['family', 'share', 'mode', 'K']
    g = D.groupby(keys, dropna=False)
    ok = g.apply(lambda q: (len(q) == 2) and bool((q.clears_B1_B4 == 1).all()),
                 include_groups=False)
    return [k for k, v in ok.items() if v]


def best_K_on_average(D, fam, share, mode, metric='R_per_dip'):
    q = D[(D.family == fam) & (D['share'] == share) & (D['mode'] == mode)]
    av = q.groupby('K')[metric].mean()
    av = av[np.isfinite(av)]
    return (int(av.idxmax()), float(av.max())) if len(av) else (None, np.nan)


def select_ev(bankev, pairs, fam, K, share):
    """The family's own selection rule, run on the ELEVEN-YEAR window."""
    adm = BK.admit_mask(bankev['ev__R'], bankev['ev__R_ex_best_day'],
                        bankev['ev__best_trade'], bankev['ev__trades'],
                        share=share)
    col = {p: i for i, p in enumerate(pairs)}
    mem = []
    if fam == 'b_per_pair':
        for p in pairs:
            ok = np.nonzero(adm[:, col[p]])[0]
            if not len(ok):
                continue
            r = bankev['ev__R'][ok, col[p]]
            for j in ok[np.argsort(-r)][:K]:
                mem.append((int(j), p))
    elif fam in ('c_all_pairs', 'd_combined', 'e_fourcell'):
        sc = np.where(adm, bankev['ev__R'], 0.0).sum(axis=1)
        ok = np.nonzero(adm.sum(axis=1) > 0)[0]
        for j in ok[np.argsort(-sc[ok])][:K]:
            for p in pairs:
                if adm[j, col[p]]:
                    mem.append((int(j), p))
    return mem, adm


def run(verbose=True):
    S.load_costs(os.environ.get('FX_COST_TABLE',
                                os.path.join(ROOTOUT, 'cost_table_h22.csv')))
    D = pd.read_csv(os.path.join(BOUT, 'books_gates.csv'))
    qual = qualifying(D)
    L = ['# FINAL_BOOK — item 5', '',
         '**`PROTOCOL.md` AMENDMENT 1, A7. Built only if a book clears B1 to B4 '
         'in BOTH rotations.**', '']
    if not qual:
        nn = (int(D.null_runs.max())
              if 'null_runs' in D and np.isfinite(D.null_runs.max()) else 0)
        L += ['## Nothing qualifies, so nothing was built', '',
              '**%d book cells were tested against %d matched null runs and '
              'none clears B1 to B4 in both rotations.** A7 is conditional and '
              'the condition is not met, so there is no final book. Assembling '
              'one anyway would be a number with no gate behind it.' % (len(D), nn),
              '']
        c = D[D.clears_B1_B4 == 1]
        if len(c):
            L += ['%d cells clear B1 to B4 in **one** rotation. The closest to '
                  'qualifying, by the averaged return per dip A7 would have '
                  'used:' % len(c), '',
                  '| family | share | mode | K | rotation | R | R/dip | B1 | '
                  'B1b | B2 | B3 | B4 | %/yr |',
                  '|---|---:|---|---:|---|---:|---:|---|---|---|---|---|---:|']
            for _i, r in c.sort_values('R_per_dip', ascending=False).head(12).iterrows():
                L.append('| %s | %s | %s | %d | %s | %+.3f | %+.3f | %s | %s | '
                         '%s | %s | %s | %+.2f |'
                         % (r.family, RP._sh(r['share']), r['mode'], r.K,
                            r.rotation, r.R, r.R_per_dip,
                            'PASS' if r.B1 == 1 else 'fail',
                            'PASS' if r.B1b == 1 else 'fail',
                            'PASS' if r.B2 == 1 else 'fail',
                            'PASS' if r.B3 == 1 else 'fail',
                            'PASS' if r.B4 == 1 else 'fail',
                            r.b5_pct_per_year))
            L.append('')
        else:
            L += ['**No cell clears B1 to B4 in even one rotation.**', '']
        L += ['## What this does not say', '',
              'It does not say the searched books lost money — several are '
              'positive on data no sleeve was admitted on, and `BOOKS.md` '
              'reports every one. It says none of them beat the 95th '
              'percentile of the same book built from scrambled data while '
              'also surviving the one-event, hold-out and nudge tests in both '
              'rotations. **2016-2020 stays closed.** Opening it is Jack\'s '
              'call and nothing here earns it.']
        open(os.path.join(OUT, 'FINAL_BOOK.md'), 'w').write('\n'.join(L) + '\n')
        print('  FINAL_BOOK.md: nothing qualifies, nothing built (%d cells, '
              '%d clear B1-B4 in one rotation)' % (len(D), len(c)), flush=True)
        return None
    # ---- something qualifies: A7's rule picks among them
    S3.init_space()
    pairs, bankev = BEV.load()
    cands, _s, _m = CL.load()
    W = BO.World(pairs)
    best = None
    for (fam, share, mode, _K) in qual:
        K, av = best_K_on_average(D, fam, share, mode)
        if K is None:
            continue
        if best is None or av > best[3]:
            best = (fam, share, mode, av, K)
    fam, share, mode, av, K = best
    mem, _adm = select_ev(bankev, pairs, fam, K, share)
    acc = BO.Acc(W)
    for (j, p) in mem:
        acc.add(S3.mkcand(cands[j]), p, 'S%d' % j)
    sep, vote, cs, cv = acc.series()
    a = sep if mode == 'separate' else vote
    m = W.mask(BEV.EVY)
    st = BO.full(a, W.dates, m)
    row = dict(family=fam, share=share, mode=mode, K=K,
               avg_R_per_dip_in_rotations=av, sleeves=acc.n,
               admission='2005-2015, all eleven years', **st)
    pd.DataFrame([row]).to_csv(os.path.join(BOUT, 'final_book.csv'),
                              index=False)
    L += ['## The qualifying construction', '',
          '**%d cell(s) clear B1 to B4 in both rotations.** A7 picks '
          '**%s, share %s, %s mode, K=%d** — the K with the highest return '
          'per dip AVERAGED over the two rotations (%+.3f), a rule declared '
          'before the counts were known.'
          % (len(qual), fam, RP._sh(share), mode, K, av), '',
          '| | |', '|---|---|',
          '| admission | **all of 2005-2015** |',
          '| sleeves | %d |' % acc.n,
          '| R | %+.3f |' % st['R_total'],
          '| R a year | %+.3f |' % st['R_per_year'],
          '| verified worst dip | %.3f |' % st['dip_binding'],
          '| return per dip | **%+.3f** |' % st['R_per_dip'],
          '| sizing to 3.6%% daily / 5.4%% trailing | x%.3f |' % st['b5_scale'],
          '| **percent a year** | **%+.2f%%** |' % st['b5_pct_per_year'],
          '| days to pass the +10%% evaluation | %s |'
          % (st.get('b5_eval_days') if st.get('b5_eval_days') else 'never'),
          '| **B5** | **%s** |' % ('PASS' if st['b5_pct_per_year'] >= 12
                                   else 'fail — %.2f points short'
                                   % (12 - st['b5_pct_per_year'])), '',
          '## EVERY FIGURE ABOVE IS IN-SAMPLE', '',
          'Admission used all eleven years, so there is nothing left to score '
          'it on. That is what A7 asks for. **This is the candidate for the '
          'one-time 2016-2020 confirm and nothing more. STOPPING HERE.** '
          'Opening 2016-2020 is Jack\'s call.']
    open(os.path.join(OUT, 'FINAL_BOOK.md'), 'w').write('\n'.join(L) + '\n')
    print('  FINAL_BOOK.md: %s K=%d, %+.2f%% a year, STOPPED for Jack'
          % (fam, K, st['b5_pct_per_year']), flush=True)
    return row


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.parse_args()
    run()
