# Crisis witnesses 2 and 3 - panel turbulence and Roll illiquidity

**2026-11-15.** Two additional WITNESSES beside the acute detector and MOVE. A witness confirms: it does not predict, it does not replace anything, and it never becomes a state. Source `results/research/RESEARCH_2026-11-09_*.md` (commit 9926531); code `code/witness.py`.

## What they are

**Panel turbulence (Kritzman-Li).** One number a day: the Mahalanobis distance of the day's return vector from its own trailing history, scaled by the trailing covariance - so a day is turbulent when the moves are big OR unusually combined. Covariance windows 250 and 500 bars, declared; built on the 7 USD legs (primary) and on all 28 pairs (secondary, partly redundant by triangulation).

**Roll illiquidity.** The effective-spread proxy from the negative autocovariance of successive daily price changes, closes only. Windows 20 and 60 bars, per pair plus the panel average. Where the autocovariance is positive the estimator is undefined; it is set to zero and **the share of undefined days is reported, because that share is itself a liquidity reading**:

| window | share_undefined_all | share_undefined_tuning | share_undefined_holdout |
|---|---|---|---|
| roll_20 | 0.4049 | 0.4067 | 0.4000 |
| roll_60 | 0.4359 | 0.4414 | 0.4212 |

## Calendar validation (crisis.py's, unchanged)

The 39 news-dated events inside the panel window, a FORWARD-ONLY window from the event date to +15 days that never opens before the event, firing at the 95th percentile learned on the tuning window.

| witness | caught | n_events | recall | base_rate | lift | false_alarm_rate_outside_windows | median_lag_days |
|---|---|---|---|---|---|---|---|
| ACUTE_maxabsmove | 31 | 39 | 0.795 | 0.053 | 15.006 | 0.044 | 0.000 |
| ACUTE_breadth2sig | 27 | 39 | 0.692 | 0.049 | 14.215 | 0.038 | 0.000 |
| turb_usd_250 | 25 | 39 | 0.641 | 0.046 | 13.975 | 0.034 | 1.000 |
| turb_all28_250 | 25 | 39 | 0.641 | 0.046 | 13.975 | 0.034 | 1.000 |
| turb_usd_500 | 24 | 39 | 0.615 | 0.044 | 13.956 | 0.031 | 1.000 |
| turb_all28_500 | 24 | 39 | 0.615 | 0.044 | 13.956 | 0.031 | 1.000 |
| roll_panel_20 | 9 | 39 | 0.231 | 0.039 | 5.921 | 0.031 | 4.000 |
| MOVE_rel | 8 | 39 | 0.205 | 0.042 | 4.864 | 0.035 | 1.000 |
| roll_panel_60 | 2 | 39 | 0.051 | 0.036 | 1.412 | 0.035 | 4.000 |

## The 200-draw re-derive null

| kind | witness | real_lift | null_mean | null_p95 | null_max | p_value |
|---|---|---|---|---|---|---|
| sign | turb_usd_250 | 13.975 | 14.959 | 15.962 | 16.532 | 0.980 |
| sign | turb_all28_250 | 13.975 | 13.736 | 14.676 | 15.468 | 0.390 |
| sign | turb_usd_500 | 13.956 | 12.738 | 13.664 | 14.616 | 0.015 |
| sign | turb_all28_500 | 13.956 | 13.572 | 14.461 | 15.039 | 0.255 |
| sign | roll_panel_20 | 5.921 | 5.729 | 7.895 | 8.227 | 0.450 |
| sign | roll_panel_60 | 1.412 | 2.562 | 3.831 | 4.885 | 0.950 |
| perm | turb_usd_250 | 13.975 | 8.243 | 11.064 | 13.026 | 0.000 |
| perm | turb_all28_250 | 13.975 | 8.165 | 10.521 | 12.229 | 0.000 |
| perm | turb_usd_500 | 13.956 | 7.751 | 10.493 | 11.317 | 0.000 |
| perm | turb_all28_500 | 13.956 | 7.703 | 9.888 | 10.974 | 0.000 |
| perm | roll_panel_20 | 5.921 | 2.669 | 4.751 | 6.852 | 0.015 |
| perm | roll_panel_60 | 1.412 | 1.855 | 3.769 | 6.354 | 0.625 |

## The incremental question - what decides keep or kill

| witness | caught | caught_that_acute_misses | overlap_with_acute | caught_that_move_misses | overlap_with_move | unique_to_this_witness |
|---|---|---|---|---|---|---|
| turb_usd_250 | 25 | 0 | 1.000 | 17 | 0.320 | 0 |
| turb_all28_250 | 25 | 0 | 1.000 | 17 | 0.320 | 0 |
| turb_usd_500 | 24 | 0 | 1.000 | 17 | 0.292 | 0 |
| turb_all28_500 | 24 | 0 | 1.000 | 17 | 0.292 | 0 |
| roll_panel_20 | 9 | 0 | 1.000 | 3 | 0.667 | 0 |
| roll_panel_60 | 2 | 0 | 1.000 | 0 | 1.000 | 0 |

## Sub-period split, 2016-2019 vs 2020

| witness | period | caught | n_events | recall | lift |
|---|---|---|---|---|---|
| turb_usd_250 | 2016-2019 | 5 | 7 | 0.714 | 14.217 |
| turb_all28_250 | 2016-2019 | 5 | 7 | 0.714 | 14.217 |
| turb_usd_500 | 2016-2019 | 4 | 7 | 0.571 | 11.374 |
| turb_all28_500 | 2016-2019 | 4 | 7 | 0.571 | 11.374 |
| roll_panel_20 | 2016-2019 | 1 | 7 | 0.143 | 2.843 |
| roll_panel_60 | 2016-2019 | 1 | 7 | 0.143 | 2.843 |
| ACUTE_maxabsmove | 2016-2019 | 5 | 7 | 0.714 | 14.217 |
| ACUTE_breadth2sig | 2016-2019 | 5 | 7 | 0.714 | 17.602 |
| MOVE_rel | 2016-2019 | 1 | 7 | 0.143 | 2.843 |
| turb_usd_250 | 2020 | 3 | 3 | 1.000 | 20.000 |
| turb_all28_250 | 2020 | 3 | 3 | 1.000 | 20.000 |
| turb_usd_500 | 2020 | 3 | 3 | 1.000 | 20.000 |
| turb_all28_500 | 2020 | 3 | 3 | 1.000 | 20.000 |
| roll_panel_20 | 2020 | 3 | 3 | 1.000 | 20.000 |
| roll_panel_60 | 2020 | 3 | 3 | 1.000 | 20.000 |
| ACUTE_maxabsmove | 2020 | 3 | 3 | 1.000 | 20.000 |
| ACUTE_breadth2sig | 2020 | 3 | 3 | 1.000 | 21.667 |
| MOVE_rel | 2020 | 3 | 3 | 1.000 | 20.000 |

