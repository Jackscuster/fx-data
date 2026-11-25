# PROTOCOL — the one fixed test for a complete NNFX algorithm

**Declared by Jack, 25 November 2026. Written before any candidate was scored. It is not
changed without Jack. HANDOFF §0o.**

Layer 1 is removed from Layer 2 for now. **No regime input gates, sizes or labels anything
in this protocol.** Nothing here reads a state, a label or a regime file. Where an earlier
stage used one, that stage is not evidence for anything in this document.

The job is narrow: **find complete, working NNFX algorithms**, under one protocol that every
candidate from every source passes through unchanged.

---

## 1. What a candidate is

A candidate is a **complete algorithm**, never a slot or a pair of slots. Ten declared
choices plus a fixed risk plan:

| part | choice |
|---|---|
| C1 | one of 39 confirmation indicators, at one of its settings |
| C2 | one of 39 confirmation indicators, at one of its settings |
| volume | one of 12 volume / volatility filters, at one of its settings |
| baseline | one of 15 baselines, at one of its settings |
| exit indicator | one of 39 exit helpers, at one of its settings |

All five slots are **live**. No slot is neutralised, forced true, or blanked. This is the
first protocol in the project where that is so: stage 1 neutralised four slots to isolate
one, and stage 2 neutralised C2, volume and the exit indicator to isolate the baseline. Both
were deliberate and both are therefore **not** tests of a complete algorithm. Their numbers
do not transfer here and are not quoted as if they did.

**The three exits are all live**: C1 opposite flip, baseline cross, and the exit indicator.

**The settings ladder** is the project's standing one — `half`, `default`, `double` of the
indicator's own length knob (its Pine default), where `half` is the shorter memory. Five
confirmation indicators are parameterised by a smoothing *constant* instead of a length
(`ehlers_reverse_ema`, `kalman_filter`, `laguerre_filter`, `mama_fama`, `parabolic_sar`); for
those a **larger** constant is a **shorter** memory, so `half` doubles the constant. Two
baselines default to length 2 (`fantail_vma`, `vidya`), where `half` collapses onto
`default`, so they carry two distinct settings and not three.

### The risk plan, fixed, Jack's

| knob | value |
|---|---|
| stop | **1.0 ATR** |
| first target | **1.5 x the stop** |
| baseline distance | **1.5 ATR** — no entry further than that from the baseline |
| bridge too far | **7 candles** — a baseline-cross entry needs a C1 signal under 7 bars old |
| continuation entries | **on** |
| one-candle rule | off |
| trail | arm at 2.0 ATR, trail 1.5 ATR |
| breakeven | 5% of price beyond target 1 |
| plan | 2 — two legs, half off at target 1 |
| ATR length | 14 |
| time stop | **off** |

**Every setting is fixed and written to the ledger BEFORE the candidate is scored.** A
candidate whose settings were not in the ledger before its result existed is not a candidate;
it is a search output, and it goes through Source 3's search null instead.

> **One flag, not a change.** Item 6a's exit factorial (576 cells, landed 25 Nov 12:25 EST)
> found that a **time stop** raises return per dip consistently across its whole range on both
> tested members — A 0.865 / 1.316 / 1.339 / 1.603 for off / 5 / 10 / 20 bars, B 0.283 / 1.137
> / 0.352 / 0.391 — and that **trail on** beats trail off on both. The plan above keeps the
> time stop OFF because that is what Jack declared. This is recorded so the choice is visible,
> not argued. Jack decides whether the plan changes; if it does, the protocol changes with it
> and every candidate re-runs.

---

## 2. Engine standing rules — unchanged, all of them

| rule | value |
|---|---|
| lag | every signal shifted one bar, `.shift(1)`. Non-negotiable. |
| costs | era-correct, from `results/cost_table_h22.csv` — 28 pairs, 28 distinct costs, median 2.4 bp round trip. Never one spread across 28 pairs. |
| leverage cap | **1:30 on all open positions summed**, sequential and causal; a new entry is scaled down to fit, never skipped, and a position already open is never resized. |
| peg guard | **X = 0.33** — no new entry while this pair's lagged ATR/price is below 0.33 x the 28-pair median of the same lagged quantity that day. Decided 25 Nov. |
| per-pair floor | **5%** — no new entry while the pair's own ATR is in its bottom 5%. Jack's rule 1, standing. Item 2d measured that it costs candidate A 12.553 R and 30% of its return per dip; it is unchanged because Jack has not changed it. |
| gap fills | **realistic**, standing from 25 Nov: every stop fills at the first tradable hourly bid/ask price at or beyond it, with the pair's own round-trip cost as the spread tolerance. Preflight guard 41 fails if this is off. |
| zero-edge check | every batch is accompanied by its null (section 4). |
| feed | OANDA daily mid, `data/oanda_ohlc`; hourly bid/ask from `data/oanda_h1` for gap fills and ambiguity. |

**The floor, the peg guard and the real volume indicator all ride the volume slot together.**
`v_ok_l` / `v_ok_s` appear only in the engine's entry conditions, so all three compose as
`volume_indicator AND NOT floor AND NOT peg_guard` and none of them can freeze an exit. This
is the one place where the protocol's "no slot is neutralised" and Jack's standing rules meet,
and the composition is an AND, not an override.

---

## 3. Years

| window | use |
|---|---|
| **2005 to 2015** | **the evidence. All eleven years are unseen, because nothing is tuned.** Every reported figure is this window. |
| 2016 to 2020 | computed and stored. **Not reported.** Not opened until Jack calls a confirm. |
| 2021 onward | **sealed.** Not read. |

A fixed setting needs no tuning years, so there is no walk-forward stitch in this protocol and
no step boundary. That is the point of fixing everything in advance: the whole eleven years are
a hold-out. Source 3 is the exception and has its own split (section 6).

---

## 4. The four gates — pass or fail, no weighting

The gauntlet is **sequential elimination, not a weighted composite**. A candidate does not
offset a failed gate with a strong one. A **passer clears all four**.

### G1 — LUCK
**Block-bootstrap t on the daily mark-to-market P&L above the floor for its batch**, where the
floor is taken from **the batch's own null**, not from a table and not from a formula.

- the statistic: moving-block bootstrap, 20-day blocks, 2,000 draws, t = observed mean divided
  by the bootstrap standard deviation of the mean. 20-day blocks keep the autocorrelation
  inside a block; an iid t on a daily series would be wildly overconfident.
- the floor: the **95th percentile of the same statistic under the batch's null**, corrected
  for the batch's size. A batch of 6 (Source 1) gets a best-of-6 floor; a batch of N hand-built
  candidates gets a best-of-N floor; Source 3 gets its own search null, which is a different
  and much harder object (section 6).
- each source states which null it used and what the floor came out at.

### G2 — ONE EVENT
**Total R stays positive with the best day removed, and with the best 5 days removed. The best
single trade is under a quarter of total R.**

Three numbers, all three must hold. This is the gate the 2015 SNB de-peg exists to break: a
candidate whose whole result is one day is not an algorithm.

### G3 — HOLD-OUT
**Positive in 2005-2010 and in 2011-2015 separately, and positive on each side of three
currency splits.**

The three splits, each run both ways — the pairs containing **neither** held-out currency
against the pairs containing **either**:

| split | held out |
|---|---|
| 1 | JPY + CHF |
| 2 | AUD + NZD |
| 3 | GBP + CAD |

Eight sub-results in all (two time halves, six currency sides). All eight must be positive.
This is the gate that asks whether the result is the whole 28-pair cross-section or two pairs
and a crisis.

### G4 — NUDGE
**Still positive with each numeric setting moved one grid step down and one step up, one at a
time.**

The grid, declared here:

| knob | one step down | one step up |
|---|---|---|
| each slot's own length knob (5 of them) | x 0.5 | x 2 |
| ATR length | 7 | 28 |
| stop | 0.75 ATR | 1.25 ATR |
| first target | 1.0 x stop | 2.0 x stop |
| baseline distance | 1.0 ATR | 2.0 ATR |
| bridge too far | 5 candles | 9 candles |

**The steps are deliberately coarser than `l2tune`'s GAUNTLET grids** (stop step 0.05, target
step 0.05). A 0.05 nudge on a 1.0 ATR stop tests nothing and would pass by construction. These
steps are large enough that passing them is information.

20 runs per candidate (10 knobs, 2 directions). Every one must come out positive on total R
over 2005-2015. The report gives the **worst** nudge, so a near-miss is visible rather than
hidden behind a pass.

---

## 5. The report, for every candidate, every source

| column | meaning |
|---|---|
| G1 G2 G3 G4 | pass / fail each |
| `R_gross_per_trade`, `R_net_per_trade` | gross and net, in the 1.5-ATR unit |
| `trades_per_year` | |
| `R_per_year` | net, over 2005-2015 |
| `dip_true`, `dip95`, `dip_binding` | realised chronological drawdown; 95th percentile over shuffled day orders; **the maximum of the two** |
| `R_per_dip` | total R over the binding dip |
| `t_yearly`, `t_block_boot` | both t statistics |
| `R_ex_best_day`, `R_ex_best5_days`, `best_trade_share` | G2's three numbers |
| per-pair table | 28 rows, per pair and per direction |

**`dip_binding` is the maximum of the realised dip and DIP95, not one or the other.** DIP95 can
sit above or below the realised dip; on the eight sleeves of item 5 it was **above on all eight,
by 1.22x to 2.36x**. Taking the maximum is the rule; assuming which one is larger is not.

Every figure is **net**, in **R per 1.5 ATR**, at **capped size**, with **year-end mark to
market**. Where a number is not computed that way the row says so.

### One declared departure, and it is a ranking shortcut only

Source 3 evaluates hundreds of thousands of candidates. The full reporting path costs ~70 ms a
candidate (trade frame, leverage cap, mark-to-market daily series); the engine's bar loop costs
~1.2 ms. So **the search's objective is computed on a numpy fast path**: realised net R
attributed to each trade's exit day, no leverage cap. **Every reported figure and every gate,
for every candidate the search surfaces, is recomputed on the full standing path.** The rank
correlation between the fast objective and the full one is measured on a sample and reported in
SOURCE3.md; if it is not high, the shortcut is withdrawn and the search budget is cut instead.
The shortcut never touches Source 1 or Source 2, which are small enough to run full.

---

## 6. The three sources, and what null each one is judged against

A candidate's floor depends on how it was found. That is the whole reason there are three
sources rather than one list.

### Source 1 — published combinations, zero search
The six five-slot NNFX combinations **N1 to N6** catalogued in the 9 November research report
(`results/research/RESEARCH_2026-11-09_part2_regime_taxonomies_and_nnfx_catalog.md`, section
2.3), at their **published settings exactly**. Chosen by people who traded them, written down
before any result of ours existed.
**Batch null: random entries, matched on count and holding period, floor for best-of-6.**

### Source 2 — hand-built, declared reasons
Up to ten complete algorithms, each with **one line of reason drawn from a measurement on
record**. The reasons are stated in SOURCE2.md and in the ledger before the runs.
**Floor for best-of-N**, N the number proposed.

### Source 3 — machine search, with a search null
- **Discovery set**: 2005-2010, the 15 pairs containing neither JPY nor CHF.
- **Replication set**: 2011-2015, the 13 pairs containing JPY or CHF.
- The two off-diagonal sets are computed and reported.
- 200,000 complete algorithms sampled at random from the full five-slot space, then a local
  search from the top 200 — one slot or one setting changed at a time, while discovery net R
  improves. Objective: net R per year excluding the best day. **Every evaluation counts into
  the ledger.**
- **The search null**: the identical search, same budget, on **zero-edge data** — each pair's
  daily returns block-shuffled in time within year, 20-day blocks, each block's direction
  randomly flipped — **50 independent runs**. The distribution of the best **replicated**
  result under the null is the floor. A real find must beat its **95th percentile on the
  replication set**.
- The top 50 from the real search go to the replication set **once**. Those that beat the
  search null then face G2, G3 (on all data) and G4.
- Also reported: the **rank correlation between discovery and replication performance across
  all 200,000**, real against null. If it is not above the null, that is said plainly: it means
  past performance in this space does not carry.

**The search null is the expensive and the honest part.** It is what separates "we found
something" from "a search of this size finds this much on noise."

---

## 7. The book

All passers from the three sources, **equal risk each**. Daily correlation matrix, book R per
year, verified worst dip, return per dip, and the prop simulator sized to the Team 1 budget.
BOOK2.md.

**No 2016-2020 number is opened.** When passers exist the run stops and reports, so Jack can
call the confirm.

---

## 8. What this protocol cannot do

Stated so no result is read as more than it is.

1. **It cannot create power that eleven years of 28 pairs do not contain.** The project's own
   power test (POWER_TEST.md) measured that a pre-declared candidate tested alone is blind
   below about 0.20 R per trade on six yearly values. Eleven years is better, not sufficient.
2. **It cannot tell a surviving candidate from a lucky one at N = 1.** Four gates reduce the
   false-pass rate; they do not take it to zero. The out-of-sample confirm is the only gate
   that settles it, and it is Jack's to call.
3. **The exit-indicator family is 39 helpers but they are not independent of the C1 family** —
   many are the same construction read as an exit. A candidate whose C1 and exit indicator are
   the same indicator is not using two pieces of information.
4. **Three settings per indicator is a coarse ladder.** A candidate that is positive only at
   `default` and fails at `half` and `double` fails G4 — which is the intent — but the ladder
   cannot distinguish "fragile" from "the half/double jump is simply too big for this
   indicator".
5. **Nothing in it measures slippage beyond the spread, financing, or execution at size.**
   `ENGINE_AUDIT_2.md` holds what was measured there; the leverage cap is the only size effect
   modelled.

---

## 9. Provenance

- `results/cost_table_h22.csv` — the cost table every run loads via `FX_COST_TABLE`.
- `results/research/RESEARCH_2026-11-09_part2_regime_taxonomies_and_nnfx_catalog.md` — section
  2.3, the N1-N6 catalogue and its grades.
- `results/nnfx/CANDIDATE_LEDGER.csv` — every candidate and every evaluation counted.
- `code/nnfxproto.py` — the one implementation of this protocol. Sources 1, 2 and 3 all call it.
