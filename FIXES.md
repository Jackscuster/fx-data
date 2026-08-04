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
