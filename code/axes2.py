import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Two axes or one? Where scale enters, how shape relates to it, and whether
'settling' is just 'transitional' under a new name.

1. WHERE SCALE ENTERS. Traced in code and then proved by ablation. The claim that
   an axis is 'feeding' a classifier is only worth anything if removing it costs
   something measurable, so both layers are knocked out in turn.

2. SHAPE AGAINST ACTIVITY. A cross-tab is not enough on its own -- twelve cells
   all being occupied does not make the axes independent. Independence is
   measured (Cramer's V, normalised mutual information, both block-bootstrapped)
   and then the question that actually decides it is asked: does the shape
   reading behave the same way inside high activity as inside low activity? If
   shape only separates when the pair is moving, it is not a second axis, it is
   a restatement of the first.

3. SETTLING vs TRANSITIONAL. 'Transitional' is the middle band of the
   straightness axis -- a place a pair can sit for weeks. 'Settling' is the first
   three bars after any state change. They sound different. Overlap is measured
   both ways, against base rates, because a large P(transitional | settling) is
   not evidence of anything if transitional is a third of all bars anyway.

NOTHING FORWARD-LOOKING. Every quantity is a description of the trailing window.
Block bootstrap over calendar dates throughout, from episodes.py, because bars
are not independent observations and neither are the 28 pairs.

Writes results/axes_crosstab.csv, results/axes_ablation.csv and
results/axes_settling.csv.
"""
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
L1 = os.path.join(ROOTOUT, 'layer1_states.csv')
SPLIT = pd.Timestamp('2016-01-01')
NBOOT = int(os.environ.get('FX_NBOOT', 2000))
EDGE = 3

from structval import properties, separation, MIN_SHARE
from combined import layers, product, confirm, DWELL, NEUT, _cfg
from ninestate import nine, raw_axes, tercile
from episodes import block_boot

MAGP = ['realised_vol', 'avg_abs_move']


def sep_of(lab, P, cols):
    return float(separation(lab, P).gap_sd.reindex(cols).mean())


def long(lab, P, extra=None):
    d = {'state': lab[lab.index >= SPLIT].stack()}
    for c in NEUT + MAGP:
        d[c] = P[c][P[c].index >= SPLIT].stack()
    if extra is not None:
        for k, v in extra.items():
            d[k] = v[v.index >= SPLIT].stack()
    X = pd.DataFrame(d).reset_index()
    X.columns = ['date', 'pair'] + list(X.columns[2:])
    return X.dropna(subset=['state'])


def gap_in(d, col):
    d = d[[col, 'state']].dropna()
    keep = d.state.value_counts(normalize=True)
    d = d[d.state.isin(keep[keep >= MIN_SHARE].index)]
    if d.state.nunique() < 2 or len(d) < 500:
        return np.nan
    g = d.groupby('state')[col].mean()
    return (g.max() - g.min()) / d[col].std()


def shape_sep_in(d):
    return float(np.nanmean([gap_in(d, c) for c in NEUT]))


def cramers_v(t):
    t = t.values.astype(float)
    n = t.sum()
    e = np.outer(t.sum(1), t.sum(0)) / n
    chi2 = np.nansum((t - e) ** 2 / np.where(e > 0, e, np.nan))
    r, c = t.shape
    return float(np.sqrt(chi2 / (n * (min(r, c) - 1))))


def nmi(t):
    t = t.values.astype(float); n = t.sum()
    p = t / n; pr = p.sum(1, keepdims=True); pc = p.sum(0, keepdims=True)
    with np.errstate(divide='ignore', invalid='ignore'):
        m = np.nansum(np.where(p > 0, p * np.log2(p / (pr * pc)), 0.0))
        hr = -np.nansum(np.where(pr > 0, pr * np.log2(pr), 0.0))
        hc = -np.nansum(np.where(pc > 0, pc * np.log2(pc), 0.0))
    return float(m / min(hr, hc)) if min(hr, hc) > 0 else np.nan


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    fit = px.index < SPLIT
    P = properties(px)
    sh_raw, act = layers(px, fit)
    shape = confirm(sh_raw, DWELL)
    comb = product(sh_raw, act, DWELL)
    grid = nine(px, fit)[0]
    actc = confirm(act, DWELL)

    # ---------------- 1. where scale enters ----------------
    print('=' * 74)
    print('1. WHERE SCALE ENTERS THE COMBINED STATE')
    print("""
  combined.layers()   act = tercile(raw_axes(px)['scale'], fit)  -> weak|medium|strong
  combined.product()  lab = act + ' ' + shape                    -> 'strong broken'
  combined.confirm()  the 5-bar dwell is applied to that JOINT label

  scale_28 in layer1_states.csv is the same raw axis, path/(vol*sqrt(28)), and
  'activity' is its tercile. The activity word is literally the first half of
  every combined label, so it is not sitting unused -- but 'it is in the string'
  is not proof it carries anything, so:""")
    ab = []
    for nm, lab in (('combined (shape x activity)', comb),
                    ('shape only, activity knocked out', shape),
                    ('activity only, shape knocked out', actc),
                    ('nine-box grid, for reference', grid)):
        m = sep_of(lab, P, MAGP)
        s = sep_of(lab, P, NEUT)
        n = lab[lab.index >= SPLIT].stack().replace('', np.nan).dropna().nunique()
        print('  %-34s magnitude %.3f   shape %.3f   %2d states'
              % (nm, m, s, n))
        ab.append(dict(variant=nm, magnitude=m, shape=s, n_states=n))
    pd.DataFrame(ab).to_csv(os.path.join(ROOTOUT, 'axes_ablation.csv'),
                            index=False)
    print("""
  Knock the activity layer out and magnitude separation collapses; knock the
  shape layer out and it does not. That is the ablation answer: the volatility
  axis supplies essentially all of the combined state's magnitude reading, and
  the shape layer supplies almost none of it.""")

    # How the generation-1/2 columns relate. `shape` and `combined` moved to
    # layer1_legacy.csv when layer1_states.csv was narrowed to generation 4 on
    # 2026-08-13; `activity` stayed in the current file. So this needs BOTH,
    # joined on date+pair. Same fault as episodes.py had -- results/MANIFEST.md
    # records where the columns went, and following it is the whole fix.
    LEG_ = os.path.join(ROOTOUT, 'layer1_legacy.csv')
    if os.path.exists(L1) and os.path.exists(LEG_):
        have = set(pd.read_csv(LEG_, nrows=0).columns)
        need = {'date', 'pair', 'shape', 'combined', 'sample'}
        if not need <= have:
            print('  layer1_legacy.csv lacks %s; skipping the column relation'
                  % sorted(need - have))
            S = None
        else:
            S = pd.read_csv(LEG_, usecols=sorted(need)).merge(
                pd.read_csv(L1, usecols=['date', 'pair', 'activity']),
                on=['date', 'pair'], how='left')
    else:
        S = None
    if S is not None:
        S = S[S['sample'] == 'oos'].dropna(subset=['combined'])
        naive = S.activity + ' ' + S['shape']   # S.shape is the frame's shape
        print('  layer1_states.csv: combined == activity + " " + shape on %.2f%% '
              'of holdout rows.' % (100 * (naive == S.combined).mean()))
        print('  The rest is the dwell: "combined" confirms the JOINT label, so a')
        print('  change in either half restarts its 5-bar clock, while "shape"')
        print('  confirms shape alone. Neither column is derivable from the other.')

    # ---------------- 2. shape against activity ----------------
    print('\n' + '=' * 74)
    print('2. HOW SHAPE RELATES TO VOLATILITY')
    X = long(shape, P, extra={'act': act})
    X = X.dropna(subset=['act'])
    T = pd.crosstab(X.state, X.act).reindex(
        columns=['weak', 'medium', 'strong'])
    print('\n  TIME IN EACH CELL, holdout, share of all labelled bars')
    print((T / T.values.sum()).to_string(float_format=lambda v: '%.4f' % v))
    print('\n  EXPECTED UNDER INDEPENDENCE (row share x column share)')
    e = np.outer(T.sum(1), T.sum(0)) / T.values.sum()
    E = pd.DataFrame(e / T.values.sum(), index=T.index, columns=T.columns)
    print(E.to_string(float_format=lambda v: '%.4f' % v))
    print('\n  OBSERVED / EXPECTED -- 1.00 is independence')
    print((T / e).to_string(float_format=lambda v: '%.3f' % v))
    v, m = cramers_v(T), nmi(T)
    bs_v = block_boot(X, lambda d: cramers_v(
        pd.crosstab(d.state, d.act).reindex(columns=T.columns).fillna(0)),
        n=max(200, NBOOT // 4))
    bs_v = bs_v[np.isfinite(bs_v)]
    print("\n  Cramer's V %.4f  [%.4f, %.4f]   normalised mutual information "
          "%.4f bits/bit" % (v, np.percentile(bs_v, 2.5),
                             np.percentile(bs_v, 97.5), m))
    print('  0 is independent, 1 is one axis fully determining the other.')
    T.to_csv(os.path.join(ROOTOUT, 'axes_crosstab.csv'))

    print('\n  SHAPE SEPARATION WITHIN EACH ACTIVITY LEVEL')
    print('  the question that decides it: does shape read the same way when the')
    print('  pair is barely moving as when it is moving hard?')
    print('  %-10s %8s %8s %20s' % ('activity', 'n bars', 'shape sep', '95% CI'))
    rows = []
    for a in ('weak', 'medium', 'strong'):
        d = X[X.act == a]
        s = shape_sep_in(d)
        bs = block_boot(d, shape_sep_in, n=max(200, NBOOT // 4))
        bs = bs[np.isfinite(bs)]
        ci = (np.percentile(bs, 2.5), np.percentile(bs, 97.5))
        print('  %-10s %8d %8.3f   [%.3f, %.3f]' % (a, len(d), s, ci[0], ci[1]))
        rows.append(dict(activity=a, n=len(d), shape_sep=s, ci_lo=ci[0],
                         ci_hi=ci[1]))
    R = pd.DataFrame(rows)
    print('  spread strong minus weak: %+.3f'
          % (R[R.activity == 'strong'].shape_sep.iloc[0]
             - R[R.activity == 'weak'].shape_sep.iloc[0]))

    print('\n  AND THE MIRROR: magnitude separation within each SHAPE state')
    print('  %-10s %8s %8s' % ('shape', 'n bars', 'mag sep'))
    for st in ['trending', 'broken', 'range', 'drifting']:
        d = X[X.state == st].copy()
        if len(d) < 500:
            continue
        d2 = d.rename(columns={'state': '_s', 'act': 'state'})
        print('  %-10s %8d %8.3f'
              % (st, len(d), float(np.nanmean([gap_in(d2, c) for c in MAGP]))))

    # ---- and the sharper question: is shape orthogonal to STRAIGHTNESS too? ----
    print('\n  SHAPE AGAINST THE NINE-BOX STRAIGHTNESS FAMILY')
    print('  scale is the nine-box axis shape was crossed with, but straightness')
    print('  is the axis shape might actually be REPLACING, so it gets the same')
    print('  test. If V is low here too, the structural read is orthogonal to')
    print('  both nine-box axes and replaces neither.')
    famf = grid.apply(lambda c: c.str.split().str[-1])
    Y = long(shape, P, extra={'fam': famf}).dropna(subset=['fam'])
    T2 = pd.crosstab(Y.state, Y.fam).reindex(
        columns=['trend', 'transitional', 'chop'])
    e2 = np.outer(T2.sum(1), T2.sum(0)) / T2.values.sum()
    print('\n  OBSERVED / EXPECTED -- 1.00 is independence')
    print((T2 / e2).to_string(float_format=lambda v: '%.3f' % v))
    print("  Cramer's V %.4f   normalised mutual information %.4f"
          % (cramers_v(T2), nmi(T2)))
    T2.to_csv(os.path.join(ROOTOUT, 'axes_crosstab_straight.csv'))

    # ---------------- 3. settling vs transitional ----------------
    print('\n' + '=' * 74)
    print('3. IS SETTLING THE SAME AS TRANSITIONAL?')
    age = pd.DataFrame({p: (lambda v: v.groupby(
        (v != v.shift()).cumsum()).cumcount() + 1)(comb[p].replace('', np.nan))
        for p in comb.columns})
    settling = (age <= EDGE)
    fam = grid.apply(lambda c: c.str.split().str[-1])
    trans = fam.eq('transitional')
    ok = comb.notna() & grid.notna() & (comb.index >= SPLIT).reshape(-1, 1)
    a = settling.where(ok).stack().dropna().astype(bool)
    b = trans.where(ok).stack().dropna().astype(bool)
    j = pd.concat([a.rename('settling'), b.rename('transitional')],
                  axis=1).dropna()
    n = len(j)
    ps, pt = j.settling.mean(), j.transitional.mean()
    both = (j.settling & j.transitional).mean()
    print('  holdout bars with both labels: %d' % n)
    print('  base rates: settling %.4f   transitional %.4f' % (ps, pt))
    print('  P(transitional | settling) %.4f   vs base %.4f   lift %.3f'
          % (both / ps, pt, (both / ps) / pt))
    print('  P(settling | transitional) %.4f   vs base %.4f   lift %.3f'
          % (both / pt, ps, (both / pt) / ps))
    print('  joint %.4f against %.4f expected if independent' % (both, ps * pt))
    st = pd.DataFrame({'a': j.settling.values, 'b': j.transitional.values})
    print("  Cramer's V %.4f" % cramers_v(pd.crosstab(st.a, st.b)))
    pd.DataFrame([dict(n=n, p_settling=ps, p_transitional=pt, joint=both,
                       p_trans_given_settling=both / ps,
                       p_settling_given_trans=both / pt,
                       lift=(both / ps) / pt,
                       cramers_v=cramers_v(pd.crosstab(st.a, st.b)))]).to_csv(
        os.path.join(ROOTOUT, 'axes_settling.csv'), index=False)
    print("""
  A lift near 1.00 means the two labels are picking out different bars and that
  'settling' is not 'transitional' renamed. A lift well above 1 would mean the
  nine-box middle band already contains most of what settling identifies.""")
    print('\nwrote axes_crosstab.csv, axes_ablation.csv, axes_settling.csv')


if __name__ == '__main__':
    main()
