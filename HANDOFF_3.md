# FX REGIME ESTIMATOR — FULL PROJECT HANDOFF
Written 2026-08-04. Everything below came out of one long working session.

---

## 1. WHAT THIS IS

A regime estimator for FX. It classifies a currency pair as **TREND**, **CHOP**, or
**CRISIS**. It is the ROOT NODE of Jack's decision tree — strategy sleeves receive
capital based on what it says.

**The deliverable is the estimator, not PnL.** Do not drift into strategy testing
unless explicitly asked.

---

## 2. DATA

Source: Fed H.10 daily FX
`https://raw.githubusercontent.com/datasets/exchange-rates/main/data/daily.csv`

**CRITICAL QUOTING CONVENTION:** the dataset is UNIFORMLY foreign-per-USD, *including
EUR, GBP, AUD, NZD*. Invert ALL with 1/x, then triangulate. An earlier attempt assumed
EUR/GBP/AUD/NZD were already inverted and produced garbage.

28 pairs from the G8 — EUR GBP AUD NZD USD CAD CHF JPY, in that base-priority order.
~6,916 rows, 1999-01-04 → present.

**Sanity checks that must pass after any rebuild:** EURUSD peak 1.601, USDCHF low 0.7296.

Close-only — no OHLC, so no true range or ATR. No carry data: 2y OIS differentials,
CFTC COT positioning, VIX and MOVE are all blocked by sandbox networking. Jack said
"do carry later"; do not guess it from price.

---

## 3. METHOD

Signals are scored on **regime identification, not profit**.

**TREND target:** forward 20-day efficiency ratio = |net move over next 20d| ÷ sum of
|daily moves| over those 20d. 1.0 = straight line, ~0 = noise. Pooled baseline **0.2226**.

**CHOP target:** forward 20-day turn frequency — share of days reversing direction.
Added in v5. Before that, "chop" was just trend with a minus sign, which made the
results table unreadable.

**CRISIS target:** defined but never scored. See §8.

Each signal is split into quintiles; the target is measured in each. Top-minus-bottom
spread is the effect. **Every signal is lagged one bar via .shift(1). Non-negotiable.**

Split: **IS 1999-2015, OOS 2016-2026.** Cut points, mappings and thresholds are learned
on IS only and applied unchanged to OOS.

---

## 4. THE GAUNTLET

Sequential elimination gates, **not** a weighted composite — a composite lets a signal
offset a fatal flaw with an unrelated strength.

| # | Gate | Threshold | What it kills |
|---|---|---|---|
| 1 | Sign holds OOS | must match | ~32% of everything |
| 2 | \|t\| OOS | ≥ 8.0 | statistically weak |
| 3 | Effect size (Q5−Q1) | ≥ 0.020 | real but too small |
| 4 | Pairs agree OOS | ≥ 0.85 | one-pair flukes |
| 5 | Monotonic | ≥ 0.95 | tail-only effects |
| 6 | Decay ratio (t_oos / t_is) | ≥ 0.60 | signals bleeding out |
| 7 | Time stability | sign holds in ≥ 4 of 6 blocks | works only in one era |
| 8 | Decorrelation | \|r\| < 0.70 vs already-kept | the same idea counted twice |

Gate 7 went live with v6. NEXT_BATCH.md is explicit that gate 6 stays a **floor only —
no ceiling** — so a signal stronger OOS than IS passes gate 6 and is caught, if at all,
by gate 7. In practice gate 7 kills nothing that reaches it (§15).

Jack's instruction: **nothing in the gauntlet may be decoration.** An earlier draft had
monotonicity at 0.80, which almost everything passed. That was called out and tightened.

**Never computed, still owed:** window robustness against neighbouring lookbacks,
turnover, detection lag, coverage.

**DATA RETENTION — non-negotiable.** Gates *mark*, they never filter. Every signal's
full record stays in the `.npz` files and in `signals.json` whether it passes or not,
including records that could not be scored at all (`ok:false`). Failures are results:
interactions at 49% retention and deltas at 42% are findings that exist only because
the losers were kept. `prep.py` used to drop 4,053 unscorable rows — it no longer does.

---

## 5. SIGNALS TESTED — 123,501 TOTAL

> **v6 added 2026-08-04.** The duration batch (`sig6.py`/`sc6.py`) added 103,226 scored
> signals, taking the total from 20,275 to 123,501. Gate 7, time stability, is now live.
> Survivors went 13 → 101, but **101 is not 101 discoveries**: gate 8, greedy
> decorrelation at |r| < 0.70, collapses them to **28 independent signals**. Quote 28.
> The table below is the pre-v6 history; §15 covers v6.

| Batch | Count | Character | Module |
|---|---|---|---|
| v2 | 1,066 | own-price | `sig2.py` |
| v3 | 964 | cross-sectional / panel | `sig3.py` |
| v4 | 10,383 | multi-timeframe, term structure, interactions | `sig4.py` |
| v5 | 7,862 | jump, contagion, entropy, vol clustering, order stats | `sig5.py` |

Every batch was cross-referenced against previously tested names before building.
**Almost zero duplicated work** — `prep.py` now reports collisions instead of silently
deduping them, which surfaced 16 real ones between sig2 and sig3 (`maxdd_*`,
`z_maxdd_*`). v6's overlap against all 20,275 is genuinely zero.

### Survivors at strict gates

Ten from the first 12,413 — **all chop detectors, all panel-volatility family**:

| Signal | t IS | t OOS | Effect | Agree | Decay |
|---|---|---|---|---|---|
| z_panelvol_40 | −15.7 | **−25.6** | 0.0257 | 96% | 1.63 |
| z_paneldisp_40 | −14.3 | −24.9 | 0.0233 | 89% | 1.75 |
| z_panelvol_60 | −17.3 | −21.9 | 0.0281 | 93% | 1.27 |
| z_bbw_120 | −13.7 | −11.4 | 0.0228 | 86% | 0.83 |

`z_panelvol_30` hit **100% pair agreement out-of-sample** — the only signal in 20,275
to do so. Decay above 1.0 means *stronger* on fresh data than on the fitting period.

Three from v5:

| Signal | t IS | t OOS | Effect | Agree | Direction |
|---|---|---|---|---|---|
| zz_coex3_D120 | −13.6 | −13.9 | 0.022 | 89% | chop |
| zz_coex2_D150 | −12.6 | −12.8 | 0.021 | 86% | chop |
| **zz_tsexceed_D375** | **+12.4** | **+12.7** | **0.021** | 86% | **TREND** |

`zz_tsexceed_D375` is the **first trend signal in 20,275 to pass every gate.** It
measures time since the last 2-sigma move — the longer since a shock, the straighter
price travels afterward.

`coex` counts how many of the 28 pairs breach 2σ or 3σ on the same day (contagion
breadth).

---

## 6. FINDINGS THAT SHOULD SHAPE ALL FUTURE WORK

**Cross-sectional beats own-price, decisively.** Panel features retained OOS sign 68%
vs 54%; of FDR survivors, 75% vs 60%. Panel volatility and dispersion dominate
everything else. Same method, same target, same 28 pairs — the only difference is what
the signals are made of.

**Interactions are worthless.** 7,140 tested (products of z-scored signal pairs).
**49.1% OOS sign retention — worse than a coin flip.** Best reached only t=13.5.
Multiplying two good signals destroys information. Do not build more.

**Deltas are worthless.** 42% retention. Measuring the *change* in a signal rather than
its level actively destroys information. Levels held 65%, z-scores 56%.

**Higher timeframes fail as FEATURES but work as CONFIRMATION.** Monthly-sourced signals
retained 47.8% — below random. Weekly 51.8%, daily 56.1%. Yet M/W/D *alignment* is the
single best filter found (§9). Different jobs entirely.

**Trend dies at effect size.** 171 trend signals clear the t-stat gate; only 10 clear
effect size. Trend is real but small. Chop is detectable because volatility spikes
panel-wide simultaneously — that's what produces 96% agreement. Trending is idiosyncratic
per pair, so trend signals will always show weaker cross-pair agreement. **An 85%
agreement bar may be the wrong bar for the trend side.**

**Complexity does not pay.** A 200-day SMA beat a fitted 2-state Gaussian HMM on both
real logics (gate −0.002 vs −0.092; switch −0.184 vs −0.249). The HMM only "won" on
`switch_backwards`, the deliberately inverted control — meaning its mapping is wrong
often enough that inverting it does less damage.

**Multiple testing is brutal.** At this scale ~1,000 signals clear |t|>2 by chance
alone. Across all signals, OOS sign retention is ~53% — indistinguishable from a coin
flip. Even among FDR survivors it's 54%. **Out-of-sample confirmation is the only gate
that matters.**

---

## 7. STRATEGY LAYER (side quest — not the estimator)

38-config sweep, 28 pairs, costs on (majors 1.5bp, crosses 3.0bp round trip):

| family | mean OOS Sharpe | median | pct positive | mean trades |
|---|---|---|---|---|
| mean_reversion | **+0.109** | +0.108 | 69% | 176 |
| momentum | **−0.225** | −0.248 | 22% | 47 |

Best single config: mean reversion, n=60, entry 2.0 — mean OOS Sharpe 0.197, 82% of
pairs positive.

**Detector ladder** (dumbest to fanciest, each must beat the row above): trend_sma200,
vol_regime, markov_naive (strawman), hmm_2state. Applied as filters to the baseline,
**not one cell beat the baseline on Ret/DD or Ret/Exposure.**

**Three logics** — gate, switch, and switch_backwards (the control). Across 140 paired
draws per detector: **switch improved in 0 of 4 detectors, gate in 0 of 4.**

**DSR (deflated Sharpe, Bailey & López de Prado):** 1,680 variants → 446 positive →
**0 survive at 0.95.** Expected max Sharpe under the null given that many attempts is
1.076; best observed is 1.164. Jack's own independent equities study got 0 of 2,400.
That replicates across asset classes.

**Look-ahead audit: 20/20 spot-checks passed.** Every detector label recomputed from
truncated data matched the label from the full series. Causality proven, not claimed.

**Regime durations:** vol_regime 39.4d mean, trend_sma200 26.0d, hmm_2state 24.6d,
markov_naive 2.1d (flagged — flips faster than weekly, as designed).

---

## 8. CRISIS — VALIDATED AGAINST REAL EVENTS

`events.py` holds **48 dated events, 2000–2026**. **Every date came from news** — policy
decisions, interventions, bankruptcies, referendums, invasions. **No date was chosen by
looking at price.** That is what makes the validation non-circular. This file exists in
the chat sandbox but was **never added to the repo — recreate it.**

Detector performance, forward-only window (0 to +15 days):

| Detector | Caught | Recall | Base rate | Lift | Lag |
|---|---|---|---|---|---|
| **maxabsmove** | 38/48 | 79% | 5% | **17.5×** | 0 days |
| breadth2sig | 35/48 | 73% | 4% | 16.4× | 0 days |
| paneldisp | 30/48 | 62% | 5% | 12.5× | 0 days |
| legdiv20 | 27/48 | 56% | 5% | 11.3× | +1 day |
| avgcorr60 | 10/48 | 21% | 5% | 5.0× | 0 days |

**These are the only real accuracy numbers in the project** — everything else is scored
against a self-referential price target.

**No detector leads. All fire on the day.** An earlier claim that `avgcorr60` fired 2.5
days early was an artifact of a window starting 5 days *before* the event; forward-only
testing removed it. Worth remembering as a methodology trap.

### The Japanese carry unwind — the canonical case

July–August 2024, peak to trough over 26 days: AUDJPY −14.4%, NZDJPY −13.6%,
CADJPY −12.4%, GBPJPY −11.5%, USDJPY −11.0%, EURJPY −9.9%, CHFJPY −6.2%.

**The magnitude ordering follows the carry ranking exactly** — high-yielders fell
hardest, the other funding currency (CHF) least. Not random panic; a specific trade
unwinding.

It is *not* a single-day shock. Aug 7 hit only 15 of 28 pairs beyond 2σ, ranking below
2008 (25/28), April 2025 (20/28), Brexit and COVID (19/28).

**Currency-leg divergence** (max minus min 20-day currency-index move, in sigma) ranks it
8.8σ — 5th of 27 years, 96th percentile — and **first breached its 95th-percentile
threshold on 2024-07-26, ten days before the Aug 5 trough.** Bloc correlation among JPY
crosses went 0.73 → 0.88.

Top episodes by leg divergence, all real named crises: COVID (11.0σ), **2007 carry
unwind (9.3σ)**, **2008 GFC carry unwind (9.2σ)**, SNB peg break (8.9σ), **2024 carry
unwind (8.8σ)**. Note 2007, 2008 and 2024 share an identical fingerprint: **JPY
strongest, AUD weakest.** Same trade unwinding three times in seventeen years.

### Crisis needs TWO modes

The yen has fallen **every year 2021–2026**: −7.5, −8.0, −10.8, −4.3, −6.5, −3.7 (~35%
cumulative). Every JPY cross is now *above* its pre-unwind July 2024 peak. Yet leg
divergence currently reads 2.9σ — 59th percentile, zero threshold breaches in twelve
months.

The spike-based definition catches Aug 2024 and **completely misses the six-year
debasement that caused it.**

| | Chronic | Acute |
|---|---|---|
| What | sustained one-way debasement | violent snap-back |
| Speed | years | days |
| Measure | currency index vs 3–5yr range | leg divergence spike, 20d sigma |

**Hard truth:** the acute trigger is policy, not price. Jack's own USDJPY Markov work
found P(stress) was 0.03 the day before the July 2024 intervention and 0.92 the day
after. Price can show *vulnerability building* — crowded positioning, stretched
extension, compressed vol — but not the trigger.

As of 2026-07-31 the US joined Japan in coordinated intervention; USD/JPY reversed from
~164 to 156.5. BOJ at 1%, Fed at 3.50–3.75%. CFTC net yen shorts ~$11.3bn, near a
two-year high and comparable to July 2024. **The same setup that produced Aug 2024 just
fired again.**

---

## 9. MULTI-TIMEFRAME CONFLUENCE — THE ONE FILTER THAT WORKS

Daily / weekly / monthly regimes on a real hierarchy: **60 days, 26 weeks, 12 months.**
Strategies trade daily; M and W exist only to confirm or contradict.

**Causality:** a weekly label isn't usable until the following Monday, a monthly label
until the next month opens. Both are shifted **on their own clock** before being
reindexed onto daily bars. Getting this wrong manufactures a huge fake edge.

Agreement vs 33% chance: D–W 46.7%, W–M 47.7%, **D–M only 36.9%.** Daily and monthly
read near-independent things — which is exactly what makes confluence informative.

| Cell | Data % | Sharpe | PF | $AvgTrade |
|---|---|---|---|---|
| aligned trending | 18.5% | **0.302** | 1.064 | $236 |
| 2 of 3 | 37.5% | 0.298 | 1.069 | $174 |
| all 3 aligned | 23.0% | 0.269 | 1.061 | $183 |
| aligned flat | 8.4% | 0.202 | 1.059 | $56 |
| **daily alone** | 39.5% | **0.007** | 1.002 | **$4** |
| BASELINE | 100% | 0.181 | 1.042 | $176 |

**When the daily read has no higher-timeframe support, the sleeve returns nothing** —
Sharpe 0.007, four dollars a trade, across 39.5% of all bars. Profit factor improves in
every confluence cell and degrades only in "daily alone."

---

## 10. THE 9-BOX (Jack's taxonomy — keep 9, do NOT collapse to 6)

Direction (down / flat / up) × volatility (low / med / high). Terciles of the 60-day
slope t-stat and the 60-day vol percentile, learned IS only, both lagged.

Mean-reversion Sharpe by box:

| | Down | Flat | Up |
|---|---|---|---|
| **High vol** | +0.26 | −0.11 | +0.28 |
| **Med vol** | +0.36 | +0.05 | +0.07 |
| **Low vol** | **+0.47** | **−0.23** | +0.25 |

**Mean reversion works when price is MOVING and fails when it's flat.** Counterintuitive
but consistent with the compression finding. Every flat box is bad; down beats up at
every volatility level.

Momentum loses in all 9 boxes. It "wins" the two flat boxes only by losing less — so the
honest routing rule is **mean reversion in the seven trending boxes, cash in the two flat
ones.** There is no box where momentum deserves capital.

Caveat: every box degrades Ret/Exposure 77–115% vs baseline purely because each covers
~10% of bars. **The untested experiment is routing capital across all seven positive
boxes simultaneously and comparing that to the full-time baseline.**

Versus the external 6-regime framework Jack supplied: same two axes, ours is a superset.
Theirs uses fixed thresholds (200-day MA, VIX>25); ours uses terciles, so every box
always holds ~11% of days and the estimator can never say "we're nowhere near a
bear-volatile market." Theirs also specifies position sizing and stop rules per regime —
we size everything flat. That gap is real and unaddressed.

---

## 11. INFRASTRUCTURE

Repo: **https://github.com/Jackscuster/fx-data**

```
code/build.py       fetch + build px28.csv, runs sanity checks
code/sig2..sig5.py  the four signal libraries
code/sc2..sc5.py    scorers — one .npz per pair, resumable, skip completed pairs
code/rank2.py       per-batch ranking with BH-FDR
code/rank3.py
code/sig6.py        v6 duration library, EVENT x CONDITION x READOUT
code/sc6.py         v6 scorer, two targets + block spreads, resumable per block
code/prep.py        pools ALL score dirs -> results/signals.json
code/stability.py   gate 7 backfill for v2-v5
code/dedup.py       correlation dedup -> how many survivors are actually distinct
code/strat.py       38-config strategy sweep
code/framework.py   look-ahead audit, durations, 3 logics, DSR
code/ninebox.py     3x3 direction x volatility
code/mtf.py         monthly/weekly/daily confluence
code/extdata.py     Yahoo daily closes + FRED 2y yields -> data/ext.csv. Aligned to
                    the px28 calendar, ffill only. FRED is unreachable from the dev
                    sandbox; the fetcher records what resolved in ext_coverage.csv
code/extsig.py      runs the SURVIVING constructions over ext.csv and scores them
                    against the same FX targets. Uses sc3.quint itself, and
                    --verify checks it reproduces published FX statistics first.
                    FX_RUN_EXTERNAL gates the ~25 min rebuild; --report-only
                    regenerates the tables from the committed ext_signals.csv
code/inflation.py   selection-inflation null: 50 circular target shifts, gauntlet
                    rerun against each. Sweep is FX_RUN_INFLATION-gated (hours cold,
                    2.2 GB of gitignored scratch); the pipeline normally runs only
                    `--adjust-only`, which rebuilds the correction from the committed
                    results/inflation_runs.csv
code/bundle.py      signals.json + csvs -> app_data.json
code/pipeline.py    runs everything in order
app_ui.js           THE ENTIRE APP INTERFACE — add new tabs here
app_data.json       the feed the app reads
.github/workflows/update.yml   weekdays 06:00 UTC, + on any push to code/**
```

**The app is a thin shell HTML on Jack's machine** that fetches BOTH `app_data.json` and
`app_ui.js` from the repo. New tabs go in `app_ui.js` — **he never redownloads the app.**

**Gotcha:** GitHub serves `.js` as `text/plain` with `nosniff`, so a `<script src>` tag
is blocked by the browser. The shell fetches `app_ui.js` as text and evals it. Don't
"fix" this back to a script tag.

**Rebuilds are ~3 minutes, not 45.** All scoring is committed under `results/scores*/`
and every scorer skips pairs that already have a `.npz`. Only genuinely new batches cost
compute, once.

### Bugs already hit — don't repeat them

- `bundle.py` once read and wrote the same file (`signals.json`), nesting the signals
  section inside itself. It must READ `signals.json` and WRITE `app_data.json`.
- `os.path.join(ROOT, '')` returns a trailing separator; concatenating paths without it
  silently writes to `resultsapp_data.json`.
- `sc5.py` writes two-target arrays named `qti/qto/qci/qco`; older scorers write `qi/qo`.
  `prep.py` now probes `z.files` and falls back. **Any new multi-target scorer must
  either match the old naming or update prep.**
- The `.github` folder does not upload through GitHub's web uploader (hidden folders are
  skipped). This silently meant nothing was automated for hours.
- Double-escaping in generated JS produced literal `\u2026` in rendered output.

---

## 12. WHAT'S NOT DONE

**Four gauntlet gates never computed:** time stability across 6 blocks, window
robustness, correlation to incumbents, turnover.

**Four regime-validation tests never built** — these are what would prove the estimator
actually works:

1. **Beats shuffled labels** — the most important. Shuffle regime labels while keeping
   run lengths, then rescore. If real labels don't clearly beat shuffled ones, the
   estimator is detecting nothing; it's just chopping the sample into persistent blocks,
   and any persistent blocking would score similarly. Nothing else catches that.
2. **Synthetic ground truth** — simulate price with known regimes (200 days trending,
   150 choppy). The only place a real accuracy number can exist. The old HMM was tested
   this way (73% accuracy on strong drift, 12 days late); the 9-box never has been.
3. **Label stability on refit** — fit through 2015, label history; refit through 2020,
   label again. If 2010's labels changed, the estimator is using information it wouldn't
   have had. Old HMM scored 93–99%; the 9-box is unmeasured.
4. **9-box persistence + transition matrix** — a real regime structure has a strong
   diagonal. If boxes flip every two days it's noise regardless of everything else.

**Also outstanding:**
- `ladder.py` and `funnel.py` were written but never added to the repo — the Detectors
  tab and part of Verdict are empty because of this.
- `events.py` (48-event crisis calendar) — same, never committed.
- Crisis never scored as a third target. Signals exist for it.
- Combined 9-box allocation test (route across all seven positive boxes at once).
- **Vol-targeted position sizing.** Everything trades flat ±1 unit, so a 4% ATR yen
  cross and a 0.5% EURCHF carry identical size. Realised risk is wildly uneven across
  the 28 pairs and high-vol pairs dominate aggregate PnL and drawdown. This is the
  obvious untouched lever for improving return and drawdown together. It may also
  change the ladder result — some of what the vol filter appears to add may just be
  crude vol control that proper sizing already handles.
- News / language detection — reading headlines for hawkish vs dovish tone. Parked
  explicitly, but it's the natural completion of the crisis work, since the acute
  trigger is policy rather than price.

---

## 13. HOW JACK WORKS

- **He owns the architecture.** Do not propose structural redesigns.
- **Never silently reduce scope.** If a job fails, say so and fix it.
- **Don't drift to PnL** when asked for regime detection.
- **Plain English. Short answers.** No jargon without explanation, no repeated caveats.
- **Never ask him to trade off return vs risk** — optimise both.
- **Don't stop to ask permission at every step.** Pick sensible defaults, state them,
  keep moving. But don't change what he explicitly asked for.
- When he pushes back: acknowledge, correct, adapt. Don't defend.
- **Every framework he supplies gets wired into all three places** — `app_ui.js`,
  `app_data.json`, and the pipeline. Never deliver results only in chat.
- **Strategy results use his standard table:** baseline vs regime-filtered columns, with
  Net Profit, Return/DD, Profit Factor, #Trades, Win%, $AvgTrade, Exposure,
  Return/Exposure; then a comparison block with Data % (share of bars the regime covers)
  and % improvement for Ret/Exp, Ret/DD, PF, Win%, $AvgTrade. **Report degradations too**
  — improvements are never uniform. Full spec in `STRATEGY_TEMPLATE.md`.

---

## 14. THE HONEST BOTTOM LINE

123,501 signals tested. 101 survive strict gates, but correlation dedup collapses those
to **28 independent signals** — quote 28. Of the 20,275 tested before v6, thirteen survive:
twelve chop detectors built on panel-wide volatility and dispersion, and one trend
detector built on time-since-shock. Of the 25 distinct new ones, eighteen are again
panel/cross-sectional and seven come from the duration family.

Total explanatory power of the entire library against forward efficiency: **1.4% of
variance.** The best single signal moves forward efficiency from 0.212 to 0.232 — about
9% of baseline.

The constraint has been the same from the beginning and hasn't moved: **information, not
model class.** Every signal here is a transform of daily closing prices predicting the
future shape of those same prices. The moment features stopped being one pair's own price
and became the panel's, both strength and durability improved. Carry, positioning,
options-market data and policy language remain untouched — and the crisis work makes
clear that the biggest single event in the dataset was triggered by something price could
not see.

---

## 15. THE v6 DURATION BATCH (added 2026-08-04)

107,040 signals generated, 103,226 scored after the coverage filter. **Overlap with the
previous 20,275: zero**, asserted at generation, not assumed.

Built as **EVENT × CONDITION × READOUT**: ~280 datable events (sigma exceedances, new
n-day highs and lows, MA crosses, direction flips, vol-median crosses, range breakouts,
drawdown openings), six states an event can be required to occur in (unconditional,
panel vol low/high, own vol low/high, coexceedance high), and readouts of time-since,
hazard ratio, occupancy, episode count and streak length. Chop stayed cross-sectional:
eigenvalue spectrum and eigen-gaps, dispersion term structure, a wider coexceedance grid,
breadth, vol rank churn, panel turn frequency.

### Results

| | |
|---|---|
| Signals | 123,501 total (103,226 new) |
| Survivors, gates 1–7 | **101** (13 pre-v6 + 88 new) |
| **Independent after gate 8** | **28 combined** (v6 alone 25, earlier alone 5) |
| v6 OOS sign retention | **63.6%** — above own-price 54.0% and multi-timeframe 52.5% |

### What actually survived

Of the 28 independent signals, **24 are v6 representatives and 4 come from the earlier
batches**. Two clusters span batches, which is the finding that matters: `z_panelvol_40`
absorbs five v6 survivors outright (`zb_ats_60_750`, `zc_cx3_m50`, `cx2_s40`,
`zb_dts_60_750`, `zb_cx3_m120`), and `ra_cx2.5_m120` absorbs `zz_coex2_D150`. **Several
v6 "discoveries" are rediscoveries of panel volatility.** Run the batches separately and
you get 25 + 5 = 30; run them together and you get 28.

By construction the panel/cross-sectional families (coexceedance, dispersion term
structure, breadth, rank churn) still dominate the representative list. The bet in
NEXT_BATCH.md was that duration would carry the trend side. It contributed — `ts_dd`,
`ts_sg`, `ep_fl`, `ep_mu`, `hz_sg` all lead clusters — but panel again dominates.

**Most representatives carry a condition suffix** (`_ch`, `_ph`, `_pl`, `_ol`). Conditioning the
event on panel or own-vol state is the single most productive idea in the batch — it is
what most distinguishes a survivor from its unconditional twin.

**Hazard ratios are a near-substitute for time-since, not a separate idea.** Under gate 8
they and `ts_*` land in the same cluster every time; which one represents it is decided by
whichever happens to be strongest, and that flips with the set. Decorrelating v6 alone,
no `hz_*` survives as a representative. Decorrelating the combined set, `hz500_sg1.5_v10_pl`
does — and it absorbs four `ts_*` signals. This is structural: hazard is
elapsed × count / H, which correlates near 1 with plain elapsed time. Build one or the
other, never both, and do not read the representative as evidence that hazard beat
time-since.

### Gate 7 — time stability

Six equal blocks, quintiles recomputed inside each, sign must hold in ≥ 4.

- **All 13 pre-v6 survivors hold 6 of 6**, including the two pre-2008 blocks. The specific
  worry — that panel-volatility signals ride the dispersion in COVID, 2020 and 2022 — is
  answered: they do not.
- Across all v6 signals the gate discriminates hard: **39% fail it**.
- But it killed **0 of 101** survivors, because gates 1–6 already select for stability.
  **Gate 7 is a strong standalone filter and a non-binding 7th sequential gate.** At ≥ 6
  of 6 it would kill 28 of 88.

### Gotchas this batch created

- `app_data.json` is **36.5 MB** raw. raw.githubusercontent serves it gzipped, so the
  transfer is **7.0 MB** — verified against the live URL. Fine, but no longer trivial.
- The decay scatter emitted one `<circle>` per signal. At 123,501 that is a multi-megabyte
  SVG that locks the browser. It now samples to ~12,000.
- The Families tab grouped on `s.rsplit('_',1)[0]`, which left **29,344 groups** on v6
  names. v6 now groups on the coarse readout × event family.
- `results/scores6/` is **438 MB** committed. Actions will never rescore it, but the repo
  is now ~500 MB.
- **16 names collide between sig2 and sig3** (`maxdd_*`, `z_maxdd_*`) and have been
  silently deduped since v3. §5's "zero duplicated work" was not exactly true. v6's own
  overlap is genuinely zero.

---

## 16. LAYER 1 FINISHED (2026-08-10)

This section is the final state of Layer 1 and, more importantly, the list of
things **not to rebuild**. Almost everything tried in this phase failed. The
failures are the valuable part — each one cost hours and each is recorded with
the number that killed it.

### 16.1 What Layer 1 is

A **backward-looking, nine-state classifier**. It describes what a pair has been
doing over the last 20 bars. It is not a prediction and has no forward target.

Two axes, both trailing over 20 bars and lagged one, each cut at that pair's own
**in-sample** terciles with a 0.25 hysteresis band:

- **straightness** = |net| / path
- **scale** = path / (60-day vol × √20)

```
                       strong          medium            weak
  trend (straight)     strong trend    medium trend      weak trend
  transitional         strong trans.   medium trans.     weak trans.
  chop                 strong chop     medium chop       weak chop
```

**The two words are two different axes.** `strong/medium/weak` is **SIZE** — how
far the pair moved in its own vol units, *not* confidence in the reading.
`trend/transitional/chop` is **CLEANLINESS** — how straight the travel was. So
"strong chop" is a pair thrashing a long way and "weak trend" is a pair drifting a
short way in a straight line.

Colour in the app follows the row: green trend, amber transitional, red chop,
darker for larger. It is an explicit cross of two tercile axes, **not** terciles of
a weighted score, so neither axis can crowd the other out. An earlier weighted
version (`classifier.py`, three states) put 97.3% of the variance on scale and was
effectively one-dimensional; it is kept for comparison and should not be treated
as the estimator.

Occupancy 9.3–13.5%. Median run 4 bars, diagonal 0.798. Refit stability **97.1%**.

**THE SECOND AXIS IS REAL AND RUNS BACKWARDS TO ITS OWN NAME.** At equal scale,
the *messy* side is followed by **more** efficient travel:

| size | chop − trend, forward path efficiency | null-corrected | p |
|---|---|---|---|
| medium | **+0.0218** | +0.0220 | **0.020** |
| strong | +0.0133 | +0.0137 | 0.078 |
| weak | +0.0053 | — | — |

Trailing straightness **mean-reverts**. So the trend/chop word describes the last
20 bars accurately and is the opposite of a forecast — reading "strong trend" as
"expect more of it" has the sign backwards. This is the same phenomenon as the
chop detectors' negative spreads, seen from the other side.

Separation across the nine: range-to-path **1.65 sd**, average absolute move 0.86,
realised vol 0.80, return autocorrelation 0.12. Against surrogates: sign-randomised
0.424, IID 0.052, both p=0.005 with 0/200 draws beating it.

`code/ninestate.py` builds it and writes `app_explorer.json`. The **Explorer** tab
is the primary screen; **States** has the grid, transition heatmap and per-pair
occupancy.

### 16.1b Which window colours the chart, and why 6 states was rejected

**Fragmentation is a display choice, but not in the way it looks.** Colouring the
price line by the fast window breaks long moves into confetti. Measured:

| window | median trend spell | longest | label changes / 1000 bars |
|---|---|---|---|
| 8 | 4 bars | 29 | 340 |
| 21 | 8 bars | 68 | 197 |
| **60** | **16 bars** | **176** | **93** |

So slow colouring is 4× longer spells and 3.7× fewer changes. Default is slow.

**But the amount of non-trend labelling does not change**: trend takes 29.0% of
bars at window 8, 29.6% at 21, 29.4% at 60. It *cannot* change — the cuts are that
pair's own terciles recomputed per window, so a third of bars land in each band by
construction. The window changes how labels are distributed in time, not how many
there are. 67.6% of bars the slow window calls trend are called non-trend by the
fast one, so the two are measuring different things, not noisy versions of each
other.

**A corollary worth internalising: a per-pair tercile cut can never show a
multi-year trend as sustained trend.** If a pair trends for two years that becomes
its normal, and the cut splits it across the bands. EURJPY reads 28.6 / 29.1 /
29.8% trend at the three windows — indistinguishable from the panel. If sustained
trends need to read as sustained, the cut has to be absolute, not relative.

**6-state was measured and rejected as the default.** Collapsing the transitional
row by which side of the straightness midpoint each bar leans:

- where the transitional bars actually sit: **28.9% dead centre**, 17.1% near the
  chop edge, 22.0% near the trend edge, and 32.0% outside the nominal band
  entirely (held there by hysteresis). Leaning trend 55.0% against chop 45.0% —
  close to a coin flip.
- separation degrades: the discriminating test, strong trend against strong chop,
  falls from **+0.0133 (t=1.89) to +0.0097 (t=1.70)** — and that is with the
  samples growing from 1113/963 to 1856/1353, so a larger n produced a *smaller*
  t. The absorbed bars dilute the effect, which is what genuinely ambiguous bars
  do.

So 9 stays the default and 6 is an optional view, both in the app.

### 16.2 The three-window ribbon

Ships at **8 / 21 / 60**. The lag-and-churn sweep in `ribbon.py` selected
**10 / 26 / 72**; both are computed, 8/21/60 is displayed by decision.

**Known issue with the 60-bar slow window.** 60 equals `VOLWIN`, so
`sum|r|_60 / (sd_60·√60)` collapses toward the constant √(2/π). The scale axis's
cross-sectional sd bottoms out exactly there — 0.343 at 60, against 0.393 at 63
and 0.550 at 72. The slow row moves less than the others partly because it has
less range to move in. If it ever looks suspiciously calm, that is why. Moving the
slow window off 60, or changing `VOLWIN`, fixes it.

Configuration occupancy: established 0.208, transition starting 0.165, confirming
0.327, unresolved 0.300 — stable IS to OOS. **But sign-randomised surrogates
reproduce that mix almost exactly** (0.198 / 0.166 / 0.331 / 0.306). Whether three
windows agree is not market structure.

### 16.2a THE LAYER 1 INTERFACE

`results/layer1_states.csv`, written by `code/export.py`, is what Layer 2 reads.
One row per pair per day: `state_7`, `state_28`, `state_128`, `tier`, `age_28`,
`straight_28`, `scale_28`, `sample`. 191,940 rows, 1999-04-01 to 2026-07-31.

It computes nothing new — every column is imported from `ninestate.py` — and it
asserts agreement with `nine_tiers.csv` and `app_explorer.json` on every pair-day,
halting the run on a mismatch. Wired into `pipeline.py` after `axischeck.py`.

**Windows ship at 7 / 28 / 128, base 28.** 60 cannot be the slow window: it equals
`VOLWIN`, so the scale axis collapses toward √(2/π) — sd 0.343 at 60 against 0.393
at 63 and 0.550 at 72, churn 92.7 against ~143 either side. It was the worst
single window in the 4–200 sweep. If a horizon argument pulls the slow window back
toward 60, use 63.

### 16.2b What separates, and what does not — settled by permutation

All figures out of sample, 11,167 entry events (26,833 across both samples), nine
states keyed on `state_28`, permutation = the label series rolled in time so run
lengths and entry clustering survive.

| keyed on | MFE spread | ratio spread | ratio p | MFE p |
|---|---|---|---|---|
| state_7 | 0.0028 | 0.2150 | 0.249 | 0.067 |
| **state_28** | 0.0023 | **0.2569** | **0.110** | 0.392 |
| state_128 | 0.0027 | 0.1994 | 0.524 | 0.521 |
| tier | 0.0010 | 0.1200 | 0.257 | 0.487 |

**Read this carefully.** The nine states beat the tier on raw ratio spread — 0.257
against 0.135 at these windows, about 1.9× — but **the omnibus test clears nothing
at 0.05**. A nine-way split of this data produces a ratio spread of 0.19 ± 0.06 by
chance; 0.257 was observed. The ordering across the nine is **not monotone** —
weak trend sits below strong trend on ratio.

What *is* significant is the single pre-specified contrast, strong trend against
strong chop on bars to peak: **+1.435 bars, t = +4.78, surrogate +0.209 ± 0.297,
0/50 draws beating it, p = 0.020**. A targeted contrast has power the max-minus-min
of nine noisy means does not. Quote that, not the omnibus.

The fast window does **not** separate better at entry: state_7's ratio spread is
0.215 against state_28's 0.257, and its only near-miss is MFE at p = 0.067. Base
stays 28.

**State age carries nothing.** Banded within each state so the band is not a proxy
for which state you are in: fresh / mid / mature give ratio 0.932 / 0.924 / 0.911,
MFE identical at 0.0141, bars 10.12 / 10.06 / 9.98. Permutation shuffling age
within state: real ratio spread 0.021 against a null of **0.048 ± 0.025, p = 0.875**
— *less* variation than chance. Per state the direction is inconsistent (strong
trend falls with age, strong transitional rises). Age is a description, not a
signal.

### 16.2c Figures that are not reproducible — do not reuse

**1.24 / 0.60 and 1.32 / 0.93 do not appear in any artefact in this repo** and
could not be reproduced at any window set or classifier. Recomputed from scratch
three times, tier ratios span 0.86–0.98 at 8/21/60 and 0.84–0.98 at 7/28/128.
`ribbon_excursion.csv`, deleted, held 0.900/0.879 — but it was 10/26/72 on the
*three-state weighted* classifier and described neither shipped set. Anything
quoting those numbers is quoting nothing.

**Two reported bugs do not exist.** No hardcoded-20 was found in the
`nine_tier_excursion.csv` path — the only literal 20s are a docstring, a 2021
timestamp and the `fav_20` column name. And `age_of` was never broken: tested on a
constructed series with a NaN gap and a resumed state it returns 1,2,1,·,·,1,2,1,2,3
correctly, `age_28` runs to a max of 70 with only 16.9% of rows at 1, and Task 9's
hazard buckets held 3,625 observations at ages 21–40 *before* any change. Nothing
was fixed because nothing was broken.

### 16.2d Agreement tiers carry nothing — settled

The tiers are a complete, symmetric enumeration of which windows disagree:

| tier | condition |
|---|---|
| all agree | f == m == s |
| fast apart | f ≠ m, m == s |
| medium apart | f == s, m ≠ s |
| slow apart | f == m, m ≠ s |
| all differ | none of the above |

**Named to predict nothing, deliberately.** The previous set (established /
transition starting / transition confirming / unresolved) asserted a narrative the
data does not support, and its fourth label was a catch-all bundling *medium
apart* with *all differ* — which is why it sat mid-table on every metric, being an
average of two different things.

**Dropped from the estimator output.** Tested formally and it is flat on every
metric. Circular-shift permutation, 500 draws, rolling the tier label series in
time so run lengths and entry clustering both survive:

| metric | real spread | null | p |
|---|---|---|---|
| MFE/\|MAE\| | 0.1200 | 0.0990 ± 0.0370 | **0.257** |
| bars to peak | 0.5291 | 0.3854 ± 0.1400 | 0.156 |
| retracement | 10.91pp | 9.77 ± 3.57 | 0.335 |
| MFE | 0.0010 | 0.0010 ± 0.0004 | 0.487 |

Cluster bootstrap by pair on the widest gap, all-agree against slow-apart: +0.062
with a 95% interval of **−0.029 to +0.165**, crossing zero, and 8.2% of draws
negative. A five-way split of this data produces a ratio spread near 0.10 by
chance; 0.12 was observed.

The configuration is still shown on the chart and in the per-pair panel as a
description of which windows disagree. No excursion table is shipped for it.

The earlier evidence, which pointed the same way:

| | ratio order, worst to best |
|---|---|
| out of sample | fast apart < medium apart < all agree < all differ < slow apart |
| in sample | medium apart < all differ < fast apart < slow apart < **all agree** |

"all agree" is *highest* in sample and third out of sample. The largest OOS gap,
all-agree 0.917 ± 0.043 against slow-apart 0.978 ± 0.033, is **t ≈ 1.1**. And the
direction flips by state family: within trend and transitional, slow-apart is
highest; within chop, all-agree is highest at 1.148 and slow-apart lowest at
0.937.

A state-mix confound was checked and rejected — it works *against* the observed
direction. Slow-apart holds 28.0% chop against all-agree's 37.0%, and chop states
have the higher ratio, so the mix should push slow-apart down, not up.

### 16.3 What each axis contributed

| Axis | Verdict | Number |
|---|---|---|
| **scale** (path/vol) | the only axis with independent content | r = **+0.041** with straightness; separates MFE 0.0150 large vs 0.0133 small |
| **straightness** | real but already covered by the composite | corrected effect 0.0314, p=0.020 |
| **persistence** | real, small, clean | corrected **0.0048** at 2.47×, p=0.039 over 50 shifts |
| **duration** (state age) | **nothing** | hazard slope real +0.039 vs surrogate +0.042 |

Note `range_vol` correlates **+0.649** with straightness — it is largely
straightness re-measured. Use `path_vol` for scale. This is why the 2×2 uses path.

### 16.4 The 200-draw null, and why one surrogate was not enough

Two surrogates, because the specified one cannot touch a scale axis:

- **A — sign randomisation.** Every |return| stays in place, only signs move.
  Preserves volatility clustering perfectly.
- **B — IID permutation.** Destroys volatility clustering, preserves the
  distribution.

| | Real | A | B |
|---|---|---|---|
| median run | 11.00 | **11.00 ± 0.00** | 10.01 ± 0.10 |
| separation | 0.3899 | 0.3781 ± 0.0030 | **0.0200 ± 0.0075** |

**`path = Σ|r|` is invariant under sign randomisation**, which is why A returns the
median run with *zero variance across 200 draws*. A scale-based classifier passes
that null by arithmetic. If you only run surrogate A you will certify anything.

Reading them together: **persistence is mechanical** (IID noise gives 10 of the 11
bars — it is the rolling window), **separation is real but near-tautological** (it
is volatility clustering, and the separation metrics restate the scale axis).

Refit stability: **99.8%** of pre-2016 pair-days keep their label after refitting
through 2020.

### 16.4 The structural classifier — built, and it fails out of sample

Swing sequence, breaks and retracements straight from price. `code/structure.py`.
**Trending** = the last two swing highs *and* the last two swing lows step the same
way, the most recent extreme was taken out by a qualifying break, and price has
not retraced past R of the impulse. Higher highs alone is not a trend — nothing in
the 175,634 tracked the with-higher-lows condition.

Swings are confirmed at t+N, never on the bar they print, then lagged one more.

144 cells, all measured on IS-A (1999-2007) and IS-B (2008-2015) only.

| lever | span of the mean IS-A contrast | verdict |
|---|---|---|
| **swing width N** | **0.691** | dominant |
| break distance D | 0.061 | weak |
| break bars-outside B | 0.029 | weaker |
| retracement R | 0.015 | negligible |

**N is the only parameter that matters, by an order of magnitude.** Of the two
break qualifiers, distance beats bars-outside — but both are noise next to N.

N=5 is a genuine plateau: all nine (B,D) cells give |t| between 2.78 and 3.93.
N=8 is equally strong and **flips sign between the two IS blocks in every cell**.
N=3 is weak but agrees in sign in all 36. N=2 is nothing.

Selection rule, stated before the sweep: among sign-agreeing cells, maximise the
*weaker* of the two blocks' |t|, so a cell that spikes in one block and dies in the
other cannot win. It chose N=3, B=3, D=1.00, R=0.62 — IS-A t −1.20, IS-B t −1.64.

**THE HOLDOUT, READ ONCE: it fails.**

| | contrast | t |
|---|---|---|
| IS-A | −1.20 | |
| IS-B | −1.64 | |
| **holdout** | **+0.2242** | **+0.94** |

The sign **inverts**. In sample, trending peaks later than chop; out of sample the
reverse, and not significantly. Against 200 sign-randomised surrogates the holdout
contrast sits at p = 0.761 — 152 of 200 draws were at least as extreme.

The selection rule was not the problem. Every configuration tried flips positive on
the holdout: the IS-A-only pick +0.21, the IS-B-only pick +0.22, N=8 +0.45. Only
the loosest cell (N=2, B=1, D=0.25, R=1.0) stays negative at −0.32, and it was
never a candidate. **The inversion is a property of the holdout, not of the pick.**

Two other gates it does pass, for the record: refit stability is genuinely 100% —
there are no fitted parameters, so refitting on more data cannot relabel history —
and persistence is high (median run 8, diagonal 0.968). But coverage is poor:
trending is only **6.7%** of holdout bars, so it is barely a two-state classifier.

**The primary metric fails; the secondary holds.** Bars-to-peak inverts and dies.
But MFE/|MAE| — the other pre-specified metric — survives on the holdout:

| contrast (holdout) | value | 95% CI | null | p |
|---|---|---|---|---|
| chop − trending, MFE/\|MAE\| | **+0.1301** | +0.014 to +0.236 | −0.011 ± 0.061 | **0.015** |
| drifting − trending, after the split | **+0.1943** | +0.061 to +0.324 | −0.021 ± 0.070 | **0.005** |

Trending entries have the *worst* MFE/|MAE| of any state, 0.803 against 0.997 for
drifting. That agrees in direction with the entirely separate nine-state grid
(strong trend 0.783 against strong chop 0.993), so two unrelated classifiers put
the same sign on it.

**The non-trending bars are not one thing.** Split five ways:

| state | share | n | MFE/\|MAE\| | bars | retrace |
|---|---|---|---|---|---|
| trending | 6.7% | 892 | **0.803** | 9.85 | 125.4% |
| broken | 45.2% | 4871 | 0.924 | 10.11 | 108.6% |
| range | 27.8% | 3348 | 0.909 | 9.99 | 109.5% |
| drifting | 20.3% | 2056 | **0.997** | 10.11 | 101.0% |
| no swings | 0.0% | — | — | — | — |

Splitting widens the ratio contrast from 0.130 to 0.194 and takes it from p=0.015
to p=0.005. "Neither" was hiding structure. `no swings` is empty on the holdout —
it only exists during warm-up.

**Two files, not comparable.** `structure_surface.csv` is the 144-cell sweep,
**in-sample only** (`A_*` = 1999-2007, `B_*` = 2008-2015); the holdout appears
nowhere in it. `structure_result.csv` is the one chosen configuration read once on
the holdout. They never describe the same sample.

### 16.4b Does anything describe SHAPE? Present-tense battery — no.

The excursion tests in 16.4 were forward-looking and should never have been read
as verdicts on a descriptive classifier. This is the correct framework: coverage,
run length, transition diagonal, separation on realised properties, refit
stability, nulls. No forward measurement.

Separation in sd units, holdout, common window W=28, three classifiers:

| property | structural | grid | weighted | |
|---|---|---|---|---|
| autocorrelation | **0.266** | 0.092 | 0.074 | shape, neutral |
| direction changes | 0.238 | 0.292 | 0.108 | shape, neutral |
| mean crossings | 0.551 | **1.134** | 0.146 | shape, neutral |
| same-sign run length | 0.208 | 0.311 | 0.122 | shape, neutral |
| variance ratio k=5 | **0.336** | 0.051 | 0.087 | shape, kin to net/path |
| variance ratio k=10 | 0.297 | 0.261 | 0.124 | shape, kin to net/path |
| range/path | 1.581 | 1.670 | 0.353 | shape, kin to net/path |
| realised vol | 0.079 | 0.881 | 0.630 | magnitude |
| mean absolute move | 0.051 | 0.976 | 0.724 | magnitude |

**The structural classifier is nearly blind to magnitude** — 0.065 mean against the
grid's 0.928. That is a real and clean property: it describes shape and only shape,
by construction.

**On the property named as the gap it is much better.** Autocorrelation separates
at 0.266 against the grid's 0.092 and the weighted classifier's 0.074 — roughly
3×. Same for variance ratio k=5, 0.336 against 0.051.

**But neither classifier's shape separation survives its own null.** Mean over the
four neutral shape properties, 60 surrogates each:

| | real | sign-randomised | IID | p |
|---|---|---|---|---|
| structural | 0.316 | 0.340 ± 0.023 | 0.325 ± 0.021 | 0.869 / 0.656 |
| grid | 0.457 | 0.517 ± 0.027 | 0.492 ± 0.025 | 0.984 / 0.934 |

Both sit **below** both surrogate means. Corrected, the grid is −0.060 and the
structural −0.024. Slicing a price series into persistent blocks by any rule
separates these properties this much, because the properties are themselves
autocorrelated; neither classifier adds anything to that.

So the answer to "does the structural definition describe shape better than
straightness does" is: **better on serial-dependence measures, worse on
oscillation-count measures, and neither beats a surrogate.** The magnitude
separation the earlier battery reported is the part that is real — 0.881 and 0.976
for the grid against nulls of 0.378 and 0.020. Shape is not described by either.

Refit stability is 100% for both grid and structural on 117,936 and 119,616
pre-2016 pair-days. Persistence: structural median run 3 diagonal 0.810 across 4
holdout states; grid 4 and 0.831 across 9; weighted 11 and 0.935 across 3.

### 16.4c Flickering and coverage: both fixed, neither helps

**Flickering, fixed.** The structural state is categorical, so it has no score to
put a hysteresis band around. The equivalent is a **confirmation dwell**: a new
state must print M consecutive bars before it is adopted, and the previous state
is held until then. Symmetric, costs M-1 bars of recognition lag, strictly causal.
`combined.confirm()`. Sweep on the structural state:

| M | median run | under 5 bars | diagonal | shape sep | eta2 |
|---|---|---|---|---|---|
| 1 | 3 | 61.9% | 0.809 | 0.316 | 0.0185 |
| 2 | 5 | 43.0% | 0.868 | 0.350 | 0.0217 |
| 3 | 8 | 27.7% | 0.901 | 0.381 | 0.0243 |
| **5** | **13** | **0.1%** | **0.948** | **0.477** | **0.0344** |
| 8 | 25 | 0.1% | 0.977 | 0.747 | 0.0358 |
| 13 | 90 | 0.0% | 0.995 | 0.384 | 0.0055 |
| 21 | 540 | 0.0% | 1.000 | 0.331 | 0.0013 |

M=5 is the smallest dwell reaching an 11-bar median run. Past M=8 the states
collapse into each other and eta2 falls off a cliff.

**THE 42% FIGURE WAS `broken`, NOT `no swings`.** Measured across the whole swing
grid, `no swings` is 0.9-1.0% of bars at every N and **0% of holdout bars**. There
is no unlabelled 70% and nothing for a fallback layer to fill — built anyway as
`combined.fallback()`, it is identical to the raw structural state to three
decimals on every metric. Shares at the shipped config: broken 0.457, range 0.263,
drifting 0.198, trending 0.073, no swings 0.009. The real coverage problem is that
**one state holds 46% of bars while `trending` holds 7%**, and a fallback cannot
touch that.

So the two classifiers are combined the way that uses both: **activity on every
bar crossed with shape on every bar** — 4 shape x 3 scale terciles = 12 states,
`combined.product()`. At M=5 it beats both parents on every shape property.

**SEPARATION IS NOT COMPARABLE ACROSS STATE COUNTS OR DWELLS.** A 12-state
classifier has more chances at an extreme than a 4-state one, and a longer dwell
lengthens every block, which raises separation on properties that are themselves
autocorrelated. Only the null-corrected value compares — the surrogate carries the
identical classifier, state count and dwell. 120 draws:

| null | classifier | real | surrogate | corrected | p |
|---|---|---|---|---|---|
| sign | structural raw | 0.316 | 0.337 ± 0.023 | −0.021 | 0.851 |
| sign | structural M=5 | 0.477 | 0.520 ± 0.032 | **−0.043** | 0.909 |
| sign | product M=5 | 0.560 | 0.646 ± 0.051 | **−0.087** | 0.959 |
| sign | grid | 0.457 | 0.512 ± 0.028 | −0.054 | 0.992 |
| iid | structural raw | 0.316 | 0.329 ± 0.023 | −0.013 | 0.694 |
| iid | structural M=5 | 0.477 | 0.504 ± 0.034 | −0.027 | 0.810 |
| iid | product M=5 | 0.560 | 0.636 ± 0.053 | −0.076 | 0.926 |
| iid | grid | 0.457 | 0.489 ± 0.025 | −0.031 | 0.884 |

**The dwell raises the surrogate faster than it raises the real value, and so does
the product.** Every corrected value is negative and the gap widens as the state
gets more persistent and more elaborate. Refit stability 100% for both, product
and structural, on ~117,600 pre-2016 pair-days.

Both fixes work as fixes — 3-bar runs with 62% under five become 13-bar runs with
0.1%, and coverage is complete — and neither buys any shape description. 16.4b's
conclusion is unchanged and now holds across seven classifier variants.

### 16.4d IS-only selection of the structural cell. Shape does not hold.

structure.py's own 144-cell sweep selected on bars-to-peak and MFE/|MAE| — forward
measurements, which this project no longer treats as verdicts on a descriptive
classifier. So the cell had never been chosen on the criterion it is now judged
by. `structsel.py` redoes it.

**Criterion, written into the file before the sweep ran:** mean **null-corrected**
shape separation over the four neutral properties. Corrected, not raw — raw
separation rises with block length, so selecting on raw would pick the most
persistent cell and call it the most descriptive. Every cell is measured against
its own sign surrogate at the same parameters and the same dwell. Select on IS-A,
require IS-B to agree in sign, holdout read once. The dwell is held at M=5 (fixed
in 16.4c on persistence alone), so the search space stays at 144.

**A degeneracy had to be fixed first.** At the loosest break settings `drifting`
collapses to **six observations** in 1999-2007 and its mean alone set the
max-minus-min gap, producing a corrected separation of +1.27 on IS-A against
+0.03 on IS-B. `structval.separation` now drops any state under a 2% share of the
block. This changes nothing already published — the smallest holdout share in
16.4b/16.4c is 4.7% — but without it the selection is meaningless.

**The surface, 40 surrogate draws per cell:**

| | count |
|---|---|
| positive corrected on IS-A | 84 of 144 |
| positive corrected on IS-B | 68 of 144 |
| positive on **both** | **36 of 144** |

39.7 is what independent coin flips would give. **Block agreement is at chance.**
Every one of the top eight cells by IS-A corrected separation is *negative* on
IS-B — the IS-A ranking does not transfer. And **R is inert**: mean IS-A corrected
separation is +0.0421 / +0.0428 / +0.0424 / +0.0428 across the four retracement
thresholds. The retracement parameter does nothing on this criterion.

**Chosen cell: N=2, B=3, D=1.00, R=0.62.** IS-A corrected +0.0968 (z +2.23), IS-B
+0.0171 (z +0.43) — it met the bar, weakly.

**Holdout, read once, 120 draws each:**

| null | real | surrogate | corrected | p |
|---|---|---|---|---|
| sign | 0.495 | 0.561 ± 0.045 | **−0.066** | 0.909 |
| iid | 0.495 | 0.547 ± 0.036 | **−0.051** | 0.909 |

**Shape separation does not hold.** The properly-selected cell is further below
its own surrogate on the holdout than the unselected one was.

**A degradation to record:** the IS-selected cell is more lopsided than
structure.py's own. `trending` falls from 7.3% of bars to 5.6%, and `broken` still
holds 44%.

**One positive number, and why it should not be promoted.** At the new cell the
twelve-state product reads corrected **+0.024** (p=0.215) and **+0.036** (p=0.140)
— the only positive corrected values anywhere in 16.4b-d. It was not the selected
object; selection ran on the structural classifier. At the *previous* cell the same
product read −0.087 and −0.076. Changing the swing width from 3 to 2 moved it from
−0.087 to +0.036 with p never below 0.14, across eight comparisons. That is what an
unstable noise quantity looks like, not a finding. Do not route on it.

Layer 1's interface now carries `shape`, `activity` and `combined`; both
self-assertions still pass on all 191,940 pair-days.

### 16.4e Counting, per pair, transitions — and a correction to 16.4b-d

**CORRECTION FIRST.** "The magnitude reading survives at 0.881 and 0.976 against
nulls of 0.378 and 0.020" was stated three times and it is **not a matched
comparison**. The two real values are the *nine-state grid's*. The two null values
come from `classifier_validation.csv` and belong to the *three-state weighted*
classifier — different classifier, and a single pooled scalar rather than a
per-property null. The grid's magnitude separation had never been nulled at all.
`magnull.py` does it properly:

| null | property | real | surrogate | corrected | p |
|---|---|---|---|---|---|
| sign | realised vol | 0.881 | 0.851 ± 0.030 | +0.030 | 0.197 |
| sign | mean abs move | 0.976 | 0.922 ± 0.023 | +0.054 | 0.033 |
| iid | realised vol | 0.881 | 0.551 ± 0.045 | **+0.330** | 0.016 |
| iid | mean abs move | 0.976 | 0.885 ± 0.046 | +0.091 | 0.066 |

And **the sign surrogate is nearly degenerate for a magnitude axis**: it keeps
every |r| exactly in place, so mean absolute move is *exactly* invariant under it
and `path = Σ|r|` barely moves, so the grid's scale axis barely moves. Only the
IID row is a real test — and clearing IID mostly establishes that volatility
clusters, which was never in question. The magnitude claim stands, but far more
weakly than 16.4b-d said.

**1. BARS ARE NOT INDEPENDENT.** Correct, and it applies unevenly.

*Surrogate-based p-values were already sound.* They recompute the whole statistic
on each surrogate panel, so the null distribution carries all the serial and
cross-pair dependence the real panel has. Redone on episode means, the verdicts
do not move — and the one positive number from 16.4d dies:

| null | classifier | real | surrogate | corrected |
|---|---|---|---|---|
| sign | structural M=5 | 0.459 | 0.518 ± 0.048 | −0.059 |
| sign | product M=5 | 0.451 | 0.668 ± 0.073 | **−0.218** |
| sign | grid | 0.349 | 0.413 ± 0.021 | −0.064 |

*t-statistics pooled over bars or events were inflated.* Effective sample:

| classifier | bars | episodes | overstatement |
|---|---|---|---|
| structural M=5 | 74,004 | 3,275 | **22.6×** |
| product M=5 | 74,004 | 4,199 | 17.6× |
| grid | 74,004 | 12,649 | 5.9× |

Two corrections applied: episode basis (fixes serial dependence within a pair)
and a **moving-block bootstrap over calendar dates** at block lengths 21/63/126
(a block carries every pair on those dates, so cross-pair correlation rides
along). The bootstrap is primary. Every excursion contrast redone:

| contrast | metric | obs | published t | p@21 | p@63 | p@126 |
|---|---|---|---|---|---|---|
| grid: strong chop − strong trend | bars_to_peak | +1.435 | +4.78 | **0.000** | **0.005** | **0.000** |
| grid: strong chop − strong trend | MFE/\|MAE\| | +0.210 | — | **0.033** | **0.002** | **0.000** |
| structure: non-trending − trending | path_eff | +0.020 | +2.27 | 0.198 | 0.231 | 0.200 |
| grid: strong chop − strong trend | path_eff | +0.015 | +2.14 | 0.215 | 0.256 | 0.193 |
| tier: all differ − all agree | path_eff | −0.009 | −1.67 | 0.187 | 0.167 | 0.092 |
| tier: all differ − all agree | MFE/\|MAE\| | +0.070 | — | 0.312 | 0.219 | 0.179 |
| structure: non-trending − trending | bars_to_peak | −0.080 | −0.22 | 0.905 | 0.913 | 0.951 |
| others | | | | all > 0.39 | | |

**Two survive, both the same contrast**: strong chop takes 1.43 bars longer to
peak than strong trend, and has a 0.21 higher MFE/|MAE|. Rule of thumb from this
table: a published |t| under about 3 does not survive the block bootstrap.

**2. PER PAIR.** `perpair.py`. Every pair scored against **its own** surrogate —
a per-pair number against a pooled null would clear the bar for reasons that have
nothing to do with the classifier.

- **Corrected shape: 10 of 28 pairs positive, median −0.036.** Best AUDJPY +0.428
  (z +2.23), worst AUDNZD −0.232. One pair past |z|=2 out of 28 is what chance
  gives. Same 10-of-28 for the structural classifier and for the grid.
- **DEGENERATE: 28 of 28.** Every pair leaves states unused at the 2% floor —
  typically 7-9 of 12. Pooled, the product looked fine; per pair its vocabulary
  fits nobody. This is the finding pooling hid.
- **UNSTABLE: 0 of 28.** The dwell works uniformly, median run 13-16 everywhere.
  Coverage is 1.00 on every pair.
- **Magnitude is a coin flip per pair**: 16 of 28 positive, median +0.013, and
  the top value is EURNZD +1.710 at z +7.46 — one outlier carrying the ranking.
  All six JPY crosses are negative.

**3. TRANSITIONS.** `transitions.py`. Bars with age ≤3 against age ≥15, *within
the same state*. Some difference must exist mechanically — a 28-bar window three
bars into a new state is still mostly describing the old one — so the surrogate,
with the same windows and dwell, is what that mechanical part looks like.

**No corrected effect reaches |z| = 2 across 18 comparisons.** Largest are grid
mean-abs-move −0.054 (z −1.42), product run_length +0.040 (z +1.71). The raw
edge-minus-interior differences do reach small bootstrap p, but the surrogate
reproduces nearly all of them.

**Direction carries nothing, and not in the way expected.** If direction were
irrelevant, X→Y and Y→X would be the same displacement with *opposite* sign. The
antisymmetry correlations are −0.785, −0.665, −0.994, −1.000 — the two directions
give the **same** signed shift. trending→broken reads (−0.144, −0.200, −0.626,
+0.250) and broken→trending reads (−0.108, −0.225, −0.517, +0.217). The signature
belongs to the boundary between two states, not to the way it was crossed.

### 16.4f Two axes or one. The nine-box is not replaced by anything.

`axes2.py`. Also corrects two figures that were quoted at me and are not what
they were taken to be: **0.751 is `classifier_validation.csv`'s `avg_abs_move`
and belongs to the THREE-STATE WEIGHTED classifier, not the nine-box** (the
nine-box reads 0.976 on mean-abs-move and 0.881 on realised vol), and **0.762
does not appear anywhere in `results/`** — the combined figures are 0.746 and
0.660. `layer1_states.csv` does carry `state_7/28/128`, `scale_28`, `activity`,
`shape` and `combined` all at once; nothing was replaced.

**1. SCALE IS GENUINELY FEEDING THE COMBINED STATE.** The path is
`act = tercile(raw_axes(px)['scale'], fit)` → `act + ' ' + shape` → the 5-bar
dwell on the joint label. Being in the string is not proof, so ablation:

| variant | magnitude | shape | states |
|---|---|---|---|
| combined (shape × activity) | 0.703 | 0.460 | 12 |
| shape only, activity removed | **0.137** | 0.495 | 4 |
| activity only, shape removed | 0.744 | 0.079 | 3 |
| **nine-box grid** | **0.928** | 0.457 | 9 |

Remove activity and magnitude separation collapses 0.703 → 0.137. Remove shape
and it does not move. **And the nine-box on its own beats the combined state on
both axes** — 0.928 vs 0.703 on magnitude, 0.457 vs 0.460 on shape, a tie.
Crossing shape into it costs magnitude resolution (12 states spread over the same
data) and buys nothing.

`combined` equals `activity + ' ' + shape` on only 66.5% of holdout rows: the
joint label's dwell restarts when *either* half changes, while `shape` confirms
shape alone. Neither column is derivable from the other.

**2. SHAPE AND ACTIVITY ARE INDEPENDENT.** Cramér's V **0.094** [0.069, 0.115],
normalised mutual information 0.009. Observed/expected stays inside 0.67–1.47 in
every one of the twelve cells. Shape separation inside weak / medium / strong
activity is **0.564 / 0.453 / 0.472** with heavily overlapping bootstrap
intervals — shape reads the same way whether or not the pair is moving. The
mirror holds too: magnitude separation inside trending / broken / range /
drifting is 1.020 / 0.807 / 0.814 / 0.816.

So they are two axes, not one, and neither is redundant. **Independence is not
informativeness, though** — the shape axis is orthogonal *and* fails its own null
(16.4d, 16.4e). It is a second axis that describes nothing measurable.

Against **straightness**, the nine-box axis shape might be replacing, V is
**0.193** — twice the overlap, with structural `trending` at 2.81× expected
inside the nine-box trend family and 0.149× inside chop. Related, as two attempts
at the same thing should be. Not a replacement.

**3. SETTLING IS NOT TRANSITIONAL RENAMED.** P(transitional | settling) 0.3544
against a base rate of 0.3565 — **lift 0.994**. Reverse: 0.1681 against 0.1691,
lift 0.994. Joint 0.0599 against 0.0603 expected under independence. Cramér's V
**0.0020**. The two labels pick out different bars, at chance with respect to
each other.

**WHAT REPLACES WHAT: nothing.** The nine-box stays whole and stays primary. It
is the strongest magnitude reader in the file (0.928), it ties the structural
work on shape, and its straightness axis is only weakly overlapped. The
structural layer sits alongside as an orthogonal description in
`layer1_states.csv` — carried, not routed on.

### 16.4g Bridging the confirmation delay: nothing beats chance

`leadtime.py`. **Deliberately predictive** — the one place in the Layer 1 work
where that is the right frame. Everywhere else the question is what a state
describes; here it is whether something fires *before* the dwell confirms a
change, which cannot be asked in the present tense.

The 5-bar dwell means a change visible in raw structure at *t* is not in the
shipped label until *t*+4. Three cheap close-only candidates, all lagged:

| | definition |
|---|---|
| `mas` | 5-bar mean turning against the 20-bar mean, scored by the fast leg's move in vol units |
| `vol` | 5-day over 60-day realised volatility |
| `rng` | 5-bar close range over its own 60-day average |

**Thresholds calibrated, not picked.** Each score is cut at the IS quantile
giving a 10% firing rate, so all three carry the same budget and their lifts
compare. A fire is an upward *crossing*, not the condition holding — otherwise a
persistent condition inflates the base rate and flattens every lift toward 1.

**Held to the confluence standard.** Cross-horizon confluence fired 79% before
real changes and 79% before surrogate ones. So hit-vs-base is not enough: the
whole thing — signals *and* states — is rebuilt on 60 sign and 60 IID surrogate
panels, and what counts is **excess** = lift minus the larger surrogate lift.

Best five of 36:

| state | signal | lead | hit | base | lift | sign | iid | excess | p |
|---|---|---|---|---|---|---|---|---|---|
| nine-box | rng | 1 | 4.5% | 3.9% | 1.132 | 1.071 | 1.046 | +0.060 | 0.082 |
| product M=5 | mas | 1 | 9.0% | 5.2% | **1.739** | 1.680 | 1.658 | +0.059 | 0.197 |
| product M=5 | rng | 3 | 9.1% | 11.7% | 0.775 | 0.730 | 0.732 | +0.043 | 0.082 |
| structural M=5 | vol | 2 | 5.5% | 6.4% | 0.858 | 0.808 | 0.824 | +0.035 | 0.164 |
| nine-box | rng | 3 | 12.1% | 11.7% | 1.031 | 0.997 | 0.964 | +0.034 | 0.066 |

**0 of 36 beat both surrogates by more than 0.05 lift at p<0.05.**

The MA slope divergence looks like a find at first — 1.739× lift, 9.0% hit
against a 5.2% base, at one bar of lead. Its surrogate is 1.680. Exactly the
confluence pattern: the signal and the state are both reacting to the same
volatility burst, so shuffling the signs of the returns barely touches either.
`vol` and `rng` mostly fire *below* chance — they lag the change rather than
lead it.

**So the lag is accepted, as specified.** `settling` is now a column in
`layer1_states.csv`: a graded confidence, `min(age/5, 1)` on the combined state
— 0.2 on the first bar a state is adopted, 1.0 from the fifth. 22.6% of holdout
bars carry a reduced weight, 77.4% are fully weighted. Not a binary flag, and
not hidden.

### 16.4h The lead-time candidates, swept. And what the MA signal was doing.

**16.4g tested three points, not three ideas.** `mas` 5/20, `vol` 5/60, `rng`
5/60 were conventional settings, none selected by anything. A null on one cell
of a two-dimensional surface says that cell is dead; it says nothing about the
approach, and reporting it as though it did was wrong. `masweep.py` sweeps all
three, both windows 1–200 on a 20-point log grid, 3 states × 2 leads = **3,420
cells**, every cell against its own surrogate at its own window pair and a common
IS-calibrated firing budget.

**The bar, set before the surface was read:** a single spiking cell in a 190-cell
grid is what noise looks like. A **plateau** — a contiguous region several cells
across — would mean something.

| threshold | cells clearing at p<0.05 | share |
|---|---|---|
| excess > 0.05 | 102 of 3,420 | **3.0%** |
| excess > 0.10 | 29 of 3,420 | 0.8% |
| excess > 0.20 | 5 of 3,420 | 0.1% |

**Chance alone gives about 5% at p<0.05. The sweep produced fewer.**

Per family, on the primary state at lead 1:

| family | cells > 0.05 | largest contiguous | best cell | excess | p | neighbours |
|---|---|---|---|---|---|---|
| mas | 37 of 190 | 8 | 5/8 | +0.214 | 0.024 | mean +0.059 |
| vol | 41 of 189 | 11 | 8/200 | +0.281 | 0.024 | mean +0.076 |
| rng | 9 of 171 | **1** | 118/152 | +0.211 | 0.317 | mean **−0.296** |

Range expansion is the clearest failure — an isolated spike whose immediate
neighbours average −0.296.

**WHAT THE MA SIGNAL WAS ACTUALLY DOING.** The raw lift surface is not flat. It
has one sharp, coherent ridge at **fast=5** running across every slow window,
peaking at 2.13×, with fast=4 and fast=6 at roughly 1.2. The shipped dwell is
5 bars. That is not a coincidence, and it is testable — move the dwell and see
if the ridge moves:

| dwell M | ridge peaks at fast = | peak lift |
|---|---|---|
| 2 | **2** | 1.49 |
| 3 | **3** | 1.63 |
| 5 | **5** | 2.13 |
| 8 | **8** | 2.40 |
| 13 | 8 | 1.85 |

**The ridge tracks the dwell.** An M-bar mean's slope turns over exactly the M
bars the confirmation is counting, so the signal is reading the same window the
dwell reads — not leading it. It cannot bridge a delay it is measuring from the
inside. That is why the lift is large and why the surrogate reproduces nearly all
of it (1.913 of the 2.127).

So the approach is now tested rather than the setting, and the conclusion in
16.4g stands: the graded `settling` confidence is the answer, and the 4-bar lag
is accepted.

### 16.4i IS/OOS split on the sweep: dropped. And the merged Layer 1.

**The flaw in 16.4h**: `state_masks` ran with `period='oos'`, so all 3,420 cells
were measured on the holdout and its peak was selected on the same data it was
scored on. Redone in `masweep.split_select()`: every cell measured on IS only,
best cell selected there, holdout read once with 200 surrogate draws.

Two figures I had quoted need fixing: the sweep peak was **2.13×** (2.40× at
dwell 8), not 1.61 — 1.61 is a cell in the M=13 row — and the grid is **3,420**
cells, not 6,000.

**On IS**: 1,290 of 3,420 cells have positive excess — 37.7%, below a coin flip.
Top cell `rng` fast=72 slow=200 on structural M=5 at lead 1, IS lift 1.492
against a surrogate of 0.914, **excess +0.578, z +3.61**. A strong-looking IS
result.

**Holdout, read once:**

| null | lift | surrogate | excess | p |
|---|---|---|---|---|
| sign | 1.117 | 1.190 ± 0.319 | **−0.073** | 0.592 |
| iid | 1.117 | 1.260 ± 0.298 | **−0.143** | 0.662 |

IS lift 1.492 → holdout 1.117, and the holdout excess is negative against both
nulls. **Does not survive. Dropped.** There is no second confirmation signal; the
graded `settling` confidence stands alone, as specified.

Note what the split changed and what it did not: the *lift* is still above 1 on
the holdout, because the lift is mechanical (16.4h — the signal reads the same
window the dwell counts). The *excess* is what had to hold and it did not.

### 16.4j THE MERGED LAYER 1 — final state

`layer1sum.py` assembles every claim next to the test run on it and writes
`results/layer1_summary.csv`. It computes nothing new.

```
shape      structural read at the IS-selected cell, 5-bar confirmation dwell
activity   nine-box scale axis, path/(vol*sqrt(28)), IS terciles
combined   the twelve-state product, '<activity> <shape>'
settling   graded confidence, min(age/5, 1)
```

and `state_7/28/128`, `straight_28`, `scale_28`, `tier`, `age_28` **unchanged**.
191,940 rows, 28 pairs, 1999-04-01 to 2026-07-31, **1.000 coverage on every
column** in the holdout. Shares: shape broken 0.633 / range 0.266 / drifting
0.075 / trending 0.026; activity medium 0.383 / weak 0.321 / strong 0.295;
settling 0.774 at full weight.

**WHAT SURVIVED ITS OWN NULL — the whole list:**

1. the nine-box **scale axis** on realised vol, +0.330 against an IID surrogate,
   p=0.016 (and +0.091 on mean-abs-move, p=0.066). Only against IID; the sign
   surrogate is degenerate for a scale axis.
2. **strong chop vs strong trend** on bars-to-peak (+1.43 bars) and MFE/|MAE|
   (+0.21), block-bootstrapped at all three block lengths.

Nothing else. Shape separation fails on bars and fails harder on episodes
(product M=5: −0.218). The IS-selected structural cell fails. The tier fails.
The lead-time signals fail, swept and split.

**WHAT TO ROUTE ON**: `activity` / `scale_28`. `shape` and `combined` are
orthogonal to it (V 0.094) and to the straightness family (V 0.193), so they are
not redundant — but they fail their own nulls, so they are not informative
either. `settling` is a weight, not a state. `tier` is description only.

### 16.4k Three kinds of regime change. Activity carries half of them.

`changes.py`. The point is right and the numbers back it: the same shape at high
activity is a trend and at low activity a drift, so an activity move is a regime
change. No volume exists for FX — H.10 is close-only, the market is
decentralised — so distance travelled, `path/(vol·√28)`, is the proxy and nothing
here claims more.

**A decomposition problem that has to be stated.** The shipped `combined` applies
the dwell to the *joint* label, so it cannot be split back into halves. Both
objects are carried: `combined` counted, and a **split-join** —
`confirm(shape) + confirm(activity)`, each dwelled on its own axis — decomposed.

| kind | changes | rate | mean gap |
|---|---|---|---|
| shape only | 3,117 | 4.212% | 23.7 bars |
| activity only | 3,125 | 4.223% | 23.7 bars |
| both same bar | 132 | 0.178% | 560.6 bars |
| split-join any | 6,374 | 8.613% | 11.6 bars |
| combined (shipped) | 4,173 | 5.639% | 17.7 bars |

**48.9% shape / 49.0% activity / 2.1% both.** Almost exactly even, and
**independent**: 132 same-bar changes against 143 expected by chance, ratio 0.92.
The shipped `combined` records 34.5% fewer changes than the split-join total —
the joint dwell merges changes landing within 5 bars of each other.

**WHICH DO THE SIGNALS TRACK — they split cleanly by axis:**

| signal | shape only | activity only |
|---|---|---|
| mas 5/8 | **+0.183 (p=0.024)** | −0.007 (p=0.634) |
| vol 8/200 | −0.076 (p=0.780) | **+0.349 (p=0.024)** |
| rng 5/60 | −0.122 | −0.122 |

A moving-average signal reads shape; a volatility-ratio signal reads activity.
That is what their construction says they should do, and it is worth knowing
before either is read as tracking "the state". `both` is not readable at n=132 —
`rng 72/200` posts an 8.245 lift there on 132 events.

### 16.4l Failed swings: a real IS plateau that does not survive

`failswing.py`. Definition entirely within the trailing window: at bar *t*, with
the 28-bar window split into an old part [t−28, t−6] and a recent part [t−5, t],
price reached at least X of the way from the old low back to the old high
**without clearing it**, and has since turned back from that recent peak by at
least Y multiples of the recent average daily range. Mirror for the downside.
Every clause is a max, min or mean of bars at or before *t*, then shifted one.

The no-clearing clause is load-bearing: without it every successful breakout
fires too and X stops meaning anything.

X ∈ {0.85, 0.90, 0.93, 0.95, 0.97, 0.98, 0.99} × Y ∈ {0.5, 0.75, 1, 1.5, 2, 3,
4} = 49 cells. Firing rates run 0.128% to 6.173% of bars.

**The IS surface has a genuine plateau** — shape changes, IS excess:

| X \ Y | 0.50 | 0.75 | 1.00 | 1.50 | 2.00 | 3.00 | 4.00 |
|---|---|---|---|---|---|---|---|
| 0.85 | −0.029 | −0.019 | −0.024 | −0.025 | −0.048 | −0.038 | −0.012 |
| 0.90 | +0.013 | +0.038 | +0.025 | +0.018 | +0.028 | +0.057 | +0.073 |
| 0.93 | +0.091 | +0.134 | +0.117 | +0.114 | +0.119 | +0.131 | +0.193 |
| 0.95 | +0.093 | +0.110 | +0.112 | +0.108 | +0.111 | +0.148 | +0.221 |
| 0.97 | +0.058 | +0.076 | +0.094 | +0.088 | +0.031 | +0.073 | +0.319 |
| 0.98 | +0.047 | +0.067 | +0.095 | +0.134 | +0.082 | +0.170 | +0.528 |
| 0.99 | +0.135 | +0.027 | +0.076 | +0.143 | +0.139 | +0.078 | +0.669 |

**34 of 49 cells above +0.05, 33 of them contiguous.** That is the broad plateau
the bar was set at, and X=0.85 failing while X≥0.93 works is a sensible boundary
rather than a random one. Combined-shipped is stronger still: 39 of 49, all
contiguous.

**A flaw in my own plateau criterion, caught and fixed.** A 3×3 neighbourhood
mean is not sufficient: a corner cell has only three neighbours, so a lone spike
at the grid edge survives smoothing. On the first run X=0.99 Y=4.00 won on *both*
the raw and the smoothed criterion while firing on **0.128% of bars**, the
sparsest cell in the sweep. Selection is now restricted to **interior** cells,
where a full 3×3 exists.

**Chosen on IS: X=0.98, Y=3.00, shape changes.** Neighbourhood mean +0.232 over 8
neighbours, IS lift 0.681 vs surrogate 0.511, excess +0.170, z +1.13.

**Holdout, read once, 200 draws:**

| null | lift | surrogate | excess | p |
|---|---|---|---|---|
| sign | 0.164 | 0.477 ± 0.190 | **−0.313** | 0.960 |
| iid | 0.164 | 0.444 ± 0.166 | **−0.281** | 0.960 |

**Does not survive.** The holdout lift is 0.164 — failed swings fire *far below*
chance before shape changes out of sample, having looked coherent on IS across 33
contiguous cells. A broad plateau is a better filter than a single cell and it
still was not enough.

### 16.4m Three shapes, not four. The lookback answer. Old vs new.

**THE FOURTH SHAPE WAS NEVER IN THE SPEC, and that is my error.**
`structure.five_state` emits trending / broken / range / drifting, and I carried
all four into the product, making 12 states where the spec said 9. `broken` then
took 64% of days while `trending` took 2.9% — the classifier spent most of its
time reporting a diagnostic, not a regime.

**Fixed as a partition, not a fold** (`shape3.py`). One question asked twice:
inside the last confirmed swing band → **range**; outside it → **trending** if
the swing sequence supports the break, **drifting** if it does not. `broken` was
the leftover of a rule requiring *both* sequence legs to step the same way; bars
that broke out with one leg confirming are now trending, with neither are
drifting. Every bar labelled exactly once.

| mode | trending | range | drifting | balance |
|---|---|---|---|---|
| strict N=5 | 0.092 | 0.518 | 0.390 | 0.845 |
| **relaxed N=5** | **0.185** | **0.518** | **0.297** | **0.923** |
| breakonly N=3 | 0.197 | 0.501 | 0.302 | 0.936 |

Balance is entropy over the three states, IS only — a design criterion, not
scored against any outcome. The raw winner is **breakonly, and it is rejected**:
it drops the swing sequence, so "trending" would mean only "a break happened and
price has not retraced". `structure.py` exists because higher highs alone is not
a trend. Not traded away for 0.013 of entropy.

**Shipped: relaxed, N=5.** Holdout shares now **range 0.614 / drifting 0.207 /
trending 0.178**, against the old **broken 0.440 / range 0.267 / drifting 0.240 /
trending 0.053**. Trending goes from 2.6% to 17.8%. `layer1_states.csv`
regenerated; both self-assertions still pass on all 191,940 pair-days.

**WHAT LOOKBACK DOES SHAPE USE — it has no fixed window.** The nine-box reads 7,
28 and 128 bars. The shape read is *event-driven*: its memory runs back to the
second-most-recent confirmed swing on each side, whose distance moves with the
market. Measured rather than asserted — bars back to the anchoring swing:

| N | p10 | median | mean | p90 | p99 |
|---|---|---|---|---|---|
| 2 | 10 | 14 | 15.2 | 22 | 30 |
| 3 | 14 | 21 | 22.5 | 32 | 44 |
| **5** | **23** | **35** | **36.7** | **52** | **71** |
| 8 | 37 | 55 | 57.8 | 82 | 109 |
| 13 | 60 | 88 | 91.3 | 127 | 170 |

**N is the horizon knob** — the direct analogue of the ribbon's windows. For a
daily entry held for weeks, N=5 (median 35 bars, p90 52) is the closest match to
the 28-day ribbon leg; N=2 is the fast leg and N=8–13 the slow one. Running three
N values side by side would reproduce the ribbon on the shape axis. That is a
build decision and it is not done yet.

**OLD vs NEW, same battery, same 5-bar dwell on every classifier** (`oldnew.py`).
Corrected = real minus its own surrogate, which is the only cross-classifier
column that means anything.

| classifier | states | run | min share | shape raw | act raw | shape corr (sign/iid) | act corr (sign/iid) |
|---|---|---|---|---|---|---|---|
| nine-box (dwelled) | 9 | 11 | 0.094 | 0.422 | 0.835 | −0.108 / −0.081 | +0.067 / +0.264 |
| **shape3 × activity** | 9 | 12 | 0.054 | 0.371 | 0.751 | **+0.026 / +0.037** | −0.003 / +0.267 |
| shape3 alone | 3 | 14 | 0.178 | 0.254 | 0.096 | −0.011 / −0.002 | +0.038 / +0.043 |
| activity alone | 3 | 19 | 0.301 | 0.079 | 0.744 | +0.037 / +0.037 | +0.005 / +0.256 |
| nine-box (as shipped) | 9 | 4 | 0.086 | 0.457 | 0.928 | −0.054 / −0.034 | +0.052 / +0.197 |

Refit stability is 100% for all five.

**What the old does well**: the highest *raw* separation on both axes (0.457 /
0.928) and the most even coverage (min share 0.086 undwelled). **What the new
does well**: it is the **first classifier in this project with a positive
corrected shape separation** (+0.026 / +0.037), and it fixes the coverage
pathology — trending 17.8% not 2.6%.

**Is the merge better than either alone? No — it is about the max of its parts.**
On shape, merge +0.026 against activity-alone **+0.037** and shape3-alone −0.011.
On activity, merge +0.267 against activity-alone +0.256 and nine-box +0.264.

And the uncomfortable line in that table: **the activity axis describes the shape
properties better than the shape axis does** (+0.037 vs −0.011). Per pair, same
story — activity alone is positive on 18 of 28 pairs, median +0.026; shape3 ×
activity on 13 of 28, median −0.005; the dwelled nine-box on 7 of 28.

**Results computed before this change** — 16.4k's change counts have been rerun
(shape now 53.4% of changes, activity 44.0%, both 2.6%, independence ratio 1.04);
`episodes`, `perpair`, `transitions`, `axes2`, `failswing` and `masweep` still
carry 12-state numbers and refresh on the next full pipeline run.

### 16.4n The shape lookback swept. Coverage fixed, separation not.

**There is no 'broken'. Three shapes: trending, range, drifting.** 16.4m's
four-state discussion is superseded.

**TWO FACTS ABOUT THE SWEEP AXIS, both of which change what could be swept.**

**A bounded lookback window does nothing.** Capping swing history at L bars and
sweeping L from 28 to 200 moves the shares by under 0.001 past L=40 — trending
.054/.056/.056 and residual .025/.009/.009 at L=28/40/200. The sequence rule
consults only the **last two** confirmed swings per side, and at a narrow swing
width those sit ~12 bars apart, so a 200-bar cap and a 40-bar cap see the
identical pair. Longer windows do contain more swings; the rule never looks at
them.

**So the horizon knob is the swing width, and it is an integer — the lookback is
quantised.** Achievable medians are 12, 18, 24, 29, 35, 41, 46… bars, not every
integer day. Every N from 2 to 40 is swept, spanning 12 to 227 bars, each row
labelled with its measured lookback.

**COVERAGE ACROSS THE SWEEP** (IS, selected rows):

| N | days | trending | range | drifting | residual | sep | corrected | range runs |
|---|---|---|---|---|---|---|---|---|
| 2 | 12 | 0.115 | 0.637 | 0.247 | 0.017 | 0.523 | +0.002 | 26 |
| 4 | 24 | 0.181 | 0.599 | 0.219 | 0.016 | 0.550 | +0.006 | 20 |
| **6** | **35** | **0.208** | **0.604** | **0.188** | **0.016** | **0.560** | **+0.020** | 22 |
| 8 | 46 | 0.212 | 0.608 | 0.179 | 0.017 | 0.548 | +0.004 | 24 |
| 24 | 132 | 0.240 | 0.611 | 0.149 | 0.048 | — | — | 48 |
| 40 | 227 | 0.256 | 0.608 | 0.135 | 0.082 | — | — | 64 |

**DOES CHOP IMPROVE, SHRINK OR HOLD WHILE TREND GROWS?** Over the full sweep:

- trending **GROWS**, 0.115 → 0.256
- drifting **SHRINKS**, 0.247 → 0.135
- range **HOLDS STEADY**, 0.637 → 0.608

But **range episodes lengthen 2.5×, 26 → 64 bars**, while its share barely moves.
That is the answer to "a three-month range is a stronger chop reading": the long
window does not find *more* chop, it finds the *same* chop in longer, readable
episodes. Trending grows and drifting is what it takes from — the trade is
trend-against-drift, not trend-against-chop.

**SELECTION on IS**, pre-specified: residual ≤2%, every shape ≥10%, then the
highest null-corrected separation. Nine of 39 windows meet the coverage bar
(N=2–10), and **all nine have positive corrected separation** — a plateau, not a
spike. Neighbourhood: +0.006 / +0.015 / **+0.020** / +0.012 / +0.004 across
N=4–8. **Chosen: N=6, lookback 35 bars.**

**HOLDOUT, READ ONCE, 120 draws:**

| trending | range | drifting | residual | sep | surrogate | corrected | p |
|---|---|---|---|---|---|---|---|
| 0.186 | 0.620 | 0.195 | **0.000** | 0.519 | 0.538 ± 0.014 | **−0.019** | 0.901 |

**Coverage is fixed; separation is not.** Zero residual, every shape above 18.6%,
trending at 18.6% instead of 2.9% — the vocabulary now works. But the separation
still sits below its own surrogate out of sample, exactly as it did at every
other setting tried since 16.4b.

**SHIPPED, and now adjustable.** `layer1_states.csv` carries a **shape ribbon** —
`shape_12`, `shape` (=35), `shape_132` — the direct analogue of
`state_7/28/128`. Suffixes are the measured median lookback, not the swing width.
Coverage 0.998 / 0.999 / 0.980. Both self-assertions still pass on all 191,940
pair-days. For a daily entry held for weeks, `shape` at 35 bars is the base and
`shape_132` is the multi-month read.

**Points 1 and 2 stand as answered in 16.4m**: the shape column previously used
no settable window at all (event-driven, median 35 bars at N=5) — that is now
fixed and exposed as the ribbon above. The old-vs-new battery is in 16.4m; its
headline is unchanged: the new nine-state is the first classifier here with
positive corrected shape separation on IS, it does not beat activity-alone, and
the merge is about the max of its parts.

**Queued in NEXT_WORK.md**: SHAPE_MEASUREMENTS.md — failed swings (partly built,
needs rescoring as present-tense), retracement depth, swing spacing, cross-pair.

### 16.4o THE SHIPPED SHAPE READ: a continuous score, cut at terciles

**Option B.** A continuous trend-versus-range score, cut at IS terciles, so every
bar lands somewhere. Three shapes, nine states, no residual, no fourth category.
`shapescore.py`. This supersedes the gated version in 16.4m-n.

**The structural information is kept, as readings rather than gates.** A gate
discards everything except which side a bar fell on; a score keeps the distance.

| component | what it measures |
|---|---|
| `seq` | swing sequence, **signed and summed so it cancels** — a higher high with a lower low nets to nothing, which is the distinction the gate existed to make and the one thing that had to survive |
| `bound` | distance outside the confirmed band, or depth inside it, in vol units, continuous through zero |
| `hold` | break-and-hold: mean distance beyond the boundary over the last 10 bars |
| `pull` | 1 − retracement from the running extreme as a fraction of the impulse |

**Equal weights, on purpose.** Each is standardised on IS and the four are summed
unweighted. Fitting weights would be a four-parameter search against a target,
and the target here is a description, not an outcome — there is nothing
legitimate to fit them to.

**IS SWEEP, N = 2..40:**

| N | days | trending | drifting | range | sep | surr | corrected | run | pairs + |
|---|---|---|---|---|---|---|---|---|---|
| 2 | 12 | 0.308 | 0.327 | 0.365 | 0.683 | 0.714 | −0.031 | 16 | 9/28 |
| 6 | 35 | 0.289 | 0.379 | 0.331 | 0.635 | 0.674 | −0.039 | 14 | 5/28 |
| 13 | 74 | 0.284 | 0.388 | 0.328 | 0.433 | 0.466 | −0.033 | 15 | 9/28 |
| 18 | 101 | 0.283 | 0.386 | 0.331 | 0.370 | 0.370 | −0.000 | 17 | 14/28 |
| 22 | 121 | 0.286 | 0.384 | 0.330 | 0.318 | 0.315 | +0.003 | 18 | 15/28 |
| **26** | **144** | 0.285 | 0.384 | 0.331 | 0.282 | 0.268 | **+0.014** | 18 | 13/28 |
| 30 | 167 | 0.282 | 0.388 | 0.330 | 0.240 | 0.236 | +0.004 | 19 | 15/28 |
| 40 | 227 | 0.284 | 0.390 | 0.326 | 0.192 | 0.181 | +0.011 | 21 | 13/28 |

**17 of 39 windows are positive, and every one of them is past N=18.** Short
windows uniformly negative, long windows uniformly positive — a plateau with a
clean boundary, not a spike. Neighbourhood at the pick: +0.007 / +0.011 /
**+0.014** / +0.010 / +0.012 across N=24–28.

Note the raw separation FALLS as the window lengthens (0.683 → 0.192) while the
corrected value RISES. The surrogate falls faster. That is the whole reason for
correcting.

**HOLDOUT, READ ONCE, N=26, 120 draws:**

| trending | drifting | range | residual | sep | surrogate | corrected | p |
|---|---|---|---|---|---|---|---|
| 0.225 | 0.395 | 0.380 | **0.000** | 0.275 | 0.266 ± 0.023 | **+0.009** | 0.314 |

**The first positive holdout corrected separation in this project** — every gated
version was negative (−0.019 at 16.4n, −0.051 to −0.066 at 16.4d). But +0.009 at
p=0.314 is inside the noise. The sign flipped; the magnitude did not arrive.

**WHICH WINDOW FOR DAILY ENTRY HELD FOR WEEKS.** The state has to outlast the
hold or it is not describing it.

| N | days | trend runs | range runs | corrected |
|---|---|---|---|---|
| 6 | 35 | 19 | 14 | −0.039 |
| 13 | 74 | 21 | 15 | −0.033 |
| 18 | 101 | 27 | 17 | −0.000 |
| **26** | **144** | **25** | **19** | **+0.014** |
| 30 | 167 | 30 | 18 | +0.004 |

**N=26 is the answer**: trend episodes of ~25 bars (five weeks) and range
episodes of ~19 (four weeks) both outlast a multi-week hold, and it is inside the
only region of the sweep with positive corrected separation. Anything under N=18
gives episodes shorter than the hold *and* negative corrected separation.

**SHIPPED.** `layer1_states.csv` carries the score at three lookbacks —
`shape_12`, `shape_35`, `shape` (=144) — and `combined` is now a genuine **nine**
states with **no residual**: medium drifting 0.147, medium range 0.144, weak
range 0.139, weak drifting 0.133, strong drifting 0.114, strong range 0.098,
strong trending 0.088, medium trending 0.079, weak trending 0.058. Both
self-assertions still pass on all 191,940 pair-days.

**Per pair at N=26**: 13 of 28 positive, median −0.003. Best CADJPY +0.148,
GBPCAD +0.142, USDJPY +0.125; worst GBPAUD −0.126, AUDNZD −0.124, GBPJPY −0.097.
Still a coin flip pair by pair.

### 16.4p Separation split by state. Drifting is the dead weight.

Every number before this was blended — one figure for the whole classifier, which
cannot tell "both trend and chop separate" from "one carries it". `shapesplit.py`
uses **one-versus-rest, signed**: the state's own mean minus every other state's,
in sd units, per property, per pair, per window. Sweep extended to N=70, a
393-bar lookback, because corrected separation was still climbing at 200.

**COVERAGE IS FLAT ACROSS THE WHOLE SWEEP** — trending 0.283–0.308, drifting
0.327–0.391, range 0.326–0.365 at every window. It is fixed by the tercile cut,
so it carries no information and is a check only.

| | | TRENDING | | | | DRIFTING | | | | RANGE | | |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| N | days | corr | raw | run | diag | corr | raw | run | diag | corr | raw | run |
| 2 | 12 | −0.016 | 0.581 | 18 | .955 | +0.015 | 0.097 | 13 | .941 | −0.032 | 0.442 | 17 |
| 6 | 35 | −0.018 | 0.509 | 19 | .960 | +0.013 | 0.065 | 12 | .936 | −0.043 | 0.403 | 14 |
| 13 | 74 | −0.028 | 0.340 | 21 | .967 | −0.008 | 0.038 | 14 | .943 | −0.015 | 0.282 | 15 |
| 18 | 101 | −0.012 | 0.277 | 27 | .973 | +0.010 | 0.063 | 15 | .949 | **+0.009** | 0.250 | 17 |
| 26 | 144 | −0.003 | 0.204 | 27 | .976 | +0.002 | 0.041 | 16 | .953 | **+0.009** | 0.190 | 18 |
| 34 | 190 | −0.000 | 0.150 | 30 | .979 | −0.004 | 0.024 | 18 | .958 | +0.002 | 0.148 | 18 |
| 44 | 247 | **+0.039** | 0.153 | 33 | .981 | +0.014 | 0.040 | 19 | .962 | −0.008 | 0.109 | 20 |
| 55 | 309 | **+0.058** | 0.148 | 34 | .984 | +0.020 | 0.049 | 21 | .966 | −0.004 | 0.086 | 25 |
| 70 | 393 | **+0.043** | 0.110 | 36 | .986 | +0.021 | 0.049 | 24 | .970 | −0.010 | 0.057 | 28 |

**THE ANSWER TO THE QUESTION: trend and chop both work; the middle is dead
weight.** Raw one-vs-rest at 144 bars is trending 0.204, range 0.190, drifting
**0.041**. Drifting never exceeds 0.10 at any window in the sweep. It is the
middle tercile of a continuous score, so being indistinguishable from average is
what it is *for* — but it should not be read as a third regime, and the blended
number was averaging it in.

**AND THEY WANT DIFFERENT WINDOWS.** Trending corrected is negative until a
~200-bar lookback, turns positive at 247 and peaks **+0.058 at 309 bars**. Range
corrected is positive only in the **101–190 bar band** (+0.009, +0.009, +0.002)
and goes negative beyond it. There is no window where both are positive together;
the best compromise is N=26–34 (144–190 bars) where range is +0.009/+0.002 and
trending is −0.003/−0.000.

**WHICH PROPERTY CARRIES EACH STATE**, at 144 bars, signed:

| state | autocorr | range/path | dir changes | mean crossings |
|---|---|---|---|---|
| trending | +0.007 | **+0.327** | −0.097 | **−0.385** |
| drifting | −0.037 | +0.055 | +0.058 | +0.014 |
| range | +0.033 | **−0.360** | +0.028 | **+0.340** |

Trending and range are near mirror images on path efficiency and oscillation
count. **Autocorrelation carries almost nothing for any state** (+0.007, −0.037,
+0.033) — the work is done by how directly price travels and how often it crosses
its own mean, not by serial dependence in returns. That is worth knowing given
autocorrelation was named as the original gap back in 16.4b.

**THE TRADEOFF.** Trending run length climbs 18 → 36 bars and its diagonal 0.955
→ 0.986 across the sweep. So the windows where trend separation is positive are
the same ones where a trend state lasts **seven weeks and changes on 1.4% of
bars**. Range peaks earlier and cheaper: +0.009 at 101–144 bars with 17–18 bar
runs.

**For an entry held weeks: range is readable at 144 bars, trend is not readable
until 250+, and at 250+ it is arguably too slow to act on.** If the choice has to
be one window, 144 bars buys a working chop read and a trend read at parity with
noise; 309 bars buys the trend read at the cost of a chop read that has gone
negative and trend episodes lasting seven weeks.

**PER PAIR** (corrected): at 144 bars, trending 13 of 28 positive (median
−0.004), drifting 16 of 28 (+0.009), range 15 of 28 (+0.017). At 247 bars,
trending 14 of 28 (−0.002). Still a coin flip pair by pair at every window and
for every state.

### 16.4q LOCKED at 106 bars. And the score is one spread, not three clusters.

**LOCKED: swing width 19, measured lookback 106 bars.** Chosen for 21-bar range
episodes over the last 5% of separation. Per state at that window: trending
sep 0.261 (corrected −0.013, run 27, diag 0.974), range 0.239 (+0.007, run 17,
0.957), drifting 0.062 (+0.011, run 15, 0.950).

**IS THE SCORE THREE CLUSTERS? No.** Four tests, since no single one settles it:

| | n | sd | excess kurtosis | KDE peaks | BIC k=1 | k=2 | k=3 |
|---|---|---|---|---|---|---|---|
| real | 189,341 | 2.498 | **+1.443** | **1 at every bandwidth** | 884,085 | 860,307 | 859,345 |
| surrogate | 189,248 | 2.635 | +3.095 | 1–2 | 903,836 | 869,425 | 868,698 |

- **A single KDE peak at every bandwidth** (0.15 through 0.40).
- **Excess kurtosis +1.443** — leptokurtic. Three well-separated clusters are
  *platykurtic*; the sign is wrong for clusters.
- BIC picks k=3 — **and so does the surrogate**. The extra components are fitting
  skew (+0.930) and tails, not finding groups. The k=2→k=3 gain is 0.11% against
  2.7% for k=1→k=2.
- The tercile cuts sit at −1.312 and +0.488, **0.72 sd apart** — well inside the
  body of one distribution.

**So the boundaries are a decision.** Recorded as such.

**BUT THE QUOTA IS NOT WHAT IT LOOKED LIKE.** `fit_frac` fits the CDF on IS and
applies it unchanged, so holdout shares are free to float — and they do:

| | 2016 | 2019 | 2021 | 2024 | 2026 | spread |
|---|---|---|---|---|---|---|
| trending | 0.221 | 0.168 | 0.319 | **0.147** | 0.306 | 0.173 |
| drifting | 0.419 | 0.418 | 0.359 | 0.410 | 0.335 | 0.118 |
| range | 0.360 | 0.415 | 0.322 | **0.443** | 0.359 | 0.121 |

**It never forces 33/33/33 out of sample.** 2024 reads 14.7% trending and 44.3%
range; 2021 reads 31.9% trending. A fixed raw-level cut at the same thresholds
gives an almost identical yearly spread (0.175 vs 0.173 on trending), so the
choice between quota-style and fixed-level is a level shift, not a change in
responsiveness. Kept as-is.

**`shape_score` is now a column** in `layer1_states.csv` — the raw continuous
value at the base window, before any cut, so Layer 2 can put the boundary
somewhere else without re-deriving anything. Higher is more trending.

**SHIPPED STATE.** Ribbon `shape_35` / `shape` (=106) / `shape_247`, plus
`shape_score`. Holdout shape shares trending 0.223 / drifting 0.410 / range
0.367. `combined` is nine states, min share 0.054, max 0.152. Both self-assertions
pass on all 191,940 pair-days.

### 16.4r TWO_SCORES.md: two axes confirmed, "neither" halved, null still fails

`twoscores.py`. Trend and chop scored independently, classified on the pair.

**FIRST QUESTION — ARE THEY ONE AXIS? No.** Pooled correlation **−0.350**, per
pair −0.207 to −0.467. The project's own decorrelation bar is |r| < 0.70, so they
clear it comfortably. **The premise holds: trend and chop are not opposite ends
of one scale.**

**A CONSTRUCTION ERROR FOUND AND FIXED, and it was mine.** The spec assigns
`hold` (do pullbacks hold above the prior low) to the trend score. Measured, it
behaves as a **chop** component. On IS: `disp` reads range/path **+0.170** and
mean crossings **−0.220**, while `hold` reads **−0.254** and **+0.288** — opposite
sign on both. Summed into one score they cancel, which is why the trend score
first came out at 0.034 while `disp` alone reached 0.088 and `hold` alone 0.147.
Moved to the chop score, **direction confirmed on IS before the holdout was
read.** Effect: trend 0.034 → 0.053, chop 0.074 → 0.124, correlation −0.400 →
−0.350.

**OCCUPANCY, holdout:**

| cell | share | sep | run | diag | autocorr | range/path | dir chg | crossings |
|---|---|---|---|---|---|---|---|---|
| trending | 0.249 | 0.104 | 21 | 0.971 | +0.051 | **+0.134** | −0.003 | **−0.229** |
| ranging | 0.371 | 0.100 | 24 | 0.978 | −0.048 | **−0.143** | +0.015 | **+0.195** |
| trend-in-range | 0.181 | 0.053 | 18 | 0.959 | −0.003 | −0.052 | −0.036 | +0.121 |
| **neither** | **0.199** | 0.065 | 18 | 0.959 | +0.013 | +0.101 | +0.015 | −0.129 |

**The honest "neither" bucket is 19.9% of bars, against 41% in the single-axis
middle tercile.** The design does what it was meant to do — it more than halves
the unclassifiable share. And trending and ranging now show clean mirror-image
signatures on path efficiency and oscillation count, which the single-axis middle
never did.

**BUT NOTHING SURVIVES ITS NULL.** 20 draws:

| | real | surrogate | corrected |
|---|---|---|---|
| trending | 0.104 | 0.150 | **−0.046** |
| ranging | 0.100 | 0.147 | **−0.046** |
| trend-in-range | 0.053 | 0.059 | −0.006 |
| neither | 0.065 | 0.066 | −0.002 |
| trend axis alone | 0.053 | 0.102 | −0.049 |
| chop axis alone | 0.124 | 0.163 | −0.039 |

**AND THE TRADEOFF AGAINST THE SINGLE AXIS IS REAL.** At the same window the
single-axis version separates *better* — trending 0.261, range 0.239 against
0.104 and 0.100 here — but leaves 41% ambiguous. Two scores buy coverage and cost
description. Neither version beats its surrogate, so the choice between them is
about what the vocabulary should look like, not about which describes more.

**JOINT vs SEPARATE CUTS with activity**: 12 cells either way. Separate mean
|sep| 0.063, min share 0.056; joint (weak activity must clear a higher trend bar)
0.061 and 0.040. **Joint cutting does not separate better and costs coverage** —
keep them separate.

**Episode basis**: 74,004 holdout bars → 2,306 episodes, 32.1×.

**Note for the record**: activity remains a distance-travelled proxy. FX is
decentralised and H.10 is close-only; there is no volume anywhere in this work.

### 16.4s The four measurements. One passes test two; the panel test is vacuous.

`measures.py`. All four built, each tested twice, reported separately.

**THE CROSS-PAIR TRAP IS WORSE THAN THE SPEC ASSUMED, and I walked into it
first.** Excluding the pair from its own leg index is not enough. 28 pairs from 8
currencies is a **rank-7 panel**, so every pair is an exact linear combination of
the others — EURGBP minus USDGBP *is* EURUSD. Measured lag-0 correlation against
a leg proxy built from every other pair: **+1.0000**. That is an identity, not a
finding, and no exclusion rule repairs it. **A contemporaneous cross-pair reading
is mathematically vacuous on this panel.**

Rebuilt on a **disjoint proxy** — the 15 pairs sharing *neither* currency, which
carries no algebraic identity:

| lag | −5 | −3 | −1 | 0 | +1 | +3 | +5 |
|---|---|---|---|---|---|---|---|
| r | −0.020 | −0.026 | −0.016 | −0.039 | −0.001 | +0.003 | +0.000 |

Peak |r| is 0.039 at lag 0 and nothing reaches 0.03 elsewhere. **No lead, in
either direction.** The 68%-retention cross-sectional result quoted in
TWO_SCORES.md was from the signal search, not from state classification, and does
not transfer.

**FAILED SWINGS — the surface, extended below the spec's 0.85 floor** because
separation was still climbing at the edge (same standard as 16.4l):

| X \ Y | 0.5 | 0.75 | 1.0 | 1.5 | 2.0 | 3.0 | 4.0 |
|---|---|---|---|---|---|---|---|
| **0.70** | 0.660 | **0.709** | 0.686 | 0.677 | 0.646 | 0.679 | 0.488 |
| 0.75 | 0.613 | 0.665 | 0.651 | 0.637 | 0.639 | 0.650 | 0.454 |
| 0.80 | 0.581 | 0.621 | 0.593 | 0.548 | 0.541 | 0.558 | 0.376 |
| 0.85 | 0.439 | 0.485 | 0.463 | 0.445 | 0.444 | 0.487 | 0.359 |
| 0.90 | 0.288 | 0.322 | 0.322 | 0.295 | 0.301 | 0.321 | 0.241 |
| 0.95 | 0.155 | 0.158 | 0.131 | 0.126 | 0.137 | 0.210 | 0.171 |
| 0.99 | 0.066 | 0.051 | 0.057 | 0.093 | 0.093 | 0.115 | 0.084 |

**18 of 70 cells above 0.5, and the gradient is monotone in X** — a broad ramp,
not a spike. But the ranking is the opposite of the premise: separation is
highest at the *loosest* approach threshold. At X=0.70 "approaching the prior
extreme" means reaching 70% of the band, which is most of the time — so what the
measurement is really counting is oscillation inside the band, not defended
levels. Honest reading: it works, and not for the stated reason.

**TEST ONE and TEST TWO, holdout:**

| measurement | sep IS | sep OOS | incremental | surrogate | corrected | lead lift | lead excess |
|---|---|---|---|---|---|---|---|
| retr_last | 0.037 | 0.109 | 0.093 | 0.089 | +0.020 | 0.130 | −0.350 |
| retr_slope | 0.028 | 0.107 | 0.089 | 0.084 | +0.023 | 0.000 | −0.498 |
| retr_rel | 0.070 | 0.103 | 0.069 | 0.085 | +0.018 | 0.000 | −0.433 |
| **space_last** | 0.425 | **0.400** | 0.094 | 0.454 | −0.054 | 0.282 | −0.056 |
| space_slope | 0.319 | 0.321 | 0.118 | 0.315 | +0.006 | 0.144 | −0.193 |
| space_rel | 0.168 | 0.067 | 0.083 | 0.172 | −0.105 | 0.444 | −0.427 |
| fail_count | 0.131 | 0.201 | 0.062 | 0.176 | +0.025 | 0.928 | −0.055 |
| **panel_r2** | 0.248 | 0.080 | 0.079 | 0.122 | −0.042 | **1.341** | **+0.349** |

**Test one**: swing spacing is much the strongest raw descriptor (0.400) but sits
*below* its surrogate — long windows make persistent states and the surrogate
gets there too. The retracement family and `fail_count` are marginally positive
corrected (+0.018 to +0.025). Every incremental value is small but non-zero
(0.062–0.118), so none of them is purely a restatement of the existing scores.

**Test two**: **only `panel_r2` leads** — 1.341 lift against a surrogate of
0.991, excess **+0.349**. Everything else fires at or below chance. Note this is
the one measurement whose *test one* is negative: it leads changes without
describing the present, the exact opposite pattern from the rest, and exactly the
case the spec said not to bury.

**REBUILT SCORES.** Score correlation **−0.350 → −0.017** — adding the
measurements makes trend and chop very nearly orthogonal, which is the design's
own premise finally holding cleanly. Occupancy barely moves (neither 0.199 →
0.214), per-cell separation shifts around without improving (trending 0.104 →
0.088, trend-in-range 0.053 → 0.096), and run lengths lengthen slightly. **The
43% overlap was not a symptom of crude scores** — better scores made the axes
independent and left the overlap where it was.

**ACTIVITY, joint or separate**, on the rebuilt scores: separate 12 cells, mean
|sep| 0.062, min share 0.049; joint 0.068 and 0.043. Joint is marginally better
on separation and worse on coverage — closer than it was in 16.4r but still not a
reason to switch.

### 16.4t Chop is concentrated — on the wrong component. And 'both' is overlap.

`chopmore.py`.

**PART ONE. The four components named as missing are already in the chop score** —
boundary tests, time inside the band, reversion crossings, failed breaks — plus
pullback hold, five in total. So the question is concentration, and that is a
drop-one:

| removed | chop \|sep\| | change |
|---|---|---|
| — (all five) | 0.124 | |
| **hold** | 0.074 | **−0.050** |
| tests | 0.156 | **+0.032** |
| fails | 0.116 | −0.008 |
| inside | 0.123 | −0.001 |
| revert | 0.116 | −0.008 |

**The concern is right and the target is wrong. Chop does lean on one component,
but it is `hold`, not failed swings.** Removing `hold` costs a third of the
score; removing `fails` costs 0.008. And **removing `tests` makes chop better by
+0.032** — the boundary-test count is actively hurting.

That `hold` is load-bearing is worth noting: it is the component I moved from
trend to chop in 16.4r on the evidence of its sign. It turns out to be the thing
holding chop up.

**Three new components added anyway**, since five correlated readings is not
redundancy:

| component | alone | dropping it | r with old chop | corrected |
|---|---|---|---|---|
| `vr_short` variance ratio at lag 5 | **0.286** | −0.000 | −0.082 | −0.036 |
| `hold_ratio` touches that held | 0.033 | +0.006 | +0.699 | −0.044 |
| `width_stab` band-width stability | 0.053 | +0.003 | +0.009 | **+0.023** |

**Adding all three makes the chop score worse: 0.124 → 0.082.** `vr_short` alone
separates at 0.286 — better than the whole five-component score — but it is
essentially uncorrelated with them (−0.082), so summing it in dilutes rather than
reinforces. `hold_ratio` is 0.699 correlated with what is already there and adds
nothing. Only `width_stab` is positive against its own surrogate, and it is weak.

**So chop does not get redundancy by addition here.** The honest options are to
drop `tests`, or to treat `vr_short` as a separate reading rather than a summand.

**PART TWO. The 'both' cell measured 18.1% of holdout bars, not 6.8%.** 257
episodes of 20+ bars.

| cell | n | net move | efficiency | median bars |
|---|---|---|---|---|
| trending | 290 | 0.56 sd | **0.113** | 39 |
| ranging | 376 | 0.80 sd | 0.143 | 50 |
| trend-in-range | 257 | 0.62 sd | **0.154** | 31 |
| neither | 272 | 0.64 sd | 0.138 | 33 |

**All four cells look the same.** A genuine trend-inside-a-range would show a
large net move and high efficiency while still being called chop. Instead
trend-in-range sits at 0.62 sd and 0.154 — indistinguishable from `neither` at
0.64 and 0.138. **It is measurement overlap.**

And the worse finding sitting in that table: **the cell labelled `trending` has
the LOWEST path efficiency of all four (0.113)**, below `ranging` at 0.143. The
trend score is not identifying directional movement.

The ten longest 'both' episodes are mostly flat — GBPNZD 2016-12→2017-06, 118
bars, net move 0.15 sd, efficiency 0.02; EURJPY 2023-08→2024-01, 107 bars, 0.14
sd, 0.02. Two exceptions are real: **USDJPY 2021-12→2022-05, 102 bars, 2.86 sd,
efficiency 0.32** — the actual yen collapse — and EURNZD 2025-07→11 at 1.43 sd.
Most 'both' episodes run ranging → both → ranging, which is what a boundary
artefact looks like, not a distinct regime.

### 16.4u Final settings and the full report. Chop holds, trend does not.

`final.py`. Two decisions, both taken on **in-sample only**, then one holdout read.

**DECISION 1 — chop component set.** 16.4t found that removing `tests` helped,
but measured it on the holdout. Redone on IS: **0.140 → 0.151 without `tests`**.
It holds, so it is adopted. Chop now has four components: `hold`, `fails`,
`inside`, `revert`.

**DECISION 2 — activity, joint or separate.** The earlier tests used a single
arbitrary bump of 0.5; here it is swept.

| bump | cells | IS mean \|sep\| | min share | usable |
|---|---|---|---|---|
| 0.00 (separate) | 12 | 0.062 | 0.049 | 12 |
| 0.25 | 12 | 0.060 | 0.041 | 12 |
| 0.50 | 12 | 0.063 | 0.034 | 12 |
| **0.75** | 12 | **0.064** | 0.026 | 12 |
| 1.00 | 12 | 0.062 | 0.020 | 12 |
| 1.50 | 12 | 0.068 | 0.012 | 11 |

Selection rule, pre-specified: highest IS separation subject to min share ≥ 2%.
That picks **bump = 0.75, the joint cut** — but **it beats the separate cut by
0.002**, which is a tie, and it costs coverage (min share 0.049 → 0.026). 1.50
scores higher still and is excluded for leaving a cell at 1.2%. **Read them as
equivalent**; the joint idea is sound and the data does not care.

**THE TWO AXES, SEPARATELY, NEVER BLENDED:**

| axis | IS \|sep\| | OOS \|sep\| | surrogate | corrected | share | run | diagonal |
|---|---|---|---|---|---|---|---|
| trend | 0.106 | **0.053** | 0.098 | **−0.044** | 0.429 | 28 | 0.980 |
| chop | 0.151 | **0.156** | 0.167 | **−0.011** | 0.555 | 24 | 0.981 |

**Chop is the stronger axis and the only one that holds up out of sample** —
0.151 → 0.156, essentially unchanged, corrected −0.011. **Trend halves**, 0.106 →
0.053, corrected −0.044. That is consistent with 16.4t, where the cell labelled
`trending` had the lowest path efficiency of the four. The trend side is the weak
half of this classifier and the evidence now says so twice, from different
directions.

**THE FULL GRID, 12 cells:**

| | cells | mean \|sep\| | coverage | min share | median run | diagonal |
|---|---|---|---|---|---|---|
| IS | 12 | 0.064 | 0.962 | 0.026 | 12 | 0.935 |
| OOS | 12 | 0.072 | **1.000** | 0.032 | 12 | 0.936 |

Against its own surrogate: 0.072 vs 0.078, **corrected −0.006**.

Per cell on the holdout, the best are `strong trending` (0.105, share 0.109, run
17) and `medium neither` (0.105, share 0.075); the worst are `strong
trend-in-range` and `weak trend-in-range`, both 0.035 — consistent with 16.4t's
finding that the 'both' cell is overlap.

**EPISODE-BASED SIGNIFICANCE.** 74,004 holdout bars are **4,604 episodes**, a
16.1× overstatement. Every significance figure in this report is a surrogate
randomisation, which carries the dependence in full. **No per-bar t-statistic
appears anywhere in it.**

**PER PAIR, holdout, the two axes separate:**

- trend median **0.118**, from CADJPY 0.059 to GBPCAD 0.283
- chop median **0.195**, from CHFJPY 0.048 to EURJPY 0.478

Chop beats trend on the median pair by 65%, the same ordering as the pooled
figures.

**SHIPPED.** `layer1_states.csv` gains `trend_score`, `chop_score`, `shape2`
(the 2×2) and `combined2` (the 12-cell joint grid), alongside everything already
there. Nothing was removed — the single-axis `shape` and nine-state `combined`
stay, because they separate better even though they leave more ambiguous. Holdout
coverage 0.986 / 0.990 / 0.986 / 0.985. Both self-assertions still pass on all
191,940 pair-days.

### 16.4v Per-pair CHARACTER. It is not there, and pairs differ less than noise.

`paircharacter.py`. Not how well the classifier reads each pair (16.4u) — what
each pair **is**.

**A METHODOLOGICAL FAULT HAD TO BE FIXED FIRST, and the first run of this file
was void without it.** `classifier.zfit` z-scores each axis **per pair** —
`v[fit].mean()` on a frame is per column — so every pair's in-sample score is
forced to mean 0, sd 1. Cutting that at a panel threshold hands every pair almost
identical state shares *by construction*, and any cross-pair spread that emerges
is holdout drift, not character. Per-pair z-scoring is right for **classifying**
(each pair judged against its own history) and wrong for **comparing**. This file
standardises **pooled**: one mean and one sd over the whole IS panel.

The fix widens the spread, as it should — trending share range 0.095 → 0.130 —
and changes nothing about the conclusion.

**RANKING, most trending to most ranging** (full sample, pooled z):

| rank | pair | trending | ranging | trendiness |
|---|---|---|---|---|
| 1 | EURUSD | 0.361 | 0.263 | **+0.098** |
| 2 | EURJPY | 0.362 | 0.292 | +0.070 |
| 3 | USDJPY | 0.334 | 0.303 | +0.032 |
| 4 | AUDUSD | 0.323 | 0.293 | +0.030 |
| … | | | | |
| 25 | EURGBP | 0.251 | 0.378 | −0.127 |
| 26 | CADCHF | 0.257 | 0.397 | −0.140 |
| 27 | GBPCHF | 0.232 | 0.406 | −0.173 |
| 28 | GBPCAD | 0.234 | 0.409 | **−0.175** |

**No pair is trend-dominant.** Trending share runs 0.232 to 0.362 — every one of
the 28 sits between 23% and 36%. Only 6 of 28 have positive trendiness and the
largest is +0.098. The panel is range-leaning throughout.

**THE RANKING DOES NOT HOLD ACROSS HALVES:**

| statistic | IS-to-OOS rank correlation |
|---|---|
| share_trending | **+0.002** |
| share_ranging | −0.130 |
| trendiness | **−0.087** |
| med_trending | +0.104 |
| med_ranging | −0.293 |

Individual moves are violent: NZDJPY rank 2 → 23, NZDUSD 4 → 26, NZDCAD 3 → 24,
CHFJPY 24 → 2, GBPNZD 26 → 15.

**AND PAIRS DIFFER LESS THAN SURROGATE PAIRS DO:**

| | real | surrogate |
|---|---|---|
| cross-pair sd of trending share | 0.0337 | **0.0430 ± 0.0061** |
| cross-pair range | 0.130 | **0.180** |
| IS-to-OOS rank correlation | −0.087 | +0.045 ± 0.245 |

p(dispersion) = 1.000, p(rank correlation) = 0.625. **28 sign-surrogate pairs,
which have no character at all, spread wider than the real ones.**

**So the answer is the one you said you also wanted: it is not true.** There is no
structurally trendy set and no structurally choppy set to route on — not on this
classifier. Whatever pair-level differences exist are smaller than noise and do
not persist between halves.

**TRANSITIONS, which do show something.** Pooled, leaving `trending`: **neither
0.454, trend-in-range 0.426, ranging 0.120**. Leaving `ranging`: neither 0.399,
trend-in-range 0.507, trending 0.095. **Direct trend↔range transitions are rare
— about 10-12%.** Pairs pass through an intermediate state almost every time.
Per pair the direct share runs 0.021 to 0.208: most direct are CHFJPY 0.208,
USDJPY 0.204, EURJPY 0.172 — all JPY crosses; least direct GBPCAD 0.021, GBPJPY
0.038.

**Longest runs on record**: trending EURAUD 237, EURCAD 234, USDCAD 227 bars;
ranging GBPCHF 291, CADCHF 258, NZDJPY 245. Median across pairs 148 and 165 bars.

### 16.4w The app rebuilt on the current classifier

**DATA.** `layer1_states.csv` now carries **only the current classifier**:
`trend_score`, `chop_score`, `shape2`, `activity`, `scale_28`, `combined2`,
`settling`, and the four measurements as `m_fail` / `m_retr` / `m_space` /
`m_panel`. Holdout coverage 0.984–1.000 on every column.

Three generations of superseded columns moved to **`results/layer1_legacy.csv`**
— not deleted: the nine-box (`state_7/28/128`, `straight_28`, `tier`, `age_28`),
the single-axis shape score (`shape_35/shape/shape_247/shape_score`) and the
nine-state product built on it (`combined`). Both `export.py` self-assertions now
run against the legacy file and still pass on all 191,940 pair-days.

**FEED.** `appfeed.py` writes **`app_regime.json`**, 9.0 MB, 28 pairs × 6,855
dates: price, shape state as an integer code, both scores as separate series, the
settling weight and all four measurements. Fetched lazily when the Regime tab is
first opened, the same pattern the signals feed already uses. State is an integer
index into a legend and every float is rounded to the fewest digits that survive
at screen resolution — a naive dump was ~30 MB.

**FOUR NEW SCREENS.**

- **Regime** — price coloured by state, pair selector across all 28, window
  selector, the two scores plotted as separate traces so their independence is
  visible, and the four measurements as their own traces. No money metrics
  anywhere on it.
- **Character** — the 28 pairs ranked by trendiness with shares, run lengths and
  longest runs, and the stability verdict stated on the screen rather than left
  to be inferred.
- **Explain** — 14 metrics, each with what it is, how it is calculated, how to
  read it, what it is good for, and **what it is NOT**. That last line carries
  the specific misreading each one invites.
- **Archive** — the index, plus a banner injected at the top of every superseded
  screen saying what it was and why it moved.

**ARCHIVED, NOT DELETED**: the nine-box, timeframe confluence, the detector
ladder, the strategy sweep, and — described in the Archive index — the tier, the
single-axis score and the moving-average lead-time work.

**A FIGURE TO CORRECT.** GBPCHF at 51% trending against EURGBP at 33% does not
appear anywhere in the data. Measured, **GBPCHF is the second-least trending pair
of the 28** at 23.2%, and EURGBP is 25.1%. The full ranking runs 23.2% to 36.2%
and no pair reaches 51%. The Character screen shows the measured figures.

### 16.5 DO NOT REBUILD — everything ruled out, with the number

**Trend detection.** Dead by every route tried.
- Panel-wide: no signal predicts whether a pair will trend.
- **Subset agreement** (relaxing gate 4): there *is* real structure below the gate
  — 120 survivors at 21/28 against a null median of 3 — but it is **not
  trend-concentrated**. Carrying pairs correlate **+0.47 with panel sensitivity**
  and **−0.10 with trendiness**. AUDNZD is the trendiest pair and one of the
  weakest carriers. A subset rule keyed to trending pairs picks the wrong pairs.
- **Cross-horizon confluence**: `conf_2of4` scores **0.40×** its own null,
  `conf_3of4` 0.76×. Layering persistence and the daily/weekly/monthly filter on
  top made it worse at every step.

**Direction.** 121 constructions at chance against a signed target. Monotonicity
collapses 0.944 → 0.363, sign-holds 0.975 → 0.339, and per-pair direction
persistence is **0.479 — below a coin flip**. The existing survivors are
direction-blind *by construction*: they were selected against an absolute-value
target. The up/down asymmetry does **not** replicate — up-moves measured straighter
(0.2252 vs 0.2200), and down-straighter held on only 12 of 28 pairs.

**Per-pair normalisation.** Provably null, not empirically null. The scorer ranks
the signal *within each pair* before quintiling, so **any strictly-monotone
per-pair transform leaves every statistic identical to the digit**. Confirmed on
three features. Normalising the *target* affinely is null on agreement for the same
reason (the constants cancel out of the sign), though pooled effect and
monotonicity do move. Only normalising *components before combining* changes
anything.

**Carry / rate differentials.** All 29 constructions transfer; retention **50.0%**
against a 60.6% price baseline — a coin flip. Nothing clears the gauntlet. The
data is built and committed (`data/rates2y.csv`, `data/carry28.csv`, 21 of 28
pairs, 7 central banks) if anyone wants to ask a different question of it.

**External market data.** 69.3% retention against 60.6%, **z = +1.5, not
significant**, and it rests on three distinct constructions repeated across
correlated series. 0 of 75 clear the gauntlet.

**Duration / state age.** See 16.3 — the entire hazard curve is reproduced by a
vol-clustering surrogate.

**The estimator does not inform trade management.** Task 3, 26,833 entries, no exit
rule: bars to peak 9.9 vs 10.1 (t = +1.2), giveback 108% vs 109%, still onside at
20 bars 47% vs 48%. Terciles and quintiles both. What differs between regimes is
**scale, not shape** — chop has larger MFE *and* larger MAE, because chop is more
volatile. Normalise by move size and the profile is identical.

### 16.6 Traps that cost time — read before writing a new feature

**A circular-shift null does not catch look-ahead.** `ACTIONABLE.md` defined
persistence from *forward* readings, which makes it a function of the target. Built
that way it scores **OOS effect 0.2460 at t = 190 with all 28 pairs agreeing** —
ten times the best real survivor. Shifting the target destroys the leaked
alignment, so the null reads ~0 and the ratio comes out around **40×**. The null
*certifies* the leak. Nulls test selection inflation; only construction discipline
tests look-ahead.

**Effect sizes are not comparable across targets.** Raw spreads are in the target's
own units. Divide by the target's sd first: eff_abs 0.146, signed 0.028, range_vol
0.160, path_vol 0.115.

**Excursion spreads are not comparable across bin counts.** Nine bins spread wider
than three by construction. The nine-state grid gives 0.0327 at 9 bins; the forward
composite gives 0.0284 at 3 bins but **0.0401 at 9**. Like for like the forward
composite separates excursion **23% better** and remains the strongest result in
the project.

**Binary rules cannot go through the quintile scorer.** `pd.qcut` needs five
distinct values and returns `None`, which silently dropped every confluence feature
from a whole run. And **NaN is truthy** — a gauntlet column built on it displayed
PASS for every rule.

**`(mfe − final)/mfe` per row explodes** when MFE is near zero. Its mean reported
6.05 vs 11.32 between regimes, which is pure divisor noise; the true figures were
108% vs 109%. Use absolute giveback per row and form the proportion at group level.

**Window = normalisation window is degenerate.** See 16.2.

**`x.rank(pct=True)` ranks against the whole sample.** Used for the tercile cuts in
`classifier.py`, `ribbon.py` and `ninestate.py`, it meant a bar's label depended on
data after it and the cut points were learned partly on the holdout. The tell was a
refit stability of **exactly 100.0%** — refitting changed nothing because nothing
was being fitted. Fixed with `classifier.fit_frac`, which builds the empirical CDF
on the fit window and applies it unchanged; stability is now 97.1%. The one place
whole-sample ranking is legitimate is `ribbon.truth()`, the non-causal reference
the reaction lag is measured against, which is never a feature.

**One library signal is broken.** `zs_coexmax_D375`: `coexmax_D375` takes 15
distinct values, is unchanged on 94% of days, and its 120-day rolling sd is
*exactly zero on 51.6% of days*, so the z-score is 0/0 across 58.8% of the sample.
Its `zs_`/`ps_` siblings on other near-constant bases deserve the same check.

### 16.7 Open, and not blocked on analysis

- **CI has failed every run since 2026-08-06**, at the `run pipeline` step,
  predating this phase. Seventeen modules added to `pipeline.py` have never
  executed there. The traceback needs a token to read.
- **`results/composite_stats.csv` is stale** (dated 2026-08-05, reports 32
  components against the current 15). `framework.py` is not regenerating it, so
  the composite headline in the app is pre-gate-change.
