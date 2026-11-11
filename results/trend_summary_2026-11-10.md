# Layer 1 trend round 2 — anatomy of the failure, and two motivated constructions

**2026-11-10.** Parts 1-3 of one declared run. Code: `code/trendanat.py` (measurement only), `code/trendt12.py` (both constructions + battery, no money), `code/trendt12report.py` (Layer 3 + delivery). Standing rules applied throughout: 5pm series, log price, one-bar lag, cuts on the tuning window, one holdout confirm, 2021+ sealed, nulls before findings.

## Part 1 — why the shipped trend axis fails (measurement only, no fix attempted)

**1. The routed trend edge lives at episode onset and dies after it.** Share of each book's trade-year R earned in each third of a TRENDING episode:

| book | third | trades | total_R | mean_R | share_positive | share_of_book_R | share_of_book_loss |
|---|---|---|---|---|---|---|---|
| A/B trend routed | first | 17840 | 2193.009 | 0.123 | 0.403 | 0.602 | 0.287 |
| A/B trend routed | last | 19184 | 679.529 | 0.035 | 0.338 | 0.187 | 0.350 |
| A/B trend routed | middle | 20276 | 768.358 | 0.038 | 0.360 | 0.211 | 0.363 |
| mode C routed | first | 8882 | 1468.456 | 0.165 | 0.428 | 0.291 | 0.289 |
| mode C routed | last | 9950 | 1306.718 | 0.131 | 0.400 | 0.259 | 0.336 |
| mode C routed | middle | 12086 | 2263.578 | 0.187 | 0.444 | 0.449 | 0.376 |

On the holdout the A/B book takes **60% of its R in the first third** and almost nothing after; mode C is flatter (29% / 45% / 26%). Losses are spread evenly across all three thirds in both books (29-38%), so the problem is not where the losses are — it is that only the opening third pays.

**2. Half of all labelled trending episodes never went anywhere.** Progress measured in tuning-window vol units against a threshold learned IS (0.509):

| era | true_trend | episodes | median_bars | median_progress | median_efficiency |
|---|---|---|---|---|---|
| holdout | False | 166 | 26.000 | 0.276 | 0.095 |
| holdout | True | 132 | 20.000 | 0.790 | 0.308 |
| is | False | 396 | 23.000 | 0.238 | 0.073 |
| is | True | 397 | 23.000 | 0.953 | 0.270 |

True-trend share: **50.1% IS, 44.3% holdout**. The false ones are not shorter — median 23-26 bars against 20-23 — they are just directionless (efficiency 0.07-0.10 against 0.27-0.31). And the shipped trend score does not tell them apart: on the holdout the FALSE episodes score **higher** (0.494) than the true ones (0.329).

**3. The label arrives after most of the move is gone.** Median **24 bars** late against a median 23-bar episode, with **57% of the leg's total move already spent** before the label confirms, in both eras. A dwell-5 confirmation on a 20-bar move cannot be anything else.

**4. Why C survives trend routing while A/B do not.** All three modes enter at the same place (median ~0.50 of the episode), so entry timing is not the difference:

| book | mode | era | trades | median_entry_position | median_hold_days | share_exit_inside_episode | mean_R | share_positive |
|---|---|---|---|---|---|---|---|---|
| A/B | A | holdout | 26712 | 0.492 | 8.000 | 0.714 | 0.071 | 0.394 |
| A/B | A | is | 30902 | 0.520 | 10.000 | 0.725 | 0.986 | 0.447 |
| A/B | B | holdout | 30588 | 0.493 | 6.000 | 0.798 | 0.057 | 0.342 |
| A/B | B | is | 34828 | 0.513 | 6.000 | 0.812 | 1.105 | 0.386 |
| C | C | holdout | 30918 | 0.500 | 10.000 | 0.700 | 0.163 | 0.425 |
| C | C | is | 34494 | 0.538 | 11.000 | 0.712 | 0.596 | 0.492 |

C holds **10-11 days against B's 6**, exits inside the episode least often (0.70 vs 0.80), and carries the highest share of winners (0.43 holdout vs A 0.39, B 0.34). C survives because its exit rule keeps it in the move, not because the regime read puts it in at a better moment.

### What Part 1 establishes
The shipped trend axis fails for two measurable reasons, neither of which is a threshold-tuning problem: **it labels directionless episodes as trends half the time**, and **it confirms roughly one median-trend-length after the move began**. Any replacement has to fix one of those two things.

## Parts 2 and 3 — the two constructions

**T1, trend as broken chop.** FX's resting state is mean reversion, so trend is the failure of snap-back. Built entirely from the existing chop machinery (`structure.swings` at the shipped N=19, the same boundary the chop measures track): a break is a close outside the boundary, and it either snaps back inside within R bars or holds. Score = share of breaks held over the shipped 106-bar window; secondary = net progress beyond the broken boundary in tuning-window vol units. Declared R = 5, 10.

**T2, currency-leg trend.** Trends are currency stories. Strength per currency = cumulative log change against the equal-weight basket of the other seven over 106 bars, from the 7 USD legs, in that leg's tuning-window vol (constant). Pair score = |strength X − strength Y|; signed version secondary. **This construction has nothing to sweep** — window and dwell are the shipped ones and there is no third knob.

### The battery (`trend_t12_battery_2026-11-10.csv`)

| variant | family | knob | cut | separation_tuning | separation_holdout | median_run | flip_rate | coverage | share_trending | corr_shipped_trend | corr_shipped_chop | label_agreement_shipped |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T1_R5 | T1 broken chop | R=5 | 0.5000 | 0.0863 | 0.1086 | 70.0000 | 0.0104 | 0.9265 | 0.5382 | 0.2721 | -0.3167 | 0.5758 |
| T1_R10 | T1 broken chop | R=10 | 0.3333 | 0.0794 | 0.1315 | 71.0000 | 0.0105 | 0.9265 | 0.5806 | 0.3496 | -0.3840 | 0.5769 |
| T2 | T2 currency leg | none | 0.5670 | 0.0610 | 0.0370 | 32.5000 | 0.0192 | 0.9764 | 0.4596 | 0.7306 | -0.1977 | 0.6800 |

Shipped trend axis on the same battery: separation **0.0651** tuning / **0.1208** holdout, median run 31.0 bars, flip rate 0.0170.

**Correlations, reported and deciding nothing.** T1 sits at 0.27-0.35 with the shipped trend score and **−0.32 to −0.38 with the chop score** — it is the chop axis read with the opposite sign, which is exactly what "trend as broken chop" predicts. T2 sits at **0.73** with the shipped trend score: it largely restates the shipped axis by a different route.

### The 200-draw null — the same re-derive-everything null that killed the DC axis (`trend_t12_null_2026-11-10.csv`)

| kind | variant | real | null_mean | null_p95 | null_max | corrected | p_value |
|---|---|---|---|---|---|---|---|
| sign | T1_R5 | 0.1086 | 0.1147 | 0.1657 | 0.1810 | -0.0061 | 0.5550 |
| sign | T1_R10 | 0.1315 | 0.1182 | 0.1748 | 0.1999 | 0.0133 | 0.2850 |
| sign | T2 | 0.0370 | 0.0491 | 0.0881 | 0.1404 | -0.0120 | 0.7200 |
| perm | T1_R5 | 0.1086 | 0.1069 | 0.1471 | 0.2102 | 0.0018 | 0.4700 |
| perm | T1_R10 | 0.1315 | 0.1118 | 0.1617 | 0.1941 | 0.0196 | 0.2150 |
| perm | T2 | 0.0370 | 0.0413 | 0.0690 | 0.0962 | -0.0043 | 0.5550 |

### Selection and the null gate (`trend_t12_selection_2026-11-10.csv`)

| variant | median_run | flip_rate | run_ok | flip_ok | eligible | null_p_sign | null_p_perm | survives_null | t1_selected |
|---|---|---|---|---|---|---|---|---|---|
| T1_R5 | 70.0000 | 0.0104 | False | True | False | 0.5550 | 0.4700 | False | True |
| T1_R10 | 71.0000 | 0.0105 | False | True | False | 0.2850 | 0.2150 | False | False |
| T2 | 32.5000 | 0.0192 | True | False | False | 0.7200 | 0.5550 | False | False |

### Sub-period split, 2016-2019 vs 2020 (2021+ sealed)

| variant | period | separation | median_run | flip_rate | share_trending |
|---|---|---|---|---|---|
| T1_R5 | 2016-2019 | 0.0964 | 60.0000 | 0.0113 | 0.4962 |
| T1_R5 | 2020 | 0.1526 | 67.5000 | 0.0098 | 0.5461 |
| T1_R10 | 2016-2019 | 0.1321 | 72.0000 | 0.0102 | 0.5319 |
| T1_R10 | 2020 | 0.1256 | 56.2500 | 0.0117 | 0.5694 |
| T2 | 2016-2019 | 0.0340 | 38.5000 | 0.0175 | 0.3596 |
| T2 | 2020 | 0.0667 | 44.7500 | 0.0184 | 0.4014 |

## Layer 3 — the money test (`trend_t12_layer3_2026-11-10.csv`)

| family | role | book | median_year_pct | worst_year_pct | dip95_pct | profit_factor | retention | p_random_entry | p_regime_shuffle |
|---|---|---|---|---|---|---|---|---|---|
| mode C | baseline | mode C routed on shape2 TRENDING (BASELINE) | 1.331 | -3.997 | 6.911 | 1.087 | 0.258 | 0.080 | 0.000 |
| mode C | control | mode C trend UNGATED | -0.484 | -1.139 | 6.370 | 1.046 | -0.168 | 0.400 | 0.000 |
| A/B trend | baseline | A/B trend slices on shape2 TRENDING | -0.324 | -1.732 | 7.538 | 0.991 | -0.062 | 0.320 | 0.600 |
| A/B trend | control | A/B trend slices UNGATED | -0.526 | -2.028 | 6.671 | 0.990 | -0.211 | 1.000 | 1.000 |

**No candidate reached this stage.** Every construction failed its 200-draw separation null, so by the rule declared before the run none was given a money test.

## What this round establishes

1. The shipped trend axis's failure is **diagnosed, not guessed**: half its episodes are directionless, and it confirms ~24 bars into a ~23-bar move with 57% of the leg already gone.
2. The routed trend edge is **an onset edge** — 60% of the A/B book's R comes from the first third of an episode — which is precisely the part the label is too late to catch.
3. Mode C survives trend routing because of **how long it holds**, not because the regime read times its entries better.
4. Neither new construction clears the bar. The null gate is the binding constraint, exactly as it was for the DC axis in round 1.

_Files: `trend_anatomy_*_2026-11-10.*`, `trend_t12_*_2026-11-10.*`, `trend_states_*_2026-11-10.csv`._
