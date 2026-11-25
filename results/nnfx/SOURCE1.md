# SOURCE 1 — the six published NNFX combinations

**Protocol: `results/nnfx/PROTOCOL.md`, unchanged. Zero search. 28 pairs, 2005-2015, all eleven years unseen because nothing is tuned. 0 of 6 passers.**

N1 to N6 are the only NNFX combinations the community has actually named with settings, from the 9 November catalogue. All six are **grade N** — named components, no published settings for every slot, and **no published results anywhere that can be re-run**. This is the first time any of them has been tested on eleven years of 28 pairs with era-correct costs, a 1:30 leverage cap and realistic gap fills.

## The six, as published

| id | published construction | trades/yr |
|---|---|---:|
| **N1** | Kijun-sen 26 / SSL Channel 10 / TDFI 13 +-0.05 / WAE 150-20-40 BB 20,2.0 / SSL | 9.7 |
| **N2** | HMA 20 / DiDi 8-20 / DSPO 14 / Variance EMA 10 / Chandelier 22,3.0 | 247.2 |
| **N3** | McGinley Dynamic / STC 12-26-10 65/35 / Vortex 14 / Damiani Volatmeter / Supertrend 10,3.0 | 104.7 |
| **N4** | KAMA / Coral 10-14 / QQE Mod 6-5-1.61 / TTM Squeeze / Coral | 152.2 |
| **N5** | EMA 20-30 (25 declared) / Aroon 25 / Kalman 1.0-1.0 / Volatility Ratio / Aroon | 164.8 |
| **N6** | Super Smoother 2-pole / Half Trend / Fisher Transform / Williams VIX Fix / Half Trend | 7.8 |

**4 of the 6 use their own C1 as their exit indicator** (N1 SSL, N4 Coral, N5 Aroon, N6 Half Trend). That is what the sources publish, so it is run as published — but those four are using one piece of information twice, and "five slots" does not mean five independent signals for them.

## The four gates

| id | G1 luck | G2 one event | G3 hold-out | G4 nudge | **passer** |
|---|---|---|---|---|---|
| **N1** | fail | fail | fail | fail | no |
| **N2** | fail | **PASS** | **PASS** | fail | no |
| **N3** | fail | fail | fail | fail | no |
| **N4** | fail | fail | fail | fail | no |
| **N5** | fail | fail | fail | fail | no |
| **N6** | fail | fail | fail | fail | no |

**G1's floor is +1.973** — the 95th percentile of the block-bootstrap t under the batch's own random-entry null, corrected for best-of-6. Each candidate's null is matched on its own per-pair trade count, its own holding periods and its own long/short split, so only the TIMING is random. The floor comes from the batch, not from a table.

## The numbers

| id | R total | R/yr | trades | R/trade net | R/trade gross | dip | **R/dip** | t block | t yearly | yrs + |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **N1** | -0.457 | -0.042 | 107 | -0.0043 | +0.0120 | 17.646 | **-0.026** | -0.05 | -0.07 | 5 of 11 |
| **N2** | +38.769 | +3.524 | 2719 | +0.0143 | +0.0305 | 69.846 | **+0.555** | +0.84 | +1.28 | 8 of 11 |
| **N3** | +3.053 | +0.278 | 1152 | +0.0027 | +0.0183 | 59.869 | **+0.051** | +0.09 | +0.08 | 5 of 11 |
| **N4** | -24.510 | -2.228 | 1674 | -0.0146 | +0.0009 | 81.704 | **-0.300** | -0.58 | -0.48 | 4 of 11 |
| **N5** | +20.450 | +1.859 | 1813 | +0.0079 | +0.0239 | 67.044 | **+0.305** | +0.43 | +0.39 | 4 of 11 |
| **N6** | +0.595 | +0.054 | 86 | +0.0069 | +0.0222 | 12.574 | **+0.047** | +0.07 | +0.07 | 6 of 11 |

`dip` is the **binding** dip — the maximum of the realised chronological drawdown and DIP95, the 95th percentile over shuffled day orders. DIP95 sat above the realised dip on all eight sleeves of item 5, by 1.22x to 2.36x, so the maximum is taken rather than assumed.

## G2, one event — the three numbers

| id | R ex best day | R ex best 5 days | best trade share | best day R | pass |
|---|---:|---:|---:|---:|---|
| **N1** | -3.028 | -9.946 | -5.454 | +2.571 | fail |
| **N2** | +28.699 | +5.508 | 0.081 | +10.070 | **PASS** |
| **N3** | -3.860 | -19.141 | 1.156 | +6.913 | fail |
| **N4** | -33.692 | -50.453 | -0.174 | +9.182 | fail |
| **N5** | +15.534 | -0.624 | 0.307 | +4.916 | fail |
| **N6** | -1.697 | -7.030 | 3.996 | +2.292 | fail |

## G3, hold-out — the eight slices

| id | 2005-10 | 2011-15 | JPY+CHF in | JPY+CHF out | AUD+NZD in | AUD+NZD out | GBP+CAD in | GBP+CAD out | worst |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **N1** | +7.992 | -8.450 | -1.342 | +0.885 | -0.196 | -0.261 | +0.919 | -1.376 | -8.450 |
| **N2** | +12.987 | +25.782 | +4.736 | +34.033 | +21.157 | +17.612 | +25.648 | +13.121 | +4.736 |
| **N3** | +17.459 | -14.407 | +3.401 | -0.348 | +3.197 | -0.144 | -4.835 | +7.888 | -14.407 |
| **N4** | +14.832 | -39.342 | +5.394 | -29.904 | -58.466 | +33.956 | +14.809 | -39.319 | -58.466 |
| **N5** | -28.558 | +49.008 | +8.999 | +11.451 | +8.767 | +11.684 | +9.066 | +11.384 | -28.558 |
| **N6** | -0.453 | +1.048 | +1.578 | -0.983 | -5.294 | +5.889 | +1.220 | -0.625 | -5.294 |

The split is taken from the **whole 28-pair capped frame**. Re-running the engine on a 15-pair subset would re-run the 1:30 leverage cap on a smaller portfolio, which is an easier book than the one the trader runs — the same rule item 3 adopted for the per-pair bank.

## G4, nudge — the worst of 20 per candidate

| id | runs | skipped | worst R | worst knob | negative |
|---|---:|---:|---:|---|---:|
| **N1** | 20 | 0 | -30.745 | base:kijun_baseline up | 12 |
| **N2** | 20 | 0 | -22.308 | base:hma_baseline down | 1 |
| **N3** | 20 | 0 | -35.141 | base:mcginley_dynamic_index up | 7 |
| **N4** | 20 | 0 | -77.611 | base:kama_baseline down | 20 |
| **N5** | 20 | 0 | -26.549 | base:ema_baseline down | 5 |
| **N6** | 20 | 0 | -8.665 | c1:halftrend_signals up | 5 |

Each slot's length knob at x0.5 and x2, ATR length 7 and 28, stop 0.75 and 1.25 ATR, target 1.0x and 2.0x, baseline distance 1.0 and 2.0 ATR, bridge 5 and 9 candles — one at a time, 20 runs. The steps are deliberately coarser than `l2tune`'s GAUNTLET grids, where a 0.05 nudge on the stop would pass by construction. `skipped` counts knobs that do not exist or whose nudge collapses onto the candidate.

## Per pair — the best and worst five of each candidate

- **N1** — 13 of 27 pairs positive. best: EURAUD +3.9, EURGBP +2.4, AUDCHF +1.6, NZDCAD +1.4, AUDJPY +1.2. worst: AUDNZD -1.4, AUDCAD -1.5, USDCAD -1.8, NZDCHF -2.0, EURCHF -2.8.
- **N2** — 19 of 28 pairs positive. best: USDCHF +10.6, EURNZD +10.4, GBPNZD +8.3, NZDCAD +7.5, GBPCHF +6.2. worst: EURCHF -4.0, AUDCHF -4.7, EURJPY -4.9, CADCHF -7.4, AUDUSD -8.8.
- **N3** — 15 of 28 pairs positive. best: EURJPY +7.8, NZDJPY +7.1, GBPJPY +6.1, AUDUSD +5.6, GBPUSD +5.3. worst: GBPAUD -4.7, NZDCAD -5.2, AUDCHF -5.2, EURCHF -7.6, USDCAD -8.5.
- **N4** — 12 of 28 pairs positive. best: GBPJPY +9.7, EURGBP +8.7, CHFJPY +8.3, CADJPY +6.0, EURJPY +5.3. worst: USDCHF -5.4, AUDCAD -5.7, GBPCAD -8.3, EURAUD -10.1, NZDCHF -12.5.
- **N5** — 16 of 28 pairs positive. best: NZDJPY +12.1, EURJPY +7.6, NZDUSD +6.3, GBPNZD +5.7, AUDUSD +5.6. worst: CADCHF -3.5, EURCHF -4.1, GBPCHF -6.4, NZDCHF -9.4, EURAUD -9.5.
- **N6** — 12 of 28 pairs positive. best: NZDCAD +3.6, EURCHF +2.1, CADCHF +2.0, CADJPY +1.7, AUDNZD +1.6. worst: CHFJPY -1.2, AUDCHF -1.2, EURNZD -1.3, GBPAUD -2.4, GBPNZD -3.2.

The full 28-pair-by-direction table is in `results/nnfx/source1_per_pair.csv`.

## The null

| id | draws | null t mean | null t p95 | null t max |
|---|---:|---:|---:|---:|
| **N1** | 200 | -0.177 | +1.406 | +2.253 |
| **N2** | 200 | -0.565 | +0.961 | +2.629 |
| **N3** | 200 | -0.507 | +1.236 | +1.840 |
| **N4** | 200 | -0.389 | +1.137 | +1.913 |
| **N5** | 200 | -0.377 | +0.988 | +1.873 |
| **N6** | 200 | -0.081 | +1.429 | +2.906 |

## What Source 1 says

**None of the six published combinations is a passer.** Not one clears all four gates on eleven unseen years of 28 pairs. These are the community's named algorithms at their own settings, and the catalogue already warned what to expect: grade N throughout, no reproducible result anywhere, and the two self-reported backtests pointing opposite ways.

That is a result and not a non-result. It means the project is not leaving a known working algorithm untested, and it sets the bar Sources 2 and 3 have to clear.

## Costs, and a correction that applies to everything else

Every figure here is charged **once** per round trip on the engine's own risk denominator. `results/nnfx/COST_DOUBLE_CHARGE.md` records a fault found while building this protocol: every NNFX-phase table written before 25 November charges **twice** the measured spread, because `l2engine.run` risks 200 per unit of raw r while `nnfx1._cost_R` divides by 100. The fault is pessimistic, it does not touch the gauntlet path, and **nothing in this document carries it.**

## Provenance

- `results/nnfx/source1_summary.csv` — 6 rows, md5 `4da72878975c`
- `results/nnfx/source1_per_pair.csv` — 304 rows, md5 `b97dfdf0e665`
- `results/nnfx/source1_nulls.csv` — 6 rows, md5 `210e37c03b7a`
- `results/nnfx/source1_nudge.csv` — 120 rows, md5 `6411bbef1f85`

The candidate ledger is `results/nnfx/proto_ledger.csv`. It is append-only and shared by all three sources, so it carries no row count here: its count changes every time a source declares its candidates, and a provenance line that goes stale on the next run is worse than no line (preflight guard 35 caught exactly that on the first draft of this document).
