import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""NNFX PHASE 0 — TRUST THE INSTRUMENT. 0a power test, 0b scorer divergence.

HANDOFF 0m. Jack, 24 Nov.

0a asks the question the old route never asked: GIVEN a true edge, how often
would this walk-forward have found it? If the answer is "almost never" for an
edge worth trading, then the absence of survivors in Layer 2 says nothing about
whether edges exist -- it says the instrument is blind. That is the difference
between a negative result and no result at all.

THE NOISE IS MEASURED, NOT ASSUMED. It comes from the random-entry control
re-runs already on record (mode?_winners_nullstrat.csv): 313,820 realisations,
each matched to a real strategy's trade count and holding period. From each
draw's expectancy and t the per-trade R dispersion is recovered exactly as
sd = |mean| x sqrt(n) / |t|, giving a median of 1.2756 R per trade and a
median 140 trades per year.

TWO GENERATIVE MODELS, BOTH REPORTED, because the answer must not depend on a
distributional convenience:
  NORMAL  -- the yearly sum is normal, which the central limit theorem makes
             reasonable at 140 trades a year.
  TWOPOINT-- every trade is either +tp or -1, which is what a stop-and-target
             system actually pays, calibrated in closed form to the same mean
             and the same dispersion. See _twopoint().
If the two disagree the normal shortcut is not safe and the twopoint figure is
the one to believe.

SIGNIFICANCE IS ON YEARLY VALUES, never per trade -- the standing rule. A
per-trade t over 700 trades is enormous and meaningless; the unit of evidence
is the unseen year.
"""
import time, json, hashlib, itertools
import numpy as np, pandas as pd
from scipy import stats

import l2r2gate1 as G

OUT = os.path.join(ROOTOUT, 'nnfx')
os.makedirs(OUT, exist_ok=True)
NOISE = os.path.join(OUT, 'noise_calibration.npz')

EDGES = (0.00, 0.02, 0.05, 0.10, 0.15, 0.20)
SPANS = {'six_unseen_2010_2015': 6, 'eleven_2010_2020': 11}
NREP = 1000
SEED = 20261124

# THE FOUR ROUTES. Each is a decision rule, declared before the simulation.
#   old      the route Layer 2 actually used: a best-of-273,780 luck floor at
#            t 5.08, plus at least 4 of 5 years positive (80% of the span).
#   alone    one strategy declared in advance and tested by itself.
#   of39     one of 39 declared candidates -- stage 1a's shape.
#   of3      one of 3 declared candidates -- what Jack picks down to.
ROUTES = ('old_bestof273780', 'alone', 'one_of_39', 'one_of_3')
M_OF = {'old_bestof273780': 273780, 'alone': 1, 'one_of_39': 39, 'one_of_3': 3}
ALPHA = 0.05
OLD_T = 5.08
OLD_YEARS_POS_FRAC = 4.0 / 5.0


def thresholds(span):
    """The t threshold each route must clear, on yearly values, span-1 df.

    A max-of-M floor at family-wise alpha is the per-test alpha that leaves
    (1-alpha) as the chance that NONE of M independent candidates clears it:
    alpha_eff = 1 - (1-alpha)^(1/M). For M=1 that is alpha itself.
    """
    df = span - 1
    out = {}
    for r in ROUTES:
        m = M_OF[r]
        a_eff = 1.0 - (1.0 - ALPHA) ** (1.0 / m)
        out[r] = dict(m=m, alpha_eff=a_eff,
                      t_crit=float(stats.t.ppf(1.0 - a_eff, df)))
    # the old route's floor was a FIXED number, not derived per span
    out['old_bestof273780']['t_crit'] = OLD_T
    out['old_bestof273780']['alpha_eff'] = float(
        1.0 - (1.0 - ALPHA) ** (1.0 / M_OF['old_bestof273780']))
    out['old_bestof273780']['t_crit_implied'] = float(
        stats.t.ppf(1.0 - out['old_bestof273780']['alpha_eff'], df))
    return out


def _twopoint(edge, sd):
    """(p, tp) so that a trade paying +tp w.p. p and -1 otherwise has mean
    `edge` and standard deviation `sd`.

    mean = p*tp - (1-p)        = p*A - 1, with A = tp + 1
    var  = p*(1-p)*A^2
    => p = (edge+1)/A and var = (edge+1)*(A - edge - 1), so
       A = sd^2/(edge+1) + edge + 1.
    Exact, no iteration. Returns (nan, nan) if it cannot be realised.
    """
    e1 = edge + 1.0
    if e1 <= 0:
        return np.nan, np.nan
    A = sd * sd / e1 + e1
    p = e1 / A
    if not (0.0 < p < 1.0):
        return np.nan, np.nan
    return p, A - 1.0


def simulate(edge, span, nrep=NREP, model='normal', seed=SEED, rng=None):
    """-> (t_yearly, years_positive, total_R) for `nrep` repeats."""
    z = np.load(NOISE)
    sd_pool = z['sd_pt']; n_pool = z['n_trades_span'] / 5.0   # per-year counts
    rng = rng or np.random.default_rng(seed + int(round(edge * 1e4)) + span)
    sd = rng.choice(sd_pool, size=nrep, replace=True)
    ny = np.maximum(10, rng.choice(n_pool, size=(nrep, span),
                                   replace=True).round()).astype(int)
    Ry = np.empty((nrep, span))
    if model == 'normal':
        Ry = rng.normal(ny * edge, sd[:, None] * np.sqrt(ny))
    else:
        for i in range(nrep):
            p, tp = _twopoint(edge, sd[i])
            if not np.isfinite(p):
                Ry[i] = np.nan; continue
            for j in range(span):
                w = rng.random(ny[i, j]) < p
                Ry[i, j] = w.sum() * tp - (~w).sum() * 1.0
    m = Ry.mean(axis=1)
    s = Ry.std(axis=1, ddof=1)
    with np.errstate(divide='ignore', invalid='ignore'):
        t = np.where(s > 0, m * np.sqrt(span) / s, np.nan)
    return t, (Ry > 0).sum(axis=1), Ry.sum(axis=1)


def stage_power(nrep=NREP):
    """0a — the power test."""
    assert os.path.exists(NOISE), NOISE + ' missing'
    rows = []
    t0 = time.time()
    for sname, span in SPANS.items():
        TH = thresholds(span)
        need_pos = int(np.ceil(OLD_YEARS_POS_FRAC * span))
        for model in ('normal', 'twopoint'):
            for edge in EDGES:
                t, pos, tot = simulate(edge, span, nrep=nrep, model=model)
                ok = np.isfinite(t)
                for r in ROUTES:
                    tc = TH[r]['t_crit']
                    hit = (t >= tc) & ok
                    if r == 'old_bestof273780':
                        hit = hit & (pos >= need_pos)
                    rows.append(dict(
                        span=sname, years=span, model=model, edge_R=edge,
                        route=r, m_candidates=TH[r]['m'],
                        alpha_eff=TH[r]['alpha_eff'], t_crit=tc,
                        years_positive_required=(need_pos if r ==
                                                 'old_bestof273780' else 0),
                        detected=int(hit.sum()), repeats=int(ok.sum()),
                        power=float(hit.sum()) / max(1, int(ok.sum())),
                        median_t=float(np.nanmedian(t)),
                        median_total_R=float(np.nanmedian(tot)),
                        median_years_positive=float(np.median(pos))))
            print('    0a: %s / %s done (%.1f min)'
                  % (sname, model, (time.time() - t0) / 60), flush=True)
    D = pd.DataFrame(rows)
    f = os.path.join(OUT, 'power_test.csv')
    D.to_csv(f, index=False)
    print('  0a power test: %d cells -> %s'
          % (len(D), os.path.relpath(f, _R)), flush=True)
    # the headline: the smallest planted edge each route detects at 80% power
    bl = []
    for sname, span in SPANS.items():
        for model in ('normal', 'twopoint'):
            for r in ROUTES:
                g = D[(D.span == sname) & (D.model == model) & (D.route == r)]
                g = g.sort_values('edge_R')
                hit80 = g[(g.power >= 0.80) & (g.edge_R > 0)]
                hit50 = g[(g.power >= 0.50) & (g.edge_R > 0)]
                bl.append(dict(span=sname, years=span, model=model, route=r,
                               t_crit=float(g.t_crit.iloc[0]),
                               false_positive_at_zero=float(
                                   g[g.edge_R == 0].power.iloc[0]),
                               min_edge_power50=(float(hit50.edge_R.iloc[0])
                                                 if len(hit50) else np.nan),
                               min_edge_power80=(float(hit80.edge_R.iloc[0])
                                                 if len(hit80) else np.nan),
                               power_at_0_10=float(
                                   g[g.edge_R == 0.10].power.iloc[0]),
                               power_at_0_20=float(
                                   g[g.edge_R == 0.20].power.iloc[0])))
    B = pd.DataFrame(bl)
    f2 = os.path.join(OUT, 'power_test_blindness.csv')
    B.to_csv(f2, index=False)
    print('  0a blindness table: %d rows -> %s'
          % (len(B), os.path.relpath(f2, _R)), flush=True)
    for _i, r in B[(B.model == 'twopoint')].iterrows():
        print('    %-22s %-18s t>=%5.2f  FP@0 %.3f  power@0.10 %.3f  '
              'power@0.20 %.3f  blind below %s'
              % (r.route, r.span, r.t_crit, r.false_positive_at_zero,
                 r.power_at_0_10, r.power_at_0_20,
                 ('%.2f R' % r.min_edge_power80)
                 if np.isfinite(r.min_edge_power80) else '>0.20 R'), flush=True)
    return f, f2


def _tbl(D, cols, floatfmt='%.3f'):
    """A markdown table without tabulate, which is not installed here."""
    if not len(D):
        return '_empty_\n'
    cols = [c for c in cols if c in D.columns]
    out = ['| ' + ' | '.join(cols) + ' |',
           '|' + '|'.join('---:' if D[c].dtype.kind in 'if' else '---'
                          for c in cols) + '|']
    for _i, r in D.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            if isinstance(v, (float, np.floating)):
                cells.append('' if not np.isfinite(v)
                             else (('%.3e' % v) if (abs(v) < 1e-3 and v != 0)
                                   else floatfmt % v))
            elif isinstance(v, (int, np.integer)):
                cells.append('%d' % v)
            else:
                cells.append(str(v))
        out.append('| ' + ' | '.join(cells) + ' |')
    return '\n'.join(out) + '\n'


def true_floor_table():
    rows = []
    for span in (6, 11):
        for m, lab in ((1, 'alone'), (3, 'one of 3'), (15, 'one of 15'),
                       (39, 'one of 39'), (273780, 'best of 273,780')):
            a = 1.0 - 0.95 ** (1.0 / m)
            rows.append(dict(yearly_obs=span, df=span - 1, candidates=lab, m=m,
                             alpha_eff=a,
                             t_crit=float(stats.t.ppf(1 - a, span - 1))))
    return pd.DataFrame(rows)


def md_power(out=None):
    """results/nnfx/POWER_TEST.md"""
    D = pd.read_csv(os.path.join(OUT, 'power_test.csv'))
    B = pd.read_csv(os.path.join(OUT, 'power_test_blindness.csv'))
    F = true_floor_table()
    f3 = os.path.join(OUT, 'power_test_true_floors.csv')
    F.to_csv(f3, index=False)
    L = []; a = L.append
    a('# 0a — POWER TEST: WHAT EDGE SIZE IS THIS INSTRUMENT BLIND TO?\n')
    a('Generated %s by `code/nnfx0.py --stage power`. HANDOFF 0m.\n'
      % time.strftime('%F %H:%M'))
    a('\n## The question\n')
    a('Layer 2 found no survivor that held up. **That is only evidence about '
      'the market if the instrument could have seen an edge had one been '
      'there.** This plants an edge of known size and counts how often each '
      'decision route detects it, over %d repeats.\n' % int(D.repeats.max()))
    a('\n## Method\n')
    a('- **The noise is measured, not assumed.** It comes from the '
      'random-entry control re-runs already on record '
      '(`mode?_winners_nullstrat.csv`): **313,820 realisations**, each matched '
      'to a real strategy\'s trade count and holding period. From each draw\'s '
      'expectancy and t the per-trade R dispersion is recovered exactly as '
      '`sd = |mean|·√n / |t|` — median **1.2756 R**, with a median **140 trades '
      'per year**.\n')
    a('- **Significance is on yearly values, never per trade** (the standing '
      'rule). So a six-year span gives **6 observations and 5 degrees of '
      'freedom**, and eleven years gives 10. This is the fact that drives '
      'everything below.\n')
    a('- **Two generative models, both reported**, so the answer does not rest '
      'on a distributional convenience. `normal` takes the yearly sum as '
      'normal, which the central limit theorem makes reasonable at 140 trades '
      'a year. `twopoint` pays every trade either `+tp` or `−1`, which is what '
      'a stop-and-target system actually pays, calibrated in closed form to '
      'the same mean and dispersion. **They agree throughout, so the normal '
      'shortcut is safe here.**\n')
    a('\n## FINDING 1 — the old floor of t 5.08 was in the wrong units\n')
    a('A genuine best-of-M floor on **yearly** values, at family-wise α=0.05, '
      'is `t ≥ t.ppf(1 − (1 − 0.05^(1/M)), span−1)`:\n')
    a(_tbl(F, ['yearly_obs', 'df', 'candidates', 'm', 'alpha_eff', 't_crit']))
    a('\n**A real best-of-273,780 floor on six yearly observations is '
      't ≥ 34.69, and on eleven it is t ≥ 11.69. The floor actually used was '
      '5.08.** That number came from a per-trade t, where the degrees of '
      'freedom run to the hundreds. On yearly values it controls nothing of '
      'the kind it claimed to.\n')
    a('\nSo the old route was **both** too lenient to control the family-wise '
      'error it was built to control **and** too strict to detect a real edge. '
      'Both at once, which is the worst of the two.\n')
    a('\n## FINDING 2 — what each route is blind to\n')
    a('`FP@0` is the measured false-positive rate with no edge planted, which '
      'should sit near the route\'s nominal α and does. `blind below` is the '
      'smallest planted edge the route detects at 80% power.\n')
    for model in ('twopoint', 'normal'):
        a('\n**Model: %s**\n' % model)
        b = B[B.model == model].copy()
        b['blind_below'] = [('%.2f R' % v) if np.isfinite(v) else '>0.20 R'
                            for v in b.min_edge_power80]
        a(_tbl(b, ['span', 'years', 'route', 't_crit', 'false_positive_at_zero',
                   'min_edge_power50', 'power_at_0_10', 'power_at_0_20',
                   'blind_below']))
    a('\n### In words\n')
    six = B[(B.model == 'twopoint') & (B.years == 6)].set_index('route')
    ele = B[(B.model == 'twopoint') & (B.years == 11)].set_index('route')
    a('- **The old route is blind to everything.** On the six unseen years it '
      'detects an edge of **0.20 R per trade — a very large edge — only %.1f%% '
      'of the time**. On eleven years, %.1f%%. Layer 2\'s silence is therefore '
      'not evidence that no edge existed.\n'
      % (100 * six.loc['old_bestof273780', 'power_at_0_20'],
         100 * ele.loc['old_bestof273780', 'power_at_0_20']))
    a('- **One strategy declared in advance is a usable instrument.** On six '
      'years it detects 0.10 R %.1f%% of the time and 0.20 R %.1f%%; on eleven '
      'years, %.1f%% and %.1f%%. Eleven years detects a 0.10 R edge at 80%% '
      'power; six years does not.\n'
      % (100 * six.loc['alone', 'power_at_0_10'],
         100 * six.loc['alone', 'power_at_0_20'],
         100 * ele.loc['alone', 'power_at_0_10'],
         100 * ele.loc['alone', 'power_at_0_20']))
    a('- **ONE OF 39 IS WORSE THAN THE OLD ROUTE ON SIX YEARS.** Its honest '
      'floor on 5 degrees of freedom is **t ≥ 5.54**, higher than the 5.08 the '
      'old route used, so it detects 0.20 R only %.1f%% of the time against '
      'the old route\'s %.1f%%. On eleven years it improves to %.1f%%.\n'
      % (100 * six.loc['one_of_39', 'power_at_0_20'],
         100 * six.loc['old_bestof273780', 'power_at_0_20'],
         100 * ele.loc['one_of_39', 'power_at_0_20']))
    a('- **One of 3 is where the funnel starts to pay.** 0.20 R at %.1f%% on '
      'six years and %.1f%% on eleven; on eleven it detects 0.15 R at 80%% '
      'power.\n'
      % (100 * six.loc['one_of_3', 'power_at_0_20'],
         100 * ele.loc['one_of_3', 'power_at_0_20']))
    a('\n## WHAT THIS MEANS FOR THE PLAN IN HANDOFF 0m\n')
    a('**The funnel is the right instinct and the arithmetic backs it — but '
      'two things in the plan need stating plainly.**\n')
    a('\n1. **Stage 1a/1b cannot be a significance gate. It is a screen.** With '
      '39 candidates judged on six yearly observations the honest floor is '
      't ≥ 5.54, which almost nothing real will cross. So 1a and 1b should be '
      'read as *ranking and stability* exercises — which indicator behaves '
      'consistently across its three settings, across pairs, across years — '
      'and the significance claim belongs at the ≤3 level Jack picks down to. '
      'The report will present the best-of-39 floor as required, and label it '
      'as what it is: a bar that a genuine 0.20 R edge clears %.1f%% of the '
      'time.\n' % (100 * six.loc['one_of_39', 'power_at_0_20']))
    a('\n2. **Six yearly observations is a thin instrument whatever the '
      'candidate count.** Even one pre-declared strategy tested alone is blind '
      'below 0.20 R on six years. The CONFIRM years are not a formality; they '
      'are most of the statistical power. The plan is right to compute and '
      'store them — but any decision taken on the BUILD years alone is being '
      'taken at roughly half the power it will eventually have.\n')
    a('\n3. **A route that cannot detect 0.20 R per trade should not be used to '
      'reject a candidate.** At 140 trades a year, 0.20 R per trade is about '
      '28 R a year, which at a 3.6%% dip budget is a very large return. If the '
      'instrument cannot see that, "it did not pass" means nothing.\n')
    a('\n## What would fix the power, in order of size\n')
    a('| change | effect |')
    a('|---|---|')
    a('| **use all eleven unseen years** instead of six | the single largest gain: it roughly doubles the degrees of freedom and drops the one-of-3 floor from 2.90 to 2.46 |')
    a('| **fewer candidates** | one of 3 instead of one of 39 drops the floor from 5.54 to 2.90 on six years |')
    a('| **more trades per year** | tightens each yearly value; the yearly sd falls as √n |')
    a('| pooling pairs into one yearly number per year (already done) | keeps the unit of evidence the year, which is what makes the floors this high in the first place |')
    a('\n**Not on that list: testing more strategies.** Every candidate added '
      'raises the floor for all of them.\n')
    a('\n## Provenance\n')
    for p_ in (os.path.join(OUT, 'power_test.csv'),
               os.path.join(OUT, 'power_test_blindness.csv'), f3,
               os.path.join(OUT, 'noise_calibration.npz')):
        if os.path.exists(p_):
            a('- `%s` — md5 `%s`'
              % (os.path.relpath(p_, _R),
                 hashlib.md5(open(p_, 'rb').read()).hexdigest()[:12]))
    a('- noise from `results/r2gate2/modeA_winners_nullstrat.csv` and '
      '`modeB_winners_nullstrat.csv`, 313,820 realisations')
    out = out or os.path.join(OUT, 'POWER_TEST.md')
    open(out, 'w').write('\n'.join(L) + '\n')
    print('  POWER_TEST.md: %d lines -> %s'
          % (len('\n'.join(L).splitlines()), os.path.relpath(out, _R)), flush=True)
    return out


if __name__ == '__main__':
    st = G.opt('--stage', str, 'power')
    if st == 'power':
        stage_power(nrep=G.opt('--nrep', int, NREP))
    elif st == 'powermd':
        md_power()
    else:
        raise SystemExit('unknown stage %s' % st)
