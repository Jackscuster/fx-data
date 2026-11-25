# STAGE 1 R2 — ONE PIECE ALONE, THREE RISK PLANS, ELEVEN UNSEEN YEARS

Generated 2026-11-25 02:46 by `code/nnfx1.py`. HANDOFF 0m.


**This supersedes `STAGE1.md`, which carries a header note saying what was wrong with it.** All three faults Jack found were real, and a fourth of mine turned up while fixing them.


## What changed, and what each fix was worth

| item | fault | fix | effect |
|---|---|---|---|
| 3 | **no cost charged on flip-only** — R was restated to the 1.5 ATR unit and the cost was not, so with a 2000 ATR sentinel stop the charge was 2000× too small | the cost is restated by the same `atr_mult / 1.5` factor. Because `units ~ 1/(atr_mult × ATR)` the factor cancels exactly, so **cost per trade is independent of the sentinel stop** — that is what declaring the notional buys | +0.00001 → **+0.018 R per trade** |
| 3 | **the worst dip was not a drawdown** — computed from six yearly sums, so it equalled minus the worst year on 56 of 117 rows and was exactly 0 on four more | true chronological drawdown on the **daily mark-to-market series**, built on gate 2's increment convention and verified to reproduce total net R to **1e-13** | 115 R → **384 R** on one candidate |
| 1 | **ambiguous bars filled stop-first** | resolved from the **hourly bid/ask path** inside the one engine, opt-in; a long's levels fill on the BID, a short's on the ASK; unresolvable bars keep stop-first and are counted | see §1 |
| 2 | **the zero-edge check failed** at −0.020 R per trade | **it was my arithmetic, not the apparatus.** The null ran over 2005-2020 while the summary divided by the six-year BUILD trade count, a factor of 2.607 | gross **−0.0008**, zero within noise |
| 5 | six unseen years for fixed settings | a fixed setting needs no tuning, so **all eleven trade years 2005-2015** are unseen for it | 6 → **11** yearly observations |
| 6 | the yearly t is nearly blind | a **block-bootstrap t** on the daily series beside it, 20-day blocks, 2,000 draws, with its own 0a power test | see §3 |
| 6 | floors from a formula | floors from the **random-entry null**, in each statistic's own units | see §3 |
| 4 | one risk plan | **three declared in advance**: `flip_only`, `jack`, `textbook` | see §2 |

**2016-2020 is computed and stored in every `*_yearly.csv` and is not summarised anywhere below.** 2021 onward is never read.


---

## 1 — ambiguous bars, resolved from the hourly path

| variant | indicators | trades | ambiguous_bars | per_1000_trades | target_first | stop_first | unresolved | share_target_first | dR_total | dR_per_trade |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| flip_only | 8 | 142988.0000 | 0 | 0.0000 | 0 | 0 | 0 |  | 0.0000 | 0.0000 |
| jack | 8 | 150344.0000 | 151 | 1.0044 | 54 | 92 | 5 | 0.3699 | 45.0000 | 0.0003 |
| textbook | 8 | 151706.0000 | 173 | 1.1404 | 90 | 79 | 4 | 0.5325 | 65.0000 | 0.0004 |


**`flip_only` shows exactly zero, and that is the control**: with no target there is no stop-versus-target ambiguity to resolve. If it showed anything, the measurement would be wrong.


**The correction is real but small.** A5 measured the target first on 40% of ambiguous days and that holds here, but ambiguous bars are rare — a few per thousand trades — so the effect on R per trade is in the fourth decimal. **It was never going to explain the −0.020 R per trade the zero-edge check flagged; that was my own scope mismatch.** The fix is kept because it is correct, not because it rescues anything.


The hourly index covers **99.6%** of daily bars at a median 24 sub-bars each, aligned on a **16:00 New York** session cut chosen by scanning every candidate: 72.8% containment of the daily range against 66.5% at 15:00, 62.8% at 17:00 and 71.2% for the best fixed-UTC cut. It is not 100% because the daily and hourly files are different products — on 16.8% of bars the hourly range is **narrower** than the daily. Unresolvable bars keep stop-first and are counted, never guessed.


---

## 2 — the three risk plans

| plan | stop | first target | baseline distance | one-candle | status |
|---|---|---|---|---|---|
| `flip_only` | none (2000 ATR sentinel, asserted never reached) | none | inert | off | the control |
| `jack` | **1.0 ATR** | **1.5× the stop** | 1.5 ATR | off | **the main version** |
| `textbook` | 1.5 ATR | half off at **1.0 ATR** | 1.0 ATR | **on** | canonical NNFX |

Both plans are scored in the **same unit, R per 1.5 ATR**, so their numbers are directly comparable although their stops differ. No engine default was changed; both plans are in `CANDIDATE_LEDGER.csv`.


**The baseline-distance setting is inert in stage 1 and the honest thing is to say so.** In the C1-alone runs the baseline is placed far from price on purpose so that `side` is fixed, which means a finite distance filter rejects *every* entry — the first `jack` run produced zero trades for exactly that reason. In the baseline-alone runs the entry *is* the cross, where the distance is about zero. It is declared for completeness, not tested.


**On where Jack's values come from**, see `results/nnfx/RISK_PLANS.md`. The short version: only the ATR *length* was ever swept (15 Aug 2026, 49 values, on a plateau whose whole range is 2.21 standard errors wide, **before** fault 27 and under the stop-first fill). The stop multiple, target multiple, baseline distance and one-candle rule were declared defaults, never swept at gate 1 — GAUNTLET.md says so. The gate 2 tuner does sweep them and picks 1.00 in 98% of cases, but 1.00 is the **lower bound of its grid**, so that is saturation against a boundary rather than an optimum.


## 3 — the two statistics and the floors

**0a rerun for the block-bootstrap t**, eleven years, floors taken from its own zero-edge null rather than a formula:

| edge_R | repeats | median_t | floor_emp_alone | floor_emp_of_3 | floor_emp_of_15 | floor_emp_of_39 | power_alone | power_of_3 | power_of_15 | power_of_39 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.000 | 150 | -0.023 | 1.493 | 1.666 | 2.030 | 2.030 | 0.060 | 0.040 | 0.007 | 0.007 |
| 0.020 | 150 | 0.745 | 1.493 | 1.666 | 2.030 | 2.030 | 0.213 | 0.167 | 0.093 | 0.093 |
| 0.050 | 150 | 1.495 | 1.493 | 1.666 | 2.030 | 2.030 | 0.653 | 0.547 | 0.400 | 0.400 |
| 0.100 | 150 | 3.218 | 1.493 | 1.666 | 2.030 | 2.030 | 0.900 | 0.887 | 0.820 | 0.820 |
| 0.150 | 150 | 4.688 | 1.493 | 1.666 | 2.030 | 2.030 | 0.960 | 0.947 | 0.940 | 0.940 |
| 0.200 | 150 | 5.732 | 1.493 | 1.666 | 2.030 | 2.030 | 1.000 | 1.000 | 0.993 | 0.993 |


**The false-positive rate at zero edge is 0.053** against a nominal 0.05, so the power below is not bought by inflating the error rate.


| statistic, one of 39, eleven years | power at 0.10 R | power at 0.20 R |
|---|---:|---:|
| yearly t (original 0a) | **14.6%** | 46.6% |
| block-bootstrap t | **82.0%** | 99.3% |

**That is the single most important number in this rerun.** The yearly t at one-of-39 could not see a 0.10 R per trade edge; the bootstrap t sees it most of the time, at a verified 5% error rate. The instrument is no longer blind.


**One limitation, stated rather than buried.** My 0a simulation lays planted trades on a calendar with independent per-trade R, so its daily series has weaker serial dependence than a real one, where open positions are marked every day. A block bootstrap handles serial dependence; my simulation does not fully exercise it. So the measured 0.053 is a **lower bound** on the real false-positive rate, and the bootstrap t should be read beside the yearly t, not instead of it. Both are reported for every candidate.


---

# C1 — all 39 candidates


## C1 — `flip_only`, fixed settings, unseen trade years 2005-2015

Empirical yearly-t floors **from the random-entry null**: alone **1.243**, best-of-39 **3.028**. The analytic equivalents on 11 yearly observations are 1.812 and 3.973 — the empirical ones are lower because the analytic formula assumes a **zero-mean** null while the real null also pays costs, so it is centred below zero.

| indicator | setting | distinct_setting | n_entered | trades_per_year | mean_bars | R_gross_per_trade | R_net_per_trade | cost_per_trade | R_net_per_year | years | years_positive | worst_year | worst_dip_R | t_yearly | t_block_boot | null_p | clears_alone_emp | clears_family_emp |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| j_tpo_signals | double | 1 | 915.0000 | 83.1818 | 77.6732 | 0.2739 | 0.2414 | 0.0325 | 20.0769 | 11 | 7 | -90.8558 | 188.3927 | 0.8956 | 0.7506 | 0.0925 | 0 | 0 |
| halftrend_signals | half | 1 | 538.0000 | 48.9091 | 130.9071 | 0.4368 | 0.4055 | 0.0314 | 19.8321 | 11 | 4 | -89.7251 | 202.0334 | 0.7399 | 0.7952 | 0.1075 | 0 | 0 |
| ichimoku_signals | half | 1 | 661.0000 | 60.0909 | 116.6384 | 0.3021 | 0.2686 | 0.0336 | 16.1375 | 11 | 6 | -60.2960 | 121.6823 | 0.9008 | 0.7675 | 0.1875 | 0 | 0 |
| halftrend_signals | default | 1 | 322.0000 | 29.2727 | 216.9596 | 0.5655 | 0.5344 | 0.0311 | 15.6429 | 11 | 8 | -141.4518 | 287.3412 | 0.6582 | 0.6334 | 0.2175 | 0 | 0 |
| laguerre_filter_signals | double | 1 | 965.0000 | 87.7273 | 71.8280 | 0.1914 | 0.1593 | 0.0321 | 13.9787 | 11 | 4 | -119.0893 | 200.0729 | 0.4882 | 0.5354 | 0.1850 | 0 | 0 |
| ichimoku_signals | default | 1 | 610.0000 | 55.4545 | 125.6508 | 0.2260 | 0.1926 | 0.0334 | 10.6806 | 11 | 7 | -71.8225 | 144.1604 | 0.8052 | 0.5208 | 0.2825 | 0 | 0 |
| price_momentum_oscillator_signals | double | 1 | 1130.0000 | 102.7273 | 61.1717 | 0.1219 | 0.0891 | 0.0328 | 9.1533 | 11 | 4 | -123.7383 | 274.9898 | 0.2925 | 0.3557 | 0.2350 | 0 | 0 |
| adx_dmi_signals | double | 1 | 58.0000 | 5.2727 | 1417.2759 | 1.6950 | 1.6662 | 0.0287 | 8.7855 | 11 | 6 | -33.6995 | 95.1428 | 0.9419 | 0.9920 | 0.0725 | 0 | 0 |
| ichimoku_signals | double | 1 | 815.0000 | 74.0909 | 92.8135 | 0.1322 | 0.1000 | 0.0322 | 7.4083 | 11 | 3 | -110.7185 | 285.6721 | 0.2481 | 0.2804 | 0.3075 | 0 | 0 |
| halftrend_signals | double | 1 | 172.0000 | 15.6364 | 396.9826 | 0.4094 | 0.3789 | 0.0305 | 5.9247 | 11 | 5 | -55.4784 | 139.5116 | 0.4329 | 0.2959 | 0.4175 | 0 | 0 |
| trend_direction_force_index_signals | double | 1 | 825.0000 | 75.0000 | 89.8715 | 0.0993 | 0.0662 | 0.0331 | 4.9623 | 11 | 4 | -92.3994 | 292.6415 | 0.1589 | 0.1882 | 0.3675 | 0 | 0 |
| dspo_signals | double | 1 | 1106.0000 | 100.5455 | 63.6962 | 0.0777 | 0.0447 | 0.0330 | 4.4945 | 11 | 4 | -107.0154 | 232.9784 | 0.1635 | 0.1778 | 0.3175 | 0 | 0 |
| lemantrend_signals | half | 1 | 2613.0000 | 237.5455 | 27.2258 | 0.0392 | 0.0063 | 0.0329 | 1.5005 | 11 | 8 | -275.6344 | 378.6155 | 0.0426 | 0.0564 | 0.2900 | 0 | 0 |
| dpo_signals | double | 1 | 2116.0000 | 192.3636 | 30.6422 | 0.0394 | 0.0070 | 0.0324 | 1.3464 | 11 | 3 | -73.8820 | 314.5872 | 0.0521 | 0.0576 | 0.2850 | 0 | 0 |
| schaff_trend_cycle_signals | half | 1 | 2653.0000 | 241.1818 | 13.5047 | 0.0367 | 0.0049 | 0.0318 | 1.1822 | 11 | 7 | -44.7638 | 114.1860 | 0.1353 | 0.0991 | 0.2075 | 0 | 0 |
| lemantrend_signals | default | 1 | 1936.0000 | 176.0000 | 36.7980 | 0.0342 | 0.0017 | 0.0325 | 0.3032 | 11 | 8 | -261.5701 | 376.6041 | 0.0089 | 0.0117 | 0.3800 | 0 | 0 |
| schaff_trend_cycle_signals | default | 1 | 2533.0000 | 230.2727 | 15.4722 | 0.0267 | -0.0053 | 0.0320 | -1.2186 | 11 | 6 | -50.1056 | 126.3247 | -0.1268 | -0.0903 | 0.2600 | 0 | 0 |
| donchian_breakout_signals | double | 1 | 854.0000 | 77.6364 | 83.9906 | -0.0110 | -0.0431 | 0.0321 | -3.3447 | 11 | 4 | -118.5841 | 257.9471 | -0.1089 | -0.1295 | 0.4950 | 0 | 0 |
| waddah_attar_explosion_signals | default | 1 | 1499.0000 | 136.2727 | 48.8406 | 0.0052 | -0.0276 | 0.0328 | -3.7575 | 11 | 7 | -272.8949 | 376.0827 | -0.1140 | -0.1451 | 0.4800 | 0 | 0 |
| mama_fama_signals | double | 1 | 1456.0000 | 132.3636 | 48.4073 | 0.0032 | -0.0292 | 0.0324 | -3.8599 | 11 | 4 | -145.0324 | 309.1732 | -0.1149 | -0.1453 | 0.4600 | 0 | 0 |
| waddah_attar_explosion_signals | double | 1 | 1546.0000 | 140.5455 | 47.3079 | 0.0046 | -0.0282 | 0.0328 | -3.9605 | 11 | 7 | -275.4516 | 382.1401 | -0.1194 | -0.1528 | 0.5225 | 0 | 0 |
| waddah_attar_explosion_signals | half | 1 | 1420.0000 | 129.0909 | 51.6317 | -0.0006 | -0.0334 | 0.0328 | -4.3163 | 11 | 7 | -267.0510 | 370.5192 | -0.1325 | -0.1663 | 0.4900 | 0 | 0 |
| dpo_signals | default | 1 | 3447.0000 | 313.3636 | 20.3963 | 0.0186 | -0.0143 | 0.0329 | -4.4866 | 11 | 3 | -117.2301 | 260.5192 | -0.1360 | -0.1720 | 0.3625 | 0 | 0 |
| aroon_signals | half | 1 | 5355.0000 | 486.8182 | 13.3731 | 0.0227 | -0.0094 | 0.0320 | -4.5539 | 11 | 5 | -141.0518 | 276.5263 | -0.1569 | -0.2100 | 0.2625 | 0 | 0 |
| lemantrend_signals | double | 1 | 1420.0000 | 129.0909 | 50.5120 | -0.0033 | -0.0359 | 0.0326 | -4.6365 | 11 | 7 | -269.7092 | 367.0176 | -0.1414 | -0.1769 | 0.5225 | 0 | 0 |
| volatility_quality_signals | default | 1 | 3390.0000 | 308.1818 | 21.2286 | 0.0155 | -0.0163 | 0.0318 | -5.0230 | 11 | 5 | -118.2051 | 240.8859 | -0.1940 | -0.2435 | 0.3500 | 0 | 0 |
| supertrend_signals | double | 1 | 1796.0000 | 163.2727 | 40.4087 | -0.0114 | -0.0429 | 0.0315 | -7.0126 | 11 | 4 | -89.5915 | 272.6592 | -0.2975 | -0.3175 | 0.5425 | 0 | 0 |
| parabolic_sar_signals | default | 1 | 6643.0000 | 603.9091 | 10.8347 | 0.0190 | -0.0131 | 0.0321 | -7.9304 | 11 | 4 | -73.1885 | 288.7037 | -0.4671 | -0.4069 | 0.2225 | 0 | 0 |
| aroon_signals | double | 1 | 1446.0000 | 131.4545 | 48.4689 | -0.0311 | -0.0634 | 0.0323 | -8.3396 | 11 | 3 | -106.3247 | 314.6587 | -0.2514 | -0.3259 | 0.5900 | 0 | 0 |
| parabolic_sar_signals | half | 1 | 9605.0000 | 873.1818 | 7.4551 | 0.0223 | -0.0097 | 0.0320 | -8.4971 | 11 | 5 | -83.6024 | 243.3002 | -0.6035 | -0.4297 | 0.1400 | 0 | 0 |
| supertrend_signals | default | 1 | 1811.0000 | 164.6364 | 39.7620 | -0.0257 | -0.0573 | 0.0316 | -9.4404 | 11 | 4 | -97.7400 | 280.8942 | -0.3805 | -0.4196 | 0.5950 | 0 | 0 |
| price_momentum_oscillator_signals | default | 1 | 1732.0000 | 157.4545 | 41.2667 | -0.0302 | -0.0625 | 0.0323 | -9.8361 | 11 | 3 | -174.1904 | 353.8481 | -0.2720 | -0.3611 | 0.6425 | 0 | 0 |
| kase_peak_oscillator_signals | double | 1 | 2840.0000 | 258.1818 | 25.2817 | -0.0064 | -0.0385 | 0.0321 | -9.9325 | 11 | 4 | -118.5654 | 384.1014 | -0.3100 | -0.3857 | 0.5250 | 0 | 0 |
| rex_oscillator_signals | default | 1 | 12531.0000 | 1139.1818 | 5.7319 | 0.0232 | -0.0090 | 0.0322 | -10.2548 | 11 | 5 | -123.2307 | 269.0644 | -0.6016 | -0.4449 | 0.0850 | 0 | 0 |
| trend_direction_force_index_signals | half | 1 | 3591.0000 | 326.4545 | 20.3305 | 0.0006 | -0.0321 | 0.0327 | -10.4652 | 11 | 5 | -125.1274 | 246.5776 | -0.3699 | -0.4564 | 0.5050 | 0 | 0 |
| aroon_signals | default | 1 | 2822.0000 | 256.5455 | 25.4791 | -0.0087 | -0.0409 | 0.0322 | -10.4859 | 11 | 4 | -173.9244 | 311.5809 | -0.3345 | -0.4175 | 0.5500 | 0 | 0 |
| laguerre_filter_signals | default | 1 | 2075.0000 | 188.6364 | 34.2795 | -0.0269 | -0.0590 | 0.0322 | -11.1367 | 11 | 3 | -140.8481 | 328.5288 | -0.3402 | -0.4307 | 0.5825 | 0 | 0 |
| ssl_channel_signals | double | 1 | 4045.0000 | 367.7273 | 17.5651 | -0.0006 | -0.0327 | 0.0321 | -12.0380 | 11 | 4 | -118.5259 | 241.3903 | -0.4561 | -0.5267 | 0.5100 | 0 | 0 |
| chandelier_exit_signals | half | 1 | 2126.0000 | 193.2727 | 34.0499 | -0.0317 | -0.0633 | 0.0316 | -12.2435 | 11 | 4 | -82.5508 | 303.3998 | -0.4910 | -0.5258 | 0.6725 | 0 | 0 |
| kase_peak_oscillator_signals | half | 1 | 5519.0000 | 501.7273 | 13.0274 | 0.0068 | -0.0250 | 0.0319 | -12.5488 | 11 | 5 | -120.0399 | 233.7232 | -0.7027 | -0.6110 | 0.4325 | 0 | 0 |
| dspo_signals | half | 1 | 4298.0000 | 390.7273 | 16.7778 | -0.0012 | -0.0334 | 0.0321 | -13.0385 | 11 | 4 | -131.2344 | 262.3568 | -0.4574 | -0.5543 | 0.5325 | 0 | 0 |
| kuskus_starlight_signals | double | 1 | 2825.0000 | 256.8182 | 24.9731 | -0.0190 | -0.0512 | 0.0322 | -13.1398 | 11 | 3 | -113.4121 | 348.2856 | -0.3858 | -0.5418 | 0.6075 | 0 | 0 |
| didi_index_signals | half | 1 | 4969.0000 | 451.7273 | 14.4611 | 0.0029 | -0.0293 | 0.0322 | -13.2296 | 11 | 4 | -107.7520 | 276.7797 | -0.5670 | -0.5835 | 0.4700 | 0 | 0 |
| bears_bulls_impulse_signals | double | 1 | 3509.0000 | 319.0000 | 21.0658 | -0.0091 | -0.0419 | 0.0328 | -13.3509 | 11 | 4 | -159.7076 | 313.7770 | -0.3950 | -0.5187 | 0.5725 | 0 | 0 |
| hieken_ashi_smoothed_signals | double | 1 | 2746.0000 | 249.6364 | 25.2283 | -0.0225 | -0.0543 | 0.0318 | -13.5671 | 11 | 4 | -217.6249 | 354.3712 | -0.4123 | -0.5369 | 0.6450 | 0 | 0 |
| kase_peak_oscillator_signals | default | 1 | 3906.0000 | 355.0909 | 18.4619 | -0.0069 | -0.0390 | 0.0320 | -13.8467 | 11 | 4 | -92.9485 | 275.5296 | -0.6147 | -0.5979 | 0.5525 | 0 | 0 |
| supertrend_signals | half | 1 | 1851.0000 | 168.2727 | 38.8612 | -0.0505 | -0.0823 | 0.0318 | -13.8546 | 11 | 3 | -90.4927 | 309.3563 | -0.5637 | -0.5927 | 0.6825 | 0 | 0 |
| glitch_index_signals | half | 1 | 2238.0000 | 203.4545 | 33.2757 | -0.0367 | -0.0689 | 0.0323 | -14.0246 | 11 | 3 | -155.7856 | 378.7038 | -0.4366 | -0.5440 | 0.6850 | 0 | 0 |
| trend_direction_force_index_signals | default | 1 | 1679.0000 | 152.6364 | 43.7784 | -0.0596 | -0.0927 | 0.0330 | -14.1445 | 11 | 4 | -180.6292 | 426.7615 | -0.4103 | -0.5284 | 0.7125 | 0 | 0 |
| polychromatic_momentum_signals | default | 1 | 2883.0000 | 262.0909 | 24.9331 | -0.0219 | -0.0542 | 0.0324 | -14.2142 | 11 | 5 | -139.4291 | 315.0139 | -0.5089 | -0.5662 | 0.5900 | 0 | 0 |
| fx_sniper_ergodic_cci_signals | double | 1 | 8107.0000 | 737.0000 | 8.8105 | 0.0131 | -0.0194 | 0.0325 | -14.2622 | 11 | 4 | -98.7034 | 345.4849 | -0.7257 | -0.7125 | 0.3025 | 0 | 0 |
| ehlers_reverse_ema_signals | double | 1 | 2832.0000 | 257.4545 | 25.3439 | -0.0234 | -0.0561 | 0.0328 | -14.4545 | 11 | 3 | -167.1249 | 373.0980 | -0.4133 | -0.5261 | 0.6175 | 0 | 0 |
| kalman_filter_signals | half | 1 | 3294.0000 | 299.4545 | 21.9426 | -0.0165 | -0.0489 | 0.0324 | -14.6382 | 11 | 5 | -157.5873 | 299.8113 | -0.5363 | -0.6024 | 0.6350 | 0 | 0 |
| rex_oscillator_signals | half | 1 | 13924.0000 | 1265.8182 | 5.1585 | 0.0205 | -0.0116 | 0.0321 | -14.6947 | 11 | 2 | -86.7522 | 339.8546 | -0.8113 | -0.7263 | 0.0975 | 0 | 0 |
| chandelier_exit_signals | default | 1 | 2359.0000 | 214.4545 | 30.8949 | -0.0390 | -0.0698 | 0.0307 | -14.9651 | 11 | 4 | -88.4435 | 284.5044 | -0.6469 | -0.6854 | 0.6825 | 0 | 0 |
| ssl_channel_signals | default | 1 | 5794.0000 | 526.7273 | 12.2917 | 0.0035 | -0.0286 | 0.0320 | -15.0534 | 11 | 4 | -113.2054 | 258.7604 | -0.8069 | -0.7426 | 0.4425 | 0 | 0 |
| volatility_quality_signals | half | 1 | 8420.0000 | 765.4545 | 8.4987 | 0.0118 | -0.0198 | 0.0316 | -15.1707 | 11 | 3 | -58.4817 | 228.3627 | -2.2003 | -0.8205 | 0.2975 | 0 | 0 |
| mama_fama_signals | half | 1 | 6745.0000 | 613.1818 | 10.6451 | 0.0074 | -0.0248 | 0.0322 | -15.2244 | 11 | 4 | -119.6484 | 235.4485 | -0.8408 | -0.7376 | 0.3675 | 0 | 0 |
| linreg_slope_signals | double | 1 | 1870.0000 | 170.0000 | 39.3567 | -0.0580 | -0.0901 | 0.0321 | -15.3254 | 11 | 3 | -158.3840 | 362.1547 | -0.4317 | -0.5705 | 0.7325 | 0 | 0 |
| glitch_index_signals | double | 1 | 1227.0000 | 111.5455 | 60.2592 | -0.1104 | -0.1431 | 0.0327 | -15.9647 | 11 | 3 | -109.9241 | 375.1906 | -0.4891 | -0.5912 | 0.7850 | 0 | 0 |
| fx_sniper_ergodic_cci_signals | default | 1 | 9785.0000 | 889.5455 | 7.3573 | 0.0140 | -0.0181 | 0.0321 | -16.0983 | 11 | 4 | -116.1234 | 298.9412 | -0.9619 | -0.7981 | 0.2375 | 0 | 0 |
| hieken_ashi_smoothed_signals | half | 1 | 5257.0000 | 477.9091 | 13.4971 | -0.0017 | -0.0339 | 0.0322 | -16.1996 | 11 | 4 | -144.2174 | 316.7691 | -0.6569 | -0.7343 | 0.4975 | 0 | 0 |
| schaff_trend_cycle_signals | double | 1 | 2310.0000 | 210.0000 | 17.8134 | -0.0456 | -0.0774 | 0.0319 | -16.2639 | 11 | 3 | -63.5497 | 261.8747 | -1.3202 | -1.2504 | 0.7350 | 0 | 0 |
| donchian_breakout_signals | half | 1 | 2924.0000 | 265.8182 | 24.4545 | -0.0302 | -0.0620 | 0.0318 | -16.4917 | 11 | 4 | -120.0569 | 335.8291 | -0.6365 | -0.7650 | 0.6650 | 0 | 0 |
| ehlers_reverse_ema_signals | default | 1 | 3820.0000 | 347.2727 | 18.9220 | -0.0153 | -0.0476 | 0.0323 | -16.5242 | 11 | 4 | -130.6060 | 282.1526 | -0.6299 | -0.6954 | 0.5825 | 0 | 0 |
| ssl_channel_signals | half | 1 | 8116.0000 | 737.8182 | 8.7976 | 0.0087 | -0.0230 | 0.0317 | -17.0053 | 11 | 4 | -68.8695 | 310.1122 | -1.3705 | -0.8706 | 0.3425 | 0 | 0 |
| mama_fama_signals | default | 1 | 3080.0000 | 280.0000 | 23.2227 | -0.0288 | -0.0611 | 0.0324 | -17.1127 | 11 | 3 | -144.6223 | 352.6129 | -0.6808 | -0.7398 | 0.6575 | 0 | 0 |
| volatility_quality_signals | double | 1 | 1184.0000 | 107.6364 | 61.1503 | -0.1287 | -0.1597 | 0.0310 | -17.1847 | 11 | 4 | -121.7669 | 387.5345 | -0.5512 | -0.8045 | 0.7650 | 0 | 0 |
| glitch_index_signals | default | 1 | 1756.0000 | 159.6364 | 42.3890 | -0.0766 | -0.1088 | 0.0322 | -17.3682 | 11 | 3 | -165.8111 | 357.5271 | -0.5041 | -0.6622 | 0.7100 | 0 | 0 |
| donchian_breakout_signals | default | 1 | 1686.0000 | 153.2727 | 42.8932 | -0.0833 | -0.1148 | 0.0315 | -17.5916 | 11 | 4 | -176.8981 | 424.1393 | -0.5269 | -0.7073 | 0.7600 | 0 | 0 |
| coral_signals | double | 1 | 6675.0000 | 606.8182 | 10.8193 | 0.0027 | -0.0295 | 0.0321 | -17.8879 | 11 | 5 | -150.8775 | 501.2822 | -0.7283 | -0.7977 | 0.4100 | 0 | 0 |
| polychromatic_momentum_signals | double | 1 | 1449.0000 | 131.7273 | 48.8392 | -0.1065 | -0.1388 | 0.0324 | -18.2863 | 11 | 3 | -191.3763 | 338.1118 | -0.5569 | -0.6813 | 0.7700 | 0 | 0 |
| coppock_curve_signals | double | 1 | 2717.0000 | 247.0000 | 26.3846 | -0.0418 | -0.0741 | 0.0323 | -18.2910 | 11 | 3 | -157.6960 | 353.6737 | -0.5751 | -0.7027 | 0.7175 | 0 | 0 |
| ehlers_reverse_ema_signals | half | 1 | 4967.0000 | 451.5455 | 14.4876 | -0.0095 | -0.0417 | 0.0322 | -18.8194 | 11 | 4 | -127.8225 | 314.8607 | -0.7597 | -0.8336 | 0.6000 | 0 | 0 |
| qqe_mod_signals | double | 1 | 3285.0000 | 298.6364 | 21.9772 | -0.0309 | -0.0634 | 0.0325 | -18.9303 | 11 | 3 | -169.3570 | 373.0121 | -0.6236 | -0.7526 | 0.6750 | 0 | 0 |
| adx_dmi_signals | default | 1 | 705.0000 | 64.0909 | 109.8780 | -0.2656 | -0.2966 | 0.0310 | -19.0116 | 11 | 1 | -91.1729 | 282.5178 | -2.0018 | -1.6142 | 0.8650 | 0 | 0 |
| laguerre_filter_signals | half | 1 | 4300.0000 | 390.9091 | 16.7267 | -0.0171 | -0.0492 | 0.0322 | -19.2457 | 11 | 4 | -147.6632 | 287.5659 | -0.7379 | -0.8514 | 0.6525 | 0 | 0 |
| price_momentum_oscillator_signals | half | 1 | 2419.0000 | 219.9091 | 29.5742 | -0.0573 | -0.0898 | 0.0325 | -19.7427 | 11 | 3 | -165.2510 | 421.9857 | -0.5382 | -0.7366 | 0.7725 | 0 | 0 |
| j_tpo_signals | half | 1 | 3721.0000 | 338.2727 | 19.4305 | -0.0261 | -0.0586 | 0.0325 | -19.8111 | 11 | 3 | -135.9565 | 309.9573 | -0.7616 | -0.8526 | 0.6925 | 0 | 0 |
| linreg_slope_signals | default | 1 | 3718.0000 | 338.0000 | 19.7461 | -0.0264 | -0.0587 | 0.0323 | -19.8527 | 11 | 4 | -182.3888 | 333.4649 | -0.7163 | -0.8504 | 0.6900 | 0 | 0 |
| dpo_signals | half | 1 | 4988.0000 | 453.4545 | 14.2237 | -0.0115 | -0.0440 | 0.0325 | -19.9486 | 11 | 3 | -188.2603 | 439.1603 | -0.5905 | -0.7299 | 0.6150 | 0 | 0 |
| chandelier_exit_signals | double | 1 | 3311.0000 | 301.0000 | 21.6053 | -0.0388 | -0.0688 | 0.0301 | -20.7170 | 11 | 3 | -87.7318 | 309.9804 | -0.9881 | -0.9706 | 0.7525 | 0 | 0 |
| fx_sniper_ergodic_cci_signals | half | 1 | 12280.0000 | 1116.3636 | 5.8682 | 0.0125 | -0.0196 | 0.0321 | -21.8638 | 11 | 5 | -117.8668 | 311.4784 | -1.4090 | -1.0796 | 0.2250 | 0 | 0 |
| polychromatic_momentum_signals | half | 1 | 5673.0000 | 515.7273 | 12.7134 | -0.0101 | -0.0425 | 0.0324 | -21.8984 | 11 | 4 | -144.3512 | 340.1178 | -0.8479 | -0.9604 | 0.6175 | 0 | 0 |
| kuskus_starlight_signals | half | 1 | 5969.0000 | 542.6364 | 12.0637 | -0.0089 | -0.0409 | 0.0320 | -22.2141 | 11 | 4 | -95.3784 | 305.9137 | -1.2512 | -1.0868 | 0.6525 | 0 | 0 |
| kuskus_starlight_signals | default | 1 | 4115.0000 | 374.0909 | 17.4457 | -0.0273 | -0.0596 | 0.0322 | -22.2786 | 11 | 4 | -108.3227 | 316.7307 | -0.9826 | -1.0061 | 0.7075 | 0 | 0 |
| fisher_transform_signals | default | 1 | 17831.0000 | 1621.0000 | 4.0454 | 0.0180 | -0.0141 | 0.0321 | -22.7959 | 11 | 4 | -133.5937 | 346.2289 | -1.0258 | -1.1087 | 0.0675 | 0 | 0 |
| didi_index_signals | default | 1 | 4109.0000 | 373.5455 | 17.5218 | -0.0295 | -0.0618 | 0.0323 | -23.0865 | 11 | 4 | -155.7116 | 297.4434 | -0.8726 | -1.0024 | 0.7425 | 0 | 0 |
| parabolic_sar_signals | double | 1 | 4314.0000 | 392.1818 | 16.6794 | -0.0268 | -0.0591 | 0.0322 | -23.1745 | 11 | 3 | -90.0595 | 337.2024 | -1.4436 | -1.1865 | 0.7175 | 0 | 0 |
| fisher_transform_signals | double | 1 | 16894.0000 | 1535.8182 | 4.2673 | 0.0168 | -0.0153 | 0.0322 | -23.5551 | 11 | 5 | -124.0069 | 355.4063 | -1.1889 | -1.2015 | 0.0950 | 0 | 0 |
| coppock_curve_signals | default | 1 | 3602.0000 | 327.4545 | 19.9117 | -0.0404 | -0.0725 | 0.0321 | -23.7344 | 11 | 4 | -150.6666 | 322.5449 | -0.9091 | -1.0270 | 0.7650 | 0 | 0 |
| qqe_mod_signals | default | 1 | 4586.0000 | 416.9091 | 15.7523 | -0.0250 | -0.0573 | 0.0323 | -23.8931 | 11 | 4 | -157.3849 | 323.2406 | -0.8994 | -1.0866 | 0.7400 | 0 | 0 |
| coppock_curve_signals | half | 1 | 4491.0000 | 408.2727 | 16.0481 | -0.0269 | -0.0591 | 0.0322 | -24.1337 | 11 | 4 | -129.4052 | 317.7134 | -0.9890 | -1.0439 | 0.7425 | 0 | 0 |
| dspo_signals | default | 1 | 2290.0000 | 208.1818 | 31.0288 | -0.0857 | -0.1185 | 0.0327 | -24.6649 | 11 | 3 | -178.9218 | 479.5434 | -0.6798 | -0.9470 | 0.8275 | 0 | 0 |
| vortex_signals | default | 1 | 6865.0000 | 624.0909 | 10.4899 | -0.0076 | -0.0396 | 0.0320 | -24.7265 | 11 | 4 | -116.4589 | 324.2938 | -0.9601 | -1.1030 | 0.5650 | 0 | 0 |
| kalman_filter_signals | double | 1 | 1647.0000 | 149.7273 | 43.5173 | -0.1349 | -0.1671 | 0.0322 | -25.0194 | 11 | 3 | -155.3957 | 408.6969 | -0.6500 | -0.9726 | 0.8825 | 0 | 0 |
| hieken_ashi_smoothed_signals | default | 1 | 4096.0000 | 372.3636 | 17.2014 | -0.0402 | -0.0725 | 0.0323 | -27.0104 | 11 | 4 | -162.5801 | 351.9108 | -1.1498 | -1.2363 | 0.8100 | 0 | 0 |
| j_tpo_signals | default | 1 | 1927.0000 | 175.1818 | 37.2361 | -0.1318 | -0.1640 | 0.0322 | -28.7218 | 11 | 3 | -182.5889 | 409.8028 | -0.8679 | -1.1564 | 0.9200 | 0 | 0 |
| vortex_signals | double | 1 | 4879.0000 | 443.5455 | 14.5991 | -0.0339 | -0.0666 | 0.0327 | -29.5476 | 11 | 4 | -211.6535 | 498.0921 | -0.7715 | -1.1086 | 0.8350 | 0 | 0 |
| linreg_slope_signals | half | 1 | 7486.0000 | 680.5455 | 9.7366 | -0.0115 | -0.0437 | 0.0322 | -29.7490 | 11 | 3 | -143.9377 | 422.3377 | -1.6834 | -1.5004 | 0.6975 | 0 | 0 |
| kalman_filter_signals | default | 1 | 2318.0000 | 210.7273 | 30.9560 | -0.1091 | -0.1415 | 0.0324 | -29.8129 | 11 | 3 | -183.0971 | 447.1723 | -0.8206 | -1.1301 | 0.9025 | 0 | 0 |
| vortex_signals | half | 1 | 9843.0000 | 894.8182 | 7.2920 | -0.0015 | -0.0335 | 0.0320 | -30.0166 | 11 | 3 | -136.8914 | 422.7183 | -1.5837 | -1.4727 | 0.5625 | 0 | 0 |
| qqe_mod_signals | half | 1 | 6285.0000 | 571.3636 | 11.4495 | -0.0240 | -0.0562 | 0.0322 | -32.0960 | 11 | 4 | -139.6034 | 398.7174 | -1.4332 | -1.5139 | 0.7650 | 0 | 0 |
| center_of_gravity_signals | default | 1 | 12981.0000 | 1180.0909 | 5.5590 | 0.0050 | -0.0272 | 0.0322 | -32.1427 | 11 | 4 | -132.7022 | 464.7795 | -1.4250 | -1.3693 | 0.3750 | 0 | 0 |
| center_of_gravity_signals | double | 1 | 8650.0000 | 786.3636 | 8.3153 | -0.0099 | -0.0423 | 0.0324 | -33.2365 | 11 | 2 | -126.6028 | 485.2497 | -2.3108 | -1.6094 | 0.6775 | 0 | 0 |
| adx_dmi_signals | half | 1 | 6157.0000 | 559.7273 | 11.7111 | -0.0300 | -0.0618 | 0.0317 | -34.5717 | 11 | 2 | -98.8669 | 442.9876 | -2.0808 | -1.9407 | 0.7975 | 0 | 0 |
| didi_index_signals | double | 1 | 4971.0000 | 451.9091 | 14.4770 | -0.0451 | -0.0775 | 0.0324 | -35.0103 | 11 | 5 | -121.5817 | 493.9227 | -1.3960 | -1.4417 | 0.8825 | 0 | 0 |
| coral_signals | default | 1 | 13360.0000 | 1214.5455 | 5.4032 | 0.0030 | -0.0290 | 0.0321 | -35.2645 | 11 | 3 | -153.9255 | 462.5936 | -1.7221 | -1.5263 | 0.4475 | 0 | 0 |
| bears_bulls_impulse_signals | default | 1 | 4587.0000 | 417.0000 | 16.1469 | -0.0586 | -0.0911 | 0.0325 | -37.9813 | 11 | 3 | -168.6906 | 467.1186 | -1.3657 | -1.6412 | 0.9200 | 0 | 0 |
| relative_vigor_index_signals | default | 1 | 12725.0000 | 1156.8182 | 5.6658 | -0.0011 | -0.0332 | 0.0321 | -38.4107 | 11 | 4 | -105.0624 | 499.1993 | -2.7596 | -1.9382 | 0.5250 | 0 | 0 |
| bears_bulls_impulse_signals | half | 1 | 4860.0000 | 441.8182 | 15.3305 | -0.0564 | -0.0887 | 0.0324 | -39.2095 | 11 | 4 | -151.7352 | 492.7652 | -1.9010 | -1.7879 | 0.9300 | 0 | 0 |
| fisher_transform_signals | half | 1 | 19851.0000 | 1804.6364 | 3.6326 | 0.0078 | -0.0243 | 0.0321 | -43.9411 | 11 | 3 | -178.8642 | 526.6384 | -2.1048 | -2.1209 | 0.2225 | 0 | 0 |
| coral_signals | half | 1 | 25744.0000 | 2340.3636 | 2.8184 | 0.0073 | -0.0247 | 0.0321 | -57.8939 | 11 | 3 | -189.7799 | 694.4348 | -2.4028 | -2.6435 | 0.1850 | 0 | 0 |
| relative_vigor_index_signals | double | 1 | 12545.0000 | 1140.4545 | 5.7364 | -0.0203 | -0.0527 | 0.0323 | -60.0798 | 11 | 2 | -127.8654 | 672.8109 | -3.5245 | -2.9145 | 0.8600 | 0 | 0 |
| relative_vigor_index_signals | half | 1 | 13656.0000 | 1241.4545 | 5.2987 | -0.0170 | -0.0492 | 0.0322 | -61.0230 | 11 | 2 | -152.1934 | 707.7223 | -2.8933 | -2.7786 | 0.8550 | 0 | 0 |
| center_of_gravity_signals | half | 1 | 20412.0000 | 1855.6364 | 3.5438 | -0.0021 | -0.0343 | 0.0322 | -63.6655 | 11 | 3 | -191.8082 | 703.7978 | -2.5764 | -2.9871 | 0.5925 | 0 | 0 |
| rex_oscillator_signals | double | 1 | 16510.0000 | 1500.9091 | 4.3588 | -0.0166 | -0.0490 | 0.0324 | -73.5103 | 11 | 0 | -178.4950 | 825.6876 | -4.5376 | -3.3924 | 0.8750 | 0 | 0 |


**0 of 117 candidate-settings clear the empirical best-of-39 floor; 0 clear the alone floor.** 16 of 117 have a positive net R per year.


### C1 — `flip_only`, stability across the three settings

`sign_agree = 1` means all three settings agree on the sign of net R per year. A candidate positive on one setting and negative on two is being fitted, not measured.

| indicator | settings | settings_positive | sign_agree | R_per_year_min | R_per_year_med | R_per_year_max | spread |
|---|---:|---:|---:|---:|---:|---:|---:|
| halftrend_signals | 3 | 3 | 1 | 5.9247 | 15.6429 | 19.8321 | 13.9074 |
| ichimoku_signals | 3 | 3 | 1 | 7.4083 | 10.6806 | 16.1375 | 8.7292 |
| lemantrend_signals | 3 | 2 | 0 | -4.6365 | 0.3032 | 1.5005 | 6.1369 |
| schaff_trend_cycle_signals | 3 | 1 | 0 | -16.2639 | -1.2186 | 1.1822 | 17.4461 |
| waddah_attar_explosion_signals | 3 | 0 | 1 | -4.3163 | -3.9605 | -3.7575 | 0.5587 |
| dpo_signals | 3 | 1 | 0 | -19.9486 | -4.4866 | 1.3464 | 21.2949 |
| aroon_signals | 3 | 0 | 1 | -10.4859 | -8.3396 | -4.5539 | 5.9320 |
| parabolic_sar_signals | 3 | 0 | 1 | -23.1745 | -8.4971 | -7.9304 | 15.2441 |
| supertrend_signals | 3 | 0 | 1 | -13.8546 | -9.4404 | -7.0126 | 6.8421 |
| price_momentum_oscillator_signals | 3 | 1 | 0 | -19.7427 | -9.8361 | 9.1533 | 28.8961 |
| trend_direction_force_index_signals | 3 | 1 | 0 | -14.1445 | -10.4652 | 4.9623 | 19.1069 |
| laguerre_filter_signals | 3 | 1 | 0 | -19.2457 | -11.1367 | 13.9787 | 33.2244 |
| kase_peak_oscillator_signals | 3 | 0 | 1 | -13.8467 | -12.5488 | -9.9325 | 3.9142 |
| dspo_signals | 3 | 1 | 0 | -24.6649 | -13.0385 | 4.4945 | 29.1594 |
| rex_oscillator_signals | 3 | 0 | 1 | -73.5103 | -14.6947 | -10.2548 | 63.2555 |
| chandelier_exit_signals | 3 | 0 | 1 | -20.7170 | -14.9651 | -12.2435 | 8.4734 |
| ssl_channel_signals | 3 | 0 | 1 | -17.0053 | -15.0534 | -12.0380 | 4.9673 |
| volatility_quality_signals | 3 | 0 | 1 | -17.1847 | -15.1707 | -5.0230 | 12.1618 |
| mama_fama_signals | 3 | 0 | 1 | -17.1127 | -15.2244 | -3.8599 | 13.2529 |
| glitch_index_signals | 3 | 0 | 1 | -17.3682 | -15.9647 | -14.0246 | 3.3436 |
| fx_sniper_ergodic_cci_signals | 3 | 0 | 1 | -21.8638 | -16.0983 | -14.2622 | 7.6016 |
| hieken_ashi_smoothed_signals | 3 | 0 | 1 | -27.0104 | -16.1996 | -13.5671 | 13.4433 |
| donchian_breakout_signals | 3 | 0 | 1 | -17.5916 | -16.4917 | -3.3447 | 14.2469 |
| ehlers_reverse_ema_signals | 3 | 0 | 1 | -18.8194 | -16.5242 | -14.4545 | 4.3650 |
| polychromatic_momentum_signals | 3 | 0 | 1 | -21.8984 | -18.2863 | -14.2142 | 7.6841 |
| adx_dmi_signals | 3 | 1 | 0 | -34.5717 | -19.0116 | 8.7855 | 43.3572 |
| j_tpo_signals | 3 | 1 | 0 | -28.7218 | -19.8111 | 20.0769 | 48.7987 |
| linreg_slope_signals | 3 | 0 | 1 | -29.7490 | -19.8527 | -15.3254 | 14.4236 |
| kuskus_starlight_signals | 3 | 0 | 1 | -22.2786 | -22.2141 | -13.1398 | 9.1387 |
| didi_index_signals | 3 | 0 | 1 | -35.0103 | -23.0865 | -13.2296 | 21.7807 |
| fisher_transform_signals | 3 | 0 | 1 | -43.9411 | -23.5551 | -22.7959 | 21.1452 |
| coppock_curve_signals | 3 | 0 | 1 | -24.1337 | -23.7344 | -18.2910 | 5.8428 |
| qqe_mod_signals | 3 | 0 | 1 | -32.0960 | -23.8931 | -18.9303 | 13.1657 |
| kalman_filter_signals | 3 | 0 | 1 | -29.8129 | -25.0194 | -14.6382 | 15.1747 |
| vortex_signals | 3 | 0 | 1 | -30.0166 | -29.5476 | -24.7265 | 5.2901 |
| center_of_gravity_signals | 3 | 0 | 1 | -63.6655 | -33.2365 | -32.1427 | 31.5228 |
| coral_signals | 3 | 0 | 1 | -57.8939 | -35.2645 | -17.8879 | 40.0060 |
| bears_bulls_impulse_signals | 3 | 0 | 1 | -39.2095 | -37.9813 | -13.3509 | 25.8586 |
| relative_vigor_index_signals | 3 | 0 | 1 | -61.0230 | -60.0798 | -38.4107 | 22.6122 |


**30 of 39 candidates have all three settings agreeing in sign.**


## C1 — `jack`, fixed settings, unseen trade years 2005-2015

Empirical yearly-t floors **from the random-entry null**: alone **0.746**, best-of-39 **2.401**. The analytic equivalents on 11 yearly observations are 1.812 and 3.973 — the empirical ones are lower because the analytic formula assumes a **zero-mean** null while the real null also pays costs, so it is centred below zero.

| indicator | setting | distinct_setting | n_entered | trades_per_year | mean_bars | R_gross_per_trade | R_net_per_trade | cost_per_trade | R_net_per_year | years | years_positive | worst_year | worst_dip_R | t_yearly | t_block_boot | null_p | clears_alone_emp | clears_family_emp |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ichimoku_signals | half | 1 | 1510.0000 | 137.2727 | 8.9152 | 0.0485 | 0.0161 | 0.0324 | 2.2066 | 11 | 7 | -21.0125 | 30.2974 | 0.4238 | 0.4175 | 0.2200 | 0 | 0 |
| schaff_trend_cycle_signals | default | 1 | 2712.0000 | 246.5455 | 8.2006 | 0.0344 | 0.0025 | 0.0319 | 0.6258 | 11 | 6 | -24.6162 | 86.9860 | 0.1157 | 0.0853 | 0.1875 | 0 | 0 |
| aroon_signals | default | 1 | 2833.0000 | 257.5455 | 8.6181 | 0.0332 | 0.0010 | 0.0322 | 0.2555 | 11 | 6 | -35.1701 | 73.8329 | 0.0320 | 0.0353 | 0.1375 | 0 | 0 |
| adx_dmi_signals | double | 1 | 75.0000 | 6.8182 | 7.5467 | 0.0477 | 0.0195 | 0.0282 | 0.1330 | 11 | 4 | -2.8186 | 8.2995 | 0.1657 | 0.1652 | 0.3250 | 0 | 0 |
| waddah_attar_explosion_signals | double | 1 | 1615.0000 | 146.8182 | 6.9325 | 0.0329 | 0.0002 | 0.0327 | 0.0343 | 11 | 5 | -20.7460 | 59.0572 | 0.0058 | 0.0089 | 0.2350 | 0 | 0 |
| halftrend_signals | double | 1 | 172.0000 | 15.6364 | 9.0756 | 0.0152 | -0.0154 | 0.0305 | -0.2402 | 11 | 3 | -4.1668 | 20.3276 | -0.2115 | -0.1648 | 0.4675 | 0 | 0 |
| halftrend_signals | default | 1 | 322.0000 | 29.2727 | 8.8137 | 0.0141 | -0.0170 | 0.0311 | -0.4972 | 11 | 5 | -5.5515 | 20.0346 | -0.4109 | -0.2681 | 0.4300 | 0 | 0 |
| trend_direction_force_index_signals | double | 1 | 2448.0000 | 222.5455 | 8.5114 | 0.0274 | -0.0048 | 0.0322 | -1.0620 | 11 | 5 | -40.2917 | 94.7967 | -0.1160 | -0.1366 | 0.2775 | 0 | 0 |
| aroon_signals | double | 1 | 1450.0000 | 131.8182 | 8.6586 | 0.0242 | -0.0082 | 0.0324 | -1.0751 | 11 | 5 | -29.0059 | 88.6418 | -0.1441 | -0.2108 | 0.3175 | 0 | 0 |
| ichimoku_signals | double | 1 | 1882.0000 | 171.0909 | 8.6041 | 0.0255 | -0.0067 | 0.0322 | -1.1437 | 11 | 4 | -26.8794 | 78.2876 | -0.1676 | -0.1755 | 0.3200 | 0 | 0 |
| waddah_attar_explosion_signals | half | 1 | 1613.0000 | 146.6364 | 7.2728 | 0.0238 | -0.0090 | 0.0328 | -1.3165 | 11 | 5 | -27.0798 | 82.9160 | -0.1806 | -0.3288 | 0.3250 | 0 | 0 |
| ichimoku_signals | default | 1 | 1350.0000 | 122.7273 | 8.4785 | 0.0189 | -0.0139 | 0.0329 | -1.7119 | 11 | 4 | -25.6514 | 53.8622 | -0.4163 | -0.3447 | 0.4150 | 0 | 0 |
| hieken_ashi_smoothed_signals | double | 1 | 2746.0000 | 249.6364 | 8.3019 | 0.0241 | -0.0078 | 0.0318 | -1.9403 | 11 | 5 | -38.9685 | 70.3311 | -0.2640 | -0.2571 | 0.2425 | 0 | 0 |
| mama_fama_signals | double | 1 | 1456.0000 | 132.3636 | 8.8386 | 0.0165 | -0.0159 | 0.0324 | -2.1019 | 11 | 5 | -29.7046 | 64.0054 | -0.3205 | -0.3758 | 0.3650 | 0 | 0 |
| waddah_attar_explosion_signals | default | 1 | 1612.0000 | 146.5455 | 7.0037 | 0.0163 | -0.0165 | 0.0328 | -2.4140 | 11 | 5 | -24.1325 | 64.0053 | -0.3731 | -0.6529 | 0.3325 | 0 | 0 |
| donchian_breakout_signals | double | 1 | 854.0000 | 77.6364 | 8.6967 | 0.0007 | -0.0314 | 0.0321 | -2.4347 | 11 | 4 | -27.6198 | 51.0668 | -0.4539 | -0.5419 | 0.4850 | 0 | 0 |
| dspo_signals | half | 1 | 4298.0000 | 390.7273 | 8.5537 | 0.0248 | -0.0073 | 0.0321 | -2.8464 | 11 | 5 | -65.7732 | 124.0434 | -0.2885 | -0.3109 | 0.2025 | 0 | 0 |
| donchian_breakout_signals | default | 1 | 1686.0000 | 153.2727 | 9.0896 | 0.0125 | -0.0189 | 0.0315 | -2.8974 | 11 | 5 | -22.3719 | 63.3991 | -0.5483 | -0.5496 | 0.3775 | 0 | 0 |
| lemantrend_signals | double | 1 | 1420.0000 | 129.0909 | 6.9577 | 0.0055 | -0.0271 | 0.0326 | -3.4993 | 11 | 5 | -28.0566 | 70.4735 | -0.6146 | -0.9801 | 0.4750 | 0 | 0 |
| price_momentum_oscillator_signals | double | 1 | 1130.0000 | 102.7273 | 8.7071 | -0.0040 | -0.0368 | 0.0328 | -3.7805 | 11 | 5 | -29.6063 | 93.9792 | -0.6552 | -0.8663 | 0.5675 | 0 | 0 |
| volatility_quality_signals | default | 1 | 3390.0000 | 308.1818 | 8.6209 | 0.0192 | -0.0125 | 0.0318 | -3.8623 | 11 | 5 | -49.4322 | 91.8428 | -0.5061 | -0.4990 | 0.2600 | 0 | 0 |
| halftrend_signals | half | 1 | 538.0000 | 48.9091 | 7.8271 | -0.0518 | -0.0831 | 0.0314 | -4.0650 | 11 | 3 | -17.3141 | 61.0637 | -1.6709 | -1.4104 | 0.7350 | 0 | 0 |
| j_tpo_signals | double | 1 | 915.0000 | 83.1818 | 8.2098 | -0.0175 | -0.0501 | 0.0325 | -4.1634 | 11 | 3 | -17.6752 | 70.1961 | -1.5171 | -1.2317 | 0.6250 | 0 | 0 |
| laguerre_filter_signals | double | 1 | 965.0000 | 87.7273 | 8.5057 | -0.0155 | -0.0475 | 0.0321 | -4.1700 | 11 | 3 | -31.3430 | 99.6793 | -0.8206 | -1.0590 | 0.5950 | 0 | 0 |
| supertrend_signals | double | 1 | 1796.0000 | 163.2727 | 8.9889 | 0.0056 | -0.0259 | 0.0315 | -4.2350 | 11 | 3 | -33.1285 | 68.4717 | -0.8337 | -0.7543 | 0.4525 | 0 | 0 |
| price_momentum_oscillator_signals | default | 1 | 1732.0000 | 157.4545 | 8.9117 | 0.0054 | -0.0269 | 0.0323 | -4.2413 | 11 | 5 | -37.4452 | 63.3646 | -0.6162 | -0.7408 | 0.4650 | 0 | 0 |
| chandelier_exit_signals | default | 1 | 2359.0000 | 214.4545 | 8.9224 | 0.0105 | -0.0203 | 0.0307 | -4.3500 | 11 | 6 | -30.8629 | 70.2632 | -0.9086 | -0.6639 | 0.3650 | 0 | 0 |
| polychromatic_momentum_signals | default | 1 | 2883.0000 | 262.0909 | 8.3944 | 0.0157 | -0.0166 | 0.0324 | -4.3590 | 11 | 4 | -37.5596 | 98.3907 | -0.7208 | -0.5642 | 0.3075 | 0 | 0 |
| kuskus_starlight_signals | default | 1 | 4115.0000 | 374.0909 | 8.4710 | 0.0204 | -0.0118 | 0.0322 | -4.4268 | 11 | 6 | -45.9027 | 88.7529 | -0.6863 | -0.5339 | 0.2175 | 0 | 0 |
| linreg_slope_signals | double | 1 | 2439.0000 | 221.7273 | 8.9459 | 0.0120 | -0.0202 | 0.0323 | -4.4871 | 11 | 4 | -36.4281 | 89.3574 | -0.5366 | -0.6354 | 0.3900 | 0 | 0 |
| glitch_index_signals | double | 1 | 2344.0000 | 213.0909 | 8.8349 | 0.0110 | -0.0216 | 0.0326 | -4.5947 | 11 | 5 | -45.0092 | 101.8111 | -0.5238 | -0.6744 | 0.4425 | 0 | 0 |
| chandelier_exit_signals | half | 1 | 2126.0000 | 193.2727 | 8.9826 | 0.0071 | -0.0245 | 0.0316 | -4.7416 | 11 | 6 | -35.3632 | 80.6550 | -0.9266 | -0.7780 | 0.3625 | 0 | 0 |
| dpo_signals | double | 1 | 2116.0000 | 192.3636 | 6.7023 | 0.0074 | -0.0250 | 0.0324 | -4.8111 | 11 | 4 | -29.4812 | 75.8478 | -1.1841 | -0.9948 | 0.4300 | 0 | 0 |
| supertrend_signals | default | 1 | 1811.0000 | 164.6364 | 8.8647 | 0.0019 | -0.0297 | 0.0316 | -4.8928 | 11 | 4 | -31.5497 | 73.0526 | -1.1253 | -0.8889 | 0.4500 | 0 | 0 |
| laguerre_filter_signals | default | 1 | 2075.0000 | 188.6364 | 8.4231 | 0.0057 | -0.0264 | 0.0322 | -4.9880 | 11 | 5 | -48.7675 | 78.9370 | -0.6290 | -0.8287 | 0.4850 | 0 | 0 |
| donchian_breakout_signals | half | 1 | 2924.0000 | 265.8182 | 8.7883 | 0.0130 | -0.0188 | 0.0318 | -5.0103 | 11 | 4 | -48.9143 | 137.8856 | -0.6442 | -0.6309 | 0.3850 | 0 | 0 |
| ehlers_reverse_ema_signals | default | 1 | 3820.0000 | 347.2727 | 8.7202 | 0.0172 | -0.0151 | 0.0323 | -5.2315 | 11 | 5 | -68.4530 | 147.3204 | -0.4921 | -0.5801 | 0.2925 | 0 | 0 |
| dspo_signals | double | 1 | 1106.0000 | 100.5455 | 8.3888 | -0.0200 | -0.0530 | 0.0330 | -5.3282 | 11 | 4 | -25.7638 | 86.3966 | -1.0628 | -1.2476 | 0.6450 | 0 | 0 |
| kalman_filter_signals | half | 1 | 3294.0000 | 299.4545 | 8.7298 | 0.0144 | -0.0180 | 0.0324 | -5.3978 | 11 | 6 | -52.0327 | 126.3921 | -0.5390 | -0.6613 | 0.3600 | 0 | 0 |
| schaff_trend_cycle_signals | half | 1 | 2807.0000 | 255.1818 | 7.5746 | 0.0104 | -0.0213 | 0.0318 | -5.4412 | 11 | 4 | -33.5611 | 116.9061 | -0.8981 | -0.7828 | 0.3325 | 0 | 0 |
| mama_fama_signals | default | 1 | 3080.0000 | 280.0000 | 8.7494 | 0.0122 | -0.0201 | 0.0324 | -5.6416 | 11 | 5 | -22.9368 | 89.9581 | -1.2229 | -0.7834 | 0.3375 | 0 | 0 |
| ehlers_reverse_ema_signals | double | 1 | 2832.0000 | 257.4545 | 8.9693 | 0.0103 | -0.0225 | 0.0328 | -5.7858 | 11 | 5 | -44.8846 | 92.8282 | -0.9817 | -0.8184 | 0.4225 | 0 | 0 |
| lemantrend_signals | default | 1 | 1936.0000 | 176.0000 | 6.2149 | -0.0004 | -0.0329 | 0.0325 | -5.7957 | 11 | 3 | -21.7377 | 76.1967 | -1.5323 | -1.4364 | 0.5100 | 0 | 0 |
| qqe_mod_signals | double | 1 | 3285.0000 | 298.6364 | 8.2749 | 0.0122 | -0.0202 | 0.0325 | -6.0469 | 11 | 6 | -57.2191 | 117.2596 | -0.6783 | -0.7687 | 0.3575 | 0 | 0 |
| supertrend_signals | half | 1 | 1851.0000 | 168.2727 | 8.7115 | -0.0047 | -0.0365 | 0.0318 | -6.1391 | 11 | 5 | -31.1984 | 112.4828 | -1.4451 | -1.1106 | 0.5175 | 0 | 0 |
| volatility_quality_signals | double | 1 | 1184.0000 | 107.6364 | 8.2407 | -0.0264 | -0.0574 | 0.0310 | -6.1738 | 11 | 4 | -22.2472 | 93.0119 | -1.4363 | -1.5709 | 0.6825 | 0 | 0 |
| lemantrend_signals | half | 1 | 2613.0000 | 237.5455 | 5.4367 | 0.0062 | -0.0266 | 0.0329 | -6.3280 | 11 | 3 | -38.5717 | 82.3275 | -1.4976 | -1.2193 | 0.4475 | 0 | 0 |
| adx_dmi_signals | default | 1 | 986.0000 | 89.6364 | 7.8347 | -0.0437 | -0.0745 | 0.0307 | -6.6739 | 11 | 2 | -15.6632 | 84.0339 | -3.2419 | -2.1681 | 0.8200 | 0 | 0 |
| glitch_index_signals | default | 1 | 3105.0000 | 282.2727 | 8.7166 | 0.0066 | -0.0257 | 0.0322 | -7.2449 | 11 | 3 | -46.2482 | 101.5151 | -0.7630 | -0.8916 | 0.4125 | 0 | 0 |
| kase_peak_oscillator_signals | double | 1 | 2840.0000 | 258.1818 | 8.3736 | 0.0037 | -0.0284 | 0.0321 | -7.3377 | 11 | 4 | -54.9465 | 104.8875 | -0.8164 | -1.0763 | 0.4350 | 0 | 0 |
| dspo_signals | default | 1 | 2290.0000 | 208.1818 | 8.7751 | -0.0031 | -0.0358 | 0.0327 | -7.4611 | 11 | 4 | -38.2651 | 108.5255 | -1.0852 | -1.2071 | 0.4675 | 0 | 0 |
| polychromatic_momentum_signals | half | 1 | 5674.0000 | 515.8182 | 7.5860 | 0.0179 | -0.0145 | 0.0324 | -7.4836 | 11 | 6 | -90.8932 | 176.6281 | -0.5987 | -0.6540 | 0.2050 | 0 | 0 |
| aroon_signals | half | 1 | 5376.0000 | 488.7273 | 7.8054 | 0.0164 | -0.0156 | 0.0320 | -7.6409 | 11 | 4 | -94.6491 | 193.0718 | -0.5709 | -0.7020 | 0.2575 | 0 | 0 |
| schaff_trend_cycle_signals | double | 1 | 2514.0000 | 228.5455 | 8.2116 | -0.0017 | -0.0334 | 0.0318 | -7.6416 | 11 | 2 | -32.2915 | 158.0593 | -1.1663 | -1.1360 | 0.5100 | 0 | 0 |
| j_tpo_signals | default | 1 | 1928.0000 | 175.2727 | 8.3154 | -0.0133 | -0.0455 | 0.0322 | -7.9716 | 11 | 4 | -60.8661 | 105.4999 | -0.9719 | -1.3675 | 0.6100 | 0 | 0 |
| ehlers_reverse_ema_signals | half | 1 | 4967.0000 | 451.5455 | 8.4405 | 0.0145 | -0.0177 | 0.0322 | -7.9969 | 11 | 4 | -81.4401 | 167.1215 | -0.7910 | -0.7254 | 0.3050 | 0 | 0 |
| laguerre_filter_signals | half | 1 | 4300.0000 | 390.9091 | 8.2619 | 0.0115 | -0.0206 | 0.0322 | -8.0703 | 11 | 5 | -52.9343 | 148.4503 | -0.9917 | -0.8434 | 0.3500 | 0 | 0 |
| kalman_filter_signals | double | 1 | 1647.0000 | 149.7273 | 8.6897 | -0.0220 | -0.0542 | 0.0322 | -8.1085 | 11 | 3 | -40.9328 | 100.3422 | -1.1809 | -1.5688 | 0.6775 | 0 | 0 |
| coppock_curve_signals | double | 1 | 2717.0000 | 247.0000 | 8.6533 | -0.0016 | -0.0338 | 0.0323 | -8.3513 | 11 | 3 | -37.3757 | 123.9471 | -1.6989 | -1.1765 | 0.4800 | 0 | 0 |
| chandelier_exit_signals | double | 1 | 3311.0000 | 301.0000 | 7.8593 | 0.0023 | -0.0277 | 0.0301 | -8.3521 | 11 | 4 | -55.4132 | 102.4190 | -1.1080 | -1.2068 | 0.4750 | 0 | 0 |
| mama_fama_signals | half | 1 | 6745.0000 | 613.1818 | 7.3045 | 0.0178 | -0.0144 | 0.0322 | -8.8358 | 11 | 5 | -87.7425 | 157.3740 | -0.9111 | -0.8053 | 0.2075 | 0 | 0 |
| dpo_signals | default | 1 | 3447.0000 | 313.3636 | 6.8538 | 0.0045 | -0.0285 | 0.0329 | -8.9190 | 11 | 4 | -63.1892 | 168.2271 | -1.0790 | -1.3152 | 0.4425 | 0 | 0 |
| ssl_channel_signals | double | 1 | 4045.0000 | 367.7273 | 8.8131 | 0.0077 | -0.0244 | 0.0321 | -8.9841 | 11 | 5 | -52.9905 | 157.0110 | -1.0654 | -0.9783 | 0.3725 | 0 | 0 |
| price_momentum_oscillator_signals | half | 1 | 2419.0000 | 219.9091 | 8.7214 | -0.0085 | -0.0409 | 0.0325 | -9.0044 | 11 | 4 | -46.1236 | 111.0068 | -1.2933 | -1.4029 | 0.5500 | 0 | 0 |
| dpo_signals | half | 1 | 4988.0000 | 453.4545 | 6.9637 | 0.0118 | -0.0207 | 0.0325 | -9.3885 | 11 | 4 | -41.3450 | 147.3103 | -1.4270 | -1.1296 | 0.3425 | 0 | 0 |
| trend_direction_force_index_signals | half | 1 | 5549.0000 | 504.4545 | 8.6102 | 0.0118 | -0.0202 | 0.0320 | -10.1777 | 11 | 5 | -80.0922 | 175.1279 | -0.8661 | -0.8739 | 0.3950 | 0 | 0 |
| kuskus_starlight_signals | half | 1 | 5969.0000 | 542.6364 | 8.0412 | 0.0129 | -0.0192 | 0.0320 | -10.3965 | 11 | 5 | -60.0561 | 176.7215 | -1.2564 | -0.9405 | 0.3025 | 0 | 0 |
| linreg_slope_signals | default | 1 | 4575.0000 | 415.9091 | 8.5867 | 0.0072 | -0.0250 | 0.0322 | -10.4006 | 11 | 4 | -60.0262 | 179.7967 | -0.9025 | -1.0095 | 0.3925 | 0 | 0 |
| kalman_filter_signals | default | 1 | 2318.0000 | 210.7273 | 8.5410 | -0.0171 | -0.0495 | 0.0324 | -10.4371 | 11 | 4 | -51.9384 | 132.4483 | -1.4748 | -1.5264 | 0.6350 | 0 | 0 |
| j_tpo_signals | half | 1 | 3723.0000 | 338.4545 | 8.3688 | 0.0008 | -0.0317 | 0.0325 | -10.7202 | 11 | 5 | -43.8520 | 148.9984 | -1.5173 | -1.3435 | 0.5075 | 0 | 0 |
| kase_peak_oscillator_signals | default | 1 | 3906.0000 | 355.0909 | 8.3564 | 0.0008 | -0.0312 | 0.0320 | -11.0834 | 11 | 5 | -62.3395 | 158.8028 | -1.5127 | -1.3195 | 0.5350 | 0 | 0 |
| qqe_mod_signals | default | 1 | 4586.0000 | 416.9091 | 7.9169 | 0.0050 | -0.0274 | 0.0323 | -11.4038 | 11 | 4 | -67.9604 | 185.8359 | -1.2947 | -1.2419 | 0.4175 | 0 | 0 |
| kuskus_starlight_signals | double | 1 | 2825.0000 | 256.8182 | 8.3904 | -0.0123 | -0.0445 | 0.0322 | -11.4197 | 11 | 5 | -57.9034 | 142.7820 | -1.3596 | -1.6927 | 0.6475 | 0 | 0 |
| vortex_signals | double | 1 | 4882.0000 | 443.8182 | 6.5219 | 0.0065 | -0.0262 | 0.0327 | -11.6340 | 11 | 3 | -47.4677 | 154.7554 | -1.2449 | -1.4608 | 0.4225 | 0 | 0 |
| coppock_curve_signals | default | 1 | 3602.0000 | 327.4545 | 8.5428 | -0.0036 | -0.0357 | 0.0321 | -11.6826 | 11 | 5 | -57.0942 | 166.8891 | -1.1233 | -1.3577 | 0.5125 | 0 | 0 |
| trend_direction_force_index_signals | default | 1 | 3678.0000 | 334.3636 | 8.5691 | -0.0027 | -0.0350 | 0.0323 | -11.7128 | 11 | 3 | -58.8660 | 171.8030 | -1.0017 | -1.2452 | 0.6275 | 0 | 0 |
| bears_bulls_impulse_signals | double | 1 | 5475.0000 | 497.7273 | 8.9991 | 0.0076 | -0.0249 | 0.0324 | -12.3714 | 11 | 5 | -68.4184 | 177.1138 | -1.0352 | -1.1567 | 0.3975 | 0 | 0 |
| didi_index_signals | half | 1 | 4969.0000 | 451.7273 | 8.0177 | 0.0040 | -0.0282 | 0.0322 | -12.7173 | 11 | 3 | -87.6461 | 195.2001 | -1.4047 | -1.2661 | 0.4275 | 0 | 0 |
| vortex_signals | default | 1 | 6869.0000 | 624.4545 | 6.4299 | 0.0114 | -0.0206 | 0.0320 | -12.8676 | 11 | 5 | -69.8169 | 193.7722 | -1.2491 | -1.1780 | 0.2750 | 0 | 0 |
| polychromatic_momentum_signals | double | 1 | 1449.0000 | 131.7273 | 8.0014 | -0.0669 | -0.0993 | 0.0324 | -13.0750 | 11 | 1 | -30.9746 | 166.9010 | -2.1414 | -2.5639 | 0.8900 | 0 | 0 |
| coppock_curve_signals | half | 1 | 4491.0000 | 408.2727 | 8.1679 | 0.0001 | -0.0321 | 0.0322 | -13.1101 | 11 | 5 | -59.5612 | 188.6383 | -1.3315 | -1.3806 | 0.5475 | 0 | 0 |
| ssl_channel_signals | default | 1 | 5794.0000 | 526.7273 | 8.0664 | 0.0062 | -0.0258 | 0.0320 | -13.6115 | 11 | 4 | -87.6369 | 223.7006 | -1.1924 | -1.1802 | 0.3725 | 0 | 0 |
| kase_peak_oscillator_signals | half | 1 | 5519.0000 | 501.7273 | 7.8775 | 0.0044 | -0.0274 | 0.0319 | -13.7709 | 11 | 4 | -86.0409 | 189.5540 | -1.5098 | -1.3354 | 0.4150 | 0 | 0 |
| glitch_index_signals | half | 1 | 3630.0000 | 330.0000 | 8.4876 | -0.0101 | -0.0425 | 0.0324 | -14.0129 | 11 | 4 | -64.9131 | 199.7362 | -1.1487 | -1.5158 | 0.6400 | 0 | 0 |
| parabolic_sar_signals | default | 1 | 6644.0000 | 604.0000 | 7.4181 | 0.0089 | -0.0233 | 0.0321 | -14.0611 | 11 | 4 | -80.6743 | 222.9344 | -1.1916 | -1.2578 | 0.3675 | 0 | 0 |
| rex_oscillator_signals | default | 1 | 12531.0000 | 1139.1818 | 4.0759 | 0.0196 | -0.0125 | 0.0322 | -14.2833 | 11 | 3 | -60.4088 | 238.6877 | -1.2325 | -1.0921 | 0.0550 | 0 | 0 |
| parabolic_sar_signals | half | 1 | 9606.0000 | 873.2727 | 6.1799 | 0.0154 | -0.0165 | 0.0320 | -14.4444 | 11 | 3 | -89.5437 | 250.0187 | -1.0619 | -1.0716 | 0.2075 | 0 | 0 |
| parabolic_sar_signals | double | 1 | 4314.0000 | 392.1818 | 8.2668 | -0.0054 | -0.0376 | 0.0322 | -14.7595 | 11 | 3 | -57.4953 | 235.4060 | -1.5896 | -1.5632 | 0.5850 | 0 | 0 |
| hieken_ashi_smoothed_signals | half | 1 | 5257.0000 | 477.9091 | 7.6858 | 0.0012 | -0.0310 | 0.0322 | -14.8040 | 11 | 4 | -81.5473 | 261.1084 | -1.0670 | -1.3405 | 0.4725 | 0 | 0 |
| didi_index_signals | default | 1 | 4109.0000 | 373.5455 | 8.0516 | -0.0135 | -0.0458 | 0.0323 | -17.1120 | 11 | 4 | -61.4984 | 232.0069 | -1.7410 | -1.8146 | 0.7075 | 0 | 0 |
| fx_sniper_ergodic_cci_signals | half | 1 | 12280.0000 | 1116.3636 | 4.9912 | 0.0157 | -0.0164 | 0.0321 | -18.2689 | 11 | 4 | -108.9329 | 220.1677 | -1.3609 | -1.2237 | 0.1425 | 0 | 0 |
| volatility_quality_signals | half | 1 | 8420.0000 | 765.4545 | 6.4452 | 0.0077 | -0.0239 | 0.0316 | -18.3044 | 11 | 3 | -73.1074 | 208.4422 | -1.8290 | -1.5348 | 0.3800 | 0 | 0 |
| fisher_transform_signals | double | 1 | 16894.0000 | 1535.8182 | 4.0761 | 0.0202 | -0.0120 | 0.0322 | -18.3836 | 11 | 4 | -87.2065 | 272.3379 | -1.2040 | -1.1839 | 0.0425 | 0 | 0 |
| hieken_ashi_smoothed_signals | default | 1 | 4096.0000 | 372.3636 | 7.9827 | -0.0176 | -0.0500 | 0.0323 | -18.6019 | 11 | 4 | -46.6116 | 234.6693 | -2.4509 | -1.9731 | 0.7425 | 0 | 0 |
| fx_sniper_ergodic_cci_signals | double | 1 | 8107.0000 | 737.0000 | 6.2450 | 0.0065 | -0.0259 | 0.0325 | -19.0912 | 11 | 3 | -74.1350 | 300.6202 | -1.5203 | -1.5262 | 0.3400 | 0 | 0 |
| adx_dmi_signals | half | 1 | 6609.0000 | 600.8182 | 6.5651 | -0.0000 | -0.0318 | 0.0318 | -19.0995 | 11 | 4 | -82.3878 | 240.4955 | -1.6541 | -1.8533 | 0.4575 | 0 | 0 |
| ssl_channel_signals | half | 1 | 8116.0000 | 737.8182 | 6.8578 | 0.0050 | -0.0267 | 0.0317 | -19.7105 | 11 | 5 | -89.9215 | 281.3666 | -1.5372 | -1.5968 | 0.3900 | 0 | 0 |
| didi_index_signals | double | 1 | 4971.0000 | 451.9091 | 6.5429 | -0.0113 | -0.0436 | 0.0324 | -19.7206 | 11 | 3 | -78.4112 | 264.4277 | -2.4091 | -2.2475 | 0.6825 | 0 | 0 |
| fisher_transform_signals | default | 1 | 17831.0000 | 1621.0000 | 3.8809 | 0.0194 | -0.0127 | 0.0321 | -20.6003 | 11 | 4 | -118.7372 | 292.9005 | -1.0774 | -1.2467 | 0.0525 | 0 | 0 |
| fx_sniper_ergodic_cci_signals | default | 1 | 9785.0000 | 889.5455 | 5.6544 | 0.0083 | -0.0239 | 0.0321 | -21.2213 | 11 | 4 | -105.1765 | 300.2529 | -1.4799 | -1.5593 | 0.3075 | 0 | 0 |
| bears_bulls_impulse_signals | default | 1 | 6575.0000 | 597.7273 | 8.4780 | -0.0068 | -0.0390 | 0.0322 | -23.3155 | 11 | 4 | -116.7485 | 291.3522 | -1.9073 | -1.8603 | 0.6025 | 0 | 0 |
| qqe_mod_signals | half | 1 | 6285.0000 | 571.3636 | 6.9954 | -0.0091 | -0.0412 | 0.0322 | -23.5647 | 11 | 2 | -90.7668 | 300.1226 | -2.6820 | -2.1210 | 0.6450 | 0 | 0 |
| vortex_signals | half | 1 | 9847.0000 | 895.1818 | 5.7649 | 0.0041 | -0.0279 | 0.0320 | -24.9854 | 11 | 3 | -104.6596 | 346.1451 | -1.9085 | -1.8181 | 0.3975 | 0 | 0 |
| linreg_slope_signals | half | 1 | 8325.0000 | 756.8182 | 7.0249 | -0.0030 | -0.0350 | 0.0321 | -26.5250 | 11 | 2 | -115.9473 | 368.4931 | -2.2089 | -1.9190 | 0.5300 | 0 | 0 |
| coral_signals | double | 1 | 6675.0000 | 606.8182 | 6.2911 | -0.0119 | -0.0440 | 0.0321 | -26.6936 | 11 | 2 | -84.1296 | 356.4271 | -2.2636 | -2.3626 | 0.7025 | 0 | 0 |
| bears_bulls_impulse_signals | half | 1 | 6502.0000 | 591.0909 | 8.1956 | -0.0134 | -0.0455 | 0.0321 | -26.9233 | 11 | 2 | -95.6785 | 335.1969 | -2.5911 | -2.0080 | 0.7175 | 0 | 0 |
| rex_oscillator_signals | half | 1 | 13924.0000 | 1265.8182 | 4.2362 | 0.0108 | -0.0213 | 0.0321 | -26.9563 | 11 | 4 | -89.3906 | 386.3203 | -1.7848 | -1.9728 | 0.1925 | 0 | 0 |
| center_of_gravity_signals | double | 1 | 8650.0000 | 786.3636 | 5.7013 | -0.0079 | -0.0403 | 0.0324 | -31.6604 | 11 | 2 | -99.3455 | 403.9832 | -2.8448 | -2.6191 | 0.6775 | 0 | 0 |
| coral_signals | default | 1 | 13360.0000 | 1214.5455 | 4.2516 | 0.0051 | -0.0269 | 0.0321 | -32.7213 | 11 | 3 | -125.9033 | 383.2934 | -1.9841 | -2.0543 | 0.3825 | 0 | 0 |
| center_of_gravity_signals | default | 1 | 12981.0000 | 1180.0909 | 4.5454 | 0.0037 | -0.0285 | 0.0322 | -33.6391 | 11 | 3 | -94.4517 | 389.3885 | -2.0818 | -1.9927 | 0.4075 | 0 | 0 |
| relative_vigor_index_signals | default | 1 | 12725.0000 | 1156.8182 | 3.2347 | 0.0013 | -0.0308 | 0.0321 | -35.6386 | 11 | 2 | -111.0147 | 441.2280 | -2.3669 | -2.9812 | 0.4500 | 0 | 0 |
| fisher_transform_signals | half | 1 | 19851.0000 | 1804.6364 | 3.5056 | 0.0096 | -0.0225 | 0.0321 | -40.6025 | 11 | 2 | -141.0348 | 473.1351 | -2.3979 | -2.4040 | 0.1650 | 0 | 0 |
| relative_vigor_index_signals | double | 1 | 12545.0000 | 1140.4545 | 3.2033 | -0.0083 | -0.0406 | 0.0323 | -46.3035 | 11 | 1 | -94.2111 | 531.1214 | -4.0157 | -3.8947 | 0.7550 | 0 | 0 |
| relative_vigor_index_signals | half | 1 | 13656.0000 | 1241.4545 | 3.3706 | -0.0111 | -0.0433 | 0.0322 | -53.7344 | 11 | 2 | -115.8104 | 610.7503 | -3.6393 | -4.0818 | 0.8025 | 0 | 0 |
| rex_oscillator_signals | double | 1 | 16510.0000 | 1500.9091 | 2.9183 | -0.0050 | -0.0374 | 0.0324 | -56.1615 | 11 | 1 | -142.5533 | 627.1567 | -4.9319 | -4.1808 | 0.7000 | 0 | 0 |
| coral_signals | half | 1 | 25744.0000 | 2340.3636 | 2.6073 | 0.0078 | -0.0243 | 0.0321 | -56.8843 | 11 | 2 | -175.0350 | 672.3322 | -2.8040 | -3.1230 | 0.1900 | 0 | 0 |
| center_of_gravity_signals | half | 1 | 20412.0000 | 1855.6364 | 3.2256 | 0.0013 | -0.0309 | 0.0322 | -57.2925 | 11 | 1 | -147.3224 | 631.8475 | -3.1892 | -3.3072 | 0.4500 | 0 | 0 |


**0 of 117 candidate-settings clear the empirical best-of-39 floor; 0 clear the alone floor.** 5 of 117 have a positive net R per year.


### C1 — `jack`, stability across the three settings

`sign_agree = 1` means all three settings agree on the sign of net R per year. A candidate positive on one setting and negative on two is being fitted, not measured.

| indicator | settings | settings_positive | sign_agree | R_per_year_min | R_per_year_med | R_per_year_max | spread |
|---|---:|---:|---:|---:|---:|---:|---:|
| halftrend_signals | 3 | 0 | 1 | -4.0650 | -0.4972 | -0.2402 | 3.8248 |
| aroon_signals | 3 | 1 | 0 | -7.6409 | -1.0751 | 0.2555 | 7.8964 |
| ichimoku_signals | 3 | 1 | 0 | -1.7119 | -1.1437 | 2.2066 | 3.9186 |
| waddah_attar_explosion_signals | 3 | 1 | 0 | -2.4140 | -1.3165 | 0.0343 | 2.4483 |
| donchian_breakout_signals | 3 | 0 | 1 | -5.0103 | -2.8974 | -2.4347 | 2.5756 |
| price_momentum_oscillator_signals | 3 | 0 | 1 | -9.0044 | -4.2413 | -3.7805 | 5.2239 |
| chandelier_exit_signals | 3 | 0 | 1 | -8.3521 | -4.7416 | -4.3500 | 4.0021 |
| supertrend_signals | 3 | 0 | 1 | -6.1391 | -4.8928 | -4.2350 | 1.9042 |
| laguerre_filter_signals | 3 | 0 | 1 | -8.0703 | -4.9880 | -4.1700 | 3.9003 |
| dspo_signals | 3 | 0 | 1 | -7.4611 | -5.3282 | -2.8464 | 4.6147 |
| schaff_trend_cycle_signals | 3 | 1 | 0 | -7.6416 | -5.4412 | 0.6258 | 8.2675 |
| mama_fama_signals | 3 | 0 | 1 | -8.8358 | -5.6416 | -2.1019 | 6.7339 |
| ehlers_reverse_ema_signals | 3 | 0 | 1 | -7.9969 | -5.7858 | -5.2315 | 2.7653 |
| lemantrend_signals | 3 | 0 | 1 | -6.3280 | -5.7957 | -3.4993 | 2.8287 |
| volatility_quality_signals | 3 | 0 | 1 | -18.3044 | -6.1738 | -3.8623 | 14.4421 |
| adx_dmi_signals | 3 | 1 | 0 | -19.0995 | -6.6739 | 0.1330 | 19.2326 |
| glitch_index_signals | 3 | 0 | 1 | -14.0129 | -7.2449 | -4.5947 | 9.4182 |
| polychromatic_momentum_signals | 3 | 0 | 1 | -13.0750 | -7.4836 | -4.3590 | 8.7160 |
| j_tpo_signals | 3 | 0 | 1 | -10.7202 | -7.9716 | -4.1634 | 6.5568 |
| kalman_filter_signals | 3 | 0 | 1 | -10.4371 | -8.1085 | -5.3978 | 5.0393 |
| dpo_signals | 3 | 0 | 1 | -9.3885 | -8.9190 | -4.8111 | 4.5774 |
| trend_direction_force_index_signals | 3 | 0 | 1 | -11.7128 | -10.1777 | -1.0620 | 10.6508 |
| kuskus_starlight_signals | 3 | 0 | 1 | -11.4197 | -10.3965 | -4.4268 | 6.9929 |
| linreg_slope_signals | 3 | 0 | 1 | -26.5250 | -10.4006 | -4.4871 | 22.0379 |
| kase_peak_oscillator_signals | 3 | 0 | 1 | -13.7709 | -11.0834 | -7.3377 | 6.4333 |
| qqe_mod_signals | 3 | 0 | 1 | -23.5647 | -11.4038 | -6.0469 | 17.5177 |
| coppock_curve_signals | 3 | 0 | 1 | -13.1101 | -11.6826 | -8.3513 | 4.7588 |
| vortex_signals | 3 | 0 | 1 | -24.9854 | -12.8676 | -11.6340 | 13.3514 |
| ssl_channel_signals | 3 | 0 | 1 | -19.7105 | -13.6115 | -8.9841 | 10.7264 |
| parabolic_sar_signals | 3 | 0 | 1 | -14.7595 | -14.4444 | -14.0611 | 0.6984 |
| hieken_ashi_smoothed_signals | 3 | 0 | 1 | -18.6019 | -14.8040 | -1.9403 | 16.6616 |
| didi_index_signals | 3 | 0 | 1 | -19.7206 | -17.1120 | -12.7173 | 7.0033 |
| fx_sniper_ergodic_cci_signals | 3 | 0 | 1 | -21.2213 | -19.0912 | -18.2689 | 2.9524 |
| fisher_transform_signals | 3 | 0 | 1 | -40.6025 | -20.6003 | -18.3836 | 22.2189 |
| bears_bulls_impulse_signals | 3 | 0 | 1 | -26.9233 | -23.3155 | -12.3714 | 14.5519 |
| rex_oscillator_signals | 3 | 0 | 1 | -56.1615 | -26.9563 | -14.2833 | 41.8782 |
| coral_signals | 3 | 0 | 1 | -56.8843 | -32.7213 | -26.6936 | 30.1906 |
| center_of_gravity_signals | 3 | 0 | 1 | -57.2925 | -33.6391 | -31.6604 | 25.6321 |
| relative_vigor_index_signals | 3 | 0 | 1 | -53.7344 | -46.3035 | -35.6386 | 18.0958 |


**34 of 39 candidates have all three settings agreeing in sign.**


## C1 — `textbook`, fixed settings, unseen trade years 2005-2015

Empirical yearly-t floors **from the random-entry null**: alone **0.610**, best-of-39 **2.252**. The analytic equivalents on 11 yearly observations are 1.812 and 3.973 — the empirical ones are lower because the analytic formula assumes a **zero-mean** null while the real null also pays costs, so it is centred below zero.

| indicator | setting | distinct_setting | n_entered | trades_per_year | mean_bars | R_gross_per_trade | R_net_per_trade | cost_per_trade | R_net_per_year | years | years_positive | worst_year | worst_dip_R | t_yearly | t_block_boot | null_p | clears_alone_emp | clears_family_emp |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ichimoku_signals | half | 1 | 1502.0000 | 136.5455 | 7.6119 | 0.0459 | 0.0136 | 0.0324 | 1.8559 | 11 | 7 | -21.5883 | 31.0607 | 0.4103 | 0.4376 | 0.2150 | 0 | 0 |
| kalman_filter_signals | half | 1 | 3294.0000 | 299.4545 | 7.7672 | 0.0352 | 0.0028 | 0.0324 | 0.8407 | 11 | 5 | -39.0661 | 84.4299 | 0.1632 | 0.1243 | 0.0925 | 0 | 0 |
| halftrend_signals | default | 1 | 322.0000 | 29.2727 | 7.0683 | 0.0489 | 0.0178 | 0.0311 | 0.5213 | 11 | 6 | -7.3293 | 17.7437 | 0.3735 | 0.3521 | 0.2925 | 0 | 0 |
| ichimoku_signals | double | 1 | 1931.0000 | 175.5455 | 7.5448 | 0.0343 | 0.0021 | 0.0322 | 0.3723 | 11 | 4 | -24.5203 | 63.5116 | 0.0604 | 0.0704 | 0.1875 | 0 | 0 |
| ichimoku_signals | default | 1 | 1353.0000 | 123.0000 | 7.6822 | 0.0319 | -0.0010 | 0.0330 | -0.1259 | 11 | 5 | -16.7360 | 48.9333 | -0.0397 | -0.0301 | 0.2650 | 0 | 0 |
| halftrend_signals | double | 1 | 172.0000 | 15.6364 | 6.7151 | 0.0002 | -0.0303 | 0.0305 | -0.4734 | 11 | 3 | -3.8875 | 16.4311 | -0.4826 | -0.4190 | 0.4825 | 0 | 0 |
| adx_dmi_signals | double | 1 | 75.0000 | 6.8182 | 7.0000 | -0.0875 | -0.1157 | 0.0282 | -0.7889 | 11 | 2 | -2.9182 | 9.6045 | -1.5257 | -1.2528 | 0.6450 | 0 | 0 |
| price_momentum_oscillator_signals | double | 1 | 1130.0000 | 102.7273 | 7.4947 | 0.0142 | -0.0186 | 0.0328 | -1.9088 | 11 | 4 | -18.5825 | 54.2833 | -0.4459 | -0.5465 | 0.3675 | 0 | 0 |
| waddah_attar_explosion_signals | half | 1 | 1624.0000 | 147.6364 | 6.3922 | 0.0195 | -0.0133 | 0.0328 | -1.9576 | 11 | 4 | -24.0314 | 67.3448 | -0.3022 | -0.4801 | 0.3225 | 0 | 0 |
| linreg_slope_signals | default | 1 | 4616.0000 | 419.6364 | 7.6155 | 0.0275 | -0.0047 | 0.0322 | -1.9629 | 11 | 6 | -42.4992 | 129.3430 | -0.2166 | -0.2334 | 0.1475 | 0 | 0 |
| waddah_attar_explosion_signals | double | 1 | 1620.0000 | 147.2727 | 6.2111 | 0.0182 | -0.0144 | 0.0327 | -2.1221 | 11 | 4 | -23.7420 | 68.2648 | -0.3725 | -0.5625 | 0.3500 | 0 | 0 |
| linreg_slope_signals | double | 1 | 2445.0000 | 222.2727 | 7.7072 | 0.0216 | -0.0106 | 0.0322 | -2.3524 | 11 | 5 | -36.9909 | 70.0189 | -0.3472 | -0.3997 | 0.3050 | 0 | 0 |
| dspo_signals | half | 1 | 4298.0000 | 390.7273 | 7.1931 | 0.0258 | -0.0064 | 0.0321 | -2.4872 | 11 | 6 | -52.2413 | 106.6135 | -0.3348 | -0.3428 | 0.1800 | 0 | 0 |
| donchian_breakout_signals | default | 1 | 1686.0000 | 153.2727 | 7.5451 | 0.0141 | -0.0174 | 0.0315 | -2.6654 | 11 | 3 | -12.0805 | 45.0073 | -0.9987 | -0.6069 | 0.3875 | 0 | 0 |
| lemantrend_signals | default | 1 | 1936.0000 | 176.0000 | 5.9256 | 0.0173 | -0.0152 | 0.0325 | -2.6781 | 11 | 4 | -23.4969 | 53.6156 | -0.6642 | -0.6735 | 0.3100 | 0 | 0 |
| laguerre_filter_signals | half | 1 | 4300.0000 | 390.9091 | 7.2098 | 0.0252 | -0.0070 | 0.0322 | -2.7199 | 11 | 7 | -40.6729 | 98.8450 | -0.4417 | -0.3607 | 0.1400 | 0 | 0 |
| laguerre_filter_signals | double | 1 | 965.0000 | 87.7273 | 7.0321 | 0.0003 | -0.0318 | 0.0321 | -2.7910 | 11 | 4 | -26.0125 | 78.1927 | -0.6809 | -0.8819 | 0.4725 | 0 | 0 |
| lemantrend_signals | double | 1 | 1420.0000 | 129.0909 | 6.2577 | 0.0106 | -0.0220 | 0.0326 | -2.8417 | 11 | 4 | -22.0007 | 48.5764 | -0.5757 | -0.8395 | 0.4375 | 0 | 0 |
| adx_dmi_signals | default | 1 | 986.0000 | 89.6364 | 6.4412 | -0.0018 | -0.0325 | 0.0307 | -2.9142 | 11 | 4 | -12.0311 | 42.1010 | -2.3827 | -1.1449 | 0.5275 | 0 | 0 |
| mama_fama_signals | double | 1 | 1456.0000 | 132.3636 | 7.7060 | 0.0096 | -0.0228 | 0.0324 | -3.0136 | 11 | 3 | -28.2247 | 55.1627 | -0.5197 | -0.6945 | 0.3600 | 0 | 0 |
| donchian_breakout_signals | double | 1 | 854.0000 | 77.6364 | 7.1604 | -0.0092 | -0.0413 | 0.0321 | -3.2041 | 11 | 3 | -21.8239 | 54.3178 | -0.6409 | -0.8478 | 0.6050 | 0 | 0 |
| aroon_signals | double | 1 | 1450.0000 | 131.8182 | 7.1152 | 0.0060 | -0.0264 | 0.0324 | -3.4783 | 11 | 4 | -21.3693 | 73.7085 | -0.7097 | -0.8514 | 0.4250 | 0 | 0 |
| mama_fama_signals | default | 1 | 3080.0000 | 280.0000 | 7.4383 | 0.0194 | -0.0130 | 0.0324 | -3.6283 | 11 | 5 | -23.8756 | 82.0807 | -1.0430 | -0.6002 | 0.2425 | 0 | 0 |
| j_tpo_signals | double | 1 | 915.0000 | 83.1818 | 7.2809 | -0.0113 | -0.0438 | 0.0325 | -3.6467 | 11 | 3 | -17.6094 | 55.8879 | -1.3335 | -1.2819 | 0.5700 | 0 | 0 |
| aroon_signals | default | 1 | 2833.0000 | 257.5455 | 7.4225 | 0.0179 | -0.0142 | 0.0322 | -3.6682 | 11 | 6 | -24.5383 | 61.0862 | -0.7869 | -0.6388 | 0.2400 | 0 | 0 |
| trend_direction_force_index_signals | double | 1 | 2449.0000 | 222.6364 | 7.2217 | 0.0156 | -0.0165 | 0.0321 | -3.6784 | 11 | 3 | -44.3950 | 76.9527 | -0.4803 | -0.5822 | 0.3275 | 0 | 0 |
| chandelier_exit_signals | default | 1 | 2359.0000 | 214.4545 | 7.5566 | 0.0134 | -0.0173 | 0.0307 | -3.7105 | 11 | 4 | -16.7819 | 55.2262 | -1.4027 | -0.7103 | 0.3800 | 0 | 0 |
| ehlers_reverse_ema_signals | default | 1 | 3820.0000 | 347.2727 | 7.3945 | 0.0216 | -0.0107 | 0.0323 | -3.7178 | 11 | 5 | -50.8423 | 105.2289 | -0.5862 | -0.5115 | 0.2400 | 0 | 0 |
| schaff_trend_cycle_signals | default | 1 | 2688.0000 | 244.3636 | 6.9044 | 0.0163 | -0.0156 | 0.0319 | -3.8093 | 11 | 4 | -24.7221 | 89.3530 | -0.7951 | -0.6479 | 0.3025 | 0 | 0 |
| didi_index_signals | default | 1 | 4109.0000 | 373.5455 | 7.1450 | 0.0208 | -0.0115 | 0.0323 | -4.2959 | 11 | 4 | -37.7145 | 96.6874 | -0.7422 | -0.5736 | 0.1925 | 0 | 0 |
| volatility_quality_signals | default | 1 | 3390.0000 | 308.1818 | 7.5690 | 0.0171 | -0.0147 | 0.0318 | -4.5207 | 11 | 6 | -34.6961 | 97.3035 | -0.9346 | -0.7272 | 0.3075 | 0 | 0 |
| schaff_trend_cycle_signals | half | 1 | 2789.0000 | 253.5455 | 6.7483 | 0.0137 | -0.0181 | 0.0318 | -4.5864 | 11 | 4 | -29.8601 | 114.3091 | -0.9044 | -0.8021 | 0.3425 | 0 | 0 |
| hieken_ashi_smoothed_signals | double | 1 | 2746.0000 | 249.6364 | 7.3387 | 0.0123 | -0.0195 | 0.0318 | -4.8666 | 11 | 5 | -39.7308 | 93.2656 | -0.7090 | -0.7705 | 0.3100 | 0 | 0 |
| waddah_attar_explosion_signals | default | 1 | 1622.0000 | 147.4545 | 6.2583 | -0.0007 | -0.0334 | 0.0327 | -4.9210 | 11 | 3 | -25.0450 | 71.8521 | -0.8422 | -1.2935 | 0.4675 | 0 | 0 |
| didi_index_signals | half | 1 | 4969.0000 | 451.7273 | 6.8827 | 0.0210 | -0.0112 | 0.0322 | -5.0433 | 11 | 5 | -49.1504 | 109.8603 | -0.8231 | -0.6222 | 0.1950 | 0 | 0 |
| coppock_curve_signals | double | 1 | 2717.0000 | 247.0000 | 7.5572 | 0.0115 | -0.0207 | 0.0323 | -5.1158 | 11 | 4 | -30.2922 | 81.5402 | -0.7818 | -0.8472 | 0.3575 | 0 | 0 |
| halftrend_signals | half | 1 | 538.0000 | 48.9091 | 6.6877 | -0.0745 | -0.1059 | 0.0314 | -5.1779 | 11 | 2 | -11.5404 | 62.8499 | -2.7034 | -2.2956 | 0.8600 | 0 | 0 |
| chandelier_exit_signals | half | 1 | 2126.0000 | 193.2727 | 7.6646 | 0.0042 | -0.0275 | 0.0316 | -5.3066 | 11 | 3 | -18.4171 | 70.6403 | -1.9994 | -1.0851 | 0.4000 | 0 | 0 |
| dspo_signals | double | 1 | 1106.0000 | 100.5455 | 7.2550 | -0.0216 | -0.0545 | 0.0330 | -5.4832 | 11 | 2 | -25.3698 | 72.7024 | -1.3652 | -1.6324 | 0.6850 | 0 | 0 |
| ssl_channel_signals | double | 1 | 4045.0000 | 367.7273 | 7.6190 | 0.0168 | -0.0154 | 0.0321 | -5.6512 | 11 | 4 | -55.8453 | 126.6892 | -0.8822 | -0.7744 | 0.3125 | 0 | 0 |
| polychromatic_momentum_signals | default | 1 | 2883.0000 | 262.0909 | 7.3524 | 0.0100 | -0.0223 | 0.0324 | -5.8512 | 11 | 6 | -40.0902 | 95.4226 | -1.0494 | -0.9008 | 0.3575 | 0 | 0 |
| j_tpo_signals | half | 1 | 3723.0000 | 338.4545 | 7.2858 | 0.0147 | -0.0178 | 0.0325 | -6.0189 | 11 | 4 | -29.1490 | 90.5443 | -1.1332 | -0.8961 | 0.2975 | 0 | 0 |
| parabolic_sar_signals | default | 1 | 6644.0000 | 604.0000 | 6.8591 | 0.0221 | -0.0100 | 0.0321 | -6.0339 | 11 | 5 | -67.2165 | 164.5563 | -0.6240 | -0.6333 | 0.1575 | 0 | 0 |
| glitch_index_signals | half | 1 | 3681.0000 | 334.6364 | 7.5167 | 0.0141 | -0.0182 | 0.0323 | -6.0948 | 11 | 5 | -31.0088 | 91.7948 | -0.8632 | -0.7837 | 0.2950 | 0 | 0 |
| price_momentum_oscillator_signals | half | 1 | 2419.0000 | 219.9091 | 7.5300 | 0.0042 | -0.0283 | 0.0325 | -6.2185 | 11 | 6 | -24.8218 | 84.4713 | -1.7084 | -1.1549 | 0.4325 | 0 | 0 |
| qqe_mod_signals | default | 1 | 4586.0000 | 416.9091 | 6.9919 | 0.0170 | -0.0153 | 0.0323 | -6.3835 | 11 | 4 | -56.9240 | 142.6059 | -0.8541 | -0.8279 | 0.2575 | 0 | 0 |
| mama_fama_signals | half | 1 | 6745.0000 | 613.1818 | 6.2749 | 0.0217 | -0.0105 | 0.0322 | -6.4317 | 11 | 5 | -56.4105 | 104.2280 | -1.1400 | -0.7560 | 0.1250 | 0 | 0 |
| ehlers_reverse_ema_signals | double | 1 | 2832.0000 | 257.4545 | 7.4414 | 0.0069 | -0.0258 | 0.0328 | -6.6508 | 11 | 3 | -37.2156 | 101.4011 | -1.6539 | -1.1235 | 0.4175 | 0 | 0 |
| hieken_ashi_smoothed_signals | half | 1 | 5257.0000 | 477.9091 | 6.8792 | 0.0182 | -0.0141 | 0.0322 | -6.7173 | 11 | 6 | -54.4418 | 152.6722 | -0.8329 | -0.7661 | 0.2200 | 0 | 0 |
| aroon_signals | half | 1 | 5374.0000 | 488.5455 | 6.8225 | 0.0182 | -0.0138 | 0.0320 | -6.7348 | 11 | 4 | -75.1081 | 164.1949 | -0.7420 | -0.7949 | 0.2300 | 0 | 0 |
| ssl_channel_signals | default | 1 | 5794.0000 | 526.7273 | 7.2592 | 0.0190 | -0.0130 | 0.0320 | -6.8629 | 11 | 4 | -53.5515 | 167.0997 | -0.7835 | -0.7634 | 0.2025 | 0 | 0 |
| kase_peak_oscillator_signals | default | 1 | 3906.0000 | 355.0909 | 6.8769 | 0.0126 | -0.0194 | 0.0320 | -6.8920 | 11 | 6 | -59.3826 | 117.1251 | -1.0899 | -1.0240 | 0.3125 | 0 | 0 |
| supertrend_signals | half | 1 | 1851.0000 | 168.2727 | 7.5208 | -0.0092 | -0.0410 | 0.0318 | -6.8959 | 11 | 2 | -26.9317 | 83.5605 | -2.3590 | -1.5130 | 0.5525 | 0 | 0 |
| coppock_curve_signals | default | 1 | 3602.0000 | 327.4545 | 7.4836 | 0.0105 | -0.0217 | 0.0321 | -7.0977 | 11 | 4 | -37.0364 | 110.1703 | -0.9422 | -1.0269 | 0.3550 | 0 | 0 |
| kase_peak_oscillator_signals | double | 1 | 2840.0000 | 258.1818 | 6.8884 | 0.0044 | -0.0276 | 0.0321 | -7.1343 | 11 | 4 | -42.5808 | 104.7781 | -1.2853 | -1.2838 | 0.4650 | 0 | 0 |
| qqe_mod_signals | double | 1 | 3285.0000 | 298.6364 | 7.2122 | 0.0086 | -0.0239 | 0.0325 | -7.1392 | 11 | 2 | -33.2925 | 120.6530 | -1.6792 | -1.1013 | 0.3800 | 0 | 0 |
| laguerre_filter_signals | default | 1 | 2075.0000 | 188.6364 | 7.1383 | -0.0061 | -0.0383 | 0.0322 | -7.2171 | 11 | 4 | -43.1815 | 83.3224 | -1.1172 | -1.4584 | 0.5775 | 0 | 0 |
| ehlers_reverse_ema_signals | half | 1 | 4967.0000 | 451.5455 | 7.1494 | 0.0160 | -0.0162 | 0.0322 | -7.2976 | 11 | 5 | -80.6550 | 153.5127 | -0.8363 | -0.8447 | 0.2450 | 0 | 0 |
| donchian_breakout_signals | half | 1 | 2924.0000 | 265.8182 | 7.7719 | 0.0033 | -0.0285 | 0.0318 | -7.5675 | 11 | 3 | -29.8517 | 113.6983 | -2.1771 | -1.1861 | 0.4250 | 0 | 0 |
| price_momentum_oscillator_signals | default | 1 | 1732.0000 | 157.4545 | 7.3874 | -0.0165 | -0.0488 | 0.0323 | -7.6911 | 11 | 4 | -28.3841 | 92.5459 | -1.5808 | -1.7366 | 0.6425 | 0 | 0 |
| volatility_quality_signals | double | 1 | 1184.0000 | 107.6364 | 7.1655 | -0.0408 | -0.0718 | 0.0310 | -7.7268 | 11 | 1 | -13.5336 | 95.0312 | -3.6239 | -2.2802 | 0.8050 | 0 | 0 |
| dpo_signals | double | 1 | 2116.0000 | 192.3636 | 5.1040 | -0.0082 | -0.0407 | 0.0324 | -7.8213 | 11 | 4 | -27.1242 | 95.8751 | -1.9782 | -1.9812 | 0.6375 | 0 | 0 |
| supertrend_signals | default | 1 | 1811.0000 | 164.6364 | 7.3446 | -0.0168 | -0.0484 | 0.0316 | -7.9718 | 11 | 3 | -24.1717 | 97.4927 | -2.5432 | -1.7208 | 0.6900 | 0 | 0 |
| kalman_filter_signals | double | 1 | 1647.0000 | 149.7273 | 7.3103 | -0.0232 | -0.0554 | 0.0322 | -8.2902 | 11 | 3 | -34.7961 | 102.5924 | -1.3548 | -1.9652 | 0.7200 | 0 | 0 |
| trend_direction_force_index_signals | default | 1 | 3789.0000 | 344.4545 | 7.3626 | 0.0080 | -0.0243 | 0.0323 | -8.3619 | 11 | 3 | -47.7743 | 110.9901 | -0.9312 | -1.0709 | 0.4650 | 0 | 0 |
| dspo_signals | default | 1 | 2290.0000 | 208.1818 | 7.3812 | -0.0075 | -0.0403 | 0.0327 | -8.3809 | 11 | 3 | -32.5771 | 107.3486 | -1.8538 | -1.7774 | 0.5425 | 0 | 0 |
| parabolic_sar_signals | double | 1 | 4314.0000 | 392.1818 | 7.3185 | 0.0104 | -0.0218 | 0.0322 | -8.5482 | 11 | 6 | -55.8980 | 141.9314 | -1.3911 | -1.1797 | 0.3300 | 0 | 0 |
| lemantrend_signals | half | 1 | 2613.0000 | 237.5455 | 5.4018 | -0.0032 | -0.0360 | 0.0329 | -8.5560 | 11 | 3 | -29.3089 | 97.7605 | -2.2513 | -1.8942 | 0.5325 | 0 | 0 |
| kuskus_starlight_signals | half | 1 | 5969.0000 | 542.6364 | 6.5939 | 0.0161 | -0.0160 | 0.0320 | -8.6740 | 11 | 5 | -49.1599 | 152.9163 | -1.4623 | -0.9955 | 0.2250 | 0 | 0 |
| supertrend_signals | double | 1 | 1796.0000 | 163.2727 | 7.4349 | -0.0216 | -0.0532 | 0.0315 | -8.6812 | 11 | 1 | -24.3710 | 104.4229 | -2.7942 | -1.9963 | 0.7225 | 0 | 0 |
| j_tpo_signals | default | 1 | 1928.0000 | 175.2727 | 7.3854 | -0.0183 | -0.0505 | 0.0322 | -8.8497 | 11 | 4 | -58.5990 | 108.5185 | -1.3292 | -1.8292 | 0.6475 | 0 | 0 |
| kalman_filter_signals | default | 1 | 2318.0000 | 210.7273 | 7.4659 | -0.0096 | -0.0420 | 0.0324 | -8.8529 | 11 | 4 | -31.9800 | 107.0657 | -1.6067 | -1.7172 | 0.5775 | 0 | 0 |
| hieken_ashi_smoothed_signals | default | 1 | 4096.0000 | 372.3636 | 7.2139 | 0.0078 | -0.0245 | 0.0323 | -9.1414 | 11 | 5 | -43.2800 | 137.0132 | -1.2094 | -1.0931 | 0.4175 | 0 | 0 |
| glitch_index_signals | default | 1 | 3064.0000 | 278.5455 | 7.4723 | -0.0007 | -0.0330 | 0.0322 | -9.1839 | 11 | 2 | -38.3546 | 109.3220 | -1.1159 | -1.4167 | 0.5350 | 0 | 0 |
| bears_bulls_impulse_signals | double | 1 | 5644.0000 | 513.0909 | 7.5895 | 0.0141 | -0.0181 | 0.0323 | -9.3066 | 11 | 5 | -70.2804 | 157.1230 | -0.9713 | -1.0847 | 0.2700 | 0 | 0 |
| trend_direction_force_index_signals | half | 1 | 5827.0000 | 529.7273 | 7.4742 | 0.0145 | -0.0176 | 0.0321 | -9.3326 | 11 | 4 | -43.9134 | 163.9758 | -1.0434 | -0.9913 | 0.2800 | 0 | 0 |
| glitch_index_signals | double | 1 | 2274.0000 | 206.7273 | 7.4582 | -0.0133 | -0.0458 | 0.0325 | -9.4778 | 11 | 4 | -43.8941 | 116.2265 | -1.3442 | -1.8009 | 0.6075 | 0 | 0 |
| kuskus_starlight_signals | default | 1 | 4115.0000 | 374.0909 | 6.7055 | 0.0067 | -0.0255 | 0.0322 | -9.5329 | 11 | 3 | -26.8720 | 135.0148 | -2.5207 | -1.4612 | 0.3575 | 0 | 0 |
| chandelier_exit_signals | double | 1 | 3311.0000 | 301.0000 | 6.3159 | -0.0029 | -0.0330 | 0.0301 | -9.9314 | 11 | 3 | -33.9766 | 118.5829 | -1.8830 | -1.8037 | 0.5400 | 0 | 0 |
| schaff_trend_cycle_signals | double | 1 | 2488.0000 | 226.1818 | 7.0257 | -0.0123 | -0.0441 | 0.0318 | -9.9734 | 11 | 2 | -29.3014 | 146.9375 | -2.1774 | -1.7868 | 0.6325 | 0 | 0 |
| polychromatic_momentum_signals | half | 1 | 5674.0000 | 515.8182 | 6.6505 | 0.0123 | -0.0201 | 0.0324 | -10.3904 | 11 | 5 | -82.7884 | 165.0664 | -1.1359 | -1.2011 | 0.3125 | 0 | 0 |
| coppock_curve_signals | half | 1 | 4491.0000 | 408.2727 | 6.9864 | 0.0048 | -0.0274 | 0.0322 | -11.1709 | 11 | 2 | -59.8918 | 145.2108 | -1.5494 | -1.4461 | 0.4175 | 0 | 0 |
| dpo_signals | default | 1 | 3447.0000 | 313.3636 | 5.1686 | -0.0036 | -0.0366 | 0.0329 | -11.4544 | 11 | 3 | -37.7651 | 149.3773 | -1.8892 | -2.2016 | 0.6025 | 0 | 0 |
| vortex_signals | default | 1 | 6868.0000 | 624.3636 | 5.4536 | 0.0131 | -0.0189 | 0.0320 | -11.8112 | 11 | 3 | -58.9646 | 146.4472 | -1.2540 | -1.3696 | 0.1975 | 0 | 0 |
| polychromatic_momentum_signals | double | 1 | 1449.0000 | 131.7273 | 7.1953 | -0.0615 | -0.0939 | 0.0324 | -12.3699 | 11 | 1 | -37.1766 | 148.5761 | -2.1360 | -2.9636 | 0.8950 | 0 | 0 |
| vortex_signals | double | 1 | 4882.0000 | 443.8182 | 5.3705 | 0.0045 | -0.0282 | 0.0327 | -12.5151 | 11 | 3 | -50.1577 | 148.7629 | -1.6604 | -1.8452 | 0.4325 | 0 | 0 |
| kuskus_starlight_signals | double | 1 | 2825.0000 | 256.8182 | 6.6450 | -0.0173 | -0.0495 | 0.0322 | -12.7039 | 11 | 4 | -48.7957 | 146.5125 | -1.8964 | -2.4648 | 0.7075 | 0 | 0 |
| dpo_signals | half | 1 | 4988.0000 | 453.4545 | 5.3204 | 0.0040 | -0.0285 | 0.0325 | -12.9248 | 11 | 2 | -33.0998 | 155.3682 | -3.7059 | -2.2367 | 0.3975 | 0 | 0 |
| parabolic_sar_signals | half | 1 | 9606.0000 | 873.2727 | 5.7619 | 0.0159 | -0.0161 | 0.0320 | -14.0461 | 11 | 4 | -76.1213 | 209.1228 | -1.3946 | -1.3057 | 0.1925 | 0 | 0 |
| kase_peak_oscillator_signals | half | 1 | 5519.0000 | 501.7273 | 6.6197 | 0.0030 | -0.0288 | 0.0319 | -14.4621 | 11 | 5 | -61.0430 | 187.7560 | -2.0772 | -1.7390 | 0.4825 | 0 | 0 |
| volatility_quality_signals | half | 1 | 8421.0000 | 765.5455 | 5.9835 | 0.0117 | -0.0199 | 0.0316 | -15.2459 | 11 | 3 | -57.7927 | 210.8244 | -2.2384 | -1.6160 | 0.2650 | 0 | 0 |
| fx_sniper_ergodic_cci_signals | double | 1 | 8107.0000 | 737.0000 | 5.6503 | 0.0109 | -0.0215 | 0.0325 | -15.8797 | 11 | 4 | -57.5779 | 238.7730 | -1.6448 | -1.6849 | 0.2975 | 0 | 0 |
| adx_dmi_signals | half | 1 | 6605.0000 | 600.4545 | 5.5947 | 0.0033 | -0.0284 | 0.0317 | -17.0527 | 11 | 4 | -68.8387 | 229.8898 | -1.9475 | -2.2051 | 0.4575 | 0 | 0 |
| rex_oscillator_signals | default | 1 | 12531.0000 | 1139.1818 | 3.8810 | 0.0171 | -0.0150 | 0.0322 | -17.1353 | 11 | 2 | -57.8158 | 282.6702 | -1.5653 | -1.4540 | 0.0875 | 0 | 0 |
| qqe_mod_signals | half | 1 | 6285.0000 | 571.3636 | 6.3220 | -0.0016 | -0.0338 | 0.0322 | -19.2963 | 11 | 2 | -76.6580 | 234.4487 | -2.8403 | -2.0973 | 0.5275 | 0 | 0 |
| ssl_channel_signals | half | 1 | 8116.0000 | 737.8182 | 6.2175 | 0.0045 | -0.0272 | 0.0317 | -20.0679 | 11 | 2 | -71.1058 | 280.1186 | -2.5646 | -2.0103 | 0.4150 | 0 | 0 |
| vortex_signals | half | 1 | 9846.0000 | 895.0909 | 5.1652 | 0.0083 | -0.0237 | 0.0320 | -21.2045 | 11 | 4 | -77.2806 | 282.1479 | -2.1519 | -1.9609 | 0.2975 | 0 | 0 |
| fx_sniper_ergodic_cci_signals | default | 1 | 9785.0000 | 889.5455 | 5.2598 | 0.0077 | -0.0244 | 0.0321 | -21.7414 | 11 | 4 | -78.6283 | 269.7509 | -2.0746 | -2.0323 | 0.3400 | 0 | 0 |
| didi_index_signals | double | 1 | 4971.0000 | 451.9091 | 5.9980 | -0.0168 | -0.0492 | 0.0324 | -22.2455 | 11 | 2 | -71.2524 | 276.1430 | -2.9781 | -2.8741 | 0.7925 | 0 | 0 |
| linreg_slope_signals | half | 1 | 8547.0000 | 777.0000 | 6.3397 | 0.0028 | -0.0292 | 0.0320 | -22.7148 | 11 | 2 | -67.7638 | 301.3562 | -2.8292 | -1.9993 | 0.4675 | 0 | 0 |
| coral_signals | double | 1 | 6675.0000 | 606.8182 | 6.0722 | -0.0075 | -0.0396 | 0.0321 | -24.0502 | 11 | 4 | -76.2436 | 325.0760 | -2.2679 | -2.4552 | 0.6950 | 0 | 0 |
| bears_bulls_impulse_signals | default | 1 | 6995.0000 | 635.9091 | 7.3229 | -0.0064 | -0.0385 | 0.0321 | -24.4923 | 11 | 3 | -96.3417 | 299.9561 | -2.2222 | -2.2535 | 0.6150 | 0 | 0 |
| bears_bulls_impulse_signals | half | 1 | 6948.0000 | 631.6364 | 7.2683 | -0.0101 | -0.0421 | 0.0319 | -26.5662 | 11 | 0 | -80.7031 | 323.8257 | -3.6308 | -2.3526 | 0.6900 | 0 | 0 |
| fx_sniper_ergodic_cci_signals | half | 1 | 12280.0000 | 1116.3636 | 4.6876 | 0.0079 | -0.0242 | 0.0321 | -27.0556 | 11 | 3 | -82.9306 | 311.5971 | -2.6926 | -2.3277 | 0.2700 | 0 | 0 |
| center_of_gravity_signals | default | 1 | 12981.0000 | 1180.0909 | 4.4282 | 0.0076 | -0.0246 | 0.0322 | -29.0789 | 11 | 2 | -67.5626 | 350.6136 | -2.5441 | -1.9933 | 0.3025 | 0 | 0 |
| fisher_transform_signals | double | 1 | 16894.0000 | 1535.8182 | 3.7622 | 0.0128 | -0.0193 | 0.0322 | -29.6433 | 11 | 2 | -99.1466 | 363.4551 | -2.6255 | -2.4597 | 0.1100 | 0 | 0 |
| center_of_gravity_signals | double | 1 | 8650.0000 | 786.3636 | 5.2687 | -0.0056 | -0.0380 | 0.0324 | -29.8632 | 11 | 0 | -76.1764 | 346.5966 | -3.5734 | -3.0196 | 0.6600 | 0 | 0 |
| rex_oscillator_signals | half | 1 | 13924.0000 | 1265.8182 | 3.9607 | 0.0079 | -0.0242 | 0.0321 | -30.6184 | 11 | 2 | -67.5818 | 367.6106 | -4.1975 | -2.7620 | 0.2650 | 0 | 0 |
| fisher_transform_signals | default | 1 | 17831.0000 | 1621.0000 | 3.5972 | 0.0108 | -0.0213 | 0.0321 | -34.5346 | 11 | 2 | -121.2880 | 404.6081 | -2.7501 | -2.6816 | 0.1850 | 0 | 0 |
| relative_vigor_index_signals | default | 1 | 12725.0000 | 1156.8182 | 3.5225 | -0.0009 | -0.0330 | 0.0321 | -38.1864 | 11 | 2 | -141.8613 | 459.8382 | -2.3865 | -3.1314 | 0.5025 | 0 | 0 |
| coral_signals | default | 1 | 13360.0000 | 1214.5455 | 4.2950 | -0.0031 | -0.0352 | 0.0321 | -42.6997 | 11 | 3 | -102.7946 | 470.1486 | -3.5076 | -3.0624 | 0.5750 | 0 | 0 |
| relative_vigor_index_signals | double | 1 | 12545.0000 | 1140.4545 | 3.4434 | -0.0083 | -0.0406 | 0.0323 | -46.3095 | 11 | 1 | -100.3255 | 535.2393 | -4.0650 | -4.0845 | 0.7475 | 0 | 0 |
| relative_vigor_index_signals | half | 1 | 13656.0000 | 1241.4545 | 3.6585 | -0.0054 | -0.0376 | 0.0322 | -46.6443 | 11 | 2 | -114.7540 | 543.7373 | -3.1182 | -3.5573 | 0.6625 | 0 | 0 |
| fisher_transform_signals | half | 1 | 19851.0000 | 1804.6364 | 3.3700 | 0.0059 | -0.0263 | 0.0321 | -47.4096 | 11 | 0 | -142.9805 | 537.0847 | -3.4333 | -3.4702 | 0.2750 | 0 | 0 |
| coral_signals | half | 1 | 25744.0000 | 2340.3636 | 2.6701 | 0.0078 | -0.0243 | 0.0321 | -56.8677 | 11 | 2 | -179.9246 | 666.6069 | -2.5215 | -3.4547 | 0.1750 | 0 | 0 |
| rex_oscillator_signals | double | 1 | 16510.0000 | 1500.9091 | 3.0096 | -0.0084 | -0.0408 | 0.0324 | -61.1919 | 11 | 0 | -119.0788 | 679.2290 | -6.2568 | -5.1196 | 0.7850 | 0 | 0 |
| center_of_gravity_signals | half | 1 | 20412.0000 | 1855.6364 | 3.2616 | -0.0015 | -0.0337 | 0.0322 | -62.6012 | 11 | 1 | -161.4504 | 691.0575 | -3.9217 | -4.1174 | 0.5775 | 0 | 0 |


**0 of 117 candidate-settings clear the empirical best-of-39 floor; 0 clear the alone floor.** 4 of 117 have a positive net R per year.


### C1 — `textbook`, stability across the three settings

`sign_agree = 1` means all three settings agree on the sign of net R per year. A candidate positive on one setting and negative on two is being fitted, not measured.

| indicator | settings | settings_positive | sign_agree | R_per_year_min | R_per_year_med | R_per_year_max | spread |
|---|---:|---:|---:|---:|---:|---:|---:|
| ichimoku_signals | 3 | 2 | 0 | -0.1259 | 0.3723 | 1.8559 | 1.9818 |
| halftrend_signals | 3 | 1 | 0 | -5.1779 | -0.4734 | 0.5213 | 5.6992 |
| waddah_attar_explosion_signals | 3 | 0 | 1 | -4.9210 | -2.1221 | -1.9576 | 2.9635 |
| linreg_slope_signals | 3 | 0 | 1 | -22.7148 | -2.3524 | -1.9629 | 20.7519 |
| laguerre_filter_signals | 3 | 0 | 1 | -7.2171 | -2.7910 | -2.7199 | 4.4973 |
| lemantrend_signals | 3 | 0 | 1 | -8.5560 | -2.8417 | -2.6781 | 5.8779 |
| adx_dmi_signals | 3 | 0 | 1 | -17.0527 | -2.9142 | -0.7889 | 16.2639 |
| donchian_breakout_signals | 3 | 0 | 1 | -7.5675 | -3.2041 | -2.6654 | 4.9020 |
| mama_fama_signals | 3 | 0 | 1 | -6.4317 | -3.6283 | -3.0136 | 3.4181 |
| aroon_signals | 3 | 0 | 1 | -6.7348 | -3.6682 | -3.4783 | 3.2565 |
| schaff_trend_cycle_signals | 3 | 0 | 1 | -9.9734 | -4.5864 | -3.8093 | 6.1641 |
| didi_index_signals | 3 | 0 | 1 | -22.2455 | -5.0433 | -4.2959 | 17.9497 |
| chandelier_exit_signals | 3 | 0 | 1 | -9.9314 | -5.3066 | -3.7105 | 6.2209 |
| dspo_signals | 3 | 0 | 1 | -8.3809 | -5.4832 | -2.4872 | 5.8936 |
| j_tpo_signals | 3 | 0 | 1 | -8.8497 | -6.0189 | -3.6467 | 5.2031 |
| price_momentum_oscillator_signals | 3 | 0 | 1 | -7.6911 | -6.2185 | -1.9088 | 5.7822 |
| ehlers_reverse_ema_signals | 3 | 0 | 1 | -7.2976 | -6.6508 | -3.7178 | 3.5798 |
| hieken_ashi_smoothed_signals | 3 | 0 | 1 | -9.1414 | -6.7173 | -4.8666 | 4.2748 |
| ssl_channel_signals | 3 | 0 | 1 | -20.0679 | -6.8629 | -5.6512 | 14.4167 |
| coppock_curve_signals | 3 | 0 | 1 | -11.1709 | -7.0977 | -5.1158 | 6.0551 |
| kase_peak_oscillator_signals | 3 | 0 | 1 | -14.4621 | -7.1343 | -6.8920 | 7.5702 |
| qqe_mod_signals | 3 | 0 | 1 | -19.2963 | -7.1392 | -6.3835 | 12.9128 |
| volatility_quality_signals | 3 | 0 | 1 | -15.2459 | -7.7268 | -4.5207 | 10.7252 |
| supertrend_signals | 3 | 0 | 1 | -8.6812 | -7.9718 | -6.8959 | 1.7853 |
| kalman_filter_signals | 3 | 1 | 0 | -8.8529 | -8.2902 | 0.8407 | 9.6936 |
| trend_direction_force_index_signals | 3 | 0 | 1 | -9.3326 | -8.3619 | -3.6784 | 5.6542 |
| parabolic_sar_signals | 3 | 0 | 1 | -14.0461 | -8.5482 | -6.0339 | 8.0122 |
| glitch_index_signals | 3 | 0 | 1 | -9.4778 | -9.1839 | -6.0948 | 3.3830 |
| kuskus_starlight_signals | 3 | 0 | 1 | -12.7039 | -9.5329 | -8.6740 | 4.0299 |
| polychromatic_momentum_signals | 3 | 0 | 1 | -12.3699 | -10.3904 | -5.8512 | 6.5187 |
| dpo_signals | 3 | 0 | 1 | -12.9248 | -11.4544 | -7.8213 | 5.1035 |
| vortex_signals | 3 | 0 | 1 | -21.2045 | -12.5151 | -11.8112 | 9.3933 |
| fx_sniper_ergodic_cci_signals | 3 | 0 | 1 | -27.0556 | -21.7414 | -15.8797 | 11.1759 |
| bears_bulls_impulse_signals | 3 | 0 | 1 | -26.5662 | -24.4923 | -9.3066 | 17.2596 |
| center_of_gravity_signals | 3 | 0 | 1 | -62.6012 | -29.8632 | -29.0789 | 33.5223 |
| rex_oscillator_signals | 3 | 0 | 1 | -61.1919 | -30.6184 | -17.1353 | 44.0567 |
| fisher_transform_signals | 3 | 0 | 1 | -47.4096 | -34.5346 | -29.6433 | 17.7663 |
| coral_signals | 3 | 0 | 1 | -56.8677 | -42.6997 | -24.0502 | 32.8175 |
| relative_vigor_index_signals | 3 | 0 | 1 | -46.6443 | -46.3095 | -38.1864 | 8.4579 |


**36 of 39 candidates have all three settings agreeing in sign.**


---

# BASELINE — all 15 candidates


## BASELINE — `flip_only`, fixed settings, unseen trade years 2005-2015

Empirical yearly-t floors **from the random-entry null**: alone **-0.023**, best-of-15 **1.174**. The analytic equivalents on 11 yearly observations are 1.812 and 3.395 — the empirical ones are lower because the analytic formula assumes a **zero-mean** null while the real null also pays costs, so it is centred below zero.

| indicator | setting | distinct_setting | n_entered | trades_per_year | mean_bars | R_gross_per_trade | R_net_per_trade | cost_per_trade | R_net_per_year | years | years_positive | worst_year | worst_dip_R | t_yearly | t_block_boot | null_p | clears_alone_emp | clears_family_emp |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| hma_baseline | double | 1 | 10521.0000 | 956.4545 | 6.7635 | 0.0285 | -0.0036 | 0.0321 | -3.4154 | 11 | 4 | -57.1127 | 214.1554 | -0.2286 | -0.1722 | 0.0575 | 0 | 0 |
| rma_baseline | double | 1 | 4962.0000 | 451.0909 | 14.2920 | 0.0137 | -0.0184 | 0.0321 | -8.2842 | 11 | 3 | -127.5290 | 333.2502 | -0.2521 | -0.3145 | 0.3325 | 0 | 0 |
| lsma_baseline | double | 1 | 9362.0000 | 851.0909 | 7.6053 | 0.0205 | -0.0115 | 0.0320 | -9.7766 | 11 | 4 | -97.5100 | 307.3779 | -0.5491 | -0.4560 | 0.2025 | 0 | 0 |
| mcginley_dynamic_index | double | 1 | 5848.0000 | 531.6364 | 12.1539 | 0.0132 | -0.0190 | 0.0322 | -10.1199 | 11 | 3 | -144.5489 | 311.1924 | -0.3337 | -0.3988 | 0.3600 | 0 | 0 |
| ema_baseline | double | 1 | 6831.0000 | 621.0000 | 10.3590 | 0.0126 | -0.0197 | 0.0323 | -12.2246 | 11 | 4 | -126.9216 | 322.8417 | -0.3930 | -0.4805 | 0.3075 | 0 | 0 |
| rma_baseline | default | 1 | 6987.0000 | 635.1818 | 10.1852 | 0.0115 | -0.0207 | 0.0322 | -13.1551 | 11 | 4 | -125.8299 | 332.3603 | -0.4242 | -0.5217 | 0.3625 | 0 | 0 |
| sma_baseline | double | 1 | 5951.0000 | 541.0000 | 11.8904 | 0.0072 | -0.0254 | 0.0326 | -13.7363 | 11 | 3 | -156.4760 | 351.8476 | -0.4258 | -0.5447 | 0.3950 | 0 | 0 |
| hma_baseline | default | 1 | 15729.0000 | 1429.9091 | 4.5644 | 0.0207 | -0.0114 | 0.0320 | -16.2659 | 11 | 3 | -70.5712 | 267.1546 | -1.3323 | -0.8082 | 0.0900 | 0 | 0 |
| lsma_baseline | default | 1 | 13936.0000 | 1266.9091 | 5.1485 | 0.0181 | -0.0139 | 0.0320 | -17.6529 | 11 | 3 | -77.1265 | 338.8744 | -1.1200 | -0.9023 | 0.1100 | 0 | 0 |
| fantail_vma | half | 0 | 11023.0000 | 1002.0909 | 6.5242 | 0.0134 | -0.0185 | 0.0319 | -18.5324 | 11 | 4 | -78.8930 | 329.9891 | -1.3330 | -1.0195 | 0.2250 | 0 | 0 |
| fantail_vma | default | 1 | 11023.0000 | 1002.0909 | 6.5242 | 0.0134 | -0.0185 | 0.0319 | -18.5324 | 11 | 4 | -78.8930 | 329.9891 | -1.3330 | -1.0195 | 0.2250 | 0 | 0 |
| tma_baseline | double | 1 | 5829.0000 | 529.9091 | 12.1494 | -0.0047 | -0.0370 | 0.0322 | -19.5969 | 11 | 4 | -169.0038 | 407.8916 | -0.6769 | -0.7914 | 0.5575 | 0 | 0 |
| t3_baseline | default | 1 | 10866.0000 | 987.8182 | 6.4944 | 0.0105 | -0.0213 | 0.0318 | -21.0594 | 11 | 4 | -66.6471 | 364.4884 | -1.4984 | -1.0338 | 0.3125 | 0 | 0 |
| t3_baseline | double | 1 | 6888.0000 | 626.1818 | 9.9345 | -0.0047 | -0.0362 | 0.0315 | -22.6677 | 11 | 5 | -139.1092 | 345.0990 | -0.9048 | -1.0584 | 0.5750 | 0 | 0 |
| wma_baseline | default | 1 | 10876.0000 | 988.7273 | 6.5494 | 0.0075 | -0.0243 | 0.0318 | -24.0403 | 11 | 5 | -97.7780 | 347.4984 | -1.3916 | -1.1268 | 0.3450 | 0 | 0 |
| wma_baseline | double | 1 | 7780.0000 | 707.2727 | 9.0870 | -0.0022 | -0.0343 | 0.0321 | -24.2319 | 11 | 4 | -147.8771 | 374.4340 | -0.8865 | -1.0374 | 0.5300 | 0 | 0 |
| mcginley_dynamic_index | default | 1 | 8416.0000 | 765.0909 | 8.4654 | -0.0002 | -0.0319 | 0.0317 | -24.4108 | 11 | 4 | -124.2625 | 313.8245 | -1.0549 | -1.1018 | 0.4975 | 0 | 0 |
| fantail_vma | double | 1 | 10921.0000 | 992.8182 | 6.5843 | 0.0070 | -0.0248 | 0.0318 | -24.6233 | 11 | 5 | -79.0541 | 361.6407 | -1.8210 | -1.3466 | 0.3825 | 0 | 0 |
| kama_baseline | double | 1 | 7857.0000 | 714.2727 | 9.1587 | -0.0049 | -0.0367 | 0.0318 | -26.2325 | 11 | 3 | -94.3591 | 347.2988 | -1.5843 | -1.2408 | 0.5750 | 0 | 0 |
| sma_baseline | default | 1 | 8735.0000 | 794.0909 | 8.1582 | -0.0021 | -0.0338 | 0.0317 | -26.8546 | 11 | 4 | -129.1801 | 361.1237 | -1.1703 | -1.2158 | 0.5050 | 0 | 0 |
| super_smoother_2pole_baseline | double | 1 | 10545.0000 | 958.6364 | 6.8042 | 0.0021 | -0.0297 | 0.0317 | -28.4448 | 11 | 4 | -110.0545 | 401.2899 | -1.6357 | -1.3504 | 0.4600 | 0 | 0 |
| tma_baseline | default | 1 | 8489.0000 | 771.7273 | 8.3912 | -0.0071 | -0.0390 | 0.0318 | -30.0854 | 11 | 5 | -118.6979 | 413.2745 | -1.3972 | -1.4116 | 0.6275 | 0 | 0 |
| ema_baseline | default | 1 | 9754.0000 | 886.7273 | 7.2985 | -0.0026 | -0.0345 | 0.0319 | -30.5885 | 11 | 4 | -126.3927 | 396.3697 | -1.3571 | -1.3803 | 0.5675 | 0 | 0 |
| rma_baseline | half | 1 | 10000.0000 | 909.0909 | 7.1330 | -0.0023 | -0.0342 | 0.0319 | -31.1148 | 11 | 3 | -126.8467 | 398.5191 | -1.4239 | -1.4009 | 0.5375 | 0 | 0 |
| tma_baseline | half | 1 | 12808.0000 | 1164.3636 | 5.5964 | 0.0050 | -0.0269 | 0.0319 | -31.3331 | 11 | 2 | -107.3187 | 445.2588 | -2.2395 | -1.5587 | 0.4000 | 0 | 0 |
| t3_baseline | half | 1 | 17519.0000 | 1592.6364 | 4.0925 | 0.0113 | -0.0206 | 0.0319 | -32.8340 | 11 | 4 | -88.6893 | 435.8507 | -2.3697 | -1.6934 | 0.1850 | 0 | 0 |
| sma_baseline | half | 1 | 12658.0000 | 1150.7273 | 5.6563 | 0.0030 | -0.0288 | 0.0318 | -33.1646 | 11 | 4 | -91.5350 | 460.7141 | -2.2290 | -1.6264 | 0.4375 | 0 | 0 |
| mcginley_dynamic_index | half | 1 | 11999.0000 | 1090.8182 | 5.9502 | 0.0010 | -0.0307 | 0.0317 | -33.4715 | 11 | 4 | -108.8390 | 416.2953 | -1.7548 | -1.5469 | 0.4800 | 0 | 0 |
| vidya | default | 1 | 16217.0000 | 1474.2727 | 4.4115 | 0.0080 | -0.0239 | 0.0318 | -35.1922 | 11 | 3 | -97.4259 | 439.1121 | -2.9497 | -1.8535 | 0.2500 | 0 | 0 |
| vidya | half | 0 | 16217.0000 | 1474.2727 | 4.4115 | 0.0080 | -0.0239 | 0.0318 | -35.1922 | 11 | 3 | -97.4259 | 439.1121 | -2.9497 | -1.8535 | 0.2500 | 0 | 0 |
| alma_baseline | double | 1 | 15003.0000 | 1363.9091 | 4.7764 | 0.0056 | -0.0263 | 0.0319 | -35.9213 | 11 | 3 | -113.1704 | 492.4653 | -2.4634 | -1.8129 | 0.3275 | 0 | 0 |
| wma_baseline | half | 1 | 15456.0000 | 1405.0909 | 4.6390 | 0.0060 | -0.0259 | 0.0319 | -36.4536 | 11 | 3 | -114.0088 | 489.5093 | -2.5413 | -1.8403 | 0.2950 | 0 | 0 |
| frama_baseline | default | 1 | 13231.0000 | 1202.8182 | 5.4221 | 0.0012 | -0.0306 | 0.0318 | -36.8303 | 11 | 3 | -101.2530 | 463.9440 | -3.0457 | -1.9834 | 0.4425 | 0 | 0 |
| frama_baseline | half | 1 | 11392.0000 | 1035.6364 | 6.2870 | -0.0038 | -0.0357 | 0.0319 | -36.9605 | 11 | 3 | -133.1900 | 435.4816 | -1.9237 | -1.7141 | 0.6150 | 0 | 0 |
| ema_baseline | half | 1 | 13602.0000 | 1236.5455 | 5.2554 | 0.0018 | -0.0300 | 0.0318 | -37.0881 | 11 | 3 | -101.8013 | 475.5205 | -2.4866 | -1.7626 | 0.4700 | 0 | 0 |
| super_smoother_2pole_baseline | default | 1 | 15814.0000 | 1437.6364 | 4.5426 | 0.0055 | -0.0265 | 0.0320 | -38.1241 | 11 | 4 | -126.7504 | 485.3229 | -2.4814 | -1.9437 | 0.3650 | 0 | 0 |
| frama_baseline | double | 1 | 12481.0000 | 1134.6364 | 5.7518 | -0.0032 | -0.0349 | 0.0318 | -39.6388 | 11 | 3 | -103.1909 | 481.3729 | -2.7479 | -2.1533 | 0.5575 | 0 | 0 |
| kama_baseline | half | 1 | 13885.0000 | 1262.2727 | 5.1681 | -0.0025 | -0.0344 | 0.0318 | -43.3753 | 11 | 2 | -154.2998 | 511.9332 | -2.8485 | -2.1098 | 0.5575 | 0 | 0 |
| vidya | double | 1 | 12902.0000 | 1172.9091 | 5.5014 | -0.0053 | -0.0370 | 0.0317 | -43.4309 | 11 | 2 | -94.3509 | 531.6679 | -3.4650 | -2.2229 | 0.6275 | 0 | 0 |
| kama_baseline | default | 1 | 10542.0000 | 958.3636 | 6.7884 | -0.0144 | -0.0461 | 0.0317 | -44.2131 | 11 | 3 | -95.9061 | 538.1243 | -3.3652 | -2.3032 | 0.7825 | 0 | 0 |
| lsma_baseline | half | 1 | 20884.0000 | 1898.5455 | 3.4629 | 0.0056 | -0.0265 | 0.0321 | -50.2475 | 11 | 2 | -112.7153 | 603.4695 | -3.2749 | -2.4197 | 0.2975 | 0 | 0 |
| alma_baseline | default | 1 | 22371.0000 | 2033.7273 | 3.2147 | 0.0007 | -0.0313 | 0.0320 | -63.6488 | 11 | 2 | -124.4324 | 751.2354 | -4.1047 | -3.2556 | 0.4625 | 0 | 0 |
| super_smoother_2pole_baseline | half | 1 | 23445.0000 | 2131.3636 | 3.0729 | 0.0013 | -0.0307 | 0.0320 | -65.4030 | 11 | 1 | -140.3204 | 762.9745 | -4.0859 | -3.3069 | 0.4350 | 0 | 0 |
| hma_baseline | half | 1 | 23297.0000 | 2117.9091 | 3.1015 | -0.0035 | -0.0356 | 0.0321 | -75.3802 | 11 | 2 | -202.4662 | 829.4902 | -3.7167 | -3.6665 | 0.6725 | 0 | 0 |
| alma_baseline | half | 1 | 34583.0000 | 3143.9091 | 2.0909 | -0.0014 | -0.0335 | 0.0320 | -105.1750 | 11 | 0 | -266.4846 | 1157.2475 | -4.6100 | -4.7546 | 0.5750 | 0 | 0 |


**0 of 45 candidate-settings clear the empirical best-of-15 floor; 0 clear the alone floor.** 0 of 45 have a positive net R per year.


### BASELINE — `flip_only`, stability across the three settings

`sign_agree = 1` means all three settings agree on the sign of net R per year. A candidate positive on one setting and negative on two is being fitted, not measured.

| indicator | settings | settings_positive | sign_agree | R_per_year_min | R_per_year_med | R_per_year_max | spread |
|---|---:|---:|---:|---:|---:|---:|---:|
| rma_baseline | 3 | 0 | 1 | -31.1148 | -13.1551 | -8.2842 | 22.8306 |
| hma_baseline | 3 | 0 | 1 | -75.3802 | -16.2659 | -3.4154 | 71.9648 |
| lsma_baseline | 3 | 0 | 1 | -50.2475 | -17.6529 | -9.7766 | 40.4709 |
| fantail_vma | 3 | 0 | 1 | -24.6233 | -18.5324 | -18.5324 | 6.0909 |
| t3_baseline | 3 | 0 | 1 | -32.8340 | -22.6677 | -21.0594 | 11.7746 |
| wma_baseline | 3 | 0 | 1 | -36.4536 | -24.2319 | -24.0403 | 12.4133 |
| mcginley_dynamic_index | 3 | 0 | 1 | -33.4715 | -24.4108 | -10.1199 | 23.3516 |
| sma_baseline | 3 | 0 | 1 | -33.1646 | -26.8546 | -13.7363 | 19.4283 |
| tma_baseline | 3 | 0 | 1 | -31.3331 | -30.0854 | -19.5969 | 11.7362 |
| ema_baseline | 3 | 0 | 1 | -37.0881 | -30.5885 | -12.2246 | 24.8636 |
| vidya | 3 | 0 | 1 | -43.4309 | -35.1922 | -35.1922 | 8.2387 |
| frama_baseline | 3 | 0 | 1 | -39.6388 | -36.9605 | -36.8303 | 2.8085 |
| super_smoother_2pole_baseline | 3 | 0 | 1 | -65.4030 | -38.1241 | -28.4448 | 36.9582 |
| kama_baseline | 3 | 0 | 1 | -44.2131 | -43.3753 | -26.2325 | 17.9806 |
| alma_baseline | 3 | 0 | 1 | -105.1750 | -63.6488 | -35.9213 | 69.2537 |


**15 of 15 candidates have all three settings agreeing in sign.**


## BASELINE — `jack`, fixed settings, unseen trade years 2005-2015

Empirical yearly-t floors **from the random-entry null**: alone **-0.405**, best-of-15 **0.732**. The analytic equivalents on 11 yearly observations are 1.812 and 3.395 — the empirical ones are lower because the analytic formula assumes a **zero-mean** null while the real null also pays costs, so it is centred below zero.

| indicator | setting | distinct_setting | n_entered | trades_per_year | mean_bars | R_gross_per_trade | R_net_per_trade | cost_per_trade | R_net_per_year | years | years_positive | worst_year | worst_dip_R | t_yearly | t_block_boot | null_p | clears_alone_emp | clears_family_emp |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| sma_baseline | double | 1 | 5898.0000 | 536.1818 | 6.8120 | 0.0203 | -0.0124 | 0.0327 | -6.6270 | 11 | 5 | -40.1710 | 125.1494 | -0.8551 | -0.7108 | 0.2125 | 0 | 0 |
| rma_baseline | double | 1 | 4925.0000 | 447.7273 | 6.8313 | 0.0165 | -0.0156 | 0.0321 | -7.0052 | 11 | 3 | -48.9152 | 137.0187 | -1.0079 | -0.8900 | 0.2525 | 0 | 0 |
| t3_baseline | double | 1 | 6815.0000 | 619.5455 | 6.8023 | 0.0199 | -0.0116 | 0.0315 | -7.1775 | 11 | 3 | -48.3146 | 139.7216 | -0.9832 | -0.6987 | 0.1975 | 0 | 0 |
| tma_baseline | double | 1 | 5771.0000 | 524.6364 | 6.9475 | 0.0159 | -0.0164 | 0.0323 | -8.5885 | 11 | 5 | -44.4438 | 152.1823 | -1.0863 | -0.9896 | 0.2250 | 0 | 0 |
| ema_baseline | double | 1 | 6782.0000 | 616.5455 | 6.4512 | 0.0168 | -0.0156 | 0.0323 | -9.5988 | 11 | 6 | -46.4079 | 147.3966 | -1.3202 | -1.0291 | 0.2200 | 0 | 0 |
| mcginley_dynamic_index | double | 1 | 5809.0000 | 528.0909 | 6.6328 | 0.0140 | -0.0183 | 0.0323 | -9.6619 | 11 | 4 | -61.7164 | 159.6831 | -1.1799 | -1.1900 | 0.3000 | 0 | 0 |
| mcginley_dynamic_index | default | 1 | 8351.0000 | 759.1818 | 6.1591 | 0.0181 | -0.0137 | 0.0318 | -10.3837 | 11 | 5 | -62.9747 | 172.0835 | -1.1225 | -0.9961 | 0.1600 | 0 | 0 |
| rma_baseline | default | 1 | 6940.0000 | 630.9091 | 6.4059 | 0.0157 | -0.0166 | 0.0323 | -10.4587 | 11 | 6 | -50.2827 | 157.9422 | -1.3839 | -1.1064 | 0.2350 | 0 | 0 |
| hma_baseline | double | 1 | 10423.0000 | 947.5455 | 5.6675 | 0.0206 | -0.0115 | 0.0321 | -10.8992 | 11 | 3 | -45.3191 | 224.7799 | -0.9924 | -0.8731 | 0.1175 | 0 | 0 |
| kama_baseline | double | 1 | 7789.0000 | 708.0909 | 6.4924 | 0.0156 | -0.0163 | 0.0319 | -11.5384 | 11 | 3 | -42.0533 | 171.9825 | -1.9586 | -1.1508 | 0.2150 | 0 | 0 |
| wma_baseline | double | 1 | 7708.0000 | 700.7273 | 6.3669 | 0.0142 | -0.0180 | 0.0322 | -12.5908 | 11 | 3 | -67.8780 | 192.0701 | -1.3809 | -1.2470 | 0.2175 | 0 | 0 |
| lsma_baseline | double | 1 | 9289.0000 | 844.4545 | 5.8265 | 0.0146 | -0.0174 | 0.0320 | -14.7136 | 11 | 3 | -45.2065 | 268.7005 | -1.4573 | -1.1753 | 0.2125 | 0 | 0 |
| ema_baseline | default | 1 | 9687.0000 | 880.6364 | 5.8294 | 0.0144 | -0.0175 | 0.0320 | -15.4494 | 11 | 3 | -65.3982 | 225.9189 | -1.5680 | -1.3538 | 0.1875 | 0 | 0 |
| sma_baseline | default | 1 | 8662.0000 | 787.4545 | 6.2801 | 0.0089 | -0.0229 | 0.0318 | -18.0247 | 11 | 4 | -65.3196 | 243.6717 | -1.9967 | -1.5079 | 0.3150 | 0 | 0 |
| wma_baseline | default | 1 | 10811.0000 | 982.8182 | 5.6459 | 0.0134 | -0.0185 | 0.0318 | -18.1599 | 11 | 3 | -57.2768 | 263.2299 | -1.8139 | -1.3680 | 0.1950 | 0 | 0 |
| t3_baseline | default | 1 | 10761.0000 | 978.2727 | 5.6970 | 0.0132 | -0.0187 | 0.0319 | -18.2577 | 11 | 2 | -60.2704 | 289.1137 | -1.7250 | -1.3644 | 0.2400 | 0 | 0 |
| rma_baseline | half | 1 | 9931.0000 | 902.8182 | 5.7699 | 0.0114 | -0.0206 | 0.0320 | -18.5732 | 11 | 3 | -70.6959 | 254.7644 | -1.8897 | -1.5886 | 0.2525 | 0 | 0 |
| lsma_baseline | default | 1 | 13894.0000 | 1263.0909 | 4.5759 | 0.0171 | -0.0149 | 0.0320 | -18.8809 | 11 | 4 | -67.0586 | 266.4314 | -1.4976 | -1.3405 | 0.1075 | 0 | 0 |
| fantail_vma | default | 1 | 10906.0000 | 991.4545 | 5.5406 | 0.0124 | -0.0195 | 0.0319 | -19.3755 | 11 | 4 | -66.3902 | 298.8744 | -1.6539 | -1.5747 | 0.2325 | 0 | 0 |
| fantail_vma | half | 0 | 10906.0000 | 991.4545 | 5.5406 | 0.0124 | -0.0195 | 0.0319 | -19.3755 | 11 | 4 | -66.3902 | 298.8744 | -1.6539 | -1.5747 | 0.2325 | 0 | 0 |
| hma_baseline | default | 1 | 15631.0000 | 1421.0000 | 4.2547 | 0.0182 | -0.0138 | 0.0321 | -19.6758 | 11 | 3 | -79.5044 | 248.1012 | -1.6920 | -1.2915 | 0.0650 | 0 | 0 |
| tma_baseline | default | 1 | 8385.0000 | 762.2727 | 6.5047 | 0.0060 | -0.0259 | 0.0319 | -19.7413 | 11 | 3 | -64.1531 | 285.4289 | -2.0296 | -1.6608 | 0.3850 | 0 | 0 |
| fantail_vma | double | 1 | 10803.0000 | 982.0909 | 5.6068 | 0.0105 | -0.0214 | 0.0319 | -21.0064 | 11 | 4 | -68.4360 | 291.1682 | -2.0056 | -1.6986 | 0.2750 | 0 | 0 |
| mcginley_dynamic_index | half | 1 | 11937.0000 | 1085.1818 | 5.2787 | 0.0120 | -0.0197 | 0.0317 | -21.3604 | 11 | 3 | -56.0565 | 282.0242 | -2.1828 | -1.5851 | 0.1775 | 0 | 0 |
| super_smoother_2pole_baseline | double | 1 | 10435.0000 | 948.6364 | 5.8439 | 0.0079 | -0.0239 | 0.0318 | -22.7079 | 11 | 3 | -64.7526 | 305.9972 | -2.1957 | -1.6977 | 0.3050 | 0 | 0 |
| sma_baseline | half | 1 | 12567.0000 | 1142.4545 | 5.1825 | 0.0098 | -0.0220 | 0.0319 | -25.1718 | 11 | 3 | -83.8223 | 338.3760 | -2.2067 | -1.8220 | 0.2350 | 0 | 0 |
| tma_baseline | half | 1 | 12687.0000 | 1153.3636 | 5.1657 | 0.0095 | -0.0224 | 0.0319 | -25.8585 | 11 | 2 | -106.6310 | 353.0791 | -1.9612 | -1.8155 | 0.2650 | 0 | 0 |
| kama_baseline | default | 1 | 10453.0000 | 950.2727 | 5.7459 | 0.0044 | -0.0274 | 0.0318 | -26.0081 | 11 | 2 | -89.1654 | 343.1763 | -2.5321 | -2.1743 | 0.3875 | 0 | 0 |
| ema_baseline | half | 1 | 13542.0000 | 1231.0909 | 4.8441 | 0.0098 | -0.0220 | 0.0318 | -27.1427 | 11 | 2 | -76.5028 | 351.3491 | -2.7242 | -1.9450 | 0.2375 | 0 | 0 |
| alma_baseline | double | 1 | 14911.0000 | 1355.5455 | 4.5472 | 0.0111 | -0.0208 | 0.0319 | -28.1595 | 11 | 3 | -106.5700 | 375.1093 | -2.0188 | -1.9076 | 0.1625 | 0 | 0 |
| vidya | half | 0 | 16145.0000 | 1467.7273 | 4.2151 | 0.0120 | -0.0198 | 0.0318 | -29.1197 | 11 | 3 | -96.0433 | 362.4599 | -2.6862 | -2.0343 | 0.1375 | 0 | 0 |
| vidya | default | 1 | 16145.0000 | 1467.7273 | 4.2151 | 0.0120 | -0.0198 | 0.0318 | -29.1197 | 11 | 3 | -96.0433 | 362.4599 | -2.6862 | -2.0343 | 0.1375 | 0 | 0 |
| wma_baseline | half | 1 | 15389.0000 | 1399.0000 | 4.4315 | 0.0109 | -0.0211 | 0.0319 | -29.4870 | 11 | 2 | -108.8485 | 383.4881 | -2.2155 | -1.9798 | 0.1700 | 0 | 0 |
| frama_baseline | default | 1 | 13143.0000 | 1194.8182 | 4.9680 | 0.0069 | -0.0250 | 0.0319 | -29.8834 | 11 | 2 | -93.5057 | 371.3347 | -2.8595 | -2.3108 | 0.3300 | 0 | 0 |
| t3_baseline | half | 1 | 17418.0000 | 1583.4545 | 3.9652 | 0.0129 | -0.0190 | 0.0319 | -30.1579 | 11 | 3 | -90.9465 | 386.0234 | -2.6304 | -1.9977 | 0.1300 | 0 | 0 |
| frama_baseline | double | 1 | 12414.0000 | 1128.5455 | 5.0960 | 0.0043 | -0.0275 | 0.0318 | -31.0090 | 11 | 1 | -77.0372 | 365.4799 | -3.7159 | -2.5256 | 0.3575 | 0 | 0 |
| super_smoother_2pole_baseline | default | 1 | 15682.0000 | 1425.6364 | 4.3532 | 0.0101 | -0.0219 | 0.0320 | -31.2448 | 11 | 3 | -107.8586 | 395.4348 | -2.4228 | -2.1149 | 0.1800 | 0 | 0 |
| frama_baseline | half | 1 | 11304.0000 | 1027.6364 | 5.2637 | 0.0014 | -0.0305 | 0.0319 | -31.3276 | 11 | 1 | -71.6667 | 369.8382 | -3.8618 | -2.5426 | 0.4950 | 0 | 0 |
| vidya | double | 1 | 12824.0000 | 1165.8182 | 5.0837 | 0.0029 | -0.0288 | 0.0317 | -33.6182 | 11 | 2 | -77.8802 | 409.3550 | -3.3955 | -2.4461 | 0.4125 | 0 | 0 |
| kama_baseline | half | 1 | 13805.0000 | 1255.0000 | 4.7696 | 0.0034 | -0.0285 | 0.0318 | -35.7556 | 11 | 1 | -89.0194 | 415.7824 | -3.5259 | -2.5123 | 0.3825 | 0 | 0 |
| lsma_baseline | half | 1 | 20858.0000 | 1896.1818 | 3.2499 | 0.0036 | -0.0285 | 0.0321 | -54.0426 | 11 | 2 | -153.5416 | 606.1641 | -3.4105 | -3.2118 | 0.3425 | 0 | 0 |
| alma_baseline | default | 1 | 22306.0000 | 2027.8182 | 3.1685 | 0.0043 | -0.0277 | 0.0320 | -56.2491 | 11 | 1 | -117.1882 | 665.5029 | -4.1605 | -3.5686 | 0.3375 | 0 | 0 |
| super_smoother_2pole_baseline | half | 1 | 23351.0000 | 2122.8182 | 3.0346 | 0.0041 | -0.0279 | 0.0320 | -59.2513 | 11 | 0 | -125.3741 | 694.4957 | -4.4959 | -3.6549 | 0.3650 | 0 | 0 |
| hma_baseline | half | 1 | 23232.0000 | 2112.0000 | 3.0085 | -0.0008 | -0.0328 | 0.0321 | -69.3745 | 11 | 2 | -202.2852 | 763.1107 | -3.6222 | -3.9639 | 0.4850 | 0 | 0 |
| alma_baseline | half | 1 | 34576.0000 | 3143.2727 | 2.0829 | 0.0001 | -0.0319 | 0.0320 | -100.3023 | 11 | 0 | -243.7322 | 1103.6869 | -5.0704 | -5.2421 | 0.4975 | 0 | 0 |


**0 of 45 candidate-settings clear the empirical best-of-15 floor; 0 clear the alone floor.** 0 of 45 have a positive net R per year.


### BASELINE — `jack`, stability across the three settings

`sign_agree = 1` means all three settings agree on the sign of net R per year. A candidate positive on one setting and negative on two is being fitted, not measured.

| indicator | settings | settings_positive | sign_agree | R_per_year_min | R_per_year_med | R_per_year_max | spread |
|---|---:|---:|---:|---:|---:|---:|---:|
| mcginley_dynamic_index | 3 | 0 | 1 | -21.3604 | -10.3837 | -9.6619 | 11.6985 |
| rma_baseline | 3 | 0 | 1 | -18.5732 | -10.4587 | -7.0052 | 11.5679 |
| ema_baseline | 3 | 0 | 1 | -27.1427 | -15.4494 | -9.5988 | 17.5439 |
| sma_baseline | 3 | 0 | 1 | -25.1718 | -18.0247 | -6.6270 | 18.5448 |
| wma_baseline | 3 | 0 | 1 | -29.4870 | -18.1599 | -12.5908 | 16.8962 |
| t3_baseline | 3 | 0 | 1 | -30.1579 | -18.2577 | -7.1775 | 22.9804 |
| lsma_baseline | 3 | 0 | 1 | -54.0426 | -18.8809 | -14.7136 | 39.3290 |
| fantail_vma | 3 | 0 | 1 | -21.0064 | -19.3755 | -19.3755 | 1.6308 |
| hma_baseline | 3 | 0 | 1 | -69.3745 | -19.6758 | -10.8992 | 58.4754 |
| tma_baseline | 3 | 0 | 1 | -25.8585 | -19.7413 | -8.5885 | 17.2700 |
| kama_baseline | 3 | 0 | 1 | -35.7556 | -26.0081 | -11.5384 | 24.2171 |
| vidya | 3 | 0 | 1 | -33.6182 | -29.1197 | -29.1197 | 4.4985 |
| frama_baseline | 3 | 0 | 1 | -31.3276 | -31.0090 | -29.8834 | 1.4442 |
| super_smoother_2pole_baseline | 3 | 0 | 1 | -59.2513 | -31.2448 | -22.7079 | 36.5434 |
| alma_baseline | 3 | 0 | 1 | -100.3023 | -56.2491 | -28.1595 | 72.1428 |


**15 of 15 candidates have all three settings agreeing in sign.**


## BASELINE — `textbook`, fixed settings, unseen trade years 2005-2015

Empirical yearly-t floors **from the random-entry null**: alone **-0.483**, best-of-15 **0.506**. The analytic equivalents on 11 yearly observations are 1.812 and 3.395 — the empirical ones are lower because the analytic formula assumes a **zero-mean** null while the real null also pays costs, so it is centred below zero.

| indicator | setting | distinct_setting | n_entered | trades_per_year | mean_bars | R_gross_per_trade | R_net_per_trade | cost_per_trade | R_net_per_year | years | years_positive | worst_year | worst_dip_R | t_yearly | t_block_boot | null_p | clears_alone_emp | clears_family_emp |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| sma_baseline | double | 1 | 5627.0000 | 511.5455 | 5.1966 | 0.0154 | -0.0173 | 0.0327 | -8.8496 | 11 | 2 | -31.0819 | 117.6454 | -1.9096 | -1.3628 | 0.2150 | 0 | 0 |
| tma_baseline | double | 1 | 5489.0000 | 499.0000 | 5.2685 | 0.0117 | -0.0207 | 0.0324 | -10.3289 | 11 | 4 | -29.3225 | 133.4190 | -2.3147 | -1.6899 | 0.2750 | 0 | 0 |
| t3_baseline | double | 1 | 6475.0000 | 588.6364 | 5.1949 | 0.0138 | -0.0177 | 0.0314 | -10.4128 | 11 | 4 | -38.6891 | 166.6202 | -1.7414 | -1.4153 | 0.2500 | 0 | 0 |
| mcginley_dynamic_index | double | 1 | 5539.0000 | 503.5455 | 5.1257 | 0.0108 | -0.0215 | 0.0324 | -10.8398 | 11 | 2 | -36.9825 | 132.0671 | -2.3696 | -1.7705 | 0.2750 | 0 | 0 |
| hma_baseline | double | 1 | 9918.0000 | 901.6364 | 4.7597 | 0.0198 | -0.0124 | 0.0322 | -11.1446 | 11 | 2 | -49.9736 | 196.5486 | -1.3464 | -1.3070 | 0.0750 | 0 | 0 |
| rma_baseline | double | 1 | 4715.0000 | 428.6364 | 5.0388 | 0.0060 | -0.0262 | 0.0322 | -11.2414 | 11 | 3 | -35.2805 | 134.1441 | -2.3011 | -1.8223 | 0.3625 | 0 | 0 |
| rma_baseline | default | 1 | 6636.0000 | 603.2727 | 5.0196 | 0.0117 | -0.0207 | 0.0324 | -12.4869 | 11 | 3 | -32.5520 | 159.2963 | -2.7392 | -1.6948 | 0.2750 | 0 | 0 |
| ema_baseline | double | 1 | 6486.0000 | 589.6364 | 5.0395 | 0.0109 | -0.0215 | 0.0324 | -12.6702 | 11 | 3 | -35.3428 | 158.8336 | -2.6810 | -1.7536 | 0.2975 | 0 | 0 |
| wma_baseline | double | 1 | 7401.0000 | 672.8182 | 4.9762 | 0.0082 | -0.0240 | 0.0322 | -16.1544 | 11 | 3 | -52.0913 | 208.6489 | -2.6803 | -2.1070 | 0.3150 | 0 | 0 |
| mcginley_dynamic_index | default | 1 | 8021.0000 | 729.1818 | 4.9043 | 0.0093 | -0.0225 | 0.0318 | -16.3938 | 11 | 4 | -40.9587 | 205.7033 | -2.4547 | -2.0648 | 0.2875 | 0 | 0 |
| ema_baseline | default | 1 | 9355.0000 | 850.4545 | 4.7914 | 0.0121 | -0.0198 | 0.0320 | -16.8435 | 11 | 3 | -43.2357 | 218.8028 | -2.2195 | -1.9167 | 0.2000 | 0 | 0 |
| sma_baseline | default | 1 | 8311.0000 | 755.5455 | 4.9610 | 0.0091 | -0.0227 | 0.0318 | -17.1527 | 11 | 3 | -42.8254 | 213.6869 | -2.7973 | -2.1720 | 0.3025 | 0 | 0 |
| kama_baseline | double | 1 | 7438.0000 | 676.1818 | 4.7983 | 0.0048 | -0.0271 | 0.0320 | -18.3357 | 11 | 1 | -40.7132 | 210.7131 | -4.5139 | -2.3919 | 0.3475 | 0 | 0 |
| rma_baseline | half | 1 | 9588.0000 | 871.6364 | 4.7644 | 0.0102 | -0.0218 | 0.0320 | -19.0145 | 11 | 3 | -46.0574 | 235.5364 | -2.6995 | -2.1292 | 0.2675 | 0 | 0 |
| tma_baseline | default | 1 | 7938.0000 | 721.6364 | 5.1295 | 0.0044 | -0.0276 | 0.0320 | -19.9140 | 11 | 1 | -55.3875 | 247.0548 | -3.1651 | -2.5244 | 0.4150 | 0 | 0 |
| wma_baseline | default | 1 | 10433.0000 | 948.4545 | 4.6751 | 0.0105 | -0.0213 | 0.0319 | -20.2223 | 11 | 3 | -54.9646 | 255.1860 | -2.8208 | -2.1652 | 0.2375 | 0 | 0 |
| fantail_vma | half | 0 | 10287.0000 | 935.1818 | 4.5290 | 0.0100 | -0.0219 | 0.0320 | -20.5129 | 11 | 3 | -42.5138 | 270.4771 | -3.2732 | -2.4492 | 0.2150 | 0 | 0 |
| fantail_vma | default | 1 | 10287.0000 | 935.1818 | 4.5290 | 0.0100 | -0.0219 | 0.0320 | -20.5129 | 11 | 3 | -42.5138 | 270.4771 | -3.2732 | -2.4492 | 0.2150 | 0 | 0 |
| t3_baseline | default | 1 | 10220.0000 | 929.0909 | 4.7040 | 0.0096 | -0.0223 | 0.0319 | -20.6987 | 11 | 1 | -49.7974 | 273.4667 | -3.5860 | -2.2577 | 0.2400 | 0 | 0 |
| fantail_vma | double | 1 | 10226.0000 | 929.6364 | 4.5342 | 0.0094 | -0.0225 | 0.0319 | -20.8919 | 11 | 3 | -55.0058 | 263.4178 | -3.3876 | -2.5890 | 0.2625 | 0 | 0 |
| lsma_baseline | double | 1 | 8933.0000 | 812.0909 | 4.6972 | 0.0049 | -0.0272 | 0.0321 | -22.1174 | 11 | 3 | -66.4261 | 293.9422 | -2.5149 | -2.5631 | 0.3575 | 0 | 0 |
| tma_baseline | half | 1 | 12027.0000 | 1093.3636 | 4.4345 | 0.0106 | -0.0213 | 0.0319 | -23.3402 | 11 | 2 | -74.9501 | 307.7582 | -2.7118 | -2.3932 | 0.2250 | 0 | 0 |
| lsma_baseline | default | 1 | 13474.0000 | 1224.9091 | 4.0219 | 0.0128 | -0.0192 | 0.0321 | -23.5699 | 11 | 2 | -83.2329 | 297.1337 | -2.6865 | -2.2594 | 0.1575 | 0 | 0 |
| hma_baseline | default | 1 | 14957.0000 | 1359.7273 | 3.8185 | 0.0146 | -0.0175 | 0.0321 | -23.8452 | 11 | 2 | -91.1062 | 275.8993 | -2.4021 | -2.1197 | 0.0925 | 0 | 0 |
| super_smoother_2pole_baseline | double | 1 | 9918.0000 | 901.6364 | 4.7828 | 0.0048 | -0.0270 | 0.0318 | -24.3698 | 11 | 2 | -49.1899 | 308.4044 | -3.8090 | -2.6357 | 0.3575 | 0 | 0 |
| kama_baseline | default | 1 | 9981.0000 | 907.3636 | 4.5748 | 0.0036 | -0.0282 | 0.0318 | -25.6060 | 11 | 2 | -61.9584 | 315.2338 | -3.7083 | -2.9691 | 0.3825 | 0 | 0 |
| sma_baseline | half | 1 | 12112.0000 | 1101.0909 | 4.4238 | 0.0086 | -0.0233 | 0.0319 | -25.6448 | 11 | 1 | -64.3239 | 321.9424 | -3.8051 | -2.6991 | 0.2625 | 0 | 0 |
| mcginley_dynamic_index | half | 1 | 11617.0000 | 1056.0909 | 4.4702 | 0.0071 | -0.0246 | 0.0317 | -26.0107 | 11 | 2 | -59.1777 | 309.1258 | -3.8397 | -2.5680 | 0.2875 | 0 | 0 |
| frama_baseline | double | 1 | 12029.0000 | 1093.5455 | 4.1816 | 0.0062 | -0.0255 | 0.0318 | -27.9221 | 11 | 0 | -72.7945 | 320.1399 | -4.7533 | -3.1887 | 0.3075 | 0 | 0 |
| frama_baseline | default | 1 | 12622.0000 | 1147.4545 | 4.1144 | 0.0069 | -0.0250 | 0.0319 | -28.6678 | 11 | 0 | -66.3893 | 336.4089 | -4.3661 | -3.1151 | 0.3150 | 0 | 0 |
| ema_baseline | half | 1 | 13237.0000 | 1203.3636 | 4.2124 | 0.0080 | -0.0239 | 0.0318 | -28.7018 | 11 | 2 | -71.6659 | 342.5347 | -3.3502 | -2.7097 | 0.2475 | 0 | 0 |
| alma_baseline | double | 1 | 14342.0000 | 1303.8182 | 4.0224 | 0.0092 | -0.0227 | 0.0319 | -29.6178 | 11 | 2 | -90.2842 | 382.8499 | -3.0448 | -2.8758 | 0.2125 | 0 | 0 |
| frama_baseline | half | 1 | 10781.0000 | 980.0909 | 4.3662 | 0.0003 | -0.0317 | 0.0320 | -31.0848 | 11 | 1 | -71.2840 | 344.6527 | -4.0349 | -3.4902 | 0.4700 | 0 | 0 |
| wma_baseline | half | 1 | 15009.0000 | 1364.4545 | 3.9536 | 0.0090 | -0.0229 | 0.0319 | -31.2230 | 11 | 1 | -88.0858 | 393.5409 | -3.5821 | -3.0124 | 0.2125 | 0 | 0 |
| vidya | double | 1 | 12324.0000 | 1120.3636 | 4.2406 | 0.0034 | -0.0284 | 0.0317 | -31.7902 | 11 | 0 | -76.2799 | 371.0630 | -4.5011 | -3.3634 | 0.3850 | 0 | 0 |
| vidya | half | 0 | 15683.0000 | 1425.7273 | 3.7096 | 0.0091 | -0.0228 | 0.0319 | -32.4548 | 11 | 0 | -85.3058 | 376.3245 | -4.2812 | -3.1303 | 0.1925 | 0 | 0 |
| vidya | default | 1 | 15683.0000 | 1425.7273 | 3.7096 | 0.0091 | -0.0228 | 0.0319 | -32.4548 | 11 | 0 | -85.3058 | 376.3245 | -4.2812 | -3.1303 | 0.1925 | 0 | 0 |
| kama_baseline | half | 1 | 13296.0000 | 1208.7273 | 4.0810 | 0.0035 | -0.0283 | 0.0319 | -34.2167 | 11 | 0 | -103.7312 | 398.9641 | -4.1686 | -3.3373 | 0.4275 | 0 | 0 |
| super_smoother_2pole_baseline | default | 1 | 14961.0000 | 1360.0909 | 3.8806 | 0.0058 | -0.0262 | 0.0320 | -35.6800 | 11 | 1 | -109.4941 | 424.0806 | -3.0793 | -3.3429 | 0.3225 | 0 | 0 |
| t3_baseline | half | 1 | 16765.0000 | 1524.0909 | 3.5880 | 0.0077 | -0.0242 | 0.0319 | -36.8837 | 11 | 2 | -106.1261 | 447.5497 | -3.4916 | -3.2759 | 0.2150 | 0 | 0 |
| lsma_baseline | half | 1 | 20567.0000 | 1869.7273 | 3.1418 | 0.0004 | -0.0317 | 0.0321 | -59.2647 | 11 | 0 | -144.3273 | 652.4556 | -4.3802 | -4.2711 | 0.5225 | 0 | 0 |
| alma_baseline | default | 1 | 21804.0000 | 1982.1818 | 3.0022 | 0.0004 | -0.0316 | 0.0320 | -62.6616 | 11 | 0 | -161.1312 | 699.3440 | -4.7251 | -4.9675 | 0.4700 | 0 | 0 |
| super_smoother_2pole_baseline | half | 1 | 22680.0000 | 2061.8182 | 2.8898 | 0.0002 | -0.0318 | 0.0320 | -65.6356 | 11 | 0 | -160.9622 | 727.0331 | -4.9144 | -5.0792 | 0.4975 | 0 | 0 |
| hma_baseline | half | 1 | 22642.0000 | 2058.3636 | 2.9166 | -0.0027 | -0.0348 | 0.0321 | -71.5975 | 11 | 1 | -152.5908 | 788.1161 | -4.3950 | -5.0536 | 0.6225 | 0 | 0 |
| alma_baseline | half | 1 | 34505.0000 | 3136.8182 | 2.0532 | 0.0012 | -0.0308 | 0.0320 | -96.6433 | 11 | 0 | -253.3761 | 1063.2638 | -4.6220 | -5.5718 | 0.3850 | 0 | 0 |


**0 of 45 candidate-settings clear the empirical best-of-15 floor; 0 clear the alone floor.** 0 of 45 have a positive net R per year.


### BASELINE — `textbook`, stability across the three settings

`sign_agree = 1` means all three settings agree on the sign of net R per year. A candidate positive on one setting and negative on two is being fitted, not measured.

| indicator | settings | settings_positive | sign_agree | R_per_year_min | R_per_year_med | R_per_year_max | spread |
|---|---:|---:|---:|---:|---:|---:|---:|
| rma_baseline | 3 | 0 | 1 | -19.0145 | -12.4869 | -11.2414 | 7.7731 |
| mcginley_dynamic_index | 3 | 0 | 1 | -26.0107 | -16.3938 | -10.8398 | 15.1709 |
| ema_baseline | 3 | 0 | 1 | -28.7018 | -16.8435 | -12.6702 | 16.0316 |
| sma_baseline | 3 | 0 | 1 | -25.6448 | -17.1527 | -8.8496 | 16.7952 |
| tma_baseline | 3 | 0 | 1 | -23.3402 | -19.9140 | -10.3289 | 13.0114 |
| wma_baseline | 3 | 0 | 1 | -31.2230 | -20.2223 | -16.1544 | 15.0686 |
| fantail_vma | 3 | 0 | 1 | -20.8919 | -20.5129 | -20.5129 | 0.3790 |
| t3_baseline | 3 | 0 | 1 | -36.8837 | -20.6987 | -10.4128 | 26.4709 |
| lsma_baseline | 3 | 0 | 1 | -59.2647 | -23.5699 | -22.1174 | 37.1473 |
| hma_baseline | 3 | 0 | 1 | -71.5975 | -23.8452 | -11.1446 | 60.4529 |
| kama_baseline | 3 | 0 | 1 | -34.2167 | -25.6060 | -18.3357 | 15.8810 |
| frama_baseline | 3 | 0 | 1 | -31.0848 | -28.6678 | -27.9221 | 3.1628 |
| vidya | 3 | 0 | 1 | -32.4548 | -32.4548 | -31.7902 | 0.6646 |
| super_smoother_2pole_baseline | 3 | 0 | 1 | -65.6356 | -35.6800 | -24.3698 | 41.2658 |
| alma_baseline | 3 | 0 | 1 | -96.6433 | -62.6616 | -29.6178 | 67.0255 |


**15 of 15 candidates have all three settings agreeing in sign.**


---

# 1c — THE SELECTION TEST, K SWEPT, LABEL-SHUFFLE NULL

At each step the candidates are ranked on that step's four TUNING years, the top K traded on its unseen year, equal weight, K swept over the whole range. **The null shuffles the tuning-year ranking and re-runs the identical top-K construction, 1,000 draws**, so it tests the SELECTION RULE and not the pool.


## The headline

| family | plan | best_K | best_R_per_year | null_mean | p | K_beating_null | K_total |
|---|---|---:|---:|---:|---:|---:|---:|
| C1 | flip_only | 11 | -8.550 | -17.150 | 0.160 | 3 | 39 |
| C1 | jack | 3 | 13.932 | -8.020 | 0.001 | 28 | 39 |
| C1 | textbook | 19 | -0.588 | -8.017 | 0.001 | 29 | 39 |
| BASELINE | flip_only | 2 | 5.125 | -18.778 | 0.058 | 2 | 15 |
| BASELINE | jack | 1 | 6.913 | -9.313 | 0.097 | 10 | 15 |
| BASELINE | textbook | 2 | 0.258 | -15.465 | 0.001 | 13 | 15 |


**JACK'S PLAN WINS THE TWO-PLAN COMPARISON, and it is not close.** On C1 the jack plan reaches **+13.93 R per year at K=3** against a null mean of −8.02, p **0.001**, with **28 of 39** K values beating their own null. The textbook plan's best K is **negative** (−0.59) even though 29 of 39 of its K values beat their null — which is the distinction that matters and is easy to miss: **beating a null of −8.02 is not the same as making money.** Under flip-only the best C1 K is −8.55 and only 3 of 39 beat anything.


That K=3 is where the jack plan peaks is worth noting and not worth over-reading: it is one sweep on one family, and Jack picks at most 3 by instruction, not because this curve says so.


## C1 — `flip_only`

| K | R_per_year_mean | R_total_build | years | years_positive | t_yearly | null_mean | null_p95 | null_p |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | -9.566 | -57.396 | 6 | 2 | -0.153 | -19.385 | 35.423 | 0.381 |
| 2 | -40.838 | -245.027 | 6 | 1 | -0.659 | -17.316 | 24.495 | 0.832 |
| 3 | -25.123 | -150.736 | 6 | 1 | -0.495 | -17.070 | 12.177 | 0.665 |
| 4 | -29.014 | -174.085 | 6 | 2 | -0.627 | -17.625 | 9.578 | 0.758 |
| 5 | -23.036 | -138.218 | 6 | 2 | -0.495 | -17.106 | 5.292 | 0.665 |
| 6 | -20.113 | -120.679 | 6 | 2 | -0.456 | -17.637 | 3.926 | 0.584 |
| 7 | -15.786 | -94.717 | 6 | 2 | -0.343 | -17.336 | 2.299 | 0.460 |
| 8 | -11.023 | -66.140 | 6 | 3 | -0.228 | -16.992 | 1.455 | 0.291 |
| 9 | -13.095 | -78.572 | 6 | 3 | -0.274 | -17.958 | -1.102 | 0.301 |
| 10 | -9.214 | -55.287 | 6 | 3 | -0.192 | -17.008 | -1.052 | 0.196 |
| 11 | -8.550 | -51.297 | 6 | 3 | -0.186 | -17.150 | -2.766 | 0.160 |
| 12 | -10.451 | -62.709 | 6 | 3 | -0.233 | -17.286 | -3.468 | 0.229 |
| 13 | -13.218 | -79.309 | 6 | 3 | -0.308 | -17.514 | -5.355 | 0.312 |
| 14 | -15.121 | -90.729 | 6 | 3 | -0.356 | -17.512 | -4.235 | 0.371 |
| 15 | -14.981 | -89.885 | 6 | 3 | -0.354 | -17.262 | -5.914 | 0.393 |
| 16 | -12.723 | -76.341 | 6 | 3 | -0.302 | -16.947 | -5.719 | 0.259 |
| 17 | -13.280 | -79.679 | 6 | 2 | -0.320 | -16.961 | -6.654 | 0.279 |
| 18 | -13.828 | -82.965 | 6 | 2 | -0.342 | -17.365 | -7.517 | 0.296 |
| 19 | -13.668 | -82.010 | 6 | 2 | -0.338 | -17.331 | -8.153 | 0.252 |
| 20 | -13.017 | -78.100 | 6 | 2 | -0.326 | -17.441 | -8.538 | 0.210 |
| 21 | -13.612 | -81.672 | 6 | 2 | -0.341 | -17.440 | -8.888 | 0.231 |
| 22 | -13.362 | -80.174 | 6 | 2 | -0.339 | -17.558 | -9.127 | 0.205 |
| 23 | -14.171 | -85.029 | 6 | 2 | -0.360 | -17.294 | -9.309 | 0.238 |
| 24 | -13.157 | -78.939 | 6 | 2 | -0.343 | -17.435 | -10.454 | 0.160 |
| 25 | -14.069 | -84.416 | 6 | 2 | -0.380 | -17.271 | -10.285 | 0.214 |
| 26 | -13.235 | -79.408 | 6 | 2 | -0.357 | -17.406 | -11.033 | 0.139 |
| 27 | -13.050 | -78.302 | 6 | 2 | -0.358 | -17.390 | -10.976 | 0.135 |
| 28 | -12.450 | -74.702 | 6 | 2 | -0.342 | -17.387 | -11.654 | 0.085 |
| 29 | -11.926 | -71.558 | 6 | 2 | -0.327 | -17.304 | -12.008 | 0.049 |
| 30 | -12.210 | -73.260 | 6 | 2 | -0.337 | -17.330 | -12.177 | 0.052 |
| 31 | -12.225 | -73.348 | 6 | 2 | -0.343 | -17.391 | -12.771 | 0.033 |
| 32 | -12.731 | -76.384 | 6 | 2 | -0.366 | -17.357 | -12.897 | 0.045 |
| 33 | -13.852 | -83.111 | 6 | 2 | -0.416 | -17.294 | -13.522 | 0.073 |
| 34 | -15.858 | -95.147 | 6 | 2 | -0.487 | -17.521 | -13.945 | 0.222 |
| 35 | -14.569 | -87.414 | 6 | 2 | -0.464 | -17.382 | -14.420 | 0.063 |
| 36 | -16.942 | -101.655 | 6 | 2 | -0.555 | -17.311 | -14.691 | 0.412 |
| 37 | -17.713 | -106.278 | 6 | 2 | -0.607 | -17.370 | -15.254 | 0.616 |
| 38 | -17.399 | -104.395 | 6 | 2 | -0.624 | -17.349 | -15.860 | 0.516 |
| 39 | -17.365 | -104.189 | 6 | 2 | -0.639 | -17.365 | -17.365 | 0.586 |


## C1 — `jack`

| K | R_per_year_mean | R_total_build | years | years_positive | t_yearly | null_mean | null_p95 | null_p |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 6.249 | 37.492 | 6 | 3 | 0.362 | -8.094 | 12.018 | 0.137 |
| 2 | 6.319 | 37.913 | 6 | 2 | 0.457 | -8.214 | 6.464 | 0.053 |
| 3 | 13.932 | 83.591 | 6 | 3 | 0.961 | -8.020 | 3.253 | 0.001 |
| 4 | 9.547 | 57.282 | 6 | 2 | 0.686 | -8.117 | 1.875 | 0.000 |
| 5 | 2.961 | 17.768 | 6 | 2 | 0.219 | -8.097 | 0.660 | 0.016 |
| 6 | -2.596 | -15.578 | 6 | 2 | -0.186 | -8.012 | -0.042 | 0.155 |
| 7 | -3.191 | -19.146 | 6 | 2 | -0.265 | -7.971 | -0.426 | 0.160 |
| 8 | -4.175 | -25.051 | 6 | 2 | -0.365 | -7.906 | -1.018 | 0.195 |
| 9 | -4.768 | -28.609 | 6 | 2 | -0.438 | -7.963 | -1.571 | 0.206 |
| 10 | -3.623 | -21.740 | 6 | 2 | -0.323 | -7.970 | -1.631 | 0.131 |
| 11 | -2.028 | -12.169 | 6 | 2 | -0.182 | -7.910 | -2.291 | 0.042 |
| 12 | -2.786 | -16.713 | 6 | 2 | -0.255 | -8.065 | -2.662 | 0.052 |
| 13 | -3.236 | -19.416 | 6 | 2 | -0.313 | -7.994 | -2.888 | 0.065 |
| 14 | -3.351 | -20.106 | 6 | 2 | -0.339 | -8.159 | -3.049 | 0.059 |
| 15 | -2.650 | -15.900 | 6 | 2 | -0.277 | -7.960 | -3.375 | 0.031 |
| 16 | -2.626 | -15.758 | 6 | 2 | -0.264 | -7.877 | -3.756 | 0.019 |
| 17 | -2.566 | -15.398 | 6 | 2 | -0.261 | -7.867 | -3.926 | 0.011 |
| 18 | -3.253 | -19.517 | 6 | 2 | -0.339 | -8.052 | -4.092 | 0.024 |
| 19 | -3.385 | -20.309 | 6 | 2 | -0.355 | -7.961 | -4.291 | 0.020 |
| 20 | -3.670 | -22.017 | 6 | 2 | -0.389 | -8.077 | -4.708 | 0.018 |
| 21 | -2.976 | -17.855 | 6 | 2 | -0.311 | -8.030 | -4.803 | 0.007 |
| 22 | -3.277 | -19.664 | 6 | 2 | -0.327 | -8.070 | -4.918 | 0.011 |
| 23 | -3.378 | -20.265 | 6 | 2 | -0.343 | -8.023 | -4.892 | 0.002 |
| 24 | -3.389 | -20.335 | 6 | 2 | -0.350 | -8.087 | -5.331 | 0.002 |
| 25 | -3.258 | -19.547 | 6 | 2 | -0.335 | -8.042 | -5.287 | 0.001 |
| 26 | -2.863 | -17.176 | 6 | 2 | -0.285 | -8.005 | -5.510 | 0.001 |
| 27 | -2.875 | -17.249 | 6 | 2 | -0.287 | -7.978 | -5.600 | 0.000 |
| 28 | -2.647 | -15.883 | 6 | 2 | -0.259 | -8.040 | -5.802 | 0.000 |
| 29 | -2.532 | -15.192 | 6 | 2 | -0.242 | -8.013 | -5.933 | 0.000 |
| 30 | -2.466 | -14.796 | 6 | 2 | -0.239 | -8.024 | -6.093 | 0.000 |
| 31 | -1.943 | -11.657 | 6 | 2 | -0.185 | -8.022 | -6.241 | 0.000 |
| 32 | -1.986 | -11.917 | 6 | 2 | -0.188 | -8.043 | -6.297 | 0.000 |
| 33 | -2.382 | -14.294 | 6 | 2 | -0.228 | -8.028 | -6.441 | 0.000 |
| 34 | -3.549 | -21.295 | 6 | 2 | -0.354 | -8.060 | -6.676 | 0.000 |
| 35 | -4.088 | -24.528 | 6 | 2 | -0.412 | -8.027 | -6.819 | 0.000 |
| 36 | -4.732 | -28.391 | 6 | 2 | -0.492 | -8.014 | -6.966 | 0.000 |
| 37 | -5.850 | -35.098 | 6 | 2 | -0.595 | -8.015 | -7.104 | 0.000 |
| 38 | -6.725 | -40.353 | 6 | 2 | -0.703 | -8.020 | -7.395 | 0.001 |
| 39 | -8.021 | -48.125 | 6 | 2 | -0.851 | -8.021 | -8.021 | 0.376 |


## C1 — `textbook`

| K | R_per_year_mean | R_total_build | years | years_positive | t_yearly | null_mean | null_p95 | null_p |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | -5.005 | -30.030 | 6 | 1 | -0.283 | -7.745 | 9.282 | 0.460 |
| 2 | -11.800 | -70.803 | 6 | 2 | -1.016 | -8.003 | 4.650 | 0.675 |
| 3 | -4.451 | -26.708 | 6 | 2 | -0.431 | -8.069 | 2.691 | 0.313 |
| 4 | -5.388 | -32.328 | 6 | 2 | -0.665 | -8.164 | 0.700 | 0.339 |
| 5 | -6.605 | -39.629 | 6 | 2 | -0.731 | -8.141 | -0.186 | 0.401 |
| 6 | -6.918 | -41.505 | 6 | 2 | -0.903 | -8.088 | -0.575 | 0.418 |
| 7 | -4.852 | -29.110 | 6 | 2 | -0.581 | -8.002 | -0.899 | 0.219 |
| 8 | -3.954 | -23.726 | 6 | 2 | -0.434 | -7.950 | -1.726 | 0.150 |
| 9 | -2.355 | -14.128 | 6 | 2 | -0.259 | -8.057 | -1.962 | 0.062 |
| 10 | -1.619 | -9.714 | 6 | 2 | -0.174 | -8.099 | -2.471 | 0.031 |
| 11 | -2.135 | -12.810 | 6 | 2 | -0.242 | -8.064 | -3.039 | 0.026 |
| 12 | -2.334 | -14.005 | 6 | 2 | -0.272 | -8.191 | -3.268 | 0.025 |
| 13 | -2.169 | -13.015 | 6 | 2 | -0.228 | -8.021 | -3.438 | 0.013 |
| 14 | -1.935 | -11.613 | 6 | 2 | -0.209 | -8.226 | -3.891 | 0.008 |
| 15 | -1.641 | -9.848 | 6 | 2 | -0.172 | -8.050 | -3.702 | 0.005 |
| 16 | -1.681 | -10.088 | 6 | 2 | -0.188 | -7.987 | -4.085 | 0.003 |
| 17 | -1.816 | -10.898 | 6 | 2 | -0.212 | -7.951 | -4.356 | 0.001 |
| 18 | -1.213 | -7.281 | 6 | 2 | -0.138 | -8.125 | -4.535 | 0.001 |
| 19 | -0.588 | -3.526 | 6 | 2 | -0.065 | -8.017 | -4.741 | 0.001 |
| 20 | -0.646 | -3.875 | 6 | 2 | -0.073 | -8.169 | -5.041 | 0.000 |
| 21 | -0.910 | -5.458 | 6 | 2 | -0.100 | -8.040 | -4.990 | 0.000 |
| 22 | -1.374 | -8.247 | 6 | 2 | -0.157 | -8.126 | -5.066 | 0.000 |
| 23 | -0.809 | -4.851 | 6 | 2 | -0.091 | -8.044 | -5.176 | 0.000 |
| 24 | -0.679 | -4.072 | 6 | 2 | -0.075 | -8.128 | -5.661 | 0.000 |
| 25 | -1.612 | -9.674 | 6 | 2 | -0.186 | -8.058 | -5.648 | 0.000 |
| 26 | -2.422 | -14.532 | 6 | 2 | -0.283 | -8.111 | -5.648 | 0.000 |
| 27 | -2.379 | -14.273 | 6 | 2 | -0.275 | -8.013 | -5.858 | 0.000 |
| 28 | -2.020 | -12.121 | 6 | 2 | -0.234 | -8.114 | -6.141 | 0.000 |
| 29 | -1.846 | -11.077 | 6 | 2 | -0.211 | -8.045 | -6.165 | 0.000 |
| 30 | -2.146 | -12.879 | 6 | 2 | -0.252 | -8.082 | -6.331 | 0.000 |
| 31 | -2.406 | -14.435 | 6 | 2 | -0.290 | -8.078 | -6.457 | 0.000 |
| 32 | -2.270 | -13.621 | 6 | 2 | -0.267 | -8.094 | -6.553 | 0.000 |
| 33 | -2.193 | -13.159 | 6 | 2 | -0.257 | -8.095 | -6.677 | 0.000 |
| 34 | -2.659 | -15.951 | 6 | 2 | -0.310 | -8.109 | -6.727 | 0.000 |
| 35 | -3.380 | -20.281 | 6 | 2 | -0.386 | -8.112 | -7.012 | 0.000 |
| 36 | -4.432 | -26.590 | 6 | 2 | -0.501 | -8.076 | -7.135 | 0.000 |
| 37 | -5.423 | -32.539 | 6 | 2 | -0.634 | -8.060 | -7.200 | 0.000 |
| 38 | -6.608 | -39.646 | 6 | 2 | -0.797 | -8.092 | -7.494 | 0.000 |
| 39 | -8.082 | -48.495 | 6 | 2 | -0.940 | -8.082 | -8.082 | 0.936 |


## BASELINE — `flip_only`

| K | R_per_year_mean | R_total_build | years | years_positive | t_yearly | null_mean | null_p95 | null_p |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | -6.585 | -39.510 | 6 | 3 | -0.194 | -20.417 | 16.303 | 0.286 |
| 2 | 5.125 | 30.749 | 6 | 3 | 0.142 | -18.778 | 7.022 | 0.058 |
| 3 | 1.237 | 7.419 | 6 | 4 | 0.032 | -17.901 | 1.472 | 0.052 |
| 4 | -9.597 | -57.583 | 6 | 3 | -0.249 | -18.324 | -2.478 | 0.193 |
| 5 | -12.947 | -77.682 | 6 | 3 | -0.327 | -18.459 | -2.911 | 0.257 |
| 6 | -13.293 | -79.760 | 6 | 3 | -0.339 | -18.329 | -6.379 | 0.246 |
| 7 | -14.306 | -85.835 | 6 | 3 | -0.395 | -18.472 | -7.253 | 0.270 |
| 8 | -15.567 | -93.404 | 6 | 3 | -0.424 | -18.411 | -9.403 | 0.305 |
| 9 | -9.406 | -56.437 | 6 | 3 | -0.267 | -18.353 | -9.828 | 0.038 |
| 10 | -10.086 | -60.516 | 6 | 3 | -0.297 | -18.280 | -11.154 | 0.033 |
| 11 | -12.560 | -75.357 | 6 | 3 | -0.389 | -18.270 | -12.417 | 0.056 |
| 12 | -13.644 | -81.861 | 6 | 3 | -0.437 | -18.069 | -12.984 | 0.072 |
| 13 | -14.456 | -86.733 | 6 | 3 | -0.476 | -18.144 | -14.270 | 0.060 |
| 14 | -16.488 | -98.927 | 6 | 3 | -0.563 | -18.168 | -15.599 | 0.141 |
| 15 | -18.193 | -109.156 | 6 | 2 | -0.633 | -18.193 | -18.193 | 0.619 |


## BASELINE — `jack`

| K | R_per_year_mean | R_total_build | years | years_positive | t_yearly | null_mean | null_p95 | null_p |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 6.913 | 41.478 | 6 | 3 | 0.397 | -9.313 | 10.364 | 0.097 |
| 2 | 0.088 | 0.526 | 6 | 3 | 0.007 | -9.117 | 4.311 | 0.142 |
| 3 | -0.437 | -2.625 | 6 | 3 | -0.035 | -9.615 | 2.039 | 0.081 |
| 4 | 0.440 | 2.638 | 6 | 3 | 0.037 | -9.587 | -0.998 | 0.028 |
| 5 | -0.747 | -4.481 | 6 | 3 | -0.078 | -9.650 | -2.122 | 0.027 |
| 6 | -0.901 | -5.406 | 6 | 2 | -0.087 | -9.432 | -3.346 | 0.013 |
| 7 | -4.057 | -24.344 | 6 | 2 | -0.449 | -9.562 | -4.001 | 0.053 |
| 8 | -0.421 | -2.525 | 6 | 3 | -0.047 | -9.594 | -4.795 | 0.001 |
| 9 | 0.368 | 2.208 | 6 | 2 | 0.041 | -9.449 | -5.185 | 0.000 |
| 10 | -2.111 | -12.665 | 6 | 2 | -0.222 | -9.480 | -5.656 | 0.001 |
| 11 | -3.985 | -23.909 | 6 | 2 | -0.452 | -9.381 | -5.976 | 0.003 |
| 12 | -4.869 | -29.217 | 6 | 2 | -0.544 | -9.363 | -6.613 | 0.002 |
| 13 | -5.503 | -33.020 | 6 | 2 | -0.607 | -9.455 | -7.280 | 0.003 |
| 14 | -7.762 | -46.575 | 6 | 2 | -0.854 | -9.458 | -7.902 | 0.039 |
| 15 | -9.440 | -56.642 | 6 | 2 | -1.031 | -9.440 | -9.440 | 0.895 |


## BASELINE — `textbook`

| K | R_per_year_mean | R_total_build | years | years_positive | t_yearly | null_mean | null_p95 | null_p |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | -0.297 | -1.782 | 6 | 3 | -0.027 | -14.844 | -0.447 | 0.048 |
| 2 | 0.258 | 1.550 | 6 | 3 | 0.022 | -15.465 | -5.339 | 0.001 |
| 3 | -1.864 | -11.184 | 6 | 3 | -0.151 | -15.165 | -6.862 | 0.003 |
| 4 | -5.640 | -33.838 | 6 | 2 | -0.523 | -15.361 | -8.560 | 0.005 |
| 5 | -5.111 | -30.664 | 6 | 2 | -0.481 | -15.322 | -9.570 | 0.002 |
| 6 | -2.745 | -16.469 | 6 | 3 | -0.271 | -15.329 | -10.163 | 0.000 |
| 7 | -4.680 | -28.080 | 6 | 2 | -0.487 | -15.330 | -10.987 | 0.000 |
| 8 | -3.959 | -23.752 | 6 | 3 | -0.409 | -15.365 | -11.280 | 0.000 |
| 9 | -6.177 | -37.064 | 6 | 1 | -0.729 | -15.389 | -11.804 | 0.000 |
| 10 | -8.890 | -53.340 | 6 | 1 | -1.045 | -15.317 | -12.229 | 0.000 |
| 11 | -10.502 | -63.009 | 6 | 1 | -1.257 | -15.211 | -12.662 | 0.000 |
| 12 | -12.092 | -72.551 | 6 | 1 | -1.390 | -15.304 | -13.072 | 0.007 |
| 13 | -13.433 | -80.600 | 6 | 1 | -1.667 | -15.373 | -13.764 | 0.025 |
| 14 | -14.986 | -89.914 | 6 | 1 | -1.938 | -15.350 | -14.242 | 0.280 |
| 15 | -15.321 | -91.924 | 6 | 1 | -2.114 | -15.321 | -15.321 | 0.994 |


---

## For Jack to pick from

**At most 3 C1 and 3 baselines, for a stated reason. I am not picking.** The tables are sorted by net R per year, as asked. Four things in them bear on a choice:


1. **`sign_agree`** — whether all three settings agree. This is the strongest single guard against fitting, and it was not reported at all in the superseded version.

2. **`t_block_boot` beside `t_yearly`** — the bootstrap t has real power (82% at 0.10 R where the yearly t had 14.6%) but rests on a serial-dependence assumption my 0a simulation under-tests. Agreement between the two is worth more than either alone.

3. **`trades_per_year` and `mean_bars`** — a candidate with 14 trades a year cannot be measured whatever its R.

4. **`null_p`**, now computed on a matched window, which it was not before.


## Provenance

- `results/nnfx/stage1r2_c1_flip_only_yearly.csv` — 1,931 rows, md5 `443aa93939f8`
- `results/nnfx/stage1r2_c1_flip_only_summary.csv` — 117 rows, md5 `0d58c3b336ad`
- `results/nnfx/stage1r2_c1_flip_only_nulls.csv` — 46,800 rows, md5 `f0bc6e90840b`
- `results/nnfx/stage1r2_c1_jack_yearly.csv` — 1,931 rows, md5 `f41bd8e0d9ce`
- `results/nnfx/stage1r2_c1_jack_summary.csv` — 117 rows, md5 `7c44dfda7575`
- `results/nnfx/stage1r2_c1_jack_nulls.csv` — 46,800 rows, md5 `8b070f31f71d`
- `results/nnfx/stage1r2_c1_textbook_yearly.csv` — 1,931 rows, md5 `c61653ad0360`
- `results/nnfx/stage1r2_c1_textbook_summary.csv` — 117 rows, md5 `12239475e3dd`
- `results/nnfx/stage1r2_c1_textbook_nulls.csv` — 46,800 rows, md5 `e08edf180e24`
- `results/nnfx/stage1r2_base_flip_only_yearly.csv` — 760 rows, md5 `352a32bbcd37`
- `results/nnfx/stage1r2_base_flip_only_summary.csv` — 45 rows, md5 `ed0cde23f353`
- `results/nnfx/stage1r2_base_flip_only_nulls.csv` — 18,000 rows, md5 `a21dbba1eae4`
- `results/nnfx/stage1r2_base_jack_yearly.csv` — 760 rows, md5 `2374368c8a71`
- `results/nnfx/stage1r2_base_jack_summary.csv` — 45 rows, md5 `8df7b22a3695`
- `results/nnfx/stage1r2_base_jack_nulls.csv` — 18,000 rows, md5 `92e362cd6349`
- `results/nnfx/stage1r2_base_textbook_yearly.csv` — 754 rows, md5 `57abdae108e9`
- `results/nnfx/stage1r2_base_textbook_summary.csv` — 45 rows, md5 `e2cdc18a931c`
- `results/nnfx/stage1r2_base_textbook_nulls.csv` — 18,000 rows, md5 `148e18e3052c`
- `results/nnfx/stage1r2_ambiguity_delta.csv` — 24 rows
- `results/nnfx/power_test_bootstrap.csv` — 6 rows
- `results/nnfx/condition4_zero_edge.csv` — 486 rows
- `results/nnfx/CANDIDATE_LEDGER.csv` — 191 rows
