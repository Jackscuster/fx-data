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
