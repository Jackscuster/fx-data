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


## Gate 3 — `gate3_verdicts.csv`, `gate3_passers.csv`, `gate3_index.json`

| file | what it holds |
|---|---|
| `gate3_verdicts.csv` | EVERY one of the 5,135 A and B crossers, verdict and full metrics, kept whatever the verdict |
| `gate3_passers.csv` | the 170 passers, ranked by the co-equal rule |
| `gate3_index.json` | per mode/slice counts and top 20, read by the app's Gate 3 panel |
| `gate3_bank/` | per-shard banking, written as each strategy completes so a stop loses one strategy |

Every figure is on the CRISIS-EXCLUDED blind book. `luck_floor_p95` is that
strategy's OWN p95 under 5,000 episode-level sign randomisations of its own
trades; `margin_vs_floor_R` is expectancy minus that floor;
`net_of_structure_R` is expectancy minus that strategy's own null MEAN.
`max_dd_frac` is drawdown as a fraction of the strategy's own gross profit —
fixed-R sizing has no compounding equity base to take a percentage of.

Regenerate: `python code/l2gate3.py` (resumable; ~2.5 h on one core).
