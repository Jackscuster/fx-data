# QUEUE_ARMED — 25 November 2026, 11:31 EST

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

**NOTHING IS ARMED RIGHT NOW, and that is accurate rather than tidy.** Both of
the queues armed this turn have finished: `code/chain/gap1.sh` (item 1) at
10:25 and `code/chain/quiet2a.sh` + `code/chain/quiet2c.sh` (item 2) at 10:44
and 10:50. Item 3 is not written yet, so it is not armed. The machine is idle
and the list is not padded with things that are merely next.

Item 3's three queues (`bank3a.sh`, `groups3.sh`) finished at 10:59 and 11:03.

**Both of the first estimates were far too long** and that is worth recording rather than
hiding: item 1 took 4 minutes against ~25 estimated, item 2 about 13 minutes
across three stages. `run_combo` caches `prepare` per pair and per indicator,
so any second pass over the same combinations is nearly free — which means my
ETAs for anything that re-runs the same candidates under a different rule
should be divided by about five.

## NOT ARMED, AND WHY

| stage | why not |
|---|---|
| item 1 — everything | **DONE 10:38.** `results/nnfx/GAP_FILLS.md`, four csvs, pre-flight **guard 41** live, app section wired, preflight **41 of 41 PASS**. |
| item 2 — everything | **DONE 10:53.** `results/nnfx/QUIET_ENTRY.md`, nine csvs, app section wired, preflight **41 of 41 PASS**. **Verdict: the rule FAILS and is not adopted.** |
| item 3 — everything | **DONE 11:06.** `PER_PAIR_BANK.md` + `PAIR_GROUPS.md`, 38,919 bank cells, six csvs, app section, preflight **41 of 41 PASS**. **Verdict: the edge is NOT pair-specific in any way a tuning-year pick can find, and pair character does not persist.** |
| item 4 — everything | **DONE 11:20.** `MEAN_REVERSION.md`, five csvs, app section, preflight **41 of 41 PASS**. **Verdict: not proven alone (nothing reaches \|t\| = 2, every positive cell over the 10% crisis threshold), kept as a sleeve candidate because every variant is NEGATIVELY correlated with A.** |
| item 5 — everything | **DONE 11:30.** `BOOK.md`, five csvs, app section, preflight **41 of 41 PASS**. **Verdict: the best book is A ON ITS OWN at 1.135%/yr at the firm's maximum legal sizing — a factor of 10.6 short of 12%, and no book at any sizing ever passes the +10% evaluation.** |
| item 6 — exits, speeds, drawdown control | **not built. NEXT.** Explicitly ordered last by Jack, and items 1-5 have all landed. Three separate reports: exits (three together against each alone; stop 1.0/1.5/2.0 ATR; first target 1.0/1.5/2.0x the stop; trail on and off; time stop 5/10/20 bars), three speeds together, and drawdown control (steady-risk sizing, equity pause, kill switch, crisis sizing). **One thing item 5 changes about it:** the book is a factor of 10 short, so an exit sweep is not going to close the gap and should not be presented as if it might. It is worth running because a 2x on the best sleeve is still a 2x. |
| chain 22B | **not armed.** It was behind 22A in the old queue; the new direction (per-pair banking, book-level judging) supersedes what it was for, and re-arming it before Jack has seen items 1-5 would spend ten cores on the old question. Flagged for his call, not quietly dropped. |
| chain 31 (A4/A5 follow-ups) | **not armed**, same reason. |

## WHAT JACK STILL OWNS

1. **The per-pair floor at 5%.** Item 2d measured it as a by-product and it is
   expensive: with the quiet rule off, turning the floor OFF is worth
   **+12.553 R and 30% of return per dip on A** and **+6.008 R and 37% on B**,
   and floor-off wins at 3 of 4 and 2 of 4 Q values tested. It is his decided
   rule of 7 Sep and **nothing has been changed**. On record, his call.
2. Whether 22B and chain 31 are dead or merely parked (see above).
3. For item 4: the repo has no half-life and no stationarity test, only a Hurst
   exponent. Building an OU half-life and an ADF is the straightforward
   reading of his instruction and that is what I will do unless he says
   otherwise — flagged rather than asked, because item 4 is not blocked on it.

X = 0.33 is adopted and the placeholder label is gone from the code, the
reports and the app.
