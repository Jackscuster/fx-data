# CODE HANDOFF — THE REPO

What exists, what it does, how to run it. Repo: `github.com/Jackscuster/fx-data`,
cloned at `~/Documents/fx-data`.

---

## DATA

**Source:** Fed H.10 daily FX, from
`raw.githubusercontent.com/datasets/exchange-rates/main/data/daily.csv`

**CRITICAL QUOTING CONVENTION.** The dataset is **uniformly foreign-per-USD, including EUR,
GBP, AUD and NZD.** Invert ALL with 1/x, then triangulate. An early attempt assumed
EUR/GBP/AUD/NZD were already inverted and produced garbage.

28 pairs from the G8 in base-priority order EUR GBP AUD NZD USD CAD CHF JPY.
~6,900 rows, 1999-01-04 to present. Close-only — **no OHLC, so no true range or ATR.**

**Sanity checks that must pass after any rebuild:** EURUSD peak 1.601, USDCHF low 0.7296.

**Also in `data/`:** 2-year government yields for all eight G8 currencies, 1990 onward,
pulled directly from central banks — US Treasury, ECB, BoJ, BoE, BoC, RBA, SNB, and RBNZ
via FRED. Free, no key except FRED. Useless for regime; **this is the carry data for
Layer 2.**

---

## LAYER 1 — THE LIVE CODE

These produce the current estimator. Everything else is history.

| File | Does |
|---|---|
| `build.py` | fetch H.10, build `px28.csv`, run sanity checks |
| `classifier.py` | the nine-state classifier — four axes, hysteresis on the cuts |
| `ninestate.py` | the 3x3 grid construction and state labelling |
| `ribbon.py` | the three-window read at 7 / 28 / 128 |
| `windowsweep.py` | swept 4–200 days to choose the three windows |
| `scale.py` | the scale axis — the piece that made it work |
| `termstruct.py` | persistence and term structure across horizons |
| `duration.py` | state age, used as a confidence weight |
| `entry.py` | entry events and excursion measurement |
| `validate.py` | persistence, separation, refit stability, shuffled null |
| `crisis.py` + `events.py` | 48 news-dated crisis events and detector scoring |
| `rates.py` | the eight central-bank yield fetchers |
| `bundle.py` | assembles everything into `app_data.json` |
| `pipeline.py` | runs it all in order |

---

## HISTORY — TESTED, ANSWERED, NOT LIVE

Kept because the answers matter. **Do not rebuild these.**

`sig2` through `sig7` and `sc2` through `sc7` — the five signal batches, 175,634 signals.
`prep.py`, `rank2/3.py`, `pool7.py`, `dedup.py`, `survivors.py` — scoring and pooling.
`inflation.py` — the 50-draw null. **The most important file in the repo.** It showed 78%
of the best effect size was manufactured by selection.
`isonly.py`, `isonly_report.py` — proved selection itself carried look-ahead.
`subsetnull.py` — killed the subset-agreement route; noise beat real data 5,724 to 1,048.
`horizon.py`, `newtargets.py`, `pairtrend.py`, `mtf.py`, `ninebox.py`, `framework.py`,
`ladder.py`, `funnel.py`, `strat.py`, `stability.py` — earlier approaches, all superseded.
`extdata.py`, `extsig.py`, `carrysig.py` — external data. Yahoo gave +8.7 points of
retention, not significant. Rates gave nothing for regime.

---

## RUNNING IT

```
python3 code/pipeline.py
```

**Expensive stages are gated behind environment flags** so a routine rebuild does not
trigger hours of scoring:

```
FX_RUN_INFLATION=1    # the 50-draw null, ~16 hours
FX_RUN_EXTERNAL=1     # external data pull
```

Scorers are **resumable** — each writes one `.npz` per pair and skips pairs already done.
A killed run costs one pair, not everything. This was added after a 16-hour run was lost.

**GitHub Actions** rebuilds weekdays at 06:00 UTC and on any push to `code/**`. Actions
must never attempt the inflation sweep — it exceeds the 180-minute job limit.

---

## THE APP

A thin HTML shell on Jack's machine that fetches **both** `app_data.json` and `app_ui.js`
from the repo. **New tabs go in `app_ui.js`. He never redownloads the shell.**

**Gotcha:** GitHub serves `.js` as `text/plain` with `nosniff`, so a `<script src>` tag is
blocked by the browser. The shell fetches `app_ui.js` as text and evals it. Do not "fix"
this back to a script tag.

**Watch the size.** `app_data.json` reached 96.7 MB against GitHub's 100 MB hard limit. A
split into separate signal and results files was specced repeatedly and should be verified
as done before adding anything large.

---

## BUGS ALREADY HIT — DO NOT REPEAT

- **`bundle.py` once read and wrote the same file**, nesting the signals section inside
  itself. It must READ `signals.json` and WRITE `app_data.json`.
- **`os.path.join(ROOT, '')`** returns a trailing separator; concatenating without it
  silently writes to `resultsapp_data.json`.
- **`sc5.py` writes two-target arrays** named `qti/qto/qci/qco`; older scorers write
  `qi/qo`. `prep.py` probes `z.files` and falls back. Any new multi-target scorer must
  match or update prep.
- **The `.github` folder does not upload through GitHub's web uploader** — hidden folders
  are skipped. This silently meant nothing was automated for hours.
- **A smoke test on non-ragged data proved nothing about ragged data.** This happened
  twice. A truncation bug survived a passing test because the test fixture had uniform
  column lengths; it would have produced "pure noise out-scores every real signal" as a
  headline. Test fixtures must be ragged.
- **A `shift(-1)` in a draft feature peeked one bar ahead** — in exactly the mechanism the
  batch existed to test. Caught before scoring. Audit new features against truncated data.

---

## WHAT LAYER 2 INHERITS

- `px28.csv` — 28 pairs, close-only, 1999 to present
- The nine-state classifier output, per pair per day, on three windows
- Central-bank 2-year yields for all eight currencies — the carry data
- The 48-event crisis calendar
- Per-pair baseline trendiness — panel varies 15%, rank correlation 0.582 between halves.
  Routing information for Layer 3.

**Do not modify Layer 1 code.** If the estimator needs to change, that is a separate
conversation.
