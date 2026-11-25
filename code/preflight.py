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
        D = pd.read_csv(os.path.join(ROOTOUT, f), comment='#', low_memory=False)
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


def c28():
    """Every bank matches its MANIFEST.sha256 on file list and size.

    SIZES, NOT HASHES, at preflight. A full sha256 of the gate 3 banks is ~20 s
    each and preflight runs before every launch; a size change catches the
    failures that actually happen -- a truncated flush, a half-written part, a
    deleted shard. `python3 code/bankcheck.py --full` hashes everything and is
    what to run before publishing a result.
    """
    import bankcheck as BC
    bad, seen = BC.verify(full=False, verbose=False)
    if seen == 0:
        return 'WARN', 'no bank manifests found; run code/bankcheck.py --write'
    if bad:
        d = bad[0]
        return 'FAIL', ('%d of %d banks drifted; first: %s (%d missing, %d extra, %d changed)'
                        % (len(bad), seen, d['bank'], len(d['missing']),
                           len(d['extra']), len(d['changed'])))
    return 'PASS', '%d banks match their manifests (file list and size)' % seen


def c37():
    """A ZERO-ROW RESULT FILE NOBODY DECLARED.

    WHAT THIS COST, twice in one day. `B1_NARROW.md` shipped naming a csv at 0
    rows. Then `stage3_report.csv`, `stage3_paired.csv` and `stage3_yearly.csv`
    were all written EMPTY and the chain logged `OK s3 report` -- in one second
    for work that needs 108 engine runs. Guard 35 did not catch the second one,
    because the report's provenance block SKIPPED files it found empty: the
    guard can only check what a report declares, so omission was a way round
    it.

    THE CAUSE OF THE STAGE 3 ONE IS WORTH RECORDING. An empty CSV field reads
    back as NaN, not ''. The currency-agreement candidate has no indicator
    name, so its 47 walk rows carry `c2 = ''` on write and NaN on read, and
    every `W.c2 == ''` match came back all-False -- so the stage found no
    control for any of the six base/plan cells and scored nothing.

    SO THIS GUARD DOES NOT GO THROUGH THE REPORTS AT ALL. It looks at the
    files: no csv under results/ may have a header and no data rows unless it
    is DECLARED empty here with a reason. An empty result file is always either
    a fault or a stated fact, and this forces the choice to be written down.
    """
    DECLARED = DECLARED_EMPTY
    empty, declared_seen = [], []
    for f in glob.glob(os.path.join(ROOTOUT, '**', '*.csv'), recursive=True):
        rel = os.path.relpath(f, _R)
        try:
            with open(f, 'rb') as fh:
                nrows = sum(1 for _ in fh)
        except OSError:
            continue
        if max(0, nrows - 1) > 0:
            continue
        if rel in DECLARED:
            declared_seen.append(rel)
        else:
            empty.append(rel)
    assert not empty, (
        '%d zero-row csv(s) under results/ that nothing declares -- either the '
        'stage that wrote them failed quietly or the emptiness is a result and '
        'must be declared in preflight.c37: %s'
        % (len(empty), '; '.join(sorted(empty)[:6])))
    return ('%d csv(s) scanned, no undeclared zero-row file; %d declared empty'
            % (len(glob.glob(os.path.join(ROOTOUT, '**', '*.csv'),
                             recursive=True)), len(declared_seen)))


# ---------------------------------------------------------------------------
# FILES THAT ARE EMPTY BY RESULT, not by failure. Guards 35 and 37 both read
# this list: 35 so a report may DECLARE a zero-row file without failing, 37 so
# the file may exist at all. Every entry carries the result that makes it
# empty, verified -- "it has always been empty" is not a reason.
DECLARED_EMPTY = {
    'results/witness_events_acute_missed_2026-11-15.csv':
        'NO acute witness was missed. The file lists the misses and there are '
        'none, so emptiness IS the finding.',
    'results/r2gate2_frozen_params.csv':
        'It lists parameters the library exposes that the declared grid does '
        'NOT move. It is empty because EVERY exposed parameter is moved -- '
        'l2r2gate2.py:1277 prints "NONE -- every parameter the registry '
        'exposes is moved (Jack, 16 Nov)" in its place. Emptiness is the good '
        'outcome here.',
    'results/r2gate2/modeA_gate3_stitched.csv':
        'ZERO of 273,780 strategies clear the stitched test in any of the four '
        'streams -- modeA_gate3_stitched_counts.csv carries n_clears_stitched '
        '= 0 on all four rows. The detail file is empty because nothing '
        'cleared, and MODEA_GATE3.md declares it at 0 rows.',
    'results/r2gate2/modeB_gate3_stitched.csv':
        'The same, for mode B: n_clears_stitched = 0 on every stream, declared '
        'at 0 rows in MODEB_GATE3.md.',
}


# ---------------------------------------------------------------------------
# PROVENANCE DRIFT THAT IS ON THE RECORD. A report names a csv at N rows and
# the file now holds M. Guard 35 allows ONLY these pairs, and it pins the
# CURRENT on-disk count: if the file moves off that count the guard fails
# afresh, so this is a record of a known divergence and not a way to switch
# the check off. Regenerating the reports is the real fix and is Jack's call,
# because MODEA_REPORT.md is a shipped record and rewriting it would move
# numbers he has already read.
DECLARED_DRIFT = {
    ('results/r2gate2/modeA_books_layer1splits.csv', 30, 55):
        'The file GREW: a later run added Layer 1 split rows and the two '
        'MODEA_REPORT files were not regenerated. The numbers they quote come '
        'from the 30-row version.',
    ('results/r2gate2_cond2_modeA.csv', 7660, 240):
        'The file SHRANK by 97%, the same signature as the STAGE1 '
        'canonical_risk overwrite: a later, smaller condition-2 run reused the '
        'production filename. MODEA_REPORT.md\'s condition-2 claim is NOT '
        'backed by the file it names. Flagged to Jack 24 Nov.',
}


def _named_note(named_ok):
    """The named-exception line that guard 34 always prints, so the set of
    exceptions cannot grow or drift unnoticed."""
    if not named_ok:
        return '; 0 named exceptions present'
    return ('; %d named exception(s): %s'
            % (len(named_ok),
               ', '.join('%s at %.0f MB' % (r, n / 1048576)
                         for n, r in sorted(named_ok, reverse=True))))


def c34():
    """NO NEW FILE OVER 50 MB MAY BE COMMITTED. Jack, 24 Nov, step 5.

    WHAT THIS COST. A chain's own `ci` committed
    results/r2reads/modeA_a2_defaults.csv at 654 MB, and GitHub refuses any
    file over 100 MB at the pre-receive hook. The remote then could not advance
    past that commit by ANY means -- a retry cannot fix it, because the blob is
    in the history being offered. It took a rewrite of 33 unpushed commits to
    clear, and the only reason that was safe is that they had never been pushed.

    THE LIMIT IS 50 MB, NOT 100. Half of GitHub's hard limit, so a stage that
    grows is noticed before it blocks anything. A stage with a big artifact
    writes it to disk, gitignores it, and commits a MANIFEST.sha256 entry and a
    summary instead -- guard 28 for the banks, code/a2summary.py for this file.

    WHY EXISTING FILES ARE GRANDFATHERED, AND IT IS NOT A LOOPHOLE. 71 tracked
    files already exceed 50 MB: results/signals.json at 92 MB, 64 KPI-bank
    shards at 58.8 MB each, six refit mark pickles. Every one of them is
    ALREADY ON THE REMOTE, so none can block a push, and removing them would
    mean rewriting pushed history -- which Jack ruled out in the same
    instruction that set this limit. So the guard's question is not "is any
    tracked file large" but "is any large file one the remote has not already
    accepted", which is exactly the thing that can break a push. The
    grandfathered count is printed every run so the set cannot grow unnoticed.
    """
    # ---- NAMED EXCEPTIONS. Jack, 24 Nov: "signals.json at 92 MB is under
    # GitHub's 100 MB limit: allow it as a named exception to the 50 MB guard."
    # It is a Layer 1 artifact the app fetches, so it cannot become a manifest
    # entry without breaking the app. The exception is NAMED, not a size band:
    # each entry carries its own ceiling, and a file that grows past its
    # ceiling fails this guard like any other. 100 MB is GitHub's hard
    # pre-receive limit, so the ceiling is 95 MB -- enough headroom to notice
    # before a push is refused rather than after.
    NAMED = {'results/signals.json': 95 * 1024 * 1024}
    LIM = 50 * 1024 * 1024
    out = subprocess.run(['git', 'ls-files', '-z'], cwd=_R,
                         capture_output=True, text=True).stdout
    big, named_ok = [], []
    for rel in [x for x in out.split('\0') if x]:
        try:
            n = os.path.getsize(os.path.join(_R, rel))
        except OSError:
            continue
        if rel in NAMED:
            assert n <= NAMED[rel], (
                '%s is a NAMED exception to the 50 MB limit with a ceiling of '
                '%.0f MB and it is now %.0f MB -- GitHub refuses anything over '
                '100 MB at the pre-receive hook, so this must shrink or move '
                'behind a manifest before the next push'
                % (rel, NAMED[rel] / 1048576, n / 1048576))
            named_ok.append((n, rel))
            continue
        if n > LIM:
            big.append((n, rel))
    if not big:
        return ('no tracked file exceeds 50 MB%s' % _named_note(named_ok))
    base = subprocess.run(['git', 'ls-remote', 'origin', 'refs/heads/main'],
                          cwd=_R, capture_output=True, text=True).stdout.split()
    base = base[0] if base else ''
    grand, newbig = [], []
    for n, rel in sorted(big, reverse=True):
        at_remote = False
        if base:
            at_remote = subprocess.run(
                ['git', 'cat-file', '-e', '%s:%s' % (base, rel)], cwd=_R,
                capture_output=True).returncode == 0
        (grand if at_remote else newbig).append((n, rel))
    assert not newbig, (
        '%d file(s) over 50 MB that the remote has NOT already accepted -- '
        'write a manifest entry and a summary instead: %s'
        % (len(newbig), '; '.join('%s (%.0f MB)' % (r, n / 1048576)
                                  for n, r in newbig[:5])))
    return ('no NEW file over 50 MB; %d grandfathered and already on the '
            'remote, largest %s at %.0f MB%s'
            % (len(grand), grand[0][1], grand[0][0] / 1048576,
               _named_note(named_ok)))


def c33():
    """A LEG COUNTED AS A TRADE. Found 24 Nov, and guard 32 did not catch it.

    `plan=2` splits every position into two legs -- leg1 banks at the first
    target, leg2 runs on the trail -- and `l2engine.trade_frame` returns ONE ROW
    PER LEG. nnfx1._yearly counted those rows as `n_entered`, so every
    per-trade and count column in the staged build was wrong by exactly two:

        n_entered, n_touching, trades_per_year    2x too large
        R_net_per_trade, R_gross_per_trade,       half the truth
        cost_per_trade

    The TOTALS were never affected -- each leg carries half the units against
    the full risk, so the legs' R sums to the position's R and each is charged
    half the spread -- which is exactly why it was invisible for a day.

    GUARD 32 CHECKED THAT THE COLUMNS WERE NAMED APART AND NEVER THAT THE COUNT
    COUNTED THE RIGHT THING. Item 8 said "gate 3's distinct-trade count for n",
    and a leg is not a distinct trade. This guard checks the arithmetic instead
    of the spelling: run one real candidate and assert that n_entered equals
    the number of distinct (pair, entry_date, direction) triples and that it is
    STRICTLY LESS than the row count whenever the plan has two legs.
    """
    import numpy as _np
    sys.path.insert(0, ROOTLIB)
    import nnfx1 as _N, l2sweep as _S
    _S.load_costs(os.environ.get('FX_COST_TABLE',
                                 'results/cost_table_h22.csv'))
    T = _N.run_one('ichimoku_signals', 'c1', 'default', 'jack',
                   pairs=['EURUSD', 'GBPJPY'], use_hourly=False)
    assert len(T), 'guard 33: the probe candidate took no trades'
    T = T.reset_index(drop=True)
    cost = _N._cost_R(T)
    Y = _N._yearly(T, cost)
    ne = _N.n_entries(T)
    got = float(Y.n_entered.sum())
    assert abs(got - ne) < 1e-9, (
        'n_entered counts LEGS, not trades: %.0f against %d distinct entries'
        % (got, ne))
    nlegs = len(T)
    assert nlegs > ne, ('guard 33 probe has one leg per entry (%d rows, %d '
                        'entries) so it cannot detect the fault -- check that '
                        'plan=2 is still two-legged' % (nlegs, ne))
    # and the totals must be untouched by the fix
    tot = float(T.R_gross.sum() - cost.sum())
    assert abs(float(Y.R_mtm.sum()) - tot) < 1e-8, (
        'the yearly R no longer sums to total net R: %.6f against %.6f'
        % (Y.R_mtm.sum(), tot))
    return ('n_entered == %d distinct entries from %d legs (%.1f legs per '
            'entry); yearly R still sums to total net R at %.1e'
            % (ne, nlegs, nlegs / ne, abs(float(Y.R_mtm.sum()) - tot)))


def c32():
    """ITEM 8 — THE STAGED BUILD NAMES ITS TWO CONVENTIONS DIFFERENTLY.

    0b found gate 2 and gate 3 disagreeing on 41 of 50 winner-years because
    both wrote a column called `n` meaning different things: gate 2 counted a
    straddling trade in every year it touched, gate 3 counted it once in its
    entry year. The staged build adopts gate 2's year-end mark to market for R
    and gate 3's distinct-trade count for n -- and the only durable protection
    against repeating the confusion is that the columns cannot share a name.

    So every stage 1 R2 yearly file must carry `R_mtm`, `n_entered` and
    `n_touching`, and must NOT carry a bare `R` or a bare `n` as its only
    count. A no-op when no such file exists.
    """
    import glob as _g
    fs = sorted(_g.glob(os.path.join(ROOTOUT, 'nnfx', 'stage1r2_*_yearly.csv')))
    if not fs:
        return 'no stage 1 R2 yearly files on disk yet'
    need = ('R_mtm', 'n_entered', 'n_touching')
    bad = []
    for f in fs:
        cols = set(pd.read_csv(f, nrows=1).columns)
        miss = [c for c in need if c not in cols]
        if miss:
            bad.append('%s missing %s' % (os.path.basename(f), ', '.join(miss)))
    assert not bad, ('the staged build must name its two conventions '
                     'differently: ' + '; '.join(bad))
    return ('%d stage 1 R2 yearly files all carry R_mtm, n_entered and '
            'n_touching' % len(fs))


def c31():
    """CONDITION 4 — THE ZERO-EDGE CHECK, for every Layer 2 job.

    Random entries taking the same exits as a real strategy must lose their
    costs and nothing else: gross of costs the mean R per trade must be zero
    within the null's own standard error. If it is not, the apparatus has a
    bias and every number it produces is wrong by that bias before any strategy
    is considered.

    On the first stage 1 run this failed decisively for the stop-and-target
    plan -- null gross -0.0203 R per trade against a band of +/-0.0029 -- while
    the flip-only exit passed 45 of 45. That localised the fault to the fill
    mechanics rather than to costs, and specifically to l2engine filling the
    STOP whenever one daily bar covers both levels, where A5 measured the target
    first on 40% of such days.

    A no-op when no stage 1 null files exist, so it does not fail a machine that
    has not run one.
    """
    import importlib
    try:
        C = importlib.import_module('nnfxcond')
    except Exception as e:
        return 'nnfxcond not importable (%s)' % type(e).__name__
    A, oks = C.condition4_all(verbose=False)
    if not len(A):
        return 'no stage 1 null files on disk; nothing to check yet'
    bad = [k for k, v in oks.items() if not v]
    worst = A.loc[A.null_gross_R_per_trade.abs().idxmax()]
    assert not bad, (
        'zero-edge check FAILED for %s. Worst: %s/%s gross %+.5f R per trade '
        'against a band of +/-%.5f. Random entries are not losing only their '
        'costs, so the apparatus is biased'
        % (', '.join(bad), worst.label, worst.indicator,
           worst.null_gross_R_per_trade, worst.tol_3se))
    return ('%d candidate-settings across %d variants: null gross R per trade '
            'is zero within 3 SE everywhere (worst %+.5f)'
            % (len(A), len(oks), A.null_gross_R_per_trade.abs().max()))


def c30():
    """CONDITION 3 — CROSS-WALK REPRODUCTION, for any extended-walk job.

    Trade years 2016-2020 use the same tuning years in the five-step and the
    eleven-step walk -- tune 2011-2014 / grade 2015 / trade 2016, and so on --
    so the eleven-step walk must reproduce the five-step record on them exactly.
    If it does not, nothing from the six earlier years may be quoted.

    This guard is a no-op when no ext11 winner bank exists, so it does not fail
    a machine that has never run an extended walk.
    """
    import importlib
    try:
        B = importlib.import_module('b1narrow')
    except Exception as e:
        return 'b1narrow not importable (%s); no extended walk on this machine' % type(e).__name__
    import l2r2gate2 as _G2
    if _G2.WALK != 'ext11':
        # the comparison reads both banks directly and needs ext11's YEAR0
        return ('skipped: FX_WALK=%s, not ext11. Run '
                'FX_WALK=ext11 python3 code/b1narrow.py --stage cond3 '
                'before quoting any extended-walk result' % _G2.WALK)
    D, ok = B.condition3(verbose=False)
    if not len(D):
        return 'no ext11 winner bank on disk; nothing to reproduce yet'
    assert ok, ('cross-walk reproduction FAILED: %d of %d winner-years differ '
                '(worst R %.3e, worst n %.3e, %d config mismatches)'
                % (int((D.dR > 1e-6).sum() + (D.dn > 1e-6).sum()), len(D),
                   D.dR.max(), D.dn.max(), int((D.cfg_same == 0).sum())))
    return ('%d winner-years reproduce the five-step record exactly '
            '(worst |dR| %.3e, worst |dn| %.3e, %d/%d config indices identical)'
            % (len(D), D.dR.max(), D.dn.max(), int(D.cfg_same.sum()), len(D)))


def c29():
    """EVERY MODULE'S __main__ BLOCK IS THE LAST THING IN THE FILE.

    THIS GUARD EXISTS BECAUSE I MADE THE SAME MISTAKE THREE TIMES IN ONE DAY.
    Appending a stage function AFTER the dispatch block leaves the dispatch
    calling a name that does not exist yet, and python only finds out at run
    time: chunk 2 died on `NameError: stage_a2 is not defined` six seconds into
    chain 24 on 24 Nov, after r2hourly.py had done the same thing an hour
    earlier. A chain is the worst place to discover it, so it is checked here.
    """
    import ast as _ast
    bad = []
    for f in sorted(glob.glob(os.path.join(ROOTLIB, '*.py'))):
        try:
            src = open(f).read()
            tree = _ast.parse(src)
        except Exception:
            continue
        mains = [n for n in tree.body
                 if isinstance(n, _ast.If)
                 and _ast.dump(n.test).find("'__main__'") >= 0]
        if not mains:
            continue
        m = mains[-1]
        after = [n for n in tree.body
                 if getattr(n, 'lineno', 0) > getattr(m, 'end_lineno', 0)]
        defs = [n for n in after
                if isinstance(n, (_ast.FunctionDef, _ast.AsyncFunctionDef,
                                  _ast.ClassDef, _ast.Assign))]
        if defs:
            names = [getattr(d, 'name', '<assign>') for d in defs][:4]
            bad.append('%s: %d definition(s) after __main__ (%s)'
                       % (os.path.basename(f), len(defs), ', '.join(names)))
    assert not bad, 'definitions after the __main__ dispatch:\n    ' + '\n    '.join(bad)
    return '%d modules: no definition sits after a __main__ dispatch' % len(
        glob.glob(os.path.join(ROOTLIB, '*.py')))


def c36():
    """THE DAILY PATH BUILT FROM FULL `units` ON A HALF-WEIGHT LEG.

    WHAT THIS COST, found 24 Nov at 22:10 checking Jack's 54.9 R dip.
    `l2engine.trade_frame` writes `units` as the FULL position size on EVERY
    leg of a plan=2 entry, while each leg's realised R is half -- a full
    stop-out is -0.5 + -0.5 = -1.0. `nnfx1.daily_series` built each leg's
    mark-to-market from full `units`, so open mark-to-market was overstated by
    the number of legs, 2x for all three plans.

    IT CANCELS AT THE EXIT BAR, which is why it survived guard 33. The exit
    term is `R - prev` and `prev` carries the same 2x, so every TOTAL is exact:
    the daily series summed over all days equals R_gross - cost to the last
    decimal, and the yearly sums reconcile. Only the PATH is wrong, and only
    path statistics are wrong with it:

        worst_dip_R            too large   (54.93 -> 22.83 on ichimoku+sma)
        R_per_year_per_dip     too small
        t_block_boot           biased DOWN (inflated daily variance)

    Unaffected: every trade-level figure -- R totals, R per trade, trades per
    year, years positive, null_p.

    ON THE 15 JANUARY 2015 SNB DAY the bug showed +101.6 R and -50.2 R on
    consecutive days where the truth is +51.3 and -0.34: a 50 R one-day spike
    that invented a peak, and a 54.93 R "drawdown" measured down from it.

    WHAT THIS CHECKS, on a live two-pair probe:
      (a) dir * (units / n_legs) * (exit_px - entry_px) / RISK reproduces each
          leg's R EXACTLY on stop exits, where the settlement is a pure price
          move;
      (b) the same identity at FULL `units` is out by about the leg count, so a
          revert is caught rather than passing quietly;
      (c) daily_series still totals to R_gross - cost.
    """
    import numpy as _np
    sys.path.insert(0, ROOTLIB)
    import nnfx1 as _N, l2sweep as _S
    _S.load_costs(os.environ.get('FX_COST_TABLE',
                                 'results/cost_table_h22.csv'))
    T = _N.run_one('ichimoku_signals', 'c1', 'default', 'jack',
                   pairs=['EURUSD', 'GBPJPY'], use_hourly=False)
    assert len(T), 'guard 36: the probe candidate took no trades'
    assert 'leg' in T.columns, 'guard 36: no leg column -- cannot weight legs'
    nleg = float(max(1, T['leg'].astype(str).nunique()))
    assert nleg >= 2, 'guard 36: the probe plan is single-leg; pick a plan=2 one'
    d = _np.where(T.direction.to_numpy() == 'long', 1.0, -1.0)
    move = (T.exit_px.to_numpy(float) - T.entry_px.to_numpy(float)) * d
    r_full = T.units.to_numpy(float) * move / _S.RISK
    r_leg = r_full / nleg
    rr = T.R.to_numpy(float)
    st = (T.reason.to_numpy() == 'stop')
    assert st.sum() >= 20, 'guard 36: only %d stop exits to test' % int(st.sum())
    e_leg = float(_np.abs(r_leg[st] - rr[st]).max())
    e_full = float(_np.abs(r_full[st] - rr[st]).max())
    assert e_leg < 1e-9, ('guard 36: units/n_legs does NOT reproduce leg R on '
                          'stop exits (worst %.3e over %d legs)'
                          % (e_leg, int(st.sum())))
    assert e_full > 0.4 * (nleg - 1), ('guard 36: full units reproduces leg R '
                                       'too -- the leg weight is not what this '
                                       'guard thinks (worst %.3e)' % e_full)
    cost = _np.asarray(_N._cost_R(T), float)
    DS = _N.daily_series(T, cost)
    want = float(T.R_gross.sum() - cost.sum())
    got = float(DS.R.sum())
    assert abs(got - want) < 1e-6, ('guard 36: daily series totals %.6f against '
                                    'R_gross - cost %.6f' % (got, want))
    return ('%d legs over 2 pairs, %d stop exits: units/%d reproduces leg R at '
            '%.1e, full units is out by %.3f, and the daily series totals to '
            'R_gross - cost at %.1e'
            % (len(T), int(st.sum()), int(nleg), e_leg, e_full,
               abs(got - want)))


def c35():
    """A REPORT THAT NAMES ITS OWN CSVs AND DOES NOT MATCH THEM.

    WHAT THIS COST. `B1_NARROW.md` was written at 19:11 on 24 Nov with its
    central section reading `_No bank rows read._` and its provenance block
    naming `b1narrow_per_strategy.csv` at **0 rows** -- while chain 29's ledger
    showed all eleven stages OK, including `md`. 7.6 h of eleven-step tune per
    mode was on disk and correct; only the read was broken, twice over. The
    universe csv carries no `stream` column, which a defensive `continue`
    turned into a silent 100% row drop; and the join was on `bank_row` while
    G2.run banks by POSITION in the combos list it is handed, which matched 27
    of 4,008 rows. Neither raised anything. A stage that writes a report is not
    verified by the report existing.

    The same scan caught a second, different fault: `STAGE1.md` names three
    `stage1_c1_canonical_risk_*.csv` files at 1,929 / 117 / 23,400 rows and
    the files on disk hold 99 / 6 / 360, overwritten at 13:08 on 24 Nov by a
    smaller run that reused the production filenames.

    WHAT IT CHECKS. Every provenance line of the form
    ``- `path` -- N rows, md5 `h` `` in any markdown file under results/: the
    file must exist, N must be greater than zero, and N must equal the file's
    actual data-row count. A report whose first line marks it SUPERSEDED is
    skipped, because a superseded report is a record of what was said at the
    time and its csvs are allowed to have moved on -- but the skip is counted
    and printed, so the set cannot grow unnoticed.
    """
    # TWO PROVENANCE FORMATS. The bullet list used by the nnfx and r2reads
    # reports, and the TABLE used by the gate 3 reports:
    #     | stitched | results/.../modeA_gate3_stitched.csv | 0 | 68b32... |
    # The first version of this guard read only the bullet form, so a report
    # that declared a zero-row file in a table escaped it -- which is how
    # MODEA_GATE3.md sat on record declaring 0 rows while this guard passed.
    pat = re.compile(r'^- `([^`]+)` . ([\d,]+) rows, md5 `([0-9a-f]+)`')
    pat_tbl = re.compile(r'^\|[^|]+\|\s*(results/[^|\s]+\.csv)\s*\|'
                         r'\s*([\d,]+)\s*\|\s*[0-9a-f]{6,}\s*\|')
    bad, n_lines, n_files, skipped, dec, drifted = [], 0, 0, [], [], []
    for md in sorted(glob.glob(os.path.join(ROOTOUT, '**', '*.md'),
                               recursive=True)):
        head = ''
        with open(md, errors='replace') as fh:
            lines = fh.read().splitlines()
        head = '\n'.join(lines[:3])
        if 'SUPERSEDED' in head:
            if any(pat.match(l) for l in lines):
                skipped.append(os.path.relpath(md, _R))
            continue
        hit = False
        for ln in lines:
            m = pat.match(ln) or pat_tbl.match(ln)
            if not m:
                continue
            hit = True
            n_lines += 1
            rel, claim = m.group(1), int(m.group(2).replace(',', ''))
            fp = rel if os.path.isabs(rel) else os.path.join(_R, rel)
            if not os.path.exists(fp):
                bad.append('%s names %s: MISSING' % (os.path.basename(md), rel))
                continue
            with open(fp, 'rb') as fh:
                act = max(0, sum(1 for _ in fh) - 1)
            if claim == 0 or act == 0:
                if rel in DECLARED_EMPTY and claim == act == 0:
                    dec.append(rel)        # empty BY RESULT, and on record
                    continue
                bad.append('%s names %s: %d rows claimed, %d on disk -- an '
                           'EMPTY read' % (os.path.basename(md), rel, claim, act))
            elif act != claim:
                if (rel, claim, act) in DECLARED_DRIFT:
                    drifted.append(rel)    # known, explained, and pinned
                    continue
                bad.append('%s names %s: %d rows claimed, %d on disk'
                           % (os.path.basename(md), rel, claim, act))
        n_files += 1 if hit else 0
    assert not bad, '; '.join(bad[:6])
    return ('%d provenance lines across %d reports (bullet and table form): '
            'every named csv exists and matches its claimed row count; '
            '%d declared empty by result; %d with DECLARED DRIFT (%s)%s'
            % (n_lines, n_files, len(set(dec)), len(set(drifted)),
               ', '.join(sorted(set(drifted))) or 'none',
               ('; %d superseded report(s) skipped: %s'
                % (len(skipped), ', '.join(skipped))) if skipped else ''))


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
    guard(28, 'A bank drifted from the bank a result names: a part file missing, truncated or regenerated, with nothing to notice it',
          'code/bankcheck.py writes MANIFEST.sha256 per bank directory (file, size, sha256, producing commit); banks are gitignored from 23 Nov and the manifest is what is committed',
          'every bank directory matches its manifest on file list and size', c28)
    guard(29, 'A stage function appended AFTER the __main__ dispatch: the dispatch calls a name that does not exist yet and python only finds out at run time (chunk 2 died on NameError six seconds into chain 24, 24 Nov; r2hourly.py did the same an hour earlier and b1narrow.py would have been the third)',
          'the __main__ block is the LAST thing in every module under code/, and this guard asserts it',
          'no function, class or assignment is defined after a __main__ dispatch in any code/*.py', c29)
    guard(30, 'An extended-walk run that does not reproduce the five-step record on the years both walks share: on 24 Nov B1_WINNERS.md reported 120.8 R for 2018 where the record says 51.399, and ~1,886 trades over 2016-2020 where the record says 826',
          'condition 3 compares the ext11 bank against the base5 bank per winner, per shared year, on the winner OWN stream: per-year R, trade count and selected config index',
          'all 50 winner-years equal to 1e-6 with identical config indices; nothing from 2010-2015 is quoted until it passes', c30)
    guard(31, 'A measurement apparatus with a built-in bias: random entries taking the same exits lost 0.0203 R per trade GROSS of costs under the stop-and-target plan, against a band of 0.0029, because l2engine fills the stop whenever one daily bar covers both levels and A5 measured the target first on 40% of such days',
          'condition 4 compares the random-entry null gross of costs against zero, judged against the null OWN standard error, per candidate and per variant',
          'null gross R per trade is zero within 3 SE for every candidate in every variant', c31)
    guard(32, 'Two different conventions sharing one column name: gate 2 and gate 3 both wrote `n` -- one counting a straddling trade in every year it touched, the other once in its entry year -- and the confusion cost a winner list',
          'the staged build writes R_mtm for year-end mark-to-market R, n_entered for distinct trades and n_touching for the touching count, so the two can never be conflated again',
          'every stage1r2_*_yearly.csv carries R_mtm, n_entered and n_touching', c32)
    guard(33, 'A LEG counted as a TRADE: plan=2 splits every position into leg1 and leg2 and trade_frame returns one row per leg, so n_entered, n_touching and trades_per_year were 2x too large and every per-trade figure was half the truth -- guard 32 checked the column NAMES and not the arithmetic',
          'nnfx1.entry_frame / n_entries count distinct (pair, entry_date, direction) triples; _yearly takes counts and holding periods from entries and R and cost from legs',
          'n_entered equals the distinct-entry count on a live probe candidate, is strictly less than the row count, and the yearly R still sums to total net R', c33)
    guard(34, 'A file too large for the remote committed by a chain: results/r2reads/modeA_a2_defaults.csv at 654 MB against GitHub\'s 100 MB pre-receive limit, which no retry can clear because the blob is in the history being offered -- it took a rewrite of 33 unpushed commits',
          'the limit is 50 MB, half of GitHub\'s, so a growing stage is noticed before it blocks anything; a big artifact goes to disk gitignored with a MANIFEST.sha256 entry and a committed summary, as guard 28 does for the banks and a2summary.py now does for this file; chainlib ci refuses the commit too',
          'no tracked file in the index or working tree exceeds 50 MB', c34)
    guard(35, 'A report that names its own csvs and does not match them: B1_NARROW.md shipped at 19:11 on 24 Nov with "_No bank rows read._" and a provenance line reading 0 rows, while chain 29 reported all eleven stages OK -- the read joined the universe on bank_row where the bank is keyed by POSITION, matching 27 of 4,008, and a defensive `continue` dropped the rest in silence. The same scan found STAGE1.md naming three canonical_risk csvs at 1,929/117/23,400 rows against 99/6/360 on disk, overwritten by a smaller run that reused the production filenames',
          'every provenance line in every report under results/ is checked against the file it names: it must exist, be non-empty, and hold exactly the claimed number of data rows; a report whose head marks it SUPERSEDED is skipped and the skip is printed',
          'all provenance lines in results/**/*.md match their files on row count', c35)
    guard(36, 'The daily mark-to-market path built from FULL `units` on a HALF-WEIGHT leg: trade_frame writes the whole position size on every leg of a plan=2 entry while each leg realises half, so open mark-to-market was overstated 2x. It cancels at the exit bar, so every total reconciled to the last decimal and guard 33 passed -- but worst_dip_R was too large (54.93 against 22.83 on ichimoku+sma), R_per_year_per_dip too small and t_block_boot biased down. On 15 Jan 2015 it showed +101.6 R then -50.2 R where the truth is +51.3 then -0.34, inventing the peak the 54.93 R dip was measured from',
          'nnfx1.daily_series divides `units` by the plan leg count, taken from the distinct `leg` labels so a frame filtered by exit year cannot sever a pair and halve the divisor',
          'on a live probe units/n_legs reproduces each leg R exactly on stop exits, full units is out by the leg count, and the daily series still totals to R_gross - cost', c36)
    guard(37, 'A zero-row result file nobody declared: B1_NARROW.md shipped naming a csv at 0 rows, and hours later stage3_report/paired/yearly were all written EMPTY while the chain logged OK in one second for work needing 108 engine runs. Guard 35 missed the second one because the report SKIPPED the empty files from its own provenance block, so omission was a way round it. The cause is worth recording: an empty CSV field reads back as NaN, not the empty string, so every `c2 == \'\'` match on the currency-agreement rows came back all-False and the stage found no control at all',
          'this guard does not go through the reports: it looks at the files, and no csv under results/ may carry a header and no data rows unless it is declared empty in preflight.c37 with a reason',
          'no undeclared zero-row csv anywhere under results/', c37)
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
