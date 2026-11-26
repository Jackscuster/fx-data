# SOURCE 3 — machine search, against a search null

**Protocol: `results/nnfx/PROTOCOL.md`, unchanged. 584,422 evaluations in the real search, 50 null runs at the same budget. The floor is the 95th percentile of the best **replicated** result under the null.**

## The design

| | pairs | years |
|---|---:|---|
| **discovery** | 15 (neither JPY nor CHF) | 2005-2010 |
| **replication** | 13 (JPY or CHF) | 2011-2015 |
| off-diagonal | 13 | 2005-2010 |
| off-diagonal | 15 | 2011-2015 |

Discovery and replication share **no pair and no year**. A candidate that carries has to work on different currencies in a different decade — stronger than an ordinary train/test split.

The space is **2.53e+09 complete five-slot algorithms** (117 C1 x 117 C2 x 36 volume x 48 baseline x 107 exit options, settings included, collapsed settings removed). The random sample of 200,000 is **0.0079%** of it.

## The budget, and what it bought

| | value |
|---|---:|
| random candidates | 200,000 |
| local-search evaluations | 184,372 |
| replication evaluations of the sample | 200,000 |
| **total evaluations, real search** | **584,422** |
| best discovery objective, random sample | +12.4117 |
| best discovery objective after local search | +18.0076 |
| **best replication objective of the top 50** | **+14.8704** |
| minutes | 17.1 |

The objective is **net R per year excluding the best day** on the fast path: realised by exit day, uncapped, charged once per round trip. `nnfxproto.verify_fast` checks it against the full reporting path to 2e-16. Every candidate the search surfaces is re-scored on the full path, with the 1:30 cap and mark to market.

## The search null — 50 independent runs at the same budget

| | best replicated under the null |
|---|---:|
| runs | 50 |
| mean | +9.3169 |
| median | +9.4802 |
| **95th percentile = THE FLOOR** | **+13.6706** |
| max | +15.6573 |
| best DISCOVERY under the null, mean | +11.9400 |
| best discovery under the null, max | +16.0968 |

Each null run block-shuffles every pair's bars in 20-day blocks within the calendar year and flips each block's direction with probability one half, then runs the **identical search at the identical budget**. The daily return standard deviation is preserved exactly and the lag-1 autocorrelation to three decimals; what is destroyed is any direction and any trend longer than 20 days.

**Two declared limitations of the null.** There is no hourly bid/ask path for a synthetic price series, so the null runs with realistic gap fills and the ambiguity resolver **off** while the real search runs with both on. Item 1 measured gap fills at under 1 R a year on real candidates and the shuffle destroys the crisis clustering that makes gaps matter, so this makes the null very slightly easier to beat, not harder. The peg guard's median is a 28-pair median in both worlds.

### The comparison

> **The real search's best replicated result is +14.8704. The null's 95th percentile is +13.6706. The real search BEATS the floor.**

**2 of the top 50 beat the search null on the replication set.**

## (e) Does past performance carry in this space?

| | Spearman rho, discovery against replication | p |
|---|---:|---:|
| **real search**, all 200,000 | **+0.0866** | 0 |
| null runs, mean | -0.0143 | — |
| null runs, 95th percentile | +0.0860 | — |

**The rank correlation IS above the null.** Discovery performance carries some information about replication performance in this space — not much at rho +0.0866, but more than shuffled data produces.

This is the FX version of Bajgrowicz and Scaillet on the DJIA 1897-2011, where fewer than 5%% of selected rules survive the first re-selection, and of this project's own blind grade, which measured a rank correlation of +0.02 to +0.05 between in-sample and out-of-sample on 20,275 signals.

## The top 20 by discovery, on every set

| rank | C1 | C2 | volume | baseline | exit | discovery | **replication** | 13 pairs 2005-10 | 15 pairs 2011-15 |
|---:|---|---|---|---|---|---:|---:|---:|---:|
| 1 | fisher_transform/double | parabolic_sar/half | ttm_squeeze/double | vidya/default | relative_vigor_index/double | +18.008 | **+13.969** | -0.830 | -10.628 |
| 2 | fisher_transform/double | parabolic_sar/half | mass_index/double | vidya/half | relative_vigor_index/double | +17.400 | **+14.870** | -1.476 | -10.665 |
| 3 | fisher_transform/default | parabolic_sar/half | ttm_squeeze/double | vidya/half | relative_vigor_index/double | +17.084 | **+10.627** | +0.486 | -8.277 |
| 4 | fisher_transform/default | parabolic_sar/half | mass_index/double | vidya/default | relative_vigor_index/double | +16.734 | **+11.378** | -0.346 | -7.842 |
| 5 | fisher_transform/default | parabolic_sar/default | mass_index/double | vidya/half | relative_vigor_index/default | +16.209 | **+5.142** | +4.295 | -9.229 |
| 6 | fx_sniper_ergodic_cci/default | rex_oscillator/half | volatility_ratio/half | super_smoother_2pole/default | relative_vigor_index/double | +15.762 | **+2.460** | +7.066 | -13.015 |
| 7 | fx_sniper_ergodic_cci/default | ssl_channel/default | volatility_ratio/double | super_smoother_2pole/default | relative_vigor_index/double | +15.583 | **+9.224** | +2.273 | -7.606 |
| 8 | coppock_curve/half | j_tpo/double | ttm_squeeze/double | frama/double | donchian_breakout/half | +15.511 | **-0.054** | +0.675 | -13.030 |
| 9 | parabolic_sar/default | j_tpo/double | volatility_ratio/double | mcginley_dynamic_index/half | chandelier/double | +15.456 | **+4.770** | +1.259 | -1.494 |
| 10 | coral/half | parabolic_sar/default | choppiness_index/double | vidya/default | relative_vigor_index/double | +15.350 | **+5.311** | -2.041 | -8.456 |
| 11 | coral/half | parabolic_sar/half | volatility_ratio/half | vidya/half | relative_vigor_index/double | +15.116 | **+9.310** | -0.614 | -5.811 |
| 12 | fisher_transform/default | parabolic_sar/half | volatility_ratio/double | super_smoother_2pole/half | relative_vigor_index/double | +15.084 | **+9.168** | -1.391 | +0.498 |
| 13 | ssl_channel/half | volatility_quality/half | volatility_ratio/half | lsma/default | relative_vigor_index/double | +15.014 | **+11.016** | -2.436 | -3.886 |
| 14 | fisher_transform/default | parabolic_sar/half | volatility_ratio/half | super_smoother_2pole/half | relative_vigor_index/default | +14.977 | **+7.587** | +0.642 | -0.328 |
| 15 | fisher_transform/default | parabolic_sar/half | volatility_ratio/half | alma/default | relative_vigor_index/double | +14.671 | **+6.605** | +1.875 | -1.440 |
| 16 | fx_sniper_ergodic_cci/double | halftrend/half | volatility_ratio/half | super_smoother_2pole/double | fx_sniper_ergodic_cci/half | +14.656 | **+5.640** | +0.040 | -0.857 |
| 17 | fx_sniper_ergodic_cci/default | parabolic_sar/half | volatility_ratio/half | wma/half | relative_vigor_index/double | +14.522 | **+6.228** | +3.864 | -10.072 |
| 18 | coppock_curve/half | j_tpo/double | ttm_squeeze/double | ema/default | adx_dmi/half | +14.314 | **-4.695** | +3.760 | -0.270 |
| 19 | coppock_curve/double | fisher_transform/half | ttm_squeeze/double | ema/half | lemantrend/half | +14.288 | **+0.672** | -4.893 | -10.392 |
| 20 | parabolic_sar/half | volatility_quality/half | volatility_ratio/double | lsma/default | relative_vigor_index/double | +14.235 | **+11.476** | -3.793 | +2.150 |

**37 of the top 50 are even POSITIVE on the replication set**, before any floor is applied. The off-diagonal columns are the control: a candidate that is strong on discovery and on the 13 pairs in the SAME years, but weak on the 13 pairs in LATER years, found a period and not a rule.

## The survivors through G2, G3 and G4

**Source 3's G1 is the search null itself.** A candidate found by looking at 584,422 of them cannot be judged against a best-of-one random-entry floor, and the random-entry null has no way of knowing how many were looked at.

| id | R total | R/yr | trades | R/dip | G2 | G3 | G4 | **passer** |
|---|---:|---:|---:|---:|---|---|---|---|
| **S3_01** | +146.813 | +13.347 | 8954 | +1.400 | **PASS** | **PASS** | **PASS** | **PASSER** |
| **S3_02** | +95.445 | +8.677 | 8996 | +0.904 | **PASS** | fail | **PASS** | no |

**1 passers.**

## Costs

Charged **once** per round trip on the engine's own risk denominator, real world and null world alike. See `results/nnfx/COST_DOUBLE_CHARGE.md`.

## Provenance

- `results/nnfx/src3_top50.csv` — 50 rows, md5 `142a86edba1a`
- `results/nnfx/src3_sample.csv` — 200000 rows, md5 `c6b3e4749023`
- `results/nnfx/src3_real_meta.csv` — 1 rows, md5 `e4826fc5a09d`
- `results/nnfx/src3_nulls.csv` — 50 rows, md5 `3e58323b9fbd`
- `results/nnfx/src3_gates.csv` — 2 rows, md5 `3fd307993d88`

The candidate ledger is `results/nnfx/proto_ledger.csv`, append-only and shared by all three sources, so no row count is quoted for it here.
