import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Score ~8,065 NEW signals x 28 pairs on TWO regime targets.

TREND  forward 20d efficiency ratio   |net| / path      high = straight travel
CHOP   forward 20d turn frequency     direction flips   high = whipsaw

Both IS 1999-2015 / OOS 2016-2026. Signals lagged one bar.
One .npz per pair into a durable directory; resumes on rerun.
"""
import os, sys, time
import numpy as np, pandas as pd
sys.path.insert(0, 'ROOTLIB')
import sig5

OUT = os.path.join(ROOTOUT,'/scores5'.lstrip('/'))
PX = os.path.join(ROOTDATA,'/px28.csv'.lstrip('/'))
SIG = os.path.join(ROOTOUT,'/signals.json'.lstrip('/'))
H = 20
SPLIT = pd.Timestamp('2016-01-01')
os.makedirs(OUT, exist_ok=True)


def targets(s):
    p = np.log(s.astype(float))
    r = p.diff()
    net = (p.shift(-H) - p).abs()
    path = r.abs().shift(-H).rolling(H).sum()
    trend = (net / path).replace([np.inf, -np.inf], np.nan)
    flip = (np.sign(r) != np.sign(r.shift(1))).astype(float)
    chop = flip.shift(-H).rolling(H).mean()
    return trend.values, chop.values


def quints(X, y, mask):
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


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    old = {d['s'] for d in __import__('json').load(open(SIG))}
    ctx = sig5.context(px)
    done = {f[:-4] for f in os.listdir(OUT) if f.endswith('.npz')}
    todo = [p for p in px.columns if p not in done]
    print('done %d/28, todo %d' % (len(done), len(todo)), flush=True)
    for pair in todo:
        t0 = time.time()
        S = sig5.build(px, pair, ctx, exclude=old).shift(1)
        X = S.values
        names = np.array(S.columns)
        ytr, ych = targets(px[pair])
        ins = np.asarray(S.index < SPLIT)
        d = {}
        for tag, y in (('t', ytr), ('c', ych)):
            for per, m in (('i', ins), ('o', ~ins)):
                q, n, v = quints(X, y, m)
                d[f'q{tag}{per}'] = q; d[f'n{tag}{per}'] = n; d[f'v{tag}{per}'] = v
        np.savez_compressed(os.path.join(OUT, pair + '.npz'), names=names, **d)
        done.add(pair)
        print('%-7s %5d sigs  %.0fs  [%d/28]' % (pair, len(names), time.time() - t0, len(done)),
              flush=True)
        del S, X
    print('ALL DONE' if len(done) == 28 else 'partial %d' % len(done))


if __name__ == '__main__':
    main()
