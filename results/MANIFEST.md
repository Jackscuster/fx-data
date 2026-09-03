# results/ MANIFEST

What each classifier output actually contains. Written by
`code/persist.py`. **Nothing in results/ is ever deleted or
overwritten** — superseded work stays readable under its original
name, and this file says what that name means.

## The four generations

| file | source column | shape | what it is |
|---|---|---|---|
| `states_g2_structural12.csv` | `restored from git f597f23` | 6916 x 28 | Structural generation 2: four shapes INCLUDING `broken` crossed with activity = 12 cells. NOT reproducible from current code; restored verbatim from history. |
| `states_g1_ninebox.csv` | `state_28` | 6875 x 28 | Nine-box, generation 1. Straightness x scale terciles at a 28-bar window. The 7 and 128 legs are in layer1_legacy.csv as state_7 and state_128. |
| `states_g3_shapescore9.csv` | `shape` | 6875 x 28 | Shape score, generation 3. One continuous trend-versus-range score cut at in-sample terciles into three shapes. Separates better than g4 (0.261 vs 0.104 on trending) but leaves 41% of days in an ambiguous middle. |
| `states_g4_twoscore4.csv` | `shape2` | 6875 x 28 | Two-score, generation 4, CURRENT. Trend and chop scored independently and classified on the pair: trending / ranging / trend-in-range / neither. The ambiguous share falls to 20%. |
| `states_g4_twoscore12.csv` | `combined2` | 6875 x 28 | Two-score crossed with activity, generation 4, CURRENT. Twelve cells, activity cut jointly with a 0.75 bump. |

## Older names that do not say what they hold

| file | what it ACTUALLY contains | superseded by |
|---|---|---|
| `nine_states.csv` | A **9-row summary table** of the generation-1 nine-box states — share, median run length and run count. It is NOT per-day labels and it does NOT hold four shape states. | `run_lengths.csv` for run statistics on every generation |
| `nine_tiers.csv` | Per-day tier labels for generation 1 — which of the three ribbon windows disagreed. Permutation p=0.257, never routed on. | nothing; the tier was dropped |
| `combined_states.csv` | Per-day generation-2 labels, wide format, 4 shapes including `broken` crossed with activity. | `states_g2_structural12.csv`, same data, named for its generation |
| `structure_states.csv` | Per-day generation-2 SHAPE only, before the activity cross. | `states_g2_structural12.csv` |
| `shape3_states.csv` | Per-day three-shape labels from the GATED version of generation 3, before it was replaced by the continuous score. | `states_g3_shapescore9.csv` |
| `layer1_states.csv` | The CURRENT interface — generation 4 only. | — |
| `layer1_legacy.csv` | Generations 1–3 as columns, kept so no earlier read is lost. | — |

## Reading any generation

```python
w = pd.read_csv('results/states_g4_twoscore4.csv',
                index_col=0, parse_dates=True)   # dates x pairs
```

Every value is already lagged one bar. Do not shift it again.


## Portfolio preview — `portfolio_preview.json` / `.csv` / `portfolio_corr.csv`

**PREVIEW, never a gate 4 result.** The crisis-excluded top 10 merged onto one
calendar at equal risk weight (1/N), normalised so the combined book risks the
same 1 R per trade as any single strategy. Gate 4 replaces this with real
weighting and the drop-one test.

| file | what it holds |
|---|---|
| `portfolio_preview.json` | the combined equity curve and the metric block; read by the app's Trades tab |
| `portfolio_preview.csv` | the same metrics, crisis-excluded and all-in side by side |
| `portfolio_corr.csv` | the 10x10 cross-strategy correlation of daily R |

R is booked on the EXIT date; holding overlap uses the entry-to-exit span. The
two are deliberately different and should not be reconciled.

Regenerate with `python code/l2portfolio.py`.


## Portfolio preview, top 20 — `portfolio_preview_top20.*`

Same method as the top-10 preview: pure overlay, equal risk weight 1/N,
normalised to 1 R per trade. **Both previews are kept.** `portfolio_preview.json`
is the top 10; `portfolio_preview_top20.json` is the top 20; the app draws both
curves on one shared scale.

`portfolio_corr_top20.csv` is the 20x20 daily-R correlation. Three pairs exceed
0.30 crisis-excluded (5&10 at 0.633, 2&12 at 0.387, 11&15 at 0.382). The ALL-IN
matrix reaches 0.963 — a pair that is near-identical in crisis windows only, and
therefore invisible in the crisis-excluded view.

Regenerate with `python code/l2portfolio.py 20`.


## Book size sweep — `portfolio_sweep_10_20.csv`

Every N from 10 to 20 under the identical preview method, crisis-excluded and
all-in (22 rows). Columns: total_R, avg_annual_R, max_dd_R, sortino, sharpe,
calmar, worst_month_R, pct_2plus, max_sim, mean_corr, max_corr.

`portfolio_preview_top13.*` is the ADOPTED preview book — the return peak and
the balance point under the co-equal rule. All three previews are kept (10, 13,
20) and the app draws all three curves on one shared scale.

Regenerate: `python code/l2portfolio.py 13`


## Gate 2 by mode and slice

`modes_index.json` is what the app reads: mode -> slice -> {status, headline,
top 20 cards}. `modes_status.json` is the hand-set status for each of the six
slots and is the ONLY source of `running` / `queued` — status is never inferred
from a missing file.

| file | what it holds |
|---|---|
| `gate2_tuned_mode<M>[_<slice>].csv` | the tuner's own output, one row per combination |
| `gate2_crisis_split_mode<M>[_<slice>]_all.csv` | crisis split over every crosser |
| `gate2_mode<M>[_<slice>]_leaderboard.csv` | the co-equal ranking, crisis-excluded |
| `gate2_mode<M>[_<slice>]_leaderboard_clean.csv` | top 60 re-ranked on clean_R |
| `trades_index[_mode<M>_<slice>].json` | trade bundles for the charts |

Mode B keeps its ORIGINAL unsuffixed names (`gate2_modeB_leaderboard.csv`,
`trades_index.json`) so nothing pointing at them breaks. Every other mode/slice
is suffixed and sits beside them.

Regenerate, in order:
```
python code/l2crisis_all.py --mode A --slice trend --src results/gate2_tuned_modeA_trend.csv
python code/l2rank.py --mode A --slice trend --clean     # verifies against B first
python code/l2deliver.py --mode A --slice trend --top 10
python code/l2modes.py
```


## Book-size sweeps beyond mode B — `portfolio_sweep_*.csv`

| file | pool swept |
|---|---|
| `portfolio_sweep_10_20.csv` | mode B, N 10..20 (the original) |
| `portfolio_sweep_modeA_trend.csv` | mode A trend only, N 5..25 |
| `portfolio_sweep_combined_AB.csv` | A-trend + B pooled and RE-RANKED, N 5..25 |

`gate2_combined_AB_leaderboard.csv` is the pooled list after re-ranking, with
`src_mode` / `src_label` / `src_rank` recording where each row came from and
what it ranked in its own mode.

`portfolio_preview_<tag>.json` holds the winning N's curve and metric block and
is what the app draws; `mix` records the A/B split of that book.

Mode A is TREND-ONLY until its chop slice finishes. `code/l2chopfinish.sh`
waits for the 57th chop chunk and redoes the chop pipeline and both sweeps.

Regenerate:
```
python code/l2sweepn.py --lb results/gate2_modeA_trend_leaderboard.csv \
       --slice trend --tag modeA_trend --lo 5 --hi 25
python code/l2sweepn.py --combine --lo 5 --hi 25
```


## The graft — `portfolio_preview_B13_plusA2.*`

Mode B's N=13 sweet-spot book with mode A-trend's ranks 1 and 2 added: the
EXACT 15, not a re-ranked pool. Same overlay math as every other preview.
`mix` in the JSON records 13 B / 2 A. Regenerate: `python code/l2graft.py`.


## Inverse candidate screen — `gate2_inverse_*.csv`

| file | what it holds |
|---|---|
| `gate2_inverse_windows.csv` | EVERY window-tested combination, pass or fail, with W1/W2/W3 expectancy, trade count and PF |
| `gate2_inverse_screen.csv` | the 670 candidates only, ranked by worst-window margin below the floor |

The windows file is written pass or fail deliberately: a screen that reports
only its survivors cannot be audited when it returns zero, which is exactly the
hole the first run fell into.

W1 and W2 are scored with `ip1`/`risk1`, W3 with `ip2`/`risk` — each window only
with parameters that never saw it. Mode B trend never banked `ip1`/`risk1` and is
reported as not-screenable.

Regenerate: `python code/l2inverse.py --jobs 1` (~2.5 h on one core).


## Mode A complete — pooled books

`gate2_modeA_all_leaderboard.csv` pools A-trend and A-chop and re-ranks;
`portfolio_sweep_modeA_all.csv` sweeps it. `gate2_combined_AB_leaderboard.csv`
now pools A-trend, A-chop AND B — the earlier version silently excluded A-chop.

Regenerate: `python code/l2sweepn.py --pool-a` and `--combine`.

### MODE C BATCH 1 — 2026-09-03

| | |
|---|---|
| combinations processed | 2,222 total, 2,222 new this batch |
| crossing the gate 2 label | **246 (11.07%)**, 246 new |
| best crosser to date | `aroon x coppock_curve x waddah_attar_explosion x fantail_vma` — 97 blind trades, **47.69 R**, Sortino 46.64 |
| C measured cost | **247.4 s/combination** (cumulative average) |
| progress | 2,222 of 716,903 combinations (0.31%) |
| projected finish | **2027-04-09** (218 days left at 9 workers) |
| graft challenge | **THE BOOK MOVED** — was N=15 {'B': 13, 'A': 2} at 81.39 R, now N=18 {'B': 15, 'A': 3} at 79.55 R |
