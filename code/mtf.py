import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,os.path.join(_R,'code'))
"""Multi-timeframe regime confluence — Monthly / Weekly / Daily.

Strategies trade the DAILY timeframe. M and W regimes exist only to confirm or
contradict the daily read, so every higher-timeframe label is mapped down to daily bars.

LOOKBACKS — a real hierarchy, each in its own units:
    daily    60 bars   (~3 months)
    weekly   26 bars   (~6 months)
    monthly  12 bars   (1 year)

CAUSALITY — the part that would otherwise manufacture a fake edge:
    a weekly label for the week ending Friday is not usable until the following Monday
    a monthly label is not usable until the first trading day of the next month
    both are shifted on their OWN clock before being reindexed onto daily bars, then
    forward-filled. Daily labels are shifted one bar as usual.

Cut points (direction terciles, volatility terciles) are learned on 1999-2015 ONLY.
"""
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA,'/px28.csv'.lstrip('/'))
SPLIT = '2016-01-01'
NOTIONAL = 100_000
MAJ = {'EURUSD', 'GBPUSD', 'AUDUSD', 'NZDUSD', 'USDCAD', 'USDCHF', 'USDJPY'}
cost = lambda p: 1.5e-4 if p in MAJ else 3.0e-4
TF = dict(D=('D', 60), W=('W-FRI', 26), M=('ME', 12))
DIRS = ['down', 'flat', 'up']
VOLS = ['low', 'med', 'high']


def slope_t(lp, n):
    t = pd.Series(np.arange(len(lp), dtype=float), index=lp.index)
    sx = t.rolling(n).sum(); sy = lp.rolling(n).sum()
    sxx = (t * t).rolling(n).sum(); syy = (lp * lp).rolling(n).sum()
    sxy = (t * lp).rolling(n).sum()
    Sxx = sxx - sx * sx / n; Sxy = sxy - sx * sy / n; Syy = syy - sy * sy / n
    b = Sxy / Sxx
    se = np.sqrt(((Syy - b * Sxy).clip(lower=0) / (n - 2)) / Sxx)
    return (b / se).replace([np.inf, -np.inf], np.nan)


def labels_for(lp_tf, n, ins_mask):
    """Return (dir, vol) labels on the timeframe's own clock, already shifted one bar."""
    r = lp_tf.diff()
    st = slope_t(lp_tf, n)
    vp = r.rolling(n).std().rolling(max(n * 4, 60)).rank(pct=True)
    dq = np.nanquantile(st[ins_mask].dropna(), [1 / 3, 2 / 3]) if st[ins_mask].notna().sum() > 30 \
        else [np.nan, np.nan]
    vq = np.nanquantile(vp[ins_mask].dropna(), [1 / 3, 2 / 3]) if vp[ins_mask].notna().sum() > 30 \
        else [np.nan, np.nan]
    d = pd.Series(np.where(st < dq[0], 'down', np.where(st > dq[1], 'up', 'flat')),
                  index=lp_tf.index).where(st.notna())
    v = pd.Series(np.where(vp < vq[0], 'low', np.where(vp > vq[1], 'high', 'med')),
                  index=lp_tf.index).where(vp.notna())
    return d.shift(1), v.shift(1)          # shifted on its OWN clock


def mr(lp, n=60, e=2.0):
    z = (lp - lp.rolling(n).mean()) / lp.rolling(n).std()
    p = pd.Series(np.nan, index=lp.index)
    p[z <= -e] = 1.; p[z >= e] = -1.; p[z.abs() < .1] = 0.
    return p.ffill().fillna(0.)


def metrics(ret, pos, tot):
    ret = ret.dropna()
    if len(ret) < 100 or ret.std() == 0:
        return None
    tr = int((pos.diff().abs() > 0).sum())
    eq = ret.cumsum(); mdd = -(eq - eq.cummax()).min()
    tot_r = ret.sum(); net = NOTIONAL * tot_r
    w = ret[ret > 0].sum(); l = -ret[ret < 0].sum()
    inpos = pos.abs() > 0; expo = float(inpos.mean())
    return dict(net=net, retdd=tot_r / mdd if mdd > 0 else np.nan,
                pf=w / l if l > 0 else np.nan, trades=tr,
                win=float((ret[inpos.shift(1).fillna(False)] > 0).mean()),
                avg=net / tr if tr else np.nan, expo=expo,
                retexp=net / expo if expo > 0 else np.nan,
                sharpe=ret.mean() / ret.std() * np.sqrt(252),
                data_pct=len(ret) / tot)


def run_surv(COMP):
    """Confluence on the SURVIVOR read rather than on direction.

    The original confluence asks whether D/W/M agree on up-vs-down. The 32
    survivors cannot answer that -- the efficiency ratio is unsigned. What they
    answer is trending-vs-choppy, so this version resamples the composite onto
    each timeframe's own clock, terciles it with IS-only cuts, shifts it on that
    clock, and asks how many timeframes agree the regime is TREND.
    """
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    acc, agree = {}, []
    for p in px.columns:
        lp = np.log(px[p].astype(float)); r = lp.diff(); c = cost(p)
        oos = lp.index >= SPLIT
        cser = COMP[p].reindex(lp.index)
        L = {}
        for tf, (rule, n) in TF.items():
            s = cser if tf == 'D' else cser.resample(rule).last().dropna()
            ins = s.index < SPLIT
            if s[ins].notna().sum() < 30:
                L[tf] = pd.Series(np.nan, index=lp.index, dtype=object); continue
            q = np.nanquantile(s[ins].dropna(), [1 / 3, 2 / 3])
            lab = pd.Series(np.where(s < q[0], 'chop', np.where(s > q[1], 'trend', 'mid')),
                            index=s.index).where(s.notna()).shift(1)
            if tf != 'D':
                lab = lab.reindex(lp.index, method='ffill')
            L[tf] = lab
        for a, b in (('D', 'W'), ('D', 'M'), ('W', 'M')):
            m = L[a].notna() & L[b].notna() & oos
            if m.sum():
                agree.append(dict(pair=p, tfs=a + '-' + b,
                                  regime_agree=float((L[a][m] == L[b][m]).mean())))
        dD = L['D']
        n_agree = ((L['W'] == dD).astype(float) + (L['M'] == dD).astype(float))
        conf = pd.Series(np.where(dD.isna(), np.nan, n_agree), index=lp.index)
        pos = mr(lp).shift(1).fillna(0.)
        net = pos * r - pos.diff().abs().fillna(0) * c
        nb = int(oos.sum())
        acc.setdefault('BASELINE', []).append((net[oos], pos[oos], nb))
        for k, nm in ((2, 'all 3 aligned'), (1, '2 of 3'), (0, 'daily alone')):
            m = oos & (conf == k).values
            if m.sum() > 150:
                acc.setdefault(nm, []).append((net[m], pos[m], nb))
        for st in ('trend', 'mid', 'chop'):
            m = oos & (dD == st).values & (conf == 2).values
            if m.sum() > 150:
                acc.setdefault('aligned ' + st, []).append((net[m], pos[m], nb))
    rows = []
    for cell, lst in acc.items():
        R = pd.concat([a for a, _, _ in lst]); P = pd.concat([b for _, b, _ in lst])
        tb = sum(x for _, _, x in lst)
        mm = metrics(R, P, tb)
        if mm:
            rows.append(dict(cell=cell, **mm))
    T = pd.DataFrame(rows)
    T.to_csv(os.path.join(ROOTOUT, 'mtf_confluence_surv.csv'), index=False)
    A = pd.DataFrame(agree).groupby('tfs').regime_agree.mean().reset_index()
    A.to_csv(os.path.join(ROOTOUT, 'mtf_agreement_surv.csv'), index=False)
    return T, A


def run():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    acc, agree, conf_rows = {}, [], []
    for p in px.columns:
        lp = np.log(px[p].astype(float)); r = lp.diff(); c = cost(p)
        oos = lp.index >= SPLIT
        L = {}
        for tf, (rule, n) in TF.items():
            s = lp if tf == 'D' else lp.resample(rule).last().dropna()
            ins = s.index < SPLIT
            d, v = labels_for(s, n, ins)
            if tf != 'D':
                d = d.reindex(lp.index, method='ffill')
                v = v.reindex(lp.index, method='ffill')
            L[tf] = (d, v)
        # pairwise agreement on direction
        for a, b in (('D', 'W'), ('D', 'M'), ('W', 'M')):
            m = L[a][0].notna() & L[b][0].notna() & oos
            if m.sum():
                agree.append(dict(pair=p, tfs=a + '-' + b,
                                  dir_agree=float((L[a][0][m] == L[b][0][m]).mean()),
                                  vol_agree=float((L[a][1][m] == L[b][1][m]).mean())))
        # confluence: how many timeframes share the daily direction
        dD = L['D'][0]
        n_agree = ((L['W'][0] == dD).astype(float) + (L['M'][0] == dD).astype(float))
        conf = pd.Series(np.where(dD.isna(), np.nan, n_agree), index=lp.index)
        pos = mr(lp).shift(1).fillna(0.)
        net = pos * r - pos.diff().abs().fillna(0) * c
        nb = int(oos.sum())
        acc.setdefault('BASELINE', []).append((net[oos], pos[oos], nb))
        for k, nm in ((2, 'all 3 aligned'), (1, '2 of 3'), (0, 'daily alone')):
            m = oos & (conf == k).values
            if m.sum() > 150:
                acc.setdefault(nm, []).append((net[m], pos[m], nb))
        # aligned AND trending vs aligned AND flat
        for lab, m2 in (('aligned trending', (conf == 2) & dD.isin(['up', 'down'])),
                        ('aligned flat', (conf == 2) & (dD == 'flat'))):
            m = oos & m2.values
            if m.sum() > 150:
                acc.setdefault(lab, []).append((net[m], pos[m], nb))
    rows = []
    for cell, lst in acc.items():
        R = pd.concat([a for a, _, _ in lst]); P = pd.concat([b for _, b, _ in lst])
        tb = sum(x for _, _, x in lst)
        mm = metrics(R, P, tb)
        if mm:
            rows.append(dict(cell=cell, **mm))
    T = pd.DataFrame(rows)
    b = T[T.cell == 'BASELINE'].iloc[0]
    for k, col in (('retexp', 'imp_retexp'), ('retdd', 'imp_retdd'), ('pf', 'imp_pf'),
                   ('win', 'imp_win'), ('avg', 'imp_avg')):
        T[col] = T[k] / b[k] - 1
    A = pd.DataFrame(agree).groupby('tfs')[['dir_agree', 'vol_agree']].mean().reset_index()
    T.to_csv(os.path.join(ROOTOUT,'/mtf_confluence.csv'.lstrip('/')), index=False)
    A.to_csv(os.path.join(ROOTOUT,'/mtf_agreement.csv'.lstrip('/')), index=False)
    return T, A


if __name__ == '__main__':
    T, A = run()
    try:
        import survivors
        TS, AS_ = run_surv(survivors.build())
        pd.set_option('display.width', 240, 'display.max_columns', 25)
        print('=' * 88)
        print('CONFLUENCE ON THE SURVIVOR READ (trend/mid/chop), not on direction')
        print('=' * 88)
        AS_['vs_chance'] = AS_.regime_agree - 1 / 3
        print(AS_.to_string(index=False, float_format=lambda v: '%.3f' % v))
        print()
        print(TS[['cell', 'data_pct', 'sharpe', 'pf', 'trades', 'win', 'avg', 'expo']]
              .sort_values('sharpe', ascending=False)
              .to_string(index=False, float_format=lambda v: '%.3f' % v))
        b = TS[TS.cell == 'BASELINE'].sharpe.iloc[0]
        print('\nbaseline Sharpe %.3f | cells beating it: %d of %d'
              % (b, (TS[TS.cell != 'BASELINE'].sharpe > b).sum(), len(TS) - 1))
    except Exception as e:
        print('survivor confluence unavailable (%s)' % e)
    pd.set_option('display.width', 240, 'display.max_columns', 25)
    f = lambda v: '%.3f' % v
    print('=' * 88); print('DO THE TIMEFRAMES LINE UP?  (OOS, mean across 28 pairs)'); print('=' * 88)
    A['dir_vs_chance'] = A.dir_agree - 1 / 3
    print(A.to_string(index=False, float_format=f))
    print('\nchance agreement on 3 direction states = 0.333')
    order = ['all 3 aligned', 'aligned trending', 'aligned flat', '2 of 3', 'daily alone', 'BASELINE']
    T['o'] = T.cell.map(lambda c: order.index(c) if c in order else 99)
    T = T.sort_values('o')
    print('\n' + '=' * 88); print('DAILY MEAN-REVERSION SLEEVE, BY CONFLUENCE'); print('=' * 88)
    print(T[['cell', 'data_pct', 'net', 'retdd', 'pf', 'trades', 'win', 'avg', 'expo',
             'sharpe']].to_string(index=False, float_format=f))
    print('\n--- improvement vs unfiltered baseline ---')
    print(T[['cell', 'data_pct', 'imp_retexp', 'imp_retdd', 'imp_pf', 'imp_win',
             'imp_avg']].to_string(index=False, float_format=f))
