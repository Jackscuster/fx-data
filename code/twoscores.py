import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Two scores, not one axis. Trend and chop measured independently.

THE CLAIM BEING TESTED. A single continuous "how trend-like" number puts
everything on one line, and the middle of a line is ambiguous by construction.
Trend and chop are different things, so score them separately and classify on the
PAIR.

  trend high, chop low     trending
  trend low,  chop high    ranging
  trend high, chop high    trending inside a wider range, or a range breaking
  trend low,  chop low     the only honest "neither"

THE FIRST THING TO CHECK, BEFORE ANY OF THAT. If the two scores come out
strongly negatively correlated they ARE one axis wearing two names, the 2x2
collapses onto its diagonal, and the premise fails. That correlation is reported
first and everything else is read in its light.

TREND SCORE -- is price making progress in one direction.
  disp   |net displacement| / path walked over the window
  seq    swing sequence, signed and SUMMED SO IT CANCELS: a higher high with a
         lower low nets to nothing

CHOP SCORE -- is price respecting boundaries and returning to them.
  hold   how far the pullback extreme sits above the prior swing extreme.
         THE SPEC ASSIGNED THIS TO TREND AND THE DATA SAYS IT IS A CHOP
         MEASURE. On IS, disp reads range/path +0.170 and mean crossings
         -0.220, while hold reads -0.254 and +0.288 -- the opposite sign on
         both. Summed into one score they cancel, which is why the trend score
         first came out at 0.034 while disp alone reached 0.088 and hold alone
         0.147. Moved here, and the direction was confirmed on IS before the
         holdout was read.
  tests  how many times the band edges have been approached and held
  revert crossings of the band midpoint per window
  fails  failed breaks: breached the band then closed back inside
  inside share of window bars spent inside the established range

Each component is standardised on IS and summed with equal weights inside its own
score. Fitting weights would be a search against a target, and the target here is
a description.

EVERYTHING IS LAGGED ONE BAR and built only from bars at or before t. Window is
the locked swing width N=19, measured lookback 106 bars.

Writes results/twoscores.csv, results/twoscores_cells.csv.
"""
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
SPLIT = pd.Timestamp('2016-01-01')
NSHUF = int(os.environ.get('FX_NSHUF', 20))
W = 106                  # the locked lookback, in bars
KFAIL = 20

from structure import swings, _seg, VOLWIN
from structsel import chosen_cell
from structval import properties, surrogate
from classifier import zfit
from combined import confirm, DWELL
from ninestate import raw_axes, tercile
from shape3 import N_SCORE
from episodes import episodes, block_boot

PROPS = ['autocorr', 'range_to_path', 'dir_changes', 'mean_crossings']
CELLS = ['trending', 'ranging', 'trend-in-range', 'neither']


def raw_parts(px, N=N_SCORE, Wl=None, kfail=None, volwin=None):
    """-> (trend components, chop components). All lagged one bar.

    Wl, kfail and volwin override the locked constants for SENSITIVITY TESTING
    ONLY. All three default to the module values, so every existing caller is
    unchanged -- refit.py's control (the 2015 vintage must reproduce the shipped
    states exactly) is the regression test for that.
    """
    W = globals()['W'] if Wl is None else Wl
    KFAIL = globals()['KFAIL'] if kfail is None else kfail
    VOLWIN = globals()['VOLWIN'] if volwin is None else volwin
    lp = np.log(px.astype(float))
    rr = lp.diff()
    sig = rr.rolling(VOLWIN).std()
    inf = [np.inf, -np.inf]
    T, C = {}, {}

    net = (lp - lp.shift(W)).abs()
    path = rr.abs().rolling(W).sum()
    T['disp'] = (net / path).replace(inf, np.nan)

    seq, hold, tests, fails, inside, revert = {}, {}, {}, {}, {}, {}
    for p in px.columns:
        c, sg = lp[p].values, sig[p].values
        hi, hip, lo, lop = swings(c, N)
        with np.errstate(invalid='ignore', divide='ignore'):
            seq[p] = ((hi - hip) + (lo - lop)) / (2 * sg)
            sh_ = pd.Series(c).groupby(_seg(lo)).cummax().values
            sl_ = pd.Series(c).groupby(_seg(hi)).cummin().values
            # pullbacks holding: how far the retracement low sits ABOVE the
            # prior swing low (and the mirror), in vol units
            up_hold = (sl_ - lop) / sg
            dn_hold = (hip - sh_) / sg
            hold[p] = np.where(c >= (hi + lo) / 2, up_hold, dn_hold)
            width = np.where(hi - lo > 0, hi - lo, np.nan)
            near_hi = (hi - c) / (0.25 * width)
            near_lo = (c - lo) / (0.25 * width)
            touch = ((near_hi <= 1) | (near_lo <= 1))
            outside = (c > hi) | (c < lo)
            tests[p] = pd.Series(touch & ~outside).rolling(W).sum().values
            back = pd.Series(outside).shift(1).fillna(False).values & ~outside
            fails[p] = pd.Series(back).rolling(KFAIL).sum().values
            inside[p] = pd.Series(~outside).rolling(W).mean().values
            mid = (hi + lo) / 2
            dev = c - mid
            cr = pd.Series(np.sign(dev)).diff().abs().fillna(0).values > 0
            revert[p] = pd.Series(cr).rolling(W).mean().values
    idx, col = px.index, px.columns
    mk = lambda d: pd.DataFrame(d, index=idx, columns=col).replace(inf, np.nan)
    T['seq'] = mk({p: np.abs(seq[p]) for p in col})
    C['hold'] = mk(hold)          # see the docstring: it measures chop, not trend
    C['tests'] = mk(tests)
    C['fails'] = mk(fails)
    C['inside'] = mk(inside)
    C['revert'] = mk(revert)
    return ({k: v.shift(1) for k, v in T.items()},
            {k: v.shift(1) for k, v in C.items()})


def two_scores(px, fit, N=N_SCORE):
    T, C = raw_parts(px, N)
    zt, zc = zfit(T, fit), zfit(C, fit)
    return sum(zt[k] for k in T), sum(zc[k] for k in C)


def classify(tr, ch, fit):
    """2x2 on the pair of scores, cut at IS medians."""
    ft = np.where(fit[:, None], tr.values, np.nan)
    fc = np.where(fit[:, None], ch.values, np.nan)
    mt, mc = np.nanmedian(ft), np.nanmedian(fc)
    hi_t, hi_c = tr > mt, ch > mc
    lab = pd.DataFrame(np.select(
        [(hi_t & ~hi_c).values, (~hi_t & hi_c).values, (hi_t & hi_c).values],
        ['trending', 'ranging', 'trend-in-range'], 'neither'),
        index=tr.index, columns=tr.columns)
    ok = tr.notna() & ch.notna()
    return confirm(lab.where(ok), DWELL), (mt, mc)


def sep_one_vs_rest(lab, P, mask, states):
    st = lab[mask].stack()
    d = pd.DataFrame({'s': st})
    for c in PROPS:
        d[c] = P[c][mask].stack()
    d = d.dropna()
    out = {}
    n = len(d)
    for c in PROPS:
        sd = d[c].std(); tot = d[c].sum()
        g = d.groupby('s')[c].agg(['mean', 'size'])
        for s in states:
            if s not in g.index or g.loc[s, 'size'] < 200 or n - g.loc[s, 'size'] < 200:
                out[(s, c)] = np.nan; continue
            rest = (tot - g.loc[s, 'mean'] * g.loc[s, 'size']) / (n - g.loc[s, 'size'])
            out[(s, c)] = (g.loc[s, 'mean'] - rest) / sd
    return out


def stats(lab, mask, states):
    L = lab[mask]
    st = L.stack()
    cv = st.value_counts(normalize=True)
    runs, stay, tot = {}, {}, {}
    for p in L.columns:
        v = L[p].dropna()
        if len(v) < 50:
            continue
        gid = (v != v.shift()).cumsum()
        for _, g in v.groupby(gid):
            runs.setdefault(g.iloc[0], []).append(len(g))
        a, b = v.values[:-1], v.values[1:]
        for s in states:
            m = a == s
            if m.sum():
                stay[s] = stay.get(s, 0) + int((b[m] == s).sum())
                tot[s] = tot.get(s, 0) + int(m.sum())
    return {s: dict(share=float(cv.get(s, 0.0)),
                    run=float(np.median(runs[s])) if s in runs else np.nan,
                    diag=(stay.get(s, 0) / tot[s]) if tot.get(s) else np.nan)
            for s in states}


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    fit = np.asarray(px.index < SPLIT)
    P = properties(px)
    tr, ch = two_scores(px, fit)

    print('TWO SCORES at the locked window (N=%d, ~%d bars)' % (N_SCORE, W))
    print('\nTHE FIRST QUESTION: ARE THEY ONE AXIS?')
    d = pd.DataFrame({'t': tr.stack(), 'c': ch.stack()}).dropna()
    r = float(np.corrcoef(d.t, d.c)[0, 1])
    print('  pooled correlation of trend and chop scores: %+.3f' % r)
    per = {}
    for p in px.columns:
        a, b = tr[p], ch[p]
        m = a.notna() & b.notna()
        if m.sum() > 500:
            per[p] = float(np.corrcoef(a[m], b[m])[0, 1])
    v = np.array(list(per.values()))
    print('  per pair: median %+.3f, range %+.3f to %+.3f'
          % (np.median(v), v.min(), v.max()))
    print("  |r| < 0.70 is the project's own decorrelation bar (gate 8).")
    print('  -> %s' % ('THEY ARE NOT ONE AXIS' if abs(r) < 0.70
                       else 'ONE AXIS WEARING TWO NAMES -- the 2x2 collapses'))

    lab, (mt, mc) = classify(tr, ch, fit)
    print('\nOCCUPANCY OF THE 2x2, holdout')
    o = lab[~fit].stack()
    cv = o.value_counts(normalize=True)
    for s in CELLS:
        print('    %-16s %.3f' % (s, cv.get(s, 0.0)))
    print('  the honest "neither" bucket is %.1f%% of bars.' % (100 * cv.get('neither', 0)))
    print('  (the single-axis version left %.1f%% in its middle tercile)' % 41.0)

    print('\nPER CELL, holdout: separation one-vs-rest, run length, diagonal')
    S = sep_one_vs_rest(lab, P, ~fit, CELLS)
    T = stats(lab, ~fit, CELLS)
    print('  %-16s %8s %7s %6s %6s | %s'
          % ('cell', 'sep', 'share', 'run', 'diag',
             ' '.join('%14s' % c for c in PROPS)))
    rows = []
    for s in CELLS:
        m = np.nanmean([abs(S[(s, c)]) for c in PROPS])
        print('  %-16s %8.3f %7.3f %6.0f %6.3f | %s'
              % (s, m, T[s]['share'], T[s]['run'], T[s]['diag'],
                 ' '.join('%+14.3f' % S[(s, c)] for c in PROPS)))
        rows.append(dict(cell=s, sep=m, **T[s],
                         **{('sep_' + c): S[(s, c)] for c in PROPS}))

    # THE MARGINAL TEST. One-vs-rest inside the 2x2 is diluted by construction:
    # 'trending' is compared against a rest that CONTAINS trend-in-range, which
    # also has a high trend score. So each axis is also cut on its own, high
    # against low, which is the clean question of whether that score works.
    print('\nEACH AXIS ON ITS OWN -- high vs low, the undiluted test')
    marg = {}
    for nm, sc in (('trend', tr), ('chop', ch)):
        m = np.nanmedian(np.where(fit[:, None], sc.values, np.nan))
        L = confirm(pd.DataFrame(np.where(sc > m, 'high', 'low'),
                                 index=sc.index,
                                 columns=sc.columns).where(sc.notna()), DWELL)
        Sm = sep_one_vs_rest(L, P, ~fit, ['high', 'low'])
        Tm = stats(L, ~fit, ['high', 'low'])
        g = np.nanmean([abs(Sm[('high', c)]) for c in PROPS])
        marg[nm] = (L, g)
        print('  %-6s score: |sep| high vs low %.3f, run %.0f, diag %.3f  | %s'
              % (nm, g, Tm['high']['run'], Tm['high']['diag'],
                 ' '.join('%s %+.3f' % (c[:9], Sm[('high', c)]) for c in PROPS)))

    print('\nNULLS, %d draws' % NSHUF)
    rng = np.random.default_rng(101)
    acc = {s: [] for s in CELLS}
    macc = {'trend': [], 'chop': []}
    for i in range(NSHUF):
        px2 = surrogate(px, 'sign', rng)
        P2 = properties(px2)
        t2, c2 = two_scores(px2, fit)
        l2, _ = classify(t2, c2, fit)
        S2 = sep_one_vs_rest(l2, P2, ~fit, CELLS)
        for s in CELLS:
            acc[s].append(np.nanmean([abs(S2[(s, c)]) for c in PROPS]))
        for nm, sc in (('trend', t2), ('chop', c2)):
            m2 = np.nanmedian(np.where(fit[:, None], sc.values, np.nan))
            L2 = confirm(pd.DataFrame(np.where(sc > m2, 'high', 'low'),
                                      index=sc.index, columns=sc.columns
                                      ).where(sc.notna()), DWELL)
            Sm2 = sep_one_vs_rest(L2, P2, ~fit, ['high', 'low'])
            macc[nm].append(np.nanmean([abs(Sm2[('high', c)]) for c in PROPS]))
        if (i + 1) % 5 == 0:
            print('  %d/%d' % (i + 1, NSHUF), flush=True)
    print('\n  %-16s %8s %9s %9s' % ('cell', 'real', 'surrogate', 'corrected'))
    for j, s in enumerate(CELLS):
        sv = np.nanmean(acc[s])
        print('  %-16s %8.3f %9.3f %+9.3f' % (s, rows[j]['sep'], sv,
                                              rows[j]['sep'] - sv))
        rows[j]['surr'] = sv
        rows[j]['corr'] = rows[j]['sep'] - sv
    print('\n  MARGINAL, each axis on its own')
    for nm in ('trend', 'chop'):
        sv = np.nanmean(macc[nm])
        print('  %-16s %8.3f %9.3f %+9.3f' % (nm + ' high', marg[nm][1], sv,
                                              marg[nm][1] - sv))
        rows.append(dict(cell=nm + ' high (marginal)', sep=marg[nm][1],
                         surr=sv, corr=marg[nm][1] - sv))
    pd.DataFrame(rows).to_csv(os.path.join(ROOTOUT, 'twoscores_cells.csv'),
                              index=False)

    print('\nEPISODE BASIS -- a 20-bar state is one observation')
    E = episodes(lab, P)
    print('  %d holdout bars -> %d episodes (%.1fx)'
          % (int(lab[~fit].notna().sum().sum()), len(E),
             lab[~fit].notna().sum().sum() / max(len(E), 1)))

    print('\nJOINT vs SEPARATE CUTS with activity')
    act = tercile(raw_axes(px)['scale'], fit).replace(
        {0.0: 'weak', 1.0: 'medium', 2.0: 'strong'})
    act = act.where(act.isin(['weak', 'medium', 'strong']))
    sep_lab = confirm((act + ' ' + lab).where(lab.notna() & act.notna()), DWELL)
    # joint: a weak-activity bar needs MORE structural evidence to be trending
    # a weak-activity bar must clear a HIGHER trend bar to be called trending,
    # since low participation makes a clean sequence less meaningful. .replace
    # rather than .map -- DataFrame.map does not exist in the pinned pandas and
    # the section failed silently on it.
    bump = act.replace({'weak': 0.5, 'medium': 0.0, 'strong': -0.5}).astype(float)
    jl, _ = classify(tr - bump, ch, fit)
    joint_lab = confirm((act + ' ' + jl).where(jl.notna() & act.notna()), DWELL)
    for nm, L in (('separate cuts', sep_lab), ('joint cut', joint_lab)):
        sts = sorted(L[~fit].stack().unique())
        Sx = sep_one_vs_rest(L, P, ~fit, sts)
        m = np.nanmean([abs(Sx[(s, c)]) for s in sts for c in PROPS])
        cvx = L[~fit].stack().value_counts(normalize=True)
        print('  %-14s %2d cells, mean |sep| %.3f, min share %.3f'
              % (nm, len(sts), m, cvx.min()))

    pd.DataFrame({'trend': tr.stack(), 'chop': ch.stack()}).describe().to_csv(
        os.path.join(ROOTOUT, 'twoscores.csv'))
    print('\nwrote twoscores.csv and twoscores_cells.csv')


if __name__ == '__main__':
    main()
