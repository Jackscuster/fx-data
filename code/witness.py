import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""TWO MORE CRISIS WITNESSES (Layer 1 research round, constructions 2 and 3;
source results/research/RESEARCH_2026-11-09_*.md, commit 9926531).

A WITNESS CONFIRMS. It does not predict, it does not replace the acute
detector and it does not become a state. The whole point of a second and
third witness is an INDEPENDENT vote on a day the acute detector already
flags, or coverage of an event the acute detector misses -- so the question
that decides keep-or-kill is incremental, not absolute.

CONSTRUCTION 2 -- PANEL TURBULENCE (Kritzman-Li Mahalanobis). One number per
day: the distance of today's return vector from its own history, scaled by
the trailing covariance, so a day is turbulent when the moves are big OR
unusually COMBINED. Declared knobs: covariance window 250 and 500 bars; the
7 USD legs (primary) and all 28 pairs (secondary -- partly redundant by
triangulation, and whether the crosses add anything is reported rather than
assumed). The firing percentile is learned on the tuning window. Lagged one
bar: the covariance and the mean use bars <= t-1, and the series is shifted
once more before anything reads it.

CONSTRUCTION 3 -- ROLL ILLIQUIDITY. The effective-spread proxy from the
negative autocovariance of successive daily price changes, closes only:
spread = 2 * sqrt(-cov(dp_t, dp_t-1)). Declared knobs: rolling 20 and 60
bars, per pair, plus the panel average. DECLARED HANDLING: where the
autocovariance is POSITIVE the estimator is undefined; it is set to zero and
the share of undefined days is reported per window, because that share is
itself a liquidity reading.

VALIDATION is crisis.py's, unchanged: the 54-event news-dated calendar from
events.py, a FORWARD-ONLY window from the event date to +15 days that never
opens before the event, the 95th percentile learned on the tuning window,
and events caught / recall / base rate / lift / false-alarm rate outside
event windows. Sub-period split 2016-19 vs 2020. Null before any finding.

    python3 code/witness.py --stage build        # both witnesses, dated series
    python3 code/witness.py --stage validate     # calendar validation + false alarms
    python3 code/witness.py --stage null         # 200-draw re-derive null
    python3 code/witness.py --stage incremental  # the keep-or-kill question
    python3 code/witness.py --stage summary
    python3 code/witness.py --stage app
"""
import argparse, json, time
import numpy as np, pandas as pd
import events as EV

STAMP = '2026-11-15'
SPLIT = pd.Timestamp('2016-01-01')
SEAL = pd.Timestamp('2020-12-31')
WINDOW = 15          # days AFTER the event, never before -- crisis.py's convention
PCTL = 95
COV_WINS = (250, 500)
ROLL_WINS = (20, 60)
USD_LEGS = ['EURUSD', 'GBPUSD', 'AUDUSD', 'NZDUSD', 'USDCAD', 'USDCHF', 'USDJPY']
NSHUF = int(os.environ.get('FX_NSHUF', 200))


def out(n):
    return os.path.join(ROOTOUT, '%s_%s' % (n, STAMP))


def load_px():
    px = pd.read_csv(os.path.join(ROOTDATA, 'px28.csv'), index_col=0, parse_dates=True).astype(float)
    return px if os.environ.get('FX_ALLOW_W4') == '1' else px[px.index <= SEAL]


# --------------------------------------------------------- construction 2
def turbulence(px, cols, win):
    """Mahalanobis distance of the day's return vector from its trailing mean,
    under the trailing covariance. Everything that scales today's move is built
    from bars <= t-1, and the series is shifted once at the end."""
    r = np.log(px[cols]).diff()
    n = len(r)
    d = np.full(n, np.nan)
    X = r.values
    for i in range(win + 1, n):
        H = X[i - win:i]                        # strictly before today
        H = H[~np.isnan(H).any(axis=1)]
        if len(H) < max(30, H.shape[1] + 5):
            continue
        x = X[i]
        if np.isnan(x).any():
            continue
        mu = H.mean(axis=0)
        C = np.cov(H, rowvar=False)
        C = C + np.eye(C.shape[0]) * 1e-12
        try:
            iC = np.linalg.pinv(C)
        except Exception:
            continue
        v = x - mu
        d[i] = float(np.sqrt(max(v @ iC @ v, 0.0)))
    return pd.Series(d, index=r.index).shift(1)


# --------------------------------------------------------- construction 3
def roll_spread(px, win):
    """Roll (1984): spread = 2*sqrt(-cov(dp_t, dp_{t-1})) on closes. Where the
    autocovariance is positive the estimator is UNDEFINED -- set to zero, and the
    share of such days is reported because it is itself a liquidity reading."""
    dp = px.diff()
    S = pd.DataFrame(index=px.index, columns=px.columns, dtype=float)
    U = pd.DataFrame(False, index=px.index, columns=px.columns)
    for p in px.columns:
        a = dp[p]
        cov = a.rolling(win).cov(a.shift(1))
        undef = cov >= 0
        s = 2.0 * np.sqrt((-cov).clip(lower=0))
        s = s.where(~undef, 0.0)
        # in basis points of price, so pairs are comparable
        S[p] = 1e4 * s / px[p]
        U[p] = undef & cov.notna()
    return S.shift(1), U.shift(1)


def build():
    px = load_px()
    series = {}
    for win in COV_WINS:
        series['turb_usd_%d' % win] = turbulence(px, USD_LEGS, win)
        series['turb_all28_%d' % win] = turbulence(px, list(px.columns), win)
    undef = {}
    for win in ROLL_WINS:
        S, U = roll_spread(px, win)
        series['roll_panel_%d' % win] = S.mean(axis=1)
        undef['roll_%d' % win] = U
        S.to_csv(out('roll_perpair_%d' % win) + '.csv')
    D = pd.DataFrame(series)
    D.index.name = 'date'
    return px, D, undef


# --------------------------------------------------------- validation
def acute_and_move(px):
    """The existing witnesses, rebuilt exactly as crisis.py / move.py read them."""
    import crisis as CR
    D = CR.detectors(px) if hasattr(CR, 'detectors') else None
    if D is None:
        r = np.log(px).diff()
        sd = r.rolling(60).std().shift(1)
        z = r / sd
        D = pd.DataFrame(index=px.index)
        D['maxabsmove'] = z.abs().max(axis=1)
        D['breadth2sig'] = (z.abs() > 2).sum(axis=1)
    mv = None
    ext = os.path.join(ROOTDATA, 'ext.csv')
    if os.path.exists(ext):
        e = pd.read_csv(ext, index_col=0, parse_dates=True)
        if '^MOVE' in e.columns:
            m = e['^MOVE'].reindex(px.index).ffill()
            mv = (m / m.rolling(250).mean().shift(1)).shift(1)       # lagged, relative level
    return D, mv


def fire_of(s, thr=None):
    s = s.dropna()
    if not len(s):
        return pd.Series(dtype=bool), np.nan
    t = np.nanpercentile(s[s.index < SPLIT], PCTL) if (s.index < SPLIT).any() else np.nanpercentile(s, PCTL)
    return (s > t), float(t)


def score_one(name, s, cal):
    fire, thr = fire_of(s)
    if not len(fire):
        return None, []
    base = float(fire.mean())
    caught, lags, per = 0, [], []
    inwin = pd.Series(False, index=fire.index)
    for _, e in cal.iterrows():
        lo = e.date; hi = e.date + pd.Timedelta(days=WINDOW)
        m = (fire.index >= lo) & (fire.index <= hi)
        inwin |= m
        w = fire[m]
        hit = bool(w.any())
        lag = int((w[w].index[0] - lo).days) if hit else None
        caught += hit
        if hit:
            lags.append(lag)
        per.append(dict(witness=name, date=str(e.date.date()), type=e.type, ccy=e.ccy,
                        severity=int(e.severity), description=e.description, caught=hit, lag_days=lag))
    n = len(cal)
    recall = caught / n if n else np.nan
    fa = float(fire[~inwin].mean()) if (~inwin).any() else np.nan
    return dict(witness=name, threshold=thr, caught=caught, n_events=n, recall=recall,
                base_rate=base, lift=(recall / base if base > 0 else np.nan),
                false_alarm_rate_outside_windows=fa,
                median_lag_days=(float(np.median(lags)) if lags else np.nan)), per


def stage_build():
    px, D, undef = build()
    D.to_csv(out('witness_series') + '.csv')
    rows = []
    for k, U in undef.items():
        rows.append(dict(window=k, share_undefined_all=float(U.mean().mean()),
                         share_undefined_tuning=float(U[U.index < SPLIT].mean().mean()),
                         share_undefined_holdout=float(U[U.index >= SPLIT].mean().mean())))
    UD = pd.DataFrame(rows); UD.to_csv(out('roll_undefined') + '.csv', index=False)
    t = ['CRISIS WITNESSES -- SERIES BUILT. %s' % STAMP,
         'Panel %s -> %s, 2021+ sealed. All series lagged one bar.' % (px.index.min().date(), px.index.max().date()), '',
         'coverage (non-null bars):', D.notna().sum().to_string(), '',
         'ROLL UNDEFINED SHARE (autocovariance positive -> estimator undefined, set to zero; the share is itself a reading):',
         UD.to_string(index=False, float_format=lambda v: '%7.4f' % v)]
    open(out('witness_series') + '.txt', 'w').write('\n'.join(t) + '\n')
    print('\n'.join(t), flush=True)


def stage_validate():
    px = load_px(); D = pd.read_csv(out('witness_series') + '.csv', index_col=0, parse_dates=True)
    A, mv = acute_and_move(px)
    cal = EV.calendar(); cal = cal[cal.date <= SEAL]
    allser = {c: D[c] for c in D.columns}
    for c in A.columns:
        allser['ACUTE_' + c] = A[c]
    if mv is not None:
        allser['MOVE_rel'] = mv
    rows, per = [], []
    for k, s in allser.items():
        r, p = score_one(k, s, cal)
        if r:
            rows.append(r); per += p
    V = pd.DataFrame(rows).sort_values('lift', ascending=False)
    V.to_csv(out('witness_validation') + '.csv', index=False)
    pd.DataFrame(per).to_csv(out('witness_per_event') + '.csv', index=False)
    sr = []
    for lab, a, b in (('2016-2019', '2016-01-01', '2019-12-31'), ('2020', '2020-01-01', '2020-12-31')):
        c2 = cal[(cal.date >= a) & (cal.date <= b)]
        if not len(c2):
            continue
        for k, s in allser.items():
            r, _ = score_one(k, s.loc[a:b] if len(s.loc[a:b]) else s, c2)
            if r:
                r['period'] = lab; sr.append(r)
    pd.DataFrame(sr).to_csv(out('witness_subperiod') + '.csv', index=False)
    t = ['CRISIS WITNESSES -- CALENDAR VALIDATION (forward-only, event date to +%d days, never before). %s' % (WINDOW, STAMP),
         '%d news-dated events inside the panel window. Firing threshold = the %dth percentile learned on the tuning window.'
         % (len(cal), PCTL), '',
         V[['witness', 'caught', 'n_events', 'recall', 'base_rate', 'lift',
            'false_alarm_rate_outside_windows', 'median_lag_days']].to_string(index=False, float_format=lambda v: '%8.3f' % v),
         '', 'A witness CONFIRMS: lag is measured from the event, and a negative lag is impossible by construction.']
    open(out('witness_validation') + '.txt', 'w').write('\n'.join(t) + '\n')
    print('\n'.join(t), flush=True)


def stage_null():
    """200-draw re-derive null: on each surrogate the series, the percentile and the
    whole validation are rebuilt, so the null prices the construction."""
    from structval import surrogate
    t0 = time.time(); px = load_px()
    cal = EV.calendar(); cal = cal[cal.date <= SEAL]
    D = pd.read_csv(out('witness_series') + '.csv', index_col=0, parse_dates=True)
    real = {}
    for c in D.columns:
        r, _ = score_one(c, D[c], cal)
        real[c] = r['lift'] if r else np.nan
    rng = np.random.default_rng(20261115); rows = []
    for kind in ('sign', 'perm'):
        draws = {c: [] for c in D.columns}
        for i in range(NSHUF):
            q = surrogate(px, kind, rng)
            try:
                ser = {}
                for win in COV_WINS:
                    ser['turb_usd_%d' % win] = turbulence(q, USD_LEGS, win)
                    ser['turb_all28_%d' % win] = turbulence(q, list(q.columns), win)
                for win in ROLL_WINS:
                    S, _ = roll_spread(q, win)
                    ser['roll_panel_%d' % win] = S.mean(axis=1)
                for c in D.columns:
                    r, _ = score_one(c, ser[c], cal)
                    draws[c].append(r['lift'] if r else np.nan)
            except Exception as e:
                print('  draw %d failed: %s' % (i, str(e)[:70]), flush=True)
            if (i + 1) % 25 == 0:
                print('  %s null: %d/%d (%.1f min)' % (kind, i + 1, NSHUF, (time.time() - t0) / 60), flush=True)
        for c in D.columns:
            v = np.array([x for x in draws[c] if np.isfinite(x)]); r = real[c]
            rows.append(dict(kind=kind, witness=c, real_lift=r, n_draws=len(v),
                             null_mean=float(v.mean()) if len(v) else np.nan,
                             null_p95=float(np.percentile(v, 95)) if len(v) else np.nan,
                             null_max=float(v.max()) if len(v) else np.nan,
                             p_value=float((v >= r).mean()) if len(v) else np.nan))
    N = pd.DataFrame(rows); N.to_csv(out('witness_null') + '.csv', index=False)
    t = ['CRISIS WITNESSES -- %d-DRAW RE-DERIVE NULL on calendar LIFT. %s' % (NSHUF, STAMP), '',
         N.to_string(index=False, float_format=lambda v: '%9.3f' % v),
         '', 'done in %.1f min' % ((time.time() - t0) / 60)]
    open(out('witness_null') + '.txt', 'w').write('\n'.join(t) + '\n')
    print('\n'.join(t), flush=True)


def stage_incremental():
    """THE KEEP-OR-KILL QUESTION: which events does each new witness catch that the
    acute detector MISSES, and how much does it just duplicate MOVE?"""
    P = pd.read_csv(out('witness_per_event') + '.csv')
    new = [c for c in P.witness.unique() if c.startswith(('turb_', 'roll_'))]
    acute = [c for c in P.witness.unique() if c.startswith('ACUTE_')]
    move = [c for c in P.witness.unique() if c.startswith('MOVE')]
    piv = P.pivot_table(index='date', columns='witness', values='caught', aggfunc='first')
    acute_any = piv[acute].any(axis=1) if acute else pd.Series(False, index=piv.index)
    move_any = piv[move].any(axis=1) if move else pd.Series(False, index=piv.index)
    rows = []
    for c in new:
        f = piv[c].fillna(False).astype(bool)
        rows.append(dict(witness=c, caught=int(f.sum()), n_events=int(len(f)),
                         caught_that_acute_misses=int((f & ~acute_any).sum()),
                         acute_misses_total=int((~acute_any).sum()),
                         overlap_with_acute=float((f & acute_any).sum() / max(f.sum(), 1)),
                         caught_that_move_misses=int((f & ~move_any).sum()),
                         overlap_with_move=float((f & move_any).sum() / max(f.sum(), 1)),
                         unique_to_this_witness=int((f & ~acute_any & ~move_any).sum())))
    I = pd.DataFrame(rows).sort_values('caught_that_acute_misses', ascending=False)
    I.to_csv(out('witness_incremental') + '.csv', index=False)
    missed = piv.index[~acute_any]
    det = P[(P.witness.isin(new)) & (P.date.isin(missed)) & (P.caught)][['witness', 'date']]
    det = det.merge(P[['date', 'type', 'ccy', 'severity', 'description']].drop_duplicates('date'), on='date', how='left')
    det.to_csv(out('witness_events_acute_missed') + '.csv', index=False)
    t = ['CRISIS WITNESSES -- THE INCREMENTAL QUESTION (what decides keep or kill). %s' % STAMP,
         'A witness earns a place by adding coverage or an independent vote, never by duplicating one that exists.', '',
         I.to_string(index=False, float_format=lambda v: '%8.3f' % v), '',
         'The acute detector misses %d of %d events; the new witnesses catch these among them:' % (int((~acute_any).sum()), len(piv))]
    if len(det):
        t += ['', det.to_string(index=False)]
    else:
        t += ['', '  none -- neither new witness catches a single event the acute detector misses.']
    open(out('witness_incremental') + '.txt', 'w').write('\n'.join(t) + '\n')
    print('\n'.join(t), flush=True)


def stage_summary():
    V = pd.read_csv(out('witness_validation') + '.csv'); N = pd.read_csv(out('witness_null') + '.csv')
    I = pd.read_csv(out('witness_incremental') + '.csv'); UD = pd.read_csv(out('roll_undefined') + '.csv')
    SB = pd.read_csv(out('witness_subperiod') + '.csv')
    def md(d, cols, fmt='%.3f'):
        head = '| ' + ' | '.join(cols) + ' |'; sep = '|' + '|'.join(['---'] * len(cols)) + '|'
        body = ['| ' + ' | '.join((fmt % x) if isinstance(x, (float, np.floating)) and np.isfinite(x) else str(x)
                                  for x in r) + ' |' for r in d[cols].itertuples(index=False)]
        return chr(10).join([head, sep] + body)
    p = N.pivot_table(index='witness', columns='kind', values='p_value')
    m = ['# Crisis witnesses 2 and 3 - panel turbulence and Roll illiquidity', '',
         '**%s.** Two additional WITNESSES beside the acute detector and MOVE. A witness confirms: it does not'
         ' predict, it does not replace anything, and it never becomes a state. Source'
         ' `results/research/RESEARCH_2026-11-09_*.md` (commit 9926531); code `code/witness.py`.' % STAMP, '',
         '## What they are', '',
         '**Panel turbulence (Kritzman-Li).** One number a day: the Mahalanobis distance of the day\'s return'
         ' vector from its own trailing history, scaled by the trailing covariance - so a day is turbulent when'
         ' the moves are big OR unusually combined. Covariance windows 250 and 500 bars, declared; built on the'
         ' 7 USD legs (primary) and on all 28 pairs (secondary, partly redundant by triangulation).', '',
         '**Roll illiquidity.** The effective-spread proxy from the negative autocovariance of successive daily'
         ' price changes, closes only. Windows 20 and 60 bars, per pair plus the panel average. Where the'
         ' autocovariance is positive the estimator is undefined; it is set to zero and **the share of'
         ' undefined days is reported, because that share is itself a liquidity reading**:', '',
         md(UD, ['window', 'share_undefined_all', 'share_undefined_tuning', 'share_undefined_holdout'], '%.4f'), '',
         '## Calendar validation (crisis.py\'s, unchanged)', '',
         'The %d news-dated events inside the panel window, a FORWARD-ONLY window from the event date to +15'
         ' days that never opens before the event, firing at the 95th percentile learned on the tuning window.'
         % int(V.n_events.iloc[0]), '',
         md(V, ['witness', 'caught', 'n_events', 'recall', 'base_rate', 'lift',
                'false_alarm_rate_outside_windows', 'median_lag_days']), '',
         '## The 200-draw re-derive null', '',
         md(N, ['kind', 'witness', 'real_lift', 'null_mean', 'null_p95', 'null_max', 'p_value']), '',
         '## The incremental question - what decides keep or kill', '',
         md(I, ['witness', 'caught', 'caught_that_acute_misses', 'overlap_with_acute',
                'caught_that_move_misses', 'overlap_with_move', 'unique_to_this_witness'], '%.3f'), '',
         '## Sub-period split, 2016-2019 vs 2020', '',
         md(SB, ['witness', 'period', 'caught', 'n_events', 'recall', 'lift'] if 'period' in SB.columns else list(SB.columns)[:6]), '']
    open(out('witness_summary') + '.md', 'w').write(chr(10).join(m) + chr(10))
    print('wrote %s' % (out('witness_summary') + '.md'), flush=True)


def stage_app():
    V = pd.read_csv(out('witness_validation') + '.csv'); N = pd.read_csv(out('witness_null') + '.csv')
    I = pd.read_csv(out('witness_incremental') + '.csv'); UD = pd.read_csv(out('roll_undefined') + '.csv')
    for root in (os.path.join(_R, 'app_data.json'), os.path.join(ROOTOUT, 'app_data.json')):
        if not os.path.exists(root):
            continue
        D = json.load(open(root))
        D['crisis_witnesses'] = dict(
            stamp=STAMP,
            what=('Two more witnesses beside the acute detector and MOVE. Panel turbulence is the Mahalanobis '
                  'distance of the day\'s return vector from its own history under the trailing covariance: a '
                  'day is turbulent when moves are big OR unusually combined. Roll illiquidity is the '
                  'effective-spread proxy from the negative autocovariance of daily price changes, closes only.'),
            what_it_is_not=('CONFIRMATION, NEVER PREDICTION. Both are read on the day, lagged one bar, and '
                            'validated on a forward-only window from each news-dated event to +15 days that '
                            'never opens before the event. Neither forecasts a crisis, neither is a state, and '
                            'neither replaces the acute detector or MOVE -- a witness earns its place only by '
                            'adding coverage or an independent vote.'),
            validation=V.replace({np.nan: None}).to_dict('records'),
            null=N.replace({np.nan: None}).to_dict('records'),
            incremental=I.replace({np.nan: None}).to_dict('records'),
            roll_undefined=UD.replace({np.nan: None}).to_dict('records'))
        json.dump(D, open(root, 'w'))
        print('wired into %s' % root, flush=True)
    ui = os.path.join(_R, 'app_ui.js'); s = open(ui).read()
    if 'cwFill' in s:
        print('app_ui.js already carries the crisis witnesses tab', flush=True); return
    anchor = '<button role="tab" aria-selected="false" data-t="tq">Trend quality</button>'
    assert s.count(anchor) == 1, 'app_ui.js: nav anchor not found'
    s = s.replace(anchor, anchor + chr(10) + '<button role="tab" aria-selected="false" data-t="cw">Crisis witnesses</button>')
    sec = ('<section id="cw" hidden>' + chr(10) + '<h3>Crisis witnesses: panel turbulence and Roll illiquidity</h3>' + chr(10) +
           '<div class="note">Two more witnesses beside the acute detector and MOVE. <b>Panel turbulence</b> asks whether' + chr(10) +
           'today&rsquo;s move across the whole panel is far from its own history once you account for how the pairs' + chr(10) +
           'normally move together &mdash; so a day counts as turbulent if the moves are big <i>or</i> unusually' + chr(10) +
           'combined. <b>Roll illiquidity</b> estimates the effective spread from the bounce in successive daily' + chr(10) +
           'closes; where the maths is undefined the value is zero and the share of undefined days is reported,' + chr(10) +
           'because that share is itself a liquidity reading. <b>What these are NOT:</b> they are confirmation,' + chr(10) +
           'never prediction. Both are lagged one bar and scored on a forward-only window from each news-dated' + chr(10) +
           'event to +15 days that never opens before the event. Neither is a state, neither forecasts anything,' + chr(10) +
           'and neither replaces the acute detector or MOVE &mdash; a witness earns its place only by catching an' + chr(10) +
           'event the others miss or by voting independently on one they catch.</div>' + chr(10) +
           '<div id="cwbody"></div>' + chr(10) + '</section>' + chr(10))
    s = s.replace('<section id="tq" hidden>', sec + '<section id="tq" hidden>', 1)
    old_t = "'ex','pt','hz','rd','xd','pc','gl','ar','vd','dc','tr2','tq'];"
    assert s.count(old_t) == 1, 'app_ui.js: TABS list not found'
    s = s.replace(old_t, "'ex','pt','hz','rd','xd','pc','gl','ar','vd','dc','tr2','tq','cw'];")
    old_s = "   if(t==='tq')tqFill();};"
    assert s.count(old_s) == 1, 'app_ui.js: show() hook not found'
    s = s.replace(old_s, "   if(t==='tq')tqFill();" + chr(10) + "   if(t==='cw')cwFill();};")
    s = s.rstrip() + chr(10) + TAB_JS
    open(ui, 'w').write(s)
    print('app_ui.js: Crisis witnesses tab added (%d bytes)' % len(s), flush=True)


TAB_JS = r'''
// ---- CRISIS WITNESSES 2 and 3 (Layer 1, 2026-11-15). Advanced only. Confirmation, never prediction.
function cwFill(){
  const d=(window.D&&D.crisis_witnesses)||null, el=document.getElementById('cwbody');
  if(!el) return;
  if(!d){el.innerHTML='<p class="note">No crisis_witnesses section in this app_data.json build.</p>';return;}
  const num=v=>v===null||v===undefined||v===''?'':(typeof v==='number'
      ?(Math.abs(v)>=1000?v.toFixed(0):Math.abs(v)<0.001&&v!==0?v.toExponential(1):v.toFixed(3)):String(v));
  const tbl=(rows,cols,cap)=>{
    if(!rows||!rows.length) return '<h4>'+cap+'</h4><p class="note">(not built in this run)</p>';
    return '<h4>'+cap+'</h4><div class="tw"><table><thead><tr>'
      +cols.map(c=>'<th>'+c+'</th>').join('')+'</tr></thead><tbody>'
      +rows.map(r=>'<tr>'+cols.map(c=>'<td>'+num(r[c])+'</td>').join('')+'</tr>').join('')
      +'</tbody></table></div>';};
  el.innerHTML='<p class="note"><b>What they are.</b> '+(d.what||'')+'</p>'
    +'<p class="note"><b>What they are not.</b> '+(d.what_it_is_not||'')+'</p>'
    +tbl(d.validation,['witness','caught','n_events','recall','base_rate','lift','false_alarm_rate_outside_windows','median_lag_days'],
         'Calendar validation: forward-only, event date to +15 days')
    +tbl(d.incremental,['witness','caught','caught_that_acute_misses','overlap_with_acute','caught_that_move_misses','overlap_with_move','unique_to_this_witness'],
         'The incremental question - does it add coverage or duplicate an existing witness')
    +tbl(d.null,['kind','witness','real_lift','null_mean','null_p95','null_max','p_value'],
         '200-draw re-derive null on calendar lift')
    +tbl(d.roll_undefined,['window','share_undefined_all','share_undefined_tuning','share_undefined_holdout'],
         'Roll: share of days the estimator is undefined (itself a liquidity reading)')
    +'<p class="note">Built '+(d.stamp||'')+'.</p>';}
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', required=True,
                    choices=['build', 'validate', 'null', 'incremental', 'summary', 'app'])
    a = ap.parse_args(); print('=== witness %s ===' % a.stage, flush=True)
    {'build': stage_build, 'validate': stage_validate, 'null': stage_null,
     'incremental': stage_incremental, 'summary': stage_summary, 'app': stage_app}[a.stage]()
    print('WITNESS STAGE %s COMPLETE' % a.stage.upper(), flush=True)


if __name__ == '__main__':
    main()
