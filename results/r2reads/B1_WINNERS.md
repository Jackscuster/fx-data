# B1-WINNERS — THE 10 WINNERS ON SIX YEARS THEY WERE NEVER SELECTED ON

Generated 2026-11-24 11:08 by `code/b1narrow.py --stage winners` with `FX_WALK=ext11`.


> ## THE VERSION OF THIS FILE ISSUED AT 10:21 ON 24 NOV IS SUPERSEDED AND WRONG
>
> It reported winner 1 as 16.68 / 6.63 / 120.8 / 85.14 / 12.14 R over 2016-2020 against a record of 13.812 / 17.462 / 51.399 / 29.295 / 13.121, and about 1,886 trades over those five years against 826. Jack caught it by checking the years the two walks share.
>
> **THE CAUSE, IN TWO LINES.** I read the banked record as `bank[k][:, step, year, ...]`, which SUMS the four streams — trend-routed, trend-allon, chop-routed and chop-allon — into one number that belongs to no strategy, instead of selecting the winner's own stream. The eleven-step tune was never wrong: it used the same gate 2 grid, the same objective and the same scoring, and it reproduces the five-step record on the shared years exactly.
>
> **Nothing else changed.** The direction of the finding is the same and slightly worse once era-correct costs are charged.


## Condition 3 — cross-walk reproduction

Trade years 2016-2020 use the same tuning years in both walks — tune 2011-2014 / grade 2015 / trade 2016, and so on — so the eleven-step walk must reproduce the five-step record on them exactly.


| check | worst difference | over tolerance |
|---|---:|---:|
| per-year total R | 0.000e+00 | 0 of 50 |
| per-year trade count | 0.000e+00 | 0 of 50 |
| selected config index | — | 50 of 50 identical |

**CONDITION 3: PASS** — 50 winner-years, 10 winners x 5 shared years. It is registered as preflight guard 30 and runs on any extended-walk job. Nothing from 2010-2015 is quoted below unless it passes.


## A SECOND DIVERGENCE, FOUND WHILE CHASING THE FIRST — NOT MINE

Jack's reference numbers came from `mode?_winners.csv`, whose `R_<year>` is written from the **gate 3 KPI bank**, not from gate 2's `win` array. The two disagree for the **same strategy, the same config index and the same year**:


| | |
|---|---|
| winner-years compared | 50 |
| per-year R differing by more than 1e-6 | **41 of 50** |
| trade counts differing | **35 of 50** |
| median \|ΔR\| | 1.0096 R |
| largest \|ΔR\| | 10.6274 R |
| largest \|Δn\| | 11 trades |

**Gate 2 is the faithful record.** A direct re-score of winner 1's config 289 over 2016 returns **13.812019**, which is gate 2's banked `sum_r` to six decimals. The gate 3 KPI bank says 16.5096. Gate 3 reads the *same* config index out of gate 2's tag and then scores it through a different scorer (`sc.score`), and that is where the two part.


So this report compares against the **gate 2 bank**, which is the cross-walk property being tested. **The gate 2 / gate 3 divergence is a separate, pre-existing defect that affects `mode?_winners.csv` and everything built on it, including `MODEA_WINNERS.md`.** It is filed in `results/r2gate2/gate2_vs_gate3_peryear.csv` and is not fixed here, because fixing it means deciding which engine is right about trade-year attribution and that is a change to what is computed.


## What makes this a test

The winners were selected on the FIVE-step walk, whose earliest tuning year is 2011 and whose trade years are 2016-2020. **Trade years 2010 through 2015 were touched by no part of that selection** — not by tuning, not by grading, not by the luck floors.


## Era-correct costs

`cost_table_h22.csv` was calibrated on **2016-2020** spreads, and it carries `bp_2004_2015` beside them. **25 of 28 pairs were wider in 2004-2015, median 1.26x.** So charging the 2010-2015 trade years the 2016-2020 table under-charges them, and the six unseen years are FLATTERED in the charged column.


The era column re-scores the **same selected configurations** under `results/cost_table_era_2004_2015.csv`, built from that column. Only the costs change, so the difference isolates the cost effect rather than mixing in a different selection. R is taken from the engine's re-scored daily series, not from the bank — the bank was built under the other table and reading it would ignore the override entirely, which is how a first attempt returned a difference of exactly zero.


## Mode A

### R per trade year, 2010-2020 — corrected

**2010-2015 were never seen at selection.** 2016-2020 are the years the winners were chosen on and now reproduce the record exactly.

| sid | stream | R_2010 | R_2011 | R_2012 | R_2013 | R_2014 | R_2015 | R_2016 | R_2017 | R_2018 | R_2019 | R_2020 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| lemantrend_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | -41.93 | -20.98 | -11.69 | -5.828 | 26.82 | -28.69 | 13.81 | 17.46 | 51.4 | 29.29 | 13.12 |
| lemantrend_signals|hieken_ashi_smoothed_signals|volatility_ratio_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | -52.62 | -9.751 | -20.13 | 22.61 | 20.83 | -44.81 | 14.45 | 42.17 | 39.57 | 34.99 | 8.264 |
| waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | -41.67 | -23.07 | -10.64 | -2.736 | 1.717 | 0.7386 | 7.85 | 14.39 | 44.64 | 25.36 | 12.18 |
| waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|volatility_ratio_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | -49.16 | -8.065 | -15.67 | 23.26 | 8.207 | 20.37 | 5.652 | 36.92 | 29.35 | 35.07 | 7.936 |
| lemantrend_signals|relative_vigor_index_signals|volatility_ratio_volume_signals|super_smoother_2pole_baseline|adx_dmi_exit | trend-allon | -72.98 | 31.92 | -19.92 | -12.22 | 19.24 | 13.89 | 46.76 | -1.309 | 32.92 | 26.37 | 22.77 |
| lemantrend_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|fantail_vma|adx_dmi_exit | trend-allon | 1.239 | -4.101 | -7.428 | 46.8 | -13.8 | -13.76 | 17.65 | 29.9 | 27.68 | 23.59 | -0.3228 |
| waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|super_smoother_2pole_baseline|adx_dmi_exit | trend-allon | -46.44 | -6.199 | 15.74 | -23.56 | -47.35 | -5.099 | 21.44 | 21.61 | 44.88 | 17.14 | 13.18 |
| lemantrend_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|frama_baseline|adx_dmi_exit | trend-allon | -38.25 | -8.147 | -18.89 | 34.53 | -9.979 | -18.54 | 11.91 | -5.781 | 62.2 | 29.66 | 18.53 |


### The six never-seen years, charged both ways

| sid | stream | R_new6 | n_new6 | dd_new6 | t_new6 | years_pos_new6 | prop_return_new6 | R_new6_era | R_delta_era | R_delta_per_trade | prop_return_new6_era |
|---|---|---|---|---|---|---|---|---|---|---|---|
| lemantrend_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | -82.31 | 2108 | 88.28 | -1.943 | 1 | -0.5594 | -90.9 | -8.589 | -0.004074 | -0.5736 |
| lemantrend_signals|hieken_ashi_smoothed_signals|volatility_ratio_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | -83.87 | 2295 | 95.8 | -0.9208 | 2 | -0.5253 | -93.01 | -9.147 | -0.003986 | -0.5323 |
| waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | -75.66 | 1794 | 91.44 | -2.144 | 2 | -0.4965 | -82.79 | -7.127 | -0.003973 | -0.5048 |
| waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|volatility_ratio_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | -21.05 | 1947 | 89.26 | 0.1628 | 3 | -0.1415 | -28.74 | -7.686 | -0.003948 | -0.1846 |
| lemantrend_signals|relative_vigor_index_signals|volatility_ratio_volume_signals|super_smoother_2pole_baseline|adx_dmi_exit | trend-allon | -40.07 | 2485 | 99.13 | -0.5621 | 3 | -0.2425 | -50.17 | -10.1 | -0.004066 | -0.2975 |
| lemantrend_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|fantail_vma|adx_dmi_exit | trend-allon | 8.96 | 1174 | 39.27 | -0.06533 | 2 | 0.1369 | 4.261 | -4.699 | -0.004003 | 0.06159 |
| waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|super_smoother_2pole_baseline|adx_dmi_exit | trend-allon | -112.9 | 1985 | 131.7 | -0.6256 | 1 | -0.5145 | -120.6 | -7.65 | -0.003854 | -0.5218 |
| lemantrend_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|frama_baseline|adx_dmi_exit | trend-allon | -59.27 | 1571 | 80.72 | -1.352 | 1 | -0.4406 | -65.37 | -6.096 | -0.003881 | -0.4717 |


**1 of 8 winners are positive over the six never-seen years under the charged table, and 1 of 8 under era-correct costs. 0 clear the 12%/yr prop target either way.**


The era correction costs every winner between 4.7 and 10.1 R over the six years — about -0.0040 R per trade, consistent across all of them, which is the sanity check a uniform cost increase should pass.


### All eleven years

| sid | R_all11 | n_all11 | dd_all11 | years_pos_all11 | prop_return_all11 |
|---|---|---|---|---|---|
| lemantrend_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | 42.78 | 2934 | 104 | 6 | 0.1346 |
| lemantrend_signals|hieken_ashi_smoothed_signals|volatility_ratio_volume_signals|alma_baseline|adx_dmi_exit | 55.58 | 3607 | 115.7 | 7 | 0.1572 |
| waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | 28.76 | 2563 | 94.42 | 7 | 0.09969 |
| waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|volatility_ratio_volume_signals|alma_baseline|adx_dmi_exit | 93.88 | 3245 | 89.26 | 8 | 0.3442 |
| lemantrend_signals|relative_vigor_index_signals|volatility_ratio_volume_signals|super_smoother_2pole_baseline|adx_dmi_exit | 87.44 | 3673 | 99.13 | 7 | 0.2887 |
| lemantrend_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|fantail_vma|adx_dmi_exit | 107.5 | 2077 | 55.68 | 6 | 0.6317 |
| waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|super_smoother_2pole_baseline|adx_dmi_exit | 5.354 | 2977 | 151 | 6 | 0.0116 |
| lemantrend_signals|hieken_ashi_smoothed_signals|choppiness_index_volume_signals|frama_baseline|adx_dmi_exit | 57.24 | 2647 | 80.72 | 5 | 0.2321 |


## Mode B

### R per trade year, 2010-2020 — corrected

**2010-2015 were never seen at selection.** 2016-2020 are the years the winners were chosen on and now reproduce the record exactly.

| sid | stream | R_2010 | R_2011 | R_2012 | R_2013 | R_2014 | R_2015 | R_2016 | R_2017 | R_2018 | R_2019 | R_2020 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|fantail_vma|adx_dmi_exit | trend-allon | -15.86 | -6.066 | 0.2522 | 4.584 | 7.233 | 1.62 | 17.12 | 14.11 | 34.84 | 18.32 | 7.85 |
| lemantrend_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | 11.54 | -16.58 | -12.34 | 12.98 | 10.78 | 6.023 | 5.283 | 23.73 | 46.81 | 12.02 | 10.31 |


### The six never-seen years, charged both ways

| sid | stream | R_new6 | n_new6 | dd_new6 | t_new6 | years_pos_new6 | prop_return_new6 | R_new6_era | R_delta_era | R_delta_per_trade | prop_return_new6_era |
|---|---|---|---|---|---|---|---|---|---|---|---|
| waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|fantail_vma|adx_dmi_exit | trend-allon | -8.235 | 659 | 36.08 | -0.02951 | 4 | -0.137 | -10.92 | -2.683 | -0.004072 | -0.1766 |
| lemantrend_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | trend-allon | 12.41 | 1129 | 36.64 | 0.03372 | 4 | 0.2032 | 7.101 | -5.307 | -0.0047 | 0.1129 |


**1 of 2 winners are positive over the six never-seen years under the charged table, and 1 of 2 under era-correct costs. 0 clear the 12%/yr prop target either way.**


The era correction costs every winner between 2.7 and 5.3 R over the six years — about -0.0044 R per trade, consistent across all of them, which is the sanity check a uniform cost increase should pass.


### All eleven years

| sid | R_all11 | n_all11 | dd_all11 | years_pos_all11 | prop_return_all11 |
|---|---|---|---|---|---|
| waddah_attar_explosion_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|fantail_vma|adx_dmi_exit | 84 | 1249 | 36.08 | 9 | 0.762 |
| lemantrend_signals|hieken_ashi_smoothed_signals|chaikin_volatility_volume_signals|alma_baseline|adx_dmi_exit | 110.6 | 1988 | 36.64 | 9 | 0.9877 |


## How to read this

These winners cleared two luck floors on 2016-2020 and they do not generalise backwards. That is a finding about the **selection method**, not about these ten strategies: the floors did their job on the years they were given, and those years were not representative. Charging the costs that actually prevailed makes it worse, not better.


## Still pending

- The family sample and the control run as a second stage, reported in `B1_NARROW.md`. Until then a winner holding up here cannot be separated from the family holding up.

- The random-entry null on these six years needs an engine pass and is not in this read.

- **The gate 2 / gate 3 per-year divergence above is unresolved.**


## Provenance

- `results/r2reads/modeA_b1winners.csv` — 8 rows, md5 `d1d70eefb2a0`
- `results/r2reads/modeB_b1winners.csv` — 2 rows, md5 `98c8349d6234`
- `results/r2reads/modeA_b1winners_era.csv` — 8 rows, md5 `9c052dbdf7f7`
- `results/r2reads/modeB_b1winners_era.csv` — 2 rows, md5 `b17dd2afe550`
- `results/r2gate2_cond3_crosswalk.csv` — 50 rows, md5 `9c5ba615e165`
- `results/r2gate2/gate2_vs_gate3_peryear.csv` — 50 rows, md5 `7a38d783b53e`
- `results/cost_table_era_2004_2015.csv` — 28 rows, md5 `7d5148783e64`
