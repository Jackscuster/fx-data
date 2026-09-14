import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""MEMBER-LEVEL STUDIES ON A ROUTED BOOK: per-strategy expectancy, attribution
by build-year quality, the weighted book, and the team-size curve.

Every "build-year quality" ranking is run on all five yardsticks -- Sortino,
expectancy (R per trade), profit factor, Calmar, and the gate-3 composite
(the count of gate-3 bars cleared, then Sortino as the tie-break) -- computed
on the BUILD years of each walk step from the engine's own trade table
(l2walkfwd.metrics), so nothing here looks past the build block. No fixed
thresholds: every sweep covers its full range and the whole curve is written.

  --stage expectancy  each member's own 2016-2020 expectancy net of costs, by
                      slice; how many positive; how many clear the gate-3 bars
                      and the gate-2 floors on the trade years
  --stage attribution deciles of build-year quality per yardstick: share of
                      trade-year book return, of book drawdown, of entries;
                      mean R per trade. Attribution of the NETTED book's daily
                      PnL to members is by each member's share of the sized
                      position on every (pair, day) it holds -- exact for the
                      netting used here, since size on a row is a function of
                      the vote and each member's vote is one unit.
  --stage weighted    member weight proportional to build-year quality (each
                      yardstick, clipped at 0, renormalised) vs equal weight
  --stage teamsize    top-N by each yardstick, N on a fine log grid from 25 to
                      ALL, random-N control at every N (10 draws), 25 on the
                      winner
"""
import argparse, time
import numpy as np, pandas as pd
import l2walkfwd as W
import l2gate3 as G3

YARDS = ['sortino', 'expectancy_R', 'profit_factor', 'calmar', 'gate3_composite']
IDENT = {y: y for y in W.YEARS}


def load(tag):
    W.TAG = tag; os.environ['WF_TAG'] = tag
    W.TRADES_F = W.OUT('wf_trades.pkl'); W.MARKS_F = W.OUT('wf_marks.pkl')
    T = pd.read_pickle(W.TRADES_F); M = pd.read_pickle(W.MARKS_F)
    return T, M, W.trade_year_sums(M)


def quality(T, TY, years):
    """All five yardsticks per member on the given years."""
    D = W.metrics(T, TY, years).set_index('sid')
    bars = G3.BARS
    ok = pd.DataFrame({k: ((D[k] <= v) if k == 'max_dd_frac' else (D[k] >= v)).fillna(False) for k, v in bars.items()})
    D['gate3_composite'] = ok.sum(axis=1) + D.sortino.rank(pct=True).fillna(0) * 0.999  # bars cleared, Sortino as tie-break
    D['gate3_pass'] = ok.all(axis=1)
    return D


# ----------------------------------------------------------------- expectancy
def stage_expectancy(tag):
    T, M, TY = load(tag)
    tr = list(range(W.STEPS[0]['trade'][0], W.STEPS[-1]['trade'][1] + 1))
    D = quality(T, TY, tr)
    D['slice'] = D.index.map(W.field_label)
    D['gate2_floor'] = (D.profit_factor >= W.S.PF_FLOOR) & (D.n >= W.S.MIN_TRADES_BLIND)
    rows = []
    for sl, g in D.groupby('slice'):
        rows.append(dict(slice=sl, members=len(g), expectancy_median=g.expectancy_R.median(), expectancy_mean=g.expectancy_R.mean(),
                         positive=int((g.expectancy_R > 0).sum()), positive_pct=100 * (g.expectancy_R > 0).mean(),
                         gate2_floor_pass=int(g.gate2_floor.sum()), gate3_bars_pass=int(g.gate3_pass.sum()),
                         pf_median=g.profit_factor.median(), sortino_median=g.sortino.median(), trades_median=g.n.median()))
    rows.append(dict(slice='ALL', members=len(D), expectancy_median=D.expectancy_R.median(), expectancy_mean=D.expectancy_R.mean(),
                     positive=int((D.expectancy_R > 0).sum()), positive_pct=100 * (D.expectancy_R > 0).mean(),
                     gate2_floor_pass=int(D.gate2_floor.sum()), gate3_bars_pass=int(D.gate3_pass.sum()),
                     pf_median=D.profit_factor.median(), sortino_median=D.sortino.median(), trades_median=D.n.median()))
    O = pd.DataFrame(rows); O.to_csv(W.OUT('members_expectancy.csv'), index=False)
    D.reset_index().to_csv(W.OUT('members_expectancy_detail.csv'), index=False)
    print(O.to_string(index=False, float_format=lambda v: '%8.3f' % v), flush=True)
    # distribution
    q = D.expectancy_R.quantile([.05, .1, .25, .5, .75, .9, .95])
    print('  expectancy quantiles (R/trade, 2016-2020, net):', q.round(3).to_dict(), flush=True)


# ---------------------------------------------------------------- attribution
def _attrib_walk(T, TY, M, dipb, dayb, member_of_row_weight=True):
    """One NO_CUT walk that also returns, per step, the per-member share of the
    trade-year daily PnL. Uses Book internals: on every row (pair, day) the
    sized position is split among the members voting on that row in
    proportion to their unit votes (all members vote one unit here)."""
    out = {}
    res = W.walk(T, TY, M, IDENT, dipb, dayb, ['ALLPASS'], nocut=True)
    return res['ALLPASS']


def stage_attribution(tag, nbins=10):
    T, M, TY = load(tag)
    # member PnL attribution: rebuild the book per step exactly as walk() does,
    # then attribute row PnL to members by vote share
    rows_out = []
    for bt, dipb, dayb in W.BUDGETS:
        per_member = None
        for si, st in enumerate(W.STEPS):
            b0, b1 = st['build']; t0, t1 = st['trade']
            bsrc = list(range(b0, b1 + 1)); tsrc = list(range(t0, t1 + 1))
            P, _ = W.cut(T, TY, bsrc, apply_bars=False)
            allp = list(P.sid)
            B = W.Book(M[M.sid.isin(allp)], allp)
            w_all = np.ones(len(B.members), np.float32)
            curve, C = W.fit_curve(B, w_all, bsrc)
            ybuild = np.isin(B.dyears, bsrc); ytrade = np.isin(B.dyears, tsrc)
            d0, den, _, _, _, _ = B.series(w_all, curve)
            sc, bD, badj, bwd, bbind = W.scale_of(d0[ybuild], dipb, dayb, use_dip=True)
            per_unit = sc / den
            d1, _, binds, worst, sz, f = B.series(w_all, curve, cap_pct=W.CAP_PCT, per_unit=per_unit, den=den)
            row_pnl = B.last['row_pnl'] * (sc / den)          # per (pair,day) row, in the book's % units
            # vote share: each member's mask on the row, over the row's total votes
            L = B.L; Sm = B.Sm                                  # sparse row x member masks
            votes = np.asarray((L + Sm).sum(axis=1)).ravel()
            share = (L + Sm).multiply(1.0 / np.maximum(votes, 1)[:, None]).tocsr()
            trade_rows = ytrade[B.dpos]
            member_pnl = np.asarray(share[trade_rows].T @ row_pnl[trade_rows]).ravel()
            entries = np.asarray((L + Sm)[trade_rows].sum(axis=0)).ravel()
            # the book's max-drawdown window on this step's trade years: peak to trough
            ds = d1[ytrade] * sc; e = np.cumsum(ds); dd = np.maximum.accumulate(e) - e
            trough = int(np.argmax(dd)); peak = int(np.argmax(e[:trough + 1])) if trough > 0 else 0
            days_t = B.udays[ytrade]; lo_d, hi_d = days_t[peak], days_t[trough]
            in_dd = trade_rows & (B.day.values > lo_d) & (B.day.values <= hi_d)
            member_dd = np.asarray(share[in_dd].T @ row_pnl[in_dd]).ravel()   # each member's PnL inside the drawdown (negative = contributed)
            Q = quality(T, TY, bsrc).reindex(B.members)
            step = pd.DataFrame({'sid': B.members, 'pnl': member_pnl, 'dd': member_dd, 'rows': entries, 'step': si + 1})
            for y in YARDS: step[y] = Q[y].values
            per_member = step if per_member is None else pd.concat([per_member, step])
        book_total = per_member.pnl.sum()
        agg = per_member.groupby('sid').agg(pnl=('pnl', 'sum'), dd=('dd', 'sum'), rows=('rows', 'sum'), **{y: (y, 'mean') for y in YARDS})
        dd_total = agg.dd.sum()
        agg['slice'] = agg.index.map(W.field_label)
        agg.to_csv(W.OUT('members_attribution_detail_%s.csv' % bt))
        # trade-level mean R per member on the trade years
        tr = list(range(W.STEPS[0]['trade'][0], W.STEPS[-1]['trade'][1] + 1))
        Dt = quality(T, TY, tr).reindex(agg.index)
        for y in YARDS:
            r = agg[y].rank(pct=True, method='first')
            tier = np.minimum((r * nbins).astype(int) + 1, nbins)   # 1 = worst build-year quality, nbins = best
            for t, g in agg.groupby(tier):
                rows_out.append(dict(budget=bt, yardstick=y, tier=int(t), members=len(g),
                                     share_of_return_pct=100 * g.pnl.sum() / book_total,
                                     share_of_drawdown_pct=100 * g.dd.sum() / dd_total,
                                     mean_member_pnl=g.pnl.mean(), share_of_entries_pct=100 * g.rows.sum() / agg.rows.sum(),
                                     mean_R_per_trade_tradeyears=Dt.loc[g.index, 'expectancy_R'].mean(),
                                     build_quality_median=g[y].median()))
    O = pd.DataFrame(rows_out); O.to_csv(W.OUT('members_attribution.csv'), index=False)
    piv = O[O.budget == 'team1'].pivot_table(index='tier', columns='yardstick', values='share_of_return_pct')
    print('=== share of trade-year book return (%) by build-year quality decile (1 = worst, 10 = best), team1 ===', flush=True)
    print(piv.to_string(float_format=lambda v: '%7.1f' % v), flush=True)
    piv3 = O[O.budget == 'team1'].pivot_table(index='tier', columns='yardstick', values='share_of_drawdown_pct')
    print('=== share of the book drawdown (%) by build decile (peak-to-trough window, both steps) ===', flush=True)
    print(piv3.to_string(float_format=lambda v: '%7.1f' % v), flush=True)
    piv2 = O[O.budget == 'team1'].pivot_table(index='tier', columns='yardstick', values='mean_R_per_trade_tradeyears')
    print('=== mean R per trade on the trade years by build decile ===', flush=True)
    print(piv2.to_string(float_format=lambda v: '%7.3f' % v), flush=True)
    return O


# ------------------------------------------------------------------ weighted
def stage_weighted(tag):
    T, M, TY = load(tag)
    rows = []
    for bt, dipb, dayb in W.BUDGETS:
        r = W.walk(T, TY, M, IDENT, dipb, dayb, ['ALLPASS'], nocut=True)
        k = r['ALLPASS'][0]; k.update(yardstick='equal', budget=bt); rows.append(k)
        print('    %-6s %-16s median %6.3f%%  worst %6.3f%%  maxDD %5.2f%%  PF %.2f' % (bt, 'equal', k['median_year_pct'], k['worst_year_pct'], k['max_dd_pct'], k['profit_factor']), flush=True)
        for y in YARDS:
            def pick(P, _y=y, **kw):
                # weights from the BUILD years of this step: quality of each passer, clipped at 0, renormalised to len(P)
                Q = quality(kw['T'], kw['TY'], list(kw['build'])).reindex(P.sid)
                wq = Q[_y].clip(lower=0).fillna(0).values
                if _y == 'expectancy_R': wq = np.clip(wq, 0, None)
                wq = wq / max(wq.mean(), 1e-9)
                return list(P.sid), dict(zip(P.sid, wq))
            W.STRUCTURES['WEIGHTED'] = pick
            r = W.walk(T, TY, M, IDENT, dipb, dayb, ['WEIGHTED'], nocut=True)
            k = r['WEIGHTED'][0]; k.update(yardstick=y, budget=bt); rows.append(k)
            print('    %-6s %-16s median %6.3f%%  worst %6.3f%%  maxDD %5.2f%%  PF %.2f' % (bt, y, k['median_year_pct'], k['worst_year_pct'], k['max_dd_pct'], k['profit_factor']), flush=True)
    O = pd.DataFrame(rows); O.to_csv(W.OUT('members_weighted.csv'), index=False)


# ------------------------------------------------------------------ team size
_TS = {}


def _init_ts():
    W.S.load_costs()
    _TS['T'], _TS['M'] = W._worker_tables()
    _TS['TY'] = W.trade_year_sums(_TS['M'])


def _ts_one(args):
    n, yard, seed, dipb, dayb = args
    try:
        T, M, TY = _TS['T'], _TS['M'], _TS['TY']
        def pick(P, _n=n, _y=yard, _seed=seed, **kw):
            if _seed is None:
                Q = quality(kw['T'], kw['TY'], list(kw['build'])).reindex(P.sid)
                order = Q[_y].fillna(-1e9).sort_values(ascending=False).index
                return list(order[:_n])
            rng = np.random.default_rng(_seed)
            return list(rng.choice(P.sid.values, size=min(_n, len(P)), replace=False))
        W.STRUCTURES['TOPN'] = pick
        r = W.walk(T, TY, M, IDENT, dipb, dayb, ['TOPN'], nocut=True)
        k = r['TOPN'][0]
        return dict(n=n, yardstick=yard, seed=(-1 if seed is None else seed), dipb=dipb, median_year_pct=k['median_year_pct'],
                    max_dd_pct=k['max_dd_pct'], worst_year_pct=k['worst_year_pct'], profit_factor=k['profit_factor'])
    except Exception as e:
        return dict(n=n, yardstick=yard, seed=(-1 if seed is None else seed), dipb=dipb, err=type(e).__name__ + ': ' + str(e)[:80])


def stage_teamsize(tag, jobs, n_rand):
    import multiprocessing as mp
    T, M, TY = load(tag)
    os.environ['WF_EXPECT_SIDS'] = str(int(T.sid.nunique()))
    total = int(T.sid.nunique())
    grid = sorted(set([int(x) for x in np.geomspace(25, total, 14)] + [total]))
    print('  N grid: %s' % grid, flush=True)
    args = []
    for bt, dipb, dayb in W.BUDGETS:
        for n in grid:
            for y in YARDS:
                args.append((n, y, None, dipb, dayb))
            for s in range(n_rand):
                args.append((n, 'random', 20260914 + s, dipb, dayb))
    print('  %d walks' % len(args), flush=True)
    t0 = time.time()
    with mp.Pool(jobs, initializer=_init_ts) as pool:
        got = pool.map(_ts_one, args, chunksize=2)
    O = pd.DataFrame(got); O['budget'] = O.dipb.map({3.6: 'team1', 5.4: 'team2'})
    O.to_csv(W.OUT('members_teamsize.csv'), index=False)
    print('  done in %.1f min; errors %d' % ((time.time() - t0) / 60, O.get('err', pd.Series(dtype=object)).notna().sum()), flush=True)
    ok = O[O.get('err', pd.Series(index=O.index, dtype=object)).isna()] if 'err' in O else O
    real = ok[ok.yardstick != 'random'].pivot_table(index='n', columns=['budget', 'yardstick'], values='median_year_pct')
    rnd = ok[ok.yardstick == 'random'].groupby(['budget', 'n']).median_year_pct.agg(['mean', 'std', 'max'])
    print('=== top-N by build-year quality, median year %, team1 ===', flush=True)
    print(real['team1'].to_string(float_format=lambda v: '%7.3f' % v), flush=True)
    print('=== random-N control, team1 (mean / sd / max over %d draws) ===' % n_rand, flush=True)
    print(rnd.loc['team1'].to_string(float_format=lambda v: '%7.3f' % v), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', required=True, choices=['expectancy', 'attribution', 'weighted', 'teamsize'])
    ap.add_argument('--suffix', default='_routed_tirexcl_actweak')
    ap.add_argument('--jobs', type=int, default=2)
    ap.add_argument('--n-rand', type=int, default=10)
    a = ap.parse_args()
    W.S.load_costs()
    t0 = time.time(); print('=== %s on %s ===' % (a.stage, a.suffix), flush=True)
    {'expectancy': lambda: stage_expectancy(a.suffix), 'attribution': lambda: stage_attribution(a.suffix),
     'weighted': lambda: stage_weighted(a.suffix), 'teamsize': lambda: stage_teamsize(a.suffix, a.jobs, a.n_rand)}[a.stage]()
    print('=== %s done in %.1f min ===' % (a.stage, (time.time() - t0) / 60), flush=True)


if __name__ == '__main__':
    main()
