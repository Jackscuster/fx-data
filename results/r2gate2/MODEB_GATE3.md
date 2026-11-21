# MODE B — GATE 3

Generated 2026-11-21 18:20 by `code/l2r2gate3.py`. **No new tuning**: every configuration here was already chosen by gate 2 and is re-scored, nothing is searched. Every number below is read back out of the CSV named beside it.


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
| counts | results/r2gate2/modeB_gate3_counts.csv | 20 | 6c92ca811cf3 |
| passers | results/r2gate2/modeB_gate3_passers.csv | 56,617 | e6619540b753 |
| null | results/r2gate2/modeB_gate3_null.csv | 20 | 17b716396b2e |
| stitched | results/r2gate2/modeB_gate3_stitched.csv | 0 | 68b329da9893 |
| stitched_counts | results/r2gate2/modeB_gate3_stitched_counts.csv | 4 | 138d3e93516b |


**Missing sources, left empty rather than filled in:** book, booknull


## 1. The bars on the GRADE year (year 5, unseen by the tuner)

| stream | step | n_field | n_clears_grade | n_also_clears_trade | pct_of_field |
|---|---|---|---|---|---|
| chop-allon | 2011-2014 | 273,780 | 2,920 | 59 | 1.067 |
| chop-allon | 2012-2015 | 273,780 | 2,351 | 10 | 0.8587 |
| chop-allon | 2013-2016 | 273,780 | 1,973 | 74 | 0.7207 |
| chop-allon | 2014-2017 | 273,780 | 5,191 | 18 | 1.896 |
| chop-allon | 2015-2018 | 273,780 | 327 | 0 | 0.1194 |
| chop-routed | 2011-2014 | 273,780 | 2,820 | 8 | 1.03 |
| chop-routed | 2012-2015 | 273,780 | 875 | 1 | 0.3196 |
| chop-routed | 2013-2016 | 273,780 | 1,173 | 13 | 0.4284 |
| chop-routed | 2014-2017 | 273,780 | 1,740 | 2 | 0.6355 |
| chop-routed | 2015-2018 | 273,780 | 328 | 1 | 0.1198 |
| trend-allon | 2011-2014 | 273,780 | 7,514 | 33 | 2.745 |
| trend-allon | 2012-2015 | 273,780 | 728 | 4 | 0.2659 |
| trend-allon | 2013-2016 | 273,780 | 1,430 | 54 | 0.5223 |
| trend-allon | 2014-2017 | 273,780 | 2,552 | 4 | 0.9321 |
| trend-allon | 2015-2018 | 273,780 | 408 | 1 | 0.149 |
| trend-routed | 2011-2014 | 273,780 | 14,635 | 220 | 5.346 |
| trend-routed | 2012-2015 | 273,780 | 1,665 | 13 | 0.6082 |
| trend-routed | 2013-2016 | 273,780 | 1,061 | 29 | 0.3875 |
| trend-routed | 2014-2017 | 273,780 | 6,320 | 14 | 2.308 |
| trend-routed | 2015-2018 | 273,780 | 606 | 4 | 0.2213 |


Totals by stream:

| stream | n_clears_grade | n_also_clears_trade |
|---|---|---|
| chop-allon | 12,762 | 161 |
| chop-routed | 6,936 | 25 |
| trend-allon | 12,632 | 96 |
| trend-routed | 24,287 | 280 |


Every passer is listed in `results/r2gate2/modeB_gate3_passers.csv` with its settings, its grade-year KPIs and its trade-year KPIs. The first 20:

| step | stream | sid | grade_expectancy_R | grade_profit_factor | grade_sortino | grade_calmar | grade_max_dd_R | grade_n | grade_sharpe | trade_expectancy_R | trade_profit_factor | trade_sortino | trade_calmar | trade_max_dd_R | trade_win_rate | trade_n | trade_sharpe | clears_trade_year |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2011-2014 | trend-routed | adx_dmi_signals|bears_bulls_impulse_signals|variance_volume_signals|ema_baseline|adx_dmi_exit | 0.4597 | 4.991 | 45.39 | 15.89 | 1.042 | 36 | 10.56 | 0.3652 | 3.79 | 31.07 | 4.951 | 2.655 | 0.5833 | 36 | 7.543 | 0 |
| 2011-2014 | trend-routed | adx_dmi_signals|bears_bulls_impulse_signals|variance_volume_signals|wma_baseline|adx_dmi_exit | 0.3722 | 3.322 | 97.18 | 12.37 | 1.023 | 34 | 8.356 | 0.3843 | 5.053 | 30.76 | 8.513 | 1.625 | 0.6111 | 36 | 8.32 | 1 |
| 2011-2014 | trend-routed | adx_dmi_signals|center_of_gravity_signals|williams_vix_fix_volume_signals|ema_baseline|adx_dmi_exit | 0.3942 | 3.782 | 27.45 | 9.158 | 1.033 | 24 | 8.681 | 0.03924 | 1.197 | 3.372 | 0.2946 | 2.664 | 0.3 | 20 | 1.087 | 0 |
| 2011-2014 | trend-routed | adx_dmi_signals|chandelier_exit_signals|variance_volume_signals|ema_baseline|adx_dmi_exit | 0.8624 | 4.027 | 86.41 | 7.966 | 8.012 | 74 | 1.712 | -0.04467 | 0.8057 | -3.675 | -0.4765 | 4.125 | 0.2727 | 44 | -1.424 | 0 |
| 2011-2014 | trend-routed | adx_dmi_signals|coral_signals|williams_vix_fix_volume_signals|ema_baseline|adx_dmi_exit | 0.3071 | 3.01 | 22.01 | 7.135 | 1.033 | 24 | 6.827 | 0.03185 | 1.172 | 2.807 | 0.3146 | 1.417 | 0.2143 | 14 | 0.8642 | 0 |
| 2011-2014 | trend-routed | adx_dmi_signals|fisher_transform_signals|williams_vix_fix_volume_signals|ema_baseline|adx_dmi_exit | 0.3537 | 3.508 | 25.35 | 8.901 | 1.033 | 26 | 7.951 | 0.03924 | 1.197 | 3.372 | 0.2946 | 2.664 | 0.3 | 20 | 1.087 | 0 |
| 2011-2014 | trend-routed | adx_dmi_signals|fisher_transform_signals|williams_vix_fix_volume_signals|wma_baseline|adx_dmi_exit | 0.4928 | 5.345 | 7916 | 8.676 | 1.022 | 18 | 12.16 | -0.1526 | 0.5471 | -16.99 | -0.7986 | 3.057 | 0.25 | 16 | -4.132 | 0 |
| 2011-2014 | trend-routed | adx_dmi_signals|fx_sniper_ergodic_cci_signals|chaikin_volatility_volume_signals|ema_baseline|adx_dmi_exit | 0.4796 | 3.174 | 42.56 | 10.4 | 7.283 | 158 | 1.373 | 0.02088 | 1.089 | 1.873 | 0.2079 | 14.66 | 0.3014 | 146 | 0.5156 | 0 |
| 2011-2014 | trend-routed | adx_dmi_signals|fx_sniper_ergodic_cci_signals|efficiency_ratio_volume_signals|rma_baseline|adx_dmi_exit | 0.9343 | 5.644 | 81.3 | 14.69 | 5.216 | 82 | 1.955 | -0.1592 | 0.4678 | -14.96 | -0.8496 | 15.74 | 0.1667 | 84 | -5.009 | 0 |
| 2011-2014 | trend-routed | adx_dmi_signals|fx_sniper_ergodic_cci_signals|williams_vix_fix_volume_signals|ema_baseline|adx_dmi_exit | 0.3829 | 3.477 | 26.66 | 8.154 | 1.033 | 22 | 8.102 | 0.03924 | 1.197 | 3.372 | 0.2946 | 2.664 | 0.3 | 20 | 1.087 | 0 |
| 2011-2014 | trend-routed | adx_dmi_signals|halftrend_signals|variance_volume_signals|ema_baseline|adx_dmi_exit | 1.312 | 9.433 | 121.2 | 28.24 | 2.973 | 64 | 2.255 | 0.1462 | 1.953 | 12.57 | 2.993 | 2.345 | 0.4167 | 48 | 3.859 | 0 |
| 2011-2014 | trend-routed | adx_dmi_signals|halftrend_signals|variance_volume_signals|mcginley_dynamic_index|adx_dmi_exit | 1.791 | 14.29 | 142.2 | 27.22 | 3.027 | 46 | 2.614 | 0.1355 | 1.714 | 9.872 | 2.311 | 2.345 | 0.4 | 40 | 3.243 | 0 |
| 2011-2014 | trend-routed | adx_dmi_signals|ichimoku_signals|chaikin_volatility_volume_signals|mcginley_dynamic_index|adx_dmi_exit | 3.293 | 10.9 | 558.8 | 11.73 | 5.616 | 20 | 3.401 | -0.2533 | 0.2493 | -24.73 | -1.04 | 7.309 | 0.1 | 30 | -9.937 | 0 |
| 2011-2014 | trend-routed | adx_dmi_signals|ichimoku_signals|choppiness_index_volume_signals|ema_baseline|adx_dmi_exit | 0.75 | 3.816 | 72.18 | 7.813 | 8.448 | 88 | 1.607 | 0.03007 | 1.128 | 2.763 | 0.2206 | 10.09 | 0.3378 | 74 | 0.7752 | 0 |
| 2011-2014 | trend-routed | adx_dmi_signals|ichimoku_signals|efficiency_ratio_volume_signals|t3_baseline|adx_dmi_exit | 1.739 | 8.644 | 177.7 | 10.73 | 6.157 | 38 | 2.477 | -0.1017 | 0.5852 | -8.758 | -1.096 | 3.71 | 0.25 | 40 | -3.625 | 0 |
| 2011-2014 | trend-routed | adx_dmi_signals|ichimoku_signals|variance_volume_signals|wma_baseline|adx_dmi_exit | 1.953 | 9.821 | 229.7 | 18.74 | 4.167 | 40 | 2.653 | 0.001752 | 1.008 | 0.1569 | 0.01801 | 2.918 | 0.3333 | 30 | 0.05163 | 0 |
| 2011-2014 | trend-routed | adx_dmi_signals|kuskus_starlight_signals|volatility_ratio_volume_signals|mcginley_dynamic_index|adx_dmi_exit | 0.6478 | 3.321 | 64.98 | 10.21 | 6.726 | 106 | 1.537 | 0.02177 | 1.094 | 1.806 | 0.3776 | 5.419 | 0.3404 | 94 | 0.5693 | 0 |
| 2011-2014 | trend-routed | adx_dmi_signals|laguerre_filter_signals|variance_volume_signals|ema_baseline|adx_dmi_exit | 1.627 | 10.37 | 148.7 | 28.4 | 2.865 | 50 | 2.473 | -0.06332 | 0.748 | -5.223 | -0.4602 | 5.229 | 0.2895 | 38 | -1.849 | 0 |
| 2011-2014 | trend-routed | adx_dmi_signals|laguerre_filter_signals|variance_volume_signals|mcginley_dynamic_index|adx_dmi_exit | 2.201 | 12.02 | 168.7 | 23.18 | 3.228 | 34 | 2.757 | -0.1376 | 0.5765 | -13.22 | -0.7567 | 6.182 | 0.2647 | 34 | -3.766 | 0 |
| 2011-2014 | trend-routed | adx_dmi_signals|lemantrend_signals|williams_vix_fix_volume_signals|hma_baseline|adx_dmi_exit | 0.2453 | 10.32 | 176.5 | 12.75 | 0.3079 | 16 | 10.23 | 0.007642 | 1.053 | 0.6497 | 0.09959 | 1.535 | 0.4 | 20 | 0.3018 | 0 |


## 2. Chance level — the identity null on the year roles

Each draw calls a randomly chosen year of the step the "grade" year and another the "trade" year, and applies the identical bars. **A caveat that belongs in the reading**: those draws can land on TUNE years, on which the settings were fitted, so the null is not a neutral yardstick — it is biased toward clearing. A real count BELOW the null mean is therefore the striking direction, not the reassuring one.

| stream | step | real_clears_grade | null_mean_clears | null_p95_clears | p_grade | real_also_clears_trade | null_mean_also_trade | p_also_trade |
|---|---|---|---|---|---|---|---|---|
| chop-allon | 2011-2014 | 2,920 | 9355 | 1.639e+04 | 0.84 | 59 | 233.8 | 0.86 |
| chop-allon | 2012-2015 | 2,351 | 8901 | 1.674e+04 | 0.86 | 10 | 171 | 1 |
| chop-allon | 2013-2016 | 1,973 | 8468 | 1.864e+04 | 1 | 74 | 279.5 | 0.905 |
| chop-allon | 2014-2017 | 5,191 | 6644 | 1.21e+04 | 0.68 | 18 | 150.8 | 0.725 |
| chop-allon | 2015-2018 | 327 | 9326 | 1.872e+04 | 1 | 0 | 263.4 | 1 |
| chop-routed | 2011-2014 | 2,820 | 7891 | 1.644e+04 | 0.81 | 8 | 168.5 | 1 |
| chop-routed | 2012-2015 | 875 | 8321 | 1.643e+04 | 1 | 1 | 146.2 | 1 |
| chop-routed | 2013-2016 | 1,173 | 6483 | 1.751e+04 | 1 | 13 | 96.19 | 0.94 |
| chop-routed | 2014-2017 | 1,740 | 3832 | 8290 | 0.81 | 2 | 37.02 | 1 |
| chop-routed | 2015-2018 | 328 | 4246 | 8542 | 1 | 1 | 32.37 | 1 |
| trend-allon | 2011-2014 | 7,514 | 9951 | 1.907e+04 | 0.875 | 33 | 265.4 | 0.895 |
| trend-allon | 2012-2015 | 728 | 1.431e+04 | 4.37e+04 | 1 | 4 | 346.9 | 1 |
| trend-allon | 2013-2016 | 1,430 | 1.239e+04 | 4.22e+04 | 1 | 54 | 269.8 | 0.785 |
| trend-allon | 2014-2017 | 2,552 | 1.057e+04 | 4.418e+04 | 0.805 | 4 | 152.6 | 0.85 |
| trend-allon | 2015-2018 | 408 | 9082 | 4.539e+04 | 1 | 1 | 147.5 | 1 |
| trend-routed | 2011-2014 | 14,635 | 9150 | 1.464e+04 | 0.145 | 220 | 364.3 | 0.64 |
| trend-routed | 2012-2015 | 1,665 | 1.527e+04 | 6.672e+04 | 0.83 | 13 | 384.1 | 1 |
| trend-routed | 2013-2016 | 1,061 | 1.308e+04 | 6.729e+04 | 1 | 29 | 342.8 | 0.87 |
| trend-routed | 2014-2017 | 6,320 | 1.461e+04 | 6.784e+04 | 0.48 | 14 | 242.2 | 0.925 |
| trend-routed | 2015-2018 | 606 | 1.635e+04 | 6.745e+04 | 1 | 4 | 313.6 | 1 |


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
