# TWO SCORES, NOT ONE AXIS

## THE PROBLEM IS UPSTREAM

Stop tuning boundaries. Tercile versus 20/60/20 is the wrong argument.

**The entire point of this layer is identifying trend, chop and crisis.** If 60% of days
cannot be classified, the measurement is inadequate — not the market. Something is always
happening to a price. It is going somewhere, it is stuck, or it broke.

The current score is a **single continuous number** — how trend-like is this bar.
Everything lands on one line, and the middle of any line is ambiguous by construction.
**That is a design flaw, not a finding about markets.**

Trend and chop are not opposite ends of one scale. They are different things.

---

## SCORE THEM SEPARATELY

**Trend score** — is price making progress in one direction. Net displacement relative to
the path walked, sequence of higher highs and higher lows or the mirror, whether pullbacks
hold above prior lows.

**Chop score** — is price respecting boundaries and returning to them. Boundary tests and
how many times each level has held, mean reversion within a band, failed breaks, time
spent inside an established range.

**These are independent measurements.** A bar can be:

| Trend | Chop | What it is |
|---|---|---|
| high | low | trending |
| low | high | ranging |
| high | high | trending within a wider range, or a range being broken |
| low | low | the only honest "neither" |

Classify on the **pair of scores**, not on a position along a line.

**Report how much lands in each combination**, and specifically what is left when a bar
scores low on both. That is the only honest unclassified bucket, and I expect it to be far
smaller than 60%. If it is not, say so plainly and explain what those bars look like.

---

## THE ACTIVITY AXIS

Activity stays as the second dimension — strong, medium, weak. **A trend on low activity is
a weak trend.** Same shape, less conviction. That is why the grid has more than three
cells.

Check whether shape and activity should be cut **jointly rather than separately.** A
weak-activity bar may need stronger structural evidence before it is called trending, since
low participation makes a clean sequence less meaningful. Test both and report which
separates better.

**Note:** there is no volume data. FX is decentralised and H.10 is close-only, so activity
measured by distance travelled is the proxy. That is fine — just be explicit that it is a
proxy.

---

## THE FOUR MEASUREMENTS — BUILD THESE ALONGSIDE

**These are not early-warning candidates.** Each measures something real about the state a
pair is in right now. Whether it also leads a state change is a second question and not the
point.

Two of them feed the trend score, two feed the chop score, and all four are worth having as
readings in their own right.

### 1. Failed swings — is a level being defended

Price approaches the prior extreme, does not reach it, and turns back. **Within-window
only** — a bar counts as a rejection based on what has already happened. No forward-looking
definition.

Sweep the approach threshold across 85/90/93/95/97/98/99% of the prior extreme, and the
turn magnitude across a range of multiples of recent daily range. **Report the full surface,
not the best cell.** A broad plateau means something; a single spike does not.

Feeds the **chop** score — repeated defended levels is what a range is.

### 2. Retracement depth — is a trend tiring

In a healthy trend, pullbacks are shallow. If successive pullbacks deepen — 30%, then 45%,
then 60% — the trend is weakening.

Retracement depth is already computed. Nobody has looked at whether it **trends within a
state.** Measure the sequence, its slope, and the latest against the running average.

Feeds the **trend** score — shallow pullbacks are what makes a trend a trend.

### 3. Swing spacing — is momentum fading

Trends have a rhythm. If each new extreme takes longer to arrive than the last, momentum is
fading. Pure shape, no volatility component.

Measure bars between successive swings, the slope of that sequence, and the current gap
against the running average.

Feeds the **trend** score.

### 4. Cross-pair — is this move idiosyncratic or panel-wide

The 28 pairs share 8 currency legs. **This has never been used for state classification**,
and cross-sectional features were the strongest thing found in the entire signal search —
68% out-of-sample retention against 54% for own-price.

Test whether related pairs and the currency-leg indices carry information about this pair's
state.

**Watch for a trap:** related pairs share a leg by construction, so they move together
mechanically. The question is whether one leads the other in *time*, not whether they
correlate. Report the lead-lag structure explicitly and check the lead is not an artifact of
shared construction.

Feeds **both** scores — a panel-wide move and an idiosyncratic one are different regimes.

---

## HOW TO TEST EACH OF THE FOUR

**Test one — does it describe the current state.** Present-tense, no forward measurement.
Does it separate the states, does it separate on structural properties, does it add anything
the existing scores do not already capture, does it hold per pair, does it survive a null.

**Test two — does it lead a state change.** Hit rate before a genuine change against base
firing rate, lift over chance, lead time in bars. Positive lead means it fires before.

**A candidate can pass one and fail the other.** Something that describes the present well
but never leads anything is still worth keeping. Report both separately and do not let a
failure on test two bury a pass on test one.

---

## SETTINGS AND REPORTING

**Window stays at 105 days** unless something above changes it. Chosen because separation is
44% of peak while runs stay at 21 days — separation keeps climbing to 200 but runs stretch
to 42, which is too slow for entries held for weeks.

**Report trend and chop separately, never blended.** A single combined separation number
hides whether one is carrying the other.

At the chosen settings report: separation, run length, transition diagonal, coverage,
per-pair. Split IS and OOS — choose on in-sample, confirm once on the holdout. Episode-based
significance, not per-bar; a 20-bar state is one observation, not 20.

Null-test anything that looks strong.
