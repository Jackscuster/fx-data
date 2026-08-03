import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Signal library v4 — ~10,000 signals.

Built around what has actually held up:
  - cross-sectional features retained sign OOS 68% vs 54% for own-price -> weight heavily
  - levels held 65%, z-scores 56%, deltas 42% -> levels and z only, no deltas
  - M/W/D structure is new as a FEATURE source, not just a filter

Composition per pair:
  A base families x 12 windows, on DAILY                      ~600
  B same families on WEEKLY and MONTHLY, mapped down causally  ~1200
  C term structure: ratio of each family at adjacent windows   ~1600
  D cross-sectional panel + currency-leg features x 3 TFs      ~1900
  E z-scored variants of A+D                                   ~2500
  F interactions among the strongest confirmed families        ~2200

CAUSALITY: weekly labels usable the following Monday, monthly the next month open.
Higher-TF series are shifted on their OWN clock before being reindexed onto daily bars.
"""
import numpy as np, pandas as pd, itertools

W = [5, 10, 15, 20, 30, 40, 60, 90, 120, 180, 250, 500]
WW = [4, 8, 13, 26, 52]          # weekly windows
WM = [3, 6, 12, 24]              # monthly windows
CCY = ['EUR', 'GBP', 'AUD', 'NZD', 'USD', 'CAD', 'CHF', 'JPY']


def _ols_t(y, x, n):
    sx = x.rolling(n).sum(); sy = y.rolling(n).sum()
    sxx = (x * x).rolling(n).sum(); syy = (y * y).rolling(n).sum()
    sxy = (x * y).rolling(n).sum()
    Sxx = sxx - sx * sx / n; Sxy = sxy - sx * sy / n; Syy = syy - sy * sy / n
    b = Sxy / Sxx
    se = np.sqrt(((Syy - b * Sxy).clip(lower=0) / (n - 2)) / Sxx)
    return b, b / se


def core(lp, wins, tag):
    """Family set computable on any timeframe."""
    r = lp.diff(); ar = r.abs(); sg = np.sign(r)
    t = pd.Series(np.arange(len(lp), dtype=float), index=lp.index)
    o = {}
    for n in wins:
        if n >= len(lp) // 3:
            continue
        mp = lp.rolling(n).mean(); sp = lp.rolling(n).std()
        sr = r.rolling(n).std(); mar = ar.rolling(n).mean()
        mx = lp.rolling(n).max(); mn = lp.rolling(n).min()
        net = lp - lp.shift(n); path = ar.rolling(n).sum(); rng = mx - mn
        rng3 = lp.rolling(3 * n).max() - lp.rolling(3 * n).min()
        dd = lp - mx; du = lp - mn
        k = f'{tag}{n}'
        o['ef_' + k] = net.abs() / path
        o['vr_' + k] = (net.rolling(n).var() / n) / r.rolling(n).var()
        o['ac1_' + k] = r.rolling(n).corr(r.shift(1))
        o['bbw_' + k] = 2 * sp / mp.abs()
        o['rngcomp_' + k] = 1 - rng / rng3
        o['volratio_' + k] = sr / r.rolling(3 * n).std()
        o['dens_' + k] = path / rng
        o['maxdd_' + k] = dd.rolling(n).min()
        o['maxdu_' + k] = du.rolling(n).max()
        o['ddarea_' + k] = dd.rolling(n).mean()
        o['duarea_' + k] = du.rolling(n).mean()
        o['dduratio_' + k] = dd.rolling(n).min().abs() / du.rolling(n).max().abs()
        o['recov_' + k] = (lp - mn) / rng
        o['ddhigh_' + k] = dd
        o['z_' + k] = (lp - mp) / sp
        o['pctabove_' + k] = (lp > mp).rolling(n).mean()
        b, tt = _ols_t(lp, t, n)
        o['maslope_' + k] = b / sr
        o['slopet_' + k] = tt
        rr = lp.rolling(n).corr(t)
        o['r2_' + k] = rr * rr
        o['kurt_' + k] = r.rolling(n).kurt()
        o['skew_' + k] = r.rolling(n).skew().abs()
        o['cv_' + k] = ar.rolling(n).std() / mar
        o['sharpe_' + k] = r.rolling(n).mean() / sr
        o['absmom_' + k] = net.abs() / (sr * np.sqrt(n))
        turn = (sg != sg.shift(1)).astype(float)
        o['turn_' + k] = turn.rolling(n).mean()
        o['updays_' + k] = (r > 0).rolling(n).mean()
        up = r.clip(lower=0).rolling(n).mean(); dn = (-r.clip(upper=0)).rolling(n).mean()
        o['rsi_' + k] = 100 - 100 / (1 + up / dn)
        db, dt = _ols_t(r, lp.shift(1), n)
        o['df_' + k] = dt
        upv = r.clip(lower=0).rolling(n).std(); dnv = (-r.clip(upper=0)).rolling(n).std()
        o['semi_' + k] = dnv / upv
        o['tail_' + k] = ar.rolling(n).quantile(.95) / ar.rolling(n).median()
        o['vov_' + k] = sr.rolling(n).std() / sr
        o['rngvol_' + k] = rng / (sr * np.sqrt(n))
        o['pathvol_' + k] = path / (sr * n)
        o['gap_' + k] = (lp - lp.rolling(n).median()) / sp
        o['accel_' + k] = mp.diff(max(1, n // 4)) / sr
        o['iqr_' + k] = (r.rolling(n).quantile(.75) - r.rolling(n).quantile(.25)) / sr
        o['zc_' + k] = ((lp - mp) * (lp - mp).shift(1) < 0).rolling(n).mean()
    return o


def context(px):
    lp = np.log(px.astype(float)); rt = lp.diff()
    idx = {}
    for c in CCY:
        b = [k for k in px.columns if k[:3] == c]; q = [k for k in px.columns if k[3:] == c]
        s = pd.Series(0.0, index=px.index)
        for k in b:
            s = s + lp[k]
        for k in q:
            s = s - lp[k]
        idx[c] = s / (len(b) + len(q))
    IDX = pd.DataFrame(idx)
    # rolling average pairwise correlation of the whole panel — genuinely new information
    avgc = {}
    for n in (20, 60, 120, 250):
        z = rt.rolling(n).corr(rt.mean(axis=1))
        avgc[n] = z.mean(axis=1)
    return dict(lp=lp, rt=rt, IDX=IDX, IR=IDX.diff(),
                pmean=rt.mean(axis=1), pdisp=rt.std(axis=1), avgc=avgc)


def panel(px, pair, ctx, wins, tag):
    rt, IDX, IR = ctx['rt'], ctx['IDX'], ctx['IR']
    pmean, pdisp = ctx['pmean'], ctx['pdisp']
    r = rt[pair]
    b, q = pair[:3], pair[3:]
    bi, qi, bir, qir = IDX[b], IDX[q], IR[b], IR[q]
    o = {}
    for n in wins:
        k = f'{tag}{n}'
        sr = r.rolling(n).std()
        pv = rt.rolling(n).std()
        o['panelvol_' + k] = pv.median(axis=1)
        o['paneldisp_' + k] = pdisp.rolling(n).mean()
        o['volrank_' + k] = pv.rank(axis=1, pct=True)[pair]
        o['relvol_' + k] = sr / pv.median(axis=1)
        o['corrpanel_' + k] = r.rolling(n).corr(pmean)
        pe = rt.rolling(n).sum().abs() / rt.abs().rolling(n).sum()
        o['efrank_' + k] = pe.rank(axis=1, pct=True)[pair]
        o['paneleff_' + k] = pe.median(axis=1)
        o['reldisp_' + k] = sr / pdisp.rolling(n).mean()
        o['basemom_' + k] = (bi - bi.shift(n)) / bir.rolling(n).std()
        o['quotemom_' + k] = (qi - qi.shift(n)) / qir.rolling(n).std()
        o['legcorr_' + k] = bir.rolling(n).corr(qir)
        o['legvolr_' + k] = bir.rolling(n).std() / qir.rolling(n).std()
        o['legdiv_' + k] = ((bi - bi.shift(n)) - (qi - qi.shift(n))).abs() / sr
        o['usdbeta_' + k] = r.rolling(n).cov(IR['USD']) / IR['USD'].rolling(n).var()
        o['baseef_' + k] = (bi - bi.shift(n)).abs() / bir.abs().rolling(n).sum()
        o['quoteef_' + k] = (qi - qi.shift(n)).abs() / qir.abs().rolling(n).sum()
        o['paneldisprank_' + k] = pdisp.rolling(n).rank(pct=True)
    for n, s in ctx['avgc'].items():
        o[f'avgcorr_{tag}{n}'] = s
    return o


def build(px, pair, ctx):
    lp = ctx['lp'][pair]
    out = {}
    # A daily
    out.update(core(lp, W, 'D'))
    # B weekly / monthly, shifted on own clock then mapped down
    for rule, wins, tg in (('W-FRI', WW, 'W'), ('ME', WM, 'M')):
        s = lp.resample(rule).last().dropna()
        d = core(s, wins, tg)
        for k, v in d.items():
            out[k] = v.shift(1).reindex(lp.index, method='ffill')
    # D panel, three timeframes
    out.update(panel(px, pair, ctx, W, 'D'))
    for rule, wins, tg in (('W-FRI', [4, 8, 13, 26], 'W'), ('ME', [3, 6, 12], 'M')):
        pxr = px.resample(rule).last().dropna()
        c2 = context(pxr)
        d = panel(pxr, pair, c2, wins, tg)
        for k, v in d.items():
            out['p' + k] = v.shift(1).reindex(lp.index, method='ffill')
    base = pd.DataFrame(out, index=lp.index).replace([np.inf, -np.inf], np.nan)

    add = {}
    # C term structure: same family, adjacent windows
    fams = {}
    for c in base.columns:
        f, k = c.rsplit('_', 1)
        fams.setdefault(f, []).append((k, c))
    for f, lst in fams.items():
        lst = sorted(lst, key=lambda x: (x[0][0], int(x[0][1:])))
        for i in range(len(lst) - 1):
            a, b2 = lst[i][1], lst[i + 1][1]
            add[f'ts_{a}_{lst[i+1][0]}'] = base[a] / base[b2].replace(0, np.nan)
    # E z-scores
    for c in base.columns:
        x = base[c]
        add['zz_' + c] = (x - x.rolling(500).mean()) / x.rolling(500).std()
    B2 = pd.DataFrame(add, index=lp.index).replace([np.inf, -np.inf], np.nan)

    # F interactions among strongest confirmed families
    STRONG = [c for c in base.columns
              if c.split('_')[0] in ('panelvol', 'paneldisp', 'bbw', 'maxdd', 'maxdu',
                                     'rngcomp', 'legcorr', 'volratio', 'avgcorr')]
    STRONG = STRONG[:120]
    inter = {}
    Z = {}
    for c in STRONG:
        x = base[c]
        Z[c] = (x - x.rolling(500).mean()) / x.rolling(500).std()
    for a, b2 in itertools.combinations(STRONG, 2):
        inter[f'x_{a}__{b2}'] = Z[a] * Z[b2]
    I = pd.DataFrame(inter, index=lp.index).replace([np.inf, -np.inf], np.nan)
    out = pd.concat([base, B2, I], axis=1)
    return out.astype(np.float32)


if __name__ == '__main__':
    import time
    px = pd.read_csv(os.path.join(ROOTDATA,'/px28.csv'.lstrip('/')), index_col=0, parse_dates=True)
    ctx = context(px)
    t0 = time.time(); S = build(px, 'USDJPY', ctx)
    el = time.time() - t0
    print('%d signals  %.0fs/pair  est %.0f min for 28' % (S.shape[1], el, 28 * el / 60))
    print('coverage median %.2f' % S.notna().mean().median())
