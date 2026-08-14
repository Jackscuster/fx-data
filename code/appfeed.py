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

Writes app_regime.json at the repo root and in results/.
"""
import json
import numpy as np, pandas as pd

L1 = os.path.join(ROOTOUT, 'layer1_states.csv')
PX = os.path.join(ROOTDATA, 'px28.csv')
OUT = 'app_regime.json'
SHAPES = ['trending', 'ranging', 'trend-in-range', 'neither']
ACTS = ['weak', 'medium', 'strong']


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
