<!-- PROVENANCE DRIFT, found by pre-flight guard 35 on 24 Nov 2026 at 22:50.

Two csvs this report names no longer hold the rows it claims:

  results/r2gate2/modeA_books_layer1splits.csv   claimed 30     on disk 55
  results/r2gate2_cond2_modeA.csv                claimed 7,660  on disk 240

The first GREW: a later run added Layer 1 split rows and this report was not
regenerated, so the figures it quotes come from the 30-row version.

The second SHRANK by 97%, which is the same signature as the STAGE1
canonical_risk overwrite: a later, smaller condition-2 run reused the
production filename. THIS REPORT'S CONDITION 2 CLAIM IS NOT BACKED BY THE FILE
IT NAMES. Do not re-derive it from that csv.

Both are recorded in preflight.DECLARED_DRIFT pinned to the CURRENT on-disk
counts, so if either file moves again the guard fails afresh. Regenerating this
report is the real fix and is Jack's call, because it is a shipped record and
rewriting it would move numbers he has already read.
-->
# MODE A — THE HONEST GATE 2, ALL 273,780 STRATEGIES

Generated 2026-11-18 09:32 by `code/l2r2modearep.py`. **Every number below was read out of a file in this run and the file is named beside it.** A section whose source is missing says so and is left empty.


## The files this report is built from

| section | file | rows | md5 | mtime |
|---|---|---|---|---|
| books | results/r2gate2/modeA_books_e2e16.csv | 40 | 8cc29eecdb67 | 2026-11-18 09:29 |
| nulls | results/r2gate2/modeA_books_nulls_e2e16.csv | 120 | 753c60feafb9 | 2026-11-18 09:31 |
| grade | results/r2gate2/modeA_books_blindgrade.csv | 20 | 653dbb5e2a06 | 2026-11-18 09:31 |
| splits | results/r2gate2/modeA_books_layer1splits.csv | 30 | a583078281a0 | 2026-11-18 09:31 |
| gate1 | results/r2gate1_pooled_modeA_full.csv | 480 | a6ea66a717e6 | 2026-11-16 18:16 |
| rankcorr | results/r2gate1_rankcorr_modeA_full.csv | 20 | 051f11bae2c2 | 2026-11-16 18:15 |
| grid | results/r2gate2_grid.csv | 6 | 85045a1adf2e | 2026-11-17 09:57 |
| cond1 | results/r2gate2_cond1_modeA.csv | 1 | 0f7083cdfc9e | 2026-11-17 09:58 |
| cond2 | results/r2gate2_cond2_modeA.csv | 7,660 | 7dfaded49155 | 2026-11-17 11:54 |
| streamed | results/r2book_series_equals_shipped_modeA.csv | 2 | 8940571fda48 | 2026-11-17 20:35 |
| shuffle1 | results/r2gate1_shufflenull_modeA.csv | 16 | 291541298c86 | 2026-11-16 18:53 |
| manifest | results/layer1_interface_manifest_2026-11-16.csv | 16 | f6582570eeb5 | 2026-11-16 14:19 |


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

**Condition 1 — no year holds another year's price.** From `results/r2gate2_cond1_modeA.csv`: | mode | n_strategies | n_evaluations | worst_abs_diff | pass_ |
|---|---|---|---|---|
| A | 40 | 240 | 1.421e-14 | 1 |


**Condition 2 — the banked one pass equals the per-step path.** From `results/r2gate2_cond2_modeA.csv`: 7660 comparisons, 0 tune-pick mismatches, 0 record mismatches, worst |diff| 0.


**The streamed book equals the shipped book.** From `results/r2book_series_equals_shipped_modeA.csv`: worst daily difference 1.22e-08 across 2 slices.


## THE FOUR BOOKS

From `results/r2gate2/modeA_books_e2e16.csv`, 40 rows = 5 steps x 4 books x 2 budgets.


### Trade-year median, by book and budget, pooled over the five steps

| book | budget | steps | median_of_trade_medians | worst_step | best_step | median_dip95 | median_PF | median_retention | steps_flagged_FIT |
|---|---|---|---|---|---|---|---|---|---|
| allon | team1 | 5 | -0.4134 | -1.19 | -0.04237 | 1.893 | 0.9358 | -0.4246 | 4 |
| allon | team2 | 5 | -0.6201 | -1.785 | -0.06356 | 2.84 | 0.9358 | -0.4246 | 4 |
| chop_notrange | team1 | 5 | 0.005026 | -1.264 | 0.5735 | 2.031 | 1.001 | -0.01303 | 4 |
| chop_notrange | team2 | 5 | 0.007539 | -1.895 | 0.8603 | 3.046 | 1.001 | -0.01303 | 4 |
| chop_trend | team1 | 5 | -0.1729 | -1.08 | 1.956 | 2.007 | 0.9695 | -0.2051 | 3 |
| chop_trend | team2 | 5 | -0.2593 | -1.621 | 2.934 | 3.01 | 0.9695 | -0.2051 | 3 |
| chop_ungated | team1 | 5 | -0.8273 | -1.877 | -0.007477 | 2.256 | 0.8392 | -0.4694 | 4 |
| chop_ungated | team2 | 5 | -1.241 | -2.816 | -0.01121 | 3.384 | 0.8392 | -0.4694 | 4 |


### Every step, every book, team1 budget

| step | book | size_scale | scale_binds | build_median_year_pct | trade_median_year_pct | trade_dip95_pct | trade_max_dd_pct | trade_profit_factor | retention | FIT |
|---|---|---|---|---|---|---|---|---|---|---|
| 2011-2014 | allon | 0.2416 | DIP95 | 0.9736 | -0.4134 | 2.261 | 1.475 | 0.9454 | -0.4246 | 1 |
| 2011-2014 | chop_notrange | 0.376 | DIP95 | 1.267 | 0.1588 | 2.031 | 1.785 | 1.021 | 0.1254 | 1 |
| 2011-2014 | chop_trend | 0.2998 | actual maxDD | 2.327 | 1.956 | 1.528 | 0.9562 | 1.329 | 0.8406 | 0 |
| 2011-2014 | chop_ungated | 0.3851 | DIP95 | 1.496 | -0.7023 | 2.631 | 2.463 | 0.9167 | -0.4694 | 1 |
| 2012-2015 | allon | 0.2555 | DIP95 | 0.5944 | -1.19 | 2.056 | 1.41 | 0.8042 | -2.003 | 1 |
| 2012-2015 | chop_notrange | 0.2597 | DIP95 | 1.175 | 0.5735 | 1.866 | 1.117 | 1.081 | 0.4882 | 0 |
| 2012-2015 | chop_trend | 0.3018 | DIP95 | 1.288 | -0.2642 | 2.671 | 1.539 | 0.9666 | -0.2051 | 1 |
| 2012-2015 | chop_ungated | 0.3488 | DIP95 | 1.103 | -1.877 | 3.395 | 1.93 | 0.8008 | -1.701 | 1 |
| 2013-2016 | allon | 0.2208 | DIP95 | -0.1132 | -0.5119 | 1.893 | 1.081 | 0.9083 | 4.524 | 0 |
| 2013-2016 | chop_notrange | 0.3674 | DIP95 | 1.284 | -0.1408 | 2.678 | 1.772 | 0.9846 | -0.1096 | 1 |
| 2013-2016 | chop_trend | 0.2084 | DIP95 | 0.9492 | 0.5503 | 1.226 | 0.5907 | 1.131 | 0.5798 | 0 |
| 2013-2016 | chop_ungated | 0.31 | DIP95 | 0.6765 | -0.007477 | 1.888 | 1.374 | 0.9989 | -0.01105 | 1 |
| 2014-2017 | allon | 0.2588 | DIP95 | 0.356 | -0.04237 | 1.402 | 0.869 | 0.9913 | -0.119 | 1 |
| 2014-2017 | chop_notrange | 0.253 | DIP95 | 0.08885 | -1.264 | 2.477 | 1.483 | 0.8171 | -14.22 | 1 |
| 2014-2017 | chop_trend | 0.2112 | DIP95 | 0.4083 | -1.08 | 2.592 | 1.922 | 0.8559 | -2.646 | 1 |
| 2014-2017 | chop_ungated | 0.3403 | DIP95 | 0.6282 | -1.139 | 2.256 | 1.857 | 0.8113 | -1.812 | 1 |
| 2015-2018 | allon | 0.2754 | DIP95 | 0.0988 | -0.2534 | 1.599 | 1.253 | 0.9358 | -2.565 | 1 |
| 2015-2018 | chop_notrange | 0.2695 | DIP95 | -0.3857 | 0.005026 | 1.316 | 1.009 | 1.001 | -0.01303 | 1 |
| 2015-2018 | chop_trend | 0.2581 | DIP95 | 0.5701 | -0.1729 | 2.007 | 1.328 | 0.9695 | -0.3032 | 1 |
| 2015-2018 | chop_ungated | 0.252 | DIP95 | -0.004923 | -0.8273 | 2.036 | 1.333 | 0.8392 | 168 | 0 |


## THE THREE NULLS

From `results/r2gate2/modeA_books_nulls_e2e16.csv`, 120 rows.


### identity

| scope | step | book | budget | members | real | n_draws | null_mean | null_p5 | null_p95 | p_one_sided |
|---|---|---|---|---|---|---|---|---|---|---|
| full field | 2011-2014 | allon | team1 |  | -0.4134 | 20 | 0.5106 | -1.034 | 2.429 | 0.85 |
| full field | 2011-2014 | allon | team2 |  | -0.6201 | 20 | 1.096 | -1.55 | 3.643 | 0.6 |
| full field | 2011-2014 | chop_notrange | team1 |  | 0.1588 | 20 | 0.9809 | -0.7097 | 2.357 | 0.8 |
| full field | 2011-2014 | chop_notrange | team2 |  | 0.2382 | 20 | 1.559 | 0.1731 | 3.535 | 0.75 |
| full field | 2011-2014 | chop_trend | team1 |  | 1.956 | 20 | 1.396 | -2.303 | 4.43 | 0.4 |
| full field | 2011-2014 | chop_trend | team2 |  | 2.934 | 20 | 2.399 | -3.454 | 6.645 | 0.6 |
| full field | 2011-2014 | chop_ungated | team1 |  | -0.7023 | 20 | 0.8653 | -0.7029 | 2.731 | 0.95 |
| full field | 2011-2014 | chop_ungated | team2 |  | -1.053 | 20 | 1.719 | -1.071 | 4.097 | 0.85 |
| full field | 2012-2015 | allon | team1 |  | -1.19 | 20 | -0.04074 | -1.19 | 0.8779 | 1 |
| full field | 2012-2015 | allon | team2 |  | -1.785 | 20 | -0.5656 | -1.785 | 1.518 | 1 |
| full field | 2012-2015 | chop_notrange | team1 |  | 0.5735 | 20 | 0.4799 | -2.274 | 3.332 | 0.4 |
| full field | 2012-2015 | chop_notrange | team2 |  | 0.8603 | 20 | 1.517 | -3.411 | 4.997 | 0.7 |
| full field | 2012-2015 | chop_trend | team1 |  | -0.2642 | 20 | 1.239 | -0.2642 | 3.909 | 0.75 |
| full field | 2012-2015 | chop_trend | team2 |  | -0.3964 | 20 | 0.5787 | -2.616 | 3.206 | 0.6 |
| full field | 2012-2015 | chop_ungated | team1 |  | -1.877 | 20 | 0.5091 | -1.211 | 1.41 | 1 |
| full field | 2012-2015 | chop_ungated | team2 |  | -2.816 | 20 | 1.289 | -2.816 | 2.817 | 1 |
| full field | 2013-2016 | allon | team1 |  | -0.5119 | 20 | -0.2557 | -0.838 | 1.562 | 0.7 |
| full field | 2013-2016 | allon | team2 |  | -0.7679 | 20 | 0.2536 | -1.257 | 2.343 | 0.8 |
| full field | 2013-2016 | chop_notrange | team1 |  | -0.1408 | 20 | 0.9132 | -1.195 | 1.894 | 0.75 |
| full field | 2013-2016 | chop_notrange | team2 |  | -0.2112 | 20 | 1.138 | -1.793 | 2.84 | 0.65 |
| full field | 2013-2016 | chop_trend | team1 |  | 0.5503 | 20 | 0.6869 | -1.756 | 3.14 | 0.5 |
| full field | 2013-2016 | chop_trend | team2 |  | 0.8255 | 20 | 1.071 | -0.7651 | 4.711 | 0.7 |
| full field | 2013-2016 | chop_ungated | team1 |  | -0.007477 | 20 | 0.2995 | -1.393 | 1.312 | 0.65 |
| full field | 2013-2016 | chop_ungated | team2 |  | -0.01121 | 20 | 0.0636 | -2.09 | 1.968 | 0.5 |
| full field | 2014-2017 | allon | team1 |  | -0.04237 | 20 | 0.3319 | -1.172 | 0.9698 | 0.9 |
| full field | 2014-2017 | allon | team2 |  | -0.06356 | 20 | 0.4543 | -1.758 | 1.455 | 0.9 |
| full field | 2014-2017 | chop_notrange | team1 |  | -1.264 | 20 | -0.2158 | -1.264 | 1.082 | 1 |
| full field | 2014-2017 | chop_notrange | team2 |  | -1.895 | 20 | -0.1758 | -1.895 | 1.623 | 0.85 |
| full field | 2014-2017 | chop_trend | team1 |  | -1.08 | 20 | 0.05777 | -1.08 | 1.236 | 1 |
| full field | 2014-2017 | chop_trend | team2 |  | -1.621 | 20 | 0.001445 | -1.621 | 1.854 | 1 |
| full field | 2014-2017 | chop_ungated | team1 |  | -1.139 | 20 | 0.2204 | -1.139 | 1.741 | 1 |
| full field | 2014-2017 | chop_ungated | team2 |  | -1.708 | 20 | 0.9761 | -1.708 | 2.612 | 1 |
| full field | 2015-2018 | allon | team1 |  | -0.2534 | 20 | 0.4104 | -0.2534 | 1.605 | 0.8 |
| full field | 2015-2018 | allon | team2 |  | -0.3801 | 20 | 0.3707 | -1.461 | 2.408 | 0.9 |
| full field | 2015-2018 | chop_notrange | team1 |  | 0.005026 | 20 | -0.01223 | -1.574 | 2.992 | 0.25 |
| full field | 2015-2018 | chop_notrange | team2 |  | 0.007539 | 20 | 0.7978 | -2.361 | 4.489 | 0.55 |
| full field | 2015-2018 | chop_trend | team1 |  | -0.1729 | 20 | 0.3282 | -0.9047 | 2.315 | 0.75 |
| full field | 2015-2018 | chop_trend | team2 |  | -0.2593 | 20 | 1.084 | -0.3142 | 3.472 | 0.95 |
| full field | 2015-2018 | chop_ungated | team1 |  | -0.8273 | 20 | 0.3101 | -0.6608 | 1.315 | 0.95 |
| full field | 2015-2018 | chop_ungated | team2 |  | -1.241 | 20 | -0.3141 | -1.241 | 0.981 | 1 |


### random-entry

| scope | step | book | budget | members | real | n_draws | null_mean | null_p5 | null_p95 | p_one_sided |
|---|---|---|---|---|---|---|---|---|---|---|
| sample 16 | 2011-2014 | allon | team1 | 16 | -0.2185 | 3 | 0.3212 | -0.6827 | 1.55 | 0.6667 |
| sample 16 | 2011-2014 | allon | team2 | 16 | -0.3278 | 3 | 0.4818 | -1.024 | 2.325 | 0.6667 |
| sample 16 | 2011-2014 | chop_notrange | team1 | 16 | -0.623 | 3 | 0.1383 | 0 | 0.3733 | 1 |
| sample 16 | 2011-2014 | chop_notrange | team2 | 16 | -0.9346 | 3 | 0.2074 | 0 | 0.5599 | 1 |
| sample 16 | 2011-2014 | chop_trend | team1 | 16 | -0.4443 | 3 | 0.0009423 | -0.3419 | 0.3445 | 1 |
| sample 16 | 2011-2014 | chop_trend | team2 | 16 | -0.6664 | 3 | 0.001413 | -0.5129 | 0.5167 | 1 |
| sample 16 | 2011-2014 | chop_ungated | team1 | 16 | -0.2474 | 3 | -0.6461 | -1.314 | 0.2866 | 0.3333 |
| sample 16 | 2011-2014 | chop_ungated | team2 | 16 | -0.3712 | 3 | -0.9691 | -1.971 | 0.4299 | 0.3333 |
| sample 16 | 2012-2015 | allon | team1 | 16 | -1.989 | 3 | -0.1937 | -0.9283 | 0.4052 | 1 |
| sample 16 | 2012-2015 | allon | team2 | 16 | -2.983 | 3 | -0.2906 | -1.392 | 0.6078 | 1 |
| sample 16 | 2012-2015 | chop_notrange | team1 | 16 | -2.095 | 3 | -0.06156 | -0.9294 | 0.7632 | 1 |
| sample 16 | 2012-2015 | chop_notrange | team2 | 16 | -3.143 | 3 | -0.09234 | -1.394 | 1.145 | 1 |
| sample 16 | 2012-2015 | chop_trend | team1 | 16 | -1.89 | 3 | -0.2749 | -0.926 | 0.1837 | 1 |
| sample 16 | 2012-2015 | chop_trend | team2 | 16 | -2.835 | 3 | -0.4124 | -1.389 | 0.2755 | 1 |
| sample 16 | 2012-2015 | chop_ungated | team1 | 16 | -1.962 | 3 | -0.6778 | -1.871 | 0.3221 | 0.6667 |
| sample 16 | 2012-2015 | chop_ungated | team2 | 16 | -2.943 | 3 | -1.017 | -2.807 | 0.4831 | 0.6667 |
| sample 16 | 2013-2016 | allon | team1 | 16 | 0.6946 | 3 | 0.1351 | -0.05254 | 0.4172 | 0 |
| sample 16 | 2013-2016 | allon | team2 | 16 | 1.042 | 3 | 0.2026 | -0.07881 | 0.6259 | 0 |
| sample 16 | 2013-2016 | chop_notrange | team1 | 16 | 0.4982 | 3 | -0.07399 | -0.1839 | -0.00198 | 0 |
| sample 16 | 2013-2016 | chop_notrange | team2 | 16 | 0.7474 | 3 | -0.111 | -0.2759 | -0.00297 | 0 |
| sample 16 | 2013-2016 | chop_trend | team1 | 16 | 0.1478 | 3 | -0.1845 | -0.6114 | 0.1132 | 0 |
| sample 16 | 2013-2016 | chop_trend | team2 | 16 | 0.2218 | 3 | -0.2768 | -0.9171 | 0.1699 | 0 |
| sample 16 | 2013-2016 | chop_ungated | team1 | 16 | 0.08378 | 3 | -0.4965 | -0.9898 | -0.04385 | 0 |
| sample 16 | 2013-2016 | chop_ungated | team2 | 16 | 0.1257 | 3 | -0.7448 | -1.485 | -0.06578 | 0 |
| sample 16 | 2014-2017 | allon | team1 | 16 | -2.938 | 2 | -0.3624 | -0.6885 | -0.03624 | 1 |
| sample 16 | 2014-2017 | allon | team2 | 16 | -4.407 | 2 | -0.5436 | -1.033 | -0.05436 | 1 |
| sample 16 | 2014-2017 | chop_notrange | team1 | 16 | -0.9127 | 2 | -0.07319 | -0.1391 | -0.007319 | 1 |
| sample 16 | 2014-2017 | chop_notrange | team2 | 16 | -1.369 | 2 | -0.1098 | -0.2086 | -0.01098 | 1 |
| sample 16 | 2014-2017 | chop_trend | team1 | 16 | -1.011 | 2 | 0 | 0 | 0 | 1 |
| sample 16 | 2014-2017 | chop_trend | team2 | 16 | -1.516 | 2 | 0 | 0 | 0 | 1 |
| sample 16 | 2014-2017 | chop_ungated | team1 | 16 | -1.193 | 2 | 0 | 0 | 0 | 1 |
| sample 16 | 2014-2017 | chop_ungated | team2 | 16 | -1.79 | 2 | 0 | 0 | 0 | 1 |
| sample 16 | 2015-2018 | allon | team1 | 16 | -0.2781 | 1 | 0 | 0 | 0 | 1 |
| sample 16 | 2015-2018 | allon | team2 | 16 | -0.4172 | 1 | 0 | 0 | 0 | 1 |
| sample 16 | 2015-2018 | chop_notrange | team1 | 16 | -0.05585 | 1 | 0 | 0 | 0 | 1 |
| sample 16 | 2015-2018 | chop_notrange | team2 | 16 | -0.08378 | 1 | 0 | 0 | 0 | 1 |
| sample 16 | 2015-2018 | chop_trend | team1 | 16 | -0.7235 | 1 | -1.114 | -1.114 | -1.114 | 0 |
| sample 16 | 2015-2018 | chop_trend | team2 | 16 | -1.085 | 1 | -1.671 | -1.671 | -1.671 | 0 |
| sample 16 | 2015-2018 | chop_ungated | team1 | 16 | -0.6577 | 1 | 0 | 0 | 0 | 1 |
| sample 16 | 2015-2018 | chop_ungated | team2 | 16 | -0.9865 | 1 | 0 | 0 | 0 | 1 |


### shuffle

| scope | step | book | budget | members | real | n_draws | null_mean | null_p5 | null_p95 | p_one_sided |
|---|---|---|---|---|---|---|---|---|---|---|
| sample 16 | 2011-2014 | allon | team1 | 16 | -0.2185 | 3 | -0.2185 | -0.2185 | -0.2185 | 1 |
| sample 16 | 2011-2014 | allon | team2 | 16 | -0.3278 | 3 | -0.3278 | -0.3278 | -0.3278 | 1 |
| sample 16 | 2011-2014 | chop_notrange | team1 | 16 | -0.623 | 3 | -0.3692 | -0.6153 | -0.1809 | 0.6667 |
| sample 16 | 2011-2014 | chop_notrange | team2 | 16 | -0.9346 | 3 | -0.5537 | -0.9229 | -0.2713 | 0.6667 |
| sample 16 | 2011-2014 | chop_trend | team1 | 16 | -0.4443 | 3 | -0.5794 | -1.48 | 0.1795 | 0.6667 |
| sample 16 | 2011-2014 | chop_trend | team2 | 16 | -0.6664 | 3 | -0.8691 | -2.22 | 0.2692 | 0.6667 |
| sample 16 | 2011-2014 | chop_ungated | team1 | 16 | -0.2474 | 3 | -0.06954 | -0.5457 | 0.4725 | 0.6667 |
| sample 16 | 2011-2014 | chop_ungated | team2 | 16 | -0.3712 | 3 | -0.1043 | -0.8185 | 0.7087 | 0.6667 |
| sample 16 | 2012-2015 | allon | team1 | 16 | -1.989 | 3 | -1.989 | -1.989 | -1.989 | 1 |
| sample 16 | 2012-2015 | allon | team2 | 16 | -2.983 | 3 | -2.983 | -2.983 | -2.983 | 1 |
| sample 16 | 2012-2015 | chop_notrange | team1 | 16 | -2.095 | 3 | -1.706 | -1.846 | -1.607 | 1 |
| sample 16 | 2012-2015 | chop_notrange | team2 | 16 | -3.143 | 3 | -2.559 | -2.769 | -2.41 | 1 |
| sample 16 | 2012-2015 | chop_trend | team1 | 16 | -1.89 | 3 | -1.658 | -2.142 | -1.347 | 0.6667 |
| sample 16 | 2012-2015 | chop_trend | team2 | 16 | -2.835 | 3 | -2.487 | -3.213 | -2.021 | 0.6667 |
| sample 16 | 2012-2015 | chop_ungated | team1 | 16 | -1.962 | 3 | -2.048 | -2.298 | -1.663 | 0.3333 |
| sample 16 | 2012-2015 | chop_ungated | team2 | 16 | -2.943 | 3 | -3.073 | -3.447 | -2.495 | 0.3333 |
| sample 16 | 2013-2016 | allon | team1 | 16 | 0.6946 | 3 | 0.6946 | 0.6946 | 0.6946 | 1 |
| sample 16 | 2013-2016 | allon | team2 | 16 | 1.042 | 3 | 1.042 | 1.042 | 1.042 | 1 |
| sample 16 | 2013-2016 | chop_notrange | team1 | 16 | 0.4982 | 3 | -0.2977 | -0.7043 | -0.01243 | 0 |
| sample 16 | 2013-2016 | chop_notrange | team2 | 16 | 0.7474 | 3 | -0.4465 | -1.057 | -0.01864 | 0 |
| sample 16 | 2013-2016 | chop_trend | team1 | 16 | 0.1478 | 3 | 0.3015 | -0.03035 | 0.8445 | 0.3333 |
| sample 16 | 2013-2016 | chop_trend | team2 | 16 | 0.2218 | 3 | 0.4523 | -0.04553 | 1.267 | 0.3333 |
| sample 16 | 2013-2016 | chop_ungated | team1 | 16 | 0.08378 | 3 | -0.00372 | -0.07676 | 0.0521 | 0 |
| sample 16 | 2013-2016 | chop_ungated | team2 | 16 | 0.1257 | 3 | -0.00558 | -0.1151 | 0.07815 | 0 |
| sample 16 | 2014-2017 | allon | team1 | 16 | -2.938 | 3 | -2.938 | -2.938 | -2.938 | 1 |
| sample 16 | 2014-2017 | allon | team2 | 16 | -4.407 | 3 | -4.407 | -4.407 | -4.407 | 1 |
| sample 16 | 2014-2017 | chop_notrange | team1 | 16 | -0.9127 | 3 | -1.053 | -1.872 | -0.1215 | 0.3333 |
| sample 16 | 2014-2017 | chop_notrange | team2 | 16 | -1.369 | 3 | -1.58 | -2.808 | -0.1823 | 0.3333 |
| sample 16 | 2014-2017 | chop_trend | team1 | 16 | -1.011 | 3 | -1.494 | -1.681 | -1.33 | 0 |
| sample 16 | 2014-2017 | chop_trend | team2 | 16 | -1.516 | 3 | -2.241 | -2.522 | -1.996 | 0 |
| sample 16 | 2014-2017 | chop_ungated | team1 | 16 | -1.193 | 3 | -0.8611 | -1.289 | -0.5435 | 0.6667 |
| sample 16 | 2014-2017 | chop_ungated | team2 | 16 | -1.79 | 3 | -1.292 | -1.933 | -0.8153 | 0.6667 |
| sample 16 | 2015-2018 | allon | team1 | 16 | -0.2781 | 3 | -0.2781 | -0.2781 | -0.2781 | 1 |
| sample 16 | 2015-2018 | allon | team2 | 16 | -0.4172 | 3 | -0.4172 | -0.4172 | -0.4172 | 1 |
| sample 16 | 2015-2018 | chop_notrange | team1 | 16 | -0.05585 | 3 | -0.2267 | -0.4384 | -0.02169 | 0.3333 |
| sample 16 | 2015-2018 | chop_notrange | team2 | 16 | -0.08378 | 3 | -0.34 | -0.6577 | -0.03254 | 0.3333 |
| sample 16 | 2015-2018 | chop_trend | team1 | 16 | -0.7235 | 3 | -0.396 | -1.213 | 0.1434 | 0.6667 |
| sample 16 | 2015-2018 | chop_trend | team2 | 16 | -1.085 | 3 | -0.594 | -1.819 | 0.2151 | 0.6667 |
| sample 16 | 2015-2018 | chop_ungated | team1 | 16 | -0.6577 | 3 | -0.1275 | -0.4092 | 0.1068 | 1 |
| sample 16 | 2015-2018 | chop_ungated | team2 | 16 | -0.9865 | 3 | -0.1913 | -0.6138 | 0.1602 | 1 |


**Is the p-value stable in the sample size?** Same (null, step, book, budget) at 5,000 and at 20,000:

| null | step | book | budget | sample 16 |
|---|---|---|---|---|
| random-entry | 2011-2014 | allon | team1 | 0.6667 |
| random-entry | 2011-2014 | allon | team2 | 0.6667 |
| random-entry | 2011-2014 | chop_notrange | team1 | 1 |
| random-entry | 2011-2014 | chop_notrange | team2 | 1 |
| random-entry | 2011-2014 | chop_trend | team1 | 1 |
| random-entry | 2011-2014 | chop_trend | team2 | 1 |
| random-entry | 2011-2014 | chop_ungated | team1 | 0.3333 |
| random-entry | 2011-2014 | chop_ungated | team2 | 0.3333 |
| random-entry | 2012-2015 | allon | team1 | 1 |
| random-entry | 2012-2015 | allon | team2 | 1 |
| random-entry | 2012-2015 | chop_notrange | team1 | 1 |
| random-entry | 2012-2015 | chop_notrange | team2 | 1 |
| random-entry | 2012-2015 | chop_trend | team1 | 1 |
| random-entry | 2012-2015 | chop_trend | team2 | 1 |
| random-entry | 2012-2015 | chop_ungated | team1 | 0.6667 |
| random-entry | 2012-2015 | chop_ungated | team2 | 0.6667 |
| random-entry | 2013-2016 | allon | team1 | 0 |
| random-entry | 2013-2016 | allon | team2 | 0 |
| random-entry | 2013-2016 | chop_notrange | team1 | 0 |
| random-entry | 2013-2016 | chop_notrange | team2 | 0 |
| random-entry | 2013-2016 | chop_trend | team1 | 0 |
| random-entry | 2013-2016 | chop_trend | team2 | 0 |
| random-entry | 2013-2016 | chop_ungated | team1 | 0 |
| random-entry | 2013-2016 | chop_ungated | team2 | 0 |
| random-entry | 2014-2017 | allon | team1 | 1 |
| random-entry | 2014-2017 | allon | team2 | 1 |
| random-entry | 2014-2017 | chop_notrange | team1 | 1 |
| random-entry | 2014-2017 | chop_notrange | team2 | 1 |
| random-entry | 2014-2017 | chop_trend | team1 | 1 |
| random-entry | 2014-2017 | chop_trend | team2 | 1 |
| random-entry | 2014-2017 | chop_ungated | team1 | 1 |
| random-entry | 2014-2017 | chop_ungated | team2 | 1 |
| random-entry | 2015-2018 | allon | team1 | 1 |
| random-entry | 2015-2018 | allon | team2 | 1 |
| random-entry | 2015-2018 | chop_notrange | team1 | 1 |
| random-entry | 2015-2018 | chop_notrange | team2 | 1 |
| random-entry | 2015-2018 | chop_trend | team1 | 0 |
| random-entry | 2015-2018 | chop_trend | team2 | 0 |
| random-entry | 2015-2018 | chop_ungated | team1 | 1 |
| random-entry | 2015-2018 | chop_ungated | team2 | 1 |
| shuffle | 2011-2014 | allon | team1 | 1 |
| shuffle | 2011-2014 | allon | team2 | 1 |
| shuffle | 2011-2014 | chop_notrange | team1 | 0.6667 |
| shuffle | 2011-2014 | chop_notrange | team2 | 0.6667 |
| shuffle | 2011-2014 | chop_trend | team1 | 0.6667 |
| shuffle | 2011-2014 | chop_trend | team2 | 0.6667 |
| shuffle | 2011-2014 | chop_ungated | team1 | 0.6667 |
| shuffle | 2011-2014 | chop_ungated | team2 | 0.6667 |
| shuffle | 2012-2015 | allon | team1 | 1 |
| shuffle | 2012-2015 | allon | team2 | 1 |
| shuffle | 2012-2015 | chop_notrange | team1 | 1 |
| shuffle | 2012-2015 | chop_notrange | team2 | 1 |
| shuffle | 2012-2015 | chop_trend | team1 | 0.6667 |
| shuffle | 2012-2015 | chop_trend | team2 | 0.6667 |
| shuffle | 2012-2015 | chop_ungated | team1 | 0.3333 |
| shuffle | 2012-2015 | chop_ungated | team2 | 0.3333 |
| shuffle | 2013-2016 | allon | team1 | 1 |
| shuffle | 2013-2016 | allon | team2 | 1 |
| shuffle | 2013-2016 | chop_notrange | team1 | 0 |
| shuffle | 2013-2016 | chop_notrange | team2 | 0 |
| shuffle | 2013-2016 | chop_trend | team1 | 0.3333 |
| shuffle | 2013-2016 | chop_trend | team2 | 0.3333 |
| shuffle | 2013-2016 | chop_ungated | team1 | 0 |
| shuffle | 2013-2016 | chop_ungated | team2 | 0 |
| shuffle | 2014-2017 | allon | team1 | 1 |
| shuffle | 2014-2017 | allon | team2 | 1 |
| shuffle | 2014-2017 | chop_notrange | team1 | 0.3333 |
| shuffle | 2014-2017 | chop_notrange | team2 | 0.3333 |
| shuffle | 2014-2017 | chop_trend | team1 | 0 |
| shuffle | 2014-2017 | chop_trend | team2 | 0 |
| shuffle | 2014-2017 | chop_ungated | team1 | 0.6667 |
| shuffle | 2014-2017 | chop_ungated | team2 | 0.6667 |
| shuffle | 2015-2018 | allon | team1 | 1 |
| shuffle | 2015-2018 | allon | team2 | 1 |
| shuffle | 2015-2018 | chop_notrange | team1 | 0.3333 |
| shuffle | 2015-2018 | chop_notrange | team2 | 0.3333 |
| shuffle | 2015-2018 | chop_trend | team1 | 0.6667 |
| shuffle | 2015-2018 | chop_trend | team2 | 0.6667 |
| shuffle | 2015-2018 | chop_ungated | team1 | 1 |
| shuffle | 2015-2018 | chop_ungated | team2 | 1 |


## THE BLIND GRADE — reported, never used

From `results/r2gate2/modeA_books_blindgrade.csv`. Year 5 of each step is graded by the tuner's own objective but was never seen by the tuner and gates nothing.

| step | stream | n_eligible | n_graded_pass | n_graded_fail | trade_R_graded_pass | trade_R_graded_fail | spearman_grade_to_trade | p |
|---|---|---|---|---|---|---|---|---|
| 2011-2014 | trend-routed | 268,733 | 134,799 | 133,735 | -0.02353 | -0.03091 | 0.02431 | 1.958e-36 |
| 2011-2014 | trend-allon | 273,628 | 142,118 | 131,150 | -0.02462 | -0.03382 | 0.09436 | 0 |
| 2011-2014 | chop-routed | 253,091 | 151,665 | 101,201 | -0.07244 | -0.03871 | -0.1034 | 0 |
| 2011-2014 | chop-allon | 272,293 | 122,004 | 150,263 | -0.02489 | -0.03541 | 0.06879 | 8.045e-283 |
| 2012-2015 | trend-routed | 269,914 | 103,546 | 164,635 | -0.05244 | -0.04308 | -0.08044 | 0 |
| 2012-2015 | trend-allon | 273,443 | 92,982 | 180,231 | -0.04543 | -0.04072 | -0.0557 | 8.902e-187 |
| 2012-2015 | chop-routed | 250,041 | 80,554 | 169,471 | -0.04737 | -0.05322 | 0.03952 | 5.376e-87 |
| 2012-2015 | chop-allon | 272,402 | 96,677 | 175,618 | -0.04562 | -0.05425 | -0.02735 | 3.061e-46 |
| 2013-2016 | trend-routed | 269,308 | 73,222 | 186,179 | 0.02003 | -0.02615 | 0.1349 | 0 |
| 2013-2016 | trend-allon | 272,773 | 69,059 | 192,198 | 0.01235 | -0.004268 | 0.1096 | 0 |
| 2013-2016 | chop-routed | 252,434 | 92,737 | 157,785 | 0.02832 | 0.05013 | -0.06811 | 3.195e-257 |
| 2013-2016 | chop-allon | 272,522 | 89,628 | 171,600 | 0.04533 | 0.006975 | 0.1562 | 0 |
| 2014-2017 | trend-routed | 267,723 | 121,606 | 140,754 | -0.08349 | -0.09945 | 0.04364 | 5.166e-113 |
| 2014-2017 | trend-allon | 273,598 | 140,457 | 131,889 | -0.06177 | -0.0691 | 0.05387 | 6.344e-175 |
| 2014-2017 | chop-routed | 253,684 | 148,889 | 104,584 | -0.103 | -0.0908 | -0.03862 | 2.555e-84 |
| 2014-2017 | chop-allon | 272,294 | 155,619 | 114,917 | -0.0893 | -0.09616 | 0.03883 | 2.335e-91 |
| 2015-2018 | trend-routed | 264,418 | 59,397 | 198,701 | -0.03729 | -0.05488 | 0.111 | 0 |
| 2015-2018 | trend-allon | 273,595 | 55,255 | 218,066 | -0.03395 | -0.03398 | 0.04416 | 3.769e-118 |
| 2015-2018 | chop-routed | 254,091 | 57,430 | 196,661 | -0.02568 | -0.02925 | 0.04377 | 5.898e-108 |
| 2015-2018 | chop-allon | 272,179 | 66,167 | 205,897 | -0.0595 | -0.06758 | 0.04771 | 6.929e-137 |


## THE TWO LAYER 1 SPLITS — reported, gate nothing

From `results/r2gate2/modeA_books_layer1splits.csv`.


### episode_third

| scope | step | quality_tag | third | total_R | mean_R_per_mark | mark_rows |
|---|---|---|---|---|---|---|
| routed trend, sample 40 | 2011-2014 |  | first | -10.14 | -0.001014 | 9,999 |
| routed trend, sample 40 | 2011-2014 |  | last | -7.192 | -0.01405 | 512 |
| routed trend, sample 40 | 2011-2014 |  | middle | -25.38 | -0.01911 | 1,328 |
| routed trend, sample 40 | 2012-2015 |  | first | -31.2 | -0.003455 | 9,028 |
| routed trend, sample 40 | 2012-2015 |  | last | -7.146 | -0.003464 | 2,063 |
| routed trend, sample 40 | 2012-2015 |  | middle | -56.91 | -0.007389 | 7,702 |
| routed trend, sample 40 | 2013-2016 |  | first | -36.24 | -0.01527 | 2,373 |
| routed trend, sample 40 | 2013-2016 |  | last | 9.823 | 0.001912 | 5,138 |
| routed trend, sample 40 | 2013-2016 |  | middle | -81.6 | -0.01154 | 7,070 |
| routed trend, sample 40 | 2014-2017 |  | first | -87.27 | -0.02474 | 3,527 |
| routed trend, sample 40 | 2014-2017 |  | last | -54.55 | -0.01033 | 5,281 |
| routed trend, sample 40 | 2014-2017 |  | middle | -99.92 | -0.02309 | 4,328 |
| routed trend, sample 40 | 2015-2018 |  | first | -23.8 | -0.0425 | 560 |
| routed trend, sample 40 | 2015-2018 |  | last | -122.1 | -0.009795 | 12,470 |
| routed trend, sample 40 | 2015-2018 |  | middle | -43.28 | -0.008575 | 5,047 |


### quality_tag

| scope | step | quality_tag | third | total_R | mean_R_per_mark | mark_rows |
|---|---|---|---|---|---|---|
| routed trend, sample 40 | 2011-2014 | high |  | -20.14 | -0.002648 | 7,605 |
| routed trend, sample 40 | 2011-2014 | low |  | -22.58 | -0.005333 | 4,234 |
| routed trend, sample 40 | 2011-2014 |  |  | 10.76 | 0.004153 | 2,592 |
| routed trend, sample 40 | 2012-2015 | high |  | -187.6 | -0.02317 | 8,099 |
| routed trend, sample 40 | 2012-2015 | low |  | 92.36 | 0.008637 | 10,694 |
| routed trend, sample 40 | 2012-2015 |  |  | -16.46 | -0.005024 | 3,276 |
| routed trend, sample 40 | 2013-2016 | high |  | -88.99 | -0.03279 | 2,714 |
| routed trend, sample 40 | 2013-2016 | low |  | -19.03 | -0.001603 | 11,867 |
| routed trend, sample 40 | 2013-2016 |  |  | 5.142 | 0.001683 | 3,055 |
| routed trend, sample 40 | 2014-2017 | high |  | -98.25 | -0.03014 | 3,260 |
| routed trend, sample 40 | 2014-2017 | low |  | -143.5 | -0.01453 | 9,876 |
| routed trend, sample 40 | 2014-2017 |  |  | -10.94 | -0.00359 | 3,046 |
| routed trend, sample 40 | 2015-2018 | high |  | -196.5 | -0.03051 | 6,441 |
| routed trend, sample 40 | 2015-2018 | low |  | 7.308 | 0.0006281 | 11,636 |
| routed trend, sample 40 | 2015-2018 |  |  | 72.71 | 0.01736 | 4,188 |


## WHAT GATE 1 SAID, for context

From `results/r2gate1_pooled_modeA_full.csv`: trade-year expectancy over the whole eligible population, by stream.

| stream | n_eligible | trade_R_pass |
|---|---|---|
| trend-routed | 242,647 | -0.03996 |
| trend-allon | 264,899 | -0.03572 |
| chop-routed | 205,732 | -0.04955 |
| chop-allon | 251,747 | -0.04715 |


And the gate 1 regime-shuffle null, from `results/r2gate1_shufflenull_modeA.csv`:

| slice | stream | top_pct | real_trade_R | surrogate_mean | p_one_sided |
|---|---|---|---|---|---|
| trend | routed | 0.1 | 0.01902 | 0.01785 | 0.4545 |
| trend | routed | 1 | 0.01902 | 0.01785 | 0.4545 |
| trend | routed | 10 | 0.02863 | -0.01233 | 0 |
| trend | routed | 50 | -0.01769 | -0.01596 | 0.6364 |
| chop | routed | 0.1 | 0.1246 | 0.008325 | 0.2727 |
| chop | routed | 1 | 0.1246 | 0.008325 | 0.2727 |
| chop | routed | 10 | 0.008984 | 0.03262 | 0.6364 |
| chop | routed | 50 | -0.008044 | -0.009278 | 0.4545 |


## WHAT IS NOT IN THIS REPORT

- **Full-field random-entry and regime-shuffle nulls.** Run here on stratified samples at two sizes. At the measured 0.48 s per strategy per draw the full field is a multi-day job; it is registered in HANDOFF 0l as the clean run to do later.

- **Any number not read from the files listed above.** Nothing here is restated from memory.
