# MODE B — GATE 3

Generated 2026-11-21 18:39 by `code/l2r2gate3.py`. **No new tuning**: every configuration here was already chosen by gate 2 and is re-scored, nothing is searched. Every number below is read back out of the CSV named beside it.


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
| book | results/r2gate2/modeB_gate3_passersbook.csv | 20 | 292d1372ad09 |
| booknull | results/r2gate2/modeB_gate3_passersbook_nulls.csv | 60 | 00aad9f58c6a |


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

Everyone who cleared the bars on the step's GRADE year, equal weight, no picking -- membership is per (step, stream), so a strategy that cleared on `trend-routed` is in that step's ROUTED book through its trend routed settings and nothing else. Two books, as asked: ROUTED and ALWAYS-ON. Sized on the BUILD years, reported on the TRADE year. Members at the widest step: allon 9,628, chop_trend 17,286.

Per-step rows with every field are in `results/r2gate2/modeB_gate3_passersbook.csv`.


### TEAM 1

| KPI | ALWAYS-ON | ROUTED (chop RANGING + trend TRENDING) |
|---|---|---|
| median year | -1.43% | -2.11% |
| average year | -0.36% | -1.55% |
| worst year | -2.91% | -2.58% |
| best year | 3.15% | 0.17% |
| total 2016-2020 | -1.80% | -7.76% |
| CAGR | -0.36% | -1.55% |
| worst day | -0.98% | -0.60% |
| max drawdown | -5.84% | -8.63% |
| DIP95 (worst step) | 7.35% | 4.79% |
| Sharpe | -0.12 | -0.68 |
| Sortino | -0.17 | -0.95 |
| Calmar (total / max DD, the shipped bar) | -0.31 | -0.90 |
| Calmar (CAGR / max DD) | -0.06 | -0.18 |
| profit factor (trades, median step) | 0.92 | 0.85 |
| win rate (trades, median step) | 49.22% | 48.65% |
| positive years of 5 | 2 | 1 |
| retention (median step) | -0.21 | -0.49 |
| steps flagged FIT of 5 | 4 | 5 |

Per year:

- ALWAYS-ON: 2016: +1.19% | 2017: -1.43% | 2018: +3.15% | 2019: -1.79% | 2020: -2.91%
- ROUTED (chop RANGING + trend TRENDING): 2016: -2.11% | 2017: -2.16% | 2018: -1.08% | 2019: -2.58% | 2020: +0.17%

### TEAM 2

| KPI | ALWAYS-ON | ROUTED (chop RANGING + trend TRENDING) |
|---|---|---|
| median year | -2.15% | -3.16% |
| average year | -0.54% | -2.33% |
| worst year | -4.36% | -3.87% |
| best year | 4.72% | 0.26% |
| total 2016-2020 | -2.70% | -11.64% |
| CAGR | -0.54% | -2.33% |
| worst day | -1.47% | -0.90% |
| max drawdown | -8.75% | -12.95% |
| DIP95 (worst step) | 11.03% | 7.18% |
| Sharpe | -0.12 | -0.68 |
| Sortino | -0.17 | -0.95 |
| Calmar (total / max DD, the shipped bar) | -0.31 | -0.90 |
| Calmar (CAGR / max DD) | -0.06 | -0.18 |
| profit factor (trades, median step) | 0.92 | 0.85 |
| win rate (trades, median step) | 49.22% | 48.65% |
| positive years of 5 | 2 | 1 |
| retention (median step) | -0.21 | -0.49 |
| steps flagged FIT of 5 | 4 | 5 |

Per year:

- ALWAYS-ON: 2016: +1.79% | 2017: -2.15% | 2018: +4.72% | 2019: -2.69% | 2020: -4.36%
- ROUTED (chop RANGING + trend TRENDING): 2016: -3.16% | 2017: -3.24% | 2018: -1.62% | 2019: -3.87% | 2020: +0.26%

### Per step, as traded

| step | book | budget | members | size_scale | scale_binds | trade_total_pct | trade_max_dd_pct | trade_dip95_pct | trade_profit_factor | trade_sortino | trade_calmar | trade_win_rate_pct | retention | FIT |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2011-2014 | allon | team1 | 9,628 | 0.9053 | DIP95 | 1.192 | 1.691 | 3.88 | 1.08 | 0.5748 | 0.7045 | 48.65 | 0.1927 | 1 |
| 2011-2014 | allon | team2 | 9,628 | 1.358 | DIP95 | 1.787 | 2.537 | 5.821 | 1.08 | 0.5748 | 0.7045 | 48.65 | 0.1927 | 1 |
| 2011-2014 | chop_trend | team1 | 17,286 | 0.5572 | DIP95 | -2.11 | 3.003 | 3.69 | 0.8046 | -1.741 | -0.7024 | 47.88 | -0.8521 | 1 |
| 2011-2014 | chop_trend | team2 | 17,286 | 0.8358 | DIP95 | -3.164 | 4.505 | 5.535 | 0.8046 | -1.741 | -0.7024 | 47.88 | -0.8521 | 1 |
| 2012-2015 | allon | team1 | 2,876 | 0.6799 | DIP95 | -1.433 | 3.478 | 4.816 | 0.9153 | -0.8152 | -0.4121 | 49.22 | -0.2087 | 1 |
| 2012-2015 | allon | team2 | 2,876 | 1.02 | DIP95 | -2.15 | 5.217 | 7.224 | 0.9153 | -0.8152 | -0.4121 | 49.22 | -0.2087 | 1 |
| 2012-2015 | chop_trend | team1 | 2,528 | 0.7954 | DIP95 | -2.163 | 3.065 | 4.567 | 0.8485 | -1.404 | -0.7058 | 49.61 | -0.4901 | 1 |
| 2012-2015 | chop_trend | team2 | 2,528 | 1.193 | DIP95 | -3.245 | 4.598 | 6.85 | 0.8485 | -1.404 | -0.7058 | 49.61 | -0.4901 | 1 |
| 2013-2016 | allon | team1 | 3,071 | 0.7056 | DIP95 | 3.146 | 1.936 | 2.734 | 1.239 | 1.867 | 1.625 | 50.19 | 0.4102 | 0 |
| 2013-2016 | allon | team2 | 3,071 | 1.058 | DIP95 | 4.719 | 2.904 | 4.101 | 1.239 | 1.867 | 1.625 | 50.19 | 0.4102 | 0 |
| 2013-2016 | chop_trend | team1 | 2,228 | 0.567 | DIP95 | -1.08 | 2.728 | 3.813 | 0.9132 | -0.7006 | -0.3959 | 45.56 | -0.2104 | 1 |
| 2013-2016 | chop_trend | team2 | 2,228 | 0.8505 | DIP95 | -1.62 | 4.092 | 5.72 | 0.9132 | -0.7006 | -0.3959 | 45.56 | -0.2104 | 1 |
| 2014-2017 | allon | team1 | 6,918 | 0.6042 | DIP95 | -1.793 | 3.021 | 4.992 | 0.8867 | -0.9388 | -0.5934 | 46.72 | -0.4035 | 1 |
| 2014-2017 | allon | team2 | 6,918 | 0.9063 | DIP95 | -2.689 | 4.531 | 7.489 | 0.8867 | -0.9388 | -0.5934 | 46.72 | -0.4035 | 1 |
| 2014-2017 | chop_trend | team1 | 8,015 | 0.6541 | DIP95 | -2.578 | 2.953 | 4.621 | 0.8037 | -1.914 | -0.8729 | 48.65 | -6.183 | 1 |
| 2014-2017 | chop_trend | team2 | 8,015 | 0.9811 | DIP95 | -3.867 | 4.43 | 6.932 | 0.8037 | -1.914 | -0.8729 | 48.65 | -6.183 | 1 |
| 2015-2018 | allon | team1 | 707 | 1.012 | DIP95 | -2.91 | 4.362 | 7.351 | 0.8717 | -1.021 | -0.667 | 51.34 | -0.2208 | 1 |
| 2015-2018 | allon | team2 | 707 | 1.518 | DIP95 | -4.364 | 6.543 | 11.03 | 0.8717 | -1.021 | -0.667 | 51.34 | -0.2208 | 1 |
| 2015-2018 | chop_trend | team1 | 930 | 0.9049 | DIP95 | 0.1724 | 3.523 | 4.786 | 1.01 | 0.07812 | 0.04894 | 51.72 | 0.02151 | 1 |
| 2015-2018 | chop_trend | team2 | 930 | 1.357 | DIP95 | 0.2586 | 5.284 | 7.179 | 1.01 | 0.07812 | 0.04894 | 51.72 | 0.02151 | 1 |


### Its three nulls

| null | scope | step | book | budget | members | real | n_draws | null_mean | null_p5 | null_p95 | p_one_sided |
|---|---|---|---|---|---|---|---|---|---|---|---|
| identity | full field | 2011-2014 | allon | team1 |  | 1.192 | 200 | 5.729 | 1.192 | 14.07 | 0.84 |
| identity | full field | 2011-2014 | allon | team2 |  | 1.787 | 200 | 8.23 | 1.787 | 21.1 | 0.83 |
| identity | full field | 2011-2014 | chop_trend | team1 |  | -2.11 | 200 | 1.854 | -2.11 | 6.655 | 0.79 |
| identity | full field | 2011-2014 | chop_trend | team2 |  | -3.164 | 200 | 3.297 | -3.164 | 9.983 | 1 |
| identity | full field | 2012-2015 | allon | team1 |  | -1.433 | 200 | 6.695 | -1.433 | 17.97 | 1 |
| identity | full field | 2012-2015 | allon | team2 |  | -2.15 | 200 | 10.34 | -2.15 | 26.96 | 1 |
| identity | full field | 2012-2015 | chop_trend | team1 |  | -2.163 | 200 | 4.841 | -2.163 | 12.79 | 1 |
| identity | full field | 2012-2015 | chop_trend | team2 |  | -3.245 | 200 | 8.059 | -3.245 | 19.19 | 1 |
| identity | full field | 2013-2016 | allon | team1 |  | 3.146 | 200 | 6.649 | 2.088 | 14.56 | 0.65 |
| identity | full field | 2013-2016 | allon | team2 |  | 4.719 | 200 | 9.679 | 3.132 | 21.84 | 0.5 |
| identity | full field | 2013-2016 | chop_trend | team1 |  | -1.08 | 200 | 4.875 | -1.08 | 13.5 | 1 |
| identity | full field | 2013-2016 | chop_trend | team2 |  | -1.62 | 200 | 8.215 | -1.62 | 20.25 | 0.84 |
| identity | full field | 2014-2017 | allon | team1 |  | -1.793 | 200 | 4.766 | -1.793 | 14.9 | 1 |
| identity | full field | 2014-2017 | allon | team2 |  | -2.689 | 200 | 7.496 | -2.689 | 22.35 | 1 |
| identity | full field | 2014-2017 | chop_trend | team1 |  | -2.578 | 200 | 2.728 | -2.578 | 11.21 | 0.825 |
| identity | full field | 2014-2017 | chop_trend | team2 |  | -3.867 | 200 | 5.273 | -3.867 | 16.82 | 1 |
| identity | full field | 2015-2018 | allon | team1 |  | -2.91 | 200 | 9.84 | -2.91 | 20.6 | 1 |
| identity | full field | 2015-2018 | allon | team2 |  | -4.364 | 200 | 14.16 | -4.364 | 30.89 | 1 |
| identity | full field | 2015-2018 | chop_trend | team1 |  | 0.1724 | 200 | 7.579 | 0.1724 | 19.44 | 1 |
| identity | full field | 2015-2018 | chop_trend | team2 |  | 0.2586 | 200 | 11.47 | 0.2586 | 29.15 | 1 |
| shuffle | passers, full | 2011-2014 | allon | team1 | 9628 | 1.192 | 19 | 1.192 | 1.192 | 1.192 | 1 |
| shuffle | passers, full | 2011-2014 | allon | team2 | 9628 | 1.787 | 19 | 1.787 | 1.787 | 1.787 | 1 |
| shuffle | passers, full | 2011-2014 | chop_trend | team1 | 1.729e+04 | -2.11 | 19 | -0.4691 | -1.061 | 0.3447 | 1 |
| shuffle | passers, full | 2011-2014 | chop_trend | team2 | 1.729e+04 | -3.164 | 19 | -0.7036 | -1.591 | 0.5171 | 1 |
| shuffle | passers, full | 2012-2015 | allon | team1 | 2876 | -1.433 | 19 | -1.433 | -1.433 | -1.433 | 1 |
| shuffle | passers, full | 2012-2015 | allon | team2 | 2876 | -2.15 | 19 | -2.15 | -2.15 | -2.15 | 1 |
| shuffle | passers, full | 2012-2015 | chop_trend | team1 | 2528 | -2.163 | 19 | -1.175 | -1.946 | -0.2815 | 1 |
| shuffle | passers, full | 2012-2015 | chop_trend | team2 | 2528 | -3.245 | 19 | -1.763 | -2.918 | -0.4223 | 1 |
| shuffle | passers, full | 2013-2016 | allon | team1 | 3071 | 3.146 | 19 | 3.146 | 3.146 | 3.146 | 1 |
| shuffle | passers, full | 2013-2016 | allon | team2 | 3071 | 4.719 | 19 | 4.719 | 4.719 | 4.719 | 1 |
| shuffle | passers, full | 2013-2016 | chop_trend | team1 | 2228 | -1.08 | 19 | 0.06445 | -0.991 | 0.7646 | 0.9474 |
| shuffle | passers, full | 2013-2016 | chop_trend | team2 | 2228 | -1.62 | 19 | 0.09667 | -1.486 | 1.147 | 0.9474 |
| shuffle | passers, full | 2014-2017 | allon | team1 | 6918 | -1.793 | 19 | -1.793 | -1.793 | -1.793 | 1 |
| shuffle | passers, full | 2014-2017 | allon | team2 | 6918 | -2.689 | 19 | -2.689 | -2.689 | -2.689 | 1 |
| shuffle | passers, full | 2014-2017 | chop_trend | team1 | 8015 | -2.578 | 19 | -1.612 | -2.26 | -1.218 | 1 |
| shuffle | passers, full | 2014-2017 | chop_trend | team2 | 8015 | -3.867 | 19 | -2.417 | -3.391 | -1.827 | 1 |
| shuffle | passers, full | 2015-2018 | allon | team1 | 707 | -2.91 | 19 | -2.91 | -2.91 | -2.91 | 1 |
| shuffle | passers, full | 2015-2018 | allon | team2 | 707 | -4.364 | 19 | -4.364 | -4.364 | -4.364 | 1 |
| shuffle | passers, full | 2015-2018 | chop_trend | team1 | 930 | 0.1724 | 19 | -1.284 | -2.831 | -0.3053 | 0.05263 |
| shuffle | passers, full | 2015-2018 | chop_trend | team2 | 930 | 0.2586 | 19 | -1.927 | -4.247 | -0.4579 | 0.05263 |
| random-entry | passers, full | 2011-2014 | allon | team1 | 9628 | 1.192 | 19 | -0.5229 | -2.396 | 0.892 | 0.05263 |
| random-entry | passers, full | 2011-2014 | allon | team2 | 9628 | 1.787 | 19 | -0.7843 | -3.594 | 1.338 | 0.05263 |
| random-entry | passers, full | 2011-2014 | chop_trend | team1 | 1.729e+04 | -2.11 | 19 | -0.5279 | -2.993 | 1.71 | 0.7895 |
| random-entry | passers, full | 2011-2014 | chop_trend | team2 | 1.729e+04 | -3.164 | 19 | -0.7918 | -4.49 | 2.565 | 0.7895 |
| random-entry | passers, full | 2012-2015 | allon | team1 | 2876 | -1.433 | 19 | -0.8569 | -2.289 | 0.1778 | 0.6316 |
| random-entry | passers, full | 2012-2015 | allon | team2 | 2876 | -2.15 | 19 | -1.285 | -3.433 | 0.2667 | 0.6316 |
| random-entry | passers, full | 2012-2015 | chop_trend | team1 | 2528 | -2.163 | 19 | -0.2937 | -0.9314 | 0.2921 | 1 |
| random-entry | passers, full | 2012-2015 | chop_trend | team2 | 2528 | -3.245 | 19 | -0.4405 | -1.397 | 0.4382 | 1 |
| random-entry | passers, full | 2013-2016 | allon | team1 | 3071 | 3.146 | 19 | -0.6522 | -1.936 | 0.6749 | 0 |
| random-entry | passers, full | 2013-2016 | allon | team2 | 3071 | 4.719 | 19 | -0.9783 | -2.903 | 1.012 | 0 |
| random-entry | passers, full | 2013-2016 | chop_trend | team1 | 2228 | -1.08 | 19 | -0.2831 | -2.098 | 1.585 | 0.7895 |
| random-entry | passers, full | 2013-2016 | chop_trend | team2 | 2228 | -1.62 | 19 | -0.4246 | -3.147 | 2.378 | 0.7895 |
| random-entry | passers, full | 2014-2017 | allon | team1 | 6918 | -1.793 | 19 | -0.6427 | -2.68 | 0.5463 | 0.8421 |
| random-entry | passers, full | 2014-2017 | allon | team2 | 6918 | -2.689 | 19 | -0.964 | -4.02 | 0.8195 | 0.8421 |
| random-entry | passers, full | 2014-2017 | chop_trend | team1 | 8015 | -2.578 | 19 | -0.3952 | -1.897 | 0.9989 | 0.9474 |
| random-entry | passers, full | 2014-2017 | chop_trend | team2 | 8015 | -3.867 | 19 | -0.5928 | -2.846 | 1.498 | 0.9474 |
| random-entry | passers, full | 2015-2018 | allon | team1 | 707 | -2.91 | 19 | -0.7761 | -2.362 | 1.058 | 0.9474 |
| random-entry | passers, full | 2015-2018 | allon | team2 | 707 | -4.364 | 19 | -1.164 | -3.544 | 1.587 | 0.9474 |
| random-entry | passers, full | 2015-2018 | chop_trend | team1 | 930 | 0.1724 | 19 | -0.9898 | -4.604 | 0.4479 | 0.1053 |
| random-entry | passers, full | 2015-2018 | chop_trend | team2 | 930 | 0.2586 | 19 | -1.485 | -6.906 | 0.6718 | 0.1053 |


The real book clears its null's 95th percentile in **6 of 60** cells.
