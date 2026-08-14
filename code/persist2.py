import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""The remaining persistence gaps: daily series, and character split by block.

WHAT WAS ALREADY ON DISK and is NOT rebuilt here:

  per-pair character   results/pair_character.csv, pair_ranking.csv,
                       pair_transitions.csv -- all tracked. Only the IS/OOS
                       split and the rank correlation were missing, and that is
                       what pair_character_blocks.csv adds.
  the window sweep     results/shapesplit.csv, 207 rows, N=2..70 which is a
                       measured lookback of 12 to 393 bars, carrying separation,
                       run length and diagonal per state per window. That is the
                       28-to-400 sweep and it is already committed.
  run lengths          results/run_lengths.csv, 3,478 rows across 6 generations
                       x 3 blocks x 29 pair slots.

WHAT WAS GENUINELY MISSING and is written here: the daily series themselves.
layer1_states.csv carries them in long format, one row per pair-day, which is
20 MB and awkward to read a single pair out of. The app needs them wide -- dates
down, pairs across -- so each is written that way, one file per series.

TWO MEASUREMENTS WERE NEVER EXPORTED AT ALL. Boundary test counts and range
containment are components of the chop score inside twoscores.raw_parts and had
no file of their own. They are added here. Boundary tests is the component the
drop-one in 16.4t found was HURTING the chop score (removing it improved
separation by +0.032), so it is persisted as a diagnostic, not as a live input.

Everything is already lagged one bar upstream. Do not shift it again.

Writes results/series_*.csv (8 files) and results/pair_character_blocks.csv,
results/pair_rank_stability.csv.
"""
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
L1 = os.path.join(ROOTOUT, 'layer1_states.csv')
SPLIT = pd.Timestamp('2016-01-01')
SHAPES = ['trending', 'ranging', 'trend-in-range', 'neither']

HDR = ('# %s\n# %s\n# Wide: dates down, 28 pairs across. Already lagged one bar '
       '-- do not shift again.\n# Written by code/persist2.py. Read with '
       "pd.read_csv(path, index_col=0, parse_dates=True, comment='#').\n")


def write_wide(w, name, title, note):
    p = os.path.join(ROOTOUT, 'series_%s.csv' % name)
    with open(p, 'w') as f:
        f.write(HDR % (title, note))
        w.to_csv(f)
    print('  series_%-22s %5d x %2d  %s' % (name + '.csv', w.shape[0],
                                            w.shape[1], title))
    return p


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    fit = np.asarray(px.index < SPLIT)
    S = pd.read_csv(L1, parse_dates=['date'])
    print('PART 1 -- DAILY SERIES, wide')

    for col, name, title, note in [
        ('trend_score', 'trend_score', 'Trend score',
         'Progress in one direction: |net displacement|/path plus the cancelling '
         'swing sequence, standardised on 1999-2015. Higher is more directional.'),
        ('chop_score', 'chop_score', 'Chop score',
         'Respecting boundaries: pullback hold, failed breaks, time inside the '
         'band, midpoint crossings. Higher is more range-bound.'),
        ('m_fail', 'measure_failed_swings', 'Failed swings',
         'Rolling 106-bar count of approaches to a prior extreme that turned '
         'back without clearing it. Feeds chop.'),
        ('m_retr', 'measure_retracement', 'Retracement depth slope',
         'Slope of the last four pullback depths. Negative means shallowing. '
         'Feeds trend.'),
        ('m_space', 'measure_swing_spacing', 'Swing spacing slope',
         'Slope of the last four gaps in bars between confirmed swings. Rising '
         'means a slowing rhythm. Feeds trend.'),
        ('m_panel', 'measure_cross_pair', 'Cross-pair R-squared',
         'Rolling R2 of this pair against the 15 pairs sharing NEITHER of its '
         'currencies. The only measurement that leads state changes.'),
    ]:
        write_wide(S.pivot(index='date', columns='pair', values=col), name,
                   title, note)

    # the two chop components that never had a file
    from twoscores import raw_parts
    T, C = raw_parts(px)
    write_wide(C['tests'], 'measure_boundary_tests', 'Boundary test counts',
               'How many times the band edges were approached and held, over 106 '
               'bars. DIAGNOSTIC ONLY: the drop-one in 16.4t found removing this '
               'from the chop score IMPROVED separation by +0.032, so it is not a '
               'live input.')
    write_wide(C['inside'], 'measure_range_containment', 'Range containment',
               'Share of the last 106 bars spent inside the confirmed swing band.')

    print('\nPART 1 -- PER-PAIR CHARACTER BY BLOCK')
    from paircharacter import labels, per_pair, spearman
    sh, comb = labels(px, fit, pooled=True)
    pairs = list(px.columns)
    A = per_pair(sh, comb, fit, pairs)
    B = per_pair(sh, comb, ~fit, pairs)
    F = per_pair(sh, comb, np.ones(len(px), bool), pairs)
    out = []
    for tag, d in (('is', A), ('oos', B), ('all', F)):
        x = d.copy(); x['block'] = tag
        out.append(x.reset_index())
    Cb = pd.concat(out, ignore_index=True)
    Cb.to_csv(os.path.join(ROOTOUT, 'pair_character_blocks.csv'), index=False)
    print('  pair_character_blocks.csv  %d rows (28 pairs x 3 blocks)' % len(Cb))

    common = A.index.intersection(B.index)
    rows = []
    for k in ('share_trending', 'share_ranging', 'share_trend-in-range',
              'share_neither', 'trendiness', 'med_trending', 'med_ranging'):
        rows.append(dict(statistic=k, rank_corr=spearman(A.loc[common, k],
                                                         B.loc[common, k]),
                         n_pairs=len(common)))
    ra = A.loc[common, 'trendiness'].rank(ascending=False)
    rb = B.loc[common, 'trendiness'].rank(ascending=False)
    R = pd.DataFrame(rows)
    R.to_csv(os.path.join(ROOTOUT, 'pair_rank_stability.csv'), index=False)
    mv = pd.DataFrame({'pair': common, 'rank_is': ra.values,
                       'rank_oos': rb.values,
                       'trendiness_is': A.loc[common, 'trendiness'].values,
                       'trendiness_oos': B.loc[common, 'trendiness'].values})
    mv['rank_move'] = mv.rank_oos - mv.rank_is
    mv.sort_values('rank_is').to_csv(
        os.path.join(ROOTOUT, 'pair_rank_moves.csv'), index=False)
    print('  pair_rank_stability.csv    %d statistics' % len(R))
    print('  pair_rank_moves.csv        %d pairs, IS rank -> OOS rank' % len(mv))
    for _, r in R.iterrows():
        print('    %-22s rank correlation %+.3f' % (r.statistic, r.rank_corr))

    print('\nPART 2 -- FILENAMES')
    src = os.path.join(ROOTOUT, 'nine_states.csv')
    d = pd.read_csv(src, index_col=0, comment='#')
    # A correctly-named COPY. The original keeps its data untouched; only a
    # comment header is added to it, and every reader is made comment-aware.
    dst = os.path.join(ROOTOUT, 'ninebox_state_summary.csv')
    with open(dst, 'w') as f:
        f.write('# Nine-box state summary -- generation 1.\n'
                '# Share of days, median run length and run count for each of the '
                'NINE nine-box states\n'
                '# (strong/medium/weak x trend/transitional/chop) at the 28-bar '
                'window.\n'
                '# This is a 9-row SUMMARY table, not per-day labels and not four '
                'shape states.\n'
                '# Per-day labels for this generation: states_g1_ninebox.csv.\n'
                '# Renamed copy of nine_states.csv, whose name did not say which '
                'classifier it came from.\n')
        d.to_csv(f)
    print('  ninebox_state_summary.csv  correctly-named copy, %d rows' % len(d))

    raw = open(src).read()
    if not raw.startswith('#'):
        with open(src, 'w') as f:
            f.write('# SUPERSEDED NAME -- kept, data untouched.\n'
                    '# This file contains the generation-1 NINE-BOX summary: the '
                    'nine states\n'
                    '# strong/medium/weak x trend/transitional/chop, with share, '
                    'median run\n'
                    '# length and run count. It is a 9-row summary table. It does '
                    'NOT contain\n'
                    '# four shape states and it does NOT contain per-day labels.\n'
                    '# Correctly-named copy: ninebox_state_summary.csv\n'
                    '# Per-day labels:       states_g1_ninebox.csv\n'
                    '# Superseded by:        generation 4, states_g4_twoscore4.csv\n'
                    + raw)
        print('  nine_states.csv            header note added, %d data rows intact'
              % len(d))
    else:
        print('  nine_states.csv            header note already present')
    print('\nwrote 8 series files, 3 character files, 1 renamed copy')


if __name__ == '__main__':
    main()
