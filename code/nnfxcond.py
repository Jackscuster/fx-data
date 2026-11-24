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
    S_ = S_[S_.n > 0]
    N_ = pd.read_csv(nulls)
    assert len(S_) and len(N_), 'condition 4: empty inputs for %s' % label
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
        cost_pt = float((s.R_gross_build - s.R_net_build) / s.n)
        net = float(g.per_trade.mean())
        med = float(g.per_trade.median())
        gross = net + cost_pt
        gross_med = med + cost_pt
        ntot = float(s.n) * len(g)
        sd = float(g.per_trade.std(ddof=1)) if len(g) > 1 else np.nan
        se = sd / np.sqrt(len(g)) if np.isfinite(sd) else np.nan
        t = TOL_K * se if np.isfinite(se) else np.nan
        rows.append(dict(label=label, indicator=ind, setting=st,
                         null_draws=len(g), null_trades=ntot,
                         charged_cost_per_trade=cost_pt,
                         null_net_R_per_trade=net,
                         null_net_R_per_trade_median=med,
                         null_gross_R_per_trade=gross,
                         null_gross_R_per_trade_median=gross_med,
                         null_sd_per_draw=sd, null_se=se, tol_3se=t,
                         passes=int(np.isfinite(t) and abs(gross) <= t)))
    D = pd.DataFrame(rows)
    ok = bool(len(D)) and bool(D.passes.all())
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
    if out:
        D.to_csv(out, index=False)
    return D, ok


def condition4_all(verbose=True):
    """Every stage-1 variant on disk."""
    import glob
    rows, oks = [], {}
    for f in sorted(glob.glob(os.path.join(OUT, 'stage1_*_summary.csv'))):
        tag = os.path.basename(f)[len('stage1_'):-len('_summary.csv')]
        nf = os.path.join(OUT, 'stage1_%s_nulls.csv' % tag)
        if not os.path.exists(nf):
            continue
        D, ok = condition4(nf, f, label=tag, verbose=verbose)
        rows.append(D); oks[tag] = ok
    if not rows:
        return pd.DataFrame(), {}
    A = pd.concat(rows, ignore_index=True)
    A.to_csv(os.path.join(OUT, 'condition4_zero_edge.csv'), index=False)
    return A, oks
