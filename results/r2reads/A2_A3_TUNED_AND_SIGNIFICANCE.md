# A2 TUNED VERSUS DEFAULT, A1 ON DEFAULTS, AND A3 HONEST SIGNIFICANCE — MODE A

Generated 2026-11-24 09:36 by `code/r2reads.py`.

A2 needed ONE engine pass, because the gate 2 bank stores only the WINNER's per-year record — the gate 1 default has none. That is 2 configurations per strategy against 547 in a full tune, about 0.4%. A1 on defaults rides the same pass, which is why Jack put them in one chunk. A3 is a pure read of the saved daily series.


## A3 — honest significance on the books

Yearly return over yearly volatility, worst dip, and a **block-bootstrap t on 20-day blocks** beside the naive daily t. Blocks keep the within-block dependence a book's multi-day positions create and destroy only the between-block ordering; a naive daily t treats consecutive days as independent and is inflated when they are not.

| source | book | budget | days | years | yearly_return_pct | yearly_vol_pct | return_over_vol | worst_dip_pct | t_block_bootstrap | t_naive_daily | inflation_naive_over_block |
|---|---|---|---|---|---|---|---|---|---|---|---|
| winners_book | allon | team1 | 1,281 | 5 | 2.963 | 1.8 | 1.646 | 1.977 | 3.364 | 3.416 | 1.015 |
| winners_book | allon | team2 | 1,281 | 5 | 4.444 | 2.701 | 1.646 | 2.966 | 3.554 | 3.416 | 0.9612 |
| passers_book | allon | team1 | 1,296 | 5 | 0.09726 | 3.078 | 0.0316 | 6.536 | 0.08807 | 0.078 | 0.8857 |
| passers_book | allon | team2 | 1,296 | 5 | 0.1459 | 4.617 | 0.0316 | 9.804 | 0.08235 | 0.078 | 0.9471 |
| passers_book | chop_trend | team1 | 1,296 | 5 | -1.469 | 1.17 | -1.255 | 8.15 | -1.729 | -1.597 | 0.9239 |
| passers_book | chop_trend | team2 | 1,296 | 5 | -2.203 | 1.756 | -1.255 | 12.23 | -1.941 | -1.597 | 0.8229 |
| full_field_book | allon | team1 | 1,296 | 5 | -1.075 | 1.129 | -0.9523 | 7.233 | -1.218 | -1.211 | 0.9946 |
| full_field_book | allon | team2 | 1,296 | 5 | -1.612 | 1.693 | -0.9523 | 10.85 | -1.301 | -1.211 | 0.9309 |
| full_field_book | chop_trend | team1 | 1,296 | 5 | -0.8753 | 0.9692 | -0.9031 | 5.279 | -1.419 | -1.236 | 0.8713 |
| full_field_book | chop_trend | team2 | 1,296 | 5 | -1.313 | 1.454 | -0.9031 | 7.918 | -1.242 | -1.236 | 0.9958 |
| full_field_book | chop_ungated | team1 | 1,296 | 5 | -0.5611 | 0.7596 | -0.7386 | 4.486 | -0.7921 | -0.7684 | 0.9701 |
| full_field_book | chop_ungated | team2 | 1,296 | 5 | -0.8416 | 1.139 | -0.7386 | 6.729 | -0.7942 | -0.7684 | 0.9675 |
| full_field_book | chop_notrange | team1 | 1,296 | 5 | -1.067 | 0.9594 | -1.112 | 7.073 | -1.794 | -1.604 | 0.894 |
| full_field_book | chop_notrange | team2 | 1,296 | 5 | -1.6 | 1.439 | -1.112 | 10.61 | -1.783 | -1.604 | 0.8992 |


On the winners' book the block t and the naive t agree closely, so the daily series is **not** materially autocorrelated at book level — the naive t was not flattering it. That is worth knowing because it was the suspicion that motivated this item.


## Provenance

| file | rows | md5 |
|---|---|---|
| `results/r2reads/modeA_a3_significance.csv` | 14 | 3af08c1dda4e |
