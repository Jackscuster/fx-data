import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""GATE 3 ON MODE A, FROM THE GATE 2 BANK -- NO NEW TUNING (Jack, 18 Nov).

JACK'S BARS, unchanged from the gate4 design, and NOT negotiable here:
    expectancy  >= 0.15 R
    profit factor >= 1.5
    Sortino     >= 1.3
    Calmar      >= 1.0
    max DD      <= 10% of the strategy's OWN gross profit
    Sharpe      reported, binding nowhere
Costs charged throughout (cost_table_h22, restated per fault #27).

WHY THIS COSTS AN ENGINE PASS AND NOT A BANK READ. The gate 2 bank stores
n, sum_r, gain, loss and n_win per (strategy, stream, step, year), which gives
expectancy, PF, win rate and trade count -- but Sortino needs the downside
deviation of per-trade R and max DD and Calmar need the ORDERED equity curve,
and neither is in there. So each winning configuration is RE-SCORED: the
configuration is already chosen, nothing is searched, and no tuning happens.

HOW. The shipped l2tune.Scorer is given one window per CALENDAR YEAR, so a
single score call returns the full KPI block -- including chronological max DD,
Sortino and Calmar -- for every year at once. One call per (strategy, slice,
routing, step) winner, which is the same 20 passes per strategy the books stage
makes.

    python3 code/l2r2gate3.py --stage score --mode A --jobs 8
    python3 code/l2r2gate3.py --stage report --mode A
"""
import time, json, glob
import numpy as np, pandas as pd

import l2sweep as S
import l2tune as T
import l2r2gate1 as G
import l2r2gate2 as G2
import l2r2book as BK
import l2ckpt

BARS = dict(expectancy_R=0.15, profit_factor=1.5, sortino=1.3, calmar=1.0,
            max_dd_frac_of_gross=0.10)
KPIS = ('n', 'expectancy_R', 'total_R', 'profit_factor', 'win_rate', 'sharpe',
        'sortino', 'max_dd_R', 'calmar')
YEARS = list(range(2011, 2021))


def year_windows():
    """One window per calendar year, injected into the Scorer's table."""
    return {'Y%d' % y: ('%d-01-01' % y, '%d-12-31' % y) for y in YEARS}


def clears(k, gross=None):
    """Jack's bars on one KPI block. Sharpe is read and ignored, as declared."""
    if k is None or not k.get('n'):
        return False
    g = gross if gross is not None else _gross(k)
    if not np.isfinite(k['expectancy_R']) or k['expectancy_R'] < BARS['expectancy_R']:
        return False
    if not np.isfinite(k['profit_factor']) or k['profit_factor'] < BARS['profit_factor']:
        return False
    if not np.isfinite(k['sortino']) or k['sortino'] < BARS['sortino']:
        return False
    if not np.isfinite(k['calmar']) or k['calmar'] < BARS['calmar']:
        return False
    # max DD as a share of the strategy's OWN gross profit
    if g <= 0:
        return False
    if k['max_dd_R'] > BARS['max_dd_frac_of_gross'] * g:
        return False
    return True


def _gross(k):
    """Gross profit in R from the KPI block: PF = gross / loss and
    total = gross - loss, so gross = total x PF / (PF - 1) when PF > 1."""
    pf = k.get('profit_factor', np.nan)
    tot = k.get('total_R', np.nan)
    if not np.isfinite(pf) or pf <= 1 or not np.isfinite(tot):
        return np.nan if not np.isfinite(tot) else max(tot, 0.0)
    return float(tot * pf / (pf - 1.0))


def _worker(args):
    """Per-year KPI blocks for one block of strategies, every (stream, step)."""
    shard, nshard, mode, tag, outdir, cap, nmax = args
    S.load_costs()
    T.ACCT_OBJECTIVE = True
    S.WINDOWS = dict(S.WINDOWS); S.WINDOWS.update(year_windows())
    z = np.load(BK._bank_slice_file(mode, tag), allow_pickle=True)
    TG = z['tag']; CB = z['combo']
    n = int(z['n']) if nmax is None else min(int(z['n']), nmax)
    lo, hi = shard * n // nshard, (shard + 1) * n // nshard
    f = os.path.join(outdir, 'g3_%04d_of%d.npz' % (shard, nshard))
    done = set()
    acc = {}
    if os.path.exists(f):
        try:
            zz = np.load(f, allow_pickle=True)
            done = set(int(x) for x in zz['idx'])
            acc = {'K': zz['K'], 'idx': zz['idx']}
            print('    g3 shard %02d: resuming, %d of %d already scored'
                  % (shard, len(done), hi - lo), flush=True)
        except Exception as e:
            print('    g3 shard %02d: part unreadable (%s), restarting' % (shard, type(e).__name__), flush=True)
    sc = T.Scorer(cache=T.SeriesCache(cap=cap, disk=True))
    ST = G2.steps()
    wk = ['Y%d' % y for y in YEARS]
    reg = T.registry()
    todo = [k for k in range(lo, hi) if k not in done]
    K = list(acc.get('K', np.zeros((0, 4, 5, len(YEARS), len(KPIS)), np.float32)))
    ids = list(acc.get('idx', np.zeros(0, np.int64)))
    t0 = time.time(); last = time.time()

    def flush():
        tmp = f + '.tmp.npz'
        np.savez(tmp, K=np.stack(K) if K else np.zeros((0, 4, 5, len(YEARS), len(KPIS)), np.float32),
                 idx=np.array(ids, np.int64), kpis=np.array(KPIS, dtype=object),
                 years=np.array(YEARS, np.int64))
        os.replace(tmp, f)

    for j, k in enumerate(todo, 1):
        combo = tuple(CB[k])
        out = np.full((4, 5, len(YEARS), len(KPIS)), np.nan, np.float32)
        for sl, (sname, plan, code) in enumerate(S.SLICES):
            dipbase = {kk: dict(reg[nm]) for kk, nm in
                       zip(('c1', 'c2', 'vol', 'base', 'exit_ind'), combo)}
            for rt in (0, 1):
                stream = 2 * sl + rt
                for si in range(5):
                    ci = int(TG[k, stream, si])
                    if ci < 0:
                        continue
                    ip, risk = BK.winner_config(mode, combo, sname, ci)
                    r = sc.score(combo, ip, risk, mode, sname, code, plan, wk,
                                 routed=(rt == 0))
                    for yi, y in enumerate(YEARS):
                        b = r.get('Y%d' % y)
                        if b is None:
                            continue
                        for ki, kn in enumerate(KPIS):
                            v = b.get(kn, np.nan)
                            out[stream, si, yi, ki] = (v if np.isfinite(v) else np.nan) \
                                if isinstance(v, (int, float, np.floating, np.integer)) else np.nan
        K.append(out); ids.append(k)
        if time.time() - last >= l2ckpt.CKPT_SECONDS:
            flush(); last = time.time()
            print('    ckpt g3 shard %02d: %d scored' % (shard, len(ids)), flush=True)
        if j % 25 == 0:
            el = time.time() - t0
            print('    g3 shard %02d: %d/%d  %.2f s/strategy  %.0f min left'
                  % (shard, j, len(todo), el / j, (el / j) * (len(todo) - j) / 60), flush=True)
    flush()
    return (f, len(todo))


def stage_score(mode='A', tag='full', jobs=8, cap=30000, n=None):
    import multiprocessing as mp
    G.manifest_check()
    S.load_costs()
    BK._bank_slice_file(mode, tag)
    outdir = os.path.join(ROOTOUT, 'r2gate2', 'mode%s_gate3parts' % mode)
    os.makedirs(outdir, exist_ok=True)
    args = [(k, jobs, mode, tag, outdir, cap, n) for k in range(jobs)]
    t0 = time.time()
    if jobs == 1:
        res = [_worker(a) for a in args]
    else:
        with mp.Pool(jobs) as pool:
            res = pool.map(_worker, args)
    print('  gate 3 scoring: %s strategies newly scored in %.1f min'
          % (f"{sum(r[1] for r in res):,}", (time.time() - t0) / 60), flush=True)
    return outdir


def load_kpis(mode='A'):
    """(idx, K) with K = (n, 4 streams, 5 steps, 10 years, len(KPIS))."""
    outdir = os.path.join(ROOTOUT, 'r2gate2', 'mode%s_gate3parts' % mode)
    fs = sorted(glob.glob(os.path.join(outdir, 'g3_*.npz')))
    assert fs, 'no gate 3 KPI bank at %s' % outdir
    Ks, ids = [], []
    for f in fs:
        z = np.load(f, allow_pickle=True)
        if len(z['idx']):
            Ks.append(z['K']); ids.append(z['idx'])
    ix = np.concatenate(ids); o = np.argsort(ix, kind='stable')
    uq = np.concatenate(([True], ix[o][1:] != ix[o][:-1])); o = o[uq]
    return ix[o], np.concatenate(Ks)[o]


def _blk(K, i, stream, step, year_i):
    d = {kn: float(K[i, stream, step, year_i, ki]) for ki, kn in enumerate(KPIS)}
    return None if not np.isfinite(d['n']) or d['n'] <= 0 else d


def stage_report(mode='A', tag='full', nullseed=20261118, ndraw=200):
    """Parts 1, 2 and 3. Part 4 (the passers' book) is a chain stage."""
    G.manifest_check()
    ix, K = load_kpis(mode)
    z = np.load(BK._bank_slice_file(mode, tag), allow_pickle=True)
    CB = z['combo']
    sid = np.array(['|'.join(r) for r in CB])[ix]
    ST = G2.steps()
    yi = {y: i for i, y in enumerate(YEARS)}
    RD = os.path.join(ROOTOUT, 'r2gate2')
    rng = np.random.default_rng(nullseed)

    # ---- 1. the bars on the GRADE year, with the trade year beside it
    rows, counts = [], []
    for si, stp in enumerate(ST):
        gy = yi[stp['grade'][0]]; ty = yi[stp['trade'][0]]
        for st in range(4):
            npass = ntrade = 0
            for i in range(len(ix)):
                gk = _blk(K, i, st, si, gy)
                if gk is None or not clears(gk):
                    continue
                npass += 1
                tk = _blk(K, i, st, si, ty)
                ok_t = bool(tk is not None and clears(tk))
                ntrade += int(ok_t)
                r = dict(mode=mode, step=stp['name'], stream=G2.STREAMS[st], sid=sid[i],
                         grade_year=stp['grade'][0], trade_year=stp['trade'][0],
                         clears_trade_year=int(ok_t))
                for pfx, blk in (('grade', gk), ('trade', tk)):
                    for kn in KPIS:
                        r['%s_%s' % (pfx, kn)] = (blk.get(kn) if blk else np.nan)
                r['grade_gross_R'] = _gross(gk)
                r['trade_gross_R'] = _gross(tk) if tk else np.nan
                rows.append(r)
            counts.append(dict(mode=mode, step=stp['name'], stream=G2.STREAMS[st],
                               n_field=len(ix), n_clears_grade=npass,
                               n_also_clears_trade=ntrade,
                               pct_of_field=100.0 * npass / max(len(ix), 1)))
    P = pd.DataFrame(rows); C = pd.DataFrame(counts)

    # ---- 2. chance level: the identity null on the YEAR ROLES
    nl = []
    for si, stp in enumerate(ST):
        yrs = [yi[y] for y in range(stp['tune'][0], stp['trade'][1] + 1)]
        for st in range(4):
            obs = int(C[(C.step == stp['name']) & (C.stream == G2.STREAMS[st])]
                      .n_clears_grade.iloc[0])
            obs_t = int(C[(C.step == stp['name']) & (C.stream == G2.STREAMS[st])]
                        .n_also_clears_trade.iloc[0])
            dg, dt = [], []
            for _ in range(ndraw):
                a, b = rng.choice(yrs, size=2, replace=False)
                ng = nt = 0
                for i in range(len(ix)):
                    gk = _blk(K, i, st, si, a)
                    if gk is None or not clears(gk):
                        continue
                    ng += 1
                    tk = _blk(K, i, st, si, b)
                    nt += int(tk is not None and clears(tk))
                dg.append(ng); dt.append(nt)
            dg = np.array(dg, float); dt = np.array(dt, float)
            nl.append(dict(mode=mode, step=stp['name'], stream=G2.STREAMS[st],
                           real_clears_grade=obs, real_also_clears_trade=obs_t,
                           n_draws=ndraw, null_mean_clears=float(dg.mean()),
                           null_p95_clears=float(np.percentile(dg, 95)),
                           null_mean_also_trade=float(dt.mean()),
                           null_p95_also_trade=float(np.percentile(dt, 95)),
                           p_grade=float((dg >= obs).mean()),
                           p_also_trade=float((dt >= obs_t).mean())))
    N = pd.DataFrame(nl)

    # ---- 3. the stitched trade years 2016-2020, all unseen
    st_rows, st_counts = [], []
    for stream in range(4):
        npass = 0
        for i in range(len(ix)):
            tot = gross = loss = nn = 0.0
            dds, sor, cal = [], [], []
            per = {}
            ok_all = True
            for si, stp in enumerate(ST):
                b = _blk(K, i, stream, si, yi[stp['trade'][0]])
                per['R_%d' % stp['trade'][0]] = (b['expectancy_R'] if b else np.nan)
                if b is None:
                    ok_all = False
                    continue
                nn += b['n']; tot += b['total_R']
                g = _gross(b)
                if np.isfinite(g):
                    gross += g; loss += g - b['total_R']
                dds.append(b['max_dd_R']); sor.append(b['sortino']); cal.append(b['calmar'])
            if not ok_all or nn <= 0:
                continue
            # the stitched block, assembled from the five disjoint trade years
            k = dict(n=nn, expectancy_R=tot / nn, total_R=tot,
                     profit_factor=(gross / loss if loss > 0 else np.inf),
                     win_rate=np.nan, sharpe=np.nan,
                     sortino=float(np.nanmean(sor)), max_dd_R=float(np.nansum(dds)),
                     calmar=(tot / float(np.nansum(dds)) if np.nansum(dds) > 0 else np.nan))
            if clears(k, gross=gross):
                npass += 1
                r = dict(mode=mode, stream=G2.STREAMS[stream], sid=sid[i], stitched_gross_R=gross)
                r.update({'stitched_%s' % a: k[a] for a in k})
                r.update(per)
                st_rows.append(r)
        st_counts.append(dict(mode=mode, stream=G2.STREAMS[stream], n_field=len(ix),
                              n_clears_stitched=npass,
                              pct_of_field=100.0 * npass / max(len(ix), 1)))
    Sx = pd.DataFrame(st_rows); SC = pd.DataFrame(st_counts)

    outs = {}
    for nm, D in (('passers', P), ('counts', C), ('null', N),
                  ('stitched', Sx), ('stitched_counts', SC)):
        p = os.path.join(RD, 'mode%s_gate3_%s.csv' % (mode, nm))
        D.to_csv(p, index=False)
        outs[nm] = p
        print('  %-16s %7d rows -> %s' % (nm, len(D), os.path.relpath(p, _R)), flush=True)
    return outs


def opt(f, c=str, d=None):
    return G.opt(f, c, d)




def write_md(mode='A', out=None):
    """results/r2gate2/MODEA_GATE3.md -- every number read back out of a CSV."""
    import hashlib
    RD = os.path.join(ROOTOUT, 'r2gate2')
    F = {k: os.path.join(RD, 'mode%s_gate3_%s.csv' % (mode, k))
         for k in ('counts', 'passers', 'null', 'stitched', 'stitched_counts')}
    F['book'] = os.path.join(RD, 'mode%s_gate3_passersbook.csv' % mode)
    F['booknull'] = os.path.join(RD, 'mode%s_gate3_passersbook_nulls.csv' % mode)
    L = []; A = L.append
    A('# MODE %s — GATE 3\n' % mode)
    A('Generated %s by `code/l2r2gate3.py`. **No new tuning**: every configuration '
      'here was already chosen by gate 2 and is re-scored, nothing is searched. '
      'Every number below is read back out of the CSV named beside it.\n'
      % time.strftime('%F %H:%M'))
    A('\n## The bars, unchanged\n')
    A('| bar | value | binds |\n|---|---|---|\n'
      '| expectancy | >= %.2f R | yes |\n| profit factor | >= %.1f | yes |\n'
      '| Sortino | >= %.1f | yes |\n| Calmar | >= %.1f | yes |\n'
      '| max DD | <= %.0f%% of the strategy\'s OWN gross profit | yes |\n'
      '| Sharpe | reported | **no — binds nowhere** |\n'
      % (BARS['expectancy_R'], BARS['profit_factor'], BARS['sortino'],
         BARS['calmar'], 100 * BARS['max_dd_frac_of_gross']))
    A('\nCosts are charged throughout (`cost_table_h22`, restated per fault #27).\n')
    A('\n**Why this cost an engine pass.** The gate 2 bank stores `n, sum_r, gain, '
      'loss, n_win` per (strategy, stream, step, year), which gives expectancy, PF, '
      'win rate and trade count — but Sortino needs the downside deviation of '
      'per-trade R, and max DD and Calmar need the ordered equity curve. Neither is '
      'banked, so each winner was re-scored through the shipped `l2tune.Scorer` with '
      'one window per calendar year; the KPIs come from `_agg`, the same aggregator '
      'every other result in this project used.\n')
    A('\n## Sources\n')
    rows = []
    for k, p in F.items():
        if os.path.exists(p):
            try:
                nr = len(pd.read_csv(p))
            except Exception:
                nr = 0          # an empty file IS the result when nobody passes
            rows.append(dict(section=k, file=os.path.relpath(p, _R), rows=nr,
                             md5=hashlib.md5(open(p, 'rb').read()).hexdigest()[:12]))
    A(BK_tbl(pd.DataFrame(rows), ['section', 'file', 'rows', 'md5']))
    miss = [k for k, p in F.items() if not os.path.exists(p)]
    if miss:
        A('\n**Missing sources, left empty rather than filled in:** %s\n' % ', '.join(miss))

    A('\n## 1. The bars on the GRADE year (year 5, unseen by the tuner)\n')
    if os.path.exists(F['counts']):
        C = pd.read_csv(F['counts'])
        A(BK_tbl(C.sort_values(['stream', 'step']),
                 ['stream', 'step', 'n_field', 'n_clears_grade',
                  'n_also_clears_trade', 'pct_of_field']))
        A('\nTotals by stream:\n')
        A(BK_tbl(C.groupby('stream', as_index=False)[
            ['n_clears_grade', 'n_also_clears_trade']].sum(),
            ['stream', 'n_clears_grade', 'n_also_clears_trade']))
        if os.path.exists(F['passers']):
            P = pd.read_csv(F['passers'])
            A('\nEvery passer is listed in `%s` with its settings, its grade-year KPIs '
              'and its trade-year KPIs. The first 20:\n' % os.path.relpath(F['passers'], _R))
            A(BK_tbl(P.head(20), ['step', 'stream', 'sid', 'grade_expectancy_R',
                                  'grade_profit_factor', 'grade_sortino', 'grade_calmar',
                                  'grade_max_dd_R', 'grade_n', 'grade_sharpe',
                                  'trade_expectancy_R', 'trade_profit_factor',
                                  'trade_sortino', 'trade_calmar', 'trade_max_dd_R',
                                  'trade_win_rate', 'trade_n', 'trade_sharpe',
                                  'clears_trade_year']))
    else:
        A('_counts CSV absent; this section is empty._\n')

    A('\n## 2. Chance level — the identity null on the year roles\n')
    if os.path.exists(F['null']):
        N = pd.read_csv(F['null'])
        A('Each draw calls a randomly chosen year of the step the "grade" year and '
          'another the "trade" year, and applies the identical bars. **A caveat that '
          'belongs in the reading**: those draws can land on TUNE years, on which the '
          'settings were fitted, so the null is not a neutral yardstick — it is '
          'biased toward clearing. A real count BELOW the null mean is therefore the '
          'striking direction, not the reassuring one.\n')
        A(BK_tbl(N.sort_values(['stream', 'step']),
                 ['stream', 'step', 'real_clears_grade', 'null_mean_clears',
                  'null_p95_clears', 'p_grade', 'real_also_clears_trade',
                  'null_mean_also_trade', 'p_also_trade']))
    else:
        A('_null CSV absent; this section is empty._\n')

    A('\n## 3. The stitched trade years 2016-2020, all unseen\n')
    if os.path.exists(F['stitched_counts']):
        SC = pd.read_csv(F['stitched_counts'])
        A(BK_tbl(SC, ['stream', 'n_field', 'n_clears_stitched', 'pct_of_field']))
        try:
            Sx = pd.read_csv(F['stitched'])
        except Exception:
            Sx = pd.DataFrame()
        if len(Sx):
            A('\nEveryone who passes on the stitched record, with per-year R:\n')
            cols = ['stream', 'sid', 'stitched_expectancy_R', 'stitched_profit_factor',
                    'stitched_sortino', 'stitched_calmar', 'stitched_max_dd_R',
                    'stitched_n'] + [c for c in Sx.columns if c.startswith('R_')]
            A(BK_tbl(Sx, cols))
        else:
            A('\n**Nobody passes on the stitched record.**\n')
    else:
        A('_stitched CSVs absent; this section is empty._\n')

    A('\n## 4. The passers\' book\n')
    def _safe(p):
        try:
            return pd.read_csv(p)
        except Exception:
            return pd.DataFrame()
    if os.path.exists(F['book']):
        A(BK_tbl(_safe(F['book']), None))
        if os.path.exists(F['booknull']):
            A('\nIts three nulls:\n')
            A(BK_tbl(_safe(F['booknull']), None))
    else:
        A('_The passers\' book has not been built; this section is empty rather than '
          'filled in from anywhere else._\n')

    txt = '\n'.join(L)
    out = out or os.path.join(RD, 'MODE%s_GATE3.md' % mode)
    open(out, 'w').write(txt)
    print('  MODE%s_GATE3.md: %d lines -> %s'
          % (mode, len(txt.splitlines()), os.path.relpath(out, _R)), flush=True)
    return out


def BK_tbl(d, cols):
    if d is None or not len(d):
        return '_no rows_\n'
    cols = [c for c in (cols or list(d.columns)) if c in d.columns]
    o = ['| ' + ' | '.join(cols) + ' |', '|' + '---|' * len(cols)]
    for _, r in d[cols].iterrows():
        cs = []
        for c in cols:
            v = r[c]
            if isinstance(v, (int, np.integer)):
                cs.append(f'{v:,}')
            elif isinstance(v, (float, np.floating)):
                cs.append('' if not np.isfinite(v) else ('%.4g' % v))
            else:
                cs.append(str(v))
        o.append('| ' + ' | '.join(cs) + ' |')
    return '\n'.join(o) + '\n'


if __name__ == '__main__':
    st = G.opt('--stage', str, 'score')
    md = G.opt('--mode', str, 'A')
    if st == 'score':
        stage_score(md, G.opt('--tag', str, 'full'), jobs=G.opt('--jobs', int, 8),
                    cap=G.opt('--cap', int, 30000), n=G.opt('--n', int, None))
    elif st == 'report':
        stage_report(md, G.opt('--tag', str, 'full'), ndraw=G.opt('--draws', int, 200))
        write_md(md)
    elif st == 'md':
        write_md(md)
    else:
        raise SystemExit('unknown stage %s' % st)
