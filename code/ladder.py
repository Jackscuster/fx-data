import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTDATA,exist_ok=True); os.makedirs(ROOTOUT,exist_ok=True)
sys.path.insert(0,ROOTLIB)
"""Detector ladder — dumbest to fanciest, each must beat the row above.

Applies each of the four framework.py detectors as a FILTER to two baseline
strategies, then reports every detector-state cell against the unfiltered
baseline in STRATEGY_TEMPLATE.md format.

  strategies   mean reversion n=60 entry 2.0   |   momentum 30/120
  detectors    trend_sma200, vol_regime, markov_naive, hmm_2state
  cells        one per (strategy, detector, state), plus BASELINE per strategy

Aggregation: an equal-weight portfolio across the 28 pairs. Each day's return is
the mean of the per-pair net returns, so Net Profit / Ret/DD / Profit Factor are
portfolio-level numbers rather than averages of per-pair ratios. Trades are summed
across pairs and Exposure is the share of (pair, day) cells holding a position.

Return/Exposure is ret/expo — see the UNRESOLVED note in STRATEGY_TEMPLATE.md.

Labels are shifted one bar before use. Costs 1.5bp majors, 3.0bp crosses, charged
on position change. Reported on OOS only (2016-2026).
"""
import numpy as np, pandas as pd
import framework as F

PX = os.path.join(ROOTDATA,'/px28.csv'.lstrip('/'))
STRATS = [('mean_reversion n=60 e=2.0', lambda lp: F.mr(lp, 60, 2.0)),
          ('momentum 30/120',           lambda lp: F.mo(lp, 30, 120))]


def metrics(ret, pos_on, trades):
    """ret: equal-weight portfolio daily return. pos_on: (pair,day) in-market share."""
    ret = ret.dropna()
    if len(ret) < 100 or ret.std() == 0:
        return None
    eq = ret.cumsum()
    mdd = -(eq - eq.cummax()).min()
    tot = ret.sum()
    wins = ret[ret > 0].sum(); loss = -ret[ret < 0].sum()
    return dict(net_profit=tot,
                retdd=tot / mdd if mdd > 0 else np.nan,
                pf=wins / loss if loss > 0 else np.nan,
                trades=int(trades),
                win=float((ret > 0).mean()),
                avgtrade=tot / trades if trades else np.nan,
                expo=float(pos_on),
                retexp=tot / pos_on if pos_on > 0 else np.nan)


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    pairs = list(px.columns)
    oos = px.index >= F.SPLIT

    # per-pair net return and position for each strategy, plus each detector's labels
    NET = {s: {} for s, _ in STRATS}
    POS = {s: {} for s, _ in STRATS}
    LAB = {d: {} for d, _ in F.DETS}
    for p in pairs:
        lp = np.log(px[p].astype(float)); r = lp.diff()
        c = F.cost(p)
        hp = F.hp_for(p, lp, r)
        for sn, fn in STRATS:
            pos = fn(lp).shift(1).fillna(0.)
            NET[sn][p] = pos * r - pos.diff().abs().fillna(0) * c
            POS[sn][p] = pos
        for dn, df in F.DETS:
            LAB[dn][p] = df(lp, r, hp).shift(1)
        print('  %s' % p, flush=True)

    rows = []
    for sn, _ in STRATS:
        net = pd.DataFrame(NET[sn]); pos = pd.DataFrame(POS[sn])
        held = pos.abs() > 0
        # BASELINE: unfiltered, same strategy, all bars
        b_ret = net[oos].mean(axis=1)
        b_tr = int((pos.diff().abs() > 0)[oos].sum().sum())
        b_on = float(held[oos].values.mean())
        base = metrics(b_ret, b_on, b_tr)
        rows.append(dict(strategy=sn, detector='-', state='-', cell='BASELINE',
                         data_pct=1.0, **base,
                         imp_retexp=0.0, imp_retdd=0.0, imp_pf=0.0,
                         imp_win=0.0, imp_avg=0.0))
        for dn, _ in F.DETS:
            lab = pd.DataFrame(LAB[dn])
            for state in ('A', 'B'):
                on = lab == state                      # filter: flat unless in state
                fnet = net.where(on, 0.0)
                fpos = pos.where(on, 0.0)
                f_ret = fnet[oos].mean(axis=1)
                f_tr = int((fpos.diff().abs() > 0)[oos].sum().sum())
                f_on = float((held & on)[oos].values.mean())
                m = metrics(f_ret, f_on, f_tr)
                if m is None:
                    continue
                imp = lambda k: ((m[k] - base[k]) / abs(base[k])
                                 if base[k] and np.isfinite(base[k]) and base[k] != 0
                                 else np.nan)
                rows.append(dict(strategy=sn, detector=dn, state=state,
                                 cell='%s %s' % (dn, state),
                                 data_pct=float(on[oos].values.mean()), **m,
                                 imp_retexp=imp('retexp'), imp_retdd=imp('retdd'),
                                 imp_pf=imp('pf'), imp_win=imp('win'),
                                 imp_avg=imp('avgtrade')))
    T = pd.DataFrame(rows)
    T.to_csv(os.path.join(ROOTOUT,'/detector_ladder.csv'.lstrip('/')), index=False)

    pd.set_option('display.width', 250, 'display.max_columns', 25)
    f = lambda x: '%.4f' % x
    print('\n' + '=' * 78); print('DETECTOR LADDER — OOS, filter vs unfiltered baseline')
    print('=' * 78)
    print(T[['strategy', 'cell', 'data_pct', 'net_profit', 'retdd', 'pf', 'trades',
             'win', 'avgtrade', 'expo', 'retexp']].to_string(index=False, float_format=f))
    print('\n' + '=' * 78); print('IMPROVEMENT VS BASELINE (negatives are real results)')
    print('=' * 78)
    print(T[['strategy', 'cell', 'data_pct', 'imp_retexp', 'imp_retdd', 'imp_pf',
             'imp_win', 'imp_avg']].to_string(index=False, float_format=f))
    # A percentage improvement against a NEGATIVE baseline means "loses less", not
    # "makes money". Momentum's baseline is negative on every metric, so counting its
    # cells as wins would repeat the exact error STRATEGY_TEMPLATE.md rule 1 warns about.
    B = T[T.cell == 'BASELINE'].set_index('strategy')
    cells = T[T.cell != 'BASELINE'].copy()
    live = cells.strategy.map(lambda s: B.loc[s, 'retdd'] > 0 and B.loc[s, 'retexp'] > 0)
    beat = cells[live & (cells.imp_retdd > 0) & (cells.imp_retexp > 0)]
    print('\ncells beating a POSITIVE baseline on BOTH Ret/DD and Ret/Exp: %d of %d'
          % (len(beat), int(live.sum())))
    if len(beat):
        print(beat[['strategy', 'cell', 'data_pct', 'imp_retdd', 'imp_retexp', 'imp_avg']]
              .to_string(index=False, float_format=f))
    dead = sorted(set(cells.strategy[~live]))
    for s in dead:
        print('%s: baseline is negative (Ret/DD %.3f) — its %d cells are excluded. A cell '
              'that improves on a losing strategy is still losing.'
              % (s, B.loc[s, 'retdd'], int((cells.strategy == s).sum())))


if __name__ == '__main__':
    main()
