# MODE A — GATE 3

Generated 2026-11-18 17:15 by `code/l2r2gate3.py`. **No new tuning**: every configuration here was already chosen by gate 2 and is re-scored, nothing is searched. Every number below is read back out of the CSV named beside it.


## The bars, unchanged

| bar | value | binds |
|---|---|---|
| expectancy | >= 0.15 R | yes |
| profit factor | >= 1.5 | yes |
| Sortino | >= 1.3 | yes |
| Calmar | >= 1.0 | yes |
| max DD | <= 10% of the strategy's OWN gross profit | yes |
| Sharpe | reported | **no — binds nowhere** |


Costs are charged throughout (`cost_table_h22`, restated per fault #27).


**Why this cost an engine pass.** The gate 2 bank stores `n, sum_r, gain, loss, n_win` per (strategy, stream, step, year), which gives expectancy, PF, win rate and trade count — but Sortino needs the downside deviation of per-trade R, and max DD and Calmar need the ordered equity curve. Neither is banked, so each winner was re-scored through the shipped `l2tune.Scorer` with one window per calendar year; the KPIs come from `_agg`, the same aggregator every other result in this project used.


## Sources

| section | file | rows | md5 |
|---|---|---|---|
| counts | results/r2gate2/modeA_gate3_counts.csv | 20 | 5fb78b102b0a |
| passers | results/r2gate2/modeA_gate3_passers.csv | 0 | 68b329da9893 |
| null | results/r2gate2/modeA_gate3_null.csv | 20 | 9246ab259329 |
| stitched | results/r2gate2/modeA_gate3_stitched.csv | 0 | 68b329da9893 |
| stitched_counts | results/r2gate2/modeA_gate3_stitched_counts.csv | 4 | 78e71b70f61e |


**Missing sources, left empty rather than filled in:** book, booknull


## 1. The bars on the GRADE year (year 5, unseen by the tuner)

| stream | step | n_field | n_clears_grade | n_also_clears_trade | pct_of_field |
|---|---|---|---|---|---|
| chop-allon | 2011-2014 | 8 | 0 | 0 | 0 |
| chop-allon | 2012-2015 | 8 | 0 | 0 | 0 |
| chop-allon | 2013-2016 | 8 | 0 | 0 | 0 |
| chop-allon | 2014-2017 | 8 | 0 | 0 | 0 |
| chop-allon | 2015-2018 | 8 | 0 | 0 | 0 |
| chop-routed | 2011-2014 | 8 | 0 | 0 | 0 |
| chop-routed | 2012-2015 | 8 | 0 | 0 | 0 |
| chop-routed | 2013-2016 | 8 | 0 | 0 | 0 |
| chop-routed | 2014-2017 | 8 | 0 | 0 | 0 |
| chop-routed | 2015-2018 | 8 | 0 | 0 | 0 |
| trend-allon | 2011-2014 | 8 | 0 | 0 | 0 |
| trend-allon | 2012-2015 | 8 | 0 | 0 | 0 |
| trend-allon | 2013-2016 | 8 | 0 | 0 | 0 |
| trend-allon | 2014-2017 | 8 | 0 | 0 | 0 |
| trend-allon | 2015-2018 | 8 | 0 | 0 | 0 |
| trend-routed | 2011-2014 | 8 | 0 | 0 | 0 |
| trend-routed | 2012-2015 | 8 | 0 | 0 | 0 |
| trend-routed | 2013-2016 | 8 | 0 | 0 | 0 |
| trend-routed | 2014-2017 | 8 | 0 | 0 | 0 |
| trend-routed | 2015-2018 | 8 | 0 | 0 | 0 |


Totals by stream:

| stream | n_clears_grade | n_also_clears_trade |
|---|---|---|
| chop-allon | 0 | 0 |
| chop-routed | 0 | 0 |
| trend-allon | 0 | 0 |
| trend-routed | 0 | 0 |


Every passer is listed in `results/r2gate2/modeA_gate3_passers.csv` with its settings, its grade-year KPIs and its trade-year KPIs. The first 20:

_no rows_


## 2. Chance level — the identity null on the year roles

Each draw calls a randomly chosen year of the step the "grade" year and another the "trade" year, and applies the identical bars. **A caveat that belongs in the reading**: those draws can land on TUNE years, on which the settings were fitted, so the null is not a neutral yardstick — it is biased toward clearing. A real count BELOW the null mean is therefore the striking direction, not the reassuring one.

| stream | step | real_clears_grade | null_mean_clears | null_p95_clears | p_grade | real_also_clears_trade | null_mean_also_trade | p_also_trade |
|---|---|---|---|---|---|---|---|---|
| chop-allon | 2011-2014 | 0 | 0.3 | 1 | 1 | 0 | 0 | 1 |
| chop-allon | 2012-2015 | 0 | 0 | 0 | 1 | 0 | 0 | 1 |
| chop-allon | 2013-2016 | 0 | 0 | 0 | 1 | 0 | 0 | 1 |
| chop-allon | 2014-2017 | 0 | 0 | 0 | 1 | 0 | 0 | 1 |
| chop-allon | 2015-2018 | 0 | 0 | 0 | 1 | 0 | 0 | 1 |
| chop-routed | 2011-2014 | 0 | 0.1 | 0.55 | 1 | 0 | 0 | 1 |
| chop-routed | 2012-2015 | 0 | 0.1 | 0.55 | 1 | 0 | 0 | 1 |
| chop-routed | 2013-2016 | 0 | 0 | 0 | 1 | 0 | 0 | 1 |
| chop-routed | 2014-2017 | 0 | 0 | 0 | 1 | 0 | 0 | 1 |
| chop-routed | 2015-2018 | 0 | 0 | 0 | 1 | 0 | 0 | 1 |
| trend-allon | 2011-2014 | 0 | 0.8 | 2 | 1 | 0 | 0 | 1 |
| trend-allon | 2012-2015 | 0 | 0.2 | 1 | 1 | 0 | 0 | 1 |
| trend-allon | 2013-2016 | 0 | 0.3 | 1 | 1 | 0 | 0 | 1 |
| trend-allon | 2014-2017 | 0 | 0 | 0 | 1 | 0 | 0 | 1 |
| trend-allon | 2015-2018 | 0 | 0 | 0 | 1 | 0 | 0 | 1 |
| trend-routed | 2011-2014 | 0 | 0.1 | 0.55 | 1 | 0 | 0 | 1 |
| trend-routed | 2012-2015 | 0 | 0.2 | 1 | 1 | 0 | 0 | 1 |
| trend-routed | 2013-2016 | 0 | 0 | 0 | 1 | 0 | 0 | 1 |
| trend-routed | 2014-2017 | 0 | 0 | 0 | 1 | 0 | 0 | 1 |
| trend-routed | 2015-2018 | 0 | 0 | 0 | 1 | 0 | 0 | 1 |


## 3. The stitched trade years 2016-2020, all unseen

| stream | n_field | n_clears_stitched | pct_of_field |
|---|---|---|---|
| trend-routed | 8 | 0 | 0 |
| trend-allon | 8 | 0 | 0 |
| chop-routed | 8 | 0 | 0 |
| chop-allon | 8 | 0 | 0 |


**Nobody passes on the stitched record.**


## 4. The passers' book

_The passers' book has not been built; this section is empty rather than filled in from anywhere else._
