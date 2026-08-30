import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""DO CRISIS MOVES BREAK WITH THE PRE-CRISIS TREND?

Research only. Changes no rule and gates nothing.

THE QUESTION. If a crisis move continues the direction that was already running,
a future crisis sleeve could take its DIRECTION from the prevailing trend and its
TRIGGER from Layer 1's crisis flag. If alignment is at chance, it could not.

DIRECTION COMES FROM PRICE, NOT FROM trend_score. Layer 1's trend_score is a
TRENDINESS MAGNITUDE -- its range is -2.76 to 8.93 and it is overwhelmingly
positive -- so it says how trending a pair is, not which way. Using it as a sign
would have produced a confident answer to a different question. The prevailing
direction is the sign of the pre-event return; shape2 is used to require that a
trend was actually present, which is what trend_score is for.

NO LOOK-AHEAD. The pre-window ENDS on the last bar strictly before the event
date. The crisis window runs from the event date to +15, forward only, matching
crisis.py. Nothing in the pre-window sees the event.

SIGNIFICANCE IS EPISODE-BASED. Pairs within one event are not independent -- a
CHF shock moves every CHF cross together -- so each EVENT contributes one
observation, the mean alignment across its affected pairs. A per-pair binomial
would inflate n by a factor of seven and manufacture significance.
"""
import numpy as np, pandas as pd
import l2sweep as S

WINDOW = 15
PRE = 20


def events():
    E = pd.read_csv(os.path.join(ROOTOUT, 'crisis_events.csv'))
    E = E[['date', 'ccy', 'severity', 'description']].drop_duplicates('date')
    E['date'] = pd.to_datetime(E.date)
    return E.sort_values('date').reset_index(drop=True)


def panel():
    px = {}
    for p in S.all_pairs():
        d = S.load_pair(p)
        px[p] = d['close']
    L = pd.read_csv(os.path.join(ROOTOUT, 'layer1_states.csv'),
                    usecols=['date', 'pair', 'shape2'], parse_dates=['date'])
    return px, L.set_index(['date', 'pair'])['shape2']


def study(pre=PRE, win=WINDOW):
    E = events(); px, shp = panel()
    rows = []
    for e in E.itertuples():
        ccy = e.ccy if isinstance(e.ccy, str) else None
        for p, c in px.items():
            if ccy and ccy not in (p[:3], p[3:]):
                continue
            idx = c.index
            before = idx[idx < e.date]
            after = idx[(idx >= e.date) & (idx <= e.date + pd.Timedelta(days=win))]
            if len(before) < pre + 1 or len(after) < 2:
                continue
            a0, a1 = before[-pre - 1], before[-1]        # pre-window: strictly before
            pre_ret = float(c.loc[a1] / c.loc[a0] - 1.0)
            cr_ret = float(c.loc[after[-1]] / c.loc[after[0]] - 1.0)
            if pre_ret == 0 or cr_ret == 0:
                continue
            st = shp.get((a1, p), None)
            rows.append(dict(event=str(e.date.date()), ccy=ccy or 'global',
                             sev=e.severity, pair=p,
                             pre_ret=pre_ret, crisis_ret=cr_ret,
                             aligned=int(np.sign(pre_ret) == np.sign(cr_ret)),
                             shape2=st,
                             abs_crisis=abs(cr_ret)))
    return pd.DataFrame(rows)
