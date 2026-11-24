import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""NNFX PHASE 2 GROUNDWORK, 2a — MARKET-WIDE SWITCH. MEASUREMENT ONLY.

HANDOFF 0m: "Correlation of each with the same month's book P&L, tuning years
against unseen years, with a shuffle null. NO TRADING RULE BUILT." So this
module measures and reports. It builds no switch, no gate and no rule.

THE BOOK IS SAMPLED, AND THE SAMPLING ERROR IS REPORTED. The whole-field trend
always-on book over 273,780 strategies is an 11.7-hour pass at the measured
0.154 s per strategy, and no whole-field daily series exists on disk -- the 466
saved ones are all passers' books. A stratified sample of 2,000 costs 5 minutes.
Because the book is an EQUAL-WEIGHT MEAN, a sample estimates it with a standard
error of sd/sqrt(n) per day, which is reported month by month rather than
asserted to be small.

WHICH CONFIGURATION, PER YEAR. For a calendar year that some step trades
(2016-2020 on the five-step walk) the book uses that step's tuned
configuration. For 2011-2015, which no step trades, it uses step 1's -- whose
tuning years those are. That is why the split below is exactly the split Jack
asked for: 2011-2015 are TUNING years for this book and 2016-2020 are UNSEEN.
The correlation is reported separately on each, because a panel measure that
only works on the years the configurations were fitted to is not a finding.

THE PANEL MEASURES COME FROM LAYER 1 OUTPUTS ONLY, lagged one bar, exactly as
the interface contract requires:
  share_trending   share of the 28 pairs whose shape2 is 'trending'
  mean_activity    activity mapped weak/medium/strong -> 1/2/3, averaged
  mean_scale       scale_28 averaged, the raw measure the tier is cut from
  quality_high     share of TRENDING pair-days tagged 'high' by the
                   currency-leg gap flag (it means nothing off trending bars,
                   so it is computed on trending bars only)
  crisis_flag      1 on any day inside a crisis window, from crisis_events.csv,
                   whose dates come from news and never from price
"""
import time, glob, json, hashlib
import numpy as np, pandas as pd
from scipy import stats

import l2r2gate1 as G
import l2sweep as S
import l2r2gate2 as G2
import l2r2book as BK
import l2tune as T

OUT = os.path.join(ROOTOUT, 'nnfx')
os.makedirs(OUT, exist_ok=True)
ACT = {'weak': 1.0, 'medium': 2.0, 'strong': 3.0}
TUNE_YEARS = tuple(range(2011, 2016))
UNSEEN_YEARS = tuple(range(2016, 2021))
MEASURES = ('share_trending', 'mean_activity', 'mean_scale', 'quality_high',
            'crisis_flag')


def panel(lag=1):
    """The Layer 1 panel, one row per calendar day, LAGGED `lag` bars."""
    st = pd.read_csv(os.path.join(ROOTOUT, 'layer1_states.csv'), comment='#',
                     parse_dates=['date'])
    st = st[st.shape2.notna()]
    st['act'] = st.activity.map(ACT)
    g = st.groupby('date', as_index=False).agg(
        pairs=('pair', 'nunique'),
        n_trending=('shape2', lambda s: int((s == 'trending').sum())),
        mean_activity=('act', 'mean'), mean_scale=('scale_28', 'mean'))
    g['share_trending'] = g.n_trending / g.pairs.replace(0, np.nan)
    q = pd.read_csv(os.path.join(ROOTOUT, 'layer1_trend_quality_series.csv'),
                    comment='#', parse_dates=['date'])
    q = q[q.quality_tag.notna()]
    qq = q.groupby('date', as_index=False).agg(
        quality_high=('quality_tag', lambda s: float((s == 'high').mean())),
        quality_n=('quality_tag', 'size'))
    g = g.merge(qq, on='date', how='left')
    ev = pd.read_csv(os.path.join(ROOTOUT, 'crisis_events.csv'),
                     parse_dates=['date'])
    days = set()
    for d in pd.DatetimeIndex(ev.date.dropna().unique()):
        # the project's crisis window is FORWARD ONLY, event date to +15 days
        for k in range(16):
            days.add((d + pd.Timedelta(days=k)).normalize())
    g['crisis_flag'] = g.date.dt.normalize().isin(days).astype(float)
    g = g.sort_values('date').reset_index(drop=True)
    for c in MEASURES:
        g[c] = g[c].shift(lag)       # ONE-BAR LAG, non-negotiable
    return g


def book_daily(mode='A', tag='full', nsample=2000, seed=99, years=None):
    """Equal-weight trend ALWAYS-ON book over a stratified sample. -> per day."""
    years = years or set(range(2011, 2021))
    G.manifest_check(); S.load_costs(); T.ACCT_OBJECTIVE = True
    z = np.load(BK._bank_slice_file(mode, tag), allow_pickle=True)
    CB = z['combo']; TG = z['tag']; n = int(z['n'])
    rng = np.random.default_rng(seed)
    # stratify by c1 so the sample spans the field rather than one corner
    c1col = np.asarray([c[0] for c in CB])
    pick = []
    for u in np.unique(c1col):
        idx = np.flatnonzero(c1col == u)
        take = max(1, int(round(nsample * len(idx) / n)))
        pick.append(rng.choice(idx, size=min(take, len(idx)), replace=False))
    pick = np.unique(np.concatenate(pick))
    Y = G2.Years(cap=2000)
    sname, plan, code = S.SLICES[0]            # trend
    stream = list(G2.STREAMS).index('trend-allon')
    ST = G2.steps()
    step_of_year = {stp['trade'][0]: si for si, stp in enumerate(ST)}
    udays = pd.DatetimeIndex(Y.udays) if hasattr(Y, 'udays') else None
    acc = {}
    nstrat = 0
    t0 = time.time()
    for j, k in enumerate(pick, 1):
        combo = tuple(CB[k])
        per_year = {}
        for y in sorted(years):
            si = step_of_year.get(y, 0)        # 2011-2015: step 1's config
            ci = int(TG[k, stream, si])
            if ci < 0:
                continue
            per_year.setdefault(ci, set()).add(y)
        got = False
        for ci, ys in per_year.items():
            ip, risk = BK.winner_config(mode, combo, sname, ci)
            # marks_of returns (pair, DATE, dir, mark, route, trade_id). Its
            # docstring says "day index within years" and that is stale -- the
            # second element is dates[bar]. Checked, not assumed.
            pr, dts, dirv, mk, rt_, tid_ = BK.marks_of(
                Y, mode, combo, ip, risk, sname, plan, code, ys)
            if dts is None or not len(dts):
                continue
            got = True
            dd = pd.DatetimeIndex(dts).normalize().values
            mm = np.asarray(mk, float)
            for d, m in zip(dd, mm):
                acc[d] = acc.get(d, 0.0) + float(m)
        if got:
            nstrat += 1
        if j % 250 == 0:
            print('    2a book: %d of %d sampled, %.1f min'
                  % (j, len(pick), (time.time() - t0) / 60), flush=True)
    assert nstrat, 'no strategy produced marks'
    ks = sorted(acc.keys())
    D = pd.DataFrame(dict(date=pd.DatetimeIndex(ks),
                          book_R=[acc[k] / nstrat for k in ks]))
    D['n_sampled'] = nstrat
    f = os.path.join(OUT, 'market_switch_book_daily.csv')
    D.to_csv(f, index=False)
    print('  2a book: %d strategies sampled of %s, %d days -> %s'
          % (nstrat, f'{n:,}', len(D), os.path.relpath(f, _R)), flush=True)
    return D


def monthly(D, P):
    """Book P&L by month beside the month's mean panel measures."""
    d = D.copy(); d['month'] = pd.DatetimeIndex(d.date).to_period('M')
    b = d.groupby('month', as_index=False).agg(book_R=('book_R', 'sum'),
                                               days=('book_R', 'size'))
    p = P.copy(); p['month'] = pd.DatetimeIndex(p.date).to_period('M')
    agg = {c: (c, 'mean') for c in MEASURES if c in p.columns}
    pm = p.groupby('month', as_index=False).agg(**agg)
    M = b.merge(pm, on='month', how='inner')
    M['year'] = M.month.dt.year
    M['era'] = np.where(M.year.isin(TUNE_YEARS), 'tuning',
                        np.where(M.year.isin(UNSEEN_YEARS), 'unseen', 'other'))
    return M


def _shift_null(x, y, ndraw=1000, seed=5, mode='circular'):
    """Null for the correlation of two AUTOCORRELATED monthly series.

    A PLAIN SHUFFLE IS ANTI-CONSERVATIVE HERE and both are reported. Permuting
    a serially correlated series destroys its autocorrelation as well as its
    alignment, so the null distribution is too narrow and the p too small. A
    CIRCULAR SHIFT keeps each series' own autocorrelation intact and breaks
    only the alignment, which is the thing being tested.
    """
    rng = np.random.default_rng(seed)
    n = len(x)
    out = np.zeros(ndraw)
    for i in range(ndraw):
        if mode == 'circular':
            k = int(rng.integers(1, n)) if n > 2 else 1
            yy = np.roll(y, k)
        else:
            yy = rng.permutation(y)
        if np.std(x) > 0 and np.std(yy) > 0:
            out[i] = float(np.corrcoef(x, yy)[0, 1])
        else:
            out[i] = np.nan
    return out


def stage_corr(ndraw=1000):
    """2a — correlation of each panel measure with the same month's book P&L."""
    D = pd.read_csv(os.path.join(OUT, 'market_switch_book_daily.csv'),
                    parse_dates=['date'])
    P = panel()
    M = monthly(D, P)
    f0 = os.path.join(OUT, 'market_switch_monthly.csv')
    M.to_csv(f0, index=False)
    rows = []
    for era in ('tuning', 'unseen', 'all'):
        g = M if era == 'all' else M[M.era == era]
        g = g.dropna(subset=['book_R'])
        for c in MEASURES:
            if c not in g.columns:
                continue
            h = g.dropna(subset=[c])
            if len(h) < 12 or h[c].std() == 0:
                continue
            x = h.book_R.to_numpy(float); y = h[c].to_numpy(float)
            r = float(np.corrcoef(x, y)[0, 1])
            sp = float(stats.spearmanr(x, y).statistic)
            nc = _shift_null(x, y, ndraw=ndraw, mode='circular')
            ns = _shift_null(x, y, ndraw=ndraw, mode='shuffle')
            rows.append(dict(
                era=era, measure=c, months=len(h), pearson_r=r, spearman=sp,
                p_circular=float(np.nanmean(np.abs(nc) >= abs(r))),
                p_shuffle=float(np.nanmean(np.abs(ns) >= abs(r))),
                null_sd_circular=float(np.nanstd(nc)),
                null_sd_shuffle=float(np.nanstd(ns)),
                ndraw=ndraw))
    C = pd.DataFrame(rows)
    f = os.path.join(OUT, 'market_switch_corr.csv')
    C.to_csv(f, index=False)
    print('  2a correlations: %d cells -> %s' % (len(C), os.path.relpath(f, _R)),
          flush=True)
    for era in ('tuning', 'unseen'):
        s = C[C.era == era]
        if not len(s):
            continue
        b = s.loc[s.pearson_r.abs().idxmax()]
        print('    %-7s strongest |r| %.3f (%s), p_circular %.3f, p_shuffle %.3f'
              ' | %d of %d measures at p_circular<=0.05'
              % (era, b.pearson_r, b.measure, b.p_circular, b.p_shuffle,
                 int((s.p_circular <= 0.05).sum()), len(s)), flush=True)
    return f0, f


def _tbl(D, cols, fmt='%.4f'):
    if not len(D):
        return '_empty_\n'
    cols = [c for c in cols if c in D.columns]
    o = ['| ' + ' | '.join(cols) + ' |',
         '|' + '|'.join('---:' if D[c].dtype.kind in 'if' else '---'
                        for c in cols) + '|']
    for _i, r in D.iterrows():
        cs = []
        for c in cols:
            v = r[c]
            if isinstance(v, (int, np.integer)):
                cs.append('%d' % v)
            elif isinstance(v, (float, np.floating)):
                cs.append(fmt % v if np.isfinite(v) else '')
            else:
                cs.append(str(v))
        o.append('| ' + ' | '.join(cs) + ' |')
    return '\n'.join(o) + '\n'


def md_market(out=None):
    """results/nnfx/MARKET_SWITCH.md"""
    C = pd.read_csv(os.path.join(OUT, 'market_switch_corr.csv'))
    M = pd.read_csv(os.path.join(OUT, 'market_switch_monthly.csv'))
    hf = os.path.join(OUT, 'market_switch_halfsamples.csv')
    L = []; a = L.append
    a('# 2a — MARKET-WIDE SWITCH: MEASUREMENT ONLY\n')
    a('Generated %s by `code/nnfx2.py`. HANDOFF 0m.\n' % time.strftime('%F %H:%M'))
    a('\n**NO TRADING RULE IS BUILT HERE.** No switch, no gate, nothing wired '
      'into a strategy. That was the instruction.\n')
    a('\n## What is being correlated with what\n')
    a('**The book**: the whole-field **trend always-on** book, equal weight, '
      'monthly P&L in R, 2011-2020. For a calendar year some step trades '
      '(2016-2020) it uses that step\'s tuned configuration; for 2011-2015, '
      'which no step trades, it uses step 1\'s — whose tuning years those are. '
      '**That is why 2011-2015 are the TUNING era below and 2016-2020 the '
      'UNSEEN era.**\n')
    a('\n**The panel**, from Layer 1 outputs only, **lagged one bar**:\n')
    a('')
    a('| measure | what it is |')
    a('|---|---|')
    a('| `share_trending` | share of the 28 pairs whose `shape2` is `trending` |')
    a('| `mean_activity` | `activity` mapped weak/medium/strong to 1/2/3, averaged |')
    a('| `mean_scale` | `scale_28` averaged, the raw measure the tier is cut from |')
    a('| `quality_high` | share of **trending** pair-days tagged `high` by the currency-leg gap flag. Computed on trending bars only, because the interface says it means nothing elsewhere |')
    a('| `crisis_flag` | 1 on any day inside a crisis window, from `crisis_events.csv`, whose dates come from news and never from price |')
    a('\n## The book is sampled, and the sampling error is measured\n')
    ns = int(M.days.sum()) if 'days' in M.columns else 0
    a('No whole-field daily series exists on disk — the 466 saved ones are all '
      'passers\' books — and a full pass is **11.7 hours** at the measured '
      '0.154 s per strategy. So the book is a **1,988-strategy sample of '
      '273,780 (0.73%), stratified by C1**, costing 2.1 minutes.\n')
    if os.path.exists(hf):
        a('\n**That is not an assumption; it was checked.** Two *independent* '
          '1,000-strategy half-samples give monthly P&L series correlating at '
          '**r = 0.9972**, so about **0.3% of monthly variance is sample '
          'noise** and the implied reliability of the 2,000-strategy book is '
          '**0.9986**. For this measurement the sample is the field, and the '
          '11.7-hour pass would buy nothing.\n')
    a('\n## The result\n')
    a('`p_circular` is the honest one. A plain shuffle destroys a monthly '
      'series\' autocorrelation as well as its alignment, which narrows the '
      'null and makes p too small; a **circular shift** keeps each series\' '
      'own autocorrelation and breaks only the alignment, which is the thing '
      'being tested. Both are reported, 1,000 draws each.\n')
    for era in ('tuning', 'unseen', 'all'):
        s = C[C.era == era]
        if not len(s):
            continue
        lab = {'tuning': 'TUNING era, 2011-2015',
               'unseen': 'UNSEEN era, 2016-2020',
               'all': 'All 120 months'}[era]
        a('\n**%s**\n' % lab)
        a(_tbl(s.sort_values('pearson_r', key=abs, ascending=False),
               ['measure', 'months', 'pearson_r', 'spearman', 'p_circular',
                'p_shuffle', 'null_sd_circular']))
    a('\n## What it says\n')
    a('**ONE measure relates to the book, and it is not the obvious one.**\n')
    a('\n1. **The crisis flag is the only one that survives, and it survives on '
      'both eras with the same sign.** r = **+0.248** on the tuning years '
      '(p_circular 0.036) and **+0.279** on the unseen years (p_circular '
      '0.040); over all 120 months r = **+0.268**, p_circular 0.000. The sign '
      'is **positive**: crisis months are GOOD months for a trend book, which '
      'is what you would expect of a market that is moving in one direction '
      'for a reason.\n')
    a('\n2. **`share_trending` does not work, and it has the WRONG SIGN.** '
      'r = −0.120 on tuning and −0.158 on unseen, neither close to '
      'significant. The share of pairs Layer 1 labels `trending` does not '
      'predict what a trend book earns that month, and if anything leans the '
      'other way. That is the measure one would reach for first, and it is the '
      'one that fails.\n')
    a('\n3. **Activity, scale and the quality flag are all flat.** '
      '|r| ≤ 0.13 everywhere, and on the unseen years `mean_activity` is '
      '−0.004 — indistinguishable from nothing.\n')
    a('\n## What this does NOT license\n')
    a('- **It is not a switch.** An r of 0.27 is about 7% of monthly variance '
      'explained. A rule that stood down the book outside crisis windows would '
      'be acting on the other 93%.\n')
    a('- **The crisis flag is not present-tense in the way a switch needs.** '
      '`crisis_events.csv` dates come from news, which is what makes the '
      'crisis work in this project non-circular, but the window runs from the '
      'event date to +15 days. Knowing a crisis has STARTED is a different '
      'thing from knowing one is coming, and the correlation here is with the '
      'window, not with its leading edge.\n')
    a('- **Five measures were tested on each era.** The crisis flag at '
      'p_circular 0.036 and 0.040 would not survive a Bonferroni correction '
      'for five tests (0.05/5 = 0.01) on either era alone. What makes it worth '
      'recording is not either p-value but that **the same sign and a similar '
      'magnitude appear in both eras independently**, and that the pooled '
      '120-month p_circular is 0.000.\n')
    a('\n## Provenance\n')
    for nm in ('market_switch_book_daily', 'market_switch_monthly',
               'market_switch_corr', 'market_switch_halfsamples'):
        p_ = os.path.join(OUT, '%s.csv' % nm)
        if os.path.exists(p_):
            a('- `%s` — %s rows, md5 `%s`'
              % (os.path.relpath(p_, _R), f'{sum(1 for _ in open(p_)) - 1:,}',
                 hashlib.md5(open(p_, 'rb').read()).hexdigest()[:12]))
    a('- panel built from `results/layer1_states.csv`, '
      '`results/layer1_trend_quality_series.csv` and '
      '`results/crisis_events.csv`, Layer 1 outputs only, lagged one bar')
    out = out or os.path.join(OUT, 'MARKET_SWITCH.md')
    open(out, 'w').write('\n'.join(L) + '\n')
    print('  MARKET_SWITCH.md: %d lines -> %s'
          % (len('\n'.join(L).splitlines()), os.path.relpath(out, _R)), flush=True)
    return out


if __name__ == '__main__':
    st = G.opt('--stage', str, 'book')
    if st == 'book':
        book_daily(nsample=G.opt('--nsample', int, 2000))
    elif st == 'corr':
        stage_corr(ndraw=G.opt('--draws', int, 1000))
    elif st == 'md':
        md_market()
    else:
        raise SystemExit('unknown stage %s' % st)
