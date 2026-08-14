# Which classifiers can be rebuilt, and which are gone

Written by `code/regenerate.py`. A variant counts as reproducible
only if current code rebuilds it AND the rebuild matches the
archived copy where one exists.

## The correction this file makes

16.4x said generation 2 was "not reproducible from current code".
That was too quick. What changed was the *pipeline path* —
`combined.layers()` stopped calling `structure.five_state` — but the
function itself is untouched and still on main. Calling it directly
rebuilds generation 2 exactly. **A rewired caller is not a deleted
function**, and only the second is genuinely lost.

## Audit

| variant | status | states | agreement with archive | what it is |
|---|---|---|---|---|
| `states_g1_ninebox_7.csv` | rebuilt | 9 | — no archive | Generation 1, fast ribbon leg. Nine-box at a 7-bar window. |
| `states_g1_ninebox.csv` | rebuilt | 9 | 100.000% | Generation 1, base. Straightness x scale terciles at 28 bars. |
| `states_g1_ninebox_128.csv` | rebuilt | 9 | — no archive | Generation 1, slow ribbon leg. Nine-box at a 128-bar window. |
| `states_g2_structural4.csv` | rebuilt | 4 | — no archive | Generation 2 SHAPE ONLY: trending / broken / range / drifting. The four states before the activity cross. 'broken' was never in the spec. |
| `states_g2_structural12.csv` | rebuilt | 12 | 100.000% | Generation 2 full: the four structural shapes crossed with activity. |
| `states_g3_gate3.csv` | rebuilt | 3 | — no archive | Generation 3a, the GATED three-shape read at swing width 6. Superseded by the continuous score because it left a residual. |
| `states_g3_shapescore9.csv` | rebuilt | 3 | 100.000% | Generation 3b, the continuous trend-vs-range score cut at terciles. |
| `states_g3_score_N6.csv` | rebuilt | 3 | — no archive | Generation 3b at a 35-bar lookback -- the fast leg of the shape ribbon. |
| `states_g3_score_N44.csv` | rebuilt | 3 | — no archive | Generation 3b at a 247-bar lookback -- the slow leg, and the only region where trend separation went positive. |
| `states_g4_twoscore4.csv` | rebuilt | 4 | 100.000% | Generation 4, CURRENT. The 2x2 on independent trend and chop scores. |
| `states_g4_twoscore12.csv` | rebuilt | 12 | 100.000% | Generation 4 crossed with activity, CURRENT. |
| `states_x_weighted3.csv` | rebuilt | 3 | — no archive | The original three-state weighted classifier (97.3% scale by variance). Predates the nine-box and is still on main. |
| `states_x_dwell1.csv` | rebuilt | 3 | — no archive | Generation 3b with NO confirmation dwell -- the flickering version, 3-bar median runs with 62% under five bars. |
| `states_x_dwell13.csv` | rebuilt | 3 | — no archive | Generation 3b at a 13-bar dwell -- past the point where states collapse. |

## Genuinely gone

**Nothing.** Every classifier variant built in this project rebuilds from code committed on `main`.

## Rule going forward

Nothing runs to `/tmp`. If a result is worth reporting it is
written to `results/` and committed. Stdout is for progress, not
for findings.
