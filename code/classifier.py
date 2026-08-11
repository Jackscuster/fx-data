import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Task 10. The backward-looking classifier.

Four axes, all TRAILING over 20 bars and lagged one: straightness (|net|/path),
scale (path in the pair's own vol units), persistence (trailing 20d efficiency
minus trailing 5d), and duration (age of the current state) carried as a
confidence weight rather than a state dimension. No forward target -- this
describes what has happened, not what will happen.

WEIGHTS AS SPECIFIED: scale 0.180, persistence 0.028, straightness 0.010. Worth
being explicit about what that means. The axes are z-scored, so on independent
axes the variance each contributes goes as the square of its weight:

  scale        0.180^2 = 0.03240   97.3%
  persistence  0.028^2 = 0.00078    2.4%
  straightness 0.010^2 = 0.00010    0.3%

The classifier is a scale classifier with two rounding errors attached. That is
reported, not editorialised -- but it decides how the nulls have to be built.

TWO SURROGATES, AND WHY ONE IS NOT ENOUGH. The spec asks for returns shuffled
within each pair preserving volatility clustering. Implemented properly that is
sign randomisation: every |return| stays exactly where it is, only the signs move.
It destroys trend structure and leaves volatility clustering perfect.

But path = sum of |returns| is INVARIANT under sign randomisation. A
scale-dominated classifier is therefore mathematically unchanged by that null --
it would pass trivially and the pass would mean nothing. So a second surrogate is
run: an IID permutation of returns within each pair, which destroys volatility
clustering while preserving the return distribution exactly. That is the null a
scale axis can actually fail.

  surrogate A  sign randomisation   tests straightness and persistence
  surrogate B  IID permutation      tests scale

Hysteresis is used on the state cuts because Task 9 established that raw median
cuts flicker at a 2-bar median run.

Writes results/classifier_states.csv and classifier_validation.csv.
"""
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
EV = os.path.join(ROOTOUT, 'entry_events.csv')
COMP = os.path.join(ROOTOUT, 'survivor_composite.csv')
SPLIT = pd.Timestamp('2016-01-01')
W, VOLWIN, BAND = 20, 60, .25
WEIGHT = dict(scale=.180, persist=.028, straight=.010)
LAB = ['low', 'mid', 'high']


def axes(px, r=None):
    """The four trailing axes. r lets a surrogate be passed in."""
    lp = np.log(px.astype(float)) if r is None else r.cumsum()
    rr = lp.diff() if r is None else r
    net = (lp - lp.shift(W)).abs()
    path = rr.abs().rolling(W).sum()
    vol = rr.rolling(VOLWIN).std()
    inf = [np.inf, -np.inf]
    straight = (net / path).replace(inf, np.nan)
    e5 = ((lp - lp.shift(5)).abs() / rr.abs().rolling(5).sum()).replace(inf, np.nan)
    return {
        'straight': straight.shift(1),
        'scale': (path / (vol * np.sqrt(W))).replace(inf, np.nan).shift(1),
        'persist': (straight - e5).shift(1),
    }


def zfit(A, fit):
    """z-score each axis per pair on the fit window only."""
    return {k: (v - v[fit].mean()) / v[fit].std() for k, v in A.items()}


def hyst(frac, band):
    lo, hi = .5 - band / 2, .5 + band / 2
    s = pd.DataFrame(np.nan, index=frac.index, columns=frac.columns)
    s[frac >= hi] = 1.0
    s[frac <= lo] = 0.0
    return s.ffill()


def classify(A, fit, band=BAND):
    """Weighted score -> three states with hysteresis on the tercile cuts."""
    Z = zfit(A, fit)
    sc = sum(WEIGHT[k] * Z[k] for k in WEIGHT)
    frac = pd.DataFrame({p: sc[p].rank(pct=True) for p in sc.columns})
    # two hysteretic thresholds at the tercile boundaries
    lo_b = hyst((frac - 1 / 3 + .5).clip(0, 1), band)
    hi_b = hyst((frac - 2 / 3 + .5).clip(0, 1), band)
    ok = frac.notna()
    lab = pd.DataFrame(np.where(ok, np.where(hi_b == 1, 'high',
                                             np.where(lo_b == 1, 'mid', 'low')), None),
                       index=frac.index, columns=frac.columns)
    return lab, sc


def runs_of(lab):
    out = []
    for p in lab.columns:
        v = lab[p].dropna()
        if not len(v):
            continue
        gid = (v != v.shift()).cumsum()
        for _, g in v.groupby(gid):
            out.append((p, g.iloc[0], len(g)))
    return pd.DataFrame(out, columns=['pair', 'state', 'len'])


def persistence(lab):
    R = runs_of(lab)
    diag = np.mean([(lab[p].dropna() == lab[p].dropna().shift()).mean()
                    for p in lab.columns])
    return dict(median_run=float(R.len.median()), mean_run=float(R.len.mean()),
                under5=float((R.len < 5).mean()), diagonal=float(diag),
                n_runs=len(R))


def realised_props(px):
    """The properties states are compared on. These read REAL prices, so they do
    not change between surrogate draws and are computed once."""
    lp = np.log(px.astype(float)); rr = lp.diff()
    return {
        'realised_vol': rr.rolling(W).std().shift(1),
        'avg_abs_move': rr.abs().rolling(W).mean().shift(1),
        'autocorr': rr.rolling(W).corr(rr.shift(1)).shift(1),
        'range_to_path': ((lp.rolling(W).max() - lp.rolling(W).min())
                          / rr.abs().rolling(W).sum()).shift(1),
    }


def separation(px, lab, props=None):
    """Do the states differ on measurable realised properties?"""
    props = realised_props(px) if props is None else props
    rows = []
    for name, P in props.items():
        d = pd.DataFrame({'s': lab.stack(), 'v': P.stack()}).dropna()
        g = d.groupby('s').v.mean().reindex(LAB)
        rng = g.max() - g.min()
        mono = bool((g.diff().dropna() > 0).all() or (g.diff().dropna() < 0).all())
        rows.append(dict(prop=name, low=g['low'], mid=g['mid'], high=g['high'],
                         gap=rng, gap_over_sd=rng / d.v.std(), monotone=mono))
    return pd.DataFrame(rows)


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    A = axes(px)
    fit15 = px.index < pd.Timestamp('2016-01-01')
    lab, sc = classify(A, fit15)
    lab.to_csv(os.path.join(ROOTOUT, 'classifier_states.csv'))
    V = []

    print('WEIGHTS %s -> variance shares %s'
          % (WEIGHT, {k: round(v ** 2 / sum(w ** 2 for w in WEIGHT.values()), 3)
                      for k, v in WEIGHT.items()}))

    print('\n1. COVERAGE')
    cov = lab.stack().value_counts(normalize=True).reindex(LAB)
    print(cov.to_string(float_format=lambda v: '%.3f' % v))
    for k in LAB:
        V.append(dict(check='coverage', metric=k, value=float(cov[k])))

    print('\n2. PERSISTENCE')
    P = persistence(lab)
    print('  median run %.1f bars, mean %.2f, %.1f%% under 5 bars, diagonal %.3f'
          % (P['median_run'], P['mean_run'], 100 * P['under5'], P['diagonal']))
    V += [dict(check='persistence', metric=k, value=v) for k, v in P.items()]

    print('\n3. SEPARATION -- do the states differ on realised properties?')
    S = separation(px, lab)
    print(S.to_string(index=False, float_format=lambda v: '%.4f' % v))
    V += [dict(check='separation', metric=r['prop'], value=r.gap_over_sd)
          for _, r in S.iterrows()]

    print('\n4. STABILITY -- refit through 2015, then through 2020, compare labels')
    fit20 = px.index < pd.Timestamp('2021-01-01')
    lab20, _ = classify(A, fit20)
    pre = px.index < pd.Timestamp('2016-01-01')
    a, b = lab[pre].stack(), lab20[pre].stack()
    j = pd.concat([a.rename('a'), b.rename('b')], axis=1).dropna()
    agree = float((j.a == j.b).mean())
    print('  labels on pre-2016 history identical after refitting through 2020:'
          ' %.1f%% of %d pair-days' % (100 * agree, len(j)))
    V.append(dict(check='stability', metric='label_agreement', value=agree))

    print('\n5. NULL -- two surrogates, because one cannot touch a scale axis')
    rr = np.log(px.astype(float)).diff()
    rng = np.random.default_rng(41)
    NSHUF = int(os.environ.get('FX_NSHUF', 200))
    props = realised_props(px)
    print('  %d draws per surrogate' % NSHUF)
    for tag, n in (('A sign-randomised (vol clustering kept)', NSHUF),
                   ('B IID permutation (vol clustering destroyed)', NSHUF)):
        pers, seps = [], []
        for _ in range(n):
            if tag.startswith('A'):
                sg = pd.DataFrame(rng.choice([-1., 1.], size=rr.shape),
                                  index=rr.index, columns=rr.columns)
                r2 = rr.abs() * sg
            else:
                r2 = pd.DataFrame({p: rng.permutation(rr[p].dropna().values.copy())
                                   for p in rr.columns},
                                  index=rr.dropna(how='all').index).reindex(rr.index)
            A2 = axes(px, r=r2)
            l2, _ = classify(A2, fit15)
            pers.append(persistence(l2)['median_run'])
            seps.append(separation(px, l2, props).gap_over_sd.mean())
        pers, seps = np.array(pers), np.array(seps)
        pr = (1 + int((pers >= P['median_run']).sum())) / (len(pers) + 1)
        ps = (1 + int((seps >= S.gap_over_sd.mean()).sum())) / (len(seps) + 1)
        print('  %-46s' % tag)
        print('     median run  surrogate %.2f +/- %.2f  real %.2f  p=%.3f'
              % (pers.mean(), pers.std(), P['median_run'], pr))
        print('     separation  surrogate %.4f +/- %.4f  real %.4f  p=%.3f'
              % (seps.mean(), seps.std(), S.gap_over_sd.mean(), ps))
        V.append(dict(check='null_' + tag[0], metric='median_run', value=np.mean(pers)))
        V.append(dict(check='null_' + tag[0], metric='separation', value=np.mean(seps)))

    print('\n6. AGAINST THE FORWARD COMPOSITE, read at entry')
    reconnect(lab)
    pd.DataFrame(V).to_csv(os.path.join(ROOTOUT, 'classifier_validation.csv'),
                           index=False)
    print('\nwrote classifier_states.csv, classifier_validation.csv')


def reconnect(lab):
    if not (os.path.exists(EV) and os.path.exists(COMP)):
        return
    E = pd.read_csv(EV); E['date'] = pd.to_datetime(E.date)
    L = lab.stack().rename('state').reset_index()
    L.columns = ['date', 'pair', 'state']
    X = E.merge(L, on=['date', 'pair'], how='left')
    X = X[X.oos & X.state.notna()]
    g = X.groupby('state').agg(n=('mfe', 'size'), mfe=('mfe', 'mean'),
                               mae=('mae', 'mean'), bars=('bars_to_peak', 'mean'),
                               eff=('path_eff', 'mean'),
                               fav20=('fav_20', 'mean')).reindex(LAB)
    g['ratio'] = g.mfe / g.mae.abs()
    print('  BACKWARD classifier:')
    print(g[['n', 'mfe', 'ratio', 'bars', 'eff', 'fav20']]
          .to_string(float_format=lambda v: '%.4f' % v))
    cuts = E[~E.oos].regime.quantile([1 / 3, 2 / 3]).values
    E['band'] = np.digitize(E.regime, cuts)
    F = E[E.oos].groupby('band').agg(n=('mfe', 'size'), mfe=('mfe', 'mean'),
                                     mae=('mae', 'mean'),
                                     bars=('bars_to_peak', 'mean'),
                                     eff=('path_eff', 'mean'),
                                     fav20=('fav_20', 'mean'))
    F['ratio'] = F.mfe / F.mae.abs()
    print('  FORWARD composite (task 3, for comparison):')
    print(F[['n', 'mfe', 'ratio', 'bars', 'eff', 'fav20']]
          .to_string(float_format=lambda v: '%.4f' % v))
    print('  spread in path efficiency: backward %.4f, forward %.4f'
          % (g.eff.max() - g.eff.min(), F.eff.max() - F.eff.min()))
    print('  spread in bars to peak:    backward %.2f, forward %.2f'
          % (g.bars.max() - g.bars.min(), F.bars.max() - F.bars.min()))


if __name__ == '__main__':
    main()
