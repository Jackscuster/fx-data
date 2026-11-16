import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""THE REGIME-SHUFFLE NULL AT GATE 1 (HANDOFF 0l, 16 Nov).

THE QUESTION, declared before the run. The honest gate 1 measures four streams
and both routed streams come out negative on the trade years. Before anything
is read into that, routing itself has to be null-tested: does routing on the
REAL Layer 1 label do anything a ROTATED label would not?

THE SURROGATE. Each pair's shape2 label series is rotated circularly by a
random offset. A rotation preserves the episode-length distribution and the
regime mix EXACTLY -- it only destroys the alignment between the label and the
price it was supposed to describe. A plain permutation would shred the episode
structure and would be a test of two things at once.

WHAT IS COMPARED, declared before the run. Not a cut value: the cut's own
distribution moves under the surrogate, so comparing at a fixed cut would
compare two different selection sizes. Instead, at a fixed SELECTION SIZE --
the top q% of eligible combinations by pooled tune-year expectancy, for
q in 0.1, 1, 10 and 50 -- the trade-year expectancy of that selection, on the
real label against 200 rotated draws.

THE CONTROL. The always-on streams are computed on every draw too. They do not
read the label at all, so they MUST come out identical on every draw. If they
move, the harness is wrong and the routed result means nothing.

    python3 code/l2r2null.py --mode A --n 10000 --draws 200
"""
import time, json
import numpy as np, pandas as pd
from numba import njit
import l2sweep as S
import l2r2gate1 as G

QS = (0.1, 1.0, 10.0, 50.0)       # DECLARED selection sizes, per cent
NSTAT = G.NSTAT


@njit(cache=False)
def _acc_draws(r, eb, nt, ybar, reg, code, off, nbar, wt, acc, s_routed, s_allon):
    """Per-draw accumulation for one pair, one plan.

    acc is (ndraw, 2, 3, NSTAT): draw, stream (routed / always-on),
    role (tune, grade, trade), stat. `wt` is (3, NYEAR) -- the tune row carries
    the pooled tune weight of each year (a year in two tune windows counts
    twice), the grade and trade rows are 0/1 masks. Draw 0 is the REAL label,
    offset 0, so the real reading and the surrogates come out of one pass.
    """
    nd = off.shape[0]
    for i in range(nt):
        b = eb[i]
        y = ybar[b]
        if y < 0:
            continue
        v = r[i]
        gain = v if v > 0.0 else 0.0
        loss = -v if v <= 0.0 else 0.0
        win = 1.0 if v > 0.0 else 0.0
        for d in range(nd):
            bb = b + off[d]
            if bb >= nbar:
                bb -= nbar
            rt = reg[bb] == code
            for k in range(2):
                if k == 0 and not rt:
                    continue
                for ro in range(3):
                    w = wt[ro, y]
                    if w == 0.0:
                        continue
                    acc[d, k, ro, 0] += w
                    acc[d, k, ro, 1] += w * v
                    acc[d, k, ro, 2] += w * gain
                    acc[d, k, ro, 3] += w * loss
                    acc[d, k, ro, 4] += w * win


def role_weights(wins):
    """(3, NYEAR): pooled tune weight per year, then the grade and trade masks."""
    w = np.zeros((3, G.NYEAR), np.float64)
    for win in wins:
        for y in range(win['tune'][0], win['tune'][1] + 1):
            if G.YEAR0 <= y < G.YEAR0 + G.NYEAR:
                w[0, y - G.YEAR0] += 1.0
        for ro, key in ((1, 'grade'), (2, 'trade')):
            for y in range(win[key][0], win[key][1] + 1):
                if G.YEAR0 <= y < G.YEAR0 + G.NYEAR:
                    w[ro, y - G.YEAR0] = 1.0
    return w


def offsets(pairs, ndraw, seed=20261116):
    """One rotation per (pair, draw). Draw 0 is offset 0 everywhere -- the real
    label -- so nothing has to be measured twice."""
    rng = np.random.default_rng(seed)
    out = {}
    for p in pairs:
        o = rng.integers(200, 4000, size=ndraw)     # never a near-zero rotation
        o[0] = 0
        out[p] = o.astype(np.int64)
    return out


def _worker(args):
    shard, nshard, mode, combos, ndraw, outdir = args
    f = os.path.join(outdir, 'shuf_%04d.npz' % shard)
    if os.path.exists(f):
        return dict(shard=shard, n=0, skipped=True)
    S.load_costs()
    opts = S.mode_opts(S.slot_options(), mode)
    kwm = S.mode_kw(mode)
    PD, BUF = G.build_pairdata(opts)
    wt = role_weights(G.windows())
    off = offsets(sorted(PD), ndraw)
    mine = [cb for i, cb in enumerate(combos) if i % nshard == shard]
    # per combination: (ndraw, slice, stream, role, stat).  slice 0 trend, 1 chop
    out = np.zeros((len(mine), ndraw, 2, 2, 3, NSTAT), np.float32)
    t0 = time.time()
    for j, cb in enumerate(mine):
        c1, c2, vol, base, ex = cb
        for sl, (sname, plan, code) in enumerate(S.SLICES):
            acc = np.zeros((ndraw, 2, 3, NSTAT), np.float64)
            for pair, P in PD.items():
                buf = BUF[pair]
                nt = S.run_combo(P, c1, c2, vol, base, ex, buf, plan=plan, **kwm)
                if nt == 0:
                    continue
                r = buf['r'][:nt].copy()
                eb = buf['entry_bar'][:nt]
                if S.COSTS and P['_cfrac']:
                    r = r - (float(kwm.get('atr_mult', S.ATR_MULT)) * P['_cfrac']
                             * P['_cmult'][eb] * np.abs(buf['entry_px'][:nt])
                             * np.abs(buf['units'][:nt]) / S.RISK)
                _acc_draws(r, eb, nt, P['_yb'], P['regime'], code, off[pair],
                           len(P['regime']), wt, acc, 0, 1)
            out[j, :, sl] = acc
        if (j + 1) % 200 == 0:
            el = time.time() - t0
            print('    shuffle shard %02d: %5d/%5d  %.0f ms/combo  %.0f min left'
                  % (shard, j + 1, len(mine), 1000 * el / (j + 1),
                     (el / (j + 1)) * (len(mine) - j - 1) / 60), flush=True)
    np.savez_compressed(f, acc=out, idx=np.array([i for i, _ in enumerate(combos) if i % nshard == shard]))
    return dict(shard=shard, n=len(mine), skipped=False, seconds=time.time() - t0)


def report(mode, outdir, ndraw, out=None):
    import glob
    fs = sorted(glob.glob(os.path.join(outdir, 'shuf_*.npz')))
    A, ix = [], []
    for f in fs:
        z = np.load(f)
        A.append(z['acc']); ix.append(z['idx'])
    A = np.concatenate(A).astype(np.float64); ix = np.concatenate(ix)
    A = A[np.argsort(ix)]
    # A: (ncombo, ndraw, slice, stream, role, stat)
    n = A[..., 0]; tot = A[..., 1]
    with np.errstate(divide='ignore', invalid='ignore'):
        e = np.where(n > 0, tot / np.maximum(n, 1), np.nan)
    rows = []
    for sl, sname in enumerate(('trend', 'chop')):
        for st, stream in enumerate(('routed', 'always-on')):
            tu_e = e[:, :, sl, st, 0]; tu_n = n[:, :, sl, st, 0]
            tr_e = e[:, :, sl, st, 2]; tr_n = n[:, :, sl, st, 2]
            elig = tu_n >= G.MIN_TUNE_TRADES * len(G.windows())
            for q in QS:
                vals = np.full(ndraw, np.nan)
                for d in range(ndraw):
                    m = elig[:, d] & np.isfinite(tu_e[:, d])
                    if m.sum() < 10:
                        continue
                    k = max(1, int(round(m.sum() * q / 100.0)))
                    idx = np.flatnonzero(m)
                    pick = idx[np.argsort(-tu_e[idx, d])[:k]]
                    g = np.isfinite(tr_e[pick, d]) & (tr_n[pick, d] > 0)
                    if g.any():
                        vals[d] = np.average(tr_e[pick[g], d], weights=tr_n[pick[g], d])
                real = vals[0]; sur = vals[1:]
                sur = sur[np.isfinite(sur)]
                rows.append(dict(
                    mode=mode, slice=sname, stream=stream, top_pct=q,
                    n_eligible_real=int(elig[:, 0].sum()),
                    n_selected=int(max(1, round(elig[:, 0].sum() * q / 100.0))),
                    real_trade_R=float(real), n_surrogates=int(len(sur)),
                    surrogate_mean=float(sur.mean()) if len(sur) else np.nan,
                    surrogate_p5=float(np.percentile(sur, 5)) if len(sur) else np.nan,
                    surrogate_p95=float(np.percentile(sur, 95)) if len(sur) else np.nan,
                    p_one_sided=float((sur >= real).mean()) if len(sur) else np.nan,
                    surrogate_spread=float(sur.max() - sur.min()) if len(sur) else np.nan))
    D = pd.DataFrame(rows)
    out = out or os.path.join(ROOTOUT, 'r2gate1_shufflenull_mode%s.csv' % mode)
    D.to_csv(out, index=False)
    print('  regime-shuffle null -> %s' % os.path.basename(out), flush=True)
    for _, r in D.iterrows():
        flag = ''
        if r.stream == 'always-on':
            flag = '   <- CONTROL, must not move' + (' : SPREAD %.2g !!' % r.surrogate_spread
                                                     if r.surrogate_spread > 1e-9 else ' : flat, ok')
        print('    %-5s %-9s top %5.1f%%  real %+.4f   surrogate %+.4f [%+.4f, %+.4f]  p=%.3f%s'
              % (r.slice, r.stream, r.top_pct, r.real_trade_R, r.surrogate_mean,
                 r.surrogate_p5, r.surrogate_p95, r.p_one_sided, flag), flush=True)
    return D


def main():
    import multiprocessing as mp
    mode = G.opt('--mode', str, 'A')
    nc = G.opt('--n', int, 10000)
    ndraw = G.opt('--draws', int, 200)
    jobs = G.opt('--jobs', int, 8)
    G.manifest_check()
    S.load_costs()
    opts = S.mode_opts(S.slot_options(), mode)
    combos = G.stratified(opts, nc)
    outdir = os.path.join(ROOTOUT, 'r2gate1', 'mode%s_shuffle' % mode)
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, 'spec.json'), 'w') as fh:
        json.dump(dict(mode=mode, n=len(combos), draws=ndraw, top_pct=list(QS),
                       surrogate='circular rotation of each pair shape2 series, 200-4000 bars',
                       note='draw 0 is the real label', stamp=time.strftime('%F %T')), fh, indent=1)
    print('  regime-shuffle null: %d stratified mode %s combinations x %d draws (draw 0 = real label)'
          % (len(combos), mode, ndraw), flush=True)
    args = [(k, jobs, mode, combos, ndraw, outdir) for k in range(jobs)]
    t0 = time.time()
    with mp.Pool(jobs) as pool:
        res = pool.map(_worker, args)
    print('  %d combinations x %d draws in %.1f min (%d shards skipped as present)'
          % (sum(r['n'] for r in res), ndraw, (time.time() - t0) / 60,
             sum(r['skipped'] for r in res)), flush=True)
    report(mode, outdir, ndraw)
    print('SHUFFLE NULL COMPLETE', flush=True)


if __name__ == '__main__':
    main()
