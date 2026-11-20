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

    python3 code/l2r2gate3.py --stage score  --mode A --jobs 8
    python3 code/l2r2gate3.py --stage report --mode A
    python3 code/l2r2gate3.py --stage book   --mode A --jobs 8   # part 4
    python3 code/l2r2gate3.py --stage booknulls --mode A --jobs 8
    python3 code/l2r2gate3.py --stage md     --mode A

EVERY STAGE TAKES --mode B unchanged. The bank, the bars, the streams and the
steps are the same objects for both modes; only the gate 2 winners differ.
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


def stage_score(mode='A', tag='full', jobs=8, cap=30000, n=None, nshard=None):
    import multiprocessing as mp
    G.manifest_check()
    S.load_costs()
    BK._bank_slice_file(mode, tag)
    outdir = os.path.join(ROOTOUT, 'r2gate2', 'mode%s_gate3parts' % mode)
    os.makedirs(outdir, exist_ok=True)
    # MORE SHARDS THAN WORKERS, for the reason gate 2 already learned: with
    # nshard == jobs one slow shard holds the stage. Measured on the first 125
    # strategies of each shard the rates spread 1.00-1.89 s/strategy, and the
    # slowest shard projected 1,385 min against the fastest's 568 -- so the
    # stage would have run 23 h for 8 h of work.
    nshard = int(nshard or max(jobs * 4, jobs))
    args = [(k, nshard, mode, tag, outdir, cap, n) for k in range(nshard)]
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


# ---------------------------------------------------------------------------
# PART 4 -- THE PASSERS' BOOK (Jack, 19 Nov)
#
# WHO IS IN IT. Everyone who cleared the bars on the step's GRADE year, equal
# weight, no picking. Membership is per (step, stream): a strategy that cleared
# on trend-routed is a member of that step's ROUTED book through its trend
# routed settings, and nothing else. "Each book runs on settings tuned on its
# own stream" (HANDOFF 0l) is why the mask is per stream and not per strategy.
#
# TWO BOOKS, as asked: ROUTED and ALWAYS-ON. The allon book takes the members
# that cleared on the *-allon streams through split_keeptabs' always-on table;
# the routed book takes those that cleared on the *-routed streams through the
# gated table. The two remaining gated variants of the full-field books
# (chop_ungated, chop_notrange) are NOT part of this request and are not built.
#
# WHY THIS NEEDS AN ENGINE PASS AND CANNOT SUBSET THE FULL-FIELD BOOK.
# NetAccumulator folds each member in with `np.add.at(self.nl, rows, 1.0)` --
# no per-member identity survives, and _Vec.__matmul__ ignores its weight
# vector and returns the accumulated column sum. So "equal weight over a
# subset" is not a weight vector over the full-field sums; the subset has to be
# accumulated on its own. That is cheap here: 59,268 member-slots against the
# field's 1,368,900, ~2 min of engine work against 30.
# ---------------------------------------------------------------------------
def passmask_file(mode='A'):
    return os.path.join(ROOTOUT, 'r2gate2', 'mode%s_gate3_passmask.npz' % mode)


def stage_passmask(mode='A'):
    """(n_bank, 4 streams, 5 steps) bool: did this strategy clear the bars on
    this step's GRADE year on this stream. Read straight off the KPI bank, so
    it is the same arithmetic part 1 of the report prints and cannot drift."""
    G.manifest_check()
    ix, K = load_kpis(mode)
    z = np.load(BK._bank_slice_file(mode, tag_of(mode)), allow_pickle=True)
    nbank = int(z['n']); del z
    ST = G2.steps()
    yi = {y: i for i, y in enumerate(YEARS)}
    PM = np.zeros((nbank, 4, len(ST)), bool)
    for si, stp in enumerate(ST):
        gy = yi[stp['grade'][0]]
        for st in range(4):
            for i in range(len(ix)):
                gk = _blk(K, i, st, si, gy)
                if gk is not None and clears(gk):
                    PM[int(ix[i]), st, si] = True
    f = passmask_file(mode)
    np.savez(f, pm=PM, n=np.int64(nbank),
             streams=np.array(G2.STREAMS, dtype=object),
             steps=np.array([s['name'] for s in ST], dtype=object))
    print('  pass mask: %s of %s (strategy, stream, step) cells clear the grade year -> %s'
          % (f'{int(PM.sum()):,}', f'{PM.size:,}', os.path.relpath(f, _R)), flush=True)
    for si, stp in enumerate(ST):
        print('    %s: routed %s members, always-on %s members'
              % (stp['name'],
                 f'{int((PM[:, 0, si] | PM[:, 2, si]).sum()):,}',
                 f'{int((PM[:, 1, si] | PM[:, 3, si]).sum()):,}'), flush=True)
    return f


def tag_of(mode):
    return 'full'


# the two books this stage builds, as (BOOKS index, name, which routing's mask)
PASSBOOKS = ((0, 'allon', 1), (1, 'chop_trend', 0))


def _passbook_worker(args):
    """One shard of the passers' book for one step. Same shape as
    l2r2book._books_worker, with two differences: a (strategy, stream, step)
    pass mask gates every accumulate, and n_members is counted PER BOOK because
    the routed and always-on books have different membership."""
    shard, nshard, mode, tag, si, outdir, cap = args
    S.load_costs()
    z = np.load(BK._bank_slice_file(mode, tag), allow_pickle=True)
    TG = z['tag']; CB = z['combo']; nstrat = int(z['n'])
    PM = np.load(passmask_file(mode), allow_pickle=True)['pm']
    assert PM.shape[0] == nstrat, ('pass mask covers %d strategies, the bank has %d'
                                   % (PM.shape[0], nstrat))
    lo = shard * nstrat // nshard
    hi = (shard + 1) * nstrat // nshard
    stp = G2.steps()[si]
    build_years = set(range(stp['tune'][0], stp['grade'][1] + 1))
    trade_years = set(range(stp['trade'][0], stp['trade'][1] + 1))
    Y = G2.Years(cap=cap)
    aidx, adays = BK.year_dayidx(Y, build_years | trade_years)
    BA = BK.BookArrays(Y.sc.pairs, adays)
    pf = os.path.join(outdir, 'pbook_s%d_of%d_%04d.npz' % (si, nshard, shard))
    done = set()
    if os.path.exists(pf):
        try:
            zz = np.load(pf, allow_pickle=True)
            BA.NL, BA.NS, BA.SL, BA.SS = zz['NL'], zz['NS'], zz['SL'], zz['SS']
            BA.n_members = zz['nm']
            done = set(int(x) for x in zz['idx'])
            print('    pbook s%d shard %02d: resuming, %d of %d already folded in'
                  % (si, shard, len(done), hi - lo), flush=True)
        except Exception as e:
            print('    pbook s%d shard %02d: part unreadable (%s), restarting it'
                  % (si, shard, type(e).__name__), flush=True)
            done = set()

    def _flush(ids):
        tmp = pf + '.tmp.npz'
        np.savez(tmp, NL=BA.NL, NS=BA.NS, SL=BA.SL, SS=BA.SS,
                 nm=BA.n_members, idx=np.array(sorted(ids), np.int64),
                 si=np.int64(si), shard=np.int64(shard))
        os.replace(tmp, pf)

    # ONLY THE STRATEGIES THIS STEP ACTUALLY NEEDS. A strategy that cleared on
    # no stream in this step contributes nothing, so it is never walked -- that
    # is what makes the stage minutes instead of half an hour.
    todo = [k for k in range(lo, hi) if PM[k, :, si].any() and k not in done]
    if not todo:
        print('    pbook s%d shard %02d: nothing to fold in (%d already done)'
              % (si, shard, len(done)), flush=True)
        if not os.path.exists(pf):
            _flush(done)
        return (pf, 0)
    t0 = time.time(); last = time.time()
    for j, k in enumerate(todo, 1):
        combo = tuple(CB[k])
        added = np.zeros(len(BK.BOOKS), np.int64)
        for sl, (sname, plan, _code) in enumerate(S.SLICES):
            allon_tab, gated_tab = BK.split_keeptabs(sname)
            for rt, tabv in ((1, allon_tab), (0, gated_tab)):
                stream = 2 * sl + rt
                if not PM[k, stream, si]:
                    continue                      # did not clear the grade year here
                ci = int(TG[k, stream, si])
                if ci < 0:
                    continue
                ip, risk = BK.winner_config(mode, combo, sname, ci)
                BK.accumulate_strategy(Y, mode, combo, ip, risk, sname, plan,
                                       aidx, BA, tabv)
                # the always-on table only opens book 0, the gated table books 1-3
                added[0 if rt == 1 else 1] = 1
        # A MEMBER IS COUNTED ONCE PER BOOK, not once per slice: a strategy that
        # cleared on both trend-routed and chop-routed is ONE member of the
        # routed book holding two sleeves, which is how the full-field book
        # counts it too.
        if added[0]:
            BA.n_members[0] += 1
        if added[1]:
            for bi in range(1, len(BK.BOOKS)):
                BA.n_members[bi] += 1
        done.add(k)
        if time.time() - last >= l2ckpt.CKPT_SECONDS:
            _flush(done); last = time.time()
            print('    ckpt pbook s%d shard %02d: %d folded in' % (si, shard, len(done)), flush=True)
        if j % 50 == 0:
            el = time.time() - t0
            print('    pbook s%d shard %02d: %d/%d  %.2f s/strategy  %.0f min left'
                  % (si, shard, j, len(todo), el / j, (el / j) * (len(todo) - j) / 60), flush=True)
    _flush(done)
    return (pf, len(todo))


def _sum_pbook_parts(outdir, si, nshard, pairs, days):
    BA = BK.BookArrays(pairs, days)
    seen = set()
    for shard in range(nshard):
        f = os.path.join(outdir, 'pbook_s%d_of%d_%04d.npz' % (si, nshard, shard))
        if not os.path.exists(f):
            continue
        z = np.load(f, allow_pickle=True)
        BA.NL += z['NL']; BA.NS += z['NS']; BA.SL += z['SL']; BA.SS += z['SS']
        BA.n_members += z['nm']
        ids = set(int(x) for x in z['idx'])
        assert not (ids & seen), ('shard %d overlaps an earlier shard -- a member '
                                 'would be double-counted' % shard)
        seen |= ids
    return BA, seen


def stage_book(mode='A', tag='full', jobs=8, nshard=None, out_tag=None):
    """Part 4: the passers' book, routed and always-on, on the trade year.

    Scored by the SHIPPED path -- l2walkfwd.fit_curve, scale_of, Book.series and
    kpis through l2r2book.StreamedBook -- so this book is scored by the same
    code as every other book in the project. The curve and the size are fitted
    on the BUILD years and not touched again; the trade year is what is
    reported.
    """
    import multiprocessing as mp
    import l2walkfwd as W
    G.manifest_check()
    S.load_costs()
    if not os.path.exists(passmask_file(mode)):
        stage_passmask(mode)
    PM = np.load(passmask_file(mode), allow_pickle=True)['pm']
    out_tag = out_tag or 'g3pass'
    nshard = int(nshard or max(jobs * 4, jobs))
    partdir = os.path.join(ROOTOUT, 'r2gate2', 'mode%s_gate3bookparts' % mode)
    os.makedirs(partdir, exist_ok=True)
    BK._bank_slice_file(mode, tag)
    ST = G2.steps()
    rows = []
    for si, stp in enumerate(ST):
        build_years = set(range(stp['tune'][0], stp['grade'][1] + 1))
        trade_years = set(range(stp['trade'][0], stp['trade'][1] + 1))
        Y = G2.Years(cap=2000)
        _ai, adays = BK.year_dayidx(Y, build_years | trade_years)
        pairs = Y.sc.pairs
        del Y
        nmem_expect = int((PM[:, :, si].any(axis=1)).sum())
        t0 = time.time()
        args = [(k, nshard, mode, tag, si, partdir, 30000) for k in range(nshard)]
        if jobs == 1:
            res = [_passbook_worker(a) for a in args]
        else:
            with mp.Pool(jobs) as pool:
                res = pool.map(_passbook_worker, args)
        BA, folded = _sum_pbook_parts(partdir, si, nshard, pairs, adays)
        print('    pbook step %s: %s members folded in by %d workers in %.1f min '
              '(%s newly computed)'
              % (stp['name'], f'{len(folded):,}', jobs, (time.time() - t0) / 60,
                 f'{sum(r[1] for r in res):,}'), flush=True)
        assert len(folded) == nmem_expect, (
            'step %s folded %d members, the pass mask says %d'
            % (stp['name'], len(folded), nmem_expect))
        for bi, bk, _rt in PASSBOOKS:
            desc = dict(BK.BOOKS)[bk]
            acc = BA.as_accumulator(bi)
            nm = int(BA.n_members[bi])
            if nm == 0 or acc.nl.sum() + acc.ns.sum() == 0:
                rows.append(dict(mode=mode, step=stp['name'], book=bk, description=desc,
                                 members=nm, book_empty=1))
                print('      %s / %-11s: EMPTY (%d members)' % (stp['name'], bk, nm), flush=True)
                continue
            SB = BK.StreamedBook(acc, nm)
            wb = np.ones(nm, np.float32)
            yrs = pd.DatetimeIndex(SB.udays).year.values
            ybuild = np.isin(yrs, sorted(build_years))
            ytrade = np.isin(yrs, sorted(trade_years))
            curve, _C = W.fit_curve(SB, wb, build_years)
            d0, den, _b0, _w0, _s0, _f0 = SB.series(wb, curve)
            for (bname, dipb, dayb) in BK.BUDGETS:
                sc_, bD, badj, bwd, binds = W.scale_of(d0[ybuild], dipb, dayb)
                d1, _dn, capbinds, worst, _sz, _f = SB.series(
                    wb, curve, cap_pct=W.CAP_PCT, per_unit=sc_ / den, den=den)
                kb = W.kpis(d1[ybuild] * sc_, yrs[ybuild])
                kt = W.kpis(d1[ytrade] * sc_, yrs[ytrade])
                ret = (kt['median_year_pct'] / kb['median_year_pct']
                       if kb['median_year_pct'] else np.nan)
                # the daily series, so identity_null never rebuilds a book
                np.savez(os.path.join(ROOTOUT, 'r2gate2',
                                      'mode%s_daily_%s_%s_%s_%s.npz'
                                      % (mode, out_tag, stp['name'], bk, bname)),
                         daily=d1 * sc_, years=yrs, build=ybuild, trade=ytrade)
                rows.append(dict(
                    mode=mode, step=stp['name'], book=bk, description=desc,
                    budget=bname, dip_budget=dipb, day_budget=dayb, members=nm,
                    size_scale=sc_, scale_binds=binds, cap_pct=W.CAP_PCT,
                    build_dip95_pct=bD * sc_, build_max_dd_pct=badj * sc_,
                    build_worst_day_pct=bwd * sc_,
                    build_median_year_pct=kb['median_year_pct'],
                    trade_median_year_pct=kt['median_year_pct'],
                    trade_worst_year_pct=kt['worst_year_pct'],
                    trade_best_year_pct=kt['best_year_pct'],
                    trade_total_pct=kt['total_return_pct'],
                    trade_max_dd_pct=kt['max_dd_pct'], trade_dip95_pct=kt['dip95_pct'],
                    trade_profit_factor=kt['profit_factor'], trade_sortino=kt['sortino'],
                    trade_sharpe=kt['sharpe'], trade_calmar=kt['calmar'],
                    trade_win_rate_pct=kt['win_rate_pct'],
                    trade_worst_day_pct=kt['worst_day_pct'],
                    trading_days=kt['trading_days'], den=den,
                    cap_bound_days=capbinds, worst_ccy_exposure=worst,
                    retention=ret, FIT=int(np.isfinite(ret) and ret < 0.20),
                    book_empty=0))
        del BA
    D = pd.DataFrame(rows)
    outp = os.path.join(ROOTOUT, 'r2gate2', 'mode%s_gate3_passersbook.csv' % mode)
    D.to_csv(outp, index=False)
    print('  passers book: %d rows -> %s' % (len(D), os.path.relpath(outp, _R)), flush=True)
    return D, outp


def stage_booknulls(mode='A', tag='full', jobs=8, ndraw=20, nid=200):
    """The three nulls on the passers' book.

    IDENTITY runs unchanged off the daily series this stage saved -- it
    reassigns which calendar year plays the trade year and never rebuilds a
    book. SHUFFLE and RANDOM-ENTRY need an engine pass, and they run on the
    WHOLE passer field rather than a stratified sample: the passers number a
    few thousand per step against the field's 273,780, so the sample sizes the
    full-field nulls were written for are larger than the population here.
    """
    import l2r2null2 as N2
    # COSTS IN THE PARENT TOO. sampled_null builds a Scorer in the parent to
    # resolve the step's trading days before it forks, and l2tune refuses to
    # build one without the cost table -- "a gross score is not a score". The
    # workers load it themselves; the parent has to as well.
    G.manifest_check()
    S.load_costs()
    RD = os.path.join(ROOTOUT, 'r2gate2')
    books_csv = os.path.join(RD, 'mode%s_gate3_passersbook.csv' % mode)
    assert os.path.exists(books_csv), books_csv + ' is missing -- run --stage book first'
    PM = np.load(passmask_file(mode), allow_pickle=True)['pm']
    members = sorted(np.flatnonzero(PM.any(axis=(1, 2))).tolist())
    print('  passers book nulls: %s distinct members across all steps' % f'{len(members):,}',
          flush=True)
    parts = []
    I = N2.identity_null(books_csv, ndraw=nid, out_tag='g3pass', mode=mode)
    if len(I):
        parts.append(I)
        print('  identity null on the passers book: %d cells, %d draws each' % (len(I), nid),
              flush=True)
    for kind in ('shuffle', 'random-entry'):
        D = N2.sampled_null(mode, tag, kind, len(members), ndraw=ndraw, jobs=jobs,
                            idxs=members, pmfile=passmask_file(mode),
                            scope='passers, full', partsuffix='_g3pass')
        if len(D):
            # the passers' book builds only these two; the other gated variants
            # are not part of this request and are dropped rather than reported
            D = D[D.book.isin([bk for _bi, bk, _rt in PASSBOOKS])]
            parts.append(D)
    A = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
    outp = os.path.join(RD, 'mode%s_gate3_passersbook_nulls.csv' % mode)
    A.to_csv(outp, index=False)
    print('  passers book nulls: %d rows -> %s' % (len(A), os.path.relpath(outp, _R)),
          flush=True)
    return A, outp


def opt(f, c=str, d=None):
    return G.opt(f, c, d)




def _safe_csv(path):
    """A result file can legitimately be EMPTY -- 'nobody passes' writes no
    header at all and pandas raises EmptyDataError. Every read in the report
    generator goes through here so an empty result renders as an empty table
    instead of killing the stage."""
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


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
            nr = len(_safe_csv(p))
            rows.append(dict(section=k, file=os.path.relpath(p, _R), rows=nr,
                             md5=hashlib.md5(open(p, 'rb').read()).hexdigest()[:12]))
    A(BK_tbl(pd.DataFrame(rows), ['section', 'file', 'rows', 'md5']))
    miss = [k for k, p in F.items() if not os.path.exists(p)]
    if miss:
        A('\n**Missing sources, left empty rather than filled in:** %s\n' % ', '.join(miss))

    A('\n## 1. The bars on the GRADE year (year 5, unseen by the tuner)\n')
    if os.path.exists(F['counts']):
        C = _safe_csv(F['counts'])
        A(BK_tbl(C.sort_values(['stream', 'step']),
                 ['stream', 'step', 'n_field', 'n_clears_grade',
                  'n_also_clears_trade', 'pct_of_field']))
        A('\nTotals by stream:\n')
        A(BK_tbl(C.groupby('stream', as_index=False)[
            ['n_clears_grade', 'n_also_clears_trade']].sum(),
            ['stream', 'n_clears_grade', 'n_also_clears_trade']))
        if os.path.exists(F['passers']):
            P = _safe_csv(F['passers'])
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
        N = _safe_csv(F['null'])
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
        SC = _safe_csv(F['stitched_counts'])
        A(BK_tbl(SC, ['stream', 'n_field', 'n_clears_stitched', 'pct_of_field']))
        Sx = _safe_csv(F['stitched'])
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
    if os.path.exists(F['book']):
        import l2r2kpis as KP
        B4 = _safe_csv(F['book'])
        nmem = (B4[B4.book_empty == 0].groupby('book').members.max().to_dict()
                if len(B4) and 'book_empty' in B4.columns else {})
        A('Everyone who cleared the bars on the step\'s GRADE year, equal weight, no '
          'picking -- membership is per (step, stream), so a strategy that cleared on '
          '`trend-routed` is in that step\'s ROUTED book through its trend routed '
          'settings and nothing else. Two books, as asked: ROUTED and ALWAYS-ON. '
          'Sized on the BUILD years, reported on the TRADE year. Members at the widest '
          'step: %s.\n'
          % (', '.join('%s %s' % (k, f'{int(v):,}') for k, v in sorted(nmem.items()))
             or 'none'))
        A('Per-step rows with every field are in `%s`.\n' % os.path.relpath(F['book'], _R))
        # THE SAME TABLE BUILDER AS MODEA_KPIS.md, on this book's own daily series,
        # so part 4 and the KPI document cannot disagree about what a row means.
        tl, _recs = KP.kpi_tables(mode, tag='g3pass', books_csv=F['book'], Bk=B4)
        if tl:
            for ln in tl:
                A(ln)
        else:
            A('_No daily series for the passers\' book; its KPI table is empty._\n')
        A('\n### Per step, as traded\n')
        A(BK_tbl(B4, ['step', 'book', 'budget', 'members', 'size_scale', 'scale_binds',
                      'trade_total_pct', 'trade_max_dd_pct', 'trade_dip95_pct',
                      'trade_profit_factor', 'trade_sortino', 'trade_calmar',
                      'trade_win_rate_pct', 'retention', 'FIT']))
        if os.path.exists(F['booknull']):
            A('\n### Its three nulls\n')
            NB = _safe_csv(F['booknull'])
            A(BK_tbl(NB, ['null', 'scope', 'step', 'book', 'budget', 'members',
                          'real', 'n_draws', 'null_mean', 'null_p5', 'null_p95',
                          'p_one_sided']))
            if len(NB) and 'null_p95' in NB.columns:
                beat = int((pd.to_numeric(NB.real, errors='coerce')
                            > pd.to_numeric(NB.null_p95, errors='coerce')).sum())
                A('\nThe real book clears its null\'s 95th percentile in **%d of %d** '
                  'cells.\n' % (beat, len(NB)))
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
                    cap=G.opt('--cap', int, 30000), n=G.opt('--n', int, None),
                    nshard=G.opt('--nshard', int, None))
    elif st == 'report':
        stage_report(md, G.opt('--tag', str, 'full'), ndraw=G.opt('--draws', int, 200))
        write_md(md)
    elif st == 'passmask':
        stage_passmask(md)
    elif st == 'book':
        stage_book(md, G.opt('--tag', str, 'full'), jobs=G.opt('--jobs', int, 8),
                   nshard=G.opt('--nshard', int, None))
    elif st == 'booknulls':
        stage_booknulls(md, G.opt('--tag', str, 'full'), jobs=G.opt('--jobs', int, 8),
                        ndraw=G.opt('--draws', int, 20),
                        nid=G.opt('--id-draws', int, 200))
    elif st == 'md':
        write_md(md)
    else:
        raise SystemExit('unknown stage %s' % st)
