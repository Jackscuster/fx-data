# Stages that can emit a file over 50 MB

Jack, 24 Nov, push decision step 5: *"Find and list every stage that can emit a
file over 50 MB."* Written after the 654 MB `modeA_a2_defaults.csv` blocked the
remote and cost a rewrite of 33 unpushed commits.

Compiled empirically — every file on disk over 50 MB, attributed to the module
that writes it — not from reading the code and guessing. **71 of these are
already on the remote and are grandfathered** (see preflight guard 34); the
point of this list is the stages that could produce a *new* one.

## Already committed and on the remote — grandfathered, nothing to do

| artifact | count | each | written by | stage |
|---|---:|---:|---|---|
| `results/r2gate2/mode{A,B}_gate3parts/g3_NNNN_of32.npz` | 64 | 58.8 MB | `l2r2gate3.py` | gate 3 KPI bank shards |
| `results/signals.json` | 1 | 92 MB | `bundle.py` ← `prep.py` | Layer 1 signal pool |
| `results/refit_marks_blind{,_smoke,2}_M_sNN.pkl` | 6 | 50–56 MB | `l2refit.py` | refit mark dumps |
| `results/r2gate1/modeC_full/shard_NN.npz` | 9 | >50 MB | `l2r2step1.py` | gate 1 mode C shards |
| `results/wf_{marks,trades}_*.pkl` | several | >50 MB | `l2walkfwd.py` and callers | walk-forward mark/trade dumps |
| `results/r2gate2/mode{A,B}_full_bookinput.npz` | 2 | >50 MB | `l2r2book.py` | book input arrays |
| `results/r2gate2/mode{A,B}_winners_universe.npz` | 2 | >50 MB | `l2r2winners.py` | winners universe |
| `results/*_infl_{i,o,ckpt}.npz` | 3 | >50 MB | `inflation.py` | inflation-null checkpoints |

## Now on disk under a manifest, summary committed instead

| artifact | each | written by | stage | replaced in git by |
|---|---:|---|---|---|
| `results/r2reads/mode{A,B}_a2_defaults.csv` | 654 / 655 MB | `r2reads.py` | `--stage a2` | `a2_defaults_summary.csv`, `a2_defaults_by_year.csv`, `a2_defaults_MANIFEST.sha256` (`code/a2summary.py`) |

## The stages to watch, because they scale with the universe

These are the ones whose output size is a function of how many strategies or
draws the stage is given, so a bigger run makes a bigger file with no code
change. Any new chain stage of these kinds must declare a manifest, not a blob.

1. **`r2reads.py --stage a2`** — one row per (bank_row, stream, step, role,
   year). 10.74 M rows at the current universe. **This is the one that broke.**
2. **`l2r2gate3.py` KPI bank** — 58.8 MB per shard at 32 shards; a wider grid
   or more steps pushes a shard over 100 MB on its own.
3. **`l2r2step1.py` gate 1 shards** — already over 50 MB for mode C.
4. **`l2r2book.py` book inputs and parts** — scale with member count; the
   grade-rule book had 12,450 members at step 1.
5. **`l2refit.py` mark dumps** — pickles of per-bar marks, linear in trades.
6. **`l2walkfwd.py` mark/trade dumps** — the same.
7. **`inflation.py` / `subsetnull.py` null checkpoints** — linear in draws.
8. **`bundle.py` → `signals.json`** — 92 MB and grows with every signal family
   added. At 100 MB it will block a push. **This is the next one to hit the
   limit** and it is a Layer 1 artifact the app fetches, so it needs its own
   decision before then, not a manifest.

## What a stage must do instead

Write the artifact to disk, add its path to `.gitignore`, record it in a
`MANIFEST.sha256` (file, bytes, sha256) as `bankcheck.py` does for the banks,
and commit a summary csv carrying the numbers any report quotes.
`code/a2summary.py` is the worked example, including the point that the summary
is **not** a substitute: the consuming stage still reads the raw file from disk
and must fail loudly if it is missing.

Enforced in two places, because preflight runs *before* a chain and these files
are written *during* one:
- **preflight guard 34** — no tracked file over 50 MB that the remote has not
  already accepted.
- **`chainlib.sh` `ci_size_gate`** — unstages any new file over 50 MB at the
  moment of commit, names it, and says what to do instead.
