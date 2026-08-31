import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""PORTFOLIO SWEET SPOT — the book-size sweep, for any leaderboard.

PREVIEW, never a gate 4 result. Identical method to the mode B sweep:
equal risk weight 1/N, PURE OVERLAY with nothing removed or netted, normalised
so the combined book risks the same 1 R per trade as any single strategy.
Crisis-excluded is primary; all-in is reported beside it, never instead.

THE WINNING N IS CHOSEN BY THE SAME CO-EQUAL RULE THAT RANKS STRATEGIES:
rank each N on total blind R, rank it on Sortino, average the two ranks, Calmar
breaks ties. Using a different selector here than the one used to build the
book would rank the ingredients by one standard and the recipe by another.

    python code/l2sweepn.py --lb results/gate2_modeA_trend_leaderboard.csv \\
                            --slice trend --tag modeA_trend --lo 5 --hi 25

--combine pools two leaderboards into one list and RE-RANKS the pool before
sweeping, so the combined book is chosen on merit across both modes rather than
by interleaving two separate rankings.
"""
import json
import numpy as np, pandas as pd
import l2portfolio as P
import l2rank as RK


def pooled(specs, out):
    """specs: [(leaderboard_path, slice_or_None, mode_letter, label), ...]"""
    fr = []
    for lb, sl, mode, lab in specs:
        D = pd.read_csv(lb, low_memory=False)
        if sl:
            D = D[D.slice == sl]
        D = D.copy()
        D['src_mode'] = mode
        D['src_label'] = lab
        D['src_rank'] = D['rank']
        fr.append(D)
    A = pd.concat(fr, ignore_index=True)
    # Re-rank the POOL. net_of_structure is already per-row from each mode's own
    # null and is carried through untouched; only the ordering is recomputed.
    A = A.drop(columns=[c for c in ('rank', 'rank_R', 'rank_S', 'score')
                        if c in A.columns])
    A['rank_R'] = A.ex_total_R.rank(ascending=False, method='min', na_option='bottom')
    A['rank_S'] = A.ex_sortino.rank(ascending=False, method='min', na_option='bottom')
    A['score'] = (A.rank_R + A.rank_S) / 2.0
    A = A.sort_values(['score', RK.TIEBREAK], ascending=[True, False],
                      kind='mergesort').reset_index(drop=True)
    A['rank'] = np.arange(1, len(A) + 1)
    A.to_csv(out, index=False)
    print('pooled %d rows -> %s' % (len(A), os.path.basename(out)), flush=True)
    return A


def sweep(lb, sl, tag, lo, hi):
    books = P.load(hi, lb=lb, sl=sl)
    rows = []
    for n in range(lo, hi + 1):
        sub = {k: v for k, v in books.items() if k <= n}
        if len(sub) < n:
            break
        for view, exc in (('excl', True), ('allin', False)):
            D, H = P.build(sub, exclude_crisis=exc)
            daily = D.sum(axis=1)
            m = P.metrics(daily)
            act = H.sum(axis=1)
            ad = D[(D != 0).any(axis=1)]
            Cm = ad.corr().values
            tri = Cm[np.triu_indices_from(Cm, 1)]
            rows.append(dict(N=n, view=view, total_R=m['total_R'],
                             avg_annual_R=m['avg_annual_R'], max_dd_R=m['max_dd_R'],
                             sortino=m['sortino'], sharpe=m['sharpe'],
                             calmar=m['calmar'], worst_month_R=m['worst_month_R'],
                             n_trades=m.get('n_trades'),
                             pct_2plus=round(100 * (act >= 2).sum() / max(1, (act > 0).sum()), 1),
                             max_sim=int(act.max()),
                             mean_corr=round(float(np.nanmean(tri)), 4),
                             max_corr=round(float(np.nanmax(tri)), 4)))
    S = pd.DataFrame(rows)
    S.to_csv(os.path.join(ROOTOUT, 'portfolio_sweep_%s.csv' % tag), index=False)
    E = S[S.view == 'excl'].copy()
    # the co-equal rule, applied to the Ns
    E['rk_R'] = E.total_R.rank(ascending=False, method='min')
    E['rk_S'] = E.sortino.rank(ascending=False, method='min')
    E['sel'] = (E.rk_R + E.rk_S) / 2.0
    E = E.sort_values(['sel', 'calmar'], ascending=[True, False], kind='mergesort')
    best = int(E.iloc[0].N)
    print('  %s: sweet spot N=%d  (total R %.2f, Sortino %.2f)'
          % (tag, best, E.iloc[0].total_R, E.iloc[0].sortino), flush=True)
    # the winning book's curve, for the app
    sub = {k: v for k, v in books.items() if k <= best}
    D, H = P.build(sub, exclude_crisis=True)
    daily = D.sum(axis=1)
    d = daily.cumsum()
    curve = [dict(d=str(i)[:10], r=round(float(v), 4)) for i, v in d.items()]
    mm = dict(P.metrics(daily))
    # the portfolio-level fields the app's metric line expects, under the same
    # names l2portfolio uses -- otherwise the line silently prints zeros
    act = H.sum(axis=1)
    ad = D[(D != 0).any(axis=1)]
    Cm = ad.corr().values
    tri = Cm[np.triu_indices_from(Cm, 1)]
    live = int((act > 0).sum())
    mm.update(years=round((daily.index[-1] - daily.index[0]).days / 365.25, 2),
              n_trades=int(sum(len(v) for v in sub.values())),
              pct_days_2plus=round(100 * (act >= 2).sum() / max(1, live), 1),
              max_simultaneous=int(act.max()),
              mean_simultaneous_when_live=round(float(act[act > 0].mean()), 2),
              mean_pairwise_corr=round(float(np.nanmean(tri)), 4),
              max_pairwise_corr=round(float(np.nanmax(tri)), 4))
    src = None
    L = pd.read_csv(lb, low_memory=False)
    if 'src_mode' in L.columns:
        t = L.sort_values('rank').head(best)
        src = {k: int(v) for k, v in t.src_mode.value_counts().items()}
    json.dump(dict(N=best, tag=tag, metrics=mm, mix=src, curve=curve),
              open(os.path.join(ROOTOUT, 'portfolio_preview_%s.json' % tag), 'w'))
    return S, best, books


def main():
    a = sys.argv[1:]
    def opt(k, d=None):
        return a[a.index(k) + 1] if k in a else d
    lo, hi = int(opt('--lo', 5)), int(opt('--hi', 25))
    if '--combine' in a:
        specs = [(os.path.join(ROOTOUT, 'gate2_modeA_trend_leaderboard.csv'),
                  'trend', 'A', 'A-trend'),
                 (os.path.join(ROOTOUT, 'gate2_modeB_leaderboard.csv'),
                  None, 'B', 'B')]
        specs = [s for s in specs if os.path.exists(s[0])]
        out = os.path.join(ROOTOUT, 'gate2_combined_AB_leaderboard.csv')
        pooled(specs, out)
        sweep(out, None, 'combined_AB', lo, hi)
    else:
        sweep(opt('--lb'), opt('--slice'), opt('--tag'), lo, hi)


if __name__ == '__main__':
    main()
