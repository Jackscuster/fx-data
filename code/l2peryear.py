import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""PER-YEAR RETURNS for every built team, at its own budget sizing.

Also the check that settles the 'worst year' question: whether a team's series
runs past 2020-12-31. It should not. Mark-to-market closes every position at the
window boundary, so a 2021 row means a trade escaped the boundary and any
'worst year' drawn from it is a partial-year artefact, not a year.
"""
import json, glob
import numpy as np, pandas as pd
import l2team as TM


def main():
    TM.S.load_costs()
    cands = TM.load_candidates()
    out = {}
    for f in sorted(glob.glob(os.path.join(ROOTOUT, 'team_index_*.json'))):
        lab = os.path.basename(f).replace('team_index', '').replace('.json', '')
        idx = json.load(open(f))
        for tag, o in idx.items():
            sub = cands[cands.cand.isin(o['members'])]
            M, cols = TM.build_matrix(sub, mode='equity', jobs=2)
            if M is None:
                continue
            w = np.array([o['votes'][c] for c in cols])
            d = pd.Series(TM.team_daily(M.values, w), index=M.index) * o['scale']
            yr = d.groupby(d.index.year).sum()
            out[tag] = yr
            stub = [y for y in yr.index if y > 2020]
            print('== %s' % tag, flush=True)
            for y, v in yr.items():
                print('    %d  %7.2f%%%s' % (y, v, '   <-- PAST THE W3 BOUNDARY' if y > 2020 else ''), flush=True)
            full = yr[yr.index <= 2020]
            print('    worst %.2f%% in %d | median %.2f%%' % (yr.min(), yr.idxmin(), yr.median()), flush=True)
            if stub:
                print('    excluding the post-2020 stub: worst %.2f%% in %d | median %.2f%%'
                      % (full.min(), full.idxmin(), full.median()), flush=True)
            print(flush=True)
    pd.DataFrame(out).to_csv(os.path.join(ROOTOUT, 'team_per_year.csv'))
    print('wrote results/team_per_year.csv', flush=True)


if __name__ == '__main__':
    main()
