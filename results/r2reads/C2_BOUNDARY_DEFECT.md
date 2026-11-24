# C2 — THE BOUNDARY-FADE STRATEGY: A DEFECT REPORT AGAINST THE PRODUCER

Generated 2026-11-24 10:37 by hand from `LAYER1_INTERFACE.md` and `results/layer1_states.csv`.


## The question, and the answer

Jack, 24 Nov: *"read LAYER1_INTERFACE.md, report whether the range boundary levels are exposed. If yes, build at most 3 declared variants of the boundary-fade strategy with random-entry and regime-shuffle nulls. If no, report the defect against the producer and stop there."*


**The answer is NO. No range boundary level is exposed, so nothing was built and this report stops at the defect.**


## What the interface actually exposes

`LAYER1_INTERFACE.md` §1 names `results/layer1_states.csv` as "THE interface". Its 14 columns, verified against the file itself and not against the document:


| # | column | is it a price level? |
|---:|---|---|
| 1 | `date` | no — a timestamp |
| 2 | `pair` | no — a label |
| 3 | `trend_score` | no — a dimensionless axis |
| 4 | `chop_score` | no — a dimensionless axis |
| 5 | `shape2` | no — a 2x2 label |
| 6 | `activity` | no — a tier label |
| 7 | `scale_28` | no — the raw scale the tier is cut from |
| 8 | `combined2` | no — a composite label |
| 9 | `settling` | no — a boolean |
| 10 | `m_fail` | no — a count, 0 to 10 |
| 11 | `m_retr` | no — unbounded, -194.6 to +194.3 |
| 12 | `m_space` | no — -41.7 to +57.0, 504 distinct values |
| 13 | `m_panel` | no — a fraction, 0 to 0.77 |
| 14 | `sample` | no — is / holdout / sealed |

**Not one column is a price.** The boundary-fade strategy needs the price of the top and the bottom of the range, in the pair's own quote units, to place an entry and a stop against. There is nothing in the interface to place them against.


## Why the near misses are not substitutes

- **`shape2 == ranging`** marks 56,228 of 171,920 rows (32.7%) as range-bound. It says a range EXISTS. It does not say where its edges are.

- **`chop_score`** is an intensity on a dimensionless axis, higher meaning more range-bound. It is not a distance to anything.

- **`m_space`** is the closest-sounding name, and it is the clearest part of the defect. It ranges −41.7 to +57.0 over 504 distinct values. It might be room-to-move in some unit, or something else entirely — `LAYER1_INTERFACE.md` says only that `m_fail`, `m_retr`, `m_space` and `m_panel` are "the four mechanism reads behind the label", and gives no individual definition, no unit and no sign convention for any of them. **A column that cannot be interpreted cannot be consumed**, and guessing would put a made-up unit into a price calculation.


## The defect, stated against the producer

**DEFECT 1 — the range boundary levels are not exposed.** Layer 1 classifies a pair as ranging but publishes no price level for the range. Any consumer wanting to act at the edge of a range must either re-derive the boundary from price itself — which duplicates Layer 1's work outside Layer 1, with a second set of undeclared cuts — or not act. For the boundary-fade strategy specifically it is a hard block.


**DEFECT 2 — the four mechanism reads are undocumented.** `m_fail`, `m_retr`, `m_space` and `m_panel` are published on the interface with one shared sentence and no per-column definition, unit or sign convention. Interface columns that cannot be interpreted are not an interface. This is separable from defect 1 and is cheaper to fix.


## What would unblock it

Either of these, from the producer:

1. two new columns on `layer1_states.csv` giving the range high and the range low **in the pair's quote units**, lagged one bar like every other column, with the lookback that defines them stated; or

2. a definition of `m_space` precise enough to convert it into a price distance — its unit, its sign convention and what it is measured from.


Option 2 is the smaller ask and may already be satisfiable from the producing code without any new computation.


## Stopped here, as instructed

No variants were declared, no strategy was built, and no null was run. Building a boundary-fade on a boundary I had invented would have produced a result that looked like evidence and was not.


## Provenance

- `LAYER1_INTERFACE.md` — md5 `89aa4bab8f13`, dated 2026-11-16 in its own header
- `results/layer1_states.csv` — 171,920 rows, 28 pairs, 14 columns, md5 `0b48ed53b78a`
