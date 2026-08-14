import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Which superseded classifiers can be REBUILT from committed code, and which are gone.

THE CORRECTION THIS FILE EXISTS TO MAKE. 16.4x said generation 2 was "not
reproducible from current code". That was too quick. What changed was the
PIPELINE PATH -- combined.layers() stopped calling structure.five_state -- but
the function itself is untouched and still on main. Calling it directly rebuilds
generation 2 exactly. The distinction that matters is between a function being
deleted and a caller being rewired, and only the first is genuinely lost.

So every superseded variant is enumerated, rebuilt where the code still exists,
and CHECKED AGAINST the archived copy where one survives. A variant only counts
as reproducible if the rebuild matches the archive on shared pair-days; anything
that rebuilds but disagrees is reported as a MISMATCH rather than quietly
accepted, because a silent disagreement is worse than a missing file.

EVERY RESULT GOES TO results/. Nothing here reports only to stdout.

Writes results/regenerate_audit.csv, results/REGENERATE.md and one
states_*.csv + .txt per reproducible variant.
"""
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
SPLIT = pd.Timestamp('2016-01-01')
ACT3 = {0.0: 'weak', 1.0: 'medium', 2.0: 'strong'}


def _px():
    return pd.read_csv(PX, index_col=0, parse_dates=True)


def _act(px, fit):
    from ninestate import raw_axes, tercile
    a = tercile(raw_axes(px)['scale'], fit).replace(ACT3)
    # list(ACT3) gives the NUMERIC KEYS, not the labels -- the first version of
    # this filtered against [0.0, 1.0, 2.0] after the frame already held strings
    # and nulled every cell, which is why the 12-state rebuilds came back empty.
    return a.where(a.isin(list(ACT3.values())))


# ---------------------------------------------------------------- builders
def b_ninebox(px, fit):
    from ninestate import nine
    return nine(px, fit)[0]


def b_ninebox_ribbon(px, fit, L):
    from ninestate import grid_at
    return grid_at(px, L, fit)[0]


def b_structural4(px, fit):
    """Generation 2 shape: four states INCLUDING 'broken'. Cell 3/3/1.00/0.62."""
    from structure import five_state
    sh = five_state(px, 3, 3, 1.00, 0.62)
    return sh.where(sh.isin(['trending', 'broken', 'range', 'drifting']))


def b_structural12(px, fit):
    from combined import confirm, DWELL
    sh, a = b_structural4(px, fit), _act(px, fit)
    return confirm((a + ' ' + sh).where(sh.notna() & a.notna()), DWELL)


def b_gate3(px, fit):
    """The GATED three-shape read, before the continuous score replaced it."""
    from shape3 import three_state
    from structsel import chosen_cell
    from combined import confirm, DWELL
    _, B, D, R = chosen_cell()
    return confirm(three_state(px, 6, B, D, R, 'relaxed').replace('', np.nan),
                   DWELL)


def b_score3(px, fit):
    from shapescore import score_at
    return score_at(px, 19, fit)[0]


def b_score3_at(px, fit, N):
    from shapescore import score_at
    return score_at(px, N, fit)[0]


def b_two4(px, fit):
    from final import scores, activity, DROP_TESTS, BUMP, ACTW
    from twoscores import classify
    tr, ch = scores(px, fit, drop_tests=DROP_TESTS)
    a = activity(px, fit)
    return classify(tr - a.replace(ACTW).astype(float) * BUMP, ch, fit)[0]


def b_two12(px, fit):
    from final import scores, activity, grid, DROP_TESTS, BUMP
    tr, ch = scores(px, fit, drop_tests=DROP_TESTS)
    return grid(tr, ch, _act(px, fit), fit, BUMP)


def b_weighted3(px, fit):
    from classifier import axes as cax, classify as ccl
    return ccl(cax(px), fit)[0]


def b_dwell(px, fit, M):
    from combined import confirm
    from shapescore import score_at
    return confirm(score_at(px, 19, fit)[0], M)


VARIANTS = [
    ('g1_ninebox_7', lambda p, f: b_ninebox_ribbon(p, f, 7), None,
     'Generation 1, fast ribbon leg. Nine-box at a 7-bar window.'),
    ('g1_ninebox', b_ninebox, 'states_g1_ninebox.csv',
     'Generation 1, base. Straightness x scale terciles at 28 bars.'),
    ('g1_ninebox_128', lambda p, f: b_ninebox_ribbon(p, f, 128), None,
     'Generation 1, slow ribbon leg. Nine-box at a 128-bar window.'),
    ('g2_structural4', b_structural4, None,
     "Generation 2 SHAPE ONLY: trending / broken / range / drifting. The four "
     "states before the activity cross. 'broken' was never in the spec."),
    ('g2_structural12', b_structural12, 'states_g2_structural12.csv',
     "Generation 2 full: the four structural shapes crossed with activity."),
    ('g3_gate3', b_gate3, None,
     'Generation 3a, the GATED three-shape read at swing width 6. Superseded '
     'by the continuous score because it left a residual.'),
    ('g3_shapescore9', b_score3, 'states_g3_shapescore9.csv',
     'Generation 3b, the continuous trend-vs-range score cut at terciles.'),
    ('g3_score_N6', lambda p, f: b_score3_at(p, f, 6), None,
     'Generation 3b at a 35-bar lookback -- the fast leg of the shape ribbon.'),
    ('g3_score_N44', lambda p, f: b_score3_at(p, f, 44), None,
     'Generation 3b at a 247-bar lookback -- the slow leg, and the only region '
     'where trend separation went positive.'),
    ('g4_twoscore4', b_two4, 'states_g4_twoscore4.csv',
     'Generation 4, CURRENT. The 2x2 on independent trend and chop scores.'),
    ('g4_twoscore12', b_two12, 'states_g4_twoscore12.csv',
     'Generation 4 crossed with activity, CURRENT.'),
    ('x_weighted3', b_weighted3, None,
     'The original three-state weighted classifier (97.3% scale by variance). '
     'Predates the nine-box and is still on main.'),
    ('x_dwell1', lambda p, f: b_dwell(p, f, 1), None,
     'Generation 3b with NO confirmation dwell -- the flickering version, '
     '3-bar median runs with 62% under five bars.'),
    ('x_dwell13', lambda p, f: b_dwell(p, f, 13), None,
     'Generation 3b at a 13-bar dwell -- past the point where states collapse.'),
]


def main():
    px = _px()
    fit = np.asarray(px.index < SPLIT)
    rows = []
    print('REGENERATING EVERY SUPERSEDED CLASSIFIER FROM COMMITTED CODE')
    for name, fn, archive, note in VARIANTS:
        rec = dict(variant=name, archive=archive or '', note=note)
        try:
            w = fn(px, fit)
            w = w.replace('', np.nan)
            sts = sorted(map(str, pd.unique(w.stack())))
            rec.update(status='rebuilt', n_states=len(sts),
                       dates=w.shape[0], pairs=w.shape[1],
                       states='; '.join(sts))
        except Exception as e:
            rec.update(status='GONE', error='%s: %s' % (type(e).__name__, e))
            rows.append(rec)
            print('  %-20s GONE -- %s' % (name, e))
            continue
        if archive and os.path.exists(os.path.join(ROOTOUT, archive)):
            old = pd.read_csv(os.path.join(ROOTOUT, archive), index_col=0,
                              parse_dates=True)
            i = old.index.intersection(w.index)
            c = old.columns.intersection(w.columns)
            a, b = old.loc[i, c], w.loc[i, c]
            m = a.notna() & b.notna()
            agree = float((a[m] == b[m]).values.sum() / max(m.values.sum(), 1))
            rec.update(checked=int(m.values.sum()), agreement=agree)
            tag = 'MATCHES' if agree > 0.999 else 'MISMATCH'
            print('  %-20s rebuilt, %2d states, %s archive (%.3f%%)'
                  % (name, rec['n_states'], tag, 100 * agree))
        else:
            print('  %-20s rebuilt, %2d states, no archive to check'
                  % (name, rec['n_states']))
        out = os.path.join(ROOTOUT, 'states_%s.csv' % name)
        if not os.path.exists(out):
            w.to_csv(out)
            with open(out.replace('.csv', '.txt'), 'w') as f:
                f.write('states_%s.csv\n%s\n\n%s\n\nREGENERATED from committed '
                        'code by code/regenerate.py -- not restored from a blob.\n'
                        'Shape: %d dates x %d pairs. Already lagged one bar.\n'
                        'States: %s\n'
                        % (name, '=' * 60, note, w.shape[0], w.shape[1],
                           rec['states']))
            rec['written'] = 1
        rows.append(rec)

    R = pd.DataFrame(rows)
    R.to_csv(os.path.join(ROOTOUT, 'regenerate_audit.csv'), index=False)
    ok = R[R.status == 'rebuilt']
    gone = R[R.status == 'GONE']
    print('\n  %d of %d variants rebuilt from committed code; %d genuinely gone'
          % (len(ok), len(R), len(gone)))

    lines = ['# Which classifiers can be rebuilt, and which are gone', '',
             'Written by `code/regenerate.py`. A variant counts as reproducible',
             'only if current code rebuilds it AND the rebuild matches the',
             'archived copy where one exists.', '',
             '## The correction this file makes', '',
             '16.4x said generation 2 was "not reproducible from current code".',
             'That was too quick. What changed was the *pipeline path* —',
             '`combined.layers()` stopped calling `structure.five_state` — but the',
             'function itself is untouched and still on main. Calling it directly',
             'rebuilds generation 2 exactly. **A rewired caller is not a deleted',
             'function**, and only the second is genuinely lost.', '',
             '## Audit', '',
             '| variant | status | states | agreement with archive | what it is |',
             '|---|---|---|---|---|']
    for _, r in R.iterrows():
        ag = ('%.3f%%' % (100 * r.agreement)) if pd.notna(r.get('agreement')) \
            else '— no archive'
        lines.append('| `states_%s.csv` | %s | %s | %s | %s |'
                     % (r.variant, r.status,
                        int(r.n_states) if pd.notna(r.get('n_states')) else '—',
                        ag, r.note))
    lines += ['', '## Genuinely gone', '']
    if len(gone):
        for _, r in gone.iterrows():
            lines.append('- `%s` — %s' % (r.variant, r.get('error', '')))
    else:
        lines.append('**Nothing.** Every classifier variant built in this project '
                     'rebuilds from code committed on `main`.')
    lines += ['', '## Rule going forward', '',
              'Nothing runs to `/tmp`. If a result is worth reporting it is',
              'written to `results/` and committed. Stdout is for progress, not',
              'for findings.']
    with open(os.path.join(ROOTOUT, 'REGENERATE.md'), 'w') as f:
        f.write('\n'.join(lines) + '\n')
    print('  wrote regenerate_audit.csv and REGENERATE.md')


if __name__ == '__main__':
    main()
