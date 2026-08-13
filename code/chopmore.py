import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Chop redundancy, measured rather than assumed. And what the 'both' cell is.

PART ONE -- IS CHOP CONCENTRATED?

The chop score already carries five components: boundary tests, time inside the
band, mean-reversion crossings, failed breaks, and pullback hold. All four things
named as missing are in it. So the real question is not whether they exist but
whether the score LEANS on one of them, and that is a drop-one test: rebuild the
score without each component in turn and see how far it moves. A score that
barely notices a removal is not concentrated on it.

THREE NEW COMPONENTS ARE ADDED ANYWAY, because five correlated readings of the
same thing is not redundancy either:

  vr_short   variance ratio at lag 5. Below 1 is mean-reverting, above 1 is
             trending. The most direct measure of reversion strength there is,
             and unlike the others it is a ratio of variances rather than a
             count of events.
  hold_ratio boundary touches that did NOT break through, over all touches. The
             counts already there measure how OFTEN the edge is visited;
             this measures how often it WINS.
  width_stab stability of the band width itself. A real range has boundaries
             that stay put; a widening band is a range failing.

PART TWO -- WHAT IS THE 'BOTH' CELL?

High trend and high chop together. Either a genuine trend inside a wider range,
or two measurements overlapping on the same bars. Longest episodes are pulled and
described directly: net move in vol units, path efficiency, boundary touches,
whether the band widened over the episode, and what state sat either side.

The before/after states are DIAGNOSTIC, not scoring -- reading what a cell turns
into is forward-looking and could not be used to build anything. It is here to
characterise, and is labelled as such.

Writes results/chop_components.csv and results/both_episodes.csv.
"""
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
SPLIT = pd.Timestamp('2016-01-01')
NSHUF = int(os.environ.get('FX_NSHUF', 12))
W = 106

from structure import swings, VOLWIN
from structval import properties, surrogate
from shape3 import N_SCORE
from twoscores import (raw_parts, classify, CELLS, sep_one_vs_rest, PROPS,
                       stats, two_scores)
from combined import confirm, DWELL
from classifier import zfit


def new_chop(px, N=N_SCORE):
    """Three additional chop readings. Causal, lagged one bar."""
    lp = np.log(px.astype(float))
    rr = lp.diff()
    inf = [np.inf, -np.inf]
    out = {}

    v1 = rr.rolling(W).var()
    v5 = (lp - lp.shift(5)).rolling(W).var()
    out['vr_short'] = (v5 / (5 * v1)).replace(inf, np.nan)

    hold_r, width_s = {}, {}
    for p in px.columns:
        c = lp[p].values
        hi, hip, lo, lop = swings(c, N)
        with np.errstate(invalid='ignore', divide='ignore'):
            width = hi - lo
            near = ((hi - c) <= 0.15 * width) | ((c - lo) <= 0.15 * width)
            broke = (c > hi) | (c < lo)
            touch = pd.Series(near | broke).rolling(W).sum().values
            held = pd.Series(near & ~broke).rolling(W).sum().values
            hold_r[p] = np.where(touch > 0, held / touch, np.nan)
            wser = pd.Series(width)
            width_s[p] = (wser.rolling(W).std()
                          / wser.rolling(W).mean()).values
    mk = lambda d: pd.DataFrame(d, index=px.index,
                                columns=px.columns).replace(inf, np.nan)
    out['hold_ratio'] = mk(hold_r)
    out['width_stab'] = -mk(width_s)      # stable width = more range-like
    return {k: v.shift(1) for k, v in out.items()}


def chop_score(px, fit, drop=None, extra=True):
    T, C = raw_parts(px)
    C = dict(C)
    if extra:
        C.update(new_chop(px))
    if drop:
        C.pop(drop, None)
    z = zfit(C, fit)
    return sum(z[k] for k in C), list(C)


def marg_sep(sc, P, fit, mask):
    m = np.nanmedian(np.where(fit[:, None], sc.values, np.nan))
    L = confirm(pd.DataFrame(np.where(sc > m, 'high', 'low'), index=sc.index,
                             columns=sc.columns).where(sc.notna()), DWELL)
    S = sep_one_vs_rest(L, P, mask, ['high', 'low'])
    return float(np.nanmean([abs(S[('high', c)]) for c in PROPS])), L


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    fit = np.asarray(px.index < SPLIT)
    oos = ~fit
    P = properties(px)

    print('PART ONE -- IS THE CHOP SCORE CONCENTRATED?')
    base5, keys5 = chop_score(px, fit, extra=False)
    g5, _ = marg_sep(base5, P, fit, oos)
    print('  the five existing components: %s' % ', '.join(keys5))
    print('  they are all present -- boundary tests, time inside, reversion')
    print('  crossings, failed breaks, pullback hold. chop |sep| = %.3f' % g5)

    print('\n  DROP-ONE on the existing five (holdout |sep|)')
    for k in keys5:
        sc, _ = chop_score(px, fit, drop=k, extra=False)
        g, _ = marg_sep(sc, P, fit, oos)
        print('    without %-11s %.3f  (%+.3f)' % (k, g, g - g5))

    print('\n  correlation of each component with the chop score')
    T, C0 = raw_parts(px)
    z = zfit(C0, fit)
    for k in keys5:
        d = pd.DataFrame({'a': z[k].stack(), 'b': base5.stack()}).dropna()
        print('    %-11s r = %+.3f' % (k, np.corrcoef(d.a, d.b)[0, 1]))

    print('\n  THREE NEW COMPONENTS')
    NC = new_chop(px)
    full, keysF = chop_score(px, fit)
    gF, labF = marg_sep(full, P, fit, oos)
    print('  chop |sep| with all %d components: %.3f  (%+.3f vs five)'
          % (len(keysF), gF, gF - g5))
    for k, v in NC.items():
        g_alone, _ = marg_sep(v, P, fit, oos)
        sc, _ = chop_score(px, fit, drop=k)
        g_wo, _ = marg_sep(sc, P, fit, oos)
        d = pd.DataFrame({'a': v.stack(), 'b': base5.stack()}).dropna()
        print('    %-11s alone %.3f | dropping it %.3f (%+.3f) | r with old'
              ' chop %+.3f' % (k, g_alone, g_wo, g_wo - gF,
                               np.corrcoef(d.a, d.b)[0, 1]))

    print('\n  NULLS on the new components, %d draws' % NSHUF)
    rng = np.random.default_rng(5150)
    acc = {k: [] for k in list(NC) + ['chop_full']}
    for i in range(NSHUF):
        px2 = surrogate(px, 'sign', rng)
        P2 = properties(px2)
        N2 = new_chop(px2)
        for k in NC:
            acc[k].append(marg_sep(N2[k], P2, fit, oos)[0])
        f2, _ = chop_score(px2, fit)
        acc['chop_full'].append(marg_sep(f2, P2, fit, oos)[0])
    rows = []
    for k in NC:
        g_alone, _ = marg_sep(NC[k], P, fit, oos)
        sv = np.nanmean(acc[k])
        print('    %-11s real %.3f  surrogate %.3f  corrected %+.3f'
              % (k, g_alone, sv, g_alone - sv))
        rows.append(dict(component=k, real=g_alone, surrogate=sv,
                         corrected=g_alone - sv))
    sv = np.nanmean(acc['chop_full'])
    print('    %-11s real %.3f  surrogate %.3f  corrected %+.3f'
          % ('chop (all)', gF, sv, gF - sv))
    rows.append(dict(component='chop_full', real=gF, surrogate=sv,
                     corrected=gF - sv))
    pd.DataFrame(rows).to_csv(os.path.join(ROOTOUT, 'chop_components.csv'),
                              index=False)

    # ---------------- part two ----------------
    print('\n' + '=' * 72)
    print("PART TWO -- WHAT IS THE 'BOTH' CELL?")
    tr, ch = two_scores(px, fit)
    lab, _ = classify(tr, ch, fit)
    o = lab[oos]
    cv = o.stack().value_counts(normalize=True)
    print('  measured share of trend-in-range on the holdout: %.1f%%'
          % (100 * cv.get('trend-in-range', 0)))
    lp = np.log(px.astype(float))
    rr = lp.diff()
    sig = rr.rolling(VOLWIN).std()
    eps = []
    for p in o.columns:
        v = o[p].dropna()
        if len(v) < 50:
            continue
        gid = (v != v.shift()).cumsum()
        for _, g in v.groupby(gid):
            if g.iloc[0] != 'trend-in-range' or len(g) < 20:
                continue
            a, b = g.index[0], g.index[-1]
            seg = lp[p].loc[a:b]
            s = sig[p].loc[a:b].mean()
            net = abs(seg.iloc[-1] - seg.iloc[0])
            path = rr[p].loc[a:b].abs().sum()
            dev = seg - seg.mean()
            cross = int((np.sign(dev) != np.sign(dev.shift(1))).sum())
            i0 = v.index.get_loc(a)
            prev = v.iloc[i0 - 1] if i0 > 0 else None
            j = v.index.get_loc(b)
            nxt = v.iloc[j + 1] if j + 1 < len(v) else None
            eps.append(dict(pair=p, start=str(a.date()), end=str(b.date()),
                            bars=len(g), net_vol=net / (s * np.sqrt(len(g))),
                            eff=net / path if path else np.nan,
                            crossings=cross, prev=prev, nxt=nxt))
    E = pd.DataFrame(eps).sort_values('bars', ascending=False)
    E.to_csv(os.path.join(ROOTOUT, 'both_episodes.csv'), index=False)
    print('  %d episodes of 20+ bars on the holdout' % len(E))
    print('\n  THE TEN LONGEST')
    print(E.head(10)[['pair', 'start', 'end', 'bars', 'net_vol', 'eff',
                      'crossings', 'prev', 'nxt']]
          .to_string(index=False, float_format=lambda v: '%.2f' % v))
    print('\n  WHAT THEY LOOK LIKE, against the other cells')
    for c in CELLS:
        sub = []
        for p in o.columns:
            v = o[p].dropna()
            if len(v) < 50:
                continue
            gid = (v != v.shift()).cumsum()
            for _, g in v.groupby(gid):
                if g.iloc[0] != c or len(g) < 20:
                    continue
                a, b = g.index[0], g.index[-1]
                seg = lp[p].loc[a:b]
                s = sig[p].loc[a:b].mean()
                net = abs(seg.iloc[-1] - seg.iloc[0])
                path = rr[p].loc[a:b].abs().sum()
                sub.append((net / (s * np.sqrt(len(g))),
                            net / path if path else np.nan, len(g)))
        if sub:
            A = np.array(sub, float)
            print('    %-16s n=%4d  net move %.2f sd  efficiency %.3f  '
                  'median %d bars'
                  % (c, len(A), np.nanmedian(A[:, 0]), np.nanmedian(A[:, 1]),
                     int(np.median(A[:, 2]))))
    print('\n  a genuine trend-inside-a-range should show a LARGE net move and')
    print('  a HIGH efficiency, like trending, while still being called chop.')
    print('  measurement overlap would show it sitting between the two.')
    print('\nwrote chop_components.csv and both_episodes.csv')


if __name__ == '__main__':
    main()
