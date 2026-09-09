# FIXES OWED — deliver these to Claude Code

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
