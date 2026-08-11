import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""The classifier on three windows at once -- a state ribbon.

One construction, not a sweep: three windows read together, where the RELATIONSHIP
between them is the output.

  all three agree            established state
  fast diverges from m + s   transition starting
  fast + medium agree, slow  transition confirming
  anything else              unresolved

CHOOSING THE THREE LENGTHS. Each band is swept and the choice is made on two
measured quantities, not on preference:

  churn   label changes per 1000 bars -- how often the label moves when nothing has
  lag     bars from a genuine change in behaviour until the label follows

GROUND TRUTH FOR LAG IS DELIBERATELY NON-CAUSAL. A CENTRED window (half its span
either side of the bar) marks when behaviour actually changed, with no lag by
construction, and the causal label is then timed against it. That reads the future
and is a DIAGNOSTIC ONLY -- it never enters a state, a feature or a score. It is
the only honest way to measure a lag: you cannot time a reaction against a
reference that is itself late.

The selection rule is stated rather than tuned: within each band, normalise lag and
churn to [0,1] across the candidates and take the length minimising their sum. The
whole curve is reported so the trade-off is visible and the pick can be overruled.

Everything else is trailing and lagged one bar, weights as in classifier.py.

Writes results/ribbon_sweep.csv, ribbon_config.csv, ribbon_excursion.csv.
"""
import numpy as np, pandas as pd
from classifier import (WEIGHT, LAB, hyst, zfit, runs_of, realised_props,
                        separation, fit_frac)

PX = os.path.join(ROOTDATA, 'px28.csv')
EV = os.path.join(ROOTOUT, 'entry_events.csv')
SPLIT = pd.Timestamp('2016-01-01')
VOLWIN, BAND = 60, .25
REF = 21                       # centred reference span for the lag diagnostic
# The slow band starts at 62, not 60. At L == VOLWIN the scale axis collapses:
# sum|r|_L / (sd_L * sqrt(L)) tends to the constant sqrt(2/pi), so its cross-
# sectional sd bottoms out exactly there (0.343 at L=60 against 0.393 at 63 and
# 0.550 at 72). L=60 therefore shows artificially low churn and high lag, which
# would look like a good slow window and is a degenerate one.
BANDS = {'fast': range(7, 15), 'medium': range(20, 32), 'slow': range(62, 91, 3)}
CFG = ['established', 'transition starting', 'transition confirming', 'unresolved']


def axes_at(px, L, r=None):
    lp = np.log(px.astype(float)) if r is None else r.cumsum()
    rr = lp.diff() if r is None else r
    net = (lp - lp.shift(L)).abs()
    path = rr.abs().rolling(L).sum()
    vol = rr.rolling(VOLWIN).std()
    inf = [np.inf, -np.inf]
    straight = (net / path).replace(inf, np.nan)
    s5 = max(3, L // 4)
    e5 = ((lp - lp.shift(s5)).abs() / rr.abs().rolling(s5).sum()).replace(inf, np.nan)
    return {'straight': straight.shift(1),
            'scale': (path / (vol * np.sqrt(L))).replace(inf, np.nan).shift(1),
            'persist': (straight - e5).shift(1)}


def label_at(px, L, fit, r=None):
    Z = zfit(axes_at(px, L, r), fit)
    sc = sum(WEIGHT[k] * Z[k] for k in WEIGHT)
    frac = fit_frac(sc, fit)
    lo_b = hyst((frac - 1 / 3 + .5).clip(0, 1), BAND)
    hi_b = hyst((frac - 2 / 3 + .5).clip(0, 1), BAND)
    ok = frac.notna()
    return pd.DataFrame(np.where(ok, np.where(hi_b == 1, 'high',
                                              np.where(lo_b == 1, 'mid', 'low')), None),
                        index=frac.index, columns=frac.columns)


def truth(px):
    """Centred, non-causal reference. Diagnostic only -- never used as a feature."""
    lp = np.log(px.astype(float)); rr = lp.diff()
    h = REF // 2
    path = rr.abs().rolling(REF, center=True).sum()
    vol = rr.rolling(VOLWIN).std()
    sc = (path / (vol * np.sqrt(REF))).replace([np.inf, -np.inf], np.nan)
    # whole-sample ranking is fine HERE and only here: truth() is the non-causal
    # reference the lag is measured against, never a feature
    frac = pd.DataFrame({p: sc[p].rank(pct=True) for p in sc.columns})
    return pd.DataFrame(np.where(frac.notna(),
                                 np.where(frac > 2 / 3, 'high',
                                          np.where(frac > 1 / 3, 'mid', 'low')), None),
                        index=frac.index, columns=frac.columns)


def lag_and_churn(lab, T, maxlag=60):
    """Median bars from a truth change to the label matching, and churn."""
    lags, chg, tot = [], 0, 0
    for p in lab.columns:
        a = lab[p]; b = T[p]
        m = a.notna() & b.notna()
        a, b = a[m], b[m]
        if len(a) < 500:
            continue
        chg += int((a != a.shift()).sum()); tot += len(a)
        ev = np.flatnonzero((b != b.shift()).values)
        av, bv = a.values, b.values
        for i in ev[1:]:
            tgt = bv[i]
            j = np.flatnonzero(av[i:i + maxlag] == tgt)
            lags.append(j[0] if len(j) else maxlag)
    return (float(np.median(lags)) if lags else np.nan,
            1000.0 * chg / max(tot, 1))


def sweep(px, fit, T):
    rows = []
    for band, rng in BANDS.items():
        for L in rng:
            lab = label_at(px, L, fit)
            lg, ch = lag_and_churn(lab, T)
            rows.append(dict(band=band, L=L, lag=lg, churn=ch))
            print('  %-7s L=%2d  lag %5.1f  churn %6.1f/1000' % (band, L, lg, ch),
                  flush=True)
    S = pd.DataFrame(rows)
    pick = {}
    for band, g in S.groupby('band'):
        n = lambda x: (x - x.min()) / (x.max() - x.min()) if x.max() > x.min() else x * 0
        g = g.assign(cost=n(g.lag) + n(g.churn))
        pick[band] = int(g.loc[g.cost.idxmin(), 'L'])
        S.loc[g.index, 'cost'] = g.cost
    return S, pick


def configs(f, m, s):
    ok = f.notna() & m.notna() & s.notna()
    est = (f == m) & (m == s)
    start = (f != m) & (m == s)
    conf = (f == m) & (m != s)
    return pd.DataFrame(np.where(ok, np.where(est, CFG[0],
                                              np.where(start, CFG[1],
                                                       np.where(conf, CFG[2], CFG[3]))),
                                 None), index=f.index, columns=f.columns)


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    fit = px.index < SPLIT
    T = truth(px)
    print('WINDOW SWEEP (lag measured against a centred %d-bar reference)' % REF)
    S, pick = sweep(px, fit, T)
    S.to_csv(os.path.join(ROOTOUT, 'ribbon_sweep.csv'), index=False)
    print('\nchosen: %s' % pick)

    F = label_at(px, pick['fast'], fit)
    M = label_at(px, pick['medium'], fit)
    L3 = label_at(px, pick['slow'], fit)
    C = configs(F, M, L3)
    C.to_csv(os.path.join(ROOTOUT, 'ribbon_config.csv'))

    print('\nTIME IN EACH CONFIGURATION')
    for tag, msk in (('is', fit), ('oos', ~fit)):
        v = C[msk].stack().value_counts(normalize=True).reindex(CFG)
        print('  %-4s %s' % (tag, ' '.join('%s %.3f' % (k[:11], v[k]) for k in CFG)))

    print('\nSTABILITY OF THE CONFIGURATIONS')
    R = runs_of(C)
    print(R.groupby('state').agg(runs=('len', 'size'), median=('len', 'median'),
                                 mean=('len', 'mean'),
                                 under5=('len', lambda x: (x < 5).mean()))
          .reindex(CFG).to_string(float_format=lambda v: '%.2f' % v))

    excursion(C)

    print('\nNULL -- does a surrogate produce the same configuration mix?')
    rr = np.log(px.astype(float)).diff()
    rng = np.random.default_rng(77)
    NS = int(os.environ.get('FX_NRIB', 30))
    for tag in ('A sign-randomised', 'B IID permutation'):
        occ = []
        for _ in range(NS):
            if tag.startswith('A'):
                sg = pd.DataFrame(rng.choice([-1., 1.], size=rr.shape),
                                  index=rr.index, columns=rr.columns)
                r2 = rr.abs() * sg
            else:
                r2 = pd.DataFrame({p: rng.permutation(rr[p].dropna().values.copy())
                                   for p in rr.columns},
                                  index=rr.dropna(how='all').index).reindex(rr.index)
            c2 = configs(label_at(px, pick['fast'], fit, r2),
                         label_at(px, pick['medium'], fit, r2),
                         label_at(px, pick['slow'], fit, r2))
            occ.append(c2.stack().value_counts(normalize=True).reindex(CFG))
        O = pd.concat(occ, axis=1)
        real = C.stack().value_counts(normalize=True).reindex(CFG)
        print('  %-20s %s' % (tag, ' '.join(
            '%s %.3f(real %.3f)' % (k[:11], O.loc[k].mean(), real[k]) for k in CFG)))
    print('\nwrote ribbon_sweep.csv, ribbon_config.csv, ribbon_excursion.csv')


def excursion(C):
    if not os.path.exists(EV):
        return
    E = pd.read_csv(EV); E['date'] = pd.to_datetime(E.date)
    L = C.stack().rename('cfg').reset_index(); L.columns = ['date', 'pair', 'cfg']
    X = E.merge(L, on=['date', 'pair'], how='left')
    X = X[X.oos & X.cfg.notna()]
    g = X.groupby('cfg').agg(n=('mfe', 'size'), mfe=('mfe', 'mean'),
                             mae=('mae', 'mean'), bars=('bars_to_peak', 'mean'),
                             eff=('path_eff', 'mean'),
                             fav20=('fav_20', 'mean')).reindex(CFG)
    g['ratio'] = g.mfe / g.mae.abs()
    print('\nTASK 3 EXCURSION BY CONFIGURATION (out of sample)')
    print(g[['n', 'mfe', 'ratio', 'bars', 'eff', 'fav20']]
          .to_string(float_format=lambda v: '%.4f' % v))
    g.to_csv(os.path.join(ROOTOUT, 'ribbon_excursion.csv'))
    base = X[X.cfg == CFG[0]]
    for c in CFG[1:]:
        sub = X[X.cfg == c]
        if len(sub) < 100:
            continue
        print('  %-22s' % c, end='')
        for col in ('bars_to_peak', 'path_eff', 'mfe'):
            a, b = base[col].dropna(), sub[col].dropna()
            d = b.mean() - a.mean()
            se = np.sqrt(a.var() / len(a) + b.var() / len(b))
            print('  %s %+.4f (t %+.1f)' % (col.split('_')[0], d, d / se if se else 0),
                  end='')
        print()


if __name__ == '__main__':
    main()
