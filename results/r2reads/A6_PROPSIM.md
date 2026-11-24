# A6 — THE PROP SIMULATOR, MODE A

Generated 2026-11-24 00:08 by `code/r2reads.py`, a **pure read** of the saved daily series. Built as a standing stage: every later book runs through it.


## The rules as modelled

| rule | value |
|---|---|
| trailing floor | 6%% below the high-water mark, **stops trailing permanently once the floor reaches the starting balance** — after equity touches +6%% once, the floor is $100k forever. Not a start-of-day lock. |
| open equity | counts for the trailing line, rolling |
| daily loss | 4%%, measured from the previous daily close; floating losses count; resets daily |
| evaluation | profit target 10%%, no time limit, no minimum days, no consistency rule |
| payout | 80%%, from day 0, every 7 days |
| fee | $549; evaluation resettable, funded not |
| leverage | 1:30 |
| internal budgets | 3.6%% daily, 5.4%% trailing — reported alongside the firm's |

**WHAT THIS CANNOT SEE.** The input is a DAILY series, so open equity is only observable at the close. Rules written on intraday open equity are evaluated at day granularity, which makes every breach count below a **LOWER BOUND**: an intraday excursion that breached and recovered before the close is invisible here. A5's hourly replay is what would tighten it.


## Evaluation phase

| source | book | budget | rules | days | passed_eval_day | breached | equity_end | worst_dip_pct |
|---|---|---|---|---|---|---|---|---|
| winners | allon | team1 | firm | 771 | 770 |  | 1.103e+05 | 1.066 |
| winners | allon | team1 | internal | 771 | 770 |  | 1.103e+05 | 1.066 |
| winners | allon | team2 | firm | 711 | 710 |  | 1.104e+05 | 1.598 |
| winners | allon | team2 | internal | 711 | 710 |  | 1.104e+05 | 1.598 |


**4 of 4 evaluation runs reached the 10% target; 0 breached.**


## Funded phase — fixed sizing, payout cushion swept

| source | book | budget | rules | keep_cushion | days | breached | paid_out_per_year | return_pct_per_year | worst_dip_pct | net_per_year_usd |
|---|---|---|---|---|---|---|---|---|---|---|
| winners | allon | team2 | firm | 0 | 1,281 |  | 4628 | 4.352 | 4.21 | 4520 |
| winners | allon | team2 | internal | 0 | 1,281 |  | 4628 | 4.352 | 4.21 | 4520 |
| winners | allon | team2 | firm | 0.02 | 1,281 |  | 4322 | 4.434 | 4.21 | 4214 |
| winners | allon | team2 | internal | 0.02 | 1,281 |  | 4322 | 4.434 | 4.21 | 4214 |
| winners | allon | team2 | firm | 0.05 | 1,281 |  | 3849 | 4.543 | 4.21 | 3741 |
| winners | allon | team2 | internal | 0.05 | 1,281 |  | 3849 | 4.543 | 4.21 | 3741 |
| winners | allon | team1 | firm | 0 | 1,281 |  | 3090 | 2.906 | 2.826 | 2982 |
| winners | allon | team1 | internal | 0 | 1,281 |  | 3090 | 2.906 | 2.826 | 2982 |
| winners | allon | team2 | firm | 0.1 | 1,281 |  | 3022 | 4.686 | 4.21 | 2914 |
| winners | allon | team2 | internal | 0.1 | 1,281 |  | 3022 | 4.686 | 4.21 | 2914 |
| winners | allon | team1 | firm | 0.02 | 1,281 |  | 2753 | 2.959 | 2.826 | 2645 |
| winners | allon | team1 | internal | 0.02 | 1,281 |  | 2753 | 2.959 | 2.826 | 2645 |
| winners | allon | team1 | firm | 0.05 | 1,281 |  | 2235 | 3.025 | 2.826 | 2127 |
| winners | allon | team1 | internal | 0.05 | 1,281 |  | 2235 | 3.025 | 2.826 | 2127 |
| winners | allon | team1 | firm | 0.1 | 1,281 |  | 1330 | 3.095 | 2.826 | 1222 |
| winners | allon | team1 | internal | 0.1 | 1,281 |  | 1330 | 3.095 | 2.826 | 1222 |


## Funded phase — sizing proportional to the cushion above the floor

| source | book | budget | rules | size_frac | days | breached | paid_out_per_year | return_pct_per_year | worst_dip_pct | net_per_year_usd |
|---|---|---|---|---|---|---|---|---|---|---|
| winners | allon | team2 | firm | 2 | 1,281 |  | 537.8 | 0.5063 | 0.4955 | 429.8 |
| winners | allon | team2 | internal | 2 | 1,281 |  | 484.1 | 0.4557 | 0.4461 | 376.1 |
| winners | allon | team2 | firm | 1.5 | 1,281 |  | 407 | 0.3831 | 0.3754 | 299 |
| winners | allon | team2 | internal | 1.5 | 1,281 |  | 366.4 | 0.3448 | 0.3379 | 258.4 |
| winners | allon | team1 | firm | 2 | 1,281 |  | 362.9 | 0.3415 | 0.3348 | 254.9 |
| winners | allon | team1 | internal | 2 | 1,281 |  | 326.6 | 0.3074 | 0.3014 | 218.6 |
| winners | allon | team1 | firm | 1.5 | 1,281 |  | 273.8 | 0.2577 | 0.2528 | 165.8 |
| winners | allon | team2 | firm | 1 | 1,281 |  | 273.8 | 0.2577 | 0.2528 | 165.8 |
| winners | allon | team2 | internal | 1 | 1,281 |  | 246.5 | 0.2319 | 0.2275 | 138.5 |
| winners | allon | team1 | internal | 1.5 | 1,281 |  | 246.5 | 0.2319 | 0.2275 | 138.5 |
| winners | allon | team2 | firm | 0.75 | 1,281 |  | 206.3 | 0.1941 | 0.1905 | 98.32 |
| winners | allon | team2 | internal | 0.75 | 1,281 |  | 185.7 | 0.1747 | 0.1715 | 77.69 |
| winners | allon | team1 | firm | 1 | 1,281 |  | 183.7 | 0.1728 | 0.1697 | 75.67 |
| winners | allon | team1 | internal | 1 | 1,281 |  | 165.3 | 0.1555 | 0.1527 | 57.31 |
| winners | allon | team2 | firm | 0.5 | 1,281 |  | 138.2 | 0.13 | 0.1277 | 30.17 |
| winners | allon | team1 | firm | 0.75 | 1,281 |  | 138.2 | 0.13 | 0.1277 | 30.17 |
| winners | allon | team1 | internal | 0.75 | 1,281 |  | 124.4 | 0.117 | 0.1149 | 16.36 |
| winners | allon | team2 | internal | 0.5 | 1,281 |  | 124.4 | 0.117 | 0.1149 | 16.36 |
| winners | allon | team1 | firm | 0.5 | 1,281 |  | 92.39 | 0.0869 | 0.0854 | -15.61 |
| winners | allon | team1 | internal | 0.5 | 1,281 |  | 83.16 | 0.07822 | 0.07687 | -24.84 |
| winners | allon | team2 | firm | 0.25 | 1,281 |  | 69.4 | 0.06527 | 0.06416 | -38.6 |
| winners | allon | team2 | internal | 0.25 | 1,281 |  | 62.46 | 0.05875 | 0.05775 | -45.54 |
| winners | allon | team1 | firm | 0.25 | 1,281 |  | 46.34 | 0.04358 | 0.04285 | -61.66 |
| winners | allon | team1 | internal | 0.25 | 1,281 |  | 41.7 | 0.03922 | 0.03856 | -66.3 |


**0 of 40 funded runs breached.** Best payout is **$4628 a year** before the $549 fee.


## Provenance

| file | rows | md5 |
|---|---|---|
| `results/r2reads/modeA_a6_propsim_winners.csv` | 44 | 5a7a078530fc |
