# A2 TUNED VERSUS DEFAULT, A1 ON DEFAULTS, AND A3 HONEST SIGNIFICANCE — MODE B

Generated 2026-11-24 16:27 by `code/r2reads.py`.

A2 needed ONE engine pass, because the gate 2 bank stores only the WINNER's per-year record — the gate 1 default has none. That is 2 configurations per strategy against 547 in a full tune, about 0.4%. A1 on defaults rides the same pass, which is why Jack put them in one chunk. A3 is a pure read of the saved daily series.


## A2 — tuned minus default on the unseen years

| role | scope | n_compared | tuned_R_per_trade | default_R_per_trade | mean_diff | median_diff | share_helped_pct | p10 | p90 |
|---|---|---|---|---|---|---|---|---|---|
| trade | ALL | 273,467 | -0.03889 | -0.04754 | 0.008641 | 0.004197 | 55.27 | -0.04498 | 0.06774 |
| trade | trend-routed | 270,067 | -0.04237 | -0.04537 | 0.002999 | 0.002132 | 51.67 | -0.08663 | 0.09258 |
| trade | trend-allon | 273,467 | -0.03182 | -0.03906 | 0.007248 | 0.003872 | 54.82 | -0.04527 | 0.0657 |
| trade | chop-routed | 255,640 | -0.04791 | -0.06497 | 0.01706 | 0.01121 | 56.43 | -0.09239 | 0.1344 |
| trade | chop-allon | 272,625 | -0.04461 | -0.06028 | 0.01567 | 0.008695 | 55.97 | -0.07737 | 0.1175 |
| grade | ALL | 273,459 | -0.02228 | -0.03539 | 0.01311 | 0.006334 | 56.89 | -0.04958 | 0.08967 |
| grade | trend-routed | 269,915 | -0.003074 | -0.02246 | 0.01938 | 0.009143 | 55.97 | -0.09731 | 0.1637 |
| grade | trend-allon | 273,459 | -0.01654 | -0.02896 | 0.01241 | 0.005881 | 56.03 | -0.05132 | 0.09147 |
| grade | chop-routed | 255,641 | -0.03687 | -0.05708 | 0.02021 | 0.008405 | 54.66 | -0.0938 | 0.145 |
| grade | chop-allon | 272,615 | -0.03313 | -0.05006 | 0.01693 | 0.007384 | 54.85 | -0.08086 | 0.1284 |


On the trade year, pooled: tuning moved R per trade by **+0.00864** on average and helped **55.3%** of strategies. If that share is near 50% and the mean near zero, the tuner is choosing noise.


## A1 repeated on the DEFAULT configuration

The same slot read with every strategy on its gate 1 default. If an option's effect survives here it is a property of the component, not of what the tuner did with it.

| slot | option | n_strategies | n_trades | R_per_trade | total_R |
|---|---|---|---|---|---|
| vol | williams_vix_fix_volume_signals | 22,815 | 7.3e+06 | 0.005502 | 4.017e+04 |
| c1 | lemantrend_signals | 7,020 | 1.172e+07 | -0.009282 | -1.088e+05 |
| c2 | lemantrend_signals | 7,020 | 1.695e+07 | -0.009561 | -1.621e+05 |
| vol | waddah_attar_explosion_volume_signals | 22,815 | 5.338e+07 | -0.009929 | -5.3e+05 |
| c2 | waddah_attar_explosion_signals | 7,020 | 1.776e+07 | -0.01019 | -1.81e+05 |
| c1 | waddah_attar_explosion_signals | 7,020 | 1.227e+07 | -0.01043 | -1.28e+05 |
| vol | variance_volume_signals | 22,815 | 7.117e+07 | -0.0189 | -1.345e+06 |
| c1 | fisher_transform_signals | 7,020 | 2.59e+07 | -0.01935 | -5.012e+05 |
| c1 | coral_signals | 7,020 | 2.29e+07 | -0.02191 | -5.017e+05 |
| c2 | coral_signals | 7,020 | 2.359e+07 | -0.0244 | -5.755e+05 |
| c1 | center_of_gravity_signals | 7,020 | 2.175e+07 | -0.02618 | -5.694e+05 |
| base | sma_baseline | 18,252 | 3.005e+07 | -0.02827 | -8.495e+05 |
| c2 | center_of_gravity_signals | 7,020 | 2.065e+07 | -0.02911 | -6.011e+05 |
| c2 | fx_sniper_ergodic_cci_signals | 7,020 | 2.072e+07 | -0.02917 | -6.043e+05 |
| c2 | fisher_transform_signals | 7,020 | 2.564e+07 | -0.02934 | -7.523e+05 |
| c2 | hieken_ashi_smoothed_signals | 7,020 | 1.994e+07 | -0.02962 | -5.905e+05 |
| c2 | parabolic_sar_signals | 7,020 | 2.283e+07 | -0.03019 | -6.892e+05 |
| c2 | schaff_trend_cycle_signals | 7,020 | 2.215e+07 | -0.03181 | -7.046e+05 |
| c1 | fx_sniper_ergodic_cci_signals | 7,020 | 2.03e+07 | -0.03188 | -6.473e+05 |
| base | mcginley_dynamic_index | 18,252 | 3.294e+07 | -0.03213 | -1.059e+06 |
| base | ema_baseline | 18,252 | 3.653e+07 | -0.03223 | -1.177e+06 |
| c1 | aroon_signals | 7,020 | 2.003e+07 | -0.03254 | -6.517e+05 |
| vol | volatility_ratio_volume_signals | 22,815 | 8.918e+07 | -0.03309 | -2.951e+06 |
| c1 | parabolic_sar_signals | 7,020 | 2.167e+07 | -0.03443 | -7.462e+05 |
| c2 | bears_bulls_impulse_signals | 7,020 | 1.171e+07 | -0.03451 | -4.041e+05 |
| c1 | bears_bulls_impulse_signals | 7,020 | 2.057e+07 | -0.03489 | -7.179e+05 |
| c1 | relative_vigor_index_signals | 7,020 | 2.065e+07 | -0.03494 | -7.215e+05 |
| c2 | ssl_channel_signals | 7,020 | 2.502e+07 | -0.03565 | -8.921e+05 |
| c1 | polychromatic_momentum_signals | 7,020 | 2.012e+07 | -0.03664 | -7.372e+05 |
| c2 | rex_oscillator_signals | 7,020 | 2.12e+07 | -0.03672 | -7.784e+05 |


## Provenance

| file | rows | md5 |
|---|---|---|
| `results/r2reads/modeB_a2_tuned_vs_default.csv` | 10 | 901324832b34 |
| `results/r2reads/modeB_a1_slots_defaults.csv` | 212 | 23a5ecfd622c |
