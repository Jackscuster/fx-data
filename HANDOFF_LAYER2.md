# LAYER 2 KNOWLEDGE BASE — READ BEFORE THE WORK ORDER

You are Claude Code working in Jackscuster/fx-data (~/Documents/fx-data).
A separate chat (Claude) does design; you build. This is your base context for
all Layer 2 work. The work order follows in the next message.

REVISED 2026-08-14 after an audit against the committed results. Three claims
in the first draft did not match the files and are corrected below: the
interface file, the stand-aside share, and whether either regime axis beats
its null. Routing decisions added. Every number here is quoted from a file in
results/ — the file is named next to it.

## WHERE THE PROJECT IS

Layer 1 — a regime classifier for 28 G8 FX pairs — is FINISHED AND FROZEN.
It says what state a pair is in right now: trending, ranging, trend-in-range,
or neither, crossed with strong/medium/weak activity, plus an acute-crisis
overlay.

THE INTERFACE IS results/layer1_states.csv — 191,940 rows, long format, one
row per pair-day: date, pair, trend_score, chop_score, shape2, activity,
scale_28, combined2, settling, m_fail, m_retr, m_space, m_panel, sample. It
carries the two raw scores, the activity word, the dwell fraction (settling)
and the IS/OOS flag, which the wide file does not. Read this one.

results/states_g4_twoscore4.csv is a DERIVED VIEW of it — the shape2 column
pivoted wide, 6,855 dates x 28 pairs, 98.6% covered. Convenient for eyeballing,
but it drops everything Layer 2 needs to condition on.

THE ACUTE-CRISIS FLAG IS NOT IN EITHER FILE. It is PANEL-WIDE, not per-pair —
738 flagged dates out of 6,855 (11%) — and lives in app_regime.json under the
"crisis" key as integer indices into its "dates" array. Layer 2 joins it itself
as a date-level column, applying to every pair on that date.

These files are an interface: Layer 2 consumes them, never modifies them, never
retunes them. If you find a Layer 1 defect, report it — do not fix it in place.

Layer 2 — the strategy library — starts now, from zero. The placeholder
strategies from earlier phases are dead. Money metrics (Sharpe, PnL, drawdown)
are permitted in Layer 2 — that is the point of it — but never leak back into
Layer 1 evaluation.

## WHAT LAYER 2 IS FOR

Jack's risk management is already settled (below). The regime estimator's job
is to pick which risk plan runs on a given pair on a given day: the two-leg
trend plan, the one-leg quick-target plan, or stand aside. Layer 2's job is to
find the entry machinery — which indicator combinations get into the market at
the best times. The strategy search runs on Jack's NNFX builder design (a Pine
strategy on TradingView), which we are porting to Python so millions of
combinations can be tested honestly.

## JACK'S RISK RULES — FIXED, NEVER SWEPT, NEVER OPTIMISED

- 2% account risk per trade, never more. Sizing: risk$ / stop distance, so
  dollar risk is identical every trade.
- Trend plan: two legs, 1% each, same entry. Leg 1: stop 1x ATR, take-profit
  1.5x ATR — banks the quick win. Leg 2: no TP; stop 1x ATR, moves to
  breakeven when Leg 1 banks, then trails 1.5x ATR behind the highest close
  once price is 2x ATR in profit.
- Chop/crisis plan: one leg only, quick target, no runner.
- Positions are never resized mid-trade; stops only move in the trade's favour.
- Daily bars only. Entries fill AT the close of the signal bar
  (process_orders_on_close semantics — this matches how Jack actually trades).
- Reversals (long straight to short) are allowed and intentional.

ROUTING — DECIDED, ON THE BOOKS. Which plan each state gets:

- trending        -> two-leg trend plan. The ONLY state that splits risk.
- ranging         -> one-trade plan.
- trend-in-range  -> one-trade plan.
- neither         -> STAND ASIDE.
- crisis (panel)  -> one trade at most, whatever the pair's own state says.

Trend-in-range is NOT a stand-aside label. It takes the one-trade plan, same
as ranging. Only "neither" is untraded.

## THE NNFX BUILDER (the machine being ported)

Five slots, interchangeable parts: C1 main confirmation (36 options — its flip
can trigger entries, its direction votes), C2 second confirmation (36 — votes
only), volume/volatility filter (12 — is the market moving enough), baseline
moving average (14 — direction gate + cross trigger), exit indicator (36 —
closes both legs). Three entry routes: baseline cross, C1 flip, continuation
re-entry. Two blocks: price >1.5x ATR past baseline = too late; >7 bars since
cross = too stale (Bridge Too Far).

Known Pine bugs, fixed in the Python build from day one: continuation entries
skipped Bridge Too Far; leg-phase state failed to reset on reversals; three
volume filters (Chaikin Osc, Chaikin Vol, Elders Force) passed every bar and
filtered nothing; J_TPO summed the wrong variable; Schaff Trend Cycle confirmed
both directions between its bands; Ehlers Reverse EMA was a mislabelled
dual-EMA cross; Glitch Index had a dead parameter. Eleven indicators are being
added: ADX/DMI, Parabolic SAR, Donchian, Ichimoku, LinReg slope (confirmation);
Choppiness, Efficiency Ratio, VHF, Fractal Dimension (volume); SMA, LSMA
(baselines). A V9 Pine patch file specifies all of this — ask Jack for it.

## THE PLAN AFTER THE ENGINE EXISTS (context, not this work order)

A two-stage funnel over all slot combinations (~17.6M with additions, default
parameters only, frozen):
- Stage 1 loose screen, 1999–2015 data ONLY: expectancy above a scrambled-
  control floor, >=100 trades, positive on multiple pairs, family survives
  (a winner whose ~200 nearest cousins died is luck — killed).
- Stage 2 real test, ONE look at 2016–2026: expectancy holds (same sign, >=half
  size), sub-period split (2016–19 / 2020–21 / 2022–26 all positive), deflated
  Sharpe, max drawdown, real per-pair costs, and regime dependence (must do
  better inside its assigned regime than outside, or the estimator earns
  nothing).
KPIs ranked: Sortino, expectancy in R, Calmar, profit factor primary; deflated
Sharpe the stage-2 judge; Sharpe reported for comparability; win rate is
diagnostic only (the runner loses often and wins big by design).
Expectation: an earlier placeholder sweep went 0 for 1,680 through deflated
Sharpe. Zero survivors is a legitimate result.

## DATA FACTS

- Layer 1's panel (px28.csv, Fed H.10) is CLOSE-ONLY — no OHLC, no ATR, no
  volume. It stays that way; it is Layer 1's file.
- Layer 2 gets its own daily OHLC (Yahoo — extdata.py has plumbing). Winners
  must port back to Pine/TradingView, so they must be found on real OHLC.
- H.10 quoting: uniformly foreign-per-USD including EUR/GBP/AUD/NZD — invert
  all with 1/x then triangulate. Sanity: EURUSD peak 1.6010, USDCHF low 0.7296.
- IS = 1999–2015, OOS = 2016–2026 (Yahoo history may start ~2003 — report what
  exists).
- FX daily close = 5pm New York, thin liquidity — cost model widens spreads
  there later.

## LAYER 1 FACTS THAT CONSTRAIN STRATEGY DESIGN

- NO REGIME AXIS IS A PROVEN EDGE. From results/final_report.csv: trend
  separation halves out of sample (in-sample 0.1056 -> holdout 0.0534) against
  a surrogate of 0.0975, corrected -0.0442. Chop holds its level (0.1506 ->
  0.1563) but its surrogate is 0.1674, corrected -0.0111. Ranging is the LEAST
  DEGRADED axis, not one shown to beat its own null. Layer 2 therefore assumes
  no regime read is a proven edge. The stage-2 regime-dependence gate is the
  test of whether the estimator earns anything — it is not assumed in advance,
  and a strategy that works equally well inside and outside its assigned
  regime tells us the estimator earned nothing.
- Entries lag state starts by ~6 bars (5-day confirmation dwell + 1-bar lag).
- ROUTING LABEL IS shape2, WITH activity AS A MODIFIER — not combined2. Mean
  gap between label changes (results/layer1_summary.csv): shape only 19.8
  bars, activity only 24.0, combined 15.2. After ~6 bars of entry lag that is
  ~14 bars of expected state life on shape2 against ~9 on combined2. Routing
  on the combined label spends a third of the remaining state on the lag.
- STAND-ASIDE MATH: neither is 19.2% of bars, trend-in-range 19.0%. Only
  "neither" stands aside, so ~19% of bars go untraded, not 38%. (The "20%" in
  earlier drafts was the "neither" share alone and was wrongly read as
  covering both labels.) Full shares: ranging 33.4%, trending 28.4%, neither
  19.2%, trend-in-range 19.0%.
- Trendy pairs have MORE trends, not longer ones (ranking 79% stable across
  eras) → more attempts, never longer holds.
- Down-moves are straighter than up-moves (21 of 28 pairs).
- ~13 effective independent bets per day across 28 pairs; JPY block clusters.
- State age carries no hazard information.

## BINDING METHODOLOGY RULES (proven in Layer 1 at 175,634-signal scale)

1. Nothing runs to /tmp — results to results/, committed.
2. Nothing deleted or overwritten — superseded files get header notes.
3. Quote numbers from files, not memory.
4. Everything lagged one bar. No exceptions.
5. Episode-based significance, never per-bar.
6. Null-test anything strong; sub-period split before believing any holdout.
7. Declared constructions and declared criteria BEFORE looking; one holdout
   look, no second pick.
8. Searching manufactures effect size — 78% of Layer 1's best headline number
   was selection artifact. The funnel's controls (scrambled floor, family
   cuts, one OOS look) exist because of this.
9. Long jobs are resumable (per-pair checkpoints); a killed run costs one
   pair, not everything.
10. If a job fails, say so immediately and fix it. Never quietly shrink the
    work.

## HOW TO WORK WITH JACK

Plain English, short. Percentages not decimals. No jargon without an inline
definition. Say what you think; push back when the spec is wrong — your
objections have repeatedly been right. Never tell him to stop working on
something. Pick something sensible, tell him what you picked, keep going.
