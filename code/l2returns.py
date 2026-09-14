import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""THE RETURN SEARCH ON THE NO_CUT BOOK. Same walk-forward, scale set on the
build blocks only, both budgets, full KPIs, and for every row whether the
trade years stayed inside the budget they were sized to.

  --stage costs      four cost models on the same trades: zero, as run (spreads
                     x1.5 markup, crisis x2), raw spreads (no markup), and the
                     19:00 NY entry cost from entry_timing.csv. Drag = share of
                     the zero-cost median year each model takes.
  --stage voltarget  the sized book rescaled daily to a constant realised-vol
                     target -- the vol of the step's own build block -- from a
                     trailing 20- and 60-day estimate, lagged one day, leverage
                     capped at 3. Applied to the daily series, which is exact
                     when every position scales together, as it does here.
  --stage parity     equal risk per G8 currency: a per-pair size multiplier,
                     iterated on the build block until the eight currency
                     blocks carry equal variance share; JPY share before/after.
  --stage peryear    NO_CUT return, max DD and realised vol, each trade year.
  --stage dirnull    writes the permission table for the DIRECTION-PRESERVING
                     null (the bars on which the real book was net long / net
                     short per pair); the null itself is l2walkfwd --stage
                     nullre --nocut with WF_ALLOWED pointing at it.
  --stage report     one table.

Sizing three-way is l2walkfwd --stage sizing --nocut (NO_CUT and its
slice-balanced twin, rules a/b/c). Everything here reads the engine pickles of
--suffix and writes results/returns_<stage><suffix>.csv.
"""
import argparse, time
import numpy as np, pandas as pd
import l2walkfwd as W
import l2sweep as S

MAJORS = {'EURUSD', 'GBPUSD', 'AUDUSD', 'NZDUSD', 'USDCAD', 'USDCHF', 'USDJPY'}
IDENT = {y: y for y in W.YEARS}


def kpis(x, days):
    W._MONTHS = pd.DatetimeIndex(days)
    return W.kpis(np.asarray(x, float), pd.DatetimeIndex(days).year.values)


def within(k, dipb, dayb):
    """Did the trade years stay inside the budget the book was sized to."""
    return bool(k['max_dd_pct'] <= dipb and k['dip95_pct'] <= dipb and k['worst_day_pct'] <= dayb)


def load(tag):
    W.TAG = tag; os.environ['WF_TAG'] = tag
    W.TRADES_F = W.OUT('wf_trades.pkl'); W.MARKS_F = W.OUT('wf_marks.pkl')
    T = pd.read_pickle(W.TRADES_F); M = pd.read_pickle(W.MARKS_F)
    return T, M, W.trade_year_sums(M)


def nocut_walk(T, TY, M, dipb, dayb, **kw):
    r = W.walk(T, TY, M, IDENT, dipb, dayb, ['ALLPASS'], nocut=True, **kw)
    return r['ALLPASS']


# ------------------------------------------------------------------- costs
def recost(T, M, field, f_new_of_pair, label):
    """Same trades, a different cost per pair. cost_R is linear in the cost
    fraction, so each trade's charge is rescaled by f_new / f_old and the
    difference moved out of its entry-day mark and its R."""
    K, BR = W.recover_k(T, M, field)
    old = S.COSTS
    rows = []
    for r in K.itertuples():
        f_old = old.get(r.pair, 0.0)
        if not f_old:
            continue
        atr = W.atr_of(BR, r.pair, r.atr_len)[r.b0]
        if not np.isfinite(atr) or atr <= 0:
            continue
        ent = BR[r.pair]['c'][r.b0]
        units = S.RISK / (r.atr_mult * atr)
        c_old = float(S._cost_R(r.pair, np.array([ent]), np.array([units]), np.array([r.entry]))[0])
        rows.append((r.sid, r.tid, c_old * (f_new_of_pair(r.pair) / f_old - 1.0)))
    D = pd.DataFrame(rows, columns=['sid', 'tid', 'delta']).set_index(['sid', 'tid'])
    T2 = T.copy(); M2 = M.copy()
    key = pd.MultiIndex.from_frame(T2[['sid', 'tid']].astype({'sid': str}))
    d = D.delta.reindex(key).fillna(0.0).values
    T2['R'] = T2.R - d
    first = M2.groupby(['sid', 'tid'], observed=True).cumcount() == 0
    keyM = pd.MultiIndex.from_frame(M2.loc[first, ['sid', 'tid']].astype({'sid': str}))
    M2.loc[first, 'mark'] = (M2.loc[first, 'mark'] - D.delta.reindex(keyM).fillna(0.0).values).astype(np.float32)
    print('  %-12s: %d trades recosted, mean delta R %+.4f' % (label, len(D), D.delta.mean()), flush=True)
    return T2, M2


def stage_costs(tag, field):
    T, M, TY = load(tag)
    tab = pd.read_csv(os.path.join(ROOTOUT, 'cost_table.csv')).set_index('pair')
    et = pd.read_csv(os.path.join(ROOTOUT, 'entry_timing.csv'))
    e19 = et[(et.entry_time.str.startswith('19:00')) & (et.period.str.startswith('IS'))].set_index('group').total_cost_pips
    rec = pd.read_csv(os.path.join(ROOTOUT, 'spread_reconciliation.csv')).set_index('pair') if os.path.exists(os.path.join(ROOTOUT, 'spread_reconciliation.csv')) else None
    models = {
        'zero':        lambda p: 0.0,
        'as_run':      lambda p: float(tab.cost_frac_roundtrip[p]),
        'raw_spread':  lambda p: float(tab.cost_frac_roundtrip[p] / tab.markup[p]),
        'entry_1900':  lambda p: float(e19['major' if p in MAJORS else 'cross'] * tab.pip_size[p] / tab.median_price[p]),
    }
    if rec is not None:
        # MEASURED per pair from the OANDA hourly bid/ask, 2016-2020 medians (l2spread.py)
        models['oanda_1900'] = lambda p: float(rec.oanda_19_pips[p] * tab.pip_size[p] / tab.median_price[p])
        models['oanda_1700'] = lambda p: float(rec.oanda_17_pips[p] * tab.pip_size[p] / tab.median_price[p])
        models['oanda_best_hour'] = lambda p: float(rec.oanda_best_pips[p] * tab.pip_size[p] / tab.median_price[p])
    print('  19:00 NY IS cost, pips: %s  (assumed round-trip, as cost_table.marked_up_pips is)' % e19.round(3).to_dict(), flush=True)
    rows = []
    for name, f in models.items():
        T2, M2 = (T, M) if name == 'as_run' else recost(T, M, field, f, name)
        TY2 = W.trade_year_sums(M2)
        for bt, dipb, dayb in W.BUDGETS:
            k, cuts, x, dy = nocut_walk(T2, TY2, M2, dipb, dayb)
            k.update(model=name, budget=bt, structure='NO_CUT', within_budget=within(k, dipb, dayb),
                     mean_cost_bp=np.mean([f(p) * 1e4 for p in tab.index]))
            rows.append(k)
            print('    %-12s %-6s median %6.3f%%  worst %6.3f%%  maxDD %5.2f%%  PF %.2f' % (name, bt, k['median_year_pct'], k['worst_year_pct'], k['max_dd_pct'], k['profit_factor']), flush=True)
    O = pd.DataFrame(rows)
    z = O[O.model == 'zero'].set_index('budget').median_year_pct
    O['drag_pct_of_median'] = [100.0 * (1 - r.median_year_pct / z[r.budget]) for r in O.itertuples()]
    O.to_csv(W.OUT('returns_costs.csv'), index=False)
    print(O[['model', 'budget', 'mean_cost_bp', 'median_year_pct', 'drag_pct_of_median', 'max_dd_pct', 'within_budget']].to_string(index=False, float_format=lambda v: '%7.3f' % v), flush=True)


# -------------------------------------------------------------- vol target
def stage_voltarget(tag):
    T, M, TY = load(tag)
    rows = []
    for bt, dipb, dayb in W.BUDGETS:
        k0, cuts, x, dy = nocut_walk(T, TY, M, dipb, dayb)
        k0.update(model='as_run', window=0, budget=bt, structure='NO_CUT', target_vol_pct=np.nan,
                  within_budget=within(k0, dipb, dayb), mean_leverage=1.0)
        rows.append(k0)
        for win in (20, 60):
            ys, ds = [], []
            for c in cuts:
                bd = pd.Series(c['build_daily'], index=pd.DatetimeIndex(c['build_days']))
                st = c['step']
                lo, hi = W.STEPS[st - 1]['trade']
                td = pd.Series(x, index=pd.DatetimeIndex(dy))
                td = td[(td.index.year >= lo) & (td.index.year <= hi)]
                target = bd.std() * np.sqrt(252)               # the build block's own vol
                full = pd.concat([bd, td])
                sig = full.rolling(win).std().shift(1) * np.sqrt(252)
                lev = (target / sig).clip(upper=3.0).reindex(td.index).fillna(1.0)
                ys.append(td.values * lev.values); ds.append(td.index)
            y = np.concatenate(ys); d = pd.DatetimeIndex(np.concatenate([q.values for q in ds]))
            k = kpis(y, d)
            k.update(model='voltarget_%d' % win, window=win, budget=bt, structure='NO_CUT',
                     target_vol_pct=float(target), within_budget=within(k, dipb, dayb),
                     mean_leverage=float(np.mean(np.concatenate([(target / (pd.concat([pd.Series(c['build_daily'], index=pd.DatetimeIndex(c['build_days'])), pd.Series(x, index=pd.DatetimeIndex(dy))]).rolling(win).std().shift(1) * np.sqrt(252))).clip(upper=3.0).dropna().values for c in cuts]))))
            rows.append(k)
            print('    %-12s %-6s median %6.3f%%  worst %6.3f%%  maxDD %5.2f%%  DIP95 %5.2f%%  lev %.2f' % (k['model'], bt, k['median_year_pct'], k['worst_year_pct'], k['max_dd_pct'], k['dip95_pct'], k['mean_leverage']), flush=True)
    O = pd.DataFrame(rows); O.to_csv(W.OUT('returns_voltarget.csv'), index=False)


# ------------------------------------------------------------------ parity
def ccy_shares(cuts, years):
    """Variance share of each currency block over the given years (build)."""
    C = pd.concat([c['ccy_daily'] for c in cuts])
    C = C[~C.index.duplicated()]
    C = C[C.index.year.isin(years)]
    tot = C.sum(axis=1)
    cov = C.apply(lambda s: np.cov(s, tot)[0, 1])
    return (cov / tot.var()).sort_values(ascending=False)


def stage_parity(tag):
    T, M, TY = load(tag)
    rows, shares = [], []
    build_years = list(range(W.STEPS[0]['build'][0], W.STEPS[-1]['build'][1] + 1))
    trade_years = list(range(W.STEPS[0]['trade'][0], W.STEPS[-1]['trade'][1] + 1))
    for bt, dipb, dayb in W.BUDGETS:
        g = None
        for it in range(4):
            k, cuts, x, dy = nocut_walk(T, TY, M, dipb, dayb, pair_scale=g)
            sh_b = ccy_shares(cuts, build_years); sh_t = ccy_shares(cuts, trade_years)
            shares.append(dict(budget=bt, iteration=it, **{'build_' + c: v for c, v in sh_b.items()}, **{'trade_' + c: v for c, v in sh_t.items()}))
            k.update(model='parity_iter%d' % it if it else 'as_run', iteration=it, budget=bt, structure='NO_CUT',
                     within_budget=within(k, dipb, dayb), jpy_share_build=float(sh_b.get('JPY', np.nan)),
                     jpy_share_trade=float(sh_t.get('JPY', np.nan)), max_share_build=float(sh_b.max()))
            rows.append(k)
            print('    %-6s iter %d: median %6.3f%%  maxDD %5.2f%%  JPY share build %.3f trade %.3f  max block %.3f (%s)'
                  % (bt, it, k['median_year_pct'], k['max_dd_pct'], sh_b.get('JPY', np.nan), sh_t.get('JPY', np.nan), sh_b.max(), sh_b.idxmax()), flush=True)
            # next multipliers: down-weight the blocks carrying more than their share
            tgt = 1.0 / len(sh_b)
            f = (tgt / sh_b.clip(lower=1e-4)) ** 0.5
            g = {p: float((g or {}).get(p, 1.0) * np.sqrt(f[p[:3]] * f[p[3:]])) for p in set(str(q) for q in M.pair.cat.categories)}
            m = np.mean(list(g.values())); g = {p: v / m for p, v in g.items()}
    pd.DataFrame(rows).to_csv(W.OUT('returns_parity.csv'), index=False)
    pd.DataFrame(shares).to_csv(W.OUT('returns_parity_shares.csv'), index=False)


# ----------------------------------------------------------------- per year
def stage_peryear(tag):
    T, M, TY = load(tag)
    rows = []
    for bt, dipb, dayb in W.BUDGETS:
        k, cuts, x, dy = nocut_walk(T, TY, M, dipb, dayb)
        s = pd.Series(x, index=pd.DatetimeIndex(dy))
        for y, g in s.groupby(s.index.year):
            e = g.cumsum(); dd = float((e.cummax() - e).max())
            rows.append(dict(budget=bt, structure='NO_CUT', year=int(y), return_pct=float(g.sum()), max_dd_pct=dd,
                             realised_vol_pct=float(g.std() * np.sqrt(252)), worst_day_pct=float(-g.min()),
                             within_dip_budget=dd <= dipb, within_day_budget=float(-g.min()) <= dayb))
    O = pd.DataFrame(rows); O.to_csv(W.OUT('returns_peryear.csv'), index=False)
    print(O.to_string(index=False, float_format=lambda v: '%7.3f' % v), flush=True)


# ---------------------------------------------------- direction-preserving null
def stage_dirnull(tag):
    T, M, TY = load(tag)
    net = M.groupby(['pair', 'day'], observed=True)['dir'].sum()
    allowed = {}
    for p, g in net.groupby(level=0, observed=True):
        s = g.droplevel(0)
        allowed[(str(p), 'dir+1')] = (s > 0)
        allowed[(str(p), 'dir-1')] = (s < 0)
    out = W.OUT('route_allowed_dirnull.pkl'); pd.to_pickle(allowed, out)
    share = np.mean([v.mean() for v in allowed.values()])
    print('  wrote %s: %d pair-direction masks, mean permitted share %.3f' % (out, len(allowed), share), flush=True)
    print('  run: WF_ALLOWED=%s python3 code/l2walkfwd.py --stage nullre --nocut --n-null 25 --suffix <dirnull suffix> ...' % out, flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', required=True, choices=['costs', 'voltarget', 'parity', 'peryear', 'dirnull'])
    ap.add_argument('--suffix', default='_cleanfield_4slice')
    ap.add_argument('--field-file', default=os.path.join(ROOTOUT, 'gate2_cleanfield_4slice.csv'))
    ap.add_argument('--slices', default='A-trend,A-chop,B-chop,B-trend')
    a = ap.parse_args()
    W.S.load_costs()
    os.environ['WF_FIELD_FILE'] = os.path.abspath(a.field_file); os.environ['WF_SLICES'] = a.slices
    t0 = time.time()
    print('=== %s on %s ===' % (a.stage, a.suffix), flush=True)
    if a.stage == 'costs':
        F = W.load_field(tuple(a.slices.split(',')), a.field_file)
        stage_costs(a.suffix, F)
    elif a.stage == 'voltarget':
        stage_voltarget(a.suffix)
    elif a.stage == 'parity':
        stage_parity(a.suffix)
    elif a.stage == 'peryear':
        stage_peryear(a.suffix)
    elif a.stage == 'dirnull':
        stage_dirnull(a.suffix)
    print('=== %s done in %.1f min ===' % (a.stage, (time.time() - t0) / 60), flush=True)


if __name__ == '__main__':
    main()
