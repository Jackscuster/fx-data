# QUEUE_ARMED — 25 November 2026, 15:20 EST

**Standing rule, Jack 25 Nov: before any turn ends this file lists every stage that is
ARMED with its pid, report file and ETA, and every requested stage that is NOT armed with
the reason. A stage that exists only as a plan counts as NOT armed. The chat reads this
file directly.**

All times US Eastern. Protocol: `results/nnfx/PROTOCOL.md` (HANDOFF §0o).

---

## ARMED AND RUNNING

| stage | pid / pgid | report | ETA |
|---|---|---|---|
| **Source 3** — real search, then 50 search-null runs, then the gates and the write-up | chain `83129`, worker `83135` | `results/nnfx/SOURCE3.md` + `src3_top50.csv`, `src3_nulls.csv`, `src3_gates.csv` | real search **15:30**, nulls **~17:30**, gates and md **~18:10** |

`code/chain/src3.sh` runs all three parts in sequence with no manual step between them.
Measured throughput at 15:19: **558 evaluations a second**, 200,000 discovery evaluations
in 6 minutes. The 50 null runs go 8 at a time through `xargs -P 8` and are **resumable by
run** — a run whose csv is already in `results/nnfx/src3_null/` is skipped, so a killed
batch costs the runs in flight and no more.

**Do not edit `code/chain/src3.sh` while it is running.** Bash reads a script incrementally
as it executes. Editing `exit6.sh` mid-run on 25 Nov is why that rule is now written in the
script's own header, in this file and in `EXITS.md`.

---

## LANDED THIS TURN

| stage | report | result |
|---|---|---|
| `PROTOCOL.md` | `results/nnfx/PROTOCOL.md` | written first, before any candidate was scored. Not changed without Jack. |
| Kijun-sen baseline added | `code/l2lib.py`, unit test in `l2lib.main()` | the one indicator the N1–N6 catalogue needed that the library lacked. Reference value 17.0 exact; identical to the project's parity-proven ichimoku base line on 5,844 EURUSD bars, max abs diff **0.0e+00**. |
| **Source 1** — the six published combinations | `results/nnfx/SOURCE1.md` | **0 of 6 passers.** Best is N2 at R +38.769, R/dip 0.555; it clears G2 and G3 and fails G1 and G4. |
| **Source 2** — ten hand-built | `results/nnfx/SOURCE2.md` | **0 of 10 passers.** Best is H10, the Pine default control, at R +30.309, R/dip 0.668. The H4 prediction held. |
| **Cost fault found and fixed** | `results/nnfx/COST_DOUBLE_CHARGE.md` | every NNFX-phase net figure before today is charged **twice** the measured spread. Pessimistic. Guard 42. |
| item 6a, the exit factorial | `results/nnfx/EXITS.md` | 576 of 576 cells, landed 12:25. |
| preflight | `results/audit_2026-09.csv` | **43 of 43 PASS**, including the two new guards 42 and 43. |

---

## NOT ARMED, WITH THE REASON

| requested stage | why it is not armed |
|---|---|
| **BOOK2** — the book of passers | **Blocked on Source 3, not on code.** `code/nnfxbook2.py` is written and imports clean. Sources 1 and 2 returned **zero passers**, so the only possible sleeve list is whatever Source 3 surfaces. It is launched by hand as soon as `src3_gates.csv` exists, or run on the best non-passers if Source 3 also returns none — which is the case the module was written for and says so in its own output. **ETA ~18:20**, after Source 3. |
| the 2016–2020 confirm | **Jack's call, not armed by design.** Those years are computed and stored per candidate and summarised nowhere. The protocol says the run stops and reports when a passer exists. |
| re-running stages 1–3 and items 1–6 under the corrected cost charge | **Jack's call.** About 6 hours of compute. `COST_DOUBLE_CHARGE.md` gives the mechanical correction (`R + cost_per_trade/2 x trades`) so the direction and rough size are known without it. Nothing in the new protocol waits on it. |
| chain 22B, chain 31 | **Still awaiting Jack's call** on whether they are dead or parked. Unchanged from 24 Nov. |
| app tab for the protocol sources | **Armed next in this turn**, not running: `code/r2app.py` + `app_ui.js` section, then `node --check`. |

---

## HAZARDS ON THE RECORD

1. **Editing a running script corrupts the rest of its run.** Bash reads incrementally.
   Hit on 25 Nov with `exit6.sh`; the follow-up had to move to `exit6b.sh` and completion
   had to be verified from `exit_grid.csv`'s row count rather than the log.
2. **A function definition pasted into the middle of `main()` silently truncates it.**
   Hit today adding guards 42 and 43: the two `def` lines at column 0 ended `main()`'s body,
   so `guard(42)` and `guard(43)` and the summary print became part of `c43`'s body and
   preflight exited 0 after guard 41 with no summary at all. Caught because the expected
   `43 of 43` line never appeared. This is the same fault class preflight's own guard 29
   exists for.
3. **Disk is at 99%, 5.5 GB free.** Null runs write one summary row each, not their
   evaluation tables, for this reason. No bank is deleted; `results/r2gate1` is untouched.
