import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""LAYER 4 SIZING v1 — net the votes, size by agreement, cap by currency.

THE CURRENT BOOK IS A PLACEHOLDER. Every member holds its own position, so three
members long EURUSD hold three EURUSD positions and the book's gross exposure is
whatever the roster happens to want. This nets them.

    1. NET PER PAIR PER DAY. Longs and shorts on the same pair offset. The
       majority count minus the minority count sets the agreement LEVEL; a tie
       is flat.
    2. SIZE BY THE CURVE, measured in the agreement study:
           1 -> 1, 2 -> 3, 3+ -> 6
       The study found return per unit rising monotonically to level 3 and
       flattening after, with level 4+ resting on 23 episodes. The curve stops
       at 3 for that reason.
    3. CONFIRMATION-DEPENDENT MEMBERS COUNT AS ZERO WHEN ALONE. Two members earn
       nothing by themselves and well in company; they contribute to the level
       only when someone agrees with them.
    4. PER-CURRENCY PER-DIRECTION CAP of 2%. EURUSD long and EURJPY long both
       spend EUR-long budget. Without this a book can be long every EUR cross
       and call it seven positions.
    5. RESCALE the whole book so DIP95, actual max drawdown and worst day fit
       the budget, exactly as the team builder does.

MARK TO MARKET at the window boundary, fees on: both inherited from
l2deliver.blind_trades, which this reads.
"""
import json, glob, time, argparse
import numpy as np, pandas as pd
import l2team as TM
import l2crisis as C
import l2deliver as DL
import l2sweep as S

CURVE = {'curve': {1: 1.0, 2: 3.0, 3: 6.0},
         'linear': {1: 1.0, 2: 2.0, 3: 3.0},
         'half': {1: 1.0, 2: 2.0, 3: 3.0},
         'stacked': None}
HALF = {1: 1.0, 2: 2.0, 3: 3.0}
CCY_CAP_PCT = 2.0        # per currency, per direction, in % of ACCOUNT EQUITY
ZERO_ALONE = ('kuskus_starlight', 'volatility_quality')


def sized(level, mode):
    if level <= 0:
        return 0.0
    if mode == 'linear':
        return float(min(level, 99))
    tab = {'curve': {1: 1.0, 2: 3.0, 3: 6.0}, 'half': {1: 1.0, 2: 2.0, 3: 3.0}}[mode]
    return tab[min(level, 3)]


def member_daily(R, wins):
    """Per member, per pair, per day: direction and that day's share of R.
    R is spread across the holding days, so a day's return belongs to the
    agreement level actually in force that day."""
    rows = []
    for m in R.to_dict('records'):
        T = DL.blind_trades(m, wins)
        if not len(T):
            continue
        zero_alone = any(z in str(m['sid']) for z in ZERO_ALONE)
        for t in T.itertuples():
            days = pd.date_range(t.entry, t.exit, freq='B')
            if not len(days):
                days = pd.DatetimeIndex([t.entry])
            per = t.R / len(days)
            for d in days:
                rows.append((m['sid'], float(m['vote']), t.pair, d, int(t.dir),
                             per, zero_alone))
    return pd.DataFrame(rows, columns=['sid', 'vote', 'pair', 'day', 'dir',
                                       'r_day', 'zero_alone'])


def net_book(PD, mode):
    """Net per pair per day, size by agreement, then cap per currency."""
    if mode == 'stacked':
        w = PD.vote
        return (PD.r_day * w).groupby(PD.day).sum().sort_index() / w.sum(), 0
    g = PD.copy()
    cnt = g.groupby(['pair', 'day', 'dir']).sid.transform('size')
    g['counts'] = np.where(g.zero_alone & (cnt == 1), 0.0, 1.0)
    side = g.groupby(['pair', 'day', 'dir']).agg(
        n=('counts', 'sum'), r=('r_day', 'mean')).reset_index()
    rows = []
    for (pair, day), d in side.groupby(['pair', 'day']):
        nl = float(d[d.dir == 1].n.sum()); ns = float(d[d.dir == -1].n.sum())
        rl = float(d[d.dir == 1].r.mean()) if (d.dir == 1).any() else 0.0
        rs = float(d[d.dir == -1].r.mean()) if (d.dir == -1).any() else 0.0
        net = nl - ns
        if abs(net) < 0.5:
            continue                                  # a tie is flat
        lvl = int(round(abs(net)))
        sz = sized(lvl, mode)
        if sz <= 0:
            continue
        sgn = 1 if net > 0 else -1
        rows.append(dict(pair=pair, day=day, level=lvl, size=sz, dir=sgn,
                         r=(rl if sgn > 0 else rs)))
    B = pd.DataFrame(rows)
    if not len(B):
        raise RuntimeError('netting produced no positions for mode %r' % mode)
    B['pnl'] = B.r * B['size']
    B['base_ccy'] = B.pair.str[:3]
    B['quote_ccy'] = B.pair.str[3:]
    # THE CAP IS 2% OF ACCOUNT EQUITY, NOT 2% OF THE DAY'S OWN BOOK.
    # The first version used `2% x the day's total size`, which is
    # self-referential: with a handful of positions every one exceeds 2% of the
    # day's total on its own, so the cap bound on all 1,304 days and acted as a
    # uniform rescale -- undone by the budget scaling that follows, so it did
    # nothing while reporting that it bound constantly.
    #
    # Position sizes here are multiples of base risk, and the final scaling
    # turns one unit into `scale`% of equity. So the cap needs the scale, and
    # the scale depends on the capped series. Two passes: size the uncapped
    # book, apply the cap in account terms at that scale, then re-size.
    def _series(bb):
        dd = bb.groupby('day').pnl.sum().sort_index()
        den = float(bb.groupby('day')['size'].sum().mean()) or 1.0
        return dd / den

    def _scale_for(dd, dipb, dayb):
        D = TM.dip95(dd.values, rng=np.random.default_rng(7))
        eq = dd.cumsum(); adj = float((eq.cummax() - eq).max())
        wd = float(-dd.min()) if dd.min() < 0 else 1e-9
        return float(min(dipb / max(adj, D) if max(adj, D) > 0 else np.inf,
                         dayb / wd if wd > 0 else np.inf))

    s0 = _scale_for(_series(B), 3.6, 3.6)
    den0 = float(B.groupby('day')['size'].sum().mean()) or 1.0
    pct_per_unit = s0 / den0              # % of equity per size-unit

    binds, out = 0, []
    for day, d in B.groupby('day'):
        expo = {}
        for r in d.itertuples():
            expo[(r.base_ccy, r.dir)] = expo.get((r.base_ccy, r.dir), 0.0) + r.size
            expo[(r.quote_ccy, -r.dir)] = expo.get((r.quote_ccy, -r.dir), 0.0) + r.size
        # exposure in % of equity, against the 2% limit
        over = [(v * pct_per_unit) / CCY_CAP_PCT for v in expo.values()
                if v * pct_per_unit > CCY_CAP_PCT]
        if over:
            binds += 1
            f = 1.0 / max(over)
            d = d.assign(size=d['size'] * f, pnl=d.pnl * f)
        out.append(d)
    B = pd.concat(out, ignore_index=True)
    B.to_csv(os.path.join(ROOTOUT, 'layer4_positions_%s.csv' % mode), index=False)
    daily = B.groupby('day').pnl.sum().sort_index()
    denom = float(B.groupby('day')['size'].sum().mean()) or 1.0
    return daily / denom, binds


def kpis(d, dipb, dayb, rng, npos):
    """Size to the budget exactly as the team builder does, then report."""
    D = TM.dip95(d.values, rng=rng)
    eq = d.cumsum(); adj = float((eq.cummax() - eq).max())
    risk = max(adj, D)
    wd = float(-d.min()) if d.min() < 0 else 1e-9
    s_risk = dipb / risk if risk > 0 else np.inf
    s_day = dayb / wd if wd > 0 else np.inf
    scale = float(min(s_risk, s_day))
    binds = 'worst day' if s_day < s_risk else ('actual maxDD' if adj >= D else 'DIP95')
    x = d * scale
    e = x.cumsum(); yr = x.groupby(x.index.year).sum()
    mon = x.groupby([x.index.year, x.index.month]).sum()
    neg = x[x < 0]
    return dict(median_year_pct=float(yr.median()), mean_year_pct=float(yr.mean()),
                worst_year_pct=float(yr.min()), best_year_pct=float(yr.max()),
                total_return_pct=float(x.sum()),
                max_dd_pct=float((e.cummax() - e).max()),
                dip95_pct=float(D * scale), worst_day_pct=float(-x.min()),
                worst_month_pct=float(-mon.min()),
                sortino=float(x.mean() / neg.std(ddof=1) * np.sqrt(252)) if len(neg) > 1 else np.nan,
                calmar=float(x.sum() / (e.cummax() - e).max()) if (e.cummax() - e).max() > 0 else np.nan,
                profit_factor=float(x[x > 0].sum() / -x[x < 0].sum()) if (x < 0).any() else np.inf,
                win_rate_pct=float(100 * (x > 0).mean()), trades=int(len(x)),
                max_positions=npos, scale=scale, binds=binds)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--label', default='_W3ONLY_ADOPTED')
    a = ap.parse_args()
    t0 = time.time()
    S.load_costs()
    rng = np.random.default_rng(20260915)
    wins = C.windows()
    R = TM.load_candidates()
    ros = pd.read_csv(os.path.join(ROOTOUT, 'team1%s_roster.csv' % a.label))
    keep = [c for c in ('sid', 'ip2', 'src_mode', 'src_label', 'exit_ind',
                        'risk_atr_len', 'risk_atr_mult', 'risk_tp_mult',
                        'risk_trail_mult', 'risk_trail_arm', 'risk_be_pct')
            if c in R.columns]
    ros = ros.merge(R[keep].drop_duplicates('sid'), on='sid', how='left')
    if ros.ip2.isna().any():
        raise SystemExit('roster members without settings -- refusing to size a '
                         'book that cannot be run')
    print('roster: %d members' % len(ros), flush=True)
    PD = member_daily(ros, wins)
    print('position-days: %d' % len(PD), flush=True)
    rows = []
    for tag, mode in (('A_stacked_placeholder', 'stacked'),
                      ('B_netted_linear', 'linear'),
                      ('C_netted_curve', 'curve'),
                      ('D_netted_half_curve', 'half')):
        d, binds = net_book(PD, mode)
        npos = 0
        f = os.path.join(ROOTOUT, 'layer4_positions_%s.csv' % mode)
        if os.path.exists(f):
            b = pd.read_csv(f)
            npos = int(b.groupby('day').size().max())
        for bt, dipb, dayb in (('team1', 3.6, 3.6), ('team2', 5.4, 3.6)):
            k = kpis(d, dipb, dayb, rng, npos)
            k.update(book=tag, mode=mode, budget=bt, ccy_cap_bound_days=binds)
            rows.append(k)
            print('  %-24s %-6s median %6.2f%%  worst %6.2f%%  maxDD %5.2f%%  binds %s  cap bound %d days'
                  % (tag, bt, k['median_year_pct'], k['worst_year_pct'],
                     k['max_dd_pct'], k['binds'], binds), flush=True)
    O = pd.DataFrame(rows)
    O.to_csv(os.path.join(ROOTOUT, 'layer4_sizing_v1.csv'), index=False)
    json.dump(O.to_dict('records'),
              open(os.path.join(ROOTOUT, 'layer4_sizing_v1.json'), 'w'),
              indent=1, default=str)
    print('DONE in %.1f min' % ((time.time() - t0) / 60), flush=True)


if __name__ == '__main__':
    main()
