import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""TASK 1 — rerun the gauntlet with NO out-of-sample information anywhere.

THE HOLE. Six of the seven gates read 2016-2026: sign-holds, |t|, agreement,
monotonicity, decay and 2 of the 6 stability blocks. Only the effect-size gate is
in-sample. So the CHOICE of which 32 signals to combine already knows the answer.
The refit test proved the composite is stable once built; it never proved the
ingredient list was chosen cleanly.

THE FIX. Split the in-sample period in two and run the identical gauntlet inside
it, so every gate has a train half and a validate half and the holdout is never
touched:

    IS-A  1999-01-04 .. 2007-12-31   train
    IS-B  2008-01-01 .. 2015-12-31   validate
    OOS   2016-01-01 .. present      NEVER READ during selection

    gate 1  sign holds      sign(t_A) == sign(t_B)
    gate 2  |t| >= 8        |t_B|
    gate 3  effect >= .020  |spread_A|
    gate 4  agree >= .85    agreement_B
    gate 5  mono >= .95     |mono_B|
    gate 6  decay >= .60    |t_B| / |t_A|
    gate 7  stable 4 of 6   six blocks spanning 1999-2015 ONLY

Only after the set is fixed is OOS opened, once, to report what it actually did.

Every signal in the library is rescored -- 175,634 of them -- because filtering
the candidate list by anything already computed would reimport the leak.

Writes results/isonly_stats.csv. The per-pair .npz go to results/_isonly/ which is
gitignored; this is a selection experiment, not a feed.
"""
import json, time, shutil
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
OUTDIR = os.path.join(ROOTOUT, '_isonly')
OUTF = os.path.join(ROOTOUT, 'isonly_stats.csv')
A_END = pd.Timestamp('2008-01-01')
B_END = pd.Timestamp('2016-01-01')
H = 20
NBLK = 6
CH = 900
os.makedirs(OUTDIR, exist_ok=True)

BATCH = [('own-price', 'sig2'), ('cross-sectional', 'sig3'),
         ('multi-timeframe', 'sig4'), ('regime-v5', 'sig5'),
         ('trend-duration', 'sig6'), ('trend-nonmomentum', 'sig7')]


def eff(s, h=H):
    p = np.log(s.astype(float)); r = p.diff()
    return ((p.shift(-h) - p).abs() / r.abs().shift(-h).rolling(h).sum()
            ).replace([np.inf, -np.inf], np.nan).values


def quints(X, y, mask):
    K = X.shape[1]
    Q = np.full((K, 5), np.nan, np.float32); N = np.zeros((K, 5), np.float32)
    V = np.full((K, 5), np.nan, np.float32)
    ym = mask & np.isfinite(y)
    for j in range(K):
        ok = ym & np.isfinite(X[:, j])
        m = ok.sum()
        if m < 200:
            continue
        xv = X[ok, j]
        if np.unique(xv).size < 5:
            continue
        yy = y[ok][np.argsort(xv, kind='stable')]
        e = np.arange(6) * m // 5
        for q in range(5):
            seg = yy[e[q]:e[q + 1]]
            if seg.size:
                Q[j, q] = seg.mean(); N[j, q] = seg.size
                V[j, q] = seg.var(ddof=1) if seg.size > 1 else np.nan
    return Q, N, V


def blockspread(X, y, blocks):
    K = X.shape[1]
    S = np.full((K, len(blocks)), np.nan, np.float32)
    fin = np.isfinite(y)
    for bi, bm in enumerate(blocks):
        ym = bm & fin
        for j in range(K):
            ok = ym & np.isfinite(X[:, j])
            m = int(ok.sum())
            if m < 80:
                continue
            xv = X[ok, j]
            if np.unique(xv).size < 5:
                continue
            yy = y[ok][np.argsort(xv, kind='stable')]
            e = m // 5
            if e >= 1:
                S[j, bi] = yy[-e:].mean() - yy[:e].mean()
    return S


def frame_for(mod, m, px, pair, ctx):
    if mod == 'sig2':
        return m.build(px[pair])
    if mod == 'sig5':
        return m.build(px, pair, ctx, exclude=frozenset())
    if mod in ('sig6', 'sig7'):
        return m.base_frame(px, pair, ctx)
    return m.build(px, pair, ctx)


def score_batch(label, mod, px, old_names):
    m = __import__(mod)
    ctx = m.context(px) if hasattr(m, 'context') else None
    idx = px.index
    insA = np.asarray(idx < A_END)
    insB = np.asarray((idx >= A_END) & (idx < B_END))
    isall = np.asarray(idx < B_END)
    # six stability blocks spanning IS ONLY
    ii = np.flatnonzero(isall)
    edges = np.linspace(ii[0], ii[-1] + 1, NBLK + 1).astype(int)
    blocks = [np.zeros(len(idx), bool) for _ in range(NBLK)]
    for i in range(NBLK):
        blocks[i][edges[i]:edges[i + 1]] = True

    for pair in px.columns:
        pf = os.path.join(OUTDIR, '%s_%s.npz' % (label.replace('-', ''), pair))
        if os.path.exists(pf):
            continue
        t0 = time.time()
        F = frame_for(mod, m, px, pair, ctx)
        y = eff(px[pair])
        cols = list(F.columns)
        chunks = [cols[i:i + CH] for i in range(0, len(cols), CH)]
        acc, names = [], []
        for cb in chunks:
            S = (m.expand(F[cb]) if hasattr(m, 'expand') else F[cb]).shift(1)
            nm = [c for c in S.columns if c in old_names]
            if not nm:
                continue
            S = S[nm]
            X = S.values
            d = {}
            for tag, msk in (('a', insA), ('b', insB)):
                q, n, v = quints(X, y, msk)
                d['q' + tag] = q; d['n' + tag] = n; d['v' + tag] = v
            d['bs'] = blockspread(X, y, blocks)
            acc.append(d); names += nm
            del S, X
        if not acc:
            continue
        merged = {k: np.concatenate([a[k] for a in acc], axis=0) for k in acc[0]}
        np.savez_compressed(pf, names=np.array(names), **merged)
        print('  %-18s %-7s %6d sigs %.0fs' % (label, pair, len(names), time.time() - t0),
              flush=True)
        del F, acc, merged


def pool(label):
    files = sorted(f for f in os.listdir(OUTDIR)
                   if f.startswith(label.replace('-', '') + '_') and f.endswith('.npz'))
    if len(files) < 28:
        print('  %s: only %d/28 pairs -- skipped' % (label, len(files)))
        return None
    Z = [np.load(os.path.join(OUTDIR, f), allow_pickle=True) for f in files]
    names = [str(x) for x in Z[0]['names']]
    K = len(names)
    out = {'s': names}
    for tag in ('a', 'b'):
        N = np.zeros((K, 5)); S = np.zeros((K, 5)); SS = np.zeros((K, 5))
        SPR = np.full((K, len(Z)), np.nan); CT = np.zeros(K)
        for i, z in enumerate(Z):
            q = z['q' + tag].astype(float); c = z['n' + tag].astype(float)
            v = z['v' + tag].astype(float)
            ok = ~np.isnan(q).any(1) & ~np.isnan(v).any(1)
            c2 = np.where(ok[:, None], c, 0)
            q2 = np.nan_to_num(q); v2 = np.nan_to_num(v)
            N += c2; S += c2 * q2; SS += (c2 - 1) * v2 + c2 * q2 * q2
            SPR[:, i] = np.where(ok, q[:, 4] - q[:, 0], np.nan)
            CT += ok
        M = np.where(N > 0, S / np.maximum(N, 1), np.nan)
        V = np.where(N > 1, (SS - N * M * M) / np.maximum(N - 1, 1), np.nan)
        spread = M[:, 4] - M[:, 0]
        se = np.sqrt(V[:, 4] / np.maximum(N[:, 4], 1) + V[:, 0] / np.maximum(N[:, 0], 1))
        rk = np.arange(5) - 2
        mono = np.array([np.corrcoef(rk, M[j])[0, 1] if not np.isnan(M[j]).any() else np.nan
                         for j in range(K)])
        with np.errstate(invalid='ignore'):
            agree = np.nanmean(np.sign(SPR) == np.sign(spread)[:, None], 1)
        out['t' + tag] = np.round(spread / se, 3)
        out['sp' + tag] = np.round(spread, 5)
        out['ag' + tag] = np.round(agree, 3)
        out['mo' + tag] = np.round(mono, 3)
        out['ct' + tag] = CT
    bs = np.nanmean(np.stack([z['bs'] for z in Z]), axis=0)
    with np.errstate(invalid='ignore'):
        out['tsb'] = np.nansum((np.sign(bs) == np.sign(out['spb'])[:, None])
                               & np.isfinite(bs), axis=1)
    D = pd.DataFrame(out)
    D['b'] = label
    return D


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    keep = {d['s'] for d in json.load(open(os.path.join(ROOTOUT, 'signals.json')))}
    print('rescoring %d signals with NO out-of-sample information' % len(keep))
    print('IS-A 1999..2007 train | IS-B 2008..2015 validate | OOS untouched\n')
    parts = []
    for label, mod in BATCH:
        score_batch(label, mod, px, keep)
        p = pool(label)
        if p is not None:
            parts.append(p)
            print('pooled %-18s %6d signals' % (label, len(p)), flush=True)
    D = pd.concat(parts, ignore_index=True).drop_duplicates(subset='s')
    D.to_csv(OUTF, index=False)
    print('\nwrote %s (%d rows)' % (os.path.basename(OUTF), len(D)))


if __name__ == '__main__':
    main()
