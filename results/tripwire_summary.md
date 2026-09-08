# Intraday tripwire — graft15

## PROVISIONAL — DO NOT QUOTE THESE NUMBERS

**1. The book is wrong for the question.** Every member's position is
stacked independently, so three members long EURUSD hold three EURUSD
positions. The live book will net votes per pair and size by agreement
(Layer 4, not built). Trip counts and false-alarm rates both move once
that exists.

**2. A known defect in the floating-loss baseline.** Position P&L is
measured from each position's ENTRY price, not from its value at the
PRIOR DAY'S CLOSE. The daily prop limit is a change since the previous
close, so a position deep in profit that gives some back never registers.
That is why this run finds only a handful of breach days in twenty-two
years — the count is far too low. Fixing it needs the prior-close mark
per position, which is the same restructuring Layer 4 forces anyway, so
it is deliberately not patched here.

Rerun unchanged on the Layer 4 book:
`python code/l2tripwire.py --positions results/layer4_positions.csv`
with columns day, pair, dir, size, entry, stop.

Equity rebuilt hour by hour with open positions marked to each hour's mid.
Sized so DIP95 = 3.6% (scale 2.3544). Coverage 2004-05 onward.

**A spike that starts and ends inside one hour is invisible in hourly data,
so every "undetectable" count is a FLOOR, not a ceiling.**



**Lowest level that never lets 4.0% through: 3.5%**, firing 0.20 times a year with 0.0% false alarms, costing 0.000% of account per year to close at.

