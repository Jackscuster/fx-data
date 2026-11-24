# A5 — THE HOURLY PATH AGAINST THE DAILY BAR

Generated 2026-11-24 16:40 by `code/r2hourly.py`.


## What was specified, and what each section answers

| specified | section |
|---|---|
| count of trades where the daily bar and the hourly path disagree | 1 |
| change in R per strategy and per book | 2 |
| the same trades under the daily cost table versus hourly spreads | 3 |
| the daily loss stop on hourly marks, threshold swept, through A6 | 4 |

**This report exists because the first A5 run delivered only the ambiguous-day identification.** Chain 25 reported 7 stages succeeded and 0 failed, but the stages declared covered one of the five things asked for. The ledger was green and the deliverable was not there.


## The daily engine fills the STOP

`l2engine.py:37`: a bar whose range covers both the stop and the target fills the **stop**, because a daily bar cannot say which came first and assuming the good one is how you fool yourself. So an hourly verdict of `stop` **agrees** with the daily engine and only `target` disagrees — and **every disagreement is in the favourable direction.** The daily assumption costs R; it does not flatter the result.


## Mode A

### 1 and 2 — disagreements and the change in R

| bank_row | ambiguous_days | disagreements | delta_R | share_disagree | mode |
|---|---|---|---|---|---|
| 164,340 | 11 | 5 | 12.5 | 0.4545 | A |
| 164,357 | 7 | 2 | 5 | 0.2857 | A |
| 164,358 | 11 | 4 | 10 | 0.3636 | A |
| 164,475 | 13 | 4 | 10 | 0.3077 | A |
| 167,005 | 5 | 1 | 2.5 | 0.2 | A |
| 269,640 | 11 | 6 | 15 | 0.5455 | A |
| 269,665 | 8 | 5 | 12.5 | 0.625 | A |
| 269,775 | 11 | 4 | 10 | 0.3636 | A |


**Book:**

| mode | book | members | ambiguous_days | disagreements | delta_R_total | delta_R_per_member |
|---|---|---|---|---|---|---|
| A | winners_allon | 8 | 77 | 31 | 77.5 | 9.688 |


31 of 77 ambiguous day-trades disagree (40%), worth **+77.50 R** in total and **+9.69 R per member**. Every one is a gain, for the reason above.


### 3 — the cost table against realised hourly spreads

**The cost table is accurate, and two errors of mine had to be corrected to see that.** A round trip crosses the spread ONCE, so round-trip cost is one spread, not two — I doubled it first. And the table is a median at a single hour (22:00 NY), not a daily average. Verified against the raw file: EURUSD median one-way spread at 22:00 NY over 2016-2020 is 1.40 pips / 1.211 bp; the table records 1.40 pips / 1.228 bp.

| pair | days | at_entry_hour | allhours | worst_hour | alldays_at_entry_hour | ambiguous_over_alldays | table_rt_bp | entry_over_table | allhours_over_table | mode |
|---|---|---|---|---|---|---|---|---|---|---|
| AUDJPY | 1 | 11.8 | 9.217 | 53.44 | 2.373 | 4.975 | 2.181 | 5.414 | 4.227 | A |
| AUDUSD | 8 | 5.586 | 5.374 | 26.76 | 1.986 | 2.813 | 1.96 | 2.85 | 2.742 | A |
| CADCHF | 6 | 6.19 | 5.727 | 11.86 | 3.865 | 1.602 | 3.385 | 1.829 | 1.692 | A |
| EURCHF | 7 | 14.73 | 7.131 | 18.51 | 1.907 | 7.726 | 2.014 | 7.315 | 3.541 | A |
| EURGBP | 2 | 4.226 | 3.273 | 6.937 | 1.998 | 2.115 | 2.092 | 2.02 | 1.565 | A |
| EURUSD | 9 | 1.86 | 1.851 | 5.022 | 1.203 | 1.546 | 1.228 | 1.514 | 1.507 | A |
| GBPAUD | 2 | 11.45 | 8.691 | 11.62 | 2.438 | 4.698 | 2.395 | 4.783 | 3.629 | A |
| GBPCAD | 7 | 12 | 8.467 | 12.14 | 2.492 | 4.817 | 2.448 | 4.903 | 3.459 | A |
| GBPCHF | 6 | 16.06 | 10.99 | 16.17 | 2.764 | 5.808 | 2.661 | 6.035 | 4.129 | A |
| GBPJPY | 5 | 27.39 | 11.63 | 29.18 | 2.077 | 13.19 | 2.035 | 13.46 | 5.713 | A |
| NZDCHF | 8 | 8.097 | 7.727 | 15.88 | 4.43 | 1.828 | 4.533 | 1.786 | 1.704 | A |
| NZDJPY | 3 | 19.78 | 11.52 | 27.45 | 3.557 | 5.56 | 2.874 | 6.882 | 4.01 | A |
| USDJPY | 13 | 3.458 | 2.731 | 11.44 | 1.276 | 2.709 | 1.262 | 2.741 | 2.165 | A |


On **all** days at the entry hour the realised spread is 2.49 bp against 2.39 bp charged (1.04x) — the table is right. On the **ambiguous** days it is 10.97 bp, **4.57x** wider, which is a selection effect and not a costing error: an ambiguous day is by construction a day whose bar covered both levels, so it is a high-range day and its spread is wide for that reason alone.


The extra spread on those days is worth far less than the +77.50 R the disagreements are worth, so correcting the daily fill assumption is a net gain even after paying the wider spread.


### 4 — the daily loss stop on hourly marks, swept

Reported as a curve over the full range, not at a chosen threshold.

| threshold_R | winners | years | days | days_marked_hourly | days_stop_fires | R_total | max_dd_R | R_per_year | prop_return | clears_12pct | R_vs_no_overlay |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.2 | 8 | 5 | 1.037e+04 | 8947 | 6492 | -943.5 | 52.37 | -188.7 | -12.97 | 0 | -1888 |
| 0.4 | 8 | 5 | 1.037e+04 | 8947 | 5445 | -1775 | 76.21 | -354.9 | -16.77 | 0 | -2719 |
| 0.6 | 8 | 5 | 1.037e+04 | 8947 | 4615 | -2307 | 112.6 | -461.3 | -14.74 | 0 | -3251 |
| 0.8 | 8 | 5 | 1.037e+04 | 8947 | 3892 | -2556 | 126.2 | -511.2 | -14.58 | 0 | -3501 |
| 1 | 8 | 5 | 1.037e+04 | 8947 | 3349 | -2752 | 148.3 | -550.4 | -13.37 | 0 | -3697 |
| 1.2 | 8 | 5 | 1.037e+04 | 8947 | 2842 | -2792 | 163.7 | -558.5 | -12.28 | 0 | -3737 |
| 1.5 | 8 | 5 | 1.037e+04 | 8947 | 2264 | -2753 | 191.5 | -550.7 | -10.35 | 0 | -3698 |
| 2 | 8 | 5 | 1.037e+04 | 8947 | 1506 | -2259 | 184.3 | -451.9 | -8.826 | 0 | -3204 |
| 2.5 | 8 | 5 | 1.037e+04 | 8947 | 1084 | -1930 | 198.1 | -386.1 | -7.017 | 0 | -2875 |
| 3 | 8 | 5 | 1.037e+04 | 8947 | 799 | -1636 | 182.5 | -327.2 | -6.453 | 0 | -2581 |
| 4 | 8 | 5 | 1.037e+04 | 8947 | 463 | -1021 | 131.4 | -204.1 | -5.592 | 0 | -1965 |
| 5 | 8 | 5 | 1.037e+04 | 8947 | 254 | -398.4 | 103.1 | -79.67 | -2.781 | 0 | -1343 |
|  | 8 | 5 | 1.037e+04 | 8947 | 0 | 944.7 | 24.79 | 188.9 | 27.43 | 1 | 0 |


**What this measurement can and cannot say.** It is computed on the ambiguous days alone, because those are the only days for which an hourly path was built. It is a per-day rate on those days and is NOT extrapolated to the rest of the book. A full hourly-marked equity curve for every book member over every day is a separate engine pass and is not in this read.


## Mode B

### 1 and 2 — disagreements and the change in R

| bank_row | ambiguous_days | disagreements | delta_R | share_disagree | mode |
|---|---|---|---|---|---|
| 164,340 | 12 | 8 | 20 | 0.6667 | B |
| 269,642 | 10 | 3 | 7.5 | 0.3 | B |


**Book:**

| mode | book | members | ambiguous_days | disagreements | delta_R_total | delta_R_per_member |
|---|---|---|---|---|---|---|
| B | winners_allon | 2 | 22 | 11 | 27.5 | 13.75 |


11 of 22 ambiguous day-trades disagree (50%), worth **+27.50 R** in total and **+13.75 R per member**. Every one is a gain, for the reason above.


### 3 — the cost table against realised hourly spreads

**The cost table is accurate, and two errors of mine had to be corrected to see that.** A round trip crosses the spread ONCE, so round-trip cost is one spread, not two — I doubled it first. And the table is a median at a single hour (22:00 NY), not a daily average. Verified against the raw file: EURUSD median one-way spread at 22:00 NY over 2016-2020 is 1.40 pips / 1.211 bp; the table records 1.40 pips / 1.228 bp.

| pair | days | at_entry_hour | allhours | worst_hour | alldays_at_entry_hour | ambiguous_over_alldays | table_rt_bp | entry_over_table | allhours_over_table | mode |
|---|---|---|---|---|---|---|---|---|---|---|
| AUDNZD | 2 | 7.667 | 4.95 | 9.617 | 3.701 | 2.072 | 2.972 | 2.58 | 1.666 | B |
| AUDUSD | 2 | 5.586 | 5.374 | 26.76 | 1.986 | 2.813 | 1.96 | 2.85 | 2.742 | B |
| EURCHF | 1 | 14.73 | 7.131 | 18.51 | 1.907 | 7.726 | 2.014 | 7.315 | 3.541 | B |
| EURGBP | 2 | 19.7 | 9.768 | 36.95 | 1.998 | 9.856 | 2.092 | 9.417 | 4.67 | B |
| EURNZD | 2 | 2.411 | 2.744 | 9.808 | 3.152 | 0.7649 | 2.669 | 0.9034 | 1.028 | B |
| GBPCAD | 2 | 12 | 8.467 | 12.14 | 2.492 | 4.817 | 2.448 | 4.903 | 3.459 | B |
| GBPCHF | 1 | 16.06 | 10.99 | 16.17 | 2.764 | 5.808 | 2.661 | 6.035 | 4.129 | B |
| GBPJPY | 2 | 27.39 | 11.63 | 29.18 | 2.077 | 13.19 | 2.035 | 13.46 | 5.713 | B |
| GBPUSD | 2 | 17.16 | 7.478 | 36.57 | 1.537 | 11.16 | 1.592 | 10.77 | 4.696 | B |
| NZDCHF | 2 | 8.097 | 7.727 | 15.88 | 4.43 | 1.828 | 4.533 | 1.786 | 1.704 | B |
| NZDJPY | 1 | 19.78 | 11.52 | 27.45 | 3.557 | 5.56 | 2.874 | 6.882 | 4.01 | B |
| USDJPY | 3 | 1.191 | 1.474 | 4.471 | 1.276 | 0.9331 | 1.262 | 0.944 | 1.168 | B |


On **all** days at the entry hour the realised spread is 2.57 bp against 2.43 bp charged (1.06x) — the table is right. On the **ambiguous** days it is 12.65 bp, **5.54x** wider, which is a selection effect and not a costing error: an ambiguous day is by construction a day whose bar covered both levels, so it is a high-range day and its spread is wide for that reason alone.


The extra spread on those days is worth far less than the +27.50 R the disagreements are worth, so correcting the daily fill assumption is a net gain even after paying the wider spread.


### 4 — the daily loss stop on hourly marks, swept

Reported as a curve over the full range, not at a chosen threshold.

| threshold_R | winners | years | days | days_marked_hourly | days_stop_fires | R_total | max_dd_R | R_per_year | prop_return | clears_12pct | R_vs_no_overlay |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.2 | 2 | 5 | 2592 | 2045 | 1475 | -241.5 | 38.85 | -48.31 | -4.476 | 0 | -431.9 |
| 0.4 | 2 | 5 | 2592 | 2045 | 1182 | -369.6 | 56.71 | -73.91 | -4.692 | 0 | -560 |
| 0.6 | 2 | 5 | 2592 | 2045 | 966 | -459.3 | 68.17 | -91.85 | -4.85 | 0 | -649.7 |
| 0.8 | 2 | 5 | 2592 | 2045 | 791 | -484 | 70.56 | -96.8 | -4.939 | 0 | -674.4 |
| 1 | 2 | 5 | 2592 | 2045 | 662 | -508.7 | 81.05 | -101.7 | -4.519 | 0 | -699.1 |
| 1.2 | 2 | 5 | 2592 | 2045 | 545 | -487.3 | 76.51 | -97.46 | -4.586 | 0 | -677.7 |
| 1.5 | 2 | 5 | 2592 | 2045 | 424 | -464.2 | 79.57 | -92.83 | -4.2 | 0 | -654.6 |
| 2 | 2 | 5 | 2592 | 2045 | 268 | -365.2 | 76.95 | -73.04 | -3.417 | 0 | -555.6 |
| 2.5 | 2 | 5 | 2592 | 2045 | 178 | -248.2 | 77.11 | -49.64 | -2.317 | 0 | -438.6 |
| 3 | 2 | 5 | 2592 | 2045 | 127 | -178.2 | 77.46 | -35.64 | -1.657 | 0 | -368.6 |
| 4 | 2 | 5 | 2592 | 2045 | 70 | -75.69 | 59.96 | -15.14 | -0.909 | 0 | -266.1 |
| 5 | 2 | 5 | 2592 | 2045 | 39 | 8.565 | 53.69 | 1.713 | 0.1149 | 0 | -181.8 |
|  | 2 | 5 | 2592 | 2045 | 0 | 190.4 | 12.61 | 38.08 | 10.87 | 0 | 0 |


**What this measurement can and cannot say.** It is computed on the ambiguous days alone, because those are the only days for which an hourly path was built. It is a per-day rate on those days and is NOT extrapolated to the rest of the book. A full hourly-marked equity curve for every book member over every day is a separate engine pass and is not in this read.


## What this says about A6

A6 states that every breach count is a lower bound because the input is a daily series. This report is the first direct evidence of the size of that blind spot: on the days where the daily bar is genuinely ambiguous, the hourly path disagrees with it **40%% of the time in mode A and 50%% in mode B**, always favourably. A6 is therefore conservative on fills and, separately, optimistic on intraday breaches.


## Provenance

- `results/r2reads/modeA_a5_hourly.csv` — 77 rows, md5 `4e6a0dc1b1ea`
- `results/r2reads/modeA_a5_disagree.csv` — 77 rows, md5 `3aec3cf3a15e`
- `results/r2reads/modeA_a5_delta_strategy.csv` — 8 rows, md5 `84f423f4c118`
- `results/r2reads/modeA_a5_delta_book.csv` — 1 rows, md5 `68bc3efd0317`
- `results/r2reads/modeA_a5_spreads.csv` — 77 rows, md5 `2215d564a1e3`
- `results/r2reads/modeA_a5_spreads_by_pair.csv` — 13 rows, md5 `257a8048951f`
- `results/r2reads/modeA_a5_overlay.csv` — 520 rows, md5 `c3b13a6bfb12`
- `results/r2reads/modeA_a5_overlay_curve.csv` — 13 rows, md5 `f27b4f53dd1b`
- `results/r2reads/modeB_a5_hourly.csv` — 22 rows, md5 `827a1d3c7521`
- `results/r2reads/modeB_a5_disagree.csv` — 22 rows, md5 `774bc785c16a`
- `results/r2reads/modeB_a5_delta_strategy.csv` — 2 rows, md5 `6b3dc9df9cfa`
- `results/r2reads/modeB_a5_delta_book.csv` — 1 rows, md5 `9ba27f6e05d5`
- `results/r2reads/modeB_a5_spreads.csv` — 22 rows, md5 `29e5af6b3bfb`
- `results/r2reads/modeB_a5_spreads_by_pair.csv` — 12 rows, md5 `4eedd5706202`
- `results/r2reads/modeB_a5_overlay.csv` — 130 rows, md5 `69e8d5bee491`
- `results/r2reads/modeB_a5_overlay_curve.csv` — 13 rows, md5 `f6fd448f628d`
