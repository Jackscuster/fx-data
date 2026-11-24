# REWRITE VERIFICATION — 23 Nov 2026

`git filter-repo` was run to strip two blobs that exceeded GitHub's hard
100 MB file limit and made the remote unreachable. This file is the evidence
that the rewrite changed nothing but those two paths and two embedded SHA
citations.

## The filter-repo arguments, exactly as run

```
git filter-repo --force \
  --path results/r2gate2/modeA_winners_universe.npz \
  --path results/r2gate2/modeB_winners_universe.npz \
  --invert-paths
```

`--force` was required because this repo is not a fresh clone. No
`--prune-empty` was passed, so the default applied; nothing was pruned.

## The two blobs

| path | size | introduced by (old SHA) | removed by (old SHA) | regenerable |
|---|---|---|---|---|
| `results/r2gate2/modeA_winners_universe.npz` | 145.7 MB | `0a2abc3` | `b12ff15` | yes — `l2r2winners.py --stage universe --mode A`, ~6 s measured |
| `results/r2gate2/modeB_winners_universe.npz` | 145.6 MB | `19ee9ec` | `b12ff15` | yes — same, mode B |

Both are streamed reductions of the gate 3 KPI bank. They carry no
information not already in `mode{A,B}_gate3parts/`.

## WHY EVERY COMMIT CHANGED SHA — corrected

**488 commits changed, 0 unchanged, 0 pruned.** An earlier note in this
session attributed this to an empty-commit prune. **That was wrong and is
retracted.** The cause is the root commit `4e5e2a7` ("Add files via upload",
committer GitHub), which became `fc04f30` when `filter-repo` dropped
GitHub's signature on it. Changing the root changes every descendant.
`b12ff15` was not pruned; it survives as `b7cf55e`.

## Equivalence of every PUBLISHED commit

Every commit reachable from `602d392` (the hash the remote was sitting on)
was compared old against new: root tree hash, author name, author email,
author date, committer date, and subject. The old side came from a
blob-filtered scratch clone of the remote at `~/fx-data-verify` (1.1 MB);
the new side from this repo. The mapping came from
`.git/filter-repo/commit-map`.

| measure | result |
|---|---|
| published commits compared | **462** |
| missing from the commit map | **0** |
| trees IDENTICAL | **462** |
| trees DIFFERING | **0** |
| author / date metadata differences | **0** |
| commit message differences | **2** |

**Zero tree differences, and zero differing paths.** The two npz files never
existed in any commit reachable from `602d392` — they were added after it —
so the published history is byte-identical in content.

Note 462, not 488: 462 commits are reachable from the published head; the
other 26 were never published.

## The two commit message differences, in full

`filter-repo` rewrites commit hashes quoted INSIDE commit messages, so a
message does not end up citing a hash that no longer exists. Both
differences are that substitution and nothing else — no wording, no path, no
metadata. They are self-consistent: the second row is the remapping the
first row's message now points at. Jack accepted these on 23 Nov.

### 1. old `2cbe037` -> new `abf5168`

OLD message text:

```
PART 0: Layer 2 parked and fully recorded in HANDOFF 0g — verified state (pre-flight 27/27, both hand checks), the commit the boxes pull (da5eddf), the per-box launch lines, the one-command merge, and that the launch is Jack's call and NOT run; nothing half-finished, the two untracked paths identified
```

NEW message text:

```
PART 0: Layer 2 parked and fully recorded in HANDOFF 0g — verified state (pre-flight 27/27, both hand checks), the commit the boxes pull (1321c14), the per-box launch lines, the one-command merge, and that the launch is Jack's call and NOT run; nothing half-finished, the two untracked paths identified
```

### 2. old `da5eddf` -> new `1321c14`

OLD message text:

```
Pre-launch verification 8 Nov: pre-flight 27/27 on c23fe98, tree clean, every cloud input tracked
```

NEW message text:

```
Pre-launch verification 8 Nov: pre-flight 27/27 on 88d29ef, tree clean, every cloud input tracked
```

## What was NOT verified, and why

The **26 commits that were never published** cannot be compared without
unpacking the bundle, which would write ~7 GB to a volume at 98%. That
comparison is registered as open housekeeping in HANDOFF.md and is to be done
from the bundle once an external drive exists. **The bundle is never
deleted.**

## The permanent record of the old history

| | |
|---|---|
| path | `~/fx-data-backups/fx-data_pre-rewrite_2026-11-23.bundle` |
| size | 7.2 GiB (7,704,952,908 bytes) |
| sha256 | `eec5254365fae71299b82f75a53e24af31d6c8b4987d0550fd1b64a366376be9` |
| `git bundle verify` | "The bundle records a complete history", 4 refs, sha1 |
| independently checked | pack checksum valid, 10,534 objects against 10,532 in the new pack |

It has NOT been fetched or unbundled into this repo or anywhere on this disk.

The old published history is additionally preserved on the remote as the
branch `pre-rewrite-2026-11-23`, pushed from the scratch clone at `602d392`.
