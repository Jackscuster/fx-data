import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""FULL KPI SET for a built team, at its own budget sizing.

TWO LEVELS, and they answer different questions:
  TEAM level    the account: return, drawdown and ratios on the daily equity
                series at the scale the budget allows.
  MEMBER level  each strategy's own trade statistics, plus its vote and the
                order the greedy search added it.

TRADE-LEVEL KPIs COME FROM TRADES, NOT FROM THE DAILY SERIES. Expectancy, win
rate, average win/loss, hold and profit concentration are properties of trades;
computing them from daily equity would silently answer a different question.
Return, drawdown, Sharpe/Sortino/Calmar and worst month come from the daily
series, because those are properties of the account.

Everything W3-only under ip2 -- BLIND_WINDOWS is inherited from l2team, so this
cannot read a window ip2 has seen.
"""
import json, time, argparse
import numpy as np, pandas as pd
import l2team as TM
import l2crisis as C
import l2deliver as DL
import l2sweep as S

R_PCT = 1.0


def daily_kpis(d, scale):
    """d: unit-scale daily % series. Returns account-level KPIs at `scale`."""
    x = d * scale
    eq = x.cumsum()
    dd = float((eq.cummax() - eq).max())
    neg = x[x < 0]
    yr = x.groupby(x.index.year).sum()
    mon = x.groupby([x.index.year, x.index.month]).sum()
    return dict(
        total_return_pct=float(x.sum()),
        median_year_pct=float(yr.median()), mean_year_pct=float(yr.mean()),
        max_dd_pct=dd,
        calmar=float(x.sum() / dd) if dd > 0 else np.nan,
        sortino=float(x.mean() / neg.std(ddof=1) * np.sqrt(252)) if len(neg) > 1 else np.nan,
        sharpe=float(x.mean() / x.std(ddof=1) * np.sqrt(252)) if x.std(ddof=1) > 0 else np.nan,
        worst_day_pct=float(-x.min()), worst_month_pct=float(-mon.min()),
        best_month_pct=float(mon.max()))


def trade_kpis(T):
    """From a trade list: the things only trades can answer."""
    if not len(T):
        return {}
    r = T.R.values
    w = r[r > 0]; l = r[r < 0]
    conc = np.nan
    if len(w):
        ws = np.sort(w)[::-1]
        k = max(1, int(np.ceil(0.05 * len(ws))))
        conc = float(100.0 * ws[:k].sum() / ws.sum()) if ws.sum() > 0 else np.nan
    hold = (pd.to_datetime(T.exit) - pd.to_datetime(T.entry)).dt.days
    gp = float(w.sum()); gl = float(-l.sum())
    return dict(trades=int(len(r)), total_R=float(r.sum()),
                expectancy_R=float(r.mean()),
                win_rate_pct=float(100.0 * (r > 0).mean()),
                avg_win_R=float(w.mean()) if len(w) else np.nan,
                avg_loss_R=float(l.mean()) if len(l) else np.nan,
                profit_factor=(gp / gl) if gl > 0 else np.inf,
                avg_hold_days=float(hold.mean()),
                profit_concentration_pct=conc)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--label', default='_W3ONLY_GATE2')
    a = ap.parse_args()
    t0 = time.time()
    S.load_costs()
    idx = json.load(open(os.path.join(ROOTOUT, 'team_index%s.json' % a.label)))
    cands = TM.load_candidates()
    wins = C.windows()
    rows_team, rows_mem = [], []
    for tag, o in idx.items():
        members, votes = o['members'], o['votes']
        scale = o['scale']
        sub = cands[cands.cand.isin(members)]
        M, cols = TM.build_matrix(sub, mode='equity', jobs=4)
        w = np.array([votes[c] for c in cols])
        d = TM.team_daily(M.values, w) * R_PCT
        k = daily_kpis(pd.Series(d, index=M.index), scale)
        # holdings and correlation
        H = (M != 0).astype(int)
        act = H.sum(axis=1)
        ad = M[(M != 0).any(axis=1)]
        Cm = ad.corr().values
        tri = Cm[np.triu_indices_from(Cm, 1)]
        # trade-level, pooled across members
        allT = []
        for r in sub.to_dict('records'):
            T = DL.blind_trades(r, wins)
            if len(T):
                T = T.copy(); T['cand'] = r['cand']; allT.append(T)
        AT = pd.concat(allT, ignore_index=True) if allT else pd.DataFrame()
        k.update(trade_kpis(AT))
        k.update(team=tag, members=len(members), scale=scale,
                 dip95_pct=o.get('dip95'), actual_max_dd_pct=o.get('actual_max_dd'),
                 clustering_ratio=o.get('clustering_ratio'), binds=o.get('binds'),
                 mean_corr=float(np.nanmean(tri)), max_corr=float(np.nanmax(tri)),
                 max_positions_open=int(act.max()),
                 mean_positions_when_live=float(act[act > 0].mean()))
        rows_team.append(k)
        for i, c in enumerate(members, 1):
            r = sub[sub.cand == c].iloc[0].to_dict()
            T = DL.blind_trades(r, wins)
            m = dict(team=tag, add_order=i, cand=c, vote=votes[c],
                     src=r.get('src_label'), slice=r.get('slice'),
                     c1=r.get('c1'), c2=r.get('c2'), vol=r.get('vol'), base=r.get('base'),
                     sharpe_only_flag=r.get('sharpe_only_flag'))
            m.update(trade_kpis(T))
            if len(T):
                s = T.groupby(pd.to_datetime(T.exit).dt.normalize()).R.sum()
                e = s.cumsum(); m['max_dd_R'] = float((e.cummax() - e).max())
                neg = s[s < 0]
                m['sortino'] = float(s.mean() / neg.std(ddof=1) * np.sqrt(252)) if len(neg) > 1 else np.nan
                m['sharpe'] = float(s.mean() / s.std(ddof=1) * np.sqrt(252)) if s.std(ddof=1) > 0 else np.nan
                m['calmar'] = float(s.sum() / m['max_dd_R']) if m['max_dd_R'] > 0 else np.nan
            rows_mem.append(m)
    T1 = pd.DataFrame(rows_team); T2 = pd.DataFrame(rows_mem)
    T1.to_csv(os.path.join(ROOTOUT, 'team_kpis%s.csv' % a.label), index=False)
    T2.to_csv(os.path.join(ROOTOUT, 'team_members_kpis%s.csv' % a.label), index=False)
    json.dump(dict(team=T1.to_dict('records'), members=T2.to_dict('records')),
              open(os.path.join(ROOTOUT, 'team_kpis%s.json' % a.label), 'w'),
              indent=1, default=str)
    print(T1.round(3).to_string(index=False), flush=True)
    print('\nDONE in %.1f min' % ((time.time() - t0) / 60), flush=True)


if __name__ == '__main__':
    main()
