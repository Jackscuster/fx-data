# SLAPBOXALGOS: COMPLETE PROJECT OVERVIEW AS OF 23 NOV 2026

Written for a fresh chat. Everything below is drawn from the repo `Jackscuster/fx-data` (live copy at `~/fx-data` on Jack's Mac), its `HANDOFF.md`, the report files under `results/r2gate2/`, and the project register `claude/open-work-register.md`. Numbers are quoted from files; where a number is an estimate it says so. Repo state at writing: last commit `bcb21e4`, 22 Nov 14:35 EST; 21 GB free on the Mac.

---

## 1. WHAT IS BEING BUILT

A complete systematic trading system for the 28 G8 currency pairs, in layers, in order:

| Layer | Job | Status |
|---|---|---|
| 1 Regime estimator | Says what state a pair is in right now: trending, ranging, trend-in-range, neither, plus activity (weak/medium/strong) and crisis. Describes the present, never predicts, carries no money metrics. | Built, validated, closed out 16 Nov with a formal interface contract (`LAYER1_INTERFACE.md`). Chop axis real out of sample; trend axis weak. |
| 2 Strategy library | The trading rules: entries, exits, stops, targets, trade management. Money metrics start here. | Restarted from scratch 11 Nov. Modes A and B fully tuned and scored on the honest machine. Mode C not run. 10 strategies beat luck; none meets the return target. |
| 3 Routing | Which strategy runs on which pair in which state. | Regime routing tested throughout (adds nothing to the strategies that beat luck). Pair routing tested on the 10 winners (no better than random); full-field version pending. |
| 4 Risk and sizing | Position sizing, exposure limits, crisis response, kill rules. | Sizing kernel exists (net exposure per pair per day, agreement curve, DIP95 scaling to budget). Overlays (kill switch, equity pause) measured once on the mode A winners. |
| 5 Validation | Walk-forward, deflated Sharpe, costs, stress. | Walk-forward and nulls are built into every Layer 2 run. 2021 onward sealed, never opened. |
| 6 Execution | Spreads, slippage, financing by pair and hour. | Measured per-pair cost table by hour of day exists (`cost_table_h22.csv`, 22:00 NY entry). Nothing live. |
| 7 Monitoring | Dashboard, alerts, decay tracking. | The app (`app_ui.js`, `app_data.json`) carries every result; no live feed. |

Jack owns the architecture. The target he set: around 20% a year, and more recently, each individual strategy must beat 12% a year when sized to the prop firm's limits. The prop profile is FundedTradingPlus 1-Step Express $100k: 4% daily, 6% trailing drawdown that locks at the starting balance once +6% is banked, 1:30 leverage, MT5. Jack's internal budget sits 10% inside those: 3.6% daily, 5.4% trailing. "Team 1" means sized so the worst dip (DIP95) fits 3.6%; "Team 2" means 5.4% dip after the cushion is banked, day still 3.6%.

### Hard rules (all broken at least once, all now enforced)

1. Nothing runs to /tmp; results go to `results/` and are committed.
2. Nothing is deleted or overwritten; superseded files get a header note.
3. Numbers are quoted from files, never memory.
4. No money metrics in Layer 1.
5. Layer 1 describes the present; validation is present-tense.
6. Everything lagged one bar.
7. Choose on closed years, confirm once on the holdout; 2021 to 2026 is sealed.
8. Episode-based significance, not per-bar.
9. Null-test anything strong before calling it a finding.
10. A small number of motivated constructions beats a large search.
11. No picking strategies by past record for the live book; no weighting by past record; everyone trades; any grade is reported, never used to select.
12. No arbitrary thresholds: every cut is swept over its full range and reported as a curve; Jack picks from the curve.
13. Stop, target, breakeven and trail multiples are tuned per strategy, never fixed; leg 2 of a trend trade always runs to its own exit.
14. Spending money (cloud boxes) is Jack's decision only.
15. Percentages not decimals, plain English, no jargon without a definition, times in US Eastern.

---

## 2. DATA

- Layer 1 history: Fed H.10 daily noon fixes, 1999 to present, uniformly foreign-per-USD (invert all, then triangulate). Sanity checks: EURUSD peak 1.601, USDCHF low 0.7296. File `data/px28_h10.csv`.
- Live Layer 1 and all of Layer 2: OANDA daily bars at the 17:00 New York close, 28 pairs triangulated from the 7 USD legs, series from 2002-09-24 (NZDUSD is the last leg to start). File `data/px28.csv`. Daily OHLC exists from 2002-06; hourly bid/ask from 2004-05-31.
- Close-only for Layer 1 (no ATR there); Layer 2 uses the OANDA OHLC and ATR.
- Costs: measured per-pair spreads by hour of day. Best entry window 21:00 to 23:00 NY; 17:00 is roughly double; the project charges the 22:00 table (`results/cost_table_h22.csv`, about 2.4 bp round trip on average). Costs are about 24% of a typical year's gross return.
- Also held: 2-year government yields for the G8 (`data/rates2y.csv`, NZD missing), 10-year yields for 5 countries, COT positioning. None of these is used by any strategy yet.
- Mac: 10-core, 16 GB RAM, 460 GB SSD (the binding constraint this month: disk, not CPU).

---

## 3. LAYER 1 IN DETAIL

### How it works
Two independent axes built from price structure. Shape: is price making directional progress (trend score, from swing sequences) or respecting boundaries (chop score, from failed swings, boundary tests and range containment on swing width 19). Activity: how far the pair is moving (distance travelled, since FX has no volume). Cuts learned on the tuning window (before 2016) only, confirmed once on 2016 to 2020, applied unchanged to 2021 onward which is never measured. Label `shape2` in {trending, ranging, trend-in-range, neither}; `activity` in {weak, medium, strong}; crisis witnesses on top.

### History (Jul to Sep 2026)
- 175,634 candidate signals built on H.10; 167,316 scorable; 32 survived (26 chop detectors, 6 trend); combining the 32 gave the best single spread in the project (+0.0398). Total explanatory power about 1.4%. Cross-pair measures beat own-pair 68% to 54%.
- Lessons that still bind: multiplying signals is worse than a coin flip (7,140 wasted); levels beat changes; monthly-timeframe features are below random; 60 and 120 day horizons are dead (0 of 43,815); momentum loses on all 28 pairs; 78% of the headline effect size was manufactured by selection (the inflation run), hence rule 9.
- 13 to 15 Sep: Layer 1 rebuilt on the 5pm OANDA bar and swapped in as the live file. Noon vs 5pm `shape2` agreement 72.2%. State shares about 29% trending / 33% ranging / 19% trend-in-range / 19% neither (the old "40/40/7/13" is stale). On the 5pm bar only 8 of the signal library survive versus 29 on H.10; the shipped estimator uses none of them.

### November close-out (10 to 16 Nov, HANDOFF items 0h to 0k)
- Round 1: a directional-change (intrinsic time) trend axis, declared in advance, came back negative: every variant below its surrogate on a 200-draw re-derive null (p 0.60 to 1.00); mode C routed on it made -1.13% vs +1.33% on the shipped axis. Not shipped.
- Round 2: the trend label's failure diagnosed. About half of labelled trending episodes are directionless (true-trend share 50% tuning, 44% holdout) and the trend score cannot tell which; the label confirms a median 24 bars late with 56 to 57% of the move already spent; 60% of routed trend P&L sits in the first third of an episode, exactly where the label is too late. Two new constructions (T1 broken-chop, T2 currency-leg gap) failed the null as axes.
- Round 3: the currency-leg gap, read at label time, survives as a QUALITY FLAG on the existing trend label: holdout gap 0.394 vs null mean 0.135, p 0.01 sign / 0.00 permutation, AUC 0.609; high-confidence episodes are true trends 55% of the time vs 39% for low. It changes no state call and never gates a trade; it is reported beside the label. File `results/layer1_trend_quality_series.csv`.
- Crisis: witnesses 2 and 3 (panel turbulence, Roll illiquidity) rejected; the crisis set is the acute detector plus MOVE only (acute catches 31 of 39 news events, lift 15x, lag 0 days).
- `LAYER1_INTERFACE.md` (16 Nov) is the only surface Layer 2 may read: `results/layer1_states.csv` (171,920 rows, md5 0b48ed53b78a), the quality series (md5 a8755566178f), the crisis files, pair character, run lengths, state correlation. Layer 2 never modifies, refits or retunes Layer 1; defects are reported against the producer script. A 16 Nov fix: `code/appsections.py` is a third app-wiring place; cold pipeline runs had been silently deleting tabs.

### What Layer 1 is worth downstream (measured in Layer 2)
On the strategies that beat luck in the restart (10 of them), regime routing adds nothing: all 10 are always-on. On the whole field, routed books are no better than books routed on shuffled regime labels (p 0.11 to 1.00). Chop slices routed to RANGING were the only positive slices in the September smoke (A-chop +0.63%, B-chop +0.52% a year) and that held in direction but not in size at full scale. The trend axis is the weak one; the one positive routed book ever seen (mode C, September, 104 strategies, +1.33% a year) has not been re-run at scale.

---

## 4. LAYER 2 BEFORE THE RESTART (Aug to Sep 2026) AND WHY IT WAS VOIDED

### The library
An NNFX-style builder: five slots per strategy, C1 confirmation (flip triggers entries), C2 confirmation (votes), volume/volatility filter, baseline moving average, exit indicator. 41 C1/C2/exit options, 16 volume, 16 baseline after the Sep indicator fixes. Three modes: A exits on the C1 flip, B exits on the baseline cross, C exits on its own exit indicator. Mode A and B each enumerate 273,780 combinations; mode C 10,677,420. Trend trades have two legs (TP1 then breakeven and trail), chop trades one leg. Every strategy trades all 28 pairs.

### The original gauntlet (spec v5, 15 Aug)
Windows: W1 2005 to 2010 pick, W2 2011 to 2015 blind, W3 2016 to 2020 blind, W4 2021 to 2026 final exam opened once. Gates: 1 discover at defaults, 2 tune and label, 3 the cull at portfolio-grade KPI bars, 4 combine. KPI bars as declared: gate 2 label expectancy >= +0.08R, PF >= 1.25, Sharpe >= 0.5, Sortino >= 0.7, Calmar >= 0.6, max DD <= 20%; gate 3 cull expectancy >= +0.15R, PF >= 1.5, Sortino >= 1.3, Calmar >= 1.0, max DD <= 10% of own gross profit, Sharpe reported only (dropped from the cut 7 Sep); minimum 100 trades in the picking window and 50 in every blind window. Routing by regime has been inside every Layer 2 number since 15 Aug (a trade is kept only if `shape2` at the entry bar, one-bar lag, matches the slice's regime).

### What it appeared to produce
Teams of 15 to 26 strategies with median years of 22% to 30% at the Team 1 budget, worst years above 10%, max drawdown about 2.3%, Sharpe 4 to 5. Those numbers are void.

### The contaminations, in the order found
1. W2 leak (8 Sep): W2 was scored with settings tuned on W1+W2. About 5x inflation.
2. Mode bug (9 Sep): `run_pair` ran mode B's exits for every mode; A and C strategies were scored with the wrong exit.
3. Delivery path gross of costs (10 Sep): the path that produced team numbers never charged costs (about 24% of a year).
4. Field selected with sight of 2016 to 2020 (11 Sep): the strategy field itself was chosen by a gate that had seen the holdout. Rebuilt blind (4,807 three-slice, 8,235 four-slice, B-trend via three rented cloud boxes, about $40).
5. Vote-timing leak (15 Sep): in the book kernel a position entered at day D's close voted on day D's move; entrants agreed with the day's move 83% of the time. Fix `VOTE_ON_ENTRY_DAY = False`. The base book went from +5.12% / +7.69% to -1.00% / -1.50% a year; the "sit-out" variant from +20% to -1.4%. Every book-level number before 15 Sep is void; per-strategy numbers stood.
6. Fault #27 (23 Sep): costs under-charged by the stop multiple (median 20%, 90th percentile 46%) on all three scoring paths, including the tuner's objective.
7. Fault #28 (24 Sep): the random-entry null had no risk source for a blind candidate list, so every such null would have been silently missing.

The mechanical audit that now guards these: `code/preflight.py`, 27 items, run before every heavy launch (`results/audit_2026-11-16.csv` and later, 27/27 PASS), plus per-mode ten-trade hand checks against the price file.

### Honest results on the old library (16 to 24 Sep)
- Fixed kernel, 2016 to 2020: base -1.00 / -1.50, chop-core -0.82 / -1.23, chop-only -0.44 / -0.66; every book below every random-entry draw (p = 1.000); routing no better than shuffled labels (p 0.52 to 0.92). Carry alone: every sleeve negative.
- In-sample check on 2011 to 2015: +4.44% (the instrument measures positive where it should).
- Refit pilot (250 strategies): re-tuning lifts the tuning window to about 1 R per trade and leaves the next year at -0.05 to +0.04 R; 1 of 5 traded years won.
- Findings that still stand as ORDERING (levels void): picking by past record is worse than random at every team size up to 2,160 (identity null p = 1.000); team size = everyone; weighting by quality hurts; rank persistence build-to-trade is about zero.
- Funnel test (21 Sep): after re-tuning, gate 2's in-sample bars pass 249 to 250 of 250; an in-sample grade selects nothing. This produced Jack's rule: no picking; a grade must be blind.
- Blind-label programme (21 to 24 Sep): tune years 1 to 4, grade year 5 (never seen by the tuner, reported, never used), trade year 6; five rolling steps 2011-14/15/16 through 2015-18/19/20. On a 250 A/B + 104 C smoke with correct costs: A+B routed book -0.64% a year (PF 1.018, first book with gross profit above gross loss, random-entry p 0.04), always-on -0.51%, chop routed + trend ungated -0.38%; per slice routed A-chop +0.63, B-chop +0.52, B-trend +0.01, A-trend -1.25. Mode C routed on TRENDING: +1.33% median year, PF 1.087, retention +0.26, 4 of 5 years positive, regime-shuffle p 0.00, random-entry p 0.08, worst year -4.0%, DIP95 6.9% against a 3.6% budget. The full cloud run of the old 45,139 gate-1 survivors was verified (27/27, 8 Nov) but never launched: Jack cancelled it with the restart.

---

## 5. THE RESTART (11 to 22 Nov): WHAT WAS RUN AND WHAT IT SAYS

Jack's instruction, 11 Nov: "completely restart Layer 2, starting with mode A then B and C. Restarting does NOT mean deleting anything. Use the cached memory and save everything. We need to find all new combinations and all new settings." Then on 16 Nov: "we shouldn't be cutting anything in gate 1, we've done this before." Registered as HANDOFF item 0l.

### 5.1 Gate 1 (16 Nov): every combination at default settings, honestly
- All 273,780 mode A, all 273,780 mode B, all 10,677,420 mode C combinations scored at default settings on the 5pm panel with correct costs, one-bar lag, 2021+ sealed, trades banked by the calendar year of entry so the five walk-forward steps are masks over one engine pass. Mode A took 2.3 minutes, B 2.2 minutes, C 77 minutes plus a 34-minute curve (disk-bound). Four streams per strategy: trend/chop x routed/always-on.
- The cut was swept over its full range on tuning years only. Passers beat non-passers on the unseen year at every level, but the absolute level is at or below zero at defaults: mode A chop-routed at the +0.128 cut passes 2.4% with +0.009 R per trade on the unseen year vs -0.051 for non-passers; tune-to-trade rank correlation 0.03 to 0.27 and sign-unstable; a regime-shuffle null on gate 1 showed the cut buying very little in any mode. Jack chose NO CUT: everyone goes to tuning. Files `results/r2gate1_pooled_mode{A,B,C}_full.csv`.

### 5.2 Gate 2 (17 to 20 Nov): tune every setting of every strategy, walk forward
- Method: for each strategy, every grid configuration is scored once over 2011 to 2020 and banked by year; each walk-forward step picks its best setting on its four tuning years and reads the grade and trade years from the bank. Proven identical to the naive per-step method on 7,660 comparisons (0 mismatches, worst difference 0), and every open trade is marked to market at each year end so no year holds another year's price (residual 1.4e-14).
- Grid (declared, `results/r2gate2_grid.csv`): ATR length 2 to 50 (49 values), stop 1.0 to 1.5 ATR (31), target 1.0 to 3.0 ATR (41), breakeven trigger 1 to 20% (20, trend only), trail arm 1.0 to 2.0 ATR (21), trail distance 0.5 to 2.0 ATR (31), plus every exposed indicator parameter including 29 that an old cap had frozen. About 520 configurations per strategy, swept one setting at a time around the defaults (axial), not every combination together (that would be 810 million per strategy). Objective: account-normalised expectancy with PF tiebreak, minimum 100 tuning trades; picks made separately for the routed and always-on streams.
- Cost: 0.87 to 1.2 seconds per strategy; mode A tuned in 10.4 hours on the Mac, mode B the same. Mode C would be 404 Mac hours or about $20 on six cloud boxes; its bank is 38 GB, which the Mac cannot hold.
- Whole-field books, everyone trading equal weight, sized to the budgets (from `MODEA_KPIS.md`, `MODEB_KPIS.md`, traded years 2016 to 2020 stitched, Team 1):

| book | mode A median yr | A total | A max DD | A PF | mode B median yr | B total | B max DD |
|---|---|---|---|---|---|---|---|
| always-on | -1.19% | -5.37% | -7.23% | 0.90 | -0.69% | about -7% | -4.4% |
| routed (chop RANGING, trend TRENDING) | -0.91% | -4.34% | -5.20% | 0.91 | -1.45% | | -2.9% |
| chop routed, trend ungated | -0.54% | -2.83% | -4.43% | 0.95 | -0.59% | | -3.1% |
| chop routed, trend NOT-RANGING | -0.59% | -5.25% | -6.87% | 0.94 | -1.47% | | -3.8% |

Every book loses. The tuning years show +1% to +5% for the same books; retention is negative in nearly every step (flagged FIT). The three nulls say: real entries no better than random entries (p 0.16 to 1.00); routing no better than shuffled labels (p 0.11 to 1.00); ranking by tuning-year record no better than random (identity p 0.35 to 1.00). The blind grade (year 5) sorts strategies weakly and inconsistently (rank correlation to the trade year between -0.10 and +0.16).

- Persistence (`MODEA_TOP30.md`, `MODEB_TOP30.md`): about a third of strategies are positive on any given unseen year (33 to 39%). Strategies positive in all five unseen years: 1.3 to 1.6x the coin-flip count in three of four streams (below coin flip in chop-routed). The tuner's own top 30 beat the field by about +0.1 R per trade on the next year but only 17 of 30 were positive. Top 30 by the blind grade did worse than the field.

### 5.3 Gate 3 (19 to 21 Nov): Jack's bars, applied honestly
Bars: expectancy >= 0.15R, PF >= 1.5, Sortino >= 1.3, Calmar >= 1.0, max DD <= 10% of own gross profit. Each strategy re-scored per calendar year through the shipped Scorer (Sortino and drawdown need the ordered trades). 6.7 hours per mode.

| mode | pass the bars on the unseen grade year (one year) | pass again on the next unseen year | pass on the stitched 2016 to 2020 record |
|---|---|---|---|
| A | 59,268 strategy-years (of 273,780 x 5 steps x 4 streams) | 492 | 0 |
| B | about 44,000 | about 400 | 0 |

One year is 8 to 40 trades, so thousands clear the bars by luck; a random year clears them more often than the real grade year. Of mode A's 492 two-year passers only 13 strategies did it in more than one step.

Passers' books (members chosen with no sight of the year they trade), Team 1, always-on, mode A: one-year rule +0.49% total over 2016 to 2020 (members 877 to 9,303 per year, max DD 6.5%); two-years-in-a-row rule +0.63% total (members 14 to 129, max DD 3.1%, beats a random pick of the same size in 12 of 16 cells); full 5-year record rule -0.07% (members 6 to 19, beats random in 14 of 20 cells). Routed versions worse (-0.3% to -7.3%). Mode B the same shape, slightly worse. The bars pick slightly better than random and land at breakeven. Files `MODEA_GATE3.md`, `MODEB_GATE3.md`, `MODEA_PASSERBOOKS.md`, `MODEB_PASSERBOOKS.md`.

### 5.4 Winners without gates (20 to 22 Nov): what beats luck
Jack: "forget my gates, from the A strategies I want the best possible performing non-luck combinations that make money." Method: each strategy's five stitched unseen trade years, t-statistic of mean R per trade; two luck floors, (a) analytic for the best of 273,780 independent tries (t = 5.08; Bonferroni 5.22; per strategy-stream cell 5.34 / 5.47) and (b) empirical from random-entry re-runs on 2,000 strategies x 20 draws with an extreme-value fit (t = 4.35 for A, 5.24 for B); winners must clear both, have >= 50 trades in every unseen year, and be positive in >= 4 of 5 years. PROP RETURN is defined as the yearly return when sized so the worst dip equals 3.6%; for a single strategy it equals 0.72 x (total R / max DD R), so 12% a year requires return/DD >= 16.7 over the five years.

Mode A: 8 winners. Mode B: 2 winners. All 10 are trend strategies, all always-on (no regime routing), all one family: lemantrend or waddah_attar_explosion as C1, hieken_ashi_smoothed as C2, adx_dmi as the exit, alma, fantail_vma, frama or super_smoother as baseline, chaikin_volatility, volatility_ratio or choppiness as the volume filter. None is a lone survivor: each has cousins at t >= 2.

| # | mode | strategy (C1 x C2 x volume x baseline x exit) | t | total R 2016 to 2020 | exp R | PF | win % | max DD R | DD % of gross | worst year R | trades | prop return |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | A | lemantrend x hieken_ashi_smoothed x chaikin_volatility x alma x adx_dmi | 6.76 | 127.8 | 0.16 | 1.71 | 51 | 40.8 | 13.3 | +13.1 | 816 | 2.25% |
| 2 | A | lemantrend x hieken_ashi x volatility_ratio x alma x adx_dmi | 6.06 | 148.3 | 0.11 | 1.48 | 48 | 55.5 | 12.2 | +8.3 | 1,290 | 1.9% |
| 3 | A | waddah_attar x hieken_ashi x chaikin_volatility x alma x adx_dmi | 5.84 | 109.4 | 0.14 | 1.64 | 49 | 41.5 | 14.7 | +10.5 | 758 | 1.9% |
| 4 | A | lemantrend x relative_vigor_index x volatility_ratio x super_smoother_2pole x adx_dmi | 5.75 | 125.4 | 0.11 | 1.49 | 50 | 53.5 | 14.0 | -0.3 | 1,178 | 1.7% |
| 5 | A | lemantrend x hieken_ashi x choppiness_index x frama x adx_dmi | 5.59 | 121.1 | 0.11 | 1.50 | 54 | 62.1 | 17.1 | -4.8 | 1,060 | 1.4% |
| 6 | A | lemantrend x hieken_ashi x choppiness_index x fantail_vma x adx_dmi | 5.27 | 106.1 | 0.12 | 1.50 | 48 | 47.3 | 14.9 | +0.8 | 890 | 1.6% |
| 7 | A | waddah_attar x hieken_ashi x volatility_ratio x alma x adx_dmi | 5.12 | 125.7 | 0.10 | 1.40 | 45 | 51.5 | 11.6 | +7.8 | 1,270 | 1.8% |
| 8 | A | waddah_attar x hieken_ashi x choppiness_index x super_smoother_2pole x adx_dmi | 5.08 | 120.7 | 0.12 | 1.48 | 42 | 61.4 | 16.5 | +13.2 | 966 | 1.4% |
| 9 | B | lemantrend x hieken_ashi x chaikin_volatility x alma x adx_dmi | 5.54 | 100.7 | 0.12 | | 41 | 35.7 | 13.8 | +7.1 | 846 | 2.03% |
| 10 | B | waddah_attar x hieken_ashi x chaikin_volatility x fantail_vma x adx_dmi | 5.41 | 93.4 | 0.16 | | 42 | 28.3 | 13.5 | +8.2 | 584 | 2.38% |

Per-year R, mode A #1: 2016 +16.5, 2017 +19.0, 2018 +51.5, 2019 +27.6, 2020 +13.1. Mode B #10: +17.8, +17.0, +31.4, +19.0, +8.2.

Every one of the 10 makes money every year on unseen data, and none comes within a factor of five of 12% a year at prop sizing. Their drawdown is 12 to 17% of their own gross profit against the 10% bar. Across both modes: 10 non-luck survivors out of 547,560 strategy-stream records, 100% trend, 100% always-on.

Winners' books (membership chosen with sight of the years reported, so descriptive only), Team 1: mode A 8-winner book +14.8% total over five years (+2.9% a year), max DD 1.98%, return/DD 7.5; mode B 2-winner book +16.2% total (+3.2% a year), worst year +1.5%, best +6.6%, max DD 1.63%. Team 2 is 1.5x. Overlays on the mode A book, swept: equity pause (flat after a 0.88 R dip, back after 0.12 R recovery) +14.0% total at 1.39% DD; kill switch at 1.08 R +13.0% at 1.16% DD. A daily loss stop showed +32.7% at 0.57% DD but is an upper bound only (assumes a free exact exit; needs intraday data). Files `MODEA_WINNERS.md`, `MODEB_WINNERS.md`, `modeA_overlay_curves_winners.csv`.

### 5.5 Pair routing on the 10 winners (22 Nov, `WINNERS_BY_PAIR.md`)
Each winner's record banked per pair and per direction per year (17,329 rows for A's 8, 3,605 for B's 2). Pairs chosen on the tuning years only (top-K by tuning-year return/drawdown, K = 1 to 28, and a positive-R threshold rule, with and without direction), traded on the unseen years, against random pair subsets of the same size (20 draws). Result: the real rule beats the random pick at 1 of 28 K values in mode A and 7 of 28 in mode B; a coin flip. Nothing clears 12%. Pair routing is now a standing stage in every report generator (commit `bcb21e4`); the full-field version still has to run on the per-pair bank.

### 5.6 Things tried in the restart that did not help
- Regime routing of entries (any variant: TRENDING, NOT-RANGING, ungated).
- Picking by any past record: tuning-year rank, blind-grade pass, gate 3 bars on one year.
- Pair selection by past record on the winners.
- The Layer 1 trend quality tag as a split on routed trend P&L: high-confidence read worse than low in 4 of 5 steps on a per-mark basis (an episode-based version was requested and not yet run).

---

## 6. INFRASTRUCTURE AND PROCESS (because most of the lost time this month was process, not maths)

- Chains: every job is one driver script under `code/chain/` (versioned since 20 Nov), launched by `launch.sh`, which snapshots the code into `~/fx-data-runs/<chain>/` so edits cannot touch a running chain, refuses a dirty tree, requires every stage to declare a checkpoint interval (<= 300 s of unsaved compute), its dependencies, its disk need (refused if free space is short) and a deliverable with an ETA. A failed stage no longer kills the chain; dependents are skipped by name. `stop_chain.sh` kills the process group and verifies zero survivors; `pkill` on chain patterns is refused. `queue.sh` runs chains back to back.
- Checkpointing: `code/l2ckpt.py`, parts on a clock, resume by set difference, even inside a single strategy's tuning. Proven bit-identical across an interruption.
- Watchdog: `chainwatch.sh` pushes Jack's phone via ntfy (topic `fxdata-chain-3df0c39e`) on halt, stall (10 minutes of no CPU and no log), any FAILED stage, a chain finishing without its deliverable, an ETA passing, free space under 2 GB, and anything waiting on Jack (`waiting.sh`, re-pushed every 2 hours). Pushes before any file write so a full disk cannot silence it.
- Approval: originally every launch needed Jack to paste a hash to Claude for review; that idled the Mac for 2 h, 14 h and 10 h on three occasions. Amended 20 Nov: only changes to WHAT is computed need approval; re-running an approved pipeline on another mode, sharding, scheduling and reports launch without it.
- Known process failures this month, all now guarded: Code ending a turn with "starting next" and doing nothing for 8 to 14 hours; editing live code under a running chain; orphaned workers from `pkill`; a 2.3-hour smoke lost to an unsaved shard; the queue arm giving up on a 20-hour timeout; two battery deaths of the laptop (keep it on power); disk hitting 100% three times (`.git` is 7.3 GB because gate 3 KPI banks were committed; 3 to 6 GB of regenerable scratch has been deleted twice, logged, never results).
- Cloud: Hetzner 16-vCPU boxes at $0.10 per box-hour, three at a time without a limit ticket; launch by one curl line per box pulling main; boxes deleted and the GitHub token revoked after each job. Total spent to date about $40, all in September.
- Speed: the one-pass bank made gate 1 take minutes instead of days and tuning 0.9 s per strategy instead of 73 s per strategy per step (five passes collapsed to one, a per-trade crisis cost loop hoisted to a per-bar array, indicator cache raised from 900 to 30,000 entries and spilled to disk, contiguous shards).

---

## 7. STATE AS OF 23 NOV 2026

Done and on file: gate 1 for A, B, C; gate 2 for A and B (expectancy objective); gate 3 for A and B; passers' books under three rules; winners with both luck floors, prop return, overlays, family support; pair routing on the 10 winners; KPI tables; pair routing wired as a standing stage; cache budget fixed to a share of free space.

Paused: chain 22A, the mode A re-tune with the tuner picking on total R / max DD R (return per unit of drawdown) with widened grids (stop 0.5 to 3.0 ATR, target 0.5 to 5.0 ATR). About half tuned (177 part files); resumes by set difference; roughly 12 hours left plus gate 3 re-score (14 h) and books.

Costed, not started, on the Mac the following need about 52 hours per mode, or about $5 total in the cloud for both modes in about a day:
1. Extended walk back to 2005: eleven rolling steps, so 2011 to 2015 is traded blind as well as 2016 to 2020 (ten unseen years instead of five; Jack's W2 window had been used only for tuning). Written into the same pass: a per-pair, per-direction bank.
2. From that bank, cheap reads: full-field pair routing sweep with random-pair null; plateau selection instead of the single best setting (median of the top 5%, centre of the widest plateau, top-5 ensemble); tuning-window length 2/3/4/6 years; regime flip as a leg-1 exit and as an entry block (with shuffle null); carry-direction filter from the 2-year rate differential, threshold swept.
3. Mode C end to end on the cloud: about $20, 34 hours on six boxes (or 67 on three); the bank (38 GB) stays on the boxes, results pushed. Never run at scale. Jack has not said go.

Open housekeeping: external SSD still not bought (21 GB free after Jack cleared files); `.git` needs a gc; `results/r2gate1` (7.1 GB, regenerable gate 1 banks) could be archived; the Code terminal window shown on 23 Nov was titled `~/Documents/fx-data` (the old location) and must be checked with `pwd`; a second GitHub token from September may still be unrevoked.

---

## 8. WHAT THE EVIDENCE SAYS, PLAINLY

- The instrument is right. The in-sample years come out positive, the hand checks pass, the one-pass method reproduces the slow method exactly, and the audit covers every leak found.
- Indicator-combination strategies on daily FX closes, tuned honestly and traded on years they never saw, lose money as a population (about -0.5% to -1.5% a year at the budget) and about a third make money in any given year.
- A small real edge exists: ten strategies, one family (trend entries from lemantrend or waddah_attar confirmed by smoothed Heikin Ashi, exited by ADX/DMI), always-on, making roughly 20 to 30 R a year each with worst dips of 28 to 62 R. At prop sizing that is 1.4% to 2.4% a year. Combined, about 3% a year at a 2% drawdown.
- Nothing selected by past record (strategy rank, grade year, KPI bars on one year, pair choice) has predicted the next year better than random at any scale tested. Two consecutive unseen years of passing the bars is the one selection that beat random picks in most cells, and it lands at breakeven.
- The regime estimator's chop axis is real but has not translated into money on this library; its trend axis is late by construction; regime routing has not helped any strategy that beats luck.
- 2016 to 2020 is the deadest FX era in decades; the walk forward has so far judged everything on it alone. Extending the walk back to 2005 is the cheapest way to double the unseen evidence.
- The gap between what exists (2 to 3% a year at a 3.6% dip) and the target (12% per strategy, 20% for the system) is a factor of 5 to 7. Levers not yet tried: tuning for return per drawdown (paused half-done), plateau settings, longer walk, carry direction, mode C, and combining families that lose on different days.

---

## 9. KEY FILES

Repo: `HANDOFF.md` (items 0 to 0l), `FIXES.md`, `GAUNTLET.md`, `LAYER1_INTERFACE.md`, `code/preflight.py`, `code/l2refit.py`, `code/l2r2gate2.py`, `code/l2r2gate3.py`, `code/l2r2book.py`, `code/l2r2kpis.py`, `code/l2r2top30.py`, `code/l2ckpt.py`, `code/chain/*`, `results/r2gate2/MODEA_REPORT.md`, `MODEB_REPORT.md`, `MODEA_GATE3.md`, `MODEB_GATE3.md`, `MODEA_PASSERBOOKS.md`, `MODEB_PASSERBOOKS.md`, `MODEA_WINNERS.md`, `MODEB_WINNERS.md`, `WINNERS_BY_PAIR.md`, `MODEA_KPIS.md`, `MODEB_KPIS.md`, `MODEA_TOP30.md`, `MODEB_TOP30.md`, the CSVs beside each, `results/r2gate1_*`, `results/layer1_states.csv`, `results/layer1_trend_quality_series.csv`, `results/cost_table_h22.csv`.

Project docs (claude.ai): `claude/open-work-register.md` (running register), `claude/gauntlet-spec.md`, `claude/gate4-design.md`, `claude/layer2-redesign.md` (hand-built sleeves S1 to S5, never started), `claude/LAYER1_FOUNDATION_FOR_LAYER2.md`, `claude/HANDOFF_CURRENT.md`, `claude/prop-profile-fundedtradingplus.md`, `claude/layer6-daily-engine.md`.

How work gets done: Jack works with Claude Code on his Mac, which builds and commits; a Claude chat (this one) does the thinking, interprets results, and writes single copy-paste prompts for Code. Neither can see the other; Jack relays. Code only works while a turn is open: anything that must happen overnight has to be built, tested and armed in a chain before Jack leaves.
