import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""ITEM 14 -- THE KILL-SWITCH, as a walk-forward rule on the routed book.

Rule: when the book's FLOATING loss on a day, measured hour by hour from the
previous 17:00 NY close, reaches the trigger, everything is closed at the next
hour's price and nothing new opens that day. The trigger is swept across its
range -- from a fraction of the day budget up to the budget itself -- and the
whole curve is reported: days fired 2016-2020, the KPI change, and the cost.

HOW INTRADAY IS MEASURED. The book is daily: each (pair, day) row carries a
sized position and its close-to-close mark. Within the day the position is
fixed, so its floating P&L at hour h is the day's mark scaled by the pair's
mid path: (mid_h - close_prev) / (close - close_prev). The hourly mid comes
from data/oanda_h1 (bid+ask)/2, 2004-05 on, aligned to the OANDA day (17:00
NY). A day whose close equals its previous close has no path and is left
untouched. The book's hourly path is the sum over rows; the first hour at
which it reaches -trigger is the fire hour, and the day's P&L becomes the
path value one hour later (the close-all fill), not the close-to-close mark.
"""
import argparse, time
import numpy as np, pandas as pd
import l2walkfwd as W
import l2sweep as S

IDENT = {y: y for y in W.YEARS}
NY = 'America/New_York'
H1 = os.path.join(ROOTDATA, 'oanda_h1')


def load(tag):
    W.TAG = tag; os.environ['WF_TAG'] = tag
    W.TRADES_F = W.OUT('wf_trades.pkl'); W.MARKS_F = W.OUT('wf_marks.pkl')
    T = pd.read_pickle(W.TRADES_F); M = pd.read_pickle(W.MARKS_F)
    return T, M, W.trade_year_sums(M)


def hourly_frac():
    """{pair: DataFrame(day x hour) of (mid_h - c_prev)/(c - c_prev)} for the
    OANDA day (17:00 NY to 17:00 NY), hours 18..17 next day mapped 1..24."""
    out = {}
    for p in S.all_pairs():
        b = pd.read_csv(os.path.join(H1, '%s_bid.csv' % p), parse_dates=['time'], usecols=['time', 'c'])
        a = pd.read_csv(os.path.join(H1, '%s_ask.csv' % p), parse_dates=['time'], usecols=['time', 'c'])
        m = b.merge(a, on='time', suffixes=('_b', '_a')); m['mid'] = (m.c_b + m.c_a) / 2
        ny = m.time.dt.tz_convert(NY)
        # candle labelled h closes at h+1: the price AT hour h+1
        at = ny + pd.Timedelta(hours=1)
        # OANDA day = the date of the 17:00 NY close that ENDS the session
        day = (at - pd.Timedelta(hours=17, minutes=0, seconds=1)).dt.normalize() + pd.Timedelta(days=1)
        m['day'] = day.dt.tz_localize(None); m['hr'] = ((at.dt.hour - 17) % 24)   # 0 = 17:00 close, 1..23 = the hours after, 24 -> next close
        m = m[m.hr != 0]
        piv = m.pivot_table(index='day', columns='hr', values='mid', aggfunc='last')
        d = pd.read_csv(os.path.join(ROOTDATA, 'oanda_ohlc', '%s_mid.csv' % p), parse_dates=['date']).set_index('date').close
        c_prev = d.shift(1).reindex(piv.index); c = d.reindex(piv.index)
        den = (c - c_prev)
        frac = piv.sub(c_prev, axis=0).div(den.replace(0, np.nan), axis=0)
        frac = frac.where(den.abs() > 0)
        out[p] = frac
    return out


def stage_sweep(tag, grid):
    T, M, TY = load(tag)
    FR = hourly_frac()
    rows = []
    for bt, dipb, dayb in W.BUDGETS:
        r = W.walk(T, TY, M, IDENT, dipb, dayb, ['ALLPASS'], nocut=True)
        k, cuts, x, dy = r['ALLPASS']
        base = pd.Series(x, index=pd.DatetimeIndex(dy))
        # rebuild the per-row sized P&L on trade days from the Book of each step, to get the intraday path
        parts = []
        for si, st in enumerate(W.STEPS):
            b0, b1 = st['build']; t0_, t1_ = st['trade']
            bsrc = list(range(b0, b1 + 1)); tsrc = list(range(t0_, t1_ + 1))
            P, _ = W.cut(T, TY, bsrc, apply_bars=False); allp = list(P.sid)
            B = W.Book(M[M.sid.isin(allp)], allp); w = np.ones(len(B.members), np.float32)
            curve, C = W.fit_curve(B, w, bsrc)
            ybuild = np.isin(B.dyears, bsrc); ytrade = np.isin(B.dyears, tsrc)
            d0, den, _, _, _, _ = B.series(w, curve)
            sc, bD, badj, bwd, bbind = W.scale_of(d0[ybuild], dipb, dayb, use_dip=True)
            d1, _, binds, worst, sz, f = B.series(w, curve, cap_pct=W.CAP_PCT, per_unit=sc / den, den=den)
            rp = B.last['row_pnl'] * (sc / den)
            tr_rows = ytrade[B.dpos]
            parts.append(pd.DataFrame({'pair': B.pair[tr_rows], 'day': B.day[tr_rows], 'pnl': rp[tr_rows]}))
        RP = pd.concat(parts)
        # hourly book path per day: sum over rows of pnl * frac(pair, day, h)
        hours = list(range(1, 24))
        path = {}
        for p, g in RP.groupby('pair'):
            fr = FR[p].reindex(g.day.values)
            contrib = fr.values * g.pnl.values[:, None]
            dfc = pd.DataFrame(contrib, index=g.day.values, columns=fr.columns)
            path[p] = dfc
        book = None
        for p, dfc in path.items():
            book = dfc if book is None else book.add(dfc, fill_value=0.0)
        book = book.reindex(columns=hours).sort_index()
        book_nan = book.isna().all(axis=1)
        for trig in grid:
            level = -trig
            fired = (book.le(level)).any(axis=1) & ~book_nan
            y = base.copy()
            for d in book.index[fired]:
                hrow = book.loc[d]; h = int(hrow.index[np.flatnonzero(hrow.values <= level)[0]])
                fill = float(hrow.get(h + 1, hrow.get(h)))        # close-all one hour later; at the last hour, the close
                if np.isfinite(fill): y[d] = fill
            W._MONTHS = y.index; kk = W.kpis(y.values, y.index.year.values)
            kk.update(budget=bt, trigger_pct=trig, days_fired=int(fired.sum()), fired_per_year=float(fired.sum() / 5),
                      cost_pct_yr=float((base.sum() - y.sum()) / 5), within_budget=bool(kk['max_dd_pct'] <= dipb and kk['dip95_pct'] <= dipb and kk['worst_day_pct'] <= dayb))
            rows.append(kk)
            print('    %-6s trigger %.2f%%: fired %3d days  median %6.3f%%  worst %6.3f%%  maxDD %5.2f%%  worst day %5.2f%%  cost %+.2f%%/yr  in-budget %s'
                  % (bt, trig, fired.sum(), kk['median_year_pct'], kk['worst_year_pct'], kk['max_dd_pct'], kk['worst_day_pct'], -kk['cost_pct_yr'], kk['within_budget']), flush=True)
        kb = dict(k); kb.update(budget=bt, trigger_pct=np.nan, days_fired=0, fired_per_year=0.0, cost_pct_yr=0.0, within_budget=bool(k['max_dd_pct'] <= dipb and k['dip95_pct'] <= dipb and k['worst_day_pct'] <= dayb)); rows.append(kb)
    O = pd.DataFrame(rows); O.to_csv(W.OUT('killswitch.csv'), index=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--suffix', default='_routed_tirexcl_actweak')
    ap.add_argument('--grid', default='0.5,0.75,1.0,1.25,1.5,1.75,2.0,2.5,3.0,3.2,3.6')
    a = ap.parse_args(); W.S.load_costs()
    t0 = time.time(); print('=== kill-switch sweep on %s ===' % a.suffix, flush=True)
    stage_sweep(a.suffix, [float(x) for x in a.grid.split(',')])
    print('=== done in %.1f min ===' % ((time.time() - t0) / 60), flush=True)


if __name__ == '__main__':
    main()
