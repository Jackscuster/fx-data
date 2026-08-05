import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,os.path.join(_R,'code'))
"""9-box regime classification: direction (3) x SECOND AXIS (3).

TWO VERSIONS ARE PRODUCED.

  vol   the original: 60d realised vol as a percentile of its own trailing 500d.
  surv  the second axis replaced by the 32 independent survivors, combined into
        one sign-aligned composite by survivors.py. High = expect straight travel.

The survivor axis is NOT a volatility axis and is not a direction axis either:
the efficiency ratio is |net|/path and carries no sign, so the survivors can say
trending-or-choppy but never up-or-down. Direction still comes from the 60d slope
t-stat in both versions. Labels change accordingly -- low/med/high becomes
chop/mid/trend.

    Trending DOWN | Not Trending | Trending UP
    x  High / Medium / Low volatility

Direction  : t-stat of OLS slope of log price over 60d. Terciles.
Volatility : 60d realised vol as percentile of its own trailing 500d. Terciles.

Cut points are learned on IS (1999-2015) ONLY and applied unchanged to OOS.
Both inputs are computed to t then .shift(1) before use. Backward-looking.

Each box is evaluated against the unfiltered baseline in the STRATEGY_TEMPLATE format,
for both sleeves, so the output is a routing table: which sleeve belongs in which box.
"""
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA,'/px28.csv'.lstrip('/'))
SPLIT = '2016-01-01'
NOTIONAL = 100_000
MAJ = {'EURUSD', 'GBPUSD', 'AUDUSD', 'NZDUSD', 'USDCAD', 'USDCHF', 'USDJPY'}
cost = lambda p: 1.5e-4 if p in MAJ else 3.0e-4
DIRS = ['down', 'flat', 'up']
VOLS = ['low', 'med', 'high']
SURV = ['chop', 'mid', 'trend']


def slope_t(lp, n=60):
    t = pd.Series(np.arange(len(lp), dtype=float), index=lp.index)
    sx = t.rolling(n).sum(); sy = lp.rolling(n).sum()
    sxx = (t * t).rolling(n).sum(); syy = (lp * lp).rolling(n).sum()
    sxy = (t * lp).rolling(n).sum()
    Sxx = sxx - sx * sx / n; Sxy = sxy - sx * sy / n; Syy = syy - sy * sy / n
    b = Sxy / Sxx
    sse = (Syy - b * Sxy).clip(lower=0)
    se = np.sqrt((sse / (n - 2)) / Sxx)
    return (b / se).replace([np.inf, -np.inf], np.nan)


def volpct(r, n=60, look=500):
    v = r.rolling(n).std()
    return v.rolling(look).rank(pct=True)


def mr(lp, n=60, e=2.0):
    z = (lp - lp.rolling(n).mean()) / lp.rolling(n).std()
    p = pd.Series(np.nan, index=lp.index)
    p[z <= -e] = 1.; p[z >= e] = -1.; p[z.abs() < .1] = 0.
    return p.ffill().fillna(0.)


def mo(lp, ns=30, nl=120):
    return np.sign(lp.rolling(ns).mean() - lp.rolling(nl).mean()).fillna(0.)


def metrics(ret, pos, tot_bars):
    ret = ret.dropna()
    if len(ret) < 100 or ret.std() == 0:
        return None
    tr = int((pos.diff().abs() > 0).sum())
    eq = ret.cumsum(); mdd = -(eq - eq.cummax()).min()
    tot = ret.sum(); net = NOTIONAL * tot
    w = ret[ret > 0].sum(); l = -ret[ret < 0].sum()
    inpos = pos.abs() > 0
    expo = float(inpos.mean())
    return dict(net=net, retdd=tot / mdd if mdd > 0 else np.nan,
                pf=w / l if l > 0 else np.nan, trades=tr,
                win=float((ret[inpos.shift(1).fillna(False)] > 0).mean()),
                avg=net / tr if tr else np.nan, expo=expo,
                retexp=net / expo if expo > 0 else np.nan,
                sharpe=ret.mean() / ret.std() * np.sqrt(252),
                data_pct=len(ret) / tot_bars)


def run(axis='vol', COMP=None):
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    LAB = VOLS if axis == 'vol' else SURV
    acc = {}
    counts = {}
    for p in px.columns:
        lp = np.log(px[p].astype(float)); r = lp.diff(); c = cost(p)
        st_ = slope_t(lp)
        vp = volpct(r) if axis == 'vol' else (
            COMP[p].reindex(lp.index) if COMP is not None else pd.Series(np.nan, index=lp.index))
        ins = lp.index < SPLIT; oos = ~ins
        # cut points from IS only
        dq = np.nanquantile(st_[ins].dropna(), [1 / 3, 2 / 3])
        vq = np.nanquantile(vp[ins].dropna(), [1 / 3, 2 / 3]) if vp.notna().any() else [0, 0]
        dl = pd.Series(np.where(st_ < dq[0], 'down',
                       np.where(st_ > dq[1], 'up', 'flat')), index=lp.index).where(st_.notna())
        vl = pd.Series(np.where(vp < vq[0], LAB[0],
                       np.where(vp > vq[1], LAB[2], LAB[1])), index=lp.index).where(vp.notna())
        dl = dl.shift(1); vl = vl.shift(1)          # BACKWARD-LOOKING
        sleeves = dict(mean_reversion=mr(lp).shift(1).fillna(0.),
                       momentum=mo(lp).shift(1).fillna(0.))
        nbars = int(oos.sum())
        for sn, pos in sleeves.items():
            net = pos * r - pos.diff().abs().fillna(0) * c
            acc.setdefault((sn, 'BASELINE'), []).append((net[oos], pos[oos], nbars))
            for d in DIRS:
                for v in LAB:
                    m = oos & (dl == d).values & (vl == v).values
                    if m.sum() < 150:
                        continue
                    acc.setdefault((sn, f'{v}|{d}'), []).append((net[m], pos[m], nbars))
                    counts[(v, d)] = counts.get((v, d), 0) + int(m.sum())
    rows = []
    for (sn, cell), lst in acc.items():
        R = pd.concat([a for a, _, _ in lst])
        P = pd.concat([b for _, b, _ in lst])
        tb = sum(x for _, _, x in lst)
        mm = metrics(R, P, tb)
        if mm:
            rows.append(dict(sleeve=sn, cell=cell, **mm))
    T = pd.DataFrame(rows)
    out = []
    for sn in T.sleeve.unique():
        b = T[(T.sleeve == sn) & (T.cell == 'BASELINE')].iloc[0]
        for _, x in T[T.sleeve == sn].iterrows():
            out.append(dict(x, imp_retexp=x.retexp / b.retexp - 1,
                            imp_retdd=x.retdd / b.retdd - 1, imp_pf=x.pf / b.pf - 1,
                            imp_win=x.win / b.win - 1, imp_avg=x.avg / b.avg - 1))
    T = pd.DataFrame(out)
    fn = 'ninebox.csv' if axis == 'vol' else 'ninebox_surv.csv'
    T.to_csv(os.path.join(ROOTOUT, fn), index=False)
    return T, counts


def compare(A, ca, B, cb):
    """Did populations and Sharpe move when the second axis changed?"""
    ta, tb = sum(ca.values()), sum(cb.values())
    print('\n' + '=' * 92)
    print('WHAT CHANGED: original volatility axis  vs  32-survivor composite axis')
    print('=' * 92)
    print('\nBOX POPULATION (share of OOS bars)')
    print('%-22s %8s      %-22s %8s' % ('vol axis cell', 'share', 'survivor axis cell', 'share'))
    for i in range(3):
        for d in DIRS:
            va, vb = VOLS[2 - i], SURV[2 - i]
            na = ca.get((va, d), 0); nb = cb.get((vb, d), 0)
            print('%-22s %7.1f%%      %-22s %7.1f%%'
                  % ('%s|%s' % (va, d), 100 * na / ta, '%s|%s' % (vb, d), 100 * nb / tb))
    print('\nMEAN-REVERSION SHARPE BY BOX')
    print('%-22s %8s      %-22s %8s   %s' % ('vol axis', 'sharpe', 'survivor axis', 'sharpe', 'delta'))
    for i in range(3):
        for d in DIRS:
            va, vb = VOLS[2 - i], SURV[2 - i]
            ra = A[(A.sleeve == 'mean_reversion') & (A.cell == '%s|%s' % (va, d))]
            rb = B[(B.sleeve == 'mean_reversion') & (B.cell == '%s|%s' % (vb, d))]
            sa = float(ra.sharpe.iloc[0]) if len(ra) else np.nan
            sb = float(rb.sharpe.iloc[0]) if len(rb) else np.nan
            print('%-22s %8.3f      %-22s %8.3f   %+.3f'
                  % ('%s|%s' % (va, d), sa, '%s|%s' % (vb, d), sb, sb - sa))
    ba = A[(A.sleeve == 'mean_reversion') & (A.cell == 'BASELINE')].sharpe.iloc[0]
    ca_ = A[(A.sleeve == 'mean_reversion') & (A.cell != 'BASELINE')]
    cb_ = B[(B.sleeve == 'mean_reversion') & (B.cell != 'BASELINE')]
    print('\nbaseline Sharpe %.3f' % ba)
    print('boxes beating baseline -- vol axis %d of %d, survivor axis %d of %d'
          % ((ca_.sharpe > ba).sum(), len(ca_), (cb_.sharpe > ba).sum(), len(cb_)))
    print('best box -- vol axis %s %.3f, survivor axis %s %.3f'
          % (ca_.loc[ca_.sharpe.idxmax(), 'cell'], ca_.sharpe.max(),
             cb_.loc[cb_.sharpe.idxmax(), 'cell'], cb_.sharpe.max()))
    print('spread across boxes -- vol axis %.3f, survivor axis %.3f'
          % (ca_.sharpe.max() - ca_.sharpe.min(), cb_.sharpe.max() - cb_.sharpe.min()))


if __name__ == '__main__':
    import survivors
    T, counts = run()
    pd.set_option('display.width', 240, 'display.max_columns', 25)
    f = lambda v: '%.3f' % v
    tot = sum(counts.values())
    print('=' * 92); print('9-BOX POPULATION (OOS bar share)'); print('=' * 92)
    grid = pd.DataFrame(index=['high', 'med', 'low'], columns=['down', 'flat', 'up'])
    for (v, d), n in counts.items():
        grid.loc[v, d] = '%.1f%%' % (100 * n / tot)
    print(grid.fillna('-').to_string())

    COMP = None
    try:
        COMP = survivors.build()
    except Exception as e:
        print('survivor composite unavailable (%s)' % e)
    if COMP is not None:
        T2, counts2 = run('surv', COMP)
        compare(T, counts, T2, counts2)

    for sn in T.sleeve.unique():
        d = T[T.sleeve == sn].copy()
        d['ord'] = d.cell.map(lambda c: 99 if c == 'BASELINE' else
                              VOLS[::-1].index(c.split('|')[0]) * 3 + DIRS.index(c.split('|')[1]))
        d = d.sort_values('ord')
        print('\n' + '=' * 92)
        print('%s  |  OOS 2016-2026, costs on' % sn.upper()); print('=' * 92)
        print(d[['cell', 'data_pct', 'net', 'retdd', 'pf', 'trades', 'win', 'avg',
                 'expo', 'sharpe']].to_string(index=False, float_format=f))
        print('--- improvement vs baseline ---')
        print(d[['cell', 'data_pct', 'imp_retexp', 'imp_retdd', 'imp_pf', 'imp_win',
                 'imp_avg']].to_string(index=False, float_format=f))

    print('\n' + '=' * 92); print('ROUTING TABLE — which sleeve wins each box (by Sharpe)'); print('=' * 92)
    piv = T[T.cell != 'BASELINE'].pivot(index='cell', columns='sleeve', values='sharpe')
    piv['winner'] = np.where(piv.mean_reversion > piv.momentum, 'mean_reversion', 'momentum')
    piv['edge'] = (piv.mean_reversion - piv.momentum).abs()
    print(piv.sort_values('edge', ascending=False).to_string(float_format=f))
