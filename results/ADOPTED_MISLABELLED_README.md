# Files labelled ADOPTED_MISLABELLED — what they actually are

These were produced by the chain run of 2026-09-10 05:27 and are **NOT built on
the fine-tune's adopted settings**, despite the label they were written with.

Two faults, both mine:

1. **Nothing wrote `gate3_costed_verdicts.csv`.** `l2clean3.py` produces the
   W3-only SCORES; the cut that turns them into verdicts had only ever been run
   by hand, in an inline script, on 2026-09-07. The chain refreshed the scores
   and then `l2team.py` read the stale 7 September verdicts file — the gate 2
   settings.

2. **The chain fired on an incomplete bank.** Its wait condition was "no
   fine-tune shards running". Shard 5 died on a transient
   `EmptyDataError` at 96.2%, leaving 194 strategies unprocessed, and the
   absence of shards read as completion.

Confirmed by comparison: these rosters are IDENTICAL to
`team1_W3ONLY_GATE2_FIXED_roster.csv` — the same 26 members. They are the gate 2
team under another name.

Kept, not deleted, so the record of what was produced and why it was wrong stays
readable.
