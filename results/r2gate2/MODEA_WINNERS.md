# MODE A — WINNERS, NO GATES

Generated 2026-11-25 11:27 by `code/l2r2winners.py`, read-only off the gate 2 bank and the gate 3 scoring. **Nothing is filtered before it is measured**: all 273,780 strategies are recorded on both unseen records, and the only cut is the LUCK FLOOR, which is a statement about chance rather than a preference about settings. Individual strategies first; the book last.


## 0. The number Jack buys: PROP RETURN

Yearly return when sized so the worst dip equals **3.6%** — max DD for a strategy, trade-year DIP95 for a book. Target **12% a year**.

For a strategy the arithmetic collapses to `0.72 x return/DD`, so prop return and return-per-drawdown are the same ranking and the 12% line is exactly **return/DD >= 16.67**.

**0 of 6 winners clear 12% at prop sizing.** Best is **2.25% a year** (return/DD 3.13 against the 16.67 needed) — short of the line by a factor of 5.3.


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
| t | -0.4438 | 1.019 | 3.184 | 0.2547 | 20 | 7,844 | 1,095,120 | 4.589 | 5.199 |
| expectancy_R | -0.02158 | 0.06639 | 0.4609 | 0.1941 | 20 | 7,844 | 1,095,120 | 1.532 | 1.996 |


Every real trade keeps its direction, units, cost and HOLD; its entry moves to a uniformly random bar in the same trade year on the same pair; R is recomputed from the price path. The floor is taken in **t-space** and the reason is measured, not asserted: the reconstruction is systematically more negative than the engine in LEVEL (see `modeA_winners_recon_distortion.csv`), but on t the median engine/reconstruction ratio is 0.924 — the engine runs slightly lower than the space the floor is fitted in, so using it is mildly **conservative**. The expectancy-space fit is reported and NOT used: its Gumbel sigma exceeds its parent sd, the signature of a fat-tailed parent outside the Gumbel domain.


**The ladder.** The winner count moves with which line binds, so the choice is shown rather than buried:

| basis | t_analytic | t_empirical | t_binding | n_winners | is_default |
|---|---|---|---|---|---|
| stated | 5.081 | 5.199 | 5.199 | 6 | 1 |
| bonf | 5.216 | 5.199 | 5.216 | 6 | 0 |
| cell | 5.339 | 5.199 | 5.339 | 5 | 0 |
| cellbonf | 5.467 | 5.199 | 5.467 | 5 | 0 |


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


**6 winners.** Every one is listed in `results/r2gate2/modeA_winners.csv` with its settings and per-year R.

| stream | sid | t_stat | trade_n_trades | trade_total_R | trade_max_dd_R_sumyr | trade_dd_pct_of_gross | trade_return_per_dd | prop_return_pct_per_year | trade_worst_year_R | trade_win_rate | years_positive |
|---|---|---|---|---|---|---|---|---|---|---|---|
| trend-allon | lemantrend_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | 6.759 | 816 | 127.8 | 40.82 | 13.31 | 3.131 | 2.254 | 13.12 | 0.5061 | 5 |
| trend-allon | lemantrend_signals|hieken_ashi_smoothed_signals|volatility_ratio_volume_signals|alma_baseline|adx_dmi_exit | 6.062 | 1290 | 148.3 | 55.55 | 12.22 | 2.67 | 1.922 | 8.264 | 0.4814 | 5 |
| trend-allon | waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | 5.843 | 758 | 109.4 | 41.46 | 14.72 | 2.639 | 1.9 | 10.48 | 0.4894 | 5 |
| trend-allon | lemantrend_signals|relative_vigor_index_signals|volatility_ratio_volume_signals|super_smoother_2pole_baseline|adx_dmi_exit | 5.753 | 1178 | 125.4 | 53.48 | 14.03 | 2.345 | 1.688 | -0.3094 | 0.5 | 4 |
| trend-allon | lemantrend_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|fantail_vma|adx_dmi_exit | 5.267 | 890 | 106.1 | 47.35 | 14.85 | 2.241 | 1.613 | 0.845 | 0.4753 | 5 |
| trend-allon | lemantrend_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|frama_baseline|adx_dmi_exit | 5.593 | 1060 | 121.1 | 62.12 | 17.08 | 1.95 | 1.404 | -4.781 | 0.5406 | 4 |


**Stream composition: trend-allon 6.**


Per-year R for each winner:

| stream | sid | R_2016 | R_2017 | R_2018 | R_2019 | R_2020 |
|---|---|---|---|---|---|---|
| trend-allon | lemantrend_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | 16.51 | 19.04 | 51.55 | 27.57 | 13.12 |
| trend-allon | lemantrend_signals|hieken_ashi_smoothed_signals|volatility_ratio_volume_signals|alma_baseline|adx_dmi_exit | 18.08 | 50.14 | 38.59 | 33.26 | 8.264 |
| trend-allon | waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | 10.48 | 17.3 | 46.74 | 22.72 | 12.18 |
| trend-allon | lemantrend_signals|relative_vigor_index_signals|volatility_ratio_volume_signals|super_smoother_2pole_baseline|adx_dmi_exit | 46.24 | -0.3094 | 32.07 | 24.64 | 22.77 |
| trend-allon | lemantrend_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|fantail_vma|adx_dmi_exit | 23.45 | 30.51 | 27.68 | 23.59 | 0.845 |
| trend-allon | lemantrend_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|frama_baseline|adx_dmi_exit | 14.38 | -4.781 | 63.22 | 29.77 | 18.53 |


### Top 30 by t-statistic, and by return-to-drawdown

Drawdown is on every row, as asked. With 6 winners both tables are the whole set.


**By t-statistic** (`results/r2gate2/modeA_winners_top30_t.csv`):

| stream | sid | t_stat | trade_total_R | trade_max_dd_R_sumyr | trade_return_per_dd | prop_return_pct_per_year |
|---|---|---|---|---|---|---|
| trend-allon | lemantrend_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | 6.759 | 127.8 | 40.82 | 3.131 | 2.254 |
| trend-allon | lemantrend_signals|hieken_ashi_smoothed_signals|volatility_ratio_volume_signals|alma_baseline|adx_dmi_exit | 6.062 | 148.3 | 55.55 | 2.67 | 1.922 |
| trend-allon | waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | 5.843 | 109.4 | 41.46 | 2.639 | 1.9 |
| trend-allon | lemantrend_signals|relative_vigor_index_signals|volatility_ratio_volume_signals|super_smoother_2pole_baseline|adx_dmi_exit | 5.753 | 125.4 | 53.48 | 2.345 | 1.688 |
| trend-allon | lemantrend_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|frama_baseline|adx_dmi_exit | 5.593 | 121.1 | 62.12 | 1.95 | 1.404 |
| trend-allon | lemantrend_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|fantail_vma|adx_dmi_exit | 5.267 | 106.1 | 47.35 | 2.241 | 1.613 |


**By return / max DD** (`results/r2gate2/modeA_winners_top30_retdd.csv`):

| stream | sid | t_stat | trade_total_R | trade_max_dd_R_sumyr | trade_return_per_dd | prop_return_pct_per_year |
|---|---|---|---|---|---|---|
| trend-allon | lemantrend_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | 6.759 | 127.8 | 40.82 | 3.131 | 2.254 |
| trend-allon | lemantrend_signals|hieken_ashi_smoothed_signals|volatility_ratio_volume_signals|alma_baseline|adx_dmi_exit | 6.062 | 148.3 | 55.55 | 2.67 | 1.922 |
| trend-allon | waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | 5.843 | 109.4 | 41.46 | 2.639 | 1.9 |
| trend-allon | lemantrend_signals|relative_vigor_index_signals|volatility_ratio_volume_signals|super_smoother_2pole_baseline|adx_dmi_exit | 5.753 | 125.4 | 53.48 | 2.345 | 1.688 |
| trend-allon | lemantrend_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|fantail_vma|adx_dmi_exit | 5.267 | 106.1 | 47.35 | 2.241 | 1.613 |
| trend-allon | lemantrend_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|frama_baseline|adx_dmi_exit | 5.593 | 121.1 | 62.12 | 1.95 | 1.404 |


**By prop return** (`results/r2gate2/modeA_winners_top30_prop.csv`):

| stream | sid | t_stat | trade_total_R | trade_max_dd_R_sumyr | trade_return_per_dd | prop_return_pct_per_year |
|---|---|---|---|---|---|---|
| trend-allon | lemantrend_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | 6.759 | 127.8 | 40.82 | 3.131 | 2.254 |
| trend-allon | lemantrend_signals|hieken_ashi_smoothed_signals|volatility_ratio_volume_signals|alma_baseline|adx_dmi_exit | 6.062 | 148.3 | 55.55 | 2.67 | 1.922 |
| trend-allon | waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | 5.843 | 109.4 | 41.46 | 2.639 | 1.9 |
| trend-allon | lemantrend_signals|relative_vigor_index_signals|volatility_ratio_volume_signals|super_smoother_2pole_baseline|adx_dmi_exit | 5.753 | 125.4 | 53.48 | 2.345 | 1.688 |
| trend-allon | lemantrend_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|fantail_vma|adx_dmi_exit | 5.267 | 106.1 | 47.35 | 2.241 | 1.613 |
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


**0 of 6 flagged lone survivors.**


## 6. The winners' book — LAST, and descriptive only

**This book's membership was chosen with sight of the years it reports.** Its return is therefore DESCRIPTIVE and is not evidence of anything. The luck floor in section 2 is the evidence. The book answers a different question: if you had held exactly these, equally weighted, what would the drawdown have looked like.

| step | book | budget | members | trade_total_pct | trade_max_dd_pct | trade_dip95_pct | trade_sortino | trade_calmar | prop_return_pct_per_year | clears_12pct_at_prop |
|---|---|---|---|---|---|---|---|---|---|---|
| 2011-2014 | allon | team1 | 6 | 1.341 | 0.7888 | 1.949 | 1.094 | 1.7 | 2.477 | 0 |
| 2011-2014 | allon | team2 | 6 | 2.011 | 1.183 | 2.923 | 1.094 | 1.7 | 2.477 | 0 |
| 2012-2015 | allon | team1 | 6 | 0.1632 | 1.428 | 1.96 | 0.2203 | 0.1143 | 0.2998 | 0 |
| 2012-2015 | allon | team2 | 6 | 0.2448 | 2.142 | 2.94 | 0.2203 | 0.1143 | 0.2998 | 0 |
| 2013-2016 | allon | team1 | 6 | 4.79 | 0.8167 | 1.63 | 3.454 | 5.864 | 10.58 | 0 |
| 2013-2016 | allon | team2 | 6 | 7.184 | 1.225 | 2.446 | 3.454 | 5.864 | 10.58 | 0 |
| 2014-2017 | allon | team1 | 6 | 4.545 | 1.234 | 2.146 | 3.343 | 3.683 | 7.623 | 0 |
| 2014-2017 | allon | team2 | 6 | 6.817 | 1.851 | 3.219 | 3.343 | 3.683 | 7.623 | 0 |
| 2015-2018 | allon | team1 | 6 | -0.5862 | 1.925 | 3.247 | -0.3969 | -0.3045 | -0.65 | 0 |
| 2015-2018 | allon | team2 | 6 | -0.8794 | 2.888 | 4.87 | -0.3969 | -0.3045 | -0.65 | 0 |


The ROUTED book is **empty** — blank rows, not zeros. No winner is a routed-stream winner, so it has no members.


### Full KPI table


### TEAM 1

| KPI | ALWAYS-ON |
|---|---|
| median year | 1.34% |
| average year | 2.05% |
| worst year | -0.59% |
| best year | 4.79% |
| total 2016-2020 | 10.25% |
| CAGR | 2.05% |
| worst day | -0.57% |
| max drawdown | -1.93% |
| DIP95 (worst step) | 3.25% |
| Sharpe | 1.10 |
| Sortino | 1.61 |
| Calmar (total / max DD, the shipped bar) | 5.33 |
| Calmar (CAGR / max DD) | 1.07 |
| profit factor (trades, median step) | 1.17 |
| win rate (trades, median step) | 51.74% |
| positive years of 5 | 4 |
| retention (median step) | 2.28 |
| steps flagged FIT of 5 | 2 |

Per year:

- ALWAYS-ON: 2016: +1.34% | 2017: +0.16% | 2018: +4.79% | 2019: +4.54% | 2020: -0.59%

### TEAM 2

| KPI | ALWAYS-ON |
|---|---|
| median year | 2.01% |
| average year | 3.08% |
| worst year | -0.88% |
| best year | 7.18% |
| total 2016-2020 | 15.38% |
| CAGR | 3.08% |
| worst day | -0.86% |
| max drawdown | -2.89% |
| DIP95 (worst step) | 4.87% |
| Sharpe | 1.10 |
| Sortino | 1.61 |
| Calmar (total / max DD, the shipped bar) | 5.33 |
| Calmar (CAGR / max DD) | 1.07 |
| profit factor (trades, median step) | 1.17 |
| win rate (trades, median step) | 51.74% |
| positive years of 5 | 4 |
| retention (median step) | 2.28 |
| steps flagged FIT of 5 | 2 |

Per year:

- ALWAYS-ON: 2016: +2.01% | 2017: +0.24% | 2018: +7.18% | 2019: +6.82% | 2020: -0.88%

### Its nulls

| null | scope | step | book | budget | members | real | n_draws | null_mean | null_p95 | p_one_sided |
|---|---|---|---|---|---|---|---|---|---|---|
| identity | full field | 2011-2014 | allon | team1 |  | 1.341 | 200 | 0.9937 | 3.398 | 0.445 |
| identity | full field | 2011-2014 | allon | team2 |  | 2.011 | 200 | 1.796 | 5.097 | 0.505 |
| identity | full field | 2012-2015 | allon | team1 |  | 0.1632 | 200 | 0.8057 | 2.759 | 0.8 |
| identity | full field | 2012-2015 | allon | team2 |  | 0.2448 | 200 | 1.216 | 4.138 | 0.82 |
| identity | full field | 2013-2016 | allon | team1 |  | 4.79 | 200 | 2.239 | 4.79 | 0.14 |
| identity | full field | 2013-2016 | allon | team2 |  | 7.184 | 200 | 2.956 | 7.184 | 0.13 |
| identity | full field | 2014-2017 | allon | team1 |  | 4.545 | 200 | 3.596 | 7.607 | 0.175 |
| identity | full field | 2014-2017 | allon | team2 |  | 6.817 | 200 | 5.374 | 11.41 | 0.37 |
| identity | full field | 2015-2018 | allon | team1 |  | -0.5862 | 200 | 2.527 | 6.915 | 0.84 |
| identity | full field | 2015-2018 | allon | team2 |  | -0.8794 | 200 | 3.933 | 10.37 | 1 |
| shuffle | passers, full | 2011-2014 | allon | team1 | 6 | 1.341 | 19 | 1.341 | 1.341 | 1 |
| shuffle | passers, full | 2011-2014 | allon | team2 | 6 | 2.011 | 19 | 2.011 | 2.011 | 1 |
| shuffle | passers, full | 2012-2015 | allon | team1 | 6 | 0.1632 | 19 | 0.1632 | 0.1632 | 1 |
| shuffle | passers, full | 2012-2015 | allon | team2 | 6 | 0.2448 | 19 | 0.2448 | 0.2448 | 1 |
| shuffle | passers, full | 2013-2016 | allon | team1 | 6 | 4.79 | 19 | 4.79 | 4.79 | 1 |
| shuffle | passers, full | 2013-2016 | allon | team2 | 6 | 7.184 | 19 | 7.184 | 7.184 | 1 |
| shuffle | passers, full | 2014-2017 | allon | team1 | 6 | 4.545 | 19 | 4.545 | 4.545 | 1 |
| shuffle | passers, full | 2014-2017 | allon | team2 | 6 | 6.817 | 19 | 6.817 | 6.817 | 1 |
| shuffle | passers, full | 2015-2018 | allon | team1 | 6 | -0.5862 | 19 | -0.5862 | -0.5862 | 1 |
| shuffle | passers, full | 2015-2018 | allon | team2 | 6 | -0.8794 | 19 | -0.8794 | -0.8794 | 1 |
| random-entry | passers, full | 2011-2014 | allon | team1 | 6 | 1.341 | 19 | 0.1076 | 1.83 | 0.1053 |
| random-entry | passers, full | 2011-2014 | allon | team2 | 6 | 2.011 | 19 | 0.1614 | 2.744 | 0.1053 |
| random-entry | passers, full | 2012-2015 | allon | team1 | 6 | 0.1632 | 19 | -0.1298 | 0.5701 | 0.2105 |
| random-entry | passers, full | 2012-2015 | allon | team2 | 6 | 0.2448 | 19 | -0.1946 | 0.8551 | 0.2105 |
| random-entry | passers, full | 2013-2016 | allon | team1 | 6 | 4.79 | 19 | -0.008465 | 1.283 | 0 |
| random-entry | passers, full | 2013-2016 | allon | team2 | 6 | 7.184 | 19 | -0.0127 | 1.924 | 0 |
| random-entry | passers, full | 2014-2017 | allon | team1 | 6 | 4.545 | 19 | 0.06049 | 0.6194 | 0 |
| random-entry | passers, full | 2014-2017 | allon | team2 | 6 | 6.817 | 19 | 0.09073 | 0.9291 | 0 |
| random-entry | passers, full | 2015-2018 | allon | team1 | 6 | -0.5862 | 19 | 0.1711 | 1.935 | 0.8947 |
| random-entry | passers, full | 2015-2018 | allon | team2 | 6 | -0.8794 | 19 | 0.2567 | 2.903 | 0.8947 |


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
| allon | team1 | none |  |  | 10.25 | 1.925 | 5.325 | baseline |
| allon | team1 | equity_pause | 1.478 | 0.1203 | 10.46 | 1.572 | 6.656 | yes -- decided at day boundaries |
| allon | team1 | kill_switch | 1.507 |  | 10.25 | 1.507 | 6.8 | yes -- decided at day boundaries |
| allon | team1 | daily_loss_stop | 0.05729 |  | 30.79 | 0.685 | 44.95 | UPPER BOUND -- needs intraday data to evaluate |
| allon | team2 | none |  |  | 15.38 | 2.888 | 5.325 | baseline |
| allon | team2 | equity_pause | 2.218 | 0.1805 | 15.69 | 2.358 | 6.656 | yes -- decided at day boundaries |
| allon | team2 | kill_switch | 2.26 |  | 15.37 | 2.26 | 6.8 | yes -- decided at day boundaries |
| allon | team2 | daily_loss_stop | 0.08593 |  | 46.19 | 1.028 | 44.95 | UPPER BOUND -- needs intraday data to evaluate |


**The daily loss stop is an UPPER BOUND, not a result.** Clipping a daily series at -x assumes the breach is caught exactly at -x, costs nothing to exit and forfeits no intraday recovery — a free lunch on daily data. The pause and the kill switch decide at DAY BOUNDARIES, which a daily series evaluates honestly.


## Provenance

| file | rows | md5 |
|---|---|---|
| `results/r2gate2/modeA_winners.csv` | 6 | 93a0c0f7c52e |
| `results/r2gate2/modeA_winners_t_observed.csv` | 10 | 59e28ba7df25 |
| `results/r2gate2/modeA_winners_floor_analytic.csv` | 2 | 5b8e63829c81 |
| `results/r2gate2/modeA_winners_floor_empirical.csv` | 10 | 9c3ae8d71e36 |
| `results/r2gate2/modeA_winners_floor_ladder.csv` | 4 | 7f0c73d4c10e |
| `results/r2gate2/modeA_winners_floor_sweep.csv` | 600 | 03f892fd70c2 |
| `results/r2gate2/modeA_winners_family.csv` | 6 | 7ef50715123b |
| `results/r2gate2/modeA_winners_nullstrat.csv` | 7,844 | 263264bb7067 |
| `results/r2gate2/modeA_winners_recon_distortion.csv` | 7,844 | 67a4ec35ea71 |
| `results/r2gate2/modeA_gate3_passersbook_winners.csv` | 15 | 76d034a82b85 |
| `results/r2gate2/modeA_gate3_passersbook_winners_nulls.csv` | 30 | 09f275e0ca35 |
| `results/r2gate2/modeA_overlay_curves_winners.csv` | 194 | 8a9eea76697f |
