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

## TEAM1_W3ONLY_GATE2 (DIP95 budget 3.6%, worst-day budget 3.6%)

| metric | value |
|---|---|
| score (median year) | **20.13%** |
| average year | 16.44% |
| worst year | 0.13% |
| best year | 25.31% |
| DIP95 (shuffled day order) | 3.60% |
| actual max drawdown | **2.52%** |
| clustering ratio (actual / DIP95) | **0.70** |
| worst day | 1.04% |
| binding budget | DIP95 |
| members | 25 |
| scale factor | 3.356 |
| candidates tried | 12075 |
| DIP95 on CLOSED trades (not used for sizing) | 2.37% |
| gap, equity vs closed | **+1.23%** |
| pairs correlated > 0.90 | 0 |

## TEAM2_W3ONLY_GATE2 (DIP95 budget 5.4%, worst-day budget 3.6%)

| metric | value |
|---|---|
| score (median year) | **30.19%** |
| average year | 24.66% |
| worst year | 0.19% |
| best year | 37.96% |
| DIP95 (shuffled day order) | 5.40% |
| actual max drawdown | **3.78%** |
| clustering ratio (actual / DIP95) | **0.70** |
| worst day | 1.56% |
| binding budget | DIP95 |
| members | 25 |
| scale factor | 5.033 |
| candidates tried | 12075 |
| DIP95 on CLOSED trades (not used for sizing) | 3.55% |
| gap, equity vs closed | **+1.85%** |
| pairs correlated > 0.90 | 0 |

