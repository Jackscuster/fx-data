import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""FRESHNESS GATE — the pipeline FAILS if what it publishes is stale.

WHY THIS EXISTS. The dashboard read "last updated 2026-08-21" for eleven days
while every CI run went green. Nothing was broken loudly enough to notice:

  * `meta.built` is `Timestamp.now()` -- the BUILD time. It is fresh on every
    run by definition, so a fresh-looking board says nothing about the data
    behind it. A build date is not a data date and must never stand in for one.
  * `appfeed.py` ran NINE LINES BEFORE `export.py`, which writes the
    `layer1_states.csv` it reads. Every run therefore published the PREVIOUS
    run's regime states.
  * `build.py` asserts EURUSD's 1.601 peak and USDCHF's 0.7296 low -- both
    historical, both true forever. Nothing asserted that the data had a RECENT
    row.

So the pipeline could fetch nothing new, publish last week's regime read, and
exit zero. Green CI meant "the code ran", not "the numbers are current".

WHAT IS CHECKED, and why each tolerance is what it is:

  1. data/px28.csv reaches within MAX_DATA_AGE_D calendar days of today. H.10 is
     a business-day release with a publication lag, so a weekend plus a holiday
     is normal; five days is the smallest window that never fires on a normal
     Tuesday.
  2. every published feed's LAST DATA DATE equals px28's. Not 'close to' --
     equal. These are all derived from the same price file in the same run, so
     any gap is an ordering bug like the one above, not a tolerance question.

Failing here is the point. A stale board that looks healthy is worse than a red
build, because nobody goes looking.
"""
import json
import pandas as pd

MAX_DATA_AGE_D = 5


def _last(path, kind):
    if not os.path.exists(path):
        return None, 'missing'
    if kind == 'csv_index':
        d = pd.read_csv(path, index_col=0, parse_dates=True)
        return d.index.max(), None
    if kind == 'csv_datecol':
        d = pd.read_csv(path, parse_dates=['date'])
        return d.date.max(), None
    if kind == 'regime':
        j = json.load(open(path))
        return pd.Timestamp(j['dates'][-1]), None
    if kind == 'todayhdr':
        j = json.load(open(path))
        t = (j.get('todayhdr') or [{}])[0]
        return (pd.Timestamp(t['date']) if t.get('date') else None), None
    return None, 'unknown kind'


FEEDS = [
    ('results/layer1_states.csv', 'csv_datecol'),
    ('app_regime.json',           'regime'),
    ('results/app_regime.json',   'regime'),
    ('app_data.json',             'todayhdr'),
    ('results/app_data.json',     'todayhdr'),
]


def main():
    px, err = _last(os.path.join(ROOTDATA, 'px28.csv'), 'csv_index')
    if px is None:
        raise SystemExit('FRESHNESS FAIL: data/px28.csv %s' % err)
    today = pd.Timestamp.now().normalize()
    age = (today - px.normalize()).days
    print('px28.csv last bar %s (%d days old)' % (px.date(), age), flush=True)
    bad = []
    if age > MAX_DATA_AGE_D:
        bad.append('data/px28.csv is %d days old (limit %d). The daily fetch is '
                   'not delivering new bars.' % (age, MAX_DATA_AGE_D))
    for rel, kind in FEEDS:
        d, err = _last(os.path.join(_R, rel), kind)
        if err:
            bad.append('%s: %s' % (rel, err)); continue
        if d is None:
            bad.append('%s: no date found' % rel); continue
        gap = (px.normalize() - pd.Timestamp(d).normalize()).days
        flag = 'OK' if gap == 0 else 'STALE by %d days' % gap
        print('  %-28s last %s  %s' % (rel, pd.Timestamp(d).date(), flag), flush=True)
        if gap != 0:
            bad.append('%s publishes %s but the price data reaches %s -- %d days '
                       'behind.' % (rel, pd.Timestamp(d).date(), px.date(), gap))
    if bad:
        print('\n' + '=' * 70, flush=True)
        print('FRESHNESS GATE FAILED -- the pipeline published stale data:', flush=True)
        for b in bad:
            print('  * ' + b, flush=True)
        print('=' * 70, flush=True)
        raise SystemExit(1)
    print('\nfreshness OK: every published feed reaches %s' % px.date(), flush=True)


if __name__ == '__main__':
    main()
