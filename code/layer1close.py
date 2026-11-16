import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""LAYER 1 CLOSE-OUT AND INTERFACE DELIVERY (16 Nov).

Layer 2 restarts from scratch and will consume Layer 1 ONLY through this repo.
This module makes the repo the complete, verified, single source of truth:
it enumerates every file Layer 2 may read, builds the one new consumable
(the trend quality flag as a daily series), writes the interface contract,
and audits the lot PASS/FAIL. Zero deletions -- anything superseded gets a
header note, never an edit.

    --stage quality    the ONE new build: the quality flag as a daily series
    --stage interface  enumerate every interface file with its provenance
    --stage contract   write LAYER1_INTERFACE.md at the repo root
    --stage audit      every check, PASS/FAIL -> results/LAYER1_CLOSEOUT_AUDIT.csv
"""
import argparse, hashlib, json, subprocess, time
import numpy as np, pandas as pd

STAMP = '2026-11-16'
SPLIT = pd.Timestamp('2016-01-01')
SEAL = pd.Timestamp('2020-12-31')
STATES = os.path.join(ROOTOUT, 'layer1_states.csv')
QSER = os.path.join(ROOTOUT, 'layer1_trend_quality_series.csv')
AUDIT = os.path.join(ROOTOUT, 'LAYER1_CLOSEOUT_AUDIT.csv')

ROWS = []


def row(kind, item, check, status, detail=''):
    ROWS.append(dict(kind=kind, item=item, check=check, status=status, detail=str(detail)[:300]))
    print('%-5s %-46s %s' % (status, item[:46], str(detail)[:110]), flush=True)


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as fh:
        for b in iter(lambda: fh.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


# ------------------------------------------------------------------ part 1.2
def stage_quality():
    """THE ONE NEW BUILD: the currency-leg confidence read (round 3, 21933e5)
    exported as a DAILY series aligned to the states file.

    Round 3 proved it as an episode-level reading. A consumable series has to
    carry it on every bar of a trending episode, and the high/low cut has to be
    learned on the TUNING WINDOW -- round 3's 55%/39% split was taken at the
    holdout's own median, which is not available to a consumer in real time. Both
    numbers are reported here so the difference is visible rather than hidden.
    """
    import trendqual as TQ
    # FULL history, exactly as export.py does it for the states file: rows after the
    # seal are produced with the SAME tuning-window cut and tagged sample=sealed, never
    # measured. Building only to 2020 would make the join to layer1_states.csv lossy.
    px = pd.read_csv(os.path.join(ROOTDATA, 'px28.csv'), index_col=0, parse_dates=True).astype(float)
    _, reads = TQ.build_all(px)
    # THE LABEL COMES FROM THE INTERFACE FILE, NEVER FROM A REBUILD (16 Nov). Rebuilding
    # shape2 here disagreed with results/layer1_states.csv on 26 AUDCAD rows at the
    # panel's warm-up edge, and two files disagreeing about what state a bar is in is
    # precisely the failure the interface contract exists to prevent. Only the READING
    # is computed; the label is read.
    _st = pd.read_csv(STATES, comment='#', parse_dates=['date'], usecols=['date', 'pair', 'shape2'])
    shape2 = _st.pivot(index='date', columns='pair', values='shape2').reindex(px.index)
    E, thr = TQ.episodes_and_truth(px[px.index <= SEAL], shape2[shape2.index <= SEAL])
    E = TQ.attach(E, reads)
    q = reads['A3_currency_leg_gap']
    # the cut: the tuning window's median reading AT TRENDING-EPISODE CONFIRMATION
    # BARS -- the only version a consumer can compute without seeing the future
    cut = float(E[E.era == 'is'].A3_currency_leg_gap.median())
    rows = []
    for p in shape2.columns:
        v = shape2[p]
        qq = q[p] if p in q.columns else pd.Series(np.nan, index=shape2.index)
        tr = (v == 'trending')
        ep_id = (tr != tr.shift()).cumsum().where(tr)
        for d in shape2.index:
            lab = v.get(d, '')
            if not isinstance(lab, str) or lab == '':
                continue
            x = float(qq.get(d, np.nan))
            rows.append((d, p, lab, bool(lab == 'trending'), x,
                         ('' if not (lab == 'trending' and np.isfinite(x)) else ('high' if x >= cut else 'low')),
                         (float(ep_id.get(d)) if np.isfinite(ep_id.get(d, np.nan)) else np.nan)))
    Q = pd.DataFrame(rows, columns=['date', 'pair', 'shape2', 'trending', 'quality_reading',
                                    'quality_tag', 'trend_episode_id'])
    Q['sample'] = np.where(Q.date < SPLIT, 'is', np.where(Q.date <= SEAL, 'holdout', 'sealed'))
    # the true-rate the tag actually delivers, under the TUNING-learned cut
    E2 = E.copy()
    E2['tag'] = np.where(E2.A3_currency_leg_gap >= cut, 'high', 'low')
    rate = E2.groupby(['era', 'tag']).true_trend.agg(['size', 'mean'])
    hdr = ('# LAYER 1 TREND QUALITY SERIES (the currency-leg confidence read, Layer 1 round 3). '
           'One row per (date, pair) that carries a shape2 label. quality_reading is the currency-leg '
           'strength gap |strength(base) - strength(quote)| over the trailing 106 bars in tuning-window '
           'vol units; quality_tag is high/low at cut %.6f, the median reading at TRENDING-episode '
           'confirmation bars on the tuning window (dates < %s). The tag is only set on trending bars. '
           'EVERY VALUE AT DATE t IS COMPUTABLE FROM BARS <= t-1: the underlying series is lagged one bar '
           'and nothing here shifts it again. Rows after %s are produced with the SAME cut and tagged '
           'sample=sealed -- applied, never measured. Readers pass comment="#".\n'
           % (cut, SPLIT.date(), SEAL.date()))
    with open(QSER, 'w') as fh:
        fh.write(hdr); Q.to_csv(fh, index=False)
    t = ['LAYER 1 TREND QUALITY SERIES -- %s' % STAMP,
         'Source: the round 3 reading (HANDOFF 0j, commit 21933e5), exported as a daily consumable.',
         '',
         'LAG CONVENTION: every value at date t is computable from bars through t-1. The currency-leg',
         'strength gap is built from trailing 106-bar cumulative log changes and shifted one bar at source;',
         'this export does not shift it again. The shape2 label carries the shipped dwell-5 confirmation.',
         '',
         'Rows %d; pairs %d; %s -> %s. Trending bars %d (%.1f%% of labelled bars).'
         % (len(Q), Q.pair.nunique(), Q.date.min().date(), Q.date.max().date(),
            int(Q.trending.sum()), 100 * Q.trending.mean()),
         'Tagged bars: high %d, low %d, untagged (non-trending or warm-up) %d.'
         % (int((Q.quality_tag == 'high').sum()), int((Q.quality_tag == 'low').sum()),
            int((Q.quality_tag == '').sum())),
         '',
         'CUT %.6f = the median reading at trending-episode confirmation bars on the TUNING WINDOW only.' % cut,
         'Round 3 reported 55.1%% / 39.3%% using the HOLDOUT median, which a live consumer cannot compute.',
         'Under this tuning-learned cut the episode true-trend rate is:', '',
         rate.to_string(float_format=lambda v: '%8.3f' % v),
         '',
         'Truth threshold for "true trend" %.4f (learned on the tuning window; results/trend_quality_verdict_%s.csv).'
         % (thr, '2026-11-11')]
    open(QSER.replace('.csv', '.txt'), 'w').write('\n'.join(t) + '\n')
    print('\n'.join(t), flush=True)
    return Q, cut, rate


# ------------------------------------------------------------------ part 1
INTERFACE = [
    ('results/layer1_states.csv', 'code/export.py', 'THE interface: shape2, activity, both scores, scale, the four mechanism reads'),
    ('results/layer1_trend_quality_series.csv', 'code/layer1close.py --stage quality',
     'the trend quality flag as a daily series (high/low confidence on trending bars)'),
    ('results/crisis_detectors.csv', 'code/crisis.py', 'the acute detectors with calendar recall, lift and lag'),
    ('results/crisis_events.csv', 'code/crisis.py', 'per detector per event: caught and lag, the daily firing record'),
    ('results/crisis_direction.csv', 'code/crisis.py', 'per event per pair behaviour during the crisis window'),
    ('results/move_coverage.csv', 'code/move.py', 'the MOVE witness: coverage and overlap with the acute detector'),
    ('results/nine_tiers.csv', 'code/ninestate.py', 'activity tiers and the nine-state grid'),
    ('results/twoscores.csv', 'code/twoscores.py', 'the two axes, raw and continuous'),
    ('results/measures_test1.csv', 'code/measures.py', 'the measurement series: separation, surrogate, corrected, lead'),
    ('results/pair_character.csv', 'code/paircharacter.py', 'per-pair character'),
    ('results/pair_character_blocks.csv', 'code/paircharacter.py', 'per-pair character by block -- whether it is stable'),
    ('results/run_lengths.csv', 'code/duration.py', 'state run lengths by generation and block'),
    ('results/duration_stats.csv', 'code/duration.py', 'duration, hazard and excursion statistics'),
    ('results/state_correlation.csv', 'code/statecorr.py', 'shared state across pairs -- the shared-bet / N_eff read'),
    ('results/state_correlation_summary.csv', 'code/statecorr.py', 'the same, summarised per pair'),
    ('results/witness_validation_2026-11-15.csv', 'code/witness.py',
     'witnesses 2 and 3 AS MEASURED -- REJECTED, not consumable: see HANDOFF 0k'),
]



def stage_interface():
    rows = []
    for path, producer, what in INTERFACE:
        p = os.path.join(_R, path)
        if not os.path.exists(p):
            row('interface', path, 'exists', 'FAIL', 'missing on disk')
            rows.append(dict(path=path, producer=producer, what=what, exists=False))
            continue
        try:
            d = pd.read_csv(p, comment='#', low_memory=False)
            n_rows = len(d)
            n_pairs = int(d.pair.nunique()) if 'pair' in d.columns else np.nan
            dmin = str(pd.to_datetime(d.date).min().date()) if 'date' in d.columns else ''
            dmax = str(pd.to_datetime(d.date).max().date()) if 'date' in d.columns else ''
        except Exception as e:
            row('interface', path, 'readable', 'FAIL', str(e)[:120]); continue
        tracked = subprocess.run(['git', 'ls-files', '--error-unmatch', path], cwd=_R,
                                 capture_output=True).returncode == 0
        rows.append(dict(path=path, producer=producer, what=what, exists=True, rows=n_rows,
                         pairs=n_pairs, date_min=dmin, date_max=dmax,
                         build_date=time.strftime('%Y-%m-%d', time.localtime(os.path.getmtime(p))),
                         md5=md5(p)[:12], git_tracked=tracked))
        row('interface', path, 'present, readable, tracked', 'PASS' if tracked else 'FAIL',
            '%d rows, %s pairs, %s..%s' % (n_rows, n_pairs, dmin, dmax))
    I = pd.DataFrame(rows)
    I.to_csv(os.path.join(ROOTOUT, 'layer1_interface_manifest_%s.csv' % STAMP), index=False)
    return I


# ------------------------------------------------------------------ part 2
def stage_contract():
    I = pd.read_csv(os.path.join(ROOTOUT, 'layer1_interface_manifest_%s.csv' % STAMP))
    V = pd.read_csv(os.path.join(ROOTOUT, 'trend_quality_verdict_2026-11-11.csv'))
    a3 = V[V.candidate == 'A3_currency_leg_gap'].iloc[0]
    W = pd.read_csv(os.path.join(ROOTOUT, 'witness_validation_2026-11-15.csv'))
    acute = W[W.witness == 'ACUTE_maxabsmove'].iloc[0]
    mv = W[W.witness == 'MOVE_rel'].iloc[0]
    qtxt = open(QSER.replace('.csv', '.txt')).read()
    rate = {}
    for line in qtxt.splitlines():
        parts = line.split()
        if len(parts) >= 4 and parts[0] in ('holdout', 'is') and parts[1] in ('high', 'low'):
            rate[(parts[0], parts[1])] = (int(parts[2]), float(parts[3]))
    def rr(era, tag):
        v = rate.get((era, tag))
        return ('%.1f%% (n=%d)' % (100 * v[1], v[0])) if v else 'n/a'
    L = []
    L.append('# LAYER 1 INTERFACE CONTRACT')
    L.append('')
    L.append('**%s.** This is the complete and only surface Layer 2 may read. Layer 2 restarts from scratch'
             ' and consumes Layer 1 through these files alone. Every number below is quoted from a named file,'
             ' with the filename beside it.' % STAMP)
    L.append('')
    L.append('## 1. The files Layer 2 may read')
    L.append('')
    L.append('| path | producer | what it is | rows | pairs | span |')
    L.append('|---|---|---|--:|--:|---|')
    for r in I.itertuples():
        L.append('| `%s` | `%s` | %s | %s | %s | %s..%s |'
                 % (r.path, r.producer, r.what, r.rows if pd.notna(r.rows) else '',
                    int(r.pairs) if pd.notna(r.pairs) else '', r.date_min if pd.notna(r.date_min) else '',
                    r.date_max if pd.notna(r.date_max) else ''))
    L.append('')
    L.append('Anything not on this list is working material, not interface. `results/layer1_interface_manifest_%s.csv`'
             ' carries the md5 and build date of each file.' % STAMP)
    L.append('')
    L.append('## 2. Columns, in plain English')
    L.append('')
    L.append('### `results/layer1_states.csv` — the live states')
    L.append('')
    L.append('| column | meaning |')
    L.append('|---|---|')
    L.append('| `date` | the bar the reading applies to. OANDA 17:00 New York close. |')
    L.append('| `pair` | one of the 28 G8 pairs. |')
    L.append('| `trend_score` | the TREND axis, raw and continuous. Higher means straighter. It does NOT say which way. |')
    L.append('| `chop_score` | the CHOP axis, raw and continuous. Higher means more range-bound. |')
    L.append('| `shape2` | the 2x2 label: `trending`, `ranging`, `trend-in-range`, `neither`. Empty during warm-up. |')
    L.append('| `activity` | `weak` / `medium` / `strong` — how much the pair is moving, cut jointly with shape. |')
    L.append('| `scale_28` | the raw scale measure the activity tier is cut from. |')
    L.append('| `combined2` | `<activity> <shape2>`, the twelve-cell product. |')
    L.append('| `settling` | the pair is inside the confirmation delay after a state change. |')
    L.append('| `m_fail`, `m_retr`, `m_space`, `m_panel` | the four mechanism reads behind the label. |')
    L.append('| `sample` | `is` (tuning, < 2016), `holdout` (2016-2020), `sealed` (2021+, applied never measured). |')
    L.append('')
    L.append('### `results/layer1_trend_quality_series.csv` — the confidence flag on a trending label')
    L.append('')
    L.append('| column | meaning |')
    L.append('|---|---|')
    L.append('| `date`, `pair` | as above, aligned one-to-one with the states file. |')
    L.append('| `shape2` | repeated from the states file so the flag can be read standalone. |')
    L.append('| `trending` | true where `shape2 == trending`. The flag means nothing on any other label. |')
    L.append('| `quality_reading` | the currency-leg strength gap: how far apart the two currencies of the pair are moving against the basket of the other seven, over the trailing 106 bars, in tuning-window vol units. |')
    L.append('| `quality_tag` | `high` or `low` at the tuning-window cut; empty off trending bars and during warm-up. |')
    L.append('| `trend_episode_id` | groups the bars of one trending run, so a consumer can count episodes rather than bars. |')
    L.append('')
    L.append('## 3. The three rules that are not negotiable')
    L.append('')
    L.append('**3.1 One-bar lag.** Every value dated `t` is computable from bars through `t-1`. A row dated D is'
             ' safe to act on at D\'s close. Do not shift it again and do not shift it back.'
             ' (`results/layer1_states.csv` header; `layer1_trend_quality_series.txt`.)')
    L.append('')
    L.append('**3.2 2021 onward is SEALED.** The cuts were fitted on < 2016 and confirmed once on 2016-2020.'
             ' Rows from 2021 are produced with the same cuts and are never measured — they carry'
             ' `sample=sealed`. The public loaders refuse to serve them without an explicit, logged flag'
             ' (`l2sweep.load_pair`, `l2route.load_states`, audit item 10).')
    L.append('')
    L.append('**3.3 Layer 2 never modifies, refits or retunes Layer 1.** No re-cutting a threshold, no'
             ' re-fitting a score, no "small adjustment" to a label. If a defect is found, report it back'
             ' and stop using the affected column — do not repair it downstream. A silent downstream repair'
             ' makes the two layers disagree and neither can then be audited.')
    L.append('')
    L.append('## 4. Confidence tiers — how much to trust each label')
    L.append('')
    L.append('Ordered by how well each label survived its own tests. This ordering is the single most useful'
             ' thing Layer 1 has to say.')
    L.append('')
    L.append('| label | confidence | what the evidence says |')
    L.append('|---|---|---|')
    L.append('| `ranging` | **strongest** | The chop axis is the one that holds up: separation corrected +0.035 on the 5pm build (`results/layer1_summary.csv`, HANDOFF 0a check B). Chop slices were the only positive per-slice books in the Layer 2 blind round (A-chop +0.63, B-chop +0.52; `results/refit_books_blind2.csv`). |')
    L.append('| `trending` + `quality_tag=high` | **weak, graded** | Trending labels are unreliable on their own; the flag grades them. Holdout episode true-trend rate %s for high against %s for low (`results/layer1_trend_quality_series.txt`). The flag cleared a 200-draw re-derive null at p=%.2f sign / %.2f permutation, AUC %.3f (`results/trend_quality_verdict_2026-11-11.csv`). |'
             % (rr('holdout', 'high'), rr('holdout', 'low'), a3.null_p_sign, a3.null_p_perm, a3.auc_holdout))
    L.append('| `trending` + `quality_tag=low` | **lowest of the trending labels** | Same caveats, worse base rate. |')
    L.append('| `trend-in-range`, `neither` | **low** | Residual cells. No construction has been validated on them. |')
    L.append('')
    L.append('**The trending label\'s two measured defects, so Layer 2 can design around them**'
             ' (`results/trend_anatomy_report_2026-11-10.txt`):')
    L.append('')
    L.append('- **~50% of labelled trending episodes are directionless** (true-trend share 50.1% tuning,'
             ' 44.3% holdout), and the trend score itself cannot tell which — on the holdout the FALSE'
             ' episodes score higher (0.494) than the true ones (0.329).')
    L.append('- **The label confirms a median 24 bars late**, with 56-57% of the leg\'s move already spent,'
             ' against a median 23-bar episode. Routed trend P&L concentrates in the first third of an'
             ' episode (60% of the A/B book\'s R), which is exactly the part the label is too late to catch.')
    L.append('')
    L.append('## 5. Crisis')
    L.append('')
    L.append('The crisis witness set is **the acute detector plus MOVE**, and nothing else'
             ' (`results/witness_incremental_2026-11-15.csv`, HANDOFF 0k).')
    L.append('')
    L.append('| witness | events caught | recall | lift | median lag |')
    L.append('|---|--:|--:|--:|--:|')
    L.append('| acute (maxabsmove) | %d of %d | %.3f | %.1fx | %.0f days |'
             % (acute.caught, acute.n_events, acute.recall, acute.lift, acute.median_lag_days))
    L.append('| MOVE (relative level) | %d of %d | %.3f | %.1fx | %.0f days |'
             % (mv.caught, mv.n_events, mv.recall, mv.lift, mv.median_lag_days))
    L.append('')
    L.append('Validated on the %d news-dated events of `code/events.py` inside the panel window, on a'
             ' FORWARD-ONLY window from the event date to +15 days that never opens before the event'
             ' (`results/witness_validation_2026-11-15.csv`). Panel turbulence and Roll illiquidity were'
             ' measured and REJECTED: neither caught any of the 7 events the acute detector misses, overlap'
             ' 1.000 (HANDOFF 0k). Their series stay in the repo as measured evidence and must not be'
             ' consumed as witnesses.' % acute.n_events)
    L.append('')
    L.append('## 6. What Layer 1 does NOT provide')
    L.append('')
    L.append('- **No prediction.** Every reading is present tense: what the pair is doing now, from bars'
             ' through t-1. Nothing here forecasts the next move, and the crisis witnesses confirm rather'
             ' than anticipate (median lag 0-1 days AFTER the event).')
    L.append('- **No direction.** `trend_score` says how straight, never which way. There is no long/short'
             ' content anywhere in Layer 1.')
    L.append('- **No money metrics.** No returns, no PnL, no Sharpe, no sizing. Every money number in this'
             ' repo belongs to Layer 2 and was produced by Layer 2 code.')
    L.append('- **No entry or exit timing.** The label tells you the state, not when to act inside it — and'
             ' per section 4 it is systematically late on trends.')
    L.append('- **No tradeable universe opinion.** Pair character (`results/paircharacter.csv`) describes'
             ' behaviour; it does not rank pairs for trading.')
    L.append('')
    L.append('## 7. Reporting a defect')
    L.append('')
    L.append('Open the finding against the producer script named in section 1, quote the file and the rows,'
             ' and leave Layer 1 untouched until it is fixed at source and re-exported. The audit that'
             ' certifies this interface is `results/LAYER1_CLOSEOUT_AUDIT.csv`; the pre-flight that guards'
             ' the invariants is `python3 code/preflight.py` (27 checks).')
    open(os.path.join(_R, 'LAYER1_INTERFACE.md'), 'w').write('\n'.join(L) + '\n')
    print('wrote LAYER1_INTERFACE.md (%d lines)' % len(L), flush=True)


# ------------------------------------------------------------------ part 4
def stage_audit():
    # 1. interface files
    stage_interface()
    # 2. states reproduce exactly
    before = os.path.join(ROOTOUT, 'layer1_states_before_closeout_%s.csv' % STAMP)
    if os.path.exists(STATES):
        import shutil; shutil.copy2(STATES, before)
    h0 = md5(STATES)
    r = subprocess.run([sys.executable, os.path.join(ROOTLIB, 'export.py')], cwd=_R, capture_output=True, text=True)
    h1 = md5(STATES)
    if r.returncode != 0:
        row('verify', 'layer1_states.csv regeneration', 'export.py runs', 'FAIL', (r.stderr or '')[-200:])
    else:
        same = h0 == h1
        row('verify', 'layer1_states.csv regeneration', 'byte-identical to the committed file',
            'PASS' if same else 'FAIL', 'md5 %s -> %s' % (h0[:12], h1[:12]))
    # 3. sanity constants
    px = pd.read_csv(os.path.join(ROOTDATA, 'px28.csv'), index_col=0, parse_dates=True)
    pk = float(px['EURUSD'].max()); lo = float(px['USDCHF'].min())
    row('verify', 'EURUSD peak 1.6010', 'panel sanity', 'PASS' if abs(pk - 1.6010) < 5e-4 else 'FAIL', '%.4f' % pk)
    row('verify', 'USDCHF low 0.7296', 'panel sanity', 'PASS' if abs(lo - 0.7296) < 5e-4 else 'FAIL', '%.4f' % lo)
    # 4. the sealing is unreachable through the public loaders
    import importlib
    for mod, fn, desc in (('l2sweep', 'load_pair', 'l2sweep.load_pair'),):
        m = importlib.import_module(mod)
        os.environ.pop('FX_ALLOW_W4', None)
        d = getattr(m, fn)('EURUSD')
        ok = d.index.max() <= SEAL
        row('verify', desc, 'refuses bars after 2020-12-31 without FX_ALLOW_W4',
            'PASS' if ok else 'FAIL', 'max date %s' % d.index.max().date())
    import l2route as RT
    sh, _ = RT.load_states(STATES)
    row('verify', 'l2route.load_states', 'refuses bars after 2020-12-31 without FX_ALLOW_W4',
        'PASS' if sh.index.max() <= SEAL else 'FAIL', 'max date %s' % sh.index.max().date())
    st = pd.read_csv(STATES, comment='#', parse_dates=['date'])
    sealed = st[st.date > SEAL]
    row('verify', 'layer1_states.csv sealed rows', 'rows after 2020-12-31 are tagged sample=sealed',
        'PASS' if (len(sealed) == 0 or (sealed['sample'] == 'sealed').all()) else 'FAIL',
        '%d rows after the seal, all tagged' % len(sealed))
    # 5. the quality series
    if os.path.exists(QSER):
        Q = pd.read_csv(QSER, comment='#', parse_dates=['date'])
        hdr = open(QSER).readline()
        ok = ('computable from bars <= t-1' in hdr) and Q.pair.nunique() == 28
        row('interface', 'results/layer1_trend_quality_series.csv', 'built, 28 pairs, lag stated in header',
            'PASS' if ok else 'FAIL', '%d rows, %d pairs, tags high %d / low %d'
            % (len(Q), Q.pair.nunique(), int((Q.quality_tag == 'high').sum()), int((Q.quality_tag == 'low').sum())))
        al = pd.read_csv(STATES, comment='#', parse_dates=['date'])
        lab = al[al.shape2.notna() & (al.shape2.astype(str) != '')]
        j = lab.merge(Q[['date', 'pair']], on=['date', 'pair'], how='left', indicator=True)
        miss = int((j._merge == 'left_only').sum())
        row('interface', 'quality series alignment', 'a row for every labelled (date, pair) of the states file',
            'PASS' if miss == 0 else 'FAIL',
            '%d quality rows vs %d labelled state rows; %d labelled state rows with no quality row'
            % (len(Q), len(lab), miss))
    else:
        row('interface', 'results/layer1_trend_quality_series.csv', 'exists', 'FAIL', 'not built')
    # 6. the contract
    c = os.path.join(_R, 'LAYER1_INTERFACE.md')
    row('contract', 'LAYER1_INTERFACE.md', 'written, names every interface file',
        'PASS' if os.path.exists(c) and all(p in open(c).read() for p, _, _ in INTERFACE) else 'FAIL',
        '%d bytes' % (os.path.getsize(c) if os.path.exists(c) else 0))
    # 7. preflight
    e = dict(os.environ); e['FX_COST_TABLE'] = 'results/cost_table_h22.csv'
    r = subprocess.run([sys.executable, os.path.join(ROOTLIB, 'preflight.py'), '--out', 'audit_%s.csv' % STAMP],
                       cwd=_R, capture_output=True, text=True, env=e)
    tail = (r.stdout or '').strip().splitlines()[-2:]
    row('verify', 'preflight.py', 'all 27 invariant checks PASS', 'PASS' if r.returncode == 0 else 'FAIL',
        ' | '.join(tail))
    # 8. app
    r = subprocess.run(['node', '--check', os.path.join(_R, 'app_ui.js')], capture_output=True, text=True)
    row('verify', 'app_ui.js', 'node --check passes', 'PASS' if r.returncode == 0 else 'FAIL', (r.stderr or '')[:120])
    D = json.load(open(os.path.join(_R, 'app_data.json')))
    for k in ('dc_axis', 'trend_round2', 'trend_quality', 'crisis_witnesses'):
        row('verify', 'app_data.json: %s' % k, 'section present for its tab', 'PASS' if k in D else 'FAIL',
            '%d keys' % len(D.get(k, {})))
    for fn in ('dcFill', 'tr2Fill', 'tqFill', 'cwFill'):
        row('verify', 'app_ui.js: %s()' % fn, 'renderer present', 'PASS' if fn in open(os.path.join(_R, 'app_ui.js')).read() else 'FAIL', '')
    A = pd.DataFrame(ROWS)
    A.to_csv(AUDIT, index=False)
    n = int((A.status == 'PASS').sum())
    print('\n%d of %d PASS -> %s' % (n, len(A), AUDIT), flush=True)
    if n < len(A):
        print('FAILURES:', flush=True)
        print(A[A.status != 'PASS'].to_string(index=False), flush=True)
        raise SystemExit('LAYER1 CLOSEOUT: %d checks FAILED -- the job halts here and is reported as a failure'
                         % int((A.status != 'PASS').sum()))
    print('LAYER1 CLOSEOUT AUDIT CLEAR', flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', required=True, choices=['quality', 'interface', 'contract', 'audit'])
    a = ap.parse_args(); print('=== layer1close %s ===' % a.stage, flush=True)
    {'quality': stage_quality, 'interface': stage_interface, 'contract': stage_contract,
     'audit': stage_audit}[a.stage]()
    print('LAYER1CLOSE STAGE %s COMPLETE' % a.stage.upper(), flush=True)


if __name__ == '__main__':
    main()
