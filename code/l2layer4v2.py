import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""LAYER 4 SIZING v2 — net first, THEN mark to market daily.

v1 spread each trade's R evenly across its holding days. That smooths the daily
series, shrinks DIP95 and max drawdown, and inflates the scale the budget
allows: the same roster and budget gave 55.56% there against the team builder's
22.97%. The ranking was sound; the levels were not comparable to anything.

Here each member's position is marked to that day's close -- the same
close-to-close change in equity the team builder uses -- and the NETTING is
applied to those daily marks. So a level-3 day carries three members' marks
netted into one position at the curve's size, and the resulting series is
directly comparable to 22.97%.

WHY THE ORDER MATTERS. Netting after mark-to-market keeps the day-to-day
volatility that sizing has to respect; netting a smoothed series hides it.
"""
import json, glob, time, argparse
import numpy as np, pandas as pd
import l2team as TM
import l2crisis as C
import l2deliver as DL
import l2sweep as S

ZERO_ALONE = ('kuskus_starlight', 'volatility_quality')
CURVES = {'stacked': None, 'linear': None,
          'curve': {1: 1.0, 2: 3.0, 3: 6.0},
          'half': {1: 1.0, 2: 2.0, 3: 3.0}}


def sized(level, mode):
    if level <= 0:
        return 0.0
    if mode == 'linear':
        return float(level)
    return CURVES[mode][min(level, 3)]


def marks(R, wins):
    """Per member, per pair, per day: direction and the DAILY MARK-TO-MARKET
    change, not a spread share of the final R."""
    rows = []
    for m in R.to_dict('records'):
        code = dict((s, c) for s, _, c in S.SLICES)[m['slice']]
        za = any(z in str(m['sid']) for z in ZERO_ALONE)
        for p in S.all_pairs():
            try:
                r = TM.TR.run_pair(m, p)
            except Exception:
                continue
            d, tr, cl = r['dates'], r['trades'], r['c']
            if len(tr['r']) == 0:
                continue
            reg = S.regime_codes(p, d)
            wb = {}
            for k, (a, z) in S.WINDOWS.items():
                w = np.flatnonzero((d >= a) & (d <= z))
                if len(w):
                    wb[k] = (int(w[0]), int(w[-1]) + 1)
            for j in range(len(tr['r'])):
                eb, xb = int(tr['entry_bar'][j]), int(tr['exit_bar'][j])
                if xb < 0 or reg[eb] != code:
                    continue
                zz = None
                for k in DL.BLIND_WINDOWS:
                    b = wb.get(k)
                    if b and b[0] <= eb < b[1]:
                        zz = b[1] - 1
                if zz is None:
                    continue
                ent = float(tr['entry_px'][j]); u = float(tr['units'][j])
                sgn = float(tr['dir'][j]); tot = float(tr['r'][j])
                end = min(xb, zz)          # mark to market at the boundary
                prev = 0.0
                for b in range(eb, end + 1):
                    cum = tot if (b == xb and xb <= zz) else sgn * (cl[b] - ent) * u / S.RISK
                    rows.append((m['sid'], p, d[b], int(sgn), cum - prev, za))
                    prev = cum
    return pd.DataFrame(rows, columns=['sid', 'pair', 'day', 'dir', 'mark', 'za'])


def build(M, mode, cap_pct):
    """Net per pair per day, size by agreement, cap per currency, return the
    daily series, cap-bound day count and the largest exposure reached."""
    if mode == 'stacked':
        n = M.sid.nunique()
        return M.groupby('day').mark.sum().sort_index() / n, 0, np.nan, None
    g = M.copy()
    cnt = g.groupby(['pair', 'day', 'dir']).sid.transform('size')
    g['counts'] = np.where(g.za & (cnt == 1), 0.0, 1.0)
    side = g.groupby(['pair', 'day', 'dir']).agg(
        n=('counts', 'sum'), mk=('mark', 'mean')).reset_index()
    rows = []
    for (pair, day), d in side.groupby(['pair', 'day']):
        nl = float(d[d.dir == 1].n.sum()); ns = float(d[d.dir == -1].n.sum())
        ml = float(d[d.dir == 1].mk.mean()) if (d.dir == 1).any() else 0.0
        ms = float(d[d.dir == -1].mk.mean()) if (d.dir == -1).any() else 0.0
        net = nl - ns
        if abs(net) < 0.5:
            continue
        lvl = int(round(abs(net))); sz = sized(lvl, mode)
        if sz <= 0:
            continue
        sgn = 1 if net > 0 else -1
        rows.append(dict(pair=pair, day=day, level=lvl, size=sz, dir=sgn,
                         mark=(ml if sgn > 0 else ms)))
    B = pd.DataFrame(rows)
    if not len(B):
        raise RuntimeError('netting produced no positions for %r' % mode)
    B['pnl'] = B['mark'] * B['size']
    B['bc'] = B.pair.str[:3]; B['qc'] = B.pair.str[3:]

    def series(bb):
        s = bb.groupby('day').pnl.sum().sort_index()
        den = float(bb.groupby('day')['size'].sum().mean()) or 1.0
        return s / den

    def scale_of(s, dipb=3.6, dayb=3.6):
        D = TM.dip95(s.values, rng=np.random.default_rng(7))
        eq = s.cumsum(); adj = float((eq.cummax() - eq).max())
        wd = float(-s.min()) if s.min() < 0 else 1e-9
        return float(min(dipb / max(adj, D) if max(adj, D) > 0 else np.inf,
                         dayb / wd if wd > 0 else np.inf))

    # two passes: the cap is in % of EQUITY, which needs the final scale
    s0 = scale_of(series(B))
    den0 = float(B.groupby('day')['size'].sum().mean()) or 1.0
    per_unit = s0 / den0
    binds, out, worst_expo = 0, [], 0.0
    for day, d in B.groupby('day'):
        expo = {}
        for r in d.itertuples():
            expo[(r.bc, r.dir)] = expo.get((r.bc, r.dir), 0.0) + r.size
            expo[(r.qc, -r.dir)] = expo.get((r.qc, -r.dir), 0.0) + r.size
        mx = max(expo.values()) * per_unit if expo else 0.0
        worst_expo = max(worst_expo, mx)
        if cap_pct is not None:
            over = [v * per_unit / cap_pct for v in expo.values()
                    if v * per_unit > cap_pct]
            if over:
                binds += 1
                f = 1.0 / max(over)
                d = d.assign(size=d['size'] * f, pnl=d.pnl * f)
        out.append(d)
    B = pd.concat(out, ignore_index=True)
    return series(B), binds, worst_expo, B


def kpis(d, dipb, dayb, npos):
    D = TM.dip95(d.values, rng=np.random.default_rng(11))
    eq = d.cumsum(); adj = float((eq.cummax() - eq).max())
    wd = float(-d.min()) if d.min() < 0 else 1e-9
    s_risk = dipb / max(adj, D) if max(adj, D) > 0 else np.inf
    s_day = dayb / wd if wd > 0 else np.inf
    scale = float(min(s_risk, s_day))
    binds = 'worst day' if s_day < s_risk else ('actual maxDD' if adj >= D else 'DIP95')
    x = d * scale; e = x.cumsum()
    yr = x.groupby(x.index.year).sum()
    mon = x.groupby([x.index.year, x.index.month]).sum()
    neg = x[x < 0]
    dd = float((e.cummax() - e).max())
    return dict(median_year_pct=float(yr.median()), mean_year_pct=float(yr.mean()),
                worst_year_pct=float(yr.min()), best_year_pct=float(yr.max()),
                total_return_pct=float(x.sum()), max_dd_pct=dd,
                dip95_pct=float(D * scale), worst_day_pct=float(-x.min()),
                worst_month_pct=float(-mon.min()),
                sortino=float(x.mean() / neg.std(ddof=1) * np.sqrt(252)) if len(neg) > 1 else np.nan,
                sharpe=float(x.mean() / x.std(ddof=1) * np.sqrt(252)) if x.std(ddof=1) > 0 else np.nan,
                calmar=float(x.sum() / dd) if dd > 0 else np.nan,
                profit_factor=float(x[x > 0].sum() / -x[x < 0].sum()) if (x < 0).any() else np.inf,
                win_rate_pct=float(100 * (x > 0).mean()),
                trading_days=int(len(x)), max_positions=npos,
                scale=scale, binds=binds)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--label', default='_W3ONLY_ADOPTED')
    a = ap.parse_args()
    t0 = time.time(); S.load_costs()
    V = TM.load_candidates()
    ros = pd.read_csv(os.path.join(ROOTOUT, 'team1%s_roster.csv' % a.label))
    keep = [c for c in ('sid', 'ip2', 'src_mode', 'src_label', 'exit_ind', 'slice',
                        'risk_atr_len', 'risk_atr_mult', 'risk_tp_mult',
                        'risk_trail_mult', 'risk_trail_arm', 'risk_be_pct')
            if c in V.columns]
    ros = ros.drop(columns=[c for c in ('slice',) if c in ros.columns])
    ros = ros.merge(V[keep].drop_duplicates('sid'), on='sid', how='left')
    if ros.ip2.isna().any():
        raise SystemExit('roster members without settings')
    print('roster %d members' % len(ros), flush=True)
    M = marks(ros, C.windows())
    print('mark-to-market rows: %d over %d days' % (len(M), M.day.nunique()), flush=True)
    rows = []
    for tag, mode in (('A_stacked', 'stacked'), ('B_netted_linear', 'linear'),
                      ('C_netted_curve', 'curve'), ('D_netted_half', 'half')):
        d, binds, wex, B = build(M, mode, 2.0 if mode != 'stacked' else None)
        npos = int(B.groupby('day').size().max()) if B is not None else int(
            M.groupby('day').size().max())
        for bt, dipb, dayb in (('team1', 3.6, 3.6), ('team2', 5.4, 3.6)):
            k = kpis(d, dipb, dayb, npos)
            k.update(book=tag, mode=mode, budget=bt, cap_pct=(2.0 if mode != 'stacked' else None),
                     cap_bound_days=binds, max_ccy_exposure_pct=wex)
            rows.append(k)
        print('  %-16s median %6.2f%%  worst %6.2f%%  maxDD %5.2f%%  cap-bound %d  max ccy expo %.2f%%'
              % (tag, rows[-2]['median_year_pct'], rows[-2]['worst_year_pct'],
                 rows[-2]['max_dd_pct'], binds, wex), flush=True)
    # the winner at four cap settings
    for cap in (2.0, 3.0, 4.0, None):
        d, binds, wex, B = build(M, 'curve', cap)
        npos = int(B.groupby('day').size().max())
        k = kpis(d, 3.6, 3.6, npos)
        k.update(book='C_curve_cap_%s' % ('none' if cap is None else '%.0f' % cap),
                 mode='curve', budget='team1', cap_pct=cap,
                 cap_bound_days=binds, max_ccy_exposure_pct=wex)
        rows.append(k)
        print('  cap %-5s median %6.2f%%  worst %6.2f%%  maxDD %5.2f%%  DIP95 %5.2f%%  worst day %5.2f%%  bound %d  max expo %.2f%%'
              % ('none' if cap is None else '%.0f%%' % cap, k['median_year_pct'],
                 k['worst_year_pct'], k['max_dd_pct'], k['dip95_pct'],
                 k['worst_day_pct'], binds, wex), flush=True)
    O = pd.DataFrame(rows)
    O.to_csv(os.path.join(ROOTOUT, 'layer4_sizing_v2.csv'), index=False)
    json.dump(O.to_dict('records'),
              open(os.path.join(ROOTOUT, 'layer4_sizing_v2.json'), 'w'), indent=1, default=str)
    print('DONE in %.1f min' % ((time.time() - t0) / 60), flush=True)


if __name__ == '__main__':
    main()
