import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""EXIT OWNERSHIP WHEN MEMBERS AGREE -- item 11.

  (a) as now: the netted book. Every member's own tuned stop/TP/legs run; the
      (pair, day) position is re-netted daily and its P&L is the size-weighted
      average of the voting members' marks. That is l2walkfwd.walk.
  (b) best member owns it: a POSITION LEDGER. A position on a pair opens the
      day the net vote turns nonzero, sized by the agreement curve at that
      moment and never resized; it is OWNED by the agreeing member with the
      highest build-year quality (each of the five yardsticks, fitted on the
      walk step's build block), and it lives and dies on that member's own
      marks -- the owner's stop, target and legs. When the owner's trade
      exits the position closes; if the vote is still on the next day a new
      position opens with a new owner. --stage bestmember.
  (c) as now + the volatility floor: no new position on a pair whose ATR sits
      in the bottom q of its own trailing-year distribution (lagged one bar),
      q swept across its full range; the whole curve reported. --stage volfloor.

Everything is sized on the build blocks only, both budgets, and the trade
years' KPIs are reported with whether they stayed inside both limits.
"""
import argparse, time
import numpy as np, pandas as pd
import l2walkfwd as W
import l2members as LM

IDENT = {y: y for y in W.YEARS}


def load(tag):
    W.TAG = tag; os.environ['WF_TAG'] = tag
    W.TRADES_F = W.OUT('wf_trades.pkl'); W.MARKS_F = W.OUT('wf_marks.pkl')
    T = pd.read_pickle(W.TRADES_F); M = pd.read_pickle(W.MARKS_F)
    return T, M, W.trade_year_sums(M)


# --------------------------------------------------------------- (b) ledger
def ledger_step(M, T, TY, bsrc, tsrc, yard, dipb, dayb):
    """One walk step under best-member ownership. Returns the trade-year daily
    series (already scaled) and diagnostics."""
    Q = LM.quality(T, TY, bsrc)
    q = Q[yard].fillna(-1e9)
    allp = sorted(set(M.sid.astype(str)))
    B = W.Book(M[M.sid.isin(allp)], allp)
    w = np.ones(len(B.members), np.float32)
    curve, C = W.fit_curve(B, w, bsrc)
    # per (pair, day): the net vote, the fraction, the curve size -- as the book sees it
    nl = B.L @ w; ns = B.Sm @ w; net = nl - ns
    f = np.abs(net) / max(float(w.sum()), 1.0)
    sz_row = curve(f) * (np.abs(net) >= 0.5)
    rows = pd.DataFrame({'pair': B.pair, 'day': B.day, 'net': net, 'sz': sz_row}).sort_values(['pair', 'day'])
    # member marks indexed for the owner lookup: (sid, pair, day) -> (tid, mark, dir)
    Mi = M.assign(sid=M.sid.astype(str), pair=M.pair.astype(str)).set_index(['pair', 'day'])
    Mi = Mi.sort_index()
    qmap = q.to_dict()
    years_all = sorted(set(bsrc) | set(tsrc))
    daily = {}
    owners = []
    for pair, g in rows.groupby('pair', sort=False):
        g = g.sort_values('day')
        open_pos = None                     # dict(sid, tid, side, size, opened)
        for r in g.itertuples():
            d = r.day
            if open_pos is not None:
                # does the owner's trade still exist today?
                try:
                    mm = Mi.loc[(pair, d)]
                except KeyError:
                    mm = None
                hit = None
                if mm is not None:
                    mm = mm[(mm.sid == open_pos['sid']) & (mm.tid == open_pos['tid'])]
                    if len(mm):
                        hit = float(mm.mark.iloc[0])
                if hit is None:
                    open_pos = None          # owner exited (its last mark was yesterday)
                else:
                    daily[d] = daily.get(d, 0.0) + hit * open_pos['size']
                    continue
            if r.sz > 0 and open_pos is None:
                side = 1 if r.net > 0 else -1
                mm = Mi.loc[(pair, d)]
                mm = mm[mm['dir'] == side]
                if not len(mm):
                    continue
                best = max(mm.sid.values, key=lambda s: qmap.get(s, -1e9))
                mo = mm[mm.sid == best].iloc[0]
                open_pos = dict(sid=best, tid=int(mo.tid), side=side, size=float(r.sz), opened=d)
                owners.append((pair, d, best))
                daily[d] = daily.get(d, 0.0) + float(mo.mark) * open_pos['size']
    s = pd.Series(daily).sort_index()
    s = s.reindex(pd.DatetimeIndex(B.udays)).fillna(0.0)
    den = float(np.abs(s[s.index.year.isin(bsrc)]).mean() or 1.0)   # unit scale, as the book's gross mean
    d0 = s.values / den
    ybuild = s.index.year.isin(bsrc); ytrade = s.index.year.isin(tsrc)
    sc, bD, badj, bwd, bbind = W.scale_of(d0[ybuild], dipb, dayb)
    x = d0[ytrade] * sc
    return x, s.index[ytrade], dict(positions=len(owners), scale=sc, binds=bbind, build_dip95_pct=bD * sc, build_max_dd_pct=badj * sc)


def stage_bestmember(tag):
    T, M, TY = load(tag)
    rows = []
    for yard in ['none'] + LM.YARDS:
        for bt, dipb, dayb in W.BUDGETS:
            if yard == 'none':
                r = W.walk(T, TY, M, IDENT, dipb, dayb, ['ALLPASS'], nocut=True)
                k = r['ALLPASS'][0]; k.update(owner='(a) netted, as now', budget=bt); rows.append(k)
            else:
                t0 = time.time(); xs, ds, diag = [], [], []
                for st in W.STEPS:
                    b0, b1 = st['build']; t0_, t1_ = st['trade']
                    x, d, dg = ledger_step(M, T, TY, list(range(b0, b1 + 1)), list(range(t0_, t1_ + 1)), yard, dipb, dayb)
                    xs.append(x); ds.append(d); diag.append(dg)
                x = np.concatenate(xs); d = pd.DatetimeIndex(np.concatenate([q.values for q in ds]))
                k = LM.kpis(x, d) if hasattr(LM, 'kpis') else None
                W._MONTHS = d; k = W.kpis(x, d.year.values)
                k.update(owner='(b) best member by ' + yard, budget=bt, positions=sum(g['positions'] for g in diag),
                         build_dip95_step1=diag[0]['build_dip95_pct'], build_max_dd_step1=diag[0]['build_max_dd_pct'], scale_step1=diag[0]['scale'])
                rows.append(k)
            k['within_budget'] = bool(k['max_dd_pct'] <= dipb and k['dip95_pct'] <= dipb and k['worst_day_pct'] <= dayb)
            print('    %-38s %-6s median %6.3f%%  worst %6.3f%%  maxDD %5.2f%%  DIP95 %5.2f%%  PF %.2f  Sortino %.2f  in-budget %s' % (k['owner'], bt, k['median_year_pct'], k['worst_year_pct'], k['max_dd_pct'], k['dip95_pct'], k['profit_factor'], k['sortino'], k['within_budget']), flush=True)
    O = pd.DataFrame(rows); O.to_csv(W.OUT('exit_bestmember.csv'), index=False)


# ------------------------------------------------------------ (c) vol floor
def volfloor_mask_factory(q, atr_len=31):
    """Returns f(Book) -> row mask: a run of position days on a pair is dropped
    whole if its FIRST day's ATR percentile (trailing 252 bars, lagged one) is
    below q."""
    import l2sweep as S
    pct = {}
    for p in S.all_pairs():
        d = pd.read_csv(os.path.join(ROOTDATA, 'oanda_ohlc', '%s_mid.csv' % p), parse_dates=['date']).set_index('date')
        import l2lib as L
        atr = pd.Series(L.P.atr(d.high.values, d.low.values, d.close.values, atr_len), index=d.index)
        pct[p] = atr.rolling(252, min_periods=120).rank(pct=True).shift(1)
    def mask(B):
        nl = B.L @ np.ones(len(B.members), np.float32); ns = B.Sm @ np.ones(len(B.members), np.float32)
        on = np.abs(nl - ns) >= 0.5
        keep = np.ones(len(on), bool)
        df = pd.DataFrame({'pair': B.pair, 'day': B.day, 'on': on, 'i': np.arange(len(on))})
        for p, g in df.groupby('pair', sort=False):
            g = g.sort_values('day'); o = g.on.values; idx = g.i.values; days = g.day.values
            prev = False; drop = False
            for j in range(len(o)):
                if o[j] and not prev:                     # a new run opens here
                    pr = pct[p].get(pd.Timestamp(days[j]), np.nan)
                    drop = bool(np.isfinite(pr) and pr < q)
                if o[j] and drop:
                    keep[idx[j]] = False
                prev = o[j]
        return keep
    return mask


def stage_volfloor(tag):
    T, M, TY = load(tag)
    rows = []
    grid = [0.0, 0.02, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5]
    for q in grid:
        W.NET_ROW_MASK = None if q == 0 else ('callable', volfloor_mask_factory(q))
        for bt, dipb, dayb in W.BUDGETS:
            r = W.walk(T, TY, M, IDENT, dipb, dayb, ['ALLPASS'], nocut=True)
            k = r['ALLPASS'][0]; k.update(floor_q=q, budget=bt)
            k['within_budget'] = bool(k['max_dd_pct'] <= dipb and k['dip95_pct'] <= dipb and k['worst_day_pct'] <= dayb)
            rows.append(k)
            print('    floor q=%.2f %-6s median %6.3f%%  worst %6.3f%%  maxDD %5.2f%%  DIP95 %5.2f%%  PF %.2f  in-budget %s' % (q, bt, k['median_year_pct'], k['worst_year_pct'], k['max_dd_pct'], k['dip95_pct'], k['profit_factor'], k['within_budget']), flush=True)
    W.NET_ROW_MASK = None
    pd.DataFrame(rows).to_csv(W.OUT('exit_volfloor.csv'), index=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', required=True, choices=['bestmember', 'volfloor'])
    ap.add_argument('--suffix', default='_routed_tirexcl_actweak')
    a = ap.parse_args(); W.S.load_costs()
    t0 = time.time(); print('=== %s on %s ===' % (a.stage, a.suffix), flush=True)
    {'bestmember': stage_bestmember, 'volfloor': stage_volfloor}[a.stage](a.suffix)
    print('=== %s done in %.1f min ===' % (a.stage, (time.time() - t0) / 60), flush=True)


if __name__ == '__main__':
    main()
