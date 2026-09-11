# FIXES OWED — deliver these to Claude Code

## 2026-09-11 — PROCESS FAILURE: git tree operations under live background work

**Mine, not the code's. Two hours lost, nothing corrupted.**

While three background jobs were writing to `results/`, I ran `git stash -q -u`
to get a clean tree for a rebase. `-u` stashes UNTRACKED files, which unlinked
both chain logs out from under running processes — they kept writing to deleted
inodes, `chain3.sh` lost its stdout and died, and the three-slice clean field
never started. The same stash also took the MODIFIED `code/l2walkfwd.py`
carrying the `--suffix` / `--field-file` support, and the
`git stash pop -q 2>/dev/null` afterwards failed silently. Six chain stages then
ran against a binary that had never heard of `--suffix` and exited in one second
each.

**The compounding error was `2>/dev/null` on the pop.** The one message that
would have said "your work is still in a stash" was the one I threw away. The
chain's own `|| echo FAILED` guard worked perfectly and printed all six
failures; it was the git error I suppressed, not the job errors.

### Rules, now binding

1. **Never `git stash` while background work is running.** Stage explicit paths
   — `git add <path>` — or wait. `-u` in particular deletes untracked files from
   the working tree.
2. **Never redirect a git error to /dev/null.** Not `pop`, not `pull`, not
   `rebase`. If a git command can fail silently it eventually will, and the
   failure surfaces somewhere unrelated an hour later.
3. **Commit a code change before launching a chain that depends on it.** A
   committed file cannot be lost by a stash, and a chain that fails on arguments
   is a chain whose code was never verified to exist.
4. **Chain logs live outside `results/`**, in the scratchpad, so git operations
   on the repo cannot touch a running job's stdout.

Nothing was corrupted and no result was wrong — `gate2_cleanfield.csv` and
`field_diff.csv`, the expensive 61.5-minute part, were already on disk. The cost
was entirely wall clock.

---

## 2026-09-10 (late 2) — THE WALK-FORWARD'S YEAR-SHUFFLED NULL IS CONFOUNDED

**Third null in two days that changes the wrong thing.** Registered here as a
pattern, not a one-off: every null must be checked against what it actually
perturbs before its p-value is read.

### What happened

The walk-forward structures run used a year-shuffled null: permute calendar
years, re-run the whole walk. In a WALK-FORWARD that is not the l2teamcheck
no-op — permuting years changes which years are build and which are traded, so
it does destroy the persistence claim. That much was right.

**But it also changes WHICH YEARS GET TRADED, and the decade is not uniform.**
2011-2015 is far richer than 2016-2020 for this field (the same fact the
retention figure of ~25% reports). So a draw that happens to trade rich years
scores well for a reason that has nothing to do with persistence.

Measured across the 25 draws, team1 ALLPASS:

    rich years traded   draws   mean null score
        1                 3          3.357%
        2                12          5.290%
        3                 7          6.837%
        4                 3          7.663%
    correlation 0.377, monotone

**None of the 25 draws traded the real walk's composition of ZERO rich years.**
The real walk always trades 2016-2020. It was being compared against draws that
all got an easier stretch.

Fitting null score on rich-years-traded and reading it at zero:

    team1  null = 2.308 + 1.445 x (rich years)  ->  2.308%  vs real 2.274%
    team2  null = 3.465 + 2.164 x (rich years)  ->  3.465%  vs real 3.412%
    raw p = 0.80        confound-adjusted p = 0.52

So the verdict changes from "decisively worse than chance" to "indistinguishable
from chance". Still no demonstrated persistence — but the stronger claim was an
artefact.

**The tell was the direction.** A real walk losing to its own null by a factor
of two is not a finding, it is a symptom. Check the direction of every null
before reading its p-value.

### Files

`results/walkforward_null_3slice.csv` and `..._null_summary_3slice.csv` are
**marked SUPERSEDED in a header note** carrying the table above. Kept as record,
not to be quoted.

### Replaced by two nulls that each answer one question

1. **IDENTITY** — `walkforward_null_identity_3slice.csv`. Traded years held at
   2016-2020; only the link between a strategy and its build-year metrics is
   permuted, so a strategy passes the cut on someone else's record and trades
   its own marks. Answers: **does build-year quality predict trade-year
   quality?** Verified to behave: 620 passers either way, overlap 111 against
   ~110 expected by chance.
2. **RANDOM ENTRY** — `walkforward_null_randomentry_3slice.csv`. Same
   strategies, pairs, directions, stop and target distances and maximum holds;
   entries moved to random bars inside the trade window. Answers: **is ALLPASS's
   2016-2020 result better than nothing at all?**

### A second bug found while building them

**`pick_stable` used the wrong window.** It read `build[1] - 2 .. build[1]` —
the SECOND element of the build-year list, not the last three. Step 1's build
window is 2011-2015 and it was cutting on **2010-2012**, a year of which has no
data at all. Corrected to the last three build years in play order. STABLE's
membership changes from 23 to **441** at step 1 and 12 to **16** at step 2, so
every STABLE number reported before 2026-09-10 22:50 is void.

### And a writer flaw, fixed

The null accumulated both budgets in memory and wrote once at the end, so a
crash in team2 would have destroyed team1's 16.4 minutes of finished draws. Now
writes per budget.

---

## 2026-09-10 (late) — ALLPASS BUILT; THE GREEDY NULL IS BROKEN; COSTS WERE NEVER CHARGED

Three results, in order of how much they change.

### 1. `l2teamcheck.py`'s year-shuffled greedy null is a no-op. p=0.60 is void.

`l2teamcheck.py:88-93` draws ONE permutation and applies it to the whole matrix:

    perm = rng.permutation(uy); mapping = dict(zip(uy, perm))
    ysh = np.array([mapping[y] for y in years])
    order = np.argsort(ysh, kind='stable')
    TM.greedy(A[order], cols, ..., ysh[order], ...)

Every member moves together. Within-year day order survives the stable sort, and
`score_team` groups by the relabelled years, so the year blocks are the SAME
BLOCKS under new names. Each member's daily series, every cross-member same-day
alignment, every yearly total and therefore the MEDIAN YEAR — the score — are
arithmetically unchanged. Only the path-dependent max drawdown moves.

Verified on synthetic data:

    real yearly sums  [2.1511 0.6611 2.4805 1.9284 2.4635]
    null yearly sums  [2.4805 2.4635 1.9284 0.6611 2.1511]

and reproduced on the real ALLPASS book, where the identical null returns
p = 0.66 against the team's 0.60.

**The docstring describes the right test and the code does not implement it.**
A per-member permutation does destroy cross-member timing — but it also destroys
the CORRELATION that sets the drawdown the budget divides by, so the null book
scores five times the real one and returns p = 1.00. **Neither year-shuffle
variant is a usable edge test for a drawdown-scaled portfolio.** One changes
nothing; the other changes the wrong thing.

**Consequence:** the greedy roster search still fails, but on ONE test, not two.
The selection holdout (8% retained) is valid and sufficient. The inference drawn
from the null — "the search extracts individual quality, not any relationship
between them" — is **unsupported and retracted**.

**Owed:** `l2teamcheck.py` still contains the broken null. It was left alone
because the team 2 run was mid-flight in it. Either fix it to permute per member
AND stop treating the result as an edge test, or delete it and keep the holdout.
Do not leave a test in the tree that returns 0.6 on unchanged data.

### 2. The delivery path has never charged costs.

`l2trades.run_pair` calls the engine directly and returns GROSS R. Only
`l2sweep.score_combo` and `l2tune.Scorer` subtract `S._cost_R`. So
`l2deliver.blind_trades` (whose comment claims "the fees applied here"),
`l2team._equity_series` and `l2layer4v2.marks` are all gross — and therefore so
are every team KPI, every portfolio preview and every Layer 4 level ever
reported.

Measured: **2.6%-8.5% of gross R per strategy, and 18-19% of the median year**,
the larger figure because costs also widen the daily losses and shrink the scale
the risk budget allows.

`code/l2allpass.py` charges the cost on the entry day's mark and reports gross
beside net. **Owed:** do the same in `run_pair`'s consumers, or in `run_pair`
itself behind a flag, so one path cannot be silently gross while the other is
costed. That asymmetry is the same shape as the mode-B hardcode.

### 3. ALLPASS is built. `code/l2allpass.py`, `results/allpass_summary.md`.

All 252 passers, equal weight, no selection, costs charged. Team 1 curve 1/3/6
with the 2% cap: **median year 6.87%**, worst 4.57%, max DD 2.57%, PF 1.50.
Team 2: 10.30%. Stacked beats it in-sample (8.24% / 12.35%).

**Honest holdout — re-cut on 2016-2018 across all 5,201 crossers, scored on
2019-2020: 2.22%, 22% retained** (stacked 0.37%, 3% retained, negative worst
year). Control: re-cutting on the full W3 through the same path gives 271
passers containing all 252 of the real cut.

Two things fall out of it and both need work:

- **The CUT is a fit to its window.** 262 pass on 2016-2018; only **76** of them
  are among the real 252. Which strategies clear gate 3 is ~30% reproducible
  when the window moves. This is a layer of fitting BELOW the roster search and
  it was hidden by it. **Owed:** decide whether gate 3's bars need a stability
  requirement across sub-windows, rather than a single pass on the whole window.

- **The 1/3/6 curve does not transfer to 252 members.** Level is an absolute
  net-vote count, so it runs to 171 and the curve is flat at 6.0 from 3 up:
  level 1 is 14.7% of position-days, level 2 is 16.4%, **level 3+ is 68.9%**.
  The agreement study calibrated "stop at 3" where level 4 meant near-unanimity
  of 25 members. **Owed:** a curve on the FRACTION of members voting, not the
  count. Not built.

**The agreement signal itself is real and this is the one clean positive.** A
level-permutation null — keep every netted position's pair, day, direction and
mark, permute only the agreement LEVELS across positions, so the size mix is
identical and only the assignment changes — gives real 6.865% against a null
mean of 3.090% and a null MAX of 4.418%. **100 of 100 draws beaten, both
budgets, p = 0.00.** Knowing which positions carry high agreement more than
doubles the score. It is the sizing rule that wastes it, not the signal.

**Also owed:** the 2% currency cap binds on **0 days of 1,296** at this size
(largest exposure 0.53%). Harmless, but it is no longer doing what the 25-member
measurement said it did.

**Not owed but noted:** Layer 2 results are not wired into `app_ui.js` or
`app_data.json` — none of them are, this is not new — and ALLPASS is not in
`l2chain2.sh`, which is still built around the retired greedy team.

---

Work through in order. Each is self-contained.

---

## 1. Commit the handoff

`HANDOFF.md` is in the repo folder but uncommitted.

```
commit and push HANDOFF.md
```

---

## 2. Wait for the running build, then confirm it worked

A GitHub Actions run is generating `results/scores5/` right now. Do not touch anything
until it finishes.

```
check the latest GitHub Actions run on Jackscuster/fx-data. Tell me if it succeeded and
how many signals are in app_data.json at the repo root.
```

**Expected: 20,275 signals.** If it says 12,413, `scores5` didn't commit — say so.

---

## 3. Recreate STRATEGY_TEMPLATE.md

Referenced by HANDOFF.md §13 but never committed.

```
Create STRATEGY_TEMPLATE.md at the repo root. It documents the standard output format
for strategy results. Structure only, no example numbers.

Two blocks.

Block 1, raw metrics, one column per regime state plus a BASELINE column (strategy run
on all data, unfiltered):
Net Profit, Return/DD, Profit Factor, #Trades, Win%, $AvgTrade, Exposure,
Return/Exposure.

Block 2, regime comparison:
Data % (share of all bars the regime covers; baseline = 100%), then % improvement vs
baseline for Ret/Exp, Ret/DD, PF, Win%, $AvgTrade. Baseline column reads 0% down this
whole block by construction.

Rules to state explicitly:
- Improvements are NOT uniform. A filter can lift profit factor and win rate while
  making drawdown worse. Report every row including the negatives.
- Report return AND drawdown together. Never present one as a trade against the other.
- Costs applied. Crosses have wider spreads than majors; do not assume one spread across
  all 28 pairs.
- Same IS/OOS split as the signal work: fit on 1999-2015, confirm on 2016-2026.
- Data % is essential. A regime covering a thin slice of bars with great numbers is a
  curve fit, and this row is what exposes it.

Note as unresolved: the exact normalisation for the Return/Exposure row is unconfirmed.

Commit and push.
```

---

## 4. Pool the chop target properly

**This is a real bug, not cosmetic.** `sc5.py` scores two targets and writes both:
`qt*/nt*/vt*` for trend, `qc*/nc*/vc*` for chop. `prep.py` only reads the trend arrays.
So chop is computed, sitting in the `.npz` files, and never used.

Consequence: every signal currently labelled "chop" is really a *negative efficiency*
reading — "not trending." That is not the same as "actively whipsawing." The genuine
chop target (forward 20-day turn frequency) has never reached `signals.json`.

```
prep.py currently pools only the trend target. sc5.py also writes a chop target under
qc*/nc*/vc* which is never read.

Extend prep.py so each signal record also carries chop-target fields — cti (t in-sample),
cto (t out-of-sample), cso (spread OOS), cao (pair agreement OOS) — read from the qc*
arrays where present, null for the older score dirs that only have one target.

Then extend bundle.py and app_ui.js so the All Signals table can sort and filter on the
chop target separately from the trend target, and each row shows which target it is
strongest on.

Commit and push.
```

---

## 5. Add the two missing analysis scripts

`ladder.py` and `funnel.py` were written but never committed. Because of this the
**Detectors tab is empty** and **part of the Verdict tab is empty** in the app.

```
Two scripts are missing from code/. Write them following the same structure as
framework.py (same imports, same ROOT path header, same 28-pair loop, costs of 1.5bp for
majors and 3.0bp for crosses).

ladder.py — applies each of the four detectors in framework.py (trend_sma200,
vol_regime, markov_naive, hmm_2state) as a filter to two baseline strategies
(mean reversion n=60 entry 2.0, and momentum 30/120). For every detector-state cell,
compute the STRATEGY_TEMPLATE metrics plus data_pct, then the % improvement vs the
unfiltered baseline. Write results/detector_ladder.csv.

funnel.py — reads results/logic_results.csv and produces the three-stage DSR attrition
table: total variants tested, how many show positive OOS Sharpe delta, how many survive
deflated Sharpe at 0.95. Write results/dsr_funnel.csv.

Add both to pipeline.py after framework.py. Confirm bundle.py already reads
detector_ladder.csv and dsr_funnel.csv — it does.

Commit and push.
```

---

## 6. Add the crisis event calendar

48 dated crisis events, 2000–2026. Built and validated in chat, never committed.

**The rule that makes it valid: every date comes from news — a policy decision, an
intervention, a bankruptcy, a referendum. No date was ever chosen by looking at price.**
Without that, validating detectors against it would be circular and meaningless.

```
Create code/events.py holding a dated FX crisis calendar as a list of tuples
(date, type, ccy, severity, description), with a calendar() function returning it as a
DataFrame with parsed dates.

Types: policy, intervention, credit, geopolitical, pandemic, vote, commodity.
ccy is the currency at the epicentre, empty string for broad events.
Severity 1 minor, 2 major, 3 systemic.

Document at the top of the file, prominently: every date comes from a NEWS event, never
from price. This is what makes detector validation non-circular.

Include at minimum these anchors: 2001-09-11 September 11; 2007-08-09 BNP freezes funds,
first carry unwind; 2008-09-15 Lehman; 2010-04-23 Greece bailout request; 2011-03-11
Tohoku earthquake; 2011-09-06 SNB announces EURCHF floor; 2012-07-26 Draghi whatever it
takes; 2013-04-04 BOJ QQE; 2015-01-15 SNB abandons floor; 2015-08-11 China devalues;
2016-06-23 Brexit referendum; 2018-02-05 volatility complex blow-up; 2020-03-11 WHO
declares pandemic; 2020-03-15 Fed emergency cut and swap lines; 2022-02-24 Russia
invades Ukraine; 2022-09-22 first MOF yen intervention since 1998; 2022-09-23 UK
mini-budget gilt crisis; 2023-03-10 SVB failure; 2023-03-19 Credit Suisse rescue;
2024-03-19 BOJ ends negative rates and YCC; 2024-07-31 BOJ surprise hike, carry unwind
begins; 2024-08-05 global carry unwind peak; 2025-04-02 US reciprocal tariff
announcement; 2026-07-31 US-Japan coordinated intervention. Fill in others you can date
confidently from news.

Then write code/crisis.py which scores candidate crisis detectors against this calendar
using a FORWARD-ONLY window (event date to +15 days). For each detector report: events
caught, recall, base firing rate, lift over chance, and median days from news.

IMPORTANT: the window must not start before the event date. An earlier version used a
window starting 5 days before and produced a false "fires 2.5 days early" result that
vanished under forward-only testing.

Add both to pipeline.py and wire the output into bundle.py and app_ui.js as a Crisis tab.

Commit and push.
```

---

## 7. Run /init

One-time. Creates a `CLAUDE.md` that loads automatically every session so context does
not have to be re-explained.

```
/init
```

Then tell it to reference HANDOFF.md from CLAUDE.md.

---

## WHAT'S RESEARCH, NOT CLEANUP

Everything above is finishing work that was started. These are the genuinely open
questions, in order of value:

1. **Beats-shuffled-labels test.** Shuffle regime labels keeping run lengths, rescore.
   If real labels don't clearly beat shuffled, the estimator is detecting nothing — just
   chopping the sample into persistent blocks. Strongest anti-overfitting test available
   without PnL, and it has never been run.
2. **Vol-targeted position sizing.** Everything trades flat size, so a 4% ATR yen cross
   and a 0.5% EURCHF carry identical risk. Obvious lever for improving return and
   drawdown together. May also deflate the vol detector's apparent edge.
3. **Combined 9-box allocation** — route across all seven positive boxes at once and
   compare to the full-time baseline. No single box can beat a full-time strategy on
   total return; the combination might.
4. **Fix the trend side of the gauntlet.** 171 trend signals clear the t-stat gate, only
   10 clear effect size. Chop is panel-wide and synchronised; trend is idiosyncratic per
   pair. An 85% cross-pair agreement bar may simply be the wrong bar for trend.
5. **Crisis as a scored third target.** Signals for it exist and were never scored.

## OPEN — Layer 1 and Layer 2 do not share a bar

**Blocking: must be settled before Layer 3 routing is built.**

Layer 1 (regime states, crisis flags, low-vol flags) is computed on
`data/px28.csv` — the Fed H.10 **noon New York** series. Layer 2 (every gate 1-3
strategy) runs on `data/oanda_ohlc/*_mid.csv` — OANDA daily mid aligned to
**17:00 New York**. The two layers are five hours apart on every single bar.

Routing a strategy on a regime read taken five hours earlier is not obviously
wrong, but it is not obviously right either, and nobody chose it — it is an
artefact of Layer 1 predating the Layer 2 data build. Before routing is built,
Layer 1 must be recomputed on the OANDA 5pm series so the regime and the
strategies it routes share one bar.

### Work involved

Mechanical rather than conceptual. `build.py` produces px28 from H.10; the Layer
1 chain (`sig2..sig5`, `sc2..sc5`, `measures.py`, `shapescore.py`,
`twoscores.py`, `export.py`, `appfeed.py`) reads it. The change is a source
swap plus a full rescore. Every scorer is resumable and idempotent but keyed on
existing `.npz` files, so a source change means **discarding results/scores*/ and
rescoring from cold — roughly 40 minutes per the documented cold-build time**,
plus the analysis chain on top. Call it half a day of machine time, no new logic.

### The history question, which is the real cost

**H.10 reaches 1999. OANDA daily reaches 2002-06; OANDA hourly only 2004-05.**
Moving Layer 1 to the OANDA series **loses 1999-2002 entirely** — three years,
including the euro's first years and the 2000-2002 dollar cycle.

Layer 1's split is IS 1999-2015 / OOS 2016-2026, so this removes ~18% of the
in-sample window. Whether any Layer 1 survivor **depends** on that period is
NOT yet known and must be measured before the swap, not after: re-run the Layer
1 gates restricted to 2002+ and compare the survivor set. If survivors are
stable, the swap is cheap. If the pre-2002 years are carrying a survivor, the
choice becomes explicit — a shorter shared-bar history against a longer
mismatched one — and that is Jack's call, not a silent consequence of a refactor.

**Do not start this yet.**

## OPEN — W2 CONTAMINATION: the FULLSTITCH rebuild (hard follow-up)

**Found 2026-09-08. Everything downstream of gate 2 scored W2 with `ip2`.**

The walk-forward stitch is W2 under the FIRST tune (`ip1`) and W3 under the
second (`ip2`). `ip2` was tuned on W1+W2. `l2deliver.blind_trades` and
`l2team._equity_series` take trades from W2 **and** W3 using the gate 2 `cfg`,
whose settings are `ip2` — so every W2 number in the leaderboards, the co-equal
ranking, the graft, the portfolio previews and the gate 3 cut was measured with
parameters that had already seen that window.

**Measured on the eight graft members that do have `ip1`: W2 total R is 452.0
under `ip2` against 92.4 under `ip1` — +389%.** Trade counts differ too, so it is
not a scaling artefact: `ip2` selects different trades.

### Done now (W3ONLY)
W3-only re-score under `ip2`, which no tune has seen. Half the blind sample, all
honest. Every output labelled `W3ONLY`.

### The follow-up, which is NOT done
1. **Recover `ip1` for all B-trend crossers** — mode B's trend slice never
   banked it (A and C do; C banks it on all 7,472 rows). ~1,650 strategies at
   ~100 s each on one core, roughly **10 h**. `code/l2recoverip1.py --which all`.
2. **Full W2(`ip1`)+W3(`ip2`) stitch re-score** for every crosser in every mode
   and slice, cost-charged.
3. **Rebuild** leaderboards, co-equal ranking and the gate 3 cut from the full
   stitch, labelled `FULLSTITCH`.
4. **Re-run the adoption evaluation** for every finished fine-tune strategy
   against a clean incumbent.
5. **Re-run the team builder and agreement study** on the full stitch and report
   every roster difference against the W3-only team.
6. **Mode C**: banks `ip1` already, so no recovery is needed — but its 299
   finished chunks were scored through the same contaminated path and are marked
   for clean re-scoring when C resumes.

**Gate 2's pass bars are ABSOLUTE** (expectancy 0.08, PF 1.25, Sharpe 0.5,
Sortino 0.7, Calmar 0.6, max DD 20%), not top-N or percentile, so nothing was
displaced by an inflated neighbour and the crosser set is too LARGE, not too
small. Contamination is not strictly monotonic per combination, so a small
number of near-misses could still flip; the FULLSTITCH re-score should include
combinations that failed the label narrowly.

## FIXED 2026-09-08 — run_pair ran every mode as mode B

`l2trades.run_pair` had `kwm = S.mode_kw('B')` hardcoded. The mode sets the EXIT
RULE — A exits on a C1 flip, B on a baseline cross, C on an exit indicator — so
every mode A and mode C configuration was run with **B's exits**. The exit rule
decides when every trade ends, so it changes the trade set outright: one A-trend
strategy gave 46 trades and +97 R scored correctly against 148 trades and -1.1 R
through this path.

**Everything built on run_pair inherited it**: `blind_trades`, `_equity_series`,
the team builder, the portfolio previews, the trade charts, the crisis split.
The tuner was never affected — `l2tune`'s Scorer always passed the real mode,
which is why the bank and the delivery layer disagreed.

Fixed: the mode comes from `src_mode`/`mode`, or the leading letter of
`src_label`/`sid`. If it cannot be determined, run_pair RAISES — guessing
silently is what caused this.

**Invalidated and needing rebuild:** the W3ONLY_GATE2 team (9 of its 25 members
are A-strategies), `graft15_honest_book.csv`, every portfolio preview containing
an A-strategy, and the trades tab for A rows.

## OPEN — trades that never close inside their window

The engine holds a position until its exit rule fires, so a trade entered inside
W3 can still be open at the last bar. Those are marked to the final bar and
counted as realised profit.

Measured: **2.9% of W3 trades across 40 adopted strategies**, and only 12 of
1,792 W3ONLY rows have `cw3_sortino > 200` (2 above 1,000; 3 of 216 adopted).
So it is NOT systemic — but where it bites it dominates. The top W3ONLY
adoption, `ehlers_reverse_ema x kase_peak_oscillator x variance x frama`, has a
13% win rate and its entire +97 R comes from three positions entered in 2020 and
still open in 2026, six years past the window's close.

**Not yet decided:** whether to close open positions at the window boundary and
book the mark, or exclude them. Either changes results; leaving them counted as
realised profit is the one option that is clearly wrong.

## QUEUED — re-runs of everything the mode bug touched

`code/l2rerun.sh`, armed and single-instance. Waits for the main chain AND the
fine-tune, then runs one study at a time on one core at nice 19, so it can never
compete with mode C once the chain relaunches it.

Each of these reads its configurations through `l2trades.run_pair`, which
hardcoded mode B, so every mode A and C row in them was scored with B's exit
rule:

| study | output |
|---|---|
| crisis split, A-trend and A-chop | `gate2_crisis_split_modeA_*_all.csv` |
| suppressed-vol flags | `gate2_*_leaderboard_clean.csv` |
| entry timing | `entry_timing.csv`, `entry_timing_summary.md` |
| calendar | `calendar_dow.csv`, `calendar_holidays.csv`, `calendar_by_member.csv` |
| agreement study | `agreement_*.csv`, `opposition_by_member_*.csv` |
| tripwire (stays PROVISIONAL) | `tripwire.csv`, `tripwire_summary.md` |

**NOT re-run, because they were never affected:** the gate 3 cut and the W3-only
leaderboards go through `l2tune`'s Scorer, which always passed the real mode.
That asymmetry is exactly why the bank and the delivery layer disagreed.

Already rebuilt outside the queue: the W3ONLY_GATE2 team baseline and
`graft15_honest_book.csv`.

## FIXED 2026-09-10 — three stages reported success while doing nothing

All three shared one shape: **a fallback where a failure belonged.**

1. **The cut read a stale verdicts file.** `gate3_costed_verdicts.csv` had only
   ever been produced by an inline script typed by hand on 7 Sep. The chain
   refreshed the W3-only scores and then read the old file, so the team labelled
   ADOPTED was the gate 2 team — confirmed identical member for member. Now
   `code/l2cut.py`, a build product, with `--settings adopted|gate2`.

2. **The agreement study found no roster.** It looked for `team1_roster.csv`;
   the chain writes `team1_W3ONLY_ADOPTED_roster.csv`. It printed "skipped" and
   exited zero in seven seconds. Now honours `TEAM_LABEL` and globs for labelled
   rosters.

3. **The agreement study found a roster with no settings.** The roster is a
   summary carrying the recipe and vote, not `ip2` or the risk parameters, so
   every engine call raised and was swallowed per pair, giving "no position-days"
   after the roster had loaded successfully. Now joins settings from the
   verdicts file and REFUSES to run if any member lacks them.

### The generic guard

`code/l2stagecheck.py` verifies each stage's OUTPUT rather than its exit code:
exists, non-empty, at least a declared per-stage minimum row count, and written
DURING that stage rather than left from a previous run. Failure writes
`results/CHAIN_HALT.marker` naming stage and reason and halts the chain. All six
stages wired; every stage command now exits the chain on non-zero rather than
logging WARN and continuing.

### The swallow audit

Five `except` clauses across l2team, l2agree, l2teamcheck, l2cut, l2deliver;
four were silent. The three identical per-pair swallows around `TR.run_pair`
hid all three faults above — they now COUNT failures by exception type and
**raise if every pair failed**, so an empty book is never returned as a valid
one. The closed-trade DIP95 swallow logs a warning instead of `pass`. `l2cut`
already counted. `l2teamcheck` has none.

## FIXED 2026-09-10 — shard assignment and the chain's completion test

**Position-based sharding let restarted shards claim overlapping work** — 228
duplicate strategy runs, 18.7 wasted core-hours, all byte-identical so nothing
was corrupted. Sharding is now `md5(sid) % shards`, fixed for all time. A
`--leftovers` mode splits remaining work by position instead, safe only when
nothing else is running: it turned 194 leftover strategies from 15 hours on one
core into two hours across nine.

**The chain treated "no shards running" as completion.** Shard 5 died on a
transient `EmptyDataError` at 96.2% and its absence read as done. It now waits
until all 5,135 sids are banked.

## 2026-09-10 — session close

`HANDOFF.md` is now the master record: state of every layer and gate, every bug
found this week with what it contaminated and what was redone, every rule
decided with its date, the queue in order, the files that matter, and the open
questions. Read its ten-line READ THIS FIRST block before anything else.

The fine-tune bank `results/gate3ft_costed_v4/` is back under git. It was
untracked during the run because eight shards appended to it every few seconds,
which aborted every rebase and blocked all pushes for an hour.

**Do not trust any number produced before 2026-09-10 without checking this file
first.** Three separate faults — W2/ip2 contamination, the mode-B exit hardcode,
and open positions booked as realised — each invalidated whole classes of
result, and each was found only because two independently computed numbers
disagreed.

## 2026-09-10 — THE GREEDY ROSTER SEARCH FAILED VALIDATION. RETIRED.

**The 22.97% team score and the 30.22% Layer 4 figure are NOT demonstrated
results. Do not quote them.**

### Greedy null: p = 0.60

    real team score        22.82%
    greedy-null mean       22.79%   <- the search beats this by 0.021pp
    greedy-null p95        23.96%   <- the real score is BELOW this
    greedy-null max        24.63%   <- and below this
    p-value                 0.60    <- 15 of 25 null runs matched or beat it

The null re-runs the SAME greedy search on YEAR-SHUFFLED data. Shuffling
destroys any real cross-member timing structure while preserving each
strategy's own return distribution. A search on destroyed data reaching the same
score means the search is extracting the strategies' individual quality, not any
relationship between them. There is no demonstrated selection edge.

### Selection holdout: 8% retained

    roster re-picked on 2016-2018    41.83% on its own picking window
    the same roster on 2019-2020      3.33%
    retained                             8%
    full team on that holdout         17.55%

A roster chosen on three years keeps 8% of its score on the two it never saw.
That is a fit to the picking window.

### What passed, and why it is not enough

The random-team comparison: the real team sits at the 100th percentile of 1,000
random draws (mean 7.98%, max 12.06%). This was always the weak test — **a
greedy search beats random selection even on pure noise**, which is exactly why
the year-shuffled null was built alongside it. The weak test passing while the
strong one fails is the expected signature of a search fitting noise.

### Consequences

- **Greedy roster search is retired.** Do not build another team with it.
- **UNAFFECTED:** gate 3, the fine-tune, the cut, the adoption rule, and the 252
  passers as individual strategies. Their gate 3 verdicts stand on their own
  merits and were never selected against each other.
- **AFFECTED:** every number that depends on a specific roster — team KPIs,
  per-year returns, the gate-2 baseline comparison, and Layer 4's absolute
  levels.
- **POSSIBLY SURVIVING:** Layer 4's RELATIVE finding, that netting and the 1/3/6
  curve beat stacking. That is a comparison of sizing methods on a FIXED roster
  rather than a comparison of selections, so it does not obviously inherit the
  fault — but it has not been re-tested on a validated roster, because there
  isn't one.

### What a replacement needs

Any future selection method must clear the year-shuffled greedy null, not merely
the random-team draw. The agreement study's own null (membership shuffle, p=0.0000
at the 100th percentile) is the standard to match: that one passed decisively on
the same data, which is evidence the test is capable of detecting real structure
when it is there.
