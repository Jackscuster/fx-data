# MODE A KPIs — all 273,780 strategies, tuned honestly, traded years 2016–2020 stitched

Source: `results/r2gate2/modeA_daily_full_*_*_*.npz` (daily series, trade-year days only, one year per walk-forward step, stitched 2016→2020) and `results/r2gate2/modeA_books_full.csv` (trade-level PF, win rate, DIP95, retention, FIT). Generated 2026-11-20 10:51 by `code/l2r2kpis.py` — every number read back out of those files, nothing typed in by hand. Numbers CSV beside this file: `modeA_kpis_stitched_2016-2020.csv`.

Team 1 = 3.6% dip / 3.6% day budget (day zero). Team 2 = 5.4% dip / 3.6% day (after the +6% cushion). Scale set on the build years only. Everyone trades, equal weight, netted, costs charged (cost_table_h22.csv, R units), one-bar lag, 2021+ sealed.


**Scale-invariant rows** — Sharpe, Sortino, Calmar, profit factor, win rate, retention and FIT — are equal in both tables by construction: team 2 is team 1 times a constant.


## TEAM 1

| KPI | ALWAYS-ON | ROUTED (chop RANGING + trend TRENDING) | CHOP ROUTED + TREND UNGATED | CHOP ROUTED + TREND NOT-RANGING |
|---|---|---|---|---|
| median year | -1.19% | -0.91% | -0.54% | -0.59% |
| average year | -1.07% | -0.88% | -0.56% | -1.07% |
| worst year | -2.56% | -1.72% | -1.76% | -2.10% |
| best year | 0.61% | 0.66% | 0.24% | -0.15% |
| total 2016-2020 | -5.37% | -4.38% | -2.81% | -5.33% |
| CAGR | -1.07% | -0.88% | -0.56% | -1.07% |
| worst day | -0.66% | -0.62% | -0.52% | -0.53% |
| max drawdown | -7.23% | -5.28% | -4.49% | -7.07% |
| DIP95 (worst step) | 4.46% | 4.03% | 3.40% | 3.66% |
| Sharpe | -0.53 | -0.55 | -0.34 | -0.71 |
| Sortino | -0.73 | -0.76 | -0.49 | -1.00 |
| Calmar (total / max DD, the shipped bar) | -0.74 | -0.83 | -0.63 | -0.75 |
| Calmar (CAGR / max DD) | -0.15 | -0.17 | -0.13 | -0.15 |
| profit factor (trades, median step) | 0.90 | 0.91 | 0.95 | 0.94 |
| win rate (trades, median step) | 47.49% | 49.04% | 50.19% | 46.72% |
| positive years of 5 | 1 | 1 | 1 | 0 |
| retention (median step) | -0.28 | -0.40 | -0.15 | -0.24 |
| steps flagged FIT of 5 | 5 | 4 | 5 | 5 |

Per year:

- ALWAYS-ON: 2016: +0.61% | 2017: -1.23% | 2018: -1.01% | 2019: -2.56% | 2020: -1.19%
- ROUTED (chop RANGING + trend TRENDING): 2016: -1.72% | 2017: -0.91% | 2018: +0.66% | 2019: -1.69% | 2020: -0.73%
- CHOP ROUTED + TREND UNGATED: 2016: -0.54% | 2017: -0.65% | 2018: +0.24% | 2019: -1.76% | 2020: -0.10%
- CHOP ROUTED + TREND NOT-RANGING: 2016: -0.59% | 2017: -2.10% | 2018: -0.39% | 2019: -2.10% | 2020: -0.15%

## TEAM 2

| KPI | ALWAYS-ON | ROUTED (chop RANGING + trend TRENDING) | CHOP ROUTED + TREND UNGATED | CHOP ROUTED + TREND NOT-RANGING |
|---|---|---|---|---|
| median year | -1.78% | -1.36% | -0.80% | -0.88% |
| average year | -1.61% | -1.31% | -0.84% | -1.60% |
| worst year | -3.84% | -2.58% | -2.64% | -3.16% |
| best year | 0.92% | 1.00% | 0.36% | -0.22% |
| total 2016-2020 | -8.06% | -6.56% | -4.21% | -8.00% |
| CAGR | -1.61% | -1.31% | -0.84% | -1.60% |
| worst day | -0.99% | -0.92% | -0.79% | -0.79% |
| max drawdown | -10.85% | -7.92% | -6.73% | -10.61% |
| DIP95 (worst step) | 6.69% | 6.04% | 5.10% | 5.49% |
| Sharpe | -0.53 | -0.55 | -0.34 | -0.71 |
| Sortino | -0.73 | -0.76 | -0.49 | -1.00 |
| Calmar (total / max DD, the shipped bar) | -0.74 | -0.83 | -0.63 | -0.75 |
| Calmar (CAGR / max DD) | -0.15 | -0.17 | -0.13 | -0.15 |
| profit factor (trades, median step) | 0.90 | 0.91 | 0.95 | 0.94 |
| win rate (trades, median step) | 47.49% | 49.04% | 50.19% | 46.72% |
| positive years of 5 | 1 | 1 | 1 | 0 |
| retention (median step) | -0.28 | -0.40 | -0.15 | -0.24 |
| steps flagged FIT of 5 | 5 | 4 | 5 | 5 |

Per year:

- ALWAYS-ON: 2016: +0.92% | 2017: -1.85% | 2018: -1.51% | 2019: -3.84% | 2020: -1.78%
- ROUTED (chop RANGING + trend TRENDING): 2016: -2.58% | 2017: -1.36% | 2018: +1.00% | 2019: -2.53% | 2020: -1.10%
- CHOP ROUTED + TREND UNGATED: 2016: -0.80% | 2017: -0.98% | 2018: +0.36% | 2019: -2.64% | 2020: -0.15%
- CHOP ROUTED + TREND NOT-RANGING: 2016: -0.88% | 2017: -3.16% | 2018: -0.59% | 2019: -3.15% | 2020: -0.22%

## Nulls (from `results/r2gate2/modeA_books_nulls.csv`)

- **Identity (strategy/year roles reassigned)**: 40 cells, p 0.30-1.00; the real book clears the null's 95th percentile in 0 of 40.
- **Random-entry (same strategies, random entry days)**: 80 cells, p 0.16-1.00; the real book clears the null's 95th percentile in 0 of 80.
- **Regime-shuffle (labels rotated, run lengths kept)**: 80 cells, p 0.11-1.00; the real book clears the null's 95th percentile in 0 of 80.

## Not available in these files

- Max simultaneous positions: not written by the streamed book.
- Sharpe is reported and binds nowhere, as declared.

## Provenance

| file | rows | md5 |
|---|---|---|
| `results/r2gate2/modeA_books_full.csv` | 40 | d8b75ab8b54d |
| `results/r2gate2/modeA_books_nulls.csv` | 200 | 6a0051f6e911 |
| `modeA_daily_full_*.npz` | 40 files | — |
