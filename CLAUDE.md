# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Read first

- **`HANDOFF_3.md`** — the full project handoff: what the estimator is, what has been
  tested, what was learned, and how Jack works. Read it before any substantive change.
  Its §11 lists bugs already hit; §12 lists what is unfinished.
- **`FIXES.md`** — the current work backlog, in order.
- **`STRATEGY_TEMPLATE.md`** — the mandatory output format for any strategy result.

## What this is

A **regime estimator** for FX: it classifies a pair as TREND, CHOP or CRISIS. It is the
root node of a decision tree — strategy sleeves get capital based on what it says.
**The deliverable is the estimator, not PnL.** Do not drift into strategy testing unless
asked.

## Commands

```bash
pip install -r requirements.txt

python code/pipeline.py      # full rebuild in order; ~3 min warm, ~40 min cold
python code/build.py         # fetch H.10 data -> data/px28.csv, with sanity asserts
python code/prep.py          # pool all score dirs -> results/signals.json
python code/bundle.py        # results/*.csv + signals.json -> results/app_data.json
```

Any script under `code/` runs standalone — each begins with the same five-line preamble
that resolves repo root and puts `code/` on the path, so `python code/<x>.py` works from
anywhere.

**There is no test suite.** Correctness is enforced by assertions inside the pipeline:
- `build.py` asserts EURUSD peak 1.601 and USDCHF low 0.7296. If these fail the data
  rebuild is wrong — stop, do not "fix" the threshold.
- `framework.py` asserts 20/20 look-ahead spot-checks pass and halts the run otherwise.
- `events.py` asserts its calendar is sorted and free of duplicate dates.

To check a single piece, run its module directly (`python code/crisis.py`,
`python code/ladder.py`) — each prints its own results table and writes its CSV.

## Architecture

**Data.** `build.py` pulls Fed H.10 daily FX. The source is uniformly *foreign-per-USD,
including EUR/GBP/AUD/NZD* — invert everything with `1/x`, then triangulate into 28 pairs
from the G8 in base-priority order EUR GBP AUD NZD USD CAD CHF JPY. An earlier attempt
assumed those four were already inverted and produced garbage. Close-only: no OHLC, so no
true range or ATR.

**Signals → scores → pooling.** `sig2..sig5.py` build signal families; `sc2..sc5.py` score
them, writing **one `.npz` per pair** into `results/scores*/`. Scorers are **resumable and
idempotent** — they skip any pair that already has a `.npz`, which is why a rebuild is 3
minutes rather than 45. `prep.py` pools every score dir into `results/signals.json`.

**The npz key convention is the sharp edge here.** `sc2`–`sc4` write a single target as
`qi/ni/vi/qo/no/vo`. `sc5` writes **two** targets: `qt*/nt*/vt*` (forward 20-day
efficiency) and `qc*/nc*/vc*` (forward 20-day turn frequency). `prep.py` probes
`z.files` and falls back. **Any new multi-target scorer must either match the old naming
or update `prep.py`.**

**Analysis layer.** `strat.py` (config sweep), `framework.py` (look-ahead audit, durations,
three logics, DSR), `ladder.py` (detectors as filters), `funnel.py` (DSR attrition),
`crisis.py` + `events.py` (news-validated crisis detection), `ninebox.py` (3×3 direction ×
volatility), `mtf.py` (monthly/weekly/daily confluence). Each writes a CSV into `results/`.

**Delivery.** `bundle.py` reads `results/signals.json` **and writes `results/app_data.json`**
— it must never read and write the same file (it once nested the signals section inside
itself). `pipeline.py` then copies `results/app_data.json` to the repo root, which is what
the app actually fetches. Editing `bundle.py` alone leaves the root copy stale.

**The app** is a thin shell HTML on Jack's machine that fetches *both* `app_data.json` and
`app_ui.js` from this repo. **New tabs go in `app_ui.js`; he never redownloads the app.**
GitHub serves `.js` as `text/plain` with `nosniff`, so a `<script src>` tag is blocked —
the shell fetches `app_ui.js` as text and evals it. Do not "fix" this back to a script tag.
A syntax error in `app_ui.js` blanks the entire interface, so check it with
`node --check app_ui.js`.

## Method invariants

These are not style preferences. Breaking one invalidates the result.

- **Every signal is lagged one bar via `.shift(1)`.** Non-negotiable.
- **Split is IS 1999-2015 / OOS 2016-2026** (`SPLIT = '2016-01-01'`). Every cut point,
  threshold and mapping is learned on IS only and applied unchanged to OOS.
- **Costs**: majors 1.5bp, crosses 3.0bp round trip, charged on position *change*. The
  seven majors are EURUSD GBPUSD AUDUSD NZDUSD USDCAD USDCHF USDJPY; the other 21 are
  crosses. Never apply one spread across all 28.
- **The gauntlet is sequential elimination, not a weighted composite** — a composite lets
  a signal offset a fatal flaw with an unrelated strength. Nothing in it may be decoration.
- **`events.py` dates come from news, never from price.** That is the only thing making
  crisis validation non-circular. If you cannot name what was announced that day, it does
  not belong in the file.
- **`crisis.py` uses a forward-only window, event date to +15 days.** It must never start
  before the event. A window opening 5 days early once produced a false "fires 2.5 days
  ahead" result that vanished under forward-only testing.
- **Out-of-sample confirmation is the only gate that matters.** At 20,275 signals, ~1,000
  clear |t|>2 by chance; overall OOS sign retention is ~53%, a coin flip.

## CI, and a race to know about

`.github/workflows/update.yml` runs `pipeline.py` weekdays 06:00 UTC, on `workflow_dispatch`,
**and on any push touching `code/**`**. It commits `app_data.json`, `app_ui.js`, `results/`
and `data/px28.csv` back to `main` as `fx-bot`.

So pushing a change under `code/` triggers a rebuild that pushes generated files minutes
later. A local push made in that window is rejected. Resolve it by rebasing and
**regenerating** the conflicting artifacts (`app_data.json`, `results/app_data.json`) rather
than hand-merging them — they are build output, not source.

Note `.github/` does not upload through GitHub's web uploader, which silently skips hidden
folders. If automation appears dead, check the folder actually exists on the remote.

## Working style

- Jack owns the architecture. Do not propose structural redesigns.
- Never silently reduce scope. If a job fails, say so and fix it.
- Plain English, short answers. No jargon without explanation, no repeated caveats.
- Never trade return against risk — optimise both.
- Pick sensible defaults and keep moving rather than asking at every step, but do not
  change what was explicitly asked for.
- **Every framework supplied gets wired into all three places**: `app_ui.js`,
  `app_data.json`, and the pipeline. Never deliver results only in chat.
- Report degradations alongside improvements. Improvements are never uniform.
