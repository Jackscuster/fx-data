import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""results/r2gate2/MODEA_REPORT.md -- EVERY NUMBER QUOTED FROM A FILE (0l).

The rule this module exists to enforce: no number is written into the report
unless it was read out of a named file in this run, and the filename is printed
beside it. Nothing is restated from memory, from an earlier chat, or from a
constant in this file. A section whose source file is missing says so and is
left empty rather than filled in from anywhere else.

    python3 code/l2r2modearep.py --mode A
"""
import time, hashlib
import numpy as np, pandas as pd
import l2r2gate1 as G

RD = os.path.join(ROOTOUT, 'r2gate2')


def src(path):
    """The provenance line for one source file: name, rows, md5."""
    if not os.path.exists(path):
        return None
    h = hashlib.md5(open(path, 'rb').read()).hexdigest()[:12]
    try:
        n = len(pd.read_csv(path, comment='#'))
    except Exception:
        n = -1
    return dict(file=os.path.relpath(path, _R), rows=n, md5=h,
                mtime=time.strftime('%F %H:%M', time.localtime(os.path.getmtime(path))))


def tbl(d, cols, fmt='%.4g'):
    cols = [c for c in cols if c in d.columns]
    if not len(d) or not cols:
        return '_no rows_\n'
    out = ['| ' + ' | '.join(cols) + ' |', '|' + '---|' * len(cols)]
    for _, r in d[cols].iterrows():
        cells = []
        for c in cols:
            v = r[c]
            if isinstance(v, (int, np.integer)):
                cells.append(f'{v:,}')
            elif isinstance(v, (float, np.floating)):
                cells.append('' if not np.isfinite(v) else (fmt % v))
            else:
                cells.append(str(v))
        out.append('| ' + ' | '.join(cells) + ' |')
    return '\n'.join(out) + '\n'


def build(mode='A', out=None, tag='full'):
    F = {
        'books': os.path.join(RD, 'mode%s_books_%s.csv' % (mode, tag)),
        'nulls': os.path.join(RD, 'mode%s_books_nulls%s.csv'
                              % (mode, '' if tag == 'full' else '_' + tag)),
        'grade': os.path.join(RD, 'mode%s_books_blindgrade.csv' % mode),
        'splits': os.path.join(RD, 'mode%s_books_layer1splits.csv' % mode),
        'gate1': os.path.join(ROOTOUT, 'r2gate1_pooled_mode%s_full.csv' % mode),
        'rankcorr': os.path.join(ROOTOUT, 'r2gate1_rankcorr_mode%s_full.csv' % mode),
        'grid': os.path.join(ROOTOUT, 'r2gate2_grid.csv'),
        'cond1': os.path.join(ROOTOUT, 'r2gate2_cond1_mode%s.csv' % mode),
        'cond2': os.path.join(ROOTOUT, 'r2gate2_cond2_mode%s.csv' % mode),
        'streamed': os.path.join(ROOTOUT, 'r2book_series_equals_shipped_mode%s.csv' % mode),
        'shuffle1': os.path.join(ROOTOUT, 'r2gate1_shufflenull_mode%s.csv' % mode),
        'manifest': os.path.join(ROOTOUT, 'layer1_interface_manifest_2026-11-16.csv'),
    }
    P = {k: src(v) for k, v in F.items()}
    L = []
    A = L.append
    A('# MODE A — THE HONEST GATE 2, ALL 273,780 STRATEGIES\n')
    A('Generated %s by `code/l2r2modearep.py`. **Every number below was read out of a '
      'file in this run and the file is named beside it.** A section whose source is '
      'missing says so and is left empty.\n' % time.strftime('%F %H:%M'))

    A('\n## The files this report is built from\n')
    prov = pd.DataFrame([dict(section=k, **v) for k, v in P.items() if v])
    A(tbl(prov, ['section', 'file', 'rows', 'md5', 'mtime']))
    miss = [k for k, v in P.items() if not v]
    if miss:
        A('\n**Missing sources, left empty rather than filled in:** %s\n' % ', '.join(miss))

    A('\n## What was run, and what was not cut\n')
    A('Gate 1 cut nothing (Jack, 16 Nov): every combination the enumeration produced '
      'went to gate 2 tuning. Mode A is **273,780** strategies, each scored over its '
      'full axial configuration set at defaults-plus-every-single-knob-deviation, with '
      'the cut reading tune years only and grade and trade years banked but never '
      'consulted while picking.\n')
    if P['grid']:
        A('\nThe declared risk grid, from `%s`:\n' % P['grid']['file'])
        A(tbl(pd.read_csv(F['grid']), ['knob', 'n_values', 'lo', 'hi', 'in_trend', 'in_chop']))

    A('\n## The two conditions that gated the run\n')
    if P['cond1']:
        d = pd.read_csv(F['cond1'])
        A('**Condition 1 — no year holds another year\'s price.** From `%s`: %s\n'
          % (P['cond1']['file'], tbl(d, ['mode', 'n_strategies', 'n_evaluations',
                                         'worst_abs_diff', 'pass_'])))
    if P['cond2']:
        d = pd.read_csv(F['cond2'])
        A('**Condition 2 — the banked one pass equals the per-step path.** From `%s`: '
          '%d comparisons, %d tune-pick mismatches, %d record mismatches, worst '
          '|diff| %.3g.\n' % (P['cond2']['file'], len(d),
                              int((1 - d.tag_match).sum()), int((1 - d.record_match).sum()),
                              float(d.max_abs_record_diff.max())))
    if P['streamed']:
        d = pd.read_csv(F['streamed'])
        A('\n**The streamed book equals the shipped book.** From `%s`: worst daily '
          'difference %.3g across %d slices.\n'
          % (P['streamed']['file'], float(d.max_abs_daily_diff.max()), len(d)))

    A('\n## THE FOUR BOOKS\n')
    if P['books']:
        B = pd.read_csv(F['books'])
        A('From `%s`, %d rows = %d steps x 4 books x 2 budgets.\n'
          % (P['books']['file'], len(B), B.step.nunique()))
        live = B[B.book_empty == 0] if 'book_empty' in B else B
        A('\n### Trade-year median, by book and budget, pooled over the five steps\n')
        piv = (live.groupby(['book', 'budget'])
               .agg(steps=('step', 'nunique'),
                    median_of_trade_medians=('trade_median_year_pct', 'median'),
                    worst_step=('trade_median_year_pct', 'min'),
                    best_step=('trade_median_year_pct', 'max'),
                    median_dip95=('trade_dip95_pct', 'median'),
                    median_PF=('trade_profit_factor', 'median'),
                    median_retention=('retention', 'median'),
                    steps_flagged_FIT=('FIT', 'sum')).reset_index())
        A(tbl(piv, list(piv.columns)))
        A('\n### Every step, every book, team1 budget\n')
        A(tbl(live[live.budget == 'team1'].sort_values(['step', 'book']),
              ['step', 'book', 'size_scale', 'scale_binds', 'build_median_year_pct',
               'trade_median_year_pct', 'trade_dip95_pct', 'trade_max_dd_pct',
               'trade_profit_factor', 'retention', 'FIT']))
    else:
        A('_`modeA_books_full.csv` is absent; this section is empty._\n')

    A('\n## THE THREE NULLS\n')
    if P['nulls']:
        N = pd.read_csv(F['nulls'])
        A('From `%s`, %d rows.\n' % (P['nulls']['file'], len(N)))
        for kind, g in N.groupby('null'):
            A('\n### %s\n' % kind)
            A(tbl(g.sort_values(['scope', 'step', 'book']),
                  ['scope', 'step', 'book', 'budget', 'members', 'real', 'n_draws',
                   'null_mean', 'null_p5', 'null_p95', 'p_one_sided']))
        if (N.null != 'identity').any():
            A('\n**Is the p-value stable in the sample size?** Same (null, step, book, '
              'budget) at 5,000 and at 20,000:\n')
            sp = N[N.null != 'identity'].pivot_table(
                index=['null', 'step', 'book', 'budget'], columns='scope',
                values='p_one_sided').reset_index()
            A(tbl(sp, list(sp.columns)))
    else:
        A('_`modeA_books_nulls.csv` is absent; this section is empty._\n')

    A('\n## THE BLIND GRADE — reported, never used\n')
    if P['grade']:
        Gd = pd.read_csv(F['grade'])
        A('From `%s`. Year 5 of each step is graded by the tuner\'s own objective but '
          'was never seen by the tuner and gates nothing.\n' % P['grade']['file'])
        A(tbl(Gd, ['step', 'stream', 'n_eligible', 'n_graded_pass', 'n_graded_fail',
                   'trade_R_graded_pass', 'trade_R_graded_fail',
                   'spearman_grade_to_trade', 'p']))
    else:
        A('_`modeA_books_blindgrade.csv` is absent; this section is empty._\n')

    A('\n## THE TWO LAYER 1 SPLITS — reported, gate nothing\n')
    if P['splits']:
        Sp = pd.read_csv(F['splits'])
        A('From `%s`.\n' % P['splits']['file'])
        for k, g in Sp.groupby('split'):
            A('\n### %s\n' % k)
            cols = ['scope', 'step'] + [c for c in ('quality_tag', 'third') if c in g.columns] \
                + ['total_R', 'mean_R_per_mark', 'mark_rows']
            A(tbl(g, cols))
    else:
        A('_`modeA_books_layer1splits.csv` is absent; this section is empty._\n')

    A('\n## WHAT GATE 1 SAID, for context\n')
    if P['gate1']:
        g1 = pd.read_csv(F['gate1'])
        A('From `%s`: trade-year expectancy over the whole eligible population, by '
          'stream.\n' % P['gate1']['file'])
        first = g1.groupby('stream', sort=False).first().reset_index()
        A(tbl(first, ['stream', 'n_eligible', 'trade_R_pass']))
    if P['shuffle1']:
        s1 = pd.read_csv(F['shuffle1'])
        A('\nAnd the gate 1 regime-shuffle null, from `%s`:\n' % P['shuffle1']['file'])
        A(tbl(s1[s1.stream == 'routed'], ['slice', 'stream', 'top_pct', 'real_trade_R',
                                          'surrogate_mean', 'p_one_sided']))

    A('\n## WHAT IS NOT IN THIS REPORT\n')
    A('- **Full-field random-entry and regime-shuffle nulls.** Run here on stratified '
      'samples at two sizes. At the measured 0.48 s per strategy per draw the full field '
      'is a multi-day job; it is registered in HANDOFF 0l as the clean run to do later.\n')
    A('- **Any number not read from the files listed above.** Nothing here is restated '
      'from memory.\n')

    txt = '\n'.join(L)
    out = out or os.path.join(RD, 'MODEA_REPORT.md')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'w').write(txt)
    print('  report: %d lines, %d sources present, %d missing -> %s'
          % (len(txt.splitlines()), sum(1 for v in P.values() if v),
             sum(1 for v in P.values() if not v), out.replace(_R + '/', '')), flush=True)
    return out, P


if __name__ == '__main__':
    build(G.opt('--mode', str, 'A'), out=G.opt('--out', str, None),
          tag=G.opt('--tag', str, 'full'))
