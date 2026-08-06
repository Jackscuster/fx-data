/* FX Regime Lab — interface module, loaded by the shell from this repo.
   Add a tab HERE and every device picks it up on next open. The shell never changes. */
(function(){'use strict';
const $=s=>document.querySelector(s);
const NAV=`<nav role="tablist">
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

<section id="vd" hidden>
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
   {k:'si', n:'Effect size',  min:0,   max:.04,step:.001,v:.02,f:d=>Math.abs(d.si)},
   {k:'ao', n:'Pairs agree',  min:.5,  max:1,  step:.01, v:.85,f:d=>d.ao},
   {k:'mo', n:'Monotonic',    min:.5,  max:1,  step:.01, v:.95,f:d=>Math.abs(d.mo)},
   {k:'dec',n:'Decay ratio',  min:0,   max:1.5,step:.05, v:.6, f:d=>d.dec},
   // Gate 7. Signals scored before block spreads were stored have tsb null; they
   // are treated as passing rather than silently killed, so the funnel never
   // reports a drop that is really just missing data.
   {k:'tsb',n:'Blocks stable',min:0,   max:6,  step:1,  v:4,  f:d=>d.tsb==null?6:d.tsb}];
  const STRICT=[8,.02,.85,.95,.6,4];
  
  $('#gates').innerHTML=GATES.map((g,i)=>
   `<div class="gate"><label>${g.n}<b id="v${i}"></b></label>
    <input type="range" id="r${i}" min="${g.min}" max="${g.max}" step="${g.step}" value="${g.v}"></div>`).join('');
  
  function fmt(g,v){return g.k==='si'?v.toFixed(3):(g.k==='tsb'?v.toFixed(0)+' of 6':v.toFixed(2));}
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
   $('#valrefit').innerHTML=RF?`<div class="note">${RF.year} labels identical after
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

  document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>{
   document.querySelectorAll('nav button').forEach(x=>x.setAttribute('aria-selected',x===b));
   ['g','iv','s','d','f','st','ld','nb','mt','cr','va','vd'].forEach(id=>{const e=$('#'+id);if(e)e.hidden=(id!==b.dataset.t);});});
  drawG();drawA();buildScatter();buildFam();buildNew();
};})();
