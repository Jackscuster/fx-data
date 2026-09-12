import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""THE CLEAN-FIELD REPORT — one table, assembled from files only.

Reads nothing it does not name and computes nothing it cannot source. Every
number here comes from a file written by the chain; `expectancy` is the mean of
the structure's own daily series in walkforward_daily_*, which is the only KPI
the walk does not already write.

Writes results/walkforward_report_3slice<TAG>.csv and prints the table.
"""
import argparse
import numpy as np, pandas as pd

TAG = '_cleanfield'
KPI = ['members_step1', 'members_step2', 'median_year_pct', 'worst_year_pct',
       'max_dd_pct', 'worst_day_pct', 'dip95_pct', 'profit_factor', 'sortino',
       'calmar', 'expectancy_pct_per_day']
ORDER = ['ALLPASS', 'STABLE', 'PICKED', 'FAMILY_CAP',
         'SLICE_BALANCED', 'NO_CUT', 'NO_CUT_SLICE_BALANCED']


def rd(name, tag=None, need=True):
    p = os.path.join(ROOTOUT, '%s%s.csv' % (name, TAG if tag is None else tag))
    if not os.path.exists(p):
        if need:
            raise SystemExit('MISSING: %s' % p)
        print('   (absent, reported as missing: %s)' % os.path.basename(p))
        return None
    return pd.read_csv(p, comment='#')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--suffix', default='_cleanfield')
    a = ap.parse_args()
    global TAG
    TAG = a.suffix

    S = rd('walkforward_structures_3slice')
    C = rd('walkforward_slicecontrols_3slice', need=False)
    D = rd('walkforward_daily_3slice')
    NI = rd('walkforward_null_identity_summary_3slice', need=False)
    NR = rd('walkforward_null_randomentry_summary_3slice', need=False)
    PS = rd('walkforward_perslice_3slice', need=False)

    frames = [S] + ([C] if C is not None else [])
    A = pd.concat(frames, ignore_index=True, sort=False)

    # expectancy: mean of the structure's own daily series
    D = D.set_index(D.columns[0])
    exp = {}
    for col in D.columns:
        bt, _, st = col.partition('|')
        exp[(bt, st)] = float(pd.to_numeric(D[col], errors='coerce').dropna().mean())
    A['expectancy_pct_per_day'] = [exp.get((r.budget, r.structure), np.nan)
                                   for r in A.itertuples()]

    def pmap(N, col='p_value'):
        if N is None:
            return {}
        return {(r.budget, r.structure): getattr(r, col) for r in N.itertuples()}

    pi, pr = pmap(NI), pmap(NR)
    mi = pmap(NI, 'null_mean') if NI is not None else {}
    mr = pmap(NR, 'null_mean') if NR is not None else {}
    A['identity_null_mean'] = [mi.get((r.budget, r.structure), np.nan) for r in A.itertuples()]
    A['identity_p'] = [pi.get((r.budget, r.structure), np.nan) for r in A.itertuples()]
    A['randomentry_null_mean'] = [mr.get((r.budget, r.structure), np.nan) for r in A.itertuples()]
    A['randomentry_p'] = [pr.get((r.budget, r.structure), np.nan) for r in A.itertuples()]

    A['_o'] = A.structure.map({s: i for i, s in enumerate(ORDER)}).fillna(99)
    A = A.sort_values(['budget', '_o']).drop(columns='_o')
    cols = ['budget', 'structure'] + KPI + ['identity_null_mean', 'identity_p',
                                            'randomentry_null_mean', 'randomentry_p']
    cols = [c for c in cols if c in A.columns]
    out = A[cols]
    p = os.path.join(ROOTOUT, 'walkforward_report_3slice%s.csv' % TAG)
    out.to_csv(p, index=False)

    pd.set_option('display.width', 250)
    print('=== CLEAN FIELD, THREE SLICES — every structure, both budgets ===')
    print(out.to_string(index=False, float_format=lambda v: '%8.3f' % v))
    if PS is not None:
        print('\n=== PER SLICE, each walked alone ===')
        pc = ['slice', 'budget', 'structure', 'field_n'] + \
             [c for c in KPI if c in PS.columns]
        print(PS[pc].to_string(index=False, float_format=lambda v: '%8.3f' % v))
    print('\nwrote %s' % p)


if __name__ == '__main__':
    main()
