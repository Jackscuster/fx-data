# External research: Layer 1 regime blueprints and Layer 2 NNFX combinations

Date: 2026-11-09. Author: Claude chat agent. Requested by Jack.
Scope: what exists outside the repo that could improve (not replace) Layer 1, and what NNFX
indicator combinations and settings the community actually uses for Layer 2.

Every claim about our own project below is traced to a repo file. Every external claim has a
source link at the bottom. Where a number is from the web it says so.

---

## Part 1. Layer 1: regime estimator blueprints

### 1.1 What is out there, in plain English

Almost everything published on "market regime detection" falls into five families:

| Family | What it does | Already tried here? | Where recorded |
|---|---|---|---|
| **A. Volatility-state models** (Hidden Markov Model on daily returns, Markov-switching variance) | Sorts days into calm / normal / turbulent by how big returns are. Says almost nothing about direction or shape. | **Yes.** 2-state Gaussian HMM lost to a plain 200-day SMA on both gate and switch logics. | `HANDOFF_3.md` lines 167 to 168, 192, 206 |
| **B. Threshold indicator stacks** (ADX > 25, Bollinger width, MA separation, Choppiness, Efficiency Ratio, Hurst) | Votes from 3 to 5 standard indicators, majority wins. | **Partly.** Efficiency ratio, choppiness, fractal dimension, variance ratio all exist in `code/`. Threshold stacks per se were not built as a Layer 1 candidate, but our two axes (straightness, scale) are the same information in cleaner form. | `code/` grep: efficiency ratio in 13 files, choppiness 4, fractal dimension 3, variance ratio 3 |
| **C. Price-structure / swing logic** (higher highs and higher lows, breaks, retracements) | Defines trend the way a discretionary trader draws it. | **Yes.** Built as `code/structure.py`, 144 cells, fails out of sample. Swing width N was the only lever that mattered. | `HANDOFF_3.md` §16.4 |
| **D. Trend-filtering as signal processing** (Kalman filter, L1 trend filter, Lanczos, wavelets; the Bruder, Dao, Richard, Roncalli 2011 paper is the standard reference) | Estimates a smooth "underlying trend" line and its slope from noisy prices, then reads regime from slope size and residual size. | **Not tried as a Layer 1 axis.** Kalman appears in one code file only, and only as an NNFX C1 option. | `code/` grep: Kalman 1 file |
| **E. Directional change / intrinsic time** (Glattfelder, Tsang; the 2022 SSRN paper applies it to FX) | Throws away the clock. Records only moves of at least X% from the last extreme. Trend = overshoot after a reversal keeps extending; range = reversals come quickly. Scale-free by construction. | **Not tried.** Zero hits for "directional change" in `HANDOFF_3.md` or `code/`. | grep |

Verdict: families A, B, C are either already tested here and dead, or are a worse version of what
our two axes already measure. Families D and E are the only genuinely new ground, and E is the
one built specifically for FX.

### 1.2 What the external work says that matters to us

1. **Nobody outside has solved "does trend predict trend."** The HMM thesis on seven FX pairs
   (Louda 2025) validates only with model-fit statistics (AIC/BIC) and reports no out-of-sample
   test at all. The regime-filtered-trend blog tests on Bitcoin and reports no numbers for the
   filter. The WorldQuant MSc paper (Srivastava 2018) uses smoothed probabilities, which look at
   future data, so its results overstate what is achievable live. Our own finding that trailing
   straightness mean-reverts (`HANDOFF_3.md` §16.1, chop minus trend forward efficiency +0.0218,
   p = 2.0%) is more rigorous than anything found. We are not behind.

2. **Volatility regimes are easy and shape regimes are hard, everywhere.** The HMM literature
   gets persistence of 90% to 99% for its calm and turbulent states on illiquid pairs, but on
   EURUSD the calm state persists only 66% day to day (Louda 2025, Table 5, web). That matches
   our panel-wide activity finding: vol spikes hit all 28 pairs at once, so activity is the
   axis that separates cleanly.

3. **Correlation rises in crisis.** Louda finds euro-quoted pairs become more correlated in
   turbulent states. Our crisis component is unfinished (`HANDOFF_LAYER2.md` routing table
   treats crisis as a panel label). A panel-correlation spike detector is a cheap, present-tense,
   motivated construction for the crisis axis that has not been built here.

4. **Relative cuts cannot show a sustained trend as sustained.** This is our own finding
   (`HANDOFF_3.md` §16.1b: EURJPY reads 28.6% to 29.8% trend at every window, indistinguishable
   from the panel). Directional change (family E) is the one external method that uses an
   absolute threshold by design, which is exactly the fix §16.1b says would be needed.

### 1.3 Recommended motivated constructions (few, declared in advance, per Rule 10)

Ranked. Each is present-tense, no money metrics, lagged one bar, tercile cuts learned on IS.

**L1-R1. Directional-change overshoot ratio (family E).** For each pair, fix a threshold
theta (candidate 0.5%, 1.0%, 1.5% of price; pick on IS by separation, not by eye). Record each
reversal of size theta from the last extreme and the overshoot that follows. Present-tense
shape score = mean overshoot / theta over the last K directional-change events. Trend = large
ratio (moves keep going after a theta reversal), range = ratio near 1 (reversals come straight
back). Cheap, scale-free, FX-specific, never tried here. Test: separation against our
straightness axis, persistence, refit stability, 200-draw null. If it just reproduces
straightness it is a confirmation, not a new axis, and we record that.

**L1-R2. Kalman slope-to-noise (family D).** Local-linear Kalman filter on log price. Shape
score = |filtered slope| / filtered residual sd over the last 20 bars. This is a smoothed cousin
of straightness; its value is lower lag at state starts. Test it on reaction lag against the
`ribbon.truth()` reference (`HANDOFF_3.md` §16.6) alongside the 8/21/60 ribbon. If lag is not
shorter it adds nothing.

**L1-R3. Panel correlation spike for crisis.** 20-bar rolling average pairwise correlation of
daily returns across the 28 pairs (or across the 7 USD majors), lagged one, cut at IS terciles.
Crisis candidate = top band AND activity top band. Validate against `events.py` dates only,
forward window event date to +15 bars, per the existing non-circularity rule in `CLAUDE.md`.
This is the only one of the three aimed at the unfinished component.

Not recommended: any further HMM on returns (already lost to a 200 SMA), ADX-style vote stacks
(same information as our axes, more parameters), swing-structure variants (§16.4 killed them).

---

## Part 2. Layer 2: NNFX combinations and settings

### 2.1 The honest state of the public record

The NNFX community does **not** publish league tables of indicator combinations with settings
and results. What exists:

- **VP's canonical rule set** (flow charts PDF, web). ATR for management; price must be within
  1x ATR of the baseline to enter; 7-candle "Bridge Too Far"; one-candle rule; pullback rule;
  continuation trades ignore volume; C2 must agree on every entry type. **Stop 1.5x ATR, take
  profit 1x ATR, trail at 1.5x ATR once 2x ATR in profit.**
- **Testing frameworks, not results**: NNFX Algo Tester (MT4, 25 baselines, 50 confirmation /
  volume / exit indicators), the goncaloe MT4 C1 backtest EA, several open-source TradingView
  "NNFX Tester" strategies. All give you the machine and leave the search to you.
- **Single-indicator reviews**: Stonehill Forex runs a series ("X as a Confirmation Indicator"),
  daily bars, 3 years, 2% risk, two half trades, stop 1.5x ATR on EURUSD. Results are posted as
  screenshots, not tables, and there is no cross-indicator ranking.
- **Shared personal algos** on Forex Factory and forex-station. Both sites refused the fetch
  from this machine (client error). Jack can open them in Chrome; what is usually posted there
  is a five-slot list with default settings and a screenshot of a myfxbook curve, not a
  reproducible test.

So the web gives us **candidate combinations**, not **verdicts**. That is still useful, for the
reason below.

### 2.2 One thing in Jack's spec differs from VP's canonical

Jack's risk rules (`HANDOFF_LAYER2.md` lines 57 to 60): **stop 1x ATR, take profit 1.5x ATR**
on leg 1. The Pine file agrees: `atrMulti_Loss = 1.0`, `RR = 1.5` (`JCs_NNFX_ALGO_V5_1.pine`
lines 97 to 99). VP's flow chart is the other way round: **stop 1.5x ATR, take profit 1x ATR**.

That is not an error, it is Jack's choice, and the risk rules are declared fixed and never
swept. Recording it because anyone comparing our results to published NNFX results must know
the two are not on the same stop-to-target geometry. Tighter stop, wider target means a lower
win rate on leg 1 and more leg 2s that never activate. Nothing to change; just know it.

### 2.3 Community-favoured combinations, with the defaults our Pine file already carries

These are the combinations that recur most in NNFX discussion and in VP's own indicator
reviews. Settings below are **our Pine file's defaults** (`JCs_NNFX_ALGO_V5_1.pine`, line
numbers given), which is what the frozen-default funnel will run anyway. Where the community
default differs it is noted.

| # | Baseline | C1 | C2 | Volume | Exit | Notes |
|---|---|---|---|---|---|---|
| N1 | Triangular MA (Pine default) or Kijun-sen 26 (VP's favourite, **not in our 14 baselines**) | SSL Channel, len 10 (line 364) | Trend Direction Force Index, lookback 13, filters +/-0.05 (lines 371 to 373) | Waddah Attar Explosion, sens 150, fast 20, slow 40, BB 20 / 2.0 (lines 384 to 388) | SSL Channel (Pine default exit) | The single most common "starter" NNFX algo in the community. Our Pine default C1 and exit are already SSL. |
| N2 | HMA 20 (line 1468) | DiDi Index, medium 8, long 20 (lines 229 to 230) | Detrended Synthetic Price Osc, len 14 (line 226; Pine default C2) | Variance, EMA len 10 (line 631; Pine default) | Chandelier Exit, ATR 22, mult 3.0 (lines 208 to 209) | Jack's own Pine defaults are closest to this row. |
| N3 | McGinley Dynamic | Schaff Trend Cycle 12 / 26 / 10, bands 65 / 35 (lines 355 to 361) | Vortex 14 (line 381) | Damiani Volatmeter | Supertrend ATR 10, factor 3.0 (lines 367 to 368) | Popular among the "oscillator C1, structure exit" crowd. |
| N4 | KAMA | Coral, smooth 10, D 14 (lines 218 to 219) | QQE Mod, RSI 6 / 5, factor 1.61 (lines 319 to 321) | TTM Squeeze | Coral | Coral/QQE is a frequently shared pairing. |
| N5 | EMA (community uses 20 to 30) | Aroon 25 (line 195) | Kalman Filter, sharpness 1.0, K 1.0 (lines 284 to 285) | Volatility Ratio | Aroon | Low-lag pairing; Aroon 25 is our default, VP reviewed 14. |
| N6 | Super Smoother 2-pole | Half Trend | Fisher Transform | Williams VIX Fix | Half Trend | Half Trend is one of the most downloaded NNFX C1s. |

Six rows, 30 slot choices, zero parameter sweeps. ATR 14 everywhere (line 96).

### 2.4 Why this matters: it is a Rule 10 problem

`HANDOFF_LAYER2.md` lines 100 to 109 describe a two-stage funnel over roughly 17.6 million slot
combinations. Rule 10 says searching manufactures effect size and that 78% of Layer 1's best
headline was selection artifact (`HANDOFF_LAYER2.md` rule 8). The funnel has controls for that
(scrambled floor, family cuts, one OOS look), and it should run. But the six rows above are
exactly what Rule 10 asks for: a **small declared set, motivated by people who traded these
combinations for years, written down before any result is seen.**

Proposal: run N1 to N6 through the engine first, as **declared constructions**, with the same
IS / OOS gate as the funnel. They become the reference the funnel's survivors are compared
against. If the funnel's best is not clearly better than the best declared row after deflation,
the funnel bought nothing but selection. If a declared row survives on its own, we have a
Layer 2 candidate with zero search debt.

Gaps to note for Code: Kijun-sen is not one of our 14 baselines. The V9 patch adds Ichimoku as
a confirmation option (`HANDOFF_LAYER2.md` line 94); Kijun as a baseline would be a one-line
addition if Jack wants N1 run the way the community runs it. Damiani Volatmeter, TTM Squeeze,
Volatility Ratio and Williams VIX Fix are all already in our 12 volume options (Pine line 136
to 137).

---

## Part 3. What to do with this

1. Layer 1: build L1-R1 (directional change) and L1-R3 (panel correlation crisis) as present-
   tense axes with the standard validation battery. L1-R2 only if reaction lag is still a
   problem after those two. Nothing else from the external literature is worth the hours.
2. Layer 2: register N1 to N6 as declared constructions in the open-work register, run them
   before or alongside the funnel, report both.
3. Jack: open the Forex Factory VP thread and forex-station NNFX indicators thread in Chrome
   and screenshot any posted five-slot algo with settings. Those get added as N7 onward, still
   declared before results are seen.

---

## Sources

Layer 1
- [Trend Following Trading under a Regime Switching Model (Dai, Zhang, Zhu)](https://www.researchgate.net/publication/220137782_Trend_Following_Trading_under_a_Regime_Switching_Model)
- [Louda 2025, Forex Market Regime Estimation via HMM, V4 countries (Charles University thesis)](https://dspace.cuni.cz/bitstream/handle/20.500.11956/200417/120507159.pdf?sequence=1&isAllowed=y)
- [Hidden Markov model analysis of extreme behaviors of FX rates (ScienceDirect)](https://www.sciencedirect.com/science/article/abs/pii/S0378437118309324)
- [Directional change and regime change detection in FX (SSRN 4048864)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4048864)
- [Hidden Markov model applied to FX prediction (E. Chan)](http://epchan.blogspot.com/2012/03/hidden-markov-model-applied-to-fx.html)
- [Trend Filtering Methods for Momentum Strategies (Bruder, Dao, Richard, Roncalli)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2289097)
- [Trend without hiccups: a Kalman filter approach (arXiv 1808.03297)](https://arxiv.org/pdf/1808.03297)
- [Momentum Strategies with L1 Filter (arXiv 1403.4069)](https://arxiv.org/pdf/1403.4069)
- [Structural clustering of volatility regimes (arXiv 2004.09963)](https://arxiv.org/pdf/2004.09963)
- [Srivastava 2018, regime-aware system on S&P 500 (arXiv 1812.02527)](https://arxiv.org/pdf/1812.02527)
- [Regime Filtered Trend Strategy (pyquantlab)](https://pyquantlab.medium.com/regime-filtered-trend-strategy-a-market-adaptive-trend-following-system-fa933e001237)
- [Market Regime Filter: SMA + ATR rules (QuantMonitor)](https://quantmonitor.net/how-to-identify-market-regimes-and-filter-strategies-by-trend-and-volatility/)
- [Building a Custom Market Regime Detection System in MQL5](https://www.mql5.com/en/articles/17737)
- [Market Regime Detector (TradingView, forexobroker)](https://www.tradingview.com/script/tL3FZynR-Market-Regime-Detector-forexobroker/)
- [Kaufman Efficiency Ratio (LuxAlgo)](https://www.luxalgo.com/library/concept/kaufman-efficiency-ratio/)
- [Market Efficiency and Regime Persistence Measures (LuxAlgo)](https://www.luxalgo.com/library/concept/market-efficiency-and-regime-persistence-measures/)
- [Choppiness Index (LuxAlgo)](https://www.luxalgo.com/library/concept/choppiness-index/)
- [The Hurst Exponent: what H actually measures (Vortex Capital)](https://www.vortexcapitalgroup.com/insights/the-hurst-exponent-mean-reversion-random-walk-or-trend-what-h-actually-measures)
- [Global FX management with systematic macro scores (Macrosynergy)](https://macrosynergy.com/research/global-fx-management-a-systematic-macro-view/)
- [FX trends and external balance headwinds (Macrosynergy)](https://macrosynergy.com/academy/notebooks/fx-trends-and-external-balance-headwinds/)
- [Market regimes in trading (Algorier)](https://algorier.com/blog/market-regimes-in-trading/)
- [Market regime detection (ArrowAlgo)](https://arrowalgo.com/market-regime-detection-algorithmic-trading/)

Layer 2
- [No Nonsense Forex flow charts PDF (nononsensetrader.com)](https://nononsensetrader.com/wp-content/uploads/2021/02/No-Nonsense-FOREX-Flow-Charts.pdf)
- [NNFX Algo Tester, included indicators](https://nnfxalgotester.com/help/included-indicators/)
- [NNFX Algo Tester, operation modes](https://help.nnfxalgotester.com/knowledgebase.php?article=54)
- [NNFX Algo Tester, candidates search](https://help.nnfxalgotester.com/knowledgebase.php?article=113)
- [goncaloe/nnfx-backtest-c1 (GitHub, MT4 C1 tester)](https://github.com/goncaloe/nnfx-backtest-c1)
- [TyphooN MQL5 NNFX Risk Management System (GitHub)](https://github.com/TyphooN-/MQL5-NNFX-Risk_Management_System)
- [Strategy NNFX Tester (TradingView, open source)](https://in.tradingview.com/script/yveRmB4r-Strategy-NNFX-Tester)
- [No Nonsense NNFX VP Strategy for Back Testing Indicators (TradingView)](https://in.tradingview.com/script/Y2UvLNZW-No-Nonsense-NNFX-VP-Strategy-for-Back-Testing-Indicators-jh)
- [Testing Overload: NNFX in LEAN Improved (Medium, fetch refused)](https://mirco-kahle.medium.com/testing-overload-nnfx-in-lean-improved-bf1cbe913c9c)
- [Cross Roads as a Confirmation Indicator (Stonehill Forex)](https://stonehillforex.com/2025/03/cross-roads-as-a-confirmation-indicator/)
- [Trend Continuation as a Confirmation Indicator (Stonehill Forex)](https://stonehillforex.com/2022/12/trend-continuation-as-a-confirmation-indicator/)
- [No Nonsense Forex indicators thread (forex-station, fetch refused)](https://forex-station.com/no-nonsense-forex-indicators-t8474695.html)
- [No nonsense Forex VP thread, page 3 (Forex Factory, fetch refused)](https://www.forexfactory.com/thread/886311-no-nonsense-forex-vp?page=3)
- [No nonsense Forex VP thread, page 4 (Forex Factory, fetch refused)](https://www.forexfactory.com/thread/886311-no-nonsense-forex-vp?page=4)
- [NNFX Algorithm Tutorial, system indicator settings (YouTube)](https://www.youtube.com/watch?v=TNiON5zVMf4)
- [No Nonsense Forex Algorithm overview (4xpip)](https://4xpip.com/no-nonsense-forex-algorithm-nnfx/)
- [NNFX Strategy Guide (frzsoftware)](https://www.frzsoftware.com/product/no-nonsense-forex-strategy-nnfx/)
- [NNFX template file (fxdreema forum)](https://fxdreema.com/forum/topic/7726/nnfx-template-file)
- [NNFX Strategy Flow Chart (Scribd)](https://www.scribd.com/document/476085071/NNFX-Strategy-Flow-Chart)
- [No Nonsense Forex: The Manual 1.0 (Scribd)](https://www.scribd.com/document/470768357/No-Nonsense-Forex-The-Manual-1-0-June-2019)

---

## Addendum, same day, after reading `HANDOFF.md` item 0f and `claude/open-work-register.md`

Parts 1 to 3 above were written from `HANDOFF_LAYER2.md` and `HANDOFF_3.md`. Both are behind
the repo's `HANDOFF.md`, which is authoritative. Nothing above is deleted; this section says what
changes.

### What is actually the plan for Layer 2

Not the 17.6M funnel. The **blind-label programme** (`HANDOFF.md` 0f): all 45,139 already-built
candidates (mode A 17,822, B 19,845, C 7,472), five rolling windows, tune years 1 to 4, grade on
year 5 which the tuner never saw, trade year 6 untouched. Everyone trades, equal weight, no
picking. The year-5 grade is reported and never used. Built, smoke-tested on 250 A/B and 104 C,
pre-flight 27 of 27 on 8 Nov (`results/audit_2026-11-08.csv`). **Full cloud run not launched.**
Cost from 0f: 225,695 jobs, 4,564 core-hours, three 16-vCPU boxes, about $47, 6.6 days. Launch
is Jack's call.

Jack's standing rule (register, 22 Sep): no verdicts on the library until the blind design runs
at full scale. Part 2 above makes none and should not be read as one.

### What the smoke already says, from files

Mode C routed to TRENDING is the first positive book: median year +1.33%, PF 1.087, retention
+0.26, 4 of 5 traded years positive, beats the regime-shuffle null (p = 0.00), random-entry
p = 0.08 (`results/refit_books_modec2.csv`). Caveats in 0f: 104 strategies, worst year −4.0%,
DIP95 6.9 against a 3.6 budget, and C's blind grade predicts nothing.

Every A/B book is negative. Per slice under correct costs: A-chop +0.63, B-chop +0.52,
B-trend +0.01, A-trend −1.25 (`results/refit_books_blind2.csv`).

### How Part 2 (N1 to N6) fits the real plan

The six community combinations are built from the same indicator slots as modes A, B and C, so
some or all of them are probably **already among the 45,139 candidates**. The right move is not
to run them separately. It is:

1. Look each one up by slot signature in `results/refit_candidates_full.csv`. Record which sid
   it is, or that it is absent (Kijun-sen baseline means N1 as the community runs it is absent).
2. Tag those sids as **declared reference rows** before the full run. Zero extra cost; they ride
   in the cloud run with everyone else.
3. In the `--stage report` output, print their year-6 records next to the pooled book. That is
   the Rule 10 comparison: did 45,139 searched candidates do better than six that people chose
   by hand years ago.

If any N-row is absent from the candidate list it stays absent until the full run is done.
Adding candidates now would change the launch inputs after pre-flight passed.

### How Part 1 (Layer 1 constructions) fits the real plan

The register records Jack's intent: "trend in the regime estimator still needs fixing
regardless; test trend with/without it." The one positive book routes on the trend axis, and the
trend axis is the weak detector (fails its separation null everywhere, 0a). So L1-R1
(directional change) is aimed at the right problem.

Three constraints Part 1 did not state:

- Layer 1 now lives on the **5pm OANDA bar** (`results/layer1_states_5pm.csv`, series from
  2002-09-24). Any new axis is built on `data/px28.csv` (the 5pm series), not `px28_h10.csv`.
- The validation window is **confirm on 2016 to 2020 only; 2021 onward is sealed** (W4, opened
  once on the finished routed system). Part 1.3 said 2016 to 2026. Wrong; 2016 to 2020.
- Tercile cuts learned on the tuning window only, per the 5pm rebuild's rules.

The test that matters for a new trend axis is not just the present-tense battery. It is: route
mode C (and the A/B trend slices) on the new axis instead of `shape2` TRENDING, same walk, same
nulls, and see whether the routed book improves. That is a Layer 3 test and it is the one Jack
asked for.

### What Jack decides

1. Launch the cloud run or not. The agent has no view on the spend that is not already in 0f.
2. Whether to tag N1 to N6 as declared reference rows in the report stage before launch. Costs
   nothing, changes no inputs, needs a short Code prompt.
3. Whether L1-R1 gets built now on the Mac while the boxes run, or after.

---

## Correction, same day, after Jack's review and a read of project memory

Two statements in Part 2.2 and 2.3 are wrong. Left in place above; corrected here.

**Stop and target are tuned, not fixed.** Part 2.2 said leg 1 is fixed at stop 1x ATR, target
1.5x, quoting `HANDOFF_LAYER2.md` and the Pine defaults. That file is stale. The engine tunes
risk multiples per strategy: `code/l2tune.py` lines 73 to 77, `GRID_STOP` 1.00 to 1.50,
`GRID_TP` 1.00 to 3.00, `GRID_TRAIL` 0.50 to 2.00, plus ATR length, breakeven and trail arm
(`RISK_KNOBS_TREND`, lines 82 to 84). Project memory records the same rule: stop, take-profit
and trail multiples are tuned per strategy, never fixed. The comparison to VP's 1.5x / 1x
geometry is void. Nothing to record, nothing to change.

**Ichimoku was tested.** Part 2.3 flagged Kijun-sen as missing. The Python library has Ichimoku
(tenkan 9, kijun 26, senkou 52, cloud lagged by kijun bars) as a confirmation indicator,
`code/l2ind.py` line 300, and it went through the gauntlet; the row at `GAUNTLET.md` line 1510
(ichimoku x fx_sniper_ergodic_cci x fractal_dimension x alma, A/trend) is negative on both
windows. Kijun as a baseline slot specifically is not in the list, but that is a detail, not a
gap, and item 3 under "What Jack decides" in the first addendum is withdrawn.

Lesson for the agent, recorded in `AGENT_LOG.md`: read project memory and `HANDOFF.md` before
`HANDOFF_LAYER2.md` or `HANDOFF_3.md`. The newer files win.
