import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Significance on an episode basis. Bars are not independent observations.

THE COMPLAINT IS CORRECT, BUT IT DOES NOT APPLY EQUALLY TO EVERY NUMBER, and
saying which is which is most of the work.

  SURROGATE-BASED p-VALUES ARE ALREADY SOUND. The shape-separation nulls in
  16.4b-d, and the classifier nulls in classifier_validation.csv, recompute the
  WHOLE statistic on each surrogate panel. The null distribution therefore
  carries every bit of the serial and cross-pair dependence the real panel has --
  that is what makes it a randomisation test rather than a parametric one. No
  independence is assumed anywhere in them, so p=0.909 is p=0.909. They are
  recomputed here on episode means anyway, to show the verdict does not move.

  t-STATISTICS POOLED OVER BARS OR EVENTS ARE INFLATED, and by a lot. Every
  excursion contrast -- structure.py's chop-minus-trending, ninestate.py's
  big_test, the tier ordering -- divides by an SE built from the pooled count.
  Those are the numbers that need redoing and they are redone here.

TWO CORRECTIONS, BOTH APPLIED, because they fix different things.

  EPISODE BASIS collapses each state run to one observation -- the run's mean of
  each property -- so a 20-bar state contributes once. This fixes serial
  dependence WITHIN a pair. It does not fix the other half: the 28 pairs are
  triangulated from 8 currencies and move together, so 28 contemporaneous
  episodes are nothing like 28 independent ones.

  MOVING-BLOCK BOOTSTRAP over CALENDAR DATES fixes both at once. A block takes
  every pair on a run of consecutive dates, so contemporaneous cross-pair
  correlation is carried inside the block and serial dependence is carried by
  the block length. This is the primary test here; the episode basis is reported
  beside it because it is the more intuitive number and because the gap between
  the two shows how much of the dependence is cross-sectional rather than serial.

  Block length is swept -- 21, 63, 126 bars -- rather than picked, since a
  bootstrap that only works at one block length is not evidence. 63 is the
  headline: longer than the 15-bar median run and more than twice the 28-bar
  property window.

Writes results/episode_counts.csv, results/episode_separation.csv and
results/episode_excursion.csv.
"""
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
EV = os.path.join(ROOTOUT, 'entry_events.csv')
L1 = os.path.join(ROOTOUT, 'layer1_states.csv')
SPLIT = pd.Timestamp('2016-01-01')
NSHUF = int(os.environ.get('FX_NSHUF', 60))
NBOOT = int(os.environ.get('FX_NBOOT', 2000))
BLOCKS = (21, 63, 126)
HEAD = 63

from structval import properties, surrogate, MIN_SHARE, SHAPE, MAG
from combined import layers, product, confirm, DWELL, NEUT
from ninestate import nine


def episodes(lab, P, oos_only=True):
    """One row per (pair, state run): the run's mean of every property.

    A 20-bar state becomes ONE observation, not twenty.
    """
    keys = list(P)
    out = []
    for p in lab.columns:
        v = lab[p]
        m = v.notna() & (v != '')
        if oos_only:
            m &= (lab.index >= SPLIT)
        v = v[m]
        if len(v) < 20:
            continue
        gid = (v != v.shift()).cumsum()
        d = pd.DataFrame({k: P[k][p].reindex(v.index) for k in keys})
        g = d.groupby(gid).mean()
        g['state'] = v.groupby(gid).first()
        g['n'] = v.groupby(gid).size()
        g['pair'] = p
        g['date'] = v.groupby(gid).apply(lambda s: s.index[0])
        out.append(g)
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def gap(d, col, wcol=None):
    """Extreme-state gap in sd units, with the same 2% share floor as elsewhere."""
    d = d[[col, 'state']].dropna()
    if d.empty:
        return np.nan
    keep = d.state.value_counts(normalize=True)
    d = d[d.state.isin(keep[keep >= MIN_SHARE].index)]
    if d.state.nunique() < 2 or len(d) < 30:
        return np.nan
    g = d.groupby('state')[col].mean()
    return (g.max() - g.min()) / d[col].std()


def sep_ep(E, cols=NEUT):
    return float(np.nanmean([gap(E, c) for c in cols]))


def block_boot(df, stat, blocks=HEAD, n=NBOOT, seed=7):
    """Moving-block bootstrap over calendar dates.

    A block is a run of consecutive DATES carrying every pair on those dates, so
    cross-pair correlation rides along inside the block instead of being assumed
    away.
    """
    rng = np.random.default_rng(seed)
    d2 = df.sort_values('date').reset_index(drop=True)
    # factorised date codes are non-decreasing after the sort, so every block of
    # consecutive dates is a CONTIGUOUS row slice -- no dict lookup, and no
    # datetime64-vs-Timestamp key mismatch (which silently returned no rows at
    # all in the first version of this function).
    codes, uniq = pd.factorize(d2.date, sort=True)
    nd = len(uniq)
    if nd < 2 * blocks:
        return np.array([])
    lo = np.searchsorted(codes, np.arange(nd), 'left')
    hi = np.searchsorted(codes, np.arange(nd), 'right')
    starts = np.arange(nd - blocks + 1)
    k = int(np.ceil(nd / blocks))
    out = []
    for _ in range(n):
        a = rng.choice(starts, size=k, replace=True)
        idx = np.concatenate([np.arange(lo[x], hi[min(x + blocks - 1, nd - 1)])
                              for x in a])
        out.append(stat(d2.iloc[idx]))
    return np.array(out, float)


def two_sided(v, null=0.0):
    v = v[np.isfinite(v)]
    if not len(v):
        return np.nan
    p = min((v <= null).mean(), (v >= null).mean())
    return float(min(1.0, 2 * p))


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    fit = px.index < SPLIT
    P = properties(px)
    sh, act = layers(px, fit)
    LAB = {'structural M=%d' % DWELL: confirm(sh, DWELL),
           'product M=%d' % DWELL: product(sh, act, DWELL),
           'grid': nine(px, fit)[0]}

    print('EFFECTIVE SAMPLE SIZE, holdout')
    print('  %-18s %10s %10s %8s' % ('classifier', 'bars', 'episodes', 'ratio'))
    cnt = []
    EPS = {}
    for k, v in LAB.items():
        E = episodes(v, P)
        EPS[k] = E
        nb = int(v[v.index >= SPLIT].notna().sum().sum())
        print('  %-18s %10d %10d %7.1fx' % (k, nb, len(E), nb / max(len(E), 1)))
        cnt.append(dict(classifier=k, bars=nb, episodes=len(E),
                        ratio=nb / max(len(E), 1)))
    pd.DataFrame(cnt).to_csv(os.path.join(ROOTOUT, 'episode_counts.csv'),
                             index=False)
    print('  a t-statistic pooled over bars therefore overstates its sample by')
    print('  roughly this factor, and its |t| by about its square root.')

    # ---- shape separation, redone on episodes, against the same surrogates ----
    print('\nSHAPE SEPARATION ON EPISODE MEANS, holdout, %d surrogate draws each'
          % NSHUF)
    print('  one observation per state run. Same statistic, same nulls.')
    real = {k: sep_ep(E) for k, E in EPS.items()}
    rng = np.random.default_rng(31337)
    rows = []
    for kind in ('sign', 'iid'):
        acc = {k: [] for k in LAB}
        for _ in range(NSHUF):
            px2 = surrogate(px, kind, rng)
            P2 = properties(px2)
            s2, a2 = layers(px2, fit)
            for k in LAB:
                l2 = (nine(px2, fit)[0] if k == 'grid'
                      else product(s2, a2, DWELL) if k.startswith('product')
                      else confirm(s2, DWELL))
                acc[k].append(sep_ep(episodes(l2, P2)))
        for k in LAB:
            v = np.array(acc[k]); v = v[np.isfinite(v)]
            p = (1 + int((v >= real[k]).sum())) / (len(v) + 1)
            print('  %-5s %-18s surrogate %.3f +/- %.3f  real %.3f  p=%.3f'
                  '  corrected %+.3f'
                  % (kind, k, v.mean(), v.std(), real[k], p, real[k] - v.mean()))
            rows.append(dict(basis='episode', classifier=k, null=kind,
                             real=real[k], surrogate=v.mean(), sd=v.std(), p=p,
                             corrected=real[k] - v.mean()))

    # ---- and per-property, block bootstrapped ----
    print('\nSEPARATION BY PROPERTY, block bootstrap over calendar dates')
    print('  %-18s %-15s %8s %8s %20s' % ('classifier', 'property', 'bar gap',
                                          'ep gap', 'episode 95% CI'))
    for k, E in EPS.items():
        for c in NEUT + MAG:
            v = LAB[k][LAB[k].index >= SPLIT].stack()
            x = P[c][P[c].index >= SPLIT].stack()
            bg = gap(pd.DataFrame({c: x, 'state': v}).dropna(), c)
            eg = gap(E, c)
            bs = block_boot(E, lambda d, c=c: gap(d, c))
            bs = bs[np.isfinite(bs)]
            ci = (np.percentile(bs, 2.5), np.percentile(bs, 97.5)) if len(bs) \
                else (np.nan, np.nan)
            print('  %-18s %-15s %8.3f %8.3f   [%.3f, %.3f]'
                  % (k, c, bg, eg, ci[0], ci[1]))
            rows.append(dict(basis='per_property', classifier=k, prop=c,
                             bar_gap=bg, ep_gap=eg, ci_lo=ci[0], ci_hi=ci[1]))
    pd.DataFrame(rows).to_csv(os.path.join(ROOTOUT, 'episode_separation.csv'),
                              index=False)

    excursion(px)


def excursion(px):
    """Every excursion contrast that ever carried a t, redone on blocks."""
    if not (os.path.exists(EV) and os.path.exists(L1)):
        print('\nentry_events.csv or layer1_states.csv missing; skipping')
        return
    E = pd.read_csv(EV); E['date'] = pd.to_datetime(E.date)
    S = pd.read_csv(L1, parse_dates=['date'],
                    usecols=['date', 'pair', 'state_28', 'tier', 'shape',
                             'combined', 'activity'])
    X = E.merge(S, on=['date', 'pair'], how='left')
    X = X[X.oos].copy()
    print('\n' + '=' * 74)
    print('EXCURSION CONTRASTS REDONE. %d holdout events.' % len(X))
    print('These are the numbers the complaint actually bites on: every one was')
    print('a Welch t over pooled events.')

    def contrast(col, a_mask, b_mask, metric):
        def st(d):
            a, b = d[d._a], d[d._b]
            if len(a) < 20 or len(b) < 20:
                return np.nan
            if metric == 'ratio':
                return (b.mfe.mean() / abs(b.mae.mean())
                        - a.mfe.mean() / abs(a.mae.mean()))
            return b[metric].mean() - a[metric].mean()
        d = X.copy(); d['_a'], d['_b'] = a_mask, b_mask
        d = d[d._a | d._b]
        obs = st(d)
        a, b = d[d._a], d[d._b]
        if metric == 'ratio':
            naive = np.nan
        else:
            se = np.sqrt(a[metric].var() / len(a) + b[metric].var() / len(b))
            naive = (b[metric].mean() - a[metric].mean()) / se if se else np.nan
        out = dict(contrast=col, metric=metric, n_a=len(a), n_b=len(b),
                   observed=obs, naive_t=naive)
        for L in BLOCKS:
            bs = block_boot(d, st, blocks=L, n=NBOOT)
            bs = bs[np.isfinite(bs)]
            out['p_%d' % L] = two_sided(bs)
            out['se_%d' % L] = bs.std() if len(bs) else np.nan
        return out

    rows = []
    tr = X['shape'].eq('trending'); rest = X['shape'].notna() & ~tr
    rows.append(contrast('structure: non-trending minus trending', tr, rest,
                         'bars_to_peak'))
    rows.append(contrast('structure: non-trending minus trending', tr, rest,
                         'ratio'))
    rows.append(contrast('structure: non-trending minus trending', tr, rest,
                         'path_eff'))
    st_, sc_ = X.state_28.eq('strong trend'), X.state_28.eq('strong chop')
    for m in ('path_eff', 'bars_to_peak', 'mfe', 'ratio'):
        rows.append(contrast('grid: strong chop minus strong trend', st_, sc_, m))
    ag, df_ = X.tier.eq('all agree'), X.tier.eq('all differ')
    for m in ('ratio', 'bars_to_peak', 'path_eff'):
        rows.append(contrast('tier: all differ minus all agree', ag, df_, m))
    R = pd.DataFrame(rows)
    R.to_csv(os.path.join(ROOTOUT, 'episode_excursion.csv'), index=False)
    print('\n  %-40s %-12s %7s %8s %7s %7s %7s'
          % ('contrast', 'metric', 'obs', 'naive t', 'p@21', 'p@63', 'p@126'))
    for _, r in R.iterrows():
        print('  %-40s %-12s %+7.4f %8s %7.3f %7.3f %7.3f'
              % (r.contrast[:40], r.metric, r.observed,
                 '%+.2f' % r.naive_t if np.isfinite(r.naive_t) else '--',
                 r.p_21, r.p_63, r.p_126))
    print('\n  naive t is the published number: a Welch t over pooled events.')
    print('  p@L is the two-sided block-bootstrap p at block length L.')
    print('\nwrote episode_counts.csv, episode_separation.csv, '
          'episode_excursion.csv')


if __name__ == '__main__':
    main()
