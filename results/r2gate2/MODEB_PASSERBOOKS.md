# MODE B — THE PASSERS' BOOKS, THREE MEMBERSHIP RULES

Generated 2026-11-21 21:05 by `code/l2r2gate3.py`. **No new tuning anywhere**: every configuration was already chosen by gate 2, and a rule only decides which of them are members. Equal weight, no picking, no weighting by past record. Sized on the build years and not touched again; the traded year is what is reported.


## The rules, and how many pass

| rule | membership | trades | steps |
|---|---|---|---|
| `grade` | cleared the bars on the GRADE year (year 5) | year 6 | all five steps |
| `strict` | cleared the bars on the GRADE year (5) AND the TRADE year (6), both unseen by the tuner | year 7 | steps 1-4; step 5's year 7 is 2021 and 2021+ is sealed |
| `fiveyr` | cleared the bars on the FULL tune-plus-grade record, years 1-5 stitched into one block | year 6 | all five steps |

### Members per step

| rule | step | routed | always_on | any_stream | member_cells |
|---|---|---|---|---|---|
| grade | 2011-2014 | 17,286 | 9,628 | 24,605 | 27,889 |
| grade | 2012-2015 | 2,528 | 2,876 | 5,249 | 5,619 |
| grade | 2013-2016 | 2,228 | 3,071 | 5,176 | 5,637 |
| grade | 2014-2017 | 8,015 | 6,918 | 14,172 | 15,803 |
| grade | 2015-2018 | 930 | 707 | 1,621 | 1,669 |
| strict | 2011-2014 | 228 | 87 | 314 | 320 |
| strict | 2012-2015 | 14 | 14 | 28 | 28 |
| strict | 2013-2016 | 42 | 119 | 160 | 170 |
| strict | 2014-2017 | 16 | 21 | 37 | 38 |
| fiveyr | 2011-2014 | 226 | 10 | 235 | 236 |
| fiveyr | 2012-2015 | 333 | 17 | 348 | 351 |
| fiveyr | 2013-2016 | 197 | 10 | 207 | 207 |
| fiveyr | 2014-2017 | 348 | 12 | 360 | 361 |
| fiveyr | 2015-2018 | 581 | 12 | 591 | 593 |


Summed over the steps each rule trades (so `strict` sums four, the others five):

| rule | routed | always_on | any_stream | member_cells |
|---|---|---|---|---|
| fiveyr | 1,685 | 61 | 1,741 | 1,748 |
| grade | 30,987 | 23,200 | 50,823 | 56,617 |
| strict | 300 | 241 | 539 | 556 |


## Rule `grade`

Membership: cleared the bars on the GRADE year (year 5). Trades year 6, all five steps.


### Full KPI table


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

| step | book | budget | size_years | trade_year | members | size_scale | scale_binds | trade_total_pct | trade_max_dd_pct | trade_dip95_pct | trade_profit_factor | trade_sortino | trade_calmar | trade_win_rate_pct | retention | FIT |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2011-2014 | allon | team1 | 2011-2015 | 2,016 | 9,628 | 0.9053 | DIP95 | 1.192 | 1.691 | 3.88 | 1.08 | 0.5748 | 0.7045 | 48.65 | 0.1927 | 1 |
| 2011-2014 | allon | team2 | 2011-2015 | 2,016 | 9,628 | 1.358 | DIP95 | 1.787 | 2.537 | 5.821 | 1.08 | 0.5748 | 0.7045 | 48.65 | 0.1927 | 1 |
| 2011-2014 | chop_trend | team1 | 2011-2015 | 2,016 | 17,286 | 0.5572 | DIP95 | -2.11 | 3.003 | 3.69 | 0.8046 | -1.741 | -0.7024 | 47.88 | -0.8521 | 1 |
| 2011-2014 | chop_trend | team2 | 2011-2015 | 2,016 | 17,286 | 0.8358 | DIP95 | -3.164 | 4.505 | 5.535 | 0.8046 | -1.741 | -0.7024 | 47.88 | -0.8521 | 1 |
| 2012-2015 | allon | team1 | 2012-2016 | 2,017 | 2,876 | 0.6799 | DIP95 | -1.433 | 3.478 | 4.816 | 0.9153 | -0.8152 | -0.4121 | 49.22 | -0.2087 | 1 |
| 2012-2015 | allon | team2 | 2012-2016 | 2,017 | 2,876 | 1.02 | DIP95 | -2.15 | 5.217 | 7.224 | 0.9153 | -0.8152 | -0.4121 | 49.22 | -0.2087 | 1 |
| 2012-2015 | chop_trend | team1 | 2012-2016 | 2,017 | 2,528 | 0.7954 | DIP95 | -2.163 | 3.065 | 4.567 | 0.8485 | -1.404 | -0.7058 | 49.61 | -0.4901 | 1 |
| 2012-2015 | chop_trend | team2 | 2012-2016 | 2,017 | 2,528 | 1.193 | DIP95 | -3.245 | 4.598 | 6.85 | 0.8485 | -1.404 | -0.7058 | 49.61 | -0.4901 | 1 |
| 2013-2016 | allon | team1 | 2013-2017 | 2,018 | 3,071 | 0.7056 | DIP95 | 3.146 | 1.936 | 2.734 | 1.239 | 1.867 | 1.625 | 50.19 | 0.4102 | 0 |
| 2013-2016 | allon | team2 | 2013-2017 | 2,018 | 3,071 | 1.058 | DIP95 | 4.719 | 2.904 | 4.101 | 1.239 | 1.867 | 1.625 | 50.19 | 0.4102 | 0 |
| 2013-2016 | chop_trend | team1 | 2013-2017 | 2,018 | 2,228 | 0.567 | DIP95 | -1.08 | 2.728 | 3.813 | 0.9132 | -0.7006 | -0.3959 | 45.56 | -0.2104 | 1 |
| 2013-2016 | chop_trend | team2 | 2013-2017 | 2,018 | 2,228 | 0.8505 | DIP95 | -1.62 | 4.092 | 5.72 | 0.9132 | -0.7006 | -0.3959 | 45.56 | -0.2104 | 1 |
| 2014-2017 | allon | team1 | 2014-2018 | 2,019 | 6,918 | 0.6042 | DIP95 | -1.793 | 3.021 | 4.992 | 0.8867 | -0.9388 | -0.5934 | 46.72 | -0.4035 | 1 |
| 2014-2017 | allon | team2 | 2014-2018 | 2,019 | 6,918 | 0.9063 | DIP95 | -2.689 | 4.531 | 7.489 | 0.8867 | -0.9388 | -0.5934 | 46.72 | -0.4035 | 1 |
| 2014-2017 | chop_trend | team1 | 2014-2018 | 2,019 | 8,015 | 0.6541 | DIP95 | -2.578 | 2.953 | 4.621 | 0.8037 | -1.914 | -0.8729 | 48.65 | -6.183 | 1 |
| 2014-2017 | chop_trend | team2 | 2014-2018 | 2,019 | 8,015 | 0.9811 | DIP95 | -3.867 | 4.43 | 6.932 | 0.8037 | -1.914 | -0.8729 | 48.65 | -6.183 | 1 |
| 2015-2018 | allon | team1 | 2015-2019 | 2,020 | 707 | 1.012 | DIP95 | -2.91 | 4.362 | 7.351 | 0.8717 | -1.021 | -0.667 | 51.34 | -0.2208 | 1 |
| 2015-2018 | allon | team2 | 2015-2019 | 2,020 | 707 | 1.518 | DIP95 | -4.364 | 6.543 | 11.03 | 0.8717 | -1.021 | -0.667 | 51.34 | -0.2208 | 1 |
| 2015-2018 | chop_trend | team1 | 2015-2019 | 2,020 | 930 | 0.9049 | DIP95 | 0.1724 | 3.523 | 4.786 | 1.01 | 0.07812 | 0.04894 | 51.72 | 0.02151 | 1 |
| 2015-2018 | chop_trend | team2 | 2015-2019 | 2,020 | 930 | 1.357 | DIP95 | 0.2586 | 5.284 | 7.179 | 1.01 | 0.07812 | 0.04894 | 51.72 | 0.02151 | 1 |


### Against a RANDOM pick of the same size

Sizes matched per (step, stream), drawn from the strategies that have a banked winner for that cell -- the same population the rule chose from.

| step | book | budget | real | random_mean | random_min | random_max | draws | real_beats_random_mean |
|---|---|---|---|---|---|---|---|---|
| 2011-2014 | allon | team1 | 1.192 | -0.6568 | -0.7914 | -0.4962 | 5 | 1 |
| 2011-2014 | allon | team2 | 1.787 | -0.9851 | -1.187 | -0.7443 | 5 | 1 |
| 2011-2014 | chop_trend | team1 | -2.11 | -0.6126 | -1.069 | -0.3597 | 5 | 0 |
| 2011-2014 | chop_trend | team2 | -3.164 | -0.9188 | -1.603 | -0.5396 | 5 | 0 |
| 2012-2015 | allon | team1 | -1.433 | -0.8109 | -1.284 | -0.5665 | 5 | 0 |
| 2012-2015 | allon | team2 | -2.15 | -1.216 | -1.926 | -0.8497 | 5 | 0 |
| 2012-2015 | chop_trend | team1 | -2.163 | -1.585 | -2.388 | -1.012 | 5 | 0 |
| 2012-2015 | chop_trend | team2 | -3.245 | -2.378 | -3.582 | -1.518 | 5 | 0 |
| 2013-2016 | allon | team1 | 3.146 | 0.7681 | 0.6319 | 0.9564 | 5 | 1 |
| 2013-2016 | allon | team2 | 4.719 | 1.152 | 0.9479 | 1.435 | 5 | 1 |
| 2013-2016 | chop_trend | team1 | -1.08 | -0.02807 | -0.5989 | 0.2031 | 5 | 0 |
| 2013-2016 | chop_trend | team2 | -1.62 | -0.0421 | -0.8983 | 0.3047 | 5 | 0 |
| 2014-2017 | allon | team1 | -1.793 | -3.929 | -4.121 | -3.744 | 5 | 1 |
| 2014-2017 | allon | team2 | -2.689 | -5.894 | -6.182 | -5.616 | 5 | 1 |
| 2014-2017 | chop_trend | team1 | -2.578 | -1.752 | -2.009 | -1.544 | 5 | 0 |
| 2014-2017 | chop_trend | team2 | -3.867 | -2.629 | -3.014 | -2.315 | 5 | 0 |
| 2015-2018 | allon | team1 | -2.91 | -1.775 | -2.157 | -1.592 | 5 | 0 |
| 2015-2018 | allon | team2 | -4.364 | -2.663 | -3.235 | -2.389 | 5 | 0 |
| 2015-2018 | chop_trend | team1 | 0.1724 | -1.489 | -1.832 | -0.9315 | 5 | 1 |
| 2015-2018 | chop_trend | team2 | 0.2586 | -2.234 | -2.748 | -1.397 | 5 | 1 |


The real book beats the random pick's mean in **8 of 20** (step, book, budget) cells.


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


### Every member, with its settings and per-year R

All 56,617 rows are in `results/r2gate2/modeB_gate3_members.csv`. The first 20:

| step | stream | sid | winner_index | risk_atr_len | risk_atr_mult | risk_be_pct | R_2011 | R_2012 | R_2013 | R_2014 | R_2015 | R_2016 | R_2017 | R_2018 | R_2019 | R_2020 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2011-2014 | trend-routed | adx_dmi_signals|bears_bulls_impulse_signals|variance_volume_signals|ema_baseline|adx_dmi_exit | 234 | 31 | 1 | 0.05 | 0.285 | 0.1809 | -0.07191 | 0.1366 | 0.4597 | 0.3652 | -0.06005 | 0.03235 | 0.6304 | 0.2428 |
| 2011-2014 | trend-routed | adx_dmi_signals|bears_bulls_impulse_signals|variance_volume_signals|wma_baseline|adx_dmi_exit | 234 | 31 | 1 | 0.05 | 0.2241 | 0.1897 | -0.1294 | 0.1522 | 0.3722 | 0.3843 | -0.08103 | 0.03712 | 0.4434 | 0.1992 |
| 2011-2014 | trend-routed | adx_dmi_signals|center_of_gravity_signals|williams_vix_fix_volume_signals|ema_baseline|adx_dmi_exit | 255 | 31 | 1 | 0.05 | 0.1811 | 0.09624 | -0.05194 | -0.02273 | 0.3942 | 0.03924 | -0.08348 | -0.1124 | -0.1801 | 0.3893 |
| 2011-2014 | trend-routed | adx_dmi_signals|chandelier_exit_signals|variance_volume_signals|ema_baseline|adx_dmi_exit | 236 | 31 | 1 | 0.05 | 0.03505 | 0.3722 | -0.1145 | 0.1824 | 0.8624 | -0.04467 | -0.08214 | -0.01264 | 0.2006 | 0.03119 |
| 2011-2014 | trend-routed | adx_dmi_signals|coral_signals|williams_vix_fix_volume_signals|ema_baseline|adx_dmi_exit | 255 | 31 | 1 | 0.05 | 0.1811 | 0.02364 | -0.1197 | -0.0115 | 0.3071 | 0.03185 | -0.03854 | -0.05766 | -0.1801 | 0.3336 |
| 2011-2014 | trend-routed | adx_dmi_signals|fisher_transform_signals|williams_vix_fix_volume_signals|ema_baseline|adx_dmi_exit | 255 | 31 | 1 | 0.05 | 0.1811 | 0.04941 | -0.08551 | -0.03907 | 0.3537 | 0.03924 | -0.04882 | -0.07471 | -0.1801 | 0.4426 |
| 2011-2014 | trend-routed | adx_dmi_signals|fisher_transform_signals|williams_vix_fix_volume_signals|wma_baseline|adx_dmi_exit | 255 | 31 | 1 | 0.05 | -0.1075 | 0.004199 | -0.01035 | 0.09418 | 0.4928 | -0.1526 | -0.1233 | -0.3483 | -0.5094 | 0.4293 |
| 2011-2014 | trend-routed | adx_dmi_signals|fx_sniper_ergodic_cci_signals|chaikin_volatility_volume_signals|ema_baseline|adx_dmi_exit | 222 | 31 | 1 | 0.05 | 0.03917 | 0.08605 | 0.03984 | -0.04808 | 0.4796 | 0.02088 | 0.06548 | 0.08444 | 0.1119 | 0.001318 |
| 2011-2014 | trend-routed | adx_dmi_signals|fx_sniper_ergodic_cci_signals|efficiency_ratio_volume_signals|rma_baseline|adx_dmi_exit | 224 | 31 | 1 | 0.05 | -0.1014 | -0.02552 | -0.04487 | -0.04062 | 0.9343 | -0.1592 | -0.08646 | -0.02792 | -0.1714 | -0.1106 |
| 2011-2014 | trend-routed | adx_dmi_signals|fx_sniper_ergodic_cci_signals|williams_vix_fix_volume_signals|ema_baseline|adx_dmi_exit | 255 | 31 | 1 | 0.05 | 0.1811 | 0.04941 | -0.08551 | -0.03907 | 0.3829 | 0.03924 | -0.04882 | -0.07471 | -0.1801 | 0.3893 |
| 2011-2014 | trend-routed | adx_dmi_signals|halftrend_signals|variance_volume_signals|ema_baseline|adx_dmi_exit | 237 | 31 | 1 | 0.05 | 0.06768 | -0.04909 | 0.2169 | 0.1727 | 1.312 | 0.1462 | -0.1247 | -0.159 | 0.1176 | -0.229 |
| 2011-2014 | trend-routed | adx_dmi_signals|halftrend_signals|variance_volume_signals|mcginley_dynamic_index|adx_dmi_exit | 236 | 31 | 1 | 0.05 | -0.01882 | -0.09646 | 0.2309 | 0.08888 | 1.791 | 0.1355 | -0.1303 | -0.1541 | -0.003657 | -0.3644 |
| 2011-2014 | trend-routed | adx_dmi_signals|ichimoku_signals|chaikin_volatility_volume_signals|mcginley_dynamic_index|adx_dmi_exit | 222 | 31 | 1 | 0.05 | -0.09814 | 0.237 | 0.4888 | 0.3725 | 3.293 | -0.2533 | 0.2331 | -0.1834 | -0.3142 | -0.06872 |
| 2011-2014 | trend-routed | adx_dmi_signals|ichimoku_signals|choppiness_index_volume_signals|ema_baseline|adx_dmi_exit | 223 | 31 | 1 | 0.05 | 0.1061 | 0.08982 | 0.01646 | 0.004826 | 0.75 | 0.03007 | 0.0711 | -0.1323 | -0.1244 | -0.001958 |
| 2011-2014 | trend-routed | adx_dmi_signals|ichimoku_signals|efficiency_ratio_volume_signals|t3_baseline|adx_dmi_exit | 234 | 31 | 1 | 0.05 | 0.1683 | 0.1661 | 0.06997 | -0.05602 | 1.739 | -0.1017 | -0.01714 | -0.1609 | -0.2556 | 0.102 |
| 2011-2014 | trend-routed | adx_dmi_signals|ichimoku_signals|variance_volume_signals|wma_baseline|adx_dmi_exit | 237 | 31 | 1 | 0.05 | 0.3842 | 0.105 | -0.1559 | 0.3965 | 1.953 | 0.001752 | 0.06242 | -0.2371 | -0.1856 | -0.1394 |
| 2011-2014 | trend-routed | adx_dmi_signals|kuskus_starlight_signals|volatility_ratio_volume_signals|mcginley_dynamic_index|adx_dmi_exit | 212 | 31 | 1 | 0.05 | -0.02922 | 0.3151 | 0.0283 | 0.02151 | 0.6478 | 0.02177 | 0.1057 | 0.1745 | -0.1583 | -0.01238 |
| 2011-2014 | trend-routed | adx_dmi_signals|laguerre_filter_signals|variance_volume_signals|ema_baseline|adx_dmi_exit | 237 | 31 | 1 | 0.05 | 0.1373 | 0.06529 | 0.114 | 0.2203 | 1.627 | -0.06332 | 0.0003223 | -0.2658 | 0.2964 | -0.2471 |
| 2011-2014 | trend-routed | adx_dmi_signals|laguerre_filter_signals|variance_volume_signals|mcginley_dynamic_index|adx_dmi_exit | 236 | 31 | 1 | 0.05 | 0.008867 | 0.2172 | 0.1133 | 0.1829 | 2.201 | -0.1376 | 0.01894 | -0.2787 | 0.1357 | -0.3474 |
| 2011-2014 | trend-routed | adx_dmi_signals|lemantrend_signals|williams_vix_fix_volume_signals|hma_baseline|adx_dmi_exit | 220 | 31 | 1 | 0.05 | -0.09574 | 0.02291 | -0.06239 | -0.1889 | 0.2453 | 0.007642 | -0.1092 | -0.1044 | -0.2737 | 0.07364 |


## Rule `strict`

Membership: cleared the bars on the GRADE year (5) AND the TRADE year (6), both unseen by the tuner. Trades year 7, steps 1-4; step 5's year 7 is 2021 and 2021+ is sealed.


### Full KPI table


### TEAM 1

| KPI | ALWAYS-ON | ROUTED (chop RANGING + trend TRENDING) |
|---|---|---|
| median year | 0.56% | 0.15% |
| average year | 0.65% | -0.09% |
| worst year | -0.16% | -1.82% |
| best year | 1.64% | 1.16% |
| total 2017-2020 | 2.59% | -0.37% |
| CAGR | 0.65% | -0.09% |
| worst day | -0.68% | -0.98% |
| max drawdown | -3.34% | -2.89% |
| DIP95 (worst step) | 3.84% | 4.30% |
| Sharpe | 0.26 | -0.04 |
| Sortino | 0.38 | -0.06 |
| Calmar (total / max DD, the shipped bar) | 0.78 | -0.13 |
| Calmar (CAGR / max DD) | 0.19 | -0.03 |
| profit factor (trades, median step) | 1.04 | 1.01 |
| win rate (trades, median step) | 50.00% | 51.08% |
| positive years of 4 | 2 | 2 |
| retention (median step) | 0.10 | 0.02 |
| steps flagged FIT of 4 | 2 | 3 |

Per year:

- ALWAYS-ON: 2017: -0.16% | 2018: +1.64% | 2019: +1.20% | 2020: -0.08%
- ROUTED (chop RANGING + trend TRENDING): 2017: -0.33% | 2018: +1.16% | 2019: -1.82% | 2020: +0.63%

### TEAM 2

| KPI | ALWAYS-ON | ROUTED (chop RANGING + trend TRENDING) |
|---|---|---|
| median year | 0.84% | 0.22% |
| average year | 0.97% | -0.14% |
| worst year | -0.24% | -2.73% |
| best year | 2.46% | 1.74% |
| total 2017-2020 | 3.89% | -0.55% |
| CAGR | 0.97% | -0.14% |
| worst day | -1.01% | -1.47% |
| max drawdown | -5.02% | -4.34% |
| DIP95 (worst step) | 5.77% | 6.45% |
| Sharpe | 0.26 | -0.04 |
| Sortino | 0.38 | -0.06 |
| Calmar (total / max DD, the shipped bar) | 0.78 | -0.13 |
| Calmar (CAGR / max DD) | 0.19 | -0.03 |
| profit factor (trades, median step) | 1.04 | 1.01 |
| win rate (trades, median step) | 50.00% | 51.08% |
| positive years of 4 | 2 | 2 |
| retention (median step) | 0.10 | 0.02 |
| steps flagged FIT of 4 | 2 | 3 |

Per year:

- ALWAYS-ON: 2017: -0.24% | 2018: +2.46% | 2019: +1.79% | 2020: -0.12%
- ROUTED (chop RANGING + trend TRENDING): 2017: -0.50% | 2018: +1.74% | 2019: -2.73% | 2020: +0.94%

### Per step, as traded

| step | book | budget | size_years | trade_year | members | size_scale | scale_binds | trade_total_pct | trade_max_dd_pct | trade_dip95_pct | trade_profit_factor | trade_sortino | trade_calmar | trade_win_rate_pct | retention | FIT |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2011-2014 | allon | team1 | 2011-2016 | 2,017 | 87 | 0.5943 | DIP95 | -0.1629 | 2.726 | 3.722 | 0.9883 | -0.1043 | -0.05976 | 49.22 | -0.04115 | 1 |
| 2011-2014 | allon | team2 | 2011-2016 | 2,017 | 87 | 0.8915 | DIP95 | -0.2444 | 4.09 | 5.583 | 0.9883 | -0.1043 | -0.05976 | 49.22 | -0.04115 | 1 |
| 2011-2014 | chop_trend | team1 | 2011-2016 | 2,017 | 228 | 0.5245 | DIP95 | -0.3329 | 1.637 | 2.925 | 0.9693 | -0.2837 | -0.2033 | 51.16 | -0.09806 | 1 |
| 2011-2014 | chop_trend | team2 | 2011-2016 | 2,017 | 228 | 0.7867 | DIP95 | -0.4993 | 2.456 | 4.387 | 0.9693 | -0.2837 | -0.2033 | 51.16 | -0.09806 | 1 |
| 2012-2015 | allon | team1 | 2012-2017 | 2,018 | 14 | 0.5537 | DIP95 | 1.643 | 2.231 | 3.032 | 1.123 | 1.084 | 0.7363 | 53.67 | 0.3102 | 0 |
| 2012-2015 | allon | team2 | 2012-2017 | 2,018 | 14 | 0.8306 | DIP95 | 2.464 | 3.347 | 4.549 | 1.123 | 1.084 | 0.7363 | 53.67 | 0.3102 | 0 |
| 2012-2015 | chop_trend | team1 | 2012-2017 | 2,018 | 14 | 0.4288 | DIP95 | 1.158 | 1.232 | 1.82 | 1.158 | 1.301 | 0.9396 | 52.38 | 0.3242 | 0 |
| 2012-2015 | chop_trend | team2 | 2012-2017 | 2,018 | 14 | 0.6432 | DIP95 | 1.736 | 1.848 | 2.731 | 1.158 | 1.301 | 0.9396 | 52.38 | 0.3242 | 0 |
| 2013-2016 | allon | team1 | 2013-2018 | 2,019 | 119 | 0.69 | DIP95 | 1.196 | 2.636 | 3.727 | 1.077 | 0.6608 | 0.4539 | 47.88 | 0.2124 | 0 |
| 2013-2016 | allon | team2 | 2013-2018 | 2,019 | 119 | 1.035 | DIP95 | 1.794 | 3.953 | 5.59 | 1.077 | 0.6608 | 0.4539 | 47.88 | 0.2124 | 0 |
| 2013-2016 | chop_trend | team1 | 2013-2018 | 2,019 | 42 | 0.6193 | DIP95 | -1.82 | 2.411 | 4.3 | 0.8595 | -1.359 | -0.7548 | 46.9 | -0.3563 | 1 |
| 2013-2016 | chop_trend | team2 | 2013-2018 | 2,019 | 42 | 0.929 | DIP95 | -2.73 | 3.616 | 6.451 | 0.8595 | -1.359 | -0.7548 | 46.9 | -0.3563 | 1 |
| 2014-2017 | allon | team1 | 2014-2019 | 2,020 | 21 | 0.4312 | DIP95 | -0.08238 | 2.326 | 3.845 | 0.9939 | -0.04324 | -0.03542 | 50.77 | -0.01991 | 1 |
| 2014-2017 | allon | team2 | 2014-2019 | 2,020 | 21 | 0.6468 | DIP95 | -0.1236 | 3.488 | 5.767 | 0.9939 | -0.04324 | -0.03542 | 50.77 | -0.01991 | 1 |
| 2014-2017 | chop_trend | team1 | 2014-2019 | 2,020 | 16 | 0.5849 | DIP95 | 0.6285 | 2.685 | 4.15 | 1.043 | 0.2926 | 0.2341 | 51 | 0.1454 | 1 |
| 2014-2017 | chop_trend | team2 | 2014-2019 | 2,020 | 16 | 0.8773 | DIP95 | 0.9427 | 4.027 | 6.225 | 1.043 | 0.2926 | 0.2341 | 51 | 0.1454 | 1 |


### Against a RANDOM pick of the same size

Sizes matched per (step, stream), drawn from the strategies that have a banked winner for that cell -- the same population the rule chose from.

| step | book | budget | real | random_mean | random_min | random_max | draws | real_beats_random_mean |
|---|---|---|---|---|---|---|---|---|
| 2011-2014 | allon | team1 | -0.1629 | -1.491 | -2.369 | -0.88 | 5 | 1 |
| 2011-2014 | allon | team2 | -0.2444 | -2.236 | -3.554 | -1.32 | 5 | 1 |
| 2011-2014 | chop_trend | team1 | -0.3329 | -1.095 | -2.181 | 0.1284 | 5 | 1 |
| 2011-2014 | chop_trend | team2 | -0.4993 | -1.643 | -3.272 | 0.1926 | 5 | 1 |
| 2012-2015 | allon | team1 | 1.643 | 1.599 | 0.7316 | 2.684 | 5 | 1 |
| 2012-2015 | allon | team2 | 2.464 | 2.399 | 1.097 | 4.026 | 5 | 1 |
| 2012-2015 | chop_trend | team1 | 1.158 | 0.2213 | 0.08432 | 0.4255 | 5 | 1 |
| 2012-2015 | chop_trend | team2 | 1.736 | 0.332 | 0.1265 | 0.6382 | 5 | 1 |
| 2013-2016 | allon | team1 | 1.196 | -3.858 | -4.32 | -3.003 | 5 | 1 |
| 2013-2016 | allon | team2 | 1.794 | -5.787 | -6.48 | -4.505 | 5 | 1 |
| 2013-2016 | chop_trend | team1 | -1.82 | -0.9868 | -1.712 | -0.4587 | 5 | 0 |
| 2013-2016 | chop_trend | team2 | -2.73 | -1.48 | -2.568 | -0.6881 | 5 | 0 |
| 2014-2017 | allon | team1 | -0.08238 | -1.826 | -2.591 | -0.7587 | 5 | 1 |
| 2014-2017 | allon | team2 | -0.1236 | -2.739 | -3.887 | -1.138 | 5 | 1 |
| 2014-2017 | chop_trend | team1 | 0.6285 | -0.7208 | -1.156 | -0.206 | 5 | 1 |
| 2014-2017 | chop_trend | team2 | 0.9427 | -1.081 | -1.734 | -0.3089 | 5 | 1 |


The real book beats the random pick's mean in **14 of 16** (step, book, budget) cells.


### Its three nulls

| null | scope | step | book | budget | members | real | n_draws | null_mean | null_p5 | null_p95 | p_one_sided |
|---|---|---|---|---|---|---|---|---|---|---|---|
| identity | full field | 2011-2014 | allon | team1 |  | -0.1629 | 200 | 5.292 | -0.1629 | 12.98 | 1 |
| identity | full field | 2011-2014 | allon | team2 |  | -0.2444 | 200 | 8.681 | -0.2444 | 19.47 | 1 |
| identity | full field | 2011-2014 | chop_trend | team1 |  | -0.3329 | 200 | 3.232 | -0.3329 | 8.34 | 1 |
| identity | full field | 2011-2014 | chop_trend | team2 |  | -0.4993 | 200 | 4.966 | -0.4993 | 12.51 | 1 |
| identity | full field | 2012-2015 | allon | team1 |  | 1.643 | 200 | 5.183 | 1.4 | 9.492 | 0.705 |
| identity | full field | 2012-2015 | allon | team2 |  | 2.464 | 200 | 6.841 | 2.1 | 14.24 | 0.84 |
| identity | full field | 2012-2015 | chop_trend | team1 |  | 1.158 | 200 | 2.914 | -1.344 | 6.385 | 0.705 |
| identity | full field | 2012-2015 | chop_trend | team2 |  | 1.736 | 200 | 4.176 | -2.016 | 9.577 | 0.57 |
| identity | full field | 2013-2016 | allon | team1 |  | 1.196 | 200 | 6.243 | 1.196 | 14.85 | 0.875 |
| identity | full field | 2013-2016 | allon | team2 |  | 1.794 | 200 | 10.02 | 1.794 | 22.28 | 1 |
| identity | full field | 2013-2016 | chop_trend | team1 |  | -1.82 | 200 | 4.496 | -1.82 | 11.35 | 1 |
| identity | full field | 2013-2016 | chop_trend | team2 |  | -2.73 | 200 | 5.105 | -2.73 | 17.03 | 1 |
| identity | full field | 2014-2017 | allon | team1 |  | -0.08238 | 200 | 4.335 | -0.08238 | 10.79 | 1 |
| identity | full field | 2014-2017 | allon | team2 |  | -0.1236 | 200 | 6.772 | -0.1236 | 16.18 | 0.855 |
| identity | full field | 2014-2017 | chop_trend | team1 |  | 0.6285 | 200 | 4.915 | -0.4966 | 15.77 | 0.71 |
| identity | full field | 2014-2017 | chop_trend | team2 |  | 0.9427 | 200 | 7.173 | -0.7419 | 23.49 | 0.57 |
| shuffle | passers, full | 2011-2014 | allon | team1 | 87 | 10.98 | 19 | 10.98 | 10.98 | 10.98 | 1 |
| shuffle | passers, full | 2011-2014 | allon | team2 | 87 | 16.46 | 19 | 16.46 | 16.46 | 16.46 | 1 |
| shuffle | passers, full | 2011-2014 | chop_trend | team1 | 228 | 3.189 | 19 | 1.21 | 0.06007 | 2.172 | 0 |
| shuffle | passers, full | 2011-2014 | chop_trend | team2 | 228 | 4.784 | 19 | 1.815 | 0.0901 | 3.258 | 0 |
| shuffle | passers, full | 2012-2015 | allon | team1 | 14 | 9.069 | 19 | 9.069 | 9.069 | 9.069 | 1 |
| shuffle | passers, full | 2012-2015 | allon | team2 | 14 | 13.6 | 19 | 13.6 | 13.6 | 13.6 | 1 |
| shuffle | passers, full | 2012-2015 | chop_trend | team1 | 14 | 3.824 | 19 | 1.031 | -0.0746 | 2.226 | 0 |
| shuffle | passers, full | 2012-2015 | chop_trend | team2 | 14 | 5.735 | 19 | 1.547 | -0.1119 | 3.339 | 0 |
| shuffle | passers, full | 2013-2016 | allon | team1 | 119 | 13.18 | 19 | 13.18 | 13.18 | 13.18 | 1 |
| shuffle | passers, full | 2013-2016 | allon | team2 | 119 | 19.77 | 19 | 19.77 | 19.77 | 19.77 | 1 |
| shuffle | passers, full | 2013-2016 | chop_trend | team1 | 42 | 10.13 | 19 | 2.524 | 0.9816 | 3.815 | 0 |
| shuffle | passers, full | 2013-2016 | chop_trend | team2 | 42 | 15.19 | 19 | 3.786 | 1.472 | 5.722 | 0 |
| shuffle | passers, full | 2014-2017 | allon | team1 | 21 | 8.469 | 19 | 8.469 | 8.469 | 8.469 | 1 |
| shuffle | passers, full | 2014-2017 | allon | team2 | 21 | 12.7 | 19 | 12.7 | 12.7 | 12.7 | 1 |
| shuffle | passers, full | 2014-2017 | chop_trend | team1 | 16 | 6.798 | 19 | 1.318 | 0.1791 | 3.244 | 0 |
| shuffle | passers, full | 2014-2017 | chop_trend | team2 | 16 | 10.2 | 19 | 1.978 | 0.2687 | 4.866 | 0 |
| random-entry | passers, full | 2011-2014 | allon | team1 | 87 | 10.98 | 19 | -0.4504 | -1.904 | 0.9861 | 0 |
| random-entry | passers, full | 2011-2014 | allon | team2 | 87 | 16.46 | 19 | -0.6756 | -2.856 | 1.479 | 0 |
| random-entry | passers, full | 2011-2014 | chop_trend | team1 | 228 | 3.189 | 19 | 0.02387 | -2.043 | 2.088 | 0 |
| random-entry | passers, full | 2011-2014 | chop_trend | team2 | 228 | 4.784 | 19 | 0.0358 | -3.065 | 3.132 | 0 |
| random-entry | passers, full | 2012-2015 | allon | team1 | 14 | 9.069 | 19 | 0.2087 | -0.006542 | 0.8437 | 0 |
| random-entry | passers, full | 2012-2015 | allon | team2 | 14 | 13.6 | 19 | 0.3131 | -0.009813 | 1.266 | 0 |
| random-entry | passers, full | 2012-2015 | chop_trend | team1 | 14 | 3.824 | 19 | -0.0869 | -2.093 | 1.272 | 0 |
| random-entry | passers, full | 2012-2015 | chop_trend | team2 | 14 | 5.735 | 19 | -0.1304 | -3.14 | 1.909 | 0 |
| random-entry | passers, full | 2013-2016 | allon | team1 | 119 | 13.18 | 19 | -0.5714 | -1.538 | 0.2101 | 0 |
| random-entry | passers, full | 2013-2016 | allon | team2 | 119 | 19.77 | 19 | -0.857 | -2.307 | 0.3151 | 0 |
| random-entry | passers, full | 2013-2016 | chop_trend | team1 | 42 | 10.13 | 19 | -0.1277 | -0.7015 | 1.088 | 0 |
| random-entry | passers, full | 2013-2016 | chop_trend | team2 | 42 | 15.19 | 19 | -0.1916 | -1.052 | 1.632 | 0 |
| random-entry | passers, full | 2014-2017 | allon | team1 | 21 | 8.469 | 19 | -0.03417 | -0.7733 | 0.79 | 0 |
| random-entry | passers, full | 2014-2017 | allon | team2 | 21 | 12.7 | 19 | -0.05125 | -1.16 | 1.185 | 0 |
| random-entry | passers, full | 2014-2017 | chop_trend | team1 | 16 | 6.798 | 19 | -0.0248 | -0.4521 | 0.3607 | 0 |
| random-entry | passers, full | 2014-2017 | chop_trend | team2 | 16 | 10.2 | 19 | -0.0372 | -0.6782 | 0.541 | 0 |


The real book clears its null's 95th percentile in **24 of 48** cells.


### Every member, with its settings and per-year R

All 556 rows are in `results/r2gate2/modeB_gate3_members_strict.csv`. The first 20:

| step | stream | sid | winner_index | risk_atr_len | risk_atr_mult | risk_be_pct | R_2011 | R_2012 | R_2013 | R_2014 | R_2015 | R_2016 | R_2017 | R_2018 | R_2019 | R_2020 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2011-2014 | trend-routed | adx_dmi_signals|bears_bulls_impulse_signals|variance_volume_signals|wma_baseline|adx_dmi_exit | 234 | 31 | 1 | 0.05 | 0.2241 | 0.1897 | -0.1294 | 0.1522 | 0.3722 | 0.3843 | -0.08103 | 0.03712 | 0.4434 | 0.1992 |
| 2011-2014 | trend-routed | adx_dmi_signals|schaff_trend_cycle_signals|variance_volume_signals|ema_baseline|adx_dmi_exit | 234 | 31 | 1 | 0.05 | 0.1585 | 0.2381 | 0.1123 | 0.05274 | 0.2644 | 0.3088 | 0.01635 | 0.1143 | 0.1987 | 0.07889 |
| 2011-2014 | trend-routed | aroon_signals|bears_bulls_impulse_signals|variance_volume_signals|kama_baseline|adx_dmi_exit | 249 | 31 | 1 | 0.05 | 0.1843 | 0.3048 | -0.07626 | -0.04253 | 1.085 | 0.364 | 0.03491 | 0.02553 | -0.04779 | 0.1104 |
| 2011-2014 | trend-routed | aroon_signals|bears_bulls_impulse_signals|variance_volume_signals|t3_baseline|adx_dmi_exit | 244 | 31 | 1 | 0.05 | 0.3329 | 0.1444 | 0.08446 | 0.1236 | 1.048 | 0.4071 | -0.08571 | -0.08204 | -0.06981 | 0.05799 |
| 2011-2014 | trend-routed | aroon_signals|bears_bulls_impulse_signals|variance_volume_signals|tma_baseline|adx_dmi_exit | 234 | 31 | 1 | 0.05 | 0.2121 | 0.03447 | 0.1199 | 0.08552 | 1.288 | 0.3722 | -0.1253 | -0.149 | -0.05862 | 0.09374 |
| 2011-2014 | trend-routed | aroon_signals|bears_bulls_impulse_signals|variance_volume_signals|wma_baseline|adx_dmi_exit | 234 | 31 | 1 | 0.05 | 0.2145 | 0.2871 | 0.1325 | 0.1707 | 1.13 | 0.3872 | -0.1751 | -0.07574 | -0.09707 | 0.07833 |
| 2011-2014 | trend-routed | aroon_signals|kase_peak_oscillator_signals|variance_volume_signals|kama_baseline|adx_dmi_exit | 251 | 31 | 1 | 0.05 | 0.174 | 0.1589 | -0.02922 | 0.1094 | 0.215 | 0.1659 | -0.1125 | -0.00676 | -0.138 | -0.09697 |
| 2011-2014 | trend-routed | bears_bulls_impulse_signals|center_of_gravity_signals|chaikin_volatility_volume_signals|frama_baseline|adx_dmi_exit | 244 | 31 | 1 | 0.05 | 0.05523 | 0.1592 | 0.02099 | 0.04107 | 0.7134 | 0.1638 | 0.0009815 | -0.04368 | 0.01046 | 0.09493 |
| 2011-2014 | trend-routed | bears_bulls_impulse_signals|dpo_signals|variance_volume_signals|rma_baseline|adx_dmi_exit | 225 | 31 | 1 | 0.05 | 0.1972 | -0.007502 | -0.06133 | -0.007103 | 0.7532 | 0.1644 | -0.1567 | -0.171 | 0.1616 | -0.0588 |
| 2011-2014 | trend-routed | bears_bulls_impulse_signals|dspo_signals|efficiency_ratio_volume_signals|ema_baseline|adx_dmi_exit | 46 | 48 | 1 | 0.05 | 0.3835 | 0.2886 | 0.1544 | -0.1344 | 1.488 | 0.3736 | -0.2722 | -0.06681 | 0.03308 | -0.03765 |
| 2011-2014 | trend-routed | bears_bulls_impulse_signals|dspo_signals|efficiency_ratio_volume_signals|mcginley_dynamic_index|adx_dmi_exit | 214 | 31 | 1 | 0.05 | 0.3791 | -0.0752 | 0.125 | -0.1288 | 1.887 | 0.3424 | -0.2519 | -0.0641 | -0.2517 | -0.05078 |
| 2011-2014 | trend-routed | bears_bulls_impulse_signals|dspo_signals|efficiency_ratio_volume_signals|rma_baseline|adx_dmi_exit | 214 | 31 | 1 | 0.05 | 0.3801 | -0.0752 | 0.125 | -0.1813 | 1.745 | 0.3401 | -0.2519 | -0.0641 | -0.2152 | -0.02335 |
| 2011-2014 | trend-routed | bears_bulls_impulse_signals|dspo_signals|fractal_dimension_volume_signals|frama_baseline|adx_dmi_exit | 191 | 31 | 1 | 0.05 | 0.3312 | 0.1614 | -0.02586 | -0.1423 | 1.152 | 0.1759 | -0.04236 | -0.1538 | -0.03177 | -0.03667 |
| 2011-2014 | trend-routed | bears_bulls_impulse_signals|ehlers_reverse_ema_signals|choppiness_index_volume_signals|t3_baseline|adx_dmi_exit | 204 | 31 | 1 | 0.05 | 0.4332 | 0.2233 | 0.1189 | -0.1818 | 1.522 | 0.3315 | -0.04012 | -0.1114 | 0.07356 | -0.1531 |
| 2011-2014 | trend-routed | bears_bulls_impulse_signals|ehlers_reverse_ema_signals|variance_volume_signals|tma_baseline|adx_dmi_exit | 241 | 31 | 1 | 0.05 | 0.4843 | 0.141 | 0.01226 | 0.03272 | 1.013 | 0.2047 | 0.004576 | -0.004979 | -0.3082 | 0.11 |
| 2011-2014 | trend-routed | bears_bulls_impulse_signals|fisher_transform_signals|variance_volume_signals|frama_baseline|adx_dmi_exit | 238 | 31 | 1 | 0.05 | 0.1377 | -0.01135 | -0.03456 | 0.05634 | 0.5178 | 0.2107 | -0.08747 | 0.02395 | 0.01258 | 0.01585 |
| 2011-2014 | trend-routed | bears_bulls_impulse_signals|laguerre_filter_signals|efficiency_ratio_volume_signals|ema_baseline|adx_dmi_exit | 203 | 31 | 1 | 0.05 | 0.1658 | 0.276 | 0.3142 | -0.2441 | 1.534 | 0.2351 | -0.2277 | -0.01181 | -0.07146 | -0.164 |
| 2011-2014 | trend-routed | bears_bulls_impulse_signals|laguerre_filter_signals|variance_volume_signals|wma_baseline|adx_dmi_exit | 241 | 31 | 1 | 0.05 | 0.3267 | 0.2845 | 0.05545 | 0.2078 | 0.9148 | 0.1941 | -0.1025 | -0.05271 | 0.01256 | -0.05693 |
| 2011-2014 | trend-routed | bears_bulls_impulse_signals|mama_fama_signals|fractal_dimension_volume_signals|frama_baseline|adx_dmi_exit | 191 | 31 | 1 | 0.05 | 0.3079 | 0.1513 | -0.02409 | -0.07804 | 1.068 | 0.1532 | 0.01421 | -0.1482 | -0.0679 | 0.07077 |
| 2011-2014 | trend-routed | bears_bulls_impulse_signals|mama_fama_signals|variance_volume_signals|frama_baseline|adx_dmi_exit | 238 | 31 | 1 | 0.05 | 0.2993 | 0.08908 | -0.05074 | 0.0856 | 0.3991 | 0.1819 | -0.06417 | -0.04632 | 0.03404 | -0.03091 |


## Rule `fiveyr`

Membership: cleared the bars on the FULL tune-plus-grade record, years 1-5 stitched into one block. Trades year 6, all five steps.


### Full KPI table


### TEAM 1

| KPI | ALWAYS-ON | ROUTED (chop RANGING + trend TRENDING) |
|---|---|---|
| median year | -0.78% | -0.89% |
| average year | 0.00% | -0.35% |
| worst year | -0.93% | -1.48% |
| best year | 2.90% | 1.81% |
| total 2016-2020 | 0.01% | -1.75% |
| CAGR | 0.00% | -0.35% |
| worst day | -0.64% | -0.55% |
| max drawdown | -6.95% | -6.45% |
| DIP95 (worst step) | 4.45% | 2.80% |
| Sharpe | 0.00 | -0.22 |
| Sortino | 0.00 | -0.28 |
| Calmar (total / max DD, the shipped bar) | 0.00 | -0.27 |
| Calmar (CAGR / max DD) | 0.00 | -0.05 |
| profit factor (trades, median step) | 0.95 | 0.84 |
| win rate (trades, median step) | 49.22% | 45.00% |
| positive years of 5 | 1 | 2 |
| retention (median step) | -0.13 | -0.47 |
| steps flagged FIT of 5 | 4 | 4 |

Per year:

- ALWAYS-ON: 2016: +2.90% | 2017: -0.93% | 2018: -0.91% | 2019: -0.78% | 2020: -0.27%
- ROUTED (chop RANGING + trend TRENDING): 2016: +0.17% | 2017: -1.48% | 2018: -0.89% | 2019: -1.37% | 2020: +1.81%

### TEAM 2

| KPI | ALWAYS-ON | ROUTED (chop RANGING + trend TRENDING) |
|---|---|---|
| median year | -1.17% | -1.33% |
| average year | 0.00% | -0.57% |
| worst year | -1.39% | -2.22% |
| best year | 4.35% | 2.76% |
| total 2016-2020 | 0.02% | -2.86% |
| CAGR | 0.00% | -0.57% |
| worst day | -0.96% | -0.82% |
| max drawdown | -10.43% | -9.62% |
| DIP95 (worst step) | 6.67% | 4.20% |
| Sharpe | 0.00 | -0.24 |
| Sortino | 0.00 | -0.31 |
| Calmar (total / max DD, the shipped bar) | 0.00 | -0.30 |
| Calmar (CAGR / max DD) | 0.00 | -0.06 |
| profit factor (trades, median step) | 0.95 | 0.84 |
| win rate (trades, median step) | 49.22% | 45.00% |
| positive years of 5 | 1 | 1 |
| retention (median step) | -0.13 | -0.47 |
| steps flagged FIT of 5 | 4 | 4 |

Per year:

- ALWAYS-ON: 2016: +4.35% | 2017: -1.39% | 2018: -1.36% | 2019: -1.17% | 2020: -0.41%
- ROUTED (chop RANGING + trend TRENDING): 2016: -0.01% | 2017: -2.22% | 2018: -1.33% | 2019: -2.05% | 2020: +2.76%

### Per step, as traded

| step | book | budget | size_years | trade_year | members | size_scale | scale_binds | trade_total_pct | trade_max_dd_pct | trade_dip95_pct | trade_profit_factor | trade_sortino | trade_calmar | trade_win_rate_pct | retention | FIT |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2011-2014 | allon | team1 | 2011-2015 | 2,016 | 10 | 0.8784 | DIP95 | 2.897 | 1.055 | 2.853 | 1.232 | 1.544 | 2.745 | 51.35 | 0.5468 | 0 |
| 2011-2014 | allon | team2 | 2011-2015 | 2,016 | 10 | 1.318 | DIP95 | 4.346 | 1.583 | 4.28 | 1.232 | 1.544 | 2.745 | 51.35 | 0.5468 | 0 |
| 2011-2014 | chop_trend | team1 | 2011-2015 | 2,016 | 226 | 0.5185 | DIP95 | 0.1686 | 1.328 | 2.306 | 1.023 | 0.1487 | 0.127 | 40.93 | 0.04231 | 1 |
| 2011-2014 | chop_trend | team2 | 2011-2015 | 2,016 | 226 | 0.7777 | DIP95 | -0.01405 | 1.939 | 3.463 | 0.9987 | -0.008388 | -0.00725 | 40.93 | -0.0024 | 1 |
| 2012-2015 | allon | team1 | 2012-2016 | 2,017 | 17 | 0.9059 | DIP95 | -0.9286 | 2.11 | 3.856 | 0.9288 | -0.6399 | -0.44 | 49.61 | -0.2085 | 1 |
| 2012-2015 | allon | team2 | 2012-2016 | 2,017 | 17 | 1.359 | DIP95 | -1.393 | 3.165 | 5.785 | 0.9288 | -0.6399 | -0.44 | 49.61 | -0.2085 | 1 |
| 2012-2015 | chop_trend | team1 | 2012-2016 | 2,017 | 333 | 0.4715 | DIP95 | -1.477 | 1.474 | 2.8 | 0.8148 | -1.607 | -1.002 | 46.51 | -0.6418 | 1 |
| 2012-2015 | chop_trend | team2 | 2012-2016 | 2,017 | 333 | 0.7072 | DIP95 | -2.216 | 2.212 | 4.2 | 0.8148 | -1.607 | -1.002 | 46.51 | -0.6418 | 1 |
| 2013-2016 | allon | team1 | 2013-2017 | 2,018 | 10 | 0.6777 | DIP95 | -0.9071 | 2.534 | 3.896 | 0.9327 | -0.5434 | -0.3579 | 47.88 | -0.1771 | 1 |
| 2013-2016 | allon | team2 | 2013-2017 | 2,018 | 10 | 1.017 | DIP95 | -1.361 | 3.801 | 5.843 | 0.9327 | -0.5434 | -0.3579 | 47.88 | -0.1771 | 1 |
| 2013-2016 | chop_trend | team1 | 2013-2017 | 2,018 | 197 | 0.3602 | DIP95 | -0.8882 | 1.323 | 2.224 | 0.839 | -0.7125 | -0.6714 | 53.67 | -0.4659 | 1 |
| 2013-2016 | chop_trend | team2 | 2013-2017 | 2,018 | 197 | 0.5403 | DIP95 | -1.332 | 1.984 | 3.337 | 0.839 | -0.7125 | -0.6714 | 53.67 | -0.4659 | 1 |
| 2014-2017 | allon | team1 | 2014-2018 | 2,019 | 12 | 0.8439 | DIP95 | -0.7774 | 2.311 | 4.215 | 0.9469 | -0.4311 | -0.3363 | 47.88 | -0.1325 | 1 |
| 2014-2017 | allon | team2 | 2014-2018 | 2,019 | 12 | 1.266 | DIP95 | -1.166 | 3.467 | 6.322 | 0.9469 | -0.4311 | -0.3363 | 47.88 | -0.1325 | 1 |
| 2014-2017 | chop_trend | team1 | 2014-2018 | 2,019 | 348 | 0.431 | DIP95 | -1.368 | 2.221 | 2.355 | 0.7254 | -1.329 | -0.616 | 43.95 | -0.7875 | 1 |
| 2014-2017 | chop_trend | team2 | 2014-2018 | 2,019 | 348 | 0.6465 | DIP95 | -2.052 | 3.331 | 3.532 | 0.7254 | -1.329 | -0.616 | 43.95 | -0.7875 | 1 |
| 2015-2018 | allon | team1 | 2015-2019 | 2,020 | 12 | 0.8388 | DIP95 | -0.2717 | 2.871 | 4.449 | 0.9826 | -0.1465 | -0.09462 | 49.22 | -0.06386 | 1 |
| 2015-2018 | allon | team2 | 2015-2019 | 2,020 | 12 | 1.258 | DIP95 | -0.4075 | 4.307 | 6.674 | 0.9826 | -0.1465 | -0.09462 | 49.22 | -0.06386 | 1 |
| 2015-2018 | chop_trend | team1 | 2015-2019 | 2,020 | 581 | 0.5 | DIP95 | 1.812 | 2.033 | 2.803 | 1.192 | 1.093 | 0.8915 | 45 | 0.3992 | 0 |
| 2015-2018 | chop_trend | team2 | 2015-2019 | 2,020 | 581 | 0.7501 | DIP95 | 2.756 | 3.049 | 4.18 | 1.195 | 1.115 | 0.9039 | 45 | 0.4048 | 0 |


### Against a RANDOM pick of the same size

Sizes matched per (step, stream), drawn from the strategies that have a banked winner for that cell -- the same population the rule chose from.

| step | book | budget | real | random_mean | random_min | random_max | draws | real_beats_random_mean |
|---|---|---|---|---|---|---|---|---|
| 2011-2014 | allon | team1 | 2.897 | -0.6096 | -1.074 | -0.08329 | 5 | 1 |
| 2011-2014 | allon | team2 | 4.346 | -0.9143 | -1.611 | -0.1249 | 5 | 1 |
| 2011-2014 | chop_trend | team1 | 0.1686 | -0.4116 | -1.229 | 0.1714 | 5 | 1 |
| 2011-2014 | chop_trend | team2 | -0.01405 | -0.6174 | -1.844 | 0.2572 | 5 | 1 |
| 2012-2015 | allon | team1 | -0.9286 | -1.489 | -2.49 | -0.2106 | 5 | 1 |
| 2012-2015 | allon | team2 | -1.393 | -2.233 | -3.736 | -0.3158 | 5 | 1 |
| 2012-2015 | chop_trend | team1 | -1.477 | -0.4085 | -0.6532 | -0.1888 | 5 | 0 |
| 2012-2015 | chop_trend | team2 | -2.216 | -0.6128 | -0.9798 | -0.2833 | 5 | 0 |
| 2013-2016 | allon | team1 | -0.9071 | 0.8694 | -0.1172 | 1.507 | 5 | 0 |
| 2013-2016 | allon | team2 | -1.361 | 1.304 | -0.1757 | 2.26 | 5 | 0 |
| 2013-2016 | chop_trend | team1 | -0.8882 | -0.4486 | -0.8125 | -0.2735 | 5 | 0 |
| 2013-2016 | chop_trend | team2 | -1.332 | -0.673 | -1.219 | -0.4103 | 5 | 0 |
| 2014-2017 | allon | team1 | -0.7774 | -1.289 | -2.67 | 1.09 | 5 | 1 |
| 2014-2017 | allon | team2 | -1.166 | -1.934 | -4.005 | 1.634 | 5 | 1 |
| 2014-2017 | chop_trend | team1 | -1.368 | -1.076 | -1.218 | -0.8005 | 5 | 0 |
| 2014-2017 | chop_trend | team2 | -2.052 | -1.614 | -1.827 | -1.201 | 5 | 0 |
| 2015-2018 | allon | team1 | -0.2717 | -0.5429 | -2.789 | 1.043 | 5 | 1 |
| 2015-2018 | allon | team2 | -0.4075 | -0.8144 | -4.183 | 1.565 | 5 | 1 |
| 2015-2018 | chop_trend | team1 | 1.812 | -1.335 | -1.66 | -0.6488 | 5 | 1 |
| 2015-2018 | chop_trend | team2 | 2.756 | -2.003 | -2.49 | -0.9731 | 5 | 1 |


The real book beats the random pick's mean in **12 of 20** (step, book, budget) cells.


### Its three nulls

| null | scope | step | book | budget | members | real | n_draws | null_mean | null_p5 | null_p95 | p_one_sided |
|---|---|---|---|---|---|---|---|---|---|---|---|
| identity | full field | 2011-2014 | allon | team1 |  | 2.897 | 200 | 6.218 | 2.897 | 14.34 | 1 |
| identity | full field | 2011-2014 | allon | team2 |  | 4.346 | 200 | 9.656 | 4.346 | 21.51 | 1 |
| identity | full field | 2011-2014 | chop_trend | team1 |  | 0.1686 | 200 | 5.02 | 0.1686 | 14.76 | 1 |
| identity | full field | 2011-2014 | chop_trend | team2 |  | -0.01405 | 200 | 8.765 | -0.01405 | 22.14 | 1 |
| identity | full field | 2012-2015 | allon | team1 |  | -0.9286 | 200 | 4.897 | -0.9286 | 14.1 | 0.81 |
| identity | full field | 2012-2015 | allon | team2 |  | -1.393 | 200 | 8.098 | -1.393 | 21.15 | 1 |
| identity | full field | 2012-2015 | chop_trend | team1 |  | -1.477 | 200 | 4.063 | -1.477 | 19.1 | 0.84 |
| identity | full field | 2012-2015 | chop_trend | team2 |  | -2.216 | 200 | 6.457 | -2.216 | 28.65 | 1 |
| identity | full field | 2013-2016 | allon | team1 |  | -0.9071 | 200 | 4.956 | -0.9071 | 13.75 | 0.865 |
| identity | full field | 2013-2016 | allon | team2 |  | -1.361 | 200 | 7.445 | -1.361 | 20.62 | 1 |
| identity | full field | 2013-2016 | chop_trend | team1 |  | -0.8882 | 200 | 3.385 | -0.8882 | 21.55 | 1 |
| identity | full field | 2013-2016 | chop_trend | team2 |  | -1.332 | 200 | 5.955 | -1.332 | 32.33 | 0.78 |
| identity | full field | 2014-2017 | allon | team1 |  | -0.7774 | 200 | 5.145 | -0.7774 | 17.03 | 0.775 |
| identity | full field | 2014-2017 | allon | team2 |  | -1.166 | 200 | 8.256 | -1.166 | 25.55 | 0.78 |
| identity | full field | 2014-2017 | chop_trend | team1 |  | -1.368 | 200 | 7.049 | -1.368 | 29.72 | 1 |
| identity | full field | 2014-2017 | chop_trend | team2 |  | -2.052 | 200 | 9.217 | -2.052 | 44.58 | 1 |
| identity | full field | 2015-2018 | allon | team1 |  | -0.2717 | 200 | 6.772 | -0.2717 | 14.67 | 0.845 |
| identity | full field | 2015-2018 | allon | team2 |  | -0.4075 | 200 | 10.05 | -0.4075 | 22 | 0.84 |
| identity | full field | 2015-2018 | chop_trend | team1 |  | 1.812 | 200 | 7.762 | -0.5085 | 37.21 | 0.7 |
| identity | full field | 2015-2018 | chop_trend | team2 |  | 2.756 | 200 | 12.6 | -0.7702 | 55.72 | 0.65 |
| shuffle | passers, full | 2011-2014 | allon | team1 | 10 | 2.897 | 19 | 2.897 | 2.897 | 2.897 | 1 |
| shuffle | passers, full | 2011-2014 | allon | team2 | 10 | 4.346 | 19 | 4.346 | 4.346 | 4.346 | 1 |
| shuffle | passers, full | 2011-2014 | chop_trend | team1 | 226 | 0.1686 | 19 | -0.11 | -1.092 | 0.6514 | 0.3684 |
| shuffle | passers, full | 2011-2014 | chop_trend | team2 | 226 | -0.01405 | 19 | -0.165 | -1.638 | 0.9771 | 0.5263 |
| shuffle | passers, full | 2012-2015 | allon | team1 | 17 | -0.9286 | 19 | -0.9286 | -0.9286 | -0.9286 | 1 |
| shuffle | passers, full | 2012-2015 | allon | team2 | 17 | -1.393 | 19 | -1.393 | -1.393 | -1.393 | 1 |
| shuffle | passers, full | 2012-2015 | chop_trend | team1 | 333 | -1.477 | 19 | -1.053 | -1.953 | -0.4408 | 0.7895 |
| shuffle | passers, full | 2012-2015 | chop_trend | team2 | 333 | -2.216 | 19 | -1.579 | -2.93 | -0.6611 | 0.7895 |
| shuffle | passers, full | 2013-2016 | allon | team1 | 10 | -0.9071 | 19 | -0.9071 | -0.9071 | -0.9071 | 1 |
| shuffle | passers, full | 2013-2016 | allon | team2 | 10 | -1.361 | 19 | -1.361 | -1.361 | -1.361 | 1 |
| shuffle | passers, full | 2013-2016 | chop_trend | team1 | 197 | -0.8882 | 19 | -0.2623 | -0.9556 | 0.4563 | 0.8421 |
| shuffle | passers, full | 2013-2016 | chop_trend | team2 | 197 | -1.332 | 19 | -0.3935 | -1.433 | 0.6845 | 0.8421 |
| shuffle | passers, full | 2014-2017 | allon | team1 | 12 | -0.7774 | 19 | -0.7774 | -0.7774 | -0.7774 | 1 |
| shuffle | passers, full | 2014-2017 | allon | team2 | 12 | -1.166 | 19 | -1.166 | -1.166 | -1.166 | 1 |
| shuffle | passers, full | 2014-2017 | chop_trend | team1 | 348 | -1.368 | 19 | -1.186 | -1.996 | -0.5424 | 0.6842 |
| shuffle | passers, full | 2014-2017 | chop_trend | team2 | 348 | -2.052 | 19 | -1.779 | -2.994 | -0.8136 | 0.6842 |
| shuffle | passers, full | 2015-2018 | allon | team1 | 12 | -0.2717 | 19 | -0.2717 | -0.2717 | -0.2717 | 1 |
| shuffle | passers, full | 2015-2018 | allon | team2 | 12 | -0.4075 | 19 | -0.4075 | -0.4075 | -0.4075 | 1 |
| shuffle | passers, full | 2015-2018 | chop_trend | team1 | 581 | 1.812 | 19 | -0.1436 | -0.9418 | 0.5682 | 0 |
| shuffle | passers, full | 2015-2018 | chop_trend | team2 | 581 | 2.756 | 19 | -0.2155 | -1.413 | 0.8523 | 0 |
| random-entry | passers, full | 2011-2014 | allon | team1 | 10 | 2.897 | 19 | -0.2799 | -2.211 | 1.486 | 0 |
| random-entry | passers, full | 2011-2014 | allon | team2 | 10 | 4.346 | 19 | -0.4198 | -3.317 | 2.229 | 0 |
| random-entry | passers, full | 2011-2014 | chop_trend | team1 | 226 | 0.1686 | 19 | -0.2702 | -2.332 | 2.817 | 0.3684 |
| random-entry | passers, full | 2011-2014 | chop_trend | team2 | 226 | -0.01405 | 19 | -0.4053 | -3.498 | 4.225 | 0.3684 |
| random-entry | passers, full | 2012-2015 | allon | team1 | 17 | -0.9286 | 19 | -0.3412 | -1.378 | 0.7077 | 0.7368 |
| random-entry | passers, full | 2012-2015 | allon | team2 | 17 | -1.393 | 19 | -0.5118 | -2.067 | 1.062 | 0.7368 |
| random-entry | passers, full | 2012-2015 | chop_trend | team1 | 333 | -1.477 | 19 | -0.04329 | -1.356 | 1.325 | 0.9474 |
| random-entry | passers, full | 2012-2015 | chop_trend | team2 | 333 | -2.216 | 19 | -0.06494 | -2.034 | 1.987 | 0.9474 |
| random-entry | passers, full | 2013-2016 | allon | team1 | 10 | -0.9071 | 19 | 0.01579 | -0.9018 | 0.4445 | 1 |
| random-entry | passers, full | 2013-2016 | allon | team2 | 10 | -1.361 | 19 | 0.02368 | -1.353 | 0.6668 | 1 |
| random-entry | passers, full | 2013-2016 | chop_trend | team1 | 197 | -0.8882 | 19 | -0.5919 | -1.99 | 0.5391 | 0.6316 |
| random-entry | passers, full | 2013-2016 | chop_trend | team2 | 197 | -1.332 | 19 | -0.8879 | -2.984 | 0.8087 | 0.6316 |
| random-entry | passers, full | 2014-2017 | allon | team1 | 12 | -0.7774 | 19 | -0.2969 | -0.9067 | 0.4242 | 0.8421 |
| random-entry | passers, full | 2014-2017 | allon | team2 | 12 | -1.166 | 19 | -0.4453 | -1.36 | 0.6363 | 0.8421 |
| random-entry | passers, full | 2014-2017 | chop_trend | team1 | 348 | -1.368 | 19 | -0.2389 | -1.26 | 0.4684 | 0.9474 |
| random-entry | passers, full | 2014-2017 | chop_trend | team2 | 348 | -2.052 | 19 | -0.3583 | -1.889 | 0.7026 | 0.9474 |
| random-entry | passers, full | 2015-2018 | allon | team1 | 12 | -0.2717 | 19 | -0.2569 | -2.203 | 1.085 | 0.7895 |
| random-entry | passers, full | 2015-2018 | allon | team2 | 12 | -0.4075 | 19 | -0.3854 | -3.305 | 1.628 | 0.7895 |
| random-entry | passers, full | 2015-2018 | chop_trend | team1 | 581 | 1.812 | 19 | -0.6664 | -1.657 | 0.1935 | 0 |
| random-entry | passers, full | 2015-2018 | chop_trend | team2 | 581 | 2.756 | 19 | -0.9996 | -2.485 | 0.2902 | 0 |


The real book clears its null's 95th percentile in **6 of 60** cells.


### Every member, with its settings and per-year R

All 1,748 rows are in `results/r2gate2/modeB_gate3_members_fiveyr.csv`. The first 20:

| step | stream | sid | winner_index | risk_atr_len | risk_atr_mult | risk_be_pct | R_2011 | R_2012 | R_2013 | R_2014 | R_2015 | R_2016 | R_2017 | R_2018 | R_2019 | R_2020 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2011-2014 | trend-routed | aroon_signals|relative_vigor_index_signals|variance_volume_signals|mcginley_dynamic_index|adx_dmi_exit | 235 | 31 | 1 | 0.05 | 0.2725 | 0.0736 | 0.2923 | 2.155 | 0.2235 | -0.1159 | -0.08065 | 0.1153 | -0.332 | -0.1354 |
| 2011-2014 | trend-routed | center_of_gravity_signals|chandelier_exit_signals|variance_volume_signals|t3_baseline|adx_dmi_exit | 228 | 31 | 1 | 0.05 | 0.2 | 0.4288 | 0.1107 | 0.1567 | 1.276 | 0.006923 | -0.2372 | 0.2103 | 0.1161 | -0.06533 |
| 2011-2014 | trend-routed | center_of_gravity_signals|dspo_signals|variance_volume_signals|wma_baseline|adx_dmi_exit | 253 | 31 | 1 | 0.05 | 0.3839 | 0.1572 | 0.0546 | 0.2389 | 1.06 | 0.0513 | -0.1081 | 0.005034 | -0.2049 | -0.003281 |
| 2011-2014 | trend-routed | center_of_gravity_signals|laguerre_filter_signals|variance_volume_signals|t3_baseline|adx_dmi_exit | 228 | 31 | 1 | 0.05 | 0.1644 | 0.411 | 0.179 | 0.2081 | 1.853 | -0.09472 | -0.1906 | 0.2138 | -0.06902 | -0.2489 |
| 2011-2014 | trend-routed | center_of_gravity_signals|relative_vigor_index_signals|variance_volume_signals|frama_baseline|adx_dmi_exit | 246 | 31 | 1 | 0.05 | 0.3194 | 0.1655 | 0.06473 | 2.043 | 0.2063 | 0.1108 | 0.1065 | 0.1217 | -0.03048 | -0.1174 |
| 2011-2014 | trend-routed | center_of_gravity_signals|schaff_trend_cycle_signals|variance_volume_signals|alma_baseline|adx_dmi_exit | 241 | 31 | 1 | 0.05 | 0.1343 | 0.1958 | 0.1688 | 0.113 | 1.059 | 0.2638 | 0.05146 | 0.02203 | 0.04792 | 0.09321 |
| 2011-2014 | trend-routed | center_of_gravity_signals|supertrend_signals|variance_volume_signals|t3_baseline|adx_dmi_exit | 228 | 31 | 1 | 0.05 | 0.1268 | 0.4115 | 0.2865 | 0.2329 | 1.345 | 0.002408 | -0.1298 | 0.1372 | 0.1432 | -0.1005 |
| 2011-2014 | trend-routed | center_of_gravity_signals|supertrend_signals|variance_volume_signals|tma_baseline|adx_dmi_exit | 241 | 31 | 1 | 0.05 | 0.2204 | 0.337 | 0.3684 | 0.2679 | 1.632 | -0.07976 | 0.06469 | 0.01501 | -0.0596 | 0.003236 |
| 2011-2014 | trend-routed | center_of_gravity_signals|volatility_quality_signals|variance_volume_signals|t3_baseline|adx_dmi_exit | 228 | 31 | 1 | 0.05 | 0.08595 | 0.4016 | 0.1811 | 0.05709 | 1.247 | 0.00667 | -0.1192 | 0.01464 | -0.03676 | -0.1512 |
| 2011-2014 | trend-routed | coppock_curve_signals|center_of_gravity_signals|choppiness_index_volume_signals|sma_baseline|adx_dmi_exit | 204 | 31 | 1 | 0.05 | 0.1427 | 0.2877 | 0.2472 | 0.09187 | 3.155 | -0.0009546 | 0.186 | 0.01616 | -0.1073 | -0.2679 |
| 2011-2014 | trend-routed | coppock_curve_signals|center_of_gravity_signals|choppiness_index_volume_signals|wma_baseline|adx_dmi_exit | 204 | 31 | 1 | 0.05 | 0.1406 | 0.2697 | 0.3198 | 0.07533 | 2.565 | 0.1269 | 0.04072 | -0.02186 | -0.2269 | -0.247 |
| 2011-2014 | trend-routed | coppock_curve_signals|fx_sniper_ergodic_cci_signals|variance_volume_signals|super_smoother_2pole_baseline|adx_dmi_exit | 229 | 31 | 1 | 0.05 | -0.02116 | 0.3076 | 0.05733 | 0.2271 | 1.084 | 0.1928 | -0.07839 | -0.05339 | 0.06653 | -0.03887 |
| 2011-2014 | trend-routed | coppock_curve_signals|fx_sniper_ergodic_cci_signals|variance_volume_signals|t3_baseline|adx_dmi_exit | 236 | 31 | 1 | 0.05 | 0.03497 | 0.3467 | 0.1719 | 0.3105 | 1.003 | 0.2307 | -0.03396 | 0.005768 | 0.09581 | 0.01029 |
| 2011-2014 | trend-routed | coppock_curve_signals|kalman_filter_signals|variance_volume_signals|tma_baseline|adx_dmi_exit | 275 | 31 | 1 | 0.05 | 0.1903 | 0.4298 | 0.3367 | 0.2365 | 0.9012 | 0.2371 | -0.04773 | -0.01952 | 0.0904 | 0.007916 |
| 2011-2014 | trend-routed | coppock_curve_signals|schaff_trend_cycle_signals|variance_volume_signals|mcginley_dynamic_index|adx_dmi_exit | 307 | 31 | 1 | 0.05 | 0.1091 | 0.2184 | 0.2977 | 0.2819 | 1.241 | 0.2075 | -0.08051 | 0.1224 | -0.2219 | 0.02669 |
| 2011-2014 | trend-routed | coppock_curve_signals|schaff_trend_cycle_signals|variance_volume_signals|tma_baseline|adx_dmi_exit | 267 | 31 | 1 | 0.05 | 0.1903 | 0.3476 | 0.3356 | 0.2039 | 0.9952 | 0.2741 | -0.03175 | -0.052 | 0.213 | 0.08579 |
| 2011-2014 | trend-routed | coppock_curve_signals|ssl_channel_signals|variance_volume_signals|t3_baseline|adx_dmi_exit | 236 | 31 | 1 | 0.05 | 0.1712 | 0.3206 | 0.2737 | 0.202 | 0.8046 | 0.2235 | -0.0325 | 0.07047 | 0.184 | 0.2269 |
| 2011-2014 | trend-routed | coppock_curve_signals|ssl_channel_signals|variance_volume_signals|tma_baseline|adx_dmi_exit | 217 | 31 | 1 | 0.05 | 0.09457 | 0.2534 | 0.7869 | 0.07088 | 1.613 | 0.1486 | -0.2418 | 0.1324 | 0.1782 | 0.1791 |
| 2011-2014 | trend-routed | coppock_curve_signals|trend_direction_force_index_signals|variance_volume_signals|ema_baseline|adx_dmi_exit | 267 | 31 | 1 | 0.05 | 0.04139 | 0.2357 | 0.02447 | 0.3403 | 1.194 | 0.1799 | 0.07734 | 0.1319 | -0.1275 | 0.2817 |
| 2011-2014 | trend-routed | coppock_curve_signals|trend_direction_force_index_signals|variance_volume_signals|tma_baseline|adx_dmi_exit | 267 | 31 | 1 | 0.05 | 0.3935 | 0.4165 | 0.1063 | 0.3738 | 1.304 | 0.2099 | 0.05445 | -0.2205 | 0.2129 | 0.3103 |


## Provenance

| file | rows | md5 |
|---|---|---|
| `results/r2gate2/modeB_gate3_passersbook.csv` | 20 | 292d1372ad09 |
| `results/r2gate2/modeB_gate3_passersbook_nulls.csv` | 60 | 00aad9f58c6a |
| `results/r2gate2/modeB_gate3_randompick.csv` | 100 | 077fae43c22e |
| `results/r2gate2/modeB_gate3_members.csv` | 56,617 | 5a6c4ef96642 |
| `results/r2gate2/modeB_gate3_passersbook_strict.csv` | 16 | 2fb75c3ad7e8 |
| `results/r2gate2/modeB_gate3_passersbook_strict_nulls.csv` | 48 | e4a065947292 |
| `results/r2gate2/modeB_gate3_randompick_strict.csv` | 80 | 8c0003ebc126 |
| `results/r2gate2/modeB_gate3_members_strict.csv` | 556 | 0698f944ae2a |
| `results/r2gate2/modeB_gate3_passersbook_fiveyr.csv` | 20 | de39bfbcf29b |
| `results/r2gate2/modeB_gate3_passersbook_fiveyr_nulls.csv` | 60 | f2331025f61b |
| `results/r2gate2/modeB_gate3_randompick_fiveyr.csv` | 100 | c661def1e331 |
| `results/r2gate2/modeB_gate3_members_fiveyr.csv` | 1,748 | 076963908de5 |
