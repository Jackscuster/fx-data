import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""THE LAYER 3 MONEY TEST for the candidate DC trend axis, and the delivery.

Runs ONLY after code/dcaxis.py's present-tense battery, never instead of it.
Money metrics are allowed in this file and in no other part of the round.

THE DECISION RULE, declared before the first number existed (Jack, 9 Nov):
the DC axis earns a routing place only if the routed book BEATS THE BASELINE
(results/refit_books_modec2.csv -- mode C routed on shape2 TRENDING: +1.331%
median year team1, PF 1.087, 4 of 5 traded years) AND BEATS ITS OWN SHUFFLE
NULL. The correlation with the shipped axis never makes this decision.

    --stage table    assemble every book + both nulls into one dated table
    --stage summary  the markdown summary of the whole round
    --stage app      wire the round into app_data.json and app_ui.js (Advanced)
"""
import argparse, json, os.path as _p
import numpy as np, pandas as pd

STAMP = '2026-11-09'
BOOKS = (
    ('_modec2_routed', 'mode C routed on shape2 TRENDING (BASELINE)', 'mode C', 'baseline'),
    ('_dc_modec_dc', 'mode C routed on the DC trend axis', 'mode C', 'candidate'),
    ('_dc_modec_alw', 'mode C trend UNGATED (no trend axis at all)', 'mode C', 'control'),
    ('_dc_abtrend_sh2', 'A/B trend slices on shape2 TRENDING', 'A/B trend', 'baseline'),
    ('_dc_abtrend_dc', 'A/B trend slices on the DC trend axis', 'A/B trend', 'candidate'),
    ('_dc_abtrend_alw', 'A/B trend slices UNGATED', 'A/B trend', 'control'),
)


def out(name):
    return _p.join(ROOTOUT, 'dc_axis_%s_%s' % (name, STAMP))


def nulls_of(suf):
    o = {}
    for key, f in (('p_random_entry', 'walkforward_null_randomentry_nocut_summary_3slice%s_dirnull.csv' % suf),
                   ('p_regime_shuffle', 'walkforward_null_regimeshuffle_summary_3slice%s.csv' % suf)):
        pth = _p.join(ROOTOUT, f)
        if _p.exists(pth):
            d = pd.read_csv(pth, comment='#')
            d = d[d.structure == 'NO_CUT'] if 'structure' in d.columns else d
            o[key] = {r.budget: float(r.p_value) for r in d.itertuples()}
            o[key + '_mean'] = {r.budget: float(getattr(r, 'null_mean', np.nan)) for r in d.itertuples()}
            o[key + '_max'] = {r.budget: float(getattr(r, 'null_max', np.nan)) for r in d.itertuples()}
        else:
            o[key] = {}; o[key + '_mean'] = {}; o[key + '_max'] = {}
    return o


def stage_table():
    rows = []
    for suf, lab, fam, role in BOOKS:
        f = _p.join(ROOTOUT, 'walkforward_structures_3slice%s.csv' % suf)
        if not _p.exists(f):
            print('  MISSING %s (%s)' % (_p.basename(f), lab), flush=True)
            rows.append(dict(family=fam, role=role, book=lab, suffix=suf, budget='', note='not built'))
            continue
        N = nulls_of(suf)
        for r in pd.read_csv(f, comment='#').itertuples():
            rows.append(dict(family=fam, role=role, book=lab, suffix=suf, budget=r.budget,
                             median_year_pct=r.median_year_pct, worst_year_pct=r.worst_year_pct,
                             max_dd_pct=r.max_dd_pct, dip95_pct=r.dip95_pct, profit_factor=r.profit_factor,
                             build_median_year_pct=getattr(r, 'build_median_year_pct', np.nan),
                             retention=getattr(r, 'retention', np.nan),
                             retention_flag=getattr(r, 'retention_flag', ''),
                             p_random_entry=N['p_random_entry'].get(r.budget),
                             rand_null_mean=N['p_random_entry_mean'].get(r.budget),
                             rand_null_max=N['p_random_entry_max'].get(r.budget),
                             p_regime_shuffle=N['p_regime_shuffle'].get(r.budget),
                             shuffle_null_mean=N['p_regime_shuffle_mean'].get(r.budget),
                             shuffle_null_max=N['p_regime_shuffle_max'].get(r.budget), note=''))
        # per slice, where it exists
        ps = _p.join(ROOTOUT, 'walkforward_perslice_3slice%s.csv' % suf)
        if _p.exists(ps):
            for r in pd.read_csv(ps, comment='#').itertuples():
                rows.append(dict(family=fam, role=role, book=lab + ' [%s]' % r.slice, suffix=suf, budget=r.budget,
                                 median_year_pct=r.median_year_pct, worst_year_pct=r.worst_year_pct,
                                 max_dd_pct=r.max_dd_pct, dip95_pct=r.dip95_pct, profit_factor=r.profit_factor,
                                 build_median_year_pct=np.nan, retention=np.nan, retention_flag='',
                                 p_random_entry='book-level', p_regime_shuffle='book-level', note='per slice'))
    T = pd.DataFrame(rows)
    T.to_csv(out('layer3') + '.csv', index=False)
    x = T[(T.budget == 'team1') & (T.note == '')]
    txt = ['DC TREND AXIS -- LAYER 3 MONEY TEST. %s' % STAMP,
           'Money metrics appear here and nowhere else in this round. Same 104 mode C candidates, same walk,',
           'same budgets, same nulls as results/refit_books_modec2.csv. team1 shown; team2 is the 5.4%% budget.',
           '', 'DECISION RULE, declared before any number: the DC axis earns a routing place only if the routed',
           'book BEATS THE BASELINE and BEATS ITS OWN SHUFFLE NULL. The correlation never decides this.', '',
           x[['family', 'role', 'book', 'median_year_pct', 'worst_year_pct', 'dip95_pct', 'profit_factor',
              'retention', 'p_random_entry', 'p_regime_shuffle']].to_string(index=False, float_format=lambda v: '%8.3f' % v)]
    # the verdict, mechanically
    def get(suf, col, bt='team1'):
        q = T[(T.suffix == suf) & (T.budget == bt) & (T.note == '')]
        return float(q[col].iloc[0]) if len(q) and pd.notna(q[col].iloc[0]) else np.nan
    base = get('_modec2_routed', 'median_year_pct'); cand = get('_dc_modec_dc', 'median_year_pct')
    try:
        sh = float(T[(T.suffix == '_dc_modec_dc') & (T.budget == 'team1')].p_regime_shuffle.iloc[0])
    except Exception:
        sh = np.nan
    beat_base = np.isfinite(cand) and np.isfinite(base) and cand > base
    beat_null = np.isfinite(sh) and sh <= 0.05
    txt += ['', 'VERDICT on the declared rule:',
            '  beats the baseline (%.3f%% vs %.3f%% median year, team1): %s' % (cand, base, 'YES' if beat_base else 'NO'),
            '  beats its own shuffle null (p = %s, bar p <= 0.05): %s' % (('%.3f' % sh) if np.isfinite(sh) else 'n/a', 'YES' if beat_null else 'NO'),
            '  => the DC axis %s a routing place on this evidence.' % ('EARNS' if (beat_base and beat_null) else 'DOES NOT EARN')]
    open(out('layer3') + '.txt', 'w').write('\n'.join(txt) + '\n')
    print('\n'.join(txt), flush=True)
    return T


def stage_summary():
    B = pd.read_csv(out('selection') + '.csv') if _p.exists(out('selection') + '.csv') else pd.read_csv(out('battery') + '.csv')
    N = pd.read_csv(out('null') + '.csv') if _p.exists(out('null') + '.csv') else pd.DataFrame()
    L3 = pd.read_csv(out('layer3') + '.csv').fillna({'note': '', 'budget': ''}) if _p.exists(out('layer3') + '.csv') else pd.DataFrame()
    E = pd.read_csv(out('events') + '.csv')
    SB = pd.read_csv(out('subperiod') + '.csv') if _p.exists(out('subperiod') + '.csv') else pd.DataFrame()
    pick = B[B.selected].iloc[0] if 'selected' in B.columns and B.selected.any() else B.iloc[0]
    v = L3[(L3.budget == 'team1') & (L3.note == '')] if len(L3) else pd.DataFrame()
    def md_table(d, cols, fmt='%.3f'):
        d = d[cols]
        head = '| ' + ' | '.join(cols) + ' |'
        sep = '|' + '|'.join(['---'] * len(cols)) + '|'
        rows = ['| ' + ' | '.join((fmt % x) if isinstance(x, float) and np.isfinite(x) else str(x) for x in r) + ' |'
                for r in d.itertuples(index=False)]
        return '\n'.join([head, sep] + rows)
    md = ['# Layer 1 research round 1 — a trend axis from DIRECTIONAL CHANGE', '',
          '**%s.** Source: `results/research/RESEARCH_2026-11-09_part2_regime_taxonomies_and_nnfx_catalog.md`'
          ' family 7 (commit 9926531). Code: `code/dcaxis.py` (battery, no money metrics) and `code/dcroute.py`'
          ' (the Layer 3 money test). Every file in this round is dated and nothing was overwritten.' % STAMP, '',
          '## Why this construction',
          'The shipped trend axis fails its separation null in routing (HANDOFF_3 16.1b) and a **relative** cut cannot'
          ' see a two-year trend: a trend that creeps inside its own shrinking volatility never clears a trailing'
          ' yardstick. Directional change replaces the yardstick with an **absolute** one measured in event time.', '',
          '## The construction, declared before any result',
          '- per pair, track the running extreme of log price; a reversal of **theta** is an event, and the'
          ' continuation to the next reversal is the **overshoot**.',
          '- **theta is a constant per pair**: `m x` that pair\'s daily log-return stdev measured ONCE on the tuning'
          ' window (dates < 2016-01-01). Not trailing vol — a trailing yardstick shrinks inside a quiet trend and'
          ' recreates the very failure this exists to fix. Declared multiples **m = 0.5, 1.0, 1.5**.',
          '- score at bar t from bars through t-1 only: `mean(overshoot / theta)` over the last **K** completed'
          ' events, **K = 5, 10**. Secondary reads: bars in the current mode, events in the trailing 106 bars.',
          '- no label before K events exist (the shipped warm-up convention); the cut is learned on the tuning'
          ' window only; 2021 onward is sealed in the loader and absent from every file here.', '',
          '## Events and the degenerate-count guard (`dc_axis_events_%s.csv`)' % STAMP,
          'Completed events on the tuning window, per m: **min %d, median %.0f, max %d** (m=0.5); **%d / %.0f / %d**'
          ' (m=1.0); **%d / %.0f / %d** (m=1.5). The guard is 30 and **every (pair, m) clears it** — no cell was'
          ' re-picked. theta runs %.0f-%.0f bp of log price across the panel.'
          % tuple([int(E[E.m == 0.5].events_tuning.min()), E[E.m == 0.5].events_tuning.median(), int(E[E.m == 0.5].events_tuning.max()),
                   int(E[E.m == 1.0].events_tuning.min()), E[E.m == 1.0].events_tuning.median(), int(E[E.m == 1.0].events_tuning.max()),
                   int(E[E.m == 1.5].events_tuning.min()), E[E.m == 1.5].events_tuning.median(), int(E[E.m == 1.5].events_tuning.max()),
                   E.theta_bp.min(), E.theta_bp.max()]), '',
          '## The present-tense battery, all six variants (`dc_axis_battery_%s.csv`)' % STAMP,
          md_table(B.assign(m=B.m.map('%.1f'.__mod__), K=B.K.astype(int)),
                   ['m', 'K', 'separation_tuning', 'separation_holdout', 'median_run', 'flip_rate', 'coverage',
                    'corr_shipped_trend_score', 'corr_straightness', 'label_agreement_with_shipped'], '%.4f'), '',
          'The shipped trend axis on the same battery: separation **%.4f** tuning, **%.4f** holdout, median run'
          ' %.1f bars, flip rate %.4f. **Every DC variant separates the panel\'s own shape properties better than the'
          ' shipped axis does**, by 1.3x to 3.8x on the holdout.'
          % (B.shipped_separation_tuning.iloc[0], B.shipped_separation_holdout.iloc[0],
             B.shipped_median_run.iloc[0], B.shipped_flip_rate.iloc[0]), '',
          '**Correlation, reported plainly.** Spearman against the shipped trend score is **%.3f** on the selected'
          ' variant and 0.04-0.13 across all six; against the straightness measure %.3f; label agreement %.3f.'
          ' These are LOW, so this construction is **not** a confirmation of the shipped axis — it measures'
          ' something the shipped axis does not. That is recorded as a fact and it decides nothing on its own.'
          % (pick.corr_shipped_trend_score, pick.corr_straightness, pick.label_agreement_with_shipped), '']
    if len(N):
        md += ['## The 200-draw surrogate null (`dc_axis_null_%s.csv`)' % STAMP,
               'The construction, the theta measurement AND the cut are re-derived on every surrogate, so the null'
               ' prices the whole pipeline rather than the labelling step alone.', '',
               md_table(N.assign(m=N.m.map('%.1f'.__mod__), K=N.K.astype(int)),
                        ['kind', 'm', 'K', 'real', 'null_mean', 'null_p95', 'null_max', 'corrected', 'p_value'], '%.4f'), '']
    if len(SB):
        md += ['## Sub-period split, 2016-2019 vs 2020 only (`dc_axis_subperiod_%s.csv`)' % STAMP,
               '2021 onward is sealed, so the research doc\'s 2020-21 window does not exist here and was not used.', '',
               md_table(SB.assign(m=SB.m.map('%.1f'.__mod__), K=SB.K.astype(int)),
                        ['m', 'K', 'period', 'separation', 'median_run', 'flip_rate', 'share_trending'], '%.4f'), '']
    md += ['## Selection (`dc_axis_selection_%s.csv`)' % STAMP]
    if 'constraint_set_empty' in B.columns and bool(B.constraint_set_empty.iloc[0]):
        md += ['**The declared constraint set is empty and that is reported, not worked around.** The rule was: best'
               ' tuning separation SUBJECT TO (a) label runs consistent with the measured trending-episode duration'
               ' (g4_twoscore4 trending states, IS block: median %.1f bars, so a %.1f-%.1f band) and (b) a flip rate'
               ' no worse than the shipped axis (%.4f). Every variant inside the run band flips more often than the'
               ' shipped axis; the only variant that flips less often runs %.1f bars, outside the band. **No variant'
               ' satisfies both.**' % (B.measured_run_bars.iloc[0], B.run_band_lo.iloc[0], B.run_band_hi.iloc[0],
                                       B.shipped_flip_rate.iloc[0], float(B[B.flip_ok].median_run.iloc[0]) if B.flip_ok.any() else float('nan')),
               '', 'The fallback was declared in code before any money number existed: the **primary** is the best'
               ' tuning separation among the variants inside the measured run band, carrying its flip-rate violation'
               ' in the open, and the only flip-rate passer is reported beside it as a **sensitivity**. Neither was'
               ' re-chosen after the Layer 3 test.', '']
    md += ['**Primary: m = %.1f, K = %d**, cut %.4f, median run %.1f bars, flip rate %.4f (shipped %.4f), holdout'
           ' separation %.4f (shipped %.4f) — one holdout confirm, no second pick.'
           % (pick.m, pick.K, pick.cut, pick.median_run, pick.flip_rate, B.shipped_flip_rate.iloc[0],
              pick.separation_holdout, B.shipped_separation_holdout.iloc[0]), '']
    if len(v):
        md += ['## Layer 3: the money test (`dc_axis_layer3_%s.csv`)' % STAMP,
               'After the battery, never instead of it. Same 104 mode C candidates, same walk, same budgets, same'
               ' nulls as the baseline. team1 shown.', '',
               md_table(v, ['family', 'role', 'book', 'median_year_pct', 'worst_year_pct', 'dip95_pct',
                            'profit_factor', 'retention', 'p_random_entry', 'p_regime_shuffle'], '%.3f'), '']
        base = v[v.suffix == '_modec2_routed']; cand = v[v.suffix == '_dc_modec_dc']
        if len(base) and len(cand):
            b = float(base.median_year_pct.iloc[0]); c = float(cand.median_year_pct.iloc[0])
            try:
                sh = float(cand.p_regime_shuffle.iloc[0])
            except Exception:
                sh = float('nan')
            ok = (c > b) and np.isfinite(sh) and sh <= 0.05
            md += ['**Verdict on the declared rule.** The DC-routed mode C book makes **%.3f%%** median year against'
                   ' the baseline\'s **%.3f%%**, and its shuffled-label null gives **p = %s**. The bar was: beat the'
                   ' baseline AND beat the shuffle null. **%s** — %s.'
                   % (c, b, ('%.3f' % sh) if np.isfinite(sh) else 'n/a',
                      'BOTH CLEARED' if ok else 'NOT CLEARED',
                      'the DC axis earns a routing place on this evidence' if ok else
                      'the DC axis does not earn a routing place on this evidence, whatever its separation advantage'), '']
    md += ['## What this round establishes', '',
           '1. The DC construction **separates the panel\'s own shape properties far better than the shipped trend'
           ' axis** — a present-tense fact, holdout-confirmed once, with the null beside it.',
           '2. It is **not** a restatement of the shipped axis: the correlation is near zero.',
           '3. The declared run-length and flip-rate constraints **cannot both be met** by any of the six variants,'
           ' which is itself a finding about the construction: at this panel\'s volatility an absolute threshold'
           ' either flips too often or runs too long.',
           '4. Whether it belongs in the routing is decided by the Layer 3 table above and by nothing else.', '',
           '_Files: `dc_axis_{events,battery,episodes,null,subperiod,refit_vintages,selection,states,layer3}_%s.{csv,txt}`._' % STAMP]
    open(out('summary') + '.md', 'w').write('\n'.join(md) + '\n')
    print('wrote %s' % (out('summary') + '.md'), flush=True)


def stage_app():
    """Into app_data.json and app_ui.js, Advanced section, like everything else."""
    B = pd.read_csv(out('selection') + '.csv') if _p.exists(out('selection') + '.csv') else pd.read_csv(out('battery') + '.csv')
    N = pd.read_csv(out('null') + '.csv') if _p.exists(out('null') + '.csv') else pd.DataFrame()
    L3 = pd.read_csv(out('layer3') + '.csv').fillna({'note': '', 'budget': ''}) if _p.exists(out('layer3') + '.csv') else pd.DataFrame()
    SB = pd.read_csv(out('subperiod') + '.csv') if _p.exists(out('subperiod') + '.csv') else pd.DataFrame()
    for root in (_p.join(_R, 'app_data.json'), _p.join(ROOTOUT, 'app_data.json')):
        if not _p.exists(root):
            continue
        D = json.load(open(root))
        D['dc_axis'] = dict(
            stamp=STAMP,
            note=('Candidate trend axis from directional change. theta = m x the pair daily log-return stdev measured '
                  'ONCE on the tuning window; score = mean(overshoot/theta) over the last K completed events; one bar '
                  'of lag; 2021+ sealed. Present-tense battery only -- the money column lives in the Layer 3 table.'),
            battery=B.replace({np.nan: None}).to_dict('records'),
            null=(N.replace({np.nan: None}).to_dict('records') if len(N) else []),
            subperiod=(SB.replace({np.nan: None}).to_dict('records') if len(SB) else []),
            layer3=(L3[(L3.budget == 'team1') & (L3.note == '')].replace({np.nan: None}).to_dict('records') if len(L3) else []),
        )
        json.dump(D, open(root, 'w'))
        print('wired into %s' % root, flush=True)
    ui = _p.join(_R, 'app_ui.js'); s = open(ui).read()
    if 'dcFill' in s:
        print('app_ui.js already carries the DC tab', flush=True)
    else:
        # 1. the nav button, next to the other Layer 1 evidence tabs
        anchor = '<button role="tab" aria-selected="false" data-t="vd">Verdict</button>'
        assert s.count(anchor) == 1, 'app_ui.js: nav anchor not found'
        s = s.replace(anchor, anchor + '\n<button role="tab" aria-selected="false" data-t="dc">DC axis</button>')
        # 2. the section, with one container the renderer fills
        sec = ('\n<section id="dc" hidden>\n'
               '<h3>Candidate trend axis: directional change</h3>\n'
               '<div class="note">A trend axis built on an ABSOLUTE reversal threshold in event time, aimed at the\n'
               'known weakness: the shipped trend axis fails its separation null in routing, and a relative cut cannot\n'
               'see a two-year trend. theta is a CONSTANT per pair &mdash; m &times; that pair\'s daily log-return stdev\n'
               'measured once on the tuning window, never trailing vol. Score = mean(overshoot/theta) over the last K\n'
               'completed events, lagged one bar. Six variants were declared before any result; 2021 onward is sealed.\n'
               'A candidate, not shipped: it earns a routing place only by beating the mode C baseline AND its own\n'
               'shuffle null, which is the Layer 3 table at the bottom.</div>\n'
               '<div id="dcbody"></div>\n</section>\n')
        tail = '<section id="vd" hidden>'
        s = s.replace(tail, sec.lstrip('\n') + tail, 1)
        # 3. register in TABS (Advanced only -- NOT in DEFAULT_TABS)
        old_t = "'ex','pt','hz','rd','xd','pc','gl','ar','vd'];"
        assert s.count(old_t) == 1, 'app_ui.js: TABS list not found'
        s = s.replace(old_t, "'ex','pt','hz','rd','xd','pc','gl','ar','vd','dc'];")
        # 4. render on first open, like the other heavy tabs
        old_s = "   if(t==='tv')initTrades();};"
        assert s.count(old_s) == 1, 'app_ui.js: show() hook not found'
        s = s.replace(old_s, "   if(t==='tv')initTrades();\n   if(t==='dc')dcFill();};")
        # 5. the renderer
        s = s.rstrip() + """

// ---- DC TREND AXIS (Layer 1 research round 1, 2026-11-09). Advanced only until it earns more.
function dcFill(){
  const d=(window.D&&D.dc_axis)||null, el=document.getElementById('dcbody');
  if(!el) return;
  if(!d){el.innerHTML='<p class="note">No dc_axis section in this app_data.json build.</p>';return;}
  const num=v=>v===null||v===undefined||v===''?'':(typeof v==='number'
      ?(Math.abs(v)>=1000?v.toFixed(0):Math.abs(v)<0.0001&&v!==0?v.toExponential(1):v.toFixed(4)):String(v));
  const tbl=(rows,cols,cap)=>{
    if(!rows||!rows.length) return '<h4>'+cap+'</h4><p class="note">(not built in this run)</p>';
    return '<h4>'+cap+'</h4><div class="tw"><table><thead><tr>'
      +cols.map(c=>'<th>'+c+'</th>').join('')+'</tr></thead><tbody>'
      +rows.map(r=>'<tr>'+cols.map(c=>'<td>'+num(r[c])+'</td>').join('')+'</tr>').join('')
      +'</tbody></table></div>';};
  el.innerHTML='<p class="note">'+(d.note||'')+' Built '+(d.stamp||'')+'.</p>'
    +tbl(d.battery,['m','K','cut','separation_tuning','separation_holdout','median_run','flip_rate','coverage',
                    'corr_shipped_trend_score','corr_straightness','label_agreement_with_shipped','eligible','selected'],
         'Present-tense battery, six declared variants (no money metric)')
    +tbl(d.null,['kind','m','K','real','null_mean','null_p95','null_max','corrected','p_value'],
         '200-draw surrogate null (construction, theta and cut re-derived on every draw)')
    +tbl(d.subperiod,['m','K','period','separation','median_run','flip_rate','share_trending'],
         'Sub-period split: 2016-2019 vs 2020 only (2021+ sealed)')
    +tbl(d.layer3,['family','role','book','median_year_pct','worst_year_pct','dip95_pct','profit_factor',
                   'retention','p_random_entry','p_regime_shuffle'],
         'Layer 3 money test, team1 \u2014 the only place money appears in this round');}
"""
        open(ui, 'w').write(s)
        print('app_ui.js: nav button, section, TABS entry, show() hook and dcFill() added (%d bytes)' % len(s), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', required=True, choices=['table', 'summary', 'app'])
    a = ap.parse_args()
    print('=== dcroute %s ===' % a.stage, flush=True)
    {'table': stage_table, 'summary': stage_summary, 'app': stage_app}[a.stage]()
    print('DC ROUTE STAGE %s COMPLETE' % a.stage.upper(), flush=True)


if __name__ == '__main__':
    main()
