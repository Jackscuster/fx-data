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
| score (median year) | **22.97%** |
| average year | 19.40% |
| worst year | 11.44% |
| best year | 25.62% |
| DIP95 (shuffled day order) | 3.60% |
| actual max drawdown | **2.69%** |
| clustering ratio (actual / DIP95) | **0.75** |
| worst day | 0.74% |
| binding budget | DIP95 |
| members | 25 |
| scale factor | 3.308 |
| candidates tried | 11975 |
| DIP95 on CLOSED trades (not used for sizing) | 2.27% |
| gap, equity vs closed | **+1.33%** |
| pairs correlated > 0.90 | 0 |

## TEAM2_W3ONLY_ADOPTED (DIP95 budget 5.4%, worst-day budget 3.6%)

| metric | value |
|---|---|
| score (median year) | **34.45%** |
| average year | 29.10% |
| worst year | 17.17% |
| best year | 38.42% |
| DIP95 (shuffled day order) | 5.40% |
| actual max drawdown | **4.03%** |
| clustering ratio (actual / DIP95) | **0.75** |
| worst day | 1.11% |
| binding budget | DIP95 |
| members | 25 |
| scale factor | 4.962 |
| candidates tried | 11975 |
| DIP95 on CLOSED trades (not used for sizing) | 3.40% |
| gap, equity vs closed | **+2.00%** |
| pairs correlated > 0.90 | 0 |

