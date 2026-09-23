# HANDOFF — master record

## READ THIS FIRST

0. **THE LAYER 2 BOOK HAD A ONE-BAR LOOK-AHEAD (found 15 Sep). Every book
   number in this file below item 0d was produced with it and is labelled
   VOTE-TIMING LEAK in `results/`. The fixed numbers, same walk, same
   pickles, both budgets (item 1 of 15 Sep; nulls in 0d as they land):**

   | book | as run (contaminated) | fixed |
   |---|---|---|
   | BASE | 5.12 / 7.69, worst 3.62 / 5.43, PF 1.49 | **−1.00 / −1.50**, worst −1.50 / −2.24, PF 0.94 |
   | CHOP-CORE | 6.98 / 10.46 | **−0.82 / −1.23**, PF 0.93 |
   | CHOP-ONLY (checking years) | 10.59 / 15.88 | **−0.44 / −0.66**, PF 0.95 |
   | sit-out (item 12) | 20.06 / 28.71 | −1.36 / −2.03 |

   The mechanism, the evidence and the fix are in **0d**; the rule is in §3.
   Per-strategy numbers (gate 2/3, member expectancy, Layer 1) stand.

   **16 Sep, morning — everything Jack queued on the 15th has run. From files:**

   *Fixed nulls, both budgets.* Random-entry (25 draws, same permitted bars):
   base −1.00 / −1.50 vs null max −0.02 / −0.02, **p = 1.000**; chop-core
   −0.82 / −1.23 vs max −0.08 / −0.12, p = 1.000; chop-only −0.44 / −0.66 vs
   a flat null, p = 1.000. Regime-shuffle (25 draws): base vs shuffled mean
   −0.60 / −0.89, max 0.13 / 0.19, **p = 0.880**; chop-core vs −0.74 / −1.12,
   max 0.02 / 0.03, **p = 0.520**. The real entries are worse than random
   entries; the real routing is no better than shuffled labels.

   *In-sample check (a).* The fixed base on its own build block 2011-2015:
   **+4.44% median year** at the build-block scale (2011-2018: +2.60%);
   trade years −1.00 → retention −0.43, flagged FIT. Ten-trade hand check
   PASS: every mark rebuilt from closes, ATR, stop multiple, legs and the
   cost table; first vote the day after the fill (`audit_handcheck_10.csv`).

   *Refit pilot (b), 250 strategies (A-trend 90, A-chop 28, B-chop 28,
   B-trend 104), 237 min on 4 workers, `refit_pilot*.csv`.* Mean 98 s per
   five-year tune (median 71, p90 133), median 539 configurations tried.
   Median R per trade net of costs on the unseen year, share positive:

   | trade year | settings | flat table as run | 17:00 measured | 22:00 measured |
   |---|---|---|---|---|
   | 2016 | 2005-10 (ip1) | −0.066, 39% | −0.086, 34% | −0.064, 40% |
   | 2016 | fresh tune 2011-15 | **−0.048, 42%** | −0.064, 40% | −0.045, 43% |
   | 2017 | 2005-10 (ip1) | −0.075, 38% | −0.096, 35% | −0.069, 39% |
   | 2017 | fresh tune 2012-16 | **−0.022, 45%** | −0.045, 43% | −0.018, 46% |

   Tuning-window medians under the fresh tune: 0.97 and 0.92 R/trade —
   retention −4% and −3%. By slice at 22:00: every slice negative on both
   years except B-trend 2016 (+0.009); A-chop goes from +0.01 (ip1) to −0.10
   after re-tuning. **Plainly: re-tuning does not restore an edge. The
   median R per trade on unseen years is negative before and after, at
   every cost level, in every slice. Re-tuning lifts the in-sample number
   4× and the unseen year by 0.02-0.05 R, to a number still below zero.**

   *Carry (item 4), alone, fixed kernel, 12 sleeves.* Every sleeve loses per
   trade on the build years AND the trade years: weekly −0.07 to −0.09 R
   (PF 0.84-0.88), monthly −0.22 to −0.43, quarterly −0.48 to −1.08. Not a
   member. `carry_routed_tirexcl_actweak.csv`.

   *Audit.* `results/audit_2026-09.csv`: **26 of 26 PASS — PRE-FLIGHT
   CLEAR** (`python3 code/preflight.py`, 15 s, rerun before any rebuild).

   **THE REPO HAS MOVED: `/Users/jackcuster/fx-data` (16 Sep 10:41).** Audit
   item 26. rsync out of the iCloud-synced ~/Documents took 134 min at the
   hydration rate (0.5-2 MB/s); 7,911 files verified, 0 dataless, checksums
   on 6 sampled files, git HEAD intact. Left behind in
   `~/Documents/fx-data_MOVED_2026-09-16` (Jack deletes it): the tuner disk
   cache (305k evicted files), `wf_randk_*` (regenerable), the retired
   routing variants (tirincl / actignore / repro / tg_notranging / legflip /
   unsuffixed), `scores_h10_archive`, `superseded`, `_isonly`, `crisis_all`.
   Every driver under `~/fx-data-logs` and every absolute path in `code/`
   now says `/Users/jackcuster/fx-data`. **Start every session in
   `~/fx-data`** — Claude's project memory is keyed by path, so the first
   session there starts with an empty memory index; HANDOFF is the record.
   `~/fx-data-logs/launch.sh` launches a driver and confirms it alive after
   60 s; `~/fx-data-logs/gitsafe.sh` refuses pull/rebase/checkout/stash while
   a chain runs (commit/push are always allowed).

   **(d) THE REBUILD'S CODE IS BUILT AND ITS 250-STRATEGY SMOKE IS RUNNING**
   (`~/fx-data-logs/refit_smoke.sh`, launched 10:50, markers "refit smoke
   <stage> done" … "REFIT SMOKE COMPLETE"). `code/l2refit.py`: `--stage
   tune` (per strategy per window: gate-2 grids cap 6, label on the window
   under its own settings, scored routed AND always-on on the window, the
   trade block and every sealed year to 2020; banked per (sid, window),
   md5-sharded, resumable), `--stage marks` (per step, build block + trade
   block under that step's settings as an always-on stream with a `step`
   column, unique tids), `--stage report`. Kernel: `Scorer.score(...,
   routed=False)`; `WF_STEPS="2011-2015:2016,..."` makes `l2walkfwd` roll
   (per-step marks, per-step random-entry null, decisions log, retention).
   A two-strategy end-to-end run passed (tune → marks → route → walk). The
   smoke: the pilot's 250, windows 2011-15 … 2015-19 (trades 2016-2020),
   the pilot's 2011-15 / 2012-16 tunes reused, everything scored on the
   22:00 measured table, then route → walk → per-slice → random-entry null →
   regime-shuffle null → report. Known approximation in the smoke: the
   random-entry null takes stop/target multiples from the field file's ip2
   risk columns, not the step's settings. **The full run is NOT started and
   nothing is rented** (Jack's word, and the pilot's answer, first).

   **Smoke, tune stage done 14:34 (225 min, 750 fresh tunes: mean 68 s,
   median 48, p90 93).** 250 strategies × 5 rolling windows, every number
   per strategy through the Scorer, `refit_report_refit_smoke.csv`:

   | window → trade | routed: build median R → trade median R (share +) | always-on: build → trade |
   |---|---|---|
   | 2011-15 → 2016 | 0.98 → **−0.045** (43%) | 0.28 → −0.083 |
   | 2012-16 → 2017 | 0.92 → **−0.018** (46%) | 0.24 → −0.004 |
   | 2013-17 → 2018 | 0.96 → **+0.041** (55%) | 0.24 → +0.036 |
   | 2014-18 → 2019 | 0.93 → **−0.082** (37%) | 0.24 → −0.078 |
   | 2015-19 → 2020 | 0.88 → **−0.005** (49%) | 0.22 → −0.016 |

   **Count of traded years won: 1 of 5.** Retention −9% to +3%. The decay
   curve is flat at about −0.02 R for every year after the window (1-5
   years) — there is nothing to decay, the edge is the tuning window's
   own. Every one of the 250 passes the gate-2 floors on its own window
   (an in-sample label passes everything) and every one reads as
   "regime-dependent" on its window (the tuner optimises in-regime), while
   on the unseen year routed and always-on land within ±0.04 R of each
   other.

   **REFIT SMOKE COMPLETE 14:45** (marks 6 min, route/walk/per-slice 25 s,
   random-entry null 80 s, shuffle 2 min — the machinery runs end to end).
   The rolling book of the 250, fixed kernel, 22:00 table, both budgets:
   build blocks (in-sample under each step's fresh settings) **+16 to +24%
   median year**; traded years 2016-2020 **−1.48 / −2.21**, worst −3.04 /
   −4.57, max DD 5.7 / 8.6, DIP95 13.2 / 19.7 (out of budget), PF 0.97,
   **retention −0.11, flagged FIT**. Per slice: A-chop +0.66, B-chop +1.12,
   A-trend −1.35, B-trend −0.54 (team1). Nulls: random-entry real −1.48 vs
   mean −2.39, max −1.04, p = 0.08; regime-shuffle vs mean −0.79, max
   +0.49, **p = 0.92**. `walkforward_*_refit_smoke_routed.csv`,
   `decisions_refit_smoke_routed.csv` (five steps, each with its window;
   `l2cfperslice` now writes its own decisions file instead of overwriting
   the book's). **The rebuild's answer on 250 is the pilot's answer: the
   edge is the tuning window's own, and nothing of it reaches the next
   year.** The full run (45,142 × 5 or 11 windows) is built, smoke-tested
   and NOT started; nothing rented.

   **FUNNEL TEST (Jack, 21 Sep; `code/l2funnel.py`, no new tunes, 12 min).**
   Gate 2's bars (n ≥ 50, expectancy ≥ 0.08, PF ≥ 1.25, Sharpe ≥ 0.5,
   Sortino ≥ 0.7, Calmar ≥ 0.6) applied to each of the 250 on its tuning-
   window record under its fresh settings, then the next year untouched.
   `funnel_groups_refit_smoke.csv`, `funnel_rankcorr_refit_smoke.csv`.

   *Passer counts.* ROUTED record: **250 / 250 / 250 / 249 / 250** — one
   non-passer in five windows. The funnel is degenerate: an in-sample record
   after coordinate descent clears every gate-2 bar for every strategy. That
   is not a sample-size problem and no sample size fixes it; only a BLIND
   label (tune on four years, label on the fifth) or gate 3's bars could
   make a funnel at all. ALWAYS-ON record: passers 227 / 210 / 218 / 215 /
   202, non-passers 23-48 per window, 178 pooled — enough to see a 0.05 R
   difference in next-year median (SE ≈ 0.02 R at the observed spread).

   *Next year, always-on, passers vs non-passers (median R/trade, share
   positive, pooled PF):* 2016 −0.083 / 24% / 0.75 vs −0.110 / 35% / 0.85;
   2017 −0.003 / 50% / 0.97 vs −0.011 / 45% / 0.95; 2018 +0.025 / 61% /
   1.12 vs +0.061 / 69% / 1.17; 2019 −0.078 / 23% / 0.78 vs −0.078 / 31% /
   0.87; 2020 −0.016 / 46% / 0.99 vs −0.016 / 42% / 0.96. **Pooled: passers
   −0.034 / 40% / 0.91, non-passers −0.016 / 44% / 0.96.** The label selects
   nothing; if anything it selects the slightly worse group. Routed
   passers = everyone: −0.045, −0.018, +0.041, −0.082, −0.005.

   *Rank correlation, tuning window vs next year (Spearman), five
   yardsticks (Sortino, expectancy, PF, Calmar, gate-3 composite).* Routed,
   pooled 1,250: **−0.03 to −0.01 on every yardstick**; per window between
   −0.10 and +0.04. Always-on, pooled: **−0.18 (Sortino), −0.10
   (expectancy), −0.11 (PF), −0.09 (Calmar), −0.08 (composite)**; 23 of the
   25 per-window values ≤ 0, the largest +0.08. The better a strategy looked
   on its tuning window, the slightly worse it did next year.

   *Passers pooled across the five windows as one rolling book, fixed
   kernel, 22:00 table, both budgets.* Always-on (227-202 members per step):
   build +4.6 to +8.6% median year; traded years **−0.05 / −0.08**, worst
   −2.35 / −3.52, DIP95 7.6 / 11.4 (out of budget), PF 0.98, retention
   −0.01 FIT; random-entry null mean −0.57 / −0.85, max −0.01 / −0.02,
   p = 0.04 (better than random entries, still not positive). Routed
   (= the whole 250): −1.48 / −2.21, worst −3.79 / −5.69, retention −0.11
   FIT; random-entry p = 0.16; regime-shuffle mean −0.81 / −1.22, max
   +0.32 / +0.47, p = 0.88.

   **On the $53:** the tuning-window record carries no information about
   the next year on any yardstick (rank correlation ≈ 0 routed, < 0
   always-on), the gate-2 funnel cannot select because it passes everyone
   in-sample, and the pooled passers book is at zero or below with the
   drawdown budget broken. The full rebuild would produce these same tables
   at 180× the size. Recommendation: do not spend it; if anything is spent,
   it is on a BLIND-label design, which is a different programme.

0-prev. **BATCH 1 / BATCH 2 (14 Sep) — as run on the contaminated kernel; kept for the record.**
   Session context was cleared at ~14:15 with Batch 1 mid-run. Everything
   below is from files. The base book is the four-slice clean field routed on
   the 5pm states, trend→TRENDING, chop→RANGING, WEAK blocks new trend
   entries, crisis on: pickles `_routed_tirexcl_actweak`, always-on stream
   `_cleanfield_4slice_allon` (7,648,503 trades). Both budgets are team1 /
   team2 (3.6/3.6 and 5.4/3.6). Nulls run on winners only.

   **Sanity checks (Jack's, done first).** (a) Rank persistence, each member's
   2011-2015 record vs its own 2016-2018 record, Spearman: Sortino −0.026,
   expectancy +0.003, PF −0.013, Calmar +0.003, gate-3 composite −0.011
   (n 8,234; per slice on expectancy −0.005 to +0.044). **Near zero, not
   negative: no persistence, and no join fault** — the identity null stands.
   (b) The cost table charges majors 1.95 pips (published ThinkMarkets ×1.5)
   and every cross a flat 4.2 (2× the widest major ×1.5). Measured OANDA
   hourly bid/ask 2016-2020 medians: majors 4.4 pips at 17:00, 2.0 at 19:00,
   1.7 at 23:00; crosses 8.7 / 3.3 / 2.7. The table is right on average for
   a 19:00 entry and wrong per pair by up to 2× both ways (GBPNZD pays 7.8,
   charged 4.2; NZDJPY pays 2.6, charged 4.2). `entry_timing.csv` (19:00,
   graft entries, to 2026) reads 4.36 / 2.26 — same source, consistent. On the
   base book the drag is:

   | cost model (base book) | mean cost | median yr | drag of zero-cost median |
   |---|--:|--:|--:|
   | zero | 0.0 bp | 6.60 / 9.90 | 0.0% |
   | as_run | 3.1 bp | 5.12 / 7.69 | 22.4% |
   | raw_spread | 2.1 bp | 5.59 / 8.39 | 15.3% |
   | entry_1900 | 3.9 bp | 4.82 / 7.23 | 26.9% |
   | oanda_1900 | 2.8 bp | 5.29 / 7.93 | 19.8% |
   | oanda_1700 | 7.4 bp | 3.72 / 5.59 | 43.6% |
   | oanda_best_hour | 2.3 bp | 5.51 / 8.27 | 16.5% |

   17:00 entry (the daily close, the engine's reference) would nearly double
   the drag; the best hour is 21:00-23:00 NY. `results/spread_by_hour.csv`,
   `spread_reconciliation.csv`, `returns_costs_routed_tirexcl_actweak.csv`.

   **Item 1 — SWAP DONE (`fc44717`, 1 h 10).** `layer1_states.csv` is the 5pm
   file (header, `sample=sealed` from 2021); H.10 is `layer1_states_h10.csv`;
   every reader passes `comment='#'`; `px28.csv` is the 5pm panel
   (`build5pm.py`), H.10 is `px28_h10.csv`; `pipeline.py` runs `build5pm.py`.
   Six checks passed (regime_codes == direct read 1,600/1,600; every reader
   opens; new reader on old file 500/500; interface == validated 5pm file;
   one strategy through the engine matches its post-filter, 205 H.10 / 190
   5pm; gate-1 constants untouched, unlabelled OANDA bars 3.7% → 0.0%). All
   score batches regenerated on 5pm in the main tree (`sc2-7`, 28/28 each;
   H.10 batches parked in `results/scores_h10_archive/`, gitignored); the
   pool/prep/dedup pass ran at 14:35 (after one filesystem-timeout retry):
   `signals.json` 175,634 records on the 5pm panel, **8 gate-7 survivors**
   (H.10 had 29), clustered by `dedup.py`. **NOT yet done for
   the swap: the Layer 1 analysis chain on the 5pm panel in the main tree**
   (`bash ~/fx-data-logs/l1analyse.sh /Users/jackcuster/Documents/fx-data
   MAIN5PM`, 111 min, then the second pass persist/regenerate/persist2/refit/
   windowsens/scoreq/today/knobs/episodes/mechanism/layer1sum) — the analysis
   CSVs in `results/` are still the H.10 ones with SUPERSEDED headers until
   it runs. Queue it after item 8, one job at a time.

   **Item 2 — expectancy (0.1 min).** On its own trade years 2016-2020, net
   of costs: 2,996 of 8,235 members (36%) have positive expectancy; median
   −0.047 R/trade (A-chop −0.059, A-trend −0.052, B-chop −0.035, B-trend
   −0.044), median PF 0.87. 1,506 (18%) clear the gate-2 floors (PF ≥ 1.05,
   ≥ 50 trades) on the trade years; **58 (0.7%) clear the gate-3 bars**.
   → per Jack's rule, the re-tune is the fix and this is the reason: nearly
   two-thirds of the field loses per trade on the years it is judged on; the
   book's return is the netting and the sizing curve on a losing population.
   `results/members_expectancy_routed_tirexcl_actweak.csv`.

   **Item 3 — attribution (2.4 min).** By build-year quality decile, all five
   yardsticks, the shape is a HUMP: deciles 4-7 carry ~55-60% of the
   trade-year return; the top decile 1.6-6.5%, the bottom 3-4%. Mean R per
   trade on the trade years is negative in every decile (best −0.01 to −0.02
   in deciles 7-8, top decile −0.025, bottom −0.075). Drawdown share follows
   entry share. **No yardstick separates good from average at the top.**
   `results/members_attribution_routed_tirexcl_actweak.csv`.

   **Item 4 — CHOP-CORE (4.5 min) = 6.98% / 10.47%** (regime-shuffle null
   p = 0.440 — see the addendum after item 8), worst +5.14 / +7.70,
   max DD 2.04 / 3.06, DIP95 3.34 / 5.01, PF 1.61, Sortino 4.45, in budget.
   Chop slices take every entry (A-chop alone 7.9%, B-chop alone 11.1%),
   trend slices gated as the base, crisis on. **Winner of item 4; chosen on
   the checking years — 2021-2026 judges it once.** Direction-preserving null
   mean −0.96 / −1.44, max −0.35 / −0.52, p = 0.000 (39 min). Regime-shuffle
   null: first run failed on a routing-option tuple bug (fixed), REQUEUED
   behind ITEM 8 (`~/fx-data-logs/nulls_q2.sh`, pid 35462, waits for "BATCH 1
   TAIL COMPLETE" — it originally waited on "ITEM 7 COMPLETE", which would
   have run it alongside item 8's two workers; re-pointed 14:57; prints
   "NULLS Q2 COMPLETE"). Pickles `_cc_chopcore`.

   **Item 5 — trend gate (10 min).** NOT-RANGING (chop axis) admits 41% of
   entries; trend slices alone improve (A-trend 1.24% vs 0.28%, B-trend 1.88%
   vs 0.55%) but the book falls to 3.41 / 5.12 vs 5.12 / 7.69. **Winner:
   TRENDING (the base).** Trend-slice mean R per trade on TRENDING bars:
   **+0.33 / +0.30 in 2011-2015, −0.048 / −0.028 in 2016-2020**; every other
   state ~0 in both eras — the trend slices' in-regime edge was entirely in
   the tuning years. `results/trendgate_meanR_by_state_era.csv`. Base
   direction-preserving null: mean −1.43 / −2.14, max −0.79 / −1.19, p =
   0.000 (27 min); base regime-shuffle p = 0.040 (Part C).

   **Item 6 — weighted book (11.2 min).** Member weight ∝ build-year quality
   hurts on every yardstick: Sortino 1.95 / 2.92, expectancy 1.77 / 2.65, PF
   3.08 / 4.61, Calmar 2.15 / 3.23 vs equal 5.12 / 7.69; gate-3 composite
   5.21 / 7.81 with worse drawdown (near-uniform weights). **Winner: equal.**
   `results/members_weighted_routed_tirexcl_actweak.csv`.

   **Item 7 — agreement sweep: DONE (curve-shape 15.9 min + min-votes 170
   min, `ITEM 7 COMPLETE` 14:58).** Grid 1,2,3 then geomspace(4, p99.5=1,747,
   12); real + zero-cost twin + 5 random-N draws per step, both budgets.
   Real book is IDENTICAL to the base (5.12 / 7.69, worst 3.62 / 5.43, 298
   trades/yr) for min_votes 1-63: no row with |net| < 63 is ever sized under
   the fitted curve, so the bar bites nothing there and the random-N rows at
   those k (which drop sized rows too) are not a like-for-like control.
   Where the bar bites: **min_votes 110: 5.53 / 8.30, worst 3.24 / 4.86,
   maxDD 1.74 / 2.61, 253 trades/yr** (random-N same count: mean 2.90 / 4.35,
   max 3.29 / 4.94 — beaten); 191: 4.22 / 6.33, worst 2.52 / 3.78 (random
   2.31 / 3.47, max 3.02 / 4.53 — beaten); 332 and above collapse (1.63 /
   2.45 down to 0.3 / 0.5, worst years negative, random-N max above real
   from 332 up). Spread paid is flat ~1.47 / 2.21 %/yr to 110 then falls with
   the trade count. **Read: the agreement bar adds ~+0.4 / +0.6 to the
   median at 110 and costs ~0.4 / 0.6 on the worst year — return up, floor
   down, not a clean win.** Winner not picked: 25-draw control at 110 and
   191 and both nulls run at the Batch 1 boundary per the resume
   instruction. `results/agree_minvotes_routed_tirexcl_actweak.csv`,
   `agree_curveshape_routed_tirexcl_actweak.csv`.

   **Item 8 — team-size curve: DONE (243 min, 420 walks, 0 errors).** Top-N
   by build-year quality, all five yardsticks, N on the 14-point log grid
   25..8,235, 10 random-N draws per N, both budgets. **Picking on build-year
   quality is worse than picking at random at every N up to 2,160**: the
   real top-N median year is negative or ~0 for every yardstick from 25 to
   2,160 (team1 −0.97 to +0.28; Sortino alone reaches 3.1 / 4.6 at 232-363,
   about the random mean there), while random-N is +1.7 / +2.6 at 148 and
   +4.5 / +6.8 by 1,383. Worst years negative for every yardstick at every
   N ≤ 2,160. At 3,375 (top 41%) still below ALL (4.82 / 7.23 calmar, 4.72 /
   7.07 expectancy vs 5.12 / 7.69). **The one point above ALL: N = 5,272
   (drop the bottom 36%)** — expectancy_R 6.12 / 9.18, worst 4.04 / 6.06,
   maxDD 2.41 / 3.61; calmar 5.82 / 8.72, worst 3.98 / 5.97, maxDD 2.15 /
   3.23; random-N at 5,272: mean 5.09 / 7.63, max 5.79 / 8.69 (10 draws).
   **Read: return up ~+1.0 / +1.5 and worst year up +0.4 / +0.6, but max DD
   up +0.64 / +0.95 — return traded against drawdown, not a clean win; and
   it is one point out of 70 real trials against a 10-draw max.** Together
   with sanity (a) (rank persistence ~0) and item 3 (the hump): the members
   that ranked best on the build years are the fitted ones. Winner: **ALL /
   equal stands** unless the 25-draw control at 5,272 says otherwise.
   `results/members_teamsize_routed_tirexcl_actweak.csv`.

   **Item 4 addendum — chop-core regime-shuffle null: DONE (57 min, 20:00).**
   real 6.98 / 10.47 vs shuffled-regime mean 6.87 / 10.31, p95 7.54 / 11.32,
   max 7.65 / 11.48, **p = 0.440 both budgets**. Chop-core is NOT
   distinguishable from a book routed on shuffled regime labels: taking every
   chop entry regardless of state leaves the trend gate as the only thing the
   regime does, and the shuffle shows that gate is worth nothing on this
   book. Chop-core's edge over the base (5.12 / 7.69) is from switching the
   chop gate OFF, not from the estimator. (Base regime-shuffle p = 0.040.)

   **Batch 1 boundary — RUNNING since 22:58 (`~/fx-data-logs/b1_boundary.sh`,
   pid 91532, serial, prints "B1 BOUNDARY COMPLETE"):** (1) 25-draw random-N
   control, fresh seeds (20260924+), on the item 7 candidate (min_votes 110
   and 191 → `agree_minvotes_winner_*.csv`) and the item 8 candidate (N =
   5,272 and 3,375 → `members_teamsize_winner_*.csv`); `l2agree.py` and
   `l2members.py` gained `--grid --out-name --seed-base` so the sweeps are
   kept. (2) The Layer 1 analysis chain on 5pm in the main tree
   (`l1analyse.sh <repo> MAIN5PM`, ~111 min) then the second pass; the
   interface `layer1_states.csv` is backed up to `~/fx-data-logs/
   layer1_states_5pm_interface_backup.csv` (md5 4e9857cf…) and the driver
   reports whether the chain changed it — if it did, compare before
   committing. **NOT run: the direction-preserving and regime-shuffle nulls
   on the two candidates.** Neither beats the base on both return and risk
   (110: worst year down; 5,272: max DD up), so under "never trade return
   against risk" neither is a winner and ~3 h of nulls on them would be spent
   on a non-result; Jack can call for them.

   **THE REST OF THE QUEUE IS ONE DETACHED DRIVER — `~/fx-data-logs/
   chain_all.sh` (pid 92588, launched 23:20), one heavy job at a time, each
   starting the moment the previous prints its marker.** Order and markers:
   waits for "B1 BOUNDARY COMPLETE" → **CHOP-ONLY** reference row (Jack, 14
   Sep: chop slices always on, NO trend strategies, crisis on, same walk,
   both budgets; `l2route --trend-gate never` added; walked with `--slices
   A-chop,B-chop`, pickles `_cc_choponly`; direction-preserving null 25
   draws; the regime-shuffle null is NOT run because with no trend strategies
   and chop always on the routing reads no regime state, so shuffling the
   states returns the real book by construction — **CHOSEN ON THE CHECKING
   YEARS**, mark it so wherever it is quoted) → "CHOP-ONLY COMPLETE" → **item
   10** (deletes `fx-data-l1A/-l1B/-l1Bfull` only if the chain reported the
   interface file unchanged; else "ITEM 10 SKIPPED") → **Batch 2 smoke tests**
   on `_cleanfield` (bestmember, volfloor, opposition, legflip, killswitch,
   carry) → "SMOKE COMPLETE: …" → **Batch 2 on the base book in order**,
   each stage only if its smoke passed ("ITEM 11 bestmember COMPLETE" …
   "ITEM 15 carry COMPLETE", or SKIPPED/FAILED) → "BATCH 2 COMPLETE". Item 16
   (stacked) is composed from the winners by hand; the refit build (item 0c)
   is code work and starts at "BATCH 2 COMPLETE". Rough ETA from the 23:00
   start: boundary ~02:30 · CHOP-ONLY ~03:15 · smoke ~04:00 · Batch 2
   ~07:00-08:00 (15 Sep). Every marker is in `batch1.log`.

   **Item 9 — entry cost: DONE** (4.9 min + 27 min), see sanity (b).

   **Item 10 — cleanup: NOT DONE.** `fx-data-l1A`, `-l1B`, `-l1Bfull` (1.1
   GB, sibling directories of the repo) can be deleted once the pool pass and
   the Layer 1 chain on 5pm have run in the main tree.

   **Batch 2 code — WRITTEN, UNTESTED ON REAL DATA (syntax-checked only):**
   `code/l2exit.py` (item 11: `--stage bestmember` position ledger by each
   yardstick; `--stage volfloor` ATR-percentile floor swept 0-0.5),
   `code/l2oppose.py` (item 12 `--stage opposition` majority/sit-out/hedge
   via `l2walkfwd.OPPOSITION`; item 13 `--stage legflip` leg 1 closed at the
   TRENDING flip, legs identified as same (sid, pair, entry) records),
   `code/l2killswitch.py` (item 14: trigger swept 0.5-3.6% on the hourly mid
   path from `data/oanda_h1`), `code/l2carry.py` (item 15: 21-pair 2y-carry
   sleeve, fraction × rebalance swept, alone and added). Kernel hooks in
   `l2walkfwd.py`: `NET_MIN_VOTES`, `NET_ROW_MASK` (bool array | ('random',
   share, seed) | ('callable', f)), `CURVE_MODE`, `OPPOSITION`; `Book.series`
   `pair_scale`; `walk(nocut=..., pair_scale=...)`. Item 16 (stacked run) is
   NOT written — compose from the winners. Run each Batch 2 stage on the
   three-slice book `_cleanfield` first as a smoke test (1-min walks), then
   on the base book, ONE heavy job at a time — the harness kills processes
   when the Mac's free memory drops under ~2.5 GB (it did so twice today).

   **Batch 1 clock so far:** item 1 70 min · 2 0.1 · 3 2.4 · 4 4.5 (+nulls
   39) · 5 10 (+null 27) · 6 11.2 · 9 4.9 + 27 · sanity 3 — plus item 7
   running since 11:52.

   **THE DISK.** This repo lives under `~/Documents`, and `brctl status` shows
   iCloud Drive syncing that container. Symptoms seen today: `du` reporting 0
   bytes for real files (dataless, evicted), and `[Errno 60] Operation timed
   out` on plain local reads of `.npz` and `signals.json` under load (killed
   `sc7` twice, `prep` once). Every scorer is resumable and every stage was
   re-run to completion, but the fix is Jack's: move the repo out of the
   iCloud-synced folder or turn off Desktop & Documents syncing. Until then,
   retry a read-timeout failure once before believing it.

   **RESUME INSTRUCTION FOR A FRESH SESSION.** (1) `tail -5 ~/fx-data-logs/
   batch1.log` and `pgrep -fl "item7.sh|queue_b1_tail.sh|nulls_q2.sh"` — the
   three detached drivers survive a session clear (ppid 1). (2) Do not start
   any other heavy job while item 7 or item 8 runs. (3) When "BATCH 1 TAIL
   COMPLETE" appears: read `agree_minvotes_*`, `agree_curveshape_*`,
   `members_teamsize_*`, pick the item 7 and 8 winners from the curves, run
   the 25-draw random-N control on each winner and both nulls
   (`~/fx-data-logs/l3nulls.sh <suffix> <route args>` for routing variants;
   for kernel settings set the global and rerun the walk), then item 10.
   (4) DONE 15 Sep — the Layer 1 chain on 5pm ran in the main tree and is committed. (5) Batch 2, one stage at
   a time, smoke-tested on `_cleanfield` first. (6) One table, HANDOFF item 0,
   commit after each item.
   (7) After Batch 2: the REFIT PROGRAMME, item 0c below — scoped, queued,
   NOT to be started until Jack says go. **(15 Sep: SUPERSEDED BY 0d — the
   kernel had a look-ahead; nothing Book-based below 0d may be quoted.)**

0d. **15 SEP — THE NETTING LAYER HAD A ONE-BAR LOOK-AHEAD. EVERY LAYER 2 BOOK
   NUMBER IN THIS FILE IS CONTAMINATED UNTIL RERUN. READ THIS BEFORE QUOTING
   ANYTHING BELOW.**

   **How it was found.** Batch 2 item 12 (same-pair opposition) returned
   sit-out = **20.06% / 28.71%, worst year 18%, worst month 0.26%, Sortino
   7.8**. Too good. The check: on the trade years, rows with votes on both
   sides carry the stop-outs (exit-day marks mean −0.353 R there vs +0.016 R
   on unanimous rows) and six times the entries (535k vs 84k). The entries
   are the tell.

   **The mechanism.** `l2engine` fills an entry AT THE CLOSE OF ITS SIGNAL BAR
   — documented there: "the project's usual one-bar lag is deliberately
   absent". So a member's presence on its entry day D is decided by D's
   close. `l2walkfwd.Book` counted that member's vote on row D, whose mark is
   the D−1 → D move of the OTHER members' positions. Entrants are
   confirmations of the move that just happened: on 34,104 pair-days with
   both entrants and open positions, the entrants' direction agrees with the
   sign of that day's move on **83%**, corr **0.61**; mean move **+0.29 R**
   when they go long, **−0.30 R** when short. Entry-day marks are pure cost
   (mean −0.023, 99% in [−0.1, 0], none positive) — the entrant had no
   exposure on the day its vote sized. Every row was sized larger on the days
   that had already gone its way, and the agreement curve learned exactly
   that.

   **Why the nulls never caught it.** A random entrant has no relation to the
   day's move, so every random-entry null sat at ~0 and every real book beat
   it at p = 0.000. The regime-shuffle null keeps the same-day entrants, so
   shuffled books stayed positive (chop-core p = 0.44). The level-permutation
   null permuted agreement levels that themselves carry the leak.

   **Measured, both budgets, same walk, same pickles:**

   | book | as run (entry-day vote) | **vote from the next day (fixed)** |
   |---|---|---|
   | BASE `_routed_tirexcl_actweak` | 5.12 / 7.69, worst 3.62 / 5.43, DD 1.77 / 2.66, PF 1.49 | **−1.00 / −1.50**, worst −1.50 / −2.24, DD 2.72 / 4.08, DIP95 5.61 / 8.41, PF 0.94 |
   | CHOP-CORE `_cc_chopcore` | 6.98 / 10.46, worst 5.14 / 7.70, PF 1.61 | **−0.82 / −1.23**, worst −1.70 / −2.55, DD 3.11 / 4.66, PF 0.93 |
   | CHOP-ONLY `_cc_choponly` (chosen on the checking years) | 10.59 / 15.88, worst 8.89 / 13.34, PF 1.88 | **−0.44 / −0.66**, worst −1.08 / −1.63, DD 2.19 / 3.28, PF 0.95 |
   | sit-out (item 12) | 20.06 / 28.71 | −1.36 / −2.03 (entry-day rows dropped, costs out) |

   Every fixed book is negative, out of budget, PF < 1. The whole Layer 2
   edge was the one-bar look-ahead in the vote.

   **Fixed nulls (item 1 of 15 Sep, phase A done 23:30; shuffles in phase B).**
   Direction-preserving (random-entry on the same permitted bars, 25 draws):

   | book | real | null mean | null p95 | null max | p |
   |---|---|---|---|---|---|
   | BASE team1 / team2 | −1.00 / −1.50 | −0.52 / −0.78 | −0.25 / −0.38 | −0.02 / −0.02 | **1.000 / 1.000** |
   | CHOP-CORE | −0.82 / −1.23 | −0.36 / −0.54 | −0.16 / −0.25 | −0.08 / −0.12 | **1.000 / 1.000** |
   | CHOP-ONLY | −0.44 / −0.66 | 0.00 / 0.00 (flat: the random book sizes to zero) | 0.00 | 0.00 | 1.000 / 1.000 |

   The strategies' own entries do WORSE than random entries on the same bars,
   on every book and both budgets. The random-entry null itself was found to
   have been built in a different convention from the real marks (no fill-day
   row, cost folded into the first move day, tid 0 everywhere) — i.e. its
   entrants already voted a day late, which is why the contaminated real
   books beat it at p = 0.000 every time. It now writes the real convention
   (fill-day cost row, one tid per trade) so `Book`'s shift and the same-day
   check apply to real and null alike. Chop-only's regime-shuffle null is
   not run (degenerate: no regime is read). Fixed files carry no header;
   contaminated ones say VOTE-TIMING LEAK on line 1.

   **The fix, applied:** `l2walkfwd.VOTE_ON_ENTRY_DAY = False` (default). A
   position votes from the day AFTER its fill; its entry cost rides on its
   first voted day's mark (`vote_from_next_day`, inside `Book.__init__`, so
   every module and every null worker gets it). `True` reproduces the old
   numbers for the record. 1,608 single-day trades (filled and closed the
   same day) have no exposure day; their −50.3 R of cost is dropped and
   printed. Nothing else in the kernel changed.

   **What is contaminated:** everything produced through `Book` — the base
   book, every structure in §0b and §1A/1B, the routing tests (0a C/D), the
   agreement study and curve, sizing and Layer 4 v2, Batch 1 items 2-9 (the
   per-member EXPECTANCY in item 2 is per-trade and stands), Batch 2 items
   11-14, chop-core, CHOP-ONLY. **Not contaminated:** anything per strategy
   — gate 2 / gate 3, `metrics()`, rank persistence, the Layer 1 estimator.

   **Where things stand.** Batch 1 and Batch 2 ran to completion on the
   contaminated kernel (markers in `batch1.log`; results below, kept for the
   record, each now labelled). The refit build (0c) is NOT started — its
   walk would inherit the kernel, and the question it asks (does re-tuning
   restore an edge) has to be asked of a book that has one. Nothing is
   running. **Decision for Jack:** rerun the Layer 2 chain under the fix from
   the always-on stream (route → walk → per-slice → nulls, ~1 h per book) to
   put honest numbers on the base, chop-core and chop-only, then decide what
   Layer 2 is for.

   **Results of the boundary and Batch 2 as run (contaminated, for the
   record).** 25-draw controls: min_votes 110 5.53 / 8.30 vs random max
   5.25 / 7.87 (beaten); 191 4.22 / 6.33 vs 4.83 / 7.25 (not). Top-5,272 by
   expectancy 6.12 / 9.18 vs random max 5.67 / 8.50, worst 4.04 / 6.06 vs
   3.93 / 5.89, max DD 2.41 / 3.61 vs 2.17 / 3.26 (return and floor up, DD
   above every draw). Item 11 best-member ledger 0.3-0.9% on every yardstick,
   out of budget; vol floor hurts at every q (q 0.10-0.20 in budget at
   3.6-3.8%). Item 12 net 5.12 / sit-out 20.06 / hedge 0.43. Item 13 close
   leg 1 at the flip 5.36 / 8.05 vs 5.12 / 7.69, DD 1.86 vs 1.77; 16.4% of
   leg-1 trades open at a flip. Item 14 kill-switch: every trigger below the
   day budget costs 0.3-2.9%/yr and fires on days that recover; in budget
   only where it never fires. Item 15 carry: smoke test crashed in
   `fit_curve` on a one-member book (fixed: flat curve), not rerun. Item 10
   done (variant copies deleted). Layer 1 chain on 5pm: 125 min + 5, two
   failures fixed (`export.py` string-date compare; `layer1sum.py` /
   `freshness.py` read the interface without `comment='#'`); `export.py` has
   NOT been rerun — when it is, diff its output against
   `~/fx-data-logs/layer1_states_5pm_interface_backup.csv` (md5 4e9857cf…).

0f. **THE BLIND-LABEL PROGRAMME (Jack, 21 Sep) — full library, no picking.
   BUILT; 250 SMOKE RUNNING; NOTHING RENTED. Jack launches the boxes.**

   **Design.** All 45,139 candidates (A 17,822 = 12,163 trend + 5,659 chop;
   B 19,845 = 14,815 + 5,030; C 7,472, the 299 chunks tuned before the
   pause — `results/refit_candidates_full.csv`, three C duplicates dropped).
   Five rolling windows: **tune on years 1-4, grade on year 5 (never seen by
   the tuner), trade year 6 untouched**, roll one year, stitch traded years
   only: 2011-14 / 2015 / 2016 … 2015-18 / 2019 / 2020. Gate 2's grids, cap
   6, 22:00 measured per-pair spreads, one-bar lag everywhere. Everyone
   trades in the book — equal weight, netted, fixed kernel, both budgets,
   always-on and routed; the walk's sizing/curve decisions read years 1-5
   (all closed at decision time). **The year-5 grade is REPORTED, never
   used**: gate 2's bars on the grade year (trade floor 10 = 50/5, one year
   not five) → graded-pass vs graded-fail on year 6; Spearman of the
   grade-year record vs the year-6 record on Sortino, expectancy, PF,
   Calmar and the gate-3 composite; per window, pooled, per slice, both
   streams. Nulls on the book (random-entry both streams, regime-shuffle
   routed), retention, per year, per slice.

   **Code.** `code/l2refit.py` (`--windows tune:grade:trade`, `--stage
   candidates | tune --box k --of N | marks | report`), `code/cloud_refit.sh`
   (three boxes, md5(sid) % 3, resumable bank per (sid, window), pushes the
   shards, merge on the Mac with `--stage report`). Two-strategy end-to-end
   passed (tune → marks → route → walk, per-step decisions log, retention).

   **SMOKE ON THE 250 — COMPLETE 22 Sep 07:30** (tune 489 min on 4 workers,
   marks 6 min, each walk 10-35 s, each random-entry null 1.6-6.6 min,
   shuffle 2.8 min). Every stage of the programme ran end to end.

   *Measured, 1,250 fresh 4-year tunes:* **mean 71.8 s, median 51.2, p90
   99.1, p99 484** (A-chop 55, A-trend 72, B-chop 66, B-trend 78; median 538
   configurations tried). Per job including the routed + always-on scoring of
   the tune window, the grade year, the trade year and every sealed year:
   **72.8 s** (the Scorer's indicator cache makes the scoring nearly free).

   *THE BLIND GRADE CARRIES SOME INFORMATION — first positive signal of the
   month.* Gate 2's bars on the grade year (trade floor 10) pass 334 of
   1,250 routed / 245 allon — a real funnel, unlike the in-sample one.
   Pooled over the five windows, next year: routed graded-pass **−0.011 R,
   48% positive, PF 0.985** vs graded-fail **−0.036 R, 43%, PF 0.961**;
   allon graded-pass −0.034 vs graded-fail −0.028. Per window the routed
   pass group beats the fail group in 3 of 5 (2018 +0.085 vs −0.038 and 68%
   vs 47% positive; 2019 goes the other way, −0.105 vs −0.066). Rank
   correlation grade year → trade year, five yardsticks: routed pooled
   **+0.03 to +0.05**, allon pooled −0.04 to −0.01; one window is strongly
   positive (2013-16 → 2018: **+0.21 to +0.36**), one negative (2012-15 →
   2017: −0.10 to −0.14), three near zero. **Read: the blind grade is not
   noise the way the in-sample record was (which ran −0.18 to 0), but the
   effect is small, one-window-dominated, and still leaves the passers
   negative.** `refit_blind_groups_blind_smoke.csv`,
   `refit_blind_rankcorr_blind_smoke.csv`.

   *The books (everyone trades, equal weight, fixed kernel, both budgets).*
   Always-on: build blocks +3.4 / +5.1 median year → traded years **−0.50 /
   −0.74**, worst −2.77 / −4.16, DIP95 8.0 / 12.0, PF 0.96, retention −0.15
   FIT; random-entry null mean −0.22, max −0.005, **p = 0.96** (worse than
   random). Routed: build +10.5 / +15.8 → **−0.53 / −0.80**, worst −2.27 /
   −3.41, DIP95 10.8 / 16.1, PF 0.996, retention −0.05 FIT; random-entry
   mean −2.31, max −0.48, **p = 0.04**; regime-shuffle mean −1.07, max
   +0.51, **p = 0.16**. Per slice, routed: A-chop +0.13, B-chop +0.44,
   B-trend −0.57, A-trend −1.17. Both books are still negative and both
   break the drawdown budget, but the routed book is the first to beat its
   random-entry null and to sit inside 0.2pp of zero on PF.

   *Per-year and decay.* Routed trade-year medians −0.056, −0.021, +0.010,
   −0.082, −0.009 (1 of 5 years positive); decay from the tune window is
   flat at −0.02 R for years 1-4 and worsens to −0.06 / −0.07 at years 5-6.

   **FULL-RUN COST, from these measurements.** 45,139 candidates × 5 windows
   = **225,695 jobs at 72.8 s = 4,564 core-hours**. Three 16-vCPU boxes
   (48 vCPU, shared at ~0.6× a Mac P-core ≈ 29 effective cores): **6.6 days,
   ~$47** at $0.10/box-hour (one 48-vCPU dedicated box: 5.0 days, ~$190).
   The Mac alone: ~30 days. Marks + walks + nulls afterwards: ~80 core-hours.

   **THE EXACT LAUNCH LINE — one per box, k = 0, 1, 2:**

   ```
   export GH_TOKEN=<token with write access to Jackscuster/fx-data>
   curl -sL https://raw.githubusercontent.com/Jackscuster/fx-data/main/code/cloud_refit.sh | bash -s -- --box k --of 3
   ```

   Each box provisions itself, clones, runs `l2refit.py --stage tune` on its
   md5(sid) % 3 share with `nproc` workers, banks every (sid, window) as it
   completes, and pushes `results/refit_settings_blind_full_b<k>_s*.csv`.
   A box that dies is relaunched with the same `--box` and resumes. Merge on
   the Mac: `python3 code/l2refit.py --stage report --suffix _blind_full
   --windows "2011-2014:2015:2016,2012-2015:2016:2017,2013-2016:2017:2018,2014-2017:2018:2019,2015-2018:2019:2020"`.
   A dry run of the same argument plumbing, no provisioning:
   `bash code/cloud_refit.sh --local --box 0 --of 3` (JOBS=2).

   **ONE KNOWN GAP, not on the launch path.** The always-on marks stream for
   the full library is ~33 GB (the smoke's 185 MB × 181) and the per-step
   Book ~8.5 GB, so the BOOK stage will not fit in the Mac's 16 GB. The fix
   is a per-step marks split (five pickles, the walk loading one step at a
   time → ~7 GB peak always-on, ~1.4 GB routed); I will build it while the
   boxes run. The tunes, the blind report and the routed book are unaffected.

0e. **THE CLEAN REBUILD FROM GATE 2 — SCOPED 16 Sep. NOT STARTED. Does not
   start until `python3 code/preflight.py` prints PRE-FLIGHT CLEAR (every row
   of `results/audit_2026-09.csv` PASS) and Jack says go.**

   **What it is.** Gate 2 re-run from the gate-1 survivor sets of modes A, B
   and C on the 5pm states, with ROLLING FIVE-YEAR TUNING: tune on a closed
   five-year window, trade the next year untouched, roll one year, repeat;
   plus the two-block reading (2011-15 → 2016-18, 2014-18 → 2019-20, both
   tunes already in the annual set). Every strategy scored alone through
   `l2tune.Scorer` (no Book), BOTH always-on and routed to its slice's
   regime, so regime dependence is measured per strategy; gate-1/2 labels
   on the tuning window only; costs from the measured per-pair table at the
   chosen entry hour (`cost_table_h22.csv`, 22:00 NY, majors 1.6 bp, crosses
   2.5 bp); then the fixed Book walk exactly as audit items 7-11 (decision
   assertions, decisions log, retention, three nulls on every winner).

   **Candidates.** Mode A 17,822 (12,163 trend + 5,659 chop); mode B 19,845
   (14,815 + 5,030); mode C: the 7,475 combinations in the 299 chunks tuned
   before the pause (2,222 in the tuned table). **C in full is 554,422
   combinations at ~4 engine-minutes each: ~58,000 core-hours (its own
   progress file's projection), not a candidate for any budget — the
   unfinished chunks stay unfinished.** Total 45,142.

   **Windows.** Annual, five-year: minimal set 2011-15 … 2015-19 (5 tunes,
   trades 2016-2020); full set 2005-09 … 2015-19 (11 tunes, trades
   2010-2020 — eleven traded years for the count-of-years verdict instead
   of five). Two-block reads come free from tunes 2011-15 and 2014-18.

   **Time.** Per five-year tune, measured in the pilot (16 Sep, cap 6, A and
   B mix): ~75 s (45-130). Scoring alone, always-on + routed, ~1 s per
   strategy per window. Engine marks for the walk ~45 core-h; walks and
   nulls ~150-300 core-h.

   | set | tunes | tune core-h | all in | 3 × CPX62 (29 eff. cores, ~$0.30/h) | Mac (6.3 eff.) | 1 × CCX63 (38 eff., $1.60/h) |
   |---|--:|--:|--:|---|---|---|
   | 5 windows | 225,710 | ~4,700 (2,800-8,200) | ~5,100 | **7.3 days, ~$53** | ~34 days | 5.6 days, ~$215 |
   | 11 windows | 496,562 | ~10,300 (6,200-17,900) | ~11,000 | **16 days, ~$114** | ~73 days | 12 days, ~$465 |

   **To build first** (~3-4 days): `l2refit.py` at scale (the pilot's loop,
   sharded by md5(sid) on `cloud_refit.sh` from `cloud_field.sh`, resumable
   per (sid, window)); the Scorer's always-on scoring mode (today it scores
   in-regime only); `l2walkfwd.STEPS` as a list with per-step settings;
   the labels-on-tuning-window pass; the rolling walk driver. **Gate:** the
   pilot's answer. If a fresh tune does not put the median unseen-year
   R/trade above zero on 250 strategies, the rebuild would be re-tuning
   45,000 of them to learn the same thing at 200× the cost — that decision
   is Jack's, with the pilot table in front of him.

0c. **REFIT PROGRAMME — rolling re-tune with rolling selection. SCOPED 14 Sep;
   BUILD APPROVED 14 Sep, TO START AFTER BATCH 2 LANDS; THE RUN WAITS FOR
   JACK'S WORD.** Decisions taken 14 Sep: second tuning window is **2014-18**
   (five-year rule holds, so the two-block version's tunes are the annual
   version's windows 1 and 4 — zero extra tunes, it IS nearly free and runs);
   passers labelled on the tuning window's own record; **annual version
   runs**, two-block on top; **three CPX62s for the tunes when Jack gives the
   word — never rent anything unprompted**; report the build ETA and the
   50-strategy timing probe before the run. Question:
   how long does a freshly tuned strategy keep its edge, and does picking on
   fresh settings beat "everyone votes"? Field: the four-slice clean field,
   8,235 (A-trend 2,960 / A-chop 930 / B-chop 917 / B-trend 3,428). Every
   number below is a plan, not a result.

   **Design (Jack's spec, verbatim in substance).**
   1. Tune every strategy on a trailing window, trade the NEXT block untouched.
      Annual: tune 2011-15 → trade 2016; 2012-16 → 2017; 2013-17 → 2018;
      2014-18 → 2019; 2015-19 → 2020. Two-block: tune 2011-15 → trade 2016-18;
      tune 2014-18 → trade 2019-20 — both tunes are annual windows, so the
      two-block version is the annual settings scored on longer blocks.
   2. At each step, three books on the fresh settings, routed as the base
      (5pm states, TRENDING/RANGING, WEAK blocks trend entries, crisis on):
      ALL (equal, netted); PASSERS (gate-2 floors + gate-3 bars on the tuning
      window); TOP-N by the tuning window's record, all five yardsticks, N on
      the 14-point log grid 25..8,235, random-N control (10 draws) at every N.
   3. Decay curve: mean R per trade in months 1-12 after the tuning window
      ends, pooled over strategies and windows → the live re-tune cadence.
   4. Report: does re-tuning restore per-strategy expectancy (median R/trade
      on the trade block, against item 2's −0.047); does picking on fresh
      settings beat ALL on unseen years; what cadence the decay implies.

   **Rules, frozen.** Tune only on closed years; trade only years sealed at
   tuning time; every choice (settings, passers, N, agreement bar) made on the
   tuning window and applied unchanged; the window is five years rolled one
   year, never shortened; grids declared before the run (below); luck floor
   deflated by the banked count of settings tried per strategy; verdict = count
   of traded years won (5 of 5 annual, 2 of 2 two-block), never the average;
   retention (trade-block result ÷ tuning-window result, annualised) reported
   for every book, under 20% = a fit whatever the raw number; random-entry,
   identity and regime-shuffle nulls on every winner; 2021-2026 sealed.

   **Grids, declared now.** Gate-2 grids as `l2tune.py` has them (stop
   1.00-1.50, tp 1.00-3.00, be 0.01-0.20, arm 1.00-2.00, trail 0.50-2.00,
   ATR 2-50, indicator parameters 12 log points 0.1×-10× default), coordinate
   descent, two passes, adopt only if better on the tuning window. **Indicator
   cap 6 for all four slices** — a fresh tune, not a recovery, so B's uncapped
   history does not bind; uncapped B would cost ~4× per tune. Per tune that is
   ~240 (chop) to ~1,100 (trend, five indicators) configurations, banked
   exactly in `evals` per (sid, window) as `l2tune` already does; annual total
   ~20-45 M configurations, the deflation input. Passer bars: `l2tune.LABEL`
   floors (expectancy, PF, ≥ 50 trades) and the `l2gate3` bars, both on the
   tuning window. Agreement bar: item 7's min-votes curve refit on the tuning
   window. Sizing: the fitted curve and both budgets, team1 / team2.

   **Two spec points, decided 14 Sep.** (i) Second tuning window 2014-18,
   not 2011-18: the five-year rule holds. (ii) PASSERS are labelled on the
   tuning window's own in-sample record, not a blind one (the current field
   labels on W2 under ip1, which never saw W2). In-sample labels pass more;
   the trade block is the only judge.

   **Candidate count.** Annual: 5 windows × 8,235 = **41,175 tunes**.
   Two-block: 0 new tunes (windows 1 and 4 of the annual), only its books
   (~12 core-h) and nulls on its winners.

   **Core-hours.** Per-tune time is the one unknown: 157 s per combination
   (mode B, uncapped, 900 real) and 216 s for uncapped stage 1 alone; the cap
   is documented as ~10× faster on the four wide indicators; gate-3 fine-tune
   (risk knobs only, widened grids, two stages) measured 304 s mean on 5,569
   and 97 s on the banked sample. **Planning figure 150 s per five-year tune,
   range 50-220 s; step 0 of the run is a 50-strategy timing probe on the
   field's indicator mix and the whole table scales linearly with it.**

   | version | tunes | tune core-h (range) | score+engine+walks | nulls (4 winners × 28) | total |
   |---|--:|--:|--:|--:|--:|
   | annual | 41,175 | 1,716 (570-2,520) | ~25 | ~112 | **~1,850** |
   | two-block on top of annual | 0 | 0 | ~12 | ~112 | **~125** |
   | both | 41,175 | 1,716 | ~37 | ~224 | **~1,975** |

   Null costs from the four-slice measurements: identity 470 min × 3 workers
   = 23.5 core-h per book, regime-shuffle 4.3, random-entry 0.4. Scoring each
   window's settings on every sealed year to 2020 (not just the next block)
   is ~4 core-h and extends the decay curve to 24-48 months for the early
   windows — recommended, it is measurement not trading.

   **Wall time and cost.**

   | where | effective cores | annual tunes | both versions, all in |
   |---|--:|--:|--:|
   | Mac, 9 workers, 0.7 duty under the guard, nulls RAM-capped at 3 | 6.3 | ~11 days | ~13 days |
   | one CPX62, 16 vCPU shared (~0.6× a P-core), ~$0.10/h | 9.6 | 7.4 days, ~$18 | 8.6 days, ~$21 |
   | **three CPX62 (decided)** | 29 | **2.5 days, ~$18** | 2.8 days, ~$21 |
   | one CCX63, 48 dedicated vCPU, ~$1.60/h | ~38 | 1.9 days, ~$72 | 2.2 days, ~$83 |

   The Mac figure assumes nothing else heavy runs. Decided: three CPX62
   boxes for the tunes (sharding is md5(sid) % N already), rented by Jack on
   his word; walks and nulls on the Mac or one box afterwards.

   **Does the cloud tooling carry it?** `cloud_field.sh`: the skeleton does —
   provisioning, `--box k --of N` sharding by md5(sid), banking outside the
   clone, resumability, the push/retry block — but its two Python steps are
   hard-coded to `l2recoverip1.py` and `l2cleanfield.py --shard-only`. Needs
   `code/cloud_refit.sh`, a copy with those two lines swapped for the new
   tuner and scorer. `cloud_walk.sh` runs `l2cfchain.sh`, whose kernel
   (`l2walkfwd.STEPS`) is hard-coded to the two-step ip1/ip2 stitch; it does
   NOT carry a five-step walk with different settings per step.

   **To build after Batch 2 lands (~3 days of build, none of it heavy on the
   Mac; the 50-strategy timing probe is ~2 core-hours and also waits for
   Batch 2).** (a) `code/l2refit.py`: per (sid,
   window) calls `l2tune.tune_one` with `tune_windows` = the trailing five
   years (the hook exists — `l2recoverip1` uses it), banks settings + `evals`
   per shard, resumable on (sid, window); then scores every sealed year to
   2020 under each window's settings (`l2cleanfield`-style, 0.87 s per
   strategy per five years). (b) `l2walkfwd`: `STEPS` becomes a list and the
   engine's trade table carries a `step` column, so 2017's trades come from
   the 2012-16 settings; the routing (`l2route`), sizing, min-votes,
   team-size and null stages then run unchanged on the routed pickles. (c)
   `cloud_refit.sh` from `cloud_field.sh`; `l2refitchain.sh` from
   `l2cfchain.sh`. (d) Smoke test: `--limit 250` on the three-slice
   `_cleanfield`, 2 cores, before any box is rented. Outputs:
   `results/refit_settings_<window>.csv`, `refit_books_annual.csv`,
   `refit_books_twoblock.csv`, `refit_teamsize_*.csv`, `refit_decay.csv`,
   `refit_report.csv`; HANDOFF item 0 table; nothing wired to the app (Layer
   2 never is).

0a. **LAYER 1 ON THE 5PM BAR, AND THE FIRST ROUTING TEST (13-14 Sep).** Four
   things, each from files: (A) whether the signal-library survivors depend on
   1999-2002; (B) Layer 1 rebuilt on OANDA 17:00 NY closes, validated on
   2016-2020 with 2021+ sealed, against the H.10 noon build on the same window;
   (C) routing the four-slice clean field on the rebuilt states, against
   always-on; (D) the return search on the NO_CUT book. Measured run times:
   A 150 min · B 114 (scoring) + 111 (analysis) + 1 · A2 control 150 + 107 ·
   always-on engine 52.7 · C 6 h 15 (of which regime-shuffle nulls 4 h 20 on one
   worker) · D 32 min. Every number below is net of costs, sized on the build
   blocks only, both budgets team1 / team2 unless stated.

   **(A) 1999-2002 dependence.** The gauntlet's survivor SET depends on it; the
   signals mostly do not. 1999+ passes 29, 2002-06+ passes 33, only 6 pass both
   (`z_panelvol_40/60`, `zz_panelvol_D40/D60`, `rc_cx1.5_x180_ch`,
   `rd_xsctop_r15_pd`). The churn is one gate — IS effect ≥ 0.0221 — with t-stats
   and agreement unchanged: 1999-2002 carried larger effect sizes for the
   trend-duration chop signals, moving the same family across a threshold
   noise-calibrated on the longer panel. The shipped estimator uses none of
   these signals. `results/layer1_survivors_1999_vs_2002.csv`.

   **(B) Noon vs 5pm — five present-tense checks on the SAME window** (2002-09-24
   → 2020-12-31, IS to 2015, holdout 2016-2020; the A2 column is the noon build
   re-run on exactly that window, which is the only fair comparison). Source:
   `results/layer1_5pm/` and the H.10 files now headered SUPERSEDED.

   | check | noon, full history | noon, same window (A2) | **5pm** | moved? |
   |---|---|---|---|---|
   | separation, chop axis OOS / surrogate / corrected | 0.156 / 0.171 / −0.016 | 0.188 / 0.173 / +0.016 | 0.203 / 0.168 / **+0.035** | 5pm best; all within noise of each other |
   | separation, trend axis, corrected | −0.047 | −0.066 | −0.052 | fails everywhere |
   | separation, 12-cell grid OOS / null / corrected | 0.072 / 0.079 / −0.007 | 0.091 / 0.090 / +0.001 | 0.088 / 0.098 / −0.010 | no |
   | persistence: high-cell run trend / chop; grid median run | 28 / 24; 12 | — ; 12.2 | 30 / 24; 12 | no |
   | refit stability, vintages 2009 / 2012 / 2018 / 2021 | 0.942 / 0.954 / 0.963 / 0.952 | 0.909 / 0.937 / 0.952 / 0.943 | 0.909 / 0.942 / 0.955 / 0.943 | 5pm = A2: the drop is the shorter history, not the source |
   | coverage (grid OOS); min cell share | 1.000; 0.032 | 1.000; 0.051 | 1.000; 0.024 | no |
   | null: scale axis on realised vol, corrected | +0.331, p 0.016 HOLDS | +0.338, p 0.016 HOLDS | +0.388, p 0.016 HOLDS | no |
   | null: strong chop − strong trend, bars to peak | +1.44, t 4.79 HOLDS | **+1.55, t 3.41 HOLDS** (p ≤ 0.002 ×3) | **+0.33, t 0.75 FAILS** (p ≈ 0.5) | **YES — the source, not the window** |
   | null: structural separation, raw, corrected | −0.018 | −0.039 | +0.081, p 0.02 | 5pm better, but "FAILS" by the module's own bar |
   | state shares trending / ranging / TIR / neither | 28.3 / 33.5 / 19.0 / 19.1 | 28.8 / 32.8 / 19.2 / 19.2 | 29.5 / 32.6 / 18.6 / 19.3 | no (the quoted 40/40/7/13 matches no build) |
   | median run length (shape2, per pair) | 19 bars | 19 | 20 | no |
   | gauntlet survivors, same window | — | 61 | **5** (3 shared) | **YES** — 56 signals lose pair agreement (0.93 → 0.6-0.86) and half their OOS t |

   Noon and 5pm agree on `shape2` on **72.2%** of 123,453 overlapping pair-days
   (activity 64.6%): ranging holds 78.5%, trending 76.7%, **neither 64.4%,
   trend-in-range 62.3%** — the two mixed states are the unstable ones. Every
   OANDA bar before 2005-01-03 is a single-quote day (O=H=L=C); their daily
   returns correlate 0.856 with H.10, the same as later eras (0.82-0.84).
   Series built by `build5pm.py`: 28 pairs triangulated from the 7 USD legs as
   `build.py` does, 2002-09-24 (NZDUSD's start) onward, direct-cross gap 0.38 bp
   median; asserts EURUSD 1.5991 / USDCHF 0.7209 on the 17:00 closes.

   **(C) ROUTING, four-slice clean field, NO_CUT, one-bar lag.** Layer 2 already
   routes on Layer 1 (`GAUNTLET.md` §"REGIME SLICING", `f79f2b1`, 15 Aug): every
   strategy runs regime-agnostic and each trade is kept only if the H.10 `shape2`
   at its entry bar is the slice's regime — so the published 5.09 / 7.64 is the
   H.10-ROUTED book, not always-on. `WF_ROUTE=off` gives the always-on stream
   (7,648,503 trades, 63.5M marks, 52.7 min); every rule below is an exact
   post-filter on it, and the H.10 rule reproduces the published book to the
   trade (1,948,908) and to every decimal. Crisis flag = `crisis.py legdiv20`
   above its IS 95th percentile, flagging the two diverging legs, lagged one bar.
   Random-entry null: entries drawn only from bars the rule permits.
   Regime-shuffle null: the state runs of each pair reordered (run lengths and
   shares kept), the always-on stream re-routed, 25 draws, both budgets.

   | book | entries kept | median yr | worst yr | max DD | worst day | DIP95 | PF | Sortino | Calmar | exp %/day | in budget | rand-entry p (null max) | regime-shuffle p (null mean / max) |
   |---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
   | ALWAYS-ON (every entry, every regime) | 100% | 3.38 / 5.07 | 2.51 / 3.77 | 1.51 / 2.27 | 0.46 / 0.70 | 2.31 / 3.46 | 1.49 | 3.61 | 13.2 | 0.015 / 0.023 | yes | — | — |
   | H.10-routed (reproduces the published book) | 25% | 5.09 / 7.64 | 3.93 / 5.89 | 1.86 / 2.79 | 0.64 / 0.96 | 3.04 / 4.56 | 1.49 | 3.92 | 15.0 | 0.022 / 0.032 | yes | — | — |
   | 5pm: trend→TRENDING, chop→RANGING, crisis on | 27% | 4.39 / 6.58 | 3.31 / 4.96 | 1.79 / 2.69 | 0.56 / 0.84 | 3.32 / 4.98 | 1.43 | 3.44 | 14.0 | 0.019 / 0.029 | yes | 0.000 (0.28 / 0.41) | 0.000 (3.24 / 4.86 / 4.08 / 6.11) |
   | 5pm: + TREND-IN-RANGE admitted | 41% | 3.23 / 4.84 | 1.92 / 2.88 | 2.23 / 3.34 | 0.73 / 1.10 | 3.60 / 5.40 | 1.33 | 2.51 | 8.2 | 0.014 / 0.021 | yes | 0.000 (0.18 / 0.26) | 0.160 (2.73 / 4.09 / 3.66 / 5.49) |
   | **5pm: + WEAK blocks new trend entries** | 21% | 5.12 / 7.69 | 3.62 / 5.43 | 1.77 / 2.66 | 0.67 / 1.01 | 3.35 / 5.02 | 1.49 | 3.62 | 16.4 | 0.022 / 0.034 | yes | 0.000 (0.20 / 0.30) | 0.040 (3.65 / 5.48 / 5.13 / 7.70) |
   | 5pm: TIR admitted + WEAK block | 33% | 3.35 / 5.02 | 2.70 / 4.04 | 2.31 / 3.47 | 0.85 / 1.27 | 3.37 / 5.06 | 1.37 | 2.78 | 8.6 | 0.015 / 0.023 | yes | 0.000 (1.23 / 1.84) | 0.160 (2.89 / 4.34 / 3.59 / 5.38) |

   Per year, NO_CUT return %, team1:

   | book (team1) | 2016 | 2017 | 2018 | 2019 | 2020 |
   |---|--:|--:|--:|--:|--:|
   | ALWAYS-ON (every entry, every regime) | 2.67 | 3.38 | 6.58 | 2.51 | 4.80 |
   | H.10-routed (reproduces the published book) | 4.36 | 3.93 | 8.52 | 5.09 | 6.04 |
   | 5pm: trend→TRENDING, chop→RANGING, crisis on | 3.91 | 3.31 | 8.12 | 5.38 | 4.39 |
   | 5pm: + TREND-IN-RANGE admitted | 3.23 | 1.92 | 6.45 | 3.94 | 2.77 |
   | 5pm: + WEAK blocks new trend entries | 5.79 | 3.62 | 10.56 | 5.12 | 3.95 |
   | 5pm: TIR admitted + WEAK block | 3.35 | 2.75 | 6.64 | 4.51 | 2.70 |

   Per slice, each walked alone (team1, median year %):

   | slice alone (team1) | ALWAYS-ON | 5pm TIRx/ACTi | 5pm TIRx/ACTw | 5pm TIRi/ACTi |
   |---|--:|--:|--:|--:|
   | A-trend | 1.80 | 0.60 | 0.28 | 0.90 |
   | A-chop | 8.05 | 5.80 | 5.80 | 5.80 |
   | B-chop | 11.20 | 8.28 | 8.28 | 8.28 |
   | B-trend | 3.02 | 1.06 | 0.54 | 1.48 |

   Regime dependence at the trade level (2016-2020, rule TIRx/ACTi, mean R per
   trade net of costs): A-chop inside −0.059 vs outside −0.099; B-chop −0.028 vs
   −0.054; A-trend −0.046 vs −0.038; B-trend −0.026 vs −0.026. By state at
   entry: `neither` ≈ 0.00 for every slice (the least bad), `trend-in-range` the
   worst everywhere (−0.05 to −0.16). **Every slice has negative mean R per
   trade; the book's return is the netting and the sizing curve, not per-trade
   expectancy.** `results/routing_*_4slice.csv`.

   **Plain English on routing.** Taking every entry in every regime makes
   3.4%. Gating trend entries to TRENDING bars and chop entries to RANGING bars
   on the 5pm states makes 4.4%, and blocking new trend entries when activity
   is WEAK as well makes 5.1% — the same as the noon gate — with a lower
   drawdown and only 21% of the entries. Both of those beat routing on
   scrambled labels of the same run-length structure in 25 of 25 and 24 of 25
   draws. Admitting TREND-IN-RANGE bars for trend entries takes the book BELOW
   always-on and its labels no longer beat scrambled ones (p 0.16) — that state
   is overlap, as §16.4t said. Per slice alone, routing makes every slice
   WORSE (A-chop 8.1 → 5.8, B-chop 11.2 → 8.3); it helps the netted book by
   removing trend entries that fight the chop book. And the activity axis,
   which "carries nothing" as a predictor, does real work as a gate: it is the
   difference between 4.4% and 5.1%.

   **(D) THE RETURN SEARCH, NO_CUT book (the H.10-routed four-slice book):**

   | item | median yr | worst yr | max DD | worst day | DIP95 | PF | Sortino | Calmar | in budget |
   |---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
   | 1 sizing (a) as now, NO_CUT team1 | 5.09 | 3.93 | 1.86 | 0.64 | 3.04 | 1.49 | 3.92 | 15.0 | yes |
   | 1 sizing (b) DIP95+maxDD vs 5.4, worst day vs 3.6, NO_CUT | 7.64 | 5.89 | 2.79 | 0.96 | 4.56 | 1.49 | 3.92 | 15.0 | yes |
   | 1 sizing (c) actual path only, NO_CUT | 8.36 | 7.52 | 2.96 | 1.05 | 5.29 | 1.50 | 4.01 | 16.9 | yes |
   | 1 sizing (a), NO_CUT_SLICE_BALANCED | 4.60 | 2.80 | 2.65 | 0.62 | 3.37 | 1.46 | 3.71 | 10.9 | yes |
   | 1 sizing (b), NO_CUT_SLICE_BALANCED | 6.91 | 4.20 | 3.97 | 0.93 | 5.06 | 1.46 | 3.71 | 10.9 | yes |
   | 1 sizing (c), NO_CUT_SLICE_BALANCED | 7.94 | 4.83 | 4.56 | 1.10 | 5.87 | 1.46 | 3.72 | 11.1 | NO |
   | 2 costs zero (0.0 bp), drag 0.0% | 6.70 / 10.05 | 5.33 / 7.99 | 1.80 / 2.70 | 0.68 / 1.02 | 3.07 / 4.61 | 1.59 | 4.57 | 19.9 | yes |
   | 2 costs as_run (3.1 bp), drag 24.0% | 5.09 / 7.64 | 3.93 / 5.89 | 1.86 / 2.79 | 0.64 / 0.96 | 3.04 / 4.56 | 1.49 | 3.92 | 15.0 | yes |
   | 2 costs raw_spread (2.1 bp), drag 16.8% | 5.58 / 8.36 | 4.36 / 6.54 | 1.83 / 2.75 | 0.65 / 0.97 | 3.03 / 4.54 | 1.52 | 4.14 | 16.5 | yes |
   | 2 costs entry_1900 (3.9 bp), drag 28.9% | 4.76 / 7.14 | 3.58 / 5.37 | 1.85 / 2.77 | 0.62 / 0.94 | 3.04 / 4.56 | 1.47 | 3.77 | 14.2 | yes |
   | 3 voltarget_20, target = build-block vol 3.10 / 4.66, lev 1.35 | 7.57 / 11.35 | 7.55 / 11.33 | 2.25 / 3.38 | 1.06 / 1.60 | 4.87 / 7.31 | 1.52 | 4.06 | 21.5 | NO |
   | 3 voltarget_60, target = build-block vol 3.10 / 4.66, lev 1.24 | 6.93 / 10.39 | 6.19 / 9.28 | 2.49 / 3.74 | 0.82 / 1.23 | 4.65 / 6.98 | 1.51 | 4.02 | 18.2 | NO |
   | 4 as run: JPY share 0.124 build / 0.122 trade, largest block 0.186 | 5.09 / 7.64 | 3.93 / 5.89 | 1.86 / 2.79 | 0.64 / 0.96 | 3.04 / 4.56 | 1.49 | 3.92 | 15.0 | yes |
   | 4 risk parity (3 iterations): JPY share 0.128 build / 0.120 trade, largest block 0.133 | 5.20 / 7.79 | 3.96 / 5.94 | 1.87 / 2.80 | 0.70 / 1.05 | 3.04 / 4.56 | 1.50 | 3.95 | 15.2 | yes |
   | 6 direction-preserving null, NO_CUT: null mean -1.07 / -1.60, p95 -0.63 / -0.95, max -0.48 / -0.72, **p = 0.000 / 0.000** | 5.09 / 7.64 | | | | | | | | |

   Per year, NO_CUT (a-sizing):

   | NO_CUT team1 / team2 | 2016 | 2017 | 2018 | 2019 | 2020 |
   |---|--:|--:|--:|--:|--:|
   | return % | 4.36 / 6.55 | 3.93 / 5.89 | 8.52 / 12.77 | 5.09 / 7.64 | 6.04 / 9.05 |
   | max DD % | 0.96 / 1.45 | 0.71 / 1.07 | 0.65 / 0.97 | 1.36 / 2.04 | 1.86 / 2.79 |
   | realised vol % | 2.41 / 3.62 | 1.79 / 2.68 | 2.12 / 3.19 | 2.37 / 3.56 | 2.91 / 4.36 |

   Reading: **costs take 24% of the median year** (6.70 → 5.09; raw spreads
   without the ×1.5 markup would take 17%, the measured 19:00 NY entry cost
   29% — it is higher than the table, not lower). **Vol targeting to the build
   block's own vol runs at 1.24-1.35× and breaks the DIP95 budget** (4.7-4.9%
   vs 3.6) in exchange for +1.8-2.5 points — it is leverage, not information.
   **The book is already at currency parity**: JPY carries 12.4% of the
   variance against 12.5% for equal blocks, the largest block (EUR) 18.6%;
   equalising moves the median +0.1 point. **Sizing rule (c)** — actual path
   only, DIP95 measured never binding — makes 8.36% at 2.96% max DD, inside
   both hard limits, with DIP95 reading 5.29%; that is the same +65% for +59%
   drawdown trade the cut book showed. **Every trade year stayed inside both
   budgets** on every row marked "yes". The direction-preserving null is the
   first null with width on the uncut book: random timing inside the book's own
   (pair, day) direction LOSES 1.1 / 1.6% a year; the real is 5.1 / 7.6 (p =
   0.000). `results/returns_*_cleanfield_4slice.csv`.

   **(7) REFIT SCOPE — rolling gate 3 fine-tune per build block, 8,235 field.**
   Measured on the whole 5,569-strategy bank rather than 10: **304 s per
   strategy** mean (median 240, p90 448; chop 252, trend 327). Two build blocks
   (2011-15, 2011-18) × 8,235 = 16,470 fine-tunes ≈ **1,390 core-hours** at the
   measured rate, ~1,800 if the longer block scales with its length. Mac (9
   cores, ~0.7 duty under the guard): **~9 days**. One CPX62 (16 vCPU at ~0.6×
   a P-core): **~8 days**; three boxes ~2.7 days, ~$20. Not started.

   **(8) CARRY SCOPE — a carry sleeve from the repo's 2-year yields.** Data:
   `data/rates2y.csv` (7 currencies, 1998-06 → 2026-08; **NZD absent**, CAD
   89%, CHF 93% coverage) and `data/carry28.csv` (21 of 28 pairs, 1999 →
   2026-07). Construction: rank the 21 pairs by 2y differential monthly, long
   the top third / short the bottom third at month-end, held a month, sized like
   the rest — marks on the same daily OANDA closes, so it enters the netting as
   28 more members whose positions net against the strategies' at the (pair,
   day) level, with its own slice label `carry` and no regime gate. Effort:
   one day — a mark generator in `l2walkfwd` shape, the NZD gap either left
   (21 pairs) or filled from RBNZ data (a fetch, blocked in the sandbox per
   HANDOFF_3 §2). Known prior: HANDOFF_3 §16.5 found carry signals at 50%
   retention for REGIME prediction; that is not the same question. Not started.

   **THE SWAP — decided by Jack, gated on the A2 control, NOT executed.** Four of
   the five checks hold on 5pm as well as or better than on noon over the same
   window; one does not — the single pre-specified contrast that ever held
   (strong chop vs strong trend on bars to peak) holds on noon and fails on 5pm
   on the same window, and the signal-library gauntlet drops from 61 survivors
   to 5. Neither is a property of the states Layer 2 routes on, and the routing
   test says the 5pm states route as well as the noon ones — but the gate set
   was "the A2 control confirms the validation", and it confirms four of five.
   Prepared and reversible: `results/layer1_states_5pm.csv` (validated, to
   2020-12-31); the full-length 5pm states with 2021+ tagged `sealed`; the
   reader fix (`comment='#'`) is a one-line change in each reader listed in
   FIXES. Not done: the rename, the `pipeline.py` source switch, the `scores6`
   regeneration. Say the word and it is one commit.

0b. **THE CLEAN-FIELD RESULT (12-13 Sep) — THE HONEST NUMBER, THREE SLICES AND
   FOUR.** Fields chosen on W2 alone under `ip1`, walked forward 2016-2020,
   costs charged, both nulls valid and drawn from the same field as the real.
   Every cell below is team1 / team2 (3.6%/3.6% and 5.4%/3.6% budgets); members
   are step 1 → step 2. Full tables: `results/walkforward_report_3slice_cleanfield.csv`
   and `..._cleanfield_4slice.csv`.

   **Three slices — `gate2_cleanfield.csv`, 4,807 (A-trend 2,960 / A-chop 930 / B-chop 917)**

   | structure | members | median yr | worst yr | max DD | worst day | DIP95 | PF | Sortino | Calmar | identity p | random-entry p |
   |---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
   | NO_CUT | 4807→4807 | 5.02 / 7.53 | 4.59 / 6.89 | 2.01 / 3.02 | 0.56 / 0.83 | 3.09 / 4.63 | 1.51 | 3.90 | 14.5 | — | 0.000 (null max 0.00) |
   | NO_CUT_SLICE_BALANCED | 4807→4807 | 5.82 / 8.72 | 4.96 / 7.45 | 2.26 / 3.40 | 0.69 / 1.03 | 3.48 / 5.22 | 1.53 | 4.02 | 15.5 | — | 0.000 (null max 0.00) |
   | ALLPASS | 1094→1008 | 2.06 / 3.09 | 0.44 / 0.66 | 3.02 / 4.53 | 0.78 / 1.17 | 4.43 / 6.64 | 1.21 | 1.66 | 4.0 | 1.000 | 0.000 |
   | STABLE | 823→19 | 0.94 / 1.41 | -4.52 / -6.78 | 5.48 / 8.22 | 0.44 / 0.66 | 5.98 / 8.97 | 0.99 | -0.05 | -0.0 | 1.000 | — |
   | SLICE_BALANCED | 1094→1008 | 0.61 / 0.92 | -1.49 / -2.23 | 2.63 / 3.95 | 0.41 / 0.61 | 3.87 / 5.81 | 1.16 | 1.48 | 3.2 | — | — |
   | PICKED | 14→16 | 0.09 / 0.13 | -2.28 / -3.42 | 6.25 / 9.38 | 1.56 / 2.34 | 10.04 / 15.06 | 1.11 | 0.92 | 1.9 | 0.960 | — |
   | FAMILY_CAP | 4→5 | -1.01 / -1.52 | -2.13 / -3.19 | 3.98 / 5.97 | 0.63 / 0.94 | 7.27 / 10.90 | 0.95 | -0.30 | -0.5 | 0.960 | — |

   **Four slices — `gate2_cleanfield_4slice.csv`, 8,235 (+ B-trend 3,428)**

   | structure | members | median yr | worst yr | max DD | worst day | DIP95 | PF | Sortino | Calmar | identity p | random-entry p |
   |---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
   | NO_CUT | 8235→8235 | 5.09 / 7.64 | 3.93 / 5.89 | 1.86 / 2.79 | 0.64 / 0.96 | 3.04 / 4.56 | 1.49 | 3.92 | 15.0 | — | 0.000 (null max 0.19) |
   | NO_CUT_SLICE_BALANCED | 8235→8235 | 4.60 / 6.91 | 2.80 / 4.20 | 2.65 / 3.97 | 0.62 / 0.93 | 3.37 / 5.06 | 1.46 | 3.71 | 10.9 | — | 0.000 (null max 0.02) |
   | ALLPASS | 2323→2142 | 2.85 / 4.27 | 0.44 / 0.66 | 3.20 / 4.80 | 0.71 / 1.06 | 4.57 / 6.85 | 1.23 | 1.84 | 4.7 | 1.000 | 0.000 |
   | STABLE | 1888→40 | 1.24 / 1.86 | -2.07 / -3.10 | 2.63 / 3.94 | 0.38 / 0.57 | 4.83 / 7.24 | 1.06 | 0.49 | 1.0 | 1.000 | — |
   | SLICE_BALANCED | 2323→2142 | -0.94 / -1.42 | -1.70 / -2.55 | 4.06 / 6.09 | 0.31 / 0.46 | 5.65 / 8.47 | 0.89 | -0.97 | -0.8 | — | — |
   | PICKED | 22→30 | 3.04 / 4.55 | 2.02 / 3.02 | 4.32 / 6.87 | 1.69 / 2.41 | 10.76 / 15.57 | 1.20 | 1.46 | 5.9 | 0.320 | — |
   | FAMILY_CAP | 3→3 | -0.42 / -0.63 | -0.97 / -1.45 | 2.76 / 4.15 | 0.54 / 0.80 | 5.31 / 7.97 | 1.05 | 0.22 | 0.6 | 0.720 | — |

   **Per slice, each walked alone with the cut (four-slice field; the first three are identical in the three-slice run)**

   | slice | strategies | passers | median yr | worst yr | max DD | worst day | PF | Sortino | Calmar |
   |---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
   | A-trend | 2960 | 921→882 | 0.23 / 0.35 | -0.29 / -0.44 | 1.01 / 1.52 | 0.24 / 0.36 | 1.06 | 0.36 | 1.0 |
   | A-chop | 930 | 82→53 | 5.85 / 8.77 | 2.39 / 3.58 | 2.34 / 3.51 | 1.19 / 1.78 | 1.44 | 2.59 | 12.9 |
   | B-chop | 917 | 91→73 | 4.17 / 6.26 | 1.04 / 1.56 | 2.76 / 4.14 | 0.94 / 1.41 | 1.40 | 2.30 | 8.8 |
   | B-trend | 3428 | 1229→1134 | 0.85 / 1.28 | 0.00 / 0.00 | 0.81 / 1.21 | 0.31 / 0.47 | 1.19 | 1.08 | 4.4 |

   **On the p-values.** Identity p: the strategy is admitted on a *random other
   strategy's* build record and trades its own; p is the share of 25 draws at or
   above the real. Random-entry p: every trade keeps its size and holding period
   but enters at a random bar; p as above. **The random-entry null of the UNCUT
   book is vacuous by construction and is reported as such**: the sizing curve
   sizes on |net votes| / members and gives zero to bins that do not earn, and
   under random entries thousands of members disagree on direction on every
   (pair, day), so the book carries almost nothing — every draw scores within
   0.00-0.29% of zero. The real beats all 25, but the null has no width. The
   cut book (1,094-2,323 members) nets less completely and its random-entry
   null is a genuine distribution. **The "—" cells are absences, not
   omissions of a number that exists:** the uncut book has no selection to
   permute, so its identity null is the real walk by construction (every
   strategy passes whatever build record it is handed); and the random-entry
   null walks the cut book as ALLPASS and the uncut pair only, so STABLE,
   SLICE_BALANCED, PICKED and FAMILY_CAP have no random-entry p — their
   entries are ALLPASS's entries, and ALLPASS's p is 0.000 on both fields.

   **Plain English.** The strategies have edge and every form of selection
   destroys it, on both fields. Trading the whole clean field, equal weight,
   nothing filtered, made 5.0% a year at the conservative budget on three
   slices and 5.1% on four, with a worst year of +3.9% to +4.6% and a drawdown
   of 2%. The gate-3 cut alone takes that to 2.1-2.8% and raises the drawdown;
   admitting strategies on their own build record picks *worse than random* —
   the identity null beats the cut book in 25 of 25 draws on both fields
   (p=1.000). Stability, greedy search and the family cap take it to zero or
   below on three slices; on four, greedy reaches 3.0% but sits at the 68th
   percentile of its null (p=0.32) — not a result. Adding B-trend neither
   raised nor diluted the book: its 3,428 strategies earn 0.85% alone (above
   A-trend's 0.23%, far below the chop slices' 4-6%), and the netted book
   absorbed them at the same median with a lower drawdown and a lower worst
   year. The trend slices are 78% of the strategies and roughly 15% of the
   return; the two chop slices are the engine. Equal weight per slice helps the
   uncut three-slice book (5.8%) and hurts the four-slice one (4.6%), because
   it now hands half the book to the trend slices. **The honest system is the
   whole clean field, not a team.** The open question is whether a null that
   keeps direction agreement and randomises only timing would give the uncut
   book a real p-value; nothing here claims one.

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

Contaminated field (3,485): engine 32.3 min · real walks 7.3 min · sizing 7 s ·
team-size sweep 30.7 min · identity null 36.6 min per budget · random-entry
null 2.6 min per budget.

Clean field (4,807), 12 Sep, RAM-capped: engine 32.1 min (9 workers) · walk
15.8 min · identity null 133 min (6 workers, 59 min per budget) · random-entry
null 4.9 min (3 workers, 2.3 min per budget, after the K/BR pickle fix) ·
sizing 7 s · team-size sweep 31 min · slice controls 50 s · per-slice walks
10 s · uncut random-entry null 9 min (2 workers). B-trend W2 scoring 35.9 min
(14,815 at 0.87 s, 6 workers).

Clean field, four slices (8,235), 12-13 Sep: engine 49 min (9 workers) · walk
64 min · identity null 470 min (3 workers, ~203 min per budget) · random-entry
null 8.5 min (3 workers) · sizing 25 s · team-size sweep 90 min (2 workers; one
worker peaks at 5.7 GB on the ALL team size) · slice controls 2 min · per-slice
walks 10 s · uncut random-entry null 17 min (2 workers).

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
| **23 Sep** | **ONE PROMPT, ONE CHAINED DRIVER.** When a prompt lists more than one step, every step goes into a single detached driver — with a marker line per step and a final COMPLETE marker — and that driver is launched before the first step starts. No step ends with nothing running; no step waits for a reply. Launch with `~/fx-data-logs/launch.sh <driver>` so the pid is confirmed alive after 60 s, post the estimate, and start immediately. |
| **15 Sep** | **NO VOTE ON THE FILL DAY.** A position may not vote on a (pair, day) row until the day AFTER its fill. The engine fills at the signal bar's close, so a fill on D is decided by D's close, and row D's mark is that day's move of the other members' positions. Enforced mechanically: `l2walkfwd.check_no_same_day_entrant` halts any walk whose vote includes a same-day entrant; `VOTE_ON_ENTRY_DAY = False` is the only default; `WF_ALLOW_VOTE_LEAK=1` is the sole way through and prints CONTAMINATED. Every book in the repo is built through `Book`, so the rule covers walk-forward, all three nulls, team-size, agreement, opposition, exit, kill-switch, carry. `l2layer4.py` / `l2layer4v2.py` carry their own netting with the same fault: retired, headered, not fixed. Per-strategy scoring (`l2tune.Scorer`, gate 2/3, the refit pilot) never touches `Book`. |
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
