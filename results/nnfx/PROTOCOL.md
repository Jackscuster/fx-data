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

---
---

# AMENDMENT 1 — 25 November 2026, 19:20 EST

**Declared by Jack after Sources 1, 2 and 3 landed and before anything below was scored.
Sections 1 to 9 above are UNCHANGED and are the record of what Sources 1, 2 and 3 were
tested under. This amendment governs everything from here on.**

Jack's words, verbatim:

> Nothing is counted out for being small or for working on only some pairs. A strategy that
> makes 4% on 5 pairs and another that makes 8% elsewhere are both winners. The only pass or
> fail is on the combined BOOK.

## A1. MEMBER UNIT

A **sleeve** is one complete NNFX algorithm — every setting fixed in advance, exactly as
section 1 defines a candidate — **on ONE PAIR**. A strategy may hold sleeves on any subset
of the 28 pairs. A strategy is not required to work on all 28, or on any particular one.

This is a change of unit, not of standard. Section 1's definition of a complete algorithm
(all five slots live, all three exits live, the fixed risk plan) is untouched. What changes
is that the thing admitted and the thing scored is an (algorithm, pair) pair.

## A2. SLEEVE ADMISSION — light, and deliberately so

On the **admission years only**, a sleeve is admitted if all three hold:

| | test |
|---|---|
| **A** | net R positive **excluding its best day** |
| **B** | best trade under a quarter of its total R |
| **C** | at least **20 trades** |

**No luck test and no nudge test on single sleeves or single strategies.** G1 and G4 of the
original protocol do not apply to a sleeve or to a strategy on its own. They move to the
book, as B1 and B4. Nothing is rejected for being small.

## A3. BOOK GATES — strict, and only on the book

| gate | test |
|---|---|
| **B1 LUCK** | beats the **95th percentile of the same book built from the null** |
| **B2 ONE EVENT** | positive excluding the best day **and** excluding the best 5 days |
| **B3 HOLD-OUT** | positive on data **no sleeve was admitted on** |
| **B4 NUDGE** | still positive with the **admission count** moved one step down and one step up |
| **B5 MONEY** | at least **12% a year** sized inside **3.6% daily** and **5.4% trailing** through the prop simulator; days to pass the **+10%** evaluation |

## A4. STANDING RULE — admission data and scoring data never overlap

Two rotations for pair-specific sleeves:

| rotation | admit on | score on |
|---|---|---|
| **R1** | 2005-2010 | 2011-2015 |
| **R2** | 2011-2015 | 2005-2010 |

Where a strategy is admitted on all pairs of a cell, the **four-cell rotation already built**
(Source 3's discovery / replication / two off-diagonals: 15 pairs without JPY or CHF against
13 pairs with, 2005-2010 against 2011-2015) is also used and reported.

2016-2020 stays computed and **not reported**. 2021 onward stays sealed. A book that clears
B1 to B4 in both rotations goes to section A7, and the 2016-2020 confirm is Jack's call and
no one else's.

## A5. What this amendment leaves me to declare, declared now

Jack's amendment fixes the unit, the admission test and the gates. These are the operational
choices it does not name. **They are written here before anything is scored, and the ledger
carries them.**

| choice | declared value | why it is a choice and not a citation |
|---|---|---|
| **sleeve sizing in a book** | equal risk, weight 1/N on a union day index, a missing day counted 0 | the same rule BOOK2 used; it is the only sizing that needs no estimate |
| **B4's "admission count" for a searched book** | the top-K count K, moved one grid step down and one up | K is the count that selects the book |
| **B4's "admission count" for the DECLARED book (3a)** | the minimum-trade threshold, 20 moved to 15 and to 30 | book (a) has no K; the trade floor is the only count in its admission test |
| **the null for a searched book** | the identical construction — scramble, re-search, re-admit, re-select, re-score — 20 runs per rotation | a null that does not repeat the SELECTION measures nothing about selection |
| **the null's search budget** | **fully matched**: 200,000 random draws AND the local search at the same cap, on every one of the 20 null worlds, then the same 28-pair bank | measured at 19:35 EST, before any book was built: 0.149 ms per candidate-pair, so a matched null run costs ~41 min and 20 of them ~2.7 hours at five workers. It is affordable, so it is done properly |
| **the voting machine's cost** | charged on changes in the NET position per pair only, Jack's 4 September rule | fewer, larger changes than sleeves traded separately; the saving is reported |
| **the fast path's role** | the 200,000+ bank is built on the fast objective (realised by exit day, uncapped, charged once); every book that is REPORTED is re-scored on the full path with the 1:30 cap and mark to market | section 5's declared departure, unchanged |
| **the four-cell rotation's cell definition** | Source 3's, unchanged: 15 pairs with neither JPY nor CHF against the 13 with either | it is "the four-cell rotation already built" |

## A6. What this amendment cannot do

1. **It widens the search enormously.** 370,000 algorithms x 28 pairs x 2 periods is about
   20 million sleeve evaluations. Selecting the best of 20 million and then testing the
   selection is exactly the situation B1 exists for, and **B1 is therefore the only gate in
   this document that carries real weight.** If a book clears B2 to B5 and fails B1, it has
   found nothing.
2. **~~The book nulls do not repeat the local search.~~** WITHDRAWN at 19:40 EST, before any
   book was built, on a measurement rather than an estimate. At 0.149 ms per candidate-pair a
   matched null run — 200,000 draws, the local search at the same cap, the full 28-pair bank —
   costs about 41 minutes, and 20 of them about 2.7 hours at five workers. **The null is
   therefore fully matched** and B1 is a real floor, not a lenient one. This paragraph is left
   in place struck through rather than deleted, because it was written before the measurement
   and the record should show that the limit was checked and not merely assumed.
3. **A sleeve is a pair-specific selection and there are only 28 pairs.** Admitting on one
   six-year window and scoring on the other gives each pair exactly one independent test per
   rotation. Item 2 (`PAIR_FIT.md`) measures whether that selection carries at all before any
   book is built on it; if it does not, every searched book in item 3 is noise by
   construction and will be reported as such.
4. **Synthetic worlds run with the ambiguity resolver and realistic gap fills OFF** — there
   is no hourly bid/ask path for a shuffled series. Same declared limitation as Source 3,
   same direction: it makes the null slightly easier to beat.
5. **B5's prop simulator is a model of one firm's rules**, not a contract. `PROP.md` holds
   what it does and does not model.

## A7. If a book clears B1 to B4 in both rotations

Build the final version with admission on **all of 2005 to 2015** at the admission count that
was **best on average across the two rotations** — the averaging rule is declared here,
before the counts are known, so it cannot be chosen after seeing them. Run B5. Then **STOP
and report.** That is the candidate for the one-time 2016 to 2020 confirm, Jack's call.
`FINAL_BOOK.md`.

## A8. Order and provenance of the amendment

1. `SLEEVE_BANK` — item 1, the bank everything reads.
2. `PAIR_FIT.md` — item 2, does pair fit carry.
3. `BOOKS.md` — item 3, the books and the five gates.
4. `WINNERS.md` — item 4, the best book's members.
5. `FINAL_BOOK.md` — item 5, only if a book clears B1 to B4 in both rotations.
6. The corrected-cost rerun of stage 1 R2, stage 2 and items 1 to 6 — background, lowest
   priority, `COST_RERUN.md`.

---

## A9. A measurement on the admission test, 19:45 EST, before any book was built

The admission test of A2 was run on the 18 declared algorithms x 28 pairs = 504 candidate
sleeves per window, purely to see what it admits. **It admits 4 of 504 on 2005-2010 and 7 of
504 on 2011-2015.** The funnel:

| test | h1 2005-2010 | h2 2011-2015 |
|---|---:|---:|
| at least 20 trades | 263 of 504 | 215 of 504 |
| net R positive excluding the best day | 142 of 504 | 162 of 504 |
| **best trade under a quarter of total R** | **4 of 504** | **7 of 504** |
| both of the first two | 82 | 76 |
| **all three** | **4** | **7** |

Of the 82 sleeves that are positive with enough trades on h1, the **median best-trade share
is 0.561** and the minimum is 0.191. The quarter rule, applied to a single pair over six
years, is binding on almost everything.

**This is arithmetic, not a flaw in any sleeve.** A sleeve takes a median of 38 trades on one
pair in six years and a profitable one totals a few R; a single +2R trade is then half the
total. The quarter rule is a concentration test sized for a 28-pair book with thousands of
trades — which is exactly where Jack has now put it, as **B2** — and at the single-sleeve
level it mostly measures how few trades a sleeve takes.

**Nothing is changed.** Jack wrote the test and the headline number for every book below is
his test at **0.25**, unchanged. But the project's standing rule is that every cut is swept
over its full range and reported as a curve, so the share threshold is swept
**0.25 / 0.40 / 0.60 / 0.80 / 1.00 / off** and every book is reported at every setting, with
0.25 marked as the declared one. If the books at 0.25 are empty or trivially small, the curve
is what says whether that is the test or the strategies.


---

## A10. The four-cell rotation applied to a BOOK — declared 20:10 EST, before it was run

A4 says: *"Where a strategy is admitted on all pairs of a cell, also use the four-cell
rotation already built."* For books (b) and (c) that rotation cannot be used as Source 3 used
it, and the reason is worth stating: those books hold **pair-specific** sleeves, so a sleeve
admitted on a 15-pair has no position at all on a 13-pair and the cross cell is empty, not
weak.

So the four-cell rotation gets its own family, **(e) FOUR-CELL**, built the one way that
makes the cross cell real:

| step | rule, fixed here before any number is computed |
|---|---|
| **select** | on the **15 pairs with neither JPY nor CHF, 2005-2010 only**. An algorithm's sleeve on each of those pairs must pass A2's admission test; the algorithm is then ranked by its **total net R over the pairs it was admitted on**, exactly as family (c) ranks. Top **K**, swept 10 / 20 / 50 / 100 / 200 / 500 / 1000 / 2000 / 3500 / 5000 |
| **score** | those K algorithms traded on **all 13 pairs containing JPY or CHF, 2011-2015**, equal risk 1/N over the K x 13 sleeves. **No per-pair admission is applied on the scoring side**, because choosing which of the 13 pairs to trade would require looking at them |
| **report** | all four cells: the selection cell (15 pairs, 2005-2010), the **true cross** (13 pairs, 2011-2015), and the two off-diagonals (13 pairs 2005-2010, and 15 pairs 2011-2015) |
| **both modes** | separate and voting, as every other family |
| **and the mirror** | the same construction with the roles swapped: select on the 13 pairs in 2011-2015, score on the 15 pairs in 2005-2010 |

**Why this is the strongest test in the amendment.** It shares **no pair and no year** with its
selection, so it does not need a pair's fit to carry at all — only for an algorithm chosen on
one set of currencies in one decade to work on different currencies in a different decade.
That is the question Source 3 answered for a single algorithm (rho +0.0866, one passer); this
asks it for a book.

**AND ITS B1 IS NOT MATCHED, WHICH IS STATED HERE AND NOT BURIED.** The 20 null runs were
already running when this family was declared, and they do not build it. Family (e) is
therefore reported **in full and without a passer verdict**: B2, B3 and B4 are computed and
B1 is left blank. A matched null for it is the next armed stage, not an omission.

---

## A11. Family (d) COMBINED — declared 20:12 EST, before it was run

Item 3d: *"COMBINED: a plus the best of b and c."* "The best of b and c" names a choice, and a
choice made by looking at the scoring window is not a choice, so the rule is fixed here as a
**procedure** that the null applies to its own numbers exactly as the real run applies it to
its own:

1. For each of families **b** and **c**, compute scoring-window **return per dip** at every K
   in that family's grid, in **both rotations**.
2. **Average the two rotations** at each K. Take each family's **best K by that average**.
   Averaging is what A7 already declared for the final book, and it is used here for the same
   reason: a K that is best on one rotation's scoring window alone has been chosen by the test.
3. The winner is whichever of b or c has the higher averaged return per dip at its own best K.
4. **d = book (a)'s admitted sleeves UNION the winner's sleeves at that K**, equal risk 1/N
   over the union, both modes, every share threshold, both rotations.

A sleeve appearing in both halves is held **once**, not twice — the union is of sleeves, not a
sum of two books.

**ITS B1 IS NOT MATCHED BY THE RUNNING NULLS EITHER**, for the same reason family (e)'s is not:
the 20 runs launched at 19:41 build families a, b and c only. Families **d** and **e** get
their own matched null chain, over the **same 20 scrambled worlds** — the seeds are
`700000 + run` and `nnfxsrc3.zero_edge_frames` is deterministic, so the second chain rebuilds
the identical worlds rather than drawing new ones. Until it lands, d and e carry B2, B3 and B4
and a blank B1, and neither is called a passer.

---

## A12. B1b — THE CELL BASELINE. Declared 20:25 EST, as a companion to B1, not a replacement

Family (e) forced this out into the open and it applies to **every** book in the amendment.

**The measurement.** Over all 384,334 algorithms, with **no selection whatsoever**, the mean
net R per sleeve (sleeves with at least 20 trades):

| cell | mean R per sleeve | share positive |
|---|---:|---:|
| **15 pairs (no JPY, no CHF), 2005-2010** | **+1.383** | 59.5% |
| 15 pairs, 2011-2015 | −0.861 | 42.1% |
| 13 pairs (JPY or CHF), 2005-2010 | −0.565 | 45.2% |
| **13 pairs (JPY or CHF), 2011-2015** | **+0.807** | 55.8% |

**A random complete NNFX algorithm makes +1.38 R on the 15 majors-and-crosses in 2005-2010 and
loses 0.86 R on the same pairs in 2011-2015.** The cell, not the algorithm, carries most of the
sign. And this is exactly the diagonal family (e) shows **in both directions, whichever cell
it selected on** — so a four-cell book that is positive on its cross cell has, so far, proved
nothing except that it was handed a profitable cell.

**Why B1 alone cannot catch this.** The zero-edge null block-shuffles within the year and flips
block directions, which destroys any trend longer than 20 days. So **B1 asks "is there
exploitable trend in this data", not "did the selection beat picking an algorithm at random".**
A trend-following book passes B1 whenever trend exists, selected or not. Both questions matter
and they need different baselines.

**B1b, declared.** A book must also beat the **unconditional mean sleeve R of its own cell** —
the table above, at the same trade floor. This is exact and not an approximation: at equal risk
1/N a book's R **is** the mean of its sleeves' R, verified at +4.5485 against +4.5516 on family
(e) fwd K=10, the 0.003 being the entry-versus-bar-price cost convention.

**B1b is reported alongside B1 and does not replace it.** B1 says whether there is an edge
beyond noise; B1b says whether the selection added anything to a coin pulled from the same
cell. A book needs both, and a book that clears B1 and fails B1b has found a good six years,
not a good algorithm.

### What family (e) looks like under B1b, before its own null lands

Selecting on the 15 pairs in 2005-2010 and trading the 13 JPY/CHF pairs in 2011-2015 — no
shared pair, no shared year — the top-10 book makes **+4.552 R per sleeve against the cell's
+0.807, an excess of +3.745.** By calendar year: **+2.170, +1.187, +0.101, +1.213, −0.120** —
positive in four of five, and still positive with **any one year removed** (+2.38 to +4.67), so
it is not one macro event, and 2013 — the strongest year of the yen trend — is its *weakest*.
The same algorithms on the 13 pairs in **2005-2010** lose money in four of six years.

That is the most interesting number of 25 November and it is **not** called a passer: family
(e)'s matched null was declared after the 19:41 chain launched and is a separate armed stage.

---

## A13. A measurement, 20:35 EST — what transfers and what does not

Not a change to the protocol. A measurement that explains every book result above, taken on
the bank with no book in the way.

Rank every algorithm by its **total net R pooled over one set of pairs in one six-year
window**, and ask what its mean net R is **per sleeve on the other set of pairs in the other
window** — no shared pair, no shared year:

| | select on | score on | algorithms | **Spearman rho** | cell baseline | top decile | bottom decile | top − bottom |
|---|---|---|---:|---:|---:|---:|---:|---:|
| **fwd** | 15 pairs 2005-2010 | 13 pairs 2011-2015 | 164,088 | **+0.2069** | +0.807 | **+2.129** | +0.481 | **+1.648** |
| **rev** | 13 pairs 2011-2015 | 15 pairs 2005-2010 | 110,143 | **+0.1871** | +1.383 | **+2.521** | +1.105 | **+1.416** |

Monotone across the deciles in both directions, and symmetric.

Now the same quantity measured **within one pair** — item 2, the per-pair rank correlation
between an algorithm's early-years and later-years result on that same pair:

| | median per-pair rho | mean per-pair rho |
|---|---:|---:|
| admit 2005-2010, score 2011-2015 | **+0.0183** | **+0.0059** |
| admit 2011-2015, score 2005-2010 | **+0.0183** | **+0.0059** |

### The conclusion, in one sentence

**An algorithm's quality transfers across currencies and across decades at rho about +0.20,
and its fit to one particular pair transfers at rho about +0.01 — a factor of eleven on the
median and thirty on the mean.**

Everything in this amendment follows from that one asymmetry:

- `b_per_pair`, which selects **per pair**, is the best single cell of all 552 in rotation R1
  (+1.30% a year) and **fails B1b at every K in R2**, returning +0.369 R where a random
  admitted algorithm in the same cell returns +0.478.
- `c_all_pairs`, which selects **pooled across pairs**, is the only one of a/b/c to beat its
  own cell in **both** rotations, and family (d) independently chose it as its winner.
- Family (e), which selects pooled and scores on different currencies in a different decade,
  has the largest excess of anything measured: **+2.46 to +3.95 R per sleeve over its cell,
  at every K from 10 to 5,000.**
- The excess being **flat in K across three orders of magnitude** says the signal is **broad,
  not a best-of-many artefact** — a whole decile carries it. That is the opposite of what
  overfitting looks like, and it is also why it is better described as a **factor exposure**
  than as a discovered rule: most algorithms that worked on one cell work on the other.

**What it does not settle.** The deciles are measured against the cell baseline, which is B1b.
B1 — against data with no trend longer than 20 days — is still the open question for families
(d) and (e), and chain 2 is armed for it. A broad factor that pays whenever trend exists is
still worth owning; it is just not a secret.

---

## A14. THE TARGET MAP — the account lifecycle, declared 12:10 EST on 2026-11-26, before it was run

Jack's item 2 asks for net dollars a year per account, which needs more than
one pass of the prop simulator: an account that breaches buys another
challenge, and the fee is paid on every attempt. The lifecycle below is
declared here **before any number is produced**, because it is a model and not
a measurement, and because the answer to "what edge reaches $12,000" depends
entirely on it.

### A14.1 What one simulated account-year is

A path is **252 trading days**. The account starts in the **evaluation** phase
with one fee of **$549** already paid.

| event | what happens |
|---|---|
| evaluation reaches **+10%** | the attempt passes. A **funded** account begins the next day at **$100,000** with its own high-water mark. No fee. |
| evaluation breaches | the attempt ends. A **new** evaluation starts the next day and **another $549 is paid**. |
| funded breaches | the funded account ends. A **new evaluation** starts the next day and **another $549 is paid**. |
| funded, every **7th** funded day | 80% of equity above $100,000 is paid out and removed from the account. |
| day 252 | the path ends wherever it is. Equity above $100,000 in a funded account at the end is **NOT** counted — only cash actually paid out counts. |

**Unpaid funded equity is deliberately not counted.** It is not money until it
is withdrawn, and counting it would let a path that was about to breach book a
profit it never received.

### A14.2 Breach rules, exactly as the firm states them

Daily loss is measured **from the previous day's close**, and the trailing
floor is the high-water mark less the trailing fraction, never above the
starting balance. These are `r2reads._floor_of` and `r2reads.prop_run`'s rules
unchanged. Three budget pairs are reported:

| budget | daily | trailing |
|---|---|---|
| Team 1 | 3.6% | 3.6% |
| internal | 3.6% | 5.4% |
| **firm hard limit** | **4.0%** | **6.0%** |

### A14.3 Edge, and why size cannot change it

An edge is stated as **true yearly return per unit of yearly volatility** —
`S = sqrt(252) * mu_daily / sigma_daily`. Position size multiplies `mu` and
`sigma` together, so **S is invariant to size**: that is the whole reason for
stating the target map in these units. Size is swept separately as the **daily
volatility in percent of the account**, which is the quantity the firm's
budgets actually constrain.

Synthetic books draw daily returns from a normal distribution at the stated
`S`. **A normal draw is a friendly assumption and is declared as one** — real
daily P&L has fatter tails, so every pass probability below is an upper bound
and every breach probability a lower bound.

### A14.4 Measured books are block-bootstrapped, not refitted

For `c_all_pairs` K=50 and family (e), the daily series is resampled in
**20-day blocks** to 252-day paths, **2,000 paths** per cell, the same block
length the project's `_block_t` uses. Blocks preserve the autocorrelation that
makes drawdowns worse than independent draws imply. The series used is the
**scored** window, never the admission window.

### A14.5 What is reported and what is not

Curves only: pass probability, median days to pass, breach probability within
the funded year, expected payout, expected fees including re-attempts, and net
dollars. **No recommendation on size**, as Jack asked. The smallest edge
reaching $12,000 a year is reported as a crossing point of a curve, with the
size and breach rate at which it crosses — not as a proposal.
