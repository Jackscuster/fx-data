# PAIR GROUPS — items 3b, 3c and 3d, Jack 25 November 2026

**The headline, and it is a negative one.** The edge is **not** pair-specific in any way a tuning-year pick can find. Every grouping loses money on the unseen years, every grouping loses MORE than pooling all 28 pairs, and the one grouping taken from Layer 1's pair character does **worse than its own shuffled labels**. At the same time the cross-sectional opportunity is enormous — with hindsight a per-pair assignment would make +520 R over the same six years — so the dispersion is real and the selection rule has no access to it.

## 3b — the three groupings, and none of them uses strategy performance

That is the whole point: a grouping built from how well strategies did on each pair would make 3c a tautology.

| grouping | what it is | measured on |
|---|---|---|
| `character` | Layer 1 trendiness — share of trending days minus share of ranging days — in terciles | **pre-2010 only**, with the classifier FIT on pre-2010 bars too |
| `bloc` | declared currency blocs: EUROPE = EUR GBP CHF, COMMODITY = AUD NZD CAD, RESERVE = USD JPY; a pair's label is its two legs' blocs, sorted | nothing — it is a fact about the currencies |
| `cost_per_atr` | round-trip cost divided by median ATR/price, in terciles | ATR pre-2010; **the cost table is a 2016–2020 measurement by construction** and that cannot be undone |

**`results/pair_character.csv` was NOT used and that matters.** Its `is` block is 1999–2015, which contains every unseen year this grouping is used to trade. The trendiness here is recomputed with the classifier fit stopping before 2010 — the fit window is the leak, not just the measurement window.

**character:** MIXED = AUDCHF AUDUSD CADJPY EURGBP EURJPY GBPCAD GBPJPY GBPUSD USDCHF; RANGE_PRONE = AUDNZD CADCHF CHFJPY EURAUD EURCAD EURCHF GBPCHF GBPNZD NZDCAD; TREND_PRONE = AUDCAD AUDJPY EURNZD EURUSD GBPAUD NZDCHF NZDJPY NZDUSD USDCAD USDJPY

**bloc:** COMMODITY-COMMODITY = AUDCAD AUDNZD NZDCAD; COMMODITY-EUROPE = AUDCHF CADCHF EURAUD EURCAD EURNZD GBPAUD GBPCAD GBPNZD NZDCHF; COMMODITY-RESERVE = AUDJPY AUDUSD CADJPY NZDJPY NZDUSD USDCAD; EUROPE-EUROPE = EURCHF EURGBP GBPCHF; EUROPE-RESERVE = CHFJPY EURJPY EURUSD GBPJPY GBPUSD USDCHF; RESERVE-RESERVE = USDJPY

**cost_per_atr:** CHEAP = AUDJPY AUDUSD EURCAD EURJPY EURUSD GBPUSD USDCAD USDCHF USDJPY; EXPENSIVE = AUDCHF AUDNZD CADCHF CHFJPY EURCHF EURGBP GBPAUD GBPCHF GBPNZD NZDCHF; MID = AUDCAD CADJPY EURAUD EURNZD GBPCAD GBPJPY NZDCAD NZDJPY NZDUSD

### How stable is each grouping over time?

| grouping | block | Spearman against pre-2010 | share of pairs keeping their label |
|---|---|---:|---:|
| character | pre2010 | +1.000 | 100.0% |
| cost_per_atr | pre2010 | +1.000 | 100.0% |
| bloc | pre2010 | +1.000 | 100.0% |
| character | unseen_2010_2015 | **-0.456** | **21.4%** |
| cost_per_atr | unseen_2010_2015 | +0.919 | 64.3% |
| bloc | unseen_2010_2015 | +1.000 | 100.0% |
| character | sealed_2016_2020 | **-0.096** | **17.9%** |
| cost_per_atr | sealed_2016_2020 | +0.824 | 64.3% |
| bloc | sealed_2016_2020 | +1.000 | 100.0% |

**PAIR CHARACTER IS NOT STABLE — it is ANTI-STABLE.** Trendiness measured before 2010 correlates **-0.456** with trendiness over 2010–2015, and only **21.4%** of pairs keep their tercile label. A pair that was trend-prone before 2010 was, if anything, range-prone afterwards. Against 2016–2020 the correlation is -0.096. `cost_per_atr` by contrast holds up (+0.919, 64.3% of labels kept) and `bloc` is constant by construction.

**That is a finding about Layer 1, not about this test.** The pair character file describes behaviour over a window and the behaviour does not persist out of that window. It is reported here because 3b asked for stability and the answer is unambiguous; nothing in Layer 1 is being changed on the back of one measurement.

## 3c — is the edge pair-specific?

At each of the six steps the best strategy for each group is picked on that step's **four TUNING years** and traded on that group in the **unseen year**. 47 candidates are available to each pick (39 C1 alone, 3 baselines alone, 3 baselines as filters, A and B), minimum 30 tuning-year trades to be eligible. A group with no eligible candidate trades nothing — it is never back-filled with the pooled winner, because that would smuggle the all-28 answer into the grouped one.

**The null SHUFFLES THE GROUP LABELS, 1,000 draws, keeping the group sizes, and repeats the whole construction** — so it tests the SELECTION RULE and not merely the components. That is the fault that invalidated A7 and it is not being repeated.

**The hindsight ceiling picks on the unseen year itself.** It is not a result and is never quoted as one. It is there because without it a negative walk-forward number cannot be told apart from "there was nothing to find".

| scheme | groups | **unseen R** | R/yr | hindsight ceiling | share of ceiling | null mean | null sd | null max | **null p** | null z |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| character | 3 | **-94.044** | -15.674 | +291.460 | -0.323 | -30.741 | +27.838 | +53.583 | **0.987** | -2.274 |
| bloc | 6 | **-73.191** | -12.199 | +383.342 | -0.191 | -40.981 | +30.142 | +41.876 | **0.860** | -1.069 |
| cost_per_atr | 3 | **-57.996** | -9.666 | +303.460 | -0.191 | -33.097 | +28.090 | +55.457 | **0.810** | -0.886 |
| single_pairs | 28 | **-72.029** | -12.005 | +520.643 | -0.138 | — | — | — | — | — |
| all_28 | 1 | **-50.960** | -8.493 | +171.244 | -0.298 | — | — | — | — | — |

### What that table says, in order

1. **The selection rule loses before grouping is even involved.** Pooled over all 28 pairs — one pick per step, the simplest possible version — it makes **-50.960 R** over the six unseen years, -8.493 a year. So the problem is not which pairs go together. It is that **a strategy's rank on four tuning years does not carry to the next year at all.**
2. **Every grouping is WORSE than pooling.** all_28 (1 groups) -50.960; character (3 groups) -94.044; cost_per_atr (3 groups) -57.996; bloc (6 groups) -73.191; single_pairs (28 groups) -72.029. There is no clean relationship with the number of groups — `character` has three groups and is the worst of all — so this is not simply "smaller samples make noisier picks". The grouping itself matters, and it matters in the wrong direction.
3. **The Layer 1 character grouping is worse than its own shuffled labels**: null p **0.987**, z **-2.274** — **987 of the 1,000 random regroupings beat the real one**, and only 13 did worse. That is exactly what the 3b stability table predicts: a grouping whose labels anti-correlate with the period being traded should underperform random labels, and it does. Note the direction of the test — a null p near 1 is not "no evidence", it is evidence AGAINST.
4. **And yet the opportunity is real and large.** Picking per pair with hindsight makes **+520.643 R** over the same six years, +86.8 a year, against -72.029 actually achieved. The cross-sectional dispersion is enormous; **no tested selection rule has any access to it.**

**WHAT THIS MEANS FOR THE BOOK PLAN, stated plainly because it is the point of the whole item.** The plan is a handful of strategies each assigned to the pairs it suits. This test says the ASSIGNMENT STEP, done the obvious way, destroys value rather than adding it. It does not say the book plan is wrong — it says an assignment cannot be made by ranking candidates on recent performance, which is the only mechanism tested here. An assignment made from something that is NOT performance — pair character would have been the candidate, and 3b has just shown it does not persist — would be a different test.

### Which candidate each group actually picked

The picks are in `group_assign_steps.csv` in full. The shape of them is the diagnosis: 
across the four declared schemes, 78 picks were made and the most frequently chosen candidates were `hieken_ashi_smoothed_signals` (11), `waddah_attar_explosion_signals` (9), `vortex_signals` (6), `linreg_slope_signals` (6), `trend_direction_force_index_signals` (5). **27 distinct candidates were picked at least once**, out of 47 — the rule is not settling on anything.

## 3d — correlation of daily P&L

Days are UNIONED and missing days are **zero**, not dropped. A day a sleeve is out of the market is a real zero for that sleeve; dropping it would compute the correlation only on days both happened to trade, which is a different and much more flattering number.

### Between groups — candidate A's own daily series, sliced by each grouping

| | MIXED | RANGE_PRONE | TREND_PRONE | COMMODITY-CO | COMMODITY-EU | COMMODITY-RE | EUROPE-EUROP | EUROPE-RESER | RESERVE-RESE | CHEAP | EXPENSIVE | MID |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:||
| character:MIXED | **1.000** | +0.224 | +0.264 | +0.038 | +0.254 | +0.425 | +0.290 | +0.677 | +0.180 | +0.580 | +0.382 | +0.440 |
| character:RANGE_PRONE | +0.224 | **1.000** | +0.191 | +0.419 | +0.614 | +0.091 | +0.322 | +0.261 | +0.057 | +0.302 | +0.677 | +0.346 |
| character:TREND_PRONE | +0.264 | +0.191 | **1.000** | +0.265 | +0.440 | +0.643 | +0.037 | +0.230 | +0.340 | +0.541 | +0.381 | +0.549 |
| bloc:COMMODITY-COMMODITY | +0.038 | +0.419 | +0.265 | **1.000** | +0.115 | +0.051 | -0.047 | +0.062 | +0.020 | +0.051 | +0.209 | +0.474 |
| bloc:COMMODITY-EUROPE | +0.254 | +0.614 | +0.440 | +0.115 | **1.000** | +0.094 | +0.037 | +0.045 | +0.001 | +0.172 | +0.703 | +0.382 |
| bloc:COMMODITY-RESERVE | +0.425 | +0.091 | +0.643 | +0.051 | +0.094 | **1.000** | +0.013 | +0.167 | +0.088 | +0.546 | +0.096 | +0.525 |
| bloc:EUROPE-EUROPE | +0.290 | +0.322 | +0.037 | -0.047 | +0.037 | +0.013 | **1.000** | +0.049 | +0.092 | +0.080 | +0.510 | -0.016 |
| bloc:EUROPE-RESERVE | +0.677 | +0.261 | +0.230 | +0.062 | +0.045 | +0.167 | +0.049 | **1.000** | +0.158 | +0.661 | +0.188 | +0.243 |
| bloc:RESERVE-RESERVE | +0.180 | +0.057 | +0.340 | +0.020 | +0.001 | +0.088 | +0.092 | +0.158 | **1.000** | +0.417 | +0.085 | +0.054 |
| cost_per_atr:CHEAP | +0.580 | +0.302 | +0.541 | +0.051 | +0.172 | +0.546 | +0.080 | +0.661 | +0.417 | **1.000** | +0.154 | +0.194 |
| cost_per_atr:EXPENSIVE | +0.382 | +0.677 | +0.381 | +0.209 | +0.703 | +0.096 | +0.510 | +0.188 | +0.085 | +0.154 | **1.000** | +0.183 |
| cost_per_atr:MID | +0.440 | +0.346 | +0.549 | +0.474 | +0.382 | +0.525 | -0.016 | +0.243 | +0.054 | +0.194 | +0.183 | **1.000** |

**Within a grouping, the groups are genuinely diversifying**: **character** 0.191 to 0.264 (median 0.224); **bloc** -0.047 to 0.167 (median 0.051); **cost_per_atr** 0.154 to 0.194 (median 0.183). That is the one piece of good news in this document — slicing ONE strategy across pair groups gives sleeves that are close to independent, which is what a book needs. The high numbers in the table are all BETWEEN groupings and are just membership overlap: `bloc:COMMODITY-EUROPE` and `cost_per_atr:EXPENSIVE` correlate 0.703 because they are largely the same pairs.

### Between strategies

41 series over the unseen years: median pairwise correlation **0.347**, mean 0.297, range -0.593 to 0.883.

**A against B is 0.370** — the two carried-forward candidates are only moderately correlated, so as SLEEVES they diversify each other. A's closest relatives are `trend_direction_force_index_signals` 0.506, `bears_bulls_impulse_signals` 0.485, `ichimoku_signals` 0.452.

## What is settled and what is not

1. **Settled: every candidate is now banked per pair and per direction**, with the leverage cap applied over the whole frame before splitting, and every year labelled tune / unseen / sealed. `PER_PAIR_BANK.md`.
2. **Settled: picking a strategy per group on tuning-year performance does not work.** It loses pooled, it loses worse grouped, and the Layer 1 character grouping loses worse than random labels.
3. **Settled: pair character does not persist.** Spearman **−0.456** from pre-2010 to 2010–2015, 21% of labels kept.
4. **Settled: the sleeves a grouping produces are close to independent**, and A and B correlate 0.370. The diversification the book plan needs is available; the selection the book plan needs is not.
5. **NOT settled: whether any assignment rule works.** One mechanism was tested — rank on four tuning years. The hindsight ceiling says there is +520 R of cross-sectional dispersion to aim at over six years. Finding a rule that reaches any of it is a new experiment and is not in item 3.

## Provenance

- `results/nnfx/pair_groups.csv` — 28 rows, md5 `019ce35df54e`
- `results/nnfx/pair_groups_stability.csv` — 9 rows, md5 `bc7dfbc8eb0a`
- `results/nnfx/group_assign.csv` — 5 rows, md5 `2b72b4d02f8f`
- `results/nnfx/group_assign_steps.csv` — 246 rows, md5 `8faaa8b67bde`
- `results/nnfx/group_daily_corr.csv` — 12 rows, md5 `9578836ef632`
- `results/nnfx/strategy_daily_corr.csv` — 41 rows, md5 `df36eebaf87a`
