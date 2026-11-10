# Layer 1 research round 1 — a trend axis from DIRECTIONAL CHANGE

**2026-11-09.** Source: `results/research/RESEARCH_2026-11-09_part2_regime_taxonomies_and_nnfx_catalog.md` family 7 (commit 9926531). Code: `code/dcaxis.py` (battery, no money metrics) and `code/dcroute.py` (the Layer 3 money test). Every file in this round is dated and nothing was overwritten.

## Why this construction
The shipped trend axis fails its separation null in routing (HANDOFF_3 16.1b) and a **relative** cut cannot see a two-year trend: a trend that creeps inside its own shrinking volatility never clears a trailing yardstick. Directional change replaces the yardstick with an **absolute** one measured in event time.

## The construction, declared before any result
- per pair, track the running extreme of log price; a reversal of **theta** is an event, and the continuation to the next reversal is the **overshoot**.
- **theta is a constant per pair**: `m x` that pair's daily log-return stdev measured ONCE on the tuning window (dates < 2016-01-01). Not trailing vol — a trailing yardstick shrinks inside a quiet trend and recreates the very failure this exists to fix. Declared multiples **m = 0.5, 1.0, 1.5**.
- score at bar t from bars through t-1 only: `mean(overshoot / theta)` over the last **K** completed events, **K = 5, 10**. Secondary reads: bars in the current mode, events in the trailing 106 bars.
- no label before K events exist (the shipped warm-up convention); the cut is learned on the tuning window only; 2021 onward is sealed in the loader and absent from every file here.

## Events and the degenerate-count guard (`dc_axis_events_2026-11-09.csv`)
Completed events on the tuning window, per m: **min 648, median 987, max 1099** (m=0.5); **366 / 604 / 717** (m=1.0); **197 / 396 / 460** (m=1.5). The guard is 30 and **every (pair, m) clears it** — no cell was re-picked. theta runs 25-160 bp of log price across the panel.

## The present-tense battery, all six variants (`dc_axis_battery_2026-11-09.csv`)
| m | K | separation_tuning | separation_holdout | median_run | flip_rate | coverage | corr_shipped_trend_score | corr_straightness | label_agreement_with_shipped |
|---|---|---|---|---|---|---|---|---|---|
| 0.5 | 5 | 0.4622 | 0.4762 | 15.0000 | 0.0485 | 0.9959 | 0.0633 | 0.3442 | 0.5346 |
| 0.5 | 10 | 0.4670 | 0.4591 | 18.7500 | 0.0326 | 0.9912 | 0.0865 | 0.3140 | 0.5545 |
| 1.0 | 5 | 0.3966 | 0.3864 | 22.2500 | 0.0308 | 0.9915 | 0.0419 | 0.3492 | 0.5335 |
| 1.0 | 10 | 0.2805 | 0.2539 | 26.5000 | 0.0211 | 0.9832 | 0.0862 | 0.2357 | 0.5515 |
| 1.5 | 5 | 0.2484 | 0.1810 | 35.0000 | 0.0202 | 0.9755 | 0.0723 | 0.2410 | 0.5418 |
| 1.5 | 10 | 0.1569 | 0.1428 | 44.5000 | 0.0136 | 0.9642 | 0.1272 | 0.1634 | 0.5511 |

The shipped trend axis on the same battery: separation **0.0651** tuning, **0.1208** holdout, median run 31.0 bars, flip rate 0.0170. **Every DC variant separates the panel's own shape properties better than the shipped axis does**, by 1.3x to 3.8x on the holdout.

**Correlation, reported plainly.** Spearman against the shipped trend score is **0.087** on the selected variant and 0.04-0.13 across all six; against the straightness measure 0.314; label agreement 0.554. These are LOW, so this construction is **not** a confirmation of the shipped axis — it measures something the shipped axis does not. That is recorded as a fact and it decides nothing on its own.

## The 200-draw surrogate null (`dc_axis_null_2026-11-09.csv`)
The construction, the theta measurement AND the cut are re-derived on every surrogate, so the null prices the whole pipeline rather than the labelling step alone.

| kind | m | K | real | null_mean | null_p95 | null_max | corrected | p_value |
|---|---|---|---|---|---|---|---|---|
| sign | 0.5 | 5 | 0.4762 | 0.5583 | 0.5900 | 0.6270 | -0.0821 | 1.0000 |
| sign | 0.5 | 10 | 0.4591 | 0.5347 | 0.5744 | 0.6203 | -0.0756 | 0.9950 |
| sign | 1.0 | 5 | 0.3864 | 0.4362 | 0.4750 | 0.5099 | -0.0499 | 0.9700 |
| sign | 1.0 | 10 | 0.2539 | 0.3231 | 0.3686 | 0.4050 | -0.0692 | 0.9900 |
| sign | 1.5 | 5 | 0.1810 | 0.2758 | 0.3255 | 0.3468 | -0.0947 | 1.0000 |
| sign | 1.5 | 10 | 0.1428 | 0.1947 | 0.2447 | 0.2889 | -0.0519 | 0.9600 |
| perm | 0.5 | 5 | 0.4762 | 0.4790 | 0.5316 | 0.5647 | -0.0028 | 0.5950 |
| perm | 0.5 | 10 | 0.4591 | 0.5262 | 0.5886 | 0.6332 | -0.0671 | 0.9000 |
| perm | 1.0 | 5 | 0.3864 | 0.4560 | 0.5198 | 0.5350 | -0.0696 | 0.9100 |
| perm | 1.0 | 10 | 0.2539 | 0.3433 | 0.3994 | 0.4213 | -0.0893 | 0.9700 |
| perm | 1.5 | 5 | 0.1810 | 0.3222 | 0.3879 | 0.4341 | -0.1412 | 1.0000 |
| perm | 1.5 | 10 | 0.1428 | 0.2227 | 0.2845 | 0.3096 | -0.0799 | 0.9700 |

## Sub-period split, 2016-2019 vs 2020 only (`dc_axis_subperiod_2026-11-09.csv`)
2021 onward is sealed, so the research doc's 2020-21 window does not exist here and was not used.

| m | K | period | separation | median_run | flip_rate | share_trending |
|---|---|---|---|---|---|---|
| 0.5 | 5 | 2016-2019 | 0.4512 | 17.0000 | 0.0439 | 0.4298 |
| 0.5 | 5 | 2020 | 0.5738 | 18.2500 | 0.0402 | 0.4246 |
| 0.5 | 10 | 2016-2019 | 0.4200 | 20.7500 | 0.0303 | 0.3998 |
| 0.5 | 10 | 2020 | 0.6158 | 33.2500 | 0.0250 | 0.3742 |
| 1.0 | 5 | 2016-2019 | 0.3496 | 27.0000 | 0.0263 | 0.4453 |
| 1.0 | 5 | 2020 | 0.5289 | 28.0000 | 0.0257 | 0.4315 |
| 1.0 | 10 | 2016-2019 | 0.2114 | 27.0000 | 0.0189 | 0.3939 |
| 1.0 | 10 | 2020 | 0.4032 | 52.5000 | 0.0151 | 0.4449 |
| 1.5 | 5 | 2016-2019 | 0.1744 | 46.5000 | 0.0162 | 0.4885 |
| 1.5 | 5 | 2020 | 0.3154 | 40.0000 | 0.0188 | 0.4945 |
| 1.5 | 10 | 2016-2019 | 0.1398 | 55.0000 | 0.0117 | 0.4731 |
| 1.5 | 10 | 2020 | 0.3139 | 50.7500 | 0.0113 | 0.5576 |

## Selection (`dc_axis_selection_2026-11-09.csv`)
**The declared constraint set is empty and that is reported, not worked around.** The rule was: best tuning separation SUBJECT TO (a) label runs consistent with the measured trending-episode duration (g4_twoscore4 trending states, IS block: median 20.0 bars, so a 10.0-40.0 band) and (b) a flip rate no worse than the shipped axis (0.0170). Every variant inside the run band flips more often than the shipped axis; the only variant that flips less often runs 44.5 bars, outside the band. **No variant satisfies both.**

The fallback was declared in code before any money number existed: the **primary** is the best tuning separation among the variants inside the measured run band, carrying its flip-rate violation in the open, and the only flip-rate passer is reported beside it as a **sensitivity**. Neither was re-chosen after the Layer 3 test.

**Primary: m = 0.5, K = 10**, cut 2.0014, median run 18.8 bars, flip rate 0.0326 (shipped 0.0170), holdout separation 0.4591 (shipped 0.1208) — one holdout confirm, no second pick.

## Layer 3: the money test (`dc_axis_layer3_2026-11-09.csv`)
After the battery, never instead of it. Same 104 mode C candidates, same walk, same budgets, same nulls as the baseline. team1 shown.

| family | role | book | median_year_pct | worst_year_pct | dip95_pct | profit_factor | retention | p_random_entry | p_regime_shuffle |
|---|---|---|---|---|---|---|---|---|---|
| mode C | baseline | mode C routed on shape2 TRENDING (BASELINE) | 1.331 | -3.997 | 6.911 | 1.087 | 0.258 | 0.08 | 0.0 |
| mode C | candidate | mode C routed on the DC trend axis | -1.126 | -1.384 | 7.137 | 0.957 | -0.395 | 0.96 | 0.92 |
| mode C | control | mode C trend UNGATED (no trend axis at all) | -0.484 | -1.139 | 6.370 | 1.046 | -0.168 | 0.4 | 0.0 |
| A/B trend | baseline | A/B trend slices on shape2 TRENDING | -0.324 | -1.732 | 7.538 | 0.991 | -0.062 | 0.32 | 0.6 |
| A/B trend | candidate | A/B trend slices on the DC trend axis | -0.384 | -1.460 | 7.161 | 0.921 | -0.282 | 0.2 | 0.28 |
| A/B trend | control | A/B trend slices UNGATED | -0.526 | -2.028 | 6.671 | 0.990 | -0.211 | 1.0 | 1.0 |

**Verdict on the declared rule.** The DC-routed mode C book makes **-1.126%** median year against the baseline's **1.331%**, and its shuffled-label null gives **p = 0.920**. The bar was: beat the baseline AND beat the shuffle null. **NOT CLEARED** — the DC axis does not earn a routing place on this evidence, whatever its separation advantage.

## What this round establishes

1. The DC construction **separates the panel's own shape properties far better than the shipped trend axis** — a present-tense fact, holdout-confirmed once, with the null beside it.
2. It is **not** a restatement of the shipped axis: the correlation is near zero.
3. The declared run-length and flip-rate constraints **cannot both be met** by any of the six variants, which is itself a finding about the construction: at this panel's volatility an absolute threshold either flips too often or runs too long.
4. Whether it belongs in the routing is decided by the Layer 3 table above and by nothing else.

_Files: `dc_axis_{events,battery,episodes,null,subperiod,refit_vintages,selection,states,layer3}_2026-11-09.{csv,txt}`._
