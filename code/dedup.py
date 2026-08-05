import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""GATE 8 — GREEDY DECORRELATION. Runs after the other gates, before survivors report.

HANDOFF_3.md 4 listed 'correlation to already-selected signals' as a gate that was
never computed. Without it a survivor count is not a count of discoveries: a family
that clears the gates clears it at a dozen neighbouring windows and in several
variants at once, and every one is counted separately.

THE RULE. Take the strongest surviving signal by |t OOS|. Drop every remaining
survivor whose absolute correlation with it is above THRESH. Take the next strongest
of what is left. Repeat until nothing remains. The kept signal is its cluster's
representative and is by construction the strongest member.

NOTHING IS DELETED. This is a marking pass. Every record in signals.json keeps its
full score row; survivors additionally get:
    indep    True if kept as a cluster representative, False if absorbed
    clust    the representative it sits under
    nclust   cluster size, on the representative
Non-survivors get null for all three -- not because their data is discarded, but
because decorrelation is only defined over the set being reported.

Correlation is measured on the signal SERIES, rebuilt from each signal's own sig
module so the definitions are guaranteed identical to what was scored, stacked
across a sample of pairs.
"""
import json, time
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
SIG = os.path.join(ROOTOUT, 'signals.json')
OUTF = os.path.join(ROOTOUT, 'survivor_clusters.csv')
CORRF = os.path.join(ROOTOUT, 'survivor_corr.csv')
THRESH = 0.70
NPAIR = 6
MOD = {'own-price': 'sig2', 'cross-sectional': 'sig3', 'multi-timeframe': 'sig4',
       'regime-v5': 'sig5', 'trend-duration': 'sig6',
       'trend-nonmomentum': 'sig7'}
VARP = {'za_': ('z', 250), 'zb_': ('z', 500), 'zc_': ('z', 750), 'zd_': ('z', 120),
        'ze_': ('z', 60), 'ra_': ('r', 500), 'rb_': ('r', 250), 'rc_': ('r', 120),
        'rd_': ('r', 60)}


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


def gates(D):
    """Gates 1-7. Unscorable records can never pass, but are never dropped either."""
    d = D[D.ok.fillna(True)]
    return d[(np.sign(d.ti) == np.sign(d.to)) & (d.to.abs() >= 8) & (d.si.abs() >= .02)
             & (d.ao >= .85) & (d.mo.abs() >= .95)
             & ((d.to.abs() / d.ti.abs().clip(lower=.01)) >= .6)
             & (d.tsb.isna() | (d.tsb >= 4))].copy()


def series_for(surv, px, pairs):
    """Rebuild each survivor's series from its own sig module. -> {name: 1d array}"""
    out = {n: [] for n in surv.s}
    for mod in sorted(set(surv.b.map(MOD))):
        names = list(surv.s[surv.b.map(MOD) == mod])
        m = __import__(mod)
        ctx = m.context(px) if hasattr(m, 'context') else None
        for pair in pairs:
            t0 = time.time()
            if mod == 'sig2':
                F = m.build(px[pair])
            elif mod == 'sig5':
                F = m.build(px, pair, ctx, exclude=frozenset())
            elif mod in ('sig6', 'sig7'):
                F = m.base_frame(px, pair, ctx)
            else:
                F = m.build(px, pair, ctx)
            for n in names:
                base, spec = (split_variant(n) if mod in ('sig6', 'sig7')
                              else (n, None))
                if base in F.columns:
                    out[n].append(apply_variant(F[base].astype(float), spec).values)
                elif n in F.columns:
                    out[n].append(F[n].astype(float).values)
            del F
            print('  %-5s %-7s %.0fs' % (mod, pair, time.time() - t0), flush=True)
    return {k: v for k, v in out.items() if v}


def decorrelate(names, C, order):
    """Greedy: strongest first, absorb everything correlated above THRESH."""
    idx = {n: i for i, n in enumerate(names)}
    keep, clust, taken = [], {}, set()
    for n in order:
        if n in taken or n not in idx:
            continue
        keep.append(n)
        clust[n] = [n]
        taken.add(n)
        for m in order:
            if m in taken or m not in idx:
                continue
            if abs(C[idx[n], idx[m]]) >= THRESH:
                clust[n].append(m)
                taken.add(m)
    return keep, clust


def report(label, sub, names, C, order):
    order = [n for n in order if n in set(sub.s)]
    keep, clust = decorrelate(names, C, order)
    print('\n%s: %d survivors -> %d independent' % (label, len(order), len(keep)))
    return keep, clust


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    S = json.load(open(SIG))
    D = pd.DataFrame(S)
    surv = gates(D).sort_values('to', key=abs, ascending=False)
    print('survivors after gates 1-7: %d' % len(surv))
    print(surv.b.value_counts().to_string())

    pairs = list(px.columns)[:NPAIR]
    print('\nrebuilding survivor series on %d pairs...' % len(pairs))
    ser = series_for(surv, px, pairs)
    names = [n for n in surv.s if n in ser]
    L = min(min(len(a) for v in ser.values() for a in v), 10 ** 9)
    M = np.column_stack([np.concatenate([a[:L] for a in ser[n]]) for n in names])
    C = pd.DataFrame(M, columns=names).corr().values
    pd.DataFrame(C, index=names, columns=names).round(3).to_csv(CORRF)

    order = [n for n in surv.s if n in ser]
    v6 = surv[surv.b == 'trend-duration']
    old = surv[surv.b != 'trend-duration']
    k6, c6 = report('trend-duration (v6)', v6, names, C, order)
    ko, co = report('earlier batches (v2-v5)', old, names, C, order)
    kc, cc = report('COMBINED, all survivors', surv, names, C, order)

    rows = []
    for rep, members in cc.items():
        r = surv[surv.s == rep].iloc[0]
        rows.append(dict(representative=rep, batch=r.b, fam=r.f, to=r.to, si=r.si,
                         ao=r.ao, tsb=r.tsb, stronger_target=r.stronger_target,
                         n_members=len(members),
                         members='|'.join(members)))
    T = pd.DataFrame(rows).sort_values('to', key=abs, ascending=False)
    T.to_csv(OUTF, index=False)

    pd.set_option('display.width', 220, 'display.max_columns', 20)
    print('\n' + '=' * 78)
    print('GATE 8 — INDEPENDENT SURVIVORS, COMBINED SET (|r| < %.2f)' % THRESH)
    print('=' * 78)
    print(T[['representative', 'batch', 'fam', 'to', 'si', 'ao', 'tsb', 'n_members']]
          .to_string(index=False, float_format=lambda x: '%.3f' % x))
    print('\nCLUSTER STRUCTURE — what sits under each representative')
    for _, r in T.iterrows():
        mem = [m for m in r.members.split('|') if m != r.representative]
        if not mem:
            print('  %-20s alone' % r.representative)
        else:
            print('  %-20s absorbs %d:' % (r.representative, len(mem)))
            for i in range(0, len(mem), 4):
                print('      ' + ', '.join(mem[i:i + 4]))

    # mark, never filter
    kset, cmap = set(kc), {}
    for rep, members in cc.items():
        for m in members:
            cmap[m] = rep
    sset = set(surv.s)
    for d in S:
        if d['s'] in sset:
            d['indep'] = bool(d['s'] in kset)
            d['clust'] = cmap.get(d['s'])
            d['nclust'] = len(cc[d['s']]) if d['s'] in cc else None
        else:
            d['indep'] = None; d['clust'] = None; d['nclust'] = None
    json.dump(S, open(SIG, 'w'), separators=(',', ':'), allow_nan=False)
    print('\nmarked %d records (%d survivors, %d independent). Nothing dropped: '
          'signals.json still holds %d rows.'
          % (len(S), len(sset), len(kset), len(S)))


if __name__ == '__main__':
    main()
