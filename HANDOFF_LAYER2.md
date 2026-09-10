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

## LAYER 2 TRAPS ALREADY HIT (do not rediscover these)

- **A RESUME CHECKPOINT MUST BE KEYED ON THE WORK, NOT THE UNIT OF WORK.**
  `l2engine.run_all_pairs` first keyed its per-pair checkpoint on the pair name
  alone. Running a DIFFERENT slot combination then found a file for every pair,
  skipped all of them, and reported the PREVIOUS combination's results in
  0.01 seconds with no error and no warning. It was caught only because an
  SSL/DSPO/Variance/TMA run printed numbers identical to a PSAR run. At sweep
  scale that is a wrong answer wearing the costume of a fast one. The checkpoint
  now carries a `combo` column built from every slot AND every risk parameter,
  and refuses a file whose signature differs. **Any resumable job added later
  must do the same** -- rule 9 says jobs are resumable, and this is the failure
  mode resumability introduces.

- **Yahoo stamps the last FX bar of the week on Sunday during US daylight
  saving.** 19,662 bars carry a date two days late. `data/ohlc_clean/` fixes it;
  never read `data/ohlc/` directly. See `code/l2clean.py`.

- **The engine's semantics come from `JCs_NNFX_ALGO_V5_1.pine`, not from prose.**
  Four mechanics were wrong when built from a description and right only after
  reading the source: continuation needs the C1 TRIGGER not its confirmation;
  the trail activates on the bar's HIGH/LOW not its close; the trail tracker is
  seeded at activation not at entry; and the trail distance uses the CURRENT ATR
  while stop and target use the ATR AT ENTRY.

- **The shipped V5.1 does not set `process_orders_on_close=true`.** Close-fill is
  the true spec (Jack enters at the close of the signal bar); the file predates
  that fix and it is added on the TradingView side before exporting.

- **Six indicators need a volume series that spot FX does not have** -- Chaikin
  Oscillator, Elders Force Index, Normalized Volume, Volume Zone Oscillator,
  Chaikin Money Flow, Ease Of Movement. Tagged UNAVAILABLE on this data.

## PHASE 3 IS SETTLED — THE ENGINE MATCHES TRADINGVIEW ON IDENTICAL BARS

Full verdict: `results/l2_parity_verdict.md`, regenerated by
`python code/l2parity.py --oanda mid`.

**185 of 189 entries match on date and direction (97.9%); EURUSD is 61 of 61.**
Entry prices on matched trades agree to a median of 0.000000%.

The earlier Yahoo comparison read 18–25% and was worth nothing: the two sides
were on different prices. Running our engine on OANDA's own daily mid candles —
the feed the TradingView charts are drawn from — settles it. The bar sequence is
PROVEN identical rather than assumed: TradingView's export carries its own
`Duration (bars)` count and it matches on **406 of 406 trades**.

**The one real defect it found.** Pine ORs its three entry conditions
independently and they do not carry the same blocks (`longcondition3` has no
Bridge Too Far). The engine picked ONE route by precedence and then applied the
blocks to it, so a bar qualifying for both the C1 flip and the continuation lost
the trade when the bridge refused the flip. Each route now carries its own
blocks. Found at GBPUSD 2008-02-19; there was no other way to find it.

**The four residuals are accounted for, none of them logic.** Two are our
warm-up against a longer TradingView chart (bars 7 and 25 of our data, ATR still
NaN). Two are floating-point ties — DSPO at 4.2e-06 on the bar, and an SSL latch
decided by a close sitting 2.0e-04 below its own moving average.

**Two data facts that bind future work.**
- OANDA's PRACTICE feed serves close-only PLACEHOLDER bars for 2002–2004
  (high = low = close, volume = 1; 672 of 6,286 on EURUSD). `sma(high)` then
  equals `sma(low)` and SSL confirms nothing, so the engine trades nothing there
  while TradingView trades normally. `l2parity.load_oanda` drops the leading
  block; comparisons start 2005-01-03.
- TradingView plots OANDA MID, not bid. Mid matched to 0.00000%, bid to 0.010–
  0.013%. And OANDA emits near-empty candles either side of the weekend that map
  to Saturday and Sunday and that TradingView does not plot; left in, they put a
  sixth and seventh bar in some weeks.

The API token lives in `.oanda_token`, gitignored, and is never printed. Nothing
in the repo contains it.

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

---

# STATE AT 2026-09-10

## Where the pipeline is

**Gate 3 fine-tune: COMPLETE.** All 5,135 gate-2 crossers re-tuned on widened
grids under full costs, gap-aware fills and stop-first resolution.
`results/gate3ft_costed_v4/` (untracked while it ran; re-add when convenient).

**Adoption: ~12.5% on the W3-only basis.** That number is the single most
consequential correction in the run. It was 0.18% until the incumbent stopped
being scored on a window its own parameters had been tuned on — see W2
CONTAMINATION below.

**Team: `W3ONLY_ADOPTED`, 25 members.** Team 1 (3.6/3.6) median year 22.97%,
worst 11.44%, max DD 2.69%. Team 2 (5.4/3.6) median 34.45%, worst 17.17%.
Built from an EMPTY start — no graft seed — on the clean cut of 252 passers,
with 494 strategies carrying the fine-tune's adopted settings.

**Mode C: PAUSED BY DECISION at 299 chunks.** Not a fault. It stays paused until
the full system is built and forward testing has started. Restart it
deliberately; it is no longer in any chain.

## Layer 4 sizing v2 — the current answer

Net the votes per pair per day, size by the agreement curve, cap per currency,
then scale to the budget. **Book C wins on every metric.**

| | A stacked | B linear | **C curve 1/3/6** | D half |
|---|---|---|---|---|
| median year | 22.27% | 27.69% | **30.22%** | 26.18% |
| worst year | 12.15% | 17.42% | **18.67%** | 16.81% |
| max DD | 2.36% | 2.51% | **2.29%** | 2.48% |
| Sortino | 8.36 | 9.87 | **10.26** | 9.53 |
| Calmar | 40.93 | 49.70 | **60.60** | 48.07 |
| max positions | 33 | 15 | **15** | 15 |

**The 2% per-currency cap is KEPT.** Largest exposure ever reached is 2.62%, so
3% and 4% never bind and are identical to uncapped; 2% binds on 9 days of 1,304
and costs 0.03pp of median year. It is a genuine backstop, not a constraint.

**v1 vs v2 — read v2.** v1 spread each trade's R across its holding days, which
smooths the series, shrinks DIP95 and inflates the scale: it reported 55.56%
where v2 reports 30.22%. v2 marks to market daily exactly as the team builder
does, and book A reproduces the builder's figure (22.27% against 22.97%), which
is the check that the path is right. v1's RANKING was correct; its levels were
not comparable to anything.

## Agreement study — verdicts

**Agreement is worth extra size, from level 2, strongest at 3.** Return per unit
rises monotonically: level 1 → 0.031 (IS) / 0.028 (OOS), level 2 → 0.079/0.065,
level 3 → 0.193/0.124. Slope 1.9095 IS and 0.6238 OOS, both at the **100th
percentile of a 1,000-shuffle membership null**, p=0.0000.

**Do not size on level 4+** — 23 IS episodes, and the IS figure is 4.7x its OOS
value. The curve stops at 3 for this reason.

**Opposition: follow the majority at net size.** +0.028 R/unit, 54.9% hit,
worst dip 9.2 R — against taking both sides (-0.034, 31.6%, dip 54.4 R) and
sitting out (zero). Following the majority pays best when the majority is clear
(3v1: +0.123) and reverses at 2v2 (-0.122), but 2v2 is 5 episodes. 1v1 and 2v1
are 537 of 567 episodes and both favour the majority.

**Nobody is reliably right when opposed.** One member of 25 clears 50% in both
periods (`coral x lemantrend x williams_vix_fix x rma`, 67% IS / 60% OOS), which
is about what chance gives. IS→OOS correlation of opposition accuracy is 0.376.
Do not weight on it.

**Two members earn only with company** — `kuskus_starlight x coral x variance x
mcginley` and `volatility_quality x aroon x waddah_attar_explosion x
fantail_vma`. Both are flat alone rather than loss-making. They count as ZERO
when alone in Layer 4 sizing. **Zero members earn alone and lose in company.**

## Still running / queued

- **Selection holdout + random-team null** on the adopted team, all 9 cores.
- **Re-run queue** (`code/l2rerun.sh`): entry timing, calendar, crisis split,
  suppressed-vol, tripwire, agreement — everything the mode bug touched. Waits
  for the chain, runs one at a time on one core.
- **Cloud ip1 package** (`code/cloud_ip1.sh`): the B-trend ip1 recovery, ~97
  core-hours. One command, one credential (GH_TOKEN). Hetzner CCX63 ~2 h / ~$3,
  AWS c7i.16xlarge ~3 h / ~$9. NOT launched.
