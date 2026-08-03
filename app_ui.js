/* FX Regime Lab — interface module, loaded by the shell from this repo.
   Add a tab HERE and every device picks it up on next open. The shell never changes. */
(function(){'use strict';
const $=s=>document.querySelector(s);
const NAV=`<nav role="tablist">
<button role="tab" aria-selected="true" data-t="g">Gauntlet</button>
<button role="tab" aria-selected="false" data-t="s">All signals</button>
<button role="tab" aria-selected="false" data-t="d">Decay</button>
<button role="tab" aria-selected="false" data-t="f">Families</button>
<button role="tab" aria-selected="false" data-t="st">Strategies</button>
<button role="tab" aria-selected="false" data-t="ld">Detectors</button>
<button role="tab" aria-selected="false" data-t="nb">9-Box</button>
<button role="tab" aria-selected="false" data-t="mt">Timeframes</button>
<button role="tab" aria-selected="false" data-t="vd">Verdict</button>
</nav>`;
const BODY=`<div class="grid">
<div>
<div class="panel"><h3>Gates</h3><div id="gates"></div>
<button class="chip" id="strict" style="width:100%;margin-top:6px">Reset to strict</button>
</div>
<div class="panel" style="margin-top:16px"><h3>Attrition</h3><div class="funnel" id="fun"></div></div>
</div>
<div>
<div class="panel"><h3>Survivors</h3>
<div class="big" id="surv">0 <span>of 2030</span></div></div>
<div class="tools" style="margin-top:18px">
<button class="chip" id="exp">Export CSV</button><span class="count" id="scnt"></span></div>
<div class="tw"><table id="gt"><thead><tr>
<th data-k="s">Signal</th><th data-k="to">t OOS</th><th data-k="ti">t IS</th>
<th data-k="si">Spread</th><th data-k="ao">Agree</th><th data-k="mo">Mono</th>
<th data-k="dec">Decay</th><th>Quintiles</th></tr></thead><tbody></tbody></table></div>
<div class="note"><b>Not yet gated:</b> time stability across 6 blocks, window robustness,
correlation to incumbents, turnover and detection lag. Those need a rescore and the
estimator rebuilt. Everything shown here is measured, nothing is assumed.</div>
</div></div></section>

<section id="s" hidden>
<div class="tools"><input type="search" id="q" placeholder="filter" aria-label="Filter">
<button class="chip" id="cT" aria-pressed="false">Trend</button>
<button class="chip" id="cC" aria-pressed="false">Chop</button>
<button class="chip" id="cX" aria-pressed="false">Cross-sectional</button>
<span class="count" id="acnt"></span></div>
<div class="tw"><table id="at"><thead><tr>
<th data-k="s">Signal</th><th data-k="ti">t IS</th><th data-k="to">t OOS</th>
<th data-k="si">Spread IS</th><th data-k="so">Spread OOS</th><th data-k="ai">Agree IS</th>
<th data-k="ao">Agree OOS</th><th data-k="dec">Decay</th><th data-k="n">Obs</th>
</tr></thead><tbody></tbody></table></div></section>

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
<div class="note"><b>Detector ladder, dumbest to fanciest.</b> Each must beat the row above or
it is not worth using. Every label is backward-looking and was audited: 20/20 spot-checks
reproduced from truncated data.</div>
<h3>How often do regimes flip?</h3><div id="durch"></div>
<h3>Filter applied to baseline, improvement vs unfiltered</h3>
<div class="tw"><table id="ldt"><thead><tr>
<th>Strategy</th><th>Cell</th><th>Data %</th><th>Ret/Exp</th><th>Ret/DD</th><th>PF</th>
<th>Win%</th><th>$AvgTrade</th></tr></thead><tbody></tbody></table></div></section>


<section id="nb" hidden>
<div class="note"><b>Direction \\u00d7 volatility, 3\\u00d73.</b> Cut points are terciles learned on
1999-2015 only and applied unchanged to 2016-2026. Both inputs lagged one bar. Colour is
OOS Sharpe: amber positive, red negative, against the unfiltered baseline shown below each grid.</div>
<div id="nbgrid"></div>
<h3>Routing \\u2014 which sleeve wins each box</h3>
<div class="tw"><table id="nbt"><thead><tr><th>Box</th><th>Mean reversion</th><th>Momentum</th>
<th>Winner</th><th>Edge</th><th>Data %</th></tr></thead><tbody></tbody></table></div>
<div class="note" id="nbtx"></div></section>


<section id="mt" hidden>
<div class="note"><b>Monthly / weekly / daily regimes, mapped onto daily bars.</b> Strategies
trade daily; M and W exist only to confirm or contradict it. Lookbacks form a real hierarchy
\\u2014 60 days, 26 weeks, 12 months. A weekly label is not usable until the following Monday and a
monthly label not until the next month opens; both are shifted on their own clock before being
mapped down.</div>
<h3>Do the timeframes line up?</h3><div id="mtag"></div>
<h3>Daily sleeve performance by confluence</h3><div id="mtcf"></div>
<div class="tw" style="margin-top:16px"><table id="mtt"><thead><tr>
<th>Cell</th><th>Data %</th><th>Sharpe</th><th>Ret/DD</th><th>PF</th><th>Trades</th>
<th>Win%</th><th>$AvgTrade</th><th>Exposure</th></tr></thead><tbody></tbody></table></div>
<div class="note" id="mttx"></div></section>

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
window.renderApp=function(BUNDLE,root){
  let BUN=BUNDLE, D=(BUNDLE.signals||BUNDLE);
  root.innerHTML=NAV+'<section id="g">'+BODY;
  const MT=BUN.meta||{};
  $('#sub').textContent=(D.length||0)+' signals \u00b7 '+(MT.pairs||28)+' pairs \u00b7 IS 1999-2015 \u00b7 OOS 2016-2026'+(MT.built?' \u00b7 rebuilt '+MT.built:'');
  const GATES=[
   {k:'to', n:'|t| OOS',      min:0,   max:25, step:.5, v:8,   f:d=>Math.abs(d.to)},
   {k:'si', n:'Effect size',  min:0,   max:.04,step:.001,v:.02,f:d=>Math.abs(d.si)},
   {k:'ao', n:'Pairs agree',  min:.5,  max:1,  step:.01, v:.85,f:d=>d.ao},
   {k:'mo', n:'Monotonic',    min:.5,  max:1,  step:.01, v:.95,f:d=>Math.abs(d.mo)},
   {k:'dec',n:'Decay ratio',  min:0,   max:1.5,step:.05, v:.6, f:d=>d.dec}];
  const STRICT=[8,.02,.85,.95,.6];
  
  $('#gates').innerHTML=GATES.map((g,i)=>
   `<div class="gate"><label>${g.n}<b id="v${i}"></b></label>
    <input type="range" id="r${i}" min="${g.min}" max="${g.max}" step="${g.step}" value="${g.v}"></div>`).join('');
  
  function fmt(g,v){return g.k==='si'?v.toFixed(3):(g.k==='ao'||g.k==='mo'?v.toFixed(2):v.toFixed(2));}
  function vals(){return GATES.map((g,i)=>+$('#r'+i).value);}
  function survivors(){
   const V=vals();
   return D.filter(d=>d.held&&GATES.every((g,i)=>g.f(d)>=V[i]));}
  function funnel(){
   const V=vals();let cur=D.filter(d=>d.held);
   const rows=[['sign holds',cur.length]];
   GATES.forEach((g,i)=>{cur=cur.filter(d=>g.f(d)>=V[i]);rows.push([g.n,cur.length]);});
   $('#fun').innerHTML=rows.map(r=>
    `<div class="fr"><span class="nm">${r[0]}</span><span class="bar">
     <i style="width:${100*r[1]/D.length}%"></i></span>
     <span class="ct ${r[1]===0?'z':''}">${r[1]}</span></div>`).join('');}
  function spark(q){const mn=Math.min(...q),mx=Math.max(...q),r=(mx-mn)||1;
   return '<span class="spark">'+q.map(v=>`<i style="height:${3+13*(v-mn)/r}px"></i>`).join('')+'</span>';}
  let gs='to',gd=-1;
  function drawG(){
   GATES.forEach((g,i)=>$('#v'+i).textContent=fmt(g,+$('#r'+i).value));
   const S=survivors();funnel();
   $('#surv').innerHTML=S.length+' <span>of '+D.length+'</span>';
   $('#scnt').textContent=S.length+' shown';
   S.sort((a,b)=>{const x=a[gs],y=b[gs];
    return (typeof x==='string'?x.localeCompare(y):Math.abs(x)-Math.abs(y))*gd;});
   $('#gt tbody').innerHTML=S.map(d=>{const c=d.ti>0?'var(--trend)':'var(--chop)';
    return `<tr><td style="color:${c}">${d.s}</td><td style="color:${c}">${d.to.toFixed(1)}</td>
    <td>${d.ti.toFixed(1)}</td><td>${d.si.toFixed(4)}</td><td>${(d.ao*100).toFixed(0)}%</td>
    <td>${d.mo.toFixed(2)}</td><td>${d.dec.toFixed(2)}</td><td>${spark(d.qo)}</td></tr>`;}).join('')
    ||'<tr><td colspan="8" style="color:var(--kill);padding:18px">Nothing survives these gates.</td></tr>';}
  GATES.forEach((g,i)=>$('#r'+i).oninput=drawG);
  $('#strict').onclick=()=>{STRICT.forEach((v,i)=>$('#r'+i).value=v);drawG();};
  $('#exp').onclick=()=>{const S=survivors();
   const csv='signal,t_is,t_oos,spread_is,spread_oos,agree_is,agree_oos,mono_oos,decay\n'+
    S.map(d=>[d.s,d.ti,d.to,d.si,d.so,d.ai,d.ao,d.mo,d.dec].join(',')).join('\n');
   const a=document.createElement('a');
   a.href=URL.createObjectURL(new Blob([csv],{type:'text/csv'}));
   a.download='gauntlet_survivors.csv';a.click();};
  document.querySelectorAll('#gt th').forEach(th=>{if(!th.dataset.k)return;th.tabIndex=0;
   th.onclick=()=>{const k=th.dataset.k;gd=(k===gs)?-gd:-1;gs=k;drawG();};});
  
  let as='ti',ad=-1,fT=0,fC=0,fX=0;
  function drawA(){
   const q=$('#q').value.trim().toLowerCase();
   let v=D.filter(d=>(!q||d.s.toLowerCase().includes(q))&&(!fT||d.ti>0)&&(!fC||d.ti<0)
    &&(!fX||d.b==='cross-sectional'));
   v.sort((a,b)=>{const x=a[as],y=b[as];
    return (typeof x==='string'?x.localeCompare(y):Math.abs(x)-Math.abs(y))*ad;});
   $('#acnt').textContent=v.length+' of '+D.length;
   $('#at tbody').innerHTML=v.slice(0,600).map(d=>{
    const c=Math.abs(d.ti)<2?'var(--flat)':(d.ti>0?'var(--trend)':'var(--chop)');
    return `<tr><td style="color:${c}">${d.s}</td><td style="color:${c}">${d.ti.toFixed(1)}</td>
    <td>${d.to.toFixed(1)}</td><td>${d.si.toFixed(4)}</td><td>${d.so.toFixed(4)}</td>
    <td>${(d.ai*100).toFixed(0)}%</td><td>${(d.ao*100).toFixed(0)}%</td>
    <td>${d.dec.toFixed(2)}</td><td>${(d.n/1000).toFixed(0)}k</td></tr>`;}).join('');}
  $('#q').oninput=drawA;
  $('#cT').onclick=e=>{fT=!fT;fC=0;e.target.setAttribute('aria-pressed',!!fT);
   $('#cC').setAttribute('aria-pressed',false);drawA();};
  $('#cC').onclick=e=>{fC=!fC;fT=0;e.target.setAttribute('aria-pressed',!!fC);
   $('#cT').setAttribute('aria-pressed',false);drawA();};
  $('#cX').onclick=e=>{fX=!fX;e.target.setAttribute('aria-pressed',!!fX);drawA();};
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
   D.forEach(d=>{const c=!d.held?'var(--kill)':(d.ti>0?'var(--trend)':'var(--chop)');
    s+=`<circle cx="${x(d.ti)}" cy="${y(d.to)}" r="2.4" fill="${c}" opacity=".5"/>`;});
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
   (function(){const N=B.ninebox;if(!N||!N.length)return;
    const DIR=['down','flat','up'],VOL=['high','med','low'];
    const cells=N.filter(d=>d.cell!=='BASELINE');
    const mx=Math.max(...cells.map(d=>Math.abs(d.sharpe)))||1;
    let html='';
    [...new Set(N.map(d=>d.sleeve))].forEach(sn=>{
     const base=N.find(d=>d.sleeve===sn&&d.cell==='BASELINE');
     const W=620,H=280,L=96,T=44,cw=(W-L-14)/3,ch=(H-T-34)/3;let g='';
     g+=txt(L+(W-L-14)/2,20,sn.replace('_',' ').toUpperCase(),{a:'middle',s:13,c:'var(--ink)',w:600});
     DIR.forEach((d,i)=>g+=txt(L+cw*i+cw/2,T-8,d==='flat'?'not trending':'trending '+d,{a:'middle',s:11}));
     VOL.forEach((v,j)=>{g+=txt(L-10,T+ch*j+ch/2+4,v+' vol',{a:'end',s:11,c:'var(--ink)'});
      DIR.forEach((d,i)=>{const r=cells.find(x=>x.sleeve===sn&&x.cell===v+'|'+d);
       const x0=L+cw*i,y0=T+ch*j;
       if(!r){g+=`<rect x="${x0+2}" y="${y0+2}" width="${cw-4}" height="${ch-4}" fill="var(--sf2)" rx="2"/>`;
        g+=txt(x0+cw/2,y0+ch/2+4,'\u2014',{a:'middle',s:12,m:1});return;}
       const c=r.sharpe>0?'224,160,60':'180,83,75';
       g+=`<rect x="${x0+2}" y="${y0+2}" width="${cw-4}" height="${ch-4}"
         fill="rgba(${c},${(0.15+0.75*Math.abs(r.sharpe)/mx).toFixed(2)})" rx="2"/>`;
       g+=txt(x0+cw/2,y0+ch/2,(r.sharpe>0?'+':'')+r.sharpe.toFixed(2),
         {a:'middle',s:16,m:1,c:'var(--ink)',w:600});
       g+=txt(x0+cw/2,y0+ch/2+17,(r.data_pct*100).toFixed(1)+'% of bars',{a:'middle',s:9.5,m:1});});});
     g+=txt(L,H-8,'baseline (unfiltered) Sharpe '+(base?base.sharpe.toFixed(3):'n/a')
       +'  \u00b7  colour scaled to \u00b1'+mx.toFixed(2),{s:10,m:1});
     html+=svg(W,H,g);});
    $('#nbgrid').innerHTML=html;
    // routing table
    const keys=[...new Set(cells.map(d=>d.cell))];
    const rows=keys.map(k=>{const a=cells.find(d=>d.cell===k&&d.sleeve==='mean_reversion');
     const b2=cells.find(d=>d.cell===k&&d.sleeve==='momentum');
     const sa=a?a.sharpe:NaN,sb=b2?b2.sharpe:NaN;
     return {k,sa,sb,w:sa>sb?'mean_reversion':'momentum',e:Math.abs(sa-sb),dp:a?a.data_pct:0};})
     .sort((p,q)=>q.e-p.e);
    $('#nbt tbody').innerHTML=rows.map(r=>{
     const pos=Math.max(r.sa,r.sb)>0;
     return `<tr><td>${r.k}</td>
     <td style="color:${r.sa>0?'var(--trend)':'var(--kill)'}">${r.sa.toFixed(3)}</td>
     <td style="color:${r.sb>0?'var(--trend)':'var(--kill)'}">${r.sb.toFixed(3)}</td>
     <td style="color:${pos?'var(--ink)':'var(--dim)'}">${pos?r.w:'cash'}</td>
     <td>${r.e.toFixed(2)}</td><td>${(r.dp*100).toFixed(1)}%</td></tr>`;}).join('');
    const nwin=rows.filter(r=>Math.max(r.sa,r.sb)>0).length;
    $('#nbtx').innerHTML=`<b>${nwin} of ${rows.length} boxes</b> have a positive sleeve.
    Where both are negative the box routes to <b>cash</b> \u2014 "winner" there only means
    losing less, which is not a reason to allocate.`;})();
  
  
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
    const m2=Math.max(...rows.map(d=>Math.abs(d.sharpe)))*1.25;
    let h=`<line x1="${P2}" y1="6" x2="${P2}" y2="${H2-22}" stroke="var(--line2)"/>`;
    rows.forEach((d,i)=>{const yy=12+i*38,w=Math.abs(d.sharpe)/m2*(W2-P2-110);
     const base=d.cell==='BASELINE';
     const c=base?'var(--flat)':(d.sharpe>0.181?'var(--trend)':'var(--kill)');
     h+=txt(P2-10,yy+16,d.cell,{a:'end',m:1,s:11,c:base?'var(--dim)':'var(--ink)'});
     h+=`<rect x="${P2}" y="${yy+3}" width="${Math.max(w,2)}" height="19" fill="${c}" opacity=".75" rx="1"/>`;
     h+=txt(P2+Math.max(w,2)+8,yy+17,d.sharpe.toFixed(3)+'   '+(d.data_pct*100).toFixed(1)+'% of bars',{m:1,s:10});});
    h+=txt(P2,H2-6,'OOS Sharpe \u00b7 grey bar is the unfiltered baseline',{s:10});
    $('#mtcf').innerHTML=svg(W2,H2,h);
    $('#mtt tbody').innerHTML=rows.map(d=>{const base=d.cell==='BASELINE';
     const c=base?'var(--dim)':(d.sharpe>0.181?'var(--trend)':'var(--kill)');
     return `<tr><td style="color:${c}">${d.cell}</td><td>${(d.data_pct*100).toFixed(1)}%</td>
     <td style="color:${c}">${d.sharpe.toFixed(3)}</td><td>${d.retdd.toFixed(2)}</td>
     <td>${d.pf.toFixed(3)}</td><td>${d.trades}</td><td>${(d.win*100).toFixed(1)}%</td>
     <td>${d.avg.toFixed(0)}</td><td>${(d.expo*100).toFixed(0)}%</td></tr>`;}).join('');
    const al=M.find(d=>d.cell==='aligned trending'),da=M.find(d=>d.cell==='daily alone');
    if(al&&da)$('#mttx').innerHTML=`When all three timeframes agree and point somewhere,
     the daily sleeve runs at <b>${al.sharpe.toFixed(3)}</b> Sharpe. When the daily read has no
     higher-timeframe support it runs at <b>${da.sharpe.toFixed(3)}</b> \u2014 essentially zero.
     Confluence is doing real work here.`;})();
  
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
  
  document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>{
   document.querySelectorAll('nav button').forEach(x=>x.setAttribute('aria-selected',x===b));
   ['g','s','d','f','st','ld','nb','mt','vd'].forEach(id=>$('#'+id).hidden=(id!==b.dataset.t));});
  
  document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>{
    document.querySelectorAll('nav button').forEach(x=>x.setAttribute('aria-selected',x===b));
    ['g','s','d','f','st','ld','nb','mt','vd'].forEach(id=>{const e=$('#'+id);if(e)e.hidden=(id!==b.dataset.t);});});
  drawG();drawA();buildScatter();buildFam();buildNew();
};})();
