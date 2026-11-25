# DRAWDOWN CONTROL — item 6c, Jack 25 November 2026

**What a drawdown control can and cannot do, before the numbers.** Item 5 measured the best book at 1.135% a year against a 12% target. **None of these controls adds return.** The most any of them can do is let the same return be taken at a larger size by shrinking the drawdown the sizing has to fit inside. That is a real gain and a bounded one, and it is the only thing this report is measuring.

## The four controls, and why each is causal

| control | what it does | swept over | causality |
|---|---|---|---|
| `steady_risk` | size inversely to the book's own trailing volatility, so the RISK is constant rather than the position size | lookback 10, 20, 40, 60, 120 bars | the volatility window ends at **t−1** (`.shift(1)`); sizing today from today's realised volatility would be sizing with the answer. Capped at 3x the median weight, declared, so a quiet stretch cannot size up without limit |
| `equity_pause` | stop trading for N days once the drawdown reaches X, then resume | X = 25/50/75/100% of the book's own binding dip, N = 5/10/20 days | one forward pass; the weight on day t is decided from equity through t−1, so a day cannot be paused because of its own loss |
| `kill_switch` | stop **permanently** at a drawdown of X | X = 50/75/100/150% of the binding dip | same forward pass |
| `crisis_sizing` | size f inside a crisis window, 1.0 outside | f = 0.75, 0.50, 0.25, 0.00 | the windows are **news-dated and forward-only** (`crisis.py`: event date to +15 days, never price), so this is knowable on the day and is not a volatility rule in disguise |

**A FAULT FOUND AND FIXED IN THE FIRST RUN OF THIS FILE, because it is the kind that looks like a result.** `equity_pause` measured the drawdown from the peak of the MANAGED equity. While paused the equity cannot recover, so the drawdown from the old peak stays above the threshold and the rule re-triggers on the first day back — forever. It showed up as the pause giving byte-identical numbers at 5, 10 and 20 days AND identical numbers to `kill_switch` at the same level. A pause that cannot end is not a pause. The peak now resets to the equity at resumption, so the drawdown clock restarts from where the book actually is.

## Book `A`

Baseline, no control: R **+39.874**, binding dip **35.125**, return per dip **1.135**, **1.135% a year** at the firm's limits.

| control | setting | R total | R/yr | binding dip | **R per dip** | worst day | days flat | **firm limits %/yr** | vs baseline |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `(none)` | off | +39.874 | +6.646 | 35.125 | **+1.135** | 3.732 | 0 | +1.135 | +0.0% |
| `steady_risk` | lookback 10 | +24.795 | +4.133 | 41.729 | **+0.594** | 6.712 | 0 | +0.594 | -47.7% |
| `steady_risk` | lookback 20 | +31.825 | +5.304 | 38.779 | **+0.821** | 6.480 | 0 | +0.821 | -27.7% |
| `steady_risk` | lookback 40 | +37.319 | +6.220 | 34.663 | **+1.077** | 5.456 | 0 | +1.077 | -5.2% |
| `steady_risk` | lookback 60 | +37.957 | +6.326 | 33.670 | **+1.127** | 5.214 | 0 | +1.127 | -0.7% |
| **`steady_risk`** | lookback 120 | +43.791 | +7.299 | 34.942 | **+1.253** | 4.828 | 0 | +1.253 | +10.4% |
| `equity_pause` | 25% of dip, 5 days | +39.763 | +6.627 | 35.047 | **+1.135** | 3.732 | 30 | +1.135 | -0.1% |
| **`equity_pause`** | 25% of dip, 10 days | +43.413 | +7.235 | 32.828 | **+1.322** | 3.732 | 60 | +1.322 | +16.5% |
| `equity_pause` | 25% of dip, 20 days | +34.858 | +5.810 | 34.309 | **+1.016** | 3.732 | 120 | +1.016 | -10.5% |
| `equity_pause` | 50% of dip, 5 days | +38.585 | +6.431 | 35.222 | **+1.095** | 3.732 | 5 | +1.095 | -3.5% |
| **`equity_pause`** | 50% of dip, 10 days | +41.097 | +6.849 | 34.926 | **+1.177** | 3.732 | 10 | +1.177 | +3.7% |
| **`equity_pause`** | 50% of dip, 20 days | +41.228 | +6.871 | 35.249 | **+1.170** | 3.732 | 20 | +1.170 | +3.0% |
| `equity_pause` | 75% of dip, 5 days | +39.874 | +6.646 | 35.125 | **+1.135** | 3.732 | 0 | +1.135 | +0.0% |
| `equity_pause` | 75% of dip, 10 days | +39.874 | +6.646 | 35.125 | **+1.135** | 3.732 | 0 | +1.135 | +0.0% |
| `equity_pause` | 75% of dip, 20 days | +39.874 | +6.646 | 35.125 | **+1.135** | 3.732 | 0 | +1.135 | +0.0% |
| `equity_pause` | 100% of dip, 5 days | +39.874 | +6.646 | 35.125 | **+1.135** | 3.732 | 0 | +1.135 | +0.0% |
| `equity_pause` | 100% of dip, 10 days | +39.874 | +6.646 | 35.125 | **+1.135** | 3.732 | 0 | +1.135 | +0.0% |
| `equity_pause` | 100% of dip, 20 days | +39.874 | +6.646 | 35.125 | **+1.135** | 3.732 | 0 | +1.135 | +0.0% |
| `kill_switch` | 50% of dip | -13.348 | -2.225 | 27.127 | **-0.492** | 3.732 | 1173 | -0.492 | -143.3% |
| `kill_switch` | 75% of dip | +39.874 | +6.646 | 35.125 | **+1.135** | 3.732 | 0 | +1.135 | +0.0% |
| `kill_switch` | 100% of dip | +39.874 | +6.646 | 35.125 | **+1.135** | 3.732 | 0 | +1.135 | +0.0% |
| `kill_switch` | 150% of dip | +39.874 | +6.646 | 35.125 | **+1.135** | 3.732 | 0 | +1.135 | +0.0% |
| `crisis_sizing` | size 0.75 in crisis | +37.247 | +6.208 | 35.036 | **+1.063** | 3.732 | 0 | +1.063 | -6.4% |
| `crisis_sizing` | size 0.50 in crisis | +34.620 | +5.770 | 34.767 | **+0.996** | 3.732 | 0 | +0.996 | -12.3% |
| `crisis_sizing` | size 0.25 in crisis | +31.993 | +5.332 | 35.069 | **+0.912** | 3.732 | 0 | +0.912 | -19.6% |
| `crisis_sizing` | size 0.00 in crisis | +29.366 | +4.894 | 35.672 | **+0.823** | 3.732 | 143 | +0.823 | -27.5% |

**4 of the 25 control settings improve return per dip by more than 1%.** `equity_pause` 25% of dip, 10 days -> +1.322 (+16.5%); `steady_risk` lookback 120 -> +1.253 (+10.4%); `equity_pause` 50% of dip, 10 days -> +1.177 (+3.7%); `equity_pause` 50% of dip, 20 days -> +1.170 (+3.0%)

## Book `A+B+MR120`

Baseline, no control: R **+27.438**, binding dip **36.580**, return per dip **0.750**, **0.750% a year** at the firm's limits.

| control | setting | R total | R/yr | binding dip | **R per dip** | worst day | days flat | **firm limits %/yr** | vs baseline |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `(none)` | off | +27.438 | +4.573 | 36.580 | **+0.750** | 2.695 | 0 | +0.750 | +0.0% |
| **`steady_risk`** | lookback 10 | +31.754 | +5.292 | 36.881 | **+0.861** | 3.830 | 0 | +0.861 | +14.8% |
| **`steady_risk`** | lookback 20 | +30.695 | +5.116 | 36.657 | **+0.837** | 3.289 | 0 | +0.837 | +11.6% |
| `steady_risk` | lookback 40 | +25.904 | +4.317 | 36.856 | **+0.703** | 2.704 | 0 | +0.703 | -6.3% |
| **`steady_risk`** | lookback 60 | +37.374 | +6.229 | 35.046 | **+1.066** | 2.547 | 0 | +1.066 | +42.2% |
| **`steady_risk`** | lookback 120 | +33.122 | +5.520 | 37.223 | **+0.890** | 2.595 | 0 | +0.890 | +18.6% |
| **`equity_pause`** | 25% of dip, 5 days | +29.300 | +4.883 | 35.813 | **+0.818** | 2.695 | 25 | +0.818 | +9.1% |
| **`equity_pause`** | 25% of dip, 10 days | +26.843 | +4.474 | 34.741 | **+0.773** | 2.695 | 50 | +0.773 | +3.0% |
| `equity_pause` | 25% of dip, 20 days | +16.925 | +2.821 | 36.489 | **+0.464** | 2.695 | 100 | +0.464 | -38.2% |
| `equity_pause` | 50% of dip, 5 days | +27.438 | +4.573 | 36.580 | **+0.750** | 2.695 | 0 | +0.750 | +0.0% |
| `equity_pause` | 50% of dip, 10 days | +27.438 | +4.573 | 36.580 | **+0.750** | 2.695 | 0 | +0.750 | +0.0% |
| `equity_pause` | 50% of dip, 20 days | +27.438 | +4.573 | 36.580 | **+0.750** | 2.695 | 0 | +0.750 | +0.0% |
| `equity_pause` | 75% of dip, 5 days | +27.438 | +4.573 | 36.580 | **+0.750** | 2.695 | 0 | +0.750 | +0.0% |
| `equity_pause` | 75% of dip, 10 days | +27.438 | +4.573 | 36.580 | **+0.750** | 2.695 | 0 | +0.750 | +0.0% |
| `equity_pause` | 75% of dip, 20 days | +27.438 | +4.573 | 36.580 | **+0.750** | 2.695 | 0 | +0.750 | +0.0% |
| `equity_pause` | 100% of dip, 5 days | +27.438 | +4.573 | 36.580 | **+0.750** | 2.695 | 0 | +0.750 | +0.0% |
| `equity_pause` | 100% of dip, 10 days | +27.438 | +4.573 | 36.580 | **+0.750** | 2.695 | 0 | +0.750 | +0.0% |
| `equity_pause` | 100% of dip, 20 days | +27.438 | +4.573 | 36.580 | **+0.750** | 2.695 | 0 | +0.750 | +0.0% |
| `kill_switch` | 50% of dip | +27.438 | +4.573 | 36.580 | **+0.750** | 2.695 | 0 | +0.750 | +0.0% |
| `kill_switch` | 75% of dip | +27.438 | +4.573 | 36.580 | **+0.750** | 2.695 | 0 | +0.750 | +0.0% |
| `kill_switch` | 100% of dip | +27.438 | +4.573 | 36.580 | **+0.750** | 2.695 | 0 | +0.750 | +0.0% |
| `kill_switch` | 150% of dip | +27.438 | +4.573 | 36.580 | **+0.750** | 2.695 | 0 | +0.750 | +0.0% |
| `crisis_sizing` | size 0.75 in crisis | +21.189 | +3.531 | 36.343 | **+0.583** | 2.695 | 0 | +0.583 | -22.3% |
| `crisis_sizing` | size 0.50 in crisis | +14.939 | +2.490 | 36.416 | **+0.410** | 2.695 | 0 | +0.410 | -45.3% |
| `crisis_sizing` | size 0.25 in crisis | +8.690 | +1.448 | 37.178 | **+0.234** | 2.695 | 0 | +0.234 | -68.8% |
| `crisis_sizing` | size 0.00 in crisis | +2.440 | +0.407 | 39.574 | **+0.062** | 2.695 | 156 | +0.062 | -91.8% |

**6 of the 25 control settings improve return per dip by more than 1%.** `steady_risk` lookback 60 -> +1.066 (+42.2%); `steady_risk` lookback 120 -> +0.890 (+18.6%); `steady_risk` lookback 10 -> +0.861 (+14.8%); `steady_risk` lookback 20 -> +0.837 (+11.6%); `equity_pause` 25% of dip, 5 days -> +0.818 (+9.1%)

## What it adds up to

1. **The best single control setting on the best book is `equity_pause` at "25% of dip, 10 days": return per dip 1.322 against 1.135, and 1.322% a year against 1.135%.** That is a **+16.5%** improvement — real, and it is the maximum over **25 swept cells on one six-year sample**, so treat it as an upper bound on what is there rather than as a setting to adopt.
2. **The curves are not monotone, which is the tell.** `equity_pause` at 25% of the dip gives no change at 5 days, its best result at 10 days and a WORSE result than baseline at 20. A control whose benefit turns over as its one knob moves by one notch is reading noise.
3. **The kill switch never fires above 50% of the dip, and the reason is a unit mismatch worth naming rather than a timing accident.** The levels are fractions of the **binding** dip, which is DIP95 at 35.125 R, while the drawdown the book actually took is 22.616 R — only 64% of it. So every level at 75% or above is a threshold the realised path never reaches, and 3 of the 4 kill settings are byte-identical to the baseline. The one that does fire, 50% of the binding dip (17.56 R), fires inside the first year — the worst drawdown bottoms on 11 March 2011, day 304 of 1,457 — and turns +39.874 R into -13.348 R. **A kill switch on this book is a way of losing the book.**
4. **Crisis sizing costs money monotonically.** Every step down in crisis size lowers both return and return per dip, and sizing to zero in crisis windows costs 26.4% of the total. The dip barely moves, because A's worst drawdown is not in a crisis window. On this book, crisis sizing buys nothing and pays for it.
5. **And none of it changes the verdict.** The best controlled book is 1.322% a year against a 12% target: still a factor of 9.1 short. A drawdown control was never going to close a gap of that size and this report does not pretend otherwise.

## Through the prop simulator

The baseline and the best cell of each control, at the Team 1 budget and at the firm's own limits.

| book | control | setting | sizing | %/yr | days to pass +10% | funded breach | payout $/yr | worst dip % | short of 12% by |
|---|---|---|---|---:|---|---|---:|---:|---:|
| A | `(none)` | off | team1 | +0.681% | **NEVER** | none | $843 | 2.49% | 11.319 pp |
| A | `(none)` | off | firm | +1.135% | **NEVER** | none | $1399 | 4.12% | 10.865 pp |
| A | `steady_risk` | lookback 120 | team1 | +0.752% | **NEVER** | none | $685 | 2.98% | 11.248 pp |
| A | `steady_risk` | lookback 120 | firm | +1.253% | **NEVER** | none | $1133 | 4.94% | 10.747 pp |
| A | `crisis_sizing` | size 0.75 in crisis | team1 | +0.638% | **NEVER** | none | $807 | 2.41% | 11.362 pp |
| A | `crisis_sizing` | size 0.75 in crisis | firm | +1.063% | **NEVER** | none | $1339 | 3.99% | 10.937 pp |
| A+B+MR120 | `(none)` | off | team1 | +0.450% | **NEVER** | none | $486 | 1.88% | 11.550 pp |
| A+B+MR120 | `(none)` | off | firm | +0.750% | **NEVER** | none | $804 | 3.12% | 11.250 pp |
| A+B+MR120 | `steady_risk` | lookback 60 | team1 | +0.640% | **NEVER** | none | $671 | 2.08% | 11.360 pp |
| A+B+MR120 | `steady_risk` | lookback 60 | firm | +1.066% | **NEVER** | none | $1111 | 3.45% | 10.934 pp |
| A+B+MR120 | `crisis_sizing` | size 0.75 in crisis | team1 | +0.350% | **NEVER** | none | $389 | 2.23% | 11.650 pp |
| A+B+MR120 | `crisis_sizing` | size 0.75 in crisis | firm | +0.583% | **NEVER** | none | $643 | 3.71% | 11.417 pp |

**No controlled book passes the +10%% evaluation either.** The controls move the sizing, not the return.

## Provenance

- `results/nnfx/dd_curves.csv` — 52 rows, md5 `7343b5085492`
- `results/nnfx/dd_prop.csv` — 12 rows, md5 `323368a60c25`
