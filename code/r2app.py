import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""THE LAYER 2 RESTART TAB (HANDOFF 0l).  The third wiring place.

Owns the `l2_restart` section of app_data.json and the "L2 restart" tab in
app_ui.js, so a cold pipeline run rebuilds both instead of deleting them --
which is exactly what bundle.py did to the four November research sections
before code/appsections.py existed.

    python3 code/r2app.py --stage app
"""
import json, glob
import numpy as np, pandas as pd

NL = '\n'
STAMP = '2026-11-16'


def _recs(path, cols=None, head=None):
    if not os.path.exists(path):
        return []
    d = pd.read_csv(path)
    if cols:
        d = d[[c for c in cols if c in d.columns]]
    if head:
        d = d.head(head)
    return json.loads(d.replace({np.nan: None}).to_json(orient='records'))


def curve_digest(mode, tag, per=14):
    """A readable slice of the curve: `per` cuts evenly spaced across the full
    swept range, pooled over the five windows, per stream."""
    p = os.path.join(ROOTOUT, 'r2gate1_pooled_mode%s_%s.csv' % (mode, tag))
    if not os.path.exists(p):
        return []
    d = pd.read_csv(p)
    out = []
    for s, g in d.groupby('stream', sort=False):
        g = g.reset_index(drop=True)
        idx = np.unique(np.linspace(0, len(g) - 1, per).astype(int))
        out.append(g.loc[idx])
    D = pd.concat(out, ignore_index=True)
    return json.loads(D.replace({np.nan: None}).to_json(orient='records'))


def stage_app():
    sec = dict(
        stamp=STAMP,
        note=('Layer 2 restarted from mode A up (HANDOFF 0l). The gate 1 on disk cut on '
              'W2+W3 pooled = 2011-2020, i.e. on every year Layer 2 then called blind, and '
              'charged no costs. The honest gate 1 scores every combination at defaults with '
              'costs on, banks each trade by the calendar year of its ENTRY bar, and CUTS ON '
              'TUNE YEARS ONLY -- grade and trade years are measured at the same time and take '
              'no part in the selection. Four streams, none selected on: trend and chop, each '
              'routed and always-on. The cut is swept over its whole range; Jack picks from the '
              'curve. Nothing from the old Layer 2 is deleted.'),
        library=_recs(os.path.join(ROOTOUT, 'r2_step1_library.csv')),
        modes=_recs(os.path.join(ROOTOUT, 'r2_step1_modes.csv')),
        timing=_recs(os.path.join(ROOTOUT, 'r2_step1_timing.csv')),
        gate1_original=_recs(os.path.join(ROOTOUT, 'r2_step1_gate1_original.csv')),
        contaminations=_recs(os.path.join(ROOTOUT, 'r2_step1_contaminations.csv')),
        superseded=_recs(os.path.join(ROOTOUT, 'r2_superseded_files.csv')),
        parity=[{'mode': m, 'comparisons': len(d), 'mismatches': int(d.mismatch.sum())}
                for m in 'ABC'
                for d in [pd.read_csv(os.path.join(ROOTOUT, 'r2gate1_parity_mode%s.csv' % m))]
                if os.path.exists(os.path.join(ROOTOUT, 'r2gate1_parity_mode%s.csv' % m))],
        rankcorr={m: _recs(os.path.join(ROOTOUT, 'r2gate1_rankcorr_mode%s_full.csv' % m)) for m in 'ABC'},
        curve={m: curve_digest(m, 'full') for m in 'ABC'},
    )
    # ---- THE READS SECTION: A1..A6, B1 and C1..C3.
    # STANDING RULE: every result gets an app tab. These reports were delivered
    # as markdown and csv on 24 Nov and had no tab until this section existed;
    # the rule is not satisfied by a file on disk.
    RD = os.path.join(ROOTOUT, 'r2reads')
    def rd(name, cols=None, head=60):
        return _recs(os.path.join(RD, name), cols=cols, head=head)
    sec['reads'] = dict(
        note=('The read-only passes off the banked gate 2 and gate 3 results. '
              'Every number here comes from a csv in results/r2reads and every '
              'report names its own provenance with an md5.'),
        b1_winners_era={m: rd('mode%s_b1winners_era.csv' % m,
                              ['sid', 'R_new6', 'prop_return_new6'])
                        for m in 'AB'},
        cond3=_recs(os.path.join(ROOTOUT, 'r2gate2_cond3_crosswalk.csv'),
                    cols=['mode', 'winner', 'year', 'base5_R', 'ext11_R', 'dR',
                          'base5_n', 'ext11_n', 'dn', 'base5_cfg', 'ext11_cfg',
                          'cfg_same'], head=50),
        gate2_vs_gate3=_recs(os.path.join(ROOTOUT, 'r2gate2',
                                          'gate2_vs_gate3_peryear.csv'), head=50),
        b1_winners={m: rd('mode%s_b1winners.csv' % m,
                          ['sid', 'stream', 'R_new6', 'dd_new6', 't_new6',
                           'years_pos_new6', 'prop_return_new6', 'R_all11',
                           'dd_all11', 'prop_return_all11'])
                    for m in 'AB'},
        a4_capcurve={m: rd('mode%s_a4_capcurve.csv' % m) for m in 'AB'},
        a4_attribution={m: rd('mode%s_a4_attribution.csv' % m,
                              ['rule', 'step', 'book', 'budget',
                               'worst10_mean_pct', 'worst10_largest_leg_share',
                               'worst10_top_currency',
                               'allday_largest_leg_share', 'worst_dip_pct',
                               'worst_dip_largest_leg_share'])
                       for m in 'AB'},
        a5_delta={m: rd('mode%s_a5_delta_strategy.csv' % m) for m in 'AB'},
        a5_spreads={m: rd('mode%s_a5_spreads_by_pair.csv' % m) for m in 'AB'},
        a5_overlay={m: rd('mode%s_a5_overlay_curve.csv' % m) for m in 'AB'},
        c1_data=rd('c1_data_availability.csv', head=20),
        c3_fix={e: rd('c3_fix_%s.csv' % e, head=0) for e in ('measure',)},
    )
    # C3 is rolled up rather than shipped raw: 1,344 rows per era is a table
    # nobody reads, and the roll-up is the currency-against-basket figure.
    try:
        import c3hourly as _C3
        import pandas as _pd
        for era in ('measure', 'confirm'):
            f_ = os.path.join(RD, 'c3_hours_%s.csv' % era)
            if os.path.exists(f_):
                g = _C3.roll_up(_pd.read_csv(f_), ['currency', 'hour_ny'])
                g = g.reindex(g.move_bp.abs().sort_values(ascending=False).index)
                sec['reads']['c3_hours_%s' % era] = json.loads(
                    g.head(40)[['currency', 'hour_ny', 'n', 'pairs', 'move_bp',
                                'spread_bp', 'move_net_bp', 't_across_pairs']]
                    .replace({np.nan: None}).to_json(orient='records'))
    except Exception as e:
        sec['reads']['c3_error'] = '%s: %s' % (type(e).__name__, e)
    for k in ('b1_winners', 'b1_winners_era', 'a4_capcurve', 'a4_attribution', 'a5_delta',
              'a5_spreads', 'a5_overlay'):
        sec['reads'][k] = {m: v for m, v in sec['reads'][k].items() if v}
    sec['reads'].pop('c3_fix', None)
    # ---- THE NNFX BUILD SECTION (HANDOFF 0m). Standing rule: every result
    # gets an app tab, and a markdown file on disk does not satisfy it.
    ND = os.path.join(ROOTOUT, 'nnfx')
    def nd(name, cols=None, head=80):
        return _recs(os.path.join(ND, name), cols=cols, head=head)
    sec['nnfx'] = dict(
        note=('Layer 2 rebuilt the NNFX way: one algorithm, one piece at a '
              'time, few candidates per stage. Eleven-step walk; unseen trade '
              'years 2010-2015 are the BUILD evidence and 2016-2020 are '
              'computed and stored but NOT shown until the confirm is called.'),
        power=nd('power_test_blindness.csv'),
        power_floors=nd('power_test_true_floors.csv'),
        scorer=nd('scorer_consequence.csv'),
        stage1_c1_flip=nd('stage1_c1_flip_only_walkbuild.csv'),
        stage1_c1_risk=nd('stage1_c1_canonical_risk_walkbuild.csv'),
        stage1_base_flip=nd('stage1_base_flip_only_walkbuild.csv'),
        stage1_base_risk=nd('stage1_base_canonical_risk_walkbuild.csv'),
        select_c1_flip=nd('stage1_c1_flip_only_select.csv'),
        select_c1_risk=nd('stage1_c1_canonical_risk_select.csv'),
        select_base_flip=nd('stage1_base_flip_only_select.csv'),
        select_base_risk=nd('stage1_base_canonical_risk_select.csv'),
        market=nd('market_switch_corr.csv'),
        ledger_n=(sum(1 for _ in open(os.path.join(ND, 'CANDIDATE_LEDGER.csv'))) - 1
                  if os.path.exists(os.path.join(ND, 'CANDIDATE_LEDGER.csv')) else 0),
    )
    # ---- STAGE 1 R2 (the rerun with all eight items applied)
    sec['nnfx']['r2'] = dict(
        note=('Stage 1 R2 supersedes stage 1. Costs charged in a declared '
              'notional, true chronological drawdowns on the daily '
              'mark-to-market series, ambiguous bars resolved from the hourly '
              'bid/ask path, eleven unseen trade years 2005-2015 for the fixed '
              'settings, three risk plans declared in advance, a '
              'block-bootstrap t beside the yearly t, and luck floors from the '
              'random-entry null rather than from a formula.'),
        ambiguity=nd('stage1r2_ambiguity_delta.csv'),
        power_boot=nd('power_test_bootstrap.csv'),
        zero_edge=nd('condition4_zero_edge.csv', head=40),
    )
    for kind in ('c1', 'base'):
        for v in ('flip_only', 'jack', 'textbook'):
            sec['nnfx']['r2']['sum_%s_%s' % (kind, v)] = nd(
                'stage1r2_%s_%s_summary.csv' % (kind, v),
                cols=['indicator', 'setting', 'n_entered', 'trades_per_year',
                      'mean_bars', 'R_gross_per_trade', 'R_net_per_trade',
                      'cost_per_trade', 'R_net_per_year', 'years',
                      'years_positive', 'worst_year', 'worst_dip_R',
                      't_yearly', 't_block_boot', 'null_p',
                      'floor_emp_alone', 'floor_emp_best_of_family'], head=120)
            sec['nnfx']['r2']['sel_%s_%s' % (kind, v)] = nd(
                'stage1r2_%s_%s_select.csv' % (kind, v))
    sec['nnfx']['r2'] = {k: v for k, v in sec['nnfx']['r2'].items()
                         if not (isinstance(v, list) and not v)}
    # ---- STAGE 2 (the baseline added to C1) and ENGINE AUDIT 2.
    # Jack's picks, 24 Nov. The side filter is in every ruleset but the
    # control, so the three other rules are INCREMENTS over it -- the note
    # carries that, because a reader comparing `side_dist` against the bare C1
    # would read the side filter's effect into the distance rule.
    sec['nnfx']['s2'] = dict(
        note=('Stage 2: the baseline added to C1, on Jack\'s picks '
              '(ichimoku / schaff_trend_cycle / halftrend plus the rolling '
              'top 3; sma / hma / t3). jack plan is the main version, '
              'textbook beside it. The baseline SIDE FILTER cannot be '
              'switched off -- every entry route gates on agreement, which '
              'contains side -- so `side` is the floor and the distance, '
              'cross-entry and cross-exit rows are INCREMENTS OVER IT, not '
              'over the bare C1.'),
        report=nd('stage2_picks_report.csv',
                  cols=['c1', 'base', 'variant', 'ruleset', 'R_net_per_year',
                        'R_net_per_trade', 'R_gross_per_trade',
                        'trades_per_year', 'mean_bars', 'years_positive',
                        'worst_year', 'worst_dip_R', 'R_per_year_per_dip',
                        't_yearly', 't_block_boot', 'null_p',
                        'clears_alone', 'clears_best_of_family'], head=160),
        paired=nd('stage2_picks_paired.csv',
                  cols=['c1', 'base', 'variant', 'ruleset', 'days',
                        'R_without', 'R_with', 'delta_R', 'delta_R_per_year',
                        'delta_t_block_boot', 'delta_t_yearly',
                        'years_delta_positive', 'days_with_only',
                        'days_without_only'], head=160),
        rolling=nd('stage2_rolling_sweep.csv', head=120),
        rolling_picks=nd('stage2_rolling_picks.csv', head=80),
        costcap=nd('stage2_costcap.csv', head=200),
        fewer=nd('stage2_fewer.csv', head=200),
        prop=nd('stage2_picks_prop.csv', head=200),
        neutral=nd('stage2_picks_neutralcheck.csv', head=40),
        grid=nd('stage2_picks_grid.csv', head=200),
    )
    sec['nnfx']['audit2'] = dict(
        note=('Engine audit 2, measurement only. The daily bar is '
              '(16:00 NY D-1, 16:00 NY D], NOT 17:00. Overnight financing is '
              'charged NOWHERE, and its mean on these candidates is POSITIVE, '
              'so adding it would flatter them. Tick volume is usable from '
              '2005 and is a tick COUNT, not traded size.'),
        fillprice=nd('audit2_fillprice.csv', head=160),
        financing=nd('audit2_financing.csv', head=40),
        cost_by_pair=nd('audit2_cost_by_pair.csv', head=40),
        cost_by_year=nd('audit2_cost_by_year.csv', head=40),
        tickvolume=nd('audit2_tickvolume.csv', head=200),
    )
    for _k in ('s2', 'audit2'):
        sec['nnfx'][_k] = {k: v for k, v in sec['nnfx'][_k].items()
                           if not (isinstance(v, list) and not v)}
    sec['nnfx'] = {k: v for k, v in sec['nnfx'].items()
                   if not (isinstance(v, list) and not v)}

    sec['curve'] = {k: v for k, v in sec['curve'].items() if v}
    sec['rankcorr'] = {k: v for k, v in sec['rankcorr'].items() if v}
    for root in (os.path.join(_R, 'app_data.json'), os.path.join(ROOTOUT, 'app_data.json')):
        if not os.path.exists(root):
            continue
        D = json.load(open(root))
        D['l2_restart'] = sec
        json.dump(D, open(root, 'w'))
        print('wired into %s' % root, flush=True)

    ui = os.path.join(_R, 'app_ui.js')
    s = open(ui).read()
    # NOT `'r2Fill' in s` -- tr2Fill contains it as a substring and the guard
    # silently skipped the whole wiring on the first run.
    if 'const r2Fill=' in s:
        print('app_ui.js already carries the L2 restart tab', flush=True)
        return
    anchor = '<button role="tab" aria-selected="false" data-t="tq">Trend quality</button>'
    assert s.count(anchor) == 1, 'app_ui.js: nav anchor not found'
    s = s.replace(anchor, anchor + NL + '<button role="tab" aria-selected="false" data-t="r2">L2 restart</button>')
    body = ('<section id="r2" hidden>' + NL +
            '<h3>Layer 2 restart: the honest gate 1</h3>' + NL +
            '<div class="note">The gate 1 on disk took its score over 2011-2020 -- every year Layer 2' + NL +
            'afterwards called blind -- and charged no costs, so its survivors were chosen on the years' + NL +
            'their record was then quoted on. This is the rebuild. Every combination is scored at' + NL +
            'defaults with costs on; each trade is banked by the calendar year of its entry bar; the cut' + NL +
            'reads tune years only. Four streams are measured and none is selected on. The cut is swept' + NL +
            'over its whole range and reported as a curve, with the identity null beside it. Nothing from' + NL +
            'the old Layer 2 was deleted.</div>' + NL + '<div id="r2body"></div>' + NL + '</section>' + NL)
    s = s.replace('<section id="tq" hidden>', body + '<section id="tq" hidden>', 1)
    old_t = "'ex','pt','hz','rd','xd','pc','gl','ar','vd','dc','tr2','tq','cw'];"
    assert s.count(old_t) == 1, 'app_ui.js: TABS list not found'
    s = s.replace(old_t, "'ex','pt','hz','rd','xd','pc','gl','ar','vd','dc','tr2','tq','r2','cw'];")
    old_s = "   if(t==='tq')tqFill();"
    assert s.count(old_s) == 1, 'app_ui.js: show() hook not found'
    s = s.replace(old_s, old_s + NL + "   if(t==='r2')r2Fill();")
    s = s.rstrip() + NL + TAB_JS
    open(ui, 'w').write(s)
    print('app_ui.js: L2 restart tab added', flush=True)


TAB_JS = """
const r2Fill=()=>{const el=document.getElementById('r2body');if(!el||el.dataset.done)return;
 const D=(window.DATA||{}).l2_restart;if(!D){el.innerHTML='<div class="note">no restart section in app_data.json</div>';return;}
 const tbl=(rows,cols,title)=>{if(!rows||!rows.length)return '';
  const c=cols||Object.keys(rows[0]);
  return '<h4>'+title+'</h4><div style="overflow-x:auto"><table><thead><tr>'+c.map(k=>'<th>'+k+'</th>').join('')+'</tr></thead><tbody>'+
   rows.map(r=>'<tr>'+c.map(k=>{let v=r[k];if(typeof v==='number')v=Math.abs(v)>=1000?v.toLocaleString():(Number.isInteger(v)?v:v.toFixed(4));return '<td>'+(v===null||v===undefined?'':v)+'</td>';}).join('')+'</tr>').join('')+
   '</tbody></table></div>';};
 let h='<div class="note">'+D.note+'</div>';
 h+=tbl(D.modes,['mode','exit_rule','uses_exit_slot','c1','c2','vol','base','exit_ind','combinations'],'The three modes, exactly one active per test');
 h+=tbl(D.contaminations,['n','name','touches_gate1'],'Which faults touched gate 1');
 h+=tbl(D.parity,null,'The _r2 code path against the shipped Scorer (0 mismatches required)');
 h+=tbl(D.timing,['mode','combinations','basis','per_combo_s','core_hours','mac_hours','bank_gb'],'Measured cost of a full honest gate 1');
 Object.keys(D.curve||{}).forEach(m=>{h+=tbl(D.curve[m],['stream','cut_tune_R','n_pass','pct_pass','n_families','n_lone_survivor_families','grade_R_pass','trade_R_pass','trade_R_fail','null_trade_R_mean','null_p_one_sided'],'Mode '+m+' gate 1 curve, pooled over the five windows (cut reads tune years only)');});
 Object.keys(D.rankcorr||{}).forEach(m=>{h+=tbl(D.rankcorr[m],['window','stream','n_eligible','spearman_tune_to_trade','p'],'Mode '+m+': does the tune-year rank survive to the trade year?');});
 h+=tbl(D.superseded,null,'Superseded, headed, kept in full');
 el.innerHTML=h;el.dataset.done='1';};
"""


if __name__ == '__main__':
    stage_app()
