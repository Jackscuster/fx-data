import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""PART C -- the routing table, from files only. ALWAYS-ON, the H.10-routed
reproduction, and the four 5pm-routed variants: full KPIs, both budgets,
per slice, per year, the regime-dependence table, both nulls, sizing."""
import numpy as np, pandas as pd
pd.set_option('display.width', 260)
BOOKS = [('ALWAYS_ON', '_cleanfield_4slice_allon'), ('H10_ROUTED_repro', '_routed_repro'),
         ('5pm TIRx ACTi', '_routed_tirexcl_actignore'), ('5pm TIRi ACTi', '_routed_tirincl_actignore'),
         ('5pm TIRx ACTw', '_routed_tirexcl_actweak'), ('5pm TIRi ACTw', '_routed_tirincl_actweak')]
K = ['median_year_pct', 'worst_year_pct', 'max_dd_pct', 'worst_day_pct', 'dip95_pct', 'profit_factor', 'sortino', 'calmar']

def rd(name, tag, need=False):
    p = os.path.join(ROOTOUT, '%s%s.csv' % (name, tag))
    if not os.path.exists(p):
        if need: raise SystemExit('MISSING ' + p)
        return None
    return pd.read_csv(p, comment='#')

rows, peryear, perslice, dep = [], [], [], []
for lab, tag in BOOKS:
    S = rd('walkforward_structures_3slice', tag, need=True)
    T = pd.read_pickle(os.path.join(ROOTOUT, 'wf_trades%s.pkl' % tag)) if os.path.exists(os.path.join(ROOTOUT, 'wf_trades%s.pkl' % tag)) else None
    NR = rd('walkforward_null_randomentry_nocut_summary_3slice', tag)
    NS = rd('walkforward_null_regimeshuffle_summary_3slice', tag)
    SZ = rd('walkforward_structures_sizing', tag)
    for r in S[S.structure == 'NO_CUT'].itertuples():
        d = dict(book=lab, budget=r.budget, trades=(len(T) if T is not None else np.nan), expectancy_pct_per_day=r.total_return_pct / r.trading_days)
        for k in K: d[k] = getattr(r, k)
        d['within_budget'] = bool(r.max_dd_pct <= r.dip_budget and r.dip95_pct <= r.dip_budget and r.worst_day_pct <= r.day_budget)
        if NR is not None:
            q = NR[(NR.budget == r.budget) & (NR.structure == 'NO_CUT')]
            if len(q): d['randentry_null_max'] = float(q.null_max.iloc[0]); d['randentry_p'] = float(q.p_value.iloc[0])
        if NS is not None:
            q = NS[NS.budget == r.budget]
            if len(q): d['shuffle_null_mean'] = float(q.null_mean.iloc[0]); d['shuffle_null_max'] = float(q.null_max.iloc[0]); d['shuffle_p'] = float(q.p_value.iloc[0])
        if SZ is not None:
            for s in SZ[SZ.structure == 'NO_CUT'].itertuples():
                if (s.sizing.startswith('a') and r.budget == 'team1') or (s.sizing.startswith('b') and r.budget == 'team2'):
                    pass
            c = SZ[(SZ.structure == 'NO_CUT') & (SZ.sizing.str.startswith('c'))]
            if len(c) and r.budget == 'team1': d['sizing_c_median'] = float(c.median_year_pct.iloc[0]); d['sizing_c_maxdd'] = float(c.max_dd_pct.iloc[0])
        rows.append(d)
    D = rd('walkforward_daily_3slice', tag)
    if D is not None:
        D = D.set_index(D.columns[0]); D.index = pd.to_datetime(D.index)
        for col in D.columns:
            bt, _, st = col.partition('|')
            if st != 'NO_CUT': continue
            s = pd.to_numeric(D[col], errors='coerce')
            for y, g in s.groupby(s.index.year):
                e = g.cumsum(); peryear.append(dict(book=lab, budget=bt, year=int(y), return_pct=float(g.sum()), max_dd_pct=float((e.cummax() - e).max()), realised_vol_pct=float(g.std() * np.sqrt(252))))
    P = rd('walkforward_perslice_3slice', tag)
    if P is not None:
        for r in P.itertuples():
            perslice.append(dict(book=lab, budget=r.budget, slice=r.slice, passers=r.members_step1, median_year_pct=r.median_year_pct, worst_year_pct=r.worst_year_pct, max_dd_pct=r.max_dd_pct, profit_factor=r.profit_factor))
    RD = rd('walkforward_regime_dependence', tag)
    if RD is not None:
        RD = RD.assign(book=lab); dep.append(RD)

OUT = pd.DataFrame(rows); OUT.to_csv(os.path.join(ROOTOUT, 'routing_report_4slice.csv'), index=False)
PY = pd.DataFrame(peryear); PY.to_csv(os.path.join(ROOTOUT, 'routing_peryear_4slice.csv'), index=False)
PS = pd.DataFrame(perslice); PS.to_csv(os.path.join(ROOTOUT, 'routing_perslice_4slice.csv'), index=False)
if dep:
    DP = pd.concat(dep, ignore_index=True); DP.to_csv(os.path.join(ROOTOUT, 'routing_dependence_4slice.csv'), index=False)
f = lambda v: '%7.3f' % v
print('=== ROUTED vs ALWAYS-ON, four-slice clean field, NO_CUT ===')
print(OUT.to_string(index=False, float_format=f))
print('\n=== per year (NO_CUT return %) ===')
print(PY.pivot_table(index=['book', 'budget'], columns='year', values='return_pct').to_string(float_format=f))
print('\n=== per year (NO_CUT max DD %) ===')
print(PY.pivot_table(index=['book', 'budget'], columns='year', values='max_dd_pct').to_string(float_format=f))
print('\n=== per slice, each walked alone (team1) ===')
print(PS[PS.budget == 'team1'].pivot_table(index='slice', columns='book', values='median_year_pct').to_string(float_format=f))
if dep:
    print('\n=== regime dependence (trade-level R, trade years, TIRx/ACTi rule) ===')
    x = DP[(DP.book == '5pm TIRx ACTi') & DP.inside.isin(['True', 'False', True, False])]
    print(x[['slice', 'inside', 'trades', 'mean_R', 'sum_R', 'win_rate', 'R_per_year']].to_string(index=False, float_format=f))
    print('\n=== by state at entry (trade-level R, trade years) ===')
    y = DP[(DP.book == '5pm TIRx ACTi') & ~DP.inside.isin(['True', 'False', True, False])]
    print(y.pivot_table(index='slice', columns='inside', values='mean_R').to_string(float_format=f))
    print(y.pivot_table(index='slice', columns='inside', values='trades').to_string(float_format=lambda v: '%d' % v))
