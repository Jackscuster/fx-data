# REGIME ESTIMATOR — WORK QUEUE

**Read the STATUS block first. Tasks 7-10 are the new priority and supersede the ordering
below.**

## WHAT THE ESTIMATOR IS FOR — CORRECTED

The estimator's job is to say **what regime a pair is in right now.** Not to predict what
regime is coming.

Everything built so far scores signals against a *forward* target — what the next 20 days
look like. That is prediction, and it is a harder and different problem. Knowing what is
likely next has value, but it is a second objective, not the main one.

**Identifying the current state has never been built.** Measure the last N days, classify
the state. No prediction required.

## THE TARGET WAS THE PROBLEM

Every one of the 175,634 signals was scored against forward efficiency ratio:

```
|net move| / sum of |daily moves|
```

That target is structurally incapable of representing two of the three things that define
a trend:

- **The absolute value discards direction.** A pair falling hard for 20 days and a pair
  rising hard for 20 days score identically.
- **Dividing by path normalises away scale.** A straight 2% move and a straight 0.3% move
  score identically.

So five batches searched for signals to predict a number that could not represent what was
being looked for. **That is the actual reason trend detection kept failing — not that FX
does not trend.**

The clue was visible and missed: the only trend signal that ever passed every gate was
`tsexceed`, a **duration** measure. Duration is the one dimension the target partially
captured, and it produced the only hit.

---

## STATUS

**Done:**
- **Task 1** — horizons. 20d has the larger effect (0.0398 vs 0.0209 at 5d), 15d ranks
  more cleanly (mono 0.9997 vs 0.9856). **Both kept. The horizons are dimensions, not
  competitors — do not collapse to one.**
- **Task 2** — per-pair normalisation. Provably null. The gauntlet sorts within each pair,
  so any per-pair shift washes out before scoring. Baselines still matter for Layer 3
  routing.
- **Task 3** — excursion after entry. **The result the project was working toward.** High
  chop peaks at 5.3 bars and retraces 82%; low chop peaks at 8.5 bars and retraces 58%.
  Monotone across all five quintiles on excursion, timing, retracement, hold rate and path
  efficiency. Held on all 28 pairs, all 4 entry types, both halves of the data. 71,000
  entries.
- **Task 4** — term structure. Persistence effect 0.0603, agreement 0.964, correlation
  0.089 with the composite. A genuinely second dimension. **Null test still outstanding.**
- **Task 5** — cross-horizon confluence. Dead. Agreement fires 79% of the time on real
  data and 79% on noise. Layering conditions reduced effect size at every step. All 71
  candidates chop-signed.
- **Task 6** — per-pair term structure. Dead. Pairs differ 4%, rank correlation 0.098.
  Persistence is a panel property, not a pair property.

**Outstanding from the old queue:**
- Null test on persistence, slope and cross-horizon agreement. Persistence reads 0.0603
  against the composite's 0.0398, and the inflation run showed the largest effects were
  the most manufactured (78% of the top effect). Until corrected, the second dimension is
  unconfirmed.

**New and now the priority — Tasks 7-10 below.**

---

## TASK 1 — SHORTER HORIZONS  *(DONE)*

Everything in this project measures forward efficiency over 20 days because that is what
was chosen at the start. It has never been justified. If a trade holds five days, 20-day
efficiency is answering a question nobody asked.

**Score the current survivor set against forward efficiency at 5, 10, 15 and 20 days.**

- [ ] All 111 survivors (or the 29 at the tightened gates — do both if cheap), scored at
      all four horizons
- [ ] Report effect size, pair agreement, monotonicity and OOS retention at each horizon
- [ ] Report whether the chop signals get stronger or weaker as the horizon shortens
- [ ] Report whether any signal that fails at 20d passes at 5d or 10d

**What to expect and why it matters either way.** Chop is a volatility phenomenon and
volatility clusters over days, not weeks. Short horizons may well be where the chop
signal is strongest. If effect sizes rise as the horizon shortens, the estimator has been
measured at the wrong horizon this entire time.

**Also run the null at the best-performing short horizon.** Shorter horizons mean more
independent observations, which inflates t-statistics for the same true effect. Do not
compare a 5-day t-stat to a 20-day t-stat without accounting for that.

---

## TASK 2 — PER-PAIR WEIGHTING

Baseline trendiness varies 64% across the panel and is stable — 0.71 rank correlation
between IS and OOS. EURCHF 0.281, EURGBP 0.171.

**A raw composite score means something different on each pair, and right now it is
treated as if it means the same thing.**

- [ ] Compute each pair's baseline forward efficiency, per horizon, **from in-sample data
      only.** These become fixed constants applied to OOS — never recomputed on the
      holdout.
- [ ] Build a normalised score: how far is this pair from *its own* baseline, in units of
      its own historical variation, rather than raw distance from the panel mean.
- [ ] Rescore the survivors using the normalised version and compare against raw on
      effect size, agreement and monotonicity.
- [ ] Report whether normalisation changes which pairs a signal fires on

**The specific thing to test:** does normalising raise pair agreement? If a signal was
failing the agreement gate because a raw threshold means different things on EURCHF and
EURGBP, normalisation fixes that and the signal was real. If agreement does not move,
normalisation is cosmetic.

**Watch for the trap.** Normalising by pair means each pair's score is now relative to
itself, so a normalised reading of "high" on EURGBP might correspond to a lower absolute
efficiency than "low" on EURCHF. For setting trade parameters that may be exactly right —
or exactly wrong. Report both and let the strategy layer decide which it wants.

---

## TASK 3 — DOES THE REGIME READ PREDICT WHAT HAPPENS AFTER ENTRY

**This is the bridge between Layer 1 and Layer 2, and it has never been tested.**

Every test so far asks "does the signal predict forward efficiency." That is a property
of the estimator. The question that decides whether the estimator is worth anything is
different:

> At the moment a strategy signal fires, does the regime reading predict whether that
> particular move continues or reverses?

### Construction

- [ ] Use simple, transparent entry triggers — not optimised strategies. A z-score
      extreme, an N-day breakout, a moving-average cross. The point is to generate entry
      events, not to find a good strategy.
- [ ] At each entry event, record the regime reading **as of the prior bar.** Standard
      lag, no exceptions.
- [ ] Then measure what happened after entry, **without any exit rule**:
      - maximum favourable excursion — how far it went the right way
      - maximum adverse excursion — how far it went the wrong way
      - how many bars until the favourable peak
      - whether it was still favourable at 5, 10, 20 bars
      - path efficiency of the move that followed

### The comparison

Split entries by regime reading — top third, middle, bottom third of the composite.

**The question:** do high-chop entries reach their peak sooner and give more of it back?
Do low-chop entries run further and hold longer?

If yes, the estimator sets take-profit distance and that is a real, usable output. If the
excursion profiles look identical across regime readings, the estimator does not inform
trade management and we need to know that before building Layer 2 on top of it.

### Rules for this task

- **No Sharpe, no PnL, no win rate.** Excursion and timing only. This measures whether
  the regime read carries information about the shape of what follows, not whether a
  strategy makes money. Money comes at Layer 2 with the full template.
- Run it per pair and pooled. If it works on some pairs and not others, that is routing
  information.
- Report sample sizes. A result on 40 entries is not a result.

---

## TASK 4 — BUILD THE TERM STRUCTURE

For every survivor, at every pair and date, we now have four readings: 5, 10, 15, 20 days.
Turn those into regime dimensions.

### 4.1 Persistence ratio

```
persistence = reading(20d) / reading(5d)
```

- High → the move sustains as the window lengthens
- Low → the move is front-loaded and decays
- Around 1 → flat term structure

**Nothing in the project currently measures this.** It is a distinct regime property from
"how straight is the move," and it is only visible with multiple horizons.

Also build the log version and the difference version — ratios are unstable when the
denominator is small, and 5-day readings can be near zero.

### 4.2 Term structure slope and curvature

- [ ] Slope: OLS fit of reading against horizon across 5/10/15/20
- [ ] Curvature: is the path across the four horizons convex, concave, or straight
- [ ] Classify each day into one of three shapes — rising, flat, falling

Three shapes is three regimes, and they are not the same thing as high/low readings.

### 4.3 Cross-horizon agreement

The multi-timeframe confluence work is the strongest filter found in this project — daily
alone gave 0.007 Sharpe, all three timeframes aligned gave 0.302. **Same construction,
applied to horizons rather than timeframes.**

- [ ] How many of the four horizons agree on direction (0–4)
- [ ] Dispersion of the four readings — tight cluster or wide spread
- [ ] Whether the extremes (5d and 20d) agree, specifically

Distinguish this clearly from the existing multi-timeframe work. That measures the same
horizon computed on daily, weekly and monthly bars. **This measures different forward
horizons on daily bars.** Different question, and both may carry information.

### 4.4 Score everything

Run all of 4.1-4.3 through the existing gauntlet at the current gate settings. Report:

- Effect size, agreement, monotonicity, retention for each construction
- Whether any term-structure feature beats the best single-horizon reading
- **Whether any of them are trend-signed** — this is the first construction in the
  project that could plausibly detect trend without predicting direction

---

## TASK 5 — TREND DETECTOR WITH CROSS-HORIZON CONFLUENCE

Trend detection has failed panel-wide, on subsets, and at long horizons. **It has never
been attempted using agreement across horizons as the confirming evidence.**

The logic: a real trend should look like a trend at 5, 10, 15 *and* 20 days. Noise that
happens to look trendy at one horizon should not survive at all four.

- [ ] Build a trend read requiring the same direction across N of 4 horizons, sweep N
- [ ] Add the persistence ratio as a second condition — a real trend sustains, so require
      persistence above a threshold as well
- [ ] Add the existing multi-timeframe agreement (daily/weekly/monthly) as a third
      dimension, since it is the strongest filter already found
- [ ] Test each condition alone and in combination, so we can see whether confluence adds
      anything or whether one condition carries it

**Run the null on this before believing any of it.** Every previous trend route died when
tested against a circularly-shifted target. Subset agreement looked promising and noise
beat it five to one. Assume this is the same until proven otherwise.

Specifically: does noise produce the same rate of four-horizon agreement? Confluence rules
can be weak in the same way subset rules were — if the criterion is easy to satisfy by
chance, agreement across horizons is not evidence of anything.

---

## TASK 6 — WHAT THE TERM STRUCTURE MEANS PER PAIR

Baseline trendiness varies 15% across the panel with 0.582 rank correlation between IS
and OOS. Modest but real.

- [ ] Compute the typical term structure shape for each pair, IS only
- [ ] Do some pairs habitually show sustained moves and others habitually show bursts
- [ ] Is that stable IS to OOS
- [ ] Does normalising by each pair's own typical shape change anything

If some pairs sustain and others burst, that is a per-pair regime property that persists —
and it is routing information for Layer 3, not a parameter for Layer 2.

---

## TASK 7 — DIRECTION  *(priority)*

Never measured. A regime detector that cannot tell up from down is not detecting all
regimes.

- [ ] Build a **signed** target: net move over the window, not absolute, normalised by
      path. Range -1 to +1. -1 is a straight fall, +1 a straight rise, 0 is chop.
- [ ] Rescore the existing survivor set against it. Do any current signals carry
      directional information, or are they all direction-blind by construction?
- [ ] Build direction-specific signals and run them through the gauntlet
- [ ] Report whether up-trends and down-trends behave differently — different typical
      durations, different persistence, different excursion profiles after entry

**Specifically test the asymmetry.** In FX, falls and rallies are not symmetric —
`maxdd` predicted trending while `maxdu` predicted chopping in an earlier batch. That was
never followed up and it points directly at direction mattering.

---

## TASK 8 — SCALE  *(priority)*

Also never measured. Dividing by path normalises magnitude away entirely.

- [ ] Build a scale measure: total distance travelled over the window, in units of that
      pair's own volatility
- [ ] Cross it with straightness — the four combinations are four regimes:
      straight+large, straight+small, choppy+large, choppy+small
- [ ] Report how much time is spent in each, per pair and pooled
- [ ] Test whether the excursion result from Task 3 differs across these four rather than
      just across the chop axis

A straight move going nowhere and a straight move covering ground are different
environments. The current estimator cannot distinguish them.

---

## TASK 9 — DURATION  *(priority)*

Partially captured, never built out properly. The `tsexceed` family produced the only
trend signal that ever passed every gate — that is a signal worth following.

- [ ] How many bars has the current state been running
- [ ] How does that compare to how long this state typically lasts on this pair
- [ ] Time since the last state change, and the count of changes in the last N bars
- [ ] Whether state age predicts what happens next — do old states persist or break

---

## TASK 10 — BACKWARD-LOOKING CLASSIFIER  *(the main build)*

Tasks 7-9 supply the dimensions. This assembles them into a classifier that says what
state a pair is in **right now**, from data already in hand.

- [ ] Four axes: **straightness, direction, scale, duration**
- [ ] Measured over multiple lookbacks — 5, 10, 15, 20 days — kept as separate readings,
      not collapsed
- [ ] Output a state label per pair per day, plus the underlying continuous readings
- [ ] No forward target. This describes what has happened, not what will happen.

### Validation is different for a backward-looking classifier

The existing gauntlet scores predictive power against a forward target. That does not
apply here. What does:

- **Persistence** — do states last, or flicker bar to bar
- **Separation** — do the states actually differ from each other on measurable properties
- **Stability** — does refitting on more data rewrite history
- **Agreement with the forward-looking composite** — where do they agree and disagree, and
  what does disagreement look like

**Then reconnect to Task 3.** Does the backward-looking state, read at the moment an entry
fires, predict excursion shape as well as or better than the forward-looking composite
does? That is the test that says whether this replaces the current approach or sits
alongside it.

---

## ORDER

Tasks 1-6 are complete. Remaining work, in order:

1. **Null test on Task 4's term structure** — short, and it determines whether persistence
   is real before anything gets built on it
2. **Task 7 — direction**
3. **Task 8 — scale**
4. **Task 9 — duration**
5. **Task 10 — backward-looking classifier**, assembling 7-9

7, 8 and 9 can run in parallel if convenient — they are independent measurements. 10
depends on all three.

## WHAT SUCCESS LOOKS LIKE

Not "we found a trend detector." The realistic good outcome is:

> When the estimator reads high-chop, moves reach their peak in N bars and retrace X% of
> it. When it reads low-chop, moves run for M bars and retrace Y%. N < M and X > Y, with
> a large enough gap to distinguish the regimes.

That is a regime estimator earning its place — it does not need to predict direction, and
it does not need a trend detector. It needs to describe the environment accurately enough
that Layer 2 can act on it.

From Tasks 4-6, the realistic good outcome is a **second dimension**: not just how
straight the recent move has been, but whether that straightness sustains or decays. Two
readings instead of one. If cross-horizon confluence also rescues trend detection, that is
a bonus rather than the premise.
