import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Present-tense validation: does the structural definition describe SHAPE?

NO FORWARD MEASUREMENT ANYWHERE IN THIS FILE. A descriptive classifier is judged
on what it says about the window it just read -- coverage, run length, transition
diagonal, separation on realised properties, refit stability, and nulls. Whether
it predicts anything is a different question and is not asked here.

THE GAP THIS EXISTS TO CLOSE. The existing battery separates strongly on
properties that measure HOW MUCH a pair moved and weakly on properties that
measure WHAT SHAPE the movement made. Shape is what trend-versus-chop means, so
separation is measured here on shape properties specifically:

  SHAPE      return autocorrelation, range/path, direction changes per window,
             crossings of the window mean, mean same-sign run length,
             variance ratio (Lo-MacKinlay, k=5 and k=10)
  MAGNITUDE  realised vol, mean absolute move -- carried only as the reference
             the shape numbers are compared against

RANGE/PATH AND VARIANCE RATIO ARE NOT NEUTRAL for every classifier. range/path is
close kin to |net|/path, so a classifier with a straightness axis part-restates it;
that is flagged in the output rather than hidden, and autocorrelation, direction
changes, crossings and run length are the properties no classifier here is built
from.

THREE CLASSIFIERS, one battery, identical properties at a common window so the
comparison is like for like:

  structural   five states from swings, breaks and retracements (structure.py)
  grid         nine states from straightness x scale (ninestate.py)
  weighted     three states from the weighted score (classifier.py)

Writes results/structval.csv.
"""
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
SPLIT = pd.Timestamp('2016-01-01')
W = 28                      # common window for every property
NSHUF = int(os.environ.get('FX_NSHUF', 200))
SHAPE = ['autocorr', 'range_to_path', 'dir_changes', 'mean_crossings',
         'run_length', 'var_ratio_5', 'var_ratio_10']
MAG = ['realised_vol', 'avg_abs_move']


def properties(px):
    """Present-tense descriptors of the trailing window. All lagged one bar."""
    lp = np.log(px.astype(float)); rr = lp.diff()
    inf = [np.inf, -np.inf]
    sgn = np.sign(rr)
    dev = lp - lp.rolling(W).mean()
    cross = ((np.sign(dev) != np.sign(dev.shift(1))) & dev.notna()).rolling(W).sum()
    flips = (sgn != sgn.shift(1)).rolling(W).mean()

    def vr(k):
        return ((lp - lp.shift(k)).rolling(W).var()
                / (k * rr.rolling(W).var())).replace(inf, np.nan)

    P = {
        'autocorr': rr.rolling(W).corr(rr.shift(1)),
        'range_to_path': ((lp.rolling(W).max() - lp.rolling(W).min())
                          / rr.abs().rolling(W).sum()).replace(inf, np.nan),
        'dir_changes': flips,
        'mean_crossings': cross,
        # mean length of a same-sign run = bars / number of flips
        'run_length': (1.0 / flips.replace(0, np.nan)),
        'var_ratio_5': vr(5),
        'var_ratio_10': vr(10),
        'realised_vol': rr.rolling(W).std(),
        'avg_abs_move': rr.abs().rolling(W).mean(),
    }
    return {k: v.shift(1) for k, v in P.items()}


MIN_SHARE = 0.02


def separation(lab, P, oos_only=True, min_share=MIN_SHARE):
    """Gap between the extreme state means, in sd units of the property.

    STATES BELOW min_share ARE EXCLUDED FROM THE GAP. A max-minus-min over
    group means is set by whichever group is smallest and noisiest: at the
    loosest break settings 'drifting' collapses to SIX observations in
    1999-2007 and its mean alone fixed the gap, producing a corrected
    separation of +1.27 on that block against +0.03 on the next. Any state
    holding under 2% of the block's bars is dropped before the extremes are
    taken. This changes nothing already published -- the smallest holdout
    share in 16.4b/16.4c is 4.7% for the structural state, 8.6% for the grid
    and 1.4% for the twelve-state product, and only the first two feed a
    max-minus-min -- but it is what makes the IS blocks comparable.
    """
    rows = []
    for nm, X in P.items():
        a, b = lab, X
        if oos_only:
            a, b = a[a.index >= SPLIT], b[b.index >= SPLIT]
        d = pd.DataFrame({'s': a.stack(), 'v': b.stack()}).dropna()
        d = d[d.s != '']
        if d.s.nunique() < 2 or len(d) < 1000:
            rows.append(dict(prop=nm, gap_sd=np.nan)); continue
        keep = d.s.value_counts(normalize=True)
        d = d[d.s.isin(keep[keep >= min_share].index)]
        if d.s.nunique() < 2 or len(d) < 1000:
            rows.append(dict(prop=nm, gap_sd=np.nan)); continue
        g = d.groupby('s').v.mean()
        rows.append(dict(prop=nm, gap_sd=(g.max() - g.min()) / d.v.std(),
                         n_states=d.s.nunique()))
    return pd.DataFrame(rows).set_index('prop')


def persistence(lab):
    runs, diag = [], []
    for p in lab.columns:
        v = lab[p].replace('', np.nan).dropna()
        if len(v) < 100:
            continue
        b = np.flatnonzero(np.r_[True, v.values[1:] != v.values[:-1]])
        runs.append(np.diff(np.r_[b, len(v)]))
        diag.append((v.values[1:] == v.values[:-1]).mean())
    R = np.concatenate(runs)
    return dict(median_run=float(np.median(R)), mean_run=float(R.mean()),
                under5=float((R < 5).mean()), diagonal=float(np.mean(diag)))


def surrogate(px, kind, rng):
    lp = np.log(px.astype(float)); rr = lp.diff()
    if kind == 'sign':
        sg = pd.DataFrame(rng.choice([-1., 1.], size=rr.shape),
                          index=rr.index, columns=rr.columns)
        r2 = rr.abs() * sg
    else:
        r2 = pd.DataFrame({p: rng.permutation(rr[p].dropna().values.copy())
                           for p in rr.columns},
                          index=rr.dropna(how='all').index).reindex(rr.index)
    return np.exp(r2.cumsum().fillna(0))


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    fit = px.index < SPLIT
    P = properties(px)

    from structure import five_state
    from ninestate import nine
    from classifier import axes as cls_axes, classify as cls_classify
    LAB = {}
    LAB['structural'] = five_state(px, 3, 3, 1.00, 0.62)
    LAB['grid'] = nine(px, fit)[0]
    LAB['weighted'] = cls_classify(cls_axes(px), fit)[0]

    print('SEPARATION IN SD UNITS OF EACH PROPERTY, holdout, common window W=%d' % W)
    S = pd.DataFrame({k: separation(v, P).gap_sd for k, v in LAB.items()})
    S['kind'] = ['SHAPE' if i in SHAPE else 'magnitude' for i in S.index]
    S = S.loc[SHAPE + MAG]
    print(S.to_string(float_format=lambda v: '%.3f' % v))
    print('\nmean over SHAPE properties only:')
    for k in LAB:
        print('  %-11s %.3f' % (k, S.loc[SHAPE, k].mean()))
    print('mean over the two magnitude properties:')
    for k in LAB:
        print('  %-11s %.3f' % (k, S.loc[MAG, k].mean()))
    print('\nnote: range_to_path and the variance ratios are kin to |net|/path, so')
    print('the grid and weighted classifiers part-restate them. autocorr,')
    print('dir_changes, mean_crossings and run_length are built into none of the three.')
    NEUT = ['autocorr', 'dir_changes', 'mean_crossings', 'run_length']
    print('mean over the four NEUTRAL shape properties:')
    for k in LAB:
        print('  %-11s %.3f' % (k, S.loc[NEUT, k].mean()))

    print('\nPERSISTENCE, COVERAGE')
    for k, v in LAB.items():
        pr = persistence(v)
        cov = v[v.index >= SPLIT].stack().replace('', np.nan).dropna()
        cv = cov.value_counts(normalize=True)
        print('  %-11s median run %4.0f  diagonal %.3f  %2d states  min share %.3f'
              % (k, pr['median_run'], pr['diagonal'], cv.size, cv.min()))

    print('\nREFIT STABILITY (pre-2016 labels after refitting through 2020)')
    # the fit mask must be rebuilt for the truncated frame -- passing the
    # full-length boolean raises on a shorter index
    px20 = px[px.index < pd.Timestamp('2021-01-01')]
    fit20 = px20.index < SPLIT
    g20 = nine(px20, fit20)[0]
    for k, cur, new in (('grid', LAB['grid'], g20),
                        ('structural', LAB['structural'],
                         five_state(px20, 3, 3, 1.00, 0.62))):
        a = cur[fit].stack(); b = new.reindex(cur.index)[fit].stack()
        j = pd.concat([a.rename('x'), b.rename('y')], axis=1).dropna()
        print('  %-11s %.2f%% of %d pair-days identical'
              % (k, 100 * (j.x == j.y).mean(), len(j)))
    print('  structural has no fitted parameter at all -- swings, breaks and')
    print('  retracements come from price, so refitting cannot relabel history.')

    print('\nNULLS on the structural classifier, %d draws each' % NSHUF)
    rng = np.random.default_rng(4242)
    real = S.loc[NEUT, 'structural'].mean()
    for kind in ('sign', 'iid'):
        acc = []
        for _ in range(NSHUF):
            px2 = surrogate(px, kind, rng)
            lb = five_state(px2, 3, 3, 1.00, 0.62)
            acc.append(separation(lb, properties(px2)).gap_sd.reindex(NEUT).mean())
        acc = np.array(acc)
        acc = acc[np.isfinite(acc)]
        p = (1 + int((acc >= real).sum())) / (len(acc) + 1)
        print('  %-5s surrogate %.3f +/- %.3f   real %.3f   p=%.3f'
              % (kind, acc.mean(), acc.std(), real, p))
    S.to_csv(os.path.join(ROOTOUT, 'structval.csv'))
    print('\nwrote structval.csv')


if __name__ == '__main__':
    main()
