import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTDATA,exist_ok=True); os.makedirs(ROOTOUT,exist_ok=True)
sys.path.insert(0,ROOTLIB)
"""Score ~1080 signals x 28 pairs, split in-sample / out-of-sample.

IS  : 1999-01-04 .. 2015-12-31   (used to RANK)
OOS : 2016-01-01 .. 2026-07-24   (used to CONFIRM — never used for selection)

Target = forward 20-day efficiency ratio. Signals lagged one bar. Quintile split.
Checkpoints one .npz per pair into a DURABLE directory, so a container wipe costs
at most the pair in flight. Resumes by scanning for existing .npz files.
"""
import os, sys, time
import numpy as np, pandas as pd
sys.path.insert(0, os.path.join(ROOTLIB,''.lstrip('/')))
import sig3

OUT = os.path.join(ROOTOUT,'/scores3'.lstrip('/'))
PX = os.path.join(ROOTDATA,'/px28.csv'.lstrip('/'))
H = 20
SPLIT = '2016-01-01'
os.makedirs(OUT, exist_ok=True)


def target(px):
    p = np.log(px.astype(float))
    net = (p.shift(-H) - p).abs()
    path = p.diff().abs().shift(-H).rolling(H).sum()
    return (net / path).replace([np.inf, -np.inf], np.nan)


def quint(x, y):
    """Return (means[5], counts[5], vars[5]) or None."""
    ok = x.notna() & y.notna()
    if ok.sum() < 400:
        return None
    xv, yv = x[ok], y[ok]
    if xv.nunique() < 5:
        return None
    try:
        q = pd.qcut(xv.rank(method='first'), 5, labels=False)
    except Exception:
        return None
    g = yv.groupby(q)
    m = g.mean(); n = g.count(); v = g.var()
    if len(m) < 5:
        return None
    return (np.array([m.get(i, np.nan) for i in range(5)]),
            np.array([n.get(i, 0) for i in range(5)]),
            np.array([v.get(i, np.nan) for i in range(5)]))


CTX=None


def run_pair(pair, px):
    y = target(px[pair])
    S = sig3.build(px, pair, CTX).shift(1)
    names = list(S.columns)
    K = len(names)
    A = {k: np.full((K, 5), np.nan, np.float32) for k in
         ('qi', 'ni', 'vi', 'qo', 'no', 'vo')}
    mi = S.index < SPLIT
    for j, c in enumerate(names):
        x = S[c]
        a = quint(x[mi], y[mi])
        if a:
            A['qi'][j], A['ni'][j], A['vi'][j] = a
        b = quint(x[~mi], y[~mi])
        if b:
            A['qo'][j], A['no'][j], A['vo'][j] = b
    np.savez_compressed(os.path.join(OUT, pair + '.npz'), names=np.array(names), **A)
    return K


def main():
    global CTX
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    CTX = sig3.context(px)
    PAIRS = list(px.columns)
    assert len(PAIRS) == 28
    done = {f[:-4] for f in os.listdir(OUT) if f.endswith('.npz')}
    todo = [p for p in PAIRS if p not in done]
    print('done %d/28, todo %d' % (len(done), len(todo)), flush=True)
    for pair in todo:
        t0 = time.time()
        k = run_pair(pair, px)
        done.add(pair)
        print('%-7s %4d sigs  %.0fs  [%d/28]' % (pair, k, time.time() - t0, len(done)),
              flush=True)
    print('ALL DONE' if len(done) == 28 else 'partial %d' % len(done))


if __name__ == '__main__':
    main()
