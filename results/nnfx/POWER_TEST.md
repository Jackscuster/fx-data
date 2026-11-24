# 0a — POWER TEST: WHAT EDGE SIZE IS THIS INSTRUMENT BLIND TO?

Generated 2026-11-24 12:00 by `code/nnfx0.py --stage power`. HANDOFF 0m.


## The question

Layer 2 found no survivor that held up. **That is only evidence about the market if the instrument could have seen an edge had one been there.** This plants an edge of known size and counts how often each decision route detects it, over 1000 repeats.


## Method

- **The noise is measured, not assumed.** It comes from the random-entry control re-runs already on record (`mode?_winners_nullstrat.csv`): **313,820 realisations**, each matched to a real strategy's trade count and holding period. From each draw's expectancy and t the per-trade R dispersion is recovered exactly as `sd = |mean|·√n / |t|` — median **1.2756 R**, with a median **140 trades per year**.

- **Significance is on yearly values, never per trade** (the standing rule). So a six-year span gives **6 observations and 5 degrees of freedom**, and eleven years gives 10. This is the fact that drives everything below.

- **Two generative models, both reported**, so the answer does not rest on a distributional convenience. `normal` takes the yearly sum as normal, which the central limit theorem makes reasonable at 140 trades a year. `twopoint` pays every trade either `+tp` or `−1`, which is what a stop-and-target system actually pays, calibrated in closed form to the same mean and dispersion. **They agree throughout, so the normal shortcut is safe here.**


## FINDING 1 — the old floor of t 5.08 was in the wrong units

A genuine best-of-M floor on **yearly** values, at family-wise α=0.05, is `t ≥ t.ppf(1 − (1 − 0.05^(1/M)), span−1)`:

| yearly_obs | df | candidates | m | alpha_eff | t_crit |
|---:|---:|---|---:|---:|---:|
| 6 | 5 | alone | 1 | 0.050 | 2.015 |
| 6 | 5 | one of 3 | 3 | 0.017 | 2.897 |
| 6 | 5 | one of 15 | 15 | 0.003 | 4.430 |
| 6 | 5 | one of 39 | 39 | 0.001 | 5.541 |
| 6 | 5 | best of 273,780 | 273780 | 1.874e-07 | 34.686 |
| 11 | 10 | alone | 1 | 0.050 | 1.812 |
| 11 | 10 | one of 3 | 3 | 0.017 | 2.456 |
| 11 | 10 | one of 15 | 15 | 0.003 | 3.395 |
| 11 | 10 | one of 39 | 39 | 0.001 | 3.973 |
| 11 | 10 | best of 273,780 | 273780 | 1.874e-07 | 11.686 |


**A real best-of-273,780 floor on six yearly observations is t ≥ 34.69, and on eleven it is t ≥ 11.69. The floor actually used was 5.08.** That number came from a per-trade t, where the degrees of freedom run to the hundreds. On yearly values it controls nothing of the kind it claimed to.


So the old route was **both** too lenient to control the family-wise error it was built to control **and** too strict to detect a real edge. Both at once, which is the worst of the two.


## FINDING 2 — what each route is blind to

`FP@0` is the measured false-positive rate with no edge planted, which should sit near the route's nominal α and does. `blind below` is the smallest planted edge the route detects at 80% power.


**Model: twopoint**

| span | years | route | t_crit | false_positive_at_zero | min_edge_power50 | power_at_0_10 | power_at_0_20 | blind_below |
|---|---:|---|---:|---:|---:|---:|---:|---|
| six_unseen_2010_2015 | 6 | old_bestof273780 | 5.080 | 0.000 |  | 0.039 | 0.089 | >0.20 R |
| six_unseen_2010_2015 | 6 | alone | 2.015 | 0.032 | 0.100 | 0.545 | 0.835 | 0.20 R |
| six_unseen_2010_2015 | 6 | one_of_39 | 5.541 | 0.000 |  | 0.024 | 0.062 | >0.20 R |
| six_unseen_2010_2015 | 6 | one_of_3 | 2.897 | 0.012 | 0.200 | 0.274 | 0.541 | >0.20 R |
| eleven_2010_2020 | 11 | old_bestof273780 | 5.080 | 0.000 |  | 0.030 | 0.152 | >0.20 R |
| eleven_2010_2020 | 11 | alone | 1.812 | 0.062 | 0.100 | 0.817 | 0.991 | 0.10 R |
| eleven_2010_2020 | 11 | one_of_39 | 3.973 | 0.001 |  | 0.146 | 0.466 | >0.20 R |
| eleven_2010_2020 | 11 | one_of_3 | 2.456 | 0.019 | 0.100 | 0.598 | 0.921 | 0.15 R |


**Model: normal**

| span | years | route | t_crit | false_positive_at_zero | min_edge_power50 | power_at_0_10 | power_at_0_20 | blind_below |
|---|---:|---|---:|---:|---:|---:|---:|---|
| six_unseen_2010_2015 | 6 | old_bestof273780 | 5.080 | 0.000 |  | 0.036 | 0.084 | >0.20 R |
| six_unseen_2010_2015 | 6 | alone | 2.015 | 0.055 | 0.100 | 0.545 | 0.860 | 0.20 R |
| six_unseen_2010_2015 | 6 | one_of_39 | 5.541 | 0.000 |  | 0.025 | 0.060 | >0.20 R |
| six_unseen_2010_2015 | 6 | one_of_3 | 2.897 | 0.015 | 0.200 | 0.263 | 0.549 | >0.20 R |
| eleven_2010_2020 | 11 | old_bestof273780 | 5.080 | 0.000 |  | 0.042 | 0.155 | >0.20 R |
| eleven_2010_2020 | 11 | alone | 1.812 | 0.041 | 0.100 | 0.817 | 0.985 | 0.10 R |
| eleven_2010_2020 | 11 | one_of_39 | 3.973 | 0.002 |  | 0.168 | 0.434 | >0.20 R |
| eleven_2010_2020 | 11 | one_of_3 | 2.456 | 0.013 | 0.100 | 0.624 | 0.912 | 0.15 R |


### In words

- **The old route is blind to everything.** On the six unseen years it detects an edge of **0.20 R per trade — a very large edge — only 8.9% of the time**. On eleven years, 15.2%. Layer 2's silence is therefore not evidence that no edge existed.

- **One strategy declared in advance is a usable instrument.** On six years it detects 0.10 R 54.5% of the time and 0.20 R 83.5%; on eleven years, 81.7% and 99.1%. Eleven years detects a 0.10 R edge at 80% power; six years does not.

- **ONE OF 39 IS WORSE THAN THE OLD ROUTE ON SIX YEARS.** Its honest floor on 5 degrees of freedom is **t ≥ 5.54**, higher than the 5.08 the old route used, so it detects 0.20 R only 6.2% of the time against the old route's 8.9%. On eleven years it improves to 46.6%.

- **One of 3 is where the funnel starts to pay.** 0.20 R at 54.1% on six years and 92.1% on eleven; on eleven it detects 0.15 R at 80% power.


## WHAT THIS MEANS FOR THE PLAN IN HANDOFF 0m

**The funnel is the right instinct and the arithmetic backs it — but two things in the plan need stating plainly.**


1. **Stage 1a/1b cannot be a significance gate. It is a screen.** With 39 candidates judged on six yearly observations the honest floor is t ≥ 5.54, which almost nothing real will cross. So 1a and 1b should be read as *ranking and stability* exercises — which indicator behaves consistently across its three settings, across pairs, across years — and the significance claim belongs at the ≤3 level Jack picks down to. The report will present the best-of-39 floor as required, and label it as what it is: a bar that a genuine 0.20 R edge clears 6.2% of the time.


2. **Six yearly observations is a thin instrument whatever the candidate count.** Even one pre-declared strategy tested alone is blind below 0.20 R on six years. The CONFIRM years are not a formality; they are most of the statistical power. The plan is right to compute and store them — but any decision taken on the BUILD years alone is being taken at roughly half the power it will eventually have.


3. **A route that cannot detect 0.20 R per trade should not be used to reject a candidate.** At 140 trades a year, 0.20 R per trade is about 28 R a year, which at a 3.6%% dip budget is a very large return. If the instrument cannot see that, "it did not pass" means nothing.


## What would fix the power, in order of size

| change | effect |
|---|---|
| **use all eleven unseen years** instead of six | the single largest gain: it roughly doubles the degrees of freedom and drops the one-of-3 floor from 2.90 to 2.46 |
| **fewer candidates** | one of 3 instead of one of 39 drops the floor from 5.54 to 2.90 on six years |
| **more trades per year** | tightens each yearly value; the yearly sd falls as √n |
| pooling pairs into one yearly number per year (already done) | keeps the unit of evidence the year, which is what makes the floors this high in the first place |

**Not on that list: testing more strategies.** Every candidate added raises the floor for all of them.


## Provenance

- `results/nnfx/power_test.csv` — md5 `0d2f9296afcf`
- `results/nnfx/power_test_blindness.csv` — md5 `968fde772648`
- `results/nnfx/power_test_true_floors.csv` — md5 `84efab82dc4b`
- `results/nnfx/noise_calibration.npz` — md5 `1cea727e2eec`
- noise from `results/r2gate2/modeA_winners_nullstrat.csv` and `modeB_winners_nullstrat.csv`, 313,820 realisations
