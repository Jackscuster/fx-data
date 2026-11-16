# LAYER 1 INTERFACE CONTRACT

**2026-11-16.** This is the complete and only surface Layer 2 may read. Layer 2 restarts from scratch and consumes Layer 1 through these files alone. Every number below is quoted from a named file, with the filename beside it.

## 1. The files Layer 2 may read

| path | producer | what it is | rows | pairs | span |
|---|---|---|--:|--:|---|
| `results/layer1_states.csv` | `code/export.py` | THE interface: shape2, activity, both scores, scale, the four mechanism reads | 171920 | 28 | 2002-12-19..2026-08-14 |
| `results/layer1_trend_quality_series.csv` | `code/layer1close.py --stage quality` | the trend quality flag as a daily series (high/low confidence on trending bars) | 168692 | 28 | 2003-02-28..2026-08-14 |
| `results/crisis_detectors.csv` | `code/crisis.py` | the acute detectors with calendar recall, lift and lag | 5 |  | .. |
| `results/crisis_events.csv` | `code/crisis.py` | per detector per event: caught and lag, the daily firing record | 250 |  | 2003-09-20..2026-07-31 |
| `results/crisis_direction.csv` | `code/crisis.py` | per event per pair behaviour during the crisis window | 525 | 28 | .. |
| `results/move_coverage.csv` | `code/move.py` | the MOVE witness: coverage and overlap with the acute detector | 1 |  | .. |
| `results/nine_tiers.csv` | `code/ninestate.py` | activity tiers and the nine-state grid | 6201 |  | .. |
| `results/twoscores.csv` | `code/twoscores.py` | the two axes, raw and continuous | 8 |  | .. |
| `results/measures_test1.csv` | `code/measures.py` | the measurement series: separation, surrogate, corrected, lead | 8 |  | .. |
| `results/pair_character.csv` | `code/paircharacter.py` | per-pair character | 28 | 28 | .. |
| `results/pair_character_blocks.csv` | `code/paircharacter.py` | per-pair character by block -- whether it is stable | 84 | 28 | .. |
| `results/run_lengths.csv` | `code/duration.py` | state run lengths by generation and block | 3479 | 29 | .. |
| `results/duration_stats.csv` | `code/duration.py` | duration, hazard and excursion statistics | 4 |  | .. |
| `results/state_correlation.csv` | `code/statecorr.py` | shared state across pairs -- the shared-bet / N_eff read | 756 |  | .. |
| `results/state_correlation_summary.csv` | `code/statecorr.py` | the same, summarised per pair | 2 |  | .. |
| `results/witness_validation_2026-11-15.csv` | `code/witness.py` | witnesses 2 and 3 AS MEASURED -- REJECTED, not consumable: see HANDOFF 0k | 9 |  | .. |

Anything not on this list is working material, not interface. `results/layer1_interface_manifest_2026-11-16.csv` carries the md5 and build date of each file.

## 2. Columns, in plain English

### `results/layer1_states.csv` — the live states

| column | meaning |
|---|---|
| `date` | the bar the reading applies to. OANDA 17:00 New York close. |
| `pair` | one of the 28 G8 pairs. |
| `trend_score` | the TREND axis, raw and continuous. Higher means straighter. It does NOT say which way. |
| `chop_score` | the CHOP axis, raw and continuous. Higher means more range-bound. |
| `shape2` | the 2x2 label: `trending`, `ranging`, `trend-in-range`, `neither`. Empty during warm-up. |
| `activity` | `weak` / `medium` / `strong` — how much the pair is moving, cut jointly with shape. |
| `scale_28` | the raw scale measure the activity tier is cut from. |
| `combined2` | `<activity> <shape2>`, the twelve-cell product. |
| `settling` | the pair is inside the confirmation delay after a state change. |
| `m_fail`, `m_retr`, `m_space`, `m_panel` | the four mechanism reads behind the label. |
| `sample` | `is` (tuning, < 2016), `holdout` (2016-2020), `sealed` (2021+, applied never measured). |

### `results/layer1_trend_quality_series.csv` — the confidence flag on a trending label

| column | meaning |
|---|---|
| `date`, `pair` | as above, aligned one-to-one with the states file. |
| `shape2` | repeated from the states file so the flag can be read standalone. |
| `trending` | true where `shape2 == trending`. The flag means nothing on any other label. |
| `quality_reading` | the currency-leg strength gap: how far apart the two currencies of the pair are moving against the basket of the other seven, over the trailing 106 bars, in tuning-window vol units. |
| `quality_tag` | `high` or `low` at the tuning-window cut; empty off trending bars and during warm-up. |
| `trend_episode_id` | groups the bars of one trending run, so a consumer can count episodes rather than bars. |

## 3. The three rules that are not negotiable

**3.1 One-bar lag.** Every value dated `t` is computable from bars through `t-1`. A row dated D is safe to act on at D's close. Do not shift it again and do not shift it back. (`results/layer1_states.csv` header; `layer1_trend_quality_series.txt`.)

**3.2 2021 onward is SEALED.** The cuts were fitted on < 2016 and confirmed once on 2016-2020. Rows from 2021 are produced with the same cuts and are never measured — they carry `sample=sealed`. The public loaders refuse to serve them without an explicit, logged flag (`l2sweep.load_pair`, `l2route.load_states`, audit item 10).

**3.3 Layer 2 never modifies, refits or retunes Layer 1.** No re-cutting a threshold, no re-fitting a score, no "small adjustment" to a label. If a defect is found, report it back and stop using the affected column — do not repair it downstream. A silent downstream repair makes the two layers disagree and neither can then be audited.

## 4. Confidence tiers — how much to trust each label

Ordered by how well each label survived its own tests. This ordering is the single most useful thing Layer 1 has to say.

| label | confidence | what the evidence says |
|---|---|---|
| `ranging` | **strongest** | The chop axis is the one that holds up: separation corrected +0.035 on the 5pm build (`results/layer1_summary.csv`, HANDOFF 0a check B). Chop slices were the only positive per-slice books in the Layer 2 blind round (A-chop +0.63, B-chop +0.52; `results/refit_books_blind2.csv`). |
| `trending` + `quality_tag=high` | **weak, graded** | Trending labels are unreliable on their own; the flag grades them. Holdout episode true-trend rate 59.8% (n=92) for high against n/a for low (`results/layer1_trend_quality_series.txt`). The flag cleared a 200-draw re-derive null at p=0.01 sign / 0.00 permutation, AUC 0.609 (`results/trend_quality_verdict_2026-11-11.csv`). |
| `trending` + `quality_tag=low` | **lowest of the trending labels** | Same caveats, worse base rate. |
| `trend-in-range`, `neither` | **low** | Residual cells. No construction has been validated on them. |

**The trending label's two measured defects, so Layer 2 can design around them** (`results/trend_anatomy_report_2026-11-10.txt`):

- **~50% of labelled trending episodes are directionless** (true-trend share 50.1% tuning, 44.3% holdout), and the trend score itself cannot tell which — on the holdout the FALSE episodes score higher (0.494) than the true ones (0.329).
- **The label confirms a median 24 bars late**, with 56-57% of the leg's move already spent, against a median 23-bar episode. Routed trend P&L concentrates in the first third of an episode (60% of the A/B book's R), which is exactly the part the label is too late to catch.

## 5. Crisis

The crisis witness set is **the acute detector plus MOVE**, and nothing else (`results/witness_incremental_2026-11-15.csv`, HANDOFF 0k).

| witness | events caught | recall | lift | median lag |
|---|--:|--:|--:|--:|
| acute (maxabsmove) | 31 of 39 | 0.795 | 15.0x | 0 days |
| MOVE (relative level) | 8 of 39 | 0.205 | 4.9x | 1 days |

Validated on the 39 news-dated events of `code/events.py` inside the panel window, on a FORWARD-ONLY window from the event date to +15 days that never opens before the event (`results/witness_validation_2026-11-15.csv`). Panel turbulence and Roll illiquidity were measured and REJECTED: neither caught any of the 7 events the acute detector misses, overlap 1.000 (HANDOFF 0k). Their series stay in the repo as measured evidence and must not be consumed as witnesses.

## 6. What Layer 1 does NOT provide

- **No prediction.** Every reading is present tense: what the pair is doing now, from bars through t-1. Nothing here forecasts the next move, and the crisis witnesses confirm rather than anticipate (median lag 0-1 days AFTER the event).
- **No direction.** `trend_score` says how straight, never which way. There is no long/short content anywhere in Layer 1.
- **No money metrics.** No returns, no PnL, no Sharpe, no sizing. Every money number in this repo belongs to Layer 2 and was produced by Layer 2 code.
- **No entry or exit timing.** The label tells you the state, not when to act inside it — and per section 4 it is systematically late on trends.
- **No tradeable universe opinion.** Pair character (`results/paircharacter.csv`) describes behaviour; it does not rank pairs for trading.

## 7. Reporting a defect

Open the finding against the producer script named in section 1, quote the file and the rows, and leave Layer 1 untouched until it is fixed at source and re-exported. The audit that certifies this interface is `results/LAYER1_CLOSEOUT_AUDIT.csv`; the pre-flight that guards the invariants is `python3 code/preflight.py` (27 checks).
