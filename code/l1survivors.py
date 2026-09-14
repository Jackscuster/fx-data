import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""THE GAUNTLET SURVIVOR SET, FROM A signals.json, AND THE COMPARISON OF TWO.

prep.py prints the survivors and dedup.py clusters them, but the gate-7 list
itself is never written. This re-applies prep.py's gates -- the same seven,
the same noise-calibrated thresholds -- to any signals.json and writes the
list, so two runs on two histories can be set side by side signal by signal.

  python3 code/l1survivors.py results/signals.json                       # list
  python3 code/l1survivors.py A.json B.json --labels 1999+ 2002+ --out X  # compare
"""
import argparse, json
import numpy as np, pandas as pd

GATES = [('sign holds OOS',    lambda x: x.held),
         ('|t| OOS >= 8',      lambda x: x.to.abs() >= 8),
         ('effect >= 0.0221',  lambda x: x.si.abs() >= .0221),
         ('agree >= 0.893',    lambda x: x.ao >= .893),
         ('monotonic >= 0.95', lambda x: x.mo.abs() >= .95),
         ('decay >= 0.60',     lambda x: x.dec >= .6)]


def survivors(path):
    D = pd.DataFrame(json.load(open(path)))
    for c in ('to', 'si', 'ao', 'mo', 'dec', 'tsb'):
        D[c] = pd.to_numeric(D[c], errors='coerce')
    D['held'] = D.held.fillna(False).astype(bool)
    S = D[D.ok.fillna(False).astype(bool)]
    counts = [('scorable', len(S))]
    cur = S
    for nm, f in GATES:
        cur = cur[f(cur).fillna(False)]
        counts.append((nm, len(cur)))
    g7 = cur[cur.tsb.isna() | (cur.tsb >= 4)]
    counts.append(('stable >= 4 of 6', len(g7)))
    g7 = g7.assign(direction=np.where(g7.to > 0, 'trend', 'chop'))
    return D, g7, counts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('paths', nargs='+')
    ap.add_argument('--labels', nargs='*')
    ap.add_argument('--out', default='')
    a = ap.parse_args()
    labels = a.labels or [os.path.basename(os.path.dirname(os.path.dirname(p))) for p in a.paths]
    res = {}
    for lab, p in zip(labels, a.paths):
        D, g7, counts = survivors(p)
        res[lab] = (D, g7)
        print('\n=== %s: %s (%d records) ===' % (lab, p, len(D)))
        for nm, n in counts:
            print('  %-22s %7d' % (nm, n))
        print('  survivors by batch: %s' % g7.groupby('b').size().to_dict())
        print('  by direction: %s' % g7.direction.value_counts().to_dict())
    if len(res) == 2:
        (la, (Da, ga)), (lb, (Db, gb)) = res.items()
        A, B = set(ga.s), set(gb.s)
        both, onlyA, onlyB = A & B, A - B, B - A
        print('\n=== %s vs %s ===' % (la, lb))
        print('  survive both: %d   only %s: %d   only %s: %d' % (len(both), la, len(onlyA), lb, len(onlyB)))
        cols = ['s', 'b', 'f', 'to', 'si', 'ao', 'mo', 'dec', 'tsb']
        rows = []
        for s in sorted(A | B):
            ra = Da[Da.s == s].iloc[0] if (Da.s == s).any() else None
            rb = Db[Db.s == s].iloc[0] if (Db.s == s).any() else None
            r = dict(signal=s, batch=(ra if ra is not None else rb).b, family=(ra if ra is not None else rb).f,
                     **{'in_' + la: s in A, 'in_' + lb: s in B})
            for lab, rr in ((la, ra), (lb, rb)):
                for c in ('to', 'si', 'ao', 'mo', 'dec', 'tsb'):
                    r['%s_%s' % (c, lab)] = (None if rr is None else rr[c])
            # which gate the other run fails, for the ones that change
            if rr is not None and s in (onlyA | onlyB):
                other = rb if s in onlyA else ra
                if other is not None:
                    fails = [nm for nm, f in GATES if not bool(f(pd.DataFrame([other])).iloc[0])]
                    if not fails and not (pd.isna(other.tsb) or other.tsb >= 4):
                        fails = ['stable >= 4 of 6']
                    r['fails_in_other'] = ';'.join(fails) if fails else 'not scored'
            rows.append(r)
        out = pd.DataFrame(rows)
        if a.out:
            out.to_csv(a.out, index=False); print('  wrote %s' % a.out)
        pd.set_option('display.width', 250)
        print(out[['signal', 'batch', 'in_' + la, 'in_' + lb, 'to_' + la, 'to_' + lb,
                   'ao_' + la, 'ao_' + lb, 'tsb_' + la, 'tsb_' + lb] +
                  (['fails_in_other'] if 'fails_in_other' in out else [])].to_string(index=False))


if __name__ == '__main__':
    main()
