# External research, part 2: every regime taxonomy in use, and the NNFX combination catalog

Date: 2026-11-09, evening. Author: Claude chat agent. Requested by Jack.
Follows `RESEARCH_2026-11-09_regime_blueprints_and_nnfx.md` (part 1, with its two corrections).

Jack's brief: (1) evaluate all regime estimators out there against our trend / chop / crisis
scheme, which can be expanded or simplified if existing concepts fit; (2) find every NNFX
indicator combination with settings, tagged as verifiable or not; anything we cannot verify we
test ourselves.

Repo state checked first: project memory, `claude/open-work-register.md`, `HANDOFF.md` 0f.
Every "already tried here" claim below is traced to a repo file. Every external claim has a
source link at the bottom. Where a number is from the web it says so.

---

## PART 1. REGIME TAXONOMIES: WHAT THE WORLD USES, AND HOW IT COMPARES TO OURS

### 1.1 Our scheme, for reference

Two present-tense axes on the last 20 bars, lagged one, per-pair tercile cuts learned on the
tuning window: **shape** (straightness = |net| / path; trend vs chop) and **activity** (scale =
path / vol-normalised). Crisis is a panel-level acute detector validated against news dates
(`events.py`), plus MOVE as a confirming witness. Chop axis real out of sample; trend axis weak
(`HANDOFF_3.md` §16.1, §16.5; project memory).

### 1.2 The eight regime families in use, and how each is estimated

| # | Family | What the regimes are | How estimated (typical) | Where it is used | Maps to ours |
|---|---|---|---|---|---|
| 1 | **Trend / range by price shape** | trending vs ranging (sometimes "transitional") | Efficiency ratio, ADX, choppiness index, fractal dimension, Hurst, variance ratio, R² of price on time; or a vote stack of several | Every practitioner framework; our Layer 1 | **= our shape axis.** Same information, usually more parameters. |
| 2 | **Volatility state** | quiet / normal / volatile (2 or 3 states) | HMM or Markov-switching on returns; or ATR% percentiles per instrument (Van Tharp: <25th pct quiet, >75th volatile) | Kole & van Dijk; Louda 2025 (7 FX pairs); Van Tharp market types; most crypto regime repos | **= our activity axis.** Tercile cut on vol-normalised path is the same idea. 2-state Gaussian HMM already lost here to a 200 SMA (`HANDOFF_3.md` line 167). |
| 3 | **Direction × volatility grid** | bull / bear / sideways × quiet / volatile = 6 types (Van Tharp); crash / slow growth / bull / recovery = 4 (Guidolin & Timmermann); 4 Wyckoff-style phases (Srivastava) | Direction from trend filter or dating rule, volatility from ATR% or MS variance; cross them | Van Tharp (equities), Guidolin-Timmermann (US stocks/bonds), WorldQuant MSc | **= our 9-box, minus direction.** We dropped direction on evidence: 121 constructions at chance, per-pair direction persistence 47.9% (`HANDOFF_3.md` §16.5). The literature's direction states are for long-only equity allocation, where direction matters; for a long/short FX system it does not. |
| 4 | **Bull / bear phase dating** | bull vs bear, with confirmed turning points | Lunde-Timmermann (switch on 20% rise / 15% fall from last extreme), Pagan-Sossounov / Bry-Boschan (extreme within a 32-week window, minimum phase length, last 13 weeks censored) | Equity indices; Kole & van Dijk compare them to Markov switching on S&P 500 1955-2010 | **Not tried here.** It is directional change (family 7) with a clock and a minimum duration. Their finding matters to us: rule-based dating and Markov switching disagree on 32% to 37% of weeks because MS weights volatility and the rules weight the trend. Rules date better in-sample; MS forecasts better. We are a describer, so the rules side is ours. |
| 5 | **Turbulence / stress** | normal vs turbulent (continuous index, or 2-state HMM on the index) | Turbulence index = Mahalanobis distance of today's return vector from its history (Kritzman & Li 2010); absorption ratio = share of panel variance in the first few PCs | Kritzman applied it to a G-10 carry strategy; First Sentier fits a 2-state HMM to monthly FX turbulence 1980-2021 | **This is our crisis component, done multivariate.** Our acute detector is univariate per pair plus a panel count. Turbulence is one number for the whole 28-pair panel, present-tense, cheap, never tried here (grep: 0 hits). Known property: stays elevated a couple of weeks after a spike, insensitive to window length from 6 months to several years. |
| 6 | **Carry regime** | calm vs volatile, defined by FX implied vol | First PC of 1-month implied vols (CAD, CHF, EUR, JPY, GBP vs USD), logistic smooth transition, lagged one day | Christiansen, Ranaldo, Söderlind: carry returns about −25% annualised in the top 5% vol days vs +4.6% full sample; equity beta 0.03 calm vs 0.20 volatile | **A Layer 3 routing fact, not a new Layer 1 state.** Our activity axis is the realised-vol cousin. Carry is dead here on 2016-2020 (register), so this only matters if carry returns. |
| 7 | **Directional change / intrinsic time** | up-mode vs down-mode; events at a fixed % threshold; overshoot after each event | Threshold δ; a reversal of δ from the last extreme is a DC event; further δ-moves are overshoots. Scaling law: average overshoot ≈ δ. Regime work (Chen & Tsang, Hu et al.) feeds DC-event returns into a 2-state HMM: normal vs abnormal | Olsen / Glattfelder (tick FX, 13 pairs); Tsang's group (Essex); Hu et al. 2023 on 8 FX pairs, tick data 2019-2020 | **Not tried here. The one genuinely new axis.** Scale-free, absolute threshold (fixes the §16.1b problem that relative tercile cuts cannot show a two-year trend as a trend). All published work is intraday; no one has published a daily-bar FX version. The regime HMM papers exclude transaction costs and are not a template; the DC event stream itself is. |
| 8 | **Liquidity regime** | liquid vs illiquid | Low-frequency proxies from daily data: Roll measure (from closes), Corwin-Schultz (from high-low). Mancini, Ranaldo, Wrampelmeyer show FX liquidity has strong commonality across pairs and dries up panel-wide in crises | SNB / EPFL working paper on 2007-2009 | **A crisis witness we do not have.** The Roll measure needs only daily closes, so it fits Layer 1's close-only panel. Untested here (grep: 0 hits for Roll). |

Two more that are not price-regimes and are out of scope for Layer 1: macro quadrants (growth
× inflation, Bridgewater-style) and risk-on / risk-off indices (correlation of risky assets).
The second is the absorption ratio by another name.

### 1.3 What the literature says that bears on our three states

**On trend.** Safari & Schmidhuber 2025 (24 futures incl. 6 FX, 1990-2020, daily): markets
trend from a few hours out to about a year, and revert inside that and beyond it. The
persistence coefficient peaks at 6 to 12 months and **has been declining over time; the authors
extrapolate it could reach zero between 2010 and 2030.** Hsu, Taylor & Wang 2016: 21,195
technical rules on 30 currencies 1971-2015 with a stepwise data-snooping test; **no significant
developed-currency predictability since 1992-1996**; the 2012-2015 developed-market portfolio
earned a Sharpe of 0.24, not significant. Our finding that trailing straightness mean-reverts
(§16.1) and that 2016-2020 is the deadest era on record (register) is the same phenomenon seen
from inside the data.

**On chop.** Nobody publishes a chop estimator as such. Mean reversion is treated as the
absence of trend (Hurst < 0.5, efficiency ratio low). Our separate chop axis with three legs
(failed swings, boundary tests, range containment, per project memory) is more developed than
anything found. Keep it.

**On crisis.** The field agrees on three facts we can use. (a) Correlation rises: Louda 2025 on
V4 pairs, Kritzman's absorption ratio, Mancini's liquidity commonality all say the panel moves
as one in stress. (b) Vol-regime estimators get 90% to 99% day-to-day persistence on illiquid
pairs but only about 66% on EURUSD (Louda, Table 5), so crisis is easier to see on the panel
than on a major. (c) Momentum crashes happen in a specific state: after a bear market, when
volatility is high, at the turn (Daniel & Moskowitz). For a trend sleeve that is the crisis
exit rule.

**On the 9-box vs 6-state question.** Van Tharp's six market types are exactly direction ×
volatility with the middle vol band dropped. We measured and rejected 6 states (§16.1b:
collapsing the transitional row cut strong-trend vs strong-chop separation from +0.0133 to
+0.0097 with a larger n). The literature does not test this; we did.

### 1.4 Verdict: expand, simplify, or keep

**Keep the three states. Do not add states.** Every taxonomy in use is a subset or a relabelling
of shape × activity plus a stress flag. Direction is the only axis others carry that we do not,
and we dropped it on 121 constructions at chance. Rule: adding states nobody asked for is on the
do-not-repeat list.

**Change how two of the three are estimated, not what they are:**

1. **Trend axis**: add a directional-change construction (family 7) as a candidate shape score.
   Absolute threshold, per pair, in units of that pair's own vol so the threshold means the same
   thing on USDJPY and EURGBP. Score = mean overshoot / threshold over the last K events (trend
   large, range near 1). Judged on the standard battery, then on the Layer 3 test: route mode C
   on it instead of `shape2` TRENDING, same walk, same nulls. Thresholds declared before the run
   (0.5, 1.0, 1.5 × 20-day vol), picked on the tuning window by separation, not by eye.
2. **Crisis**: add the panel turbulence index (family 5) and the Roll illiquidity measure
   (family 8) as two more witnesses beside MOVE. Both are present-tense, both need only daily
   closes, both are one number for the panel. Validation unchanged: `events.py` dates, forward
   window only, sub-period split.

Not recommended: HMM / Markov switching (lost to a 200 SMA here; also the Kole-van Dijk finding
that it weights volatility, which our activity axis already carries); bull/bear dating rules
(long-only equity tools; our long/short system has no use for direction); vote stacks of ADX,
Bollinger width and friends (our two axes, more knobs).

---

## PART 2. THE NNFX COMBINATION CATALOG

### 2.1 What exists publicly, graded by verifiability

| Grade | Meaning | What falls in it |
|---|---|---|
| **V** | Verifiable: source data or code and results we can re-run | Nothing found. Zero published NNFX combinations come with data we can re-run against. |
| **M** | Methodology published, results as screenshots or prose | Stonehill Forex single-indicator tests (daily, 3 years, 2% risk, two half trades, stop 1.5× ATR, EURUSD / BTC / XAU / SPX500); frameworks (NNFX Algo Tester, backtestd-expert, goncaloe EA, TradingView NNFX Tester) |
| **S** | Self-reported, no data | myfxbook "Real NNFX" (backtest Jan 2017 to Dec 2019, 33% a year, 61% win rate, 28 pairs; system since deleted); babypips journal (44 pairs, 3-year windows: 2012-14 +15%, **2014-16 −129%, 2016-18 −63%**, 2018-20 +75%, 2020-21 +45%; author's own verdict: fitted to recent data, no edge) |
| **N** | Named components only, no settings, no results | VP's own site (he says "test them all, see who wins" and publishes nothing); frzsoftware product mapping; most TradingView scripts |

VP has never disclosed his algorithm (confirmed on frzsoftware and on his own volume page).
Every "VP's favourite" claim in the community is hearsay.

### 2.2 Canonical rule set, from the flow charts (grade M, rules not results)

ATR 14. Entry only within 1× ATR of the baseline. Bridge Too Far: C1 signal must be under 7
candles old for a baseline-cross entry. One-candle rule. Pullback rule (price beyond 1× ATR,
then closes back inside, all indicators agree). Continuation entries need the baseline not to
have been crossed since the last entry and ignore volume. C2 must agree on every entry type.
Order 1: stop 1.5× ATR, target 1× ATR. Order 2: stop 1.5× ATR, no target, breakeven when order
1 banks, trail 1.5× ATR once 2× ATR in profit. 2% risk split 1% / 1%. Exit on baseline cross or
exit indicator (C1 opposite flip if none).

Our engine: risk multiples are tuned per strategy over `GRID_STOP` 1.00 to 1.50, `GRID_TP`
1.00 to 3.00, `GRID_TRAIL` 0.50 to 2.00 (`code/l2tune.py` lines 73 to 77), so VP's fixed
geometry is one point inside our grid. Nothing to change.

### 2.3 Every named combination found, with settings where stated

Settings in **bold** are stated by the source. Everything else is the indicator's standard
default (the value our Pine file carries, `JCs_NNFX_ALGO_V5_1.pine`, line numbers in part 1).

| ID | Baseline | C1 | C2 | Volume / filter | Exit | Source, grade | In our 45,139? |
|---|---|---|---|---|---|---|---|
| N1 | Kijun-sen 26 (community) / TMA (our default) | SSL Channel 10 | TDFI 13, ±0.05 | Waddah Attar Explosion 150 / 20 / 40 / BB 20, 2.0 | SSL | community "starter algo", grade N | **No.** SSL+TDFI+WAE: 0 rows. SSL+any C2+WAE: 79 rows |
| N2 | HMA 20 | DiDi Index 8 / 20 | DSPO 14 | Variance EMA 10 | Chandelier 22 / 3.0 | Jack's own Pine defaults, grade N | **No.** DiDi+DSPO: 0 rows |
| N3 | McGinley Dynamic | Schaff Trend Cycle 12 / 26 / 10, 65 / 35 | Vortex 14 | Damiani Volatmeter | Supertrend 10 / 3.0 | community, grade N | Partly. STC+Vortex: 11 rows |
| N4 | KAMA | Coral 10 / 14 | QQE Mod 6 / 5 / 1.61 | TTM Squeeze | Coral | community, grade N | Partly. Coral+QQE: 13 rows |
| N5 | EMA 20-30 | Aroon 25 | Kalman Filter 1.0 / 1.0 | Volatility Ratio | Aroon | community, grade N | Partly. Aroon+Kalman: 86 rows |
| N6 | Super Smoother 2-pole | Half Trend | Fisher Transform | Williams VIX Fix | Half Trend | community, grade N | Partly. HalfTrend+Fisher: 36 rows |
| N7 | selectable | **QQE Mod fast** | **QQE Mod slow** | WAE | selectable | TradingView chrisfraser05 "NNFX Baseline, QQEs Fast C1, Slow C2" script, grade N. **Default TP 1× ATR, SL 1.5× ATR, entry within 1.5× ATR of baseline, 3-candle signal suppression**, later added EVZ filter and currency-strength filter | QQE as C1 and C2: not checked (our list has one QQE entry name) |
| N8 | **Hull MA** | **Bull Bear Pressure** (net pressure vs zero) | user's choice | **Ranging Market indicator**, optional **EVZ < 7-8 = no trade** | Hull MA turn or BBP flip | frzsoftware product, grade N. ATR 14, bands 1.0 / 1.5 | Bull Bear Pressure not in our library |
| N9 | **Kijun-sen + ATR** (as C1 in a TradingView tester) | **Cronex T Demarker**, **Squeeze Momentum**, **Awesome Oscillator** offered as C1s; **Absolute Strength Histogram**, **KDJ** as C2s | | WAE | | TradingView "Strategy NNFX Tester", grade N, no defaults given | Cronex, Squeeze Momentum, AO, ASH, KDJ not in our library |
| N10 | | **Cross Roads** (filtered WMA pair, **StartLen 2, Lookback 24**) | | | | Stonehill 2025, grade M: daily, 3 yrs, EURUSD stop **1.50× ATR**, all default-setting results positive, screenshots only | Not in our library |
| N11 | **LowPassFilter**, **Hull MA** as baselines | **Ehlers Sine Wave Stochastic, Ehlers Fisher, RMO, R-Squared, Kalman, Zero-Lag MACD, Ehlers Reverse EMA, Disparity Index, Leman Trend** each tested alone as C1 | | **WAE** (sensitivity typically **75-125**) | | Stonehill series, grade M, per-indicator, no combinations | Fisher, Kalman, Reverse EMA, Lemantrend in our library; Sine Wave Stoch, RMO, R², ZL-MACD, Disparity not |

Our candidate list has 39 confirmation indicators, 12 volume filters, 15 baselines and 39
exits (`results/refit_candidates_full.csv`). The 45,139 rows are the gate-1 survivor set, not
the full product, which is why two of the most-shared community combinations are not in it.

### 2.4 Three things the catalog tells us

1. **The community has no verified result.** Not one. The two self-reported multi-year
   backtests that exist (myfxbook 33%/yr on 2017-2019; babypips −129% on 2014-2016) point
   opposite ways and neither is reproducible. The academic record on FX technical rules (Hsu et
   al., 21,195 rules; Bajgrowicz & Scaillet on persistence) says the same thing our blind grade
   says: in-sample winners do not persist. Bajgrowicz & Scaillet, DJIA 1897-2011: fewer than 5%
   of selected rules survive the first re-selection, in-sample Sharpe 3.4 to 5.3 against
   out-of-sample 0.0 to 0.7, "no hot hands." Our blind grade's rank correlation of +0.02 to
   +0.05 (0f) is the FX version of that number.

2. **Six community combinations can be tested at trivial cost.** N1 to N6 in the exact
   community form (where our library has the parts) are 6 strategies × 5 windows at 72.8 s a
   job (0f): about 36 minutes on the Mac. They are declared constructions in Rule 10's sense:
   chosen by people who traded them for years, written down before any result. If any one of
   them beats the pooled 45,139 book after deflation, the search bought nothing. If none does,
   the search is vindicated on its own terms. Either answer is worth 36 minutes. N1 needs
   Kijun-sen as a baseline (one line in `l2ind.py`, pattern `baseline_sma`); the other five run
   as-is.

3. **Two filters the community uses that we do not have, both cheap, both Layer 3 not Layer 2:**
   an EVZ / implied-vol floor (no trade when the market is too quiet) and a currency-strength
   filter. The first is our activity axis WEAK band. The second is a per-currency aggregate of
   our shape axis across the 7 pairs each currency sits in; project memory already notes that
   currency-leg sharing roughly triples state agreement. Neither is a new indicator; both are
   routing rules we can test on the existing states.

---

## PART 3. WHAT THIS CHANGES, IN ONE PLACE

Layer 1: keep trend / chop / crisis. Add one candidate trend construction (directional change)
and two crisis witnesses (panel turbulence, Roll illiquidity). Nothing else from the literature
is worth the hours; most of it is our two axes with more parameters.

Layer 2: no verified NNFX result exists anywhere. Run N1 to N6 as declared constructions, 36
minutes on the Mac, as the Rule 10 reference for the full run. Add Kijun-sen baseline for N1.

Layer 3: two cheap routing tests from community practice, EVZ-style quiet filter (our WEAK
band) and currency-strength agreement, on the existing states.

Jack decides: cloud launch; whether N1 to N6 run before, during or after it; order of the Layer
1 constructions.

---

## Sources

Regime taxonomies and estimation
- [Louda 2025, FX regime estimation via HMM, V4 countries (Charles University)](https://dspace.cuni.cz/bitstream/handle/20.500.11956/200417/120507159.pdf?sequence=1&isAllowed=y)
- [Kole & van Dijk, How to identify and forecast bull and bear markets (ERIM 2013)](https://repub.eur.nl/pub/41558/ERS-2013-016-F&A.pdf)
- [Kole, How to identify and predict bull and bear markets (ERIM)](https://www.erim.eur.nl/fileadmin/erim_content/documents/BullBear3.pdf)
- [Pagan & Sossounov style dating, Extracting bull and bear markets (Toronto WP 369)](https://www.economics.utoronto.ca/public/workingPapers/tecipa-369.pdf)
- [A top-down approach to identifying bull and bear market states (QUB)](https://pureadmin.qub.ac.uk/ws/files/137453711/Bullbear_TD_IRFA_Revised.pdf)
- [Guidolin & Timmermann, Asset allocation under multivariate regime switching (St Louis Fed WP 2005-002)](https://files.stlouisfed.org/files/htdocs/wp/2005/2005-002.pdf)
- [First Sentier, Regimes, turbulence and absorption (FX turbulence HMM 1980-2021)](https://www.firstsentierinvestors.com/content/dam/web/global/islp-documentation/MAS_Regimes-turbulence-and-absorption.pdf)
- [Portfolio Optimizer, The turbulence index: formula and properties](https://portfoliooptimizer.io/blog/the-turbulence-index-measuring-financial-risk/)
- [Kritzman & Li bibliography: financial turbulence and absorption ratio](http://thefjg.blogspot.com/2018/03/bibliography-financial-turbulence-and.html)
- [Skulls, Financial Turbulence, and Risk Management (Kritzman & Li)](https://www.researchgate.net/publication/228232291_Skulls_Financial_Turbulence_and_Risk_Management)
- [wiktorjl/turbulence (GitHub implementation)](https://github.com/wiktorjl/turbulence)
- [Geometric observables for financial regime detection (arXiv 2605.17117)](https://arxiv.org/html/2605.17117)
- [Christiansen, Ranaldo & Söderlind, Time-varying systematic risk of carry trade strategies (St Gallen DP 2009)](https://ux-tauri.unisg.ch/RePEc/usg/dp2009/DP-0906-So.pdf)
- [Same paper, SNB working paper 2010-01](https://www.snb.ch/en/publications/research/working-papers/2010/working_paper_2010_01)
- [Glattfelder & Olsen, The theory of intrinsic time: a primer (arXiv 2406.07354)](https://arxiv.org/pdf/2406.07354)
- [Glattfelder et al., Patterns in high-frequency FX data: 12 scaling laws (ETH 2011)](https://www.sg.ethz.ch/publications/2011/glattfelder2011patterns-in-high-frequency/Patterns_in_high_frequency_FX_data_discovery_of_12_empirical_scaling_laws.pdf)
- [Hu et al., Intelligent trading strategy based on improved directional change and regime change detection (arXiv 2309.15383)](https://arxiv.org/html/2309.15383v1)
- [Chen, Studying regime change using directional change (Essex thesis)](https://pdf.core.ac.uk/corefilesystem/pdf/176/237700800.pdf)
- [Tsang et al., Classification of normal and abnormal regimes in financial markets (Algorithms 2018)](https://doi.org/10.3390/a11120202)
- [Tsang, Directional changes: a new way to look at price dynamics (2017)](https://www.bracil.net/finance/papers/Tsang-DCHorizon-2017.pdf)
- [Tsang, Tao & Ma, Profiling financial market dynamics under directional changes (CCFEA WP074)](https://www.bracil.net/ccfea/WorkingPapers/2015/Tsang-Tao-Ma-DCProfiling-WP074-2015.pdf)
- [Ma, Guidelines for the useable range of DC thresholds (CCFEA WP081)](https://www.bracil.net/ccfea/WorkingPapers/2019/Ma-Thresholds-WP081-19.pdf)
- [Voicu, Directional change trading strategies in FX (Essex MSc 2012)](https://www.bracil.net/finance/papers/Voicu-DCTrading-MSc2012.pdf)
- [Mancini, Ranaldo & Wrampelmeyer, Liquidity in the FX market: measurement, commonality and risk premiums (SNB WP 2010-03)](https://www.snb.ch/en/publications/research/working-papers/2010/working_paper_2010_03)
- [Same paper, EPFL copy](https://infoscience.epfl.ch/record/141852/files/SSRN-id1447869%5B1%5D.pdf)
- [Van Tharp, market type classification (newsletter archive)](https://vantharp.com/Tharps-Thoughts/685_June_11_2014.html)
- [NexusFi, market type classification for adaptive trading](https://nexusfi.com/a/strategies/market-type-classification-adaptive-trading)
- [Harbourfront, regime classification framework (Azizi 2026 ETF study)](https://harbourfronts.com/regime-classification-framework-mean-reverting-trending-markets/)
- [QuestDB, market regime detection using HMMs (glossary)](https://questdb.com/glossary/market-regime-detection-using-hidden-markov-models/)
- [Fractal Cycles, trending vs mean-reverting regime detection](https://fractalcycles.com/guides/market-regime-detection)
- [Volatility Box, volatility regimes explained](https://volatilitybox.com/research/volatility-regimes-explained/)
- [Thomas-quinn7/market-regime-detection (look-ahead-free Markov switching, GitHub)](https://github.com/Thomas-quinn7/market-regime-detection)

Trend persistence and technical rule profitability by era
- [Safari & Schmidhuber, Trends and reversion on time scales from minutes to decades (arXiv 2501.16772)](https://arxiv.org/pdf/2501.16772)
- [Schmidhuber, Trends, reversion and critical phenomena (arXiv 2006.07847)](https://arxiv.org/pdf/2006.07847)
- [Hsu, Taylor & Wang, Technical trading: is it still beating the FX market? (2016, SSRN 2765673)](https://technicalanalyst-cdn-1.s3.eu-west-2.amazonaws.com/wp-content/uploads/2016/04/13144511/SSRN-id2765673.pdf)
- [Same paper, SSRN page](https://papers.ssrn.com/abstract=2765673)
- [Neely & Weller, Technical analysis in the foreign exchange market (St Louis Fed WP 2011-001)](https://ideas.repec.org/p/fip/fedlwp/2011-001.html)
- [Neely, Weller & Ulrich, Lessons from the evolution of FX trading strategies (JBF 2013)](https://ideas.repec.org/a/eee/jbfina/v37y2013i10p3783-3798.html)
- [Bajgrowicz & Scaillet, Technical trading revisited: false discoveries, persistence tests and transaction costs (JFE 2012)](https://bashtage.github.io/kevinsheppard.com/files/teaching/mfe/advanced-econometrics/Bajgrowicz_Scaillet.pdf)
- [Same paper, EconPapers](https://econpapers.repec.org/RePEc:eee:jfinec:v:106:y:2012:i:3:p:473-491)
- [Daniel & Moskowitz, Momentum crashes (NBER w20439)](https://www.nber.org/system/files/working_papers/w20439/w20439.pdf)
- [Baz et al., Dissecting investment strategies in the cross section and time series (CME copy)](https://www.cmegroup.com/content/dam/cmegroup/education/files/dissecting-investment-strategies-in-the-cross-section-and-time-series.pdf)
- [Hurst, Ooi & Pedersen, A century of evidence on trend-following investing](https://www.researchgate.net/publication/318390566_A_Century_of_Evidence_on_Trend-Following_Investing)
- [Revisiting the structure of trend premia (arXiv 2510.23150)](https://arxiv.org/pdf/2510.23150)
- [The science and practice of trend-following systems (arXiv 2607.19497)](https://arxiv.org/pdf/2607.19497)

NNFX
- [No Nonsense Forex flow charts PDF](https://nononsensetrader.com/wp-content/uploads/2021/02/No-Nonsense-FOREX-Flow-Charts.pdf)
- [VP, Forex volume indicator: you will need one (nononsenseforex.com)](https://nononsenseforex.com/indicators/forex-volume/)
- [frzsoftware, NNFX strategy guide and indicator mapping](https://www.frzsoftware.com/product/no-nonsense-forex-strategy-nnfx/)
- [TradingView, Strategy NNFX Tester (chrisfraser05)](https://www.tradingview.com/script/yveRmB4r-Strategy-NNFX-Tester/)
- [TradingView, NNFX Baseline, QQEs Fast C1, Slow C2, ATR, Volume and Exit](https://in.tradingview.com/script/hoqTnCGd-NNFX-Baseline-QQEs-Fast-C1-Slow-C2-ATR-Volume-and-Exit)
- [TradingView, No Nonsense NNFX VP Strategy for Back Testing](https://www.tradingview.com/script/wmJpD8xR-No-Nonsense-NNFX-VP-Strategy-for-Back-Testing-jh/)
- [TradingView, NNFX scripts listing](https://in.tradingview.com/scripts/nnfx/page-3/)
- [myfxbook, The Real NNFX discussion (system deleted)](https://www.myfxbook.com/community/trading-systems/real-nnfx/2028808,1)
- [babypips, My first forex experience (NNFX), page 6](https://forums.babypips.com/t/my-first-forex-experience-nnfx/495320?page=6)
- [babypips, NNFX no nonsense forex thread](https://forums.babypips.com/t/nnfx-no-nonsense-forex/262850?page=2)
- [NNFX Algo Tester, included indicators](https://nnfxalgotester.com/help/included-indicators/)
- [NNFX Algo Tester, how do I build my algorithm](https://help.nnfxalgotester.com/knowledgebase.php?article=52)
- [stfl/backtestd-expert (MT5 NNFX EA, GitHub; cloned and read)](https://github.com/stfl/backtestd-expert)
- [rahuljugnarain/mt4-indicator-backtest (GitHub; cloned and read)](https://github.com/rahuljugnarain/mt4-indicator-backtest)
- [goncaloe/nnfx-backtest-c1 (GitHub)](https://github.com/goncaloe/nnfx-backtest-c1)
- [pedrofsantoscom/nnfx-backtest (GitHub)](https://github.com/pedrofsantoscom/nnfx-backtest)
- [Stonehill Forex, Cross Roads as a confirmation indicator (2025)](https://stonehillforex.com/2025/03/cross-roads-as-a-confirmation-indicator/)
- [Stonehill Forex, Waddah Attar Explosion as a volume indicator (2022)](https://stonehillforex.com/2022/02/waddah-attar-explosion-as-a-volume-indicator/)
- [Stonehill Forex, Trend continuation as a confirmation indicator (2022)](https://stonehillforex.com/2022/12/trend-continuation-as-a-confirmation-indicator/)
- [forex-station, No Nonsense Forex indicators thread (fetch refused)](https://forex-station.com/no-nonsense-forex-indicators-t8474695.html)
- [Forex Factory, No nonsense Forex VP thread (fetch refused)](https://www.forexfactory.com/thread/886311-no-nonsense-forex-vp?page=4)
- [Medium, Testing overload: NNFX in LEAN improved (fetch refused)](https://mirco-kahle.medium.com/testing-overload-nnfx-in-lean-improved-bf1cbe913c9c)
- [Didi Index indicator review (forexcracked)](https://www.forexcracked.com/forex-indicator/didi-index-indicator-review/)
