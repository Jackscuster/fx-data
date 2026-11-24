# A2 TUNED VERSUS DEFAULT, A1 ON DEFAULTS, AND A3 HONEST SIGNIFICANCE — MODE A

Generated 2026-11-24 12:49 by `code/r2reads.py`.

A2 needed ONE engine pass, because the gate 2 bank stores only the WINNER's per-year record — the gate 1 default has none. That is 2 configurations per strategy against 547 in a full tune, about 0.4%. A1 on defaults rides the same pass, which is why Jack put them in one chunk. A3 is a pure read of the saved daily series.


## A2 — tuned minus default on the unseen years

| role | scope | n_compared | tuned_R_per_trade | default_R_per_trade | mean_diff | median_diff | share_helped_pct | p10 | p90 |
|---|---|---|---|---|---|---|---|---|---|
| trade | ALL | 273,463 | -0.03985 | -0.04758 | 0.007732 | 0.002551 | 52.78 | -0.05344 | 0.07224 |
| trade | trend-routed | 269,890 | -0.04556 | -0.045 | -0.000559 | -0.0001144 | 49.92 | -0.1075 | 0.1019 |
| trade | trend-allon | 273,463 | -0.03428 | -0.04173 | 0.007444 | 0.003306 | 53.58 | -0.05267 | 0.07329 |
| trade | chop-routed | 254,894 | -0.04341 | -0.06129 | 0.01788 | 0.01025 | 55.1 | -0.1075 | 0.1511 |
| trade | chop-allon | 272,595 | -0.04375 | -0.05695 | 0.0132 | 0.005462 | 53.38 | -0.08939 | 0.1238 |
| grade | ALL | 273,455 | -0.02141 | -0.03675 | 0.01534 | 0.00672 | 56.39 | -0.05484 | 0.09765 |
| grade | trend-routed | 269,739 | 0.0003759 | -0.02402 | 0.02439 | 0.01142 | 56.13 | -0.1076 | 0.1919 |
| grade | trend-allon | 273,455 | -0.01777 | -0.03181 | 0.01404 | 0.005965 | 55.39 | -0.05709 | 0.09967 |
| grade | chop-routed | 254,894 | -0.03423 | -0.05716 | 0.02294 | 0.006371 | 53.19 | -0.1061 | 0.1585 |
| grade | chop-allon | 272,587 | -0.03134 | -0.04897 | 0.01763 | 0.006411 | 53.73 | -0.09023 | 0.1395 |


On the trade year, pooled: tuning moved R per trade by **+0.00773** on average and helped **52.8%** of strategies. If that share is near 50% and the mean near zero, the tuner is choosing noise.


## A1 repeated on the DEFAULT configuration

The same slot read with every strategy on its gate 1 default. If an option's effect survives here it is a property of the component, not of what the tuner did with it.

| slot | option | n_strategies | n_trades | R_per_trade | total_R |
|---|---|---|---|---|---|
| vol | williams_vix_fix_volume_signals | 22,815 | 7.265e+06 | 0.002816 | 2.046e+04 |
| c1 | waddah_attar_explosion_signals | 7,020 | 1.082e+07 | -0.0006691 | -7238 |
| c1 | lemantrend_signals | 7,020 | 1.047e+07 | -0.0009575 | -1.002e+04 |
| vol | waddah_attar_explosion_volume_signals | 22,815 | 4.826e+07 | -0.002553 | -1.232e+05 |
| c2 | waddah_attar_explosion_signals | 7,020 | 1.625e+07 | -0.00393 | -6.387e+04 |
| c2 | lemantrend_signals | 7,020 | 1.568e+07 | -0.005795 | -9.088e+04 |
| c1 | fisher_transform_signals | 7,020 | 2.588e+07 | -0.0161 | -4.167e+05 |
| vol | variance_volume_signals | 22,815 | 6.362e+07 | -0.01943 | -1.236e+06 |
| c1 | coral_signals | 7,020 | 2.199e+07 | -0.02101 | -4.62e+05 |
| c1 | center_of_gravity_signals | 7,020 | 2.106e+07 | -0.02172 | -4.574e+05 |
| c1 | aroon_signals | 7,020 | 1.695e+07 | -0.02361 | -4.001e+05 |
| c2 | schaff_trend_cycle_signals | 7,020 | 1.942e+07 | -0.02455 | -4.768e+05 |
| c2 | coral_signals | 7,020 | 2.209e+07 | -0.02461 | -5.438e+05 |
| c2 | parabolic_sar_signals | 7,020 | 2.03e+07 | -0.02566 | -5.21e+05 |
| c2 | hieken_ashi_smoothed_signals | 7,020 | 1.725e+07 | -0.02669 | -4.603e+05 |
| c1 | hieken_ashi_smoothed_signals | 7,020 | 1.835e+07 | -0.02675 | -4.907e+05 |
| c1 | fx_sniper_ergodic_cci_signals | 7,020 | 1.906e+07 | -0.02715 | -5.175e+05 |
| c2 | fx_sniper_ergodic_cci_signals | 7,020 | 1.937e+07 | -0.02723 | -5.275e+05 |
| base | mcginley_dynamic_index | 18,252 | 3.125e+07 | -0.02742 | -8.568e+05 |
| c1 | relative_vigor_index_signals | 7,020 | 2.019e+07 | -0.02747 | -5.546e+05 |
| c2 | fisher_transform_signals | 7,020 | 2.384e+07 | -0.02891 | -6.891e+05 |
| base | sma_baseline | 18,252 | 2.865e+07 | -0.02904 | -8.318e+05 |
| c2 | center_of_gravity_signals | 7,020 | 1.96e+07 | -0.02948 | -5.776e+05 |
| c1 | bears_bulls_impulse_signals | 7,020 | 1.821e+07 | -0.02956 | -5.383e+05 |
| base | rma_baseline | 18,252 | 2.895e+07 | -0.03021 | -8.746e+05 |
| base | ema_baseline | 18,252 | 3.437e+07 | -0.03148 | -1.082e+06 |
| c2 | ssl_channel_signals | 7,020 | 2.201e+07 | -0.03199 | -7.04e+05 |
| vol | volatility_ratio_volume_signals | 22,815 | 7.969e+07 | -0.03235 | -2.578e+06 |
| c2 | bears_bulls_impulse_signals | 7,020 | 1.061e+07 | -0.03253 | -3.452e+05 |
| c1 | schaff_trend_cycle_signals | 7,020 | 1.498e+07 | -0.03477 | -5.208e+05 |


## A3 — honest significance on the books

Yearly return over yearly volatility, worst dip, and a **block-bootstrap t on 20-day blocks** beside the naive daily t. Blocks keep the within-block dependence a book's multi-day positions create and destroy only the between-block ordering; a naive daily t treats consecutive days as independent and is inflated when they are not.

| source | book | budget | days | years | yearly_return_pct | yearly_vol_pct | return_over_vol | worst_dip_pct | t_block_bootstrap | t_naive_daily | inflation_naive_over_block |
|---|---|---|---|---|---|---|---|---|---|---|---|
| winners_book | allon | team1 | 1,281 | 5 | 2.963 | 1.8 | 1.646 | 1.977 | 3.483 | 3.416 | 0.9806 |
| winners_book | allon | team2 | 1,281 | 5 | 4.444 | 2.701 | 1.646 | 2.966 | 3.4 | 3.416 | 1.005 |
| passers_book | allon | team1 | 1,296 | 5 | 0.09726 | 3.078 | 0.0316 | 6.536 | 0.08153 | 0.078 | 0.9567 |
| passers_book | allon | team2 | 1,296 | 5 | 0.1459 | 4.617 | 0.0316 | 9.804 | 0.08257 | 0.078 | 0.9446 |
| passers_book | chop_trend | team1 | 1,296 | 5 | -1.469 | 1.17 | -1.255 | 8.15 | -1.834 | -1.597 | 0.8712 |
| passers_book | chop_trend | team2 | 1,296 | 5 | -2.203 | 1.756 | -1.255 | 12.23 | -1.83 | -1.597 | 0.8727 |
| full_field_book | allon | team1 | 1,296 | 5 | -1.075 | 1.129 | -0.9523 | 7.233 | -1.326 | -1.211 | 0.9132 |
| full_field_book | allon | team2 | 1,296 | 5 | -1.612 | 1.693 | -0.9523 | 10.85 | -1.271 | -1.211 | 0.953 |
| full_field_book | chop_trend | team1 | 1,296 | 5 | -0.8753 | 0.9692 | -0.9031 | 5.279 | -1.313 | -1.236 | 0.9415 |
| full_field_book | chop_trend | team2 | 1,296 | 5 | -1.313 | 1.454 | -0.9031 | 7.918 | -1.341 | -1.236 | 0.9224 |
| full_field_book | chop_ungated | team1 | 1,296 | 5 | -0.5611 | 0.7596 | -0.7386 | 4.486 | -0.7794 | -0.7684 | 0.9859 |
| full_field_book | chop_ungated | team2 | 1,296 | 5 | -0.8416 | 1.139 | -0.7386 | 6.729 | -0.7784 | -0.7684 | 0.9872 |
| full_field_book | chop_notrange | team1 | 1,296 | 5 | -1.067 | 0.9594 | -1.112 | 7.073 | -1.834 | -1.604 | 0.8745 |
| full_field_book | chop_notrange | team2 | 1,296 | 5 | -1.6 | 1.439 | -1.112 | 10.61 | -1.84 | -1.604 | 0.8713 |


On the winners' book the block t and the naive t agree closely, so the daily series is **not** materially autocorrelated at book level — the naive t was not flattering it. That is worth knowing because it was the suspicion that motivated this item.


## Provenance

| file | rows | md5 |
|---|---|---|
| `results/r2reads/modeA_a2_tuned_vs_default.csv` | 10 | 191fa7669715 |
| `results/r2reads/modeA_a1_slots_defaults.csv` | 212 | 2c3b0b3fce36 |
| `results/r2reads/modeA_a3_significance.csv` | 14 | e4e52163419d |
