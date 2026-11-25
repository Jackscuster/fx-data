# THE BOOK — item 5, Jack 25 November 2026

## The answer first

**The best book is `A`. At the firm's own maximum legal sizing it makes 1.135% a year. The target is 12%. It is 10.9 percentage points short — a factor of 10.6.**

**And no book at any sizing ever passes the +10% evaluation**, over six years of unseen data. Not one of the 6 prefixes, not at the Team 1 budget and not at the firm's limits.

**The gap is not a sizing problem and it is not a combination problem. It is a return problem.** Combination and sizing are arithmetic and both have been done correctly here; reaching 12% needs roughly ten times more return per unit of risk than the best thing this project has built.

## How the book is built, and the two choices that matter

**EQUAL RISK PER SLEEVE means weight 1/N on each sleeve's daily R series**, so the book's risk budget is held constant as sleeves are added and a sleeve has to EARN its place by being better than the dilution it causes. The alternative — every sleeve at full size, book = sum — makes every addition look additive because it is adding risk as well as return.

**THE ADDITION ORDER IS THE BRIEF'S OWN AND IS NOT SEARCHED**: "A, B, quiet-entry versions, group-assigned strategies, mean reversion", in that order. A greedy search over orderings would find the best book by construction, and the number it produced would be a maximum over orderings — the exact fault item 2 spent a document demonstrating. The marginal contribution of **every** sleeve to the A+B book is reported separately so the ordering is not the only view.

**THE DIP IS VERIFIED TWO WAYS AND THE WORSE ONE BINDS**, exactly as `l2team` does: the realised chronological drawdown of the daily series, and DIP95 over 400 shuffled day orders. Either can be the larger — on the graft book `l2team` found the realised drawdown worse than the shuffle, and on these sleeves it is the other way round — so the rule is to take the maximum rather than to assume which way it goes.

**The prop simulator is `r2reads.prop_run`, unchanged** — the FundedTradingPlus profile Jack confirmed with the firm: 6% trailing floor that stops trailing permanently once it reaches the starting balance, 4% daily from the previous close with floating losses counting, 10% evaluation target, 80% payouts every 7 days, $549 fee, 1:30 leverage. **Its breach counts are LOWER BOUNDS** because the input is a daily series: an intraday excursion that breached and recovered before the close is invisible.

## The sleeves on their own, unseen years 2010–2015

| sleeve | legs | days | R total | R/yr | true dip | DIP95 | **binding dip** | R per dip | worst day | years + | t yearly |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `A_quiet` | 1032 | 1284 | +35.058 | +5.843 | 21.900 | 26.798 | **26.798** | +1.308 | 3.732 | 2 of 6 | +0.824 |
| `A` | 1470 | 1457 | +39.874 | +6.646 | 22.616 | 35.125 | **35.125** | +1.135 | 3.732 | 3 of 6 | +1.076 |
| `MR120` | 336 | 1035 | +18.507 | +3.084 | 23.620 | 37.939 | **37.939** | +0.488 | 3.466 | 3 of 6 | +0.602 |
| `MR60` | 855 | 1272 | +14.210 | +2.368 | 26.914 | 45.132 | **45.132** | +0.315 | 4.575 | 3 of 6 | +0.648 |
| `B` | 3926 | 1523 | +23.934 | +3.989 | 44.541 | 90.655 | **90.655** | +0.264 | 6.779 | 4 of 6 | +0.468 |
| `B_quiet` | 2193 | 1293 | -1.755 | -0.292 | 31.807 | 75.165 | **75.165** | -0.023 | 5.510 | 4 of 6 | -0.091 |
| `MR20` | 6552 | 1558 | -9.627 | -1.604 | 63.603 | 122.925 | **122.925** | -0.078 | 8.269 | 2 of 6 | -0.167 |
| `group_assign` | 3034 | 1558 | -64.735 | -10.789 | 93.453 | 120.715 | **120.715** | -0.536 | 7.783 | 4 of 6 | -1.145 |

**DIP95 is ABOVE the realised dip on every one of the 8 sleeves**, by a factor of 1.22 to 2.36. That is the opposite of what `l2team` found on the graft book (which drew 5.35% where its DIP95 was 3.60%) and it has to be said the right way round: on these sleeves a RANDOM arrangement of the same days produces a worse drawdown than the arrangement that actually happened. The realised path was luckier than its own day distribution, not unluckier. **So DIP95 binds everywhere and every %-a-year figure in this document is sized off the HARSHER of the two measures** — which also means the R-per-dip numbers here are smaller than ones quoted elsewhere in the project against the realised dip. For A the realised dip is 22.616 R and the binding one is 35.125 R.

## The declared addition sequence

| step | added | members | R/yr | binding dip | **R per dip** | **Team 1 %/yr** | dR total | t of the difference | years improved | corr of the new sleeve with the book |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `A` | A | +6.646 | 35.125 | **+1.135** | **+0.681%** | — | — | — | — |
| 2 | `B` | A+B | +5.317 | 55.105 | **+0.579** | **+0.347%** | -7.970 | -0.307 | 3 | +0.377 |
| 3 | `A_quiet` | A+B+A_quiet | +5.493 | 40.105 | **+0.822** | **+0.493%** | +1.051 | +0.103 | 3 | +0.551 |
| 4 | `B_quiet` | A+B+A_quiet+B_quiet | +4.046 | 44.504 | **+0.546** | **+0.327%** | -8.678 | -1.238 | 3 | +0.679 |
| 5 | `group_assign` | A+B+A_quiet+B_quiet+group_assign | +1.079 | 52.217 | **+0.124** | **+0.074%** | -17.802 | -1.692 | 1 | +0.434 |
| 6 | `MR120` | A+B+A_quiet+B_quiet+group_assign+MR120 | +1.413 | 42.298 | **+0.200** | **+0.120%** | +2.005 | +0.299 | 4 | -0.007 |

**Every addition in the declared order makes the book worse than A on its own.** A alone is R per dip +1.135 and 0.681% a year at the Team 1 budget; the full six-sleeve book is +0.200 and 0.120%. Not one step's paired t statistic comes close to 2, in either direction.

## Every sleeve's marginal contribution to the A+B book

Judged on **return per dip**, because a book is judged on what it earns for the risk it has to be allowed to take, and because total R alone would reward whichever combination holds the most risk.

| added to A+B | R/yr | binding dip | **R per dip** | Team 1 %/yr | dR total | t of the difference | corr with the A+B book | better? |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `A_quiet` | +5.493 | 40.105 | **+0.822** | +0.493% | +1.051 | +0.103 | +0.551 | **BETTER** |
| `MR120` | +4.573 | 36.580 | **+0.750** | +0.450% | -4.466 | -0.298 | +0.002 | **BETTER** |
| `MR60` | +4.334 | 37.624 | **+0.691** | +0.415% | -5.898 | -0.381 | -0.022 | **BETTER** |
| **`(none)`** | +5.317 | 55.105 | **+0.579** | +0.347% | +0.000 | — | — | — |
| `MR20` | +3.010 | 39.092 | **+0.462** | +0.277% | -13.843 | -0.485 | -0.366 | worse |
| `B_quiet` | +3.447 | 55.653 | **+0.372** | +0.223% | -11.220 | -1.184 | +0.715 | worse |
| `group_assign` | -0.052 | 63.499 | **-0.005** | -0.003% | -32.213 | -1.768 | +0.445 | worse |

**3 of the 6 candidate additions improve the A+B book's return per dip**: `A_quiet` +0.822 (corr +0.551); `MR120` +0.750 (corr +0.002); `MR60` +0.691 (corr -0.022). And every one of them still leaves the book below **A on its own** (+1.135).

**The two findings in that table are worth separating.** `A_quiet` improves the A+B book but correlates **0.856** with A — it is not a second sleeve, it is A with a quarter of the trades removed, so what it is really showing is that A+B is worse than A and anything that dilutes B helps. `MR120` and `MR60` improve it at a correlation of **+0.002** and **-0.022** — those ARE genuine diversification, exactly as item 4 predicted, and they are still not enough to beat one sleeve.

## The sleeve correlation matrix

| | `A` | `B` | `A_quiet` | `B_quiet` | `group_assign` | `MR60` | `MR20` | `MR120` |
|---|---:|---:|---:|---:|---:|---:|---:|---:||
| `A` | **1.000** | +0.370 | +0.856 | +0.301 | +0.315 | -0.197 | -0.338 | -0.124 |
| `B` | +0.370 | **1.000** | +0.281 | +0.757 | +0.408 | +0.068 | -0.296 | +0.062 |
| `A_quiet` | +0.856 | +0.281 | **1.000** | +0.318 | +0.234 | -0.184 | -0.296 | -0.135 |
| `B_quiet` | +0.301 | +0.757 | +0.318 | **1.000** | +0.339 | +0.075 | -0.246 | +0.075 |
| `group_assign` | +0.315 | +0.408 | +0.234 | +0.339 | **1.000** | -0.058 | -0.177 | -0.027 |
| `MR60` | -0.197 | +0.068 | -0.184 | +0.075 | -0.058 | **1.000** | +0.301 | +0.600 |
| `MR20` | -0.338 | -0.296 | -0.296 | -0.246 | -0.177 | +0.301 | **1.000** | +0.079 |
| `MR120` | -0.124 | +0.062 | -0.135 | +0.075 | -0.027 | +0.600 | +0.079 | **1.000** |

**The diversification the book plan needs is genuinely there.** All three mean-reversion sleeves are negatively correlated with A and `MR20` is negatively correlated with every trend sleeve in the table. **It is not the binding constraint.** `A_quiet` at 0.856 with A is the one thing in the matrix that is not a sleeve at all.

## Through the prop simulator, at the Team 1 budget and at the firm's limits

| book | Team 1 %/yr | **firm limits %/yr** | days to pass +10% | at firm limits | funded breaches | payout $/yr | internal (3.6/5.4) breaches | **short of 12% by** | **times short** |
|---|---:|---:|---|---|---|---:|---|---:|---:|
| A | +0.681% | **+1.135%** | **NEVER** | **NEVER** | none | $843 | none | 10.865 pp | **10.6x** |
| A+B | +0.347% | **+0.579%** | **NEVER** | **NEVER** | none | $386 | none | 11.421 pp | **20.7x** |
| A+B+A_quiet | +0.493% | **+0.822%** | **NEVER** | **NEVER** | none | $527 | none | 11.178 pp | **14.6x** |
| A+B+A_quiet+B_quiet | +0.327% | **+0.546%** | **NEVER** | **NEVER** | none | $350 | none | 11.454 pp | **22.0x** |
| A+B+A_quiet+B_quiet+group_assign | +0.074% | **+0.124%** | **NEVER** | **NEVER** | none | $100 | none | 11.876 pp | **96.8x** |
| A+B+A_quiet+B_quiet+group_assign+MR120 | +0.120% | **+0.200%** | **NEVER** | **NEVER** | none | $144 | none | 11.800 pp | **59.9x** |

**Three things to read off it.**

1. **No book passes the evaluation, ever, at either sizing.** The best makes about 6.8% in six years where the target is +10% with no time limit. The evaluation is not the binding problem — the return is.
2. **No book breaches anything, at either the firm's limits or the tighter internal ones.** That is not a safety result, it is the same fact from the other side: a book sized so its worst historical drawdown fits in 3.6% or 6% is a book that barely moves.
3. **The payout on the best book is $843 a year against a $549 fee** — $294 a year net. On the full six-sleeve book it is $144, which is less than the fee.

## What this settles

1. **Settled: the book machinery works and is not the problem.** Equal-risk combination, the two-way dip verification, the Team 1 and firm-limit sizing and the prop simulator all run end to end on every sleeve this project has produced, and every number above comes from files.
2. **Settled: the diversification is available and it is not enough.** Mean reversion is negatively correlated with A, improves the A+B book's return per dip, and the resulting book is still worse than A on its own.
3. **Settled: the best book is ONE SLEEVE**, and every addition in the brief's own order makes it worse at equal risk.
4. **Settled: the distance to 12% is a factor of about ten**, at the largest size the firm's rules permit, on six years of unseen data.
5. **NOT settled, and this is the live question: where another order of magnitude of return per unit of risk would come from.** Nothing in items 1 to 5 found it. Item 3 did find that the cross-sectional dispersion is enormous — a per-pair assignment with hindsight is worth +520 R over the same six years against the −72 R any tested rule achieved — so the room exists in the data. No tested selection rule reaches any of it, and that, rather than combination or sizing, is where the remaining distance lives.

## Provenance

- `results/nnfx/book_sleeves.csv` — 8 rows, md5 `e65cabf1a198`
- `results/nnfx/book_incremental.csv` — 6 rows, md5 `0cb82f82ff3d`
- `results/nnfx/book_marginal.csv` — 7 rows, md5 `4547b1c8e24d`
- `results/nnfx/book_prop.csv` — 6 rows, md5 `d63cc351596d`
- `results/nnfx/book_corr.csv` — 8 rows, md5 `b5ad0ef1fd04`
