import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""The four measurements from TWO_SCORES.md, built and tested twice each.

  1 failed swings     is a level being defended        -> chop
  2 retracement depth is a trend tiring                -> trend
  3 swing spacing     is momentum fading               -> trend
  4 cross-pair        idiosyncratic or panel-wide      -> both

TWO TESTS, REPORTED SEPARATELY, and a pass on the first counts even if the second
fails.

  TEST ONE -- does it describe the present state. Present tense, no forward
  measurement. Does the measurement differ across the current states, does it
  still differ once the existing trend and chop scores are regressed out (the
  INCREMENTAL test -- a measurement that only restates the scores adds nothing),
  does it hold per pair, does it survive a surrogate.

  TEST TWO -- does it lead a change. Hit rate before a genuine state change
  against base firing rate, corrected by the same measurement on a surrogate.

THE CROSS-PAIR TRAP IS WORSE THAN "EXCLUDE THE PAIR", and the first version of
this file walked straight into it. The 28 pairs are triangulated from 8
currencies, so the panel has rank 7: ANY pair is an exact linear combination of
the others. Building a leg index that merely omits the pair under test still
reconstructs it exactly -- EURGBP minus USDGBP is EURUSD, identically. The
measured lag-0 correlation came back +1.000, which is the proof.

So a contemporaneous cross-pair reading is mathematically vacuous on this panel
and no exclusion rule fixes it. Two things are reported instead:

  the identity itself, at lag 0, as the record of why this cannot be done the
  obvious way; and

  a DISJOINT proxy -- the mean move of the 15 pairs sharing NEITHER currency with
  the pair under test. That carries no algebraic identity with it, so a
  correlation there is a real panel-wide effect rather than a restatement.

Everything is lagged one bar and built from bars at or before t. Window is the
locked 106-bar lookback (swing width N=19).

Writes results/measures_test1.csv, results/measures_test2.csv,
results/measures_failsurface.csv.
"""
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
SPLIT = pd.Timestamp('2016-01-01')
NSHUF = int(os.environ.get('FX_NSHUF', 15))
W = 106
# 0.85 was the spec's floor and the separation surface was still climbing at it,
# so the sweep is extended downward -- a best cell sitting on the grid edge means
# the grid was too narrow, which is the same standard applied in 16.4l.
XS = (0.70, 0.75, 0.80, 0.85, 0.90, 0.93, 0.95, 0.97, 0.98, 0.99)
YS = (0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0)
KSEQ = 4                 # how many recent swings feed a slope
LAGS = range(-5, 6)

from structure import swings, VOLWIN
from structval import properties, surrogate
from shape3 import N_SCORE
from twoscores import two_scores, classify, CELLS, sep_one_vs_rest, PROPS, stats
from combined import confirm, DWELL
from masweep import warn_of
from classifier import zfit
from ninestate import raw_axes, tercile

G8 = ['EUR', 'GBP', 'AUD', 'NZD', 'USD', 'CAD', 'CHF', 'JPY']


def swing_seq(c, N):
    """-> (positions, levels) of confirmed swings, and the bar each is known."""
    n = len(c); s = pd.Series(c)
    out = []
    for mask in ((s == s.rolling(2 * N + 1, center=True).max()).values,
                 (s == s.rolling(2 * N + 1, center=True).min()).values):
        pos = np.flatnonzero(mask); conf = pos + N
        k = conf < n
        out.append((pos[k], conf[k]))
    return out


def retr_and_space(px, N=N_SCORE):
    """Retracement-depth and swing-spacing readings. Causal, lagged."""
    lp = np.log(px.astype(float))
    n = len(lp)
    R = {'retr_last': {}, 'retr_slope': {}, 'retr_rel': {},
         'space_last': {}, 'space_slope': {}, 'space_rel': {}}
    for p in px.columns:
        c = lp[p].values
        (hp, hc), (lpz, lc) = swing_seq(c, N)
        allp = np.sort(np.concatenate([hp, lpz]))
        allc = allp + N
        depth = np.full(len(allp), np.nan)
        for i in range(2, len(allp)):
            a, b, d = c[allp[i - 2]], c[allp[i - 1]], c[allp[i]]
            imp = abs(b - a)
            if imp > 0:
                depth[i] = abs(d - b) / imp
        gaps = np.r_[np.nan, np.diff(allp)].astype(float)
        idx = np.searchsorted(allc, np.arange(n), 'right') - 1

        def series(vals, slope=False, rel=False):
            """Computed once PER SWING, then mapped to bars.

            The obvious version loops over all 7,000 bars per pair and refits a
            slope at each -- 196k polyfits per panel, which is unusable inside a
            surrogate loop. There are only ~180 swings, and the reading only
            changes when a new one confirms, so it is computed there and read
            off by index.
            """
            ns = len(vals)
            per = np.full(ns, np.nan)
            run_sum, run_n = 0.0, 0
            for i in range(ns):
                v = vals[max(0, i - KSEQ + 1):i + 1]
                v = v[np.isfinite(v)]
                if np.isfinite(vals[i]):
                    run_sum += vals[i]; run_n += 1
                if not len(v):
                    continue
                if slope:
                    if len(v) > 2:
                        xx = np.arange(len(v), dtype=float)
                        per[i] = (((xx - xx.mean()) * (v - v.mean())).sum()
                                  / ((xx - xx.mean()) ** 2).sum())
                elif rel:
                    if run_n > 2 and run_sum:
                        per[i] = v[-1] / (run_sum / run_n)
                else:
                    per[i] = v[-1]
            o = np.where(idx >= 0, per[np.clip(idx, 0, None)], np.nan)
            return o
        R['retr_last'][p] = series(depth)
        R['retr_slope'][p] = series(depth, slope=True)
        R['retr_rel'][p] = series(depth, rel=True)
        R['space_last'][p] = series(gaps)
        R['space_slope'][p] = series(gaps, slope=True)
        # current bars since the last confirmed swing, against the running mean
        cur = np.arange(n) - np.where(idx >= 0, allp[np.clip(idx, 0, None)], np.nan)
        mg = series(gaps, rel=False)
        with np.errstate(invalid='ignore', divide='ignore'):
            R['space_rel'][p] = cur / np.where(mg > 0, mg, np.nan)
    inf = [np.inf, -np.inf]
    return {k: pd.DataFrame(v, index=px.index).replace(inf, np.nan).shift(1)
            for k, v in R.items()}


def failed_count(px, X, Y, N=N_SCORE):
    """Rolling count of within-window failed swings. The measurement form."""
    from failswing import failed
    return failed(px, X, Y).rolling(W).sum().replace([np.inf, -np.inf], np.nan)


def leg_returns(px):
    """-> per-currency return index, and a version excluding one pair."""
    rr = np.log(px.astype(float)).diff()
    contrib = {g: [] for g in G8}
    for p in px.columns:
        b, q = p[:3], p[3:]
        contrib[b].append((p, +1.0))
        contrib[q].append((p, -1.0))
    return contrib, rr


def cross_pair(px):
    """-> (panel R2 on a DISJOINT proxy, disjoint proxies, leg-identity proxies).

    The leg version is kept only to document the identity; the disjoint version
    is the one that carries information.
    """
    contrib, rr = leg_returns(px)
    idx, col = px.index, px.columns
    panel, disj, legp = {}, {}, {}
    for p in col:
        b, q = p[:3], p[3:]
        legb = pd.concat([rr[x] * sgn for x, sgn in contrib[b] if x != p],
                         axis=1).mean(axis=1)
        legq = pd.concat([rr[x] * sgn for x, sgn in contrib[q] if x != p],
                         axis=1).mean(axis=1)
        legp[p] = legb - legq          # exactly equals rr[p]; see the docstring
        other = [x for x in col if b not in x and q not in x]
        d = rr[other].abs().mean(axis=1)          # panel-wide ACTIVITY, no identity
        disj[p] = d
        a = rr[p].abs()
        cov = a.rolling(W).cov(d)
        va, vc = a.rolling(W).var(), d.rolling(W).var()
        with np.errstate(invalid='ignore', divide='ignore'):
            panel[p] = (cov ** 2 / (va * vc)).replace([np.inf, -np.inf], np.nan)
    return (pd.DataFrame(panel, index=idx).shift(1),
            pd.DataFrame(disj, index=idx), pd.DataFrame(legp, index=idx))


def leadlag(px, proxies):
    """Cross-correlation at lags, on the leg proxy that EXCLUDES the pair."""
    rr = np.log(px.astype(float)).diff()
    out = []
    for p in px.columns:
        a, c = rr[p], proxies[p]
        m = a.notna() & c.notna()
        for L in LAGS:
            v = c.shift(L)[m]
            aa = a[m]
            k = v.notna() & aa.notna()
            if k.sum() < 500:
                continue
            out.append(dict(pair=p, lag=L, r=float(np.corrcoef(aa[k], v[k])[0, 1])))
    return pd.DataFrame(out)


def build_measures(px):
    M = {}
    RS = retr_and_space(px)
    for k, v in RS.items():
        v.columns = px.columns
        M[k] = v
    M['fail_count'] = failed_count(px, 0.95, 1.0)
    pan, disj, legp = cross_pair(px)
    M['panel_r2'] = pan
    return M, (disj, legp)


def sep_of_measure(m, lab, mask):
    """How far apart the states are ON THIS MEASUREMENT, in sd units."""
    d = pd.DataFrame({'s': lab[mask].stack(), 'v': m[mask].stack()}).dropna()
    if d.s.nunique() < 2 or len(d) < 1000:
        return np.nan
    g = d.groupby('s').v.mean()
    return float((g.max() - g.min()) / d.v.std())


def incremental(m, lab, tr, ch, mask):
    """Same, after regressing the existing trend and chop scores out."""
    d = pd.DataFrame({'s': lab[mask].stack(), 'v': m[mask].stack(),
                      't': tr[mask].stack(), 'c': ch[mask].stack()}).dropna()
    if len(d) < 1000:
        return np.nan
    A = np.c_[np.ones(len(d)), d.t.values, d.c.values]
    beta, *_ = np.linalg.lstsq(A, d.v.values, rcond=None)
    d['r'] = d.v.values - A @ beta
    g = d.groupby('s').r.mean()
    return float((g.max() - g.min()) / d.r.std())


def lead_lift(m, lab, mask, lead=1, q=0.90):
    """Test two: does a high reading fire before a genuine state change."""
    thr = np.nanquantile(np.where(mask[:, None], m.values, np.nan), q)
    on = (m > thr).values
    prev = np.roll(on, 1, axis=0); prev[0] = False
    fire = on & ~prev
    w = warn_of(fire, lead)
    v = lab.values
    pv = np.roll(v, 1, axis=0); pv[0] = None
    ok = (v != None) & (pv != None) & mask[:, None]          # noqa: E711
    chg = ok & (v != pv)
    if not chg.any() or not ok.any():
        return np.nan
    base = w[ok].mean()
    return (w[chg].mean() / base) if base else np.nan


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    fit = np.asarray(px.index < SPLIT)
    oos = ~fit
    P = properties(px)
    tr0, ch0 = two_scores(px, fit)
    lab0, _ = classify(tr0, ch0, fit)
    M, (disj, legp) = build_measures(px)
    print('FOUR MEASUREMENTS at the locked window (N=%d, ~%d bars)'
          % (N_SCORE, W))
    print('coverage of each, holdout:')
    for k, v in M.items():
        print('  %-12s %.3f of bars' % (k, v[oos].notna().mean().mean()))

    # ---------------- failed-swing surface ----------------
    print('\n1. FAILED SWINGS -- the full X x Y surface, IS separation')
    print('   (rolling count of within-window rejections, not an event flag)')
    rows = []
    print('  %5s | %s' % ('X', ' '.join('%7s' % ('Y=' + str(y)) for y in YS)))
    for X in XS:
        line = []
        for Y in YS:
            fc = failed_count(px, X, Y)
            g = sep_of_measure(fc, lab0, fit)
            line.append(g); rows.append(dict(X=X, Y=Y, is_sep=g))
        print('  %5.2f | %s' % (X, ' '.join('%7.3f' % v for v in line)))
    FS = pd.DataFrame(rows)
    FS.to_csv(os.path.join(ROOTOUT, 'measures_failsurface.csv'), index=False)
    n05 = int((FS.is_sep > 0.5).sum())
    print('  cells above 0.5: %d of %d. best %.3f at X=%.2f Y=%.2f'
          % (n05, len(FS), FS.is_sep.max(),
             FS.loc[FS.is_sep.idxmax(), 'X'], FS.loc[FS.is_sep.idxmax(), 'Y']))

    # ---------------- cross-pair lead-lag ----------------
    print('\n4. CROSS-PAIR. First the trap, measured rather than assumed.')
    L0 = leadlag(px, legp).groupby('lag').r.mean()
    print('  leg proxy built from every OTHER pair, lag 0 correlation: %+.4f'
          % L0[0])
    print('  that is an identity, not a finding: 28 pairs from 8 currencies is a')
    print('  rank-7 panel, so EURGBP minus USDGBP IS EURUSD. No exclusion rule')
    print('  fixes it, and a contemporaneous cross-pair reading is vacuous here.')
    print('  the same proxy at non-zero lags: %s'
          % '  '.join('%+d:%+.3f' % (l, L0[l]) for l in LAGS if l != 0))
    print('\n  DISJOINT proxy -- the 15 pairs sharing NEITHER currency:')
    LL = leadlag(px, disj)
    g = LL.groupby('lag').r.mean()
    print('    ' + '  '.join('%+d:%+.3f' % (l, g[l]) for l in LAGS))
    peak = int(g.abs().idxmax())
    print('  peak |r| at lag %+d (%+.3f), lag 0 is %+.3f'
          % (peak, g[peak], g[0]))
    print('  negative lag = the rest of the panel leads this pair.')

    # ---------------- test one and test two ----------------
    print('\nTEST ONE (describes the present) and TEST TWO (leads a change)')
    print('  %-12s %8s %10s %9s %8s | %8s'
          % ('measurement', 'sep IS', 'sep OOS', 'increm.', 'surr', 'lead lift'))
    t1, rng = [], np.random.default_rng(777)
    surr_acc = {k: [] for k in M}
    lead_acc = {k: [] for k in M}
    for i in range(NSHUF):
        px2 = surrogate(px, 'sign', rng)
        t2, c2 = two_scores(px2, fit)
        l2, _ = classify(t2, c2, fit)
        M2, _ = build_measures(px2)
        for k in M:
            surr_acc[k].append(sep_of_measure(M2[k], l2, oos))
            lead_acc[k].append(lead_lift(M2[k], l2, oos))
        if (i + 1) % 5 == 0:
            print('  ... %d/%d surrogates' % (i + 1, NSHUF), flush=True)
    for k, v in M.items():
        a = sep_of_measure(v, lab0, fit)
        b = sep_of_measure(v, lab0, oos)
        inc = incremental(v, lab0, tr0, ch0, oos)
        sv = np.nanmean(surr_acc[k])
        ll = lead_lift(v, lab0, oos)
        lv = np.nanmean(lead_acc[k])
        print('  %-12s %8.3f %10.3f %9.3f %8.3f | %6.3f (surr %.3f, %+.3f)'
              % (k, a, b, inc, sv, ll, lv, ll - lv))
        t1.append(dict(measure=k, is_sep=a, oos_sep=b, incremental=inc,
                       surrogate=sv, corrected=b - sv, lead_lift=ll,
                       lead_surr=lv, lead_excess=ll - lv))
    T1 = pd.DataFrame(t1)
    T1.to_csv(os.path.join(ROOTOUT, 'measures_test1.csv'), index=False)

    # ---------------- rebuild the scores ----------------
    print('\nREBUILT SCORES using the measurements')
    from twoscores import raw_parts
    T, C = raw_parts(px)
    T2 = dict(T); C2 = dict(C)
    T2['retr_slope'] = -M['retr_slope']      # deepening pullbacks = tiring
    T2['space_slope'] = -M['space_slope']    # widening gaps = fading
    C2['fail_count'] = M['fail_count']
    for k in ('panel_r2',):
        T2[k] = M[k]; C2[k] = -M[k]
    zt, zc = zfit(T2, fit), zfit(C2, fit)
    trN = sum(zt[k] for k in T2); chN = sum(zc[k] for k in C2)
    labN, _ = classify(trN, chN, fit)
    d = pd.DataFrame({'a': trN.stack(), 'b': chN.stack()}).dropna()
    rN = float(np.corrcoef(d.a, d.b)[0, 1])
    d0 = pd.DataFrame({'a': tr0.stack(), 'b': ch0.stack()}).dropna()
    r0 = float(np.corrcoef(d0.a, d0.b)[0, 1])
    print('  score correlation  before %+.3f  after %+.3f' % (r0, rN))
    for nm, L in (('before', lab0), ('after', labN)):
        cv = L[oos].stack().value_counts(normalize=True)
        S = sep_one_vs_rest(L, P, oos, CELLS)
        st = stats(L, oos, CELLS)
        print('  %s: %s' % (nm, '  '.join('%s %.3f' % (c[:5], cv.get(c, 0))
                                          for c in CELLS)))
        print('    sep %s'
              % '  '.join('%s %.3f' % (c[:5],
                                       np.nanmean([abs(S[(c, q)]) for q in PROPS]))
                          for c in CELLS))
        print('    run %s'
              % '  '.join('%s %.0f' % (c[:5], st[c]['run']) for c in CELLS))

    # ---------------- joint vs separate activity ----------------
    print('\nACTIVITY: joint or separate cut?')
    act = tercile(raw_axes(px)['scale'], fit).replace(
        {0.0: 'weak', 1.0: 'medium', 2.0: 'strong'})
    act = act.where(act.isin(['weak', 'medium', 'strong']))
    sep_lab = confirm((act + ' ' + labN).where(labN.notna() & act.notna()), DWELL)
    bump = act.replace({'weak': 0.5, 'medium': 0.0, 'strong': -0.5}).astype(float)
    jl, _ = classify(trN - bump, chN, fit)
    joint_lab = confirm((act + ' ' + jl).where(jl.notna() & act.notna()), DWELL)
    for nm, L in (('separate', sep_lab), ('joint', joint_lab)):
        sts = sorted(L[oos].stack().unique())
        S = sep_one_vs_rest(L, P, oos, sts)
        m = np.nanmean([abs(S[(s, c)]) for s in sts for c in PROPS])
        cv = L[oos].stack().value_counts(normalize=True)
        print('  %-9s %2d cells, mean |sep| %.3f, min share %.3f'
              % (nm, len(sts), m, cv.min()))
    print('\nwrote measures_test1.csv and measures_failsurface.csv')


if __name__ == '__main__':
    main()
