import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Is the shape score three clusters, or one spread being cut in three?

THE TERCILE CUT IS A DESIGN CHOICE, NOT A FINDING. It forces trending, drifting
and range to be a third of days each, in every year, for every pair. If the
underlying score is genuinely trimodal that is close to free. If it is one
continuous distribution then 33/33/33 is a decision being taken by default, and a
year that was 20% trending and 45% chopping gets relabelled to fit the quota.

FOUR TESTS, because no single one settles multimodality.

  1. KDE local maxima. A trimodal score shows three peaks at sensible bandwidths.
     Counted across a range of bandwidths, since one bandwidth proves nothing.
  2. Gaussian mixture BIC for k = 1, 2, 3, by hand-rolled EM. If k=1 wins, the
     spread is one distribution. If k=3 wins by a wide margin the clusters are
     real. BIC already penalises the extra parameters.
  3. Excess kurtosis and the gap statistic. A mixture of three well-separated
     Gaussians is PLATYKURTIC -- flatter than normal. A single heavy-tailed
     spread is leptokurtic. The sign of excess kurtosis discriminates the two.
  4. The same four tests on a SIGN SURROGATE. If noise produces the same shape,
     whatever structure the histogram appears to have is not evidence.

THEN THE CONSEQUENCE, which is the part that matters for the estimator: shares
per year under the quota cut against shares under a FIXED cut at the same
in-sample thresholds. The quota version is 33/33/33 by construction in every
year. The fixed version lets the market say what it is, and the spread of its
yearly shares is the size of what the quota was suppressing.

Writes results/scoredist.csv and results/scoredist_years.csv.
"""
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
SPLIT = pd.Timestamp('2016-01-01')
N_LOCK = int(os.environ.get('FX_NLOCK', 19))
THREE = ['trending', 'drifting', 'range']

from structval import properties, surrogate
from shapescore import score_at, components, lookback
from classifier import zfit
from ninestate import tercile, BAND
from combined import confirm, DWELL


def raw_score(px, N, fit):
    C = components(px, N)
    Z = zfit({k: v for k, v in C.items()}, fit)
    return sum(Z[k] for k in C)


def kde_peaks(x, bws=(0.15, 0.20, 0.25, 0.30, 0.40)):
    g = np.linspace(np.percentile(x, 0.5), np.percentile(x, 99.5), 512)
    s = x.std()
    out = {}
    samp = x if len(x) <= 40000 else np.random.default_rng(0).choice(x, 40000,
                                                                    replace=False)
    for bw in bws:
        h = bw * s
        d = np.exp(-0.5 * ((g[:, None] - samp[None, :]) / h) ** 2).sum(1)
        pk = int(((d[1:-1] > d[:-2]) & (d[1:-1] > d[2:])).sum())
        out[bw] = pk
    return out


def gmm_bic(x, k, iters=200, seed=0):
    rng = np.random.default_rng(seed)
    x = x[np.isfinite(x)]
    n = len(x)
    mu = np.percentile(x, np.linspace(15, 85, k))
    sd = np.full(k, x.std() / k) + 1e-9
    w = np.full(k, 1.0 / k)
    for _ in range(iters):
        p = w * np.exp(-0.5 * ((x[:, None] - mu) / sd) ** 2) / (sd * np.sqrt(2 * np.pi))
        tot = p.sum(1, keepdims=True)
        tot[tot == 0] = 1e-300
        r = p / tot
        nk = r.sum(0) + 1e-9
        w = nk / n
        mu = (r * x[:, None]).sum(0) / nk
        sd = np.sqrt((r * (x[:, None] - mu) ** 2).sum(0) / nk) + 1e-9
    p = w * np.exp(-0.5 * ((x[:, None] - mu) / sd) ** 2) / (sd * np.sqrt(2 * np.pi))
    ll = np.log(np.clip(p.sum(1), 1e-300, None)).sum()
    npar = 3 * k - 1
    return float(-2 * ll + npar * np.log(n)), mu, w


def kurt(x):
    z = (x - x.mean()) / x.std()
    return float((z ** 4).mean() - 3.0)


def describe(x, tag):
    x = x[np.isfinite(x)]
    pk = kde_peaks(x)
    bics = {k: gmm_bic(x, k)[0] for k in (1, 2, 3)}
    best = min(bics, key=bics.get)
    print('  %-10s n=%d  sd=%.3f  skew=%+.3f  excess kurtosis=%+.3f'
          % (tag, len(x), x.std(),
             float((((x - x.mean()) / x.std()) ** 3).mean()), kurt(x)))
    print('    KDE peaks by bandwidth: %s'
          % '  '.join('%.2f->%d' % (b, v) for b, v in pk.items()))
    print('    BIC k=1 %.0f   k=2 %.0f   k=3 %.0f   -> best k=%d'
          % (bics[1], bics[2], bics[3], best))
    return dict(tag=tag, n=len(x), sd=x.std(), kurtosis=kurt(x),
                best_k=best, bic1=bics[1], bic2=bics[2], bic3=bics[3],
                peaks_min=min(pk.values()), peaks_max=max(pk.values()))


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    fit = np.asarray(px.index < SPLIT)
    lb = lookback(px, N_LOCK)
    print('SHAPE SCORE DISTRIBUTION at N=%d, measured lookback %.0f bars'
          % (N_LOCK, lb))
    sc = raw_score(px, N_LOCK, fit)
    x = sc.values.ravel()
    x = x[np.isfinite(x)]

    print('\nIS THE SCORE THREE CLUSTERS OR ONE SPREAD?')
    rows = [describe(x, 'real')]
    rng = np.random.default_rng(4242)
    px2 = surrogate(px, 'sign', rng)
    s2 = raw_score(px2, N_LOCK, fit).values.ravel()
    rows.append(describe(s2[np.isfinite(s2)], 'surrogate'))

    print('\n  quantiles of the real score')
    q = np.percentile(x, [1, 5, 10, 25, 33.3, 50, 66.7, 75, 90, 95, 99])
    print('    ' + '  '.join('%.0f%%:%+.2f' % (p, v) for p, v in
                             zip([1, 5, 10, 25, 33, 50, 67, 75, 90, 95, 99], q)))
    lo, hi = np.percentile(x[np.isfinite(x)], [33.333, 66.667])
    print('    the tercile cuts sit at %+.3f and %+.3f, %.2f sd apart'
          % (lo, hi, (hi - lo) / x.std()))
    pd.DataFrame(rows).to_csv(os.path.join(ROOTOUT, 'scoredist.csv'), index=False)

    print("""
  READ THIS TOGETHER. Three well-separated clusters would show three KDE peaks at
  most bandwidths, a BIC minimum at k=3, and NEGATIVE excess kurtosis. One
  continuous spread shows a single peak, k=1 or k=2 on BIC, and kurtosis at or
  above zero.""")

    # ---- the consequence: quota cut against a fixed cut ----
    print('\nWHAT THE QUOTA COSTS. Shares per year, holdout.')
    print('  QUOTA: the tercile cut refits nothing but ranks within the fitted')
    print('  CDF, so shares still drift; FIXED: the same IS thresholds applied')
    print('  as raw score levels, letting the market say what it is.')
    tq = tercile(sc, fit)
    labq = pd.DataFrame(np.where(tq.notna(),
                                 np.select([tq.values == 2, tq.values == 1],
                                           ['trending', 'drifting'], 'range'),
                                 None), index=sc.index, columns=sc.columns)
    labq = confirm(labq.where(tq.notna()), DWELL)
    f = np.where(np.isfinite(sc.values) & fit[:, None], sc.values, np.nan)
    LO, HI = np.nanpercentile(f, [33.333, 66.667])
    labf = pd.DataFrame(np.where(sc.notna(),
                                 np.select([sc.values >= HI, sc.values >= LO],
                                           ['trending', 'drifting'], 'range'),
                                 None), index=sc.index, columns=sc.columns)
    labf = confirm(labf.where(sc.notna()), DWELL)

    yr = []
    print('  %6s | %s | %s' % ('year',
                               ' '.join('%8s' % ('q_' + s[:5]) for s in THREE),
                               ' '.join('%8s' % ('f_' + s[:5]) for s in THREE)))
    for y, gq in labq[~fit].stack().groupby(labq[~fit].stack().index.get_level_values(0).year):
        gf = labf[~fit].stack()
        gf = gf[gf.index.get_level_values(0).year == y]
        a = gq.value_counts(normalize=True)
        b = gf.value_counts(normalize=True)
        print('  %6d | %s | %s'
              % (y, ' '.join('%8.3f' % a.get(s, 0) for s in THREE),
                 ' '.join('%8.3f' % b.get(s, 0) for s in THREE)))
        yr.append(dict(year=y, **{('quota_' + s): a.get(s, 0) for s in THREE},
                       **{('fixed_' + s): b.get(s, 0) for s in THREE}))
    Y = pd.DataFrame(yr)
    Y.to_csv(os.path.join(ROOTOUT, 'scoredist_years.csv'), index=False)
    print('\n  yearly spread (max - min share across holdout years)')
    for s in THREE:
        print('    %-9s quota %.3f   fixed %.3f'
              % (s, Y['quota_' + s].max() - Y['quota_' + s].min(),
                 Y['fixed_' + s].max() - Y['fixed_' + s].min()))
    print('\nwrote scoredist.csv and scoredist_years.csv')


if __name__ == '__main__':
    main()
