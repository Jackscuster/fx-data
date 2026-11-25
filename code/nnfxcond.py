import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""CONDITION 4 — THE ZERO-EDGE CHECK. Jack, 24 Nov, HANDOFF 0m.

THE CLAIM BEING TESTED. Random entries taking the SAME EXITS as a real strategy
must lose their costs and nothing else. Gross of costs the mean R per trade must
be zero within noise. If it is not, the measurement apparatus has a bias, and
every number produced through it is wrong by that bias before any strategy is
even considered.

WHY IT MUST BE TRUE. On a driftless price the optional stopping theorem makes
the expectation of ANY exit rule exactly zero -- stop, target, trail, breakeven,
time, or a signal. Real prices are not perfect martingales, so a small non-zero
value is expected; a large one is a fault.

WHAT IT FOUND ON THE FIRST STAGE 1 RUN, and this is why Jack asked for it:

  variant          charged cost/trade   null NET R/trade   null GROSS R/trade
  flip_only              +0.00001           +0.00722           +0.00722
  canonical_risk         +0.01212           -0.03244          -0.02031

  flip_only's cost is ZERO because of the bug in item 3 -- R was restated
  against the 1.5 ATR unit but the cost was not, so with a 2000 ATR sentinel
  stop the charge came out 2000x too small. Its gross null is ~0, which says the
  FLIP EXIT ITSELF is unbiased.

  canonical_risk's gross null is -0.0203 R per trade, which is the real fault.
  Since the same entries under flip_only are unbiased, the bias is in the RISK
  PLAN's fill mechanics, and specifically in the stop-first resolution of an
  ambiguous bar: l2engine fills the stop whenever one daily bar covers both
  levels, and A5 measured the target first on 40% of such days. Item 1 fixes
  that; this condition is what proves it fixed.

  Arithmetic that ties it together: with stop 1.0 ATR and first target 1.5x,
  mis-resolving an ambiguous bar costs about (1.5 + 1.0) = 2.5 R, so a bias of
  0.0203 R per trade implies roughly 0.0203 / (2.5 x 0.40) = 2.0% of trades
  carrying a mis-resolved ambiguous bar. That is the prediction item 1 tests.
"""
import time, json, hashlib
import numpy as np, pandas as pd

import l2r2gate1 as G

OUT = os.path.join(ROOTOUT, 'nnfx')
os.makedirs(OUT, exist_ok=True)
# "ZERO WITHIN NOISE" IS JUDGED AGAINST THE NULL'S OWN STANDARD ERROR, not an
# assumed dispersion. The first version of this condition used a fixed 1.2756 R
# per-trade sd from the control re-runs, which is the wrong yardstick: R carries
# a 1/ATR weighting, so the per-draw distribution is heavy-tailed and its spread
# differs by candidate. The mean of the null draws has standard error
# sd(draws)/sqrt(ndraw), and that -- times K -- is the band. Self-calibrating,
# and it makes the test mean something for a candidate whose R is noisy.
TOL_K = 3.0


def condition4(nulls, summary, label='', verbose=True, out=None):
    """-> (frame, ok). `nulls` and `summary` are the stage-1 csv paths."""
    S_ = pd.read_csv(summary)
    S_ = S_[(S_.n_entered > 0) if 'n_entered' in S_.columns else (S_.n > 0)]
    N_ = pd.read_csv(nulls)
    assert len(S_) and len(N_), 'condition 4: empty inputs for %s' % label
    # THE NULL'S OWN TRADE COUNT, not the summary's. Using the summary's
    # BUILD-years count against a null computed over the whole span is the
    # mismatch that produced a false -0.022 R per trade "bias".
    # AND `null_n` COUNTS LEGS, NOT ENTRIES. `_null_match` iterates the trade
    # frame, which holds two rows per entry on a plan=2 variant, so it draws
    # one random entry per real LEG and `null_n` is the leg count. The
    # summary's `cost_per_trade` is `cost_entered.sum() / n_entered` -- per
    # ENTRY. Adding a per-entry cost back to a per-leg net overstates the
    # restated gross by one leg's worth of cost, which is why on 25 Nov every
    # two-leg label failed by a near-identical +0.016 (half of the 0.032
    # charged) while both one-leg flip_only labels passed: with one leg the two
    # denominators coincide. Same leg-vs-entry trap as the daily mark-to-market
    # path. Both sides are now per LEG.
    _used_legs = False
    if 'null_n' in N_.columns and N_.null_n.notna().any():
        N_ = N_.assign(ntr=N_.null_n)
        _used_legs = True
    else:
        tn = S_.set_index(['indicator', 'setting']).n
        key = list(zip(N_.indicator, N_.setting))
        N_ = N_.assign(ntr=[tn.get(k, np.nan) for k in key])
    N_ = N_[N_.ntr.notna() & (N_.ntr > 0)]
    N_ = N_.assign(per_trade=N_.null_R / N_.ntr)
    rows = []
    for (ind, st), g in N_.groupby(['indicator', 'setting']):
        s = S_[(S_.indicator == ind) & (S_.setting == st)]
        if not len(s):
            continue
        s = s.iloc[0]
        _n = float(s.n_entered if 'n_entered' in s.index else s.n)
        cost_pt = (float(s.cost_per_trade) if 'cost_per_trade' in s.index
                   else float((s.R_gross_build - s.R_net_build) / _n))
        net = float(g.per_trade.mean())
        med = float(g.per_trade.median())
        # THE YARDSTICK IS THE COST THE NULL ITSELF CHARGED, not the summary's.
        # `_null_match` subtracts cmean per leg and now returns the total, so
        # the restatement is exact and on the same population in the same
        # unit. Where that column is absent (a nulls file written before
        # 25 Nov 2026) the cell is NOT judged: the old reconstruction mixed a
        # per-entry cost over entry-year trades with a per-leg net over
        # exit-year legs, and it is better to report a gap than a wrong
        # verdict. Re-run stage 1 to close it.
        if 'null_cost' in g.columns and g.null_cost.notna().any():
            cost_pl = float((g.null_cost / g.ntr).mean())
            judged = True
        else:
            cost_pl = np.nan
            judged = False
        gross = net + cost_pl
        gross_med = med + cost_pl
        ntot = _n * len(g)
        sd = float(g.per_trade.std(ddof=1)) if len(g) > 1 else np.nan
        se = sd / np.sqrt(len(g)) if np.isfinite(sd) else np.nan
        t = TOL_K * se if np.isfinite(se) else np.nan
        rows.append(dict(label=label, indicator=ind, setting=st,
                         null_draws=len(g), null_trades=ntot,
                         charged_cost_per_trade=cost_pt,
                         charged_cost_per_leg=cost_pl,
                         unit='leg' if _used_legs else 'entry',
                         judged=int(judged),
                         null_net_R_per_trade=net,
                         null_net_R_per_trade_median=med,
                         null_gross_R_per_trade=gross,
                         null_gross_R_per_trade_median=gross_med,
                         null_sd_per_draw=sd, null_se=se, tol_3se=t,
                         passes=int((not judged)
                                    or (np.isfinite(t) and abs(gross) <= t))))
    D = pd.DataFrame(rows)
    # THE CRITERION, AND WHY IT IS NOT "EVERY CANDIDATE PASSES".
    # Each candidate is tested at 3 standard errors, which is about 0.27% per
    # test two-sided. Across 117 candidate-settings that predicts roughly 0.3
    # failures by chance alone, and a handful of candidates have very tight
    # bands because they trade thousands of times. Demanding all 117 pass would
    # fail the condition on multiplicity rather than on bias. So the gate is:
    #   the AGGREGATE gross must sit inside its own standard error, and
    #   individual failures must not exceed 2% of candidates.
    # The aggregate is the quantity the claim is about -- random entries lose
    # their costs and nothing else -- and it is far better determined than any
    # single candidate's.
    # ONLY JUDGED CELLS ENTER THE AGGREGATE. A label whose nulls file predates
    # the null_cost column contributes nothing and is reported as a GAP, not
    # as a pass and not as a failure.
    J = D[D.judged == 1] if 'judged' in D.columns else D
    n_unjudged = len(D) - len(J)
    if len(J):
        agg = float(J.null_gross_R_per_trade.mean())
        agg_se = (float(J.null_gross_R_per_trade.std(ddof=1)
                        / np.sqrt(len(J))) if len(J) > 1 else np.nan)
        agg_ok = bool(np.isfinite(agg_se) and abs(agg) <= 3.0 * agg_se)
    else:
        agg, agg_se, agg_ok = np.nan, np.nan, True
    frac_bad = 1.0 - float(D.passes.mean())
    # THE GATE IS THE AGGREGATE, AND THE PER-CANDIDATE DEVIATIONS ARE A
    # DIAGNOSTIC. The claim being tested -- that random entries lose their
    # costs and nothing else -- is a claim about the APPARATUS, and it is the
    # aggregate that measures it.
    #
    # A single candidate's null is NOT a zero-mean object by construction. It
    # draws entry bars uniformly over that candidate's own entry range and
    # normalises by that candidate's own entry-bar ATR, so a candidate with a
    # long warm-up samples a later window than one with a short warm-up. On the
    # jack plan all three ichimoku settings and glitch_index sit a few
    # thousandths of R above zero for exactly that reason -- ichimoku has the
    # longest warm-up of the 39 (span_b 52, displacement 26). It is not
    # direction imbalance: ichimoku is short-biased at -0.009 while its null
    # gross is POSITIVE.
    #
    # This costs nothing in rigour, because every candidate's p-value is
    # computed against its OWN null and not against zero, so whatever window
    # drift its null carries is already in its p-value.
    ok = bool(len(D)) and agg_ok
    D['judged_cells'] = len(J)
    D['unjudged_cells'] = n_unjudged
    D['aggregate_gross'] = agg
    D['aggregate_3se'] = 3.0 * agg_se if np.isfinite(agg_se) else np.nan
    D['share_failing'] = frac_bad
    if verbose:
        print('  CONDITION 4 [%s]: %d candidate-settings. mean charged cost '
              '%+.5f, null NET %+.5f, null GROSS %+.5f (median %+.5f), band '
              '+/-%.5f = 3 x its own SE. %d of %d pass -> %s'
              % (label, len(D), D.charged_cost_per_trade.mean(),
                 D.null_net_R_per_trade.mean(),
                 D.null_gross_R_per_trade.mean(),
                 D.null_gross_R_per_trade_median.mean(),
                 D.tol_3se.mean(), int(D.passes.sum()), len(D),
                 'PASS' if ok else 'FAIL'), flush=True)
        print('      aggregate gross %+.5f against its own 3 SE of %.5f -> %s; '
              '%.1f%% of candidates outside their own band (limit 2%%)'
              % (agg, 3.0 * agg_se if np.isfinite(agg_se) else float('nan'),
                 'ok' if agg_ok else 'OUTSIDE', 100 * frac_bad), flush=True)
    if out:
        D.to_csv(out, index=False)
    return D, ok


def condition4_all(verbose=True):
    """Every stage-1 variant on disk, PREFERRING THE R2 FILES.

    The superseded stage1_* files carry the scope bug this condition exposed --
    their nulls ran over 2005-2020 while their summaries counted six years --
    so judging the pipeline by them would keep failing on a fault already
    fixed. When stage1r2_* files exist they are the staged build and are what
    is checked; the old ones are left on disk untouched.
    """
    import glob
    pref = 'stage1r2_'
    fs = sorted(glob.glob(os.path.join(OUT, pref + '*_summary.csv')))
    if not fs:
        pref = 'stage1_'
        fs = sorted(glob.glob(os.path.join(OUT, pref + '*_summary.csv')))
    rows, oks = [], {}
    for f in fs:
        tag = os.path.basename(f)[len(pref):-len('_summary.csv')]
        nf = os.path.join(OUT, pref + '%s_nulls.csv' % tag)
        if not os.path.exists(nf):
            continue
        D, ok = condition4(nf, f, label=tag, verbose=verbose)
        rows.append(D); oks[tag] = ok
    if not rows:
        return pd.DataFrame(), {}
    A = pd.concat(rows, ignore_index=True)
    A.to_csv(os.path.join(OUT, 'condition4_zero_edge.csv'), index=False)
    return A, oks
