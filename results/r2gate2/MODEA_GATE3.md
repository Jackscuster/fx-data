# MODE A — GATE 3

Generated 2026-11-19 10:00 by `code/l2r2gate3.py`. **No new tuning**: every configuration here was already chosen by gate 2 and is re-scored, nothing is searched. Every number below is read back out of the CSV named beside it.


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
| counts | results/r2gate2/modeA_gate3_counts.csv | 20 | 7d8ef94bd5a5 |
| passers | results/r2gate2/modeA_gate3_passers.csv | 33,892 | 80ba745eb886 |
| null | results/r2gate2/modeA_gate3_null.csv | 20 | 92255ad512f6 |
| stitched | results/r2gate2/modeA_gate3_stitched.csv | 0 | 68b329da9893 |
| stitched_counts | results/r2gate2/modeA_gate3_stitched_counts.csv | 4 | 7c1ea5246872 |


**Missing sources, left empty rather than filled in:** book, booknull


## 1. The bars on the GRADE year (year 5, unseen by the tuner)

| stream | step | n_field | n_clears_grade | n_also_clears_trade | pct_of_field |
|---|---|---|---|---|---|
| chop-allon | 2011-2014 | 156,647 | 1,854 | 44 | 1.184 |
| chop-allon | 2012-2015 | 156,647 | 1,321 | 5 | 0.8433 |
| chop-allon | 2013-2016 | 156,647 | 1,344 | 53 | 0.858 |
| chop-allon | 2014-2017 | 156,647 | 3,213 | 13 | 2.051 |
| chop-allon | 2015-2018 | 156,647 | 238 | 1 | 0.1519 |
| chop-routed | 2011-2014 | 156,647 | 2,615 | 5 | 1.669 |
| chop-routed | 2012-2015 | 156,647 | 527 | 4 | 0.3364 |
| chop-routed | 2013-2016 | 156,647 | 716 | 4 | 0.4571 |
| chop-routed | 2014-2017 | 156,647 | 1,548 | 1 | 0.9882 |
| chop-routed | 2015-2018 | 156,647 | 122 | 0 | 0.07788 |
| trend-allon | 2011-2014 | 156,647 | 4,068 | 20 | 2.597 |
| trend-allon | 2012-2015 | 156,647 | 631 | 6 | 0.4028 |
| trend-allon | 2013-2016 | 156,647 | 855 | 26 | 0.5458 |
| trend-allon | 2014-2017 | 156,647 | 1,646 | 5 | 1.051 |
| trend-allon | 2015-2018 | 156,647 | 263 | 3 | 0.1679 |
| trend-routed | 2011-2014 | 156,647 | 6,872 | 50 | 4.387 |
| trend-routed | 2012-2015 | 156,647 | 1,094 | 20 | 0.6984 |
| trend-routed | 2013-2016 | 156,647 | 835 | 22 | 0.533 |
| trend-routed | 2014-2017 | 156,647 | 3,501 | 27 | 2.235 |
| trend-routed | 2015-2018 | 156,647 | 629 | 7 | 0.4015 |


Totals by stream:

| stream | n_clears_grade | n_also_clears_trade |
|---|---|---|
| chop-allon | 7,970 | 116 |
| chop-routed | 5,528 | 14 |
| trend-allon | 7,463 | 60 |
| trend-routed | 12,931 | 126 |


Every passer is listed in `results/r2gate2/modeA_gate3_passers.csv` with its settings, its grade-year KPIs and its trade-year KPIs. The first 20:

| step | stream | sid | grade_expectancy_R | grade_profit_factor | grade_sortino | grade_calmar | grade_max_dd_R | grade_n | grade_sharpe | trade_expectancy_R | trade_profit_factor | trade_sortino | trade_calmar | trade_max_dd_R | trade_win_rate | trade_n | trade_sharpe | clears_trade_year |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2011-2014 | trend-routed | adx_dmi_signals|adx_dmi_signals|williams_vix_fix_volume_signals|t3_baseline|adx_dmi_exit | 0.4865 | 3.419 | 44.57 | 7.083 | 2.335 | 34 | 6.267 | 0.01662 | 1.068 | 1.167 | 0.1613 | 3.915 | 0.3158 | 38 | 0.4297 | 0 |
| 2011-2014 | trend-routed | adx_dmi_signals|aroon_signals|williams_vix_fix_volume_signals|t3_baseline|adx_dmi_exit | 0.806 | 6.753 | 67.31 | 13.5 | 1.313 | 22 | 9.295 | 0.1206 | 1.567 | 7.86 | 1.153 | 2.093 | 0.35 | 20 | 2.786 | 0 |
| 2011-2014 | trend-routed | adx_dmi_signals|bears_bulls_impulse_signals|chaikin_volatility_volume_signals|mcginley_dynamic_index|adx_dmi_exit | 0.2182 | 3.259 | 21.06 | 8.029 | 1.033 | 38 | 6.016 | 0.07542 | 1.366 | 7.119 | 1.275 | 2.366 | 0.475 | 40 | 2.244 | 0 |
| 2011-2014 | trend-routed | adx_dmi_signals|bears_bulls_impulse_signals|variance_volume_signals|ema_baseline|adx_dmi_exit | 0.2742 | 3.218 | 24.3 | 9.45 | 0.7543 | 26 | 6.588 | 0.239 | 3.475 | 23.13 | 3.908 | 1.345 | 0.4545 | 22 | 5.425 | 0 |
| 2011-2014 | trend-routed | adx_dmi_signals|bears_bulls_impulse_signals|variance_volume_signals|wma_baseline|adx_dmi_exit | 0.2584 | 2.965 | 26.97 | 8.225 | 1.194 | 38 | 7.029 | 0.2548 | 3.483 | 25.43 | 5.494 | 1.855 | 0.625 | 40 | 7.807 | 0 |
| 2011-2014 | trend-routed | adx_dmi_signals|bears_bulls_impulse_signals|volatility_ratio_volume_signals|frama_baseline|adx_dmi_exit | 0.4957 | 5.252 | 20.91 | 8.632 | 1.493 | 26 | 10.11 | 0.04266 | 1.149 | 2.302 | 0.2646 | 6.128 | 0.4737 | 38 | 0.9781 | 0 |
| 2011-2014 | trend-routed | adx_dmi_signals|bears_bulls_impulse_signals|waddah_attar_explosion_volume_signals|ema_baseline|adx_dmi_exit | 0.295 | 2.721 | 20.04 | 6.759 | 1.047 | 24 | 6.03 | -0.09905 | 0.695 | -9.832 | -0.7326 | 5.949 | 0.2045 | 44 | -2.197 | 0 |
| 2011-2014 | trend-routed | adx_dmi_signals|bears_bulls_impulse_signals|waddah_attar_explosion_volume_signals|sma_baseline|adx_dmi_exit | 0.3742 | 3.662 | 23.76 | 7.86 | 1.047 | 22 | 7.622 | -0.1292 | 0.6227 | -13.02 | -0.7181 | 6.117 | 0.1765 | 34 | -2.764 | 0 |
| 2011-2014 | trend-routed | adx_dmi_signals|bears_bulls_impulse_signals|waddah_attar_explosion_volume_signals|tma_baseline|adx_dmi_exit | 0.4164 | 3.431 | 28.61 | 7.157 | 1.047 | 18 | 7.816 | -0.1157 | 0.6238 | -10.78 | -0.5581 | 5.805 | 0.2143 | 28 | -2.476 | 0 |
| 2011-2014 | trend-routed | adx_dmi_signals|bears_bulls_impulse_signals|waddah_attar_explosion_volume_signals|wma_baseline|adx_dmi_exit | 0.3275 | 2.752 | 22.26 | 6.88 | 1.047 | 22 | 6.369 | -0.08518 | 0.708 | -7.76 | -0.3815 | 5.805 | 0.2308 | 26 | -1.775 | 0 |
| 2011-2014 | trend-routed | adx_dmi_signals|bears_bulls_impulse_signals|williams_vix_fix_volume_signals|alma_baseline|adx_dmi_exit | 0.6517 | 5.449 | 46.11 | 8.949 | 1.019 | 14 | 9.917 | -0.07981 | 0.6593 | -5.526 | -0.3418 | 3.736 | 0.25 | 16 | -2.68 | 0 |
| 2011-2014 | trend-routed | adx_dmi_signals|bears_bulls_impulse_signals|williams_vix_fix_volume_signals|hma_baseline|adx_dmi_exit | 0.6549 | 9.903 | 39.04 | 17.9 | 1.024 | 28 | 12.76 | -0.2923 | 0.2476 | -35.77 | -0.8821 | 5.965 | 0.1667 | 18 | -10.84 | 0 |
| 2011-2014 | trend-routed | adx_dmi_signals|center_of_gravity_signals|williams_vix_fix_volume_signals|ema_baseline|adx_dmi_exit | 0.3789 | 3.415 | 29.27 | 8.848 | 1.028 | 24 | 8.19 | -0.05453 | 0.7709 | -4.092 | -0.3678 | 3.261 | 0.2273 | 22 | -1.566 | 0 |
| 2011-2014 | trend-routed | adx_dmi_signals|center_of_gravity_signals|williams_vix_fix_volume_signals|frama_baseline|adx_dmi_exit | 0.5837 | 5.575 | 9376 | 9.135 | 1.022 | 16 | 12.27 | 0.1131 | 1.749 | 8.448 | 1.366 | 1.656 | 0.35 | 20 | 3.319 | 0 |
| 2011-2014 | trend-routed | adx_dmi_signals|chandelier_exit_signals|variance_volume_signals|mcginley_dynamic_index|adx_dmi_exit | 1.049 | 4.747 | 97.1 | 8.072 | 7.794 | 60 | 1.875 | -0.05572 | 0.7842 | -4.423 | -0.4365 | 6.384 | 0.26 | 50 | -1.62 | 0 |
| 2011-2014 | trend-routed | adx_dmi_signals|coppock_curve_signals|williams_vix_fix_volume_signals|lsma_baseline|adx_dmi_exit | 0.5346 | 4.082 | 45.81 | 8.038 | 3.059 | 46 | 7.28 | 0.1571 | 1.842 | 10.09 | 2.28 | 2.344 | 0.3824 | 34 | 3.836 | 0 |
| 2011-2014 | trend-routed | adx_dmi_signals|coral_signals|williams_vix_fix_volume_signals|hma_baseline|adx_dmi_exit | 0.9156 | 14.78 | 63.31 | 23.14 | 1.029 | 26 | 11.83 | -0.1798 | 0.4838 | -14.84 | -0.6259 | 5.172 | 0.1667 | 18 | -4.771 | 0 |
| 2011-2014 | trend-routed | adx_dmi_signals|coral_signals|williams_vix_fix_volume_signals|super_smoother_2pole_baseline|adx_dmi_exit | 0.2752 | 2.877 | 1216 | 7.453 | 1.034 | 28 | 7.089 | 0.6473 |  |  | 0 | 0 | 1 | 4 | 20.18 | 0 |
| 2011-2014 | trend-routed | adx_dmi_signals|didi_index_signals|williams_vix_fix_volume_signals|lsma_baseline|adx_dmi_exit | 0.5346 | 4.082 | 45.81 | 8.038 | 3.059 | 46 | 7.28 | 0.1308 | 1.614 | 8.652 | 1.897 | 2.344 | 0.3824 | 34 | 3.107 | 0 |
| 2011-2014 | trend-routed | adx_dmi_signals|donchian_breakout_signals|williams_vix_fix_volume_signals|t3_baseline|adx_dmi_exit | 0.6961 | 5.068 | 65.92 | 12.72 | 1.313 | 24 | 8.084 | 0.1605 | 1.899 | 10.16 | 1.84 | 2.093 | 0.375 | 24 | 3.916 | 0 |


## 2. Chance level — the identity null on the year roles

Each draw calls a randomly chosen year of the step the "grade" year and another the "trade" year, and applies the identical bars. **A caveat that belongs in the reading**: those draws can land on TUNE years, on which the settings were fitted, so the null is not a neutral yardstick — it is biased toward clearing. A real count BELOW the null mean is therefore the striking direction, not the reassuring one.

| stream | step | real_clears_grade | null_mean_clears | null_p95_clears | p_grade | real_also_clears_trade | null_mean_also_trade | p_also_trade |
|---|---|---|---|---|---|---|---|---|
| chop-allon | 2011-2014 | 1,854 | 3718 | 7487 | 0.6 | 44 | 92.4 | 0.9 |
| chop-allon | 2012-2015 | 1,321 | 3932 | 9256 | 1 | 5 | 102.6 | 1 |
| chop-allon | 2013-2016 | 1,344 | 4589 | 9716 | 1 | 53 | 145.5 | 0.9 |
| chop-allon | 2014-2017 | 3,213 | 3752 | 5270 | 0.7 | 13 | 60.8 | 0.7 |
| chop-allon | 2015-2018 | 238 | 5388 | 1.017e+04 | 1 | 1 | 168.7 | 1 |
| chop-routed | 2011-2014 | 2,615 | 5751 | 1.068e+04 | 0.7 | 5 | 129.9 | 1 |
| chop-routed | 2012-2015 | 527 | 4376 | 9646 | 1 | 4 | 191.2 | 1 |
| chop-routed | 2013-2016 | 716 | 3004 | 7261 | 1 | 4 | 109.1 | 1 |
| chop-routed | 2014-2017 | 1,548 | 3261 | 6781 | 0.8 | 1 | 27.2 | 1 |
| chop-routed | 2015-2018 | 122 | 3658 | 7589 | 1 | 0 | 28.3 | 1 |
| trend-allon | 2011-2014 | 4,068 | 6109 | 6985 | 1 | 20 | 245.6 | 1 |
| trend-allon | 2012-2015 | 631 | 8038 | 2.285e+04 | 1 | 6 | 287.1 | 1 |
| trend-allon | 2013-2016 | 855 | 7199 | 1.702e+04 | 1 | 26 | 294.8 | 1 |
| trend-allon | 2014-2017 | 1,646 | 7644 | 2.368e+04 | 0.5 | 5 | 117.4 | 1 |
| trend-allon | 2015-2018 | 263 | 4052 | 1.639e+04 | 1 | 3 | 40.1 | 1 |
| trend-routed | 2011-2014 | 6,872 | 5352 | 6487 | 0.1 | 50 | 157.1 | 0.5 |
| trend-routed | 2012-2015 | 1,094 | 9043 | 3.194e+04 | 0.8 | 20 | 148.6 | 0.8 |
| trend-routed | 2013-2016 | 835 | 1.143e+04 | 3.187e+04 | 1 | 22 | 124.2 | 0.6 |
| trend-routed | 2014-2017 | 3,501 | 7904 | 3.255e+04 | 0.2 | 27 | 108.6 | 0.9 |
| trend-routed | 2015-2018 | 629 | 5157 | 2.166e+04 | 0.8 | 7 | 112 | 1 |


## 3. The stitched trade years 2016-2020, all unseen

| stream | n_field | n_clears_stitched | pct_of_field |
|---|---|---|---|
| trend-routed | 156,647 | 0 | 0 |
| trend-allon | 156,647 | 0 | 0 |
| chop-routed | 156,647 | 0 | 0 |
| chop-allon | 156,647 | 0 | 0 |


**Nobody passes on the stitched record.**


## 4. The passers' book

_The passers' book has not been built; this section is empty rather than filled in from anywhere else._
