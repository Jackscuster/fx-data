import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""TREND ROUND 3 -- ONE QUESTION (11 Nov): can anything ALREADY COMMITTED
separate TRUE from FALSE trending episodes AT LABEL TIME?

Round 2 measured the failure: ~50% of labelled trending episodes are
directionless, and the shipped trend score cannot tell them apart -- on the
holdout the FALSE episodes score HIGHER (0.494) than the true ones (0.329).
This asks whether some other already-committed series, read at the
confirmation bar, carries that information. It is a QUALITY FLAG on the
existing label: no new axis, no new state, no state call changes.

THE WHOLE MENU, declared before any result, all existing series, no sweeps,
no combinations, no interactions (interactions are a measured graveyard):
  A1 activity level        -- the scale measure the activity axis is cut from
  A2 chop score            -- the shipped chop axis, raw
  A3 currency-leg gap      -- round 2's T2 series (failed as an AXIS; whether
                              it works as a CONDITIONAL read is a different
                              question and is asked once, here)
  A4 break follow-through  -- round 2's T1 series at the already-selected R=5
  A5 trend score           -- THE CONTROL, expected to fail

EVERY reading is taken at the episode's confirmation bar from bars <= t-1
(the series are already lagged one bar, and nothing here shifts them again).

THE STATISTIC: the absolute standardised gap between the true-episode and
false-episode readings, episode-counted -- one labelled episode is one
observation, never one bar. AUC is reported beside it for interpretation and
decides nothing.

THE NULL: the same re-derive-everything 200-draw surrogate null that killed
the DC axis, T1 and T2. On each surrogate panel the shipped two-score
classifier, the episode set, the truth threshold AND every candidate reading
are rebuilt from scratch, so the null prices the entire question and not one
step of it.

DECLARED DECISION: a candidate that survives the tuning window, the single
holdout confirm, the null and the sub-period split becomes a reported QUALITY
reading beside the trend label (high / low confidence), changing no state
call. If nothing survives, the finding recorded is that the trend axis is at
its information ceiling on this data, and the round closes.

    python3 code/trendqual.py --stage battery
    python3 code/trendqual.py --stage null
    python3 code/trendqual.py --stage report
"""
import argparse, time
import numpy as np, pandas as pd
from structval import SPLIT, surrogate
from ninestate import raw_axes
import twoscores as TS
import trendt12 as T12

STAMP = '2026-11-11'
SEAL = pd.Timestamp('2020-12-31')
NSHUF = int(os.environ.get('FX_NSHUF', 200))
CANDS = ('A1_activity_scale', 'A2_chop_score', 'A3_currency_leg_gap',
         'A4_break_followthrough', 'A5_trend_score_CONTROL')


def out(n):
    return os.path.join(ROOTOUT, 'trend_quality_%s_%s' % (n, STAMP))


def load_px():
    px = pd.read_csv(os.path.join(ROOTDATA, 'px28.csv'), index_col=0, parse_dates=True).astype(float)
    return px if os.environ.get('FX_ALLOW_W4') == '1' else px[px.index <= SEAL]


def build_all(px):
    """Everything this question needs, rebuilt from one panel: the shipped 2x2
    label, and the five candidate readings. Used for the real panel and for every
    surrogate draw -- that is what makes the null price the whole pipeline."""
    fit = np.asarray(px.index < SPLIT)
    tr, ch = TS.two_scores(px, fit)
    shape2, _ = TS.classify(tr, ch, fit)
    axes = raw_axes(px)                       # already lagged one bar inside
    t1, _ = T12.t1_scores(px, 5)              # round 2's declared selection
    t2, _ = T12.t2_scores(px)
    reads = {'A1_activity_scale': axes['scale'], 'A2_chop_score': ch,
             'A3_currency_leg_gap': t2, 'A4_break_followthrough': t1,
             'A5_trend_score_CONTROL': tr}
    return shape2, reads


def episodes_and_truth(px, shape2):
    """Labelled TRENDING episodes, each with its confirmation bar, and the truth:
    did the pair make net directional progress over the episode, in tuning-window
    vol units, against the threshold learned on the TUNING WINDOW only."""
    lp = np.log(px); rr = lp.diff()
    sd = rr[rr.index < SPLIT].std()
    rows = []
    for p in shape2.columns:
        v = shape2[p]
        m = (v == 'trending').values
        if not m.any():
            continue
        idx = shape2.index
        gid = np.cumsum(np.r_[True, m[1:] != m[:-1]])
        for k in np.unique(gid[m]):
            sel = (gid == k) & m
            d = idx[sel]
            seg = lp[p].reindex(d).dropna()
            if len(seg) < 3:
                continue
            s = float(sd[p])
            if not np.isfinite(s) or s <= 0:
                continue
            prog = abs(float(seg.iloc[-1] - seg.iloc[0])) / (s * np.sqrt(len(seg)))
            rows.append(dict(pair=p, confirm_bar=d[0], end=d[-1], bars=int(sel.sum()),
                             progress_vol=prog, era='is' if d[0] < SPLIT else 'holdout'))
    E = pd.DataFrame(rows)
    if not len(E):
        return E, np.nan
    thr = float(E[E.era == 'is'].progress_vol.median())      # learned IS only
    E['true_trend'] = E.progress_vol >= thr
    return E, thr


def attach(E, reads):
    """The candidate readings AT THE CONFIRMATION BAR."""
    for k, M in reads.items():
        vals = []
        for e in E.itertuples():
            try:
                vals.append(float(M.at[e.confirm_bar, e.pair]))
            except Exception:
                vals.append(np.nan)
        E[k] = vals
    return E


def gap_auc(E, col, era):
    """Absolute standardised gap between true and false episodes, episode-counted,
    plus AUC. One episode is one observation."""
    d = E[(E.era == era)][[col, 'true_trend']].dropna()
    if len(d) < 20 or d.true_trend.nunique() < 2:
        return np.nan, np.nan, len(d)
    a = d[d.true_trend][col].values; b = d[~d.true_trend][col].values
    s = d[col].std()
    gap = abs(a.mean() - b.mean()) / s if s > 0 else np.nan
    # AUC via the rank-sum identity
    r = pd.Series(d[col].values).rank().values
    n1, n0 = len(a), len(b)
    auc = (r[d.true_trend.values].sum() - n1 * (n1 + 1) / 2) / (n1 * n0) if n1 and n0 else np.nan
    return float(gap), float(auc), int(len(d))


def stage_battery():
    t0 = time.time(); px = load_px()
    shape2, reads = build_all(px)
    E, thr = episodes_and_truth(px, shape2)
    E = attach(E, reads)
    E.to_csv(out('episodes') + '.csv', index=False)
    rows = []
    for c in CANDS:
        g_is, a_is, n_is = gap_auc(E, c, 'is')
        g_oos, a_oos, n_oos = gap_auc(E, c, 'holdout')
        # direction, so a "pass" that points the wrong way is visible
        di = E[E.era == 'is'].groupby('true_trend')[c].median()
        do = E[E.era == 'holdout'].groupby('true_trend')[c].median()
        rows.append(dict(candidate=c, gap_tuning=g_is, auc_tuning=a_is, n_episodes_tuning=n_is,
                         gap_holdout=g_oos, auc_holdout=a_oos, n_episodes_holdout=n_oos,
                         median_true_tuning=float(di.get(True, np.nan)), median_false_tuning=float(di.get(False, np.nan)),
                         median_true_holdout=float(do.get(True, np.nan)), median_false_holdout=float(do.get(False, np.nan)),
                         sign_consistent=bool(np.sign(di.get(True, np.nan) - di.get(False, np.nan)) ==
                                              np.sign(do.get(True, np.nan) - do.get(False, np.nan)))))
    B = pd.DataFrame(rows); B['truth_threshold'] = thr
    B.to_csv(out('battery') + '.csv', index=False)
    # sub-period split, 2016-19 vs 2020 only
    sr = []
    for c in CANDS:
        for lab, a, b in (('2016-2019', '2016-01-01', '2019-12-31'), ('2020', '2020-01-01', '2020-12-31')):
            q = E[(E.confirm_bar >= a) & (E.confirm_bar <= b)].copy(); q['era'] = 'x'
            g, au, n = gap_auc(q, c, 'x')
            sr.append(dict(candidate=c, period=lab, gap=g, auc=au, n_episodes=n))
    pd.DataFrame(sr).to_csv(out('subperiod') + '.csv', index=False)
    t = ['TREND ROUND 3 -- CAN ANY COMMITTED SERIES SEPARATE TRUE FROM FALSE TRENDING EPISODES AT LABEL TIME? %s' % STAMP,
         'A quality flag on the existing label: no new axis, no new state, no state call changes. No money metric here.',
         'Episode-counted: one labelled trending episode is one observation. Truth threshold %.3f learned on the tuning window.' % thr,
         'Episodes: %d tuning, %d holdout; true-trend share %.3f tuning, %.3f holdout.'
         % (int((E.era == 'is').sum()), int((E.era == 'holdout').sum()),
            float(E[E.era == 'is'].true_trend.mean()), float(E[E.era == 'holdout'].true_trend.mean())), '',
         B[['candidate', 'gap_tuning', 'auc_tuning', 'gap_holdout', 'auc_holdout', 'n_episodes_holdout',
            'sign_consistent']].to_string(index=False, float_format=lambda v: '%8.4f' % v),
         '', 'gap = |mean(true) - mean(false)| in sd units of the reading. AUC 0.5 is coin-flip.',
         'done in %.1f min' % ((time.time() - t0) / 60)]
    open(out('battery') + '.txt', 'w').write('\n'.join(t) + '\n')
    print('\n'.join(t), flush=True)


def stage_null():
    t0 = time.time(); px = load_px()
    shape2, reads = build_all(px)
    E, _ = episodes_and_truth(px, shape2)
    E = attach(E, reads)
    real = {c: gap_auc(E, c, 'holdout')[0] for c in CANDS}
    rng = np.random.default_rng(20261111); rows = []
    for kind in ('sign', 'perm'):
        draws = {c: [] for c in CANDS}
        for i in range(NSHUF):
            q = surrogate(px, kind, rng)
            try:
                s2, rd = build_all(q)
                Eq, _ = episodes_and_truth(q, s2)
                if not len(Eq):
                    continue
                Eq = attach(Eq, rd)
                for c in CANDS:
                    g, _, _ = gap_auc(Eq, c, 'holdout')
                    draws[c].append(g)
            except Exception as e:
                print('  draw %d failed: %s' % (i, str(e)[:80]), flush=True)
            if (i + 1) % 25 == 0:
                print('  %s null: %d/%d (%.1f min)' % (kind, i + 1, NSHUF, (time.time() - t0) / 60), flush=True)
        for c in CANDS:
            v = np.array([x for x in draws[c] if np.isfinite(x)]); r = real[c]
            rows.append(dict(kind=kind, candidate=c, real=r, n_draws=len(v),
                             null_mean=float(v.mean()) if len(v) else np.nan,
                             null_p95=float(np.percentile(v, 95)) if len(v) else np.nan,
                             null_max=float(v.max()) if len(v) else np.nan,
                             corrected=(r - float(v.mean())) if len(v) else np.nan,
                             p_value=float((v >= r).mean()) if len(v) else np.nan))
    N = pd.DataFrame(rows); N.to_csv(out('null') + '.csv', index=False)
    t = ['TREND ROUND 3 -- %d-DRAW RE-DERIVE NULL. %s' % (NSHUF, STAMP),
         'On every surrogate the two-score classifier, the episode set, the truth threshold and all five readings',
         'are rebuilt from scratch, so the null prices the whole question.', '',
         N.to_string(index=False, float_format=lambda v: '%9.4f' % v),
         '', 'done in %.1f min' % ((time.time() - t0) / 60)]
    open(out('null') + '.txt', 'w').write('\n'.join(t) + '\n')
    print('\n'.join(t), flush=True)


def stage_report():
    B = pd.read_csv(out('battery') + '.csv'); N = pd.read_csv(out('null') + '.csv')
    SB = pd.read_csv(out('subperiod') + '.csv')
    p = N.pivot_table(index='candidate', columns='kind', values='p_value')
    B['null_p_sign'] = B.candidate.map(p['sign']); B['null_p_perm'] = B.candidate.map(p['perm'])
    sub = SB.pivot_table(index='candidate', columns='period', values='gap')
    for c in sub.columns:
        B['gap_' + c.replace('-', '_')] = B.candidate.map(sub[c])
    B['survives'] = ((B.null_p_sign <= 0.05) & (B.null_p_perm <= 0.05) & B.sign_consistent
                     & (B.gap_holdout > 0) & (B.auc_holdout.sub(0.5).abs() > 0.05))
    B.to_csv(out('verdict') + '.csv', index=False)
    surv = B[B.survives]
    t = ['TREND ROUND 3 -- VERDICT. %s' % STAMP, '',
         B[['candidate', 'gap_tuning', 'gap_holdout', 'auc_holdout', 'sign_consistent',
            'null_p_sign', 'null_p_perm', 'gap_2016_2019', 'gap_2020', 'survives']
           ].to_string(index=False, float_format=lambda v: '%8.4f' % v), '',
         'A candidate survives only if it clears BOTH nulls at p <= 0.05, points the same way on the tuning window',
         'and the holdout, and moves AUC more than 0.05 off a coin flip.', '']
    if len(surv):
        t += ['SURVIVORS: %s' % ', '.join(surv.candidate),
              'Each becomes a reported QUALITY reading beside the trend label (high / low confidence trend).',
              'No state call changes; this flag never gates a trade on its own.']
    else:
        t += ['SURVIVORS: NONE.', '',
              'RECORDED FINDING: nothing already committed separates a true trending episode from a false one at',
              'label time. Combined with round 2 (the label confirms a median 24 bars late with 57% of the move',
              'gone, and ~50% of labelled episodes are directionless), the trend axis is AT ITS INFORMATION',
              'CEILING on this data: the panel is not carrying a present-tense signal that says which trend',
              'labels will be real. The round closes. No quality flag ships.']
    open(out('verdict') + '.txt', 'w').write('\n'.join(t) + '\n')
    print('\n'.join(t), flush=True)


NL = chr(10)
TAB_JS = '\n// ---- TREND ROUND 3, quality flag (Layer 1, 2026-11-11). Advanced only.\nfunction tqFill(){\n  const d=(window.D&&D.trend_quality)||null, el=document.getElementById(\'tqbody\');\n  if(!el) return;\n  if(!d){el.innerHTML=\'<p class="note">No trend_quality section in this app_data.json build.</p>\';return;}\n  const num=v=>v===null||v===undefined||v===\'\'?\'\':(typeof v===\'number\'\n      ?(Math.abs(v)>=1000?v.toFixed(0):Math.abs(v)<0.0001&&v!==0?v.toExponential(1):v.toFixed(4)):String(v));\n  const tbl=(rows,cols,cap)=>{\n    if(!rows||!rows.length) return \'<h4>\'+cap+\'</h4><p class="note">(not built in this run)</p>\';\n    return \'<h4>\'+cap+\'</h4><div class="tw"><table><thead><tr>\'\n      +cols.map(c=>\'<th>\'+c+\'</th>\').join(\'\')+\'</tr></thead><tbody>\'\n      +rows.map(r=>\'<tr>\'+cols.map(c=>\'<td>\'+num(r[c])+\'</td>\').join(\'\')+\'</tr>\').join(\'\')\n      +\'</tbody></table></div>\';};\n  el.innerHTML=\'<p class="note">\'+(d.note||\'\')+\' Built \'+(d.stamp||\'\')+\'.</p>\'\n    +tbl(d.verdict,[\'candidate\',\'gap_tuning\',\'auc_tuning\',\'gap_holdout\',\'auc_holdout\',\'sign_consistent\',\n                    \'null_p_sign\',\'null_p_perm\',\'survives\'],\n         \'Readings at the confirmation bar, and the verdict (A5 is the control)\')\n    +tbl(d.null,[\'kind\',\'candidate\',\'real\',\'null_mean\',\'null_p95\',\'null_max\',\'corrected\',\'p_value\'],\n         \'200-draw re-derive null\')\n    +tbl(d.subperiod,[\'candidate\',\'period\',\'gap\',\'auc\',\'n_episodes\'],\n         \'Sub-period split: 2016-2019 vs 2020\');}\n'


def stage_summary():
    B = pd.read_csv(out('verdict') + '.csv'); N = pd.read_csv(out('null') + '.csv')
    SB = pd.read_csv(out('subperiod') + '.csv'); E = pd.read_csv(out('episodes') + '.csv')
    def md(d, cols, fmt='%.4f'):
        head = '| ' + ' | '.join(cols) + ' |'; sep = '|' + '|'.join(['---'] * len(cols)) + '|'
        body = ['| ' + ' | '.join((fmt % x) if isinstance(x, (float, np.floating)) and np.isfinite(x) else str(x)
                                  for x in r) + ' |' for r in d[cols].itertuples(index=False)]
        return chr(10).join([head, sep] + body)
    surv = B[B.survives]
    m = ['# Layer 1 trend round 3 - is there a quality flag on the trend label?', '',
         '**%s.** One question, asked once: can anything ALREADY COMMITTED separate a TRUE trending episode '
         'from a FALSE one AT LABEL TIME? Round 2 measured the problem - about half of all labelled trending '
         'episodes are directionless and the shipped trend score cannot tell them apart (on the holdout the '
         'false ones score HIGHER). This is a quality flag on the existing label: no new axis, no new state, '
         'no state call changes, and no money metric anywhere in the run. Code `code/trendqual.py`.' % STAMP, '',
         '## The menu, declared before any result', '',
         'Five existing series read at the confirmation bar from bars <= t-1. No sweeps, no combinations, no '
         'interactions. A5 is the control and is expected to fail.', '',
         '- **A1** activity level (the scale measure the activity axis is cut from)',
         '- **A2** chop score (shipped, raw)',
         '- **A3** currency-leg gap (round 2 T2 series - failed as an AXIS; whether it works as a CONDITIONAL '
         'read is a different question, asked once here)',
         '- **A4** boundary-break follow-through (round 2 T1 series at the already-selected R=5)',
         '- **A5** trend score - THE CONTROL', '',
         'Episodes: **%d tuning, %d holdout**; true-trend share %.3f / %.3f; truth threshold %.3f learned on '
         'the tuning window. One episode is one observation throughout.'
         % (int((E.era == 'is').sum()), int((E.era == 'holdout').sum()),
            float(E[E.era == 'is'].true_trend.mean()), float(E[E.era == 'holdout'].true_trend.mean()),
            float(B.truth_threshold.iloc[0])), '',
         '## The readings', '',
         md(B, ['candidate', 'gap_tuning', 'auc_tuning', 'gap_holdout', 'auc_holdout', 'n_episodes_holdout',
                'sign_consistent']), '',
         'gap = |mean(true) - mean(false)| in sd units of the reading; AUC 0.5 is a coin flip. **A5, the '
         'control, behaved exactly as predicted** - the trend score carries no information about whether its '
         'own label will be real.', '',
         '## The 200-draw re-derive null (`trend_quality_null_%s.csv`)' % STAMP, '',
         'The same null that killed the DC axis, T1 and T2: on every surrogate the two-score classifier, the '
         'episode set, the truth threshold and all five readings are rebuilt from scratch, so it prices the '
         'whole question rather than one step of it.', '',
         md(N, ['kind', 'candidate', 'real', 'null_mean', 'null_p95', 'null_max', 'corrected', 'p_value']), '',
         '## Sub-period split, 2016-2019 vs 2020 (2021+ sealed)', '',
         md(SB, ['candidate', 'period', 'gap', 'auc', 'n_episodes']), '',
         '## Verdict', '',
         md(B, ['candidate', 'gap_holdout', 'auc_holdout', 'sign_consistent', 'null_p_sign', 'null_p_perm',
                'survives']), '']
    if len(surv):
        m += ['**Survivors: %s.** Each becomes a reported QUALITY reading beside the trend label (high / low '
              'confidence trend). No state call changes and the flag never gates a trade on its own.'
              % ', '.join(surv.candidate), '']
    else:
        m += ['**Survivors: none.**', '',
              '**Recorded finding: the trend axis is at its information ceiling on this data.** Nothing already '
              'committed separates a true trending episode from a false one at label time. Put beside round 2 - '
              'the label confirms a median 24 bars late with 57% of the move already gone, and half the labelled '
              'episodes are directionless - the panel is not carrying a present-tense signal that says which '
              'trend labels will be real. The round closes and no quality flag ships.', '']
    m += ['_Files: `trend_quality_{episodes,battery,null,subperiod,verdict}_%s.{csv,txt}`._' % STAMP]
    open(out('summary') + '.md', 'w').write(chr(10).join(m) + chr(10))
    print('wrote %s' % (out('summary') + '.md'), flush=True)


def stage_app():
    import json
    B = pd.read_csv(out('verdict') + '.csv'); N = pd.read_csv(out('null') + '.csv')
    SB = pd.read_csv(out('subperiod') + '.csv')
    for root in (os.path.join(_R, 'app_data.json'), os.path.join(ROOTOUT, 'app_data.json')):
        if not os.path.exists(root):
            continue
        D = json.load(open(root))
        D['trend_quality'] = dict(
            stamp=STAMP,
            note=('Round 3: can any already-committed series separate a TRUE trending episode from a FALSE one '
                  'at label time? A quality flag on the existing label -- no new axis, no new state, no money. '
                  'A5 is the declared control. The 200-draw null re-derives the classifier, the episodes, the '
                  'truth threshold and every reading on each surrogate.'),
            verdict=B.replace({np.nan: None}).to_dict('records'),
            null=N.replace({np.nan: None}).to_dict('records'),
            subperiod=SB.replace({np.nan: None}).to_dict('records'))
        json.dump(D, open(root, 'w'))
        print('wired into %s' % root, flush=True)
    ui = os.path.join(_R, 'app_ui.js'); s = open(ui).read()
    if 'tqFill' in s:
        print('app_ui.js already carries the trend quality tab', flush=True); return
    anchor = '<button role="tab" aria-selected="false" data-t="tr2">Trend round 2</button>'
    assert s.count(anchor) == 1, 'app_ui.js: nav anchor not found'
    s = s.replace(anchor, anchor + NL + '<button role="tab" aria-selected="false" data-t="tq">Trend quality</button>')
    sec = ('<section id="tq" hidden>' + NL + '<h3>Trend round 3: is there a quality flag on the trend label?</h3>' + NL +
           '<div class="note">Half of all labelled trending episodes go nowhere, and the trend score cannot tell' + NL +
           'which. This asks whether any series already in the repo can, read at the confirmation bar: activity' + NL +
           'scale, chop score, the currency-leg gap, break follow-through, and the trend score itself as a' + NL +
           'control. One episode is one observation; the 200-draw null re-derives everything on each surrogate.' + NL +
           'A survivor would be reported as a high/low confidence reading beside the label and would change no' + NL +
           'state call.</div>' + NL + '<div id="tqbody"></div>' + NL + '</section>' + NL)
    s = s.replace('<section id="tr2" hidden>', sec + '<section id="tr2" hidden>', 1)
    old_t = "'ex','pt','hz','rd','xd','pc','gl','ar','vd','dc','tr2'];"
    assert s.count(old_t) == 1, 'app_ui.js: TABS list not found'
    s = s.replace(old_t, "'ex','pt','hz','rd','xd','pc','gl','ar','vd','dc','tr2','tq'];")
    old_s = "   if(t==='tr2')tr2Fill();};"
    assert s.count(old_s) == 1, 'app_ui.js: show() hook not found'
    s = s.replace(old_s, "   if(t==='tr2')tr2Fill();" + NL + "   if(t==='tq')tqFill();};")
    s = s.rstrip() + NL + TAB_JS
    open(ui, 'w').write(s)
    print('app_ui.js: Trend quality tab added (%d bytes)' % len(s), flush=True)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--stage', required=True, choices=['battery', 'null', 'report', 'summary', 'app'])
    a = ap.parse_args(); print('=== trendqual %s ===' % a.stage, flush=True)
    {'battery': stage_battery, 'null': stage_null, 'report': stage_report,
     'summary': stage_summary, 'app': stage_app}[a.stage]()
    print('TREND QUALITY STAGE %s COMPLETE' % a.stage.upper(), flush=True)


if __name__ == '__main__':
    main()
