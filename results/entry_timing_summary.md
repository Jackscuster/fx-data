# Entry timing — graft 15

## CALIBRATION CAVEAT — READ FIRST

The first version of this study used NOON as the reference, because H.10
is a noon rate. **Layer 2 does not use H.10.** l2sweep.load_pair reads
OANDA daily mid aligned to 17:00 New York, so the engine enters at the
17:00 close; px28.csv (H.10 noon) is Layer 1 only. Measuring against noon
made every entry look 7.5 pips cheap, because noon is five hours before
the price the engine actually used.

Drift at the reference hour is now **0.000 pips** — zero to three decimals, which is the check that the reference is right.

**Reference: noon New York**, per the Fed H.10 documentation.
**Coverage: 2004-05-31 onward** — OANDA hourly history does not reach 1999,
so the in-sample column is 2004-2015, not 1999-2015.

Drift is signed AGAINST the trade: positive means price already moved the
wrong way, so total cost = drift + spread.

| entry time | total cost (pips) |
|---|---|
| 19:00 NY Tokyo | 3.809 |
| 03:00 NY London | 5.204 |
| 18:01 NY Sydney | 7.492 |
| 17:00 NY (engine ref) | 9.813 |
| 08:00 NY New York | 11.739 |
| 12:00 NY (H.10 noon) | 18.008 |

**Cheapest: 19:00 NY Tokyo** at 3.809 pips, against 18.008 for the dearest (12:00 NY (H.10 noon)) — a saving of 14.199 pips per trade.

