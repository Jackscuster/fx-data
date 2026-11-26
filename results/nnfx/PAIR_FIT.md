# PAIR_FIT -- does a strategy's fit to a pair carry?

**Item 2 of Jack's correction. `PROTOCOL.md` AMENDMENT 1, A6.3. This is the gate on item 3: if the fit does not persist, every searched book is noise by construction.**

## What is measured

For each of the 28 pairs, across **384334 algorithms** -- Source 3's 200,000 random draws plus every algorithm its local search evaluated:

| | |
|---|---|
| **RHO** | the Spearman rank correlation between an algorithm's net R on that pair in the early years and its net R on the **same pair** in the later years |
| **SHARE** | the fraction of sleeves ADMITTED on the early years (A2) that are positive on the later years |
| **BASELINE** | the same fraction over every sleeve with at least 20 trades, admitted or not. This is the honest comparison: if admission does not raise the share above its own baseline, admission selects nothing |

Both in both rotations, against **0 matched null runs** (scrambled data, the same search, the same bank).

## Pooled over all (algorithm, pair) sleeves

| rotation | share | real rho | null rho mean | null rho p95 | real admitted share positive later | its own baseline | null admitted share |
|---|---:|---:|---:|---:|---:|---:|---:|
| R1 | 0.25 | **+0.0038** | pending | -- | **0.4832** | 0.4888 | pending |
| R2 | 0.25 | **+0.0038** | pending | -- | **0.5128** | 0.5338 | pending |
| R1 | 0.40 | **+0.0038** | pending | -- | **0.4930** | 0.4888 | pending |
| R2 | 0.40 | **+0.0038** | pending | -- | **0.5206** | 0.5338 | pending |
| R1 | 0.60 | **+0.0038** | pending | -- | **0.4944** | 0.4888 | pending |
| R2 | 0.60 | **+0.0038** | pending | -- | **0.5248** | 0.5338 | pending |
| R1 | 0.80 | **+0.0038** | pending | -- | **0.4940** | 0.4888 | pending |
| R2 | 0.80 | **+0.0038** | pending | -- | **0.5282** | 0.5338 | pending |
| R1 | 1.00 | **+0.0038** | pending | -- | **0.4933** | 0.4888 | pending |
| R2 | 1.00 | **+0.0038** | pending | -- | **0.5299** | 0.5338 | pending |
| R1 | off | **+0.0038** | pending | -- | **0.4928** | 0.4888 | pending |
| R2 | off | **+0.0038** | pending | -- | **0.5310** | 0.5338 | pending |

## Per pair, rotation R1 (admit 2005-2010, score 2011-2015), share 0.25

| pair | real rho | null rho mean | null rho p05 | null rho p95 | outside the null? | admitted | share positive later | baseline |
|---|---:|---:|---:|---:|---|---:|---:|---:|
| EURCHF | +0.2136 | -- | -- | -- | pending | 2070 | 0.144 | 0.097 |
| AUDNZD | +0.1892 | -- | -- | -- | pending | 35495 | 0.769 | 0.697 |
| GBPJPY | +0.1609 | -- | -- | -- | pending | 35419 | 0.828 | 0.813 |
| EURUSD | +0.1538 | -- | -- | -- | pending | 26863 | 0.665 | 0.571 |
| EURCAD | +0.1150 | -- | -- | -- | pending | 6138 | 0.469 | 0.449 |
| NZDJPY | +0.0823 | -- | -- | -- | pending | 51294 | 0.638 | 0.653 |
| AUDUSD | +0.0671 | -- | -- | -- | pending | 16383 | 0.566 | 0.481 |
| AUDCAD | +0.0651 | -- | -- | -- | pending | 6440 | 0.235 | 0.258 |
| GBPUSD | +0.0570 | -- | -- | -- | pending | 11397 | 0.294 | 0.273 |
| NZDCHF | +0.0269 | -- | -- | -- | pending | 8228 | 0.236 | 0.188 |
| AUDCHF | +0.0261 | -- | -- | -- | pending | 597 | 0.610 | 0.460 |
| CADJPY | +0.0224 | -- | -- | -- | pending | 9864 | 0.708 | 0.604 |
| GBPAUD | +0.0213 | -- | -- | -- | pending | 3525 | 0.763 | 0.775 |
| EURGBP | +0.0184 | -- | -- | -- | pending | 19970 | 0.334 | 0.323 |
| AUDJPY | +0.0181 | -- | -- | -- | pending | 30962 | 0.593 | 0.652 |
| EURJPY | +0.0154 | -- | -- | -- | pending | 14865 | 0.860 | 0.812 |
| GBPCAD | +0.0149 | -- | -- | -- | pending | 6435 | 0.188 | 0.259 |
| GBPCHF | +0.0086 | -- | -- | -- | pending | 5520 | 0.390 | 0.465 |
| USDJPY | -0.0018 | -- | -- | -- | pending | 14997 | 0.507 | 0.420 |
| USDCAD | -0.0162 | -- | -- | -- | pending | 6599 | 0.373 | 0.348 |
| EURAUD | -0.0802 | -- | -- | -- | pending | 8031 | 0.628 | 0.635 |
| USDCHF | -0.1109 | -- | -- | -- | pending | 1985 | 0.553 | 0.703 |
| GBPNZD | -0.1143 | -- | -- | -- | pending | 25902 | 0.388 | 0.495 |
| NZDCAD | -0.1388 | -- | -- | -- | pending | 53497 | 0.195 | 0.232 |
| CHFJPY | -0.1390 | -- | -- | -- | pending | 8483 | 0.815 | 0.834 |
| EURNZD | -0.1407 | -- | -- | -- | pending | 36238 | 0.336 | 0.419 |
| CADCHF | -0.1422 | -- | -- | -- | pending | 202 | 0.272 | 0.523 |
| NZDUSD | -0.2274 | -- | -- | -- | pending | 55264 | 0.169 | 0.208 |

## Per pair, rotation R2 (admit 2011-2015, score 2005-2010), share 0.25

| pair | real rho | null rho mean | null rho p05 | null rho p95 | outside the null? | admitted | share positive later | baseline |
|---|---:|---:|---:|---:|---|---:|---:|---:|
| EURCHF | +0.2136 | -- | -- | -- | pending | 304 | 0.395 | 0.319 |
| AUDNZD | +0.1892 | -- | -- | -- | pending | 21773 | 0.786 | 0.754 |
| GBPJPY | +0.1609 | -- | -- | -- | pending | 22562 | 0.732 | 0.723 |
| EURUSD | +0.1538 | -- | -- | -- | pending | 9033 | 0.869 | 0.754 |
| EURCAD | +0.1150 | -- | -- | -- | pending | 4428 | 0.670 | 0.506 |
| NZDJPY | +0.0823 | -- | -- | -- | pending | 12662 | 0.852 | 0.793 |
| AUDUSD | +0.0671 | -- | -- | -- | pending | 5915 | 0.772 | 0.724 |
| AUDCAD | +0.0651 | -- | -- | -- | pending | 1268 | 0.326 | 0.464 |
| GBPUSD | +0.0570 | -- | -- | -- | pending | 1368 | 0.698 | 0.542 |
| NZDCHF | +0.0269 | -- | -- | -- | pending | 589 | 0.334 | 0.418 |
| AUDCHF | +0.0261 | -- | -- | -- | pending | 7229 | 0.067 | 0.192 |
| CADJPY | +0.0224 | -- | -- | -- | pending | 8387 | 0.478 | 0.458 |
| GBPAUD | +0.0213 | -- | -- | -- | pending | 21470 | 0.430 | 0.405 |
| EURGBP | +0.0184 | -- | -- | -- | pending | 3466 | 0.678 | 0.592 |
| AUDJPY | +0.0181 | -- | -- | -- | pending | 16791 | 0.780 | 0.782 |
| EURJPY | +0.0154 | -- | -- | -- | pending | 30164 | 0.587 | 0.488 |
| GBPCAD | +0.0149 | -- | -- | -- | pending | 590 | 0.429 | 0.487 |
| GBPCHF | +0.0086 | -- | -- | -- | pending | 11014 | 0.400 | 0.473 |
| USDJPY | -0.0018 | -- | -- | -- | pending | 3491 | 0.586 | 0.518 |
| USDCAD | -0.0162 | -- | -- | -- | pending | 1260 | 0.361 | 0.383 |
| EURAUD | -0.0802 | -- | -- | -- | pending | 19884 | 0.443 | 0.486 |
| USDCHF | -0.1109 | -- | -- | -- | pending | 33874 | 0.215 | 0.272 |
| GBPNZD | -0.1143 | -- | -- | -- | pending | 8474 | 0.503 | 0.634 |
| NZDCAD | -0.1388 | -- | -- | -- | pending | 560 | 0.729 | 0.810 |
| CHFJPY | -0.1390 | -- | -- | -- | pending | 31243 | 0.341 | 0.336 |
| EURNZD | -0.1407 | -- | -- | -- | pending | 6939 | 0.558 | 0.676 |
| CADCHF | -0.1422 | -- | -- | -- | pending | 10804 | 0.048 | 0.117 |
| NZDUSD | -0.2274 | -- | -- | -- | pending | 578 | 0.837 | 0.811 |

## The verdict, plainly

**A strategy's fit to a pair does not carry.** Admitting a sleeve on six years of one pair does not make it more likely to be profitable on the other six years of that same pair. In rotation R1 the admitted sleeves are positive later **48.3% of the time against a baseline of 48.9%**, and in R2 **51.3% against 53.4%** -- at or below the baseline in both. The pooled rank correlation is **+0.0038**.

The consequence for item 3 is stated here rather than left to be inferred: **every book built by selecting algorithms on a pair's admission years is selecting on something that does not persist.** Those books are reported in full because Jack asked for them, and B1 is the test that says so numerically, but this is the reason to expect them to fail it.

## Provenance

- `results/nnfx/books/fit_real.csv` -- 336 rows
- `results/nnfx/books/fitpooled_real.csv` -- 12 rows
- `results/nnfx/books/null/fit_*.csv` -- 0 null runs
- the bank: `results/nnfx/bank/sleeve_bank_real.npz`
- the algorithm list: `results/nnfx/bank/cand_index.npz`
