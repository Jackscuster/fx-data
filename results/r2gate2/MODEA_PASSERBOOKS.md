# MODE A — THE PASSERS' BOOKS, THREE MEMBERSHIP RULES

Generated 2026-11-20 10:38 by `code/l2r2gate3.py`. **No new tuning anywhere**: every configuration was already chosen by gate 2, and a rule only decides which of them are members. Equal weight, no picking, no weighting by past record. Sized on the build years and not touched again; the traded year is what is reported.


## The rules, and how many pass

| rule | membership | trades | steps |
|---|---|---|---|
| `grade` | cleared the bars on the GRADE year (year 5) | year 6 | all five steps |
| `strict` | cleared the bars on the GRADE year (5) AND the TRADE year (6), both unseen by the tuner | year 7 | steps 1-4; step 5's year 7 is 2021 and 2021+ is sealed |
| `fiveyr` | cleared the bars on the FULL tune-plus-grade record, years 1-5 stitched into one block | year 6 | all five steps |

### Members per step

| rule | step | routed | always_on | any_stream | member_cells |
|---|---|---|---|---|---|
| grade | 2011-2014 | 16,963 | 9,303 | 24,296 | 27,381 |
| grade | 2012-2015 | 2,505 | 2,661 | 5,046 | 5,470 |
| grade | 2013-2016 | 2,590 | 3,826 | 6,281 | 6,761 |
| grade | 2014-2017 | 9,135 | 7,233 | 15,536 | 17,395 |
| grade | 2015-2018 | 1,322 | 877 | 2,161 | 2,261 |
| strict | 2011-2014 | 86 | 93 | 178 | 182 |
| strict | 2012-2015 | 26 | 14 | 40 | 40 |
| strict | 2013-2016 | 34 | 129 | 163 | 170 |
| strict | 2014-2017 | 54 | 26 | 80 | 81 |
| fiveyr | 2011-2014 | 107 | 14 | 121 | 121 |
| fiveyr | 2012-2015 | 162 | 19 | 181 | 181 |
| fiveyr | 2013-2016 | 109 | 15 | 124 | 124 |
| fiveyr | 2014-2017 | 298 | 10 | 308 | 308 |
| fiveyr | 2015-2018 | 471 | 6 | 477 | 477 |


Summed over the steps each rule trades (so `strict` sums four, the others five):

| rule | routed | always_on | any_stream | member_cells |
|---|---|---|---|---|
| fiveyr | 1,147 | 64 | 1,211 | 1,211 |
| grade | 32,515 | 23,900 | 53,320 | 59,268 |
| strict | 200 | 262 | 461 | 473 |


## Rule `grade`

Membership: cleared the bars on the GRADE year (year 5). Trades year 6, all five steps.


### Full KPI table


### TEAM 1

| KPI | ALWAYS-ON | ROUTED (chop RANGING + trend TRENDING) |
|---|---|---|
| median year | 0.03% | -1.05% |
| average year | 0.10% | -1.47% |
| worst year | -3.04% | -2.90% |
| best year | 3.43% | 0.03% |
| total 2016-2020 | 0.49% | -7.34% |
| CAGR | 0.10% | -1.47% |
| worst day | -1.09% | -0.56% |
| max drawdown | -6.54% | -8.15% |
| DIP95 (worst step) | 7.47% | 4.69% |
| Sharpe | 0.03 | -0.70 |
| Sortino | 0.05 | -1.02 |
| Calmar (total / max DD, the shipped bar) | 0.07 | -0.90 |
| Calmar (CAGR / max DD) | 0.01 | -0.18 |
| profit factor (trades, median step) | 1.00 | 0.89 |
| win rate (trades, median step) | 49.42% | 47.10% |
| positive years of 5 | 3 | 1 |
| retention (median step) | 0.00 | -0.32 |
| steps flagged FIT of 5 | 3 | 5 |

Per year:

- ALWAYS-ON: 2016: +2.94% | 2017: +0.03% | 2018: +3.43% | 2019: -3.04% | 2020: -2.87%
- ROUTED (chop RANGING + trend TRENDING): 2016: -1.03% | 2017: -2.38% | 2018: -1.05% | 2019: -2.90% | 2020: +0.03%

### TEAM 2

| KPI | ALWAYS-ON | ROUTED (chop RANGING + trend TRENDING) |
|---|---|---|
| median year | 0.05% | -1.58% |
| average year | 0.15% | -2.20% |
| worst year | -4.56% | -4.35% |
| best year | 5.15% | 0.04% |
| total 2016-2020 | 0.73% | -11.02% |
| CAGR | 0.15% | -2.20% |
| worst day | -1.64% | -0.85% |
| max drawdown | -9.80% | -12.23% |
| DIP95 (worst step) | 11.21% | 7.04% |
| Sharpe | 0.03 | -0.70 |
| Sortino | 0.05 | -1.02 |
| Calmar (total / max DD, the shipped bar) | 0.07 | -0.90 |
| Calmar (CAGR / max DD) | 0.01 | -0.18 |
| profit factor (trades, median step) | 1.00 | 0.89 |
| win rate (trades, median step) | 49.42% | 47.10% |
| positive years of 5 | 3 | 1 |
| retention (median step) | 0.00 | -0.32 |
| steps flagged FIT of 5 | 3 | 5 |

Per year:

- ALWAYS-ON: 2016: +4.41% | 2017: +0.05% | 2018: +5.15% | 2019: -4.56% | 2020: -4.31%
- ROUTED (chop RANGING + trend TRENDING): 2016: -1.55% | 2017: -3.57% | 2018: -1.58% | 2019: -4.35% | 2020: +0.04%

### Per step, as traded

| step | book | budget | members | size_scale | scale_binds | trade_total_pct | trade_max_dd_pct | trade_dip95_pct | trade_profit_factor | trade_sortino | trade_calmar | trade_win_rate_pct | retention | FIT |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2011-2014 | allon | team1 | 9,303 | 0.7901 | DIP95 | 2.939 | 1.373 | 2.717 | 1.247 | 1.971 | 2.141 | 49.42 | 0.6296 | 0 |
| 2011-2014 | allon | team2 | 9,303 | 1.185 | DIP95 | 4.409 | 2.06 | 4.075 | 1.247 | 1.971 | 2.141 | 49.42 | 0.6296 | 0 |
| 2011-2014 | chop_trend | team1 | 16,963 | 0.545 | DIP95 | -1.034 | 2.21 | 2.902 | 0.8876 | -1.041 | -0.4681 | 44.4 | -0.3158 | 1 |
| 2011-2014 | chop_trend | team2 | 16,963 | 0.8175 | DIP95 | -1.552 | 3.315 | 4.353 | 0.8876 | -1.041 | -0.4681 | 44.4 | -0.3158 | 1 |
| 2012-2015 | allon | team1 | 2,661 | 0.6743 | DIP95 | 0.03109 | 3.149 | 4.076 | 1.002 | 0.01849 | 0.009872 | 50 | 0.003956 | 1 |
| 2012-2015 | allon | team2 | 2,661 | 1.011 | DIP95 | 0.04663 | 4.724 | 6.114 | 1.002 | 0.01849 | 0.009872 | 50 | 0.003956 | 1 |
| 2012-2015 | chop_trend | team1 | 2,505 | 0.8489 | DIP95 | -2.38 | 2.958 | 4.691 | 0.834 | -1.53 | -0.8045 | 50 | -0.548 | 1 |
| 2012-2015 | chop_trend | team2 | 2,505 | 1.273 | DIP95 | -3.57 | 4.438 | 7.037 | 0.834 | -1.53 | -0.8045 | 50 | -0.548 | 1 |
| 2013-2016 | allon | team1 | 3,826 | 0.6648 | DIP95 | 3.432 | 1.67 | 2.108 | 1.317 | 2.711 | 2.055 | 49.42 | 0.7415 | 0 |
| 2013-2016 | allon | team2 | 3,826 | 0.9973 | DIP95 | 5.148 | 2.505 | 3.162 | 1.317 | 2.711 | 2.055 | 49.42 | 0.7415 | 0 |
| 2013-2016 | chop_trend | team1 | 2,590 | 0.5838 | DIP95 | -1.055 | 2.827 | 3.493 | 0.9087 | -0.8844 | -0.3732 | 45.17 | -0.1775 | 1 |
| 2013-2016 | chop_trend | team2 | 2,590 | 0.8757 | DIP95 | -1.582 | 4.24 | 5.239 | 0.9087 | -0.8844 | -0.3732 | 45.17 | -0.1775 | 1 |
| 2014-2017 | allon | team1 | 7,233 | 0.6465 | DIP95 | -3.043 | 3.637 | 5.682 | 0.8193 | -1.689 | -0.8368 | 44.4 | -0.7144 | 1 |
| 2014-2017 | allon | team2 | 7,233 | 0.9697 | DIP95 | -4.565 | 5.455 | 8.523 | 0.8193 | -1.689 | -0.8368 | 44.4 | -0.7144 | 1 |
| 2014-2017 | chop_trend | team1 | 9,135 | 0.6232 | DIP95 | -2.902 | 3.367 | 4.418 | 0.7547 | -2.498 | -0.8619 | 47.1 | -3.535 | 1 |
| 2014-2017 | chop_trend | team2 | 9,135 | 0.9348 | DIP95 | -4.353 | 5.051 | 6.627 | 0.7547 | -2.498 | -0.8619 | 47.1 | -3.535 | 1 |
| 2015-2018 | allon | team1 | 877 | 1.077 | DIP95 | -2.873 | 4.374 | 7.473 | 0.8741 | -0.9622 | -0.6569 | 51.34 | -0.2323 | 1 |
| 2015-2018 | allon | team2 | 877 | 1.616 | DIP95 | -4.31 | 6.561 | 11.21 | 0.8741 | -0.9622 | -0.6569 | 51.34 | -0.2323 | 1 |
| 2015-2018 | chop_trend | team1 | 1,322 | 1.01 | DIP95 | 0.02627 | 3.011 | 4.332 | 1.002 | 0.0135 | 0.008727 | 49.04 | 0.004368 | 1 |
| 2015-2018 | chop_trend | team2 | 1,322 | 1.514 | DIP95 | 0.03941 | 4.516 | 6.497 | 1.002 | 0.0135 | 0.008727 | 49.04 | 0.004368 | 1 |


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


### Every member, with its settings and per-year R

All 59,268 rows are in `results/r2gate2/modeA_gate3_members.csv`. The first 20:

| step | stream | sid | winner_index | risk_atr_len | risk_atr_mult | risk_be_pct | R_2011 | R_2012 | R_2013 | R_2014 | R_2015 | R_2016 | R_2017 | R_2018 | R_2019 | R_2020 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2011-2014 | trend-routed | adx_dmi_signals|adx_dmi_signals|williams_vix_fix_volume_signals|t3_baseline|adx_dmi_exit | 217 | 31 | 1 | 0.05 | 0.07833 | 0.2851 | -0.03326 | -0.1809 | 0.4865 | 0.01662 | -0.002377 | -0.07441 | -0.2129 | -0.1379 |
| 2011-2014 | trend-routed | adx_dmi_signals|aroon_signals|williams_vix_fix_volume_signals|t3_baseline|adx_dmi_exit | 217 | 31 | 1 | 0.05 | 0.005966 | 0.3336 | 0.1822 | -0.1694 | 0.806 | 0.1206 | -0.06577 | -0.01403 | 0.1943 | -0.1339 |
| 2011-2014 | trend-routed | adx_dmi_signals|bears_bulls_impulse_signals|chaikin_volatility_volume_signals|mcginley_dynamic_index|adx_dmi_exit | 220 | 31 | 1 | 0.05 | 0.2236 | 0.03535 | 0.07478 | -0.1172 | 0.2182 | 0.07542 | 0.06148 | -0.1367 | -0.1962 | -0.03764 |
| 2011-2014 | trend-routed | adx_dmi_signals|bears_bulls_impulse_signals|variance_volume_signals|ema_baseline|adx_dmi_exit | 235 | 31 | 1 | 0.05 | 0.2157 | 0.01371 | 0.09715 | -0.05011 | 0.2742 | 0.239 | 0.0124 | 0.05251 | 0.3736 | 0.2632 |
| 2011-2014 | trend-routed | adx_dmi_signals|bears_bulls_impulse_signals|variance_volume_signals|wma_baseline|adx_dmi_exit | 234 | 31 | 1 | 0.05 | 0.145 | -0.05429 | -0.004859 | -0.01513 | 0.2584 | 0.2548 | 0.02026 | -0.02186 | 0.2717 | 0.1086 |
| 2011-2014 | trend-routed | adx_dmi_signals|bears_bulls_impulse_signals|volatility_ratio_volume_signals|frama_baseline|adx_dmi_exit | 74 | 31 | 1.46 | 0.05 | 0.2212 | 0.1986 | -0.04348 | 0.274 | 0.4957 | 0.04266 | 0.05405 | -0.09552 | -0.003694 | 0.004101 |
| 2011-2014 | trend-routed | adx_dmi_signals|bears_bulls_impulse_signals|waddah_attar_explosion_volume_signals|ema_baseline|adx_dmi_exit | 257 | 31 | 1 | 0.05 | 0.1472 | 0.4084 | -0.1391 | -0.1599 | 0.295 | -0.09905 | -0.1575 | 0.06672 | -0.08619 | -0.03596 |
| 2011-2014 | trend-routed | adx_dmi_signals|bears_bulls_impulse_signals|waddah_attar_explosion_volume_signals|sma_baseline|adx_dmi_exit | 257 | 31 | 1 | 0.05 | 0.181 | 0.3432 | -0.1576 | -0.2528 | 0.3742 | -0.1292 | -0.1368 | 0.05668 | -0.08974 | 0.07259 |
| 2011-2014 | trend-routed | adx_dmi_signals|bears_bulls_impulse_signals|waddah_attar_explosion_volume_signals|tma_baseline|adx_dmi_exit | 257 | 31 | 1 | 0.05 | 0.2195 | 0.2952 | -0.05293 | -0.2487 | 0.4164 | -0.1157 | -0.001225 | 0.05576 | -0.07695 | -0.05624 |
| 2011-2014 | trend-routed | adx_dmi_signals|bears_bulls_impulse_signals|waddah_attar_explosion_volume_signals|wma_baseline|adx_dmi_exit | 257 | 31 | 1 | 0.05 | 0.1871 | 0.3004 | -0.02381 | -0.2737 | 0.3275 | -0.08518 | -0.1069 | 0.1351 | -0.06145 | 0.06119 |
| 2011-2014 | trend-routed | adx_dmi_signals|bears_bulls_impulse_signals|williams_vix_fix_volume_signals|alma_baseline|adx_dmi_exit | 274 | 31 | 1 | 0.05 | -0.1707 | 0.06404 | -0.191 | -0.2793 | 0.6517 | -0.07981 | -0.1745 | -0.1736 | -0.1121 | 0.1291 |
| 2011-2014 | trend-routed | adx_dmi_signals|bears_bulls_impulse_signals|williams_vix_fix_volume_signals|hma_baseline|adx_dmi_exit | 220 | 31 | 1 | 0.05 | -0.1606 | 0.08076 | -0.1581 | -0.294 | 0.6549 | -0.2923 | 0.05907 | 0.2588 | -0.1615 | -0.1943 |
| 2011-2014 | trend-routed | adx_dmi_signals|center_of_gravity_signals|williams_vix_fix_volume_signals|ema_baseline|adx_dmi_exit | 255 | 31 | 1 | 0.05 | 0.05152 | 0.1375 | -0.04055 | -0.006922 | 0.3789 | -0.05453 | -0.1828 | -0.04994 | -0.1801 | 0.2668 |
| 2011-2014 | trend-routed | adx_dmi_signals|center_of_gravity_signals|williams_vix_fix_volume_signals|frama_baseline|adx_dmi_exit | 249 | 31 | 1 | 0.05 | -0.04483 | 0.1792 | 0.2242 | 0.05196 | 0.5837 | 0.1131 | -0.1702 | -0.1858 | -0.01148 | 0.02018 |
| 2011-2014 | trend-routed | adx_dmi_signals|chandelier_exit_signals|variance_volume_signals|mcginley_dynamic_index|adx_dmi_exit | 235 | 31 | 1 | 0.05 | -0.03671 | 0.4138 | -0.04344 | 0.1118 | 1.049 | -0.05572 | -0.04763 | 0.1428 | 0.0953 | 6.743e-05 |
| 2011-2014 | trend-routed | adx_dmi_signals|coppock_curve_signals|williams_vix_fix_volume_signals|lsma_baseline|adx_dmi_exit | 218 | 31 | 1 | 0.05 | -0.2266 | 0.09713 | 0.2081 | -0.07097 | 0.5346 | 0.1571 | 0.01056 | 0.2586 | -0.3229 | -0.2376 |
| 2011-2014 | trend-routed | adx_dmi_signals|coral_signals|williams_vix_fix_volume_signals|hma_baseline|adx_dmi_exit | 220 | 31 | 1 | 0.05 | 0.04218 | 0.08502 | -0.3446 | -0.2068 | 0.9156 | -0.1798 | 0.01116 | 0.04972 | -0.1613 | -0.255 |
| 2011-2014 | trend-routed | adx_dmi_signals|coral_signals|williams_vix_fix_volume_signals|super_smoother_2pole_baseline|adx_dmi_exit | 229 | 31 | 1 | 0.05 | 0.1379 | 0.1582 | -0.353 | 0.167 | 0.2752 | 0.6473 | 0.0499 | 0.2433 | 0.08561 | -0.002894 |
| 2011-2014 | trend-routed | adx_dmi_signals|didi_index_signals|williams_vix_fix_volume_signals|lsma_baseline|adx_dmi_exit | 218 | 31 | 1 | 0.05 | -0.2457 | 0.09713 | 0.2547 | -0.135 | 0.5346 | 0.1308 | 0.01056 | 0.2586 | -0.3377 | -0.2376 |
| 2011-2014 | trend-routed | adx_dmi_signals|donchian_breakout_signals|williams_vix_fix_volume_signals|t3_baseline|adx_dmi_exit | 217 | 31 | 1 | 0.05 | 0.1798 | 0.39 | 0.1034 | -0.1921 | 0.6961 | 0.1605 | -0.1652 | 0.1209 | -0.09208 | -0.1339 |


## Rule `strict`

Membership: cleared the bars on the GRADE year (5) AND the TRADE year (6), both unseen by the tuner. Trades year 7, steps 1-4; step 5's year 7 is 2021 and 2021+ is sealed.


### Full KPI table


### TEAM 1

| KPI | ALWAYS-ON | ROUTED (chop RANGING + trend TRENDING) |
|---|---|---|
| median year | -0.01% | -0.74% |
| average year | 0.16% | -1.17% |
| worst year | -1.73% | -4.07% |
| best year | 2.38% | 0.86% |
| total 2016-2020 | 0.63% | -4.69% |
| CAGR | 0.16% | -1.17% |
| worst day | -0.70% | -0.86% |
| max drawdown | -3.14% | -7.02% |
| DIP95 (worst step) | 4.54% | 5.81% |
| Sharpe | 0.06 | -0.57 |
| Sortino | 0.10 | -0.79 |
| Calmar (total / max DD, the shipped bar) | 0.20 | -0.67 |
| Calmar (CAGR / max DD) | 0.05 | -0.17 |
| profit factor (trades, median step) | 1.00 | 0.94 |
| win rate (trades, median step) | 49.71% | 48.44% |
| positive years of 5 | 2 | 2 |
| retention (median step) | 0.01 | -0.13 |
| steps flagged FIT of 5 | 3 | 4 |

Per year:

- ALWAYS-ON: 2017: -0.23% | 2018: +2.38% | 2019: -1.73% | 2020: +0.22%
- ROUTED (chop RANGING + trend TRENDING): 2017: -1.96% | 2018: +0.86% | 2019: -4.07% | 2020: +0.48%

### TEAM 2

| KPI | ALWAYS-ON | ROUTED (chop RANGING + trend TRENDING) |
|---|---|---|
| median year | -0.01% | -1.11% |
| average year | 0.24% | -1.76% |
| worst year | -2.59% | -6.11% |
| best year | 3.56% | 1.29% |
| total 2016-2020 | 0.95% | -7.04% |
| CAGR | 0.24% | -1.76% |
| worst day | -1.05% | -1.29% |
| max drawdown | -4.71% | -10.54% |
| DIP95 (worst step) | 6.81% | 8.72% |
| Sharpe | 0.06 | -0.57 |
| Sortino | 0.10 | -0.79 |
| Calmar (total / max DD, the shipped bar) | 0.20 | -0.67 |
| Calmar (CAGR / max DD) | 0.05 | -0.17 |
| profit factor (trades, median step) | 1.00 | 0.94 |
| win rate (trades, median step) | 49.71% | 48.44% |
| positive years of 5 | 2 | 2 |
| retention (median step) | 0.01 | -0.13 |
| steps flagged FIT of 5 | 3 | 4 |

Per year:

- ALWAYS-ON: 2017: -0.35% | 2018: +3.56% | 2019: -2.59% | 2020: +0.33%
- ROUTED (chop RANGING + trend TRENDING): 2017: -2.94% | 2018: +1.29% | 2019: -6.11% | 2020: +0.72%

### Per step, as traded

| step | book | budget | size_years | trade_year | members | size_scale | scale_binds | trade_total_pct | trade_max_dd_pct | trade_dip95_pct | trade_profit_factor | trade_sortino | trade_calmar | trade_win_rate_pct | retention | FIT |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2011-2014 | allon | team1 | 2011-2016 | 2,017 | 93 | 0.5951 | DIP95 | -0.2349 | 2.861 | 4.037 | 0.984 | -0.1412 | -0.0821 | 50 | -0.0477 | 1 |
| 2011-2014 | allon | team2 | 2011-2016 | 2,017 | 93 | 0.8927 | DIP95 | -0.3523 | 4.291 | 6.056 | 0.984 | -0.1412 | -0.0821 | 50 | -0.0477 | 1 |
| 2011-2014 | chop_trend | team1 | 2011-2016 | 2,017 | 86 | 0.6924 | DIP95 | -1.963 | 3.029 | 4.071 | 0.8478 | -1.499 | -0.648 | 44.96 | -0.3911 | 1 |
| 2011-2014 | chop_trend | team2 | 2011-2016 | 2,017 | 86 | 1.039 | DIP95 | -2.945 | 4.544 | 6.107 | 0.8478 | -1.499 | -0.648 | 44.96 | -0.3911 | 1 |
| 2012-2015 | allon | team1 | 2012-2017 | 2,018 | 14 | 0.6628 | DIP95 | 2.376 | 2.709 | 3.166 | 1.16 | 1.479 | 0.8768 | 51.35 | 0.5702 | 0 |
| 2012-2015 | allon | team2 | 2012-2017 | 2,018 | 14 | 0.9943 | DIP95 | 3.564 | 4.064 | 4.749 | 1.16 | 1.479 | 0.8768 | 51.35 | 0.5702 | 0 |
| 2012-2015 | chop_trend | team1 | 2012-2017 | 2,018 | 26 | 0.6683 | DIP95 | 0.8612 | 1.353 | 2.413 | 1.085 | 0.6712 | 0.6366 | 52.12 | 0.1588 | 1 |
| 2012-2015 | chop_trend | team2 | 2012-2017 | 2,018 | 26 | 1.003 | DIP95 | 1.292 | 2.029 | 3.62 | 1.085 | 0.6712 | 0.6366 | 52.12 | 0.1588 | 1 |
| 2013-2016 | allon | team1 | 2013-2018 | 2,019 | 129 | 0.6744 | DIP95 | -1.726 | 2.796 | 4.543 | 0.8881 | -1.231 | -0.6172 | 44.4 | -0.4544 | 1 |
| 2013-2016 | allon | team2 | 2013-2018 | 2,019 | 129 | 1.012 | DIP95 | -2.588 | 4.194 | 6.814 | 0.8881 | -1.231 | -0.6172 | 44.4 | -0.4544 | 1 |
| 2013-2016 | chop_trend | team1 | 2013-2018 | 2,019 | 34 | 0.6551 | DIP95 | -4.074 | 4.362 | 5.812 | 0.7224 | -3.172 | -0.934 | 42.08 | -1.03 | 1 |
| 2013-2016 | chop_trend | team2 | 2013-2018 | 2,019 | 34 | 0.9826 | DIP95 | -6.111 | 6.543 | 8.719 | 0.7224 | -3.172 | -0.934 | 42.08 | -1.03 | 1 |
| 2014-2017 | allon | team1 | 2014-2019 | 2,020 | 26 | 0.6437 | DIP95 | 0.2177 | 2.241 | 3.997 | 1.015 | 0.1374 | 0.09716 | 49.43 | 0.06581 | 1 |
| 2014-2017 | allon | team2 | 2014-2019 | 2,020 | 26 | 0.9655 | DIP95 | 0.3266 | 3.361 | 5.996 | 1.015 | 0.1374 | 0.09716 | 49.43 | 0.06581 | 1 |
| 2014-2017 | chop_trend | team1 | 2014-2019 | 2,020 | 54 | 0.6421 | DIP95 | 0.4831 | 1.629 | 3.412 | 1.038 | 0.2446 | 0.2966 | 51.92 | 0.1368 | 1 |
| 2014-2017 | chop_trend | team2 | 2014-2019 | 2,020 | 54 | 0.9631 | DIP95 | 0.7247 | 2.443 | 5.118 | 1.038 | 0.2446 | 0.2966 | 51.92 | 0.1368 | 1 |


### Against a RANDOM pick of the same size

Sizes matched per (step, stream), drawn from the strategies that have a banked winner for that cell -- the same population the rule chose from.

| step | book | budget | real | random_mean | random_min | random_max | draws | real_beats_random_mean |
|---|---|---|---|---|---|---|---|---|
| 2011-2014 | allon | team1 | -0.2349 | -1.376 | -3.022 | -0.808 | 5 | 1 |
| 2011-2014 | allon | team2 | -0.3523 | -2.064 | -4.533 | -1.212 | 5 | 1 |
| 2011-2014 | chop_trend | team1 | -1.963 | 0.1948 | -1.076 | 1.676 | 5 | 0 |
| 2011-2014 | chop_trend | team2 | -2.945 | 0.2922 | -1.614 | 2.514 | 5 | 0 |
| 2012-2015 | allon | team1 | 2.376 | 0.7746 | -0.2972 | 1.674 | 5 | 1 |
| 2012-2015 | allon | team2 | 3.564 | 1.162 | -0.4458 | 2.511 | 5 | 1 |
| 2012-2015 | chop_trend | team1 | 0.8612 | 0.2363 | -0.2219 | 0.5387 | 5 | 1 |
| 2012-2015 | chop_trend | team2 | 1.292 | 0.3545 | -0.3328 | 0.808 | 5 | 1 |
| 2013-2016 | allon | team1 | -1.726 | -3.385 | -5.966 | -2.237 | 5 | 1 |
| 2013-2016 | allon | team2 | -2.588 | -5.078 | -8.95 | -3.356 | 5 | 1 |
| 2013-2016 | chop_trend | team1 | -4.074 | -1.138 | -1.544 | -0.4799 | 5 | 0 |
| 2013-2016 | chop_trend | team2 | -6.111 | -1.707 | -2.316 | -0.7198 | 5 | 0 |
| 2014-2017 | allon | team1 | 0.2177 | -2.005 | -4.204 | -0.421 | 5 | 1 |
| 2014-2017 | allon | team2 | 0.3266 | -3.008 | -6.306 | -0.6315 | 5 | 1 |
| 2014-2017 | chop_trend | team1 | 0.4831 | -0.9199 | -1.499 | -0.4672 | 5 | 1 |
| 2014-2017 | chop_trend | team2 | 0.7247 | -1.38 | -2.249 | -0.7007 | 5 | 1 |


The real book beats the random pick's mean in **12 of 16** (step, book, budget) cells.


### Its three nulls

| null | scope | step | book | budget | members | real | n_draws | null_mean | null_p5 | null_p95 | p_one_sided |
|---|---|---|---|---|---|---|---|---|---|---|---|
| identity | full field | 2011-2014 | allon | team1 |  | -0.2349 | 200 | 5.192 | -0.2349 | 11.27 | 0.86 |
| identity | full field | 2011-2014 | allon | team2 |  | -0.3523 | 200 | 7.582 | -0.3523 | 16.9 | 0.825 |
| identity | full field | 2011-2014 | chop_trend | team1 |  | -1.963 | 200 | 3.237 | -1.963 | 7.69 | 1 |
| identity | full field | 2011-2014 | chop_trend | team2 |  | -2.945 | 200 | 6.125 | -2.945 | 11.53 | 1 |
| identity | full field | 2012-2015 | allon | team1 |  | 2.376 | 200 | 4.749 | 0.192 | 9.787 | 0.875 |
| identity | full field | 2012-2015 | allon | team2 |  | 3.564 | 200 | 7.025 | 0.2879 | 14.68 | 0.845 |
| identity | full field | 2012-2015 | chop_trend | team1 |  | 0.8612 | 200 | 4.389 | 0.8612 | 7.164 | 1 |
| identity | full field | 2012-2015 | chop_trend | team2 |  | 1.292 | 200 | 6.448 | 1.292 | 10.75 | 0.85 |
| identity | full field | 2013-2016 | allon | team1 |  | -1.726 | 200 | 4.513 | -1.726 | 12.14 | 1 |
| identity | full field | 2013-2016 | allon | team2 |  | -2.588 | 200 | 6.805 | -2.588 | 18.21 | 1 |
| identity | full field | 2013-2016 | chop_trend | team1 |  | -4.074 | 200 | 3.111 | -4.074 | 9.74 | 1 |
| identity | full field | 2013-2016 | chop_trend | team2 |  | -6.111 | 200 | 4.995 | -6.111 | 14.61 | 1 |
| identity | full field | 2014-2017 | allon | team1 |  | 0.2177 | 200 | 4.278 | 0.2177 | 10.52 | 0.865 |
| identity | full field | 2014-2017 | allon | team2 |  | 0.3266 | 200 | 5.338 | 0.3266 | 15.78 | 1 |
| identity | full field | 2014-2017 | chop_trend | team1 |  | 0.4831 | 200 | 3.91 | -1.742 | 14.15 | 0.68 |
| identity | full field | 2014-2017 | chop_trend | team2 |  | 0.7247 | 200 | 6.235 | -2.613 | 21.2 | 0.72 |
| shuffle | passers, full | 2011-2014 | allon | team1 | 93 | 9.455 | 19 | 9.455 | 9.455 | 9.455 | 1 |
| shuffle | passers, full | 2011-2014 | allon | team2 | 93 | 14.18 | 19 | 14.18 | 14.18 | 14.18 | 1 |
| shuffle | passers, full | 2011-2014 | chop_trend | team1 | 86 | 4.234 | 19 | 1.767 | 0.8638 | 3.27 | 0 |
| shuffle | passers, full | 2011-2014 | chop_trend | team2 | 86 | 6.35 | 19 | 2.65 | 1.296 | 4.906 | 0 |
| shuffle | passers, full | 2012-2015 | allon | team1 | 14 | 8.181 | 19 | 8.181 | 8.181 | 8.181 | 1 |
| shuffle | passers, full | 2012-2015 | allon | team2 | 14 | 12.27 | 19 | 12.27 | 12.27 | 12.27 | 1 |
| shuffle | passers, full | 2012-2015 | chop_trend | team1 | 26 | 6.51 | 19 | 0.8048 | -0.1656 | 1.941 | 0 |
| shuffle | passers, full | 2012-2015 | chop_trend | team2 | 26 | 9.766 | 19 | 1.207 | -0.2484 | 2.912 | 0 |
| shuffle | passers, full | 2013-2016 | allon | team1 | 129 | 10.26 | 19 | 10.26 | 10.26 | 10.26 | 1 |
| shuffle | passers, full | 2013-2016 | allon | team2 | 129 | 15.38 | 19 | 15.38 | 15.38 | 15.38 | 1 |
| shuffle | passers, full | 2013-2016 | chop_trend | team1 | 34 | 8.309 | 19 | 3.224 | 1.686 | 4.614 | 0 |
| shuffle | passers, full | 2013-2016 | chop_trend | team2 | 34 | 12.46 | 19 | 4.836 | 2.53 | 6.921 | 0 |
| shuffle | passers, full | 2014-2017 | allon | team1 | 26 | 9.457 | 19 | 9.457 | 9.457 | 9.457 | 1 |
| shuffle | passers, full | 2014-2017 | allon | team2 | 26 | 14.19 | 19 | 14.19 | 14.19 | 14.19 | 1 |
| shuffle | passers, full | 2014-2017 | chop_trend | team1 | 54 | 5.47 | 19 | 0.4995 | -0.4326 | 1.703 | 0 |
| shuffle | passers, full | 2014-2017 | chop_trend | team2 | 54 | 8.204 | 19 | 0.7492 | -0.649 | 2.554 | 0 |
| random-entry | passers, full | 2011-2014 | allon | team1 | 93 | 9.455 | 19 | -0.09676 | -1.187 | 1.065 | 0 |
| random-entry | passers, full | 2011-2014 | allon | team2 | 93 | 14.18 | 19 | -0.1451 | -1.781 | 1.598 | 0 |
| random-entry | passers, full | 2011-2014 | chop_trend | team1 | 86 | 4.234 | 19 | -0.5451 | -2.188 | 1.54 | 0 |
| random-entry | passers, full | 2011-2014 | chop_trend | team2 | 86 | 6.35 | 19 | -0.8176 | -3.282 | 2.31 | 0 |
| random-entry | passers, full | 2012-2015 | allon | team1 | 14 | 8.181 | 19 | 0.05454 | -0.7792 | 0.8848 | 0 |
| random-entry | passers, full | 2012-2015 | allon | team2 | 14 | 12.27 | 19 | 0.08181 | -1.169 | 1.327 | 0 |
| random-entry | passers, full | 2012-2015 | chop_trend | team1 | 26 | 6.51 | 19 | 0.1341 | -0.6618 | 1.19 | 0 |
| random-entry | passers, full | 2012-2015 | chop_trend | team2 | 26 | 9.766 | 19 | 0.2011 | -0.9927 | 1.785 | 0 |
| random-entry | passers, full | 2013-2016 | allon | team1 | 129 | 10.26 | 19 | -0.09723 | -1.934 | 1.55 | 0 |
| random-entry | passers, full | 2013-2016 | allon | team2 | 129 | 15.38 | 19 | -0.1458 | -2.902 | 2.325 | 0 |
| random-entry | passers, full | 2013-2016 | chop_trend | team1 | 34 | 8.309 | 19 | -0.2461 | -1.248 | 0.3894 | 0 |
| random-entry | passers, full | 2013-2016 | chop_trend | team2 | 34 | 12.46 | 19 | -0.3692 | -1.872 | 0.5842 | 0 |
| random-entry | passers, full | 2014-2017 | allon | team1 | 26 | 9.457 | 19 | -0.2598 | -0.9718 | 0.1841 | 0 |
| random-entry | passers, full | 2014-2017 | allon | team2 | 26 | 14.19 | 19 | -0.3897 | -1.458 | 0.2762 | 0 |
| random-entry | passers, full | 2014-2017 | chop_trend | team1 | 54 | 5.47 | 19 | -0.06464 | -1.104 | 0.7258 | 0 |
| random-entry | passers, full | 2014-2017 | chop_trend | team2 | 54 | 8.204 | 19 | -0.09696 | -1.656 | 1.089 | 0 |


The real book clears its null's 95th percentile in **24 of 48** cells.


### Every member, with its settings and per-year R

All 473 rows are in `results/r2gate2/modeA_gate3_members_strict.csv`. The first 20:

| step | stream | sid | winner_index | risk_atr_len | risk_atr_mult | risk_be_pct | R_2011 | R_2012 | R_2013 | R_2014 | R_2015 | R_2016 | R_2017 | R_2018 | R_2019 | R_2020 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2011-2014 | trend-routed | aroon_signals|bears_bulls_impulse_signals|variance_volume_signals|kama_baseline|adx_dmi_exit | 249 | 31 | 1 | 0.05 | 0.2052 | 0.1696 | -0.02992 | 0.07972 | 0.9725 | 0.2165 | 0.02388 | -0.01346 | -0.06172 | -0.02921 |
| 2011-2014 | trend-routed | bears_bulls_impulse_signals|bears_bulls_impulse_signals|choppiness_index_volume_signals|frama_baseline|adx_dmi_exit | 233 | 31 | 1 | 0.05 | -0.001428 | 0.196 | 0.005553 | 0.01615 | 0.4536 | 0.2847 | -0.02271 | 0.1016 | -0.3156 | -0.06527 |
| 2011-2014 | trend-routed | bears_bulls_impulse_signals|bears_bulls_impulse_signals|choppiness_index_volume_signals|t3_baseline|adx_dmi_exit | 245 | 31 | 1 | 0.05 | 0.002484 | 0.1745 | 0.1479 | 0.009186 | 0.4436 | 0.4314 | -0.0847 | 0.2005 | -0.2906 | -0.2008 |
| 2011-2014 | trend-routed | bears_bulls_impulse_signals|dspo_signals|fractal_dimension_volume_signals|frama_baseline|adx_dmi_exit | 191 | 31 | 1 | 0.05 | 0.3438 | 0.2317 | -0.06104 | -0.05151 | 1.176 | 0.2373 | -0.02012 | -0.05473 | 0.1212 | -0.0895 |
| 2011-2014 | trend-routed | bears_bulls_impulse_signals|dspo_signals|fractal_dimension_volume_signals|kama_baseline|adx_dmi_exit | 191 | 31 | 1 | 0.05 | 0.2599 | 0.5655 | -0.06887 | -0.3033 | 3.498 | 0.3174 | -0.09413 | -0.07086 | 0.1367 | -0.1239 |
| 2011-2014 | trend-routed | bears_bulls_impulse_signals|ehlers_reverse_ema_signals|fractal_dimension_volume_signals|frama_baseline|adx_dmi_exit | 191 | 31 | 1 | 0.05 | 0.3053 | 0.1891 | -0.02586 | 0.05188 | 0.9909 | 0.2138 | -0.04391 | -0.066 | -0.01828 | 0.09365 |
| 2011-2014 | trend-routed | bears_bulls_impulse_signals|fisher_transform_signals|choppiness_index_volume_signals|frama_baseline|adx_dmi_exit | 222 | 31 | 1 | 0.05 | -0.06304 | 0.1278 | -0.09072 | 0.0118 | 0.2076 | 0.2349 | -0.07831 | 0.04682 | -0.2407 | 0.1056 |
| 2011-2014 | trend-routed | bears_bulls_impulse_signals|fisher_transform_signals|variance_volume_signals|frama_baseline|adx_dmi_exit | 238 | 31 | 1 | 0.05 | 0.1649 | 0.01683 | -0.01269 | 0.09384 | 0.6072 | 0.2047 | 0.0116 | 0.1099 | -0.04285 | -0.01308 |
| 2011-2014 | trend-routed | bears_bulls_impulse_signals|kase_peak_oscillator_signals|fractal_dimension_volume_signals|frama_baseline|adx_dmi_exit | 191 | 31 | 1 | 0.05 | 0.3419 | 0.1611 | -0.04403 | 0.03713 | 1.057 | 0.2083 | -0.03817 | -0.07677 | -0.01801 | 0.06715 |
| 2011-2014 | trend-routed | bears_bulls_impulse_signals|kuskus_starlight_signals|choppiness_index_volume_signals|tma_baseline|adx_dmi_exit | 204 | 31 | 1 | 0.05 | 0.2142 | -0.09589 | 0.09353 | 0.1737 | 1.999 | 0.3339 | 0.3164 | -0.4481 | 0.006224 | -0.1225 |
| 2011-2014 | trend-routed | bears_bulls_impulse_signals|mama_fama_signals|fractal_dimension_volume_signals|frama_baseline|adx_dmi_exit | 191 | 31 | 1 | 0.05 | 0.302 | 0.186 | -0.05368 | 0.01903 | 1.081 | 0.2167 | 0.01443 | -0.07643 | 0.03697 | 0.07373 |
| 2011-2014 | trend-routed | bears_bulls_impulse_signals|mama_fama_signals|variance_volume_signals|frama_baseline|adx_dmi_exit | 238 | 31 | 1 | 0.05 | 0.2731 | 0.09233 | -0.05736 | 0.07535 | 0.4489 | 0.1563 | 0.04297 | -0.03807 | 0.01925 | -0.08315 |
| 2011-2014 | trend-routed | bears_bulls_impulse_signals|parabolic_sar_signals|choppiness_index_volume_signals|frama_baseline|adx_dmi_exit | 222 | 31 | 1 | 0.05 | -0.0591 | 0.1401 | -0.05024 | 0.02483 | 0.3134 | 0.2472 | -0.06016 | 0.09697 | -0.277 | 0.1525 |
| 2011-2014 | trend-routed | bears_bulls_impulse_signals|parabolic_sar_signals|ttm_squeeze_volume_signals|frama_baseline|adx_dmi_exit | 240 | 31 | 1 | 0.05 | -0.08147 | 0.1226 | -0.06916 | -0.04562 | 0.259 | 0.2578 | -0.04961 | 0.1247 | -0.2482 | 0.1891 |
| 2011-2014 | trend-routed | bears_bulls_impulse_signals|parabolic_sar_signals|variance_volume_signals|fantail_vma|adx_dmi_exit | 237 | 31 | 1 | 0.05 | 0.2 | 0.366 | -0.1032 | 0.02909 | 0.7038 | 0.1998 | -0.1287 | 0.0886 | -0.2228 | -0.05137 |
| 2011-2014 | trend-routed | bears_bulls_impulse_signals|price_momentum_oscillator_signals|efficiency_ratio_volume_signals|ema_baseline|adx_dmi_exit | 237 | 31 | 1 | 0.05 | 0.2167 | 0.3229 | 0.04199 | -0.1737 | 1.466 | 0.27 | -0.2806 | -0.08903 | 0.08264 | -0.07115 |
| 2011-2014 | trend-routed | bears_bulls_impulse_signals|price_momentum_oscillator_signals|fractal_dimension_volume_signals|kama_baseline|adx_dmi_exit | 191 | 31 | 1 | 0.05 | 0.2199 | 0.4459 | -0.05148 | -0.2304 | 2.903 | 0.3155 | -0.03454 | -0.07086 | 0.1338 | -0.1908 |
| 2011-2014 | trend-routed | bears_bulls_impulse_signals|schaff_trend_cycle_signals|ttm_squeeze_volume_signals|kama_baseline|adx_dmi_exit | 257 | 31 | 1 | 0.05 | 0.1285 | 0.1455 | -0.04416 | 0.03005 | 0.2358 | 0.3175 | -0.1015 | 0.119 | -0.3671 | 0.008179 |
| 2011-2014 | trend-routed | bears_bulls_impulse_signals|waddah_attar_explosion_signals|efficiency_ratio_volume_signals|ema_baseline|adx_dmi_exit | 236 | 31 | 1 | 0.05 | 0.3622 | 0.2294 | 0.0175 | -0.09387 | 1.76 | 0.2934 | -0.2671 | -0.1881 | 0.08264 | -0.06973 |
| 2011-2014 | trend-routed | center_of_gravity_signals|vortex_signals|williams_vix_fix_volume_signals|frama_baseline|adx_dmi_exit | 228 | 31 | 1 | 0.05 | 0.1477 | 0.09586 | -0.0782 | -0.02881 | 0.3098 | 0.2128 | -0.09579 | 0.2244 | -0.008555 | 0.2189 |


## Rule `fiveyr`

Membership: cleared the bars on the FULL tune-plus-grade record, years 1-5 stitched into one block. Trades year 6, all five steps.


### Full KPI table


### TEAM 1

| KPI | ALWAYS-ON | ROUTED (chop RANGING + trend TRENDING) |
|---|---|---|
| median year | 0.10% | -0.44% |
| average year | -0.01% | -0.06% |
| worst year | -3.13% | -1.65% |
| best year | 1.93% | 2.18% |
| total 2016-2020 | -0.07% | -0.31% |
| CAGR | -0.01% | -0.06% |
| worst day | -0.83% | -0.42% |
| max drawdown | -5.71% | -5.36% |
| DIP95 (worst step) | 5.83% | 3.01% |
| Sharpe | -0.01 | -0.04 |
| Sortino | -0.01 | -0.05 |
| Calmar (total / max DD, the shipped bar) | -0.01 | -0.06 |
| Calmar (CAGR / max DD) | -0.00 | -0.01 |
| profit factor (trades, median step) | 1.01 | 0.92 |
| win rate (trades, median step) | 52.12% | 46.33% |
| positive years of 5 | 3 | 2 |
| retention (median step) | 0.01 | -0.12 |
| steps flagged FIT of 5 | 3 | 4 |

Per year:

- ALWAYS-ON: 2016: +1.50% | 2017: -3.13% | 2018: +1.93% | 2019: +0.10% | 2020: -0.47%
- ROUTED (chop RANGING + trend TRENDING): 2016: +0.66% | 2017: -1.06% | 2018: -1.65% | 2019: -0.44% | 2020: +2.18%

### TEAM 2

| KPI | ALWAYS-ON | ROUTED (chop RANGING + trend TRENDING) |
|---|---|---|
| median year | 0.12% | -0.65% |
| average year | -0.06% | -0.15% |
| worst year | -4.69% | -2.48% |
| best year | 2.74% | 3.27% |
| total 2016-2020 | -0.29% | -0.76% |
| CAGR | -0.06% | -0.15% |
| worst day | -1.25% | -0.63% |
| max drawdown | -8.72% | -7.90% |
| DIP95 (worst step) | 8.74% | 4.52% |
| Sharpe | -0.01 | -0.06 |
| Sortino | -0.02 | -0.09 |
| Calmar (total / max DD, the shipped bar) | -0.03 | -0.10 |
| Calmar (CAGR / max DD) | -0.01 | -0.02 |
| profit factor (trades, median step) | 1.00 | 0.92 |
| win rate (trades, median step) | 52.12% | 46.33% |
| positive years of 5 | 3 | 2 |
| retention (median step) | 0.01 | -0.12 |
| steps flagged FIT of 5 | 3 | 4 |

Per year:

- ALWAYS-ON: 2016: +2.25% | 2017: -4.69% | 2018: +2.74% | 2019: +0.12% | 2020: -0.71%
- ROUTED (chop RANGING + trend TRENDING): 2016: +0.70% | 2017: -1.60% | 2018: -2.48% | 2019: -0.65% | 2020: +3.27%

### Per step, as traded

| step | book | budget | size_years | trade_year | members | size_scale | scale_binds | trade_total_pct | trade_max_dd_pct | trade_dip95_pct | trade_profit_factor | trade_sortino | trade_calmar | trade_win_rate_pct | retention | FIT |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2011-2014 | allon | team1 | 2011-2015 | 2,016 | 14 | 1.008 | DIP95 | 1.497 | 1.654 | 3.275 | 1.113 | 0.8694 | 0.9052 | 47.1 | 0.2988 | 0 |
| 2011-2014 | allon | team2 | 2011-2015 | 2,016 | 14 | 1.512 | DIP95 | 2.245 | 2.481 | 4.913 | 1.113 | 0.8694 | 0.9052 | 47.1 | 0.2988 | 0 |
| 2011-2014 | chop_trend | team1 | 2011-2015 | 2,016 | 107 | 0.6239 | DIP95 | 0.6615 | 1.272 | 2.549 | 1.071 | 0.5616 | 0.52 | 45.17 | 0.1287 | 1 |
| 2011-2014 | chop_trend | team2 | 2011-2015 | 2,016 | 107 | 0.9358 | DIP95 | 0.6954 | 1.87 | 3.8 | 1.051 | 0.4033 | 0.3718 | 45.17 | 0.08956 | 1 |
| 2012-2015 | allon | team1 | 2012-2016 | 2,017 | 19 | 0.9742 | DIP95 | -3.127 | 3.51 | 5.826 | 0.8224 | -1.706 | -0.891 | 44.96 | -0.5079 | 1 |
| 2012-2015 | allon | team2 | 2012-2016 | 2,017 | 19 | 1.461 | DIP95 | -4.691 | 5.265 | 8.738 | 0.8224 | -1.706 | -0.891 | 44.96 | -0.5079 | 1 |
| 2012-2015 | chop_trend | team1 | 2012-2016 | 2,017 | 162 | 0.5013 | DIP95 | -1.064 | 1.443 | 2.867 | 0.8821 | -1.078 | -0.7377 | 47.29 | -0.3353 | 1 |
| 2012-2015 | chop_trend | team2 | 2012-2016 | 2,017 | 162 | 0.752 | DIP95 | -1.596 | 2.164 | 4.3 | 0.8821 | -1.078 | -0.7377 | 47.29 | -0.3353 | 1 |
| 2013-2016 | allon | team1 | 2013-2017 | 2,018 | 15 | 0.6447 | DIP95 | 1.927 | 1.647 | 2.971 | 1.167 | 1.175 | 1.17 | 52.12 | 0.3258 | 0 |
| 2013-2016 | allon | team2 | 2013-2017 | 2,018 | 15 | 0.967 | DIP95 | 2.739 | 2.47 | 4.44 | 1.158 | 1.113 | 1.109 | 52.12 | 0.3284 | 0 |
| 2013-2016 | chop_trend | team1 | 2013-2017 | 2,018 | 109 | 0.4589 | DIP95 | -1.653 | 2.179 | 3.01 | 0.7897 | -1.375 | -0.7588 | 46.33 | -0.5317 | 1 |
| 2013-2016 | chop_trend | team2 | 2013-2017 | 2,018 | 109 | 0.6884 | DIP95 | -2.48 | 3.268 | 4.515 | 0.7897 | -1.375 | -0.7588 | 46.33 | -0.5483 | 1 |
| 2014-2017 | allon | team1 | 2014-2018 | 2,019 | 10 | 1.179 | DIP95 | 0.09909 | 3.982 | 5.036 | 1.005 | 0.04472 | 0.02488 | 52.51 | 0.01096 | 1 |
| 2014-2017 | allon | team2 | 2014-2018 | 2,019 | 10 | 1.768 | DIP95 | 0.1244 | 5.973 | 7.55 | 1.004 | 0.03742 | 0.02083 | 52.51 | 0.009177 | 1 |
| 2014-2017 | chop_trend | team1 | 2014-2018 | 2,019 | 298 | 0.5104 | DIP95 | -0.4363 | 1.706 | 2.122 | 0.9189 | -0.4365 | -0.2557 | 39.84 | -0.1155 | 1 |
| 2014-2017 | chop_trend | team2 | 2014-2018 | 2,019 | 298 | 0.7656 | DIP95 | -0.6544 | 2.559 | 3.183 | 0.9189 | -0.4365 | -0.2557 | 39.84 | -0.1227 | 1 |
| 2015-2018 | allon | team1 | 2015-2019 | 2,020 | 6 | 0.8052 | DIP95 | -0.4707 | 2.549 | 4.582 | 0.9707 | -0.2715 | -0.1847 | 53.57 | -0.09968 | 1 |
| 2015-2018 | allon | team2 | 2015-2019 | 2,020 | 6 | 1.208 | DIP95 | -0.7061 | 3.823 | 6.873 | 0.9707 | -0.2715 | -0.1847 | 53.57 | -0.09968 | 1 |
| 2015-2018 | chop_trend | team1 | 2015-2019 | 2,020 | 471 | 0.4832 | DIP95 | 2.181 | 1.705 | 2.358 | 1.248 | 1.548 | 1.279 | 51.15 | 1.027 | 0 |
| 2015-2018 | chop_trend | team2 | 2015-2019 | 2,020 | 471 | 0.7249 | DIP95 | 3.272 | 2.558 | 3.536 | 1.248 | 1.548 | 1.279 | 51.15 | 1.03 | 0 |


### Against a RANDOM pick of the same size

Sizes matched per (step, stream), drawn from the strategies that have a banked winner for that cell -- the same population the rule chose from.

| step | book | budget | real | random_mean | random_min | random_max | draws | real_beats_random_mean |
|---|---|---|---|---|---|---|---|---|
| 2011-2014 | allon | team1 | 1.497 | -0.7241 | -1.541 | 0.5129 | 5 | 1 |
| 2011-2014 | allon | team2 | 2.245 | -1.086 | -2.312 | 0.7694 | 5 | 1 |
| 2011-2014 | chop_trend | team1 | 0.6615 | -0.01598 | -1.113 | 0.9049 | 5 | 1 |
| 2011-2014 | chop_trend | team2 | 0.6954 | -0.02397 | -1.67 | 1.357 | 5 | 1 |
| 2012-2015 | allon | team1 | -3.127 | -1.573 | -2.735 | -0.01808 | 5 | 0 |
| 2012-2015 | allon | team2 | -4.691 | -2.36 | -4.103 | -0.02712 | 5 | 0 |
| 2012-2015 | chop_trend | team1 | -1.064 | -0.6363 | -1.082 | -0.2005 | 5 | 0 |
| 2012-2015 | chop_trend | team2 | -1.596 | -0.9545 | -1.623 | -0.3007 | 5 | 0 |
| 2013-2016 | allon | team1 | 1.927 | 0.4287 | -0.6713 | 1.985 | 5 | 1 |
| 2013-2016 | allon | team2 | 2.739 | 0.6431 | -1.007 | 2.978 | 5 | 1 |
| 2013-2016 | chop_trend | team1 | -1.653 | -0.6284 | -1.163 | -0.1512 | 5 | 0 |
| 2013-2016 | chop_trend | team2 | -2.48 | -0.9427 | -1.745 | -0.2268 | 5 | 0 |
| 2014-2017 | allon | team1 | 0.09909 | -1.363 | -2.162 | -0.2292 | 5 | 1 |
| 2014-2017 | allon | team2 | 0.1244 | -2.044 | -3.243 | -0.3438 | 5 | 1 |
| 2014-2017 | chop_trend | team1 | -0.4363 | -1.381 | -1.59 | -1.167 | 5 | 1 |
| 2014-2017 | chop_trend | team2 | -0.6544 | -2.071 | -2.385 | -1.751 | 5 | 1 |
| 2015-2018 | allon | team1 | -0.4707 | -1.002 | -2.155 | 0.203 | 5 | 1 |
| 2015-2018 | allon | team2 | -0.7061 | -1.503 | -3.233 | 0.3044 | 5 | 1 |
| 2015-2018 | chop_trend | team1 | 2.181 | -1.562 | -1.976 | -1.318 | 5 | 1 |
| 2015-2018 | chop_trend | team2 | 3.272 | -2.343 | -2.965 | -1.978 | 5 | 1 |


The real book beats the random pick's mean in **14 of 20** (step, book, budget) cells.


### Its three nulls

| null | scope | step | book | budget | members | real | n_draws | null_mean | null_p5 | null_p95 | p_one_sided |
|---|---|---|---|---|---|---|---|---|---|---|---|
| identity | full field | 2011-2014 | allon | team1 |  | 1.497 | 200 | 5.172 | 1.497 | 9.444 | 0.78 |
| identity | full field | 2011-2014 | allon | team2 |  | 2.245 | 200 | 8.422 | 2.245 | 14.17 | 1 |
| identity | full field | 2011-2014 | chop_trend | team1 |  | 0.6615 | 200 | 6.462 | 0.6615 | 18.39 | 1 |
| identity | full field | 2011-2014 | chop_trend | team2 |  | 0.6954 | 200 | 9.71 | 0.6954 | 27.59 | 0.83 |
| identity | full field | 2012-2015 | allon | team1 |  | -3.127 | 200 | 6.282 | -3.127 | 16.05 | 1 |
| identity | full field | 2012-2015 | allon | team2 |  | -4.691 | 200 | 9.967 | -4.691 | 24.07 | 0.845 |
| identity | full field | 2012-2015 | chop_trend | team1 |  | -1.064 | 200 | 5.728 | -1.064 | 24.67 | 0.835 |
| identity | full field | 2012-2015 | chop_trend | team2 |  | -1.596 | 200 | 7.6 | -1.596 | 37.01 | 1 |
| identity | full field | 2013-2016 | allon | team1 |  | 1.927 | 200 | 6.078 | 0.975 | 18.58 | 0.77 |
| identity | full field | 2013-2016 | allon | team2 |  | 2.739 | 200 | 9.207 | 1.463 | 27.87 | 0.825 |
| identity | full field | 2013-2016 | chop_trend | team1 |  | -1.653 | 200 | 5.317 | -1.653 | 23.64 | 1 |
| identity | full field | 2013-2016 | chop_trend | team2 |  | -2.48 | 200 | 5.157 | -2.48 | 35.45 | 0.795 |
| identity | full field | 2014-2017 | allon | team1 |  | 0.09909 | 200 | 10.21 | 0.09909 | 23.12 | 0.835 |
| identity | full field | 2014-2017 | allon | team2 |  | 0.1244 | 200 | 15.49 | 0.1244 | 34.64 | 0.84 |
| identity | full field | 2014-2017 | chop_trend | team1 |  | -0.4363 | 200 | 6.905 | -0.4363 | 34.09 | 1 |
| identity | full field | 2014-2017 | chop_trend | team2 |  | -0.6544 | 200 | 9.964 | -0.6544 | 51.27 | 0.855 |
| identity | full field | 2015-2018 | allon | team1 |  | -0.4707 | 200 | 6.023 | -0.4707 | 13.64 | 1 |
| identity | full field | 2015-2018 | allon | team2 |  | -0.7061 | 200 | 8.654 | -0.7061 | 20.46 | 0.835 |
| identity | full field | 2015-2018 | chop_trend | team1 |  | 2.181 | 200 | 5.642 | 0.5623 | 26.64 | 0.335 |
| identity | full field | 2015-2018 | chop_trend | team2 |  | 3.272 | 200 | 8.217 | 0.8434 | 39.96 | 0.31 |
| shuffle | passers, full | 2011-2014 | allon | team1 | 14 | 1.497 | 19 | 1.497 | 1.497 | 1.497 | 1 |
| shuffle | passers, full | 2011-2014 | allon | team2 | 14 | 2.245 | 19 | 2.245 | 2.245 | 2.245 | 1 |
| shuffle | passers, full | 2011-2014 | chop_trend | team1 | 107 | 0.6615 | 19 | -0.0857 | -1.288 | 1.13 | 0.1579 |
| shuffle | passers, full | 2011-2014 | chop_trend | team2 | 107 | 0.6954 | 19 | -0.1286 | -1.932 | 1.695 | 0.3158 |
| shuffle | passers, full | 2012-2015 | allon | team1 | 19 | -3.127 | 19 | -3.127 | -3.127 | -3.127 | 1 |
| shuffle | passers, full | 2012-2015 | allon | team2 | 19 | -4.691 | 19 | -4.691 | -4.691 | -4.691 | 1 |
| shuffle | passers, full | 2012-2015 | chop_trend | team1 | 162 | -1.064 | 19 | -0.7723 | -1.715 | 0.7472 | 0.6842 |
| shuffle | passers, full | 2012-2015 | chop_trend | team2 | 162 | -1.596 | 19 | -1.158 | -2.573 | 1.121 | 0.6842 |
| shuffle | passers, full | 2013-2016 | allon | team1 | 15 | 1.927 | 19 | 1.927 | 1.927 | 1.927 | 1 |
| shuffle | passers, full | 2013-2016 | allon | team2 | 15 | 2.739 | 19 | 2.739 | 2.739 | 2.739 | 1 |
| shuffle | passers, full | 2013-2016 | chop_trend | team1 | 109 | -1.653 | 19 | -0.3277 | -1.02 | 0.5382 | 1 |
| shuffle | passers, full | 2013-2016 | chop_trend | team2 | 109 | -2.48 | 19 | -0.4915 | -1.531 | 0.8074 | 1 |
| shuffle | passers, full | 2014-2017 | allon | team1 | 10 | 0.09909 | 19 | 0.09909 | 0.09909 | 0.09909 | 1 |
| shuffle | passers, full | 2014-2017 | allon | team2 | 10 | 0.1244 | 19 | 0.1244 | 0.1244 | 0.1244 | 1 |
| shuffle | passers, full | 2014-2017 | chop_trend | team1 | 298 | -0.4363 | 19 | -0.9565 | -1.733 | -0.3417 | 0.1053 |
| shuffle | passers, full | 2014-2017 | chop_trend | team2 | 298 | -0.6544 | 19 | -1.435 | -2.6 | -0.5126 | 0.1053 |
| shuffle | passers, full | 2015-2018 | allon | team1 | 6 | -0.4707 | 19 | -0.4707 | -0.4707 | -0.4707 | 1 |
| shuffle | passers, full | 2015-2018 | allon | team2 | 6 | -0.7061 | 19 | -0.7061 | -0.7061 | -0.7061 | 1 |
| shuffle | passers, full | 2015-2018 | chop_trend | team1 | 471 | 2.181 | 19 | 0.02396 | -0.8426 | 0.6899 | 0 |
| shuffle | passers, full | 2015-2018 | chop_trend | team2 | 471 | 3.272 | 19 | 0.03594 | -1.264 | 1.035 | 0 |
| random-entry | passers, full | 2011-2014 | allon | team1 | 14 | 1.497 | 19 | -0.3026 | -3.205 | 1.46 | 0.05263 |
| random-entry | passers, full | 2011-2014 | allon | team2 | 14 | 2.245 | 19 | -0.4538 | -4.807 | 2.19 | 0.05263 |
| random-entry | passers, full | 2011-2014 | chop_trend | team1 | 107 | 0.6615 | 19 | -0.2355 | -2.375 | 1.587 | 0.1579 |
| random-entry | passers, full | 2011-2014 | chop_trend | team2 | 107 | 0.6954 | 19 | -0.3532 | -3.562 | 2.381 | 0.2632 |
| random-entry | passers, full | 2012-2015 | allon | team1 | 19 | -3.127 | 19 | -0.2402 | -1.183 | 0.3085 | 1 |
| random-entry | passers, full | 2012-2015 | allon | team2 | 19 | -4.691 | 19 | -0.3603 | -1.775 | 0.4627 | 1 |
| random-entry | passers, full | 2012-2015 | chop_trend | team1 | 162 | -1.064 | 19 | -0.02069 | -1.229 | 1.18 | 0.8947 |
| random-entry | passers, full | 2012-2015 | chop_trend | team2 | 162 | -1.596 | 19 | -0.03104 | -1.844 | 1.77 | 0.8947 |
| random-entry | passers, full | 2013-2016 | allon | team1 | 15 | 1.927 | 19 | -0.08838 | -1.484 | 1.894 | 0.05263 |
| random-entry | passers, full | 2013-2016 | allon | team2 | 15 | 2.739 | 19 | -0.1326 | -2.226 | 2.841 | 0.05263 |
| random-entry | passers, full | 2013-2016 | chop_trend | team1 | 109 | -1.653 | 19 | -0.1841 | -1.516 | 0.7563 | 0.9474 |
| random-entry | passers, full | 2013-2016 | chop_trend | team2 | 109 | -2.48 | 19 | -0.2761 | -2.274 | 1.134 | 0.9474 |
| random-entry | passers, full | 2014-2017 | allon | team1 | 10 | 0.09909 | 19 | -0.1989 | -0.9069 | 0.06773 | 0.05263 |
| random-entry | passers, full | 2014-2017 | allon | team2 | 10 | 0.1244 | 19 | -0.2984 | -1.36 | 0.1016 | 0.05263 |
| random-entry | passers, full | 2014-2017 | chop_trend | team1 | 298 | -0.4363 | 19 | -0.3489 | -1.145 | 0.6957 | 0.4737 |
| random-entry | passers, full | 2014-2017 | chop_trend | team2 | 298 | -0.6544 | 19 | -0.5233 | -1.718 | 1.044 | 0.4737 |
| random-entry | passers, full | 2015-2018 | allon | team1 | 6 | -0.4707 | 19 | -0.2452 | -1.96 | 0.3543 | 0.7895 |
| random-entry | passers, full | 2015-2018 | allon | team2 | 6 | -0.7061 | 19 | -0.3679 | -2.94 | 0.5314 | 0.7895 |
| random-entry | passers, full | 2015-2018 | chop_trend | team1 | 471 | 2.181 | 19 | -0.3599 | -1.935 | 0.7675 | 0 |
| random-entry | passers, full | 2015-2018 | chop_trend | team2 | 471 | 3.272 | 19 | -0.5398 | -2.903 | 1.151 | 0 |


The real book clears its null's 95th percentile in **9 of 60** cells.


### Every member, with its settings and per-year R

All 1,211 rows are in `results/r2gate2/modeA_gate3_members_fiveyr.csv`. The first 20:

| step | stream | sid | winner_index | risk_atr_len | risk_atr_mult | risk_be_pct | R_2011 | R_2012 | R_2013 | R_2014 | R_2015 | R_2016 | R_2017 | R_2018 | R_2019 | R_2020 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2011-2014 | trend-routed | aroon_signals|mama_fama_signals|variance_volume_signals|sma_baseline|adx_dmi_exit | 237 | 31 | 1 | 0.05 | 0.3432 | 0.4559 | 0.009285 | 0.2475 | 1.119 | 0.0946 | -0.1834 | -0.1901 | 0.129 | -0.01938 |
| 2011-2014 | trend-routed | aroon_signals|mama_fama_signals|variance_volume_signals|tma_baseline|adx_dmi_exit | 237 | 31 | 1 | 0.05 | 0.3994 | 0.3507 | 0.04046 | 0.2476 | 1.209 | 0.09528 | -0.1689 | -0.2127 | 0.06455 | 0.02762 |
| 2011-2014 | trend-routed | aroon_signals|relative_vigor_index_signals|variance_volume_signals|mcginley_dynamic_index|adx_dmi_exit | 235 | 31 | 1 | 0.05 | 0.2792 | 0.147 | 0.2631 | 2.339 | 0.1162 | -0.05278 | -0.07366 | 0.04443 | -0.26 | -0.2014 |
| 2011-2014 | trend-routed | bears_bulls_impulse_signals|mama_fama_signals|efficiency_ratio_volume_signals|tma_baseline|adx_dmi_exit | 1 | 2 | 1 | 0.05 | 0.2933 | 0.1702 | 0.1549 | 0.1685 | 2.232 | 0.06423 | -0.007643 | -0.04767 | -0.04317 | 0.3167 |
| 2011-2014 | trend-routed | coppock_curve_signals|bears_bulls_impulse_signals|variance_volume_signals|fantail_vma|adx_dmi_exit | 243 | 31 | 1 | 0.05 | 0.1395 | 0.3282 | 0.2353 | 0.2667 | 1.782 | 0.1973 | 0.03375 | -0.1408 | -0.004516 | 0.05997 |
| 2011-2014 | trend-routed | coppock_curve_signals|center_of_gravity_signals|variance_volume_signals|tma_baseline|adx_dmi_exit | 280 | 31 | 1 | 0.05 | 0.1487 | 0.4192 | 0.2697 | 0.2721 | 0.9828 | 0.2231 | -0.07368 | -0.01315 | 0.1024 | 0.08947 |
| 2011-2014 | trend-routed | coppock_curve_signals|center_of_gravity_signals|variance_volume_signals|wma_baseline|adx_dmi_exit | 263 | 31 | 1 | 0.05 | 0.05622 | 0.3579 | 0.07054 | 1.229 | 0.3372 | 0.02355 | -0.05413 | 0.1178 | 0.01365 | -0.2954 |
| 2011-2014 | trend-routed | coppock_curve_signals|donchian_breakout_signals|variance_volume_signals|tma_baseline|adx_dmi_exit | 268 | 31 | 1 | 0.05 | 0.1186 | 0.215 | 0.2899 | 0.2669 | 0.9551 | 0.1878 | -0.03301 | -0.03673 | 0.1011 | 0.1469 |
| 2011-2014 | trend-routed | coppock_curve_signals|trend_direction_force_index_signals|variance_volume_signals|tma_baseline|adx_dmi_exit | 267 | 31 | 1 | 0.05 | 0.2999 | 0.3879 | 0.05142 | 0.5246 | 1.433 | 0.1972 | 0.03999 | -0.2205 | 0.1298 | 0.3098 |
| 2011-2014 | trend-routed | coral_signals|bears_bulls_impulse_signals|fractal_dimension_volume_signals|ema_baseline|adx_dmi_exit | 226 | 31 | 1 | 0.05 | 0.2855 | 0.07486 | 0.06772 | -0.1154 | 3.852 | 0.1178 | -0.06866 | 0.1007 | -0.1284 | 0.001145 |
| 2011-2014 | trend-routed | coral_signals|bears_bulls_impulse_signals|fractal_dimension_volume_signals|kama_baseline|adx_dmi_exit | 240 | 31 | 1 | 0.05 | 0.03672 | 0.1434 | 0.09981 | 0.1604 | 1.94 | 0.06057 | -0.1225 | -0.04125 | -0.2373 | -0.02344 |
| 2011-2014 | trend-routed | coral_signals|bears_bulls_impulse_signals|fractal_dimension_volume_signals|sma_baseline|adx_dmi_exit | 226 | 31 | 1 | 0.05 | 0.3392 | 0.04106 | 0.06509 | 0.003598 | 4.865 | -0.04315 | -0.02714 | 0.04899 | -0.06852 | 0.05327 |
| 2011-2014 | trend-routed | coral_signals|bears_bulls_impulse_signals|fractal_dimension_volume_signals|wma_baseline|adx_dmi_exit | 226 | 31 | 1 | 0.05 | 0.3143 | 0.1372 | 0.09597 | -0.1276 | 4.476 | 0.0802 | -0.1665 | -0.0546 | -0.03192 | -0.1124 |
| 2011-2014 | trend-routed | didi_index_signals|hieken_ashi_smoothed_signals|fractal_dimension_volume_signals|vidya|adx_dmi_exit | 235 | 31 | 1 | 0.05 | -0.02041 | 0.07019 | 0.1588 | 0.4132 | 1.373 | -0.2291 | 0.07495 | 0.1878 | 0.1102 | -0.03995 |
| 2011-2014 | trend-routed | didi_index_signals|hieken_ashi_smoothed_signals|fractal_dimension_volume_signals|wma_baseline|adx_dmi_exit | 242 | 31 | 1 | 0.05 | 0.077 | 0.1218 | 0.2754 | 0.3038 | 1.637 | -0.1019 | -0.05537 | 0.08986 | 0.1491 | -0.01914 |
| 2011-2014 | trend-routed | didi_index_signals|mama_fama_signals|variance_volume_signals|sma_baseline|adx_dmi_exit | 246 | 31 | 1 | 0.05 | 0.3662 | 0.4208 | 0.1318 | 0.1683 | 1.297 | 0.09388 | 0.09927 | -0.08116 | -0.2236 | 0.05343 |
| 2011-2014 | trend-routed | didi_index_signals|price_momentum_oscillator_signals|variance_volume_signals|mcginley_dynamic_index|adx_dmi_exit | 2 | 3 | 1 | 0.05 | 0.2394 | 0.227 | 0.2307 | 0.2481 | 1.709 | 0.0255 | 0.02305 | -0.1568 | -0.2334 | 0.04457 |
| 2011-2014 | trend-routed | donchian_breakout_signals|price_momentum_oscillator_signals|variance_volume_signals|mcginley_dynamic_index|adx_dmi_exit | 236 | 31 | 1 | 0.05 | 0.2938 | 0.314 | 0.04518 | 0.2849 | 2.373 | -0.07275 | 0.03379 | -0.2327 | 0.2263 | -0.4406 |
| 2011-2014 | trend-routed | donchian_breakout_signals|supertrend_signals|variance_volume_signals|t3_baseline|adx_dmi_exit | 228 | 31 | 1 | 0.05 | 0.1413 | 0.2198 | 0.3954 | 0.2473 | 1.664 | 0.1425 | -0.05496 | 0.01427 | -0.1698 | -0.434 |
| 2011-2014 | trend-routed | dspo_signals|fx_sniper_ergodic_cci_signals|fractal_dimension_volume_signals|alma_baseline|adx_dmi_exit | 1 | 2 | 1 | 0.05 | -0.009102 | 0.3187 | 0.03618 | 0.03366 | 5.817 | -0.1217 | -0.3594 | -0.1941 | -0.1545 | -0.1745 |


## Provenance

| file | rows | md5 |
|---|---|---|
| `results/r2gate2/modeA_gate3_passersbook.csv` | 20 | 913e3f4f358a |
| `results/r2gate2/modeA_gate3_passersbook_nulls.csv` | 60 | 6131572191d2 |
| `results/r2gate2/modeA_gate3_members.csv` | 59,268 | 8339720b134a |
| `results/r2gate2/modeA_gate3_passersbook_strict.csv` | 16 | 2e8a1a18e674 |
| `results/r2gate2/modeA_gate3_passersbook_strict_nulls.csv` | 48 | 0957b45fb14e |
| `results/r2gate2/modeA_gate3_randompick_strict.csv` | 80 | a7d6b5124749 |
| `results/r2gate2/modeA_gate3_members_strict.csv` | 473 | 4cfc48f800b2 |
| `results/r2gate2/modeA_gate3_passersbook_fiveyr.csv` | 20 | 53d38d4b5747 |
| `results/r2gate2/modeA_gate3_passersbook_fiveyr_nulls.csv` | 60 | 2695dfa81ceb |
| `results/r2gate2/modeA_gate3_randompick_fiveyr.csv` | 100 | 499e85dfb072 |
| `results/r2gate2/modeA_gate3_members_fiveyr.csv` | 1,211 | b44ed6814d39 |
