# LOGIC HANDOFF — HOW THE THINKING WENT

Why the project is built the way it is. What was tried, what failed, and what the failures
taught. Read this before touching anything, so the same ground is not covered twice.

---

## THE PROJECT

A complete systematic FX trading system. Seven layers. **Layer 1, the regime estimator, is
the root node — everything else hangs off it.**

```
LAYER 1   REGIME ESTIMATOR   what kind of market is this pair in?   <- built
LAYER 2   STRATEGY LIBRARY   entries, exits, stops, sizing
LAYER 3   ROUTING            which strategy, which pair, which regime
LAYER 4   RISK AND SIZING    how much, adjusted for volatility
LAYER 5   VALIDATION         walk-forward, real costs, stress
LAYER 6   EXECUTION          spreads, slippage, capacity
LAYER 7   MONITORING         live dashboard, alerts, decay tracking
```

---

## THE BIGGEST MISTAKE, AND THE CORRECTION

**For five batches and 175,634 signals, this project was solving the wrong problem.**

Every signal was scored against a *forward* target — will this pair move in a straight line
over the next 20 days. That is **prediction**. Most of it failed, and the failures were
consistent and uninformative.

The correction: **a regime estimator's job is to identify what regime we are in now,** not
to forecast what is coming. That is an observation, not a prediction, and it is a far
easier problem.

Everything that works in Layer 1 came after that reframe.

---

## THE SECOND MISTAKE — THE TARGET COULD NOT SEE WHAT WE WERE LOOKING FOR

The forward target was:

```
|net move| / sum of |daily moves|
```

Two things were destroyed by construction:

- **The absolute value discards direction.** A pair falling hard and a pair rising hard
  score identically.
- **Dividing by path discards scale.** A straight 2% move and a straight 0.3% move score
  identically.

So the search for a trend detector was looking for signals to predict a number that could
not represent a trend. **That is why trend detection kept failing — not because FX does not
trend.**

The clue was visible and missed for months: the only trend signal that ever passed every
gate was `tsexceed`, a **duration** measure. Duration was the one dimension the target
partially captured.

**Adding scale fixed it.** Scale corrected to 0.180 against the old composite's 0.0104 —
seventeen times stronger, and it is what separates a real trend from a pair drifting
quietly.

---

## THE MOST IMPORTANT LESSON — SEARCHING MANUFACTURES EFFECT SIZE

A null test: shuffle the target 50 times, rerun the identical selection pipeline, see what
survives when there is nothing to find.

**Pure noise produced survivors in 34 of 50 runs.** Ten of those runs produced a noise
signal with a *larger* effect size than the best real one.

**78% of the top effect size was manufactured by selection.** The best signal read 0.0473
and corrected to 0.0104 at p = 0.255 — not distinguishable from noise.

**What survived was what was not searched.** Persistence — one motivated construction, not
the best of 167,316 — corrected to 0.0278 at p = 0.020, with all 50 null runs below it.
Scale corrected to 0.180.

> **A small number of motivated constructions beats a large search.**

This is the single most transferable finding in the project. Layer 2 will be tempted to
sweep thousands of strategy variants. That temptation is precisely what turned a 0.0473
into a 0.0104.

Related: **0 of 1,680 strategy variants survived deflated Sharpe correction** in earlier
placeholder work. An independent equities study got 0 of 2,400. Expect the strategy
gauntlet to be brutal.

---

## THE OTHER LOOK-AHEAD — SELECTION ITSELF

Six of seven gates read out-of-sample statistics. So *which* signals were chosen already
knew about 2016–2026.

Rerunning selection entirely inside 1999–2015: **zero of the 32 survivors would have been
chosen.** Not a reduced set — an empty intersection.

The honestly-selected set still retained 75% out-of-sample sign against a 60.6% library
baseline, so honest selection finds something. It is just much weaker than the
hindsight-selected version looked.

**The gate thresholds themselves had been calibrated by looking at selection-inflated
numbers.** They were rebuilt against the null distribution afterwards.

---

## WHAT LAYER 1 ENDED UP BEING

**A backward-looking classifier. Nine states. Three windows.**

Two axes: **straightness** (how cleanly price is travelling) and **scale** (how far, in the
pair's own volatility units).

| | Large move | Medium | Small |
|---|---|---|---|
| **Clean** | strong trend | medium trend | weak trend |
| **Mixed** | strong transitional | medium transitional | weak transitional |
| **Messy** | strong chop | medium chop | weak chop |

**Strong/medium/weak means size of move, not confidence.**

Read on three lookbacks — **7, 28, 128 days** — chosen by sweeping every window from 4 to
200 and picking three that separate well while staying different enough to carry distinct
information. A fourth was tested and rejected: 128 and 200 agree 89% of the time.

**Agreement between windows is a second signal.** All three agree (26% of bars) →
excursion 1.24. Fast diverges (21%) → excursion 0.60. Roughly double the movement with a
third less give-back.

### Why it works

It does not forecast. It works because recent volatility relates to near-future
volatility — quiet stays quiet, wild stays wild, usually. **That is description, not
prediction**, and it is exactly what the layer is supposed to do.

### The result Layer 2 needs

Measured on 71,000 entry events, four entry types, all 28 pairs, both halves of the data.
**The state at the moment of entry predicts the shape of what follows.**

Strong trend: peak 1.32, ~8 bars, retrace ~57%.
Strong chop: peak 0.93, ~5.5 bars, retrace ~84%.

Monotone across states on excursion, timing, retracement, hold rate and path efficiency.

---

## DESIGN DECISIONS AND THE REASONING

**Nine states, not six.** Collapsing the transitional row was tested. **87% of those bars
sit dead centre on the straightness axis** — genuinely ambiguous, not near a boundary.
Collapsing would invent certainty that is not in the data. The toggle exists; nine is the
honest default.

**Slow window colours the price chart.** A 20-day read made long trends look fragmented —
EURJPY showed 33 state changes in a year that was one sustained move. Colouring by the
128-day window cut that to 12. The trend was never broken; the lens was too short.

**Duration is a confidence weight, not a state axis.** Old states persist rather than break
— a 100-bar-old state has a 96% chance of surviving tomorrow against 78% for a young one.
But young and old trending produce nearly identical excursion (1.14 vs 1.06), so age tells
you how stable a state is, not what it will do.

**Weights were nearly a disaster.** Weighting the axes by effect size gave scale 97.3% of
the variance — "a scale classifier with two rounding errors attached." The fix was an
explicit 3x3 grid rather than terciles of a weighted composite, which guarantees both axes
contribute by construction.

**Straightness only matters when the pair is moving.** Within large moves it makes a 0.39
difference to excursion. Within small moves, 0.10. That is why it looked useless when
measured across everything.

---

## WHAT WAS RULED OUT — DO NOT REBUILD

All tested properly, most against a shuffled null.

| Ruled out | Evidence |
|---|---|
| **Momentum** | loses on all 28 pairs |
| **Predicting direction from price** | 121 constructions, all at 40–60% — chance |
| **Long horizons (60d, 120d)** | zero survivors from 43,815 |
| **Subset agreement** | noise produced 5,724 survivors against real data's 1,048 |
| **Cross-horizon confluence** | fires 79% on real data and 79% on noise |
| **Per-pair normalisation** | provably null — the gauntlet ranks within pairs, so any per-pair shift washes out |
| **Rate differentials for regime** | 5.5% rate spread produced 0.0011 difference in behaviour |
| **Interactions between signals** | 49% OOS sign retention — worse than a coin flip |
| **Delta features** | 42% retention. Levels win |
| **Monthly-timeframe features** | below random |
| **Hazard ratios** | correlate near 1 with plain time-since — same thing |

**One measured asymmetry worth carrying:** down-moves are straighter than up-moves — 0.226
against 0.219, holding on 21 of 28 pairs. Falls are more orderly than rallies in FX.

---

## THE OPEN ITEM — CRISIS DETECTION

**This is a Layer 1 component and it is unfinished.** It is parked, not delegated. Layer 2
does not build it.

A calendar of **48 news-dated crisis events, 2000–2026** exists. Every date came from news —
a policy decision, an intervention, a bankruptcy, a referendum — and **never from price.**
That is what makes validation non-circular, and it produced the only real accuracy numbers
in the project.

Best detector: `maxabsmove` catches **38 of 48 at 17x lift** over chance — with **zero days
of lead time.** It confirms a crisis. It does not warn of one.

**Two modes, only one partially built:**

- **Acute** — violent snap-back, like the 2024 yen carry unwind. Currency-leg divergence
  ranked it 8.8 sigma, 5th of 27 years, and fired ten days before the trough.
- **Chronic** — sustained one-way debasement, like the yen falling every year since 2021.
  **Not built at all.** The spike-based measure reads 2.9 sigma on it — nothing.

**Why it is hard:** the acute trigger is usually policy, invisible in price until it lands.
An earlier claim that one detector fired 2.5 days early turned out to be an artifact of a
window that started before the event date; forward-only testing removed it. Price can show
vulnerability building — crowded positioning, stretched extension, compressed volatility —
but not the trigger.

---

## STANDING RULES

- **No money metrics in Layer 1.** Sharpe, PnL, drawdown, win rate begin at Layer 2.
- **Everything lagged one bar.** No exceptions.
- **IS 1999–2015, OOS 2016–2026.** Thresholds learned on IS, applied unchanged to OOS.
- **Null-test anything that looks strong** before calling it a finding. Four separate
  results in this project turned out to be selection artifacts: the horizon reversal, the
  subset clustering, the trend-family dominance, and 78% of the headline effect size.
- **Never delete data that fails.** Failures are results. The 49% retention on interactions
  and 42% on deltas are why nobody rebuilds them.

---

## HOW THE WORK GETS DONE

Jack works alongside Claude Code, which runs on his Mac with full internet and commits
directly to `github.com/Jackscuster/fx-data`. Claude Code builds; the chat side designs
methodology, interprets results, and argues.

**Claude Code has caught real errors repeatedly** — a look-ahead bug in a feature, 700
byte-identical duplicate signals, a truncation bug that would have produced a dramatic and
entirely false headline, and a selection effect that had been mistaken for a market
mechanism. When it pushes back, it is usually right.

**The app** is a thin HTML shell that fetches `app_data.json` and `app_ui.js` from the
repo, so new work appears without redownloading anything.

**How Jack wants to be spoken to:** plain English, short, explained as if he knows nothing
about the subject. No jargon without an inline definition. No hedging. No repeated caveats.
Do not tell him to stop working on something. If a job fails, say so immediately and fix
it — never quietly shrink the work.
