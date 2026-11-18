# MODE A — TOP 30, PERSISTENCE AND WHAT WAS KNOWN IN ADVANCE

Generated 2026-11-18 13:34 by `code/l2r2top30.py`, read-only off the mode A gate 2 bank. **No tuning and no engine pass.** Every number below is read back out of the CSV named beside it. **Everything here is reported; nothing is selected for a book** — HANDOFF 0l's rule stands that everyone who enters tuning trades, at equal weight, with no picking and no weighting by past record.


## Sources

| section | file | rows | md5 |
|---|---|---|---|
| top30 | results/r2gate2/modeA_top30_top30.csv | 40 | 5d43159ec227 |
| fieldshare | results/r2gate2/modeA_top30_fieldshare.csv | 20 | 27d13a3667cb |
| persistence | results/r2gate2/modeA_top30_persistence.csv | 12 | bb52042b14c7 |
| all5 | results/r2gate2/modeA_top30_all5.csv | 7,566 | fbea0851c6d6 |
| all5_rank | results/r2gate2/modeA_top30_all5_rank.csv | 37,830 | 1176c03af757 |


## 3. The share of the field positive on the trade year

| stream | step | n_with_trades | share_positive_pct | field_mean_trade_R | field_median_trade_R |
|---|---|---|---|---|---|
| chop-allon | 2011-2014 | 272,293 | 39.31 | -0.03821 | -0.03998 |
| chop-allon | 2012-2015 | 272,402 | 37.62 | -0.03937 | -0.04542 |
| chop-allon | 2013-2016 | 272,564 | 54.28 | 0.0155 | 0.01488 |
| chop-allon | 2014-2017 | 272,304 | 23.98 | -0.09118 | -0.09318 |
| chop-allon | 2015-2018 | 272,179 | 30.22 | -0.07734 | -0.06872 |
| chop-routed | 2011-2014 | 253,091 | 35.49 | -0.05988 | -0.06186 |
| chop-routed | 2012-2015 | 250,041 | 35.03 | -0.04633 | -0.05265 |
| chop-routed | 2013-2016 | 253,864 | 60.2 | 0.03998 | 0.03998 |
| chop-routed | 2014-2017 | 253,684 | 22.41 | -0.1 | -0.09854 |
| chop-routed | 2015-2018 | 254,091 | 42.46 | -0.02564 | -0.03229 |
| trend-allon | 2011-2014 | 273,628 | 35.9 | -0.02902 | -0.03208 |
| trend-allon | 2012-2015 | 273,443 | 30.52 | -0.03857 | -0.04277 |
| trend-allon | 2013-2016 | 273,636 | 47.11 | -0.007068 | -0.005898 |
| trend-allon | 2014-2017 | 273,626 | 20.92 | -0.06072 | -0.06629 |
| trend-allon | 2015-2018 | 273,597 | 29.49 | -0.04489 | -0.03883 |
| trend-routed | 2011-2014 | 268,734 | 39.84 | -0.0316 | -0.03096 |
| trend-routed | 2012-2015 | 269,917 | 31.62 | -0.05051 | -0.05123 |
| trend-routed | 2013-2016 | 269,762 | 43.08 | -0.01187 | -0.02806 |
| trend-routed | 2014-2017 | 267,836 | 23.19 | -0.09607 | -0.1046 |
| trend-routed | 2015-2018 | 264,434 | 31.83 | -0.05539 | -0.05379 |


Mean over the five steps:

| stream | share_positive_pct | field_mean_trade_R |
|---|---|---|
| chop-allon | 37.08 | -0.04612 |
| chop-routed | 39.12 | -0.03837 |
| trend-allon | 32.79 | -0.03605 |
| trend-routed | 33.91 | -0.04909 |


## 1. Top 30 by what the tuner saw, and by the blind grade

Per step and stream, then pooled. `top_minus_field` is the top 30's mean trade-year R per trade minus the whole eligible field's.

| basis | stream | top_mean_trade_R | field_mean_trade_R | top_minus_field | n_top_positive | top_mean_trade_PF | top_mean_trade_count |
|---|---|---|---|---|---|---|---|
| blind grade (year 5) | chop-allon | -0.108 | -0.04612 | -0.06183 | 12.8 | 0.951 | 21.63 |
| blind grade (year 5) | chop-routed | -0.07272 | -0.03837 | -0.03435 | 11.8 | 1.015 | 28.63 |
| blind grade (year 5) | trend-allon | -0.02365 | -0.03605 | 0.01241 | 10.6 | 0.9538 | 23.03 |
| blind grade (year 5) | trend-routed | -0.1106 | -0.04909 | -0.06154 | 9 | 0.8141 | 21.5 |
| tune-year objective | chop-allon | 0.05597 | -0.04612 | 0.1021 | 17 | 1.153 | 30.09 |
| tune-year objective | chop-routed | -0.02455 | -0.03837 | 0.01382 | 12.8 | 0.9944 | 35.91 |
| tune-year objective | trend-allon | -0.04329 | -0.03605 | -0.007233 | 11.2 | 1.02 | 28.07 |
| tune-year objective | trend-routed | 0.04926 | -0.04909 | 0.09835 | 17 | 1.371 | 29.99 |


Every step, by basis and stream:

| basis | stream | step | n_top_with_trade_year_trades | top_mean_trade_R | top_median_trade_R | n_top_positive | field_mean_trade_R | top_minus_field |
|---|---|---|---|---|---|---|---|---|
| blind grade (year 5) | chop-allon | 2011-2014 | 30 | 0.03335 | 0.05696 | 19 | -0.03821 | 0.07156 |
| blind grade (year 5) | chop-allon | 2012-2015 | 30 | -0.06504 | -0.00102 | 14 | -0.03937 | -0.02567 |
| blind grade (year 5) | chop-allon | 2013-2016 | 30 | -0.1237 | -0.06256 | 13 | 0.0155 | -0.1392 |
| blind grade (year 5) | chop-allon | 2014-2017 | 30 | -0.3961 | -0.4348 | 0 | -0.09118 | -0.3049 |
| blind grade (year 5) | chop-allon | 2015-2018 | 30 | 0.01175 | 0.04473 | 18 | -0.07734 | 0.08909 |
| blind grade (year 5) | chop-routed | 2011-2014 | 30 | -0.2294 | -0.3585 | 7 | -0.05988 | -0.1696 |
| blind grade (year 5) | chop-routed | 2012-2015 | 30 | 0.02963 | 0.006687 | 15 | -0.04633 | 0.07596 |
| blind grade (year 5) | chop-routed | 2013-2016 | 30 | 0.1281 | 0.1711 | 20 | 0.03998 | 0.0881 |
| blind grade (year 5) | chop-routed | 2014-2017 | 30 | -0.2373 | -0.1947 | 4 | -0.1 | -0.1373 |
| blind grade (year 5) | chop-routed | 2015-2018 | 30 | -0.05457 | -0.02516 | 13 | -0.02564 | -0.02894 |
| blind grade (year 5) | trend-allon | 2011-2014 | 30 | -0.1115 | -0.1171 | 6 | -0.02902 | -0.08243 |
| blind grade (year 5) | trend-allon | 2012-2015 | 30 | -0.0643 | -0.09992 | 10 | -0.03857 | -0.02573 |
| blind grade (year 5) | trend-allon | 2013-2016 | 27 | 0.1344 | 0.1072 | 17 | -0.007068 | 0.1415 |
| blind grade (year 5) | trend-allon | 2014-2017 | 30 | -0.01925 | -0.008462 | 14 | -0.06072 | 0.04148 |
| blind grade (year 5) | trend-allon | 2015-2018 | 30 | -0.05765 | -0.04976 | 6 | -0.04489 | -0.01275 |
| blind grade (year 5) | trend-routed | 2011-2014 | 30 | -0.09544 | -0.09826 | 8 | -0.0316 | -0.06384 |
| blind grade (year 5) | trend-routed | 2012-2015 | 30 | -0.1177 | -0.08319 | 7 | -0.05051 | -0.06722 |
| blind grade (year 5) | trend-routed | 2013-2016 | 28 | -0.2337 | -0.2823 | 6 | -0.01187 | -0.2218 |
| blind grade (year 5) | trend-routed | 2014-2017 | 30 | -0.1109 | -0.1756 | 8 | -0.09607 | -0.01486 |
| blind grade (year 5) | trend-routed | 2015-2018 | 30 | 0.004665 | 0.03074 | 16 | -0.05539 | 0.06006 |
| tune-year objective | chop-allon | 2011-2014 | 30 | -0.06049 | -0.05033 | 11 | -0.03821 | -0.02228 |
| tune-year objective | chop-allon | 2012-2015 | 30 | 0.08862 | 0.09191 | 19 | -0.03937 | 0.128 |
| tune-year objective | chop-allon | 2013-2016 | 30 | 0.2749 | 0.229 | 23 | 0.0155 | 0.2594 |
| tune-year objective | chop-allon | 2014-2017 | 30 | 0.01997 | 0.03424 | 19 | -0.09118 | 0.1112 |
| tune-year objective | chop-allon | 2015-2018 | 30 | -0.04315 | -0.05036 | 13 | -0.07734 | 0.03418 |
| tune-year objective | chop-routed | 2011-2014 | 30 | 0.1334 | 0.2034 | 21 | -0.05988 | 0.1933 |
| tune-year objective | chop-routed | 2012-2015 | 30 | -0.04838 | 0.007595 | 16 | -0.04633 | -0.002042 |
| tune-year objective | chop-routed | 2013-2016 | 30 | 0.03416 | 0.0008649 | 15 | 0.03998 | -0.005812 |
| tune-year objective | chop-routed | 2014-2017 | 30 | -0.1326 | -0.131 | 5 | -0.1 | -0.0326 |
| tune-year objective | chop-routed | 2015-2018 | 30 | -0.1093 | -0.1089 | 7 | -0.02564 | -0.08371 |
| tune-year objective | trend-allon | 2011-2014 | 30 | -0.1077 | -0.1082 | 7 | -0.02902 | -0.07866 |
| tune-year objective | trend-allon | 2012-2015 | 30 | -0.01989 | -0.08218 | 10 | -0.03857 | 0.01868 |
| tune-year objective | trend-allon | 2013-2016 | 30 | 0.03426 | 0.04851 | 17 | -0.007068 | 0.04133 |
| tune-year objective | trend-allon | 2014-2017 | 30 | -0.05633 | -0.05427 | 14 | -0.06072 | 0.004395 |
| tune-year objective | trend-allon | 2015-2018 | 30 | -0.0668 | -0.06515 | 8 | -0.04489 | -0.02191 |
| tune-year objective | trend-routed | 2011-2014 | 30 | 0.07726 | 0.01887 | 17 | -0.0316 | 0.1089 |
| tune-year objective | trend-routed | 2012-2015 | 30 | -0.01908 | -0.005527 | 15 | -0.05051 | 0.03144 |
| tune-year objective | trend-routed | 2013-2016 | 30 | 0.0903 | 0.05807 | 19 | -0.01187 | 0.1022 |
| tune-year objective | trend-routed | 2014-2017 | 30 | 0.07219 | 0.01948 | 17 | -0.09607 | 0.1683 |
| tune-year objective | trend-routed | 2015-2018 | 30 | 0.02564 | 0.03986 | 17 | -0.05539 | 0.08103 |


## 2. Persistence across the five steps, against a coin flip

`base_rate_pct` is that stream's own share of positive trade years, averaged over the five steps; `coin_flip_expected` is the binomial count at that rate.

| stream | k_of_5 | n_eligible | observed | base_rate_pct | coin_flip_expected | ratio_obs_over_expected |
|---|---|---|---|---|---|---|
| trend-routed | 5 | 263,753 | 1,899 | 33.91 | 1183 | 1.606 |
| trend-routed | 4 | 263,753 | 15,793 | 33.91 | 1.271e+04 | 1.243 |
| trend-routed | 3 | 263,753 | 60,773 | 33.91 | 5.763e+04 | 1.055 |
| trend-allon | 5 | 273,305 | 1,513 | 32.79 | 1035 | 1.461 |
| trend-allon | 4 | 273,305 | 14,491 | 32.79 | 1.165e+04 | 1.244 |
| trend-allon | 3 | 273,305 | 58,049 | 32.79 | 5.517e+04 | 1.052 |
| chop-routed | 5 | 249,908 | 1,650 | 39.12 | 2288 | 0.7211 |
| chop-routed | 4 | 249,908 | 16,927 | 39.12 | 2.01e+04 | 0.8423 |
| chop-routed | 3 | 249,908 | 71,968 | 39.12 | 7.554e+04 | 0.9527 |
| chop-allon | 5 | 271,862 | 2,504 | 37.08 | 1906 | 1.314 |
| chop-allon | 4 | 271,862 | 20,348 | 37.08 | 1.807e+04 | 1.126 |
| chop-allon | 3 | 271,862 | 75,223 | 37.08 | 7.295e+04 | 1.031 |


### The strategies positive on the trade year in all five steps

7,566 in total, listed in full in `results/r2gate2/modeA_top30_all5.csv` with their settings and per-year R. Count by stream:

| stream | n_all_five |
|---|---|
| chop-allon | 2,504 |
| chop-routed | 1,650 |
| trend-allon | 1,513 |
| trend-routed | 1,899 |


The first 15 of them, with per-year R:

| stream | sid | trade_R_2016 | trade_R_2017 | trade_R_2018 | trade_R_2019 | trade_R_2020 |
|---|---|---|---|---|---|---|
| trend-routed | adx_dmi_signals|bears_bulls_impulse_signals|variance_volume_signals|t3_baseline|adx_dmi_exit | 0.3118 | 0.004963 | 0.07794 | 0.5009 | 0.01963 |
| trend-routed | adx_dmi_signals|coppock_curve_signals|variance_volume_signals|ema_baseline|adx_dmi_exit | 0.04499 | 0.0328 | 0.03059 | 0.001046 | 0.1441 |
| trend-routed | adx_dmi_signals|coral_signals|chaikin_volatility_volume_signals|tma_baseline|adx_dmi_exit | 0.04978 | 0.1354 | 0.08609 | 0.06033 | 0.01719 |
| trend-routed | adx_dmi_signals|ehlers_reverse_ema_signals|variance_volume_signals|ema_baseline|adx_dmi_exit | 0.01866 | 0.03484 | 0.001019 | 0.07669 | 0.05589 |
| trend-routed | adx_dmi_signals|fisher_transform_signals|chaikin_volatility_volume_signals|ema_baseline|adx_dmi_exit | 0.2284 | 0.04607 | 0.08069 | 0.02566 | 0.001808 |
| trend-routed | adx_dmi_signals|fisher_transform_signals|chaikin_volatility_volume_signals|sma_baseline|adx_dmi_exit | 0.1203 | 0.1049 | 0.1475 | 0.01474 | 0.03075 |
| trend-routed | adx_dmi_signals|fisher_transform_signals|chaikin_volatility_volume_signals|tma_baseline|adx_dmi_exit | 0.02971 | 0.1676 | 0.1476 | 0.09914 | 0.0357 |
| trend-routed | adx_dmi_signals|glitch_index_signals|waddah_attar_explosion_volume_signals|vidya|adx_dmi_exit | 0.02245 | 0.1073 | 0.06301 | 0.04158 | 0.2237 |
| trend-routed | adx_dmi_signals|ichimoku_signals|waddah_attar_explosion_volume_signals|vidya|adx_dmi_exit | 0.009977 | 0.1825 | 0.03046 | 0.2959 | 0.1715 |
| trend-routed | adx_dmi_signals|kalman_filter_signals|waddah_attar_explosion_volume_signals|frama_baseline|adx_dmi_exit | 0.0213 | 0.03171 | 0.03525 | 0.2078 | 0.05415 |
| trend-routed | adx_dmi_signals|kuskus_starlight_signals|chaikin_volatility_volume_signals|ema_baseline|adx_dmi_exit | 0.1036 | 0.1173 | 0.04895 | 0.03534 | 0.01884 |
| trend-routed | adx_dmi_signals|kuskus_starlight_signals|volatility_ratio_volume_signals|sma_baseline|adx_dmi_exit | 0.02825 | 0.1238 | 0.03677 | 0.06928 | 0.01629 |
| trend-routed | adx_dmi_signals|lemantrend_signals|volatility_ratio_volume_signals|t3_baseline|adx_dmi_exit | 0.2199 | 0.1486 | 0.1257 | 0.0718 | 0.05447 |
| trend-routed | adx_dmi_signals|mama_fama_signals|waddah_attar_explosion_volume_signals|frama_baseline|adx_dmi_exit | 0.0808 | 0.004516 | 0.05757 | 0.1633 | 0.03135 |
| trend-routed | adx_dmi_signals|parabolic_sar_signals|chaikin_volatility_volume_signals|tma_baseline|adx_dmi_exit | 0.1265 | 0.1411 | 0.03403 | 0.1463 | 0.04566 |


## 4. Was anything known in advance about the all-five names?

Each all-five name's tune-year rank percentile in its own stream and step. If the tuner could see them coming, they would sit in the top bands.

| stream | band | n | total | pct_of_name_steps |
|---|---|---|---|---|
| chop-allon | bottom 50% | 3,027 | 12,520 | 24.18 |
| chop-allon | top 1% | 696 | 12,520 | 5.559 |
| chop-allon | top 10% | 3,035 | 12,520 | 24.24 |
| chop-allon | top 50% | 5,762 | 12,520 | 46.02 |
| chop-routed | bottom 50% | 2,415 | 8,250 | 29.27 |
| chop-routed | top 1% | 155 | 8,250 | 1.879 |
| chop-routed | top 10% | 1,418 | 8,250 | 17.19 |
| chop-routed | top 50% | 4,262 | 8,250 | 51.66 |
| trend-allon | bottom 50% | 2,184 | 7,565 | 28.87 |
| trend-allon | top 1% | 78 | 7,565 | 1.031 |
| trend-allon | top 10% | 1,343 | 7,565 | 17.75 |
| trend-allon | top 50% | 3,960 | 7,565 | 52.35 |
| trend-routed | bottom 50% | 4,196 | 9,495 | 44.19 |
| trend-routed | top 1% | 288 | 9,495 | 3.033 |
| trend-routed | top 10% | 871 | 9,495 | 9.173 |
| trend-routed | top 50% | 4,140 | 9,495 | 43.6 |


Pooled over streams:

| band | n | pct |
|---|---|---|
| top 50% | 18,124 | 47.91 |
| bottom 50% | 11,822 | 31.25 |
| top 10% | 6,667 | 17.62 |
| top 1% | 1,217 | 3.217 |


A uniform draw would put 1%% of name-steps in "top 1%%", 10%% in "top 10%%" and 50%% in "top 50%%". Compare those against the table above.
