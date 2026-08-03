import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Score ~10,400 signals x 28 pairs. IS 1999-2015 / OOS 2016-2026.

Quintile stats computed in numpy — pandas groupby is the bottleneck at this width.
One .npz per pair into a DURABLE directory; resumes by scanning for existing files.
"""
import os, sys, time
import numpy as np, pandas as pd
sys.path.insert(0, 'ROOTLIB')
import sig4

OUT = os.path.join(ROOTOUT,'/scores4'.lstrip('/'))
PX = os.path.join(ROOTDATA,'/px28.csv'.lstrip('/'))
H = 20
SPLIT = pd.Timestamp('2016-01-01')
os.makedirs(OUT, exist_ok=True)


def target(px):
    p = np.log(px.astype(float))
    net = (p.shift(-H) - p).abs()
    path = p.diff().abs().shift(-H).rolling(H).sum()
    return (net / path).replace([np.inf, -np.inf], np.nan)


def quints(X, y, mask):
    """X (T,K) float32, y (T,) float. Returns q,n,v arrays (K,5)."""
    K = X.shape[1]
    Q = np.full((K, 5), np.nan, np.float32)
    N = np.zeros((K, 5), np.float32)
    V = np.full((K, 5), np.nan, np.float32)
    ym = mask & np.isfinite(y)
    for j in range(K):
        ok = ym & np.isfinite(X[:, j])
        m = ok.sum()
        if m < 400:
            continue
        xv = X[ok, j]; yv = y[ok]
        if np.unique(xv).size < 5:
            continue
        order = np.argsort(xv, kind='stable')
        yy = yv[order]
        edges = (np.arange(6) * m // 5)
        for q in range(5):
            seg = yy[edges[q]:edges[q + 1]]
            if seg.size:
                Q[j, q] = seg.mean(); N[j, q] = seg.size
                V[j, q] = seg.var(ddof=1) if seg.size > 1 else np.nan
    return Q, N, V


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    ctx = sig4.context(px)
    pairs = list(px.columns)
    done = {f[:-4] for f in os.listdir(OUT) if f.endswith('.npz')}
    todo = [p for p in pairs if p not in done]
    print('done %d/28, todo %d' % (len(done), len(todo)), flush=True)
    for pair in todo:
        t0 = time.time()
        S = sig4.build(px, pair, ctx).shift(1)
        names = np.array(S.columns)
        X = S.values
        y = target(px[pair]).values
        ins = np.asarray(S.index < SPLIT)
        qi, ni, vi = quints(X, y, ins)
        qo, no, vo = quints(X, y, ~ins)
        np.savez_compressed(os.path.join(OUT, pair + '.npz'), names=names,
                            qi=qi, ni=ni, vi=vi, qo=qo, no=no, vo=vo)
        done.add(pair)
        print('%-7s %5d sigs  %.0fs  [%d/28]' % (pair, len(names), time.time() - t0, len(done)),
              flush=True)
        del S, X
    print('ALL DONE' if len(done) == 28 else 'partial %d' % len(done))


if __name__ == '__main__':
    main()
