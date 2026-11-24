# STAGE 1 R2 — ONE PIECE ALONE, THREE RISK PLANS, ELEVEN UNSEEN YEARS

> ## CORRECTION, 24 Nov 16:40 ET — the per-trade and count columns in this file are wrong by a factor of two
>
> Found while testing stage 2's trade-thinning sweep, and it is my fault.
>
> `plan=2` splits every position into **two legs** — leg1 banks at the first
> target, leg2 runs on the trail — and `l2engine.trade_frame` returns **one row
> per leg**. `nnfx1._yearly` counted those rows as `n_entered`. Verified on
> EURUSD and GBPJPY across all three plans: rows are exactly 2× distinct
> entries, every time, min and max legs per entry both 2.
>
> **What is wrong in the tables below:**
>
> | column | this file says | truth |
> |---|---|---|
> | `n_entered`, `n_touching`, `trades_per_year` | 2× too large | halve it |
> | `R_net_per_trade`, `R_gross_per_trade`, `cost_per_trade` | half the truth | double it |
>
> **What is NOT wrong, and this is most of the file.** Each leg carries half the
> units against the full risk, so the two legs' R sums to the position's R (a
> full stop-out is −0.5 + −0.5 = −1.0 R) and each leg is charged half the
> spread, summing to the whole. So **every total and every test statistic is
> unaffected**: `R_net_build`, `R_gross_build`, `R_net_per_year`,
> `worst_dip_R`, `t_yearly`, `t_block_boot`, `null_p`, the luck floors, the
> selection test, condition 4's pass, and the conclusion that Jack's plan wins
> the two-plan comparison. That is also exactly why it was invisible for a day.
>
> The one quoted number that needs restating: **condition 4's charged cost of
> +0.01752 R is per LEG; per trade it is +0.03504.** The zero-edge test itself
> still passes, because the null was computed on the same per-leg basis as the
> charge it is compared against.
>
> Guard 32 checked that the two conventions were *named* apart and never that
> the count counted the right thing. **Preflight guard 33** now checks the
> arithmetic on a live candidate instead of the spelling. Fixed in
> `nnfx1.entry_frame` / `n_entries`; stage 2 is built on the fixed version. This
> file is not regenerated — the correction is stated here instead, because the
> totals it turns on are unchanged.



Generated 2026-11-24 13:55 by `code/nnfx1.py`. HANDOFF 0m.


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

Empirical yearly-t floors **from the random-entry null**: alone **1.264**, best-of-39 **2.915**. The analytic equivalents on 11 yearly observations are 1.812 and 3.973 — the empirical ones are lower because the analytic formula assumes a **zero-mean** null while the real null also pays costs, so it is centred below zero.

| indicator | setting | distinct_setting | n_entered | trades_per_year | mean_bars | R_gross_per_trade | R_net_per_trade | cost_per_trade | R_net_per_year | years | years_positive | worst_year | worst_dip_R | t_yearly | t_block_boot | null_p | clears_alone_emp | clears_family_emp |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| j_tpo_signals | double | 1 | 2026.0000 | 184.1818 | 78.5084 | 0.2203 | 0.2029 | 0.0175 | 37.3614 | 11 | 6 | -181.2961 | 426.9056 | 0.7700 | 0.5881 | 0.0200 | 0 | 0 |
| halftrend_signals | half | 1 | 1196.0000 | 108.7273 | 130.6254 | 0.3242 | 0.3073 | 0.0169 | 33.4140 | 11 | 5 | -221.4382 | 521.0217 | 0.5150 | 0.5703 | 0.0200 | 0 | 0 |
| laguerre_filter_signals | double | 1 | 2156.0000 | 196.0000 | 72.0325 | 0.1799 | 0.1624 | 0.0176 | 31.8276 | 11 | 7 | -263.7627 | 492.6681 | 0.5101 | 0.5036 | 0.0325 | 0 | 0 |
| halftrend_signals | default | 1 | 722.0000 | 65.6364 | 214.1274 | 0.4585 | 0.4415 | 0.0170 | 28.9810 | 11 | 7 | -242.4768 | 648.9191 | 0.5480 | 0.5301 | 0.0425 | 0 | 0 |
| price_momentum_oscillator_signals | double | 1 | 2560.0000 | 232.7273 | 61.1508 | 0.1375 | 0.1195 | 0.0180 | 27.8213 | 11 | 5 | -240.1339 | 620.9173 | 0.4443 | 0.4433 | 0.0450 | 0 | 0 |
| dpo_signals | double | 1 | 4882.0000 | 443.8182 | 31.1213 | 0.0747 | 0.0568 | 0.0179 | 25.2064 | 11 | 4 | -253.5280 | 644.1242 | 0.4274 | 0.4055 | 0.0400 | 0 | 0 |
| ichimoku_signals | half | 1 | 1408.0000 | 128.0000 | 115.2912 | 0.1995 | 0.1819 | 0.0176 | 23.2824 | 11 | 6 | -148.3332 | 342.7233 | 0.6188 | 0.4613 | 0.0900 | 0 | 0 |
| ichimoku_signals | double | 1 | 1732.0000 | 157.4545 | 93.2771 | 0.1515 | 0.1342 | 0.0172 | 21.1364 | 11 | 6 | -260.7740 | 635.6459 | 0.3468 | 0.3317 | 0.1050 | 0 | 0 |
| trend_direction_force_index_signals | double | 1 | 1754.0000 | 159.4545 | 89.2725 | 0.1495 | 0.1320 | 0.0175 | 21.0444 | 11 | 4 | -259.0043 | 642.7001 | 0.3322 | 0.3317 | 0.0675 | 0 | 0 |
| dspo_signals | double | 1 | 2480.0000 | 225.4545 | 63.6419 | 0.0970 | 0.0791 | 0.0179 | 17.8363 | 11 | 6 | -250.7944 | 576.1493 | 0.3029 | 0.2866 | 0.0875 | 0 | 0 |
| halftrend_signals | double | 1 | 374.0000 | 34.0000 | 384.4866 | 0.4330 | 0.4165 | 0.0165 | 14.1626 | 11 | 6 | -128.1245 | 294.1970 | 0.5236 | 0.3036 | 0.3250 | 0 | 0 |
| ichimoku_signals | default | 1 | 1310.0000 | 119.0909 | 123.7176 | 0.1351 | 0.1174 | 0.0176 | 13.9838 | 11 | 6 | -169.9437 | 328.4782 | 0.5127 | 0.2939 | 0.2125 | 0 | 0 |
| adx_dmi_signals | double | 1 | 118.0000 | 10.7273 | 1419.4237 | 1.3020 | 1.2877 | 0.0143 | 13.8139 | 11 | 5 | -48.7463 | 146.4821 | 0.8278 | 0.7485 | 0.0050 | 0 | 0 |
| schaff_trend_cycle_signals | default | 1 | 5648.0000 | 513.4545 | 15.4483 | 0.0368 | 0.0194 | 0.0174 | 9.9791 | 11 | 6 | -56.7577 | 254.8840 | 0.7911 | 0.3066 | 0.0875 | 0 | 0 |
| schaff_trend_cycle_signals | half | 1 | 5926.0000 | 538.7273 | 13.4587 | 0.0359 | 0.0184 | 0.0175 | 9.9226 | 11 | 6 | -73.3423 | 173.2314 | 0.6152 | 0.3677 | 0.0900 | 0 | 0 |
| dpo_signals | default | 1 | 7800.0000 | 709.0909 | 20.2367 | 0.0305 | 0.0125 | 0.0180 | 8.8651 | 11 | 7 | -321.0110 | 604.8072 | 0.1374 | 0.1370 | 0.1200 | 0 | 0 |
| mama_fama_signals | double | 1 | 3232.0000 | 293.8182 | 48.2710 | 0.0458 | 0.0280 | 0.0177 | 8.2361 | 11 | 6 | -300.5766 | 637.4202 | 0.1292 | 0.1347 | 0.2050 | 0 | 0 |
| volatility_quality_signals | default | 1 | 7576.0000 | 688.7273 | 21.0750 | 0.0280 | 0.0108 | 0.0172 | 7.4386 | 11 | 6 | -174.1691 | 447.8817 | 0.2153 | 0.1603 | 0.1350 | 0 | 0 |
| donchian_breakout_signals | double | 1 | 1934.0000 | 175.8182 | 83.8097 | 0.0594 | 0.0420 | 0.0175 | 7.3761 | 11 | 5 | -249.3667 | 570.5319 | 0.1144 | 0.1169 | 0.2625 | 0 | 0 |
| supertrend_signals | double | 1 | 3968.0000 | 360.7273 | 40.0413 | 0.0354 | 0.0183 | 0.0171 | 6.6128 | 11 | 5 | -163.4791 | 452.0788 | 0.1914 | 0.1301 | 0.2675 | 0 | 0 |
| supertrend_signals | default | 1 | 4030.0000 | 366.3636 | 39.6333 | 0.0273 | 0.0101 | 0.0172 | 3.6965 | 11 | 5 | -215.7933 | 529.9627 | 0.0897 | 0.0687 | 0.2600 | 0 | 0 |
| kuskus_starlight_signals | double | 1 | 6276.0000 | 570.5455 | 25.0739 | 0.0186 | 0.0013 | 0.0173 | 0.7559 | 11 | 5 | -285.9874 | 616.5298 | 0.0131 | 0.0128 | 0.2350 | 0 | 0 |
| price_momentum_oscillator_signals | default | 1 | 3838.0000 | 348.9091 | 41.2376 | 0.0197 | 0.0021 | 0.0176 | 0.7382 | 11 | 6 | -264.8410 | 672.2571 | 0.0120 | 0.0117 | 0.3825 | 0 | 0 |
| glitch_index_signals | double | 1 | 2612.0000 | 237.4545 | 60.9158 | 0.0193 | 0.0018 | 0.0175 | 0.4366 | 11 | 5 | -320.1570 | 655.9194 | 0.0072 | 0.0069 | 0.4475 | 0 | 0 |
| chandelier_exit_signals | half | 1 | 4728.0000 | 429.8182 | 33.7458 | 0.0164 | -0.0007 | 0.0171 | -0.3192 | 11 | 5 | -184.4486 | 522.6520 | -0.0082 | -0.0060 | 0.3425 | 0 | 0 |
| aroon_signals | half | 1 | 11924.0000 | 1084.0000 | 13.3796 | 0.0168 | -0.0008 | 0.0176 | -0.8400 | 11 | 5 | -168.3961 | 370.7464 | -0.0240 | -0.0176 | 0.1900 | 0 | 0 |
| ssl_channel_signals | default | 1 | 12948.0000 | 1177.0909 | 12.3071 | 0.0166 | -0.0008 | 0.0174 | -0.9570 | 11 | 6 | -92.7909 | 309.0733 | -0.0428 | -0.0213 | 0.1525 | 0 | 0 |
| laguerre_filter_signals | default | 1 | 4612.0000 | 419.2727 | 34.3660 | 0.0149 | -0.0026 | 0.0175 | -1.0889 | 11 | 4 | -216.9874 | 664.9012 | -0.0205 | -0.0182 | 0.3875 | 0 | 0 |
| ehlers_reverse_ema_signals | double | 1 | 6328.0000 | 575.2727 | 25.3110 | 0.0146 | -0.0032 | 0.0178 | -1.8467 | 11 | 6 | -249.5605 | 643.9392 | -0.0309 | -0.0293 | 0.3500 | 0 | 0 |
| kase_peak_oscillator_signals | double | 1 | 6300.0000 | 572.7273 | 25.1702 | 0.0135 | -0.0038 | 0.0173 | -2.2028 | 11 | 4 | -195.3864 | 656.2831 | -0.0455 | -0.0371 | 0.3600 | 0 | 0 |
| chandelier_exit_signals | default | 1 | 5154.0000 | 468.5455 | 30.8421 | 0.0114 | -0.0051 | 0.0165 | -2.3941 | 11 | 4 | -131.4433 | 428.4055 | -0.0781 | -0.0484 | 0.3750 | 0 | 0 |
| ssl_channel_signals | half | 1 | 18122.0000 | 1647.4545 | 8.7916 | 0.0156 | -0.0017 | 0.0172 | -2.7233 | 11 | 4 | -73.3593 | 342.2013 | -0.1616 | -0.0674 | 0.0900 | 0 | 0 |
| parabolic_sar_signals | default | 1 | 14824.0000 | 1347.6364 | 10.7567 | 0.0149 | -0.0026 | 0.0175 | -3.4808 | 11 | 5 | -74.6513 | 325.0159 | -0.1880 | -0.0866 | 0.1550 | 0 | 0 |
| parabolic_sar_signals | half | 1 | 21478.0000 | 1952.5455 | 7.4215 | 0.0156 | -0.0019 | 0.0175 | -3.6383 | 11 | 5 | -71.1291 | 319.3068 | -0.2202 | -0.0931 | 0.0700 | 0 | 0 |
| trend_direction_force_index_signals | default | 1 | 3644.0000 | 331.2727 | 43.3814 | 0.0064 | -0.0115 | 0.0179 | -3.7992 | 11 | 5 | -335.3230 | 736.1326 | -0.0584 | -0.0615 | 0.4175 | 0 | 0 |
| mama_fama_signals | default | 1 | 6794.0000 | 617.6364 | 23.2370 | 0.0105 | -0.0073 | 0.0178 | -4.5171 | 11 | 5 | -167.8149 | 498.4503 | -0.1215 | -0.0820 | 0.3900 | 0 | 0 |
| dpo_signals | half | 1 | 11108.0000 | 1009.8182 | 14.2778 | 0.0134 | -0.0046 | 0.0180 | -4.6406 | 11 | 4 | -204.6955 | 740.5175 | -0.0967 | -0.0739 | 0.2575 | 0 | 0 |
| donchian_breakout_signals | default | 1 | 3740.0000 | 340.0000 | 42.9706 | 0.0030 | -0.0142 | 0.0172 | -4.8311 | 11 | 4 | -252.5918 | 734.7141 | -0.0900 | -0.0788 | 0.4575 | 0 | 0 |
| dspo_signals | half | 1 | 9556.0000 | 868.7273 | 16.6756 | 0.0117 | -0.0060 | 0.0177 | -5.1719 | 11 | 6 | -154.0119 | 434.4879 | -0.1405 | -0.0977 | 0.3050 | 0 | 0 |
| fx_sniper_ergodic_cci_signals | double | 1 | 18036.0000 | 1639.6364 | 8.7701 | 0.0146 | -0.0032 | 0.0178 | -5.2409 | 11 | 5 | -108.9032 | 401.4048 | -0.2163 | -0.1535 | 0.1325 | 0 | 0 |
| donchian_breakout_signals | half | 1 | 6562.0000 | 596.5455 | 24.3630 | 0.0079 | -0.0094 | 0.0173 | -5.6114 | 11 | 6 | -157.9001 | 521.4302 | -0.1569 | -0.1097 | 0.3775 | 0 | 0 |
| bears_bulls_impulse_signals | double | 1 | 7600.0000 | 690.9091 | 20.9400 | 0.0089 | -0.0086 | 0.0174 | -5.9115 | 11 | 5 | -227.5678 | 624.7539 | -0.1200 | -0.1017 | 0.3775 | 0 | 0 |
| polychromatic_momentum_signals | default | 1 | 6422.0000 | 583.8182 | 24.7468 | 0.0070 | -0.0110 | 0.0180 | -6.4260 | 11 | 4 | -165.8008 | 617.8753 | -0.1558 | -0.1121 | 0.4400 | 0 | 0 |
| mama_fama_signals | half | 1 | 14884.0000 | 1353.0909 | 10.6826 | 0.0128 | -0.0048 | 0.0176 | -6.4498 | 11 | 5 | -79.9927 | 328.7603 | -0.3156 | -0.1522 | 0.2050 | 0 | 0 |
| trend_direction_force_index_signals | half | 1 | 7964.0000 | 724.0000 | 19.9694 | 0.0090 | -0.0090 | 0.0179 | -6.4972 | 11 | 6 | -168.4463 | 463.8925 | -0.1655 | -0.1205 | 0.3425 | 0 | 0 |
| linreg_slope_signals | double | 1 | 4074.0000 | 370.3636 | 39.4016 | -0.0009 | -0.0185 | 0.0175 | -6.8332 | 11 | 4 | -210.8460 | 729.5965 | -0.1197 | -0.1126 | 0.5150 | 0 | 0 |
| fx_sniper_ergodic_cci_signals | default | 1 | 21636.0000 | 1966.9091 | 7.3467 | 0.0141 | -0.0035 | 0.0175 | -6.8367 | 11 | 4 | -140.3007 | 315.6835 | -0.3269 | -0.2043 | 0.0625 | 0 | 0 |
| polychromatic_momentum_signals | double | 1 | 3220.0000 | 292.7273 | 49.1043 | -0.0064 | -0.0240 | 0.0175 | -7.0156 | 11 | 6 | -313.5484 | 618.7955 | -0.1131 | -0.1142 | 0.5000 | 0 | 0 |
| volatility_quality_signals | half | 1 | 18822.0000 | 1711.0909 | 8.4664 | 0.0130 | -0.0041 | 0.0172 | -7.0492 | 11 | 3 | -69.6300 | 258.9170 | -0.5967 | -0.1890 | 0.1025 | 0 | 0 |
| chandelier_exit_signals | double | 1 | 7160.0000 | 650.9091 | 22.0846 | 0.0049 | -0.0111 | 0.0161 | -7.2516 | 11 | 5 | -112.9594 | 430.0736 | -0.2717 | -0.1444 | 0.4425 | 0 | 0 |
| kase_peak_oscillator_signals | half | 1 | 12186.0000 | 1107.8182 | 12.9751 | 0.0106 | -0.0066 | 0.0172 | -7.2665 | 11 | 4 | -101.4239 | 324.9859 | -0.3469 | -0.1486 | 0.2225 | 0 | 0 |
| ssl_channel_signals | double | 1 | 9140.0000 | 830.9091 | 17.3851 | 0.0089 | -0.0088 | 0.0177 | -7.3400 | 11 | 6 | -162.0342 | 459.8512 | -0.2175 | -0.1416 | 0.3500 | 0 | 0 |
| kalman_filter_signals | half | 1 | 7352.0000 | 668.3636 | 21.7002 | 0.0065 | -0.0114 | 0.0179 | -7.6398 | 11 | 6 | -183.7749 | 528.4397 | -0.2040 | -0.1377 | 0.4400 | 0 | 0 |
| hieken_ashi_smoothed_signals | half | 1 | 11606.0000 | 1055.0909 | 13.5149 | 0.0102 | -0.0075 | 0.0176 | -7.8692 | 11 | 5 | -170.8366 | 391.3464 | -0.2483 | -0.1673 | 0.3350 | 0 | 0 |
| ehlers_reverse_ema_signals | default | 1 | 8438.0000 | 767.0909 | 18.8943 | 0.0075 | -0.0103 | 0.0178 | -7.9115 | 11 | 6 | -155.7116 | 465.6795 | -0.2146 | -0.1444 | 0.3925 | 0 | 0 |
| glitch_index_signals | half | 1 | 4858.0000 | 441.6364 | 32.9123 | -0.0006 | -0.0180 | 0.0174 | -7.9365 | 11 | 5 | -266.3563 | 712.4553 | -0.1512 | -0.1322 | 0.5200 | 0 | 0 |
| didi_index_signals | half | 1 | 11050.0000 | 1004.5455 | 14.3810 | 0.0089 | -0.0088 | 0.0177 | -8.8040 | 11 | 5 | -121.6222 | 375.3883 | -0.2881 | -0.1748 | 0.3150 | 0 | 0 |
| kase_peak_oscillator_signals | default | 1 | 8644.0000 | 785.8182 | 18.2955 | 0.0053 | -0.0120 | 0.0173 | -9.4517 | 11 | 5 | -111.2080 | 417.7466 | -0.3442 | -0.1839 | 0.4150 | 0 | 0 |
| price_momentum_oscillator_signals | half | 1 | 5368.0000 | 488.0000 | 29.6311 | -0.0019 | -0.0197 | 0.0178 | -9.5965 | 11 | 4 | -230.5175 | 692.4502 | -0.1669 | -0.1566 | 0.5500 | 0 | 0 |
| aroon_signals | double | 1 | 3276.0000 | 297.8182 | 48.3675 | -0.0160 | -0.0340 | 0.0180 | -10.1364 | 11 | 5 | -258.9844 | 711.8782 | -0.1764 | -0.1656 | 0.5700 | 0 | 0 |
| dspo_signals | default | 1 | 5078.0000 | 461.6364 | 31.3048 | -0.0065 | -0.0243 | 0.0178 | -11.2193 | 11 | 4 | -279.5871 | 706.2496 | -0.1863 | -0.1856 | 0.5625 | 0 | 0 |
| ehlers_reverse_ema_signals | half | 1 | 11006.0000 | 1000.5455 | 14.4916 | 0.0064 | -0.0113 | 0.0177 | -11.3475 | 11 | 5 | -150.4386 | 363.8596 | -0.3778 | -0.2331 | 0.3750 | 0 | 0 |
| coppock_curve_signals | double | 1 | 6064.0000 | 551.2727 | 26.1379 | -0.0031 | -0.0210 | 0.0179 | -11.5748 | 11 | 4 | -175.0911 | 650.4312 | -0.2551 | -0.1981 | 0.5125 | 0 | 0 |
| laguerre_filter_signals | half | 1 | 9486.0000 | 862.3636 | 16.7502 | 0.0041 | -0.0135 | 0.0176 | -11.6572 | 11 | 6 | -171.4385 | 415.1282 | -0.3612 | -0.2351 | 0.4475 | 0 | 0 |
| glitch_index_signals | default | 1 | 3796.0000 | 345.0909 | 42.0448 | -0.0170 | -0.0343 | 0.0173 | -11.8249 | 11 | 4 | -271.7582 | 702.1360 | -0.2043 | -0.1940 | 0.6250 | 0 | 0 |
| lemantrend_signals | default | 1 | 4324.0000 | 393.0909 | 36.6610 | -0.0127 | -0.0306 | 0.0178 | -12.0192 | 11 | 5 | -458.1809 | 711.6843 | -0.2039 | -0.1978 | 0.5925 | 0 | 0 |
| rex_oscillator_signals | default | 1 | 27810.0000 | 2528.1818 | 5.7223 | 0.0127 | -0.0048 | 0.0175 | -12.0750 | 11 | 6 | -171.3014 | 481.0766 | -0.4524 | -0.2702 | 0.0525 | 0 | 0 |
| kuskus_starlight_signals | half | 1 | 13146.0000 | 1195.0909 | 12.0993 | 0.0070 | -0.0103 | 0.0173 | -12.3208 | 11 | 5 | -118.1557 | 345.3575 | -0.5153 | -0.2648 | 0.3575 | 0 | 0 |
| j_tpo_signals | half | 1 | 8272.0000 | 752.0000 | 19.3126 | 0.0013 | -0.0166 | 0.0178 | -12.4741 | 11 | 5 | -167.6127 | 500.9327 | -0.3544 | -0.2385 | 0.4800 | 0 | 0 |
| adx_dmi_signals | default | 1 | 1470.0000 | 133.6364 | 110.0585 | -0.0804 | -0.0967 | 0.0163 | -12.9225 | 11 | 3 | -134.1372 | 395.7769 | -0.6084 | -0.4013 | 0.7350 | 0 | 0 |
| linreg_slope_signals | default | 1 | 8102.0000 | 736.5455 | 19.7531 | -0.0003 | -0.0180 | 0.0177 | -13.2579 | 11 | 6 | -212.0764 | 426.9323 | -0.3704 | -0.2605 | 0.4675 | 0 | 0 |
| kuskus_starlight_signals | default | 1 | 9108.0000 | 828.0000 | 17.4256 | 0.0013 | -0.0161 | 0.0174 | -13.3226 | 11 | 4 | -122.7881 | 476.2474 | -0.4485 | -0.2611 | 0.4600 | 0 | 0 |
| qqe_mod_signals | double | 1 | 7360.0000 | 669.0909 | 21.7057 | -0.0020 | -0.0200 | 0.0180 | -13.3739 | 11 | 5 | -194.9610 | 654.0264 | -0.3146 | -0.2204 | 0.5150 | 0 | 0 |
| polychromatic_momentum_signals | half | 1 | 12500.0000 | 1136.3636 | 12.7606 | 0.0059 | -0.0119 | 0.0178 | -13.4729 | 11 | 5 | -172.9502 | 415.9590 | -0.4228 | -0.2825 | 0.4225 | 0 | 0 |
| volatility_quality_signals | double | 1 | 2600.0000 | 236.3636 | 61.2646 | -0.0438 | -0.0606 | 0.0169 | -14.3288 | 11 | 4 | -263.1840 | 710.8181 | -0.2543 | -0.2650 | 0.7300 | 0 | 0 |
| schaff_trend_cycle_signals | double | 1 | 5156.0000 | 468.7273 | 17.7905 | -0.0145 | -0.0318 | 0.0173 | -14.8965 | 11 | 4 | -77.0728 | 362.4145 | -1.2041 | -0.5289 | 0.6400 | 0 | 0 |
| didi_index_signals | default | 1 | 9074.0000 | 824.9091 | 17.5294 | -0.0007 | -0.0184 | 0.0177 | -15.1569 | 11 | 6 | -179.5920 | 450.1744 | -0.4383 | -0.2964 | 0.5275 | 0 | 0 |
| lemantrend_signals | half | 1 | 5822.0000 | 529.2727 | 27.2384 | -0.0109 | -0.0288 | 0.0179 | -15.2298 | 11 | 6 | -477.2611 | 729.8983 | -0.2526 | -0.2473 | 0.5975 | 0 | 0 |
| kalman_filter_signals | default | 1 | 5138.0000 | 467.0909 | 31.0954 | -0.0155 | -0.0334 | 0.0179 | -15.5993 | 11 | 4 | -199.9141 | 737.7035 | -0.2940 | -0.2541 | 0.6425 | 0 | 0 |
| kalman_filter_signals | double | 1 | 3688.0000 | 335.2727 | 43.4452 | -0.0301 | -0.0478 | 0.0177 | -16.0399 | 11 | 5 | -209.0419 | 741.3876 | -0.3204 | -0.2701 | 0.6775 | 0 | 0 |
| coral_signals | double | 1 | 14804.0000 | 1345.8182 | 10.7598 | 0.0056 | -0.0119 | 0.0175 | -16.0520 | 11 | 4 | -154.6663 | 588.3397 | -0.5446 | -0.4068 | 0.4025 | 0 | 0 |
| supertrend_signals | half | 1 | 4150.0000 | 377.2727 | 38.5051 | -0.0260 | -0.0434 | 0.0174 | -16.3627 | 11 | 5 | -246.2001 | 689.4527 | -0.3531 | -0.2769 | 0.7200 | 0 | 0 |
| coppock_curve_signals | default | 1 | 8022.0000 | 729.2727 | 19.7816 | -0.0050 | -0.0229 | 0.0178 | -16.6695 | 11 | 6 | -176.6533 | 523.7513 | -0.4825 | -0.3190 | 0.5725 | 0 | 0 |
| parabolic_sar_signals | double | 1 | 9640.0000 | 876.3636 | 16.5498 | -0.0019 | -0.0195 | 0.0176 | -17.0730 | 11 | 5 | -103.9616 | 389.0154 | -1.0135 | -0.4154 | 0.5750 | 0 | 0 |
| j_tpo_signals | default | 1 | 4284.0000 | 389.4545 | 37.3422 | -0.0271 | -0.0447 | 0.0176 | -17.4096 | 11 | 4 | -245.2932 | 767.5074 | -0.3277 | -0.2969 | 0.7250 | 0 | 0 |
| waddah_attar_explosion_signals | half | 1 | 3124.0000 | 284.0000 | 51.5941 | -0.0445 | -0.0622 | 0.0177 | -17.6696 | 11 | 5 | -524.7816 | 748.1163 | -0.2739 | -0.2864 | 0.7525 | 0 | 0 |
| waddah_attar_explosion_signals | double | 1 | 3408.0000 | 309.8182 | 47.2817 | -0.0395 | -0.0572 | 0.0177 | -17.7103 | 11 | 5 | -526.1899 | 770.4896 | -0.2756 | -0.2853 | 0.7450 | 0 | 0 |
| lemantrend_signals | double | 1 | 3160.0000 | 287.2727 | 50.2873 | -0.0447 | -0.0624 | 0.0177 | -17.9263 | 11 | 4 | -518.1337 | 740.9084 | -0.2796 | -0.2927 | 0.7450 | 0 | 0 |
| waddah_attar_explosion_signals | default | 1 | 3300.0000 | 300.0000 | 48.8327 | -0.0423 | -0.0599 | 0.0177 | -17.9804 | 11 | 5 | -523.8200 | 764.8462 | -0.2787 | -0.2892 | 0.7475 | 0 | 0 |
| vortex_signals | double | 1 | 10940.0000 | 994.5455 | 14.5567 | -0.0004 | -0.0189 | 0.0186 | -18.8118 | 11 | 4 | -232.1704 | 813.8876 | -0.3986 | -0.3185 | 0.4750 | 0 | 0 |
| aroon_signals | default | 1 | 6286.0000 | 571.4545 | 25.3213 | -0.0151 | -0.0330 | 0.0179 | -18.8712 | 11 | 4 | -191.6583 | 768.5123 | -0.4654 | -0.3404 | 0.6600 | 0 | 0 |
| coppock_curve_signals | half | 1 | 9956.0000 | 905.0909 | 15.9839 | -0.0036 | -0.0213 | 0.0177 | -19.2668 | 11 | 6 | -154.1004 | 415.6269 | -0.6152 | -0.3846 | 0.5700 | 0 | 0 |
| fisher_transform_signals | default | 1 | 39540.0000 | 3594.5455 | 4.0330 | 0.0121 | -0.0055 | 0.0176 | -19.5968 | 11 | 3 | -127.0543 | 369.6464 | -0.9077 | -0.6313 | 0.0225 | 0 | 0 |
| qqe_mod_signals | default | 1 | 10190.0000 | 926.3636 | 15.6610 | -0.0034 | -0.0212 | 0.0178 | -19.6584 | 11 | 5 | -183.8237 | 426.9237 | -0.5619 | -0.3955 | 0.5900 | 0 | 0 |
| fisher_transform_signals | double | 1 | 37484.0000 | 3407.6364 | 4.2538 | 0.0116 | -0.0060 | 0.0176 | -20.5263 | 11 | 4 | -117.7153 | 356.5579 | -1.1177 | -0.6796 | 0.0175 | 0 | 0 |
| vortex_signals | default | 1 | 15280.0000 | 1389.0909 | 10.4347 | 0.0030 | -0.0150 | 0.0179 | -20.7687 | 11 | 4 | -175.3929 | 422.4422 | -0.6608 | -0.4170 | 0.4050 | 0 | 0 |
| vortex_signals | half | 1 | 21688.0000 | 1971.6364 | 7.3537 | 0.0067 | -0.0109 | 0.0176 | -21.4017 | 11 | 5 | -107.1152 | 467.0894 | -0.9214 | -0.5112 | 0.2475 | 0 | 0 |
| hieken_ashi_smoothed_signals | default | 1 | 9104.0000 | 827.6364 | 17.0815 | -0.0081 | -0.0260 | 0.0178 | -21.4836 | 11 | 5 | -189.6281 | 404.2625 | -0.7756 | -0.4357 | 0.6875 | 0 | 0 |
| hieken_ashi_smoothed_signals | double | 1 | 6068.0000 | 551.6364 | 25.2126 | -0.0222 | -0.0395 | 0.0173 | -21.7810 | 11 | 4 | -225.6551 | 817.0609 | -0.5030 | -0.4088 | 0.7650 | 0 | 0 |
| linreg_slope_signals | half | 1 | 16380.0000 | 1489.0909 | 9.7477 | 0.0024 | -0.0152 | 0.0175 | -22.5791 | 11 | 5 | -137.9879 | 498.2436 | -1.0003 | -0.5550 | 0.4050 | 0 | 0 |
| adx_dmi_signals | half | 1 | 13522.0000 | 1229.2727 | 11.7533 | -0.0022 | -0.0192 | 0.0170 | -23.6311 | 11 | 4 | -146.0051 | 511.0789 | -1.0348 | -0.6167 | 0.5475 | 0 | 0 |
| qqe_mod_signals | half | 1 | 13914.0000 | 1264.9091 | 11.4512 | -0.0020 | -0.0196 | 0.0176 | -24.8191 | 11 | 4 | -153.9291 | 481.0200 | -0.8992 | -0.5612 | 0.5450 | 0 | 0 |
| didi_index_signals | double | 1 | 11032.0000 | 1002.9091 | 14.4409 | -0.0096 | -0.0277 | 0.0181 | -27.7393 | 11 | 4 | -167.2985 | 647.9613 | -0.8485 | -0.5317 | 0.7100 | 0 | 0 |
| bears_bulls_impulse_signals | default | 1 | 9924.0000 | 902.1818 | 16.1066 | -0.0147 | -0.0321 | 0.0174 | -28.9188 | 11 | 5 | -172.4248 | 512.9159 | -0.8397 | -0.5683 | 0.7250 | 0 | 0 |
| center_of_gravity_signals | double | 1 | 19188.0000 | 1744.3636 | 8.2922 | 0.0010 | -0.0167 | 0.0177 | -29.0976 | 11 | 2 | -151.9845 | 587.1711 | -1.3715 | -0.7042 | 0.4425 | 0 | 0 |
| bears_bulls_impulse_signals | half | 1 | 10446.0000 | 949.6364 | 15.3067 | -0.0139 | -0.0311 | 0.0172 | -29.5419 | 11 | 5 | -122.4995 | 520.2758 | -1.2618 | -0.6355 | 0.7425 | 0 | 0 |
| rex_oscillator_signals | half | 1 | 30826.0000 | 2802.3636 | 5.1604 | 0.0053 | -0.0122 | 0.0175 | -34.1128 | 11 | 3 | -147.9558 | 623.7743 | -1.3666 | -1.0718 | 0.2100 | 0 | 0 |
| fx_sniper_ergodic_cci_signals | half | 1 | 27232.0000 | 2475.6364 | 5.8493 | 0.0033 | -0.0143 | 0.0176 | -35.4381 | 11 | 4 | -172.9901 | 536.9309 | -1.6664 | -1.1534 | 0.3575 | 0 | 0 |
| fisher_transform_signals | half | 1 | 43934.0000 | 3994.0000 | 3.6304 | 0.0076 | -0.0101 | 0.0176 | -40.2295 | 11 | 3 | -123.6243 | 526.9456 | -2.1341 | -1.2697 | 0.0975 | 0 | 0 |
| center_of_gravity_signals | default | 1 | 28770.0000 | 2615.4545 | 5.5406 | -0.0011 | -0.0189 | 0.0178 | -49.3572 | 11 | 4 | -146.8054 | 675.9652 | -1.7098 | -1.4456 | 0.5650 | 0 | 0 |
| coral_signals | default | 1 | 29666.0000 | 2696.9091 | 5.3622 | -0.0016 | -0.0193 | 0.0176 | -51.9979 | 11 | 4 | -217.6642 | 743.7737 | -1.6532 | -1.5634 | 0.5925 | 0 | 0 |
| coral_signals | half | 1 | 56812.0000 | 5164.7273 | 2.8090 | 0.0074 | -0.0101 | 0.0175 | -52.3212 | 11 | 2 | -168.3077 | 684.9425 | -2.1820 | -1.8990 | 0.0325 | 0 | 0 |
| relative_vigor_index_signals | double | 1 | 27908.0000 | 2537.0909 | 5.6982 | -0.0054 | -0.0232 | 0.0177 | -58.7409 | 11 | 3 | -141.1094 | 793.2863 | -2.6542 | -1.6520 | 0.7675 | 0 | 0 |
| relative_vigor_index_signals | half | 1 | 30146.0000 | 2740.5455 | 5.2914 | -0.0042 | -0.0218 | 0.0176 | -59.7274 | 11 | 2 | -169.3243 | 826.0249 | -2.1278 | -1.8276 | 0.7250 | 0 | 0 |
| relative_vigor_index_signals | default | 1 | 28118.0000 | 2556.1818 | 5.6660 | -0.0069 | -0.0245 | 0.0176 | -62.6891 | 11 | 2 | -132.8542 | 904.1055 | -3.9466 | -2.0010 | 0.7850 | 0 | 0 |
| rex_oscillator_signals | double | 1 | 36616.0000 | 3328.7273 | 4.3368 | -0.0032 | -0.0209 | 0.0177 | -69.7190 | 11 | 1 | -227.2478 | 916.7484 | -2.3145 | -1.9333 | 0.7225 | 0 | 0 |
| center_of_gravity_signals | half | 1 | 45002.0000 | 4091.0909 | 3.5451 | -0.0019 | -0.0195 | 0.0176 | -79.9465 | 11 | 2 | -268.4897 | 890.9286 | -2.5338 | -2.6514 | 0.5875 | 0 | 0 |


**0 of 117 candidate-settings clear the empirical best-of-39 floor; 0 clear the alone floor.** 24 of 117 have a positive net R per year.


### C1 — `flip_only`, stability across the three settings

`sign_agree = 1` means all three settings agree on the sign of net R per year. A candidate positive on one setting and negative on two is being fitted, not measured.

| indicator | settings | settings_positive | sign_agree | R_per_year_min | R_per_year_med | R_per_year_max | spread |
|---|---:|---:|---:|---:|---:|---:|---:|
| halftrend_signals | 3 | 3 | 1 | 14.1626 | 28.9810 | 33.4140 | 19.2514 |
| ichimoku_signals | 3 | 3 | 1 | 13.9838 | 21.1364 | 23.2824 | 9.2987 |
| schaff_trend_cycle_signals | 3 | 2 | 0 | -14.8965 | 9.9226 | 9.9791 | 24.8755 |
| dpo_signals | 3 | 2 | 0 | -4.6406 | 8.8651 | 25.2064 | 29.8470 |
| supertrend_signals | 3 | 2 | 0 | -16.3627 | 3.6965 | 6.6128 | 22.9754 |
| price_momentum_oscillator_signals | 3 | 2 | 0 | -9.5965 | 0.7382 | 27.8213 | 37.4178 |
| laguerre_filter_signals | 3 | 1 | 0 | -11.6572 | -1.0889 | 31.8276 | 43.4849 |
| chandelier_exit_signals | 3 | 0 | 1 | -7.2516 | -2.3941 | -0.3192 | 6.9324 |
| ssl_channel_signals | 3 | 0 | 1 | -7.3400 | -2.7233 | -0.9570 | 6.3830 |
| parabolic_sar_signals | 3 | 0 | 1 | -17.0730 | -3.6383 | -3.4808 | 13.5922 |
| trend_direction_force_index_signals | 3 | 1 | 0 | -6.4972 | -3.7992 | 21.0444 | 27.5415 |
| mama_fama_signals | 3 | 1 | 0 | -6.4498 | -4.5171 | 8.2361 | 14.6859 |
| donchian_breakout_signals | 3 | 1 | 0 | -5.6114 | -4.8311 | 7.3761 | 12.9875 |
| dspo_signals | 3 | 1 | 0 | -11.2193 | -5.1719 | 17.8363 | 29.0556 |
| fx_sniper_ergodic_cci_signals | 3 | 0 | 1 | -35.4381 | -6.8367 | -5.2409 | 30.1972 |
| polychromatic_momentum_signals | 3 | 0 | 1 | -13.4729 | -7.0156 | -6.4260 | 7.0469 |
| volatility_quality_signals | 3 | 1 | 0 | -14.3288 | -7.0492 | 7.4386 | 21.7674 |
| kase_peak_oscillator_signals | 3 | 0 | 1 | -9.4517 | -7.2665 | -2.2028 | 7.2489 |
| ehlers_reverse_ema_signals | 3 | 0 | 1 | -11.3475 | -7.9115 | -1.8467 | 9.5008 |
| glitch_index_signals | 3 | 1 | 0 | -11.8249 | -7.9365 | 0.4366 | 12.2615 |
| aroon_signals | 3 | 0 | 1 | -18.8712 | -10.1364 | -0.8400 | 18.0312 |
| kuskus_starlight_signals | 3 | 1 | 0 | -13.3226 | -12.3208 | 0.7559 | 14.0785 |
| j_tpo_signals | 3 | 1 | 0 | -17.4096 | -12.4741 | 37.3614 | 54.7710 |
| adx_dmi_signals | 3 | 1 | 0 | -23.6311 | -12.9225 | 13.8139 | 37.4450 |
| linreg_slope_signals | 3 | 0 | 1 | -22.5791 | -13.2579 | -6.8332 | 15.7458 |
| didi_index_signals | 3 | 0 | 1 | -27.7393 | -15.1569 | -8.8040 | 18.9353 |
| lemantrend_signals | 3 | 0 | 1 | -17.9263 | -15.2298 | -12.0192 | 5.9072 |
| kalman_filter_signals | 3 | 0 | 1 | -16.0399 | -15.5993 | -7.6398 | 8.4001 |
| coppock_curve_signals | 3 | 0 | 1 | -19.2668 | -16.6695 | -11.5748 | 7.6920 |
| waddah_attar_explosion_signals | 3 | 0 | 1 | -17.9804 | -17.7103 | -17.6696 | 0.3108 |
| qqe_mod_signals | 3 | 0 | 1 | -24.8191 | -19.6584 | -13.3739 | 11.4451 |
| fisher_transform_signals | 3 | 0 | 1 | -40.2295 | -20.5263 | -19.5968 | 20.6327 |
| vortex_signals | 3 | 0 | 1 | -21.4017 | -20.7687 | -18.8118 | 2.5899 |
| hieken_ashi_smoothed_signals | 3 | 0 | 1 | -21.7810 | -21.4836 | -7.8692 | 13.9118 |
| bears_bulls_impulse_signals | 3 | 0 | 1 | -29.5419 | -28.9188 | -5.9115 | 23.6305 |
| rex_oscillator_signals | 3 | 0 | 1 | -69.7190 | -34.1128 | -12.0750 | 57.6440 |
| center_of_gravity_signals | 3 | 0 | 1 | -79.9465 | -49.3572 | -29.0976 | 50.8488 |
| coral_signals | 3 | 0 | 1 | -52.3212 | -51.9979 | -16.0520 | 36.2692 |
| relative_vigor_index_signals | 3 | 0 | 1 | -62.6891 | -59.7274 | -58.7409 | 3.9482 |


**25 of 39 candidates have all three settings agreeing in sign.**


## C1 — `jack`, fixed settings, unseen trade years 2005-2015

Empirical yearly-t floors **from the random-entry null**: alone **0.596**, best-of-39 **2.064**. The analytic equivalents on 11 yearly observations are 1.812 and 3.973 — the empirical ones are lower because the analytic formula assumes a **zero-mean** null while the real null also pays costs, so it is centred below zero.

| indicator | setting | distinct_setting | n_entered | trades_per_year | mean_bars | R_gross_per_trade | R_net_per_trade | cost_per_trade | R_net_per_year | years | years_positive | worst_year | worst_dip_R | t_yearly | t_block_boot | null_p | clears_alone_emp | clears_family_emp |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ichimoku_signals | half | 1 | 3400.0000 | 309.0909 | 6.8850 | 0.0420 | 0.0241 | 0.0180 | 7.4431 | 11 | 7 | -23.3090 | 57.5555 | 1.0496 | 0.8230 | 0.0825 | 1 | 0 |
| schaff_trend_cycle_signals | default | 1 | 6050.0000 | 550.0000 | 6.3451 | 0.0286 | 0.0113 | 0.0173 | 6.2243 | 11 | 7 | -27.4711 | 108.3255 | 0.8867 | 0.5096 | 0.0425 | 1 | 0 |
| ichimoku_signals | default | 1 | 3032.0000 | 275.6364 | 6.5841 | 0.0312 | 0.0129 | 0.0183 | 3.5606 | 11 | 5 | -20.5401 | 69.8169 | 0.6373 | 0.4045 | 0.1750 | 1 | 0 |
| dspo_signals | half | 1 | 9556.0000 | 868.7273 | 6.5387 | 0.0196 | 0.0020 | 0.0177 | 1.7172 | 11 | 5 | -63.9743 | 135.9594 | 0.1375 | 0.1203 | 0.0675 | 0 | 0 |
| volatility_quality_signals | default | 1 | 7576.0000 | 688.7273 | 6.6697 | 0.0192 | 0.0020 | 0.0172 | 1.3576 | 11 | 4 | -46.5049 | 128.9458 | 0.1164 | 0.1078 | 0.1300 | 0 | 0 |
| aroon_signals | default | 1 | 6310.0000 | 573.6364 | 6.6219 | 0.0190 | 0.0011 | 0.0179 | 0.6551 | 11 | 6 | -36.0622 | 93.6217 | 0.0812 | 0.0589 | 0.2000 | 0 | 0 |
| halftrend_signals | double | 1 | 374.0000 | 34.0000 | 7.1364 | 0.0313 | 0.0149 | 0.0165 | 0.5052 | 11 | 5 | -8.9233 | 26.2989 | 0.2836 | 0.2252 | 0.3325 | 0 | 0 |
| trend_direction_force_index_signals | double | 1 | 5470.0000 | 497.2727 | 6.5945 | 0.0182 | 0.0008 | 0.0173 | 0.4187 | 11 | 6 | -42.7030 | 118.5452 | 0.0440 | 0.0364 | 0.1650 | 0 | 0 |
| halftrend_signals | default | 1 | 722.0000 | 65.6364 | 6.9224 | 0.0227 | 0.0057 | 0.0170 | 0.3762 | 11 | 5 | -8.0646 | 25.0030 | 0.2556 | 0.1343 | 0.2825 | 0 | 0 |
| schaff_trend_cycle_signals | half | 1 | 6278.0000 | 570.7273 | 5.9597 | 0.0179 | 0.0004 | 0.0175 | 0.2119 | 11 | 4 | -37.2336 | 132.3369 | 0.0266 | 0.0186 | 0.1650 | 0 | 0 |
| adx_dmi_signals | double | 1 | 152.0000 | 13.8182 | 5.5132 | 0.0192 | 0.0051 | 0.0140 | 0.0711 | 11 | 4 | -2.9282 | 12.4923 | 0.0801 | 0.0633 | 0.3525 | 0 | 0 |
| ehlers_reverse_ema_signals | default | 1 | 8438.0000 | 767.0909 | 6.6587 | 0.0173 | -0.0005 | 0.0178 | -0.3904 | 11 | 5 | -64.4157 | 181.7689 | -0.0281 | -0.0270 | 0.1475 | 0 | 0 |
| glitch_index_signals | double | 1 | 5300.0000 | 481.8182 | 6.7581 | 0.0167 | -0.0011 | 0.0178 | -0.5169 | 11 | 5 | -47.6821 | 124.3674 | -0.0493 | -0.0452 | 0.1950 | 0 | 0 |
| polychromatic_momentum_signals | default | 1 | 6422.0000 | 583.8182 | 6.3971 | 0.0169 | -0.0012 | 0.0180 | -0.6842 | 11 | 5 | -45.2138 | 130.7984 | -0.0793 | -0.0531 | 0.1800 | 0 | 0 |
| ichimoku_signals | double | 1 | 4186.0000 | 380.5455 | 6.5210 | 0.0151 | -0.0023 | 0.0174 | -0.8862 | 11 | 4 | -27.7990 | 84.8674 | -0.1282 | -0.0938 | 0.3425 | 0 | 0 |
| waddah_attar_explosion_signals | double | 1 | 3564.0000 | 324.0000 | 5.7135 | 0.0134 | -0.0042 | 0.0176 | -1.3627 | 11 | 5 | -25.0164 | 71.3470 | -0.2100 | -0.2749 | 0.2625 | 0 | 0 |
| aroon_signals | double | 1 | 3286.0000 | 298.7273 | 6.5548 | 0.0133 | -0.0047 | 0.0180 | -1.4179 | 11 | 5 | -26.2157 | 99.6336 | -0.2044 | -0.1763 | 0.3175 | 0 | 0 |
| waddah_attar_explosion_signals | half | 1 | 3578.0000 | 325.2727 | 6.0126 | 0.0128 | -0.0049 | 0.0177 | -1.5998 | 11 | 4 | -30.3702 | 91.1009 | -0.2061 | -0.2951 | 0.2875 | 0 | 0 |
| kuskus_starlight_signals | default | 1 | 9108.0000 | 828.0000 | 6.4975 | 0.0154 | -0.0020 | 0.0174 | -1.6252 | 11 | 6 | -30.0910 | 91.9113 | -0.2977 | -0.1256 | 0.1625 | 0 | 0 |
| kalman_filter_signals | half | 1 | 7352.0000 | 668.3636 | 6.6430 | 0.0153 | -0.0026 | 0.0179 | -1.7270 | 11 | 6 | -53.8236 | 167.1254 | -0.1316 | -0.1303 | 0.1825 | 0 | 0 |
| donchian_breakout_signals | default | 1 | 3740.0000 | 340.0000 | 7.0086 | 0.0120 | -0.0053 | 0.0172 | -1.7930 | 11 | 5 | -22.0606 | 71.3873 | -0.3167 | -0.2140 | 0.3125 | 0 | 0 |
| aroon_signals | half | 1 | 11978.0000 | 1088.9091 | 6.0984 | 0.0157 | -0.0019 | 0.0176 | -2.0929 | 11 | 5 | -77.6990 | 202.0120 | -0.1270 | -0.1241 | 0.0975 | 0 | 0 |
| polychromatic_momentum_signals | half | 1 | 12502.0000 | 1136.5455 | 5.9111 | 0.0159 | -0.0019 | 0.0178 | -2.1099 | 11 | 6 | -84.2764 | 220.0846 | -0.1333 | -0.1193 | 0.1000 | 0 | 0 |
| dpo_signals | half | 1 | 11108.0000 | 1009.8182 | 5.2793 | 0.0158 | -0.0022 | 0.0180 | -2.2030 | 11 | 4 | -43.0804 | 162.3430 | -0.2240 | -0.1588 | 0.1025 | 0 | 0 |
| laguerre_filter_signals | half | 1 | 9486.0000 | 862.3636 | 6.4279 | 0.0148 | -0.0028 | 0.0176 | -2.4170 | 11 | 6 | -40.5785 | 177.0781 | -0.2295 | -0.1645 | 0.2000 | 0 | 0 |
| mama_fama_signals | double | 1 | 3232.0000 | 293.8182 | 6.7169 | 0.0091 | -0.0086 | 0.0177 | -2.5190 | 11 | 5 | -27.5036 | 74.9577 | -0.4174 | -0.3116 | 0.3675 | 0 | 0 |
| mama_fama_signals | default | 1 | 6794.0000 | 617.6364 | 6.6822 | 0.0137 | -0.0041 | 0.0178 | -2.5234 | 11 | 6 | -31.9062 | 127.0235 | -0.3410 | -0.2076 | 0.2400 | 0 | 0 |
| dpo_signals | double | 1 | 4882.0000 | 443.8182 | 5.0115 | 0.0122 | -0.0057 | 0.0179 | -2.5248 | 11 | 5 | -29.3659 | 85.4223 | -0.5320 | -0.3476 | 0.1875 | 0 | 0 |
| donchian_breakout_signals | half | 1 | 6562.0000 | 596.5455 | 6.7743 | 0.0127 | -0.0046 | 0.0173 | -2.7275 | 11 | 5 | -48.8909 | 151.7174 | -0.3073 | -0.2215 | 0.1950 | 0 | 0 |
| qqe_mod_signals | double | 1 | 7360.0000 | 669.0909 | 6.3488 | 0.0136 | -0.0044 | 0.0180 | -2.9225 | 11 | 6 | -60.8626 | 156.4680 | -0.2480 | -0.2332 | 0.2075 | 0 | 0 |
| hieken_ashi_smoothed_signals | double | 1 | 6068.0000 | 551.6364 | 6.4281 | 0.0114 | -0.0059 | 0.0173 | -3.2595 | 11 | 6 | -46.4575 | 113.0232 | -0.3865 | -0.2843 | 0.2275 | 0 | 0 |
| ehlers_reverse_ema_signals | half | 1 | 11006.0000 | 1000.5455 | 6.4994 | 0.0144 | -0.0034 | 0.0177 | -3.3587 | 11 | 6 | -75.3290 | 203.3497 | -0.2644 | -0.1988 | 0.1300 | 0 | 0 |
| waddah_attar_explosion_signals | default | 1 | 3564.0000 | 324.0000 | 5.7840 | 0.0072 | -0.0104 | 0.0176 | -3.3755 | 11 | 5 | -28.5396 | 75.3680 | -0.4813 | -0.7010 | 0.3375 | 0 | 0 |
| donchian_breakout_signals | double | 1 | 1934.0000 | 175.8182 | 6.5812 | -0.0032 | -0.0206 | 0.0175 | -3.6272 | 11 | 4 | -28.8119 | 68.8002 | -0.7151 | -0.5450 | 0.5250 | 0 | 0 |
| j_tpo_signals | default | 1 | 4286.0000 | 389.6364 | 6.3586 | 0.0082 | -0.0094 | 0.0176 | -3.6676 | 11 | 4 | -61.0116 | 131.9796 | -0.3856 | -0.3539 | 0.3225 | 0 | 0 |
| chandelier_exit_signals | default | 1 | 5154.0000 | 468.5455 | 6.8531 | 0.0084 | -0.0081 | 0.0165 | -3.8081 | 11 | 6 | -29.9769 | 82.4245 | -0.7720 | -0.3707 | 0.3275 | 0 | 0 |
| mama_fama_signals | half | 1 | 14884.0000 | 1353.0909 | 5.7031 | 0.0147 | -0.0028 | 0.0176 | -3.8553 | 11 | 4 | -77.2027 | 194.4324 | -0.3398 | -0.2330 | 0.0825 | 0 | 0 |
| lemantrend_signals | double | 1 | 3160.0000 | 287.2727 | 5.7323 | 0.0042 | -0.0135 | 0.0177 | -3.8790 | 11 | 4 | -31.4552 | 79.3653 | -0.6544 | -0.8594 | 0.4350 | 0 | 0 |
| supertrend_signals | double | 1 | 3968.0000 | 360.7273 | 6.9594 | 0.0060 | -0.0111 | 0.0171 | -3.9885 | 11 | 5 | -32.0740 | 84.3455 | -0.7281 | -0.4460 | 0.3725 | 0 | 0 |
| j_tpo_signals | double | 1 | 2026.0000 | 184.1818 | 6.3110 | -0.0045 | -0.0220 | 0.0175 | -4.0461 | 11 | 3 | -19.0105 | 81.0595 | -1.3223 | -0.7848 | 0.5950 | 0 | 0 |
| coppock_curve_signals | double | 1 | 6064.0000 | 551.2727 | 6.6135 | 0.0103 | -0.0076 | 0.0179 | -4.2069 | 11 | 4 | -33.6598 | 149.7279 | -0.5357 | -0.3477 | 0.2200 | 0 | 0 |
| laguerre_filter_signals | double | 1 | 2156.0000 | 196.0000 | 6.5682 | -0.0041 | -0.0217 | 0.0176 | -4.2516 | 11 | 4 | -34.0363 | 109.3426 | -0.8662 | -0.7271 | 0.5275 | 0 | 0 |
| supertrend_signals | default | 1 | 4030.0000 | 366.3636 | 6.9362 | 0.0050 | -0.0122 | 0.0172 | -4.4754 | 11 | 5 | -26.6445 | 89.4173 | -1.1155 | -0.5049 | 0.4100 | 0 | 0 |
| price_momentum_oscillator_signals | default | 1 | 3838.0000 | 348.9091 | 6.8319 | 0.0048 | -0.0129 | 0.0176 | -4.4900 | 11 | 5 | -35.0974 | 84.9660 | -0.7339 | -0.5171 | 0.4300 | 0 | 0 |
| ehlers_reverse_ema_signals | double | 1 | 6328.0000 | 575.2727 | 6.7775 | 0.0095 | -0.0083 | 0.0178 | -4.8028 | 11 | 4 | -41.9702 | 113.8908 | -0.7945 | -0.4460 | 0.2925 | 0 | 0 |
| price_momentum_oscillator_signals | double | 1 | 2560.0000 | 232.7273 | 6.5867 | -0.0037 | -0.0217 | 0.0180 | -5.0397 | 11 | 4 | -28.7613 | 101.2211 | -0.9389 | -0.7712 | 0.5325 | 0 | 0 |
| volatility_quality_signals | double | 1 | 2600.0000 | 236.3636 | 6.4735 | -0.0048 | -0.0216 | 0.0169 | -5.1167 | 11 | 4 | -25.5989 | 93.1408 | -1.1439 | -0.8020 | 0.5825 | 0 | 0 |
| laguerre_filter_signals | default | 1 | 4612.0000 | 419.2727 | 6.4690 | 0.0053 | -0.0123 | 0.0175 | -5.1420 | 11 | 6 | -53.5695 | 88.0545 | -0.6126 | -0.5508 | 0.4300 | 0 | 0 |
| kalman_filter_signals | default | 1 | 5138.0000 | 467.0909 | 6.5849 | 0.0067 | -0.0113 | 0.0179 | -5.2631 | 11 | 5 | -60.1391 | 157.5852 | -0.5313 | -0.4343 | 0.3550 | 0 | 0 |
| chandelier_exit_signals | half | 1 | 4728.0000 | 429.8182 | 6.9645 | 0.0048 | -0.0123 | 0.0171 | -5.2894 | 11 | 5 | -42.3242 | 106.2379 | -0.8895 | -0.5604 | 0.3850 | 0 | 0 |
| halftrend_signals | half | 1 | 1196.0000 | 108.7273 | 6.0008 | -0.0356 | -0.0525 | 0.0169 | -5.7103 | 11 | 3 | -17.5594 | 87.8235 | -2.6724 | -1.3687 | 0.8625 | 0 | 0 |
| linreg_slope_signals | default | 1 | 10048.0000 | 913.4545 | 6.6666 | 0.0111 | -0.0064 | 0.0176 | -5.8627 | 11 | 5 | -66.8144 | 225.3457 | -0.4231 | -0.3671 | 0.2000 | 0 | 0 |
| vortex_signals | double | 1 | 10948.0000 | 995.2727 | 5.0326 | 0.0126 | -0.0060 | 0.0186 | -5.9675 | 11 | 4 | -48.4549 | 186.2373 | -0.5684 | -0.4625 | 0.1775 | 0 | 0 |
| linreg_slope_signals | double | 1 | 5364.0000 | 487.6364 | 6.7899 | 0.0051 | -0.0124 | 0.0175 | -6.0630 | 11 | 4 | -44.9651 | 118.3365 | -0.7140 | -0.5975 | 0.4025 | 0 | 0 |
| j_tpo_signals | half | 1 | 8278.0000 | 752.5455 | 6.4287 | 0.0096 | -0.0082 | 0.0178 | -6.1768 | 11 | 4 | -49.0209 | 171.2127 | -0.6015 | -0.4591 | 0.2875 | 0 | 0 |
| supertrend_signals | half | 1 | 4150.0000 | 377.2727 | 6.7896 | 0.0006 | -0.0168 | 0.0174 | -6.3522 | 11 | 4 | -26.6462 | 126.9801 | -1.6145 | -0.7133 | 0.4550 | 0 | 0 |
| lemantrend_signals | default | 1 | 4324.0000 | 393.0909 | 5.2981 | 0.0015 | -0.0163 | 0.0178 | -6.4075 | 11 | 5 | -29.4794 | 95.5058 | -1.6550 | -1.2672 | 0.4650 | 0 | 0 |
| dspo_signals | double | 1 | 2480.0000 | 225.4545 | 6.4532 | -0.0108 | -0.0287 | 0.0179 | -6.4678 | 11 | 4 | -29.1216 | 94.9979 | -1.4121 | -0.9988 | 0.6150 | 0 | 0 |
| ssl_channel_signals | double | 1 | 9140.0000 | 830.9091 | 6.7685 | 0.0099 | -0.0078 | 0.0177 | -6.4943 | 11 | 4 | -58.0477 | 198.5336 | -0.6055 | -0.4465 | 0.2925 | 0 | 0 |
| schaff_trend_cycle_signals | double | 1 | 5626.0000 | 511.4545 | 6.3864 | 0.0043 | -0.0129 | 0.0172 | -6.6140 | 11 | 2 | -34.3841 | 177.5386 | -1.0442 | -0.6255 | 0.3900 | 0 | 0 |
| trend_direction_force_index_signals | half | 1 | 12346.0000 | 1122.3636 | 6.6298 | 0.0113 | -0.0062 | 0.0175 | -6.9600 | 11 | 5 | -83.2742 | 221.5494 | -0.4789 | -0.3826 | 0.2225 | 0 | 0 |
| glitch_index_signals | default | 1 | 6872.0000 | 624.7273 | 6.7205 | 0.0058 | -0.0116 | 0.0174 | -7.2643 | 11 | 3 | -49.7179 | 132.5731 | -0.6743 | -0.5675 | 0.4375 | 0 | 0 |
| hieken_ashi_smoothed_signals | half | 1 | 11606.0000 | 1055.0909 | 6.0640 | 0.0107 | -0.0070 | 0.0176 | -7.3456 | 11 | 6 | -74.0745 | 290.1590 | -0.4107 | -0.4294 | 0.1950 | 0 | 0 |
| chandelier_exit_signals | double | 1 | 7160.0000 | 650.9091 | 6.0406 | 0.0047 | -0.0113 | 0.0161 | -7.3835 | 11 | 4 | -57.5783 | 117.4299 | -0.8943 | -0.7091 | 0.3675 | 0 | 0 |
| dspo_signals | default | 1 | 5078.0000 | 461.6364 | 6.6987 | 0.0013 | -0.0165 | 0.0178 | -7.6365 | 11 | 4 | -37.5979 | 137.3566 | -1.1845 | -0.8163 | 0.5375 | 0 | 0 |
| kase_peak_oscillator_signals | double | 1 | 6300.0000 | 572.7273 | 6.4067 | 0.0039 | -0.0134 | 0.0173 | -7.6934 | 11 | 4 | -57.2557 | 129.4452 | -0.8269 | -0.7198 | 0.4225 | 0 | 0 |
| glitch_index_signals | half | 1 | 7976.0000 | 725.0909 | 6.5802 | 0.0068 | -0.0107 | 0.0175 | -7.7541 | 11 | 5 | -64.2663 | 239.5063 | -0.4984 | -0.5119 | 0.3625 | 0 | 0 |
| adx_dmi_signals | default | 1 | 2104.0000 | 191.2727 | 6.1027 | -0.0245 | -0.0406 | 0.0161 | -7.7672 | 11 | 0 | -16.1014 | 100.0216 | -4.5511 | -1.7274 | 0.8025 | 0 | 0 |
| kuskus_starlight_signals | half | 1 | 13146.0000 | 1195.0909 | 6.2449 | 0.0106 | -0.0067 | 0.0173 | -7.9799 | 11 | 5 | -55.6490 | 192.3008 | -0.9182 | -0.4997 | 0.1700 | 0 | 0 |
| bears_bulls_impulse_signals | double | 1 | 11978.0000 | 1088.9091 | 6.9010 | 0.0099 | -0.0074 | 0.0173 | -8.1092 | 11 | 4 | -73.6803 | 202.8577 | -0.5433 | -0.4904 | 0.2325 | 0 | 0 |
| coppock_curve_signals | default | 1 | 8022.0000 | 729.2727 | 6.5856 | 0.0067 | -0.0112 | 0.0178 | -8.1347 | 11 | 5 | -62.7003 | 214.1773 | -0.6193 | -0.5942 | 0.3350 | 0 | 0 |
| coppock_curve_signals | half | 1 | 9956.0000 | 905.0909 | 6.3388 | 0.0084 | -0.0093 | 0.0177 | -8.4290 | 11 | 5 | -60.8260 | 220.7361 | -0.6424 | -0.5661 | 0.3025 | 0 | 0 |
| price_momentum_oscillator_signals | half | 1 | 5368.0000 | 488.0000 | 6.6755 | 0.0002 | -0.0175 | 0.0178 | -8.5557 | 11 | 4 | -46.3098 | 127.5813 | -1.1658 | -0.8639 | 0.4525 | 0 | 0 |
| parabolic_sar_signals | double | 1 | 9640.0000 | 876.3636 | 6.4694 | 0.0076 | -0.0099 | 0.0176 | -8.7146 | 11 | 4 | -52.8149 | 271.9013 | -0.7419 | -0.5938 | 0.3100 | 0 | 0 |
| vortex_signals | default | 1 | 15292.0000 | 1390.1818 | 5.0052 | 0.0117 | -0.0063 | 0.0179 | -8.7516 | 11 | 5 | -64.5267 | 230.8491 | -0.6350 | -0.5170 | 0.1075 | 0 | 0 |
| lemantrend_signals | half | 1 | 5822.0000 | 529.2727 | 4.9136 | 0.0010 | -0.0169 | 0.0179 | -8.9332 | 11 | 3 | -36.7281 | 111.5526 | -1.7638 | -1.4418 | 0.4425 | 0 | 0 |
| kuskus_starlight_signals | double | 1 | 6276.0000 | 570.5455 | 6.4591 | 0.0017 | -0.0157 | 0.0173 | -8.9374 | 11 | 5 | -47.7569 | 132.8982 | -1.1105 | -0.8911 | 0.4100 | 0 | 0 |
| trend_direction_force_index_signals | default | 1 | 8150.0000 | 740.9091 | 6.6946 | 0.0054 | -0.0121 | 0.0175 | -8.9921 | 11 | 2 | -62.2081 | 167.0291 | -0.7607 | -0.6245 | 0.4025 | 0 | 0 |
| ssl_channel_signals | default | 1 | 12948.0000 | 1177.0909 | 6.2977 | 0.0094 | -0.0080 | 0.0174 | -9.4276 | 11 | 5 | -92.6342 | 251.3422 | -0.6902 | -0.5534 | 0.2125 | 0 | 0 |
| dpo_signals | default | 1 | 7800.0000 | 709.0909 | 5.1222 | 0.0043 | -0.0137 | 0.0180 | -9.7370 | 11 | 4 | -56.7800 | 179.0417 | -1.3646 | -0.9698 | 0.3850 | 0 | 0 |
| didi_index_signals | half | 1 | 11050.0000 | 1004.5455 | 6.2043 | 0.0079 | -0.0098 | 0.0177 | -9.8458 | 11 | 4 | -98.2103 | 245.2537 | -0.7674 | -0.6413 | 0.2725 | 0 | 0 |
| kalman_filter_signals | double | 1 | 3688.0000 | 335.2727 | 6.7454 | -0.0117 | -0.0294 | 0.0177 | -9.8666 | 11 | 3 | -42.1798 | 130.3847 | -1.4853 | -1.2928 | 0.6775 | 0 | 0 |
| qqe_mod_signals | default | 1 | 10190.0000 | 926.3636 | 6.1189 | 0.0070 | -0.0108 | 0.0178 | -10.0032 | 11 | 4 | -73.5539 | 238.9409 | -0.8172 | -0.6806 | 0.3200 | 0 | 0 |
| parabolic_sar_signals | default | 1 | 14826.0000 | 1347.8182 | 5.9003 | 0.0098 | -0.0077 | 0.0175 | -10.3394 | 11 | 6 | -77.5970 | 229.0506 | -0.7589 | -0.5895 | 0.2025 | 0 | 0 |
| kase_peak_oscillator_signals | half | 1 | 12186.0000 | 1107.8182 | 6.0611 | 0.0075 | -0.0096 | 0.0172 | -10.6803 | 11 | 5 | -85.8244 | 234.5527 | -0.9204 | -0.6603 | 0.2425 | 0 | 0 |
| kase_peak_oscillator_signals | default | 1 | 8644.0000 | 785.8182 | 6.4172 | 0.0034 | -0.0139 | 0.0173 | -10.9038 | 11 | 5 | -61.8052 | 191.8453 | -1.4469 | -0.8666 | 0.4100 | 0 | 0 |
| parabolic_sar_signals | half | 1 | 21480.0000 | 1952.7273 | 5.0804 | 0.0114 | -0.0061 | 0.0175 | -11.8649 | 11 | 4 | -84.1401 | 265.4065 | -0.8107 | -0.6174 | 0.1025 | 0 | 0 |
| didi_index_signals | default | 1 | 9074.0000 | 824.9091 | 6.2701 | 0.0031 | -0.0146 | 0.0177 | -12.0382 | 11 | 4 | -66.2668 | 262.4185 | -0.9401 | -0.7990 | 0.4150 | 0 | 0 |
| polychromatic_momentum_signals | double | 1 | 3220.0000 | 292.7273 | 6.1323 | -0.0255 | -0.0431 | 0.0175 | -12.6095 | 11 | 2 | -30.6749 | 170.0909 | -2.5919 | -1.6854 | 0.8950 | 0 | 0 |
| volatility_quality_signals | half | 1 | 18822.0000 | 1711.0909 | 5.2425 | 0.0097 | -0.0075 | 0.0172 | -12.7980 | 11 | 5 | -70.9092 | 232.5491 | -1.2004 | -0.7223 | 0.1650 | 0 | 0 |
| adx_dmi_signals | half | 1 | 14572.0000 | 1324.7273 | 5.1830 | 0.0073 | -0.0098 | 0.0171 | -12.9456 | 11 | 5 | -67.5768 | 244.4035 | -1.0414 | -0.8453 | 0.2525 | 0 | 0 |
| hieken_ashi_smoothed_signals | default | 1 | 9104.0000 | 827.6364 | 6.2417 | 0.0003 | -0.0176 | 0.0178 | -14.5309 | 11 | 3 | -53.2977 | 280.1075 | -1.2869 | -0.9382 | 0.5275 | 0 | 0 |
| rex_oscillator_signals | default | 1 | 27810.0000 | 2528.1818 | 3.4745 | 0.0115 | -0.0060 | 0.0175 | -15.2050 | 11 | 3 | -76.1399 | 347.7828 | -0.8698 | -0.7859 | 0.0525 | 0 | 0 |
| fx_sniper_ergodic_cci_signals | double | 1 | 18036.0000 | 1639.6364 | 5.1153 | 0.0083 | -0.0095 | 0.0178 | -15.6394 | 11 | 4 | -74.1316 | 326.9779 | -1.0545 | -0.8820 | 0.2050 | 0 | 0 |
| ssl_channel_signals | half | 1 | 18122.0000 | 1647.4545 | 5.4902 | 0.0077 | -0.0095 | 0.0172 | -15.7059 | 11 | 6 | -82.4286 | 272.6860 | -1.1498 | -0.8477 | 0.2300 | 0 | 0 |
| fx_sniper_ergodic_cci_signals | default | 1 | 21636.0000 | 1966.9091 | 4.7880 | 0.0094 | -0.0082 | 0.0175 | -16.0915 | 11 | 4 | -109.9965 | 276.1877 | -1.0310 | -0.8924 | 0.1525 | 0 | 0 |
| didi_index_signals | double | 1 | 11032.0000 | 1002.9091 | 5.1524 | 0.0004 | -0.0177 | 0.0181 | -17.7980 | 11 | 2 | -84.2114 | 316.7498 | -1.4742 | -1.2014 | 0.5000 | 0 | 0 |
| bears_bulls_impulse_signals | default | 1 | 14294.0000 | 1299.4545 | 6.5916 | 0.0021 | -0.0151 | 0.0172 | -19.6839 | 11 | 3 | -110.7511 | 328.6657 | -1.3731 | -1.0277 | 0.4725 | 0 | 0 |
| fisher_transform_signals | double | 1 | 37484.0000 | 3407.6364 | 3.4824 | 0.0117 | -0.0059 | 0.0176 | -20.2603 | 11 | 3 | -77.3718 | 327.9334 | -1.4112 | -0.9869 | 0.0150 | 0 | 0 |
| qqe_mod_signals | half | 1 | 13914.0000 | 1264.9091 | 5.5086 | 0.0010 | -0.0167 | 0.0176 | -21.0719 | 11 | 3 | -89.1800 | 340.0985 | -1.8122 | -1.2416 | 0.4650 | 0 | 0 |
| fx_sniper_ergodic_cci_signals | half | 1 | 27232.0000 | 2475.6364 | 4.2978 | 0.0090 | -0.0086 | 0.0176 | -21.1693 | 11 | 4 | -108.2346 | 309.2099 | -1.3968 | -1.1221 | 0.1375 | 0 | 0 |
| fisher_transform_signals | default | 1 | 39540.0000 | 3594.5455 | 3.3702 | 0.0117 | -0.0059 | 0.0176 | -21.2332 | 11 | 3 | -111.6545 | 341.5971 | -1.1640 | -0.9748 | 0.0125 | 0 | 0 |
| coral_signals | double | 1 | 14804.0000 | 1345.8182 | 5.2339 | 0.0018 | -0.0158 | 0.0175 | -21.2561 | 11 | 3 | -96.4950 | 376.9428 | -1.5625 | -1.2852 | 0.4125 | 0 | 0 |
| bears_bulls_impulse_signals | half | 1 | 14072.0000 | 1279.2727 | 6.4104 | -0.0009 | -0.0180 | 0.0171 | -22.9833 | 11 | 2 | -86.6628 | 352.7242 | -1.8748 | -1.1589 | 0.5550 | 0 | 0 |
| linreg_slope_signals | half | 1 | 18290.0000 | 1662.7273 | 5.5909 | 0.0035 | -0.0140 | 0.0175 | -23.3231 | 11 | 4 | -127.4456 | 390.2730 | -1.5306 | -1.1683 | 0.3575 | 0 | 0 |
| vortex_signals | half | 1 | 21700.0000 | 1972.7273 | 4.6184 | 0.0050 | -0.0126 | 0.0176 | -24.8180 | 11 | 4 | -107.7616 | 395.5706 | -1.5278 | -1.2272 | 0.2625 | 0 | 0 |
| center_of_gravity_signals | double | 1 | 19188.0000 | 1744.3636 | 4.6914 | 0.0021 | -0.0155 | 0.0177 | -27.1004 | 11 | 2 | -104.5978 | 419.1746 | -2.0021 | -1.4953 | 0.4375 | 0 | 0 |
| rex_oscillator_signals | half | 1 | 30826.0000 | 2802.3636 | 3.5705 | 0.0054 | -0.0121 | 0.0175 | -33.7765 | 11 | 3 | -113.9162 | 475.4996 | -1.8136 | -1.8652 | 0.1800 | 0 | 0 |
| center_of_gravity_signals | default | 1 | 28770.0000 | 2615.4545 | 3.9579 | 0.0032 | -0.0146 | 0.0178 | -38.1870 | 11 | 3 | -112.8012 | 458.6414 | -1.9321 | -1.8298 | 0.3475 | 0 | 0 |
| coral_signals | default | 1 | 29666.0000 | 2696.9091 | 3.8135 | 0.0035 | -0.0142 | 0.0176 | -38.2456 | 11 | 4 | -128.5101 | 490.0746 | -2.0409 | -1.9577 | 0.3350 | 0 | 0 |
| fisher_transform_signals | half | 1 | 43934.0000 | 3994.0000 | 3.1168 | 0.0072 | -0.0105 | 0.0176 | -41.8343 | 11 | 3 | -116.1688 | 506.9537 | -2.8359 | -1.8849 | 0.0800 | 0 | 0 |
| relative_vigor_index_signals | double | 1 | 27908.0000 | 2537.0909 | 3.0787 | -0.0013 | -0.0191 | 0.0177 | -48.4392 | 11 | 0 | -98.3765 | 563.5490 | -4.6577 | -3.1475 | 0.6000 | 0 | 0 |
| relative_vigor_index_signals | default | 1 | 28118.0000 | 2556.1818 | 3.1091 | -0.0026 | -0.0202 | 0.0176 | -51.6479 | 11 | 2 | -135.4273 | 620.0778 | -2.8089 | -3.8501 | 0.6100 | 0 | 0 |
| relative_vigor_index_signals | half | 1 | 30146.0000 | 2740.5455 | 3.2542 | -0.0025 | -0.0200 | 0.0176 | -54.8785 | 11 | 2 | -128.4973 | 687.3521 | -3.0136 | -3.1804 | 0.6950 | 0 | 0 |
| coral_signals | half | 1 | 56812.0000 | 5164.7273 | 2.4823 | 0.0067 | -0.0108 | 0.0175 | -55.7027 | 11 | 2 | -171.3608 | 694.8855 | -2.6006 | -2.5585 | 0.0400 | 0 | 0 |
| rex_oscillator_signals | double | 1 | 36616.0000 | 3328.7273 | 2.7317 | 0.0003 | -0.0175 | 0.0177 | -58.1578 | 11 | 2 | -166.5590 | 678.4539 | -3.2451 | -3.3213 | 0.4625 | 0 | 0 |
| center_of_gravity_signals | half | 1 | 45002.0000 | 4091.0909 | 2.9845 | 0.0021 | -0.0155 | 0.0176 | -63.4633 | 11 | 2 | -142.2786 | 705.5983 | -3.1244 | -3.1253 | 0.3350 | 0 | 0 |


**0 of 117 candidate-settings clear the empirical best-of-39 floor; 3 clear the alone floor.** 11 of 117 have a positive net R per year.


### C1 — `jack`, stability across the three settings

`sign_agree = 1` means all three settings agree on the sign of net R per year. A candidate positive on one setting and negative on two is being fitted, not measured.

| indicator | settings | settings_positive | sign_agree | R_per_year_min | R_per_year_med | R_per_year_max | spread |
|---|---:|---:|---:|---:|---:|---:|---:|
| ichimoku_signals | 3 | 2 | 0 | -0.8862 | 3.5606 | 7.4431 | 8.3293 |
| halftrend_signals | 3 | 2 | 0 | -5.7103 | 0.3762 | 0.5052 | 6.2155 |
| schaff_trend_cycle_signals | 3 | 2 | 0 | -6.6140 | 0.2119 | 6.2243 | 12.8383 |
| aroon_signals | 3 | 1 | 0 | -2.0929 | -1.4179 | 0.6551 | 2.7480 |
| waddah_attar_explosion_signals | 3 | 0 | 1 | -3.3755 | -1.5998 | -1.3627 | 2.0127 |
| polychromatic_momentum_signals | 3 | 0 | 1 | -12.6095 | -2.1099 | -0.6842 | 11.9253 |
| mama_fama_signals | 3 | 0 | 1 | -3.8553 | -2.5234 | -2.5190 | 1.3363 |
| dpo_signals | 3 | 0 | 1 | -9.7370 | -2.5248 | -2.2030 | 7.5341 |
| donchian_breakout_signals | 3 | 0 | 1 | -3.6272 | -2.7275 | -1.7930 | 1.8341 |
| ehlers_reverse_ema_signals | 3 | 0 | 1 | -4.8028 | -3.3587 | -0.3904 | 4.4123 |
| j_tpo_signals | 3 | 0 | 1 | -6.1768 | -4.0461 | -3.6676 | 2.5092 |
| laguerre_filter_signals | 3 | 0 | 1 | -5.1420 | -4.2516 | -2.4170 | 2.7250 |
| supertrend_signals | 3 | 0 | 1 | -6.3522 | -4.4754 | -3.9885 | 2.3638 |
| price_momentum_oscillator_signals | 3 | 0 | 1 | -8.5557 | -5.0397 | -4.4900 | 4.0657 |
| volatility_quality_signals | 3 | 1 | 0 | -12.7980 | -5.1167 | 1.3576 | 14.1556 |
| kalman_filter_signals | 3 | 0 | 1 | -9.8666 | -5.2631 | -1.7270 | 8.1396 |
| chandelier_exit_signals | 3 | 0 | 1 | -7.3835 | -5.2894 | -3.8081 | 3.5755 |
| linreg_slope_signals | 3 | 0 | 1 | -23.3231 | -6.0630 | -5.8627 | 17.4604 |
| lemantrend_signals | 3 | 0 | 1 | -8.9332 | -6.4075 | -3.8790 | 5.0542 |
| dspo_signals | 3 | 1 | 0 | -7.6365 | -6.4678 | 1.7172 | 9.3538 |
| trend_direction_force_index_signals | 3 | 1 | 0 | -8.9921 | -6.9600 | 0.4187 | 9.4108 |
| glitch_index_signals | 3 | 0 | 1 | -7.7541 | -7.2643 | -0.5169 | 7.2372 |
| hieken_ashi_smoothed_signals | 3 | 0 | 1 | -14.5309 | -7.3456 | -3.2595 | 11.2714 |
| adx_dmi_signals | 3 | 1 | 0 | -12.9456 | -7.7672 | 0.0711 | 13.0166 |
| kuskus_starlight_signals | 3 | 0 | 1 | -8.9374 | -7.9799 | -1.6252 | 7.3122 |
| coppock_curve_signals | 3 | 0 | 1 | -8.4290 | -8.1347 | -4.2069 | 4.2221 |
| vortex_signals | 3 | 0 | 1 | -24.8180 | -8.7516 | -5.9675 | 18.8504 |
| ssl_channel_signals | 3 | 0 | 1 | -15.7059 | -9.4276 | -6.4943 | 9.2116 |
| qqe_mod_signals | 3 | 0 | 1 | -21.0719 | -10.0032 | -2.9225 | 18.1493 |
| parabolic_sar_signals | 3 | 0 | 1 | -11.8649 | -10.3394 | -8.7146 | 3.1503 |
| kase_peak_oscillator_signals | 3 | 0 | 1 | -10.9038 | -10.6803 | -7.6934 | 3.2104 |
| didi_index_signals | 3 | 0 | 1 | -17.7980 | -12.0382 | -9.8458 | 7.9522 |
| fx_sniper_ergodic_cci_signals | 3 | 0 | 1 | -21.1693 | -16.0915 | -15.6394 | 5.5300 |
| bears_bulls_impulse_signals | 3 | 0 | 1 | -22.9833 | -19.6839 | -8.1092 | 14.8741 |
| fisher_transform_signals | 3 | 0 | 1 | -41.8343 | -21.2332 | -20.2603 | 21.5740 |
| rex_oscillator_signals | 3 | 0 | 1 | -58.1578 | -33.7765 | -15.2050 | 42.9527 |
| center_of_gravity_signals | 3 | 0 | 1 | -63.4633 | -38.1870 | -27.1004 | 36.3629 |
| coral_signals | 3 | 0 | 1 | -55.7027 | -38.2456 | -21.2561 | 34.4466 |
| relative_vigor_index_signals | 3 | 0 | 1 | -54.8785 | -51.6479 | -48.4392 | 6.4392 |


**31 of 39 candidates have all three settings agreeing in sign.**


## C1 — `textbook`, fixed settings, unseen trade years 2005-2015

Empirical yearly-t floors **from the random-entry null**: alone **0.471**, best-of-39 **2.049**. The analytic equivalents on 11 yearly observations are 1.812 and 3.973 — the empirical ones are lower because the analytic formula assumes a **zero-mean** null while the real null also pays costs, so it is centred below zero.

| indicator | setting | distinct_setting | n_entered | trades_per_year | mean_bars | R_gross_per_trade | R_net_per_trade | cost_per_trade | R_net_per_year | years | years_positive | worst_year | worst_dip_R | t_yearly | t_block_boot | null_p | clears_alone_emp | clears_family_emp |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ichimoku_signals | half | 1 | 3376.0000 | 306.9091 | 5.5237 | 0.0403 | 0.0224 | 0.0179 | 6.8717 | 11 | 5 | -18.5660 | 56.0458 | 1.0638 | 0.8709 | 0.0700 | 1 | 0 |
| ichimoku_signals | default | 1 | 3044.0000 | 276.7273 | 5.4941 | 0.0346 | 0.0163 | 0.0183 | 4.4985 | 11 | 7 | -18.1706 | 77.4432 | 0.9198 | 0.5444 | 0.0950 | 1 | 0 |
| kalman_filter_signals | half | 1 | 7352.0000 | 668.3636 | 5.4351 | 0.0220 | 0.0040 | 0.0179 | 2.6885 | 11 | 5 | -45.9637 | 106.9643 | 0.3077 | 0.2261 | 0.0875 | 0 | 0 |
| mama_fama_signals | default | 1 | 6794.0000 | 617.6364 | 5.2984 | 0.0203 | 0.0025 | 0.0178 | 1.5303 | 11 | 8 | -36.9891 | 88.6298 | 0.2083 | 0.1390 | 0.1225 | 0 | 0 |
| schaff_trend_cycle_signals | half | 1 | 6242.0000 | 567.4545 | 4.8887 | 0.0194 | 0.0019 | 0.0175 | 1.0927 | 11 | 5 | -27.8666 | 132.4232 | 0.1360 | 0.1075 | 0.1425 | 0 | 0 |
| schaff_trend_cycle_signals | default | 1 | 5992.0000 | 544.7273 | 4.9321 | 0.0192 | 0.0019 | 0.0173 | 1.0461 | 11 | 5 | -25.8044 | 108.1635 | 0.1469 | 0.1013 | 0.1150 | 0 | 0 |
| dspo_signals | half | 1 | 9556.0000 | 868.7273 | 5.0911 | 0.0188 | 0.0011 | 0.0177 | 0.9647 | 11 | 7 | -54.5018 | 129.7035 | 0.1012 | 0.0769 | 0.0750 | 0 | 0 |
| halftrend_signals | default | 1 | 722.0000 | 65.6364 | 5.1828 | 0.0302 | 0.0132 | 0.0170 | 0.8657 | 11 | 7 | -11.2077 | 21.6044 | 0.5331 | 0.3947 | 0.2150 | 1 | 0 |
| laguerre_filter_signals | half | 1 | 9486.0000 | 862.3636 | 5.1939 | 0.0181 | 0.0005 | 0.0176 | 0.3934 | 11 | 6 | -44.4029 | 129.0515 | 0.0430 | 0.0311 | 0.1025 | 0 | 0 |
| linreg_slope_signals | default | 1 | 10156.0000 | 923.2727 | 5.4623 | 0.0178 | 0.0002 | 0.0176 | 0.1876 | 11 | 6 | -60.6964 | 160.8545 | 0.0158 | 0.0131 | 0.1050 | 0 | 0 |
| ichimoku_signals | double | 1 | 4320.0000 | 392.7273 | 5.3329 | 0.0172 | -0.0006 | 0.0178 | -0.2514 | 11 | 5 | -17.4160 | 76.9902 | -0.0415 | -0.0329 | 0.2300 | 0 | 0 |
| halftrend_signals | double | 1 | 374.0000 | 34.0000 | 5.1524 | 0.0085 | -0.0079 | 0.0165 | -0.2693 | 11 | 3 | -7.3129 | 25.3453 | -0.1851 | -0.1498 | 0.3975 | 0 | 0 |
| volatility_quality_signals | default | 1 | 7576.0000 | 688.7273 | 5.4464 | 0.0164 | -0.0008 | 0.0172 | -0.5815 | 11 | 6 | -34.9517 | 124.0685 | -0.0717 | -0.0545 | 0.1150 | 0 | 0 |
| adx_dmi_signals | double | 1 | 152.0000 | 13.8182 | 4.9342 | -0.0497 | -0.0638 | 0.0140 | -0.8811 | 11 | 2 | -3.9332 | 12.8870 | -1.4289 | -0.9586 | 0.6425 | 0 | 0 |
| ehlers_reverse_ema_signals | default | 1 | 8438.0000 | 767.0909 | 5.2533 | 0.0163 | -0.0014 | 0.0178 | -1.0977 | 11 | 5 | -54.9864 | 141.2055 | -0.1109 | -0.0874 | 0.1150 | 0 | 0 |
| polychromatic_momentum_signals | default | 1 | 6422.0000 | 583.8182 | 5.2541 | 0.0151 | -0.0029 | 0.0180 | -1.6957 | 11 | 4 | -40.9430 | 125.4913 | -0.1829 | -0.1501 | 0.1600 | 0 | 0 |
| waddah_attar_explosion_signals | half | 1 | 3596.0000 | 326.9091 | 4.8348 | 0.0119 | -0.0057 | 0.0177 | -1.8790 | 11 | 4 | -19.4575 | 77.7783 | -0.2881 | -0.3701 | 0.3325 | 0 | 0 |
| donchian_breakout_signals | default | 1 | 3740.0000 | 340.0000 | 5.4511 | 0.0113 | -0.0059 | 0.0172 | -2.0118 | 11 | 4 | -13.6114 | 63.4781 | -0.5638 | -0.2876 | 0.3200 | 0 | 0 |
| didi_index_signals | default | 1 | 9074.0000 | 824.9091 | 5.1417 | 0.0152 | -0.0024 | 0.0177 | -2.0191 | 11 | 5 | -44.2288 | 130.9852 | -0.2192 | -0.1574 | 0.1225 | 0 | 0 |
| glitch_index_signals | half | 1 | 8086.0000 | 735.0909 | 5.4149 | 0.0146 | -0.0028 | 0.0175 | -2.0796 | 11 | 4 | -42.5639 | 136.2049 | -0.1887 | -0.1538 | 0.1550 | 0 | 0 |
| coppock_curve_signals | double | 1 | 6064.0000 | 551.2727 | 5.3621 | 0.0139 | -0.0041 | 0.0179 | -2.2341 | 11 | 4 | -34.9108 | 101.5341 | -0.2507 | -0.2068 | 0.2075 | 0 | 0 |
| lemantrend_signals | double | 1 | 3160.0000 | 287.2727 | 4.7810 | 0.0094 | -0.0083 | 0.0177 | -2.3745 | 11 | 4 | -21.8804 | 57.4254 | -0.4679 | -0.5352 | 0.3425 | 0 | 0 |
| parabolic_sar_signals | default | 1 | 14826.0000 | 1347.8182 | 4.9635 | 0.0155 | -0.0020 | 0.0175 | -2.7134 | 11 | 6 | -63.4813 | 167.4409 | -0.2528 | -0.1742 | 0.0625 | 0 | 0 |
| ssl_channel_signals | default | 1 | 12948.0000 | 1177.0909 | 5.1978 | 0.0150 | -0.0024 | 0.0174 | -2.7674 | 11 | 4 | -51.9012 | 194.9631 | -0.2589 | -0.1883 | 0.0950 | 0 | 0 |
| waddah_attar_explosion_signals | double | 1 | 3576.0000 | 325.0909 | 4.7176 | 0.0090 | -0.0086 | 0.0176 | -2.8043 | 11 | 4 | -22.3133 | 79.6536 | -0.4686 | -0.6194 | 0.2825 | 0 | 0 |
| laguerre_filter_signals | double | 1 | 2156.0000 | 196.0000 | 5.0928 | 0.0032 | -0.0143 | 0.0176 | -2.8072 | 11 | 5 | -27.2335 | 84.5891 | -0.6969 | -0.6157 | 0.4175 | 0 | 0 |
| trend_direction_force_index_signals | double | 1 | 5472.0000 | 497.4545 | 5.2423 | 0.0114 | -0.0059 | 0.0174 | -2.9372 | 11 | 5 | -46.2143 | 89.8381 | -0.3421 | -0.3135 | 0.2575 | 0 | 0 |
| hieken_ashi_smoothed_signals | half | 1 | 11606.0000 | 1055.0909 | 5.0150 | 0.0148 | -0.0028 | 0.0176 | -2.9598 | 11 | 7 | -64.7855 | 177.1268 | -0.2461 | -0.1986 | 0.1275 | 0 | 0 |
| mama_fama_signals | double | 1 | 3232.0000 | 293.8182 | 5.4505 | 0.0067 | -0.0110 | 0.0177 | -3.2440 | 11 | 3 | -27.5184 | 86.8506 | -0.5857 | -0.4756 | 0.3950 | 0 | 0 |
| lemantrend_signals | default | 1 | 4324.0000 | 393.0909 | 4.6094 | 0.0094 | -0.0084 | 0.0178 | -3.3084 | 11 | 4 | -16.7869 | 57.2385 | -0.8666 | -0.6923 | 0.3475 | 0 | 0 |
| j_tpo_signals | half | 1 | 8280.0000 | 752.7273 | 5.1732 | 0.0134 | -0.0045 | 0.0179 | -3.3531 | 11 | 5 | -34.0671 | 137.5553 | -0.3830 | -0.2759 | 0.1600 | 0 | 0 |
| didi_index_signals | half | 1 | 11050.0000 | 1004.5455 | 4.9052 | 0.0143 | -0.0034 | 0.0177 | -3.4304 | 11 | 5 | -59.6130 | 153.7890 | -0.3492 | -0.2556 | 0.1075 | 0 | 0 |
| price_momentum_oscillator_signals | double | 1 | 2560.0000 | 232.7273 | 5.3156 | 0.0028 | -0.0151 | 0.0180 | -3.5222 | 11 | 4 | -18.0487 | 66.9901 | -0.8448 | -0.6530 | 0.4400 | 0 | 0 |
| aroon_signals | half | 1 | 11974.0000 | 1088.5455 | 4.9303 | 0.0143 | -0.0033 | 0.0176 | -3.6015 | 11 | 4 | -61.1929 | 197.5994 | -0.3050 | -0.2574 | 0.1200 | 0 | 0 |
| j_tpo_signals | double | 1 | 2026.0000 | 184.1818 | 5.2981 | -0.0022 | -0.0197 | 0.0175 | -3.6273 | 11 | 3 | -21.1568 | 62.9069 | -1.3210 | -0.8160 | 0.4725 | 0 | 0 |
| mama_fama_signals | half | 1 | 14884.0000 | 1353.0909 | 4.4889 | 0.0148 | -0.0028 | 0.0176 | -3.7441 | 11 | 5 | -45.3838 | 148.8553 | -0.4769 | -0.2707 | 0.0775 | 0 | 0 |
| linreg_slope_signals | double | 1 | 5392.0000 | 490.1818 | 5.4870 | 0.0097 | -0.0079 | 0.0176 | -3.8495 | 11 | 5 | -37.8565 | 86.5649 | -0.5908 | -0.4370 | 0.3400 | 0 | 0 |
| ehlers_reverse_ema_signals | half | 1 | 11006.0000 | 1000.5455 | 5.1133 | 0.0138 | -0.0039 | 0.0177 | -3.9178 | 11 | 5 | -84.1969 | 185.3270 | -0.3368 | -0.2796 | 0.0975 | 0 | 0 |
| j_tpo_signals | default | 1 | 4286.0000 | 389.6364 | 5.2846 | 0.0069 | -0.0107 | 0.0176 | -4.1651 | 11 | 5 | -59.4928 | 119.5678 | -0.4720 | -0.4606 | 0.3175 | 0 | 0 |
| adx_dmi_signals | default | 1 | 2104.0000 | 191.2727 | 4.6288 | -0.0057 | -0.0218 | 0.0161 | -4.1671 | 11 | 3 | -13.8971 | 63.0717 | -2.8858 | -1.0871 | 0.5875 | 0 | 0 |
| coppock_curve_signals | default | 1 | 8022.0000 | 729.2727 | 5.3257 | 0.0121 | -0.0057 | 0.0178 | -4.1718 | 11 | 5 | -38.3500 | 155.8461 | -0.4042 | -0.3437 | 0.2100 | 0 | 0 |
| donchian_breakout_signals | double | 1 | 1934.0000 | 175.8182 | 5.1499 | -0.0066 | -0.0241 | 0.0175 | -4.2298 | 11 | 3 | -23.8550 | 67.7126 | -0.8783 | -0.7693 | 0.6375 | 0 | 0 |
| chandelier_exit_signals | default | 1 | 5154.0000 | 468.5455 | 5.3661 | 0.0068 | -0.0097 | 0.0165 | -4.5631 | 11 | 4 | -20.0999 | 76.3541 | -1.3535 | -0.5513 | 0.3500 | 0 | 0 |
| qqe_mod_signals | default | 1 | 10190.0000 | 926.3636 | 5.0241 | 0.0128 | -0.0050 | 0.0178 | -4.6537 | 11 | 4 | -63.3460 | 182.7008 | -0.4600 | -0.3517 | 0.1400 | 0 | 0 |
| aroon_signals | double | 1 | 3286.0000 | 298.7273 | 5.1117 | 0.0020 | -0.0161 | 0.0180 | -4.8026 | 11 | 4 | -20.6940 | 97.8025 | -1.0650 | -0.7840 | 0.4175 | 0 | 0 |
| parabolic_sar_signals | double | 1 | 9640.0000 | 876.3636 | 5.2644 | 0.0120 | -0.0056 | 0.0176 | -4.8833 | 11 | 3 | -44.8287 | 160.3751 | -0.5773 | -0.3907 | 0.1625 | 0 | 0 |
| kalman_filter_signals | default | 1 | 5138.0000 | 467.0909 | 5.4192 | 0.0075 | -0.0105 | 0.0179 | -4.8970 | 11 | 4 | -42.3140 | 118.5537 | -0.5991 | -0.4750 | 0.3300 | 0 | 0 |
| aroon_signals | default | 1 | 6310.0000 | 573.6364 | 5.2727 | 0.0093 | -0.0086 | 0.0179 | -4.9469 | 11 | 6 | -30.7137 | 105.0362 | -0.9249 | -0.5440 | 0.2775 | 0 | 0 |
| waddah_attar_explosion_signals | default | 1 | 3586.0000 | 326.0000 | 4.7786 | 0.0015 | -0.0161 | 0.0176 | -5.2482 | 11 | 4 | -25.7818 | 82.4005 | -0.8803 | -1.1276 | 0.4475 | 0 | 0 |
| ssl_channel_signals | double | 1 | 9140.0000 | 830.9091 | 5.4323 | 0.0111 | -0.0066 | 0.0177 | -5.4860 | 11 | 4 | -68.5289 | 167.9271 | -0.6170 | -0.4469 | 0.2100 | 0 | 0 |
| qqe_mod_signals | double | 1 | 7360.0000 | 669.0909 | 5.1599 | 0.0093 | -0.0087 | 0.0180 | -5.8344 | 11 | 2 | -44.9519 | 171.3736 | -0.6834 | -0.5158 | 0.2900 | 0 | 0 |
| hieken_ashi_smoothed_signals | default | 1 | 9104.0000 | 827.6364 | 5.2279 | 0.0106 | -0.0072 | 0.0178 | -5.9551 | 11 | 5 | -59.0793 | 183.5677 | -0.5232 | -0.4211 | 0.2100 | 0 | 0 |
| glitch_index_signals | double | 1 | 5122.0000 | 465.6364 | 5.4428 | 0.0048 | -0.0129 | 0.0178 | -6.0184 | 11 | 5 | -47.7674 | 134.8325 | -0.6529 | -0.6397 | 0.4450 | 0 | 0 |
| price_momentum_oscillator_signals | half | 1 | 5368.0000 | 488.0000 | 5.3430 | 0.0051 | -0.0126 | 0.0178 | -6.1656 | 11 | 4 | -27.6228 | 98.7190 | -1.5183 | -0.7244 | 0.4475 | 0 | 0 |
| halftrend_signals | half | 1 | 1196.0000 | 108.7273 | 4.9933 | -0.0427 | -0.0596 | 0.0169 | -6.4833 | 11 | 2 | -13.6710 | 79.2400 | -3.4318 | -2.1189 | 0.9100 | 0 | 0 |
| chandelier_exit_signals | half | 1 | 4728.0000 | 429.8182 | 5.5089 | 0.0019 | -0.0152 | 0.0171 | -6.5336 | 11 | 3 | -22.7992 | 92.2152 | -1.8464 | -0.8180 | 0.4350 | 0 | 0 |
| hieken_ashi_smoothed_signals | double | 1 | 6068.0000 | 551.6364 | 5.2754 | 0.0055 | -0.0119 | 0.0173 | -6.5386 | 11 | 5 | -49.5119 | 133.0413 | -0.8164 | -0.6963 | 0.3875 | 0 | 0 |
| ehlers_reverse_ema_signals | double | 1 | 6328.0000 | 575.2727 | 5.2747 | 0.0063 | -0.0116 | 0.0178 | -6.6574 | 11 | 6 | -42.5434 | 116.4942 | -1.2293 | -0.6994 | 0.3600 | 0 | 0 |
| bears_bulls_impulse_signals | double | 1 | 12344.0000 | 1122.1818 | 5.4441 | 0.0113 | -0.0060 | 0.0173 | -6.6880 | 11 | 4 | -66.3398 | 182.6328 | -0.5522 | -0.4704 | 0.1775 | 0 | 0 |
| dspo_signals | double | 1 | 2480.0000 | 225.4545 | 5.1819 | -0.0141 | -0.0319 | 0.0179 | -7.1999 | 11 | 3 | -28.8867 | 90.9497 | -1.9594 | -1.4631 | 0.7300 | 0 | 0 |
| donchian_breakout_signals | half | 1 | 6562.0000 | 596.5455 | 5.5635 | 0.0050 | -0.0123 | 0.0173 | -7.3494 | 11 | 4 | -27.9984 | 139.7468 | -1.6924 | -0.7252 | 0.4175 | 0 | 0 |
| supertrend_signals | half | 1 | 4150.0000 | 377.2727 | 5.4571 | -0.0026 | -0.0200 | 0.0174 | -7.5468 | 11 | 2 | -25.4535 | 104.3375 | -2.4900 | -1.0280 | 0.5450 | 0 | 0 |
| dpo_signals | double | 1 | 4882.0000 | 443.8182 | 3.4738 | 0.0009 | -0.0170 | 0.0179 | -7.5606 | 11 | 4 | -28.8208 | 102.6639 | -1.6865 | -1.3394 | 0.5100 | 0 | 0 |
| trend_direction_force_index_signals | half | 1 | 13020.0000 | 1183.6364 | 5.3717 | 0.0111 | -0.0065 | 0.0176 | -7.6946 | 11 | 4 | -50.5764 | 198.2578 | -0.6909 | -0.4832 | 0.1675 | 0 | 0 |
| volatility_quality_signals | double | 1 | 2600.0000 | 236.3636 | 5.3450 | -0.0162 | -0.0330 | 0.0169 | -7.8029 | 11 | 2 | -15.2942 | 105.5792 | -3.2661 | -1.5033 | 0.7925 | 0 | 0 |
| polychromatic_momentum_signals | half | 1 | 12502.0000 | 1136.5455 | 4.8035 | 0.0108 | -0.0070 | 0.0178 | -7.9376 | 11 | 6 | -86.3880 | 215.5453 | -0.6468 | -0.5518 | 0.1575 | 0 | 0 |
| laguerre_filter_signals | default | 1 | 4612.0000 | 419.2727 | 5.0906 | -0.0014 | -0.0190 | 0.0175 | -7.9491 | 11 | 3 | -48.3635 | 101.7020 | -1.1856 | -1.0197 | 0.5475 | 0 | 0 |
| coppock_curve_signals | half | 1 | 9956.0000 | 905.0909 | 5.0173 | 0.0089 | -0.0088 | 0.0177 | -7.9742 | 11 | 4 | -62.1833 | 173.8883 | -0.7970 | -0.6225 | 0.2275 | 0 | 0 |
| price_momentum_oscillator_signals | default | 1 | 3838.0000 | 348.9091 | 5.2788 | -0.0069 | -0.0245 | 0.0176 | -8.5624 | 11 | 3 | -28.8493 | 111.8433 | -1.8193 | -1.2384 | 0.6125 | 0 | 0 |
| kuskus_starlight_signals | half | 1 | 13146.0000 | 1195.0909 | 4.6676 | 0.0101 | -0.0072 | 0.0173 | -8.6120 | 11 | 4 | -49.1554 | 177.1798 | -1.3140 | -0.6388 | 0.1650 | 0 | 0 |
| dpo_signals | half | 1 | 11108.0000 | 1009.8182 | 3.6751 | 0.0094 | -0.0085 | 0.0180 | -8.6207 | 11 | 2 | -38.0638 | 184.3650 | -1.1050 | -0.8070 | 0.1400 | 0 | 0 |
| kase_peak_oscillator_signals | default | 1 | 8644.0000 | 785.8182 | 4.9365 | 0.0063 | -0.0110 | 0.0173 | -8.6278 | 11 | 4 | -62.4848 | 148.8546 | -1.3300 | -0.8314 | 0.3325 | 0 | 0 |
| supertrend_signals | default | 1 | 4030.0000 | 366.3636 | 5.3548 | -0.0066 | -0.0238 | 0.0172 | -8.7160 | 11 | 2 | -23.5413 | 114.5447 | -2.8631 | -1.1398 | 0.6475 | 0 | 0 |
| kuskus_starlight_signals | default | 1 | 9108.0000 | 828.0000 | 4.7067 | 0.0068 | -0.0106 | 0.0174 | -8.7682 | 11 | 4 | -30.7568 | 140.9441 | -2.0779 | -0.8346 | 0.2950 | 0 | 0 |
| kase_peak_oscillator_signals | double | 1 | 6300.0000 | 572.7273 | 4.9067 | 0.0020 | -0.0153 | 0.0173 | -8.7686 | 11 | 5 | -44.7609 | 139.3068 | -1.4096 | -1.0195 | 0.4175 | 0 | 0 |
| vortex_signals | double | 1 | 10948.0000 | 995.2727 | 3.8440 | 0.0094 | -0.0091 | 0.0186 | -9.1032 | 11 | 4 | -50.0964 | 177.1912 | -1.0184 | -0.7757 | 0.2050 | 0 | 0 |
| dspo_signals | default | 1 | 5078.0000 | 461.6364 | 5.2475 | -0.0019 | -0.0198 | 0.0178 | -9.1238 | 11 | 3 | -29.5921 | 134.8269 | -2.1255 | -1.2266 | 0.5375 | 0 | 0 |
| vortex_signals | default | 1 | 15290.0000 | 1390.0000 | 3.9057 | 0.0113 | -0.0066 | 0.0179 | -9.1946 | 11 | 4 | -65.3120 | 177.2178 | -0.7538 | -0.6681 | 0.0825 | 0 | 0 |
| trend_direction_force_index_signals | default | 1 | 8398.0000 | 763.4545 | 5.3406 | 0.0054 | -0.0122 | 0.0176 | -9.2995 | 11 | 3 | -50.9295 | 145.4843 | -0.8808 | -0.7848 | 0.3500 | 0 | 0 |
| kalman_filter_signals | double | 1 | 3688.0000 | 335.2727 | 5.2701 | -0.0102 | -0.0279 | 0.0177 | -9.3512 | 11 | 3 | -36.3286 | 120.7359 | -1.6199 | -1.4719 | 0.7475 | 0 | 0 |
| glitch_index_signals | default | 1 | 6788.0000 | 617.0909 | 5.4333 | 0.0015 | -0.0160 | 0.0174 | -9.8462 | 11 | 2 | -44.8973 | 133.0889 | -0.9947 | -0.9741 | 0.4900 | 0 | 0 |
| supertrend_signals | double | 1 | 3968.0000 | 360.7273 | 5.4040 | -0.0105 | -0.0275 | 0.0171 | -9.9281 | 11 | 2 | -27.1313 | 131.5819 | -2.5754 | -1.3941 | 0.7025 | 0 | 0 |
| chandelier_exit_signals | double | 1 | 7160.0000 | 650.9091 | 4.4802 | 0.0007 | -0.0154 | 0.0161 | -10.0260 | 11 | 3 | -31.9220 | 140.0349 | -1.7105 | -1.1434 | 0.4500 | 0 | 0 |
| schaff_trend_cycle_signals | double | 1 | 5568.0000 | 506.1818 | 5.0007 | -0.0031 | -0.0203 | 0.0172 | -10.2922 | 11 | 2 | -27.8081 | 173.7726 | -2.3783 | -1.2149 | 0.5650 | 0 | 0 |
| lemantrend_signals | half | 1 | 5822.0000 | 529.2727 | 4.3744 | -0.0021 | -0.0200 | 0.0179 | -10.5969 | 11 | 2 | -35.3442 | 128.2497 | -2.5465 | -1.9987 | 0.5550 | 0 | 0 |
| adx_dmi_signals | half | 1 | 14568.0000 | 1324.3636 | 4.0034 | 0.0080 | -0.0091 | 0.0171 | -12.0114 | 11 | 3 | -57.3278 | 234.0147 | -1.1907 | -0.9206 | 0.2250 | 0 | 0 |
| kase_peak_oscillator_signals | half | 1 | 12186.0000 | 1107.8182 | 4.7389 | 0.0059 | -0.0112 | 0.0172 | -12.4539 | 11 | 6 | -73.0779 | 236.2195 | -1.1785 | -0.9139 | 0.2975 | 0 | 0 |
| polychromatic_momentum_signals | double | 1 | 3220.0000 | 292.7273 | 5.1571 | -0.0259 | -0.0434 | 0.0175 | -12.7117 | 11 | 2 | -35.1896 | 161.8281 | -2.6600 | -2.1204 | 0.8525 | 0 | 0 |
| kuskus_starlight_signals | double | 1 | 6276.0000 | 570.5455 | 4.6933 | -0.0066 | -0.0239 | 0.0173 | -13.6479 | 11 | 3 | -48.4721 | 174.5542 | -2.0438 | -1.7042 | 0.6425 | 0 | 0 |
| volatility_quality_signals | half | 1 | 18824.0000 | 1711.2727 | 4.3490 | 0.0092 | -0.0080 | 0.0172 | -13.6707 | 11 | 4 | -64.6104 | 217.9098 | -1.6919 | -0.9030 | 0.1350 | 0 | 0 |
| fx_sniper_ergodic_cci_signals | double | 1 | 18036.0000 | 1639.6364 | 4.1660 | 0.0093 | -0.0086 | 0.0178 | -14.0353 | 11 | 5 | -61.7528 | 275.4231 | -1.2244 | -0.9384 | 0.1250 | 0 | 0 |
| dpo_signals | default | 1 | 7800.0000 | 709.0909 | 3.5219 | -0.0018 | -0.0198 | 0.0180 | -14.0369 | 11 | 2 | -37.5888 | 171.7418 | -2.5992 | -1.8092 | 0.5325 | 0 | 0 |
| parabolic_sar_signals | half | 1 | 21480.0000 | 1952.7273 | 4.2323 | 0.0100 | -0.0075 | 0.0175 | -14.6025 | 11 | 4 | -73.1893 | 261.9412 | -1.3815 | -0.8442 | 0.1200 | 0 | 0 |
| qqe_mod_signals | half | 1 | 13914.0000 | 1264.9091 | 4.6021 | 0.0040 | -0.0136 | 0.0176 | -17.2345 | 11 | 3 | -77.6980 | 286.8125 | -1.9240 | -1.1688 | 0.3600 | 0 | 0 |
| ssl_channel_signals | half | 1 | 18122.0000 | 1647.4545 | 4.5030 | 0.0065 | -0.0107 | 0.0172 | -17.6276 | 11 | 2 | -68.5338 | 288.1938 | -1.8059 | -1.0984 | 0.1825 | 0 | 0 |
| rex_oscillator_signals | default | 1 | 27810.0000 | 2528.1818 | 3.0096 | 0.0101 | -0.0074 | 0.0175 | -18.6208 | 11 | 2 | -74.8365 | 390.0768 | -1.0989 | -1.0064 | 0.0525 | 0 | 0 |
| fx_sniper_ergodic_cci_signals | default | 1 | 21636.0000 | 1966.9091 | 3.9708 | 0.0075 | -0.0101 | 0.0175 | -19.8162 | 11 | 4 | -77.1410 | 270.4081 | -1.7677 | -1.2642 | 0.1925 | 0 | 0 |
| vortex_signals | half | 1 | 21698.0000 | 1972.5455 | 3.7550 | 0.0068 | -0.0108 | 0.0176 | -21.2648 | 11 | 3 | -80.6508 | 338.5741 | -1.8113 | -1.2595 | 0.1975 | 0 | 0 |
| coral_signals | double | 1 | 14804.0000 | 1345.8182 | 4.5620 | 0.0016 | -0.0159 | 0.0175 | -21.4321 | 11 | 3 | -83.1359 | 359.5934 | -1.7036 | -1.4253 | 0.4575 | 0 | 0 |
| didi_index_signals | double | 1 | 11032.0000 | 1002.9091 | 4.4010 | -0.0036 | -0.0217 | 0.0181 | -21.7605 | 11 | 2 | -77.1784 | 324.9512 | -1.9720 | -1.6082 | 0.6300 | 0 | 0 |
| bears_bulls_impulse_signals | default | 1 | 15206.0000 | 1382.3636 | 5.2917 | 0.0013 | -0.0159 | 0.0172 | -21.9888 | 11 | 4 | -94.1721 | 339.5163 | -1.7052 | -1.2587 | 0.4600 | 0 | 0 |
| linreg_slope_signals | half | 1 | 18788.0000 | 1708.0000 | 4.5953 | 0.0038 | -0.0136 | 0.0175 | -23.3046 | 11 | 2 | -77.7377 | 359.6676 | -2.1564 | -1.3231 | 0.3400 | 0 | 0 |
| bears_bulls_impulse_signals | half | 1 | 15008.0000 | 1364.3636 | 5.2925 | -0.0014 | -0.0184 | 0.0170 | -25.0546 | 11 | 3 | -76.0201 | 344.5725 | -2.8129 | -1.4116 | 0.5950 | 0 | 0 |
| center_of_gravity_signals | double | 1 | 19188.0000 | 1744.3636 | 3.9436 | 0.0022 | -0.0155 | 0.0177 | -27.0297 | 11 | 2 | -96.9501 | 375.1473 | -2.2372 | -1.7222 | 0.4050 | 0 | 0 |
| fx_sniper_ergodic_cci_signals | half | 1 | 27232.0000 | 2475.6364 | 3.5619 | 0.0045 | -0.0131 | 0.0176 | -32.4426 | 11 | 2 | -84.0537 | 382.9142 | -2.9665 | -2.1250 | 0.2550 | 0 | 0 |
| fisher_transform_signals | double | 1 | 37484.0000 | 3407.6364 | 2.8254 | 0.0081 | -0.0096 | 0.0176 | -32.5922 | 11 | 2 | -80.9764 | 406.8004 | -3.2952 | -1.9666 | 0.0525 | 0 | 0 |
| fisher_transform_signals | default | 1 | 39540.0000 | 3594.5455 | 2.7409 | 0.0073 | -0.0103 | 0.0176 | -36.9129 | 11 | 2 | -83.4049 | 440.6019 | -3.2354 | -2.1540 | 0.0775 | 0 | 0 |
| center_of_gravity_signals | default | 1 | 28770.0000 | 2615.4545 | 3.4248 | 0.0028 | -0.0149 | 0.0178 | -39.0635 | 11 | 3 | -133.0537 | 469.8965 | -2.4299 | -2.1181 | 0.3400 | 0 | 0 |
| rex_oscillator_signals | half | 1 | 30826.0000 | 2802.3636 | 2.9935 | 0.0035 | -0.0140 | 0.0175 | -39.2171 | 11 | 1 | -103.8813 | 477.6991 | -3.3962 | -2.4827 | 0.2925 | 0 | 0 |
| fisher_transform_signals | half | 1 | 43934.0000 | 3994.0000 | 2.6176 | 0.0056 | -0.0120 | 0.0176 | -47.9483 | 11 | 1 | -101.9805 | 560.7287 | -4.3422 | -2.6018 | 0.1175 | 0 | 0 |
| relative_vigor_index_signals | double | 1 | 27908.0000 | 2537.0909 | 3.0272 | -0.0012 | -0.0190 | 0.0177 | -48.0886 | 11 | 1 | -108.0525 | 584.1634 | -3.7863 | -3.1358 | 0.6200 | 0 | 0 |
| relative_vigor_index_signals | half | 1 | 30146.0000 | 2740.5455 | 3.2077 | -0.0002 | -0.0177 | 0.0176 | -48.5937 | 11 | 2 | -121.7202 | 628.6494 | -2.5624 | -2.8201 | 0.5400 | 0 | 0 |
| coral_signals | default | 1 | 29666.0000 | 2696.9091 | 3.3952 | -0.0005 | -0.0181 | 0.0176 | -48.8638 | 11 | 4 | -144.9773 | 551.5170 | -2.9768 | -2.7983 | 0.5300 | 0 | 0 |
| relative_vigor_index_signals | default | 1 | 28118.0000 | 2556.1818 | 3.0839 | -0.0033 | -0.0209 | 0.0176 | -53.5193 | 11 | 2 | -165.7009 | 629.9468 | -2.8828 | -3.9781 | 0.6800 | 0 | 0 |
| coral_signals | half | 1 | 56812.0000 | 5164.7273 | 2.2595 | 0.0063 | -0.0112 | 0.0175 | -57.7418 | 11 | 1 | -191.5249 | 690.0026 | -2.5634 | -2.9553 | 0.0675 | 0 | 0 |
| rex_oscillator_signals | double | 1 | 36616.0000 | 3328.7273 | 2.5845 | -0.0019 | -0.0196 | 0.0177 | -65.2973 | 11 | 1 | -181.3948 | 741.4690 | -3.8521 | -4.0686 | 0.6275 | 0 | 0 |
| center_of_gravity_signals | half | 1 | 45002.0000 | 4091.0909 | 2.6766 | 0.0006 | -0.0171 | 0.0176 | -69.8601 | 11 | 2 | -159.5629 | 774.9679 | -4.0762 | -3.8407 | 0.4275 | 0 | 0 |


**0 of 117 candidate-settings clear the empirical best-of-39 floor; 3 clear the alone floor.** 10 of 117 have a positive net R per year.


### C1 — `textbook`, stability across the three settings

`sign_agree = 1` means all three settings agree on the sign of net R per year. A candidate positive on one setting and negative on two is being fitted, not measured.

| indicator | settings | settings_positive | sign_agree | R_per_year_min | R_per_year_med | R_per_year_max | spread |
|---|---:|---:|---:|---:|---:|---:|---:|
| ichimoku_signals | 3 | 2 | 0 | -0.2514 | 4.4985 | 6.8717 | 7.1232 |
| schaff_trend_cycle_signals | 3 | 2 | 0 | -10.2922 | 1.0461 | 1.0927 | 11.3848 |
| halftrend_signals | 3 | 1 | 0 | -6.4833 | -0.2693 | 0.8657 | 7.3490 |
| waddah_attar_explosion_signals | 3 | 0 | 1 | -5.2482 | -2.8043 | -1.8790 | 3.3692 |
| laguerre_filter_signals | 3 | 1 | 0 | -7.9491 | -2.8072 | 0.3934 | 8.3425 |
| mama_fama_signals | 3 | 1 | 0 | -3.7441 | -3.2440 | 1.5303 | 5.2743 |
| lemantrend_signals | 3 | 0 | 1 | -10.5969 | -3.3084 | -2.3745 | 8.2224 |
| didi_index_signals | 3 | 0 | 1 | -21.7605 | -3.4304 | -2.0191 | 19.7414 |
| j_tpo_signals | 3 | 0 | 1 | -4.1651 | -3.6273 | -3.3531 | 0.8119 |
| linreg_slope_signals | 3 | 1 | 0 | -23.3046 | -3.8495 | 0.1876 | 23.4922 |
| ehlers_reverse_ema_signals | 3 | 0 | 1 | -6.6574 | -3.9178 | -1.0977 | 5.5597 |
| adx_dmi_signals | 3 | 0 | 1 | -12.0114 | -4.1671 | -0.8811 | 11.1302 |
| coppock_curve_signals | 3 | 0 | 1 | -7.9742 | -4.1718 | -2.2341 | 5.7400 |
| donchian_breakout_signals | 3 | 0 | 1 | -7.3494 | -4.2298 | -2.0118 | 5.3376 |
| aroon_signals | 3 | 0 | 1 | -4.9469 | -4.8026 | -3.6015 | 1.3454 |
| parabolic_sar_signals | 3 | 0 | 1 | -14.6025 | -4.8833 | -2.7134 | 11.8891 |
| kalman_filter_signals | 3 | 1 | 0 | -9.3512 | -4.8970 | 2.6885 | 12.0397 |
| ssl_channel_signals | 3 | 0 | 1 | -17.6276 | -5.4860 | -2.7674 | 14.8602 |
| qqe_mod_signals | 3 | 0 | 1 | -17.2345 | -5.8344 | -4.6537 | 12.5808 |
| hieken_ashi_smoothed_signals | 3 | 0 | 1 | -6.5386 | -5.9551 | -2.9598 | 3.5788 |
| glitch_index_signals | 3 | 0 | 1 | -9.8462 | -6.0184 | -2.0796 | 7.7666 |
| price_momentum_oscillator_signals | 3 | 0 | 1 | -8.5624 | -6.1656 | -3.5222 | 5.0402 |
| chandelier_exit_signals | 3 | 0 | 1 | -10.0260 | -6.5336 | -4.5631 | 5.4629 |
| dspo_signals | 3 | 1 | 0 | -9.1238 | -7.1999 | 0.9647 | 10.0885 |
| trend_direction_force_index_signals | 3 | 0 | 1 | -9.2995 | -7.6946 | -2.9372 | 6.3623 |
| volatility_quality_signals | 3 | 0 | 1 | -13.6707 | -7.8029 | -0.5815 | 13.0892 |
| polychromatic_momentum_signals | 3 | 0 | 1 | -12.7117 | -7.9376 | -1.6957 | 11.0160 |
| dpo_signals | 3 | 0 | 1 | -14.0369 | -8.6207 | -7.5606 | 6.4763 |
| supertrend_signals | 3 | 0 | 1 | -9.9281 | -8.7160 | -7.5468 | 2.3813 |
| kuskus_starlight_signals | 3 | 0 | 1 | -13.6479 | -8.7682 | -8.6120 | 5.0358 |
| kase_peak_oscillator_signals | 3 | 0 | 1 | -12.4539 | -8.7686 | -8.6278 | 3.8262 |
| vortex_signals | 3 | 0 | 1 | -21.2648 | -9.1946 | -9.1032 | 12.1616 |
| fx_sniper_ergodic_cci_signals | 3 | 0 | 1 | -32.4426 | -19.8162 | -14.0353 | 18.4073 |
| bears_bulls_impulse_signals | 3 | 0 | 1 | -25.0546 | -21.9888 | -6.6880 | 18.3666 |
| fisher_transform_signals | 3 | 0 | 1 | -47.9483 | -36.9129 | -32.5922 | 15.3561 |
| center_of_gravity_signals | 3 | 0 | 1 | -69.8601 | -39.0635 | -27.0297 | 42.8304 |
| rex_oscillator_signals | 3 | 0 | 1 | -65.2973 | -39.2171 | -18.6208 | 46.6766 |
| relative_vigor_index_signals | 3 | 0 | 1 | -53.5193 | -48.5937 | -48.0886 | 5.4307 |
| coral_signals | 3 | 0 | 1 | -57.7418 | -48.8638 | -21.4321 | 36.3097 |


**31 of 39 candidates have all three settings agreeing in sign.**


---

# BASELINE — all 15 candidates


## BASELINE — `flip_only`, fixed settings, unseen trade years 2005-2015

Empirical yearly-t floors **from the random-entry null**: alone **-0.136**, best-of-15 **0.958**. The analytic equivalents on 11 yearly observations are 1.812 and 3.395 — the empirical ones are lower because the analytic formula assumes a **zero-mean** null while the real null also pays costs, so it is centred below zero.

| indicator | setting | distinct_setting | n_entered | trades_per_year | mean_bars | R_gross_per_trade | R_net_per_trade | cost_per_trade | R_net_per_year | years | years_positive | worst_year | worst_dip_R | t_yearly | t_block_boot | null_p | clears_alone_emp | clears_family_emp |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| hma_baseline | double | 1 | 23422.0000 | 2129.2727 | 6.7417 | 0.0208 | 0.0032 | 0.0176 | 6.8637 | 11 | 5 | -59.4803 | 237.9486 | 0.3740 | 0.1755 | 0.0100 | 1 | 0 |
| lsma_baseline | double | 1 | 20892.0000 | 1899.2727 | 7.5682 | 0.0191 | 0.0016 | 0.0175 | 3.0185 | 11 | 4 | -106.5735 | 322.6244 | 0.1483 | 0.0718 | 0.0350 | 1 | 0 |
| rma_baseline | double | 1 | 11116.0000 | 1010.5455 | 14.3311 | 0.0199 | 0.0025 | 0.0174 | 2.5261 | 11 | 6 | -309.0460 | 668.2210 | 0.0395 | 0.0404 | 0.1500 | 1 | 0 |
| mcginley_dynamic_index | double | 1 | 13030.0000 | 1184.5455 | 12.2163 | 0.0183 | 0.0006 | 0.0176 | 0.7428 | 11 | 6 | -190.7648 | 571.3350 | 0.0159 | 0.0123 | 0.1275 | 1 | 0 |
| ema_baseline | double | 1 | 15238.0000 | 1385.2727 | 10.3986 | 0.0162 | -0.0014 | 0.0176 | -1.9987 | 11 | 5 | -198.7773 | 604.1796 | -0.0453 | -0.0342 | 0.1100 | 1 | 0 |
| rma_baseline | default | 1 | 15564.0000 | 1414.9091 | 10.2313 | 0.0158 | -0.0017 | 0.0175 | -2.4643 | 11 | 5 | -206.9882 | 592.3319 | -0.0564 | -0.0414 | 0.1175 | 1 | 0 |
| sma_baseline | double | 1 | 13368.0000 | 1215.2727 | 11.8609 | 0.0156 | -0.0024 | 0.0180 | -2.9566 | 11 | 5 | -196.5947 | 650.5793 | -0.0669 | -0.0503 | 0.1925 | 1 | 0 |
| tma_baseline | double | 1 | 13042.0000 | 1185.6364 | 12.1463 | 0.0114 | -0.0064 | 0.0179 | -7.5965 | 11 | 6 | -186.2138 | 681.7911 | -0.1823 | -0.1296 | 0.2425 | 0 | 0 |
| fantail_vma | half | 0 | 24526.0000 | 2229.6364 | 6.4973 | 0.0126 | -0.0049 | 0.0175 | -11.0130 | 11 | 3 | -75.1746 | 334.2864 | -0.7125 | -0.3099 | 0.1050 | 0 | 0 |
| fantail_vma | default | 1 | 24526.0000 | 2229.6364 | 6.4973 | 0.0126 | -0.0049 | 0.0175 | -11.0130 | 11 | 3 | -75.1746 | 334.2864 | -0.7125 | -0.3099 | 0.1050 | 0 | 0 |
| lsma_baseline | default | 1 | 30906.0000 | 2809.6364 | 5.1499 | 0.0137 | -0.0040 | 0.0177 | -11.2738 | 11 | 3 | -75.2225 | 381.2984 | -0.6683 | -0.3273 | 0.0225 | 0 | 0 |
| t3_baseline | default | 1 | 24188.0000 | 2198.9091 | 6.4996 | 0.0116 | -0.0060 | 0.0176 | -13.1050 | 11 | 4 | -76.9359 | 360.3340 | -0.8038 | -0.3208 | 0.0850 | 0 | 0 |
| wma_baseline | default | 1 | 24184.0000 | 2198.5455 | 6.5750 | 0.0114 | -0.0061 | 0.0175 | -13.5189 | 11 | 5 | -113.0235 | 349.0916 | -0.5983 | -0.2928 | 0.1000 | 0 | 0 |
| t3_baseline | double | 1 | 15450.0000 | 1404.5455 | 9.9353 | 0.0078 | -0.0096 | 0.0175 | -13.5473 | 11 | 6 | -179.9485 | 494.4732 | -0.4239 | -0.2725 | 0.2175 | 0 | 0 |
| mcginley_dynamic_index | default | 1 | 18676.0000 | 1697.8182 | 8.5266 | 0.0092 | -0.0081 | 0.0173 | -13.7881 | 11 | 6 | -150.4921 | 428.7817 | -0.4290 | -0.2672 | 0.2025 | 0 | 0 |
| wma_baseline | double | 1 | 17344.0000 | 1576.7273 | 9.1207 | 0.0083 | -0.0094 | 0.0177 | -14.7843 | 11 | 6 | -170.5025 | 590.1612 | -0.4010 | -0.2791 | 0.2550 | 0 | 0 |
| kama_baseline | double | 1 | 17322.0000 | 1574.7273 | 9.1762 | 0.0065 | -0.0106 | 0.0172 | -16.7458 | 11 | 5 | -131.5737 | 405.2295 | -0.7044 | -0.3727 | 0.2775 | 0 | 0 |
| super_smoother_2pole_baseline | double | 1 | 23378.0000 | 2125.2727 | 6.8330 | 0.0087 | -0.0087 | 0.0175 | -18.5594 | 11 | 6 | -124.8354 | 387.3242 | -0.8910 | -0.4158 | 0.1450 | 0 | 0 |
| fantail_vma | double | 1 | 24272.0000 | 2206.5455 | 6.5652 | 0.0089 | -0.0087 | 0.0176 | -19.2052 | 11 | 3 | -72.8049 | 374.6090 | -1.5122 | -0.5319 | 0.1600 | 0 | 0 |
| sma_baseline | default | 1 | 19366.0000 | 1760.5455 | 8.2069 | 0.0065 | -0.0110 | 0.0175 | -19.2862 | 11 | 5 | -149.5681 | 409.9593 | -0.6898 | -0.4013 | 0.2300 | 0 | 0 |
| ema_baseline | default | 1 | 21644.0000 | 1967.6364 | 7.3421 | 0.0064 | -0.0110 | 0.0174 | -21.6907 | 11 | 5 | -158.0540 | 453.7865 | -0.7179 | -0.4430 | 0.2525 | 0 | 0 |
| tma_baseline | default | 1 | 18884.0000 | 1716.7273 | 8.4200 | 0.0048 | -0.0127 | 0.0175 | -21.7268 | 11 | 5 | -142.2636 | 449.7918 | -0.8619 | -0.4665 | 0.3500 | 0 | 0 |
| mcginley_dynamic_index | half | 1 | 26598.0000 | 2418.0000 | 5.9882 | 0.0081 | -0.0094 | 0.0174 | -22.6894 | 11 | 4 | -127.6829 | 410.6889 | -1.0042 | -0.5035 | 0.1625 | 0 | 0 |
| tma_baseline | half | 1 | 28444.0000 | 2585.8182 | 5.6032 | 0.0086 | -0.0089 | 0.0175 | -23.0191 | 11 | 3 | -90.5051 | 417.6664 | -1.5892 | -0.5785 | 0.1350 | 0 | 0 |
| rma_baseline | half | 1 | 22206.0000 | 2018.7273 | 7.1711 | 0.0060 | -0.0114 | 0.0174 | -23.0625 | 11 | 5 | -151.8057 | 457.1012 | -0.8020 | -0.4703 | 0.2575 | 0 | 0 |
| sma_baseline | half | 1 | 28062.0000 | 2551.0909 | 5.6786 | 0.0078 | -0.0098 | 0.0176 | -25.0252 | 11 | 4 | -99.9809 | 440.3386 | -1.5478 | -0.6147 | 0.1500 | 0 | 0 |
| frama_baseline | half | 1 | 25338.0000 | 2303.4545 | 6.2898 | 0.0061 | -0.0114 | 0.0174 | -26.1803 | 11 | 4 | -158.9703 | 566.3336 | -1.0492 | -0.5823 | 0.2225 | 0 | 0 |
| frama_baseline | default | 1 | 29300.0000 | 2663.6364 | 5.4358 | 0.0074 | -0.0101 | 0.0174 | -26.8174 | 11 | 4 | -135.5509 | 418.4003 | -1.8025 | -0.7948 | 0.1525 | 0 | 0 |
| vidya | half | 0 | 35846.0000 | 3258.7273 | 4.4323 | 0.0090 | -0.0084 | 0.0174 | -27.2766 | 11 | 2 | -92.0293 | 392.0324 | -2.4308 | -0.8482 | 0.0900 | 0 | 0 |
| vidya | default | 1 | 35846.0000 | 3258.7273 | 4.4323 | 0.0090 | -0.0084 | 0.0174 | -27.2766 | 11 | 2 | -92.0293 | 392.0324 | -2.4308 | -0.8482 | 0.0900 | 0 | 0 |
| ema_baseline | half | 1 | 30098.0000 | 2736.1818 | 5.2940 | 0.0070 | -0.0105 | 0.0175 | -28.7260 | 11 | 3 | -120.1018 | 464.2760 | -1.5453 | -0.6506 | 0.1600 | 0 | 0 |
| alma_baseline | double | 1 | 33304.0000 | 3027.6364 | 4.7829 | 0.0077 | -0.0099 | 0.0176 | -29.8685 | 11 | 3 | -105.2910 | 485.6353 | -2.0171 | -0.7868 | 0.1225 | 0 | 0 |
| wma_baseline | half | 1 | 34346.0000 | 3122.3636 | 4.6418 | 0.0077 | -0.0099 | 0.0176 | -30.9717 | 11 | 3 | -118.6660 | 487.2731 | -2.0629 | -0.8207 | 0.1150 | 0 | 0 |
| hma_baseline | default | 1 | 34910.0000 | 3173.6364 | 4.5561 | 0.0078 | -0.0100 | 0.0177 | -31.5931 | 11 | 3 | -166.9455 | 497.9502 | -1.5344 | -1.0188 | 0.1425 | 0 | 0 |
| vidya | double | 1 | 28558.0000 | 2596.1818 | 5.5367 | 0.0046 | -0.0127 | 0.0173 | -33.0665 | 11 | 2 | -99.0919 | 479.6926 | -2.4591 | -0.8512 | 0.2700 | 0 | 0 |
| kama_baseline | default | 1 | 23314.0000 | 2119.4545 | 6.8335 | 0.0015 | -0.0157 | 0.0172 | -33.2978 | 11 | 5 | -124.9881 | 524.4709 | -1.8142 | -0.8438 | 0.4450 | 0 | 0 |
| super_smoother_2pole_baseline | default | 1 | 35138.0000 | 3194.3636 | 4.5418 | 0.0069 | -0.0107 | 0.0176 | -34.1424 | 11 | 2 | -139.4959 | 490.5510 | -2.1452 | -0.9558 | 0.1750 | 0 | 0 |
| kama_baseline | half | 1 | 30684.0000 | 2789.4545 | 5.1944 | 0.0049 | -0.0125 | 0.0173 | -34.7442 | 11 | 2 | -107.7554 | 503.2659 | -2.8115 | -0.8937 | 0.2550 | 0 | 0 |
| frama_baseline | double | 1 | 27568.0000 | 2506.1818 | 5.7713 | 0.0034 | -0.0142 | 0.0175 | -35.4926 | 11 | 2 | -133.1577 | 494.5626 | -2.3662 | -1.0607 | 0.3400 | 0 | 0 |
| t3_baseline | half | 1 | 38870.0000 | 3533.6364 | 4.0904 | 0.0030 | -0.0146 | 0.0176 | -51.7028 | 11 | 3 | -216.5333 | 687.1515 | -2.2258 | -1.5631 | 0.3300 | 0 | 0 |
| alma_baseline | default | 1 | 49498.0000 | 4499.8182 | 3.2223 | 0.0041 | -0.0134 | 0.0176 | -60.4572 | 11 | 2 | -197.4371 | 739.3310 | -3.3351 | -1.8137 | 0.1925 | 0 | 0 |
| lsma_baseline | half | 1 | 46152.0000 | 4195.6364 | 3.4562 | 0.0018 | -0.0158 | 0.0176 | -66.4392 | 11 | 2 | -216.9050 | 898.9622 | -2.6116 | -2.2963 | 0.3375 | 0 | 0 |
| super_smoother_2pole_baseline | half | 1 | 51826.0000 | 4711.4545 | 3.0773 | -0.0004 | -0.0180 | 0.0176 | -84.5757 | 11 | 0 | -263.5060 | 996.9974 | -3.3493 | -2.6302 | 0.5275 | 0 | 0 |
| hma_baseline | half | 1 | 51390.0000 | 4671.8182 | 3.1041 | -0.0021 | -0.0196 | 0.0175 | -91.7702 | 11 | 2 | -317.6060 | 1084.4825 | -3.1556 | -3.0733 | 0.6575 | 0 | 0 |
| alma_baseline | half | 1 | 76062.0000 | 6914.7273 | 2.0976 | -0.0010 | -0.0184 | 0.0175 | -127.5318 | 11 | 0 | -256.4383 | 1418.2531 | -4.7069 | -4.2661 | 0.6075 | 0 | 0 |


**0 of 45 candidate-settings clear the empirical best-of-15 floor; 7 clear the alone floor.** 4 of 45 have a positive net R per year.


### BASELINE — `flip_only`, stability across the three settings

`sign_agree = 1` means all three settings agree on the sign of net R per year. A candidate positive on one setting and negative on two is being fitted, not measured.

| indicator | settings | settings_positive | sign_agree | R_per_year_min | R_per_year_med | R_per_year_max | spread |
|---|---:|---:|---:|---:|---:|---:|---:|
| rma_baseline | 3 | 1 | 0 | -23.0625 | -2.4643 | 2.5261 | 25.5886 |
| fantail_vma | 3 | 0 | 1 | -19.2052 | -11.0130 | -11.0130 | 8.1921 |
| lsma_baseline | 3 | 1 | 0 | -66.4392 | -11.2738 | 3.0185 | 69.4577 |
| t3_baseline | 3 | 0 | 1 | -51.7028 | -13.5473 | -13.1050 | 38.5979 |
| mcginley_dynamic_index | 3 | 1 | 0 | -22.6894 | -13.7881 | 0.7428 | 23.4322 |
| wma_baseline | 3 | 0 | 1 | -30.9717 | -14.7843 | -13.5189 | 17.4528 |
| sma_baseline | 3 | 0 | 1 | -25.0252 | -19.2862 | -2.9566 | 22.0686 |
| ema_baseline | 3 | 0 | 1 | -28.7260 | -21.6907 | -1.9987 | 26.7274 |
| tma_baseline | 3 | 0 | 1 | -23.0191 | -21.7268 | -7.5965 | 15.4226 |
| frama_baseline | 3 | 0 | 1 | -35.4926 | -26.8174 | -26.1803 | 9.3123 |
| vidya | 3 | 0 | 1 | -33.0665 | -27.2766 | -27.2766 | 5.7898 |
| hma_baseline | 3 | 1 | 0 | -91.7702 | -31.5931 | 6.8637 | 98.6339 |
| kama_baseline | 3 | 0 | 1 | -34.7442 | -33.2978 | -16.7458 | 17.9984 |
| super_smoother_2pole_baseline | 3 | 0 | 1 | -84.5757 | -34.1424 | -18.5594 | 66.0163 |
| alma_baseline | 3 | 0 | 1 | -127.5318 | -60.4572 | -29.8685 | 97.6634 |


**11 of 15 candidates have all three settings agreeing in sign.**


## BASELINE — `jack`, fixed settings, unseen trade years 2005-2015

Empirical yearly-t floors **from the random-entry null**: alone **-0.400**, best-of-15 **0.471**. The analytic equivalents on 11 yearly observations are 1.812 and 3.395 — the empirical ones are lower because the analytic formula assumes a **zero-mean** null while the real null also pays costs, so it is centred below zero.

| indicator | setting | distinct_setting | n_entered | trades_per_year | mean_bars | R_gross_per_trade | R_net_per_trade | cost_per_trade | R_net_per_year | years | years_positive | worst_year | worst_dip_R | t_yearly | t_block_boot | null_p | clears_alone_emp | clears_family_emp |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| sma_baseline | double | 1 | 13228.0000 | 1202.5455 | 5.1136 | 0.0177 | -0.0003 | 0.0180 | -0.3579 | 11 | 5 | -42.9908 | 159.5869 | -0.0324 | -0.0236 | 0.0625 | 1 | 0 |
| t3_baseline | double | 1 | 15270.0000 | 1388.1818 | 5.1663 | 0.0151 | -0.0023 | 0.0175 | -3.2332 | 11 | 4 | -49.7938 | 167.6933 | -0.3358 | -0.1973 | 0.0850 | 1 | 0 |
| tma_baseline | double | 1 | 12900.0000 | 1172.7273 | 5.2426 | 0.0149 | -0.0029 | 0.0179 | -3.4349 | 11 | 4 | -42.6269 | 188.5903 | -0.3198 | -0.2361 | 0.0925 | 1 | 0 |
| hma_baseline | double | 1 | 23192.0000 | 2108.3636 | 4.4872 | 0.0158 | -0.0018 | 0.0176 | -3.8229 | 11 | 3 | -41.1141 | 208.1875 | -0.3409 | -0.2024 | 0.0175 | 1 | 0 |
| mcginley_dynamic_index | default | 1 | 18526.0000 | 1684.1818 | 4.6944 | 0.0148 | -0.0025 | 0.0174 | -4.2456 | 11 | 6 | -68.9214 | 181.9973 | -0.3807 | -0.2621 | 0.0575 | 1 | 0 |
| ema_baseline | double | 1 | 15112.0000 | 1373.8182 | 4.8631 | 0.0144 | -0.0032 | 0.0176 | -4.4309 | 11 | 6 | -42.8873 | 168.3353 | -0.4846 | -0.2936 | 0.0800 | 0 | 0 |
| rma_baseline | default | 1 | 15444.0000 | 1404.0000 | 4.8347 | 0.0139 | -0.0037 | 0.0176 | -5.1470 | 11 | 6 | -45.7266 | 176.7589 | -0.5437 | -0.3477 | 0.0925 | 0 | 0 |
| rma_baseline | double | 1 | 11014.0000 | 1001.2727 | 5.0968 | 0.0120 | -0.0054 | 0.0174 | -5.4069 | 11 | 4 | -48.9812 | 161.8855 | -0.7252 | -0.4414 | 0.1525 | 0 | 0 |
| lsma_baseline | double | 1 | 20720.0000 | 1883.6364 | 4.5540 | 0.0146 | -0.0029 | 0.0176 | -5.5221 | 11 | 5 | -48.4933 | 200.5011 | -0.5355 | -0.2957 | 0.0375 | 0 | 0 |
| kama_baseline | double | 1 | 17152.0000 | 1559.2727 | 4.9460 | 0.0136 | -0.0035 | 0.0172 | -5.5302 | 11 | 4 | -46.8065 | 168.0804 | -0.7525 | -0.3547 | 0.0825 | 0 | 0 |
| wma_baseline | double | 1 | 17176.0000 | 1561.4545 | 4.8238 | 0.0122 | -0.0055 | 0.0177 | -8.6370 | 11 | 5 | -70.9249 | 225.6702 | -0.7772 | -0.5360 | 0.0975 | 0 | 0 |
| mcginley_dynamic_index | double | 1 | 12924.0000 | 1174.9091 | 5.0082 | 0.0099 | -0.0078 | 0.0176 | -9.1191 | 11 | 5 | -54.2259 | 179.7031 | -1.0381 | -0.7211 | 0.1825 | 0 | 0 |
| ema_baseline | default | 1 | 21486.0000 | 1953.2727 | 4.4757 | 0.0124 | -0.0050 | 0.0174 | -9.7879 | 11 | 4 | -71.9821 | 235.0702 | -0.8085 | -0.5620 | 0.0575 | 0 | 0 |
| wma_baseline | default | 1 | 24028.0000 | 2184.3636 | 4.3869 | 0.0115 | -0.0060 | 0.0176 | -13.1367 | 11 | 3 | -53.0723 | 261.0921 | -1.2333 | -0.6667 | 0.0525 | 0 | 0 |
| sma_baseline | default | 1 | 19186.0000 | 1744.1818 | 4.8255 | 0.0098 | -0.0077 | 0.0175 | -13.4354 | 11 | 5 | -66.8273 | 265.9941 | -1.3895 | -0.7665 | 0.1200 | 0 | 0 |
| rma_baseline | half | 1 | 22044.0000 | 2004.0000 | 4.4365 | 0.0105 | -0.0069 | 0.0175 | -13.8799 | 11 | 4 | -77.2781 | 267.4653 | -1.1626 | -0.7775 | 0.0875 | 0 | 0 |
| lsma_baseline | default | 1 | 30788.0000 | 2798.9091 | 3.8257 | 0.0125 | -0.0052 | 0.0177 | -14.5444 | 11 | 3 | -58.8118 | 285.2668 | -1.3031 | -0.7581 | 0.0200 | 0 | 0 |
| t3_baseline | default | 1 | 23930.0000 | 2175.4545 | 4.4913 | 0.0109 | -0.0067 | 0.0176 | -14.6145 | 11 | 2 | -47.5214 | 281.2698 | -1.4109 | -0.7360 | 0.0725 | 0 | 0 |
| tma_baseline | default | 1 | 18640.0000 | 1694.5455 | 5.0146 | 0.0088 | -0.0087 | 0.0175 | -14.7718 | 11 | 3 | -56.7821 | 272.6588 | -1.4487 | -0.8158 | 0.1750 | 0 | 0 |
| fantail_vma | half | 0 | 24246.0000 | 2204.1818 | 4.4122 | 0.0100 | -0.0075 | 0.0176 | -16.6270 | 11 | 5 | -63.2586 | 312.6554 | -1.3819 | -0.9203 | 0.1050 | 0 | 0 |
| fantail_vma | default | 1 | 24246.0000 | 2204.1818 | 4.4122 | 0.0100 | -0.0075 | 0.0176 | -16.6270 | 11 | 5 | -63.2586 | 312.6554 | -1.3819 | -0.9203 | 0.1050 | 0 | 0 |
| mcginley_dynamic_index | half | 1 | 26456.0000 | 2405.0909 | 4.1230 | 0.0105 | -0.0069 | 0.0175 | -16.6952 | 11 | 4 | -56.8971 | 274.7946 | -1.7412 | -0.8464 | 0.0675 | 0 | 0 |
| super_smoother_2pole_baseline | double | 1 | 23122.0000 | 2102.0000 | 4.5782 | 0.0089 | -0.0086 | 0.0175 | -18.1200 | 11 | 2 | -59.0430 | 281.4646 | -1.9384 | -0.9271 | 0.1625 | 0 | 0 |
| fantail_vma | double | 1 | 23980.0000 | 2180.0000 | 4.4530 | 0.0090 | -0.0086 | 0.0176 | -18.7695 | 11 | 3 | -61.9896 | 302.1941 | -2.0992 | -1.0209 | 0.1200 | 0 | 0 |
| kama_baseline | default | 1 | 23106.0000 | 2100.5455 | 4.4931 | 0.0067 | -0.0105 | 0.0172 | -21.9545 | 11 | 3 | -66.1433 | 366.9985 | -1.8753 | -1.2206 | 0.1875 | 0 | 0 |
| sma_baseline | half | 1 | 27850.0000 | 2531.8182 | 4.1473 | 0.0085 | -0.0091 | 0.0176 | -23.0576 | 11 | 1 | -84.9948 | 343.1711 | -2.1564 | -1.1495 | 0.1100 | 0 | 0 |
| hma_baseline | default | 1 | 34680.0000 | 3152.7273 | 3.6182 | 0.0104 | -0.0074 | 0.0177 | -23.2363 | 11 | 3 | -84.9531 | 316.4079 | -1.7897 | -1.2009 | 0.0425 | 0 | 0 |
| tma_baseline | half | 1 | 28152.0000 | 2559.2727 | 4.1625 | 0.0082 | -0.0093 | 0.0175 | -23.8057 | 11 | 2 | -95.5989 | 359.0905 | -1.9527 | -1.1674 | 0.1425 | 0 | 0 |
| ema_baseline | half | 1 | 29962.0000 | 2723.8182 | 3.8538 | 0.0086 | -0.0089 | 0.0175 | -24.3032 | 11 | 2 | -77.0694 | 344.5672 | -2.5324 | -1.1876 | 0.0875 | 0 | 0 |
| vidya | default | 1 | 35682.0000 | 3243.8182 | 3.5348 | 0.0092 | -0.0082 | 0.0174 | -26.6881 | 11 | 3 | -72.4085 | 351.2039 | -3.0174 | -1.3540 | 0.0600 | 0 | 0 |
| vidya | half | 0 | 35682.0000 | 3243.8182 | 3.5348 | 0.0092 | -0.0082 | 0.0174 | -26.6881 | 11 | 3 | -72.4085 | 351.2039 | -3.0174 | -1.3540 | 0.0600 | 0 | 0 |
| frama_baseline | half | 1 | 25106.0000 | 2282.3636 | 4.1552 | 0.0052 | -0.0123 | 0.0175 | -27.9609 | 11 | 3 | -89.9952 | 395.5250 | -2.4033 | -1.5176 | 0.2650 | 0 | 0 |
| alma_baseline | double | 1 | 33084.0000 | 3007.6364 | 3.7125 | 0.0081 | -0.0095 | 0.0176 | -28.4530 | 11 | 3 | -88.3924 | 405.4321 | -2.4002 | -1.3567 | 0.1125 | 0 | 0 |
| frama_baseline | default | 1 | 29086.0000 | 2644.1818 | 4.0130 | 0.0064 | -0.0111 | 0.0175 | -29.2876 | 11 | 2 | -87.2607 | 386.9208 | -2.6180 | -1.5606 | 0.1500 | 0 | 0 |
| wma_baseline | half | 1 | 34192.0000 | 3108.3636 | 3.6214 | 0.0080 | -0.0097 | 0.0176 | -30.0092 | 11 | 2 | -101.4943 | 410.1596 | -2.5152 | -1.4262 | 0.0700 | 0 | 0 |
| frama_baseline | double | 1 | 27402.0000 | 2491.0909 | 4.0434 | 0.0054 | -0.0122 | 0.0175 | -30.3213 | 11 | 1 | -82.6931 | 381.1511 | -3.9342 | -1.7034 | 0.2100 | 0 | 0 |
| vidya | double | 1 | 28368.0000 | 2578.9091 | 4.0762 | 0.0053 | -0.0121 | 0.0173 | -31.1291 | 11 | 2 | -70.4520 | 405.4493 | -3.5173 | -1.6048 | 0.2150 | 0 | 0 |
| super_smoother_2pole_baseline | default | 1 | 34816.0000 | 3165.0909 | 3.6087 | 0.0073 | -0.0103 | 0.0176 | -32.5808 | 11 | 3 | -109.3149 | 428.6497 | -2.6900 | -1.5900 | 0.1175 | 0 | 0 |
| kama_baseline | half | 1 | 30488.0000 | 2771.6364 | 3.8760 | 0.0054 | -0.0120 | 0.0174 | -33.1315 | 11 | 1 | -58.5465 | 417.8396 | -4.7586 | -1.6352 | 0.2025 | 0 | 0 |
| t3_baseline | half | 1 | 38628.0000 | 3511.6364 | 3.3641 | 0.0073 | -0.0103 | 0.0176 | -36.3024 | 11 | 3 | -116.7195 | 470.2546 | -2.7841 | -1.8530 | 0.0875 | 0 | 0 |
| alma_baseline | default | 1 | 49340.0000 | 4485.4545 | 2.7717 | 0.0046 | -0.0129 | 0.0176 | -58.0724 | 11 | 1 | -155.7456 | 700.4666 | -4.0882 | -2.7507 | 0.1425 | 0 | 0 |
| lsma_baseline | half | 1 | 46088.0000 | 4189.8182 | 2.9515 | 0.0032 | -0.0144 | 0.0176 | -60.2024 | 11 | 2 | -154.9578 | 744.2132 | -3.1933 | -2.9781 | 0.2650 | 0 | 0 |
| super_smoother_2pole_baseline | half | 1 | 51598.0000 | 4690.7273 | 2.6877 | 0.0031 | -0.0145 | 0.0176 | -68.0656 | 11 | 0 | -160.1393 | 809.1265 | -4.4912 | -3.3829 | 0.2750 | 0 | 0 |
| hma_baseline | half | 1 | 51224.0000 | 4656.7273 | 2.7587 | 0.0013 | -0.0162 | 0.0175 | -75.5638 | 11 | 2 | -206.8251 | 857.7791 | -3.6965 | -3.6670 | 0.3725 | 0 | 0 |
| alma_baseline | half | 1 | 76040.0000 | 6912.7273 | 1.9394 | 0.0015 | -0.0160 | 0.0175 | -110.7913 | 11 | 0 | -237.2493 | 1220.1572 | -5.1301 | -5.0287 | 0.3250 | 0 | 0 |


**0 of 45 candidate-settings clear the empirical best-of-15 floor; 5 clear the alone floor.** 0 of 45 have a positive net R per year.


### BASELINE — `jack`, stability across the three settings

`sign_agree = 1` means all three settings agree on the sign of net R per year. A candidate positive on one setting and negative on two is being fitted, not measured.

| indicator | settings | settings_positive | sign_agree | R_per_year_min | R_per_year_med | R_per_year_max | spread |
|---|---:|---:|---:|---:|---:|---:|---:|
| rma_baseline | 3 | 0 | 1 | -13.8799 | -5.4069 | -5.1470 | 8.7329 |
| mcginley_dynamic_index | 3 | 0 | 1 | -16.6952 | -9.1191 | -4.2456 | 12.4496 |
| ema_baseline | 3 | 0 | 1 | -24.3032 | -9.7879 | -4.4309 | 19.8722 |
| wma_baseline | 3 | 0 | 1 | -30.0092 | -13.1367 | -8.6370 | 21.3722 |
| sma_baseline | 3 | 0 | 1 | -23.0576 | -13.4354 | -0.3579 | 22.6997 |
| lsma_baseline | 3 | 0 | 1 | -60.2024 | -14.5444 | -5.5221 | 54.6803 |
| t3_baseline | 3 | 0 | 1 | -36.3024 | -14.6145 | -3.2332 | 33.0692 |
| tma_baseline | 3 | 0 | 1 | -23.8057 | -14.7718 | -3.4349 | 20.3708 |
| fantail_vma | 3 | 0 | 1 | -18.7695 | -16.6270 | -16.6270 | 2.1425 |
| kama_baseline | 3 | 0 | 1 | -33.1315 | -21.9545 | -5.5302 | 27.6013 |
| hma_baseline | 3 | 0 | 1 | -75.5638 | -23.2363 | -3.8229 | 71.7408 |
| vidya | 3 | 0 | 1 | -31.1291 | -26.6881 | -26.6881 | 4.4410 |
| frama_baseline | 3 | 0 | 1 | -30.3213 | -29.2876 | -27.9609 | 2.3604 |
| super_smoother_2pole_baseline | 3 | 0 | 1 | -68.0656 | -32.5808 | -18.1200 | 49.9455 |
| alma_baseline | 3 | 0 | 1 | -110.7913 | -58.0724 | -28.4530 | 82.3383 |


**15 of 15 candidates have all three settings agreeing in sign.**


## BASELINE — `textbook`, fixed settings, unseen trade years 2005-2015

Empirical yearly-t floors **from the random-entry null**: alone **-0.693**, best-of-15 **0.308**. The analytic equivalents on 11 yearly observations are 1.812 and 3.395 — the empirical ones are lower because the analytic formula assumes a **zero-mean** null while the real null also pays costs, so it is centred below zero.

| indicator | setting | distinct_setting | n_entered | trades_per_year | mean_bars | R_gross_per_trade | R_net_per_trade | cost_per_trade | R_net_per_year | years | years_positive | worst_year | worst_dip_R | t_yearly | t_block_boot | null_p | clears_alone_emp | clears_family_emp |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| sma_baseline | double | 1 | 12618.0000 | 1147.0909 | 3.5313 | 0.0142 | -0.0038 | 0.0180 | -4.3879 | 11 | 3 | -34.7709 | 137.0975 | -0.5725 | -0.3785 | 0.0700 | 1 | 0 |
| tma_baseline | double | 1 | 12252.0000 | 1113.8182 | 3.6039 | 0.0117 | -0.0063 | 0.0179 | -6.9761 | 11 | 3 | -33.2171 | 164.0359 | -0.9087 | -0.6190 | 0.1250 | 0 | 0 |
| t3_baseline | double | 1 | 14476.0000 | 1316.0000 | 3.5926 | 0.0114 | -0.0061 | 0.0175 | -7.9841 | 11 | 5 | -43.1879 | 197.3221 | -0.9511 | -0.6392 | 0.0875 | 0 | 0 |
| hma_baseline | double | 1 | 22022.0000 | 2002.0000 | 3.3513 | 0.0135 | -0.0041 | 0.0176 | -8.2034 | 11 | 3 | -44.1407 | 219.4562 | -0.8069 | -0.5695 | 0.0250 | 0 | 0 |
| rma_baseline | default | 1 | 14760.0000 | 1341.8182 | 3.4226 | 0.0115 | -0.0061 | 0.0176 | -8.2115 | 11 | 4 | -36.3278 | 179.8192 | -1.1527 | -0.6849 | 0.0775 | 0 | 0 |
| ema_baseline | double | 1 | 14448.0000 | 1313.4545 | 3.4378 | 0.0110 | -0.0067 | 0.0177 | -8.8120 | 11 | 4 | -40.9199 | 181.4240 | -1.2475 | -0.7425 | 0.1150 | 0 | 0 |
| mcginley_dynamic_index | default | 1 | 17778.0000 | 1616.1818 | 3.3667 | 0.0107 | -0.0066 | 0.0174 | -10.7027 | 11 | 5 | -40.2128 | 210.2072 | -1.4077 | -0.8067 | 0.0800 | 0 | 0 |
| ema_baseline | default | 1 | 20710.0000 | 1882.7273 | 3.2950 | 0.0110 | -0.0064 | 0.0174 | -12.0492 | 11 | 5 | -41.1873 | 222.1871 | -1.4302 | -0.8468 | 0.0625 | 0 | 0 |
| wma_baseline | double | 1 | 16462.0000 | 1496.5455 | 3.4057 | 0.0097 | -0.0081 | 0.0177 | -12.0720 | 11 | 3 | -49.5517 | 235.3411 | -1.5164 | -0.9238 | 0.1175 | 0 | 0 |
| mcginley_dynamic_index | double | 1 | 12300.0000 | 1118.1818 | 3.4846 | 0.0065 | -0.0111 | 0.0176 | -12.4608 | 11 | 2 | -32.5278 | 181.2781 | -2.8972 | -1.2940 | 0.2575 | 0 | 0 |
| sma_baseline | default | 1 | 18378.0000 | 1670.7273 | 3.4320 | 0.0098 | -0.0077 | 0.0175 | -12.8760 | 11 | 4 | -44.6242 | 221.9517 | -1.8562 | -0.9481 | 0.1250 | 0 | 0 |
| rma_baseline | double | 1 | 10542.0000 | 958.3636 | 3.4141 | 0.0037 | -0.0138 | 0.0174 | -13.2046 | 11 | 3 | -33.1678 | 167.0829 | -2.8389 | -1.4193 | 0.3850 | 0 | 0 |
| rma_baseline | half | 1 | 21250.0000 | 1931.8182 | 3.2784 | 0.0099 | -0.0076 | 0.0175 | -14.6698 | 11 | 3 | -39.8189 | 238.3218 | -1.9544 | -1.0152 | 0.0775 | 0 | 0 |
| kama_baseline | double | 1 | 16358.0000 | 1487.0909 | 3.3188 | 0.0071 | -0.0101 | 0.0172 | -14.9462 | 11 | 2 | -41.5072 | 223.7275 | -2.3499 | -1.2120 | 0.2100 | 0 | 0 |
| wma_baseline | default | 1 | 23142.0000 | 2103.8182 | 3.2371 | 0.0095 | -0.0080 | 0.0176 | -16.9218 | 11 | 4 | -63.3912 | 241.4535 | -2.2628 | -1.1107 | 0.0925 | 0 | 0 |
| tma_baseline | default | 1 | 17614.0000 | 1601.2727 | 3.5423 | 0.0069 | -0.0107 | 0.0176 | -17.0853 | 11 | 1 | -37.1639 | 237.5875 | -3.2872 | -1.2817 | 0.2025 | 0 | 0 |
| lsma_baseline | double | 1 | 19896.0000 | 1808.7273 | 3.2928 | 0.0073 | -0.0103 | 0.0176 | -18.6093 | 11 | 3 | -84.2158 | 266.7166 | -2.0492 | -1.3278 | 0.1825 | 0 | 0 |
| t3_baseline | default | 1 | 22696.0000 | 2063.2727 | 3.2975 | 0.0085 | -0.0091 | 0.0176 | -18.8344 | 11 | 2 | -51.9087 | 278.9042 | -2.7541 | -1.2620 | 0.1075 | 0 | 0 |
| fantail_vma | half | 0 | 22844.0000 | 2076.7273 | 3.2026 | 0.0082 | -0.0094 | 0.0176 | -19.5914 | 11 | 4 | -51.2068 | 278.5444 | -2.4752 | -1.4521 | 0.1175 | 0 | 0 |
| fantail_vma | default | 1 | 22844.0000 | 2076.7273 | 3.2026 | 0.0082 | -0.0094 | 0.0176 | -19.5914 | 11 | 4 | -51.2068 | 278.5444 | -2.4752 | -1.4521 | 0.1175 | 0 | 0 |
| fantail_vma | double | 1 | 22650.0000 | 2059.0909 | 3.1991 | 0.0079 | -0.0097 | 0.0176 | -19.9520 | 11 | 2 | -43.9063 | 267.4161 | -3.9010 | -1.5112 | 0.1500 | 0 | 0 |
| tma_baseline | half | 1 | 26648.0000 | 2422.5455 | 3.1517 | 0.0092 | -0.0084 | 0.0176 | -20.3739 | 11 | 1 | -57.6963 | 292.6812 | -3.0752 | -1.3614 | 0.1075 | 0 | 0 |
| super_smoother_2pole_baseline | double | 1 | 21942.0000 | 1994.7273 | 3.3317 | 0.0072 | -0.0104 | 0.0175 | -20.6831 | 11 | 3 | -50.2872 | 291.2159 | -3.0546 | -1.4127 | 0.1800 | 0 | 0 |
| kama_baseline | default | 1 | 22030.0000 | 2002.7273 | 3.1986 | 0.0066 | -0.0106 | 0.0172 | -21.2991 | 11 | 3 | -73.1853 | 304.6601 | -2.6825 | -1.5259 | 0.1450 | 0 | 0 |
| lsma_baseline | default | 1 | 29808.0000 | 2709.8182 | 2.9698 | 0.0097 | -0.0080 | 0.0177 | -21.6967 | 11 | 3 | -56.0577 | 301.3228 | -2.9016 | -1.3890 | 0.0675 | 0 | 0 |
| sma_baseline | half | 1 | 26780.0000 | 2434.5455 | 3.1221 | 0.0083 | -0.0094 | 0.0177 | -22.8606 | 11 | 1 | -49.9146 | 310.7675 | -3.8214 | -1.5365 | 0.1150 | 0 | 0 |
| mcginley_dynamic_index | half | 1 | 25710.0000 | 2337.2727 | 3.1044 | 0.0075 | -0.0099 | 0.0175 | -23.2496 | 11 | 2 | -63.0269 | 298.5352 | -3.5806 | -1.4835 | 0.0975 | 0 | 0 |
| frama_baseline | half | 1 | 23920.0000 | 2174.5455 | 3.0825 | 0.0051 | -0.0124 | 0.0175 | -27.0266 | 11 | 2 | -77.1949 | 344.8937 | -2.9122 | -1.8519 | 0.2275 | 0 | 0 |
| frama_baseline | default | 1 | 27902.0000 | 2536.5455 | 2.9360 | 0.0067 | -0.0108 | 0.0175 | -27.4642 | 11 | 0 | -75.9138 | 335.7620 | -3.7351 | -1.9266 | 0.1475 | 0 | 0 |
| ema_baseline | half | 1 | 29218.0000 | 2656.1818 | 2.9632 | 0.0071 | -0.0104 | 0.0175 | -27.7033 | 11 | 2 | -83.0030 | 345.5419 | -2.8772 | -1.6820 | 0.1150 | 0 | 0 |
| frama_baseline | double | 1 | 26520.0000 | 2410.9091 | 2.9396 | 0.0058 | -0.0117 | 0.0175 | -28.2928 | 11 | 0 | -58.1628 | 339.7153 | -4.9721 | -2.0767 | 0.1550 | 0 | 0 |
| hma_baseline | default | 1 | 33114.0000 | 3010.3636 | 2.8468 | 0.0082 | -0.0096 | 0.0178 | -28.8923 | 11 | 3 | -100.3087 | 344.8324 | -2.4705 | -1.9058 | 0.0400 | 0 | 0 |
| vidya | double | 1 | 27234.0000 | 2475.8182 | 3.0118 | 0.0055 | -0.0118 | 0.0173 | -29.1980 | 11 | 0 | -68.0612 | 356.9455 | -4.7840 | -1.9415 | 0.2000 | 0 | 0 |
| alma_baseline | double | 1 | 31766.0000 | 2887.8182 | 2.8815 | 0.0073 | -0.0103 | 0.0176 | -29.6564 | 11 | 2 | -84.9916 | 402.5733 | -3.5096 | -1.8619 | 0.0875 | 0 | 0 |
| kama_baseline | half | 1 | 29316.0000 | 2665.0909 | 2.9258 | 0.0059 | -0.0114 | 0.0174 | -30.4730 | 11 | 0 | -60.3338 | 390.0919 | -6.8911 | -1.9260 | 0.1650 | 0 | 0 |
| vidya | half | 0 | 34604.0000 | 3145.8182 | 2.7125 | 0.0076 | -0.0098 | 0.0174 | -30.6988 | 11 | 0 | -65.1434 | 371.0947 | -4.8332 | -1.9842 | 0.0725 | 0 | 0 |
| vidya | default | 1 | 34604.0000 | 3145.8182 | 2.7125 | 0.0076 | -0.0098 | 0.0174 | -30.6988 | 11 | 0 | -65.1434 | 371.0947 | -4.8332 | -1.9842 | 0.0725 | 0 | 0 |
| wma_baseline | half | 1 | 33284.0000 | 3025.8182 | 2.8321 | 0.0072 | -0.0105 | 0.0176 | -31.6829 | 11 | 1 | -84.3711 | 421.5948 | -3.6750 | -1.9909 | 0.0850 | 0 | 0 |
| super_smoother_2pole_baseline | default | 1 | 33174.0000 | 3015.8182 | 2.8101 | 0.0054 | -0.0122 | 0.0176 | -36.7432 | 11 | 1 | -94.9973 | 451.7943 | -3.7101 | -2.3546 | 0.1650 | 0 | 0 |
| t3_baseline | half | 1 | 37108.0000 | 3373.4545 | 2.6497 | 0.0043 | -0.0133 | 0.0176 | -44.9320 | 11 | 1 | -117.2286 | 544.0727 | -3.8499 | -2.9097 | 0.1800 | 0 | 0 |
| lsma_baseline | half | 1 | 45414.0000 | 4128.5455 | 2.4956 | 0.0019 | -0.0157 | 0.0176 | -64.8775 | 11 | 1 | -148.4072 | 719.4945 | -4.1972 | -3.8097 | 0.3125 | 0 | 0 |
| alma_baseline | default | 1 | 48170.0000 | 4379.0909 | 2.2899 | 0.0026 | -0.0150 | 0.0176 | -65.5963 | 11 | 0 | -156.9807 | 739.6725 | -4.2713 | -3.7239 | 0.2400 | 0 | 0 |
| super_smoother_2pole_baseline | half | 1 | 50066.0000 | 4551.4545 | 2.2301 | 0.0011 | -0.0165 | 0.0176 | -75.2133 | 11 | 0 | -159.0378 | 844.7695 | -4.9949 | -4.6274 | 0.4150 | 0 | 0 |
| hma_baseline | half | 1 | 49878.0000 | 4534.3636 | 2.3359 | 0.0005 | -0.0171 | 0.0176 | -77.4788 | 11 | 1 | -155.5853 | 852.9642 | -4.6831 | -4.5760 | 0.4200 | 0 | 0 |
| alma_baseline | half | 1 | 75870.0000 | 6897.2727 | 1.6883 | 0.0017 | -0.0158 | 0.0175 | -109.2050 | 11 | 0 | -250.3095 | 1201.5771 | -4.8158 | -5.5441 | 0.2775 | 0 | 0 |


**0 of 45 candidate-settings clear the empirical best-of-15 floor; 1 clear the alone floor.** 0 of 45 have a positive net R per year.


### BASELINE — `textbook`, stability across the three settings

`sign_agree = 1` means all three settings agree on the sign of net R per year. A candidate positive on one setting and negative on two is being fitted, not measured.

| indicator | settings | settings_positive | sign_agree | R_per_year_min | R_per_year_med | R_per_year_max | spread |
|---|---:|---:|---:|---:|---:|---:|---:|
| ema_baseline | 3 | 0 | 1 | -27.7033 | -12.0492 | -8.8120 | 18.8913 |
| mcginley_dynamic_index | 3 | 0 | 1 | -23.2496 | -12.4608 | -10.7027 | 12.5469 |
| sma_baseline | 3 | 0 | 1 | -22.8606 | -12.8760 | -4.3879 | 18.4726 |
| rma_baseline | 3 | 0 | 1 | -14.6698 | -13.2046 | -8.2115 | 6.4582 |
| wma_baseline | 3 | 0 | 1 | -31.6829 | -16.9218 | -12.0720 | 19.6108 |
| tma_baseline | 3 | 0 | 1 | -20.3739 | -17.0853 | -6.9761 | 13.3978 |
| t3_baseline | 3 | 0 | 1 | -44.9320 | -18.8344 | -7.9841 | 36.9479 |
| fantail_vma | 3 | 0 | 1 | -19.9520 | -19.5914 | -19.5914 | 0.3607 |
| kama_baseline | 3 | 0 | 1 | -30.4730 | -21.2991 | -14.9462 | 15.5268 |
| lsma_baseline | 3 | 0 | 1 | -64.8775 | -21.6967 | -18.6093 | 46.2682 |
| frama_baseline | 3 | 0 | 1 | -28.2928 | -27.4642 | -27.0266 | 1.2662 |
| hma_baseline | 3 | 0 | 1 | -77.4788 | -28.8923 | -8.2034 | 69.2754 |
| vidya | 3 | 0 | 1 | -30.6988 | -30.6988 | -29.1980 | 1.5008 |
| super_smoother_2pole_baseline | 3 | 0 | 1 | -75.2133 | -36.7432 | -20.6831 | 54.5302 |
| alma_baseline | 3 | 0 | 1 | -109.2050 | -65.5963 | -29.6564 | 79.5486 |


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

- `results/nnfx/stage1r2_c1_flip_only_yearly.csv` — 1,931 rows, md5 `71a26ae37242`
- `results/nnfx/stage1r2_c1_flip_only_summary.csv` — 117 rows, md5 `1fd79aaf25d3`
- `results/nnfx/stage1r2_c1_flip_only_nulls.csv` — 46,800 rows, md5 `c28370c1e724`
- `results/nnfx/stage1r2_c1_jack_yearly.csv` — 1,931 rows, md5 `7740dc7c3d31`
- `results/nnfx/stage1r2_c1_jack_summary.csv` — 117 rows, md5 `0109e209095f`
- `results/nnfx/stage1r2_c1_jack_nulls.csv` — 46,800 rows, md5 `67337cbb2d8d`
- `results/nnfx/stage1r2_c1_textbook_yearly.csv` — 1,931 rows, md5 `de3d72842dc6`
- `results/nnfx/stage1r2_c1_textbook_summary.csv` — 117 rows, md5 `72e167ef2ef1`
- `results/nnfx/stage1r2_c1_textbook_nulls.csv` — 46,800 rows, md5 `a9671c58fbff`
- `results/nnfx/stage1r2_base_flip_only_yearly.csv` — 760 rows, md5 `236b8d8830c0`
- `results/nnfx/stage1r2_base_flip_only_summary.csv` — 45 rows, md5 `2414b2cec88c`
- `results/nnfx/stage1r2_base_flip_only_nulls.csv` — 18,000 rows, md5 `7a4ca1328c4a`
- `results/nnfx/stage1r2_base_jack_yearly.csv` — 760 rows, md5 `2e679cea7adc`
- `results/nnfx/stage1r2_base_jack_summary.csv` — 45 rows, md5 `5c849dd92500`
- `results/nnfx/stage1r2_base_jack_nulls.csv` — 18,000 rows, md5 `607a2fa03a84`
- `results/nnfx/stage1r2_base_textbook_yearly.csv` — 754 rows, md5 `1aa1cb3ca94f`
- `results/nnfx/stage1r2_base_textbook_summary.csv` — 45 rows, md5 `8169d4fe7f79`
- `results/nnfx/stage1r2_base_textbook_nulls.csv` — 18,000 rows, md5 `44322a6fa708`
- `results/nnfx/stage1r2_ambiguity_delta.csv` — 24 rows
- `results/nnfx/power_test_bootstrap.csv` — 6 rows
- `results/nnfx/condition4_zero_edge.csv` — 279 rows
- `results/nnfx/CANDIDATE_LEDGER.csv` — 54 rows
