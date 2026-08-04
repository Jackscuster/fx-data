# STRATEGY RESULTS — STANDARD OUTPUT FORMAT

Every strategy result in this project is reported in the two blocks below. No
exceptions, no abridged versions. If a run cannot fill a cell, write `n/a` — do not
drop the row.

The unit of comparison is always **regime-filtered vs unfiltered**. A strategy result
with no BASELINE column next to it is not interpretable and should not be presented.

---

## BLOCK 1 — RAW METRICS

One column per regime state, plus a BASELINE column showing the same strategy run on
all data with no regime filter applied.

| Metric | State A | State B | … | BASELINE |
|---|---|---|---|---|
| Net Profit | | | | |
| Return/DD | | | | |
| Profit Factor | | | | |
| #Trades | | | | |
| Win% | | | | |
| $AvgTrade | | | | |
| Exposure | | | | |
| Return/Exposure | | | | |

Source fields in `strat.py:stats()` — `ret`, `retdd`, `pf`, `trades`, `win`,
`avgtrade`, `expo`. Return/Exposure is derived, not returned by `stats()`.

---

## BLOCK 2 — REGIME COMPARISON

Data % first, then percentage improvement against the BASELINE column of Block 1.

| Metric | State A | State B | … | BASELINE |
|---|---|---|---|---|
| Data % | | | | 100% |
| Ret/Exp % improvement | | | | 0% |
| Ret/DD % improvement | | | | 0% |
| PF % improvement | | | | 0% |
| Win% improvement | | | | 0% |
| $AvgTrade % improvement | | | | 0% |

The BASELINE column reads 0% down the whole improvement section by construction — it
is being compared against itself. Keep the column in place anyway; its presence is what
makes the row readable as a comparison rather than a standalone number.

---

## RULES

**1. Improvements are not uniform. Report every row, including the negatives.**
A regime filter can lift profit factor and win rate while making drawdown worse. That
is a normal result, not a failed run. Selecting only the rows that improved turns a
result into an advertisement.

**2. Report return and drawdown together.** Never present one as a trade against the
other, and never ask which is preferred. Both are optimised. A result that improves
return by accepting worse drawdown has not improved.

**3. Costs are applied.** Majors 1.5bp, crosses 3.0bp round trip, charged on position
*change*, per `strat.py:cost()`. The seven majors are EURUSD, GBPUSD, AUDUSD, NZDUSD,
USDCAD, USDCHF, USDJPY; the remaining 21 pairs are crosses. Do not apply one spread
across all 28 pairs — it understates the cost of the cross book, which is three
quarters of the universe.

**4. Same IS/OOS split as the signal work.** Fit on 1999-2015, confirm on 2016-2026
(`SPLIT = '2016-01-01'`). Every threshold, cut point and mapping is learned on IS only
and applied unchanged to OOS. Report OOS.

**5. Data % is essential — it is the row that exposes curve fits.** A regime covering a
thin slice of bars with excellent numbers is not a discovery. Improvement percentages
scale freely as coverage shrinks, so an improvement figure without its Data % beside it
carries no information. State coverage before stating performance.

---

## UNRESOLVED

**Return/Exposure normalisation is unconfirmed.** `expo` is the fraction of bars
holding a position (`(pos.abs() > 0).mean()`), so the natural reading is
`ret / expo` — total return scaled up to a hypothetical always-in-market equivalent.
This has not been confirmed as the intended definition, and the alternative
(annualising by time in market rather than by calendar time) gives different numbers.
Until it is settled, state which normalisation a given table used.
