# PER-PAIR BANK — item 3a, Jack 25 November 2026

**The unit of account changed, so the bank did.** The 12%-a-year target is for the whole BOOK and the book is a handful of strategies each assigned to the pairs it suits, so every candidate is now banked **per pair, per direction, per year** as the primary output — not pooled and split on request. An assignment can be built from this file without re-running anything.

| | |
|---|---:|
| cells | **38,919** |
| candidates | 47 |
| pairs | 28 |
| unseen cells (2010–2015, the only reportable block) | 14,996 |
| tuning cells (2005–2009, may CHOOSE, never reported) | 11,876 |
| sealed cells (2016–2020, computed, NOT reported) | 12,047 |

**Three things about how it is built that change what the numbers mean.**

1. **The leverage cap is applied over the whole 28-pair frame and THEN split.** It has to be: the cap is a portfolio constraint over all pairs at once, so capping each pair separately would let every pair use the whole 1:30 and the sum of the slices would be a book no account could hold. A group's R in this file is its share of a book that was achievable **as a whole**.
2. **The year is the EXIT year**, matching every realized per-trade figure in the project. An entry-year convention would put a trade's R in a year the account did not receive it.
3. **"The 3 baselines as filters" is ambiguous and both readings are in.** `base_alone` is a baseline as its own entry rule (price crosses it, stage 1's form); `base_filter` is ichimoku plus that baseline (stage 2's form). Six runs instead of three, and no guess.

**NOTHING IN THIS FILE IS A SELECTION.** 28 pairs x 2 directions is 56 ways to find a winner by luck inside each candidate, and 14,996 unseen cells is a lot of lottery tickets. The selection rule and its label-shuffle null are item 3c in `PAIR_GROUPS.md`. **A cell in here reaching a nice number means nothing on its own**, which is why the per-pair view carries `best_trade_share` next to every total.

## Candidates on the unseen block, ranked

| kind | candidate | pairs | trades | R total | R/yr | cells positive | % of cells positive |
|---|---|---:|---:|---:|---:|---:|---:|
| candidate | **A** | 28 | 745 | **+41.489** | +6.915 | 129 of 279 | 46.2% |
| candidate | **B** | 28 | 1970 | **+29.587** | +4.931 | 172 of 331 | 52.0% |
| c1_alone | waddah_attar_explosion_signals | 28 | 995 | +19.629 | +3.272 | 153 of 331 | 46.2% |
| c1_alone | laguerre_filter_signals | 28 | 596 | +12.417 | +2.070 | 151 of 323 | 46.7% |
| c1_alone | glitch_index_signals | 28 | 1462 | +2.625 | +0.437 | 159 of 335 | 47.5% |
| c1_alone | adx_dmi_signals | 18 | 41 | +0.304 | +0.051 | 17 of 36 | 47.2% |
| c1_alone | lemantrend_signals | 28 | 893 | -1.166 | -0.194 | 146 of 331 | 44.1% |
| c1_alone | supertrend_signals | 28 | 1102 | -7.867 | -1.311 | 147 of 336 | 43.8% |
| c1_alone | j_tpo_signals | 28 | 561 | -11.964 | -1.994 | 136 of 324 | 42.0% |
| c1_alone | dpo_signals | 28 | 1414 | -12.756 | -2.126 | 154 of 304 | 50.7% |
| c1_alone | halftrend_signals | 28 | 99 | -13.331 | -2.222 | 38 of 99 | 38.4% |
| c1_alone | aroon_signals | 28 | 899 | -13.824 | -2.304 | 154 of 335 | 46.0% |
| c1_alone | qqe_mod_signals | 28 | 2009 | -14.143 | -2.357 | 159 of 336 | 47.3% |
| c1_alone | mama_fama_signals | 28 | 919 | -14.937 | -2.490 | 152 of 331 | 45.9% |
| c1_alone | donchian_breakout_signals | 28 | 527 | -16.849 | -2.808 | 139 of 316 | 44.0% |
| c1_alone | bears_bulls_impulse_signals | 28 | 3258 | -27.811 | -4.635 | 158 of 336 | 47.0% |
| c1_alone | chandelier_exit_signals | 28 | 1936 | -27.989 | -4.665 | 154 of 336 | 45.8% |
| base_alone | t3_baseline | 28 | 4251 | -28.943 | -4.824 | 156 of 336 | 46.4% |
| c1_alone | ehlers_reverse_ema_signals | 28 | 1755 | -34.939 | -5.823 | 151 of 336 | 44.9% |
| c1_alone | price_momentum_oscillator_signals | 28 | 755 | -35.583 | -5.931 | 138 of 319 | 43.3% |

*(27 further rows in the csv, all negative.)*

**Only 6 of the 47 candidates are positive on the unseen block**: A +41.489 R, B +29.587 R, waddah_attar_explosion_signals +19.629 R, laguerre_filter_signals +12.417 R, glitch_index_signals +2.625 R, adx_dmi_signals +0.304 R.

## How broadly based is each positive candidate?

This is the question the book plan actually turns on. A candidate whose R comes from two cells cannot be assigned to a set of pairs; it IS those two cells, and the assignment is a story told about them afterwards.

| kind | candidate | cells | positive | R total | top cell as a share of total | top 5 cells as a share |
|---|---|---:|---:|---:|---:|---:|
| candidate | A | 56 | 33 | +41.489 | **0.180** | **0.794** |
| candidate | B | 56 | 35 | +29.587 | **0.387** | **1.581** |
| c1_alone | waddah_attar_explosion_signals | 56 | 24 | +19.629 | **0.465** | **2.041** |
| c1_alone | laguerre_filter_signals | 56 | 29 | +12.417 | **0.616** | **2.257** |
| c1_alone | glitch_index_signals | 56 | 25 | +2.625 | **12.928** | **23.606** |
| c1_alone | adx_dmi_signals | 25 | 12 | +0.304 | **6.264** | **27.417** |

**A is the only one of them that is broadly based.** 33 of its 56 cells are positive, its best cell is **18.0%** of the total and its best five are **79.4%**. Every other positive candidate is worse on both counts, and the C1 alone are not in the same league — `glitch_index` has a single cell worth nearly thirteen times its own total, which means the rest of its book is a large negative that one cell is paying for. **That is what a per-pair bank is for: it makes the difference visible before anything is assigned.**

### Candidate A, its 56 cells, best and worst

| pair | direction | trades | R total | R per trade | years positive | best trade | best trade as a share |
|---|---|---:|---:|---:|---:|---:|---:|
| CADCHF | short | 16 | +7.452 | +0.466 | 5 of 6 | +1.512 | 0.203 |
| EURNZD | short | 10 | +7.156 | +0.716 | 4 of 6 | +1.665 | 0.233 |
| AUDNZD | short | 16 | +7.009 | +0.438 | 3 of 6 | +2.639 | 0.376 |
| EURUSD | short | 10 | +5.709 | +0.571 | 4 of 6 | +2.441 | 0.428 |
| EURJPY | short | 8 | +5.597 | +0.700 | 4 of 6 | +1.612 | 0.288 |
| USDCHF | long | 10 | +4.965 | +0.497 | 4 of 6 | +2.399 | 0.483 |
| EURAUD | short | 14 | +4.698 | +0.336 | 4 of 6 | +1.368 | 0.291 |
| AUDJPY | long | 13 | +4.568 | +0.351 | 2 of 6 | +4.667 | 1.022 |
| AUDNZD | long | 10 | -3.437 | -0.344 | 1 of 6 | +1.814 | -0.528 |
| AUDUSD | long | 21 | -4.571 | -0.218 | 2 of 6 | +1.881 | -0.412 |
| CADJPY | short | 15 | -4.883 | -0.326 | 0 of 6 | +0.860 | -0.176 |
| USDJPY | short | 18 | -5.670 | -0.315 | 0 of 6 | +0.559 | -0.099 |
| GBPCAD | short | 19 | -7.762 | -0.409 | 0 of 6 | +0.459 | -0.059 |

**6 of A's best 8 cells are SHORT**, and its four worst are all on the other side of a USD or CAD cross. That asymmetry is on record here and is not acted on: it is one candidate over six years, and splitting a book by direction as well as by pair would double the number of ways to find a winner by luck again.

## Provenance

- `results/nnfx/per_pair_bank.csv` — 38,919 rows, md5 `6ec21edb2447`
- `results/nnfx/per_pair_bank_pair.csv` — 2,596 rows, md5 `1811043c7bf6`
- `results/nnfx/per_pair_bank_cand.csv` — 47 rows, md5 `9a98c8510834`
