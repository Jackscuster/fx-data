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

## 157 of 576 cells on disk

### Member A

**The inherited configuration** — all three exits, stop 1.5 ATR, target 1.5x, trail on, no time stop — is R **+20.498**, R/yr **+3.416**, dip 13.584, **return per dip 1.509**, 746 trades. Everything below is measured against that row.

**The eight best cells by return per dip.**

| exit arm | stop | target | trail | time stop | R total | R/yr | R/yr ex best day | mean bars | worst dip | **R per dip** | t yearly | years + |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `all_three` | 1.0 | 1.5 | on | 20 | +42.372 | +7.062 | +6.159 | 6.6 | 17.492 | **+2.422** | +1.304 | 3 of 6 |
| `base_cross_only` | 1.0 | 1.5 | on | 20 | +45.217 | +7.536 | +6.633 | 7.2 | 20.545 | **+2.201** | +1.501 | 3 of 6 |
| `c1_flip_only` | 2.0 | 1.0 | on | 20 | +20.220 | +3.370 | +3.002 | 10.3 | 9.269 | **+2.182** | +1.472 | 5 of 6 |
| `c1_flip_only` | 2.0 | 1.0 | off | 20 | +19.760 | +3.293 | +2.926 | 11.4 | 9.110 | **+2.169** | +1.472 | 4 of 6 |
| `c1_flip_only` | 1.5 | 1.5 | on | 20 | +31.568 | +5.261 | +4.719 | 10.5 | 14.884 | **+2.121** | +1.315 | 4 of 6 |
| `all_three` | 2.0 | 1.5 | on | 20 | +18.730 | +3.122 | +2.670 | 6.9 | 8.862 | **+2.114** | +1.100 | 3 of 6 |
| `all_three` | 1.0 | 1.5 | off | 10 | +35.122 | +5.854 | +4.950 | 5.3 | 17.447 | **+2.013** | +1.613 | 3 of 6 |
| `c1_flip_only` | 1.0 | 1.5 | on | 20 | +46.631 | +7.772 | +6.958 | 8.5 | 23.186 | **+2.011** | +1.609 | 3 of 6 |

**Each factor on its own, averaged over every other cell** — which is what a factorial is for: a factor that only looks good in one corner is not a factor, it is a corner.

*exit rules*

| value | cells | mean R | mean R per dip | median R per dip | mean dip | mean trades |
|---|---:|---:|---:|---:|---:|---:|
| all_three | 72 | +20.391 | **+1.375** | +1.436 | 14.895 | 749 |
| base_cross_only | 13 | +29.378 | **+1.434** | +1.403 | 21.238 | 746 |
| c1_flip_only | 72 | +16.865 | **+0.973** | +1.011 | 19.979 | 654 |

*stop (ATR)*

| value | cells | mean R | mean R per dip | median R per dip | mean dip | mean trades |
|---|---:|---:|---:|---:|---:|---:|
| 1.0 | 61 | +28.615 | **+1.343** | +1.396 | 23.209 | 724 |
| 1.5 | 48 | +15.873 | **+1.062** | +1.052 | 16.720 | 699 |
| 2.0 | 48 | +11.602 | **+1.142** | +1.117 | 11.847 | 687 |

*target (x stop)*

| value | cells | mean R | mean R per dip | median R per dip | mean dip | mean trades |
|---|---:|---:|---:|---:|---:|---:|
| 1.0 | 56 | +16.443 | **+1.019** | +1.019 | 17.430 | 717 |
| 1.5 | 53 | +22.313 | **+1.412** | +1.563 | 17.244 | 704 |
| 2.0 | 48 | +20.019 | **+1.163** | +1.293 | 18.687 | 693 |

*trail*

| value | cells | mean R | mean R per dip | median R per dip | mean dip | mean trades |
|---|---:|---:|---:|---:|---:|---:|
| 0.0 | 77 | +15.571 | **+0.975** | +1.026 | 18.965 | 700 |
| 1.0 | 80 | +23.317 | **+1.408** | +1.412 | 16.584 | 710 |

*time stop (bars)*

| value | cells | mean R | mean R per dip | median R per dip | mean dip | mean trades |
|---|---:|---:|---:|---:|---:|---:|
| 0.0 | 40 | +13.525 | **+0.786** | +0.968 | 21.782 | 681 |
| 5.0 | 39 | +19.130 | **+1.209** | +1.099 | 16.066 | 735 |
| 10.0 | 39 | +19.265 | **+1.217** | +1.172 | 16.303 | 710 |
| 20.0 | 39 | +26.305 | **+1.581** | +1.561 | 16.752 | 695 |

**What A says.** The best cell is 2.422 return per dip against 1.509 for the inherited configuration, a factor of 1.61 — **and it is the maximum over 157 cells on one six-year sample**, so it is an upper bound on what is there and not a configuration to adopt. The one-factor tables above are the part worth reading: a factor whose mean moves consistently across its whole range is evidence, and a single corner cell is not.

## What the sweep does and does not change

1. **It does not close the gap to 12%** and could not: the best cell anywhere in the grid is a small multiple of the inherited configuration, against a target that needs a factor of ten.
2. **The inherited exit configuration was never tested**, and now it has been. Where the one-factor means move consistently, that is a real finding about the exits; where only one corner cell wins, it is not.
3. **Nothing here is adopted.** Changing the exits would mean re-running every stage table in the project, and on the evidence of a best-of-157 maximum that is not warranted. Jack decides.

## Provenance

- `results/nnfx/exit_grid.csv` — 157 rows, md5 `c62b6c953af7`
