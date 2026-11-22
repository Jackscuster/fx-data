# MODE B — WINNERS, NO GATES

Generated 2026-11-22 14:35 by `code/l2r2winners.py`, read-only off the gate 2 bank and the gate 3 scoring. **Nothing is filtered before it is measured**: all 273,780 strategies are recorded on both unseen records, and the only cut is the LUCK FLOOR, which is a statement about chance rather than a preference about settings. Individual strategies first; the book last.


## 0. The number Jack buys: PROP RETURN

Yearly return when sized so the worst dip equals **3.6%** — max DD for a strategy, trade-year DIP95 for a book. Target **12% a year**.

For a strategy the arithmetic collapses to `0.72 x return/DD`, so prop return and return-per-drawdown are the same ranking and the 12% line is exactly **return/DD >= 16.67**.

**0 of 2 winners clear 12% at prop sizing.** Best is **2.38% a year** (return/DD 3.31 against the 16.67 needed) — short of the line by a factor of 5.0.


## 1. The universe, and the two unseen records

Per (strategy, stream), two records that the tuner never saw: the five stitched TRADE years 2016-2020, and the five GRADE years 2015-2019 as an independent second read. Each year uses the settings tuned before it — the walk forward as built.


**Observed t**, from `results/r2gate2/modeB_winners_t_observed.csv`:

| record | stream | n_finite | t_max | t_p99 | t_median |
|---|---|---|---|---|---|
| trade | ALL | 1,073,096 | 5.74 | 2.052 | -1.163 |
| grade | ALL | 1,073,070 | 6.718 | 2.314 | -0.9195 |


The t-statistic is **exact and not stored**: `l2tune` computes `sharpe = mean/sd x sqrt(252)` on per-trade R, so `sd = mean sqrt(252)/sharpe` and the per-year sum of squares is `sd^2 (n-1) + n mean^2`; those sum across the five years, so the pooled t is recovered without re-scoring. Verified against direct re-scoring on 10 records, agreeing to five decimals.


**Three fields are NOT exact from the bank**, and each is named where it appears: stitched max DD (summed per-year, gate 3's own stitched recipe, an upper bound), stitched Sortino (the mean of the five per-year figures), and longest losing streak (needs the ordered trade list, which the Scorer discards).


## 2. The luck floors

**(a) Analytic**, from `results/r2gate2/modeB_winners_floor_analytic.csv`:

| basis | M | alpha | t_max_of_M | t_bonferroni |
|---|---|---|---|---|
| strategies, as Jack specified | 273,780 | 0.05 | 5.081 | 5.216 |
| strategy x stream cells, which is what is actually compared | 1,095,120 | 0.05 | 5.339 | 5.467 |


Both lines assume independent tries and normal t. FX trade R is fat-tailed, the 28 pairs overlap in time, and a strategy's four streams share settings — all of which inflate real t. **These lines are therefore optimistic**: clearing one is the weakest version of the question.


**(b) Empirical**, a per-strategy random-entry null, from `results/r2gate2/modeB_winners_floor_empirical.csv`:

| space | null_mean | null_sd | mu | sigma | n_blocks | block_size | M | expected_best | pct |
|---|---|---|---|---|---|---|---|---|---|
| t | -0.4847 | 1.024 | 3.168 | 0.262 | 20 | 7,847 | 1,095,120 | 4.613 | 5.24 |
| expectancy_R | -0.02199 | 0.06403 | 0.4386 | 0.1846 | 20 | 7,847 | 1,095,120 | 1.457 | 1.898 |


Every real trade keeps its direction, units, cost and HOLD; its entry moves to a uniformly random bar in the same trade year on the same pair; R is recomputed from the price path. The floor is taken in **t-space** and the reason is measured, not asserted: the reconstruction is systematically more negative than the engine in LEVEL (see `modeB_winners_recon_distortion.csv`), but on t the median engine/reconstruction ratio is 0.924 — the engine runs slightly lower than the space the floor is fitted in, so using it is mildly **conservative**. The expectancy-space fit is reported and NOT used: its Gumbel sigma exceeds its parent sd, the signature of a fat-tailed parent outside the Gumbel domain.


**The ladder.** The winner count moves with which line binds, so the choice is shown rather than buried:

| basis | t_analytic | t_empirical | t_binding | n_winners | is_default |
|---|---|---|---|---|---|
| stated | 5.081 | 5.24 | 5.24 | 2 | 1 |
| bonf | 5.216 | 5.24 | 5.24 | 2 | 0 |
| cell | 5.339 | 5.24 | 5.339 | 2 | 0 |
| cellbonf | 5.467 | 5.24 | 5.467 | 1 | 0 |


## 3. The floor sweep

How many clear each level, and what they earned, from `results/r2gate2/modeB_winners_floor_sweep.csv` (600 rows over all streams):

| t_floor | n_clearing | mean_trade_expectancy_R | mean_trade_total_R |
|---|---|---|---|
| 0 | 2.204e+05 | 0.04241 | 11.54 |
| 0.2919 | 1.614e+05 | 0.05507 | 14.92 |
| 0.5837 | 1.14e+05 | 0.06804 | 18.26 |
| 0.8756 | 7.715e+04 | 0.08119 | 21.6 |
| 1.167 | 5.023e+04 | 0.09415 | 24.9 |
| 1.459 | 3.132e+04 | 0.1069 | 28.16 |
| 1.751 | 1.895e+04 | 0.1191 | 31.28 |
| 2.043 | 1.09e+04 | 0.131 | 34.27 |
| 2.335 | 5990 | 0.1432 | 37.52 |
| 2.627 | 3175 | 0.1546 | 40.73 |
| 2.919 | 1618 | 0.1673 | 43.93 |
| 3.211 | 806 | 0.1795 | 47.22 |
| 3.502 | 402 | 0.192 | 49.43 |
| 3.794 | 183 | 0.1954 | 52.08 |
| 4.086 | 81 | 0.2039 | 53.54 |
| 4.378 | 36 | 0.1954 | 61.5 |
| 4.67 | 16 | 0.1889 | 68.55 |
| 4.962 | 8 | 0.2391 | 60.97 |
| 5.254 | 4 | 0.3003 | 61.49 |
| 5.545 | 1 | 0.5813 | 11.63 |


## 4. The non-luck winners

Above BOTH floors, **>= 50 trades in every unseen year**, positive in **>= 4 of 5** trade years.


**2 winners.** Every one is listed in `results/r2gate2/modeB_winners.csv` with its settings and per-year R.

| stream | sid | t_stat | trade_n_trades | trade_total_R | trade_max_dd_R_sumyr | trade_dd_pct_of_gross | trade_return_per_dd | prop_return_pct_per_year | trade_worst_year_R | trade_win_rate | years_positive |
|---|---|---|---|---|---|---|---|---|---|---|---|
| trend-allon | waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|fantail_vma|adx_dmi_exit | 5.413 | 584 | 93.43 | 28.27 | 13.47 | 3.305 | 2.38 | 8.164 | 0.4178 | 5 |
| trend-allon | lemantrend_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | 5.538 | 846 | 100.7 | 35.67 | 13.8 | 2.823 | 2.033 | 7.122 | 0.4113 | 5 |


**Stream composition: trend-allon 2.**


Per-year R for each winner:

| stream | sid | R_2016 | R_2017 | R_2018 | R_2019 | R_2020 |
|---|---|---|---|---|---|---|
| trend-allon | waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|fantail_vma|adx_dmi_exit | 17.83 | 17.01 | 31.38 | 19.04 | 8.164 |
| trend-allon | lemantrend_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | 7.122 | 27.64 | 42.61 | 13.02 | 10.29 |


### Top 30 by t-statistic, and by return-to-drawdown

Drawdown is on every row, as asked. With 2 winners both tables are the whole set.


**By t-statistic** (`results/r2gate2/modeB_winners_top30_t.csv`):

| stream | sid | t_stat | trade_total_R | trade_max_dd_R_sumyr | trade_return_per_dd | prop_return_pct_per_year |
|---|---|---|---|---|---|---|
| trend-allon | lemantrend_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | 5.538 | 100.7 | 35.67 | 2.823 | 2.033 |
| trend-allon | waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|fantail_vma|adx_dmi_exit | 5.413 | 93.43 | 28.27 | 3.305 | 2.38 |


**By return / max DD** (`results/r2gate2/modeB_winners_top30_retdd.csv`):

| stream | sid | t_stat | trade_total_R | trade_max_dd_R_sumyr | trade_return_per_dd | prop_return_pct_per_year |
|---|---|---|---|---|---|---|
| trend-allon | waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|fantail_vma|adx_dmi_exit | 5.413 | 93.43 | 28.27 | 3.305 | 2.38 |
| trend-allon | lemantrend_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | 5.538 | 100.7 | 35.67 | 2.823 | 2.033 |


**By prop return** (`results/r2gate2/modeB_winners_top30_prop.csv`):

| stream | sid | t_stat | trade_total_R | trade_max_dd_R_sumyr | trade_return_per_dd | prop_return_pct_per_year |
|---|---|---|---|---|---|---|
| trend-allon | waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|fantail_vma|adx_dmi_exit | 5.413 | 93.43 | 28.27 | 3.305 | 2.38 |
| trend-allon | lemantrend_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | 5.538 | 100.7 | 35.67 | 2.823 | 2.033 |


## 5. Family support

Cousins are same (c1, c2). A winner alone in its family is the shape a lucky draw takes; one surrounded by near-winners is the shape a real effect takes.

| stream | family_c1_c2 | winner_t | n_cousins | cousin_t_median | cousin_t_max | cousins_t_over_2 | cousins_t_over_3 | cousins_positive_pct | lone_survivor |
|---|---|---|---|---|---|---|---|---|---|
| trend-allon | lemantrend_signals|hieken_ashi_smoothed_signals | 5.538 | 179 | 1.024 | 4.838 | 53 | 15 | 70.39 | 0 |
| trend-allon | waddah_attar_explosion_signals|hieken_ashi_smoothed_signals | 5.413 | 179 | 0.8302 | 5.023 | 38 | 9 | 68.72 | 0 |


**0 of 2 flagged lone survivors.**


## 6. The winners' book — LAST, and descriptive only

**This book's membership was chosen with sight of the years it reports.** Its return is therefore DESCRIPTIVE and is not evidence of anything. The luck floor in section 2 is the evidence. The book answers a different question: if you had held exactly these, equally weighted, what would the drawdown have looked like.

| step | book | budget | members | trade_total_pct | trade_max_dd_pct | trade_dip95_pct | trade_sortino | trade_calmar |
|---|---|---|---|---|---|---|---|---|
| 2011-2014 | allon | team1 | 2 | 1.538 | 1.028 | 2.19 | 1.152 | 1.496 |
| 2011-2014 | allon | team2 | 2 | 2.306 | 1.542 | 3.285 | 1.152 | 1.496 |
| 2012-2015 | allon | team1 | 2 | 2.459 | 0.5738 | 1.285 | 2.71 | 4.286 |
| 2012-2015 | allon | team2 | 2 | 3.689 | 0.8606 | 1.928 | 2.71 | 4.286 |
| 2013-2016 | allon | team1 | 2 | 6.559 | 0.8458 | 1.506 | 5.155 | 7.754 |
| 2013-2016 | allon | team2 | 2 | 9.838 | 1.269 | 2.26 | 5.155 | 7.754 |
| 2014-2017 | allon | team1 | 2 | 4.121 | 1.31 | 2.311 | 2.688 | 3.146 |
| 2014-2017 | allon | team2 | 2 | 6.167 | 1.965 | 3.385 | 2.777 | 3.139 |
| 2015-2018 | allon | team1 | 2 | 1.488 | 1.406 | 2.697 | 1.106 | 1.058 |
| 2015-2018 | allon | team2 | 2 | 2.232 | 2.109 | 4.045 | 1.106 | 1.058 |


The ROUTED book is **empty** — blank rows, not zeros. No winner is a routed-stream winner, so it has no members.


### Full KPI table


### TEAM 1

| KPI | ALWAYS-ON |
|---|---|
| median year | 2.46% |
| average year | 3.23% |
| worst year | 1.49% |
| best year | 6.56% |
| total 2016-2020 | 16.16% |
| CAGR | 3.23% |
| worst day | -0.65% |
| max drawdown | -1.63% |
| DIP95 (worst step) | 2.70% |
| Sharpe | 1.69 |
| Sortino | 2.45 |
| Calmar (total / max DD, the shipped bar) | 9.91 |
| Calmar (CAGR / max DD) | 1.98 |
| profit factor (trades, median step) | 1.38 |
| win rate (trades, median step) | 54.70% |
| positive years of 5 | 5 |
| retention (median step) | 2.12 |
| steps flagged FIT of 5 | 0 |

Per year:

- ALWAYS-ON: 2016: +1.54% | 2017: +2.46% | 2018: +6.56% | 2019: +4.12% | 2020: +1.49%

### TEAM 2

| KPI | ALWAYS-ON |
|---|---|
| median year | 3.69% |
| average year | 4.85% |
| worst year | 2.23% |
| best year | 9.84% |
| total 2016-2020 | 24.23% |
| CAGR | 4.85% |
| worst day | -0.97% |
| max drawdown | -2.45% |
| DIP95 (worst step) | 4.04% |
| Sharpe | 1.70 |
| Sortino | 2.47 |
| Calmar (total / max DD, the shipped bar) | 9.90 |
| Calmar (CAGR / max DD) | 1.98 |
| profit factor (trades, median step) | 1.38 |
| win rate (trades, median step) | 54.70% |
| positive years of 5 | 5 |
| retention (median step) | 2.12 |
| steps flagged FIT of 5 | 0 |

Per year:

- ALWAYS-ON: 2016: +2.31% | 2017: +3.69% | 2018: +9.84% | 2019: +6.17% | 2020: +2.23%

### Its nulls

| null | scope | step | book | budget | members | real | n_draws | null_mean | null_p95 | p_one_sided |
|---|---|---|---|---|---|---|---|---|---|---|
| identity | full field | 2011-2014 | allon | team1 |  | 1.538 | 200 | 1.057 | 3.974 | 0.5 |
| identity | full field | 2011-2014 | allon | team2 |  | 2.306 | 200 | 1.577 | 5.961 | 0.49 |
| identity | full field | 2012-2015 | allon | team1 |  | 2.459 | 200 | 1.344 | 2.468 | 0.22 |
| identity | full field | 2012-2015 | allon | team2 |  | 3.689 | 200 | 1.996 | 3.701 | 0.365 |
| identity | full field | 2013-2016 | allon | team1 |  | 6.559 | 200 | 2.698 | 6.559 | 0 |
| identity | full field | 2013-2016 | allon | team2 |  | 9.838 | 200 | 4.237 | 9.838 | 0.175 |
| identity | full field | 2014-2017 | allon | team1 |  | 4.121 | 200 | 3.859 | 7.933 | 0.53 |
| identity | full field | 2014-2017 | allon | team2 |  | 6.167 | 200 | 5.859 | 12.15 | 0.475 |
| identity | full field | 2015-2018 | allon | team1 |  | 1.488 | 200 | 2.623 | 10.21 | 0.415 |
| identity | full field | 2015-2018 | allon | team2 |  | 2.232 | 200 | 4.794 | 15.32 | 0.67 |
| shuffle | passers, full | 2011-2014 | allon | team1 | 2 | 1.538 | 19 | 1.538 | 1.538 | 1 |
| shuffle | passers, full | 2011-2014 | allon | team2 | 2 | 2.306 | 19 | 2.306 | 2.306 | 1 |
| shuffle | passers, full | 2012-2015 | allon | team1 | 2 | 2.459 | 19 | 2.459 | 2.459 | 1 |
| shuffle | passers, full | 2012-2015 | allon | team2 | 2 | 3.689 | 19 | 3.689 | 3.689 | 1 |
| shuffle | passers, full | 2013-2016 | allon | team1 | 2 | 6.559 | 19 | 6.559 | 6.559 | 1 |
| shuffle | passers, full | 2013-2016 | allon | team2 | 2 | 9.838 | 19 | 9.838 | 9.838 | 1 |
| shuffle | passers, full | 2014-2017 | allon | team1 | 2 | 4.121 | 19 | 4.121 | 4.121 | 1 |
| shuffle | passers, full | 2014-2017 | allon | team2 | 2 | 6.167 | 19 | 6.167 | 6.167 | 1 |
| shuffle | passers, full | 2015-2018 | allon | team1 | 2 | 1.488 | 19 | 1.488 | 1.488 | 1 |
| shuffle | passers, full | 2015-2018 | allon | team2 | 2 | 2.232 | 19 | 2.232 | 2.232 | 1 |
| random-entry | passers, full | 2011-2014 | allon | team1 | 2 | 1.538 | 19 | -0.1599 | 0.6852 | 0.05263 |
| random-entry | passers, full | 2011-2014 | allon | team2 | 2 | 2.306 | 19 | -0.2398 | 1.028 | 0.05263 |
| random-entry | passers, full | 2012-2015 | allon | team1 | 2 | 2.459 | 19 | 0.4206 | 1.824 | 0 |
| random-entry | passers, full | 2012-2015 | allon | team2 | 2 | 3.689 | 19 | 0.6309 | 2.736 | 0 |
| random-entry | passers, full | 2013-2016 | allon | team1 | 2 | 6.559 | 19 | -0.1095 | 1.176 | 0 |
| random-entry | passers, full | 2013-2016 | allon | team2 | 2 | 9.838 | 19 | -0.1643 | 1.763 | 0 |
| random-entry | passers, full | 2014-2017 | allon | team1 | 2 | 4.121 | 17 | -0.09688 | 0.4028 | 0 |
| random-entry | passers, full | 2014-2017 | allon | team2 | 2 | 6.167 | 17 | -0.1453 | 0.6042 | 0 |
| random-entry | passers, full | 2015-2018 | allon | team1 | 2 | 1.488 | 14 | -0.03691 | 0.408 | 0 |
| random-entry | passers, full | 2015-2018 | allon | team2 | 2 | 2.232 | 14 | -0.05536 | 0.612 | 0 |


## 6b. Pair routing — a STANDING test

Jack, 22 Nov: *"Pair routing is a standing test, not a one-off: every mode, every re-tune, every winners pipeline from now on reports the pair-routing sweep."* Chosen on tuning years, traded on unseen years, against a random-pair null of the same size.

| rule | K | real_return_per_dd | random_null | real_beats_null | prop_return_pct | clears_12pct |
|---|---|---|---|---|---|---|
| topk | 1 | 1.454 | 2.279 | 0 | 1.047 | 0 |
| topk | 2 | 1.297 | 1.585 | 0 | 0.9337 | 0 |
| topk | 3 | 1.269 | 1.29 | 0 | 0.9135 | 0 |
| topk | 4 | 1.333 | 1.422 | 0 | 0.9599 | 0 |
| topk | 5 | 0.8727 | 1.357 | 0 | 0.6283 | 0 |
| topk | 6 | 1.046 | 1.495 | 0 | 0.7532 | 0 |
| topk | 7 | 0.9973 | 1.247 | 0 | 0.7181 | 0 |
| topk | 8 | 1.081 | 1.395 | 0 | 0.7781 | 0 |
| topk | 9 | 1.246 | 1.252 | 0 | 0.897 | 0 |
| topk | 10 | 1.081 | 1.139 | 0 | 0.7785 | 0 |
| topk | 11 | 0.9209 | 1.213 | 0 | 0.663 | 0 |
| topk | 12 | 0.8445 | 1.229 | 0 | 0.6081 | 0 |
| topk | 13 | 0.8351 | 1.19 | 0 | 0.6012 | 0 |
| topk | 14 | 0.9377 | 1.187 | 0 | 0.6752 | 0 |
| topk | 15 | 1.068 | 1.206 | 0 | 0.7693 | 0 |
| topk | 16 | 1.13 | 1.233 | 0 | 0.8136 | 0 |
| topk | 17 | 1.189 | 1.199 | 0 | 0.8564 | 0 |
| topk | 18 | 1.171 | 1.272 | 0 | 0.843 | 0 |
| topk | 19 | 1.151 | 1.245 | 0 | 0.8288 | 0 |
| topk | 20 | 1.186 | 1.212 | 0 | 0.8539 | 0 |
| topk | 21 | 1.227 | 1.188 | 1 | 0.8833 | 0 |
| topk | 22 | 1.292 | 1.174 | 1 | 0.9306 | 0 |
| topk | 23 | 1.429 | 1.217 | 1 | 1.029 | 0 |
| topk | 24 | 1.382 | 1.207 | 1 | 0.9951 | 0 |
| topk | 25 | 1.365 | 1.202 | 1 | 0.9831 | 0 |
| topk | 26 | 1.269 | 1.209 | 1 | 0.9139 | 0 |
| topk | 27 | 1.271 | 1.219 | 1 | 0.915 | 0 |
| topk | 28 | 1.21 | 1.21 | 0 | 0.8712 | 0 |
| threshold |  | 1.221 |  |  | 0.8793 | 0 |
| topk_dir |  | 1.397 |  |  | 1.006 | 0 |
| threshold_dir |  | 1.243 |  |  | 0.8953 | 0 |


All-28 baseline return/DD **1.210** (prop return 0.87%). The real rule beats the random-pair null at **7 of 28** values of K, and **0** rows clear 12% at prop sizing.


**The drawdown basis in this section sums per (pair, direction, year) drawdowns** and is a looser bound than the strategy-level figure used elsewhere in this document, so its level is not comparable to section 4 and its prop return is a floor. Real and null share the basis, so the comparison within the section is sound. Full detail in `results/r2gate2/modeB_winners_pairrouted.csv` and `WINNERS_BY_PAIR.md`.


## 7. Overlay curves

Swept over their full range with **no fixed value chosen**, from `results/r2gate2/modeB_overlay_curves_winners.csv` (194 points). Return against max drawdown on the unseen years at the budget.

| book | budget | overlay | p1 | p2 | total_pct | max_dd_pct | return_per_dd | implementable |
|---|---|---|---|---|---|---|---|---|
| allon | team1 | none |  |  | 16.16 | 1.632 | 9.907 | baseline |
| allon | team1 | equity_pause | 1.253 | 0.3263 | 15.52 | 1.406 | 11.03 | yes -- decided at day boundaries |
| allon | team1 | kill_switch | 1.082 |  | 14.63 | 1.283 | 11.4 | yes -- decided at day boundaries |
| allon | team1 | daily_loss_stop | 0.06473 |  | 34.87 | 0.5073 | 68.74 | UPPER BOUND -- needs intraday data to evaluate |
| allon | team2 | none |  |  | 24.23 | 2.448 | 9.901 | baseline |
| allon | team2 | equity_pause | 1.879 | 0.4895 | 23.26 | 2.109 | 11.03 | yes -- decided at day boundaries |
| allon | team2 | kill_switch | 1.623 |  | 21.93 | 1.925 | 11.39 | yes -- decided at day boundaries |
| allon | team2 | daily_loss_stop | 0.09709 |  | 52.12 | 0.7609 | 68.5 | UPPER BOUND -- needs intraday data to evaluate |


**The daily loss stop is an UPPER BOUND, not a result.** Clipping a daily series at -x assumes the breach is caught exactly at -x, costs nothing to exit and forfeits no intraday recovery — a free lunch on daily data. The pause and the kill switch decide at DAY BOUNDARIES, which a daily series evaluates honestly.


## Provenance

| file | rows | md5 |
|---|---|---|
| `results/r2gate2/modeB_winners.csv` | 2 | 944799a18e83 |
| `results/r2gate2/modeB_winners_t_observed.csv` | 10 | bba093817f40 |
| `results/r2gate2/modeB_winners_floor_analytic.csv` | 2 | 5b8e63829c81 |
| `results/r2gate2/modeB_winners_floor_empirical.csv` | 10 | cd4d434348fc |
| `results/r2gate2/modeB_winners_floor_ladder.csv` | 4 | 97695a21bb59 |
| `results/r2gate2/modeB_winners_floor_sweep.csv` | 600 | 9afe90066b6d |
| `results/r2gate2/modeB_winners_family.csv` | 2 | 87589011dc8b |
| `results/r2gate2/modeB_winners_nullstrat.csv` | 7,847 | 36e7d0cb1f2f |
| `results/r2gate2/modeB_winners_recon_distortion.csv` | 7,847 | 0b4f160be9f6 |
| `results/r2gate2/modeB_gate3_passersbook_winners.csv` | 15 | ffe41d35b615 |
| `results/r2gate2/modeB_gate3_passersbook_winners_nulls.csv` | 30 | 8cb2249ad2a1 |
| `results/r2gate2/modeB_overlay_curves_winners.csv` | 194 | ccea41b1314f |
