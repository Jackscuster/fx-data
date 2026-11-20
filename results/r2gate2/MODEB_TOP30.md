# MODE B — TOP 30, PERSISTENCE AND WHAT WAS KNOWN IN ADVANCE

Generated 2026-11-19 21:57 by `code/l2r2top30.py`, read-only off the mode B gate 2 bank. **No tuning and no engine pass.** Every number below is read back out of the CSV named beside it. **Everything here is reported; nothing is selected for a book** -- HANDOFF 0l's rule stands that everyone who enters tuning trades, at equal weight, with no picking and no weighting by past record.


## Sources

| section | file | rows | md5 |
|---|---|---|---|
| top30 | results/r2gate2/modeB_top30_top30.csv | 40 | 03ae79ac7124 |
| fieldshare | results/r2gate2/modeB_top30_fieldshare.csv | 20 | e7a05d4ca040 |
| persistence | results/r2gate2/modeB_top30_persistence.csv | 12 | 8f94530e4c35 |
| all5 | results/r2gate2/modeB_top30_all5.csv | 6,712 | 2bc1ae2f6028 |
| all5_rank | results/r2gate2/modeB_top30_all5_rank.csv | 33,560 | 6b4a8f16c7fe |


## 3. The share of the field positive on the trade year

| stream | step | n_with_trades | share_positive_pct | field_mean_trade_R | field_median_trade_R |
|---|---|---|---|---|---|
| chop-allon | 2011-2014 | 272,330 | 38.8 | -0.03722 | -0.03984 |
| chop-allon | 2012-2015 | 272,432 | 36.14 | -0.03868 | -0.04713 |
| chop-allon | 2013-2016 | 272,585 | 53.75 | 0.01716 | 0.01202 |
| chop-allon | 2014-2017 | 272,328 | 22.11 | -0.09025 | -0.08958 |
| chop-allon | 2015-2018 | 272,229 | 25.77 | -0.08287 | -0.07783 |
| chop-routed | 2011-2014 | 253,874 | 32.91 | -0.06259 | -0.06915 |
| chop-routed | 2012-2015 | 250,812 | 33.91 | -0.04739 | -0.05791 |
| chop-routed | 2013-2016 | 254,735 | 52.15 | 0.008745 | 0.007436 |
| chop-routed | 2014-2017 | 254,603 | 25.09 | -0.07649 | -0.0748 |
| chop-routed | 2015-2018 | 255,076 | 35.36 | -0.04487 | -0.05382 |
| trend-allon | 2011-2014 | 273,637 | 33.3 | -0.03206 | -0.03452 |
| trend-allon | 2012-2015 | 273,417 | 31.38 | -0.02982 | -0.03458 |
| trend-allon | 2013-2016 | 273,624 | 46.33 | -0.004748 | -0.006295 |
| trend-allon | 2014-2017 | 273,626 | 19.21 | -0.05903 | -0.06074 |
| trend-allon | 2015-2018 | 273,613 | 26.9 | -0.04435 | -0.04026 |
| trend-routed | 2011-2014 | 269,045 | 33.82 | -0.04182 | -0.04282 |
| trend-routed | 2012-2015 | 270,102 | 29.67 | -0.04704 | -0.04991 |
| trend-routed | 2013-2016 | 269,955 | 40.99 | -0.01204 | -0.03151 |
| trend-routed | 2014-2017 | 268,317 | 20.23 | -0.09149 | -0.09248 |
| trend-routed | 2015-2018 | 265,139 | 29.94 | -0.04568 | -0.04886 |


Mean over the five steps:

| stream | share_positive_pct | field_mean_trade_R |
|---|---|---|
| chop-allon | 35.32 | -0.04637 |
| chop-routed | 35.89 | -0.04452 |
| trend-allon | 31.42 | -0.034 |
| trend-routed | 30.93 | -0.04761 |


## 1. Top 30 by what the tuner saw, and by the blind grade

Per step and stream, then pooled. `top_minus_field` is the top 30's mean trade-year R per trade minus the whole eligible field's.

| basis | stream | top_mean_trade_R | field_mean_trade_R | top_minus_field | n_top_positive | top_mean_trade_PF | top_mean_trade_count |
|---|---|---|---|---|---|---|---|
| blind grade (year 5) | chop-allon | -0.0441 | -0.04637 | 0.002273 | 11.2 | 0.989 | 20.35 |
| blind grade (year 5) | chop-routed | 0.07964 | -0.04452 | 0.1242 | 15 | 2.345 | 26.25 |
| blind grade (year 5) | trend-allon | -0.07938 | -0.034 | -0.04538 | 9 | 0.8198 | 24.38 |
| blind grade (year 5) | trend-routed | -0.07298 | -0.04761 | -0.02537 | 10.6 | 2.495 | 17.32 |
| tune-year objective | chop-allon | 0.007271 | -0.04637 | 0.05364 | 16.2 | 1.112 | 26.97 |
| tune-year objective | chop-routed | 0.02466 | -0.04452 | 0.06918 | 15.2 | 1.121 | 34.55 |
| tune-year objective | trend-allon | -0.05335 | -0.034 | -0.01935 | 10.8 | 0.971 | 28.08 |
| tune-year objective | trend-routed | 0.05308 | -0.04761 | 0.1007 | 16.8 | 3.367 | 28.13 |


Every step, by basis and stream:

| basis | stream | step | n_top_with_trade_year_trades | top_mean_trade_R | top_median_trade_R | n_top_positive | field_mean_trade_R | top_minus_field |
|---|---|---|---|---|---|---|---|---|
| blind grade (year 5) | chop-allon | 2011-2014 | 30 | 0.01198 | -0.0007419 | 14 | -0.03722 | 0.0492 |
| blind grade (year 5) | chop-allon | 2012-2015 | 30 | 0.01771 | -0.01539 | 14 | -0.03868 | 0.05639 |
| blind grade (year 5) | chop-allon | 2013-2016 | 29 | 0.1534 | 0.0529 | 17 | 0.01716 | 0.1363 |
| blind grade (year 5) | chop-allon | 2014-2017 | 30 | -0.317 | -0.3331 | 0 | -0.09025 | -0.2268 |
| blind grade (year 5) | chop-allon | 2015-2018 | 30 | -0.0866 | -0.05215 | 11 | -0.08287 | -0.003734 |
| blind grade (year 5) | chop-routed | 2011-2014 | 30 | 0.002985 | -0.02764 | 13 | -0.06259 | 0.06558 |
| blind grade (year 5) | chop-routed | 2012-2015 | 30 | 0.06697 | 0.1003 | 19 | -0.04739 | 0.1144 |
| blind grade (year 5) | chop-routed | 2013-2016 | 30 | 0.4728 | 0.5752 | 24 | 0.008745 | 0.464 |
| blind grade (year 5) | chop-routed | 2014-2017 | 30 | -0.1761 | -0.1569 | 2 | -0.07649 | -0.09963 |
| blind grade (year 5) | chop-routed | 2015-2018 | 30 | 0.03158 | 0.02653 | 17 | -0.04487 | 0.07646 |
| blind grade (year 5) | trend-allon | 2011-2014 | 30 | -0.07957 | -0.1073 | 7 | -0.03206 | -0.04752 |
| blind grade (year 5) | trend-allon | 2012-2015 | 30 | -0.007651 | 0.01223 | 17 | -0.02982 | 0.02216 |
| blind grade (year 5) | trend-allon | 2013-2016 | 28 | -0.08502 | -0.1447 | 10 | -0.004748 | -0.08027 |
| blind grade (year 5) | trend-allon | 2014-2017 | 30 | -0.1106 | -0.0863 | 8 | -0.05903 | -0.05157 |
| blind grade (year 5) | trend-allon | 2015-2018 | 30 | -0.114 | -0.124 | 3 | -0.04435 | -0.06969 |
| blind grade (year 5) | trend-routed | 2011-2014 | 30 | -0.1024 | -0.1609 | 5 | -0.04182 | -0.06059 |
| blind grade (year 5) | trend-routed | 2012-2015 | 30 | -0.1166 | -0.1155 | 7 | -0.04704 | -0.06961 |
| blind grade (year 5) | trend-routed | 2013-2016 | 29 | -0.2151 | -0.2111 | 6 | -0.01204 | -0.203 |
| blind grade (year 5) | trend-routed | 2014-2017 | 29 | 0.0816 | 0.06468 | 21 | -0.09149 | 0.1731 |
| blind grade (year 5) | trend-routed | 2015-2018 | 30 | -0.0124 | -0.0257 | 14 | -0.04568 | 0.03328 |
| tune-year objective | chop-allon | 2011-2014 | 30 | -0.02138 | -0.0148 | 14 | -0.03722 | 0.01583 |
| tune-year objective | chop-allon | 2012-2015 | 30 | -0.04851 | -0.02668 | 14 | -0.03868 | -0.009828 |
| tune-year objective | chop-allon | 2013-2016 | 30 | 0.1361 | 0.1062 | 20 | 0.01716 | 0.119 |
| tune-year objective | chop-allon | 2014-2017 | 30 | -0.01112 | 0.04517 | 17 | -0.09025 | 0.07913 |
| tune-year objective | chop-allon | 2015-2018 | 30 | -0.01874 | 0.0176 | 16 | -0.08287 | 0.06412 |
| tune-year objective | chop-routed | 2011-2014 | 30 | 0.1513 | 0.1701 | 23 | -0.06259 | 0.2139 |
| tune-year objective | chop-routed | 2012-2015 | 30 | 0.1043 | 0.1084 | 19 | -0.04739 | 0.1517 |
| tune-year objective | chop-routed | 2013-2016 | 30 | -0.03695 | -0.06695 | 12 | 0.008745 | -0.04569 |
| tune-year objective | chop-routed | 2014-2017 | 30 | -0.02051 | -0.06339 | 12 | -0.07649 | 0.05599 |
| tune-year objective | chop-routed | 2015-2018 | 30 | -0.07485 | -0.1027 | 10 | -0.04487 | -0.02997 |
| tune-year objective | trend-allon | 2011-2014 | 30 | -0.07541 | -0.07683 | 12 | -0.03206 | -0.04335 |
| tune-year objective | trend-allon | 2012-2015 | 30 | -0.03935 | -0.07151 | 10 | -0.02982 | -0.009535 |
| tune-year objective | trend-allon | 2013-2016 | 30 | 0.004693 | -0.02125 | 14 | -0.004748 | 0.009441 |
| tune-year objective | trend-allon | 2014-2017 | 30 | -0.08203 | -0.1287 | 11 | -0.05903 | -0.023 |
| tune-year objective | trend-allon | 2015-2018 | 30 | -0.07467 | -0.05994 | 7 | -0.04435 | -0.03031 |
| tune-year objective | trend-routed | 2011-2014 | 30 | -0.009142 | 0.006061 | 16 | -0.04182 | 0.03268 |
| tune-year objective | trend-routed | 2012-2015 | 30 | 0.02725 | 0.04656 | 16 | -0.04704 | 0.07428 |
| tune-year objective | trend-routed | 2013-2016 | 30 | 0.1468 | 0.1042 | 19 | -0.01204 | 0.1589 |
| tune-year objective | trend-routed | 2014-2017 | 30 | 0.03843 | -0.01297 | 14 | -0.09149 | 0.1299 |
| tune-year objective | trend-routed | 2015-2018 | 30 | 0.06202 | 0.0423 | 19 | -0.04568 | 0.1077 |


## 2. Persistence across the five steps, against a coin flip

`base_rate_pct` is that stream's own share of positive trade years, averaged over the five steps; `coin_flip_expected` is the binomial count at that rate.

| stream | k_of_5 | n_eligible | observed | base_rate_pct | coin_flip_expected | ratio_obs_over_expected |
|---|---|---|---|---|---|---|
| trend-routed | 5 | 264,338 | 1,404 | 30.93 | 748.2 | 1.876 |
| trend-routed | 4 | 264,338 | 12,716 | 30.93 | 9103 | 1.397 |
| trend-routed | 3 | 264,338 | 51,722 | 30.93 | 4.642e+04 | 1.114 |
| trend-allon | 5 | 273,263 | 1,462 | 31.42 | 837.1 | 1.746 |
| trend-allon | 4 | 273,263 | 13,618 | 31.42 | 9972 | 1.366 |
| trend-allon | 3 | 273,263 | 54,711 | 31.42 | 4.984e+04 | 1.098 |
| chop-routed | 5 | 250,670 | 1,433 | 35.89 | 1492 | 0.9607 |
| chop-routed | 4 | 250,670 | 14,282 | 35.89 | 1.482e+04 | 0.9639 |
| chop-routed | 3 | 250,670 | 59,867 | 35.89 | 6.243e+04 | 0.9589 |
| chop-allon | 5 | 271,915 | 2,413 | 35.32 | 1494 | 1.616 |
| chop-allon | 4 | 271,915 | 18,990 | 35.32 | 1.517e+04 | 1.252 |
| chop-allon | 3 | 271,915 | 69,045 | 35.32 | 6.528e+04 | 1.058 |


### The strategies positive on the trade year in all five steps

6,712 in total, listed in full in `results/r2gate2/modeB_top30_all5.csv` with their settings and per-year R. Count by stream:

| stream | n_all_five |
|---|---|
| chop-allon | 2,413 |
| chop-routed | 1,433 |
| trend-allon | 1,462 |
| trend-routed | 1,404 |


The first 15 of them, with per-year R:

| stream | sid | trade_R_2016 | trade_R_2017 | trade_R_2018 | trade_R_2019 | trade_R_2020 |
|---|---|---|---|---|---|---|
| trend-routed | adx_dmi_signals|aroon_signals|variance_volume_signals|tma_baseline|adx_dmi_exit | 0.01405 | 0.247 | 0.2756 | 0.3187 | 0.08452 |
| trend-routed | adx_dmi_signals|center_of_gravity_signals|chaikin_volatility_volume_signals|frama_baseline|adx_dmi_exit | 0.1701 | 0.01873 | 0.005893 | 0.02439 | 0.002171 |
| trend-routed | adx_dmi_signals|center_of_gravity_signals|chaikin_volatility_volume_signals|tma_baseline|adx_dmi_exit | 0.0417 | 0.04476 | 0.05998 | 0.05003 | 0.02689 |
| trend-routed | adx_dmi_signals|ehlers_reverse_ema_signals|variance_volume_signals|ema_baseline|adx_dmi_exit | 0.07751 | 0.0813 | 0.03619 | 0.02437 | 0.06406 |
| trend-routed | adx_dmi_signals|fisher_transform_signals|chaikin_volatility_volume_signals|sma_baseline|adx_dmi_exit | 0.1583 | 0.05412 | 0.1074 | 0.06591 | 0.02028 |
| trend-routed | adx_dmi_signals|fisher_transform_signals|williams_vix_fix_volume_signals|hma_baseline|adx_dmi_exit | 0.08904 | 0.0828 | 0.5511 | 0.5016 | 0.1667 |
| trend-routed | adx_dmi_signals|fx_sniper_ergodic_cci_signals|chaikin_volatility_volume_signals|ema_baseline|adx_dmi_exit | 0.01504 | 0.06827 | 0.0916 | 0.09164 | 0.006305 |
| trend-routed | adx_dmi_signals|kalman_filter_signals|variance_volume_signals|sma_baseline|adx_dmi_exit | 0.08251 | 0.1417 | 0.1029 | 0.112 | 0.03903 |
| trend-routed | adx_dmi_signals|kuskus_starlight_signals|chaikin_volatility_volume_signals|ema_baseline|adx_dmi_exit | 0.0346 | 0.08809 | 0.1299 | 0.04998 | 0.03981 |
| trend-routed | adx_dmi_signals|lemantrend_signals|variance_volume_signals|hma_baseline|adx_dmi_exit | 0.03434 | 0.00404 | 0.07249 | 0.06576 | 0.1108 |
| trend-routed | adx_dmi_signals|lemantrend_signals|variance_volume_signals|super_smoother_2pole_baseline|adx_dmi_exit | 0.07059 | 0.06531 | 0.0986 | 0.09087 | 0.07287 |
| trend-routed | adx_dmi_signals|lemantrend_signals|volatility_ratio_volume_signals|fantail_vma|adx_dmi_exit | 0.1833 | 0.009362 | 0.1392 | 0.03043 | 0.0526 |
| trend-routed | adx_dmi_signals|lemantrend_signals|volatility_ratio_volume_signals|frama_baseline|adx_dmi_exit | 0.1596 | 0.1106 | 0.03816 | 0.1291 | 0.01111 |
| trend-routed | adx_dmi_signals|lemantrend_signals|volatility_ratio_volume_signals|super_smoother_2pole_baseline|adx_dmi_exit | 0.1034 | 0.05136 | 0.08743 | 0.005174 | 0.03131 |
| trend-routed | adx_dmi_signals|parabolic_sar_signals|chaikin_volatility_volume_signals|tma_baseline|adx_dmi_exit | 0.1802 | 0.06908 | 0.09734 | 0.1214 | 0.03617 |


## 4. Was anything known in advance about the all-five names?

Each all-five name's tune-year rank percentile in its own stream and step. If the tuner could see them coming, they would sit in the top bands.

| stream | band | n | total | pct_of_name_steps |
|---|---|---|---|---|
| chop-allon | bottom 50% | 2,692 | 12,065 | 22.31 |
| chop-allon | top 1% | 591 | 12,065 | 4.898 |
| chop-allon | top 10% | 3,129 | 12,065 | 25.93 |
| chop-allon | top 50% | 5,653 | 12,065 | 46.85 |
| chop-routed | bottom 50% | 1,515 | 7,165 | 21.14 |
| chop-routed | top 1% | 224 | 7,165 | 3.126 |
| chop-routed | top 10% | 1,589 | 7,165 | 22.18 |
| chop-routed | top 50% | 3,837 | 7,165 | 53.55 |
| trend-allon | bottom 50% | 1,647 | 7,310 | 22.53 |
| trend-allon | top 1% | 75 | 7,310 | 1.026 |
| trend-allon | top 10% | 1,360 | 7,310 | 18.6 |
| trend-allon | top 50% | 4,228 | 7,310 | 57.84 |
| trend-routed | bottom 50% | 2,732 | 7,020 | 38.92 |
| trend-routed | top 1% | 189 | 7,020 | 2.692 |
| trend-routed | top 10% | 932 | 7,020 | 13.28 |
| trend-routed | top 50% | 3,167 | 7,020 | 45.11 |


Pooled over streams:

| band | n | pct |
|---|---|---|
| top 50% | 16,885 | 50.31 |
| bottom 50% | 8,586 | 25.58 |
| top 10% | 7,010 | 20.89 |
| top 1% | 1,079 | 3.215 |


A uniform draw would put 1%% of name-steps in "top 1%%", 10%% in "top 10%%" and 50%% in "top 50%%". Compare those against the table above.
