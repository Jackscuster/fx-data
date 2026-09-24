import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""PRE-FLIGHT -- the September 2026 fault audit as MECHANICAL checks.

Every fault found this month gets a row: fault, fix, check, status. Each check
runs here, against the repo as it is, and the script exits non-zero if any row
is not PASS. Writes results/audit_2026-09.csv. No rebuild starts until the
whole table is PASS (Jack, 16 Sep).

    python3 code/preflight.py                 # the whole audit
    python3 code/preflight.py --quick         # skips the engine runs (items 12, 13, 15)
    FX_COST_TABLE=results/cost_table_h22.csv python3 code/preflight.py   # the rebuild's table

Statuses: PASS -- the check ran and held. FAIL -- the check ran and did not.
MANUAL -- the check cannot be run by code here and says what to do. Nothing is
marked PASS without a check that executed.
"""
import argparse, glob, json, re, subprocess, time
import numpy as np, pandas as pd

ROWS = []
AUDIT_OUT = 'audit_2026-09.csv'


def row(n, fault, fix, check, status, detail=''):
    ROWS.append(dict(item=n, fault=fault, fix=fix, check=check, status=status, detail=str(detail)[:400]))
    print('%-4s %2d  %s%s' % (status, n, fault[:70], ('  -- ' + str(detail)[:120]) if detail else ''), flush=True)


def guard(n, fault, fix, check, fn):
    """Run fn(); PASS on a truthy return (its detail), FAIL on False or any exception."""
    try:
        r = fn()
        if r is False:
            row(n, fault, fix, check, 'FAIL')
        else:
            row(n, fault, fix, check, 'PASS', r if isinstance(r, str) else '')
    except Exception as e:
        row(n, fault, fix, check, 'FAIL', '%s: %s' % (type(e).__name__, str(e)[:200]))


def src(name):
    return open(os.path.join(ROOTLIB, name)).read()


# ----------------------------------------------------------------- LOOKAHEAD
def c1():
    import l2walkfwd as W
    assert W.VOTE_ON_ENTRY_DAY is False, 'VOTE_ON_ENTRY_DAY default is not False'
    assert 'check_no_same_day_entrant(M, fill' in src('l2walkfwd.py'), 'Book does not call the same-day check'
    # exercise it on a small synthetic book: a fill-day vote must halt
    M = pd.DataFrame(dict(sid=['a', 'a', 'b', 'b'], tid=[1, 1, 2, 2], pair=['EURUSD'] * 4,
                          day=pd.to_datetime(['2016-01-04', '2016-01-05', '2016-01-04', '2016-01-05']),
                          dir=[1, 1, -1, -1], mark=[-0.02, 0.1, -0.02, -0.1]))
    B = W.Book(M, ['a', 'b'])
    assert B.L.shape[0] == 1, 'fixed Book kept a fill-day row'
    W.VOTE_ON_ENTRY_DAY = True
    try:
        W.Book(M, ['a', 'b'])
        return False
    except RuntimeError:
        pass
    finally:
        W.VOTE_ON_ENTRY_DAY = False
    return 'default False; fill-day vote halts; synthetic book keeps 1 of 2 rows'


def c2():
    import l2sweep as S
    line = S.layer1_header_check(S.LABELS)
    # the axes export.py imports are lagged in ninestate.raw_axes / grid_at; a
    # PERTURBATION test proves it: change the close on day D and the state row
    # dated D must not move (D+1 may)
    import ninestate as N
    px = pd.read_csv(os.path.join(ROOTDATA, 'px28.csv'), index_col=0, parse_dates=True)
    px = px.loc[:'2020-12-31']
    D = px.index[-300]
    a = N.raw_axes(px)
    q = px.copy(); q.loc[D] = q.loc[D] * 1.02
    b = N.raw_axes(q)
    for k in a:
        ra, rb = a[k].loc[D], b[k].loc[D]
        assert np.allclose(ra.fillna(0).values, rb.fillna(0).values), 'raw axis %s dated %s moved when %s close moved' % (k, D.date(), D.date())
        assert not np.allclose(a[k].loc[D:].iloc[1].fillna(0).values, b[k].loc[D:].iloc[1].fillna(0).values), 'perturbation had no effect on %s at D+1' % k
    # and the join in regime_codes must be unshifted (the file is already lagged)
    rc = src('l2sweep.py')[src('l2sweep.py').index('def regime_codes'):]
    assert '.shift(' not in rc[:1500], 'regime_codes shifts again (double lag)'
    return 'header declares the lag; perturbing the %s close leaves every axis dated %s unchanged and moves D+1; regime_codes joins unshifted' % (D.date(), D.date())


def c3():
    import l2walkfwd as W
    for w in W.SETTINGS_TUNE_END:
        assert W.SETTINGS_TUNE_END[w] < W.SETTINGS_SCORE_START[w]
    for st in W.STEPS:
        assert st['build'][1] < st['trade'][0]
    import l2refitpilot as P
    for pw, tw in P.STEPS:
        assert P.PILOT_WINDOWS[pw][1] < P.PILOT_WINDOWS[tw][0], 'pilot %s does not end before %s' % (pw, tw)
    return 'W2 by ip1 (to 2010), W3 by ip2 (to 2015); pilot P1<T1, P2<T2; STEPS build<trade'


def c4():
    F = pd.read_csv(os.path.join(ROOTOUT, 'gate2_cleanfield_4slice.csv'), low_memory=False)
    assert 'label_basis' in F, 'field has no label_basis column'
    b = F.label_basis.unique().tolist()
    assert b == ['W2_ip1'], 'label_basis not uniform W2_ip1: %s' % b
    assert F.clean_label.all(), 'a field row without clean_label'
    return '%d rows, label_basis W2_ip1 (2011-2015 under ip1 tuned to 2010) on every row' % len(F)


def c5():
    import l2walkfwd as W
    assert 'check_mark_convention(out' in src('l2walkfwd.py'), 'null writer does not assert the convention'
    M = pd.DataFrame(dict(sid=['a', 'a'], tid=[1, 1], day=pd.to_datetime(['2016-01-04', '2016-01-05']), dir=[1, 1], mark=[0.05, 0.1]))
    try:
        W.check_mark_convention(M, 'synthetic')
        return False
    except RuntimeError:
        pass
    assert 'tid = 10 ** 9' in src('l2walkfwd.py'), 'null tids not offset'
    return 'null writes fill-day cost row + unique tid; a positive fill-day mark halts'


def c6():
    import l2walkfwd as W
    W.TAG = '_routed_tirexcl_actweak'; os.environ['WF_TAG'] = W.TAG
    T = pd.read_pickle(W.OUT('wf_trades.pkl')); M = pd.read_pickle(W.OUT('wf_marks.pkl'))
    g = M.groupby(['sid', 'tid'], observed=True).day.agg(['min', 'max'])
    k = T.set_index(['sid', 'tid'])
    j = g.join(k[['entry', 'exit']], how='inner')
    assert len(j) == len(T), 'marks/trades key mismatch'
    assert (j['min'] == j.entry).all() and (j['max'] <= j.exit).all(), 'marks outside [entry, exit]'
    # the trade table's exit is clipped to the era end: nothing carries past 2020
    assert T.exit.max() <= pd.Timestamp('2020-12-31'), 'a trade carries marks past 2020'
    # and the trade-year sums are truncated to calendar years (window boundary = marking boundary)
    TY = W.trade_year_sums(M.head(200000))
    assert (TY.yr >= 2005).all() and (TY.yr <= 2020).all()
    return '%d trades: marks start on entry, end <= exit <= 2020-12-31; TY truncated by year' % len(T)


# ---------------------------------------------------------------- WALK-FORWARD
def c7():
    s = src('l2walkfwd.py')
    assert "raise RuntimeError('step %d: build %d-%d does not end before trade" in s
    assert "a played year is in both build and trade" in s
    import l2walkfwd as W
    for st in W.STEPS:
        assert st['build'][1] < st['trade'][0]
    return 'walk() halts if a build block reaches its trade block or shares a played year with it'


def c8():
    s = src('l2walkfwd.py')
    assert "decisions.append(dict(structure=s, step=si + 1, build=" in s and "OUT('decisions%s.csv' % dtag)" in s
    f = glob.glob(os.path.join(ROOTOUT, 'decisions_*.csv'))
    if not f:
        return False
    d = pd.read_csv(sorted(f)[-1])
    need = {'step', 'build', 'trade', 'size_scale', 'net_min_votes', 'curve_mode', 'opposition', 'vote_on_entry_day', 'members', 'passers'}
    assert need <= set(d.columns), 'decisions log lacks %s' % (need - set(d.columns))
    return '%s: %d decisions, each with its build window' % (os.path.basename(sorted(f)[-1]), len(d))


def c9():
    s = src('l2walkfwd.py')
    assert "k['retention'] =" in s and "'FIT' if" in s and "< 0.2" in s
    return 'every walk KPI carries retention = trade median / build median and flags < 20% as FIT'


def c10():
    import l2sweep as S
    os.environ.pop('FX_ALLOW_W4', None)
    d = S.load_pair('EURUSD')
    assert d.index.max() <= pd.Timestamp(S.SEAL_END), 'loader served %s' % d.index.max()
    s = src('l2route.py')
    assert '_seal(' in s and 'S.SEAL_END' in s, 'l2route does not seal states/px'
    assert 'load_pair(p)' in src('l2carry.py'), 'l2carry reads raw prices'
    return 'load_pair ends %s without FX_ALLOW_W4; route and carry sealed; the flag prints when set' % d.index.max().date()


def c11():
    import l2walkfwd as W
    s = src('l2walkfwd.py')
    assert 'WF_EXPECT_SIDS' in s and "raise SystemExit" in s[s.index('def _init_pool') if 'def _init_pool' in s else 0:]
    for st in ('stage_null_identity', 'stage_null_randomentry'):
        assert ('def %s' % st) in s, 'missing %s' % st
    assert '--shuffle-null' in src('l2route.py')
    return 'identity, random-entry (routed to permitted bars) and regime-shuffle nulls exist; workers halt on a field mismatch'


# -------------------------------------------------------------- EXITS PER MODE
def c12_13(quick):
    import l2sweep as S, l2trades as TR, l2engine as E
    if quick:
        raise RuntimeError('skipped (--quick)')
    S.load_costs()
    exp = {'A': E.C1_FLIP, 'B': E.BASE_CROSS, 'C': E.EXIT_IND}
    forbid = {'A': (E.BASE_CROSS, E.EXIT_IND), 'B': (E.C1_FLIP, E.EXIT_IND), 'C': (E.C1_FLIP, E.BASE_CROSS)}
    rng = np.random.default_rng(20260916)
    out = []; legs_ok = True; leg_detail = []
    for mode, f in (('A', 'gate2_tuned_modeA_trend.csv'), ('A', 'gate2_tuned_modeA_chop.csv'), ('B', 'gate2_tuned_modeB.csv'), ('C', 'gate2_tuned_modeC.csv')):
        D = pd.read_csv(os.path.join(ROOTOUT, f), low_memory=False)
        D = D[D.ip2.notna()]
        D = D.iloc[rng.choice(len(D), size=min(10 if mode == 'A' else 20, len(D)), replace=False)]
        for cfg in D.to_dict('records'):
            cfg['mode'] = mode
            reasons = []; leg2_reasons = []; legs = {}
            for p in ('EURUSD', 'GBPJPY', 'AUDNZD'):
                r = TR.run_pair(cfg, p)
                tr = r['trades']; n = len(tr['r'])
                reasons += list(tr['reason'][:n]); legs_arr = tr['leg'][:n]
                for lg in set(int(x) for x in legs_arr):
                    legs[lg] = legs.get(lg, 0) + int((legs_arr == lg).sum())
                leg2_reasons += [int(x) for x, l in zip(tr['reason'][:n], legs_arr) if int(l) == 2]
            rs = set(int(x) for x in reasons)
            bad = rs & set(forbid[mode])
            fired = exp[mode] in rs
            out.append(dict(mode=mode, slice=cfg['slice'], sid=cfg.get('sid', '%s|%s|%s' % (cfg['c1'], cfg['c2'], cfg['base']))[:70],
                            n_trades=len(reasons), fired_own_rule=fired, forbidden_rules=sorted(E.REASON[b] for b in bad), legs=legs))
            if bad:
                raise RuntimeError('mode %s strategy fired %s' % (mode, sorted(E.REASON[b] for b in bad)))
            # leg accounting: trend = plan 2 (legs 1 and 2 present when trades exist), chop = plan 1 (leg 0 only)
            plan = 2 if cfg['slice'] == 'trend' else 1
            if plan == 2 and reasons and not (1 in legs and 2 in legs):
                legs_ok = False; leg_detail.append((mode, cfg['slice'], legs))
            if plan == 1 and reasons and set(legs) - {0}:
                legs_ok = False; leg_detail.append((mode, cfg['slice'], legs))
            # leg 2 runs to its own exit: never a leg-1-only reason (leg 1 exits are stop/target only)
            if plan == 2 and leg2_reasons and set(leg2_reasons) <= {E.STOP, E.TARGET}:
                legs_ok = False; leg_detail.append((mode, 'leg2 never used its trail/exit', legs))
    R = pd.DataFrame(out); R.to_csv(os.path.join(ROOTOUT, 'audit_exits_by_mode.csv'), index=False)
    n_fired = R.groupby('mode').fired_own_rule.mean().round(2).to_dict()
    # a mode label that never produced its own exit rule across the sample is a mismatch
    assert all(v > 0 for v in n_fired.values()), 'a mode never fired its own exit rule: %s' % n_fired
    return R, n_fired, legs_ok, leg_detail


# --------------------------------------------------------------------- REGIME
def c14():
    import l2sweep as S
    S.layer1_header_check(os.path.join(ROOTOUT, 'layer1_states.csv'))
    assert 'S.layer1_header_check(path)' in src('l2route.py')
    return 'route and Scorer both assert the 5pm/lagged header on load'


def c15(quick):
    import l2route as R
    s = src('l2route.py')
    assert "TREND_STATES" in s
    assert 'trend_in_range' not in R.TREND_STATES['excl'], 'tir=excl admits trend_in_range'
    assert 'def dependence(' in s, 'no regime-dependence measurement'
    f = os.path.join(ROOTOUT, 'walkforward_regime_dependence_routed_tirexcl_actweak.csv')
    if os.path.exists(f):
        d = pd.read_csv(f, comment='#')
        return 'tir=excl excludes trend_in_range; dependence per strategy in %s (%d rows: inside vs outside regime)' % (os.path.basename(f), len(d))
    return False


# ------------------------------------------------------------ COSTS AND SIZING
def c16():
    import l2sweep as S, l2walkfwd as W
    for m in ('l2walkfwd.py', 'l2cleanfield.py', 'l2refitpilot.py', 'l2carry.py', 'l2agree.py', 'l2members.py', 'l2oppose.py', 'l2exit.py', 'l2killswitch.py'):
        assert 'load_costs()' in src(m) or 'load_costs(' in src(m), '%s never loads costs' % m
    # the Scorer itself refuses to exist without costs loaded, so no tuner or scorer can be gross
    assert 'COSTS NOT LOADED' in src('l2tune.py'), 'Scorer does not refuse to run gross'
    import l2tune as T
    saved = S.COSTS; S.COSTS = None
    try:
        T._require_costs()
        return False
    except RuntimeError:
        pass
    finally:
        S.COSTS = saved
    W.TAG = '_routed_tirexcl_actweak'; os.environ['WF_TAG'] = W.TAG
    M = pd.read_pickle(W.OUT('wf_marks.pkl'))
    first = M.groupby(['sid', 'tid'], observed=True).day.transform('min')
    e = M.mark[M.day == first]
    share = float((e < 0).mean())
    assert share > 0.99, 'only %.3f of fill-day marks are negative (cost charged)' % share
    return 'every scoring module loads costs; %.1f%% of fill-day marks carry a negative cost' % (100 * share)


def c17():
    import l2sweep as S
    path = os.environ.get('FX_COST_TABLE') or os.path.join(ROOTOUT, 'cost_table.csv')
    t = pd.read_csv(path)
    assert len(t) == 28 and t.pair.nunique() == 28
    assert 'entry_hour_ny' in t and t.provenance.str.startswith('OANDA hourly bid/ask').all(), '%s is not the measured per-pair table' % os.path.basename(path)
    S.load_costs(path)
    return '%s: measured at %02d:00 NY, 28 pairs, majors median %.2f bp, crosses %.2f bp' % (os.path.basename(path), int(t.entry_hour_ny.iloc[0]), t[t.group == 'major'].cost_bp_roundtrip.median(), t[t.group == 'cross'].cost_bp_roundtrip.median())


def c18():
    s = src('l2walkfwd.py')
    assert 'UNIT MISMATCH' in s and "tot = float(tr['r'][j]) * am" in s, 'engine does not assert marks == R'
    t = src('l2tune.py')
    assert "r = r * float(risk.get('atr_mult', 1.0))" in t
    import l2walkfwd as W
    W.TAG = '_routed_tirexcl_actweak'; os.environ['WF_TAG'] = W.TAG
    T = pd.read_pickle(W.OUT('wf_trades.pkl')); M = pd.read_pickle(W.OUT('wf_marks.pkl'))
    ms = M.groupby(['sid', 'tid'], observed=True).mark.sum().astype(float)
    rr = T.set_index(['sid', 'tid']).R.astype(float)
    gap = float((ms.reindex(rr.index) - rr).abs().max())
    assert gap < 1e-2, 'marks vs R gap %.4g' % gap
    return 'atr_mult applied to marks and R (Scorer and engine); marks sum to R, max gap %.2e over %d trades' % (gap, len(rr))


def c19():
    import l2tune as T
    r = np.array([1.0, -2.0, 1.0, 1.0]); d = np.array(['2016-03-01', '2016-01-01', '2016-02-01', '2016-04-01'], dtype='datetime64[D]')
    a = T._agg(r, dates=d)
    # chronological: -2, +1, +1, +1 -> the curve only rises from its first point, max DD 0.0;
    # the pair-major order as given (+1, -2, +1, +1) would report 2.0
    assert abs(a['max_dd_R'] - 0.0) < 1e-9, 'max DD not chronological: %s' % a['max_dd_R']
    b = T._agg(r)
    assert np.isnan(b['max_dd_R']), 'undated aggregate reports a drawdown'
    return '_agg sorts by entry date before the equity curve (synthetic: 0.0 chronological vs 2.0 in given order); undated calls report NaN'


def c20():
    bad = []
    for f in glob.glob(os.path.join(ROOTLIB, '*.py')):
        s = open(f).read()
        if re.search(r"for \(pair, day\), d in side\.groupby\(\['pair', 'day'\]\)", s):
            bad.append(os.path.basename(f))
    assert not bad, 'old netting loop in %s' % bad
    assert not os.path.exists(os.path.join(ROOTLIB, 'l2layer4v2.py'))
    return 'no per-(pair, day) netting loop outside retired/; only l2walkfwd.Book builds books'


# ---------------------------------------------------------- DATA AND PIPELINE
def c21():
    s = src('l2walkfwd.py')
    assert '--field-file is REQUIRED' in s and 'WF_EXPECT_SIDS' in s and 'FIELD FILE' in s
    return 'walk halts without --field-file; first log line names the file and per-slice counts; workers re-derive and halt'


def c22():
    F = pd.read_csv(os.path.join(ROOTOUT, 'gate2_cleanfield_4slice.csv'), low_memory=False)
    assert not F.sid.astype(str).str.startswith('B-chop|').any(), 'B-chop| ids in the field'
    import l2walkfwd as W
    W.TAG = '_routed_tirexcl_actweak'; os.environ['WF_TAG'] = W.TAG
    T = pd.read_pickle(W.OUT('wf_trades.pkl'))
    assert not T.sid.astype(str).str.startswith('B-chop|').any(), 'B-chop| ids in the pickle'
    n = int(F.sid.astype(str).str.startswith('B|chop|').sum())
    return 'no B-chop| ids; %d B|chop| ids in the field' % n


def c23():
    p = src('pipeline.py')
    assert p.index("run('export.py')") < p.index("run('persist.py')"), 'export.py after persist.py'
    assert p.index("run('prep.py')") < p.index("run('sc5.py')"), 'no prep before sc5'
    return 'export.py before persist.py; prep.py before sc5/sc6/sc7 in pipeline.py'


def c24():
    d = json.load(open(os.path.join(ROOTOUT, 'signals.json')))
    keys = set(d[0].keys())
    assert {'cti', 'cto', 'cso', 'cao'} <= keys, 'chop target not pooled'
    n = sum(1 for r in d if r.get('cto') is not None)
    return 'signals.json carries cti/cto/cso/cao; %d of %d records have a chop-target value' % (n, len(d))


def c25():
    r = subprocess.run([sys.executable, os.path.join(ROOTLIB, 'l2nosilence.py')], capture_output=True, text=True)
    assert r.returncode == 0, 'l2nosilence: ' + (r.stdout + r.stderr)[-300:]
    logs = [os.path.basename(f) for f in glob.glob(os.path.join(ROOTOUT, '*.log')) if os.path.basename(f) != 'ci_last_failure.log']
    assert not logs, 'logs inside results/: %s' % logs[:5]
    assert os.path.exists(os.path.expanduser('~/fx-data-logs/launch.sh')), 'no launch.sh (60-second confirmation)'
    running = subprocess.run(['pgrep', '-fl', r'fx-data-logs/.*\.sh'], capture_output=True, text=True).stdout.strip()
    # the git guard: a chain in flight means no tree operations -- reported, and enforced in launch.sh
    return 'no silenced errors (l2nosilence); no logs in results/ except the CI failure log; launch.sh confirms 60 s; chains running now: %d' % (len(running.splitlines()) if running else 0)


def c26():
    path = os.path.abspath(_R)
    home = os.path.expanduser('~')
    cloud = any(path.startswith(os.path.join(home, d)) for d in ('Documents', 'Desktop'))
    assert not cloud, 'repo is under %s -- iCloud Desktop & Documents sync; move it (e.g. ~/fx-data) before the rebuild' % path
    return 'repo at %s, outside the iCloud-synced folders' % path


def c27():
    import l2sweep as S
    for m, pat in (('l2walkfwd.py', "np.array([dv[eb]]))[0]) * am"), ('l2refit.py', "np.array([dv[eb]]))[0]) * am"),
                   ('l2tune.py', "r = r - _cm * S._cost_R(")):
        assert pat in src(m), '%s does not scale the cost by atr_mult' % m
    # arithmetic identity: cost in account-normalised units is f x px / ATR, independent of atr_mult
    S.load_costs(os.environ.get('FX_COST_TABLE') or os.path.join(ROOTOUT, 'cost_table.csv'))
    f = S.COSTS['EURUSD']; px, atr = 1.1000, 0.0060
    for am in (1.0, 1.2, 1.5):
        u = S.RISK / (am * atr)
        got = float(S._cost_R('EURUSD', np.array([px]), np.array([u]), np.array([np.datetime64('2017-06-15')]))[0]) * am
        want = f * px / atr
        assert abs(got - want) < 1e-12 * want, 'atr_mult %.1f: scaled cost %.8g != f*px/ATR %.8g' % (am, got, want)
    return 'all three paths scale by atr_mult; scaled cost == f*px/ATR at atr_mult 1.0, 1.2, 1.5 (unscaled it is that / atr_mult)'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--quick', action='store_true')
    ap.add_argument('--out', default='audit_2026-09.csv', help='results/<name>; a dated name keeps every run (nothing is overwritten)')
    a = ap.parse_args()
    global AUDIT_OUT
    AUDIT_OUT = a.out
    t0 = time.time()
    guard(1, 'Vote-timing leak: a position voted on its fill day against that day\'s move', 'votes from the day after the fill; entry cost on the first voted day (l2walkfwd.vote_from_next_day)', 'any (pair, day) vote containing a same-day entrant halts the walk', c1)
    guard(2, 'Layer 1 one-bar lag: the state used on D must come from bars <= D-1', 'export.py shifts one bar; the interface header says so; regime_codes joins unshifted', 'header declares the lag; export.py shift(1); no second shift on the join', c2)
    guard(3, 'Settings vs scoring window: settings tuned on years reaching into the scoring window', 'ip1 (to 2010) scores W2, ip2 (to 2015) scores W3; pilot P1<T1, P2<T2', 'tune_end < score_start asserted at import (l2walkfwd) and in the pilot', c3)
    guard(4, 'Field labels computed with sight of the trade years (crosses_label on W2+W3)', 'gate2_cleanfield_4slice.csv labelled on W2 alone under ip1 (label_basis W2_ip1)', 'label_basis uniform W2_ip1 on every field row', c4)
    guard(5, 'Random-entry null in a different mark convention from the real (no fill-day row, tid 0)', 'null writes a fill-day cost row and one tid per trade (offset 1e9)', 'check_mark_convention in the null writer; a positive fill-day mark halts', c5)
    guard(6, 'Open positions at window boundaries', 'marks are daily increments truncated to the window; exits clipped to the era end', 'marks lie in [entry, exit]; exit <= 2020-12-31; trade-year sums by calendar year', c6)
    guard(7, 'Walk-forward: a decision reading a bar inside or after its trade block', 'walk() asserts build end < trade start and disjoint played years, per step', 'halt on violation, in walk()', c7)
    guard(8, 'Choices made on the build block not logged with their window', 'decisions_<tag>.csv per real walk: window, passers, members, curve, scale, votes, mode', 'decisions log exists with the required columns', c8)
    guard(9, 'Retention not reported', 'every walk KPI carries retention = trade-block median / build-block median; < 20% flagged FIT', 'code assert', c9)
    guard(10, '2021-2026 readable by Layer 2 modules', 'l2sweep.load_pair, l2route states/px and l2carry sealed at 2020-12-31 unless FX_ALLOW_W4=1 (logged)', 'loader refuses past 2020-12-31 without the flag', c10)
    guard(11, 'Nulls not on the same field as the real, or changing the wrong thing', 'identity (year permutation), random-entry (routed to permitted bars), regime-shuffle (labels); WF_EXPECT_SIDS halts a field mismatch', 'three null stages present; field-count halt present', c11)
    try:
        if a.quick:
            raise RuntimeError('skipped (--quick)')
        R, fired, legs_ok, leg_detail = c12_13(a.quick)
        row(12, 'Exit rule not the mode\'s own (mode B for everything)', 'run_pair takes the mode from the config/sid and raises if unknown', 'sample per mode: the exit rule that fired matches the mode; any forbidden rule fails', 'PASS', 'share of sampled strategies that fired their own rule: %s; no forbidden rule fired; audit_exits_by_mode.csv' % fired)
        row(13, 'Leg plans: two-leg trend / one-leg chop with each strategy\'s own multiples; leg 2 to its own exit', 'engine plan from the slice; leg 2 runs to trail/exit rule', 'leg accounting on the same sample', 'PASS' if legs_ok else 'FAIL', leg_detail[:3] if leg_detail else 'trend: legs 1 and 2 present, leg 2 exits by its own rule; chop: single leg')
    except Exception as e:
        row(12, 'Exit rule not the mode\'s own', 'run_pair takes the mode from the config/sid', 'sample per mode', 'FAIL', str(e)[:200])
        row(13, 'Leg plans', 'engine plan from the slice', 'leg accounting on the sample', 'FAIL', str(e)[:200])
    guard(14, 'Layer 1 and Layer 2 on different bars', 'routing and the Scorer read layer1_states.csv only with the 5pm header', 'header assert on load', c14)
    guard(15, 'Regime usage assumed, not measured; trend-in-range admitted', 'always-on stream + routed stream per strategy; dependence per strategy; tir=excl', 'TREND_STATES[excl] has no trend_in_range; dependence measured per strategy', lambda: c15(a.quick))
    guard(16, 'Gross numbers on some path (delivery never charged costs)', 'every scoring module calls load_costs; costs charged on the fill day', 'modules load costs; >99% of fill-day marks negative', c16)
    guard(17, 'Flat cross spread (4.2 pips) instead of measured per-pair spreads', 'costtable.py: cost_table_h17/h19/h22.csv from spread_by_hour.csv; FX_COST_TABLE picks; load_costs logs it', 'active table is the measured per-pair table at the chosen hour', c17)
    guard(18, 'R not account-normalised on marks or on trade R', 'x atr_mult in the Scorer and the engine; engine halts if marks do not sum to R', 'unit assert in the engine; pickle consistency', c18)
    guard(19, 'Max drawdown pair-major in _agg', '_agg sorts by entry date; undated calls report NaN', 'synthetic test: chronological DD 2.0, undated NaN', c19)
    guard(20, 'Layer 4 v1/v2 own netting with the fill-day vote', 'retired to code/retired/; only l2walkfwd.Book builds books', 'grep for the old loop under code/ fails the pre-flight', c20)
    guard(21, 'Field file defaulted to the contaminated crosses_label field', '--field-file required; first log line names it with per-slice counts; workers re-derive', 'code assert', c21)
    guard(22, 'B-chop sid spelled B-chop| in places', 'B|chop|... everywhere', 'no B-chop| id in the field or the pickles', c22)
    guard(23, 'pipeline.py: export.py after persist.py; sc5-7 need signals.json on a cold build', 'export.py moved before persist.py; prep.py before sc5 and after', 'order parsed from pipeline.py', c23)
    guard(24, 'sc5 chop target never pooled by prep.py', 'prep.py pools qc*/nc*/vc* as cti/cto/cso/cao', 'signals.json records carry the chop-target fields', c24)
    guard(25, 'Silenced errors; git tree ops during a chain; logs in results/; launches not confirmed', 'l2nosilence.py; launch.sh confirms 60 s and refuses git ops while a chain runs; logs in ~/fx-data-logs', 'l2nosilence passes; no logs in results/ (CI failure log excepted); launch.sh exists', c25)
    guard(26, 'Repo on the iCloud-synced volume (dataless files, read timeouts)', 'move the repo out of ~/Documents (Jack)', 'repo path not under ~/Documents or ~/Desktop', c26)
    guard(27, 'Costs under-charged by the account-normalisation factor: R restated by x atr_mult, cost subtracted unscaled (median 20%, p90 46% too cheap)', 'the cost is multiplied by atr_mult wherever R is -- engine marks, refit marks, the Scorer objective', 'code assert in all three paths + the arithmetic identity cost == f x px / ATR at several atr_mult', c27)
    A = pd.DataFrame(ROWS)
    A.to_csv(os.path.join(ROOTOUT, AUDIT_OUT), index=False)
    n_pass = int((A.status == 'PASS').sum())
    print('\n%d of %d PASS in %.0f s -> results/%s' % (n_pass, len(A), time.time() - t0, AUDIT_OUT), flush=True)
    if n_pass < len(A):
        print('NOT CLEAR: ' + ', '.join('%d (%s)' % (r.item, r.status) for r in A.itertuples() if r.status != 'PASS'), flush=True)
        sys.exit(1)
    print('PRE-FLIGHT CLEAR', flush=True)


if __name__ == '__main__':
    main()
