# A1 — SLOT MAIN EFFECTS, MODE A

Generated 2026-11-24 00:10 by `code/r2reads.py`, a **pure read** of the gate 2 bank (`win` and `combo`). Nothing was scored and the engine was not run.

**Trade year is the primary unseen record**; the grade year is reported separately as a second independent read. **Significance is on the five yearly values**, not per trade: `t = mean/(sd/sqrt(5))` over the five per-year R-per-trade figures, which is the honest unit for "does this option work across years".


## Does any slot beat its own label-shuffle null?

The null shuffles option labels within the slot across strategies, 50 draws, and takes the BEST option each time — so the p-value is against **best-of-slot**, which is what a reader actually looks at.


**TRADE year**

| slot | n_options | best_option | best_R_per_trade | null_mean | null_p95 | null_max | p_best_of_slot |
|---|---|---|---|---|---|---|---|
| c1 | 3 | bears_bulls_impulse_signals | -0.02322 | -0.03389 | -0.03345 | -0.0332 | 0 |
| c2 | 39 | waddah_attar_explosion_signals | -0.002241 | -0.03037 | -0.02869 | -0.02806 | 0 |
| vol | 12 | williams_vix_fix_volume_signals | 0.01518 | -0.03279 | -0.03198 | -0.0319 | 0 |
| base | 15 | sma_baseline | -0.01817 | -0.03245 | -0.03179 | -0.03076 | 0 |
| exit_ind | 1 | adx_dmi_exit | -0.03433 | -0.03433 | -0.03433 | -0.03433 | 1 |
| c1_x_c2 | 117 | (pair) | 0.01762 | -0.02672 | -0.02433 | -0.0235 | 0 |


**GRADE year**

| slot | n_options | best_option | best_R_per_trade | null_mean | null_p95 | null_max | p_best_of_slot |
|---|---|---|---|---|---|---|---|
| c1 | 3 | bears_bulls_impulse_signals | -0.005302 | -0.02025 | -0.0199 | -0.01946 | 0 |
| c2 | 39 | lemantrend_signals | 0.002935 | -0.01635 | -0.0142 | -0.01332 | 0 |
| vol | 12 | williams_vix_fix_volume_signals | 0.06274 | -0.01902 | -0.01812 | -0.01755 | 0 |
| base | 15 | mcginley_dynamic_index | -0.007583 | -0.01862 | -0.01782 | -0.01742 | 0 |
| exit_ind | 1 | adx_dmi_exit | -0.02073 | -0.02073 | -0.02073 | -0.02073 | 1 |
| c1_x_c2 | 117 | (pair) | 0.05065 | -0.0118 | -0.009789 | -0.009176 | 0 |


**5 of 6 slots clear p<=0.05 on the trade year.**


## Every option, trade year, pooled over the four streams

| slot | option | n_strategies | n_trades | R_per_trade | total_R | years_positive | t_on_5_years | R_2015 | R_2016 | R_2017 | R_2018 | R_2019 | R_2020 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| vol | williams_vix_fix_volume_signals | 1,665 | 7.578e+05 | 0.01518 | 1.15e+04 | 3 | 0.3761 |  | 0.04625 | 0.01105 | 0.124 | -0.07575 | -0.0402 |
| c2 | waddah_attar_explosion_signals | 360 | 4.861e+05 | -0.002241 | -1089 | 2 | -0.1979 |  | 0.009034 | -0.002383 | 0.04222 | -0.06445 | -0.001503 |
| c2 | lemantrend_signals | 540 | 7.177e+05 | -0.003212 | -2305 | 3 | -0.1722 |  | 0.02721 | -0.01101 | 0.02988 | -0.06746 | 0.006103 |
| vol | waddah_attar_explosion_volume_signals | 1,665 | 2.171e+06 | -0.005154 | -1.119e+04 | 3 | -0.2674 |  | 0.003705 | 0.01464 | 0.05362 | -0.09333 | -0.01102 |
| vol | variance_volume_signals | 1,665 | 3.146e+06 | -0.01276 | -4.014e+04 | 2 | -0.719 |  | 0.02601 | -0.04074 | 0.02213 | -0.05822 | -0.009237 |
| c2 | schaff_trend_cycle_signals | 540 | 9.082e+05 | -0.01531 | -1.39e+04 | 2 | -0.5692 |  | 0.0003645 | -0.03081 | 0.0579 | -0.08945 | -0.00599 |
| c2 | parabolic_sar_signals | 540 | 1.154e+06 | -0.01619 | -1.868e+04 | 2 | -0.8672 |  | 0.01257 | -0.03561 | 0.02382 | -0.07142 | -0.004378 |
| c2 | bears_bulls_impulse_signals | 540 | 7.617e+05 | -0.01693 | -1.29e+04 | 1 | -0.8201 |  | -0.004593 | -0.03371 | 0.03853 | -0.08246 | -0.0001964 |
| base | sma_baseline | 1,333 | 1.75e+06 | -0.01817 | -3.179e+04 | 1 | -1.346 |  | -0.01191 | -0.02063 | 0.0155 | -0.06474 | -0.006926 |
| c2 | fx_sniper_ergodic_cci_signals | 540 | 9.583e+05 | -0.0215 | -2.06e+04 | 2 | -0.8034 |  | 0.04769 | -0.02562 | 0.01056 | -0.08555 | -0.03748 |
| c2 | hieken_ashi_smoothed_signals | 540 | 9.393e+05 | -0.02246 | -2.109e+04 | 1 | -0.9234 |  | -0.05884 | -0.02976 | 0.07653 | -0.07514 | -0.03535 |
| c1 | bears_bulls_impulse_signals | 5,960 | 1.049e+07 | -0.02322 | -2.435e+05 | 2 | -1.059 |  | 0.00269 | -0.03458 | 0.03616 | -0.09655 | -0.02432 |
| c2 | aroon_signals | 540 | 1.011e+06 | -0.0238 | -2.407e+04 | 1 | -1.018 |  | -0.01333 | -0.05975 | 0.05578 | -0.07757 | -0.02244 |
| vol | volatility_ratio_volume_signals | 1,665 | 3.307e+06 | -0.02427 | -8.026e+04 | 2 | -1.371 |  | 0.006522 | -0.03172 | 0.022 | -0.07801 | -0.04033 |
| c2 | coral_signals | 540 | 1.115e+06 | -0.02429 | -2.709e+04 | 2 | -1.128 |  | 0.0256 | -0.03169 | 0.02067 | -0.07343 | -0.05194 |
| c2 | center_of_gravity_signals | 540 | 9.408e+05 | -0.0254 | -2.39e+04 | 2 | -1.191 |  | 0.03807 | -0.02976 | 7.686e-05 | -0.0821 | -0.04866 |
| c2 | didi_index_signals | 540 | 8.678e+05 | -0.02556 | -2.218e+04 | 1 | -1.235 |  | -0.05277 | -0.03524 | 0.05228 | -0.08418 | -0.0204 |
| c2 | kuskus_starlight_signals | 540 | 1.117e+06 | -0.02782 | -3.106e+04 | 1 | -1.563 |  | -0.01489 | -0.05631 | 0.02639 | -0.07461 | -0.01821 |
| c2 | ssl_channel_signals | 380 | 8.735e+05 | -0.02789 | -2.436e+04 | 2 | -1.596 |  | 0.01891 | -0.04327 | 0.001298 | -0.07338 | -0.0344 |
| c2 | relative_vigor_index_signals | 540 | 8.633e+05 | -0.02803 | -2.42e+04 | 1 | -2.055 |  | -0.03032 | -0.06674 | 0.01725 | -0.034 | -0.0241 |
| c1 | aroon_signals | 7,020 | 1.441e+07 | -0.0289 | -4.164e+05 | 1 | -1.526 |  | -0.02261 | -0.0583 | 0.03322 | -0.07607 | -0.01975 |
| base | mcginley_dynamic_index | 1,333 | 1.807e+06 | -0.02967 | -5.362e+04 | 1 | -1.585 |  | -0.002847 | -0.02312 | 0.01574 | -0.09266 | -0.04602 |
| c2 | qqe_mod_signals | 540 | 1.047e+06 | -0.02981 | -3.119e+04 | 1 | -1.531 |  | -0.03444 | -0.04514 | 0.03943 | -0.08054 | -0.02882 |
| base | ema_baseline | 1,334 | 1.957e+06 | -0.03016 | -5.902e+04 | 1 | -2.402 |  | -0.02637 | -0.02904 | 0.01048 | -0.0669 | -0.03674 |
| c2 | vortex_signals | 360 | 7.036e+05 | -0.0302 | -2.125e+04 | 1 | -1.607 |  | -0.04977 | -0.03969 | 0.03915 | -0.07762 | -0.02797 |
| c2 | kase_peak_oscillator_signals | 540 | 1.044e+06 | -0.03022 | -3.156e+04 | 1 | -2.465 |  | -0.02613 | -0.05573 | 0.01142 | -0.05392 | -0.0261 |
| base | vidya | 1,333 | 3.022e+06 | -0.03027 | -9.147e+04 | 1 | -1.527 |  | -0.001778 | -0.07377 | 0.02991 | -0.07111 | -0.03623 |
| vol | chaikin_volatility_volume_signals | 1,680 | 3.33e+06 | -0.03103 | -1.033e+05 | 1 | -1.735 |  | -0.01909 | -0.05132 | 0.02391 | -0.08242 | -0.02451 |
| c2 | fisher_transform_signals | 540 | 1.205e+06 | -0.03123 | -3.764e+04 | 1 | -1.872 |  | 0.01394 | -0.04129 | -0.002491 | -0.0756 | -0.04381 |
| vol | choppiness_index_volume_signals | 1,670 | 4.655e+06 | -0.03153 | -1.468e+05 | 1 | -1.885 |  | -0.01994 | -0.0472 | 0.02059 | -0.08245 | -0.03001 |
| vol | ttm_squeeze_volume_signals | 1,665 | 3.526e+06 | -0.03167 | -1.116e+05 | 1 | -2.211 |  | -0.02671 | -0.05969 | 0.015 | -0.06817 | -0.02391 |
| base | wma_baseline | 1,333 | 2.17e+06 | -0.03229 | -7.007e+04 | 1 | -2.262 |  | -0.01171 | -0.03869 | 0.01069 | -0.06798 | -0.05088 |
| base | rma_baseline | 1,333 | 1.707e+06 | -0.03278 | -5.595e+04 | 1 | -1.405 |  | -0.03613 | -0.01167 | 0.03339 | -0.1081 | -0.0388 |
| c2 | ehlers_reverse_ema_signals | 540 | 1.089e+06 | -0.03425 | -3.73e+04 | 1 | -1.598 |  | -0.04523 | -0.04473 | 0.03962 | -0.09814 | -0.02832 |
| exit_ind | adx_dmi_exit | 20,000 | 3.509e+07 | -0.03433 | -1.205e+06 | 1 | -2.002 |  | -0.01587 | -0.05298 | 0.01864 | -0.08118 | -0.03757 |
| c2 | kalman_filter_signals | 540 | 9.636e+05 | -0.03433 | -3.308e+04 | 1 | -2.056 |  | -0.0129 | -0.07289 | 0.01021 | -0.06785 | -0.02221 |
| c2 | coppock_curve_signals | 540 | 9.684e+05 | -0.03456 | -3.347e+04 | 1 | -1.491 |  | -0.0615 | -0.04045 | 0.04958 | -0.09512 | -0.03136 |
| base | alma_baseline | 1,334 | 3.472e+06 | -0.035 | -1.215e+05 | 1 | -1.779 |  | -0.01538 | -0.0726 | 0.02135 | -0.08501 | -0.02221 |
| base | lsma_baseline | 1,333 | 2.508e+06 | -0.0351 | -8.804e+04 | 1 | -1.339 |  | -0.005878 | -0.0731 | 0.05433 | -0.08556 | -0.06548 |
| c2 | volatility_quality_signals | 360 | 7.338e+05 | -0.03525 | -2.587e+04 | 1 | -1.784 |  | -0.009438 | -0.05157 | 0.02372 | -0.09061 | -0.04576 |
| base | t3_baseline | 1,333 | 1.841e+06 | -0.03551 | -6.536e+04 | 2 | -1.857 |  | 0.0035 | -0.06816 | 0.01489 | -0.07147 | -0.04641 |
| base | super_smoother_2pole_baseline | 1,333 | 2.934e+06 | -0.03552 | -1.042e+05 | 1 | -2.107 |  | -0.02637 | -0.06936 | 0.0139 | -0.07152 | -0.01771 |
| base | tma_baseline | 1,333 | 1.675e+06 | -0.0356 | -5.964e+04 | 0 | -2.529 |  | -0.002273 | -0.03572 | -0.01594 | -0.08313 | -0.03612 |
| c2 | trend_direction_force_index_signals | 360 | 3.926e+05 | -0.03656 | -1.435e+04 | 2 | -1.41 |  | -0.07081 | -0.08659 | 0.04542 | -0.07063 | 0.002358 |
| base | hma_baseline | 1,334 | 2.871e+06 | -0.03751 | -1.077e+05 | 1 | -1.694 |  | -0.002964 | -0.07041 | 0.02689 | -0.08277 | -0.04533 |
| base | kama_baseline | 1,333 | 2.125e+06 | -0.0376 | -7.992e+04 | 1 | -1.672 |  | -0.01551 | -0.0509 | 0.02786 | -0.1029 | -0.0378 |
| c2 | donchian_breakout_signals | 540 | 9.998e+05 | -0.03806 | -3.805e+04 | 1 | -1.691 |  | -0.003822 | -0.04073 | 0.02622 | -0.09622 | -0.07508 |
| base | frama_baseline | 1,334 | 2.868e+06 | -0.03829 | -1.098e+05 | 0 | -2.937 |  | -0.01485 | -0.03926 | -0.01041 | -0.0821 | -0.04051 |
| vol | efficiency_ratio_volume_signals | 1,665 | 2.448e+06 | -0.03841 | -9.403e+04 | 0 | -3.184 |  | -0.0292 | -0.0553 | -0.01062 | -0.07374 | -0.01869 |
| vol | damiani_volatmeter_volume_signals | 1,665 | 2.61e+06 | -0.03903 | -1.019e+05 | 1 | -1.284 |  | -0.002993 | -0.03676 | 0.0441 | -0.137 | -0.06162 |
| c2 | rex_oscillator_signals | 540 | 8.904e+05 | -0.03936 | -3.505e+04 | 1 | -1.851 |  | -0.01065 | -0.03821 | 0.01078 | -0.106 | -0.03797 |
| c2 | mama_fama_signals | 540 | 1.03e+06 | -0.03957 | -4.076e+04 | 1 | -2.097 |  | -0.01945 | -0.0614 | 0.01835 | -0.09094 | -0.04097 |
| c2 | chandelier_exit_signals | 540 | 1.068e+06 | -0.04072 | -4.348e+04 | 1 | -2.13 |  | -0.0327 | -0.06793 | 0.02571 | -0.08613 | -0.04215 |
| c2 | linreg_slope_signals | 540 | 7.532e+05 | -0.04094 | -3.084e+04 | 1 | -1.878 |  | -0.05313 | -0.07467 | 0.02687 | -0.09239 | -0.01069 |
| c2 | polychromatic_momentum_signals | 540 | 1.004e+06 | -0.04104 | -4.123e+04 | 1 | -2.012 |  | -0.02748 | -0.06859 | 0.02965 | -0.08368 | -0.04872 |
| vol | mass_index_volume_signals | 1,665 | 4.2e+06 | -0.04374 | -1.837e+05 | 1 | -1.927 |  | -0.03142 | -0.07027 | 0.03565 | -0.07381 | -0.05309 |
| c2 | supertrend_signals | 360 | 7.523e+05 | -0.04452 | -3.35e+04 | 1 | -2.507 |  | -0.03011 | -0.06887 | 0.01853 | -0.07556 | -0.06159 |
| base | fantail_vma | 1,334 | 2.386e+06 | -0.04463 | -1.065e+05 | 1 | -2.627 |  | -0.06167 | -0.0618 | 0.01609 | -0.08625 | -0.03546 |
| c2 | dspo_signals | 540 | 9.799e+05 | -0.04762 | -4.666e+04 | 0 | -3.255 |  | -0.01557 | -0.06679 | -0.00985 | -0.08155 | -0.05952 |
| c2 | adx_dmi_signals | 540 | 6.588e+05 | -0.04832 | -3.183e+04 | 1 | -2.789 |  | -0.01508 | -0.07184 | 0.001902 | -0.08131 | -0.06775 |
| c2 | ichimoku_signals | 540 | 7.077e+05 | -0.05004 | -3.541e+04 | 1 | -3.226 |  | -0.08847 | -0.05848 | 0.004201 | -0.07071 | -0.0413 |
| c2 | j_tpo_signals | 540 | 9.07e+05 | -0.05053 | -4.583e+04 | 0 | -3.652 |  | -0.004677 | -0.06635 | -0.03569 | -0.08319 | -0.05834 |
| c2 | price_momentum_oscillator_signals | 540 | 9.758e+05 | -0.05116 | -4.992e+04 | 0 | -3.249 |  | -0.01034 | -0.07756 | -0.01737 | -0.08601 | -0.06055 |
| c2 | laguerre_filter_signals | 540 | 9.531e+05 | -0.0519 | -4.946e+04 | 0 | -3.821 |  | -0.01862 | -0.06813 | -0.02022 | -0.08417 | -0.06168 |
| c1 | adx_dmi_signals | 7,020 | 1.02e+07 | -0.05341 | -5.447e+05 | 0 | -4.357 |  | -0.02598 | -0.06359 | -0.02028 | -0.0733 | -0.07533 |
| c2 | glitch_index_signals | 540 | 6.081e+05 | -0.05628 | -3.422e+04 | 1 | -2.534 |  | -0.0528 | -0.1025 | 0.01118 | -0.1061 | -0.03072 |
| c2 | dpo_signals | 540 | 1.091e+06 | -0.05636 | -6.149e+04 | 0 | -4.285 |  | -0.02286 | -0.0651 | -0.02695 | -0.08777 | -0.07231 |
| vol | vertical_horizontal_filter_volume_signals | 1,665 | 2.25e+06 | -0.06171 | -1.389e+05 | 0 | -3.794 |  | -0.0671 | -0.1249 | -0.03643 | -0.06114 | -0.02965 |
| c2 | halftrend_signals | 540 | 8.521e+05 | -0.06305 | -5.373e+04 | 1 | -2.781 |  | 0.008934 | -0.1096 | -0.03302 | -0.1056 | -0.07465 |
| vol | fractal_dimension_volume_signals | 1,665 | 2.691e+06 | -0.07592 | -2.043e+05 | 0 | -5.524 |  | -0.04627 | -0.09765 | -0.03623 | -0.09376 | -0.0942 |


## Per stream, trade year — top 10 options by R per trade in each


**trend-routed**

| slot | option | n_strategies | R_per_trade | years_positive | t_on_5_years |
|---|---|---|---|---|---|
| c2 | waddah_attar_explosion_signals | 360 | 0.00092 | 2 | -0.02043 |
| vol | waddah_attar_explosion_volume_signals | 1,665 | -0.006948 | 1 | -0.3921 |
| c2 | lemantrend_signals | 540 | -0.01335 | 2 | -0.5832 |
| c2 | schaff_trend_cycle_signals | 540 | -0.01388 | 3 | -0.5372 |
| vol | williams_vix_fix_volume_signals | 1,665 | -0.0169 | 2 | -0.5864 |
| c2 | aroon_signals | 540 | -0.03019 | 2 | -1.036 |
| c2 | coral_signals | 540 | -0.0304 | 2 | -1.229 |
| c2 | relative_vigor_index_signals | 540 | -0.03084 | 1 | -2.517 |
| c2 | parabolic_sar_signals | 540 | -0.03084 | 2 | -1.443 |
| base | ema_baseline | 1,334 | -0.03225 | 1 | -1.665 |


**trend-allon**

| slot | option | n_strategies | R_per_trade | years_positive | t_on_5_years |
|---|---|---|---|---|---|
| vol | williams_vix_fix_volume_signals | 1,665 | 0.01322 | 3 | 0.5338 |
| c2 | lemantrend_signals | 540 | -0.01067 | 2 | -0.7914 |
| c2 | waddah_attar_explosion_signals | 360 | -0.01218 | 1 | -1.145 |
| vol | waddah_attar_explosion_volume_signals | 1,665 | -0.01257 | 2 | -0.7523 |
| c2 | parabolic_sar_signals | 540 | -0.01995 | 1 | -1.458 |
| c2 | schaff_trend_cycle_signals | 540 | -0.02196 | 1 | -1.156 |
| vol | variance_volume_signals | 1,665 | -0.02225 | 1 | -1.894 |
| c2 | hieken_ashi_smoothed_signals | 540 | -0.02457 | 1 | -1.358 |
| vol | volatility_ratio_volume_signals | 1,665 | -0.02459 | 2 | -1.722 |
| c2 | bears_bulls_impulse_signals | 540 | -0.0259 | 1 | -1.585 |


**chop-routed**

| slot | option | n_strategies | R_per_trade | years_positive | t_on_5_years |
|---|---|---|---|---|---|
| vol | williams_vix_fix_volume_signals | 1,665 | 0.03511 | 2 | 0.5624 |
| c2 | bears_bulls_impulse_signals | 540 | 0.01534 | 4 | 0.8167 |
| vol | variance_volume_signals | 1,665 | 0.007474 | 3 | 0.4026 |
| vol | efficiency_ratio_volume_signals | 1,665 | 0.0001784 | 3 | 0.233 |
| c2 | parabolic_sar_signals | 540 | -0.000631 | 3 | 0.2439 |
| c2 | lemantrend_signals | 540 | -0.006006 | 1 | -0.1868 |
| c2 | waddah_attar_explosion_signals | 360 | -0.006126 | 3 | -0.09283 |
| c2 | center_of_gravity_signals | 540 | -0.006208 | 3 | -0.005557 |
| base | sma_baseline | 1,333 | -0.007594 | 2 | -0.08319 |
| c2 | ssl_channel_signals | 380 | -0.008256 | 3 | -0.01338 |


**chop-allon**

| slot | option | n_strategies | R_per_trade | years_positive | t_on_5_years |
|---|---|---|---|---|---|
| vol | williams_vix_fix_volume_signals | 1,665 | 0.03132 | 3 | 0.7177 |
| c2 | lemantrend_signals | 540 | 0.01688 | 4 | 0.6978 |
| c2 | waddah_attar_explosion_signals | 360 | 0.01394 | 4 | 0.5068 |
| vol | waddah_attar_explosion_volume_signals | 1,665 | 0.01295 | 3 | 0.2994 |
| vol | variance_volume_signals | 1,665 | 0.008624 | 3 | 0.3972 |
| base | sma_baseline | 1,333 | 0.001831 | 3 | 0.1221 |
| c2 | fx_sniper_ergodic_cci_signals | 540 | -0.005081 | 3 | -0.1354 |
| c2 | parabolic_sar_signals | 540 | -0.006802 | 2 | -0.3258 |
| c2 | bears_bulls_impulse_signals | 540 | -0.007012 | 3 | -0.3645 |
| c2 | hieken_ashi_smoothed_signals | 540 | -0.007504 | 1 | -0.3392 |


## Grade year, pooled — the second unseen read

| slot | option | n_strategies | R_per_trade | years_positive | t_on_5_years |
|---|---|---|---|---|---|
| vol | williams_vix_fix_volume_signals | 1,665 | 0.06274 | 4 | 1.135 |
| vol | variance_volume_signals | 1,665 | 0.01615 | 3 | 0.4362 |
| c2 | lemantrend_signals | 540 | 0.002935 | 3 | 0.1171 |
| c2 | fx_sniper_ergodic_cci_signals | 540 | 0.001492 | 3 | 0.1194 |
| vol | waddah_attar_explosion_volume_signals | 1,665 | 0.0003921 | 3 | -0.06376 |
| c2 | center_of_gravity_signals | 540 | -0.002596 | 3 | -0.04534 |
| c2 | parabolic_sar_signals | 540 | -0.004862 | 3 | -0.2078 |
| c1 | bears_bulls_impulse_signals | 5,960 | -0.005302 | 3 | -0.08904 |
| c2 | bears_bulls_impulse_signals | 540 | -0.006398 | 2 | -0.2165 |
| c2 | schaff_trend_cycle_signals | 540 | -0.006629 | 2 | -0.2078 |
| c2 | waddah_attar_explosion_signals | 360 | -0.006955 | 2 | -0.3711 |
| c2 | coral_signals | 540 | -0.006982 | 3 | -0.159 |
| base | mcginley_dynamic_index | 1,333 | -0.007583 | 2 | -0.2883 |
| c2 | fisher_transform_signals | 540 | -0.008799 | 3 | -0.2234 |
| base | sma_baseline | 1,333 | -0.009353 | 2 | -0.3638 |
| c2 | donchian_breakout_signals | 540 | -0.01007 | 2 | -0.3508 |
| c2 | hieken_ashi_smoothed_signals | 540 | -0.01154 | 2 | -0.3853 |
| vol | chaikin_volatility_volume_signals | 1,680 | -0.0129 | 2 | -0.3568 |
| base | ema_baseline | 1,334 | -0.01352 | 2 | -0.5247 |
| base | rma_baseline | 1,333 | -0.01397 | 2 | -0.3817 |
| c1 | aroon_signals | 7,020 | -0.01449 | 2 | -0.5317 |
| base | wma_baseline | 1,333 | -0.01454 | 2 | -0.6863 |
| vol | volatility_ratio_volume_signals | 1,665 | -0.01456 | 2 | -0.6749 |
| c2 | ssl_channel_signals | 380 | -0.01457 | 3 | -0.6663 |
| c2 | aroon_signals | 540 | -0.0154 | 2 | -0.5401 |
| c2 | kuskus_starlight_signals | 540 | -0.01543 | 2 | -0.5174 |
| base | vidya | 1,333 | -0.01662 | 2 | -0.6699 |
| c2 | qqe_mod_signals | 540 | -0.01753 | 2 | -0.6649 |
| c2 | kase_peak_oscillator_signals | 540 | -0.01796 | 2 | -0.8006 |
| c2 | vortex_signals | 360 | -0.01863 | 2 | -0.7314 |


## C1 x C2 — top 30 pairs, trade year

| c1 | c2 | n_strategies | n_trades | R_per_trade | total_R |
|---|---|---|---|---|---|
| bears_bulls_impulse_signals | ssl_channel_signals | 20 | 5.134e+04 | 0.01762 | 904.6 |
| aroon_signals | lemantrend_signals | 180 | 2.559e+05 | 0.01634 | 4181 |
| aroon_signals | waddah_attar_explosion_signals | 180 | 2.517e+05 | 0.01442 | 3629 |
| bears_bulls_impulse_signals | parabolic_sar_signals | 180 | 3.86e+05 | -0.0001418 | -54.75 |
| bears_bulls_impulse_signals | schaff_trend_cycle_signals | 180 | 3.287e+05 | -0.0007204 | -236.8 |
| aroon_signals | bears_bulls_impulse_signals | 180 | 2.42e+05 | -0.002304 | -557.6 |
| bears_bulls_impulse_signals | bears_bulls_impulse_signals | 180 | 3.283e+05 | -0.00315 | -1034 |
| bears_bulls_impulse_signals | coral_signals | 180 | 3.707e+05 | -0.005202 | -1929 |
| aroon_signals | schaff_trend_cycle_signals | 180 | 3.4e+05 | -0.005991 | -2037 |
| aroon_signals | didi_index_signals | 180 | 3.537e+05 | -0.006702 | -2371 |
| bears_bulls_impulse_signals | fx_sniper_ergodic_cci_signals | 180 | 3.777e+05 | -0.007856 | -2967 |
| bears_bulls_impulse_signals | lemantrend_signals | 180 | 2.332e+05 | -0.009869 | -2301 |
| bears_bulls_impulse_signals | aroon_signals | 180 | 3.118e+05 | -0.01009 | -3145 |
| aroon_signals | hieken_ashi_smoothed_signals | 180 | 3.835e+05 | -0.01046 | -4010 |
| bears_bulls_impulse_signals | kuskus_starlight_signals | 180 | 3.614e+05 | -0.01119 | -4043 |
| aroon_signals | parabolic_sar_signals | 180 | 4.172e+05 | -0.01211 | -5054 |
| bears_bulls_impulse_signals | fisher_transform_signals | 180 | 4.197e+05 | -0.01417 | -5946 |
| bears_bulls_impulse_signals | qqe_mod_signals | 180 | 3.292e+05 | -0.01428 | -4702 |
| bears_bulls_impulse_signals | center_of_gravity_signals | 180 | 3.674e+05 | -0.01452 | -5333 |
| aroon_signals | fx_sniper_ergodic_cci_signals | 180 | 3.227e+05 | -0.01535 | -4954 |
| aroon_signals | vortex_signals | 180 | 4.207e+05 | -0.0168 | -7066 |
| aroon_signals | aroon_signals | 180 | 4.859e+05 | -0.01736 | -8434 |
| bears_bulls_impulse_signals | relative_vigor_index_signals | 180 | 2.054e+05 | -0.01759 | -3613 |
| adx_dmi_signals | lemantrend_signals | 180 | 2.287e+05 | -0.0183 | -4185 |
| bears_bulls_impulse_signals | kalman_filter_signals | 180 | 3.448e+05 | -0.0187 | -6449 |
| bears_bulls_impulse_signals | kase_peak_oscillator_signals | 180 | 3.365e+05 | -0.01914 | -6442 |
| aroon_signals | ssl_channel_signals | 180 | 4.506e+05 | -0.0192 | -8652 |
| adx_dmi_signals | waddah_attar_explosion_signals | 180 | 2.343e+05 | -0.02014 | -4719 |
| bears_bulls_impulse_signals | ehlers_reverse_ema_signals | 180 | 3.811e+05 | -0.02069 | -7886 |
| bears_bulls_impulse_signals | hieken_ashi_smoothed_signals | 180 | 2.82e+05 | -0.02108 | -5945 |


## Provenance

| file | rows | md5 |
|---|---|---|
| `results/r2reads/modeA_a1_slots.csv` | 700 | 9d8408e4a359 |
| `results/r2reads/modeA_a1_nulls.csv` | 12 | c69d6132dd27 |
| `results/r2reads/modeA_a1_c1xc2.csv` | 224 | 0336824e6d3c |
