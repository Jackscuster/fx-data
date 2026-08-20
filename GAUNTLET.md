# THE GAUNTLET — Layer 2 strategy search

**No gate is adjusted after results exist.** Every threshold, window boundary and
rule below is fixed at the moment this file was committed. If a gate turns out to
be too harsh or too soft, that is a finding to report, not a number to move.

Authored from Jack's spec. Window boundaries and coverage are filled in from
`results/l2_feed_comparison.csv`; nothing else here was chosen by the builder.

---

## DATA

**Feed: OANDA daily mid, all 28 G8 pairs.** `data/oanda_ohlc/<PAIR>_mid.csv`.

Chosen because the engine's parity proof is a proof *about OANDA bars* — 185 of
189 entries reproduced against TradingView, `results/l2_parity_verdict.md` — and
because winners must port back to TradingView, whose FX charts are OANDA. Running
the search on any other feed forfeits that proof.

**Clean history starts 2005-01-03 for all 28 pairs.** Before that OANDA's
practice feed serves close-only placeholder bars (high = low = close, volume = 1),
110–672 per pair. Those bars are not neutral: `sma(high) == sma(low)`, so SSL
Channel confirms neither direction and the engine trades nothing — which reads as
"no edge" rather than "no data". **Every sweep loader must drop the leading
placeholder block.**

**Never backfill.** Coverage is reported per pair, per window, always.

---

## WINDOWS

Four equal-ish quarters of the *actual clean history*, split at year ends. Not of
1999–2026 — the data does not exist that far back on this feed.

| window | from | to | bars (28 pairs) | share |
|---|---|---|---|---|
| **W1** | 2005-01-03 | 2010-12-31 | 43,810 | 27.9% |
| **W2** | 2011-01-01 | 2015-12-31 | 36,316 | 23.1% |
| **W3** | 2016-01-01 | 2020-12-31 | 36,262 | 23.1% |
| **W4** | 2021-01-01 | 2026-08-14 | 40,839 | 26.0% |

Per-pair coverage is uniform — W1 1563–1565 bars, W2 1297, W3 1295–1296, W4
1458–1461. **No pair has fewer than 1,000 bars in any window**, so no pair is
carried by a thin sample.

### THE WALK-FORWARD MACHINE

Used at **every** gate, without exception:

```
tune on W1            ->  trade W2 blind
re-tune on W1 + W2    ->  trade W3 blind
```

**A candidate's score is ONLY its stitched blind performance** — W2 and W3
concatenated. Performance in a tuning window is never a score; it is the thing
that chose the parameters and is therefore not evidence about them.

**W4 is outside the machine.** It is touched once, ever, after all tuning at all
gates is finished. Nothing may be re-tuned after W4 is read. If a look at W4
changes any decision, the exam is void.

---

## REGIME SLICING — how every combination is scored, at every gate

**Every combination runs TWICE**: once with the two-leg trend plan, once with
the one-leg quick-target plan. Every trade is tagged, at its ENTRY BAR, with
Layer 1's regime label for that pair and date.

```
TREND score = the TWO-LEG run,  trades entered while the label is `trending`
CHOP  score = the ONE-LEG run,  trades entered while the label is `ranging`
```

**Combinations pass gates PER REGIME.** A combination may graduate as a trend
strategy, as a chop strategy, as both, or as neither, and those are four
different outcomes. KPI floors are unchanged within each slice; **the trade
minimums apply per slice**, not to the combined total.

**No dynamic plan-switching in the sweep.** A run is one plan for its whole
length. Choosing the plan bar-by-bar from the live label is Layer 3's job, and
doing it here would score the router and the strategy in one number.

**The label source is `results/layer1_states.csv`, column `shape2`.** It is
already lagged one bar — the value dated D was computed from data through D−1 —
so it is joined on the entry date with no further shift. Adding a lag would
double-count it; removing one would read the future.

`trend-in-range` and `neither` are **not scored slices** at gate 1. Layer 1's
routing gives `trend-in-range` the one-trade plan and stands aside on `neither`;
both are carried in the trade tags and reported, but a combination is not
admitted or rejected on them.

**Bars with no label are never backfilled.** 96.3% of OANDA bars carry one; the
rest are calendar mismatches between the H.10 panel Layer 1 was built on and
OANDA's, plus Layer 1 ending 2026-07-31. Trades entered on an unlabelled bar are
counted and excluded from both slices.

---

## RISK — the structure is permanent, the numbers are tunable later

**Fixed forever, never swept, at any gate:**
- 2% account risk per trade, **sized off fixed equity — no compounding**
- two legs in the trend plan (50/50), one leg in the quick plan
- leg 2 moves to breakeven when leg 1 banks
- stops only ever move in the trade's favour
- entries fill at the close of the signal bar

**Gate 1 defaults — the same in both plans:**
- reward:risk **1 : 1.5** — stop 1.0 × ATR, take-profit 1.5 × ATR
- trail **1.5 × ATR** behind the highest close
- trail arming at **2.0 × ATR** in profit
- ATR length: **set by the pre-test below**

Those four numbers — RR, trail distance, arming multiple, ATR length — become
**family-level tunables at gates 2 and 3**. They are not tunable at gate 1, and
they are never tuned per-combination.

**Why sizing is off fixed equity, and why that is not a simplification.** The
2% is taken against a constant account, so every trade risks the same cash and
one R means the same thing in 2006 as in 2019. That is the whole point: the
gauntlet ranks thousands of combinations against each other and against a
scrambled-control floor, and both comparisons are only valid if R is a fixed
unit. Under compounding it is not — R grows with the equity curve, so late
trades in a winning combination carry more weight than early ones, and a
combination that happened to win early outranks an identical one that won late
purely through the ordering of its returns. The measured quantity would stop
being edge and start being edge times path.

In the code this is `RISK = 100.0` in `l2sweep.py` — a fixed 100 units of cash
per trade, which is the 2% of a constant account expressed directly. Expectancy,
profit factor and the luck floor are all denominated in that unit.

Compounding re-enters at **Layer 4 / live sizing**, where path dependence is the
actual question being asked. It does not belong anywhere in the gauntlet.

---

## ATR LENGTH PRE-TEST — run before gate 1, frozen after

ATR sets the stop distance, the target, the trail and the position size. It is
the one parameter that touches every trade in every combination, so it is chosen
once, in advance, on the **picking window only**.

- a spread sample of a few hundred combinations covering every slot type
- RR 1:1.5, both plans, all 28 pairs
- **every** ATR length from 2 to 50
- picking window (W1) only — W2 and W3 are blind and stay blind
- ranked on pooled expectancy in R, profit factor as tiebreak

**The shape of the curve decides, not the winner.** A spike at one length is
luck and is not used; a plateau is real. **If the best length sits on a spike,
the centre of the best plateau is used instead.** Full table to `results/`, and
the chosen value and the curve's shape recorded here.

**RESULT — ATR length 31, frozen.** 300 spread combinations (every option in
every slot appearing 7–25 times), lengths 2–50, W1 only, both plans, all 28
pairs, ~240,000 trades per length. `results/gate1_atr_pretest.csv`,
`results/gate1_atr_choice.csv`.

The raw winner on pooled expectancy is 31 (+0.01377R, PF 1.0490) and it sits
**inside** the best 5-length plateau (27–31, mean +0.01340), so it is not a
spike and the winner stands.

**But the honest reading is that the pooled curve is flat.** Across all 49
lengths expectancy runs +0.01107 to +0.01377 — a total spread of **2.2 standard
errors**. There is no pooled optimum worth the name; 31 is the top of a very
gentle rise, not a peak.

**And the two slices want opposite things.** This is the finding, not the
number:

| slice | best ATR | worst ATR | correlation with ATR length |
|---|---|---|---|
| trend (two-leg) | **3** (+0.01397) | 47 (+0.00820) | **−0.78** |
| chop (one-leg) | **30** (+0.02059) | 6 (+0.01070) | **+0.73** |

Short ATR suits the trend slice and long ATR suits the chop slice, and they
cancel into a flat pooled curve. A single global value is therefore a compromise
that is near-optimal for chop and clearly sub-optimal for trend — at 31 the
trend slice scores +0.01079 against +0.01397 at length 3, a 23% reduction.

**Gate 1 runs the global 31 anyway, as specified.** Two reasons it is safe to
do so: gate 1 is a deliberately low sieve, not a judge; and ATR length is a
family-level tunable at gates 2–3, where families are already regime-specific
because gating is per regime — so the slices can separate there. **The risk is
recorded here: any trend family killed at gate 1 may have been killed by the
ATR compromise rather than by its own merit.**

---

## GATE 1 — DISCOVER

All slot combinations, **default parameters only**, through the machine, in both
plans. A deliberately low bar: this gate is a sieve, not a judge.

### AMENDED — THREE SIGNAL-EXIT MODES, EXACTLY ONE ACTIVE PER TEST

**This supersedes the configuration the first two gate 1 runs used.** Those runs
stay on disk, labelled superseded, and their combinations count toward the true
search total.

| mode | signal exit | C1 exits | baseline exits | exit slot | enumeration |
|---|---|---|---|---|---|
| **A** | C1 flip | yes | no | **unused** | 39×39×12×15 = **273,780** |
| **B** | baseline cross | no | yes | **unused** | 39×39×12×15 = **273,780** |
| **C** | exit indicator | no | no | used | 39×39×12×15×39 = **10,677,420** |

**Total: 11,224,980 combinations**, both plans, both slices — 22,449,960
evaluations.

**They are never combined.** The risk plan — stop, take-profit, trail, breakeven
— stays active in all three modes; it is not a signal exit. Reversal entries are
still allowed per the entry routes, and in mode A a C1 flip that reverses is both
the exit and the new entry.

**Why this had to change.** The original configuration ran the exit indicator
*and* the baseline cross simultaneously and unconditionally, with the C1-flip
exit off. Every combination was therefore testing "whichever of two exits fires
first". Measured on the instrumented run, in the trend slice:

| close reason | share |
|---|---|
| baseline cross | 44.0% |
| stop | 27.7% |
| target | 13.3% |
| **exit indicator** | **7.5%** |
| trail / breakeven stop | 5.1% / 2.3% |
| **C1 flip** | **0%** (switch was off) |

The exit slot was being judged on what the baseline left it, which is why its
enrichment was the flattest of any slot at 0.18×–1.19×. That was a fact about
the configuration, not about the indicators. Isolating each exit is the only way
the question "which exit rule works" is being asked at all.

**Six luck floors, one per slice per mode** — `results/gate1_luck_floor_mode{A,B,C}.csv`.
Floors never transfer across modes: the exit rule decides when every trade ends,
so it decides the R distribution a scrambled control draws from, exactly as the
stop and the ATR length do.

**The count is 10,677,420** — 39 C1 × 39 C2 × 12 volume × 15 baseline × 39 exit.
The 17.6M figure counts all 41/41/16/16/41 registry entries, but 9 of those read
a volume series spot FX does not have, so 6.96M combinations selecting one are
guaranteed to produce zero trades. They are excluded and counted, not searched.
Run in both plans, that is 21,354,840 evaluations.

**KPI floors, on stitched blind performance, PER SLICE:**
- expectancy above the **luck floor** — the 95th percentile of scrambled controls
- profit factor ≥ 1.05

**The luck floors, measured under the exact gate 1 configuration** (OANDA mid,
regime slicing, ATR 31), 12 sign-randomised surrogates × 400 combinations —
`results/gate1_luck_floor.csv`:

| slice | controls | mean | p50 | **p95 = the floor** |
|---|---|---|---|---|
| trend | 4,097 | −0.0036 | −0.0104 | **+0.078975 R** |
| chop | 3,311 | **+0.0217** | +0.0222 | **+0.094892 R** |

Two things to notice. These are **far above** the 0.042854 measured before
slicing existed — a slice has fewer trades than the pooled set, so its sampling
noise is wider and luck reaches higher. A floor is a property of the exact setup
it gates and does not survive a change to the trade definition.

And the **chop control has a positive mean**: the one-leg plan makes +0.0217R
per trade on directionally-scrambled data. That is structural, not an edge — it
is what a 1:1.5 barrier pair with indicator exits does to a random walk. It is
precisely why the bar is a measured control rather than "expectancy > 0".

**Minimum trades, PER REGIME SLICE:** ≥ 100 pooled in the picking window, ≥ 50
pooled per blind window. A slice that cannot produce that many is not evaluated,
it is recorded as untested — which is not the same as failing.

### DECLARED CONTINGENCY — a trend-slice pass at ATR 3

**Declared before any gate 1 result was seen.** At the moment this was written
the run had completed zero shards; nothing had been looked at.

The pre-test showed the trend slice wants a SHORT ATR (best at 3, correlation
−0.78 with length) while the chop slice wants a long one (best at 30,
correlation +0.73). Gate 1 runs the pooled compromise of 31, which is
near-optimal for chop and costs the trend slice about 23% of its picking-window
expectancy. So a depressed trend result at gate 1 is ambiguous between "no trend
edge exists" and "the ATR compromise suppressed it", and that ambiguity is
resolved by a test, not by argument.

**Trigger:** the trend slice returns few survivors, or clearly depressed ones,
relative to chop.

**The pass:** ONE supplementary gate 1 run, **trend slice only, at ATR 3**.
Everything else identical — same windows, same walk-forward machine, same KPI
floors, same trade minimums, same combinations, blind-only scoring.

**The trend luck floor is re-measured at ATR 3 first.** Floors do not transfer
across a change to the trade definition, and ATR sets the stop distance, the
target, the trail and the position size. Reusing 0.078975 would be reusing a
bar measured on a different set of trades.

**Its combinations are counted in the TRUE SEARCH COUNT** for the final deflated
Sharpe, alongside every gate 1 combination and every tuned variant from gates
2–3. A contingency branch is still search.

**Results are labelled as the declared contingency**, never merged into the
primary gate 1 output as though they came from one pass.

**This is a pre-declared branch, not a second pick after peeking.** One
supplementary pass, at one length chosen by the pre-test before any gate 1
result existed. If it also comes back empty, that is the answer.

### AMENDED — NO FAMILY-BASED CUTS, AT ANY GATE

**~~The output is FAMILIES, not combinations. A family is a neighbourhood of
similar combinations that survive together. A lone survivor whose neighbours all
died is luck and is killed.~~** — **STRUCK.**

**Every gate 1 survivor advances.** Each is judged by the same walk-forward
gates as everything else, on its own blind performance. No combination is
removed for the company it keeps.

**Families are an organizing tool only.** They carry exactly two jobs and no
others:

1. **Gate 2 tunes shared settings per family** — one setting applied across the
   family, never per-combination. That restriction survives the amendment
   intact, because it is about *how many free parameters tuning may spend*, not
   about which combinations are allowed to live.
2. **The enrichment map sets tuning priority** — which families get worked
   first. Priority, not permission.

**Why the lone-winner rule is struck.** It killed on a property of a
combination's *neighbours* rather than of the combination. Two things are wrong
with that. It is not a walk-forward test, so it imports a judgement the blind
windows never made; and the neighbourhood is an artefact of a neighbour
definition that the original text openly admitted could not be fixed in advance.
A rule whose verdict depends on a parameter chosen after seeing the survivor
count is a rule that can be tuned to its answer. Isolation is a reason to rank a
combination lower for tuning effort. It is not evidence that it does not work.

The neighbour definition is therefore no longer a gate parameter. It is set once
for the enrichment map, recorded, and nothing dies by it.

---

## GATE 2 — TUNE / EXPLORE

Surviving combinations get parameter tuning, through the same machine.

> **~~Tuning is at family level — shared settings across the family, never
> per-combination. Per-combination tuning is how a family of 200 becomes 200
> separate overfits.~~** — **STRUCK.**
>
> **A family is each distinct combination. Tuning is per-combination.** Jack's
> call, recorded with its consequence stated rather than hidden: this is 754,670
> independently tuned configurations, each with roughly twelve free parameters,
> and the overfitting risk the struck text describes is real and is accepted.
> What controls it is not the tuning rule but the two things downstream — blind
> windows the tuner never sees, and a deflation total that counts **every**
> configuration evaluated. Both are enforced below.

### THE TUNING METHOD

**Coordinate descent.** One knob at a time in priority order, all others held,
then **one full second pass** to settle interactions.

**A tuned value is adopted ONLY if it beats the default** on the tuning window —
expectancy in R, profit factor as tiebreak, minimum-trade rules enforced. A knob
that finds nothing better keeps its default.

    tune on W1  ->  trade W2 blind  ->  re-tune on W1+W2  ->  trade W3 blind

The re-tune is free to pick different values. **Score = stitched blind
performance (W2 + W3).** W4 is never touched.

**Knob priority within a combination:** vol filter params → baseline params →
C1 params → C2 params → exit params (mode C only) → then risk: ATR length →
stop → target → breakeven X → arming M → trail D.

**PARAMETER ORDER WITHIN A SLOT IS MEASURED IMPACT ORDER**, highest response
first, from `results/gate2_param_impact.csv`. This is now specified rather than
left open, because it is not cosmetic: **coordinate descent is order-dependent**,
so the order silently determines which values get adopted. It floated once and
must not again.

> **MODE B IS THE EXCEPTION, and it is a permanent one.** Mode B was launched
> seven seconds after commit **`a86edb0`**, before the impact measurement
> existed, and therefore tuned parameters **alphabetically** within each slot.
> **Reproducing any mode B result means running commit `a86edb0`** — current
> code will return a different answer, and not by rounding: re-running three
> banked B combinations gave +0.0740 → −0.0640, −0.0400 → +0.0652, and
> +0.2913 → −0.1103. **45 of 105 indicators** have an impact order differing
> from alphabetical, so this reaches most of the population.
>
> Mode B is internally consistent — every chunk ran in one process on one code
> version — and both orders satisfy this document, which fixed the SLOT order
> and was silent on parameter order until now.
>
> **B-vs-A and B-vs-C comparisons therefore carry an ordering difference on top
> of the exit-mode difference.** This is tolerable for one specific reason:
> **no gate compares modes head-to-head.** Every mode is judged against the null
> measured for its own configuration — six separate floors, six separate nulls —
> and never against another mode's result. The ordering difference would matter
> if a mode's survival depended on beating another mode; it does not.
>
> **Round-2 deepening may re-tune mode B survivors under impact order**, before
> any W4 touch, which unifies everything that reaches the final exam. Whether it
> does is Jack's call at round 2; the option is preserved by the checkpointing
> rule above.

**Engine flags stay active in their current working state and are never tuned,
at any gate:** continuation, One Candle Rule, 1.5× ATR max distance, Bridge Too
Far 7, and the entry routes.

### RISK GRIDS

| knob | grid | points | applies to |
|---|---|---|---|
| stop | 1.00–1.25 @0.05, then 1.26–1.50 @0.01 | 31 | both plans |
| target / RR | 1.00–3.00 @0.05 | 41 | trend leg 1 and the chop trade. **Leg 2 never has a target** |
| breakeven X | 0.01%–0.20% @0.01%, of PRICE | 20 | trend only |
| arming M | 1.00–2.00 @0.05 | 21 | trend only |
| trail D | 0.50–2.00 @0.05 | 31 | trend only |
| ATR length | every integer 2–50 | 49 | both plans |

**Indicator grids:** every parameter of the combination's indicators, spanning
1/10× to 10× its default, ~12 log-spaced points, integer periods rounded and
floored at 2.

### LEG-2 MECHANICS — the trend plan, FINAL

**This supersedes the old fixed breakeven/arming rules and deliberately diverges
from both the previous engine and the shipped Pine. It is the specification, not
a port.**

1. **When TP1 hits**, record the most recent **completed** daily close and the
   **ATR as of that same close**. Both are **frozen** from that moment. The trail
   never uses current ATR.
2. **Breakeven**: leg 2's stop moves to entry when price is **X% of price**
   beyond TP1.
3. **Arming**: after breakeven, the trail arms when price reaches
   **M × frozen-ATR** beyond the recorded close.
4. **Trail**: **D × frozen-ATR** behind the **highest close since arming**.
5. **Stop precedence**: once breakeven is set the effective stop is
   **max(breakeven, trail)** for a long, mirrored for a short. The trail never
   places the stop below breakeven and takes over only once its level passes it.
   **Stops move one way only, always.**

Triggers read the bar's high/low; the trail tracker reads closes. Phases may
cascade within one bar — price can clear TP1, the breakeven gate and the arming
level on the same bar, and that is correct.

**Why frozen rather than current.** A volatility expansion arriving *after* TP1
would widen a current-ATR trail and give back profit already made. Freezing the
base stops volatility that arrives after the decision from rewriting it.

> ### THE STITCHING DEFECT — mode B averaged where the spec says stitch
>
> `GAUNTLET.md` scores a candidate on **stitched** blind performance: ONE equity
> curve over W2 then W3. **Mode B computed it by averaging the two windows'
> aggregates** — Sharpe, Sortino and profit factor averaged, max drawdown taken
> as the larger of the two. That understates a drawdown running across the seam,
> and an average of two Sharpes is not the Sharpe of anything.
>
> **Modes A and C concatenate the blind returns and score one curve**, which is
> what this document asks for.
>
> **`max_dd_R`, `calmar`, `sharpe`, `sortino` and `profit_factor` are therefore
> NOT comparable between B and A/C.** `total_R`, `expectancy_R`, `n_blind` and
> the trade counts ARE — they sum and average identically either way. Any
> cross-mode ratio must be taken from the comparable set or from re-scored B
> numbers, never from B's originals.
>
> Handled exactly like the parameter-order split: B is reproducible at commit
> `a86edb0`, the defect is recorded rather than retro-fixed, and round-2
> deepening re-runs B under current code and resolves both at once.

**Verified before tuning started** — `code/l2legcheck.py`, six hand-computed
cases, all passing: the frozen base is the previous bar's, an ATR jump after TP1
changes nothing, TP1 tagged but not exceeded by X does not scratch the runner,
breakeven floors a low trail, stops never retreat, and a stop moved on a bar
cannot fill on that bar.

**The chop plan is unchanged**: one leg, stop and target only.

### MODE C'S SHAPE — DECLARED BEFORE ANY C TUNING EXISTS

**Written with mode B 900/14,815 tuned and mode C not started. No C result of
any kind existed when this was committed.** The prices it argues from are
measured, not guessed: 157 s per combination observed over 900 real
combinations, and per-indicator recompute costs measured across 28 pairs.

**1. THE CAP.** Tuning is capped at each indicator's **6 highest-impact
parameters**; the rest are frozen at their defaults. Impact is **measured**, not
asserted — see the response measurement below — and the ranking is frozen before
C runs.

Only four indicators are affected: `rex_oscillator_signals` (22 parameters),
`hieken_ashi_smoothed_signals` (16), `schaff_trend_cycle_signals` (8),
`schaff_trend_cycle_exit` (7). They are a small minority of the registry and a
third of mode C's cost, because they are named often *and* are among the most
expensive to recompute.

> **Six was reaffirmed after the response measurement existed, not before.**
> Measured over 267 parameters, the cap captures this share of total response:
>
> | cap | params tuned | response captured |
> |---|---|---|
> | 1 | 105 (39%) | 57.7% |
> | 2 | 173 (65%) | 84.9% |
> | 3 | 211 (79%) | 94.8% |
> | 4 | 227 (85%) | 98.0% |
> | **6** | **238 (89%)** | **99.6%** |
>
> The knee of the curve is at 3, and a cap of 3 would cut deeper for 4.8% of
> measured response. Jack chose 6 with that in front of him. Recorded because a
> threshold that was examined and kept is a different thing from one that was
> never questioned, and only the record can tell them apart later.

| mode C | full | capped |
|---|---|---|
| trend | 166.3 days | **113.0 days** |
| chop | 58.6 days | **37.5 days** |
| total | 225.0 days | **150.4 days** |

**2. THE STAGED PASS.** Every C combination first gets a **cheap pass**: ATR
length, stop, target, and **the single most impactful parameter of each of its
four indicators**, all on full grids.

> **A combination whose cheap pass improves on its default by at least
> +0.02R expectancy on the tuning window gets the FULL deep treatment
> immediately. The rest keep their cheap-pass result and still advance.**

**The 0.02R threshold is declared here, before any C tuning exists.** Gate 2
kills nothing: a combination that fails the threshold is not dropped, it is
carried forward with a cheaper parameter set and a flag saying so.

Every configuration evaluated in either pass counts toward the deflation total.

**3. NOTHING IS EVER LOST.** Every cheap-pass result, every tuned parameter set
and every response measurement is checkpointed to disk, summarised into
committed `results/` files, and given a `results/MANIFEST.md` entry. Large
regenerable artefacts are gitignored but **retained locally and never deleted**.

**The deep pass must be re-runnable LATER for any subset — including all of C —
from the banked cheap-pass state, without redoing it.** This is round 2 by
design: the fast shape carries the project through every gate first, and
anything can be deepened afterwards.

**4. W4 DISCIPLINE, RESTATED.** The final exam runs **only after Jack declares
all tuning finished, including any round-2 deepening**. If deepening is planned,
W4 is not touched after the fast cycle. A window spent early cannot be
un-spent.

**5.** Mode C runs **sorted** — `--sorted`, the wired fix. Gate 1 wrote survivors
in shard-interleaved order, so a 100-combination chunk touched 62 distinct
indicators against 30 sorted, and recompute is where the time goes.

### DECLARED — CROSS-MODE REUSE FROM MODE B, before A starts

Jack's premise is correct and worth stating: **indicator series are
exit-independent.** `L.compute(name, o,h,l,c, **params)` never sees the exit
mode, so every series computed during B's tuning is valid, unchanged, for A and
C. What follows is what that is worth, measured rather than assumed.

**1. PERSISTENT CACHE — adopted in a bounded form, not wholesale.**

The full reachable space is **12.9M distinct (indicator, param-tuple) sets**
— 12 grid points per parameter, capped at 6 parameters, so 12^6 for the widest
indicators — which at 28 pairs and ~20 KB an entry is **6.7 TB**. That is not a
storage problem to solve, it is a reason not to store it.

What IS shareable is the shallow layer, and it is small:

| layer | tuples | on disk, 28 pairs |
|---|---|---|
| defaults (already pinned in memory) | 105 | 0.06 GB |
| one parameter off default | 2,856 | **1.47 GB** |

Coordinate descent sweeps each indicator's first parameter **from that
indicator's defaults for every combination**, so those tuples are shared by
every combination naming it. Deeper tuples depend on what earlier knobs adopted
and diverge per combination — that is where the 6.7 TB lives and where reuse
does not.

**The cache is therefore a disk-backed LRU under a fixed size budget**, not a
complete store: shallow, hot entries survive and deep one-off entries are
evicted. A 20 GB budget holds ~1M entries against the current in-memory 600.

**2. SEEDING B'S ADOPTED VALUES — implemented only where it is not already a
no-op, and the reason is recorded.**

**B's adopted values are grid points by construction.** They were chosen from
the same grids A and C will search, so offering them as "additional candidates"
adds candidates that are already there, and the exhaustive per-knob search
already evaluates every one of them. As specified, seeding changes no outcome.

**The exception is real and is what gets implemented.** B ran UNCAPPED; A and C
are capped at each indicator's 6 highest-impact parameters. For the four
indicators above the cap — `rex_oscillator_signals` (22),
`hieken_ashi_smoothed_signals` (16), `schaff_trend_cycle_signals` (8),
`schaff_trend_cycle_exit` (7) — B may have adopted a value for a parameter that
A and C will never tune. **Those values, and only those, are genuinely new
information**, and are offered as candidates for otherwise-frozen parameters.
**14.5% of B's combinations name a capped indicator.**

Adoption is unchanged: a seeded value is taken only if it beats the default and
every grid alternative on the tuning window. No grid is narrowed and nothing is
inherited untested.

Overlap available to seed from: **74.5% of A's trend combinations and 42.0% of
A's chop combinations also appear in B.**

### RANKING AND INTENT — what the search is actually for

**1. GATES ARE FLOORS, NEVER TARGETS.** Passing a gate is the sub-goal. The goal
is the highest-performing strategies. **The tuner maximises; it never
satisfices.** Nothing selects on "cleared the label" — `crosses_label` is
computed for reporting and is read by no tuning decision.

**2. FINAL RANKING OF ALL GRADUATES — production and risk-aversion co-equal.**

    rank on total R over the blind windows
    rank on Sortino
    final position = the AVERAGE of the two ranks
    Calmar breaks ties

Ranks are averaged rather than the metrics themselves, because total R is
unbounded and Sortino is not — averaging the raw numbers would let one scale
swamp the other. This governs ordering, **round-2 deepening priority**, and
presentation. `l2tune.rank_graduates()`.

**3. THE FULL KPI STACK IS TRACKED AND REPORTED PER COMBINATION**: expectancy,
profit factor, Sharpe, Sortino, Calmar, max drawdown, **Ulcer index**, win rate,
and trade counts per window. Floors stay floors; diagnostics stay diagnostics.
No floor is set on Ulcer.

**4. TOTAL BLIND R IS CAPTURED PER COMBINATION** — confirmed present as
`total_R`, not derived from expectancy after the fact.

> ### THE OBJECTIVE MISMATCH — flagged, not fixed, because fixing it is Jack's call
>
> Item 1 asked whether anything optimises to a threshold. Nothing does. But
> there is a worse problem in the same family, and it is measured rather than
> suspected:
>
> **The tuner maximises EXPECTANCY (per-trade R). The ranking rewards TOTAL R
> (per-window).** Those are not the same objective, and they diverge exactly
> where it matters.
>
> Measured on 3,164 banked mode B trend combinations with valid blind windows:
> the overall rank correlation is high, 0.976 — but **only 12 of the top 50 by
> expectancy are also in the top 50 by total R.**
>
> | | expectancy | total R | trades |
> |---|---|---|---|
> | best by expectancy | 0.882 | 116.4 | 132 |
> | best by total R | 0.541 | **161.1** | 298 |
>
> Maximising expectancy systematically selects **fewer, higher-quality trades**.
> The top-by-expectancy set runs 130–170 blind trades; the top-by-total-R set
> runs 230–694. The tuner is actively trading total R away for per-trade
> quality, and then the ranking asks for total R back.
>
> **This cannot be fully repaired by a results-reading rule.** Re-ranking finds
> the best of what was explored; it cannot find configurations the tuner never
> walked toward. The parameter sets themselves were chosen for a different
> objective.
>
> ### RESOLVED — the adoption rule changes at ROUND-2 DEEPENING, all modes at once
>
> **Declared before any round-2 work exists.** Round 1 keeps its current
> adoption rule and stays internally consistent across A, B and C; round 2
> changes it for everything in one pass, so no mode is ever half-converted.
>
> **The round-2 adoption rule is Jack's co-equal rule applied to TUNING**, not
> total R alone:
>
>     among candidate settings on the TUNING window:
>       rank by total R
>       rank by Sortino
>       adopt the best AVERAGE rank, Calmar breaking ties,
>       if and only if it beats the DEFAULT under the same comparison
>
> This is the same rule that ranks the graduates, moved inside the search. **The
> tuner's compass and the final ranking then point at the same thing**, which is
> the whole point: round 1's tuner walked toward per-trade expectancy and was
> then judged on total R, and no re-ranking can recover configurations it never
> walked toward.
>
> Minimum-trade rules and the adopt-only-if-better-than-default discipline are
> unchanged. Round 2's combinations count toward the deflation total like
> everything else.
>
> ### ROUND-2 RE-TUNE VALUE TEST — declared before round 2 exists
>
> **Round 2 also asks whether the second tuning step is worth running at all.**
> For every combination, both variants are scored on **blind W3**:
>
>     (a) keep the W1-tuned settings unchanged
>     (b) apply the W1+W2 re-tune          <- what the machine does today
>
> **If (a) systematically beats (b), the second tune step is destroying value
> and the walk-forward machine drops it going forward: tune once, test blind
> twice.** Decided by the data, and recorded either way — a null result is
> reported as loudly as a positive one.
>
> **Both variants are clean blind tests.** W3 never entered either tuning step:
> under (a) the settings saw only W1, under (b) they saw W1+W2. Neither reads
> W3 before scoring it, so the comparison is fair and nothing leaks.
>
> **What motivated it**, from the W3 re-score of mode B (commit `a579ca6`,
> 5,400 combinations, W2 recovered exactly by subtraction):
>
> | | W2 — blind test of the W1 tune | W3 — blind test of the W1+W2 re-tune |
> |---|---|---|
> | mean expectancy | **+0.0827** | **−0.0075** |
> | mean total R | +13.05 | −0.40 |
> | share positive | 55.5% | 45.4% |
> | Spearman W2 vs W3 expectancy | \multicolumn — **−0.006** | |
>
> The second re-tune, given MORE data, produced settings that performed worse in
> their blind window than the first tune did in its. That is the shape of
> overfitting. It is not proof — the two windows were traded with different
> parameter sets, so some decorrelation is expected — which is exactly why it is
> being settled by a controlled test rather than by this table.
>
> **This is the one place the walk-forward machine itself may change.** Section
> WINDOWS fixes it as tune-W1 → blind-W2 → retune-W1+W2 → blind-W3; if the test
> says the second step subtracts value, the machine becomes tune-W1 →
> blind-W2 → blind-W3 and this document is amended with the evidence beside it.
> Dropping it would also halve gate-2 tuning cost, which is a consequence and
> not a reason.
>
> **Implementation is nearly free where the sets are banked.** Variant (a)'s W3
> score is one extra scoring call, because A and C bank `ip1`/`risk1`. Mode B
> does not, which is why B is re-run wholesale at round 2 regardless.

### THE INVERSION ARM, TRIGGERED

After normal tuning, chop combinations **still failing any of the six gate-2
label criteria** get the inversion test: full mirror, same signal events,
opposite positions, exits mirrored, one-leg plan. **Chop combinations that came
alive through tuning skip inversion** — no extra work where the normal direction
already works.

### FLOORS AND COUNTING AT GATE 2

**No floors are measured at gate 2, and gate 2 kills nothing.** The existing
mode-level floors are carried only as labels and are marked
**"gate 1 defaults floor — not valid for tuned configurations"**: they were
measured at ATR 31 with fixed 1.0/1.5 risk, and a tuned combination may sit at
ATR 7 with a 2.6 target, so they are not approximations of its null but
measurements of a different setup. **Fresh floors are measured at gate 3, once
per surviving configuration.**

**Every configuration evaluated is logged.** The deflation total at the final
exam includes all of it — 1,033,571,395 configurations at gate 2, on top of gate
1's 11,224,980 and both superseded runs.

**NOTHING IS THROWN OUT AT GATE 2.** Its KPI floors are a **sorting label**, not
a kill switch.

### THE GATE 1 VERDICT, AND WHAT IT DOES NOT DO

Gate 1 measured, against six fresh nulls:

| mode | slice | rate | null (95% CI) | ratio | clears |
|---|---|---|---|---|---|
| A C1-flip | trend | 5.543% | 5.593 (5.34–5.85) | 0.991× | no |
| A | chop | 3.094% | 6.999 (6.69–7.31) | 0.442× | no |
| **B baseline-cross** | **trend** | **6.648%** | 5.578 (5.32–5.83) | **1.192×** | **YES** |
| B | chop | 2.721% | 7.019 (6.71–7.33) | 0.388× | no |
| C exit-indicator | trend | 6.426% | 6.322 (6.05–6.59) | 1.016× | no |
| C | chop | 2.278% | 6.157 (5.86–6.45) | 0.370× | no |

**ALL THREE MODES ADVANCE. Nothing is dropped.** Gate 2's rule is that nothing
is thrown out here, and that rule is not suspended because a gate 1 number was
disappointing.

**"At chance" for modes A and C is an AT-DEFAULTS LABEL, not a kill.** Gate 1
ran default parameters only. A configuration that is indistinguishable from
noise at defaults has been shown one thing — that its defaults are not special —
and that is not the same as having no reachable settings that work. Parameter
tuning may move it. It may also not, and then it dies on evidence rather than on
a first impression.

**Mode B (baseline-cross exit, trend, 1.192×) is the only configuration proven
at defaults, and is therefore TUNING PRIORITY 1.** Modes A and C tune after it,
at lower budget, and **must clear their own post-tuning nulls to stay alive**.
Clearing mode B's null does not qualify them; each is judged against the null
measured for its own configuration.

**Deflation counting is unchanged and strict**: all three modes, both superseded
runs, and every tuned variant to come. Mode B's 1.192× must survive deflation
against the whole search, not against its own branch.

**Gate 2 population:** every survivor from all three modes, organized by family.

**Slot priority within tuning, from the corrected wins-more map:**
**vol filter → baseline → C1 → C2 → exit.**

### THE CHOP INVERSION ARM RUNS UNDER ALL THREE MODES

Chop failed in every configuration tested — 0.442×, 0.388×, 0.370×, and 0.383×
under the superseded run. The inversion arm therefore runs **under all three
modes' configurations wherever survivors exist, mode B first**: entries faded,
exits mirrored, one-leg plan, **fresh luck floors measured per inverted setup**,
each judged against its own null.

**If inversion fails across the board post-tuning, chop closes on evidence** and
the router stands aside in ranges.

### DECLARED — the chop slice gains an INVERSION arm

**Written after the gate 1 headline counts and BEFORE any look at which chop
combinations survived, or at anything inside them.** What is known at the time
of writing is three numbers: chop returned 168,819 survivors of 7,211,988
eligible, a 2.34% pass rate, against a null of roughly 5%.

> **Correction, added when the null was measured properly and not applied
> retroactively to anything above.** The "roughly 5%" was the circular figure —
> the floor-setting controls scored against their own p95, which is 5% by
> definition. Measured on 26,088 fresh controls against the frozen floor, the
> chop null is **6.11%** (95% CI 5.82–6.40). The declaration's premise is
> therefore stronger than it was written: chop is at **0.38×** chance, not
> 0.47×. Nothing in the arm changes; only the number it argues from.

**The observation.** Chop came back *below* its own scrambled controls. The
control keeps the real Layer 1 labels and scrambles only the price path, so the
comparison is like for like: real ranging price action is worse for the one-leg
plan than a random walk through the same bars. A signal that is merely useless
lands *at* chance. Landing reliably below it is a signal carrying information
with the sign reversed.

**The arm.** Gate 2's chop tuning includes **fading the signals** as a
family-level variant: short where the combination says long, long where it says
short, exits mirrored, the same one-leg plan, the same ATR-derived stop, target
and trail. Everything else identical.

**The honesty rules do not relax for it:**
- same walk-forward machine — tune on W1, trade W2 blind; re-tune on W1+W2,
  trade W3 blind; scored on stitched blind performance only
- family-level settings, never per-combination
- **its combinations count toward the true search total** for the deflated
  Sharpe. An inverted arm is a second look at the same data and is search like
  any other. Understating the count is the commonest way a deflated Sharpe is
  made to lie, and this is the second time that sentence has had to be written
  in this document.
- W4 stays untouched

**The kill condition, declared now.** If fading also fails, **chop dies at gate
2 on evidence** and the regime router **stands aside in ranges** — no chop
sleeve, no capital allocated to the ranging state, rather than a sleeve kept
alive because the regime exists in the taxonomy. A regime the estimator can
name is not thereby a regime that can be traded.

**Both directions cannot be right.** Long and fade cannot both beat the floor on
the same combinations in the same windows; if both appear to, that is a bug in
the mirroring and is treated as one, not as two edges.

**Gate 2 label, on stitched blind performance:**
- expectancy ≥ +0.08R
- profit factor ≥ 1.25
- Sharpe ≥ 0.5
- Sortino ≥ 0.7
- Calmar ≥ 0.6
- max drawdown ≤ 20%

---

## GATE 3 — THE CULL

Fine tuning, same machine, then **one brutal cut**. Tuning continues until
strategies exist at these levels or it is clear that none do.

**Gate 3 kill thresholds, on stitched blind performance:**
- expectancy ≥ +0.15R
- profit factor ≥ 1.5
- Sharpe ≥ 1.1
- Sortino ≥ 1.3
- Calmar ≥ 1.0
- max drawdown ≤ 10%

**Declared fallback, before any result exists:** if gate 3 passes few or zero,
gate 4 assembles from **gate-2-labelled graduates instead**. That is information
about how hard the problem is — it is not a failure, and it is not a reason to
lower gate 3.

---

## GATE 4 — COMBINE

All graduates into the routed portfolio, using Layer 1's routing (`shape2` with
`activity` as modifier; trending → two-leg plan, ranging and trend-in-range →
one-trade plan, neither → stand aside, crisis → one trade at most).

**No fixed floors here. Two relative bars:**

1. **Beat your best player.** The portfolio must beat its single best member on a
   risk-adjusted basis. A team that cannot outperform one of its own members is
   not a team.
2. **Drop-one.** Remove each member in turn. Any member whose removal does not
   hurt the portfolio loses its seat.

---

## FINAL EXAM — W4

**A single pass** by the finished routed portfolio. Reported **per member**, not
only in aggregate.

- **Real costs.** ThinkMarkets Standard table. **Crisis periods ×2.** Swap
  excluded and flagged — and **no pass is valid with an average hold longer than
  5 bars while swap is excluded**, because a multi-day carry cost that has been
  left out is not a rounding error.
- **Deflated Sharpe**, fed the **TRUE search count** — every combination *and*
  every tuned variant evaluated anywhere in gates 1–3. Not the number of
  survivors. Understating the search count is the most common way a deflated
  Sharpe is made to lie.
- **Regime dependence.** Each member must do better inside its assigned regime
  than outside it. If it does not, the estimator earned nothing and the routing
  is decoration.
- **Expectancy** on W4 must be the **same sign** and **at least half** the size of
  the stitched blind-period figure.

**Declared expectation, before the exam is run:** gate 3 graduates **should**
score worse on W4 than in walk-forward. That is the winner's curse and it is
normal. **Holding half is a pass.** A result that is *better* on W4 than in
walk-forward is not a triumph — it is a reason to check for a leak.

---

## STANDING RULES

- Everything lagged one bar. Entries fill at the close of the signal bar.
- Layer 1's labels are read, never modified or re-tuned.
- Costs charged on position change; majors and crosses priced separately.
- Nothing is deleted; superseded results get header notes.
- Every number quoted in a report comes from a committed file.
- Searching manufactures effect size. 78% of Layer 1's best headline was
  selection artifact. The scrambled-control floor, the family requirement, the
  blind-only scoring and the single W4 pass all exist because of that one fact.
