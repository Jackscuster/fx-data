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


if __name__ == '__main__':
    st = G.opt('--stage', str, 'universe')
    md = G.opt('--mode', str, 'A')
    if st == 'universe':
        stage_universe(md, G.opt('--tag', str, 'full'))
    elif st == 'floors':
        stage_floors(md)
    elif st == 'sweep':
        stage_sweep(md, npts=G.opt('--sweep-points', int, 60))
    else:
        raise SystemExit('unknown stage %s' % st)
