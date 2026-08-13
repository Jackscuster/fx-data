import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Separation split by state. Trending, drifting and range scored one at a time.

EVERY NUMBER SO FAR HAS BEEN BLENDED. The metric was the gap between the extreme
state means, averaged over four properties -- one number for the whole
classifier. It cannot distinguish "both trend and chop separate" from "trend
carries it and chop is dead weight", and those call for different decisions.

THE METRIC HERE IS ONE-VERSUS-REST, SIGNED.

  sep(state, property) = (mean of that state - mean of every other state) / sd

Signed on purpose: trending should sit HIGH on autocorrelation and LOW on
direction changes, and a magnitude-only number would hide a state that separates
in the wrong direction. The headline per state is the mean of |sep| over the four
properties, which is what the blended number was implicitly averaging.

NULL-CORRECTED PER STATE. Each state is compared with the same state on a sign
surrogate at the same window, so the correction is per state and per property
rather than borrowed from the pooled figure.

COVERAGE, RUN LENGTH AND DIAGONAL ARE ALSO PER STATE. The diagonal is
P(still in s tomorrow | in s today), which is the number that matters for whether
a state can be acted on -- a classifier can hold a 20-bar median run overall while
one of its states flickers.

THE SWEEP RUNS TO N=70, a measured lookback near 400 bars, because corrected
separation was still climbing at 200. Run length and diagonal are reported beside
separation at every window, because separation only helps if the state still
turns over often enough to trade: a state that lasts a year is not a regime read
for an entry held weeks, and less separation on a state that moves is the better
trade.

Writes results/shapesplit.csv and results/shapesplit_pairs.csv.
"""
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
SPLIT = pd.Timestamp('2016-01-01')
NS = tuple(range(2, 71))
NSHUF = int(os.environ.get('FX_NSHUF', 15))
THREE = ['trending', 'drifting', 'range']
PROPS = ['autocorr', 'range_to_path', 'dir_changes', 'mean_crossings']

from structval import properties, surrogate
from shapescore import score_at, lookback


def longframe(lab, P, mask):
    st = lab[mask].stack()
    d = pd.DataFrame({'s': st})
    for c in PROPS:
        d[c] = P[c][mask].stack()
    d = d.dropna()
    d.index.names = ['date', 'pair']
    return d.reset_index()


def one_vs_rest(d, by=None):
    """-> {(state, prop): signed sep}. by='pair' gives {(pair, state): mean|sep|}."""
    out = {}
    if by is None:
        n = len(d)
        for c in PROPS:
            sd = d[c].std()
            g = d.groupby('s')[c].agg(['mean', 'size'])
            tot = d[c].sum()
            for s in THREE:
                if s not in g.index or g.loc[s, 'size'] < 200:
                    out[(s, c)] = np.nan; continue
                rest = (tot - g.loc[s, 'mean'] * g.loc[s, 'size']) \
                    / (n - g.loc[s, 'size'])
                out[(s, c)] = (g.loc[s, 'mean'] - rest) / sd
        return out
    for c in PROPS:
        sd = d.groupby('pair')[c].transform('std')
        d = d.assign(**{'_z_' + c: d[c] / sd})
    g = d.groupby(['pair', 's'])[['_z_' + c for c in PROPS]].agg(['mean', 'size'])
    tot = d.groupby('pair')[['_z_' + c for c in PROPS]].agg(['sum', 'size'])
    res = {}
    for (p, s), row in g.iterrows():
        vals = []
        for c in PROPS:
            k = '_z_' + c
            m, n_s = row[(k, 'mean')], row[(k, 'size')]
            S, n = tot.loc[p, (k, 'sum')], tot.loc[p, (k, 'size')]
            if n - n_s < 100 or n_s < 100:
                vals.append(np.nan); continue
            vals.append(m - (S - m * n_s) / (n - n_s))
        res[(p, s)] = float(np.nanmean(np.abs(vals)))
    return res


def state_stats(lab, mask):
    """-> per-state share, median run, diagonal."""
    L = lab[mask]
    st = L.stack()
    cv = st.value_counts(normalize=True)
    runs, stay, tot = {}, {}, {}
    for p in L.columns:
        v = L[p].dropna()
        if len(v) < 50:
            continue
        gid = (v != v.shift()).cumsum()
        for _, g in v.groupby(gid):
            runs.setdefault(g.iloc[0], []).append(len(g))
        a, b = v.values[:-1], v.values[1:]
        for s in THREE:
            m = a == s
            if m.sum():
                stay[s] = stay.get(s, 0) + int((b[m] == s).sum())
                tot[s] = tot.get(s, 0) + int(m.sum())
    return {s: dict(share=float(cv.get(s, 0.0)),
                    run=float(np.median(runs[s])) if s in runs else np.nan,
                    diag=(stay.get(s, 0) / tot[s]) if tot.get(s) else np.nan)
            for s in THREE}


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    fit = np.asarray(px.index < SPLIT)
    P = properties(px)
    print('SEPARATION SPLIT BY STATE. N = %d..%d, lookback to ~%d bars.'
          % (NS[0], NS[-1], int(lookback(px, NS[-1]))))
    print('one-vs-rest, signed. IS.')

    labs, real, stats = {}, {}, {}
    for N in NS:
        lab, _ = score_at(px, N, fit)
        labs[N] = lab
        real[N] = one_vs_rest(longframe(lab, P, fit))
        stats[N] = state_stats(lab, fit)

    print('\nNULLS, %d draws, per state per window' % NSHUF)
    rng = np.random.default_rng(31415)
    acc = {N: [] for N in NS}
    for i in range(NSHUF):
        px2 = surrogate(px, 'sign', rng)
        P2 = properties(px2)
        for N in NS:
            l2, _ = score_at(px2, N, fit)
            acc[N].append(one_vs_rest(longframe(l2, P2, fit)))
        if (i + 1) % 5 == 0:
            print('  %d/%d' % (i + 1, NSHUF), flush=True)

    rows = []
    for N in NS:
        lb = lookback(px, N)
        for s in THREE:
            r = np.nanmean([abs(real[N][(s, c)]) for c in PROPS])
            sv = np.nanmean([[abs(a[(s, c)]) for c in PROPS] for a in acc[N]])
            rec = dict(N=N, lookback=lb, state=s, sep=r, surr=sv, corr=r - sv,
                       **stats[N][s])
            for c in PROPS:
                rec['sep_' + c] = real[N][(s, c)]
            rows.append(rec)
    S = pd.DataFrame(rows)
    S.to_csv(os.path.join(ROOTOUT, 'shapesplit.csv'), index=False)

    print('\nPER STATE, IS. sep is mean |one-vs-rest| over the four properties.')
    for s in THREE:
        d = S[S.state == s]
        print('\n  %s' % s.upper())
        print('    %3s %5s | %6s %6s %8s | %6s %5s %6s'
              % ('N', 'days', 'sep', 'surr', 'corrected', 'share', 'run',
                 'diag'))
        for _, r in d[d.N.isin((2, 6, 13, 18, 26, 34, 44, 55, 70))].iterrows():
            print('    %3d %5.0f | %6.3f %6.3f %+8.3f | %6.3f %5.0f %6.3f'
                  % (r.N, r.lookback, r.sep, r.surr, r['corr'], r.share, r.run,
                     r.diag))

    print('\nWHICH PROPERTY CARRIES EACH STATE, at N=26 (144 bars). signed.')
    d = S[S.N == 26]
    print('    %-10s %s' % ('state', ' '.join('%16s' % c for c in PROPS)))
    for _, r in d.iterrows():
        print('    %-10s %s' % (r.state,
                                ' '.join('%+16.3f' % r['sep_' + c]
                                         for c in PROPS)))

    print('\nTHE TRADEOFF: corrected separation against how often the state turns')
    print('over. A state that lasts a year is not a read for an entry held weeks.')
    print('  %3s %5s | %s' % ('N', 'days', ' | '.join(
        '%-24s' % ('%s corr / run / diag' % s[:5]) for s in THREE)))
    for N in (2, 6, 13, 18, 22, 26, 30, 36, 44, 52, 60, 70):
        d = S[S.N == N].set_index('state')
        print('  %3d %5.0f | %s'
              % (N, d.lookback.iloc[0], ' | '.join(
                  '%+7.3f %5.0f %6.3f  ' % (d.loc[s, 'corr'], d.loc[s, 'run'],
                                            d.loc[s, 'diag']) for s in THREE)))

    print('\nPER PAIR, corrected, at three windows')
    pr = []
    for N in (13, 26, 44):
        rp = one_vs_rest(longframe(labs[N], P, fit), by='pair')
        sp = []
        r2 = np.random.default_rng(1618)
        for _ in range(max(4, NSHUF // 3)):
            px2 = surrogate(px, 'sign', r2)
            l2, _ = score_at(px2, N, fit)
            sp.append(one_vs_rest(longframe(l2, properties(px2), fit),
                                  by='pair'))
        for s in THREE:
            c = {p: rp.get((p, s), np.nan)
                 - np.nanmean([x.get((p, s), np.nan) for x in sp])
                 for p in px.columns}
            v = np.array([c[p] for p in px.columns], float)
            print('  N=%-3d %-9s %2d of 28 pairs positive, median %+.3f,'
                  ' best %+.3f worst %+.3f'
                  % (N, s, int(np.nansum(v > 0)), np.nanmedian(v),
                     np.nanmax(v), np.nanmin(v)))
            for p in px.columns:
                pr.append(dict(N=N, state=s, pair=p, corrected=c[p]))
    pd.DataFrame(pr).to_csv(os.path.join(ROOTOUT, 'shapesplit_pairs.csv'),
                            index=False)
    print('\nwrote shapesplit.csv and shapesplit_pairs.csv')


if __name__ == '__main__':
    main()
