# B1-WINNERS — THE 10 WINNERS ON SIX YEARS THEY WERE NEVER SELECTED ON

Generated 2026-11-24 10:18 by `code/b1narrow.py --stage winners` with `FX_WALK=ext11`.

Eleven rolling steps: tune 2005-2008 / grade 2009 / trade 2010 through tune 2015-2018 / grade 2019 / trade 2020. **2021 onward stays sealed.** One-bar lag; costs from `cost_table_h22.csv`.


## What makes this a test

The winners were selected on the FIVE-step walk, whose earliest tuning year is 2011 and whose trade years are 2016-2020. **Trade years 2010, 2011, 2012, 2013, 2014 and 2015 were touched by no part of that selection** — not by tuning, not by grading, not by the luck floors. They are marked `never_seen = 1` below. 2016-2020 are the years the winners were chosen on and are shown only for contrast; they are not evidence.


**Both conditions pass on this walk**: condition 1 worst |per-year marks − trade R| = 8.88e-16 over 48 evaluations; condition 2 264 comparisons over 11 steps, zero tune-pick and zero record mismatches.


**Prop return here is the REAL figure.** The winner-only bank carries no drawdown, so this stage re-scores each winner's selected configuration with `want_dd=True` and takes the true chronological max DD from `role_dd` over the span being reported. It is therefore comparable with `MODEA_WINNERS.md`, unlike the spread proxy in `B1_NARROW.md`.


## Mode A

### R per trade year, 2010-2020

Total R in the year. `never_seen` years are **2010-2015**.

| sid | stream | R_2010 | R_2011 | R_2012 | R_2013 | R_2014 | R_2015 | R_2016 | R_2017 | R_2018 | R_2019 | R_2020 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| lemantrend_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | -86.3 | -20.32 | -13.54 | -4.813 | 31.36 | -75.17 | 16.68 | 6.629 | 120.8 | 85.14 | 12.14 |
| lemantrend_signals|hieken_ashi_smoothed_signals|volatility_ratio_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | -115.6 | 16.69 | -49.26 | 48.71 | 44.96 | -33.56 | 19.66 | 58.25 | 82.89 | 72.96 | 14.6 |
| waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | -81.99 | -43.96 | -25.75 | 34.63 | -2.522 | -7.787 | -20.45 | 12.56 | 133.5 | 70.96 | 7.693 |
| waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|volatility_ratio_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | -123.3 | -39.22 | -37.32 | 52.06 | 0.05824 | 30.81 | -3.113 | 17.44 | 78.32 | 77.98 | 16.71 |
| lemantrend_signals|relative_vigor_index_signals|volatility_ratio_volume_signals|super_smoother_2pole_baseline|adx_dmi_exit | trend-allon | -123.8 | 51.25 | -57.38 | -18.02 | 18.02 | 48.34 | 85.11 | -29.37 | 60.88 | 61.24 | 61.97 |
| lemantrend_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|fantail_vma|adx_dmi_exit | trend-allon | -12.43 | -6.932 | -24.87 | 65.05 | -30.61 | 22.78 | 14.45 | 39.84 | 78.71 | 56.39 | -1.848 |
| waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|super_smoother_2pole_baseline|adx_dmi_exit | trend-allon | -93.64 | -12.78 | 32.99 | -29.17 | -118.4 | -28.58 | -2.648 | 17.1 | 68.95 | 55.71 | 24.36 |
| lemantrend_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|frama_baseline|adx_dmi_exit | trend-allon | -32.57 | -40.83 | -62.91 | 65.33 | -1.276 | -29.13 | 29.86 | -6.519 | 151.2 | 75.74 | 41.92 |


### R per trade, same years

| sid | Rpt_2010 | Rpt_2011 | Rpt_2012 | Rpt_2013 | Rpt_2014 | Rpt_2015 | Rpt_2016 | Rpt_2017 | Rpt_2018 | Rpt_2019 | Rpt_2020 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| lemantrend_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | -0.08933 | -0.02139 | -0.02746 | -0.007057 | 0.03934 | -0.1563 | 0.03033 | 0.01451 | 0.364 | 0.2711 | 0.0521 |
| lemantrend_signals|hieken_ashi_smoothed_signals|volatility_ratio_volume_signals|alma_baseline|adx_dmi_exit | -0.1089 | 0.01914 | -0.119 | 0.08825 | 0.07543 | -0.05285 | 0.03355 | 0.06649 | 0.2193 | 0.1379 | 0.03387 |
| waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | -0.08931 | -0.05296 | -0.05287 | 0.05992 | -0.003991 | -0.02512 | -0.05271 | 0.03461 | 0.375 | 0.1993 | 0.0286 |
| waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|volatility_ratio_volume_signals|alma_baseline|adx_dmi_exit | -0.1143 | -0.0423 | -0.09952 | 0.1186 | 0.0001309 | 0.06939 | -0.006302 | 0.0236 | 0.2146 | 0.13 | 0.03868 |
| lemantrend_signals|relative_vigor_index_signals|volatility_ratio_volume_signals|super_smoother_2pole_baseline|adx_dmi_exit | -0.1117 | 0.05939 | -0.1502 | -0.02768 | 0.02076 | 0.06649 | 0.1107 | -0.1064 | 0.1381 | 0.1105 | 0.1386 |
| lemantrend_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|fantail_vma|adx_dmi_exit | -0.04913 | -0.0212 | -0.0625 | 0.1328 | -0.07972 | 0.04574 | 0.02811 | 0.1379 | 0.2905 | 0.1855 | -0.00672 |
| waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|super_smoother_2pole_baseline|adx_dmi_exit | -0.1019 | -0.01516 | 0.1875 | -0.03828 | -0.2407 | -0.05648 | -0.005633 | 0.04266 | 0.2268 | 0.1565 | 0.04912 |
| lemantrend_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|frama_baseline|adx_dmi_exit | -0.04487 | -0.1464 | -0.1597 | 0.1261 | -0.002435 | -0.04691 | 0.04832 | -0.02469 | 0.3846 | 0.1654 | 0.08899 |


### The six never-seen years, summarised

| sid | stream | R_new6 | n_new6 | dd_new6 | t_new6 | years_pos_new6 | prop_return_new6 |
|---|---|---|---|---|---|---|---|
| lemantrend_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | -168.8 | 4369 | 88.28 | -1.553 | 1 | -1.147 |
| lemantrend_signals|hieken_ashi_smoothed_signals|volatility_ratio_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | -88.11 | 4131 | 95.8 | -0.4412 | 3 | -0.5519 |
| waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | -127.4 | 3755 | 91.44 | -1.3 | 1 | -0.8357 |
| waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|volatility_ratio_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | -116.9 | 3708 | 89.26 | -0.3 | 3 | -0.7855 |
| lemantrend_signals|relative_vigor_index_signals|volatility_ratio_volume_signals|super_smoother_2pole_baseline|adx_dmi_exit | trend-allon | -81.63 | 4600 | 99.13 | -0.6461 | 3 | -0.494 |
| lemantrend_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|fantail_vma|adx_dmi_exit | trend-allon | 12.98 | 2350 | 39.27 | -0.172 | 2 | 0.1984 |
| waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|super_smoother_2pole_baseline|adx_dmi_exit | trend-allon | -249.6 | 3698 | 131.7 | -0.7784 | 1 | -1.138 |
| lemantrend_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|frama_baseline|adx_dmi_exit | trend-allon | -101.4 | 3062 | 80.72 | -1.072 | 1 | -0.7537 |


### All eleven years

| sid | R_all11 | n_all11 | dd_all11 | years_pos_all11 | prop_return_all11 |
|---|---|---|---|---|---|
| lemantrend_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | 72.64 | 6255 | 104 | 6 | 0.2286 |
| lemantrend_signals|hieken_ashi_smoothed_signals|volatility_ratio_volume_signals|alma_baseline|adx_dmi_exit | 160.2 | 6931 | 115.7 | 8 | 0.4533 |
| waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | 76.9 | 5487 | 94.42 | 5 | 0.2666 |
| waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|volatility_ratio_volume_signals|alma_baseline|adx_dmi_exit | 70.48 | 6338 | 89.26 | 7 | 0.2584 |
| lemantrend_signals|relative_vigor_index_signals|volatility_ratio_volume_signals|super_smoother_2pole_baseline|adx_dmi_exit | 158.2 | 7087 | 99.13 | 7 | 0.5223 |
| lemantrend_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|fantail_vma|adx_dmi_exit | 200.5 | 4003 | 55.68 | 6 | 1.179 |
| waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|super_smoother_2pole_baseline|adx_dmi_exit | -86.13 | 5725 | 151 | 5 | -0.1866 |
| lemantrend_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|frama_baseline|adx_dmi_exit | 190.8 | 5266 | 80.72 | 5 | 0.7734 |


**1 of 8 winners are positive over the six never-seen years.** **0 clear the 12%/yr prop target on those six years; 0 clear it on all eleven.** Median years-positive out of six: 1.5.


Top by prop return on the never-seen years:

| sid | stream | prop_return_new6 | R_new6 | dd_new6 | t_new6 |
|---|---|---|---|---|---|
| lemantrend_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|fantail_vma|adx_dmi_exit | trend-allon | 0.1984 | 12.98 | 39.27 | -0.172 |
| lemantrend_signals|relative_vigor_index_signals|volatility_ratio_volume_signals|super_smoother_2pole_baseline|adx_dmi_exit | trend-allon | -0.494 | -81.63 | 99.13 | -0.6461 |
| lemantrend_signals|hieken_ashi_smoothed_signals|volatility_ratio_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | -0.5519 | -88.11 | 95.8 | -0.4412 |
| lemantrend_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|frama_baseline|adx_dmi_exit | trend-allon | -0.7537 | -101.4 | 80.72 | -1.072 |
| waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|volatility_ratio_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | -0.7855 | -116.9 | 89.26 | -0.3 |
| waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | -0.8357 | -127.4 | 91.44 | -1.3 |
| waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|super_smoother_2pole_baseline|adx_dmi_exit | trend-allon | -1.138 | -249.6 | 131.7 | -0.7784 |
| lemantrend_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | -1.147 | -168.8 | 88.28 | -1.553 |


## Mode B

### R per trade year, 2010-2020

Total R in the year. `never_seen` years are **2010-2015**.

| sid | stream | R_2010 | R_2011 | R_2012 | R_2013 | R_2014 | R_2015 | R_2016 | R_2017 | R_2018 | R_2019 | R_2020 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|fantail_vma|adx_dmi_exit | trend-allon | -17.92 | -28.3 | 7.647 | 6.684 | 16.98 | -3.177 | -5.294 | 15.41 | 57.46 | 45.76 | 13.7 |
| lemantrend_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | 23.45 | -42.67 | -28.98 | 56.39 | -13.98 | 7.112 | 2.918 | 33.44 | 111.9 | 45.97 | 15.29 |


### R per trade, same years

| sid | Rpt_2010 | Rpt_2011 | Rpt_2012 | Rpt_2013 | Rpt_2014 | Rpt_2015 | Rpt_2016 | Rpt_2017 | Rpt_2018 | Rpt_2019 | Rpt_2020 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|fantail_vma|adx_dmi_exit | -0.03838 | -0.09726 | 0.04134 | 0.02832 | 0.06361 | -0.02626 | -0.02036 | 0.06729 | 0.1785 | 0.152 | 0.06315 |
| lemantrend_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | 0.08498 | -0.2072 | -0.1146 | 0.09477 | -0.01944 | 0.02586 | 0.006017 | 0.08823 | 0.3067 | 0.1372 | 0.0665 |


### The six never-seen years, summarised

| sid | stream | R_new6 | n_new6 | dd_new6 | t_new6 | years_pos_new6 | prop_return_new6 |
|---|---|---|---|---|---|---|---|
| waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|fantail_vma|adx_dmi_exit | trend-allon | -18.09 | 1567 | 36.08 | -0.1946 | 3 | -0.3008 |
| lemantrend_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | 1.318 | 2324 | 36.64 | -0.4669 | 3 | 0.02158 |


### All eleven years

| sid | R_all11 | n_all11 | dd_all11 | years_pos_all11 | prop_return_all11 |
|---|---|---|---|---|---|
| waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|fantail_vma|adx_dmi_exit | 109 | 2896 | 36.08 | 7 | 0.9883 |
| lemantrend_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | 210.9 | 4118 | 36.64 | 8 | 1.884 |


**1 of 2 winners are positive over the six never-seen years.** **0 clear the 12%/yr prop target on those six years; 0 clear it on all eleven.** Median years-positive out of six: 3.0.


Top by prop return on the never-seen years:

| sid | stream | prop_return_new6 | R_new6 | dd_new6 | t_new6 |
|---|---|---|---|---|---|
| lemantrend_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | 0.02158 | 1.318 | 36.64 | -0.4669 |
| waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|fantail_vma|adx_dmi_exit | trend-allon | -0.3008 | -18.09 | 36.08 | -0.1946 |


## How to read a failure here

These winners cleared two luck floors on 2016-2020. If they are flat or negative on 2010-2015 the floors did their job on the years they were given and the selection still does not generalise — which is a finding about the METHOD, not about these ten strategies. If they hold up, the six years are the first genuinely out-of-sample evidence the project has for them.


## Still pending

- The family sample and the control run as a **second stage** and are reported in `B1_NARROW.md`. Without them, a winner holding up here cannot yet be separated from the family holding up.

- The random-entry null on these six years needs an engine pass and is not in this read.


## Provenance

- `results/r2reads/modeA_b1winners.csv` — 8 rows, md5 `e1f5681887cf`
- `results/r2reads/modeB_b1winners.csv` — 2 rows, md5 `9ef287546af7`
