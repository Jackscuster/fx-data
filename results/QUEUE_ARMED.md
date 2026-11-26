# QUEUE — what is armed right now

**Written 25 November 2026, 19:45 EST. Standing rule: this file is rewritten before the end
of every turn, and it names what is RUNNING, what LANDED, and what is NOT ARMED with the
reason. Nothing is "about to be launched".**

Governing document: `results/nnfx/PROTOCOL.md` — sections 1-9 (the original, unchanged) plus
**AMENDMENT 1** (25 Nov 19:20 EST), which changes the member unit to one algorithm on one
pair, makes admission light, and puts the whole pass/fail on the combined book as B1-B5.

---

## ARMED AND RUNNING

| stage | what | pid / pgid | ETA (US Eastern) |
|---|---|---|---|
| **20 matched null runs** | B1's floor. Each run scrambles the world, draws 200,000 algorithms, runs the local search at the same cap, builds the full 28-pair sleeve bank, and rebuilds every book of item 3 and every statistic of item 2 | chain pid 25292, **pgid 25289** (in `results/chainlogs/booknull.pgid`), 7 workers | **~22:35** |

**To stop it:** `bash code/chain/stop_chain.sh $(cat results/chainlogs/booknull.pgid)`.
It is resumable by run — a run whose `books_NNN.csv` and `fit_NNN.csv` are both on disk is
skipped, so a stop costs the runs in flight and no more.

**DO NOT EDIT** `code/nnfxbooks.py`, `code/nnfxnullrun.py`, `code/nnfxsleeves.py`,
`code/nnfxfit.py` or `code/chain/booknull.sh` while it runs. This chain was launched with
plain `nohup`, as `src3.sh` was, and so has **no frozen snapshot** — guard 1 of `launch.sh`
is not protecting it. A Python worker imports its modules once at start, so an edit reaches
the workers that have not started yet and not the ones that have.

---

## LANDED THIS TURN

| what | where | result |
|---|---|---|
| **Amendment 1** to the protocol, dated, original untouched | `results/nnfx/PROTOCOL.md` A1-A9 | the member unit, light admission, B1-B5, the two rotations, and the nine operational choices it left me to declare |
| **Source 3's verdict** (it finished at 17:42 while the context turned over) | `results/nnfx/SOURCE3.md` | **1 passer of 50 survivors**: S3_01, +146.8 R, +13.3 R/yr, R/dip 1.400, clears G1-G4 |
| the candidate list, **recovered and checked** | `results/nnfx/bank/cand_index.npz` | 384,334 algorithms. Two assertions passed: 300 recovered tuples reproduce `src3_sample.csv` to 1e-9, and the replayed local search reproduces +18.007580 on exactly 184,372 evaluations |
| `fast_per_pair` / `sleeve_daily`, the sleeve path | `code/nnfxproto.py` | agrees with `fast_obj` at **0.0e+00**, and the two six-year windows sum to the eleven-year figure |
| the **neutral slot sentinel** so A and B can be sleeves | `code/nnfxproto.py` `NEUTRAL` | A and B are C1+baseline members, not complete algorithms; every table carrying them says so |
| **item 1, the declared 18** | `results/nnfx/bank/bank_declared.csv` (1,512 rows), `bank_declared_yearly.csv` (5,544) | per pair, per window and per calendar year |
| **item 1, the searched bank** | `results/nnfx/bank/sleeve_bank_real.npz` (208 MB) | 384,334 algorithms x 28 pairs x 2 windows, in 4.5 minutes |
| **item 2 on real data** | `results/nnfx/books/fit_real.csv`, `fitpooled_real.csv` | pooled rho **+0.0038**; admission does **not** beat its own baseline. Null pending |
| **item 3 on real data** | `results/nnfx/books/books_sweep_real.csv` | every family, every K, every share threshold, both rotations, both modes |

---

## NOT ARMED, AND WHY

| what | why not |
|---|---|
| `PAIR_FIT.md`, `BOOKS.md`, `WINNERS.md` | each needs the 20 null runs for its floor. The real numbers are computed and on disk; the write-ups are blocked on B1 only. ETA ~22:45 |
| `FINAL_BOOK.md` (item 5) | conditional by construction: only if a book clears B1 to B4 **in both rotations**. A7 declares the rule for picking its admission count in advance so it cannot be chosen after the fact |
| the 2016-2020 confirm | **Jack's call and no one else's.** Computed, never opened. 2021 onward sealed |
| item 6, the corrected-cost rerun of stage 1 R2, stage 2 and items 1-6 | Jack ranked it lowest priority and it is ~6 hours of compute that would contend with the nulls. `COST_DOUBLE_CHARGE.md` holds the mechanical correction so no earlier table has to be re-run to be read correctly |
| chains 22B and 31 | still unresolved: dead or parked. Asked, not answered |

---

## HAZARDS ON THE RECORD

1. **A chain launched with plain `nohup` has no frozen snapshot.** `launch.sh` refuses a dirty
   tree and snapshots `code/` so an edit cannot reach a running chain; `src3.sh` and this
   chain both skipped it. The pgid is recorded so `stop_chain.sh` still works, which is how
   the 19:37 launch was stopped cleanly with zero survivors.
2. **`np.add.at` onto a shared index does not scale, and an unbounded parts cache is worse.**
   The first accumulator scattered every sleeve onto the union day index and cached four
   7,000-element arrays per sleeve — about 120 GB at the ~550,000 sleeves one world's sweep
   touches. Caught by arithmetic before launch, not by a crash. Rewritten to accumulate in
   each pair's own bar space and map once per snapshot.
3. **A per-bar cost must carry the engine's risk denominator.** The first version charged
   `f/2 * px * notional` and left out `/RISK_DOLLARS * atr_mult/1.5`, making a sleeve's cost
   300 times too large. Now within 0.2% of `cost_R` on the same trades, the residual being
   the entry-versus-exit price convention, which nets out across trades.
4. **A sleeve must not net against itself.** The separate-positions cost was first computed
   from the sleeve's cumulative signed notional, so two of its own overlapping legs in
   opposite directions quietly cancelled. Leg-wise now; the cumulative array is used only
   where netting is the point, inside the voting machine.
5. **Disk is at 100%, 3.4 GB free.** The null banks are therefore never written — they are
   built in memory, reduced to statistics, and dropped. 20 of them on disk would be 6.8 GB.
6. Editing a running script; a `def` pasted at column 0 inside `main()` silently truncating
   it — both still live, both from earlier turns.
