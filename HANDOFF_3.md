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
