<!-- PROVISIONAL, added 2026-11-24. The winner list in this file is NOT SAFE.

Item 0b found that `mode?_winners.csv`, from which this report is built, writes
`R_<year>` from the GATE 3 KPI bank, which books each whole trade to the year it
was ENTERED. Gate 2's `win` array marks every trade to market at each year end,
which is this project's declared rule and the convention the staged build now
uses (item 8). The two disagree on 41 of 50 winner-years, median 1.01 R, largest
10.63 R, and on 35 of 50 trade counts by up to 11 trades.

CONSEQUENCE FOR THIS FILE: one winner's yearly t moves 4.116 -> 5.033 against a
floor that was set at 5.08, and another's years-positive moves 4 -> 5 against a
rule requiring 4 of 5. So the MEMBERSHIP of the list could have been different.
The broad conclusion -- that these winners are not distinguishable from luck at
a best-of-field floor -- does not reverse, and B1_WINNERS.md shows they do not
survive the six years they were never selected on either.

Nothing here has been regenerated, as instructed. See
results/nnfx/SCORER_DIVERGENCE.md and results/r2gate2/gate2_vs_gate3_peryear.csv.
-->

# MODE A — WINNERS, NO GATES

Generated 2026-11-22 14:35 by `code/l2r2winners.py`, read-only off the gate 2 bank and the gate 3 scoring. **Nothing is filtered before it is measured**: all 273,780 strategies are recorded on both unseen records, and the only cut is the LUCK FLOOR, which is a statement about chance rather than a preference about settings. Individual strategies first; the book last.


## 0. The number Jack buys: PROP RETURN

Yearly return when sized so the worst dip equals **3.6%** — max DD for a strategy, trade-year DIP95 for a book. Target **12% a year**.

For a strategy the arithmetic collapses to `0.72 x return/DD`, so prop return and return-per-drawdown are the same ranking and the 12% line is exactly **return/DD >= 16.67**.

**0 of 8 winners clear 12% at prop sizing.** Best is **2.25% a year** (return/DD 3.13 against the 16.67 needed) — short of the line by a factor of 5.3.


## 1. The universe, and the two unseen records

Per (strategy, stream), two records that the tuner never saw: the five stitched TRADE years 2016-2020, and the five GRADE years 2015-2019 as an independent second read. Each year uses the settings tuned before it — the walk forward as built.


**Observed t**, from `results/r2gate2/modeA_winners_t_observed.csv`:

| record | stream | n_finite | t_max | t_p99 | t_median |
|---|---|---|---|---|---|
| trade | ALL | 1,072,087 | 6.759 | 2.141 | -0.9992 |
| grade | ALL | 1,072,072 | 7.813 | 2.368 | -0.8046 |


The t-statistic is **exact and not stored**: `l2tune` computes `sharpe = mean/sd x sqrt(252)` on per-trade R, so `sd = mean sqrt(252)/sharpe` and the per-year sum of squares is `sd^2 (n-1) + n mean^2`; those sum across the five years, so the pooled t is recovered without re-scoring. Verified against direct re-scoring on 10 records, agreeing to five decimals.


**Three fields are NOT exact from the bank**, and each is named where it appears: stitched max DD (summed per-year, gate 3's own stitched recipe, an upper bound), stitched Sortino (the mean of the five per-year figures), and longest losing streak (needs the ordered trade list, which the Scorer discards).


## 2. The luck floors

**(a) Analytic**, from `results/r2gate2/modeA_winners_floor_analytic.csv`:

| basis | M | alpha | t_max_of_M | t_bonferroni |
|---|---|---|---|---|
| strategies, as Jack specified | 273,780 | 0.05 | 5.081 | 5.216 |
| strategy x stream cells, which is what is actually compared | 1,095,120 | 0.05 | 5.339 | 5.467 |


Both lines assume independent tries and normal t. FX trade R is fat-tailed, the 28 pairs overlap in time, and a strategy's four streams share settings — all of which inflate real t. **These lines are therefore optimistic**: clearing one is the weakest version of the question.


**(b) Empirical**, a per-strategy random-entry null, from `results/r2gate2/modeA_winners_floor_empirical.csv`:

| space | null_mean | null_sd | mu | sigma | n_blocks | block_size | M | expected_best | pct |
|---|---|---|---|---|---|---|---|---|---|
| t | -0.4091 | 1.02 | 3.226 | 0.1426 | 20 | 7,844 | 1,095,120 | 4.013 | 4.354 |
| expectancy_R | -0.02162 | 0.0722 | 0.4195 | 0.2274 | 20 | 7,844 | 1,095,120 | 1.674 | 2.218 |


Every real trade keeps its direction, units, cost and HOLD; its entry moves to a uniformly random bar in the same trade year on the same pair; R is recomputed from the price path. The floor is taken in **t-space** and the reason is measured, not asserted: the reconstruction is systematically more negative than the engine in LEVEL (see `modeA_winners_recon_distortion.csv`), but on t the median engine/reconstruction ratio is 0.924 — the engine runs slightly lower than the space the floor is fitted in, so using it is mildly **conservative**. The expectancy-space fit is reported and NOT used: its Gumbel sigma exceeds its parent sd, the signature of a fat-tailed parent outside the Gumbel domain.


**The ladder.** The winner count moves with which line binds, so the choice is shown rather than buried:

| basis | t_analytic | t_empirical | t_binding | n_winners | is_default |
|---|---|---|---|---|---|
| stated | 5.081 | 4.354 | 5.081 | 8 | 1 |
| bonf | 5.216 | 4.354 | 5.216 | 6 | 0 |
| cell | 5.339 | 4.354 | 5.339 | 5 | 0 |
| cellbonf | 5.467 | 4.354 | 5.467 | 5 | 0 |


## 3. The floor sweep

How many clear each level, and what they earned, from `results/r2gate2/modeA_winners_floor_sweep.csv` (600 rows over all streams):

| t_floor | n_clearing | mean_trade_expectancy_R | mean_trade_total_R |
|---|---|---|---|
| 0 | 2.447e+05 | 0.04614 | 12.36 |
| 0.3437 | 1.682e+05 | 0.06251 | 16.64 |
| 0.6874 | 1.095e+05 | 0.0792 | 20.83 |
| 1.031 | 6.8e+04 | 0.0955 | 24.87 |
| 1.375 | 4.002e+04 | 0.1114 | 28.8 |
| 1.718 | 2.278e+04 | 0.1262 | 32.57 |
| 2.062 | 1.241e+04 | 0.1402 | 36.32 |
| 2.406 | 6544 | 0.1526 | 40 |
| 2.749 | 3287 | 0.1633 | 43.5 |
| 3.093 | 1606 | 0.1712 | 47.03 |
| 3.437 | 763 | 0.1817 | 50.97 |
| 3.781 | 368 | 0.1886 | 54.12 |
| 4.124 | 156 | 0.1871 | 57.45 |
| 4.468 | 69 | 0.1889 | 68.01 |
| 4.812 | 26 | 0.1854 | 75.57 |
| 5.155 | 12 | 0.2189 | 78.73 |
| 5.499 | 10 | 0.2296 | 79.81 |
| 5.843 | 4 | 0.2512 | 96.97 |
| 6.186 | 2 | 0.3727 | 65.07 |
| 6.53 | 2 | 0.3727 | 65.07 |


## 4. The non-luck winners

Above BOTH floors, **>= 50 trades in every unseen year**, positive in **>= 4 of 5** trade years.


**8 winners.** Every one is listed in `results/r2gate2/modeA_winners.csv` with its settings and per-year R.

| stream | sid | t_stat | trade_n_trades | trade_total_R | trade_max_dd_R_sumyr | trade_dd_pct_of_gross | trade_return_per_dd | prop_return_pct_per_year | trade_worst_year_R | trade_win_rate | years_positive |
|---|---|---|---|---|---|---|---|---|---|---|---|
| trend-allon | lemantrend_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | 6.759 | 816 | 127.8 | 40.82 | 13.31 | 3.131 | 2.254 | 13.12 | 0.5061 | 5 |
| trend-allon | lemantrend_signals|hieken_ashi_smoothed_signals|volatility_ratio_volume_signals|alma_baseline|adx_dmi_exit | 6.062 | 1290 | 148.3 | 55.55 | 12.22 | 2.67 | 1.922 | 8.264 | 0.4814 | 5 |
| trend-allon | waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | 5.843 | 758 | 109.4 | 41.46 | 14.72 | 2.639 | 1.9 | 10.48 | 0.4894 | 5 |
| trend-allon | waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|volatility_ratio_volume_signals|alma_baseline|adx_dmi_exit | 5.118 | 1270 | 125.7 | 51.46 | 11.61 | 2.442 | 1.758 | 7.746 | 0.4528 | 5 |
| trend-allon | lemantrend_signals|relative_vigor_index_signals|volatility_ratio_volume_signals|super_smoother_2pole_baseline|adx_dmi_exit | 5.753 | 1178 | 125.4 | 53.48 | 14.03 | 2.345 | 1.688 | -0.3094 | 0.5 | 4 |
| trend-allon | lemantrend_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|fantail_vma|adx_dmi_exit | 5.267 | 890 | 106.1 | 47.35 | 14.85 | 2.241 | 1.613 | 0.845 | 0.4753 | 5 |
| trend-allon | waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|super_smoother_2pole_baseline|adx_dmi_exit | 5.084 | 966 | 120.7 | 61.37 | 16.46 | 1.967 | 1.416 | 13.18 | 0.4244 | 5 |
| trend-allon | lemantrend_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|frama_baseline|adx_dmi_exit | 5.593 | 1060 | 121.1 | 62.12 | 17.08 | 1.95 | 1.404 | -4.781 | 0.5406 | 4 |


**Stream composition: trend-allon 8.**


Per-year R for each winner:

| stream | sid | R_2016 | R_2017 | R_2018 | R_2019 | R_2020 |
|---|---|---|---|---|---|---|
| trend-allon | lemantrend_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | 16.51 | 19.04 | 51.55 | 27.57 | 13.12 |
| trend-allon | lemantrend_signals|hieken_ashi_smoothed_signals|volatility_ratio_volume_signals|alma_baseline|adx_dmi_exit | 18.08 | 50.14 | 38.59 | 33.26 | 8.264 |
| trend-allon | waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | 10.48 | 17.3 | 46.74 | 22.72 | 12.18 |
| trend-allon | waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|volatility_ratio_volume_signals|alma_baseline|adx_dmi_exit | 7.746 | 47.55 | 27.48 | 34.96 | 7.936 |
| trend-allon | lemantrend_signals|relative_vigor_index_signals|volatility_ratio_volume_signals|super_smoother_2pole_baseline|adx_dmi_exit | 46.24 | -0.3094 | 32.07 | 24.64 | 22.77 |
| trend-allon | lemantrend_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|fantail_vma|adx_dmi_exit | 23.45 | 30.51 | 27.68 | 23.59 | 0.845 |
| trend-allon | waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|super_smoother_2pole_baseline|adx_dmi_exit | 26.1 | 21.2 | 45.86 | 14.37 | 13.18 |
| trend-allon | lemantrend_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|frama_baseline|adx_dmi_exit | 14.38 | -4.781 | 63.22 | 29.77 | 18.53 |


### Top 30 by t-statistic, and by return-to-drawdown

Drawdown is on every row, as asked. With 8 winners both tables are the whole set.


**By t-statistic** (`results/r2gate2/modeA_winners_top30_t.csv`):

| stream | sid | t_stat | trade_total_R | trade_max_dd_R_sumyr | trade_return_per_dd | prop_return_pct_per_year |
|---|---|---|---|---|---|---|
| trend-allon | lemantrend_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | 6.759 | 127.8 | 40.82 | 3.131 | 2.254 |
| trend-allon | lemantrend_signals|hieken_ashi_smoothed_signals|volatility_ratio_volume_signals|alma_baseline|adx_dmi_exit | 6.062 | 148.3 | 55.55 | 2.67 | 1.922 |
| trend-allon | waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | 5.843 | 109.4 | 41.46 | 2.639 | 1.9 |
| trend-allon | lemantrend_signals|relative_vigor_index_signals|volatility_ratio_volume_signals|super_smoother_2pole_baseline|adx_dmi_exit | 5.753 | 125.4 | 53.48 | 2.345 | 1.688 |
| trend-allon | lemantrend_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|frama_baseline|adx_dmi_exit | 5.593 | 121.1 | 62.12 | 1.95 | 1.404 |
| trend-allon | lemantrend_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|fantail_vma|adx_dmi_exit | 5.267 | 106.1 | 47.35 | 2.241 | 1.613 |
| trend-allon | waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|volatility_ratio_volume_signals|alma_baseline|adx_dmi_exit | 5.118 | 125.7 | 51.46 | 2.442 | 1.758 |
| trend-allon | waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|super_smoother_2pole_baseline|adx_dmi_exit | 5.084 | 120.7 | 61.37 | 1.967 | 1.416 |


**By return / max DD** (`results/r2gate2/modeA_winners_top30_retdd.csv`):

| stream | sid | t_stat | trade_total_R | trade_max_dd_R_sumyr | trade_return_per_dd | prop_return_pct_per_year |
|---|---|---|---|---|---|---|
| trend-allon | lemantrend_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | 6.759 | 127.8 | 40.82 | 3.131 | 2.254 |
| trend-allon | lemantrend_signals|hieken_ashi_smoothed_signals|volatility_ratio_volume_signals|alma_baseline|adx_dmi_exit | 6.062 | 148.3 | 55.55 | 2.67 | 1.922 |
| trend-allon | waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | 5.843 | 109.4 | 41.46 | 2.639 | 1.9 |
| trend-allon | waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|volatility_ratio_volume_signals|alma_baseline|adx_dmi_exit | 5.118 | 125.7 | 51.46 | 2.442 | 1.758 |
| trend-allon | lemantrend_signals|relative_vigor_index_signals|volatility_ratio_volume_signals|super_smoother_2pole_baseline|adx_dmi_exit | 5.753 | 125.4 | 53.48 | 2.345 | 1.688 |
| trend-allon | lemantrend_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|fantail_vma|adx_dmi_exit | 5.267 | 106.1 | 47.35 | 2.241 | 1.613 |
| trend-allon | waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|super_smoother_2pole_baseline|adx_dmi_exit | 5.084 | 120.7 | 61.37 | 1.967 | 1.416 |
| trend-allon | lemantrend_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|frama_baseline|adx_dmi_exit | 5.593 | 121.1 | 62.12 | 1.95 | 1.404 |


**By prop return** (`results/r2gate2/modeA_winners_top30_prop.csv`):

| stream | sid | t_stat | trade_total_R | trade_max_dd_R_sumyr | trade_return_per_dd | prop_return_pct_per_year |
|---|---|---|---|---|---|---|
| trend-allon | lemantrend_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | 6.759 | 127.8 | 40.82 | 3.131 | 2.254 |
| trend-allon | lemantrend_signals|hieken_ashi_smoothed_signals|volatility_ratio_volume_signals|alma_baseline|adx_dmi_exit | 6.062 | 148.3 | 55.55 | 2.67 | 1.922 |
| trend-allon | waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | 5.843 | 109.4 | 41.46 | 2.639 | 1.9 |
| trend-allon | waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|volatility_ratio_volume_signals|alma_baseline|adx_dmi_exit | 5.118 | 125.7 | 51.46 | 2.442 | 1.758 |
| trend-allon | lemantrend_signals|relative_vigor_index_signals|volatility_ratio_volume_signals|super_smoother_2pole_baseline|adx_dmi_exit | 5.753 | 125.4 | 53.48 | 2.345 | 1.688 |
| trend-allon | lemantrend_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|fantail_vma|adx_dmi_exit | 5.267 | 106.1 | 47.35 | 2.241 | 1.613 |
| trend-allon | waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|super_smoother_2pole_baseline|adx_dmi_exit | 5.084 | 120.7 | 61.37 | 1.967 | 1.416 |
| trend-allon | lemantrend_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|frama_baseline|adx_dmi_exit | 5.593 | 121.1 | 62.12 | 1.95 | 1.404 |


## 5. Family support

Cousins are same (c1, c2). A winner alone in its family is the shape a lucky draw takes; one surrounded by near-winners is the shape a real effect takes.

| stream | family_c1_c2 | winner_t | n_cousins | cousin_t_median | cousin_t_max | cousins_t_over_2 | cousins_t_over_3 | cousins_positive_pct | lone_survivor |
|---|---|---|---|---|---|---|---|---|---|
| trend-allon | lemantrend_signals|hieken_ashi_smoothed_signals | 6.759 | 179 | 1.611 | 6.062 | 74 | 42 | 75.42 | 0 |
| trend-allon | lemantrend_signals|hieken_ashi_smoothed_signals | 6.062 | 179 | 1.611 | 6.759 | 74 | 42 | 75.42 | 0 |
| trend-allon | waddah_attar_explosion_signals|hieken_ashi_smoothed_signals | 5.843 | 179 | 1.259 | 5.118 | 60 | 35 | 75.42 | 0 |
| trend-allon | lemantrend_signals|relative_vigor_index_signals | 5.753 | 179 | -0.2286 | 4.125 | 16 | 8 | 45.81 | 0 |
| trend-allon | lemantrend_signals|hieken_ashi_smoothed_signals | 5.593 | 179 | 1.611 | 6.759 | 74 | 42 | 75.42 | 0 |
| trend-allon | lemantrend_signals|hieken_ashi_smoothed_signals | 5.267 | 179 | 1.611 | 6.759 | 74 | 42 | 75.42 | 0 |
| trend-allon | waddah_attar_explosion_signals|hieken_ashi_smoothed_signals | 5.118 | 179 | 1.259 | 5.843 | 60 | 35 | 75.42 | 0 |
| trend-allon | waddah_attar_explosion_signals|hieken_ashi_smoothed_signals | 5.084 | 179 | 1.259 | 5.843 | 60 | 35 | 75.42 | 0 |


**0 of 8 flagged lone survivors.**


## 6. The winners' book — LAST, and descriptive only

**This book's membership was chosen with sight of the years it reports.** Its return is therefore DESCRIPTIVE and is not evidence of anything. The luck floor in section 2 is the evidence. The book answers a different question: if you had held exactly these, equally weighted, what would the drawdown have looked like.

| step | book | budget | members | trade_total_pct | trade_max_dd_pct | trade_dip95_pct | trade_sortino | trade_calmar | prop_return_pct_per_year | clears_12pct_at_prop |
|---|---|---|---|---|---|---|---|---|---|---|
| 2011-2014 | allon | team1 | 8 | 1.874 | 0.9261 | 2.01 | 1.405 | 2.024 | 3.357 | 0 |
| 2011-2014 | allon | team2 | 8 | 2.811 | 1.389 | 3.015 | 1.405 | 2.024 | 3.357 | 0 |
| 2012-2015 | allon | team1 | 8 | 1.911 | 0.665 | 1.828 | 1.812 | 2.874 | 3.763 | 0 |
| 2012-2015 | allon | team2 | 8 | 2.867 | 0.9975 | 2.743 | 1.812 | 2.874 | 3.763 | 0 |
| 2013-2016 | allon | team1 | 8 | 6.138 | 0.7813 | 1.291 | 5.453 | 7.856 | 17.11 | 1 |
| 2013-2016 | allon | team2 | 8 | 9.207 | 1.172 | 1.937 | 5.453 | 7.856 | 17.11 | 1 |
| 2014-2017 | allon | team1 | 8 | 2.612 | 1.951 | 2.264 | 1.937 | 1.338 | 4.153 | 0 |
| 2014-2017 | allon | team2 | 8 | 3.917 | 2.927 | 3.396 | 1.937 | 1.338 | 4.153 | 0 |
| 2015-2018 | allon | team1 | 8 | 2.278 | 1.362 | 2.696 | 1.497 | 1.673 | 3.041 | 0 |
| 2015-2018 | allon | team2 | 8 | 3.417 | 2.042 | 4.044 | 1.497 | 1.673 | 3.041 | 0 |


The ROUTED book is **empty** — blank rows, not zeros. No winner is a routed-stream winner, so it has no members.


### Full KPI table


### TEAM 1

| KPI | ALWAYS-ON |
|---|---|
| median year | 2.28% |
| average year | 2.96% |
| worst year | 1.87% |
| best year | 6.14% |
| total 2016-2020 | 14.81% |
| CAGR | 2.96% |
| worst day | -0.71% |
| max drawdown | -1.98% |
| DIP95 (worst step) | 2.70% |
| Sharpe | 1.51 |
| Sortino | 2.28 |
| Calmar (total / max DD, the shipped bar) | 7.49 |
| Calmar (CAGR / max DD) | 1.50 |
| profit factor (trades, median step) | 1.23 |
| win rate (trades, median step) | 52.51% |
| positive years of 5 | 5 |
| retention (median step) | 1.17 |
| steps flagged FIT of 5 | 0 |

Per year:

- ALWAYS-ON: 2016: +1.87% | 2017: +1.91% | 2018: +6.14% | 2019: +2.61% | 2020: +2.28%

### TEAM 2

| KPI | ALWAYS-ON |
|---|---|
| median year | 3.42% |
| average year | 4.44% |
| worst year | 2.81% |
| best year | 9.21% |
| total 2016-2020 | 22.22% |
| CAGR | 4.44% |
| worst day | -1.06% |
| max drawdown | -2.97% |
| DIP95 (worst step) | 4.04% |
| Sharpe | 1.51 |
| Sortino | 2.28 |
| Calmar (total / max DD, the shipped bar) | 7.49 |
| Calmar (CAGR / max DD) | 1.50 |
| profit factor (trades, median step) | 1.23 |
| win rate (trades, median step) | 52.51% |
| positive years of 5 | 5 |
| retention (median step) | 1.17 |
| steps flagged FIT of 5 | 0 |

Per year:

- ALWAYS-ON: 2016: +2.81% | 2017: +2.87% | 2018: +9.21% | 2019: +3.92% | 2020: +3.42%

### Its nulls

| null | scope | step | book | budget | members | real | n_draws | null_mean | null_p95 | p_one_sided |
|---|---|---|---|---|---|---|---|---|---|---|
| identity | full field | 2011-2014 | allon | team1 |  | 1.874 | 200 | 0.8015 | 3.247 | 0.405 |
| identity | full field | 2011-2014 | allon | team2 |  | 2.811 | 200 | 1.723 | 4.871 | 0.335 |
| identity | full field | 2012-2015 | allon | team1 |  | 1.911 | 200 | 1.344 | 2.182 | 0.535 |
| identity | full field | 2012-2015 | allon | team2 |  | 2.867 | 200 | 1.863 | 3.274 | 0.5 |
| identity | full field | 2013-2016 | allon | team1 |  | 6.138 | 200 | 2.6 | 6.138 | 0.205 |
| identity | full field | 2013-2016 | allon | team2 |  | 9.207 | 200 | 3.535 | 9.207 | 0 |
| identity | full field | 2014-2017 | allon | team1 |  | 2.612 | 200 | 3.117 | 7.4 | 0.745 |
| identity | full field | 2014-2017 | allon | team2 |  | 3.917 | 200 | 4.277 | 11.1 | 0.655 |
| identity | full field | 2015-2018 | allon | team1 |  | 2.278 | 200 | 3.267 | 8.839 | 0.635 |
| identity | full field | 2015-2018 | allon | team2 |  | 3.417 | 200 | 4.823 | 13.26 | 0.62 |
| shuffle | passers, full | 2011-2014 | allon | team1 | 8 | 1.874 | 19 | 1.874 | 1.874 | 1 |
| shuffle | passers, full | 2011-2014 | allon | team2 | 8 | 2.811 | 19 | 2.811 | 2.811 | 1 |
| shuffle | passers, full | 2012-2015 | allon | team1 | 8 | 1.911 | 19 | 1.911 | 1.911 | 1 |
| shuffle | passers, full | 2012-2015 | allon | team2 | 8 | 2.867 | 19 | 2.867 | 2.867 | 1 |
| shuffle | passers, full | 2013-2016 | allon | team1 | 8 | 6.138 | 19 | 6.138 | 6.138 | 1 |
| shuffle | passers, full | 2013-2016 | allon | team2 | 8 | 9.207 | 19 | 9.207 | 9.207 | 1 |
| shuffle | passers, full | 2014-2017 | allon | team1 | 8 | 2.612 | 19 | 2.612 | 2.612 | 1 |
| shuffle | passers, full | 2014-2017 | allon | team2 | 8 | 3.917 | 19 | 3.917 | 3.917 | 1 |
| shuffle | passers, full | 2015-2018 | allon | team1 | 8 | 2.278 | 19 | 2.278 | 2.278 | 1 |
| shuffle | passers, full | 2015-2018 | allon | team2 | 8 | 3.417 | 19 | 3.417 | 3.417 | 1 |
| random-entry | passers, full | 2011-2014 | allon | team1 | 8 | 1.874 | 19 | -0.04024 | 1.208 | 0 |
| random-entry | passers, full | 2011-2014 | allon | team2 | 8 | 2.811 | 19 | -0.06037 | 1.811 | 0 |
| random-entry | passers, full | 2012-2015 | allon | team1 | 8 | 1.911 | 19 | 0.185 | 1.326 | 0 |
| random-entry | passers, full | 2012-2015 | allon | team2 | 8 | 2.867 | 19 | 0.2775 | 1.989 | 0 |
| random-entry | passers, full | 2013-2016 | allon | team1 | 8 | 6.138 | 19 | -0.07404 | 0.9408 | 0 |
| random-entry | passers, full | 2013-2016 | allon | team2 | 8 | 9.207 | 19 | -0.1111 | 1.411 | 0 |
| random-entry | passers, full | 2014-2017 | allon | team1 | 8 | 2.612 | 19 | -0.2697 | 0.5616 | 0 |
| random-entry | passers, full | 2014-2017 | allon | team2 | 8 | 3.917 | 19 | -0.4045 | 0.8425 | 0 |
| random-entry | passers, full | 2015-2018 | allon | team1 | 8 | 2.278 | 19 | -0.1223 | 0.8936 | 0 |
| random-entry | passers, full | 2015-2018 | allon | team2 | 8 | 3.417 | 19 | -0.1835 | 1.34 | 0 |


## 6b. Pair routing — a STANDING test

Jack, 22 Nov: *"Pair routing is a standing test, not a one-off: every mode, every re-tune, every winners pipeline from now on reports the pair-routing sweep."* Chosen on tuning years, traded on unseen years, against a random-pair null of the same size.

| rule | K | real_return_per_dd | random_null | real_beats_null | prop_return_pct | clears_12pct |
|---|---|---|---|---|---|---|
| topk | 1 | 0.8229 | 1.252 | 0 | 0.5925 | 0 |
| topk | 2 | 0.8475 | 1.061 | 0 | 0.6102 | 0 |
| topk | 3 | 0.5726 | 0.9628 | 0 | 0.4123 | 0 |
| topk | 4 | 0.6386 | 0.862 | 0 | 0.4598 | 0 |
| topk | 5 | 0.7301 | 0.9021 | 0 | 0.5256 | 0 |
| topk | 6 | 0.766 | 0.9159 | 0 | 0.5515 | 0 |
| topk | 7 | 0.7551 | 0.8625 | 0 | 0.5437 | 0 |
| topk | 8 | 0.6912 | 0.8687 | 0 | 0.4976 | 0 |
| topk | 9 | 0.7511 | 0.8986 | 0 | 0.5408 | 0 |
| topk | 10 | 0.6879 | 0.844 | 0 | 0.4953 | 0 |
| topk | 11 | 0.6908 | 0.8885 | 0 | 0.4974 | 0 |
| topk | 12 | 0.7284 | 0.8291 | 0 | 0.5244 | 0 |
| topk | 13 | 0.7279 | 0.8967 | 0 | 0.5241 | 0 |
| topk | 14 | 0.7182 | 0.835 | 0 | 0.5171 | 0 |
| topk | 15 | 0.7217 | 0.8492 | 0 | 0.5196 | 0 |
| topk | 16 | 0.7214 | 0.8488 | 0 | 0.5194 | 0 |
| topk | 17 | 0.7371 | 0.8334 | 0 | 0.5307 | 0 |
| topk | 18 | 0.7392 | 0.838 | 0 | 0.5322 | 0 |
| topk | 19 | 0.7611 | 0.8422 | 0 | 0.548 | 0 |
| topk | 20 | 0.7699 | 0.8271 | 0 | 0.5544 | 0 |
| topk | 21 | 0.7778 | 0.8369 | 0 | 0.56 | 0 |
| topk | 22 | 0.7892 | 0.8247 | 0 | 0.5682 | 0 |
| topk | 23 | 0.7855 | 0.8293 | 0 | 0.5656 | 0 |
| topk | 24 | 0.7933 | 0.8334 | 0 | 0.5712 | 0 |
| topk | 25 | 0.7997 | 0.8291 | 0 | 0.5758 | 0 |
| topk | 26 | 0.8227 | 0.8304 | 0 | 0.5924 | 0 |
| topk | 27 | 0.8074 | 0.8356 | 0 | 0.5813 | 0 |
| topk | 28 | 0.8339 | 0.8339 | 1 | 0.6004 | 0 |
| threshold |  | 0.7726 |  |  | 0.5563 | 0 |
| topk_dir |  | 0.8636 |  |  | 0.6218 | 0 |
| threshold_dir |  | 0.9253 |  |  | 0.6662 | 0 |


All-28 baseline return/DD **0.834** (prop return 0.60%). The real rule beats the random-pair null at **1 of 28** values of K, and **0** rows clear 12% at prop sizing.


**The drawdown basis in this section sums per (pair, direction, year) drawdowns** and is a looser bound than the strategy-level figure used elsewhere in this document, so its level is not comparable to section 4 and its prop return is a floor. Real and null share the basis, so the comparison within the section is sound. Full detail in `results/r2gate2/modeA_winners_pairrouted.csv` and `WINNERS_BY_PAIR.md`.


## 7. Overlay curves

Swept over their full range with **no fixed value chosen**, from `results/r2gate2/modeA_overlay_curves_winners.csv` (194 points). Return against max drawdown on the unseen years at the budget.

| book | budget | overlay | p1 | p2 | total_pct | max_dd_pct | return_per_dd | implementable |
|---|---|---|---|---|---|---|---|---|
| allon | team1 | none |  |  | 14.81 | 1.977 | 7.492 | baseline |
| allon | team1 | equity_pause | 0.8827 | 0.1236 | 13.96 | 1.394 | 10.01 | yes -- decided at day boundaries |
| allon | team1 | kill_switch | 1.075 |  | 13.03 | 1.165 | 11.19 | yes -- decided at day boundaries |
| allon | team1 | daily_loss_stop | 0.07089 |  | 32.72 | 0.5718 | 57.23 | UPPER BOUND -- needs intraday data to evaluate |
| allon | team2 | none |  |  | 22.22 | 2.966 | 7.492 | baseline |
| allon | team2 | equity_pause | 1.324 | 0.1854 | 20.94 | 2.091 | 10.01 | yes -- decided at day boundaries |
| allon | team2 | kill_switch | 1.612 |  | 19.55 | 1.747 | 11.19 | yes -- decided at day boundaries |
| allon | team2 | daily_loss_stop | 0.1063 |  | 49.09 | 0.8577 | 57.23 | UPPER BOUND -- needs intraday data to evaluate |


**The daily loss stop is an UPPER BOUND, not a result.** Clipping a daily series at -x assumes the breach is caught exactly at -x, costs nothing to exit and forfeits no intraday recovery — a free lunch on daily data. The pause and the kill switch decide at DAY BOUNDARIES, which a daily series evaluates honestly.


## Provenance

| file | rows | md5 |
|---|---|---|
| `results/r2gate2/modeA_winners.csv` | 8 | dda3e396fd22 |
| `results/r2gate2/modeA_winners_t_observed.csv` | 10 | 59e28ba7df25 |
| `results/r2gate2/modeA_winners_floor_analytic.csv` | 2 | 5b8e63829c81 |
| `results/r2gate2/modeA_winners_floor_empirical.csv` | 10 | 05054ca102bf |
| `results/r2gate2/modeA_winners_floor_ladder.csv` | 4 | acbd8520fb1d |
| `results/r2gate2/modeA_winners_floor_sweep.csv` | 600 | 03f892fd70c2 |
| `results/r2gate2/modeA_winners_family.csv` | 8 | 7345d4b27d4e |
| `results/r2gate2/modeA_winners_nullstrat.csv` | 7,844 | 6cafdedcaa97 |
| `results/r2gate2/modeA_winners_recon_distortion.csv` | 7,844 | b34b5ebc9591 |
| `results/r2gate2/modeA_gate3_passersbook_winners.csv` | 15 | d78d9b7b5062 |
| `results/r2gate2/modeA_gate3_passersbook_winners_nulls.csv` | 30 | c53a41895ae5 |
| `results/r2gate2/modeA_overlay_curves_winners.csv` | 194 | 06d8a43d6c58 |
