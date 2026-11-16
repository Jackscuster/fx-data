# Layer 1 trend round 3 - is there a quality flag on the trend label?

**2026-11-11.** One question, asked once: can anything ALREADY COMMITTED separate a TRUE trending episode from a FALSE one AT LABEL TIME? Round 2 measured the problem - about half of all labelled trending episodes are directionless and the shipped trend score cannot tell them apart (on the holdout the false ones score HIGHER). This is a quality flag on the existing label: no new axis, no new state, no state call changes, and no money metric anywhere in the run. Code `code/trendqual.py`.

## The menu, declared before any result

Five existing series read at the confirmation bar from bars <= t-1. No sweeps, no combinations, no interactions. A5 is the control and is expected to fail.

- **A1** activity level (the scale measure the activity axis is cut from)
- **A2** chop score (shipped, raw)
- **A3** currency-leg gap (round 2 T2 series - failed as an AXIS; whether it works as a CONDITIONAL read is a different question, asked once here)
- **A4** boundary-break follow-through (round 2 T1 series at the already-selected R=5)
- **A5** trend score - THE CONTROL

Episodes: **725 tuning, 271 holdout**; true-trend share 0.501 / 0.472; truth threshold 0.503 learned on the tuning window. One episode is one observation throughout.

## The readings

| candidate | gap_tuning | auc_tuning | gap_holdout | auc_holdout | n_episodes_holdout | sign_consistent |
|---|---|---|---|---|---|---|
| A1_activity_scale | 0.1232 | 0.5342 | 0.1326 | 0.4598 | 271 | False |
| A2_chop_score | 0.0191 | 0.4980 | 0.0693 | 0.4827 | 271 | True |
| A3_currency_leg_gap | 0.2319 | 0.5595 | 0.3944 | 0.6089 | 271 | True |
| A4_break_followthrough | 0.0692 | 0.5187 | 0.0628 | 0.4806 | 261 | True |
| A5_trend_score_CONTROL | 0.0126 | 0.4927 | 0.0151 | 0.4857 | 271 | True |

gap = |mean(true) - mean(false)| in sd units of the reading; AUC 0.5 is a coin flip. **A5, the control, behaved exactly as predicted** - the trend score carries no information about whether its own label will be real.

## The 200-draw re-derive null (`trend_quality_null_2026-11-11.csv`)

The same null that killed the DC axis, T1 and T2: on every surrogate the two-score classifier, the episode set, the truth threshold and all five readings are rebuilt from scratch, so it prices the whole question rather than one step of it.

| kind | candidate | real | null_mean | null_p95 | null_max | corrected | p_value |
|---|---|---|---|---|---|---|---|
| sign | A1_activity_scale | 0.1326 | 0.1053 | 0.2521 | 0.3481 | 0.0274 | 0.2850 |
| sign | A2_chop_score | 0.0693 | 0.1101 | 0.2672 | 0.4964 | -0.0408 | 0.6300 |
| sign | A3_currency_leg_gap | 0.3944 | 0.1346 | 0.2987 | 0.4671 | 0.2598 | 0.0100 |
| sign | A4_break_followthrough | 0.0628 | 0.1020 | 0.2530 | 0.3387 | -0.0391 | 0.6400 |
| sign | A5_trend_score_CONTROL | 0.0151 | 0.0978 | 0.2337 | 0.3339 | -0.0827 | 0.9250 |
| perm | A1_activity_scale | 0.1326 | 0.0854 | 0.2195 | 0.3374 | 0.0472 | 0.2200 |
| perm | A2_chop_score | 0.0693 | 0.1076 | 0.2445 | 0.3660 | -0.0383 | 0.6300 |
| perm | A3_currency_leg_gap | 0.3944 | 0.0943 | 0.2406 | 0.3341 | 0.3001 | 0.0000 |
| perm | A4_break_followthrough | 0.0628 | 0.0922 | 0.2329 | 0.3941 | -0.0293 | 0.5800 |
| perm | A5_trend_score_CONTROL | 0.0151 | 0.1005 | 0.2558 | 0.3496 | -0.0855 | 0.8850 |

## Sub-period split, 2016-2019 vs 2020 (2021+ sealed)

| candidate | period | gap | auc | n_episodes |
|---|---|---|---|---|
| A1_activity_scale | 2016-2019 | 0.1150 | 0.4617 | 212 |
| A1_activity_scale | 2020 | 0.2100 | 0.4482 | 59 |
| A2_chop_score | 2016-2019 | 0.0927 | 0.4918 | 212 |
| A2_chop_score | 2020 | 0.0412 | 0.4735 | 59 |
| A3_currency_leg_gap | 2016-2019 | 0.3581 | 0.5968 | 212 |
| A3_currency_leg_gap | 2020 | 0.5923 | 0.6659 | 59 |
| A4_break_followthrough | 2016-2019 | 0.2485 | 0.4300 | 203 |
| A4_break_followthrough | 2020 | 0.4174 | 0.6278 | 58 |
| A5_trend_score_CONTROL | 2016-2019 | 0.0509 | 0.4801 | 212 |
| A5_trend_score_CONTROL | 2020 | 0.0961 | 0.5092 | 59 |

## Verdict

| candidate | gap_holdout | auc_holdout | sign_consistent | null_p_sign | null_p_perm | survives |
|---|---|---|---|---|---|---|
| A1_activity_scale | 0.1326 | 0.4598 | False | 0.2850 | 0.2200 | False |
| A2_chop_score | 0.0693 | 0.4827 | True | 0.6300 | 0.6300 | False |
| A3_currency_leg_gap | 0.3944 | 0.6089 | True | 0.0100 | 0.0000 | True |
| A4_break_followthrough | 0.0628 | 0.4806 | True | 0.6400 | 0.5800 | False |
| A5_trend_score_CONTROL | 0.0151 | 0.4857 | True | 0.9250 | 0.8850 | False |

**Survivors: A3_currency_leg_gap.** Each becomes a reported QUALITY reading beside the trend label (high / low confidence trend). No state call changes and the flag never gates a trade on its own.

_Files: `trend_quality_{episodes,battery,null,subperiod,verdict}_2026-11-11.{csv,txt}`._
