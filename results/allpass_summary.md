# ALLPASS — the no-search construction

Every gate 3 passer, equal weight, no selection. Built 2026-09-10 by
`code/l2allpass.py`. Basis `adopted`, window W3 (2016-2020), 252 members:
136 B, 63 A-trend, 52 A-chop, 1 C-trend.

**Costs are charged here and were not charged before.** `l2trades.run_pair`
calls the engine directly and returns GROSS R — only `l2sweep.score_combo` and
`l2tune.Scorer` subtract `S._cost_R`. Everything on the delivery side
(`blind_trades`, `l2team._equity_series`, `l2layer4v2.marks`, and so the team
KPIs and the Layer 4 levels) is therefore gross. Measured drag is 2.6%–8.5% of
gross R per strategy and 18%–19% of the median year, because costs widen the
daily losses and so shrink the scale the risk budget allows as well. Both books
are reported.

**Intraday lows are invisible in close-only data.** Every figure is
close-to-close, so the true worst moment inside a day is worse than anything
below.

---

## 1. THE CONSTRUCTION, 2016-2020, net of costs

`C_netted_curve` = net votes per pair per day, size by the agreement curve
1/3/6, 2% per-currency cap. `A_stacked` = the same 252 at equal weight with no
netting and no cap, as the reference.

| | team1 curve | team1 stacked | team2 curve | team2 stacked |
|---|---|---|---|---|
| **median year** | **6.87%** | **8.24%** | **10.30%** | **12.35%** |
| average year | 6.99% | 9.52% | 10.48% | 14.28% |
| worst year | 4.57% | 5.32% | 6.85% | 7.98% |
| best year | 10.77% | 16.56% | 16.15% | 24.85% |
| total return | 34.93% | 47.60% | 52.39% | 71.40% |
| max drawdown | 2.57% | 2.40% | 3.85% | 3.60% |
| DIP95 | 3.60% | 3.60% | 5.40% | 5.40% |
| clustering ratio | 0.71 | 0.67 | 0.71 | 0.67 |
| worst day | 0.59% | 0.63% | 0.88% | 0.94% |
| worst month | 0.91% | 1.35% | 1.36% | 2.03% |
| Sortino | 4.20 | 4.91 | 4.20 | 4.91 |
| Sharpe | 2.39 | 2.78 | 2.39 | 2.78 |
| Calmar | 13.61 | 19.81 | 13.61 | 19.81 |
| profit factor | 1.50 | 1.67 | 1.50 | 1.67 |
| win rate | 54.71% | 55.32% | 54.71% | 55.32% |
| max positions | 27 | 600 | 27 | 600 |
| binding budget | DIP95 | DIP95 | DIP95 | DIP95 |
| cap-bound days | 0 of 1,296 | n/a | 0 of 1,296 | n/a |
| max currency exposure | 0.53% | n/a | 0.80% | n/a |

Gross of costs the same four medians are 8.51% / 10.08% / 12.76% / 15.13%.

**The 2% cap is dead weight at this size.** Largest single-currency exposure
ever reached is 0.53%, against 2.62% on the 25-member roster, and the cap binds
on 0 days of 1,296. Netting 252 members across 28 pairs spreads exposure far
below any level a per-currency cap would reach. Keep it as a backstop; it is not
doing work here.

**The 1/3/6 curve does not transfer to 252 members.** Agreement level is an
absolute net-vote count, so it runs to 171, and the curve is flat at 6.0 from
level 3 upward:

| level | position-days | share | size |
|---|---|---|---|
| 1 | 3,482 | 14.7% | 1.0 |
| 2 | 3,878 | 16.4% | 3.0 |
| 3 or more | 16,299 | **68.9%** | 6.0 |

Two thirds of the book sits on the flat part, so the curve is very nearly a
constant. The agreement study's "do not size above level 3" was calibrated where
level 4 meant near-unanimity of 25 members; at 252 members level 4 means four
net votes out of up to 252. It is a different quantity wearing the same name.
Sizing on the FRACTION of members voting rather than the count is the obvious
repair and has not been built.

---

## 2. THE HONEST HOLDOUT — re-cut on 2016-2018, scored on 2019-2020

ALLPASS has no selection to overfit, but the CUT saw all of 2016-2020, so
"which strategies passed" is an in-sample decision. This re-runs the gate 3 bars
on 2016-2018 alone across all 5,201 gate-2 crossers with adopted settings,
builds ALLPASS from whatever passes that, and scores it on 2019-2020.

**Control.** Re-cutting on the full W3 through this same path gives 271 passers
containing **all 252** of the real cut. The 19 extra rows come from the metric
source: `l2cut` takes the fine-tune bank's boundary-marked `cw3_*` for adopted
strategies, while this path recomputes every row through `l2tune.Scorer`.
Verified exactly on a sampled row — expectancy 0.3031919 against the bank's
0.3031919, with n, PF, Sortino, Calmar and max DD all matching to the printed
digit.

| | team1 curve | team1 stacked | team2 curve | team2 stacked |
|---|---|---|---|---|
| re-cut on 2016-2018, scored there | 9.89% | 14.49% | 14.83% | 21.73% |
| **the same book on 2019-2020** | **2.22%** | **0.37%** | **3.33%** | **0.56%** |
| **retained** | **22%** | **3%** | **22%** | **3%** |
| real (2016-2020) cut on 2019-2020 | 6.60% | 10.36% | 9.90% | 15.54% |
| holdout worst year | 1.19% | **-0.50%** | 1.78% | **-0.75%** |
| holdout profit factor | 1.17 | 1.04 | 1.17 | 1.04 |
| holdout Sharpe | 0.95 | 0.21 | 0.95 | 0.21 |
| holdout win rate | 52.12% | 50.00% | 52.12% | 50.00% |

**Two findings, and they point in opposite directions.**

**The cut is itself a fit to its window.** The 2016-2018 re-cut passes 262
strategies, of which only **76 are among the real 252**. Which strategies clear
gate 3 is about 30% reproducible when the scoring window moves. Removing the
roster search removed one layer of fitting and exposed the one underneath.
ALLPASS retains 22% against the greedy roster's 8% — better, still a collapse.

**Netting and the agreement curve survive the holdout; stacking does not.**
Stacking wins in-sample (8.24% vs 6.87%) and is worth almost nothing out of it
— 0.37% median year, a NEGATIVE worst year, profit factor 1.04, win rate
exactly 50.0%, Sharpe 0.21. The netted curve book keeps 22% of its picking-window
score with profit factor 1.17 and a positive worst year. The in-sample ranking of
the two constructions is the reverse of the out-of-sample ranking.

---

## 3. THE NULLS

100 draws each, p-resolution 0.01, both budgets.

| budget | null | real | null mean | null p95 | null max | p |
|---|---|---|---|---|---|---|
| team1 | joint year shuffle | 6.802% | 6.817% | 6.867% | 6.907% | 0.66 |
| team1 | per-member year shuffle | 6.802% | 35.100% | 37.647% | 39.297% | 1.00 |
| team1 | **level permutation** | **6.865%** | **3.090%** | **4.015%** | **4.418%** | **0.00** |
| team2 | joint year shuffle | 10.203% | 10.225% | 10.300% | 10.360% | 0.66 |
| team2 | per-member year shuffle | 10.203% | 52.729% | 56.480% | 59.865% | 1.00 |
| team2 | **level permutation** | **10.298%** | **4.634%** | **6.023%** | **6.627%** | **0.00** |

### The joint shuffle is a no-op. This is `l2teamcheck.py`'s null.

`l2teamcheck.py:88-93` draws ONE permutation and applies it to the whole matrix,
so every member moves together. Within-year day order survives the stable sort,
and `score_team` then groups by the relabelled years — so the year blocks are the
same blocks under new names. Verified on synthetic data:

    real yearly sums  [2.1511 0.6611 2.4805 1.9284 2.4635]
    null yearly sums  [2.4805 2.4635 1.9284 0.6611 2.1511]

Each member's daily series, every cross-member same-day alignment, every yearly
total and therefore the MEDIAN YEAR — which is the score — are arithmetically
unchanged. Only the path-dependent max drawdown moves, shifting `scale` by a
percent or two. Reproduced on the real ALLPASS book above: p = 0.66 against the
0.60 reported for the team. **The team's p = 0.60 measured the test, not the
team.**

### The per-member shuffle changes the wrong thing.

Permuting each member's year blocks independently is what the team check's
docstring describes, and it destroys cross-member timing as intended. But it
also destroys the CORRELATION between members, and correlation is what sets the
drawdown that the budget divides by. The null book scores FIVE TIMES the real
one (35.1% against 6.8%) purely because independent members draw down less.
p = 1.00 is not a verdict on the construction; it is a measurement that the 252
passers are heavily positively correlated.

**Neither year-shuffle variant is a usable edge test for a drawdown-scaled
portfolio.** One changes nothing; the other changes the wrong thing. This is a
property of the test family, not of any particular roster.

### The level permutation is the one that works, and it passes decisively.

Keep every netted position's pair, day, direction and mark exactly as they are,
and permute only the AGREEMENT LEVELS across positions. The level distribution —
and so the mix of sizes in the book — is identical; only the assignment of size
to position changes. Nothing about correlation, timing or drawdown structure is
touched.

The real assignment scores 6.865% against a null mean of 3.090% and a null MAX
of 4.418%. **100 of 100 draws beaten, at both budgets.** Knowing which positions
carry high agreement more than doubles the score relative to spreading the same
sizes at random. The agreement signal is real, and it is the sizing rule that
wastes it — 69% of position-days are pinned to the same size by a curve that
stops at 3.

---

## 4. WHAT THIS DOES AND DOES NOT ESTABLISH

**Established.**
- Agreement between passers carries real information about which positions to
  size up: level permutation p = 0.00, 100th percentile, both budgets.
- `l2teamcheck.py`'s year-shuffled greedy null cannot detect anything. Its
  p = 0.60 on the team is uninformative.
- The delivery path has never charged costs. The drag is 18%–19% of the median
  year, so every previously reported team and Layer 4 figure is gross.
- The gate 3 cut is unstable across sub-windows: 76 of 262 overlap.

**Not established.**
- Any tradeable absolute level. The honest out-of-sample figure is **2.22%**
  median year at the team 1 budget, from a two-year holdout, which is one median
  of two observations.
- That the 1/3/6 curve is the right curve. It is demonstrably the wrong shape at
  252 members; the level null says the underlying signal deserves a better one.
- FULLSTITCH. Everything here is W3-only, as in the rest of the current state.

## FILES

    results/allpass_kpis.csv                     the construction, both budgets, net and gross
    results/allpass_daily.csv                    daily series per budget and book
    results/allpass_levels.csv                   agreement level distribution
    results/allpass_marks.pkl                    252 members' daily marks, 251,624 rows
    results/allpass_field_subwindow_scores.csv   5,201 crossers scored on W3, 2016-2018, 2019-2020
    results/allpass_holdout_cut.csv              the 262 that pass on 2016-2018
    results/allpass_holdout_kpis.csv             all four legs, both books, both budgets
    results/allpass_holdout.json                 the retention summary
    results/allpass_null.csv                     every null draw
    results/allpass_null_summary.csv             the table above
    results/allpass.log                          the run
