import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTDATA,exist_ok=True); os.makedirs(ROOTOUT,exist_ok=True)
sys.path.insert(0,ROOTLIB)
"""Signal library v3 — ~1000 NEW signals, deliberately different information.

Three sources of novelty:
  1. CROSS-SECTIONAL — uses the other 27 pairs and the 8 currency legs. This is the
     only genuinely new information in the project; everything prior was one pair's
     own close.
  2. DRAWDOWN EXTENDED — maxdd was the breakout winner in v2, so the family is
     expanded: drawup, duration, time-since-high, recovery, asymmetry.
  3. INTERACTIONS — products/ratios among confirmed v2 survivors.

Levels held OOS 65%, z-scores 56%, deltas 42%. Deltas are dropped. Level + z only.
"""
import numpy as np, pandas as pd, itertools

W = [5, 10, 15, 20, 30, 40, 60, 90, 120, 180, 250, 500]
CCY = ['EUR', 'GBP', 'AUD', 'NZD', 'USD', 'CAD', 'CHF', 'JPY']


def context(px):
    """Panel-wide objects computed once, shared across pairs."""
    lp = np.log(px.astype(float))
    rt = lp.diff()
    # currency leg indices: mean log value of ccy against all others
    idx = {}
    for c in CCY:
        base = [k for k in px.columns if k[:3] == c]
        quote = [k for k in px.columns if k[3:] == c]
        s = pd.Series(0.0, index=px.index)
        for k in base:
            s = s + lp[k]
        for k in quote:
            s = s - lp[k]
        idx[c] = s / (len(base) + len(quote))
    IDX = pd.DataFrame(idx)
    return dict(rt=rt, IDX=IDX, IR=IDX.diff(),
                pmean=rt.mean(axis=1), pdisp=rt.std(axis=1))


def build(px, pair, ctx):
    p = np.log(px[pair].astype(float))
    r = p.diff(); ar = r.abs(); sg = np.sign(r)
    rt, IDX, IR = ctx['rt'], ctx['IDX'], ctx['IR']
    pmean, pdisp = ctx['pmean'], ctx['pdisp']
    b, q = pair[:3], pair[3:]
    bi, qi = IDX[b], IDX[q]
    bir, qir = IR[b], IR[q]
    o = {}

    for n in W:
        sr = r.rolling(n).std()
        mx = p.rolling(n).max(); mn = p.rolling(n).min()
        dd = p - mx; du = p - mn
        rng = mx - mn

        # --- drawdown family, extended ---
        o[f'maxdd_{n}'] = dd.rolling(n).min()
        o[f'maxdu_{n}'] = du.rolling(n).max()
        o[f'dduratio_{n}'] = dd.rolling(n).min().abs() / du.rolling(n).max().abs()
        o[f'ddarea_{n}'] = dd.rolling(n).mean()
        o[f'duarea_{n}'] = du.rolling(n).mean()
        o[f'tsh_{n}'] = (p.rolling(n).apply(lambda a: len(a) - 1 - np.argmax(a), raw=True)) / n
        o[f'tsl_{n}'] = (p.rolling(n).apply(lambda a: len(a) - 1 - np.argmin(a), raw=True)) / n
        o[f'recov_{n}'] = (p - mn) / rng
        o[f'ddvol_{n}'] = dd.rolling(n).min().abs() / (sr * np.sqrt(n))

        # --- asymmetry / semivariance ---
        upv = r.clip(lower=0).rolling(n).std(); dnv = (-r.clip(upper=0)).rolling(n).std()
        o[f'semi_{n}'] = dnv / upv
        o[f'upvol_{n}'] = upv / sr
        o[f'dnvol_{n}'] = dnv / sr
        o[f'maxup_{n}'] = r.rolling(n).max() / sr
        o[f'maxdn_{n}'] = r.rolling(n).min().abs() / sr
        o[f'q90_{n}'] = ar.rolling(n).quantile(0.90) / ar.rolling(n).mean()

        # --- CROSS-SECTIONAL: this pair vs the panel ---
        pv = rt.rolling(n).std()
        o[f'volrank_{n}'] = pv.rank(axis=1, pct=True)[pair]
        o[f'relvol_{n}'] = sr / pv.median(axis=1)
        o[f'paneldisp_{n}'] = pdisp.rolling(n).mean()
        o[f'panelvol_{n}'] = pv.median(axis=1)
        o[f'corrpanel_{n}'] = r.rolling(n).corr(pmean)
        pe = (rt.rolling(n).sum().abs() / rt.abs().rolling(n).sum())
        o[f'efrank_{n}'] = pe.rank(axis=1, pct=True)[pair]
        o[f'paneleff_{n}'] = pe.median(axis=1)
        o[f'reldisp_{n}'] = sr / pdisp.rolling(n).mean()

        # --- CROSS-SECTIONAL: the two currency legs ---
        o[f'basemom_{n}'] = (bi - bi.shift(n)) / bir.rolling(n).std()
        o[f'quotemom_{n}'] = (qi - qi.shift(n)) / qir.rolling(n).std()
        o[f'legdiv_{n}'] = ((bi - bi.shift(n)) - (qi - qi.shift(n))).abs() / sr
        o[f'legcorr_{n}'] = bir.rolling(n).corr(qir)
        o[f'basevol_{n}'] = bir.rolling(n).std() / sr
        o[f'quotevol_{n}'] = qir.rolling(n).std() / sr
        o[f'legvolr_{n}'] = bir.rolling(n).std() / qir.rolling(n).std()
        o[f'usdbeta_{n}'] = r.rolling(n).cov(IR['USD']) / IR['USD'].rolling(n).var()
        o[f'baseef_{n}'] = (bi - bi.shift(n)).abs() / bir.abs().rolling(n).sum()
        o[f'quoteef_{n}'] = (qi - qi.shift(n)).abs() / qir.abs().rolling(n).sum()

    B = pd.DataFrame(o, index=px.index).replace([np.inf, -np.inf], np.nan)
    out = {c: B[c] for c in B.columns}
    for c in B.columns:
        x = B[c]
        out['z_' + c] = (x - x.rolling(500).mean()) / x.rolling(500).std()

    # --- INTERACTIONS among confirmed v2 survivors ---
    lp2 = p
    sr60 = r.rolling(60).std()
    W2 = {}
    for n in (20, 40, 60, 90, 120):
        W2[f'bbw{n}'] = 2 * lp2.rolling(n).std() / lp2.rolling(n).mean().abs()
        W2[f'mdd{n}'] = (lp2 - lp2.rolling(n).max()).rolling(n).min()
        W2[f'rcp{n}'] = 1 - (lp2.rolling(n).max() - lp2.rolling(n).min()) / \
                        (lp2.rolling(3 * n).max() - lp2.rolling(3 * n).min())
        W2[f'hur{n}'] = lp2.rolling(n).std() / lp2.rolling(3 * n).std()
    ks = list(W2)
    for a, c in itertools.combinations(ks, 2):
        x, y = W2[a], W2[c]
        xs = (x - x.rolling(500).mean()) / x.rolling(500).std()
        ys = (y - y.rolling(500).mean()) / y.rolling(500).std()
        out[f'x_{a}_{c}'] = xs * ys

    return pd.DataFrame(out, index=px.index).replace([np.inf, -np.inf], np.nan)


if __name__ == '__main__':
    import time
    px = pd.read_csv(os.path.join(ROOTDATA,'/px28.csv'.lstrip('/')), index_col=0, parse_dates=True)
    ctx = context(px)
    t0 = time.time(); S = build(px, 'USDJPY', ctx)
    print(S.shape, '%.0fs/pair  est %.0f min total' %
          (time.time() - t0, 28 * (time.time() - t0) / 60))
