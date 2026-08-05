import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""How many of the gauntlet survivors are actually DIFFERENT signals?

HANDOFF_3.md 4 lists 'correlation to already-selected signals' as a gate that was
never computed. Without it a survivor count is not a count of discoveries: a
family that clears the gates tends to clear it at a dozen neighbouring windows
and in several variants at once, and every one of those is counted separately.

This rebuilds each survivor from its own sig module, stacks the series across a
sample of pairs, and greedily keeps a signal only when its absolute correlation
with everything already kept is below THRESH. Survivors are considered strongest
first, so the representative of each cluster is its best member.

The output is the number that should be quoted as 'new signals found'. The raw
survivor count is an upper bound on it, not a substitute.
"""
import json, time
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
SIG = os.path.join(ROOTOUT, 'signals.json')
OUTF = os.path.join(ROOTOUT, 'survivor_clusters.csv')
THRESH = 0.70
NPAIR = 6                       # pairs sampled for the correlation estimate
VARP = {'za_': ('z', 250), 'zb_': ('z', 500), 'zc_': ('z', 750),
        'zd_': ('z', 120), 'ze_': ('z', 60),
        'ra_': ('r', 500), 'rb_': ('r', 250), 'rc_': ('r', 120), 'rd_': ('r', 60)}


def split_variant(name):
    for p, spec in VARP.items():
        if name.startswith(p):
            return name[len(p):], spec
    return name, None


def apply_variant(x, spec):
    if spec is None:
        return x
    kind, n = spec
    if kind == 'z':
        return (x - x.rolling(n).mean()) / x.rolling(n).std()
    return x.rolling(n).rank(pct=True)


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    S = json.load(open(SIG))
    D = pd.DataFrame(S)
    surv = D[(np.sign(D.ti) == np.sign(D.to)) & (D.to.abs() >= 8) & (D.si.abs() >= .02)
             & (D.ao >= .85) & (D.mo.abs() >= .95)
             & ((D.to.abs() / D.ti.abs().clip(lower=.01)) >= .6)
             & (D.tsb.isna() | (D.tsb >= 4))].copy()
    surv = surv.sort_values('to', key=abs, ascending=False)
    v6 = surv[surv.b == 'trend-duration']
    other = surv[surv.b != 'trend-duration']
    print('survivors %d  (v6 %d, earlier batches %d)' % (len(surv), len(v6), len(other)))
    if len(other):
        print('earlier-batch survivors are not rebuilt here (they need sig2-sig5);')
        print('they are reported separately and counted as their own families.')

    import sig6
    pairs = list(px.columns)[:NPAIR]
    ctx = sig6.context(px)
    need = {}
    for n in v6.s:
        base, spec = split_variant(n)
        need.setdefault(base, []).append((n, spec))

    series = {n: [] for n in v6.s}
    for pair in pairs:
        t0 = time.time()
        F = sig6.base_frame(px, pair, ctx)
        for base, lst in need.items():
            if base not in F.columns:
                continue
            x = F[base].astype(float)
            for n, spec in lst:
                series[n].append(apply_variant(x, spec).values)
        del F
        print('  %s %.0fs' % (pair, time.time() - t0), flush=True)

    names = [n for n in v6.s if series[n]]
    M = np.column_stack([np.concatenate(series[n]) for n in names])
    C = pd.DataFrame(M, columns=names).corr().abs().values
    print('correlation matrix %d x %d over %d pairs' % (C.shape[0], C.shape[1], len(pairs)))

    keep, cluster = [], {}
    for i, n in enumerate(names):
        hit = None
        for j, k in enumerate(keep):
            if C[i, names.index(k)] >= THRESH:
                hit = k
                break
        if hit is None:
            keep.append(n)
            cluster[n] = [n]
        else:
            cluster[hit].append(n)

    rows = []
    for rep, members in cluster.items():
        r = v6[v6.s == rep].iloc[0]
        rows.append(dict(representative=rep, fam=r.fam, to=r.to, si=r.si, ao=r.ao,
                         tsb=r.tsb, bt=r.bt, n_members=len(members),
                         members='|'.join(members)))
    T = pd.DataFrame(rows).sort_values('to', key=abs, ascending=False)
    T.to_csv(OUTF, index=False)

    pd.set_option('display.width', 200, 'display.max_columns', 20)
    print('\n' + '=' * 78)
    print('DISTINCT SURVIVORS AFTER CORRELATION DEDUP (|r| < %.2f)' % THRESH)
    print('=' * 78)
    print(T[['representative', 'fam', 'to', 'si', 'ao', 'tsb', 'bt', 'n_members']]
          .to_string(index=False, float_format=lambda x: '%.3f' % x))
    print('\n%d v6 survivors collapse to %d distinct signals.' % (len(names), len(keep)))
    print('largest clusters:')
    for _, r in T.nlargest(5, 'n_members').iterrows():
        print('  %-18s %2d members  (%s)' % (r.representative, r.n_members, r.fam))


if __name__ == '__main__':
    main()
