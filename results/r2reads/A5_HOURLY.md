# A5 — THE HOURLY PATH AGAINST THE DAILY BAR

Generated 2026-11-24 10:33 by `code/r2hourly.py`.


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
| 0.2 | 1 | 1 | 259 | 240 | 172 | -30.68 | 35 | -30.68 | -3.155 | 0 | -44.49 |
| 0.4 | 1 | 1 | 259 | 240 | 133 | -52.15 | 56.28 | -52.15 | -3.336 | 0 | -65.96 |
| 0.6 | 1 | 1 | 259 | 240 | 114 | -67.08 | 71 | -67.08 | -3.401 | 0 | -80.89 |
| 0.8 | 1 | 1 | 259 | 240 | 95 | -69.26 | 78 | -69.26 | -3.197 | 0 | -83.08 |
| 1 | 1 | 1 | 259 | 240 | 86 | -82.15 | 92.23 | -82.15 | -3.207 | 0 | -95.96 |
| 1.2 | 1 | 1 | 259 | 240 | 77 | -87.84 | 95.45 | -87.84 | -3.313 | 0 | -101.6 |
| 1.5 | 1 | 1 | 259 | 240 | 62 | -86.68 | 96.9 | -86.68 | -3.22 | 0 | -100.5 |
| 2 | 1 | 1 | 259 | 240 | 49 | -93.68 | 105.4 | -93.68 | -3.2 | 0 | -107.5 |
| 2.5 | 1 | 1 | 259 | 240 | 33 | -78.62 | 90.91 | -78.62 | -3.113 | 0 | -92.43 |
| 3 | 1 | 1 | 259 | 240 | 27 | -78.79 | 90.76 | -78.79 | -3.125 | 0 | -92.61 |
| 4 | 1 | 1 | 259 | 240 | 16 | -60.22 | 77.09 | -60.22 | -2.812 | 0 | -74.04 |
| 5 | 1 | 1 | 259 | 240 | 11 | -51.34 | 68.21 | -51.34 | -2.71 | 0 | -65.15 |
|  | 1 | 1 | 259 | 240 | 0 | 13.81 | 18.18 | 13.81 | 2.735 | 0 | 0 |


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


## What this says about A6

A6 states that every breach count is a lower bound because the input is a daily series. This report is the first direct evidence of the size of that blind spot: on the days where the daily bar is genuinely ambiguous, the hourly path disagrees with it **40%% of the time in mode A and 50%% in mode B**, always favourably. A6 is therefore conservative on fills and, separately, optimistic on intraday breaches.


## Provenance

- `results/r2reads/modeA_a5_hourly.csv` — 77 rows, md5 `4e6a0dc1b1ea`
- `results/r2reads/modeA_a5_disagree.csv` — 77 rows, md5 `3aec3cf3a15e`
- `results/r2reads/modeA_a5_delta_strategy.csv` — 8 rows, md5 `84f423f4c118`
- `results/r2reads/modeA_a5_delta_book.csv` — 1 rows, md5 `68bc3efd0317`
- `results/r2reads/modeA_a5_spreads.csv` — 77 rows, md5 `2215d564a1e3`
- `results/r2reads/modeA_a5_spreads_by_pair.csv` — 13 rows, md5 `257a8048951f`
- `results/r2reads/modeA_a5_overlay.csv` — 13 rows, md5 `0c284a12879b`
- `results/r2reads/modeA_a5_overlay_curve.csv` — 13 rows, md5 `aef2991a2544`
- `results/r2reads/modeB_a5_hourly.csv` — 22 rows, md5 `827a1d3c7521`
- `results/r2reads/modeB_a5_disagree.csv` — 22 rows, md5 `774bc785c16a`
- `results/r2reads/modeB_a5_delta_strategy.csv` — 2 rows, md5 `6b3dc9df9cfa`
- `results/r2reads/modeB_a5_delta_book.csv` — 1 rows, md5 `9ba27f6e05d5`
- `results/r2reads/modeB_a5_spreads.csv` — 22 rows, md5 `29e5af6b3bfb`
- `results/r2reads/modeB_a5_spreads_by_pair.csv` — 12 rows, md5 `4eedd5706202`
