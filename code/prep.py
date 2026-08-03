import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTDATA,exist_ok=True); os.makedirs(ROOTOUT,exist_ok=True)
sys.path.insert(0,ROOTLIB)
import os, json, numpy as np, pandas as pd

DIRS = [os.path.join(ROOTOUT,'/scores'.lstrip('/')),
        os.path.join(ROOTOUT,'/scores3'.lstrip('/'))]
OUT = os.path.join(ROOTOUT,''.lstrip('/'))


def pool(d):
    files = sorted(f for f in os.listdir(d) if f.endswith('.npz'))
    Z = [np.load(os.path.join(d, f), allow_pickle=True) for f in files]
    names = [str(x) for x in Z[0]['names']]
    K = len(names)
    res = {}
    for tag in ('i', 'o'):
        N = np.zeros((K, 5)); S = np.zeros((K, 5)); SS = np.zeros((K, 5))
        SPR = np.full((K, len(Z)), np.nan); CT = np.zeros(K)
        for i, z in enumerate(Z):
            m = z['q' + tag].astype(float); c = z['n' + tag].astype(float)
            w = z['v' + tag].astype(float)
            ok = ~np.isnan(m).any(1) & ~np.isnan(w).any(1)
            c2 = np.where(ok[:, None], c, 0)
            m2 = np.nan_to_num(m); w2 = np.nan_to_num(w)
            N += c2; S += c2 * m2; SS += (c2 - 1) * w2 + c2 * m2 * m2
            SPR[:, i] = np.where(ok, m[:, 4] - m[:, 0], np.nan)
            CT += ok
        M = np.where(N > 0, S / np.maximum(N, 1), np.nan)
        V = np.where(N > 1, (SS - N * M * M) / np.maximum(N - 1, 1), np.nan)
        spread = M[:, 4] - M[:, 0]
        se = np.sqrt(V[:, 4] / np.maximum(N[:, 4], 1) + V[:, 0] / np.maximum(N[:, 0], 1))
        rk = np.arange(5) - 2
        mono = np.array([np.corrcoef(rk, M[j])[0, 1] if not np.isnan(M[j]).any() else np.nan
                         for j in range(K)])
        res[tag] = dict(M=M, spread=spread, t=spread / se, mono=mono,
                        agree=np.nanmean(np.sign(SPR) == np.sign(spread)[:, None], 1),
                        n=N.sum(1), ct=CT)
    return names, res


rows = []
for d, batch in zip(DIRS, ['own-price', 'cross-sectional']):
    names, R = pool(d)
    for j, s in enumerate(names):
        i, o = R['i'], R['o']
        if i['ct'][j] < 20 or o['ct'][j] < 20:
            continue
        if np.isnan(i['t'][j]) or np.isnan(o['t'][j]):
            continue
        rows.append(dict(
            s=s, f=s.rsplit('_', 1)[0], b=batch,
            ti=round(float(i['t'][j]), 2), to=round(float(o['t'][j]), 2),
            si=round(float(i['spread'][j]), 5), so=round(float(o['spread'][j]), 5),
            ai=round(float(i['agree'][j]), 3), ao=round(float(o['agree'][j]), 3),
            mi=round(float(i['mono'][j]), 3), mo=round(float(o['mono'][j]), 3),
            n=int(i['n'][j] + o['n'][j]),
            qi=[round(float(v), 4) for v in i['M'][j]],
            qo=[round(float(v), 4) for v in o['M'][j]]))

D = pd.DataFrame(rows).drop_duplicates(subset='s')
D['dec'] = (D.to.abs() / D.ti.abs().clip(lower=.01)).round(3)
D['held'] = np.sign(D.ti) == np.sign(D.to)
recs = D.to_dict('records')
json.dump(recs, open(os.path.join(OUT, 'app_data.json'), 'w'), separators=(',', ':'))
print('signals %d  | own-price %d  cross-sectional %d'
      % (len(D), (D.b == 'own-price').sum(), (D.b == 'cross-sectional').sum()))
print('json %.0f KB' % (os.path.getsize(os.path.join(OUT, 'app_data.json')) / 1024))
g = D[(D.to.abs() >= 8) & (D.si.abs() >= .02) & (D.ao >= .85) & (D.mo.abs() >= .95)
      & (D.dec >= .6) & D.held]
print('passing strict gates (no time-stability yet): %d' % len(g))
print(g.sort_values('to', key=abs, ascending=False).head(12)[
    ['s', 'ti', 'to', 'si', 'ao', 'mo', 'dec']].to_string(index=False))
