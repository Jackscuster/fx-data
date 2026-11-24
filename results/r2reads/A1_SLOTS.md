# A1 — SLOT MAIN EFFECTS, MODE B

Generated 2026-11-24 00:21 by `code/r2reads.py`, a **pure read** of the gate 2 bank (`win` and `combo`). Nothing was scored and the engine was not run.

**Trade year is the primary unseen record**; the grade year is reported separately as a second independent read. **Significance is on the five yearly values**, not per trade: `t = mean/(sd/sqrt(5))` over the five per-year R-per-trade figures, which is the honest unit for "does this option work across years".


## Does any slot beat its own label-shuffle null?

The null shuffles option labels within the slot across strategies, 1000 draws, and takes the BEST option each time — so the p-value is against **best-of-slot**, which is what a reader actually looks at.


**TRADE year**

| slot | n_options | best_option | best_R_per_trade | null_mean | null_p95 | null_max | p_best_of_slot |
|---|---|---|---|---|---|---|---|
| c1 | 39 | fisher_transform_signals | -0.01953 | -0.03838 | -0.03809 | -0.03749 | 0 |
| c2 | 39 | lemantrend_signals | -0.02008 | -0.03837 | -0.03805 | -0.03776 | 0 |
| vol | 12 | williams_vix_fix_volume_signals | -0.003968 | -0.03884 | -0.03865 | -0.03843 | 0 |
| base | 15 | sma_baseline | -0.02489 | -0.03878 | -0.03857 | -0.03835 | 0 |
| exit_ind | 1 | adx_dmi_exit | -0.03918 | -0.03918 | -0.03918 | -0.03918 | 1 |
| c1_x_c2 | 1,521 | (pair) | 0.03135 | -0.03121 | -0.02964 | -0.02509 | 0 |


**GRADE year**

| slot | n_options | best_option | best_R_per_trade | null_mean | null_p95 | null_max | p_best_of_slot |
|---|---|---|---|---|---|---|---|
| c1 | 39 | bears_bulls_impulse_signals | -0.01144 | -0.02625 | -0.02586 | -0.02543 | 0 |
| c2 | 39 | center_of_gravity_signals | -0.01219 | -0.02627 | -0.02588 | -0.02543 | 0 |
| vol | 12 | williams_vix_fix_volume_signals | 0.03818 | -0.02681 | -0.02659 | -0.02616 | 0 |
| base | 15 | sma_baseline | -0.01442 | -0.02674 | -0.02648 | -0.02616 | 0 |
| exit_ind | 1 | adx_dmi_exit | -0.02721 | -0.02721 | -0.02721 | -0.02721 | 1 |
| c1_x_c2 | 1,521 | (pair) | 0.03732 | -0.0176 | -0.01565 | -0.01261 | 0 |


**5 of 6 slots clear p<=0.05 on the trade year.**


## Every option, trade year, pooled over the four streams

| slot | option | n_strategies | n_trades | R_per_trade | total_R | years_positive | t_on_5_years | R_2015 | R_2016 | R_2017 | R_2018 | R_2019 | R_2020 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| vol | williams_vix_fix_volume_signals | 22,815 | 1.12e+07 | -0.003968 | -4.442e+04 | 3 | -0.1479 |  | 0.01213 | 0.01476 | 0.07138 | -0.03501 | -0.08241 |
| vol | variance_volume_signals | 22,815 | 4.977e+07 | -0.01641 | -8.166e+05 | 2 | -0.9592 |  | 0.02172 | -0.03874 | 0.02441 | -0.06066 | -0.02772 |
| c1 | fisher_transform_signals | 7,020 | 2.052e+07 | -0.01953 | -4.007e+05 | 1 | -1.882 |  | 0.009574 | -0.03818 | -0.001065 | -0.04092 | -0.02369 |
| c2 | lemantrend_signals | 7,020 | 1.14e+07 | -0.02008 | -2.289e+05 | 2 | -1.691 |  | 0.0003122 | -0.02217 | 0.01263 | -0.04364 | -0.04214 |
| c1 | lemantrend_signals | 7,020 | 9.452e+06 | -0.02124 | -2.008e+05 | 2 | -1.518 |  | 0.009004 | -0.03006 | 0.0138 | -0.04609 | -0.04699 |
| vol | waddah_attar_explosion_volume_signals | 22,815 | 3.388e+07 | -0.02132 | -7.222e+05 | 1 | -1.361 |  | -0.01389 | -0.004685 | 0.02408 | -0.06024 | -0.04981 |
| c2 | waddah_attar_explosion_signals | 7,020 | 1.177e+07 | -0.02216 | -2.609e+05 | 1 | -1.783 |  | -0.01253 | -0.01923 | 0.0176 | -0.04247 | -0.04729 |
| c1 | waddah_attar_explosion_signals | 7,020 | 9.561e+06 | -0.02304 | -2.203e+05 | 1 | -1.675 |  | -0.005424 | -0.03214 | 0.02065 | -0.04191 | -0.04997 |
| c2 | coral_signals | 7,020 | 1.714e+07 | -0.02454 | -4.206e+05 | 2 | -1.581 |  | 0.005267 | -0.01944 | 0.01195 | -0.05978 | -0.05793 |
| base | sma_baseline | 18,252 | 2.73e+07 | -0.02489 | -6.793e+05 | 1 | -1.852 |  | -0.03894 | -0.01609 | 0.01422 | -0.06582 | -0.01669 |
| c2 | hieken_ashi_smoothed_signals | 7,020 | 1.621e+07 | -0.02684 | -4.35e+05 | 1 | -1.568 |  | -0.05138 | -0.03023 | 0.03907 | -0.05922 | -0.03479 |
| c2 | parabolic_sar_signals | 7,020 | 1.852e+07 | -0.02728 | -5.054e+05 | 1 | -2.923 |  | -0.02436 | -0.03396 | 0.002133 | -0.05531 | -0.02387 |
| c2 | fisher_transform_signals | 7,020 | 1.975e+07 | -0.02746 | -5.426e+05 | 1 | -2.392 |  | -0.01042 | -0.03373 | 0.007454 | -0.05471 | -0.04405 |
| c1 | coral_signals | 7,020 | 1.731e+07 | -0.02786 | -4.823e+05 | 1 | -2.064 |  | -0.004681 | -0.04165 | 0.0106 | -0.06253 | -0.03885 |
| c1 | center_of_gravity_signals | 7,020 | 1.645e+07 | -0.02788 | -4.587e+05 | 1 | -1.672 |  | -0.007084 | -0.04727 | 0.02464 | -0.06939 | -0.03817 |
| c1 | bears_bulls_impulse_signals | 7,020 | 1.354e+07 | -0.02931 | -3.969e+05 | 1 | -1.91 |  | -0.000922 | -0.03117 | 0.007814 | -0.07447 | -0.04305 |
| c2 | fx_sniper_ergodic_cci_signals | 7,020 | 1.561e+07 | -0.02943 | -4.596e+05 | 1 | -2.165 |  | 0.009283 | -0.03182 | -0.0079 | -0.06227 | -0.04859 |
| c2 | schaff_trend_cycle_signals | 7,020 | 1.51e+07 | -0.02945 | -4.447e+05 | 1 | -2.01 |  | -0.02183 | -0.02999 | 0.01888 | -0.0673 | -0.04114 |
| vol | volatility_ratio_volume_signals | 22,815 | 6.014e+07 | -0.02947 | -1.772e+06 | 1 | -2.377 |  | -0.01336 | -0.02431 | 0.002024 | -0.06989 | -0.04129 |
| c1 | relative_vigor_index_signals | 7,020 | 1.603e+07 | -0.02951 | -4.729e+05 | 1 | -2.284 |  | -0.04571 | -0.05158 | 0.02038 | -0.04054 | -0.03057 |
| c2 | ssl_channel_signals | 7,020 | 1.91e+07 | -0.03011 | -5.75e+05 | 0 | -2.473 |  | -0.004 | -0.03335 | -0.002386 | -0.06484 | -0.04154 |
| c2 | center_of_gravity_signals | 7,020 | 1.579e+07 | -0.03063 | -4.837e+05 | 1 | -2.104 |  | -0.002952 | -0.03349 | 0.00774 | -0.06353 | -0.05892 |
| c1 | polychromatic_momentum_signals | 7,020 | 1.617e+07 | -0.0308 | -4.981e+05 | 1 | -2.064 |  | -0.03926 | -0.05107 | 0.02549 | -0.05536 | -0.03028 |
| c1 | aroon_signals | 7,020 | 1.528e+07 | -0.03084 | -4.712e+05 | 1 | -2.168 |  | -0.03232 | -0.04524 | 0.02267 | -0.0595 | -0.03779 |
| c2 | bears_bulls_impulse_signals | 7,020 | 9.672e+06 | -0.03124 | -3.021e+05 | 1 | -2.773 |  | -0.03655 | -0.02371 | 0.004694 | -0.06523 | -0.03585 |
| c2 | didi_index_signals | 7,020 | 1.478e+07 | -0.03127 | -4.621e+05 | 1 | -2.146 |  | -0.04505 | -0.03479 | 0.01862 | -0.06959 | -0.02471 |
| base | ema_baseline | 18,252 | 3.156e+07 | -0.03151 | -9.944e+05 | 1 | -2.574 |  | -0.05384 | -0.03105 | 0.01391 | -0.05183 | -0.03435 |
| base | mcginley_dynamic_index | 18,252 | 2.908e+07 | -0.03403 | -9.896e+05 | 1 | -1.936 |  | -0.03318 | -0.01772 | 0.01875 | -0.08642 | -0.04958 |
| c1 | dspo_signals | 7,020 | 1.605e+07 | -0.03431 | -5.506e+05 | 0 | -3.268 |  | -0.02237 | -0.03603 | -0.005148 | -0.06763 | -0.03658 |
| c1 | vortex_signals | 7,020 | 1.874e+07 | -0.03442 | -6.45e+05 | 0 | -2.844 |  | -0.02494 | -0.02401 | -0.0009964 | -0.07031 | -0.04551 |
| c1 | parabolic_sar_signals | 7,020 | 1.864e+07 | -0.03468 | -6.464e+05 | 1 | -2.724 |  | -0.024 | -0.04904 | 0.007692 | -0.06653 | -0.03896 |
| c1 | hieken_ashi_smoothed_signals | 7,020 | 1.69e+07 | -0.03499 | -5.915e+05 | 1 | -2.628 |  | -0.04654 | -0.03367 | 0.009982 | -0.07209 | -0.03252 |
| c2 | vortex_signals | 7,020 | 1.81e+07 | -0.0352 | -6.373e+05 | 1 | -2.476 |  | -0.04451 | -0.02994 | 0.01605 | -0.06679 | -0.04731 |
| c2 | relative_vigor_index_signals | 7,020 | 1.41e+07 | -0.03525 | -4.969e+05 | 1 | -3.327 |  | -0.03888 | -0.05898 | 0.004598 | -0.04137 | -0.04143 |
| base | hma_baseline | 18,252 | 4.801e+07 | -0.03569 | -1.713e+06 | 1 | -2.594 |  | -0.005591 | -0.04581 | 0.0002508 | -0.05385 | -0.06307 |
| c1 | fx_sniper_ergodic_cci_signals | 7,020 | 1.596e+07 | -0.03582 | -5.718e+05 | 2 | -2.226 |  | 0.0001767 | -0.06209 | 0.003142 | -0.0704 | -0.04184 |
| c1 | didi_index_signals | 7,020 | 1.429e+07 | -0.0362 | -5.174e+05 | 1 | -2.753 |  | -0.04961 | -0.02503 | 0.004018 | -0.07355 | -0.03327 |
| c2 | volatility_quality_signals | 7,020 | 1.785e+07 | -0.03697 | -6.599e+05 | 1 | -2.705 |  | -0.03015 | -0.03072 | 0.007216 | -0.0714 | -0.05618 |
| vol | chaikin_volatility_volume_signals | 22,815 | 5.254e+07 | -0.03722 | -1.956e+06 | 1 | -3.273 |  | -0.03636 | -0.04527 | 0.004547 | -0.06433 | -0.04586 |
| vol | choppiness_index_volume_signals | 22,815 | 7.805e+07 | -0.03757 | -2.932e+06 | 0 | -3.789 |  | -0.03519 | -0.04225 | -0.005987 | -0.06785 | -0.03556 |
| c1 | mama_fama_signals | 7,020 | 1.738e+07 | -0.03762 | -6.538e+05 | 0 | -4.126 |  | -0.03804 | -0.03836 | -0.004745 | -0.05973 | -0.04508 |
| base | wma_baseline | 18,252 | 3.562e+07 | -0.03792 | -1.351e+06 | 0 | -3.351 |  | -0.04115 | -0.02697 | -0.001496 | -0.06807 | -0.05063 |
| vol | ttm_squeeze_volume_signals | 22,815 | 7.042e+07 | -0.03792 | -2.671e+06 | 0 | -3.976 |  | -0.05138 | -0.04467 | -0.001669 | -0.05736 | -0.03951 |
| c1 | kuskus_starlight_signals | 7,020 | 1.82e+07 | -0.03826 | -6.963e+05 | 1 | -2.904 |  | -0.04273 | -0.04574 | 0.01047 | -0.06806 | -0.0418 |
| c2 | coppock_curve_signals | 7,020 | 1.716e+07 | -0.03833 | -6.576e+05 | 1 | -2.465 |  | -0.05993 | -0.03573 | 0.01783 | -0.0731 | -0.04089 |
| c2 | supertrend_signals | 7,020 | 1.655e+07 | -0.03865 | -6.395e+05 | 1 | -3.096 |  | -0.03164 | -0.0504 | 0.007235 | -0.05838 | -0.05719 |
| c2 | kuskus_starlight_signals | 7,020 | 1.759e+07 | -0.03869 | -6.805e+05 | 1 | -3.169 |  | -0.04479 | -0.05236 | 0.006319 | -0.0654 | -0.03678 |
| c1 | supertrend_signals | 7,020 | 1.543e+07 | -0.0387 | -5.973e+05 | 1 | -3.189 |  | -0.04191 | -0.05327 | 0.00898 | -0.05283 | -0.05217 |
| c2 | rex_oscillator_signals | 7,020 | 1.464e+07 | -0.03909 | -5.724e+05 | 0 | -3.647 |  | -0.01953 | -0.03056 | -0.0155 | -0.07006 | -0.05073 |
| exit_ind | adx_dmi_exit | 273,780 | 5.957e+08 | -0.03918 | -2.334e+07 | 0 | -3.488 |  | -0.0341 | -0.04215 | -0.0005822 | -0.06827 | -0.04728 |
| base | vidya | 18,252 | 5.464e+07 | -0.03924 | -2.144e+06 | 1 | -3.229 |  | -0.04514 | -0.05133 | 0.008736 | -0.05813 | -0.05175 |
| base | alma_baseline | 18,252 | 6.435e+07 | -0.03927 | -2.527e+06 | 0 | -4.452 |  | -0.04256 | -0.05633 | -0.01025 | -0.05703 | -0.02978 |
| c2 | qqe_mod_signals | 7,020 | 1.635e+07 | -0.03934 | -6.433e+05 | 1 | -2.779 |  | -0.04794 | -0.03995 | 0.01092 | -0.07551 | -0.04194 |
| c1 | donchian_breakout_signals | 7,020 | 1.478e+07 | -0.03943 | -5.828e+05 | 0 | -2.9 |  | -0.02663 | -0.02326 | -0.005748 | -0.05996 | -0.0803 |
| c1 | schaff_trend_cycle_signals | 7,020 | 1.251e+07 | -0.03993 | -4.995e+05 | 1 | -2.903 |  | -0.02096 | -0.04986 | 0.003714 | -0.0709 | -0.05609 |
| base | lsma_baseline | 18,252 | 4.61e+07 | -0.03994 | -1.841e+06 | 1 | -2.435 |  | -0.01449 | -0.05569 | 0.01127 | -0.06651 | -0.07269 |
| c2 | kase_peak_oscillator_signals | 7,020 | 1.715e+07 | -0.04021 | -6.895e+05 | 0 | -4.649 |  | -0.04518 | -0.04751 | -0.0083 | -0.05958 | -0.03888 |
| c1 | coppock_curve_signals | 7,020 | 1.701e+07 | -0.04048 | -6.886e+05 | 1 | -3.053 |  | -0.04796 | -0.02409 | 0.001935 | -0.07234 | -0.05481 |
| c2 | donchian_breakout_signals | 7,020 | 1.6e+07 | -0.04067 | -6.508e+05 | 0 | -2.798 |  | -0.02507 | -0.02732 | -0.002017 | -0.07938 | -0.06799 |
| c1 | ssl_channel_signals | 7,020 | 1.808e+07 | -0.04093 | -7.4e+05 | 0 | -3.248 |  | -0.01885 | -0.05129 | -0.002991 | -0.06512 | -0.06046 |
| base | frama_baseline | 18,252 | 4.901e+07 | -0.04098 | -2.008e+06 | 0 | -3.783 |  | -0.01591 | -0.04013 | -0.01751 | -0.06979 | -0.05515 |
| c1 | kalman_filter_signals | 7,020 | 1.746e+07 | -0.04101 | -7.161e+05 | 1 | -3.117 |  | -0.04917 | -0.05448 | 0.01073 | -0.0622 | -0.0494 |
| c2 | ehlers_reverse_ema_signals | 7,020 | 1.752e+07 | -0.04104 | -7.188e+05 | 1 | -2.796 |  | -0.05667 | -0.03429 | 0.009433 | -0.07941 | -0.04455 |
| base | tma_baseline | 18,252 | 2.737e+07 | -0.04133 | -1.131e+06 | 0 | -4.29 |  | -0.03573 | -0.03112 | -0.01898 | -0.07537 | -0.04178 |
| base | kama_baseline | 18,252 | 3.541e+07 | -0.0415 | -1.47e+06 | 1 | -2.85 |  | -0.03449 | -0.04808 | 0.005898 | -0.08433 | -0.04519 |
| base | super_smoother_2pole_baseline | 18,252 | 4.786e+07 | -0.04158 | -1.99e+06 | 0 | -3.948 |  | -0.04441 | -0.05508 | -0.003485 | -0.06397 | -0.03793 |
| c1 | rex_oscillator_signals | 7,020 | 1.781e+07 | -0.04173 | -7.433e+05 | 0 | -3.305 |  | -0.03754 | -0.0235 | -0.02047 | -0.08834 | -0.0337 |
| c2 | kalman_filter_signals | 7,020 | 1.632e+07 | -0.04201 | -6.858e+05 | 0 | -4.162 |  | -0.0435 | -0.05996 | -0.01055 | -0.06388 | -0.02861 |
| base | rma_baseline | 18,252 | 2.752e+07 | -0.04259 | -1.172e+06 | 1 | -2.082 |  | -0.06327 | -0.01309 | 0.01643 | -0.09654 | -0.04787 |
| c2 | polychromatic_momentum_signals | 7,020 | 1.575e+07 | -0.0426 | -6.712e+05 | 1 | -2.783 |  | -0.05169 | -0.05402 | 0.01403 | -0.07575 | -0.04167 |
| c1 | kase_peak_oscillator_signals | 7,020 | 1.679e+07 | -0.04277 | -7.181e+05 | 0 | -4.885 |  | -0.03802 | -0.02828 | -0.02105 | -0.0676 | -0.0558 |
| c1 | ehlers_reverse_ema_signals | 7,020 | 1.69e+07 | -0.04318 | -7.297e+05 | 1 | -2.612 |  | -0.0585 | -0.01067 | 0.002018 | -0.08309 | -0.06179 |
| c2 | aroon_signals | 7,020 | 1.53e+07 | -0.04342 | -6.643e+05 | 1 | -2.815 |  | -0.04605 | -0.05201 | 0.0112 | -0.08294 | -0.04423 |
| c1 | j_tpo_signals | 7,020 | 1.469e+07 | -0.044 | -6.463e+05 | 0 | -4.861 |  | -0.02293 | -0.04939 | -0.02236 | -0.06649 | -0.05667 |
| vol | mass_index_volume_signals | 22,815 | 7.718e+07 | -0.0445 | -3.434e+06 | 0 | -3.674 |  | -0.04545 | -0.04402 | -0.0006536 | -0.07095 | -0.04876 |
| c1 | chandelier_exit_signals | 7,020 | 1.61e+07 | -0.04478 | -7.209e+05 | 1 | -3.546 |  | -0.06457 | -0.05008 | 0.004049 | -0.0639 | -0.0495 |
| c2 | j_tpo_signals | 7,020 | 1.565e+07 | -0.04507 | -7.056e+05 | 0 | -6.463 |  | -0.02237 | -0.04074 | -0.04456 | -0.06473 | -0.05115 |
| vol | efficiency_ratio_volume_signals | 22,815 | 3.606e+07 | -0.04519 | -1.629e+06 | 0 | -4.481 |  | -0.04683 | -0.0462 | -0.01269 | -0.07619 | -0.04347 |
| c2 | mama_fama_signals | 7,020 | 1.675e+07 | -0.04533 | -7.592e+05 | 0 | -4.103 |  | -0.04329 | -0.04609 | -0.00862 | -0.07702 | -0.04786 |
| c1 | adx_dmi_signals | 7,020 | 1.147e+07 | -0.04569 | -5.243e+05 | 0 | -3.605 |  | -0.02515 | -0.0573 | -0.006159 | -0.06521 | -0.06988 |
| base | t3_baseline | 18,252 | 3.05e+07 | -0.0458 | -1.397e+06 | 0 | -3.903 |  | -0.0148 | -0.04032 | -0.027 | -0.07744 | -0.06026 |
| c1 | volatility_quality_signals | 7,020 | 1.675e+07 | -0.04598 | -7.701e+05 | 0 | -4.481 |  | -0.03947 | -0.04866 | -0.00989 | -0.06825 | -0.0598 |
| c2 | linreg_slope_signals | 7,020 | 1.174e+07 | -0.04653 | -5.462e+05 | 0 | -3.88 |  | -0.05869 | -0.0615 | -0.005118 | -0.07372 | -0.03602 |
| c1 | price_momentum_oscillator_signals | 7,020 | 1.5e+07 | -0.04659 | -6.988e+05 | 0 | -6.585 |  | -0.0364 | -0.03638 | -0.03543 | -0.07173 | -0.05132 |
| base | fantail_vma | 18,252 | 4.141e+07 | -0.04663 | -1.931e+06 | 0 | -3.776 |  | -0.03919 | -0.05456 | -0.007138 | -0.08266 | -0.04667 |
| c2 | chandelier_exit_signals | 7,020 | 1.745e+07 | -0.04697 | -8.194e+05 | 1 | -3.711 |  | -0.05812 | -0.05821 | 0.001258 | -0.07254 | -0.04827 |
| c1 | laguerre_filter_signals | 7,020 | 1.416e+07 | -0.04719 | -6.683e+05 | 0 | -4.491 |  | -0.03227 | -0.04478 | -0.02383 | -0.08435 | -0.04779 |
| c1 | qqe_mod_signals | 7,020 | 1.583e+07 | -0.04783 | -7.571e+05 | 0 | -3.701 |  | -0.04651 | -0.04132 | -0.009102 | -0.08826 | -0.04778 |
| c2 | dspo_signals | 7,020 | 1.652e+07 | -0.04852 | -8.014e+05 | 0 | -6.775 |  | -0.03598 | -0.05341 | -0.02859 | -0.06865 | -0.05155 |
| c2 | adx_dmi_signals | 7,020 | 1.106e+07 | -0.04859 | -5.372e+05 | 0 | -4.411 |  | -0.0314 | -0.0544 | -0.0138 | -0.07071 | -0.06437 |
| c2 | trend_direction_force_index_signals | 7,020 | 8.856e+06 | -0.0492 | -4.357e+05 | 1 | -2.578 |  | -0.07993 | -0.05456 | 0.02014 | -0.08311 | -0.04309 |
| c2 | price_momentum_oscillator_signals | 7,020 | 1.558e+07 | -0.04981 | -7.758e+05 | 0 | -5.986 |  | -0.03053 | -0.05572 | -0.03148 | -0.07406 | -0.05284 |
| c1 | linreg_slope_signals | 7,020 | 1.322e+07 | -0.05028 | -6.648e+05 | 0 | -3.91 |  | -0.04686 | -0.0596 | -0.009184 | -0.08863 | -0.04594 |
| c2 | laguerre_filter_signals | 7,020 | 1.57e+07 | -0.05041 | -7.915e+05 | 0 | -6.266 |  | -0.03636 | -0.05003 | -0.03351 | -0.07819 | -0.04978 |
| vol | damiani_volatmeter_volume_signals | 22,815 | 4.452e+07 | -0.05083 | -2.263e+06 | 0 | -2.957 |  | -0.04617 | -0.02969 | -0.004307 | -0.1025 | -0.05863 |
| c1 | dpo_signals | 7,020 | 1.613e+07 | -0.05265 | -8.492e+05 | 0 | -6.195 |  | -0.04416 | -0.04477 | -0.03146 | -0.0808 | -0.05685 |
| c1 | glitch_index_signals | 7,020 | 1.114e+07 | -0.05359 | -5.967e+05 | 1 | -3.437 |  | -0.07653 | -0.05966 | 0.003588 | -0.08786 | -0.05147 |
| c1 | trend_direction_force_index_signals | 7,020 | 1.244e+07 | -0.0542 | -6.74e+05 | 1 | -2.418 |  | -0.115 | -0.04454 | 0.01801 | -0.08762 | -0.0442 |
| c1 | ichimoku_signals | 7,020 | 9.972e+06 | -0.05588 | -5.573e+05 | 0 | -4.065 |  | -0.1031 | -0.03718 | -0.02347 | -0.06609 | -0.04935 |
| vol | vertical_horizontal_filter_volume_signals | 22,815 | 4.329e+07 | -0.05589 | -2.42e+06 | 0 | -5.542 |  | -0.07754 | -0.08478 | -0.02748 | -0.05521 | -0.04541 |
| c2 | dpo_signals | 7,020 | 1.702e+07 | -0.05616 | -9.559e+05 | 0 | -5.933 |  | -0.04085 | -0.0415 | -0.03646 | -0.07951 | -0.07396 |
| c2 | ichimoku_signals | 7,020 | 1.048e+07 | -0.05758 | -6.036e+05 | 0 | -4.225 |  | -0.09921 | -0.034 | -0.02352 | -0.07474 | -0.05753 |
| c2 | halftrend_signals | 7,020 | 1.403e+07 | -0.05871 | -8.238e+05 | 0 | -3.728 |  | -0.01197 | -0.0815 | -0.02981 | -0.08944 | -0.07961 |
| c2 | glitch_index_signals | 7,020 | 9.641e+06 | -0.06153 | -5.932e+05 | 0 | -3.877 |  | -0.07218 | -0.08375 | -0.005822 | -0.09762 | -0.05092 |
| c1 | halftrend_signals | 7,020 | 1.157e+07 | -0.06217 | -7.195e+05 | 0 | -3.784 |  | -0.008833 | -0.08968 | -0.03799 | -0.08825 | -0.08235 |
| vol | fractal_dimension_volume_signals | 22,815 | 3.867e+07 | -0.06923 | -2.677e+06 | 0 | -6.62 |  | -0.06391 | -0.07752 | -0.03076 | -0.07984 | -0.09056 |


## Per stream, trade year — top 10 options by R per trade in each


**trend-routed**

| slot | option | n_strategies | R_per_trade | years_positive | t_on_5_years |
|---|---|---|---|---|---|
| vol | williams_vix_fix_volume_signals | 22,815 | -0.007982 | 1 | -0.5089 |
| vol | variance_volume_signals | 22,815 | -0.01798 | 2 | -0.9758 |
| c1 | lemantrend_signals | 7,020 | -0.02009 | 1 | -1.671 |
| c1 | fisher_transform_signals | 7,020 | -0.02166 | 1 | -1.858 |
| c2 | lemantrend_signals | 7,020 | -0.02261 | 1 | -1.722 |
| c2 | coral_signals | 7,020 | -0.02287 | 1 | -1.938 |
| c1 | waddah_attar_explosion_signals | 7,020 | -0.02319 | 1 | -1.901 |
| c2 | fx_sniper_ergodic_cci_signals | 7,020 | -0.02397 | 1 | -1.93 |
| c2 | schaff_trend_cycle_signals | 7,020 | -0.02432 | 1 | -1.635 |
| base | sma_baseline | 18,252 | -0.02605 | 1 | -1.776 |


**trend-allon**

| slot | option | n_strategies | R_per_trade | years_positive | t_on_5_years |
|---|---|---|---|---|---|
| vol | williams_vix_fix_volume_signals | 22,815 | 0.0008819 | 3 | 0.0476 |
| vol | variance_volume_signals | 22,815 | -0.01495 | 2 | -1.188 |
| vol | waddah_attar_explosion_volume_signals | 22,815 | -0.01697 | 2 | -1.148 |
| c1 | lemantrend_signals | 7,020 | -0.01758 | 2 | -1.515 |
| c2 | lemantrend_signals | 7,020 | -0.01922 | 1 | -2.168 |
| c1 | fisher_transform_signals | 7,020 | -0.01931 | 0 | -2.4 |
| c1 | waddah_attar_explosion_signals | 7,020 | -0.02042 | 1 | -1.781 |
| c2 | waddah_attar_explosion_signals | 7,020 | -0.02184 | 1 | -2.247 |
| c2 | hieken_ashi_smoothed_signals | 7,020 | -0.02235 | 1 | -1.772 |
| c2 | coral_signals | 7,020 | -0.0224 | 1 | -2.241 |


**chop-routed**

| slot | option | n_strategies | R_per_trade | years_positive | t_on_5_years |
|---|---|---|---|---|---|
| c1 | fisher_transform_signals | 7,020 | -0.01527 | 1 | -2.523 |
| c2 | bears_bulls_impulse_signals | 7,020 | -0.01728 | 1 | -1.282 |
| c1 | center_of_gravity_signals | 7,020 | -0.02297 | 2 | -0.7826 |
| c1 | coral_signals | 7,020 | -0.02724 | 2 | -1.252 |
| base | sma_baseline | 18,252 | -0.02751 | 2 | -1.605 |
| vol | waddah_attar_explosion_volume_signals | 22,815 | -0.02753 | 1 | -2.685 |
| vol | variance_volume_signals | 22,815 | -0.02846 | 2 | -1.367 |
| c2 | parabolic_sar_signals | 7,020 | -0.02868 | 0 | -4.224 |
| c1 | polychromatic_momentum_signals | 7,020 | -0.02887 | 1 | -1.442 |
| c1 | bears_bulls_impulse_signals | 7,020 | -0.02921 | 1 | -3.091 |


**chop-allon**

| slot | option | n_strategies | R_per_trade | years_positive | t_on_5_years |
|---|---|---|---|---|---|
| vol | williams_vix_fix_volume_signals | 22,815 | -0.000202 | 3 | -0.01852 |
| vol | waddah_attar_explosion_volume_signals | 22,815 | -0.01074 | 2 | -0.2906 |
| vol | variance_volume_signals | 22,815 | -0.01246 | 2 | -0.5324 |
| c2 | lemantrend_signals | 7,020 | -0.01435 | 2 | -0.5599 |
| c2 | waddah_attar_explosion_signals | 7,020 | -0.01467 | 3 | -0.4936 |
| c1 | lemantrend_signals | 7,020 | -0.01827 | 2 | -0.6836 |
| c1 | waddah_attar_explosion_signals | 7,020 | -0.01969 | 2 | -0.6889 |
| c1 | fisher_transform_signals | 7,020 | -0.0206 | 2 | -1.119 |
| c2 | hieken_ashi_smoothed_signals | 7,020 | -0.02278 | 1 | -0.9539 |
| c1 | bears_bulls_impulse_signals | 7,020 | -0.02331 | 2 | -0.8558 |


## Grade year, pooled — the second unseen read

| slot | option | n_strategies | R_per_trade | years_positive | t_on_5_years |
|---|---|---|---|---|---|
| vol | williams_vix_fix_volume_signals | 22,815 | 0.03818 | 4 | 1.366 |
| vol | variance_volume_signals | 22,815 | 0.008674 | 3 | 0.2528 |
| c1 | bears_bulls_impulse_signals | 7,020 | -0.01144 | 3 | -0.4734 |
| c2 | center_of_gravity_signals | 7,020 | -0.01219 | 2 | -0.5572 |
| c2 | fx_sniper_ergodic_cci_signals | 7,020 | -0.01232 | 2 | -0.5486 |
| c2 | lemantrend_signals | 7,020 | -0.01258 | 1 | -1.011 |
| vol | chaikin_volatility_volume_signals | 22,815 | -0.01278 | 2 | -0.5206 |
| c2 | ssl_channel_signals | 7,020 | -0.01318 | 2 | -0.5739 |
| c2 | coral_signals | 7,020 | -0.0133 | 2 | -0.7558 |
| vol | waddah_attar_explosion_volume_signals | 22,815 | -0.01336 | 2 | -0.8445 |
| c2 | waddah_attar_explosion_signals | 7,020 | -0.01356 | 1 | -1.109 |
| c1 | waddah_attar_explosion_signals | 7,020 | -0.01363 | 1 | -1.03 |
| c1 | center_of_gravity_signals | 7,020 | -0.01424 | 2 | -0.5572 |
| c1 | lemantrend_signals | 7,020 | -0.01441 | 1 | -1.034 |
| base | sma_baseline | 18,252 | -0.01442 | 2 | -0.5705 |
| c2 | fisher_transform_signals | 7,020 | -0.01468 | 2 | -0.7489 |
| c1 | fisher_transform_signals | 7,020 | -0.01494 | 3 | -1.09 |
| c1 | donchian_breakout_signals | 7,020 | -0.01544 | 2 | -0.9538 |
| c2 | parabolic_sar_signals | 7,020 | -0.01639 | 2 | -0.868 |
| c2 | schaff_trend_cycle_signals | 7,020 | -0.01704 | 2 | -0.8983 |
| c2 | donchian_breakout_signals | 7,020 | -0.01716 | 2 | -0.8334 |
| base | ema_baseline | 18,252 | -0.01733 | 2 | -0.7267 |
| c2 | supertrend_signals | 7,020 | -0.01884 | 2 | -0.7998 |
| c1 | aroon_signals | 7,020 | -0.01885 | 2 | -1.099 |
| c1 | schaff_trend_cycle_signals | 7,020 | -0.01911 | 2 | -0.9125 |
| base | mcginley_dynamic_index | 18,252 | -0.01914 | 2 | -0.699 |
| base | rma_baseline | 18,252 | -0.01966 | 2 | -0.5381 |
| c2 | bears_bulls_impulse_signals | 7,020 | -0.01983 | 2 | -0.9819 |
| c1 | relative_vigor_index_signals | 7,020 | -0.02027 | 2 | -1.274 |
| c1 | polychromatic_momentum_signals | 7,020 | -0.02059 | 2 | -1.043 |


## C1 x C2 — top 30 pairs, trade year

| c1 | c2 | n_strategies | n_trades | R_per_trade | total_R |
|---|---|---|---|---|---|
| lemantrend_signals | hieken_ashi_smoothed_signals | 180 | 2.492e+05 | 0.03135 | 7813 |
| waddah_attar_explosion_signals | hieken_ashi_smoothed_signals | 180 | 2.527e+05 | 0.02705 | 6836 |
| aroon_signals | lemantrend_signals | 180 | 2.491e+05 | 0.01678 | 4180 |
| aroon_signals | waddah_attar_explosion_signals | 180 | 2.264e+05 | 0.0129 | 2920 |
| trend_direction_force_index_signals | lemantrend_signals | 180 | 1.738e+05 | 0.01075 | 1868 |
| lemantrend_signals | vortex_signals | 180 | 2.458e+05 | 0.002634 | 647.4 |
| dspo_signals | bears_bulls_impulse_signals | 180 | 2.147e+05 | 0.001634 | 350.7 |
| trend_direction_force_index_signals | waddah_attar_explosion_signals | 180 | 1.894e+05 | 0.001511 | 286.2 |
| lemantrend_signals | relative_vigor_index_signals | 180 | 2.699e+05 | 0.001039 | 280.4 |
| lemantrend_signals | didi_index_signals | 180 | 1.909e+05 | 0.0005926 | 113.1 |
| rex_oscillator_signals | hieken_ashi_smoothed_signals | 180 | 4.317e+05 | 0.0004775 | 206.1 |
| waddah_attar_explosion_signals | relative_vigor_index_signals | 180 | 2.78e+05 | -0.001732 | -481.5 |
| waddah_attar_explosion_signals | vortex_signals | 180 | 2.43e+05 | -0.002147 | -521.8 |
| lemantrend_signals | volatility_quality_signals | 180 | 2.9e+05 | -0.002651 | -768.8 |
| waddah_attar_explosion_signals | trend_direction_force_index_signals | 180 | 1.713e+05 | -0.003187 | -545.8 |
| waddah_attar_explosion_signals | didi_index_signals | 180 | 2.003e+05 | -0.003773 | -755.6 |
| lemantrend_signals | aroon_signals | 180 | 1.965e+05 | -0.003871 | -760.7 |
| relative_vigor_index_signals | waddah_attar_explosion_signals | 180 | 3.547e+05 | -0.003926 | -1393 |
| lemantrend_signals | donchian_breakout_signals | 180 | 1.981e+05 | -0.003969 | -786.3 |
| aroon_signals | bears_bulls_impulse_signals | 180 | 2.508e+05 | -0.004065 | -1020 |
| coppock_curve_signals | waddah_attar_explosion_signals | 180 | 2.155e+05 | -0.004426 | -953.6 |
| waddah_attar_explosion_signals | coppock_curve_signals | 180 | 1.783e+05 | -0.004687 | -835.8 |
| lemantrend_signals | trend_direction_force_index_signals | 180 | 1.79e+05 | -0.004875 | -872.4 |
| waddah_attar_explosion_signals | volatility_quality_signals | 180 | 2.866e+05 | -0.004935 | -1414 |
| hieken_ashi_smoothed_signals | waddah_attar_explosion_signals | 180 | 3.209e+05 | -0.005034 | -1615 |
| didi_index_signals | hieken_ashi_smoothed_signals | 180 | 4.081e+05 | -0.005071 | -2069 |
| hieken_ashi_smoothed_signals | lemantrend_signals | 180 | 3.168e+05 | -0.005223 | -1655 |
| fisher_transform_signals | relative_vigor_index_signals | 180 | 4.834e+05 | -0.005329 | -2576 |
| center_of_gravity_signals | schaff_trend_cycle_signals | 180 | 5.037e+05 | -0.005379 | -2710 |
| lemantrend_signals | coppock_curve_signals | 180 | 1.759e+05 | -0.005811 | -1022 |


## Provenance

| file | rows | md5 |
|---|---|---|
| `results/r2reads/modeB_a1_slots.csv` | 1,060 | 09a005a1f40a |
| `results/r2reads/modeB_a1_nulls.csv` | 12 | 408e295fec72 |
| `results/r2reads/modeB_a1_c1xc2.csv` | 3,042 | 6ad23e2631f1 |
