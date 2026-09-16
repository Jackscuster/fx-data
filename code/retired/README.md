# retired code

Kept for the record, never run. `l2layer4.py` / `l2layer4v2.py` carry their own
(pair, day) netting loop that counts a position's vote on its fill day -- the
vote-timing leak of HANDOFF 0d -- and are superseded by `l2walkfwd.Book`. The
pre-flight (`code/preflight.py`, audit item 20) fails if that loop reappears
anywhere under `code/` outside this folder.
