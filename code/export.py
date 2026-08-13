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
               weights. Equals shape_144. 5-bar confirmation dwell.
  shape_12     the same score at a 12-bar median lookback  \  the shape ribbon,
  shape_35     ...at 35 bars                                >  the analogue of
  shape_144    ...at 144 bars, chosen on IS                /   state_7/28/128.
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
COLS = ['date', 'pair', 'state_7', 'state_28', 'state_128', 'tier', 'age_28',
        'straight_28', 'scale_28', 'shape_12', 'shape_35', 'shape',
        'activity', 'combined', 'settling', 'sample']


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
    rib = {lb: score_at(px, n, fit)[0] for n, lb in RIBBON}
    cage = age_of(comb)
    settle = (cage / DWELL).clip(upper=1.0)
    # the shape layer carries the dwell too, so the three columns are consistent
    sh = confirm(sh, DWELL)

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
        'shape_12': flat(rib[12]),
        'shape_35': flat(rib[35]),
        'shape': flat(sh),
        'activity': flat(act),
        'combined': flat(comb),
        'settling': flat(settle),
        'sample': np.where(np.repeat(fit, m), 'is', 'oos'),
    })
    keep = T[['state_7', 'state_28', 'state_128', 'combined']].notna().any(axis=1)
    T = T[keep].reset_index(drop=True)
    T['age_28'] = T.age_28.astype('Int64')
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

    print('\nSTATE SHARE, 28-day window')
    for tag in ('is', 'oos'):
        v = T[T['sample'] == tag].state_28.value_counts(normalize=True).reindex(STATES)
        print('  %-4s %s' % (tag, '  '.join('%s %.3f' % (s.split()[0][:6] + s.split()[1][:5], v[s])
                                            for s in STATES)))

    print('\nTIER SHARE')
    for tag in ('is', 'oos'):
        v = T[T['sample'] == tag].tier.value_counts(normalize=True)
        print('  %-4s %s' % (tag, '  '.join('%s %.3f' % (k[:11], v[k])
                                            for k in v.sort_index().index)))

    print('\nSHAPE RIBBON AND ACTIVITY SHARE')
    for c in ('shape_12', 'shape_35', 'shape', 'activity'):
        for tag in ('is', 'oos'):
            v = T[T['sample'] == tag][c].value_counts(normalize=True)
            print('  %-9s %-4s %s' % (c, tag, '  '.join('%s %.3f' % (k, v[k])
                                                        for k in v.index)))

    print('\nSETTLING CONFIDENCE, share of holdout rows at each grade')
    v = T[T['sample'] == 'oos'].settling.round(2).value_counts(normalize=True)
    print('  ' + '  '.join('%.1f %.3f' % (k, v[k]) for k in sorted(v.index)))

    print('\nCOVERAGE, share of rows with a label')
    for c in ('state_7', 'state_28', 'state_128', 'tier', 'shape_12',
              'shape_35', 'shape', 'activity', 'combined', 'settling'):
        print('  %-11s %.3f' % (c, T[c].notna().mean()))

    print('\nAGREEMENT WITH THE PUBLISHED OUTPUT')
    check(T, multi, tier)
    print('\nwrote %s' % OUT)


if __name__ == '__main__':
    main()
