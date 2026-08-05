import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Score the v7 trend batch x 28 pairs against THREE HORIZONS.

TARGETS. The horizon question -- does FX trend live at 60-120 days rather than 20 --
has been open since the start of the project and has never been tested. Every signal
is scored against forward efficiency at three horizons plus turn frequency:

    t   forward 20d  efficiency ratio   |net| / path      (the historical primary)
    e   forward 60d  efficiency ratio
    f   forward 120d efficiency ratio
    c   forward 20d  turn frequency     direction flips

Turn frequency stays at 20d. It is here for corroboration, not for the horizon
question: on the v6 batch the two targets agreed in direction on 25 of 25
independents, and that cross-check is worth keeping. Array naming follows sc5/sc6
for t and c so v7 pools through prep.py unchanged.

Block spreads (bst/bse/bsf/bsc) are stored per target so gate 7 can be evaluated at
any horizon, not only at 20d.

NO SHARPE. Nothing here measures a strategy.

RESUMABLE at two levels, as sc6: finished pairs skip, and each block of columns is
written to _part/ as it completes so an interrupted run resumes mid-pair.

The .npz output is LOCAL ONLY -- results/scores7/ is gitignored. The repo already
carries 438 MB of scores6. pool7.py turns these into the committed per-signal
statistics.
"""
import time, json, shutil
import numpy as np, pandas as pd
import sig7

OUT = os.path.join(ROOTOUT, 'scores7')
PART = os.path.join(OUT, '_part')
PX = os.path.join(ROOTDATA, 'px28.csv')
SIG = os.path.join(ROOTOUT, 'signals.json')
SPLIT = pd.Timestamp('2016-01-01')
NBLK = 6
CH = 900                       # base cols per block -> 9,000 signal cols
HOR = [('t', 20), ('e', 60), ('f', 120)]
os.makedirs(PART, exist_ok=True)


def eff(s, H):
    p = np.log(s.astype(float))
    r = p.diff()
    net = (p.shift(-H) - p).abs()
    path = r.abs().shift(-H).rolling(H).sum()
    return (net / path).replace([np.inf, -np.inf], np.nan).values


def turn(s, H=20):
    p = np.log(s.astype(float))
    r = p.diff()
    flip = (np.sign(r) != np.sign(r.shift(1))).astype(float)
    return flip.shift(-H).rolling(H).mean().values


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


def blockspread(X, y, blocks):
    K = X.shape[1]
    S = np.full((K, len(blocks)), np.nan, np.float32)
    fin = np.isfinite(y)
    for bi, bm in enumerate(blocks):
        ym = bm & fin
        for j in range(K):
            ok = ym & np.isfinite(X[:, j])
            m = int(ok.sum())
            if m < 100:
                continue
            xv = X[ok, j]
            if np.unique(xv).size < 5:
                continue
            yy = y[ok][np.argsort(xv, kind='stable')]
            e = m // 5
            if e < 1:
                continue
            S[j, bi] = yy[-e:].mean() - yy[:e].mean()
    return S


def score_block(Xb, Y, ins, blocks):
    d = {}
    for tag, y in Y.items():
        for per, m in (('i', ins), ('o', ~ins)):
            q, n, v = quints(Xb, y, m)
            d['q%s%s' % (tag, per)] = q
            d['n%s%s' % (tag, per)] = n
            d['v%s%s' % (tag, per)] = v
        d['bs' + tag] = blockspread(Xb, y, blocks)
    return d


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    old = {d['s'] for d in json.load(open(SIG))}
    print('building panel context...', flush=True)
    ctx = sig7.context(px)
    done = {f[:-4] for f in os.listdir(OUT) if f.endswith('.npz')}
    todo = [p for p in px.columns if p not in done]
    print('done %d/28, todo %d' % (len(done), len(todo)), flush=True)

    for pair in todo:
        t0 = time.time()
        F = sig7.base_frame(px, pair, ctx)
        cols = list(F.columns)
        Y = {tag: eff(px[pair], H) for tag, H in HOR}
        Y['c'] = turn(px[pair])
        ins = np.asarray(F.index < SPLIT)
        edges = np.linspace(0, len(F), NBLK + 1).astype(int)
        blocks = [np.zeros(len(F), bool) for _ in range(NBLK)]
        for i in range(NBLK):
            blocks[i][edges[i]:edges[i + 1]] = True

        chunks = [cols[i:i + CH] for i in range(0, len(cols), CH)]
        acc, names = [], []
        for bi, cb in enumerate(chunks):
            pf = os.path.join(PART, '%s_%03d.npz' % (pair, bi))
            if os.path.exists(pf):
                z = np.load(pf, allow_pickle=True)
                acc.append({k: z[k] for k in z.files if k != 'names'})
                names += list(z['names'])
                continue
            S = sig7.expand(F[cb]).shift(1)
            nm = [c for c in S.columns if c not in old]
            S = S[nm]
            d = score_block(S.values, Y, ins, blocks)
            np.savez_compressed(pf, names=np.array(nm), **d)
            acc.append(d); names += nm
            del S
            print('  %s block %d/%d  %d cols  %.0fs'
                  % (pair, bi + 1, len(chunks), len(nm), time.time() - t0), flush=True)

        merged = {k: np.concatenate([a[k] for a in acc], axis=0) for k in acc[0]}
        np.savez_compressed(os.path.join(OUT, pair + '.npz'),
                            names=np.array(names), **merged)
        for bi in range(len(chunks)):
            pf = os.path.join(PART, '%s_%03d.npz' % (pair, bi))
            if os.path.exists(pf):
                os.remove(pf)
        done.add(pair)
        del F, acc, merged
        print('%-7s %6d sigs  %.0fs  [%d/28]'
              % (pair, len(names), time.time() - t0, len(done)), flush=True)

    if len(done) == 28:
        shutil.rmtree(PART, ignore_errors=True)
        print('ALL DONE')
    else:
        print('partial %d/28' % len(done))


if __name__ == '__main__':
    main()
