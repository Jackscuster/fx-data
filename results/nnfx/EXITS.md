# EXITS — item 6a, Jack 25 November 2026

**Read item 5 first.** The best book is 1.135% a year against a 12% target, a factor of 10.6 short. An exit sweep is not going to close that, and this document does not present it as if it might. It is worth running because a 2x on the best sleeve is still a 2x, and because the exit configuration every result so far was computed under was **inherited, not tested**.

## The grid — the full factorial, nothing chosen

| factor | values |
|---|---|
| exit rules | all three together, then **each alone**: c1 flip / baseline cross / exit indicator |
| stop | 1.0, 1.5, 2.0 ATR |
| first target | 1.0, 1.5, 2.0 x the stop |
| trail | on and off |
| time stop | off, 5, 10, 20 bars |

4 x 3 x 3 x 2 x 4 = **288 cells per member**, A and B = **576 walk-forward stitches**. Each cell is the full six-step stitch with its own settings chosen on its own tuning years; only the exit configuration changes.

**Two things the apparatus needed first, both regression-proven.**

1. **The engine had no time stop.** `l2engine.run_bars` now takes `time_stop_bars`, default 0 = off, checked **after** the three signal exits so a bar on which a signal also fires is attributed to the signal and not to the clock — otherwise a short time stop would silently absorb the very exits being measured. With it at 0 the engine is byte-identical to before: SHA `e5264776bbacc833` on six base/plan cells over four pairs, the same check the gap-fill change passed.
2. **The exit-indicator slot was blank.** Stage 2 zeroed `x_el/x_es` because the exit slot was not its question, so `exit_on_exit_ind=True` had nothing to fire on and "each alone" would have been two arms, not three. The arrays `E.prepare` already computes are now kept when the exit indicator is under test. The family has exactly one member, `adx_dmi_exit`, so **no choice is being made**.

## 576 of 576 cells on disk

### Member A

**The inherited configuration** — all three exits, stop 1.5 ATR, target 1.5x, trail on, no time stop — is R **+20.498**, R/yr **+3.416**, dip 13.584, **return per dip 1.509**, 746 trades. Everything below is measured against that row.

**The eight best cells by return per dip.**

| exit arm | stop | target | trail | time stop | R total | R/yr | R/yr ex best day | mean bars | worst dip | **R per dip** | t yearly | years + |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `all_three` | 1.0 | 1.5 | on | 20 | +42.372 | +7.062 | +6.159 | 6.6 | 17.492 | **+2.422** | +1.304 | 3 of 6 |
| `base_cross_only` | 2.0 | 1.5 | on | 20 | +21.384 | +3.564 | +3.112 | 7.8 | 8.876 | **+2.409** | +1.330 | 4 of 6 |
| `base_cross_only` | 2.0 | 1.5 | off | 10 | +19.153 | +3.192 | +2.741 | 6.0 | 8.283 | **+2.312** | +1.647 | 5 of 6 |
| `base_cross_only` | 2.0 | 1.5 | on | 10 | +18.698 | +3.116 | +2.665 | 5.9 | 8.393 | **+2.228** | +1.488 | 4 of 6 |
| `base_cross_only` | 1.0 | 1.5 | on | 20 | +45.217 | +7.536 | +6.633 | 7.2 | 20.545 | **+2.201** | +1.501 | 3 of 6 |
| `c1_flip_only` | 2.0 | 1.0 | on | 20 | +20.220 | +3.370 | +3.002 | 10.3 | 9.269 | **+2.182** | +1.472 | 5 of 6 |
| `c1_flip_only` | 2.0 | 1.0 | off | 20 | +19.760 | +3.293 | +2.926 | 11.4 | 9.110 | **+2.169** | +1.472 | 4 of 6 |
| `base_cross_only` | 1.5 | 1.5 | on | 20 | +28.135 | +4.689 | +4.087 | 7.7 | 13.005 | **+2.163** | +1.237 | 4 of 6 |

**Each factor on its own, averaged over every other cell** — which is what a factorial is for: a factor that only looks good in one corner is not a factor, it is a corner.

*exit rules*

| value | cells | mean R | mean R per dip | median R per dip | mean dip | mean trades |
|---|---:|---:|---:|---:|---:|---:|
| all_three | 72 | +20.391 | **+1.375** | +1.436 | 14.895 | 749 |
| base_cross_only | 72 | +22.029 | **+1.464** | +1.511 | 15.854 | 742 |
| c1_flip_only | 72 | +16.865 | **+0.973** | +1.011 | 19.979 | 654 |
| exit_ind_only | 72 | +21.661 | **+1.311** | +1.328 | 17.080 | 701 |

*stop (ATR)*

| value | cells | mean R | mean R per dip | median R per dip | mean dip | mean trades |
|---|---:|---:|---:|---:|---:|---:|
| 1.0 | 96 | +29.721 | **+1.359** | +1.412 | 23.287 | 724 |
| 1.5 | 96 | +17.213 | **+1.160** | +1.243 | 16.082 | 709 |
| 2.0 | 96 | +13.776 | **+1.323** | +1.387 | 11.487 | 701 |

*target (x stop)*

| value | cells | mean R | mean R per dip | median R per dip | mean dip | mean trades |
|---|---:|---:|---:|---:|---:|---:|
| 1.0 | 96 | +16.370 | **+1.089** | +1.071 | 16.240 | 719 |
| 1.5 | 96 | +22.749 | **+1.494** | +1.613 | 16.364 | 710 |
| 2.0 | 96 | +21.591 | **+1.260** | +1.378 | 18.251 | 705 |

*trail*

| value | cells | mean R | mean R per dip | median R per dip | mean dip | mean trades |
|---|---:|---:|---:|---:|---:|---:|
| 0.0 | 144 | +17.299 | **+1.099** | +1.136 | 17.866 | 710 |
| 1.0 | 144 | +23.174 | **+1.462** | +1.462 | 16.038 | 713 |

*time stop (bars)*

| value | cells | mean R | mean R per dip | median R per dip | mean dip | mean trades |
|---|---:|---:|---:|---:|---:|---:|
| 0.0 | 72 | +15.252 | **+0.865** | +0.925 | 20.473 | 696 |
| 5.0 | 72 | +19.873 | **+1.316** | +1.317 | 15.381 | 735 |
| 10.0 | 72 | +20.123 | **+1.339** | +1.358 | 15.568 | 713 |
| 20.0 | 72 | +25.699 | **+1.603** | +1.609 | 16.385 | 702 |

**What A says.** The best cell is 2.422 return per dip against 1.509 for the inherited configuration, a factor of 1.61 — **and it is the maximum over 288 cells on one six-year sample**, so it is an upper bound on what is there and not a configuration to adopt. The one-factor tables above are the part worth reading: a factor whose mean moves consistently across its whole range is evidence, and a single corner cell is not.

### Member B

**The inherited configuration** — all three exits, stop 1.5 ATR, target 1.5x, trail on, no time stop — is R **+15.710**, R/yr **+2.618**, dip 29.561, **return per dip 0.531**, 2230 trades. Everything below is measured against that row.

**The eight best cells by return per dip.**

| exit arm | stop | target | trail | time stop | R total | R/yr | R/yr ex best day | mean bars | worst dip | **R per dip** | t yearly | years + |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `exit_ind_only` | 2.0 | 1.5 | on | 5 | +29.766 | +4.961 | +4.091 | 4.2 | 12.880 | **+2.311** | +1.269 | 3 of 6 |
| `c1_flip_only` | 1.5 | 1.0 | on | 20 | +34.906 | +5.818 | +4.418 | 7.8 | 15.432 | **+2.262** | +1.008 | 4 of 6 |
| `exit_ind_only` | 2.0 | 2.0 | on | 5 | +29.266 | +4.878 | +3.935 | 4.3 | 13.850 | **+2.113** | +1.153 | 3 of 6 |
| `exit_ind_only` | 2.0 | 1.0 | on | 20 | +24.164 | +4.027 | +3.082 | 7.5 | 11.898 | **+2.031** | +0.943 | 4 of 6 |
| `exit_ind_only` | 2.0 | 1.5 | off | 5 | +26.602 | +4.434 | +3.564 | 4.3 | 13.107 | **+2.030** | +1.153 | 3 of 6 |
| `c1_flip_only` | 2.0 | 1.0 | on | off | +29.996 | +4.999 | +4.054 | 8.8 | 15.422 | **+1.945** | +1.210 | 4 of 6 |
| `c1_flip_only` | 2.0 | 1.0 | on | 20 | +29.105 | +4.851 | +3.906 | 8.4 | 15.003 | **+1.940** | +1.180 | 4 of 6 |
| `c1_flip_only` | 1.5 | 1.0 | on | off | +34.798 | +5.800 | +4.400 | 8.0 | 18.051 | **+1.928** | +0.972 | 4 of 6 |

**Each factor on its own, averaged over every other cell** — which is what a factorial is for: a factor that only looks good in one corner is not a factor, it is a corner.

*exit rules*

| value | cells | mean R | mean R per dip | median R per dip | mean dip | mean trades |
|---|---:|---:|---:|---:|---:|---:|
| all_three | 72 | +6.428 | **+0.352** | +0.383 | 31.381 | 2232 |
| base_cross_only | 72 | +3.476 | **+0.233** | +0.290 | 33.641 | 2223 |
| c1_flip_only | 72 | +20.172 | **+0.944** | +1.121 | 28.836 | 1869 |
| exit_ind_only | 72 | +10.291 | **+0.634** | +0.488 | 34.055 | 1947 |

*stop (ATR)*

| value | cells | mean R | mean R per dip | median R per dip | mean dip | mean trades |
|---|---:|---:|---:|---:|---:|---:|
| 1.0 | 96 | +8.722 | **+0.369** | +0.347 | 45.515 | 2119 |
| 1.5 | 96 | +11.167 | **+0.582** | +0.547 | 28.855 | 2056 |
| 2.0 | 96 | +10.387 | **+0.671** | +0.651 | 21.564 | 2030 |

*target (x stop)*

| value | cells | mean R | mean R per dip | median R per dip | mean dip | mean trades |
|---|---:|---:|---:|---:|---:|---:|
| 1.0 | 96 | +20.143 | **+0.923** | +0.850 | 24.967 | 2083 |
| 1.5 | 96 | +13.292 | **+0.592** | +0.452 | 31.367 | 2064 |
| 2.0 | 96 | -3.160 | **+0.108** | -0.193 | 39.599 | 2056 |

*trail*

| value | cells | mean R | mean R per dip | median R per dip | mean dip | mean trades |
|---|---:|---:|---:|---:|---:|---:|
| 0.0 | 144 | +7.221 | **+0.422** | +0.385 | 34.130 | 2066 |
| 1.0 | 144 | +12.962 | **+0.660** | +0.582 | 29.826 | 2070 |

*time stop (bars)*

| value | cells | mean R | mean R per dip | median R per dip | mean dip | mean trades |
|---|---:|---:|---:|---:|---:|---:|
| 0.0 | 72 | +4.276 | **+0.283** | +0.166 | 38.916 | 2039 |
| 5.0 | 72 | +23.046 | **+1.137** | +1.060 | 21.293 | 2124 |
| 10.0 | 72 | +6.944 | **+0.352** | +0.359 | 33.597 | 2062 |
| 20.0 | 72 | +6.100 | **+0.391** | +0.307 | 34.107 | 2046 |

**What B says.** The best cell is 2.311 return per dip against 0.531 for the inherited configuration, a factor of 4.35 — **and it is the maximum over 288 cells on one six-year sample**, so it is an upper bound on what is there and not a configuration to adopt. The one-factor tables above are the part worth reading: a factor whose mean moves consistently across its whole range is evidence, and a single corner cell is not.

## What the sweep does and does not change

1. **It does not close the gap to 12%** and could not: the best cell anywhere in the grid is a small multiple of the inherited configuration, against a target that needs a factor of ten.
2. **The inherited exit configuration was never tested**, and now it has been. Where the one-factor means move consistently, that is a real finding about the exits; where only one corner cell wins, it is not.
3. **Nothing here is adopted.** Changing the exits would mean re-running every stage table in the project, and on the evidence of a best-of-576 maximum that is not warranted. Jack decides.

## Provenance

- `results/nnfx/exit_grid.csv` — 576 rows, md5 `02b7335dcd40`
