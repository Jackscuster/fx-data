# THE WINNERS BY PAIR AND BY DIRECTION, AND PAIR ROUTING

Generated 2026-11-22 14:31 by `code/l2r2pairs.py`. Part 1 of item 3: the non-luck winners broken out per pair, per direction, per year, and their PAIR-ROUTED trade-year record against trading all 28.


**The routing is walk forward and there is no per-pair tuning.** The settings are the ones each strategy already won with; the only per-step choice is WHICH PAIRS to trade, made on that step's TUNING years alone and then applied unchanged to the trade year.


**PROP RETURN** is the yearly return at a 3.6% worst dip, which for a strategy is `0.72 x return/DD`; the target is 12% a year, i.e. **return/DD >= 16.67**.


## The headline

| mode | winners | all28_return_per_dd | all28_prop_return_pct | best_K | best_K_return_per_dd | random_null_at_best_K | K_where_real_beats_random | clears_12pct |
|---|---|---|---|---|---|---|---|---|
| A | 8 | 0.8339 | 0.6004 | 2 | 0.8475 | 1.061 | 1 of 28 | 0 |
| B | 2 | 1.21 | 0.8712 | 1 | 1.454 | 2.279 | 7 of 28 | 0 |


**Pair routing is no better than a random pair pick.** The null -- a subset of the SAME SIZE drawn from the pairs the strategy actually traded in the tuning years -- scores higher at most K. The `K_where_real_beats_random` column is the honest count: the real rule wins at a minority of the 28 values of K, which is what a coin flip would give. Ranking pairs by their tuning-year return per drawdown carries no usable information about the trade year.


**THE DRAWDOWN BASIS HERE IS NOT THE ONE IN `MODE*_WINNERS.md`, and the two ratios must not be compared.** This table sums each (pair, direction, year) drawdown, which is a far looser upper bound than the strategy-level drawdown -- a strategy whose pairs draw down at different times has a portfolio drawdown far smaller than the sum of theirs. That is why return/DD reads ~0.8 here against 1.95-3.13 in the winners table. The comparison inside this table is sound because real and null use the identical basis; the LEVEL is not comparable to anything outside it, and the prop return computed from it is therefore a floor, not an estimate.


**Nothing here clears 12% at prop sizing.** Routed or unrouted, the best return/DD in the table is far below the 16.67 the target needs.


## Mode A


### The rules, against all 28 and against the null

| rule | K | pairs_selected | real_return_per_dd | random_null_return_per_dd | real_beats_null | prop_return_pct |
|---|---|---|---|---|---|---|
| topk | 1 | 1 | 0.8229 | 1.252 | 0 | 0.5925 |
| topk | 2 | 2 | 0.8475 | 1.061 | 0 | 0.6102 |
| topk | 3 | 3 | 0.5726 | 0.9628 | 0 | 0.4123 |
| topk | 4 | 4 | 0.6386 | 0.862 | 0 | 0.4598 |
| topk | 5 | 5 | 0.7301 | 0.9021 | 0 | 0.5256 |
| topk | 6 | 6 | 0.766 | 0.9159 | 0 | 0.5515 |
| topk | 7 | 7 | 0.7551 | 0.8625 | 0 | 0.5437 |
| topk | 8 | 8 | 0.6912 | 0.8687 | 0 | 0.4976 |
| topk | 9 | 9 | 0.7511 | 0.8986 | 0 | 0.5408 |
| topk | 10 | 10 | 0.6879 | 0.844 | 0 | 0.4953 |
| topk | 11 | 11 | 0.6908 | 0.8885 | 0 | 0.4974 |
| topk | 12 | 12 | 0.7284 | 0.8291 | 0 | 0.5244 |
| topk | 13 | 13 | 0.7279 | 0.8967 | 0 | 0.5241 |
| topk | 14 | 14 | 0.7182 | 0.835 | 0 | 0.5171 |
| topk | 15 | 15 | 0.7217 | 0.8492 | 0 | 0.5196 |
| topk | 16 | 16 | 0.7214 | 0.8488 | 0 | 0.5194 |
| topk | 17 | 17 | 0.7371 | 0.8334 | 0 | 0.5307 |
| topk | 18 | 18 | 0.7392 | 0.838 | 0 | 0.5322 |
| topk | 19 | 19 | 0.7611 | 0.8422 | 0 | 0.548 |
| topk | 20 | 20 | 0.7699 | 0.8271 | 0 | 0.5544 |
| topk | 21 | 21 | 0.7778 | 0.8369 | 0 | 0.56 |
| topk | 22 | 22 | 0.7892 | 0.8247 | 0 | 0.5682 |
| topk | 23 | 23 | 0.7855 | 0.8293 | 0 | 0.5656 |
| topk | 24 | 24 | 0.7933 | 0.8334 | 0 | 0.5712 |
| topk | 25 | 25 | 0.7997 | 0.8291 | 0 | 0.5758 |
| topk | 26 | 26 | 0.8227 | 0.8304 | 0 | 0.5924 |
| topk | 27 | 27 | 0.8074 | 0.8356 | 0 | 0.5813 |
| topk | 28 | 27.98 | 0.8339 | 0.8339 | 1 | 0.6004 |
| threshold |  | 19.9 | 0.7726 |  |  | 0.5563 |
| topk_dir |  | 14.5 | 0.8636 |  |  | 0.6218 |
| threshold_dir |  | 35 | 0.9253 |  |  | 0.6662 |
| all28 (no routing) |  | 28 | 0.8339 |  |  | 0.6004 |


### Top 30 by prop return, per winner, unrouted

| sid | stream | trade_n | trade_total_R | trade_max_dd_R | return_per_dd | prop_return_pct_per_year | clears_12pct |
|---|---|---|---|---|---|---|---|
| lemantrend_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | 816 | 140.2 | 123.6 | 1.134 | 0.8165 | 0 |
| waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | 758 | 121.1 | 118 | 1.026 | 0.7386 | 0 |
| lemantrend_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|fantail_vma|adx_dmi_exit | trend-allon | 890 | 119.1 | 145.5 | 0.8184 | 0.5893 | 0 |
| waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|super_smoother_2pole_baseline|adx_dmi_exit | trend-allon | 966 | 134.5 | 166.2 | 0.8091 | 0.5825 | 0 |
| lemantrend_signals|hieken_ashi_smoothed_signals|volatility_ratio_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | 1290 | 167.7 | 210.6 | 0.7962 | 0.5732 | 0 |
| lemantrend_signals|relative_vigor_index_signals|volatility_ratio_volume_signals|super_smoother_2pole_baseline|adx_dmi_exit | trend-allon | 1178 | 143.1 | 190.7 | 0.7502 | 0.5402 | 0 |
| waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|volatility_ratio_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | 1270 | 145.1 | 214.9 | 0.6751 | 0.4861 | 0 |
| lemantrend_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|frama_baseline|adx_dmi_exit | trend-allon | 1060 | 101.2 | 152.7 | 0.6624 | 0.4769 | 0 |


### Where the money came from: by pair, trade years only

All 28 pairs, summed over the 8 winners and the five trade years. Full per (pair, direction, year) detail in `results/r2gate2/modeA_winners_by_pair.csv`.

| pair | n | total_R | max_dd_R | return_per_dd |
|---|---|---|---|---|
| NZDJPY | 302 | 86.28 | 34.27 | 2.518 |
| CHFJPY | 312 | 74.39 | 36.97 | 2.012 |
| NZDCAD | 278 | 63.17 | 40.1 | 1.575 |
| AUDJPY | 240 | 62.8 | 30 | 2.093 |
| USDCHF | 344 | 58.16 | 41.67 | 1.396 |
| NZDCHF | 318 | 56.15 | 44.92 | 1.25 |
| GBPNZD | 224 | 54.04 | 31.99 | 1.689 |
| USDCAD | 362 | 50.06 | 59.29 | 0.8444 |
| CADJPY | 318 | 48.26 | 45.44 | 1.062 |
| CADCHF | 358 | 45.77 | 58.07 | 0.7882 |
| NZDUSD | 280 | 40.2 | 43.93 | 0.9151 |
| EURCAD | 396 | 40.16 | 64.96 | 0.6183 |
| AUDNZD | 286 | 36.66 | 47.11 | 0.7782 |
| EURJPY | 284 | 36.14 | 39.84 | 0.9072 |
| AUDCAD | 280 | 34.59 | 46.82 | 0.7387 |
| EURAUD | 350 | 33.7 | 62.78 | 0.5368 |
| GBPCHF | 260 | 30.88 | 45.49 | 0.6788 |
| GBPUSD | 268 | 30.35 | 50.35 | 0.6027 |
| AUDUSD | 298 | 30.18 | 55.83 | 0.5405 |
| USDJPY | 254 | 29.67 | 46 | 0.6451 |
| GBPAUD | 226 | 27.5 | 33.29 | 0.8259 |
| EURNZD | 278 | 23.43 | 52.5 | 0.4462 |
| EURGBP | 250 | 19.77 | 42.92 | 0.4606 |
| EURCHF | 266 | 17.02 | 48.4 | 0.3516 |
| AUDCHF | 392 | 15.03 | 72.05 | 0.2086 |
| GBPJPY | 270 | 11.82 | 56.47 | 0.2093 |
| EURUSD | 250 | 11 | 40.51 | 0.2715 |
| GBPCAD | 284 | 4.733 | 50.4 | 0.09391 |


### By direction

| direction | n | total_R | max_dd_R | return_per_dd |
|---|---|---|---|---|
| long | 4,036 | 582.3 | 631.7 | 0.9218 |
| short | 4,192 | 489.5 | 690.6 | 0.7088 |


## Mode B


### The rules, against all 28 and against the null

| rule | K | pairs_selected | real_return_per_dd | random_null_return_per_dd | real_beats_null | prop_return_pct |
|---|---|---|---|---|---|---|
| topk | 1 | 1 | 1.454 | 2.279 | 0 | 1.047 |
| topk | 2 | 2 | 1.297 | 1.585 | 0 | 0.9337 |
| topk | 3 | 3 | 1.269 | 1.29 | 0 | 0.9135 |
| topk | 4 | 4 | 1.333 | 1.422 | 0 | 0.9599 |
| topk | 5 | 5 | 0.8727 | 1.357 | 0 | 0.6283 |
| topk | 6 | 6 | 1.046 | 1.495 | 0 | 0.7532 |
| topk | 7 | 7 | 0.9973 | 1.247 | 0 | 0.7181 |
| topk | 8 | 8 | 1.081 | 1.395 | 0 | 0.7781 |
| topk | 9 | 9 | 1.246 | 1.252 | 0 | 0.897 |
| topk | 10 | 10 | 1.081 | 1.139 | 0 | 0.7785 |
| topk | 11 | 11 | 0.9209 | 1.213 | 0 | 0.663 |
| topk | 12 | 12 | 0.8445 | 1.229 | 0 | 0.6081 |
| topk | 13 | 13 | 0.8351 | 1.19 | 0 | 0.6012 |
| topk | 14 | 14 | 0.9377 | 1.187 | 0 | 0.6752 |
| topk | 15 | 15 | 1.068 | 1.206 | 0 | 0.7693 |
| topk | 16 | 16 | 1.13 | 1.233 | 0 | 0.8136 |
| topk | 17 | 17 | 1.189 | 1.199 | 0 | 0.8564 |
| topk | 18 | 18 | 1.171 | 1.272 | 0 | 0.843 |
| topk | 19 | 19 | 1.151 | 1.245 | 0 | 0.8288 |
| topk | 20 | 20 | 1.186 | 1.212 | 0 | 0.8539 |
| topk | 21 | 21 | 1.227 | 1.188 | 1 | 0.8833 |
| topk | 22 | 22 | 1.292 | 1.174 | 1 | 0.9306 |
| topk | 23 | 23 | 1.429 | 1.217 | 1 | 1.029 |
| topk | 24 | 24 | 1.382 | 1.207 | 1 | 0.9951 |
| topk | 25 | 25 | 1.365 | 1.202 | 1 | 0.9831 |
| topk | 26 | 26 | 1.269 | 1.209 | 1 | 0.9139 |
| topk | 27 | 27 | 1.271 | 1.219 | 1 | 0.915 |
| topk | 28 | 28 | 1.21 | 1.21 | 0 | 0.8712 |
| threshold |  | 19.9 | 1.221 |  |  | 0.8793 |
| topk_dir |  | 14.5 | 1.397 |  |  | 1.006 |
| threshold_dir |  | 33 | 1.243 |  |  | 0.8953 |
| all28 (no routing) |  | 28 | 1.21 |  |  | 0.8712 |


### Top 30 by prop return, per winner, unrouted

| sid | stream | trade_n | trade_total_R | trade_max_dd_R | return_per_dd | prop_return_pct_per_year | clears_12pct |
|---|---|---|---|---|---|---|---|
| waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|fantail_vma|adx_dmi_exit | trend-allon | 584 | 102.3 | 74.33 | 1.376 | 0.9907 | 0 |
| lemantrend_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | 846 | 113.6 | 108.8 | 1.044 | 0.7517 | 0 |


### Where the money came from: by pair, trade years only

All 28 pairs, summed over the 2 winners and the five trade years. Full per (pair, direction, year) detail in `results/r2gate2/modeB_winners_by_pair.csv`.

| pair | n | total_R | max_dd_R | return_per_dd |
|---|---|---|---|---|
| CHFJPY | 62 | 15.85 | 6.485 | 2.444 |
| EURNZD | 48 | 15.66 | 7.468 | 2.097 |
| GBPNZD | 44 | 15.05 | 5.199 | 2.894 |
| AUDJPY | 42 | 14.4 | 3.71 | 3.88 |
| GBPCHF | 48 | 13.22 | 5.656 | 2.338 |
| EURCAD | 64 | 13.2 | 4.82 | 2.74 |
| AUDCAD | 44 | 12.47 | 4.951 | 2.518 |
| NZDCAD | 34 | 12.18 | 3.445 | 3.536 |
| CADCHF | 66 | 12 | 7.893 | 1.52 |
| NZDJPY | 48 | 11.92 | 4.062 | 2.934 |
| USDJPY | 28 | 10.54 | 2.464 | 4.28 |
| EURGBP | 46 | 10.5 | 6.071 | 1.73 |
| NZDUSD | 60 | 10.44 | 8.173 | 1.277 |
| GBPAUD | 44 | 7.207 | 5.114 | 1.409 |
| GBPUSD | 48 | 7.173 | 5.056 | 1.419 |
| GBPCAD | 48 | 7.173 | 5.186 | 1.383 |
| GBPJPY | 48 | 7.059 | 5.982 | 1.18 |
| NZDCHF | 46 | 7.021 | 4.884 | 1.438 |
| AUDUSD | 64 | 6.244 | 9.883 | 0.6318 |
| USDCAD | 48 | 4.814 | 6.298 | 0.7644 |
| USDCHF | 58 | 4.443 | 5.659 | 0.7852 |
| CADJPY | 32 | 2.86 | 3.286 | 0.8702 |
| EURCHF | 56 | 2.415 | 9.135 | 0.2643 |
| EURAUD | 68 | -0.3588 | 12.23 | -0.02934 |
| EURJPY | 58 | -0.5642 | 8.701 | -0.06484 |
| EURUSD | 42 | -1.177 | 7.974 | -0.1475 |
| AUDNZD | 54 | -2.262 | 9.436 | -0.2398 |
| AUDCHF | 82 | -3.61 | 13.92 | -0.2594 |


### By direction

| direction | n | total_R | max_dd_R | return_per_dd |
|---|---|---|---|---|
| long | 740 | 111.6 | 88.38 | 1.262 |
| short | 690 | 104.3 | 94.76 | 1.101 |


## Provenance

| file | rows | md5 |
|---|---|---|
| `results/r2gate2/modeA_winners_by_pair.csv` | 17,329 | 68a40fed2b5d |
| `results/r2gate2/modeA_winners_pairrouted.csv` | 696 | 53d122566182 |
| `results/r2gate2/modeB_winners_by_pair.csv` | 3,605 | a1babe4c85b3 |
| `results/r2gate2/modeB_winners_pairrouted.csv` | 174 | ebdc16e810da |
