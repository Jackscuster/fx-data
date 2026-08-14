import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""The Regime Detector feed. One file, read directly by the app.

Per pair: price, the current shape state, the two scores as separate series so
their independence is visible on the chart, and the four measurements. Nothing
else -- no money metrics anywhere, by design. This screen answers "what state is
this pair in and what did price do", and nothing about what it earned.

SIZE IS THE CONSTRAINT. Eleven series x 28 pairs x ~6,900 days is 2.1 million
numbers, and a naive dump is ~30 MB. So: state is an integer index into a legend,
every float is rounded to the fewest digits that survive a chart at screen
resolution, and nulls are written as null rather than a padded float. That lands
it near the existing explorer feed rather than three times it.

THE CHART VIEW ALSO READS THIS FILE, which is why three things were added to it
rather than a second nine-megabyte payload being built beside it:

  cuts    the two boundaries the classifier actually cuts at, so the optional
          score panel can draw them instead of the reader guessing.
  trb     the trend score AFTER the activity adjustment. This matters and is the
          reason a plain `tr` line would misexplain the label: the cut mt is
          applied to tr minus the activity bump, so plotting raw `tr` against mt
          would show bars sitting the wrong side of a line they never crossed.
          Both series are kept -- `tr` raw, `trb` as used.
  crisis  indices of days inside the forward-only acute-crisis window, so the
          chart can mark them. The window opens ON a news-dated event and never
          before it; these marks are the detector CONFIRMING, never predicting.

Writes app_regime.json at the repo root and in results/.
"""
import json
import numpy as np, pandas as pd

L1 = os.path.join(ROOTOUT, 'layer1_states.csv')
SPLIT = pd.Timestamp('2016-01-01')
PX = os.path.join(ROOTDATA, 'px28.csv')
OUT = 'app_regime.json'
SHAPES = ['trending', 'ranging', 'trend-in-range', 'neither']
ACTS = ['weak', 'medium', 'strong']


from final import scores as _sc, activity as _act, DROP_TESTS, BUMP, ACTW
from drivers import crisis_mask


def rnd(v, n):
    """-> list with None for NaN, rounded, so JSON stays small."""
    return [None if not np.isfinite(x) else round(float(x), n) for x in v]


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    S = pd.read_csv(L1, parse_dates=['date'])
    print('building the regime feed from %d rows' % len(S))
    dates = sorted(S.date.unique())
    di = {d: i for i, d in enumerate(dates)}
    n = len(dates)
    out = {'dates': [pd.Timestamp(d).strftime('%Y-%m-%d') for d in dates],
           'shapes': SHAPES, 'acts': ACTS,
           'split': int(np.searchsorted(np.array(dates),
                                        np.datetime64('2016-01-01'))),
           'pairs': {}}
    sidx = {s: i for i, s in enumerate(SHAPES)}
    aidx = {a: i for i, a in enumerate(ACTS)}
    # the series the cuts are ACTUALLY applied to, plus the cuts themselves
    fitm = np.asarray(px.index < SPLIT)
    _tr, _ch = _sc(px, fitm, drop_tests=DROP_TESTS)
    _a = _act(px, fitm)
    _trb = _tr - _a.replace(ACTW).astype(float) * BUMP
    _ft = np.where(fitm[:, None], _trb.values, np.nan)
    _fc = np.where(fitm[:, None], _ch.values, np.nan)
    out['cuts'] = {'mt': round(float(np.nanmedian(_ft)), 4),
                   'mc': round(float(np.nanmedian(_fc)), 4)}
    cm, n_ev = crisis_mask(px.index)
    cmi = cm.reindex(pd.DatetimeIndex(dates)).fillna(False).values
    out['crisis'] = [int(i) for i in np.flatnonzero(cmi)]
    out['crisis_events'] = int(n_ev)
    print('  cuts mt=%.4f mc=%.4f | %d acute-crisis days from %d events'
          % (out['cuts']['mt'], out['cuts']['mc'], len(out['crisis']), n_ev))

    for p, g in S.groupby('pair'):
        g = g.set_index('date')
        pos = np.array([di[d] for d in g.index])
        def col(name, nd=3, code=None):
            a = np.full(n, np.nan)
            v = g[name].values
            if code is not None:
                v = np.array([code.get(x, np.nan) for x in v], float)
            a[pos] = v.astype(float)
            return rnd(a, nd)
        pr = np.full(n, np.nan)
        pr[pos] = px[p].reindex(g.index).values
        out['pairs'][p] = {
            'px': rnd(pr, 5),
            'st': [None if x is None else int(x)
                   for x in col('shape2', 0, sidx)],
            'ac': [None if x is None else int(x)
                   for x in col('activity', 0, aidx)],
            'tr': col('trend_score', 2),
            'trb': rnd(_trb[p].reindex(pd.DatetimeIndex(dates)).values, 2),
            'ch': col('chop_score', 2),
            'set': col('settling', 2),
            'mf': col('m_fail', 1),
            'mr': col('m_retr', 4),
            'ms': col('m_space', 3),
            'mp': col('m_panel', 3),
        }
    for path in (os.path.join(_R, OUT), os.path.join(ROOTOUT, OUT)):
        with open(path, 'w') as f:
            json.dump(out, f, separators=(',', ':'))
    mb = os.path.getsize(os.path.join(_R, OUT)) / 1048576
    print('wrote %s -- %d pairs, %d dates, %.1f MB' % (OUT, len(out['pairs']),
                                                       n, mb))


if __name__ == '__main__':
    main()
