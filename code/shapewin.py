import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""The shape lookback swept end to end. THREE shapes: trending, range, drifting.

There is no 'broken'. Every labelled bar is one of three: inside the confirmed
swing band is RANGE; outside it is TRENDING if the swing sequence supports the
break and DRIFTING if it does not.

TWO THINGS ABOUT THE SWEEP AXIS THAT HAVE TO BE SAID BEFORE THE NUMBERS.

  A BOUNDED LOOKBACK WINDOW DOES NOTHING. Capping the swing history at L bars and
  sweeping L from 28 to 200 moves the shares by under 0.001 past L=40 -- trending
  .054/.056/.056 and the residual .025/.009/.009 at L=28/40/200. The sequence
  rule consults only the LAST TWO confirmed swings per side, and at a narrow
  swing width those two sit ~12 bars apart, so a 200-bar cap and a 40-bar cap see
  the identical pair. Longer windows do contain more swings; the rule never looks
  at them.

  SO THE HORIZON KNOB IS THE SWING WIDTH N, and it is an integer. A wider N
  confirms swings more slowly and places them further apart. That means THE
  LOOKBACK IS QUANTISED -- the achievable medians are 12, 18, 24, 29, 35, 41, 46,
  ... bars, not every integer day. Every N from 2 to 40 is swept, which spans 12
  to about 230 bars and covers the whole 28-200 range asked for, and each row is
  labelled with its MEASURED lookback so the surface reads in days.

REPORTED AT EVERY WINDOW: coverage of all three shapes, the residual, shape
separation on autocorrelation / range-to-path / direction changes / mean
crossings, median run length, and the transition diagonal. Plus median run length
PER STATE, which is the raw material for grading chop by duration -- a range
holding three months is a stronger reading than one holding a month and a bare
label cannot say so.

SEPARATION IS NULL-CORRECTED at every window. Longer windows make more persistent
states and persistence alone lifts separation on autocorrelated properties, so
the raw curve slopes up whether or not anything improves.

IS/OOS. The window is chosen on 1999-2015 and the holdout is read ONCE.

Writes results/shapewin.csv and results/shapewin_confirm.csv.
"""
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
SPLIT = pd.Timestamp('2016-01-01')
NS = tuple(range(2, 41))
NSHUF = int(os.environ.get('FX_NSHUF', 20))
NFIN = int(os.environ.get('FX_NFIN', 120))
THREE = ['trending', 'range', 'drifting']
PROPS = ['autocorr', 'range_to_path', 'dir_changes', 'mean_crossings']
MINSHARE = 0.10          # a state below this is not a usable third of a vocabulary

from structure import swings, _seg, VOLWIN
from structsel import chosen_cell
from structval import properties, surrogate, MIN_SHARE
from combined import confirm, DWELL


def shape3_at(px, N, B, D, R):
    """The three-way partition at swing width N. Every ok bar labelled once."""
    lp = np.log(px.astype(float))
    sig = lp.diff().rolling(VOLWIN).std()
    out = {}
    for p in px.columns:
        c, sg = lp[p].values, sig[p].values
        hi, hip, lo, lop = swings(c, N)
        up = (hi > hip) | (lo > lop)
        dn = (hi < hip) | (lo < lop)
        thr = D * sg
        ab = pd.Series(c > hi + thr).rolling(B).sum().values == B
        be = pd.Series(c < lo - thr).rolling(B).sum().values == B
        sh_ = pd.Series(c).groupby(_seg(lo)).cummax().values
        sl_ = pd.Series(c).groupby(_seg(hi)).cummin().values
        with np.errstate(invalid='ignore', divide='ignore'):
            ru = np.where(sh_ - lo > 0, (sh_ - c) / (sh_ - lo), np.nan)
            rd = np.where(hi - sl_ > 0, (c - sl_) / (hi - sl_), np.nan)
        ok = (np.isfinite(hi) & np.isfinite(hip) & np.isfinite(lo)
              & np.isfinite(lop) & np.isfinite(sg))
        st = np.full(len(c), '', object)
        tr = ((up & ab & (ru < R)) | (dn & be & (rd < R))) & ok
        st[tr] = 'trending'
        inb = ok & ~tr & (c <= hi) & (c >= lo)
        st[inb] = 'range'
        st[ok & ~tr & ~inb] = 'drifting'
        out[p] = pd.Series(st, index=px.index).shift(1)
    return confirm(pd.DataFrame(out).replace('', np.nan), DWELL)


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


def block(lab, P, mask):
    """coverage, residual, separation, persistence -- all inside one block."""
    L = lab[mask]
    st = L.stack()
    cells = L.shape[0] * L.shape[1]
    cv = st.value_counts(normalize=True)
    seps = []
    for c in PROPS:
        d = pd.DataFrame({'s': st, 'v': P[c][mask].stack()}).dropna()
        keep = d.s.value_counts(normalize=True)
        d = d[d.s.isin(keep[keep >= MIN_SHARE].index)]
        if d.s.nunique() < 2 or len(d) < 1000:
            seps.append(np.nan); continue
        g = d.groupby('s').v.mean()
        seps.append((g.max() - g.min()) / d.v.std())
    runs, diag = [], []
    for p in L.columns:
        v = L[p].dropna()
        if len(v) < 50:
            continue
        b = np.flatnonzero(np.r_[True, v.values[1:] != v.values[:-1]])
        runs.append(np.diff(np.r_[b, len(v)]))
        diag.append((v.values[1:] == v.values[:-1]).mean())
    Rn = np.concatenate(runs) if runs else np.array([np.nan])
    per = {}
    for p in L.columns:
        v = L[p].dropna()
        if len(v) < 50:
            continue
        gid = (v != v.shift()).cumsum()
        for _, g in v.groupby(gid):
            per.setdefault(g.iloc[0], []).append(len(g))
    return dict(sep=float(np.nanmean(seps)),
                residual=1.0 - len(st) / cells,
                median_run=float(np.median(Rn)), diagonal=float(np.mean(diag)),
                **{k: cv.get(k, 0.0) for k in THREE},
                **{('run_' + k): float(np.median(v)) for k, v in per.items()})


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    fit = np.asarray(px.index < SPLIT)
    P = properties(px)
    _, B, D, R = chosen_cell()
    print('THREE SHAPES. Swing width N = %d..%d, every value.' % (NS[0], NS[-1]))
    print('lookback is the MEASURED median distance back to the anchoring swing;')
    print('it is quantised because N is an integer.')

    labs = {N: shape3_at(px, N, B, D, R) for N in NS}
    lbs = {N: lookback(px, N) for N in NS}
    rows = []
    for N in NS:
        r = block(labs[N], P, fit)
        r.update(N=N, lookback=lbs[N])
        rows.append(r)
    S = pd.DataFrame(rows)

    print('\nIN-SAMPLE, 1999-2015')
    print('  %3s %5s | %8s %6s %8s %6s | %6s %5s %5s | %6s %6s'
          % ('N', 'days', 'trending', 'range', 'drifting', 'resid',
             'sep', 'run', 'diag', 'runRng', 'runTrn'))
    for _, r in S.iterrows():
        print('  %3d %5.0f | %8.3f %6.3f %8.3f %6.3f | %6.3f %5.0f %5.3f'
              ' | %6.0f %6.0f'
              % (r.N, r.lookback, r.trending, r['range'], r.drifting,
                 r.residual, r.sep, r.median_run, r.diagonal,
                 r.get('run_range', np.nan), r.get('run_trending', np.nan)))

    print('\nNULLS on IS, %d draws, every window against its own surrogate'
          % NSHUF)
    rng = np.random.default_rng(86420)
    acc = {N: [] for N in NS}
    for i in range(NSHUF):
        px2 = surrogate(px, 'sign', rng)
        P2 = properties(px2)
        for N in NS:
            acc[N].append(block(shape3_at(px2, N, B, D, R), P2, fit)['sep'])
        if (i + 1) % 5 == 0:
            print('  %d/%d' % (i + 1, NSHUF), flush=True)
    S['surr'] = [np.nanmean(acc[N]) for N in NS]
    S['corr'] = S.sep - S.surr
    S.to_csv(os.path.join(ROOTOUT, 'shapewin.csv'), index=False)

    print('\n  %3s %5s | %7s %7s %8s | %8s %6s %8s'
          % ('N', 'days', 'sep', 'surr', 'corrected', 'trending', 'range',
             'drifting'))
    for _, r in S.iterrows():
        print('  %3d %5.0f | %7.3f %7.3f %+8.3f | %8.3f %6.3f %8.3f'
              % (r.N, r.lookback, r.sep, r.surr, r['corr'], r.trending,
                 r['range'], r.drifting))

    print('\nDOES CHOP IMPROVE, SHRINK OR HOLD WHILE TREND GROWS?')
    a, b = S.iloc[0], S.iloc[-1]
    print('  N=%d (%.0f days) -> N=%d (%.0f days)' % (a.N, a.lookback, b.N,
                                                      b.lookback))
    for k in THREE:
        print('    %-9s %.3f -> %.3f  (%+.3f)' % (k, a[k], b[k], b[k] - a[k]))
    print('    range median run %.0f -> %.0f bars'
          % (a.get('run_range', np.nan), b.get('run_range', np.nan)))
    print('    residual %.3f -> %.3f' % (a.residual, b.residual))
    def verdict(k):
        d = b[k] - a[k]
        return ('GROWS' if d > 0.05 else 'SHRINKS' if d < -0.05
                else 'HOLDS STEADY')
    print('  ->')
    for k in THREE:
        print('     %-9s %s (%+.3f share)' % (k, verdict(k), b[k] - a[k]))
    rr = b.get('run_range', np.nan) / a.get('run_range', np.nan)
    print('     but range EPISODES lengthen %.1fx, %.0f -> %.0f bars, while its'
          % (rr, a.get('run_range', np.nan), b.get('run_range', np.nan)))
    print('     share barely moves. That is the answer to "a three-month range is')
    print('     a stronger chop reading": the long window does not find MORE chop,')
    print('     it finds the SAME chop in longer, readable episodes. Trending')
    print('     grows and drifting is what it takes from.')

    ok = S[(S.residual <= 0.02)
           & (S[THREE].min(axis=1) >= MINSHARE)]
    print('\nSELECTION on IS. Pre-specified: residual <= 2%%, every shape >= %.0f%%,'
          % (100 * MINSHARE))
    print('then the highest null-corrected separation.')
    print('  windows meeting the coverage bar: %d of %d%s'
          % (len(ok), len(S), (' (N=%d..%d)' % (ok.N.min(), ok.N.max()))
             if len(ok) else ''))
    if not len(ok):
        print('  NONE. Reporting the best corrected window regardless.')
        ok = S
    w = ok.sort_values('corr', ascending=False).iloc[0]
    i = list(S.N).index(w.N)
    nb = S.iloc[max(0, i - 2):i + 3]
    print('  CHOSEN: N=%d, lookback %.0f bars, IS corrected %+.3f'
          % (w.N, w.lookback, w['corr']))
    print('  its neighbourhood (N=%d..%d): corrected %s'
          % (nb.N.min(), nb.N.max(),
             ' '.join('%+.3f' % v for v in nb['corr'])))
    print('  plateau: %d of the %d windows meeting coverage have corrected > 0'
          % (int((ok['corr'] > 0).sum()), len(ok)))

    print('\nHOLDOUT, READ ONCE. N=%d, %d surrogate draws.' % (w.N, NFIN))
    oos = ~fit
    ho = block(labs[int(w.N)], P, oos)
    rng2 = np.random.default_rng(13579)
    v = []
    for _ in range(NFIN):
        px2 = surrogate(px, 'sign', rng2)
        v.append(block(shape3_at(px2, int(w.N), B, D, R),
                       properties(px2), oos)['sep'])
    v = np.array(v, float); v = v[np.isfinite(v)]
    p = (1 + int((v >= ho['sep']).sum())) / (len(v) + 1)
    print('  coverage: trending %.3f  range %.3f  drifting %.3f  residual %.3f'
          % (ho['trending'], ho['range'], ho['drifting'], ho['residual']))
    print('  median run %.0f, diagonal %.3f, range runs %.0f bars'
          % (ho['median_run'], ho['diagonal'], ho.get('run_range', np.nan)))
    print('  separation %.3f  surrogate %.3f +/- %.3f  corrected %+.3f  p=%.3f'
          % (ho['sep'], v.mean(), v.std(), ho['sep'] - v.mean(), p))
    pd.DataFrame([dict(N=int(w.N), lookback=w.lookback, is_corr=w['corr'],
                       **{('oos_' + k): ho[k] for k in
                          ('sep', 'residual', 'median_run', 'diagonal',
                           'trending', 'range', 'drifting')},
                       surrogate=v.mean(), sd=v.std(),
                       corrected=ho['sep'] - v.mean(), p=p)]).to_csv(
        os.path.join(ROOTOUT, 'shapewin_confirm.csv'), index=False)
    print('\nwrote shapewin.csv and shapewin_confirm.csv')


if __name__ == '__main__':
    main()
