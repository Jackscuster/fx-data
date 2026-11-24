# A1b — WALK-FORWARD COMPONENT SELECTION, MODE A

Generated 2026-11-24 00:08 by `code/r2reads.py`, a **pure read** of the gate 2 bank.

For each step, every slot option is ranked by its main effect on **that step's four TUNING years only**. The book is then all strategies whose C1 and C2 are both in the top K (and separately, C1 alone), traded on **that step's unseen trade year**, everyone equal weight. K is swept over its full range.


**This replaces A7, which was mis-posed.** A7 picked components on 2016-2020 and scored them on the same years. Here the ranking sees only tuning years and the book is traded on an unseen one, so it is a walk forward rather than a restatement.


## The curve: equal-weight R per trade on the unseen trade year

| rule | K | steps | mean_members | mean_eq_R | mean_tw_R |
|---|---|---|---|---|---|
| c1_and_c2_in_topK | 1 | 5 | 180 | 0.002779 | 0.0009621 |
| c1_and_c2_in_topK | 2 | 5 | 720 | -0.003791 | -0.009423 |
| c1_and_c2_in_topK | 3 | 5 | 1584 | -0.02258 | -0.02192 |
| c1_in_topK | 1 | 5 | 5960 | -0.01925 | -0.02332 |
| c1_in_topK | 2 | 5 | 1.298e+04 | -0.02154 | -0.02617 |
| c1_in_topK | 3 | 5 | 2e+04 | -0.03475 | -0.03379 |


## Against the label-shuffle null

| K | real | null_mean | null_p95 | p | draws |
|---|---|---|---|---|---|
| 1 | 0.002779 | -0.03425 | -0.0227 | 0.21 | 20 |
| 2 | -0.003791 | -0.0345 | -0.03074 | 0.2 | 20 |
| 3 | -0.02258 | -0.03427 | -0.03117 | 0.2 | 20 |


Lowest null p is **0.200 at K=2**. A component rule that beat chance would show p well under 0.05 across K, not at one value.


## Per step, per K

| step | trade_year | rule | K | members | eq_R_per_trade | tw_R_per_trade | total_R | n_trades |
|---|---|---|---|---|---|---|---|---|
| 2011-2014 | 2,016 | c1_and_c2_in_topK | 1 | 180 | 0.06675 | 0.06533 | 4400 | 6.734e+04 |
| 2011-2014 | 2,016 | c1_and_c2_in_topK | 2 | 720 | 0.05453 | 0.05221 | 1.118e+04 | 2.142e+05 |
| 2011-2014 | 2,016 | c1_and_c2_in_topK | 3 | 1620 | 0.03155 | 0.02957 | 1.469e+04 | 4.97e+05 |
| 2012-2015 | 2,017 | c1_and_c2_in_topK | 1 | 180 | 0.0005326 | -0.003756 | -298.1 | 7.936e+04 |
| 2012-2015 | 2,017 | c1_and_c2_in_topK | 2 | 720 | -0.03191 | -0.03236 | -7804 | 2.411e+05 |
| 2012-2015 | 2,017 | c1_and_c2_in_topK | 3 | 1620 | -0.03753 | -0.0364 | -1.903e+04 | 5.228e+05 |
| 2013-2016 | 2,018 | c1_and_c2_in_topK | 1 | 180 | 0.03183 | 0.03783 | 2911 | 7.696e+04 |
| 2013-2016 | 2,018 | c1_and_c2_in_topK | 2 | 720 | 0.02745 | 0.01402 | 4203 | 2.999e+05 |
| 2013-2016 | 2,018 | c1_and_c2_in_topK | 3 | 1620 | -0.009313 | -0.006999 | -4089 | 5.842e+05 |
| 2014-2017 | 2,019 | c1_and_c2_in_topK | 1 | 180 | -0.09878 | -0.1002 | -8006 | 7.992e+04 |
| 2014-2017 | 2,019 | c1_and_c2_in_topK | 2 | 720 | -0.0885 | -0.08978 | -2.629e+04 | 2.928e+05 |
| 2014-2017 | 2,019 | c1_and_c2_in_topK | 3 | 1620 | -0.07442 | -0.07955 | -4.536e+04 | 5.702e+05 |
| 2015-2018 | 2,020 | c1_and_c2_in_topK | 1 | 180 | 0.01357 | 0.005577 | 284.9 | 5.109e+04 |
| 2015-2018 | 2,020 | c1_and_c2_in_topK | 2 | 720 | 0.01947 | 0.008796 | 2104 | 2.391e+05 |
| 2015-2018 | 2,020 | c1_and_c2_in_topK | 3 | 1440 | -0.02321 | -0.01621 | -6419 | 3.96e+05 |
| 2011-2014 | 2,016 | c1_in_topK | 1 | 5960 | 0.009705 | 0.00269 | 5033 | 1.871e+06 |
| 2011-2014 | 2,016 | c1_in_topK | 2 | 1.298e+04 | -0.008619 | -0.01042 | -3.594e+04 | 3.448e+06 |
| 2011-2014 | 2,016 | c1_in_topK | 3 | 2e+04 | -0.01462 | -0.01587 | -9.893e+04 | 6.233e+06 |
| 2012-2015 | 2,017 | c1_in_topK | 1 | 5960 | -0.02818 | -0.03458 | -7.541e+04 | 2.181e+06 |
| 2012-2015 | 2,017 | c1_in_topK | 2 | 1.298e+04 | -0.04023 | -0.04846 | -2.546e+05 | 5.255e+06 |
| 2012-2015 | 2,017 | c1_in_topK | 3 | 2e+04 | -0.04803 | -0.05298 | -3.972e+05 | 7.498e+06 |
| 2013-2016 | 2,018 | c1_in_topK | 1 | 5960 | 0.04138 | 0.03616 | 7.989e+04 | 2.209e+06 |
| 2013-2016 | 2,018 | c1_in_topK | 2 | 1.298e+04 | 0.04487 | 0.03449 | 1.767e+05 | 5.122e+06 |
| 2013-2016 | 2,018 | c1_in_topK | 3 | 2e+04 | 0.01632 | 0.01864 | 1.344e+05 | 7.208e+06 |
| 2014-2017 | 2,019 | c1_in_topK | 1 | 5960 | -0.09552 | -0.09655 | -2.008e+05 | 2.08e+06 |
| 2014-2017 | 2,019 | c1_in_topK | 2 | 1.298e+04 | -0.08496 | -0.08474 | -4.164e+05 | 4.915e+06 |
| 2014-2017 | 2,019 | c1_in_topK | 3 | 2e+04 | -0.08368 | -0.08118 | -5.789e+05 | 7.131e+06 |
| 2015-2018 | 2,020 | c1_in_topK | 1 | 5960 | -0.02363 | -0.02432 | -5.218e+04 | 2.146e+06 |
| 2015-2018 | 2,020 | c1_in_topK | 2 | 1.298e+04 | -0.01874 | -0.02173 | -1.075e+05 | 4.946e+06 |
| 2015-2018 | 2,020 | c1_in_topK | 3 | 2e+04 | -0.04371 | -0.03757 | -2.639e+05 | 7.022e+06 |


## What this does NOT report, and why

Jack asked for this "at Team 1 through A6". **That is not a bank read.** A6 needs a daily equity series, and a component book of thousands of strategies has no saved daily series — producing one is a book pass through the engine, not a read. The figures above are therefore in R space. Putting this book through A6 is a chunk-2 or later item and is registered as such rather than faked here.


## Provenance

| file | rows | md5 |
|---|---|---|
| `results/r2reads/modeA_a1b_walkforward.csv` | 50 | bab9664196ea |
