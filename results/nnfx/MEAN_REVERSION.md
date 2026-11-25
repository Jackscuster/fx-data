# MEAN REVERSION — item 4, Jack 25 November 2026

**A second TYPE of strategy, declared, three variants, no search.**

## Where the rule comes from, cited

`code/strat.py:52` — `meanrev(p, n, entry)`: the z-score of price against its own rolling `n`-bar mean and standard deviation, long at `z <= -entry`, short at `z >= entry`, flat at `|z| < 0.1`.

Its evidence is **`HANDOFF_3.md` §9**: a 38-config sweep over 28 pairs with costs on, in which `mean_reversion` had mean OOS Sharpe **+0.109** with 69% of pairs positive against `momentum` at **−0.225**, and the best single config was **n = 60, entry = 2.0** at mean OOS Sharpe 0.197 with 82% of pairs positive.

**One correction to the brief, because it changes what is being tested.** The request calls this "the conditional mean reversion rule from the early project work". The early work's CONDITION was the 9-box (`HANDOFF_3.md` §10: *"mean reversion works when price is MOVING and fails when it is flat"*, every flat box negative) — **not** a half-life and **not** a stationarity test. The repo has a Hurst exponent (`code/sig2.py:31`) and neither of the other two. So the half-life and the stationarity test specified in item 4 are **new and built here**, and the early work's own condition is named as the declared alternative it was.

## The three variants, and what is NOT varied

| variant | lookback n | entry z | stop z | target |
|---|---:|---:|---:|---|
| `MR60` | 60 | 2.0 | 3.0 | the mean (z = 0) |
| `MR20` | 20 | 2.0 | 3.0 | the mean (z = 0) |
| `MR120` | 120 | 2.0 | 3.0 | the mean (z = 0) |

`MR60` is the early work's best config as cited. `MR20` is one faster and `MR120` one slower. **`entry` is not varied at all** — varying it would be the search item 4 forbids. The stop is one further standard deviation beyond the entry stretch in every variant.

**The stop is at a fixed z, not a fixed distance from the fill, and that has a consequence worth stating.** An entry triggers at `|z| >= 2.0` but can fire at 2.5, in which case only 0.5σ of room is left to a 3.0σ stop. That is the literal reading of "stop beyond the stretch" and it is kept, but it means the risk per trade is not constant and the hit rate is structurally low.

## The condition, and which half of it actually binds

Both halves are measured on a trailing 252-bar window ending at t−1, from ONE regression `ds_t = a + b·s_{t−1} + e` on the spread (close minus its own n-bar mean) — computing them from two different fits would let them disagree about the same window, which is the thing "both must agree" is meant to rule out.

- **half-life** = −ln2 / ln(1+b), required finite, positive and no longer than the lookback `n`. A series that takes longer than its own window to revert is not reverting inside the window the rule trades on.
- **stationarity** = the Dickey-Fuller t on `b`, constant and no trend, against the large-sample 5% critical value **-2.86** (Fuller 1976; MacKinnon 1991). There is no statsmodels in this environment, so the statistic is computed directly and the critical value is a named constant in `code/nnfxmr.py` — stated rather than hidden behind a library call.

| variant | half-life passes | stationarity passes | **both** | median half-life | median DF t |
|---|---:|---:|---:|---:|---:|
| `MR120` | 96.7% | **9.3%** | 9.3% | 27.5 bars | -1.82 |
| `MR20` | 99.9% | **90.4%** | 90.4% | 7.5 bars | -3.39 |
| `MR60` | 98.8% | **18.0%** | 18.0% | 18.5 bars | -2.17 |

**The half-life is not binding and the stationarity test is the whole condition.** The half-life passes on 96.7% to 99.9% of bars; the ADF passes on 9.3% (`MR120`), 18.0% (`MR60`) and 90.4% (`MR20`), and "both" equals the ADF figure to the decimal in every variant. So "a pair's own half-life AND a stationarity test both agree" is, in practice, the stationarity test alone — and for `MR20` it barely gates anything at all, which is why `MR20` conditional and unconditional are nearly the same book (daily correlation 0.930).

## The results, unseen years 2010–2015

Realistic gap fills through `l2engine._gap_px`, the ambiguous bar resolved by the hourly path through `l2engine._amb_first`, costs from the standing table, the leverage cap on, R in the same 1.5-ATR unit as every other Layer 2 number. 2016–2020 computed and not reported.

| variant | conditional | RANGING gate | scope | R total | R/yr | R/yr ex best day | trades | worst dip | R per dip | t yearly | t block boot | years + | null p | best trade share | crisis share |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **`MR60`** | 1 | 0 | all_28 | **+14.210** | +2.368 | +1.332 | 379 | 26.914 | +0.528 | +0.648 | +0.501 | 3 of 6 | +0.155 | +0.253 | **0.487** |
| **`MR60`** | 1 | 0 | range_prone | **+2.802** | +0.467 | -0.026 | 118 | 16.469 | +0.170 | +0.140 | +0.181 | 3 of 6 | +0.310 | +1.255 | **1.117** |
| `MR60` | 1 | 1 | all_28 | +1.621 | +0.270 | -0.737 | 183 | 16.353 | +0.099 | +0.145 | +0.092 | 3 of 6 | +0.380 | +1.760 | **0.933** |
| `MR60` | 1 | 1 | range_prone | -5.068 | -0.845 | -1.115 | 44 | 9.120 | -0.556 | -0.780 | -0.718 | 2 of 6 | +0.675 | -0.752 | **0.292** |
| `MR60` | 0 | 0 | all_28 | -115.252 | -19.209 | -21.901 | 2210 | 201.706 | -0.571 | -1.033 | -1.001 | 1 of 6 | +0.620 | -0.051 | -0.148 |
| `MR60` | 0 | 0 | range_prone | -29.026 | -4.838 | -6.271 | 709 | 62.136 | -0.467 | -0.560 | -0.585 | 2 of 6 | +0.420 | -0.196 | -0.221 |
| `MR60` | 0 | 1 | all_28 | -35.926 | -5.988 | -7.153 | 826 | 56.880 | -0.632 | -1.848 | -0.879 | 1 of 6 | +0.525 | -0.126 | -0.110 |
| `MR60` | 0 | 1 | range_prone | -16.478 | -2.746 | -3.099 | 187 | 27.830 | -0.592 | -0.974 | -0.999 | 1 of 6 | +0.625 | -0.219 | +0.044 |
| `MR20` | 1 | 0 | all_28 | -9.627 | -1.604 | -3.452 | 2601 | 63.603 | -0.151 | -0.167 | -0.143 | 2 of 6 | +0.190 | -0.328 | -0.714 |
| **`MR20`** | 1 | 0 | range_prone | **+14.366** | +2.394 | +1.565 | 869 | 25.842 | +0.556 | +0.414 | +0.427 | 3 of 6 | +0.190 | +0.210 | **0.116** |
| `MR20` | 1 | 1 | all_28 | -39.898 | -6.650 | -7.620 | 879 | 48.580 | -0.821 | -1.651 | -1.338 | 1 of 6 | +0.675 | -0.076 | -0.253 |
| `MR20` | 1 | 1 | range_prone | -1.096 | -0.183 | -0.509 | 230 | 14.861 | -0.074 | -0.112 | -0.074 | 3 of 6 | +0.455 | -2.235 | -1.400 |
| `MR20` | 0 | 0 | all_28 | -23.808 | -3.968 | -6.354 | 2931 | 62.750 | -0.379 | -0.292 | -0.295 | 2 of 6 | +0.260 | -0.167 | -0.049 |
| `MR20` | 0 | 0 | range_prone | +17.359 | +2.893 | +1.792 | 975 | 29.060 | +0.597 | +0.592 | +0.483 | 4 of 6 | +0.170 | +0.218 | **0.120** |
| `MR20` | 0 | 1 | all_28 | -44.638 | -7.440 | -8.410 | 972 | 54.899 | -0.813 | -1.660 | -1.428 | 2 of 6 | +0.730 | -0.081 | -0.220 |
| `MR20` | 0 | 1 | range_prone | +1.886 | +0.314 | -0.010 | 256 | 12.655 | +0.149 | +0.166 | +0.123 | 4 of 6 | +0.365 | +2.126 | **1.563** |
| **`MR120`** | 1 | 0 | all_28 | **+18.507** | +3.084 | +2.270 | 145 | 23.620 | +0.784 | +0.602 | +0.673 | 3 of 6 | +0.110 | +0.280 | **0.736** |
| `MR120` | 1 | 0 | range_prone | -10.711 | -1.785 | -2.095 | 58 | 20.174 | -0.531 | -0.586 | -0.935 | 3 of 6 | +0.635 | -0.405 | **0.350** |
| `MR120` | 1 | 1 | all_28 | -9.811 | -1.635 | -2.048 | 83 | 21.996 | -0.446 | -0.844 | -0.867 | 2 of 6 | +0.685 | -0.340 | **0.148** |
| `MR120` | 1 | 1 | range_prone | -7.058 | -1.176 | -1.389 | 34 | 14.169 | -0.498 | -0.993 | -0.874 | 2 of 6 | +0.745 | -0.458 | -0.000 |
| `MR120` | 0 | 0 | all_28 | -83.542 | -13.924 | -16.489 | 1551 | 222.541 | -0.375 | -0.443 | -0.701 | 3 of 6 | +0.280 | -0.085 | -0.902 |
| `MR120` | 0 | 0 | range_prone | -45.808 | -7.635 | -9.064 | 492 | 62.335 | -0.735 | -0.622 | -0.849 | 4 of 6 | +0.525 | -0.156 | -0.518 |
| `MR120` | 0 | 1 | all_28 | -70.091 | -11.682 | -12.597 | 597 | 79.527 | -0.881 | -2.065 | -1.647 | 1 of 6 | +0.850 | -0.075 | -0.153 |
| `MR120` | 0 | 1 | range_prone | -41.742 | -6.957 | -7.339 | 153 | 46.856 | -0.891 | -2.039 | -2.175 | 1 of 6 | +0.845 | -0.088 | +0.001 |

### What that says, in order

1. **7 of the 24 cells are positive and not one of them reaches |t| = 2.** The best are `MR120` all_28 cond=1 gate=0 **+18.507 R** (t +0.602, null p +0.110); `MR20` range_prone cond=0 gate=0 **+17.359 R** (t +0.592, null p +0.170); `MR20` range_prone cond=1 gate=0 **+14.366 R** (t +0.414, null p +0.190). Every cell that DOES reach |t| ≥ 2 is negative (`MR120` all_28 t -2.065; `MR120` range_prone t -2.039).
2. **THE CONDITION IS DOING ALL THE WORK, and the size of that is the most striking number in the file.** On all 28 pairs with no gate: `MR120` goes from **-83.542 R unconditional to +18.507 R conditional** and `MR60` from -115.252 to +14.210. The worst dip falls from 222.5 to 23.6 on `MR120`. That is not a tweak — the unconditional rule is a disaster and the ADF filter is what makes it merely unproven.
3. **THE LAYER 1 `RANGING` GATE MAKES IT WORSE, and exactly where it matters.** Over all 12 comparisons it helps in 5 — but split them: among the **conditional** variants it helps in **1 of 6**, and among the unconditional ones in 4 of 6. So the gate only adds anything where there is no condition to add it to. It is a worse substitute for the ADF filter, not a complement to it. And the gated column is **not a walk-forward number**: `layer1_states.csv` says "IS to 2015 (cuts fitted)", so a `ranging` label on a 2010–2015 bar comes from a model whose cuts were fitted on a window containing that bar. The gate is in-sample and still loses.
4. **"Mean reversion for range-prone pairs" is NOT supported, and the way the comparison has to be made is the point.** On TOTAL R the range-prone group beats all 28 pairs in 9 of 12 comparisons — but that is not a fair comparison: range-prone is 9 pairs of 28, so a losing rule run on a third of the universe simply loses less. On **R per trade** it wins **5 of 12** and on **R per dip 6 of 12** — a coin flip. And the two best cells in the whole table disagree with each other: `MR120` is far worse on range-prone (-10.711 against +18.507 on all 28) while `MR20` is far better. That is exactly what item 3b predicts: the range-prone label is pre-2010 pair character and pair character does not persist (Spearman −0.456 into 2010–2015), so a grouping drawn from it should split the variants at random — and it does.
5. **FLAGGED: crisis dependence, over the 10% standing threshold on every positive cell.** `MR60` all_28 **48.7%**; `MR60` range_prone **111.7%**; `MR60` all_28 **93.3%**; `MR20` range_prone **11.6%**; `MR20` range_prone **12.0%**; `MR20` range_prone **156.3%**; `MR120` all_28 **73.6%**. The two conditional all-28 winners make most of their money in crisis windows, which for a mean-reversion rule is the opposite of reassuring — a stretch away from the mean during a crisis is exactly the stretch that does not come back.

## The daily correlation to candidate A — the number that decides it

A second TYPE of strategy earns its place in a book by being uncorrelated, not by being better. A sleeve at 0.0 making half as much as A is a better addition than one at 0.8 matching it.

| | `A` | `MR120_uncond` | `MR120` | `MR20_uncond` | `MR20` | `MR60_uncond` | `MR60` |
|---|---:|---:|---:|---:|---:|---:|---:||
| `A` | **1.000** | -0.341 | -0.124 | -0.339 | -0.338 | -0.397 | -0.197 |
| `MR120_uncond` | -0.341 | **1.000** | +0.430 | +0.373 | +0.300 | +0.792 | +0.416 |
| `MR120` | -0.124 | +0.430 | **1.000** | +0.067 | +0.079 | +0.299 | +0.600 |
| `MR20_uncond` | -0.339 | +0.373 | +0.067 | **1.000** | +0.930 | +0.594 | +0.276 |
| `MR20` | -0.338 | +0.300 | +0.079 | +0.930 | **1.000** | +0.501 | +0.301 |
| `MR60_uncond` | -0.397 | +0.792 | +0.299 | +0.594 | +0.501 | **1.000** | +0.470 |
| `MR60` | -0.197 | +0.416 | +0.600 | +0.276 | +0.301 | +0.470 | **1.000** |

**Every variant is NEGATIVELY correlated with A, from -0.397 to -0.124.** That is the genuinely valuable property in this document and it is the one thing here that is not borderline: a sleeve that loses when A wins and wins when A loses reduces a book's dip even if its own return is modest. `MR120` conditional and `MR20` conditional are also nearly independent of each other (+0.079), so they are not one sleeve wearing two labels.

## Per pair, the declared variants, conditional, no gate

| variant | pair | direction | trades | R total | R per trade | win rate | mean bars | range-prone? |
|---|---|---|---:|---:|---:|---:|---:|---|
| `MR20` | EURGBP | short | 41 | **+15.003** | +0.366 | 0.54 | 4 | no |
| `MR20` | CADCHF | short | 39 | **+11.228** | +0.288 | 0.51 | 5 | yes |
| `MR20` | USDJPY | long | 35 | **+10.077** | +0.288 | 0.46 | 5 | no |
| `MR20` | AUDCHF | long | 41 | **+8.731** | +0.213 | 0.39 | 9 | no |
| `MR20` | NZDCHF | long | 49 | **+8.442** | +0.172 | 0.39 | 5 | no |
| `MR20` | GBPNZD | long | 52 | **+8.244** | +0.159 | 0.35 | 6 | yes |
| `MR60` | CADJPY | short | 7 | **+7.902** | +1.129 | 0.43 | 8 | no |
| `MR20` | CHFJPY | short | 50 | **+7.478** | +0.150 | 0.34 | 5 | yes |
| `MR20` | CADJPY | short | 46 | **+7.278** | +0.158 | 0.35 | 5 | no |
| `MR120` | NZDJPY | short | 3 | **+7.135** | +2.378 | 1.00 | 53 | no |
| `MR20` | USDCHF | short | 47 | -10.927 | -0.232 | 0.19 | 3 | no |
| `MR20` | USDCAD | short | 64 | -10.607 | -0.166 | 0.22 | 4 | no |
| `MR20` | NZDUSD | long | 46 | -9.629 | -0.209 | 0.20 | 4 | no |
| `MR120` | EURAUD | long | 5 | -8.880 | -1.776 | 0.00 | 17 | yes |

75 of the 146 per-pair cells are positive (51.4%), and 3 of the top 10 are range-prone pairs against 30.8% of the universe.

## The verdict

**It is not proven and it is worth keeping as a sleeve candidate for item 5, for one reason: the negative correlation to A.** Taken on its own, nothing here clears anything — the best cell is `MR120` conditional on all 28 pairs at **+18.507 R over six years, +3.084 a year**, with t 0.602, null p 0.110, 3 of 6 years positive and **73.6% of its R from crisis windows**. On its own that is a candidate, not a result.

**What would settle it, and is not in item 4:** the crisis dependence has to be explained or removed, because a mean-reversion rule that earns three quarters of its money during crises is betting that the biggest stretches come back, and the one event this project has studied in detail — the SNB de-peg — is a stretch that did not. `GAP_FILLS.md` measures what being on the wrong side of that costs: up to −20 R at a normal stop.

**What it adds to a book is a separate question and that is item 5.** The correlation says it should help; its own numbers say it brings little to help with. The book test is where those two meet.

## Provenance

- `results/nnfx/mr_condition.csv` — 84 rows, md5 `d3e3e76c7628`
- `results/nnfx/mr_summary.csv` — 24 rows, md5 `24307cc41bc8`
- `results/nnfx/mr_per_pair.csv` — 146 rows, md5 `097a1cca4fd2`
- `results/nnfx/mr_trades.csv` — 34,830 rows, md5 `01745938fa2d`
- `results/nnfx/mr_corr.csv` — 7 rows, md5 `32d3890099fd`
