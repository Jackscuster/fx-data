# NEXT WORK — THREE TASKS IN ORDER

Do these in order. Each is self-contained. Report after each rather than at the end.

---

## TASK 1 — CLOSE THE LOOK-AHEAD IN SURVIVOR SELECTION

This is the last hole in Layer 1 and it is the one you identified yourself.

The four validation tests passed, but they validate the composite, not the selection. The
32 survivors were chosen by gates reading out-of-sample statistics — so *which signals we
combined* already knows about 2016–2026. The refit test proves the composite is stable
once built; it does not prove the ingredient list was chosen cleanly.

**Rerun the gauntlet using in-sample data only (1999–2015) for every gate.** Select
survivors on that basis alone. Then measure how that in-sample-selected set performs on
2016–2026 as a genuine untouched holdout.

Report:
- How many of the current 32 would have been selected without ever seeing OOS data
- The honest out-of-sample spread for the in-sample-selected set
- Whether the in-sample-selected composite beats or trails the current one
- Which survivors were selected only because the gates saw OOS statistics

If the in-sample-selected set holds up, Layer 1 is genuinely finished. If it collapses,
we need to know that before building anything on top of it.

---

## TASK 2 — EXTERNAL DATA, USING ONLY THE PROVEN CONSTRUCTIONS

First non-price data in the project. Everything so far is FX closes predicting their own
future shape.

**Do not build new signal families.** We already know which shapes work. Test whether
those same shapes work on different data.

### Pull from Yahoo Finance, daily closes, 1999 to present

```
^VIX  ^VIX3M  ^VVIX      equity implied vol and term structure
^MOVE                    bond / rates volatility
HYG  LQD                 credit stress — use the HYG/LQD ratio
TLT  SHY  IEF            bond trends; TLT/SHY is the curve slope
CL=F  GC=F  SI=F         oil, gold, silver
^TNX  ^FVX  ^IRX         US yields 10y, 5y, 3m
DX-Y.NYB                 dollar index
```

### Plus from FRED

2y government yields for all eight G8 currencies, so we can build rate differentials
between every currency pair. **In FX the rate differential is the carry, and the carry is
where the money is.** This has been blocked for the entire project and is now reachable.

### Apply the 32 surviving constructions

They translate in three groups:

- **Duration and occupancy** (`ts_`, `hz_`, `ep_`, `oc_`, `cx_`, `ats_`, `dts_`) apply
  directly to any single series. Time since VIX last exceeded 2 sigma. Occupancy of MOVE
  in its bottom tercile. These are the constructions that produced the trend survivors.
- **Range and drawdown** (`bbw`, `rch`, `bd`, `pdd`) apply directly.
- **Panel measures** (`panelvol`, `paneldisp`, `coex`, `xsctop`) need a panel — so treat
  the external series as their own panel. Cross-sectional dispersion across VIX, MOVE,
  credit and commodities; rank each series within that set. Same construction, different
  universe.

### Causality — where this breaks if done wrong

- US markets and FX have different holiday calendars. Align to the px28 index,
  **forward-fill only, NEVER backfill.**
- Lag one bar, same as everything else.
- `^MOVE` and `^VVIX` have shorter histories than 1999. Report coverage per series and let
  the minimum-observation rule handle it. **Do not pad or interpolate.**

Score through the existing gauntlet unchanged — same targets, same six gates plus
decorrelation. No money metrics.

### The number that matters

**Out-of-sample sign retention by data source.** FX price-derived signals retain 53%.
Cross-sectional FX retains 68%. Does external market data beat either, using identical
constructions?

That single comparison tells us whether to keep mining price or move to data. Because the
constructions are held constant, any difference is about the data itself.

Also report: survivors by source series, and whether any external signal enters the
independent set alongside the current 32.

---

## TASK 3 — PAIR EXPLORER TAB

One pair at a time, price and estimated regime shown together, flip through all 28.

### Layout

- Pair selector at the top — 28 buttons or a dropdown, with left/right arrow keys to move
  between them
- Main chart: log price, full history 1999 to present
- **The price line is coloured by regime** — one colour for trending, one for choppy, one
  for mid. Colour the line itself, not background bands, so regime and price movement read
  together
- Below it, a second panel showing the raw composite score on the same x-axis with the
  threshold lines drawn, so it is visible how close to a boundary any given day was
- Date range control: full history / 5 years / 1 year / 90 days

### Data

The composite already exists at `results/survivor_composite.csv` — dates by 28 pairs. Ship
it in the feed with the regime labels derived from it. Downsample for the full-history
view so the file stays small; full resolution for shorter ranges.

### Per-pair summary panel, beside the chart

- Current regime and how many days it has been in it
- Expected remaining duration in this state, from the transition matrix diagonal
- Share of history spent in each regime, for this pair
- Median run length per regime, for this pair
- This pair's agreement rate with the pooled read — some pairs follow the panel closely
  and some will not, and that is worth seeing

### Mark on the chart

- The 48 events from the crisis calendar as vertical markers, so it is possible to see
  what the estimator was saying when something real happened
- The IS/OOS boundary at 2016-01-01 as a vertical line, since everything to the right of
  it is the honest test

### No money metrics on this screen

It shows what regime was estimated and what price did. Nothing about returns.

**The point of this screen is eyeball validation** — being able to look at 2008, or the
2024 yen unwind, and judge whether the estimator was saying something sensible at the
time. Every validation so far is a number. This is the first thing that lets a human look
at a real period and form a view.
