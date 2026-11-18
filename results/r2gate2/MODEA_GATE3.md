# MODE A — GATE 3

Generated 2026-11-18 14:40 by `code/l2r2gate3.py`. **No new tuning**: every configuration here was already chosen by gate 2 and is re-scored, nothing is searched. Every number below is read back out of the CSV named beside it.


## The bars, unchanged

| bar | value | binds |
|---|---|---|
| expectancy | >= 0.15 R | yes |
| profit factor | >= 1.5 | yes |
| Sortino | >= 1.3 | yes |
| Calmar | >= 1.0 | yes |
| max DD | <= 10% of the strategy's OWN gross profit | yes |
| Sharpe | reported | **no — binds nowhere** |


Costs are charged throughout (`cost_table_h22`, restated per fault #27).


**Why this cost an engine pass.** The gate 2 bank stores `n, sum_r, gain, loss, n_win` per (strategy, stream, step, year), which gives expectancy, PF, win rate and trade count — but Sortino needs the downside deviation of per-trade R, and max DD and Calmar need the ordered equity curve. Neither is banked, so each winner was re-scored through the shipped `l2tune.Scorer` with one window per calendar year; the KPIs come from `_agg`, the same aggregator every other result in this project used.


## Sources

| section | file | rows | md5 |
|---|---|---|---|
| counts | results/r2gate2/modeA_gate3_counts.csv | 20 | 8a4cd6deb003 |
| passers | results/r2gate2/modeA_gate3_passers.csv | 21 | fd76d88fa244 |
| null | results/r2gate2/modeA_gate3_null.csv | 20 | 3c309fcc6313 |
| stitched | results/r2gate2/modeA_gate3_stitched.csv | 0 | 68b329da9893 |
| stitched_counts | results/r2gate2/modeA_gate3_stitched_counts.csv | 4 | 9025eb474a13 |


**Missing sources, left empty rather than filled in:** book, booknull


## 1. The bars on the GRADE year (year 5, unseen by the tuner)

| stream | step | n_field | n_clears_grade | n_also_clears_trade | pct_of_field |
|---|---|---|---|---|---|
| chop-allon | 2011-2014 | 200 | 0 | 0 | 0 |
| chop-allon | 2012-2015 | 200 | 0 | 0 | 0 |
| chop-allon | 2013-2016 | 200 | 0 | 0 | 0 |
| chop-allon | 2014-2017 | 200 | 2 | 0 | 1 |
| chop-allon | 2015-2018 | 200 | 1 | 0 | 0.5 |
| chop-routed | 2011-2014 | 200 | 8 | 0 | 4 |
| chop-routed | 2012-2015 | 200 | 0 | 0 | 0 |
| chop-routed | 2013-2016 | 200 | 0 | 0 | 0 |
| chop-routed | 2014-2017 | 200 | 1 | 0 | 0.5 |
| chop-routed | 2015-2018 | 200 | 0 | 0 | 0 |
| trend-allon | 2011-2014 | 200 | 0 | 0 | 0 |
| trend-allon | 2012-2015 | 200 | 0 | 0 | 0 |
| trend-allon | 2013-2016 | 200 | 1 | 0 | 0.5 |
| trend-allon | 2014-2017 | 200 | 1 | 0 | 0.5 |
| trend-allon | 2015-2018 | 200 | 2 | 1 | 1 |
| trend-routed | 2011-2014 | 200 | 1 | 0 | 0.5 |
| trend-routed | 2012-2015 | 200 | 1 | 0 | 0.5 |
| trend-routed | 2013-2016 | 200 | 2 | 0 | 1 |
| trend-routed | 2014-2017 | 200 | 0 | 0 | 0 |
| trend-routed | 2015-2018 | 200 | 1 | 0 | 0.5 |


Totals by stream:

| stream | n_clears_grade | n_also_clears_trade |
|---|---|---|
| chop-allon | 3 | 0 |
| chop-routed | 9 | 0 |
| trend-allon | 4 | 1 |
| trend-routed | 5 | 0 |


Every passer is listed in `results/r2gate2/modeA_gate3_passers.csv` with its settings, its grade-year KPIs and its trade-year KPIs. The first 20:

| step | stream | sid | grade_expectancy_R | grade_profit_factor | grade_sortino | grade_calmar | grade_max_dd_R | grade_n | grade_sharpe | trade_expectancy_R | trade_profit_factor | trade_sortino | trade_calmar | trade_max_dd_R | trade_win_rate | trade_n | trade_sharpe | clears_trade_year |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2011-2014 | trend-routed | adx_dmi_signals|adx_dmi_signals|williams_vix_fix_volume_signals|t3_baseline|adx_dmi_exit | 0.4865 | 3.419 | 44.57 | 7.083 | 2.335 | 34 | 6.267 | 0.01662 | 1.068 | 1.167 | 0.1613 | 3.915 | 0.3158 | 38 | 0.4297 | 0 |
| 2011-2014 | chop-routed | adx_dmi_signals|adx_dmi_signals|fractal_dimension_volume_signals|alma_baseline|adx_dmi_exit | 0.3218 | 1.598 | 18.76 | 3.762 | 4.704 | 55 | 3.682 | -0.115 | 0.8405 | -6.501 | -0.5205 | 8.615 | 0.4103 | 39 | -1.341 | 0 |
| 2011-2014 | chop-routed | adx_dmi_signals|adx_dmi_signals|fractal_dimension_volume_signals|mcginley_dynamic_index|adx_dmi_exit | 0.3268 | 1.703 | 48.52 | 4.48 | 4.085 | 56 | 4.151 | -0.1015 | 0.8394 | -8.52 | -0.4829 | 8.193 | 0.359 | 39 | -1.335 | 0 |
| 2011-2014 | chop-routed | adx_dmi_signals|adx_dmi_signals|mass_index_volume_signals|frama_baseline|adx_dmi_exit | 0.2814 | 1.582 | 43.4 | 3.731 | 4.375 | 58 | 3.565 | -0.2276 | 0.6627 | -17.99 | -0.8289 | 11.81 | 0.3023 | 43 | -3.145 | 0 |
| 2011-2014 | chop-routed | adx_dmi_signals|adx_dmi_signals|vertical_horizontal_filter_volume_signals|mcginley_dynamic_index|adx_dmi_exit | 0.2821 | 1.584 | 42.67 | 4.244 | 3.722 | 56 | 3.575 | -0.1856 | 0.7193 | -13.58 | -0.8861 | 5.864 | 0.3214 | 28 | -2.496 | 0 |
| 2011-2014 | chop-routed | adx_dmi_signals|adx_dmi_signals|waddah_attar_explosion_volume_signals|alma_baseline|adx_dmi_exit | 0.4325 | 2.011 | 933.6 | 7.735 | 3.076 | 55 | 5.515 | 0.01193 | 1.02 | 1.747 | 0.06738 | 7.793 | 0.4091 | 44 | 0.1534 | 0 |
| 2011-2014 | chop-routed | adx_dmi_signals|adx_dmi_signals|waddah_attar_explosion_volume_signals|frama_baseline|adx_dmi_exit | 0.4922 | 2.22 | 1023 | 9.156 | 2.043 | 38 | 6.306 | -0.2257 | 0.6721 | -30.23 | -1.052 | 6.865 | 0.3125 | 32 | -3.055 | 0 |
| 2011-2014 | chop-routed | adx_dmi_signals|adx_dmi_signals|waddah_attar_explosion_volume_signals|vidya|adx_dmi_exit | 0.4369 | 2.026 | 937.2 | 6.853 | 3.06 | 48 | 5.566 | -0.02244 | 0.963 | -3.27 | -0.1254 | 7.694 | 0.3953 | 43 | -0.2893 | 0 |
| 2011-2014 | chop-routed | adx_dmi_signals|aroon_signals|choppiness_index_volume_signals|alma_baseline|adx_dmi_exit | 0.3543 | 1.783 | 46.14 | 5.073 | 3.073 | 44 | 4.505 | -0.07233 | 0.8844 | -10.37 | -0.313 | 9.244 | 0.375 | 40 | -0.9428 | 0 |
| 2012-2015 | trend-routed | adx_dmi_signals|adx_dmi_signals|mass_index_volume_signals|t3_baseline|adx_dmi_exit | 0.5784 | 10.53 | 45.06 | 9.63 | 0.7208 | 12 | 15.5 | -0.5177 | 0 | -3.75e+04 | -1.333 | 1.553 | 0 | 4 | -3.75e+04 | 0 |
| 2013-2016 | trend-routed | adx_dmi_signals|adx_dmi_signals|mass_index_volume_signals|rma_baseline|adx_dmi_exit | 0.3575 | 41.79 | 7616 | 79.2 | 0.01805 | 4 | 13.11 | -0.2225 | 0.3544 | -15.94 | -1.292 | 1.034 | 0.1667 | 6 | -6.95 | 0 |
| 2013-2016 | trend-routed | adx_dmi_signals|adx_dmi_signals|variance_volume_signals|sma_baseline|adx_dmi_exit | 0.6403 | 23.08 | 67.64 | 23.05 | 0.2222 | 8 | 13.24 | -0.3259 | 0.1708 | -29.43 | -1.078 | 6.651 | 0.09091 | 22 | -13.51 | 0 |
| 2013-2016 | trend-allon | adx_dmi_signals|aroon_signals|chaikin_volatility_volume_signals|mcginley_dynamic_index|adx_dmi_exit | 0.4027 | 2.954 | 38.82 | 7.701 | 1.046 | 20 | 6.658 | -0.01469 | 0.9543 | -1.914 | -0.07586 | 5.035 | 0.3462 | 26 | -0.3215 | 0 |
| 2014-2017 | trend-allon | adx_dmi_signals|aroon_signals|chaikin_volatility_volume_signals|tma_baseline|adx_dmi_exit | 0.3616 | 3.544 | 24.98 | 7.644 | 1.041 | 22 | 8.384 | -0.1517 | 0.5104 | -12.85 | -0.8213 | 6.279 | 0.2353 | 34 | -4.772 | 0 |
| 2014-2017 | chop-routed | adx_dmi_signals|aroon_signals|choppiness_index_volume_signals|fantail_vma|adx_dmi_exit | 0.7253 | 3.379 | 4400 | 11.86 | 1.04 | 17 | 9.822 | -0.3444 | 0.5231 | -22.33 | -0.8094 | 9.787 | 0.2609 | 23 | -4.931 | 0 |
| 2014-2017 | chop-allon | adx_dmi_signals|adx_dmi_signals|vertical_horizontal_filter_volume_signals|ema_baseline|adx_dmi_exit | 0.525 | 2.477 | 22.76 | 6.689 | 1.177 | 15 | 6.862 | -0.2686 | 0.624 | -333 | -0.5662 | 6.167 | 0.3077 | 13 | -3.578 | 0 |
| 2014-2017 | chop-allon | adx_dmi_signals|adx_dmi_signals|vertical_horizontal_filter_volume_signals|kama_baseline|adx_dmi_exit | 0.2588 | 1.549 | 15.48 | 3.791 | 4.232 | 62 | 3.353 | -0.3227 | 0.5528 | -26.59 | -0.8715 | 20.37 | 0.2727 | 55 | -4.592 | 0 |
| 2015-2018 | trend-routed | adx_dmi_signals|adx_dmi_signals|variance_volume_signals|ema_baseline|adx_dmi_exit | 0.5126 | 7.887 | 36.25 | 19.71 | 0.5202 | 20 | 11.34 | -0.2397 | 0.3049 | -29.85 | -1.115 | 4.73 | 0.09091 | 22 | -7.837 | 0 |
| 2015-2018 | trend-allon | adx_dmi_signals|adx_dmi_signals|choppiness_index_volume_signals|t3_baseline|adx_dmi_exit | 0.5706 | 5.03 | 47.98 | 12.08 | 1.039 | 22 | 8.944 | 0.5516 | 5.668 | 32.91 | 9.243 | 1.074 | 0.5 | 18 | 5.777 | 1 |
| 2015-2018 | trend-allon | adx_dmi_signals|adx_dmi_signals|vertical_horizontal_filter_volume_signals|sma_baseline|adx_dmi_exit | 0.3377 | 3.521 | 20.95 | 7.513 | 1.079 | 24 | 8.699 | 0.07789 | 1.298 | 6.48 | 0.5308 | 4.109 | 0.3929 | 28 | 1.662 | 0 |


## 2. Chance level — the identity null on the year roles

Each draw calls a randomly chosen year of the step the "grade" year and another the "trade" year, and applies the identical bars. **A caveat that belongs in the reading**: those draws can land on TUNE years, on which the settings were fitted, so the null is not a neutral yardstick — it is biased toward clearing. A real count BELOW the null mean is therefore the striking direction, not the reassuring one.

| stream | step | real_clears_grade | null_mean_clears | null_p95_clears | p_grade | real_also_clears_trade | null_mean_also_trade | p_also_trade |
|---|---|---|---|---|---|---|---|---|
| chop-allon | 2011-2014 | 0 | 5.1 | 15 | 1 | 0 | 0 | 1 |
| chop-allon | 2012-2015 | 0 | 2.1 | 6.1 | 1 | 0 | 0 | 1 |
| chop-allon | 2013-2016 | 0 | 2.2 | 5 | 1 | 0 | 0 | 1 |
| chop-allon | 2014-2017 | 2 | 1.1 | 1.55 | 0.1 | 0 | 0 | 1 |
| chop-allon | 2015-2018 | 1 | 1 | 3 | 0.6 | 0 | 0 | 1 |
| chop-routed | 2011-2014 | 8 | 3.8 | 7.1 | 0.1 | 0 | 0 | 1 |
| chop-routed | 2012-2015 | 0 | 3 | 10 | 1 | 0 | 0 | 1 |
| chop-routed | 2013-2016 | 0 | 3.4 | 11 | 1 | 0 | 0 | 1 |
| chop-routed | 2014-2017 | 1 | 4.6 | 14 | 0.7 | 0 | 0 | 1 |
| chop-routed | 2015-2018 | 0 | 6.8 | 19 | 1 | 0 | 0 | 1 |
| trend-allon | 2011-2014 | 0 | 5 | 11 | 1 | 0 | 0 | 1 |
| trend-allon | 2012-2015 | 0 | 2 | 5 | 1 | 0 | 0 | 1 |
| trend-allon | 2013-2016 | 1 | 2.6 | 5 | 0.9 | 0 | 0 | 1 |
| trend-allon | 2014-2017 | 1 | 1.3 | 4 | 0.4 | 0 | 0 | 1 |
| trend-allon | 2015-2018 | 2 | 2.7 | 5.1 | 0.9 | 1 | 0.1 | 0.1 |
| trend-routed | 2011-2014 | 1 | 8.1 | 14 | 1 | 0 | 0 | 1 |
| trend-routed | 2012-2015 | 1 | 4.4 | 12 | 0.8 | 0 | 0 | 1 |
| trend-routed | 2013-2016 | 2 | 2.4 | 6.55 | 0.6 | 0 | 0.2 | 1 |
| trend-routed | 2014-2017 | 0 | 3.2 | 5 | 1 | 0 | 0 | 1 |
| trend-routed | 2015-2018 | 1 | 1.6 | 4.1 | 0.8 | 0 | 0 | 1 |


## 3. The stitched trade years 2016-2020, all unseen

| stream | n_field | n_clears_stitched | pct_of_field |
|---|---|---|---|
| trend-routed | 200 | 0 | 0 |
| trend-allon | 200 | 0 | 0 |
| chop-routed | 200 | 0 | 0 |
| chop-allon | 200 | 0 | 0 |


**Nobody passes on the stitched record.**


## 4. The passers' book

_The passers' book has not been built; this section is empty rather than filled in from anywhere else._
