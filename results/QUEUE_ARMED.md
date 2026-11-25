# QUEUE_ARMED — 25 November 2026, 10:40 EST

**New standing rule, Jack 25 Nov: this file is written before any turn ends and
the chat reads it directly.** A stage that exists only as a plan counts as NOT
ARMED and is listed as such. "Armed" means a process is running or a script is
queued behind a named pid — not that it is written, not that it is next.

Machine state: chain 22A (the `_r2dd` mode A tune) **finished at 08:58 today**
and committed itself (`8472553`). **Nothing else was running when this turn
started.** 10 cores free.

## ARMED

| stage | pid / pgid | what it writes | ETA (US Eastern) |
|---|---|---|---|
| — | — | — | — |

**NOTHING IS ARMED RIGHT NOW, and that is accurate rather than tidy.** Item 1
finished at 10:25 (it took 4 minutes, not the 25 estimated: `run_combo` caches
per pair and indicator, so the second pass over the same twelve runs costs
almost nothing). Item 2 is being written in this turn and is not launched yet.
The machine is idle. The list is not padded with things that are merely next.

## NOT ARMED, AND WHY

| stage | why not |
|---|---|
| item 1 — everything | **DONE 10:38.** `results/nnfx/GAP_FILLS.md`, four csvs, pre-flight **guard 41** live, app section wired, preflight **41 of 41 PASS**. |
| item 2 — quiet-entry test, `QUIET_ENTRY.md` | **being written now, not launched.** 39 C1 alone x 10 deciles x own-pair causal, plus a count/holding/decile-matched random-entry null, plus a walk-forward Q and a fixed-Q curve, plus the floor interaction at 0/1%/5%. |
| item 3 — per-pair bank, `PAIR_GROUPS.md` | **not built.** Needs per-pair-per-direction-per-year banking as the primary output (a change to how every candidate is stored), three declared groupings, and a 1,000-draw label-shuffle null. |
| item 4 — mean reversion, `MEAN_REVERSION.md` | **not built, and not yet located.** The conditional mean-reversion rule from the early project work has to be found in the repo and cited before anything is run. Not started. |
| item 5 — the book, `BOOK.md` | **not built.** Depends on 2, 3 and 4 landing first; it is the thing they feed. |
| item 6 — exits, speeds, drawdown control | **not built.** Explicitly ordered last. |
| chain 22B | **not armed.** It was behind 22A in the old queue; the new direction (per-pair banking, book-level judging) supersedes what it was for, and re-arming it before Jack has seen items 1-5 would spend ten cores on the old question. Flagged for his call, not quietly dropped. |
| chain 31 (A4/A5 follow-ups) | **not armed**, same reason. |

## WHAT JACK STILL OWNS

1. Nothing. **X = 0.33 is adopted** and the placeholder label is gone from the
   code, the reports and the app.
2. Whether 22B and chain 31 are dead or merely parked (see above).
