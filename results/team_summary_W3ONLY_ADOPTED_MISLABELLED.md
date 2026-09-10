# Trading teams — built from the costed gate 3 cut

Sizing uses the EQUITY series: close-to-close change with every open
position marked to that day's close. Floating open losses count toward
both the daily and the trailing prop limit, so realised-only accounting
would size the team against a drawdown the account never sees. The
closed-trade DIP95 is reported beside it so the gap is visible.

**Intraday lows are invisible in close-only data.** Every figure here is
a close-to-close number, so the true worst moment inside a day is worse
than anything below. The live limit needs margin on top of the 3.6%
budget; 3.6% is not a level to trade right up to.

## TEAM1_W3ONLY_ADOPTED (DIP95 budget 3.6%, worst-day budget 3.6%)

| metric | value |
|---|---|
| score (median year) | **22.59%** |
| average year | 18.51% |
| worst year | 10.19% |
| best year | 25.65% |
| DIP95 (shuffled day order) | 3.60% |
| actual max drawdown | **2.72%** |
| clustering ratio (actual / DIP95) | **0.76** |
| worst day | 0.84% |
| binding budget | DIP95 |
| members | 26 |
| scale factor | 3.198 |
| candidates tried | 12532 |
| DIP95 on CLOSED trades (not used for sizing) | 1.99% |
| gap, equity vs closed | **+1.61%** |
| pairs correlated > 0.90 | 0 |

## TEAM2_W3ONLY_ADOPTED (DIP95 budget 5.4%, worst-day budget 3.6%)

| metric | value |
|---|---|
| score (median year) | **33.88%** |
| average year | 27.77% |
| worst year | 15.29% |
| best year | 38.47% |
| DIP95 (shuffled day order) | 5.40% |
| actual max drawdown | **4.08%** |
| clustering ratio (actual / DIP95) | **0.76** |
| worst day | 1.27% |
| binding budget | DIP95 |
| members | 26 |
| scale factor | 4.797 |
| candidates tried | 12532 |
| DIP95 on CLOSED trades (not used for sizing) | 2.99% |
| gap, equity vs closed | **+2.41%** |
| pairs correlated > 0.90 | 0 |

