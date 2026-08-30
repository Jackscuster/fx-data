# results/ MANIFEST

What each classifier output actually contains. Written by
`code/persist.py`. **Nothing in results/ is ever deleted or
overwritten** — superseded work stays readable under its original
name, and this file says what that name means.

## The four generations

| file | source column | shape | what it is |
|---|---|---|---|
| `states_g2_structural12.csv` | `restored from git f597f23` | 6916 x 28 | Structural generation 2: four shapes INCLUDING `broken` crossed with activity = 12 cells. NOT reproducible from current code; restored verbatim from history. |
| `states_g1_ninebox.csv` | `state_28` | 6870 x 28 | Nine-box, generation 1. Straightness x scale terciles at a 28-bar window. The 7 and 128 legs are in layer1_legacy.csv as state_7 and state_128. |
| `states_g3_shapescore9.csv` | `shape` | 6870 x 28 | Shape score, generation 3. One continuous trend-versus-range score cut at in-sample terciles into three shapes. Separates better than g4 (0.261 vs 0.104 on trending) but leaves 41% of days in an ambiguous middle. |
| `states_g4_twoscore4.csv` | `shape2` | 6870 x 28 | Two-score, generation 4, CURRENT. Trend and chop scored independently and classified on the pair: trending / ranging / trend-in-range / neither. The ambiguous share falls to 20%. |
| `states_g4_twoscore12.csv` | `combined2` | 6870 x 28 | Two-score crossed with activity, generation 4, CURRENT. Twelve cells, activity cut jointly with a 0.75 bump. |

## Older names that do not say what they hold

| file | what it ACTUALLY contains | superseded by |
|---|---|---|
| `nine_states.csv` | A **9-row summary table** of the generation-1 nine-box states — share, median run length and run count. It is NOT per-day labels and it does NOT hold four shape states. | `run_lengths.csv` for run statistics on every generation |
| `nine_tiers.csv` | Per-day tier labels for generation 1 — which of the three ribbon windows disagreed. Permutation p=0.257, never routed on. | nothing; the tier was dropped |
| `combined_states.csv` | Per-day generation-2 labels, wide format, 4 shapes including `broken` crossed with activity. | `states_g2_structural12.csv`, same data, named for its generation |
| `structure_states.csv` | Per-day generation-2 SHAPE only, before the activity cross. | `states_g2_structural12.csv` |
| `shape3_states.csv` | Per-day three-shape labels from the GATED version of generation 3, before it was replaced by the continuous score. | `states_g3_shapescore9.csv` |
| `layer1_states.csv` | The CURRENT interface — generation 4 only. | — |
| `layer1_legacy.csv` | Generations 1–3 as columns, kept so no earlier read is lost. | — |

## Reading any generation

```python
w = pd.read_csv('results/states_g4_twoscore4.csv',
                index_col=0, parse_dates=True)   # dates x pairs
```

Every value is already lagged one bar. Do not shift it again.


## Portfolio preview — `portfolio_preview.json` / `.csv` / `portfolio_corr.csv`

**PREVIEW, never a gate 4 result.** The crisis-excluded top 10 merged onto one
calendar at equal risk weight (1/N), normalised so the combined book risks the
same 1 R per trade as any single strategy. Gate 4 replaces this with real
weighting and the drop-one test.

| file | what it holds |
|---|---|
| `portfolio_preview.json` | the combined equity curve and the metric block; read by the app's Trades tab |
| `portfolio_preview.csv` | the same metrics, crisis-excluded and all-in side by side |
| `portfolio_corr.csv` | the 10x10 cross-strategy correlation of daily R |

R is booked on the EXIT date; holding overlap uses the entry-to-exit span. The
two are deliberately different and should not be reconciled.

Regenerate with `python code/l2portfolio.py`.
