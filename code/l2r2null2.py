import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""THE THREE NULLS ON THE MODE A BOOKS (HANDOFF 0l, Jack 18 Nov).

WHAT EACH ONE PERTURBS, declared before it runs:

  IDENTITY        the year -> role assignment. The books are built once; each
                  draw reassigns which calendar year plays "trade year" and
                  which play "build years", keeping the daily series untouched.
                  It asks whether the build -> trade ORDERING carries anything,
                  and it is the only one cheap enough for the FULL FIELD.
                  Full field, 200 draws.

  REGIME-SHUFFLE  each pair's shape2 label series, rotated circularly. Episode
                  lengths and the regime mix are preserved exactly; only the
                  alignment with price is destroyed. It asks whether the three
                  GATED books owe anything to the real labels. Stratified
                  sample, two sizes.

  RANDOM-ENTRY    each trade's entry bar, moved to a uniformly random permitted
                  bar in the same pair, holding period kept. It asks whether
                  the book owes anything to WHEN the strategies entered.
                  Stratified sample, two sizes.

TWO SAMPLE SIZES, 5,000 and 20,000, so the report can show whether the
p-values are stable in the sample size rather than asserting that they are.
The full-field versions of regime-shuffle and random-entry are registered in
HANDOFF 0l as the clean run to do later: at 0.48 s per strategy per draw they
are a multi-day job, which is a scheduling fact and not a reason to skip them
tonight at a declared size.
"""
import time, json, glob
import numpy as np, pandas as pd
from numba import njit

import l2sweep as S
import l2walkfwd as W
import l2r2gate1 as G
import l2r2gate2 as G2
import l2r2book as BK
import l2ckpt

NDRAW_IDENTITY = 200
NDRAW_SAMPLED = 20
SAMPLE_SIZES = (5000, 20000)


# ==========================================================================
# S3 -- THE IDENTITY NULL, FULL FIELD
# ==========================================================================
def identity_null(books_csv, ndraw=NDRAW_IDENTITY, seed=20261118, out_tag='full', mode='A'):
    """Reassign which year is the trade year, keeping the daily series as is.

    The real reading is the book's own trade year. Each draw picks a different
    year of the step's six to call the trade year and sizes on the other five,
    so the statistic is the same arithmetic on a different ordering. If the
    real trade year sits inside this spread, the build -> trade ordering is not
    doing anything the calendar would not have done by itself.
    """
    rows = []
    D = pd.read_csv(books_csv)
    for (step, book, budget), g in D[D.book_empty == 0].groupby(['step', 'book', 'budget']):
        r = g.iloc[0]
        real = float(r.trade_median_year_pct)
        f = os.path.join(ROOTOUT, 'r2gate2', 'mode%s_daily_%s_%s_%s_%s.npz'
                         % (mode, out_tag, step, book, budget))
        if not os.path.exists(f):
            continue
        z = np.load(f)
        x = z['daily']; yr = z['years']
        uy = sorted(set(yr.tolist()))
        rng = np.random.default_rng(seed + abs(hash((step, book, budget))) % 10000)
        draws = []
        for _ in range(ndraw):
            ty = int(rng.choice(uy))
            m = yr == ty
            if m.sum() < 50:
                continue
            draws.append(float(pd.Series(x[m]).sum()))
        draws = np.array(draws)
        if not len(draws):
            continue
        rows.append(dict(null='identity', scope='full field', step=step, book=book,
                         budget=budget, real=real, n_draws=len(draws),
                         null_mean=float(draws.mean()),
                         null_p5=float(np.percentile(draws, 5)),
                         null_p95=float(np.percentile(draws, 95)),
                         p_one_sided=float((draws >= real).mean())))
    return pd.DataFrame(rows)


# ==========================================================================
# S4/S5 -- THE SAMPLED NULLS, DRAWS INSIDE ONE PASS
# ==========================================================================
@njit(cache=False)
def _acc_draws_book(nt, eb, xb, dirv, epx, units, rtot, cst, am, risk,
                    cl, dayidx, lab_arr, pair_off, keeptab,
                    roff, eshift, NL, NS, SL, SS):
    """One (pair, configuration) into EVERY draw's books in one bar walk.

    `roff[d]` rotates the label series for draw d (the regime-shuffle null);
    `eshift[d]` moves the entry bar for draw d (the random-entry null). Draw 0
    is always the REAL reading -- offset 0 and shift 0 -- so the real number and
    its null come out of the same pass and cannot drift apart.

    Running the draws inside the pass is not an optimisation: at 0.48 s per
    strategy per draw, 20 draws over 20,000 strategies is 53 core-hours as
    separate passes and under 3 as one.
    """
    nd = roff.shape[0]
    nbook = keeptab.shape[0]
    nbar = cl.shape[0]
    for j in range(nt):
        e0 = eb[j]
        x0 = xb[j]
        if x0 < 0 or x0 <= e0:
            continue
        hold = x0 - e0
        d = dirv[j]
        u = units[j]
        for dd in range(nd):
            e = e0 + eshift[dd]
            if e < 0 or e + hold >= nbar:
                continue
            x = e + hold
            lb = e + roff[dd]
            if lb >= nbar:
                lb -= nbar
            lab = lab_arr[lb] + 1
            any_book = False
            for b in range(nbook):
                if keeptab[b, lab] != 0:
                    any_book = True
                    break
            if not any_book:
                continue
            px = cl[e] if eshift[dd] != 0 else epx[j]
            tot = rtot[j] * am if eshift[dd] == 0 else d * (cl[x] - px) * u / risk * am
            prev = 0.0
            carry = 0.0
            for bar in range(e, x + 1):
                if bar == x:
                    cum = tot
                else:
                    cum = d * (cl[bar] - px) * u / risk * am
                inc = cum - prev
                if bar == e:
                    inc -= cst[j]
                prev = cum
                if bar == e:
                    carry = inc
                    continue
                v = inc + carry
                carry = 0.0
                di = dayidx[bar]
                if di < 0:
                    continue
                row = pair_off + di
                for b in range(nbook):
                    if keeptab[b, lab] == 0:
                        continue
                    if d > 0.0:
                        NL[dd, b, row] += 1.0
                        SL[dd, b, row] += v
                    else:
                        NS[dd, b, row] += 1.0
                        SS[dd, b, row] += v


def _null_worker(args):
    """One shard of the sampled null: every draw, in one bar walk per config."""
    (shard, nshard, mode, tag, si, idxs, kind, ndraw, outdir, cap, seed,
     pmfile) = args
    S.load_costs()
    z = np.load(BK._bank_slice_file(mode, tag), allow_pickle=True)
    TG = z['tag']; CB = z['combo']
    # A PASS MASK NARROWS MEMBERSHIP PER (STRATEGY, STREAM, STEP). Passed only
    # by the passers'-book nulls; None here is the full-field behaviour this
    # function has always had, unchanged.
    PM = np.load(pmfile, allow_pickle=True)['pm'] if pmfile else None
    mine = [i for n, i in enumerate(idxs) if n % nshard == shard]
    stp = G2.steps()[si]
    build_years = set(range(stp['tune'][0], stp['grade'][1] + 1))
    trade_years = set(range(stp['trade'][0], stp['trade'][1] + 1))
    Y = G2.Years(cap=cap)
    aidx, adays = BK.year_dayidx(Y, build_years | trade_years)
    nrow = len(Y.sc.pairs) * len(adays)
    nb = len(BK.BOOKS)
    # float64 for the accumulation, float32 ON DISK. The first version wrote
    # four float64 arrays of (20 draws x 4 books x 54,180 rows) per shard = 106 MB,
    # and 8 shards x 5 steps x 4 (null kind, sample size) directories filled the
    # volume to 362 MB free and took the stage down with OSError 28.
    NL = np.zeros((ndraw, nb, nrow)); NS = np.zeros((ndraw, nb, nrow))
    SL = np.zeros((ndraw, nb, nrow)); SS = np.zeros((ndraw, nb, nrow))
    rng = np.random.default_rng(seed + shard)
    # DRAW 0 IS THE REAL READING in both nulls: offset 0, shift 0.
    if kind == 'shuffle':
        roff = np.concatenate(([0], rng.integers(200, 4000, ndraw - 1))).astype(np.int64)
        eshift = np.zeros(ndraw, np.int64)
    else:
        roff = np.zeros(ndraw, np.int64)
        eshift = np.concatenate(([0], rng.integers(-1200, 1200, ndraw - 1))).astype(np.int64)
    nmem = np.zeros(nb, np.int64)
    import l2lib as L, l2engine as E
    kwm = S.mode_kw(mode)
    t0 = time.time()
    for q, k in enumerate(mine, 1):
        combo = tuple(CB[k])
        added = np.zeros(nb, np.int64)
        for sl, (sname, plan, _code) in enumerate(S.SLICES):
            allon_tab, gated_tab = BK.split_keeptabs(sname)
            for rt, tabv in ((1, allon_tab), (0, gated_tab)):
                if PM is not None and not PM[k, 2 * sl + rt, si]:
                    continue
                ci = int(TG[k, 2 * sl + rt, si])
                if ci < 0:
                    continue
                added[0 if rt == 1 else 1] = 1
                ip, risk = BK.winner_config(mode, combo, sname, ci)
                am = float(risk['atr_mult']); alen = int(risk['atr_len'])
                t1 = L.KIND[combo[0]] == 'TERNARY'; t2 = L.KIND[combo[1]] == 'TERNARY'
                for p in Y.sc.pairs:
                    o, h, l, c = Y.sc.arr[p]
                    atr = Y.sc._atr.get((alen, p))
                    if atr is None:
                        atr = L.P.atr(h, l, c, alen); Y.sc._atr[(alen, p)] = atr
                    gg = Y.sc.cache.get
                    lt, st, lc, scr = gg(combo[0], ip['c1'], p, Y.sc.arr[p])[:4]
                    _, _, c2lc, c2sc = gg(combo[1], ip['c2'], p, Y.sc.arr[p])[:4]
                    vl, vs = gg(combo[2], ip['vol'], p, Y.sc.arr[p])[:2]
                    bl = gg(combo[3], ip['base'], p, Y.sc.arr[p])
                    bl = bl[0] if isinstance(bl, tuple) else bl
                    el, es = gg(combo[4], ip['exit_ind'], p, Y.sc.arr[p])[:2]
                    b = Y.sc.buf[p]
                    nt, _, _, _ = E.run_bars(
                        o, h, l, c, atr, bl, lt, st, lc, scr, c2lc, c2sc, vl, vs,
                        el, es, Y.sc._nosus[p], t1, t2, True, True, True,
                        kwm['exit_on_c1_flip'], kwm['exit_on_base_cross'],
                        kwm['exit_on_exit_ind'], False, int(plan), S.RISK, am,
                        float(risk['tp_mult']), float(risk['trail_mult']),
                        float(risk['trail_arm']), float(risk['be_pct']), 1.5, 7, True, True,
                        b['entry_bar'], b['exit_bar'], b['dir'], b['leg'], b['entry_px'],
                        b['exit_px'], b['units'], b['r'], b['reason'], b['route'])
                    if nt == 0:
                        continue
                    ebv = b['entry_bar'][:nt]
                    cst = (Y.cfrac[p] * Y.cmult[p][ebv] * np.abs(b['entry_px'][:nt])
                           * np.abs(b['units'][:nt]) / S.RISK) * am
                    _acc_draws_book(nt, ebv, b['exit_bar'][:nt],
                                    b['dir'][:nt].astype(np.float64), b['entry_px'][:nt],
                                    b['units'][:nt], b['r'][:nt], cst, am, S.RISK,
                                    Y.cl[p], aidx[p], Y.sc.reg[p].astype(np.int64),
                                    len(adays) * Y.sc.pairs.index(p), tabv,
                                    roff, eshift, NL, NS, SL, SS)
        if PM is None:
            nmem += 1
        else:
            # the routed and always-on books have DIFFERENT membership here, so
            # each book counts only its own members -- the vote fraction is
            # |net| / members and a wrong denominator moves every book day
            if added[0]:
                nmem[0] += 1
            if added[1]:
                nmem[1:] += 1
        if q % 25 == 0:
            el = time.time() - t0
            print('    null %s s%d shard %02d: %d/%d  %.2f s/strategy  %.0f min left'
                  % (kind, si, shard, q, len(mine), el / q,
                     (el / q) * (len(mine) - q) / 60), flush=True)
    f = os.path.join(outdir, 'null_%s_s%d_of%d_%04d.npz' % (kind, si, nshard, shard))
    np.savez(f, NL=NL.astype(np.float32), NS=NS.astype(np.float32),
             SL=SL.astype(np.float32), SS=SS.astype(np.float32), nmem=nmem,
             idx=np.array(mine, np.int64), ndraw=np.int64(ndraw))
    return f


def sampled_null(mode, tag, kind, nsample, ndraw=NDRAW_SAMPLED, jobs=8, cap=30000,
                 seed=20261118, idxs=None, pmfile=None, scope=None, partsuffix=''):
    """One sampled null at one sample size. Draw 0 is the real reading.

    `idxs` names the members explicitly instead of drawing a stratified sample
    -- the passers' book passes its own membership, which is smaller than the
    sample sizes this function was written for, so it runs on ALL of it. With
    `idxs` None the behaviour is the stratified sample it has always been.
    """
    import multiprocessing as mp
    if idxs is None:
        opts = S.mode_opts(S.slot_options(), mode)
        ntot = S.n_combos(opts)
        rng = np.random.default_rng(seed)
        idxs = sorted(rng.choice(ntot, size=min(nsample, ntot), replace=False).tolist())
    else:
        idxs = sorted(int(x) for x in idxs)
    scope = scope or 'sample %d' % nsample
    outdir = os.path.join(ROOTOUT, 'r2gate2',
                          'mode%s_nullparts_%s_%d%s' % (mode, kind, nsample, partsuffix))
    os.makedirs(outdir, exist_ok=True)
    print('  null %s, sample %s, %d draws (draw 0 = real), %d workers'
          % (kind, f'{len(idxs):,}', ndraw, jobs), flush=True)
    rows = []
    for si, stp in enumerate(G2.steps()):
        build_years = set(range(stp['tune'][0], stp['grade'][1] + 1))
        trade_years = set(range(stp['trade'][0], stp['trade'][1] + 1))
        Y = G2.Years(cap=2000)
        _ai, adays = BK.year_dayidx(Y, build_years | trade_years)
        pairs = Y.sc.pairs
        del Y
        args = [(k, jobs, mode, tag, si, idxs, kind, ndraw, outdir, cap, seed, pmfile)
                for k in range(jobs)]
        t0 = time.time()
        if jobs == 1:
            fs = [_null_worker(a) for a in args]
        else:
            with mp.Pool(jobs) as pool:
                fs = pool.map(_null_worker, args)
        nb = len(BK.BOOKS)
        nrow = len(pairs) * len(adays)
        NL = np.zeros((ndraw, nb, nrow)); NS = np.zeros((ndraw, nb, nrow))
        SL = np.zeros((ndraw, nb, nrow)); SS = np.zeros((ndraw, nb, nrow))
        nmem = np.zeros(nb, np.int64)
        for f in fs:
            z = np.load(f)
            NL += z['NL']; NS += z['NS']; SL += z['SL']; SS += z['SS']; nmem += z['nmem']
            del z
        # A STEP'S SCRATCH IS DEAD ONCE IT IS SUMMED. Keeping every step's parts
        # is what filled the volume; the bound is now one step's worth, ~400 MB.
        for f in fs:
            os.remove(f)
        print('    null %s step %s: %d workers in %.1f min'
              % (kind, stp['name'], jobs, (time.time() - t0) / 60), flush=True)
        for bi, (bk, _desc) in enumerate(BK.BOOKS):
            vals = {}
            for dd in range(ndraw):
                acc = BK.NetAccumulator(pairs, adays)
                acc.nl = NL[dd, bi]; acc.ns = NS[dd, bi]
                acc.sl = SL[dd, bi]; acc.ss = SS[dd, bi]
                acc.n_members = int(nmem[bi])
                if acc.nl.sum() + acc.ns.sum() == 0:
                    continue
                SB = BK.StreamedBook(acc, int(nmem[bi]))
                w = np.ones(int(nmem[bi]), np.float32)
                yrs = pd.DatetimeIndex(SB.udays).year.values
                ybuild = np.isin(yrs, sorted(build_years))
                ytrade = np.isin(yrs, sorted(trade_years))
                if not ybuild.any() or not ytrade.any():
                    continue
                curve, _c = W.fit_curve(SB, w, build_years)
                d0, den, _a, _b2, _c2, _d2 = SB.series(w, curve)
                for (bname, dipb, dayb) in BK.BUDGETS:
                    sc_, _bD, _badj, _bwd, _bt = W.scale_of(d0[ybuild], dipb, dayb)
                    d1, _dn, _cb, _wc, _sz, _f = SB.series(
                        w, curve, cap_pct=W.CAP_PCT, per_unit=sc_ / den, den=den)
                    kt = W.kpis(d1[ytrade] * sc_, yrs[ytrade])
                    vals.setdefault(bname, []).append((dd, kt['median_year_pct']))
            for bname, lst in vals.items():
                real = [v for d_, v in lst if d_ == 0]
                sur = np.array([v for d_, v in lst if d_ != 0])
                if not real or not len(sur):
                    continue
                rows.append(dict(null=kind, scope=scope, step=stp['name'],
                                 book=bk, budget=bname, members=int(nmem[bi]),
                                 real=float(real[0]), n_draws=int(len(sur)),
                                 null_mean=float(sur.mean()),
                                 null_p5=float(np.percentile(sur, 5)),
                                 null_p95=float(np.percentile(sur, 95)),
                                 p_one_sided=float((sur >= real[0]).mean())))
    return pd.DataFrame(rows)


def stage_nulls(mode='A', tag='full', books_csv=None, jobs=8, sizes=SAMPLE_SIZES,
                ndraw=NDRAW_SAMPLED, nid=NDRAW_IDENTITY, out=None, out_tag='full'):
    G.manifest_check()
    S.load_costs()
    books_csv = books_csv or os.path.join(ROOTOUT, 'r2gate2', 'mode%s_books_full.csv' % mode)
    parts = []
    I = identity_null(books_csv, ndraw=nid, out_tag=out_tag, mode=mode)
    if len(I):
        parts.append(I)
        print('  identity null, FULL FIELD: %d (step, book, budget) cells, %d draws each'
              % (len(I), nid), flush=True)
    for kind in ('shuffle', 'random-entry'):
        for nsz in sizes:
            D = sampled_null(mode, tag, kind, nsz, ndraw=ndraw, jobs=jobs)
            if len(D):
                parts.append(D)
    A = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
    out = out or os.path.join(ROOTOUT, 'r2gate2', 'mode%s_books_nulls.csv' % mode)
    A.to_csv(out, index=False)
    print('  nulls: %d rows -> %s' % (len(A), out.replace(_R + '/', '')), flush=True)
    return A, out


if __name__ == '__main__':
    stage = G.opt('--stage', str, 'nulls')
    if stage == 'nulls':
        stage_nulls(G.opt('--mode', str, 'A'), G.opt('--tag', str, 'full'),
                    books_csv=G.opt('--books', str, None),
                    jobs=G.opt('--jobs', int, 8),
                    sizes=tuple(int(x) for x in G.opt('--sizes', str, '5000,20000').split(',')),
                    ndraw=G.opt('--draws', int, NDRAW_SAMPLED),
                    nid=G.opt('--id-draws', int, NDRAW_IDENTITY),
                    out=G.opt('--out', str, None),
                    out_tag=G.opt('--out-tag', str, 'full'))
    else:
        raise SystemExit('unknown stage %s' % stage)
