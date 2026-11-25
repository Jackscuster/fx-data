# QUIET ENTRY — item 2, Jack 25 November 2026

**The hypothesis, and why it is being tested rather than reported.** Item 3 of 24 November found that for candidate A the bottom three ATR deciles at entry carry almost all of the profit from about a quarter of the trades. **That was found by looking.** A rule built from it and measured on the same sample would be fitted to it by construction, so this is run as a declared test with the pass conditions stated first.

**What would make the rule real, written down before the numbers:**

1. the walk-forward version has to **beat its own control on the paired test** — same days, same everything else;
2. the fixed-Q curve has to be a **broad plateau**, not a spike at one Q, because Q was swept and the best of ten tries is a maximum;
3. the effect has to appear in candidates that are **not ichimoku**.

Any one of those failing is a reason to drop it.

---

## THE ANSWER: the rule FAILS, and the thing underneath it is real

**Condition 1 fails, 0 of 2.** The walk-forward quiet rule does not beat its own control on the same days: **A -4.816 R** (t -0.335, 1 of 6 years positive); **B -25.689 R** (t -0.680, 1 of 6 years positive).

**Condition 2 fails.** Return per dip turns direction 4 times for A; 5 times for B along Q. A curve that turns that often is noise with a maximum in it.

**Condition 3 is met, and in the opposite direction to the hypothesis.** The tilt is general — 35 of 39 C1 alone show it — but it is **losses concentrated in loud entries**, not profit concentrated in quiet ones, and the decile-matched null confirms it is in the entries rather than in the axis.

**So: do not adopt a Q cut.** The best fixed Q is a maximum over ten tries on one six-year sample, and the honest walk-forward version of the same idea loses money. This document is the clearest hindsight-versus-walk-forward demonstration in the project: with hindsight, A at Q = 0.40 makes **+44.010 R against +39.874 R unfiltered**, and A at Q = 0.20 more than doubles return per dip. Pick Q the only way you actually could — on the tuning years — and A loses 4.816 R and B goes from +23.934 R to -1.755 R.

**ONE THING WORTH FLAGGING AND NOT BUILDING WITHOUT BEING ASKED.** The asymmetry that survives every test here is about SIZE, not about admission: a high-ATR entry is a worse bet than a same-decile random entry, and an entry in the top deciles is bigger in notional for the same R because the stop is wider. A rule that scales risk down with the ATR decile instead of refusing the trade would act on exactly the measured effect without throwing away three quarters of the sample, which is what the Q cut does and what kills it. That is a different experiment and it is not in item 2, so it is not run here.

---

`Q` is the cut: a pair may enter only while its own one-bar-lagged ATR/price is at or below its own expanding `Q`-th percentile. **Q = 1.00 is the rule OFF** and takes the identical code path, which is what lets the curve end at the unfiltered candidate with nothing special-cased. A bar inside the first 250 bars of history, where the percentile is not yet defined, is **blocked** — allowing it would make the rule look free on exactly the sample it cannot police.

| Q | share of all 28 pairs' bars blocked |
|---:|---:|
| 0.10 | 84.7% |
| 0.20 | 75.2% |
| 0.30 | 66.5% |
| 0.40 | 57.9% |
| 0.50 | 49.1% |
| 0.60 | 40.6% |
| 0.70 | 32.1% |
| 0.80 | 23.9% |
| 0.90 | 15.9% |
| 1.00 | 0.0% |

## 2a — is the low-decile tilt ICHIMOKU, or is it the MARKET?

All 39 C1 alone (no baseline, no floor, no peg guard — this question is about the decile axis itself, and a floor that deletes the bottom 5% of it would remove part of the region under test), plus candidates A and B as reported. `rho` is the rank correlation of R per trade against the decile: **negative is the claim.**

**35 of 41 have a negative rho** — median -0.297. And **39 of the 39 C1 alone are negative overall**, which changes what the finding actually is.

### THE ANSWER, and it is not the one the hypothesis expected

**It is the market, not ichimoku — but the direction is the other way round.** The tilt is not "profit concentrated in quiet entries". It is **losses concentrated in loud ones.** Every one of the 39 C1 alone loses money, and the top three deciles are where they lose it: 
across the 39, the top three deciles total **-2756 R** against **-994 R** in the bottom three. So a rule that refuses loud entries is not harvesting an edge, it is **declining to take the worst trades** — which is a smaller claim and a much more believable one.

**And candidate A, the one the hypothesis came from, does NOT show the per-trade gradient at all**: its rho is **+0.055**, flat, against **-0.442** for B. What A has is a TOTAL-R concentration — 92.0% of its R from 27.0% of its entries — which is a story about a few large winners being quiet trades, not about quiet trades paying better on average. Those are different claims and only the second one supports a rule.

| candidate | entries | R total | R bottom 3 deciles | R top 3 | share bottom 3 | share of entries bottom 3 | rho |
|---|---:|---:|---:|---:|---:|---:|---:|
| j_tpo_signals | 1445 | -45.067 | +39.041 | -56.132 | -0.866 | 0.372 | -0.770 |
| laguerre_filter_signals | 1564 | -41.754 | +36.695 | -43.655 | -0.879 | 0.370 | -0.697 |
| parabolic_sar_signals | 6532 | -275.587 | -46.790 | -175.033 | 0.170 | 0.385 | -0.685 |
| polychromatic_momentum_signals | 2253 | -171.883 | -14.696 | -95.063 | 0.086 | 0.362 | -0.685 |
| price_momentum_oscillator_signals | 1889 | -62.854 | +4.501 | -37.076 | -0.072 | 0.375 | -0.588 |
| bears_bulls_impulse_signals | 8280 | -186.566 | -52.136 | -151.142 | 0.279 | 0.349 | -0.564 |
| kuskus_starlight_signals | 4379 | -148.872 | -32.002 | -117.405 | 0.215 | 0.356 | -0.552 |
| relative_vigor_index_signals | 19207 | -579.700 | -167.278 | -266.229 | 0.289 | 0.369 | -0.539 |
| chandelier_exit_signals | 4964 | -160.805 | -5.505 | -110.841 | 0.034 | 0.307 | -0.527 |
| ehlers_reverse_ema_signals | 4331 | -152.251 | -53.924 | -86.191 | 0.354 | 0.363 | -0.527 |
| glitch_index_signals | 3660 | -77.758 | +2.365 | -62.555 | -0.030 | 0.385 | -0.491 |
| dpo_signals | 3692 | -111.988 | +13.547 | -60.250 | -0.121 | 0.404 | -0.491 |
| center_of_gravity_signals | 13193 | -375.797 | -66.074 | -127.976 | 0.176 | 0.367 | -0.455 |
| **B** | 1970 | +29.587 | +16.615 | -13.751 | 0.562 | 0.255 | **-0.442** |
| ssl_channel_signals | 6277 | -218.933 | -19.949 | -128.382 | 0.091 | 0.383 | -0.442 |
| didi_index_signals | 7617 | -221.863 | +14.821 | -98.227 | -0.067 | 0.369 | -0.406 |
| supertrend_signals | 2761 | -56.752 | -9.962 | -48.822 | 0.176 | 0.363 | -0.406 |
| donchian_breakout_signals | 1347 | -23.507 | +0.971 | -8.250 | -0.041 | 0.409 | -0.406 |
| ichimoku_signals | 2890 | -29.431 | +12.212 | -25.793 | -0.415 | 0.365 | -0.394 |
| coral_signals | 10307 | -371.591 | -99.602 | -144.301 | 0.268 | 0.368 | -0.382 |
| coppock_curve_signals | 4142 | -117.717 | +30.121 | -63.461 | -0.256 | 0.363 | -0.297 |
| kase_peak_oscillator_signals | 4382 | -114.929 | -24.808 | -68.335 | 0.216 | 0.350 | -0.261 |
| dspo_signals | 1778 | -58.492 | -5.113 | -30.263 | 0.087 | 0.363 | -0.261 |
| mama_fama_signals | 2288 | -53.059 | -20.819 | -19.590 | 0.392 | 0.362 | -0.248 |
| trend_direction_force_index_signals | 3887 | -113.114 | +0.960 | -61.462 | -0.008 | 0.378 | -0.224 |
| aroon_signals | 2284 | -25.082 | -8.053 | -29.862 | 0.321 | 0.400 | -0.188 |
| qqe_mod_signals | 5031 | -136.892 | -25.572 | -101.684 | 0.187 | 0.365 | -0.188 |
| kalman_filter_signals | 2496 | -110.123 | -18.266 | -56.407 | 0.166 | 0.360 | -0.176 |
| fisher_transform_signals | 25683 | -257.380 | -51.278 | -66.320 | 0.199 | 0.370 | -0.164 |
| hieken_ashi_smoothed_signals | 4289 | -24.101 | -12.193 | -6.105 | 0.506 | 0.351 | -0.127 |
| schaff_trend_cycle_signals | 3893 | -208.826 | -49.951 | -66.432 | 0.239 | 0.372 | -0.127 |
| linreg_slope_signals | 3682 | -64.334 | -11.589 | -29.772 | 0.180 | 0.363 | -0.055 |
| volatility_quality_signals | 1746 | -108.656 | -38.352 | -41.849 | 0.353 | 0.359 | -0.042 |
| rex_oscillator_signals | 25347 | -501.819 | -176.636 | -126.373 | 0.352 | 0.370 | -0.042 |
| fx_sniper_ergodic_cci_signals | 12555 | -198.237 | -31.248 | -72.049 | 0.158 | 0.375 | -0.006 |
| vortex_signals | 7515 | -138.185 | -32.944 | -52.896 | 0.238 | 0.378 | +0.006 |
| **A** | 745 | +41.489 | +38.190 | +12.522 | 0.920 | 0.270 | **+0.055** |
| adx_dmi_signals | 85 | -0.246 | -0.405 | -5.003 | 1.643 | 0.200 | +0.067 |
| lemantrend_signals | 2230 | -92.829 | -40.596 | -24.451 | 0.437 | 0.374 | +0.079 |
| halftrend_signals | 278 | -10.353 | +3.396 | +3.390 | -0.328 | 0.371 | +0.176 |
| waddah_attar_explosion_signals | 2482 | -49.387 | -37.162 | +6.660 | 0.752 | 0.369 | +0.358 |

**One warning about the `share bottom 3` column.** Where a candidate's total R is negative the share is meaningless and can come out negative or above 1 — it is a share of a negative denominator. Read `R bottom 3` and `R top 3` directly for those rows; the share only means something on A and B.

## 2b — the null: random entries matched on count, holding period AND decile

**Why this null and not the usual one.** The standing random-entry null matches trade count, holding period and the long/short split but draws the entry bar from anywhere in the pair's span. That is the right null for "does the timing carry anything". It is the **wrong** null for a decile table: if quiet bars happen to be followed by larger moves for any reason at all — a volatility cycle, mean reversion after a squeeze, anything — then every strategy's low deciles would look good and 2a would be measuring the axis rather than the strategy. So here the draw is restricted to bars in the **same decile** as the real entry it replaces, and the test is per decile, **gross of cost**: each decile's null mean must sit inside 3 standard errors of zero.

| decile | real entries | cells failing the null | null mean R (gross) | real mean R (gross) | mean z of real vs null |
|---:|---:|---:|---:|---:|---:|
| 1 | 38109 | **3 of 39** | +0.00676 | +0.00898 | +0.261 |
| 2 | 23232 | **2 of 39** | +0.00430 | +0.01707 | +0.127 |
| 3 | 20656 | **4 of 39** | +0.00210 | +0.05091 | +0.473 |
| 4 | 20865 | **6 of 39** | -0.00107 | +0.01276 | +0.127 |
| 5 | 21149 | **4 of 39** | +0.00171 | +0.01713 | +0.067 |
| 6 | 20478 | **1 of 39** | -0.00025 | +0.01521 | +0.053 |
| 7 | 20678 | **5 of 39** | +0.00517 | -0.02010 | -0.379 |
| 8 | 19689 | **3 of 39** | +0.00640 | -0.03507 | -0.768 |
| 9 | 19291 | **8 of 39** | +0.00804 | -0.05199 | -1.102 |
| 10 | 18514 | **4 of 39** | +0.00432 | -0.02625 | -0.348 |

**40 of 390 (candidate, decile) cells fail** — the null's own mean is further than 3 standard errors from zero. At 3 SE under a true null about 1 in 300 should fail, so **10.3% is not noise: the decile-matched null does not make exactly zero.** Its mean is **+0.00375 R per trade gross**, positive in 8 of the 10 deciles.

**But the question 2a needs answered is whether the drift SLOPES, and it does not.** A flat drift shifts every decile by the same amount and cannot manufacture a tilt; only a sloping one can. The null's mean across deciles 1 to 10 has a slope of **+0.000257 R per decile** — flat — while the REAL entries' z against their own same-decile null slopes **-0.132 per decile**, from +0.261 in decile 1 to -0.348 in decile 10.

**So the tilt is in the strategies' entries, not in the bucketing.** Real entries in the top deciles underperform RANDOM entries drawn from the same deciles, with the same holding periods and the same direction mix, by up to about one standard deviation of the null. That is the strongest single statement item 2 produces, and it is a statement about loud entries being bad, not about quiet ones being good.

**Where the drift itself comes from, stated rather than left open:** the null inherits the real candidate's long/short mix per pair, so any net currency drift over the sample is inherited with it. +0.004 R per trade is about 0.4% of one R, and it is the same in every decile. It is not corrected for, because correcting it would mean altering the direction mix and that would stop the null being matched.

## 2c — the rule

### The fixed-Q curve, 10% to 100% — SHAPE ONLY, not a result

Q is swept here, so the best Q in this table is a maximum over ten tries on the same six years. Every row carries `hindsight = 1` for that reason. What the curve is FOR is its shape — a real effect is a broad plateau — and its end point, because Q = 1.00 is the unfiltered candidate.

| candidate | Q | R total | R/yr | R/yr ex best day | trades | worst dip | **R per dip** | best trade share | t yearly | t yearly ex best day | crisis share |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 0.10 | +3.702 | +0.617 | 0.439 | 35 | 2.957 | **1.252** | 0.449 | 0.674 | 0.578 | 0.320 |
| A | 0.20 | +25.906 | +4.318 | 3.887 | 118 | 7.136 | **3.630** | 0.125 | 1.330 | 1.304 | 0.071 |
| A | 0.30 | +36.314 | +6.052 | 5.408 | 201 | 17.830 | **2.037** | 0.129 | 1.021 | 0.987 | 0.083 |
| A | 0.40 | +44.010 | +7.335 | 6.644 | 312 | 17.394 | **2.530** | 0.105 | 1.225 | 1.179 | 0.142 |
| A | 0.50 | +33.777 | +5.629 | 5.057 | 425 | 14.381 | **2.349** | 0.137 | 1.003 | 0.939 | 0.277 |
| A | 0.60 | +27.153 | +4.525 | 3.845 | 526 | 19.403 | **1.399** | 0.170 | 0.747 | 0.661 | 0.396 |
| A | 0.70 | +26.785 | +4.464 | 3.666 | 616 | 22.479 | **1.192** | 0.164 | 0.684 | 0.585 | 0.544 |
| A | 0.80 | +27.688 | +4.615 | 3.711 | 689 | 22.727 | **1.218** | 0.159 | 0.694 | 0.581 | 0.536 |
| A | 0.90 | +38.227 | +6.371 | 5.468 | 735 | 22.419 | **1.705** | 0.117 | 1.020 | 0.913 | 0.416 |
| **A** | **1.00** | +39.874 | +6.646 | 5.742 | 742 | 22.616 | **1.763** | 0.112 | 1.076 | 0.969 | 0.395 |
| B | 0.10 | +0.654 | +0.109 | -0.182 | 117 | 15.662 | **0.042** | 4.452 | 0.038 | -0.058 | 2.609 |
| B | 0.20 | +19.683 | +3.281 | 2.683 | 304 | 18.565 | **1.060** | 0.195 | 0.767 | 0.719 | 0.289 |
| B | 0.30 | +21.821 | +3.637 | 2.849 | 518 | 22.210 | **0.982** | 0.185 | 0.648 | 0.527 | 0.806 |
| B | 0.40 | +19.625 | +3.271 | 2.201 | 764 | 21.042 | **0.933** | 0.201 | 0.644 | 0.413 | 1.600 |
| B | 0.50 | +31.377 | +5.229 | 3.537 | 1060 | 27.559 | **1.139** | 0.129 | 0.862 | 0.711 | 1.222 |
| B | 0.60 | +17.953 | +2.992 | 0.964 | 1320 | 41.537 | **0.432** | 0.203 | 0.452 | 0.175 | 2.179 |
| B | 0.70 | +40.517 | +6.753 | 4.159 | 1587 | 27.131 | **1.493** | 0.090 | 1.060 | 0.903 | 1.051 |
| B | 0.80 | +29.723 | +4.954 | 2.586 | 1786 | 38.793 | **0.766** | 0.117 | 0.722 | 0.419 | 1.506 |
| B | 0.90 | +25.510 | +4.252 | 1.858 | 1920 | 43.966 | **0.580** | 0.129 | 0.522 | 0.250 | 1.853 |
| **B** | **1.00** | +23.934 | +3.989 | 1.752 | 1957 | 44.541 | **0.537** | 0.136 | 0.468 | 0.225 | 2.052 |

**A.** Rule off: R +39.874 over 742 trades, dip 22.616, **R per dip 1.763**. Best Q on return per dip is **0.20**: R +25.906 (65% of the unfiltered total) over 118 trades (16% of them), dip 7.136, **R per dip 3.630**.

    *Shape:* return per dip turns direction **4 times in 8 steps** along Q, between 1.192 and 3.630. **That is not a plateau.** A curve that turns that often is noise with a maximum in it, and the maximum is a best of ten tries on one six-year sample.

**B.** Rule off: R +23.934 over 1957 trades, dip 44.541, **R per dip 0.537**. Best Q on return per dip is **0.70**: R +40.517 (169% of the unfiltered total) over 1587 trades (81% of them), dip 27.131, **R per dip 1.493**.

    *Shape:* return per dip turns direction **5 times in 8 steps** along Q, between 0.042 and 1.493. **That is not a plateau.** A curve that turns that often is noise with a maximum in it, and the maximum is a best of ten tries on one six-year sample.

### Walk-forward Q — the only form that may be read as a result

Q picked on each step's own four TUNING years by tuning-year net R at achievable size, minimum 30 entries in the tuning window, then traded on that step's unseen year. A step with no eligible Q runs with the rule OFF and is recorded as Q = 1.00 rather than left as a gap.

| candidate | step | unseen trade year | Q picked | tuning R at the pick |
|---|---|---:|---:|---:|
| A | 2005-2008 | 2010 | **1.00** | 28.109 |
| A | 2006-2009 | 2011 | **0.60** | 17.174 |
| A | 2007-2010 | 2012 | **0.70** | 28.251 |
| A | 2008-2011 | 2013 | **0.40** | -0.016 |
| A | 2009-2012 | 2014 | **0.70** | 35.291 |
| A | 2010-2013 | 2015 | **0.40** | 49.449 |
| B | 2005-2008 | 2010 | **1.00** | 23.444 |
| B | 2006-2009 | 2011 | **0.50** | 7.111 |
| B | 2007-2010 | 2012 | **0.50** | -1.766 |
| B | 2008-2011 | 2013 | **0.70** | 2.391 |
| B | 2009-2012 | 2014 | **0.20** | -1.861 |
| B | 2010-2013 | 2015 | **0.20** | 16.308 |

### The paired test — the walk-forward rule against its own control, same days

Days are UNIONED, not intersected. A day on which only one side is in the market is a real difference and is the rule's main effect — it STOPS trades happening. Missing days are zero P&L, not missing data.

| candidate | days | R with | R without | **dR** | dip with | dip without | **R/dip with** | R/dip without | trades removed | t block boot of the difference | years positive | beats its control? |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| A | 1457 | +35.058 | +39.874 | **-4.816** | 21.900 | 22.616 | **1.601** | 1.763 | 219 | -0.335 | 1 of 6 | no |
| B | 1523 | -1.755 | +23.934 | **-25.689** | 31.807 | 44.541 | **-0.055** | 0.537 | 867 | -0.680 | 1 of 6 | no |

**The Q picked per step is in the file** (`quiet_paired.csv`, column `Q_by_step`) so the walk is auditable step by step rather than summarised into one number.

## 2d — crossed with the per-pair floor: do the two rules conflict?

They are the two ends of one axis. The floor blocks the bottom `floor_q`; the quiet rule blocks everything above `Q`; together they keep the band. **If the profit really is in the quiet entries then the floor is cutting into the best part of the book and the two fight.** The cross answers it directly because the floor-OFF column is in it. The measure is **return per dip**, which is what Jack asked for and which does not simply reward whichever combination holds the most risk.

| candidate | floor | Q | R total | R/yr | R/yr ex best day | trades | worst dip | **R per dip** | t yearly | years positive |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A | off | 0.20 | +37.970 | +6.328 | 5.608 | 239 | 13.147 | **2.888** | 2.100 | 4 |
| A | off | 0.30 | +47.641 | +7.940 | 7.220 | 322 | 14.944 | **3.188** | 1.762 | 5 |
| A | off | 0.50 | +45.916 | +7.653 | 6.932 | 546 | 14.186 | **3.237** | 1.523 | 3 |
| A | off | 1.00 | +52.426 | +8.738 | 7.834 | 863 | 22.834 | **2.296** | 1.666 | 4 |
| A | 1.0% | 0.20 | +25.446 | +4.241 | 3.739 | 189 | 11.943 | **2.131** | 1.304 | 3 |
| A | 1.0% | 0.30 | +35.853 | +5.976 | 5.261 | 272 | 17.382 | **2.063** | 1.021 | 4 |
| A | 1.0% | 0.50 | +33.317 | +5.553 | 4.930 | 496 | 14.186 | **2.349** | 0.981 | 2 |
| A | 1.0% | 1.00 | +39.305 | +6.551 | 5.647 | 813 | 22.834 | **1.721** | 1.047 | 3 |
| A | 5.0% | 0.20 | +25.906 | +4.318 | 3.887 | 118 | 7.136 | **3.630** | 1.330 | 3 |
| A | 5.0% | 0.30 | +36.314 | +6.052 | 5.408 | 201 | 17.830 | **2.037** | 1.021 | 4 |
| A | 5.0% | 0.50 | +33.777 | +5.629 | 5.057 | 425 | 14.381 | **2.349** | 1.003 | 2 |
| A | 5.0% | 1.00 | +39.874 | +6.646 | 5.742 | 742 | 22.616 | **1.763** | 1.076 | 3 |
| B | off | 0.20 | +29.706 | +4.951 | 4.154 | 615 | 28.100 | **1.057** | 1.841 | 5 |
| B | off | 0.30 | +25.742 | +4.290 | 3.502 | 828 | 33.720 | **0.763** | 1.157 | 4 |
| B | off | 0.50 | +36.241 | +6.040 | 4.348 | 1370 | 27.827 | **1.302** | 1.090 | 4 |
| B | off | 1.00 | +29.942 | +4.990 | 2.558 | 2267 | 40.800 | **0.734** | 0.614 | 5 |
| B | 1.0% | 0.20 | +24.928 | +4.155 | 3.456 | 469 | 23.932 | **1.042** | 1.369 | 3 |
| B | 1.0% | 0.30 | +22.902 | +3.817 | 2.914 | 682 | 31.854 | **0.719** | 0.892 | 4 |
| B | 1.0% | 0.50 | +27.004 | +4.501 | 2.809 | 1224 | 29.375 | **0.919** | 0.793 | 3 |
| B | 1.0% | 1.00 | +11.097 | +1.850 | -0.267 | 2121 | 46.260 | **0.240** | 0.231 | 4 |
| B | 5.0% | 0.20 | +19.683 | +3.281 | 2.683 | 304 | 18.565 | **1.060** | 0.767 | 4 |
| B | 5.0% | 0.30 | +21.821 | +3.637 | 2.849 | 518 | 22.210 | **0.982** | 0.648 | 4 |
| B | 5.0% | 0.50 | +31.377 | +5.229 | 3.537 | 1060 | 27.559 | **1.139** | 0.862 | 3 |
| B | 5.0% | 1.00 | +23.934 | +3.989 | 1.752 | 1957 | 44.541 | **0.537** | 0.468 | 4 |

### DO THEY CONFLICT? Yes — and the floor is the one that loses

**A.** With the quiet rule off, turning the per-pair floor OFF gives R **+52.426** and return per dip **2.296**, against R +39.874 and 1.763 at the decided 5% floor — the floor costs **12.553 R** and **30.2%** of return per dip. And it is not one column: floor-off beats floor-5% on return per dip at **3 of the 4 Q values tested**.

**B.** With the quiet rule off, turning the per-pair floor OFF gives R **+29.942** and return per dip **0.734**, against R +23.934 and 0.537 at the decided 5% floor — the floor costs **6.008 R** and **36.6%** of return per dip. And it is not one column: floor-off beats floor-5% on return per dip at **2 of the 4 Q values tested**.

**So the two rules fight, exactly as the hypothesis predicted they would if the profit sat in quiet entries — but the resolution is not to add the quiet rule, it is that the FLOOR is expensive.** That is a result about a rule Jack has already decided (5%, 7 Sep), it is measured here only as a by-product of item 2d, and it is NOT being changed. It is on record and it is his call. Note also the one cell in the whole cross that reaches |t| >= 2 — A with the floor OFF at Q = 0.20, t 2.100 with 4 of 6 years positive — and note equally that its Q was chosen with hindsight, which is the whole lesson of 2c.

**A.** Best return per dip in the cross: floor **5.0%**, Q **0.20** — R +25.906, dip 7.136, R/dip **3.630**. The decided combination (floor 5%, rule off) gives R +39.874, dip 22.616, R/dip 1.763.

**B.** Best return per dip in the cross: floor **off**, Q **0.50** — R +36.241, dip 27.827, R/dip **1.302**. The decided combination (floor 5%, rule off) gives R +23.934, dip 44.541, R/dip 0.537.

## Verdict against the three conditions set at the top

1. **Beats its own control on the paired test: 0 of 2 candidates.** That condition is NOT met, and it was the first one.
2. **Broad plateau in the fixed-Q curve: NO.** Return per dip turns direction 4 times for A; 5 times for B out of a possible 8 steps. That is a maximum in noise, not a plateau. **NOT met.**
3. **Appears outside ichimoku: YES, and more strongly than in ichimoku.** 35 of 39 C1 alone have a negative rho and candidate A — the one the hypothesis came from — is the flattest thing in the table.

## Provenance

- `results/nnfx/quiet_blocked_share.csv` — 280 rows, md5 `9ed62baccb4b`
- `results/nnfx/quiet_deciles_c1.csv` — 410 rows, md5 `18f105268dbd`
- `results/nnfx/quiet_deciles_summary.csv` — 41 rows, md5 `29c4d1af54fb`
- `results/nnfx/quiet_deciles_null.csv` — 390 rows, md5 `a0ebedcdcbb5`
- `results/nnfx/quiet_fixedq.csv` — 20 rows, md5 `4b182bee4606`
- `results/nnfx/quiet_walkq.csv` — 12 rows, md5 `3e56a78c30d9`
- `results/nnfx/quiet_walkq_grid.csv` — 120 rows, md5 `82d8b337927b`
- `results/nnfx/quiet_paired.csv` — 2 rows, md5 `37662196f942`
- `results/nnfx/quiet_floor_cross.csv` — 24 rows, md5 `2dbf3979755c`
