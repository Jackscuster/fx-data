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

Generated 2026-11-18 12:50 by `code/l2r2modearep.py`. **Every number below was read out of a file in this run and the file is named beside it.** A section whose source is missing says so and is left empty.


## The files this report is built from

| section | file | rows | md5 | mtime |
|---|---|---|---|---|
| books | results/r2gate2/modeA_books_full.csv | 40 | d8b75ab8b54d | 2026-11-18 10:52 |
| nulls | results/r2gate2/modeA_books_nulls.csv | 200 | 6a0051f6e911 | 2026-11-18 12:50 |
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

From `results/r2gate2/modeA_books_nulls.csv`, 200 rows.


### identity

| scope | step | book | budget | members | real | n_draws | null_mean | null_p5 | null_p95 | p_one_sided |
|---|---|---|---|---|---|---|---|---|---|---|
| full field | 2011-2014 | allon | team1 |  | 0.6139 | 200 | 4.567 | 0.6139 | 9.412 | 1 |
| full field | 2011-2014 | allon | team2 |  | 0.9209 | 200 | 7.022 | 0.9209 | 14.12 | 1 |
| full field | 2011-2014 | chop_notrange | team1 |  | -0.5891 | 200 | 2.575 | -0.5891 | 5.348 | 1 |
| full field | 2011-2014 | chop_notrange | team2 |  | -0.8837 | 200 | 3.947 | -0.8837 | 8.021 | 1 |
| full field | 2011-2014 | chop_trend | team1 |  | -1.718 | 200 | 2.883 | -1.718 | 6.255 | 1 |
| full field | 2011-2014 | chop_trend | team2 |  | -2.577 | 200 | 4.817 | -2.577 | 9.382 | 0.855 |
| full field | 2011-2014 | chop_ungated | team1 |  | -0.5357 | 200 | 2.173 | -0.5357 | 5.55 | 1 |
| full field | 2011-2014 | chop_ungated | team2 |  | -0.8036 | 200 | 2.817 | -0.8036 | 8.326 | 1 |
| full field | 2012-2015 | allon | team1 |  | -1.233 | 200 | 3.661 | -1.233 | 7.745 | 0.885 |
| full field | 2012-2015 | allon | team2 |  | -1.849 | 200 | 5.071 | -1.849 | 11.62 | 0.825 |
| full field | 2012-2015 | chop_notrange | team1 |  | -2.104 | 200 | 2.134 | -2.104 | 5.513 | 1 |
| full field | 2012-2015 | chop_notrange | team2 |  | -3.156 | 200 | 2.26 | -3.156 | 8.269 | 1 |
| full field | 2012-2015 | chop_trend | team1 |  | -0.9068 | 200 | 1.955 | -1.045 | 6.068 | 0.685 |
| full field | 2012-2015 | chop_trend | team2 |  | -1.36 | 200 | 2.99 | -1.568 | 9.102 | 0.725 |
| full field | 2012-2015 | chop_ungated | team1 |  | -0.65 | 200 | 1.496 | -0.65 | 4.955 | 1 |
| full field | 2012-2015 | chop_ungated | team2 |  | -0.975 | 200 | 2.216 | -0.975 | 7.432 | 1 |
| full field | 2013-2016 | allon | team1 |  | -1.01 | 200 | 2.515 | -1.462 | 6.672 | 0.855 |
| full field | 2013-2016 | allon | team2 |  | -1.514 | 200 | 3.21 | -2.193 | 10.01 | 0.615 |
| full field | 2013-2016 | chop_notrange | team1 |  | -0.3925 | 200 | 1.619 | -1.067 | 4.313 | 0.87 |
| full field | 2013-2016 | chop_notrange | team2 |  | -0.5887 | 200 | 1.969 | -1.6 | 6.469 | 0.63 |
| full field | 2013-2016 | chop_trend | team1 |  | 0.6639 | 200 | 1.1 | -1.128 | 3.625 | 0.35 |
| full field | 2013-2016 | chop_trend | team2 |  | 0.9958 | 200 | 1.336 | -1.693 | 5.438 | 0.305 |
| full field | 2013-2016 | chop_ungated | team1 |  | 0.2426 | 200 | 1.533 | -0.6113 | 4.866 | 0.705 |
| full field | 2013-2016 | chop_ungated | team2 |  | 0.3639 | 200 | 2.173 | -0.917 | 7.299 | 0.47 |
| full field | 2014-2017 | allon | team1 |  | -2.558 | 200 | 2.529 | -2.558 | 6.512 | 1 |
| full field | 2014-2017 | allon | team2 |  | -3.838 | 200 | 3.694 | -3.838 | 9.768 | 1 |
| full field | 2014-2017 | chop_notrange | team1 |  | -2.103 | 200 | 1.05 | -2.103 | 4.312 | 0.86 |
| full field | 2014-2017 | chop_notrange | team2 |  | -3.155 | 200 | 1.905 | -3.155 | 6.469 | 0.87 |
| full field | 2014-2017 | chop_trend | team1 |  | -1.686 | 200 | 0.7535 | -1.686 | 4.616 | 1 |
| full field | 2014-2017 | chop_trend | team2 |  | -2.529 | 200 | 1.377 | -2.529 | 6.924 | 1 |
| full field | 2014-2017 | chop_ungated | team1 |  | -1.762 | 200 | 0.84 | -1.762 | 4.89 | 1 |
| full field | 2014-2017 | chop_ungated | team2 |  | -2.643 | 200 | 1.571 | -2.643 | 7.336 | 0.83 |
| full field | 2015-2018 | allon | team1 |  | -1.187 | 200 | 1.798 | -2.633 | 5.42 | 0.65 |
| full field | 2015-2018 | allon | team2 |  | -1.781 | 200 | 2.767 | -3.95 | 8.131 | 0.845 |
| full field | 2015-2018 | chop_notrange | team1 |  | -0.1455 | 200 | 0.5655 | -1.61 | 3.567 | 0.68 |
| full field | 2015-2018 | chop_notrange | team2 |  | -0.2183 | 200 | 1.03 | -2.415 | 5.351 | 0.675 |
| full field | 2015-2018 | chop_trend | team1 |  | -0.7302 | 200 | 1.222 | -2.014 | 5.341 | 0.815 |
| full field | 2015-2018 | chop_trend | team2 |  | -1.095 | 200 | 1.878 | -3.022 | 8.011 | 0.84 |
| full field | 2015-2018 | chop_ungated | team1 |  | -0.1005 | 200 | 1.819 | -1.972 | 6.088 | 0.87 |
| full field | 2015-2018 | chop_ungated | team2 |  | -0.1508 | 200 | 2.894 | -2.958 | 9.132 | 0.71 |


### random-entry

| scope | step | book | budget | members | real | n_draws | null_mean | null_p5 | null_p95 | p_one_sided |
|---|---|---|---|---|---|---|---|---|---|---|
| sample 20000 | 2011-2014 | allon | team1 | 2e+04 | 0.2305 | 19 | -0.8438 | -2.438 | 1.069 | 0.1579 |
| sample 20000 | 2011-2014 | allon | team2 | 2e+04 | 0.3457 | 19 | -1.266 | -3.658 | 1.603 | 0.1579 |
| sample 20000 | 2011-2014 | chop_notrange | team1 | 2e+04 | -0.6892 | 19 | -0.5242 | -1.981 | 0.8254 | 0.6842 |
| sample 20000 | 2011-2014 | chop_notrange | team2 | 2e+04 | -1.034 | 19 | -0.7864 | -2.972 | 1.238 | 0.6842 |
| sample 20000 | 2011-2014 | chop_trend | team1 | 2e+04 | -1.826 | 19 | 0.03265 | -1.998 | 1.802 | 0.8947 |
| sample 20000 | 2011-2014 | chop_trend | team2 | 2e+04 | -2.739 | 19 | 0.04897 | -2.996 | 2.703 | 0.8947 |
| sample 20000 | 2011-2014 | chop_ungated | team1 | 2e+04 | -0.2763 | 19 | -0.6359 | -2.401 | 1.367 | 0.4737 |
| sample 20000 | 2011-2014 | chop_ungated | team2 | 2e+04 | -0.4145 | 19 | -0.9539 | -3.602 | 2.05 | 0.4737 |
| sample 20000 | 2012-2015 | allon | team1 | 2e+04 | -1.161 | 19 | -0.09594 | -1.686 | 1.872 | 0.8421 |
| sample 20000 | 2012-2015 | allon | team2 | 2e+04 | -1.741 | 19 | -0.1439 | -2.53 | 2.808 | 0.8421 |
| sample 20000 | 2012-2015 | chop_notrange | team1 | 2e+04 | -2.573 | 19 | -0.4584 | -2.179 | 1.305 | 0.9474 |
| sample 20000 | 2012-2015 | chop_notrange | team2 | 2e+04 | -3.86 | 19 | -0.6876 | -3.268 | 1.958 | 0.9474 |
| sample 20000 | 2012-2015 | chop_trend | team1 | 2e+04 | -0.6468 | 19 | -0.3131 | -2.362 | 0.8034 | 0.7368 |
| sample 20000 | 2012-2015 | chop_trend | team2 | 2e+04 | -0.9702 | 19 | -0.4696 | -3.543 | 1.205 | 0.7368 |
| sample 20000 | 2012-2015 | chop_ungated | team1 | 2e+04 | -0.7493 | 19 | -0.3212 | -1.249 | 1.375 | 0.7368 |
| sample 20000 | 2012-2015 | chop_ungated | team2 | 2e+04 | -1.124 | 19 | -0.4817 | -1.874 | 2.062 | 0.7368 |
| sample 20000 | 2013-2016 | allon | team1 | 2e+04 | -0.5436 | 19 | -0.1993 | -1.547 | 1.576 | 0.6316 |
| sample 20000 | 2013-2016 | allon | team2 | 2e+04 | -0.8153 | 19 | -0.2989 | -2.321 | 2.365 | 0.6316 |
| sample 20000 | 2013-2016 | chop_notrange | team1 | 2e+04 | -0.4091 | 19 | -0.2025 | -2.413 | 1.581 | 0.6842 |
| sample 20000 | 2013-2016 | chop_notrange | team2 | 2e+04 | -0.6137 | 19 | -0.3037 | -3.619 | 2.371 | 0.6842 |
| sample 20000 | 2013-2016 | chop_trend | team1 | 2e+04 | 0.7637 | 19 | -0.2257 | -2.073 | 1.585 | 0.3158 |
| sample 20000 | 2013-2016 | chop_trend | team2 | 2e+04 | 1.146 | 19 | -0.3386 | -3.11 | 2.377 | 0.3158 |
| sample 20000 | 2013-2016 | chop_ungated | team1 | 2e+04 | 0.1723 | 19 | -0.2725 | -1.658 | 1.311 | 0.2632 |
| sample 20000 | 2013-2016 | chop_ungated | team2 | 2e+04 | 0.2585 | 19 | -0.4088 | -2.487 | 1.966 | 0.2632 |
| sample 20000 | 2014-2017 | allon | team1 | 2e+04 | -2.135 | 19 | -0.5241 | -2.081 | 0.4144 | 1 |
| sample 20000 | 2014-2017 | allon | team2 | 2e+04 | -3.203 | 19 | -0.7862 | -3.122 | 0.6216 | 1 |
| sample 20000 | 2014-2017 | chop_notrange | team1 | 2e+04 | -2.123 | 19 | -0.5951 | -2.162 | 0.5052 | 0.8947 |
| sample 20000 | 2014-2017 | chop_notrange | team2 | 2e+04 | -3.184 | 19 | -0.8927 | -3.243 | 0.7577 | 0.8947 |
| sample 20000 | 2014-2017 | chop_trend | team1 | 2e+04 | -1.631 | 19 | -0.5127 | -1.877 | 0.5724 | 0.8947 |
| sample 20000 | 2014-2017 | chop_trend | team2 | 2e+04 | -2.447 | 19 | -0.7691 | -2.815 | 0.8585 | 0.8947 |
| sample 20000 | 2014-2017 | chop_ungated | team1 | 2e+04 | -1.884 | 19 | -0.213 | -1.729 | 1.436 | 0.9474 |
| sample 20000 | 2014-2017 | chop_ungated | team2 | 2e+04 | -2.826 | 19 | -0.3196 | -2.593 | 2.154 | 0.9474 |
| sample 20000 | 2015-2018 | allon | team1 | 2e+04 | -1.313 | 19 | -0.7375 | -3.052 | 1.053 | 0.7368 |
| sample 20000 | 2015-2018 | allon | team2 | 2e+04 | -1.969 | 19 | -1.106 | -4.578 | 1.58 | 0.7368 |
| sample 20000 | 2015-2018 | chop_notrange | team1 | 2e+04 | -0.3897 | 19 | -1.098 | -3.139 | 1.097 | 0.3158 |
| sample 20000 | 2015-2018 | chop_notrange | team2 | 2e+04 | -0.5846 | 19 | -1.646 | -4.708 | 1.645 | 0.3158 |
| sample 20000 | 2015-2018 | chop_trend | team1 | 2e+04 | -0.7628 | 19 | -0.6965 | -2.52 | 1.145 | 0.6316 |
| sample 20000 | 2015-2018 | chop_trend | team2 | 2e+04 | -1.144 | 19 | -1.045 | -3.781 | 1.717 | 0.6316 |
| sample 20000 | 2015-2018 | chop_ungated | team1 | 2e+04 | -0.3692 | 19 | -0.826 | -2.32 | 0.705 | 0.3684 |
| sample 20000 | 2015-2018 | chop_ungated | team2 | 2e+04 | -0.5537 | 19 | -1.239 | -3.48 | 1.057 | 0.3684 |
| sample 5000 | 2011-2014 | allon | team1 | 5000 | 0.5335 | 19 | -0.5392 | -2.417 | 1.059 | 0.2105 |
| sample 5000 | 2011-2014 | allon | team2 | 5000 | 0.8002 | 19 | -0.8088 | -3.625 | 1.588 | 0.2105 |
| sample 5000 | 2011-2014 | chop_notrange | team1 | 5000 | -0.366 | 19 | -0.8928 | -2.587 | 0.7028 | 0.3158 |
| sample 5000 | 2011-2014 | chop_notrange | team2 | 5000 | -0.549 | 19 | -1.339 | -3.88 | 1.054 | 0.3158 |
| sample 5000 | 2011-2014 | chop_trend | team1 | 5000 | -1.548 | 19 | -0.3826 | -2.236 | 1.373 | 0.7368 |
| sample 5000 | 2011-2014 | chop_trend | team2 | 5000 | -2.322 | 19 | -0.5739 | -3.354 | 2.06 | 0.7368 |
| sample 5000 | 2011-2014 | chop_ungated | team1 | 5000 | -0.66 | 19 | -0.6095 | -2.965 | 0.9648 | 0.5789 |
| sample 5000 | 2011-2014 | chop_ungated | team2 | 5000 | -0.99 | 19 | -0.9142 | -4.448 | 1.447 | 0.5789 |
| sample 5000 | 2012-2015 | allon | team1 | 5000 | -1.221 | 19 | 0.06147 | -0.9793 | 1.669 | 0.9474 |
| sample 5000 | 2012-2015 | allon | team2 | 5000 | -1.832 | 19 | 0.09221 | -1.469 | 2.503 | 0.9474 |
| sample 5000 | 2012-2015 | chop_notrange | team1 | 5000 | -1.934 | 19 | -0.1077 | -1.764 | 1.304 | 0.9474 |
| sample 5000 | 2012-2015 | chop_notrange | team2 | 5000 | -2.901 | 19 | -0.1615 | -2.645 | 1.956 | 0.9474 |
| sample 5000 | 2012-2015 | chop_trend | team1 | 5000 | -1.024 | 19 | 0.0215 | -1.7 | 1.8 | 0.8421 |
| sample 5000 | 2012-2015 | chop_trend | team2 | 5000 | -1.536 | 19 | 0.03225 | -2.55 | 2.7 | 0.8421 |
| sample 5000 | 2012-2015 | chop_ungated | team1 | 5000 | -0.8929 | 19 | -0.1089 | -1.825 | 1.65 | 0.7895 |
| sample 5000 | 2012-2015 | chop_ungated | team2 | 5000 | -1.339 | 19 | -0.1634 | -2.737 | 2.475 | 0.7895 |
| sample 5000 | 2013-2016 | allon | team1 | 5000 | -0.5126 | 19 | -0.5078 | -2.14 | 1.056 | 0.5263 |
| sample 5000 | 2013-2016 | allon | team2 | 5000 | -0.7688 | 19 | -0.7618 | -3.21 | 1.585 | 0.5263 |
| sample 5000 | 2013-2016 | chop_notrange | team1 | 5000 | 0.268 | 19 | -0.2026 | -2.047 | 1.949 | 0.2105 |
| sample 5000 | 2013-2016 | chop_notrange | team2 | 5000 | 0.402 | 19 | -0.3039 | -3.07 | 2.924 | 0.2105 |
| sample 5000 | 2013-2016 | chop_trend | team1 | 5000 | 0.557 | 19 | -0.1704 | -1.44 | 1.927 | 0.3158 |
| sample 5000 | 2013-2016 | chop_trend | team2 | 5000 | 0.8356 | 19 | -0.2556 | -2.161 | 2.89 | 0.3158 |
| sample 5000 | 2013-2016 | chop_ungated | team1 | 5000 | 0.5306 | 19 | -0.3289 | -2.016 | 1.951 | 0.1579 |
| sample 5000 | 2013-2016 | chop_ungated | team2 | 5000 | 0.7959 | 19 | -0.4933 | -3.024 | 2.927 | 0.1579 |
| sample 5000 | 2014-2017 | allon | team1 | 5000 | -3.109 | 19 | -0.4615 | -1.645 | 0.688 | 1 |
| sample 5000 | 2014-2017 | allon | team2 | 5000 | -4.664 | 19 | -0.6923 | -2.467 | 1.032 | 1 |
| sample 5000 | 2014-2017 | chop_notrange | team1 | 5000 | -1.975 | 19 | -0.5053 | -2.551 | 0.585 | 0.8947 |
| sample 5000 | 2014-2017 | chop_notrange | team2 | 5000 | -2.962 | 19 | -0.7579 | -3.826 | 0.8775 | 0.8947 |
| sample 5000 | 2014-2017 | chop_trend | team1 | 5000 | -1.749 | 19 | -0.8668 | -1.677 | 0.03147 | 1 |
| sample 5000 | 2014-2017 | chop_trend | team2 | 5000 | -2.623 | 19 | -1.3 | -2.516 | 0.04721 | 1 |
| sample 5000 | 2014-2017 | chop_ungated | team1 | 5000 | -1.872 | 19 | -0.2993 | -1.671 | 1.095 | 0.9474 |
| sample 5000 | 2014-2017 | chop_ungated | team2 | 5000 | -2.809 | 19 | -0.4489 | -2.506 | 1.643 | 0.9474 |
| sample 5000 | 2015-2018 | allon | team1 | 5000 | -0.9814 | 19 | -0.6335 | -2.854 | 1.509 | 0.5789 |
| sample 5000 | 2015-2018 | allon | team2 | 5000 | -1.472 | 19 | -0.9502 | -4.28 | 2.263 | 0.5789 |
| sample 5000 | 2015-2018 | chop_notrange | team1 | 5000 | -0.6291 | 19 | -0.7686 | -2.652 | 0.7273 | 0.4737 |
| sample 5000 | 2015-2018 | chop_notrange | team2 | 5000 | -0.9437 | 19 | -1.153 | -3.978 | 1.091 | 0.4737 |
| sample 5000 | 2015-2018 | chop_trend | team1 | 5000 | -0.863 | 19 | -0.5198 | -2.536 | 0.9908 | 0.5263 |
| sample 5000 | 2015-2018 | chop_trend | team2 | 5000 | -1.295 | 19 | -0.7796 | -3.804 | 1.486 | 0.5263 |
| sample 5000 | 2015-2018 | chop_ungated | team1 | 5000 | -0.3368 | 19 | -0.5894 | -2.653 | 1.182 | 0.4737 |
| sample 5000 | 2015-2018 | chop_ungated | team2 | 5000 | -0.5051 | 19 | -0.884 | -3.98 | 1.774 | 0.4737 |


### shuffle

| scope | step | book | budget | members | real | n_draws | null_mean | null_p5 | null_p95 | p_one_sided |
|---|---|---|---|---|---|---|---|---|---|---|
| sample 20000 | 2011-2014 | allon | team1 | 2e+04 | 0.2305 | 19 | 0.2305 | 0.2305 | 0.2305 | 1 |
| sample 20000 | 2011-2014 | allon | team2 | 2e+04 | 0.3457 | 19 | 0.3457 | 0.3457 | 0.3457 | 1 |
| sample 20000 | 2011-2014 | chop_notrange | team1 | 2e+04 | -0.6892 | 19 | -0.4252 | -1.04 | 0.3511 | 0.6316 |
| sample 20000 | 2011-2014 | chop_notrange | team2 | 2e+04 | -1.034 | 19 | -0.6378 | -1.56 | 0.5266 | 0.6316 |
| sample 20000 | 2011-2014 | chop_trend | team1 | 2e+04 | -1.826 | 19 | -0.496 | -0.9992 | 0.113 | 1 |
| sample 20000 | 2011-2014 | chop_trend | team2 | 2e+04 | -2.739 | 19 | -0.744 | -1.499 | 0.1696 | 1 |
| sample 20000 | 2011-2014 | chop_ungated | team1 | 2e+04 | -0.2763 | 19 | -0.2194 | -0.8225 | 0.2643 | 0.7368 |
| sample 20000 | 2011-2014 | chop_ungated | team2 | 2e+04 | -0.4145 | 19 | -0.3291 | -1.234 | 0.3965 | 0.7368 |
| sample 20000 | 2012-2015 | allon | team1 | 2e+04 | -1.161 | 19 | -1.161 | -1.161 | -1.161 | 1 |
| sample 20000 | 2012-2015 | allon | team2 | 2e+04 | -1.741 | 19 | -1.741 | -1.741 | -1.741 | 1 |
| sample 20000 | 2012-2015 | chop_notrange | team1 | 2e+04 | -2.573 | 19 | -0.3833 | -0.909 | 0.3856 | 1 |
| sample 20000 | 2012-2015 | chop_notrange | team2 | 2e+04 | -3.86 | 19 | -0.575 | -1.363 | 0.5784 | 1 |
| sample 20000 | 2012-2015 | chop_trend | team1 | 2e+04 | -0.6468 | 19 | -0.8072 | -1.537 | -0.2056 | 0.3158 |
| sample 20000 | 2012-2015 | chop_trend | team2 | 2e+04 | -0.9702 | 19 | -1.211 | -2.306 | -0.3085 | 0.3158 |
| sample 20000 | 2012-2015 | chop_ungated | team1 | 2e+04 | -0.7493 | 19 | -0.51 | -1.295 | 0.06464 | 0.7368 |
| sample 20000 | 2012-2015 | chop_ungated | team2 | 2e+04 | -1.124 | 19 | -0.765 | -1.943 | 0.09696 | 0.7368 |
| sample 20000 | 2013-2016 | allon | team1 | 2e+04 | -0.5436 | 19 | -0.5436 | -0.5436 | -0.5436 | 1 |
| sample 20000 | 2013-2016 | allon | team2 | 2e+04 | -0.8153 | 19 | -0.8153 | -0.8153 | -0.8153 | 1 |
| sample 20000 | 2013-2016 | chop_notrange | team1 | 2e+04 | -0.4091 | 19 | 0.09832 | -0.3956 | 0.5498 | 0.9474 |
| sample 20000 | 2013-2016 | chop_notrange | team2 | 2e+04 | -0.6137 | 19 | 0.1475 | -0.5935 | 0.8248 | 0.9474 |
| sample 20000 | 2013-2016 | chop_trend | team1 | 2e+04 | 0.7637 | 19 | 0.1857 | -0.653 | 1.063 | 0.1053 |
| sample 20000 | 2013-2016 | chop_trend | team2 | 2e+04 | 1.146 | 19 | 0.2786 | -0.9795 | 1.595 | 0.1053 |
| sample 20000 | 2013-2016 | chop_ungated | team1 | 2e+04 | 0.1723 | 19 | 0.1167 | -0.6151 | 0.7755 | 0.5263 |
| sample 20000 | 2013-2016 | chop_ungated | team2 | 2e+04 | 0.2585 | 19 | 0.1751 | -0.9226 | 1.163 | 0.5263 |
| sample 20000 | 2014-2017 | allon | team1 | 2e+04 | -2.135 | 19 | -2.135 | -2.135 | -2.135 | 1 |
| sample 20000 | 2014-2017 | allon | team2 | 2e+04 | -3.203 | 19 | -3.203 | -3.203 | -3.203 | 1 |
| sample 20000 | 2014-2017 | chop_notrange | team1 | 2e+04 | -2.123 | 19 | -1.132 | -1.676 | -0.8078 | 1 |
| sample 20000 | 2014-2017 | chop_notrange | team2 | 2e+04 | -3.184 | 19 | -1.698 | -2.514 | -1.212 | 1 |
| sample 20000 | 2014-2017 | chop_trend | team1 | 2e+04 | -1.631 | 19 | -1.378 | -2.349 | -0.2607 | 0.6316 |
| sample 20000 | 2014-2017 | chop_trend | team2 | 2e+04 | -2.447 | 19 | -2.068 | -3.524 | -0.3911 | 0.6316 |
| sample 20000 | 2014-2017 | chop_ungated | team1 | 2e+04 | -1.884 | 19 | -0.8951 | -1.596 | -0.4113 | 0.9474 |
| sample 20000 | 2014-2017 | chop_ungated | team2 | 2e+04 | -2.826 | 19 | -1.343 | -2.395 | -0.6169 | 0.9474 |
| sample 20000 | 2015-2018 | allon | team1 | 2e+04 | -1.313 | 19 | -1.313 | -1.313 | -1.313 | 1 |
| sample 20000 | 2015-2018 | allon | team2 | 2e+04 | -1.969 | 19 | -1.969 | -1.969 | -1.969 | 1 |
| sample 20000 | 2015-2018 | chop_notrange | team1 | 2e+04 | -0.3897 | 19 | 0.03505 | -0.443 | 0.3782 | 0.8947 |
| sample 20000 | 2015-2018 | chop_notrange | team2 | 2e+04 | -0.5846 | 19 | 0.05258 | -0.6645 | 0.5673 | 0.8947 |
| sample 20000 | 2015-2018 | chop_trend | team1 | 2e+04 | -0.7628 | 19 | -0.3614 | -1.205 | 0.5895 | 0.7895 |
| sample 20000 | 2015-2018 | chop_trend | team2 | 2e+04 | -1.144 | 19 | -0.5422 | -1.807 | 0.8842 | 0.7895 |
| sample 20000 | 2015-2018 | chop_ungated | team1 | 2e+04 | -0.3692 | 19 | 0.1016 | -0.5134 | 0.6296 | 0.8947 |
| sample 20000 | 2015-2018 | chop_ungated | team2 | 2e+04 | -0.5537 | 19 | 0.1524 | -0.7701 | 0.9444 | 0.8947 |
| sample 5000 | 2011-2014 | allon | team1 | 5000 | 0.5335 | 19 | 0.5335 | 0.5335 | 0.5335 | 1 |
| sample 5000 | 2011-2014 | allon | team2 | 5000 | 0.8002 | 19 | 0.8002 | 0.8002 | 0.8002 | 1 |
| sample 5000 | 2011-2014 | chop_notrange | team1 | 5000 | -0.366 | 19 | -0.4807 | -1.266 | 0.3208 | 0.4737 |
| sample 5000 | 2011-2014 | chop_notrange | team2 | 5000 | -0.549 | 19 | -0.7211 | -1.899 | 0.4812 | 0.4737 |
| sample 5000 | 2011-2014 | chop_trend | team1 | 5000 | -1.548 | 19 | -0.446 | -1.084 | 0.126 | 1 |
| sample 5000 | 2011-2014 | chop_trend | team2 | 5000 | -2.322 | 19 | -0.669 | -1.626 | 0.1891 | 1 |
| sample 5000 | 2011-2014 | chop_ungated | team1 | 5000 | -0.66 | 19 | -0.3264 | -1.074 | 0.2444 | 0.8421 |
| sample 5000 | 2011-2014 | chop_ungated | team2 | 5000 | -0.99 | 19 | -0.4896 | -1.611 | 0.3665 | 0.8421 |
| sample 5000 | 2012-2015 | allon | team1 | 5000 | -1.221 | 19 | -1.221 | -1.221 | -1.221 | 1 |
| sample 5000 | 2012-2015 | allon | team2 | 5000 | -1.832 | 19 | -1.832 | -1.832 | -1.832 | 1 |
| sample 5000 | 2012-2015 | chop_notrange | team1 | 5000 | -1.934 | 19 | -0.4167 | -0.9658 | 0.4501 | 1 |
| sample 5000 | 2012-2015 | chop_notrange | team2 | 5000 | -2.901 | 19 | -0.6251 | -1.449 | 0.6752 | 1 |
| sample 5000 | 2012-2015 | chop_trend | team1 | 5000 | -1.024 | 19 | -0.8741 | -1.384 | -0.4564 | 0.6316 |
| sample 5000 | 2012-2015 | chop_trend | team2 | 5000 | -1.536 | 19 | -1.311 | -2.077 | -0.6847 | 0.6316 |
| sample 5000 | 2012-2015 | chop_ungated | team1 | 5000 | -0.8929 | 19 | -0.4869 | -1.215 | 0.1018 | 0.8421 |
| sample 5000 | 2012-2015 | chop_ungated | team2 | 5000 | -1.339 | 19 | -0.7304 | -1.822 | 0.1527 | 0.8421 |
| sample 5000 | 2013-2016 | allon | team1 | 5000 | -0.5126 | 19 | -0.5126 | -0.5126 | -0.5126 | 1 |
| sample 5000 | 2013-2016 | allon | team2 | 5000 | -0.7688 | 19 | -0.7688 | -0.7688 | -0.7688 | 1 |
| sample 5000 | 2013-2016 | chop_notrange | team1 | 5000 | 0.268 | 19 | 0.2739 | -0.2667 | 0.84 | 0.3684 |
| sample 5000 | 2013-2016 | chop_notrange | team2 | 5000 | 0.402 | 19 | 0.4108 | -0.4 | 1.26 | 0.3684 |
| sample 5000 | 2013-2016 | chop_trend | team1 | 5000 | 0.557 | 19 | 0.08173 | -0.6153 | 0.9301 | 0.2105 |
| sample 5000 | 2013-2016 | chop_trend | team2 | 5000 | 0.8356 | 19 | 0.1226 | -0.9229 | 1.395 | 0.2105 |
| sample 5000 | 2013-2016 | chop_ungated | team1 | 5000 | 0.5306 | 19 | 0.16 | -0.3872 | 0.6817 | 0.2105 |
| sample 5000 | 2013-2016 | chop_ungated | team2 | 5000 | 0.7959 | 19 | 0.24 | -0.5808 | 1.022 | 0.2105 |
| sample 5000 | 2014-2017 | allon | team1 | 5000 | -3.109 | 19 | -3.109 | -3.109 | -3.109 | 1 |
| sample 5000 | 2014-2017 | allon | team2 | 5000 | -4.664 | 19 | -4.664 | -4.664 | -4.664 | 1 |
| sample 5000 | 2014-2017 | chop_notrange | team1 | 5000 | -1.975 | 19 | -1.097 | -1.626 | -0.6255 | 1 |
| sample 5000 | 2014-2017 | chop_notrange | team2 | 5000 | -2.962 | 19 | -1.646 | -2.439 | -0.9383 | 1 |
| sample 5000 | 2014-2017 | chop_trend | team1 | 5000 | -1.749 | 19 | -1.425 | -2.274 | -0.4066 | 0.7368 |
| sample 5000 | 2014-2017 | chop_trend | team2 | 5000 | -2.623 | 19 | -2.137 | -3.41 | -0.6099 | 0.7368 |
| sample 5000 | 2014-2017 | chop_ungated | team1 | 5000 | -1.872 | 19 | -0.8594 | -1.453 | -0.2087 | 1 |
| sample 5000 | 2014-2017 | chop_ungated | team2 | 5000 | -2.809 | 19 | -1.289 | -2.18 | -0.3131 | 1 |
| sample 5000 | 2015-2018 | allon | team1 | 5000 | -0.9814 | 19 | -0.9814 | -0.9814 | -0.9814 | 1 |
| sample 5000 | 2015-2018 | allon | team2 | 5000 | -1.472 | 19 | -1.472 | -1.472 | -1.472 | 1 |
| sample 5000 | 2015-2018 | chop_notrange | team1 | 5000 | -0.6291 | 19 | 0.03204 | -0.471 | 0.4217 | 0.9474 |
| sample 5000 | 2015-2018 | chop_notrange | team2 | 5000 | -0.9437 | 19 | 0.04806 | -0.7066 | 0.6326 | 0.9474 |
| sample 5000 | 2015-2018 | chop_trend | team1 | 5000 | -0.863 | 19 | -0.3623 | -1.066 | 0.4336 | 0.7895 |
| sample 5000 | 2015-2018 | chop_trend | team2 | 5000 | -1.295 | 19 | -0.5434 | -1.599 | 0.6503 | 0.7895 |
| sample 5000 | 2015-2018 | chop_ungated | team1 | 5000 | -0.3368 | 19 | 0.1011 | -0.3207 | 0.5061 | 0.9474 |
| sample 5000 | 2015-2018 | chop_ungated | team2 | 5000 | -0.5051 | 19 | 0.1517 | -0.481 | 0.7592 | 0.9474 |


**Is the p-value stable in the sample size?** Same (null, step, book, budget) at 5,000 and at 20,000:

| null | step | book | budget | sample 20000 | sample 5000 |
|---|---|---|---|---|---|
| random-entry | 2011-2014 | allon | team1 | 0.1579 | 0.2105 |
| random-entry | 2011-2014 | allon | team2 | 0.1579 | 0.2105 |
| random-entry | 2011-2014 | chop_notrange | team1 | 0.6842 | 0.3158 |
| random-entry | 2011-2014 | chop_notrange | team2 | 0.6842 | 0.3158 |
| random-entry | 2011-2014 | chop_trend | team1 | 0.8947 | 0.7368 |
| random-entry | 2011-2014 | chop_trend | team2 | 0.8947 | 0.7368 |
| random-entry | 2011-2014 | chop_ungated | team1 | 0.4737 | 0.5789 |
| random-entry | 2011-2014 | chop_ungated | team2 | 0.4737 | 0.5789 |
| random-entry | 2012-2015 | allon | team1 | 0.8421 | 0.9474 |
| random-entry | 2012-2015 | allon | team2 | 0.8421 | 0.9474 |
| random-entry | 2012-2015 | chop_notrange | team1 | 0.9474 | 0.9474 |
| random-entry | 2012-2015 | chop_notrange | team2 | 0.9474 | 0.9474 |
| random-entry | 2012-2015 | chop_trend | team1 | 0.7368 | 0.8421 |
| random-entry | 2012-2015 | chop_trend | team2 | 0.7368 | 0.8421 |
| random-entry | 2012-2015 | chop_ungated | team1 | 0.7368 | 0.7895 |
| random-entry | 2012-2015 | chop_ungated | team2 | 0.7368 | 0.7895 |
| random-entry | 2013-2016 | allon | team1 | 0.6316 | 0.5263 |
| random-entry | 2013-2016 | allon | team2 | 0.6316 | 0.5263 |
| random-entry | 2013-2016 | chop_notrange | team1 | 0.6842 | 0.2105 |
| random-entry | 2013-2016 | chop_notrange | team2 | 0.6842 | 0.2105 |
| random-entry | 2013-2016 | chop_trend | team1 | 0.3158 | 0.3158 |
| random-entry | 2013-2016 | chop_trend | team2 | 0.3158 | 0.3158 |
| random-entry | 2013-2016 | chop_ungated | team1 | 0.2632 | 0.1579 |
| random-entry | 2013-2016 | chop_ungated | team2 | 0.2632 | 0.1579 |
| random-entry | 2014-2017 | allon | team1 | 1 | 1 |
| random-entry | 2014-2017 | allon | team2 | 1 | 1 |
| random-entry | 2014-2017 | chop_notrange | team1 | 0.8947 | 0.8947 |
| random-entry | 2014-2017 | chop_notrange | team2 | 0.8947 | 0.8947 |
| random-entry | 2014-2017 | chop_trend | team1 | 0.8947 | 1 |
| random-entry | 2014-2017 | chop_trend | team2 | 0.8947 | 1 |
| random-entry | 2014-2017 | chop_ungated | team1 | 0.9474 | 0.9474 |
| random-entry | 2014-2017 | chop_ungated | team2 | 0.9474 | 0.9474 |
| random-entry | 2015-2018 | allon | team1 | 0.7368 | 0.5789 |
| random-entry | 2015-2018 | allon | team2 | 0.7368 | 0.5789 |
| random-entry | 2015-2018 | chop_notrange | team1 | 0.3158 | 0.4737 |
| random-entry | 2015-2018 | chop_notrange | team2 | 0.3158 | 0.4737 |
| random-entry | 2015-2018 | chop_trend | team1 | 0.6316 | 0.5263 |
| random-entry | 2015-2018 | chop_trend | team2 | 0.6316 | 0.5263 |
| random-entry | 2015-2018 | chop_ungated | team1 | 0.3684 | 0.4737 |
| random-entry | 2015-2018 | chop_ungated | team2 | 0.3684 | 0.4737 |
| shuffle | 2011-2014 | allon | team1 | 1 | 1 |
| shuffle | 2011-2014 | allon | team2 | 1 | 1 |
| shuffle | 2011-2014 | chop_notrange | team1 | 0.6316 | 0.4737 |
| shuffle | 2011-2014 | chop_notrange | team2 | 0.6316 | 0.4737 |
| shuffle | 2011-2014 | chop_trend | team1 | 1 | 1 |
| shuffle | 2011-2014 | chop_trend | team2 | 1 | 1 |
| shuffle | 2011-2014 | chop_ungated | team1 | 0.7368 | 0.8421 |
| shuffle | 2011-2014 | chop_ungated | team2 | 0.7368 | 0.8421 |
| shuffle | 2012-2015 | allon | team1 | 1 | 1 |
| shuffle | 2012-2015 | allon | team2 | 1 | 1 |
| shuffle | 2012-2015 | chop_notrange | team1 | 1 | 1 |
| shuffle | 2012-2015 | chop_notrange | team2 | 1 | 1 |
| shuffle | 2012-2015 | chop_trend | team1 | 0.3158 | 0.6316 |
| shuffle | 2012-2015 | chop_trend | team2 | 0.3158 | 0.6316 |
| shuffle | 2012-2015 | chop_ungated | team1 | 0.7368 | 0.8421 |
| shuffle | 2012-2015 | chop_ungated | team2 | 0.7368 | 0.8421 |
| shuffle | 2013-2016 | allon | team1 | 1 | 1 |
| shuffle | 2013-2016 | allon | team2 | 1 | 1 |
| shuffle | 2013-2016 | chop_notrange | team1 | 0.9474 | 0.3684 |
| shuffle | 2013-2016 | chop_notrange | team2 | 0.9474 | 0.3684 |
| shuffle | 2013-2016 | chop_trend | team1 | 0.1053 | 0.2105 |
| shuffle | 2013-2016 | chop_trend | team2 | 0.1053 | 0.2105 |
| shuffle | 2013-2016 | chop_ungated | team1 | 0.5263 | 0.2105 |
| shuffle | 2013-2016 | chop_ungated | team2 | 0.5263 | 0.2105 |
| shuffle | 2014-2017 | allon | team1 | 1 | 1 |
| shuffle | 2014-2017 | allon | team2 | 1 | 1 |
| shuffle | 2014-2017 | chop_notrange | team1 | 1 | 1 |
| shuffle | 2014-2017 | chop_notrange | team2 | 1 | 1 |
| shuffle | 2014-2017 | chop_trend | team1 | 0.6316 | 0.7368 |
| shuffle | 2014-2017 | chop_trend | team2 | 0.6316 | 0.7368 |
| shuffle | 2014-2017 | chop_ungated | team1 | 0.9474 | 1 |
| shuffle | 2014-2017 | chop_ungated | team2 | 0.9474 | 1 |
| shuffle | 2015-2018 | allon | team1 | 1 | 1 |
| shuffle | 2015-2018 | allon | team2 | 1 | 1 |
| shuffle | 2015-2018 | chop_notrange | team1 | 0.8947 | 0.9474 |
| shuffle | 2015-2018 | chop_notrange | team2 | 0.8947 | 0.9474 |
| shuffle | 2015-2018 | chop_trend | team1 | 0.7895 | 0.7895 |
| shuffle | 2015-2018 | chop_trend | team2 | 0.7895 | 0.7895 |
| shuffle | 2015-2018 | chop_ungated | team1 | 0.8947 | 0.9474 |
| shuffle | 2015-2018 | chop_ungated | team2 | 0.8947 | 0.9474 |


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
