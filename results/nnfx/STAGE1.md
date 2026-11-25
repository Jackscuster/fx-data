<!-- SUPERSEDED 2026-11-24 by results/nnfx/STAGE1_R2.md.

ALSO: THREE OF THE CSVs THIS FILE NAMES NO LONGER BACK ITS NUMBERS.
Found by pre-flight guard 35 on 24 Nov at 21:30. The provenance block
below names stage1_c1_canonical_risk_yearly.csv at 1,929 rows,
_summary.csv at 117 and _nulls.csv at 23,400. The files on disk hold
99, 6 and 360: they were overwritten at 13:08 on 24 Nov by a smaller
run that reused the production filenames. The full canonical_risk
numbers quoted in this file are therefore NOT reproducible from disk.
Do not re-derive anything from them. The live record is the R2 run,
which writes under the stage1r2_ prefix and whose 18 provenance lines
all match -- and the three C1 picks and the three baselines Jack chose
were read off STAGE1_R2.md, not off this file. The baseline-side
canonical_risk csvs (stage1_base_*) are intact and still match.

Jack read this file and found three faults. All three were real:

1. NO COST WAS CHARGED ON THE FLIP-ONLY VARIANT. R was restated against the
   1.5 ATR risk unit and the cost was not, so with a 2000 ATR sentinel stop the
   charge came out 2000 times too small -- +0.00001 R per trade instead of
   +0.018. Every flip-only figure in this file is GROSS of costs.

2. THE WORST DIP WAS NOT A DRAWDOWN. It was computed from six yearly sums, so
   it equalled minus the worst year on 56 of 117 rows and was exactly 0 on four
   more. The true chronological drawdown on the daily mark-to-market series is
   two to three times larger: 384 R against 115 R on one candidate.

3. AMBIGUOUS BARS WERE RESOLVED STOP-FIRST. Every bar whose daily range covered
   both the stop and the target was filled as a stop, where A5 had measured the
   target first on 40 per cent of such days.

And a fourth fault, mine, which Jack's zero-edge check exposed: the random-entry
null was computed over the WHOLE span 2005-2020 while the summary divided its
total by the six-year BUILD trade count, a factor of 2.607. That made every
null_p in this file meaningless, because a six-year real total was being
compared against a sixteen-year null total.

STAGE1_R2.md replaces it with costs charged in a declared notional, true
chronological drawdowns, hourly-resolved ambiguous bars, eleven unseen years for
the fixed settings, three declared risk plans, a block-bootstrap t beside the
yearly t, and luck floors computed from the random-entry null rather than from a
formula. Read that instead.
-->

# STAGE 1 — ONE PIECE ALONE, WALK-FORWARD

Generated 2026-11-24 12:31 by `code/nnfx1.py`. HANDOFF 0m.


**NO SELECTION BY ME.** Every one of the 39 C1 indicators and all 15 baselines is reported. Jack picks at most 3 of each, for a stated reason. All 54 are in `CANDIDATE_LEDGER.csv`, which is what the luck floors are computed from.


## How it was run

- **The shipped engine, not a second one.** 0b cost this project a winner list because two scorers held two undeclared conventions, so stage 1 runs `l2engine` and neutralises the slots it is not testing. "C1 alone" = C2 and volume agreement forced True, the exit indicator off, continuation off, the one-candle rule off, `bridge_bars` and `max_atr_dist` set so they can never block.

- **One direction at a time.** `agree_long` is `c1_lc and c2_lc and v_ok_l and side == 1` (`l2engine.py:441`) — the baseline SIDE is inside the agreement. So the long side runs with the baseline far below the close and the short side far above it, and the two trade sets are concatenated. The exit needs neither side nor agreement (`l2engine.py:414`), so each one-sided run still exits on the opposite flip. **My first attempt set the baseline equal to the close and took 0 trades, which is how this was found.**

- **Both variants in the same R unit: R per 1.5 ATR**, the canonical stop. Engine `r` scales as `1/atr_mult`, so everything is restated as `r × atr_mult / 1.5`. Without it the no-stop and 1.5-ATR variants could not be compared.

- **`flip_only` is checked to BE flip-only.** The stop sentinel is 2000 ATR, and `run_one` asserts no trade exited by stop, target, breakeven or trail. 50 ATR was not enough (two AUDJPY longs held 345 bars in 2008); 200 was not enough (one EURCHF baseline trade, the 2015 SNB de-peg). At 2000 there is not one risk-plan exit anywhere.

- **Three settings per indicator**: half, default and double the length. Five C1 indicators are parameterised by a smoothing CONSTANT instead, where a larger constant means a shorter memory, so for those "half length" doubles the constant — the opposite direction, stated because it is easy to get backwards. Two baselines default to length 2, where half is also 2, so they have two distinct settings not three.

- **The walk-forward pick**: each step chooses the setting on its four tuning years and is judged only on that step's unseen trade year. **BUILD = unseen trade years 2010-2015, reported below. CONFIRM = unseen trade years 2016-2020, computed and stored in the same files and NOT shown.** 2021 onward never touched.


## The headline

| family | variant | candidates | R_build_positive | median_t | max_t | floor_alone | floor_best_of_family | clear_alone | clear_best_of_family |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| C1 (39) | flip_only | 39 | 15 | -0.087 | 1.545 | 2.015 | 5.541 | 0 | 0 |
| C1 (39) | canonical_risk | 39 | 18 | -0.033 | 1.254 | 2.015 | 5.541 | 0 | 0 |
| baseline (15) | flip_only | 15 | 7 | -0.004 | 2.136 | 2.015 | 4.430 | 1 | 0 |
| baseline (15) | canonical_risk | 15 | 6 | -0.371 | 0.387 | 2.015 | 4.430 | 0 | 0 |


**Not one of the 39 C1 indicators clears even the single-candidate floor, in either variant.** The baselines manage one, under `flip_only` only. Against the honest best-of-family floor — t 5.54 for 39 candidates on six yearly observations, t 4.43 for 15 — **nothing clears anything.**


0a already said this would happen: at six yearly observations the best-of-39 floor is higher than the old best-of-273,780 floor was, and a genuine 0.20 R per trade edge would clear it only 6% of the time. **So "nothing clears the floor" is close to uninformative here. The informative part is the ranking, the stability across settings, and the selection test below.**


---


# C1 — all 39 candidates


## C1 — flip_only, walk-forward pick, BUILD years 2010-2015

`n_settings_used` is how many different settings the six steps chose. A candidate whose steps keep switching setting is being fitted, not measured.

| indicator | R_net_build | n | R_per_trade | trades_per_year | mean_bars | years_positive | worst_year | best_year | worst_dip_R | t_yearly | settings_used | n_settings_used | clears_alone | clears_best_of_family |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|
| schaff_trend_cycle_signals | 174.9589 | 3212.0000 | 0.0545 | 535.3333 | 14.6627 | 5 | -20.2279 | 114.4127 | 20.2279 | 1.5451 | default,half | 2 | 0 | 0 |
| fisher_transform_signals | 166.9824 | 21706.0000 | 0.0077 | 3617.6667 | 4.0304 | 5 | -72.5672 | 89.0502 | 0.0000 | 1.1308 | default,double,half | 3 | 0 | 0 |
| j_tpo_signals | 153.5286 | 1636.0000 | 0.0938 | 272.6667 | 68.7801 | 4 | -70.6625 | 134.3043 | 75.9305 | 0.9310 | double,half | 2 | 0 | 0 |
| laguerre_filter_signals | 103.8781 | 2870.0000 | 0.0362 | 478.3333 | 43.1819 | 4 | -132.5803 | 89.5280 | 132.5803 | 0.5199 | default,double,half | 3 | 0 | 0 |
| lemantrend_signals | 97.9756 | 2396.0000 | 0.0409 | 399.3333 | 38.9925 | 3 | -79.2718 | 150.7400 | 89.3477 | 0.4656 | default,double,half | 3 | 0 | 0 |
| parabolic_sar_signals | 97.9663 | 9312.0000 | 0.0105 | 1552.0000 | 9.5818 | 5 | -63.2904 | 118.2998 | 0.0000 | 0.6841 | default,half | 2 | 0 | 0 |
| fx_sniper_ergodic_cci_signals | 92.8428 | 13856.0000 | 0.0067 | 2309.3333 | 6.3758 | 3 | -79.4462 | 125.2496 | 37.6663 | 0.5081 | default,half | 2 | 0 | 0 |
| relative_vigor_index_signals | 69.1459 | 15452.0000 | 0.0045 | 2575.3333 | 5.6627 | 2 | -51.6909 | 118.6090 | 101.1791 | 0.4354 | default,double,half | 3 | 0 | 0 |
| waddah_attar_explosion_signals | 68.2189 | 1786.0000 | 0.0382 | 297.6667 | 48.9950 | 3 | -93.6532 | 135.2744 | 102.8652 | 0.3581 | default,double,half | 3 | 0 | 0 |
| volatility_quality_signals | 55.3526 | 5612.0000 | 0.0099 | 935.3333 | 22.7662 | 4 | -104.8137 | 85.1273 | 104.8137 | 0.3299 | default,double,half | 3 | 0 | 0 |
| trend_direction_force_index_signals | 50.0569 | 1974.0000 | 0.0254 | 329.0000 | 65.2019 | 4 | -79.5692 | 73.3120 | 118.1874 | 0.3621 | double,half | 2 | 0 | 0 |
| dspo_signals | 44.6948 | 2630.0000 | 0.0170 | 438.3333 | 46.0966 | 4 | -77.1974 | 58.8862 | 97.7752 | 0.3743 | double,half | 2 | 0 | 0 |
| linreg_slope_signals | 36.6165 | 3538.0000 | 0.0103 | 589.6667 | 31.5855 | 4 | -148.5717 | 77.8557 | 148.5717 | 0.1723 | default,double,half | 3 | 0 | 0 |
| halftrend_signals | 30.8029 | 600.0000 | 0.0513 | 100.0000 | 160.0373 | 2 | -83.2623 | 131.9627 | 110.3300 | 0.1690 | double,half | 2 | 0 | 0 |
| aroon_signals | 15.2272 | 4254.0000 | 0.0036 | 709.0000 | 24.6595 | 4 | -150.0792 | 84.1011 | 150.0792 | 0.0737 | default,double,half | 3 | 0 | 0 |
| ichimoku_signals | -5.2834 | 826.0000 | -0.0064 | 137.6667 | 112.6882 | 3 | -77.2063 | 53.9560 | 154.9767 | -0.0352 | default,double,half | 3 | 0 | 0 |
| didi_index_signals | -8.5671 | 5924.0000 | -0.0014 | 987.3333 | 14.6977 | 3 | -94.1124 | 49.0206 | 94.1124 | -0.0648 | double,half | 2 | 0 | 0 |
| donchian_breakout_signals | -10.2765 | 2130.0000 | -0.0048 | 355.0000 | 50.8338 | 4 | -154.0200 | 101.5274 | 163.2853 | -0.0473 | default,double,half | 3 | 0 | 0 |
| ssl_channel_signals | -12.5943 | 6520.0000 | -0.0019 | 1086.6667 | 14.3039 | 3 | -88.1489 | 49.3064 | 88.1489 | -0.0865 | default,double,half | 3 | 0 | 0 |
| kuskus_starlight_signals | -13.2847 | 4936.0000 | -0.0027 | 822.6667 | 19.7099 | 4 | -106.0218 | 82.2355 | 106.0218 | -0.0806 | default,double,half | 3 | 0 | 0 |
| price_momentum_oscillator_signals | -21.9818 | 1784.0000 | -0.0123 | 297.3333 | 53.2686 | 3 | -109.5542 | 97.3959 | 130.4460 | -0.1340 | double,half | 2 | 0 | 0 |
| supertrend_signals | -23.2183 | 2182.0000 | -0.0106 | 363.6667 | 39.4354 | 3 | -65.1711 | 59.4676 | 65.1711 | -0.2265 | default,double | 2 | 0 | 0 |
| dpo_signals | -26.6565 | 4240.0000 | -0.0063 | 706.6667 | 20.9014 | 3 | -100.7891 | 93.2383 | 100.7891 | -0.1709 | default,double,half | 3 | 0 | 0 |
| chandelier_exit_signals | -46.8051 | 2998.0000 | -0.0156 | 499.6667 | 30.3645 | 2 | -55.6400 | 52.1327 | 55.6400 | -0.4331 | default,double,half | 3 | 0 | 0 |
| coral_signals | -53.0942 | 24050.0000 | -0.0022 | 4008.3333 | 4.0277 | 3 | -105.5194 | 100.6204 | 123.8543 | -0.2710 | default,half | 2 | 0 | 0 |
| kase_peak_oscillator_signals | -66.9047 | 4214.0000 | -0.0159 | 702.3333 | 21.3889 | 3 | -108.7053 | 80.3709 | 118.6956 | -0.3871 | default,double,half | 3 | 0 | 0 |
| hieken_ashi_smoothed_signals | -74.3712 | 4920.0000 | -0.0151 | 820.0000 | 19.4945 | 3 | -199.0990 | 85.6875 | 199.0990 | -0.2954 | double,half | 2 | 0 | 0 |
| kalman_filter_signals | -86.8459 | 3780.0000 | -0.0230 | 630.0000 | 23.3158 | 3 | -158.7152 | 80.9034 | 158.7152 | -0.4220 | default,half | 2 | 0 | 0 |
| polychromatic_momentum_signals | -87.1693 | 3746.0000 | -0.0233 | 624.3333 | 26.6915 | 3 | -119.5227 | 50.6606 | 119.5227 | -0.5910 | default,double,half | 3 | 0 | 0 |
| glitch_index_signals | -104.0232 | 2048.0000 | -0.0508 | 341.3333 | 44.8639 | 3 | -144.5383 | 41.2199 | 144.5383 | -0.6070 | default,double,half | 3 | 0 | 0 |
| bears_bulls_impulse_signals | -109.5637 | 4418.0000 | -0.0248 | 736.3333 | 19.6567 | 2 | -126.5197 | 56.6338 | 126.5197 | -0.6577 | double,half | 2 | 0 | 0 |
| ehlers_reverse_ema_signals | -112.1569 | 4050.0000 | -0.0277 | 675.0000 | 21.8071 | 4 | -143.9145 | 43.3341 | 143.9145 | -0.6416 | default,double,half | 3 | 0 | 0 |
| rex_oscillator_signals | -122.8703 | 16122.0000 | -0.0076 | 2687.0000 | 5.4334 | 3 | -101.2975 | 41.1633 | 164.6025 | -0.8386 | default,half | 2 | 0 | 0 |
| qqe_mod_signals | -123.5662 | 4880.0000 | -0.0253 | 813.3333 | 18.8715 | 2 | -136.0668 | 51.4160 | 136.0668 | -0.8028 | default,double,half | 3 | 0 | 0 |
| mama_fama_signals | -125.6053 | 4238.0000 | -0.0296 | 706.3333 | 31.5200 | 3 | -142.9878 | 33.0071 | 142.9878 | -0.8263 | default,double,half | 3 | 0 | 0 |
| coppock_curve_signals | -149.1405 | 4122.0000 | -0.0362 | 687.0000 | 22.4516 | 2 | -135.0676 | 47.5700 | 135.0676 | -0.9894 | double,half | 2 | 0 | 0 |
| center_of_gravity_signals | -210.2945 | 20228.0000 | -0.0104 | 3371.3333 | 4.5397 | 2 | -103.0563 | 42.7384 | 155.3552 | -1.4438 | default,half | 2 | 0 | 0 |
| vortex_signals | -260.1391 | 7278.0000 | -0.0357 | 1213.0000 | 12.2305 | 2 | -188.4583 | 41.0820 | 203.0578 | -1.2960 | default,double | 2 | 0 | 0 |
| adx_dmi_signals | -305.2078 | 3958.0000 | -0.0771 | 659.6667 | 253.1822 | 0 | -81.7946 | -20.7027 | 232.4263 | -4.8239 | default,double,half | 3 | 0 | 0 |


### C1 — flip_only, ALL THREE SETTINGS UNPICKED

The same six BUILD years with each setting held fixed, so the walk-forward number above can be compared with what any single setting would have done. `null_p` is against the matched random-entry null, 200 draws, matched on trade count and holding period per pair.

| indicator | setting | distinct_setting | params | n | trades_per_year | mean_bars | R_gross_build | R_net_build | R_per_trade_net | years_positive | worst_year | worst_dip_R | t_yearly | null_p | null_p95 | straddles |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| adx_dmi_signals | default | 1 | {} | 752 | 125.3333 | 121.5718 | -148.3933 | -148.3995 | -0.1973 | 1 | -81.7946 | 142.7308 | -1.8870 | 0.8100 | 412.4558 | 274 |
| adx_dmi_signals | double | 1 | {"di_length": 28} | 46 | 7.6667 | 772.6957 | 7.2731 | 7.2728 | 0.1581 | 4 | -62.1810 | 80.0740 | 0.0731 | 0.5950 | 192.8767 | 34 |
| adx_dmi_signals | half | 1 | {"di_length": 7} | 7340 | 1223.3333 | 11.8728 | -57.7777 | -57.8420 | -0.0079 | 3 | -72.7815 | 67.7481 | -0.5073 | 0.5750 | 457.2091 | 336 |
| aroon_signals | default | 1 | {} | 3540 | 590.0000 | 24.5910 | -219.5519 | -219.5852 | -0.0620 | 2 | -150.0792 | 194.9756 | -1.2504 | 0.8100 | 424.2404 | 336 |
| aroon_signals | double | 1 | {"length": 50} | 1802 | 300.3333 | 47.7558 | -191.5523 | -191.5693 | -0.1063 | 2 | -96.5929 | 94.9765 | -1.3824 | 0.8000 | 398.5956 | 336 |
| aroon_signals | half | 1 | {"length": 12} | 6436 | 1072.6667 | 13.5174 | 218.8303 | 218.7708 | 0.0340 | 5 | -102.5711 | 102.5711 | 1.0773 | 0.2050 | 402.6190 | 336 |
| bears_bulls_impulse_signals | default | 1 | {} | 5398 | 899.6667 | 16.0900 | -20.9685 | -21.0165 | -0.0039 | 3 | -107.3698 | 107.3698 | -0.1517 | 0.5750 | 405.8416 | 336 |
| bears_bulls_impulse_signals | double | 1 | {"length": 26} | 4158 | 693.0000 | 20.8124 | -37.8568 | -37.8940 | -0.0091 | 3 | -126.5197 | 126.5197 | -0.2070 | 0.6150 | 464.0023 | 336 |
| bears_bulls_impulse_signals | half | 1 | {"length": 6} | 5696 | 949.3333 | 15.2370 | 12.7895 | 12.7392 | 0.0022 | 3 | -46.3976 | 46.3976 | 0.1543 | 0.4600 | 352.5042 | 336 |
| center_of_gravity_signals | default | 1 | {} | 15856 | 2642.6667 | 5.4970 | -156.9049 | -157.0521 | -0.0099 | 2 | -92.8924 | 216.4695 | -0.7626 | 0.7450 | 379.6833 | 336 |
| center_of_gravity_signals | double | 1 | {"length": 20} | 10346 | 1724.3333 | 8.4261 | 113.9927 | 113.8972 | 0.0110 | 4 | -16.2696 | 15.6206 | 0.9560 | 0.2600 | 332.0450 | 336 |
| center_of_gravity_signals | half | 1 | {"length": 5} | 24842 | 4140.3333 | 3.5156 | -288.5768 | -288.8054 | -0.0116 | 1 | -197.7708 | 228.4875 | -1.3476 | 0.8850 | 427.2148 | 336 |
| chandelier_exit_signals | default | 1 | {} | 2842 | 473.6667 | 30.5693 | -37.5350 | -37.5591 | -0.0132 | 2 | -61.4708 | 61.4708 | -0.3089 | 0.6150 | 400.7029 | 336 |
| chandelier_exit_signals | double | 1 | {"atr_period": 44} | 3876 | 646.0000 | 22.3323 | -18.4557 | -18.4877 | -0.0048 | 3 | -69.9151 | 69.9151 | -0.1338 | 0.5350 | 407.6749 | 336 |
| chandelier_exit_signals | half | 1 | {"atr_period": 11} | 2636 | 439.3333 | 32.9605 | -58.9241 | -58.9472 | -0.0224 | 2 | -55.6400 | 55.6400 | -0.6136 | 0.5950 | 372.0355 | 336 |
| coppock_curve_signals | default | 1 | {} | 4392 | 732.0000 | 19.7987 | -46.8649 | -46.9060 | -0.0107 | 3 | -113.3387 | 113.3387 | -0.2965 | 0.5500 | 423.1490 | 336 |
| coppock_curve_signals | double | 1 | {"smooth_len": 20} | 3366 | 561.0000 | 25.8069 | -205.5633 | -205.5949 | -0.0611 | 2 | -135.0676 | 167.6472 | -1.2724 | 0.8350 | 409.8609 | 336 |
| coppock_curve_signals | half | 1 | {"smooth_len": 5} | 5424 | 904.0000 | 16.0678 | -10.5364 | -10.5867 | -0.0020 | 3 | -92.0217 | 92.0217 | -0.0792 | 0.5250 | 347.0298 | 336 |
| coral_signals | default | 1 | {} | 16574 | 2762.3333 | 5.2697 | -286.4547 | -286.6078 | -0.0173 | 2 | -166.2730 | 281.7087 | -1.1949 | 0.8650 | 422.2313 | 336 |
| coral_signals | double | 1 | {"smooth_period": 20} | 8002 | 1333.6667 | 10.8650 | 257.8380 | 257.7644 | 0.0322 | 4 | -36.6808 | 36.6808 | 1.3281 | 0.1550 | 371.2461 | 336 |
| coral_signals | half | 1 | {"smooth_period": 5} | 31152 | 5192.0000 | 2.8013 | 232.4324 | 232.1475 | 0.0075 | 5 | -78.2951 | 78.2951 | 1.5550 | 0.1950 | 413.8954 | 336 |
| didi_index_signals | default | 1 | {} | 4956 | 826.0000 | 17.5682 | -17.7742 | -17.8199 | -0.0036 | 3 | -118.8009 | 118.8009 | -0.1127 | 0.5750 | 397.9180 | 336 |
| didi_index_signals | double | 1 | {"medium": 16} | 5960 | 993.3333 | 14.5977 | -206.7209 | -206.7782 | -0.0347 | 1 | -94.1124 | 177.4196 | -2.1435 | 0.8450 | 442.0445 | 336 |
| didi_index_signals | half | 1 | {"medium": 4} | 5990 | 998.3333 | 14.5412 | 72.8399 | 72.7846 | 0.0122 | 4 | -63.3219 | 63.3219 | 0.7234 | 0.4500 | 413.6716 | 336 |
| donchian_breakout_signals | default | 1 | {} | 2052 | 342.0000 | 42.2125 | -134.4183 | -134.4368 | -0.0655 | 3 | -154.0200 | 192.3250 | -0.6110 | 0.7200 | 400.5663 | 334 |
| donchian_breakout_signals | double | 1 | {"length": 40} | 1050 | 175.0000 | 84.1086 | 27.1526 | 27.1432 | 0.0259 | 2 | -73.4784 | 124.2110 | 0.1533 | 0.5000 | 418.9574 | 324 |
| donchian_breakout_signals | half | 1 | {"length": 10} | 3536 | 589.3333 | 24.6674 | -20.7606 | -20.7920 | -0.0059 | 3 | -93.6458 | 93.6458 | -0.1528 | 0.5350 | 408.9890 | 336 |
| dpo_signals | default | 1 | {} | 4160 | 693.3333 | 20.7202 | 27.6746 | 27.6354 | 0.0066 | 3 | -100.7891 | 100.7891 | 0.1531 | 0.4300 | 441.1922 | 336 |
| dpo_signals | double | 1 | {"len": 100} | 2836 | 472.6667 | 31.4245 | 39.8397 | 39.8143 | 0.0140 | 4 | -99.5579 | 99.5579 | 0.2375 | 0.4350 | 383.8353 | 314 |
| dpo_signals | half | 1 | {"len": 25} | 6192 | 1032.0000 | 14.0275 | -56.0369 | -56.0950 | -0.0091 | 3 | -159.5293 | 159.5293 | -0.2590 | 0.6150 | 343.4527 | 336 |
| dspo_signals | default | 1 | {} | 2824 | 470.6667 | 30.7479 | -158.2426 | -158.2686 | -0.0560 | 3 | -158.2424 | 185.7346 | -0.7020 | 0.7050 | 342.1947 | 336 |
| dspo_signals | double | 1 | {"len": 28} | 1398 | 233.0000 | 63.2961 | 46.0170 | 46.0043 | 0.0329 | 3 | -77.1974 | 97.7752 | 0.3464 | 0.3750 | 402.0282 | 332 |
| dspo_signals | half | 1 | {"len": 7} | 5132 | 855.3333 | 16.9462 | 64.7370 | 64.6899 | 0.0126 | 4 | -96.4163 | 96.4163 | 0.4101 | 0.3650 | 400.3903 | 336 |
| ehlers_reverse_ema_signals | default | 1 | {} | 4518 | 753.0000 | 19.2581 | 25.6600 | 25.6179 | 0.0057 | 3 | -95.7334 | 95.7334 | 0.1756 | 0.4500 | 371.9761 | 336 |
| ehlers_reverse_ema_signals | double | 1 | {"alpha": 0.05} | 3502 | 583.6667 | 24.7167 | -116.5394 | -116.5715 | -0.0333 | 3 | -143.9145 | 143.9145 | -0.6351 | 0.6800 | 390.0152 | 336 |
| ehlers_reverse_ema_signals | half | 1 | {"alpha": 0.2} | 5930 | 988.3333 | 14.6597 | 75.8817 | 75.8266 | 0.0128 | 5 | -81.1690 | 81.1690 | 0.5639 | 0.3050 | 335.9786 | 336 |
| fisher_transform_signals | default | 1 | {} | 21936 | 3656.0000 | 3.9778 | 194.2061 | 194.0040 | 0.0088 | 5 | -72.5672 | 0.0000 | 1.2091 | 0.2650 | 450.8386 | 336 |
| fisher_transform_signals | double | 1 | {"length": 20} | 20530 | 3421.6667 | 4.2483 | 201.3445 | 201.1542 | 0.0098 | 5 | -27.7348 | 0.0000 | 1.7092 | 0.1700 | 374.4398 | 336 |
| fisher_transform_signals | half | 1 | {"length": 5} | 24266 | 4044.3333 | 3.5975 | 97.4508 | 97.2261 | 0.0040 | 3 | -64.4009 | 39.8573 | 0.6663 | 0.3600 | 459.4388 | 336 |
| fx_sniper_ergodic_cci_signals | default | 1 | {} | 11730 | 1955.0000 | 7.4181 | 215.8475 | 215.7404 | 0.0184 | 3 | -38.5945 | 3.2865 | 1.3769 | 0.2400 | 450.1241 | 336 |
| fx_sniper_ergodic_cci_signals | double | 1 | {"cci_length": 28} | 9836 | 1639.3333 | 8.8589 | 187.1403 | 187.0485 | 0.0190 | 4 | -34.1205 | 34.1205 | 1.1154 | 0.2350 | 412.9799 | 336 |
| fx_sniper_ergodic_cci_signals | half | 1 | {"cci_length": 7} | 14984 | 2497.3333 | 5.8135 | -147.2358 | -147.3735 | -0.0098 | 3 | -133.7853 | 143.1901 | -0.8029 | 0.7750 | 420.5366 | 336 |
| glitch_index_signals | default | 1 | {} | 2104 | 350.6667 | 41.2681 | -172.3645 | -172.3832 | -0.0819 | 3 | -144.5383 | 144.5383 | -0.8739 | 0.7450 | 415.1660 | 336 |
| glitch_index_signals | double | 1 | {"length": 60} | 1448 | 241.3333 | 59.9890 | -63.5023 | -63.5154 | -0.0439 | 3 | -113.0209 | 113.0209 | -0.3547 | 0.6550 | 418.3549 | 334 |
| glitch_index_signals | half | 1 | {"length": 15} | 2720 | 453.3333 | 31.8515 | -148.7858 | -148.8102 | -0.0547 | 2 | -128.5927 | 211.8572 | -0.7429 | 0.6950 | 318.1087 | 336 |
| halftrend_signals | default | 1 | {} | 444 | 74.0000 | 195.6892 | -67.5909 | -67.5948 | -0.1522 | 4 | -137.1909 | 217.2461 | -0.3310 | 0.6300 | 380.6224 | 260 |
| halftrend_signals | double | 1 | {"amplitude": 100} | 200 | 33.3333 | 403.4200 | -54.2599 | -54.2617 | -0.2713 | 2 | -34.7916 | 57.9978 | -0.8739 | 0.7050 | 391.6647 | 174 |
| halftrend_signals | half | 1 | {"amplitude": 25} | 714 | 119.0000 | 128.3277 | 161.3442 | 161.3382 | 0.2260 | 3 | -83.2623 | 110.3300 | 0.8302 | 0.2550 | 405.3208 | 310 |
| hieken_ashi_smoothed_signals | default | 1 | {} | 5128 | 854.6667 | 16.9731 | -72.1368 | -72.1848 | -0.0141 | 3 | -115.3461 | 151.9855 | -0.4630 | 0.6050 | 400.7674 | 336 |
| hieken_ashi_smoothed_signals | double | 1 | {"ma_len1": 16} | 3474 | 579.0000 | 25.1100 | -306.9657 | -306.9969 | -0.0884 | 2 | -199.0990 | 277.1734 | -1.1786 | 0.9200 | 443.8162 | 336 |
| hieken_ashi_smoothed_signals | half | 1 | {"ma_len1": 4} | 6398 | 1066.3333 | 13.6221 | 137.9915 | 137.9323 | 0.0216 | 4 | -100.6028 | 100.6028 | 0.7623 | 0.2800 | 385.8920 | 336 |
| ichimoku_signals | default | 1 | {} | 768 | 128.0000 | 118.2812 | 12.6601 | 12.6533 | 0.0165 | 2 | -40.9203 | 65.8533 | 0.1441 | 0.4850 | 334.1448 | 312 |
| ichimoku_signals | double | 1 | {"conversion_len": 18} | 978 | 163.0000 | 91.4479 | 1.8586 | 1.8501 | 0.0019 | 2 | -77.2063 | 165.8088 | 0.0099 | 0.4750 | 356.0222 | 324 |
| ichimoku_signals | half | 1 | {"conversion_len": 4} | 784 | 130.6667 | 113.2551 | 93.1956 | 93.1888 | 0.1189 | 4 | -28.2357 | 33.7598 | 1.2077 | 0.3600 | 382.4473 | 310 |
| j_tpo_signals | default | 1 | {} | 2348 | 391.3333 | 37.0273 | -135.4588 | -135.4802 | -0.0577 | 3 | -180.0685 | 180.0685 | -0.5317 | 0.6900 | 450.5160 | 336 |
| j_tpo_signals | double | 1 | {"len": 80} | 1122 | 187.0000 | 79.6524 | 166.6551 | 166.6451 | 0.1485 | 4 | -70.6625 | 75.9305 | 1.0063 | 0.2100 | 333.6642 | 336 |
| j_tpo_signals | half | 1 | {"len": 20} | 4494 | 749.0000 | 19.3716 | -67.5811 | -67.6228 | -0.0150 | 2 | -94.3516 | 94.9892 | -0.5737 | 0.6350 | 345.7818 | 336 |
| kalman_filter_signals | default | 1 | {} | 2804 | 467.3333 | 31.0442 | -172.2027 | -172.2289 | -0.0614 | 3 | -158.7152 | 162.2808 | -0.7711 | 0.7050 | 422.7551 | 336 |
| kalman_filter_signals | double | 1 | {"sharpness": 0.5, "k": 0.5} | 1990 | 331.6667 | 43.7960 | -80.7438 | -80.7621 | -0.0406 | 3 | -161.8869 | 161.8869 | -0.3233 | 0.5950 | 456.7766 | 336 |
| kalman_filter_signals | half | 1 | {"sharpness": 2.0, "k": 2.0} | 3980 | 663.3333 | 21.8482 | -52.6171 | -52.6542 | -0.0132 | 3 | -124.5235 | 124.5235 | -0.2958 | 0.5450 | 345.4700 | 336 |
| kase_peak_oscillator_signals | default | 1 | {} | 4706 | 784.3333 | 18.4003 | -51.0644 | -51.1067 | -0.0109 | 3 | -73.8915 | 73.8915 | -0.5385 | 0.5750 | 381.3167 | 336 |
| kase_peak_oscillator_signals | double | 1 | {"short_cycle": 16} | 3574 | 595.6667 | 24.3145 | -130.1660 | -130.1978 | -0.0364 | 3 | -108.7053 | 118.6956 | -0.8079 | 0.7100 | 371.5595 | 336 |
| kase_peak_oscillator_signals | half | 1 | {"short_cycle": 4} | 6522 | 1087.0000 | 13.3002 | 128.4035 | 128.3451 | 0.0197 | 4 | -28.7869 | 3.9897 | 1.4036 | 0.2850 | 372.4813 | 336 |
| kuskus_starlight_signals | default | 1 | {} | 4900 | 816.6667 | 17.7355 | -47.7585 | -47.8023 | -0.0098 | 2 | -77.8761 | 77.8761 | -0.3668 | 0.5850 | 339.5869 | 336 |
| kuskus_starlight_signals | double | 1 | {"range_periods": 60} | 3478 | 579.6667 | 24.9425 | -46.5080 | -46.5389 | -0.0134 | 3 | -106.0218 | 106.0218 | -0.2661 | 0.5500 | 373.9221 | 336 |
| kuskus_starlight_signals | half | 1 | {"range_periods": 15} | 7110 | 1185.0000 | 12.2321 | 74.8888 | 74.8252 | 0.0105 | 5 | -53.1359 | 53.1359 | 0.8790 | 0.4250 | 388.8890 | 336 |
| laguerre_filter_signals | default | 1 | {} | 2564 | 427.3333 | 33.9228 | -64.4750 | -64.4982 | -0.0252 | 3 | -132.5803 | 132.5803 | -0.3309 | 0.6400 | 414.5089 | 336 |
| laguerre_filter_signals | double | 1 | {"alpha": 0.1} | 1192 | 198.6667 | 74.2685 | 204.8722 | 204.8613 | 0.1719 | 4 | -34.3846 | 67.6785 | 1.2143 | 0.1900 | 326.2089 | 332 |
| laguerre_filter_signals | half | 1 | {"alpha": 0.4} | 5166 | 861.0000 | 16.8560 | 19.7353 | 19.6879 | 0.0038 | 3 | -112.0013 | 112.0013 | 0.1184 | 0.4300 | 378.3167 | 336 |
| lemantrend_signals | default | 1 | {} | 2454 | 409.0000 | 35.4939 | 90.7576 | 90.7350 | 0.0370 | 3 | -71.8570 | 81.9329 | 0.4526 | 0.3000 | 351.0952 | 336 |
| lemantrend_signals | double | 1 | {"slow_period": 26} | 1782 | 297.0000 | 48.9136 | 66.3011 | 66.2850 | 0.0372 | 3 | -79.2718 | 109.2695 | 0.3495 | 0.3600 | 401.2141 | 336 |
| lemantrend_signals | half | 1 | {"slow_period": 6} | 3276 | 546.0000 | 26.4420 | 122.5626 | 122.5323 | 0.0374 | 3 | -53.8433 | 92.2722 | 0.6182 | 0.2950 | 408.7922 | 336 |
| linreg_slope_signals | default | 1 | {} | 4376 | 729.3333 | 19.8816 | 33.0104 | 32.9698 | 0.0075 | 4 | -144.4166 | 144.4166 | 0.1680 | 0.3950 | 319.8136 | 336 |
| linreg_slope_signals | double | 1 | {"length": 28} | 2240 | 373.3333 | 39.0321 | -88.8973 | -88.9176 | -0.0397 | 3 | -148.5717 | 148.5717 | -0.3990 | 0.6450 | 374.2722 | 336 |
| linreg_slope_signals | half | 1 | {"length": 7} | 8812 | 1468.6667 | 9.8522 | 90.4675 | 90.3868 | 0.0103 | 4 | -50.4761 | 28.4044 | 0.7297 | 0.4050 | 481.8169 | 336 |
| mama_fama_signals | default | 1 | {} | 3780 | 630.0000 | 22.9751 | -74.4687 | -74.5038 | -0.0197 | 3 | -111.8553 | 111.8553 | -0.5387 | 0.6450 | 396.8292 | 336 |
| mama_fama_signals | double | 1 | {"fast_limit": 0.25, "slow_limit": 0.025} | 1842 | 307.0000 | 47.4875 | -51.9118 | -51.9289 | -0.0282 | 3 | -142.9878 | 142.9878 | -0.2851 | 0.5600 | 303.8143 | 334 |
| mama_fama_signals | half | 1 | {"fast_limit": 1.0, "slow_limit": 0.1} | 8182 | 1363.6667 | 10.6248 | 65.6441 | 65.5691 | 0.0080 | 3 | -37.9927 | 37.9927 | 0.7601 | 0.4350 | 412.4151 | 336 |
| parabolic_sar_signals | default | 1 | {} | 8128 | 1354.6667 | 10.7345 | 22.4601 | 22.3865 | 0.0028 | 5 | -63.2904 | 0.0000 | 0.2680 | 0.4850 | 386.4714 | 336 |
| parabolic_sar_signals | double | 1 | {"sar_start": 0.01, "sar_increment": 0.01} | 5252 | 875.3333 | 16.6021 | -33.5320 | -33.5798 | -0.0064 | 2 | -24.8807 | 30.5512 | -0.7248 | 0.6150 | 405.8995 | 336 |
| parabolic_sar_signals | half | 1 | {"sar_start": 0.04, "sar_increment": 0.04} | 11678 | 1946.3333 | 7.4561 | 212.7133 | 212.6074 | 0.0182 | 5 | -67.5217 | 0.0000 | 1.3252 | 0.2000 | 386.2091 | 336 |
| polychromatic_momentum_signals | default | 1 | {} | 3578 | 596.3333 | 24.2946 | -160.4630 | -160.4969 | -0.0449 | 3 | -119.5227 | 134.3240 | -1.0260 | 0.7650 | 432.1980 | 336 |
| polychromatic_momentum_signals | double | 1 | {"len": 28} | 1764 | 294.0000 | 49.0522 | 15.2064 | 15.1905 | 0.0086 | 3 | -107.0195 | 87.5853 | 0.0688 | 0.4750 | 423.3563 | 336 |
| polychromatic_momentum_signals | half | 1 | {"len": 7} | 6780 | 1130.0000 | 12.8440 | 104.0566 | 103.9933 | 0.0153 | 4 | -104.7908 | 104.7908 | 0.6159 | 0.2600 | 354.0896 | 336 |
| price_momentum_oscillator_signals | default | 1 | {} | 2160 | 360.0000 | 40.1815 | -119.8140 | -119.8338 | -0.0555 | 3 | -160.2493 | 160.2493 | -0.6078 | 0.7500 | 364.7947 | 336 |
| price_momentum_oscillator_signals | double | 1 | {"s1": 70} | 1508 | 251.3333 | 58.7069 | 54.0177 | 54.0039 | 0.0358 | 3 | -109.5542 | 130.4460 | 0.2800 | 0.3800 | 353.8778 | 330 |
| price_momentum_oscillator_signals | half | 1 | {"s1": 18} | 3028 | 504.6667 | 28.5978 | -168.2445 | -168.2722 | -0.0556 | 3 | -148.6208 | 159.3464 | -0.8150 | 0.8050 | 422.1023 | 336 |
| qqe_mod_signals | default | 1 | {} | 5496 | 916.0000 | 15.8308 | -17.3367 | -17.3877 | -0.0032 | 4 | -116.2028 | 116.2028 | -0.1076 | 0.5000 | 402.2866 | 336 |
| qqe_mod_signals | double | 1 | {"rsi_period": 12} | 4008 | 668.0000 | 21.6203 | -109.9178 | -109.9551 | -0.0274 | 2 | -136.0668 | 136.0668 | -0.6734 | 0.6850 | 392.3317 | 336 |
| qqe_mod_signals | half | 1 | {"rsi_period": 3} | 7618 | 1269.6667 | 11.4169 | 35.6543 | 35.5839 | 0.0047 | 4 | -78.6238 | 78.6238 | 0.3091 | 0.4800 | 404.5748 | 336 |
| relative_vigor_index_signals | default | 1 | {} | 15250 | 2541.6667 | 5.7091 | -187.0964 | -187.2373 | -0.0123 | 0 | -62.9933 | 179.8256 | -3.3400 | 0.7850 | 431.1109 | 336 |
| relative_vigor_index_signals | double | 1 | {"len": 20} | 15406 | 2567.6667 | 5.6710 | 114.4275 | 114.2843 | 0.0074 | 3 | -95.0163 | 95.0163 | 0.5612 | 0.3500 | 361.4142 | 336 |
| relative_vigor_index_signals | half | 1 | {"len": 5} | 16542 | 2757.0000 | 5.2702 | 76.6382 | 76.4862 | 0.0046 | 4 | -128.8776 | 242.7461 | 0.2633 | 0.3900 | 482.5392 | 336 |
| rex_oscillator_signals | default | 1 | {} | 15306 | 2551.0000 | 5.6959 | 245.4968 | 245.3573 | 0.0160 | 5 | -83.7573 | 83.7573 | 1.2890 | 0.2150 | 493.9154 | 336 |
| rex_oscillator_signals | double | 1 | {"smooth": 26} | 20198 | 3366.3333 | 4.3155 | -0.1065 | -0.2940 | -0.0000 | 2 | -138.4281 | 108.3699 | -0.0010 | 0.5050 | 436.4784 | 336 |
| rex_oscillator_signals | half | 1 | {"smooth": 6} | 16884 | 2814.0000 | 5.1568 | -27.4424 | -27.5957 | -0.0016 | 3 | -101.2975 | 140.5255 | -0.1831 | 0.5100 | 383.6186 | 336 |
| schaff_trend_cycle_signals | default | 1 | {} | 3114 | 519.0000 | 15.3340 | 98.5703 | 98.5424 | 0.0316 | 5 | -28.6384 | 28.6384 | 1.3786 | 0.2300 | 280.8651 | 158 |
| schaff_trend_cycle_signals | double | 1 | {"macdFast": 46} | 2834 | 472.3333 | 18.0275 | -102.5985 | -102.6235 | -0.0362 | 1 | -47.6776 | 82.3602 | -1.3378 | 0.7150 | 258.0782 | 160 |
| schaff_trend_cycle_signals | half | 1 | {"macdFast": 12} | 3298 | 549.6667 | 13.5355 | 182.9851 | 182.9551 | 0.0555 | 4 | -20.2279 | 26.3108 | 1.5845 | 0.1650 | 291.5955 | 158 |
| ssl_channel_signals | default | 1 | {} | 6986 | 1164.3333 | 12.4446 | 147.8076 | 147.7450 | 0.0211 | 3 | -30.6362 | 30.6362 | 1.3701 | 0.2950 | 421.6341 | 336 |
| ssl_channel_signals | double | 1 | {"len": 20} | 4994 | 832.3333 | 17.4485 | 1.4840 | 1.4384 | 0.0003 | 3 | -88.1489 | 88.1489 | 0.0116 | 0.4500 | 433.2187 | 336 |
| ssl_channel_signals | half | 1 | {"len": 5} | 9898 | 1649.6667 | 8.7798 | 134.6000 | 134.5119 | 0.0136 | 4 | -56.3357 | 2.6403 | 1.1735 | 0.2600 | 371.0828 | 336 |
| supertrend_signals | default | 1 | {} | 2232 | 372.0000 | 38.8522 | -25.3459 | -25.3657 | -0.0114 | 3 | -69.2345 | 69.2345 | -0.2125 | 0.5100 | 368.5296 | 336 |
| supertrend_signals | double | 1 | {"atr_period": 20} | 2208 | 368.0000 | 39.2808 | -19.2736 | -19.2929 | -0.0087 | 3 | -65.1711 | 65.1711 | -0.1886 | 0.6100 | 434.2636 | 336 |
| supertrend_signals | half | 1 | {"atr_period": 5} | 2312 | 385.3333 | 37.5389 | -208.9005 | -208.9213 | -0.0904 | 2 | -100.7195 | 167.2056 | -1.6137 | 0.7800 | 350.3251 | 336 |
| trend_direction_force_index_signals | default | 1 | {} | 2052 | 342.0000 | 41.9045 | -182.8448 | -182.8638 | -0.0891 | 3 | -160.0652 | 197.8029 | -0.8822 | 0.7450 | 445.9592 | 336 |
| trend_direction_force_index_signals | double | 1 | {"lookback": 26} | 982 | 163.6667 | 89.1202 | -1.7001 | -1.7088 | -0.0017 | 3 | -79.5692 | 118.1874 | -0.0130 | 0.4700 | 372.8162 | 324 |
| trend_direction_force_index_signals | half | 1 | {"lookback": 6} | 4228 | 704.6667 | 20.5530 | 53.1386 | 53.0990 | 0.0126 | 4 | -89.9391 | 89.9391 | 0.3980 | 0.3300 | 369.6822 | 336 |
| volatility_quality_signals | default | 1 | {} | 4052 | 675.3333 | 21.3445 | 123.2017 | 123.1660 | 0.0304 | 4 | -58.6813 | 58.6813 | 0.9812 | 0.2450 | 338.5627 | 336 |
| volatility_quality_signals | double | 1 | {"smooth": 20} | 1470 | 245.0000 | 59.3905 | -219.8550 | -219.8680 | -0.1496 | 2 | -104.8137 | 169.0213 | -1.7526 | 0.8500 | 371.3511 | 330 |
| volatility_quality_signals | half | 1 | {"smooth": 5} | 10212 | 1702.0000 | 8.5212 | 150.9157 | 150.8252 | 0.0148 | 4 | -35.3887 | 35.3887 | 1.3234 | 0.2650 | 390.9430 | 336 |
| vortex_signals | default | 1 | {} | 8254 | 1375.6667 | 10.5614 | 35.4000 | 35.3206 | 0.0043 | 3 | -74.1298 | 74.1298 | 0.2250 | 0.4400 | 376.9141 | 336 |
| vortex_signals | double | 1 | {"period": 28} | 6078 | 1013.0000 | 14.2945 | -159.0171 | -159.0766 | -0.0262 | 3 | -188.4583 | 188.4583 | -0.7127 | 0.7600 | 346.7895 | 336 |
| vortex_signals | half | 1 | {"period": 7} | 11832 | 1972.0000 | 7.3425 | 91.8101 | 91.7010 | 0.0078 | 3 | -44.9332 | 25.3425 | 0.7107 | 0.3950 | 465.9467 | 336 |
| waddah_attar_explosion_signals | default | 1 | {} | 1822 | 303.6667 | 47.7651 | 67.5373 | 67.5209 | 0.0371 | 3 | -93.6532 | 114.5288 | 0.3439 | 0.3950 | 392.0909 | 336 |
| waddah_attar_explosion_signals | double | 1 | {"sensitivity": 300} | 1888 | 314.6667 | 46.0265 | 75.9151 | 75.8982 | 0.0402 | 4 | -85.5784 | 102.4750 | 0.3972 | 0.3900 | 361.6039 | 336 |
| waddah_attar_explosion_signals | half | 1 | {"sensitivity": 75} | 1722 | 287.0000 | 50.6283 | 51.6413 | 51.6258 | 0.0300 | 3 | -85.7297 | 119.4582 | 0.2763 | 0.4150 | 353.5800 | 336 |


## C1 — canonical_risk, walk-forward pick, BUILD years 2010-2015

`n_settings_used` is how many different settings the six steps chose. A candidate whose steps keep switching setting is being fitted, not measured.

| indicator | R_net_build | n | R_per_trade | trades_per_year | mean_bars | years_positive | worst_year | best_year | worst_dip_R | t_yearly | settings_used | n_settings_used | clears_alone | clears_best_of_family |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|
| didi_index_signals | 103.4874 | 5392.0000 | 0.0192 | 898.6667 | 5.0920 | 4 | -23.9573 | 68.0268 | 8.3768 | 1.2544 | default,double,half | 3 | 0 | 0 |
| linreg_slope_signals | 73.1106 | 4274.0000 | 0.0171 | 712.3333 | 5.4694 | 4 | -35.5186 | 80.1011 | 35.5186 | 0.7343 | default,double | 2 | 0 | 0 |
| dspo_signals | 71.9602 | 3529.0000 | 0.0204 | 588.1667 | 5.2971 | 3 | -16.8394 | 48.8418 | 5.6591 | 1.1491 | default,double,half | 3 | 0 | 0 |
| kalman_filter_signals | 65.2588 | 3466.0000 | 0.0188 | 577.6667 | 5.3529 | 4 | -18.7291 | 67.8392 | 18.7291 | 0.9038 | default,half | 2 | 0 | 0 |
| schaff_trend_cycle_signals | 57.3506 | 3448.0000 | 0.0166 | 574.6667 | 5.0859 | 4 | -26.7836 | 68.2063 | 18.9023 | 0.6976 | default,half | 2 | 0 | 0 |
| ehlers_reverse_ema_signals | 54.6181 | 4054.0000 | 0.0135 | 675.6667 | 5.2546 | 2 | -13.6903 | 66.2738 | 18.1731 | 0.7685 | default,double | 2 | 0 | 0 |
| laguerre_filter_signals | 39.9395 | 2775.0000 | 0.0144 | 462.5000 | 5.2532 | 2 | -27.7309 | 64.0855 | 27.7309 | 0.4868 | default,double,half | 3 | 0 | 0 |
| bears_bulls_impulse_signals | 37.9005 | 6748.0000 | 0.0056 | 1124.6667 | 5.4339 | 3 | -34.5417 | 54.4141 | 30.2736 | 0.4344 | double | 1 | 0 | 0 |
| ssl_channel_signals | 35.4143 | 6807.0000 | 0.0052 | 1134.5000 | 5.2539 | 3 | -35.3198 | 39.9676 | 11.0920 | 0.5163 | default,double,half | 3 | 0 | 0 |
| waddah_attar_explosion_signals | 27.2739 | 2008.0000 | 0.0136 | 334.6667 | 4.9915 | 2 | -14.2127 | 47.7455 | 16.6136 | 0.4341 | double,half | 2 | 0 | 0 |
| aroon_signals | 25.6771 | 3778.0000 | 0.0068 | 629.6667 | 5.1273 | 2 | -19.6281 | 78.2653 | 33.7151 | 0.2709 | default,double,half | 3 | 0 | 0 |
| coppock_curve_signals | 20.3134 | 3957.0000 | 0.0051 | 659.5000 | 5.2448 | 3 | -26.8379 | 42.3763 | 32.5067 | 0.3254 | default,double,half | 3 | 0 | 0 |
| qqe_mod_signals | 14.5368 | 4544.0000 | 0.0032 | 757.3333 | 5.0525 | 2 | -17.2754 | 55.0866 | 41.5693 | 0.2233 | default,double | 2 | 0 | 0 |
| hieken_ashi_smoothed_signals | 13.1597 | 4215.0000 | 0.0031 | 702.5000 | 5.3209 | 2 | -37.2966 | 85.4660 | 81.5352 | 0.1208 | default,double,half | 3 | 0 | 0 |
| kuskus_starlight_signals | 9.6912 | 5331.0000 | 0.0018 | 888.5000 | 4.7538 | 3 | -23.9841 | 22.6242 | 23.9841 | 0.2519 | double,half | 2 | 0 | 0 |
| ichimoku_signals | 5.3861 | 2027.0000 | 0.0027 | 337.8333 | 5.3175 | 2 | -26.1728 | 44.1224 | 27.1928 | 0.0845 | double,half | 2 | 0 | 0 |
| parabolic_sar_signals | 2.4400 | 7207.0000 | 0.0003 | 1201.1667 | 5.0433 | 3 | -63.2572 | 56.8611 | 25.9665 | 0.0241 | default,double | 2 | 0 | 0 |
| lemantrend_signals | 1.1505 | 1995.0000 | 0.0006 | 332.5000 | 4.7830 | 2 | -20.6877 | 24.8871 | 22.5213 | 0.0274 | default,double | 2 | 0 | 0 |
| mama_fama_signals | -1.4236 | 4221.0000 | -0.0003 | 703.5000 | 5.1134 | 3 | -27.2693 | 42.8928 | 43.9442 | -0.0236 | default,double,half | 3 | 0 | 0 |
| dpo_signals | -2.8105 | 2873.0000 | -0.0010 | 478.8333 | 3.7039 | 3 | -16.8956 | 25.6758 | 17.1064 | -0.0656 | default,double | 2 | 0 | 0 |
| halftrend_signals | -2.9614 | 402.0000 | -0.0074 | 67.0000 | 5.0003 | 3 | -5.6657 | 4.9084 | 9.4673 | -0.3096 | default,double | 2 | 0 | 0 |
| volatility_quality_signals | -3.0088 | 4251.0000 | -0.0007 | 708.5000 | 5.3133 | 3 | -54.4378 | 54.5349 | 10.1401 | -0.0347 | default,double,half | 3 | 0 | 0 |
| polychromatic_momentum_signals | -3.1539 | 4128.0000 | -0.0008 | 688.0000 | 5.0846 | 2 | -38.9359 | 67.2199 | 83.8425 | -0.0333 | default,half | 2 | 0 | 0 |
| donchian_breakout_signals | -8.4626 | 2064.0000 | -0.0041 | 344.0000 | 5.4042 | 1 | -9.9753 | 25.5747 | 17.6958 | -0.2564 | default | 1 | 0 | 0 |
| chandelier_exit_signals | -21.4341 | 2820.0000 | -0.0076 | 470.0000 | 5.4152 | 3 | -16.4262 | 3.9557 | 29.3016 | -1.1245 | default,half | 2 | 0 | 0 |
| vortex_signals | -25.7557 | 7584.0000 | -0.0034 | 1264.0000 | 3.8123 | 2 | -49.5076 | 54.4048 | 37.5448 | -0.2662 | default,double | 2 | 0 | 0 |
| trend_direction_force_index_signals | -29.0021 | 3563.0000 | -0.0081 | 593.8333 | 5.2561 | 2 | -24.4140 | 17.8659 | 34.0948 | -0.8285 | default,double | 2 | 0 | 0 |
| supertrend_signals | -45.2121 | 2296.0000 | -0.0197 | 382.6667 | 5.3724 | 2 | -23.0096 | 6.3689 | 36.0163 | -1.7042 | default,half | 2 | 0 | 0 |
| j_tpo_signals | -48.9630 | 3647.0000 | -0.0134 | 607.8333 | 5.0808 | 2 | -55.3295 | 51.1931 | 90.0246 | -0.5579 | default,double,half | 3 | 0 | 0 |
| kase_peak_oscillator_signals | -55.3691 | 3726.0000 | -0.0149 | 621.0000 | 4.8868 | 1 | -25.2065 | 4.0672 | 38.3328 | -2.1081 | default,double | 2 | 0 | 0 |
| fx_sniper_ergodic_cci_signals | -61.6381 | 12747.0000 | -0.0048 | 2124.5000 | 3.8352 | 2 | -75.6187 | 61.0775 | 85.4212 | -0.4830 | default,double,half | 3 | 0 | 0 |
| price_momentum_oscillator_signals | -65.2893 | 2198.0000 | -0.0297 | 366.3333 | 5.0804 | 1 | -18.4185 | 4.0995 | 49.5978 | -3.0195 | default,double,half | 3 | 0 | 0 |
| glitch_index_signals | -67.4020 | 4367.0000 | -0.0154 | 727.8333 | 5.4278 | 2 | -28.7789 | 18.2327 | 69.2526 | -1.5260 | default,half | 2 | 0 | 0 |
| adx_dmi_signals | -81.0910 | 1775.0000 | -0.0457 | 295.8333 | 4.9022 | 1 | -66.7223 | 2.8551 | 17.0199 | -1.2575 | default,double,half | 3 | 0 | 0 |
| fisher_transform_signals | -129.2130 | 20666.0000 | -0.0063 | 3444.3333 | 2.8102 | 1 | -54.5135 | 16.2129 | 100.3024 | -1.9481 | default,double | 2 | 0 | 0 |
| rex_oscillator_signals | -142.0751 | 16298.0000 | -0.0087 | 2716.3333 | 3.0255 | 0 | -46.7067 | -1.8325 | 118.3200 | -3.6810 | default,half | 2 | 0 | 0 |
| relative_vigor_index_signals | -177.5960 | 15561.0000 | -0.0114 | 2593.5000 | 3.1296 | 2 | -80.1429 | 37.8785 | 210.1300 | -1.5201 | default,double,half | 3 | 0 | 0 |
| center_of_gravity_signals | -214.5161 | 16527.0000 | -0.0130 | 2754.5000 | 3.3670 | 1 | -102.1452 | 50.9940 | 221.6895 | -1.7190 | default,double,half | 3 | 0 | 0 |
| coral_signals | -234.5125 | 19928.0000 | -0.0118 | 3321.3333 | 3.2529 | 2 | -143.2040 | 37.4756 | 208.1880 | -1.4681 | default,double,half | 3 | 0 | 0 |


### C1 — canonical_risk, ALL THREE SETTINGS UNPICKED

The same six BUILD years with each setting held fixed, so the walk-forward number above can be compared with what any single setting would have done. `null_p` is against the matched random-entry null, 200 draws, matched on trade count and holding period per pair.

| indicator | setting | distinct_setting | params | n | trades_per_year | mean_bars | R_gross_build | R_net_build | R_per_trade_net | years_positive | worst_year | worst_dip_R | t_yearly | null_p | null_p95 | straddles |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| adx_dmi_signals | default | 1 | {} | 1092 | 182.0000 | 4.6484 | -3.5143 | -15.3858 | -0.0141 | 1 | -6.6097 | 16.0987 | -1.9334 | 0.4050 | 83.3733 | 11 |
| adx_dmi_signals | double | 1 | {"di_length": 28} | 82 | 13.6667 | 4.8902 | -2.9974 | -3.7217 | -0.0454 | 1 | -3.8840 | 5.6807 | -0.7073 | 0.5500 | 21.3570 | 0 |
| adx_dmi_signals | half | 1 | {"di_length": 7} | 7941 | 1323.5000 | 4.0370 | 59.2670 | -33.5876 | -0.0042 | 3 | -66.7223 | 34.2716 | -0.3203 | 0.0300 | -72.7860 | 123 |
| aroon_signals | default | 1 | {} | 3561 | 593.5000 | 5.1008 | 23.6179 | -21.0016 | -0.0059 | 2 | -17.5951 | 34.9910 | -0.5555 | 0.2400 | 80.6560 | 63 |
| aroon_signals | double | 1 | {"length": 50} | 1807 | 301.1667 | 5.1267 | -5.4999 | -28.2236 | -0.0156 | 2 | -21.1140 | 22.2232 | -0.6320 | 0.3300 | 74.5564 | 40 |
| aroon_signals | half | 1 | {"length": 12} | 6463 | 1077.1667 | 5.0190 | 185.9571 | 106.2413 | 0.0164 | 3 | -13.2965 | 13.2965 | 1.2360 | 0.0250 | 44.7820 | 137 |
| bears_bulls_impulse_signals | default | 1 | {} | 8240 | 1373.3333 | 5.3095 | 91.2762 | -5.9026 | -0.0007 | 3 | -62.3795 | 20.2991 | -0.0607 | 0.0550 | 3.2518 | 160 |
| bears_bulls_impulse_signals | double | 1 | {"length": 26} | 6748 | 1124.6667 | 5.4235 | 118.0180 | 37.9005 | 0.0056 | 3 | -34.5417 | 30.2736 | 0.4344 | 0.0750 | 50.5323 | 142 |
| bears_bulls_impulse_signals | half | 1 | {"length": 6} | 8210 | 1368.3333 | 5.3061 | 32.8593 | -62.9395 | -0.0077 | 1 | -22.1805 | 60.4105 | -1.7194 | 0.1200 | 21.2811 | 172 |
| center_of_gravity_signals | default | 1 | {} | 15856 | 2642.6667 | 3.3954 | -18.9318 | -215.2157 | -0.0136 | 1 | -102.1452 | 229.6912 | -1.6541 | 0.0600 | -185.7775 | 226 |
| center_of_gravity_signals | double | 1 | {"length": 20} | 10337 | 1722.8333 | 4.0038 | 123.7485 | -3.5039 | -0.0003 | 4 | -50.5338 | 17.2035 | -0.0429 | 0.0450 | -42.6211 | 163 |
| center_of_gravity_signals | half | 1 | {"length": 5} | 24833 | 4138.8333 | 2.6689 | -95.9931 | -400.6810 | -0.0161 | 0 | -113.8018 | 286.8792 | -5.3397 | 0.0450 | -413.5969 | 234 |
| chandelier_exit_signals | default | 1 | {} | 2838 | 473.0000 | 5.3587 | 21.4909 | -10.5871 | -0.0037 | 4 | -16.4262 | 23.4492 | -0.5156 | 0.1850 | 64.6770 | 61 |
| chandelier_exit_signals | double | 1 | {"atr_period": 44} | 3876 | 646.0000 | 4.5359 | 4.8494 | -37.8369 | -0.0098 | 3 | -35.3509 | 46.1088 | -0.9389 | 0.2400 | 76.5587 | 60 |
| chandelier_exit_signals | half | 1 | {"atr_period": 11} | 2630 | 438.3333 | 5.4913 | 14.0134 | -16.7335 | -0.0064 | 1 | -11.3156 | 21.5082 | -1.2486 | 0.1950 | 59.4026 | 61 |
| coppock_curve_signals | default | 1 | {} | 4394 | 732.3333 | 5.3143 | 119.4106 | 64.6381 | 0.0147 | 3 | -38.4640 | 44.1328 | 0.7992 | 0.0600 | 82.2069 | 112 |
| coppock_curve_signals | double | 1 | {"smooth_len": 20} | 3367 | 561.1667 | 5.2236 | 49.1043 | 6.9282 | 0.0021 | 3 | -26.8379 | 49.8065 | 0.0982 | 0.1400 | 92.7161 | 62 |
| coppock_curve_signals | half | 1 | {"smooth_len": 5} | 5415 | 902.5000 | 5.0395 | 136.4801 | 69.4137 | 0.0128 | 4 | -16.8060 | 16.8060 | 1.4173 | 0.0350 | 42.3417 | 117 |
| coral_signals | default | 1 | {} | 16563 | 2760.5000 | 3.3559 | -145.8834 | -349.8149 | -0.0211 | 1 | -108.2129 | 286.0148 | -3.2573 | 0.2200 | -155.8759 | 206 |
| coral_signals | double | 1 | {"smooth_period": 20} | 8006 | 1334.3333 | 4.6209 | 99.5665 | 1.5034 | 0.0002 | 3 | -75.2092 | 18.5765 | 0.0128 | 0.0400 | -14.2637 | 158 |
| coral_signals | half | 1 | {"smooth_period": 5} | 31145 | 5190.8333 | 2.2548 | 181.3344 | -198.5240 | -0.0064 | 1 | -143.2040 | 224.8933 | -1.4128 | 0.0000 | -609.8102 | 269 |
| didi_index_signals | default | 1 | {} | 4949 | 824.8333 | 5.1881 | 134.4927 | 73.7657 | 0.0149 | 4 | -13.1387 | 13.1387 | 1.0394 | 0.0500 | 69.2140 | 116 |
| didi_index_signals | double | 1 | {"medium": 16} | 5972 | 995.3333 | 4.3835 | -32.5927 | -109.1453 | -0.0183 | 1 | -47.7118 | 131.9133 | -1.3108 | 0.2800 | 7.8372 | 101 |
| didi_index_signals | half | 1 | {"medium": 4} | 5986 | 997.6667 | 4.9739 | 172.0821 | 98.3714 | 0.0164 | 4 | -9.5281 | 9.5281 | 1.3106 | 0.0150 | 42.5520 | 116 |
| donchian_breakout_signals | default | 1 | {} | 2064 | 344.0000 | 5.3745 | 16.3161 | -8.4626 | -0.0041 | 1 | -9.9753 | 17.6958 | -0.2564 | 0.2450 | 75.5736 | 48 |
| donchian_breakout_signals | double | 1 | {"length": 40} | 1054 | 175.6667 | 5.1708 | -0.0769 | -12.6656 | -0.0120 | 1 | -21.5650 | 12.1064 | -0.3375 | 0.3850 | 80.4297 | 22 |
| donchian_breakout_signals | half | 1 | {"length": 10} | 3527 | 587.8333 | 5.6110 | 4.9196 | -36.9225 | -0.0105 | 1 | -17.6240 | 39.4638 | -1.8285 | 0.2950 | 127.7965 | 74 |
| dpo_signals | default | 1 | {} | 4170 | 695.0000 | 3.6511 | 3.0067 | -49.3667 | -0.0118 | 2 | -37.2167 | 37.2167 | -0.8736 | 0.1700 | 2.4957 | 67 |
| dpo_signals | double | 1 | {"len": 100} | 2836 | 472.6667 | 3.5257 | 20.3057 | -13.6862 | -0.0048 | 3 | -16.8956 | 17.1064 | -0.3842 | 0.1450 | 36.1612 | 32 |
| dpo_signals | half | 1 | {"len": 25} | 6192 | 1032.0000 | 3.6437 | 75.7328 | -1.7309 | -0.0003 | 2 | -26.6578 | 40.3906 | -0.0293 | 0.0550 | 6.5632 | 96 |
| dspo_signals | default | 1 | {} | 2829 | 471.5000 | 5.1304 | -9.6593 | -44.2844 | -0.0157 | 2 | -27.7954 | 45.3990 | -1.2837 | 0.3300 | 87.8023 | 67 |
| dspo_signals | double | 1 | {"len": 28} | 1408 | 234.6667 | 5.4638 | -9.1313 | -26.1721 | -0.0186 | 1 | -16.8394 | 20.9561 | -0.8823 | 0.3500 | 69.9366 | 35 |
| dspo_signals | half | 1 | {"len": 7} | 5132 | 855.3333 | 5.1354 | 171.6925 | 108.8672 | 0.0212 | 4 | -5.9839 | 5.9839 | 2.0974 | 0.0450 | 38.9891 | 105 |
| ehlers_reverse_ema_signals | default | 1 | {} | 4519 | 753.1667 | 5.3244 | 140.7222 | 84.5037 | 0.0187 | 4 | -3.2666 | 3.2666 | 1.3244 | 0.0500 | 84.8164 | 103 |
| ehlers_reverse_ema_signals | double | 1 | {"alpha": 0.05} | 3505 | 584.1667 | 5.2311 | 22.7335 | -20.0789 | -0.0057 | 2 | -13.6903 | 18.1731 | -1.1860 | 0.1850 | 64.1428 | 78 |
| ehlers_reverse_ema_signals | half | 1 | {"alpha": 0.2} | 5930 | 988.3333 | 5.1728 | 155.1171 | 81.5752 | 0.0138 | 3 | -8.0863 | 5.3440 | 1.2299 | 0.0300 | 32.3752 | 132 |
| fisher_transform_signals | default | 1 | {} | 21934 | 3655.6667 | 2.7141 | 79.8666 | -189.4375 | -0.0086 | 1 | -70.4376 | 135.2128 | -2.2486 | 0.0050 | -322.5091 | 225 |
| fisher_transform_signals | double | 1 | {"length": 20} | 20536 | 3422.6667 | 2.8212 | 109.1539 | -144.6424 | -0.0070 | 1 | -54.5135 | 100.3024 | -2.5413 | 0.0050 | -341.9811 | 223 |
| fisher_transform_signals | half | 1 | {"length": 5} | 24265 | 4044.1667 | 2.5984 | 74.5053 | -225.1320 | -0.0093 | 1 | -83.8826 | 147.2568 | -2.4242 | 0.0050 | -402.0453 | 229 |
| fx_sniper_ergodic_cci_signals | default | 1 | {} | 11736 | 1956.0000 | 3.9885 | 46.4967 | -96.3269 | -0.0082 | 3 | -75.6187 | 72.6437 | -0.8388 | 0.0800 | -78.0303 | 212 |
| fx_sniper_ergodic_cci_signals | double | 1 | {"cci_length": 28} | 9833 | 1638.8333 | 4.2376 | 142.1882 | 19.8113 | 0.0020 | 3 | -43.4004 | 30.9146 | 0.2008 | 0.0300 | -73.6639 | 191 |
| fx_sniper_ergodic_cci_signals | half | 1 | {"cci_length": 7} | 14983 | 2497.1667 | 3.5396 | -18.3449 | -201.8791 | -0.0135 | 1 | -72.8823 | 167.3211 | -2.0418 | 0.1050 | -78.5065 | 215 |
| glitch_index_signals | default | 1 | {} | 3714 | 619.0000 | 5.3600 | -13.0758 | -57.4854 | -0.0155 | 2 | -33.0804 | 55.6380 | -0.9151 | 0.2950 | 47.4905 | 95 |
| glitch_index_signals | double | 1 | {"length": 60} | 2834 | 472.3333 | 5.4312 | 38.4254 | 3.6728 | 0.0013 | 2 | -37.5204 | 37.5204 | 0.0538 | 0.2050 | 101.4381 | 62 |
| glitch_index_signals | half | 1 | {"length": 15} | 4449 | 741.5000 | 5.4545 | 80.0231 | 26.6944 | 0.0060 | 3 | -23.4335 | 40.4738 | 0.3227 | 0.0850 | 58.6840 | 120 |
| halftrend_signals | default | 1 | {} | 434 | 72.3333 | 5.1198 | 3.4479 | -1.8205 | -0.0042 | 3 | -5.6657 | 9.4673 | -0.1873 | 0.3400 | 47.5906 | 4 |
| halftrend_signals | double | 1 | {"amplitude": 100} | 200 | 33.3333 | 4.6300 | -9.5757 | -11.9430 | -0.0597 | 1 | -3.9087 | 12.0765 | -3.0274 | 0.5950 | 41.9060 | 7 |
| halftrend_signals | half | 1 | {"amplitude": 25} | 714 | 119.0000 | 5.0140 | -24.0557 | -32.2428 | -0.0452 | 1 | -11.0782 | 21.1646 | -1.8719 | 0.5950 | 71.4377 | 12 |
| hieken_ashi_smoothed_signals | default | 1 | {} | 5131 | 855.1667 | 5.1674 | 110.7145 | 46.5477 | 0.0091 | 3 | -39.0637 | 52.1945 | 0.5106 | 0.0600 | 50.9665 | 126 |
| hieken_ashi_smoothed_signals | double | 1 | {"ma_len1": 16} | 3479 | 579.8333 | 5.1845 | -25.2535 | -66.9208 | -0.0192 | 2 | -37.2966 | 79.9021 | -1.4200 | 0.3450 | 96.6289 | 70 |
| hieken_ashi_smoothed_signals | half | 1 | {"ma_len1": 4} | 6389 | 1064.8333 | 5.0819 | 200.5943 | 121.7305 | 0.0191 | 5 | -5.4305 | 5.4305 | 1.5167 | 0.0350 | 82.9332 | 133 |
| ichimoku_signals | default | 1 | {} | 1691 | 281.8333 | 5.4654 | 53.3863 | 31.9846 | 0.0189 | 4 | -13.4477 | 16.2279 | 0.7991 | 0.1700 | 88.2176 | 57 |
| ichimoku_signals | double | 1 | {"conversion_len": 18} | 2358 | 393.0000 | 5.3109 | 8.5752 | -20.5274 | -0.0087 | 3 | -26.1728 | 15.3654 | -0.5239 | 0.2950 | 110.9884 | 47 |
| ichimoku_signals | half | 1 | {"conversion_len": 4} | 1824 | 304.0000 | 5.5707 | 90.3650 | 67.7565 | 0.0371 | 3 | -11.8274 | 17.1860 | 1.2569 | 0.0900 | 87.4471 | 46 |
| j_tpo_signals | default | 1 | {} | 2346 | 391.0000 | 5.3171 | 22.8628 | -5.7009 | -0.0024 | 3 | -55.3295 | 55.3295 | -0.0719 | 0.2600 | 86.2162 | 47 |
| j_tpo_signals | double | 1 | {"len": 80} | 1127 | 187.8333 | 5.4658 | 5.8049 | -7.6290 | -0.0068 | 2 | -12.5220 | 15.5626 | -0.3122 | 0.3200 | 67.2788 | 44 |
| j_tpo_signals | half | 1 | {"len": 20} | 4495 | 749.1667 | 5.1141 | 96.4922 | 40.7631 | 0.0091 | 3 | -25.7421 | 43.0984 | 0.5831 | 0.0750 | 67.8124 | 112 |
| kalman_filter_signals | default | 1 | {} | 2810 | 468.3333 | 5.2302 | 14.4524 | -20.5665 | -0.0073 | 3 | -35.2692 | 67.2264 | -0.3089 | 0.2750 | 72.5559 | 64 |
| kalman_filter_signals | double | 1 | {"sharpness": 0.5, "k": 0.5} | 1984 | 330.6667 | 5.3508 | -7.5592 | -31.9660 | -0.0161 | 1 | -32.1806 | 32.1806 | -0.6261 | 0.3450 | 79.3720 | 50 |
| kalman_filter_signals | half | 1 | {"sharpness": 2.0, "k": 2.0} | 3980 | 663.3333 | 5.4636 | 147.6496 | 98.1297 | 0.0247 | 5 | -0.9359 | 0.9359 | 1.5477 | 0.0300 | 65.3557 | 91 |
| kase_peak_oscillator_signals | default | 1 | {} | 4706 | 784.3333 | 4.9751 | 46.0855 | -10.3368 | -0.0022 | 3 | -22.2644 | 13.7690 | -0.3126 | 0.1250 | 45.9214 | 93 |
| kase_peak_oscillator_signals | double | 1 | {"short_cycle": 16} | 3577 | 596.1667 | 4.8230 | -16.6450 | -59.1245 | -0.0165 | 1 | -25.2065 | 42.0882 | -2.3685 | 0.2800 | 66.3915 | 75 |
| kase_peak_oscillator_signals | half | 1 | {"short_cycle": 4} | 6532 | 1088.6667 | 4.8097 | 105.2003 | 27.2091 | 0.0042 | 3 | -27.1658 | 18.8530 | 0.3923 | 0.0500 | 26.7943 | 116 |
| kuskus_starlight_signals | default | 1 | {} | 4906 | 817.6667 | 4.8341 | 74.0092 | 15.4194 | 0.0031 | 3 | -14.9533 | 6.2223 | 0.4764 | 0.1050 | 78.5265 | 93 |
| kuskus_starlight_signals | double | 1 | {"range_periods": 60} | 3480 | 580.0000 | 4.7526 | -19.1319 | -60.3058 | -0.0173 | 2 | -36.9549 | 61.7618 | -1.1345 | 0.3100 | 67.1130 | 75 |
| kuskus_starlight_signals | half | 1 | {"range_periods": 15} | 7108 | 1184.6667 | 4.7631 | 114.7355 | 29.8829 | 0.0042 | 4 | -4.2617 | 4.2617 | 1.2758 | 0.0450 | 10.1022 | 126 |
| laguerre_filter_signals | default | 1 | {} | 2563 | 427.1667 | 5.1436 | -6.7133 | -37.6195 | -0.0147 | 2 | -27.7309 | 42.8918 | -0.7280 | 0.3000 | 83.9511 | 49 |
| laguerre_filter_signals | double | 1 | {"alpha": 0.1} | 1192 | 198.6667 | 5.3490 | 41.1828 | 26.6394 | 0.0223 | 4 | -8.5940 | 7.7018 | 1.0115 | 0.1750 | 78.9214 | 22 |
| laguerre_filter_signals | half | 1 | {"alpha": 0.4} | 5165 | 860.8333 | 5.2372 | 164.2470 | 101.0798 | 0.0196 | 5 | -10.5394 | 10.5394 | 1.6275 | 0.0150 | 54.1617 | 110 |
| lemantrend_signals | default | 1 | {} | 2458 | 409.6667 | 4.5618 | 33.8443 | 3.6688 | 0.0015 | 3 | -13.2908 | 13.2908 | 0.0967 | 0.1800 | 75.8647 | 48 |
| lemantrend_signals | double | 1 | {"slow_period": 26} | 1785 | 297.5000 | 4.8801 | 29.3838 | 7.8528 | 0.0044 | 2 | -20.6877 | 22.5213 | 0.1573 | 0.1750 | 99.7681 | 34 |
| lemantrend_signals | half | 1 | {"slow_period": 6} | 3279 | 546.5000 | 4.3425 | 1.9905 | -38.3451 | -0.0117 | 2 | -17.6244 | 33.3001 | -1.7378 | 0.2950 | 76.9579 | 53 |
| linreg_slope_signals | default | 1 | {} | 5511 | 918.5000 | 5.4135 | 215.6186 | 148.3406 | 0.0269 | 5 | -23.0551 | 23.0551 | 1.7923 | 0.0100 | 39.8593 | 132 |
| linreg_slope_signals | double | 1 | {"length": 28} | 2952 | 492.0000 | 5.4424 | -2.7727 | -38.5440 | -0.0131 | 2 | -35.5186 | 35.5186 | -0.7742 | 0.3150 | 90.7256 | 68 |
| linreg_slope_signals | half | 1 | {"length": 7} | 10180 | 1696.6667 | 4.6152 | 93.4847 | -30.3891 | -0.0030 | 3 | -40.0324 | 26.6812 | -0.4385 | 0.0650 | -0.9699 | 199 |
| mama_fama_signals | default | 1 | {} | 3780 | 630.0000 | 5.2508 | 72.3948 | 25.5242 | 0.0068 | 4 | -20.8264 | 33.8587 | 0.4567 | 0.1350 | 77.5539 | 76 |
| mama_fama_signals | double | 1 | {"fast_limit": 0.25, "slow_limit": 0.025} | 1840 | 306.6667 | 5.3902 | -8.6675 | -31.4524 | -0.0171 | 1 | -27.2693 | 46.9341 | -0.4906 | 0.3350 | 71.7664 | 32 |
| mama_fama_signals | half | 1 | {"fast_limit": 1.0, "slow_limit": 0.1} | 8181 | 1363.5000 | 4.5029 | 155.3974 | 55.4738 | 0.0068 | 5 | -10.2448 | 0.0000 | 1.2279 | 0.0250 | -11.8402 | 150 |
| parabolic_sar_signals | default | 1 | {} | 8127 | 1354.5000 | 4.9915 | 93.1121 | -5.0030 | -0.0006 | 3 | -63.2572 | 25.9665 | -0.0542 | 0.0700 | 8.5863 | 170 |
| parabolic_sar_signals | double | 1 | {"sar_start": 0.01, "sar_increment": 0.01} | 5248 | 874.6667 | 5.1803 | 95.8289 | 32.1243 | 0.0061 | 4 | -22.4336 | 22.4336 | 0.4572 | 0.0850 | 73.6804 | 125 |
| parabolic_sar_signals | half | 1 | {"sar_start": 0.04, "sar_increment": 0.04} | 11675 | 1945.8333 | 4.2218 | 104.4654 | -36.8365 | -0.0032 | 2 | -74.5688 | 56.3644 | -0.3216 | 0.0350 | -87.2228 | 191 |
| polychromatic_momentum_signals | default | 1 | {} | 3581 | 596.8333 | 5.0639 | 38.4174 | -6.9126 | -0.0019 | 2 | -38.9359 | 83.8425 | -0.0755 | 0.1500 | 89.5440 | 70 |
| polychromatic_momentum_signals | double | 1 | {"len": 28} | 1756 | 292.6667 | 5.2306 | -42.5969 | -63.7309 | -0.0363 | 1 | -37.3252 | 41.8622 | -1.0580 | 0.5850 | 102.6021 | 48 |
| polychromatic_momentum_signals | half | 1 | {"len": 7} | 6771 | 1128.5000 | 4.8798 | 182.5686 | 98.2466 | 0.0145 | 5 | -1.5516 | 1.5516 | 1.5790 | 0.0150 | -5.9430 | 130 |
| price_momentum_oscillator_signals | default | 1 | {} | 2167 | 361.1667 | 5.2026 | -1.2871 | -27.7682 | -0.0128 | 3 | -25.9085 | 33.1112 | -0.6605 | 0.3550 | 83.8555 | 49 |
| price_momentum_oscillator_signals | double | 1 | {"s1": 70} | 1510 | 251.6667 | 5.3954 | -4.9952 | -23.4049 | -0.0155 | 2 | -19.9169 | 20.0418 | -0.5562 | 0.3300 | 79.1946 | 29 |
| price_momentum_oscillator_signals | half | 1 | {"s1": 18} | 3032 | 505.3333 | 5.1336 | -2.5347 | -39.5588 | -0.0130 | 2 | -19.1448 | 42.6767 | -1.7564 | 0.3150 | 73.6024 | 71 |
| qqe_mod_signals | default | 1 | {} | 5495 | 915.8333 | 5.0286 | 124.2023 | 56.2249 | 0.0102 | 3 | -14.7485 | 17.3947 | 0.8774 | 0.0750 | 84.5746 | 122 |
| qqe_mod_signals | double | 1 | {"rsi_period": 12} | 4010 | 668.3333 | 5.1372 | 64.8504 | 15.0698 | 0.0038 | 1 | -17.2754 | 41.5693 | 0.2237 | 0.1500 | 100.0527 | 93 |
| qqe_mod_signals | half | 1 | {"rsi_period": 3} | 7614 | 1269.0000 | 4.6534 | 103.6057 | 9.6856 | 0.0013 | 3 | -23.5250 | 16.3399 | 0.1657 | 0.0450 | 6.3652 | 151 |
| relative_vigor_index_signals | default | 1 | {} | 15258 | 2543.0000 | 3.0893 | -46.8201 | -234.6888 | -0.0154 | 1 | -80.8267 | 264.6334 | -1.9617 | 0.1100 | -176.4267 | 211 |
| relative_vigor_index_signals | double | 1 | {"len": 20} | 15386 | 2564.3333 | 3.0254 | 106.0944 | -84.6018 | -0.0055 | 2 | -94.4248 | 116.5480 | -0.7644 | 0.0100 | -205.7712 | 179 |
| relative_vigor_index_signals | half | 1 | {"len": 5} | 16527 | 2754.5000 | 3.1764 | 130.0584 | -72.3845 | -0.0044 | 3 | -92.2034 | 232.4768 | -0.3764 | 0.0150 | -191.9760 | 189 |
| rex_oscillator_signals | default | 1 | {} | 15297 | 2549.5000 | 2.9879 | 243.6157 | 57.6777 | 0.0038 | 2 | -42.1538 | 62.7830 | 0.3424 | 0.0000 | -176.0910 | 208 |
| rex_oscillator_signals | double | 1 | {"smooth": 26} | 20180 | 3363.3333 | 2.5715 | -2.1442 | -251.9101 | -0.0125 | 2 | -138.6494 | 170.2320 | -1.5687 | 0.0250 | -330.5260 | 168 |
| rex_oscillator_signals | half | 1 | {"smooth": 6} | 16885 | 2814.1667 | 2.9977 | 35.0394 | -169.4139 | -0.0100 | 1 | -87.9271 | 164.6749 | -1.8680 | 0.0250 | -228.4645 | 217 |
| schaff_trend_cycle_signals | default | 1 | {} | 3289 | 548.1667 | 4.9611 | 67.7342 | 28.5659 | 0.0087 | 3 | -26.7836 | 28.3276 | 0.4248 | 0.1250 | 78.7908 | 64 |
| schaff_trend_cycle_signals | double | 1 | {"macdFast": 46} | 3085 | 514.1667 | 4.9789 | -29.2986 | -65.6566 | -0.0213 | 1 | -25.1226 | 62.9689 | -2.5984 | 0.4000 | 74.6083 | 63 |
| schaff_trend_cycle_signals | half | 1 | {"macdFast": 12} | 3488 | 581.3333 | 5.0459 | 102.9524 | 60.4809 | 0.0173 | 3 | -18.9023 | 20.6521 | 0.8117 | 0.0850 | 68.0573 | 63 |
| ssl_channel_signals | default | 1 | {} | 6989 | 1164.8333 | 5.2792 | 143.3569 | 59.8216 | 0.0086 | 4 | -35.3198 | 11.0920 | 0.8535 | 0.0350 | 19.9793 | 163 |
| ssl_channel_signals | double | 1 | {"len": 20} | 4986 | 831.0000 | 5.4619 | 100.7200 | 39.9838 | 0.0080 | 2 | -20.8965 | 20.8965 | 0.7185 | 0.0700 | 53.4971 | 101 |
| ssl_channel_signals | half | 1 | {"len": 5} | 9901 | 1650.1667 | 4.5012 | 51.9022 | -65.6655 | -0.0066 | 3 | -67.8091 | 44.1648 | -0.7362 | 0.0500 | -66.0450 | 187 |
| supertrend_signals | default | 1 | {} | 2233 | 372.1667 | 5.3063 | -13.2606 | -39.6364 | -0.0178 | 1 | -23.0096 | 36.4174 | -1.5115 | 0.3200 | 57.3782 | 40 |
| supertrend_signals | double | 1 | {"atr_period": 20} | 2206 | 367.6667 | 5.3083 | -25.2918 | -51.0499 | -0.0231 | 0 | -15.1553 | 40.9074 | -3.4871 | 0.4550 | 107.3786 | 37 |
| supertrend_signals | half | 1 | {"atr_period": 5} | 2318 | 386.3333 | 5.4314 | -3.5356 | -31.3684 | -0.0135 | 2 | -12.7858 | 24.1340 | -1.5875 | 0.3100 | 76.7724 | 51 |
| trend_direction_force_index_signals | default | 1 | {} | 4630 | 771.6667 | 5.3525 | 15.1871 | -40.5233 | -0.0088 | 2 | -50.6975 | 75.1115 | -0.4979 | 0.2000 | 76.7562 | 135 |
| trend_direction_force_index_signals | double | 1 | {"lookback": 26} | 3056 | 509.3333 | 5.1443 | 35.8610 | -0.5476 | -0.0002 | 3 | -9.6808 | 9.6808 | -0.0213 | 0.2450 | 96.3807 | 57 |
| trend_direction_force_index_signals | half | 1 | {"lookback": 6} | 7046 | 1174.3333 | 5.3806 | 101.0021 | 14.8186 | 0.0021 | 3 | -38.0798 | 38.0798 | 0.1555 | 0.0650 | 21.0983 | 144 |
| volatility_quality_signals | default | 1 | {} | 4056 | 676.0000 | 5.6053 | 129.0282 | 81.2981 | 0.0200 | 5 | -9.5076 | 9.5076 | 1.5026 | 0.0400 | 74.8213 | 99 |
| volatility_quality_signals | double | 1 | {"smooth": 20} | 1474 | 245.6667 | 5.1967 | -32.9480 | -50.2832 | -0.0341 | 1 | -16.4701 | 40.5620 | -2.7446 | 0.5650 | 72.6121 | 33 |
| volatility_quality_signals | half | 1 | {"smooth": 5} | 10212 | 1702.0000 | 4.3363 | 71.9483 | -48.6391 | -0.0048 | 4 | -56.2924 | 56.2924 | -0.5197 | 0.0500 | -69.7456 | 202 |
| vortex_signals | default | 1 | {} | 8249 | 1374.8333 | 3.9134 | 154.8819 | 48.9879 | 0.0059 | 3 | -24.1605 | 37.5448 | 0.6036 | 0.0150 | -47.5622 | 121 |
| vortex_signals | double | 1 | {"period": 28} | 6088 | 1014.6667 | 3.7684 | 18.7992 | -60.6698 | -0.0100 | 2 | -49.5076 | 51.9115 | -0.7987 | 0.1600 | 22.5485 | 96 |
| vortex_signals | half | 1 | {"period": 7} | 11835 | 1972.5000 | 3.7709 | 88.2945 | -57.2363 | -0.0048 | 3 | -65.8729 | 51.3255 | -0.5572 | 0.0500 | -65.8363 | 195 |
| waddah_attar_explosion_signals | default | 1 | {} | 1997 | 332.8333 | 4.9344 | 27.0399 | 3.1771 | 0.0016 | 2 | -21.7599 | 27.3124 | 0.0534 | 0.1950 | 97.4138 | 36 |
| waddah_attar_explosion_signals | double | 1 | {"sensitivity": 300} | 1998 | 333.0000 | 4.8734 | 43.3510 | 19.5259 | 0.0098 | 2 | -16.8012 | 23.0652 | 0.3386 | 0.1550 | 71.9945 | 36 |
| waddah_attar_explosion_signals | half | 1 | {"sensitivity": 75} | 2015 | 335.8333 | 5.0486 | 49.6630 | 25.5599 | 0.0127 | 2 | -14.2127 | 18.3275 | 0.4044 | 0.1100 | 73.5747 | 41 |


---


# BASELINE — all 15 candidates


## BASELINE — flip_only, walk-forward pick, BUILD years 2010-2015

`n_settings_used` is how many different settings the six steps chose. A candidate whose steps keep switching setting is being fitted, not measured.

| indicator | R_net_build | n | R_per_trade | trades_per_year | mean_bars | years_positive | worst_year | best_year | worst_dip_R | t_yearly | settings_used | n_settings_used | clears_alone | clears_best_of_family |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|
| lsma_baseline | 211.6939 | 18262.0000 | 0.0116 | 3043.6667 | 5.5870 | 4 | -44.1391 | 127.9265 | 9.2392 | 1.2890 | double,half | 2 | 0 | 0 |
| fantail_vma | 201.9924 | 13238.0000 | 0.0153 | 2206.3333 | 6.5966 | 4 | -16.1849 | 71.4005 | 16.1849 | 2.1359 | default,double | 2 | 1 | 0 |
| vidya | 168.3253 | 19590.0000 | 0.0086 | 3265.0000 | 4.4600 | 4 | -36.8190 | 99.4834 | 8.3234 | 1.4215 | default | 1 | 0 | 0 |
| hma_baseline | 85.9991 | 17812.0000 | 0.0048 | 2968.6667 | 5.0243 | 3 | -108.6094 | 117.0289 | 164.3166 | 0.3936 | default,double | 2 | 0 | 0 |
| alma_baseline | 85.2347 | 25228.0000 | 0.0034 | 4204.6667 | 3.8196 | 4 | -48.8004 | 66.1709 | 48.8004 | 0.6623 | default,double,half | 3 | 0 | 0 |
| frama_baseline | 58.6062 | 15034.0000 | 0.0039 | 2505.6667 | 5.8149 | 3 | -68.2747 | 95.6143 | 73.1451 | 0.4420 | default,double,half | 3 | 0 | 0 |
| super_smoother_2pole_baseline | 13.4873 | 22600.0000 | 0.0006 | 3766.6667 | 4.2218 | 2 | -58.1569 | 60.8163 | 66.7992 | 0.1121 | default,double,half | 3 | 0 | 0 |
| kama_baseline | -0.4107 | 14020.0000 | -0.0000 | 2336.6667 | 6.6595 | 3 | -62.1797 | 52.8803 | 71.9036 | -0.0040 | double,half | 2 | 0 | 0 |
| rma_baseline | -38.0861 | 8282.0000 | -0.0046 | 1380.3333 | 10.8375 | 3 | -102.7859 | 51.9717 | 102.7859 | -0.2867 | default,double,half | 3 | 0 | 0 |
| ema_baseline | -42.8439 | 12654.0000 | -0.0034 | 2109.0000 | 7.6385 | 2 | -93.6941 | 51.4990 | 93.6941 | -0.3586 | double,half | 2 | 0 | 0 |
| t3_baseline | -49.5624 | 18948.0000 | -0.0026 | 3158.0000 | 5.3633 | 3 | -165.1140 | 106.1355 | 238.7058 | -0.1987 | double,half | 2 | 0 | 0 |
| wma_baseline | -72.9190 | 15800.0000 | -0.0046 | 2633.3333 | 6.1510 | 2 | -105.9296 | 60.2117 | 105.9296 | -0.4628 | double,half | 2 | 0 | 0 |
| sma_baseline | -99.5629 | 10778.0000 | -0.0092 | 1796.3333 | 8.8929 | 2 | -124.4756 | 77.7242 | 124.4756 | -0.5703 | default,double,half | 3 | 0 | 0 |
| tma_baseline | -108.0687 | 12926.0000 | -0.0084 | 2154.3333 | 7.6808 | 3 | -134.8543 | 56.9202 | 134.8543 | -0.5830 | double,half | 2 | 0 | 0 |
| mcginley_dynamic_index | -117.4496 | 9704.0000 | -0.0121 | 1617.3333 | 9.9028 | 2 | -115.3289 | 76.9821 | 115.3289 | -0.7493 | double,half | 2 | 0 | 0 |


### BASELINE — flip_only, ALL THREE SETTINGS UNPICKED

The same six BUILD years with each setting held fixed, so the walk-forward number above can be compared with what any single setting would have done. `null_p` is against the matched random-entry null, 200 draws, matched on trade count and holding period per pair.

| indicator | setting | distinct_setting | params | n | trades_per_year | mean_bars | R_gross_build | R_net_build | R_per_trade_net | years_positive | worst_year | worst_dip_R | t_yearly | null_p | null_p95 | straddles |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| alma_baseline | default | 1 | {} | 26984 | 4497.3333 | 3.2339 | 97.5900 | 97.3402 | 0.0036 | 4 | -90.4226 | 90.4226 | 0.5761 | 0.4150 | 455.0972 | 336 |
| alma_baseline | double | 1 | {"length": 18} | 18186 | 3031.0000 | 4.7873 | 100.0711 | 99.9025 | 0.0055 | 3 | -45.0912 | 22.6730 | 0.8932 | 0.3300 | 389.2146 | 336 |
| alma_baseline | half | 1 | {"length": 4} | 41532 | 6922.0000 | 2.1036 | -43.8517 | -44.2319 | -0.0011 | 3 | -123.0153 | 228.6191 | -0.2170 | 0.6000 | 464.5525 | 336 |
| ema_baseline | default | 1 | {} | 11766 | 1961.0000 | 7.3859 | 26.5091 | 26.4018 | 0.0022 | 4 | -75.7708 | 75.7708 | 0.2279 | 0.4400 | 421.5565 | 336 |
| ema_baseline | double | 1 | {"ma_length": 40} | 8348 | 1391.3333 | 10.4032 | 19.4266 | 19.3499 | 0.0023 | 4 | -93.6941 | 93.6941 | 0.1511 | 0.5600 | 418.8181 | 336 |
| ema_baseline | half | 1 | {"ma_length": 10} | 16500 | 2750.0000 | 5.2785 | 54.3267 | 54.1743 | 0.0033 | 2 | -13.8614 | 9.2298 | 0.7409 | 0.4700 | 399.0064 | 336 |
| fantail_vma | default | 1 | {} | 13282 | 2213.6667 | 6.5550 | 215.9258 | 215.8029 | 0.0162 | 4 | -16.1849 | 16.1849 | 2.1460 | 0.2350 | 446.3199 | 336 |
| fantail_vma | double | 1 | {"fma_adx_length": 4} | 13084 | 2180.6667 | 6.6512 | 155.8937 | 155.7725 | 0.0119 | 4 | -33.3689 | 33.3689 | 1.3944 | 0.2500 | 416.5730 | 336 |
| fantail_vma | half | 0 | {"fma_adx_length": 2} | 13282 | 2213.6667 | 6.5550 | 215.9258 | 215.8029 | 0.0162 | 4 | -16.1849 | 16.1849 | 2.1460 | 0.2350 | 446.3199 | 336 |
| frama_baseline | default | 1 | {} | 15886 | 2647.6667 | 5.4779 | 122.6896 | 122.5435 | 0.0077 | 4 | -68.2747 | 68.2747 | 0.8877 | 0.3650 | 434.7574 | 336 |
| frama_baseline | double | 1 | {"length": 20} | 15324 | 2554.0000 | 5.6879 | -17.2007 | -17.3427 | -0.0011 | 3 | -62.1222 | 66.9927 | -0.2185 | 0.5500 | 412.7539 | 336 |
| frama_baseline | half | 1 | {"length": 5} | 13822 | 2303.6667 | 6.2816 | 116.6551 | 116.5286 | 0.0084 | 4 | -92.0675 | 92.0675 | 0.7032 | 0.3350 | 359.6258 | 336 |
| hma_baseline | default | 1 | {} | 19106 | 3184.3333 | 4.5631 | 45.0396 | 44.8608 | 0.0023 | 3 | -108.6094 | 164.3166 | 0.2182 | 0.4550 | 447.1268 | 336 |
| hma_baseline | double | 1 | {"ma_length": 40} | 12792 | 2132.0000 | 6.8247 | 288.0074 | 287.8892 | 0.0225 | 6 | 6.5971 | 0.0000 | 3.8647 | 0.0950 | 438.2367 | 336 |
| hma_baseline | half | 1 | {"ma_length": 10} | 28294 | 4715.6667 | 3.0872 | -184.0497 | -184.3089 | -0.0065 | 3 | -234.7567 | 284.0396 | -0.6272 | 0.7400 | 410.1877 | 336 |
| kama_baseline | default | 1 | {} | 12482 | 2080.3333 | 6.9636 | 18.3886 | 18.2763 | 0.0015 | 3 | -46.8851 | 21.3198 | 0.2087 | 0.4650 | 378.8894 | 336 |
| kama_baseline | double | 1 | {"length": 20} | 9312 | 1552.0000 | 9.3540 | 51.4262 | 51.3428 | 0.0055 | 4 | -22.2973 | 22.2973 | 0.7656 | 0.4200 | 400.0482 | 336 |
| kama_baseline | half | 1 | {"length": 5} | 16480 | 2746.6667 | 5.2769 | 71.5653 | 71.4153 | 0.0043 | 4 | -62.1797 | 71.9036 | 0.6003 | 0.3950 | 413.8179 | 336 |
| lsma_baseline | default | 1 | {} | 16602 | 2767.0000 | 5.2425 | 320.1479 | 319.9936 | 0.0193 | 5 | -21.2475 | 0.0000 | 2.4548 | 0.1100 | 382.8206 | 336 |
| lsma_baseline | double | 1 | {"length": 40} | 11516 | 1919.3333 | 7.5809 | 202.4876 | 202.3821 | 0.0176 | 5 | -9.2392 | 9.2392 | 1.6795 | 0.2100 | 396.1423 | 336 |
| lsma_baseline | half | 1 | {"length": 10} | 25560 | 4260.0000 | 3.4177 | -119.6851 | -119.9205 | -0.0047 | 3 | -146.0520 | 227.0305 | -0.5499 | 0.7000 | 396.3811 | 336 |
| mcginley_dynamic_index | default | 1 | {} | 9962 | 1660.3333 | 8.7292 | 67.3887 | 67.2981 | 0.0068 | 4 | -82.2239 | 82.2239 | 0.5263 | 0.4350 | 392.5149 | 336 |
| mcginley_dynamic_index | double | 1 | {"mci_length": 28} | 7126 | 1187.6667 | 12.1524 | -3.5894 | -3.6543 | -0.0005 | 3 | -115.3289 | 115.3289 | -0.0200 | 0.5000 | 436.4827 | 336 |
| mcginley_dynamic_index | half | 1 | {"mci_length": 7} | 14484 | 2414.0000 | 6.0039 | 88.7077 | 88.5739 | 0.0061 | 3 | -24.9291 | 24.9291 | 0.8267 | 0.3150 | 409.9492 | 336 |
| rma_baseline | default | 1 | {} | 8492 | 1415.3333 | 10.2273 | 30.4861 | 30.4086 | 0.0036 | 4 | -91.9025 | 91.9025 | 0.2404 | 0.4850 | 409.6336 | 336 |
| rma_baseline | double | 1 | {"ma_length": 40} | 6094 | 1015.6667 | 14.3226 | -17.2989 | -17.3532 | -0.0028 | 2 | -102.7859 | 111.3811 | -0.1036 | 0.4650 | 310.7608 | 336 |
| rma_baseline | half | 1 | {"ma_length": 10} | 11998 | 1999.6667 | 7.2440 | 30.3621 | 30.2522 | 0.0025 | 3 | -66.2648 | 66.2648 | 0.2714 | 0.4250 | 414.6074 | 336 |
| sma_baseline | default | 1 | {} | 10400 | 1733.3333 | 8.3679 | 77.3503 | 77.2543 | 0.0074 | 4 | -72.3468 | 72.3468 | 0.6064 | 0.3800 | 420.1527 | 336 |
| sma_baseline | double | 1 | {"length": 40} | 7324 | 1220.6667 | 11.8831 | 8.1954 | 8.1271 | 0.0011 | 4 | -124.4756 | 124.4756 | 0.0473 | 0.4400 | 363.7259 | 336 |
| sma_baseline | half | 1 | {"length": 10} | 15408 | 2568.0000 | 5.6456 | 51.8448 | 51.7018 | 0.0034 | 3 | -63.8534 | 7.0658 | 0.4919 | 0.4200 | 377.6574 | 336 |
| super_smoother_2pole_baseline | default | 1 | {} | 19104 | 3184.0000 | 4.5613 | 87.6124 | 87.4355 | 0.0046 | 3 | -58.1569 | 62.9281 | 0.5646 | 0.3550 | 383.3625 | 336 |
| super_smoother_2pole_baseline | double | 1 | {"cutoff_period": 30} | 12692 | 2115.3333 | 6.8598 | 113.7305 | 113.6133 | 0.0090 | 4 | -15.2668 | 15.2668 | 1.3205 | 0.2700 | 397.4083 | 336 |
| super_smoother_2pole_baseline | half | 1 | {"cutoff_period": 8} | 28364 | 4727.3333 | 3.0773 | -167.3771 | -167.6394 | -0.0059 | 2 | -189.3178 | 276.8333 | -0.6763 | 0.7200 | 385.1980 | 336 |
| t3_baseline | default | 1 | {} | 13408 | 2234.6667 | 6.5021 | 115.6878 | 115.5632 | 0.0086 | 4 | -17.5791 | 17.5791 | 1.4170 | 0.3550 | 423.2491 | 336 |
| t3_baseline | double | 1 | {"length": 20} | 8610 | 1435.0000 | 10.1168 | 37.6111 | 37.5311 | 0.0044 | 4 | -98.2202 | 98.2202 | 0.2295 | 0.4450 | 447.0916 | 336 |
| t3_baseline | half | 1 | {"length": 5} | 21146 | 3524.3333 | 4.1221 | -57.1122 | -57.3086 | -0.0027 | 3 | -165.1140 | 238.7058 | -0.2337 | 0.6300 | 335.2735 | 336 |
| tma_baseline | default | 1 | {} | 10284 | 1714.0000 | 8.4584 | 4.1757 | 4.0808 | 0.0004 | 3 | -74.3525 | 74.3525 | 0.0349 | 0.5400 | 373.4796 | 336 |
| tma_baseline | double | 1 | {"length": 40} | 7048 | 1174.6667 | 12.3365 | -19.9110 | -19.9768 | -0.0028 | 4 | -134.8543 | 134.8543 | -0.1133 | 0.4850 | 437.5797 | 336 |
| tma_baseline | half | 1 | {"length": 10} | 15564 | 2594.0000 | 5.5924 | 73.9879 | 73.8445 | 0.0047 | 4 | -76.5888 | 10.0924 | 0.5761 | 0.3800 | 453.9026 | 336 |
| vidya | default | 1 | {} | 19590 | 3265.0000 | 4.4528 | 168.5035 | 168.3253 | 0.0086 | 4 | -36.8190 | 8.3234 | 1.4215 | 0.2600 | 392.8901 | 336 |
| vidya | double | 1 | {"vda_length": 4} | 15652 | 2608.6667 | 5.5633 | 62.5622 | 62.4200 | 0.0040 | 4 | -47.2153 | 32.9999 | 0.5621 | 0.4400 | 412.5772 | 336 |
| vidya | half | 0 | {"vda_length": 2} | 19590 | 3265.0000 | 4.4528 | 168.5035 | 168.3253 | 0.0086 | 4 | -36.8190 | 8.3234 | 1.4215 | 0.2600 | 392.8901 | 336 |
| wma_baseline | default | 1 | {} | 13210 | 2201.6667 | 6.5871 | 141.9682 | 141.8455 | 0.0107 | 4 | -14.6017 | 14.6017 | 1.7479 | 0.2400 | 396.3298 | 336 |
| wma_baseline | double | 1 | {"ma_length": 40} | 9324 | 1554.0000 | 9.3290 | -5.6846 | -5.7716 | -0.0006 | 3 | -105.9296 | 105.9296 | -0.0408 | 0.4950 | 322.8614 | 336 |
| wma_baseline | half | 1 | {"ma_length": 10} | 18802 | 3133.6667 | 4.6310 | 86.4528 | 86.2782 | 0.0046 | 3 | -42.5548 | 42.7533 | 0.7211 | 0.4000 | 441.5115 | 336 |


## BASELINE — canonical_risk, walk-forward pick, BUILD years 2010-2015

`n_settings_used` is how many different settings the six steps chose. A candidate whose steps keep switching setting is being fitted, not measured.

| indicator | R_net_build | n | R_per_trade | trades_per_year | mean_bars | years_positive | worst_year | best_year | worst_dip_R | t_yearly | settings_used | n_settings_used | clears_alone | clears_best_of_family |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|
| hma_baseline | 37.2327 | 15870.0000 | 0.0023 | 2645.0000 | 3.1760 | 3 | -32.8425 | 57.1606 | 50.2818 | 0.3872 | default,double | 2 | 0 | 0 |
| tma_baseline | 22.3306 | 11220.0000 | 0.0020 | 1870.0000 | 3.5521 | 4 | -61.8740 | 49.9372 | 16.8309 | 0.2327 | double,half | 2 | 0 | 0 |
| lsma_baseline | 14.8747 | 13022.0000 | 0.0011 | 2170.3333 | 3.2968 | 4 | -30.1480 | 23.0716 | 19.8158 | 0.2690 | default,double | 2 | 0 | 0 |
| rma_baseline | 11.2494 | 8613.0000 | 0.0013 | 1435.5000 | 3.5196 | 3 | -23.5191 | 32.5233 | 23.5191 | 0.2263 | default,double,half | 3 | 0 | 0 |
| sma_baseline | 10.4677 | 10042.0000 | 0.0010 | 1673.6667 | 3.5058 | 3 | -63.9369 | 41.3254 | 8.9788 | 0.1147 | double,half | 2 | 0 | 0 |
| mcginley_dynamic_index | 4.6904 | 8565.0000 | 0.0005 | 1427.5000 | 3.5429 | 4 | -25.9715 | 21.9050 | 35.4208 | 0.0952 | default,double | 2 | 0 | 0 |
| t3_baseline | -23.0058 | 11315.0000 | -0.0020 | 1885.8333 | 3.5068 | 4 | -31.4848 | 24.0694 | 62.3323 | -0.4158 | default,double,half | 3 | 0 | 0 |
| fantail_vma | -24.6905 | 13122.0000 | -0.0019 | 2187.0000 | 3.3251 | 4 | -45.6438 | 25.1614 | 34.6220 | -0.3449 | default,double | 2 | 0 | 0 |
| ema_baseline | -28.8477 | 13276.0000 | -0.0022 | 2212.6667 | 3.2710 | 2 | -52.9294 | 37.7245 | 79.5265 | -0.3712 | default,double,half | 3 | 0 | 0 |
| wma_baseline | -31.8202 | 14142.0000 | -0.0023 | 2357.0000 | 3.2375 | 3 | -26.9528 | 10.3705 | 34.4878 | -0.8704 | default,half | 2 | 0 | 0 |
| frama_baseline | -59.4020 | 15058.0000 | -0.0039 | 2509.6667 | 3.0640 | 3 | -66.8956 | 16.1326 | 74.4658 | -0.8025 | default,double,half | 3 | 0 | 0 |
| vidya | -97.2372 | 19588.0000 | -0.0050 | 3264.6667 | 2.7755 | 2 | -48.8053 | 12.0854 | 99.3827 | -1.6823 | default | 1 | 0 | 0 |
| alma_baseline | -119.9710 | 18187.0000 | -0.0066 | 3031.1667 | 2.9395 | 1 | -55.6774 | 13.3766 | 90.5549 | -1.8538 | double | 1 | 0 | 0 |
| kama_baseline | -147.5761 | 11777.0000 | -0.0125 | 1962.8333 | 3.2528 | 0 | -56.3568 | -4.4412 | 138.9851 | -2.8913 | double,half | 2 | 0 | 0 |
| super_smoother_2pole_baseline | -149.8170 | 17997.0000 | -0.0083 | 2999.5000 | 2.9520 | 2 | -85.9113 | 18.7683 | 155.3922 | -1.5771 | default,double | 2 | 0 | 0 |


### BASELINE — canonical_risk, ALL THREE SETTINGS UNPICKED

The same six BUILD years with each setting held fixed, so the walk-forward number above can be compared with what any single setting would have done. `null_p` is against the matched random-entry null, 200 draws, matched on trade count and holding period per pair.

| indicator | setting | distinct_setting | params | n | trades_per_year | mean_bars | R_gross_build | R_net_build | R_per_trade_net | years_positive | worst_year | worst_dip_R | t_yearly | null_p | null_p95 | straddles |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| alma_baseline | default | 1 | {} | 26976 | 4496.0000 | 2.3158 | 59.2040 | -273.7965 | -0.0101 | 0 | -130.2868 | 246.1979 | -2.3100 | 0.0150 | -514.2716 | 237 |
| alma_baseline | double | 1 | {"length": 18} | 18187 | 3031.1667 | 2.9370 | 104.7825 | -119.9710 | -0.0066 | 1 | -55.6774 | 90.5549 | -1.8538 | 0.0300 | -250.3793 | 210 |
| alma_baseline | half | 1 | {"length": 4} | 41516 | 6919.3333 | 1.6926 | 108.3259 | -398.5092 | -0.0096 | 1 | -141.5348 | 423.4404 | -2.7364 | 0.0000 | -872.0023 | 261 |
| ema_baseline | default | 1 | {} | 11769 | 1961.5000 | 3.3753 | 102.0687 | -40.9973 | -0.0035 | 2 | -33.5236 | 57.9442 | -0.7669 | 0.0150 | -120.7517 | 145 |
| ema_baseline | double | 1 | {"ma_length": 40} | 8346 | 1391.0000 | 3.5345 | 118.3496 | 16.1370 | 0.0019 | 4 | -26.1030 | 28.0441 | 0.2898 | 0.0250 | -53.4287 | 109 |
| ema_baseline | half | 1 | {"ma_length": 10} | 16499 | 2749.8333 | 2.9959 | 80.4123 | -122.6945 | -0.0074 | 0 | -52.9294 | 99.1536 | -2.6380 | 0.0200 | -172.7815 | 189 |
| fantail_vma | default | 1 | {} | 13285 | 2214.1667 | 3.3268 | 136.4720 | -27.4055 | -0.0021 | 4 | -45.6438 | 44.3588 | -0.3533 | 0.0300 | -89.4148 | 190 |
| fantail_vma | double | 1 | {"fma_adx_length": 4} | 13088 | 2181.3333 | 3.3288 | 125.8456 | -35.7636 | -0.0027 | 3 | -41.9859 | 36.8463 | -0.5377 | 0.0250 | -123.0327 | 180 |
| fantail_vma | half | 0 | {"fma_adx_length": 2} | 13285 | 2214.1667 | 3.3268 | 136.4720 | -27.4055 | -0.0021 | 4 | -45.6438 | 44.3588 | -0.3533 | 0.0300 | -89.4148 | 190 |
| frama_baseline | default | 1 | {} | 15891 | 2648.5000 | 3.0255 | 107.7045 | -87.0660 | -0.0055 | 2 | -66.8956 | 73.7243 | -1.2257 | 0.0050 | -227.7854 | 201 |
| frama_baseline | double | 1 | {"length": 20} | 15326 | 2554.3333 | 2.9977 | 67.4069 | -121.8628 | -0.0080 | 1 | -58.6338 | 111.7057 | -2.1751 | 0.0200 | -175.9427 | 169 |
| frama_baseline | half | 1 | {"length": 5} | 13834 | 2305.6667 | 3.1641 | 137.1009 | -31.5440 | -0.0023 | 3 | -61.0696 | 67.0334 | -0.4474 | 0.0150 | -153.3123 | 193 |
| hma_baseline | default | 1 | {} | 19101 | 3183.5000 | 2.8841 | 97.4034 | -140.8860 | -0.0074 | 2 | -99.4987 | 176.6358 | -1.0748 | 0.0100 | -276.8085 | 236 |
| hma_baseline | double | 1 | {"ma_length": 40} | 12787 | 2131.1667 | 3.4801 | 212.1178 | 54.4604 | 0.0043 | 4 | -26.4472 | 26.4472 | 0.7862 | 0.0050 | -117.8153 | 182 |
| hma_baseline | half | 1 | {"ma_length": 10} | 28277 | 4712.8333 | 2.3384 | -17.9134 | -363.3274 | -0.0128 | 1 | -123.2358 | 302.7627 | -3.0736 | 0.0050 | -533.0540 | 237 |
| kama_baseline | default | 1 | {} | 12487 | 2081.1667 | 3.3321 | 70.5575 | -79.2751 | -0.0063 | 2 | -41.1288 | 58.1469 | -1.4495 | 0.0250 | -112.6033 | 172 |
| kama_baseline | double | 1 | {"length": 20} | 9312 | 1552.0000 | 3.4201 | 65.9844 | -45.1619 | -0.0048 | 1 | -21.8444 | 58.3874 | -1.1699 | 0.0650 | -25.7123 | 107 |
| kama_baseline | half | 1 | {"length": 5} | 16483 | 2747.1667 | 2.9990 | 74.4785 | -125.4783 | -0.0076 | 1 | -56.3568 | 110.2702 | -2.0954 | 0.0300 | -202.1913 | 202 |
| lsma_baseline | default | 1 | {} | 16607 | 2767.8333 | 3.0541 | 165.2850 | -40.4972 | -0.0024 | 3 | -51.1411 | 76.2587 | -0.4107 | 0.0150 | -165.9317 | 216 |
| lsma_baseline | double | 1 | {"length": 40} | 11509 | 1918.1667 | 3.3961 | 98.7267 | -41.8006 | -0.0036 | 3 | -32.2098 | 52.0256 | -0.7228 | 0.0150 | -111.3944 | 171 |
| lsma_baseline | half | 1 | {"length": 10} | 25548 | 4258.0000 | 2.4879 | 8.1724 | -305.6055 | -0.0120 | 1 | -113.2249 | 299.1700 | -2.5046 | 0.0050 | -441.7413 | 239 |
| mcginley_dynamic_index | default | 1 | {} | 9963 | 1660.5000 | 3.4880 | 133.9502 | 13.1343 | 0.0013 | 3 | -23.8556 | 28.1534 | 0.2406 | 0.0150 | -96.5261 | 123 |
| mcginley_dynamic_index | double | 1 | {"mci_length": 28} | 7130 | 1188.3333 | 3.5961 | 40.8873 | -45.6252 | -0.0064 | 3 | -25.9715 | 49.4669 | -1.2834 | 0.0750 | -7.1003 | 101 |
| mcginley_dynamic_index | half | 1 | {"mci_length": 7} | 14488 | 2414.6667 | 3.1590 | 117.2407 | -61.1843 | -0.0042 | 2 | -36.1452 | 37.0550 | -1.5029 | 0.0100 | -174.9366 | 176 |
| rma_baseline | default | 1 | {} | 8490 | 1415.0000 | 3.4996 | 114.5572 | 11.2441 | 0.0013 | 4 | -23.5191 | 24.7213 | 0.2304 | 0.0350 | -23.9589 | 110 |
| rma_baseline | double | 1 | {"ma_length": 40} | 6101 | 1016.8333 | 3.5470 | 0.4606 | -71.9211 | -0.0118 | 1 | -38.2033 | 55.8692 | -1.9126 | 0.1050 | -35.7833 | 80 |
| rma_baseline | half | 1 | {"ma_length": 10} | 12003 | 2000.5000 | 3.3532 | 96.3560 | -50.2949 | -0.0042 | 2 | -34.9315 | 58.8001 | -1.0235 | 0.0150 | -128.2786 | 147 |
| sma_baseline | default | 1 | {} | 10402 | 1733.6667 | 3.5546 | 137.7661 | 9.6926 | 0.0009 | 3 | -30.8357 | 33.5617 | 0.1934 | 0.0350 | -34.8419 | 133 |
| sma_baseline | double | 1 | {"length": 40} | 7322 | 1220.3333 | 3.6409 | 133.1717 | 42.1654 | 0.0058 | 2 | -18.8802 | 18.8802 | 0.7213 | 0.0100 | -28.0559 | 101 |
| sma_baseline | half | 1 | {"length": 10} | 15407 | 2567.8333 | 3.1722 | 83.3661 | -107.2826 | -0.0070 | 2 | -63.9369 | 53.3471 | -1.5972 | 0.0400 | -130.5008 | 187 |
| super_smoother_2pole_baseline | default | 1 | {} | 19104 | 3184.0000 | 2.8781 | 89.9613 | -145.8470 | -0.0076 | 2 | -85.9113 | 155.3922 | -1.5369 | 0.0050 | -292.7756 | 218 |
| super_smoother_2pole_baseline | double | 1 | {"cutoff_period": 30} | 12692 | 2115.3333 | 3.4364 | 108.8375 | -47.3782 | -0.0037 | 3 | -28.5021 | 26.7025 | -1.2878 | 0.0150 | -106.0934 | 175 |
| super_smoother_2pole_baseline | half | 1 | {"cutoff_period": 8} | 28355 | 4725.8333 | 2.2505 | -42.4648 | -392.1409 | -0.0138 | 0 | -128.9871 | 349.1737 | -4.0221 | 0.0100 | -544.1770 | 237 |
| t3_baseline | default | 1 | {} | 13405 | 2234.1667 | 3.3953 | 115.9662 | -50.0783 | -0.0037 | 3 | -48.5521 | 44.0340 | -0.6493 | 0.0100 | -141.3238 | 180 |
| t3_baseline | double | 1 | {"length": 20} | 8605 | 1434.1667 | 3.6947 | 104.9511 | -1.6809 | -0.0002 | 3 | -30.8475 | 33.2593 | -0.0377 | 0.0450 | -29.0099 | 108 |
| t3_baseline | half | 1 | {"length": 5} | 21143 | 3523.8333 | 2.7030 | 53.7706 | -208.0672 | -0.0098 | 2 | -106.2101 | 198.1669 | -1.8954 | 0.0050 | -400.4377 | 224 |
| tma_baseline | default | 1 | {} | 10284 | 1714.0000 | 3.6971 | 62.1167 | -64.4622 | -0.0063 | 1 | -27.1176 | 54.0612 | -2.4824 | 0.0650 | -38.7869 | 144 |
| tma_baseline | double | 1 | {"length": 40} | 7050 | 1175.0000 | 3.7894 | 117.9604 | 30.1890 | 0.0043 | 4 | -23.6887 | 24.7516 | 0.4713 | 0.0350 | -15.9401 | 98 |
| tma_baseline | half | 1 | {"length": 10} | 15562 | 2593.6667 | 3.2178 | 99.7418 | -91.3404 | -0.0059 | 2 | -61.8740 | 59.4749 | -1.1474 | 0.0100 | -189.0600 | 199 |
| vidya | default | 1 | {} | 19588 | 3264.6667 | 2.7720 | 140.3229 | -97.2372 | -0.0050 | 2 | -48.8053 | 99.3827 | -1.6823 | 0.0050 | -294.8642 | 208 |
| vidya | double | 1 | {"vda_length": 4} | 15653 | 2608.8333 | 3.0923 | 74.5941 | -114.9825 | -0.0073 | 1 | -49.7208 | 79.4944 | -2.1072 | 0.0300 | -131.8052 | 185 |
| vidya | half | 0 | {"vda_length": 2} | 19588 | 3264.6667 | 2.7720 | 140.3229 | -97.2372 | -0.0050 | 2 | -48.8053 | 99.3827 | -1.6823 | 0.0050 | -294.8642 | 208 |
| wma_baseline | default | 1 | {} | 13213 | 2202.1667 | 3.3214 | 132.0819 | -31.4682 | -0.0024 | 3 | -26.9528 | 34.4878 | -0.8565 | 0.0100 | -153.8872 | 176 |
| wma_baseline | double | 1 | {"ma_length": 40} | 9325 | 1554.1667 | 3.5266 | 100.8325 | -15.2193 | -0.0016 | 3 | -20.7108 | 55.9831 | -0.3083 | 0.0250 | -89.4562 | 113 |
| wma_baseline | half | 1 | {"ma_length": 10} | 18800 | 3133.3333 | 2.8640 | 93.2516 | -139.5696 | -0.0074 | 1 | -73.7257 | 117.8879 | -1.9351 | 0.0300 | -225.2492 | 210 |


---


# 1c — THE SELECTION TEST

At each step the candidates are ranked on that step's four TUNING years, the top K are traded on its unseen year, equal weight, and K is swept over the whole range. **The null shuffles the tuning-year ranking and re-runs the identical top-K construction, 1,000 draws** — so it tests the SELECTION RULE, not the pool.


## C1 — flip_only

| K | R_per_year_mean | R_total_build | years | years_positive | t_yearly | null_mean | null_p95 | null_p |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | -7.987 | -47.925 | 6 | 4 | -0.384 | -3.688 | 36.903 | 0.563 |
| 2 | -10.810 | -64.860 | 6 | 3 | -0.574 | -3.734 | 22.542 | 0.672 |
| 3 | -14.653 | -87.920 | 6 | 2 | -0.778 | -3.524 | 17.724 | 0.789 |
| 4 | -15.821 | -94.926 | 6 | 3 | -0.801 | -4.002 | 14.061 | 0.859 |
| 5 | -1.440 | -8.639 | 6 | 3 | -0.070 | -3.617 | 12.238 | 0.401 |
| 6 | -8.893 | -53.360 | 6 | 2 | -0.510 | -4.094 | 11.701 | 0.710 |
| 7 | -15.394 | -92.365 | 6 | 1 | -0.904 | -3.614 | 10.103 | 0.931 |
| 8 | -14.460 | -86.760 | 6 | 1 | -0.892 | -3.587 | 8.489 | 0.934 |
| 9 | -11.438 | -68.626 | 6 | 3 | -0.642 | -4.009 | 7.242 | 0.868 |
| 10 | -11.035 | -66.209 | 6 | 3 | -0.570 | -3.707 | 6.739 | 0.879 |
| 11 | -11.526 | -69.156 | 6 | 3 | -0.614 | -3.514 | 6.492 | 0.902 |
| 12 | -11.921 | -71.525 | 6 | 3 | -0.616 | -3.747 | 5.754 | 0.922 |
| 13 | -10.449 | -62.692 | 6 | 3 | -0.529 | -3.785 | 4.715 | 0.896 |
| 14 | -8.254 | -49.522 | 6 | 3 | -0.401 | -3.814 | 4.728 | 0.803 |
| 15 | -8.150 | -48.902 | 6 | 4 | -0.399 | -3.619 | 4.207 | 0.827 |
| 16 | -8.738 | -52.425 | 6 | 4 | -0.441 | -3.847 | 3.809 | 0.861 |
| 17 | -6.488 | -38.929 | 6 | 4 | -0.353 | -3.582 | 3.728 | 0.742 |
| 18 | -7.577 | -45.464 | 6 | 4 | -0.434 | -3.627 | 3.005 | 0.835 |
| 19 | -6.785 | -40.713 | 6 | 4 | -0.405 | -3.912 | 2.237 | 0.784 |
| 20 | -7.311 | -43.863 | 6 | 4 | -0.424 | -3.941 | 1.865 | 0.822 |
| 21 | -7.346 | -44.079 | 6 | 4 | -0.419 | -4.038 | 1.815 | 0.825 |
| 22 | -7.626 | -45.756 | 6 | 4 | -0.426 | -3.809 | 1.669 | 0.880 |
| 23 | -6.498 | -38.990 | 6 | 4 | -0.386 | -3.634 | 1.942 | 0.794 |
| 24 | -5.268 | -31.607 | 6 | 4 | -0.300 | -3.941 | 0.890 | 0.663 |
| 25 | -4.170 | -25.022 | 6 | 4 | -0.233 | -3.770 | 0.842 | 0.559 |
| 26 | -4.991 | -29.949 | 6 | 4 | -0.271 | -3.820 | 0.501 | 0.662 |
| 27 | -5.580 | -33.479 | 6 | 4 | -0.304 | -3.816 | 0.333 | 0.760 |
| 28 | -5.714 | -34.283 | 6 | 4 | -0.310 | -3.769 | -0.222 | 0.809 |
| 29 | -5.180 | -31.079 | 6 | 4 | -0.283 | -3.871 | -0.215 | 0.738 |
| 30 | -5.423 | -32.538 | 6 | 4 | -0.310 | -3.840 | -0.544 | 0.799 |
| 31 | -5.239 | -31.432 | 6 | 4 | -0.297 | -3.738 | -0.804 | 0.785 |
| 32 | -4.694 | -28.164 | 6 | 4 | -0.274 | -3.947 | -0.966 | 0.680 |
| 33 | -4.977 | -29.861 | 6 | 4 | -0.286 | -3.843 | -1.169 | 0.752 |
| 34 | -5.488 | -32.929 | 6 | 4 | -0.324 | -3.860 | -1.501 | 0.879 |
| 35 | -5.236 | -31.418 | 6 | 4 | -0.320 | -3.861 | -1.767 | 0.855 |
| 36 | -4.908 | -29.448 | 6 | 4 | -0.299 | -3.834 | -2.139 | 0.843 |
| 37 | -5.284 | -31.701 | 6 | 4 | -0.332 | -3.799 | -2.505 | 0.959 |
| 38 | -4.439 | -26.632 | 6 | 4 | -0.299 | -3.847 | -2.833 | 0.831 |
| 39 | -3.852 | -23.112 | 6 | 4 | -0.278 | -3.852 | -3.852 | 0.414 |


Best mean R per year **-1.440 at K=5** against a null mean of -3.617, p **0.401**. **0 of 39 K values beat their own null at p ≤ 0.05.**


## C1 — canonical_risk

| K | R_per_year_mean | R_total_build | years | years_positive | t_yearly | null_mean | null_p95 | null_p |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | -6.178 | -37.066 | 6 | 2 | -0.374 | -3.124 | 13.089 | 0.634 |
| 2 | -3.156 | -18.938 | 6 | 2 | -0.199 | -3.354 | 8.191 | 0.507 |
| 3 | -7.826 | -46.957 | 6 | 3 | -0.582 | -3.150 | 6.670 | 0.782 |
| 4 | -5.358 | -32.146 | 6 | 3 | -0.391 | -3.361 | 5.070 | 0.643 |
| 5 | -7.354 | -44.122 | 6 | 3 | -0.605 | -3.307 | 3.920 | 0.838 |
| 6 | -4.435 | -26.609 | 6 | 2 | -0.389 | -3.139 | 3.747 | 0.619 |
| 7 | -1.666 | -9.997 | 6 | 2 | -0.147 | -3.210 | 3.188 | 0.350 |
| 8 | -0.205 | -1.229 | 6 | 2 | -0.018 | -3.155 | 2.671 | 0.208 |
| 9 | -0.987 | -5.919 | 6 | 2 | -0.087 | -3.240 | 2.472 | 0.249 |
| 10 | -1.451 | -8.703 | 6 | 2 | -0.144 | -3.326 | 1.812 | 0.267 |
| 11 | -2.308 | -13.848 | 6 | 2 | -0.246 | -3.218 | 1.553 | 0.366 |
| 12 | -1.971 | -11.827 | 6 | 2 | -0.201 | -3.285 | 1.028 | 0.318 |
| 13 | -1.537 | -9.222 | 6 | 2 | -0.162 | -3.293 | 0.931 | 0.241 |
| 14 | -1.205 | -7.232 | 6 | 2 | -0.125 | -3.385 | 0.635 | 0.181 |
| 15 | -1.076 | -6.453 | 6 | 2 | -0.105 | -3.197 | 0.652 | 0.183 |
| 16 | -0.801 | -4.806 | 6 | 2 | -0.077 | -3.201 | 0.453 | 0.146 |
| 17 | -0.311 | -1.864 | 6 | 2 | -0.030 | -3.176 | 0.067 | 0.074 |
| 18 | -0.100 | -0.599 | 6 | 2 | -0.010 | -3.259 | -0.017 | 0.055 |
| 19 | 0.458 | 2.749 | 6 | 2 | 0.044 | -3.160 | -0.408 | 0.024 |
| 20 | -0.082 | -0.493 | 6 | 2 | -0.008 | -3.368 | -0.391 | 0.032 |
| 21 | 0.340 | 2.038 | 6 | 2 | 0.035 | -3.249 | -0.506 | 0.022 |
| 22 | 0.893 | 5.359 | 6 | 2 | 0.093 | -3.303 | -0.542 | 0.007 |
| 23 | 1.113 | 6.676 | 6 | 2 | 0.116 | -3.225 | -0.649 | 0.002 |
| 24 | 0.832 | 4.994 | 6 | 2 | 0.090 | -3.309 | -0.916 | 0.001 |
| 25 | 0.736 | 4.416 | 6 | 2 | 0.084 | -3.212 | -0.995 | 0.003 |
| 26 | 0.891 | 5.346 | 6 | 3 | 0.105 | -3.261 | -1.091 | 0.000 |
| 27 | 0.607 | 3.640 | 6 | 2 | 0.075 | -3.203 | -1.234 | 0.002 |
| 28 | 0.398 | 2.389 | 6 | 2 | 0.051 | -3.260 | -1.362 | 0.001 |
| 29 | 0.025 | 0.148 | 6 | 3 | 0.003 | -3.229 | -1.605 | 0.000 |
| 30 | 0.040 | 0.241 | 6 | 3 | 0.005 | -3.265 | -1.633 | 0.001 |
| 31 | -0.220 | -1.319 | 6 | 2 | -0.031 | -3.247 | -1.738 | 0.000 |
| 32 | -0.316 | -1.896 | 6 | 2 | -0.044 | -3.275 | -1.842 | 0.001 |
| 33 | -0.111 | -0.666 | 6 | 2 | -0.015 | -3.267 | -1.942 | 0.000 |
| 34 | -0.272 | -1.630 | 6 | 2 | -0.036 | -3.275 | -2.056 | 0.000 |
| 35 | -1.505 | -9.028 | 6 | 2 | -0.197 | -3.283 | -2.346 | 0.001 |
| 36 | -2.484 | -14.902 | 6 | 2 | -0.342 | -3.241 | -2.403 | 0.068 |
| 37 | -2.404 | -14.423 | 6 | 2 | -0.330 | -3.242 | -2.494 | 0.031 |
| 38 | -2.844 | -17.062 | 6 | 2 | -0.405 | -3.274 | -2.760 | 0.075 |
| 39 | -3.257 | -19.544 | 6 | 1 | -0.462 | -3.257 | -3.257 | 0.185 |


Best mean R per year **+1.113 at K=23** against a null mean of -3.225, p **0.002**. **18 of 39 K values beat their own null at p ≤ 0.05.**


## BASELINE — flip_only

| K | R_per_year_mean | R_total_build | years | years_positive | t_yearly | null_mean | null_p95 | null_p |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | -33.790 | -202.743 | 6 | 2 | -1.224 | 2.203 | 32.850 | 0.969 |
| 2 | -26.408 | -158.447 | 6 | 2 | -1.201 | 3.716 | 24.432 | 0.991 |
| 3 | -32.318 | -193.907 | 6 | 2 | -1.328 | 2.888 | 19.935 | 1.000 |
| 4 | -16.659 | -99.955 | 6 | 2 | -0.899 | 3.762 | 18.391 | 0.988 |
| 5 | -14.816 | -88.895 | 6 | 2 | -0.796 | 2.897 | 15.355 | 0.990 |
| 6 | -8.056 | -48.333 | 6 | 2 | -0.467 | 3.502 | 14.560 | 0.959 |
| 7 | -8.174 | -49.042 | 6 | 2 | -0.443 | 2.911 | 12.181 | 0.974 |
| 8 | -9.325 | -55.952 | 6 | 2 | -0.472 | 3.230 | 11.796 | 0.997 |
| 9 | -5.665 | -33.990 | 6 | 2 | -0.305 | 3.250 | 10.683 | 0.983 |
| 10 | -3.255 | -19.529 | 6 | 2 | -0.176 | 3.182 | 9.302 | 0.950 |
| 11 | -1.761 | -10.565 | 6 | 2 | -0.100 | 3.304 | 8.143 | 0.945 |
| 12 | -1.238 | -7.429 | 6 | 2 | -0.073 | 3.376 | 7.672 | 0.966 |
| 13 | 1.484 | 8.901 | 6 | 2 | 0.089 | 3.310 | 6.719 | 0.806 |
| 14 | 2.261 | 13.563 | 6 | 2 | 0.137 | 3.317 | 5.791 | 0.721 |
| 15 | 3.294 | 19.762 | 6 | 2 | 0.200 | 3.294 | 3.294 | 0.176 |


Best mean R per year **+3.294 at K=15** against a null mean of +3.294, p **0.176**. **0 of 15 K values beat their own null at p ≤ 0.05.**


Note the degenerate end: at **K = 15 of 15** the "top K" is every baseline, so shuffling the ranking changes nothing and the null equals the real number exactly. That is a check on the null, not a result.


## BASELINE — canonical_risk

| K | R_per_year_mean | R_total_build | years | years_positive | t_yearly | null_mean | null_p95 | null_p |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 13.052 | 78.309 | 6 | 4 | 0.930 | -6.345 | 7.438 | 0.007 |
| 2 | 2.357 | 14.143 | 6 | 4 | 0.173 | -6.418 | 2.896 | 0.061 |
| 3 | 0.958 | 5.746 | 6 | 4 | 0.068 | -6.437 | 0.669 | 0.044 |
| 4 | -0.021 | -0.128 | 6 | 3 | -0.002 | -6.223 | 0.145 | 0.054 |
| 5 | -2.207 | -13.240 | 6 | 3 | -0.196 | -6.583 | -1.122 | 0.100 |
| 6 | -1.726 | -10.353 | 6 | 3 | -0.162 | -6.473 | -1.717 | 0.051 |
| 7 | -2.442 | -14.650 | 6 | 3 | -0.244 | -6.391 | -2.190 | 0.060 |
| 8 | -2.271 | -13.625 | 6 | 3 | -0.236 | -6.510 | -3.077 | 0.021 |
| 9 | -2.168 | -13.008 | 6 | 3 | -0.231 | -6.518 | -3.146 | 0.011 |
| 10 | -2.707 | -16.242 | 6 | 3 | -0.290 | -6.525 | -3.870 | 0.004 |
| 11 | -2.619 | -15.715 | 6 | 3 | -0.277 | -6.370 | -4.068 | 0.006 |
| 12 | -3.552 | -21.314 | 6 | 3 | -0.403 | -6.438 | -4.519 | 0.011 |
| 13 | -4.669 | -28.013 | 6 | 3 | -0.561 | -6.498 | -4.990 | 0.029 |
| 14 | -5.924 | -35.543 | 6 | 3 | -0.737 | -6.498 | -5.457 | 0.163 |
| 15 | -6.461 | -38.768 | 6 | 3 | -0.806 | -6.461 | -6.461 | 0.512 |


Best mean R per year **+13.052 at K=1** against a null mean of -6.345, p **0.007**. **8 of 15 K values beat their own null at p ≤ 0.05.**


## What 1c says, carefully

**Under `flip_only`, nothing: 0 of 39 and 0 of 15 K values beat their null, and the best C1 mean is negative.** Enter on a flip and exit on the opposite flip, with no risk plan, does not work for any of these 54 components, alone or ranked.


**Under `canonical_risk` the selection rule does something.** C1: best +1.113 R per year at K=23, null mean −3.225, p 0.002, and **18 of 39 K values beat their null at p ≤ 0.05** — far more than the ~2 that 39 tests at α 0.05 would give by chance, so it is not an artefact of sweeping K. Baselines: best **+13.052 R per year at K=1**, null mean −6.345, p 0.007, 8 of 15 beating.


**This is the first null-tested positive in the programme, and it is a statement about the RISK PLAN, not about any indicator.** The same 54 components, ranked the same way, are worthless without the 1.5 ATR stop and the half-off at 1 ATR, and have an edge with them. No single component is significant on its own in either variant.


**What I am not claiming.** Four (family × variant) combinations were run, so there is a multiplicity of 4 above the K sweep that these p-values do not carry. The K sweep itself is accounted for by counting how many K values beat their null rather than quoting the best one. And 0a's limit still applies: six yearly observations is a thin instrument, so this needs the CONFIRM years before it is more than a lead.


## For Jack to pick from

**At most 3 C1 and 3 baselines, for a stated reason. I am not picking.** Three things in the tables above are worth weighing when you do:


1. **Stability across settings** (`n_settings_used`, and the all-three-settings table). A candidate that is positive on all three settings is a different kind of evidence from one that is positive on its best.

2. **Trade count.** Some settings produce very few trades over six years — `adx_dmi` at double length took 46. A thin candidate cannot be measured, whatever its R.

3. **`null_p`**, the matched random-entry null, which asks whether the timing did anything beyond being in the market.


## Provenance

- `results/nnfx/stage1_c1_flip_only_yearly.csv` — 1,906 rows, md5 `bbcdff1a4f55`
- `results/nnfx/stage1_c1_flip_only_summary.csv` — 117 rows, md5 `2902ad497cec`
- `results/nnfx/stage1_c1_flip_only_nulls.csv` — 23,400 rows, md5 `32bd90b66337`
- `results/nnfx/stage1_c1_flip_only_walk.csv` — 429 rows, md5 `0eba7c864950`
- `results/nnfx/stage1_c1_flip_only_walkbuild.csv` — 39 rows, md5 `274de5dd1d90`
- `results/nnfx/stage1_c1_flip_only_select.csv` — 39 rows, md5 `037e7988835f`
- `results/nnfx/stage1_c1_canonical_risk_yearly.csv` — 1,929 rows, md5 `2d2967d74063`
- `results/nnfx/stage1_c1_canonical_risk_summary.csv` — 117 rows, md5 `2f4ad2a1f518`
- `results/nnfx/stage1_c1_canonical_risk_nulls.csv` — 23,400 rows, md5 `f8a47a989657`
- `results/nnfx/stage1_c1_canonical_risk_walk.csv` — 429 rows, md5 `266de4cfc411`
- `results/nnfx/stage1_c1_canonical_risk_walkbuild.csv` — 39 rows, md5 `2b1ac2e43be3`
- `results/nnfx/stage1_c1_canonical_risk_select.csv` — 39 rows, md5 `0946750292ce`
- `results/nnfx/stage1_base_flip_only_yearly.csv` — 748 rows, md5 `69d0c988d335`
- `results/nnfx/stage1_base_flip_only_summary.csv` — 45 rows, md5 `bd6325fef0a0`
- `results/nnfx/stage1_base_flip_only_nulls.csv` — 9,000 rows, md5 `c95cd604e274`
- `results/nnfx/stage1_base_flip_only_walk.csv` — 165 rows, md5 `9e6467be8f65`
- `results/nnfx/stage1_base_flip_only_walkbuild.csv` — 15 rows, md5 `3d2852a9cf2c`
- `results/nnfx/stage1_base_flip_only_select.csv` — 15 rows, md5 `fa0f527dfea5`
- `results/nnfx/stage1_base_canonical_risk_yearly.csv` — 756 rows, md5 `89c995b1dbad`
- `results/nnfx/stage1_base_canonical_risk_summary.csv` — 45 rows, md5 `543fa54967e1`
- `results/nnfx/stage1_base_canonical_risk_nulls.csv` — 9,000 rows, md5 `9876707d8add`
- `results/nnfx/stage1_base_canonical_risk_walk.csv` — 165 rows, md5 `ea59099e9a82`
- `results/nnfx/stage1_base_canonical_risk_walkbuild.csv` — 15 rows, md5 `1cabb056dc66`
- `results/nnfx/stage1_base_canonical_risk_select.csv` — 15 rows, md5 `e482394d42e8`
- `results/nnfx/CANDIDATE_LEDGER.csv` — 54 candidates on record
