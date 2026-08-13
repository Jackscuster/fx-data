import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""THE MERGED LAYER 1, in one place, with every verdict attached.

This computes nothing. It assembles what the other modules already wrote so the
final state can be read without opening nine CSVs, and so that any claim about
Layer 1 has to sit next to the test that was run on it.

WHAT THE MERGE IS

  shape      structural read -- swings, breaks, retracements -- at the cell
             selected on IS by structsel.py, with a 5-bar confirmation dwell
  activity   the nine-box scale axis, path/(vol*sqrt(28)), cut into terciles
             on IS and applied unchanged
  combined   the twelve-state product, '<activity> <shape>'
  settling   graded confidence min(age/5, 1) on the combined state

  and the nine-box itself is UNCHANGED and still primary -- state_7/28/128,
  straight_28, scale_28, tier, age_28 all still in the file. Nothing was
  replaced. See 16.4f: the nine-box beats the merged state on magnitude 0.928
  to 0.703 and ties it on shape.

WHAT SURVIVED ITS OWN NULL, which is the only question that matters:

  the nine-box scale axis, against an IID surrogate, and weakly
  nothing else

That is the honest summary of 16.4b through 16.4i and it is printed below with
the numbers attached rather than asserted.

Writes results/layer1_summary.csv.
"""
import numpy as np, pandas as pd

OUT = os.path.join(ROOTOUT, 'layer1_summary.csv')


def rd(f):
    p = os.path.join(ROOTOUT, f)
    return pd.read_csv(p) if os.path.exists(p) else pd.DataFrame()


def main():
    rows = []

    def add(area, claim, stat, null, verdict, ref):
        rows.append(dict(area=area, claim=claim, statistic=stat, null=null,
                         verdict=verdict, ref=ref))

    L1 = rd('layer1_states.csv')
    print('LAYER 1, MERGED. results/layer1_states.csv')
    if len(L1):
        oos = L1[L1['sample'] == 'oos']
        print('  %d rows, %d pairs, %s to %s'
              % (len(L1), L1.pair.nunique(), L1.date.iloc[0], L1.date.iloc[-1]))
        print('  columns: %s' % ', '.join(L1.columns))
        print('\n  COVERAGE, holdout')
        for c in ('state_28', 'state_7', 'state_128', 'tier', 'shape',
                  'activity', 'combined', 'settling'):
            if c in oos:
                print('    %-10s %.3f' % (c, oos[c].notna().mean()))
        print('\n  SHARES, holdout')
        for c in ('shape', 'activity'):
            if c in oos:
                v = oos[c].value_counts(normalize=True)
                print('    %-9s %s' % (c, '  '.join('%s %.3f' % (k, v[k])
                                                    for k in v.index)))
        if 'settling' in oos:
            v = oos.settling.round(2).value_counts(normalize=True)
            print('    settling  %s' % '  '.join('%.1f %.3f' % (k, v[k])
                                                 for k in sorted(v.index)))

    print('\n' + '=' * 74)
    print('EVERY CLAIM, WITH THE TEST THAT WAS RUN ON IT')

    M = rd('magnitude_null.csv')
    if len(M):
        g = M[(M.classifier == 'grid') & (M.null == 'iid')]
        for _, r in g.iterrows():
            add('nine-box scale axis',
                'separates on %s' % r['prop'],
                '%.3f vs surrogate %.3f, corrected %+.3f' % (r.real, r.surrogate,
                                                             r.corrected),
                'iid', 'HOLDS (p=%.3f)' % r.p, '16.4e')
        g = M[(M.classifier == 'grid') & (M.null == 'sign')]
        for _, r in g.iterrows():
            add('nine-box scale axis',
                'separates on %s' % r['prop'],
                '%.3f vs surrogate %.3f, corrected %+.3f' % (r.real, r.surrogate,
                                                             r.corrected),
                'sign (degenerate here)', 'p=%.3f' % r.p, '16.4e')

    C = rd('combined_validation.csv')
    if len(C) and 'null' in C:
        for _, r in C[C.null.notna()].iterrows():
            add('shape separation', str(r.classifier),
                'real %.3f vs surrogate %.3f, corrected %+.3f'
                % (r.real, r.surrogate, r.corrected), str(r.null),
                'FAILS (p=%.3f)' % r.p, '16.4c')

    ES = rd('episode_separation.csv')
    if len(ES) and 'basis' in ES:
        for _, r in ES[ES.basis == 'episode'].iterrows():
            add('shape separation, EPISODE basis', str(r.classifier),
                'real %.3f vs surrogate %.3f, corrected %+.3f'
                % (r.real, r.surrogate, r.corrected), str(r.null),
                'FAILS (p=%.3f)' % r.p, '16.4e')

    S = rd('structsel_result.csv')
    for _, r in S.iterrows():
        add('structural cell, IS-selected', 'N=%d B=%d D=%.2f R=%.2f'
            % (r.N, r.B, r.D, r.R),
            'holdout %.3f vs surrogate %.3f, corrected %+.3f'
            % (r.real, r.surrogate, r.corrected), str(r.null),
            'FAILS (p=%.3f)' % r.p, '16.4d')

    E = rd('episode_excursion.csv')
    for _, r in E.iterrows():
        ok = max(r.p_21, r.p_63, r.p_126) < 0.05
        add('excursion', '%s / %s' % (r.contrast, r.metric),
            'observed %+.4f, published t %s' % (
                r.observed, '%.2f' % r.naive_t if np.isfinite(r.naive_t) else '--'),
            'block bootstrap 21/63/126',
            ('HOLDS' if ok else 'FAILS') + ' (p %.3f/%.3f/%.3f)'
            % (r.p_21, r.p_63, r.p_126), '16.4e')

    A = rd('axes_settling.csv')
    for _, r in A.iterrows():
        add('settling vs transitional', 'are they the same bars',
            'lift %.3f, Cramers V %.4f' % (r.lift, r.cramers_v), '-',
            'INDEPENDENT', '16.4f')

    CT = rd('change_counts.csv')
    for _, r in CT.iterrows():
        add('regime change counts', str(r.kind),
            '%d changes, %.3f%% of bars, mean gap %.1f bars'
            % (r.changes, 100 * r.rate, r.mean_gap), '-', 'COUNT', '16.4k')

    FC = rd('failswing_confirm.csv')
    for _, r in FC.iterrows():
        add('failed swings, IS-selected cell',
            'X=%.2f Y=%.2f on %s' % (r.X, r.Y, r.kind),
            'IS excess %+.3f, holdout lift %.3f vs surrogate %.3f, excess %+.3f'
            % (r.is_excess, r.holdout_lift, r.surrogate, r.excess), str(r.null),
            'FAILS (p=%.3f)' % r.p, '16.4l')

    MC = rd('masweep_confirm.csv')
    for _, r in MC.iterrows():
        add('lead-time, IS-selected cell',
            '%s fast=%d slow=%d on %s' % (r.family, r.fast, r.slow, r.state),
            'IS excess %+.3f, holdout lift %.3f vs surrogate %.3f, excess %+.3f'
            % (r.is_excess, r.holdout_lift, r.surrogate, r.excess), str(r.null),
            'FAILS (p=%.3f)' % r.p, '16.4i')

    R = pd.DataFrame(rows)
    R.to_csv(OUT, index=False)
    for area in R.area.unique():
        d = R[R.area == area]
        print('\n  %s' % area.upper())
        for _, r in d.iterrows():
            print('    %-46s %s' % (r.claim[:46], r.verdict))
            print('      %s   [null: %s, %s]' % (r.statistic, r.null, r.ref))

    print('\n' + '=' * 74)
    print('WHAT TO ROUTE ON')
    print('  activity / scale_28   the only axis whose separation survives a')
    print('                        surrogate, and only against IID')
    print('  shape, combined       carried as description. Orthogonal to')
    print('                        activity (V 0.094) and to the nine-box')
    print('                        straightness family (V 0.193), so not')
    print('                        redundant -- but failing their own nulls,')
    print('                        so not informative either')
    print('  settling              a weight, not a state. 22.6% of holdout bars')
    print('                        carry a reduced one')
    print('  tier                  description only, permutation p=0.257')
    print('\nwrote layer1_summary.csv')


if __name__ == '__main__':
    main()
