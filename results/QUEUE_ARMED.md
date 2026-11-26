# QUEUE — what is armed right now

**Rewritten 25 November 2026, 20:20 EST. Standing rule: this file is rewritten before the end
of every turn, and it names what is RUNNING, what LANDED, and what is NOT ARMED with the
reason. Nothing is "about to be launched".**

Governing document: `results/nnfx/PROTOCOL.md` — sections 1-9 (the original, unchanged) plus
**AMENDMENT 1** (25 Nov 19:20 EST), which changes the member unit to one algorithm on one
pair, makes admission light, and puts the whole pass/fail on the combined book as B1-B5.

---

## ARMED AND RUNNING

| stage | what | pgid | ETA (US Eastern) |
|---|---|---|---|
| **chain 1 — 20 matched null runs** | B1's floor for families **a, b and c**, and item 2's null. Each run scrambles the world, draws 200,000 algorithms, runs the local search at the same cap, builds the full 28-pair sleeve bank, and rebuilds every book | **25289** (`results/chainlogs/booknull.pgid`), 7 workers | **~21:50** |
| **chain 2 — the matched null for families (d) and (e)** | **ARMED AND WAITING on chain 1**, not launched by hand. Rebuilds the SAME 20 worlds (seeds 700000+run, deterministic) and applies `nnfxcomb.build_d` and `nnfxcell4.build_e` — the same functions that produced the real numbers, imported and not copied | **31947** (`results/chainlogs/booknull2.pgid`), 7 workers | starts ~21:50, **~00:10** |

**To stop either:** `bash code/chain/stop_chain.sh $(cat results/chainlogs/booknull.pgid)` or
`…booknull2.pgid`. Both are resumable by run — a run whose output CSVs are on disk is skipped,
so a stop costs the runs in flight and no more. Chain 2's waiter **refuses to start** if chain
1 disappears with fewer than 20 runs on disk, and says so in its log, rather than waiting for
ever or starting on a short batch.

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
| **item 3 on real data**, families a, b, c | `books_sweep_real.csv`, `books_full_real.csv` (552 cells) | every family, every K, all six share thresholds, both rotations, both modes, full stats |
| **item 3d**, family (d) COMBINED | `books_combined.csv` (72 rows) | the winner is `c_all_pairs` K=50 at share 0.25; **positive in both rotations**, +0.72% to +0.76% a year |
| **A4's four-cell rotation**, family (e) | `books_fourcell.csv` (960 rows) | select on 15 pairs 2005-2010, trade the 13 JPY/CHF pairs 2011-2015 — no shared pair, no shared year. **+4.55 R per sleeve against the cell's +0.81** |
| **item 4** | `results/nnfx/WINNERS.md`, `books/winners.csv` | the best book's 2,426 algorithms, sorted by contribution |
| **B1b, the cell baseline** (A12) | `books/cell_baseline.csv` | a random algorithm makes **+1.383 R** on the 15 pairs in 2005-2010 and **−0.861** on the same pairs in 2011-2015. The cell carries most of the sign, so every book is now also tested against its own cell |
| preflight guard 44, and guard 34 extended | `code/preflight.py` | 44 of 44. Guard 34 now also refuses a file over 50 MB that is neither tracked nor ignored — it passed at 19:55 and the push was refused at 19:58 |

---

## NOT ARMED, AND WHY

| what | why not |
|---|---|
| the FINAL versions of `PAIR_FIT.md`, `BOOKS.md`, `WINNERS.md` | written and generated from the real numbers already, with B1 blank. They are regenerated the moment chain 1 lands — one command, `python3 code/nnfxrep.py --reports`. ETA ~21:55 |
| B1 for families (d) and (e) | chain 2, armed and waiting above. Until it lands neither is called a passer, and both carry B2, B3, B4 and a blank B1. **Family (e) is the strongest result of the night and it is the one with no floor yet** |
| `FINAL_BOOK.md` (item 5) | conditional by construction: only if a book clears B1 to B4 **in both rotations**. A7 declares the rule for picking its admission count in advance so it cannot be chosen after the fact |
| the 2016-2020 confirm | **Jack's call and no one else's.** Computed, never opened. 2021 onward sealed. `FINAL_BOOK.md` (item 5) is written and armed both ways: if a book clears B1-B4 in both rotations it builds the final version with admission on all eleven years at the K best on AVERAGE across rotations — A7's rule, declared before any count was known — runs B5 and stops; if nothing qualifies it says so and builds nothing. The eleven-year admission bank it needs is built (`bankev`, pgid 32294) |
| item 6, the corrected-cost rerun of stage 1 R2, stage 2 and items 1-6 | Jack ranked it lowest priority; it is ~6 hours of compute that would contend with the two null chains, which are the thing he actually asked a question about. `COST_DOUBLE_CHARGE.md` holds the mechanical correction so no earlier table has to be re-run to be read correctly. **The exact blocker is one line**, written down here so the next turn does not have to find it again: `code/nnfx1.py` `_cost_R` ends `... * np.abs(T.units...) / S.RISK) * am / RISK_UNIT_ATR`, and `S.RISK` is 100 while `l2engine.run` risked 200. It needs to become a module constant read from the environment and **defaulting to the present value**, so every existing table stays byte-identical and item 6 is `FX_COST_DIVISOR=engine` rather than a code change. **It was NOT done this turn on purpose:** `nnfx1.py` is imported by `nnfxproto`, so the 13 null workers that had not started yet would have picked up the edit and the 7 running ones would not — the hazard in row 1 below, and the null chains are the critical path |
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
6. **A guard that checks the wrong set passes and protects nothing.** Guard 34 refuses any
   NEW tracked file over 50 MB and it passed at 19:55 — because the 208 MB sleeve bank was
   not tracked yet. The next `git add -A` staged it and GitHub declined the push at 19:58.
   The guard was right and useless. It now also checks files that are neither tracked nor
   ignored, and the new branch was self-tested with a sparse 57 MB file to confirm it fires.
7. **A four-cell book can look out-of-sample and be measuring the cell.** Family (e) is
   positive on (15 pairs, 2005-2010) and (13 pairs, 2011-2015) and negative on the other two
   cells **in both directions, whichever cell it selected on** — because a random algorithm
   does the same. Caught by computing the unconditional per-cell mean, which is now B1b.
8. Editing a running script; a `def` pasted at column 0 inside `main()` silently truncating
   it — both still live, both from earlier turns.
