# Study D — close-time robustness: CANCELLED

**Cancelled 2026-09-07, before it ran. It would have compared 5pm to 5pm.**

The study was specified to re-score the graft 15 on an OANDA daily series aligned
to the 5pm New York close and compare that against "the H.10 series". That
assumed Layer 2 runs on H.10. It does not.

`l2sweep.load_pair` reads `data/oanda_ohlc/<pair>_mid.csv`, fetched by
`l2oanda.py` with `dailyAlignment=17` and `alignmentTimezone=America/New_York`.
**Layer 2 already runs on OANDA 5pm daily bars.** `data/px28.csv`, the Fed H.10
noon series, is Layer 1 only.

So the two sides of the comparison would have been the same data, and the answer
would have been "the edge survives perfectly" — a tautology, not a test.

This was found while fixing study A, where drift against the assumed noon
reference measured -7.5 pips when it must be zero by construction. With the
reference corrected to 17:00 NY, drift is 0.001 pips.

**What a real version of this study would need:** a genuinely different daily
close time — for example midnight UTC, or the 17:00 London close — fetched as a
separate OANDA series and used to rebuild the indicators. That is a worthwhile
test and is NOT what was specified here, so it is left for a later decision
rather than substituted silently.
