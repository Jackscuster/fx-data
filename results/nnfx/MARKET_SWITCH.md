# 2a — MARKET-WIDE SWITCH: MEASUREMENT ONLY

Generated 2026-11-24 12:41 by `code/nnfx2.py`. HANDOFF 0m.


**NO TRADING RULE IS BUILT HERE.** No switch, no gate, nothing wired into a strategy. That was the instruction.


## What is being correlated with what

**The book**: the whole-field **trend always-on** book, equal weight, monthly P&L in R, 2011-2020. For a calendar year some step trades (2016-2020) it uses that step's tuned configuration; for 2011-2015, which no step trades, it uses step 1's — whose tuning years those are. **That is why 2011-2015 are the TUNING era below and 2016-2020 the UNSEEN era.**


**The panel**, from Layer 1 outputs only, **lagged one bar**:


| measure | what it is |
|---|---|
| `share_trending` | share of the 28 pairs whose `shape2` is `trending` |
| `mean_activity` | `activity` mapped weak/medium/strong to 1/2/3, averaged |
| `mean_scale` | `scale_28` averaged, the raw measure the tier is cut from |
| `quality_high` | share of **trending** pair-days tagged `high` by the currency-leg gap flag. Computed on trending bars only, because the interface says it means nothing elsewhere |
| `crisis_flag` | 1 on any day inside a crisis window, from `crisis_events.csv`, whose dates come from news and never from price |

## The book is sampled, and the sampling error is measured

No whole-field daily series exists on disk — the 466 saved ones are all passers' books — and a full pass is **11.7 hours** at the measured 0.154 s per strategy. So the book is a **1,988-strategy sample of 273,780 (0.73%), stratified by C1**, costing 2.1 minutes.


**That is not an assumption; it was checked.** Two *independent* 1,000-strategy half-samples give monthly P&L series correlating at **r = 0.9972**, so about **0.3% of monthly variance is sample noise** and the implied reliability of the 2,000-strategy book is **0.9986**. For this measurement the sample is the field, and the 11.7-hour pass would buy nothing.


## The result

`p_circular` is the honest one. A plain shuffle destroys a monthly series' autocorrelation as well as its alignment, which narrows the null and makes p too small; a **circular shift** keeps each series' own autocorrelation and breaks only the alignment, which is the thing being tested. Both are reported, 1,000 draws each.


**TUNING era, 2011-2015**

| measure | months | pearson_r | spearman | p_circular | p_shuffle | null_sd_circular |
|---|---:|---:|---:|---:|---:|---:|
| crisis_flag | 60 | 0.2478 | 0.2644 | 0.0360 | 0.0420 | 0.1238 |
| quality_high | 60 | -0.1300 | -0.1305 | 0.2860 | 0.3230 | 0.1113 |
| mean_activity | 60 | -0.1235 | -0.1148 | 0.3720 | 0.3320 | 0.1295 |
| share_trending | 60 | -0.1204 | -0.1669 | 0.2410 | 0.3900 | 0.1040 |
| mean_scale | 60 | -0.0795 | -0.0337 | 0.5010 | 0.5510 | 0.1242 |


**UNSEEN era, 2016-2020**

| measure | months | pearson_r | spearman | p_circular | p_shuffle | null_sd_circular |
|---|---:|---:|---:|---:|---:|---:|
| crisis_flag | 60 | 0.2785 | 0.2860 | 0.0400 | 0.0200 | 0.1509 |
| share_trending | 60 | -0.1576 | -0.1480 | 0.2090 | 0.2140 | 0.1447 |
| mean_scale | 60 | 0.0443 | -0.0085 | 0.7390 | 0.7420 | 0.1566 |
| quality_high | 60 | -0.0263 | -0.0467 | 0.7450 | 0.8470 | 0.0964 |
| mean_activity | 60 | -0.0043 | -0.0094 | 1.0000 | 0.9730 | 0.1594 |


**All 120 months**

| measure | months | pearson_r | spearman | p_circular | p_shuffle | null_sd_circular |
|---|---:|---:|---:|---:|---:|---:|
| crisis_flag | 120 | 0.2682 | 0.2932 | 0.0000 | 0.0080 | 0.0901 |
| share_trending | 120 | -0.0889 | -0.1273 | 0.3810 | 0.3500 | 0.1043 |
| mean_activity | 120 | -0.0724 | -0.0616 | 0.4420 | 0.4210 | 0.0987 |
| quality_high | 120 | -0.0280 | -0.0461 | 0.8340 | 0.7400 | 0.1144 |
| mean_scale | 120 | -0.0279 | -0.0203 | 0.7880 | 0.7560 | 0.0958 |


## What it says

**ONE measure relates to the book, and it is not the obvious one.**


1. **The crisis flag is the only one that survives, and it survives on both eras with the same sign.** r = **+0.248** on the tuning years (p_circular 0.036) and **+0.279** on the unseen years (p_circular 0.040); over all 120 months r = **+0.268**, p_circular 0.000. The sign is **positive**: crisis months are GOOD months for a trend book, which is what you would expect of a market that is moving in one direction for a reason.


2. **`share_trending` does not work, and it has the WRONG SIGN.** r = −0.120 on tuning and −0.158 on unseen, neither close to significant. The share of pairs Layer 1 labels `trending` does not predict what a trend book earns that month, and if anything leans the other way. That is the measure one would reach for first, and it is the one that fails.


3. **Activity, scale and the quality flag are all flat.** |r| ≤ 0.13 everywhere, and on the unseen years `mean_activity` is −0.004 — indistinguishable from nothing.


## What this does NOT license

- **It is not a switch.** An r of 0.27 is about 7% of monthly variance explained. A rule that stood down the book outside crisis windows would be acting on the other 93%.

- **The crisis flag is not present-tense in the way a switch needs.** `crisis_events.csv` dates come from news, which is what makes the crisis work in this project non-circular, but the window runs from the event date to +15 days. Knowing a crisis has STARTED is a different thing from knowing one is coming, and the correlation here is with the window, not with its leading edge.

- **Five measures were tested on each era.** The crisis flag at p_circular 0.036 and 0.040 would not survive a Bonferroni correction for five tests (0.05/5 = 0.01) on either era alone. What makes it worth recording is not either p-value but that **the same sign and a similar magnitude appear in both eras independently**, and that the pooled 120-month p_circular is 0.000.


## Provenance

- `results/nnfx/market_switch_book_daily.csv` — 2,593 rows, md5 `b2bcae9fac67`
- `results/nnfx/market_switch_monthly.csv` — 120 rows, md5 `9efd30ef20da`
- `results/nnfx/market_switch_corr.csv` — 15 rows, md5 `338b71ea97be`
- `results/nnfx/market_switch_halfsamples.csv` — 120 rows, md5 `8a0a15408659`
- panel built from `results/layer1_states.csv`, `results/layer1_trend_quality_series.csv` and `results/crisis_events.csv`, Layer 1 outputs only, lagged one bar
