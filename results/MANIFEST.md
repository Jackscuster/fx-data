# results/ MANIFEST

What each classifier output actually contains. Written by
`code/persist.py`. **Nothing in results/ is ever deleted or
overwritten** — superseded work stays readable under its original
name, and this file says what that name means.

## The four generations

| file | source column | shape | what it is |
|---|---|---|---|
| `states_g2_structural12.csv` | `restored from git f597f23` | 6916 x 28 | Structural generation 2: four shapes INCLUDING `broken` crossed with activity = 12 cells. NOT reproducible from current code; restored verbatim from history. |
| `states_g1_ninebox.csv` | `state_28` | 6855 x 28 | Nine-box, generation 1. Straightness x scale terciles at a 28-bar window. The 7 and 128 legs are in layer1_legacy.csv as state_7 and state_128. |
| `states_g3_shapescore9.csv` | `shape` | 6855 x 28 | Shape score, generation 3. One continuous trend-versus-range score cut at in-sample terciles into three shapes. Separates better than g4 (0.261 vs 0.104 on trending) but leaves 41% of days in an ambiguous middle. |
| `states_g4_twoscore4.csv` | `shape2` | 6855 x 28 | Two-score, generation 4, CURRENT. Trend and chop scored independently and classified on the pair: trending / ranging / trend-in-range / neither. The ambiguous share falls to 20%. |
| `states_g4_twoscore12.csv` | `combined2` | 6855 x 28 | Two-score crossed with activity, generation 4, CURRENT. Twelve cells, activity cut jointly with a 0.75 bump. |

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

---

# LAYER 2 — GATE 1

## The number of record

**Gate 1's survivor rate against chance is `ratio_to_null` in
`results/gate1_summary.csv`. Nothing else is canonical.**

| slice | pass rate | null | **ratio (canonical)** |
|---|---|---|---|
| trend | 7.1758% | 6.4735% | **1.108×** |
| chop | 2.3408% | 6.1063% | **0.383×** |

**A ratio of 1.43× (trend) or 0.47× (chop) appears in commit `f9e2b6f` and in
chat before it. Those are superseded and must not be quoted.** They divided by
a null of 5.00%, which was measured by scoring the floor-setting controls
against their own 95th percentile — 5% by construction, not by evidence. The
canonical null is measured on fresh controls against the frozen floor.

## The two null files, and why both are kept

| file | what it ACTUALLY contains | status |
|---|---|---|
| `gate1_null_fresh.csv` | The null pass rate on 31,822 trend / 26,088 chop **fresh** controls — new seed, new combination sample — scored against the frozen floor. Carries `se_pct` and a 95% CI. | **CANONICAL.** This is the null. |
| `gate1_null_joint.csv` | The same test run on the controls that SET the floor. Its `null_joint_pct` of 5.0037 / 5.0136 is circular and is not a null estimate. | Superseded as a null. Kept because its other finding stands: `null_joint_pct` equals `null_exp_only_pct` exactly, i.e. **`PF >= 1.05` is non-binding** — no control clearing the expectancy floor fails it. `gate1_null_fresh.csv` reconfirms that on independent data. |
| `gate1_null_raw.csv` | Per-control expectancy and profit factor for the floor-setting set. The evidence behind the PF finding. | Current. |

## Gate 1 outputs

| file | what it contains |
|---|---|
| `gate1_summary.csv` | Per-slice counts, pass rate, canonical null, expected-from-noise, excess, ratio. **The headline record.** |
| `gate1_luck_floor.csv` | The frozen expectancy floors gate 1 gated on. Never regenerate: gate 1 has run against these exact numbers. |
| `gate1_atr_pretest.csv`, `gate1_atr_choice.csv` | The ATR length pre-test and the frozen choice of 31. |
| `gate1_enrichment_slots.csv`, `gate1_enrichment_cores.csv` | Survivor structure — per-option and per-C1×baseline enrichment. **Tuning priority only, never a cut** (GAUNTLET.md is amended: no family-based cuts at any gate). Denominator is ALL combinations, so these fold trade frequency together with edge. |
| `gate1_survivors.csv`, `gate1/` | **Not in the repo** — 224 MB and 217 MB, gitignored. Regenerate with `python code/l2sweep.py --shards 128 --jobs 8`, which reuses any shard checkpoints present. |
