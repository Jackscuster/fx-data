# MODE A KPIs — all 273,780 strategies, tuned honestly, traded years 2016–2020 stitched

Source: results/r2gate2/modeA_daily_full_*.npz (daily series, trade-year days only, one year per walk-forward step, stitched 2016→2020) and results/r2gate2/modeA_books_full.csv (trade-level PF, win rate, DIP95, retention, FIT). Generated 2026-11-18 by Claude (chat) from files on disk; numbers CSV beside this file: MODEA_KPIS_stitched_2016-2020.csv.

Team 1 = 3.6% dip / 3.6% day budget (day zero). Team 2 = 5.4% dip / 3.6% day (after the +6% cushion). Scale set on the build years only; DIP95 binds in every step. Everyone trades, equal weight, netted, costs charged (22:00 table, R units), one-bar lag, 2021+ sealed.

## TEAM 1

| KPI | ALWAYS-ON | ROUTED (chop RANGING + trend TRENDING) | CHOP ROUTED + TREND UNGATED | CHOP ROUTED + TREND NOT-RANGING |
|---|---|---|---|---|
| median year | -1.19% | -0.91% | -0.54% | -0.59% |
| average year | -1.07% | -0.88% | -0.56% | -1.07% |
| worst year | -2.56% | -1.72% | -1.76% | -2.10% |
| best year | 0.61% | 0.66% | 0.24% | -0.15% |
| total 2016-2020 | -5.33% | -4.34% | -2.83% | -5.25% |
| CAGR | -1.06% | -0.86% | -0.56% | -1.04% |
| worst day | -0.66% | -0.62% | -0.52% | -0.53% |
| max drawdown | -7.03% | -5.20% | -4.43% | -6.87% |
| DIP95 (worst step) | 4.46% | 4.03% | 3.40% | 3.66% |
| Sharpe | -0.53 | -0.55 | -0.34 | -0.71 |
| Sortino | -0.73 | -0.76 | -0.49 | -1.00 |
| Calmar | -0.15 | -0.17 | -0.13 | -0.15 |
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
| total 2016-2020 | -7.95% | -6.49% | -4.26% | -7.80% |
| CAGR | -1.60% | -1.30% | -0.84% | -1.57% |
| worst day | -0.99% | -0.92% | -0.79% | -0.79% |
| max drawdown | -10.39% | -7.74% | -6.59% | -10.16% |
| DIP95 (worst step) | 6.69% | 6.04% | 5.10% | 5.49% |
| Sharpe | -0.53 | -0.55 | -0.34 | -0.71 |
| Sortino | -0.73 | -0.76 | -0.49 | -1.00 |
| Calmar | -0.15 | -0.17 | -0.13 | -0.15 |
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

## Nulls (from MODEA_REPORT.md, results/r2gate2/modeA_books_nulls.csv)

- Random-entry (same strategies, random entry days): real book no better than random in most steps (p 0.16–1.00).
- Regime-shuffle (labels rotated, run lengths kept): routed books no better than shuffled labels (p 0.11–1.00); always-on p=1.00 by construction.
- Identity (strategy labels shuffled against build-year records): real below the null in every step (p 0.35–1.00).

## Not available in these files

- Max simultaneous positions (not written by the streamed book). Sharpe reported, binding nowhere.
