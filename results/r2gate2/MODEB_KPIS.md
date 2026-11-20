# MODE B KPIs — all 273,780 strategies, tuned honestly, traded years 2016–2020 stitched

Source: `results/r2gate2/modeB_daily_full_*_*_*.npz` (daily series, trade-year days only, one year per walk-forward step, stitched 2016→2020) and `results/r2gate2/modeB_books_full.csv` (trade-level PF, win rate, DIP95, retention, FIT). Generated 2026-11-19 22:21 by `code/l2r2kpis.py` — every number read back out of those files, nothing typed in by hand. Numbers CSV beside this file: `modeB_kpis_stitched_2016-2020.csv`.

Team 1 = 3.6% dip / 3.6% day budget (day zero). Team 2 = 5.4% dip / 3.6% day (after the +6% cushion). Scale set on the build years only. Everyone trades, equal weight, netted, costs charged (cost_table_h22.csv, R units), one-bar lag, 2021+ sealed.


**Scale-invariant rows** — Sharpe, Sortino, Calmar, profit factor, win rate, retention and FIT — are equal in both tables by construction: team 2 is team 1 times a constant.


### TEAM 1

| KPI | ALWAYS-ON | ROUTED (chop RANGING + trend TRENDING) | CHOP ROUTED + TREND UNGATED | CHOP ROUTED + TREND NOT-RANGING |
|---|---|---|---|---|
| median year | -0.69% | -1.45% | -0.59% | -1.47% |
| average year | -1.44% | -1.26% | -0.98% | -1.25% |
| worst year | -4.22% | -2.06% | -2.33% | -2.57% |
| best year | 0.49% | 0.22% | 0.35% | -0.33% |
| total 2016-2020 | -7.18% | -6.29% | -4.90% | -6.23% |
| CAGR | -1.44% | -1.26% | -0.98% | -1.25% |
| worst day | -0.88% | -0.57% | -0.60% | -0.61% |
| max drawdown | -8.55% | -7.19% | -6.08% | -7.78% |
| DIP95 (worst step) | 5.65% | 3.91% | 3.74% | 4.36% |
| Sharpe | -0.71 | -0.86 | -0.64 | -0.91 |
| Sortino | -0.90 | -1.17 | -0.87 | -1.18 |
| Calmar (total / max DD, the shipped bar) | -0.84 | -0.88 | -0.80 | -0.80 |
| Calmar (CAGR / max DD) | -0.17 | -0.18 | -0.16 | -0.16 |
| profit factor (trades, median step) | 0.95 | 0.85 | 0.93 | 0.83 |
| win rate (trades, median step) | 46.72% | 46.90% | 47.10% | 47.10% |
| positive years of 5 | 1 | 1 | 1 | 0 |
| retention (median step) | -0.16 | -0.81 | -0.50 | -0.94 |
| steps flagged FIT of 5 | 5 | 4 | 4 | 5 |

Per year:

- ALWAYS-ON: 2016: -0.69% | 2017: -0.18% | 2018: +0.49% | 2019: -4.22% | 2020: -2.57%
- ROUTED (chop RANGING + trend TRENDING): 2016: -1.45% | 2017: -2.06% | 2018: +0.22% | 2019: -1.70% | 2020: -1.30%
- CHOP ROUTED + TREND UNGATED: 2016: -1.76% | 2017: -0.57% | 2018: +0.35% | 2019: -2.33% | 2020: -0.59%
- CHOP ROUTED + TREND NOT-RANGING: 2016: -2.57% | 2017: -1.50% | 2018: -0.33% | 2019: -1.47% | 2020: -0.36%

### TEAM 2

| KPI | ALWAYS-ON | ROUTED (chop RANGING + trend TRENDING) | CHOP ROUTED + TREND UNGATED | CHOP ROUTED + TREND NOT-RANGING |
|---|---|---|---|---|
| median year | -1.04% | -2.18% | -0.88% | -2.21% |
| average year | -2.15% | -1.89% | -1.47% | -1.87% |
| worst year | -6.33% | -3.09% | -3.50% | -3.85% |
| best year | 0.73% | 0.34% | 0.53% | -0.50% |
| total 2016-2020 | -10.77% | -9.43% | -7.34% | -9.35% |
| CAGR | -2.15% | -1.89% | -1.47% | -1.87% |
| worst day | -1.32% | -0.86% | -0.90% | -0.91% |
| max drawdown | -12.82% | -10.78% | -9.13% | -11.68% |
| DIP95 (worst step) | 8.48% | 5.86% | 5.60% | 6.54% |
| Sharpe | -0.71 | -0.86 | -0.64 | -0.91 |
| Sortino | -0.90 | -1.17 | -0.87 | -1.18 |
| Calmar (total / max DD, the shipped bar) | -0.84 | -0.88 | -0.80 | -0.80 |
| Calmar (CAGR / max DD) | -0.17 | -0.18 | -0.16 | -0.16 |
| profit factor (trades, median step) | 0.95 | 0.85 | 0.93 | 0.83 |
| win rate (trades, median step) | 46.72% | 46.90% | 47.10% | 47.10% |
| positive years of 5 | 1 | 1 | 1 | 0 |
| retention (median step) | -0.16 | -0.81 | -0.50 | -0.94 |
| steps flagged FIT of 5 | 5 | 4 | 4 | 5 |

Per year:

- ALWAYS-ON: 2016: -1.04% | 2017: -0.27% | 2018: +0.73% | 2019: -6.33% | 2020: -3.86%
- ROUTED (chop RANGING + trend TRENDING): 2016: -2.18% | 2017: -3.09% | 2018: +0.34% | 2019: -2.55% | 2020: -1.95%
- CHOP ROUTED + TREND UNGATED: 2016: -2.65% | 2017: -0.85% | 2018: +0.53% | 2019: -3.50% | 2020: -0.88%
- CHOP ROUTED + TREND NOT-RANGING: 2016: -3.85% | 2017: -2.25% | 2018: -0.50% | 2019: -2.21% | 2020: -0.54%

## Nulls (from `results/r2gate2/modeB_books_nulls.csv`)

- **Identity (strategy/year roles reassigned)**: 40 cells, p 0.32-1.00; the real book clears the null's 95th percentile in 0 of 40.
- **Random-entry (same strategies, random entry days)**: 80 cells, p 0.11-1.00; the real book clears the null's 95th percentile in 0 of 80.
- **Regime-shuffle (labels rotated, run lengths kept)**: 80 cells, p 0.05-1.00; the real book clears the null's 95th percentile in 2 of 80.

## Not available in these files

- Max simultaneous positions: not written by the streamed book.
- Sharpe is reported and binds nowhere, as declared.

## Provenance

| file | rows | md5 |
|---|---|---|
| `results/r2gate2/modeB_books_full.csv` | 40 | 8a753619cf2b |
| `results/r2gate2/modeB_books_nulls.csv` | 200 | eb9232beeb7d |
| `modeB_daily_full_*.npz` | 40 files | — |
