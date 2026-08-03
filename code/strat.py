import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTDATA,exist_ok=True); os.makedirs(ROOTOUT,exist_ok=True)
sys.path.insert(0,ROOTLIB)
"""Strategy sweep across 28 pairs, output in Jack's config-table format.

Families and grids extend the supplied configs rather than replacing them:
  momentum        n_short x n_long  (SMA crossover)
  mean_reversion  n x entry         (z-score, exit at 0)

Split: IS 1999-2015, OOS 2016-2026. Sharpe annualised on daily returns.
Costs applied on position CHANGE. Majors 1.5bp, crosses 3.0bp round trip.
"""
import itertools, numpy as np, pandas as pd

PX = os.path.join(ROOTDATA,'/px28.csv'.lstrip('/'))
SPLIT = '2016-01-01'
MAJ = {'EURUSD', 'GBPUSD', 'AUDUSD', 'NZDUSD', 'USDCAD', 'USDCHF', 'USDJPY'}


def cost(pair):
    return 1.5e-4 if pair in MAJ else 3.0e-4


def stats(ret, pos, c):
    """ret: strategy daily returns net. pos: position series."""
    if ret.std() == 0 or ret.notna().sum() < 100:
        return None
    trades = int((pos.diff().abs() > 0).sum())
    eq = ret.cumsum()
    dd = (eq - eq.cummax())
    mdd = -dd.min()
    tot = ret.sum()
    wins = ret[ret > 0].sum(); loss = -ret[ret < 0].sum()
    return dict(
        sharpe=ret.mean() / ret.std() * np.sqrt(252),
        ret=tot,
        maxdd=mdd,
        retdd=tot / mdd if mdd > 0 else np.nan,
        pf=wins / loss if loss > 0 else np.nan,
        win=(ret[pos.shift(1).abs() > 0] > 0).mean(),
        trades=trades,
        expo=(pos.abs() > 0).mean(),
        avgtrade=tot / trades if trades else np.nan)


def momentum(p, ns, nl):
    return np.sign(p.rolling(int(ns)).mean() - p.rolling(int(nl)).mean())


def meanrev(p, n, entry):
    z = (p - p.rolling(int(n)).mean()) / p.rolling(int(n)).std()
    pos = pd.Series(np.nan, index=p.index)
    pos[z <= -entry] = 1.0
    pos[z >= entry] = -1.0
    pos[z.abs() < 0.1] = 0.0
    return pos.ffill().fillna(0.0)


def run():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    pairs = list(px.columns)
    cfgs = []
    for i, (ns, nl) in enumerate(itertools.product([5, 10, 20, 30, 50], [60, 90, 120, 200])):
        if ns >= nl:
            continue
        cfgs.append(dict(config_id=f'momentum_{len(cfgs)}', family='momentum',
                         param_n_short=float(ns), param_n_long=float(nl),
                         param_n=np.nan, param_entry=np.nan))
    m0 = len(cfgs)
    for i, (n, e) in enumerate(itertools.product([5, 10, 20, 30, 60], [1.0, 1.5, 2.0, 2.5])):
        cfgs.append(dict(config_id=f'mean_reversion_{len(cfgs)-m0}', family='mean_reversion',
                         param_n_short=np.nan, param_n_long=np.nan,
                         param_n=float(n), param_entry=float(e)))

    LP = {p: np.log(px[p].astype(float)) for p in pairs}
    R = {p: LP[p].diff() for p in pairs}
    rows = []
    for cf in cfgs:
        per = []
        for p in pairs:
            lp = LP[p]
            if cf['family'] == 'momentum':
                pos = momentum(lp, cf['param_n_short'], cf['param_n_long'])
            else:
                pos = meanrev(lp, cf['param_n'], cf['param_entry'])
            pos = pos.shift(1).fillna(0.0)
            gross = pos * R[p]
            net = gross - pos.diff().abs().fillna(0) * cost(p)
            for tag, mask in (('is', net.index < SPLIT), ('oos', net.index >= SPLIT)):
                s = stats(net[mask].dropna(), pos[mask], cost(p))
                if s:
                    per.append(dict(pair=p, tag=tag, **s))
        if not per:
            continue
        d = pd.DataFrame(per)
        o = d[d.tag == 'oos']; i_ = d[d.tag == 'is']
        rows.append(dict(**cf, n_tickers=o.pair.nunique(),
                         mean_oos_sharpe=o.sharpe.mean(),
                         median_oos_sharpe=o.sharpe.median(),
                         pct_positive=(o.sharpe > 0).mean(),
                         mean_trades=o.trades.mean(),
                         mean_is_sharpe=i_.sharpe.mean(),
                         sharpe_decay=o.sharpe.mean() / i_.sharpe.mean()
                         if i_.sharpe.mean() != 0 else np.nan,
                         worst_sharpe=o.sharpe.min(),
                         mean_retdd=o.retdd.mean(),
                         mean_pf=o.pf.mean(),
                         mean_win=o.win.mean(),
                         mean_expo=o.expo.mean(),
                         t_across=o.sharpe.mean() / (o.sharpe.std() / np.sqrt(len(o)))))
    T = pd.DataFrame(rows)
    T.to_csv(os.path.join(ROOTOUT,'/strategy_sweep.csv'.lstrip('/')), index=False)
    return T


if __name__ == '__main__':
    T = run()
    pd.set_option('display.width', 250, 'display.max_columns', 30)
    core = ['config_id', 'family', 'param_n_short', 'param_n_long', 'param_n', 'param_entry',
            'n_tickers', 'mean_oos_sharpe', 'median_oos_sharpe', 'pct_positive', 'mean_trades']
    print('configs %d' % len(T))
    print('\n=== JACK FORMAT, sorted by mean OOS sharpe ===')
    print(T.sort_values('mean_oos_sharpe', ascending=False)[core].head(14)
          .to_string(index=False, float_format=lambda v: '%.3f' % v))
    print('\n=== ADDED DIAGNOSTICS, same order ===')
    ext = ['config_id', 'mean_is_sharpe', 'mean_oos_sharpe', 'sharpe_decay', 'worst_sharpe',
           'mean_retdd', 'mean_pf', 'mean_win', 'mean_expo', 't_across']
    print(T.sort_values('mean_oos_sharpe', ascending=False)[ext].head(14)
          .to_string(index=False, float_format=lambda v: '%.3f' % v))
    print('\n=== BY FAMILY ===')
    print(T.groupby('family')[['mean_oos_sharpe', 'median_oos_sharpe', 'pct_positive',
                               'mean_trades']].mean().to_string())
