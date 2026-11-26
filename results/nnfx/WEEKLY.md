# WEEKLY — item 4

**Same protocol as amended.** Weekly bars resampled from the daily file, week ending Friday: open is the week's first open, high its max high, low its min low, close its last close. The final partial week of each series is dropped, because a bar built from two days of a five-day week is not a weekly bar. 834 weeks a pair, 52.2 a year.

**The one-bar lag is still one bar, which on weekly data means one WEEK.** That is no change in the code and a large change in the strategy, and it is the single most important thing about this file.

`PROTOCOL.md` A16 applies: the peg guard's cross-section is the world's own traded universe, here the same 28 pairs.

## Item 4's headline — gross edge per trade against cost per trade

| bars | trades | gross R/trade | cost R/trade | net R/trade | cost as % of gross | total net R |
|---|---:|---:|---:|---:|---:|---:|
| **daily** | 25178 | +0.01742 | 0.01789 | **-0.00048** | **102.7%** | -11.96 |
| **weekly** | 5013 | +0.02961 | 0.01796 | **+0.01165** | **60.7%** | +58.39 |

**This is the answer to item 4 and it is not a small one.** On daily bars the 18 declared algorithms earn a gross edge of **+0.0174 R a trade** and pay **0.0179 R a trade** in cost. **Cost is 103% of gross.** The strategies are not losing because they have no edge; they are losing because the edge is slightly smaller than the spread.

On weekly bars the **cost per trade is identical** — 0.0180 R, because a round trip costs the same spread whatever the bar — while the gross edge per trade is **70% larger** at +0.0296 R. Cost falls to **61% of gross** and net per trade goes from **−0.0005 R to +0.0116 R**. Total net R over the 1,008 sleeve-windows goes from **−11.96 to +58.39**.

Sixteen of 28 pairs are net positive per trade on both. Weekly takes **5,013** trades against daily's **25,178** — a fifth as many, for five times the net.

## And the amended admission test admits NOTHING on weekly bars

| bars | sleeve-windows | median trades | mean R per sleeve-window | share positive | admitted |
|---|---:|---:|---:|---:|---:|
| **daily** | 1008 | 18 | **-0.0119** | 0.469 | **11** |
| **weekly** | 1008 | 4 | **+0.0579** | 0.397 | **0** |

**Zero, and not because the system is worse.** Which of A2's three conditions binds:

| condition | daily passes | weekly passes |
|---|---:|---:|
| net R positive excluding its best day | 304 | 239 |
| at least 20 trades | 478 | 18 |
| best trade under a quarter of total | **11** | **0** |
| all three | 11 | 0 |

**The quarter rule is the binding test, and on weekly bars it is close to arithmetically unsatisfiable.** With n trades and positive total R, the best trade is at least R/n, so its share is at least 1/n. A share under 0.25 therefore **requires more than four trades even if every single one wins**. The median weekly sleeve-window takes **5** trades and its median best-trade share is **1.000** — one trade is the entire profit. **The smallest best-trade share across all 400 profitable weekly sleeve-windows is 0.263**, just above the cut. Not one can pass.

**The trade floor is not what blocks it.** Swept, as the standing rule requires:

| trade floor | daily admitted | weekly admitted |
|---:|---:|---:|
| 2 | 11 | 0 |
| 4 | 11 | 0 |
| 6 | 11 | 0 |
| 8 | 11 | 0 |
| 12 | 11 | 0 |
| 16 | 11 | 0 |
| 20 | 11 | 0 |
| 30 | 9 | 0 |
| 40 | 6 | 0 |

Weekly admits zero at **every** floor including 2. The share threshold is what moves it, swept here at a trade floor of 2:

| share threshold | weekly admitted |
|---|---:|
| 0.25 (declared) | 0 |
| 0.40 | 14 |
| 0.60 | 49 |
| 0.80 | 110 |
| 1.00 | 161 |
| off | 215 |

**This is reported, not acted on.** A2 is Jack's rule and the 0.25 threshold is his number; the measurement says it is a daily-bar number and that a weekly book cannot be built under it. Changing it is his call, not mine.

## What is NOT in this file

The **200,000-algorithm sample on weekly bars**, the **fit-carries test** and the **books under the five gates**. All three need a clear run at the machine, which three null workers hold until about 18:00. None is blocked on a decision: `nnfxweek.weekly_frames` feeds `set_world` and the declared bank ran clean on 1,008 sleeve-windows for each bar type.

**And one of them is blocked on Jack.** A weekly book under A2 as written would hold zero sleeves, so there is nothing to put the five gates on. The share threshold decides whether item 4 has a book at all.

## Provenance

- `results/nnfx/week/declared_bank.csv` — 2016 rows
- `results/nnfx/week/edge_vs_cost.csv` — 56 rows
- `results/nnfx/week/trade_floor_sweep.csv` — 9 rows
- `code/nnfxweek.py`; weekly bars resampled from `nnfx1.pair_data`
- costs `results/cost_table_h22.csv`, unchanged — which is the point
