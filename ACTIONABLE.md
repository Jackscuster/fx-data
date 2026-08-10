# MAKING THE ESTIMATOR ACTIONABLE

Six tasks. Task 1 is done; 2 and 3 were specced earlier; 4-6 are new.

**What the estimator is for.** It says what regime a pair is in. When a Layer 2 signal
fires, the regime read is the environment that signal is firing into. What Layer 2 does
with that information is Layer 2's decision.

**Correction to record.** The conclusion "trend is not detectable" was too broad. What was
actually established is narrower — no signal predicts *whether* a pair will trend over the
next 20 days, panel-wide. Every pair trends sometimes. The measured spread in baseline
trendiness across the panel is 15%, not the 64% an earlier version of this doc claimed.

---

## STATUS

- **Task 1 — DONE.** Answer: 20d stays primary. Effect size falls steadily as the horizon
  shortens (0.0398 at 20d, 0.0209 at 5d). Nothing new appears short. Monotonicity is
  cleanest at 15d (0.9997 vs 0.9856), so 15d is carried alongside.
- **Task 2 — pending.** Note the premise was overstated: measured panel spread is 15%, not
  64%, and IS/OOS rank correlation is 0.582, not 0.71. EURCHF and EURGBP both sit
  mid-table and differ by 0.006. Expect normalisation to be closer to cosmetic than
  decisive; the agreement-gate criterion settles it either way.
- **Task 3 — pending.** Still the task that decides whether the estimator earns its place.
- **Tasks 4-6 — new, below.** Added because Task 1 was framed wrongly: the four horizons
  were treated as competing candidates for one slot when they are actually dimensions
  describing the shape of a move. Two pairs both reading 0.30 at 5 days are in different
  regimes if one reads 0.30 at 20d and the other 0.15. The estimator currently cannot tell
  them apart.

**Scope, restated:** the estimator says what regime a pair is in. Nothing more. What
Layer 2 does with that — targets, stops, holding periods — is Layer 2's decision and is
not specified here. An earlier version of this doc said the estimator "sets take-profit
distance." That was wrong and is withdrawn.

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

## ORDER

1 → 2 → 3 → 4 → 5 → 6.

Tasks 1-3 were the original set. Task 1 is done. Tasks 4-6 came out of what Task 1
revealed and slot in after Task 3, because Task 3 is the bridge to Layer 2 and should not
wait on the term-structure work.

If Task 4 produces something strong, it may be worth rerunning Task 3 with the
term-structure reading as an additional input. Decide that after Task 4 reports.

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
