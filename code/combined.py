import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""The combined classifier: structural shape crossed with an activity layer.

NOTHING FORWARD-LOOKING IN THIS FILE. Same present-tense battery as structval.py
-- separation on realised properties, persistence, refit stability, coverage,
nulls. Whether any of it predicts is a different question and is not asked here.

FLICKERING, and the categorical form of hysteresis. The raw structural state has
a 3-bar median run with 62% of runs under 5 bars. That is a signal firing, not a
regime. The nine-state grid gets its persistence from a hysteresis band around
its tercile cuts, but the structural state has no continuous score to put a band
around -- it is categorical. The equivalent is a CONFIRMATION DWELL: a new state
must print M consecutive bars before it is adopted, and the previous state is
held until then. Switching back needs the same M bars, so the rule is symmetric
in the way a hysteresis band is. It costs M-1 bars of recognition lag and is
strictly causal: bar t reads only bars t-M+1..t, each already lagged upstream.

COVERAGE -- THE 42% FIGURE WAS 'broken', NOT 'no swings'. Measured across the
whole swing-width grid, 'no swings' is 0.9-1.0% of bars at every N, and zero in
the holdout. The structural vocabulary already labels essentially every bar, so
there is no unlabelled 70% and nothing for a fallback layer to fill. What is
true is that ONE state holds nearly half the bars -- 'broken' at 44%/46%/41%/37%
for N=2/3/5/8 -- while 'trending' holds 6-10%. That is a coverage problem of a
different kind and a fallback cannot touch it.

So the two classifiers are combined the way that actually uses both: not shape
where available and activity in the gaps, but ACTIVITY ON EVERY BAR CROSSED WITH
SHAPE ON EVERY BAR.

  product   shape (trending/broken/range/drifting) x activity tercile
            (weak/medium/strong) from the grid's scale axis = 12 states
  fallback  shape where it fires, activity only in the gaps -- built and
            reported anyway, since it is what a 42% gap would have needed, and
            it is within 0.001 of the raw structural state because the gap is
            1% wide

SEPARATION IS NOT COMPARABLE ACROSS STATE COUNTS. The gap between the extreme
state means grows mechanically with the number of states: a 12-state classifier
has more chances at an extreme than a 4-state one. Two things are done about it.
eta squared -- between-state variance over total -- is reported alongside, and
every comparison that matters is made on the NULL-CORRECTED value, where the
surrogate carries the identical classifier, the identical state count and the
identical dwell. That correction is the only cross-classifier number here that
means anything.

Writes results/combined_states.csv and results/combined_validation.csv.
"""
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
SPLIT = pd.Timestamp('2016-01-01')
NSHUF = int(os.environ.get('FX_NSHUF', 200))
MS = (1, 2, 3, 5, 8, 13, 21)        # confirmation dwells swept
DWELL = 5                           # the shipped dwell, fixed on persistence


def _cfg():
    """The structural cell selected on IS by structsel.py.

    Read from the CSV rather than imported: structsel.py imports confirm() from
    here, so an import the other way would be circular.
    """
    f = os.path.join(ROOTOUT, 'structsel_result.csv')
    if os.path.exists(f):
        r = pd.read_csv(f).iloc[0]
        return int(r.N), int(r.B), float(r.D), float(r.R)
    return 3, 3, 1.00, 0.62         # structure.py's own, pre-selection


CFG = None                          # resolved at call time by layers()
SHAPE_STATES = ['trending', 'broken', 'range', 'drifting']
ACT = {0.0: 'weak', 1.0: 'medium', 2.0: 'strong'}

from structval import properties, separation, persistence, surrogate, SHAPE, MAG, W
NEUT = ['autocorr', 'dir_changes', 'mean_crossings', 'run_length']


def confirm(lab, M):
    """Categorical hysteresis. A new state must print M consecutive bars before
    it is adopted; until then the previous state is held.

    Causal by construction: the adopted label at bar t is the label of the most
    recent run that had already reached M bars by t.
    """
    if M <= 1:
        return lab.copy()
    out = {}
    for p in lab.columns:
        v = lab[p]
        m = v.notna() & (v != '')
        s = v.where(m)
        gid = (s != s.shift()).cumsum()
        k = s.groupby(gid).cumcount() + 1
        out[p] = s.where(k >= M).ffill().where(m)
    return pd.DataFrame(out)


def layers(px, fit, cfg=None):
    """-> (shape, activity) frames, both defined on every bar."""
    from structure import five_state
    from ninestate import raw_axes, tercile
    sh = five_state(px, *(cfg or _cfg()))
    sh = sh.where(sh.isin(SHAPE_STATES))
    act = tercile(raw_axes(px)['scale'], fit).replace(ACT)
    return sh, act.where(act.isin(list(ACT.values())))


def product(sh, act, M=1):
    lab = (act + ' ' + sh).where(sh.notna() & act.notna())
    return confirm(lab, M)


def fallback(sh, act, M=1):
    q = 'quiet ' + act
    return confirm(sh.where(sh.notna(), q.where(act.notna())), M)


def eta2(lab, X):
    d = pd.DataFrame({'s': lab[lab.index >= SPLIT].stack(),
                      'v': X[X.index >= SPLIT].stack()}).dropna()
    d = d[d.s != '']
    if d.s.nunique() < 2 or len(d) < 1000:
        return np.nan
    g = d.groupby('s').v
    return float((g.count() * (g.mean() - d.v.mean()) ** 2).sum()
                 / ((d.v - d.v.mean()) ** 2).sum())


def score(lab, P):
    """-> (mean extreme gap, mean eta2) over the four neutral shape properties."""
    s = separation(lab, P).gap_sd.reindex(NEUT)
    e = [eta2(lab, P[k]) for k in NEUT]
    return float(s.mean()), float(np.nanmean(e))


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    fit = px.index < SPLIT
    P = properties(px)
    from ninestate import nine
    sh, act = layers(px, fit)
    print('structural cell selected on IS: N=%d B=%d D=%.2f R=%.2f' % _cfg())
    grid = nine(px, fit)[0]

    print('COVERAGE OF THE RAW STRUCTURAL STATE')
    from structure import five_state
    cv = five_state(px, *_cfg()).stack().replace('', np.nan).dropna() \
        .value_counts(normalize=True)
    print(cv.to_string(float_format=lambda v: '%.3f' % v))
    print('  "no swings" is %.1f%% of all bars and 0%% of holdout bars -- there is'
          % (100 * cv.get('no swings', 0)))
    print('  no unlabelled 70%. The coverage problem is that ONE state holds')
    print('  %.0f%% of bars while "trending" holds %.0f%%.'
          % (100 * cv.max(), 100 * cv['trending']))

    BUILD = {'structural': lambda M: confirm(sh, M),
             'fallback': lambda M: fallback(sh, act, M),
             'product': lambda M: product(sh, act, M)}
    rows = []
    for nm, b in BUILD.items():
        print('\n%s -- confirmation dwell sweep' % nm)
        print('  %3s %11s %9s %8s %9s %10s %8s %7s'
              % ('M', 'median run', 'mean run', 'under5', 'diagonal',
                 'gap sd', 'eta2', 'states'))
        for M in MS:
            lab = b(M)
            pr = persistence(lab)
            g, e = score(lab, P)
            n = lab[lab.index >= SPLIT].stack().replace('', np.nan).dropna().nunique()
            print('  %3d %11.0f %9.1f %7.1f%% %9.3f %10.3f %8.4f %7d'
                  % (M, pr['median_run'], pr['mean_run'], 100 * pr['under5'],
                     pr['diagonal'], g, e, n))
            rows.append(dict(classifier=nm, M=M, median_run=pr['median_run'],
                             mean_run=pr['mean_run'], under5=pr['under5'],
                             diagonal=pr['diagonal'], gap_sd=g, eta2=e,
                             n_states=n))
    gp = persistence(grid)
    gg, ge = score(grid, P)
    print('\n  grid, for reference   median run %.0f  under5 %.1f%%  diagonal %.3f'
          '  gap sd %.3f  eta2 %.4f  9 states'
          % (gp['median_run'], 100 * gp['under5'], gp['diagonal'], gg, ge))
    rows.append(dict(classifier='grid', M=0, median_run=gp['median_run'],
                     mean_run=gp['mean_run'], under5=gp['under5'],
                     diagonal=gp['diagonal'], gap_sd=gg, eta2=ge, n_states=9))
    C = pd.DataFrame(rows)
    C.to_csv(os.path.join(ROOTOUT, 'combined_validation.csv'), index=False)

    # The dwell is chosen for persistence, not fitted to any outcome: the
    # smallest M whose median run reaches the target the flickering complaint
    # named. It is a display parameter and the whole curve is printed above.
    TARGET = 11
    cc = C[C.classifier == 'product']
    ok = cc[cc.median_run >= TARGET]
    M = int(ok.M.iloc[0]) if len(ok) else int(cc.M.iloc[-1])
    print('\nsmallest dwell reaching an %d-bar median run is M=%d' % (TARGET, M))

    lab = product(sh, act, M)
    LAB = {'product M=%d' % M: lab, 'structural M=%d' % M: confirm(sh, M),
           'structural raw': confirm(sh, 1), 'grid': grid}
    print('\nSEPARATION IN SD UNITS OF EACH PROPERTY, holdout, common window W=%d'
          % W)
    S = pd.DataFrame({k: separation(v, P).gap_sd for k, v in LAB.items()})
    S['kind'] = ['SHAPE' if i in SHAPE else 'magnitude' for i in S.index]
    S = S.loc[SHAPE + MAG]
    print(S.to_string(float_format=lambda v: '%.3f' % v))
    for nm, sel in (('all seven SHAPE properties', SHAPE),
                    ('the four NEUTRAL shape properties', NEUT),
                    ('the two magnitude properties', MAG)):
        print('  mean over %s:' % nm)
        for k in LAB:
            print('    %-18s %.3f' % (k, S.loc[sel, k].mean()))

    print('\nPERSISTENCE AND COVERAGE, holdout')
    for k, v in LAB.items():
        pr = persistence(v)
        o = v[v.index >= SPLIT]
        cv2 = o.stack().replace('', np.nan).dropna().value_counts(normalize=True)
        print('  %-18s median run %3.0f  under5 %5.1f%%  diagonal %.3f  '
              '%2d states  min share %.3f  labelled %.1f%%'
              % (k, pr['median_run'], 100 * pr['under5'], pr['diagonal'],
                 cv2.size, cv2.min(), 100 * o.notna().sum().sum()
                 / (o.shape[0] * o.shape[1])))
    print('\n  product state shares, holdout')
    print(lab[lab.index >= SPLIT].stack().replace('', np.nan).dropna()
          .value_counts(normalize=True).to_string(float_format=lambda v: '%.3f' % v))

    print('\nREFIT STABILITY (pre-2016 labels after refitting through 2020)')
    px20 = px[px.index < pd.Timestamp('2021-01-01')]
    sh20, act20 = layers(px20, px20.index < SPLIT)
    for k, cur, new in (('product', lab, product(sh20, act20, M)),
                        ('structural', LAB['structural M=%d' % M],
                         confirm(sh20, M))):
        a = cur[fit].stack(); b = new.reindex(cur.index)[fit].stack()
        j = pd.concat([a.rename('x'), b.rename('y')], axis=1).dropna()
        print('  %-11s %.2f%% of %d pair-days identical'
              % (k, 100 * (j.x == j.y).mean(), len(j)))
    print('  only the activity layer has a fitted parameter -- the scale tercile')
    print('  cut. The shape layer and the dwell come from price alone.')

    # NULLS. One surrogate draw serves every classifier, so the comparison is
    # paired and the properties are only rebuilt once per draw.
    print('\nNULLS, %d draws each. The surrogate carries the identical'
          ' classifier,' % NSHUF)
    print('state count and dwell, which is what makes these comparable at all.')
    CAND = {'structural raw': lambda s, a: confirm(s, 1),
            'structural M=%d' % M: lambda s, a: confirm(s, M),
            'product M=%d' % M: lambda s, a: product(s, a, M),
            'grid': None}
    real = {k: score(v, P)[0] for k, v in LAB.items()}
    rng = np.random.default_rng(90210)
    out = []
    for kind in ('sign', 'iid'):
        acc = {k: [] for k in CAND}
        for _ in range(NSHUF):
            px2 = surrogate(px, kind, rng)
            P2 = properties(px2)
            s2, a2 = layers(px2, fit)
            for k, f in CAND.items():
                l2 = nine(px2, fit)[0] if f is None else f(s2, a2)
                acc[k].append(score(l2, P2)[0])
        for k in CAND:
            v = np.array(acc[k]); v = v[np.isfinite(v)]
            r = real[k]
            p = (1 + int((v >= r).sum())) / (len(v) + 1)
            print('  %-5s %-18s surrogate %.3f +/- %.3f  real %.3f  p=%.3f'
                  '  corrected %+.3f'
                  % (kind, k, v.mean(), v.std(), r, p, r - v.mean()))
            out.append(dict(classifier=k, null=kind, surrogate=v.mean(),
                            sd=v.std(), real=r, p=p, corrected=r - v.mean()))
    pd.concat([C, pd.DataFrame(out)], ignore_index=True) \
        .to_csv(os.path.join(ROOTOUT, 'combined_validation.csv'), index=False)
    lab.to_csv(os.path.join(ROOTOUT, 'combined_states.csv'))
    print('\nwrote combined_states.csv and combined_validation.csv')


if __name__ == '__main__':
    main()
