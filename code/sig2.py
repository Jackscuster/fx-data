import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTDATA,exist_ok=True); os.makedirs(ROOTOUT,exist_ok=True)
sys.path.insert(0,ROOTLIB)
"""Expanded signal library: ~42 base families x 8 windows x 3 variants = ~1000.

Variants per base signal:
  (raw)   the level
  d_      change in the level over 20 days
  z_      level standardised against its own trailing 500-day history

Everything vectorised except Hurst. Signals returned UNLAGGED; the scorer shifts.
"""
import numpy as np, pandas as pd

W = [5, 10, 20, 40, 60, 90, 120, 250]


def _ols(y, x, n):
    sx = x.rolling(n).sum(); sy = y.rolling(n).sum()
    sxx = (x * x).rolling(n).sum(); syy = (y * y).rolling(n).sum()
    sxy = (x * y).rolling(n).sum()
    Sxx = sxx - sx * sx / n; Sxy = sxy - sx * sy / n; Syy = syy - sy * sy / n
    b = Sxy / Sxx
    sse = (Syy - b * Sxy).clip(lower=0)
    se = np.sqrt((sse / (n - 2)) / Sxx)
    return b, b / se


def _hurst(a):
    n = len(a)
    if n < 16:
        return np.nan
    L, S = [], []
    for k in (n // 8, n // 4, n // 2, n):
        if k < 8:
            continue
        m = n // k
        rs = []
        for i in range(m):
            g = a[i * k:(i + 1) * k]
            d = g - g.mean(); c = np.cumsum(d)
            r = c.max() - c.min(); s = g.std()
            if s > 0 and r > 0:
                rs.append(r / s)
        if rs:
            L.append(np.log(k)); S.append(np.log(np.mean(rs)))
    if len(L) < 2:
        return np.nan
    return np.polyfit(L, S, 1)[0]


def _wma(s, n):
    w = np.arange(1, n + 1, dtype=float)
    return s.rolling(n).apply(lambda a: np.dot(a, w) / w.sum(), raw=True)


def base(px):
    p = np.log(px.astype(float))
    r = p.diff(); ar = r.abs(); sg = np.sign(r)
    t = pd.Series(np.arange(len(p), dtype=float), index=p.index)
    o = {}
    for n in W:
        mp = p.rolling(n).mean(); sp = p.rolling(n).std()
        sr = r.rolling(n).std(); mar = ar.rolling(n).mean()
        mx = p.rolling(n).max(); mn = p.rolling(n).min()
        net = p - p.shift(n); path = ar.rolling(n).sum(); rng = mx - mn
        rng3 = p.rolling(3 * n).max() - p.rolling(3 * n).min()

        o[f'ef_{n}'] = net.abs() / path
        o[f'vr_{n}'] = (net.rolling(n).var() / n) / r.rolling(n).var()
        o[f'ac1_{n}'] = r.rolling(n).corr(r.shift(1))
        o[f'ac2_{n}'] = r.rolling(n).corr(r.shift(2))
        o[f'acsum_{n}'] = sum(r.rolling(n).corr(r.shift(k)) for k in (1, 2, 3, 4, 5))
        o[f'negac_{n}'] = sum((r.rolling(n).corr(r.shift(k)) < 0).astype(float)
                              for k in (1, 2, 3, 4, 5))
        o[f'ddhigh_{n}'] = p - mx
        o[f'ddlow_{n}'] = p - mn
        o[f'z_{n}'] = (p - mp) / sp
        o[f'dpo_{n}'] = p - mp.shift(n // 2 + 1)
        o[f'pctabove_{n}'] = (p > mp).rolling(n).mean()
        o[f'bbw_{n}'] = 2 * sp / mp.abs()
        o[f'rngcomp_{n}'] = 1 - rng / rng3
        o[f'volratio_{n}'] = sr / r.rolling(3 * n).std()
        o[f'dens_{n}'] = path / rng
        o[f'ampratio_{n}'] = path / net.abs()
        b, tt = _ols(p, t, n)
        o[f'maslope_{n}'] = b / sr
        o[f'slopet_{n}'] = tt
        rr = p.rolling(n).corr(t)
        o[f'r2_{n}'] = rr * rr
        h = _wma(2 * _wma(p, max(2, n // 2)) - _wma(p, n), max(2, int(np.sqrt(n))))
        o[f'hma_{n}'] = (h - h.shift(max(1, n // 4))) / sr
        o[f'kurt_{n}'] = r.rolling(n).kurt()
        o[f'skew_{n}'] = r.rolling(n).skew().abs()
        o[f'cv_{n}'] = ar.rolling(n).std() / mar
        o[f'sharpe_{n}'] = r.rolling(n).mean() / sr
        o[f'absmom_{n}'] = net.abs() / (sr * np.sqrt(n))
        turn = (sg != sg.shift(1)).astype(float)
        o[f'turn_{n}'] = turn.rolling(n).mean()
        o[f'runmax_{n}'] = turn.rolling(n).apply(
            lambda a: np.diff(np.r_[0, np.flatnonzero(a), len(a)]).max(), raw=True) / n
        pu = (sg > 0).rolling(n).mean().clip(1e-6, 1 - 1e-6)
        o[f'signent_{n}'] = -(pu * np.log(pu) + (1 - pu) * np.log(1 - pu))
        up = r.clip(lower=0).rolling(n).mean(); dn = (-r.clip(upper=0)).rolling(n).mean()
        o[f'rsi_{n}'] = 100 - 100 / (1 + up / dn)
        db, dt = _ols(p.diff(), p.shift(1), n)
        o[f'df_{n}'] = dt
        o[f'ou_{n}'] = (-np.log(2) / np.log1p(db.where(db.between(-0.999, -1e-6)))).clip(upper=500)
        o[f'hurst_{n}'] = r.rolling(n).apply(_hurst, raw=True)
        # --- added families ---
        cm = p.rolling(n).max().cummax() if False else None
        dd = p - p.rolling(n).max()
        o[f'maxdd_{n}'] = dd.rolling(n).min()
        o[f'ddratio_{n}'] = dd.rolling(n).min() / rng
        o[f'accel_{n}'] = mp.diff(max(1, n // 4)) / sr
        o[f'vov_{n}'] = sr.rolling(n).std() / sr
        o[f'tail_{n}'] = ar.rolling(n).quantile(0.95) / ar.rolling(n).median()
        o[f'iqr_{n}'] = (r.rolling(n).quantile(0.75) - r.rolling(n).quantile(0.25)) / sr
        o[f'zc_{n}'] = ((p - mp) * (p - mp).shift(1) < 0).rolling(n).mean()
        o[f'macorr_{n}'] = p.rolling(n).corr(mp)
        o[f'tstat_{n}'] = r.rolling(n).mean() / (sr / np.sqrt(n))
        o[f'gap_{n}'] = (p - p.rolling(n).median()) / sp
        o[f'updays_{n}'] = (r > 0).rolling(n).mean()
        o[f'pathvol_{n}'] = path / (sr * n)
        o[f'rngvol_{n}'] = rng / (sr * np.sqrt(n))
    return pd.DataFrame(o, index=px.index).replace([np.inf, -np.inf], np.nan)


def build(px):
    B = base(px)
    out = {c: B[c] for c in B.columns}
    for c in B.columns:
        x = B[c]
        out['d_' + c] = x - x.shift(20)
        m = x.rolling(500).mean(); s = x.rolling(500).std()
        out['z_' + c] = (x - m) / s
    return pd.DataFrame(out, index=px.index).replace([np.inf, -np.inf], np.nan)


if __name__ == '__main__':
    import time
    px = pd.read_csv(os.path.join(ROOTDATA,'/px28.csv'.lstrip('/')), index_col=0, parse_dates=True)
    t0 = time.time(); S = build(px['USDJPY'])
    print(S.shape, '%.0fs/pair' % (time.time() - t0))
    print('families:', len(set(c.rsplit('_', 1)[0] for c in base(px['USDJPY']).columns)))
    print('est full run: %.0f min' % (28 * (time.time() - t0) / 60))
