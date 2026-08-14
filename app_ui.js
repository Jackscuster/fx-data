/* FX Regime Lab — interface module, loaded by the shell from this repo.
   Add a tab HERE and every device picks it up on next open. The shell never changes. */
(function(){'use strict';
const $=s=>document.querySelector(s);
const NAV=`<nav role="tablist">
<button role="tab" aria-selected="false" data-t="px">Explorer</button>
<button role="tab" aria-selected="false" data-t="ns">States</button>
<button role="tab" aria-selected="true" data-t="g">Gauntlet</button>
<button role="tab" aria-selected="false" data-t="iv">Survivors</button>
<button role="tab" aria-selected="false" data-t="s">All signals</button>
<button role="tab" aria-selected="false" data-t="d">Decay</button>
<button role="tab" aria-selected="false" data-t="f">Families</button>
<button role="tab" aria-selected="false" data-t="st">Strategies</button>
<button role="tab" aria-selected="false" data-t="ld">Detectors</button>
<button role="tab" aria-selected="false" data-t="nb">9-Box</button>
<button role="tab" aria-selected="false" data-t="mt">Timeframes</button>
<button role="tab" aria-selected="false" data-t="cr">Crisis</button>
<button role="tab" aria-selected="false" data-t="va">Validation</button>
<button role="tab" aria-selected="false" data-t="if">Inflation</button>
<button role="tab" aria-selected="false" data-t="ex">External</button>
<button role="tab" aria-selected="false" data-t="pt">Pairs</button>
<button role="tab" aria-selected="false" data-t="hz">Horizon</button>
<button role="tab" aria-selected="false" data-t="rd">Regime</button>
<button role="tab" aria-selected="false" data-t="xd">Drivers</button>
<button role="tab" aria-selected="false" data-t="pc">Character</button>
<button role="tab" aria-selected="false" data-t="gl">Explain</button>
<button role="tab" aria-selected="false" data-t="ar">Archive</button>
<button role="tab" aria-selected="false" data-t="vd">Verdict</button>
</nav>`;
const BODY=`<div class="grid">
<div>
<div class="panel"><h3>Gates</h3><div id="gates"></div>
<button class="chip" id="indep" aria-pressed="true" style="width:100%;margin-top:6px"
 title="Gate 8. Greedy decorrelation: strongest survivor first, absorb everything correlated above 0.70, repeat. Computed at the STRICT settings, so it is only meaningful there.">Gate 8: independent only</button>
<button class="chip" id="strict" style="width:100%;margin-top:6px">Reset to strict</button>
</div>
<div class="panel" style="margin-top:16px"><h3>Attrition</h3><div class="funnel" id="fun"></div></div>
</div>
<div>
<div class="panel"><h3>Survivors</h3>
<div class="big" id="surv">0 <span>of 0</span></div>
<div class="note" id="counts" style="margin-top:6px;font-size:12px"></div></div>
<div class="tools" style="margin-top:18px">
<button class="chip" id="exp">Export CSV</button><span class="count" id="scnt"></span></div>
<div class="tw"><table id="gt"><thead><tr>
<th data-k="s">Signal</th><th data-k="to">t OOS</th><th data-k="ti">t IS</th>
<th data-k="si">Spread</th><th data-k="ao">Agree</th><th data-k="mo">Mono</th>
<th data-k="dec">Decay</th><th>Quintiles</th></tr></thead><tbody></tbody></table></div>
<div class="note"><b>Gate 7</b> is time stability across 6 blocks; <b>gate 8</b> is greedy
decorrelation against already-selected signals, which is why the survivor count is far
below the raw number clearing gates 1-6. <b>Still not gated:</b> window robustness against
neighbouring lookbacks, turnover, detection lag and coverage. Everything shown here is
measured, nothing is assumed.</div>
</div></div></section>

<section id="iv" hidden>
<div class="note"><b>The output of this phase.</b> Every signal that clears all eight
gates and is not a near-duplicate of a stronger one. Gate 8 is greedy decorrelation:
strongest first, absorb everything correlated above 0.70, repeat — so each row here is
a distinct effect, and <b>Absorbs</b> says how many others collapsed into it.
<br><br><b>Trend or chop is the SIGN of the efficiency spread</b>, not which target
scores higher. A large negative spread is a chop detector however it reads elsewhere.</div>
<div class="panel" id="cmp" style="margin-bottom:18px"></div>
<div class="tools"><span class="count" id="ivcnt"></span>
<button class="chip" id="ivT" aria-pressed="false">Trend only</button>
<button class="chip" id="ivC" aria-pressed="false">Chop only</button></div>
<div class="tw"><table id="ivt"><thead><tr>
<th data-k="s">Signal</th><th data-k="dirn">Dir</th><th data-k="f">Mechanism</th>
<th data-k="b">Batch</th><th data-k="to">t OOS</th><th data-k="ti">t IS</th>
<th data-k="si">Effect IS</th><th data-k="so">Effect OOS</th><th data-k="ao">Agree</th>
<th data-k="mo">Mono</th><th data-k="dec">Decay</th><th data-k="tsb">Blocks</th>
<th data-k="nclust">Absorbs</th><th data-k="n">Obs</th>
</tr></thead><tbody></tbody></table></div>
<div class="note" id="ivtx" style="margin-top:10px"></div></section>

<section id="s" hidden>
<div class="tools"><input type="search" id="q" placeholder="filter" aria-label="Filter">
<button class="chip" id="cT" aria-pressed="false" title="Positive efficiency t IS — sign of the trend target, not the chop target">Trend</button>
<button class="chip" id="cC" aria-pressed="false" title="Negative efficiency t IS — 'not trending'. Not the same as the chop target.">Chop</button>
<button class="chip" id="cQ" aria-pressed="false" title="Signals that read more strongly on the chop target (turn frequency) than on trend">Chop target</button>
<button class="chip" id="cX" aria-pressed="false">Cross-sectional</button>
<button class="chip" id="cM" aria-pressed="false">Multi-timeframe</button>
<button class="chip" id="cI" aria-pressed="false">Hide interactions</button>
<span class="count" id="acnt"></span></div>
<div class="tw"><table id="at"><thead><tr>
<th data-k="s">Signal</th><th data-k="ti">t IS</th><th data-k="to">t OOS</th>
<th data-k="si">Spread IS</th><th data-k="so">Spread OOS</th><th data-k="ai">Agree IS</th>
<th data-k="ao">Agree OOS</th><th data-k="dec">Decay</th>
<th data-k="cto" title="Chop target (forward 20d turn frequency), t OOS">t OOS chop</th>
<th data-k="cso" title="Chop target spread OOS">Spr OOS chop</th>
<th data-k="cao" title="Chop target pair agreement OOS">Agr OOS chop</th>
<th data-k="stronger_target" title="Which of the two targets this signal scores higher on. NOT the trend/chop split — that is the sign of t OOS.">Stronger target</th>
<th data-k="n">Obs</th>
</tr></thead><tbody></tbody></table></div>
<div class="note" style="margin-top:8px;opacity:.7;font-size:12px">Chop-target columns are
blank for the v2–v4 batches, which scored a single target. Only regime-v5 carries both.</div></section>

<section id="d" hidden>
<div class="note">Each dot is one signal: in-sample strength across, out-of-sample down.
The diagonal is perfect retention. Below it, the signal weakened on fresh data. Above it,
it strengthened. Anything in the shaded band flipped sign and is dead.</div>
<div id="scat"></div></section>

<section id="f" hidden><div class="tw"><table id="ft"><thead><tr>
<th data-k="f">Family</th><th data-k="n">Signals</th><th data-k="bt">Best t OOS</th>
<th data-k="md">Median |t| OOS</th><th data-k="hd">Held sign</th><th data-k="pa">Pass gates</th>
</tr></thead><tbody></tbody></table></div></section>


<section id="st" hidden>
<div class="note"><b>Parameter sweep, 28 pairs, costs on, OOS 2016-2026.</b> Mean against
median exposes when one pair is carrying a config. Dots below the diagonal mean the average
is being propped up by outliers.</div>
<div id="swscat"></div>
<div class="tw" style="margin-top:20px"><table id="swt"><thead><tr>
<th>Config</th><th>Family</th><th>Params</th><th>Mean OOS SR</th><th>Median OOS SR</th>
<th>Pct positive</th><th>Mean trades</th><th>Worst pair</th><th>t across</th>
</tr></thead><tbody></tbody></table></div></section>

<section id="ld" hidden>
<div class="note" style="border-left:3px solid var(--kill);padding-left:10px"><b>PHASE 4 GROUNDWORK — strategy performance, not regime detection.</b> Everything below is measured in Sharpe, Ret/DD and profit factor. Those are money metrics and they say nothing about whether the estimator identifies the regime correctly. Kept for the record; not a verdict on the estimator.</div>
<div class="note"><b>Detector ladder, dumbest to fanciest.</b> Each must beat the row above or
it is not worth using. Every label is backward-looking and was audited: 20/20 spot-checks
reproduced from truncated data.</div>
<h3>How often do regimes flip?</h3><div id="durch"></div>
<h3>Filter applied to baseline, improvement vs unfiltered</h3>
<div class="tw"><table id="ldt"><thead><tr>
<th>Strategy</th><th>Cell</th><th>Data %</th><th>Ret/Exp</th><th>Ret/DD</th><th>PF</th>
<th>Win%</th><th>$AvgTrade</th></tr></thead><tbody></tbody></table></div></section>


<section id="nb" hidden>
<div class="note"><b>Direction × second axis, 3×3.</b> Cut points are terciles learned on
1999-2015 only and applied unchanged to 2016-2026. Both inputs lagged one bar. Colour is
the <b>forward 20-day efficiency lift</b> against the all-bars baseline — amber means the
box precedes straighter travel, red means choppier. <b>No money metrics here:</b> the
question is whether the boxes separate regimes, not what a strategy would have earned.</div>
<div class="tools" style="margin-bottom:10px">
<button class="chip" id="nbA" aria-pressed="true">Volatility axis (original)</button>
<button class="chip" id="nbB" aria-pressed="false">32-survivor axis</button>
<span class="count" id="nbwhich"></span></div>
<div id="nbgrid"></div>
<h3>Separation by box</h3>
<div class="tw"><table id="nbt"><thead><tr><th>Box</th><th>Fwd efficiency</th>
<th>Eff lift</th><th>Pair agree</th><th>Turn freq</th><th>Turn lift</th><th>Data %</th>
</tr></thead><tbody></tbody></table></div>
<div class="note" id="nbtx"></div></section>


<section id="mt" hidden>
<div class="note"><b>Monthly / weekly / daily regimes, mapped onto daily bars.</b> Strategies
trade daily; M and W exist only to confirm or contradict it. Lookbacks form a real hierarchy
— 60 days, 26 weeks, 12 months. A weekly label is not usable until the following Monday and a
monthly label not until the next month opens; both are shifted on their own clock before being
mapped down.</div>
<h3>Do the timeframes line up?</h3><div id="mtag"></div>
<h3>Regime separation by confluence</h3>
<div class="note">Forward efficiency and turn frequency per confluence cell, against the
all-bars baseline. No Sharpe, no Ret/DD — those belong to Phase 4.</div>
<div id="mtcf"></div>
<div class="tw" style="margin-top:16px"><table id="mtt"><thead><tr>
<th>Cell</th><th>Data %</th><th>Fwd efficiency</th><th>Eff lift</th><th>Pair agree</th>
<th>Turn freq</th><th>Turn lift</th></tr></thead><tbody></tbody></table></div>
<div class="note" id="mttx"></div>
<div class="note" id="mtsagree" style="margin-top:12px"></div></section>

<section id="cr" hidden>
<div id="chronic"></div>

<div class="note" style="border-left:3px solid var(--kill);padding-left:10px"><b>PHASE 4 GROUNDWORK — crisis detection against news, not regime detection.</b> Lift here measures whether a detector fires near dated events. It is a different question from whether the estimator separates trend from chop, and a low lift is not a mark against a trend/chop signal.</div>
<div class="note"><b>The only real accuracy numbers in the project.</b> Every other score here
is measured against a target derived from price itself. These are measured against dated news
events — policy decisions, interventions, bankruptcies, referendums, invasions. No event date
was ever chosen by looking at a chart, which is what stops this being circular.
<br><br><b>The window is forward-only: the event date to +15 days.</b> An earlier version
started the window 5 days <i>before</i> the event and reported a detector firing 2.5 days
early. That was the window taking credit for the run-up, not a detector predicting anything.
Under forward-only testing it vanished, and every detector fires on the day.</div>
<div class="tw"><table id="crt"><thead><tr>
<th>Detector</th><th>Caught</th><th>Recall</th><th>Base rate</th><th>Lift</th>
<th>Median lag</th></tr></thead><tbody></tbody></table></div>
<div class="note" id="crtx"></div>
<h3>Events missed by the best detector</h3>
<div class="tw"><table id="cet"><thead><tr>
<th>Date</th><th>Type</th><th>Ccy</th><th>Severity</th><th>Event</th>
</tr></thead><tbody></tbody></table></div></section>

<section id="va" hidden>
<div class="note"><b>Is the estimator detecting anything at all?</b> Four tests, none of
them a money metric. Every other score in this app is measured against a target derived
from the same prices; these are the tests that can say the whole thing is an artefact.</div>
<div id="valcards" style="display:flex;gap:14px;flex-wrap:wrap;margin:16px 0"></div>
<h3>0 — The backward-looking classifier</h3>
<div class="note">The Layer 1 output: nine states from straightness &times; scale, trailing
and lagged. Validated as a <i>description</i> rather than a prediction &mdash; persistence,
separation, refit stability, coverage and two surrogate nulls.</div>
<div id="clsval"></div>
<div class="note" id="clstxt"></div>
<h3>Does anything describe SHAPE?</h3>
<div id="shapeblock"></div>
<div id="dwellblock"></div>
<div class="note" id="shapetxt"></div>
<div id="selblock"></div>
<h3>Counting, per pair, and transitions</h3>
<div id="epiblock"></div>
<div id="pairblock"></div>
<div id="transblock"></div>
<h3>Two axes or one?</h3>
<div id="axesblock"></div>
<h3>Can a fast signal bridge the confirmation delay?</h3>
<div id="leadblock"></div>
<div id="sweepblock"></div>
<div id="confirmblock"></div>
<h3>Layer 1, merged &mdash; every claim beside its test</h3>
<div id="l1sumblock"></div>
<h3>Three shapes, and what lookback shape uses</h3>
<div id="shape3block"></div>
<div id="swinblock"></div>
<h3>The shipped shape read: a continuous score</h3>
<div id="scoreblock"></div>
<h3>Separation split by state</h3>
<div id="splitblock"></div>
<h3>Is the score three clusters, or one spread?</h3>
<div id="distblock"></div>
<h3>Final settings and full report</h3>
<div id="finalblock"></div>
<h3>Old nine-box vs new nine-state</h3>
<div id="oldnewblock"></div>
<h3>Three kinds of regime change</h3>
<div id="chgblock"></div>
<h3>Failed swings</h3>
<div id="fswblock"></div>
<h3>0b — Window selection</h3>
<div class="note">The three ribbon lengths come from a measured trade-off, not a preference:
churn is label changes per 1000 bars, lag is bars until the label follows a genuine change
in behaviour, timed against a <b>centred</b> reference that is a diagnostic only and never
enters a feature.</div>
<div id="ribcurve"></div>
<h3>1 — Shuffled labels</h3>
<div class="note">Shuffle the regime labels while preserving run lengths, rescore, 500
times. If the real labels sit inside that null, the composite is only chopping the sample
into persistent blocks and any persistent blocking would score the same.</div>
<div id="valshuf"></div>
<h3>2 — Synthetic ground truth</h3>
<div class="note">Simulate a panel whose regimes we set ourselves, then run the composite
against them. The only place in the project a real accuracy number can exist.</div>
<div id="valsynth"></div>
<h3>3 — Refit stability</h3>
<div class="note">Build the composite through 2015 and label history; rebuild through 2020
and label again. If 2010's labels move, the composite is using information it would not
have had at the time.</div>
<div id="valrefit"></div>
<h3>4 — Persistence and transitions</h3>
<div class="note">A real regime structure has a strong diagonal and spends its time in
long runs. Note that share-of-runs and share-of-bars answer different questions: a third
of runs can be short while almost no time is spent in them.</div>
<div id="valpers"></div>
<div class="tw" style="margin-top:12px"><table id="valtr"><thead><tr>
<th>from \ to</th><th>chop</th><th>mid</th><th>trend</th></tr></thead><tbody></tbody></table></div>
</section>

<section id="if" hidden>
<div class="note"><b>How much of the effect did the selection itself invent?</b> Every
measured effect is the true effect plus sampling noise, and taking the best out of 175,634
preferentially takes the ones whose noise ran positive. This measures that directly: the
target panel is circularly shifted by a random offset of at least 1000 bars, which destroys
signal-to-outcome alignment while leaving autocorrelation and cross-pair correlation intact,
and the whole gauntlet is rerun against it. 50 offsets. True effect is zero by construction,
so anything that survives is manufactured.</div>
<div class="note">This is not the shuffled-labels test on the Validation tab. That asks
whether the composite beats noise. This asks how much effect the procedure makes
<i>from</i> noise.</div>
<div id="inflcards" style="display:flex;gap:14px;flex-wrap:wrap;margin:16px 0"></div>
<h3>Rank-matched correction</h3>
<div class="note">Real effect at rank k against what the same procedure manufactures at
rank k. The correction uses the median over runs that actually produced a k-th survivor
&mdash; where the null produced nothing there is no correction to apply, not a correction
of zero. The p-value uses all 50 runs, so a run that produced nothing counts as a
non-exceedance. <b>Read the deep ranks with care</b>: the runs column shows how thin the
correction gets.</div>
<div class="tw"><table id="infltab"><thead><tr>
<th>Rank</th><th>Real |spread|</th><th>Null when it fired</th><th>Adjusted</th>
<th>Manufactured</th><th>p</th><th>Runs reaching</th></tr></thead><tbody></tbody></table></div>
<h3>Family mix</h3>
<div class="note">If noise favours the same families our survivors come from, the mix is
not evidence of anything.</div>
<div class="tw"><table id="inflfam"><thead><tr>
<th>Family</th><th>Built</th><th>% of built</th><th>Real survivors</th><th>% of real</th>
<th>Null survivors</th><th>% of null</th></tr></thead><tbody></tbody></table></div>
<div class="note" id="infltx"></div>
</section>

<section id="ex" hidden>
<div class="note"><b>First non-price data in the project.</b> Everything else here is FX
closes predicting their own future shape. This runs the <i>surviving constructions,
unchanged</i>, over the outside world &mdash; equity and rates vol, credit, bonds,
commodities, US yields, the dollar index &mdash; and scores them against the same 28 FX
targets. No new signal families: because the construction is held constant, any difference
is about the data.</div>
<div id="excards" style="display:flex;gap:14px;flex-wrap:wrap;margin:16px 0"></div>
<h3>Out-of-sample sign retention by source</h3>
<div class="note">The comparison the task turns on. <b>Read the n column first</b> &mdash;
these groups are small enough that the individual rows are noise.</div>
<div class="tw"><table id="extab"><thead><tr>
<th>Source</th><th>n</th><th>OOS retention</th><th>vs FX price</th></tr></thead><tbody></tbody></table></div>
<h3>Which constructions transfer at all</h3>
<div class="note">A construction that indexes a currency pair's two legs has nothing to read
on a VIX series. That is a property of the construction, not a data failure.</div>
<div id="extr"></div>
<h3>Rate differentials &mdash; the carry test</h3>
<div class="note">Two-year government yields for the G8, one leg per currency, assembled
from eight central banks and treasuries because FRED's keyless host refuses this network.
The differential base&minus;quote <i>is</i> the carry. Unlike the market series above these
are <b>pair-specific</b>, so every construction produces a genuine 28-pair panel and is
scored exactly the way an FX price signal is.</div>
<div class="note">A rate differential crosses zero and every signal module starts with
<code>log(price)</code>, so the differential is accumulated into a carry index
<code>cumprod(1+d/252)</code> whose log-increments are the differential exactly. Gaps stay
gaps &mdash; a missing month is never filled into flat carry.</div>
<div class="tw"><table id="cartab"><thead><tr>
<th>Group</th><th>n</th><th>OOS retention</th><th>vs FX price</th></tr></thead><tbody></tbody></table></div>
<div id="carnote"></div>
<div class="tw"><table id="ratecov"><thead><tr>
<th>Currency</th><th>Source</th><th>Obs</th><th>First</th><th>Last</th><th>Coverage</th>
</tr></thead><tbody></tbody></table></div>
<h3>Coverage</h3>
<div class="note">Aligned to the FX calendar, forward-filled only, never backfilled and
never padded at the front. Series that start late stay NaN until they start.</div>
<div class="tw"><table id="excov"><thead><tr>
<th>Series</th><th>Source</th><th>Group</th><th>First</th><th>Coverage</th></tr></thead><tbody></tbody></table></div>
<div class="note" id="extx"></div>
</section>

<section id="pt" hidden>
<div class="note"><b>Which pairs trend and which chop.</b> Mean forward 20-day efficiency,
<b>|net move| &divide; |path travelled|</b>, per pair, in sample and out. Nothing is fitted
&mdash; this is a property of the pair, not of the estimator. A high number means the pair
goes somewhere in a straight line.</div>
<div id="ptcards" style="display:flex;gap:14px;flex-wrap:wrap;margin:16px 0"></div>
<div class="tw"><table id="pttab"><thead><tr>
<th>Pair</th><th></th><th>IS</th><th>OOS</th><th>Rank IS</th><th>Rank OOS</th><th>Move</th>
</tr></thead><tbody></tbody></table></div>
<h3>Is the agreement gate killing pair-specific trend signals?</h3>
<div class="note">Gate 4 demands a signal point the same way on 25 of 28 pairs. If a signal
genuinely worked on trending pairs and did nothing on choppy ones, that would be real
structure and the gate would delete it for not being universal. So: every signal that
clears every other gate and dies only on agreement, with its per-pair spreads recovered
from the score files, asking whether the pairs carrying it are the trending ones.</div>
<div id="agnote"></div>
<h3>The null test on the subset route</h3>
<div class="note">A looser gate always admits more signals, so counting them proves
nothing. The whole agreement sweep is therefore run twice &mdash; once on the real target,
once against each of the 50 circularly-shifted panels where the true effect is zero by
construction. <b>Expected false</b> is what the same threshold admits from noise.</div>
<div class="tw"><table id="sntab"><thead><tr>
<th>Agreement</th><th>Pairs</th><th>Real</th><th>Null median</th><th>Null max</th>
<th>Expected false</th><th>Contamination</th></tr></thead><tbody></tbody></table></div>
<div id="snnote"></div>
<div class="tw"><table id="agtab"><thead><tr>
<th>Pair</th><th>In the strongest 7 for…</th><th>Trendiness</th></tr></thead><tbody></tbody></table></div>
</section>

<section id="hz" hidden>
<div class="note"><b>Is 20 days the right horizon, or just the first one anybody picked?</b>
Every effect in this project is measured against forward 20-day efficiency because that was
chosen at the start and never justified. The 111 old survivors rescored at 5, 10, 15 and 20
days, same signals, same pooling.</div>
<div class="note"><b>t-statistics do not compare across horizons.</b> Overlapping windows
make the target more serially correlated the longer the horizon, so a zero effect earns a
bigger t at 20 days than at 5. The null column is what the same signals score against a
circularly shifted target &mdash; <b>real ÷ null</b> is the only honest comparison here.</div>
<div id="hzcards" style="display:flex;gap:14px;flex-wrap:wrap;margin:16px 0"></div>
<div class="tw"><table id="hztab"><thead><tr>
<th>Horizon</th><th>|effect| OOS</th><th>Agreement</th><th>Monotonic</th><th>Retention</th>
<th>Null |t|</th><th>Real ÷ null</th></tr></thead><tbody></tbody></table></div>
<div class="note" id="hznote"></div>
</section>

<section id="px" hidden>
<div class="note"><b>What state is this pair in, and what did price do.</b> The nine-state
grid is size &times; cleanliness, both measured over the trailing 20 bars and lagged one.
<b>strong/medium/weak is how far it moved, not how confident the reading is.</b>
No forward target and no money metrics &mdash; this describes what has happened.</div>
<div id="pxsel" style="display:flex;flex-wrap:wrap;gap:4px;margin:10px 0"></div>
<div id="pxwin" style="display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:10px 0"></div>
<div id="pxrange" style="display:flex;gap:6px;margin:10px 0"></div>
<div class="grid" style="grid-template-columns:1fr 300px;gap:16px;align-items:start">
<div><div id="pxchart"></div><div id="pxribbon"></div><div id="pxaxes"></div></div>
<div class="panel" id="pxpanel"></div>
</div>
<div id="pxlegend" style="display:flex;flex-wrap:wrap;gap:10px;margin-top:10px"></div>
</section>

<section id="ns" hidden>
<h3>Current classifier &mdash; states and validation</h3>
<div id="curstates"></div>
<div id="rfwrap"></div>

<div class="note"><b>The nine states.</b> An explicit grid: size &times; cleanliness, each
cut at that pair's own in-sample terciles with hysteresis. Both axes contribute by
construction &mdash; the states are the cross, not terciles of a weighted score, so neither
axis can crowd the other out.</div>
<div class="note" style="border-left:3px solid var(--dim);padding-left:10px">
<b>The two words mean different things.</b><br>
<b>strong / medium / weak</b> is <b>SIZE</b> &mdash; how far the pair moved, in its own
volatility units. It is <i>not</i> confidence in the reading.<br>
<b>trend / transitional / chop</b> is <b>CLEANLINESS</b> &mdash; how straight the travel
was.<br>
So <i>strong chop</i> is a pair thrashing a long way, and <i>weak trend</i> is a pair
drifting a short way in a straight line. Neither word says how sure the classifier is.
Colour follows the row: green trend, amber transitional, red chop; darker is larger.</div>
<div class="note" style="border-left:3px solid var(--kill);padding-left:10px"><b>The second
axis is real, and it runs backwards to its own name.</b> Comparing states at the same scale
but opposite straightness, the <i>chop</i> side is followed by <b>more</b> efficient travel,
not less: <b>+0.0218</b> at medium size (null-corrected +0.0220, p=0.020) and +0.0133 at
strong (p=0.078, not significant). Trailing straightness mean-reverts. So the trend/chop
word describes the <i>last</i> 20 bars accurately and is the opposite of a forecast
&mdash; reading <i>strong trend</i> as "expect more of it" has the sign backwards.</div>
<div class="tw"><table id="nstab"><thead><tr>
<th>State</th><th>Share</th><th>Median run</th><th>n entries</th><th>Peak (MFE)</th>
<th>Bars to peak</th><th>Retrace</th><th>Path eff.</th></tr></thead><tbody></tbody></table></div>
<h3>Transition matrix</h3>
<div class="note">Row = state today, column = state tomorrow. The diagonal is the stay
probability.</div>
<div id="nstm" style="overflow-x:auto"></div>
<h3>Window agreement &mdash; dropped as a signal</h3>
<div class="note" style="border-left:3px solid var(--kill);padding-left:10px">
<b>This is no longer presented as part of the estimator output.</b> Whether the three
windows agree was tested against a circular-shift permutation that preserves the tier
run-lengths and the entry clustering, and against a cluster bootstrap by pair:
<br><br>
<code>ratio</code> spread 0.120 against a null of 0.099 &plusmn; 0.037, <b>p = 0.257</b>.
<code>bars to peak</code> 0.529 against 0.385 &plusmn; 0.140, p = 0.156.
<code>retracement</code> 10.9pp against 9.8 &plusmn; 3.6, p = 0.335.
<code>MFE</code> 0.0010 against 0.0010, p = 0.487.
The widest single gap, all-agree against slow-apart, is +0.062 with a bootstrap 95%
interval of <b>&minus;0.029 to +0.165</b> &mdash; it crosses zero.
<br><br>
A five-way split of this data produces a ratio spread near 0.10 by chance alone; we
observed 0.12. The configuration is still shown on the chart and in the per-pair panel as
a <i>description</i> of which windows currently disagree, because that is a fact about the
windows. It predicts nothing measurable and no excursion table is shipped for it.</div>
<h3>Per pair</h3>
<div class="tw" style="max-height:420px;overflow:auto"><table id="nsper"><thead><tr>
<th>Pair</th></tr></thead><tbody></tbody></table></div>
</section>

<section id="vd" hidden>
<h3>Does the regime read predict what happens after entry?</h3>
<div class="note">The bridge to Layer 2. Three deliberately dumb triggers &mdash; a 20-day
breakout, a 20/100 moving-average cross, a two-sigma stretch faded &mdash; generate entry
events. At each one the regime reading is taken as of the prior bar, then the next 20 bars
are measured with <b>no exit rule</b>: how far it went the right way, how far the wrong
way, how long to the peak, how much of the peak was surrendered, how straight the path was.
No PnL, no win rate. Terciles cut on in-sample data only.</div>
<div class="tw"><table id="entab"><thead><tr>
<th>Regime third</th><th>n</th><th>MFE</th><th>MAE</th><th>MFE/|MAE|</th>
<th>Bars to peak</th><th>Giveback</th><th>Path eff.</th><th>Onside at 20</th>
</tr></thead><tbody></tbody></table></div>
<div class="note" id="entxt"></div>
<h3>The term structure &mdash; a second regime dimension?</h3>
<div class="note">Efficiency measured over the past 5, 10, 15 and 20 days gives a shape,
not a number: its level, how much it persists from the short window to the long one, its
slope and curvature, its dispersion, and how many horizons agree. <b>All trailing and
lagged one bar.</b> Every feature is scored against a circularly shifted target as well,
and <b>corrected</b> is the real effect minus what the same feature earns from noise.</div>
<div class="note" style="border-left:3px solid var(--kill);padding-left:10px"><b>Why
trailing matters here more than anywhere else.</b> Defining persistence from the
<i>forward</i> readings makes it a function of the target: it scores an OOS effect of
0.2460 at t=190 with all 28 pairs agreeing, about ten times the best real survivor in the
project. A shifted-target null does <b>not</b> catch that &mdash; shifting destroys the
leaked alignment, so the null reads near zero and the ratio comes out around 40×,
certifying the leak. Nulls test selection inflation, not look-ahead.</div>
<div class="tw"><table id="tstab"><thead><tr>
<th>Feature</th><th>OOS effect</th><th>Null</th><th>Corrected</th><th>Ratio</th>
<th>Agreement</th><th>\|t\|</th></tr></thead><tbody></tbody></table></div>
<div class="note" id="tstxt"></div>
<h3>The strictest test — is any one variant provably not luck?</h3>
<div id="funch"></div>
<div class="note" id="funtx"></div>
<h3>Three logics, paired draws</h3>
<div class="note">Switch and gate are real. <b>Switch backwards is the control</b> — the same
mapping deliberately inverted. If switching works for a real reason, backwards should be worse.</div>
<div id="logch"></div>
<h3>The 200-day SMA vs complexity</h3>
<div id="cmpch"></div>
<div class="note" id="cmptx"></div></section>



<section id="rd" hidden>
<div id="rdwrap"></div>
</section>

<section id="pc" hidden>
<div id="pcwrap"></div>
<div id="shwrap"></div>
</section>

<section id="gl" hidden>
<div class="note"><b>Every metric in this build, in plain English.</b> What it is, how it is calculated, how to read it, what it is good for, and the most likely misreading. The last line of each is the one that matters.</div>
<div id="glwrap"></div>
</section>

<section id="ar" hidden>
<div id="arwrap"></div>
</section>


<section id="xd" hidden>
<h3>External drivers &mdash; do they confirm the regime read?</h3>
<div id="extdrv0"></div>
<div id="drvc"></div>
<div id="fwdodds"></div>
<div id="drvde"></div>
<div id="drvf"></div>
<div id="drvprog"></div>
<h3>Direction tests (superseded, kept on file)</h3>
<div id="extdrv"></div>
<div id="extdrv2"></div>
</section>
`;
// The feed is split in two: app_data.json (small, everything except signals) and
// app_signals.json (large). The shell only fetches the first and hands it here, so
// this module fetches the second itself and merges before rendering.
window.renderApp=function(BUNDLE,root){
  if(BUNDLE&&BUNDLE.signals){return boot(BUNDLE,root);}          // pre-split feed
  const url=(BUNDLE&&BUNDLE.meta&&BUNDLE.meta.signals_url)||'app_signals.json';
  root.innerHTML='<div style="padding:32px;font:14px/1.6 system-ui;color:#8a8f98">'
   +'Loading signals\u2026<br><span style="font-size:12px;opacity:.7">'
   +'app_signals.json is ~47 MB and gzips to about 6 MB.</span></div>';
  fetch(url).then(function(r){if(!r.ok)throw new Error('HTTP '+r.status);return r.json();})
   .then(function(sig){BUNDLE.signals=sig;boot(BUNDLE,root);})
   .catch(function(e){root.innerHTML='<div style="padding:32px;font:14px/1.6 system-ui;'
     +'color:#d05">Could not load signals ('+e.message+').<br><span style="font-size:12px">'
     +'The feed is split: <code>app_data.json</code> and <code>app_signals.json</code> '
     +'must both be reachable. Tried:<br><code>'+url+'</code></span></div>';});
};

function boot(BUNDLE,root){
  let BUN=BUNDLE, DALL=(BUNDLE.signals||BUNDLE);
  // Every scored signal is carried in the feed, including the ones that could not be
  // scored at all (ok:false -- too few pairs with data, or an undefined t). Those have
  // null metrics, so they are excluded from RENDERING while still being counted. The
  // data file keeps them; the tables just have nothing to draw.
  let D=DALL.filter(d=>d.ok!==false&&d.to!=null);
  root.innerHTML=NAV+'<section id="g">'+BODY;
  const MT=BUN.meta||{};
  // TWO numbers, always both, never one ambiguous figure: everything built, and
  // the subset that could produce quintile statistics. The gap is signals with too
  // few pairs of data or an undefined t -- kept in the feed, marked ok:false.
  const nBuilt=MT.n_built||DALL.length, nScor=MT.n_scorable||D.length;
  $('#sub').textContent=nBuilt.toLocaleString()+' signals built \u00b7 '
   +nScor.toLocaleString()+' scorable \u00b7 '+(nBuilt-nScor).toLocaleString()
   +' unscorable \u00b7 '+(MT.pairs||28)+' pairs \u00b7 IS 1999-2015 \u00b7 OOS 2016-2026'
   +(MT.built?' \u00b7 rebuilt '+MT.built:'');
  const GATES=[
   {k:'to', n:'|t| OOS',      min:0,   max:25, step:.5, v:8,   f:d=>Math.abs(d.to)},
   // Gates 2 and 3 sit where the noise null (inflation.py) stops manufacturing
   // survivors, not at a round number. 0.893 is 25 of 28 pairs; the old 0.85 was
   // 24 of 28 in disguise. Steps are fine enough to land on them exactly.
   {k:'si', n:'Effect size',  min:0,   max:.04,step:.0001,v:.0221,f:d=>Math.abs(d.si)},
   {k:'ao', n:'Pairs agree',  min:.5,  max:1,  step:.001,v:.893,f:d=>d.ao},
   {k:'mo', n:'Monotonic',    min:.5,  max:1,  step:.01, v:.95,f:d=>Math.abs(d.mo)},
   {k:'dec',n:'Decay ratio',  min:0,   max:1.5,step:.05, v:.6, f:d=>d.dec},
   // Gate 7. Signals scored before block spreads were stored have tsb null; they
   // are treated as passing rather than silently killed, so the funnel never
   // reports a drop that is really just missing data.
   {k:'tsb',n:'Blocks stable',min:0,   max:6,  step:1,  v:4,  f:d=>d.tsb==null?6:d.tsb}];
  const STRICT=[8,.0221,.893,.95,.6,4];
  
  $('#gates').innerHTML=GATES.map((g,i)=>
   `<div class="gate"><label>${g.n}<b id="v${i}"></b></label>
    <input type="range" id="r${i}" min="${g.min}" max="${g.max}" step="${g.step}" value="${g.v}"></div>`).join('');
  
  function fmt(g,v){return g.k==='si'?v.toFixed(4)
   :(g.k==='tsb'?v.toFixed(0)+' of 6'
   :(g.k==='ao'?v.toFixed(3)+' ('+Math.ceil(v*28)+' of 28)':v.toFixed(2)));}
  function vals(){return GATES.map((g,i)=>+$('#r'+i).value);}
  let fIND=1;
  function survivors(){
   const V=vals();
   const s=D.filter(d=>d.held&&GATES.every((g,i)=>g.f(d)>=V[i]));
   // Gate 8. indep is marked by dedup.py against the STRICT set, so it only means
   // what it says at strict settings; loosen a slider and the clustering behind it
   // no longer matches what is on screen.
   return fIND?s.filter(d=>d.indep!==false):s;}
  function funnel(){
   const V=vals();let cur=D.filter(d=>d.held);
   const rows=[['sign holds',cur.length]];
   GATES.forEach((g,i)=>{cur=cur.filter(d=>g.f(d)>=V[i]);rows.push([g.n,cur.length]);});
   if(fIND){cur=cur.filter(d=>d.indep!==false);rows.push(['independent',cur.length]);}
   $('#fun').innerHTML=rows.map(r=>
    `<div class="fr"><span class="nm">${r[0]}</span><span class="bar">
     <i style="width:${100*r[1]/D.length}%"></i></span>
     <span class="ct ${r[1]===0?'z':''}">${r[1]}</span></div>`).join('');}
  function spark(q){if(!q||!q.length||q.some(v=>v==null))return '<span style="opacity:.3">—</span>';
   const mn=Math.min(...q),mx=Math.max(...q),r=(mx-mn)||1;
   return '<span class="spark">'+q.map(v=>`<i style="height:${3+13*(v-mn)/r}px"></i>`).join('')+'</span>';}
  let gs='to',gd=-1;
  function drawG(){
   GATES.forEach((g,i)=>$('#v'+i).textContent=fmt(g,+$('#r'+i).value));
   const S=survivors();funnel();
   $('#surv').innerHTML=S.length+' <span>of '+D.length.toLocaleString()+' scorable</span>';
   if($('#counts'))$('#counts').innerHTML=
     (MT.n_built||DALL.length).toLocaleString()+' built \u00b7 '
     +D.length.toLocaleString()+' scorable \u00b7 '
     +((MT.n_built||DALL.length)-D.length).toLocaleString()+' could not be scored'
     +'<br><span style="opacity:.7">Gates run on the scorable set. Unscorable rows are '
     +'kept in the feed, never deleted \u2014 a failure is a result.</span>';
   $('#scnt').textContent=S.length+' shown';
   S.sort((a,b)=>{const x=a[gs],y=b[gs];
    return (typeof x==='string'?x.localeCompare(y):Math.abs(x)-Math.abs(y))*gd;});
   $('#gt tbody').innerHTML=S.map(d=>{const c=d.ti>0?'var(--trend)':'var(--chop)';
    return `<tr><td style="color:${c}">${d.s}</td><td style="color:${c}">${d.to.toFixed(1)}</td>
    <td>${d.ti.toFixed(1)}</td><td>${d.si.toFixed(4)}</td><td>${(d.ao*100).toFixed(0)}%</td>
    <td>${d.mo.toFixed(2)}</td><td>${d.dec.toFixed(2)}</td><td>${spark(d.qo)}</td></tr>`;}).join('')
    ||'<tr><td colspan="8" style="color:var(--kill);padding:18px">Nothing survives these gates.</td></tr>';}
  GATES.forEach((g,i)=>$('#r'+i).oninput=drawG);
  $('#strict').onclick=()=>{STRICT.forEach((v,i)=>$('#r'+i).value=v);fIND=1;
   $('#indep').setAttribute('aria-pressed',true);drawG();};
  $('#indep').onclick=e=>{fIND=fIND?0:1;e.target.setAttribute('aria-pressed',!!fIND);drawG();};
  $('#exp').onclick=()=>{const S=survivors();
   const csv='signal,t_is,t_oos,spread_is,spread_oos,agree_is,agree_oos,mono_oos,decay\n'+
    S.map(d=>[d.s,d.ti,d.to,d.si,d.so,d.ai,d.ao,d.mo,d.dec].join(',')).join('\n');
   const a=document.createElement('a');
   a.href=URL.createObjectURL(new Blob([csv],{type:'text/csv'}));
   a.download='gauntlet_survivors.csv';a.click();};
  document.querySelectorAll('#gt th').forEach(th=>{if(!th.dataset.k)return;th.tabIndex=0;
   th.onclick=()=>{const k=th.dataset.k;gd=(k===gs)?-gd:-1;gs=k;drawG();};});
  
  let as='ti',ad=-1,fT=0,fC=0,fQ=0,fX=0,fM=0,fI=0;
  const NA='<span style="opacity:.3">—</span>';
  const nf=(x,p)=>x==null?NA:x.toFixed(p);
  const np=x=>x==null?NA:(x*100).toFixed(0)+'%';
  function drawA(){
   const q=$('#q').value.trim().toLowerCase();
   let v=D.filter(d=>(!q||d.s.toLowerCase().includes(q))&&(!fT||d.ti>0)&&(!fC||d.ti<0)
    &&(!fQ||d.stronger_target==='chop')
    &&(!fX||d.b==='cross-sectional')&&(!fM||d.b==='multi-timeframe')&&(!fI||!d.s.startsWith('x_')));
   // nulls sort last in both directions rather than colliding at zero
   v.sort((a,b)=>{const x=a[as],y=b[as];
    if(x==null&&y==null)return 0; if(x==null)return 1; if(y==null)return -1;
    return (typeof x==='string'?x.localeCompare(y):Math.abs(x)-Math.abs(y))*ad;});
   $('#acnt').textContent=v.length+' of '+D.length;
   $('#at tbody').innerHTML=v.slice(0,600).map(d=>{
    const c=Math.abs(d.ti)<2?'var(--flat)':(d.ti>0?'var(--trend)':'var(--chop)');
    const tc=d.stronger_target==='chop'?'var(--chop)':(d.stronger_target==='trend'?'var(--trend)':'var(--flat)');
    return `<tr><td style="color:${c}">${d.s}</td><td style="color:${c}">${d.ti.toFixed(1)}</td>
    <td>${d.to.toFixed(1)}</td><td>${d.si.toFixed(4)}</td><td>${d.so.toFixed(4)}</td>
    <td>${(d.ai*100).toFixed(0)}%</td><td>${(d.ao*100).toFixed(0)}%</td>
    <td>${d.dec.toFixed(2)}</td>
    <td>${nf(d.cto,1)}</td><td>${nf(d.cso,4)}</td><td>${np(d.cao)}</td>
    <td style="color:${tc}">${d.stronger_target||NA}</td>
    <td>${(d.n/1000).toFixed(0)}k</td></tr>`;}).join('');}
  $('#q').oninput=drawA;
  $('#cT').onclick=e=>{fT=!fT;fC=0;e.target.setAttribute('aria-pressed',!!fT);
   $('#cC').setAttribute('aria-pressed',false);drawA();};
  $('#cC').onclick=e=>{fC=!fC;fT=0;e.target.setAttribute('aria-pressed',!!fC);
   $('#cT').setAttribute('aria-pressed',false);drawA();};
  if($('#cQ'))$('#cQ').onclick=e=>{fQ=!fQ;e.target.setAttribute('aria-pressed',!!fQ);drawA();};
  $('#cX').onclick=e=>{fX=!fX;fM=0;e.target.setAttribute('aria-pressed',!!fX);if($('#cM'))$('#cM').setAttribute('aria-pressed',false);drawA();};if($('#cM'))$('#cM').onclick=e=>{fM=!fM;fX=0;e.target.setAttribute('aria-pressed',!!fM);if($('#cX'))$('#cX').setAttribute('aria-pressed',false);drawA();};if($('#cI'))$('#cI').onclick=e=>{fI=!fI;e.target.setAttribute('aria-pressed',!!fI);drawA();};
  document.querySelectorAll('#at th').forEach(th=>{th.tabIndex=0;
   th.onclick=()=>{const k=th.dataset.k;ad=(k===as)?-ad:-1;as=k;drawA();};});
  
  function buildScatter(){const W=760,H=470,P=48,M=26;
   const x=v=>P+(Math.min(Math.abs(v),M)/M)*(W-P-14);
   const y=v=>H-P-(Math.min(Math.abs(v),M)/M)*(H-P-14);
   let s=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="In-sample versus out-of-sample strength">`;
   s+=`<rect x="${P}" y="${H-P-((H-P-14)*2/M)}" width="${W-P-14}" height="${(H-P-14)*2/M}"
    fill="var(--kill)" opacity=".13"/>`;
   s+=`<line x1="${P}" y1="${H-P}" x2="${x(M)}" y2="${y(M)}" stroke="var(--line2)"
    stroke-dasharray="4 4"/>`;
   for(let g=0;g<=M;g+=5){s+=`<line x1="${P}" y1="${y(g)}" x2="${W-14}" y2="${y(g)}"
    stroke="var(--line)"/><text x="${P-8}" y="${y(g)+4}" fill="var(--dim)" font-size="10"
    text-anchor="end" font-family="var(--mono)">${g}</text>
    <text x="${x(g)}" y="${H-P+16}" fill="var(--dim)" font-size="10" text-anchor="middle"
    font-family="var(--mono)">${g}</text>`;}
   // One <circle> per signal was fine at 20k. At 123k it builds a multi-megabyte
   // SVG string and locks the browser, so plot every Nth point plus every signal
   // strong enough to be worth seeing individually. The cloud looks the same;
   // nothing above |t|=8 is ever dropped.
   // |t|>=8 is not rare enough to exempt at this scale -- 24,853 signals clear it,
   // which put 33,822 circles back into the SVG. Exempt only the genuinely extreme.
   const CAP=12000, step=Math.max(1,Math.ceil(D.length/CAP));
   let plotted=0;
   D.forEach((d,i)=>{
    if(i%step&&Math.abs(d.to)<18) return;
    plotted++;
    const c=!d.held?'var(--kill)':(d.ti>0?'var(--trend)':'var(--chop)');
    s+=`<circle cx="${x(d.ti)}" cy="${y(d.to)}" r="2.4" fill="${c}" opacity=".5"/>`;});
   s+=txt(W-16,26,plotted.toLocaleString()+' of '+D.length.toLocaleString()+' plotted',
    {a:'end',s:10,c:'var(--dim)'});
   s+=`<text x="${W/2}" y="${H-8}" fill="var(--mute)" font-size="11" text-anchor="middle">
    |t| in-sample 1999-2015</text>
    <text x="14" y="${H/2}" fill="var(--mute)" font-size="11" text-anchor="middle"
    transform="rotate(-90 14 ${H/2})">|t| out-of-sample 2016-2026</text></svg>`;
   $('#scat').innerHTML=s;}
  
  function buildFam(){const m={};D.forEach(d=>{(m[d.f]=m[d.f]||[]).push(d);});
   const V=STRICT;
   let rows=Object.entries(m).map(([f,a])=>({f,n:a.length,
    bt:Math.max(...a.map(d=>Math.abs(d.to))),
    md:a.map(d=>Math.abs(d.to)).sort((p,q)=>p-q)[Math.floor(a.length/2)],
    hd:a.filter(d=>d.held).length/a.length,
    pa:a.filter(d=>d.held&&GATES.every((g,i)=>g.f(d)>=V[i])).length}));
   rows.sort((a,b)=>b.bt-a.bt);
   $('#ft tbody').innerHTML=rows.map(r=>`<tr><td>${r.f}</td><td>${r.n}</td>
    <td>${r.bt.toFixed(1)}</td><td>${r.md.toFixed(1)}</td><td>${(r.hd*100).toFixed(0)}%</td>
    <td style="color:${r.pa?'var(--trend)':'var(--dim)'}">${r.pa}</td></tr>`).join('');}
  
  
  // ================= GLOSSARY =================
  const GLOSS=[
   {k:'trend_score',n:'Trend score',
    what:'How much progress price is making in one direction over the last ~106 bars.',
    how:'Sum of two standardised readings: |net displacement| / path walked, and the swing sequence (higher high minus previous, plus higher low minus previous, in volatility units). The sequence is SIGNED and SUMMED so a higher high with a lower low nets to zero. Standardised on 1999-2015 only.',
    read:'Higher is more directional. Cut at the in-sample median to give "high"/"low".',
    good:'Separating a pair that is going somewhere from one that is not, on its own history.',
    not:'It is NOT a forecast, and it is NOT strong: out of sample it separates at 0.053 against a surrogate of 0.098 — worse than noise. The most likely misreading is treating a high trend score as a reason to expect continuation.'},
   {k:'chop_score',n:'Chop score',
    what:'How much price is respecting boundaries and returning to them.',
    how:'Sum of four standardised readings: pullback hold, failed breaks, share of time inside the confirmed swing band, and crossings of the band midpoint. The boundary-test count was dropped — it made the score worse.',
    read:'Higher is more range-bound. Cut at the in-sample median.',
    good:'The stronger of the two axes and the only one that holds up out of sample — 0.151 in-sample, 0.156 out.',
    not:'It still does not beat its own surrogate (corrected −0.011). Do NOT read "chop" as "safe to fade".'},
   {k:'shape2',n:'Shape state',
    what:'The 2×2 on the pair of scores: trending, ranging, trend-in-range, neither.',
    how:'trend high + chop low = trending; low + high = ranging; high + high = trend-in-range; low + low = neither. A 5-bar confirmation dwell is applied, so a state must print five consecutive bars before it is adopted.',
    read:'Every bar lands somewhere. "neither" is the honest unclassified bucket at ~20% of days.',
    good:'A vocabulary that always answers, with the ambiguous share halved against the old single-axis version (41% → 20%).',
    not:'"trend-in-range" is mostly MEASUREMENT OVERLAP, not a real regime — those episodes look statistically identical to "neither" (net move 0.62 sd vs 0.64, efficiency 0.154 vs 0.138). Two genuine cases exist in the record (USDJPY Dec 2021–May 2022) and they are the exception.'},
   {k:'activity',n:'Activity',
    what:'How far price travelled over the window, in the pair’s own volatility units.',
    how:'path / (vol × √28), cut into terciles on in-sample data. There is NO VOLUME — FX is decentralised and H.10 is close-only — so distance travelled is the proxy.',
    read:'weak / medium / strong.',
    good:'The only axis in this whole build whose separation survives a surrogate, and only against an IID one (+0.330 on realised vol, p=0.016).',
    not:'It is a proxy for participation, not a measurement of it. Do NOT call it volume.'},
   {k:'combined2',n:'Combined state',
    what:'Activity crossed with shape — twelve cells.',
    how:'Activity is cut JOINTLY with a 0.75 bump, so a weak-activity bar must clear a higher trend bar before being called trending. That beat a separate cut by 0.002 on in-sample, which is a tie.',
    read:'e.g. "strong trending", "weak ranging".',
    good:'Full coverage (1.000 out of sample), 12 usable cells, median run 12 bars, diagonal 0.936.',
    not:'Mean separation 0.072 against a surrogate of 0.078 — corrected −0.006. The grid describes state, it does not beat noise.'},
   {k:'settling',n:'Settling confidence',
    what:'How settled the current state is, from 0.2 on its first bar to 1.0 from the fifth.',
    how:'min(age / 5, 1) on the combined state.',
    read:'A weight, not a state. 22.6% of days carry a reduced one.',
    good:'Making the 4-bar confirmation lag explicit instead of hiding it.',
    not:'It is NOT an early warning. Three fast signals were swept across 3,420 window pairs to try to bridge that lag and none beat its own surrogate.'},
   {k:'m_fail',n:'Failed swings',
    what:'How often price approached a prior extreme without clearing it, then turned back.',
    how:'Rolling count over 106 bars. Approach threshold and turn magnitude were swept 10×7; separation is highest at the LOOSEST threshold.',
    read:'Higher means more rejections at boundaries. Feeds the chop score.',
    good:'Marginally positive against its surrogate (+0.025) and it adds something the scores do not already carry.',
    not:'It works, and NOT for the stated reason. At the best setting "approaching the prior extreme" means reaching 70% of the band, which is most of the time — so it is counting oscillation inside the band, not defended levels.'},
   {k:'m_retr',n:'Retracement depth slope',
    what:'Whether successive pullbacks are getting deeper — a trend tiring.',
    how:'Slope of the last four retracement depths, each measured as pullback ÷ prior impulse between confirmed swings.',
    read:'Negative slope means pullbacks are shallowing. Feeds the trend score.',
    good:'Positive against its surrogate (+0.023) and it is not a restatement of the existing scores.',
    not:'It does NOT lead state changes — lead lift 0.000 against a surrogate of 0.498.'},
   {k:'m_space',n:'Swing spacing slope',
    what:'Whether each new extreme is taking longer to arrive — momentum fading.',
    how:'Slope of the last four gaps, in bars, between confirmed swings. Pure shape, no volatility component.',
    read:'Rising gaps mean a slowing rhythm. Feeds the trend score.',
    good:'The strongest raw descriptor of the four (0.400 out of sample).',
    not:'It sits BELOW its own surrogate (−0.054). Long windows make persistent states and the surrogate gets there too.'},
   {k:'m_panel',n:'Cross-pair',
    what:'How much of this pair’s movement is shared with the rest of the panel.',
    how:'Rolling R² of the pair’s absolute move against the mean absolute move of the 15 pairs sharing NEITHER of its currencies.',
    read:'High means the move is panel-wide; low means idiosyncratic.',
    good:'The ONLY measurement that leads state changes — lift 1.341 against a surrogate of 0.991.',
    not:'It does not describe the present (corrected −0.042), so it is a lead indicator that says nothing about now. And a leg-based version is VACUOUS: 28 pairs from 8 currencies is a rank-7 panel, so any leg index reconstructs the pair exactly (measured lag-0 correlation +1.0000).'},
   {k:'sep',n:'Separation',
    what:'How far apart the states sit on a property they were not built from.',
    how:'One-versus-rest: a state’s mean minus every other state’s, in standard deviations, averaged over autocorrelation, range/path, direction changes and mean crossings.',
    read:'Bigger is a sharper description. Always read the CORRECTED value.',
    good:'Comparing classifiers on the same properties.',
    not:'Raw separation is NOT comparable across classifiers with different state counts or different persistence — more states and longer runs both raise it mechanically. That is why every figure here is corrected against a surrogate carrying the identical classifier.'},
   {k:'surrogate',n:'Surrogate / null',
    what:'The same statistic computed on price with its structure destroyed.',
    how:'Sign randomisation keeps every |return| in place and flips signs, so volatility clustering survives. IID permutation destroys clustering too. Everything is rebuilt on the surrogate — signals AND states.',
    read:'Corrected = real − surrogate. Positive means the classifier beat noise.',
    good:'It is the only test here that carries the full dependence structure, so no independence is assumed anywhere.',
    not:'Sign randomisation is NEARLY DEGENERATE for anything scale-based: mean absolute move is exactly invariant under it, so passing that test proves nothing about an activity axis. Only the IID row is a real test there.'},
   {k:'episode',n:'Episode basis',
    what:'One observation per state run, instead of one per bar.',
    how:'74,004 holdout bars collapse to 4,604 episodes.',
    read:'Any per-bar t-statistic overstates its sample by about 16× and its |t| by about 4×.',
    good:'It is why no per-bar t-statistic appears anywhere in this build.',
    not:'It does not fix cross-pair correlation — 28 pairs from 8 currencies move together. Block bootstrap over calendar dates handles both.'},
   {k:'dwell',n:'Confirmation dwell',
    what:'A new state must print 5 consecutive bars before it is adopted.',
    how:'The categorical equivalent of a hysteresis band. Strictly causal — bar t reads only bars t−4…t.',
    read:'Fixes flickering: 3-bar median runs with 62% under five bars became 13-bar runs with 0.1%.',
    good:'Making the state a regime rather than a signal firing.',
    not:'It costs 4 bars of recognition lag, and it RAISES the surrogate as much as it raises the real value — the corrected separation gets worse, not better, as the dwell lengthens.'}];

  function glossHTML(){
   return GLOSS.map(g=>`<details class="panel" style="margin-bottom:10px">
    <summary style="cursor:pointer;font-weight:600">${g.n} <span class="count">${g.k}</span></summary>
    <div style="margin-top:10px;font-size:13px;line-height:1.65">
    <p><b>What it is.</b> ${g.what}</p>
    <p><b>How it is calculated.</b> ${g.how}</p>
    <p><b>How to read it.</b> ${g.read}</p>
    <p><b>What it is good for.</b> ${g.good}</p>
    <p style="color:var(--chop)"><b>What it is NOT.</b> ${g.not}</p></div></details>`).join('');
  }

  // ================= ARCHIVE BANNERS =================
  const ARCHIVED={
   nb:['The nine-box','Straightness × scale terciles, the first classifier. Superseded by the two-score version. It still holds the highest RAW separation of anything built (0.457 shape, 0.928 activity) but its corrected shape separation is −0.108, and its activity result was compared against the wrong classifier’s null for three revisions.'],
   mt:['Multi-timeframe confluence','Fired 79% before real state changes and 79% before surrogate ones. Dropped.'],
   ld:['Detector ladder','Built against forward efficiency, which is a prediction test. Layer 1 is descriptive; these numbers were never a verdict on the classifier.'],
   st:['Strategy sweep','Money metrics. Out of scope for Layer 1 and kept only as a record.']};

  function archiveBanner(id,title,why){
   const sec=document.getElementById(id); if(!sec||sec.querySelector('.arcban'))return;
   const d=document.createElement('div');
   d.className='note arcban';
   d.style.cssText='border-left:3px solid var(--chop);margin-bottom:14px';
   d.innerHTML='<b>ARCHIVED — '+title+'.</b> '+why+' Kept because it is the record of what was tried, not deleted.';
   sec.insertBefore(d,sec.firstChild);
  }

  // ================= REGIME DETECTOR =================
  let REG=null;
  function loadRegime(){
   if(REG)return Promise.resolve(REG);
   const url=(BUN.meta&&BUN.meta.regime_url)||'app_regime.json';
   $('#rdwrap').innerHTML='<div class="note">Loading the regime feed (~9 MB)…</div>';
   return fetch(url).then(r=>{if(!r.ok)throw new Error('HTTP '+r.status);return r.json();})
    .then(j=>{REG=j;return j;});
  }
  const SCOL={0:'var(--trend)',1:'var(--chop)',2:'#b58900',3:'var(--mute)'};
  function drawRegime(pair){
   const R=REG,P=R.pairs[pair]; if(!P)return;
   const n=R.dates.length, W=980,H=260,L=54,Rp=14,T=12,B=22;
   const yrs=$('#rdyears')?+$('#rdyears').value:10;
   const i0=Math.max(0,n-Math.round(yrs*252)), N=n-i0;
   const px=P.px.slice(i0),st=P.st.slice(i0);
   const fin=px.filter(v=>v!=null);
   const lo=Math.min(...fin),hi=Math.max(...fin),pad=(hi-lo)*.06||1;
   const x=i=>L+i/(N-1)*(W-L-Rp), y=v=>T+(hi+pad-v)/(hi-lo+2*pad)*(H-T-B);
   let g='';
   for(let k=0;k<=4;k++){const v=lo-pad+(hi-lo+2*pad)*k/4;
    g+=`<line x1="${L}" y1="${y(v)}" x2="${W-Rp}" y2="${y(v)}" stroke="var(--line)"/>`
      +txt(L-7,y(v)+4,v.toPrecision(5),{a:'end',m:1,s:10});}
   let seg=[],cur=null;
   for(let i=0;i<N;i++){
    if(px[i]==null){continue;}
    if(st[i]!==cur){if(seg.length>1)g+=`<polyline fill="none" stroke="${SCOL[cur]}" stroke-width="1.6" points="${seg.join(' ')}"/>`;
     seg=seg.length?[seg[seg.length-1]]:[];cur=st[i];}
    seg.push(x(i).toFixed(1)+','+y(px[i]).toFixed(1));}
   if(seg.length>1)g+=`<polyline fill="none" stroke="${SCOL[cur]}" stroke-width="1.6" points="${seg.join(' ')}"/>`;
   for(let k=0;k<6;k++){const i=Math.round(k*(N-1)/5);
    g+=txt(x(i),H-4,R.dates[i0+i].slice(0,7),{a:'middle',m:1,s:10});}
   $('#rdpx').innerHTML=svg(W,H,g);
   const leg=R.shapes.map((s,i)=>`<span style="margin-right:14px"><span style="display:inline-block;width:22px;height:3px;background:${SCOL[i]};vertical-align:middle"></span> ${s}</span>`).join('');
   $('#rdleg').innerHTML=leg;
   function trace(id,keys,names,cols,ttl,zero){
    const H2=140;let s='';
    const all=[].concat(...keys.map(k=>P[k].slice(i0).filter(v=>v!=null)));
    if(!all.length){$(id).innerHTML='';return;}
    let a=Math.min(...all),b=Math.max(...all);if(zero){const m=Math.max(Math.abs(a),Math.abs(b));a=-m;b=m;}
    const pd=(b-a)*.08||1;
    const yy=v=>10+(b+pd-v)/(b-a+2*pd)*(H2-30);
    for(let k=0;k<=2;k++){const v=a-pd+(b-a+2*pd)*k/2;
     s+=`<line x1="${L}" y1="${yy(v)}" x2="${W-Rp}" y2="${yy(v)}" stroke="var(--line)"/>`
       +txt(L-7,yy(v)+4,v.toFixed(2),{a:'end',m:1,s:10});}
    keys.forEach((k,ki)=>{const v=P[k].slice(i0);let pts=[];
     for(let i=0;i<N;i++){if(v[i]==null){continue;}pts.push(x(i).toFixed(1)+','+yy(v[i]).toFixed(1));}
     s+=`<polyline fill="none" stroke="${cols[ki]}" stroke-width="1.3" points="${pts.join(' ')}"/>`;});
    const lg=names.map((nm,i)=>`<span style="margin-right:12px"><span style="display:inline-block;width:18px;height:3px;background:${cols[i]};vertical-align:middle"></span> ${nm}</span>`).join('');
    $(id).innerHTML='<div class="count" style="margin:6px 0 2px">'+ttl+' &nbsp; '+lg+'</div>'+svg(W,H2,s);
   }
   trace('#rdscores',['tr','ch'],['trend score','chop score'],['var(--trend)','var(--chop)'],
     'THE TWO SCORES — plotted separately so their independence is visible (pooled correlation −0.35)',1);
   trace('#rdm1',['mf'],['failed swings'],['#7aa2f7'],'FAILED SWINGS — rolling count of rejections at a prior extreme (feeds chop)');
   trace('#rdm2',['mr','ms'],['retracement slope','swing-spacing slope'],['#bb9af7','#9ece6a'],
     'RETRACEMENT DEPTH and SWING SPACING — deepening pullbacks and widening gaps (feed trend)',1);
   trace('#rdm3',['mp'],['cross-pair R²'],['#e0af68'],'CROSS-PAIR — how much of the move is shared with the 15 pairs sharing neither currency');
   const cur2=st.filter(v=>v!=null);
   const li=cur2.length?cur2[cur2.length-1]:3;
   const last=cur2.length?R.shapes[li]:'\u2014';
   const sh={};cur2.forEach(v=>{sh[v]=(sh[v]||0)+1;});
   $('#rdnow').innerHTML='<b>'+pair+'</b> is currently <b style="color:'
    +SCOL[cur2[cur2.length-1]]+'">'+last+'</b>. Over the window shown: '
    +R.shapes.map((s,i)=>s+' '+((sh[i]||0)/cur2.length*100).toFixed(0)+'%').join(' · ');
  }
  function initRegime(){
   loadRegime().then(R=>{
    const pairs=Object.keys(R.pairs).sort();
    $('#rdwrap').innerHTML=
     '<div class="tools" style="margin-bottom:10px">Pair '
     +'<select id="rdpair">'+pairs.map(p=>`<option>${p}</option>`).join('')+'</select>'
     +' &nbsp; Years <select id="rdyears"><option>3</option><option>5</option>'
     +'<option selected>10</option><option>30</option></select>'
     +'<span class="count" id="rdnow" style="margin-left:14px"></span></div>'
     +'<div id="rdpx"></div><div class="count" id="rdleg" style="margin:4px 0 14px"></div>'
     +'<div id="rdscores"></div><div id="rdm1"></div><div id="rdm2"></div><div id="rdm3"></div>'
     +'<div class="note" style="margin-top:14px"><b>No money metrics on this screen, by design.</b> '
     +'It shows what state a pair is in and what price did. What that was worth is Layer 2 and is not here.</div>';
    const go=()=>drawRegime($('#rdpair').value);
    $('#rdpair').onchange=go;$('#rdyears').onchange=go;
    $('#rdpair').value=pairs.indexOf('EURUSD')>=0?'EURUSD':pairs[0];go();
   }).catch(e=>{$('#rdwrap').innerHTML='<div class="note" style="color:var(--chop)">'
     +'Could not load app_regime.json ('+e.message+'). It must sit beside app_data.json.</div>';});
  }

  // ================= PAIR CHARACTER =================
  function buildShared(){
   const f=(v,n)=>v==null||v===''?'—':(+v).toFixed(n==null?3:n);
   const S=BUN.stcorrs||[],C=BUN.stcorr||[],BK=BUN.stblk||[],
         BR=BUN.stbrd||[],NF=BUN.stneff||[],EX=BUN.stext||[];
   if(!S.length){$('#shwrap').innerHTML='';return;}
   const gs=b=>S.find(r=>r.block===b)||{};
   const is=gs('is'),oos=gs('oos');

   let h='<h3>Shared states &mdash; how many independent bets are there?</h3>'
    +'<div class="note" style="border-left:3px solid var(--dim)">'
    +'<b>What this is.</b> If fourteen pairs read “trending” on the same day, is '
    +'that fourteen observations or one? This measures how much the 28 state '
    +'calls overlap.<br><br>'
    +'<b>What this is NOT.</b> It does <b>not change any state call</b>, does not '
    +'feed the classifier, and is not a routing rule. It is a counting number for '
    +'Layer 3/4: how many <i>independent</i> bets exist on a given day.</div>'
    +'<div class="note" style="border-left:3px solid var(--kill)">'
    +'<b>The rank-7 floor, which bounds every number below.</b> The 28 pairs are '
    +'built from 8 currencies, so the panel has <b>rank 7, not 28</b>. EURJPY '
    +'<i>is</i> EURUSD plus USDJPY — by construction, not by correlation. '
    +'Agreement between pairs sharing a leg is partly an <b>identity</b> and is '
    +'not evidence that the market moved together. The question was never whether '
    +'these overlap; it is <i>how much</i>, and <i>where</i>.</div>'

    +'<div class="tw"><table><thead><tr><th>Block</th><th>Days</th>'
    +'<th>Raw agreement</th><th>Expected by chance</th><th>Excess</th>'
    +'<th>Mean kappa</th><th>Range</th></tr></thead><tbody>'
    +S.map(r=>'<tr><td>'+r.block+'</td><td>'+r.days+'</td><td>'+f(r.mean_observed)
     +'</td><td>'+f(r.mean_expected)+'</td><td><b>+'+f(r.excess_over_chance)
     +'</b></td><td><b>'+f(r.mean_kappa)+'</b></td><td>'+f(r.min_kappa)+' to '
     +f(r.max_kappa)+'</td></tr>').join('')
    +'</tbody></table><div class="count"><b>Agreement is chance-corrected.</b> Two '
    +'pairs both sitting in “ranging” 45% of the time agree ~27% of days by '
    +'coincidence alone, so raw agreement would make everything look enormous. '
    +'<b>kappa = (observed − expected) / (1 − expected)</b>: 0 means no more '
    +'agreement than the marginals force. Complete-case days only, so kappa is '
    +'exact rather than approximate. — <code>results/state_correlation.csv</code>'
    +'</div></div>'

    +'<div class="note"><b>The headline: raw agreement is ~30%, but almost all of '
    +'that is coincidence.</b> The excess over chance is only <b>+'
    +f(is.excess_over_chance)+'</b> in-sample and <b>+'+f(oos.excess_over_chance)
    +'</b> out-of-sample, and mean kappa is <b>'+f(is.mean_kappa)+' → '
    +f(oos.mean_kappa)+'</b>. <b>States are far less shared than they look.</b> '
    +'And the figure repeats almost exactly across halves, which is the reason to '
    +'trust it.</div>'

    +'<div class="tw"><table><thead><tr><th>Block</th>'
    +'<th>Pairs sharing a currency</th><th>Pairs sharing none</th><th>Gap</th>'
    +'</tr></thead><tbody>'
    +S.map(r=>'<tr><td>'+r.block+'</td><td><b>'+f(r.share_leg_kappa)+'</b> <span '
     +'class="count">'+r.n_share_leg+' pairs-of-pairs</span></td><td>'
     +f(r.no_leg_kappa)+' <span class="count">'+r.n_no_leg+'</span></td><td><b>'
     +f(r.share_leg_kappa-r.no_leg_kappa)+'</b></td></tr>').join('')
    +'</tbody></table><div class="count"><b>Yes — states cluster around a shared '
    +'currency leg.</b> Sharing a leg roughly <b>triples</b> agreement. A pair '
    +'belongs to two blocks, so these are not a partition of the pairs but of the '
    +'378 <i>pairs-of-pairs</i>, by whether the two share a leg.</div></div>';

   // ---- the full 28x28 matrix ----
   const PR=[...new Set(C.map(r=>r.pair_a).concat(C.map(r=>r.pair_b)))].sort();
   const key=(a,b)=>a<b?a+'|'+b:b+'|'+a;
   const MAP={is:{},oos:{}};
   C.forEach(r=>{if(MAP[r.block])MAP[r.block][key(r.pair_a,r.pair_b)]=r.kappa;});
   const cell=v=>{
    if(v==null)return 'background:transparent';
    const a=Math.min(1,Math.abs(v)/0.40).toFixed(2);
    return 'background:rgba('+(v>=0?'86,166,124':'201,92,92')+','+a+')';};
   const grid=b=>'<table style="border-collapse:collapse;font-size:9px">'
    +'<thead><tr><th></th>'+PR.map(p=>'<th style="writing-mode:vertical-rl;'
     +'text-orientation:mixed;padding:1px;font-weight:500">'+p+'</th>').join('')
    +'</tr></thead><tbody>'
    +PR.map(a=>'<tr><td style="padding:1px 4px;white-space:nowrap;font-weight:500">'
      +a+'</td>'+PR.map(b2=>{
        if(a===b2)return '<td style="background:var(--dim);width:14px;height:14px"'
         +' title="'+a+' with itself"></td>';
        const v=MAP[b][key(a,b2)];
        return '<td style="width:14px;height:14px;'+cell(v)+'" title="'+a+' / '+b2
         +': kappa '+(v==null?'—':f(v))+'"></td>';}).join('')+'</tr>').join('')
    +'</tbody></table>';
   h+='<div class="tw"><div style="margin-bottom:6px">'
    +'<button type="button" class="shbtn" data-b="is" style="margin-right:6px">'
    +'In-sample</button><button type="button" class="shbtn" data-b="oos">'
    +'Out-of-sample</button></div>'
    +'<div id="shmat-is">'+grid('is')+'</div>'
    +'<div id="shmat-oos" hidden>'+grid('oos')+'</div>'
    +'<div class="count"><b>The full 28&times;28 matrix.</b> Green is agreement '
    +'above chance, red below; intensity saturates at |kappa| = 0.40. Hover any '
    +'cell for the exact figure. <b>The visible block structure is currency '
    +'blocks</b> — and it is largely the rank-7 identity, not co-movement. — '
    +'<code>results/state_correlation.csv</code></div></div>';

   if(BK.length){
    const per=[...new Set(BK.map(r=>r.block_period))];
    const ccys=[...new Set(BK.map(r=>r.block))];
    h+='<div class="tw"><table><thead><tr><th>Currency block</th>'
     +per.map(p=>'<th>'+p+'</th>').join('')+'</tr></thead><tbody>'
     +ccys.map(c=>'<tr><td><b>'+c+'</b></td>'+per.map(p=>{
       const r=BK.find(x=>x.block===c&&x.block_period===p);
       return '<td>'+(r?f(r.mean_kappa):'—')+'</td>';}).join('')+'</tr>').join('')
     +'</tbody></table><div class="count">Mean kappa among the 7 pairs carrying '
     +'each currency. <b>JPY is the most synchronised block in both halves</b> — '
     +'the yen pairs move as a group more than any other currency\'s do. '
     +'<b>EUR and GBP are the least.</b> — <code>results/state_blocks.csv</code>'
     +'</div></div>';}

   const dist=BR.filter(r=>r.metric==='modal_count distribution');
   if(dist.length){
    const mx=Math.max(...dist.map(r=>r.share));
    h+='<div class="tw"><table><thead><tr><th>Pairs sharing the modal state</th>'
     +'<th>Days</th><th>Share</th><th></th><th>Usually</th></tr></thead><tbody>'
     +dist.map(r=>'<tr><td>'+r.modal_count+' of 28</td><td>'+r.days+'</td><td>'
      +f(r.share,3)+'</td><td style="min-width:120px"><div style="height:9px;'
      +'background:var(--trend);width:'+(100*r.share/mx).toFixed(1)+'%"></div>'
      +'</td><td>'+r.modal_state_mode+'</td></tr>').join('')
     +'</tbody></table><div class="count"><b>Breadth. The floor is 7, not 1</b> — '
     +'four states over 28 pairs means the biggest group cannot be smaller than '
     +'ceil(28/4). — <code>results/state_breadth.csv</code></div></div>';}

   const bs=BR.filter(r=>r.metric==='modal_count');
   if(bs.length){
    h+='<div class="note"><b>Is FX one market or 28?</b> Overwhelmingly the '
     +'latter. The modal state is shared by a median of <b>'+f(bs[0].median,0)
     +' of 28</b> pairs, 20 or more on only <b>'+f(100*bs[0].share_ge_20,1)
     +'%</b> of days in-sample and <b>'+f(100*bs[1].share_ge_20,1)+'%</b> out-of-'
     +'sample, and <b>never 24 or more</b> in 6,694 days. The widest day on record '
     +'reached 23. <b>FX is not one market</b> — but it is not 28 separate ones '
     +'either.</div>';}

   const cr=BR.filter(r=>r.metric==='widest decile vs crisis calendar'&&r.p_null!=null);
   if(cr.length){
    const r=cr[0];
    h+='<div class="tw"><table><thead><tr><th>Widest decile</th><th>Days</th>'
     +'<th>In a crisis window</th><th>Base</th><th>Lift</th><th>Null</th>'
     +'<th>p</th></tr></thead><tbody><tr><td>modal count ≥ '+f(r.threshold,0)
     +'</td><td>'+r.days+'</td><td>'+f(r.p)+'</td><td>'+f(r.base)+'</td><td><b>×'
     +f(r.lift,2)+'</b></td><td>×'+f(r.null_mean_lift,2)+' ± '+f(r.null_sd,2)
     +'</td><td><b>'+f(r.p_null)+'</b></td></tr></tbody></table>'
     +'<div class="count"><b>Do the widest days coincide with the '+r.events
     +'-event crisis calendar? No.</b> The lift is ×'+f(r.lift,2)+', which looks '
     +'like something until it is compared with a circular-shift null of the '
     +'breadth series: <b>p='+f(r.p_null)+'</b>. Breadth and crisis are not the '
     +'same phenomenon — <b>the widest days are usually broad <i>trending</i>, not '
     +'panic</b>.</div></div>';}

   h+='<div class="tw"><table><thead><tr><th>Block</th>'
    +'<th>N<sub>eff</sub> full sample</th><th>Rolling mean</th><th>Rolling range</th>'
    +'<th>Eigenvalue check</th></tr></thead><tbody>'
    +['is','oos'].map(b=>{
      const r=gs(b),n=NF.filter(x=>x.block===b);
      if(!n.length)return '';
      const mn=Math.min(...n.map(x=>x.neff_equicorr)),
            mx=Math.max(...n.map(x=>x.neff_equicorr)),
            av=n.reduce((a,x)=>a+x.neff_equicorr,0)/n.length,
            ae=n.reduce((a,x)=>a+x.neff_eigen,0)/n.length;
      return '<tr><td>'+b+'</td><td><b>'+f(r.neff_equicorr,2)+'</b> of 28</td><td>'
       +f(av,2)+'</td><td>'+f(mn,2)+' to '+f(mx,2)+'</td><td>'+f(ae,2)+'</td></tr>';
     }).join('')
    +'</tbody></table><div class="count"><b>The routing number.</b> '
    +'N<sub>eff</sub> = N / (1 + (N−1)·k̄) — 28 if states were independent, 1 if '
    +'all 28 always agreed. Rolling 252-day windows, step 21. — '
    +'<code>results/state_neff_rolling.csv</code></div></div>'

    +'<div class="note" style="border-left:3px solid var(--trend)">'
    +'<b>The number for Layer 3/4: a day of 28 state readings is worth about '
    +'<span style="font-size:1.15em">13</span> independent observations, not 28.</b> '
    +'It is stable across halves ('+f(is.neff_equicorr,1)+' → '
    +f(oos.neff_equicorr,1)+') but it moves a lot through time — the rolling range '
    +'runs from under 7 to over 26, so <b>on the most synchronised years fewer '
    +'than a quarter of the pairs are telling you anything new</b>.</div>'

    +'<div class="note"><b>Two constructions, and they disagree — stated rather '
    +'than picked over.</b> The equicorrelation formula above gives ~13 on the '
    +'full sample; an eigenvalue participation ratio on the same matrix gives '
    +'~23. They agree closely on rolling windows (~15 both) and diverge on the '
    +'full sample because equicorrelation assumes <i>every</i> pairing shares the '
    +'same kappa, while the real structure is <b>a few strong currency blocks in a '
    +'sea of near-zero</b>. <b>Use ~13</b>: it is the conservative one, and for '
    +'counting independent bets the cost of overstating independence is higher '
    +'than the cost of understating it.</div>';

   if(EX.length){
    const t=EX.filter(r=>r.block==='is'&&r.end==='top').slice(0,6);
    h+='<div class="tw"><table><thead><tr><th>Strongest cells (IS)</th>'
     +'<th>kappa</th><th>Raw</th><th>Chance</th><th>Shared leg</th></tr></thead>'
     +'<tbody>'+t.map(r=>'<tr><td>'+r.pair_a+' / '+r.pair_b+'</td><td><b>'
      +f(r.kappa)+'</b></td><td>'+f(r.observed)+'</td><td>'+f(r.expected)
      +'</td><td>'+r.shared_leg+'</td></tr>').join('')
     +'</tbody></table><div class="count"><b>Every one of the strongest cells '
     +'shares a leg</b> — that is the rank-7 identity showing up, not a discovery. '
     +'But sharing a leg does not <i>guarantee</i> agreement: GBPCAD/USDCAD is '
     +'among the <b>weakest</b> cells on the holdout at −0.157 despite both '
     +'carrying CAD. — <code>results/state_pairs_extremes.csv</code></div></div>';}

   h+='<div class="note" style="border-left:3px solid var(--kill)">'
    +'<b>The caveat that decides how this can be used.</b> The <i>aggregate</i> '
    +'repeats almost perfectly across halves (mean kappa '+f(is.mean_kappa)+' → '
    +f(oos.mean_kappa)+'), but <i>individual cells</i> repeat only moderately — '
    +'Spearman <b>'+f(is.pairwise_is_oos_spearman)+'</b> over 378 pairs-of-pairs. '
    +'<b>So use the aggregate; do not use a single cell as a lookup.</b> “These '
    +'two pairs agreed last decade” is not a reliable statement about the next '
    +'one.</div>';
   $('#shwrap').innerHTML=h;
   document.querySelectorAll('.shbtn').forEach(b=>b.onclick=()=>{
    $('#shmat-is').hidden=(b.dataset.b!=='is');
    $('#shmat-oos').hidden=(b.dataset.b!=='oos');});
  }

  function buildCharacter(){
   const C=BUN.paircha||[],RK=BUN.pairrank||[];
   if(!C.length){$('#pcwrap').innerHTML='<div class="note">pair_character.csv not in the feed.</div>';return;}
   const f=(v,n)=>v==null||v===''?'—':(+v).toFixed(n==null?3:n);
   const rk=C.slice().sort((a,b)=>b.trendiness-a.trendiness);
   const mx=Math.max(...C.map(r=>r.share_trending)),mn=Math.min(...C.map(r=>r.share_trending));
   let h='<div class="note"><b>What each pair IS, not how well the classifier reads it.</b> '
    +'Ranked by trendiness = share of days trending minus share ranging, pooled '
    +'standardisation so cross-pair differences survive. <b>Read the verdict at the '
    +'bottom before using this to route anything.</b></div>'
    +'<div class="tw"><table><thead><tr><th>#</th><th>Pair</th><th>Trending</th>'
    +'<th>Ranging</th><th>Both</th><th>Neither</th><th>Trendiness</th>'
    +'<th>Median trend run</th><th>Median range run</th><th>Longest trend</th>'
    +'<th>Longest range</th></tr></thead><tbody>'
    +rk.map((r,i)=>{const w=(r.share_trending-mn)/((mx-mn)||1);
     return '<tr><td>'+(i+1)+'</td><td><b>'+r.pair+'</b></td>'
      +'<td><span style="display:inline-block;height:8px;background:var(--trend);width:'
      +(4+w*46).toFixed(0)+'px;vertical-align:middle;margin-right:6px"></span>'
      +f(r.share_trending)+'</td><td>'+f(r.share_ranging)+'</td><td>'
      +f(r['share_trend-in-range'])+'</td><td>'+f(r.share_neither)+'</td><td><b>'
      +(r.trendiness>0?'+':'')+f(r.trendiness)+'</b></td><td>'+f(r.med_trending,0)
      +'</td><td>'+f(r.med_ranging,0)+'</td><td>'+f(r.max_trending,0)+'</td><td>'
      +f(r.max_ranging,0)+'</td></tr>';}).join('')+'</tbody></table></div>';
   h+='<div class="note" style="border-left:3px solid var(--chop);margin-top:16px">'
    +'<b>THE RANKING DOES NOT HOLD, AND PAIRS DIFFER LESS THAN NOISE.</b><br><br>'
    +'Rank correlation between 1999–2015 and 2016–2026: share trending <b>+0.002</b>, '
    +'trendiness <b>−0.087</b>, median ranging run −0.293. Individual moves are violent — '
    +'NZDJPY rank 2→23, NZDUSD 4→26, CHFJPY 24→2.<br><br>'
    +'Cross-pair spread of trending share: real sd <b>0.0337</b> against a sign-surrogate '
    +'sd of <b>0.0430 ± 0.0061</b>; real range 0.130 against 0.180. '
    +'<b>28 surrogate pairs, which have no character at all, spread wider than the real ones.</b> '
    +'p(dispersion) = 1.000, p(rank correlation) = 0.625.<br><br>'
    +'So there is no structurally trendy set and no structurally choppy set to route on — '
    +'not on this classifier. Every pair sits between 23% and 36% trending, and only 6 of 28 '
    +'have positive trendiness at all. <b>The one per-pair structure that does show up is in '
    +'the transitions:</b> direct trend↔range moves are rare (10–12%), pairs pass through an '
    +'intermediate state, and the most direct are all JPY crosses (CHFJPY 0.208, USDJPY 0.204, '
    +'EURJPY 0.172) against GBPCAD 0.021. That is untested against a null and is an '
    +'observation, not a finding.</div>';
   $('#pcwrap').innerHTML=h;
  }

  // ================= CURRENT CLASSIFIER: STATES AND VALIDATION =================
  function buildRefit(){
   const f=(v,n)=>v==null||v===''?'—':(+v).toFixed(n==null?3:n);
   const IV=BUN.rfinv||[],AG=BUN.rfagr||[],DG=BUN.rfdis||[],TH=BUN.rfthr||[];
   if(!AG.length){$('#rfwrap').innerHTML='';return;}
   const CE=['trending','ranging','trend-in-range','neither'];
   const vints=[...new Set(AG.map(r=>r.vintage))].sort((a,b)=>a-b);
   const post=AG.filter(r=>r.scope==='post-vintage only'&&r.state==='ALL');
   const nref=IV.filter(r=>r.kind==='REFIT').reduce((a,r)=>a+ +r.count,0);
   const worst=post.reduce((a,r)=>r.agreement<a.agreement?r:a,post[0]);

   let h='<h3>Refit stability &mdash; does re-estimating produce a different machine?</h3>'
    +'<div class="note" style="border-left:3px solid var(--dim)">'
    +'<b>The question.</b> If every fitted quantity is re-derived from data '
    +'ending at an earlier date, do the state calls stay the same? This matters '
    +'because <b>live is a refit</b> — every day adds data that would move a cut '
    +'point if anyone re-estimated it. If calls flip on refit, live behaviour '
    +'will not match the validated history.<br><br>'
    +'<b>Measurement only.</b> Nothing here changes a state call or the shipped '
    +'classifier.</div>'

    +'<div class="tw"><table><thead><tr><th>Component</th><th>Kind</th>'
    +'<th>Numbers</th><th>Detail</th></tr></thead><tbody>'
    +IV.map(r=>'<tr><td>'+r.component+'</td><td><b style="color:'
     +(r.kind==='REFIT'?'var(--trend)':(r.kind==='FIXED'?'var(--dim)'
      :'var(--chop)'))+'">'+r.kind+'</b></td><td>'+(+r.count||'—')+'</td><td>'
     +'<span class="count">'+r.detail+'</span></td></tr>').join('')
    +'</tbody></table><div class="count"><b>The inventory is a deliverable in '
    +'itself</b> — “refit stability” means nothing until it says which numbers '
    +'move. <b>'+nref+' numbers are estimated from data</b>; the window lengths, '
    +'dwell, hysteresis band, equal weights and cell boundaries move with '
    +'nothing. — <code>results/refit_inventory.csv</code></div></div>'

    +'<div class="note" style="border-left:3px solid var(--trend)">'
    +'<b>The control, and why it is here.</b> The shipped classifier fits on data '
    +'before 2016, so <b>the 2015 vintage IS the shipped fit</b> and must '
    +'reproduce it exactly. It does: <b>1.0000</b> over 189,211 labelled '
    +'pair-bars, asserted in the run. A refit test that cannot reproduce its own '
    +'starting point is measuring its own plumbing.<br><br>'
    +'<b>An earlier version of this test returned exactly 100% and was wrong.</b> '
    +'The cut points were built by ranking over the whole sample, so refitting '
    +'changed nothing because nothing was actually being fitted. That bug is '
    +'fixed — and a suspiciously perfect number here would mean it had '
    +'returned.</div>'

    +'<div class="tw"><table><thead><tr><th>Vintage</th><th>Fitted through</th>'
    +'<th>Agreement, all days</th><th>Agreement, post-vintage</th>'
    +'<th>Chance</th><th>kappa</th></tr></thead><tbody>'
    +vints.map(v=>{
      const a=AG.find(r=>r.vintage===v&&r.scope==='all overlapping days'&&r.state==='ALL'),
            b=AG.find(r=>r.vintage===v&&r.scope==='post-vintage only'&&r.state==='ALL');
      if(!a||!b)return '';
      const ctl=(v===2015);
      return '<tr'+(ctl?' style="opacity:.75"':'')+'><td>'+v+(ctl?
        ' <span class="count">control</span>':'')+'</td><td>'+v+'-12-31</td><td>'
       +f(a.agreement,4)+'</td><td><b>'+f(b.agreement,4)+'</b></td><td>'
       +f(b.expected,4)+'</td><td>'+f(b.kappa)+'</td></tr>';}).join('')
    +'</tbody></table><div class="count"><b>Post-vintage is the number that '
    +'matters</b> — it is the live case, a cut point estimated on the past applied '
    +'to data it never saw. Agreement is shown beside the agreement forced by the '
    +'marginals alone (~27%), and kappa corrects for it. — '
    +'<code>results/refit_agreement.csv</code></div></div>'

    +'<div class="note"><b>The answer: the classifier survives re-estimation.</b> '
    +'Post-vintage agreement runs <b>'+f(worst.agreement,3)+' to '
    +f(Math.max(...post.filter(r=>r.vintage!==2015).map(r=>r.agreement)),3)
    +'</b> across five independent refits, chance-corrected kappa <b>0.92 to '
    +'0.95</b>. Refitting from a fit window seven years shorter still reproduces '
    +'roughly <b>19 state calls in 20</b>.</div>'

    +'<div class="tw"><table><thead><tr><th>Vintage</th>'
    +CE.map(s2=>'<th>'+s2+'</th>').join('')+'</tr></thead><tbody>'
    +vints.map(v=>'<tr><td>'+v+'</td>'+CE.map(s2=>{
      const r=AG.find(x=>x.vintage===v&&x.scope==='post-vintage only'&&x.state===s2);
      const q=r?r.agreement:null;
      return '<td'+(q!=null&&q<0.9?' style="color:var(--chop)"':'')+'>'
       +(q==null?'—':f(q))+'</td>';}).join('')+'</tr>').join('')
    +'</tbody></table><div class="count"><b>Which states flip most?</b> Not the '
    +'ones you would fear. <b>“trending” is the most stable</b> — 0.97 to 0.99 on '
    +'every vintage after 2012. <b>“neither” is the least</b>, bottoming at 0.860 '
    +'on the 2024 vintage: it is the residual cell, so a bar lands there by '
    +'failing both cuts and it inherits the wobble of both.</div></div>';

   if(DG.length){
    h+='<div class="tw"><table><thead><tr><th>Vintage</th>'
     +'<th>Disagreeing bars</th><th>Median run</th><th>In runs &ge;5</th>'
     +'<th>In runs &ge;20</th><th>Episodes</th><th>Fully relabelled</th>'
     +'</tr></thead><tbody>'
     +DG.map(r=>'<tr><td>'+r.vintage+'</td><td>'+r.disagreeing_bars+'</td><td>'
      +f(r.median_run,1)+'</td><td>'+f(r.share_of_bars_in_runs_ge5)+'</td><td>'
      +f(r.share_of_bars_in_runs_ge20)+'</td><td>'+r.episodes+'</td><td><b>'
      +f(r.share_fully_relabelled)+'</b></td></tr>').join('')
     +'</tbody></table><div class="count"><b>Boundary noise or structural '
     +'drift?</b> Two very different failures look identical in an agreement '
     +'rate. Scattered days are bars sitting on a cut point — unavoidable and '
     +'harmless. Whole episodes relabelled would be the classifier telling a '
     +'different story about the same stretch of market. — '
     +'<code>results/refit_disagreement.csv</code></div></div>'
     +'<div class="note"><b>It is mostly boundary noise.</b> The median '
     +'disagreement run is <b>3 to 4 bars — below the 5-bar confirmation '
     +'dwell</b>, so most disagreement is shorter than the window the classifier '
     +'needs to adopt a state at all. Only <b>3 to 6% of episodes are fully '
     +'relabelled</b>. Read the “in runs &ge;5” column with care: the dwell means '
     +'a relabelling cannot be one bar wide by construction, so that share is '
     +'partly forced. The median being <i>below</i> the dwell is the informative '
     +'part.</div>';}

   if(TH.length){
    const key=['mt','mc','mt_in_sd','mc_in_sd','act_cut_lo','act_cut_hi'];
    const nm={mt:'trend score cut (mt)',mc:'chop score cut (mc)',
              mt_in_sd:'mt, in sd of its score',mc_in_sd:'mc, in sd of its score',
              act_cut_lo:'activity cut, lower',act_cut_hi:'activity cut, upper'};
    h+='<div class="tw"><table><thead><tr><th>Parameter</th>'
     +vints.map(v=>'<th>'+v+(v===2015?'*':'')+'</th>').join('')+'<th>Max move</th>'
     +'</tr></thead><tbody>'
     +key.map(k=>{
       const vals=vints.map(v=>{const r=TH.find(x=>+x.vintage===v);
         return r?+r[k]:null;});
       const b=vals[vints.indexOf(2015)];
       const mx=Math.max(...vals.map((x,i)=>vints[i]===2015?0:Math.abs(x-b)));
       return '<tr><td>'+nm[k]+'</td>'+vals.map(x=>'<td>'+f(x,4)+'</td>').join('')
        +'<td><b>'+f(mx,4)+'</b></td></tr>';}).join('')
     +'</tbody></table><div class="count">* 2015 is the shipped fit and the '
     +'reference row. — <code>results/refit_thresholds.csv</code></div></div>'
     +'<div class="note"><b>The cut points barely move.</b> In sd units of the '
     +'score they cut — <b>the only scale on which the question is answerable</b> '
     +'— the trend cut moves at most <b>0.006 sd</b> and the chop cut <b>0.003 '
     +'sd</b> across fifteen years of refitting. The activity cuts move <b>0.1%</b>. '
     +'The standardisation statistics move most, and still only up to 5.1% '
     +'(mean_hold, 2024 vintage).<br><br>'
     +'<b>Why the percentages are not the headline.</b> mc sits within 0.005 of '
     +'zero, so its <i>relative</i> change reads <b>+211%</b> while the absolute '
     +'move is 0.006. That figure is in the file and is meaningless; the sd-unit '
     +'row is the one to read.</div>';}

   const WS=BUN.wsens||[];
   if(WS.length){
    const wins=[...new Set(WS.map(r=>r.window))].sort((a,b)=>a-b);
    const all=w=>WS.find(r=>r.window===w&&r.state==='ALL')||{};
    h+='<h3 style="margin-top:26px">Window sensitivity &mdash; the companion check</h3>'
     +'<div class="note" style="border-left:3px solid var(--dim)">'
     +'<b>Refit asked whether re-estimating the fitted numbers changes the '
     +'calls. This asks about the one big number that is <i>not</i> fitted:</b> '
     +'the lookback, fixed by construction at <b>106 bars</b>. Does it sit on a '
     +'cliff or a plateau?<br><br>'
     +'<b>This is not a re-tune.</b> The shipped window stays at 106. Nothing is '
     +'selected, no window is compared on separation or any quality measure, and '
     +'none is proposed. 90 and 120 were declared before running, chosen only as '
     +'“near”, and the measure is the <b>same per-day agreement</b> the refit '
     +'test uses so the two read against each other.</div>'
     +'<div class="tw"><table><thead><tr><th>Lookback</th><th>Agreement</th>'
     +'<th>Chance</th><th>kappa</th>'
     +CE.map(s2=>'<th>'+s2+'</th>').join('')+'</tr></thead><tbody>'
     +wins.map(w=>{const a=all(w),ctl=(w===106);
       return '<tr'+(ctl?' style="opacity:.75"':'')+'><td>'+w+' bars'+(ctl?
        ' <span class="count">shipped / control</span>':'')+'</td><td><b>'
        +f(a.agreement,4)+'</b></td><td>'+f(a.expected,4)+'</td><td>'+f(a.kappa)
        +'</td>'+CE.map(s2=>{const r=WS.find(x=>x.window===w&&x.state===s2);
          const q=r?r.agreement:null;
          return '<td'+(q!=null&&q<0.8?' style="color:var(--chop)"':'')+'>'
           +(q==null?'—':f(q))+'</td>';}).join('')+'</tr>';}).join('')
     +'</tbody></table><div class="count">Rebuilding at 106 reproduces the '
     +'shipped states exactly (1.0000, asserted in the run). The lookback moves '
     +'<code>disp</code>, <code>tests</code>, <code>inside</code> and '
     +'<code>revert</code>; it does not touch <code>fails</code>, '
     +'<code>seq</code>, the swing width, the activity axis, the dwell or any '
     +'cut rule. — <code>results/window_sensitivity.csv</code></div></div>'
     +'<div class="note" style="border-left:3px solid var(--kill)">'
     +'<b>The result, and it is not the comfortable one.</b> '
     +f(all(90).agreement,3)+' at 90 bars and '+f(all(120).agreement,3)+' at 120, '
     +'against <b>0.939&ndash;0.964</b> for refit. Moving the lookback by 15% '
     +'changes roughly <b>one call in six</b>; re-estimating every fitted number '
     +'from a fit window seven years shorter changes <b>one in twenty</b>. '
     +'<b>The window is a bigger lever than the fitting.</b><br><br>'
     +'The disagreements are a different <i>kind</i>, too. Under refit the median '
     +'run was 3&ndash;4 bars — <b>below</b> the 5-bar dwell — and 3&ndash;6% of '
     +'episodes were fully relabelled: boundary noise. Here the median run is '
     +'<b>7 bars, above the dwell</b>, and <b>15&ndash;16% of episodes are fully '
     +'relabelled</b>. Changing the window does not jitter the edges; it tells a '
     +'different story about whole stretches of market.<br><br>'
     +'<b>It is still not a cliff</b> — kappa 0.74 and 0.77 is substantial, and '
     +'120 sits closer to the shipped read than 90, a monotone drift rather than '
     +'a discontinuity. What it means: the lookback is a <b>real choice with real '
     +'consequences</b>, not a free parameter. That argues for leaving it locked '
     +'and documented, and against reading any single state call as though the '
     +'window were incidental to it.</div>'
     +'<div class="note"><b>The same cells are fragile as in the refit test.</b> '
     +'trending and ranging hold ~0.85 at both windows; <b>trend-in-range and '
     +'neither fall to 0.73</b> at 90 bars. The overlap cell and the residual '
     +'cell inherit the wobble of both cuts.</div>';}

   h+='<div class="note" style="border-left:3px solid var(--kill)">'
    +'<b>What this does NOT establish.</b> <code>DROP_TESTS</code> and '
    +'<code>BUMP = 0.75</code> were chosen by in-sample comparison and are held '
    +'fixed across every vintage. So this measures the stability of the '
    +'<b>estimated parameters</b>, not of the <b>selection decisions</b>. '
    +'Re-running those choices at each vintage is a larger test and is not '
    +'claimed here. It also says nothing about whether the states are '
    +'<i>useful</i> — only that they are reproducible.</div>';
   $('#rfwrap').innerHTML=h;
  }

  function buildCurrentStates(){
   const f=(v,n)=>v==null||v===''?'—':(+v).toFixed(n==null?3:n);
   const RL=(BUN.runlen||[]).filter(r=>r.generation==='g4_twoscore4');
   const PT=BUN.pairtrans||[],FR=BUN.finalrep||[],FP=BUN.finalpairs||[],
         CB=BUN.charblocks||[],RS=BUN.rankstab||[];
   const row=k=>FR.find(r=>r.item===k)||{};
   let h='<div class="note"><b>The current classifier &mdash; generation 4.</b> '
    +'Two independent scores, four shape states, a <b>106</b>-bar lookback, a 5-bar '
    +'confirmation dwell. Every number on this screen traces to a committed file; '
    +'the file is named under each table.</div>'
    +'<div class="note"><b>On the lookback constant, since two numbers are in '
    +'circulation.</b> The shipped value is <b>106</b> — <code>twoscores.py:55</code>, '
    +'<code>W = 106</code>, matched by <code>RIBBON = ((6,35),(19,106),(44,247))</code>. '
    +'<b>105 is not wrong, it is the same quantity on a different window.</b> The '
    +'settable parameter is the integer swing width <b>N=19</b>; the lookback is a '
    +'<i>measured</i> consequence of it — the pooled median distance back to the '
    +'previous confirmed swing — which is <b>106.0 bars measured in-sample</b> and '
    +'<b>105.0 measured on the full sample</b>. 105 was also the nominal figure the '
    +'sweep pointed at, so the decision was phrased in it. <code>TWO_SCORES.md</code> '
    +'still says 105 and now carries a correction note; the handoff and this app say '
    +'106 and are correct.</div>';

   // coverage + run length + diagonal
   if(RL.length){
    const blocks=['is','oos','all'];
    h+='<div class="tw"><table><thead><tr><th>State</th>'
     +blocks.map(b=>'<th colspan="4">'+b.toUpperCase()+'</th>').join('')
     +'</tr><tr><th></th>'+blocks.map(()=>'<th>share</th><th>median run</th>'
      +'<th>mean</th><th>longest</th>').join('')+'</tr></thead><tbody>'
     +['trending','ranging','trend-in-range','neither'].map(st=>{
       let r='<tr><td><b>'+st+'</b></td>';
       blocks.forEach(b=>{const x=RL.find(v=>v.state===st&&v.block===b&&v.pair==='ALL');
        r+=x?('<td>'+f(x.share)+'</td><td><b>'+f(x.median,0)+'</b></td><td>'
             +f(x.mean,1)+'</td><td>'+f(x.longest,0)+'</td>')
            :'<td>—</td><td>—</td><td>—</td><td>—</td>';});
       return r+'</tr>';}).join('')
     +'</tbody></table><div class="count">Coverage and run lengths &mdash; '
     +'<code>results/run_lengths.csv</code>, generation <code>g4_twoscore4</code>. '
     +'Recomputed by <code>code/persist.py</code>, not carried forward.</div></div>';
   }

   // transition matrix
   if(PT.length){
    const ST=['trending','ranging','trend-in-range','neither'];
    const agg={};
    PT.forEach(r=>{const k=r.frm+'|'+r.to;(agg[k]=agg[k]||[]).push(+r.share);});
    h+='<div class="tw"><table><thead><tr><th>From ↓ &nbsp; To →</th>'
     +ST.map(s=>'<th>'+s+'</th>').join('')+'</tr></thead><tbody>'
     +ST.map(a=>'<tr><td><b>'+a+'</b></td>'+ST.map(b=>{
       if(a===b)return '<td style="opacity:.35">—</td>';
       const v=agg[a+'|'+b];
       const m=v?v.reduce((x,y)=>x+y,0)/v.length:null;
       return '<td'+(m!=null&&m<0.15?' style="color:var(--chop)"':'')+'>'
        +f(m)+'</td>';}).join('')+'</tr>').join('')
     +'</tbody></table><div class="count">Mean transition share across the 28 '
     +'pairs, conditional on leaving that state &mdash; '
     +'<code>results/pair_transitions.csv</code>. <b>Direct trend&harr;range '
     +'moves are rare</b> (0.120 and 0.095): pairs pass through an intermediate '
     +'state almost every time.</div></div>';
   }

   // separation IS vs OOS + null
   if(FR.length){
    const tr=row('trend'),ch=row('chop'),gO=row('grid OOS'),gN=row('grid null');
    h+='<div class="tw"><table><thead><tr><th>Axis</th><th>IS separation</th>'
     +'<th>OOS separation</th><th>Surrogate</th><th>Corrected</th></tr></thead>'
     +'<tbody>'+[['trend',tr],['chop',ch]].map(([n,r])=>
      '<tr><td><b>'+n+'</b></td><td>'+f(r.is_sep)+'</td><td>'+f(r.oos_sep)
      +'</td><td>'+f(r.surrogate)+'</td><td><b>'+(r.corrected>0?'+':'')
      +f(r.corrected)+'</b></td></tr>').join('')
     +'<tr><td><b>full grid</b></td><td>'+f(gO.oos_sep)+' <span class="count">'
     +'(12 cells)</span></td><td>'+f(gN.oos_sep)+'</td><td>'+f(gN.surrogate)
     +'</td><td><b>'+(gN.corrected>0?'+':'')+f(gN.corrected)+'</b></td></tr>'
     +'</tbody></table><div class="count">One-versus-rest separation on four '
     +'properties the classifier is not built from &mdash; '
     +'<code>results/final_report.csv</code>. <b>Chop is the only axis that '
     +'holds up out of sample</b> (0.151&rarr;0.156); trend halves. Neither '
     +'clears its surrogate.</div></div>';
   }

   // the null, stated at its real draw count
   h+='<div class="note"><b>The null, at its actual size.</b> Every corrected '
    +'figure above is a <i>surrogate randomisation</i>: price is rebuilt with its '
    +'sign structure destroyed, the whole classifier is rebuilt on it, and the '
    +'statistic is recomputed. The draw counts are what was run, not a round '
    +'number &mdash; 15 draws for the final report '
    +'(<code>code/final.py</code>), 120 for the shape-window confirmation '
    +'(<code>results/shapescore_confirm.csv</code>), 200 for the lead-time '
    +'holdout reads (<code>results/masweep_confirm.csv</code>). '
    +'<b>There is no 200-shuffle null on the generation-4 classifier</b>; the '
    +'200-draw figures belong to the lead-time work, and quoting them here would '
    +'be wrong.</div>';

   // per-pair separation
   if(FP.length){
    const t=FP.filter(r=>r.axis==='trend').sort((a,b)=>b.sep-a.sep),
          c=FP.filter(r=>r.axis==='chop').sort((a,b)=>b.sep-a.sep);
    h+='<div class="tw"><table><thead><tr><th>#</th><th>Pair</th>'
     +'<th>Trend separation</th><th>Pair</th><th>Chop separation</th></tr>'
     +'</thead><tbody>'+t.map((x,i)=>'<tr><td>'+(i+1)+'</td><td>'+x.pair
      +'</td><td>'+f(x.sep)+'</td><td>'+(c[i]?c[i].pair:'')+'</td><td>'
      +(c[i]?f(c[i].sep):'')+'</td></tr>').join('')
     +'</tbody></table><div class="count">Per-pair separation, holdout, the two '
     +'axes never blended &mdash; <code>results/final_pairs.csv</code>. Trend '
     +'median 0.118, chop median 0.195.</div></div>';
   }

   // IS vs OOS character stability
   if(RS.length){
    h+='<div class="tw"><table><thead><tr><th>Per-pair statistic</th>'
     +'<th>1999&ndash;2015 vs 2016&ndash;2026 rank correlation</th></tr></thead>'
     +'<tbody>'+RS.map(r=>'<tr><td>'+r.statistic+'</td><td><b>'
      +(r.rank_corr>0?'+':'')+f(r.rank_corr)+'</b></td></tr>').join('')
     +'</tbody></table><div class="count">Does a pair keep its character between '
     +'halves? &mdash; <code>results/pair_rank_stability.csv</code>. It does not: '
     +'trendiness correlates <b>&minus;0.087</b> across the split, and 28 '
     +'sign-surrogate pairs spread wider (sd 0.0430) than the real ones '
     +'(0.0337).</div></div>';
   }
   $('#curstates').innerHTML=h;
  }

  // ================= EXTERNAL DRIVERS =================
  function buildExtDrivers(){
   const f=(v,n)=>v==null||v===''?'—':(+v).toFixed(n==null?3:n);
   const Q1=BUN.rdq1||[],Q2=BUN.rdq2||[],NL=BUN.rdnull||[],PR=BUN.rdpairs||[];
   if(!Q1.length){$('#extdrv').innerHTML='<div class="note">ratediff feeds not in the bundle.</div>';return;}
   const W=NL.length?NL[0].W:5;
   let h='<div class="note"><b>Rate differential momentum against regime shape.</b> '
    +'The <i>level</i> of the 2-year yield differential was tested before and gave '
    +'nothing. This tests the <b>change</b>. It is a <b>separate output</b> — it does '
    +'not feed the shape or activity scores, and it never has.</div>'
    +'<div class="note" style="border-left:3px solid var(--chop)"><b>Three data facts '
    +'that limit what this covers.</b> <code>rates2y.csv</code> starts 1998-06-01, not '
    +'1990. <b>NZD has no 2-year yield data at all</b>, so seven pairs are absent and '
    +'the test runs on <b>21 pairs, not 28</b>. CAD starts 2001 and CHF ends July 2025, '
    +'so those pairs lose part of each block. Per-pair coverage is in '
    +'<code>results/ratediff_momentum_coverage.csv</code>.</div>';

   h+='<div class="tw"><table><thead><tr><th>Window</th><th>Block</th><th>State</th>'
    +'<th>Episodes</th><th>Agreement</th><th>Base (all states)</th><th>Excess</th>'
    +'</tr></thead><tbody>'
    +Q1.filter(r=>r.state==='trending'||r.state==='ranging')
      .map(r=>'<tr><td>'+r.W+'</td><td>'+r.block+'</td><td>'+r.state+'</td><td>'
       +r.episodes+'</td><td>'+f(r.agree)+'</td><td>'+f(r.base_all_states)
       +'</td><td><b style="color:'+(r.excess>0?'var(--trend)':'var(--chop)')+'">'
       +(r.excess>0?'+':'')+f(r.excess)+'</b></td></tr>').join('')
    +'</tbody></table><div class="count"><b>Question 1 — present-tense association.</b> '
    +'Episode-based: one state run is one observation, so a 40-bar episode contributes '
    +'a single agree/disagree, not forty. — <code>results/ratediff_momentum_q1.csv</code>'
    +'</div></div>';

   h+='<div class="tw"><table><thead><tr><th>Block</th><th>Kind</th><th>n</th>'
    +'<th>Agreement</th><th>Excess over control</th></tr></thead><tbody>'
    +Q2.map(r=>'<tr><td>'+r.block+'</td><td>'+r.kind+'</td><td>'+r.n+'</td><td>'
     +f(r.agree)+'</td><td>'+(r.excess==null||r.excess===''?'—':
       ((r.excess>0?'+':'')+f(r.excess)))+'</td></tr>').join('')
    +'</tbody></table><div class="count"><b>Question 2 — lead into trending.</b> '
    +'Momentum read at the bar <i>before</i> the state changes; since momentum is '
    +'already lagged one bar that value uses yields through t&minus;2. The control '
    +'draws non-transition bars with the same forward horizon, three per transition. '
    +'— <code>results/ratediff_momentum_q2.csv</code></div></div>';

   h+='<div class="tw"><table><thead><tr><th>Block</th><th>Statistic</th>'
    +'<th>Real</th><th>Null mean</th><th>Null sd</th><th>Shifts</th>'
    +'<th>Rank of real</th><th>p</th></tr></thead><tbody>'
    +NL.map(r=>'<tr><td>'+r.block+'</td><td>'+r.statistic+'</td><td><b>'
     +(r.real>0?'+':'')+f(r.real,4)+'</b></td><td>'+(r.null_mean>0?'+':'')
     +f(r.null_mean,4)+'</td><td>'+f(r.null_sd,4)+'</td><td>'+r.n_shifts
     +'</td><td>'+r.rank_of_real+' of '+(r.n_shifts+1)+'</td><td>'+f(r.p)
     +'</td></tr>').join('')
    +'</tbody></table><div class="count"><b>Null — circular shift of the yield panel '
    +'against price</b>, offsets of at least 1,000 bars. Both series keep their own '
    +'behaviour; only the alignment between them breaks. <b>'+(NL.length?NL[0].n_shifts:0)
    +' shifts</b>, the exact count run. — <code>results/ratediff_momentum_null.csv</code>'
    +'</div></div>';

   const op=PR.filter(r=>r.block==='oos');
   if(op.length) h+='<div class="tw"><table><thead><tr><th>Pair</th>'
    +'<th>Trending episodes</th><th>Agreement</th><th>Base</th><th>Excess</th>'
    +'</tr></thead><tbody>'+op.slice().sort((a,b)=>b.excess-a.excess)
     .map(r=>'<tr><td>'+r.pair+'</td><td>'+r.episodes+'</td><td>'+f(r.agree)
      +'</td><td>'+f(r.base)+'</td><td>'+(r.excess>0?'+':'')+f(r.excess)
      +'</td></tr>').join('')+'</tbody></table><div class="count">Per pair, holdout, '
    +'at the IS-chosen window W='+W+'. — <code>results/ratediff_momentum_pairs.csv</code>'
    +'</div></div>';

   h+='<details class="panel" style="margin-top:14px" open>'
    +'<summary style="cursor:pointer;font-weight:600">Rate differential momentum '
    +'<span class="count">plain English</span></summary>'
    +'<div style="margin-top:10px;font-size:13px;line-height:1.65">'
    +'<p><b>What it is.</b> For each pair, the base currency&rsquo;s 2-year government '
    +'yield minus the quote currency&rsquo;s, and then how much that gap has '
    +'<i>changed</i> over the last W days. Not the gap itself &mdash; the gap was '
    +'tested before and gave nothing.</p>'
    +'<p><b>How it is calculated.</b> differential = base 2y &minus; quote 2y, '
    +'forward-filled at most 10 bars. momentum = differential &minus; its value W bars '
    +'ago, then lagged one bar. Three windows only &mdash; 5, 21 and 63 days, chosen '
    +'as a week, one median state run and a quarter. No sweep: the menu was fixed '
    +'before the test ran, the winner picked on 1999&ndash;2015 and the holdout read '
    +'once.</p>'
    +'<p><b>How to read it.</b> During each trending episode, does the sign of the '
    +'differential momentum match the direction price actually moved? Compare that '
    +'agreement rate with the same rate over episodes of <i>every</i> state. The '
    +'baseline is not 50% &mdash; price and yields both drift, so agreement runs above '
    +'a half by default. Only the <b>excess</b> column means anything.</p>'
    +'<p><b>What it is good for.</b> Ruling the idea in or out cheaply, and doing it '
    +'on episodes rather than bars so a long trend cannot count forty times.</p>'
    +'<p style="color:var(--chop)"><b>What it is NOT.</b> <b>This does not predict '
    +'price direction.</b> It is tested against <i>regime shape only</i> &mdash; '
    +'whether momentum agrees with the move that already happened during an episode, '
    +'and whether it was already leaning the right way before a state changed. Nothing '
    +'here is a directional forecast, nothing here is sized, and no money metric '
    +'appears anywhere in it. The second most likely misreading is treating the '
    +'ranging row as a finding: it is the one cell that clears its null on the '
    +'holdout, it was <i>not</i> the question asked, and a single surviving cell out '
    +'of four tested is roughly what chance delivers.</p></div></details>';
   $('#extdrv').innerHTML=h;
  }

  function buildDrivers2(){
   const f=(v,n)=>v==null||v===''?'—':(+v).toFixed(n==null?3:n);
   const PRE=(BUN.rdpre||[])[0],PC=BUN.precov||[],M1=BUN.mvq1||[],
         MC=BUN.mvchg||[],M2=BUN.mvq2||[],MN=BUN.mvnull||[],MV=(BUN.mvcov||[])[0];
   let h='';
   if(PRE){
    h+='<h3>Rate differential — pre-1999 confirmation</h3>'
     +'<div class="note"><b>One shot, zero tuning, on data nobody had touched.</b> '
     +'W=5 frozen, the same one-bar lag, the same episode scoring imported rather '
     +'than reimplemented, and the classifier cut points fitted on 1999&ndash;2015 '
     +'carried backwards unchanged.</div>'
     +'<div class="note" style="border-left:3px solid var(--chop)">'
     +'<b>It ran on 3 pairs, not the 21 the brief assumed.</b> Only USD, GBP and '
     +'CHF have 2-year yields before 1999 — CAD starts 2001, AUD&rsquo;s cache is '
     +'a 31-row fragment, JPY&rsquo;s will not parse, NZD does not exist. <b>And '
     +'those three are not independent</b>: three currencies give three pairs and '
     +'any one is the ratio of the other two, so the effective sample is nearer '
     +'two series than three. FX was rebuilt from the FRED mirror of H.10 (the Fed '
     +'endpoint returns 403) and checked against the committed panel over 6,916 '
     +'shared bars — median relative difference 0.00004 / 0.00000 / 0.00004.</div>'
     +'<div class="tw"><table><thead><tr><th>Sample</th><th>Pairs</th>'
     +'<th>Ranging episodes</th><th>Excess</th><th>Null mean</th><th>Rank</th>'
     +'<th>p</th><th>Verdict</th></tr></thead><tbody><tr><td>'+PRE.sample
     +'</td><td>'+PRE.pairs+'</td><td>'+PRE.ranging_episodes+'</td><td><b>'
     +(PRE.excess>0?'+':'')+f(PRE.excess,4)+'</b></td><td>'
     +(PRE.null_mean>0?'+':'')+f(PRE.null_mean,4)+'</td><td>'+PRE.rank_of_real
     +' of '+PRE.n_compared+'</td><td>'+f(PRE.p)+'</td><td><b style="color:'
     +(PRE.verdict==='CONFIRMED'?'var(--trend)':'var(--chop)')+'">'+PRE.verdict
     +'</b></td></tr></tbody></table>'
     +'<div class="count">Verdict rule fixed <i>before</i> the read: excess &gt; 0 '
     +'AND rank &le; 3, the bar the original cleared on its holdout. — '
     +'<code>results/ratediff_pre1999_result.csv</code></div></div>'
     +'<div class="note"><b>What actually happened, stated both ways.</b> The '
     +'point estimate did <i>not</i> flip: <b>+0.053</b> pre-1999 against '
     +'<b>+0.046</b> on the original holdout, the same sign and nearly the same '
     +'size. But the null spread is <b>0.075</b> here against <b>0.019</b> there, '
     +'because 39 ranging episodes is not 478. So this is a <b>failure to '
     +'confirm through lack of power</b>, not a refutation — and by the rule set '
     +'in advance, that closes the question either way. The ranging cell stays '
     +'unpromoted and is not revisited.</div>';
   }
   if(M1.length){
    const sp={};M1.forEach(r=>{sp[r.block+'|'+r.state+'|'+r.bucket]=r.mean_share;});
    const ST=['trending','ranging','trend-in-range','neither'];
    h+='<h3>External driver #2 — bond volatility (MOVE)</h3>'
     +'<div class="note"><b>MOVE is one global series hitting all 28 pairs at '
     +'once</b>, so pair-level episodes are not independent observations. '
     +'Everything here is <b>pooled by day</b>: the unit is a calendar day and the '
     +'statistic is the cross-sectional share of pairs in each state. '
     +(MV?('Overlap '+MV.first+' to '+MV.last+', '+MV.days+' days ('+MV.is_days
        +' in-sample, '+MV.oos_days+' holdout). The FX sample starts 1999-01-04, '
        +'so the first ~3.9 years have no MOVE at all.'):'')+'</div>'
     +'<div class="tw"><table><thead><tr><th>Block</th><th>State</th>'
     +'<th>Low MOVE</th><th>Mid</th><th>High MOVE</th><th>Spread (high&minus;low)</th>'
     +'</tr></thead><tbody>'
     +['is','oos'].map(b=>ST.map(s=>{
       const lo=sp[b+'|'+s+'|low'],mi=sp[b+'|'+s+'|mid'],hi=sp[b+'|'+s+'|high'];
       if(lo==null)return '';
       return '<tr><td>'+b+'</td><td>'+s+'</td><td>'+f(lo)+'</td><td>'+f(mi)
        +'</td><td>'+f(hi)+'</td><td><b>'+((hi-lo)>0?'+':'')+f(hi-lo)
        +'</b></td></tr>';}).join('')).join('')
     +'</tbody></table><div class="count"><b>Question 1</b> — state occupancy by '
     +'MOVE tercile, cut on in-sample only. MOVE is a level, not a direction, so '
     +'this is an occupancy question and not a sign test. — '
     +'<code>results/move_q1.csv</code></div></div>';
    if(MC.length) h+='<div class="tw"><table><thead><tr><th>Block</th>'
     +'<th>State</th><th>Days</th><th>Correlation with 21-bar MOVE change</th>'
     +'</tr></thead><tbody>'+MC.map(r=>'<tr><td>'+r.block+'</td><td>'+r.state
      +'</td><td>'+r.n_days+'</td><td>'+(r.corr_chg21>0?'+':'')+f(r.corr_chg21,4)
      +'</td></tr>').join('')+'</tbody></table><div class="count">The trending '
     +'correlation <b>flips sign</b> between blocks, +0.143 to &minus;0.039. — '
     +'<code>results/move_q1_chg.csv</code></div></div>';
    if(M2.length) h+='<div class="tw"><table><thead><tr><th>Block</th>'
     +'<th>Day type</th><th>Days</th><th>Mean MOVE level</th>'
     +'<th>Mean 21-bar change</th></tr></thead><tbody>'
     +M2.map(r=>'<tr><td>'+r.block+'</td><td>'+r.kind+'</td><td>'+r.days
      +'</td><td>'+f(r.mean_level,2)+'</td><td>'+(r.mean_chg21>0?'+':'')
      +f(r.mean_chg21,2)+'</td></tr>').join('')+'</tbody></table>'
     +'<div class="count"><b>Question 2</b> — MOVE on days containing a transition '
     +'into trending against days containing none, both reads lagged one bar. — '
     +'<code>results/move_q2.csv</code></div></div>';
    if(MN.length) h+='<div class="tw"><table><thead><tr><th>Block</th>'
     +'<th>Statistic</th><th>Real</th><th>Null mean</th><th>Null sd</th>'
     +'<th>Shifts</th><th>Rank</th><th>p</th></tr></thead><tbody>'
     +MN.map(r=>'<tr><td>'+r.block+'</td><td>'+r.statistic+'</td><td><b>'
      +(r.real>0?'+':'')+f(r.real,4)+'</b></td><td>'+(r.null_mean>0?'+':'')
      +f(r.null_mean,4)+'</td><td>'+f(r.null_sd,4)+'</td><td>'+r.n_shifts
      +'</td><td>'+r.rank_of_real+' of '+r.n_compared+'</td><td>'+f(r.p)
      +'</td></tr>').join('')+'</tbody></table><div class="count">Circular shift '
     +'of MOVE against the state panel, offsets &ge;500 days, two-sided on '
     +'|spread| because the headline state was chosen on in-sample magnitude. — '
     +'<code>results/move_null.csv</code></div></div>';
    h+='<details class="panel" style="margin-top:14px" open>'
     +'<summary style="cursor:pointer;font-weight:600">Bond volatility (MOVE) '
     +'<span class="count">plain English</span></summary>'
     +'<div style="margin-top:10px;font-size:13px;line-height:1.65">'
     +'<p><b>What it is.</b> The MOVE index — implied volatility of US Treasury '
     +'options, the bond market&rsquo;s equivalent of the VIX. One number a day '
     +'for the whole world.</p>'
     +'<p><b>How it is calculated here.</b> Two declared constructions and nothing '
     +'else: the level cut into terciles on 1999&ndash;2015 data and applied '
     +'unchanged, and its 21-bar change. Both lagged one bar. No sweep.</p>'
     +'<p><b>How to read it.</b> Because MOVE is global, a day is one observation '
     +'no matter how many of the 28 pairs move. The tables show the average share '
     +'of pairs sitting in each state on high-MOVE days against low-MOVE days.</p>'
     +'<p><b>What it is good for.</b> Ruling the idea in or out cheaply, with the '
     +'non-independence handled by construction rather than argued away.</p>'
     +'<p style="color:var(--chop)"><b>What it is NOT.</b> <b>It does not predict '
     +'price direction</b> — it is tested against <i>regime shape only</i>, and '
     +'MOVE has no direction to give. It is also <b>not confirmed</b>: the '
     +'in-sample trending spread of +0.071 shrinks to <b>+0.015</b> out of sample '
     +'and ranks 31st of 46 nulls, and the 21-bar-change correlation flips sign '
     +'between blocks. The one cell that survives its null is question 2 — MOVE '
     +'rising ahead of transition days — and the most likely misreading is '
     +'treating that as an early-warning signal. A day when FX regimes turn is a '
     +'day something happened globally, and bond volatility rising on such days is '
     +'close to a restatement of that, not an independent forecast.</p>'
     +'</div></details>';
   }
   $('#extdrv2').innerHTML=h;
  }

  function buildDriversReframed(){
   const f=(v,n)=>v==null||v===''?'—':(+v).toFixed(n==null?3:n);
   const SA=BUN.drvsepa||[],SB=BUN.drvsepb||[],CF=BUN.drvconf||[],SU=BUN.drvsub||[];
   if(!SA.length){$('#extdrv0').innerHTML='';return;}
   const sep=r=>r.group&&r.real==null, nul=r=>r.real!=null;
   let h='<div class="note" style="border-left:3px solid var(--trend)">'
    +'<b>Drivers CONFIRM the regime read. They do not predict price.</b> The '
    +'question here is the one the internal measurements were held to: does the '
    +'driver <i>read differently across states</i>? A driver that does is a second '
    +'opinion from outside price. The old direction-agreement results stay on file '
    +'and are superseded as the main question, not deleted. Nothing here folds into '
    +'the shape or activity scores.</div>'
    +'<div class="note">Crisis is a <b>forward-only</b> window, event date to +15 '
    +'bars — the convention crisis.py already uses, because a window opening '
    +'before the event once produced a false “fires 2.5 days ahead” result. The '
    +'calendar holds <b>54</b> events, and crisis days are 10.7% of bars.</div>';

   h+='<div class="tw"><table><thead><tr><th>Driver</th><th>Block</th>'
    +'<th>Group</th><th>Episodes / days</th><th>Mean reading</th>'
    +'<th>Separation vs rest</th></tr></thead><tbody>'
    +SA.filter(sep).map(r=>'<tr><td>A rate-gap |21d|</td><td>'+r.block+'</td><td>'
     +r.group+'</td><td>'+r.episodes+'</td><td>'+f(r.mean_drv,4)+'</td><td><b>'
     +(r.sep_vs_rest>0?'+':'')+f(r.sep_vs_rest)+'</b></td></tr>').join('')
    +SB.filter(r=>r.group&&r.real==null).map(r=>'<tr><td>B MOVE level</td><td>'
     +r.block+'</td><td>'+r.group+'</td><td>'+r.days+'</td><td>'
     +f(r.mean_level,2)+'</td><td><b>'+(r.sep_level>0?'+':'')+f(r.sep_level)
     +'</b></td></tr>').join('')
    +'</tbody></table><div class="count"><b>Test 1</b> — driver A is per-pair and '
    +'episode-based; driver B is <b>pooled by day</b>, because MOVE is one global '
    +'series and pooling by pair would let one world event count 28 times. — '
    +'<code>results/driver_separation_a.csv</code>, '
    +'<code>results/driver_separation_b.csv</code></div></div>';

   const nulls=SA.filter(nul).concat(SB.filter(nul));
   if(nulls.length) h+='<div class="tw"><table><thead><tr><th>Driver</th>'
    +'<th>Block</th><th>Group (chosen on IS)</th><th>Real</th><th>Null</th>'
    +'<th>Rank</th><th>p</th></tr></thead><tbody>'
    +nulls.map(r=>'<tr><td>'+r.driver+'</td><td>'+r.block+'</td><td>'+r.group
     +'</td><td><b>'+(r.real>0?'+':'')+f(r.real,4)+'</b></td><td>'
     +(r.null_mean>0?'+':'')+f(r.null_mean,4)+' ± '+f(r.null_sd,4)+'</td><td>'
     +r.rank_of_real+' of '+r.n_compared+'</td><td><b style="color:'
     +(r.p<0.05?'var(--trend)':'var(--mute)')+'">'+f(r.p)+'</b></td></tr>')
     .join('')+'</tbody></table><div class="count">Circular-shift null, 50 draws, '
    +'two-sided. <b>Both drivers clear on the holdout at p=0.020</b> — and both '
    +'FAIL in-sample (p=0.157 and p=0.235). A holdout stronger than its own '
    +'in-sample is unusual enough to check, which is the next table.</div></div>';

   if(SU.length){
    const per=['2016-19','2020-21','2022-26'];
    h+='<div class="tw"><table><thead><tr><th>Driver</th><th>Group</th>'
     +per.map(p=>'<th>'+p+'</th>').join('')+'</tr></thead><tbody>'
     +[['A','ranging'],['A','crisis'],['B','range-leaning'],['B','crisis']]
      .map(([d,g])=>'<tr><td>'+d+'</td><td>'+g+'</td>'+per.map(p=>{
        const r=SU.find(x=>x.driver===d&&x.group===g&&x.period===p);
        const v=r?r.sep:null;
        return '<td'+(v!=null&&v>0&&(g==='ranging'||g==='range-leaning')
          ?' style="color:var(--chop)"':'')+'>'
          +(v==null||isNaN(v)?'—':((v>0?'+':'')+f(v)))+'</td>';}).join('')
       +'</tr>').join('')+'</tbody></table>'
     +'<div class="count"><b>The two drivers part company here.</b> '
     +'<b>Driver A is not robust</b>: its ranging separation is <b>+0.160 in '
     +'2016–19 — the wrong sign</b> — and only turns negative from 2020. Its '
     +'holdout result is a post-COVID effect, not a property of the sample. '
     +'<b>Driver B is robust</b>: range-leaning reads −0.538 / −0.314 / −0.648 '
     +'and crisis +0.932 / — / +0.852, the same sign and similar size in every '
     +'sub-period. — <code>results/driver_subperiod.csv</code></div></div>';
   }

   if(CF.length) h+='<div class="tw"><table><thead><tr><th>Driver</th>'
    +'<th>Block</th><th>Subset</th><th>n</th><th>Median run</th>'
    +'<th>Daily flip rate</th></tr></thead><tbody>'
    +CF.map(r=>'<tr><td>'+r.driver+'</td><td>'+r.block+'</td><td>'+r.subset
     +'</td><td>'+r.episodes+'</td><td>'+(r.median_run==null||r.median_run===''
      ?'—':f(r.median_run,1))+'</td><td>'+(r.daily_flip_rate==null
      ||r.daily_flip_rate===''?'—':f(r.daily_flip_rate,4))+'</td></tr>').join('')
    +'</tbody></table><div class="count"><b>Test 2 — does agreement add '
    +'confidence?</b> Barely. Driver A: trending runs are 26.0 vs 20.0 bars '
    +'in-sample when the gap is moving hard, but <b>19.0 vs 18.0 out of '
    +'sample</b> — the gap collapses. Driver B: the daily flip rate is 0.0343 vs '
    +'0.0332 in-sample and <b>0.0343 vs 0.0372 out of sample</b> — the sign '
    +'flips. Neither is a usable confidence input. — '
    +'<code>results/driver_confidence_a.csv</code></div></div>';

   h+='<details class="panel" style="margin-top:14px" open>'
    +'<summary style="cursor:pointer;font-weight:600">Drivers as confirmation '
    +'<span class="count">plain English</span></summary>'
    +'<div style="margin-top:10px;font-size:13px;line-height:1.65">'
    +'<p><b>What it is.</b> Two readings from outside the price series — how hard '
    +'the 2-year rate gap is moving, and how volatile the bond market is — checked '
    +'against what the classifier already says the pair is doing.</p>'
    +'<p><b>How it is calculated.</b> Driver A is the <i>absolute</i> 21-bar '
    +'change in the rate differential: size, not direction. Driver B is the MOVE '
    +'level and its 21-bar change. Both lagged one bar. States come from the '
    +'committed classifier and are never modified.</p>'
    +'<p><b>How to read it.</b> Separation is the group mean minus every other '
    +'group, in standard deviations. Crisis days carry a MOVE reading about '
    +'<b>0.9 sd</b> above everything else, consistently. That is the driver '
    +'agreeing with the regime read.</p>'
    +'<p><b>What it is good for.</b> A second opinion. When MOVE is elevated and '
    +'the panel is not range-leaning, two independent things are saying the same '
    +'thing.</p>'
    +'<p style="color:var(--chop)"><b>What it is NOT.</b> <b>It does not predict '
    +'price direction</b> — driver A is deliberately stripped of sign, and MOVE '
    +'has no direction to give. It is <b>not a new state</b>: nothing here changes '
    +'a label. It is <b>not yet a confidence input</b> either — test 2 asked '
    +'whether agreement makes the state call better and the answer was no in both '
    +'blocks. And <b>driver A should not be used at all</b>: it clears its null '
    +'only because of 2020 onwards, and reads the wrong sign in 2016–19.</p>'
    +'</div></details>';
   h+='<div class="note" style="border-left:3px solid var(--mute)">'
    +'<b>MOVE status after driver 3&rsquo;s run: STILL PROVISIONAL, separation '
    +'only.</b> Its separation result is corroborated &mdash; same sign and size '
    +'in every sub-period, crisis days ~0.9&nbsp;sd high. Its <b>forward</b> odds '
    +'are not: ×0.83 in-sample against ×1.66 out, and the sub-period split cannot '
    +'corroborate the holdout figure (two windows have too few events, the third '
    +'reads ×1.18). And the confidence test failed on it, as on everything else. '
    +'MOVE is a second opinion on the <i>current</i> call and nothing more.</div>';
   $('#extdrv0').innerHTML=h;
  }

  function buildDriverC(){
   const f=(v,n)=>v==null||v===''?'—':(+v).toFixed(n==null?3:n);
   const SC=BUN.drvsepc||[],CF=BUN.drvconfc||[],FC=BUN.drvfwdc||[],
         FB=BUN.drvfwdb||[],SU=BUN.drvsubc||[],ME=BUN.drvmech||[],
         FS=BUN.drvfwdsub||[];
   if(!SC.length){$('#drvc').innerHTML='';return;}
   const sep=SC.filter(r=>r.group&&r.real==null), nul=SC.filter(r=>r.real!=null);
   let h='<h3>Driver 3 — equity correlation (S&amp;P 500)</h3>'
    +'<div class="note"><b>^GSPC via the Yahoo chart API, 1996-12-09 to '
    +'2026-08-14, 7,464 closes</b> (cached to <code>data/gspc.csv</code>). '
    +'Overlap with the FX sample is <b>6,872 bars, 1999-01-04 to 2026-07-30</b> — '
    +'the whole sample, unlike MOVE which misses the first 3.9 years. Driver is '
    +'the rolling |correlation| of each pair&rsquo;s returns with S&amp;P returns '
    +'at 21 and 63 bars. Unlike MOVE it is <b>pair-specific</b>.</div>'
    +'<div class="note"><b>Mechanism prediction, written down before the run:</b> '
    +'JPY and CHF crosses are funding currencies moving on global risk, so the '
    +'equity link should separate most on those and weakly on EURGBP/AUDNZD types. '
    +'Separation on the wrong pairs would be a red flag, not a pass.</div>';

   h+='<div class="tw"><table><thead><tr><th>W</th><th>Block</th><th>Group</th>'
    +'<th>Episodes</th><th>Mean |corr|</th><th>Separation vs rest</th></tr>'
    +'</thead><tbody>'+sep.map(r=>'<tr><td>'+r.W+'</td><td>'+r.block+'</td><td>'
     +r.group+'</td><td>'+r.episodes+'</td><td>'+f(r.mean_drv,4)+'</td><td><b>'
     +(r.sep_vs_rest>0?'+':'')+f(r.sep_vs_rest)+'</b></td></tr>').join('')
    +'</tbody></table><div class="count"><b>Test 1 — separation.</b> — '
    +'<code>results/driver_separation_c.csv</code></div></div>';

   if(nul.length) h+='<div class="tw"><table><thead><tr><th>Block</th>'
    +'<th>Chosen on IS</th><th>Real</th><th>Null</th><th>Rank</th><th>p</th>'
    +'</tr></thead><tbody>'+nul.map(r=>'<tr><td>'+r.block+'</td><td>W='+r.W+' '
     +r.group+'</td><td><b>'+(r.real>0?'+':'')+f(r.real,4)+'</b></td><td>'
     +f(r.null_mean,4)+' ± '+f(r.null_sd,4)+'</td><td>'+r.rank_of_real+' of '
     +r.n_compared+'</td><td><b style="color:'+(r.p<0.05?'var(--trend)':'var(--chop)')
     +'">'+f(r.p)+'</b></td></tr>').join('')+'</tbody></table>'
    +'<div class="count">In-sample clears at p=0.020; <b>the holdout flips sign '
    +'and fails at p=0.647</b>.</div></div>';

   if(SU.length){const per=['2016-19','2020-21','2022-26'];
    h+='<div class="tw"><table><thead><tr><th>Group</th>'
     +per.map(p=>'<th>'+p+'</th>').join('')+'</tr></thead><tbody>'
     +['trending','ranging','crisis'].map(g=>'<tr><td>'+g+'</td>'
      +per.map(p=>{const r=SU.find(x=>x.group===g&&x.period===p);
        return '<td>'+(r&&r.sep!=null?((r.sep>0?'+':'')+f(r.sep)):'—')+'</td>';})
       .join('')+'</tr>').join('')+'</tbody></table>'
     +'<div class="count"><b>Sub-period split, run before reporting.</b> Crisis '
     +'reads +0.112 / &minus;0.105 / &minus;0.139 — inconsistent in sign. This is '
     +'the check that killed driver 1. — '
     +'<code>results/driver_subperiod_c.csv</code></div></div>';}

   if(ME.length){
    const fu=ME.filter(r=>r.funding===true||r.funding==='True'),
          nf=ME.filter(r=>!(r.funding===true||r.funding==='True'));
    const am=a=>a.reduce((s,r)=>s+Math.abs(r.sep),0)/(a.length||1);
    const top=ME.slice().sort((a,b)=>Math.abs(b.sep)-Math.abs(a.sep)).slice(0,5);
    h+='<div class="note"><b>Mechanism check.</b> JPY/CHF crosses mean |sep| <b>'
     +f(am(fu))+'</b> (n='+fu.length+') against <b>'+f(am(nf))+'</b> for all '
     +'others (n='+nf.length+') — the prediction holds <i>on the mean</i>. But the '
     +'largest single separation is <b>'+top[0].pair+' '+(top[0].sep>0?'+':'')
     +f(top[0].sep,2)+'</b>, which is not a funding cross, and the top five are '
     +top.map(r=>r.pair+' '+(r.sep>0?'+':'')+f(r.sep,2)).join(', ')+'. A margin '
     +'of '+f(am(fu)-am(nf))+' sd with a non-funding pair at the top is weak '
     +'support, and the driver failed its holdout anyway. — '
     +'<code>results/driver_mechanism_c.csv</code></div>';}

   if(CF.length) h+='<div class="tw"><table><thead><tr><th>Block</th>'
    +'<th>State</th><th>Subset</th><th>Episodes</th><th>Median run</th></tr>'
    +'</thead><tbody>'+CF.map(r=>'<tr><td>'+r.block+'</td><td>'+r.state
     +'</td><td>'+r.subset+'</td><td>'+r.episodes+'</td><td>'+f(r.median_run,1)
     +'</td></tr>').join('')+'</tbody></table>'
    +'<div class="count"><b>Test 2 — confidence. RETIRED.</b> Run-length gaps '
    +'(driver high minus low) are +1.0, +1.0, +1.5 and +8.5 bars — three of four '
    +'under two bars on a ~23-bar median, which is noise. This test has now failed '
    +'on all three drivers: rate-gap momentum (26.0 vs 20.0 in-sample collapsing '
    +'to 19.0 vs 18.0), MOVE (flip-rate sign flipped between blocks) and equity '
    +'correlation. <b>Agreement between a driver and the state call does not make '
    +'the call more reliable, and three independent attempts is enough.</b> — '
    +'<code>results/driver_confidence_c.csv</code></div></div>';
   $('#drvc').innerHTML=h;
  }

  function buildForwardOdds(){
   const f=(v,n)=>v==null||v===''?'—':(+v).toFixed(n==null?3:n);
   const FC=BUN.drvfwdc||[],FB=BUN.drvfwdb||[],FS=BUN.drvfwdsub||[];
   if(!FC.length){$('#fwdodds').innerHTML='';return;}
   const cell=A=>A.filter(r=>r.bucket);
   const nl=A=>A.filter(r=>r.real!=null);
   let h='<h3>Forward odds — the only place prediction lives</h3>'
    +'<div class="note" style="border-left:3px solid var(--trend)">'
    +'<b>Layer 1 does not predict.</b> It is a view of the current regime and is '
    +'never modified for, fed by, or judged on prediction. <b>Only drivers carry '
    +'forward odds</b>, they are reported as their own block, and nothing here '
    +'changes a state label.</div>'
    +'<div class="tw"><table><thead><tr><th>Driver</th><th>Block</th>'
    +'<th>Metric</th><th>Base</th><th>Low</th><th>Mid</th><th>High</th></tr>'
    +'</thead><tbody>'
    +[['C',FC],['B',FB]].map(([nm,A])=>{
      const C2=cell(A);const mets=[...new Set(C2.map(r=>r.metric))];
      return mets.map(mt=>['is','oos'].map(bl=>{
        const d=C2.filter(r=>r.metric===mt&&r.block===bl);
        if(!d.length)return '';
        const g=b=>{const r=d.find(x=>x.bucket===b);
          return r?(f(r.p)+' <span class="count">×'+f(r.lift,2)+'</span>'):'—';};
        return '<tr><td>'+nm+'</td><td>'+bl+'</td><td>'+mt+'</td><td>'
         +f(d[0].base)+'</td><td>'+g('low')+'</td><td>'+g('mid')+'</td><td>'
         +g('high')+'</td></tr>';}).join('')).join('');}).join('')
    +'</tbody></table><div class="count">Probability of each regime over the next '
    +'20 bars, by tercile of today&rsquo;s driver reading. <b>One crisis is one '
    +'observation</b> — the crisis row is computed at day level against distinct '
    +'event dates, not per bar or per pair. — <code>results/driver_forward_c.csv</code>, '
    +'<code>results/driver_forward_b.csv</code></div></div>';
   const N=nl(FC).concat(nl(FB));
   if(N.length) h+='<div class="tw"><table><thead><tr><th>Driver</th>'
    +'<th>Block</th><th>High-bucket lift</th><th>Null</th><th>Rank</th><th>p</th>'
    +'</tr></thead><tbody>'+N.map(r=>'<tr><td>'+r.driver+'</td><td>'+r.block
     +'</td><td><b>'+f(r.real)+'</b></td><td>'+f(r.null_mean)+' ± '+f(r.null_sd)
     +'</td><td>'+r.rank_of_real+' of '+r.n_compared+'</td><td><b style="color:'
     +(r.p<0.05?'var(--trend)':'var(--chop)')+'">'+f(r.p)+'</b></td></tr>')
     .join('')+'</tbody></table>'
    +(FS.length?('<div class="count">Sub-period lift: '
      +FS.map(r=>r.driver.split(' ')[0]+' '+r.period+' '
        +(r.lift==null||isNaN(r.lift)?'n/a':f(r.lift,2))).join(' · ')+'</div>'):'')
    +'<div class="count"><b>Neither driver has usable forward odds.</b> Equity '
    +'correlation flips from ×1.21 in-sample to ×0.61 out, and fails its null in '
    +'both blocks. MOVE flips the other way — ×0.83 in-sample to <b>×1.66</b> out, '
    +'which does clear its null (p=0.043) — but its in-sample block sits <i>below</i> '
    +'base rate and the sub-period split cannot corroborate it: two of three '
    +'windows have too few events to compute, and the one that does reads ×1.18, '
    +'not ×1.66. By the standard now in force that is not a pass.</div></div>';
   h+='<details class="panel" style="margin-top:14px" open>'
    +'<summary style="cursor:pointer;font-weight:600">Forward odds '
    +'<span class="count">plain English</span></summary>'
    +'<div style="margin-top:10px;font-size:13px;line-height:1.65">'
    +'<p><b>What it is.</b> Given what a driver reads today, how likely is each '
    +'regime at some point in the next 20 bars — and is that different from the '
    +'unconditional rate?</p>'
    +'<p><b>How it is calculated.</b> Days are split into terciles of the '
    +'driver&rsquo;s reading, cut on in-sample data only. For crisis, the question '
    +'is whether one of the 54 dated events falls in the next 20 bars, counted '
    +'once per event at day level. For trending and ranging it is per pair: does '
    +'the pair enter that state at any point in the window.</p>'
    +'<p><b>How to read it.</b> The lift column is bucket over base. ×1.00 is no '
    +'information. The cell that would matter is the high bucket on '
    +'P(crisis in 20 bars): the price-based detector has <b>zero days of '
    +'warning</b>, so a driver that raised those odds would be genuinely new.</p>'
    +'<p style="color:var(--chop)"><b>What it is NOT.</b> <b>Layer 1 does not '
    +'predict — only drivers carry forward odds</b>, and none of them currently '
    +'carries any that survive. This is not a directional forecast: it says '
    +'nothing about which way price moves, only which regime may appear. And a '
    +'lift above 1.00 in one block is not a finding — both drivers here flip sign '
    +'between in-sample and holdout, which is exactly what a spurious result looks '
    +'like.</p></div></details>';
   $('#fwdodds').innerHTML=h;
  }

  function buildDriverF(){
   const f=(v,n)=>v==null||v===''?'—':(+v).toFixed(n==null?3:n);
   const S=BUN.cotsep||[],U=BUN.cotsub||[],F=BUN.cotfwd||[],CV=BUN.cotcov||[];
   if(!S.length){$('#drvf').innerHTML='';return;}
   const per=['2016-19','2020-21','2022-26'];
   const names=[...new Set(S.map(r=>r.driver))];
   let h='<h3>Driver 6 &mdash; CFTC positioning (Commitments of Traders)</h3>'
    +'<div class="note" style="border-left:3px solid var(--chop)">'
    +'<b>The release lag is the thing that fakes results here.</b> A COT report '
    +'gives <b>Tuesday</b> positions and is published <b>Friday afternoon</b>, so '
    +'a Tuesday reading is not usable until the <b>following Monday</b>: report '
    +'date + 6 calendar days, then the standard one-bar shift on top. '
    +'<b>Seven calendar days from snapshot to first usable bar.</b> Using the '
    +'report date instead would grant a five-day head start on a weekly series. '
    +'A reading is dropped once older than 12 days, so NZD does not get its final '
    +'2022 report carried forward to today.</div>';

   if(CV.length){
    const cv=CV.filter(r=>r.reports>0);
    h+='<div class="tw"><table><thead><tr><th>Currency</th><th>Reports</th>'
     +'<th>First</th><th>Last</th><th>Daily coverage</th></tr></thead><tbody>'
     +cv.map(r=>'<tr><td>'+r.currency+'</td><td>'+r.reports+'</td><td>'+r.first
      +'</td><td>'+r.last+'</td><td>'+f(r.daily_coverage,3)+'</td></tr>').join('')
     +'</tbody></table><div class="count"><b>Coverage is the binding limit, not '
     +'frequency.</b> CME FX futures are quoted against USD, so this reaches '
     +'<b>7 of 28 pairs and no cross at all</b>. <b>NZD stops being reported '
     +'after 2022-02-01</b> — NZDUSD covers 65% of bars and none of the last four '
     +'years. — <code>results/cot_coverage.csv</code></div></div>';}

   h+='<div class="note"><b>Signed or absolute — declared before running, because '
    +'it decides the answer.</b> State labels carry no direction: “trending” '
    +'covers trending up and trending down. A <i>signed</i> position averaged over '
    +'trending episodes therefore cancels toward zero <i>by construction</i>, and '
    +'a null result would say nothing about positioning. So separation is decided '
    +'on the <b>absolute</b> readings — |net| is crowding, |4-week change| is '
    +'turnover — and the signed ones are reported beside them so the choice can be '
    +'checked rather than trusted.</div>';

   const sep=S.filter(r=>r.group&&r.real==null),nul=S.filter(r=>r.real!=null);
   h+='<div class="tw"><table><thead><tr><th>Reading</th><th>Block</th>'
    +'<th>Group</th><th>Episodes</th><th>Mean</th><th>Separation vs rest</th>'
    +'</tr></thead><tbody>'
    +sep.map(r=>'<tr><td>'+r.driver+(r.primary===true||r.primary==='True'
      ?' <b>(primary)</b>':'')+'</td><td>'+r.block+'</td><td>'+r.group+'</td><td>'
      +r.episodes+'</td><td>'+f(r.mean_drv,4)+'</td><td><b>'
      +(r.sep_vs_rest>0?'+':'')+f(r.sep_vs_rest)+'</b></td></tr>').join('')
    +'</tbody></table><div class="count"><b>Test 1 — separation.</b> This is the '
    +'test that decides keep or kill. Episode-based: one state run is one '
    +'observation. — <code>results/cot_separation.csv</code></div></div>';

   if(U.length){
    h+='<div class="tw"><table><thead><tr><th>Reading</th><th>Group</th>'
     +per.map(p=>'<th>'+p+'</th>').join('')+'</tr></thead><tbody>'
     +names.map(n=>['trending','ranging','crisis'].map(g=>'<tr><td>'+n+'</td><td>'
       +g+'</td>'+per.map(p=>{
         const r=U.find(x=>x.driver===n&&x.group===g&&x.period===p);
         const v=r?r.sep:null;
         return '<td'+(v!=null&&v<0?' style="color:var(--chop)"':'')+'>'
          +(v==null?'—':((v>0?'+':'')+f(v)))+'</td>';}).join('')+'</tr>').join(''))
      .join('')
     +'</tbody></table><div class="count"><b>Sub-period split, run before any '
     +'holdout pass was reported.</b> A sign change across these columns is what '
     +'kills a driver — and it has now killed four. — '
     +'<code>results/cot_subperiod.csv</code></div></div>';}

   if(nul.length){
    h+='<div class="tw"><table><thead><tr><th>Reading</th><th>Block</th>'
     +'<th>Chosen on IS</th><th>Real</th><th>Null</th><th>Rank</th><th>p</th>'
     +'</tr></thead><tbody>'+nul.map(r=>'<tr><td>'+r.driver+'</td><td>'+r.block
      +'</td><td>'+r.group+'</td><td><b>'+(r.real>0?'+':'')+f(r.real,4)
      +'</b></td><td>'+f(r.null_mean,4)+' ± '+f(r.null_sd,4)+'</td><td>'
      +r.rank_of_real+' of '+r.n_compared+'</td><td>'+f(r.p)+'</td></tr>').join('')
     +'</tbody></table><div class="count">Circular-shift null of the positioning '
     +'panel, exact draw count in <code>n_shifts</code>.</div></div>';}

   const fw=F.filter(r=>r.bucket&&r.metric!=='NULL of the declared cell'),
         fn=F.filter(r=>r.metric==='NULL of the declared cell');
   if(fw.length){
    const mets=[...new Set(fw.map(r=>r.metric))];
    h+='<div class="tw"><table><thead><tr><th>Block</th><th>Metric</th>'
     +'<th>Base</th><th>Low</th><th>Mid</th><th>High</th><th>Top decile</th>'
     +'</tr></thead><tbody>'
     +mets.map(mt=>['is','oos'].map(bl=>{
       const d=fw.filter(r=>r.metric===mt&&r.block===bl);
       if(!d.length)return '';
       const g=b=>{const r=d.find(x=>x.bucket===b);
         return r?(f(r.p)+' <span class="count">×'+f(r.lift,2)+'</span>'):'—';};
       return '<tr><td>'+bl+'</td><td>'+mt+'</td><td>'+f(d[0].base)+'</td><td>'
        +g('low')+'</td><td>'+g('mid')+'</td><td>'+g('high')+'</td><td>'
        +g('top decile (declared cell)')+'</td></tr>';}).join('')).join('')
     +'</tbody></table><div class="count"><b>Test 2 — forward odds. Reported, and '
     +'cannot kill a driver.</b> Panel: one pair-bar with a reading is one '
     +'observation, over the 7 USD pairs. Terciles cut in-sample and applied '
     +'unchanged. The acute-crisis window is <b>global</b>, so the 7 pairs share '
     +'it and those rows are not 7 independent samples. — '
     +'<code>results/cot_forward.csv</code></div></div>';}

   if(fn.length){
    h+='<div class="tw"><table><thead><tr><th>Block</th><th>Real lift</th>'
     +'<th>Null</th><th>Rank</th><th>p</th></tr></thead><tbody>'
     +fn.map(r=>'<tr><td>'+r.block+'</td><td><b>×'+f(r.real_lift,2)+'</b></td>'
      +'<td>×'+f(r.null_mean_lift,2)+' ± '+f(r.null_sd,2)+'</td><td>'
      +r.rank_of_real+' of '+r.n_compared+'</td><td>'+f(r.p_null)+'</td></tr>')
      .join('')
     +'</tbody></table><div class="count"><b>The declared special cell, stated '
     +'before running: the crowded-trade hypothesis.</b> Top decile of |net| '
     +'against P(acute crisis within 20 bars). It <i>held direction</i> across '
     +'both halves — ×1.32 in-sample, ×1.21 on the holdout — which is why it was '
     +'null-tested rather than reported bare. <b>It fails in both.</b> '
     +'Commodities looked exactly like this (×1.17 in both halves) before failing '
     +'its null the same way.</div></div>';}

   h+='<div class="note" style="border-left:3px solid var(--chop)">'
    +'<b>Verdict: DEAD. All four readings flip sign.</b> The sharpest one is also '
    +'the most instructive failure in the whole programme: |4-week change| '
    +'separates ranging at <b>+0.246 in-sample (p=0.020)</b> and <b>reverses to '
    +'−0.193 on the holdout (p=0.078)</b>. It beats its null in both halves '
    +'<i>with opposite signs</i> — a real magnitude attached to a sign that cannot '
    +'be relied on, which is worse than noise, because noise does not look '
    +'significant twice.</div>'
    +'<div class="note"><b>Why this one mattered.</b> Drivers 1–5 were all prices '
    +'of other assets. The standing objection was that if predictive value existed '
    +'anywhere free, it would live in <i>positioning</i> rather than realised '
    +'prices. Positioning has now been tested directly and it died on the same '
    +'fault as the rest. <b>The free external universe is fully worked '
    +'through</b>: one confirmation signal (MOVE), no forecast. Everything left — '
    +'options risk reversals, dealer flow, order-book depth — is paid.</div>';
   $('#drvf').innerHTML=h;
  }

  function buildDriverDE(){
   const f=(v,n)=>v==null||v===''?'—':(+v).toFixed(n==null?3:n);
   const SD=BUN.drvsepd||[],SE=BUN.drvsepe||[],FD=BUN.drvfwdd||[],
         FE=BUN.drvfwde||[],UD=BUN.drvsubd||[],UE=BUN.drvsube||[],
         RC=BUN.r10cov||[],PG=BUN.drvprog||[];
   if(!SD.length){$('#drvde').innerHTML='';return;}
   const per=['2016-19','2020-21','2022-26'];
   const blk=(title,note,S,U,fwd,fwdnote)=>{
    const sep=S.filter(r=>r.group&&r.real==null),nul=S.filter(r=>r.real!=null);
    let x='<h3>'+title+'</h3><div class="note">'+note+'</div>'
     +'<div class="tw"><table><thead><tr><th>Block</th><th>Group</th>'
     +'<th>Episodes</th><th>Mean</th><th>Separation vs rest</th></tr></thead>'
     +'<tbody>'+sep.map(r=>'<tr><td>'+r.block+'</td><td>'+r.group+'</td><td>'
      +r.episodes+'</td><td>'+f(r.mean_drv,4)+'</td><td><b>'
      +(r.sep_vs_rest>0?'+':'')+f(r.sep_vs_rest)+'</b></td></tr>').join('')
     +'</tbody></table><div class="count">Test 1 — separation. This is the test '
     +'that decides keep or kill.</div></div>';
    if(U.length) x+='<div class="tw"><table><thead><tr><th>Group</th>'
     +per.map(p=>'<th>'+p+'</th>').join('')+'</tr></thead><tbody>'
     +['trending','ranging','crisis'].map(g=>'<tr><td>'+g+'</td>'
      +per.map(p=>{const r=U.find(x2=>x2.group===g&&x2.period===p);
        const v=r?r.sep:null;
        return '<td'+(v!=null&&v<0?' style="color:var(--chop)"':'')+'>'
         +(v==null?'—':((v>0?'+':'')+f(v)))+'</td>';}).join('')+'</tr>')
      .join('')+'</tbody></table><div class="count"><b>Sub-period split, run '
     +'before reporting.</b> A sign change across these columns is what kills a '
     +'driver.</div></div>';
    if(nul.length) x+='<div class="tw"><table><thead><tr><th>Block</th>'
     +'<th>Chosen on IS</th><th>Real</th><th>Null</th><th>Rank</th><th>p</th>'
     +'</tr></thead><tbody>'+nul.map(r=>'<tr><td>'+r.block+'</td><td>'+r.group
      +'</td><td><b>'+(r.real>0?'+':'')+f(r.real,4)+'</b></td><td>'
      +f(r.null_mean,4)+' ± '+f(r.null_sd,4)+'</td><td>'+r.rank_of_real+' of '
      +r.n_compared+'</td><td>'+f(r.p)+'</td></tr>').join('')
     +'</tbody></table></div>';
    const fw=fwd.filter(r=>r.bucket);
    if(fw.length){const mets=[...new Set(fw.map(r=>r.metric))];
     x+='<div class="tw"><table><thead><tr><th>Block</th><th>Metric</th>'
      +'<th>Base</th><th>Low</th><th>Mid</th><th>High</th></tr></thead><tbody>'
      +mets.map(mt=>['is','oos'].map(bl=>{
        const d=fw.filter(r=>r.metric===mt&&r.block===bl);
        if(!d.length)return '';
        const g=b=>{const r=d.find(x2=>x2.bucket===b);
          return r?(f(r.p)+' <span class="count">×'+f(r.lift,2)+'</span>'):'—';};
        return '<tr><td>'+bl+'</td><td>'+mt+'</td><td>'+f(d[0].base)+'</td><td>'
         +g('low')+'</td><td>'+g('mid')+'</td><td>'+g('high')+'</td></tr>';})
       .join('')).join('')+'</tbody></table><div class="count">Test 2 — forward '
      +'odds. <b>Reported, and cannot kill a driver.</b> '+fwdnote+'</div></div>';}
    return x;};

   let h=blk('Driver 4 — yield curve shape (10y &minus; 2y)',
    '<b>Only USD is daily on FRED</b> — every other G8 long-rate series there is '
    +'monthly, so the 10-year comes from the same central-bank sources as the '
    +'2-year: Bundesbank, BoE GLC, SNB and MoF. <b>AUD and CAD have a 2-year but '
    +'no daily 10-year; NZD has neither</b>, so the driver runs on <b>10 of 28 '
    +'pairs</b>. — <code>results/rates10y_coverage.csv</code>',
    SD,UD,FD,
    'The holdout "high" bucket is empty: the mean |slope gap| roughly halves '
    +'between blocks, 0.728 to 0.369, so in-sample terciles do not partition the '
    +'holdout at all. That is itself the finding — the level moved regime.');

   h+=blk('Driver 5 — commodities (oil, gold)',
    'Free on the Yahoo chart API: <b>WTI CL=F from 2000-08-23</b> and <b>gold '
    +'GC=F from 2000-08-30</b> — both start ~1.6 years into the in-sample '
    +'window. Scope is mechanism-led: <b>oil → CAD and JPY pairs</b> (Japan '
    +'imports its energy), <b>gold → AUD pairs</b>, and <b>no test at all for '
    +'EUR/GBP/CHF-only pairs</b> — no mechanism exists there, so a hit would be '
    +'noise by construction. Iron ore TIO=F is free but only from 2010 and '
    +'duplicates gold\'s scope; <b>coal and dairy are not free, so NZD '
    +'commodities are recorded UNTESTABLE</b>.',
    SE,UE,FE,
    'The crisis lift is <b>×1.17 in both halves</b> — the most consistent '
    +'forward number in the whole programme — but it fails its null in both '
    +'(p=0.255 and p=0.235).');
   $('#drvde').innerHTML=h;

   if(PG.length){
    let p='<h3>The driver programme, closed — the free universe is fully tested</h3>'
     +'<div class="note" style="border-left:3px solid var(--trend)">'
     +'<b>Confirmation is the bar.</b> A driver that reliably reads the current '
     +'regime is a keeper even if it predicts nothing — failing the forward test '
     +'never kills a driver. Drivers die only when their read on the <i>present</i> '
     +'is unreliable: a sign flip between data halves or sub-periods.</div>'
     +'<div class="tw"><table><thead><tr><th>Driver</th><th>Status</th>'
     +'<th>Good for</th><th>Decided by</th><th>Evidence</th></tr></thead><tbody>'
     +PG.map(r=>'<tr><td><b>'+r.driver+'</b></td><td><b style="color:'
      +(r.status==='KEEPER'?'var(--trend)':(r.status==='UNTESTABLE'?'var(--mute)'
       :'var(--chop)'))+'">'+r.status+'</b></td><td>'+r.good_for+'</td><td>'
      +r.decided_by+'</td><td>'+r.evidence+'</td></tr>').join('')
     +'</tbody></table><div class="count">— '
     +'<code>results/driver_program_summary.csv</code></div></div>'
     +'<div class="note"><b>One keeper out of six.</b> Bond volatility confirms '
     +'a crisis reading that price structure has already made — crisis days carry '
     +'a MOVE level ~0.9&nbsp;sd above everything else, in every sub-period. It is '
     +'a second opinion on the present, worth having precisely because it comes '
     +'from outside the price series the classifier is built on.</div>'
     +'<div class="note"><b>What free external data cannot do, established rather '
     +'than assumed.</b> It cannot make the state call more reliable — the '
     +'confidence test ran on three drivers and failed on all three, and is '
     +'retired. And it cannot see forward: every forward reading that looked like '
     +'something either flipped sign between halves (equity ×1.21→×0.61, MOVE '
     +'×0.83→×1.66) or failed its null (commodities ×1.17 both halves, p=0.255 / '
     +'0.235; COT crowded-trade ×1.32→×1.21, p=0.196 / 0.412).</div>'
     +'<div class="note"><b>Why the failures look alike.</b> Four of five died the '
     +'same death — real in one block or sub-period, gone or reversed in another. '
     +'That is what a driver looks like when it tracks a regime of the world '
     +'rather than a property of the market; <b>2020–21 dominates almost every one '
     +'of these tables</b>. The sub-period split is what exposed it and it is now '
     +'standard.</div>'
     +'<div class="note" style="border-left:3px solid var(--mute)">'
     +'<b>Where predictive value would have to come from.</b> Not from the prices '
     +'of other assets, which is what all five of these are — from <b>positioning '
     +'and expectations</b>. <b>CFTC Commitments of Traders is free, weekly, and '
     +'not yet tested</b>: the one obvious gap left in the free universe, though '
     +'weekly frequency is a real limit against a daily classifier and it is '
     +'US-exchange only. Beyond that: FX options risk reversals, dealer flow and '
     +'order-book depth — all paid. <b>Layer 1 remains what it always was: a view '
     +'of the current regime, never judged on prediction.</b></div>';
    $('#drvprog').innerHTML=p;}
  }

  function buildChronic(){
   const f=(v,n)=>v==null||v===''?'—':(+v).toFixed(n==null?3:n);
   const EP=BUN.chronep||[],SP=BUN.chronsep||[],DT=BUN.chrondet||[];
   if(!EP.length){$('#chronic').innerHTML='';return;}
   const g=(d,gr)=>{const r=SP.find(x=>x.detector===d&&x.group===gr);return r?r.sep:null;};
   const indep=[...new Set(EP.map(r=>r.macro_event))].length;
   let h='<h3>Chronic crisis — sustained one-way debasement</h3>'
    +'<div class="note"><b>Acute is a spike; chronic is a bleed.</b> The canonical '
    +'JPY case reads 2.9&nbsp;sigma on the spike measure — nothing. Chronic is years '
    +'of one-way movement with no violence, which the acute detector cannot see by '
    +'construction.</div>'
    +'<div class="note"><b>The episode list is dated from the NEWS record, never '
    +'from the chart</b> — the same principle that made the 54-event acute calendar '
    +'non-circular. Dating a "sustained depreciation" from where the chart started '
    +'falling would make the detector\'s validation worthless, because the detector '
    +'reads the chart. <b>'+EP.length+' rows, '+indep+' independent macro '
    +'events.</b></div>'
    +'<div class="tw"><table><thead><tr><th>Currency</th><th>Dir</th>'
    +'<th>Start</th><th>End</th><th>Macro event</th><th>What was announced</th>'
    +'</tr></thead><tbody>'+EP.map(r=>'<tr><td><b>'+r.currency+'</b></td><td>'
     +(r.direction>0?'+':'')+r.direction+'</td><td>'+String(r.start).slice(0,10)
     +'</td><td>'+String(r.end).slice(0,10)+'</td><td>'+r.macro_event+'</td><td>'
     +r.what_happened+'</td></tr>').join('')+'</tbody></table>'
    +'<div class="count">EUR-down and USD-up 2014–15 are the <b>same divergence '
    +'seen from two sides</b> — any count of independent episodes must use the '
    +'macro_event column, not the row count. — '
    +'<code>results/chronic_episodes.csv</code></div></div>';

   h+='<div class="tw"><table><thead><tr><th>Detector</th><th>chronic</th>'
    +'<th>trending<br>(not chronic)</th><th>acute</th><th>other</th>'
    +'<th>BOUNDARY<br>chronic vs trending</th></tr></thead><tbody>'
    +['drift','onesided','starve'].map(d=>'<tr><td><b>'+d+'</b></td><td>'
     +f(g(d,'chronic'))+'</td><td>'+f(g(d,'trending (not chronic)'))+'</td><td>'
     +f(g(d,'acute'))+'</td><td>'+f(g(d,'other'))+'</td><td><b>'
     +f(g(d,'BOUNDARY chronic vs trending'))+'</b></td></tr>').join('')
    +'</tbody></table><div class="count"><b>The hard boundary is ordinary '
    +'trending, not calm.</b> Chronic <i>is</i> a trend, so separating it from a '
    +'quiet market says nothing — and 61% of the "everything else" comparison is '
    +'quiet market. Selecting on the diluted metric would have picked '
    +'<code>drift</code>; selecting on the boundary picks <code>onesided</code>. — '
    +'<code>results/chronic_separation.csv</code></div></div>';

   h+='<div class="note" style="border-left:3px solid var(--chop)">'
    +'<b>It does not clear its null.</b> The boundary separation is '
    +'<b>+0.237&nbsp;sd</b> against a shifted-window null of &minus;0.170&nbsp;± '
    +'0.288 — <b>rank 20 of 51, p=0.392</b>. Against everything, +0.492, rank 8 of '
    +'51, p=0.157. <b>Chronic episodes are not distinguishable from ordinary '
    +'trending by any of the three declared constructions.</b></div>'
    +'<div class="note"><b>And a reading of ~1.00 means "random walk".</b> The '
    +'drift measure is a 250-bar move over its own volatility, so a random walk '
    +'sits at 1.00 by construction. Chronic episodes read <b>1.037</b>. Ordinary '
    +'trending reads 0.912, acute 0.714, everything else 0.667. So the apparent '
    +'separation is not "chronic is unusually persistent" — it is <b>"everything '
    +'else is unusually mean-reverting, and chronic is merely random-walk-like"</b>. '
    +'That is a much weaker claim than the one the construction was built to '
    +'test.</div>'
    +'<div class="note"><b>Pullback starvation is simply false.</b> The premise was '
    +'that chronic bleeds never retrace properly. Measured, <code>starve</code> '
    +'separates chronic from trending by <b>+0.012&nbsp;sd</b> — nothing. Chronic '
    +'episodes retrace like ordinary trends do.</div>';

   const ac=g('acute maxabsmove','chronic'),ca=g('onesided','acute');
   h+='<div class="tw"><table><thead><tr><th>Detector</th>'
    +'<th>on CHRONIC episodes</th><th>on ACUTE episodes</th></tr></thead><tbody>'
    +'<tr><td>chronic (onesided)</td><td><b>'+f(g('onesided','chronic'))
    +'</b></td><td>'+f(ca)+'</td></tr>'
    +'<tr><td>acute (maxabsmove)</td><td>'+f(ac)+'</td><td><b>'
    +f(g('acute maxabsmove','acute'))+'</b></td></tr></tbody></table>'
    +'<div class="count"><b>The cross-check is the one clean pass here.</b> Each '
    +'alarm reads ~0 on the other\'s episodes (+0.095 and +0.032) while reading '
    +'~+0.48 on its own. They are genuinely two different alarms and neither is a '
    +'relabelling of the other.</div></div>';

   const ev=[...new Set(DT.filter(r=>r.detector==='onesided').map(r=>r.macro_event))];
   if(ev.length) h+='<div class="tw"><table><thead><tr><th>Macro event</th>'
    +'<th>Pairs</th><th>chronic detector</th><th>acute detector</th></tr></thead>'
    +'<tbody>'+ev.map(e=>{const c=DT.filter(r=>r.detector==='onesided'&&r.macro_event===e),
      a=DT.filter(r=>r.detector==='acute maxabsmove'&&r.macro_event===e);
      const m=x=>x.length?x.reduce((s,r)=>s+r.mean,0)/x.length:null;
      return '<tr><td>'+e+'</td><td>'+c.length+'</td><td>'+f(m(c))+'</td><td>'
       +f(m(a))+'</td></tr>';}).join('')+'</tbody></table>'
    +'<div class="count">Per episode. The readings are <b>near-identical across '
    +'all five macro events</b> (0.297–0.312) and the ordinary-trending mean is '
    +'0.296 — which is the same finding stated a third way. — '
    +'<code>results/chronic_detector.csv</code></div></div>';

   h+='<details class="panel" style="margin-top:14px" open>'
    +'<summary style="cursor:pointer;font-weight:600">Chronic crisis '
    +'<span class="count">plain English</span></summary>'
    +'<div style="margin-top:10px;font-size:13px;line-height:1.65">'
    +'<p><b>What it is.</b> A currency ground one way for quarters or years by '
    +'policy — not a crash. The anchor case is <b>the yen from April 2022 to July '
    +'2024</b>: the Bank of Japan kept yield curve control while the Fed and ECB '
    +'hiked, and the yen bled for two years without a single day that looked like '
    +'a crisis.</p>'
    +'<p><b>How it differs from acute.</b> Acute is one violent day across many '
    +'pairs — a spike the currency-leg divergence measure catches. Chronic has no '
    +'spike at all; the JPY case reads 2.9&nbsp;sigma on the spike measure, which '
    +'is a normal week. They are meant to be two separate alarms, and the '
    +'cross-check above confirms they are: each reads ~0 on the other\'s '
    +'episodes.</p>'
    +'<p><b>How to read the table.</b> Separation is in standard deviations, '
    +'one group against all others. The only column that matters is the last one — '
    +'chronic against <i>ordinary trending</i>.</p>'
    +'<p style="color:var(--chop)"><b>What it is NOT.</b> It is <b>not a trend '
    +'detector</b> — chronic is supposed to be trend <i>plus</i> starvation of '
    +'pullbacks <i>plus</i> duration, and the whole point is separating it from a '
    +'normal trend. <b>On this evidence it does not.</b> The boundary separation is '
    +'+0.237&nbsp;sd at p=0.392, the starvation component is worth +0.012&nbsp;sd, '
    +'and the drift component puts chronic episodes at a random walk. It is also '
    +'<b>not validated out of sample</b>: five independent macro events, three '
    +'before 2016 and three after, cannot support a holdout split — that is a '
    +'limit of the phenomenon, which is rare, not of the method. <b>Do not route '
    +'on this.</b></p></div></details>';
   $('#chronic').innerHTML=h;
  }

  function svg(w,h,inner){return `<svg viewBox="0 0 ${w} ${h}" xmlns="http://www.w3.org/2000/svg">${inner}</svg>`;}
  function txt(x,y,t,o){o=o||{};return `<text x="${x}" y="${y}" fill="${o.c||'var(--mute)'}" font-size="${o.s||11}" text-anchor="${o.a||'start'}" font-family="${o.m?'var(--mono)':'inherit'}" font-weight="${o.w||400}">${t}</text>`;}
  function buildNew(){
   const B=BUN; if(!B.sweep) return;
   // ---- sweep scatter: mean vs median ----
   (function(){const S=B.sweep;if(!S.length)return;const W=700,H=420,P=52;
    const xs=S.map(d=>d.mean_oos_sharpe),ys=S.map(d=>d.median_oos_sharpe);
    const lo=Math.min(...xs,...ys),hi=Math.max(...xs,...ys),pad=(hi-lo)*.1||.1;
    const x=v=>P+(v-lo+pad)/(hi-lo+2*pad)*(W-P-16),y=v=>H-P-(v-lo+pad)/(hi-lo+2*pad)*(H-P-16);
    let g='';for(let i=0;i<=4;i++){const v=lo-pad+(hi-lo+2*pad)*i/4;
     g+=`<line x1="${P}" y1="${y(v)}" x2="${W-16}" y2="${y(v)}" stroke="var(--line)"/>`;
     g+=txt(P-7,y(v)+4,v.toFixed(2),{a:'end',m:1,s:10})+txt(x(v),H-P+16,v.toFixed(2),{a:'middle',m:1,s:10});}
    g+=`<line x1="${x(lo-pad)}" y1="${y(lo-pad)}" x2="${x(hi+pad)}" y2="${y(hi+pad)}" stroke="var(--line2)" stroke-dasharray="4 4"/>`;
    g+=`<line x1="${x(0)}" y1="16" x2="${x(0)}" y2="${H-P}" stroke="var(--line2)"/>`;
    S.forEach(d=>{const c=d.family==='momentum'?'var(--kill)':'var(--trend)';
     g+=`<circle cx="${x(d.mean_oos_sharpe)}" cy="${y(d.median_oos_sharpe)}" r="4.5" fill="${c}" opacity=".7"/>`;});
    g+=txt(W/2,H-10,'mean OOS Sharpe',{a:'middle'})+`<text x="14" y="${H/2}" fill="var(--mute)" font-size="11" text-anchor="middle" transform="rotate(-90 14 ${H/2})">median OOS Sharpe</text>`;
    g+=`<circle cx="${W-150}" cy="30" r="4.5" fill="var(--trend)"/>`+txt(W-138,34,'mean reversion');
    g+=`<circle cx="${W-150}" cy="48" r="4.5" fill="var(--kill)"/>`+txt(W-138,52,'momentum');
    $('#swscat').innerHTML=svg(W,H,g);})();
   // ---- sweep table ----
   $('#swt tbody').innerHTML=B.sweep.slice().sort((a,b)=>b.mean_oos_sharpe-a.mean_oos_sharpe)
    .map(d=>{const c=d.mean_oos_sharpe>0?'var(--trend)':'var(--kill)';
     const pr=d.family==='momentum'?`${d.param_n_short}/${d.param_n_long}`:`${d.param_n} @ ${d.param_entry}`;
     return `<tr><td>${d.config_id}</td><td>${d.family}</td><td>${pr}</td>
     <td style="color:${c}">${d.mean_oos_sharpe.toFixed(3)}</td><td>${d.median_oos_sharpe.toFixed(3)}</td>
     <td>${(d.pct_positive*100).toFixed(0)}%</td><td>${d.mean_trades.toFixed(0)}</td>
     <td>${d.worst_sharpe.toFixed(2)}</td><td>${d.t_across.toFixed(2)}</td></tr>`;}).join('');
   // ---- durations ----
   (function(){const D2=B.duration;if(!D2.length)return;const W=700,H=190,P=118;
    const mx=Math.max(...D2.map(d=>d.mean_duration_days))*1.15;let g='';
    const th=P+(5/mx)*(W-P-60);
    g+=`<line x1="${th}" y1="6" x2="${th}" y2="${H-24}" stroke="var(--kill)" stroke-dasharray="3 3"/>`;
    g+=txt(th+5,16,'5-day floor',{c:'var(--kill)',s:10});
    D2.forEach((d,i)=>{const yy=22+i*38,w=(d.mean_duration_days/mx)*(W-P-60);
     const c=d.flips_faster_than_weekly?'var(--kill)':'var(--chop)';
     g+=txt(P-8,yy+13,d.detector,{a:'end',m:1,s:11,c:'var(--ink)'});
     g+=`<rect x="${P}" y="${yy}" width="${Math.max(w,2)}" height="18" fill="${c}" opacity=".7" rx="1"/>`;
     g+=txt(P+Math.max(w,2)+7,yy+13,d.mean_duration_days.toFixed(1)+'d avg / '+d.median_duration_days.toFixed(0)+'d median',{m:1,s:10});});
    $('#durch').innerHTML=svg(W,H,g);})();
   // ---- ladder table ----
   $('#ldt tbody').innerHTML=B.ladder.slice().sort((a,b)=>a.strategy.localeCompare(b.strategy)||a.cell.localeCompare(b.cell))
    .map(d=>{const f=v=>{if(v==null)return '';const c=v>0?'var(--trend)':(v<-.001?'var(--kill)':'var(--dim)');
     return `<td style="color:${c}">${(v*100).toFixed(1)}%</td>`;};
     return `<tr><td>${d.strategy}</td><td>${d.cell}</td><td>${(d.data_pct*100).toFixed(1)}%</td>
     ${f(d.imp_retexp)}${f(d.imp_retdd)}${f(d.imp_pf)}${f(d.imp_win)}${f(d.imp_avg)}</tr>`;}).join('');
  
   // ---- 9-box heatmaps ----
   (function(){
    // Two second axes: the original volatility percentile, and the 32 independent
    // survivors combined into one sign-aligned composite. Direction comes from the
    // 60d slope t-stat in both -- the survivors carry no direction, the efficiency
    // ratio being unsigned.
    let NBSRC='vol';
    function nbdata(){return NBSRC==='vol'?B.ninebox:(B.ninebox_surv||[]);}
    function nbrows(){return NBSRC==='vol'?['high','med','low']:['trend','mid','chop'];}
    function drawNB(){const N=nbdata();if(!N||!N.length)return;
    const DIR=['down','flat','up'],VOL=nbrows();
    const base=N.find(d=>d.cell==='BASELINE')||{eff:0,turn:0};
    const cells=N.filter(d=>d.cell!=='BASELINE');
    const mx=Math.max(...cells.map(d=>Math.abs(d.eff_lift)))||1;
    let html='<table class="nb"><tr><th></th>'+DIR.map(d=>'<th>'+d+'</th>').join('')+'</tr>';
    VOL.forEach(v=>{html+='<tr><th>'+v+'</th>';
     DIR.forEach(d=>{const c=cells.find(x=>x.cell===v+'|'+d);
      if(!c){html+='<td>\u2014</td>';return;}
      const a=Math.abs(c.eff_lift)/mx*.85+.1;
      const col=c.eff_lift>0?'var(--trend)':'var(--chop)';
      html+='<td style="background:'+col+';opacity:'+a.toFixed(2)+'" '
       +'title="fwd efficiency '+c.eff.toFixed(4)+', lift '+(c.eff_lift>0?'+':'')
       +c.eff_lift.toFixed(4)+', pair agreement '+(c.agree_eff*100).toFixed(0)+'%">'
       +(c.eff_lift>0?'+':'')+c.eff_lift.toFixed(4)+'<br><span style="font-size:10px;opacity:.85">'
       +(c.agree_eff*100).toFixed(0)+'% agree</span></td>';});
     html+='</tr>';});
    html+='</table>';
    $('#nbgrid').innerHTML=html;
    if($('#nbwhich'))$('#nbwhich').textContent=NBSRC==='vol'
      ?'60d realised vol as a percentile of its own trailing 500d'
      :'32 survivors, sign-aligned so high = expect straight travel';
    const srt=cells.slice().sort((a,b)=>b.eff_lift-a.eff_lift);
    $('#nbt tbody').innerHTML=srt.map(c=>`<tr><td>${c.cell}</td>
     <td>${c.eff.toFixed(4)}</td>
     <td style="color:${c.eff_lift>0?'var(--trend)':'var(--chop)'}">${c.eff_lift>0?'+':''}${c.eff_lift.toFixed(4)}</td>
     <td>${(c.agree_eff*100).toFixed(0)}%</td>
     <td>${c.turn.toFixed(4)}</td>
     <td style="color:${c.turn_lift<0?'var(--trend)':'var(--chop)'}">${c.turn_lift>0?'+':''}${c.turn_lift.toFixed(4)}</td>
     <td>${(c.data_pct*100).toFixed(1)}%</td></tr>`).join('');
    const sep=srt[0].eff_lift-srt[srt.length-1].eff_lift;
    $('#nbtx').innerHTML=`Baseline forward-20d efficiency <b>${base.eff.toFixed(4)}</b>, `
     +`turn frequency <b>${base.turn.toFixed(4)}</b>. Best box minus worst box `
     +`<b>${sep>0?'+':''}${sep.toFixed(4)}</b> \u2014 that is the separation power of `
     +`this axis. Efficiency and turn frequency move in opposite directions across the `
     +`grid, which is the coherence check: a box that precedes straighter travel should `
     +`also precede fewer direction changes.`;}
    drawNB();
    if($('#nbA'))$('#nbA').onclick=e=>{NBSRC='vol';
      e.target.setAttribute('aria-pressed',true);$('#nbB').setAttribute('aria-pressed',false);drawNB();};
    if($('#nbB'))$('#nbB').onclick=e=>{NBSRC='surv';
      e.target.setAttribute('aria-pressed',true);$('#nbA').setAttribute('aria-pressed',false);drawNB();};
   })();
  
  
   // ---- survivor-read agreement across timeframes (regime, not direction) ----
   (function(){const A=B.mtfagree_surv;if(!A||!A.length)return;
    $('#mtsagree').innerHTML='<b>Agreement on the survivor read (trend/mid/chop) '
     +'across timeframes:</b> '
     +A.map(d=>`${d.tfs} ${(d.regime_agree*100).toFixed(1)}%`).join(' \u00b7 ')
     +'. Chance is 33%. Far higher than the direction agreement above \u2014 the '
     +'trend/chop read is much more consistent across timeframes than direction is, '
     +'which is why all-three-aligned covers most bars and carries less information '
     +'than partial agreement.';})();

   // ---- multi-timeframe ----
   (function(){const A=B.mtfagree,M=B.mtf;if(!A||!A.length)return;
    const W=660,H=170,P=76,CH=1/3;
    const mx=Math.max(...A.map(d=>Math.max(d.dir_agree,d.vol_agree)))*1.2;
    let g='';const cx=v=>P+(v/mx)*(W-P-96);
    g+=`<line x1="${cx(CH)}" y1="8" x2="${cx(CH)}" y2="${H-30}" stroke="var(--kill)" stroke-dasharray="3 3"/>`;
    g+=txt(cx(CH)+5,18,'chance 0.333',{c:'var(--kill)',s:10});
    A.forEach((d,i)=>{const yy=26+i*42;
     g+=txt(P-8,yy+22,d.tfs,{a:'end',m:1,s:12,c:'var(--ink)'});
     [['dir_agree','var(--trend)',0],['vol_agree','var(--chop)',18]].forEach(([k,c,off])=>{
      const w=cx(d[k])-P;
      g+=`<rect x="${P}" y="${yy+off}" width="${Math.max(w,2)}" height="15" fill="${c}" opacity=".7" rx="1"/>`;
      g+=txt(P+w+7,yy+off+12,d[k].toFixed(3),{m:1,s:10});});});
    g+=`<rect x="${W-92}" y="10" width="11" height="11" fill="var(--trend)"/>`+txt(W-77,20,'direction',{s:10});
    g+=`<rect x="${W-92}" y="26" width="11" height="11" fill="var(--chop)"/>`+txt(W-77,36,'volatility',{s:10});
    $('#mtag').innerHTML=svg(W,H,g);
    // confluence bars
    const ord=['all 3 aligned','aligned trending','aligned flat','2 of 3','daily alone','BASELINE'];
    const rows=ord.map(k=>M.find(d=>d.cell===k)).filter(Boolean);
    const W2=660,H2=40+rows.length*38,P2=140;
    const m2=Math.max(...rows.map(d=>Math.abs(d.eff_lift||0)))*1.25||1;
    let h=`<line x1="${P2}" y1="6" x2="${P2}" y2="${H2-22}" stroke="var(--line2)"/>`;
    rows.forEach((d,i)=>{const yy=12+i*38,w=Math.abs(d.eff_lift||0)/m2*(W2-P2-110);
     const base=d.cell==='BASELINE';
     const c=base?'var(--flat)':((d.eff_lift||0)>0?'var(--trend)':'var(--chop)');
     h+=txt(P2-10,yy+16,d.cell,{a:'end',m:1,s:11,c:base?'var(--dim)':'var(--ink)'});
     h+=`<rect x="${P2}" y="${yy+3}" width="${Math.max(w,2)}" height="19" fill="${c}" opacity=".75" rx="1"/>`;
     h+=txt(P2+Math.max(w,2)+8,yy+17,((d.eff_lift>0?'+':'')+d.eff_lift.toFixed(4))+'   '+(d.data_pct*100).toFixed(1)+'% of bars',{m:1,s:10});});
    h+=txt(P2,H2-6,'forward-20d efficiency lift \u00b7 grey bar is the all-bars baseline',{s:10});
    $('#mtcf').innerHTML=svg(W2,H2,h);
    $('#mtt tbody').innerHTML=rows.slice().sort((x,y)=>(y.eff_lift||0)-(x.eff_lift||0)).map(d=>{
     const base=d.cell==='BASELINE';
     const c=base?'var(--dim)':(d.eff_lift>0?'var(--trend)':'var(--chop)');
     return `<tr><td style="color:${c}">${d.cell}</td><td>${(d.data_pct*100).toFixed(1)}%</td>
     <td>${d.eff.toFixed(4)}</td>
     <td style="color:${c}">${d.eff_lift>0?'+':''}${d.eff_lift.toFixed(4)}</td>
     <td>${d.agree_eff==null?'\u2014':(d.agree_eff*100).toFixed(0)+'%'}</td>
     <td>${d.turn.toFixed(4)}</td>
     <td style="color:${d.turn_lift<0?'var(--trend)':'var(--chop)'}">${d.turn_lift>0?'+':''}${d.turn_lift.toFixed(4)}</td>
     </tr>`;}).join('');
    const cells=M.filter(d=>d.cell!=='BASELINE');
    const bestc=cells.reduce((a,b)=>a.eff_lift>b.eff_lift?a:b);
    const worstc=cells.reduce((a,b)=>a.eff_lift<b.eff_lift?a:b);
    $('#mttx').innerHTML=`<b>${bestc.cell}</b> precedes the straightest travel
     (${bestc.eff_lift>0?'+':''}${bestc.eff_lift.toFixed(4)} efficiency against baseline,
     ${(bestc.agree_eff*100).toFixed(0)}% of pairs agreeing);
     <b>${worstc.cell}</b> the choppiest (${worstc.eff_lift.toFixed(4)}).
     Separation across cells is
     <b>${(bestc.eff_lift-worstc.eff_lift).toFixed(4)}</b>. Turn frequency moves the
     opposite way, which is the coherence check.`;})();
  
   // ---- DSR funnel ----
   (function(){const F2=B.funnel;if(!F2.length)return;const W=700,H=160,P=16;
    const mx=F2[0].count;let g='';
    F2.forEach((d,i)=>{const yy=14+i*46,w=(d.count/mx)*(W-2*P);
     const c=d.count===0?'var(--kill)':'var(--trend)';
     g+=`<rect x="${P}" y="${yy}" width="${Math.max(w,2)}" height="20" fill="${c}" opacity=".55" rx="1"/>`;
     g+=txt(P+4,yy-3,d.stage,{s:10.5});
     g+=txt(P+Math.max(w,2)+8,yy+15,d.count.toLocaleString(),{m:1,s:13,c:c,w:600});});
    $('#funch').innerHTML=svg(W,H,g);
    $('#funtx').innerHTML=`<b>${B.meta.dsr_pass} of ${B.meta.variants.toLocaleString()}</b> individual
    variants survive DSR &ge; 0.95. Expected max Sharpe under the null, given this many attempts,
    is <b>${B.meta.emax}</b> \u2014 higher than almost anything observed.`;})();
   // ---- logic diverging bars ----
   (function(){const L=B.logic;if(!L.length)return;const W=700,P=150;
    const rows=L.slice().sort((a,b)=>b.mean_delta_sharpe-a.mean_delta_sharpe);
    const H=26+rows.length*26;const mx=Math.max(...rows.map(d=>Math.abs(d.mean_delta_sharpe)))*1.2;
    const zx=P+((W-P-60)/2);let g=`<line x1="${zx}" y1="6" x2="${zx}" y2="${H-14}" stroke="var(--line2)"/>`;
    rows.forEach((d,i)=>{const yy=12+i*26,v=d.mean_delta_sharpe,w=Math.abs(v)/mx*((W-P-60)/2);
     const ctrl=d.logic==='switch_backwards';
     const c=ctrl?'var(--flat)':(v>0?'var(--trend)':'var(--kill)');
     g+=txt(P-8,yy+13,d.detector+' / '+d.logic,{a:'end',m:1,s:10,c:ctrl?'var(--dim)':'var(--ink)'});
     g+=`<rect x="${v>0?zx:zx-w}" y="${yy+2}" width="${Math.max(w,1)}" height="15" fill="${c}" opacity=".75" rx="1"/>`;
     g+=txt(v>0?zx+w+6:zx-w-6,yy+14,v.toFixed(3)+'  '+(d.pct_positive*100).toFixed(0)+'%+',
      {m:1,s:9.5,a:v>0?'start':'end'});});
    g+=txt(zx,H-2,'mean \u0394 OOS Sharpe vs baseline',{a:'middle',s:10});
    $('#logch').innerHTML=svg(W,H,g);})();
   // ---- complexity ----
   (function(){const L=B.logic;const lg=['gate','switch','switch_backwards'];
    const get=(d,l)=>{const r=L.find(x=>x.detector===d&&x.logic===l);return r?r.mean_delta_sharpe:0;};
    const W=700,H=230,P=60;const mx=Math.max(...lg.map(l=>Math.max(Math.abs(get('trend_sma200',l)),Math.abs(get('hmm_2state',l)))))*1.25;
    const y0=H-46,sc=(H-70)/mx;let g=`<line x1="${P}" y1="${y0}" x2="${W-16}" y2="${y0}" stroke="var(--line2)"/>`;
    lg.forEach((l,i)=>{const bx=P+30+i*((W-P-60)/3);
     [['trend_sma200','var(--trend)',0],['hmm_2state','var(--chop)',46]].forEach(([d,c,off])=>{
      const v=get(d,l),h=Math.abs(v)*sc;
      g+=`<rect x="${bx+off}" y="${v>0?y0-h:y0}" width="38" height="${Math.max(h,1)}" fill="${c}" opacity=".75" rx="1"/>`;
      g+=txt(bx+off+19,(v>0?y0-h-6:y0+h+13),v.toFixed(3),{a:'middle',m:1,s:9.5});});
     g+=txt(bx+42,H-12,l,{a:'middle',s:11});});
    g+=`<rect x="${W-160}" y="12" width="12" height="12" fill="var(--trend)"/>`+txt(W-143,22,'200-day SMA');
    g+=`<rect x="${W-160}" y="32" width="12" height="12" fill="var(--chop)"/>`+txt(W-143,42,'fitted HMM');
    $('#cmpch').innerHTML=svg(W,H,g);
    const t=get('trend_sma200','switch'),h=get('hmm_2state','switch');
    $('#cmptx').innerHTML=`On switch logic the simple rule wins: <b>${t.toFixed(3)}</b> vs
    <b>${h.toFixed(3)}</b> for the fitted model. On gate it is not close:
    <b>${get('trend_sma200','gate').toFixed(3)}</b> vs <b>${get('hmm_2state','gate').toFixed(3)}</b>.
    Complexity did not buy anything here.`;})();
  }
  
  // ---- classifier validation + window curve ----
  (function(){const V=BUN.clsval||[],RS=BUN.ribsweep||[];
   const get=(c,m)=>{const r=V.find(d=>d.check===c&&d.metric===m);return r?r.value:null;};
   if(V.length){
    const f=(v,n)=>v==null?'—':(+v).toFixed(n==null?3:n);
    $('#clsval').innerHTML='<div class="tw"><table><thead><tr><th>Check</th>'
     +'<th>Result</th><th>Surrogate A<br><span class="count">signs shuffled,'
     +' vol clustering kept</span></th><th>Surrogate B<br><span class="count">IID,'
     +' vol clustering destroyed</span></th></tr></thead><tbody>'
     +`<tr><td>Median run length</td><td><b>${f(get('persistence','median_run'),2)}</b>
        bars</td><td>${f(get('null_A','median_run'),2)}</td>
        <td>${f(get('null_B','median_run'),2)}</td></tr>`
     +`<tr><td>Separation (mean gap, sd units)</td>
        <td><b>${f(get('separation','realised_vol'))}</b> vol,
        ${f(get('separation','avg_abs_move'))} move</td>
        <td>${f(get('null_A','separation'))}</td>
        <td>${f(get('null_B','separation'))}</td></tr>`
     +`<tr><td>Refit stability</td><td colspan="3"><b>${
        get('stability','label_agreement')==null?'—'
        :(get('stability','label_agreement')*100).toFixed(1)+'%'}</b> of pre-2016
        pair-days keep their label after refitting through 2020</td></tr>`
     +`<tr><td>Coverage</td><td colspan="3">${['low','mid','high'].map(k=>
        k+' '+f(get('coverage',k))).join(' · ')}</td></tr>`
     +'</tbody></table></div>';
    $('#clstxt').innerHTML=`<b>Read the two surrogates together.</b> A keeps every
     |return| exactly in place and moves only the signs, so volatility clustering is
     preserved perfectly &mdash; but <code>path = &Sigma;|r|</code> is <i>invariant</i>
     under that, which is why it returns the median run with zero variance across 200
     draws. It cannot move a scale-based classifier and passing it would mean nothing.
     B destroys volatility clustering instead. Under B the separation collapses from
     ${f(get('separation','realised_vol'))} to ${f(get('null_B','separation'))} &mdash;
     real &mdash; while the persistence only falls from
     ${f(get('persistence','median_run'),2)} to ${f(get('null_B','median_run'),2)} bars,
     so about one bar in eleven is market structure and the other ten are the rolling
     window.`;
   }
   const SV=BUN.shapeval||[],CV=BUN.combval||[];
   if(SV.length){
    const f=(v,n)=>v==null||v===''?'&mdash;':(+v).toFixed(n==null?3:n);
    const NEUT=['autocorr','dir_changes','mean_crossings','run_length'];
    $('#shapeblock').innerHTML='<div class="tw"><table><thead><tr>'
     +'<th>Property</th><th>Structural</th><th>Nine-state</th><th>Weighted</th>'
     +'<th>Kind</th></tr></thead><tbody>'+SV.map(r=>'<tr><td>'+r.prop+'</td><td>'
     +f(r.structural)+'</td><td>'+f(r.grid)+'</td><td>'+f(r.weighted)+'</td><td>'
     +'<span class="count">'+(r.kind||'')+(NEUT.indexOf(r.prop)>=0
       ?', neutral':'')+'</span></td></tr>').join('')+'</tbody></table></div>';
   }
   if(CV.length){
    const f=(v,n)=>v==null||v===''?'&mdash;':(+v).toFixed(n==null?3:n);
    const sw=CV.filter(r=>r.null==null||r.null===''),
          nl=CV.filter(r=>r.null!=null&&r.null!=='');
    $('#dwellblock').innerHTML='<div class="tw"><table><thead><tr><th>Classifier'
     +'</th><th>Dwell M</th><th>Median run</th><th>Runs under 5</th>'
     +'<th>Diagonal</th><th>Shape separation</th><th>States</th>'
     +'</tr></thead><tbody>'+sw.map(r=>'<tr><td>'+r.classifier+'</td><td>'
     +(r.M?r.M:'&mdash;')+'</td><td>'+f(r.median_run,0)+'</td><td>'
     +f(100*r.under5,1)+'%</td><td>'+f(r.diagonal)+'</td><td>'+f(r.gap_sd)
     +'</td><td>'+r.n_states+'</td></tr>').join('')+'</tbody></table></div>'
     +'<div class="tw"><table><thead><tr><th>Null</th><th>Classifier</th>'
     +'<th>Real</th><th>Surrogate</th><th>Corrected</th><th>p</th></tr></thead>'
     +'<tbody>'+nl.map(r=>'<tr><td>'+r.null+'</td><td>'+r.classifier+'</td><td>'
     +f(r.real)+'</td><td>'+f(r.surrogate)+' &plusmn; '+f(r.sd)+'</td><td><b>'
     +(r.corrected>0?'+':'')+f(r.corrected)+'</b></td><td>'+f(r.p)
     +'</td></tr>').join('')+'</tbody></table></div>';
    $('#shapetxt').innerHTML=`<b>Separation is not comparable across state
     counts</b> &mdash; a 12-state classifier has more chances at an extreme than
     a four-state one, and a longer confirmation dwell lengthens every block,
     which raises separation on properties that are themselves autocorrelated.
     Both effects are why only the <b>corrected</b> column means anything: the
     surrogate carries the identical classifier, the identical state count and
     the identical dwell. Every corrected value here is negative. The dwell does
     fix the flickering &mdash; a 3-bar median run and 62% of runs under 5 bars
     becomes 13 bars and 0.1% at M=5 &mdash; and it does raise raw shape
     separation from 0.316 to 0.477, but it raises the surrogate from 0.337 to
     0.520 at the same time. Shape is not described by any of these definitions.
     What survives its null is the magnitude reading: 0.881 on realised vol and
     0.976 on mean absolute move against 0.378 and 0.020.`;
   }
   const SS=BUN.structsel||[],SR=BUN.structselres||[];
   if(SS.length){
    const f=(v,n)=>v==null||v===''?'&mdash;':(+v).toFixed(n==null?4:n);
    const pa=SS.filter(r=>r.A_corr>0).length,pb=SS.filter(r=>r.B_corr>0).length,
          both=SS.filter(r=>r.A_corr>0&&r.B_corr>0).length,
          exp=(pa*pb/SS.length).toFixed(1);
    const top=SS.slice().sort((x,y)=>y.A_corr-x.A_corr).slice(0,8);
    $('#selblock').innerHTML='<h3>IS-only selection of the structural cell</h3>'
     +'<div class="note">Criterion fixed before the sweep: mean <b>null-corrected'
     +'</b> shape separation over the four neutral properties, selected on IS-A'
     +' (1999&ndash;2007), required to agree in sign on IS-B (2008&ndash;2015),'
     +' holdout read once. Corrected, not raw &mdash; raw separation rises with'
     +' block length, so selecting on it would pick the most persistent cell and'
     +' call it the most descriptive.</div>'
     +'<div class="note">Positive on IS-A: <b>'+pa+'</b> of '+SS.length
     +'. Positive on IS-B: <b>'+pb+'</b>. Positive on <b>both</b>: <b>'+both
     +'</b>, against '+exp+' expected if the two blocks were independent coin'
     +' flips. Block agreement is at chance.</div>'
     +'<div class="tw"><table><thead><tr><th>N</th><th>B</th><th>D</th><th>R</th>'
     +'<th>IS-A corrected</th><th>z</th><th>IS-B corrected</th><th>z</th>'
     +'<th>Agree</th></tr></thead><tbody>'+top.map(r=>'<tr><td>'+r.N+'</td><td>'
     +r.B+'</td><td>'+r.D+'</td><td>'+r.R+'</td><td>'+f(r.A_corr)+'</td><td>'
     +f(r.A_z,2)+'</td><td>'+f(r.B_corr)+'</td><td>'+f(r.B_z,2)+'</td><td>'
     +(r.agree===true||r.agree==='True'?'yes':'<b>no</b>')+'</td></tr>').join('')
     +'</tbody></table><div class="count">Top eight cells by IS-A corrected'
     +' separation. Every one is negative on IS-B &mdash; the IS-A ranking does'
     +' not transfer between blocks.</div></div>'
     +(SR.length?'<div class="tw"><table><thead><tr><th>Holdout, read once</th>'
      +'<th>Real</th><th>Surrogate</th><th>Corrected</th><th>p</th></tr></thead>'
      +'<tbody>'+SR.map(r=>'<tr><td>N='+r.N+' B='+r.B+' D='+r.D+' R='+r.R
      +', M='+r.M+' &middot; '+r.null+'</td><td>'+f(r.real,3)+'</td><td>'
      +f(r.surrogate,3)+' &plusmn; '+f(r.sd,3)+'</td><td><b>'
      +(r.corrected>0?'+':'')+f(r.corrected,3)+'</b></td><td>'+f(r.p,3)
      +'</td></tr>').join('')+'</tbody></table></div>':'');
   }
   const EC=BUN.epicount||[],EX=BUN.epiexc||[],PC=BUN.pairclf||[],
         TE=BUN.transedge||[],MN=BUN.magnull||[],ES=BUN.episep||[];
   const ff=(v,n)=>v==null||v===''?'&mdash;':(+v).toFixed(n==null?3:n);
   if(EC.length||EX.length){
    let h='<div class="note"><b>Bars are not independent observations.</b> A '
     +'20-bar state is one episode, not twenty pieces of evidence. Two '
     +'corrections are applied: an <b>episode basis</b> (one row per state run, '
     +'fixing serial dependence within a pair) and a <b>moving-block bootstrap '
     +'over calendar dates</b> (a block carries every pair on those dates, so '
     +'cross-pair correlation rides along too). Surrogate-based p-values were '
     +'already sound &mdash; they recompute the whole statistic on each '
     +'surrogate panel, so no independence was ever assumed in them.</div>';
    if(EC.length) h+='<div class="tw"><table><thead><tr><th>Classifier</th>'
     +'<th>Holdout bars</th><th>Episodes</th><th>Overstatement</th></tr></thead>'
     +'<tbody>'+EC.map(r=>'<tr><td>'+r.classifier+'</td><td>'+r.bars+'</td><td>'
     +r.episodes+'</td><td><b>'+ff(r.ratio,1)+'&times;</b></td></tr>').join('')
     +'</tbody></table><div class="count">A t-statistic pooled over bars '
     +'overstates its sample by this factor and its |t| by about its square '
     +'root.</div></div>';
    if(EX.length) h+='<div class="tw"><table><thead><tr><th>Contrast</th>'
     +'<th>Metric</th><th>Observed</th><th>Published t</th><th>p@21</th>'
     +'<th>p@63</th><th>p@126</th></tr></thead><tbody>'+EX.map(r=>{
      const live=Math.max(r.p_21,r.p_63,r.p_126)<0.05;
      return '<tr><td>'+(live?'&#9679; ':'')+r.contrast+'</td><td>'
      +r.metric+'</td><td>'+ff(r.observed,4)+'</td><td>'
      +(r.naive_t==null||r.naive_t===''?'&mdash;':ff(r.naive_t,2))+'</td><td>'
      +ff(r.p_21)+'</td><td><b>'+ff(r.p_63)+'</b></td><td>'+ff(r.p_126)
      +'</td></tr>';}).join('')+'</tbody></table><div class="count">Two-sided '
     +'block-bootstrap p at three block lengths. &#9679; marks the rows '
     +'significant at every block length.</div></div>';
    if(MN.length) h+='<div class="note"><b>Correction.</b> &ldquo;Magnitude '
     +'survives at 0.881 and 0.976 against nulls of 0.378 and 0.020&rdquo; was '
     +'not a matched comparison &mdash; the real values are the grid&rsquo;s, '
     +'the nulls belong to the three-state weighted classifier. Matched:</div>'
     +'<div class="tw"><table><thead><tr><th>Null</th><th>Classifier</th>'
     +'<th>Property</th><th>Real</th><th>Surrogate</th><th>Corrected</th>'
     +'<th>p</th></tr></thead><tbody>'+MN.map(r=>'<tr><td>'+r.null+'</td><td>'
     +r.classifier+'</td><td>'+r.prop+'</td><td>'+ff(r.real)+'</td><td>'
     +ff(r.surrogate)+' &plusmn; '+ff(r.sd)+'</td><td><b>'
     +(r.corrected>0?'+':'')+ff(r.corrected)+'</b></td><td>'+ff(r.p)
     +'</td></tr>').join('')+'</tbody></table><div class="count">Sign '
     +'randomisation is nearly degenerate for a magnitude axis: it keeps every '
     +'|r| in place, so mean absolute move is exactly invariant and '
     +'path = &Sigma;|r| barely moves. Only the IID row is a real test.</div>'
     +'</div>';
    $('#epiblock').innerHTML=h;
   }
   if(PC.length){
    const pos=PC.filter(r=>r.shape_corr>0).length,
          deg=PC.filter(r=>r.DEGENERATE===true||r.DEGENERATE==='True').length,
          uns=PC.filter(r=>r.UNSTABLE===true||r.UNSTABLE==='True').length;
    $('#pairblock').innerHTML='<div class="note"><b>Nothing had been tested per '
     +'pair.</b> Every pair gets its own surrogate &mdash; a per-pair number '
     +'against a pooled null would clear the bar for reasons that have nothing '
     +'to do with the classifier. <b>'+pos+' of '+PC.length+'</b> pairs are '
     +'positive on corrected shape, <b>'+deg+'</b> are degenerate (a state under '
     +'2% of that pair&rsquo;s bars), <b>'+uns+'</b> are unstable (median run '
     +'under 5).</div><div class="tw"><table><thead><tr><th>Pair</th>'
     +'<th>Shape</th><th>Surrogate</th><th>Corrected</th><th>z</th>'
     +'<th>Magnitude corr</th><th>Median run</th><th>States used</th></tr>'
     +'</thead><tbody>'+PC.slice().sort((a,b)=>b.shape_corr-a.shape_corr)
     .map(r=>'<tr><td>'+r.pair+'</td><td>'+ff(r.shape)+'</td><td>'
     +ff(r.shape_surr)+'</td><td><b>'+(r.shape_corr>0?'+':'')+ff(r.shape_corr)
     +'</b></td><td>'+(r.shape_z>0?'+':'')+ff(r.shape_z,2)+'</td><td>'
     +(r.mag_corr>0?'+':'')+ff(r.mag_corr)+'</td><td>'+ff(r.median_run,0)
     +'</td><td>'+r.states_used+'/'+r.states_seen+'</td></tr>').join('')
     +'</tbody></table></div>';
   }
   if(TE.length){
    $('#transblock').innerHTML='<div class="note"><b>Do bars at a state change '
     +'differ from bars deep inside one?</b> Age &le;3 against age &ge;15, '
     +'within the same state. Some difference must exist mechanically &mdash; a '
     +'28-bar window three bars into a new state is still mostly describing the '
     +'old one &mdash; so the surrogate, which has the same windows and the same '
     +'dwell, is what that mechanical part looks like.</div>'
     +'<div class="tw"><table><thead><tr><th>Classifier</th><th>Property</th>'
     +'<th>Edge &minus; interior</th><th>Surrogate</th><th>Corrected</th>'
     +'<th>z</th></tr></thead><tbody>'+TE.map(r=>'<tr><td>'+r.classifier
     +'</td><td>'+r.prop+'</td><td>'+(r.observed>0?'+':'')+ff(r.observed)
     +'</td><td>'+(r.surrogate>0?'+':'')+ff(r.surrogate)+'</td><td><b>'
     +(r.corrected>0?'+':'')+ff(r.corrected)+'</b></td><td>'
     +(r.corrected/r.sd>0?'+':'')+ff(r.corrected/r.sd,2)+'</td></tr>').join('')
     +'</tbody></table><div class="count">No corrected effect reaches |z| = 2 '
     +'across 18 comparisons. And direction carries nothing: entering trending '
     +'from broken and entering broken from trending show the SAME signed shift, '
     +'not opposite ones &mdash; the signature belongs to the boundary, not to '
     +'the way it was crossed.</div></div>';
   }
   const AB=BUN.axesab||[],AC=BUN.axesct||[],ACS=BUN.axescts||[],AS=BUN.axesset||[];
   if(AB.length){
    const g=(v,n)=>v==null||v===''?'&mdash;':(+v).toFixed(n==null?3:n);
    const pct=t=>{const tot=t.reduce((a,r)=>a+['weak','medium','strong','trend',
      'transitional','chop'].reduce((x,k)=>x+(+r[k]||0),0),0);
      return {t:t,tot:tot};};
    let h='<div class="note"><b>Where scale enters.</b> <code>act = tercile('
     +'raw_axes(px)[&#39;scale&#39;], fit)</code> &rarr; <code>act + &#39; &#39;'
     +' + shape</code> &rarr; the 5-bar dwell on the joint label. The activity '
     +'word is the first half of every combined state. But being in the string '
     +'is not proof it carries anything, so each layer is knocked out in '
     +'turn:</div><div class="tw"><table><thead><tr><th>Variant</th>'
     +'<th>Magnitude separation</th><th>Shape separation</th><th>States</th>'
     +'</tr></thead><tbody>'+AB.map(r=>'<tr><td>'+r.variant+'</td><td><b>'
     +g(r.magnitude)+'</b></td><td>'+g(r.shape)+'</td><td>'+r.n_states
     +'</td></tr>').join('')+'</tbody></table><div class="count">Removing '
     +'activity collapses magnitude 0.703 &rarr; 0.137. Removing shape does not '
     +'touch it. The volatility axis supplies essentially all of the combined '
     +'state&rsquo;s magnitude reading &mdash; and the nine-box on its own beats '
     +'the combined state on <i>both</i> axes.</div></div>';
    if(AC.length) h+='<div class="note"><b>Shape against activity</b>, observed '
     +'&divide; expected. 1.00 is independence.</div><div class="tw"><table>'
     +'<thead><tr><th>Shape</th><th>weak</th><th>medium</th><th>strong</th></tr>'
     +'</thead><tbody>'+(function(){const tot=AC.reduce((a,r)=>a+(+r.weak)+
      (+r.medium)+(+r.strong),0);
      const rs=AC.map(r=>(+r.weak)+(+r.medium)+(+r.strong));
      const cs=['weak','medium','strong'].map(k=>AC.reduce((a,r)=>a+(+r[k]),0));
      return AC.map((r,i)=>'<tr><td>'+(r.shape||r.state)+'</td>'
       +['weak','medium','strong'].map((k,j)=>'<td>'
        +g((+r[k])/(rs[i]*cs[j]/tot))+'</td>').join('')+'</tr>').join('');})()
     +'</tbody></table><div class="count">Cramer&rsquo;s V 0.094 '
     +'[0.069, 0.115], normalised mutual information 0.009. Shape separation '
     +'inside weak / medium / strong activity is 0.564 / 0.453 / 0.472 with '
     +'overlapping intervals &mdash; shape reads the same way whether or not the '
     +'pair is moving. <b>Two genuinely independent axes.</b></div></div>';
    if(ACS.length) h+='<div class="note"><b>And against straightness</b> &mdash; '
     +'the nine-box axis shape might actually be replacing.</div>'
     +'<div class="tw"><table><thead><tr><th>Shape</th><th>trend</th>'
     +'<th>transitional</th><th>chop</th></tr></thead><tbody>'
     +(function(){const K=['trend','transitional','chop'];
      const tot=ACS.reduce((a,r)=>a+K.reduce((x,k)=>x+(+r[k]),0),0);
      const rs=ACS.map(r=>K.reduce((x,k)=>x+(+r[k]),0));
      const cs=K.map(k=>ACS.reduce((a,r)=>a+(+r[k]),0));
      return ACS.map((r,i)=>'<tr><td>'+(r.shape||r.state)+'</td>'
       +K.map((k,j)=>'<td>'+g((+r[k])/(rs[i]*cs[j]/tot))+'</td>').join('')
       +'</tr>').join('');})()
     +'</tbody></table><div class="count">Cramer&rsquo;s V 0.193 &mdash; twice '
     +'the overlap with scale, and structural <i>trending</i> runs 2.81&times; '
     +'expected inside the nine-box trend family. Related, as two attempts to '
     +'measure the same thing should be, but nowhere near a replacement.</div>'
     +'</div>';
    if(AS.length){const r=AS[0];
     h+='<div class="note"><b>Settling is not transitional renamed.</b> '
     +'P(transitional | settling) = '+g(r.p_trans_given_settling,4)+' against a '
     +'base rate of '+g(r.p_transitional,4)+' &mdash; lift <b>'+g(r.lift,3)
     +'</b>. The reverse is the same. Joint '+g(r.joint,4)+' against '
     +g(r.p_settling*r.p_transitional,4)+' expected under independence, '
     +'Cramer&rsquo;s V '+g(r.cramers_v,4)+'. The two labels pick out different '
     +'bars, at chance with respect to each other.</div>';}
    $('#axesblock').innerHTML=h;
   }
   const LT=BUN.leadtime||[];
   if(LT.length){
    const g=(v,n)=>v==null||v===''?'&mdash;':(+v).toFixed(n==null?3:n);
    const win=LT.filter(r=>r.excess>0.05&&r.p_sign<0.05).length;
    const top=LT.slice().sort((a,b)=>b.excess-a.excess);
    $('#leadblock').innerHTML='<div class="note">The 5-bar dwell means a change '
     +'visible in raw structure at <i>t</i> is not in the shipped label until '
     +'<i>t</i>+4. Three cheap signals were tested for whether they fire in that '
     +'window more often than before an arbitrary bar: <b>mas</b> (5-bar mean '
     +'turning against the 20-bar mean), <b>vol</b> (5 over 60 realised '
     +'volatility) and <b>rng</b> (5-bar close range over its 60-day average). '
     +'Thresholds are calibrated on IS to a common 10% firing budget, so a '
     +'signal cannot buy hit rate by firing more often, and a fire is an upward '
     +'<i>crossing</i>, not the condition holding.</div>'
     +'<div class="note"><b>The bar this is held to.</b> Cross-horizon '
     +'confluence fired 79% before real state changes and 79% before surrogate '
     +'ones, which is why it was dropped. So the whole thing &mdash; signals '
     +'<i>and</i> states &mdash; is rebuilt on 60 sign and 60 IID surrogate '
     +'panels, and what counts is <b>excess</b>: lift on real data minus the '
     +'larger surrogate lift.</div>'
     +'<div class="tw"><table><thead><tr><th>State</th><th>Signal</th>'
     +'<th>Lead</th><th>Hit</th><th>Base</th><th>Lift</th><th>Sign</th>'
     +'<th>IID</th><th>Excess</th><th>p</th></tr></thead><tbody>'
     +top.slice(0,12).map(r=>'<tr><td>'+r.state+'</td><td>'+r.signal+'</td><td>'
      +r.lead+'</td><td>'+g(100*r.hit,1)+'%</td><td>'+g(100*r.base,1)
      +'%</td><td>'+g(r.lift)+'</td><td>'+g(r.sign_lift)+'</td><td>'
      +g(r.iid_lift)+'</td><td><b>'+(r.excess>0?'+':'')+g(r.excess)
      +'</b></td><td>'+g(r.p_sign)+'</td></tr>').join('')
     +'</tbody></table><div class="count">Best twelve of 36 by excess. '
     +'<b>'+win+' of '+LT.length+'</b> beat both surrogates by more than 0.05 '
     +'lift at p&lt;0.05. The strongest raw lift in the table, mas at lead 1, is '
     +'1.739 &mdash; and its surrogate is 1.680. Same story as confluence: the '
     +'signal and the state are both reacting to the same volatility burst.'
     +'</div></div>'
     +'<div class="note"><b>So the lag is accepted.</b> <code>settling</code> in '
     +'layer1_states.csv is a graded confidence, min(age/5, 1) &mdash; 0.2 on the '
     +'first bar a state is adopted, 1.0 from the fifth. 22.6% of holdout bars '
     +'carry a reduced weight; 77.4% are fully weighted.</div>';
   }
   const MW=BUN.masweep||[],MR=BUN.maridge||[];
   if(MW.length){
    const g=(v,n)=>v==null||v===''?'&mdash;':(+v).toFixed(n==null?3:n);
    const ST='product M=5',G=[1,2,3,4,5,6,8,10,13,16,21,27,34,44,56,72,92,118,152,200];
    const sel=MW.filter(r=>r.state===ST&&r.lead===1&&r.family==='mas');
    const cell=(f,s2)=>sel.find(r=>r.fast===f&&r.slow===s2);
    const at=t=>MW.filter(r=>r.excess>t&&r.p<0.05).length;
    let h='<div class="note"><b>The three candidates in 16.4g were single '
     +'arbitrary settings</b> &mdash; 5/20, 5/60, 5/60 &mdash; so that result '
     +'tested three points, not three ideas. All three swept, both windows '
     +'1&ndash;200 on a 20-point log grid, 3,420 cells in total, every cell '
     +'against its own surrogate at its own window pair and a common firing '
     +'budget.</div>'
     +'<div class="note">A single spiking cell in a 190-cell grid is what noise '
     +'looks like; a broad <b>plateau</b> would mean something. So: <b>'+at(0.05)
     +' of '+MW.length+'</b> cells clear excess&gt;0.05 at p&lt;0.05 &mdash; '
     +(100*at(0.05)/MW.length).toFixed(1)+'%, <i>below</i> the ~5% chance alone '
     +'produces. '+at(0.10)+' clear at excess&gt;0.10, '+at(0.20)
     +' at excess&gt;0.20.</div>'
     +'<div class="tw"><table><thead><tr><th>MAS lift, fast &darr; slow &rarr;'
     +'</th>'+G.slice(1,12).map(x=>'<th>'+x+'</th>').join('')+'</tr></thead>'
     +'<tbody>'+G.slice(0,10).map(f=>'<tr><td><b>'+f+'</b></td>'
      +G.slice(1,12).map(s2=>{const c=cell(f,s2);
        return '<td>'+(c?(c.lift>=1.5?'<b>'+g(c.lift,2)+'</b>':g(c.lift,2)):'&middot;')+'</td>';})
      .join('')+'</tr>').join('')+'</tbody></table>'
     +'<div class="count">The lift surface has genuine structure: one sharp '
     +'ridge, at fast=5, reaching 2.13&times;. Its excess over its own surrogate '
     +'is only +0.21, and the surrogate sits at 1.91.</div></div>';
    if(MR.length) h+='<div class="tw"><table><thead><tr><th>Dwell M</th>'
     +'<th>Ridge peaks at fast =</th><th>Peak lift</th></tr></thead><tbody>'
     +MR.map(r=>'<tr><td>'+r.dwell+'</td><td><b>'+r.peak_fast+'</b></td><td>'
      +g(r.peak_lift,2)+'</td></tr>').join('')+'</tbody></table>'
     +'<div class="count"><b>The ridge moves with the dwell.</b> That is the '
     +'mechanism: an M-bar mean&rsquo;s slope turns over exactly the M bars the '
     +'confirmation is counting, so the signal reads the same window the dwell '
     +'reads rather than leading it. It cannot bridge a delay it is measuring '
     +'from the inside &mdash; which is why the lift is large and the surrogate '
     +'reproduces nearly all of it.</div></div>'
     +'<div class="note">Range expansion is the clearest failure: its best cell '
     +'scores +0.211 excess and its immediate neighbours average '
     +'<b>&minus;0.296</b>. An isolated spike with nothing around it.</div>';
    $('#sweepblock').innerHTML=h;
   }
   const MCF=BUN.maconfirm||[],MIS=BUN.maiss||[],LS=BUN.l1sum||[];
   const gg=(v,n)=>v==null||v===''?'&mdash;':(+v).toFixed(n==null?3:n);
   if(MCF.length){
    $('#confirmblock').innerHTML='<div class="note"><b>The sweep above measured '
     +'every cell on the holdout</b>, so its peak was selected on the same data '
     +'it was scored on. Redone properly: cell picked on IS, holdout read '
     +'once.</div><div class="tw"><table><thead><tr><th>Cell (IS-selected)</th>'
     +'<th>IS excess</th><th>Holdout lift</th><th>Surrogate</th>'
     +'<th>Holdout excess</th><th>p</th></tr></thead><tbody>'
     +MCF.map(r=>'<tr><td>'+r.family+' '+r.fast+'/'+r.slow+' &middot; '+r.null
      +'</td><td>'+(r.is_excess>0?'+':'')+gg(r.is_excess)+'</td><td>'
      +gg(r.holdout_lift)+'</td><td>'+gg(r.surrogate)+' &plusmn; '+gg(r.sd)
      +'</td><td><b>'+(r.excess>0?'+':'')+gg(r.excess)+'</b></td><td>'+gg(r.p)
      +'</td></tr>').join('')+'</tbody></table><div class="count">IS lift 1.492 '
     +'&rarr; holdout 1.117, and the holdout excess is negative against both '
     +'nulls. Dropped &mdash; there is no second confirmation signal. The graded '
     +'confidence stands alone.</div></div>';
   }
   if(LS.length){
    const grp={};LS.forEach(r=>{(grp[r.area]=grp[r.area]||[]).push(r);});
    $('#l1sumblock').innerHTML='<div class="note">shape (structural, IS-selected '
     +'cell, 5-bar dwell) &times; activity (nine-box scale tercile) = '
     +'<b>combined</b>, twelve states, with <b>settling</b> as a graded weight. '
     +'The nine-box is unchanged and still primary. Every claim below sits next '
     +'to the test that was run on it.</div>'
     +Object.keys(grp).map(a=>'<div class="tw"><table><thead><tr><th>'+a
      +'</th><th>Statistic</th><th>Null</th><th>Verdict</th></tr></thead><tbody>'
      +grp[a].map(r=>'<tr><td>'+r.claim+'</td><td>'+r.statistic+'</td><td>'
       +r.null+'</td><td>'+(String(r.verdict).indexOf('HOLDS')===0
        ?'<b>'+r.verdict+'</b>':r.verdict)+'</td></tr>').join('')
      +'</tbody></table></div>').join('')
     +'<div class="note"><b>What to route on.</b> <code>activity</code> / '
     +'<code>scale_28</code> &mdash; the only axis whose separation survives a '
     +'surrogate, and only against IID. <code>shape</code> and '
     +'<code>combined</code> are orthogonal to it and to the nine-box '
     +'straightness family, so not redundant, but they fail their own nulls, so '
     +'not informative either. <code>settling</code> is a weight, not a state. '
     +'<code>tier</code> is description only.</div>';
   }
   const CC=BUN.chgcount||[],CTk=BUN.chgtrack||[],FS=BUN.fswing||[],FC=BUN.fswingc||[];
   const f3=(v,n)=>v==null||v===''?'&mdash;':(+v).toFixed(n==null?3:n);
   if(CC.length){
    let h='<div class="note"><b>Activity is not a side question.</b> The same '
     +'shape at high activity is a trend; at low activity it is a drift. So a '
     +'move from <i>weak broken</i> to <i>strong broken</i> is a regime change '
     +'even though the shape word did not move. No volume data exists for FX '
     +'&mdash; H.10 is close-only and the market is decentralised &mdash; so '
     +'distance travelled is the proxy.</div>'
     +'<div class="tw"><table><thead><tr><th>Kind</th><th>Changes</th>'
     +'<th>Rate</th><th>Mean gap</th></tr></thead><tbody>'
     +CC.map(r=>'<tr><td>'+r.kind+'</td><td>'+r.changes+'</td><td>'
      +f3(100*r.rate,3)+'%</td><td>'+f3(r.mean_gap,1)+' bars</td></tr>').join('')
     +'</tbody></table><div class="count">Shape and activity change at almost '
     +'exactly the same rate &mdash; 48.9% / 49.0% of the split-join total &mdash; '
     +'and independently: both-on-the-same-bar is 132 against 143 expected by '
     +'chance, ratio 0.92. Activity carries half the regime changes.</div></div>';
    if(CTk.length) h+='<div class="tw"><table><thead><tr><th>Signal</th>'
     +'<th>Change type</th><th>n</th><th>Lift</th><th>Surrogate</th>'
     +'<th>Excess</th><th>p</th></tr></thead><tbody>'
     +CTk.filter(r=>r.kind!=='both').map(r=>'<tr><td>'+r.family+' '+r.fast+'/'
      +r.slow+'</td><td>'+r.kind+'</td><td>'+r.n+'</td><td>'+f3(r.lift)
      +'</td><td>'+f3(r.surrogate)+'</td><td><b>'+(r.excess>0?'+':'')
      +f3(r.excess)+'</b></td><td>'+f3(r.p)+'</td></tr>').join('')
     +'</tbody></table><div class="count"><b>The signals split by axis.</b> '
     +'mas 5/8 tracks shape (+0.183, p=0.024) and not activity (&minus;0.007, '
     +'p=0.634); vol 8/200 tracks activity (+0.349, p=0.024) and not shape '
     +'(&minus;0.076, p=0.780). A moving-average signal reads shape, a '
     +'volatility-ratio signal reads activity &mdash; which is what their '
     +'construction says they should do, and is worth knowing before either is '
     +'read as tracking &ldquo;the state&rdquo;. <i>both</i> is omitted here: '
     +'132 events is too few to read.</div></div>';
    $('#chgblock').innerHTML=h;
   }
   if(FS.length){
    const XS=[0.85,0.90,0.93,0.95,0.97,0.98,0.99],YS=[0.5,0.75,1,1.5,2,3,4];
    const sel=FS.filter(r=>r.kind==='shape only');
    const cel=(x,y)=>sel.find(r=>Math.abs(r.X-x)<1e-9&&Math.abs(r.Y-y)<1e-9);
    let h='<div class="note"><b>Within-window only.</b> A bar counts as a '
     +'rejection on what already happened: price came within X of the prior '
     +'extreme without clearing it, and has since turned back by Y multiples of '
     +'the recent daily range. The no-clearing clause matters &mdash; without it '
     +'every successful breakout fires too and X stops meaning anything.</div>'
     +'<div class="tw"><table><thead><tr><th>IS excess, shape changes<br>'
     +'<span class="count">X &darr; Y &rarr;</span></th>'
     +YS.map(y=>'<th>'+y+'</th>').join('')+'</tr></thead><tbody>'
     +XS.map(x=>'<tr><td><b>'+x+'</b></td>'+YS.map(y=>{const c=cel(x,y);
       return '<td>'+(c?((c.is_excess>0.10?'<b>':'')+(c.is_excess>0?'+':'')
        +f3(c.is_excess)+(c.is_excess>0.10?'</b>':'')):'&middot;')+'</td>';})
      .join('')+'</tr>').join('')+'</tbody></table>'
     +'<div class="count">34 of 49 cells clear +0.05 on IS, 33 of them '
     +'contiguous &mdash; a genuine broad plateau across X = 0.93&ndash;0.99, '
     +'which is what was set as the bar.</div></div>';
    if(FC.length) h+='<div class="tw"><table><thead><tr><th>Cell</th>'
     +'<th>IS excess</th><th>Holdout lift</th><th>Surrogate</th>'
     +'<th>Holdout excess</th><th>p</th></tr></thead><tbody>'
     +FC.map(r=>'<tr><td>X='+r.X+' Y='+r.Y+' &middot; '+r.kind+' &middot; '
      +r.null+'</td><td>'+(r.is_excess>0?'+':'')+f3(r.is_excess)+'</td><td>'
      +f3(r.holdout_lift)+'</td><td>'+f3(r.surrogate)+' &plusmn; '+f3(r.sd)
      +'</td><td><b>'+(r.excess>0?'+':'')+f3(r.excess)+'</b></td><td>'+f3(r.p)
      +'</td></tr>').join('')+'</tbody></table><div class="count">The plateau '
     +'does not survive. Selection was restricted to <b>interior</b> cells: a '
     +'3&times;3 mean alone is not enough, because a corner has only three '
     +'neighbours and a lone spike at the grid edge survives smoothing &mdash; '
     +'which is exactly what happened first time, where X=0.99 Y=4.00 won on '
     +'both criteria while firing on 0.128% of bars, the sparsest cell in the '
     +'sweep.</div></div>';
    $('#fswblock').innerHTML=h;
   }
   const S3=BUN.shape3cov||[],LB=BUN.shape3lb||[],ON=BUN.oldnew||[];
   const f4=(v,n)=>v==null||v===''?'&mdash;':(+v).toFixed(n==null?3:n);
   if(S3.length){
    let h='<div class="note"><b>The fourth shape was never in the spec.</b> '
     +'&ldquo;broken&rdquo; took 64% of days while trending took 2.9%, so the '
     +'classifier mostly reported a diagnostic rather than a regime. Replaced by '
     +'a partition: inside the confirmed swing band is <b>range</b>; outside it '
     +'is <b>trending</b> if the swing sequence supports the break and '
     +'<b>drifting</b> if it does not. Every bar labelled exactly once, 3 &times; '
     +'3 = 9 states.</div>'
     +'<div class="tw"><table><thead><tr><th>Mode</th><th>N</th>'
     +'<th>trending</th><th>range</th><th>drifting</th><th>Balance</th></tr>'
     +'</thead><tbody>'+S3.map(r=>'<tr><td>'+r.mode+'</td><td>'+r.N+'</td><td>'
      +f4(r.trending)+'</td><td>'+f4(r.range_)+'</td><td>'+f4(r.drifting)
      +'</td><td>'+f4(r.balance)+'</td></tr>').join('')+'</tbody></table>'
     +'<div class="count">Balance is entropy over the three states, IS only. '
     +'The raw winner is <i>breakonly</i> N=3 at 0.936 &mdash; <b>rejected</b>: '
     +'it drops the swing sequence, so &ldquo;trending&rdquo; would mean only '
     +'&ldquo;a break happened&rdquo;, and the whole point of the structural '
     +'read is that higher highs alone is not a trend. Not traded away for 0.013 '
     +'of entropy. Shipped: <b>relaxed, N=5</b> &mdash; trending goes from 2.6% '
     +'to 17.8% of holdout bars.</div></div>';
    if(LB.length) h+='<div class="note"><b>Shape has no fixed window.</b> The '
     +'nine-box reads 7 / 28 / 128 bars. The shape read is event-driven: its '
     +'memory runs back to the second-most-recent confirmed swing, whose '
     +'distance moves with the market. Measured, not asserted:</div>'
     +'<div class="tw"><table><thead><tr><th>Swing width N</th><th>p10</th>'
     +'<th>median</th><th>mean</th><th>p90</th><th>p99</th></tr></thead><tbody>'
     +LB.map(r=>'<tr><td>'+r.N+'</td><td>'+f4(r.p10,0)+'</td><td><b>'
      +f4(r.median,0)+'</b></td><td>'+f4(r.mean,1)+'</td><td>'+f4(r.p90,0)
      +'</td><td>'+f4(r.p99,0)+'</td></tr>').join('')+'</tbody></table>'
     +'<div class="count">Bars back to the anchoring swing. <b>N is the horizon '
     +'knob</b> &mdash; the direct analogue of the ribbon&rsquo;s windows. For a '
     +'daily entry held for weeks, N=5 (median 35 bars, p90 52) is the closest '
     +'match to the 28-day ribbon leg; N=2 is the fast leg, N=8&ndash;13 the '
     +'slow one. Running three N values side by side would reproduce the ribbon '
     +'on the shape axis &mdash; a build decision, not a finding.</div></div>';
    $('#shape3block').innerHTML=h;
   }
   if(ON.length){
    $('#oldnewblock').innerHTML='<div class="note">Every classifier carries the '
     +'same 5-bar dwell, including the nine-box: persistence drives separation '
     +'on autocorrelated properties, so comparing a dwelled classifier with an '
     +'undwelled one measures the dwell. The nine-box as shipped is listed too. '
     +'<b>Corrected</b> is the only cross-classifier column that means anything '
     +'&mdash; raw separation is not comparable across state counts.</div>'
     +'<div class="tw"><table><thead><tr><th>Classifier</th><th>States</th>'
     +'<th>Median run</th><th>Min share</th><th>Refit</th>'
     +'<th>Shape (raw)</th><th>Activity (raw)</th>'
     +'<th>Shape corr (sign / iid)</th><th>Activity corr (sign / iid)</th>'
     +'</tr></thead><tbody>'+ON.map(r=>'<tr><td>'+r.classifier+'</td><td>'
      +r.n_states+'</td><td>'+f4(r.median_run,0)+'</td><td>'+f4(r.min_share)
      +'</td><td>'+f4(r.refit,1)+'%</td><td>'+f4(r.shape)+'</td><td>'
      +f4(r.activity)+'</td><td><b>'+(r.corr_shape_sign>0?'+':'')
      +f4(r.corr_shape_sign)+'</b> / <b>'+(r.corr_shape_iid>0?'+':'')
      +f4(r.corr_shape_iid)+'</b></td><td>'+(r.corr_act_sign>0?'+':'')
      +f4(r.corr_act_sign)+' / '+(r.corr_act_iid>0?'+':'')+f4(r.corr_act_iid)
      +'</td></tr>').join('')+'</tbody></table>'
     +'<div class="count"><b>The new nine-state is the first classifier in this '
     +'project with a positive corrected shape separation</b> (+0.026 sign, '
     +'+0.037 iid) &mdash; the old nine-box is &minus;0.108 / &minus;0.081. But '
     +'it does not beat its own components: activity alone scores +0.037 on the '
     +'same shape properties, and shape3 alone scores &minus;0.011. The merge is '
     +'about the max of its parts, not more than them.</div></div>';
   }
   const SW=BUN.shapewin||[],SWC=BUN.shapewinc||[];
   const f5=(v,n)=>v==null||v===''?'&mdash;':(+v).toFixed(n==null?3:n);
   if(SW.length){
    const a=SW[0],b=SW[SW.length-1];
    let h='<div class="note"><b>A bounded lookback window does nothing.</b> '
     +'Capping swing history at L bars and sweeping L from 28 to 200 moves the '
     +'shares by under 0.001 past L=40 &mdash; the sequence rule consults only '
     +'the <i>last two</i> confirmed swings per side, and at a narrow swing width '
     +'those sit ~12 bars apart, so a 200-bar cap and a 40-bar cap see the same '
     +'pair. The horizon knob is the <b>swing width</b>, and because it is an '
     +'integer the lookback is <b>quantised</b>: 12, 18, 24, 29, 35, 41&hellip; '
     +'bars, not every integer day.</div>'
     +'<div class="tw"><table><thead><tr><th>N</th><th>Lookback</th>'
     +'<th>trending</th><th>range</th><th>drifting</th><th>Residual</th>'
     +'<th>Separation</th><th>Corrected</th><th>Median run</th><th>Diagonal</th>'
     +'<th>Range runs</th></tr></thead><tbody>'
     +SW.map(r=>'<tr><td>'+r.N+'</td><td>'+f5(r.lookback,0)+'</td><td>'
      +f5(r.trending)+'</td><td>'+f5(r.range)+'</td><td>'+f5(r.drifting)
      +'</td><td>'+f5(r.residual)+'</td><td>'+f5(r.sep)+'</td><td>'
      +(r.corr>0?'+':'')+f5(r.corr)+'</td><td>'+f5(r.median_run,0)+'</td><td>'
      +f5(r.diagonal)+'</td><td>'+f5(r.run_range,0)+'</td></tr>').join('')
     +'</tbody></table><div class="count">In-sample. Corrected = separation minus '
     +'its own surrogate at the same window.</div></div>'
     +'<div class="note"><b>Does chop improve, shrink or hold while trend '
     +'grows?</b> Over the full sweep trending <b>grows</b> '+f5(a.trending)
     +' &rarr; '+f5(b.trending)+', drifting <b>shrinks</b> '+f5(a.drifting)
     +' &rarr; '+f5(b.drifting)+', and range <b>holds steady</b> '+f5(a.range)
     +' &rarr; '+f5(b.range)+'. But range <i>episodes</i> lengthen '
     +f5(b.run_range/a.run_range,1)+'&times;, '+f5(a.run_range,0)+' &rarr; '
     +f5(b.run_range,0)+' bars. The long window does not find MORE chop &mdash; '
     +'it finds the SAME chop in longer, readable episodes, which is exactly the '
     +'three-month-range-versus-one-month distinction. Trending grows and '
     +'drifting is what it takes from.</div>';
    if(SWC.length){const c=SWC[0];
     h+='<div class="note"><b>Chosen on IS: N=6, lookback 35 bars.</b> All nine '
      +'windows meeting the coverage bar (residual &le;2%, every shape &ge;10%) '
      +'have positive corrected separation &mdash; a plateau, not a spike, with '
      +'neighbours +0.006 / +0.015 / <b>+0.020</b> / +0.012 / +0.004 across '
      +'N=4&ndash;8.</div><div class="tw"><table><thead><tr>'
      +'<th>Holdout, read once</th><th>trending</th><th>range</th>'
      +'<th>drifting</th><th>Residual</th><th>Separation</th><th>Surrogate</th>'
      +'<th>Corrected</th><th>p</th></tr></thead><tbody><tr><td>N='+c.N
      +' &middot; '+f5(c.lookback,0)+' bars</td><td>'+f5(c.oos_trending)
      +'</td><td>'+f5(c.oos_range)+'</td><td>'+f5(c.oos_drifting)+'</td><td><b>'
      +f5(c.oos_residual)+'</b></td><td>'+f5(c.oos_sep)+'</td><td>'
      +f5(c.surrogate)+' &plusmn; '+f5(c.sd)+'</td><td><b>'
      +(c.corrected>0?'+':'')+f5(c.corrected)+'</b></td><td>'+f5(c.p)
      +'</td></tr></tbody></table><div class="count"><b>Coverage is fixed; '
      +'separation is not.</b> Zero residual, every shape above 18%, trending at '
      +'18.6% instead of 2.9% &mdash; but the separation still sits below its own '
      +'surrogate on the holdout.</div></div>';}
    $('#swinblock').innerHTML=h;
   }
   const SC=BUN.shapesc||[],SCC=BUN.shapescc||[];
   const f6=(v,n)=>v==null||v===''?'&mdash;':(+v).toFixed(n==null?3:n);
   if(SC.length){
    let h='<div class="note"><b>Option B, shipped.</b> A continuous '
     +'trend-versus-range score cut at IS terciles, so <b>every bar lands '
     +'somewhere</b> &mdash; three shapes, nine states, no residual and no fourth '
     +'category. The structural information is kept as four continuous readings '
     +'rather than four pass/fail gates: <b>seq</b> (swing sequence, signed and '
     +'summed so a higher high with a lower low cancels), <b>bound</b> (distance '
     +'outside or depth inside the confirmed band), <b>hold</b> (break-and-hold), '
     +'<b>pull</b> (1 &minus; retracement). Equal weights, standardised on IS '
     +'&mdash; fitting weights would be a four-parameter search against a target '
     +'that does not exist for a description.</div>'
     +'<div class="tw"><table><thead><tr><th>N</th><th>Lookback</th>'
     +'<th>trending</th><th>drifting</th><th>range</th><th>Separation</th>'
     +'<th>Surrogate</th><th>Corrected</th><th>Median run</th><th>Diagonal</th>'
     +'<th>Pairs +</th></tr></thead><tbody>'
     +SC.filter(r=>[2,4,6,8,13,18,22,26,30,36,40].indexOf(r.N)>=0)
      .map(r=>'<tr><td>'+r.N+'</td><td>'+f6(r.lookback,0)+'</td><td>'
      +f6(r.trending)+'</td><td>'+f6(r.drifting)+'</td><td>'+f6(r.range)
      +'</td><td>'+f6(r.sep)+'</td><td>'+f6(r.surr)+'</td><td><b>'
      +(r.corr>0?'+':'')+f6(r.corr)+'</b></td><td>'+f6(r.median_run,0)
      +'</td><td>'+f6(r.diagonal)+'</td><td>'+r.pairs_pos+'/28</td></tr>')
      .join('')+'</tbody></table><div class="count">In-sample. Corrected = '
     +'separation minus its own surrogate at the same window. <b>17 of 39 '
     +'windows are positive, all of them past N=18</b> &mdash; the short windows '
     +'are uniformly negative and the long ones uniformly positive, which is a '
     +'plateau rather than a spike.</div></div>';
    if(SCC.length){const c=SCC[0];
     h+='<div class="tw"><table><thead><tr><th>Holdout, read once</th>'
      +'<th>trending</th><th>drifting</th><th>range</th><th>Residual</th>'
      +'<th>Separation</th><th>Surrogate</th><th>Corrected</th><th>p</th>'
      +'</tr></thead><tbody><tr><td>N='+c.N+' &middot; '+f6(c.lookback,0)
      +' bars</td><td>'+f6(c.oos_trending)+'</td><td>'+f6(c.oos_drifting)
      +'</td><td>'+f6(c.oos_range)+'</td><td><b>'+f6(c.oos_residual)
      +'</b></td><td>'+f6(c.oos_sep)+'</td><td>'+f6(c.surrogate)+' &plusmn; '
      +f6(c.sd)+'</td><td><b>'+(c.corrected>0?'+':'')+f6(c.corrected)
      +'</b></td><td>'+f6(c.p)+'</td></tr></tbody></table>'
      +'<div class="count"><b>The first positive holdout corrected separation in '
      +'this project</b> &mdash; every gated version was negative. But +0.009 at '
      +'p=0.314 is inside the noise. The sign flipped; the magnitude did not '
      +'arrive.</div></div>';}
    $('#scoreblock').innerHTML=h;
   }
   const SP=BUN.shapesplit||[];
   const f7=(v,n)=>v==null||v===''?'&mdash;':(+v).toFixed(n==null?3:n);
   if(SP.length){
    const SHOW=[2,6,13,18,22,26,30,36,44,52,60,70];
    let h='<div class="note">Every number before this was <b>blended</b> &mdash; '
     +'one figure for the whole classifier, which cannot tell "both trend and '
     +'chop separate" from "trend carries it and chop is dead weight". The metric '
     +'here is <b>one-versus-rest, signed</b>: the state&rsquo;s own mean minus '
     +'every other state&rsquo;s, in sd units. Sweep extended to a 393-bar '
     +'lookback because corrected separation was still climbing at 200.</div>'
     +'<div class="tw"><table><thead><tr><th>N</th><th>Days</th>'
     +'<th colspan="4">Trending</th><th colspan="4">Drifting</th>'
     +'<th colspan="4">Range</th></tr><tr><th></th><th></th>'
     +['Trending','Drifting','Range'].map(()=>'<th>corr</th><th>share</th>'
       +'<th>run</th><th>diag</th>').join('')+'</tr></thead><tbody>'
     +SHOW.map(N=>{const r={};SP.filter(x=>x.N===N).forEach(x=>{r[x.state]=x;});
      if(!r.trending) return '';
      return '<tr><td>'+N+'</td><td>'+f7(r.trending.lookback,0)+'</td>'
       +['trending','drifting','range'].map(s=>'<td><b>'
        +(r[s].corr>0?'+':'')+f7(r[s].corr)+'</b></td><td>'+f7(r[s].share)
        +'</td><td>'+f7(r[s].run,0)+'</td><td>'+f7(r[s].diag)+'</td>').join('')
       +'</tr>';}).join('')+'</tbody></table>'
     +'<div class="count"><b>Trend and chop want different windows.</b> Trending '
     +'corrected turns positive only past a 200-bar lookback and peaks at +0.058 '
     +'near 309 bars; range is positive only in the 100&ndash;190 bar band and '
     +'goes negative beyond it. Drifting &mdash; the middle tercile &mdash; never '
     +'exceeds 0.10 raw at any window: it is the dead weight, and that is what a '
     +'blended number was hiding.</div></div>'
     +'<div class="note"><b>Which property carries each state</b>, at a 144-bar '
     +'lookback, signed: trending is range/path <b>+0.327</b> and mean crossings '
     +'<b>&minus;0.385</b>; range is the mirror, &minus;0.360 and +0.340; '
     +'drifting is +0.055 / +0.014. <b>Autocorrelation carries almost nothing '
     +'for any state</b> (+0.007, &minus;0.037, +0.033) &mdash; the work is done '
     +'by path efficiency and oscillation count, not by serial dependence.</div>'
     +'<div class="note"><b>The tradeoff.</b> Trending run length climbs 18 '
     +'&rarr; 36 bars and its diagonal 0.955 &rarr; 0.986 as the window '
     +'lengthens, so the windows where trend separation is positive are also the '
     +'ones where a trend state lasts seven weeks and changes on 1.4% of bars. '
     +'Range peaks earlier and cheaper: +0.009 at 101&ndash;144 bars with 17&ndash;'
     +'18 bar runs. For an entry held weeks, <b>range is readable at 144 bars '
     +'and trend is not readable until 250+</b>, where it is arguably too slow '
     +'to act on.</div>';
    $('#splitblock').innerHTML=h;
   }
   const SD=BUN.scoredist||[],SY=BUN.scoreyears||[];
   const f8=(v,n)=>v==null||v===''?'&mdash;':(+v).toFixed(n==null?3:n);
   if(SD.length){
    let h='<div class="note"><b>The tercile cut is a design choice, not a '
     +'finding.</b> Four tests, because no single one settles multimodality: KDE '
     +'local maxima across bandwidths, Gaussian-mixture BIC for k=1/2/3, excess '
     +'kurtosis (three separated clusters are <i>platykurtic</i>, one heavy '
     +'spread is <i>leptokurtic</i>), and all three repeated on a sign '
     +'surrogate.</div><div class="tw"><table><thead><tr><th></th><th>n</th>'
     +'<th>sd</th><th>Excess kurtosis</th><th>KDE peaks</th><th>BIC k=1</th>'
     +'<th>k=2</th><th>k=3</th></tr></thead><tbody>'
     +SD.map(r=>'<tr><td>'+r.tag+'</td><td>'+r.n+'</td><td>'+f8(r.sd)+'</td><td>'
      +(r.kurtosis>0?'+':'')+f8(r.kurtosis)+'</td><td>'+r.peaks_min+'&ndash;'
      +r.peaks_max+'</td><td>'+f8(r.bic1,0)+'</td><td>'+f8(r.bic2,0)+'</td><td>'
      +f8(r.bic3,0)+'</td></tr>').join('')+'</tbody></table>'
     +'<div class="count"><b>One spread, not three clusters.</b> A single KDE '
     +'peak at every bandwidth; excess kurtosis <b>+1.44</b>, the wrong sign for '
     +'separated clusters; and although BIC picks k=3, <i>the surrogate picks '
     +'k=3 too</i> &mdash; the extra components are fitting skew and tails, not '
     +'finding groups. The k=2&rarr;k=3 gain is 0.11% against 2.7% for '
     +'k=1&rarr;k=2. The tercile boundaries sit only <b>0.72 sd apart</b>, well '
     +'inside the body of one distribution.</div></div>';
    if(SY.length) h+='<div class="note"><b>But the quota is not what it looked '
     +'like.</b> The cut fits the CDF on in-sample and applies it unchanged, so '
     +'holdout shares are free to float &mdash; and they do, trending running '
     +'from 14.7% to 31.9% across holdout years. It never forces 33/33/33 out of '
     +'sample. A fixed raw-level cut at the same thresholds gives an almost '
     +'identical yearly spread (0.175 vs 0.173 for trending), so the choice '
     +'between them is a level shift, not a change in responsiveness.</div>'
     +'<div class="tw"><table><thead><tr><th>Year</th><th>trending</th>'
     +'<th>drifting</th><th>range</th></tr></thead><tbody>'
     +SY.map(r=>'<tr><td>'+r.year+'</td><td>'+f8(r.quota_trending)+'</td><td>'
      +f8(r.quota_drifting)+'</td><td>'+f8(r.quota_range)+'</td></tr>').join('')
     +'</tbody></table><div class="count">Holdout shares by year under the '
     +'shipped cut. <code>shape_score</code> is now a column in '
     +'layer1_states.csv so the boundary can be moved downstream without '
     +'re-deriving the score.</div></div>';
    $('#distblock').innerHTML=h;
   }
   const FR=BUN.finalrep||[],FP=BUN.finalpairs||[],CCH=BUN.chopcomp||[];
   const f9=(v,n)=>v==null||v===''?'&mdash;':(+v).toFixed(n==null?3:n);
   if(FR.length){
    const row=k=>FR.find(r=>r.item===k)||{};
    const tr=row('trend'),ch=row('chop'),gi=row('grid OOS'),gn=row('grid null');
    let h='<div class="note"><b>Two decisions, both taken on in-sample only.</b> '
     +'Chop drops the <code>tests</code> component (IS |sep| 0.140 &rarr; 0.151). '
     +'Activity is cut <b>jointly</b> with a 0.75 bump, so a weak-activity bar '
     +'must clear a higher trend bar &mdash; but it beats a separate cut by '
     +'<b>0.002</b> on IS, which is a tie, and it costs coverage (min share '
     +'0.049 &rarr; 0.026). Treat them as equivalent.</div>'
     +'<div class="tw"><table><thead><tr><th>Axis</th><th>IS |sep|</th>'
     +'<th>OOS |sep|</th><th>Surrogate</th><th>Corrected</th><th>Share</th>'
     +'<th>Run</th><th>Diagonal</th></tr></thead><tbody>'
     +[['trend',tr],['chop',ch]].map(([n,r])=>'<tr><td>'+n+'</td><td>'
      +f9(r.is_sep)+'</td><td>'+f9(r.oos_sep)+'</td><td>'+f9(r.surrogate)
      +'</td><td><b>'+(r.corrected>0?'+':'')+f9(r.corrected)+'</b></td><td>'
      +f9(r.hi_share)+'</td><td>'+f9(r.hi_run,0)+'</td><td>'+f9(r.hi_diag)
      +'</td></tr>').join('')+'</tbody></table>'
     +'<div class="count"><b>Chop is the stronger axis and the only one that '
     +'holds up out of sample</b> &mdash; 0.151 &rarr; 0.156, corrected '
     +'&minus;0.011. Trend halves, 0.106 &rarr; 0.053, corrected &minus;0.044. '
     +'Neither clears its surrogate.</div></div>'
     +'<div class="note"><b>The full grid</b>, 12 cells: OOS mean |sep| '
     +f9(gi.oos_sep)+', coverage <b>'+f9(gi.coverage)+'</b>, min share '
     +f9(gi.min_share)+', median run '+f9(gi.median_run,0)+' bars, diagonal '
     +f9(gi.diagonal)+'. Against its surrogate: '+f9(gn.oos_sep)+' vs '
     +f9(gn.surrogate)+', corrected <b>'+(gn.corrected>0?'+':'')
     +f9(gn.corrected)+'</b>. Significance is surrogate randomisation '
     +'throughout &mdash; 74,004 holdout bars are only 4,604 episodes, so no '
     +'per-bar t-statistic appears anywhere in this report.</div>';
    if(FP.length){
     const byax=a=>FP.filter(r=>r.axis===a).slice().sort((x,y)=>y.sep-x.sep);
     h+='<div class="tw"><table><thead><tr><th>Pair</th><th>Trend |sep|</th>'
      +'<th>Pair</th><th>Chop |sep|</th></tr></thead><tbody>'
      +(function(){const t=byax('trend'),c=byax('chop');let o='';
        for(let i=0;i<Math.max(t.length,c.length);i++){
         o+='<tr><td>'+(t[i]?t[i].pair:'')+'</td><td>'+(t[i]?f9(t[i].sep):'')
          +'</td><td>'+(c[i]?c[i].pair:'')+'</td><td>'+(c[i]?f9(c[i].sep):'')
          +'</td></tr>';}
        return o;})()
      +'</tbody></table><div class="count">Per pair, holdout, the two axes '
      +'reported separately and never blended. Trend median 0.118 (CADJPY 0.059 '
      +'to GBPCAD 0.283); chop median 0.195 (CHFJPY 0.048 to EURJPY 0.478).'
      +'</div></div>';}
    if(CCH.length) h+='<div class="tw"><table><thead><tr><th>Chop component</th>'
     +'<th>Real</th><th>Surrogate</th><th>Corrected</th></tr></thead><tbody>'
     +CCH.map(r=>'<tr><td>'+r.component+'</td><td>'+f9(r.real)+'</td><td>'
      +f9(r.surrogate)+'</td><td>'+(r.corrected>0?'+':'')+f9(r.corrected)
      +'</td></tr>').join('')+'</tbody></table><div class="count">The three '
     +'components added for redundancy. Adding all three made chop <i>worse</i> '
     +'(0.124 &rarr; 0.082): <code>vr_short</code> separates better alone than '
     +'the whole score but is uncorrelated with it, so summing dilutes; '
     +'<code>hold_ratio</code> is 0.699 correlated with what was already there. '
     +'Only <code>width_stab</code> clears its own surrogate.</div></div>';
    $('#finalblock').innerHTML=h;
   }
   if(RS.length){
    const W=640,H=170,PL=40;
    const bands=['fast','medium','slow'];let g='';
    bands.forEach((b,bi)=>{
     const d=RS.filter(r=>r.band===b);if(!d.length)return;
     const x0=PL+bi*((W-PL)/3),w=(W-PL)/3-26;
     const lg=d.map(r=>r.lag),ch=d.map(r=>r.churn);
     const lmax=Math.max(...lg),cmax=Math.max(...ch);
     const best=d.reduce((a,c)=>c.cost<a.cost?c:a,d[0]);
     d.forEach((r,i)=>{const x=x0+i*(w/Math.max(d.length-1,1));
      g+=`<circle cx="${x}" cy="${20+(1-r.lag/lmax)*50}" r="2.5" fill="#5b8dd9"/>`
       +`<circle cx="${x}" cy="${90+(1-r.churn/cmax)*50}" r="2.5" fill="#d9a441"/>`
       +(r.L===best.L?`<line x1="${x}" y1="14" x2="${x}" y2="146"
          stroke="var(--trend)" stroke-width="1.4" stroke-dasharray="3 2"/>`:'');});
     g+=txt(x0+w/2,162,b+' — chose '+best.L,{a:'middle',s:10,c:'var(--trend)'});});
    g+=txt(4,26,'lag',{s:9,c:'#5b8dd9'})+txt(4,96,'churn',{s:9,c:'#d9a441'});
    $('#ribcurve').innerHTML=`<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg">${g}</svg>`
     +'<div class="note">Both curves are normalised within their band; the dashed line is'
     +' the length minimising normalised lag plus normalised churn. <b>The slow band'
     +' starts at 62, not 60</b> — at a 60-bar window the scale axis collapses toward'
     +' &radic;(2/&pi;) because it equals the volatility normalisation span, and its'
     +' artificially low churn would have read as the best slow window.</div>';
   }
  })();

  // ---- validation tab ----
  (function(){const SUM=BUN.val_summary||[];if(!SUM.length)return;
   const NAME={shuffled_labels:'Shuffled labels',synthetic:'Synthetic truth',
               refit_stability:'Refit stability',persistence:'Persistence'};
   $('#valcards').innerHTML=SUM.map(d=>{
    const ok=d.passes===true||d.passes==='True';
    return `<div class="panel" style="flex:1;min-width:170px;border-left:3px solid
     ${ok?'var(--trend)':'var(--kill)'}">
     <div class="big" style="color:${ok?'var(--trend)':'var(--kill)'}">${ok?'PASS':'FAIL'}</div>
     <span class="count">${NAME[d.test]||d.test}</span></div>`;}).join('');
   const S=(BUN.val_shuffle||[])[0];
   if(S)$('#valshuf').innerHTML=`<div class="note">Real trend-minus-chop efficiency gap
    <b>${S.real>0?'+':''}${S.real.toFixed(5)}</b>. Shuffled null: mean
    ${S.null_mean>0?'+':''}${S.null_mean.toFixed(5)}, sd ${S.null_std.toFixed(5)},
    95th percentile ${S.null_p95>0?'+':''}${S.null_p95.toFixed(5)} over
    ${S.n_shuffles} shuffles. The real labels sit at the
    <b>${(S.percentile*100).toFixed(1)}%</b> percentile of the null,
    <b>z = ${S.z>0?'+':''}${S.z.toFixed(2)}</b>.</div>`;
   const Y=(BUN.val_synth||[])[0];
   $('#valsynth').innerHTML=Y?`<div class="note">On regimes we defined:
    accuracy <b>${(Y.accuracy*100).toFixed(1)}%</b>, precision
    <b>${(Y.precision*100).toFixed(1)}%</b>, recall <b>${(Y.recall*100).toFixed(1)}%</b>,
    median detection lag <b>${Y.median_lag_days} days</b> across ${Y.n_pairs} pairs.</div>`
    :'<div class="note">Not run in this build (rebuilds the composite; run with FX_FULL_VALIDATION).</div>';
   const RF=(BUN.val_refit||[])[0];
   $('#valrefit').innerHTML=RF?`<div class="note" style="border-left:3px solid var(--kill)">
    <b>SUPERSEDED &mdash; kept for the record, do not read this as the refit result.</b>
    The 100.0% below is an artefact: the cut points were built by ranking over the whole
    sample, so refitting changed nothing because <b>nothing was actually being fitted</b>.
    That look-ahead is fixed. The real refit test is on the
    <b>States and validation</b> screen: five independent refits of generation 4, and the
    answer is <b>94&ndash;96%</b>, not 100%.</div>
    <div class="note" style="opacity:.7">${RF.year} labels identical after
    refitting through 2020: <b>${(RF.label_agreement*100).toFixed(1)}%</b> of days across
    ${RF.n_pairs} pairs.<br><b>Limitation:</b> this refits the composite only. The 32
    survivors were selected by gates that read out-of-sample statistics, so the choice of
    which signals to combine already knows about 2016\u20132026. That is a larger
    look-ahead than this test measures.</div>`
    :'<div class="note">Not run in this build (rebuilds the composite twice).</div>';
   const P=BUN.val_persist||[];
   if(P.length)$('#valpers').innerHTML='<div class="tw"><table><thead><tr>'
    +'<th>Regime</th><th>Runs</th><th>Median len</th><th>Mean len</th>'
    +'<th>% runs &lt;5d</th><th>% bars &lt;5d</th><th>Diagonal</th></tr></thead><tbody>'
    +P.map(d=>`<tr><td>${d.regime}</td><td>${d.n_runs}</td>
      <td>${d.median_len.toFixed(1)}</td><td>${d.mean_len.toFixed(1)}</td>
      <td>${(d.share_runs_under_5*100).toFixed(1)}%</td>
      <td><b>${(d.share_bars_under_5*100).toFixed(1)}%</b></td>
      <td>${d.diagonal.toFixed(3)}</td></tr>`).join('')+'</tbody></table></div>';
   const TR=BUN.val_trans||[];
   if(TR.length)$('#valtr tbody').innerHTML=TR.map(r=>{
    const k=Object.keys(r)[0];
    return `<tr><td><b>${r[k]}</b></td><td>${(+r.chop).toFixed(3)}</td>
     <td>${(+r.mid).toFixed(3)}</td><td>${(+r.trend).toFixed(3)}</td></tr>`;}).join('');
  })();

  // ---- selection-inflation tab ----
  (function(){const A=BUN.infl||[],SM=BUN.inflsum||[],FM=BUN.inflfam||[];
   if(!A.length)return;
   const by=m=>SM.find(d=>d.metric===m)||{};
   const f4=v=>v==null?'—':(+v).toFixed(4);
   const NS=by('n_survivors'),BE=by('best_effect'),EM=by('runs_empty');
   const card=(ok,head,sub)=>`<div class="panel" style="flex:1;min-width:210px;
     border-left:3px solid ${ok?'var(--trend)':'var(--kill)'}">
     <div class="big" style="color:${ok?'var(--trend)':'var(--kill)'}">${head}</div>
     <span class="count">${sub}</span></div>`;
   $('#inflcards').innerHTML=
    card(NS.p_emp!=null&&NS.p_emp<=.05,'p = '+(NS.p_emp==null?'—':NS.p_emp.toFixed(3)),
      `<b>How many survive.</b> Real ${NS.real} against a null median of
       ${NS.null_med}, worst case ${NS.null_max}. The gauntlet does not manufacture
       a set this deep from noise.`)
   +card(BE.p_emp!=null&&BE.p_emp<=.05,'p = '+(BE.p_emp==null?'—':BE.p_emp.toFixed(3)),
      `<b>How big the best one looks.</b> Real ${f4(BE.real)} against ${f4(BE.null_med)}
       manufactured. The single strongest signal is <b>not</b> distinguishable from
       what selection invents.`)
   +card(true,(EM.null_max==null?'—':EM.null_max)+' of 50',
      `<b>Null runs that produced nothing at all.</b> The other ${50-(EM.null_max||0)}
       produced at least one survivor from a target with no signal in it.`);
   $('#infltab tbody').innerHTML=A.map(r=>{
    const hit=r.p_emp!=null&&r.p_emp<=.05;
    return `<tr><td><b>${r.rank}</b></td><td>${f4(r.real_eff)}</td>
     <td>${f4(r.null_med_fired)}</td><td><b>${f4(r.adjusted)}</b></td>
     <td>${r.manufactured_pct==null?'—':r.manufactured_pct.toFixed(0)+'%'}</td>
     <td style="color:${hit?'var(--trend)':'var(--kill)'}">${r.p_emp==null?'—'
       :r.p_emp.toFixed(3)}</td>
     <td${r.n_runs_reaching<10?' style="color:var(--dim)"':''}>${r.n_runs_reaching}</td>
     </tr>`;}).join('');
   $('#inflfam tbody').innerHTML=FM.map(r=>`<tr><td>${r.family}</td>
     <td>${r.n_built.toLocaleString()}</td><td>${r.built_share.toFixed(1)}%</td>
     <td>${r.real_survivors}</td><td><b>${r.real_share.toFixed(1)}%</b></td>
     <td>${r.null_survivors}</td><td><b>${r.null_share.toFixed(1)}%</b></td></tr>`).join('');
   const top=FM.slice().sort((a,b)=>b.null_share-a.null_share)[0];
   $('#infltx').innerHTML=top?`<b>What this says.</b> The depth of the survivor set is real
    &mdash; 50 runs against a signal-free target never got past ${NS.null_max}, so
    ${NS.real} is not luck. The size of any individual effect is largely not:
    ${A[0].manufactured_pct==null?'':'about '+A[0].manufactured_pct.toFixed(0)
    +'% of the top signal’s headline spread is what the procedure manufactures '
    +'from noise, leaving '+f4(A[0].adjusted)+' after correction. '}And the family mix is no
    evidence either &mdash; <b>${top.family}</b> takes ${top.null_share.toFixed(0)}% of null
    survivors against ${top.built_share.toFixed(0)}% of everything built, so its dominance
    among the real survivors is what noise alone produces at that population size.`:'';
  })();

  // ---- external data tab ----
  (function(){const R=BUN.extret||[],C=BUN.extcov||[],T=BUN.exttr||[];
   if(!R.length)return;
   const pct=v=>(v*100).toFixed(1)+'%';
   const base=R.find(d=>/FX price/.test(d.group)),all=R.find(d=>d.group==='ALL EXTERNAL');
   const xs=R.find(d=>/cross-sectional/.test(d.group));
   const card=(ok,head,sub)=>`<div class="panel" style="flex:1;min-width:220px;
     border-left:3px solid ${ok?'var(--trend)':'var(--kill)'}">
     <div class="big" style="color:${ok?'var(--trend)':'var(--kill)'}">${head}</div>
     <span class="count">${sub}</span></div>`;
   if(all&&base)$('#excards').innerHTML=
     card(all.retention>base.retention,pct(all.retention),
       `<b>External data, all ${all.n} signals.</b> Against ${pct(base.retention)} for FX
        price and ${xs?pct(xs.retention):'—'} for FX cross-sectional.`)
    +card(false,'0 of '+all.n,
       `<b>Through the gauntlet.</b> Nothing external clears the seven gates. At this
        sample size that is expected, not a verdict.`)
    +card(T.length&&T.filter(d=>d.transferred).length===T.length,
       T.filter(d=>d.transferred).length+' of '+T.length,
       `<b>Constructions that transfer.</b> The rest read a currency pair's two legs and
        have nothing to compute on a single external series.`);
   $('#extab tbody').innerHTML=R.map(r=>{
    const hd=/^\(|ALL EXTERNAL/.test(r.group), up=r.vs_price_baseline>0;
    return `<tr${hd?' style="opacity:.75"':''}><td>${hd?'<i>'+r.group+'</i>':r.group}</td>
     <td>${r.n.toLocaleString()}</td><td><b>${pct(r.retention)}</b></td>
     <td style="color:${up?'var(--trend)':'var(--kill)'}">${
       (r.vs_price_baseline>0?'+':'')+(r.vs_price_baseline*100).toFixed(1)}pp</td></tr>`;
   }).join('');
   const nt=T.filter(d=>!d.transferred);
   $('#extr').innerHTML='<div class="note">'+(nt.length
     ? `<b>${nt.length} of ${T.length} did not transfer:</b> `
       +nt.map(d=>'<code>'+d.signal+'</code>').join(', ')
     : 'All '+T.length+' transferred.')+'</div>';
   $('#excov tbody').innerHTML=C.filter(d=>d.ok===true||d.ok==='True').map(d=>
    `<tr><td>${d.series}</td><td>${d.source}</td><td>${d.group}</td><td>${d.first}</td>
     <td>${d.coverage_on_px28==null?'—':pct(d.coverage_on_px28)}</td></tr>`).join('');
   // ---- carry / rate differentials ----
   const CR=BUN.carryret||[],RC=BUN.ratecov||[],CS=BUN.carrysig||[];
   const cbase=CR.find(d=>/FX price/.test(d.group));
   if(CR.length)$('#cartab tbody').innerHTML=CR.map(r=>{
    const hd=/^\(/.test(r.group),up=r.vs_price_baseline>0;
    return `<tr${hd?' style="opacity:.75"':''}><td>${hd?'<i>'+r.group+'</i>':r.group}</td>
     <td>${r.n.toLocaleString()}</td><td><b>${r.retention==null?'—':pct(r.retention)}</b></td>
     <td style="color:${up?'var(--trend)':'var(--kill)'}">${r.vs_price_baseline==null?'—'
       :(r.vs_price_baseline>0?'+':'')+(r.vs_price_baseline*100).toFixed(1)+'pp'}</td></tr>`;
   }).join('');
   const kc=CR.find(d=>/surviving constructions/.test(d.group));
   if(kc)$('#carnote').innerHTML=`<div class="note"><b>The constructions do not transfer to
    carry.</b> ${pct(kc.retention)} of ${kc.n} keep their sign out of sample &mdash; a coin
    flip, and ${Math.abs(kc.vs_price_baseline*100).toFixed(1)}pp below FX price. Nothing
    clears the gauntlet. Note what the target is: forward efficiency is
    <b>|net|&divide;path</b>, a trend-versus-chop measure carrying no direction at all,
    while carry is a directional return phenomenon. This says the shapes that read trend in
    price do not read trend in rate differentials &mdash; it does not say carry is
    uninformative about returns, which is a question this project does not ask.</div>`;
   if(RC.length)$('#ratecov tbody').innerHTML=RC.map(r=>
    `<tr${(r.ok===true||r.ok==='True')?'':' style="opacity:.5"'}><td><b>${r.currency}</b></td>
     <td>${r.source}</td><td>${(r.n||0).toLocaleString()}</td><td>${r.first||'—'}</td>
     <td>${r.last||'—'}</td>
     <td>${r.coverage_on_px28==null?'—':pct(r.coverage_on_px28)}</td></tr>`).join('');
   const miss=C.filter(d=>!(d.ok===true||d.ok==='True'));
   $('#extx').innerHTML=(miss.length?`<b>${miss.length} series unavailable in this build</b>
     &mdash; ${miss.map(d=>d.series).join(', ')}. `:'')
    +`<b>Do not over-read the source rows.</b> Most of the surviving constructions turn out
      to be panel-wide on the external universe, so they contribute one signal each rather
      than one per series; the per-source rows rest on only a handful of distinct
      constructions repeated across correlated series. The effective sample is far smaller
      than the n column suggests.`;
  })();

  // ---- pair trendiness ----
  (function(){const P=BUN.pairtrend||[],AG=BUN.agreepairs||[];
   if(!P.length)return;
   const MAJ=new Set(['EURUSD','GBPUSD','AUDUSD','NZDUSD','USDCAD','USDCHF','USDJPY']);
   const f4=v=>v==null?'—':(+v).toFixed(4);
   const rk=(a,b)=>{const r=x=>x.map((_,i)=>i);const ia=a.map((v,i)=>[v,i]).sort((x,y)=>x[0]-y[0]),
     ib=b.map((v,i)=>[v,i]).sort((x,y)=>x[0]-y[0]);
    const ra=[],rb=[];ia.forEach(([,i],k)=>ra[i]=k);ib.forEach(([,i],k)=>rb[i]=k);
    const n=a.length,m=(n-1)/2;let sx=0,sy=0,sxy=0;
    for(let i=0;i<n;i++){sx+=(ra[i]-m)**2;sy+=(rb[i]-m)**2;sxy+=(ra[i]-m)*(rb[i]-m);}
    return sxy/Math.sqrt(sx*sy);};
   const rho=rk(P.map(d=>d.eff_is),P.map(d=>d.eff_oos));
   const mj=P.filter(d=>MAJ.has(d.pair)),cr=P.filter(d=>!MAJ.has(d.pair));
   const avg=a=>a.reduce((s,d)=>s+d.eff_both,0)/a.length;
   const card=(h,s)=>`<div class="panel" style="flex:1;min-width:200px">
     <div class="big">${h}</div><span class="count">${s}</span></div>`;
   $('#ptcards').innerHTML=
     card(rho.toFixed(2),`<b>IS&ndash;OOS rank correlation.</b> The ordering is only
       partly stable: roughly ${Math.round(rho*rho*100)}% of the rank variance carries
       across the split.`)
    +card(f4(avg(mj))+' / '+f4(avg(cr)),`<b>Majors vs crosses.</b> The ranking sorts
       almost entirely by whether the dollar is in the pair.`)
    +card(f4(P[0].eff_both-P[P.length-1].eff_both),`<b>Trendiest minus choppiest.</b>
       Real but modest &mdash; about 13% of the level, on a standard error near 0.0025.`);
   $('#pttab tbody').innerHTML=P.map(d=>{
    const mv=d.rank_move,big=Math.abs(mv)>=8;
    return `<tr><td><b>${d.pair}</b></td>
     <td><span class="count">${MAJ.has(d.pair)?'major':'cross'}</span></td>
     <td>${f4(d.eff_is)}</td><td>${f4(d.eff_oos)}</td>
     <td>${d.rank_is}</td><td>${d.rank_oos}</td>
     <td style="color:${big?(mv>0?'var(--trend)':'var(--kill)'):'inherit'}">${
       mv>0?'+'+mv:mv}</td></tr>`;}).join('');
   if(AG.length){
    const rr=rk(AG.map(d=>d.backing_rate),AG.map(d=>d.eff_both));
    $('#agnote').innerHTML=`<div class="note"><b>No &mdash; the gate is doing its job.</b>
     Across the signals killed only by agreement, the pairs carrying the largest effects
     are no trendier than the pairs where the effect is smallest, and the correlation
     between how often a pair is among a killed signal's strongest and how trendy that
     pair is comes out at <b>${rr.toFixed(3)}</b>. If the gate were deleting real
     trend-concentrated structure this number would be strongly positive. The killed
     signals lean on an arbitrary handful of pairs, which is what noise lining up on a
     subset looks like.</div>`;
    $('#agtab tbody').innerHTML=AG.slice(0,10).map(d=>
     `<tr><td>${d.pair}</td><td>${(d.backing_rate*100).toFixed(0)}% of them</td>
      <td>${f4(d.eff_both)}</td></tr>`).join('');}
   const SN=BUN.subnull||[],SP=BUN.subnullpairs||[];
   if(SN.length){
    $('#sntab tbody').innerHTML=SN.map(r=>{
     const ef=r.real/r.ratio,cont=ef/r.real,cur=Math.abs(r.thresh-0.893)<1e-6;
     return `<tr${cur?' style="font-weight:600"':''}><td>${r.thresh.toFixed(3)}${
       cur?' &larr; current':''}</td><td>${r.pairs_required} of 28</td>
      <td><b>${r.real}</b></td><td>${r.null_med.toFixed(1)}</td><td>${r.null_max}</td>
      <td>${ef.toFixed(1)}</td>
      <td style="color:${cont<.05?'var(--trend)':'var(--kill)'}">${(cont*100).toFixed(1)}%</td>
      </tr>`;}).join('');
    const a=SN.find(d=>Math.abs(d.thresh-0.893)<1e-6),b=SN.find(d=>Math.abs(d.thresh-0.75)<1e-6);
    let pc='';
    if(SP.length){const rr=rk(SP.map(d=>d['real_0.750']),SP.map(d=>d.panel_corr)),
      tt=rk(SP.map(d=>d['real_0.750']),SP.map(d=>d.eff));
     pc=`<br><br><b>And the clustering is not a trend pattern.</b> Which pairs carry the
      subset survivors correlates <b>${rr.toFixed(2)}</b> with how closely that pair's
      forward efficiency tracks the panel's, and <b>${tt.toFixed(2)}</b> with how much the
      pair trends. AUDNZD is the cleanest case: the trendiest pair on the board and one of
      the weakest carriers. The survivor set is overwhelmingly panel-volatility chop
      detectors, so the pairs that carry them are the pairs that move with the panel &mdash;
      a sensitivity effect, not a trend effect.`;}
    if(a&&b)$('#snnote').innerHTML=`<div class="note"><b>The subset survivors are real.</b>
      Relaxing agreement to ${b.pairs_required} of 28 admits <b>${b.real}</b> signals where
      the shifted-target null yields a median of ${b.null_med.toFixed(0)} and never exceeds
      ${b.null_max}. Expected contamination rises from
      ${((a.real/a.ratio)/a.real*100).toFixed(1)}% at the current gate to
      ${((b.real/b.ratio)/b.real*100).toFixed(1)}%, while survivors go from ${a.real} to
      ${b.real}. So there is genuine structure below gate 4 and the price of reaching it is
      a few percent of noise.${pc}</div>`;}
  })();

  // ---- Explorer + States: the nine-state read ----
  (function(){
   // hue = cleanliness (green trend / amber transitional / red chop),
   // darkness = size, so the grid reads as a grid
   const SC={'strong trend':'#1f6b40','medium trend':'#3d9968','weak trend':'#8fc9a6',
    'strong transitional':'#9c6b12','medium transitional':'#d9a441',
    'weak transitional':'#ecd39a',
    'strong chop':'#8f2b3a','medium chop':'#d1495b','weak chop':'#e8a3ac'};
   const RC=['#d1495b','#9aa0a6','#2e9e5b'];
   let EXP=null,PAIR=null,RANGE='full',loading=false,WIN='128',GRP=9;
   const RANGES={full:0,'5y':1260,'1y':252,'90d':90};
   const WINS={'7':'fast 7','28':'medium 28','128':'slow 128','c':'consensus'};
   // consensus: the label at least two of the three windows agree on, else slow.
   // Slow is the fallback rather than medium because it is the one that does not
   // fragment -- see the note under the chart.
   function stateAt(P,i){
    if(WIN!=='c')return P['st'+WIN]?P['st'+WIN][i]:P.st[i];
    const a=P.st7[i],b=P.st28[i],c=P.st128[i];
    if(a===b||a===c)return a; if(b===c)return b; return c;
   }
   function leanAt(P,i){
    const k=WIN==='c'?'128':WIN;return P['ln'+k]?P['ln'+k][i]:null;
   }
   // 9 -> 6: a transitional bar joins trend or chop by which side of the
   // straightness midpoint it sits on. Its SIZE word is unchanged.
   function display(P,i){
    const s=stateAt(P,i); if(s==null)return null;
    const nm=EXP.states[s]; if(GRP===9||nm.indexOf('transitional')<0)return nm;
    const ln=leanAt(P,i); if(ln==null)return nm;
    return nm.split(' ')[0]+(ln?' trend':' chop');
   }

   function load(){
    if(EXP||loading)return;loading=true;
    const url=(BUN.meta&&BUN.meta.explorer_url)||'app_explorer.json';
    $('#pxchart').innerHTML='<div class="note">Loading the per-pair feed'
     +' (about 7 MB)…</div>';
    fetch(url).then(r=>{if(!r.ok)throw new Error('HTTP '+r.status);return r.json();})
     .then(j=>{EXP=j;PAIR=Object.keys(j.pairs)[0];loading=false;draw();})
     .catch(e=>{$('#pxchart').innerHTML='<div class="note" style="color:var(--kill)">'
      +'Could not load '+url+' ('+e.message+').</div>';loading=false;});
   }

   function slice(){
    const P=EXP.pairs[PAIR],n=EXP.dates.length,k=RANGES[RANGE];
    const a=k?Math.max(0,n-k):0;
    const idx=[];const step=Math.max(1,Math.ceil((n-a)/1400));
    for(let i=a;i<n;i+=step)idx.push(i);
    if(idx[idx.length-1]!==n-1)idx.push(n-1);
    return {P,idx};
   }

   function draw(){
    if(!EXP)return;
    $('#pxsel').innerHTML=Object.keys(EXP.pairs).map(p=>
     `<button class="chip" data-p="${p}"${p===PAIR?' aria-pressed="true"':''}
      style="${p===PAIR?'outline:2px solid var(--trend)':''}">${p}</button>`).join('');
    $('#pxsel').querySelectorAll('button').forEach(b=>b.onclick=()=>{
     PAIR=b.dataset.p;draw();});
    $('#pxwin').innerHTML='<span class="count">colour by</span> '
     +Object.keys(WINS).map(w=>`<button class="chip" data-w="${w}"
       style="${w===WIN?'outline:2px solid var(--trend)':''}">${WINS[w]}</button>`).join('')
     +' &nbsp; <span class="count">grouping</span> '
     +[9,6].map(gv=>`<button class="chip" data-g="${gv}"
       style="${gv===GRP?'outline:2px solid var(--trend)':''}">${gv}-state</button>`).join('');
    $('#pxwin').querySelectorAll('[data-w]').forEach(b=>b.onclick=()=>{
     WIN=b.dataset.w;draw();});
    $('#pxwin').querySelectorAll('[data-g]').forEach(b=>b.onclick=()=>{
     GRP=+b.dataset.g;draw();});
    $('#pxrange').innerHTML=Object.keys(RANGES).map(r=>
     `<button class="chip" data-r="${r}"${r===RANGE?' aria-pressed="true"':''}
      style="${r===RANGE?'outline:2px solid var(--trend)':''}">${r}</button>`).join('');
    $('#pxrange').querySelectorAll('button').forEach(b=>b.onclick=()=>{
     RANGE=b.dataset.r;draw();});

    const {P,idx}=slice();
    const W=760,H=300,PL=52,PR=8,PT=10,PB=18;
    const lp=idx.map(i=>P.px[i]==null?null:Math.log(P.px[i]));
    const fin=lp.filter(v=>v!=null);
    if(!fin.length){$('#pxchart').innerHTML='<div class="note">No data.</div>';return;}
    const mn=Math.min(...fin),mx=Math.max(...fin),rg=(mx-mn)||1;
    const X=k=>PL+k*(W-PL-PR)/Math.max(idx.length-1,1);
    const Y=v=>PT+(1-(v-mn)/rg)*(H-PT-PB);
    // one polyline per run of identical state keeps the element count sane
    let g='',cur=null,pts=[];
    const flush=()=>{if(pts.length>1)g+=`<polyline points="${pts.join(' ')}" fill="none"
      stroke="${SC[cur]||'#888'}" stroke-width="1.6"/>`;};
    idx.forEach((i,k)=>{
     if(lp[k]==null)return;
     const s=display(P,i);
     if(s!==cur){flush();pts=pts.length?[pts[pts.length-1]]:[];cur=s;}
     pts.push(X(k).toFixed(1)+','+Y(lp[k]).toFixed(1));});
    flush();
    // split line and crisis events
    const dstr=idx.map(i=>EXP.dates[i]);
    const at=d=>{let k=dstr.findIndex(x=>x>=d);return k<0?null:X(k);};
    const sx=at(EXP.split);
    if(sx!=null)g+=`<line x1="${sx}" y1="${PT}" x2="${sx}" y2="${H-PB}"
      stroke="var(--dim)" stroke-width="1.5" stroke-dasharray="5 3"/>`
      +txt(sx+3,PT+10,'IS | OOS',{s:9,c:'var(--dim)'});
    (EXP.events||[]).forEach(e=>{const x=at(e.date);
     if(x!=null&&x>PL)g+=`<line x1="${x}" y1="${PT}" x2="${x}" y2="${H-PB}"
       stroke="#d1495b" stroke-width="0.6" opacity="0.35"><title>${e.date} ${e.type}
       ${e.ccy}</title></line>`;});
    [0,.5,1].forEach(f=>{const v=mn+f*rg;
     g+=txt(PL-6,Y(v)+3,Math.exp(v).toFixed(4),{a:'end',s:9,c:'var(--dim)'});});
    g+=txt(PL,H-4,dstr[0],{s:9,c:'var(--dim)'})
      +txt(W-PR,H-4,dstr[dstr.length-1],{a:'end',s:9,c:'var(--dim)'});
    $('#pxchart').innerHTML=`<h3>${PAIR} — log price, coloured by state</h3>
     <svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg">${g}</svg>`;

    // ribbon: three stacked window rows
    const RH=54;let r='';
    [['fast 7','rf'],['med 28','rm'],['slow 128','rs']].forEach((row,ri)=>{
     const y=ri*16+6;
     r+=txt(PL-6,y+9,row[0],{a:'end',s:9,c:'var(--dim)'});
     let run=null,x0=null;
     idx.forEach((i,k)=>{const v=P[row[1]][i];
      if(v!==run){if(run!=null&&x0!=null)r+=`<rect x="${x0}" y="${y}"
        width="${Math.max(X(k)-x0,.8)}" height="11" fill="${RC[run]}" opacity="0.85"/>`;
       run=v;x0=X(k);}});
     if(run!=null&&x0!=null)r+=`<rect x="${x0}" y="${y}" width="${Math.max(X(idx.length-1)-x0,.8)}"
       height="11" fill="${RC[run]}" opacity="0.85"/>`;});
    $('#pxribbon').innerHTML=`<svg viewBox="0 0 ${W} ${RH}" xmlns="http://www.w3.org/2000/svg">${r}</svg>`;

    // the four underlying axes
    const AH=150;let a2='';
    [['straightness','straight','#2e9e5b'],['scale','scale','#d9a441'],
     ['persistence','persist','#5b8dd9'],['state age','age','#9aa0a6']]
     .forEach((ax,ai)=>{
      const vals=idx.map(i=>P[ax[1]][i]),f2=vals.filter(v=>v!=null);
      if(!f2.length)return;
      const lo=Math.min(...f2),hi=Math.max(...f2),rr=(hi-lo)||1;
      const y0=ai*36+8,hh=28;
      let pp=[];vals.forEach((v,k)=>{if(v==null)return;
       pp.push(X(k).toFixed(1)+','+(y0+(1-(v-lo)/rr)*hh).toFixed(1));});
      a2+=`<polyline points="${pp.join(' ')}" fill="none" stroke="${ax[2]}"
        stroke-width="1.1" opacity="0.9"/>`
       +txt(PL-6,y0+hh/2,ax[0],{a:'end',s:9,c:'var(--dim)'})
       +txt(W-PR,y0+8,hi.toFixed(2),{a:'end',s:8,c:'var(--dim)'});});
    $('#pxaxes').innerHTML=`<svg viewBox="0 0 ${W} ${AH}" xmlns="http://www.w3.org/2000/svg">${a2}</svg>`;

    panel(P);
    $('#pxlegend').innerHTML=(GRP===9?EXP.states:EXP.states.filter(
      x=>x.indexOf('transitional')<0)).map(s=>
     `<span class="count"><span style="display:inline-block;width:11px;height:11px;
      background:${SC[s]};border-radius:2px;vertical-align:-1px"></span> ${s}</span>`).join('');
   }

   function panel(P){
    const n=EXP.dates.length;let last=n-1;
    while(last>0&&P.st[last]==null)last--;
    const st=display(P,last),age=P.age[last];
    const rf=P.rf[last],rm=P.rm[last],rs=P.rs[last];
    const nm=['low','mid','high'];
    const agree=(rf===rm&&rm===rs)?'all three agree'
      :(rf!==rm&&rm===rs)?'fast apart':(rf===rs&&rm!==rs)?'medium apart'
      :(rf===rm&&rm!==rs)?'slow apart':'all differ';
    const ti=EXP.states.indexOf(st);
    const stay=(EXP.transitions&&ti>=0&&EXP.transitions[ti])?EXP.transitions[ti][ti]:null;
    const per=(EXP.per_pair||[]).find(d=>d.pair===PAIR)||{};
    const dur=(EXP.per_pair_dur||[]).find(d=>d.pair===PAIR)||{};
    $('#pxpanel').innerHTML=`<h3>${PAIR} now</h3>
     <div class="big" style="color:${SC[st]||'inherit'}">${st||'—'}</div>
     <span class="count">coloured by ${WINS[WIN]}, ${GRP}-state view</span><br>
     <span class="count">as of ${EXP.dates[last]}, ${age||'—'} bars in this state</span>
     <div class="note" style="margin-top:10px"><b>Windows:</b> fast ${nm[rf]},
      medium ${nm[rm]}, slow ${nm[rs]}<br>${agree} <span class="count">(description only — carries no
      measured excursion signal)</span></div>
     <div class="note"><b>Stays tomorrow:</b> ${stay==null?'—':(stay*100).toFixed(1)+'%'}
      <span class="count">from the transition matrix</span></div>
     <div class="tw" style="margin-top:10px"><table><thead><tr><th>State</th>
      <th>Share</th><th>Median run</th></tr></thead><tbody>
      ${EXP.states.map(s=>`<tr><td><span style="display:inline-block;width:9px;height:9px;
        background:${SC[s]};border-radius:2px"></span> ${s}</td>
        <td>${per[s]==null?'—':(per[s]*100).toFixed(1)+'%'}</td>
        <td>${dur[s]==null?'—':(+dur[s]).toFixed(0)}</td></tr>`).join('')}
      </tbody></table></div>`;
   }

   document.addEventListener('keydown',e=>{
    const sec=$('#px');if(!sec||sec.hidden||!EXP)return;
    if(e.key!=='ArrowLeft'&&e.key!=='ArrowRight')return;
    const ks=Object.keys(EXP.pairs),i=ks.indexOf(PAIR);
    PAIR=ks[(i+(e.key==='ArrowRight'?1:ks.length-1))%ks.length];draw();e.preventDefault();});

   const navb=[...document.querySelectorAll('nav button')].find(b=>b.dataset.t==='px');
   if(navb)navb.addEventListener('click',load);
   if(!$('#px').hidden)load();

   // ---- States tab, from the small feed ----
   const NS=BUN.ninestates||[],NE=BUN.nineexc||[],NT=BUN.ninetrans||[];
   if(NS.length){
    const ex=Object.fromEntries(NE.map(d=>[d.state,d]));
    $('#nstab tbody').innerHTML=NS.map(d=>{const e=ex[d.state]||{};
     return `<tr><td><span style="display:inline-block;width:10px;height:10px;
      background:${SC[d.state]};border-radius:2px"></span> <b>${d.state}</b></td>
      <td>${(d.share*100).toFixed(1)}%</td><td>${d.median_len}</td>
      <td>${e.n==null?'—':e.n}</td>
      <td>${e.mfe==null?'—':e.mfe.toFixed(4)}</td>
      <td>${e.bars==null?'—':e.bars.toFixed(1)}</td>
      <td>${e.retrace_pct==null?'—':e.retrace_pct.toFixed(0)+'%'}</td>
      <td>${e.eff==null?'—':e.eff.toFixed(4)}</td></tr>`;}).join('');
    if(NT.length){
     const names=NS.map(d=>d.state);
     let h='<table><thead><tr><th></th>'+names.map(n=>
      `<th style="font-size:10px">${n.slice(0,9)}</th>`).join('')+'</tr></thead><tbody>';
     NT.forEach((row,i)=>{h+=`<tr><td style="font-size:11px"><b>${names[i]}</b></td>`;
      row.forEach((v,j)=>{const a=v==null?0:v;
       h+=`<td style="background:rgba(46,158,91,${Math.min(a*1.6,.85)});
        text-align:center;font-size:10px">${v==null?'':(v*100).toFixed(0)}</td>`;});
      h+='</tr>';});
     $('#nstm').innerHTML=h+'</tbody></table>';}
     const PP=BUN.nineper||[];
    if(PP.length){
     const names=NS.map(d=>d.state);
     $('#nsper thead tr').innerHTML='<th>Pair</th>'+names.map(n=>
      `<th style="font-size:10px">${n.slice(0,9)}</th>`).join('');
     $('#nsper tbody').innerHTML=PP.map(r=>`<tr><td><b>${r.pair}</b></td>`
      +names.map(n=>`<td>${r[n]==null?'—':(r[n]*100).toFixed(1)}</td>`).join('')
      +'</tr>').join('');}
   }
  })();

  // ---- Task 3: excursion shape by regime ----
  (function(){const E=BUN.entry||[],EP=BUN.entrypair||[];if(!E.length)return;
   const O=E.filter(d=>d.sample==='oos');if(!O.length)return;
   const f4=v=>v==null?'—':(+v).toFixed(4);
   $('#entab tbody').innerHTML=O.map(d=>`<tr><td>${d.band}</td>
     <td>${d.n.toLocaleString()}</td><td>${f4(d.mfe)}</td><td>${f4(d.mae)}</td>
     <td>${d.ratio.toFixed(2)}</td><td>${d.bars_to_peak.toFixed(1)}</td>
     <td>${d.gb_pct.toFixed(1)}%</td><td>${f4(d.path_eff)}</td>
     <td>${(d.fav20*100).toFixed(1)}%</td></tr>`).join('');
   const c=O[0],t=O[2];
   const pk=EP.filter(d=>d.peak_later_in_trend===true||d.peak_later_in_trend==='True').length;
   $('#entxt').innerHTML=`<b>No. The excursion profiles are the same.</b> The prediction was
    that chop entries peak sooner and give more of it back. Bars to peak come out
    ${c.bars_to_peak.toFixed(1)} against ${t.bars_to_peak.toFixed(1)} (t = +1.2, not
    significant), and giveback is <b>${c.gb_pct.toFixed(0)}% against
    ${t.gb_pct.toFixed(0)}%</b> of the favourable peak &mdash; indistinguishable. Still
    onside at 20 bars is ${(c.fav20*100).toFixed(0)}% against ${(t.fav20*100).toFixed(0)}%,
    both coin flips. Pair by pair the peak arrives later in the trend third in just
    ${pk} of ${EP.length}.
    <br><br><b>What does differ is scale, not shape.</b> Chop entries have a larger MFE
    (${f4(c.mfe)} vs ${f4(t.mfe)}) <i>and</i> a larger MAE (${f4(c.mae)} vs ${f4(t.mae)}) —
    chop regimes are simply more volatile, so everything is bigger in both directions.
    Normalise by the size of the move and the shape is identical. The one asymmetry is that
    adverse excursion shrinks faster than favourable, lifting MFE/|MAE| from
    ${c.ratio.toFixed(2)} to ${t.ratio.toFixed(2)} — a stop-distance input at best, and it
    is not stable across subsamples.
    <br><br><b>Path efficiency does separate cleanly</b> (${f4(c.path_eff)} to
    ${f4(t.path_eff)}, t = +7.9) — but that is the quantity the composite was selected to
    predict, so it confirms the estimator works as an estimator and says nothing about
    whether it informs trade management.`;
  })();

  // ---- term structure (tasks 4-6) ----
  (function(){const T=BUN.termstruct||[],TP=BUN.termpairs||[];if(!T.length)return;
   const N=(BUN.termnull||[]);
   const f4=v=>v==null?'—':(+v).toFixed(4);
   const rows=T.filter(d=>d.scorable===true||d.scorable==='True')
     .map(d=>({...d,abs_so:Math.abs(d.so),corr:Math.abs(d.so)-(d.null_eff||0)}))
     .sort((a,b)=>b.corr-a.corr);
   $('#tstab tbody').innerHTML=rows.map(d=>{
    const ok=d.corr>0;
    return `<tr><td>${d.signal}${d.kind==='binary'?' <span class="count">rule</span>':''}</td>
     <td>${f4(d.abs_so)}</td><td>${f4(d.null_eff)}</td>
     <td style="color:${ok?'var(--trend)':'var(--kill)'}"><b>${f4(d.corr)}</b></td>
     <td>${d.null_eff?(d.abs_so/d.null_eff).toFixed(2)+'x':'—'}</td>
     <td>${d.ao==null?'—':d.ao.toFixed(3)}</td>
     <td>${Math.abs(d.to).toFixed(1)}</td></tr>`;}).join('');
   const b=rows[0];
   const stable=TP.filter(d=>d.stable===true||d.stable==='True').length;
   $('#tstxt').innerHTML=`<b>Nothing here clears the gauntlet.</b> The strongest corrected
    effect is <code>${b.signal}</code> at <b>${f4(b.corr)}</b>, against a gate of 0.0221 and
    a survivor set averaging 0.0277. Best agreement across the whole table is 0.79 against a
    gate of 0.893, and best |t| is 5.5 against a gate of 8.
    <br><br><b>Cross-horizon confluence does not rescue trend detection.</b> Requiring
    2-of-4 or 3-of-4 agreement scores <i>below</i> its own null (0.40× and 0.76×). The best
    rule, 3-of-4 plus positive persistence, corrects to 0.0033 — weaker than simply reading
    trailing 20-day efficiency on its own. Adding the daily/weekly/monthly filter as a third
    condition makes it worse, not better. Confluence is not adding evidence here.
    <br><br><b>Persistence is real but small:</b> corrected 0.0050 in difference form,
    0.0045 as a log ratio. That is a fifth of the gate.
    <br><br><b>Per pair (Task 6):</b> the absolute "sustains vs bursts" split is not
    meaningful — every pair lands on the same side under either construction, because
    efficiency decays as 1/&radic;H for any series and the common component swamps the
    pair. What <i>is</i> real is the ordering: the slope's rank correlation from in-sample
    to out is <b>+0.559</b> with ${stable} of ${TP.length} pairs keeping their sign, about
    as stable as baseline trendiness at 0.582. Term-structure shape is a genuine per-pair
    property, of the same modest size as everything else per-pair here.`;
  })();

  // ---- horizon sweep ----
  (function(){const H=BUN.horizon||[];if(!H.length)return;
   const f4=v=>v==null?'—':(+v).toFixed(4);
   const best=H.reduce((a,b)=>(b.t_ratio||0)>(a.t_ratio||0)?b:a,H[0]);
   const h20=H.find(d=>d.H===20)||{};
   const card=(h,s)=>`<div class="panel" style="flex:1;min-width:210px">
     <div class="big">${h}</div><span class="count">${s}</span></div>`;
   $('#hzcards').innerHTML=
     card(best.H+' days',`<b>Best horizon on the null-normalised comparison.</b>
       Real effect divided by what a shifted target earns peaks here at
       ${best.eff_ratio.toFixed(2)}x, against ${h20.eff_ratio.toFixed(2)}x at 20 days.`)
    +card(f4(best.eff_oos),`<b>Median |OOS effect| at ${best.H} days</b>, against
       ${f4(h20.eff_oos)} at 20 &mdash; ${((best.eff_oos/h20.eff_oos-1)*100).toFixed(0)}%
       larger for the same signals.`)
    +card(h20.null_t.toFixed(2)+' vs '+H[0].null_t.toFixed(2),
      `<b>Null |t| at 20 days against 5.</b> A zero effect earns a BIGGER t at long
       horizons, not smaller &mdash; overlapping windows, not sample size, dominate.`);
   $('#hztab tbody').innerHTML=H.map(d=>{
    const b=d.H===best.H;
    return `<tr${b?' style="font-weight:600"':''}><td>${d.H} days${b?' &larr; best':''}</td>
     <td>${f4(d.eff_oos)}</td><td>${d.agree.toFixed(3)}</td><td>${d.mono.toFixed(3)}</td>
     <td>${(d.retention*100).toFixed(1)}%</td><td>${d.null_t.toFixed(2)}</td>
     <td><b>${d.eff_ratio.toFixed(2)}x</b></td></tr>`;}).join('');
   $('#hznote').innerHTML=`<b>The 20-day choice was not optimal, but it was not badly
    wrong either.</b> Effect size peaks at 10 days and the null-normalised ratio peaks
    there too, ${best.eff_ratio.toFixed(2)}x against ${h20.eff_ratio.toFixed(2)}x &mdash;
    roughly ${((best.eff_ratio/h20.eff_ratio-1)*100).toFixed(0)}% more signal per unit of
    noise. Against that, agreement and monotonicity both improve monotonically with
    horizon, and out-of-sample sign retention is perfect at 15 and 20 days but not at 5.
    Shortening buys effect size and pays for it in cross-pair consistency.`;
  })();

  // ---- composite headline ----
  (function(){const C=(BUN.composite||[])[0];if(!C){return;}
   const q=[C.q1,C.q2,C.q3,C.q4,C.q5];
   const mn=Math.min(...q),mx=Math.max(...q),rg=(mx-mn)||1;
   const W=520,Hh=150,P=44;
   let g='';
   q.forEach((v,i)=>{const x=P+i*((W-P-20)/4);
    const y=Hh-26-((v-mn)/rg)*(Hh-60);
    if(i)g+=`<line x1="${P+(i-1)*((W-P-20)/4)}" y1="${Hh-26-((q[i-1]-mn)/rg)*(Hh-60)}" `
      +`x2="${x}" y2="${y}" stroke="var(--trend)" stroke-width="2"/>`;
    g+=`<circle cx="${x}" cy="${y}" r="4" fill="var(--trend)"/>`;
    g+=txt(x,y-10,v.toFixed(4),{a:'middle',s:10,m:1});
    g+=txt(x,Hh-8,'Q'+(i+1),{a:'middle',s:10,c:'var(--dim)'});});
   const svgc=`<svg viewBox="0 0 ${W} ${Hh}" xmlns="http://www.w3.org/2000/svg">${g}</svg>`;
   const better=C.uplift>0;
   $('#cmp').innerHTML=`<h3>The composite \u2014 all ${C.n_components} independents combined</h3>
   <div class="note">Each survivor z-scored and sign-aligned so high means expect straight
   travel, then averaged. This is the estimator's actual regime read.</div>
   ${svgc}
   <div style="display:flex;gap:26px;flex-wrap:wrap;margin-top:8px">
     <div><div class="big">${C.spread>0?'+':''}${C.spread.toFixed(4)}</div>
       <span class="count">Q5\u2212Q1 forward-efficiency spread</span></div>
     <div><div class="big">${(C.agree*100).toFixed(1)}%</div>
       <span class="count">pair agreement</span></div>
     <div><div class="big">${C.mono>0?'+':''}${C.mono.toFixed(3)}</div>
       <span class="count">monotonicity</span></div>
     <div><div class="big">${C.turn_spread.toFixed(4)}</div>
       <span class="count">turn-frequency spread</span></div>
   </div>
   <div class="note" style="margin-top:12px;border-left:3px solid ${better?'var(--trend)':'var(--kill)'};padding-left:10px">
   <b>Against its own best component:</b> ${C.best_single_name} alone scores
   <b>${C.best_single.toFixed(4)}</b>, so combining all ${C.n_components}
   <b>${better?'adds':'costs'} ${Math.abs(C.uplift).toFixed(4)}</b>.
   ${better?'':'The composite does NOT beat its strongest single component on spread. '
    +'What it buys is breadth \u2014 32 independent effects rather than one \u2014 and it '
    +'matches on pair agreement, but on raw separation a single panel-volatility signal '
    +'is still the strongest regime read in the project.'}</div>`;})();

  // ---- survivors tab: the 32 independents ----
  (function(){const IV=(BUN.independents||[]).slice();if(!IV.length)return;
   IV.forEach(d=>{d.dirn=d.to>0?'trend':'chop';});
   let ks='to',kd=-1,fT=0,fC=0;
   function draw(){
    let v=IV.filter(d=>(!fT||d.dirn==='trend')&&(!fC||d.dirn==='chop'));
    v.sort((a,b)=>{const x=a[ks],y=b[ks];
     if(x==null&&y==null)return 0; if(x==null)return 1; if(y==null)return -1;
     return (typeof x==='string'?x.localeCompare(y):Math.abs(x)-Math.abs(y))*kd;});
    $('#ivcnt').textContent=v.length+' of '+IV.length+' independent'
      +' \u00b7 '+IV.filter(d=>d.dirn==='trend').length+' trend, '
      +IV.filter(d=>d.dirn==='chop').length+' chop';
    const nf=(x,p)=>x==null?'\u2014':x.toFixed(p);
    $('#ivt tbody').innerHTML=v.map(d=>{
     const c=d.dirn==='trend'?'var(--trend)':'var(--chop)';
     return `<tr><td style="color:${c}">${d.s}</td>
     <td style="color:${c}">${d.dirn}</td><td>${d.f}</td><td>${d.b}</td>
     <td style="color:${c}">${nf(d.to,2)}</td><td>${nf(d.ti,2)}</td>
     <td>${nf(d.si,4)}</td><td>${nf(d.so,4)}</td>
     <td>${d.ao==null?'\u2014':(d.ao*100).toFixed(0)+'%'}</td>
     <td>${nf(d.mo,3)}</td><td>${nf(d.dec,2)}</td>
     <td>${d.tsb==null?'\u2014':d.tsb+'/6'}</td>
     <td>${d.nclust==null?'\u2014':(d.nclust-1)}</td>
     <td>${d.n==null?'\u2014':(d.n/1000).toFixed(0)+'k'}</td></tr>`;}).join('');
    const tr=IV.filter(d=>d.dirn==='trend'),ch=IV.filter(d=>d.dirn==='chop');
    const med=a=>{const x=a.slice().sort((p,q)=>p-q);return x.length?x[Math.floor(x.length/2)]:NaN;};
    $('#ivtx').innerHTML=`<b>${IV.length} independent</b> from `
     +`${(BUN.survivors||[]).length} that clear gates 1\u20137, out of `
     +`${(BUN.meta.n_scorable||0).toLocaleString()} scorable signals.<br>`
     +`Median |t| OOS \u2014 trend ${med(tr.map(d=>Math.abs(d.to))).toFixed(1)}, `
     +`chop ${med(ch.map(d=>Math.abs(d.to))).toFixed(1)}. `
     +`Median pair agreement \u2014 trend ${(100*med(tr.map(d=>d.ao))).toFixed(0)}%, `
     +`chop ${(100*med(ch.map(d=>d.ao))).toFixed(0)}%. `
     +`That gap is the structural asymmetry: volatility spikes hit all 28 pairs at once, `
     +`so panel-based chop measures clear the agreement gate almost by construction, `
     +`while trending is idiosyncratic per pair.`;}
   document.querySelectorAll('#ivt th').forEach(th=>{th.tabIndex=0;
    th.onclick=()=>{const k=th.dataset.k;kd=(k===ks)?-kd:-1;ks=k;draw();};});
   $('#ivT').onclick=e=>{fT=!fT;fC=0;e.target.setAttribute('aria-pressed',!!fT);
    $('#ivC').setAttribute('aria-pressed',false);draw();};
   $('#ivC').onclick=e=>{fC=!fC;fT=0;e.target.setAttribute('aria-pressed',!!fC);
    $('#ivT').setAttribute('aria-pressed',false);draw();};
   draw();})();

  // ---- crisis tab ----
  (function(){const C=BUN.crisis;if(!C||!C.length)return;
   const best=C.slice().sort((a,b)=>b.lift-a.lift)[0];
   $('#crt tbody').innerHTML=C.slice().sort((a,b)=>b.lift-a.lift).map(d=>{
    const lc=d.lift>=10?'var(--trend)':(d.lift>=5?'var(--chop)':'var(--dim)');
    return `<tr><td>${d.detector}</td><td>${d.caught} of ${d.n_events}</td>
    <td>${(d.recall*100).toFixed(0)}%</td><td>${(d.base_rate*100).toFixed(1)}%</td>
    <td style="color:${lc}">${d.lift.toFixed(1)}×</td>
    <td>${d.median_lag_days==null?'—':d.median_lag_days.toFixed(0)+'d'}</td></tr>`;}).join('');
   const lead=C.filter(d=>d.median_lag_days<0);
   $('#crtx').innerHTML=`Thresholds are the in-sample ${'95'}th percentile, so base rates sit
   near 5% by construction and lift is comparable across detectors. Detectors firing
   <i>before</i> the news: <b>${lead.length?lead.map(d=>d.detector).join(', '):'none'}</b>
   — the window cannot reach backwards, so this is a property of the test, not a finding.`;
   const EVs=(BUN.crisisev||[]).filter(e=>e.detector===best.detector&&!e.caught)
    .sort((a,b)=>b.severity-a.severity||a.date.localeCompare(b.date));
   $('#cet tbody').innerHTML=EVs.map(e=>`<tr><td>${e.date}</td><td>${e.type}</td>
    <td>${e.ccy||'—'}</td><td>${e.severity}</td><td>${e.description}</td></tr>`).join('')
    ||'<tr><td colspan="5">none</td></tr>';})();

  const TABS=['px','ns','g','iv','s','d','f','st','ld','nb','mt','cr','va','if',
              'ex','pt','hz','rd','xd','pc','gl','ar','vd'];
  document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>{
   document.querySelectorAll('nav button').forEach(x=>x.setAttribute('aria-selected',x===b));
   TABS.forEach(id=>{const e=$('#'+id);if(e)e.hidden=(id!==b.dataset.t);});
   // the regime feed is ~9 MB, so it is fetched only when that tab is first opened
   if(b.dataset.t==='rd'&&!REG&&!$('#rdpair'))initRegime();});
  drawG();drawA();buildScatter();buildFam();buildNew();
  // ---- the four new screens ----
  $('#glwrap').innerHTML=glossHTML();
  buildCharacter();
  buildShared();
  buildCurrentStates();
  buildRefit();
  buildExtDrivers();
  buildDriversReframed();
  buildDriverC();
  buildForwardOdds();
  buildDriverDE();
  buildDriverF();
  buildChronic();
  buildDrivers2();
  Object.keys(ARCHIVED).forEach(k=>archiveBanner(k,ARCHIVED[k][0],ARCHIVED[k][1]));
  (function(){
   const names={nb:'9-Box',mt:'Timeframes',ld:'Detectors',st:'Strategies'};
   $('#arwrap').innerHTML='<div class="note"><b>Nothing here is deleted.</b> These are '
    +'earlier generations of the classifier and the work that was tried and did not '
    +'survive. They stay because the record of what was ruled out is worth as much as '
    +'what shipped, and because two of them were re-tested later and the second look '
    +'changed the answer. Each tab carries a banner saying what it was and why it moved '
    +'here.</div>'
    +'<div class="tw"><table><thead><tr><th>Screen</th><th>What it was</th>'
    +'<th>Why it is archived</th></tr></thead><tbody>'
    +Object.keys(ARCHIVED).map(k=>'<tr><td><b>'+(names[k]||k)+'</b></td><td>'
      +ARCHIVED[k][0]+'</td><td>'+ARCHIVED[k][1]+'</td></tr>').join('')
    +'<tr><td><b>Validation</b> &mdash; part</td><td>The single-axis shape score</td>'
    +'<td>One continuous &ldquo;how trend-like&rdquo; number cut at terciles. It '
    +'separates better than the two-score version (0.261 vs 0.104 on trending) but '
    +'leaves 41% of days in an ambiguous middle against 20%. Superseded on coverage, '
    +'not on description &mdash; and that trade is still open.</td></tr>'
    +'<tr><td><b>Validation</b> &mdash; part</td><td>Moving-average and lead-time work</td>'
    +'<td>3,420 window pairs swept across three signal families to try to bridge the '
    +'4-bar confirmation lag. The best raw lift was 2.13&times; and its surrogate was '
    +'1.91&times;. The ridge <i>tracks the dwell</i> &mdash; an M-bar mean turns over '
    +'exactly the M bars the confirmation counts &mdash; so it reads the same window '
    +'rather than leading it.</td></tr>'
    +'<tr><td><b>States</b> &mdash; part</td><td>The tier</td>'
    +'<td>Five words describing which of the three ribbon windows disagreed. '
    +'Permutation p=0.257 on MFE/|MAE| and worse on everything else. Carried as '
    +'description only, never routed on.</td></tr>'
    +'</tbody></table></div>';})();
};})();
