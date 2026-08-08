import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""How large an effect size does our SELECTION PROCEDURE manufacture from noise?

Every measured effect = true effect + sampling noise. Taking the top performers
out of 167,316 preferentially takes the ones whose noise ran positive, so every
effect size we report is biased upward. This measures that bias directly.

NOT the shuffled-label test in validate.py. That asks whether the composite beats
noise. This asks how much effect the selection procedure invents FROM noise.

THE NULL — circular time shift of the target panel
  offset drawn uniformly from [1000, T-1000]
  the ENTIRE panel rotated by the SAME offset, wrapping around
  signal values untouched

  Minimum 1000 because signals in the library read windows up to 1000 bars
  (duocc_pl_1000, _rsum(b,1000), hz750, oc750). A 250-bar shift would leave a
  slow signal still overlapping the outcomes it was genuinely related to, which
  leaves real signal in the null and UNDERSTATES inflation.

  Same offset for every pair because that preserves cross-pair target
  correlation. Panel-wide signals -- z_panelvol_40 is near-identical across the
  28 -- earn pair agreement by construction, and the null has to reproduce that
  or it understates inflation on exactly the family that dominates our survivors.

  Target autocorrelation and cross-pair correlation are preserved exactly; only
  signal-to-outcome alignment is destroyed. True effect is zero by construction.

WHAT IS NOT CHANGED. The gauntlet, its seven gates and its thresholds are
untouched. The one implementation change is that each column's sort order is
computed once per pair and reused across all 50 offsets -- the sort order does
not depend on the target, so quintile statistics come out identical. That is a
cost optimisation, not a change to the selection procedure.

Writes results/inflation_runs.csv (per-run order statistics) and
results/inflation_adjusted.csv (rank-matched corrections).
"""
import json, time
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
SIG = os.path.join(ROOTOUT, 'signals.json')
SPLIT = pd.Timestamp('2016-01-01')
H = 20
NRUN = 50
MINOFF = 1000
RANKS = [1, 2, 3, 5, 10, 32]
CH = 1000                       # base columns per block
SEED = 7
BATCH = [('own-price', 'sig2'), ('cross-sectional', 'sig3'),
         ('multi-timeframe', 'sig4'), ('regime-v5', 'sig5'),
         ('trend-duration', 'sig6'), ('trend-nonmomentum', 'sig7')]


def fwd_eff(s, h=H):
    p = np.log(s.astype(float)); r = p.diff()
    return ((p.shift(-h) - p).abs() / r.abs().shift(-h).rolling(h).sum()
            ).replace([np.inf, -np.inf], np.nan).values.astype(np.float64)


def frame_for(mod, m, px, pair, ctx):
    if mod == 'sig2':
        return m.build(px[pair])
    if mod == 'sig5':
        return m.build(px, pair, ctx, exclude=frozenset())
    if mod in ('sig6', 'sig7'):
        return m.base_frame(px, pair, ctx)
    return m.build(px, pair, ctx)


class Acc:
    """Pooled sufficient statistics per offset, per mask, for every signal."""

    def __init__(self, K, nrun, npair):
        sh = (nrun, K, 5)
        self.N = np.zeros(sh, np.float32); self.S = np.zeros(sh, np.float32)
        self.SS = np.zeros(sh, np.float32)
        self.CT = np.zeros((nrun, K), np.float32)
        self.SGN = np.zeros((nrun, K, npair), np.int8)   # per-pair spread sign

    def add(self, run, cols, q, n, v, pi):
        ok = np.isfinite(q).all(1) & np.isfinite(v).all(1)
        c2 = np.where(ok[:, None], n, 0)
        q2 = np.nan_to_num(q); v2 = np.nan_to_num(v)
        self.N[run, cols] += c2
        self.S[run, cols] += c2 * q2
        self.SS[run, cols] += (c2 - 1) * v2 + c2 * q2 * q2
        self.CT[run, cols] += ok
        self.SGN[run, cols, pi] = np.where(ok, np.sign(q[:, 4] - q[:, 0]), 0).astype(np.int8)

    def stats(self, run):
        N = self.N[run].astype(np.float64); S = self.S[run].astype(np.float64)
        SS = self.SS[run].astype(np.float64)
        M = np.where(N > 0, S / np.maximum(N, 1), np.nan)
        V = np.where(N > 1, (SS - N * M * M) / np.maximum(N - 1, 1), np.nan)
        spread = M[:, 4] - M[:, 0]
        se = np.sqrt(V[:, 4] / np.maximum(N[:, 4], 1) + V[:, 0] / np.maximum(N[:, 0], 1))
        rk = np.arange(5) - 2
        with np.errstate(invalid='ignore'):
            mono = np.array([np.corrcoef(rk, M[j])[0, 1] if np.isfinite(M[j]).all() else np.nan
                             for j in range(M.shape[0])])
            sg = self.SGN[run]
            agree = np.nansum(sg == np.sign(spread)[:, None], 1) / np.maximum((sg != 0).sum(1), 1)
        return spread, spread / se, mono, agree, self.CT[run]


def quintiles(ys, nvalid):
    """Per-column quintiles with PER-COLUMN edges.

    Columns in a block have different numbers of valid rows. An earlier version
    truncated every column to the shortest one, which computed 'quintiles' over
    the bottom sixth of most columns' range and produced meaningless spreads.
    Edges are now placed at q*n_j/5 for each column j independently, and the
    sums are taken from cumulative sums so it stays vectorised.

    ys is already sorted ascending by signal value, invalid rows last.
    """
    Tn, K = ys.shape
    # float32 throughout: the float64 version was memory-bandwidth bound and ran
    # 4x slower for no accuracy that matters at these magnitudes.
    fin = np.isfinite(ys)
    z = np.where(fin, ys, np.float32(0)).astype(np.float32)
    Z1 = np.zeros((1, K), np.float32)
    CS = np.concatenate([Z1, np.cumsum(z, 0, dtype=np.float32)])
    CS2 = np.concatenate([Z1, np.cumsum(z * z, 0, dtype=np.float32)])
    # count of rows valid in BOTH signal and target, so a NaN target is excluded
    # from the bin it falls in -- matching the real scorer's ym & isfinite(y).
    CV = np.concatenate([Z1, np.cumsum(fin, 0, dtype=np.float32)])
    e = (np.arange(6)[:, None] * nvalid[None, :] // 5).astype(np.intp)
    lo, hi = e[:-1], e[1:]
    n = (np.take_along_axis(CV, hi, 0) - np.take_along_axis(CV, lo, 0)).astype(np.float64)
    s1 = (np.take_along_axis(CS, hi, 0) - np.take_along_axis(CS, lo, 0)).astype(np.float64)
    s2 = (np.take_along_axis(CS2, hi, 0) - np.take_along_axis(CS2, lo, 0)).astype(np.float64)
    with np.errstate(invalid='ignore', divide='ignore'):
        q = s1 / n
        v = (s2 - n * q * q) / np.maximum(n - 1, 1)
    q = np.where(n > 0, q, np.nan)
    v = np.where(n > 1, v, np.nan)
    return (q.T.astype(np.float32), n.T.astype(np.float32), v.T.astype(np.float32))


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    T = len(px)
    names = [d['s'] for d in json.load(open(SIG))]
    gidx = {n: i for i, n in enumerate(names)}
    K = len(names)
    rng = np.random.default_rng(SEED)
    offs = rng.integers(MINOFF, T - MINOFF, NRUN)
    print('null: %d circular shifts, offsets %d..%d of %d bars'
          % (NRUN, offs.min(), offs.max(), T), flush=True)

    ins = np.asarray(px.index < SPLIT)
    MASKS = [('i', ins), ('o', ~ins)]
    A = {t: Acc(K, NRUN, len(px.columns)) for t, _ in MASKS}

    # rotated targets, same offset for every pair
    Y = {p: fwd_eff(px[p]) for p in px.columns}
    ROT = {p: np.stack([np.roll(Y[p], int(o)) for o in offs]) for p in px.columns}

    # Checkpoint after every pair. The argsort itself cannot be persisted -- it is
    # 4.9 GB per pair, 137 GB across 28, against 22 GB free -- but it is not what a
    # kill costs. What costs hours is the accumulators, and they are 1.6 GB. With
    # this, an interrupted run resumes at the next pair instead of from zero.
    CKPT = os.path.join(ROOTOUT, '_infl_ckpt.npz')
    done = set()
    if os.path.exists(CKPT):
        z = np.load(CKPT, allow_pickle=True)
        if int(z['nrun']) == NRUN and str(z['seed']) == str(SEED):
            for t in ('i', 'o'):
                A[t].N = z['N_' + t]; A[t].S = z['S_' + t]; A[t].SS = z['SS_' + t]
                A[t].CT = z['CT_' + t]; A[t].SGN = z['SGN_' + t]
            done = set(str(x) for x in z['done'])
            print('resuming: %d pairs already accumulated' % len(done), flush=True)

    for pi, pair in enumerate(px.columns):
        if pair in done:
            continue
        t0 = time.time()
        for label, mod in BATCH:
            m = __import__(mod)
            ctx = getattr(m, '_ctx_cache', None)
            if ctx is None and hasattr(m, 'context'):
                ctx = m.context(px); m._ctx_cache = ctx
            F = frame_for(mod, m, px, pair, ctx)
            cols = list(F.columns)
            for b in range(0, len(cols), CH):
                cb = cols[b:b + CH]
                S = (m.expand(F[cb]) if hasattr(m, 'expand') else F[cb]).shift(1)
                nm = [c for c in S.columns if c in gidx]
                if not nm:
                    continue
                gi = np.array([gidx[c] for c in nm])
                X = S[nm].values.astype(np.float32)
                for tag, msk in MASKS:
                    Xm = X[msk]
                    fin = np.isfinite(Xm)
                    # columns with too little data or no variation cannot be scored
                    good = (fin.sum(0) >= 400) & (np.nanmax(Xm, 0) > np.nanmin(Xm, 0))
                    if not good.any():
                        continue
                    nvalid = fin[:, good].sum(0)
                    keep2 = nvalid >= 400
                    if not keep2.any():
                        continue
                    Xg = np.where(fin, Xm, np.inf)[:, good][:, keep2]
                    order = np.argsort(Xg, axis=0, kind='stable')   # NaN sorts last
                    nv = nvalid[keep2].astype(np.intp)
                    gcols = gi[good][keep2]
                    for r in range(NRUN):
                        yr = ROT[pair][r][msk]
                        # positions beyond a column's valid count are never read --
                        # every edge satisfies hi <= nv -- so no masking pass is needed
                        ys = yr[order]
                        q, n, v = quintiles(ys, nv)
                        A[tag].add(r, gcols, q, n, v, pi)
                    del Xg, order
                del S, X
            del F
        done.add(pair)
        np.savez(CKPT, nrun=NRUN, seed=SEED, done=np.array(sorted(done)),
                 **{'%s_%s' % (k, t): getattr(A[t], k)
                    for t in ('i', 'o') for k in ('N', 'S', 'SS', 'CT', 'SGN')})
        print('  %-7s %.0fs  [%d/28 checkpointed]'
              % (pair, time.time() - t0, len(done)), flush=True)

    np.save(os.path.join(ROOTOUT, '_infl_offsets.npy'), offs)
    for tag in ('i', 'o'):
        np.savez_compressed(os.path.join(ROOTOUT, '_infl_%s.npz' % tag),
                            N=A[tag].N, S=A[tag].S, SS=A[tag].SS,
                            CT=A[tag].CT, SGN=A[tag].SGN)
    print('accumulators written', flush=True)

    rows = []
    for r in range(NRUN):
        si, ti, mi, ai, cti = A['i'].stats(r)
        so, to, mo, ao, cto = A['o'].stats(r)
        ok = (cti >= 20) & (cto >= 20) & np.isfinite(ti) & np.isfinite(to)
        with np.errstate(invalid='ignore', divide='ignore'):
            dec = np.abs(to) / np.maximum(np.abs(ti), .01)
        sel = ok & (np.sign(ti) == np.sign(to)) & (np.abs(to) >= 8) & (np.abs(si) >= .02) \
            & (ao >= .85) & (np.abs(mo) >= .95) & (dec >= .6)
        eff = np.abs(so[sel])
        eff = np.sort(eff)[::-1]
        rec = dict(run=r, offset=int(offs[r]), n_survivors=int(sel.sum()))
        for k in RANKS:
            rec['eff_rank%d' % k] = float(eff[k - 1]) if len(eff) >= k else np.nan
        rows.append(rec)
        print('  run %2d offset %5d survivors %4d  best %.4f'
              % (r, offs[r], sel.sum(), eff[0] if len(eff) else np.nan), flush=True)
        np.save(os.path.join(ROOTOUT, '_infl_sel_%02d.npy' % r), np.flatnonzero(sel))
    D = pd.DataFrame(rows)
    D.to_csv(os.path.join(ROOTOUT, 'inflation_runs.csv'), index=False)
    print('\nwrote inflation_runs.csv')
    return D


# ---------------------------------------------------------------- adjustment

def real_survivors():
    """The live gauntlet's output, recomputed here so the two are provably the
    same arithmetic. Gates 1-7, matching dedup.gates()."""
    D = pd.DataFrame(json.load(open(SIG)))
    d = D[D.ok.fillna(True)]
    with np.errstate(invalid='ignore', divide='ignore'):
        dec = d.to.abs() / d.ti.abs().clip(lower=.01)
    return d[(np.sign(d.ti) == np.sign(d.to)) & (d.to.abs() >= 8) & (d.si.abs() >= .02)
             & (d.ao >= .85) & (d.mo.abs() >= .95) & (dec >= .6)
             & (d.tsb.isna() | (d.tsb >= 4))].copy()


def adjust(D=None):
    """Rank-matched correction: real effect at rank k minus what the same
    procedure manufactures at rank k from a target with no signal in it.

    TWO DIFFERENT NULLS, and conflating them is the easy mistake here.

      the CORRECTION uses the conditional median -- the median over only those
      runs that actually produced a k-th survivor. When the null yields nothing
      at rank k there is no k-th effect to have reported, so that run cannot
      contribute a zero to a "what would we have reported" average.

      the P-VALUE uses the unconditional distribution over all NRUN runs. A run
      that produced no k-th survivor genuinely failed to exceed us, so it counts
      as a non-exceedance rather than being dropped.

    Conditional medians thin out fast -- by rank 10 only a handful of runs reach
    -- so n_runs_reaching is carried in the output and the correction should not
    be read below the ranks where it is comfortably populated.
    """
    if D is None:
        D = pd.read_csv(os.path.join(ROOTOUT, 'inflation_runs.csv'))
    S = json.load(open(SIG))
    R = real_survivors()
    eff = np.sort(R.so.abs().values)[::-1]
    n = len(D)

    rows = []
    for k in RANKS:
        c = D['eff_rank%d' % k]
        nreach = int(c.notna().sum())
        cond = float(c.median()) if nreach else np.nan
        uncond = c.fillna(0.).values
        re = float(eff[k - 1]) if len(eff) >= k else np.nan
        # +1 in both terms: with 50 draws a zero count is not evidence of p=0
        p = (1 + int((uncond >= re).sum())) / (n + 1) if np.isfinite(re) else np.nan
        rows.append(dict(
            rank=k, real_eff=re, n_runs_reaching=nreach,
            null_med_fired=cond, null_med=float(np.median(uncond)),
            null_p90=float(np.quantile(uncond, .9)), null_max=float(uncond.max()),
            # both left blank where the null never reached rank k: there is no
            # correction to apply, not a correction of zero
            adjusted=re - cond if np.isfinite(cond) else np.nan,
            manufactured_pct=100 * cond / re if np.isfinite(cond) and re else np.nan,
            p_emp=p))
    A = pd.DataFrame(rows)
    A.to_csv(os.path.join(ROOTOUT, 'inflation_adjusted.csv'), index=False)

    ns = D.n_survivors.values
    csum = [dict(metric='n_survivors', real=float(len(R)), null_mean=float(ns.mean()),
                 null_med=float(np.median(ns)), null_p90=float(np.quantile(ns, .9)),
                 null_max=float(ns.max()),
                 p_emp=(1 + int((ns >= len(R)).sum())) / (n + 1)),
            dict(metric='best_effect', real=float(eff[0]),
                 null_mean=float(np.nanmean(D.eff_rank1)),
                 null_med=float(A.null_med_fired.iloc[0]),
                 null_p90=float(A.null_p90.iloc[0]), null_max=float(A.null_max.iloc[0]),
                 p_emp=float(A.p_emp.iloc[0])),
            dict(metric='runs_empty', real=0., null_mean=float((ns == 0).mean()),
                 null_med=np.nan, null_p90=np.nan, null_max=float((ns == 0).sum()),
                 p_emp=np.nan)]
    C = pd.DataFrame(csum)
    C.to_csv(os.path.join(ROOTOUT, 'inflation_summary.csv'), index=False)

    # Which families does the null preferentially manufacture? If noise favours
    # the same families our survivors come from, the mix is not evidence of
    # anything; if it favours different ones, the mix is doing real work.
    fam = [d['b'] for d in S]
    nullf = {}
    for r in range(n):
        f = os.path.join(ROOTOUT, '_infl_sel_%02d.npy' % r)
        if not os.path.exists(f):
            continue
        for i in np.load(f):
            nullf[fam[i]] = nullf.get(fam[i], 0) + 1
    realf = R.b.value_counts().to_dict()
    allf = sorted(set(fam))
    tn, tr, tb = max(sum(nullf.values()), 1), max(len(R), 1), max(len(fam), 1)
    F = pd.DataFrame([dict(family=x, n_built=sum(1 for y in fam if y == x),
                           built_share=100. * sum(1 for y in fam if y == x) / tb,
                           real_survivors=int(realf.get(x, 0)),
                           real_share=100. * realf.get(x, 0) / tr,
                           null_survivors=int(nullf.get(x, 0)),
                           null_share=100. * nullf.get(x, 0) / tn) for x in allf])
    F.to_csv(os.path.join(ROOTOUT, 'inflation_families.csv'), index=False)

    print('\nSELECTION INFLATION  (%d null runs, %d real survivors)' % (n, len(R)))
    print('%-5s %9s %9s %9s %9s %7s %6s'
          % ('rank', 'real', 'null*', 'adjusted', 'manuf%', 'p', 'runs*'))
    for _, r in A.iterrows():
        print('%-5d %9.4f %9s %9s %8s%% %7.3f %6d'
              % (r['rank'], r.real_eff,
                 '%.4f' % r.null_med_fired if np.isfinite(r.null_med_fired) else '  --  ',
                 '%.4f' % r.adjusted if np.isfinite(r.adjusted) else '  --  ',
                 '%.0f' % r.manufactured_pct if np.isfinite(r.manufactured_pct) else ' --',
                 r.p_emp, r.n_runs_reaching))
    print('* conditional on the null producing a survivor at that rank')
    print('\nsurvivor count: real %d, null median %.0f, max %d, p=%.3f'
          % (len(R), np.median(ns), ns.max(), csum[0]['p_emp']))
    print('wrote inflation_adjusted.csv, inflation_summary.csv, inflation_families.csv')
    return A


if __name__ == '__main__':
    # The sweep is resumable and its checkpoint holds all 28 pairs once complete,
    # so a rerun is cheap -- but on a cold machine it is hours. --adjust-only
    # recomputes the correction from the committed inflation_runs.csv.
    if '--adjust-only' in sys.argv:
        adjust()
    else:
        adjust(main())
