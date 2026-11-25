# THREE SPEEDS TOGETHER — item 6b, Jack 25 November 2026

**What "three speeds" is read as, and the reading that was not built.** The project's own three settings per indicator are `half`, `default` and `double` — the knob that scales an indicator's memory, halved and doubled (`nnfx1.setting_params`), and the three stage 1 ranked every C1 over. So this is the same strategy at those three settings run SIMULTANEOUSLY as three equal-risk sleeves, against each alone. The other reading — three TIMEFRAMES, the daily/weekly/monthly hierarchy of `HANDOFF_3.md` §9 — needs a weekly and a monthly engine path that does not exist, and item 6 gives one line to the whole question. If that was the intent it is a different job and it is named here rather than guessed at.

**THE WINDOW IS 2005–2015, NOT 2010–2015, and that is Jack's own rule.** A speed is the variable under test so it cannot also be chosen per step; these are FIXED settings across every step, which is not the walk-forward stitch and is **not comparable to candidate A's headline**. The standing rigour covers exactly this case: "unseen 2010 to 2015 (2005 to 2015 for fixed settings)". 2016–2020 computed, not reported.

## Each speed alone

| member | speed | setting | legs | R total 2005–2015 | R/yr | worst dip | **R per dip** | years + | t yearly | R total 2010–2015 | R/yr | **R per dip 2010–2015** |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A | `half` | {'conversion_len': 4} | 7860 | -23.686 | -2.153 | 87.239 | **-0.272** | 6 of 11 | -0.339 | -5.868 | -0.978 | **-0.109** |
| A | `default` | {} | 7296 | -19.902 | -1.809 | 67.882 | **-0.293** | 4 of 11 | -0.394 | +5.692 | +0.949 | **+0.173** |
| A | `double` | {'conversion_len': 18} | 7612 | -66.225 | -6.020 | 77.701 | **-0.852** | 3 of 11 | -1.221 | -29.407 | -4.901 | **-0.756** |
| B | `half` | {'macdFast': 12} | 13280 | -86.523 | -7.866 | 145.488 | **-0.595** | 4 of 11 | -1.133 | +0.298 | +0.050 | **+0.006** |
| B | `default` | {} | 13104 | -105.848 | -9.623 | 143.143 | **-0.739** | 3 of 11 | -1.475 | -25.837 | -4.306 | **-0.355** |
| B | `double` | {'macdFast': 46} | 13010 | -196.183 | -17.835 | 232.201 | **-0.845** | 3 of 11 | -2.037 | -60.060 | -10.010 | **-0.681** |

### THE RESULT THAT MATTERS IS IN THIS TABLE AND IT IS NOT ABOUT SPEEDS

**6 of the 6 fixed-setting cells lose money on 2005–2015, and 4 of 6 lose on 2010–2015.** For A: `half` -23.686 R; `default` -19.902 R; `double` -66.225 R on 2005–2015, and `half` -5.868 R; `default` +5.692 R; `double` -29.407 R on 2010–2015. The best fixed-setting cell on those same six years is **A/default at +5.692 R** — against **+39.874 R** for the walk-forward stitch of the same combination.

**The window is NOT the explanation** — that is what the 2010–2015 columns are for. On the identical six years the best fixed setting anywhere in the table is worth about a seventh of what the stitch makes, and four of the six cells lose. Choosing the setting on each step's own four tuning years is what turns the combination positive. **Candidate A's result is substantially the walk-forward SELECTION rather than the indicator at any one setting.**

That is not a reason to distrust A — the selection is causal, it is made on tuning years only, and it is the thing being tested. It IS a reason to be precise about what A is: not "ichimoku plus an SMA baseline", which at a fixed setting loses on the eleven-year window and makes at best a seventh as much on the six, but **that combination with its lookback re-chosen on every step**. The re-choosing is most of the result.

## The three together, equal risk per sleeve

| member | sleeves | R total | R/yr | worst dip | **R per dip** | best single speed | its R per dip | does the combination beat it? |
|---|---:|---:|---:|---:|---:|---|---:|---|
| A | 3 | -36.604 | -3.328 | 67.580 | **-0.542** | `A_half` | -0.272 | no |
| B | 3 | -129.518 | -11.774 | 165.633 | **-0.782** | `B_half` | -0.595 | no |

**0 of 2 members improve on their own best single speed.** Diversifying across speeds is NOT free: the three sleeves are the same rule on the same pairs reading the same prices, so they share most of their risk, and at equal risk the dilution can cost more than the smoothing earns.

## How much do the speeds actually diversify?

| | `A_half` | `A_default` | `A_double` | `B_half` | `B_default` | `B_double` |
|---|---:|---:|---:|---:|---:|---:||
| `A_half` | **1.000** | +0.898 | +0.807 | +0.226 | +0.182 | +0.188 |
| `A_default` | +0.898 | **1.000** | +0.822 | +0.152 | +0.129 | +0.149 |
| `A_double` | +0.807 | +0.822 | **1.000** | +0.037 | +0.026 | +0.086 |
| `B_half` | +0.226 | +0.152 | +0.037 | **1.000** | +0.883 | +0.747 |
| `B_default` | +0.182 | +0.129 | +0.026 | +0.883 | **1.000** | +0.824 |
| `B_double` | +0.188 | +0.149 | +0.086 | +0.747 | +0.824 | **1.000** |

**Within a member the speeds correlate **A** 0.807 to 0.898; **B** 0.747 to 0.883.** That is the whole story of this report: they are the same rule on the same pairs reading the same prices, so the correlation is high by construction and there is far less to diversify than the three sleeves make it look. Compare the mean-reversion sleeves in `BOOK.md`, which sit at −0.12 to −0.40 against A.

## Provenance

- `results/nnfx/speed_cells.csv` — 6 rows, md5 `e1b7dffaea31`
- `results/nnfx/speed_book.csv` — 2 rows, md5 `8fa6c1cfd64d`
- `results/nnfx/speed_corr.csv` — 6 rows, md5 `69bae2c4829d`
