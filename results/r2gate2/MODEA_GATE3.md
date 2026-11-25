# MODE A — GATE 3

Generated 2026-11-25 10:19 by `code/l2r2gate3.py`. **No new tuning**: every configuration here was already chosen by gate 2 and is re-scored, nothing is searched. Every number below is read back out of the CSV named beside it.


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
| book | results/r2gate2/modeA_gate3_passersbook.csv | 20 | ae2d82da85da |
| booknull | results/r2gate2/modeA_gate3_passersbook_nulls.csv | 60 | 6131572191d2 |


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

Everyone who cleared the bars on the step's GRADE year, equal weight, no picking -- membership is per (step, stream), so a strategy that cleared on `trend-routed` is in that step's ROUTED book through its trend routed settings and nothing else. Two books, as asked: ROUTED and ALWAYS-ON. Sized on the BUILD years, reported on the TRADE year. Members at the widest step: allon 9,303, chop_trend 16,963.

Per-step rows with every field are in `results/r2gate2/modeA_gate3_passersbook.csv`.


### TEAM 1

| KPI | ALWAYS-ON | ROUTED (chop RANGING + trend TRENDING) |
|---|---|---|
| median year | 0.15% | -1.09% |
| average year | 0.33% | -1.33% |
| worst year | -2.84% | -2.91% |
| best year | 3.73% | 0.32% |
| total 2016-2020 | 1.65% | -6.65% |
| CAGR | 0.33% | -1.33% |
| worst day | -1.11% | -0.57% |
| max drawdown | -6.00% | -7.80% |
| DIP95 (worst step) | 7.38% | 4.66% |
| Sharpe | 0.11 | -0.62 |
| Sortino | 0.16 | -0.91 |
| Calmar (total / max DD, the shipped bar) | 0.28 | -0.85 |
| Calmar (CAGR / max DD) | 0.06 | -0.17 |
| profit factor (trades, median step) | 1.01 | 0.89 |
| win rate (trades, median step) | 49.81% | 45.95% |
| positive years of 5 | 3 | 1 |
| retention (median step) | 0.02 | -0.31 |
| steps flagged FIT of 5 | 3 | 5 |

Per year:

- ALWAYS-ON: 2016: +3.10% | 2017: +0.15% | 2018: +3.73% | 2019: -2.84% | 2020: -2.49%
- ROUTED (chop RANGING + trend TRENDING): 2016: -1.09% | 2017: -2.17% | 2018: -0.80% | 2019: -2.91% | 2020: +0.32%

### TEAM 2

| KPI | ALWAYS-ON | ROUTED (chop RANGING + trend TRENDING) |
|---|---|---|
| median year | 0.23% | -1.64% |
| average year | 0.50% | -1.99% |
| worst year | -4.26% | -4.37% |
| best year | 5.60% | 0.49% |
| total 2016-2020 | 2.48% | -9.97% |
| CAGR | 0.50% | -1.99% |
| worst day | -1.66% | -0.86% |
| max drawdown | -9.00% | -11.70% |
| DIP95 (worst step) | 11.07% | 6.99% |
| Sharpe | 0.11 | -0.62 |
| Sortino | 0.16 | -0.91 |
| Calmar (total / max DD, the shipped bar) | 0.28 | -0.85 |
| Calmar (CAGR / max DD) | 0.06 | -0.17 |
| profit factor (trades, median step) | 1.01 | 0.89 |
| win rate (trades, median step) | 49.81% | 45.95% |
| positive years of 5 | 3 | 1 |
| retention (median step) | 0.02 | -0.31 |
| steps flagged FIT of 5 | 3 | 5 |

Per year:

- ALWAYS-ON: 2016: +4.65% | 2017: +0.23% | 2018: +5.60% | 2019: -4.26% | 2020: -3.74%
- ROUTED (chop RANGING + trend TRENDING): 2016: -1.64% | 2017: -3.25% | 2018: -1.19% | 2019: -4.37% | 2020: +0.49%

### Per step, as traded

| step | book | budget | members | size_scale | scale_binds | trade_total_pct | trade_max_dd_pct | trade_dip95_pct | trade_profit_factor | trade_sortino | trade_calmar | trade_win_rate_pct | retention | FIT |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2011-2014 | allon | team1 | 9,303 | 0.8122 | DIP95 | 3.099 | 1.382 | 2.747 | 1.255 | 2.033 | 2.243 | 49.81 | 0.6281 | 0 |
| 2011-2014 | allon | team2 | 9,303 | 1.218 | DIP95 | 4.649 | 2.072 | 4.121 | 1.255 | 2.033 | 2.243 | 49.81 | 0.6281 | 0 |
| 2011-2014 | chop_trend | team1 | 16,963 | 0.5742 | DIP95 | -1.092 | 2.289 | 3.018 | 0.8864 | -1.068 | -0.4769 | 45.17 | -0.3082 | 1 |
| 2011-2014 | chop_trend | team2 | 16,963 | 0.8614 | DIP95 | -1.638 | 3.434 | 4.527 | 0.8864 | -1.068 | -0.4769 | 45.17 | -0.3082 | 1 |
| 2012-2015 | allon | team1 | 2,661 | 0.7117 | DIP95 | 0.1503 | 3.19 | 4.087 | 1.009 | 0.08884 | 0.04712 | 50.78 | 0.0183 | 1 |
| 2012-2015 | allon | team2 | 2,661 | 1.068 | DIP95 | 0.2255 | 4.785 | 6.13 | 1.009 | 0.08884 | 0.04712 | 50.78 | 0.0183 | 1 |
| 2012-2015 | chop_trend | team1 | 2,505 | 0.8803 | DIP95 | -2.169 | 2.779 | 4.658 | 0.8529 | -1.372 | -0.7806 | 49.61 | -0.4745 | 1 |
| 2012-2015 | chop_trend | team2 | 2,505 | 1.32 | DIP95 | -3.253 | 4.168 | 6.988 | 0.8529 | -1.372 | -0.7806 | 49.61 | -0.4745 | 1 |
| 2013-2016 | allon | team1 | 3,826 | 0.6855 | DIP95 | 3.734 | 1.644 | 2.117 | 1.339 | 2.884 | 2.271 | 49.81 | 0.7574 | 0 |
| 2013-2016 | allon | team2 | 3,826 | 1.028 | DIP95 | 5.601 | 2.466 | 3.175 | 1.339 | 2.884 | 2.271 | 49.81 | 0.7574 | 0 |
| 2013-2016 | chop_trend | team1 | 2,590 | 0.6174 | DIP95 | -0.7956 | 2.726 | 3.433 | 0.9323 | -0.6544 | -0.2919 | 45.95 | -0.1289 | 1 |
| 2013-2016 | chop_trend | team2 | 2,590 | 0.9262 | DIP95 | -1.193 | 4.088 | 5.15 | 0.9323 | -0.6544 | -0.2919 | 45.95 | -0.1289 | 1 |
| 2014-2017 | allon | team1 | 7,233 | 0.672 | DIP95 | -2.838 | 3.493 | 5.664 | 0.8354 | -1.53 | -0.8126 | 44.4 | -0.6101 | 1 |
| 2014-2017 | allon | team2 | 7,233 | 1.008 | DIP95 | -4.258 | 5.24 | 8.495 | 0.8354 | -1.53 | -0.8126 | 44.4 | -0.6101 | 1 |
| 2014-2017 | chop_trend | team1 | 9,135 | 0.6572 | DIP95 | -2.914 | 3.399 | 4.564 | 0.767 | -2.498 | -0.8573 | 45.95 | -2.826 | 1 |
| 2014-2017 | chop_trend | team2 | 9,135 | 0.9859 | DIP95 | -4.371 | 5.099 | 6.845 | 0.767 | -2.498 | -0.8573 | 45.95 | -2.826 | 1 |
| 2015-2018 | allon | team1 | 877 | 1.104 | DIP95 | -2.494 | 4.299 | 7.377 | 0.892 | -0.8245 | -0.5801 | 51.72 | -0.1924 | 1 |
| 2015-2018 | allon | team2 | 877 | 1.657 | DIP95 | -3.741 | 6.448 | 11.07 | 0.892 | -0.8245 | -0.5801 | 51.72 | -0.1924 | 1 |
| 2015-2018 | chop_trend | team1 | 1,322 | 1.038 | DIP95 | 0.3245 | 2.935 | 4.309 | 1.019 | 0.1632 | 0.1106 | 49.81 | 0.05074 | 1 |
| 2015-2018 | chop_trend | team2 | 1,322 | 1.556 | DIP95 | 0.4867 | 4.402 | 6.464 | 1.019 | 0.1632 | 0.1106 | 49.81 | 0.05074 | 1 |


### Its three nulls

| null | scope | step | book | budget | members | real | n_draws | null_mean | null_p5 | null_p95 | p_one_sided |
|---|---|---|---|---|---|---|---|---|---|---|---|
| identity | full field | 2011-2014 | allon | team1 |  | 2.939 | 200 | 5.847 | 2.122 | 13.9 | 0.835 |
| identity | full field | 2011-2014 | allon | team2 |  | 4.409 | 200 | 8.552 | 3.182 | 20.85 | 0.83 |
| identity | full field | 2011-2014 | chop_trend | team1 |  | -1.034 | 200 | 2.532 | -1.034 | 8.264 | 0.805 |
| identity | full field | 2011-2014 | chop_trend | team2 |  | -1.552 | 200 | 3.927 | -1.552 | 12.4 | 1 |
| identity | full field | 2012-2015 | allon | team1 |  | 0.03109 | 200 | 7.426 | 0.03109 | 20.01 | 0.835 |
| identity | full field | 2012-2015 | allon | team2 |  | 0.04663 | 200 | 12.2 | 0.04663 | 30.01 | 1 |
| identity | full field | 2012-2015 | chop_trend | team1 |  | -2.38 | 200 | 4.395 | -2.38 | 13.63 | 1 |
| identity | full field | 2012-2015 | chop_trend | team2 |  | -3.57 | 200 | 7.656 | -3.57 | 20.45 | 1 |
| identity | full field | 2013-2016 | allon | team1 |  | 3.432 | 200 | 4.909 | 1.423 | 11.5 | 0.435 |
| identity | full field | 2013-2016 | allon | team2 |  | 5.148 | 200 | 8.007 | 2.134 | 17.25 | 0.675 |
| identity | full field | 2013-2016 | chop_trend | team1 |  | -1.055 | 200 | 3.866 | -1.055 | 10.91 | 1 |
| identity | full field | 2013-2016 | chop_trend | team2 |  | -1.582 | 200 | 5.882 | -1.582 | 16.36 | 1 |
| identity | full field | 2014-2017 | allon | team1 |  | -3.043 | 200 | 4.473 | -3.043 | 13.95 | 1 |
| identity | full field | 2014-2017 | allon | team2 |  | -4.565 | 200 | 6.29 | -4.565 | 20.93 | 1 |
| identity | full field | 2014-2017 | chop_trend | team1 |  | -2.902 | 200 | 2.014 | -2.902 | 9.365 | 1 |
| identity | full field | 2014-2017 | chop_trend | team2 |  | -4.353 | 200 | 3.574 | -4.353 | 14.05 | 1 |
| identity | full field | 2015-2018 | allon | team1 |  | -2.873 | 200 | 9.055 | -2.873 | 19.5 | 1 |
| identity | full field | 2015-2018 | allon | team2 |  | -4.31 | 200 | 14.25 | -4.31 | 29.24 | 1 |
| identity | full field | 2015-2018 | chop_trend | team1 |  | 0.02627 | 200 | 5.563 | 0.02627 | 14.14 | 1 |
| identity | full field | 2015-2018 | chop_trend | team2 |  | 0.03941 | 200 | 8.856 | 0.03941 | 21.21 | 0.795 |
| shuffle | passers, full | 2011-2014 | allon | team1 | 9303 | 3.099 | 19 | 3.099 | 3.099 | 3.099 | 1 |
| shuffle | passers, full | 2011-2014 | allon | team2 | 9303 | 4.649 | 19 | 4.649 | 4.649 | 4.649 | 1 |
| shuffle | passers, full | 2011-2014 | chop_trend | team1 | 1.696e+04 | -1.092 | 19 | -0.5542 | -1.424 | 0.4501 | 0.7895 |
| shuffle | passers, full | 2011-2014 | chop_trend | team2 | 1.696e+04 | -1.638 | 19 | -0.8313 | -2.136 | 0.6752 | 0.7895 |
| shuffle | passers, full | 2012-2015 | allon | team1 | 2661 | 0.1503 | 19 | 0.1503 | 0.1503 | 0.1503 | 1 |
| shuffle | passers, full | 2012-2015 | allon | team2 | 2661 | 0.2255 | 19 | 0.2255 | 0.2255 | 0.2255 | 1 |
| shuffle | passers, full | 2012-2015 | chop_trend | team1 | 2505 | -2.169 | 19 | -1.178 | -1.969 | -0.1146 | 0.9474 |
| shuffle | passers, full | 2012-2015 | chop_trend | team2 | 2505 | -3.253 | 19 | -1.767 | -2.953 | -0.1719 | 0.9474 |
| shuffle | passers, full | 2013-2016 | allon | team1 | 3826 | 3.734 | 19 | 3.734 | 3.734 | 3.734 | 1 |
| shuffle | passers, full | 2013-2016 | allon | team2 | 3826 | 5.601 | 19 | 5.601 | 5.601 | 5.601 | 1 |
| shuffle | passers, full | 2013-2016 | chop_trend | team1 | 2590 | -0.7956 | 19 | -0.04376 | -0.8641 | 0.7145 | 0.8947 |
| shuffle | passers, full | 2013-2016 | chop_trend | team2 | 2590 | -1.193 | 19 | -0.06564 | -1.296 | 1.072 | 0.8947 |
| shuffle | passers, full | 2014-2017 | allon | team1 | 7233 | -2.838 | 19 | -2.838 | -2.838 | -2.838 | 1 |
| shuffle | passers, full | 2014-2017 | allon | team2 | 7233 | -4.258 | 19 | -4.258 | -4.258 | -4.258 | 1 |
| shuffle | passers, full | 2014-2017 | chop_trend | team1 | 9135 | -2.914 | 19 | -1.512 | -1.967 | -0.663 | 1 |
| shuffle | passers, full | 2014-2017 | chop_trend | team2 | 9135 | -4.371 | 19 | -2.268 | -2.95 | -0.9944 | 1 |
| shuffle | passers, full | 2015-2018 | allon | team1 | 877 | -2.494 | 19 | -2.494 | -2.494 | -2.494 | 1 |
| shuffle | passers, full | 2015-2018 | allon | team2 | 877 | -3.741 | 19 | -3.741 | -3.741 | -3.741 | 1 |
| shuffle | passers, full | 2015-2018 | chop_trend | team1 | 1322 | 0.3245 | 19 | -0.2011 | -1.231 | 0.9162 | 0.2632 |
| shuffle | passers, full | 2015-2018 | chop_trend | team2 | 1322 | 0.4867 | 19 | -0.3016 | -1.847 | 1.374 | 0.2632 |
| random-entry | passers, full | 2011-2014 | allon | team1 | 9303 | 3.099 | 19 | -0.3896 | -2.969 | 1.835 | 0.05263 |
| random-entry | passers, full | 2011-2014 | allon | team2 | 9303 | 4.649 | 19 | -0.5844 | -4.453 | 2.753 | 0.05263 |
| random-entry | passers, full | 2011-2014 | chop_trend | team1 | 1.696e+04 | -1.092 | 19 | -0.5724 | -3.094 | 1.016 | 0.7368 |
| random-entry | passers, full | 2011-2014 | chop_trend | team2 | 1.696e+04 | -1.638 | 19 | -0.8586 | -4.641 | 1.523 | 0.7368 |
| random-entry | passers, full | 2012-2015 | allon | team1 | 2661 | 0.1503 | 19 | -0.6076 | -2.355 | 1.256 | 0.1579 |
| random-entry | passers, full | 2012-2015 | allon | team2 | 2661 | 0.2255 | 19 | -0.9114 | -3.532 | 1.885 | 0.1579 |
| random-entry | passers, full | 2012-2015 | chop_trend | team1 | 2505 | -2.169 | 19 | -0.3051 | -1.924 | 1.066 | 0.9474 |
| random-entry | passers, full | 2012-2015 | chop_trend | team2 | 2505 | -3.253 | 19 | -0.4576 | -2.887 | 1.599 | 0.9474 |
| random-entry | passers, full | 2013-2016 | allon | team1 | 3826 | 3.734 | 19 | -0.5851 | -2.99 | 0.4533 | 0 |
| random-entry | passers, full | 2013-2016 | allon | team2 | 3826 | 5.601 | 19 | -0.8777 | -4.484 | 0.6799 | 0 |
| random-entry | passers, full | 2013-2016 | chop_trend | team1 | 2590 | -0.7956 | 19 | -0.134 | -1.443 | 0.9239 | 0.7368 |
| random-entry | passers, full | 2013-2016 | chop_trend | team2 | 2590 | -1.193 | 19 | -0.201 | -2.164 | 1.386 | 0.7368 |
| random-entry | passers, full | 2014-2017 | allon | team1 | 7233 | -2.838 | 19 | -0.6666 | -2.667 | 0.5745 | 0.9474 |
| random-entry | passers, full | 2014-2017 | allon | team2 | 7233 | -4.258 | 19 | -0.9999 | -4 | 0.8618 | 0.9474 |
| random-entry | passers, full | 2014-2017 | chop_trend | team1 | 9135 | -2.914 | 19 | -0.3097 | -2.088 | 1.593 | 1 |
| random-entry | passers, full | 2014-2017 | chop_trend | team2 | 9135 | -4.371 | 19 | -0.4645 | -3.132 | 2.389 | 1 |
| random-entry | passers, full | 2015-2018 | allon | team1 | 877 | -2.494 | 19 | -0.371 | -2.13 | 1.256 | 1 |
| random-entry | passers, full | 2015-2018 | allon | team2 | 877 | -3.741 | 19 | -0.5565 | -3.195 | 1.884 | 1 |
| random-entry | passers, full | 2015-2018 | chop_trend | team1 | 1322 | 0.3245 | 19 | -0.9234 | -2.261 | 0.2495 | 0.05263 |
| random-entry | passers, full | 2015-2018 | chop_trend | team2 | 1322 | 0.4867 | 19 | -1.385 | -3.392 | 0.3743 | 0.05263 |


The real book clears its null's 95th percentile in **6 of 60** cells.
