# MODE A — GATE 3

Generated 2026-11-19 18:13 by `code/l2r2gate3.py`. **No new tuning**: every configuration here was already chosen by gate 2 and is re-scored, nothing is searched. Every number below is read back out of the CSV named beside it.


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
| counts | results/r2gate2/modeA_gate3_counts.csv | 20 | 0e9de5a7dc41 |
| passers | results/r2gate2/modeA_gate3_passers.csv | 59,268 | 85422926296a |
| null | results/r2gate2/modeA_gate3_null.csv | 20 | dd9d7d439433 |
| stitched | results/r2gate2/modeA_gate3_stitched.csv | 0 | 68b329da9893 |
| stitched_counts | results/r2gate2/modeA_gate3_stitched_counts.csv | 4 | 18313dcc9133 |


**Missing sources, left empty rather than filled in:** book, booknull


## 1. The bars on the GRADE year (year 5, unseen by the tuner)

| stream | step | n_field | n_clears_grade | n_also_clears_trade | pct_of_field |
|---|---|---|---|---|---|
| chop-allon | 2011-2014 | 273,780 | 3,164 | 58 | 1.156 |
| chop-allon | 2012-2015 | 273,780 | 2,008 | 7 | 0.7334 |
| chop-allon | 2013-2016 | 273,780 | 2,531 | 86 | 0.9245 |
| chop-allon | 2014-2017 | 273,780 | 5,311 | 19 | 1.94 |
| chop-allon | 2015-2018 | 273,780 | 445 | 2 | 0.1625 |
| chop-routed | 2011-2014 | 273,780 | 4,736 | 10 | 1.73 |
| chop-routed | 2012-2015 | 273,780 | 899 | 5 | 0.3284 |
| chop-routed | 2013-2016 | 273,780 | 1,200 | 5 | 0.4383 |
| chop-routed | 2014-2017 | 273,780 | 2,560 | 1 | 0.9351 |
| chop-routed | 2015-2018 | 273,780 | 231 | 0 | 0.08437 |
| trend-allon | 2011-2014 | 273,780 | 7,031 | 38 | 2.568 |
| trend-allon | 2012-2015 | 273,780 | 945 | 7 | 0.3452 |
| trend-allon | 2013-2016 | 273,780 | 1,634 | 50 | 0.5968 |
| trend-allon | 2014-2017 | 273,780 | 2,886 | 8 | 1.054 |
| trend-allon | 2015-2018 | 273,780 | 492 | 5 | 0.1797 |
| trend-routed | 2011-2014 | 273,780 | 12,450 | 76 | 4.547 |
| trend-routed | 2012-2015 | 273,780 | 1,618 | 21 | 0.591 |
| trend-routed | 2013-2016 | 273,780 | 1,396 | 29 | 0.5099 |
| trend-routed | 2014-2017 | 273,780 | 6,638 | 53 | 2.425 |
| trend-routed | 2015-2018 | 273,780 | 1,093 | 12 | 0.3992 |


Totals by stream:

| stream | n_clears_grade | n_also_clears_trade |
|---|---|---|
| chop-allon | 13,459 | 172 |
| chop-routed | 9,626 | 21 |
| trend-allon | 12,988 | 108 |
| trend-routed | 23,195 | 191 |


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
| chop-allon | 2011-2014 | 3,164 | 9066 | 1.639e+04 | 0.84 | 58 | 209.8 | 0.945 |
| chop-allon | 2012-2015 | 2,008 | 9120 | 1.879e+04 | 1 | 7 | 193.8 | 1 |
| chop-allon | 2013-2016 | 2,531 | 8343 | 1.769e+04 | 1 | 86 | 283.7 | 0.905 |
| chop-allon | 2014-2017 | 5,311 | 6905 | 1.238e+04 | 0.68 | 19 | 172.9 | 0.855 |
| chop-allon | 2015-2018 | 445 | 1.009e+04 | 1.998e+04 | 1 | 2 | 308.5 | 1 |
| chop-routed | 2011-2014 | 4,736 | 8945 | 1.886e+04 | 0.665 | 10 | 228.5 | 1 |
| chop-routed | 2012-2015 | 899 | 9139 | 1.911e+04 | 1 | 5 | 193 | 1 |
| chop-routed | 2013-2016 | 1,200 | 7765 | 2.064e+04 | 1 | 5 | 152.6 | 1 |
| chop-routed | 2014-2017 | 2,560 | 4370 | 1.209e+04 | 0.81 | 1 | 40.07 | 1 |
| chop-routed | 2015-2018 | 231 | 5775 | 1.357e+04 | 1 | 0 | 64.84 | 1 |
| trend-allon | 2011-2014 | 7,031 | 1.132e+04 | 2.353e+04 | 0.875 | 38 | 361 | 0.975 |
| trend-allon | 2012-2015 | 945 | 1.527e+04 | 3.993e+04 | 1 | 7 | 418.6 | 1 |
| trend-allon | 2013-2016 | 1,634 | 1.304e+04 | 3.838e+04 | 1 | 50 | 334.2 | 0.885 |
| trend-allon | 2014-2017 | 2,886 | 1.158e+04 | 4.202e+04 | 0.805 | 8 | 211.7 | 1 |
| trend-allon | 2015-2018 | 492 | 9534 | 4.422e+04 | 1 | 5 | 183.3 | 1 |
| trend-routed | 2011-2014 | 12,450 | 7966 | 1.245e+04 | 0.145 | 76 | 247.5 | 0.64 |
| trend-routed | 2012-2015 | 1,618 | 1.419e+04 | 5.874e+04 | 1 | 21 | 272.9 | 0.91 |
| trend-routed | 2013-2016 | 1,396 | 1.266e+04 | 5.884e+04 | 1 | 29 | 261 | 0.805 |
| trend-routed | 2014-2017 | 6,638 | 1.473e+04 | 5.972e+04 | 0.48 | 53 | 252 | 0.795 |
| trend-routed | 2015-2018 | 1,093 | 1.528e+04 | 5.898e+04 | 0.855 | 12 | 344.8 | 1 |


## 3. The stitched trade years 2016-2020, all unseen

| stream | n_field | n_clears_stitched | pct_of_field |
|---|---|---|---|
| trend-routed | 273,780 | 0 | 0 |
| trend-allon | 273,780 | 0 | 0 |
| chop-routed | 273,780 | 0 | 0 |
| chop-allon | 273,780 | 0 | 0 |


**Nobody passes on the stitched record.**


## 4. The passers' book

_The passers' book has not been built; this section is empty rather than filled in from anywhere else._
