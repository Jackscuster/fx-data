import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Pool results/scores7/*.npz into the ONE artefact that gets committed.

results/scores7/ is gitignored -- the repo already carries 438 MB of scores6 and
this batch would add ~200 MB more. What is committed instead is this file: one row
per signal, carrying for every horizon the IS/OOS t, spread, agreement, monotonicity
and decay, plus the block-stability count behind gate 7.

That is everything prep.py and the gauntlet need. What it does NOT preserve is the
raw quintile arrays, so correlations cannot be recomputed in the cloud -- which is
why dedup.py's clusters and independence flags are committed at build time too.

NOTHING IS FILTERED. Signals that cannot be scored are carried with ok=False, same
rule as prep.py. Failures are results.
"""
import numpy as np, pandas as pd
import sig7

MOMPAIRS = 6      # pairs sampled for the momentum-collinearity measurement


def momentum_corr(px):
    """Max |corr| of each base feature with the pair's OWN N-day return.

    px28 is built by triangulating 8 USD rates, so the panel is exactly consistent
    and leg_base - leg_quote IS the pair's return. Any M1 feature built on the
    difference between a pair's two legs is therefore momentum in cross-sectional
    clothing -- xsspr_r* correlates 1.000 with the N-day return, and the rank gap
    inherits most of it. Momentum is on the do-not-build list, so rather than
    silently counting those as cross-sectional discoveries this measures the
    collinearity and carries it per signal. Nothing is dropped; the retention table
    can then separate genuinely panel-wide features from disguised momentum.
    """
    ctx = sig7.context(px)
    pairs = list(px.columns)[:MOMPAIRS]
    acc = {}
    for pair in pairs:
        F = sig7.base_frame(px, pair, ctx)
        lp = ctx['lp'][pair]
        rets = pd.DataFrame({n: lp - lp.shift(n) for n in (20, 60, 120, 250, 500)})
        Fv = F.astype(float)
        for n in rets:
            c = Fv.corrwith(rets[n]).abs()
            for k, v in c.items():
                if np.isfinite(v):
                    acc[k] = max(acc.get(k, 0.0), float(v))
        del F, Fv
        print('  mom-corr %s' % pair, flush=True)
    return acc

SC = os.path.join(ROOTOUT, 'scores7')
OUTF = os.path.join(ROOTOUT, 'signals7_stats.csv')
HOR = {'t': 20, 'e': 60, 'f': 120}          # efficiency horizons
TURN = 'c'                                  # 20d turn frequency


def pool_target(Z, K, pfx):
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
        with np.errstate(invalid='ignore'):
            agree = np.nanmean(np.sign(SPR) == np.sign(spread)[:, None], 1)
        res[tag] = dict(spread=spread, t=spread / se, mono=mono, agree=agree,
                        n=N.sum(1), ct=CT)
    return res


def main():
    files = sorted(f for f in os.listdir(SC) if f.endswith('.npz'))
    if len(files) < 28:
        raise SystemExit('only %d/28 pairs scored -- pooling a subset would '
                         'understate cross-pair agreement' % len(files))
    Z = [np.load(os.path.join(SC, f), allow_pickle=True) for f in files]
    names = [str(x) for x in Z[0]['names']]
    K = len(names)
    print('pooling %d signals x %d pairs' % (K, len(Z)))

    out = pd.DataFrame({'s': names})
    out['mech'] = [sig7.mech_of(n) for n in names]
    out['b'] = 'trend-nonmomentum'

    px = pd.read_csv(os.path.join(ROOTDATA, 'px28.csv'), index_col=0, parse_dates=True)
    print('measuring momentum collinearity...', flush=True)
    MC = momentum_corr(px)
    def basename(n):
        for p, _ in sig7.VAR:
            if p and n.startswith(p):
                return n[len(p):]
        return n
    out['mom_corr'] = [round(MC.get(basename(n), np.nan), 3) for n in names]
    out['disguised_momentum'] = out.mom_corr >= .70

    prim = None
    for tag, H in HOR.items():
        R = pool_target(Z, K, tag)
        i, o = R['i'], R['o']
        out['ti_%d' % H] = np.round(i['t'], 2)
        out['to_%d' % H] = np.round(o['t'], 2)
        out['si_%d' % H] = np.round(i['spread'], 5)
        out['so_%d' % H] = np.round(o['spread'], 5)
        out['ai_%d' % H] = np.round(i['agree'], 3)
        out['ao_%d' % H] = np.round(o['agree'], 3)
        out['mi_%d' % H] = np.round(i['mono'], 3)
        out['mo_%d' % H] = np.round(o['mono'], 3)
        with np.errstate(invalid='ignore', divide='ignore'):
            out['dec_%d' % H] = np.round(np.abs(o['t']) / np.maximum(np.abs(i['t']), .01), 3)
        out['ct_%d' % H] = np.minimum(i['ct'], o['ct'])
        # gate 7 at this horizon
        bs = np.nanmean(np.stack([z['bs' + tag] for z in Z]), axis=0)
        with np.errstate(invalid='ignore'):
            out['tsb_%d' % H] = np.nansum(
                (np.sign(bs) == np.sign(o['spread'])[:, None]) & np.isfinite(bs), axis=1)
        if H == 20:
            prim = (i, o)
        print('  horizon %3dd pooled' % H, flush=True)

    C = pool_target(Z, K, TURN)
    out['cti'] = np.round(C['i']['t'], 2)
    out['cto'] = np.round(C['o']['t'], 2)
    out['cso'] = np.round(C['o']['spread'], 5)
    out['cao'] = np.round(C['o']['agree'], 3)
    out['n'] = (prim[0]['n'] + prim[1]['n']).astype(np.int64)

    # ok mirrors prep.py: unscorable is MARKED, never dropped
    out['ok'] = ((out['ct_20'] >= 20) & out['ti_20'].notna() & out['to_20'].notna())
    out.to_csv(OUTF, index=False)
    sz = os.path.getsize(OUTF) / 1e6
    print('\nwrote %s  (%d rows, %.1f MB)' % (os.path.basename(OUTF), len(out), sz))
    print('scorable %d | unscorable %d (kept, ok=False)'
          % (int(out.ok.sum()), int((~out.ok).sum())))
    print('\nby mechanism:'); print(out.mech.value_counts().to_string())
    dm = out.groupby('mech').disguised_momentum.agg(['sum', 'mean'])
    dm.columns = ['n_disguised', 'share']
    print('\nmomentum collinearity (|corr| with the pair\'s own N-day return >= 0.70):')
    print(dm.to_string(float_format=lambda x: '%.3f' % x))


if __name__ == '__main__':
    main()
