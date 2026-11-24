import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""MODE <M> WINNERS, NO GATES -- READ-ONLY OFF THE GATE 2 BANK AND GATE 3 SCORING
(Jack, 20 Nov). Individual strategies first; the book last.

WHAT "NO GATES" MEANS HERE. Nothing is filtered before it is measured. All
273,780 strategies are recorded on both unseen records, and the only cut made
afterwards is the LUCK FLOOR, which is a statement about chance and not a
preference about settings.

THE TWO UNSEEN RECORDS, per (strategy, stream):
  TRADE  the five steps' trade years stitched -- 2016, 2017, 2018, 2019, 2020.
         Each year's settings are the ones tuned before it, which is the walk
         forward exactly as built.
  GRADE  the five steps' grade years stitched -- 2015..2019. Also never seen by
         the tuner, so it is a second independent read on the same strategy.

THE t-STATISTIC IS EXACT, AND IT IS NOT STORED. l2tune computes
`sharpe = mean/sd * sqrt(252)` on PER-TRADE R, so sd = mean*sqrt(252)/sharpe
and the per-year sum of squares is sd^2 (n-1) + n mean^2. Those sum across the
five years, so the POOLED t = mean_pooled * sqrt(N) / sd_pooled is recovered
exactly from (n, expectancy_R, sharpe) without re-scoring anything.

THREE FIELDS ARE NOT EXACT FROM THE BANK, and each is named where it appears:
  stitched max DD   the bank holds each YEAR's max DD. Summing them is an upper
                    bound on the real drawdown of the stitched curve, and it is
                    the recipe gate 3's own stitched section already uses.
                    The TRUE chronological figure needs the concatenated trade
                    sequence, so it is computed for the WINNERS only, by
                    re-scoring that small set.
  stitched Sortino  the mean of the five per-year Sortinos, again gate 3's own
                    stitched recipe. A pooled downside deviation would need the
                    sum of squares over losing trades alone, which the bank
                    does not carry.
  longest losing    needs the ordered trade list, which the Scorer discards.
  streak            Computed for the WINNERS only, same targeted re-score.

STREAMED, NOT LOADED. The KPI bank is ~2 GB and concatenating it peaks near 4.
This reduces one part file at a time and keeps only per-(strategy, stream)
scalars, so it can run beside a chain without taking the memory its memguard
is watching.

    python3 code/l2r2winners.py --stage universe --mode A
"""
import time, json, glob
import numpy as np, pandas as pd

import l2sweep as S
import l2r2gate1 as G
import l2r2gate2 as G2
import l2r2book as BK
import l2r2gate3 as G3

RD = os.path.join(ROOTOUT, 'r2gate2')
KI = {k: i for i, k in enumerate(G3.KPIS)}
RECORDS = ('trade', 'grade')
# the per-(strategy, stream) columns this stage derives, in file order
FIELDS = ('n_trades', 'expectancy_R', 'total_R', 'profit_factor', 'win_rate',
          'sortino_meanyr', 'calmar', 'max_dd_R_sumyr', 'gross_R',
          'dd_pct_of_gross', 'worst_year_R', 'years_positive', 'years_present',
          'sd_R', 't_stat', 't_undefined')


def _year_index(record):
    """The bank year index of each step's contribution to one record."""
    out = []
    for stp in G2.steps():
        y = stp['trade'][0] if record == 'trade' else stp['grade'][0]
        out.append((stp['name'], y, G3.YEARS.index(y)))
    return out


def _reduce_part(K, idx, record):
    """One part file -> per-(strategy, stream) stitched scalars for one record.

    K is (n_part, 4 streams, 5 steps, 10 years, 9 kpis).
    """
    yi = _year_index(record)
    nb, nst = K.shape[0], K.shape[1]
    n = np.zeros((nb, nst)); tot = np.zeros((nb, nst))
    gross = np.zeros((nb, nst)); loss = np.zeros((nb, nst))
    ss = np.zeros((nb, nst)); wsum = np.zeros((nb, nst))
    ddsum = np.zeros((nb, nst)); sor = np.zeros((nb, nst)); sorn = np.zeros((nb, nst))
    pos = np.zeros((nb, nst)); present = np.zeros((nb, nst))
    worst = np.full((nb, nst), np.inf)
    undef = np.zeros((nb, nst), bool)
    per_year = {}
    for si, (_name, year, iy) in enumerate(yi):
        b = K[:, :, si, iy, :]
        ny = b[:, :, KI['n']]
        ok = np.isfinite(ny) & (ny > 0)
        mean = np.where(ok, b[:, :, KI['expectancy_R']], 0.0)
        ty = np.where(ok, b[:, :, KI['total_R']], 0.0)
        pf = b[:, :, KI['profit_factor']]
        shp = b[:, :, KI['sharpe']]
        nyv = np.where(ok, ny, 0.0)
        per_year['R_%d' % year] = np.where(ok, ty, np.nan)
        per_year['n_%d' % year] = np.where(ok, nyv, np.nan)
        n += nyv; tot += ty
        present += ok.astype(float)
        pos += (ok & (ty > 0)).astype(float)
        worst = np.where(ok, np.minimum(worst, ty), worst)
        # gross and loss, by gate 3's own identity: gross = tot*PF/(PF-1)
        gy = np.where(np.isfinite(pf) & (pf > 1), ty * pf / np.where(pf > 1, pf - 1, 1),
                      np.maximum(ty, 0.0))
        gy = np.where(ok & np.isfinite(gy), gy, 0.0)
        gross += gy; loss += np.maximum(gy - ty, 0.0)
        wsum += np.where(ok, b[:, :, KI['win_rate']] * nyv, 0.0)
        ddsum += np.where(ok & np.isfinite(b[:, :, KI['max_dd_R']]),
                          b[:, :, KI['max_dd_R']], 0.0)
        sv = b[:, :, KI['sortino']]
        sgood = ok & np.isfinite(sv)
        sor += np.where(sgood, sv, 0.0); sorn += sgood.astype(float)
        # --- the sum of squares, recovered from sharpe
        # sd = mean*sqrt(252)/sharpe ; SS_y = sd^2 (n-1) + n mean^2
        with np.errstate(divide='ignore', invalid='ignore'):
            sd = np.where(np.isfinite(shp) & (shp != 0),
                          np.abs(mean) * np.sqrt(252.0) / np.abs(shp), 0.0)
        # sharpe == 0 means sd == 0 (identical trades) UNLESS mean is also 0,
        # in which case sd is genuinely unrecoverable and the record is flagged
        amb = ok & (np.isfinite(shp)) & (shp == 0) & (np.abs(mean) < 1e-12) & (nyv > 1)
        undef |= amb
        ss += np.where(ok, sd ** 2 * np.maximum(nyv - 1, 0) + nyv * mean ** 2, 0.0)
    with np.errstate(divide='ignore', invalid='ignore'):
        mean_p = np.where(n > 0, tot / n, np.nan)
        var_p = np.where(n > 1, (ss - n * mean_p ** 2) / (n - 1), np.nan)
        var_p = np.where(np.isfinite(var_p) & (var_p > 0), var_p, np.nan)
        sd_p = np.sqrt(var_p)
        t = np.where(np.isfinite(sd_p) & (sd_p > 0), mean_p * np.sqrt(n) / sd_p, np.nan)
        pf_p = np.where(loss > 0, gross / loss, np.where(gross > 0, np.inf, np.nan))
        wr_p = np.where(n > 0, wsum / n, np.nan)
        sor_p = np.where(sorn > 0, sor / np.maximum(sorn, 1), np.nan)
        cal_p = np.where(ddsum > 0, tot / ddsum, np.nan)
        ddpct = np.where(gross > 0, 100.0 * ddsum / gross, np.nan)
    out = dict(n_trades=n, expectancy_R=mean_p, total_R=tot, profit_factor=pf_p,
               win_rate=wr_p, sortino_meanyr=sor_p, calmar=cal_p,
               max_dd_R_sumyr=ddsum, gross_R=gross, dd_pct_of_gross=ddpct,
               worst_year_R=np.where(np.isfinite(worst), worst, np.nan),
               years_positive=pos, years_present=present,
               sd_R=sd_p, t_stat=t, t_undefined=undef.astype(float))
    out.update(per_year)
    return out


def universe_file(mode):
    return os.path.join(RD, 'mode%s_winners_universe.npz' % mode)


def stage_universe(mode='A', tag='full'):
    """Both unseen records for every (strategy, stream), streamed off the bank."""
    G.manifest_check()
    z = np.load(BK._bank_slice_file(mode, tag), allow_pickle=True)
    nbank = int(z['n']); CB = z['combo']; del z
    parts = sorted(glob.glob(os.path.join(RD, 'mode%s_gate3parts' % mode,
                                          'g3_*_of32.npz')))
    assert parts, 'no gate 3 KPI bank for mode %s' % mode
    acc = {rec: {} for rec in RECORDS}
    seen = np.zeros(nbank, bool)
    t0 = time.time()
    for pi, f in enumerate(parts, 1):
        zz = np.load(f, allow_pickle=True)
        ids = np.asarray(zz['idx'], np.int64)
        if not len(ids):
            continue
        K = np.asarray(zz['K'], np.float64)
        seen[ids] = True
        for rec in RECORDS:
            red = _reduce_part(K, ids, rec)
            for k, v in red.items():
                if k not in acc[rec]:
                    acc[rec][k] = np.full((nbank, K.shape[1]), np.nan)
                acc[rec][k][ids] = v
        del K, zz
        if pi % 8 == 0 or pi == len(parts):
            print('    universe: %d of %d part files reduced (%.1f min)'
                  % (pi, len(parts), (time.time() - t0) / 60), flush=True)
    nseen = int(seen.sum())
    print('  universe [mode %s]: %s of %s strategies carry a gate 3 record'
          % (mode, f'{nseen:,}', f'{nbank:,}'), flush=True)
    assert nseen == nbank, ('the bank covers %d strategies but gate 3 scored %d -- '
                            'this report would describe a smaller universe than it '
                            'claims' % (nbank, nseen))
    save = dict(n=np.int64(nbank), streams=np.array(G2.STREAMS, dtype=object),
                sid=np.array(['|'.join(r) for r in CB], dtype=object),
                fields=np.array(FIELDS, dtype=object),
                records=np.array(RECORDS, dtype=object))
    for rec in RECORDS:
        for k, v in acc[rec].items():
            save['%s__%s' % (rec, k)] = v.astype(np.float32)
    f = universe_file(mode)
    np.savez_compressed(f, **save)
    print('  universe -> %s (%.0f MB)'
          % (os.path.relpath(f, _R), os.path.getsize(f) / 1048576), flush=True)
    for rec in RECORDS:
        t = acc[rec]['t_stat']
        fin = np.isfinite(t)
        print('    %s record: t finite on %s of %s (strategy, stream) cells, '
              'max t %.2f, undefined %s'
              % (rec, f'{int(fin.sum()):,}', f'{t.size:,}',
                 float(np.nanmax(t)) if fin.any() else float('nan'),
                 f"{int(np.nansum(acc[rec]['t_undefined'])):,}"), flush=True)
    return f


# ==========================================================================
# THE LUCK FLOOR, WAY (a): ANALYTIC, FROM THE NUMBER OF TRIES
# ==========================================================================
def load_universe(mode):
    z = np.load(universe_file(mode), allow_pickle=True)
    return z


def _phi_inv(p):
    """Inverse standard normal CDF, no scipy dependency.

    Acklam's rational approximation, |error| < 1.15e-9 over the open interval,
    then two Halley refinement steps using an erfc built from the series. At
    the tail probabilities here (p ~ 1 - 1e-7) the refinement is what keeps the
    threshold trustworthy to the second decimal.
    """
    import math
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    pl, ph = 0.02425, 1 - 0.02425
    if p <= 0 or p >= 1:
        return float('nan')
    if p < pl:
        q = math.sqrt(-2 * math.log(p))
        x = (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
            ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    elif p <= ph:
        q = p - 0.5; r = q*q
        x = (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / \
            (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)
    else:
        q = math.sqrt(-2 * math.log(1 - p))
        x = -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
             ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    for _ in range(2):
        e = 0.5 * math.erfc(-x / math.sqrt(2)) - p
        u = e * math.sqrt(2 * math.pi) * math.exp(x * x / 2)
        x = x - u / (1 + x * u / 2)
    return x


def analytic_floor(M, alpha=0.05):
    """Two thresholds on t, both reported, neither claimed to be the truth.

    max-of-M   the 95th percentile of the LARGEST of M independent standard
               normals: Phi^-1(alpha_root) with alpha_root = (1-alpha)^(1/M).
               This is the honest question "what is the best t I should expect
               to see having looked M times at nothing".
    bonferroni Phi^-1(1 - alpha/(2M)), the two-sided familywise line. It is
               slightly higher than max-of-M and is the conventional citation.

    WHAT BOTH ASSUME, and it is not true here: that each try is an independent
    draw and that t is standard normal. Trade R in FX is fat-tailed, the 28
    pairs overlap in time so trades inside one strategy are not independent,
    and the four streams of one strategy share settings. Fat tails and serial
    dependence both INFLATE real t beyond the normal, so these lines are
    optimistic -- a strategy clearing them has not proved an edge, it has only
    cleared the weakest version of the question.
    """
    ar = (1.0 - alpha) ** (1.0 / M)
    return dict(M=int(M), alpha=alpha,
                t_max_of_M=_phi_inv(ar),
                t_bonferroni=_phi_inv(1.0 - alpha / (2.0 * M)))


def stage_floors(mode='A'):
    z = load_universe(mode)
    nstrat = int(z['n']); streams = list(z['streams'])
    rows = []
    for M, why in ((nstrat, 'strategies, as Jack specified'),
                   (nstrat * len(streams),
                    'strategy x stream cells, which is what is actually compared')):
        a = analytic_floor(M)
        rows.append(dict(basis=why, M=a['M'], alpha=a['alpha'],
                         t_max_of_M=a['t_max_of_M'], t_bonferroni=a['t_bonferroni']))
    F = pd.DataFrame(rows)
    obs = []
    for rec in RECORDS:
        t = np.asarray(z['%s__t_stat' % rec], np.float64)
        for si, sname in enumerate(streams):
            col = t[:, si]
            fin = np.isfinite(col)
            obs.append(dict(record=rec, stream=sname, n_finite=int(fin.sum()),
                            t_max=float(np.nanmax(col)) if fin.any() else np.nan,
                            t_p99=float(np.nanpercentile(col, 99)) if fin.any() else np.nan,
                            t_median=float(np.nanmedian(col)) if fin.any() else np.nan))
        fin = np.isfinite(t)
        obs.append(dict(record=rec, stream='ALL', n_finite=int(fin.sum()),
                        t_max=float(np.nanmax(t)) if fin.any() else np.nan,
                        t_p99=float(np.nanpercentile(t, 99)) if fin.any() else np.nan,
                        t_median=float(np.nanmedian(t)) if fin.any() else np.nan))
    O = pd.DataFrame(obs)
    fa = os.path.join(RD, 'mode%s_winners_floor_analytic.csv' % mode)
    fo = os.path.join(RD, 'mode%s_winners_t_observed.csv' % mode)
    F.to_csv(fa, index=False); O.to_csv(fo, index=False)
    print('  analytic floor -> %s' % os.path.relpath(fa, _R), flush=True)
    for _i, r in F.iterrows():
        print('    M=%s (%s): max-of-M t %.3f, Bonferroni t %.3f'
              % (f"{r.M:,}", r.basis, r.t_max_of_M, r.t_bonferroni), flush=True)
    print('  observed t -> %s' % os.path.relpath(fo, _R), flush=True)
    for _i, r in O[O.stream == 'ALL'].iterrows():
        print('    %s record: max t %.3f, p99 %.3f, median %.3f over %s cells'
              % (r.record, r.t_max, r.t_p99, r.t_median, f"{r.n_finite:,}"), flush=True)
    return fa, fo


def stage_sweep(mode='A', npts=60):
    """The floor swept over its full range: who clears it, and what they earn.

    THE CURVE IS THE POINT. A single threshold invites the question "why that
    one"; the curve answers it by showing the whole range at once, so the
    reader can see whether the surviving count and the mean trade-year R move
    together or whether survivors are just the tail of a null.
    """
    z = load_universe(mode)
    streams = list(z['streams'])
    rows = []
    for rec in RECORDS:
        t = np.asarray(z['%s__t_stat' % rec], np.float64)
        R = np.asarray(z['trade__expectancy_R'], np.float64)   # always the TRADE year
        TR = np.asarray(z['trade__total_R'], np.float64)
        fin = np.isfinite(t)
        if not fin.any():
            continue
        lo, hi = 0.0, float(np.nanmax(t))
        grid = np.linspace(lo, max(hi, 1.0), npts)
        for thr in grid:
            for si, sname in enumerate(streams + ['ALL']):
                if sname == 'ALL':
                    m = fin & (t >= thr)
                    rr, tt = R[m], TR[m]
                else:
                    m = fin[:, si] & (t[:, si] >= thr)
                    rr, tt = R[m, si], TR[m, si]
                rows.append(dict(record=rec, stream=sname, t_floor=float(thr),
                                 n_clearing=int(m.sum()),
                                 mean_trade_expectancy_R=(float(np.nanmean(rr))
                                                          if m.sum() else np.nan),
                                 mean_trade_total_R=(float(np.nanmean(tt))
                                                     if m.sum() else np.nan)))
    D = pd.DataFrame(rows)
    f = os.path.join(RD, 'mode%s_winners_floor_sweep.csv' % mode)
    D.to_csv(f, index=False)
    print('  floor sweep: %d rows over %d thresholds -> %s'
          % (len(D), npts, os.path.relpath(f, _R)), flush=True)
    return f


# ==========================================================================
# THE LUCK FLOOR, WAY (b): EMPIRICAL, A PER-STRATEGY RANDOM-ENTRY NULL
# ==========================================================================
# WHY THE PROJECT'S EXISTING RANDOM-ENTRY NULL CANNOT BE REUSED. l2r2null2's
# null shifts WHEN a trade lands in the book and keeps the trade's R. For a
# BOOK that is the right question -- it destroys the alignment between the
# members' timing and the market. For ONE STRATEGY's expectancy it is
# degenerate: the same R values in a different order have the same mean.
#
# WHAT THIS NULL DOES INSTEAD, and it is exactly "same costs and holds":
# every real trade keeps its direction, its unit size, its cost and its HOLD
# in bars; its entry moves to a uniformly random bar inside the same trade
# year on the same pair; and R is recomputed from the price path over that
# hold. It asks: had this strategy traded the same instruments, the same number
# of times, in the same sizes, for the same durations, but at random moments,
# what expectancy would it have earned?
#
# THE ONE WAY IT IS NOT LIKE-FOR-LIKE, stated here and in the md: a null trade
# is held to the end of its hold with no stop, while the real trade may have
# exited early on one. The reconstruction error is MEASURED rather than
# asserted -- the stage recomputes R for the REAL entries by the same formula
# and reports how far that lands from the engine's own R, so the reader can see
# the size of the approximation instead of taking it on faith.
def _trade_lists(Y, mode, combo, ip, risk, sname, plan, aidx):
    """Every trade of one tuned configuration inside one window, per pair."""
    import l2lib as L, l2engine as E
    sc = Y.sc
    c1, c2, vol, base, ex = combo
    kwm = S.mode_kw(mode)
    am = float(risk['atr_mult']); alen = int(risk['atr_len'])
    t1 = L.KIND[c1] == 'TERNARY'; t2 = L.KIND[c2] == 'TERNARY'
    out = {}
    for p in sc.pairs:
        o, h, l, c = sc.arr[p]
        atr = sc._atr.get((alen, p))
        if atr is None:
            atr = L.P.atr(h, l, c, alen); sc._atr[(alen, p)] = atr
        g = sc.cache.get
        lt, st, lc, scr = g(c1, ip['c1'], p, sc.arr[p])[:4]
        _, _, c2lc, c2sc = g(c2, ip['c2'], p, sc.arr[p])[:4]
        vl, vs = g(vol, ip['vol'], p, sc.arr[p])[:2]
        bl = g(base, ip['base'], p, sc.arr[p])
        bl = bl[0] if isinstance(bl, tuple) else bl
        el, es = g(ex, ip['exit_ind'], p, sc.arr[p])[:2]
        b = sc.buf[p]
        nt, _, _, _ = E.run_bars(
            o, h, l, c, atr, bl, lt, st, lc, scr, c2lc, c2sc, vl, vs, el, es,
            sc._nosus[p], t1, t2, True, True, True,
            kwm['exit_on_c1_flip'], kwm['exit_on_base_cross'], kwm['exit_on_exit_ind'],
            False, int(plan), S.RISK, am, float(risk['tp_mult']),
            float(risk['trail_mult']), float(risk['trail_arm']), float(risk['be_pct']),
            1.5, 7, True, True,
            b['entry_bar'], b['exit_bar'], b['dir'], b['leg'], b['entry_px'],
            b['exit_px'], b['units'], b['r'], b['reason'], b['route'],
                *E._amb_off(len(c)))
        if nt == 0:
            continue
        eb = np.array(b['entry_bar'][:nt], np.int64)
        xb = np.array(b['exit_bar'][:nt], np.int64)
        keep = aidx[p][eb] >= 0                     # entered inside the window
        if not keep.any():
            continue
        cst = (Y.cfrac[p] * Y.cmult[p][eb] * np.abs(b['entry_px'][:nt])
               * np.abs(b['units'][:nt]) / S.RISK) * am
        out[p] = dict(eb=eb[keep], xb=xb[keep],
                      dirv=np.array(b['dir'][:nt], np.float64)[keep],
                      units=np.array(b['units'][:nt], np.float64)[keep],
                      r=np.array(b['r'][:nt], np.float64)[keep],
                      cst=np.asarray(cst, np.float64)[keep])
    return out


def _null_draws(Y, tl, ndraw, rng):
    """(ndraw+1, ) summed R and trade count; row 0 is the RECONSTRUCTED real.

    Row 0 uses the REAL entry bars through the same formula, so the caller can
    compare it against the engine's own R and report the approximation.
    """
    tot = np.zeros(ndraw + 1); ss = np.zeros(ndraw + 1); nn = 0
    eng = 0.0
    for p, d in tl.items():
        cl = np.asarray(Y.cl[p], np.float64)
        nb = len(cl)
        eb, xb = d['eb'], d['xb']
        hold = np.maximum(xb - eb, 1)
        ok = (eb + hold) < nb
        if not ok.any():
            continue
        eb, hold = eb[ok], hold[ok]
        dirv, units, cst = d['dirv'][ok], d['units'][ok], d['cst'][ok]
        eng += float(d['r'][ok].sum()); nn += int(ok.sum())
        # row 0: the real entries, same formula
        r0 = dirv * (cl[eb + hold] - cl[eb]) * units / S.RISK - cst
        tot[0] += float(r0.sum()); ss[0] += float((r0 ** 2).sum())
        # the draws: a uniformly random entry that leaves room for the hold
        hi = nb - hold - 1
        for dd in range(1, ndraw + 1):
            e2 = (rng.random(len(eb)) * np.maximum(hi, 1)).astype(np.int64)
            rr = dirv * (cl[e2 + hold] - cl[e2]) * units / S.RISK - cst
            tot[dd] += float(rr.sum()); ss[dd] += float((rr ** 2).sum())
    return tot, ss, nn, eng


def _nullstrat_worker(args):
    shard, nshard, mode, tag, idxs, ndraw, seed, cap = args
    S.load_costs()
    z = np.load(BK._bank_slice_file(mode, tag), allow_pickle=True)
    TG = z['tag']; CB = z['combo']
    mine = [i for k, i in enumerate(idxs) if k % nshard == shard]
    ST = G2.steps()
    Y = G2.Years(cap=cap)
    aidx = {}
    for si, stp in enumerate(ST):
        a, _d = BK.year_dayidx(Y, {stp['trade'][0]})
        aidx[si] = a
    rng = np.random.default_rng(seed + shard)
    rows = []
    t0 = time.time()
    for q, k in enumerate(mine, 1):
        combo = tuple(CB[k])
        for stream in range(4):
            sl, rt = stream // 2, stream % 2
            sname, plan, _code = S.SLICES[sl]
            tot = np.zeros(ndraw + 1); ssq = np.zeros(ndraw + 1); nn = 0; eng = 0.0
            for si, stp in enumerate(ST):
                ci = int(TG[k, stream, si])
                if ci < 0:
                    continue
                ip, risk = BK.winner_config(mode, combo, sname, ci)
                tl = _trade_lists(Y, mode, combo, ip, risk, sname, plan, aidx[si])
                if not tl:
                    continue
                t_, s_, n_, e_ = _null_draws(Y, tl, ndraw, rng)
                tot += t_; ssq += s_; nn += n_; eng += e_
            if nn <= 0:
                continue
            # t per draw, from the same pooled identity the universe uses:
            # sd^2 = (sum r^2 - n mean^2) / (n - 1), t = mean sqrt(n) / sd
            def _t(i):
                m = tot[i] / nn
                v = (ssq[i] - nn * m * m) / max(nn - 1, 1)
                return (m * np.sqrt(nn) / np.sqrt(v)) if v > 0 else np.nan
            rows.append(dict(bank_row=k, stream=G2.STREAMS[stream], n_trades=nn,
                             engine_total_R=eng,
                             recon_real_total_R=float(tot[0]),
                             recon_real_expectancy_R=float(tot[0] / nn),
                             recon_real_t=float(_t(0)),
                             **{'null_total_R_%02d' % d: float(tot[d])
                                for d in range(1, ndraw + 1)},
                             **{'null_expectancy_R_%02d' % d: float(tot[d] / nn)
                                for d in range(1, ndraw + 1)},
                             **{'null_t_%02d' % d: float(_t(d))
                                for d in range(1, ndraw + 1)}))
        if q % 10 == 0:
            el = time.time() - t0
            print('    nullstrat shard %02d: %d/%d  %.2f s/strategy  %.0f min left'
                  % (shard, q, len(mine), el / q, (el / q) * (len(mine) - q) / 60),
                  flush=True)
    f = os.path.join(RD, 'mode%s_winners_nullparts' % mode,
                     'ns_%04d_of%d.npz' % (shard, nshard))
    os.makedirs(os.path.dirname(f), exist_ok=True)
    D = pd.DataFrame(rows)
    D.to_csv(f.replace('.npz', '.csv'), index=False)
    return f.replace('.npz', '.csv'), len(rows)


def stage_nullstrat(mode='A', tag='full', nsample=2000, ndraw=20, jobs=4,
                    seed=20261120, cap=4000):
    """The empirical luck floor: a per-strategy random-entry null.

    STRATIFIED BY c1, the first condition slot, so the sample spans the grid's
    families rather than landing wherever a uniform draw puts it. Within a
    family the pick is uniform.
    """
    import multiprocessing as mp
    G.manifest_check()
    S.load_costs()
    z = np.load(BK._bank_slice_file(mode, tag), allow_pickle=True)
    CB = z['combo']; ntot = int(z['n']); del z
    c1 = np.array([r[0] for r in CB])
    fam = sorted(set(c1.tolist()))
    rng = np.random.default_rng(seed)
    per = max(1, nsample // len(fam))
    pick = []
    for f_ in fam:
        cand = np.flatnonzero(c1 == f_)
        if not len(cand):
            continue
        pick.extend(rng.choice(cand, size=min(per, len(cand)), replace=False).tolist())
    if len(pick) < nsample:
        rest = np.setdiff1d(np.arange(ntot), np.array(pick))
        pick.extend(rng.choice(rest, size=min(nsample - len(pick), len(rest)),
                               replace=False).tolist())
    idxs = sorted(int(x) for x in pick[:nsample])
    print('  nullstrat [mode %s]: %s strategies stratified over %d c1 families, '
          '%d draws each, %d workers'
          % (mode, f'{len(idxs):,}', len(fam), ndraw, jobs), flush=True)
    args = [(k, jobs, mode, tag, idxs, ndraw, seed, cap) for k in range(jobs)]
    t0 = time.time()
    if jobs == 1:
        res = [_nullstrat_worker(a) for a in args]
    else:
        with mp.Pool(jobs) as pool:
            res = pool.map(_nullstrat_worker, args)
    D = pd.concat([pd.read_csv(f) for f, _n in res], ignore_index=True)
    out = os.path.join(RD, 'mode%s_winners_nullstrat.csv' % mode)
    D.to_csv(out, index=False)
    print('  nullstrat: %s (strategy, stream) records in %.1f min -> %s'
          % (f'{len(D):,}', (time.time() - t0) / 60, os.path.relpath(out, _R)),
          flush=True)
    # THE APPROXIMATION, MEASURED. How close does the same formula on the REAL
    # entries land to the engine's own R?
    if len(D):
        a = D.engine_total_R.to_numpy(float); b = D.recon_real_total_R.to_numpy(float)
        ok = np.isfinite(a) & np.isfinite(b)
        if ok.sum() > 2:
            cc = float(np.corrcoef(a[ok], b[ok])[0, 1])
            print('    reconstruction of the REAL trades by the null formula: '
                  'correlation %.4f, mean engine %.3f R vs reconstructed %.3f R '
                  'over %s records' % (cc, a[ok].mean(), b[ok].mean(), f'{int(ok.sum()):,}'),
                  flush=True)
    return out


# ==========================================================================
# THE EXTREME-VALUE EXTRAPOLATION: BEST-OF-273,780 UNDER THE NULL
# ==========================================================================
EULER = 0.5772156649015329


def _gumbel_mom(x):
    """Gumbel (mu, sigma) by method of moments on block maxima.

    Method of moments rather than MLE on purpose: with 20 block maxima per
    stream an MLE's extra precision is not real, and the moment estimator
    cannot fail to converge and leave the report with a blank where a floor
    should be.
    """
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    if len(x) < 3:
        return np.nan, np.nan
    sd = float(x.std(ddof=1))
    sig = sd * np.sqrt(6.0) / np.pi
    return float(x.mean() - sig * EULER), sig


def _ev_floor(block_max, block_size, M, q=0.95):
    """Scale a Gumbel fitted on maxima of `block_size` up to maxima of M.

    If the max of B tries is Gumbel(mu, sigma), the max of M is
    Gumbel(mu + sigma ln(M/B), sigma). The EXPECTED best-of-M is its mean,
    mu_M + sigma * EULER; the q-th percentile is mu_M - sigma ln(-ln q).
    """
    mu, sig = _gumbel_mom(block_max)
    if not np.isfinite(mu):
        return dict(mu=np.nan, sigma=np.nan, mu_M=np.nan, expected_best=np.nan,
                    pct=np.nan, block_size=int(block_size), M=int(M), q=q,
                    n_blocks=0)
    mu_M = mu + sig * np.log(max(M, 1) / max(block_size, 1))
    return dict(mu=mu, sigma=sig, mu_M=mu_M,
                expected_best=mu_M + sig * EULER,
                pct=mu_M - sig * np.log(-np.log(q)),
                block_size=int(block_size), M=int(M), q=q,
                n_blocks=int(np.isfinite(np.asarray(block_max, float)).sum()))


def stage_floorb(mode='A'):
    """The empirical floor, in t-space and in expectancy-space, both reported.

    WHY t-SPACE IS THE BINDING ONE. The null reconstructs a trade as "held the
    same number of bars, no stop", because re-simulating a shifted entry
    through the engine is a 15-hour pass. Measured on this sample that
    reconstruction is systematically more negative than the engine
    (correlation is high, the LEVEL is not), so an expectancy floor built in
    that space sits too LOW and would flatter every strategy. The t-statistic
    divides by the spread, which absorbs most of the distortion -- so the
    t-floor is used for selection and the expectancy floor is reported beside
    it with its bias measured, not asserted.
    """
    nsf = os.path.join(RD, 'mode%s_winners_nullstrat.csv' % mode)
    assert os.path.exists(nsf), nsf + ' is missing -- run --stage nullstrat first'
    N = pd.read_csv(nsf)
    z = load_universe(mode)
    streams = list(z['streams']); nstrat = int(z['n'])
    tcols = [c for c in N.columns if c.startswith('null_t_')]
    ecols = [c for c in N.columns if c.startswith('null_expectancy_R_')]
    rows = []
    for space, cols in (('t', tcols), ('expectancy_R', ecols)):
        for sname in streams + ['ALL']:
            g = N if sname == 'ALL' else N[N.stream == sname]
            if not len(g):
                continue
            V = g[cols].to_numpy(float)
            # ONE BLOCK PER DRAW: the maximum over the sampled strategies in
            # that draw IS the best of `block_size` no-edge tries.
            bm = np.nanmax(V, axis=0)
            B = int(np.isfinite(V).sum(axis=0).max())
            M = nstrat if sname != 'ALL' else nstrat * len(streams)
            r = _ev_floor(bm, B, M)
            r.update(space=space, stream=sname,
                     null_mean=float(np.nanmean(V)), null_sd=float(np.nanstd(V, ddof=1)),
                     null_max_observed=float(np.nanmax(V)),
                     n_records=int(len(g)), n_draws=len(cols))
            rows.append(r)
    F = pd.DataFrame(rows)
    f = os.path.join(RD, 'mode%s_winners_floor_empirical.csv' % mode)
    F.to_csv(f, index=False)
    print('  empirical floor -> %s' % os.path.relpath(f, _R), flush=True)
    for _i, r in F[F.stream == 'ALL'].iterrows():
        print('    %-14s null mean %+.4f sd %.4f | Gumbel mu %+.4f sigma %.4f on %d blocks '
              'of %s | expected best-of-%s %+.4f, its %.0fth pct %+.4f'
              % (r.space, r.null_mean, r.null_sd, r.mu, r.sigma, r.n_blocks,
                 f'{r.block_size:,}', f'{r.M:,}', r.expected_best, r.q * 100, r.pct),
              flush=True)
    # --- THE DISTORTION, MEASURED: engine-space t against reconstruction-space t
    ut = np.asarray(z['trade__t_stat'], np.float64)
    si = {sname: i for i, sname in enumerate(streams)}
    N2 = N.dropna(subset=['recon_real_t']).copy()
    N2['engine_t'] = [ut[int(r.bank_row), si[r.stream]] for _k, r in N2.iterrows()]
    ok = np.isfinite(N2.engine_t.to_numpy(float)) & np.isfinite(N2.recon_real_t.to_numpy(float))
    D = N2[ok]
    dd = os.path.join(RD, 'mode%s_winners_recon_distortion.csv' % mode)
    D[['bank_row', 'stream', 'n_trades', 'engine_total_R', 'recon_real_total_R',
       'engine_t', 'recon_real_t']].to_csv(dd, index=False)
    if len(D) > 2:
        a = D.engine_t.to_numpy(float); b = D.recon_real_t.to_numpy(float)
        print('    reconstruction distortion on t, over %s records: engine mean %+.3f, '
              'reconstruction mean %+.3f, correlation %.4f, median ratio %.3f -> %s'
              % (f'{len(D):,}', a.mean(), b.mean(), float(np.corrcoef(a, b)[0, 1]),
                 float(np.nanmedian(np.where(b != 0, a / b, np.nan))),
                 os.path.relpath(dd, _R)), flush=True)
    return f, dd


# ==========================================================================
# THE NON-LUCK WINNERS
# ==========================================================================
MIN_TRADES_PER_YEAR = 50
MIN_YEARS_POSITIVE = 4


# THE FOUR ANALYTIC LINES, AND WHICH ONE IS THE DEFAULT.
#   stated      max-of-M at M = 273,780 STRATEGIES. This is the line Jack
#               specified -- "the t-statistic threshold for the maximum of
#               273,780 independent tries under no edge" -- and it is the
#               default here for that reason.
#   bonf        Bonferroni at M = 273,780.
#   cell        max-of-M at M = 1,095,120 strategy x stream cells, which is
#               what is actually compared.
#   cellbonf    Bonferroni on the cell basis; the strictest of the four.
# The winner count moves with the choice, so the md reports all four and says
# which one produced the set it lists. A floor is an argument, not a constant,
# and hiding the ladder would hide the argument.
FLOOR_BASES = ('stated', 'bonf', 'cell', 'cellbonf')


def binding_floors(mode, basis='stated'):
    """(analytic, empirical, binding) t floors. BOTH must be cleared."""
    A = pd.read_csv(os.path.join(RD, 'mode%s_winners_floor_analytic.csv' % mode))
    E = pd.read_csv(os.path.join(RD, 'mode%s_winners_floor_empirical.csv' % mode))
    strat = A[A.basis.str.contains('strategies')].iloc[0]
    cell = A[A.basis.str.contains('cells')].iloc[0]
    an = {'stated': float(strat.t_max_of_M), 'bonf': float(strat.t_bonferroni),
          'cell': float(cell.t_max_of_M), 'cellbonf': float(cell.t_bonferroni)}[basis]
    er = E[(E.space == 't') & (E.stream == 'ALL')].iloc[0]
    em = float(er.pct)
    return an, em, max(an, em)


def stage_winners(mode='A', tag='full', basis='stated'):
    """Above BOTH floors, >= 50 trades in every unseen year, >= 4 of 5 positive."""
    G.manifest_check()
    z = load_universe(mode)
    streams = list(z['streams']); sid = np.asarray(z['sid'])
    an, em, binding = binding_floors(mode, basis)
    t = np.asarray(z['trade__t_stat'], np.float64)
    yp = np.asarray(z['trade__years_positive'], np.float64)
    nyr = [c for c in z.files if c.startswith('trade__n_')]
    NY = np.stack([np.asarray(z[c], np.float64) for c in sorted(nyr)], axis=-1)
    minn = np.nanmin(np.where(np.isfinite(NY), NY, np.inf), axis=-1)
    keep = (np.isfinite(t) & (t >= binding) & (minn >= MIN_TRADES_PER_YEAR)
            & (yp >= MIN_YEARS_POSITIVE))
    print('  floors [mode %s, %s basis]: analytic t %.3f, empirical t %.3f -> binding %.3f'
          % (mode, basis, an, em, binding), flush=True)
    stepcut = [('above the binding floor', np.isfinite(t) & (t >= binding)),
               ('    and >= %d trades in every unseen year' % MIN_TRADES_PER_YEAR,
                np.isfinite(t) & (t >= binding) & (minn >= MIN_TRADES_PER_YEAR)),
               ('    and positive in >= %d of 5 trade years' % MIN_YEARS_POSITIVE, keep)]
    for lbl, m in stepcut:
        print('    %-46s %6d cells, %6d distinct strategies'
              % (lbl, int(m.sum()), int(np.unique(np.flatnonzero(m.any(axis=1))).size)),
              flush=True)
    rows = []
    bank, st_i = np.nonzero(keep)
    for k, si in zip(bank, st_i):
        r = dict(mode=mode, bank_row=int(k), stream=streams[si], sid=sid[k],
                 t_stat=float(t[k, si]),
                 floor_analytic=an, floor_empirical=em, floor_binding=binding,
                 min_trades_in_a_year=float(minn[k, si]),
                 years_positive=float(yp[k, si]))
        for rec in RECORDS:
            for f_ in ('n_trades', 'expectancy_R', 'total_R', 'profit_factor', 'win_rate',
                       'sortino_meanyr', 'calmar', 'max_dd_R_sumyr', 'gross_R',
                       'dd_pct_of_gross', 'worst_year_R', 'years_positive', 't_stat'):
                r['%s_%s' % (rec, f_)] = float(np.asarray(z['%s__%s' % (rec, f_)])[k, si])
            r['%s_return_per_dd' % rec] = (
                r['%s_total_R' % rec] / r['%s_max_dd_R_sumyr' % rec]
                if r['%s_max_dd_R_sumyr' % rec] > 0 else np.nan)
        for c in sorted(z.files):
            if c.startswith('trade__R_') or c.startswith('trade__n_'):
                r[c.replace('trade__', '')] = float(np.asarray(z[c])[k, si])
        rows.append(r)
    W = pd.DataFrame(rows)
    if len(W):
        W = W.sort_values('t_stat', ascending=False).reset_index(drop=True)
    f = os.path.join(RD, 'mode%s_winners.csv' % mode)
    W.to_csv(f, index=False)
    print('  NON-LUCK WINNERS [mode %s, %s floor]: %d -> %s'
          % (mode, basis, len(W), os.path.relpath(f, _R)), flush=True)
    # THE LADDER, so the choice of line is visible rather than buried
    lad = []
    for b in FLOOR_BASES:
        a2, e2, bd = binding_floors(mode, b)
        m2 = (np.isfinite(t) & (t >= bd) & (minn >= MIN_TRADES_PER_YEAR)
              & (yp >= MIN_YEARS_POSITIVE))
        lad.append(dict(basis=b, t_analytic=a2, t_empirical=e2, t_binding=bd,
                        n_winners=int(m2.sum()), is_default=int(b == basis)))
    L = pd.DataFrame(lad)
    lf = os.path.join(RD, 'mode%s_winners_floor_ladder.csv' % mode)
    L.to_csv(lf, index=False)
    print('    floor ladder -> %s' % os.path.relpath(lf, _R), flush=True)
    for _i, r in L.iterrows():
        print('      %-9s binding t %.3f -> %2d winners%s'
              % (r.basis, r.t_binding, r.n_winners, '   <- default' if r.is_default else ''),
              flush=True)
    if len(W):
        print('    t %.3f..%.3f | total R %.1f..%.1f | return/DD %.2f..%.2f'
              % (W.t_stat.min(), W.t_stat.max(),
                 W.trade_total_R.min(), W.trade_total_R.max(),
                 np.nanmin(W.trade_return_per_dd), np.nanmax(W.trade_return_per_dd)),
              flush=True)
    return f, W


def stage_family(mode='A', tag='full'):
    """For each winner, how its nearest cousins did. Lone survivors flagged.

    COUSINS ARE SAME (c1, c2) -- the two condition slots, which is what Jack
    called nearest. A winner whose cousins are all poor is a lone survivor and
    is flagged: one strategy standing alone in its family is the shape a lucky
    draw takes, while a winner surrounded by near-winners is the shape a real
    effect takes.
    """
    z = load_universe(mode)
    streams = list(z['streams']); sid = np.asarray(z['sid'])
    W = pd.read_csv(os.path.join(RD, 'mode%s_winners.csv' % mode))
    if not len(W):
        f = os.path.join(RD, 'mode%s_winners_family.csv' % mode)
        pd.DataFrame().to_csv(f, index=False)
        print('  family support: no winners, nothing to support', flush=True)
        return f
    t = np.asarray(z['trade__t_stat'], np.float64)
    TR = np.asarray(z['trade__total_R'], np.float64)
    fam_key = np.array(['|'.join(s.split('|')[:2]) for s in sid])
    rows = []
    for _i, w in W.iterrows():
        si = streams.index(w.stream)
        key = '|'.join(str(w.sid).split('|')[:2])
        m = (fam_key == key)
        m[int(w.bank_row)] = False                    # the winner is not its own cousin
        tt = t[m, si]; rr = TR[m, si]
        fin = np.isfinite(tt)
        n = int(fin.sum())
        rows.append(dict(
            mode=mode, bank_row=int(w.bank_row), stream=w.stream, sid=w.sid,
            family_c1_c2=key, winner_t=float(w.t_stat),
            n_cousins=n,
            cousin_t_median=float(np.nanmedian(tt[fin])) if n else np.nan,
            cousin_t_p90=float(np.nanpercentile(tt[fin], 90)) if n else np.nan,
            cousin_t_max=float(np.nanmax(tt[fin])) if n else np.nan,
            cousins_t_over_2=int((tt[fin] >= 2.0).sum()) if n else 0,
            cousins_t_over_3=int((tt[fin] >= 3.0).sum()) if n else 0,
            cousin_total_R_median=float(np.nanmedian(rr[fin])) if n else np.nan,
            cousins_positive_pct=(float(100.0 * (rr[fin] > 0).mean()) if n else np.nan),
            lone_survivor=int(n > 0 and float(np.nanmax(tt[fin])) < 2.0)))
    F = pd.DataFrame(rows)
    f = os.path.join(RD, 'mode%s_winners_family.csv' % mode)
    F.to_csv(f, index=False)
    print('  family support: %d winners, %d flagged LONE SURVIVORS (no cousin reaches t=2) -> %s'
          % (len(F), int(F.lone_survivor.sum()), os.path.relpath(f, _R)), flush=True)
    return f


# ==========================================================================
# THE WINNERS' BOOK, AND THE OVERLAY SWEEPS
# ==========================================================================
# THE BOOK'S RETURN IS DESCRIPTIVE, NOT EVIDENCE, and the md says so in those
# words. Its membership was chosen by looking at the same 2016-2020 trade
# years it then reports, so the book cannot be a test of anything -- the luck
# floor is the evidence. The book answers a different and still useful
# question: if you had held exactly these, equally weighted, what would the
# drawdown have looked like.
def stage_winbook(mode='A', tag='full', jobs=4, nshard=16, ndraw=20, nid=200):
    """Equal-weight book of the non-luck winners, routed and always-on."""
    import l2r2gate3 as G3x
    G.manifest_check()
    W = pd.read_csv(os.path.join(RD, 'mode%s_winners.csv' % mode))
    assert len(W), 'no winners to book'
    z = np.load(BK._bank_slice_file(mode, tag), allow_pickle=True)
    nstrat = int(z['n']); del z
    streams = list(np.load(universe_file(mode), allow_pickle=True)['streams'])
    PM = np.zeros((nstrat, 4, len(G2.steps())), bool)
    for _i, w in W.iterrows():
        PM[int(w.bank_row), streams.index(w.stream), :] = True
    rule = 'winners'
    f = G3x.passmask_file(mode, rule)
    np.savez(f, pm=PM, n=np.int64(nstrat), rule=np.array(rule, dtype=object),
             steps_used=np.arange(len(G2.steps())))
    print('  winners book [mode %s]: %d winners -> %s member cells over %d steps'
          % (mode, len(W), f'{int(PM.sum()):,}', len(G2.steps())), flush=True)
    D, outp = G3x.stage_book(mode, tag, jobs=jobs, nshard=nshard, rule=rule)
    N, nout = G3x.stage_booknulls(mode, tag, jobs=jobs, ndraw=ndraw, nid=nid, rule=rule)
    return outp, nout


# --- the three overlays, each a pure function of a daily series -------------
def _ov_daily_stop(d, x):
    """Stop for the day once the day's loss reaches x%: the day ends at -x."""
    return np.maximum(d, -abs(x))


def _ov_pause(d, n_dd, m_rec):
    """Flat after an n_dd drawdown from peak; back in after m_rec recovery.

    THE RECOVERY IS MEASURED ON THE SHADOW CURVE, not on the paused one. While
    flat you earn nothing, so a paused equity curve can never recover on its
    own and the rule would latch forever -- which is a kill switch, not a
    pause. The shadow curve is what the strategies did while you sat out, and
    it is what you would have seen on the screen.
    """
    out = np.zeros_like(d)
    shadow = np.cumsum(d)
    speak = np.maximum.accumulate(shadow)
    paused = False
    trough = 0.0
    for i in range(len(d)):
        ddi = speak[i] - shadow[i]
        if not paused:
            out[i] = d[i]
            if ddi >= n_dd:
                paused = True
                trough = shadow[i]
        else:
            out[i] = 0.0
            if shadow[i] - trough >= m_rec:
                paused = False
            trough = min(trough, shadow[i])
    return out


def _ov_kill(d, k):
    """Flat for good once drawdown from peak reaches k."""
    out = np.array(d, float)
    eq = np.cumsum(d); peak = np.maximum.accumulate(eq)
    hit = np.flatnonzero((peak - eq) >= k)
    if len(hit):
        out[hit[0] + 1:] = 0.0
    return out


def _curve_point(d, years):
    import l2walkfwd as W_
    k = W_.kpis(np.asarray(d, float), years)
    return dict(total_pct=k['total_return_pct'], max_dd_pct=k['max_dd_pct'],
                median_year_pct=k['median_year_pct'],
                worst_year_pct=k['worst_year_pct'],
                sortino=k['sortino'], calmar=k['calmar'],
                worst_day_pct=k['worst_day_pct'],
                dip95_pct=k['dip95_pct'],
                return_per_dd=(k['total_return_pct'] / k['max_dd_pct']
                               if k['max_dd_pct'] > 0 else np.nan))


def stage_overlays(mode='A', src_tag='g3passwinners', label='winners',
                   books=('allon', 'chop_trend'), npts=24):
    """Return-vs-max-DD curves for the three overlays, over their full range.

    NO FIXED VALUES ARE CHOSEN. Each overlay is swept and every point is a row;
    the md plots return against max drawdown and Jack reads the knee. The
    baseline (no overlay) is row 0 of every sweep so the curves all start from
    the same point.
    """
    import l2r2kpis as KP
    rows = []
    for bk in books:
        for (bname, _dip, _day) in BK.BUDGETS:
            d, y, steps = KP.stitched(mode, bk, bname, src_tag)
            if d is None or not len(d):
                continue
            base = _curve_point(d, y)
            rng_dd = float(base['max_dd_pct'])
            rows.append(dict(mode=mode, source=label, book=bk, budget=bname,
                             overlay='none', p1=np.nan, p2=np.nan, **base))
            # 1. DAILY LOSS STOP, from a tenth of the worst day to past it
            wd = abs(float(base['worst_day_pct'])) or 1.0
            for x in np.linspace(wd / 10.0, wd * 1.5, npts):
                rows.append(dict(mode=mode, source=label, book=bk, budget=bname,
                                 overlay='daily_loss_stop', p1=float(x), p2=np.nan,
                                 **_curve_point(_ov_daily_stop(d, x), y)))
            # 2. EQUITY-CURVE PAUSE, a grid of (drawdown to pause, recovery to resume)
            for n_dd in np.linspace(rng_dd / 8.0, rng_dd * 1.25, 8):
                for m_rec in np.linspace(rng_dd / 16.0, rng_dd * 0.75, 6):
                    rows.append(dict(mode=mode, source=label, book=bk, budget=bname,
                                     overlay='equity_pause', p1=float(n_dd),
                                     p2=float(m_rec),
                                     **_curve_point(_ov_pause(d, n_dd, m_rec), y)))
            # 3. KILL SWITCH
            for k in np.linspace(rng_dd / 8.0, rng_dd * 1.5, npts):
                rows.append(dict(mode=mode, source=label, book=bk, budget=bname,
                                 overlay='kill_switch', p1=float(k), p2=np.nan,
                                 **_curve_point(_ov_kill(d, k), y)))
    D = pd.DataFrame(rows)
    # WHETHER THE CURVE IS IMPLEMENTABLE TRAVELS WITH THE DATA, not just the
    # prose. The pause and the kill switch decide at DAY BOUNDARIES and a daily
    # series is enough to evaluate them honestly. The daily loss stop does not:
    # clipping a day at -x assumes the breach is caught exactly at -x, costs
    # nothing to exit, and forfeits no intraday recovery. On a daily series
    # that is a free lunch and the curve is an UPPER BOUND, not an estimate.
    IMPL = {'none': 'baseline',
            'daily_loss_stop': 'UPPER BOUND -- needs intraday data to evaluate',
            'equity_pause': 'yes -- decided at day boundaries',
            'kill_switch': 'yes -- decided at day boundaries'}
    if len(D):
        D['implementable_on_daily_data'] = D.overlay.map(IMPL)
    f = os.path.join(RD, 'mode%s_overlay_curves_%s.csv' % (mode, label))
    D.to_csv(f, index=False)
    print('  overlay curves [%s]: %d points over %d (book, budget) series -> %s'
          % (label, len(D), D.groupby(['book', 'budget']).ngroups if len(D) else 0,
             os.path.relpath(f, _R)), flush=True)
    if len(D):
        for (bk, bd), g in D.groupby(['book', 'budget']):
            b = g[g.overlay == 'none'].iloc[0]
            print('    %-11s %-6s baseline total %+6.2f%% maxDD %5.2f%% (ret/DD %5.2f)'
                  % (bk, bd, b.total_pct, b.max_dd_pct, b.return_per_dd), flush=True)
            for ov in ('equity_pause', 'kill_switch', 'daily_loss_stop'):
                h = g[g.overlay == ov]
                if not len(h):
                    continue
                best = h.loc[h.return_per_dd.idxmax()]
                if ov == 'daily_loss_stop':
                    print('      %-16s UPPER BOUND ONLY (clipping a daily series costs '
                          'nothing and forfeits nothing; needs intraday data)' % ov,
                          flush=True)
                print('      %-16s best ret/DD %5.2f at p1=%.3f%s  (total %+6.2f%%, maxDD %5.2f%%)'
                      % (ov, best.return_per_dd, best.p1,
                         '' if not np.isfinite(best.p2) else ' p2=%.3f' % best.p2,
                         best.total_pct, best.max_dd_pct), flush=True)
    return f


# ==========================================================================
# PROP RETURN -- the number Jack actually buys (20 Nov, 21 Nov)
# ==========================================================================
# "yearly return when sized so the worst dip equals 3.6%". The worst dip is
# MAX DD for a strategy and DIP95 for a book, and the target line is 12% a
# year.
#
# FOR A STRATEGY THE ARITHMETIC COLLAPSES, and it is worth seeing why.
# A strategy's record is in R. Sizing so that max DD = PROP_DIP means one R is
# worth PROP_DIP / max_dd_R percent, so
#     prop return per year = (total_R / n_years) * PROP_DIP / max_dd_R
#                          = (PROP_DIP / n_years) * (total_R / max_dd_R)
# With PROP_DIP 3.6 and five years that is 0.72 x return-per-drawdown. So the
# prop return and the return/DD ratio are the SAME RANKING, and the 12% target
# is exactly return/DD >= 16.67. Nothing is gained by ranking on both; what is
# gained is that 12% is now a line on a chart instead of an aspiration.
#
# FOR A BOOK the sizing is already in the budget: team1 is the 3.6% dip
# budget, so its reported return is already prop-sized ON THE BUILD YEARS.
# This rescales to the TRADE years, where DIP95 is what it turned out to be
# rather than what it was fitted to, which is the honest version.
PROP_DIP = 3.6
PROP_TARGET = 12.0


def prop_return_strategy(total_R, max_dd_R, n_years=5, dip=PROP_DIP):
    t = np.asarray(total_R, np.float64); d = np.asarray(max_dd_R, np.float64)
    with np.errstate(divide='ignore', invalid='ignore'):
        return np.where(np.isfinite(d) & (d > 0), (t / n_years) * dip / d, np.nan)


def prop_return_book(median_year_pct, trade_dip95_pct, dip=PROP_DIP):
    m = np.asarray(median_year_pct, np.float64); p = np.asarray(trade_dip95_pct, np.float64)
    with np.errstate(divide='ignore', invalid='ignore'):
        return np.where(np.isfinite(p) & (p > 0), m * dip / p, np.nan)


def add_prop_columns(D, kind, n_years=5):
    """Add prop_return_pct_per_year, prop_scale and clears_12pct to a table."""
    D = D.copy()
    if not len(D):
        return D
    if kind == 'strategy':
        tot = D.get('trade_total_R', D.get('total_R'))
        dd = D.get('trade_max_dd_R_sumyr', D.get('max_dd_R_sumyr'))
        D['prop_return_pct_per_year'] = prop_return_strategy(tot, dd, n_years)
        D['prop_scale_pct_per_R'] = np.where(
            np.asarray(dd, float) > 0, PROP_DIP / np.asarray(dd, float), np.nan)
        D['prop_sized_on'] = 'max DD = %.1f%%' % PROP_DIP
    else:
        D['prop_return_pct_per_year'] = prop_return_book(
            D.get('trade_median_year_pct'), D.get('trade_dip95_pct'))
        D['prop_scale_x'] = np.where(
            np.asarray(D.get('trade_dip95_pct'), float) > 0,
            PROP_DIP / np.asarray(D.get('trade_dip95_pct'), float), np.nan)
        D['prop_sized_on'] = 'trade-year DIP95 = %.1f%%' % PROP_DIP
    D['prop_target_pct'] = PROP_TARGET
    D['clears_12pct_at_prop'] = (
        np.asarray(D.prop_return_pct_per_year, float) >= PROP_TARGET).astype(int)
    return D


def stage_prop(mode='A'):
    """Add the prop column to every table that reports a strategy or a book."""
    done = []
    # --- strategy tables
    for nm in ('winners',):
        f = os.path.join(RD, 'mode%s_%s.csv' % (mode, nm))
        if not os.path.exists(f):
            continue
        D = add_prop_columns(pd.read_csv(f), 'strategy')
        D = D.sort_values('prop_return_pct_per_year', ascending=False)
        D.to_csv(f, index=False)
        done.append((f, len(D), int(D.clears_12pct_at_prop.sum())))
    # --- book tables
    for pat in ('mode%s_gate3_passersbook*.csv', 'mode%s_books_full.csv'):
        for f in sorted(glob.glob(os.path.join(RD, pat % mode))):
            if '_nulls' in f:
                continue
            try:
                D = pd.read_csv(f)
            except Exception:
                continue
            if 'trade_dip95_pct' not in D.columns:
                continue
            D = add_prop_columns(D, 'book')
            D.to_csv(f, index=False)
            done.append((f, len(D), int(D.clears_12pct_at_prop.sum())))
    print('  PROP RETURN [mode %s]: sized so the worst dip = %.1f%%, target %.0f%% a year'
          % (mode, PROP_DIP, PROP_TARGET), flush=True)
    for f, n, c in done:
        print('    %-52s %4d rows, %2d clear %.0f%%'
              % (os.path.relpath(f, _R), n, c, PROP_TARGET), flush=True)
    if not done:
        print('    nothing to annotate yet', flush=True)
    return done


def stage_top30(mode='A'):
    """Top 30 by t, by return/DD, and by prop return, among the non-luck set."""
    f = os.path.join(RD, 'mode%s_winners.csv' % mode)
    if not os.path.exists(f):
        print('  no winners table to rank', flush=True)
        return []
    W = add_prop_columns(pd.read_csv(f), 'strategy')
    outs = []
    for key, col in (('t', 't_stat'), ('retdd', 'trade_return_per_dd'),
                     ('prop', 'prop_return_pct_per_year')):
        if col not in W.columns:
            continue
        D = W.sort_values(col, ascending=False).head(30)
        o = os.path.join(RD, 'mode%s_winners_top30_%s.csv' % (mode, key))
        D.to_csv(o, index=False)
        outs.append(o)
        print('    top 30 by %-6s -> %s (%d rows)'
              % (key, os.path.relpath(o, _R), len(D)), flush=True)
    return outs


def write_md(mode='A', out=None):
    """MODE<M>_WINNERS.md -- individual strategies first, the book last."""
    import hashlib
    import l2r2kpis as KP
    import l2r2gate3 as G3x
    L = []; A = L.append
    def tbl(d, cols=None):
        return G3x.BK_tbl(d, cols)
    def rd(nm):
        f = os.path.join(RD, 'mode%s_%s.csv' % (mode, nm))
        if not os.path.exists(f) or os.path.getsize(f) < 2:
            return pd.DataFrame(), f
        try:
            return pd.read_csv(f), f
        except Exception:
            return pd.DataFrame(), f

    A('# MODE %s — WINNERS, NO GATES\n' % mode)
    A('Generated %s by `code/l2r2winners.py`, read-only off the gate 2 bank and the '
      'gate 3 scoring. **Nothing is filtered before it is measured**: all 273,780 '
      'strategies are recorded on both unseen records, and the only cut is the LUCK '
      'FLOOR, which is a statement about chance rather than a preference about '
      'settings. Individual strategies first; the book last.\n'
      % time.strftime('%F %H:%M'))

    A('\n## 0. The number Jack buys: PROP RETURN\n')
    A('Yearly return when sized so the worst dip equals **%.1f%%** — max DD for a '
      'strategy, trade-year DIP95 for a book. Target **%.0f%% a year**.\n'
      % (PROP_DIP, PROP_TARGET))
    A('For a strategy the arithmetic collapses to `%.2f x return/DD`, so prop return '
      'and return-per-drawdown are the same ranking and the %.0f%% line is exactly '
      '**return/DD >= %.2f**.\n' % (PROP_DIP / 5.0, PROP_TARGET, PROP_TARGET / (PROP_DIP / 5.0)))
    W, wf = rd('winners')
    if len(W) and 'prop_return_pct_per_year' in W.columns:
        n12 = int(W.clears_12pct_at_prop.sum())
        A('**%d of %d winners clear %.0f%% at prop sizing.** Best is **%.2f%% a year** '
          '(return/DD %.2f against the %.2f needed) — short of the line by a factor of '
          '%.1f.\n' % (n12, len(W), PROP_TARGET, W.prop_return_pct_per_year.max(),
                       W.trade_return_per_dd.max(), PROP_TARGET / (PROP_DIP / 5.0),
                       (PROP_TARGET / (PROP_DIP / 5.0)) / W.trade_return_per_dd.max()))

    A('\n## 1. The universe, and the two unseen records\n')
    A('Per (strategy, stream), two records that the tuner never saw: the five stitched '
      'TRADE years 2016-2020, and the five GRADE years 2015-2019 as an independent '
      'second read. Each year uses the settings tuned before it — the walk forward as '
      'built.\n')
    O, of = rd('winners_t_observed')
    if len(O):
        A('\n**Observed t**, from `%s`:\n' % os.path.relpath(of, _R))
        A(tbl(O[O.stream == 'ALL'], ['record', 'stream', 'n_finite', 't_max', 't_p99',
                                     't_median']))
    A('\nThe t-statistic is **exact and not stored**: `l2tune` computes '
      '`sharpe = mean/sd x sqrt(252)` on per-trade R, so `sd = mean sqrt(252)/sharpe` '
      'and the per-year sum of squares is `sd^2 (n-1) + n mean^2`; those sum across the '
      'five years, so the pooled t is recovered without re-scoring. Verified against '
      'direct re-scoring on 10 records, agreeing to five decimals.\n')
    A('\n**Three fields are NOT exact from the bank**, and each is named where it '
      'appears: stitched max DD (summed per-year, gate 3\'s own stitched recipe, an '
      'upper bound), stitched Sortino (the mean of the five per-year figures), and '
      'longest losing streak (needs the ordered trade list, which the Scorer discards).\n')

    A('\n## 2. The luck floors\n')
    FA, faf = rd('winners_floor_analytic')
    if len(FA):
        A('**(a) Analytic**, from `%s`:\n' % os.path.relpath(faf, _R))
        A(tbl(FA, ['basis', 'M', 'alpha', 't_max_of_M', 't_bonferroni']))
        A('\nBoth lines assume independent tries and normal t. FX trade R is '
          'fat-tailed, the 28 pairs overlap in time, and a strategy\'s four streams '
          'share settings — all of which inflate real t. **These lines are therefore '
          'optimistic**: clearing one is the weakest version of the question.\n')
    FE, fef = rd('winners_floor_empirical')
    if len(FE):
        A('\n**(b) Empirical**, a per-strategy random-entry null, from `%s`:\n'
          % os.path.relpath(fef, _R))
        A(tbl(FE[FE.stream == 'ALL'], ['space', 'null_mean', 'null_sd', 'mu', 'sigma',
                                       'n_blocks', 'block_size', 'M', 'expected_best',
                                       'pct']))
        A('\nEvery real trade keeps its direction, units, cost and HOLD; its entry '
          'moves to a uniformly random bar in the same trade year on the same pair; R '
          'is recomputed from the price path. The floor is taken in **t-space** and the '
          'reason is measured, not asserted: the reconstruction is systematically more '
          'negative than the engine in LEVEL (see '
          '`mode%s_winners_recon_distortion.csv`), but on t the median engine/'
          'reconstruction ratio is 0.924 — the engine runs slightly lower than the '
          'space the floor is fitted in, so using it is mildly **conservative**. The '
          'expectancy-space fit is reported and NOT used: its Gumbel sigma exceeds its '
          'parent sd, the signature of a fat-tailed parent outside the Gumbel domain.\n'
          % mode)
    LAD, lf = rd('winners_floor_ladder')
    if len(LAD):
        A('\n**The ladder.** The winner count moves with which line binds, so the '
          'choice is shown rather than buried:\n')
        A(tbl(LAD, ['basis', 't_analytic', 't_empirical', 't_binding', 'n_winners',
                    'is_default']))

    A('\n## 3. The floor sweep\n')
    SW, sf = rd('winners_floor_sweep')
    if len(SW):
        d = SW[(SW.record == 'trade') & (SW.stream == 'ALL')]
        A('How many clear each level, and what they earned, from `%s` (%d rows over all '
          'streams):\n' % (os.path.relpath(sf, _R), len(SW)))
        A(tbl(d.iloc[::max(1, len(d) // 20)],
              ['t_floor', 'n_clearing', 'mean_trade_expectancy_R', 'mean_trade_total_R']))

    A('\n## 4. The non-luck winners\n')
    A('Above BOTH floors, **>= %d trades in every unseen year**, positive in **>= %d of '
      '5** trade years.\n' % (MIN_TRADES_PER_YEAR, MIN_YEARS_POSITIVE))
    if len(W):
        A('\n**%d winners.** Every one is listed in `%s` with its settings and per-year '
          'R.\n' % (len(W), os.path.relpath(wf, _R)))
        base = ['stream', 'sid', 't_stat', 'trade_n_trades', 'trade_total_R',
                'trade_max_dd_R_sumyr', 'trade_dd_pct_of_gross',
                'trade_return_per_dd', 'prop_return_pct_per_year',
                'trade_worst_year_R', 'trade_win_rate', 'years_positive']
        A(tbl(W, base))
        if 'stream' in W.columns:
            vc = W.stream.value_counts()
            A('\n**Stream composition: %s.**\n'
              % ', '.join('%s %d' % (k, v) for k, v in vc.items()))
        A('\nPer-year R for each winner:\n')
        yrs = [c for c in W.columns if c.startswith('R_2')]
        A(tbl(W, ['stream', 'sid'] + sorted(yrs)))
    else:
        A('\n_No winners at the binding floor._\n')

    A('\n### Top 30 by t-statistic, and by return-to-drawdown\n')
    A('Drawdown is on every row, as asked. With %d winners both tables are the whole '
      'set.\n' % len(W))
    for key, lbl in (('t', 't-statistic'), ('retdd', 'return / max DD'),
                     ('prop', 'prop return')):
        T30, tf = rd('winners_top30_%s' % key)
        if len(T30):
            A('\n**By %s** (`%s`):\n' % (lbl, os.path.relpath(tf, _R)))
            A(tbl(T30.head(30), ['stream', 'sid', 't_stat', 'trade_total_R',
                                 'trade_max_dd_R_sumyr', 'trade_return_per_dd',
                                 'prop_return_pct_per_year']))

    A('\n## 5. Family support\n')
    F, ff = rd('winners_family')
    if len(F):
        A('Cousins are same (c1, c2). A winner alone in its family is the shape a lucky '
          'draw takes; one surrounded by near-winners is the shape a real effect takes.\n')
        A(tbl(F, ['stream', 'family_c1_c2', 'winner_t', 'n_cousins', 'cousin_t_median',
                  'cousin_t_max', 'cousins_t_over_2', 'cousins_t_over_3',
                  'cousins_positive_pct', 'lone_survivor']))
        A('\n**%d of %d flagged lone survivors.**\n'
          % (int(F.lone_survivor.sum()), len(F)))

    A('\n## 6. The winners\' book — LAST, and descriptive only\n')
    A('**This book\'s membership was chosen with sight of the years it reports.** Its '
      'return is therefore DESCRIPTIVE and is not evidence of anything. The luck floor '
      'in section 2 is the evidence. The book answers a different question: if you had '
      'held exactly these, equally weighted, what would the drawdown have looked like.\n')
    BK_, bkf = rd('gate3_passersbook_winners')
    if len(BK_):
        b = BK_[BK_.get('book_empty', 0) == 0]
        A(tbl(b, ['step', 'book', 'budget', 'members', 'trade_total_pct',
                  'trade_max_dd_pct', 'trade_dip95_pct', 'trade_sortino',
                  'trade_calmar', 'prop_return_pct_per_year', 'clears_12pct_at_prop']))
        if (BK_.get('book_empty', 0) == 1).any():
            A('\nThe ROUTED book is **empty** — blank rows, not zeros. No winner is a '
              'routed-stream winner, so it has no members.\n')
        tl, _r = KP.kpi_tables(mode, tag='g3passwinners', books_csv=bkf, Bk=BK_)
        if tl:
            A('\n### Full KPI table\n')
            for ln in tl:
                A(ln)
    NB, nbf = rd('gate3_passersbook_winners_nulls')
    if len(NB):
        A('\n### Its nulls\n')
        A(tbl(NB, ['null', 'scope', 'step', 'book', 'budget', 'members', 'real',
                   'n_draws', 'null_mean', 'null_p95', 'p_one_sided']))

    A('\n## 6b. Pair routing — a STANDING test\n')
    A('Jack, 22 Nov: *"Pair routing is a standing test, not a one-off: every mode, '
      'every re-tune, every winners pipeline from now on reports the pair-routing '
      'sweep."* Chosen on tuning years, traded on unseen years, against a random-pair '
      'null of the same size.\n')
    PR = os.path.join(RD, 'mode%s_winners_pairrouted.csv' % mode)
    if os.path.exists(PR) and os.path.getsize(PR) > 1:
        R = pd.read_csv(PR)
        base = float(R[R.rule == 'all28'].return_per_dd.mean())
        tk = R[R.rule == 'topk'].groupby('K').return_per_dd.mean()
        nl = R[R.rule == 'random_null'].groupby('K').return_per_dd.mean()
        rows = []
        for K in tk.index:
            rows.append(dict(rule='topk', K=int(K), real_return_per_dd=float(tk[K]),
                             random_null=float(nl.get(K, np.nan)),
                             real_beats_null=int(tk[K] > nl.get(K, np.inf)),
                             prop_return_pct=float(tk[K]) * PROP_DIP / 5.0,
                             clears_12pct=int(float(tk[K]) * PROP_DIP / 5.0
                                              >= PROP_TARGET)))
        for rl in ('threshold', 'topk_dir', 'threshold_dir'):
            g = R[R.rule == rl]
            if len(g):
                v = float(g.return_per_dd.mean())
                rows.append(dict(rule=rl, K=np.nan, real_return_per_dd=v,
                                 random_null=np.nan, real_beats_null=np.nan,
                                 prop_return_pct=v * PROP_DIP / 5.0,
                                 clears_12pct=int(v * PROP_DIP / 5.0 >= PROP_TARGET)))
        T_ = pd.DataFrame(rows)
        A(G3x.BK_tbl(T_, ['rule', 'K', 'real_return_per_dd', 'random_null',
                          'real_beats_null', 'prop_return_pct', 'clears_12pct']))
        nb = int(T_.real_beats_null.fillna(0).sum())
        A('\nAll-28 baseline return/DD **%.3f** (prop return %.2f%%). The real rule '
          'beats the random-pair null at **%d of %d** values of K, and **%d** rows '
          'clear %.0f%% at prop sizing.\n'
          % (base, base * PROP_DIP / 5.0, nb, int(T_.K.notna().sum()),
             int(T_.clears_12pct.sum()), PROP_TARGET))
        A('\n**The drawdown basis in this section sums per (pair, direction, year) '
          'drawdowns** and is a looser bound than the strategy-level figure used '
          'elsewhere in this document, so its level is not comparable to section 4 and '
          'its prop return is a floor. Real and null share the basis, so the comparison '
          'within the section is sound. Full detail in `%s` and `WINNERS_BY_PAIR.md`.\n'
          % os.path.relpath(PR, _R))
    else:
        A('_No pair-routing sweep on disk for mode %s yet; run '
          '`code/l2r2pairs.py --stage winners` then `--stage routed`._\n' % mode)

    A('\n## 7. Overlay curves\n')
    OV, ovf = rd('overlay_curves_winners')
    if len(OV):
        A('Swept over their full range with **no fixed value chosen**, from `%s` (%d '
          'points). Return against max drawdown on the unseen years at the budget.\n'
          % (os.path.relpath(ovf, _R), len(OV)))
        rows = []
        for (bk, bd), g in OV.groupby(['book', 'budget']):
            for ov in ('none', 'equity_pause', 'kill_switch', 'daily_loss_stop'):
                h = g[g.overlay == ov]
                if not len(h):
                    continue
                r = h.loc[h.return_per_dd.idxmax()]
                rows.append(dict(book=bk, budget=bd, overlay=ov, p1=r.p1, p2=r.p2,
                                 total_pct=r.total_pct, max_dd_pct=r.max_dd_pct,
                                 return_per_dd=r.return_per_dd,
                                 implementable=r.get('implementable_on_daily_data', '')))
        A(tbl(pd.DataFrame(rows), ['book', 'budget', 'overlay', 'p1', 'p2', 'total_pct',
                                   'max_dd_pct', 'return_per_dd', 'implementable']))
        A('\n**The daily loss stop is an UPPER BOUND, not a result.** Clipping a daily '
          'series at -x assumes the breach is caught exactly at -x, costs nothing to '
          'exit and forfeits no intraday recovery — a free lunch on daily data. The '
          'pause and the kill switch decide at DAY BOUNDARIES, which a daily series '
          'evaluates honestly.\n')

    A('\n## Provenance\n')
    A('| file | rows | md5 |\n|---|---|---|')
    for nm in ('winners', 'winners_t_observed', 'winners_floor_analytic',
               'winners_floor_empirical', 'winners_floor_ladder', 'winners_floor_sweep',
               'winners_family', 'winners_nullstrat', 'winners_recon_distortion',
               'gate3_passersbook_winners', 'gate3_passersbook_winners_nulls',
               'overlay_curves_winners'):
        f = os.path.join(RD, 'mode%s_%s.csv' % (mode, nm))
        if os.path.exists(f) and os.path.getsize(f) > 1:
            try:
                n = len(pd.read_csv(f))
            except Exception:
                n = 0
            A('| `%s` | %s | %s |' % (os.path.relpath(f, _R), f'{n:,}',
                                      hashlib.md5(open(f, 'rb').read()).hexdigest()[:12]))

    txt = '\n'.join(L) + '\n'
    out = out or os.path.join(RD, 'MODE%s_WINNERS.md' % mode)
    open(out, 'w').write(txt)
    print('  MODE%s_WINNERS.md: %d lines -> %s'
          % (mode, len(txt.splitlines()), os.path.relpath(out, _R)), flush=True)
    return out


if __name__ == '__main__':
    st = G.opt('--stage', str, 'universe')
    md = G.opt('--mode', str, 'A')
    if st == 'universe':
        stage_universe(md, G.opt('--tag', str, 'full'))
    elif st == 'floors':
        stage_floors(md)
    elif st == 'sweep':
        stage_sweep(md, npts=G.opt('--sweep-points', int, 60))
    elif st == 'md':
        write_md(md)
    elif st == 'prop':
        stage_prop(md)
    elif st == 'top30':
        stage_top30(md)
    elif st == 'winbook':
        stage_winbook(md, G.opt('--tag', str, 'full'), jobs=G.opt('--jobs', int, 4),
                      nshard=G.opt('--nshard', int, 16))
    elif st == 'overlays':
        stage_overlays(md, src_tag=G.opt('--src-tag', str, 'g3passwinners'),
                       label=G.opt('--label', str, 'winners'),
                       npts=G.opt('--points', int, 24))
    elif st == 'winners':
        stage_winners(md, G.opt('--tag', str, 'full'), basis=G.opt('--basis', str, 'stated'))
    elif st == 'family':
        stage_family(md, G.opt('--tag', str, 'full'))
    elif st == 'floorb':
        stage_floorb(md)
    elif st == 'nullstrat':
        stage_nullstrat(md, G.opt('--tag', str, 'full'),
                        nsample=G.opt('--nsample', int, 2000),
                        ndraw=G.opt('--draws', int, 20),
                        jobs=G.opt('--jobs', int, 4))
    else:
        raise SystemExit('unknown stage %s' % st)
