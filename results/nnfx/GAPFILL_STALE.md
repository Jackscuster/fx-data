# WHICH TABLES RAN ON THE OLD FILL RULE

**Realistic gap fills became standing on 25 November 2026 (Jack, item 1).**
Every Layer 2 table written before that ran on the old rule: a stop filled at
the stop price unless the daily bar OPENED beyond it. Pre-flight guard 41
refuses to pass unless this file exists and names them, because the way a stale
table gets quoted is that nothing says it is stale.

## What the old rule got wrong

Only the INTRADAY gap. An overnight gap was already handled (fill at the daily
open) and a level price genuinely traded through was already right (fill at the
stop). A bar that opens on the right side of the stop and then jumps through it
mid-session was filled at the stop, and there was no quote there.

## What that is worth, measured

**Small on these candidates, and not zero.** Over the six A/B/C cells on the
walk-forward stitch and again at default settings over the whole span, the
correction moves total R by well under 1 R a year and makes the worst single
trade worse by about 5% (−2.813 R → −2.956 R). It is not a correction that
changes a verdict. It is a correction that has to be in before any result is
believed, because the size of it is a property of THESE candidates' stop
distances and not of the method: the same fault on a wider stop through the
same event is worth 80 R (see `snb_long_eurchf.csv`).

## The tables that predate it

Everything under `results/nnfx/` written before 25 Nov 2026 10:21 EST, which is
all of:

- `stage1_*.csv`, `STAGE1.md`, `STAGE1_R2.md`
- `stage2_*.csv`, `STAGE2.md`
- `stage3_*.csv`, `STAGE3.md`
- `stage4_*.csv`
- `floor_curve_abc.csv`, `floor_leaders_stage1.csv`, `pegguard_*.csv`
- `atr_buckets_abc.csv`, `snb_trade_value.csv`, `dipcheck_*.csv`
- `leverage_census*.csv`, `amb_hourly_coverage.csv`

**They are not deleted and not quietly restated.** They are the record of what
was reported. They will be superseded by the per-pair bank (item 3), which is
being built on the new rule from the start — re-running the old stage tables to
move a sub-1-R-a-year figure would spend a night to change no conclusion, and
the direction of 25 Nov supersedes what they were for.

## The one thing to carry forward when reading them

The worst single trade in every one of those tables is understated by about
5%, and any figure that leans on a stop-out through a gap is understated by
more. Nothing in them leans on one.
