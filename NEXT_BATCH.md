# NEXT BATCH — 100,000 NEW SIGNALS

Deliver this to Claude Code. Read HANDOFF.md first if you haven't.

---

## THE ASK

Build and score **100,000 signals that have never been tested**: 75,000 aimed at TREND,
25,000 aimed at CHOP. Running total after this batch: **120,275**.

Two hard constraints:

**1. No duplicates.** Load every existing signal name from `results/signals.json`
(20,275 of them) and exclude any generated name that matches. Print the overlap count —
it must be zero. Every previous batch did this and none duplicated work.

**2. Do not repeat what already failed.** From the last 20,275:
- **Interactions: 49.1% OOS sign retention, worse than chance.** 7,140 were wasted.
  Do not build products of signal pairs.
- **Deltas: 42% retention.** Do not build change-in-signal features.
- **Monthly-sourced features: 47.8% retention**, below random. Weekly 51.8%. Keep
  higher-timeframe use light.
- Variants that work: level (65%), z-score vs long window (56%), rolling percentile rank.

---

## WHERE TO AIM THE 75,000 TREND SIGNALS

`zz_tsexceed_D375` is the **only trend signal in 20,275 to pass every gate**
(t_oos +12.7, effect 0.021, 86% agreement, decay 1.03). It measures **time since the
last 2-sigma move**. The longer since a shock, the straighter price travels afterward.

That family is almost entirely unexplored. Build it out properly — elapsed-time and
duration features, not level features:

- Time since last N-sigma move, for N in 1.0 / 1.5 / 2.0 / 2.5 / 3.0 / 4.0
- Time since the last new N-day high, and the last new N-day low
- Time since price last crossed its own moving average
- Time since the last direction flip
- Length of the current same-sign streak, and that length relative to its own history
- Age of the current drawdown, and age of the current drawup
- Time since realised vol last crossed its own median
- Time since the last range breakout
- **Hazard-style ratios: elapsed time ÷ that family's own historical mean duration.**
  This is the most promising untested idea — it asks "are we overdue?" rather than
  "how long has it been?"
- Fraction of the last N days spent above / below a threshold (occupancy)
- Count of distinct episodes in the last N days (event frequency rather than recency)

Also worth pushing for trend, since trend keeps dying at the effect-size gate:

- **Conditional / state-dependent features.** Compute a trend measure only within a
  condition — e.g. efficiency ratio measured only on days when panel vol is in its
  bottom tercile. Trend is idiosyncratic per pair while chop is panel-synchronised;
  conditioning may be what lifts the effect size.
- **Longer target horizons.** Everything so far scores against a 20-day forward
  efficiency ratio. Add signals designed for 60-day and 120-day persistence. Jack's
  earlier hypothesis that FX trends live at 60–120 days rather than 20 was never tested,
  and the winning windows in every batch have been the long ones.

---

## WHERE TO AIM THE 25,000 CHOP SIGNALS

Chop is the easier side — it's panel-synchronised, so cross-pair agreement runs 86–96%.
Cross-sectional features retained OOS sign 68% vs 54% for own-price. Stay in that vein
and go deeper:

- Correlation structure: rolling eigenvalue spectrum of the 28-pair correlation matrix
  (not just the top eigenvalue — the second, third, and the gap between them)
- Dispersion term structure: short-window dispersion vs long-window
- Coexceedance at more thresholds and windows (`coex2`/`coex3` both survived)
- Breadth measures: share of pairs in drawdown, share above their own MA, share with
  rising vol
- Cross-pair rank churn — how much the volatility ranking of the 28 pairs reshuffles
- Panel-level turn frequency and its persistence
- Vol-of-vol and vol clustering at the panel level rather than per pair

**Score chop against the real chop target** (forward 20-day turn frequency), not against
negative efficiency. `sc5.py` already writes both; `prep.py` now pools both.

---

## IMPLEMENTATION — READ THIS, IT WILL BREAK OTHERWISE

**Memory.** 100,000 columns × 6,916 rows × float32 is ~2.7 GB per pair. You cannot build
the whole matrix at once. **Generate and score in blocks of roughly 5,000–10,000
columns**, write each block's quintile stats, free the memory, move to the next block.

**Runtime.** At the v5 rate (~84s/pair for 8,065 signals) this is roughly 8–10 hours of
compute. **Do not try to run this inside GitHub Actions** — the job times out at 180
minutes. Run it locally on this machine, in the background, resumable. The scorers
already skip pairs that have a `.npz`; extend that to skip completed blocks too.

**Commit the results.** This is the whole reason Claude Code exists here — you can commit
the `.npz` files directly. Once `results/scores6/` is in the repo, GitHub Actions will
never rescore it. Previous batches were bottlenecked because the web chat could only move
20 KB at a time.

**Naming.** New score dir `results/scores6/`. New modules `code/sig6.py` and
`code/sc6.py`. Add both to `pipeline.py`. Add `scores6` to the `DIRS` list in `prep.py`
and `'trend-duration'` to the batch label list.

**Follow sc5.py's structure** — two targets, arrays named `qt*/nt*/vt*` for trend and
`qc*/nc*/vc*` for chop. `prep.py` already probes `z.files` for both.

---

## EXPECT THIS RESULT

At 100,000 tests, roughly **5,000 signals will clear |t| > 2 by pure chance.** Sorting
winners to the top concentrates exactly that luck. The gauntlet is what protects against
it and it must run unchanged:

| Gate | Threshold |
|---|---|
| Sign holds OOS | must match |
| \|t\| OOS | ≥ 8.0 |
| Effect size | ≥ 0.020 |
| Pairs agree OOS | ≥ 0.85 |
| Monotonic | ≥ 0.95 |
| Decay ratio | ≥ 0.60 (floor only — do NOT add a ceiling) |

Do not loosen any gate to make more signals pass.

**Survivors will not scale with sample size.** 20,275 signals produced 13 survivors.
100,000 more will not produce 65 — the effect-size gate is a hard physical bar and most
of what's left is noise. A realistic good outcome is **5 to 20 new survivors, weighted
toward trend**, because the duration family is genuinely unexplored territory rather
than another reshuffle of the same measurements.

---

## WHAT TO REPORT WHEN IT FINISHES

1. Overlap count against the existing 20,275 — must be zero
2. Total scored, and the attrition at each gate
3. New survivors, split trend vs chop, with the full metric row for each
4. **Which families survived** — is it the duration/hazard family, the conditional
   features, or the longer horizons? That determines where the next batch aims.
5. OOS sign retention by family, so we learn what to stop building — the same way
   interactions and deltas were killed on evidence
6. Rebuild `app_data.json` and push, so the app shows all 120,275

---

## ONE THING TO BUILD ALONGSIDE

**Time stability across 6 blocks.** It's the missing gate and it matters more at this
scale. Split the history into six chunks and require the sign to hold in at least four.

The concern it addresses is specific: 2016–2026 contains COVID, 2020 and 2022 — extreme
dispersion periods. Panel-volatility signals would naturally look strong in a window
stuffed with volatility events. Block stability catches a signal that only works in
2020–2022. Nothing currently in the gauntlet does.

Add it as gate 7 and report how many of the existing 13 survivors still pass.
