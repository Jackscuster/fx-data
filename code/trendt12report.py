import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Layer 1 trend round 2: the Layer 3 table (money allowed here only), the
summary markdown covering all three parts, and the app wiring.

DECISION RULE, declared before any number: a construction earns a routing place
only if the routed book BEATS THE BASELINE (results/refit_books_modec2.csv:
mode C routed on shape2 TRENDING, +1.331% median year team1, PF 1.087) AND
BEATS ITS OWN SHUFFLE NULL. A construction that fails its 200-draw separation
null never reaches this stage at all. If both survive and improve, the better
routed book wins -- no blending, no third pick.
"""
import argparse, glob, json, os.path as _p
import numpy as np, pandas as pd

STAMP = '2026-11-10'
DCSTAMP = '2026-11-09'


def out(n):
    return _p.join(ROOTOUT, 'trend_%s_%s' % (n, STAMP))


def nulls_of(suf):
    o = {}
    for key, f in (('p_random_entry', 'walkforward_null_randomentry_nocut_summary_3slice%s_dirnull.csv' % suf),
                   ('p_regime_shuffle', 'walkforward_null_regimeshuffle_summary_3slice%s.csv' % suf)):
        pth = _p.join(ROOTOUT, f)
        o[key] = ({r.budget: float(r.p_value) for r in pd.read_csv(pth, comment='#').query("structure == 'NO_CUT'").itertuples()}
                  if _p.exists(pth) else {})
    return o


def book_rows():
    rows = []
    fixed = [('_modec2_routed', 'mode C routed on shape2 TRENDING (BASELINE)', 'mode C', 'baseline'),
             ('_dc_modec_alw', 'mode C trend UNGATED', 'mode C', 'control'),
             ('_dc_abtrend_sh2', 'A/B trend slices on shape2 TRENDING', 'A/B trend', 'baseline'),
             ('_dc_abtrend_alw', 'A/B trend slices UNGATED', 'A/B trend', 'control')]
    found = []
    for f in sorted(glob.glob(_p.join(ROOTOUT, 'walkforward_structures_3slice_t2_*.csv'))):
        suf = '_' + _p.basename(f).split('3slice_')[1].rsplit('.csv', 1)[0]
        v = suf.rsplit('_', 1)[-1].upper()
        fam = 'mode C' if '_modec_' in suf else 'A/B trend'
        found.append((suf, '%s routed on %s' % (fam, v), fam, 'candidate'))
    for suf, lab, fam, role in fixed + found:
        f = _p.join(ROOTOUT, 'walkforward_structures_3slice%s.csv' % suf)
        if not _p.exists(f):
            continue
        N = nulls_of(suf)
        for r in pd.read_csv(f, comment='#').itertuples():
            rows.append(dict(family=fam, role=role, book=lab, suffix=suf, budget=r.budget,
                             median_year_pct=r.median_year_pct, worst_year_pct=r.worst_year_pct,
                             max_dd_pct=r.max_dd_pct, dip95_pct=r.dip95_pct, profit_factor=r.profit_factor,
                             retention=getattr(r, 'retention', np.nan),
                             p_random_entry=N['p_random_entry'].get(r.budget),
                             p_regime_shuffle=N['p_regime_shuffle'].get(r.budget)))
    return pd.DataFrame(rows)


def stage_table():
    T = book_rows()
    T.to_csv(out('t12_layer3') + '.csv', index=False)
    x = T[T.budget == 'team1']
    t = ['LAYER 1 TREND ROUND 2 -- LAYER 3 MONEY TEST. %s' % STAMP,
         'Money appears here and nowhere else in this round. Same candidates, walk, budgets and nulls as the baseline.',
         'Only constructions that cleared their 200-draw separation null are here at all.', '']
    if len(x):
        t += [x[['family', 'role', 'book', 'median_year_pct', 'worst_year_pct', 'dip95_pct', 'profit_factor',
                 'retention', 'p_random_entry', 'p_regime_shuffle']].to_string(index=False, float_format=lambda v: '%8.3f' % v), '']
    cands = x[x.role == 'candidate'] if len(x) else pd.DataFrame()
    if not len(cands):
        t += ['NO CANDIDATE REACHED THIS STAGE: every construction failed its 200-draw null, so by the declared',
              'rule none was given a money test. The round ends at the battery and the shipped trend axis is',
              'unchanged -- it keeps its place by default, not by merit.']
    else:
        base = x[(x.suffix == '_modec2_routed')]
        b = float(base.median_year_pct.iloc[0]) if len(base) else np.nan
        for r in cands.itertuples():
            sh = r.p_regime_shuffle
            ok = np.isfinite(r.median_year_pct) and r.median_year_pct > b and (sh is not None and np.isfinite(sh) and sh <= 0.05)
            t += ['%s: %.3f%% vs baseline %.3f%%, shuffle p = %s -> %s'
                  % (r.book, r.median_year_pct, b, ('%.3f' % sh) if (sh is not None and np.isfinite(sh)) else 'n/a',
                     'EARNS a routing place' if ok else 'DOES NOT earn a routing place')]
    open(out('t12_layer3') + '.txt', 'w').write('\n'.join(t) + '\n')
    print('\n'.join(t), flush=True)


def md_table(d, cols, fmt='%.4f'):
    if not len(d):
        return '_(not built)_'
    head = '| ' + ' | '.join(cols) + ' |'
    sep = '|' + '|'.join(['---'] * len(cols)) + '|'
    body = ['| ' + ' | '.join((fmt % x) if isinstance(x, (float, np.floating)) and np.isfinite(x) else str(x)
                              for x in r) + ' |' for r in d[cols].itertuples(index=False)]
    return '\n'.join([head, sep] + body)


def stage_summary():
    B = pd.read_csv(out('t12_selection') + '.csv')
    N = pd.read_csv(out('t12_null') + '.csv')
    SB = pd.read_csv(out('t12_subperiod') + '.csv')
    L3 = pd.read_csv(out('t12_layer3') + '.csv') if _p.exists(out('t12_layer3') + '.csv') else pd.DataFrame()
    TT = pd.read_csv(_p.join(ROOTOUT, 'trend_anatomy_truth_table_%s.csv' % STAMP))
    ON = pd.read_csv(_p.join(ROOTOUT, 'trend_anatomy_onset_%s.csv' % STAMP))
    P1 = pd.read_csv(_p.join(ROOTOUT, 'trend_anatomy_pnl_by_position_%s.csv' % STAMP))
    MP = pd.read_csv(_p.join(ROOTOUT, 'trend_anatomy_mode_placement_%s.csv' % STAMP))
    md = ['# Layer 1 trend round 2 — anatomy of the failure, and two motivated constructions', '',
          '**%s.** Parts 1-3 of one declared run. Code: `code/trendanat.py` (measurement only),'
          ' `code/trendt12.py` (both constructions + battery, no money), `code/trendt12report.py`'
          ' (Layer 3 + delivery). Standing rules applied throughout: 5pm series, log price, one-bar lag,'
          ' cuts on the tuning window, one holdout confirm, 2021+ sealed, nulls before findings.' % STAMP, '',
          '## Part 1 — why the shipped trend axis fails (measurement only, no fix attempted)', '',
          '**1. The routed trend edge lives at episode onset and dies after it.** Share of each book\'s'
          ' trade-year R earned in each third of a TRENDING episode:', '',
          md_table(P1[P1.era == 'holdout'], ['book', 'third', 'trades', 'total_R', 'mean_R', 'share_positive',
                                             'share_of_book_R', 'share_of_book_loss'], '%.3f'), '',
          'On the holdout the A/B book takes **60% of its R in the first third** and almost nothing after;'
          ' mode C is flatter (29% / 45% / 26%). Losses are spread evenly across all three thirds in both'
          ' books (29-38%), so the problem is not where the losses are — it is that only the opening third'
          ' pays.', '',
          '**2. Half of all labelled trending episodes never went anywhere.** Progress measured in'
          ' tuning-window vol units against a threshold learned IS (0.509):', '',
          md_table(TT.groupby(['era', 'true_trend']).agg(episodes=('bars', 'size'), median_bars=('bars', 'median'),
                                                         median_progress=('progress_vol', 'median'),
                                                         median_efficiency=('efficiency', 'median')).reset_index(),
                   ['era', 'true_trend', 'episodes', 'median_bars', 'median_progress', 'median_efficiency'], '%.3f'), '',
          'True-trend share: **%.1f%% IS, %.1f%% holdout**. The false ones are not shorter — median 23-26 bars'
          ' against 20-23 — they are just directionless (efficiency 0.07-0.10 against 0.27-0.31). And the'
          ' shipped trend score does not tell them apart: on the holdout the FALSE episodes score **higher**'
          ' (0.494) than the true ones (0.329).'
          % (100 * TT[TT.era == 'is'].true_trend.mean(), 100 * TT[TT.era == 'holdout'].true_trend.mean()), '',
          '**3. The label arrives after most of the move is gone.** Median **%d bars** late against a median'
          ' %d-bar episode, with **%.0f%% of the leg\'s total move already spent** before the label confirms,'
          ' in both eras. A dwell-5 confirmation on a 20-bar move cannot be anything else.'
          % (ON.bars_before_label.median(), TT.bars.median(), 100 * ON.share_of_move_before_label.median()), '',
          '**4. Why C survives trend routing while A/B do not.** All three modes enter at the same place'
          ' (median ~0.50 of the episode), so entry timing is not the difference:', '',
          md_table(MP, ['book', 'mode', 'era', 'trades', 'median_entry_position', 'median_hold_days',
                        'share_exit_inside_episode', 'mean_R', 'share_positive'], '%.3f'), '',
          'C holds **10-11 days against B\'s 6**, exits inside the episode least often (0.70 vs 0.80), and'
          ' carries the highest share of winners (0.43 holdout vs A 0.39, B 0.34). C survives because its'
          ' exit rule keeps it in the move, not because the regime read puts it in at a better moment.', '',
          '### What Part 1 establishes', 'The shipped trend axis fails for two measurable reasons, neither'
          ' of which is a threshold-tuning problem: **it labels directionless episodes as trends half the'
          ' time**, and **it confirms roughly one median-trend-length after the move began**. Any'
          ' replacement has to fix one of those two things.', '',
          '## Parts 2 and 3 — the two constructions', '',
          '**T1, trend as broken chop.** FX\'s resting state is mean reversion, so trend is the failure of'
          ' snap-back. Built entirely from the existing chop machinery (`structure.swings` at the shipped'
          ' N=19, the same boundary the chop measures track): a break is a close outside the boundary, and'
          ' it either snaps back inside within R bars or holds. Score = share of breaks held over the'
          ' shipped 106-bar window; secondary = net progress beyond the broken boundary in tuning-window'
          ' vol units. Declared R = 5, 10.', '',
          '**T2, currency-leg trend.** Trends are currency stories. Strength per currency = cumulative log'
          ' change against the equal-weight basket of the other seven over 106 bars, from the 7 USD legs,'
          ' in that leg\'s tuning-window vol (constant). Pair score = |strength X − strength Y|; signed'
          ' version secondary. **This construction has nothing to sweep** — window and dwell are the'
          ' shipped ones and there is no third knob.', '',
          '### The battery (`trend_t12_battery_%s.csv`)' % STAMP, '',
          md_table(B, ['variant', 'family', 'knob', 'cut', 'separation_tuning', 'separation_holdout',
                       'median_run', 'flip_rate', 'coverage', 'share_trending', 'corr_shipped_trend',
                       'corr_shipped_chop', 'label_agreement_shipped']), '',
          'Shipped trend axis on the same battery: separation **%.4f** tuning / **%.4f** holdout, median run'
          ' %.1f bars, flip rate %.4f.' % (B.shipped_separation_tuning.iloc[0], B.shipped_separation_holdout.iloc[0],
                                           B.shipped_median_run.iloc[0], B.shipped_flip_rate.iloc[0]), '',
          '**Correlations, reported and deciding nothing.** T1 sits at 0.27-0.35 with the shipped trend score'
          ' and **−0.32 to −0.38 with the chop score** — it is the chop axis read with the opposite sign,'
          ' which is exactly what "trend as broken chop" predicts. T2 sits at **0.73** with the shipped trend'
          ' score: it largely restates the shipped axis by a different route.', '',
          '### The 200-draw null — the same re-derive-everything null that killed the DC axis'
          ' (`trend_t12_null_%s.csv`)' % STAMP, '',
          md_table(N, ['kind', 'variant', 'real', 'null_mean', 'null_p95', 'null_max', 'corrected', 'p_value']), '',
          '### Selection and the null gate (`trend_t12_selection_%s.csv`)' % STAMP, '',
          md_table(B, ['variant', 'median_run', 'flip_rate', 'run_ok', 'flip_ok', 'eligible',
                       'null_p_sign', 'null_p_perm', 'survives_null', 't1_selected']), '',
          '### Sub-period split, 2016-2019 vs 2020 (2021+ sealed)', '',
          md_table(SB, ['variant', 'period', 'separation', 'median_run', 'flip_rate', 'share_trending']), '']
    if len(L3):
        x = L3[L3.budget == 'team1']
        md += ['## Layer 3 — the money test (`trend_t12_layer3_%s.csv`)' % STAMP, '',
               md_table(x, ['family', 'role', 'book', 'median_year_pct', 'worst_year_pct', 'dip95_pct',
                            'profit_factor', 'retention', 'p_random_entry', 'p_regime_shuffle'], '%.3f'), '']
        if not (x.role == 'candidate').any():
            md += ['**No candidate reached this stage.** Every construction failed its 200-draw separation null,'
                   ' so by the rule declared before the run none was given a money test.', '']
    md += ['## What this round establishes', '',
           '1. The shipped trend axis\'s failure is **diagnosed, not guessed**: half its episodes are'
           ' directionless, and it confirms ~%d bars into a ~%d-bar move with %.0f%% of the leg already gone.'
           % (ON.bars_before_label.median(), TT.bars.median(), 100 * ON.share_of_move_before_label.median()),
           '2. The routed trend edge is **an onset edge** — 60% of the A/B book\'s R comes from the first'
           ' third of an episode — which is precisely the part the label is too late to catch.',
           '3. Mode C survives trend routing because of **how long it holds**, not because the regime read'
           ' times its entries better.',
           '4. Neither new construction clears the bar. The null gate is the binding constraint, exactly as'
           ' it was for the DC axis in round 1.', '',
           '_Files: `trend_anatomy_*_%s.*`, `trend_t12_*_%s.*`, `trend_states_*_%s.csv`._' % (STAMP, STAMP, STAMP)]
    open(out('summary') + '.md', 'w').write('\n'.join(md) + '\n')
    print('wrote %s' % (out('summary') + '.md'), flush=True)


def stage_app():
    B = pd.read_csv(out('t12_selection') + '.csv')
    N = pd.read_csv(out('t12_null') + '.csv')
    SB = pd.read_csv(out('t12_subperiod') + '.csv')
    L3 = pd.read_csv(out('t12_layer3') + '.csv') if _p.exists(out('t12_layer3') + '.csv') else pd.DataFrame()
    TT = pd.read_csv(_p.join(ROOTOUT, 'trend_anatomy_truth_table_%s.csv' % STAMP))
    ON = pd.read_csv(_p.join(ROOTOUT, 'trend_anatomy_onset_%s.csv' % STAMP))
    P1 = pd.read_csv(_p.join(ROOTOUT, 'trend_anatomy_pnl_by_position_%s.csv' % STAMP))
    MP = pd.read_csv(_p.join(ROOTOUT, 'trend_anatomy_mode_placement_%s.csv' % STAMP))
    anat = dict(
        pnl_by_position=P1.replace({np.nan: None}).to_dict('records'),
        truth=TT.groupby(['era', 'true_trend']).agg(episodes=('bars', 'size'), median_bars=('bars', 'median'),
                                                    median_progress=('progress_vol', 'median'),
                                                    median_efficiency=('efficiency', 'median')).reset_index().replace({np.nan: None}).to_dict('records'),
        onset=ON.groupby('era').agg(episodes=('bars_before_label', 'size'), median_bars_late=('bars_before_label', 'median'),
                                    median_share_of_move_gone=('share_of_move_before_label', 'median')).reset_index().replace({np.nan: None}).to_dict('records'),
        mode_placement=MP.replace({np.nan: None}).to_dict('records'))
    for root in (_p.join(_R, 'app_data.json'), _p.join(ROOTOUT, 'app_data.json')):
        if not _p.exists(root):
            continue
        D = json.load(open(root))
        D['trend_round2'] = dict(
            stamp=STAMP,
            note=('Layer 1 trend round 2: an anatomy of the shipped trend axis failure, then two motivated '
                  'constructions -- T1 trend-as-broken-chop and T2 currency-leg trend. Present-tense battery '
                  'and a 200-draw re-derive-everything null; money only in the Layer 3 table, and only for a '
                  'construction that cleared its null.'),
            anatomy=anat,
            battery=B.replace({np.nan: None}).to_dict('records'),
            null=N.replace({np.nan: None}).to_dict('records'),
            subperiod=SB.replace({np.nan: None}).to_dict('records'),
            layer3=(L3[L3.budget == 'team1'].replace({np.nan: None}).to_dict('records') if len(L3) else []))
        json.dump(D, open(root, 'w'))
        print('wired into %s' % root, flush=True)
    ui = _p.join(_R, 'app_ui.js'); s = open(ui).read()
    if 'tr2Fill' in s:
        print('app_ui.js already carries the trend round 2 tab', flush=True); return
    anchor = '<button role="tab" aria-selected="false" data-t="dc">DC axis</button>'
    assert s.count(anchor) == 1, 'app_ui.js: nav anchor not found'
    s = s.replace(anchor, anchor + '\n<button role="tab" aria-selected="false" data-t="tr2">Trend round 2</button>')
    sec = ('<section id="tr2" hidden>\n<h3>Trend round 2: failure anatomy, and two constructions</h3>\n'
           '<div class="note">Part 1 measures WHY the shipped trend axis fails -- where inside an episode the routed\n'
           'P&amp;L sits, how many labelled trending episodes actually went anywhere, how late the label confirms, and\n'
           'why mode C survives trend routing when A/B do not. Parts 2 and 3 are two motivated candidates: T1 reads\n'
           'trend as the failure of chop snap-back, T2 as a currency-leg story. Both face the same 200-draw\n'
           're-derive-everything null that killed the DC axis; money appears only for a construction that clears it.</div>\n'
           '<div id="tr2body"></div>\n</section>\n')
    s = s.replace('<section id="dc" hidden>', sec + '<section id="dc" hidden>', 1)
    old_t = "'ex','pt','hz','rd','xd','pc','gl','ar','vd','dc'];"
    assert s.count(old_t) == 1, 'app_ui.js: TABS list not found'
    s = s.replace(old_t, "'ex','pt','hz','rd','xd','pc','gl','ar','vd','dc','tr2'];")
    old_s = "   if(t==='dc')dcFill();};"
    assert s.count(old_s) == 1, 'app_ui.js: show() hook not found'
    s = s.replace(old_s, "   if(t==='dc')dcFill();\n   if(t==='tr2')tr2Fill();};")
    s = s.rstrip() + """

// ---- TREND ROUND 2 (Layer 1, 2026-11-10). Advanced only.
function tr2Fill(){
  const d=(window.D&&D.trend_round2)||null, el=document.getElementById('tr2body');
  if(!el) return;
  if(!d){el.innerHTML='<p class="note">No trend_round2 section in this app_data.json build.</p>';return;}
  const num=v=>v===null||v===undefined||v===''?'':(typeof v==='number'
      ?(Math.abs(v)>=1000?v.toFixed(0):Math.abs(v)<0.0001&&v!==0?v.toExponential(1):v.toFixed(4)):String(v));
  const tbl=(rows,cols,cap)=>{
    if(!rows||!rows.length) return '<h4>'+cap+'</h4><p class="note">(not built in this run)</p>';
    return '<h4>'+cap+'</h4><div class="tw"><table><thead><tr>'
      +cols.map(c=>'<th>'+c+'</th>').join('')+'</tr></thead><tbody>'
      +rows.map(r=>'<tr>'+cols.map(c=>'<td>'+num(r[c])+'</td>').join('')+'</tr>').join('')
      +'</tbody></table></div>';};
  const a=d.anatomy||{};
  el.innerHTML='<p class="note">'+(d.note||'')+' Built '+(d.stamp||'')+'.</p>'
    +'<h4>Part 1 &mdash; failure anatomy (measurement only)</h4>'
    +tbl(a.pnl_by_position,['book','era','third','trades','total_R','mean_R','share_positive','share_of_book_R','share_of_book_loss'],
         'Routed trend P&amp;L by position inside the episode')
    +tbl(a.truth,['era','true_trend','episodes','median_bars','median_progress','median_efficiency'],
         'Episode truth table: did the labelled trend actually go anywhere')
    +tbl(a.onset,['era','episodes','median_bars_late','median_share_of_move_gone'],
         'Onset cost: how late the label confirms, and how much of the move is already gone')
    +tbl(a.mode_placement,['book','mode','era','trades','median_entry_position','median_hold_days','share_exit_inside_episode','mean_R','share_positive'],
         'Trade placement inside trending episodes, by mode')
    +'<h4>Parts 2-3 &mdash; the constructions</h4>'
    +tbl(d.battery,['variant','family','knob','cut','separation_tuning','separation_holdout','median_run','flip_rate',
                    'coverage','corr_shipped_trend','corr_shipped_chop','survives_null','t1_selected'],
         'Present-tense battery and the null gate')
    +tbl(d.null,['kind','variant','real','null_mean','null_p95','null_max','corrected','p_value'],
         '200-draw surrogate null (construction, vol and cut re-derived on every draw)')
    +tbl(d.subperiod,['variant','period','separation','median_run','flip_rate','share_trending'],
         'Sub-period split: 2016-2019 vs 2020')
    +tbl(d.layer3,['family','role','book','median_year_pct','worst_year_pct','dip95_pct','profit_factor','retention','p_random_entry','p_regime_shuffle'],
         'Layer 3 money test &mdash; only for constructions that cleared the null');}
"""
    open(ui, 'w').write(s)
    print('app_ui.js: Trend round 2 tab added (%d bytes)' % len(s), flush=True)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--stage', required=True, choices=['table', 'summary', 'app'])
    a = ap.parse_args(); print('=== trendt12report %s ===' % a.stage, flush=True)
    {'table': stage_table, 'summary': stage_summary, 'app': stage_app}[a.stage]()
    print('TREND REPORT STAGE %s COMPLETE' % a.stage.upper(), flush=True)


if __name__ == '__main__':
    main()
