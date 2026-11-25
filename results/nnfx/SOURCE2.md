# SOURCE 2 — ten hand-built algorithms, each with a declared reason

**Protocol: `results/nnfx/PROTOCOL.md`, unchanged. Settings fixed and in the ledger BEFORE any of them was scored. 28 pairs, 2005-2015, all eleven years unseen. Floor for best-of-10. 0 of 10 passers.**

## What is backed by a measurement and what is a declared choice

The project has measured all 39 C1 alone and all 15 baselines alone, on 28 pairs over unseen years. It has measured **nothing about which C2, which volume filter or which exit indicator to use** — stage 1 tested C1 and baselines, stage 2 tested baselines with C2, volume and the exit *blanked*. So the C1 and the baseline of every candidate below carry a number; the other three slots carry a **stated principle and no measurement**, and that is said here rather than dressed up as a citation.

Two principles were used. **C2 and the exit come from a different construction family than C1**, so the candidate is not using one signal twice — four of the six published combinations in Source 1 fail this. And **the volume slot's direction was read out of the source before it was used**: choppiness index (CI < 61.8) and efficiency ratio (ER > 0.30) are *shape* filters, while ttm squeeze, chaikin volatility, williams vix fix and volatility ratio all pass only when the market is **loud**. Item 2 measured losses concentrating in loud entries, so the loud filters are predicted to be worse. **H4 is that prediction, run.**

## The ten, with their reasons

**H1** — ichimoku/half is the best of the 39 C1 alone (+24.273 R net, 28 pairs, 2005-2015) and sma the least-bad of the 15 baselines at its best setting (double, -72.897); ichimoku with sma is also candidate A's own pair. C2/volume/exit declared: a different family each, shape filter.  
`C1 ichimoku/half · C2 vortex/default · VOL choppiness_index/default · BASE sma/double · EXIT adx_dmi/default` → **R +14.841**

**H2** — schaff_trend_cycle/default is the second-best C1 alone (+6.884 R) and aroon/default the third (+2.810), so this is the two best INDEPENDENT oscillators in C1 and C2; stc with sma is candidate B's own pair.  
`C1 schaff_trend_cycle/default · C2 aroon/default · VOL choppiness_index/default · BASE sma/double · EXIT supertrend/default` → **R +15.119**

**H3** — adx_dmi/double has the best R per TRADE of all 39 C1 alone (+0.0195) on only 75 entries in six years. The question is whether the per-trade edge survives being given a full algorithm, or whether the thinness was the edge.  
`C1 adx_dmi/double · C2 vortex/default · VOL choppiness_index/default · BASE sma/double · EXIT linreg_slope/default` → **R +1.851**

**H4** — H1 with one slot changed: an EXPANSION volume filter (true range above its own 14-bar average) in place of a shape one. Item 2 measured losses concentrating in loud entries on 35 of 39 C1, so this is PREDICTED TO BE WORSE THAN H1, and that prediction is the test.  
`C1 ichimoku/half · C2 vortex/default · VOL volatility_ratio/default · BASE sma/double · EXIT adx_dmi/default` → **R -11.903**

**H5** — H1 with every slot at its SLOW setting. The double setting was the best of three for every one of the 15 baselines without exception, which is a statement about memory length and not about baselines; this asks whether it generalises to all five slots.  
`C1 ichimoku/double · C2 vortex/double · VOL choppiness_index/double · BASE sma/double · EXIT adx_dmi/double` → **R -14.473**

**H6** — Kijun-sen is flat and STEPS, so price crosses it far less often than an SMA of the same length. The baseline distance rule and the baseline cross are the only rules in Jack's plan whose effect depends on cross frequency, and item 6a found base_cross_only the best exit arm for A by mean return per dip (+1.464 over 72 cells, best of four arms).  
`C1 schaff_trend_cycle/default · C2 vortex/default · VOL choppiness_index/default · BASE kijun/default · EXIT linreg_slope/default` → **R +2.384**

**H7** — halftrend is the third of Jack's three picked C1 -- his reason on record: "the only C1 positive net under both the jack and textbook plans at more than one setting". t3/double is the third-best baseline (-78.953) and the one least correlated in construction with sma.  
`C1 halftrend/double · C2 vortex/default · VOL choppiness_index/default · BASE t3/double · EXIT adx_dmi/default` → **R +21.258**

**H8** — WAE is the only indicator the community uses in TWO different slots (C1 in the Stonehill series, volume in N1, N7, N9 and N11) and waddah_attar_explosion/double is the fifth and last of the 39 C1 that is positive alone (+0.377 R). This runs it in both slots at once, which is what the community actually does.  
`C1 waddah_attar_explosion/double · C2 vortex/default · VOL waddah_attar_explosion/default · BASE sma/double · EXIT adx_dmi/default` → **R -24.967**

**H9** — H1 with one slot changed: rma (Wilder) in place of sma. rma/double is the second-best baseline alone (-77.057 against sma's -72.897) and the slowest-responding of the three; since no baseline is positive alone they are judged as filters, and this is the paired test of which filter.  
`C1 ichimoku/half · C2 vortex/default · VOL choppiness_index/default · BASE rma/double · EXIT adx_dmi/default` → **R -24.038**

**H10** — THE CONTROL. This is l2engine.DEFAULT_SLOTS -- the five slots the project's own Pine file ships and the ONLY five-slot combination with a parity proof against TradingView (185 of 189 entries). If the protocol fails it, the failure is about the strategy and not about the engine.  
`C1 ssl_channel/default · C2 dspo/default · VOL variance/default · BASE tma/default · EXIT ssl_channel/default` → **R +30.309**

## The four gates

| id | G1 luck | G2 one event | G3 hold-out | G4 nudge | **passer** |
|---|---|---|---|---|---|
| **H1** | fail | fail | fail | fail | no |
| **H2** | fail | fail | fail | fail | no |
| **H3** | fail | fail | fail | fail | no |
| **H4** | fail | fail | fail | fail | no |
| **H5** | fail | fail | fail | fail | no |
| **H6** | fail | fail | fail | fail | no |
| **H7** | fail | **PASS** | fail | fail | no |
| **H8** | fail | fail | fail | fail | no |
| **H9** | fail | fail | fail | fail | no |
| **H10** | fail | **PASS** | fail | fail | no |

**G1's floor is +2.242**, the 95th percentile of the block-bootstrap t under the batch's own random-entry null, corrected for best-of-10. A ten-candidate batch has a higher floor than Source 1's six by construction, and that is the price of proposing ten.

## The numbers

| id | R total | R/yr | trades | R/trade net | dip | **R/dip** | t block | t yearly | yrs + |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **H1** | +14.841 | +1.349 | 741 | +0.0102 | 43.673 | **+0.340** | +0.51 | +0.40 | 6 of 11 |
| **H2** | +15.119 | +1.374 | 814 | +0.0107 | 43.473 | **+0.348** | +0.52 | +0.36 | 5 of 11 |
| **H3** | +1.851 | +0.168 | 56 | +0.0330 | 10.299 | **+0.180** | +0.23 | +0.25 | 5 of 11 |
| **H4** | -11.903 | -1.082 | 522 | -0.0272 | 46.383 | **-0.257** | -0.53 | -0.41 | 5 of 11 |
| **H5** | -14.473 | -1.316 | 643 | -0.0291 | 46.052 | **-0.314** | -0.63 | -0.60 | 5 of 11 |
| **H6** | +2.384 | +0.217 | 2093 | -0.0008 | 89.066 | **+0.027** | +0.05 | +0.04 | 5 of 11 |
| **H7** | +21.258 | +1.933 | 1264 | +0.0144 | 52.766 | **+0.403** | +0.60 | +1.17 | 6 of 11 |
| **H8** | -24.967 | -2.270 | 2390 | -0.0104 | 100.070 | **-0.249** | -0.55 | -0.54 | 4 of 11 |
| **H9** | -24.038 | -2.185 | 812 | -0.0351 | 65.571 | **-0.367** | -0.80 | -0.89 | 4 of 11 |
| **H10** | +30.309 | +2.755 | 791 | +0.0367 | 45.354 | **+0.668** | +0.94 | +0.88 | 8 of 11 |

## The three paired tests — which slot moved the number

| against H1 | change | R total | dR | R/dip | d R/dip |
|---|---|---:|---:|---:|---:|
| **H1** | — | +14.841 | — | +0.340 | — |
| **H4** | volume slot: expansion filter instead of shape | -11.903 | -26.745 | -0.257 | -0.596 |
| **H9** | baseline: rma instead of sma | -24.038 | -38.879 | -0.367 | -0.706 |
| **H5** | every slot at its slow setting | -14.473 | -29.314 | -0.314 | -0.654 |

**The H4 prediction HELD.** Item 2's measurement said an expansion filter — one that only lets the algorithm trade when the true range is above its own average — should be worse than a shape filter. It came out worse by +26.745 R. That is one paired comparison on one candidate, not a law; it is reported because the direction was declared before the run.

## G2, one event

| id | R ex best day | R ex best 5 days | best trade share | pass |
|---|---:|---:|---:|---|
| **H1** | +10.952 | -3.101 | 0.711 | fail |
| **H2** | +10.526 | -1.588 | 0.473 | fail |
| **H3** | +0.177 | -5.457 | 1.440 | fail |
| **H4** | -15.306 | -25.601 | -0.236 | fail |
| **H5** | -17.244 | -26.265 | -0.208 | fail |
| **H6** | -5.010 | -26.138 | -2.880 | fail |
| **H7** | +16.889 | +0.932 | 0.192 | **PASS** |
| **H8** | -31.735 | -54.039 | -0.104 | fail |
| **H9** | -31.146 | -46.944 | -0.188 | fail |
| **H10** | +23.034 | +10.201 | 0.120 | **PASS** |

## G3, hold-out — the eight slices

| id | 2005-10 | 2011-15 | JPY+CHF in | out | AUD+NZD in | out | GBP+CAD in | out | worst |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **H1** | +15.118 | -0.277 | +5.865 | +8.977 | +5.795 | +9.046 | +12.935 | +1.906 | -0.277 |
| **H2** | -22.906 | +38.025 | +7.451 | +7.668 | +6.660 | +8.459 | -1.549 | +16.668 | -22.906 |
| **H3** | +0.656 | +1.195 | -2.603 | +4.454 | +5.653 | -3.803 | -2.218 | +4.069 | -3.803 |
| **H4** | +3.079 | -14.982 | -3.443 | -8.460 | -13.788 | +1.885 | -1.582 | -10.322 | -14.982 |
| **H5** | -15.080 | +0.607 | -7.099 | -7.374 | +8.607 | -23.080 | -17.646 | +3.173 | -23.080 |
| **H6** | +2.743 | -0.359 | -9.839 | +12.223 | -6.546 | +8.930 | +12.428 | -10.044 | -10.044 |
| **H7** | +15.531 | +5.727 | +21.562 | -0.304 | -1.499 | +22.757 | +7.034 | +14.224 | -1.499 |
| **H8** | -10.134 | -14.833 | -21.958 | -3.010 | +4.400 | -29.367 | -27.593 | +2.626 | -29.367 |
| **H9** | -24.239 | +0.201 | -35.858 | +11.820 | +10.378 | -34.416 | -33.287 | +9.249 | -35.858 |
| **H10** | -1.242 | +31.551 | +18.093 | +12.216 | +14.471 | +15.837 | -14.422 | +44.730 | -14.422 |

## G4, nudge

| id | runs | skipped | worst R | worst knob | negative |
|---|---:|---:|---:|---|---:|
| **H1** | 20 | 0 | -7.264 | base:sma_baseline up | 1 |
| **H2** | 20 | 0 | -24.441 | base:sma_baseline up | 2 |
| **H3** | 20 | 0 | -20.086 | c1:adx_dmi_signals down | 10 |
| **H4** | 20 | 0 | -22.199 | base:sma_baseline up | 15 |
| **H5** | 20 | 0 | -63.007 | base:sma_baseline up | 16 |
| **H6** | 20 | 0 | -32.488 | c1:schaff_trend_cycle_signals up | 10 |
| **H7** | 20 | 0 | -44.245 | base:t3_baseline up | 1 |
| **H8** | 20 | 0 | -55.206 | base:sma_baseline down | 20 |
| **H9** | 20 | 0 | -33.887 | c2:vortex_signals up | 20 |
| **H10** | 20 | 0 | -1.895 | vol:variance_volume_signals up | 1 |

## Per pair

- **H1** — 14 of 28 pairs positive. best: AUDJPY +8.5, EURCAD +6.8, CADJPY +6.2. worst: GBPJPY -5.1, AUDUSD -5.1, EURCHF -7.2.
- **H2** — 17 of 28 pairs positive. best: AUDJPY +9.5, EURJPY +7.8, GBPJPY +7.4. worst: GBPNZD -7.5, EURNZD -7.7, CADCHF -10.2.
- **H3** — 10 of 25 pairs positive. best: EURNZD +4.3, NZDUSD +3.5, NZDJPY +1.9. worst: CADJPY -1.2, AUDCHF -1.4, EURAUD -1.4.
- **H4** — 14 of 28 pairs positive. best: EURGBP +3.6, USDCHF +3.1, CADJPY +2.9. worst: GBPAUD -4.6, USDCAD -5.0, AUDCHF -5.8.
- **H5** — 15 of 28 pairs positive. best: EURAUD +6.8, NZDJPY +6.7, CHFJPY +3.8. worst: GBPUSD -6.3, GBPCAD -8.5, AUDUSD -10.0.
- **H6** — 14 of 28 pairs positive. best: GBPJPY +9.6, AUDNZD +9.3, AUDJPY +9.3. worst: AUDCHF -10.1, EURCHF -12.7, NZDCHF -17.3.
- **H7** — 12 of 28 pairs positive. best: GBPCHF +15.2, USDCHF +7.7, NZDUSD +6.7. worst: USDCAD -3.5, AUDCHF -4.5, NZDCHF -5.7.
- **H8** — 10 of 28 pairs positive. best: EURAUD +10.4, AUDJPY +8.6, EURCAD +7.4. worst: EURCHF -9.0, CADCHF -10.8, USDCAD -16.3.
- **H9** — 15 of 28 pairs positive. best: AUDJPY +10.0, NZDUSD +8.2, USDCHF +7.4. worst: NZDCHF -9.6, EURCHF -9.8, CADCHF -10.8.
- **H10** — 14 of 28 pairs positive. best: AUDJPY +11.9, GBPCHF +8.6, EURUSD +8.6. worst: AUDCAD -4.5, NZDCHF -6.5, USDCAD -6.8.

## The null

| id | draws | null t mean | null t p95 | null t max |
|---|---:|---:|---:|---:|
| **H1** | 200 | -0.132 | +1.356 | +3.076 |
| **H2** | 200 | -0.314 | +1.184 | +2.758 |
| **H3** | 200 | -0.357 | +1.469 | +2.446 |
| **H4** | 200 | -0.133 | +1.330 | +1.943 |
| **H5** | 200 | -0.156 | +1.436 | +2.376 |
| **H6** | 200 | -0.602 | +0.933 | +2.174 |
| **H7** | 200 | -0.307 | +1.485 | +2.824 |
| **H8** | 200 | -0.748 | +0.944 | +2.296 |
| **H9** | 200 | -0.303 | +1.133 | +2.145 |
| **H10** | 200 | -0.100 | +1.578 | +2.933 |

## What Source 2 says

**No hand-built candidate is a passer.** The best by return per dip is **H10** at +0.668, and it does not clear all four gates. Ten declared constructions built on the project's own best measurements do not produce a working algorithm under this protocol.

That is worth stating precisely because of WHERE the reasons came from: the C1 and baseline choices are the project's own measured leaders, not guesses. If those do not survive a complete algorithm on eleven unseen years, the problem is not the choice of C1.

## Costs

Charged **once** per round trip on the engine's own risk denominator. See `results/nnfx/COST_DOUBLE_CHARGE.md`: every NNFX table written before 25 November charges twice the measured spread. **Nothing in this document carries that fault**, which is why its R figures are not comparable with stage 1 and stage 2 numbers without the correction in that file.

## Provenance

- `results/nnfx/source2_summary.csv` — 10 rows, md5 `fe7b9ef5fc5b`
- `results/nnfx/source2_per_pair.csv` — 539 rows, md5 `de3d1c1fa205`
- `results/nnfx/source2_nulls.csv` — 10 rows, md5 `dcd5a8e79303`
- `results/nnfx/source2_nudge.csv` — 200 rows, md5 `632f83c98cfb`

The candidate ledger is `results/nnfx/proto_ledger.csv`, append-only and shared by all three sources, so no row count is quoted for it here.
