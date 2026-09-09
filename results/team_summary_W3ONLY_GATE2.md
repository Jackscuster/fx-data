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


## CORRECTION — the "worst year" figures above are wrong

The `worst year` in the tables above was computed BEFORE mark-to-market was
applied at the window boundary. Positions still open at 2020-12-31 ran on into
2021, creating a partial-year row that the minimum then picked up. The pre-fix
team's "0.13%" was that 2021 stub, not a year.

Recomputed with mark-to-market, both rosters span 2016-2020 only:

| roster | 2016 | 2017 | 2018 | 2019 | 2020 | worst | median |
|---|---|---|---|---|---|---|---|
| pre-fix team 1 | 21.33 | 19.90 | 29.36 | 19.12 | 15.72 | **15.72 (2020)** | 19.90 |
| fixed team 1 | 22.59 | 11.53 | 25.65 | 10.19 | 22.62 | **10.19 (2019)** | 22.59 |
| pre-fix team 2 | 32.00 | 29.85 | 44.04 | 28.69 | 23.59 | **23.59 (2020)** | 29.85 |
| fixed team 2 | 33.88 | 17.29 | 38.47 | 15.29 | 33.93 | **15.29 (2019)** | 33.88 |

So the mode fix RAISES the median year and LOWERS the worst year. It does not
produce a uniformly better book, and the earlier claim that it improved the
worst year from 0.13% to 10.19% was an artefact of comparing against a stub.
