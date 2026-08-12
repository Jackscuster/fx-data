import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""IS-only selection of the structural cell, on a PRESENT-TENSE criterion.

structure.py's own 144-cell sweep selects on bars-to-peak and MFE/|MAE|. Those are
forward measurements and this project no longer treats them as verdicts on a
descriptive classifier, so the configuration was never chosen on the criterion it
is now judged by. This file redoes the selection properly.

THE CRITERION, WRITTEN DOWN BEFORE THE SWEEP RUNS:

  mean NULL-CORRECTED shape separation over the four neutral shape properties
  -- return autocorrelation, direction changes, mean crossings, mean same-sign
  run length -- none of which any classifier here is built from.

CORRECTED, NOT RAW, AND THAT IS THE WHOLE POINT. Raw separation rises with block
length: a cell whose states happen to persist longer separates further on
properties that are themselves autocorrelated, whether or not its rule means
anything. Selecting on raw separation would pick the most persistent cell and
call it the most descriptive. So every cell is measured against its OWN
surrogate -- same cell, same parameters, same dwell, price replaced by a sign
surrogate -- and the criterion is real minus surrogate.

  SELECT on IS-A (1999-2007). REQUIRE IS-B (2008-2015) to agree in sign.
  The holdout (2016-2026) appears nowhere until the winner is fixed.

The sign of the criterion is pre-specified here because, unlike the excursion
contrast, there is no ambiguity about which direction is good: a classifier that
describes shape separates on shape MORE than its own surrogate does. Positive.

THE DWELL IS NOT SWEPT. M=5 was fixed in 16.4c on persistence alone -- the
smallest confirmation dwell reaching an 11-bar median run -- and persistence is
not the criterion here, so it is held constant and the search space stays at the
144 cells structure.py specified.

Writes results/structsel_surface.csv (IS only, all 144 cells) and
results/structsel_result.csv (the winner, read once on the holdout).
"""
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
A_LO, A_HI = pd.Timestamp('1999-01-01'), pd.Timestamp('2008-01-01')
B_LO, B_HI = A_HI, pd.Timestamp('2016-01-01')
SPLIT = B_HI
M = 5
NSEL = int(os.environ.get('FX_NSEL', 40))     # surrogate draws for selection
NFIN = int(os.environ.get('FX_NSHUF', 120))   # surrogate draws for the final read

from structure import NS, BS, DS, RS, five_state
from structval import properties, surrogate, MIN_SHARE
from combined import confirm, NEUT

CELLS = [(n, b, d, r) for n in NS for b in BS for d in DS for r in RS]


def sep_block(lab, P, lo, hi):
    """Mean extreme-state gap over the neutral shape properties, in one block."""
    m = (lab.index >= lo) & (lab.index < hi)
    L = lab[m].stack()
    if L.empty:
        return np.nan
    out = []
    for k in NEUT:
        d = pd.DataFrame({'s': L, 'v': P[k][m].stack()}).dropna()
        d = d[d.s != '']
        keep = d.s.value_counts(normalize=True)
        d = d[d.s.isin(keep[keep >= MIN_SHARE].index)]
        if d.s.nunique() < 2 or len(d) < 1000:
            out.append(np.nan); continue
        g = d.groupby('s').v.mean()
        out.append((g.max() - g.min()) / d.v.std())
    return float(np.nanmean(out))


def sweep(px, P):
    """-> dict cell -> (A, B) block separations, at the fixed dwell."""
    out = {}
    for c in CELLS:
        lab = confirm(five_state(px, *c), M)
        out[c] = (sep_block(lab, P, A_LO, A_HI), sep_block(lab, P, B_LO, B_HI))
    return out


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    P = properties(px)
    print('IS-ONLY SELECTION over %d cells at dwell M=%d, %d surrogate draws'
          % (len(CELLS), M, NSEL))
    real = sweep(px, P)

    rng = np.random.default_rng(1301)
    acc = {c: ([], []) for c in CELLS}
    for i in range(NSEL):
        px2 = surrogate(px, 'sign', rng)
        P2 = properties(px2)
        for c, (a, b) in sweep(px2, P2).items():
            acc[c][0].append(a); acc[c][1].append(b)
        if (i + 1) % 10 == 0:
            print('  %d/%d draws' % (i + 1, NSEL), flush=True)

    rows = []
    for c in CELLS:
        sa, sb = np.nanmean(acc[c][0]), np.nanmean(acc[c][1])
        da, db = np.nanstd(acc[c][0]), np.nanstd(acc[c][1])
        ra, rb = real[c]
        rows.append(dict(N=c[0], B=c[1], D=c[2], R=c[3],
                         A_real=ra, A_surr=sa, A_corr=ra - sa,
                         A_z=(ra - sa) / da if da else np.nan,
                         B_real=rb, B_surr=sb, B_corr=rb - sb,
                         B_z=(rb - sb) / db if db else np.nan))
    S = pd.DataFrame(rows)
    S['agree'] = np.sign(S.A_corr) == np.sign(S.B_corr)
    S.to_csv(os.path.join(ROOTOUT, 'structsel_surface.csv'), index=False)

    print('\nTHE SURFACE, IS only. corrected = real minus own surrogate.')
    print('  cells with POSITIVE corrected separation on IS-A: %d of %d'
          % (int((S.A_corr > 0).sum()), len(S)))
    print('  cells with POSITIVE corrected separation on IS-B: %d of %d'
          % (int((S.B_corr > 0).sum()), len(S)))
    print('  cells positive on BOTH blocks:                    %d of %d'
          % (int(((S.A_corr > 0) & (S.B_corr > 0)).sum()), len(S)))
    print('  cells where the two blocks agree in sign:         %d of %d'
          % (int(S.agree.sum()), len(S)))
    print('\nMARGINALS -- mean IS-A corrected separation by each parameter')
    for k in ('N', 'B', 'D', 'R'):
        print(S.groupby(k)[['A_corr', 'B_corr', 'A_real', 'A_surr']].mean()
              .to_string(float_format=lambda v: '%+.4f' % v))
    print('\nTOP 10 CELLS BY IS-A CORRECTED SEPARATION, with their IS-B result')
    T = S.sort_values('A_corr', ascending=False)
    print(T.head(10)[['N', 'B', 'D', 'R', 'A_real', 'A_surr', 'A_corr', 'A_z',
                      'B_corr', 'B_z', 'agree']]
          .to_string(index=False, float_format=lambda v: '%+.4f' % v))

    both = S[(S.A_corr > 0) & (S.B_corr > 0)]
    if len(both):
        w = both.sort_values('A_corr', ascending=False).iloc[0]
        chosen, why = (int(w.N), int(w.B), float(w.D), float(w.R)), 'criterion'
    else:
        w = T.iloc[0]
        chosen, why = (int(w.N), int(w.B), float(w.D), float(w.R)), 'best-available'
        print('\nNO CELL IS POSITIVE ON BOTH BLOCKS. The criterion selects nothing.')
        print('The best IS-A cell is carried to the holdout anyway, so the holdout')
        print('read is on the record rather than withheld -- but it is a')
        print('best-available cell, not a cell that met the pre-specified bar.')
    print('\nCHOSEN CELL: N=%d B=%d D=%.2f R=%.2f   (%s)'
          % (chosen + (why,)))
    print('  IS-A corrected %+.4f (z %+.2f)   IS-B corrected %+.4f (z %+.2f)'
          % (w.A_corr, w.A_z, w.B_corr, w.B_z))

    print('\n' + '=' * 68)
    print('HOLDOUT, READ ONCE. %d surrogate draws of each kind.' % NFIN)
    lab = confirm(five_state(px, *chosen), M)
    ho = sep_block(lab, P, SPLIT, pd.Timestamp('2100-01-01'))
    out = []
    for kind in ('sign', 'iid'):
        rng2 = np.random.default_rng(5150)
        v = []
        for _ in range(NFIN):
            px2 = surrogate(px, kind, rng2)
            v.append(sep_block(confirm(five_state(px2, *chosen), M),
                               properties(px2), SPLIT,
                               pd.Timestamp('2100-01-01')))
        v = np.array(v); v = v[np.isfinite(v)]
        p = (1 + int((v >= ho).sum())) / (len(v) + 1)
        print('  %-5s surrogate %.3f +/- %.3f   real %.3f   p=%.3f  corrected %+.3f'
              % (kind, v.mean(), v.std(), ho, p, ho - v.mean()))
        out.append(dict(N=chosen[0], B=chosen[1], D=chosen[2], R=chosen[3], M=M,
                        selected_by=why, block='holdout', null=kind,
                        real=ho, surrogate=v.mean(), sd=v.std(), p=p,
                        corrected=ho - v.mean(),
                        A_corr=w.A_corr, B_corr=w.B_corr))
    pd.DataFrame(out).to_csv(os.path.join(ROOTOUT, 'structsel_result.csv'),
                             index=False)
    print('\nwrote structsel_surface.csv and structsel_result.csv')


def chosen_cell():
    """The selected cell, for combined.py. Falls back to structure.py's own."""
    f = os.path.join(ROOTOUT, 'structsel_result.csv')
    if os.path.exists(f):
        r = pd.read_csv(f).iloc[0]
        return int(r.N), int(r.B), float(r.D), float(r.R)
    return 3, 3, 1.00, 0.62


if __name__ == '__main__':
    main()
