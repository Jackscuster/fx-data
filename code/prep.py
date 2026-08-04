import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTDATA,exist_ok=True); os.makedirs(ROOTOUT,exist_ok=True)
sys.path.insert(0,ROOTLIB)
import os, json, numpy as np, pandas as pd

DIRS = [os.path.join(ROOTOUT,'/scores'.lstrip('/')),
        os.path.join(ROOTOUT,'/scores3'.lstrip('/')),
        os.path.join(ROOTOUT,'scores4'),
        os.path.join(ROOTOUT,'scores5'),
        os.path.join(ROOTOUT,'scores6')]
LABELS = ['own-price', 'cross-sectional', 'multi-timeframe', 'regime-v5', 'trend-duration']
OUT = os.path.join(ROOTOUT,''.lstrip('/'))
NBLK = 6          # time-stability blocks; gate 7 wants the sign holding in >= 4


def nn(x):
    """NaN -> None. json.dump would otherwise emit bare NaN, which JSON.parse rejects."""
    x = float(x)
    return None if np.isnan(x) else x


def _target(Z, K, pfx):
    """Pool one target across pairs. pfx: '' single-target dirs, 't' trend, 'c' chop."""
    res = {}
    for tag in ('i', 'o'):
        N = np.zeros((K, 5)); S = np.zeros((K, 5)); SS = np.zeros((K, 5))
        SPR = np.full((K, len(Z)), np.nan); CT = np.zeros(K)
        for i, z in enumerate(Z):
            m = z['q' + pfx + tag].astype(float); c = z['n' + pfx + tag].astype(float)
            w = z['v' + pfx + tag].astype(float)
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
    return res


def pool(d):
    """-> names, trend, chop. chop is None for score dirs holding a single target.

    sc5 writes two targets: qt*/nt*/vt* (forward efficiency) and qc*/nc*/vc*
    (forward turn frequency). sc2-sc4 write plain q*/n*/v*, efficiency only.
    """
    files = sorted(f for f in os.listdir(d) if f.endswith('.npz'))
    Z = [np.load(os.path.join(d, f), allow_pickle=True) for f in files]
    names = [str(x) for x in Z[0]['names']]
    K = len(names)
    keys = set(Z[0].files)
    trend = _target(Z, K, '' if 'qi' in keys else 't')
    chop = _target(Z, K, 'c') if 'qci' in keys else None
    # gate 7 inputs: per-block spreads, averaged across pairs. Only sc6 writes these.
    bs = {}
    for tag in ('t', 'c'):
        k = 'bs' + tag
        if k in keys:
            with np.errstate(invalid='ignore'):
                bs[tag] = np.nanmean(np.stack([z[k] for z in Z]), axis=0)
    return names, trend, chop, bs


def stability(bs, spread):
    """Blocks (of NBLK) whose spread sign matches the pooled OOS sign."""
    if bs is None:
        return None
    s = np.sign(spread)[:, None]
    with np.errstate(invalid='ignore'):
        return np.nansum((np.sign(bs) == s) & np.isfinite(bs), axis=1)


def rd(x, p):
    v = nn(x)
    return None if v is None else round(v, p)


rows = []
for d, batch in zip(DIRS, LABELS):
    nz = len([f for f in os.listdir(d) if f.endswith('.npz')]) if os.path.isdir(d) else 0
    if nz < 28:
        # a half-scored dir would pool a subset of pairs and quietly understate
        # agreement, so it is skipped entirely rather than partially included
        print('skip %s (%d/28 pairs scored)' % (os.path.basename(d), nz))
        continue
    names, R, C, BS = pool(d)
    stb = stability(BS.get('t'), R['o']['spread'])
    stc = stability(BS.get('c'), C['o']['spread']) if C is not None else None
    for j, s in enumerate(names):
        i, o = R['i'], R['o']
        if i['ct'][j] < 20 or o['ct'][j] < 20:
            continue
        if np.isnan(i['t'][j]) or np.isnan(o['t'][j]):
            continue
        r = dict(
            s=s, f=s.rsplit('_', 1)[0], b=batch,
            ti=round(float(i['t'][j]), 2), to=round(float(o['t'][j]), 2),
            si=round(float(i['spread'][j]), 5), so=round(float(o['spread'][j]), 5),
            ai=round(float(i['agree'][j]), 3), ao=round(float(o['agree'][j]), 3),
            mi=round(float(i['mono'][j]), 3), mo=round(float(o['mono'][j]), 3),
            n=int(i['n'][j] + o['n'][j]),
            qo=[round(float(v), 4) for v in o['M'][j]])
        # chop target: present only where the scorer wrote qc*/nc*/vc*.
        if C is None or C['o']['ct'][j] < 20:
            r.update(cti=None, cto=None, cso=None, cao=None, bt=None)
        else:
            ci, co = C['i'], C['o']
            r.update(cti=rd(ci['t'][j], 2), cto=rd(co['t'][j], 2),
                     cso=rd(co['spread'][j], 5), cao=rd(co['agree'][j], 3))
            # which target this signal reads more strongly OOS
            r['bt'] = ('chop' if r['cto'] is not None and abs(r['cto']) > abs(r['to'])
                       else 'trend')
        # gate 7: blocks (of NBLK) holding the OOS sign. None for batches scored
        # before block spreads were stored.
        r['tsb'] = int(stb[j]) if stb is not None else None
        r['csb'] = int(stc[j]) if stc is not None else None
        rows.append(r)

D = pd.DataFrame(rows).drop_duplicates(subset='s')
D['dec'] = (D.to.abs() / D.ti.abs().clip(lower=.01)).round(3)
D['held'] = np.sign(D.ti) == np.sign(D.to)
def clean(v):
    """DataFrame round-trip turns None into NaN in float columns. json.dump would then
    emit bare NaN, which the browser's JSON.parse rejects outright."""
    if isinstance(v, float) and np.isnan(v):
        return None
    if isinstance(v, list):
        return [clean(x) for x in v]
    return v


recs = [{k: clean(v) for k, v in r.items()} for r in D.to_dict('records')]
json.dump(recs, open(os.path.join(OUT, 'signals.json'), 'w'), separators=(',', ':'),
          allow_nan=False)
print('signals %d' % len(D))
for lab in LABELS:
    k = int((D.b == lab).sum())
    if k:
        print('  %-16s %6d' % (lab, k))
print('json %.0f KB' % (os.path.getsize(os.path.join(OUT, 'signals.json')) / 1024))

# ---- the gauntlet: sequential elimination, thresholds unchanged ----
# Gate 6 is a FLOOR only. NEXT_BATCH.md is explicit that no ceiling is added, so a
# signal that is stronger OOS than IS passes here and is caught by gate 7 instead.
GATES = [('sign holds OOS',    lambda x: x.held),
         ('|t| OOS >= 8',      lambda x: x.to.abs() >= 8),
         ('effect >= 0.020',   lambda x: x.si.abs() >= .02),
         ('agree >= 0.85',     lambda x: x.ao >= .85),
         ('monotonic >= 0.95', lambda x: x.mo.abs() >= .95),
         ('decay >= 0.60',     lambda x: x.dec >= .6)]
cur = D
print('\nGAUNTLET')
print('%-22s %8s %8s' % ('gate', 'passing', 'killed'))
for nm, f in GATES:
    before = len(cur)
    cur = cur[f(cur)]
    print('%-22s %8d %8d' % (nm, len(cur), before - len(cur)))
g6 = cur
# gate 7 only applies where block spreads exist
has = g6[g6.tsb.notna()]
g7 = g6[g6.tsb.isna() | (g6.tsb >= 4)]
print('%-22s %8d %8d   (%d of %d scorable)'
      % ('stable >= 4 of 6', len(g7), len(g6) - len(g7),
         int((has.tsb >= 4).sum()), len(has)))
print('\nsurvivors: %d  (%d with block stability measured)' % (len(g7), len(has)))
cols = ['s', 'b', 'ti', 'to', 'si', 'ao', 'mo', 'dec', 'tsb', 'bt']
print(g7.sort_values('to', key=abs, ascending=False).head(25)[cols].to_string(index=False))
