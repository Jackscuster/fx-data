import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Is the transition itself a thing, or just the boundary between two states?

A transition matrix says how often chop follows trend. It does not say whether
the BARS AT THE CHANGE look different from the bars either side of it. If they
do, the change is an event with its own character and deserves its own label. If
they do not, it is only where one description stops and the next begins.

NOTHING FORWARD-LOOKING. Every property is the same trailing-window descriptor
used everywhere else, already lagged. This asks what the bars at a change LOOK
like, not what follows them.

TWO QUESTIONS, and the second is the one that matters.

  1. EDGE vs INTERIOR. Do bars with age <= 3 differ from bars with age >= 15,
     WITHIN the same state? Conditioning on the state is essential -- comparing
     all young bars to all old bars would just rediscover that short-lived
     states are different states.

  2. DIRECTION. Is chop-to-trend a different event from trend-to-chop? Same
     comparison, but split by which transition produced the run. If entering
     'trending' from 'range' looks like entering 'range' from 'trending' with
     the sign flipped, direction carries nothing.

THE OBVIOUS TRAP, and why the answer to 1 is partly mechanical. Every property
here is a rolling statistic over a 28-bar window, and the dwell needs 5 bars of
confirmation. A bar 3 days into a new state is describing a window that is mostly
the OLD state. So some edge-vs-interior difference must exist for reasons that
have nothing to do with regimes. The control for that is the surrogate: it has
the same windows, the same dwell and the same rolling overlap, so whatever the
overlap manufactures appears in it too.

SIGNIFICANCE IS BLOCK-BOOTSTRAPPED over calendar dates, from episodes.py. Bars
at an edge are heavily clustered in time -- that is what an edge is -- so a
pooled t here would be worse than usual.

Writes results/transition_edge.csv and results/transition_pairs.csv.
"""
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
SPLIT = pd.Timestamp('2016-01-01')
NSHUF = int(os.environ.get('FX_NSHUF', 40))
NBOOT = int(os.environ.get('FX_NBOOT', 2000))
EDGE, DEEP = 3, 15

from structval import properties, surrogate
from combined import layers, product, confirm, DWELL, NEUT
from episodes import block_boot, two_sided
from ninestate import nine

MAGP = ['realised_vol', 'avg_abs_move']


def tagged(lab, P, oos=True):
    """Long frame: one row per labelled bar, with age, previous state, props."""
    keys = NEUT + MAGP
    out = []
    for p in lab.columns:
        v = lab[p].replace('', np.nan).dropna()
        if oos:
            v = v[v.index >= SPLIT]
        if len(v) < 100:
            continue
        gid = (v != v.shift()).cumsum()
        age = v.groupby(gid).cumcount() + 1
        prev = v.groupby(gid).first().shift().reindex(gid.values)
        d = pd.DataFrame({k: P[k][p].reindex(v.index) for k in keys})
        d['state'] = v.values
        d['prev'] = prev.values
        d['age'] = age.values
        d['pair'] = p
        d['date'] = v.index
        out.append(d)
    return pd.concat(out, ignore_index=True)


def edge_gap(d, col):
    """Edge minus interior, in sd units, pooled within state then averaged.

    Within-state so the contrast cannot be answered by 'young bars are in
    different states'. Each state's difference is weighted by its interior count.
    """
    d = d[[col, 'state', 'age']].dropna()
    if len(d) < 500:
        return np.nan
    e = d[d.age <= EDGE]; i = d[d.age >= DEEP]
    if len(e) < 100 or len(i) < 100:
        return np.nan
    sd = d[col].std()
    num = den = 0.0
    for s in d.state.unique():
        a, b = e[e.state == s][col], i[i.state == s][col]
        if len(a) < 30 or len(b) < 30:
            continue
        num += len(b) * (a.mean() - b.mean()); den += len(b)
    return (num / den / sd) if den else np.nan


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    fit = px.index < SPLIT
    P = properties(px)
    sh, act = layers(px, fit)
    LAB = {'product M=%d' % DWELL: product(sh, act, DWELL),
           'structural M=%d' % DWELL: confirm(sh, DWELL),
           'grid': nine(px, fit)[0]}

    print('EDGE vs INTERIOR, within state. age <= %d against age >= %d.'
          % (EDGE, DEEP))
    print('holdout, %d block-bootstrap replicates, %d surrogate draws'
          % (NBOOT, NSHUF))
    T = {k: tagged(v, P) for k, v in LAB.items()}
    for k, d in T.items():
        print('  %-18s %6d edge bars, %6d interior bars'
              % (k, int((d.age <= EDGE).sum()), int((d.age >= DEEP).sum())))

    rng = np.random.default_rng(8675309)
    surr = {k: {c: [] for c in NEUT + MAGP} for k in LAB}
    for _ in range(NSHUF):
        px2 = surrogate(px, 'sign', rng)
        P2 = properties(px2)
        s2, a2 = layers(px2, fit)
        for k in LAB:
            l2 = (nine(px2, fit)[0] if k == 'grid'
                  else product(s2, a2, DWELL) if k.startswith('product')
                  else confirm(s2, DWELL))
            d2 = tagged(l2, P2)
            for c in NEUT + MAGP:
                surr[k][c].append(edge_gap(d2, c))

    rows = []
    print('\n  %-18s %-15s %8s %9s %9s %8s' % ('classifier', 'property',
                                               'edge-int', 'surrogate',
                                               'corrected', 'boot p'))
    for k, d in T.items():
        for c in NEUT + MAGP:
            obs = edge_gap(d, c)
            sv = np.array(surr[k][c], float); sv = sv[np.isfinite(sv)]
            bs = block_boot(d, lambda x, c=c: edge_gap(x, c), n=NBOOT)
            p = two_sided(bs)
            print('  %-18s %-15s %+8.3f %+9.3f %+9.3f %8.3f'
                  % (k, c, obs, sv.mean(), obs - sv.mean(), p))
            rows.append(dict(classifier=k, prop=c, observed=obs,
                             surrogate=sv.mean(), sd=sv.std(),
                             corrected=obs - sv.mean(), boot_p=p))
    pd.DataFrame(rows).to_csv(os.path.join(ROOTOUT, 'transition_edge.csv'),
                              index=False)
    print('\n  edge-int is what the bars at a change look like relative to bars')
    print('  deep inside the same state. surrogate is the same quantity with')
    print('  price replaced -- it captures the part that is only rolling-window')
    print('  overlap, since a 28-bar window 3 bars into a new state is still')
    print('  mostly describing the old one. corrected is the residue.')

    # ---- direction ----
    print('\n' + '=' * 74)
    print('DIRECTION. Is chop-to-trend a different event from trend-to-chop?')
    k = 'structural M=%d' % DWELL
    d = T[k]
    e = d[(d.age <= EDGE) & d.prev.notna()]
    pairs = (e.groupby(['prev', 'state']).size()
             .rename('n').reset_index().sort_values('n', ascending=False))
    pairs = pairs[pairs.n >= 300]
    print('  %s, transitions with at least 300 edge bars' % k)
    print('  %-12s %-12s %6s %s' % ('from', 'to', 'n',
                                    ' '.join('%14s' % c for c in NEUT)))
    rows2 = []
    base = {c: d[d.age >= DEEP][c].mean() for c in NEUT}
    sds = {c: d[c].std() for c in NEUT}
    for _, r in pairs.iterrows():
        g = e[(e.prev == r.prev) & (e.state == r.state)]
        vals = [(g[c].mean() - base[c]) / sds[c] for c in NEUT]
        print('  %-12s %-12s %6d %s'
              % (r.prev, r.state, r.n, ' '.join('%+14.3f' % v for v in vals)))
        rows2.append(dict(classifier=k, frm=r.prev, to=r.state, n=int(r.n),
                          **{c: v for c, v in zip(NEUT, vals)}))
    R2 = pd.DataFrame(rows2)
    R2.to_csv(os.path.join(ROOTOUT, 'transition_pairs.csv'), index=False)

    print('\n  ANTISYMMETRY TEST: if direction carries nothing, X->Y and Y->X')
    print('  are the same displacement with opposite sign.')
    seen = set()
    for _, r in R2.iterrows():
        key = tuple(sorted((r.frm, r.to)))
        if key in seen or r.frm == r.to:
            continue
        b = R2[(R2.frm == r.to) & (R2.to == r.frm)]
        if b.empty:
            continue
        seen.add(key)
        b = b.iloc[0]
        f = [r[c] for c in NEUT]; g = [b[c] for c in NEUT]
        anti = -np.array(g)
        print('    %-10s <-> %-10s  corr(fwd, -rev) %+.3f   |fwd| %.3f  |rev| %.3f'
              % (r.frm, r.to, np.corrcoef(f, anti)[0, 1] if len(f) > 2 else np.nan,
                 np.abs(f).mean(), np.abs(g).mean()))
    print('\nwrote transition_edge.csv and transition_pairs.csv')


if __name__ == '__main__':
    main()
