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
