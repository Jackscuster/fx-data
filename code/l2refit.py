import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""THE CLEAN REBUILD FROM GATE 2 -- rolling five-year tuning (HANDOFF 0e, 16 Sep).

For every candidate strategy and every window W = [y, y+4]:
    tune on W with gate 2's grids (cap 6, full pass)        -> settings_W
    label on W: gate-2 floors on W's own record under settings_W (audit 4)
    score under settings_W, ROUTED and ALWAYS-ON (audit 15):  W itself,
        the trade block y+5 (and y+5..2020 for the decay curve)
Every number per strategy goes through l2tune.Scorer -- no Book. Then
--stage marks writes, per step, the build block AND the trade block scored
under settings_W as an always-on marks stream with a `step` column, which
l2route routes and l2walkfwd walks with WF_STEPS set (per-step assertions,
decisions log, retention, nulls -- audit 7-11).

    --stage tune    --candidates <csv> --windows 2011-2015:2016,...  --jobs N  [--reuse <pilot csv>]
    --stage marks   --candidates <csv> --windows ...  --jobs N  --suffix _refit_smoke
    --stage report  --windows ...

Resumable: one row per (sid, window) in results/refit_settings<suffix>_s<shard>.csv.
Sharded by md5(sid) % jobs so a restart never duplicates work.
"""
import argparse, glob, hashlib, json, time
import numpy as np, pandas as pd
import l2sweep as S
import l2tune as T

CAP = 6


def parse_windows(spec):
    """'2011-2014:2015:2016' = tune on 2011-2014, GRADE on 2015 (never seen by the
    tuner, reported never used), trade 2016 untouched -- the BLIND-LABEL design
    (Jack, 21 Sep). '2011-2015:2016' = the older tune:trade form, no grade."""
    out = []
    for part in spec.split(','):
        bits = part.split(':')
        b0, b1 = (int(x) for x in bits[0].split('-'))
        if len(bits) == 3:
            g0, g1 = (int(x) for x in bits[1].split('-')) if '-' in bits[1] else (int(bits[1]), int(bits[1]))
            t = bits[2]
        else:
            g0 = g1 = None; t = bits[1]
        t0, t1 = (int(x) for x in t.split('-')) if '-' in t else (int(t), int(t))
        if g0 is not None:
            assert b1 < g0 and g1 < t0, 'window %s: tune must end before the grade year and the grade year before the trade block' % part
        assert b1 < t0, 'window %s does not end before its trade block' % part      # audit 3 / 7
        out.append(dict(name='%d-%d' % (b0, b1), build=(b0, b1), grade=((g0, g1) if g0 is not None else None), trade=(t0, t1),
                        span=(b0, t1)))
    return out


def windows_table(wins):
    """The Scorer's window table: tune window, grade year, trade block, every sealed year after the tune window."""
    W = {}
    for w in wins:
        W['B' + w['name']] = ('%d-01-01' % w['build'][0], '%d-12-31' % w['build'][1])
        if w['grade']:
            W['G' + w['name']] = ('%d-01-01' % w['grade'][0], '%d-12-31' % w['grade'][1])
        W['T' + w['name']] = ('%d-01-01' % w['trade'][0], '%d-12-31' % w['trade'][1])
        for y in range(w['build'][1] + 1, 2021):
            W['Y%d' % y] = ('%d-01-01' % y, '%d-12-31' % y)
    return W


KEEP = ('n', 'expectancy_R', 'total_R', 'profit_factor', 'sharpe', 'sortino', 'calmar', 'max_dd_R', 'win_rate', 'avg_win_R', 'avg_loss_R')


def g3_composite(a):
    """count of gate-3 bars cleared on a record (0-5); max_dd_frac = max DD / gross profit"""
    import l2gate3 as G3
    gp = a['avg_win_R'] * a['win_rate'] * a['n'] if np.isfinite(a['avg_win_R']) else np.nan
    ddf = a['max_dd_R'] / gp if gp and gp > 0 else np.inf
    return int(a['expectancy_R'] >= G3.BARS['expectancy_R']) + int(a['profit_factor'] >= G3.BARS['profit_factor']) + \
        int(np.nan_to_num(a['sortino'], nan=-9) >= G3.BARS['sortino']) + int(a['calmar'] >= G3.BARS['calmar']) + int(ddf <= G3.BARS['max_dd_frac'])


GRADE_MIN_TRADES = 10   # gate 2's 50-trade floor is for a five-year blind window; the grade is ONE year, so 50/5


def pass2(a, min_n=None):
    """gate 2's bars on one record (crosses_label): the trade floor and every ratio floor"""
    min_n = S.MIN_TRADES_BLIND if min_n is None else min_n
    return bool(a and a['n'] >= min_n and T.crosses_label(dict(a, n_w2=S.MIN_TRADES_BLIND, n_w3=S.MIN_TRADES_BLIND)))


def shard_of(sid, n, salt=''):
    return int(hashlib.md5((str(sid) + salt).encode()).hexdigest(), 16) % n


def bank_path(suffix, i, box=None):
    if box is not None:
        return os.path.join(ROOTOUT, 'refit_settings%s_b%02d_s%02d.csv' % (suffix, box, i))
    return os.path.join(ROOTOUT, 'refit_settings%s_s%02d.csv' % (suffix, i))


def _pick(a):
    return dict(n=a['n'], expectancy_R=a['expectancy_R'], profit_factor=a['profit_factor'], total_R=a['total_R']) if a else dict(n=0, expectancy_R=np.nan, profit_factor=np.nan, total_R=np.nan)


def combo_of(cfg):
    return (cfg['c1'], cfg['c2'], cfg['vol'], cfg['base'], cfg['exit_ind'] if isinstance(cfg.get('exit_ind'), str) else S.slot_options()['exit_ind'][0])


def slice_bits(cfg):
    sn = cfg['slice']
    return sn, dict((s_, c) for s_, _, c in S.SLICES)[sn], dict((s_, p_) for s_, p_, _ in S.SLICES)[sn]


def tune_worker(args):
    i, n, suffix, cand_path, wins, reuse_path, box, of = args
    S.WINDOWS = dict(S.WINDOWS); S.WINDOWS.update(windows_table(wins))
    S.load_costs(); T.ACCT_OBJECTIVE = True
    D = pd.read_csv(cand_path, low_memory=False)
    if of > 1:
        D = D[[shard_of(s, of) == box for s in D.sid]]            # this box's share, fixed for all time
    D = D[[shard_of(s, n, '|w') == i for s in D.sid]]             # this worker's share within the box
    bank = bank_path(suffix, i, box if of > 1 else None)
    done = set()
    if os.path.exists(bank):
        b = pd.read_csv(bank); done = set(zip(b.sid, b.window))
    reuse = {}
    if reuse_path and os.path.exists(reuse_path):
        P = pd.read_csv(reuse_path, low_memory=False)
        for r in P.itertuples():
            for pw, wname in (('P1', '2011-2015'), ('P2', '2012-2016')):
                if hasattr(r, 'tune_%s_ip' % pw):
                    reuse[(r.sid, wname)] = (getattr(r, 'tune_%s_ip' % pw), getattr(r, 'tune_%s_risk' % pw), getattr(r, 'tune_%s_evals' % pw), getattr(r, 'tune_%s_seconds' % pw))
    sc = T.Scorer()
    t0 = time.time(); k = 0
    todo = [(cfg, w) for cfg in D.to_dict('records') for w in wins if (cfg['sid'], w['name']) not in done]
    print('  shard %d: %d (strategy, window) jobs, %d banked' % (i, len(todo), len(done)), flush=True)
    for cfg, w in todo:
        combo = combo_of(cfg); sn, code, plan = slice_bits(cfg); mode = cfg['mode']
        bw, tw = 'B' + w['name'], 'T' + w['name']
        t1 = time.time(); n0 = sc.n_eval
        if (cfg['sid'], w['name']) in reuse:
            ipj, rkj, ev, secs = reuse[(cfg['sid'], w['name'])]
            ip, rk = json.loads(ipj), json.loads(rkj); stage = 'reused-pilot'
        else:
            try:
                ip, rk, info = T._stage(sc, combo, mode, sn, code, plan, (bw,), CAP, False)
            except Exception as e:
                print('  shard %d: %s %s FAILED %s' % (i, cfg['sid'][:50], w['name'], str(e)[:80]), flush=True)
                continue
            ev = sc.n_eval - n0; secs = round(time.time() - t1, 1); stage = info.get('stage')
        years = ['Y%d' % y for y in range(w['build'][1] + 1, 2021)]
        # FIXED COLUMN SET per row: the bank is appended row by row, so every row
        # must carry the same columns in the same order (a window-dependent year
        # list misaligned the CSV on the first smoke run, 16 Sep)
        all_years = ['Y%d' % y for y in range(2006, 2021)]
        gw = ('G' + w['name']) if w['grade'] else None
        row = dict(sid=cfg['sid'], slice=cfg.get('lab', sn), mode=mode, window=w['name'], build_end=w['build'][1],
                   grade_year=(w['grade'][0] if w['grade'] else -1), trade_start=w['trade'][0],
                   tune_evals=ev, tune_seconds=secs, tune_stage=stage, ip=json.dumps(ip, sort_keys=True), risk=json.dumps(rk, sort_keys=True))
        assert row['build_end'] < row['trade_start']                                  # audit 3, per strategy per window
        if gw:
            assert row['build_end'] < row['grade_year'] < row['trade_start']         # the grade year is blind to the tuner and before the trade block
        keys = [(bw, 'build')] + ([(gw, 'grade')] if gw else []) + [(tw, 'trade')]
        for routed in (True, False):
            r = sc.score(combo, ip, rk, mode, sn, code, plan, tuple(k for k, _ in keys) + tuple(years), routed=routed)
            tag = 'routed' if routed else 'allon'
            for wn, key in keys:
                a = r.get(wn)
                for kk in KEEP:
                    row['%s_%s_%s' % (tag, key, kk)] = (a[kk] if a else (0 if kk == 'n' else np.nan))
                row['%s_%s_g3' % (tag, key)] = g3_composite(a) if a else 0
                row['%s_%s_pass2' % (tag, key)] = pass2(a, GRADE_MIN_TRADES if key == 'grade' else None)
            if not gw:
                for kk in KEEP:
                    row['%s_grade_%s' % (tag, kk)] = np.nan
                row['%s_grade_g3' % tag] = np.nan; row['%s_grade_pass2' % tag] = False
            for yn in all_years:
                a = r.get(yn) if yn in years else None
                row['%s_%s_expectancy_R' % (tag, yn)] = a['expectancy_R'] if a else np.nan
                row['%s_%s_n' % (tag, yn)] = a['n'] if a else 0
        # THE BLIND LABEL, REPORTED NEVER USED: gate 2's bars on the GRADE year
        # (never seen by the tuner) under the window's own settings. The book
        # takes everyone regardless; the report asks whether this grade predicts
        # the trade year. label_basis names the year it was read on.
        row['label_basis'] = ('G%d_blind' % w['grade'][0]) if gw else ('B%s_own' % w['name'])
        row['graded_pass_routed'] = bool(row['routed_grade_pass2']) if gw else False
        row['graded_pass_allon'] = bool(row['allon_grade_pass2']) if gw else False
        row['passes_gate2_on_window'] = bool(row['routed_build_pass2'])
        row['regime_dependent_on_window'] = bool(np.nan_to_num(row['routed_build_expectancy_R'], nan=-9) > np.nan_to_num(row['allon_build_expectancy_R'], nan=-9))
        pd.DataFrame([row]).to_csv(bank, mode='a', index=False, header=not os.path.exists(bank))
        k += 1
        if k <= 10 or k % 25 == 0:
            print('  shard %d: %d/%d  %.0f s per job  window %s  tune %ss (%s)  grade %s routed %+.3f (pass %s)  trade %s routed %+.3f allon %+.3f'
                  % (i, k, len(todo), (time.time() - t0) / k, w['name'], secs, stage, w['grade'], row['routed_grade_expectancy_R'], row['graded_pass_routed'],
                     w['trade'], row['routed_trade_expectancy_R'], row['allon_trade_expectancy_R']), flush=True)
    return i


EXIT_OF_MODE = {'A': 'C1_FLIP', 'B': 'BASE_CROSS', 'C': 'EXIT_IND'}


def check_mode_exits(mode, reasons, what):
    """AUDIT 12 on the blind path (22 Sep): the exit rule that FIRED must be the
    mode's own. Mode C had never run through this pipeline and run_pair was once
    hardcoded to mode B, so this asserts per strategy rather than trusting the
    label: a forbidden rule anywhere in a strategy's trades halts the run."""
    import l2engine as E
    own = getattr(E, EXIT_OF_MODE[mode])
    forbidden = {m: getattr(E, EXIT_OF_MODE[m]) for m in ('A', 'B', 'C') if m != mode}
    rs = set(int(x) for x in reasons)
    bad = {m: c for m, c in forbidden.items() if c in rs}
    if bad:
        raise RuntimeError('MODE EXIT MISMATCH (%s, mode %s): fired %s -- the exit rules of mode(s) %s'
                           % (what, mode, sorted(E.REASON[c] for c in bad.values()), sorted(bad)))
    return own in rs


def marks_worker(args):
    """Per strategy: for each step, the ALWAYS-ON trade stream under that step's settings over
    [build start, trade end], marks truncated at the trade end, one tid per trade, `step` column."""
    import l2trades as TR
    i, n, suffix, cand_path, wins, settings_path = args
    S.load_costs()
    D = pd.read_csv(cand_path, low_memory=False)
    D = D[[shard_of(s, n) == i for s in D.sid]]
    SET = pd.read_csv(settings_path, low_memory=False).set_index(['sid', 'window'])
    Tr, Mr = [], []
    own_fired, seen = {}, {}
    for cfg in D.to_dict('records'):
        sn, code, plan = slice_bits(cfg)
        for si, w in enumerate(wins):
            if (cfg['sid'], w['name']) not in SET.index:
                continue
            st = SET.loc[(cfg['sid'], w['name'])]
            ip = json.loads(st['ip']); rk = json.loads(st['risk'])
            c = dict(cfg); c['ip2'] = json.dumps(ip)
            for kk, v in rk.items():
                c['risk_' + kk] = v
            am = float(rk['atr_mult'])
            a = pd.Timestamp('%d-01-01' % w['span'][0]); z = pd.Timestamp('%d-12-31' % w['span'][1])   # tune + grade + trade years under this step's settings
            for p in S.all_pairs():
                try:
                    r = TR.run_pair(c, p)
                except Exception as e:
                    print('  marks: %s %s on %s FAILED %s' % (cfg['sid'][:50], w['name'], p, str(e)[:60]), flush=True)
                    continue
                d, tr, cl = r['dates'], r['trades'], r['c']
                nt = len(tr['r'])
                if nt == 0:
                    continue
                fired = check_mode_exits(cfg['mode'], tr['reason'][:nt], '%s %s %s' % (cfg['sid'][:50], w['name'], p))
                own_fired[cfg['mode']] = own_fired.get(cfg['mode'], 0) + int(fired)
                seen[cfg['mode']] = seen.get(cfg['mode'], 0) + 1
                dv = d.values
                wi = np.flatnonzero((d >= a) & (d <= z))
                if not len(wi):
                    continue
                lo, hi = int(wi[0]), int(wi[-1]) + 1
                for j in range(nt):
                    eb, xb = int(tr['entry_bar'][j]), int(tr['exit_bar'][j])
                    if xb < 0 or not (lo <= eb < hi):
                        continue
                    ent = float(tr['entry_px'][j]); u = float(tr['units'][j]); sgn = float(tr['dir'][j]); tot = float(tr['r'][j]) * am
                    cst = float(S._cost_R(p, np.array([ent]), np.array([u]), np.array([dv[eb]]))[0]) * am   # fault #27: same unit as R
                    end = min(xb, hi - 1)
                    tid = (si + 1) * 10 ** 10 + i * 10 ** 8 + len(Tr) + 1     # unique across steps and shards
                    prev = 0.0
                    for b in range(eb, end + 1):
                        cum = tot if (b == xb and xb <= hi - 1) else sgn * (cl[b] - ent) * u / S.RISK * am
                        Mr.append((cfg['sid'], p, dv[b], int(sgn), np.float32(cum - prev - (cst if b == eb else 0.0)), tid, si + 1))
                        prev = cum
                    Tr.append((cfg['sid'], tid, p, dv[eb], dv[end], float(prev - cst), w['name'], si + 1))
    Tf = pd.DataFrame(Tr, columns=['sid', 'tid', 'pair', 'entry', 'exit', 'R', 'era', 'step'])
    Mf = pd.DataFrame(Mr, columns=['sid', 'pair', 'day', 'dir', 'mark', 'tid', 'step'])
    del Tr, Mr
    if len(Mf):
        Mf['dir'] = Mf['dir'].astype(np.int8); Mf['mark'] = Mf['mark'].astype(np.float32); Mf['day'] = pd.to_datetime(Mf.day)
        Mf['step'] = Mf['step'].astype(np.int8); Tf['step'] = Tf['step'].astype(np.int8)
    Tf.to_pickle(os.path.join(ROOTOUT, 'refit_marks%s_T_s%02d.pkl' % (suffix, i))); Mf.to_pickle(os.path.join(ROOTOUT, 'refit_marks%s_M_s%02d.pkl' % (suffix, i)))
    print('  marks shard %d: %d trades, %d marks; own-exit-rule fired on %s of %s (strategy, window, pair) runs per mode'
          % (i, len(Tf), len(Mf), own_fired, seen), flush=True)
    return i


def step_path(suffix, kind, si):
    return os.path.join(ROOTOUT, 'wf_%s%s_step%d.pkl' % ({'T': 'trades', 'M': 'marks'}[kind], suffix, si))


BOOKS = (('', 'always-on (no routing)', []),
         ('_routed', 'routed: chop RANGING + trend TRENDING', ['--trend-gate', 'trending']),
         ('_tgalways', 'chop RANGING + trend UNGATED', ['--trend-gate', 'always']),
         ('_tgnotrang', 'chop RANGING + trend NOT-RANGING', ['--trend-gate', 'not-ranging']))


def book_table(suffix, slices):
    """The four books of `suffix` as one per-slice table: median year, worst year,
    DIP95, PF, retention and the two null p-values (book-level; the always-on book
    has no regime-shuffle null by construction -- it reads no state)."""
    rows = []
    for sfx, lab, _ in BOOKS:
        b = suffix + sfx
        f = os.path.join(ROOTOUT, 'walkforward_structures_3slice%s.csv' % b)
        if not os.path.exists(f):
            print('  book_table: %s not built (%s)' % (lab, os.path.basename(f)), flush=True); continue
        N = {}
        for kind, nf in (('p_random_entry', 'walkforward_null_randomentry_nocut_summary_3slice%s_dirnull.csv' % b),
                         ('p_regime_shuffle', 'walkforward_null_regimeshuffle_summary_3slice%s.csv' % b)):
            pth = os.path.join(ROOTOUT, nf)
            N[kind] = ({r.budget: r.p_value for r in pd.read_csv(pth, comment='#').query("structure == 'NO_CUT'").itertuples()} if os.path.exists(pth) else {})
        for r in pd.read_csv(f, comment='#').itertuples():
            rows.append(dict(book=lab, suffix=b, slice='ALL (book)', budget=r.budget, median_year_pct=r.median_year_pct, worst_year_pct=r.worst_year_pct,
                             dip95_pct=r.dip95_pct, profit_factor=r.profit_factor, build_median_year_pct=getattr(r, 'build_median_year_pct', np.nan),
                             retention=getattr(r, 'retention', np.nan), retention_flag=getattr(r, 'retention_flag', ''),
                             p_random_entry=N['p_random_entry'].get(r.budget), p_regime_shuffle=N['p_regime_shuffle'].get(r.budget, 'n/a (no state read)' if sfx == '' else None)))
        ps = os.path.join(ROOTOUT, 'walkforward_perslice_3slice%s.csv' % b)
        if os.path.exists(ps):
            for r in pd.read_csv(ps, comment='#').itertuples():
                rows.append(dict(book=lab, suffix=b, slice=r.slice, budget=r.budget, median_year_pct=r.median_year_pct, worst_year_pct=r.worst_year_pct,
                                 dip95_pct=r.dip95_pct, profit_factor=r.profit_factor, build_median_year_pct=np.nan, retention=np.nan, retention_flag='',
                                 p_random_entry='book-level', p_regime_shuffle='book-level'))
    if not rows:
        print('  book_table: no books built yet', flush=True); return pd.DataFrame()
    Tb = pd.DataFrame(rows)
    out = os.path.join(ROOTOUT, 'refit_books%s.csv' % suffix); Tb.to_csv(out, index=False)
    print('\n=== FOUR BOOKS, PER SLICE (team1; team2 is the 5.4%% budget) -> %s ===' % os.path.basename(out), flush=True)
    print(Tb[Tb.budget == 'team1'][['book', 'slice', 'median_year_pct', 'worst_year_pct', 'dip95_pct', 'profit_factor', 'retention', 'p_random_entry', 'p_regime_shuffle']].to_string(index=False, float_format=lambda v: '%7.3f' % v), flush=True)
    return Tb


def run_books(suffix, cand, slices, jobs=3):
    """The four books end to end on an existing marks stream: route -> walk -> per-slice
    -> random-entry null -> regime-shuffle null. One command for the cloud merge."""
    import subprocess
    env = dict(os.environ)
    for sfx, lab, args in BOOKS:
        out = suffix + sfx
        print('\n--- book: %s (%s) ---' % (lab, out), flush=True)
        if sfx:
            subprocess.run([sys.executable, os.path.join(ROOTLIB, 'l2route.py'), '--states', os.path.join(ROOTOUT, 'layer1_states.csv'),
                            '--px', os.path.join(ROOTDATA, 'px28.csv'), '--suffix', suffix, '--out', out, '--tir', 'excl', '--activity', 'weak'] + args, check=True, env=env)
        e = dict(env); e['WF_TAG'] = out
        subprocess.run([sys.executable, os.path.join(ROOTLIB, 'l2walkfwd.py'), '--stage', 'walk', '--n-null', '0', '--structures', 'ALLPASS',
                        '--nocut', '--jobs', '1', '--slices', slices, '--suffix', out, '--field-file', cand], check=True, env=e)
        subprocess.run([sys.executable, os.path.join(ROOTLIB, 'l2cfperslice.py'), '--suffix', out, '--field-file', cand, '--slices', slices, '--nocut'], check=False, env=env)
        subprocess.run([sys.executable, os.path.join(ROOTLIB, 'l2returns.py'), '--stage', 'dirnull', '--suffix', out], check=True, env=env)
        for k in ('trades', 'marks'):
            src = os.path.join(ROOTOUT, 'wf_%s%s.pkl' % (k, out)); dst = os.path.join(ROOTOUT, 'wf_%s%s_dirnull.pkl' % (k, out))
            if os.path.exists(dst) or os.path.islink(dst):
                os.remove(dst)
            os.symlink(os.path.basename(src), dst)
        e2 = dict(env); e2['WF_ALLOWED'] = os.path.join(ROOTOUT, 'route_allowed_dirnull%s.pkl' % out); e2['WF_TAG'] = out + '_dirnull'
        subprocess.run([sys.executable, os.path.join(ROOTLIB, 'l2walkfwd.py'), '--stage', 'nullre', '--nocut', '--n-null', '25', '--jobs', str(jobs),
                        '--slices', slices, '--suffix', out + '_dirnull', '--field-file', cand], check=False, env=e2)
        if sfx:
            subprocess.run([sys.executable, os.path.join(ROOTLIB, 'l2route.py'), '--states', os.path.join(ROOTOUT, 'layer1_states.csv'),
                            '--px', os.path.join(ROOTDATA, 'px28.csv'), '--suffix', suffix, '--out', out, '--tir', 'excl', '--activity', 'weak'] + args +
                           ['--shuffle-null', '25', '--jobs', '1'], check=False, env=env)


def merge_settings(suffix):
    fs = sorted(glob.glob(os.path.join(ROOTOUT, 'refit_settings%s_s[0-9][0-9].csv' % suffix)) + glob.glob(os.path.join(ROOTOUT, 'refit_settings%s_b[0-9][0-9]_s[0-9][0-9].csv' % suffix)))
    if not fs:
        raise SystemExit('no settings shards for %s' % suffix)
    A = pd.concat([pd.read_csv(f, low_memory=False) for f in fs], ignore_index=True).drop_duplicates(['sid', 'window'])
    out = os.path.join(ROOTOUT, 'refit_settings%s.csv' % suffix); A.to_csv(out, index=False)
    return out, A


def candidates_full(out):
    """All 45,142: modes A (trend + chop banks), B (both slices), C (the 299 chunks tuned before the pause).
    Combos only -- every tune is fresh. sid = '<mode>|<slice>|c1|c2|vol|base' (+ '|exit' for C)."""
    parts = []
    for f, mode in (('gate2_tuned_modeA_trend.csv', 'A'), ('gate2_tuned_modeA_chop.csv', 'A'), ('gate2_tuned_modeB.csv', 'B')):
        d = pd.read_csv(os.path.join(ROOTOUT, f), low_memory=False)[['c1', 'c2', 'vol', 'base', 'exit_ind', 'slice']]; d['mode'] = mode; parts.append(d)
    cs = sorted(glob.glob(os.path.join(ROOTOUT, 'gate2', 'modeC_trend', 'chunk_*.csv')))
    if cs:
        d = pd.concat([pd.read_csv(f, low_memory=False)[['c1', 'c2', 'vol', 'base', 'exit_ind', 'slice']] for f in cs], ignore_index=True); d['mode'] = 'C'; parts.append(d)
    D = pd.concat(parts, ignore_index=True)
    D['lab'] = D['mode'] + '-' + D['slice']
    D['sid'] = D.apply(lambda r: '|'.join([r['mode'], r['slice'], r.c1, r.c2, r.vol, r.base] + ([r.exit_ind] if r['mode'] == 'C' else [])), axis=1)
    D = D.drop_duplicates('sid').reset_index(drop=True)
    D.to_csv(out, index=False)
    print('candidates: %d -> %s  %s' % (len(D), out, D.lab.value_counts().to_dict()), flush=True)
    return D


def blind_report(A, wins, suffix):
    """THE QUESTION (Jack, 21 Sep): does the grade on the unseen year 5 predict year 6 --
    reported, never used to select. Graded-pass vs graded-fail on the trade year; Spearman
    of the grade-year record vs the trade-year record on five yardsticks; per window, pooled,
    per slice; both streams."""
    from scipy.stats import spearmanr
    yards = ('sortino', 'expectancy_R', 'profit_factor', 'calmar', 'g3')
    rows, corr = [], []
    def pooled_pf(g, tag, key):
        gp = (g['%s_%s_avg_win_R' % (tag, key)].fillna(0) * g['%s_%s_win_rate' % (tag, key)].fillna(0) * g['%s_%s_n' % (tag, key)]).sum()
        gl = (-g['%s_%s_avg_loss_R' % (tag, key)].fillna(0) * (1 - g['%s_%s_win_rate' % (tag, key)].fillna(0)) * g['%s_%s_n' % (tag, key)]).sum()
        return gp / gl if gl > 0 else np.nan
    def groups(g, tag, wname, ty, sl):
        ok = g['%s_trade_n' % tag] > 0; p = g['graded_pass_%s' % tag].astype(bool)
        for lab, m in (('graded-pass', p & ok), ('graded-fail', ~p & ok), ('all', ok)):
            gg = g[m]; e = gg['%s_trade_expectancy_R' % tag]
            rows.append(dict(stream=tag, window=wname, trade_year=ty, slice=sl, group=lab, n=int(len(gg)),
                             grade_median_R=float(gg['%s_grade_expectancy_R' % tag].median()) if len(gg) else np.nan,
                             tune_median_R=float(gg['%s_build_expectancy_R' % tag].median()) if len(gg) else np.nan,
                             trade_median_R=float(e.median()) if len(gg) else np.nan, share_positive=float((e > 0).mean()) if len(gg) else np.nan,
                             pooled_PF=pooled_pf(gg, tag, 'trade') if len(gg) else np.nan))
    def rank(g, tag, wname, sl):
        ok = g['%s_trade_n' % tag] > 0
        for y in yards:
            a = g['%s_grade_%s' % (tag, y)].astype(float); b = g['%s_trade_%s' % (tag, y)].astype(float)
            m = ok & np.isfinite(a) & np.isfinite(b)
            rho, pv = spearmanr(a[m], b[m]) if m.sum() > 5 else (np.nan, np.nan)
            corr.append(dict(stream=tag, window=wname, slice=sl, yardstick=y, n=int(m.sum()), spearman=float(rho), p=float(pv)))
    for tag in ('routed', 'allon'):
        for w in wins:
            g = A[A.window == w['name']]
            groups(g, tag, w['name'], w['trade'][0], 'ALL'); rank(g, tag, w['name'], 'ALL')
        groups(A, tag, 'POOLED', 0, 'ALL'); rank(A, tag, 'POOLED', 'ALL')
        for sl, g in A.groupby('slice'):
            groups(g, tag, 'POOLED', 0, sl); rank(g, tag, 'POOLED', sl)
    R = pd.DataFrame(rows); C = pd.DataFrame(corr)
    R.to_csv(os.path.join(ROOTOUT, 'refit_blind_groups%s.csv' % suffix), index=False); C.to_csv(os.path.join(ROOTOUT, 'refit_blind_rankcorr%s.csv' % suffix), index=False)
    print('\n=== BLIND GRADE (year 5, unseen by the tuner) -> TRADE YEAR (year 6): graded-pass vs graded-fail ===', flush=True)
    print(R[R.slice == 'ALL'].to_string(index=False, float_format=lambda v: '%8.3f' % v), flush=True)
    print('\n=== RANK CORRELATION grade year vs trade year (Spearman), ALL slices ===', flush=True)
    print(C[C.slice == 'ALL'].pivot_table(index=['stream', 'window'], columns='yardstick', values='spearman').round(3).to_string(), flush=True)
    print('\n=== per slice, POOLED ===', flush=True)
    print(R[(R.window == 'POOLED') & (R.slice != 'ALL')].to_string(index=False, float_format=lambda v: '%8.3f' % v), flush=True)
    print(C[(C.window == 'POOLED') & (C.slice != 'ALL')].pivot_table(index=['stream', 'slice'], columns='yardstick', values='spearman').round(3).to_string(), flush=True)
    # graded-pass counts per window (power)
    P = A.groupby('window').agg(graded_pass_routed=('graded_pass_routed', 'sum'), graded_pass_allon=('graded_pass_allon', 'sum'), n=('sid', 'size'))
    print('\ngraded-pass counts per window:'); print(P.to_string(), flush=True)


def report(A, wins, suffix):
    print('\n=== REFIT %s: %d strategies x %d windows = %d settings ===' % (suffix, A.sid.nunique(), len(wins), len(A)), flush=True)
    rows = []
    for w in wins:
        g = A[A.window == w['name']]
        for tag in ('routed', 'allon'):
            e = g['%s_trade_expectancy_R' % tag]; ok = e.notna() & (g['%s_trade_n' % tag] > 0)
            eb = g['%s_build_expectancy_R' % tag]
            rows.append(dict(window=w['name'], trade=('%d' % w['trade'][0]) if w['trade'][0] == w['trade'][1] else '%d-%d' % w['trade'], stream=tag, n=int(ok.sum()),
                             build_median_R=float(eb[ok].median()), trade_median_R=float(e[ok].median()), share_positive=float((e[ok] > 0).mean()),
                             median_retention=float((e[ok] / eb[ok]).where(eb[ok] > 0).median()),
                             passers_on_window=int(g.passes_gate2_on_window.sum()), regime_dependent=int(g.regime_dependent_on_window.sum())))
    Rr = pd.DataFrame(rows); Rr.to_csv(os.path.join(ROOTOUT, 'refit_report%s.csv' % suffix), index=False)
    print(Rr.to_string(index=False, float_format=lambda v: '%8.3f' % v), flush=True)
    # decay: months after the window end, pooled -- year granularity here (the marks stage gives months)
    dec = []
    for w in wins:
        g = A[A.window == w['name']]
        for y in range(w['build'][1] + 1, 2021):
            col = 'routed_Y%d_expectancy_R' % y
            if col in g:
                dec.append(dict(window=w['name'], years_after=y - w['build'][1], median_R=float(g[col].median()), share_positive=float((g[col] > 0).mean()), n=int(g[col].notna().sum())))
    Dd = pd.DataFrame(dec); Dd.to_csv(os.path.join(ROOTOUT, 'refit_decay%s.csv' % suffix), index=False)
    print('\ndecay by years after the tuning window (routed, median R/trade):'); print(Dd.pivot_table(index='years_after', values='median_R', aggfunc='median').round(3).to_string(), flush=True)
    sec = A.tune_seconds[A.tune_stage != 'reused-pilot']
    if len(sec):
        print('\nseconds per tune (fresh): mean %.0f median %.0f p90 %.0f (n %d)' % (sec.mean(), sec.median(), sec.quantile(0.9), len(sec)), flush=True)
    for sl, g in A.groupby('slice'):
        e = g[g.window == wins[-1]['name']]['routed_trade_expectancy_R']
        print('  %-8s last window trade median %+.3f  share positive %.2f  (n %d)' % (sl, e.median(), (e > 0).mean(), len(e)), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', required=True, choices=['tune', 'marks', 'report', 'candidates', 'blind', 'books'])
    ap.add_argument('--slices', default='A-trend,A-chop,B-chop,B-trend')
    ap.add_argument('--box', type=int, default=0); ap.add_argument('--of', type=int, default=1)
    ap.add_argument('--candidates', default=os.path.join(ROOTOUT, 'refit_pilot_sample.csv'))
    ap.add_argument('--windows', default='2011-2014:2015:2016,2012-2015:2016:2017,2013-2016:2017:2018,2014-2017:2018:2019,2015-2018:2019:2020')
    ap.add_argument('--jobs', type=int, default=4)
    ap.add_argument('--suffix', default='_refit_smoke')
    ap.add_argument('--reuse', default='', help='pilot csv whose 2011-2015 / 2012-2016 tunes are reused')
    a = ap.parse_args()
    wins = parse_windows(a.windows)
    t0 = time.time()
    import multiprocessing as mp
    if a.stage == 'tune':
        D = pd.read_csv(a.candidates, low_memory=False)
        print('candidates: %s (%d); windows %s; jobs %d' % (os.path.basename(a.candidates), len(D), [w['name'] for w in wins], a.jobs), flush=True)
        args = [(i, a.jobs, a.suffix, a.candidates, wins, a.reuse, a.box, a.of) for i in range(a.jobs)]
        with mp.get_context('spawn').Pool(a.jobs) as pool:
            pool.map(tune_worker, args)
        if a.of > 1:
            print('box %d of %d: tunes banked in refit_settings%s_b%02d_s*.csv -- merge on the Mac with --stage report' % (a.box, a.of, a.suffix, a.box), flush=True)
        else:
            out, A = merge_settings(a.suffix)
            print('tune done in %.1f min -> %s (%d rows)' % ((time.time() - t0) / 60, out, len(A)), flush=True)
            report(A, wins, a.suffix)
            if wins[0]['grade']:
                blind_report(A, wins, a.suffix)
    elif a.stage == 'marks':
        out, A = merge_settings(a.suffix)
        args = [(i, a.jobs, a.suffix, a.candidates, wins, out) for i in range(a.jobs)]
        with mp.get_context('spawn').Pool(a.jobs) as pool:
            pool.map(marks_worker, args)
        # PER-STEP FILES (22 Sep). The always-on stream for the full library is ~33 GB;
        # one frame per step is ~1/5 of that and the walk only ever needs one step at
        # a time. Per-step pickles are ALWAYS written; the combined pair is written
        # too unless FX_NO_COMBINED=1 (set it for the full run).
        import l2walkfwd as W
        nT = nM = 0; sids = set(); steps = []
        for si in range(1, len(wins) + 1):
            Ts = pd.concat([pd.read_pickle(f).pipe(lambda d: d[d.step == si]) for f in sorted(glob.glob(os.path.join(ROOTOUT, 'refit_marks%s_T_s*.pkl' % a.suffix)))], ignore_index=True)
            Ms = pd.concat([pd.read_pickle(f).pipe(lambda d: d[d.step == si]) for f in sorted(glob.glob(os.path.join(ROOTOUT, 'refit_marks%s_M_s*.pkl' % a.suffix)))], ignore_index=True)
            if not len(Ts):
                continue
            for c in ('sid', 'pair'):
                Ts[c] = Ts[c].astype(str).astype('category'); Ms[c] = Ms[c].astype(str).astype('category')
            W.check_mark_convention(Ms, 'refit marks step %d' % si)
            Ts.to_pickle(step_path(a.suffix, 'T', si)); Ms.to_pickle(step_path(a.suffix, 'M', si))
            nT += len(Ts); nM += len(Ms); sids |= set(Ts.sid.astype(str).unique()); steps.append(si)
            print('  step %d: %d trades, %d marks -> %s' % (si, len(Ts), len(Ms), os.path.basename(step_path(a.suffix, 'M', si))), flush=True)
            del Ts, Ms
        if os.environ.get('FX_NO_COMBINED') != '1':
            Tf = pd.concat([pd.read_pickle(step_path(a.suffix, 'T', si)) for si in steps], ignore_index=True)
            Mf = pd.concat([pd.read_pickle(step_path(a.suffix, 'M', si)) for si in steps], ignore_index=True)
            for c in ('sid', 'pair'):
                Tf[c] = Tf[c].astype(str).astype('category'); Mf[c] = Mf[c].astype(str).astype('category')
            Tf.to_pickle(os.path.join(ROOTOUT, 'wf_trades%s.pkl' % a.suffix)); Mf.to_pickle(os.path.join(ROOTOUT, 'wf_marks%s.pkl' % a.suffix))
        print('marks done in %.1f min: %d trades, %d marks, %d strategies, steps %s; per-step files written%s'
              % ((time.time() - t0) / 60, nT, nM, len(sids), steps, '' if os.environ.get('FX_NO_COMBINED') == '1' else ' + the combined pair'), flush=True)
    elif a.stage == 'candidates':
        candidates_full(os.path.join(ROOTOUT, 'refit_candidates_full.csv'))
    elif a.stage == 'blind':
        out, A = merge_settings(a.suffix)
        blind_report(A, wins, a.suffix)
    elif a.stage == 'books':
        run_books(a.suffix, a.candidates, a.slices, jobs=min(a.jobs, 3))
        book_table(a.suffix, a.slices)
    else:
        out, A = merge_settings(a.suffix)
        report(A, wins, a.suffix)
        if wins[0]['grade']:
            blind_report(A, wins, a.suffix)
        book_table(a.suffix, a.slices)
    print('REFIT %s STAGE %s COMPLETE' % (a.suffix, a.stage.upper()), flush=True)


if __name__ == '__main__':
    main()
