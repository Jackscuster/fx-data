# A4 — CURRENCY NETTING AND THE EXPOSURE CAP

Generated 2026-11-24 10:33 by `code/r2hourly.py`.


## What was specified, and what each section answers

| specified | section |
|---|---|
| share of the 10 worst days from the largest leg | 2 |
| share of the worst dip from the largest leg | 2 |
| the cap on net exposure per currency swept over its full range, with yearly return, worst dip, DIP95 and Team 1 return at each cap | 3 |
| winners' books and the whole-field book | both, by `rule` |

**This report exists because the first A4 run delivered only the per-currency legs.** Chain 26 reported 8 stages succeeded and 0 failed, but the stages declared covered one of the four things asked for.


## 1 — the cap is the shipped one, not a new one

`l2walkfwd.Book.series` already takes `cap_pct` and `per_unit`, builds the per-currency exposure matrix, scales the whole book down on any day the worst leg exceeds the cap, and reports how many days bound. The standing value is `W.CAP_PCT = 2.0`. The sweep below loops that same call, so every swept number is comparable with what gate 3 reports rather than being a parallel implementation that might differ.


## Mode A

### The currency legs

| currency | mean_abs_exposure | max_abs_exposure | share_of_total_mean |
|---|---|---|---|
| NZD | 4.78 | 28.1 | 0.1313 |
| CAD | 4.726 | 26.62 | 0.1456 |
| JPY | 4.649 | 27.3 | 0.129 |
| GBP | 4.455 | 36.43 | 0.1216 |
| USD | 4.26 | 29.91 | 0.1176 |
| AUD | 4.247 | 20.6 | 0.1194 |
| CHF | 4.127 | 22.1 | 0.1214 |
| EUR | 4.045 | 22.62 | 0.1141 |


### 2 — what the largest leg accounts for

`worst10_largest_leg_share` is the mean share of total absolute exposure held by the single biggest currency leg **on the ten worst days**; `allday_largest_leg_share` is the same on every day. If the first is materially higher, the bad days are concentration events.

| rule | step | book | budget | worst10_mean_pct | worst10_largest_leg_share | worst10_top_currency | allday_largest_leg_share | worst_dip_pct | worst_dip_days | worst_dip_largest_leg_share | worst_dip_top_currency |
|---|---|---|---|---|---|---|---|---|---|---|---|
| winners | 2011-2014 | allon | team1 | -0.2585 | 0.3159 | GBP | 0.3032 | 0.9261 | 31 | 0.3571 | GBP |
| winners | 2011-2014 | allon | team2 | -0.3878 | 0.3159 | GBP | 0.3032 | 1.389 | 31 | 0.3571 | GBP |
| winners | 2012-2015 | allon | team1 | -0.2356 | 0.3084 | CAD | 0.3227 | 0.665 | 16 | 0.3202 | JPY |
| winners | 2012-2015 | allon | team2 | -0.3534 | 0.3084 | CAD | 0.3227 | 0.9975 | 16 | 0.3202 | JPY |
| winners | 2013-2016 | allon | team1 | -0.2289 | 0.3145 | USD | 0.3724 | 0.7813 | 20 | 0.3222 | USD |
| winners | 2013-2016 | allon | team2 | -0.3433 | 0.3145 | USD | 0.3724 | 1.172 | 20 | 0.3222 | USD |
| winners | 2014-2017 | allon | team1 | -0.2845 | 0.3126 | CAD | 0.3586 | 1.951 | 68 | 0.3526 | CAD |
| winners | 2014-2017 | allon | team2 | -0.4267 | 0.3126 | CAD | 0.3586 | 2.927 | 68 | 0.3526 | CAD |
| winners | 2015-2018 | allon | team1 | -0.3458 | 0.2967 | CAD | 0.3576 | 1.362 | 62 | 0.3546 | AUD |
| winners | 2015-2018 | allon | team2 | -0.5187 | 0.2967 | CAD | 0.3576 | 2.042 | 62 | 0.3546 | AUD |


The largest leg carries **31.0%** of absolute exposure on the ten worst days against **34.3%** on an average day, and **34.1%** through the worst dip.


### 3 — the cap swept over its full range

Team 1 budget (3.6%% dip, 3.6%% day), median across steps and books. `cap_pct = NaN` is uncapped. Reported as a curve, not at a chosen cap.

| cap_pct | yearly_return_pct | worst_dip_pct | dip95_pct | prop_return | cap_bound_days | clears |
|---|---|---|---|---|---|---|
| 0.5 | 1.865 | 1.738 | 2.005 | 3.665 | 1001 | 1 |
| 0.75 | 1.934 | 1.94 | 2.01 | 3.763 | 236 | 1 |
| 1 | 2.168 | 1.951 | 2.01 | 3.763 | 14 | 1 |
| 1.25 | 2.278 | 1.951 | 2.01 | 3.763 | 0 | 1 |
| 1.5 | 2.278 | 1.951 | 2.01 | 3.763 | 0 | 1 |
| 1.75 | 2.278 | 1.951 | 2.01 | 3.763 | 0 | 1 |
| 2 | 2.278 | 1.951 | 2.01 | 3.763 | 0 | 1 |
| 2.5 | 2.278 | 1.951 | 2.01 | 3.763 | 0 | 1 |
| 3 | 2.278 | 1.951 | 2.01 | 3.763 | 0 | 1 |
| 4 | 2.278 | 1.951 | 2.01 | 3.763 | 0 | 1 |
| 5 | 2.278 | 1.951 | 2.01 | 3.763 | 0 | 1 |
| 6 | 2.278 | 1.951 | 2.01 | 3.763 | 0 | 1 |
| 8 | 2.278 | 1.951 | 2.01 | 3.763 | 0 | 1 |
|  | 2.278 | 1.951 | 2.01 | 3.763 | 0 | 1 |


Best prop return **3.76%/yr at cap 0.75**, against **3.76%/yr uncapped**. The standing cap is 2.0.


**28 of 140 swept cells clear the 12%/yr target.**


### The full sweep, every rule, book and budget

`rule = winners` is the winners' books; `rule = grade` is the whole-field book of everything clearing the grade-year bars.

| rule | step | book | budget | members | cap_pct | cap_bound_days | yearly_return_pct | worst_dip_pct | dip95_pct | prop_return | clears_12pct |
|---|---|---|---|---|---|---|---|---|---|---|---|
| winners | 2011-2014 | allon | team1 | 8 | 0.5 | 5 | 1.838 | 0.9261 | 2.005 | 3.299 | 0 |
| winners | 2012-2015 | allon | team1 | 8 | 0.5 | 34 | 1.865 | 0.665 | 1.831 | 3.665 | 0 |
| winners | 2013-2016 | allon | team1 | 8 | 0.5 | 148 | 5.929 | 0.7524 | 1.191 | 17.93 | 1 |
| winners | 2014-2017 | allon | team1 | 8 | 0.5 | 287 | 2.102 | 1.738 | 2.053 | 3.687 | 0 |
| winners | 2015-2018 | allon | team1 | 8 | 0.5 | 527 | 1.303 | 1.352 | 2.4 | 1.955 | 0 |
| winners | 2011-2014 | allon | team1 | 8 | 0.75 | 0 | 1.874 | 0.9261 | 2.01 | 3.357 | 0 |
| winners | 2012-2015 | allon | team1 | 8 | 0.75 | 0 | 1.911 | 0.665 | 1.828 | 3.763 | 0 |
| winners | 2013-2016 | allon | team1 | 8 | 0.75 | 36 | 6.112 | 0.781 | 1.289 | 17.07 | 1 |
| winners | 2014-2017 | allon | team1 | 8 | 0.75 | 64 | 2.694 | 1.94 | 2.197 | 4.415 | 0 |
| winners | 2015-2018 | allon | team1 | 8 | 0.75 | 136 | 1.934 | 1.399 | 2.694 | 2.584 | 0 |
| winners | 2011-2014 | allon | team1 | 8 | 1 | 0 | 1.874 | 0.9261 | 2.01 | 3.357 | 0 |
| winners | 2012-2015 | allon | team1 | 8 | 1 | 0 | 1.911 | 0.665 | 1.828 | 3.763 | 0 |
| winners | 2013-2016 | allon | team1 | 8 | 1 | 1 | 6.138 | 0.7813 | 1.291 | 17.11 | 1 |
| winners | 2014-2017 | allon | team1 | 8 | 1 | 1 | 2.614 | 1.951 | 2.263 | 4.159 | 0 |
| winners | 2015-2018 | allon | team1 | 8 | 1 | 12 | 2.168 | 1.362 | 2.704 | 2.886 | 0 |
| winners | 2011-2014 | allon | team1 | 8 | 1.25 | 0 | 1.874 | 0.9261 | 2.01 | 3.357 | 0 |
| winners | 2012-2015 | allon | team1 | 8 | 1.25 | 0 | 1.911 | 0.665 | 1.828 | 3.763 | 0 |
| winners | 2013-2016 | allon | team1 | 8 | 1.25 | 0 | 6.138 | 0.7813 | 1.291 | 17.11 | 1 |
| winners | 2014-2017 | allon | team1 | 8 | 1.25 | 0 | 2.612 | 1.951 | 2.264 | 4.153 | 0 |
| winners | 2015-2018 | allon | team1 | 8 | 1.25 | 0 | 2.278 | 1.362 | 2.696 | 3.041 | 0 |
| winners | 2011-2014 | allon | team1 | 8 | 1.5 | 0 | 1.874 | 0.9261 | 2.01 | 3.357 | 0 |
| winners | 2012-2015 | allon | team1 | 8 | 1.5 | 0 | 1.911 | 0.665 | 1.828 | 3.763 | 0 |
| winners | 2013-2016 | allon | team1 | 8 | 1.5 | 0 | 6.138 | 0.7813 | 1.291 | 17.11 | 1 |
| winners | 2014-2017 | allon | team1 | 8 | 1.5 | 0 | 2.612 | 1.951 | 2.264 | 4.153 | 0 |
| winners | 2015-2018 | allon | team1 | 8 | 1.5 | 0 | 2.278 | 1.362 | 2.696 | 3.041 | 0 |
| winners | 2011-2014 | allon | team1 | 8 | 1.75 | 0 | 1.874 | 0.9261 | 2.01 | 3.357 | 0 |
| winners | 2012-2015 | allon | team1 | 8 | 1.75 | 0 | 1.911 | 0.665 | 1.828 | 3.763 | 0 |
| winners | 2013-2016 | allon | team1 | 8 | 1.75 | 0 | 6.138 | 0.7813 | 1.291 | 17.11 | 1 |
| winners | 2014-2017 | allon | team1 | 8 | 1.75 | 0 | 2.612 | 1.951 | 2.264 | 4.153 | 0 |
| winners | 2015-2018 | allon | team1 | 8 | 1.75 | 0 | 2.278 | 1.362 | 2.696 | 3.041 | 0 |
| winners | 2011-2014 | allon | team1 | 8 | 2 | 0 | 1.874 | 0.9261 | 2.01 | 3.357 | 0 |
| winners | 2012-2015 | allon | team1 | 8 | 2 | 0 | 1.911 | 0.665 | 1.828 | 3.763 | 0 |
| winners | 2013-2016 | allon | team1 | 8 | 2 | 0 | 6.138 | 0.7813 | 1.291 | 17.11 | 1 |
| winners | 2014-2017 | allon | team1 | 8 | 2 | 0 | 2.612 | 1.951 | 2.264 | 4.153 | 0 |
| winners | 2015-2018 | allon | team1 | 8 | 2 | 0 | 2.278 | 1.362 | 2.696 | 3.041 | 0 |
| winners | 2011-2014 | allon | team1 | 8 | 2.5 | 0 | 1.874 | 0.9261 | 2.01 | 3.357 | 0 |
| winners | 2012-2015 | allon | team1 | 8 | 2.5 | 0 | 1.911 | 0.665 | 1.828 | 3.763 | 0 |
| winners | 2013-2016 | allon | team1 | 8 | 2.5 | 0 | 6.138 | 0.7813 | 1.291 | 17.11 | 1 |
| winners | 2014-2017 | allon | team1 | 8 | 2.5 | 0 | 2.612 | 1.951 | 2.264 | 4.153 | 0 |
| winners | 2015-2018 | allon | team1 | 8 | 2.5 | 0 | 2.278 | 1.362 | 2.696 | 3.041 | 0 |
| winners | 2011-2014 | allon | team1 | 8 | 3 | 0 | 1.874 | 0.9261 | 2.01 | 3.357 | 0 |
| winners | 2012-2015 | allon | team1 | 8 | 3 | 0 | 1.911 | 0.665 | 1.828 | 3.763 | 0 |
| winners | 2013-2016 | allon | team1 | 8 | 3 | 0 | 6.138 | 0.7813 | 1.291 | 17.11 | 1 |
| winners | 2014-2017 | allon | team1 | 8 | 3 | 0 | 2.612 | 1.951 | 2.264 | 4.153 | 0 |
| winners | 2015-2018 | allon | team1 | 8 | 3 | 0 | 2.278 | 1.362 | 2.696 | 3.041 | 0 |
| winners | 2011-2014 | allon | team1 | 8 | 4 | 0 | 1.874 | 0.9261 | 2.01 | 3.357 | 0 |
| winners | 2012-2015 | allon | team1 | 8 | 4 | 0 | 1.911 | 0.665 | 1.828 | 3.763 | 0 |
| winners | 2013-2016 | allon | team1 | 8 | 4 | 0 | 6.138 | 0.7813 | 1.291 | 17.11 | 1 |
| winners | 2014-2017 | allon | team1 | 8 | 4 | 0 | 2.612 | 1.951 | 2.264 | 4.153 | 0 |
| winners | 2015-2018 | allon | team1 | 8 | 4 | 0 | 2.278 | 1.362 | 2.696 | 3.041 | 0 |
| winners | 2011-2014 | allon | team1 | 8 | 5 | 0 | 1.874 | 0.9261 | 2.01 | 3.357 | 0 |
| winners | 2012-2015 | allon | team1 | 8 | 5 | 0 | 1.911 | 0.665 | 1.828 | 3.763 | 0 |
| winners | 2013-2016 | allon | team1 | 8 | 5 | 0 | 6.138 | 0.7813 | 1.291 | 17.11 | 1 |
| winners | 2014-2017 | allon | team1 | 8 | 5 | 0 | 2.612 | 1.951 | 2.264 | 4.153 | 0 |
| winners | 2015-2018 | allon | team1 | 8 | 5 | 0 | 2.278 | 1.362 | 2.696 | 3.041 | 0 |
| winners | 2011-2014 | allon | team1 | 8 | 6 | 0 | 1.874 | 0.9261 | 2.01 | 3.357 | 0 |
| winners | 2012-2015 | allon | team1 | 8 | 6 | 0 | 1.911 | 0.665 | 1.828 | 3.763 | 0 |
| winners | 2013-2016 | allon | team1 | 8 | 6 | 0 | 6.138 | 0.7813 | 1.291 | 17.11 | 1 |
| winners | 2014-2017 | allon | team1 | 8 | 6 | 0 | 2.612 | 1.951 | 2.264 | 4.153 | 0 |
| winners | 2015-2018 | allon | team1 | 8 | 6 | 0 | 2.278 | 1.362 | 2.696 | 3.041 | 0 |
| winners | 2011-2014 | allon | team1 | 8 | 8 | 0 | 1.874 | 0.9261 | 2.01 | 3.357 | 0 |
| winners | 2012-2015 | allon | team1 | 8 | 8 | 0 | 1.911 | 0.665 | 1.828 | 3.763 | 0 |
| winners | 2013-2016 | allon | team1 | 8 | 8 | 0 | 6.138 | 0.7813 | 1.291 | 17.11 | 1 |
| winners | 2014-2017 | allon | team1 | 8 | 8 | 0 | 2.612 | 1.951 | 2.264 | 4.153 | 0 |
| winners | 2015-2018 | allon | team1 | 8 | 8 | 0 | 2.278 | 1.362 | 2.696 | 3.041 | 0 |
| winners | 2011-2014 | allon | team1 | 8 |  | 0 | 1.874 | 0.9261 | 2.01 | 3.357 | 0 |
| winners | 2012-2015 | allon | team1 | 8 |  | 0 | 1.911 | 0.665 | 1.828 | 3.763 | 0 |
| winners | 2013-2016 | allon | team1 | 8 |  | 0 | 6.138 | 0.7813 | 1.291 | 17.11 | 1 |
| winners | 2014-2017 | allon | team1 | 8 |  | 0 | 2.612 | 1.951 | 2.264 | 4.153 | 0 |
| winners | 2015-2018 | allon | team1 | 8 |  | 0 | 2.278 | 1.362 | 2.696 | 3.041 | 0 |
| winners | 2011-2014 | allon | team2 | 8 | 0.5 | 238 | 2.643 | 1.322 | 2.823 | 3.37 | 0 |
| winners | 2012-2015 | allon | team2 | 8 | 0.5 | 429 | 2.399 | 0.9225 | 2.563 | 3.37 | 0 |
| winners | 2013-2016 | allon | team2 | 8 | 0.5 | 544 | 7.645 | 0.9638 | 1.478 | 18.63 | 1 |
| winners | 2014-2017 | allon | team2 | 8 | 0.5 | 712 | 2.394 | 1.971 | 2.475 | 3.481 | 0 |
| winners | 2015-2018 | allon | team2 | 8 | 0.5 | 844 | 0.9444 | 1.759 | 2.908 | 1.169 | 0 |
| winners | 2011-2014 | allon | team2 | 8 | 0.75 | 5 | 2.757 | 1.389 | 3.008 | 3.299 | 0 |
| winners | 2012-2015 | allon | team2 | 8 | 0.75 | 34 | 2.797 | 0.9975 | 2.747 | 3.665 | 0 |
| winners | 2013-2016 | allon | team2 | 8 | 0.75 | 148 | 8.894 | 1.129 | 1.786 | 17.93 | 1 |
| winners | 2014-2017 | allon | team2 | 8 | 0.75 | 287 | 3.154 | 2.606 | 3.079 | 3.687 | 0 |
| winners | 2015-2018 | allon | team2 | 8 | 0.75 | 527 | 1.955 | 2.028 | 3.6 | 1.955 | 0 |
| winners | 2011-2014 | allon | team2 | 8 | 1 | 0 | 2.811 | 1.389 | 3.015 | 3.357 | 0 |
| winners | 2012-2015 | allon | team2 | 8 | 1 | 0 | 2.867 | 0.9975 | 2.743 | 3.763 | 0 |
| winners | 2013-2016 | allon | team2 | 8 | 1 | 60 | 9.165 | 1.158 | 1.884 | 17.51 | 1 |
| winners | 2014-2017 | allon | team2 | 8 | 1 | 104 | 3.872 | 2.88 | 3.286 | 4.243 | 0 |
| winners | 2015-2018 | allon | team2 | 8 | 1 | 193 | 2.768 | 2.148 | 3.923 | 2.539 | 0 |
| winners | 2011-2014 | allon | team2 | 8 | 1.25 | 0 | 2.811 | 1.389 | 3.015 | 3.357 | 0 |
| winners | 2012-2015 | allon | team2 | 8 | 1.25 | 0 | 2.867 | 0.9975 | 2.743 | 3.763 | 0 |
| winners | 2013-2016 | allon | team2 | 8 | 1.25 | 7 | 9.198 | 1.172 | 1.937 | 17.1 | 1 |
| winners | 2014-2017 | allon | team2 | 8 | 1.25 | 24 | 4.022 | 2.927 | 3.341 | 4.334 | 0 |
| winners | 2015-2018 | allon | team2 | 8 | 1.25 | 67 | 3.082 | 2.065 | 4.056 | 2.735 | 0 |
| winners | 2011-2014 | allon | team2 | 8 | 1.5 | 0 | 2.811 | 1.389 | 3.015 | 3.357 | 0 |
| winners | 2012-2015 | allon | team2 | 8 | 1.5 | 0 | 2.867 | 0.9975 | 2.743 | 3.763 | 0 |
| winners | 2013-2016 | allon | team2 | 8 | 1.5 | 1 | 9.207 | 1.172 | 1.937 | 17.11 | 1 |
| winners | 2014-2017 | allon | team2 | 8 | 1.5 | 1 | 3.921 | 2.927 | 3.394 | 4.159 | 0 |
| winners | 2015-2018 | allon | team2 | 8 | 1.5 | 12 | 3.251 | 2.042 | 4.056 | 2.886 | 0 |
| winners | 2011-2014 | allon | team2 | 8 | 1.75 | 0 | 2.811 | 1.389 | 3.015 | 3.357 | 0 |
| winners | 2012-2015 | allon | team2 | 8 | 1.75 | 0 | 2.867 | 0.9975 | 2.743 | 3.763 | 0 |
| winners | 2013-2016 | allon | team2 | 8 | 1.75 | 0 | 9.207 | 1.172 | 1.937 | 17.11 | 1 |
| winners | 2014-2017 | allon | team2 | 8 | 1.75 | 0 | 3.917 | 2.927 | 3.396 | 4.153 | 0 |
| winners | 2015-2018 | allon | team2 | 8 | 1.75 | 0 | 3.417 | 2.042 | 4.044 | 3.041 | 0 |
| winners | 2011-2014 | allon | team2 | 8 | 2 | 0 | 2.811 | 1.389 | 3.015 | 3.357 | 0 |
| winners | 2012-2015 | allon | team2 | 8 | 2 | 0 | 2.867 | 0.9975 | 2.743 | 3.763 | 0 |
| winners | 2013-2016 | allon | team2 | 8 | 2 | 0 | 9.207 | 1.172 | 1.937 | 17.11 | 1 |
| winners | 2014-2017 | allon | team2 | 8 | 2 | 0 | 3.917 | 2.927 | 3.396 | 4.153 | 0 |
| winners | 2015-2018 | allon | team2 | 8 | 2 | 0 | 3.417 | 2.042 | 4.044 | 3.041 | 0 |
| winners | 2011-2014 | allon | team2 | 8 | 2.5 | 0 | 2.811 | 1.389 | 3.015 | 3.357 | 0 |
| winners | 2012-2015 | allon | team2 | 8 | 2.5 | 0 | 2.867 | 0.9975 | 2.743 | 3.763 | 0 |
| winners | 2013-2016 | allon | team2 | 8 | 2.5 | 0 | 9.207 | 1.172 | 1.937 | 17.11 | 1 |
| winners | 2014-2017 | allon | team2 | 8 | 2.5 | 0 | 3.917 | 2.927 | 3.396 | 4.153 | 0 |
| winners | 2015-2018 | allon | team2 | 8 | 2.5 | 0 | 3.417 | 2.042 | 4.044 | 3.041 | 0 |
| winners | 2011-2014 | allon | team2 | 8 | 3 | 0 | 2.811 | 1.389 | 3.015 | 3.357 | 0 |
| winners | 2012-2015 | allon | team2 | 8 | 3 | 0 | 2.867 | 0.9975 | 2.743 | 3.763 | 0 |
| winners | 2013-2016 | allon | team2 | 8 | 3 | 0 | 9.207 | 1.172 | 1.937 | 17.11 | 1 |
| winners | 2014-2017 | allon | team2 | 8 | 3 | 0 | 3.917 | 2.927 | 3.396 | 4.153 | 0 |
| winners | 2015-2018 | allon | team2 | 8 | 3 | 0 | 3.417 | 2.042 | 4.044 | 3.041 | 0 |
| winners | 2011-2014 | allon | team2 | 8 | 4 | 0 | 2.811 | 1.389 | 3.015 | 3.357 | 0 |
| winners | 2012-2015 | allon | team2 | 8 | 4 | 0 | 2.867 | 0.9975 | 2.743 | 3.763 | 0 |
| winners | 2013-2016 | allon | team2 | 8 | 4 | 0 | 9.207 | 1.172 | 1.937 | 17.11 | 1 |
| winners | 2014-2017 | allon | team2 | 8 | 4 | 0 | 3.917 | 2.927 | 3.396 | 4.153 | 0 |
| winners | 2015-2018 | allon | team2 | 8 | 4 | 0 | 3.417 | 2.042 | 4.044 | 3.041 | 0 |
| winners | 2011-2014 | allon | team2 | 8 | 5 | 0 | 2.811 | 1.389 | 3.015 | 3.357 | 0 |
| winners | 2012-2015 | allon | team2 | 8 | 5 | 0 | 2.867 | 0.9975 | 2.743 | 3.763 | 0 |
| winners | 2013-2016 | allon | team2 | 8 | 5 | 0 | 9.207 | 1.172 | 1.937 | 17.11 | 1 |
| winners | 2014-2017 | allon | team2 | 8 | 5 | 0 | 3.917 | 2.927 | 3.396 | 4.153 | 0 |
| winners | 2015-2018 | allon | team2 | 8 | 5 | 0 | 3.417 | 2.042 | 4.044 | 3.041 | 0 |
| winners | 2011-2014 | allon | team2 | 8 | 6 | 0 | 2.811 | 1.389 | 3.015 | 3.357 | 0 |
| winners | 2012-2015 | allon | team2 | 8 | 6 | 0 | 2.867 | 0.9975 | 2.743 | 3.763 | 0 |
| winners | 2013-2016 | allon | team2 | 8 | 6 | 0 | 9.207 | 1.172 | 1.937 | 17.11 | 1 |
| winners | 2014-2017 | allon | team2 | 8 | 6 | 0 | 3.917 | 2.927 | 3.396 | 4.153 | 0 |
| winners | 2015-2018 | allon | team2 | 8 | 6 | 0 | 3.417 | 2.042 | 4.044 | 3.041 | 0 |
| winners | 2011-2014 | allon | team2 | 8 | 8 | 0 | 2.811 | 1.389 | 3.015 | 3.357 | 0 |
| winners | 2012-2015 | allon | team2 | 8 | 8 | 0 | 2.867 | 0.9975 | 2.743 | 3.763 | 0 |
| winners | 2013-2016 | allon | team2 | 8 | 8 | 0 | 9.207 | 1.172 | 1.937 | 17.11 | 1 |
| winners | 2014-2017 | allon | team2 | 8 | 8 | 0 | 3.917 | 2.927 | 3.396 | 4.153 | 0 |
| winners | 2015-2018 | allon | team2 | 8 | 8 | 0 | 3.417 | 2.042 | 4.044 | 3.041 | 0 |
| winners | 2011-2014 | allon | team2 | 8 |  | 0 | 2.811 | 1.389 | 3.015 | 3.357 | 0 |
| winners | 2012-2015 | allon | team2 | 8 |  | 0 | 2.867 | 0.9975 | 2.743 | 3.763 | 0 |
| winners | 2013-2016 | allon | team2 | 8 |  | 0 | 9.207 | 1.172 | 1.937 | 17.11 | 1 |
| winners | 2014-2017 | allon | team2 | 8 |  | 0 | 3.917 | 2.927 | 3.396 | 4.153 | 0 |
| winners | 2015-2018 | allon | team2 | 8 |  | 0 | 3.417 | 2.042 | 4.044 | 3.041 | 0 |


## Mode B

### The currency legs

| currency | mean_abs_exposure | max_abs_exposure | share_of_total_mean |
|---|---|---|---|
| NZD | 3.597 | 30 | 0.1343 |
| AUD | 3.194 | 30 | 0.1295 |
| CHF | 3.082 | 18 | 0.1517 |
| EUR | 2.972 | 24 | 0.1227 |
| USD | 2.958 | 24 | 0.1157 |
| GBP | 2.864 | 30 | 0.1151 |
| CAD | 2.776 | 18 | 0.1252 |
| JPY | 2.715 | 30 | 0.1059 |


### 2 — what the largest leg accounts for

`worst10_largest_leg_share` is the mean share of total absolute exposure held by the single biggest currency leg **on the ten worst days**; `allday_largest_leg_share` is the same on every day. If the first is materially higher, the bad days are concentration events.

| rule | step | book | budget | worst10_mean_pct | worst10_largest_leg_share | worst10_top_currency | allday_largest_leg_share | worst_dip_pct | worst_dip_days | worst_dip_largest_leg_share | worst_dip_top_currency |
|---|---|---|---|---|---|---|---|---|---|---|---|
| winners | 2011-2014 | allon | team1 | -0.2934 | 0.3828 | AUD | 0.4159 | 1.028 | 54 | 0.4114 | AUD |
| winners | 2011-2014 | allon | team2 | -0.4401 | 0.3828 | AUD | 0.4159 | 1.542 | 54 | 0.4114 | AUD |
| winners | 2012-2015 | allon | team1 | -0.2064 | 0.3232 | GBP | 0.3748 | 0.5738 | 45 | 0.4656 | AUD |
| winners | 2012-2015 | allon | team2 | -0.3096 | 0.3232 | GBP | 0.3748 | 0.8606 | 45 | 0.4656 | AUD |
| winners | 2013-2016 | allon | team1 | -0.2685 | 0.3485 | JPY | 0.3767 | 0.8458 | 36 | 0.3765 | NZD |
| winners | 2013-2016 | allon | team2 | -0.4028 | 0.3485 | JPY | 0.3767 | 1.269 | 36 | 0.3765 | NZD |
| winners | 2014-2017 | allon | team1 | -0.3555 | 0.4019 | GBP | 0.4293 | 1.31 | 52 | 0.4383 | GBP |
| winners | 2014-2017 | allon | team2 | -0.5332 | 0.4019 | GBP | 0.4293 | 1.965 | 52 | 0.4383 | GBP |
| winners | 2015-2018 | allon | team1 | -0.3631 | 0.3 | CAD | 0.4248 | 1.406 | 32 | 0.4464 | AUD |
| winners | 2015-2018 | allon | team2 | -0.5446 | 0.3 | CAD | 0.4248 | 2.109 | 32 | 0.4464 | AUD |


The largest leg carries **35.1%** of absolute exposure on the ten worst days against **40.4%** on an average day, and **42.8%** through the worst dip.


### 3 — the cap swept over its full range

Team 1 budget (3.6%% dip, 3.6%% day), median across steps and books. `cap_pct = NaN` is uncapped. Reported as a curve, not at a chosen cap.

| cap_pct | yearly_return_pct | worst_dip_pct | dip95_pct | prop_return | cap_bound_days | clears |
|---|---|---|---|---|---|---|
| 0.5 | 2.004 | 1.281 | 1.91 | 3.777 | 1321 | 1 |
| 0.75 | 2.459 | 1.406 | 2.097 | 4.96 | 322 | 1 |
| 1 | 2.459 | 1.406 | 2.19 | 5.75 | 99 | 1 |
| 1.25 | 2.459 | 1.406 | 2.19 | 6.453 | 24 | 1 |
| 1.5 | 2.459 | 1.406 | 2.19 | 6.601 | 11 | 1 |
| 1.75 | 2.459 | 1.406 | 2.19 | 6.421 | 0 | 1 |
| 2 | 2.459 | 1.406 | 2.19 | 6.421 | 0 | 1 |
| 2.5 | 2.459 | 1.406 | 2.19 | 6.421 | 0 | 1 |
| 3 | 2.459 | 1.406 | 2.19 | 6.421 | 0 | 1 |
| 4 | 2.459 | 1.406 | 2.19 | 6.421 | 0 | 1 |
| 5 | 2.459 | 1.406 | 2.19 | 6.421 | 0 | 1 |
| 6 | 2.459 | 1.406 | 2.19 | 6.421 | 0 | 1 |
| 8 | 2.459 | 1.406 | 2.19 | 6.421 | 0 | 1 |
|  | 2.459 | 1.406 | 2.19 | 6.421 | 0 | 1 |


Best prop return **6.60%/yr at cap 1.5**, against **6.42%/yr uncapped**. The standing cap is 2.0.


**28 of 140 swept cells clear the 12%/yr target.**


### The full sweep, every rule, book and budget

`rule = winners` is the winners' books; `rule = grade` is the whole-field book of everything clearing the grade-year bars.

| rule | step | book | budget | members | cap_pct | cap_bound_days | yearly_return_pct | worst_dip_pct | dip95_pct | prop_return | clears_12pct |
|---|---|---|---|---|---|---|---|---|---|---|---|
| winners | 2011-2014 | allon | team1 | 2 | 0.5 | 123 | 1.019 | 0.9283 | 1.98 | 1.853 | 0 |
| winners | 2012-2015 | allon | team1 | 2 | 0.5 | 44 | 2.482 | 0.5738 | 1.281 | 6.975 | 0 |
| winners | 2013-2016 | allon | team1 | 2 | 0.5 | 192 | 6.398 | 0.7451 | 1.25 | 18.43 | 1 |
| winners | 2014-2017 | allon | team1 | 2 | 0.5 | 507 | 2.004 | 1.154 | 1.91 | 3.777 | 0 |
| winners | 2015-2018 | allon | team1 | 2 | 0.5 | 455 | 0.184 | 1.281 | 2.437 | 0.2719 | 0 |
| winners | 2011-2014 | allon | team1 | 2 | 0.75 | 26 | 1.494 | 1.028 | 2.189 | 2.458 | 0 |
| winners | 2012-2015 | allon | team1 | 2 | 0.75 | 4 | 2.459 | 0.5738 | 1.285 | 6.888 | 0 |
| winners | 2013-2016 | allon | team1 | 2 | 0.75 | 51 | 6.564 | 0.8279 | 1.444 | 16.36 | 1 |
| winners | 2014-2017 | allon | team1 | 2 | 0.75 | 143 | 2.889 | 1.191 | 2.097 | 4.96 | 0 |
| winners | 2015-2018 | allon | team1 | 2 | 0.75 | 98 | 0.8207 | 1.406 | 2.767 | 1.068 | 0 |
| winners | 2011-2014 | allon | team1 | 2 | 1 | 0 | 1.538 | 1.028 | 2.19 | 2.528 | 0 |
| winners | 2012-2015 | allon | team1 | 2 | 1 | 1 | 2.459 | 0.5738 | 1.285 | 6.888 | 0 |
| winners | 2013-2016 | allon | team1 | 2 | 1 | 0 | 6.559 | 0.8458 | 1.506 | 15.67 | 1 |
| winners | 2014-2017 | allon | team1 | 2 | 1 | 89 | 3.505 | 1.298 | 2.195 | 5.75 | 0 |
| winners | 2015-2018 | allon | team1 | 2 | 1 | 9 | 1.488 | 1.406 | 2.697 | 1.986 | 0 |
| winners | 2011-2014 | allon | team1 | 2 | 1.25 | 0 | 1.538 | 1.028 | 2.19 | 2.528 | 0 |
| winners | 2012-2015 | allon | team1 | 2 | 1.25 | 0 | 2.459 | 0.5738 | 1.285 | 6.888 | 0 |
| winners | 2013-2016 | allon | team1 | 2 | 1.25 | 0 | 6.559 | 0.8458 | 1.506 | 15.67 | 1 |
| winners | 2014-2017 | allon | team1 | 2 | 1.25 | 15 | 4.034 | 1.31 | 2.25 | 6.453 | 0 |
| winners | 2015-2018 | allon | team1 | 2 | 1.25 | 9 | 1.488 | 1.406 | 2.697 | 1.986 | 0 |
| winners | 2011-2014 | allon | team1 | 2 | 1.5 | 0 | 1.538 | 1.028 | 2.19 | 2.528 | 0 |
| winners | 2012-2015 | allon | team1 | 2 | 1.5 | 0 | 2.459 | 0.5738 | 1.285 | 6.888 | 0 |
| winners | 2013-2016 | allon | team1 | 2 | 1.5 | 0 | 6.559 | 0.8458 | 1.506 | 15.67 | 1 |
| winners | 2014-2017 | allon | team1 | 2 | 1.5 | 11 | 4.181 | 1.31 | 2.28 | 6.601 | 0 |
| winners | 2015-2018 | allon | team1 | 2 | 1.5 | 0 | 1.488 | 1.406 | 2.697 | 1.986 | 0 |
| winners | 2011-2014 | allon | team1 | 2 | 1.75 | 0 | 1.538 | 1.028 | 2.19 | 2.528 | 0 |
| winners | 2012-2015 | allon | team1 | 2 | 1.75 | 0 | 2.459 | 0.5738 | 1.285 | 6.888 | 0 |
| winners | 2013-2016 | allon | team1 | 2 | 1.75 | 0 | 6.559 | 0.8458 | 1.506 | 15.67 | 1 |
| winners | 2014-2017 | allon | team1 | 2 | 1.75 | 0 | 4.121 | 1.31 | 2.311 | 6.421 | 0 |
| winners | 2015-2018 | allon | team1 | 2 | 1.75 | 0 | 1.488 | 1.406 | 2.697 | 1.986 | 0 |
| winners | 2011-2014 | allon | team1 | 2 | 2 | 0 | 1.538 | 1.028 | 2.19 | 2.528 | 0 |
| winners | 2012-2015 | allon | team1 | 2 | 2 | 0 | 2.459 | 0.5738 | 1.285 | 6.888 | 0 |
| winners | 2013-2016 | allon | team1 | 2 | 2 | 0 | 6.559 | 0.8458 | 1.506 | 15.67 | 1 |
| winners | 2014-2017 | allon | team1 | 2 | 2 | 0 | 4.121 | 1.31 | 2.311 | 6.421 | 0 |
| winners | 2015-2018 | allon | team1 | 2 | 2 | 0 | 1.488 | 1.406 | 2.697 | 1.986 | 0 |
| winners | 2011-2014 | allon | team1 | 2 | 2.5 | 0 | 1.538 | 1.028 | 2.19 | 2.528 | 0 |
| winners | 2012-2015 | allon | team1 | 2 | 2.5 | 0 | 2.459 | 0.5738 | 1.285 | 6.888 | 0 |
| winners | 2013-2016 | allon | team1 | 2 | 2.5 | 0 | 6.559 | 0.8458 | 1.506 | 15.67 | 1 |
| winners | 2014-2017 | allon | team1 | 2 | 2.5 | 0 | 4.121 | 1.31 | 2.311 | 6.421 | 0 |
| winners | 2015-2018 | allon | team1 | 2 | 2.5 | 0 | 1.488 | 1.406 | 2.697 | 1.986 | 0 |
| winners | 2011-2014 | allon | team1 | 2 | 3 | 0 | 1.538 | 1.028 | 2.19 | 2.528 | 0 |
| winners | 2012-2015 | allon | team1 | 2 | 3 | 0 | 2.459 | 0.5738 | 1.285 | 6.888 | 0 |
| winners | 2013-2016 | allon | team1 | 2 | 3 | 0 | 6.559 | 0.8458 | 1.506 | 15.67 | 1 |
| winners | 2014-2017 | allon | team1 | 2 | 3 | 0 | 4.121 | 1.31 | 2.311 | 6.421 | 0 |
| winners | 2015-2018 | allon | team1 | 2 | 3 | 0 | 1.488 | 1.406 | 2.697 | 1.986 | 0 |
| winners | 2011-2014 | allon | team1 | 2 | 4 | 0 | 1.538 | 1.028 | 2.19 | 2.528 | 0 |
| winners | 2012-2015 | allon | team1 | 2 | 4 | 0 | 2.459 | 0.5738 | 1.285 | 6.888 | 0 |
| winners | 2013-2016 | allon | team1 | 2 | 4 | 0 | 6.559 | 0.8458 | 1.506 | 15.67 | 1 |
| winners | 2014-2017 | allon | team1 | 2 | 4 | 0 | 4.121 | 1.31 | 2.311 | 6.421 | 0 |
| winners | 2015-2018 | allon | team1 | 2 | 4 | 0 | 1.488 | 1.406 | 2.697 | 1.986 | 0 |
| winners | 2011-2014 | allon | team1 | 2 | 5 | 0 | 1.538 | 1.028 | 2.19 | 2.528 | 0 |
| winners | 2012-2015 | allon | team1 | 2 | 5 | 0 | 2.459 | 0.5738 | 1.285 | 6.888 | 0 |
| winners | 2013-2016 | allon | team1 | 2 | 5 | 0 | 6.559 | 0.8458 | 1.506 | 15.67 | 1 |
| winners | 2014-2017 | allon | team1 | 2 | 5 | 0 | 4.121 | 1.31 | 2.311 | 6.421 | 0 |
| winners | 2015-2018 | allon | team1 | 2 | 5 | 0 | 1.488 | 1.406 | 2.697 | 1.986 | 0 |
| winners | 2011-2014 | allon | team1 | 2 | 6 | 0 | 1.538 | 1.028 | 2.19 | 2.528 | 0 |
| winners | 2012-2015 | allon | team1 | 2 | 6 | 0 | 2.459 | 0.5738 | 1.285 | 6.888 | 0 |
| winners | 2013-2016 | allon | team1 | 2 | 6 | 0 | 6.559 | 0.8458 | 1.506 | 15.67 | 1 |
| winners | 2014-2017 | allon | team1 | 2 | 6 | 0 | 4.121 | 1.31 | 2.311 | 6.421 | 0 |
| winners | 2015-2018 | allon | team1 | 2 | 6 | 0 | 1.488 | 1.406 | 2.697 | 1.986 | 0 |
| winners | 2011-2014 | allon | team1 | 2 | 8 | 0 | 1.538 | 1.028 | 2.19 | 2.528 | 0 |
| winners | 2012-2015 | allon | team1 | 2 | 8 | 0 | 2.459 | 0.5738 | 1.285 | 6.888 | 0 |
| winners | 2013-2016 | allon | team1 | 2 | 8 | 0 | 6.559 | 0.8458 | 1.506 | 15.67 | 1 |
| winners | 2014-2017 | allon | team1 | 2 | 8 | 0 | 4.121 | 1.31 | 2.311 | 6.421 | 0 |
| winners | 2015-2018 | allon | team1 | 2 | 8 | 0 | 1.488 | 1.406 | 2.697 | 1.986 | 0 |
| winners | 2011-2014 | allon | team1 | 2 |  | 0 | 1.538 | 1.028 | 2.19 | 2.528 | 0 |
| winners | 2012-2015 | allon | team1 | 2 |  | 0 | 2.459 | 0.5738 | 1.285 | 6.888 | 0 |
| winners | 2013-2016 | allon | team1 | 2 |  | 0 | 6.559 | 0.8458 | 1.506 | 15.67 | 1 |
| winners | 2014-2017 | allon | team1 | 2 |  | 0 | 4.121 | 1.31 | 2.311 | 6.421 | 0 |
| winners | 2015-2018 | allon | team1 | 2 |  | 0 | 1.488 | 1.406 | 2.697 | 1.986 | 0 |
| winners | 2011-2014 | allon | team2 | 2 | 0.5 | 313 | 1.019 | 0.9764 | 2.387 | 1.537 | 0 |
| winners | 2012-2015 | allon | team2 | 2 | 0.5 | 232 | 3.383 | 0.8606 | 1.775 | 6.862 | 0 |
| winners | 2013-2016 | allon | team2 | 2 | 0.5 | 631 | 7.667 | 0.9242 | 1.466 | 18.82 | 1 |
| winners | 2014-2017 | allon | team2 | 2 | 0.5 | 560 | 1.917 | 1.402 | 2.365 | 2.917 | 0 |
| winners | 2015-2018 | allon | team2 | 2 | 0.5 | 455 | -0.2467 | 1.728 | 3.104 | -0.2861 | 0 |
| winners | 2011-2014 | allon | team2 | 2 | 0.75 | 123 | 1.529 | 1.392 | 2.97 | 1.853 | 0 |
| winners | 2012-2015 | allon | team2 | 2 | 0.75 | 44 | 3.723 | 0.8606 | 1.922 | 6.975 | 0 |
| winners | 2013-2016 | allon | team2 | 2 | 0.75 | 192 | 9.597 | 1.118 | 1.875 | 18.43 | 1 |
| winners | 2014-2017 | allon | team2 | 2 | 0.75 | 507 | 3.005 | 1.731 | 2.865 | 3.777 | 0 |
| winners | 2015-2018 | allon | team2 | 2 | 0.75 | 455 | 0.276 | 1.921 | 3.655 | 0.2719 | 0 |
| winners | 2011-2014 | allon | team2 | 2 | 1 | 26 | 2.08 | 1.542 | 3.275 | 2.286 | 0 |
| winners | 2012-2015 | allon | team2 | 2 | 1 | 7 | 3.689 | 0.8606 | 1.928 | 6.888 | 0 |
| winners | 2013-2016 | allon | team2 | 2 | 1 | 74 | 9.906 | 1.23 | 2.093 | 17.04 | 1 |
| winners | 2014-2017 | allon | team2 | 2 | 1 | 325 | 4.02 | 1.737 | 3.09 | 4.684 | 0 |
| winners | 2015-2018 | allon | team2 | 2 | 1 | 98 | 0.8383 | 2.109 | 4.199 | 0.7188 | 0 |
| winners | 2011-2014 | allon | team2 | 2 | 1.25 | 0 | 2.306 | 1.542 | 3.285 | 2.528 | 0 |
| winners | 2012-2015 | allon | team2 | 2 | 1.25 | 1 | 3.689 | 0.8606 | 1.928 | 6.888 | 0 |
| winners | 2013-2016 | allon | team2 | 2 | 1.25 | 48 | 9.825 | 1.278 | 2.238 | 15.81 | 1 |
| winners | 2014-2017 | allon | team2 | 2 | 1.25 | 93 | 4.641 | 1.84 | 3.198 | 5.224 | 0 |
| winners | 2015-2018 | allon | team2 | 2 | 1.25 | 98 | 1.624 | 2.109 | 4.102 | 1.425 | 0 |
| winners | 2011-2014 | allon | team2 | 2 | 1.5 | 0 | 2.306 | 1.542 | 3.285 | 2.528 | 0 |
| winners | 2012-2015 | allon | team2 | 2 | 1.5 | 1 | 3.689 | 0.8606 | 1.928 | 6.888 | 0 |
| winners | 2013-2016 | allon | team2 | 2 | 1.5 | 0 | 9.838 | 1.269 | 2.26 | 15.67 | 1 |
| winners | 2014-2017 | allon | team2 | 2 | 1.5 | 89 | 5.258 | 1.947 | 3.292 | 5.75 | 0 |
| winners | 2015-2018 | allon | team2 | 2 | 1.5 | 9 | 2.232 | 2.109 | 4.045 | 1.986 | 0 |
| winners | 2011-2014 | allon | team2 | 2 | 1.75 | 0 | 2.306 | 1.542 | 3.285 | 2.528 | 0 |
| winners | 2012-2015 | allon | team2 | 2 | 1.75 | 0 | 3.689 | 0.8606 | 1.928 | 6.888 | 0 |
| winners | 2013-2016 | allon | team2 | 2 | 1.75 | 0 | 9.838 | 1.269 | 2.26 | 15.67 | 1 |
| winners | 2014-2017 | allon | team2 | 2 | 1.75 | 39 | 5.826 | 1.965 | 3.36 | 6.242 | 0 |
| winners | 2015-2018 | allon | team2 | 2 | 1.75 | 9 | 2.232 | 2.109 | 4.045 | 1.986 | 0 |
| winners | 2011-2014 | allon | team2 | 2 | 2 | 0 | 2.306 | 1.542 | 3.285 | 2.528 | 0 |
| winners | 2012-2015 | allon | team2 | 2 | 2 | 0 | 3.689 | 0.8606 | 1.928 | 6.888 | 0 |
| winners | 2013-2016 | allon | team2 | 2 | 2 | 0 | 9.838 | 1.269 | 2.26 | 15.67 | 1 |
| winners | 2014-2017 | allon | team2 | 2 | 2 | 15 | 6.167 | 1.965 | 3.385 | 6.558 | 0 |
| winners | 2015-2018 | allon | team2 | 2 | 2 | 0 | 2.232 | 2.109 | 4.045 | 1.986 | 0 |
| winners | 2011-2014 | allon | team2 | 2 | 2.5 | 0 | 2.306 | 1.542 | 3.285 | 2.528 | 0 |
| winners | 2012-2015 | allon | team2 | 2 | 2.5 | 0 | 3.689 | 0.8606 | 1.928 | 6.888 | 0 |
| winners | 2013-2016 | allon | team2 | 2 | 2.5 | 0 | 9.838 | 1.269 | 2.26 | 15.67 | 1 |
| winners | 2014-2017 | allon | team2 | 2 | 2.5 | 8 | 6.205 | 1.965 | 3.445 | 6.485 | 0 |
| winners | 2015-2018 | allon | team2 | 2 | 2.5 | 0 | 2.232 | 2.109 | 4.045 | 1.986 | 0 |
| winners | 2011-2014 | allon | team2 | 2 | 3 | 0 | 2.306 | 1.542 | 3.285 | 2.528 | 0 |
| winners | 2012-2015 | allon | team2 | 2 | 3 | 0 | 3.689 | 0.8606 | 1.928 | 6.888 | 0 |
| winners | 2013-2016 | allon | team2 | 2 | 3 | 0 | 9.838 | 1.269 | 2.26 | 15.67 | 1 |
| winners | 2014-2017 | allon | team2 | 2 | 3 | 0 | 6.182 | 1.965 | 3.466 | 6.421 | 0 |
| winners | 2015-2018 | allon | team2 | 2 | 3 | 0 | 2.232 | 2.109 | 4.045 | 1.986 | 0 |
| winners | 2011-2014 | allon | team2 | 2 | 4 | 0 | 2.306 | 1.542 | 3.285 | 2.528 | 0 |
| winners | 2012-2015 | allon | team2 | 2 | 4 | 0 | 3.689 | 0.8606 | 1.928 | 6.888 | 0 |
| winners | 2013-2016 | allon | team2 | 2 | 4 | 0 | 9.838 | 1.269 | 2.26 | 15.67 | 1 |
| winners | 2014-2017 | allon | team2 | 2 | 4 | 0 | 6.182 | 1.965 | 3.466 | 6.421 | 0 |
| winners | 2015-2018 | allon | team2 | 2 | 4 | 0 | 2.232 | 2.109 | 4.045 | 1.986 | 0 |
| winners | 2011-2014 | allon | team2 | 2 | 5 | 0 | 2.306 | 1.542 | 3.285 | 2.528 | 0 |
| winners | 2012-2015 | allon | team2 | 2 | 5 | 0 | 3.689 | 0.8606 | 1.928 | 6.888 | 0 |
| winners | 2013-2016 | allon | team2 | 2 | 5 | 0 | 9.838 | 1.269 | 2.26 | 15.67 | 1 |
| winners | 2014-2017 | allon | team2 | 2 | 5 | 0 | 6.182 | 1.965 | 3.466 | 6.421 | 0 |
| winners | 2015-2018 | allon | team2 | 2 | 5 | 0 | 2.232 | 2.109 | 4.045 | 1.986 | 0 |
| winners | 2011-2014 | allon | team2 | 2 | 6 | 0 | 2.306 | 1.542 | 3.285 | 2.528 | 0 |
| winners | 2012-2015 | allon | team2 | 2 | 6 | 0 | 3.689 | 0.8606 | 1.928 | 6.888 | 0 |
| winners | 2013-2016 | allon | team2 | 2 | 6 | 0 | 9.838 | 1.269 | 2.26 | 15.67 | 1 |
| winners | 2014-2017 | allon | team2 | 2 | 6 | 0 | 6.182 | 1.965 | 3.466 | 6.421 | 0 |
| winners | 2015-2018 | allon | team2 | 2 | 6 | 0 | 2.232 | 2.109 | 4.045 | 1.986 | 0 |
| winners | 2011-2014 | allon | team2 | 2 | 8 | 0 | 2.306 | 1.542 | 3.285 | 2.528 | 0 |
| winners | 2012-2015 | allon | team2 | 2 | 8 | 0 | 3.689 | 0.8606 | 1.928 | 6.888 | 0 |
| winners | 2013-2016 | allon | team2 | 2 | 8 | 0 | 9.838 | 1.269 | 2.26 | 15.67 | 1 |
| winners | 2014-2017 | allon | team2 | 2 | 8 | 0 | 6.182 | 1.965 | 3.466 | 6.421 | 0 |
| winners | 2015-2018 | allon | team2 | 2 | 8 | 0 | 2.232 | 2.109 | 4.045 | 1.986 | 0 |
| winners | 2011-2014 | allon | team2 | 2 |  | 0 | 2.306 | 1.542 | 3.285 | 2.528 | 0 |
| winners | 2012-2015 | allon | team2 | 2 |  | 0 | 3.689 | 0.8606 | 1.928 | 6.888 | 0 |
| winners | 2013-2016 | allon | team2 | 2 |  | 0 | 9.838 | 1.269 | 2.26 | 15.67 | 1 |
| winners | 2014-2017 | allon | team2 | 2 |  | 0 | 6.182 | 1.965 | 3.466 | 6.421 | 0 |
| winners | 2015-2018 | allon | team2 | 2 |  | 0 | 2.232 | 2.109 | 4.045 | 1.986 | 0 |


## Provenance

- `results/r2reads/modeA_a4_currency_legs.csv` — 40 rows, md5 `8a97a6ab3fe1`
- `results/r2reads/modeA_a4_summary.csv` — 5 rows, md5 `e76b4c066651`
- `results/r2reads/modeA_a4_attribution.csv` — 10 rows, md5 `69f69c8f8373`
- `results/r2reads/modeA_a4_capsweep.csv` — 140 rows, md5 `cce79267ece7`
- `results/r2reads/modeA_a4_capcurve.csv` — 14 rows, md5 `d50d22be43bf`
- `results/r2reads/modeB_a4_currency_legs.csv` — 40 rows, md5 `ecbf022a6e85`
- `results/r2reads/modeB_a4_summary.csv` — 5 rows, md5 `1cc1e39ec89b`
- `results/r2reads/modeB_a4_attribution.csv` — 10 rows, md5 `6e38663712e6`
- `results/r2reads/modeB_a4_capsweep.csv` — 140 rows, md5 `f0f7d8bb0ac9`
- `results/r2reads/modeB_a4_capcurve.csv` — 14 rows, md5 `24bfc5f1fd68`
