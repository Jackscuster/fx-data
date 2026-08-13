import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""A CONTINUOUS trend-versus-range score, cut at terciles. Nine states, no residual.

The structural information is kept -- completed sequences, boundary tests,
break-and-hold, retracement -- but it enters as four continuous readings instead
of four pass/fail gates. A gate throws away everything except which side of it a
bar fell on; a score keeps the distance. Every bar then lands in a tercile, so
the classifier always answers. Structureless bars get assigned and the boundaries
are noisier: that is the accepted cost, not an oversight.

THE FOUR COMPONENTS, all built from bars at or before t, all lagged one bar.

  seq    completed sequence, signed and summed so it CANCELS:
         ((hi - hi_prev) + (lo - lo_prev)) / (2 * sigma). A higher high with a
         lower low nets to nothing, which is the distinction the gate version
         existed to make and the one thing that must survive the move to a score.
  bound  boundary test: how far outside the confirmed swing band price sits, in
         vol units, and how deep inside it when it is inside. Positive outside,
         negative inside, continuous through zero.
  hold   break-and-hold: the share of the last K bars spent beyond the boundary
         times the mean distance beyond, in vol units. The continuous form of
         "B bars outside by at least D".
  pull   1 - retracement from the running extreme as a fraction of the impulse.
         High when a move has not given anything back.

EQUAL WEIGHTS, on purpose. Each component is standardised on IS and the four are
summed unweighted. Fitting weights would be a four-parameter search against a
target, and the target here is a description, not an outcome -- there is nothing
legitimate to fit them to. Equal weighting is stated rather than optimised.

THE CUT is the nine-box's own tercile with hysteresis, fitted on IS and applied
unchanged. High score is TRENDING, middle is DRIFTING, low is RANGE.

Writes results/shapescore.csv and results/shapescore_confirm.csv.
"""
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
SPLIT = pd.Timestamp('2016-01-01')
NS = tuple(range(2, 41))
NSHUF = int(os.environ.get('FX_NSHUF', 20))
NFIN = int(os.environ.get('FX_NFIN', 120))
KHOLD = 10
THREE = ['trending', 'drifting', 'range']
PROPS = ['autocorr', 'range_to_path', 'dir_changes', 'mean_crossings']

from structure import swings, _seg, VOLWIN
from structsel import chosen_cell
from structval import properties, surrogate, MIN_SHARE
from combined import confirm, DWELL
from ninestate import tercile
from classifier import zfit

MAGP = ['realised_vol', 'avg_abs_move']


def components(px, N):
    """-> dict of four continuous structural readings, each lagged one bar."""
    lp = np.log(px.astype(float))
    sig = lp.diff().rolling(VOLWIN).std()
    out = {k: {} for k in ('seq', 'bound', 'hold', 'pull')}
    for p in px.columns:
        c, sg = lp[p].values, sig[p].values
        hi, hip, lo, lop = swings(c, N)
        with np.errstate(invalid='ignore', divide='ignore'):
            seq = ((hi - hip) + (lo - lop)) / (2 * sg)
            above = (c - hi) / sg
            below = (lo - c) / sg
            inside = -np.minimum(c - lo, hi - c) / sg
            bound = np.where(c > hi, above, np.where(c < lo, below, inside))
            beyond = np.maximum(np.maximum(above, below), 0.0)
            hold = pd.Series(beyond).rolling(KHOLD).mean().values
            sh_ = pd.Series(c).groupby(_seg(lo)).cummax().values
            sl_ = pd.Series(c).groupby(_seg(hi)).cummin().values
            ru = np.where(sh_ - lo > 0, (sh_ - c) / (sh_ - lo), np.nan)
            rd = np.where(hi - sl_ > 0, (c - sl_) / (hi - sl_), np.nan)
            pull = 1.0 - np.where(c >= (hi + lo) / 2, ru, rd)
        idx = px.index
        out['seq'][p] = pd.Series(np.abs(seq), index=idx)
        out['bound'][p] = pd.Series(bound, index=idx)
        out['hold'][p] = pd.Series(hold, index=idx)
        out['pull'][p] = pd.Series(np.clip(pull, -1, 2), index=idx)
    inf = [np.inf, -np.inf]
    return {k: pd.DataFrame(v).replace(inf, np.nan).shift(1)
            for k, v in out.items()}


def score_at(px, N, fit):
    """-> (three-state labels, raw score). Equal-weighted, IS-standardised."""
    C = components(px, N)
    Z = zfit({k: v for k, v in C.items()}, fit)
    sc = sum(Z[k] for k in C)
    t = tercile(sc, fit)
    lab = pd.DataFrame(np.where(t.notna(),
                                np.select([t.values == 2, t.values == 1],
                                          ['trending', 'drifting'], 'range'),
                                None), index=px.index, columns=px.columns)
    lab = lab.where(t.notna())
    return confirm(lab, DWELL), sc


def lookback(px, N):
    lp = np.log(px.astype(float))
    a = []
    for p in px.columns:
        c = lp[p].values; n = len(c); s = pd.Series(c)
        m = (s == s.rolling(2 * N + 1, center=True).max()).values
        pos = np.flatnonzero(m); conf = pos + N
        k = conf < n; pos, conf = pos[k], conf[k]
        i = np.searchsorted(conf, np.arange(n), 'right') - 1
        prev = np.where(i >= 1, pos[np.clip(i - 1, 0, None)], np.nan)
        a.append((np.arange(n) - prev)[np.isfinite(prev)])
    return float(np.median(np.concatenate(a)))


def gap(d, col):
    keep = d.s.value_counts(normalize=True)
    d = d[d.s.isin(keep[keep >= MIN_SHARE].index)]
    if d.s.nunique() < 2 or len(d) < 500:
        return np.nan
    g = d.groupby('s')[col].mean()
    return (g.max() - g.min()) / d[col].std()


def block(lab, P, mask, props=PROPS):
    L = lab[mask]
    st = L.stack()
    seps = []
    for c in props:
        d = pd.DataFrame({'s': st, c: P[c][mask].stack()}).dropna()
        seps.append(gap(d, c))
    runs, diag = [], []
    for p in L.columns:
        v = L[p].dropna()
        if len(v) < 50:
            continue
        b = np.flatnonzero(np.r_[True, v.values[1:] != v.values[:-1]])
        runs.append(np.diff(np.r_[b, len(v)]))
        diag.append((v.values[1:] == v.values[:-1]).mean())
    Rn = np.concatenate(runs) if runs else np.array([np.nan])
    cv = st.value_counts(normalize=True)
    per = {}
    for p in L.columns:
        v = L[p].dropna()
        if len(v) < 50:
            continue
        gid = (v != v.shift()).cumsum()
        for _, g in v.groupby(gid):
            per.setdefault(g.iloc[0], []).append(len(g))
    return dict(sep=float(np.nanmean(seps)),
                residual=1.0 - len(st) / (L.shape[0] * L.shape[1]),
                median_run=float(np.median(Rn)), diagonal=float(np.mean(diag)),
                **{k: cv.get(k, 0.0) for k in THREE},
                **{('run_' + k): float(np.median(v)) for k, v in per.items()})


def per_pair(lab, P, mask, props=PROPS):
    out = {}
    for p in lab.columns:
        v = lab[p][mask]
        vals = []
        for c in props:
            d = pd.DataFrame({'s': v, c: P[c][p][mask]}).dropna()
            vals.append(gap(d, c) if len(d) > 500 else np.nan)
        out[p] = float(np.nanmean(vals))
    return out


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    fit = np.asarray(px.index < SPLIT)
    P = properties(px)
    pairs = list(px.columns)
    print('CONTINUOUS TREND-vs-RANGE SCORE, terciles, N = %d..%d every value.'
          % (NS[0], NS[-1]))
    print('components: seq (cancelling), bound, hold, pull. Equal weights,')
    print('standardised on IS. Cut = the nine-box tercile with hysteresis.')

    labs, rows = {}, []
    for N in NS:
        lab, _ = score_at(px, N, fit)
        labs[N] = lab
        r = block(lab, P, fit)
        r.update(N=N, lookback=lookback(px, N))
        rows.append(r)
    S = pd.DataFrame(rows)

    print('\nIN-SAMPLE. coverage is fixed by construction, so it is a check only.')
    print('  %3s %5s | %8s %8s %6s %6s | %6s %5s %5s | %6s %6s'
          % ('N', 'days', 'trending', 'drifting', 'range', 'resid', 'sep',
             'run', 'diag', 'runRng', 'runTrn'))
    for _, r in S.iterrows():
        print('  %3d %5.0f | %8.3f %8.3f %6.3f %6.3f | %6.3f %5.0f %5.3f'
              ' | %6.0f %6.0f'
              % (r.N, r.lookback, r.trending, r.drifting, r['range'],
                 r.residual, r.sep, r.median_run, r.diagonal,
                 r.get('run_range', np.nan), r.get('run_trending', np.nan)))

    print('\nNULLS on IS, %d draws, every window against its own surrogate'
          % NSHUF)
    rng = np.random.default_rng(24680)
    acc = {N: [] for N in NS}
    pacc = {N: [] for N in NS}
    for i in range(NSHUF):
        px2 = surrogate(px, 'sign', rng)
        P2 = properties(px2)
        for N in NS:
            l2, _ = score_at(px2, N, fit)
            acc[N].append(block(l2, P2, fit)['sep'])
            pacc[N].append(per_pair(l2, P2, fit))
        if (i + 1) % 5 == 0:
            print('  %d/%d' % (i + 1, NSHUF), flush=True)
    S['surr'] = [np.nanmean(acc[N]) for N in NS]
    S['corr'] = S.sep - S.surr
    pp = []
    for N in NS:
        rp = per_pair(labs[N], P, fit)
        sp = pd.DataFrame(pacc[N])
        c = {p: rp[p] - sp[p].mean() for p in pairs}
        S.loc[S.N == N, 'pairs_pos'] = int(sum(v > 0 for v in c.values()))
        S.loc[S.N == N, 'pairs_med'] = float(np.median(list(c.values())))
        for p in pairs:
            pp.append(dict(N=N, pair=p, corrected=c[p]))
    S.to_csv(os.path.join(ROOTOUT, 'shapescore.csv'), index=False)
    pd.DataFrame(pp).to_csv(os.path.join(ROOTOUT, 'shapescore_pairs.csv'),
                            index=False)

    print('\n  %3s %5s | %7s %7s %9s | %6s %5s | %8s %9s'
          % ('N', 'days', 'sep', 'surr', 'corrected', 'run', 'diag',
             'pairs +', 'pair med'))
    for _, r in S.iterrows():
        print('  %3d %5.0f | %7.3f %7.3f %+9.3f | %6.0f %5.3f | %5d/28 %+9.3f'
              % (r.N, r.lookback, r.sep, r.surr, r['corr'], r.median_run,
                 r.diagonal, int(r.pairs_pos), r.pairs_med))

    w = S.sort_values('corr', ascending=False).iloc[0]
    i = list(S.N).index(w.N)
    nb = S.iloc[max(0, i - 2):i + 3]
    print('\nSELECTION on IS: highest null-corrected separation.')
    print('  CHOSEN N=%d, lookback %.0f bars, corrected %+.3f'
          % (w.N, w.lookback, w['corr']))
    print('  neighbourhood N=%d..%d: %s'
          % (nb.N.min(), nb.N.max(), ' '.join('%+.3f' % v for v in nb['corr'])))
    print('  windows with corrected > 0: %d of %d'
          % (int((S['corr'] > 0).sum()), len(S)))

    print('\nHOLDOUT, READ ONCE. N=%d, %d draws.' % (w.N, NFIN))
    oos = ~fit
    ho = block(labs[int(w.N)], P, oos)
    rng2 = np.random.default_rng(11223)
    v = []
    for _ in range(NFIN):
        px2 = surrogate(px, 'sign', rng2)
        l2, _ = score_at(px2, int(w.N), fit)
        v.append(block(l2, properties(px2), oos)['sep'])
    v = np.array(v, float); v = v[np.isfinite(v)]
    p = (1 + int((v >= ho['sep']).sum())) / (len(v) + 1)
    print('  coverage trending %.3f drifting %.3f range %.3f residual %.3f'
          % (ho['trending'], ho['drifting'], ho['range'], ho['residual']))
    print('  median run %.0f  diagonal %.3f  range runs %.0f  trend runs %.0f'
          % (ho['median_run'], ho['diagonal'], ho.get('run_range', np.nan),
             ho.get('run_trending', np.nan)))
    print('  separation %.3f  surrogate %.3f +/- %.3f  corrected %+.3f  p=%.3f'
          % (ho['sep'], v.mean(), v.std(), ho['sep'] - v.mean(), p))
    pd.DataFrame([dict(N=int(w.N), lookback=w.lookback, is_corr=w['corr'],
                       **{('oos_' + k): ho[k] for k in
                          ('sep', 'residual', 'median_run', 'diagonal',
                           'trending', 'drifting', 'range')},
                       surrogate=v.mean(), sd=v.std(),
                       corrected=ho['sep'] - v.mean(), p=p)]).to_csv(
        os.path.join(ROOTOUT, 'shapescore_confirm.csv'), index=False)

    print('\nWHICH WINDOW FOR DAILY ENTRY, HELD FOR WEEKS?')
    print('  the state has to outlast the hold or it is not describing it.')
    print('  %3s %5s | %9s %10s %9s' % ('N', 'days', 'trend runs', 'range runs',
                                        'corrected'))
    for _, r in S[S.N.isin((4, 6, 8, 13, 18, 24, 30))].iterrows():
        print('  %3d %5.0f | %8.0f %10.0f %+9.3f'
              % (r.N, r.lookback, r.get('run_trending', np.nan),
                 r.get('run_range', np.nan), r['corr']))
    print('\nwrote shapescore.csv, shapescore_pairs.csv, shapescore_confirm.csv')


if __name__ == '__main__':
    main()
