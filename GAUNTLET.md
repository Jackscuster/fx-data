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

## GATE 1 — DISCOVER

All ~17.6M slot combinations, **default parameters only**, through the machine.
A deliberately low bar: this gate is a sieve, not a judge.

**KPI floors, on stitched blind performance:**
- expectancy above the **luck floor** — the 95th percentile of scrambled controls
- profit factor ≥ 1.05

**Minimum trades:** ≥ 100 pooled in the picking window, ≥ 50 pooled per blind
window. A combination that cannot produce that many is not evaluated, it is
recorded as untested.

**The output is FAMILIES, not combinations.** A family is a neighbourhood of
similar combinations that survive together. A lone survivor whose neighbours all
died is luck and is killed.

> **The neighbour definition is set ONCE, after survivor counts exist, and then
> frozen.** It is deliberately not fixed here: choosing it before knowing whether
> 200 or 200,000 combinations survive would either dissolve every family or merge
> them all into one. Fixing it afterwards is the one thing in this document
> allowed to be decided late — and it is decided once, recorded, and never
> revisited.

---

## GATE 2 — TUNE / EXPLORE

Surviving families get parameter tuning, through the same machine. Tuning is at
**family level — shared settings across the family, never per-combination**.
Per-combination tuning is how a family of 200 becomes 200 separate overfits.

**NOTHING IS THROWN OUT AT GATE 2.** Its KPI floors are a **sorting label**, not
a kill switch.

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
