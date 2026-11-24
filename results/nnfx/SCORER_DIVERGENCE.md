# 0b — ONE SCORER: WHY GATE 2 AND GATE 3 DISAGREE, AND WHICH IS RIGHT

Generated 2026-11-24 12:05. HANDOFF 0m. **Report only — nothing is regenerated.**


## The cause, in one sentence

**Gate 2 marks every trade to market at each year end; gate 3 books each whole trade to the year it was entered.**


`l2r2gate2._year_marks` splits a trade into per-bar increments and attributes each increment to that bar's own calendar year. `l2tune.Scorer.score` buckets by `entry_bar` into whole-window buckets, so a trade entered on 19 December 2018 and closed on 3 January 2019 is booked entirely to 2018.


## The trade-level example

Winner 1 (`lemantrend | hieken_ashi_smoothed | chaikin_volatility | alma | adx_dmi`, trend-allon), configuration 227:

```
AUDCAD  entry 2018-12-19  exit 2019-01-03   9 bars   R = +0.7500
   gate 3 (entry-year)  : all +0.7500 R booked to 2018, trade counted in 2018
   gate 2 (year-end MTM): the bars to 31 Dec score in 2018, the rest in 2019,
                          and the trade is counted in BOTH years
EURCAD  entry 2017-12-21  exit 2018-01-05   9 bars   R = +0.7500
EURCAD  entry 2017-12-21  exit 2018-01-09  11 bars   R = +1.0771
```

## The reconciliation — both conventions reproduce exactly

Recomputing winner 1 from a single trade list, applying each convention by hand:


| trade year | entry-year R | n | `winners.csv` (gate 3) | year-end MTM R | n | gate 2 bank |
|---:|---:|---:|---|---:|---:|---|
| 2016 | **16.510** | 256 | ✓ 16.510 | **13.812** | 262 | ✓ 13.812 |
| 2017 | **19.041** | 144 | ✓ 19.041 | **17.462** | 144 | ✓ 17.462 |
| 2018 | **51.546** | 164 | ✓ 51.546 | **51.399** | 166 | ✓ 51.399 |
| 2019 | **27.569** | 142 | ✓ 27.569 | **29.295** | 144 | ✓ 29.295 |
| 2020 | **13.121** | 110 | ✓ 13.121 | **13.121** | 110 | ✓ 13.121 |

**Every figure reproduces to three decimals under the convention claimed.** There is no bug in either scorer. There are two conventions, both internally consistent, and nothing declared which one the project uses.


## Which is right

**For R per year: GATE 2.** The project's own declared rule — in HANDOFF and restated in 0m — is **year-end mark to market**. Gate 2 implements it; gate 3 does not. Gate 2's convention also has the property that summing a trade's increments reproduces its R exactly, which is what condition 1 tests and passes at 8.88e-16.


**For the count of distinct trades: GATE 3.** Gate 2 counts a straddling trade in *every* year it touches, so summing gate 2's per-year `n` over-counts: 262 in 2016 against 256 trades actually entered. Gate 3's `n` is entries in the year and sums to the true total.


**So the two columns both labelled `n` mean different things, and neither file says so.** That is the real defect: not an arithmetic error but an undeclared convention, in two places, with the same column name.


## Three paths, not two

| path | convention | used by |
|---|---|---|
| gate 2 `win` array (`_year_marks`) | **year-end MTM** | `l2r2gate2`, `r2reads` (A1, A1b, A2, A3), `l2r2top30`, `b1narrow` (B1-winners) |
| gate 3 KPI bank `K` (`Scorer.score`) | **entry-year** | `l2r2winners` only — but that writes `mode?_winners.csv` |
| gate 3 book path (`marks_of` → daily series) | **daily marks, so MTM-consistent** | `l2r2gate3` books, `l2r2kpis` (MODEA_KPIS.md), A4 |

**Only one of the three is on the entry-year convention**, and it is the one that selected the winners.


## Every file on record built on the entry-year convention

| file | what it would change | could the conclusion change? |
|---|---|---|
| `results/r2gate2/mode?_winners.csv` | every `R_<year>`, `n_<year>`, and the aggregates built from them | **YES — see below** |
| `results/r2gate2/MODEA_WINNERS.md`, `MODEB_WINNERS.md` | the per-year tables, yearly t, years-positive, the luck-floor comparison | **YES** |
| `results/r2gate2/WINNERS_BY_PAIR.md` | it reads `mode?_winners.csv` to pick its winners | only if the winner SET changes |
| `results/r2reads/A6_PROPSIM.md` | the 8-winner book it simulates is the winner set | only if the winner set changes |
| `results/nnfx/POWER_TEST.md` (0a) | **no** — it uses the null re-runs, not either scorer | no |
| `MODEA_KPIS.md`, `MODEA_PASSERBOOKS.md`, `A4_NETTING.md` | **no** — book path, daily marks | no |
| `A1_SLOTS.md`, `A1B_WALKFORWARD.md`, `A2_A3_*.md`, `B1_WINNERS.md`, `B1_NARROW.md` | **no** — gate 2 bank | no |

### Could the conclusions change? Measured, not guessed

Over the 50 winner-years: **41 of 50 per-year R values differ** by more than 1e-6, median |ΔR| **1.0096 R**, largest **10.6274 R**; **35 of 50 trade counts differ**, by up to **11**; and **1 winner-year flips sign** (mode A 2020: −0.323 under MTM, +0.845 under entry-year).


Per winner, the statistics the selection actually used:

| mode | winner | t_gate2 | t_gate3 | t_delta | yrs_pos_gate2 | yrs_pos_gate3 | R5_gate2 | R5_gate3 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 1 | 3.472 | 3.692 | 0.220 | 5 | 5 | 125.089 | 127.786 |
| A | 2 | 4.033 | 3.993 | -0.040 | 5 | 5 | 139.446 | 148.330 |
| A | 3 | 3.162 | 3.329 | 0.167 | 5 | 5 | 104.425 | 109.410 |
| A | 4 | 3.412 | 3.241 | -0.171 | 5 | 5 | 114.931 | 125.673 |
| A | 5 | 3.247 | 3.313 | 0.066 | 4 | 4 | 127.508 | 125.407 |
| A | 6 | 3.633 | 4.032 | 0.398 | 4 | 5 | 98.510 | 106.085 |
| A | 7 | 4.276 | 4.081 | -0.195 | 5 | 5 | 118.255 | 120.701 |
| A | 8 | 2.063 | 2.157 | 0.094 | 4 | 4 | 116.514 | 121.112 |
| B | 1 | 4.116 | 5.033 | 0.917 | 5 | 5 | 92.237 | 93.425 |
| B | 2 | 2.640 | 3.038 | 0.399 | 5 | 5 | 98.161 | 100.690 |


**Yes, the winner set could have been different.** Two specific ways:


1. **Mode B winner 1's yearly t moves from 4.116 to 5.033** — a shift of +0.917 against a floor that was set at 5.08. Under one convention it fails clearly; under the other it is at the bar. Any floor in that region is decided by the convention, not by the strategy.


2. **Mode A winner 6's years-positive moves from 4 to 5**, and the old route required *4 of 5 years positive*. A strategy sitting on that boundary passes or fails on the convention alone.


The five-year total R moves by up to **+10.7 R** (mode A winner 4: 114.9 under MTM, 125.7 under entry-year). Directions and signs are otherwise stable, so the broad conclusion of `MODEA_WINNERS.md` — that the winners are not distinguishable from luck at a best-of-field floor — does not reverse. **But the membership of the list is not safe, and any result that turns on a threshold near t 5 is not safe.**


## What the staged build uses

**Gate 2's year-end mark to market, for R.** It is the declared rule, it is what condition 1 verifies, and it is what two of the three paths already do. Where a count of distinct trades is wanted, it must be counted by entry year and **labelled differently from the per-year `n`** so the two can never be confused again.


## Recommended fixes, not applied here

1. Rename the columns so the convention is in the name: `R_<year>_mtm` and `n_<year>_touching` for gate 2; `n_<year>_entered` for entry-year counts. Cheap, and it makes the defect impossible to repeat.

2. Make `Scorer.score` capable of per-bar year attribution, so gate 3's KPI bank can be rebuilt on the declared convention. That is a change to what is computed and needs Jack's approval, plus a rerun of gate 3 scoring.

3. Add a preflight guard asserting the two paths agree on a sample, once they are meant to.


## Provenance

- `results/r2gate2/gate2_vs_gate3_peryear.csv` — 50 rows, md5 `d046fa9a2f0c`
- `results/nnfx/scorer_consequence.csv` — 10 rows, md5 `7510182f9766`
- cause located at `code/l2r2gate2.py:_year_marks` (per-bar increments) and `code/l2tune.py:Scorer.score` (`eb`-bucketed windows)
