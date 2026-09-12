# HANDOFF — master record

## READ THIS FIRST

1. **THE TEAM IS NOT A RESULT.** The greedy roster search failed its SELECTION
   HOLDOUT on 2026-09-10 — 8% retained. **The 22.97% team score and the 30.22%
   Layer 4 figure are not demonstrated and must not be quoted as findings.**
   Its OTHER failure, the greedy null at p=0.60, is **void**: that null applies
   ONE year permutation to the whole matrix, so every member moves together and
   the median year is arithmetically unchanged. See §1 VALIDITY. The holdout
   alone is enough; the null said nothing.
2. **Greedy roster search is RETIRED.** Do not build another team with it, and
   do not treat any roster it produced as a portfolio.
3. **What still stands:** the 252 gate 3 passers are real, individually. Gate 3
   itself, the fine-tune, the cut and the adoption rule are unaffected.
4. **What does not:** the selection AMONG those passers, and every number that
   depends on a specific roster.
5. **Everything is scored on W3 only (2016-2020).** W2 is contaminated — `ip2`
   was tuned on it. FULLSTITCH is a hard follow-up, not done.
6. **Mode C is paused by decision** at 299 chunks until forward testing starts.
   It is in no chain. Restart it deliberately.
7. **Sharpe binds nothing** — not in adoption, not in the cut. Reported only.
8. **`run_pair` ran every mode as B until 8 Sep**; three chain stages once
   reported success while doing nothing. Trust no number produced before
   2026-09-10 without reading `FIXES.md`.
9. **The B-trend `ip1` recovery is packaged for a rented box** —
   `code/cloud_ip1.sh`, ~2 h, ~$3, one credential. 1,614 of 1,650 still to do.
   Not launched.
10. **THE DELIVERY PATH HAS NEVER CHARGED COSTS.** `l2trades.run_pair` returns
   gross R; only `l2sweep.score_combo` and `l2tune.Scorer` subtract
   `S._cost_R`. So `blind_trades`, `l2team._equity_series` and
   `l2layer4v2.marks` — and therefore every team KPI and every Layer 4 level —
   are **gross**. Drag is 2.6-8.5% of gross R and **18-19% of the median year**.
   `code/l2allpass.py` charges it; nothing else does.
11. **ALLPASS is the no-search construction and it is built** — §1A. Honest
   holdout 22% retained; the agreement signal clears its null at p=0.00.
12. Working style and Layer 1 history: `HANDOFF_3.md`. Layer 2 detail:
    `HANDOFF_LAYER2.md`. Material held outside this repo: see the last section.

---

# 1. STATE OF EVERY LAYER AND GATE

## Gate 3 fine-tune — COMPLETE
- All **5,135** gate-2 crossers re-tuned: widened grids, full costs (+50% markup, crisis x2), gap-aware fills, stop-first resolution, mark-to-market at window boundaries.
- **Adoption 12.5% on the W3-only basis** (was 0.18% while the incumbent was scored on a contaminated W2 — see §2).
- **494 strategies carry adopted settings** into the cut.
- Bank: `results/gate3ft_costed_v4/` — untracked during the run because eight shards appended every few seconds and broke every rebase; **now back under git** (8.2 MB).

## Gate 3 cut
- `code/l2cut.py`, a build product. `--settings adopted|gate2`.
- **252 passers** on adopted settings: 136 B, 63 A-trend, 52 A-chop, 1 C-trend.
- `settings_basis` column records which basis produced the file. Bars: expectancy >= 0.15R, PF >= 1.5, Sortino >= 1.3, Calmar >= 1.0, max DD <= 10% of own gross profit. **Sharpe reported, never binding.**

## The team — `W3ONLY_ADOPTED` — **NOT VALIDATED, DO NOT QUOTE**
25 members, empty start, no size cap. **The figures below failed both validity
checks — see VALIDITY below. They describe what the search produced, not an
edge.**

| | Team 1 (3.6/3.6) | Team 2 (5.4/3.6) |
|---|---|---|
| median year | **22.97%** | **34.45%** |
| average year | 19.40% | 29.10% |
| worst year | 11.44% | 17.17% |
| best year | 25.62% | 38.42% |
| max DD | 2.69% | 4.03% |
| DIP95 | 3.60% | 5.40% |
| worst day | 0.74% | 1.11% |
| clustering ratio | 0.75 | 0.75 |
| binding | DIP95 | DIP95 |
| corr > 0.90 | 0 | 0 |

Composition **13 B, 7 A-chop, 5 A-trend**; votes **4 full, 21 half**. Roster with votes and add order: `results/team1_W3ONLY_ADOPTED_roster.csv`, `team2_...`. KPIs: `team_kpis_W3ONLY_ADOPTED.csv`, per member `team_members_kpis_W3ONLY_ADOPTED.csv`.

## The gate-2 baseline — `W3ONLY_GATE2_FIXED`
26 members, built on gate 2's settings on the **fixed** code. It exists so the adopted-settings team has something to be measured against. Team 1 median 22.59%, worst 10.19%. The adopted team beats it on median, average, worst year, drawdown and worst day.

## Layer 4 sizing v2 — **levels inherit the roster problem**
Net votes per pair per day, size by agreement level, cap per currency, then scale to budget. **Marks to market daily, exactly as the team builder does** — book A reproduces the builder (22.27% vs 22.97%), which is the check that the path is right.

**Team 1:**

| | A stacked | B linear | **C curve 1/3/6** | D half |
|---|---|---|---|---|
| median year | 22.27% | 27.69% | **30.22%** | 26.18% |
| worst year | 12.15% | 17.42% | **18.67%** | 16.81% |
| max DD | 2.36% | 2.51% | **2.29%** | 2.48% |
| Sortino | 8.36 | 9.87 | **10.26** | 9.53 |
| Sharpe | 4.00 | 4.58 | **4.72** | 4.48 |
| Calmar | 40.93 | 49.70 | **60.60** | 48.07 |
| profit factor | 2.07 | 2.31 | **2.48** | 2.26 |
| win rate | 56.40% | 58.26% | **58.87%** | 58.10% |
| max positions | 33 | 15 | **15** | 15 |

**Team 2:** C 45.33% median / 28.00% worst; A 33.41% / 18.22%.

**These levels are built on a roster that failed validation.** The RELATIVE
finding may survive — netting and the 1/3/6 curve beat stacking on a FIXED
roster, which is a comparison of sizing methods rather than of selections — but
no absolute Layer 4 number should be quoted.

**The 2% cap is KEPT.** Largest single-currency exposure ever reached is **2.62%**, so 3% and 4% never bind and equal uncapped; **2% binds on 9 days of 1,304** and costs 0.03pp of median year. A genuine backstop, not a constraint.

**v1 is superseded** — it spread R across holding days, smoothing the series and inflating the scale (55.56% vs 30.22%). Its ranking was right; its levels were not comparable to anything.

## Agreement study — verdicts
**Agreement earns extra size, from level 2, strongest at 3.**

| level | IS R/unit | OOS R/unit | IS episodes |
|---|---|---|---|
| 1 | 0.0305 | 0.0279 | 715 |
| 2 | 0.0789 | 0.0646 | 268 |
| 3 | 0.1930 | 0.1236 | 98 |
| 4 | 0.6846 | 0.1452 | 23 |

**Null: slope 1.9095 IS / 0.6238 OOS, both at the 100th percentile of a 1,000-shuffle membership null, p=0.0000.** **Do not size on level 4+** — 23 IS episodes and the IS figure is 4.7x its OOS value. The curve stops at 3 for that reason.

**Opposition: follow the majority at net size.** +0.028 R/unit, 54.9% hit, worst dip 9.2 R — versus taking both sides (-0.034, 31.6%, dip 54.4 R) and sitting out (zero). By split: 3v1 +0.123, 2v1 +0.052, 1v1 +0.012, 2v2 **-0.122** (only 5 episodes). 1v1 and 2v1 are 537 of 567 episodes and both favour the majority.

**No per-member opposition weighting.** One member of 25 clears 50% in both periods (`coral x lemantrend x williams_vix_fix x rma`, 67%/60%); IS→OOS correlation 0.376. That is chance.

**Two confirmation-dependent members**, flat alone and profitable in company — `kuskus_starlight x coral x variance x mcginley` and `volatility_quality x aroon x waddah_attar_explosion x fantail_vma`. They count as **zero when alone** in Layer 4. **Zero members earn alone and lose in company.**

## VALIDITY — ONE CHECK FAILED, ONE CHECK IS VOID

**Greedy null, p = 0.60 — THE TEST IS BROKEN. DISREGARD THIS RESULT.**

`l2teamcheck.py:88-93` draws ONE permutation and applies it to the whole
matrix. Every member moves together, within-year day order survives the stable
sort, and `score_team` then groups by the relabelled years — so the year blocks
are the SAME BLOCKS under new names. Each member's daily series, every
cross-member same-day alignment, every yearly total and therefore the MEDIAN
YEAR, which is the score, are arithmetically unchanged. Only the path-dependent
max drawdown moves. Verified on synthetic data (real yearly sums
`[2.1511 0.6611 2.4805 1.9284 2.4635]`, null yearly sums the same five numbers
reordered) and reproduced on the real ALLPASS book, where the same null returns
p = 0.66. **p = 0.60 is what this test returns when the data has not changed.**

A per-member permutation destroys cross-member timing as the docstring intends,
but it also destroys the CORRELATION that sets the drawdown the budget divides
by, so the null book scores five times the real one and returns p = 1.00.
**Neither year-shuffle variant is a usable edge test for a drawdown-scaled
portfolio.** The working replacement is the level-permutation null in
`code/l2allpass.py` — see §1A.

The numbers as they were reported:

**Both teams, 2026-09-10. Team 2 completed 21:05 in 459 min.**

| | Team 1 | Team 2 |
|---|---|---|
| real team score | 22.82% | 34.20% |
| greedy-null mean | 22.79% | 34.58% |
| null p95 / max | 23.96% / 24.63% | 36.05% / 36.38% |
| p-value | 0.60 | 0.68 |

In BOTH cases the null MEAN sits at or above the real score — Team 2's by
0.38pp. That is the artefact, not a finding: the null data is the real data with
its year blocks relabelled, so the median year cannot move and only the
path-dependent max drawdown does. **Disregard both p-values.**

**Selection holdout: 8% retained, BOTH teams. This is the valid test and both
teams fail it.**

| | Team 1 | Team 2 |
|---|---|---|
| roster re-picked on 2016-2018 | 41.83% on its own picking window | 62.76% |
| the same roster on 2019-2020 | **3.33%** | **4.98%** |
| **retained** | **8.0%** | **7.9%** |
| full team on that holdout | 17.55% | 26.20% |
| members picked | 21 | 21 |

Team 2's looser drawdown budget scales every figure up and changes nothing:
the retention is identical to a tenth of a point.

**What passed:** the random-team comparison only — both teams sit at the
100th percentile of 1,000 random draws (Team 1 mean 7.98%, max 12.06%; Team 2
mean 11.98%, max 17.28%). That test was
always the weak one: a greedy search beats random selection even on noise, which
is precisely why the second null exists — and the second null turned out not to
exist in working form. **The selection holdout is the only valid evidence
against the roster. It is sufficient on its own.**

Files: `results/teamcheck_adopted.log`, `team_checks_W3ONLY_ADOPTED.*`.

## 1A. ALLPASS — the no-search construction — BUILT 2026-09-10

All 252 passers, equal weight, no selection. `code/l2allpass.py`, four stages.
Full record: `results/allpass_summary.md`. **Costs charged**, unlike every
earlier delivery-side number.

**2016-2020, net of costs, median year:**

| | curve 1/3/6 + 2% cap | stacked (no netting) |
|---|---|---|
| team1 (3.6/3.6) | **6.87%** | 8.24% |
| team2 (5.4/3.6) | **10.30%** | 12.35% |

worst year 4.57% / max DD 2.57% / PF 1.50 / Sortino 4.20 / Sharpe 2.39 /
Calmar 13.61 / win rate 54.7%, team1 curve. Gross-of-cost medians are 8.51% and
12.76% — **costs take 18-19% off the median year.**

**Honest holdout — re-cut on 2016-2018 across all 5,201 crossers, scored on
2019-2020:**

| | curve | stacked |
|---|---|---|
| re-cut on 2016-2018, scored there | 9.89% | 14.49% |
| **the same book on 2019-2020** | **2.22%** | **0.37%** |
| **retained** | **22%** | **3%** |
| real (2016-2020) cut on 2019-2020 | 6.60% | 10.36% |
| holdout worst year | 1.19% | **-0.50%** |
| holdout profit factor | 1.17 | 1.04 |

Control: the same path re-cutting on the full W3 gives 271 passers containing
**all 252** of the real cut, so the machinery is verified as a superset.

**THE CUT IS ITSELF A FIT TO ITS WINDOW.** The 2016-2018 re-cut passes 262
strategies of which only **76** are among the real 252. Which strategies clear
gate 3 is about 30% reproducible when the window moves. Removing the roster
search removed one layer of fitting and exposed the one underneath.

**NETTING SURVIVES THE HOLDOUT; STACKING DOES NOT.** Stacking wins in-sample
and is worth almost nothing out of it — negative worst year, PF 1.04, win rate
exactly 50.0%, Sharpe 0.21. The in-sample ranking of the two constructions is
the reverse of the out-of-sample ranking.

**Nulls, 100 draws each, both budgets:**

| null | real | null mean | null max | p |
|---|---|---|---|---|
| joint year shuffle (l2teamcheck's) | 6.802% | 6.817% | 6.907% | 0.66 |
| per-member year shuffle | 6.802% | 35.100% | 39.297% | 1.00 |
| **level permutation** | **6.865%** | **3.090%** | **4.418%** | **0.00** |

The level permutation keeps every netted position's pair, day, direction and
mark, and permutes only the AGREEMENT LEVELS across positions — same level
distribution, same size mix, only the assignment changes. **100 of 100 draws
beaten at both budgets.** Knowing which positions carry high agreement more
than doubles the score. **The agreement signal is real; the 1/3/6 curve is what
wastes it.**

**THE 1/3/6 CURVE DOES NOT TRANSFER.** Level is an absolute net-vote count, so
at 252 members it runs to 171 and the curve is flat at 6.0 from level 3 up:
level 1 is 14.7% of position-days, level 2 is 16.4%, **level 3+ is 68.9%**. Two
thirds of the book is pinned to one size. The agreement study calibrated
"stop at 3" where level 4 meant near-unanimity of 25; at 252 members level 4 is
four net votes out of 252. Sizing on the FRACTION voting rather than the count
is the obvious repair and is NOT built.

**THE 2% CAP IS DEAD WEIGHT AT THIS SIZE.** Largest currency exposure ever
reached is 0.53% (team1) / 0.80% (team2), against 2.62% on the 25-member
roster. It binds on **0 days of 1,296**. Keep it as a backstop; it does no work
here.

**Not established:** any tradeable absolute level. 2.22% is one median of two
observations.

## 1B. WALK-FORWARD ON THE THREE SLICES WITH ip1 — 2026-09-11

`code/l2walkfwd.py`. A-trend 1,804 + A-chop 678 + B-chop 1,003 = **3,485**, all
with `ip1` banked. B-trend's 1,650 have none and join via `--slices
A-trend,A-chop,B-chop,B-trend` once the cloud bank lands; `load_field` already
falls back to `gate2_ip1_recovered*.csv`.

**Clean stitch, W2 under `ip1` and W3 under `ip2`, cost-charged and
account-normalised.** W1 is excluded: it is `ip1`'s own tuning window. Two steps,
every decision — cut, members, curve, SIZE — taken on build years only:

    step 1  build 2011-2015 (ip1)              trade 2016-2018 (ip2)
    step 2  build 2011-2015 + 2016-2018        trade 2019-2020 (ip2)

### The four structures, stitched 2016-2020, team1 budget

| | members | median yr | worst yr | max DD | PF |
|---|---|---|---|---|---|
| **ALLPASS** | 620/575 | **+2.27%** | **+0.92%** | 3.32% | 1.22 |
| PICKED (greedy on build years) | 12/13 | +1.24% | -1.21% | 4.43% | 1.16 |
| FAMILY_CAP | 7/7 | -0.36% | -1.37% | 3.10% | 1.02 |
| STABLE | 441/16 | -0.49% | -2.45% | 3.70% | 0.98 |

**Every structure that SELECTS loses to taking every passer.** ALLPASS is the
only one with a positive worst year.

### THE TWO NULLS, AND THEY POINT IN OPPOSITE DIRECTIONS

**RANDOM ENTRY — "is this better than nothing at all?" — p = 0.000.**
Same strategies, pairs, directions, stop and target distances and maximum holds;
entries moved to random bars. Real **2.274%** against a null mean of **-0.159%**,
p95 0.252%, max 0.312%. **25 of 25 beaten, both budgets.** The entry signals
carry real information. The unit scale is derived exactly (`k = 1/ATR`, since the
engine sizes `units = RISK/(atr_mult x ATR)`) and validated against the bank at
each trade's real entry: correlation **0.937** on the ip2 era.

**IDENTITY — "does build-year quality predict trade-year quality?" — p = 1.000.**
Traded years held at 2016-2020; only the link between a strategy and its
build-year metrics is permuted, so a strategy passes on someone else's record and
trades its own marks. Real 2.274% against a null mean of **8.546%**, p95 9.516%.
**0 of 25 draws lost.** A random 620 of the field beats the 620 that passed gate
3, by nearly 4x — at half the drawdown and PF 1.83 against 1.22.

**Not a sizing artefact.** Scales are the same (1.016/1.154 real against
1.037/1.168 null); the gap is raw return, 0.0098 against 0.0341 per unit.

### THE CAUSE: GATE 3 CONCENTRATES THE BOOK INTO THE SLICE THAT DIED

| | A-trend | B-chop | A-chop |
|---|---|---|---|
| field | 51.8% | 28.8% | 19.5% |
| passers, build 2011-2015 | **78.4%** | 12.6% | 9.0% |
| passers, build 2011-2018 | **79.7%** | 12.9% | 7.5% |

mean R per trade-year row:

| | A-chop | B-chop | A-trend |
|---|---|---|---|
| 2016-2018 | +0.193 | +0.174 | **+0.025** |
| 2019-2020 | +0.080 | +0.049 | **-0.023** |

**79% of the book goes into the one slice that earns nothing on the traded years
and loses money in 2019-2020.** A random draw keeps the field's 52/29/20 mix and
so keeps its A-chop and B-chop weight, which is where the return is. That is the
whole gap. **The strategies work; the filter that chooses among them is broken.**

**A PER-SLICE CUT CANNOT FIX IT AND MUST NOT BE BUILT AS ONE.** Gate 3's bars are
ABSOLUTE — expectancy 0.15R, PF 1.5, Sortino 1.3, Calmar 1.0, maxDD 10% of own
gross — so no strategy's pass depends on any other and applying them within a
slice returns the **identical 620 sids**. Tested, not assumed. The concentration
is not crowding-out; A-trend simply clears absolute bars more often on 2011-2015.
Two constructions that DO bind are registered in FIXES.md: **SLICE_BALANCED**
(all passers, equal risk share per slice) and **PER_SLICE_CUT** (equal member
count per slice, 56 each at step 1, 43 at step 2).

### Team-size sweep — the answer is ALL

Ranked on build years by Sortino, tie-break Calmar, fixed in advance.
Coarse N = 10..100 and ALL; fine walk by 1 across the peak's neighbours.

**Coarse peak N = ALL (13.77% total return). Fine walk 519 sizes, peak N=619 at
13.78% — 0 of 519 beat their random p95, 0 had null p < 0.05, so the decision
rule rejected it and the answer stays ALL.** Every fixed size 10-100 has a
NEGATIVE worst year and PF between 0.99 and 1.08. At N=75 and N=100 the random
draw's median beats the ranked pick outright. `walkforward_teamsize.csv` carries
both units in every column name.

### Sizing — DIP95 binds, and what it costs

| | median yr | worst yr | max DD | worst day | DIP95 | binds |
|---|---|---|---|---|---|---|
| (a) all three vs 3.6% | 2.274% | +0.92% | **3.32%** | 0.80% | 4.79% | DIP95 |
| (b) risk 5.4 / day 3.6 | 3.412% | +1.37% | 4.97% | 1.20% | 7.19% | DIP95 |
| (c) actual path only | 3.800% | +1.44% | **5.20%** | 1.25% | 7.67% | actual maxDD |

**(c) breaches the limit it was sized against** — 5.20% realised against 3.6%,
44% over — so its +1.53pp is unusable as specified. (b) stays inside both its
limits with 0.43pp and 2.40pp of headroom, but its 5.4% budget only exists once
the trailing limit has locked at +6%.

Build-block diagnostics, ALLPASS: DIP95 binds at both steps at exactly 3.600%
while max DD uses 2.15/2.30 and worst day 0.92/1.26. 277 and 334 trades a year,
11.8 and 11.5 mean open positions, 0.83% and 1.02% mean gross exposure. **The 2%
currency cap binds on 0 days of 1,296** at peak exposure 0.74%/0.94%. **43% of
position-days are sized to ZERO** — the two thinnest agreement bins lose money on
build years and the fitted curve declines to trade them.

### The year-shuffled null is SUPERSEDED — confounded

It permutes which years get TRADED, and 2011-2015 is far richer than 2016-2020:
null score rises monotonically with rich years traded (3.36/5.29/6.84/7.66 at
1/2/3/4, correlation 0.377) and **none of the 25 draws traded the real walk's
composition of zero**. Adjusted p is 0.52, not 0.80. Files carry a SUPERSEDED
header. Detail in FIXES.md.

### Measured run time

engine 32.3 min · real walks 7.3 min · sizing 7 s · team-size sweep 30.7 min ·
identity null 36.6 min per budget · random-entry null 2.6 min per budget.

## Mode C
**Paused by decision at 299 chunks.** Not a fault, not a stall. It stays paused until the full system is built and forward testing has started. It has been removed from every chain.

---

# 2. EVERY BUG FOUND AND FIXED THIS WEEK

| bug | what it contaminated | redone |
|---|---|---|
| **W2/ip2 contamination.** The stitch is W2 under `ip1`, W3 under `ip2`; everything downstream scored both windows with `ip2`, which had been tuned on W1+W2. Measured on the graft: W2 total R **452.0 vs 92.4 — +389%**. | leaderboards, co-equal ranking, the graft, portfolio previews, the gate 3 cut, adoption decisions | everything re-scored **W3-only**; adoption 0.18% → 12.5%; FULLSTITCH still owed |
| **Stale-incumbent back-fill error.** My back-fill re-scored candidates with `ip2` on both windows, producing numbers that disagreed with the bank in both directions, and I reported a "corrected" adoption list from them. **Retracted.** The bank was right; `ip1`/`rk1` are now banked so candidates stay reconstructible. | one erroneous report | retracted in full |
| **`run_pair` hardcoded mode B.** Exit rule is per mode; every A and C strategy ran with B's exits. One A-trend strategy: 46 trades/+97 R correct vs 148/-1.1 R. | `blind_trades`, `_equity_series`, team builder, portfolio previews, trade charts, crisis split, entry timing, calendar, agreement, tripwire | team rebuilt (only 7 of 25 members survived); graft book rebuilt; re-run queue covers the rest |
| **Chain fired on an incomplete bank.** Wait condition was "no shards running"; shard 5 died at 96.2% and its absence read as completion. | the first ADOPTED team | chain now waits for all 5,135 sids |
| **The cut was never scripted.** `gate3_costed_verdicts.csv` existed only from an inline script typed by hand; the chain read it stale and produced the gate-2 team labelled ADOPTED. | that team, identical member for member | `l2cut.py`; files renamed `ADOPTED_MISLABELLED` with a README |
| **Roster without settings.** The agreement study loaded rosters, then every engine call raised and was swallowed per pair, giving "no position-days". | agreement study, twice | settings joined from verdicts; refuses to run if any member lacks them |
| **Swap guard exited silently.** Its single-instance check used `pgrep -f`, which matched its own `nohup` wrapper, so it exited immediately while reporting success. | shards ran unguarded | pidfile-based single instance |
| **Persistence.** `nohup … &` inside tool calls did not survive; `launchd` could not read `~/Documents` (**TCC**, `Operation not permitted`). | chains died three times | `nohup /bin/bash -c 'exec …' & disown`. **The weekly `batchC` LaunchAgent has the same TCC problem and will fail** — needs Full Disk Access for `/bin/bash` |
| **Per-pair silent swallows.** Five `except` clauses, four silent; the three identical ones around `TR.run_pair` hid all three "success while doing nothing" faults. | three stages | count by exception type and **raise if every pair failed**; `l2stagecheck.py` guards all six chain stages |
| **Position-based sharding.** Restarted shards claimed overlapping work — 228 duplicates, 18.7 core-hours, byte-identical so nothing corrupted. | wasted time only | `md5(sid) % shards`; `--leftovers` for recovery |
| **Open positions counted as realised.** Trades open at a window boundary were booked at the final bar — the top adoption's entire +97 R was three positions opened in 2020 and still open in 2026. | 2.9% of W3 trades; 12 rows with `cw3_sortino > 200` | mark-to-market at the boundary, everywhere |

---

# 3. EVERY RULE DECIDED

| date | rule |
|---|---|
| 08 Sep | **Adoption**: account return strictly higher AND max DD no worse AND Sortino no worse. **Sharpe dropped.** |
| 08 Sep | **Sharpe binds nothing anywhere** — not in adoption, not in the gate 3 cut. Reported only, plus `sharpe_only_flag`. |
| 07 Sep | **Budgets** 3.6%/3.6% (Team 1) and 5.4%/3.6% (Team 2). |
| 09 Sep | **Sizing binds on the WORSE of actual max drawdown and DIP95**, then the worst-day budget. DIP95 shuffles day order and so understates clustered losses. |
| 07 Sep | **Score is the MEDIAN year**, not the mean. One extraordinary year must not carry a team. |
| 09 Sep | **Mark-to-market at window boundaries**, everywhere. |
| 09 Sep | **Team builder starts EMPTY, no size cap.** No graft seed — greedy cannot leave a seed it was handed. |
| 08 Sep | **Clean over shortcut**: recover `ip1` uncapped as mode B actually ran it, never a faster capped approximation wearing the name of a recovery. |
| 10 Sep | **A worker's absence is not evidence of finished work.** Wait on the artefact. |
| 08 Sep | **W3-only now; FULLSTITCH is a hard follow-up**, registered in FIXES.md. |
| 07 Sep | **Layer 1 must be re-confirmed on 2016-2020 only** when rebuilt on 5pm bars — OANDA daily starts 2002-06 against H.10's 1999. |
| 10 Sep | **Mode C paused until forward testing starts.** |
| 11 Sep | **NO SILENCED ERRORS.** No `2>/dev/null`, no `\|\| true`, no `-q` on git, no bare or swallowing `except` anywhere in `code/`. Every failure prints and halts. A line that has earned an exception carries `# NOSILENCE-OK: <reason>` and the reason is read. Enforced mechanically by `code/l2nosilence.py`, which `l2stagecheck.no_silenced_errors()` runs before any chain starts and which writes `CHAIN_HALT.marker` on a finding. |
| 11 Sep | **NO GIT TREE OPERATIONS WHILE A CHAIN IS RUNNING.** No `stash`, no `rebase`, no `checkout`. `git stash -u` deletes untracked files from the working tree — on 11 Sep it unlinked a running chain's logs out from under it and took an uncommitted module with it. Chains write a pidfile via `chain_pidfile`; `assert_no_chain` in `code/l2chainguard.sh` refuses the operation while one is live. Stage explicit paths with `git add <path>`, or wait. |
| 11 Sep | **COMMIT A CODE CHANGE BEFORE LAUNCHING A CHAIN THAT NEEDS IT.** A committed file cannot be lost to a stash. `need_flags` in `code/l2chainguard.sh` asserts every flag a stage passes actually exists in the script it calls — a stage that dies on its own arguments exits in one second and reads as a fast success. |
| 11 Sep | **EVERY WALK-FORWARD NAMES ITS FIELD IN THE FIRST LINE OF ITS LOG.** `load_field` prints the absolute path of the field file and the per-slice counts before any work, then asserts the loaded field matches that file exactly and halts on any difference. **The field file is a REQUIRED argument** — the old `field_sids=None` default meant `crosses_label == True`, the contaminated field, so a caller that forgot the argument silently got a different population; `_init_rand()` had forgotten it, which sent every random-entry null to the contaminated field regardless of what the run was launched with. `assert_field` in `code/l2chainguard.sh` checks the same file in pre-flight. A wrong field is the one error that produces a complete, plausible, correctly-formatted table for a population nobody chose. |
| 12 Sep | **POOL STAGES ARE CAPPED BY RAM, NOT BY CORES.** The Mac kernel-panicked twice (watchdog, memory pressure) under the random-entry null — 23:33 on 11 Sep and 11:45 on 12 Sep — because nine workers each paid a 6.9 GB transient at once. Every pool stage in `code/l2cfchain.sh` now gets `min(--jobs, 60% of RAM ÷ its per-worker GB)` workers (random-entry null: ~2 GB → 3 on 16 GB), and `code/l2memguard.sh` SIGSTOPs the stage when free memory drops below 3 GB and resumes it above 4 GB, so a leak pauses a run instead of panicking the machine. `code/cloud_walk.sh` runs the same chain on a rented box and is an option, not the default. |
| 11 Sep | **A LAUNCH IS NOT CONFIRMED UNTIL THE FIRST STAGE IS MEASURABLY RUNNING.** Starting a chain is not evidence it is running, and neither is a pidfile on its own — a chain can die in pre-flight, in a wait loop, or on its own arguments and leave both behind. Before reporting a chain as running, and before quoting any ETA, prove three things: the pidfile's PID answers `kill -0`; a named worker process is alive under it in `ps`; and the stage log has GROWN across at least 60 seconds of wall clock. Quote the stage the log actually reached, never the stage the script would reach. On 11 Sep the clean-field chain was reported as "running, ~2 hours" at 16:00 having halted in pre-flight at 15:25 with a 0-line log. |
| 11 Sep | **CHAIN LOGS LIVE OUTSIDE `results/` AND OUTSIDE THE SESSION SCRATCHPAD** — in `$HOME/fx-data-logs/`. A git operation on the repo cannot touch them, and the end of a Claude session cannot wipe them (it wiped one at 23:36 on 11 Sep, chain included). Launch chains detached: `( nohup bash code/<chain>.sh … & )`. |
| 11 Sep | **A POOL WORKER MUST PROVE IT LOADED THE PARENT'S FIELD.** macOS `multiprocessing` spawns, so a worker's module globals are the DEFAULTS, not what `main()` set — `_init_null` read the unsuffixed contaminated pickle while the real walk used the clean one, and the identity null compared the two. Every initializer now resolves through `_worker_tables()`, which re-derives the path from `WF_TAG` and halts the stage if the sid count differs from `WF_EXPECT_SIDS`. A null drawn from a different population than the real is not a null. |
| 08 Sep | **Enter at 19:00 NY (Tokyo)** — cheapest of six candidate times, ~6 pips/trade better than the 17:00 reference, which carries double the spread. |
| 08 Sep | **No calendar switches.** Every weekday is profitable in both periods; no holiday window justifies a cut. |
| 10 Sep | **Opposition nets to the majority.** |
| 10 Sep | **No per-member opposition weighting.** |

---

# 4. THE QUEUE, IN ORDER

1. **Selection holdout + null checks** — running now, all 9 cores. Waits on nothing.
2. **Tripwire on book C** — waits on Layer 4 v2 positions. Stays **PROVISIONAL**: its floating-loss baseline measures from entry, not prior close.
3. **`code/l2rerun.sh`** — entry timing, calendar, crisis split, suppressed-vol, tripwire, agreement, all on fixed code. Waits for the chain and the fine-tune; one at a time, one core.
4. **Cloud `ip1` recovery** — `code/cloud_ip1.sh`. **Hetzner CCX63, ~2 h, ~$3.21; AWS c7i.16xlarge ~3 h, ~$8.67.** One credential: `GH_TOKEN`. **Not launched.**
5. **FULLSTITCH**, after (4): full W2(`ip1`)+W3(`ip2`) re-score of every crosser → rebuild leaderboards, ranking and cut → re-run adoption for all 5,135 → re-run team and agreement → report roster differences against the W3-only team. Mode C banks `ip1` already and needs no recovery, but its 299 chunks need clean re-scoring.
6. **Parked**: the 670-candidate inversion test (screen only, never run); the 6 A_ENTRY_B_EXIT challengers.

---

# 5. FILES THAT MATTER

**Banks and scores**
- `results/gate3ft_costed_v4/` — the fine-tune bank, 5,135 rows, one file per shard
- `results/gate3ft_costed_v4_dedup.csv` — deduplicated, 2,930 unique sids
- `results/gate3ft_adoptions_v2.csv` — adoption under the v2 rule, with `rule` per row
- `results/gate3ft_alternates.csv` — candidates that beat the incumbent but failed DD or Sortino
- `results/gate2_w3only_scores_*.csv` — W3-only re-score of all 5,381 crossers
- `results/gate2_ip1_recovered.csv` — recovered `ip1` (graft 15 + 34 of B-trend)

**Verdicts and teams**
- `results/gate3_costed_verdicts.csv` — the cut, 252 passers, `settings_basis` recorded
- `results/team{1,2}_W3ONLY_ADOPTED_roster.csv` — the team, votes and add order
- `results/team_kpis_W3ONLY_ADOPTED.csv` / `team_members_kpis_...` — full KPI sets
- `results/team{1,2}_W3ONLY_GATE2_FIXED_roster.csv` — the gate-2 baseline
- `results/team_per_year.csv` — per-year returns, all teams
- `results/*ADOPTED_MISLABELLED*` + README — the void team, kept as record

**Layer 4 and studies**
- `results/layer4_sizing_v2.csv` / `_summary.md` — the current sizing answer
- `results/layer4_positions_curve.csv` — book C's daily positions
- `results/agreement_levels_*.csv`, `agreement_by_member_*.csv`, `agreement_opposition.csv`, `opposition_by_member_*.csv`
- `results/variant_A_ENTRY_B_EXIT.csv` — the mode bug kept as a deliberate experiment
- `results/entry_timing.csv`, `calendar_*.csv`, `tripwire.csv` — all need re-running on fixed code
- `results/cost_table.csv` — per-pair costs, +50%, provenance per row

**Scripts**
- `code/l2gate3ft.py` fine-tune · `code/l2cut.py` the cut · `code/l2team.py` team builder · `code/l2teamkpi.py` KPIs · `code/l2teamcheck.py` holdout+nulls · `code/l2agree.py` agreement · `code/l2layer4v2.py` sizing · `code/l2recoverip1.py` ip1 · `code/cloud_ip1.sh` the rented box · `code/l2rerun.sh` the re-run queue · `code/l2chain2.sh` the chain

**Guards**
- `code/l2stagecheck.py` — every stage's output verified; writes `CHAIN_HALT.marker`
- `code/l2swapguard.sh`, `code/l2ftguard.sh` — swap protection, pidfile single-instance
- `code/l2stoppool.sh` — parent-first pool stop, never orphans

---

# 6. OPEN QUESTIONS

**For Jack**
1. **FULLSTITCH** — launch the cloud `ip1` recovery? ~$3 and two hours buys the full W2+W3 stitch.
2. **Full Disk Access for `/bin/bash`** — without it the weekly `batchC` LaunchAgent cannot read `~/Documents` and will fail silently on schedule.
3. **The 12 rows with `cw3_sortino > 200`** — individually check them; that metric is a reliable detector of open-position distortion.
4. **The 6 A_ENTRY_B_EXIT challengers** — worth a proper gate 2 tune with B's exit? Their settings were tuned for A's exit, so they cannot be adopted as they stand.

**For the next session**
5. **Layer 1 rebuild on 5pm bars** — Layer 1 uses H.10 noon, Layer 2 uses OANDA 17:00 NY; five hours apart on every bar. Must be settled before Layer 3 routing. Measure the survivor set restricted to 2002+ BEFORE swapping.
6. **Layer 3 routing** — not started. Blocked on (5).
7. **Layer 6 engine design** — not started.
8. **The duplicated kalman row** — cause found (position sharding) and fixed; the dedup is in `gate3ft_costed_v4_dedup.csv`. Confirm nothing downstream still reads the raw bank.
9. **Tripwire's floating-loss baseline** — measures from entry, not prior close. Needs the Layer 4 restructuring anyway.
10. **W4 is untouched** and must stay so until Jack declares all tuning finished.

---

## MATERIAL THAT IS NOT IN THIS REPO

The following live in **Jack's Claude project**, not here. Do not reconstruct
them from memory or infer them from code — **ask Jack to paste them** when the
work reaches them.

**Layer 6 — the daily engine.** Design docs only; nothing is built. Not in this
repo.

**The prop-firm profile — FundedTradingPlus.** The rules that shape every sizing
decision:
- **Floating losses count toward BOTH limits** — the daily limit and the trailing
  limit. This is why the team builder and Layer 4 mark to market daily rather
  than booking on exit; realised-only accounting would size against a drawdown
  the account never sees.
- **All 28 pairs are available**, so nothing in the universe is unreachable.
- **The 6% trailing limit locks at +6%** — which is exactly the Team 2 budget
  case (DIP95 5.4%, worst day 3.6%): the looser drawdown budget only applies
  once the floor has locked at the starting balance.

The full document is in the project. The three points above are the ones already
load-bearing in this repo's code; anything else about the profile must come from
Jack rather than be assumed.

**Parked work, also documented in the project:**
- **Disk cache redesign** — one file per indicator+params holding all 28 pairs,
  with a real-scale cold-start test. To be done **before round 2**, not during.
- **XAU pass** — gold, outside the 28-pair G8 universe.
- **V5.2 Pine wiring** — TradingView export of the shipped configuration.
- **Per-pair chart selector** — an app feature for the Trades tab.

None of these is scheduled here and none blocks the current queue.
