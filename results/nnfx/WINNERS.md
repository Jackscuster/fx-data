# WINNERS -- every strategy in the best book

**Item 4 of Jack's correction. The best book was picked by the best percent a year -- NOTHING CLEARS B1 TO B4.**

## The book

| | |
|---|---|
| family | b per pair |
| rotation | R1 -- admitted on 2005-2010, scored on 2011-2015 |
| K | 89 |
| share threshold | 0.25 |
| mode | voting |
| distinct algorithms | 2426 |
| sleeves (algorithm x pair) | 2492 |
| R on the scoring window | +1.122 |
| R a year | +0.224 |
| verified worst dip | 0.933 (realised 0.725, shuffled-order 95th 0.933, the larger binding) |
| **return per dip** | **+1.203** |
| sizing to 3.6% daily / 5.4% trailing | x5.790 |
| **percent a year at that sizing** | **+1.30%** |
| days to pass the +10% evaluation | 844 |
| gates cleared | B1 --, B2 PASS, B3 PASS, B4 PASS, B5 fail |

## How far from 12%

**+1.30% a year against Jack's 12% target: short by 10.70 percentage points, a factor of 9.2.**

## Every strategy in it, sorted by contribution

*Attribution is exact for the `separate` mode, where the book is 1/N times the sum of its sleeves. In `voting` mode the netting saving is a property of the whole pair, not of one member, so the per-member figures below are the separate-position contributions and the book total they sum to is the separate one.*

| # | algorithm | pairs | sleeves | R scoring | R/yr | %/yr at book sizing | share of book | trades |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 1 | C1 fisher_transform/default | C2 coral/default | VOL ttm_squeeze/double | BASE wma/half | EXIT donchian_breakout/half | CHFJPY EURJPY | 2 | +37.096 | +0.0030 | +0.017% | +1.7% | 331 |
| 2 | C1 fisher_transform/default | C2 coral/half | VOL mass_index/double | BASE vidya/default | EXIT relative_vigor_index/double | EURGBP GBPJPY | 2 | +27.489 | +0.0022 | +0.013% | +1.3% | 424 |
| 3 | C1 fisher_transform/default | C2 coral/default | VOL ttm_squeeze/double | BASE vidya/half | EXIT polychromatic_momentum/half | CHFJPY EURJPY | 2 | +25.891 | +0.0021 | +0.012% | +1.2% | 353 |
| 4 | C1 fisher_transform/default | C2 coral/half | VOL ttm_squeeze/double | BASE vidya/half | EXIT relative_vigor_index/double | EURGBP GBPJPY | 2 | +24.601 | +0.0020 | +0.011% | +1.1% | 419 |
| 5 | C1 fisher_transform/default | C2 coral/half | VOL ttm_squeeze/double | BASE vidya/default | EXIT relative_vigor_index/double | EURGBP GBPJPY | 2 | +24.601 | +0.0020 | +0.011% | +1.1% | 419 |
| 6 | C1 fisher_transform/double | C2 fisher_transform/double | VOL ttm_squeeze/double | BASE vidya/half | EXIT ichimoku/double | EURJPY NZDJPY | 2 | +23.933 | +0.0019 | +0.011% | +1.1% | 474 |
| 7 | C1 center_of_gravity/default | C2 coral/default | VOL ttm_squeeze/double | BASE ema/half | EXIT schaff_trend_cycle/double | CHFJPY | 1 | +22.408 | +0.0018 | +0.010% | +1.0% | 129 |
| 8 | C1 fisher_transform/double | C2 parabolic_sar/half | VOL mass_index/double | BASE alma/default | EXIT halftrend/default | NZDJPY USDJPY | 2 | +21.793 | +0.0017 | +0.010% | +1.0% | 317 |
| 9 | C1 coral/half | C2 coral/half | VOL variance/double | BASE alma/half | EXIT waddah_attar_explosion/half | EURAUD GBPJPY | 2 | +21.501 | +0.0017 | +0.010% | +1.0% | 459 |
| 10 | C1 fx_sniper_ergodic_cci/half | C2 coral/half | VOL efficiency_ratio/half | BASE hma/default | EXIT chandelier/double | GBPJPY | 1 | +19.725 | +0.0016 | +0.009% | +0.9% | 96 |
| 11 | C1 coral/default | C2 fisher_transform/half | VOL ttm_squeeze/double | BASE ema/half | EXIT polychromatic_momentum/half | CHFJPY | 1 | +19.687 | +0.0016 | +0.009% | +0.9% | 146 |
| 12 | C1 coral/default | C2 coral/half | VOL mass_index/double | BASE vidya/half | EXIT relative_vigor_index/double | EURGBP GBPJPY GBPNZD | 3 | +18.476 | +0.0015 | +0.009% | +0.9% | 616 |
| 13 | C1 center_of_gravity/default | C2 volatility_quality/half | VOL ttm_squeeze/double | BASE ema/half | EXIT rex_oscillator/default | CHFJPY | 1 | +18.288 | +0.0015 | +0.008% | +0.8% | 118 |
| 14 | C1 fisher_transform/double | C2 fisher_transform/double | VOL mass_index/double | BASE vidya/half | EXIT relative_vigor_index/double | EURJPY NZDJPY | 2 | +18.160 | +0.0015 | +0.008% | +0.8% | 478 |
| 15 | C1 fisher_transform/default | C2 hieken_ashi_smoothed/default | VOL mass_index/double | BASE vidya/half | EXIT polychromatic_momentum/half | AUDJPY | 1 | +18.147 | +0.0015 | +0.008% | +0.8% | 106 |
| 16 | C1 fisher_transform/double | C2 fisher_transform/double | VOL ttm_squeeze/double | BASE vidya/default | EXIT relative_vigor_index/double | EURJPY NZDJPY | 2 | +17.611 | +0.0014 | +0.008% | +0.8% | 475 |
| 17 | C1 fisher_transform/default | C2 fisher_transform/half | VOL mass_index/double | BASE super_smoother_2pole/default | EXIT relative_vigor_index/double | CHFJPY | 1 | +17.584 | +0.0014 | +0.008% | +0.8% | 196 |
| 18 | C1 fisher_transform/default | C2 fisher_transform/default | VOL ttm_squeeze/double | BASE wma/half | EXIT chandelier/double | CHFJPY | 1 | +16.937 | +0.0014 | +0.008% | +0.8% | 199 |
| 19 | C1 center_of_gravity/default | C2 volatility_quality/half | VOL ttm_squeeze/double | BASE ema/half | EXIT parabolic_sar/half | CHFJPY | 1 | +16.905 | +0.0014 | +0.008% | +0.8% | 118 |
| 20 | C1 fisher_transform/default | C2 coral/half | VOL mass_index/double | BASE vidya/half | EXIT fisher_transform/double | GBPJPY | 1 | +16.682 | +0.0013 | +0.008% | +0.8% | 201 |
| 21 | C1 coral/default | C2 coral/half | VOL ttm_squeeze/double | BASE ema/half | EXIT polychromatic_momentum/half | CHFJPY | 1 | +16.679 | +0.0013 | +0.008% | +0.8% | 139 |
| 22 | C1 fisher_transform/default | C2 hieken_ashi_smoothed/default | VOL ttm_squeeze/double | BASE vidya/half | EXIT polychromatic_momentum/half | AUDJPY | 1 | +16.288 | +0.0013 | +0.008% | +0.8% | 103 |
| 23 | C1 parabolic_sar/half | C2 rex_oscillator/half | VOL ttm_squeeze/double | BASE hma/default | EXIT hieken_ashi_smoothed/double | GBPJPY | 1 | +16.195 | +0.0013 | +0.008% | +0.7% | 107 |
| 24 | C1 parabolic_sar/half | C2 rex_oscillator/half | VOL mass_index/double | BASE hma/default | EXIT hieken_ashi_smoothed/double | GBPJPY | 1 | +16.195 | +0.0013 | +0.008% | +0.7% | 107 |
| 25 | C1 center_of_gravity/default | C2 volatility_quality/half | VOL ttm_squeeze/double | BASE ema/half | EXIT polychromatic_momentum/half | CHFJPY | 1 | +16.149 | +0.0013 | +0.008% | +0.7% | 118 |
| 26 | C1 center_of_gravity/default | C2 volatility_quality/half | VOL ttm_squeeze/double | BASE ema/half | EXIT aroon/half | CHFJPY | 1 | +16.149 | +0.0013 | +0.008% | +0.7% | 118 |
| 27 | C1 coral/half | C2 rex_oscillator/default | VOL variance/double | BASE alma/half | EXIT ichimoku/double | EURAUD GBPAUD GBPJPY | 3 | +16.065 | +0.0013 | +0.007% | +0.7% | 329 |
| 28 | C1 coral/half | C2 halftrend/half | VOL efficiency_ratio/half | BASE alma/half | EXIT ichimoku/double | USDJPY | 1 | +16.065 | +0.0013 | +0.007% | +0.7% | 117 |
| 29 | C1 coral/default | C2 coral/half | VOL mass_index/double | BASE alma/half | EXIT bears_bulls_impulse/double | GBPJPY | 1 | +16.040 | +0.0013 | +0.007% | +0.7% | 283 |
| 30 | C1 ssl_channel/half | C2 coral/default | VOL mass_index/double | BASE alma/half | EXIT ichimoku/double | EURJPY | 1 | +15.971 | +0.0013 | +0.007% | +0.7% | 203 |
| 31 | C1 fisher_transform/default | C2 hieken_ashi_smoothed/default | VOL ttm_squeeze/double | BASE vidya/half | EXIT mama_fama/half | AUDJPY | 1 | +15.428 | +0.0012 | +0.007% | +0.7% | 103 |
| 32 | C1 fisher_transform/default | C2 coral/default | VOL ttm_squeeze/double | BASE super_smoother_2pole/default | EXIT fisher_transform/double | CHFJPY | 1 | +15.397 | +0.0012 | +0.007% | +0.7% | 163 |
| 33 | C1 fisher_transform/default | C2 fisher_transform/half | VOL ttm_squeeze/double | BASE super_smoother_2pole/default | EXIT fisher_transform/double | CHFJPY | 1 | +14.973 | +0.0012 | +0.007% | +0.7% | 191 |
| 34 | C1 vortex/half | C2 volatility_quality/half | VOL mass_index/double | BASE vidya/half | EXIT polychromatic_momentum/half | AUDJPY | 1 | +14.819 | +0.0012 | +0.007% | +0.7% | 136 |
| 35 | C1 fisher_transform/default | C2 fisher_transform/double | VOL volatility_ratio/half | BASE super_smoother_2pole/half | EXIT relative_vigor_index/default | AUDJPY | 1 | +14.718 | +0.0012 | +0.007% | +0.7% | 134 |
| 36 | C1 vortex/half | C2 volatility_quality/half | VOL ttm_squeeze/double | BASE vidya/half | EXIT polychromatic_momentum/half | AUDJPY | 1 | +14.697 | +0.0012 | +0.007% | +0.7% | 134 |
| 37 | C1 hieken_ashi_smoothed/half | C2 ehlers_reverse_ema/half | VOL ttm_squeeze/double | BASE vidya/half | EXIT coral/double | AUDUSD | 1 | +14.486 | +0.0012 | +0.007% | +0.7% | 129 |
| 38 | C1 fisher_transform/default | C2 coral/default | VOL ttm_squeeze/double | BASE vidya/half | EXIT chandelier/double | CHFJPY | 1 | +14.472 | +0.0012 | +0.007% | +0.7% | 168 |
| 39 | C1 fisher_transform/default | C2 fisher_transform/default | VOL ttm_squeeze/double | BASE super_smoother_2pole/default | EXIT fisher_transform/double | CHFJPY | 1 | +14.444 | +0.0012 | +0.007% | +0.7% | 205 |
| 40 | C1 mama_fama/half | C2 coral/half | VOL ttm_squeeze/double | BASE frama/double | EXIT donchian_breakout/half | GBPNZD | 1 | +14.341 | +0.0012 | +0.007% | +0.7% | 105 |
| 41 | C1 coral/half | C2 parabolic_sar/half | VOL choppiness_index/default | BASE vidya/half | EXIT relative_vigor_index/default | EURAUD | 1 | +14.295 | +0.0011 | +0.007% | +0.7% | 143 |
| 42 | C1 coral/half | C2 parabolic_sar/half | VOL choppiness_index/default | BASE vidya/default | EXIT relative_vigor_index/default | EURAUD | 1 | +14.295 | +0.0011 | +0.007% | +0.7% | 143 |
| 43 | C1 fisher_transform/default | C2 fisher_transform/double | VOL mass_index/double | BASE super_smoother_2pole/half | EXIT relative_vigor_index/double | AUDJPY CADJPY | 2 | +14.251 | +0.0011 | +0.007% | +0.7% | 522 |
| 44 | C1 kuskus_starlight/half | C2 parabolic_sar/default | VOL ttm_squeeze/double | BASE fantail_vma/default | EXIT trend_direction_force_index/double | GBPJPY | 1 | +14.183 | +0.0011 | +0.007% | +0.7% | 72 |
| 45 | C1 parabolic_sar/half | C2 rex_oscillator/half | VOL ttm_squeeze/double | BASE hma/default | EXIT chandelier/double | GBPJPY | 1 | +14.154 | +0.0011 | +0.007% | +0.7% | 107 |
| 46 | C1 parabolic_sar/half | C2 rex_oscillator/half | VOL mass_index/double | BASE hma/default | EXIT chandelier/double | GBPJPY | 1 | +14.154 | +0.0011 | +0.007% | +0.7% | 107 |
| 47 | C1 fx_sniper_ergodic_cci/default | C2 ssl_channel/half | VOL choppiness_index/default | BASE alma/double | EXIT relative_vigor_index/double | CADJPY | 1 | +13.992 | +0.0011 | +0.007% | +0.6% | 94 |
| 48 | C1 coral/default | C2 volatility_quality/half | VOL mass_index/double | BASE ema/half | EXIT qqe_mod/half | CHFJPY | 1 | +13.957 | +0.0011 | +0.006% | +0.6% | 113 |
| 49 | C1 coppock_curve/default | C2 parabolic_sar/default | VOL mass_index/double | BASE vidya/default | EXIT relative_vigor_index/double | CADJPY | 1 | +13.944 | +0.0011 | +0.006% | +0.6% | 104 |
| 50 | C1 coppock_curve/default | C2 parabolic_sar/default | VOL mass_index/double | BASE vidya/half | EXIT relative_vigor_index/double | CADJPY | 1 | +13.944 | +0.0011 | +0.006% | +0.6% | 104 |
| 51 | C1 fisher_transform/default | C2 coral/default | VOL mass_index/double | BASE vidya/half | EXIT polychromatic_momentum/half | EURJPY | 1 | +13.901 | +0.0011 | +0.006% | +0.6% | 186 |
| 52 | C1 fisher_transform/default | C2 fisher_transform/half | VOL ttm_squeeze/double | BASE super_smoother_2pole/default | EXIT polychromatic_momentum/half | CHFJPY | 1 | +13.831 | +0.0011 | +0.006% | +0.6% | 191 |
| 53 | C1 fisher_transform/double | C2 parabolic_sar/half | VOL mass_index/double | BASE vidya/half | EXIT donchian_breakout/double | NZDJPY | 1 | +13.796 | +0.0011 | +0.006% | +0.6% | 144 |
| 54 | C1 fisher_transform/double | C2 parabolic_sar/half | VOL mass_index/double | BASE vidya/half | EXIT adx_dmi/double | NZDJPY | 1 | +13.654 | +0.0011 | +0.006% | +0.6% | 144 |
| 55 | C1 fisher_transform/double | C2 parabolic_sar/half | VOL ttm_squeeze/double | BASE vidya/default | EXIT donchian_breakout/double | NZDJPY | 1 | +13.636 | +0.0011 | +0.006% | +0.6% | 142 |
| 56 | C1 fisher_transform/double | C2 parabolic_sar/half | VOL ttm_squeeze/double | BASE vidya/half | EXIT donchian_breakout/double | NZDJPY | 1 | +13.636 | +0.0011 | +0.006% | +0.6% | 142 |
| 57 | C1 vortex/half | C2 volatility_quality/half | VOL ttm_squeeze/double | BASE vidya/half | EXIT ichimoku/double | AUDJPY | 1 | +13.624 | +0.0011 | +0.006% | +0.6% | 135 |
| 58 | C1 coral/half | C2 rex_oscillator/default | VOL variance/double | BASE alma/half | EXIT waddah_attar_explosion/half | GBPAUD GBPJPY | 2 | +13.558 | +0.0011 | +0.006% | +0.6% | 214 |
| 59 | C1 fisher_transform/default | C2 center_of_gravity/half | VOL ttm_squeeze/double | BASE vidya/half | EXIT polychromatic_momentum/half | CHFJPY | 1 | +13.552 | +0.0011 | +0.006% | +0.6% | 165 |
| 60 | C1 ssl_channel/half | C2 fisher_transform/double | VOL mass_index/double | BASE hma/default | EXIT kuskus_starlight/half | GBPJPY | 1 | +13.513 | +0.0011 | +0.006% | +0.6% | 154 |

*2366 more in `winners.csv`.*

## Provenance

- `results/nnfx/books/winners.csv` -- 2426 algorithms
- `results/nnfx/books/books_gates.csv` -- the cell this book is
- `results/nnfx/bank/sleeve_bank_real.npz` -- every number above
