import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Three kinds of regime change, counted separately.

ACTIVITY IS NOT A SIDE QUESTION. The same shape at high activity is a trend; at
low activity it is a drift. So a move from 'weak broken' to 'strong broken' is a
regime change even though the shape word did not move, and lumping it in with
shape changes hides which of the two anything is actually tracking.

  shape change      trending/broken/range/drifting moves, activity does not
  activity change   weak/medium/strong moves, shape does not
  both              they move on the same bar

NO VOLUME, AND THAT IS FINE. FX is decentralised and H.10 is close-only, so
distance travelled -- path/(vol*sqrt(28)) -- is the activity proxy. It measures
how far price went, not how much changed hands, and nothing here claims otherwise.

A DECOMPOSITION PROBLEM THAT HAS TO BE STATED. The shipped `combined` applies the
dwell to the JOINT label, so a change in either half restarts one 5-bar clock and
the result cannot be split back into halves -- it agrees with a post-dwell join on
66.5% of bars (16.4f). So both objects are carried here:

  combined     the shipped column. Counted, not decomposed.
  split-join   confirm(shape) + confirm(activity), each dwelled on its own axis,
               which IS decomposable and is what the three-way split is computed
               on. Its total change count differs from `combined` and the gap is
               reported rather than hidden.

WHICH DO THE MEASUREMENTS TRACK. Every lead-time signal from 16.4g-i is rerun
against each change type separately, with the same per-cell surrogate correction,
because a signal that appears to track 'the state' may only be tracking the
volatility half of it -- which for a vol-ratio signal would be close to circular.

Writes results/change_counts.csv and results/change_tracking.csv.
"""
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
SPLIT = pd.Timestamp('2016-01-01')
NSHUF = int(os.environ.get('FX_NSHUF', 40))
LEAD = 1

from combined import layers, product, confirm, DWELL
from masweep import fire_of, warn_of, score_one
from structval import surrogate

SIGS = [('mas', 5, 8), ('mas', 5, 20), ('vol', 5, 60), ('vol', 8, 200),
        ('rng', 5, 60), ('rng', 72, 200)]


def parts(px, fit):
    """-> (shape confirmed, activity confirmed, shipped combined)."""
    sh, act = layers(px, fit)
    return confirm(sh, DWELL), confirm(act, DWELL), product(sh, act, DWELL)


def change_masks(shc, actc, comb, period='oos'):
    """-> dict change-type -> (bool mask, valid mask), numpy.

    period picks the block. It is a parameter and not a constant because
    failswing.py selects on IS and reads the holdout once; an earlier version
    hardcoded the holdout here and silently returned empty IS masks.
    """
    oos = np.asarray(shc.index >= SPLIT if period == 'oos'
                     else shc.index < SPLIT)[:, None]

    def prev(v):
        p = np.roll(v, 1, axis=0); p[0] = None
        return p
    s, a, c = shc.values, actc.values, comb.values
    ps, pa, pc = prev(s), prev(a), prev(c)
    ok = ((s != None) & (ps != None) & (a != None) & (pa != None) & oos)  # noqa
    okc = (c != None) & (pc != None) & oos                                # noqa
    ds, da = ok & (s != ps), ok & (a != pa)
    return {'shape only': (ds & ~da, ok),
            'activity only': (da & ~ds, ok),
            'both': (ds & da, ok),
            'split-join any': (ds | da, ok),
            'combined (shipped)': (okc & (c != pc), okc)}


def counts(shc, actc, comb):
    M = change_masks(shc, actc, comb)
    rows = []
    for k, (m, ok) in M.items():
        n = int(m.sum()); tot = int(ok.sum())
        rows.append(dict(kind=k, changes=n, bars=tot, rate=n / tot,
                         mean_gap=tot / n if n else np.nan))
    return pd.DataFrame(rows)


def tracking(px, fit, M):
    out = {}
    for fam, a, b in SIGS:
        w = warn_of(fire_of(score_one(px, fam, a, b), fit), LEAD)
        for k, (m, ok) in M.items():
            base = w[ok].mean()
            out[(fam, a, b, k)] = (w[m].mean() / base) if base and m.any() \
                else np.nan
            out[('N', 0, 0, k)] = int(m.sum())
    return out


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    fit = px.index < SPLIT
    shc, actc, comb = parts(px, fit)

    print('HOW OFTEN DOES EACH THING CHANGE? holdout, 28 pairs')
    C = counts(shc, actc, comb)
    C.to_csv(os.path.join(ROOTOUT, 'change_counts.csv'), index=False)
    print('  %-20s %9s %9s %10s' % ('kind', 'changes', 'rate', 'mean gap'))
    for _, r in C.iterrows():
        print('  %-20s %9d %8.3f%% %8.1f bars' % (r.kind, r.changes,
                                                  100 * r.rate, r.mean_gap))
    sh_n = int(C[C.kind == 'shape only'].changes.iloc[0])
    ac_n = int(C[C.kind == 'activity only'].changes.iloc[0])
    bo_n = int(C[C.kind == 'both'].changes.iloc[0])
    tot = sh_n + ac_n + bo_n
    print('\n  DECOMPOSITION of the %d split-join changes' % tot)
    print('    shape only     %6d  %5.1f%%' % (sh_n, 100 * sh_n / tot))
    print('    activity only  %6d  %5.1f%%' % (ac_n, 100 * ac_n / tot))
    print('    both same bar  %6d  %5.1f%%' % (bo_n, 100 * bo_n / tot))
    ship = int(C[C.kind == 'combined (shipped)'].changes.iloc[0])
    print('  the shipped `combined` column records %d changes, %+.1f%% against'
          % (ship, 100 * (ship - tot) / tot))
    print('  the split-join total -- the joint dwell merges changes that land')
    print('  within 5 bars of each other into one.')
    print('\n  if the two were independent, both-on-the-same-bar would be about')
    ok = change_masks(shc, actc, comb)['shape only'][1]
    ps, pa = sh_n + bo_n, ac_n + bo_n
    print('  %.0f of %d; observed %d, ratio %.2f'
          % (ps * pa / ok.sum(), tot, bo_n, bo_n / (ps * pa / ok.sum())))

    M = change_masks(shc, actc, comb)
    real = tracking(px, fit, M)
    print('\nWHICH CHANGES DO THE SIGNALS TRACK? lift over base, lead %d' % LEAD)
    print('%d surrogate draws, signals and states rebuilt on each' % NSHUF)
    rng = np.random.default_rng(6553)
    acc = {k: [] for k in real}
    for i in range(NSHUF):
        px2 = surrogate(px, 'sign', rng)
        s2, a2, c2 = parts(px2, fit)
        for k, v in tracking(px2, fit, change_masks(s2, a2, c2)).items():
            acc[k].append(v)
        if (i + 1) % 10 == 0:
            print('  %d/%d' % (i + 1, NSHUF), flush=True)

    rows = []
    KINDS = ['shape only', 'activity only', 'both', 'combined (shipped)']
    print('\n  %-14s %-18s %7s %7s %9s %9s %7s'
          % ('signal', 'change type', 'n', 'lift', 'surrogate', 'excess', 'p'))
    for (fam, a, b, k), v in real.items():
        if k not in KINDS or fam == 'N':
            continue
        nch = int(real[('N', 0, 0, k)])
        s = np.array(acc[(fam, a, b, k)], float); s = s[np.isfinite(s)]
        p = (1 + int((s >= v).sum())) / (len(s) + 1)
        print('  %-14s %-18s %7d %7.3f %9.3f %+9.3f %7.3f'
              % ('%s %d/%d' % (fam, a, b), k, nch, v, s.mean(), v - s.mean(), p))
        rows.append(dict(family=fam, fast=a, slow=b, kind=k, n=nch, lift=v,
                         surrogate=s.mean(), sd=s.std(), excess=v - s.mean(),
                         p=p))
    R = pd.DataFrame(rows)
    R.to_csv(os.path.join(ROOTOUT, 'change_tracking.csv'), index=False)

    print('\n  RAW LIFT BY CHANGE TYPE, averaged over the six signals')
    for k in KINDS:
        d = R[R.kind == k]
        print('    %-18s lift %.3f   excess %+.3f   %d of %d with p<0.05'
              % (k, d.lift.mean(), d.excess.mean(),
                 int((d.p < 0.05).sum()), len(d)))
    print('\n  the comparison that matters is ACROSS COLUMNS, not down them:')
    print('  a signal tracking activity but not shape would show it here.')
    print('\nwrote change_counts.csv and change_tracking.csv')


if __name__ == '__main__':
    main()
