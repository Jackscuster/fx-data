# GAP FILLS — item 1, Jack 25 November 2026

**The question: when price gaps through a stop, what does the engine fill at?**

## The answer as the engine stood

| case | what it filled at | right? |
|---|---|---|
| price walks through the level inside the bar | the stop | **yes** |
| the daily bar OPENS beyond the stop | the daily open | **yes**, and already there |
| the bar opens on the right side of the stop and then JUMPS through it mid-session | the stop | **NO.** There was no quote there |

Only the third case was wrong, and it is the one that matters, because it is the shape every currency-peg break has. EURCHF on 15 January 2015: the daily bar dated the 15th (16:00 NY on the 14th to 16:00 NY on the 15th) **opens at 1.2008**, above every long stop anyone held, so the opening-gap rule never fires. The hourly bid went **1.20083 open, 1.16777 low at 09:00 UTC, and the next hour opened at 1.03592**. A long stop at 1.10 was booked at 1.10.

## What is standing now

`l2engine._gap_px`, from 25 Nov, enforced by **pre-flight guard 41**: a stop fills at the **first tradable price at or beyond it** — the daily open for an overnight gap, the breaching hour's OPEN on the fill side for an intraday one, and the stop price itself only where price was genuinely quoted through it. A long exits by selling so it fills on the **bid**; a short buys so it fills on the **ask**. An hourly open counts as a gap only when it is beyond the stop by more than the pair's round-trip cost — a charge the cost table is already making, and the one place these two feeds (daily MID, hourly BID/ASK) could otherwise double-count.

**The hourly-OFF path is byte-identical to the pre-patch engine** — six base/plan cells on four pairs, same trade counts, same R to ten decimals, same exit prices, SHA `e5264776bbacc833` both ways.

## THE RESOLUTION LIMIT, stated before the numbers

**An hour is not a tick, and on this event that is decisive.** Inside the hour that breaches the stop this method cannot say what was quoted, so it keeps the stop price. On 15 Jan 2015 the breaching hour for any stop near the peg is the 09:00 bar, whose own range (1.20090 down to 1.16777) covers that stop — so **a 1.5 ATR stop is not seen as gapped at all** and still fills at the stop, exactly as before. That is a measurement limit, not a result, and the table below therefore gives three fills: the stop, the hourly rule, and the **bound** — the worst price the breaching hour contains. The bound is a bound. Making it the standing fill would be a judgement the data cannot support, and that call is Jack's, not mine.

## A LONG EURCHF held into 15 January 2015

**No candidate held this trade.** Every A, B and C entry through the de-peg was a SHORT, which is why the SNB day is a windfall in those tables and not a ruin. This is the other side, constructed: long at the close of 14 Jan 2015 (the last bar before the break), stop at a multiple of that bar's 14-day ATR, sized the way the engine sizes — risk at the stop distance. The entry date is the event, not a choice, and nothing here is optimised.

ATR on 14 Jan 2015 was **0.00110** (11.0 pips) on a price of **1.20096** — the pair had been pegged for three years.

| stop | stop price | fill | fill price | R, engine size | leverage | cap scale | R, capped size |
|---:|---:|---|---:|---:|---:|---:|---:|
| 1.0 ATR | 1.19986 | stop | 1.19986 | -0.667 | 10.91:1 | 1.0000 | -0.667 |
| 1.0 ATR | 1.19986 | hourly | 1.19986 | -0.667 | 10.91:1 | 1.0000 | -0.667 |
| 1.0 ATR | 1.19986 | **bound** | 1.16777 | **-20.100** | 10.91:1 | 1.0000 | **-20.100** |
| 1.5 ATR | 1.19931 | stop | 1.19931 | -1.000 | 7.27:1 | 1.0000 | -1.000 |
| 1.5 ATR | 1.19931 | hourly | 1.19931 | -1.000 | 7.27:1 | 1.0000 | -1.000 |
| 1.5 ATR | 1.19931 | **bound** | 1.16777 | **-20.100** | 7.27:1 | 1.0000 | **-20.100** |
| 2.0 ATR | 1.19876 | stop | 1.19876 | -1.333 | 5.45:1 | 1.0000 | -1.333 |
| 2.0 ATR | 1.19876 | hourly | 1.19876 | -1.333 | 5.45:1 | 1.0000 | -1.333 |
| 2.0 ATR | 1.19876 | **bound** | 1.16777 | **-20.100** | 5.45:1 | 1.0000 | **-20.100** |
| 3.0 ATR | 1.19766 | stop | 1.19766 | -2.000 | 3.64:1 | 1.0000 | -2.000 |
| 3.0 ATR | 1.19766 | hourly | 1.19766 | -2.000 | 3.64:1 | 1.0000 | -2.000 |
| 3.0 ATR | 1.19766 | **bound** | 1.16777 | **-20.100** | 3.64:1 | 1.0000 | **-20.100** |
| 31.0 ATR | 1.16683 | stop | 1.16683 | -20.667 | 0.35:1 | 1.0000 | -20.667 |
| 31.0 ATR | 1.16683 | hourly | 1.03592 | -99.949 | 0.35:1 | 1.0000 | -99.949 |
| 31.0 ATR | 1.16683 | **bound** | 1.03345 | **-101.444** | 0.35:1 | 1.0000 | **-101.444** |
| 50.0 ATR | 1.14592 | stop | 1.14592 | -33.333 | 0.22:1 | 1.0000 | -33.333 |
| 50.0 ATR | 1.14592 | hourly | 1.03592 | -99.949 | 0.22:1 | 1.0000 | -99.949 |
| 50.0 ATR | 1.14592 | **bound** | 1.03345 | **-101.444** | 0.22:1 | 1.0000 | **-101.444** |

**Three things to take from that table.**

1. **At a realistic stop the engine understates the loss by up to 20 times and the hourly path cannot prove it.** A 1.5 ATR stop books **-1.000 R**; the bound is **-20.100 R**.
2. **Where the gap IS resolvable the correction is enormous.** A stop below 1.16777 breaches in the 10:00 bar instead, whose open is 1.03592: at a 31 ATR stop **-20.667 R becomes -99.949 R**, and the bound is -101.444 R.
3. **The leverage cap is no protection against this.** That position is **7.3:1** at a 1.5 ATR stop — comfortably inside the 1:30 prop limit — so the cap scales it by 1.0000 and capped size EQUALS engine size. The cap limits how much you may hold. It does nothing about what a hole in the market does to what you are already holding.

## What it is worth on A, B and C

The candidates **as reported** — the walk-forward stitch, each step's settings picked on that step's own tuning years, trades taken only in that step's unseen trade year, floor 5%, peg guard X = 0.33, leverage cap on. Everything identical between the two rows except the fill rule.

| candidate | R total, old fill | R total, realistic | R/yr old | R/yr new | worst dip old | worst dip new | worst trade old | worst trade new | entries moved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A / jack | +40.030 | **+39.874** | +6.672 | **+6.646** | 22.616 | 22.616 | -1.496 | **-1.577** | 4 of 745 |
| A / textbook | -7.226 | **-7.802** | -1.204 | **-1.300** | 18.115 | 18.167 | -1.496 | **-1.577** | 21 of 551 |
| B / jack | +26.256 | **+23.934** | +4.376 | **+3.989** | 44.403 | 44.541 | -1.496 | **-1.577** | 20 of 1970 |
| B / textbook | -28.611 | **-30.870** | -4.768 | **-5.145** | 55.354 | 56.095 | -1.936 | **-2.014** | 78 of 2557 |
| C / jack | -46.652 | **-47.054** | -7.775 | **-7.842** | 69.497 | 69.858 | -1.496 | **-1.577** | 8 of 1657 |
| C / textbook | -12.367 | **-13.068** | -2.061 | **-2.178** | 36.658 | 36.953 | -1.496 | **-1.577** | 29 of 1673 |

| candidate | stop fills resolved, no gap | **resolved as GAPS** | unresolvable, daily rule kept | daily-open gaps |
|---|---:|---:|---:|---:|
| A / jack | 13908 | **204** | 306 | 210 |
| A / textbook | 5828 | **294** | 78 | 258 |
| B / jack | 40917 | **593** | 874 | 454 |
| B / textbook | 38173 | **1908** | 738 | 1920 |
| C / jack | 20945 | **248** | 414 | 195 |
| C / textbook | 14253 | **566** | 222 | 567 |

### The entries that moved most

| candidate | pair | entry | dir | exit | reason | old fill | new fill | R old | R new | dR |
|---|---|---|---|---|---|---:|---:|---:|---:|---:|
| B/jack | CHFJPY | 2015-01-15 | long | 2015-01-16 | stop | 135.60594 | 133.78900 | -0.683 | -1.115 | **-0.432** |
| B/jack | GBPCHF | 2015-01-15 | short | 2015-01-16 | stop | 1.30428 | 1.31902 | -0.681 | -0.997 | **-0.316** |
| B/jack | USDCHF | 2015-01-15 | short | 2015-01-16 | stop | 0.86074 | 0.86933 | -0.677 | -0.945 | **-0.268** |
| B/jack | NZDCHF | 2015-01-15 | short | 2015-01-16 | stop | 0.67394 | 0.68056 | -0.690 | -0.949 | **-0.259** |
| B/jack | AUDCHF | 2015-01-15 | short | 2015-01-16 | stop | 0.70885 | 0.71527 | -0.686 | -0.910 | **-0.225** |
| B/jack | CADCHF | 2015-01-15 | short | 2015-01-16 | stop | 0.72058 | 0.72673 | -0.684 | -0.902 | **-0.219** |
| B/textbook | NZDCHF | 2011-06-17 | long | 2011-06-27 | stop | 0.67312 | 0.67077 | -1.055 | -1.207 | **-0.153** |
| B/jack | EURNZD | 2011-08-08 | long | 2011-08-10 | trail stop | 1.71675 | 1.70915 | +0.313 | +0.197 | **-0.116** |
| B/jack | EURUSD | 2010-03-24 | short | 2010-03-29 | stop | 1.34640 | 1.34842 | -0.781 | -0.884 | **-0.103** |
| C/jack | CADJPY | 2015-06-25 | long | 2015-06-29 | stop | 99.45400 | 99.33700 | -0.760 | -0.860 | **-0.099** |

**7 of the 160 corrected entries were opened on 15 January 2015 itself**, and they are the six largest. The engine entered at the close of the de-peg day and was stopped out on the 16th, into a market that was still jumping — which is the case the old rule could not see, happening on the one day it mattered most.

## How often a stop-out exceeded 2 R and 5 R, by ATR decile at entry

The decile is the entry bar's own-pair causal ATR percentile — the same bucket the per-pair floor cuts into — and the loss is the whole ENTRY's net R at achievable size, both legs together, because that is the loss the account takes.

| decile | entries | losers | **worse than −2 R** | **worse than −5 R** | worst single entry, old fill | worst single entry, realistic |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 467 | 218 | **0** | **0** | -1.487 | -1.571 |
| 2 | 860 | 382 | **1** | **0** | -1.936 | -2.014 |
| 3 | 933 | 467 | **0** | **0** | -1.064 | -1.064 |
| 4 | 1213 | 576 | **0** | **0** | -1.061 | -1.061 |
| 5 | 1323 | 676 | **0** | **0** | -1.056 | -1.083 |
| 6 | 1264 | 621 | **0** | **0** | -1.256 | -1.256 |
| 7 | 1247 | 607 | **0** | **0** | -1.308 | -1.308 |
| 8 | 1041 | 576 | **0** | **0** | -1.211 | -1.229 |
| 9 | 643 | 341 | **0** | **0** | -1.039 | -1.039 |
| 10 | 162 | 71 | **0** | **0** | -1.025 | -1.025 |
| **all** | **9153** | **4535** | **1** | **0** | **-1.936** | **-2.014** |

**Essentially never — and that is not reassurance.** 1 of 9153 entries across the six cells lose more than 2 R with realistic fills (0 with the old rule), and **none** loses more than 5 R, in any decile. The reason is not that the stops held. It is that **the book was never long CHF into the de-peg.** The constructed trade above shows what the same mechanism is worth when the position is on the wrong side: −20 R at a normal stop, −100 R at a wide one. The empirical tail here measures the sample, not the exposure.

## The same three at default settings, as a larger sample

The stitch's BUILD window holds a few hundred entries per cell and a couple of hundred gap-resolvable stop fills. The same three combinations at DEFAULT settings over the whole span give four to six times the trades. Same direction, same size, nothing new — which is the point of running it.

| candidate | R total, old fill | R total, realistic | worst trade old | worst trade new | entries moved | gaps resolved |
|---|---:|---:|---:|---:|---:|---:|
| A / jack | -14.093 | -14.386 | -2.813 | -2.956 | 17 of 2103 | 24 |
| A / textbook | -7.193 | -7.792 | -2.813 | -2.956 | 42 of 1615 | 51 |
| B / jack | -43.372 | -45.920 | -2.813 | -2.956 | 50 of 4859 | 93 |
| B / textbook | -37.604 | -39.671 | -2.813 | -2.956 | 139 of 4633 | 201 |
| C / jack | -19.051 | -19.306 | -2.813 | -2.956 | 29 of 4307 | 49 |
| C / textbook | +0.431 | -0.283 | -2.813 | -2.956 | 68 of 4102 | 96 |

## What this does and does not settle

1. **Settled: the engine no longer books a fill at a price that was never quoted**, wherever an hourly path exists to prove it, and guard 41 will not let a Layer 2 table ship without it.
2. **Settled: it changes no verdict on A, B or C.** The largest correction to a candidate total is 2.322 R and the worst single trade gets about 5% worse. Nothing here rescues or kills anything.
3. **NOT settled: what a peg break actually costs a position on the wrong side of it.** Hour resolution cannot answer it for a normal stop. The bound is −20 R against an intended −1 R, the leverage cap does not touch it, and the only ways to close that gap are tick data for the event or a declared assumption. Jack's call.
4. **NOT settled: every stage table written before today ran on the old rule.** `results/nnfx/GAPFILL_STALE.md` names them and guard 41 fails if it goes missing. They are not being re-run to move a sub-1-R-a-year figure; the per-pair bank replaces them on the new rule from the start.

## Provenance

- `results/nnfx/snb_long_eurchf.csv` — 18 rows, md5 `a861ad543a2f`
- `results/nnfx/gap_fill_effect.csv` — 12 rows, md5 `35d09428d8fe`
- `results/nnfx/gap_fill_trades.csv` — 160 rows, md5 `3dddcee5bf30`
- `results/nnfx/gap_stopout_deciles.csv` — 120 rows, md5 `b026f78ade71`
- `results/nnfx/gap_fill_effect_defaults.csv` — 12 rows, md5 `2f3a3e161a20`
- `results/nnfx/gap_fill_trades_defaults.csv` — 345 rows, md5 `17713106deba`
- `results/nnfx/gap_stopout_deciles_defaults.csv` — 120 rows, md5 `3d926da0e03c`
