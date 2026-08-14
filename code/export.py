import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""THE LAYER 1 INTERFACE. One row per pair per day, the nine-state label at each
of the three ribbon windows, and the agreement tier.

WHY THIS FILE EXISTS. The estimator's output was scattered. The nine-state labels
at 7 / 28 / 128 existed in exactly one place -- as integer codes nested inside
app_explorer.json, a feed built for the chart. The tier was in nine_tiers.csv
with no states beside it. classifier_states.csv holds the older THREE-state
low/mid/high read, and ribbon_config.csv holds the same four tier words computed
from different windows and a different classifier, so the two are easy to confuse
and are not interchangeable.

Anything downstream therefore had to reconstruct the estimator's answer from a UI
feed or re-derive it from price. Both are ways to drift away from what Layer 1
actually said. This is the one file to read instead.

IT COMPUTES NOTHING NEW. Every column is imported from ninestate.py -- the same
grid_at, tiers_from and age_of that produce nine_tiers.csv and the explorer feed.
If this file and those disagree, this file is wrong. Two assertions at the end
check exactly that against nine_tiers.csv and app_explorer.json, and halt the run
on a mismatch.

SCHEMA of results/layer1_states.csv

  date         ISO date
  pair         one of the 28
  state_7      nine-state label on the 7-day window    \\
  state_28     nine-state label on the 28-day window    > 'strong trend' ... 'weak chop'
  state_128    nine-state label on the 128-day window  /
  tier         all agree | fast apart | medium apart | slow apart | all differ
               (a complete, symmetric enumeration of which windows disagree;
                DESCRIPTION ONLY -- tested flat on excursion, see HANDOFF 16.2b)
  age_28       bars the 28-day state has held, 1 on its first bar
  straight_28  straightness axis, |net| / path over 28 bars
  scale_28     scale axis, path over 28 bars in the pair's own vol units
  shape        trending | drifting | range -- THREE shapes, NO residual and no
               fourth category. A CONTINUOUS trend-versus-range score cut at IS
               terciles, so every bar lands somewhere. The score sums four
               standardised structural readings -- cancelling swing sequence,
               boundary distance, break-and-hold, and pullback -- with equal
               weights. Equals shape_106. 5-bar confirmation dwell.
  shape_35     the same score at a 35-bar median lookback  \  the shape ribbon,
  shape_106    ...at 106 bars, the LOCKED base              >  the analogue of
  shape_247    ...at 247 bars                              /   state_7/28/128.
  trend_score  the TREND axis of the two-score classifier (TWO_SCORES.md), raw
               and continuous. Higher is more directional.
  chop_score   the CHOP axis, raw and continuous. Higher is more range-bound.
               The two are only -0.35 correlated, so they are genuinely two
               readings and not one axis wearing two names (16.4r). Chop is the
               stronger of the two: it holds up out of sample (0.151 -> 0.156)
               while trend halves (0.106 -> 0.053). See 16.4u.
  shape2       the 2x2 on that pair -- trending | ranging | trend-in-range |
               neither. 'trend-in-range' is measurement overlap on most bars,
               not a real regime; see 16.4t before using it.
  combined2    '<activity> <shape2>', twelve cells, activity cut JOINTLY with a
               0.75 bump so a weak-activity bar must clear a higher trend bar.
               Chosen on IS, and the margin over a separate cut is 0.002 -- a
               tie in practice.
  shape_score  THE RAW SCORE at the base window, before any cut. The tercile
               boundaries are a DECISION, not a discovery: the score is one
               continuous right-skewed spread with a single KDE peak at every
               bandwidth and excess kurtosis +1.44, not three clusters (16.4q).
               This column is here so Layer 2 can cut it somewhere else without
               re-deriving it. Higher is more trending.
               Suffixes are the MEASURED median distance back to the anchoring
               swing, not the swing width. The lookback is quantised because the
               swing width is an integer; 12/35/132 are the achievable values
               nearest the ribbon's own 7/28/128.
  activity     weak | medium | strong -- the scale tercile, the same axis as
               scale_28, cut on IS and applied unchanged
  settling     graded confidence in the combined state, min(age/5, 1). 0.2 on
               the first bar a state is adopted, 1.0 from the fifth. NOT a
               binary flag: three fast signals were tested for whether they fire
               before a confirmed change more often than chance and none beat
               its own surrogate (16.4g), so the 4-bar confirmation lag is
               accepted and carried as a weight rather than hidden.
  combined     '<activity> <shape>', the twelve-state product. DESCRIPTION ONLY:
               its shape separation is BELOW its own surrogate on the holdout,
               so it describes size honestly and shape not at all. See 16.4c.
  sample       is | oos, split at 2016-01-01

READING IT.

  s = pd.read_csv('results/layer1_states.csv', parse_dates=['date'])
  s = s[s.sample == 'oos']                      # thresholds were learned on 'is'
  wide = s.pivot(index='date', columns='pair', values='state_28')

THE CONTRACT, so Layer 2 can rely on it.

  - Every value is already lagged one bar. A row dated D is safe to act on at D's
    close. Do not shift it again, and do not shift it back.
  - 28 is the base window. The grid, the transition matrix and every published
    excursion number are measured on it. state_7 and state_128 are the ribbon
    either side; the tier is how they agree.
  - The tier compares FAMILY only -- trend / transitional / chop. Window
    disagreement is about cleanliness, not about size, so 'strong trend' and
    'weak trend' count as agreeing.
  - age_28 is a confidence weight, not a state, and a weak one: the hazard curve
    is fully reproduced by a volatility-clustering surrogate.
  - shape, activity and combined carry the same warning as the tier, for the
    same reason: they are descriptions that failed their own null. Route on
    activity if you route on anything -- it is the only axis in this file whose
    separation survives a surrogate. Do not route on shape.
  - The tier predicts NOTHING measurable. Permutation p=0.257 on MFE/|MAE| and
    worse on the other three metrics. It is carried as a description of the
    windows, not as a signal. Do not route on it.
  - Cut points are fitted on 1999-2015 and applied unchanged afterwards, so a
    historical row never changes when new data arrives. Only the tail moves.
  - Rows where all three windows are still warming up are dropped. Rows where
    only the slow window is short are kept, with state_128 and tier empty.
  - No money metrics here. Sizing, cost and PnL start at Layer 2.

Sorted by date then pair, so a rebuild appends rather than rewrites -- the file is
committed and a pair-major sort would rewrite every line each day.

Writes results/layer1_states.csv.
"""
import json
import numpy as np, pandas as pd
from ninestate import MULTI, STATES, SPLIT, grid_at, age_of, tiers_from, raw_axes
from combined import layers, product, confirm, DWELL
from structsel import chosen_cell

PX = os.path.join(ROOTDATA, 'px28.csv')
OUT = os.path.join(ROOTOUT, 'layer1_states.csv')
TIERCSV = os.path.join(ROOTOUT, 'nine_tiers.csv')
EXPL = os.path.join(ROOTOUT, 'app_explorer.json')
BASE = 28                      # the medium ribbon window, and ninestate's W
# THE CURRENT CLASSIFIER. Two independent scores, four shape states, a 106-bar
# window, activity from the scale axis, and a graded confidence on age.
COLS = ['date', 'pair', 'trend_score', 'chop_score', 'shape2', 'activity',
        'scale_28', 'combined2', 'settling', 'm_fail', 'm_retr', 'm_space',
        'm_panel', 'sample']
# SUPERSEDED, written to layer1_legacy.csv rather than deleted. Three earlier
# generations: the nine-box (state_7/28/128, straight_28, tier, age_28), the
# single-axis shape score (shape_35/shape/shape_247/shape_score) and the
# nine-state product built on it (combined).
LEGACY = ['date', 'pair', 'state_7', 'state_28', 'state_128', 'tier', 'age_28',
          'straight_28', 'shape_35', 'shape', 'shape_247', 'shape_score',
          'combined', 'sample']


def build(px):
    fit = px.index < SPLIT
    multi = {L: grid_at(px, L, fit) for L in MULTI}
    tier = tiers_from(multi)
    age = age_of(multi[BASE][0])
    A = raw_axes(px, BASE)
    cell = chosen_cell()
    sh, act = layers(px, fit, cell)
    sh, act = sh.reindex_like(px), act.reindex_like(px)
    comb = product(sh, act, DWELL)
    # graded settling confidence: a state is fully weighted only once it has
    # held as long as it took to confirm. See 16.4g for why this is a weight
    # rather than a fast signal.
    from shape3 import RIBBON
    from shapescore import score_at
    from shape3 import N_SCORE
    rib, scr = {}, None
    for n, lb in RIBBON:
        rib[lb], sc_ = score_at(px, n, fit)
        if n == N_SCORE:
            scr = sc_
    # the two-score classifier, at the settings chosen on IS in final.py
    from final import scores as _sc, activity as _act, grid as _grid, DROP_TESTS, BUMP
    from twoscores import classify as _cls
    _tr, _ch = _sc(px, fit, drop_tests=DROP_TESTS)
    _a = _act(px, fit)
    _s2, _ = _cls(_tr - _a.replace({'weak': 1.0, 'medium': 0.0,
                                    'strong': -1.0}).astype(float) * BUMP,
                  _ch, fit)
    _c2 = _grid(_tr, _ch, _a, fit, BUMP)
    from measures import build_measures
    _M, _ = build_measures(px)
    cage = age_of(comb)
    settle = (cage / DWELL).clip(upper=1.0)
    # NO SECOND CONFIRM HERE. layers() now returns score_at output, which
    # already applies the 5-bar dwell internally. This line used to read
    # `sh = confirm(sh, DWELL)` -- correct when the shape came from five_state,
    # which does not dwell, and a DOUBLE DWELL once the source changed. It gave
    # the shipped `shape` column an 8-bar effective confirmation and a 4-bar lag
    # against everything else in the file. Caught by regenerate.py: the archived
    # column matched score_at(19) at exactly +4 bars, 100.000%, and matched
    # confirm(score_at(19), DWELL) at 100.000% unshifted. `combined` was built
    # before this line and was never affected.

    n, m = len(px.index), len(px.columns)
    flat = lambda d: d.reindex(index=px.index, columns=px.columns).values.ravel()
    T = pd.DataFrame({
        'date': np.repeat(px.index.strftime('%Y-%m-%d').values, m),
        'pair': np.tile(px.columns.values, n),
        'state_7': flat(multi[7][0]),
        'state_28': flat(multi[28][0]),
        'state_128': flat(multi[128][0]),
        'tier': flat(tier),
        'age_28': flat(age),
        'straight_28': flat(A['straight']),
        'scale_28': flat(A['scale']),
        'shape_35': flat(rib[35]),
        'shape': flat(sh),
        'shape_247': flat(rib[247]),
        'shape_score': flat(scr),
        'trend_score': flat(_tr),
        'chop_score': flat(_ch),
        'shape2': flat(_s2),
        'm_fail': flat(_M['fail_count']),
        'm_retr': flat(_M['retr_slope']),
        'm_space': flat(_M['space_slope']),
        'm_panel': flat(_M['panel_r2']),
        'activity': flat(act),
        'combined': flat(comb),
        'combined2': flat(_c2),
        'settling': flat(settle),
        'sample': np.where(np.repeat(fit, m), 'is', 'oos'),
    })
    keep = T[['state_7', 'state_28', 'state_128', 'combined']].notna().any(axis=1)
    T = T[keep].reset_index(drop=True)
    T['age_28'] = T.age_28.astype('Int64')
    T[LEGACY].to_csv(os.path.join(ROOTOUT, 'layer1_legacy.csv'), index=False,
                     float_format='%.6g')
    return T[COLS], multi, tier


def check(T, multi, tier):
    """This file must agree with what ninestate.py already published. If it does
    not, the interface is lying about the estimator and the run stops."""
    if os.path.exists(TIERCSV):
        pub = pd.read_csv(TIERCSV, index_col=0, parse_dates=True)
        mine = T.pivot(index='date', columns='pair', values='tier')
        mine.index = pd.to_datetime(mine.index)
        i = pub.index.intersection(mine.index)
        c = pub.columns.intersection(mine.columns)
        a, b = pub.loc[i, c], mine.loc[i, c]
        bad = int(((a != b) & (a.notna() | b.notna())).values.sum())
        assert bad == 0, 'tier disagrees with nine_tiers.csv on %d pair-days' % bad
        print('  tier matches nine_tiers.csv on %d pair-days' % (len(i) * len(c)))

    if os.path.exists(EXPL):
        d = json.load(open(EXPL))
        dts = pd.to_datetime(d['dates'])
        mine = T.pivot(index='date', columns='pair', values='state_28')
        mine.index = pd.to_datetime(mine.index)
        bad = tot = 0
        for p, rec in d['pairs'].items():
            if p not in mine.columns:
                continue
            f = pd.Series([None if v is None else d['states'][v] for v in rec['st28']],
                          index=dts).reindex(mine.index)
            g = mine[p]
            bad += int(((f != g) & (f.notna() | g.notna())).sum())
            tot += len(g)
        assert bad == 0, 'state_28 disagrees with app_explorer.json on %d pair-days' % bad
        print('  state_28 matches app_explorer.json st28 on %d pair-days' % tot)


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    T, multi, tier = build(px)
    T.to_csv(OUT, index=False, float_format='%.6g')

    print('LAYER 1 INTERFACE  %s' % os.path.basename(OUT))
    print('  %d rows, %d pairs, %s to %s, %.1f MB'
          % (len(T), T.pair.nunique(), T.date.iloc[0], T.date.iloc[-1],
             os.path.getsize(OUT) / 1048576))
    print('  windows %s, base %d, structural cell %s, dwell M=%d'
          % (str(MULTI), BASE, str(chosen_cell()), DWELL))

    print('\nSHAPE2 SHARE (the current classifier)')
    for tag in ('is', 'oos'):
        v = T[T['sample'] == tag].shape2.value_counts(normalize=True)
        print('  %-4s %s' % (tag, '  '.join('%s %.3f' % (k, v[k])
                                            for k in v.index)))

    print('\nSTATE SHARE, 28-day window (LEGACY)')
    for tag in ('is', 'oos'):
        L = pd.read_csv(os.path.join(ROOTOUT, 'layer1_legacy.csv'),
                        usecols=['state_28', 'sample'])
        v = L[L['sample'] == tag].state_28.value_counts(normalize=True).reindex(STATES)
        print('  %-4s %s' % (tag, '  '.join('%s %.3f' % (s.split()[0][:6] + s.split()[1][:5], v[s])
                                            for s in STATES)))

    print('\nTIER SHARE (LEGACY)')
    L = pd.read_csv(os.path.join(ROOTOUT, 'layer1_legacy.csv'),
                    usecols=['tier', 'sample'])
    for tag in ('is', 'oos'):
        v = L[L['sample'] == tag].tier.value_counts(normalize=True)
        print('  %-4s %s' % (tag, '  '.join('%s %.3f' % (k[:11], v[k])
                                            for k in v.sort_index().index)))

    print('\nSHAPE RIBBON AND ACTIVITY SHARE')
    for c in ('activity',):
        for tag in ('is', 'oos'):
            v = T[T['sample'] == tag][c].value_counts(normalize=True)
            print('  %-9s %-4s %s' % (c, tag, '  '.join('%s %.3f' % (k, v[k])
                                                        for k in v.index)))

    print('\nSETTLING CONFIDENCE, share of holdout rows at each grade')
    v = T[T['sample'] == 'oos'].settling.round(2).value_counts(normalize=True)
    print('  ' + '  '.join('%.1f %.3f' % (k, v[k]) for k in sorted(v.index)))

    print('\nCOVERAGE, share of rows with a label')
    for c in ('trend_score', 'chop_score', 'shape2', 'activity', 'scale_28',
              'combined2', 'settling', 'm_fail', 'm_retr', 'm_space', 'm_panel'):
        print('  %-11s %.3f' % (c, T[c].notna().mean()))

    print('\nAGREEMENT WITH THE PUBLISHED OUTPUT')
    L = pd.read_csv(os.path.join(ROOTOUT, 'layer1_legacy.csv'))
    check(L, multi, tier)
    print('\nwrote %s' % OUT)


if __name__ == '__main__':
    main()
