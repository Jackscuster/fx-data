# MAKING THE ESTIMATOR ACTIONABLE

Three tasks. The estimator is not a warning light — it is a parameter setting. When a
Layer 2 signal fires, the regime read should tell us how to manage the trade, not whether
to take it.

**Chop reading** → take profit early, tight target, expect the move to stall and reverse
**Not-chop reading** → let it run, trail the stop, wide target

Same entry. Different exit. That is the estimator doing real work, and it does not
require a trend detector — "not choppy" is information whether or not we can name what is
happening instead.

**Correction to record before starting:** the conclusion "trend is not detectable" was
too broad. What was actually established is narrower — no signal predicts *whether* a
pair will trend over the next 20 days, panel-wide. Every pair trends sometimes. EURGBP at
0.171 trends less often than EURCHF at 0.281; it does not fail to trend.

---

## TASK 1 — SHORTER HORIZONS

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

## ORDER

1 and 2 first — they are cheap and they change what "the regime reading" means before
Task 3 tests it. Task 3 is the one that matters.

## WHAT SUCCESS LOOKS LIKE

Not "we found a trend detector." The realistic good outcome is:

> When the estimator reads high-chop, moves reach their peak in N bars and retrace X% of
> it. When it reads low-chop, moves run for M bars and retrace Y%. N < M and X > Y, with
> a large enough gap to set different targets.

That is a regime estimator earning its place — it does not need to predict direction, and
it does not need a trend detector. It needs to tell the strategy layer how to hold.
