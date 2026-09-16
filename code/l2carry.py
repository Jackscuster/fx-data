import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""ITEM 15 -- THE CARRY SLEEVE, from the repo's 2-year yields.

data/carry28.csv holds the 2y rate differential (base - quote, percentage
points) for 21 of 28 pairs, 1999-01 on (no NZD yield in the repo, so no NZD
pair). Each rebalance date the 21 pairs are ranked by the differential known
the bar before; the top fraction is held long, the bottom fraction short,
for the holding period, then re-ranked. Positions are SIZED LIKE THE REST:
units = RISK / (ATR_31 at entry) so a 1-ATR move is 1 R, and the daily mark
is the close-to-close change in R -- exactly the engine's mark convention,
with the pair's round-trip cost charged on the entry day from cost_table.
Each (fraction, period) sleeve is one MEMBER with sid 'carry|carry|f<frac>|p<period>|..'
and slice label 'carry'; it enters the netting as any other member's marks
do -- its positions net against the strategies' on the same (pair, day).

Sweeps: fraction in {1/6, 1/4, 1/3, 1/2}; rebalance in {weekly, monthly,
quarterly}. Each sleeve is walked ALONE and ADDED to the routed book, both
budgets; return-per-DIP95 is the question, so it is reported next to the
book's own.
"""
import argparse, time
import numpy as np, pandas as pd
import l2walkfwd as W
import l2sweep as S
import l2lib as L

IDENT = {y: y for y in W.YEARS}
ATR_LEN = S.ATR_LEN


def build_marks(frac, period):
    """-> (T rows, M rows) for one sleeve, engine convention."""
    car = pd.read_csv(os.path.join(ROOTDATA, 'carry28.csv'), index_col=0, parse_dates=True).shift(1)   # known the bar before
    pairs = [p for p in car.columns]
    px = {}
    for p in pairs:
        d = W.S.load_pair(p)   # the sealed loader (AUDIT 10), not a raw read
        d['atr'] = L.P.atr(d.high.values, d.low.values, d.close.values, ATR_LEN)
        px[p] = d
    idx = px[pairs[0]].index
    idx = idx[(idx >= '2010-06-01') & (idx <= '2020-12-31')]
    if period == 'weekly':
        reb = idx[idx.to_series().dt.isocalendar().week.diff().fillna(1) != 0]
    elif period == 'monthly':
        reb = idx[idx.to_series().dt.month.diff().fillna(1) != 0]
    else:
        reb = idx[idx.to_series().dt.quarter.diff().fillna(1) != 0]
    reb = list(reb) + [idx[-1] + pd.Timedelta(days=1)]
    sid = 'carry|carry|f%.3f|p%s|rank|hold' % (frac, period)
    T, M = [], []; tid = 0
    S.load_costs()
    for i in range(len(reb) - 1):
        d0, d1 = reb[i], reb[i + 1]
        diff = car.loc[:d0].iloc[-1].dropna() if d0 in car.index or True else None
        diff = car.reindex([d0]).iloc[0].dropna()
        if len(diff) < 6:
            continue
        n = max(1, int(round(len(diff) * frac)))
        order = diff.sort_values()
        legs = [(p, -1) for p in order.index[:n]] + [(p, 1) for p in order.index[-n:]]
        for p, sgn in legs:
            d = px[p]
            days = d.index[(d.index >= d0) & (d.index < d1)]
            if len(days) < 2:
                continue
            e = days[0]; atr = float(d.at[e, 'atr'])
            if not np.isfinite(atr) or atr <= 0:
                continue
            units = S.RISK / atr
            ent = float(d.at[e, 'close'])
            cst = float(S._cost_R(p, np.array([ent]), np.array([units]), np.array([e]))[0])
            tid += 1
            cl = d.close.reindex(days).values
            prev = ent; tot = 0.0
            for j, day in enumerate(days):
                mk = sgn * (cl[j] - prev) * units / S.RISK
                prev = cl[j]; tot += mk
                M.append((sid, p, day, sgn, np.float32(mk - (cst if j == 0 else 0.0)), tid))
            T.append((sid, tid, p, e, days[-1], float(tot - cst), 'ip2'))
    Tf = pd.DataFrame(T, columns=['sid', 'tid', 'pair', 'entry', 'exit', 'R', 'era'])
    Mf = pd.DataFrame(M, columns=['sid', 'pair', 'day', 'dir', 'mark', 'tid'])
    return Tf, Mf


def kp(k, dipb, dayb):
    k['within_budget'] = bool(k['max_dd_pct'] <= dipb and k['dip95_pct'] <= dipb and k['worst_day_pct'] <= dayb); return k


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--suffix', default='_routed_tirexcl_actweak')
    ap.add_argument('--alone-only', action='store_true', help='each sleeve walked alone only, with its own per-trade expectancy; no book walks (15 Sep: the book is contaminated, HANDOFF 0d)')
    a = ap.parse_args(); W.S.load_costs()
    W.TAG = a.suffix; os.environ['WF_TAG'] = a.suffix
    T = pd.read_pickle(W.OUT('wf_trades.pkl')); M = pd.read_pickle(W.OUT('wf_marks.pkl')); TY = W.trade_year_sums(M)
    t0 = time.time(); rows = []
    for bt, dipb, dayb in ([] if a.alone_only else W.BUDGETS):
        r = W.walk(T, TY, M, IDENT, dipb, dayb, ['ALLPASS'], nocut=True); k = kp(r['ALLPASS'][0], dipb, dayb)
        k.update(sleeve='book alone', frac=np.nan, period='', budget=bt, ret_per_dip=k['median_year_pct'] / max(k['dip95_pct'], 1e-9)); rows.append(k)
    for frac in (1 / 6, 1 / 4, 1 / 3, 1 / 2):
        for period in ('weekly', 'monthly', 'quarterly'):
            Tc, Mc = build_marks(frac, period)
            if not len(Tc):
                continue
            Tc['sid'] = Tc.sid.astype('category'); Tc['pair'] = Tc.pair.astype('category'); Mc['sid'] = Mc.sid.astype('category'); Mc['pair'] = Mc.pair.astype('category')
            Mc['dir'] = Mc['dir'].astype(np.int8)
            TYc = W.trade_year_sums(Mc)
            # the sleeve's own per-trade record, net of costs: what a new member type has to show first
            ex = {}
            for lab, y0, y1 in (('build', 2011, 2015), ('trade', 2016, 2020)):
                tt = Tc[Tc.entry.dt.year.between(y0, y1)]
                ex[lab] = dict(n=int(len(tt)), expectancy_R=float(tt.R.mean()) if len(tt) else np.nan, share_pos=float((tt.R > 0).mean()) if len(tt) else np.nan,
                               profit_factor=float(tt.R[tt.R > 0].sum() / max(-tt.R[tt.R < 0].sum(), 1e-9)) if len(tt) else np.nan)
            print('    carry f=%.2f %-9s per-trade: build 2011-15 n %4d  R/trade %+.3f  win %.2f  PF %.2f | trade 2016-20 n %4d  R/trade %+.3f  win %.2f  PF %.2f'
                  % (frac, period, ex['build']['n'], ex['build']['expectancy_R'], ex['build']['share_pos'], ex['build']['profit_factor'],
                     ex['trade']['n'], ex['trade']['expectancy_R'], ex['trade']['share_pos'], ex['trade']['profit_factor']), flush=True)
            for bt, dipb, dayb in W.BUDGETS:
                r = W.walk(Tc, TYc, Mc, IDENT, dipb, dayb, ['ALLPASS'], nocut=True); k = kp(r['ALLPASS'][0], dipb, dayb)
                k.update(sleeve='carry alone', frac=frac, period=period, budget=bt, ret_per_dip=k['median_year_pct'] / max(k['dip95_pct'], 1e-9), positions=len(Tc),
                         **{'pt_%s_%s' % (lab, kk): v for lab in ex for kk, v in ex[lab].items()}); rows.append(k)
                print('    carry f=%.2f %-9s alone %-6s median %6.3f%%  worst %6.3f%%  maxDD %5.2f%%  DIP95 %5.2f%%  PF %.2f  ret/DIP %.2f' % (frac, period, bt, k['median_year_pct'], k['worst_year_pct'], k['max_dd_pct'], k['dip95_pct'], k['profit_factor'], k['ret_per_dip']), flush=True)
                if a.alone_only:
                    continue
                Ta = pd.concat([T.assign(sid=T.sid.astype(str), pair=T.pair.astype(str)), Tc.assign(sid=Tc.sid.astype(str), pair=Tc.pair.astype(str))], ignore_index=True)
                Ma = pd.concat([M.assign(sid=M.sid.astype(str), pair=M.pair.astype(str)), Mc.assign(sid=Mc.sid.astype(str), pair=Mc.pair.astype(str))], ignore_index=True)
                for c in ('sid', 'pair'):
                    Ta[c] = Ta[c].astype('category'); Ma[c] = Ma[c].astype('category')
                TYa = W.trade_year_sums(Ma)
                r = W.walk(Ta, TYa, Ma, IDENT, dipb, dayb, ['ALLPASS'], nocut=True); k = kp(r['ALLPASS'][0], dipb, dayb)
                k.update(sleeve='book + carry', frac=frac, period=period, budget=bt, ret_per_dip=k['median_year_pct'] / max(k['dip95_pct'], 1e-9)); rows.append(k)
                print('    carry f=%.2f %-9s added %-6s median %6.3f%%  worst %6.3f%%  maxDD %5.2f%%  DIP95 %5.2f%%  PF %.2f  ret/DIP %.2f' % (frac, period, bt, k['median_year_pct'], k['worst_year_pct'], k['max_dd_pct'], k['dip95_pct'], k['profit_factor'], k['ret_per_dip']), flush=True)
            pd.DataFrame(rows).to_csv(W.OUT('carry.csv'), index=False)
    pd.DataFrame(rows).to_csv(W.OUT('carry.csv'), index=False)
    print('=== carry done in %.1f min ===' % ((time.time() - t0) / 60), flush=True)


if __name__ == '__main__':
    main()
