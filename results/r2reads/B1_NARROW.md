# B1-NARROW — THE ELEVEN-STEP WALK ON A NARROW UNIVERSE

Generated 2026-11-24 21:20 by `code/b1narrow.py` with `FX_WALK=ext11`.

Eleven rolling steps: tune 2005-2008 / grade 2009 / trade 2010 through tune 2015-2018 / grade 2019 / trade 2020. **2021 onward stays sealed.** Same expectancy objective and grid as gate 2.


**THE SIX NEVER-SEEN YEARS.** The winners were selected on the FIVE-step walk, whose earliest tuning year is 2011 and whose trade years are 2016-2020. Trade years **2010, 2011, 2012, 2013, 2014 and 2015** were touched by no part of that selection. They are the test; 2016-2020 are the years the winners were chosen on and are shown only for contrast.


**BOTH CONDITIONS PASS ON THIS WALK**: condition 1 worst |per-year marks - trade R| = 8.88e-16 over 48 evaluations; condition 2 264 comparisons over 11 steps, zero tune-pick and zero record mismatches.


**WHAT IS NOT BANKED.** Per-config-per-year would be 19.1 GB against 10 GB free, so it was not built and **plateau selection and tuning-window length still need their own pass**. Nothing in this report needs it: every figure reads the selected configuration.


**THE JOIN, STATED.** Universe rows, rows matched into the bank by `sid`, rows not matched, and strategies in the bank:

- mode A: 4,008 universe rows, **3,968 matched**, 40 unmatched, 4,008 in the bank
- mode B: 4,002 universe rows, **4,002 matched**, 0 unmatched, 4,002 in the bank

Unmatched rows are universe rows whose strategy is not in the bank -- the universe csv was re-sampled after that bank was built. They are dropped, not substituted.


## The 10 winners, year by year

`never_seen = 1` marks a year no part of the original selection touched.

Stream is each winner's **own selected stream** from the five-step record, not a pooled figure.

| mode | sid | stream | R_2010 | R_2011 | R_2012 | R_2013 | R_2014 | R_2015 | R_2016 | R_2017 | R_2018 | R_2019 | R_2020 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | lemantrend_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | -0.0832 | -0.04362 | -0.08725 | -0.02067 | 0.05635 | -0.1242 | 0.05272 | 0.1213 | 0.3096 | 0.2034 | 0.1193 |
| A | lemantrend_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|fantail_vma|adx_dmi_exit | trend-allon | 0.01318 | -0.03417 | -0.03733 | 0.1619 | -0.06214 | -0.05503 | 0.05333 | 0.1967 | 0.2197 | 0.1456 | -0.002445 |
| A | lemantrend_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|frama_baseline|adx_dmi_exit | trend-allon | -0.08443 | -0.1164 | -0.0954 | 0.117 | -0.03898 | -0.062 | 0.03523 | -0.08259 | 0.3079 | 0.1246 | 0.08128 |
| A | lemantrend_signals|hieken_ashi_smoothed_signals|volatility_ratio_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | -0.09726 | -0.01779 | -0.09361 | 0.0739 | 0.06428 | -0.1241 | 0.05274 | 0.09414 | 0.2223 | 0.1732 | 0.03935 |
| A | lemantrend_signals|relative_vigor_index_signals|volatility_ratio_volume_signals|super_smoother_2pole_baseline|adx_dmi_exit | trend-allon | -0.1189 | 0.06514 | -0.1038 | -0.03284 | 0.04075 | 0.04027 | 0.1224 | -0.01559 | 0.1286 | 0.09284 | 0.1251 |
| A | waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | -0.08401 | -0.04857 | -0.06912 | -0.01255 | 0.005573 | 0.005165 | 0.04089 | 0.0911 | 0.3356 | 0.1585 | 0.09664 |
| A | waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|super_smoother_2pole_baseline|adx_dmi_exit | trend-allon | -0.09381 | -0.01292 | 0.1831 | -0.05479 | -0.1894 | -0.0209 | 0.06937 | 0.1114 | 0.3139 | 0.1058 | 0.07162 |
| A | waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|volatility_ratio_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | -0.09508 | -0.01516 | -0.07996 | 0.09456 | 0.03405 | 0.09474 | 0.02641 | 0.07992 | 0.1677 | 0.1455 | 0.03852 |
| B | lemantrend_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | 0.09089 | -0.1782 | -0.09208 | 0.1248 | 0.02018 | 0.04396 | 0.01873 | 0.1648 | 0.2803 | 0.08234 | 0.08594 |
| B | waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|fantail_vma|adx_dmi_exit | trend-allon | -0.07698 | -0.05514 | 0.007643 | 0.03952 | 0.05318 | 0.02793 | 0.1197 | 0.1411 | 0.2262 | 0.1465 | 0.1154 |


### The six never-seen years alone, per winner

| mode | sid | stream | R_new6_mean | t_new6 | years_pos_new6 | R_old5_mean | t_old5 | years_pos_old5 | R_all11_mean | years_pos_all11 |
|---|---|---|---|---|---|---|---|---|---|---|
| A | lemantrend_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | -0.05043 | -1.943 | 1 | 0.1613 | 3.655 | 5 | 0.04579 | 6 |
| A | lemantrend_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|fantail_vma|adx_dmi_exit | trend-allon | -0.002258 | -0.06533 | 2 | 0.1226 | 2.894 | 4 | 0.05449 | 6 |
| A | lemantrend_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|frama_baseline|adx_dmi_exit | trend-allon | -0.04669 | -1.352 | 1 | 0.09329 | 1.461 | 4 | 0.01694 | 5 |
| A | lemantrend_signals|hieken_ashi_smoothed_signals|volatility_ratio_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | -0.03244 | -0.9208 | 2 | 0.1163 | 3.295 | 5 | 0.03519 | 7 |
| A | lemantrend_signals|relative_vigor_index_signals|volatility_ratio_volume_signals|super_smoother_2pole_baseline|adx_dmi_exit | trend-allon | -0.01822 | -0.5621 | 3 | 0.09067 | 3.319 | 4 | 0.03128 | 7 |
| A | waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | -0.03392 | -2.144 | 2 | 0.1446 | 2.819 | 5 | 0.04721 | 7 |
| A | waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|super_smoother_2pole_baseline|adx_dmi_exit | trend-allon | -0.03146 | -0.6256 | 1 | 0.1344 | 2.943 | 5 | 0.04394 | 6 |
| A | waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|volatility_ratio_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | 0.005526 | 0.1628 | 3 | 0.09162 | 3.249 | 5 | 0.04466 | 8 |
| B | lemantrend_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | 0.001587 | 0.03372 | 4 | 0.1264 | 2.815 | 5 | 0.05833 | 9 |
| B | waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|fantail_vma|adx_dmi_exit | trend-allon | -0.0006418 | -0.02951 | 4 | 0.1498 | 7.483 | 5 | 0.06774 | 9 |


**2 of 10 winners have a positive mean R per trade on the six never-seen years.** Their mean on the five selection years is +0.12310 against -0.02089 on the six unseen ones.


## The family and the control, as distributions

Family and control are shown PER STREAM, because neither cohort has a selected stream and pooling the four would describe no strategy.

| mode | cohort | stream | n | mean_new6 | median_new6 | pct_positive_new6 | mean_old5 | mean_t_new6 |
|---|---|---|---|---|---|---|---|---|
| A | control | chop-allon | 1,960 | -0.02668 | -0.02531 | 36.28 | -0.04555 | -0.4317 |
| A | control | chop-routed | 1,960 | 0.002641 | 0.000448 | 47.5 | -0.04259 | -0.03118 |
| A | control | trend-allon | 1,960 | -0.008047 | -0.007253 | 43.01 | -0.03653 | -0.2511 |
| A | control | trend-routed | 1,960 | -0.01491 | -0.02141 | 37.81 | -0.05166 | -0.4558 |
| A | family | chop-allon | 2,000 | 0.002704 | 0.005309 | 50.9 | -0.02276 | 0.003503 |
| A | family | chop-routed | 2,000 | -0.01277 | -0.01417 | 36.95 | -0.03609 | -0.224 |
| A | family | trend-allon | 2,000 | -0.003213 | -0.004384 | 46.05 | -0.01887 | -0.09395 |
| A | family | trend-routed | 2,000 | -0.01542 | -0.0194 | 37.45 | -0.02211 | -0.3989 |
| A | winner | chop-allon | 8 | -0.02673 | -0.024 | 0 | 0.1543 | -0.556 |
| A | winner | chop-routed | 8 | -0.08477 | -0.08473 | 0 | 0.02086 | -1.264 |
| A | winner | trend-allon | 8 | -0.02624 | -0.03195 | 12.5 | 0.1193 | -0.9314 |
| A | winner | trend-routed | 8 | -0.008444 | -0.01699 | 37.5 | 0.1222 | -0.3104 |
| B | control | chop-allon | 2,000 | -0.01923 | -0.01857 | 38.35 | -0.04825 | -0.3308 |
| B | control | chop-routed | 2,000 | 0.004767 | 0.002295 | 48.3 | -0.04774 | -0.007327 |
| B | control | trend-allon | 2,000 | -0.002696 | -0.003886 | 46.15 | -0.03557 | -0.1694 |
| B | control | trend-routed | 2,000 | -0.005888 | -0.01436 | 39.3 | -0.05103 | -0.3761 |
| B | family | chop-allon | 2,000 | 0.009602 | 0.00834 | 54.8 | -0.0204 | 0.1195 |
| B | family | chop-routed | 2,000 | 0.001508 | -0.002621 | 42.85 | -0.03684 | -0.05497 |
| B | family | trend-allon | 2,000 | 0.005797 | 0.005565 | 54.5 | -0.01986 | 0.05358 |
| B | family | trend-routed | 2,000 | -0.01413 | -0.01792 | 37.15 | -0.01987 | -0.5568 |
| B | winner | chop-allon | 2 | -0.05452 | -0.05452 | 0 | 0.2383 | -0.8252 |
| B | winner | chop-routed | 2 | -0.05067 | -0.05067 | 0 | -0.08704 | -0.7224 |
| B | winner | trend-allon | 2 | 0.0004724 | 0.0004724 | 50 | 0.1381 | 0.002108 |
| B | winner | trend-routed | 2 | 0.03593 | 0.03593 | 100 | 0.06354 | 0.3716 |


### Each winner against the control, on its OWN stream

The percentile is the share of CONTROL strategies on the same stream and in the same mode whose mean R per trade on the six never-seen years is **below** the winner. 50 means the winner is at the control median; a winner that carried a real edge into unseen years should sit high.

| mode | sid | stream | R_new6_mean | control_n | control_mean | pctile_vs_control |
|---|---|---|---|---|---|---|
| A | waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|volatility_ratio_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | 0.005526 | 1,960 | -0.008047 | 61.48 |
| B | lemantrend_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | 0.001587 | 2,000 | -0.002696 | 55.3 |
| A | lemantrend_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|fantail_vma|adx_dmi_exit | trend-allon | -0.002258 | 1,960 | -0.008047 | 54.74 |
| B | waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|fantail_vma|adx_dmi_exit | trend-allon | -0.0006418 | 2,000 | -0.002696 | 53.2 |
| A | lemantrend_signals|relative_vigor_index_signals|volatility_ratio_volume_signals|super_smoother_2pole_baseline|adx_dmi_exit | trend-allon | -0.01822 | 1,960 | -0.008047 | 41.22 |
| A | waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|super_smoother_2pole_baseline|adx_dmi_exit | trend-allon | -0.03146 | 1,960 | -0.008047 | 30.97 |
| A | lemantrend_signals|hieken_ashi_smoothed_signals|volatility_ratio_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | -0.03244 | 1,960 | -0.008047 | 30.51 |
| A | waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | -0.03392 | 1,960 | -0.008047 | 29.69 |
| A | lemantrend_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|frama_baseline|adx_dmi_exit | trend-allon | -0.04669 | 1,960 | -0.008047 | 21.68 |
| A | lemantrend_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | -0.05043 | 1,960 | -0.008047 | 19.95 |


**Median winner percentile against its own-stream control: 36.1.** 4 of 10 winners sit above the control median.


If the family and the control are indistinguishable on the six never-seen years, the components the winners are built from carry nothing the rest of the field lacks — which is what A1 already suggested when no slot option was profitable.


## Prop return

**A STATED PROXY, not the A6 figure.** Prop return needs a drawdown and the eleven-step winner-only bank does not carry max DD, so this uses the spread of the per-year R values in place of it. It ranks correctly within this table and is NOT comparable to the prop return in `MODEA_WINNERS.md`.

| mode | sid | stream | R_new6_mean | prop_proxy_new6 |
|---|---|---|---|---|
| A | waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|volatility_ratio_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | 0.005526 | 0.03988 |
| B | lemantrend_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | 0.001587 | 0.00826 |
| B | waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|fantail_vma|adx_dmi_exit | trend-allon | -0.0006418 | -0.007227 |
| A | lemantrend_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|fantail_vma|adx_dmi_exit | trend-allon | -0.002258 | -0.016 |
| A | lemantrend_signals|relative_vigor_index_signals|volatility_ratio_volume_signals|super_smoother_2pole_baseline|adx_dmi_exit | trend-allon | -0.01822 | -0.1377 |
| A | waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|super_smoother_2pole_baseline|adx_dmi_exit | trend-allon | -0.03146 | -0.1532 |
| A | lemantrend_signals|hieken_ashi_smoothed_signals|volatility_ratio_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | -0.03244 | -0.2255 |
| A | lemantrend_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|frama_baseline|adx_dmi_exit | trend-allon | -0.04669 | -0.3313 |
| A | lemantrend_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | -0.05043 | -0.476 |
| A | waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | -0.03392 | -0.5252 |


## Random-entry null on the six never-seen years

_Not run. It needs an engine pass over the universe on the eleven-step walk and is a declared follow-on, not part of this read._


## Provenance

- `results/r2reads/b1narrow_per_strategy.csv` — 31,880 rows, md5 `6942fb3d8a70`
- `results/r2reads/modeA_b1narrow_universe.csv` — 4,008 rows, md5 `9cf6e43526d4`
- `results/r2reads/modeB_b1narrow_universe.csv` — 4,002 rows, md5 `0b8ad1cd00c6`
