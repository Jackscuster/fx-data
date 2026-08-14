import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Every generation of the classifier, each in its own clearly-named file.

NOTHING IS DELETED OR OVERWRITTEN. This file only ADDS. Every existing output
stays exactly where it is under its existing name; what is new here is a
generation-numbered copy whose name says which classifier produced it, plus a
manifest that says what each of the old names actually contains.

WHY NOT A COMMENT INSIDE THE OLD CSVs. A '#' header line would become a data row
for pandas, and bundle.py reads several of these straight into the app feed --
nine_states.csv among them. Annotating in place would break the app. The notes
live in results/MANIFEST.md instead, and every new file here carries a companion
.txt header of its own.

THE FOUR GENERATIONS, oldest first:

  g1 ninebox      straightness x scale terciles, 9 states, windows 7/28/128
  g2 structural   swings/breaks/retracements, 4 shapes INCLUDING 'broken',
                  crossed with activity = 12 cells
  g3 shapescore   one continuous trend-vs-range score cut at terciles, 3 shapes,
                  crossed with activity = 9 cells
  g4 twoscore     trend and chop scored independently, 4 shapes from the 2x2,
                  crossed with activity = 12 cells   <-- CURRENT

Run lengths for all of them are recomputed here rather than hunted for, and
written to results/run_lengths.csv -- per state, per generation, pooled and per
pair, on IS and OOS separately.

Writes results/states_g1_ninebox.csv, states_g2_structural12.csv,
states_g3_shapescore9.csv, states_g4_twoscore4.csv, states_g4_twoscore12.csv,
results/run_lengths.csv and results/MANIFEST.md.
"""
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
L1 = os.path.join(ROOTOUT, 'layer1_states.csv')
LG = os.path.join(ROOTOUT, 'layer1_legacy.csv')
SPLIT = pd.Timestamp('2016-01-01')

GENS = [
    ('g1_ninebox', 'state_28', LG,
     'Nine-box, generation 1. Straightness x scale terciles at a 28-bar window. '
     'The 7 and 128 legs are in layer1_legacy.csv as state_7 and state_128.'),
    # g2 is NOT reproducible from current code -- see restore_g2() below.
    ('g3_shapescore9', 'shape', LG,
     'Shape score, generation 3. One continuous trend-versus-range score cut at '
     'in-sample terciles into three shapes. Separates better than g4 (0.261 vs '
     '0.104 on trending) but leaves 41% of days in an ambiguous middle.'),
    ('g4_twoscore4', 'shape2', L1,
     'Two-score, generation 4, CURRENT. Trend and chop scored independently and '
     'classified on the pair: trending / ranging / trend-in-range / neither. '
     'The ambiguous share falls to 20%.'),
    ('g4_twoscore12', 'combined2', L1,
     'Two-score crossed with activity, generation 4, CURRENT. Twelve cells, '
     'activity cut jointly with a 0.75 bump.'),
]


# The generation-2 output cannot be regenerated. combined.layers() was changed to
# the three-shape read, so re-running any current module produces generation 3
# under the old column name. The only intact copy is in git at f597f23, verified
# to hold the twelve 'weak/medium/strong x trending/broken/range/drifting' cells,
# and it is restored from there rather than rebuilt.
G2_COMMIT = 'f597f23'
G2_SRC = 'results/combined_states.csv'


def restore_g2():
    import subprocess
    out = os.path.join(ROOTOUT, 'states_g2_structural12.csv')
    try:
        blob = subprocess.run(['git', 'show', '%s:%s' % (G2_COMMIT, G2_SRC)],
                              cwd=_R, capture_output=True, text=True,
                              check=True).stdout
    except Exception as e:
        print('  COULD NOT RESTORE g2: %s' % e)
        return None
    with open(out, 'w') as f:
        f.write(blob)
    w = pd.read_csv(out, index_col=0, parse_dates=True)
    sts = sorted(map(str, pd.unique(w.stack())))
    assert len(sts) == 12, 'g2 should have 12 cells, got %d' % len(sts)
    assert any('broken' in x for x in sts), "g2 must contain 'broken'"
    with open(out.replace('.csv', '.txt'), 'w') as f:
        f.write('states_g2_structural12.csv\n' + '=' * 60 + '\n\n'
                'Structural, generation 2. Swings, breaks and retracements '
                'giving four shapes INCLUDING \'broken\', crossed with the '
                'activity tercile = 12 cells.\n\n'
                'NOT REPRODUCIBLE FROM CURRENT CODE. combined.layers() was '
                'changed to the three-shape read, so re-running any current '
                'module yields generation 3 under the old column name. This '
                'file is RESTORED VERBATIM from git %s:%s, which is the last '
                'commit where the twelve cells were written.\n\n'
                "'broken' was never in the spec and took 64%% of days; that is "
                'why this generation was replaced.\n\n'
                'Shape: %d dates x %d pairs. Already lagged one bar.\n'
                'States: %s\n' % (G2_COMMIT, G2_SRC, w.shape[0], w.shape[1],
                                   ', '.join(sts)))
    print('  restored states_g2_structural12.csv from git %s  %d x %d, %d cells'
          % (G2_COMMIT, w.shape[0], w.shape[1], len(sts)))
    return w


def runs(v):
    v = v.dropna()
    if len(v) < 10:
        return {}
    gid = (v != v.shift()).cumsum()
    out = {}
    for _, g in v.groupby(gid):
        out.setdefault(g.iloc[0], []).append(len(g))
    return out


def main():
    S = pd.read_csv(L1, parse_dates=['date'])
    L = pd.read_csv(LG, parse_dates=['date'])
    src = {L1: S, LG: L}
    print('PERSISTING EVERY GENERATION. Nothing is deleted or overwritten.')
    rows, man = [], []
    g2 = restore_g2()
    if g2 is not None:
        man.append(('g2_structural12', 'restored from git %s' % G2_COMMIT,
                    '%d x %d' % g2.shape,
                    'Structural generation 2: four shapes INCLUDING `broken` '
                    'crossed with activity = 12 cells. NOT reproducible from '
                    'current code; restored verbatim from history.'))
        for tag, m in (('is', g2.index < SPLIT), ('oos', g2.index >= SPLIT),
                       ('all', np.ones(len(g2), bool))):
            ww = g2[m]
            pooled = {}
            for p in ww.columns:
                rr = runs(ww[p])
                for s_, r in rr.items():
                    pooled.setdefault(s_, []).extend(r)
                    rows.append(dict(generation='g2_structural12', block=tag,
                                     pair=p, state=s_, n_runs=len(r),
                                     median=float(np.median(r)),
                                     mean=float(np.mean(r)), longest=int(max(r)),
                                     share=float((ww[p] == s_).mean())))
            for s_, r in pooled.items():
                rows.append(dict(generation='g2_structural12', block=tag,
                                 pair='ALL', state=s_, n_runs=len(r),
                                 median=float(np.median(r)),
                                 mean=float(np.mean(r)), longest=int(max(r)),
                                 share=float((ww == s_).values.mean())))
    for name, col, path, note in GENS:
        d = src[path]
        if col not in d.columns:
            print('  MISSING: %s (column %s)' % (name, col))
            man.append((name, col, 'MISSING', note))
            continue
        w = d.pivot(index='date', columns='pair', values=col)
        out = os.path.join(ROOTOUT, 'states_%s.csv' % name)
        w.to_csv(out)
        with open(out.replace('.csv', '.txt'), 'w') as f:
            f.write('states_%s.csv\n%s\n\n%s\n\nSource column: %s in %s\n'
                    'Shape: %d dates x %d pairs. Every value is already lagged '
                    'one bar.\nStates: %s\n'
                    % (name, '=' * 60, note, col, os.path.basename(path),
                       w.shape[0], w.shape[1],
                       ', '.join(sorted(pd.unique(w.stack())))))
        print('  wrote states_%s.csv  %d x %d, %d states'
              % (name, w.shape[0], w.shape[1], w.stack().nunique()))
        man.append((name, col, '%d x %d' % w.shape, note))

        # ---- run lengths, recomputed rather than hunted for ----
        for tag, m in (('is', w.index < SPLIT), ('oos', w.index >= SPLIT),
                       ('all', np.ones(len(w), bool))):
            ww = w[m]
            pooled = {}
            for p in ww.columns:
                for s, r in runs(ww[p]).items():
                    pooled.setdefault(s, []).extend(r)
                    rr = runs(ww[p]).get(s, [])
                    if rr:
                        rows.append(dict(generation=name, block=tag, pair=p,
                                         state=s, n_runs=len(rr),
                                         median=float(np.median(rr)),
                                         mean=float(np.mean(rr)),
                                         longest=int(max(rr)),
                                         share=float((ww[p] == s).mean())))
            for s, r in pooled.items():
                rows.append(dict(generation=name, block=tag, pair='ALL',
                                 state=s, n_runs=len(r),
                                 median=float(np.median(r)),
                                 mean=float(np.mean(r)), longest=int(max(r)),
                                 share=float((ww == s).values.mean())))
    R = pd.DataFrame(rows)
    R.to_csv(os.path.join(ROOTOUT, 'run_lengths.csv'), index=False)
    print('\nRUN LENGTHS recomputed: %d rows (%d generations x 3 blocks x '
          '29 pair slots)' % (len(R), R.generation.nunique()))
    print('\n  pooled, all data, median run length per state')
    for g in R.generation.unique():
        d = R[(R.generation == g) & (R.pair == 'ALL') & (R.block == 'all')]
        print('    %-18s %s' % (g, '  '.join(
            '%s %.0f' % (r.state, r['median']) for _, r in
            d.sort_values('share', ascending=False).iterrows())))

    # ---------------- manifest ----------------
    lines = ['# results/ MANIFEST', '',
             'What each classifier output actually contains. Written by',
             '`code/persist.py`. **Nothing in results/ is ever deleted or',
             'overwritten** — superseded work stays readable under its original',
             'name, and this file says what that name means.', '',
             '## The four generations', '',
             '| file | source column | shape | what it is |',
             '|---|---|---|---|']
    for name, col, shp, note in man:
        lines.append('| `states_%s.csv` | `%s` | %s | %s |' % (name, col, shp, note))
    lines += ['', '## Older names that do not say what they hold', '',
              '| file | what it ACTUALLY contains | superseded by |',
              '|---|---|---|',
              '| `nine_states.csv` | A **9-row summary table** of the '
              'generation-1 nine-box states — share, median run length and run '
              'count. It is NOT per-day labels and it does NOT hold four shape '
              'states. | `run_lengths.csv` for run statistics on every '
              'generation |',
              '| `nine_tiers.csv` | Per-day tier labels for generation 1 — which '
              'of the three ribbon windows disagreed. Permutation p=0.257, never '
              'routed on. | nothing; the tier was dropped |',
              '| `combined_states.csv` | Per-day generation-2 labels, wide '
              'format, 4 shapes including `broken` crossed with activity. | '
              '`states_g2_structural12.csv`, same data, named for its generation |',
              '| `structure_states.csv` | Per-day generation-2 SHAPE only, before '
              'the activity cross. | `states_g2_structural12.csv` |',
              '| `shape3_states.csv` | Per-day three-shape labels from the '
              'GATED version of generation 3, before it was replaced by the '
              'continuous score. | `states_g3_shapescore9.csv` |',
              '| `layer1_states.csv` | The CURRENT interface — generation 4 only. |'
              ' — |',
              '| `layer1_legacy.csv` | Generations 1–3 as columns, kept so no '
              'earlier read is lost. | — |', '',
              '## Reading any generation', '', '```python',
              "w = pd.read_csv('results/states_g4_twoscore4.csv',",
              "                index_col=0, parse_dates=True)   # dates x pairs",
              '```', '',
              'Every value is already lagged one bar. Do not shift it again.']
    with open(os.path.join(ROOTOUT, 'MANIFEST.md'), 'w') as f:
        f.write('\n'.join(lines) + '\n')
    print('\nwrote MANIFEST.md, run_lengths.csv and %d generation files'
          % len([m for m in man if m[2] != 'MISSING']))


if __name__ == '__main__':
    main()
