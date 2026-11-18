# MODE A — THE HONEST GATE 2, ALL 273,780 STRATEGIES

Generated 2026-11-18 11:06 by `code/l2r2modearep.py`. **Every number below was read out of a file in this run and the file is named beside it.** A section whose source is missing says so and is left empty.


## The files this report is built from

| section | file | rows | md5 | mtime |
|---|---|---|---|---|
| books | results/r2gate2/modeA_books_full.csv | 40 | d8b75ab8b54d | 2026-11-18 10:52 |
| grade | results/r2gate2/modeA_books_blindgrade.csv | 20 | 653dbb5e2a06 | 2026-11-18 09:47 |
| splits | results/r2gate2/modeA_books_layer1splits.csv | 30 | e7bf6d6c82c5 | 2026-11-18 09:52 |
| gate1 | results/r2gate1_pooled_modeA_full.csv | 480 | a6ea66a717e6 | 2026-11-16 18:16 |
| rankcorr | results/r2gate1_rankcorr_modeA_full.csv | 20 | 051f11bae2c2 | 2026-11-16 18:15 |
| grid | results/r2gate2_grid.csv | 6 | 85045a1adf2e | 2026-11-17 09:57 |
| cond1 | results/r2gate2_cond1_modeA.csv | 1 | 0f7083cdfc9e | 2026-11-17 09:58 |
| cond2 | results/r2gate2_cond2_modeA.csv | 7,660 | 7dfaded49155 | 2026-11-17 11:54 |
| streamed | results/r2book_series_equals_shipped_modeA.csv | 2 | 8940571fda48 | 2026-11-17 20:35 |
| shuffle1 | results/r2gate1_shufflenull_modeA.csv | 16 | 291541298c86 | 2026-11-16 18:53 |
| manifest | results/layer1_interface_manifest_2026-11-16.csv | 16 | f6582570eeb5 | 2026-11-16 14:19 |


**Missing sources, left empty rather than filled in:** nulls


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

From `results/r2gate2/modeA_books_full.csv`, 40 rows = 5 steps x 4 books x 2 budgets.


### Trade-year median, by book and budget, pooled over the five steps

| book | budget | steps | median_of_trade_medians | worst_step | best_step | median_dip95 | median_PF | median_retention | steps_flagged_FIT |
|---|---|---|---|---|---|---|---|---|---|
| allon | team1 | 5 | -1.187 | -2.558 | 0.6139 | 3.613 | 0.8995 | -0.2844 | 5 |
| allon | team2 | 5 | -1.781 | -3.838 | 0.9209 | 5.42 | 0.8995 | -0.2844 | 5 |
| chop_notrange | team1 | 5 | -0.5891 | -2.104 | -0.1455 | 2.868 | 0.9376 | -0.2442 | 5 |
| chop_notrange | team2 | 5 | -0.8837 | -3.156 | -0.2183 | 4.301 | 0.9376 | -0.2442 | 5 |
| chop_trend | team1 | 5 | -0.9068 | -1.718 | 0.6639 | 2.903 | 0.9062 | -0.4028 | 4 |
| chop_trend | team2 | 5 | -1.36 | -2.577 | 0.9958 | 4.355 | 0.9062 | -0.4028 | 4 |
| chop_ungated | team1 | 5 | -0.5357 | -1.762 | 0.2426 | 2.89 | 0.9505 | -0.1513 | 5 |
| chop_ungated | team2 | 5 | -0.8036 | -2.643 | 0.3639 | 4.335 | 0.9505 | -0.1513 | 5 |


### Every step, every book, team1 budget

| step | book | size_scale | scale_binds | build_median_year_pct | trade_median_year_pct | trade_dip95_pct | trade_max_dd_pct | trade_profit_factor | retention | FIT |
|---|---|---|---|---|---|---|---|---|---|---|
| 2011-2014 | allon | 0.6122 | DIP95 | 3.961 | 0.6139 | 3.318 | 1.588 | 1.052 | 0.155 | 1 |
| 2011-2014 | chop_notrange | 0.5774 | DIP95 | 2.412 | -0.5891 | 2.868 | 2.116 | 0.9376 | -0.2442 | 1 |
| 2011-2014 | chop_trend | 0.5675 | DIP95 | 4.264 | -1.718 | 4.026 | 2.917 | 0.8569 | -0.4028 | 1 |
| 2011-2014 | chop_ungated | 0.6377 | DIP95 | 3.54 | -0.5357 | 3.111 | 2.599 | 0.9505 | -0.1513 | 1 |
| 2012-2015 | allon | 0.5935 | DIP95 | 5.061 | -1.233 | 3.693 | 2.125 | 0.8995 | -0.2435 | 1 |
| 2012-2015 | chop_notrange | 0.5537 | DIP95 | 2.867 | -2.104 | 3.657 | 2.125 | 0.8018 | -0.7339 | 1 |
| 2012-2015 | chop_trend | 0.4778 | DIP95 | 3.644 | -0.9068 | 2.903 | 1.422 | 0.9062 | -0.2488 | 1 |
| 2012-2015 | chop_ungated | 0.546 | DIP95 | 2.953 | -0.65 | 2.89 | 1.266 | 0.937 | -0.2201 | 1 |
| 2013-2016 | allon | 0.4807 | DIP95 | 3.549 | -1.01 | 3.218 | 2.247 | 0.9026 | -0.2844 | 1 |
| 2013-2016 | chop_notrange | 0.5193 | DIP95 | 1.838 | -0.3925 | 2.303 | 1.364 | 0.9529 | -0.2135 | 1 |
| 2013-2016 | chop_trend | 0.4243 | DIP95 | 0.5631 | 0.6639 | 1.549 | 0.9816 | 1.094 | 1.179 | 0 |
| 2013-2016 | chop_ungated | 0.464 | DIP95 | 1.425 | 0.2426 | 2.195 | 1.529 | 1.028 | 0.1703 | 1 |
| 2014-2017 | allon | 0.5486 | DIP95 | 2.661 | -2.558 | 4.462 | 3.247 | 0.7862 | -0.9614 | 1 |
| 2014-2017 | chop_notrange | 0.5421 | DIP95 | 1.216 | -2.103 | 3.339 | 2.464 | 0.7711 | -1.73 | 1 |
| 2014-2017 | chop_trend | 0.4253 | DIP95 | 0.6947 | -1.686 | 3.165 | 2.399 | 0.8122 | -2.427 | 1 |
| 2014-2017 | chop_ungated | 0.4288 | DIP95 | 0.8101 | -1.762 | 3.4 | 2.296 | 0.8177 | -2.175 | 1 |
| 2015-2018 | allon | 0.5 | DIP95 | 2.584 | -1.187 | 3.613 | 2.633 | 0.8942 | -0.4595 | 1 |
| 2015-2018 | chop_notrange | 0.3829 | DIP95 | 0.6488 | -0.1455 | 2.311 | 1.39 | 0.9809 | -0.2243 | 1 |
| 2015-2018 | chop_trend | 0.4404 | DIP95 | 0.9124 | -0.7302 | 2.876 | 1.958 | 0.9218 | -0.8004 | 1 |
| 2015-2018 | chop_ungated | 0.465 | DIP95 | 1.192 | -0.1005 | 2.645 | 2.801 | 0.9888 | -0.08436 | 1 |


## THE THREE NULLS

_`modeA_books_nulls.csv` is absent; this section is empty._


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
| routed trend, sample 4000 | 2011-2014 |  | first | -5141 | -0.005345 | 961,817 |
| routed trend, sample 4000 | 2011-2014 |  | last | -711.3 | -0.01253 | 56,758 |
| routed trend, sample 4000 | 2011-2014 |  | middle | -1208 | -0.00764 | 158,083 |
| routed trend, sample 4000 | 2012-2015 |  | first | -2798 | -0.003861 | 724,566 |
| routed trend, sample 4000 | 2012-2015 |  | last | 323.7 | 0.001797 | 180,102 |
| routed trend, sample 4000 | 2012-2015 |  | middle | -5625 | -0.008664 | 649,299 |
| routed trend, sample 4000 | 2013-2016 |  | first | -3836 | -0.01724 | 222,439 |
| routed trend, sample 4000 | 2013-2016 |  | last | 2532 | 0.005151 | 491,481 |
| routed trend, sample 4000 | 2013-2016 |  | middle | -5822 | -0.009252 | 629,274 |
| routed trend, sample 4000 | 2014-2017 |  | first | -6753 | -0.02243 | 301,096 |
| routed trend, sample 4000 | 2014-2017 |  | last | -3651 | -0.008885 | 410,948 |
| routed trend, sample 4000 | 2014-2017 |  | middle | -8222 | -0.02329 | 353,007 |
| routed trend, sample 4000 | 2015-2018 |  | first | -570.5 | -0.01104 | 51,671 |
| routed trend, sample 4000 | 2015-2018 |  | last | -1.438e+04 | -0.01282 | 1,122,283 |
| routed trend, sample 4000 | 2015-2018 |  | middle | -5629 | -0.01193 | 471,916 |


### quality_tag

| scope | step | quality_tag | third | total_R | mean_R_per_mark | mark_rows |
|---|---|---|---|---|---|---|
| routed trend, sample 4000 | 2011-2014 | high |  | -1711 | -0.002287 | 748,357 |
| routed trend, sample 4000 | 2011-2014 | low |  | -5348 | -0.01249 | 428,301 |
| routed trend, sample 4000 | 2011-2014 |  |  | -307.6 | -0.001143 | 269,205 |
| routed trend, sample 4000 | 2012-2015 | high |  | -1.348e+04 | -0.02144 | 628,805 |
| routed trend, sample 4000 | 2012-2015 | low |  | 5381 | 0.005816 | 925,162 |
| routed trend, sample 4000 | 2012-2015 |  |  | -2373 | -0.009847 | 241,007 |
| routed trend, sample 4000 | 2013-2016 | high |  | -7342 | -0.03031 | 242,206 |
| routed trend, sample 4000 | 2013-2016 | low |  | 215.8 | 0.000196 | 1,100,988 |
| routed trend, sample 4000 | 2013-2016 |  |  | 897.5 | 0.003099 | 289,627 |
| routed trend, sample 4000 | 2014-2017 | high |  | -8286 | -0.03177 | 260,808 |
| routed trend, sample 4000 | 2014-2017 | low |  | -1.034e+04 | -0.01286 | 804,243 |
| routed trend, sample 4000 | 2014-2017 |  |  | 217.4 | 0.0008428 | 257,968 |
| routed trend, sample 4000 | 2015-2018 | high |  | -1.73e+04 | -0.0296 | 584,520 |
| routed trend, sample 4000 | 2015-2018 | low |  | -3279 | -0.00309 | 1,061,350 |
| routed trend, sample 4000 | 2015-2018 |  |  | 4899 | 0.01301 | 376,675 |


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
