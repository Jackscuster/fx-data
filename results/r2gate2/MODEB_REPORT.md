# MODE B — THE HONEST GATE 2, ALL 273,780 STRATEGIES

Generated 2026-11-19 19:22 by `code/l2r2modearep.py`. **Every number below was read out of a file in this run and the file is named beside it.** A section whose source is missing says so and is left empty.


## The files this report is built from

| section | file | rows | md5 | mtime |
|---|---|---|---|---|
| books | results/r2gate2/modeB_books_full.csv | 40 | 8a753619cf2b | 2026-11-19 18:44 |
| nulls | results/r2gate2/modeB_books_nulls.csv | 200 | eb9232beeb7d | 2026-11-19 19:02 |
| grade | results/r2gate2/modeB_books_blindgrade.csv | 20 | 3383fb5a2dfd | 2026-11-19 19:02 |
| splits | results/r2gate2/modeB_books_layer1splits.csv | 55 | 7995f349ff5e | 2026-11-19 19:12 |
| gate1 | results/r2gate1_pooled_modeB_full.csv | 480 | 248c7d8a1494 | 2026-11-16 18:51 |
| rankcorr | results/r2gate1_rankcorr_modeB_full.csv | 20 | 56c33e723315 | 2026-11-16 18:51 |
| grid | results/r2gate2_grid.csv | 6 | 85045a1adf2e | 2026-11-17 09:57 |
| shuffle1 | results/r2gate1_shufflenull_modeB.csv | 16 | 90eee2643a99 | 2026-11-16 18:55 |
| manifest | results/layer1_interface_manifest_2026-11-16.csv | 16 | f6582570eeb5 | 2026-11-16 14:19 |


**Missing sources, left empty rather than filled in:** cond1, cond2, streamed


## What was run, and what was not cut

Gate 1 cut nothing (Jack, 16 Nov): every combination the enumeration produced went to gate 2 tuning. Mode A is **273,780** strategies, each scored over its full axial configuration set at defaults-plus-every-single-knob-deviation, with the cut reading tune years only and grade and trade years banked but never consulted while picking.


The declared risk grid, from `results/r2gate2_grid.csv`:

| knob | n_values | lo | hi | in_trend | in_chop |
|---|---|---|---|---|---|
| atr_len | 49 | 2 | 50 | 1 | 1 |
| atr_mult (stop) | 31 | 1 | 1.5 | 1 | 1 |
| tp_mult | 41 | 1 | 3 | 1 | 1 |
| be_pct | 20 | 0.01 | 0.2 | 1 | 0 |
| trail_arm | 21 | 1 | 2 | 1 | 0 |
| trail_mult | 31 | 0.5 | 2 | 1 | 0 |


## The two conditions that gated the run


## THE FOUR BOOKS

From `results/r2gate2/modeB_books_full.csv`, 40 rows = 5 steps x 4 books x 2 budgets.


### Trade-year median, by book and budget, pooled over the five steps

| book | budget | steps | median_of_trade_medians | worst_step | best_step | median_dip95 | median_PF | median_retention | steps_flagged_FIT |
|---|---|---|---|---|---|---|---|---|---|
| allon | team1 | 5 | -0.6939 | -4.218 | 0.4863 | 4.208 | 0.9496 | -0.1565 | 5 |
| allon | team2 | 5 | -1.041 | -6.327 | 0.7294 | 6.312 | 0.9496 | -0.1565 | 5 |
| chop_notrange | team1 | 5 | -1.471 | -2.567 | -0.334 | 2.319 | 0.8257 | -0.9356 | 5 |
| chop_notrange | team2 | 5 | -2.206 | -3.851 | -0.501 | 3.479 | 0.8257 | -0.9356 | 5 |
| chop_trend | team1 | 5 | -1.454 | -2.06 | 0.2246 | 2.956 | 0.847 | -0.8128 | 4 |
| chop_trend | team2 | 5 | -2.181 | -3.089 | 0.3369 | 4.434 | 0.847 | -0.8128 | 4 |
| chop_ungated | team1 | 5 | -0.5857 | -2.333 | 0.3513 | 2.799 | 0.9278 | -0.5024 | 4 |
| chop_ungated | team2 | 5 | -0.8785 | -3.499 | 0.527 | 4.198 | 0.9278 | -0.5024 | 4 |


### Every step, every book, team1 budget

| step | book | size_scale | scale_binds | build_median_year_pct | trade_median_year_pct | trade_dip95_pct | trade_max_dd_pct | trade_profit_factor | retention | FIT |
|---|---|---|---|---|---|---|---|---|---|---|
| 2011-2014 | allon | 0.6378 | DIP95 | 4.433 | -0.6939 | 4.208 | 2.548 | 0.9496 | -0.1565 | 1 |
| 2011-2014 | chop_notrange | 0.6132 | DIP95 | 3.968 | -2.567 | 4.36 | 3.77 | 0.7782 | -0.647 | 1 |
| 2011-2014 | chop_trend | 0.5738 | DIP95 | 4.413 | -1.454 | 3.91 | 2.911 | 0.8812 | -0.3295 | 1 |
| 2011-2014 | chop_ungated | 0.6077 | DIP95 | 2.434 | -1.763 | 3.735 | 3.075 | 0.843 | -0.7245 | 1 |
| 2012-2015 | allon | 0.5801 | DIP95 | 4.615 | -0.1817 | 2.942 | 1.817 | 0.9838 | -0.03937 | 1 |
| 2012-2015 | chop_notrange | 0.5092 | DIP95 | 2.674 | -1.501 | 2.849 | 1.523 | 0.8257 | -0.5613 | 1 |
| 2012-2015 | chop_trend | 0.4381 | DIP95 | 2.534 | -2.06 | 3.406 | 1.994 | 0.7771 | -0.8128 | 1 |
| 2012-2015 | chop_ungated | 0.4639 | DIP95 | 1.809 | -0.5653 | 2.799 | 1.268 | 0.9417 | -0.3126 | 1 |
| 2013-2016 | allon | 0.4519 | DIP95 | 3.359 | 0.4863 | 2.288 | 1.316 | 1.054 | 0.1448 | 1 |
| 2013-2016 | chop_notrange | 0.3927 | DIP95 | 0.357 | -0.334 | 2.058 | 1.158 | 0.9538 | -0.9356 | 1 |
| 2013-2016 | chop_trend | 0.3818 | DIP95 | 1.05 | 0.2246 | 1.585 | 0.8615 | 1.035 | 0.2139 | 0 |
| 2013-2016 | chop_ungated | 0.3785 | DIP95 | 0.2388 | 0.3513 | 1.811 | 1.511 | 1.049 | 1.471 | 0 |
| 2014-2017 | allon | 0.5476 | DIP95 | 2.449 | -4.218 | 5.651 | 4.398 | 0.676 | -1.723 | 1 |
| 2014-2017 | chop_notrange | 0.3768 | DIP95 | 0.1141 | -1.471 | 2.319 | 1.464 | 0.7624 | -12.9 | 1 |
| 2014-2017 | chop_trend | 0.3144 | DIP95 | 0.2063 | -1.698 | 2.58 | 2.049 | 0.7314 | -8.227 | 1 |
| 2014-2017 | chop_ungated | 0.4013 | DIP95 | 0.7488 | -2.333 | 3.632 | 2.53 | 0.7543 | -3.116 | 1 |
| 2015-2018 | allon | 0.4493 | DIP95 | 2.328 | -2.571 | 4.479 | 3.298 | 0.7758 | -1.105 | 1 |
| 2015-2018 | chop_notrange | 0.3149 | DIP95 | 0.02999 | -0.3604 | 2.163 | 1.339 | 0.9446 | -12.02 | 1 |
| 2015-2018 | chop_trend | 0.3672 | DIP95 | 0.5129 | -1.301 | 2.956 | 2.081 | 0.847 | -2.537 | 1 |
| 2015-2018 | chop_ungated | 0.394 | DIP95 | 1.166 | -0.5857 | 2.495 | 2.493 | 0.9278 | -0.5024 | 1 |


## THE THREE NULLS

From `results/r2gate2/modeB_books_nulls.csv`, 200 rows.


### identity

| scope | step | book | budget | members | real | n_draws | null_mean | null_p5 | null_p95 | p_one_sided |
|---|---|---|---|---|---|---|---|---|---|---|
| full field | 2011-2014 | allon | team1 |  | -0.6939 | 200 | 4.088 | -0.6939 | 10.43 | 1 |
| full field | 2011-2014 | allon | team2 |  | -1.041 | 200 | 6.765 | -1.041 | 15.64 | 0.815 |
| full field | 2011-2014 | chop_notrange | team1 |  | -2.567 | 200 | 2.45 | -2.567 | 7.081 | 1 |
| full field | 2011-2014 | chop_notrange | team2 |  | -3.851 | 200 | 4.124 | -3.851 | 10.62 | 0.825 |
| full field | 2011-2014 | chop_trend | team1 |  | -1.454 | 200 | 3.721 | -1.454 | 6.528 | 1 |
| full field | 2011-2014 | chop_trend | team2 |  | -2.181 | 200 | 4.312 | -2.181 | 9.792 | 1 |
| full field | 2011-2014 | chop_ungated | team1 |  | -1.763 | 200 | 1.849 | -1.763 | 5.072 | 1 |
| full field | 2011-2014 | chop_ungated | team2 |  | -2.645 | 200 | 2.996 | -2.645 | 7.608 | 1 |
| full field | 2012-2015 | allon | team1 |  | -0.1817 | 200 | 2.895 | -0.881 | 8.074 | 0.845 |
| full field | 2012-2015 | allon | team2 |  | -0.2725 | 200 | 5.003 | -1.322 | 12.11 | 0.815 |
| full field | 2012-2015 | chop_notrange | team1 |  | -1.501 | 200 | 1.487 | -1.563 | 4.647 | 0.815 |
| full field | 2012-2015 | chop_notrange | team2 |  | -2.251 | 200 | 2.193 | -2.345 | 6.97 | 0.84 |
| full field | 2012-2015 | chop_trend | team1 |  | -2.06 | 200 | 1.215 | -2.06 | 4.974 | 1 |
| full field | 2012-2015 | chop_trend | team2 |  | -3.089 | 200 | 1.583 | -3.089 | 7.462 | 1 |
| full field | 2012-2015 | chop_ungated | team1 |  | -0.5653 | 200 | 1.825 | -1.595 | 5.461 | 0.66 |
| full field | 2012-2015 | chop_ungated | team2 |  | -0.8479 | 200 | 2.638 | -2.392 | 8.191 | 0.685 |
| full field | 2013-2016 | allon | team1 |  | 0.4863 | 200 | 2.413 | -1.303 | 5.629 | 0.655 |
| full field | 2013-2016 | allon | team2 |  | 0.7294 | 200 | 3.538 | -1.954 | 8.444 | 0.675 |
| full field | 2013-2016 | chop_notrange | team1 |  | -0.334 | 200 | 0.8645 | -0.7818 | 3.476 | 0.845 |
| full field | 2013-2016 | chop_notrange | team2 |  | -0.501 | 200 | 1.316 | -1.173 | 5.214 | 0.83 |
| full field | 2013-2016 | chop_trend | team1 |  | 0.2246 | 200 | 1.286 | -1.26 | 5.849 | 0.635 |
| full field | 2013-2016 | chop_trend | team2 |  | 0.3369 | 200 | 2.462 | -1.889 | 8.774 | 0.68 |
| full field | 2013-2016 | chop_ungated | team1 |  | 0.3513 | 200 | 0.9943 | -0.6931 | 4.684 | 0.505 |
| full field | 2013-2016 | chop_ungated | team2 |  | 0.527 | 200 | 1.511 | -1.04 | 7.026 | 0.315 |
| full field | 2014-2017 | allon | team1 |  | -4.218 | 200 | 2.58 | -4.218 | 6.866 | 1 |
| full field | 2014-2017 | allon | team2 |  | -6.327 | 200 | 3.12 | -6.327 | 10.3 | 1 |
| full field | 2014-2017 | chop_notrange | team1 |  | -1.471 | 200 | 0.3228 | -1.471 | 3.257 | 0.85 |
| full field | 2014-2017 | chop_notrange | team2 |  | -2.206 | 200 | 0.6691 | -2.206 | 4.885 | 1 |
| full field | 2014-2017 | chop_trend | team1 |  | -1.698 | 200 | 0.5645 | -1.698 | 5.238 | 1 |
| full field | 2014-2017 | chop_trend | team2 |  | -2.546 | 200 | 0.8341 | -2.546 | 7.856 | 1 |
| full field | 2014-2017 | chop_ungated | team1 |  | -2.333 | 200 | 0.7352 | -2.333 | 4.488 | 1 |
| full field | 2014-2017 | chop_ungated | team2 |  | -3.499 | 200 | 1.255 | -3.499 | 6.732 | 1 |
| full field | 2015-2018 | allon | team1 |  | -2.571 | 200 | 1.579 | -3.312 | 6.898 | 0.89 |
| full field | 2015-2018 | allon | team2 |  | -3.857 | 200 | 1.688 | -4.968 | 10.35 | 0.82 |
| full field | 2015-2018 | chop_notrange | team1 |  | -0.3604 | 200 | 0.3753 | -1.963 | 3.337 | 0.695 |
| full field | 2015-2018 | chop_notrange | team2 |  | -0.5407 | 200 | 0.3639 | -2.944 | 5.006 | 0.655 |
| full field | 2015-2018 | chop_trend | team1 |  | -1.301 | 200 | 0.9051 | -2.15 | 5.361 | 0.67 |
| full field | 2015-2018 | chop_trend | team2 |  | -1.952 | 200 | 1.495 | -3.224 | 8.042 | 0.84 |
| full field | 2015-2018 | chop_ungated | team1 |  | -0.5857 | 200 | 1.036 | -2.062 | 5.028 | 0.805 |
| full field | 2015-2018 | chop_ungated | team2 |  | -0.8785 | 200 | 1.483 | -3.092 | 7.542 | 0.805 |


### random-entry

| scope | step | book | budget | members | real | n_draws | null_mean | null_p5 | null_p95 | p_one_sided |
|---|---|---|---|---|---|---|---|---|---|---|
| sample 20000 | 2011-2014 | allon | team1 | 2e+04 | -0.801 | 19 | -0.7977 | -2.677 | 1.089 | 0.4737 |
| sample 20000 | 2011-2014 | allon | team2 | 2e+04 | -1.202 | 19 | -1.197 | -4.016 | 1.633 | 0.4737 |
| sample 20000 | 2011-2014 | chop_notrange | team1 | 2e+04 | -2.561 | 19 | -0.7461 | -2.627 | 0.8668 | 0.9474 |
| sample 20000 | 2011-2014 | chop_notrange | team2 | 2e+04 | -3.841 | 19 | -1.119 | -3.94 | 1.3 | 0.9474 |
| sample 20000 | 2011-2014 | chop_trend | team1 | 2e+04 | -1.086 | 19 | -0.5583 | -2.265 | 1.375 | 0.6316 |
| sample 20000 | 2011-2014 | chop_trend | team2 | 2e+04 | -1.629 | 19 | -0.8374 | -3.397 | 2.062 | 0.6316 |
| sample 20000 | 2011-2014 | chop_ungated | team1 | 2e+04 | -1.845 | 19 | -0.5554 | -2.349 | 0.7938 | 0.8947 |
| sample 20000 | 2011-2014 | chop_ungated | team2 | 2e+04 | -2.768 | 19 | -0.8331 | -3.524 | 1.191 | 0.8947 |
| sample 20000 | 2012-2015 | allon | team1 | 2e+04 | -0.1338 | 19 | -0.1894 | -1.55 | 1.573 | 0.5789 |
| sample 20000 | 2012-2015 | allon | team2 | 2e+04 | -0.2007 | 19 | -0.284 | -2.325 | 2.359 | 0.5789 |
| sample 20000 | 2012-2015 | chop_notrange | team1 | 2e+04 | -1.516 | 19 | -0.2405 | -1.543 | 1.506 | 0.9474 |
| sample 20000 | 2012-2015 | chop_notrange | team2 | 2e+04 | -2.274 | 19 | -0.3607 | -2.315 | 2.259 | 0.9474 |
| sample 20000 | 2012-2015 | chop_trend | team1 | 2e+04 | -2.013 | 19 | -0.6876 | -1.514 | 0.5751 | 1 |
| sample 20000 | 2012-2015 | chop_trend | team2 | 2e+04 | -3.019 | 19 | -1.031 | -2.271 | 0.8626 | 1 |
| sample 20000 | 2012-2015 | chop_ungated | team1 | 2e+04 | -0.7672 | 19 | -0.3249 | -1.196 | 0.8435 | 0.7895 |
| sample 20000 | 2012-2015 | chop_ungated | team2 | 2e+04 | -1.151 | 19 | -0.4873 | -1.794 | 1.265 | 0.7895 |
| sample 20000 | 2013-2016 | allon | team1 | 2e+04 | 0.2053 | 19 | -0.438 | -2.039 | 0.9956 | 0.2105 |
| sample 20000 | 2013-2016 | allon | team2 | 2e+04 | 0.3079 | 19 | -0.657 | -3.059 | 1.493 | 0.2105 |
| sample 20000 | 2013-2016 | chop_notrange | team1 | 2e+04 | -0.3322 | 19 | -0.09167 | -1.149 | 1.523 | 0.6842 |
| sample 20000 | 2013-2016 | chop_notrange | team2 | 2e+04 | -0.4983 | 19 | -0.1375 | -1.724 | 2.284 | 0.6842 |
| sample 20000 | 2013-2016 | chop_trend | team1 | 2e+04 | 0.3128 | 19 | -0.4035 | -1.649 | 0.6075 | 0.1579 |
| sample 20000 | 2013-2016 | chop_trend | team2 | 2e+04 | 0.4692 | 19 | -0.6053 | -2.473 | 0.9113 | 0.1579 |
| sample 20000 | 2013-2016 | chop_ungated | team1 | 2e+04 | 0.4281 | 19 | -0.4974 | -1.76 | 1.094 | 0.1579 |
| sample 20000 | 2013-2016 | chop_ungated | team2 | 2e+04 | 0.6421 | 19 | -0.746 | -2.639 | 1.641 | 0.1579 |
| sample 20000 | 2014-2017 | allon | team1 | 2e+04 | -3.74 | 19 | -0.3866 | -1.642 | 0.6948 | 1 |
| sample 20000 | 2014-2017 | allon | team2 | 2e+04 | -5.61 | 19 | -0.5799 | -2.463 | 1.042 | 1 |
| sample 20000 | 2014-2017 | chop_notrange | team1 | 2e+04 | -1.706 | 19 | -0.4637 | -1.837 | 0.8664 | 0.8421 |
| sample 20000 | 2014-2017 | chop_notrange | team2 | 2e+04 | -2.559 | 19 | -0.6955 | -2.756 | 1.3 | 0.8421 |
| sample 20000 | 2014-2017 | chop_trend | team1 | 2e+04 | -1.871 | 19 | -0.7669 | -1.559 | 0.04195 | 0.9474 |
| sample 20000 | 2014-2017 | chop_trend | team2 | 2e+04 | -2.807 | 19 | -1.15 | -2.339 | 0.06292 | 0.9474 |
| sample 20000 | 2014-2017 | chop_ungated | team1 | 2e+04 | -2.271 | 19 | -0.4568 | -2.166 | 0.808 | 1 |
| sample 20000 | 2014-2017 | chop_ungated | team2 | 2e+04 | -3.407 | 19 | -0.6853 | -3.249 | 1.212 | 1 |
| sample 20000 | 2015-2018 | allon | team1 | 2e+04 | -2.228 | 19 | -0.7818 | -2.232 | 0.3968 | 0.9474 |
| sample 20000 | 2015-2018 | allon | team2 | 2e+04 | -3.342 | 19 | -1.173 | -3.348 | 0.5952 | 0.9474 |
| sample 20000 | 2015-2018 | chop_notrange | team1 | 2e+04 | -0.2974 | 19 | -0.561 | -2.442 | 2.085 | 0.4737 |
| sample 20000 | 2015-2018 | chop_notrange | team2 | 2e+04 | -0.4461 | 19 | -0.8414 | -3.663 | 3.127 | 0.4737 |
| sample 20000 | 2015-2018 | chop_trend | team1 | 2e+04 | -1.508 | 19 | -0.9978 | -3.003 | 1.919 | 0.5789 |
| sample 20000 | 2015-2018 | chop_trend | team2 | 2e+04 | -2.262 | 19 | -1.497 | -4.505 | 2.878 | 0.5789 |
| sample 20000 | 2015-2018 | chop_ungated | team1 | 2e+04 | -0.8176 | 19 | -0.784 | -3.1 | 1.106 | 0.5263 |
| sample 20000 | 2015-2018 | chop_ungated | team2 | 2e+04 | -1.226 | 19 | -1.176 | -4.651 | 1.659 | 0.5263 |
| sample 5000 | 2011-2014 | allon | team1 | 5000 | -0.3398 | 19 | -0.7765 | -2.74 | 0.4396 | 0.5263 |
| sample 5000 | 2011-2014 | allon | team2 | 5000 | -0.5097 | 19 | -1.165 | -4.11 | 0.6594 | 0.5263 |
| sample 5000 | 2011-2014 | chop_notrange | team1 | 5000 | -2.794 | 19 | -0.631 | -2.455 | 1.262 | 0.9474 |
| sample 5000 | 2011-2014 | chop_notrange | team2 | 5000 | -4.191 | 19 | -0.9465 | -3.682 | 1.894 | 0.9474 |
| sample 5000 | 2011-2014 | chop_trend | team1 | 5000 | -0.9785 | 19 | -0.6404 | -2.611 | 1.349 | 0.5789 |
| sample 5000 | 2011-2014 | chop_trend | team2 | 5000 | -1.468 | 19 | -0.9605 | -3.917 | 2.023 | 0.5789 |
| sample 5000 | 2011-2014 | chop_ungated | team1 | 5000 | -1.933 | 19 | -0.6032 | -2.64 | 1.334 | 0.7895 |
| sample 5000 | 2011-2014 | chop_ungated | team2 | 5000 | -2.9 | 19 | -0.9048 | -3.961 | 2.001 | 0.7895 |
| sample 5000 | 2012-2015 | allon | team1 | 5000 | -0.7351 | 19 | -0.08603 | -1.322 | 1.524 | 0.7368 |
| sample 5000 | 2012-2015 | allon | team2 | 5000 | -1.103 | 19 | -0.129 | -1.983 | 2.285 | 0.7368 |
| sample 5000 | 2012-2015 | chop_notrange | team1 | 5000 | -1.671 | 19 | -0.2027 | -1.02 | 0.9494 | 0.9474 |
| sample 5000 | 2012-2015 | chop_notrange | team2 | 5000 | -2.506 | 19 | -0.3041 | -1.53 | 1.424 | 0.9474 |
| sample 5000 | 2012-2015 | chop_trend | team1 | 5000 | -2.134 | 19 | -0.7798 | -2.252 | 0.8435 | 0.9474 |
| sample 5000 | 2012-2015 | chop_trend | team2 | 5000 | -3.201 | 19 | -1.17 | -3.378 | 1.265 | 0.9474 |
| sample 5000 | 2012-2015 | chop_ungated | team1 | 5000 | -1.384 | 19 | -0.2296 | -1.372 | 0.7333 | 0.9474 |
| sample 5000 | 2012-2015 | chop_ungated | team2 | 5000 | -2.076 | 19 | -0.3444 | -2.058 | 1.1 | 0.9474 |
| sample 5000 | 2013-2016 | allon | team1 | 5000 | 0.813 | 19 | -0.3852 | -2.082 | 1.008 | 0.1579 |
| sample 5000 | 2013-2016 | allon | team2 | 5000 | 1.219 | 19 | -0.5778 | -3.122 | 1.512 | 0.1579 |
| sample 5000 | 2013-2016 | chop_notrange | team1 | 5000 | -0.6122 | 19 | -0.1366 | -0.9994 | 0.8931 | 0.7368 |
| sample 5000 | 2013-2016 | chop_notrange | team2 | 5000 | -0.9182 | 19 | -0.2049 | -1.499 | 1.34 | 0.7368 |
| sample 5000 | 2013-2016 | chop_trend | team1 | 5000 | 0.4693 | 19 | -0.3673 | -1.753 | 0.9291 | 0.2632 |
| sample 5000 | 2013-2016 | chop_trend | team2 | 5000 | 0.7039 | 19 | -0.551 | -2.63 | 1.394 | 0.2632 |
| sample 5000 | 2013-2016 | chop_ungated | team1 | 5000 | 0.2997 | 19 | -0.6138 | -2.975 | 0.6364 | 0.1053 |
| sample 5000 | 2013-2016 | chop_ungated | team2 | 5000 | 0.4496 | 19 | -0.9207 | -4.462 | 0.9546 | 0.1053 |
| sample 5000 | 2014-2017 | allon | team1 | 5000 | -3.575 | 19 | -0.4516 | -1.896 | 0.9027 | 1 |
| sample 5000 | 2014-2017 | allon | team2 | 5000 | -5.363 | 19 | -0.6775 | -2.845 | 1.354 | 1 |
| sample 5000 | 2014-2017 | chop_notrange | team1 | 5000 | -1.732 | 19 | -0.4692 | -1.665 | 0.9263 | 0.9474 |
| sample 5000 | 2014-2017 | chop_notrange | team2 | 5000 | -2.599 | 19 | -0.7038 | -2.498 | 1.389 | 0.9474 |
| sample 5000 | 2014-2017 | chop_trend | team1 | 5000 | -2.195 | 19 | -0.5146 | -2.048 | 0.8007 | 0.9474 |
| sample 5000 | 2014-2017 | chop_trend | team2 | 5000 | -3.293 | 19 | -0.7719 | -3.072 | 1.201 | 0.9474 |
| sample 5000 | 2014-2017 | chop_ungated | team1 | 5000 | -1.987 | 19 | -0.5587 | -1.613 | 0.3837 | 0.9474 |
| sample 5000 | 2014-2017 | chop_ungated | team2 | 5000 | -2.98 | 19 | -0.8381 | -2.42 | 0.5755 | 0.9474 |
| sample 5000 | 2015-2018 | allon | team1 | 5000 | -2.87 | 19 | -0.5397 | -2.271 | 0.8534 | 1 |
| sample 5000 | 2015-2018 | allon | team2 | 5000 | -4.305 | 19 | -0.8096 | -3.406 | 1.28 | 1 |
| sample 5000 | 2015-2018 | chop_notrange | team1 | 5000 | -0.7113 | 19 | -0.7914 | -2.364 | 0.7263 | 0.5263 |
| sample 5000 | 2015-2018 | chop_notrange | team2 | 5000 | -1.067 | 19 | -1.187 | -3.546 | 1.089 | 0.5263 |
| sample 5000 | 2015-2018 | chop_trend | team1 | 5000 | -1.927 | 19 | -0.7293 | -2.311 | 1.678 | 0.7368 |
| sample 5000 | 2015-2018 | chop_trend | team2 | 5000 | -2.891 | 19 | -1.094 | -3.466 | 2.517 | 0.7368 |
| sample 5000 | 2015-2018 | chop_ungated | team1 | 5000 | -0.9577 | 19 | -0.9373 | -3.171 | 0.3323 | 0.6316 |
| sample 5000 | 2015-2018 | chop_ungated | team2 | 5000 | -1.436 | 19 | -1.406 | -4.757 | 0.4985 | 0.6316 |


### shuffle

| scope | step | book | budget | members | real | n_draws | null_mean | null_p5 | null_p95 | p_one_sided |
|---|---|---|---|---|---|---|---|---|---|---|
| sample 20000 | 2011-2014 | allon | team1 | 2e+04 | -0.801 | 19 | -0.801 | -0.801 | -0.801 | 1 |
| sample 20000 | 2011-2014 | allon | team2 | 2e+04 | -1.202 | 19 | -1.202 | -1.202 | -1.202 | 1 |
| sample 20000 | 2011-2014 | chop_notrange | team1 | 2e+04 | -2.561 | 19 | -0.9714 | -1.38 | -0.6037 | 1 |
| sample 20000 | 2011-2014 | chop_notrange | team2 | 2e+04 | -3.841 | 19 | -1.457 | -2.07 | -0.9055 | 1 |
| sample 20000 | 2011-2014 | chop_trend | team1 | 2e+04 | -1.086 | 19 | -0.8 | -1.434 | 0.03006 | 0.6842 |
| sample 20000 | 2011-2014 | chop_trend | team2 | 2e+04 | -1.629 | 19 | -1.2 | -2.15 | 0.04509 | 0.6842 |
| sample 20000 | 2011-2014 | chop_ungated | team1 | 2e+04 | -1.845 | 19 | -1.113 | -1.753 | -0.698 | 0.9474 |
| sample 20000 | 2011-2014 | chop_ungated | team2 | 2e+04 | -2.768 | 19 | -1.67 | -2.629 | -1.047 | 0.9474 |
| sample 20000 | 2012-2015 | allon | team1 | 2e+04 | -0.1338 | 19 | -0.1338 | -0.1338 | -0.1338 | 1 |
| sample 20000 | 2012-2015 | allon | team2 | 2e+04 | -0.2007 | 19 | -0.2007 | -0.2007 | -0.2007 | 1 |
| sample 20000 | 2012-2015 | chop_notrange | team1 | 2e+04 | -1.516 | 19 | -0.9053 | -1.395 | -0.3948 | 0.9474 |
| sample 20000 | 2012-2015 | chop_notrange | team2 | 2e+04 | -2.274 | 19 | -1.358 | -2.092 | -0.5922 | 0.9474 |
| sample 20000 | 2012-2015 | chop_trend | team1 | 2e+04 | -2.013 | 19 | -0.8758 | -1.445 | 0.158 | 1 |
| sample 20000 | 2012-2015 | chop_trend | team2 | 2e+04 | -3.019 | 19 | -1.314 | -2.168 | 0.237 | 1 |
| sample 20000 | 2012-2015 | chop_ungated | team1 | 2e+04 | -0.7672 | 19 | -0.7457 | -1.362 | -0.3323 | 0.5789 |
| sample 20000 | 2012-2015 | chop_ungated | team2 | 2e+04 | -1.151 | 19 | -1.119 | -2.043 | -0.4984 | 0.5789 |
| sample 20000 | 2013-2016 | allon | team1 | 2e+04 | 0.2053 | 19 | 0.2053 | 0.2053 | 0.2053 | 1 |
| sample 20000 | 2013-2016 | allon | team2 | 2e+04 | 0.3079 | 19 | 0.3079 | 0.3079 | 0.3079 | 1 |
| sample 20000 | 2013-2016 | chop_notrange | team1 | 2e+04 | -0.3322 | 19 | 0.3142 | 0.005086 | 0.6403 | 1 |
| sample 20000 | 2013-2016 | chop_notrange | team2 | 2e+04 | -0.4983 | 19 | 0.4712 | 0.007629 | 0.9604 | 1 |
| sample 20000 | 2013-2016 | chop_trend | team1 | 2e+04 | 0.3128 | 19 | 0.1885 | -0.5094 | 0.9438 | 0.4211 |
| sample 20000 | 2013-2016 | chop_trend | team2 | 2e+04 | 0.4692 | 19 | 0.2827 | -0.7641 | 1.416 | 0.4211 |
| sample 20000 | 2013-2016 | chop_ungated | team1 | 2e+04 | 0.4281 | 19 | 0.3401 | -0.08818 | 0.7016 | 0.3684 |
| sample 20000 | 2013-2016 | chop_ungated | team2 | 2e+04 | 0.6421 | 19 | 0.5102 | -0.1323 | 1.052 | 0.3684 |
| sample 20000 | 2014-2017 | allon | team1 | 2e+04 | -3.74 | 19 | -3.74 | -3.74 | -3.74 | 1 |
| sample 20000 | 2014-2017 | allon | team2 | 2e+04 | -5.61 | 19 | -5.61 | -5.61 | -5.61 | 1 |
| sample 20000 | 2014-2017 | chop_notrange | team1 | 2e+04 | -1.706 | 19 | -1.984 | -2.482 | -1.361 | 0.2105 |
| sample 20000 | 2014-2017 | chop_notrange | team2 | 2e+04 | -2.559 | 19 | -2.975 | -3.723 | -2.042 | 0.2105 |
| sample 20000 | 2014-2017 | chop_trend | team1 | 2e+04 | -1.871 | 19 | -1.864 | -2.807 | -0.8027 | 0.5263 |
| sample 20000 | 2014-2017 | chop_trend | team2 | 2e+04 | -2.807 | 19 | -2.796 | -4.211 | -1.204 | 0.5263 |
| sample 20000 | 2014-2017 | chop_ungated | team1 | 2e+04 | -2.271 | 19 | -1.811 | -2.146 | -1.448 | 1 |
| sample 20000 | 2014-2017 | chop_ungated | team2 | 2e+04 | -3.407 | 19 | -2.717 | -3.22 | -2.172 | 1 |
| sample 20000 | 2015-2018 | allon | team1 | 2e+04 | -2.228 | 19 | -2.228 | -2.228 | -2.228 | 1 |
| sample 20000 | 2015-2018 | allon | team2 | 2e+04 | -3.342 | 19 | -3.342 | -3.342 | -3.342 | 1 |
| sample 20000 | 2015-2018 | chop_notrange | team1 | 2e+04 | -0.2974 | 19 | -0.6514 | -1.129 | -0.308 | 0.05263 |
| sample 20000 | 2015-2018 | chop_notrange | team2 | 2e+04 | -0.4461 | 19 | -0.9771 | -1.693 | -0.462 | 0.05263 |
| sample 20000 | 2015-2018 | chop_trend | team1 | 2e+04 | -1.508 | 19 | -0.9106 | -1.395 | -0.3935 | 1 |
| sample 20000 | 2015-2018 | chop_trend | team2 | 2e+04 | -2.262 | 19 | -1.366 | -2.093 | -0.5902 | 1 |
| sample 20000 | 2015-2018 | chop_ungated | team1 | 2e+04 | -0.8176 | 19 | -0.7764 | -1.076 | -0.5056 | 0.4737 |
| sample 20000 | 2015-2018 | chop_ungated | team2 | 2e+04 | -1.226 | 19 | -1.165 | -1.614 | -0.7584 | 0.4737 |
| sample 5000 | 2011-2014 | allon | team1 | 5000 | -0.3398 | 19 | -0.3398 | -0.3398 | -0.3398 | 1 |
| sample 5000 | 2011-2014 | allon | team2 | 5000 | -0.5097 | 19 | -0.5097 | -0.5097 | -0.5097 | 1 |
| sample 5000 | 2011-2014 | chop_notrange | team1 | 5000 | -2.794 | 19 | -0.8753 | -1.194 | -0.4611 | 1 |
| sample 5000 | 2011-2014 | chop_notrange | team2 | 5000 | -4.191 | 19 | -1.313 | -1.791 | -0.6916 | 1 |
| sample 5000 | 2011-2014 | chop_trend | team1 | 5000 | -0.9785 | 19 | -0.7832 | -1.435 | 0.09088 | 0.6842 |
| sample 5000 | 2011-2014 | chop_trend | team2 | 5000 | -1.468 | 19 | -1.175 | -2.152 | 0.1363 | 0.6842 |
| sample 5000 | 2011-2014 | chop_ungated | team1 | 5000 | -1.933 | 19 | -1.076 | -1.494 | -0.7984 | 1 |
| sample 5000 | 2011-2014 | chop_ungated | team2 | 5000 | -2.9 | 19 | -1.614 | -2.24 | -1.198 | 1 |
| sample 5000 | 2012-2015 | allon | team1 | 5000 | -0.7351 | 19 | -0.7351 | -0.7351 | -0.7351 | 1 |
| sample 5000 | 2012-2015 | allon | team2 | 5000 | -1.103 | 19 | -1.103 | -1.103 | -1.103 | 1 |
| sample 5000 | 2012-2015 | chop_notrange | team1 | 5000 | -1.671 | 19 | -0.9026 | -1.588 | -0.4391 | 1 |
| sample 5000 | 2012-2015 | chop_notrange | team2 | 5000 | -2.506 | 19 | -1.354 | -2.382 | -0.6586 | 1 |
| sample 5000 | 2012-2015 | chop_trend | team1 | 5000 | -2.134 | 19 | -0.8853 | -1.735 | 0.2458 | 1 |
| sample 5000 | 2012-2015 | chop_trend | team2 | 5000 | -3.201 | 19 | -1.328 | -2.602 | 0.3687 | 1 |
| sample 5000 | 2012-2015 | chop_ungated | team1 | 5000 | -1.384 | 19 | -0.7766 | -1.371 | -0.1917 | 0.9474 |
| sample 5000 | 2012-2015 | chop_ungated | team2 | 5000 | -2.076 | 19 | -1.165 | -2.056 | -0.2876 | 0.9474 |
| sample 5000 | 2013-2016 | allon | team1 | 5000 | 0.813 | 19 | 0.813 | 0.813 | 0.813 | 1 |
| sample 5000 | 2013-2016 | allon | team2 | 5000 | 1.219 | 19 | 1.219 | 1.219 | 1.219 | 1 |
| sample 5000 | 2013-2016 | chop_notrange | team1 | 5000 | -0.6122 | 19 | 0.3222 | -0.2014 | 0.8212 | 1 |
| sample 5000 | 2013-2016 | chop_notrange | team2 | 5000 | -0.9182 | 19 | 0.4832 | -0.3022 | 1.232 | 1 |
| sample 5000 | 2013-2016 | chop_trend | team1 | 5000 | 0.4693 | 19 | 0.2736 | -0.3621 | 0.9087 | 0.3684 |
| sample 5000 | 2013-2016 | chop_trend | team2 | 5000 | 0.7039 | 19 | 0.4104 | -0.5432 | 1.363 | 0.3684 |
| sample 5000 | 2013-2016 | chop_ungated | team1 | 5000 | 0.2997 | 19 | 0.2457 | -0.1868 | 0.845 | 0.4211 |
| sample 5000 | 2013-2016 | chop_ungated | team2 | 5000 | 0.4496 | 19 | 0.3685 | -0.2802 | 1.268 | 0.4211 |
| sample 5000 | 2014-2017 | allon | team1 | 5000 | -3.575 | 19 | -3.575 | -3.575 | -3.575 | 1 |
| sample 5000 | 2014-2017 | allon | team2 | 5000 | -5.363 | 19 | -5.363 | -5.363 | -5.363 | 1 |
| sample 5000 | 2014-2017 | chop_notrange | team1 | 5000 | -1.732 | 19 | -2.072 | -2.715 | -1.449 | 0.1579 |
| sample 5000 | 2014-2017 | chop_notrange | team2 | 5000 | -2.599 | 19 | -3.108 | -4.072 | -2.173 | 0.1579 |
| sample 5000 | 2014-2017 | chop_trend | team1 | 5000 | -2.195 | 19 | -1.811 | -2.895 | -0.9522 | 0.6842 |
| sample 5000 | 2014-2017 | chop_trend | team2 | 5000 | -3.293 | 19 | -2.717 | -4.343 | -1.428 | 0.6842 |
| sample 5000 | 2014-2017 | chop_ungated | team1 | 5000 | -1.987 | 19 | -1.862 | -2.31 | -1.483 | 0.6316 |
| sample 5000 | 2014-2017 | chop_ungated | team2 | 5000 | -2.98 | 19 | -2.792 | -3.464 | -2.225 | 0.6316 |
| sample 5000 | 2015-2018 | allon | team1 | 5000 | -2.87 | 19 | -2.87 | -2.87 | -2.87 | 1 |
| sample 5000 | 2015-2018 | allon | team2 | 5000 | -4.305 | 19 | -4.305 | -4.305 | -4.305 | 1 |
| sample 5000 | 2015-2018 | chop_notrange | team1 | 5000 | -0.7113 | 19 | -0.8643 | -1.219 | -0.4697 | 0.2632 |
| sample 5000 | 2015-2018 | chop_notrange | team2 | 5000 | -1.067 | 19 | -1.297 | -1.829 | -0.7046 | 0.2632 |
| sample 5000 | 2015-2018 | chop_trend | team1 | 5000 | -1.927 | 19 | -1.004 | -1.68 | -0.4197 | 1 |
| sample 5000 | 2015-2018 | chop_trend | team2 | 5000 | -2.891 | 19 | -1.506 | -2.519 | -0.6295 | 1 |
| sample 5000 | 2015-2018 | chop_ungated | team1 | 5000 | -0.9577 | 19 | -0.9488 | -1.252 | -0.6336 | 0.5789 |
| sample 5000 | 2015-2018 | chop_ungated | team2 | 5000 | -1.436 | 19 | -1.423 | -1.878 | -0.9503 | 0.5789 |


**Is the p-value stable in the sample size?** Same (null, step, book, budget) at 5,000 and at 20,000:

| null | step | book | budget | sample 20000 | sample 5000 |
|---|---|---|---|---|---|
| random-entry | 2011-2014 | allon | team1 | 0.4737 | 0.5263 |
| random-entry | 2011-2014 | allon | team2 | 0.4737 | 0.5263 |
| random-entry | 2011-2014 | chop_notrange | team1 | 0.9474 | 0.9474 |
| random-entry | 2011-2014 | chop_notrange | team2 | 0.9474 | 0.9474 |
| random-entry | 2011-2014 | chop_trend | team1 | 0.6316 | 0.5789 |
| random-entry | 2011-2014 | chop_trend | team2 | 0.6316 | 0.5789 |
| random-entry | 2011-2014 | chop_ungated | team1 | 0.8947 | 0.7895 |
| random-entry | 2011-2014 | chop_ungated | team2 | 0.8947 | 0.7895 |
| random-entry | 2012-2015 | allon | team1 | 0.5789 | 0.7368 |
| random-entry | 2012-2015 | allon | team2 | 0.5789 | 0.7368 |
| random-entry | 2012-2015 | chop_notrange | team1 | 0.9474 | 0.9474 |
| random-entry | 2012-2015 | chop_notrange | team2 | 0.9474 | 0.9474 |
| random-entry | 2012-2015 | chop_trend | team1 | 1 | 0.9474 |
| random-entry | 2012-2015 | chop_trend | team2 | 1 | 0.9474 |
| random-entry | 2012-2015 | chop_ungated | team1 | 0.7895 | 0.9474 |
| random-entry | 2012-2015 | chop_ungated | team2 | 0.7895 | 0.9474 |
| random-entry | 2013-2016 | allon | team1 | 0.2105 | 0.1579 |
| random-entry | 2013-2016 | allon | team2 | 0.2105 | 0.1579 |
| random-entry | 2013-2016 | chop_notrange | team1 | 0.6842 | 0.7368 |
| random-entry | 2013-2016 | chop_notrange | team2 | 0.6842 | 0.7368 |
| random-entry | 2013-2016 | chop_trend | team1 | 0.1579 | 0.2632 |
| random-entry | 2013-2016 | chop_trend | team2 | 0.1579 | 0.2632 |
| random-entry | 2013-2016 | chop_ungated | team1 | 0.1579 | 0.1053 |
| random-entry | 2013-2016 | chop_ungated | team2 | 0.1579 | 0.1053 |
| random-entry | 2014-2017 | allon | team1 | 1 | 1 |
| random-entry | 2014-2017 | allon | team2 | 1 | 1 |
| random-entry | 2014-2017 | chop_notrange | team1 | 0.8421 | 0.9474 |
| random-entry | 2014-2017 | chop_notrange | team2 | 0.8421 | 0.9474 |
| random-entry | 2014-2017 | chop_trend | team1 | 0.9474 | 0.9474 |
| random-entry | 2014-2017 | chop_trend | team2 | 0.9474 | 0.9474 |
| random-entry | 2014-2017 | chop_ungated | team1 | 1 | 0.9474 |
| random-entry | 2014-2017 | chop_ungated | team2 | 1 | 0.9474 |
| random-entry | 2015-2018 | allon | team1 | 0.9474 | 1 |
| random-entry | 2015-2018 | allon | team2 | 0.9474 | 1 |
| random-entry | 2015-2018 | chop_notrange | team1 | 0.4737 | 0.5263 |
| random-entry | 2015-2018 | chop_notrange | team2 | 0.4737 | 0.5263 |
| random-entry | 2015-2018 | chop_trend | team1 | 0.5789 | 0.7368 |
| random-entry | 2015-2018 | chop_trend | team2 | 0.5789 | 0.7368 |
| random-entry | 2015-2018 | chop_ungated | team1 | 0.5263 | 0.6316 |
| random-entry | 2015-2018 | chop_ungated | team2 | 0.5263 | 0.6316 |
| shuffle | 2011-2014 | allon | team1 | 1 | 1 |
| shuffle | 2011-2014 | allon | team2 | 1 | 1 |
| shuffle | 2011-2014 | chop_notrange | team1 | 1 | 1 |
| shuffle | 2011-2014 | chop_notrange | team2 | 1 | 1 |
| shuffle | 2011-2014 | chop_trend | team1 | 0.6842 | 0.6842 |
| shuffle | 2011-2014 | chop_trend | team2 | 0.6842 | 0.6842 |
| shuffle | 2011-2014 | chop_ungated | team1 | 0.9474 | 1 |
| shuffle | 2011-2014 | chop_ungated | team2 | 0.9474 | 1 |
| shuffle | 2012-2015 | allon | team1 | 1 | 1 |
| shuffle | 2012-2015 | allon | team2 | 1 | 1 |
| shuffle | 2012-2015 | chop_notrange | team1 | 0.9474 | 1 |
| shuffle | 2012-2015 | chop_notrange | team2 | 0.9474 | 1 |
| shuffle | 2012-2015 | chop_trend | team1 | 1 | 1 |
| shuffle | 2012-2015 | chop_trend | team2 | 1 | 1 |
| shuffle | 2012-2015 | chop_ungated | team1 | 0.5789 | 0.9474 |
| shuffle | 2012-2015 | chop_ungated | team2 | 0.5789 | 0.9474 |
| shuffle | 2013-2016 | allon | team1 | 1 | 1 |
| shuffle | 2013-2016 | allon | team2 | 1 | 1 |
| shuffle | 2013-2016 | chop_notrange | team1 | 1 | 1 |
| shuffle | 2013-2016 | chop_notrange | team2 | 1 | 1 |
| shuffle | 2013-2016 | chop_trend | team1 | 0.4211 | 0.3684 |
| shuffle | 2013-2016 | chop_trend | team2 | 0.4211 | 0.3684 |
| shuffle | 2013-2016 | chop_ungated | team1 | 0.3684 | 0.4211 |
| shuffle | 2013-2016 | chop_ungated | team2 | 0.3684 | 0.4211 |
| shuffle | 2014-2017 | allon | team1 | 1 | 1 |
| shuffle | 2014-2017 | allon | team2 | 1 | 1 |
| shuffle | 2014-2017 | chop_notrange | team1 | 0.2105 | 0.1579 |
| shuffle | 2014-2017 | chop_notrange | team2 | 0.2105 | 0.1579 |
| shuffle | 2014-2017 | chop_trend | team1 | 0.5263 | 0.6842 |
| shuffle | 2014-2017 | chop_trend | team2 | 0.5263 | 0.6842 |
| shuffle | 2014-2017 | chop_ungated | team1 | 1 | 0.6316 |
| shuffle | 2014-2017 | chop_ungated | team2 | 1 | 0.6316 |
| shuffle | 2015-2018 | allon | team1 | 1 | 1 |
| shuffle | 2015-2018 | allon | team2 | 1 | 1 |
| shuffle | 2015-2018 | chop_notrange | team1 | 0.05263 | 0.2632 |
| shuffle | 2015-2018 | chop_notrange | team2 | 0.05263 | 0.2632 |
| shuffle | 2015-2018 | chop_trend | team1 | 1 | 1 |
| shuffle | 2015-2018 | chop_trend | team2 | 1 | 1 |
| shuffle | 2015-2018 | chop_ungated | team1 | 0.4737 | 0.5789 |
| shuffle | 2015-2018 | chop_ungated | team2 | 0.4737 | 0.5789 |


## THE BLIND GRADE — reported, never used

From `results/r2gate2/modeB_books_blindgrade.csv`. Year 5 of each step is graded by the tuner's own objective but was never seen by the tuner and gates nothing.

| step | stream | n_eligible | n_graded_pass | n_graded_fail | trade_R_graded_pass | trade_R_graded_fail | spearman_grade_to_trade | p |
|---|---|---|---|---|---|---|---|---|
| 2011-2014 | trend-routed | 269,043 | 136,172 | 132,539 | -0.02893 | -0.04049 | 0.07886 | 0 |
| 2011-2014 | trend-allon | 273,637 | 134,667 | 138,645 | -0.02195 | -0.03438 | 0.1304 | 0 |
| 2011-2014 | chop-routed | 253,874 | 136,158 | 117,467 | -0.07995 | -0.04297 | -0.1097 | 0 |
| 2011-2014 | chop-allon | 272,330 | 110,735 | 161,560 | -0.01697 | -0.03472 | 0.1033 | 0 |
| 2012-2015 | trend-routed | 270,100 | 88,410 | 179,637 | -0.05389 | -0.04164 | -0.08613 | 0 |
| 2012-2015 | trend-allon | 273,416 | 90,399 | 182,692 | -0.0345 | -0.03331 | -0.01523 | 1.695e-15 |
| 2012-2015 | chop-routed | 250,812 | 73,053 | 177,734 | -0.03568 | -0.06137 | 0.1121 | 0 |
| 2012-2015 | chop-allon | 272,432 | 98,040 | 174,182 | -0.03912 | -0.0534 | 0.04729 | 1.212e-134 |
| 2013-2016 | trend-routed | 269,541 | 70,681 | 190,045 | 0.01656 | -0.03003 | 0.1563 | 0 |
| 2013-2016 | trend-allon | 272,540 | 72,412 | 188,785 | 0.01466 | -0.006427 | 0.134 | 0 |
| 2013-2016 | chop-routed | 252,923 | 94,030 | 156,056 | -0.003567 | 0.01807 | -0.06602 | 3.093e-242 |
| 2013-2016 | chop-allon | 272,538 | 89,147 | 172,365 | 0.04699 | 0.002369 | 0.1681 | 0 |
| 2014-2017 | trend-routed | 268,184 | 115,023 | 148,822 | -0.07755 | -0.07679 | 0.008077 | 2.879e-05 |
| 2014-2017 | trend-allon | 273,587 | 135,149 | 137,210 | -0.05363 | -0.05787 | 0.06418 | 1.379e-247 |
| 2014-2017 | chop-routed | 254,603 | 134,668 | 119,634 | -0.07407 | -0.07034 | -0.01913 | 4.706e-22 |
| 2014-2017 | chop-allon | 272,319 | 153,829 | 116,777 | -0.08213 | -0.08824 | 0.0622 | 1.494e-231 |
| 2015-2018 | trend-routed | 265,113 | 50,021 | 207,450 | -0.0366 | -0.04648 | 0.0482 | 4.192e-136 |
| 2015-2018 | trend-allon | 273,612 | 48,240 | 225,074 | -0.03056 | -0.03452 | 0.08099 | 0 |
| 2015-2018 | chop-routed | 255,076 | 64,135 | 190,941 | -0.04801 | -0.05209 | 0.006154 | 0.001883 |
| 2015-2018 | chop-allon | 272,229 | 57,573 | 214,522 | -0.06773 | -0.07538 | 0.06977 | 8.164e-291 |


## THE TWO LAYER 1 SPLITS — reported, gate nothing

From `results/r2gate2/modeB_books_layer1splits.csv`.


### episode_third

| scope | step | quality_tag | third | total_R | mean_R_per_mark | mark_rows |
|---|---|---|---|---|---|---|
| routed trend, sample 4000 | 2011-2014 |  | first | -7848 | -0.009287 | 8.45e+05 |
| routed trend, sample 4000 | 2011-2014 |  | last | -455.9 | -0.00901 | 5.061e+04 |
| routed trend, sample 4000 | 2011-2014 |  | middle | -1126 | -0.008388 | 1.342e+05 |
| routed trend, sample 4000 | 2012-2015 |  | first | -4622 | -0.006983 | 6.619e+05 |
| routed trend, sample 4000 | 2012-2015 |  | last | 94.52 | 0.0006235 | 1.516e+05 |
| routed trend, sample 4000 | 2012-2015 |  | middle | -6108 | -0.01083 | 5.639e+05 |
| routed trend, sample 4000 | 2013-2016 |  | first | -4486 | -0.02002 | 2.241e+05 |
| routed trend, sample 4000 | 2013-2016 |  | last | 2867 | 0.006243 | 4.593e+05 |
| routed trend, sample 4000 | 2013-2016 |  | middle | -4523 | -0.007837 | 5.771e+05 |
| routed trend, sample 4000 | 2014-2017 |  | first | -7672 | -0.02843 | 2.699e+05 |
| routed trend, sample 4000 | 2014-2017 |  | last | -1972 | -0.005356 | 3.682e+05 |
| routed trend, sample 4000 | 2014-2017 |  | middle | -8035 | -0.02241 | 3.586e+05 |
| routed trend, sample 4000 | 2015-2018 |  | first | -326.6 | -0.006749 | 4.839e+04 |
| routed trend, sample 4000 | 2015-2018 |  | last | -1.35e+04 | -0.01324 | 1.02e+06 |
| routed trend, sample 4000 | 2015-2018 |  | middle | -4691 | -0.01129 | 4.155e+05 |


### episode_third_by_episode

| scope | step | quality_tag | third | total_R | mean_R_per_mark | mark_rows |
|---|---|---|---|---|---|---|
| routed trend, mode B, sample 4000 strategies | 2011-2014 |  | first | 1333 |  |  |
| routed trend, mode B, sample 4000 strategies | 2011-2014 |  | last | -1.318e+04 |  |  |
| routed trend, mode B, sample 4000 strategies | 2011-2014 |  | middle | 2419 |  |  |
| routed trend, mode B, sample 4000 strategies | 2012-2015 |  | first | 1442 |  |  |
| routed trend, mode B, sample 4000 strategies | 2012-2015 |  | last | -1.733e+04 |  |  |
| routed trend, mode B, sample 4000 strategies | 2012-2015 |  | middle | 5248 |  |  |
| routed trend, mode B, sample 4000 strategies | 2013-2016 |  | first | 2079 |  |  |
| routed trend, mode B, sample 4000 strategies | 2013-2016 |  | last | -1.204e+04 |  |  |
| routed trend, mode B, sample 4000 strategies | 2013-2016 |  | middle | 3823 |  |  |
| routed trend, mode B, sample 4000 strategies | 2014-2017 |  | first | 783.4 |  |  |
| routed trend, mode B, sample 4000 strategies | 2014-2017 |  | last | -1.439e+04 |  |  |
| routed trend, mode B, sample 4000 strategies | 2014-2017 |  | middle | -4070 |  |  |
| routed trend, mode B, sample 4000 strategies | 2015-2018 |  | first | -2531 |  |  |
| routed trend, mode B, sample 4000 strategies | 2015-2018 |  | last | -1.227e+04 |  |  |
| routed trend, mode B, sample 4000 strategies | 2015-2018 |  | middle | -3716 |  |  |


### quality_tag

| scope | step | quality_tag | third | total_R | mean_R_per_mark | mark_rows |
|---|---|---|---|---|---|---|
| routed trend, sample 4000 | 2011-2014 | high |  | -2962 | -0.004516 | 6.558e+05 |
| routed trend, sample 4000 | 2011-2014 | low |  | -6468 | -0.01729 | 3.741e+05 |
| routed trend, sample 4000 | 2011-2014 |  |  | 524 | 0.003106 | 1.687e+05 |
| routed trend, sample 4000 | 2012-2015 | high |  | -1.544e+04 | -0.02815 | 5.485e+05 |
| routed trend, sample 4000 | 2012-2015 | low |  | 4805 | 0.005797 | 8.289e+05 |
| routed trend, sample 4000 | 2012-2015 |  |  | -1223 | -0.007166 | 1.707e+05 |
| routed trend, sample 4000 | 2013-2016 | high |  | -6152 | -0.02601 | 2.365e+05 |
| routed trend, sample 4000 | 2013-2016 | low |  | 11.66 | 1.139e-05 | 1.024e+06 |
| routed trend, sample 4000 | 2013-2016 |  |  | -1264 | -0.006734 | 1.878e+05 |
| routed trend, sample 4000 | 2014-2017 | high |  | -6879 | -0.02647 | 2.599e+05 |
| routed trend, sample 4000 | 2014-2017 | low |  | -1.08e+04 | -0.01466 | 7.367e+05 |
| routed trend, sample 4000 | 2014-2017 |  |  | -405.5 | -0.002681 | 1.512e+05 |
| routed trend, sample 4000 | 2015-2018 | high |  | -1.496e+04 | -0.02922 | 5.119e+05 |
| routed trend, sample 4000 | 2015-2018 | low |  | -3562 | -0.003666 | 9.716e+05 |
| routed trend, sample 4000 | 2015-2018 |  |  | 3380 | 0.0155 | 2.181e+05 |


### quality_tag_by_episode

| scope | step | quality_tag | third | total_R | mean_R_per_mark | mark_rows |
|---|---|---|---|---|---|---|
| routed trend, mode B, sample 4000 strategies | 2011-2014 | high |  | -8404 |  |  |
| routed trend, mode B, sample 4000 strategies | 2011-2014 | low |  | -1026 |  |  |
| routed trend, mode B, sample 4000 strategies | 2012-2015 | high |  | -6191 |  |  |
| routed trend, mode B, sample 4000 strategies | 2012-2015 | low |  | -4444 |  |  |
| routed trend, mode B, sample 4000 strategies | 2013-2016 | high |  | -2250 |  |  |
| routed trend, mode B, sample 4000 strategies | 2013-2016 | low |  | -3891 |  |  |
| routed trend, mode B, sample 4000 strategies | 2014-2017 | high |  | -5455 |  |  |
| routed trend, mode B, sample 4000 strategies | 2014-2017 | low |  | -1.222e+04 |  |  |
| routed trend, mode B, sample 4000 strategies | 2015-2018 | high |  | -2959 |  |  |
| routed trend, mode B, sample 4000 strategies | 2015-2018 | low |  | -1.556e+04 |  |  |


## WHAT GATE 1 SAID, for context

From `results/r2gate1_pooled_modeB_full.csv`: trade-year expectancy over the whole eligible population, by stream.

| stream | n_eligible | trade_R_pass |
|---|---|---|
| trend-routed | 243,568 | -0.042 |
| trend-allon | 265,092 | -0.03406 |
| chop-routed | 206,723 | -0.05737 |
| chop-allon | 252,371 | -0.05172 |


And the gate 1 regime-shuffle null, from `results/r2gate1_shufflenull_modeB.csv`:

| slice | stream | top_pct | real_trade_R | surrogate_mean | p_one_sided |
|---|---|---|---|---|---|
| trend | routed | 0.1 | 0.01817 | 0.01927 | 0.4523 |
| trend | routed | 1 | -0.02148 | 0.002388 | 0.7136 |
| trend | routed | 10 | -0.029 | -0.01291 | 0.7739 |
| trend | routed | 50 | -0.02916 | -0.0236 | 0.6734 |
| chop | routed | 0.1 | 0.08131 | 0.1017 | 0.6382 |
| chop | routed | 1 | 0.01929 | 0.06027 | 0.8945 |
| chop | routed | 10 | -0.01607 | 0.009094 | 0.8744 |
| chop | routed | 50 | -0.04411 | -0.03065 | 0.7789 |


## WHAT IS NOT IN THIS REPORT

- **Full-field random-entry and regime-shuffle nulls.** Run here on stratified samples at two sizes. At the measured 0.48 s per strategy per draw the full field is a multi-day job; it is registered in HANDOFF 0l as the clean run to do later.

- **Any number not read from the files listed above.** Nothing here is restated from memory.
