# ITEM 4 — WHAT TEST SET THE RISK VALUES, AND WHAT IT CANNOT SUPPORT

Generated 2026-11-24 13:23. HANDOFF 0m.


## The short answer

**Only one of the four values was set by a test, and it is not one of the three Jack named.** The ATR *length* was swept and frozen by a pre-test. The stop multiple, the target multiple, the baseline distance and the one-candle rule were **declared as defaults and never swept at gate 1** — GAUNTLET.md says so in its own words.


## The one test on record

| | |
|---|---|
| file | `results/gate1_atr_pretest.csv` and `results/gate1_atr_choice.csv` |
| date | **15 August 2026, 20:23 and 20:24** (file mtime) |
| what was swept | **ATR length only**, 49 values from 2 to 50 |
| held fixed during it | RR 1:1.5, both plans, all 28 pairs, the picking window only |
| result | chosen **31**, raw best **31**, plateau **27-31**, plateau mean expectancy **0.01340 R** |
| rule applied | `raw winner (it sits inside the best plateau)` |
| curve spread | min 0.01107, max 0.01377, range **2.21 standard errors** |

**It swept ATR LENGTH. It did not sweep the stop multiple, the target multiple, the baseline distance or the one-candle rule.** Those were held at RR 1:1.5 *while* it ran.


## What GAUNTLET.md says about the risk numbers

From its own `## RISK` section:


> **Fixed forever, never swept, at any gate:** … two legs in the trend plan (50/50) … leg 2 moves to breakeven when leg 1 banks … entries fill at the close of the signal bar

>

> **Gate 1 defaults — the same in both plans:** reward:risk **1 : 1.5** — stop 1.0 × ATR, take-profit 1.5 × ATR … ATR length: **set by the pre-test below**

>

> Those four numbers … are **not tunable at gate 1**, and they are never tuned per-combination.


So the document itself distinguishes the ATR length, which a pre-test set, from RR 1:1.5, which was a **declared default**. The baseline distance (1.5 ATR) and the one-candle rule (off) are not in GAUNTLET.md at all — they are `l2engine.run()` defaults.


## Before or after fault 27, and under which fill

| question | answer |
|---|---|
| ran before or after fault 27? | **BEFORE.** The pre-test ran 15 Aug 2026; fault 27 — costs under-charged by the stop multiple — was found **23 Sep 2026** (`code/l2tune.py`, the FAULT #27 comment). So the pre-test was run with costs under-charged by a median 20% and a p90 of 46%. |
| under which ambiguous-bar fill? | **Stop-first**, necessarily: the hourly resolver did not exist until today (item 1). |
| does that invalidate the ATR choice? | Not obviously, but it is untested. The chosen length sits on a plateau whose whole range is **2.21 standard errors** wide, so the curve is nearly flat and a 20-46% cost error could plausibly move the argmax within that plateau without changing much. The honest statement is that the ATR length was chosen on a flat curve, with costs too low, under a biased fill. |

## The one piece of empirical support for 1.0 and 1.5 — and why it is weak

Gates 2 and 3 DO sweep these knobs per strategy: `atr_mult` over 31 values 1.00–1.50 and `tp_mult` over 41 values 1.00–3.00. On a 400-strategy sample of the mode A bank at step 1 the tuner chose:


| slice | `atr_mult` median | chose 1.00 | `tp_mult` median | chose 1.50 | n |
|---|---:|---:|---:|---:|---:|
| trend | 1.00 | **98%** | 1.50 | **100%** | 400 |
| chop | 1.00 | **99%** | 1.50 | **96%** | 398 |

**That near-unanimity is a warning, not a confirmation.** 1.00 is the **lower bound of the stop grid**. A tuner that saturates against a boundary is telling you the boundary is binding, not that it found an optimum — and HANDOFF records exactly this failure mode before `ACCT_OBJECTIVE` existed: "median stop fell 1.00 → 0.17×ATR and win rates fell to 16%". The grid floor at 1.00 is doing the work. The same applies to `tp_mult`: 1.50 is where the grid is densest around the declared default.


## What this means for the three variants

Jack instructed that his values remain the standard and are the main version, and that is how stage 1 R2 runs them. **I am not changing them.** But the citation he asked for does not exist in the form the question assumes, so the record should say:


- **`jack`** — stop 1.0 ATR, first target 1.5× the stop, baseline distance 1.5 ATR, one-candle off. **Declared defaults**, supported by a tuner that saturates at the grid floor. The main version.

- **`textbook`** — stop 1.5 ATR, half off at 1.0 ATR, baseline distance 1.0 ATR, one-candle on. **Canonical NNFX**, per 0c.

- **`flip_only`** — no risk plan, as the control.


Running the two plans side by side is the test that was never done. It is declared in advance, both plans are in `CANDIDATE_LEDGER.csv`, and no engine default is changed.


## Provenance

- `results/gate1_atr_pretest.csv` — 49 rows, mtime 2026-08-15 20:23, md5 `6316656fbd67`
- `results/gate1_atr_choice.csv` — 1 rows, mtime 2026-08-15 20:24, md5 `06950082e382`
- `GAUNTLET.md` `## RISK` and `## ATR LENGTH PRE-TEST` sections, md5 `26d16ac6d12f`
- fault 27 dated from the `FAULT #27 (23 Sep)` comment in `code/l2tune.py`
