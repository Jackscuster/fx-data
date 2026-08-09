import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""TASK 1 report — what does the gauntlet select when it cannot see the holdout?

Reads isonly_stats.csv (IS-A / IS-B statistics, no OOS anywhere), applies the
identical seven gates inside the in-sample period, decorrelates, and only THEN
opens 2016-2026 to report what the cleanly-chosen set actually did.

The comparison that matters is not how many signals overlap. It is whether the
cleanly-selected set holds up out of sample -- because if it does, the current 32
being partly chosen with hindsight cost us nothing real.
"""
import json
import numpy as np, pandas as pd

STATS = os.path.join(ROOTOUT, 'isonly_stats.csv')
SIG = os.path.join(ROOTOUT, 'signals.json')
OUTF = os.path.join(ROOTOUT, 'isonly_survivors.csv')
THRESH = 0.70
NPAIR = 6


def gates(D):
    """The same seven gates, every one computed inside 1999-2015."""
    g = D[(D.cta >= 20) & (D.ctb >= 20) & D.ta.notna() & D.tb.notna()].copy()
    steps = [('sign holds A->B', lambda x: np.sign(x.ta) == np.sign(x.tb)),
             ('|t| B >= 8', lambda x: x.tb.abs() >= 8),
             ('effect A >= 0.0221', lambda x: x.spa.abs() >= .0221),
             ('agree B >= 0.893', lambda x: x.agb >= .893),
             ('monotonic B >= 0.95', lambda x: x.mob.abs() >= .95),
             ('decay B/A >= 0.60', lambda x: (x.tb.abs() / x.ta.abs().clip(lower=.01)) >= .6),
             ('stable >= 4 of 6 IS blocks', lambda x: x.tsb >= 4)]
    print('\nGAUNTLET, IN-SAMPLE ONLY (%d scorable of %d)' % (len(g), len(D)))
    print('%-30s %8s %8s' % ('gate', 'passing', 'killed'))
    cur = g
    for nm, f in steps:
        b = len(cur); cur = cur[f(cur)]
        print('%-30s %8d %8d' % (nm, len(cur), b - len(cur)))
    return cur


def decorrelate(names, px, sigs):
    """Same greedy rule as gate 8, on the IS-selected set."""
    import dedup
    surv = pd.DataFrame(sigs)
    if not len(surv):
        return [], {}
    surv = surv[surv.s.isin(names)].copy()
    if not len(surv):
        return [], {}
    ser = dedup.series_for(surv, px, list(px.columns)[:NPAIR])
    keep_names = [n for n in surv.s if n in ser]
    if not keep_names:
        return [], {}
    L = min(min(len(a) for v in ser.values() for a in v), 10 ** 9)
    M = np.column_stack([np.concatenate([a[:L] for a in ser[n]]) for n in keep_names])
    C = pd.DataFrame(M, columns=keep_names).corr().values
    idx = {n: i for i, n in enumerate(keep_names)}
    order = [n for n in (surv.sort_values('tb_abs', ascending=False).s
                         if 'tb_abs' in surv.columns else pd.Series(keep_names))
             if n in idx]
    keep, clust, taken = [], {}, set()
    for n in order:
        if n in taken:
            continue
        keep.append(n); clust[n] = [n]; taken.add(n)
        for mm in order:
            if mm in taken:
                continue
            if abs(C[idx[n], idx[mm]]) >= THRESH:
                clust[n].append(mm); taken.add(mm)
    return keep, clust


def main():
    D = pd.read_csv(STATS)
    S = json.load(open(SIG))
    OOS = pd.DataFrame(S).set_index('s')
    cur32 = set(OOS[OOS.indep == True].index)
    cur111 = set(OOS[OOS.indep.notna()].index)

    sel = gates(D)
    sel = sel.assign(tb_abs=sel.tb.abs()).sort_values('tb_abs', ascending=False)
    print('\nIS-only survivors before decorrelation: %d' % len(sel))
    print(sel.groupby('b').size().to_string())

    px = pd.read_csv(os.path.join(ROOTDATA, 'px28.csv'), index_col=0, parse_dates=True)
    sigs = [d for d in S if d['s'] in set(sel.s)]
    for d in sigs:
        d['tb_abs'] = float(sel.set_index('s').loc[d['s'], 'tb_abs'])
    keep, clust = decorrelate(list(sel.s), px, sigs)
    print('after decorrelation: %d independent' % len(keep))

    # ---- ONLY NOW is the holdout opened ----
    K = OOS.reindex(keep)
    K = K[K.to.notna()]
    print('\n' + '=' * 78)
    print('HOLDOUT, OPENED ONCE: how the cleanly-selected set did on 2016-2026')
    print('=' * 78)
    held = (np.sign(K.ti) == np.sign(K.to))
    print('  independent signals selected without any OOS information : %d' % len(K))
    print('  of those, OOS sign held                                  : %d (%.0f%%)'
          % (held.sum(), 100 * held.mean()))
    print('  median |t| OOS                                           : %.2f' % K.to.abs().median())
    print('  median |OOS spread|                                      : %.4f' % K.so.abs().median())
    print('  median pair agreement OOS                                : %.3f' % K.ao.median())
    C32 = OOS.loc[sorted(cur32)]
    print('\n  current 32 (selected WITH hindsight) for comparison:')
    print('  median |t| OOS %.2f | median |spread| %.4f | median agreement %.3f'
          % (C32.to.abs().median(), C32.so.abs().median(), C32.ao.median()))

    ov = set(keep) & cur32
    print('\n' + '=' * 78)
    print('OVERLAP')
    print('=' * 78)
    print('  in BOTH sets                              : %d' % len(ov))
    print('  chosen cleanly but NOT in the current 32  : %d' % len(set(keep) - cur32))
    print('  in the current 32 but NOT chosen cleanly  : %d' % len(cur32 - set(keep)))
    only_hind = sorted(cur32 - set(keep))
    if only_hind:
        print('\n  survivors that exist only because the gates saw the holdout:')
        H = OOS.loc[only_hind]
        st = D.set_index('s')
        for n in only_hind:
            row = st.loc[n] if n in st.index else None
            why = 'not scorable in IS' if row is None else (
                'IS-B |t| %.1f' % abs(row.tb) if abs(row.tb) < 8 else
                'IS-A effect %.4f' % abs(row.spa) if abs(row.spa) < .0221 else
                'IS-B agree %.2f' % row.agb if row.agb < .893 else
                'IS-B mono %.2f' % abs(row.mob) if abs(row.mob) < .95 else
                'IS sign flip' if np.sign(row.ta) != np.sign(row.tb) else 'other')
            print('    %-22s %-14s OOS |t| %6.2f   fails: %s'
                  % (n, H.loc[n, 'b'], abs(H.loc[n, 'to']), why))
    out = pd.DataFrame(dict(s=keep))
    out['in_current_32'] = out.s.isin(cur32)
    out = out.merge(OOS[['b', 'ti', 'to', 'si', 'so', 'ao', 'mo']],
                    left_on='s', right_index=True, how='left')
    out.to_csv(OUTF, index=False)
    print('\nwrote %s' % os.path.basename(OUTF))
    return out


if __name__ == '__main__':
    main()
