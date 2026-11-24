# C1 — THE DATA REPORT: WHAT DAILY OHLC IS OBTAINABLE BEYOND FX

Generated 2026-11-24 10:40 by `code/l2data.py:yahoo_ohlc`, the fetcher this project already uses for `^GSPC`.


**Every row below was FETCHED TODAY, not quoted from memory.** The spans are what the endpoint actually returned.


## What is already on this disk

| path | what | span |
|---|---|---|
| `data/oanda_h1/` | OANDA **hourly bid and ask**, 28 FX pairs, 56 files, 453 MB | 2002-05-06 … 2026-09-07 |
| `data/oanda_ohlc/` | OANDA **daily OHLC** mid, 28 FX pairs | 2004-06-01 … 2026-08-14 |
| `data/px28.csv` | the daily close matrix the whole project runs on | 1999 … 2026 |
| `data/gspc.csv` | S&P 500 **close only**, no OHLC | 1996-12-09 … 2026-08-14 |

**No gold, silver, oil or crypto data exists anywhere in the repo.** `data/tv/` and `data/tv_oanda/` are TradingView *strategy-tester trade exports*, not price series, and are not a source for this.


## What is obtainable, measured today

| asset_class | ticker | description | rows | first | last | has_ohlc |
|---|---|---|---|---|---|---|
| gold | GC=F | COMEX gold future, front month | 6,585 | 2000-08-30 | 2026-11-24 | 1 |
| gold | XAUUSD=X | spot gold cross | 0 |  |  | 0 |
| silver | SI=F | COMEX silver future | 6,586 | 2000-08-30 | 2026-11-24 | 1 |
| oil WTI | CL=F | NYMEX WTI future | 6,593 | 2000-08-23 | 2026-11-24 | 1 |
| oil Brent | BZ=F | ICE Brent future | 4,811 | 2007-07-30 | 2026-11-24 | 1 |
| index S&P | ^GSPC | S&P 500 index | 9,292 | 1990-01-02 | 2026-11-23 | 1 |
| index Nasdaq | ^NDX | Nasdaq 100 index | 9,292 | 1990-01-02 | 2026-11-23 | 1 |
| index Dow | ^DJI | Dow Jones index | 8,786 | 1992-01-02 | 2026-11-23 | 1 |
| index DAX | ^GDAXI | DAX index | 9,337 | 1990-01-02 | 2026-11-24 | 1 |
| index Nikkei | ^N225 | Nikkei 225 index | 9,050 | 1990-01-04 | 2026-11-20 | 1 |
| crypto BTC | BTC-USD | Bitcoin in USD | 4,452 | 2014-09-17 | 2026-11-24 | 1 |
| crypto ETH | ETH-USD | Ether in USD | 3,303 | 2017-11-09 | 2026-11-24 | 1 |


`has_ohlc = 1` means open, high, low and close were all present and non-null. `XAUUSD=X` is the one failure: HTTPError from the endpoint.


## The three constraints that decide whether any of this is usable


### 1. History depth against the project's own split

The split is IS 1999-2015 / OOS 2016-2026, and every cut is learned on IS only. Measured against that:


| asset | first bar | IS years | OOS years | verdict |
|---|---|---:|---:|---|
| Indices — S&P, Nasdaq, DAX, Nikkei | 1990-01-02 | 26.0 | 10.9 | usable — longer history than the FX data itself |
| Dow ^DJI | 1992-01-02 | 24.0 | 10.9 | usable |
| WTI CL=F | 2000-08-23 | 15.4 | 10.9 | usable — 15 IS years |
| Gold GC=F | 2000-08-30 | 15.3 | 10.9 | usable — 15 IS years |
| Silver SI=F | 2000-08-30 | 15.3 | 10.9 | usable — 15 IS years |
| Brent BZ=F | 2007-07-30 | 8.4 | 10.9 | thin — 8 IS years, and adds nothing over WTI |
| BTC-USD | 2014-09-17 | 1.3 | 10.9 | **NOT TUNABLE** — 1.3 IS years |
| ETH-USD | 2017-11-09 | 0.0 | 9.1 | **NOT TUNABLE** — starts inside OOS |

**The crypto finding is the important one.** ETH's first bar is 2017-11-09, almost two years AFTER the split, so it has no IS at all; BTC has 1.3 years. Under this project's method **ETH cannot be tuned and BTC cannot be tuned honestly.** Either would need a different split, which would make its results non-comparable with everything else here. That is a design conclusion, not a data-quality complaint.


### 2. These are FUTURES, and futures roll

`GC=F`, `SI=F`, `CL=F` and `BZ=F` are **front-month continuous** series. At each roll the series jumps to a different contract, so a close-to-close return across a roll date is partly a contract change rather than a price move. For a trend system measured in ATR units that is not cosmetic — it manufactures gaps that look like breakouts.


Spot gold would avoid it, and **`XAUUSD=X` was the one ticker of the twelve that failed.** So the no-roll route for gold is not available from this endpoint and needs another source.


The indices are index levels, so they have no roll problem — but they also cannot be traded directly, and the tradable instrument (a future or CFD) has its own roll and financing.


### 3. COSTS ARE NOT OBTAINABLE FROM THIS SOURCE, AND THAT IS THE BLOCKER

This project charges costs from `results/cost_table_h22.csv`, built from **OANDA hourly bid/ask at a stated hour, per pair, per era** — a measured two-sided spread. The Yahoo v8 endpoint returns **mid OHLC only**: no bid, no ask, no spread, in anything fetched above.


So for every instrument in the table: **the price history is in hand and the cost is not.** A result on gold or oil costed by a guessed spread would not be comparable with any FX result in this repo, and the method invariant — costs from the measured table — would be broken.


**What it would take to close the gap**, cheapest first:

1. An **OANDA v20 account and API token.** OANDA quotes spot gold (`XAU_USD`), silver (`XAG_USD`), WTI (`WTICO_USD`), Brent (`BCO_USD`) and the major index CFDs two-sided, on the same hourly basis as the FX data already here, so the identical `spread_by_hour` method would apply unchanged. **There are no OANDA credentials on this machine** — no `~/.oanda*` file and no OANDA environment variable — so this needs Jack. The exact instrument names and history depth should be confirmed against the account rather than taken from me.

2. A **broker spread schedule**, which gives a headline figure but not the by-hour and by-era structure the FX table has.

3. **Nothing** — and restrict non-FX work to effect measurement that never nets a cost, the way C3 reports gross and net side by side and claims nothing tradable.


## Recommendation

**Indices first, if anything.** 26 years of IS history, more than the FX data itself, no roll problem in the index level, deepest liquidity. Gold and WTI second, 15 IS years each with a roll that must be handled explicitly. Brent adds nothing over WTI. **Crypto should not be attempted under this method at all**, regardless of cost data.


And none of it should start before the cost question is settled, because the cost table is the one thing standing between this project and the over-fitting Layer 2 spent itself learning to detect.


## Provenance

- `results/r2reads/c1_data_availability.csv` — 12 rows fetched 2026-11-24, md5 `baef34b53541`
- fetcher `code/l2data.py:yahoo_ohlc`, the Yahoo v8 chart endpoint, unchanged from what built `data/gspc.csv`
- 11 of 12 candidate tickers returned full daily OHLC; `XAUUSD=X` returned HTTPError
