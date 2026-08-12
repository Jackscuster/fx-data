import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""The classifier pair by pair. Everything so far has been pooled over 28 pairs.

WHY POOLING HIDES THE ANSWER LAYER 3 NEEDS. A pooled separation of 0.46 is
consistent with the classifier working on twenty pairs and failing on eight, and
routing capital by pair is exactly the decision that turns on which. Nothing in
16.4b-d could see it.

EVERY PAIR GETS ITS OWN SURROGATE. A per-pair number compared against a pooled
null would be meaningless -- JPY crosses carry more volatility clustering than
EUR crosses and would clear a pooled bar for reasons that have nothing to do with
the classifier. So the surrogate draws are recomputed per pair and each pair is
scored against its own.

WHAT COUNTS AS FAILING, defined before the numbers are read:

  DEGENERATE  a state the classifier never assigns, or assigns to under 2% of
              the pair's holdout bars, so the vocabulary does not fit the pair
  FLAT        corrected shape separation at or below zero -- the pair's own
              surrogate describes its shape at least as well
  UNSTABLE    median run under 5 bars, i.e. the flickering the dwell was meant
              to fix has not been fixed for this pair

A pair can fail more than one way. Failing FLAT is expected almost everywhere
given 16.4d and is reported for completeness rather than as news; DEGENERATE and
UNSTABLE are the ones that would actually break a routing table.

Writes results/pair_classifier.csv.
"""
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
SPLIT = pd.Timestamp('2016-01-01')
NSHUF = int(os.environ.get('FX_NSHUF', 60))

from structval import properties, surrogate, MIN_SHARE
from combined import layers, product, confirm, DWELL, NEUT
from ninestate import nine

MAGP = ['realised_vol', 'avg_abs_move']


def pair_gap(v, x, cols_min=MIN_SHARE):
    d = pd.DataFrame({'s': v, 'v': x}).dropna()
    d = d[d.s != '']
    if len(d) < 200:
        return np.nan
    keep = d.s.value_counts(normalize=True)
    d = d[d.s.isin(keep[keep >= cols_min].index)]
    if d.s.nunique() < 2 or len(d) < 200:
        return np.nan
    g = d.groupby('s').v.mean()
    return (g.max() - g.min()) / d.v.std()


def pair_scores(lab, P, pairs):
    """-> DataFrame indexed by pair: mean shape gap, mean magnitude gap."""
    out = {}
    for p in pairs:
        v = lab[p][lab.index >= SPLIT]
        sh = np.nanmean([pair_gap(v, P[c][p][P[c].index >= SPLIT]) for c in NEUT])
        mg = np.nanmean([pair_gap(v, P[c][p][P[c].index >= SPLIT]) for c in MAGP])
        out[p] = (sh, mg)
    return pd.DataFrame(out, index=['shape', 'magnitude']).T


def runlen(v):
    v = v.replace('', np.nan).dropna()
    if len(v) < 30:
        return np.nan, np.nan
    b = np.flatnonzero(np.r_[True, v.values[1:] != v.values[:-1]])
    r = np.diff(np.r_[b, len(v)])
    return float(np.median(r)), float((r < 5).mean())


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    fit = px.index < SPLIT
    P = properties(px)
    sh, act = layers(px, fit)
    lab = product(sh, act, DWELL)
    shp = confirm(sh, DWELL)
    grid = nine(px, fit)[0]
    pairs = list(px.columns)

    real = pair_scores(lab, P, pairs)
    real_s = pair_scores(shp, P, pairs)
    real_g = pair_scores(grid, P, pairs)

    print('PER-PAIR SURROGATES, %d draws each, per pair, both kinds' % NSHUF)
    rng = np.random.default_rng(24601)
    acc = {k: [] for k in ('product', 'structural', 'grid')}
    for i in range(NSHUF):
        px2 = surrogate(px, 'sign', rng)
        P2 = properties(px2)
        s2, a2 = layers(px2, fit)
        acc['product'].append(pair_scores(product(s2, a2, DWELL), P2, pairs))
        acc['structural'].append(pair_scores(confirm(s2, DWELL), P2, pairs))
        acc['grid'].append(pair_scores(nine(px2, fit)[0], P2, pairs))
        if (i + 1) % 20 == 0:
            print('  %d/%d' % (i + 1, NSHUF), flush=True)
    S = {k: (pd.concat(v).groupby(level=0).mean(),
             pd.concat(v).groupby(level=0).std()) for k, v in acc.items()}

    rows = []
    for p in pairs:
        v = lab[p][lab.index >= SPLIT]
        med, u5 = runlen(v)
        cov = v.replace('', np.nan).dropna()
        shr = cov.value_counts(normalize=True)
        n_used = int((shr >= MIN_SHARE).sum())
        rows.append(dict(
            pair=p,
            shape=real.shape_ if False else real.loc[p, 'shape'],
            shape_surr=S['product'][0].loc[p, 'shape'],
            shape_corr=real.loc[p, 'shape'] - S['product'][0].loc[p, 'shape'],
            shape_z=(real.loc[p, 'shape'] - S['product'][0].loc[p, 'shape'])
            / S['product'][1].loc[p, 'shape'],
            mag=real.loc[p, 'magnitude'],
            mag_surr=S['product'][0].loc[p, 'magnitude'],
            mag_corr=real.loc[p, 'magnitude'] - S['product'][0].loc[p, 'magnitude'],
            mag_z=(real.loc[p, 'magnitude'] - S['product'][0].loc[p, 'magnitude'])
            / S['product'][1].loc[p, 'magnitude'],
            struct_shape_corr=real_s.loc[p, 'shape'] - S['structural'][0].loc[p, 'shape'],
            grid_shape_corr=real_g.loc[p, 'shape'] - S['grid'][0].loc[p, 'shape'],
            grid_mag_corr=real_g.loc[p, 'magnitude'] - S['grid'][0].loc[p, 'magnitude'],
            median_run=med, under5=u5,
            states_used=n_used, states_seen=int(shr.size),
            min_share=float(shr.min()), coverage=float(len(cov) / len(v)),
        ))
    R = pd.DataFrame(rows)
    R['DEGENERATE'] = R.states_used < R.states_seen
    R['FLAT'] = R.shape_corr <= 0
    R['UNSTABLE'] = R.median_run < 5
    R.to_csv(os.path.join(ROOTOUT, 'pair_classifier.csv'), index=False)

    print('\nPER PAIR, twelve-state product, holdout. Ranked by corrected SHAPE.')
    print('  %-8s %7s %7s %7s %6s %7s %7s %6s %6s %5s'
          % ('pair', 'shape', 'surr', 'corr', 'z', 'mag', 'magcorr', 'run',
             'used', 'cov'))
    for _, r in R.sort_values('shape_corr', ascending=False).iterrows():
        print('  %-8s %7.3f %7.3f %+7.3f %+6.2f %7.3f %+7.3f %6.0f %3d/%-2d %5.2f'
              % (r.pair, r['shape'], r.shape_surr, r.shape_corr, r.shape_z,
                 r['mag'], r.mag_corr, r.median_run, r.states_used,
                 r.states_seen, r.coverage))

    print('\nMAGNITUDE, ranked -- the axis that survives its null pooled')
    for _, r in R.sort_values('mag_corr', ascending=False).head(6).iterrows():
        print('  %-8s corrected %+.3f (z %+.2f)' % (r.pair, r.mag_corr, r.mag_z))
    print('  ...')
    for _, r in R.sort_values('mag_corr', ascending=False).tail(6).iterrows():
        print('  %-8s corrected %+.3f (z %+.2f)' % (r.pair, r.mag_corr, r.mag_z))

    print('\nSPREAD ACROSS PAIRS')
    for c, nm in (('shape_corr', 'shape corrected'), ('mag_corr', 'magnitude corrected'),
                  ('median_run', 'median run'), ('coverage', 'coverage')):
        print('  %-22s min %+.3f  median %+.3f  max %+.3f'
              % (nm, R[c].min(), R[c].median(), R[c].max()))

    print('\nFAILURES, by the definitions fixed above')
    for flag in ('DEGENERATE', 'UNSTABLE', 'FLAT'):
        bad = R[R[flag]]
        print('  %-11s %2d of %d%s' % (flag, len(bad), len(R),
                                       ('  ' + ' '.join(bad.pair)) if len(bad)
                                       and len(bad) <= 14 else ''))
    hard = R[R.DEGENERATE | R.UNSTABLE]
    print('\n  pairs failing on something other than FLAT: %s'
          % (' '.join(hard.pair) if len(hard) else 'none'))
    print('\nCROSS-CLASSIFIER, corrected shape by pair -- how many pairs positive')
    for c, nm in (('shape_corr', 'product'), ('struct_shape_corr', 'structural'),
                  ('grid_shape_corr', 'grid')):
        print('  %-11s %2d of %d pairs positive, median %+.3f'
              % (nm, int((R[c] > 0).sum()), len(R), R[c].median()))
    print('  grid MAGNITUDE %2d of %d pairs positive, median %+.3f'
          % (int((R.grid_mag_corr > 0).sum()), len(R), R.grid_mag_corr.median()))
    print('\nwrote pair_classifier.csv')


if __name__ == '__main__':
    main()
