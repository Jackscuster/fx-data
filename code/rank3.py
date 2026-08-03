import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTDATA,exist_ok=True); os.makedirs(ROOTOUT,exist_ok=True)
sys.path.insert(0,ROOTLIB)
import os, numpy as np, pandas as pd
from scipy import stats

SC = os.path.join(ROOTOUT,'/scores3'.lstrip('/'))
files = sorted(f for f in os.listdir(SC) if f.endswith('.npz'))
Z = [np.load(os.path.join(SC, f), allow_pickle=True) for f in files]
names = list(Z[0]['names'])
K = len(names)
print('pairs %d  signals %d' % (len(Z), K))


def pool(tag):
    q, n, v = 'q' + tag, 'n' + tag, 'v' + tag
    N = np.zeros((K, 5)); S = np.zeros((K, 5)); SS = np.zeros((K, 5))
    AG = np.zeros(K); CT = np.zeros(K); SPR = np.zeros((K, len(Z)))
    for i, z in enumerate(Z):
        m, c, w = z[q].astype(float), z[n].astype(float), z[v].astype(float)
        ok = ~np.isnan(m).any(1) & ~np.isnan(w).any(1)
        c2 = np.where(ok[:, None], c, 0); m2 = np.nan_to_num(m); w2 = np.nan_to_num(w)
        N += c2; S += c2 * m2; SS += (c2 - 1) * w2 + c2 * m2 * m2
        SPR[:, i] = np.where(ok, m[:, 4] - m[:, 0], np.nan)
        CT += ok
    M = np.where(N > 0, S / np.maximum(N, 1), np.nan)
    V = np.where(N > 1, (SS - N * M * M) / np.maximum(N - 1, 1), np.nan)
    spread = M[:, 4] - M[:, 0]
    se = np.sqrt(V[:, 4] / np.maximum(N[:, 4], 1) + V[:, 0] / np.maximum(N[:, 0], 1))
    t = spread / se
    agree = np.nanmean(np.sign(SPR) == np.sign(spread)[:, None], axis=1)
    return spread, t, N.sum(1), agree, CT


si, ti, ni, ai, ci = pool('i')
so, to, no, ao, co = pool('o')

R = pd.DataFrame(dict(sig=names, fam=[s.rsplit('_', 1)[0] for s in names],
                      spread_is=si, t_is=ti, n_is=ni, agree_is=ai,
                      spread_oos=so, t_oos=to, n_oos=no, agree_oos=ao))
R = R[(ci >= 20) & (co >= 20)].dropna(subset=['t_is', 't_oos']).copy()
R['held'] = np.sign(R.t_is) == np.sign(R.t_oos)
R['p_is'] = 2 * stats.norm.sf(R.t_is.abs())

# Benjamini-Hochberg FDR at 5% on the IS p-values
R = R.sort_values('p_is').reset_index(drop=True)
m = len(R)
thr = (np.arange(1, m + 1) / m) * 0.05
passing = np.where(R.p_is.values <= thr)[0]
kmax = passing.max() + 1 if len(passing) else 0
R['fdr_pass'] = False
R.loc[:kmax - 1, 'fdr_pass'] = True

R = R.sort_values('t_is', key=abs, ascending=False).reset_index(drop=True)
R.to_csv(os.path.join(ROOTOUT,'/ranked982.csv'.lstrip('/')), index=False)

exp_false = m * 0.05
print('\ntested %d  |  expected |t|>2 by chance: %.0f  |  observed: %d'
      % (m, exp_false, (R.t_is.abs() > 2).sum()))
print('survive BH-FDR 5%%: %d' % R.fdr_pass.sum())
print('of FDR survivors, sign HELD out-of-sample: %d (%.0f%%)'
      % (R[R.fdr_pass].held.sum(), 100 * R[R.fdr_pass].held.mean()))
print('of ALL signals, sign held OOS: %.0f%% (coin flip = 50%%)' % (100 * R.held.mean()))

pd.set_option('display.width', 220)
cols = ['sig', 'spread_is', 't_is', 'agree_is', 't_oos', 'agree_oos', 'held']
top = R[R.held & R.fdr_pass].sort_values('t_is', key=abs, ascending=False)
print('\n=== TOP 25 — significant IS, confirmed OOS, sorted by strength ===')
print(top.head(25)[cols].to_string(index=False, float_format=lambda v: '%.4f' % v))
print('\n=== TOP 15 TREND (confirmed) ===')
print(top[top.t_is > 0].head(15)[cols].to_string(index=False, float_format=lambda v: '%.4f' % v))
print('\n=== TOP 15 CHOP (confirmed) ===')
print(top[top.t_is < 0].head(15)[cols].to_string(index=False, float_format=lambda v: '%.4f' % v))
print('\n=== BY VARIANT ===')
R['var'] = np.where(R.sig.str.startswith('d_'), 'delta',
                    np.where(R.sig.str.startswith('z_'), 'zscore', 'level'))
print(R.groupby('var').agg(n=('sig', 'size'), fdr=('fdr_pass', 'sum'),
                           held=('held', 'mean'), best=('t_is', lambda s: s.abs().max())
                           ).to_string())
