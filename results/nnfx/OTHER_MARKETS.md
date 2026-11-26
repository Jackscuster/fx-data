# OTHER_MARKETS — item 3, parts a to d

**Same protocol as amended. Nothing about the method changed except what `PROTOCOL.md` A16 declares**, and A16 exists because one engine standing rule — the peg guard — reaches for the 28 FX pairs by construction and had to be pointed at the traded universe instead.

Parts **e, f and g are NOT in this file.** What is missing and what it needs is stated at the end, plainly.

## 3a — history and gaps, every row fetched today

| instrument | ticker | group | bars | first | last | evidence bars (to 2015) | evidence yrs | worst gap (cal days) | gaps >7d |
|---|---|---|---:|---|---|---:|---:|---:|---:|
| gold | `GC=F` | metals_energy | 6587 | 2000-08-30 | 2026-11-26 | 3845 | 15.3 | 5 | 0 |
| silver | `SI=F` | metals_energy | 6588 | 2000-08-30 | 2026-11-26 | 3847 | 15.3 | 5 | 0 |
| wti | `CL=F` | metals_energy | 6595 | 2000-08-23 | 2026-11-26 | 3853 | 15.3 | 5 | 0 |
| brent | `BZ=F` | metals_energy | 4813 | 2007-07-30 | 2026-11-26 | 2070 | 8.2 | 17 | 1 |
| spx | `^GSPC` | indices | 10557 | 1985-01-02 | 2026-11-25 | 7816 | 31.0 | 7 | 0 |
| ndx | `^NDX` | indices | 10369 | 1985-10-01 | 2026-11-25 | 7628 | 30.3 | 7 | 0 |
| dji | `^DJI` | indices | 8788 | 1992-01-02 | 2026-11-25 | 6047 | 24.0 | 7 | 0 |
| dax | `^GDAXI` | indices | 9841 | 1987-12-30 | 2026-11-26 | 7072 | 28.1 | 6 | 0 |
| ftse | `^FTSE` | indices | 10586 | 1985-01-02 | 2026-11-26 | 7831 | 31.1 | 5 | 0 |
| nikkei | `^N225` | indices | 10288 | 1985-01-02 | 2026-11-25 | 7627 | 30.3 | 11 | 3 |
| btc | `BTC-USD` | crypto | 4454 | 2014-09-17 | 2026-11-26 | 471 | 1.9 | 1 | 0 |
| eth | `ETH-USD` | crypto | 3305 | 2017-11-09 | 2026-11-26 | 0 | 0.0 | 1 | 0 |

**The indices reach further back than the 24 November data report assumed** — it fetched from 1990 and these were fetched from 1985, so the S&P 500 and the FTSE 100 carry **31 years of evidence**, more than the FX data itself.

**ETH has zero evidence bars.** Its first bar is 2017-11-09, after the evidence period closes. BTC has **1.9 years**. Under Jack's calendar neither can be tuned at all, which is 3c's answer before any test is run.

### A data-quality finding the geometry check caught

A bar must contain its own open and close. The futures series violate it: **gold on 463 bars, silver on 244, Brent on 69, WTI on 7**. The six indices and both crypto series violate it on **zero**. The violations are repaired the way a synthetic world is repaired — high raised to max(high, open, close), low lowered to min — and the count is reported rather than silently fixed.

## 3a — the second source, on ten random dates each

**This is the weakest part of item 3, and it is weak for a reason outside my reach.** Only three of the twelve have a reachable independent source. Everything tried and refused is listed below so the limit is auditable.

| instrument | tier | source | n | worst difference | reading |
|---|---|---|---:|---:|---|
| gold | proxy | same underlying via GLD, DAILY RETURNS only | 10 | 0.941 pp of daily return | moderate — +0.888 against GLD |
| silver | proxy | same underlying via SLV, DAILY RETURNS only | 10 | 1.523 pp of daily return | moderate — +0.897 against SLV |
| wti | proxy | same underlying via USO, DAILY RETURNS only | 10 | 9.619 pp of daily return | **poor, +0.541** — USO is a known-bad tracker of WTI, so this says nothing about the price series and everything about the proxy |
| brent | proxy | same underlying via BNO, DAILY RETURNS only | 10 | 1.981 pp of daily return | moderate — +0.912 against BNO |
| spx | proxy | same underlying via SPY, DAILY RETURNS only | 10 | 0.148 pp of daily return | strong — returns track SPY at +0.984 |
| ndx | independent | api.nasdaq.com historical (NDX) | 10 | 3.57e-08 relative | exact — 3.6e-08 relative, the series is confirmed |
| dji | proxy | same underlying via DIA, DAILY RETURNS only | 10 | 0.425 pp of daily return | strong — returns track DIA at +0.987 |
| dax | proxy | same underlying via EWG, DAILY RETURNS only | 10 | 1.463 pp of daily return | **uninformative, +0.738** — EWG is USD-denominated and trades in US hours |
| ftse | proxy | same underlying via EWU, DAILY RETURNS only | 10 | 2.864 pp of daily return | **uninformative, +0.668** — EWU, same reason |
| nikkei | proxy | same underlying via EWJ, DAILY RETURNS only | 10 | 1.840 pp of daily return | **uninformative, +0.427** — EWJ, same reason |
| btc | independent | Coinbase Exchange public candles | 10 | 2.37e-02 relative | **2.37% relative** — crypto has no official close, so two venues disagree by this much on the same day |
| eth | independent | Coinbase Exchange public candles | 10 | 1.26e-02 relative | **1.26% relative** — same reason |

**Endpoints tried and refused**, so this is a reach limit and not an omission:

- `stooq.com / stooq.pl` — returns a JavaScript anti-bot challenge instead of CSV for every symbol tried
- `fred.stlouisfed.org fredgraph.csv` — read timeout on SP500 and DJIA, retried
- `financialmodelingprep.com` — HTTP 401 without an API key
- `api.statistiken.bundesbank.de (DAX)` — HTTP 404 on the documented path
- `api.nasdaq.com for SPX, DJI and commodities` — rCode 400 -- the endpoint serves COMP and NDX only

**What this means for the result.** The S&P 500, Dow and Nasdaq 100 series are confirmed. Gold, silver and Brent are consistent with their ETFs. **WTI, DAX, FTSE and Nikkei are UNVERIFIED** — the only proxy available measures a different thing and no independent source was reachable. Any result on those four carries that caveat.

## 3b — costs: a stated baseline, swept 1x to 5x

| instrument | published points | point size | baseline (bp round trip) | exchange tick floor (bp) | confidence |
|---|---:|---:|---:|---:|---|
| gold | 0.5 | 1 | 1.131 | 0.226 | published |
| silver | 3 | 0.01 | 4.455 | 0.743 | published_unit_corrected_by_tick_floor |
| wti | 5 | 0.01 | 5.828 | 1.166 | published_unit_ambiguous |
| brent | 5 | 0.01 | 5.436 | 1.087 | placeholder_group_median |
| spx | 1 | 1 | 1.358 | -- | published |
| ndx | 3 | 1 | 1.070 | -- | published |
| dji | 5 | 1 | 0.996 | -- | published |
| dax | -- | 1 | 1.070 | -- | placeholder_group_median |
| ftse | -- | 1 | 1.070 | -- | placeholder_group_median |
| nikkei | -- | 1 | 1.070 | -- | placeholder_group_median |
| btc | -- | 1 | -- | -- | no_source |
| eth | -- | 1 | -- | -- | no_source |

FX reference: **majors 1.5 bp, crosses 3.0 bp** round trip. The index CFDs come out comparable to an FX major; WTI comes out about four times one.

### The exchange tick turned out to be a validator, not a footnote

A retail CFD spread cannot be **tighter** than the underlying exchange's minimum tick. Silver's published figure read as **0.446 bp against a tick floor of 0.743 bp**, which is impossible, so the point size was wrong by a factor of ten. The correction is applied by the factor the floor implies and the row is relabelled `published_unit_corrected_by_tick_floor`. Every baseline now sits at or above its floor, checked arithmetically.

**BTC and ETH have no cost source, so they are not costed and not booked.** That leaves **ten** instruments. The five swept tables are `results/nnfx/mkt/cost_table_mkt_x{1,2,3,4,5}.csv`.

### For Jack to fill in — the MT5 symbol list

Every number above the sweep is a published headline, not a measured two-sided spread, and the FX work is costed from **measured OANDA hourly bid/ask**. These are not the same kind of number, and the sweep exists because of it.

| instrument | baseline used (bp) | your MT5 spread | ratio to baseline |
|---|---:|---|---|
| gold | 1.131 | | |
| silver | 4.455 | | |
| wti | 5.828 | | |
| brent | 5.436 | | |
| spx | 1.358 | | |
| ndx | 1.070 | | |
| dji | 0.996 | | |
| dax | 1.070 | | |
| ftse | 1.070 | | |
| nikkei | 1.070 | | |
| btc | -- | | |
| eth | -- | | |

## 3c — the calendar, unchanged

Evidence to **2015**. **2016-2020 computed and not reported.** **2021 onward sealed.** The admission and scoring windows are the same 2005-2010 and 2011-2015 the FX work uses, on purpose: item 3g asks for a combined book, and a book whose halves were admitted on different calendars is not one book. The extra index history back to 1985 is measured above and deliberately not used.

**Crypto, reported separately as Jack asked.** It is not that short history is awkward — **ETH has no evidence period at all** and BTC has 1.9 years against the 5 to 6 every other instrument gets. Neither has a cost source. Neither is admitted, booked or scored anywhere in this file, and no amount of compute changes that: it would need a different calendar, which would make its results non-comparable with everything else here.

## 3d — the sleeve bank, the 18 declared algorithms

| | FX, 28 pairs | other markets, 10 instruments |
|---|---:|---:|
| sleeve-windows | 1008 | 360 |
| median trades | 18 | 20 |
| mean R per sleeve-window | **-0.012** | **+0.378** |
| share positive | 0.469 | 0.497 |
| admitted | 11 (1.09%) | 5 (1.39%) |

**The 18 declared algorithms are not worse off FX — they are mildly better.** Mean R per sleeve-window is **+0.378** on the other instruments against **-0.012** on FX. Both are close to zero and the admission rate is about 1% either way, so this is not an edge; it is the absence of the penalty one might have expected.

**Trade counts are the same, which rules out the obvious artefact.** Median 18 on FX and 20 off it, with near-identical deciles, so the handful of admissions is the admission test being strict and not these instruments being untradeable.

**All five admissions fall in 2005-2010 and none in 2011-2015.**

| instrument | window | mean R | best R | admitted | median trades |
|---|---|---:|---:|---:|---:|
| brent | h1 | -1.39 | +5.57 | 0 | 13 |
| brent | h2 | -1.58 | +3.20 | 0 | 14 |
| dax | h1 | +3.86 | +15.90 | 1 | 22 |
| dax | h2 | +1.15 | +10.66 | 0 | 19 |
| dji | h1 | +0.43 | +9.88 | 0 | 24 |
| dji | h2 | -2.01 | +7.86 | 0 | 24 |
| ftse | h1 | +1.80 | +12.79 | 1 | 17 |
| ftse | h2 | +0.36 | +9.00 | 0 | 25 |
| gold | h1 | +0.73 | +13.92 | 1 | 24 |
| gold | h2 | +2.76 | +7.70 | 0 | 21 |
| ndx | h1 | +0.95 | +5.44 | 0 | 22 |
| ndx | h2 | +1.06 | +10.61 | 0 | 22 |
| nikkei | h1 | +0.58 | +14.59 | 1 | 24 |
| nikkei | h2 | +0.92 | +14.82 | 0 | 22 |
| silver | h1 | +2.12 | +13.12 | 1 | 21 |
| silver | h2 | -0.69 | +7.88 | 0 | 18 |
| spx | h1 | -0.83 | +3.98 | 0 | 24 |
| spx | h2 | -1.13 | +6.45 | 0 | 24 |
| wti | h1 | -0.71 | +6.76 | 0 | 22 |
| wti | h2 | -0.82 | +3.54 | 0 | 11 |

### A16, measured rather than assumed

A16 kept the peg guard switched on for sameness of method while warning that its cross-section is heterogeneous off FX. Measured: it blocks **0.3% of bars** across the ten instruments against **0.7% on the 28 FX pairs**. It barely binds, so no result here rests on it, and the low admission count is not its doing.

## What is NOT in this file

**3d, the Source 3 sample.** The 18 declared algorithms are done. The 200,000-algorithm sample on ten instruments is the same shape of job as the FX bank and needs a clear run at the machine; three null workers hold it until about 18:00.

**3e, does fit carry here.** Needs the sample bank above, and a scrambled-data null built per instrument.

**3f, the books under the five gates**, including the instrument-group rotations. Needs 3d and 3e.

**3g, the combined FX plus other-markets book.** Needs 3f.

None of these is blocked on a decision — they are blocked on compute, and on the machine being busy with item 1. The engine wiring they need is built and tested: `nnfxmkt.frames` feeds `set_world`, the cost tables load, and the declared bank ran with **zero errors on 360 sleeve-windows**.

## Provenance

- `results/nnfx/mkt/availability.csv` — 12 rows
- `results/nnfx/mkt/verify.csv` — 12 rows
- `results/nnfx/mkt/cost_baseline.csv` — 12 rows
- `results/nnfx/mkt/declared_bank_x1.csv` — 360 rows
- `results/nnfx/mkt/declared_bank_fx_reference.csv` — 1008 rows
- `data/other/*.csv` — 12 daily OHLC series, fetched 2026-11-26
- `code/nnfxmkt.py`; fetcher `code/l2data.py:yahoo_ohlc`
- `PROTOCOL.md` A16 — the peg guard off FX
- tick sizes: CME Group contract specifications, corroborated by the AMP Futures spec table and the CITICS June 2026 futures sheet
- spreads: Pepperstone published CFD spread tables (01/07/2025-30/09/2025) and Capital.com indicative September spreads
