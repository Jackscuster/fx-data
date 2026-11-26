# BOOKS -- the four families, both rotations, both modes, five gates

**Item 3 of Jack's correction. `PROTOCOL.md` AMENDMENT 1, A1 to A5. Every book is built on its admission years and scored on the other years, so no number below is computed on data any of its sleeves was admitted on.**

## The construction

| family | what |
|---|---|
| **a_declared** | every admitted sleeve from the 6 published, the 10 hand-built, and A and B |
| **b_per_pair** | for each pair, the top K algorithms on THAT PAIR'S admission years. K swept 1 / 2 / 3 / 5 / 8 / 13 / 21 / 34 / 55 / 89 / 144 / 200 |
| **c_all_pairs** | the top K algorithms across all pairs, each trading only the pairs it was admitted on. K swept 10 / 20 / 50 / 100 / 200 / 500 / 1000 / 2000 / 3500 / 5000 |

| mode | what |
|---|---|
| **separate** | every sleeve its own position at equal risk, 1/N each |
| **voting** | Jack's 4 September rule: N signals on a pair are ONE position with N votes, cost on changes in the NET position |

Selection pool: **384334 algorithms** -- Source 3's 200,000 random draws plus every algorithm its local search evaluated -- times 28 pairs, so about **21.5 million sleeve evaluations** across the two windows. Null: **0 matched runs**, each one scrambling the world and repeating all of it.

## The gate table at Jack's declared threshold (share 0.25)

| rot | family | K | sleeves | R | R/yr | dip | R/dip | %/yr at B5 sizing | B1 | B2 | B3 | B4 | B5 | passer |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|---|---|
| R1 | a declared | 4 | 4 | +0.021 | +0.004 | 2.712 | +0.008 | +0.01 | -- | fail | **PASS** | **PASS** | fail | no |
| R1 | b per pair | 1 | 28 | +0.706 | +0.141 | 1.806 | +0.391 | +0.42 | -- | fail | **PASS** | **PASS** | fail | no |
| R1 | b per pair | 2 | 56 | +0.394 | +0.079 | 1.657 | +0.238 | +0.26 | -- | fail | **PASS** | **PASS** | fail | no |
| R1 | b per pair | 3 | 84 | +0.562 | +0.112 | 1.532 | +0.367 | +0.40 | -- | fail | **PASS** | **PASS** | fail | no |
| R1 | b per pair | 5 | 140 | +0.294 | +0.059 | 1.479 | +0.198 | +0.21 | -- | fail | **PASS** | **PASS** | fail | no |
| R1 | b per pair | 8 | 224 | +0.507 | +0.101 | 1.385 | +0.366 | +0.40 | -- | fail | **PASS** | **PASS** | fail | no |
| R1 | b per pair | 13 | 364 | +0.704 | +0.141 | 1.265 | +0.557 | +0.60 | -- | fail | **PASS** | **PASS** | fail | no |
| R1 | b per pair | 21 | 588 | +0.717 | +0.143 | 1.201 | +0.597 | +0.64 | -- | fail | **PASS** | **PASS** | fail | no |
| R1 | b per pair | 34 | 952 | +0.757 | +0.151 | 1.183 | +0.640 | +0.69 | -- | **PASS** | **PASS** | **PASS** | fail | no |
| R1 | b per pair | 55 | 1540 | +0.952 | +0.190 | 1.033 | +0.921 | +0.99 | -- | **PASS** | **PASS** | **PASS** | fail | no |
| R1 | b per pair | 89 | 2492 | +1.122 | +0.224 | 0.933 | +1.203 | +1.30 | -- | **PASS** | **PASS** | **PASS** | fail | no |
| R1 | b per pair | 144 | 4032 | +1.074 | +0.215 | 0.924 | +1.163 | +1.26 | -- | **PASS** | **PASS** | **PASS** | fail | no |
| R1 | b per pair | 200 | 5600 | +0.947 | +0.189 | 0.962 | +0.985 | +1.06 | -- | **PASS** | **PASS** | **PASS** | fail | no |
| R1 | c all pairs | 10 | 110 | +0.895 | +0.179 | 3.608 | +0.248 | +0.27 | -- | fail | **PASS** | **PASS** | fail | no |
| R1 | c all pairs | 20 | 217 | +1.352 | +0.270 | 3.234 | +0.418 | +0.45 | -- | fail | **PASS** | **PASS** | fail | no |
| R1 | c all pairs | 50 | 555 | +1.668 | +0.334 | 2.373 | +0.703 | +0.76 | -- | **PASS** | **PASS** | **PASS** | fail | no |
| R1 | c all pairs | 100 | 1107 | +1.329 | +0.266 | 2.112 | +0.629 | +0.68 | -- | **PASS** | **PASS** | **PASS** | fail | no |
| R1 | c all pairs | 200 | 2195 | +1.030 | +0.206 | 2.179 | +0.473 | +0.51 | -- | **PASS** | **PASS** | **PASS** | fail | no |
| R1 | c all pairs | 500 | 5233 | +1.101 | +0.220 | 1.793 | +0.614 | +0.66 | -- | **PASS** | **PASS** | **PASS** | fail | no |
| R1 | c all pairs | 1000 | 10140 | +1.052 | +0.210 | 1.853 | +0.568 | +0.61 | -- | **PASS** | **PASS** | **PASS** | fail | no |
| R1 | c all pairs | 2000 | 18771 | +0.944 | +0.189 | 1.689 | +0.559 | +0.60 | -- | **PASS** | **PASS** | **PASS** | fail | no |
| R1 | c all pairs | 3500 | 30454 | +0.597 | +0.119 | 1.707 | +0.350 | +0.38 | -- | fail | **PASS** | **PASS** | fail | no |
| R1 | c all pairs | 5000 | 41330 | +0.520 | +0.104 | 1.646 | +0.316 | +0.34 | -- | fail | **PASS** | **PASS** | fail | no |
| R2 | a declared | 7 | 7 | -0.953 | -0.159 | 3.759 | -0.254 | -0.23 | -- | fail | fail | fail | fail | no |
| R2 | b per pair | 1 | 28 | -2.091 | -0.348 | 3.540 | -0.591 | -0.53 | -- | fail | fail | fail | fail | no |
| R2 | b per pair | 2 | 56 | -1.629 | -0.271 | 3.058 | -0.533 | -0.48 | -- | fail | fail | fail | fail | no |
| R2 | b per pair | 3 | 84 | -1.312 | -0.219 | 2.695 | -0.487 | -0.44 | -- | fail | fail | fail | fail | no |
| R2 | b per pair | 5 | 140 | -0.523 | -0.087 | 2.039 | -0.257 | -0.23 | -- | fail | fail | fail | fail | no |
| R2 | b per pair | 8 | 224 | -0.282 | -0.047 | 1.857 | -0.152 | -0.14 | -- | fail | fail | fail | fail | no |
| R2 | b per pair | 13 | 364 | -0.405 | -0.067 | 1.915 | -0.211 | -0.19 | -- | fail | fail | fail | fail | no |
| R2 | b per pair | 21 | 588 | +0.081 | +0.013 | 1.792 | +0.045 | +0.04 | -- | fail | **PASS** | fail | fail | no |
| R2 | b per pair | 34 | 952 | +0.349 | +0.058 | 1.752 | +0.199 | +0.18 | -- | fail | **PASS** | **PASS** | fail | no |
| R2 | b per pair | 55 | 1540 | +0.335 | +0.056 | 1.725 | +0.194 | +0.18 | -- | fail | **PASS** | **PASS** | fail | no |
| R2 | b per pair | 89 | 2492 | +0.369 | +0.061 | 1.665 | +0.222 | +0.20 | -- | fail | **PASS** | **PASS** | fail | no |
| R2 | b per pair | 144 | 4032 | +0.305 | +0.051 | 1.601 | +0.191 | +0.17 | -- | fail | **PASS** | **PASS** | fail | no |
| R2 | b per pair | 200 | 5600 | +0.469 | +0.078 | 1.516 | +0.310 | +0.28 | -- | fail | **PASS** | **PASS** | fail | no |
| R2 | c all pairs | 10 | 100 | +1.326 | +0.221 | 3.028 | +0.438 | +0.39 | -- | fail | **PASS** | **PASS** | fail | no |
| R2 | c all pairs | 20 | 202 | +1.812 | +0.302 | 3.203 | +0.566 | +0.51 | -- | fail | **PASS** | **PASS** | fail | no |
| R2 | c all pairs | 50 | 500 | +2.864 | +0.477 | 3.543 | +0.808 | +0.73 | -- | **PASS** | **PASS** | **PASS** | fail | no |
| R2 | c all pairs | 100 | 980 | +2.910 | +0.485 | 3.700 | +0.786 | +0.71 | -- | **PASS** | **PASS** | **PASS** | fail | no |
| R2 | c all pairs | 200 | 1861 | +2.443 | +0.407 | 3.590 | +0.681 | +0.61 | -- | **PASS** | **PASS** | **PASS** | fail | no |
| R2 | c all pairs | 500 | 4168 | +2.192 | +0.365 | 3.289 | +0.667 | +0.60 | -- | fail | **PASS** | **PASS** | fail | no |
| R2 | c all pairs | 1000 | 7725 | +1.565 | +0.261 | 3.091 | +0.506 | +0.46 | -- | fail | **PASS** | **PASS** | fail | no |
| R2 | c all pairs | 2000 | 14364 | +0.582 | +0.097 | 3.030 | +0.192 | +0.17 | -- | fail | **PASS** | **PASS** | fail | no |
| R2 | c all pairs | 3500 | 23551 | +0.323 | +0.054 | 2.697 | +0.120 | +0.11 | -- | fail | **PASS** | **PASS** | fail | no |
| R2 | c all pairs | 5000 | 31811 | +0.361 | +0.060 | 2.462 | +0.146 | +0.13 | -- | fail | **PASS** | **PASS** | fail | no |

*The `voting` mode is shown because it dominates `separate` everywhere -- see the cost section. The full table for both modes and all six share thresholds is `books_gates.csv`.*

## What netting saves

Both costs are charged on one convention -- half the round-trip spread on each change in notional, at the bar's own price -- so the difference between them is netting and nothing else. On a single sleeve the two agree exactly, and the separate figure agrees with `nnfxproto.cost_R` on the same trades to within 0.2%, the residual being entry-versus-exit pricing.

| rot | family | K | sleeves | cost separate | cost voting | saved | saved % |
|---|---|---:|---:|---:|---:|---:|---:|
| R1 | a declared | 4 | 4 | 0.565 | 0.512 | 0.053 | 9.4% |
| R1 | b per pair | 1 | 28 | 1.770 | 1.566 | 0.204 | 11.5% |
| R1 | b per pair | 2 | 56 | 1.639 | 1.425 | 0.214 | 13.0% |
| R1 | b per pair | 3 | 84 | 1.596 | 1.373 | 0.223 | 14.0% |
| R1 | b per pair | 5 | 140 | 1.539 | 1.317 | 0.222 | 14.4% |
| R1 | b per pair | 8 | 224 | 1.521 | 1.282 | 0.239 | 15.7% |
| R1 | b per pair | 13 | 364 | 1.502 | 1.256 | 0.246 | 16.4% |
| R1 | b per pair | 21 | 588 | 1.467 | 1.218 | 0.249 | 17.0% |
| R1 | b per pair | 34 | 952 | 1.433 | 1.180 | 0.253 | 17.7% |
| R1 | b per pair | 55 | 1540 | 1.389 | 1.137 | 0.252 | 18.1% |
| R1 | b per pair | 89 | 2492 | 1.345 | 1.092 | 0.253 | 18.8% |
| R1 | b per pair | 144 | 4032 | 1.314 | 1.060 | 0.253 | 19.3% |
| R1 | b per pair | 200 | 5600 | 1.311 | 1.054 | 0.257 | 19.6% |
| R1 | c all pairs | 10 | 110 | 2.788 | 2.503 | 0.285 | 10.2% |
| R1 | c all pairs | 20 | 217 | 2.744 | 2.466 | 0.278 | 10.1% |
| R1 | c all pairs | 50 | 555 | 2.522 | 2.239 | 0.282 | 11.2% |
| R1 | c all pairs | 100 | 1107 | 2.386 | 2.089 | 0.297 | 12.4% |
| R1 | c all pairs | 200 | 2195 | 2.346 | 2.057 | 0.289 | 12.3% |
| R1 | c all pairs | 500 | 5233 | 2.120 | 1.822 | 0.298 | 14.1% |
| R1 | c all pairs | 1000 | 10140 | 2.099 | 1.798 | 0.301 | 14.4% |
| R1 | c all pairs | 2000 | 18771 | 2.009 | 1.694 | 0.315 | 15.7% |
| R1 | c all pairs | 3500 | 30454 | 1.930 | 1.602 | 0.328 | 17.0% |
| R1 | c all pairs | 5000 | 41330 | 1.831 | 1.494 | 0.337 | 18.4% |
| R2 | a declared | 7 | 7 | 1.160 | 1.026 | 0.134 | 11.6% |
| R2 | b per pair | 1 | 28 | 1.902 | 1.701 | 0.201 | 10.6% |
| R2 | b per pair | 2 | 56 | 1.929 | 1.686 | 0.243 | 12.6% |
| R2 | b per pair | 3 | 84 | 1.826 | 1.584 | 0.242 | 13.2% |
| R2 | b per pair | 5 | 140 | 1.817 | 1.566 | 0.250 | 13.8% |
| R2 | b per pair | 8 | 224 | 1.805 | 1.540 | 0.265 | 14.7% |
| R2 | b per pair | 13 | 364 | 1.794 | 1.514 | 0.280 | 15.6% |
| R2 | b per pair | 21 | 588 | 1.785 | 1.493 | 0.292 | 16.3% |
| R2 | b per pair | 34 | 952 | 1.763 | 1.459 | 0.304 | 17.3% |
| R2 | b per pair | 55 | 1540 | 1.703 | 1.391 | 0.312 | 18.3% |
| R2 | b per pair | 89 | 2492 | 1.665 | 1.349 | 0.316 | 19.0% |
| R2 | b per pair | 144 | 4032 | 1.647 | 1.320 | 0.327 | 19.9% |
| R2 | b per pair | 200 | 5600 | 1.603 | 1.277 | 0.326 | 20.3% |
| R2 | c all pairs | 10 | 100 | 2.373 | 2.065 | 0.307 | 12.9% |
| R2 | c all pairs | 20 | 202 | 2.395 | 2.104 | 0.290 | 12.1% |
| R2 | c all pairs | 50 | 500 | 2.451 | 2.172 | 0.279 | 11.4% |
| R2 | c all pairs | 100 | 980 | 2.491 | 2.213 | 0.278 | 11.2% |
| R2 | c all pairs | 200 | 1861 | 2.502 | 2.192 | 0.310 | 12.4% |
| R2 | c all pairs | 500 | 4168 | 2.431 | 2.093 | 0.338 | 13.9% |
| R2 | c all pairs | 1000 | 7725 | 2.388 | 2.011 | 0.377 | 15.8% |
| R2 | c all pairs | 2000 | 14364 | 2.336 | 1.938 | 0.397 | 17.0% |
| R2 | c all pairs | 3500 | 23551 | 2.238 | 1.818 | 0.421 | 18.8% |
| R2 | c all pairs | 5000 | 31811 | 2.148 | 1.715 | 0.433 | 20.1% |

## The K curves, every share threshold

Jack's standing rule: every cut swept over its full range and reported as a curve. R on the scoring window, `voting` mode.

**b per pair, R1**

| share | 1 | 2 | 3 | 5 | 8 | 13 | 21 | 34 | 55 | 89 | 144 | 200 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.25 | +0.71 | +0.39 | +0.56 | +0.29 | +0.51 | +0.70 | +0.72 | +0.76 | +0.95 | +1.12 | +1.07 | +0.95 |
| 0.40 | +0.71 | +0.45 | +0.58 | +0.27 | +0.48 | +0.68 | +0.70 | +0.71 | +0.92 | +1.05 | +1.02 | +0.93 |
| 0.60 | +0.71 | +0.45 | +0.58 | +0.27 | +0.48 | +0.68 | +0.70 | +0.72 | +0.92 | +1.05 | +1.02 | +0.90 |
| 0.80 | +0.71 | +0.45 | +0.58 | +0.27 | +0.48 | +0.68 | +0.70 | +0.71 | +0.92 | +1.05 | +1.02 | +0.91 |
| 1.00 | +0.71 | +0.45 | +0.58 | +0.27 | +0.48 | +0.68 | +0.70 | +0.72 | +0.92 | +1.05 | +1.02 | +0.91 |
| off | +0.71 | +0.45 | +0.58 | +0.27 | +0.48 | +0.68 | +0.70 | +0.71 | +0.92 | +1.05 | +1.02 | +0.91 |

**b per pair, R2**

| share | 1 | 2 | 3 | 5 | 8 | 13 | 21 | 34 | 55 | 89 | 144 | 200 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.25 | -2.09 | -1.63 | -1.31 | -0.52 | -0.28 | -0.40 | +0.08 | +0.35 | +0.34 | +0.37 | +0.31 | +0.47 |
| 0.40 | -2.41 | -1.63 | -1.35 | -0.74 | -0.38 | -0.23 | +0.10 | +0.37 | +0.42 | +0.40 | +0.34 | +0.55 |
| 0.60 | -2.41 | -1.63 | -1.35 | -0.74 | -0.39 | -0.23 | +0.10 | +0.37 | +0.42 | +0.40 | +0.34 | +0.52 |
| 0.80 | -2.41 | -1.63 | -1.35 | -0.74 | -0.38 | -0.23 | +0.10 | +0.37 | +0.42 | +0.40 | +0.34 | +0.52 |
| 1.00 | -2.41 | -1.63 | -1.35 | -0.74 | -0.39 | -0.23 | +0.10 | +0.37 | +0.42 | +0.40 | +0.34 | +0.52 |
| off | -2.41 | -1.63 | -1.35 | -0.74 | -0.39 | -0.23 | +0.10 | +0.37 | +0.42 | +0.40 | +0.34 | +0.52 |

**c all pairs, R1**

| share | 10 | 20 | 50 | 100 | 200 | 500 | 1000 | 2000 | 3500 | 5000 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.25 | +0.89 | +1.35 | +1.67 | +1.33 | +1.03 | +1.10 | +1.05 | +0.94 | +0.60 | +0.52 |
| 0.40 | -0.33 | +0.23 | +0.76 | +1.02 | +0.97 | +1.04 | +1.19 | +1.00 | +0.71 | +0.57 |
| 0.60 | -0.04 | +0.41 | +0.53 | +0.90 | +1.37 | +0.96 | +0.95 | +0.78 | +0.59 | +0.51 |
| 0.80 | -0.25 | +0.15 | +0.52 | +0.67 | +1.14 | +0.81 | +0.55 | +0.51 | +0.42 | +0.43 |
| 1.00 | +0.09 | +0.39 | +0.49 | +0.46 | +1.07 | +0.79 | +0.43 | +0.34 | +0.29 | +0.29 |
| off | -0.41 | +0.30 | +0.41 | +0.32 | +0.92 | +0.87 | +0.39 | +0.28 | +0.27 | +0.26 |

**c all pairs, R2**

| share | 10 | 20 | 50 | 100 | 200 | 500 | 1000 | 2000 | 3500 | 5000 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.25 | +1.33 | +1.81 | +2.86 | +2.91 | +2.44 | +2.19 | +1.57 | +0.58 | +0.32 | +0.36 |
| 0.40 | -0.80 | +0.16 | +0.29 | +0.37 | +0.76 | +0.52 | +0.21 | +0.21 | +0.22 | +0.24 |
| 0.60 | -1.07 | -0.63 | -0.31 | +0.08 | +0.11 | +0.04 | -0.24 | -0.08 | +0.06 | +0.15 |
| 0.80 | -1.16 | -0.80 | -0.55 | -0.16 | +0.07 | -0.27 | -0.21 | -0.13 | -0.01 | +0.12 |
| 1.00 | -1.15 | -0.99 | -0.40 | -0.15 | +0.19 | -0.13 | -0.22 | -0.09 | +0.04 | +0.16 |
| off | -1.22 | -1.06 | -0.51 | -0.17 | +0.32 | -0.05 | -0.19 | -0.08 | +0.07 | +0.20 |

## Book (a), the declared 18, and its B4 nudge

Book (a) has no K, so A5 declared its admission count to be the 20-trade floor, moved to 15 and 30.

| rot | trade floor | share | mode | sleeves | R | R/yr | R/dip | %/yr at B5 sizing |
|---|---:|---:|---|---:|---:|---:|---:|---:|
| R1 | 15 | 0.25 | separate | 4 | -0.032 | -0.006 | -0.012 | -0.01 |
| R1 | 15 | 0.25 | voting | 4 | +0.021 | +0.004 | +0.008 | +0.01 |
| R1 | 20 | 0.25 | separate | 4 | -0.032 | -0.006 | -0.012 | -0.01 |
| R1 | 20 | 0.25 | voting | 4 | +0.021 | +0.004 | +0.008 | +0.01 |
| R1 | 30 | 0.25 | separate | 3 | +1.182 | +0.236 | +0.417 | +0.45 |
| R1 | 30 | 0.25 | voting | 3 | +1.235 | +0.247 | +0.442 | +0.48 |
| R2 | 15 | 0.25 | separate | 7 | -1.088 | -0.181 | -0.283 | -0.26 |
| R2 | 15 | 0.25 | voting | 7 | -0.953 | -0.159 | -0.254 | -0.23 |
| R2 | 20 | 0.25 | separate | 7 | -1.088 | -0.181 | -0.283 | -0.26 |
| R2 | 20 | 0.25 | voting | 7 | -0.953 | -0.159 | -0.254 | -0.23 |
| R2 | 30 | 0.25 | separate | 6 | -0.089 | -0.015 | -0.024 | -0.02 |
| R2 | 30 | 0.25 | voting | 6 | +0.053 | +0.009 | +0.015 | +0.01 |

## Book (d) COMBINED — a plus the best of b and c

A11 fixed the choice as a procedure so the null can apply the identical one: each family's best K by return per dip AVERAGED over the two rotations, then whichever family wins. B4 reads off that K one grid step down and up. A sleeve in both halves is held once.

| rotation | K | is_central_K | sleeves | sleeves_from_a | sleeves_from_winner | winner_family | winner_K | R | cell_baseline_R | excess_over_cell | B1b | R_per_dip | b5_pct_per_year | B2 | B3 | B4 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| R1 | 50 | 1 | 559 | 4 | 555 | c_all_pairs | 50 | +1.657 | -0.092 | +1.750 | 1 | +0.703 | +0.759 | 1 | 1 | +1.000 |
| R2 | 50 | 1 | 507 | 7 | 500 | c_all_pairs | 50 | +2.813 | +0.478 | +2.335 | 1 | +0.805 | +0.724 | 1 | 1 | +1.000 |

**B1 is blank for both families on purpose.** They were declared at 20:10 and 20:12, after the 19:41 null chain launched, so neither is called a passer until chain 2 lands. See A10 and A11.

## Book (e) FOUR-CELL — the true cross only

A10. Select on 15 pairs in one six-year window, trade the 13 OTHER pairs in the OTHER window. No shared pair, no shared year. Only the TRUE CROSS cell is shown here; all four cells are in the csv, and the other three are what forced B1b into existence.

| direction | cell_pairs | cell_years | K | sleeves | R | cell_baseline_R | excess_over_cell | B1b | R_per_dip | b5_pct_per_year | B2 | B4 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fwd | 13pairs | 2011_2015 | 10 | 130 | +4.760 | +0.807 | +3.953 | 1 | +2.791 | +3.014 | 1 | +1.000 |
| fwd | 13pairs | 2011_2015 | 20 | 260 | +4.205 | +0.807 | +3.398 | 1 | +2.695 | +2.911 | 1 | +1.000 |
| fwd | 13pairs | 2011_2015 | 50 | 650 | +3.974 | +0.807 | +3.167 | 1 | +2.617 | +2.826 | 1 | +1.000 |
| fwd | 13pairs | 2011_2015 | 100 | 1300 | +3.915 | +0.807 | +3.109 | 1 | +2.576 | +2.782 | 1 | +1.000 |
| fwd | 13pairs | 2011_2015 | 200 | 2600 | +4.322 | +0.807 | +3.515 | 1 | +2.711 | +2.928 | 1 | +1.000 |
| fwd | 13pairs | 2011_2015 | 500 | 6500 | +4.123 | +0.807 | +3.316 | 1 | +2.654 | +2.866 | 1 | +1.000 |
| fwd | 13pairs | 2011_2015 | 1000 | 13000 | +3.704 | +0.807 | +2.897 | 1 | +2.493 | +2.692 | 1 | +1.000 |
| fwd | 13pairs | 2011_2015 | 2000 | 26000 | +3.491 | +0.807 | +2.685 | 1 | +2.801 | +3.025 | 1 | +1.000 |
| fwd | 13pairs | 2011_2015 | 3500 | 45500 | +3.331 | +0.807 | +2.525 | 1 | +3.052 | +3.296 | 1 | +1.000 |
| fwd | 13pairs | 2011_2015 | 5000 | 65000 | +3.266 | +0.807 | +2.459 | 1 | +3.045 | +3.288 | 1 | +1.000 |
| rev | 15pairs | 2005_2010 | 10 | 150 | +1.490 | +1.383 | +0.107 | 1 | +0.410 | +0.369 | 0 | +1.000 |
| rev | 15pairs | 2005_2010 | 20 | 300 | +2.788 | +1.383 | +1.405 | 1 | +0.931 | +0.838 | 1 | +1.000 |
| rev | 15pairs | 2005_2010 | 50 | 750 | +4.252 | +1.383 | +2.869 | 1 | +1.613 | +1.452 | 1 | +1.000 |
| rev | 15pairs | 2005_2010 | 100 | 1500 | +4.674 | +1.383 | +3.292 | 1 | +1.762 | +1.586 | 1 | +1.000 |
| rev | 15pairs | 2005_2010 | 200 | 3000 | +4.526 | +1.383 | +3.144 | 1 | +1.819 | +1.637 | 1 | +1.000 |
| rev | 15pairs | 2005_2010 | 500 | 7500 | +4.250 | +1.383 | +2.867 | 1 | +1.871 | +1.684 | 1 | +1.000 |
| rev | 15pairs | 2005_2010 | 1000 | 15000 | +3.963 | +1.383 | +2.580 | 1 | +1.920 | +1.728 | 1 | +1.000 |
| rev | 15pairs | 2005_2010 | 2000 | 30000 | +3.800 | +1.383 | +2.417 | 1 | +2.107 | +1.896 | 1 | +1.000 |
| rev | 15pairs | 2005_2010 | 3500 | 52500 | +3.611 | +1.383 | +2.228 | 1 | +2.260 | +2.034 | 1 | +1.000 |
| rev | 15pairs | 2005_2010 | 5000 | 75000 | +3.357 | +1.383 | +1.974 | 1 | +2.289 | +2.060 | 1 | +1.000 |

**B1 is blank for both families on purpose.** They were declared at 20:10 and 20:12, after the 19:41 null chain launched, so neither is called a passer until chain 2 lands. See A10 and A11.

## What transfers and what does not — A13

Measured on the bank with no book in the way. Rank every algorithm by its total net R pooled over one set of pairs in one window; ask its mean net R per sleeve on the OTHER pairs in the OTHER window.

| | select | score | algorithms | Spearman rho | cell baseline | top decile | bottom decile | top − bottom |
|---|---|---|---:|---:|---:|---:|---:|---:|
| **fwd** | 15 pairs 2005-2010 | 13 pairs 2011-2015 | 164088 | **+0.2069** | +0.807 | **+2.129** | +0.481 | **+1.648** |
| **rev** | 13 pairs 2011-2015 | 15 pairs 2005-2010 | 110143 | **+0.1871** | +1.383 | **+2.521** | +1.105 | **+1.416** |

Against the SAME-PAIR figure from item 2: median per-pair rho **+0.0183**, mean **+0.0059**.

**An algorithm's quality transfers across currencies and decades at rho about +0.20; its fit to one particular pair transfers at about +0.01.** Every book result above follows from that asymmetry — per-pair selection fails its own cell baseline in one rotation, pooled selection clears it in both, and the four-cell excess is flat in K across three orders of magnitude, which is what a broad factor looks like and not what overfitting looks like.

| decile of the selection ranking | mean cross-cell R, fwd | mean cross-cell R, rev |
|---:|---:|---:|
| 1 | +2.129 | +2.521 |
| 2 | +1.393 | +2.164 |
| 3 | +1.236 | +1.985 |
| 4 | +1.117 | +1.725 |
| 5 | +0.954 | +1.464 |
| 6 | +0.759 | +1.527 |
| 7 | +0.818 | +1.491 |
| 8 | +0.866 | +1.525 |
| 9 | +0.776 | +1.428 |
| 10 | +0.481 | +1.105 |

## The verdict, plainly

**0 of 552 book cells clear B1 to B4. 0 are passers (B1 to B5).**

The best cell by percent a year is **R1 b per pair K=89 voting at share 0.25**: +1.30% a year, R/dip +1.203, and it is **10.70 percentage points short of 12%**.

## Provenance

- `results/nnfx/books/books_full_real.csv` -- 552 rows
- `results/nnfx/books/books_gates.csv` -- 552 rows
- `results/nnfx/books/books_declared_nudge.csv` -- 24 rows
- `results/nnfx/books/null/books_*.csv` -- 0 matched null runs
- `results/nnfx/PROTOCOL.md` -- AMENDMENT 1 is the governing text
