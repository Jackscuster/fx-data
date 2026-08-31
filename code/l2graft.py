import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""THE GRAFT — mode B's N=13 book with mode A-trend's #1 and #2 added. PREVIEW.

NOT a re-ranked pool. The pooled sweep re-ranked A and B together and let the
rule choose 18; this takes B's own sweet-spot book EXACTLY as it stands and
grafts on the two A strategies that earned their way into the pooled book. The
question it answers is narrower and more useful: does adding A's two best to a
finished B book help, or does the pooled result depend on the reshuffling?

Same overlay math as every other preview: equal risk weight 1/N over 15,
nothing removed or netted, normalised to 1 R per trade, crisis-excluded primary.
"""
import json
import numpy as np, pandas as pd
import l2portfolio as P

A_OFF = 100          # keep A's ranks from colliding with B's in the book dict


def build_book():
    B = P.load(13)
    A = P.load(2, lb=os.path.join(ROOTOUT, 'gate2_modeA_trend_leaderboard.csv'),
               sl='trend')
    books = dict(B)
    for k, v in A.items():
        books[A_OFF + k] = v
    return books


def block(books, exclude_crisis=True):
    D, H = P.build(books, exclude_crisis=exclude_crisis)
    daily = D.sum(axis=1)
    m = dict(P.metrics(daily))
    act = H.sum(axis=1)
    ad = D[(D != 0).any(axis=1)]
    Cm = ad.corr().values
    tri = Cm[np.triu_indices_from(Cm, 1)]
    live = int((act > 0).sum())
    m.update(years=round((daily.index[-1] - daily.index[0]).days / 365.25, 2),
             n_trades=int(sum(len(v) for v in books.values())),
             pct_days_2plus=round(100 * (act >= 2).sum() / max(1, live), 1),
             max_simultaneous=int(act.max()),
             mean_simultaneous_when_live=round(float(act[act > 0].mean()), 2),
             mean_pairwise_corr=round(float(np.nanmean(tri)), 4),
             max_pairwise_corr=round(float(np.nanmax(tri)), 4))
    return m, daily


def main():
    books = build_book()
    m, daily = block(books, True)
    ma, _ = block(books, False)
    curve = [dict(d=str(i)[:10], r=round(float(v), 4))
             for i, v in daily.cumsum().items()]
    json.dump(dict(N=len(books), tag='B13_plusA2', metrics=m,
                   mix={'B': 13, 'A': 2}, curve=curve),
              open(os.path.join(ROOTOUT, 'portfolio_preview_B13_plusA2.json'), 'w'))
    pd.DataFrame([dict(view='excl', **m), dict(view='allin', **ma)]).to_csv(
        os.path.join(ROOTOUT, 'portfolio_preview_B13_plusA2.csv'), index=False)
    for k in ('total_R', 'avg_annual_R', 'max_dd_R', 'sortino', 'sharpe',
              'calmar', 'worst_month_R', 'n_trades', 'pct_days_2plus',
              'mean_pairwise_corr', 'max_pairwise_corr'):
        print('  %-22s excl %-10s all-in %s' % (k, m.get(k), ma.get(k)))
    print('DONE', flush=True)


if __name__ == '__main__':
    main()
