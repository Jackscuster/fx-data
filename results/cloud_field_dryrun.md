# cloud_field.sh — sharding dry run, 2026-09-11

Run on the Mac through the REAL script (`cloud_field.sh --local`, which skips
provisioning/clone/push and executes the same two Python steps with the same
argument plumbing), so what was tested is the script that will be launched.

10 candidates, A-trend + A-chop + B-chop.

    STRAIGHT   python3 code/l2cleanfield.py --limit 10 --shard-only
               -> 10 scored

    SHARDED    bash code/cloud_field.sh --local --box 0 --of 3 --limit 10  -> 4
               bash code/cloud_field.sh --local --box 1 --of 3 --limit 10  -> 4
               bash code/cloud_field.sh --local --box 2 --of 3 --limit 10  -> 2
                                                                     total  10

    MERGE      python3 code/l2cleanfield.py --limit 10 --merge
               -> merged 3 box banks -> 10 scored strategies

| check | result |
|---|---|
| same sid set, straight vs merged | yes |
| any sid claimed by two boxes | no |
| max abs difference across every `w2_*` metric | **0.000e+00** |
| bit-identical | **yes** |

The 4/4/2 split is `md5(sid) % 3` — the same rule `l2recoverip1` uses, so a box
owns the SAME strategies in both phases and never waits on another box's `ip1`.

**The merge guard fired and was correct.** Merging a 10-candidate universe
against the full 3,485 reported 3,484 LEAVES; that is the completeness check
doing its job, not a result. On a real run a box that dies or fails to push
leaves candidates unscored and `--merge` REFUSES rather than labelling a
silently shrunken field. The `--limit` diff is now taken against the same
limited universe so a dry run reads sensibly.

## Launch

    N=1   export GH_TOKEN=...
          curl -sL https://raw.githubusercontent.com/Jackscuster/fx-data/main/code/cloud_field.sh \
            | bash -s -- --box 0 --of 1

    N=3   same line on each box with --box 0 / 1 / 2 and --of 3, then from the Mac:
          python3 code/l2cleanfield.py --slices A-trend,A-chop,B-chop,B-trend --merge

| | wall | cost |
|---|---|---|
| N=1, CPX62 (16 cores) | ~56 h | ~EUR 36 |
| N=3, CPX62 | ~19 h | ~EUR 37 |
| N=1, CCX63 (48 cores) | ~19 h | ~USD 30 |

898 core-hours either way: 889 for B-trend `ip1` across all 14,815 candidates,
9 for the W2 scoring. Sharding buys wall time, not money.
