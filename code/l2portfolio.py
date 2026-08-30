import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""PORTFOLIO PREVIEW — the crisis-excluded top 10 merged onto one calendar.

PREVIEW. Gate 4 does this properly, with real weighting and the drop-one test.
This is equal risk weight and nothing else, so that the SHAPE of the combined
book is visible before gate 4 rather than after.

THE NORMALISATION, stated because it decides every number below. Each strategy
risks 1 R per trade on its own. Ten strategies at equal weight each risk 1/10 R,
so the combined book risks the SAME 1 R per trade as any single strategy would.
Combined total R is therefore directly comparable to a single strategy's total R
-- it is not ten books stacked, it is one book of the same size.

R IS BOOKED ON THE EXIT DATE, because that is when the money is realised. A
trade opened in 2013 and closed in 2014 belongs to 2014's P&L. Holding overlap
uses the ENTRY-to-EXIT span, because that is when capital is committed -- the
two questions want different dates and conflating them would understate overlap.

CRISIS-EXCLUDED IS PRIMARY, matching the ranking that selected these ten. The
all-in figure is reported beside it, never instead of it.
"""
import json
import numpy as np, pandas as pd
import l2deliver as DL, l2crisis as C

N_STRAT = 10
SUF = ''      # output suffix, set by the CLI so a top-20 run never overwrites top-10


def load(n=N_STRAT):
    wins = C.windows()
    L = pd.read_csv(os.path.join(ROOTOUT, 'gate2_modeB_leaderboard.csv'),
                    low_memory=False).sort_values('rank').head(n)
    books = {}
    for cfg in L.to_dict('records'):
        rk = int(cfg['rank'])
        T = DL.blind_trades(cfg, wins)
        T['rank'] = rk
        books[rk] = T
        print('  loaded rank %2d: %4d blind trades (%d crisis)'
              % (rk, len(T), int(T.crisis.sum())), flush=True)
    return books


def metrics(daily):
    d = daily.dropna()
    if not len(d):
        return {}
    tot = float(d.sum())
    eq = d.cumsum()
    ddv = eq.cummax() - eq
    dd = float(ddv.max())
    neg = d[d < 0]
    dn = float(neg.std(ddof=1)) if len(neg) > 1 else 0.0
    sd = float(d.std(ddof=1)) if len(d) > 1 else 0.0
    yrs = (d.index[-1] - d.index[0]).days / 365.25 or 1
    m = d.resample('ME').sum() if hasattr(d, 'resample') else None
    return dict(total_R=round(tot, 2), years=round(yrs, 2),
                avg_annual_R=round(tot / yrs, 2),
                max_dd_R=round(dd, 2),
                sortino=round(float(d.mean() / dn * np.sqrt(252)), 2) if dn > 0 else None,
                sharpe=round(float(d.mean() / sd * np.sqrt(252)), 2) if sd > 0 else None,
                calmar=round(tot / dd, 2) if dd > 0 else None,
                worst_month_R=round(float(m.min()), 2) if m is not None and len(m) else None,
                worst_month=str(m.idxmin().date()) if m is not None and len(m) else None,
                best_month_R=round(float(m.max()), 2) if m is not None and len(m) else None,
                n_trades=None)


def build(books, exclude_crisis=True):
    W = 1.0 / len(books)                      # equal risk weight
    frames, holds = {}, {}
    lo = min(b.entry.min() for b in books.values())
    hi = max(b.exit.max() for b in books.values())
    cal = pd.date_range(lo, hi, freq='D')
    for rk, T in books.items():
        t = T[~T.crisis] if exclude_crisis else T
        s = t.groupby(t.exit.dt.normalize()).R.sum() * W
        frames[rk] = s.reindex(cal, fill_value=0.0)
        h = pd.Series(0, index=cal, dtype=int)
        for r in t.itertuples():                       # capital committed span
            h.loc[r.entry:r.exit] = 1
        holds[rk] = h
    D = pd.DataFrame(frames).sort_index()
    H = pd.DataFrame(holds).sort_index()
    return D, H


def report(n=N_STRAT):
    books = load(n)
    out = {}
    for tag, exc in (('crisis_excluded', True), ('all_in', False)):
        D, H = build(books, exclude_crisis=exc)
        daily = D.sum(axis=1)
        m = metrics(daily)
        m['n_trades'] = int(sum(len(t[~t.crisis] if exc else t) for t in books.values()))
        act = H.sum(axis=1)
        live = act[act > 0]
        m['days_with_any_position'] = int((act > 0).sum())
        m['days_2plus'] = int((act >= 2).sum())
        m['pct_days_2plus'] = round(100 * (act >= 2).sum() / max(1, (act > 0).sum()), 1)
        m['max_simultaneous'] = int(act.max())
        m['mean_simultaneous_when_live'] = round(float(live.mean()), 2) if len(live) else None
        # correlation on days where at least one strategy realised something
        act_d = D[(D != 0).any(axis=1)]
        Cm = act_d.corr()
        m['mean_pairwise_corr'] = round(float(
            Cm.values[np.triu_indices_from(Cm.values, 1)].mean()), 4)
        m['max_pairwise_corr'] = round(float(
            Cm.values[np.triu_indices_from(Cm.values, 1)].max()), 4)
        out[tag] = m
        if exc:
            eq = daily.cumsum()
            nz = eq[daily != 0]
            json.dump(dict(
                preview=True,
                note='PREVIEW. Equal risk weight, 1/N each, so the combined book '
                     'risks the same 1 R per trade as any single strategy. Gate 4 '
                     'does this properly with real weighting and the drop-one test.',
                curve=[dict(d=str(i.date()), r=round(float(v), 3))
                       for i, v in nz.items()],
                metrics=m,
                corr=[dict(a=int(a), b=int(b), r=round(float(Cm.loc[a, b]), 4))
                      for a in Cm.index for b in Cm.columns if a < b]),
                open(os.path.join(ROOTOUT, 'portfolio_preview%s.json' % SUF), 'w'))
            Cm.round(4).to_csv(os.path.join(ROOTOUT, 'portfolio_corr%s.csv' % SUF))
    pd.DataFrame(out).to_csv(os.path.join(ROOTOUT, 'portfolio_preview%s.csv' % SUF))
    return out, books


if __name__ == '__main__':
    import sys as _s
    n = int(_s.argv[1]) if len(_s.argv) > 1 else N_STRAT
    SUF = '' if n == 10 else '_top%d' % n
    globals()['SUF'] = SUF
    print('portfolio preview over the top %d (files suffixed %r)' % (n, SUF), flush=True)
    out, books = report(n)
    for tag, m in out.items():
        print('\n=== %s ===' % tag.upper())
        for k, v in m.items():
            print('  %-30s %s' % (k, v))
    print('\nDONE')
