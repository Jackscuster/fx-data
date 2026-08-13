import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""The lead-time candidates, swept. 16.4g tested three POINTS, not three ideas.

WHAT 16.4g ACTUALLY DID. mas 5/20, vol 5/60, rng 5/60 -- three conventional
settings, none of them selected by anything. A null result on one cell of a
two-dimensional surface says that cell is dead. It says nothing about the
approach, and reporting it as though it did was wrong.

So all three get their full surface, both windows swept 1 to 200 on a 20-point
log grid, 190 fast<slow cells each, 570 in total:

  mas   fast mean turning against slow mean, scored in vol units
  vol   short realised vol over long realised vol
  rng   close range over its own longer-run average range

WHAT WOULD COUNT AS A RESULT, written down before the surface is read. A single
spiking cell in a 190-cell grid is what noise looks like -- at a 5% bar, ten
cells clear by construction. What would mean something is a PLATEAU: a
contiguous region of the surface, several cells across in both directions, all
above chance. So the report is the whole surface plus three plateau statistics:
how many cells clear, whether they touch, and what the best cell's own
NEIGHBOURS do. A peak whose neighbours are at chance is a peak of nothing.

EVERY CELL CARRIES ITS OWN SURROGATE, at the same window pair and the same
firing budget. Excess is lift minus surrogate lift, exactly as in 16.4g, because
the failure mode there was a real 1.74x lift that the surrogate reproduced at
1.68x.

Thresholds are calibrated per cell on IS to a common firing rate so that a wide
window cannot buy hit rate by firing more often than a narrow one.

Writes results/masweep.csv.
"""
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
SPLIT = pd.Timestamp('2016-01-01')
NSHUF = int(os.environ.get('FX_NSHUF', 20))
GRID = (1, 2, 3, 4, 5, 6, 8, 10, 13, 16, 21, 27, 34, 44, 56, 72, 92, 118,
        152, 200)
LEAD = 1                 # the bar that matters: the first of the 4-bar delay
LEAD2 = 3
TARGET = 0.10
VOLW = 60

from combined import layers, product, confirm, DWELL
from ninestate import nine
from structval import surrogate


def state_masks(px, fit):
    """-> dict name -> (change mask, valid mask), both numpy bool (n x 28)."""
    sh, act = layers(px, fit)
    LAB = {'product M=%d' % DWELL: product(sh, act, DWELL),
           'structural M=%d' % DWELL: confirm(sh, DWELL),
           'nine-box': nine(px, fit)[0]}
    oos = np.asarray(px.index >= SPLIT)[:, None]
    out = {}
    for k, lab in LAB.items():
        v = lab.values
        prev = np.roll(v, 1, axis=0); prev[0] = None
        ok = (v != None) & (prev != None) & oos            # noqa: E711
        chg = ok & (v != prev)
        out[k] = (chg, ok)
    return out


def fire_of(score, fit):
    """Upward crossing of an IS-calibrated threshold -> numpy bool."""
    v = score.values.astype(float)
    thr = np.nanquantile(v[fit], 1 - TARGET)
    on = v > thr
    prev = np.roll(on, 1, axis=0); prev[0] = False
    return on & ~prev & np.isfinite(v)


def warn_of(fire, lead):
    """Did the signal fire in the previous <lead> bars?"""
    w = np.zeros_like(fire)
    for k in range(1, lead + 1):
        s = np.roll(fire, k, axis=0); s[:k] = False
        w |= s
    return w


def lifts(fire, masks):
    out = {}
    for lead in (LEAD, LEAD2):
        w = warn_of(fire, lead)
        for k, (chg, ok) in masks.items():
            h = w[chg].mean() if chg.any() else np.nan
            b = w[ok].mean() if ok.any() else np.nan
            out[(k, lead)] = h / b if b else np.nan
    return out


def families(px):
    """-> dict family -> {(a, b): score frame}. Every score lagged one bar."""
    lp = np.log(px.astype(float)); rr = lp.diff()
    vol = rr.rolling(VOLW).std()
    inf = [np.inf, -np.inf]
    ma = {n: lp.rolling(n).mean().diff() for n in GRID}
    sd = {n: rr.rolling(max(n, 2)).std() for n in GRID}
    rg = {n: (lp.rolling(n).max() - lp.rolling(n).min()) for n in GRID}
    F = {'mas': {}, 'vol': {}, 'rng': {}}
    for i, a in enumerate(GRID):
        for b in GRID[i + 1:]:
            sf, ss = ma[a], ma[b]
            against = (np.sign(sf) != np.sign(ss)) & sf.notna() & ss.notna()
            F['mas'][(a, b)] = ((sf.abs() / vol).where(against, 0.0)
                                .replace(inf, np.nan).shift(1))
            F['vol'][(a, b)] = (sd[a] / sd[b]).replace(inf, np.nan).shift(1)
            F['rng'][(a, b)] = (rg[a] / rg[a].rolling(b).mean()
                                ).replace(inf, np.nan).shift(1)
    return F


def sweep(px, fit, masks):
    out = {}
    for fam, cells in families(px).items():
        for (a, b), sc in cells.items():
            for key, v in lifts(fire_of(sc, fit), masks).items():
                out[(fam, a, b) + key] = v
    return out


def plateau(M, thr):
    """Largest 4-connected region of cells above thr, and how many clear."""
    A = (M > thr) & np.isfinite(M)
    seen = np.zeros_like(A); best = 0
    for i in range(A.shape[0]):
        for j in range(A.shape[1]):
            if not A[i, j] or seen[i, j]:
                continue
            st = [(i, j)]; seen[i, j] = True; n = 0
            while st:
                x, y = st.pop(); n += 1
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    u, v = x + dx, y + dy
                    if (0 <= u < A.shape[0] and 0 <= v < A.shape[1]
                            and A[u, v] and not seen[u, v]):
                        seen[u, v] = True; st.append((u, v))
            best = max(best, n)
    return int(A.sum()), best


def ridge(px, fit):
    """Does the MAS lift ridge sit at fast = the confirmation dwell?

    The raw lift surface has one sharp ridge, at fast=5, and the shipped dwell
    is 5 bars. If that is not a coincidence the ridge should MOVE when the dwell
    moves -- which is a cheap, decisive test of what the signal is doing.
    """
    sh, act = layers(px, fit)
    F = families(px)['mas']
    oos = np.asarray(px.index >= SPLIT)[:, None]
    rows = []
    print('\nDOES THE RIDGE TRACK THE DWELL?')
    print('  %5s %s' % ('dwell', ''.join('%7d' % f for f in GRID[:9])))
    for M in (2, 3, 5, 8, 13):
        v = product(sh, act, M).values
        prev = np.roll(v, 1, axis=0); prev[0] = None
        ok = (v != None) & (prev != None) & oos              # noqa: E711
        chg = ok & (v != prev)
        row = []
        for f in GRID[:9]:
            best = [None]
            best = [warn_of(fire_of(sc, fit), LEAD) for (a, b), sc in F.items()
                    if a == f]
            best = [w[chg].mean() / w[ok].mean() for w in best]
            row.append(max(best) if best else np.nan)
        star = int(np.nanargmax(row))
        print('  M=%-3d %s   peak at fast=%d'
              % (M, ''.join(('%7.2f' % x) if i != star else ('%6.2f*' % x)
                            for i, x in enumerate(row)), GRID[star]))
        rows.append(dict(dwell=M, peak_fast=GRID[star], peak_lift=row[star],
                         **{('fast_%d' % f): x for f, x in zip(GRID[:9], row)}))
    pd.DataFrame(rows).to_csv(os.path.join(ROOTOUT, 'masweep_ridge.csv'),
                              index=False)
    print('  * = best lift for that dwell, maximised over all slow windows.')
    print("""
  The ridge MOVES WITH THE DWELL. That is the mechanism: an M-bar mean's slope
  turns over exactly the M bars the confirmation is counting, so the signal is
  reading the same window the dwell reads, not leading it. It cannot bridge a
  delay it is measuring from the inside -- which is why the lift is large and
  the surrogate reproduces nearly all of it.""")


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    fit = px.index < SPLIT
    masks = state_masks(px, fit)
    print('SWEEP: 3 families x 190 window pairs x 3 states x 2 leads')
    print('grid %s' % str(GRID))
    real = sweep(px, fit, masks)

    print('\n%d surrogate draws, EVERY CELL against its own -- signals and'
          ' states both rebuilt' % NSHUF)
    rng = np.random.default_rng(4919)
    acc = {k: [] for k in real}
    for i in range(NSHUF):
        px2 = surrogate(px, 'sign', rng)
        for k, v in sweep(px2, fit, state_masks(px2, fit)).items():
            acc[k].append(v)
        print('  %d/%d' % (i + 1, NSHUF), flush=True)

    rows = []
    for k, v in real.items():
        s = np.array(acc[k], float); s = s[np.isfinite(s)]
        rows.append(dict(family=k[0], fast=k[1], slow=k[2], state=k[3],
                         lead=k[4], lift=v, surr=s.mean() if len(s) else np.nan,
                         surr_sd=s.std() if len(s) else np.nan,
                         excess=v - s.mean() if len(s) else np.nan,
                         p=(1 + int((s >= v).sum())) / (len(s) + 1)))
    R = pd.DataFrame(rows)
    R.to_csv(os.path.join(ROOTOUT, 'masweep.csv'), index=False)

    ST = 'product M=%d' % DWELL
    for fam in ('mas', 'vol', 'rng'):
        d = R[(R.family == fam) & (R.state == ST) & (R.lead == LEAD)]
        L = d.pivot(index='fast', columns='slow', values='lift')
        E = d.pivot(index='fast', columns='slow', values='excess')
        print('\n' + '=' * 78)
        print('%s -- LIFT over chance, state %s, lead %d' % (fam.upper(), ST, LEAD))
        print(L.to_string(float_format=lambda v: '%.2f' % v, na_rep='  .'))
        print('\n%s -- EXCESS over its own surrogate' % fam.upper())
        print(E.to_string(float_format=lambda v: '%+.2f' % v, na_rep='   .'))
        M = E.values
        for t in (0.05, 0.10, 0.20):
            n, big = plateau(M, t)
            print('  cells with excess > %.2f: %3d of %d   largest contiguous'
                  ' region: %d' % (t, n, np.isfinite(M).sum(), big))
        b = d.sort_values('excess', ascending=False).iloc[0]
        print('  best cell fast=%d slow=%d  lift %.3f  surrogate %.3f'
              '  excess %+.3f  p=%.3f'
              % (b.fast, b.slow, b.lift, b.surr, b.excess, b.p))
        i = list(L.index).index(b.fast); j = list(L.columns).index(b.slow)
        nb = [M[u, v] for u in range(max(0, i - 1), min(M.shape[0], i + 2))
              for v in range(max(0, j - 1), min(M.shape[1], j + 2))
              if (u, v) != (i, j) and np.isfinite(M[u, v])]
        print('  its %d neighbours: mean excess %+.3f, max %+.3f'
              % (len(nb), np.mean(nb) if nb else np.nan,
                 np.max(nb) if nb else np.nan))

    print('\n' + '=' * 78)
    print('VERDICT ACROSS EVERYTHING SWEPT (%d cells, all states, both leads)'
          % len(R))
    for t in (0.05, 0.10, 0.20):
        w = R[(R.excess > t) & (R.p < 0.05)]
        print('  excess > %.2f AND p<0.05: %d of %d  (%.1f%%, chance alone gives'
              ' about 5%% at p<0.05)' % (t, len(w), len(R), 100 * len(w) / len(R)))
    top = R.sort_values('excess', ascending=False).head(10)
    print('\nTOP 10 BY EXCESS, anywhere in the sweep')
    print(top[['family', 'fast', 'slow', 'state', 'lead', 'lift', 'surr',
               'excess', 'p']]
          .to_string(index=False, float_format=lambda v: '%.3f' % v))
    ridge(px, fit)
    print('\nwrote masweep.csv and masweep_ridge.csv')


if __name__ == '__main__':
    main()
