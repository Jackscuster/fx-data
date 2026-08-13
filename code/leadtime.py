import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Can a faster signal bridge the confirmation delay?

THIS FILE IS DELIBERATELY PREDICTIVE and it is the one place in the Layer 1 work
where that is the right frame. Everywhere else the question is what a state
DESCRIBES. Here it is whether something fires BEFORE the dwell confirms a change,
which is a lead-time question and cannot be asked in the present tense.

THE DELAY BEING BRIDGED. The 5-bar confirmation dwell adopts a new state only
once it has printed five consecutive bars, so a change visible in raw structure
at t is not in the shipped label until t+4. A fast signal that fires in that
window would let the state be marked provisional rather than simply late.

THREE CANDIDATES, all close-only, all lagged one bar like everything else:

  mas   moving-average slope divergence -- the 5-bar mean turning against the
        20-bar mean, scored by how hard the fast leg is moving in vol units.
        Needs no swing point to form, so it can move before structure resolves.
  vol   short over long realised volatility, 5 against 60
  rng   the 5-bar close range against its own 60-day average

THRESHOLDS ARE CALIBRATED, NOT PICKED. Each score is cut at the IS quantile that
makes it fire on TARGET of bars, so all three carry the same firing budget and
their lifts are comparable. Without that, a signal can buy hit rate simply by
firing more often, which is not a finding. A fire is an upward CROSSING of the
threshold, not the condition holding -- otherwise a persistent state inflates
the base rate and flattens every lift toward 1.

THE STANDARD THIS IS HELD TO. Cross-horizon confluence fired 79% before real
state changes and 79% before surrogate ones, and that is why it was dropped. So
hit rate against base rate is not enough on its own: the whole thing is rebuilt
on sign-randomised and IID surrogate panels, SIGNALS AND STATES BOTH, and what
counts is lift on real data minus lift on noise. A signal that leads a state
change only because both are reacting to the same volatility burst will show the
same lift on a surrogate and must fail here.

Writes results/leadtime.csv.
"""
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
SPLIT = pd.Timestamp('2016-01-01')
NSHUF = int(os.environ.get('FX_NSHUF', 60))
LEADS = (1, 2, 3, 5)
TARGET = 0.10            # IS-calibrated unconditional firing rate per signal
VOLW = 60

from combined import layers, product, confirm, DWELL
from ninestate import nine


def scores(px):
    """-> dict of continuous scores, each already lagged one bar."""
    lp = np.log(px.astype(float)); rr = lp.diff()
    vol = rr.rolling(VOLW).std()
    inf = [np.inf, -np.inf]

    sf = lp.rolling(5).mean().diff()
    ss = lp.rolling(20).mean().diff()
    against = (np.sign(sf) != np.sign(ss)) & sf.notna() & ss.notna()
    mas = (sf.abs() / vol).where(against, 0.0).replace(inf, np.nan)

    volr = (rr.rolling(5).std() / vol).replace(inf, np.nan)
    rng5 = lp.rolling(5).max() - lp.rolling(5).min()
    rngr = (rng5 / rng5.rolling(VOLW).mean()).replace(inf, np.nan)
    return {'mas': mas.shift(1), 'vol': volr.shift(1), 'rng': rngr.shift(1)}


def fires(sc, fit, target=TARGET):
    """Upward crossings of an IS-calibrated threshold.

    The threshold is one number for the whole panel, taken on IS only, so the
    holdout firing rate is free to differ from target -- which is itself worth
    seeing rather than forcing.
    """
    out = {}
    for k, v in sc.items():
        thr = np.nanquantile(v[fit].values.astype(float), 1 - target)
        on = v > thr
        out[k] = (on & ~on.shift(1).fillna(False)).where(v.notna(), False)
    return out


def lift(lab, fr, lead):
    """-> (hit rate before genuine changes, base rate, lift, n changes)."""
    oos = pd.Series(lab.index >= SPLIT, index=lab.index)
    ok = lab.notna() & lab.shift(1).notna()
    ok = ok.mul(oos, axis=0).astype(bool)
    chg = (lab != lab.shift(1)) & ok
    warn = fr.shift(1).rolling(lead, min_periods=1).max().fillna(0).astype(bool)
    w = warn.where(ok)
    a = w[chg].stack()
    b = w.stack()
    if len(a) < 100 or len(b) < 1000:
        return (np.nan,) * 3 + (len(a),)
    h, base = float(a.mean()), float(b.mean())
    return h, base, (h / base if base else np.nan), int(len(a))


def run(px, fit):
    sh, act = layers(px, fit)
    LAB = {'product M=%d' % DWELL: product(sh, act, DWELL),
           'structural M=%d' % DWELL: confirm(sh, DWELL),
           'nine-box': nine(px, fit)[0]}
    fr = fires(scores(px), fit)
    out = {}
    for ln, lab in LAB.items():
        for sn, f in fr.items():
            for L in LEADS:
                out[(ln, sn, L)] = lift(lab, f, L)
    return out


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    fit = px.index < SPLIT
    real = run(px, fit)

    print('LEAD-TIME TEST. Does a fast signal fire before a confirmed state')
    print('change more often than it fires before an arbitrary bar?')
    print('holdout, thresholds calibrated on IS to fire on %.0f%% of bars,'
          % (100 * TARGET))
    print('%d surrogate draws of each kind, signals AND states rebuilt on each.'
          % NSHUF)

    from structval import surrogate
    rng = np.random.default_rng(19937)
    acc = {'sign': {k: [] for k in real}, 'iid': {k: [] for k in real}}
    for kind in ('sign', 'iid'):
        for _ in range(NSHUF):
            r = run(surrogate(px, kind, rng), fit)
            for k, v in r.items():
                acc[kind][k].append(v[2])

    rows = []
    print('\n  %-18s %-4s %-4s %7s %7s %6s %8s %8s %8s'
          % ('state', 'sig', 'lead', 'hit', 'base', 'lift', 'sign L', 'iid L',
             'excess'))
    for k, (h, b, lf, n) in real.items():
        s = np.array(acc['sign'][k], float); s = s[np.isfinite(s)]
        i = np.array(acc['iid'][k], float); i = i[np.isfinite(i)]
        ex = lf - max(s.mean(), i.mean())
        p = (1 + int((s >= lf).sum())) / (len(s) + 1)
        print('  %-18s %-4s %-4d %6.1f%% %6.1f%% %6.3f %8.3f %8.3f %+8.3f'
              % (k[0], k[1], k[2], 100 * h, 100 * b, lf, s.mean(), i.mean(), ex))
        rows.append(dict(state=k[0], signal=k[1], lead=k[2], hit=h, base=b,
                         lift=lf, n_changes=n, sign_lift=s.mean(),
                         sign_sd=s.std(), iid_lift=i.mean(), iid_sd=i.std(),
                         excess=ex, p_sign=p))
    R = pd.DataFrame(rows)
    R.to_csv(os.path.join(ROOTOUT, 'leadtime.csv'), index=False)

    print('\n  hit    share of genuine state changes with a fire in the previous'
          ' <lead> bars')
    print('  base   the same quantity over ALL bars -- the firing budget')
    print('  lift   hit / base. 1.000 is chance.')
    print('  sign L, iid L   the same lift with price replaced by a surrogate')
    print('  excess lift minus the larger surrogate lift. THIS is the number.')

    best = R.sort_values('excess', ascending=False).head(5)
    print('\nBEST FIVE BY EXCESS')
    print(best[['state', 'signal', 'lead', 'lift', 'sign_lift', 'iid_lift',
                'excess', 'p_sign']]
          .to_string(index=False, float_format=lambda v: '%.3f' % v))
    win = R[(R.excess > 0.05) & (R.p_sign < 0.05)]
    print('\n  configurations beating BOTH surrogates by more than 0.05 lift'
          ' at p<0.05: %d of %d' % (len(win), len(R)))
    if len(win):
        print(win[['state', 'signal', 'lead', 'lift', 'excess', 'p_sign']]
              .to_string(index=False, float_format=lambda v: '%.3f' % v))
    else:
        print('  none. The settling flag stays a graded confidence and the lag')
        print('  is accepted -- which is what was specified for this outcome.')

    print('\nGRADED SETTLING CONFIDENCE, the fallback')
    lab = product(*layers(px, fit), DWELL)
    v = lab[lab.index >= SPLIT]
    age = pd.DataFrame({p: (lambda c: c.groupby(
        (c != c.shift()).cumsum()).cumcount() + 1)(v[p].replace('', np.nan))
        for p in v.columns})
    a = age.stack().dropna()
    print('  age 1..%d is settling; the grade is min(age/%d, 1), so a state is'
          % (DWELL, DWELL))
    print('  fully weighted only once it has held as long as it took to confirm.')
    for k in range(1, DWELL + 1):
        print('    age %d  %6.2f%% of holdout bars  confidence %.2f'
              % (k, 100 * (a == k).mean(), min(k / DWELL, 1.0)))
    print('    age >%d %6.2f%% of holdout bars  confidence 1.00'
          % (DWELL, 100 * (a > DWELL).mean()))
    print('\nwrote leadtime.csv')


if __name__ == '__main__':
    main()
