# Layer 4 sizing v1 — netted votes, agreement curve, per-currency cap

Roster: the W3ONLY_ADOPTED team, 25 members. Fees on, mark-to-market at the
window boundary, W3 only (2016-2020).

## CAVEAT — THESE LEVELS ARE NOT COMPARABLE TO THE TEAM BUILDER'S

The team builder scores a book on the **daily mark-to-market change in equity**.
This study spreads each trade's R evenly across the days it was held, because
agreement is a property of the days risk is carried, not of the exit date.

Spreading R smooths the daily series, which shrinks DIP95 and max drawdown,
which inflates the scale the budget allows. The same roster and budget give
22.97% here as a median year under mark-to-market and 55.56% under spread-R.

**So read the RANKING of A/B/C/D, not the levels.** All four use identical
attribution, so the comparison between them is sound; none of them is directly
comparable to a team-builder number. A v2 should net positions and then value
them mark-to-market, which is a larger change than sizing.

## The four books

| book | sizing | median year | worst year | max DD | binds | cap-bound days |
|---|---|---|---|---|---|---|
| A stacked placeholder | every member holds its own | 55.56% | 28.46% | 3.60% | actual maxDD | 0 |
| B netted linear | level N = N units | 54.55% | 27.83% | 3.60% | actual maxDD | 423 |
| **C netted curve** | **1/3/6** | **64.23%** | **29.00%** | 3.60% | actual maxDD | 664 |
| D netted half curve | 1/2/3 | 55.07% | 27.70% | 3.60% | actual maxDD | 353 |

Team 2 (5.4% budget) is the same ordering at 1.5x scale: C 96.34%, A 83.34%,
D 82.60%, B 81.83%.

## Verdict

**C wins on both** — the best normal year by 8.7 points over the placeholder,
and the best worst year. The curve's convexity is doing the work: linear sizing
(B) is no better than not netting at all, and halving the curve (D) gives back
almost all of the gain. The agreement study's finding that level 3 earns roughly
four times level 1 per unit is what makes 1/3/6 pay and 1/2/3 not.

**The per-currency cap binds, and more often the steeper the curve** — 664 days
of 1,304 for C against 353 for D and 0 for the uncapped placeholder. That is the
cap doing its job: the curve concentrates risk into high-agreement days, and
high agreement across several pairs usually means the same currency.

**Note the cap was wrong in the first run** and is worth stating so the number
is not misread later: it was implemented as 2% of the day's own total book,
which is self-referential -- every position exceeds 2% of a book of six
positions, so it bound on all 1,304 days and acted as a uniform rescale that the
budget scaling then undid. It is now 2% of ACCOUNT EQUITY, which needs the final
scale, so the book is sized twice: once uncapped to find the scale, then capped
in account terms and re-sized.
