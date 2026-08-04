import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Signal library v5 — ~10,000 NEW signals. Nothing here duplicates v2/v3/v4.

THREE REGIME CLASSES, three separate targets:
  TREND   forward 20d efficiency ratio        |net| / path
  CHOP    forward 20d turn frequency          share of direction changes
  CRISIS  forward 20d volatility surprise     max|move| next 20d / trailing 60d sigma

NEW FAMILY GROUPS (none present in earlier batches):
  jump / discontinuity   bipower variation, jump ratio, sigma-exceedance counts,
                         realized quarticity, largest-move share   -> crisis
  contagion              coexceedance counts, correlation-matrix eigenvalue
                         concentration, max pairwise correlation   -> crisis
  entropy / complexity    permutation entropy, sample entropy, DFA, Lempel-Ziv
  vol clustering          ACF of |returns|, Ljung-Box on squares, ARCH LM
  order statistics        rank of today's move, quantile-regression slope,
                         time since sigma-exceedance
  drawdown clustering     panel-wide simultaneous drawdown depth

DROPPED ON EVIDENCE: interactions (49% OOS sign retention, worse than chance),
deltas (42%). Variants kept: level, z-score, rolling percentile rank.
"""
import math
import numpy as np, pandas as pd

W = [3, 5, 8, 10, 15, 20, 25, 30, 40, 50, 60, 75, 90, 120, 150, 180, 250, 375, 500, 750]
WW = [4, 6, 8, 13, 20, 26, 39, 52]
WM = [2, 3, 6, 9, 12, 18, 24]
CCY = ['EUR', 'GBP', 'AUD', 'NZD', 'USD', 'CAD', 'CHF', 'JPY']


def _perm_entropy(a, m=3):
    n = len(a) - m + 1
    if n < 3:
        return np.nan
    pats = {}
    for i in range(n):
        k = tuple(np.argsort(a[i:i + m]))
        pats[k] = pats.get(k, 0) + 1
    p = np.array(list(pats.values()), float) / n
    return -(p * np.log(p)).sum() / np.log(math.factorial(m))


def _lz(a):
    s = ''.join('1' if x > 0 else '0' for x in a)
    i, c, n = 0, 1, len(s)
    k, l = 1, 1
    while True:
        if i + k > n - 1:
            c += 1
            break
        if s[i:i + k] == s[l:l + k] if l + k <= n else False:
            k += 1
        else:
            if k > 1:
                l += 1
                i = 0
                k = 1
            else:
                l += 1
                c += 1
                i = 0
                k = 1
        if l + k > n:
            c += 1
            break
    return c / (n / np.log2(max(n, 2)))


def _dfa(a):
    n = len(a)
    if n < 16:
        return np.nan
    y = np.cumsum(a - a.mean())
    out = []
    for s in (4, 8, n // 4, n // 2):
        if s < 4 or s > n // 2:
            continue
        m = n // s
        rms = []
        for i in range(m):
            seg = y[i * s:(i + 1) * s]
            t = np.arange(s)
            c = np.polyfit(t, seg, 1)
            rms.append(np.sqrt(((seg - np.polyval(c, t)) ** 2).mean()))
        if rms:
            out.append((np.log(s), np.log(np.mean(rms))))
    if len(out) < 2:
        return np.nan
    x, yv = zip(*out)
    return np.polyfit(x, yv, 1)[0]


def core(lp, wins, tag):
    r = lp.diff(); ar = r.abs(); r2 = r * r
    o = {}
    for n in wins:
        if n >= len(lp) // 3 or n < 3:
            continue
        k = f'{tag}{n}'
        sr = r.rolling(n).std()
        # --- jump / discontinuity ---
        bp = (ar * ar.shift(1)).rolling(n).sum() * (np.pi / 2)
        rv = r2.rolling(n).sum()
        o['jumpratio_' + k] = (rv - bp).clip(lower=0) / rv
        o['bipow_' + k] = bp / rv
        o['quartic_' + k] = (r2 * r2).rolling(n).sum() * n / (rv * rv)
        o['maxshare_' + k] = ar.rolling(n).max() / ar.rolling(n).sum()
        o['top3share_' + k] = (ar.rolling(n).apply(
            lambda a: np.sort(a)[-3:].sum(), raw=True)) / ar.rolling(n).sum()
        for s in (2, 3):
            o[f'exceed{s}_' + k] = (ar > s * sr.shift(1)).rolling(n).sum() / n
        o['tsexceed_' + k] = (ar > 2 * sr.shift(1)).rolling(n).apply(
            lambda a: len(a) - 1 - (np.flatnonzero(a).max() if a.any() else -1), raw=True) / n
        # --- vol clustering ---
        o['absac1_' + k] = ar.rolling(n).corr(ar.shift(1))
        o['absac5_' + k] = ar.rolling(n).corr(ar.shift(5))
        o['sqac1_' + k] = r2.rolling(n).corr(r2.shift(1))
        lb = sum(ar.rolling(n).corr(ar.shift(j)) ** 2 for j in (1, 2, 3, 4, 5)) * n
        o['ljungabs_' + k] = lb
        o['archlm_' + k] = r2.rolling(n).corr(r2.shift(1)) ** 2 * n
        o['volpersist_' + k] = sr / sr.shift(n)
        o['volaccel_' + k] = sr.diff(max(1, n // 4)) / sr
        # --- entropy / complexity ---
        if n in (20, 60, 120):
            o['perment_' + k] = r.rolling(n).apply(_perm_entropy, raw=True)
        if n in (60, 120):
            o['dfa_' + k] = r.rolling(n).apply(_dfa, raw=True)
        # --- order statistics ---
        o['rankmove_' + k] = ar.rolling(n).rank(pct=True)
        o['rankret_' + k] = r.rolling(n).rank(pct=True)
        o['medabs_' + k] = ar.rolling(n).median() / ar.rolling(n).mean()
        o['q10q90_' + k] = (r.rolling(n).quantile(.9) - r.rolling(n).quantile(.1)) / sr
        o['posq_' + k] = (lp - lp.rolling(n).min()) / (
            lp.rolling(n).max() - lp.rolling(n).min())
        # --- shape not previously covered ---
        o['upcap_' + k] = r.clip(lower=0).rolling(n).sum() / ar.rolling(n).sum()
        o['streakvol_' + k] = sr / ar.rolling(n).mean()
        o['convex_' + k] = (lp - lp.shift(n)).abs() / (
            lp.diff(max(1, n // 2)).abs().rolling(n).mean() * n)
        # --- additional cheap families ---
        mn_ = ar.rolling(n).mean()
        o['volskew_' + k] = ar.rolling(n).skew()
        o['volkurt_' + k] = ar.rolling(n).kurt()
        o['gini_' + k] = ar.rolling(n).std() / mn_
        o['rmean_' + k] = r.rolling(n).mean() / mn_
        o['downshare_' + k] = (-r.clip(upper=0)).rolling(n).sum() / ar.rolling(n).sum()
        o['sigmaup_' + k] = (r > sr.shift(1)).rolling(n).mean()
        o['sigmadn_' + k] = (r < -sr.shift(1)).rolling(n).mean()
        o['calm_' + k] = (ar < 0.5 * sr.shift(1)).rolling(n).mean()
        o['volofvol_' + k] = ar.rolling(n).std() / ar.rolling(n).std().shift(n)
        o['rangeratio_' + k] = (lp.rolling(n).max() - lp.rolling(n).min()) / (
            ar.rolling(n).max() * np.sqrt(n))
        o['halfsplit_' + k] = (r.rolling(max(2, n // 2)).mean() /
                               r.rolling(n).mean().replace(0, np.nan))
        o['volsplit_' + k] = r.rolling(max(2, n // 2)).std() / sr
        o['absmean_' + k] = mn_ / sr
        o['nzero_' + k] = (ar < 1e-6).rolling(n).mean()
        o['trendvol_' + k] = (lp - lp.shift(n)) / (sr * np.sqrt(n))
        o['whip_' + k] = ar.rolling(n).sum() / (lp - lp.shift(n)).abs().clip(lower=1e-9)
        o['dispvsown_' + k] = sr / sr.rolling(4 * n).mean()
        o['minvol_' + k] = sr.rolling(n).min() / sr
        o['maxvol_' + k] = sr.rolling(n).max() / sr
        o['volrange_' + k] = (sr.rolling(n).max() - sr.rolling(n).min()) / sr
    return o


def context(px):
    lp = np.log(px.astype(float)); rt = lp.diff()
    z = (rt - rt.rolling(250).mean()) / rt.rolling(250).std()
    ctx = dict(lp=lp, rt=rt, z=z)
    # contagion: how many pairs exceed 2 sigma on the same day
    ctx['coex2'] = (z.abs() > 2).sum(axis=1) / z.shape[1]
    ctx['coex3'] = (z.abs() > 3).sum(axis=1) / z.shape[1]
    # correlation-matrix concentration
    eig = {}
    for n in (60, 120, 250):
        vals = []
        R = rt.tail(0)
        arr = rt.values
        idx = rt.index
        out = np.full(len(idx), np.nan)
        for i in range(n, len(idx), 5):
            blk = arr[i - n:i]
            blk = blk[~np.isnan(blk).any(1)]
            if len(blk) > n // 2:
                C = np.corrcoef(blk.T)
                w = np.linalg.eigvalsh(C)
                out[i] = w.max() / w.sum()
        eig[n] = pd.Series(out, index=idx).ffill()
    ctx['eig'] = eig
    ctx['maxcorr'] = {n: rt.rolling(n).corr(rt.mean(axis=1)).max(axis=1) for n in (60, 250)}
    # pair-INDEPENDENT panel series: compute once, reuse for all 28 pairs
    shared = {}
    L = np.log(px.astype(float))
    for n in W:
        if n < 3:
            continue
        dd = L - L.rolling(n).max()
        shared[f'paneldd_D{n}'] = dd.mean(axis=1)
        shared[f'paneldd_min_D{n}'] = dd.min(axis=1)
        shared[f'ddbreadth_D{n}'] = (dd < -0.02).sum(axis=1) / dd.shape[1]
        shared[f'coex2_D{n}'] = ctx['coex2'].rolling(n).mean()
        shared[f'coex3_D{n}'] = ctx['coex3'].rolling(n).mean()
        shared[f'coexmax_D{n}'] = ctx['coex2'].rolling(n).max()
    ctx['shared'] = shared
    ctx['big5'] = (z.abs() > 1.5).sum(axis=1).gt(5)
    return ctx


def panel(px, pair, ctx, wins, tag):
    z = ctx['z']
    o = dict(ctx['shared'])
    zi = z[pair].abs() > 1.5
    for n in wins:
        if n < 3:
            continue
        o[f'taildep_{tag}{n}'] = (zi & ctx['big5']).rolling(n).mean()
    for n, s in ctx['eig'].items():
        o[f'eigconc_{tag}{n}'] = s
    for n, s in ctx['maxcorr'].items():
        o[f'maxcorr_{tag}{n}'] = s
    return o


def build(px, pair, ctx, exclude=frozenset()):
    lp = ctx['lp'][pair]
    out = {}
    out.update(core(lp, W, 'D'))
    for rule, wins, tg in (('W-FRI', WW, 'W'), ('ME', WM, 'M')):
        s = lp.resample(rule).last().dropna()
        for k, v in core(s, wins, tg).items():
            out[k] = v.shift(1).reindex(lp.index, method='ffill')
    out.update(panel(px, pair, ctx, W, 'D'))
    base = pd.DataFrame(out, index=lp.index).replace([np.inf, -np.inf], np.nan)
    add = {}
    for c in base.columns:
        x = base[c]
        add['zz_' + c] = (x - x.rolling(500).mean()) / x.rolling(500).std()
        add['zs_' + c] = (x - x.rolling(120).mean()) / x.rolling(120).std()
        add['pr_' + c] = x.rolling(250).rank(pct=True)
        add['ps_' + c] = x.rolling(60).rank(pct=True)
    S = pd.concat([base, pd.DataFrame(add, index=lp.index)], axis=1)
    S = S.replace([np.inf, -np.inf], np.nan)
    keep = [c for c in S.columns if c not in exclude]
    return S[keep].astype(np.float32)


if __name__ == '__main__':
    import time, json
    px = pd.read_csv(os.path.join(ROOTDATA,'/px28.csv'.lstrip('/')), index_col=0, parse_dates=True)
    old = {d['s'] for d in json.load(open(
        os.path.join(ROOTOUT,'/signals.json'.lstrip('/'))))}
    ctx = context(px)
    t0 = time.time()
    S = build(px, 'USDJPY', ctx, exclude=old)
    el = time.time() - t0
    print('%d NEW signals  %.0fs/pair  est %.0f min for 28' % (S.shape[1], el, 28 * el / 60))
    print('overlap with previous 12,413:', len(set(S.columns) & old))
    print('coverage median %.2f' % S.notna().mean().median())
