# EVERY NNFX-PHASE NET FIGURE IS CHARGED TWICE THE MEASURED SPREAD

**Found 25 November 2026, 15:1x EST, building `code/nnfxproto.py` for Jack's new protocol.
Confirmed two ways. Fixed in the protocol path. NOT retro-applied to the existing tables —
that is Jack's call, and this file is what it would be called on.**

## The fault, in three lines

`l2engine.run` has `risk_dollars=200.0` as its default. **Every `nnfx*` caller takes that
default**, so the engine's raw `r` is (price move x units) / **200**. But `nnfx1._cost_R`
divides by `l2sweep.RISK`, which is **100**. Numerator and denominator are in different
units, and the cost comes out **exactly 2x too large**.

## Confirmed two ways

**1. From the engine, by measurement.** On 80 stop exits of a complete candidate on three
pairs, the booked leg R is exactly `-0.5`. Reconstructing it as
`direction x (exit_px - entry_px) x units / 200` reproduces `-0.5` to 0.0 exactly;
`/ 100` gives `-1.0`. So the R unit is 200 dollars, not 100.

**2. From two independent code paths disagreeing.** `nnfxproto.fast_obj` (numpy, realised by
exit day) and `nnfxproto.run_candidate` + `score` (pandas, mark-to-market) were built to
compute the same realised net R. They disagreed by exactly the charged cost, on every
candidate tested:

| candidate | fast | full | difference | legs |
|---|---:|---:|---:|---:|
| ichimoku / vortex / variance / sma / ssl | −0.928 | −3.596 | 2.668 | 354 |
| aroon / kalman / volratio / ema / aroon | −4.029 | −13.778 | 9.750 | 1062 |
| stc / vortex / damiani / mcginley / supertrend | +7.585 | +2.420 | 5.165 | 650 |

The gross sums agreed to the last decimal (1.7394 against 1.7394 on the first). Only the cost
differed, and it differed by a factor of exactly 2.000. With the divisor corrected the two
paths agree to **2.2e-16** on plan 2 and **2.2e-15** on plan 1.

## The gauntlet path is NOT affected

`l2sweep.run_combo` passes `RISK` straight through to `run_bars` as `risk_dollars`
(`l2sweep.py:339`) and its `_cost_R` divides by the same `RISK`. Engine and cost divisor are
the same number there, so the gauntlet, gate 1, gate 2, gate 3, the r2 book and the null
machinery are all internally consistent. **The mismatch exists only where a caller takes
`l2engine.run`'s default and then charges `nnfx1._cost_R`.** That is the whole `nnfx*` family
and nothing else.

`nnfxvol.py:336` already knew the engine risks 200 — the leverage cap's `EQUITY = 10000` was
calibrated against it. So the project had the right number in one place and the wrong one in
another, which is exactly how a factor of two survives for weeks.

## The direction is PESSIMISTIC

Every affected figure is **too low**, never too high. Nothing that was reported as working
was really failing; things reported as failing may be less bad than reported.

## The mechanical correction

Each stage table already reports `cost_per_trade`. The corrected total is

> **R_corrected = R_reported + (cost_per_trade / 2) x trades**

| candidate | reported R | cost/trade | true cost/trade | correction | corrected R | change |
|---|---:|---:|---:|---:|---:|---:|
| **A** ichimoku+sma full_nnfx, 742 trades | +39.874 | 0.03279 | 0.01640 | **+12.166** | **+52.040** | **+31%** |
| **B** stc+sma side_xentry, 1957 trades | +23.934 | 0.02777 | 0.01389 | **+27.174** | **+51.108** | **+114%** |

**This is an approximation and is labelled one.** It corrects the total exactly, but the
drawdown path changes too, so `dip_binding`, `R_per_dip`, the prop scaling and every t
statistic have to be RE-RUN, not adjusted. A candidate whose cost correction lands in a
drawdown window gains more than its total suggests; one whose correction lands on good days
gains less.

## What it does and does not change

1. **Item 5's verdict survives in direction.** The best book was 1.135% a year against a 12%
   target. A 31% improvement on A takes that to roughly 1.5%, so the gap goes from a factor of
   10.6 to about a factor of 8. **Still a return problem, not a sizing problem.**
2. **Item 2d's floor cost roughly halves in R terms** but not in sign: the 5% floor cost A
   12.553 R with a doubled charge, and removing the floor adds trades, so the corrected figure
   needs the re-run rather than an adjustment.
3. **Item 1's gap-fill effect is unaffected in kind** — it is a difference between two runs
   charged the same way.
4. **Every "fails" verdict stays a fails verdict on the gates that are not cost-sensitive** —
   G2 (one event), G3 (hold-out sign), the shuffle and label nulls. Cost moves levels, not the
   shape of a null comparison where both arms are charged the same.

## The tables that carry the doubled charge

Every `results/nnfx/*.csv` and `results/nnfx/*.md` written before 25 November 2026 15:00 EST
whose numbers come through `nnfx1._cost_R`, which is all of them except the three gap-fill
measurement files that report engine counts rather than R:

`stage1_*`, `stage1r2_*` (all 62), `stage2_*` (all), `stage3_*`, `atr_buckets_*`,
`floor_curve_*`, `pegguard_*`, `quiet_*`, `per_pair_bank*`, `pair_groups*`, `group_*`,
`mr_*`, `book_*`, `dd_*`, `exit_grid.csv`, `market_switch_*`, and the documents written from
them: `STAGE1.md`, `STAGE1_R2.md`, `STAGE2.md`, `STAGE3.md`, `QUIET_ENTRY.md`,
`PER_PAIR_BANK.md`, `PAIR_GROUPS.md`, `MEAN_REVERSION.md`, `BOOK.md`, `EXITS.md`,
`SPEEDS.md`, `DRAWDOWN.md`, `GAP_FILLS.md`, `RISK_PLANS.md`, `MARKET_SWITCH.md`.

**They are not edited and not deleted.** They are the record of what was computed. This file
is the correction, and `nnfxproto.cost_R` is the fix going forward.

## What is fixed, and the guard

`code/nnfxproto.py` declares `RISK_DOLLARS = 200.0`, **passes it explicitly on every engine
call** so the two can never drift apart again, and charges `nnfxproto.cost_R`, which divides
by it. Preflight **guard 42** fails if `nnfxproto` stops passing `risk_dollars`, if `cost_R`
stops dividing by `RISK_DOLLARS`, or if `verify_fast` on a live candidate does not agree to
1e-6.

**Jack's call:** whether to re-run the stage tables and items 1 to 6 under the corrected
charge. It is about 6 hours of compute. The protocol's own candidates are all computed
correctly from the start, so nothing in the new work is waiting on it.
