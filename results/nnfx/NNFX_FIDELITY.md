# 0c — NNFX FIDELITY AUDIT

Generated 2026-11-24 12:06. HANDOFF 0m. **Report only — nothing was changed.**


Every row below was checked against `code/l2engine.py` and `code/l2sweep.py`, not from memory. "Where" gives the parameter or array in `l2engine.run_bars`.


## The canonical rules, one by one

| # | canonical rule | implemented? | where | default in use | cost to add / switch |
|---|---|---|---|---|---|
| 1 | Entry on baseline cross with C1 agreeing | **YES** | `use_base_cross` | `True` | already switchable — none |
| 2 | Entry on C1 flip with price on the right side of the baseline | **YES** | `use_c1_flip` | `True` | already switchable — none |
| 3 | No entry when price is more than 1 ATR from the baseline | **YES, but loose** | `max_atr_dist` | **`1.5`** | none to switch; **the default is 1.5 ATR, not the canonical 1.0** |
| 4 | Bridge too far — C1 signal 7 or more bars old | **YES** | `bridge_bars` | `7` | none — default is canonical |
| 5 | One-candle rule | **YES, but off** | `one_candle_rule` | **`False`** | none to switch; **it has never been on** |
| 6 | Pullback rule | **NO** | — | — | **engine change**: defer an entry until price returns inside X ATR of the baseline. A new parameter plus bar-loop state, an njit recompile, and a re-tune. Moderate. |
| 7 | Continuation trades | **YES** | `use_continuation` | `True` | already switchable — none |
| 8 | C2 agreement | **YES** | `c2_lc`/`c2_sc` arrays | active | pass all-True arrays to disable — none |
| 9 | Volume gate | **YES** | `v_ok_l`/`v_ok_s` arrays | active | pass all-True arrays to disable — none |
| 10 | 1.5 ATR stop | **YES, but wrong size** | `atr_mult` | **`1.0`** | none to switch; **the default stop is 1.0 ATR, not 1.5** |
| 11 | Half off at 1 ATR, stop to breakeven, trail the rest | **PARTLY** | `plan=2`, `tp_mult`, `be_pct`, `trail_start_mult`, `trail_mult` | `plan 2`, 50/50, leg-1 target `1.5x` the stop, BE at `0.05`, arm `2.0`, trail `1.5` | **the structure is there; the first target is at 1.5x the stop, i.e. 1.5 ATR, where canonical takes half off at 1 ATR.** Changing it is a parameter, not code. |
| 12 | Exit by exit indicator, C1 flip or baseline cross | **YES, all three** | `exit_on_exit_ind`, `exit_on_c1_flip`, `exit_on_base_cross` | **one at a time — see below** | none to switch; **no mode ever runs more than one** |
| 13 | Risk halved when two trades share a currency | **NO** | — | — | **structural.** `run_bars` runs one pair in isolation and has no view of concurrent positions, so this cannot be a `run_bars` flag. It needs a portfolio pass over the trade list after the fact, or a rewrite to a cross-pair loop. Expensive. A *related* control exists at book level: `l2walkfwd.Book.series(cap_pct=...)` caps net exposure per currency, standing value 2.0 — but it caps the book, it does not halve a trade. |
| 14 | No entry before major news | **NO** | — | — | **cheap.** `code/events.py` already holds a news-sourced, date-sorted, duplicate-free calendar, and its dates come from announcements rather than price. A per-pair per-bar blackout mask passed in as an entry filter would do it. The hard part is not the code, it is that the calendar covers crisis events, not the routine high-impact releases this rule means. |
| 15 | A market-wide volatility floor | **NO** | — | — | **cheap-ish.** Nothing in the repo implements it. But Layer 1 already publishes `activity` and `scale_28` per pair per day, so a cross-pair floor could be precomputed into a per-day mask and passed as an entry filter without touching the bar loop. 2a measures whether such a panel measure relates to P&L at all before anything is built. |

## Summary

**11 of 15 canonical rules are implemented and switchable. 4 are not: the pullback rule, the news blackout, shared-currency risk halving, and a market-wide volatility floor.** Of the four, only shared-currency risk halving is structurally hard — the other three are a mask or a parameter.


**Three implemented rules are set to non-canonical values**, which matters more than the four missing ones because they are silently wrong rather than absent:


| rule | canonical | in use | direction of the error |
|---|---|---|---|
| distance from baseline | 1.0 ATR | **1.5 ATR** | **more permissive** — takes entries canonical NNFX refuses |
| stop | 1.5 ATR | **1.0 ATR** | **tighter** — more stop-outs, and it inflates R per trade, which is the exact fault `ACCT_OBJECTIVE` was added to neutralise |
| first target | 1.0 ATR (half off) | **1.5 ATR** | **later** — banks less early, runs more |
| one-candle rule | on | **off** | **more permissive** |

## How modes A, B and C differ from canonical

**Canonical NNFX exits on whichever comes first: the exit indicator, a C1 flip, or a baseline cross. All three are live at once.** The three modes each enable exactly one:


| mode | `exit_on_c1_flip` | `exit_on_base_cross` | `exit_on_exit_ind` | exit slot used |
|---|---|---|---|---|
| **A** | **True** | False | False | no |
| **B** | False | **True** | False | no |
| **C** | False | False | **True** | yes |
| canonical | True | True | True | yes |
| `l2engine.run()` default | False | True | True | yes |

**So no mode on record is canonical, and none of them is even the engine's own default.** Each mode is a deliberate single-exit variant, which was the right call for isolating the exit's contribution — HANDOFF records that the exit slot was being scored on what the baseline left behind, which is why its enrichment was flat — but it means **every Layer 2 result to date is for a strategy that exits on one condition where NNFX exits on three.**


The practical consequence: a mode A trade runs until C1 flips even if price has crossed back through the baseline, and a mode B trade runs through a C1 flip. Canonical would have closed both earlier. Holding periods in every Layer 2 result are therefore longer than canonical, and the exposure to a reversal is larger.


## What this means for the staged build

1. **Stage 1 is unaffected** — it runs one piece alone, with no exit indicator and no baseline, so the mode question does not arise yet.

2. **The three wrong defaults should be corrected to canonical as the starting point of the build**, not tuned away from it. They are parameters, so this costs nothing but a declaration.

3. **A canonical multi-exit mode (call it mode N) should be added** as a fourth entry in `l2sweep.MODES` with all three exits True. It is a three-line change and it makes the canonical algorithm expressible at all, which it currently is not.

4. **Shared-currency risk halving should be deferred**, not dropped: it is the only structurally expensive rule, and the book-level currency cap already measured in `A4_NETTING.md` does a related job. A4 found the cap makes almost no difference to return over drawdown, which is weak evidence that the trade-level version would not either.


## Provenance

- `code/l2engine.py` — md5 `78d7ee2086c9`
- `code/l2sweep.py` — md5 `1b4000fd0ac0`
- defaults read from `l2engine.run()` and the `GAUNTLET.md "RISK"` block of `l2sweep.py`; mode table from `l2sweep.MODES`
