# A6 — THE PROP SIMULATOR, MODE A

Generated 2026-11-24 00:48 by `code/r2reads.py`, a **pure read** of the saved daily series. Built as a standing stage: every later book runs through it.


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
| full | allon | team1 | firm | 1,130 |  | trailing | 9.525e+04 | 5.824 |
| full | allon | team1 | internal | 839 |  | trailing | 9.569e+04 | 5.283 |
| full | allon | team2 | firm | 813 |  | trailing | 9.587e+04 | 5.369 |
| full | allon | team2 | internal | 668 |  | trailing | 9.651e+04 | 5.145 |
| full | chop_trend | team1 | firm | 1,296 |  |  | 9.566e+04 | 5.199 |
| full | chop_trend | team1 | internal | 1,296 |  |  | 9.566e+04 | 5.199 |
| full | chop_trend | team2 | firm | 830 |  | trailing | 9.494e+04 | 5.863 |
| full | chop_trend | team2 | internal | 826 |  | trailing | 9.535e+04 | 5.226 |
| full | chop_ungated | team1 | firm | 1,296 |  |  | 9.717e+04 | 4.426 |
| full | chop_ungated | team1 | internal | 1,296 |  |  | 9.717e+04 | 4.426 |
| full | chop_ungated | team2 | firm | 839 |  | trailing | 9.586e+04 | 5.724 |
| full | chop_ungated | team2 | internal | 832 |  | trailing | 9.65e+04 | 5.266 |
| full | chop_notrange | team1 | firm | 832 |  | trailing | 9.519e+04 | 5.884 |
| full | chop_notrange | team1 | internal | 820 |  | trailing | 9.582e+04 | 5.316 |
| full | chop_notrange | team2 | firm | 514 |  | trailing | 9.578e+04 | 5.782 |
| full | chop_notrange | team2 | internal | 505 |  | trailing | 9.64e+04 | 5.159 |


**4 of 20 evaluation runs reached the 10% target; 12 breached.**


## Funded phase — fixed sizing, payout cushion swept

| source | book | budget | rules | keep_cushion | days | breached | paid_out_per_year | return_pct_per_year | worst_dip_pct | net_per_year_usd |
|---|---|---|---|---|---|---|---|---|---|---|
| winners | allon | team2 | firm | 0 | 1,281 |  | 4628 | 4.352 | 4.21 | 4520 |
| winners | allon | team2 | internal | 0 | 1,281 |  | 4628 | 4.352 | 4.21 | 4520 |
| winners | allon | team2 | internal | 0.02 | 1,281 |  | 4322 | 4.434 | 4.21 | 4214 |
| winners | allon | team2 | firm | 0.02 | 1,281 |  | 4322 | 4.434 | 4.21 | 4214 |
| winners | allon | team2 | internal | 0.05 | 1,281 |  | 3849 | 4.543 | 4.21 | 3741 |
| winners | allon | team2 | firm | 0.05 | 1,281 |  | 3849 | 4.543 | 4.21 | 3741 |
| winners | allon | team1 | firm | 0 | 1,281 |  | 3090 | 2.906 | 2.826 | 2982 |
| winners | allon | team1 | internal | 0 | 1,281 |  | 3090 | 2.906 | 2.826 | 2982 |
| winners | allon | team2 | firm | 0.1 | 1,281 |  | 3022 | 4.686 | 4.21 | 2914 |
| winners | allon | team2 | internal | 0.1 | 1,281 |  | 3022 | 4.686 | 4.21 | 2914 |
| winners | allon | team1 | firm | 0.02 | 1,281 |  | 2753 | 2.959 | 2.826 | 2645 |
| winners | allon | team1 | internal | 0.02 | 1,281 |  | 2753 | 2.959 | 2.826 | 2645 |
| winners | allon | team1 | firm | 0.05 | 1,281 |  | 2235 | 3.025 | 2.826 | 2127 |
| winners | allon | team1 | internal | 0.05 | 1,281 |  | 2235 | 3.025 | 2.826 | 2127 |
| winners | allon | team1 | internal | 0.1 | 1,281 |  | 1330 | 3.095 | 2.826 | 1222 |
| winners | allon | team1 | firm | 0.1 | 1,281 |  | 1330 | 3.095 | 2.826 | 1222 |
| full | chop_ungated | team2 | internal | 0 | 314 | trailing | 1230 | -2.107 | 5.293 | 789.7 |
| full | chop_notrange | team2 | internal | 0 | 482 | trailing | 791.5 | -1.627 | 5.34 | 504.4 |
| full | chop_notrange | team2 | firm | 0 | 506 | trailing | 753.9 | -1.8 | 5.894 | 480.5 |
| full | chop_trend | team2 | internal | 0 | 313 | trailing | 599.3 | -3.197 | 5.089 | 157.3 |
| full | allon | team2 | internal | 0 | 664 | trailing | 585 | -1.147 | 5.27 | 376.6 |
| full | allon | team2 | firm | 0 | 813 | trailing | 477.8 | -1.255 | 5.762 | 307.6 |
| full | chop_ungated | team2 | firm | 0 | 830 | trailing | 465.4 | -1.001 | 5.908 | 298.7 |
| full | allon | team1 | internal | 0 | 837 | trailing | 314.5 | -1.193 | 5.285 | 149.2 |
| full | chop_notrange | team1 | internal | 0 | 813 | trailing | 312.8 | -1.225 | 5.323 | 142.6 |
| full | allon | team1 | firm | 0 | 842 | trailing | 312.6 | -1.335 | 5.949 | 148.3 |
| full | chop_notrange | team1 | firm | 0 | 825 | trailing | 308.2 | -1.344 | 5.912 | 140.5 |
| full | chop_trend | team2 | firm | 0 | 826 | trailing | 227.1 | -1.407 | 5.806 | 59.61 |
| full | chop_ungated | team1 | internal | 0 | 1,296 |  | 198.6 | -0.5431 | 4.946 | 91.83 |
| full | chop_ungated | team1 | firm | 0 | 1,296 |  | 198.6 | -0.5431 | 4.946 | 91.83 |
| full | chop_trend | team1 | internal | 0 | 1,134 | trailing | 110.3 | -0.9847 | 5.349 | -11.7 |
| full | chop_trend | team1 | firm | 0 | 1,296 |  | 96.51 | -0.8397 | 5.586 | -10.24 |
| full | allon | team2 | firm | 0.1 | 813 | trailing | 0 | -1.28 | 5.369 | -170.2 |
| full | chop_notrange | team1 | firm | 0.1 | 832 | trailing | 0 | -1.458 | 5.884 | -166.3 |
| full | chop_ungated | team2 | firm | 0.05 | 839 | trailing | 0 | -1.244 | 5.724 | -164.9 |
| full | chop_ungated | team2 | firm | 0.1 | 839 | trailing | 0 | -1.244 | 5.724 | -164.9 |
| full | allon | team1 | internal | 0.05 | 839 | trailing | 0 | -1.295 | 5.283 | -164.9 |
| full | chop_ungated | team2 | internal | 0.02 | 832 | trailing | 0 | -1.06 | 5.266 | -166.3 |
| full | chop_ungated | team2 | internal | 0.05 | 832 | trailing | 0 | -1.06 | 5.266 | -166.3 |
| full | chop_ungated | team2 | internal | 0.1 | 832 | trailing | 0 | -1.06 | 5.266 | -166.3 |
| full | allon | team1 | internal | 0.02 | 839 | trailing | 0 | -1.295 | 5.283 | -164.9 |
| full | chop_notrange | team1 | firm | 0.02 | 832 | trailing | 0 | -1.458 | 5.884 | -166.3 |
| full | chop_notrange | team1 | firm | 0.05 | 832 | trailing | 0 | -1.458 | 5.884 | -166.3 |
| full | allon | team1 | firm | 0.1 | 1,130 | trailing | 0 | -1.06 | 5.824 | -122.4 |
| full | allon | team1 | internal | 0.1 | 839 | trailing | 0 | -1.295 | 5.283 | -164.9 |
| full | chop_notrange | team1 | internal | 0.02 | 820 | trailing | 0 | -1.285 | 5.316 | -168.7 |
| full | chop_notrange | team1 | internal | 0.05 | 820 | trailing | 0 | -1.285 | 5.316 | -168.7 |
| full | chop_notrange | team1 | internal | 0.1 | 820 | trailing | 0 | -1.285 | 5.316 | -168.7 |
| full | allon | team1 | firm | 0.05 | 1,130 | trailing | 0 | -1.06 | 5.824 | -122.4 |
| full | chop_notrange | team2 | firm | 0.02 | 514 | trailing | 0 | -2.07 | 5.782 | -269.2 |
| full | chop_notrange | team2 | firm | 0.05 | 514 | trailing | 0 | -2.07 | 5.782 | -269.2 |
| full | chop_notrange | team2 | firm | 0.1 | 514 | trailing | 0 | -2.07 | 5.782 | -269.2 |
| full | allon | team1 | firm | 0.02 | 1,130 | trailing | 0 | -1.06 | 5.824 | -122.4 |
| full | chop_notrange | team2 | internal | 0.02 | 505 | trailing | 0 | -1.798 | 5.159 | -274 |
| full | chop_notrange | team2 | internal | 0.05 | 505 | trailing | 0 | -1.798 | 5.159 | -274 |
| full | chop_ungated | team2 | firm | 0.02 | 839 | trailing | 0 | -1.244 | 5.724 | -164.9 |
| full | chop_ungated | team1 | internal | 0.05 | 1,296 |  | 0 | -0.5505 | 4.426 | -106.8 |
| full | chop_ungated | team1 | internal | 0.1 | 1,296 |  | 0 | -0.5505 | 4.426 | -106.8 |
| full | chop_trend | team2 | firm | 0.02 | 830 | trailing | 0 | -1.537 | 5.863 | -166.7 |
| full | allon | team2 | internal | 0.05 | 668 | trailing | 0 | -1.317 | 5.145 | -207.1 |
| full | allon | team2 | internal | 0.1 | 668 | trailing | 0 | -1.317 | 5.145 | -207.1 |
| full | chop_trend | team1 | firm | 0.02 | 1,296 |  | 0 | -0.8443 | 5.199 | -106.8 |
| full | chop_trend | team1 | firm | 0.05 | 1,296 |  | 0 | -0.8443 | 5.199 | -106.8 |
| full | chop_trend | team1 | firm | 0.1 | 1,296 |  | 0 | -0.8443 | 5.199 | -106.8 |
| full | chop_trend | team1 | internal | 0.02 | 1,296 |  | 0 | -0.8443 | 5.199 | -106.8 |
| full | chop_trend | team1 | internal | 0.05 | 1,296 |  | 0 | -0.8443 | 5.199 | -106.8 |
| full | chop_trend | team1 | internal | 0.1 | 1,296 |  | 0 | -0.8443 | 5.199 | -106.8 |
| full | allon | team2 | firm | 0.05 | 813 | trailing | 0 | -1.28 | 5.369 | -170.2 |
| full | chop_trend | team2 | firm | 0.05 | 830 | trailing | 0 | -1.537 | 5.863 | -166.7 |
| full | allon | team2 | internal | 0.02 | 668 | trailing | 0 | -1.317 | 5.145 | -207.1 |
| full | chop_trend | team2 | firm | 0.1 | 830 | trailing | 0 | -1.537 | 5.863 | -166.7 |
| full | allon | team2 | firm | 0.02 | 813 | trailing | 0 | -1.28 | 5.369 | -170.2 |
| full | chop_trend | team2 | internal | 0.02 | 826 | trailing | 0 | -1.419 | 5.226 | -167.5 |
| full | chop_trend | team2 | internal | 0.05 | 826 | trailing | 0 | -1.419 | 5.226 | -167.5 |
| full | chop_trend | team2 | internal | 0.1 | 826 | trailing | 0 | -1.419 | 5.226 | -167.5 |
| full | chop_ungated | team1 | firm | 0.02 | 1,296 |  | 0 | -0.5505 | 4.426 | -106.8 |
| full | chop_ungated | team1 | firm | 0.05 | 1,296 |  | 0 | -0.5505 | 4.426 | -106.8 |
| full | chop_ungated | team1 | firm | 0.1 | 1,296 |  | 0 | -0.5505 | 4.426 | -106.8 |
| full | chop_ungated | team1 | internal | 0.02 | 1,296 |  | 0 | -0.5505 | 4.426 | -106.8 |
| full | chop_notrange | team2 | internal | 0.1 | 505 | trailing | 0 | -1.798 | 5.159 | -274 |


## Funded phase — sizing proportional to the cushion above the floor

| source | book | budget | rules | size_frac | days | breached | paid_out_per_year | return_pct_per_year | worst_dip_pct | net_per_year_usd |
|---|---|---|---|---|---|---|---|---|---|---|
| winners | allon | team2 | firm | 2 | 1,281 |  | 537.8 | 0.5063 | 0.4955 | 429.8 |
| winners | allon | team2 | internal | 2 | 1,281 |  | 484.1 | 0.4557 | 0.4461 | 376.1 |
| winners | allon | team2 | firm | 1.5 | 1,281 |  | 407 | 0.3831 | 0.3754 | 299 |
| winners | allon | team2 | internal | 1.5 | 1,281 |  | 366.4 | 0.3448 | 0.3379 | 258.4 |
| winners | allon | team1 | firm | 2 | 1,281 |  | 362.9 | 0.3415 | 0.3348 | 254.9 |
| winners | allon | team1 | internal | 2 | 1,281 |  | 326.6 | 0.3074 | 0.3014 | 218.6 |
| winners | allon | team2 | firm | 1 | 1,281 |  | 273.8 | 0.2577 | 0.2528 | 165.8 |
| winners | allon | team1 | firm | 1.5 | 1,281 |  | 273.8 | 0.2577 | 0.2528 | 165.8 |
| winners | allon | team1 | internal | 1.5 | 1,281 |  | 246.5 | 0.2319 | 0.2275 | 138.5 |
| winners | allon | team2 | internal | 1 | 1,281 |  | 246.5 | 0.2319 | 0.2275 | 138.5 |
| winners | allon | team2 | firm | 0.75 | 1,281 |  | 206.3 | 0.1941 | 0.1905 | 98.32 |
| winners | allon | team2 | internal | 0.75 | 1,281 |  | 185.7 | 0.1747 | 0.1715 | 77.69 |
| winners | allon | team1 | firm | 1 | 1,281 |  | 183.7 | 0.1728 | 0.1697 | 75.67 |
| winners | allon | team1 | internal | 1 | 1,281 |  | 165.3 | 0.1555 | 0.1527 | 57.31 |
| winners | allon | team2 | firm | 0.5 | 1,281 |  | 138.2 | 0.13 | 0.1277 | 30.17 |
| winners | allon | team1 | firm | 0.75 | 1,281 |  | 138.2 | 0.13 | 0.1277 | 30.17 |
| winners | allon | team2 | internal | 0.5 | 1,281 |  | 124.4 | 0.117 | 0.1149 | 16.36 |
| winners | allon | team1 | internal | 0.75 | 1,281 |  | 124.4 | 0.117 | 0.1149 | 16.36 |
| winners | allon | team1 | firm | 0.5 | 1,281 |  | 92.39 | 0.0869 | 0.0854 | -15.61 |
| winners | allon | team1 | internal | 0.5 | 1,281 |  | 83.16 | 0.07822 | 0.07687 | -24.84 |
| winners | allon | team2 | firm | 0.25 | 1,281 |  | 69.4 | 0.06527 | 0.06416 | -38.6 |
| winners | allon | team2 | internal | 0.25 | 1,281 |  | 62.46 | 0.05875 | 0.05775 | -45.54 |
| winners | allon | team1 | firm | 0.25 | 1,281 |  | 46.34 | 0.04358 | 0.04285 | -61.66 |
| winners | allon | team1 | internal | 0.25 | 1,281 |  | 41.7 | 0.03922 | 0.03856 | -66.3 |
| full | chop_ungated | team2 | firm | 2 | 1,296 |  | 35.42 | -0.09354 | 0.8585 | -71.33 |
| full | chop_notrange | team2 | firm | 2 | 1,296 |  | 34.94 | -0.1673 | 1.219 | -71.81 |
| full | allon | team2 | firm | 2 | 1,296 |  | 33.64 | -0.1728 | 1.229 | -73.11 |
| full | chop_ungated | team2 | internal | 2 | 1,296 |  | 31.87 | -0.0842 | 0.7729 | -74.88 |
| full | chop_notrange | team2 | internal | 2 | 1,296 |  | 31.45 | -0.1507 | 1.097 | -75.3 |
| full | allon | team2 | internal | 2 | 1,296 |  | 30.29 | -0.1555 | 1.106 | -76.46 |
| full | chop_ungated | team2 | firm | 1.5 | 1,296 |  | 26.61 | -0.07109 | 0.6528 | -80.14 |
| full | chop_notrange | team2 | firm | 1.5 | 1,296 |  | 26.27 | -0.129 | 0.9364 | -80.48 |
| full | allon | team2 | firm | 1.5 | 1,296 |  | 25.98 | -0.1324 | 0.9435 | -80.77 |
| full | chop_ungated | team2 | internal | 1.5 | 1,296 |  | 23.95 | -0.06399 | 0.5876 | -82.8 |
| full | chop_ungated | team1 | firm | 2 | 1,296 |  | 23.67 | -0.06346 | 0.5829 | -83.08 |
| full | chop_notrange | team2 | internal | 1.5 | 1,296 |  | 23.65 | -0.1162 | 0.8431 | -83.1 |
| full | allon | team2 | internal | 1.5 | 1,296 |  | 23.39 | -0.1192 | 0.8495 | -83.36 |
| full | chop_notrange | team1 | firm | 2 | 1,296 |  | 23.37 | -0.1158 | 0.8392 | -83.38 |
| full | allon | team1 | firm | 2 | 1,296 |  | 23.32 | -0.1185 | 0.8453 | -83.43 |
| full | chop_ungated | team1 | internal | 2 | 1,296 |  | 21.3 | -0.05712 | 0.5247 | -85.45 |
| full | chop_notrange | team1 | internal | 2 | 1,296 |  | 21.04 | -0.1042 | 0.7555 | -85.71 |
| full | allon | team1 | internal | 2 | 1,296 |  | 21 | -0.1067 | 0.7611 | -85.75 |
| full | allon | team2 | firm | 1 | 1,296 |  | 17.84 | -0.09014 | 0.6441 | -88.91 |
| full | allon | team1 | firm | 1.5 | 1,296 |  | 17.84 | -0.09014 | 0.6441 | -88.91 |
| full | chop_ungated | team2 | firm | 1 | 1,296 |  | 17.78 | -0.04799 | 0.4411 | -88.97 |
| full | chop_ungated | team1 | firm | 1.5 | 1,296 |  | 17.78 | -0.04799 | 0.4411 | -88.97 |
| full | chop_notrange | team2 | firm | 1 | 1,296 |  | 17.56 | -0.08842 | 0.6397 | -89.19 |
| full | chop_notrange | team1 | firm | 1.5 | 1,296 |  | 17.56 | -0.08842 | 0.6397 | -89.19 |
| full | chop_trend | team2 | firm | 2 | 1,296 |  | 17.27 | -0.1439 | 0.9655 | -89.48 |
| full | allon | team1 | internal | 1.5 | 1,296 |  | 16.06 | -0.08114 | 0.5798 | -90.69 |
| full | allon | team2 | internal | 1 | 1,296 |  | 16.06 | -0.08114 | 0.5798 | -90.69 |
| full | chop_ungated | team2 | internal | 1 | 1,296 |  | 16 | -0.04319 | 0.3971 | -90.75 |
| full | chop_ungated | team1 | internal | 1.5 | 1,296 |  | 16 | -0.04319 | 0.3971 | -90.75 |
| full | chop_notrange | team1 | internal | 1.5 | 1,296 |  | 15.81 | -0.0796 | 0.5759 | -90.94 |
| full | chop_notrange | team2 | internal | 1 | 1,296 |  | 15.81 | -0.0796 | 0.5759 | -90.94 |
| full | chop_trend | team2 | internal | 2 | 1,296 |  | 15.54 | -0.1296 | 0.8693 | -91.21 |
| full | allon | team2 | firm | 0.75 | 1,296 |  | 13.57 | -0.06833 | 0.4888 | -93.18 |
| full | chop_ungated | team2 | firm | 0.75 | 1,296 |  | 13.35 | -0.03621 | 0.3331 | -93.4 |
| full | chop_notrange | team2 | firm | 0.75 | 1,296 |  | 13.19 | -0.06723 | 0.4857 | -93.56 |
| full | chop_trend | team2 | firm | 1.5 | 1,296 |  | 12.97 | -0.1097 | 0.7351 | -93.78 |
| full | allon | team2 | internal | 0.75 | 1,296 |  | 12.22 | -0.0615 | 0.44 | -94.53 |
| full | allon | team1 | firm | 1 | 1,296 |  | 12.12 | -0.06095 | 0.4362 | -94.63 |
| full | chop_ungated | team2 | internal | 0.75 | 1,296 |  | 12.01 | -0.03259 | 0.2998 | -94.74 |
| full | chop_notrange | team2 | internal | 0.75 | 1,296 |  | 11.87 | -0.06052 | 0.4372 | -94.88 |
| full | chop_ungated | team1 | firm | 1 | 1,296 |  | 11.87 | -0.03225 | 0.2967 | -94.88 |
| full | chop_notrange | team1 | firm | 1 | 1,296 |  | 11.73 | -0.06003 | 0.4335 | -95.02 |
| full | chop_trend | team2 | internal | 1.5 | 1,296 |  | 11.68 | -0.09874 | 0.6618 | -95.07 |
| full | chop_trend | team1 | firm | 2 | 1,296 |  | 11.54 | -0.09802 | 0.6567 | -95.21 |
| full | allon | team1 | internal | 1 | 1,296 |  | 10.91 | -0.05486 | 0.3927 | -95.84 |
| full | chop_ungated | team1 | internal | 1 | 1,296 |  | 10.68 | -0.02902 | 0.2671 | -96.07 |
| full | chop_notrange | team1 | internal | 1 | 1,296 |  | 10.56 | -0.05403 | 0.3902 | -96.19 |
| full | chop_trend | team1 | internal | 2 | 1,296 |  | 10.38 | -0.08823 | 0.5912 | -96.37 |
| full | allon | team1 | firm | 0.75 | 1,296 |  | 9.177 | -0.04604 | 0.3298 | -97.57 |
| full | allon | team2 | firm | 0.5 | 1,296 |  | 9.177 | -0.04604 | 0.3298 | -97.57 |
| full | chop_ungated | team2 | firm | 0.5 | 1,296 |  | 8.906 | -0.02428 | 0.2235 | -97.84 |
| full | chop_ungated | team1 | firm | 0.75 | 1,296 |  | 8.906 | -0.02428 | 0.2235 | -97.84 |
| full | chop_notrange | team1 | firm | 0.75 | 1,296 |  | 8.804 | -0.04543 | 0.3278 | -97.95 |
| full | chop_notrange | team2 | firm | 0.5 | 1,296 |  | 8.804 | -0.04543 | 0.3278 | -97.95 |
| full | chop_trend | team1 | firm | 1.5 | 1,296 |  | 8.663 | -0.07429 | 0.4974 | -98.09 |
| full | chop_trend | team2 | firm | 1 | 1,296 |  | 8.663 | -0.07429 | 0.4974 | -98.09 |
| full | allon | team1 | internal | 0.75 | 1,296 |  | 8.261 | -0.04144 | 0.2968 | -98.49 |
| full | allon | team2 | internal | 0.5 | 1,296 |  | 8.261 | -0.04144 | 0.2968 | -98.49 |
| full | chop_ungated | team2 | internal | 0.5 | 1,296 |  | 8.015 | -0.02185 | 0.2012 | -98.73 |
| full | chop_ungated | team1 | internal | 0.75 | 1,296 |  | 8.015 | -0.02185 | 0.2012 | -98.73 |
| full | chop_notrange | team1 | internal | 0.75 | 1,296 |  | 7.923 | -0.04089 | 0.295 | -98.83 |
| full | chop_notrange | team2 | internal | 0.5 | 1,296 |  | 7.923 | -0.04089 | 0.295 | -98.83 |
| full | chop_trend | team2 | internal | 1 | 1,296 |  | 7.796 | -0.06687 | 0.4478 | -98.95 |
| full | chop_trend | team1 | internal | 1.5 | 1,296 |  | 7.796 | -0.06687 | 0.4478 | -98.95 |
| full | chop_trend | team2 | firm | 0.75 | 1,296 |  | 6.502 | -0.05615 | 0.3758 | -100.2 |
| full | allon | team1 | firm | 0.5 | 1,296 |  | 6.176 | -0.03091 | 0.2216 | -100.6 |
| full | chop_ungated | team1 | firm | 0.5 | 1,296 |  | 5.941 | -0.01625 | 0.1497 | -100.8 |
| full | chop_notrange | team1 | firm | 0.5 | 1,296 |  | 5.874 | -0.03056 | 0.2203 | -100.9 |
| full | chop_trend | team2 | internal | 0.75 | 1,296 |  | 5.852 | -0.05054 | 0.3383 | -100.9 |
| full | chop_trend | team1 | firm | 1 | 1,296 |  | 5.781 | -0.05004 | 0.3349 | -101 |
| full | allon | team1 | internal | 0.5 | 1,296 |  | 5.559 | -0.02782 | 0.1994 | -101.2 |
| full | chop_ungated | team1 | internal | 0.5 | 1,296 |  | 5.347 | -0.01462 | 0.1347 | -101.4 |
| full | chop_notrange | team1 | internal | 0.5 | 1,296 |  | 5.287 | -0.02751 | 0.1983 | -101.5 |
| full | chop_trend | team1 | internal | 1 | 1,296 |  | 5.203 | -0.04504 | 0.3014 | -101.5 |
| full | allon | team2 | firm | 0.25 | 1,296 |  | 4.654 | -0.02326 | 0.1668 | -102.1 |
| full | chop_ungated | team2 | firm | 0.25 | 1,296 |  | 4.457 | -0.01221 | 0.1125 | -102.3 |
| full | chop_notrange | team2 | firm | 0.25 | 1,296 |  | 4.408 | -0.02303 | 0.1659 | -102.3 |
| full | chop_trend | team2 | firm | 0.5 | 1,296 |  | 4.338 | -0.03772 | 0.2524 | -102.4 |
| full | chop_trend | team1 | firm | 0.75 | 1,296 |  | 4.338 | -0.03772 | 0.2524 | -102.4 |
| full | allon | team2 | internal | 0.25 | 1,296 |  | 4.189 | -0.02094 | 0.1502 | -102.6 |
| full | chop_ungated | team2 | internal | 0.25 | 1,296 |  | 4.011 | -0.01099 | 0.1013 | -102.7 |
| full | chop_notrange | team2 | internal | 0.25 | 1,296 |  | 3.967 | -0.02072 | 0.1493 | -102.8 |
| full | chop_trend | team2 | internal | 0.5 | 1,296 |  | 3.904 | -0.03395 | 0.2272 | -102.8 |
| full | chop_trend | team1 | internal | 0.75 | 1,296 |  | 3.904 | -0.03395 | 0.2272 | -102.8 |
| full | allon | team1 | firm | 0.25 | 1,296 |  | 3.117 | -0.01556 | 0.1117 | -103.6 |
| full | chop_ungated | team1 | firm | 0.25 | 1,296 |  | 2.972 | -0.008153 | 0.07517 | -103.8 |
| full | chop_notrange | team1 | firm | 0.25 | 1,296 |  | 2.94 | -0.01542 | 0.1111 | -103.8 |
| full | chop_trend | team1 | firm | 0.5 | 1,296 |  | 2.893 | -0.02528 | 0.1691 | -103.9 |
| full | allon | team1 | internal | 0.25 | 1,296 |  | 2.805 | -0.01401 | 0.1005 | -103.9 |
| full | chop_ungated | team1 | internal | 0.25 | 1,296 |  | 2.675 | -0.007338 | 0.06766 | -104.1 |
| full | chop_notrange | team1 | internal | 0.25 | 1,296 |  | 2.646 | -0.01388 | 0.09996 | -104.1 |
| full | chop_trend | team1 | internal | 0.5 | 1,296 |  | 2.604 | -0.02275 | 0.1522 | -104.1 |
| full | chop_trend | team2 | firm | 0.25 | 1,296 |  | 2.171 | -0.01901 | 0.1271 | -104.6 |
| full | chop_trend | team2 | internal | 0.25 | 1,296 |  | 1.954 | -0.01711 | 0.1144 | -104.8 |
| full | chop_trend | team1 | firm | 0.25 | 1,296 |  | 1.447 | -0.0127 | 0.08494 | -105.3 |
| full | chop_trend | team1 | internal | 0.25 | 1,296 |  | 1.303 | -0.01143 | 0.07645 | -105.4 |


**49 of 200 funded runs breached.** Best payout is **$4628 a year** before the $549 fee.


## Provenance

| file | rows | md5 |
|---|---|---|
| `results/r2reads/modeA_a6_propsim_winners.csv` | 44 | 5a7a078530fc |
| `results/r2reads/modeA_a6_propsim_full.csv` | 176 | e9b05386919c |
