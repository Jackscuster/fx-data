# NEXT BATCH — TREND ONLY: FIVE MECHANISMS, THREE HORIZONS

Deliver to Claude Code. Read HANDOFF.md first.

---

## WHERE THINGS STAND — DECORRELATION IS DONE

127,554 signals tested. After the new decorrelation gate: **28 independent survivors,
split 22 chop and 6 trend.**

Six independent trend detectors is a real result — before the duration batch there was
exactly **one** in 20,275. The duration family delivered. But 22 to 6 is the same
asymmetry the project has shown throughout, and it did not budge.

**Two findings from decorrelation that change this spec:**

1. **Hazard ratios are out.** `elapsed × count / H` correlates near 1 with plain
   time-since. They are substitutes. Build one, not both. This was listed as the most
   promising untested idea and it is not.

2. **Both targets agree on 25 of 25 independents that have both.** Where the efficiency
   spread is negative the turn-frequency spread is positive, and vice versa — every time.
   Chop detectors are not merely failing to find trend; they genuinely predict more
   direction changes. That is independent corroboration and the strongest validation the
   estimator has.

**Also note:** the trend/chop split is the SIGN of the efficiency spread, not the
`stronger_target` field (formerly `bt`), which only says which target a signal scores
higher on.

**Why chop keeps winning on agreement:** volatility spikes hit all 28 pairs
simultaneously, so any panel-based chop measure gets high cross-pair agreement almost by
construction. Trend is idiosyncratic per pair, so a genuine trend signal will always look
weaker on that gate. **This is the structural reason mechanism 1 below matters most** —
cross-sectional trend signals are also panel-based, and are the first trend construction
that could plausibly reach chop-like agreement.

---

## THE THESIS FOR THIS BATCH

Every trend-capture mechanism tested so far is **momentum** — some form of "price moved,
expect more of the same." Moving-average crosses, N-day returns, slope t-stats,
efficiency ratios. All the same idea wearing different clothes. It loses on all 28 pairs.

But the two best non-chop findings in the whole project are **not** momentum:

- `zz_tsexceed_D375` — time since the last 2σ move. The only trend signal to pass every
  gate. It is a *duration* measure.
- Currency-leg divergence — ranked the 2024 carry unwind 8.8σ, 5th of 27 years, and
  fired ten days before the trough. It is a *cross-sectional* measure.

Neither says "price went up so it will keep going up." **The next batch should abandon
momentum entirely and test mechanisms that have never been tried.**

---

## MECHANISM 1 — CROSS-SECTIONAL / RELATIVE STRENGTH  ← **HIGHEST PRIORITY**

We have tested time-series momentum (does *this pair* keep going) exhaustively. We have
never tested cross-sectional momentum (**is this currency strong relative to the other
seven**).

These are different effects. In other asset classes cross-sectional momentum works in
periods when time-series momentum fails, because it is a relative bet rather than a
directional one.

**We already have the currency leg indices built** — they were used for the crisis work.

- [ ] Rank all 8 currency legs by N-day strength. Signals: this pair's base rank, quote
      rank, and the rank *gap* between them
- [ ] Persistence of rank — how long has this currency held its position in the ranking
- [ ] Rank velocity and rank acceleration — is it climbing or falling through the table
- [ ] Rank dispersion across the panel — is there clear leadership or is everything
      bunched
- [ ] Distance from the ranking median, in sigma
- [ ] Time since the current leader took the top spot, and since the laggard took the
      bottom  *(combines the two things that already work)*
- [ ] Strongest-vs-weakest spread — the classic construction, applied to legs not pairs

**Why this is the priority:** it is a genuinely different question, our own leg-based
crisis work is the strongest non-chop result we have, and every input already exists.

---

## MECHANISM 2 — MARKET STRUCTURE

Momentum measures magnitude. Structure measures *shape*. Never tested.

- [ ] Higher-highs-and-higher-lows count over N bars; the mirror for downtrends
- [ ] Swing-point sequence integrity — how many consecutive swings respected the pattern
- [ ] Distance since the last structure break
- [ ] Pullback depth relative to the prior impulse leg
- [ ] Impulse-to-correction ratio — trends have long impulses and shallow corrections
- [ ] Count of failed breaks in either direction
- [ ] Support/resistance touch counts and time since the last test

**Close-only construction:** a swing high is a close higher than the N closes on either
side of it; a swing low is the mirror. Weaker than true OHLC swings — note that in the
code. If it produces nothing, that is a real answer about close-only data rather than
about structure as a mechanism.

---

## MECHANISM 3 — ACCELERATION, NOT VELOCITY

Everything tested is first-derivative. Trends may be better characterised by the second.

- [ ] Second difference of price over N, vol-normalised
- [ ] Rate of change of the slope t-stat
- [ ] Curvature of the price path — is it convex or concave
- [ ] Is the trend accelerating, steady, or decaying
- [ ] Acceleration of *volatility* alongside price — do they move together

---

## MECHANISM 4 — REGIME PERSISTENCE AND HAZARD *(extend the winner)*

`tsexceed` at 63.6% retention is the best family found, and decorrelation showed the
family is genuinely wide — 28 independents from 101, not one effect in many costumes.
Worth extending, but it produced only 6 trend detectors, so it will not close the gap
alone.

- [ ] Time since the last regime change, by every definition of regime we have
- [ ] Survival probability: given N days in this state, what has historically followed
- [ ] Time since the last chop episode, and its length
- [ ] Count of state changes in the last N days — regime churn
- [ ] Age of the current directional streak relative to its own distribution

---

## MECHANISM 5 — CONDITIONAL TREND

Trend keeps dying at the effect-size gate. Chop is panel-synchronised and therefore easy
to detect; trend is idiosyncratic. Conditioning may be what lifts the effect.

- [ ] Trend measures computed only when panel volatility is in its bottom tercile
- [ ] Trend measures computed only when panel dispersion is low
- [ ] Trend measures computed only when the pair's own vol is compressed
- [ ] Trend measures computed only when the two currency legs are diverging
- [ ] Trend measures computed only when time-since-shock is high

**This is the direct test of the compression finding** — that coiled range predicts
trending. It has never been implemented as a conditional feature, only as a standalone
one.

---

## ALLOCATION — 50,000 ACROSS FIVE MECHANISMS

| Mechanism | Signals | Why this weight |
|---|---|---|
| 1. Cross-sectional relative strength | **20,000** | Only genuinely untested question, and the one trend construction that is panel-based like the chop detectors that keep winning on agreement |
| 2. Conditional trend | 10,000 | Direct test of the compression finding; attacks the effect-size wall |
| 3. Market structure | 8,000 | Never tried; close-only limits it but that is itself worth knowing |
| 4. Acceleration | 6,000 | Never tried; cheap to build |
| 5. Duration extended | 6,000 | Already gave 6 trend detectors and the family is wide, but it will not close the gap alone |

---

## SCORING RULE — THREE HORIZONS, APPLIED TO ALL FIVE

**This is not a sixth mechanism.** It is a target choice that applies to every signal in
the batch.

Score all 50,000 against forward efficiency at **20 days, 60 days and 120 days.**

- [ ] Three target sets, three sets of quintile statistics per signal
- [ ] Report whether effect sizes rise with horizon
- [ ] Report whether the trend/chop split shifts with horizon

**Why it is worth roughly tripling scoring time:** the hypothesis that FX trend lives at
60–120 days rather than 20 has been open since the beginning of the project and has never
been tested. Every winning window in every batch has been a long one. If runtime forces a
choice, **cut total signal count to 35,000 rather than drop the horizons** — the horizon
question is worth more than 15,000 extra signals.

---

## SIZE AND CONSTRAINTS

**Trend only.** No chop signals in this batch — chop is well covered, with 86–96% pair
agreement and multiple confirmed survivors.

**Size: 50,000.** Not 100,000. The last batch produced 88 survivors that are probably a
handful of real effects. More volume is not the constraint; **new mechanisms are.** Spend
the budget on breadth of mechanism, not depth of parameter sweep.

**Deduplicate** against all 127k existing names. Print the overlap — must be zero.

**Do not rebuild:** momentum, moving-average crosses, N-day returns, slope measures,
efficiency ratios, interactions, deltas, monthly-sourced features. All tested, all
either failed or already covered.

**Gates unchanged.** Do not loosen anything to make more pass. The decorrelation gate is
now permanent and runs after the other six.

**Do not commit raw .npz for this batch.** The repo is already ~500 MB with
`results/scores6/` at 438 MB. Commit pooled per-signal statistics only — name, mechanism,
and for each horizon the IS/OOS t, spread, agreement, monotonicity and decay. Gitignore
`results/scores7/` and keep the npz local. Because that removes the ability to recompute
correlations in the cloud, **also commit the correlation clusters and independence flags
produced by the decorrelation gate at build time.**

**No Sharpe anywhere in this batch.** Signals are scored on forward efficiency ratio and
forward turn frequency. Sharpe belongs at the strategy layer (Phase 4), not in regime
detection. Any result expressed in Sharpe at this stage is measuring a strategy, not a
regime.

**Add the decorrelation gate permanently** — after the existing six, before reporting
survivors. It should have been there from the start.

---

## WHAT TO REPORT

1. Independent survivor count after decorrelation, not the raw count
2. Survivors by mechanism — which of the five above actually produced anything
3. OOS retention by mechanism, so we learn what to stop building
4. Whether effect sizes rise at 60d and 120d horizons versus 20d
5. Whether any trend signal finally clears 0.020 effect size with high pair agreement —
   that has happened exactly once in 127k

---

## THE HONEST FRAME

Momentum losing on all 28 pairs is not proof that trend is unharvestable. It is proof
that *one mechanism* fails. The two things that have worked best in this project —
duration and cross-sectional leg divergence — are neither momentum nor mean reversion.

That is the bet this batch makes. If 50,000 signals across five genuinely new mechanisms
produce nothing that clears the trend gates, that is a real answer and worth having: it
would mean FX trend at a 20-day horizon is not detectable from price, and the next move
is Phase 1.5 — rates, credit, positioning, implied vol — rather than more price
transforms.
