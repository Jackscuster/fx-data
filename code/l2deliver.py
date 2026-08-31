import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""App bundles for the crisis-excluded top 10: trades, equity, years, CAGR.

ONE FILE PER STRATEGY, carrying everything the app draws:
  bars/trades  the best pair's candles and every blind trade on it, each trade
               carrying `crisis` so quarantined money is visible on the chart
  equity       cumulative R across ALL 28 pairs over the blind span, ordered by
               EXIT date -- a trade contributes when it closes, not when it opens
  years        R per calendar year, and the largest year's share of the total
  cagr         BOTH figures, never one alone

WHY BOTH CAGR FIGURES. The gauntlet is fixed-R by design: every trade risks the
same cash, so expectancy in R is exact and does not depend on the order trades
fell in. That makes AVERAGE ANNUAL R the native honest number. A CAGR only
exists if you assume compounding, which the gauntlet deliberately does not do --
so the compounded figure is a SIMULATION laid over the same trade sequence at 2%
of running equity, and it is path-dependent in a way the R figures are not. It
is reported with its assumption attached and never on its own.
"""
import json, glob
import numpy as np, pandas as pd
import l2trades as TR, l2crisis as C, l2sweep as S

RISK_FRac = 0.02


def blind_trades(cfg, wins):
    """Every blind-window trade in this slice, across all 28 pairs."""
    code = dict((s, c) for s, _, c in S.SLICES)[cfg['slice']]
    out = []
    for p in S.all_pairs():
        try:
            r = TR.run_pair(cfg, p)
        except Exception:
            continue
        d, tr = r['dates'], r['trades']
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
            if not any(wb.get(k) and wb[k][0] <= eb < wb[k][1] for k in ('W2', 'W3')):
                continue
            out.append(dict(pair=p, entry=d[eb], exit=d[xb], R=float(tr['r'][j]),
                            crisis=bool(C.flag(d[eb], d[xb], p, wins))))
    return pd.DataFrame(out)


def equity_and_years(T):
    if not len(T):
        return [], [], {}
    T = T.sort_values('exit').reset_index(drop=True)
    cum = T.R.cumsum()
    eq = [dict(d=str(r.exit.date()), r=round(float(cum[i]), 3),
               c=int(r.crisis), pair=r.pair, tr=round(float(r.R), 3))
          for i, r in enumerate(T.itertuples())]
    T = T.assign(year=T.exit.dt.year)
    yr = T.groupby('year').R.agg(['sum', 'size'])
    years = [dict(y=int(y), R=round(float(v['sum']), 2), n=int(v['size']))
             for y, v in yr.iterrows()]
    span_days = (T.exit.max() - T.exit.min()).days or 1
    yrs = span_days / 365.25
    total = float(T.R.sum())
    # compounding SIMULATION, 2% of running equity per trade, same order
    e = 1.0
    for r in T.R.values:
        e *= (1.0 + RISK_FRac * float(r))
        if e <= 0:
            e = 1e-9
            break
    cagr = (e ** (1.0 / yrs) - 1.0) if yrs > 0 else float('nan')
    top = max((abs(x['R']) for x in years), default=0.0)
    stats = dict(total_R=round(total, 2), years=round(yrs, 2),
                 avg_annual_R=round(total / yrs, 2) if yrs else None,
                 cagr_pct=round(100 * cagr, 2),
                 cagr_assumption='SIMULATED: 2%% of running equity per trade, '
                                 'same trade order. The gauntlet itself is '
                                 'fixed-R and does NOT compound.',
                 final_equity_x=round(e, 3),
                 top_year_share=round(top / abs(total), 3) if total else None)
    return eq, years, stats


def bundle(cfg, rank, wins):
    T = blind_trades(cfg, wins)
    eq, years, stats = equity_and_years(T)
    # best pair by blind R, for the candlestick view
    bp = T.groupby('pair').R.sum().sort_values(ascending=False)
    pair = bp.index[0] if len(bp) else S.all_pairs()[0]
    r = TR.run_pair(cfg, pair)
    d, o, h, l, c, atr = r['dates'], r['o'], r['h'], r['l'], r['c'], r['atr']
    tr, risk = r['trades'], r['risk']
    code = dict((s, cc) for s, _, cc in S.SLICES)[cfg['slice']]
    reg = S.regime_codes(pair, d)
    wb = {}
    for k, (a, z) in S.WINDOWS.items():
        w = np.flatnonzero((d >= a) & (d <= z))
        if len(w):
            wb[k] = (int(w[0]), int(w[-1]) + 1)
    trades, okall = [], True
    for j in range(len(tr['r'])):
        eb, xb = int(tr['entry_bar'][j]), int(tr['exit_bar'][j])
        if xb < 0 or reg[eb] != code:
            continue
        if not any(wb.get(k) and wb[k][0] <= eb < wb[k][1] for k in ('W2', 'W3')):
            continue
        dirn = int(tr['dir'][j])
        sp = TR.stop_path(r, eb, xb, dirn, float(tr['entry_px'][j]), risk, atr, c, h, l)
        import l2engine as E
        reason = int(tr['reason'][j])
        ok = True
        if int(tr['leg'][j]) == 2 and reason in (E.STOP, E.STOP_BE, E.STOP_TRAIL):
            ok = abs(sp['path'][-1] - float(tr['exit_px'][j])) < 1e-9
        okall &= ok
        trades.append(dict(leg=int(tr['leg'][j]), dir=dirn, entry_bar=eb, exit_bar=xb,
                           entry_date=str(d[eb].date()), exit_date=str(d[xb].date()),
                           entry_px=float(tr['entry_px'][j]), exit_px=float(tr['exit_px'][j]),
                           initial_stop=sp['l1_stop'], tp1=sp['l1_tp'],
                           stop_path=sp['path'], events=sp['events'],
                           reason=E.REASON.get(reason, str(reason)),
                           R=float(tr['r'][j]),
                           crisis=bool(C.flag(d[eb], d[xb], pair, wins)),
                           reconstruction_ok=bool(ok)))
    lo_b = max(0, min([t['entry_bar'] for t in trades], default=0) - 20)
    hi_b = min(len(c) - 1, max([t['exit_bar'] for t in trades], default=len(c) - 1) + 20)
    cr = T[T.crisis]; ex = T[~T.crisis]
    return dict(
        rank=rank, pair=pair, slice=cfg['slice'],
        slots={k: cfg[k] for k in ('c1', 'c2', 'vol', 'base')},
        risk={k: float(cfg['risk_' + k]) for k in
              ('atr_len', 'atr_mult', 'tp_mult', 'trail_mult', 'trail_arm', 'be_pct')},
        indicator_params=json.loads(cfg['ip2']) if isinstance(cfg.get('ip2'), str) else {},
        metrics=dict(ex_n=int(len(ex)), ex_total_R=round(float(ex.R.sum()), 2),
                     ex_expectancy_R=round(float(ex.R.mean()), 4) if len(ex) else None,
                     cr_n=int(len(cr)), cr_total_R=round(float(cr.R.sum()), 2),
                     crisis_share=round(float(cr.R.sum() / T.R.sum()), 3) if T.R.sum() else None,
                     net_of_structure_R=cfg.get('net_of_structure_R'),
                     sortino=cfg.get('ex_sortino'), sharpe=cfg.get('ex_sharpe'),
                     pf=cfg.get('ex_profit_factor'), calmar=cfg.get('ex_calmar'),
                     max_dd_R=cfg.get('ex_max_dd_R'), ulcer_R=cfg.get('ex_ulcer_R'),
                     win_rate=cfg.get('ex_win_rate'), conc=cfg.get('ex_max_trade_share')),
        stats=stats, equity=eq, years=years,
        pair_totals=[dict(pair=k, R=round(float(v), 2),
                          n=int((T.pair == k).sum()))
                     for k, v in T.groupby('pair').R.sum()
                     .sort_values(ascending=False).items()],
        n_trades=len(trades), reconstruction_ok=bool(okall),
        provisional='crisis-excluded ranking; stitched score pending round 2',
        bar0=int(lo_b),
        bars=[dict(d=str(d[i].date()), o=float(o[i]), h=float(h[i]),
                   l=float(l[i]), c=float(c[i])) for i in range(lo_b, hi_b + 1)],
        trades=trades)


def sh(x):
    return str(x).replace('_signals', '').replace('_volume', '').replace('_baseline', '')


def main():
    # PARAMETERISED BY MODE AND SLICE. Bare `python code/l2deliver.py` still
    # produces mode B's files at their original names, so nothing that already
    # points at trades_index.json changes. Any other mode/slice writes its own
    # suffixed index and bundles beside them -- never over them.
    a = sys.argv[1:]
    mode = a[a.index('--mode') + 1] if '--mode' in a else 'B'
    sl = a[a.index('--slice') + 1] if '--slice' in a else None
    ntop = int(a[a.index('--top') + 1]) if '--top' in a else 10
    tag = '' if (mode, sl) == ('B', None) else '_mode%s%s' % (mode, '_' + sl if sl else '')
    wins = C.windows()
    lb = os.path.join(ROOTOUT, 'gate2_mode%s%s_leaderboard.csv'
                      % (mode, '_' + sl if sl else ''))
    if not os.path.exists(lb):
        lb = os.path.join(ROOTOUT, 'gate2_mode%s_leaderboard.csv' % mode)
    L = pd.read_csv(lb, low_memory=False)
    if sl:
        L = L[L.slice == sl]
    L = L.sort_values('rank').head(ntop)
    idx = []
    for cfg in L.to_dict('records'):
        rk = int(cfg['rank'])
        b = bundle(cfg, rk, wins)
        f = os.path.join(ROOTOUT, 'trades%s_r%02d_%s.json' % (tag, rk, b['pair']))
        json.dump(b, open(f, 'w'))
        print('  rank %2d %-7s %-6s best-pair %3d trades | all-pairs %d blind '
              '(%d crisis) | %.1f R | avg %.1f R/yr | CAGR %.1f%% | top year %.0f%%'
              % (rk, b['pair'], b['slice'], b['n_trades'],
                 b['metrics']['ex_n'] + b['metrics']['cr_n'], b['metrics']['cr_n'],
                 b['stats']['total_R'], b['stats']['avg_annual_R'],
                 b['stats']['cagr_pct'], 100 * (b['stats']['top_year_share'] or 0)),
              flush=True)
        idx.append(dict(rank=rk, pair=b['pair'], slice=b['slice'],
                        file=os.path.basename(f), n_trades=b['n_trades'],
                        total_R=b['stats']['total_R'],
                        # LEAD WITH STRATEGY IDENTITY. The old label read like a
                        # pair selector and mixed scopes -- an all-pairs R total
                        # sat beside a best-pair trade count in one string.
                        label='#%d · %s · %s × %s × %s × %s  (charts: %s)'
                              % (rk, b['slice'],
                                 sh(b['slots']['c1']), sh(b['slots']['c2']),
                                 sh(b['slots']['vol']), sh(b['slots']['base']),
                                 b['pair'])))
    fout = 'trades_index%s.json' % tag
    json.dump(idx, open(os.path.join(ROOTOUT, fout), 'w'))
    print('wrote %s' % fout, flush=True)
    print('DONE', flush=True)


if __name__ == '__main__':
    main()
