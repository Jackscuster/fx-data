import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Per-pair CHARACTER, not per-pair read quality.

16.4u reported how well the classifier reads each pair. This is the different
question: what each pair IS. A structurally trendy pair should spend more days
trending, hold those runs longer, and do so in both halves of the data.

REPORTED PER PAIR: share of days in each of the four shape states and each of the
twelve combined states, median and mean run length per state, the 4x4 transition
matrix, the longest trending and ranging runs on record, and every one of those
computed separately on 1999-2015 and 2016-2026 with the rank correlation between
them.

STANDARDISATION HAD TO CHANGE FOR THIS QUESTION, AND THE FIRST RUN WAS INVALID
WITHOUT IT. classifier.zfit z-scores each axis PER PAIR -- v[fit].mean() on a
frame is per column -- so every pair's in-sample score is forced to mean 0 and
sd 1. Cutting that at a panel-level threshold hands every pair almost identical
state shares by construction, and the cross-pair spread that comes out is drift
in the holdout rather than character. The first run of this file measured exactly
that and its numbers are void.

Per-pair z-scoring is the correct choice for CLASSIFYING -- each pair judged
against its own history, so a quiet pair still gets a full range of states. It is
the wrong choice for COMPARING pairs. So this file standardises POOLED: one mean
and one standard deviation over the whole in-sample panel, which lets a pair that
is genuinely straighter carry a genuinely higher score. Both versions are
reported so the difference is visible.

THE TEST THAT DECIDES WHETHER ANY OF IT IS REAL. Pairs will always differ
somewhat -- 28 draws from anything spread out. So the dispersion of trending
share across pairs is compared with the SAME dispersion on sign surrogates, which
keep each pair's own volatility clustering and destroy everything else. If real
pairs spread no wider than surrogate pairs, the character differences are noise
and there is nothing for Layer 3 to route on. The IS-to-OOS rank correlation gets
the same treatment: a surrogate panel has no persistent character at all, so
whatever rank correlation IT produces is the floor.

Writes results/pair_character.csv, results/pair_transitions.csv,
results/pair_ranking.csv.
"""
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
SPLIT = pd.Timestamp('2016-01-01')
NSHUF = int(os.environ.get('FX_NSHUF', 15))
SHAPES = ['trending', 'ranging', 'trend-in-range', 'neither']

from structval import surrogate
from twoscores import classify
from combined import confirm, DWELL
from final import scores, activity, grid, DROP_TESTS, BUMP, ACTW
from twoscores import raw_parts


def zpool(A, fit):
    """z-score POOLED across the whole in-sample panel, not per pair.

    One mean and one sd for the entire panel, so cross-pair differences survive.
    """
    out = {}
    for k, v in A.items():
        f = v[fit].values.astype(float)
        m, s = np.nanmean(f), np.nanstd(f)
        out[k] = (v - m) / (s if s else 1.0)
    return out


def scores_pooled(px, fit, drop_tests=DROP_TESTS):
    T, C = raw_parts(px)
    C = dict(C)
    if drop_tests:
        C.pop('tests', None)
    zt, zc = zpool(T, fit), zpool(C, fit)
    return sum(zt[k] for k in T), sum(zc[k] for k in C)


def labels(px, fit, pooled=True):
    tr, ch = (scores_pooled(px, fit) if pooled
              else scores(px, fit, drop_tests=DROP_TESTS))
    a = activity(px, fit)
    adj = tr - a.replace(ACTW).astype(float) * BUMP
    sh, _ = classify(adj, ch, fit)
    cb = confirm((a + ' ' + sh).where(sh.notna() & a.notna()), DWELL)
    return sh, cb


def runs_of(v):
    v = v.dropna()
    if len(v) < 20:
        return {}
    gid = (v != v.shift()).cumsum()
    out = {}
    for _, g in v.groupby(gid):
        out.setdefault(g.iloc[0], []).append(len(g))
    return out


def per_pair(sh, comb, mask, pairs):
    rows = []
    for p in pairs:
        v = sh[p][mask].dropna()
        c = comb[p][mask].dropna()
        if len(v) < 200:
            continue
        share = v.value_counts(normalize=True)
        R = runs_of(v)
        rec = dict(pair=p, n=len(v))
        for s in SHAPES:
            rec['share_' + s] = float(share.get(s, 0.0))
            r = R.get(s, [])
            rec['med_' + s] = float(np.median(r)) if r else np.nan
            rec['mean_' + s] = float(np.mean(r)) if r else np.nan
            rec['max_' + s] = int(max(r)) if r else 0
        cs = c.value_counts(normalize=True)
        for k, x in cs.items():
            rec['c_' + k] = float(x)
        rec['trendiness'] = rec['share_trending'] - rec['share_ranging']
        rows.append(rec)
    return pd.DataFrame(rows).set_index('pair')


def transitions(sh, mask, pairs):
    rows = []
    for p in pairs:
        v = sh[p][mask].dropna()
        if len(v) < 200:
            continue
        a, b = v.values[:-1], v.values[1:]
        ch = a != b
        for s in SHAPES:
            m = ch & (a == s)
            if m.sum() < 5:
                continue
            d = pd.Series(b[m]).value_counts(normalize=True)
            for t in SHAPES:
                if t == s:
                    continue
                rows.append(dict(pair=p, frm=s, to=t, share=float(d.get(t, 0.0)),
                                 n=int(m.sum())))
    return pd.DataFrame(rows)


def spearman(a, b):
    x = pd.Series(a).rank(); y = pd.Series(b).rank()
    m = x.notna() & y.notna()
    if m.sum() < 5:
        return np.nan
    return float(np.corrcoef(x[m], y[m])[0, 1])


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    fit = np.asarray(px.index < SPLIT)
    oos = ~fit
    pairs = list(px.columns)
    sh, comb = labels(px, fit, pooled=True)
    shP, _ = labels(px, fit, pooled=False)
    bp = per_pair(shP, comb, np.ones(len(px), bool), pairs)
    print('PER-PAIR vs POOLED STANDARDISATION -- why this file changes it')
    print('  spread of trending share across the 28 pairs:')
    print('    per-pair z (what the classifier ships): %.3f to %.3f, range %.3f'
          % (bp.share_trending.min(), bp.share_trending.max(),
             bp.share_trending.max() - bp.share_trending.min()))

    A = per_pair(sh, comb, fit, pairs)
    B = per_pair(sh, comb, oos, pairs)
    both = per_pair(sh, comb, np.ones(len(px), bool), pairs)
    both.to_csv(os.path.join(ROOTOUT, 'pair_character.csv'))

    print('    pooled z (used below):                  %.3f to %.3f, range %.3f'
          % (both.share_trending.min(), both.share_trending.max(),
             both.share_trending.max() - both.share_trending.min()))
    print()
    print('SHARE OF DAYS IN EACH SHAPE STATE, per pair')
    print('  ranked most trending to most ranging, by (trending - ranging), full sample')
    print('  %-8s %9s %8s %9s %8s | %10s %6s %6s'
          % ('pair', 'trending', 'ranging', 'both', 'neither', 'trendiness',
             'medTrn', 'medRng'))
    for p, r in both.sort_values('trendiness', ascending=False).iterrows():
        print('  %-8s %9.3f %8.3f %9.3f %8.3f | %+10.3f %6.0f %6.0f'
              % (p, r.share_trending, r.share_ranging,
                 r['share_trend-in-range'], r.share_neither, r.trendiness,
                 r.med_trending, r.med_ranging))
    print('\n  spread of trending share: %.3f to %.3f (range %.3f)'
          % (both.share_trending.min(), both.share_trending.max(),
             both.share_trending.max() - both.share_trending.min()))
    print('  spread of trendiness:     %+.3f to %+.3f'
          % (both.trendiness.min(), both.trendiness.max()))

    print('\nLONGEST RUNS ON RECORD')
    t = both.sort_values('max_trending', ascending=False)
    print('  longest trending: %s'
          % ', '.join('%s %d' % (p, r.max_trending)
                      for p, r in t.head(5).iterrows()))
    t = both.sort_values('max_ranging', ascending=False)
    print('  longest ranging:  %s'
          % ', '.join('%s %d' % (p, r.max_ranging)
                      for p, r in t.head(5).iterrows()))
    print('  median across pairs: trending %d bars, ranging %d bars'
          % (both.max_trending.median(), both.max_ranging.median()))

    print('\nIS THE CHARACTER STABLE? 1999-2015 against 2016-2026')
    common = A.index.intersection(B.index)
    for k in ('share_trending', 'share_ranging', 'trendiness', 'med_trending',
              'med_ranging'):
        rho = spearman(A.loc[common, k], B.loc[common, k])
        print('  %-16s rank correlation %+.3f' % (k, rho))
    print('\n  %-8s %9s %9s | %9s %9s | %s'
          % ('pair', 'trend IS', 'trend OOS', 'trendy IS', 'trendy OOS', 'rank move'))
    ra = A.loc[common, 'trendiness'].rank(ascending=False)
    rb = B.loc[common, 'trendiness'].rank(ascending=False)
    for p in A.loc[common].sort_values('trendiness', ascending=False).index:
        print('  %-8s %9.3f %9.3f | %+9.3f %+9.3f | %2d -> %2d'
              % (p, A.loc[p, 'share_trending'], B.loc[p, 'share_trending'],
                 A.loc[p, 'trendiness'], B.loc[p, 'trendiness'],
                 int(ra[p]), int(rb[p])))
    rho_main = spearman(A.loc[common, 'trendiness'], B.loc[common, 'trendiness'])

    print('\nTRANSITIONS -- does a pair go trend to range directly?')
    T = transitions(sh, np.ones(len(px), bool), pairs)
    T.to_csv(os.path.join(ROOTOUT, 'pair_transitions.csv'), index=False)
    g = T[T.frm == 'trending'].groupby('to').share.mean()
    print('  pooled, leaving TRENDING: %s'
          % '  '.join('%s %.3f' % (k, v) for k, v in g.items()))
    g2 = T[T.frm == 'ranging'].groupby('to').share.mean()
    print('  pooled, leaving RANGING:  %s'
          % '  '.join('%s %.3f' % (k, v) for k, v in g2.items()))
    d = T[(T.frm == 'trending') & (T.to == 'ranging')].set_index('pair').share
    print('  trending -> ranging DIRECT, per pair: %.3f to %.3f (median %.3f)'
          % (d.min(), d.max(), d.median()))
    print('  most direct: %s' % ', '.join('%s %.3f' % (p, v)
                                          for p, v in d.nlargest(4).items()))
    print('  least direct: %s' % ', '.join('%s %.3f' % (p, v)
                                           for p, v in d.nsmallest(4).items()))

    print('\nNULL: is any of this more than 28 pairs spreading out? %d draws'
          % NSHUF)
    rng = np.random.default_rng(90210)
    sd_acc, rho_acc, rangeacc = [], [], []
    for i in range(NSHUF):
        px2 = surrogate(px, 'sign', rng)
        s2, c2 = labels(px2, fit)
        A2 = per_pair(s2, c2, fit, pairs)
        B2 = per_pair(s2, c2, oos, pairs)
        cm = A2.index.intersection(B2.index)
        full2 = per_pair(s2, c2, np.ones(len(px), bool), pairs)
        sd_acc.append(full2.share_trending.std())
        rangeacc.append(full2.share_trending.max() - full2.share_trending.min())
        rho_acc.append(spearman(A2.loc[cm, 'trendiness'], B2.loc[cm, 'trendiness']))
        if (i + 1) % 5 == 0:
            print('  ... %d/%d' % (i + 1, NSHUF), flush=True)
    print('\n  cross-pair sd of trending share: real %.4f  surrogate %.4f +/- %.4f'
          % (both.share_trending.std(), np.mean(sd_acc), np.std(sd_acc)))
    print('  cross-pair range:                real %.4f  surrogate %.4f'
          % (both.share_trending.max() - both.share_trending.min(),
             np.mean(rangeacc)))
    print('  IS-to-OOS rank correlation:      real %+.3f  surrogate %+.3f +/- %.3f'
          % (rho_main, np.mean(rho_acc), np.std(rho_acc)))
    p_sd = (1 + sum(1 for v in sd_acc if v >= both.share_trending.std())) / (len(sd_acc) + 1)
    p_rho = (1 + sum(1 for v in rho_acc if v >= rho_main)) / (len(rho_acc) + 1)
    print('  p(dispersion) = %.3f   p(rank correlation) = %.3f' % (p_sd, p_rho))
    rk = both.sort_values('trendiness', ascending=False)
    rk['rank'] = range(1, len(rk) + 1)
    rk[['share_trending', 'share_ranging', 'trendiness', 'rank']].to_csv(
        os.path.join(ROOTOUT, 'pair_ranking.csv'))
    print('\nwrote pair_character.csv, pair_transitions.csv, pair_ranking.csv')


if __name__ == '__main__':
    main()
