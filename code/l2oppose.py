import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""ITEMS 12 AND 13 on the routed book.

  --stage opposition  same-pair opposition on a (pair, day): (i) majority-net
                      as now, (ii) sit out, (iii) both sides open as a hedge.
                      Episodes counted: rows in the trade years with votes on
                      both sides, and their share of traded rows.
  --stage legflip     a regime flip on an OPEN trend position. Leg 2 (past
                      TP1) is never touched. Leg 1 -- the leg still short of
                      TP1 -- when the pair's state leaves TRENDING: (i) run to
                      its own exit (as now) vs (ii) close at the flip, at that
                      day's close. Legs are identified from the trade table:
                      a two-leg position is two trade records with the same
                      (sid, pair, entry); leg 1 is the one that exits first.
                      One-leg trades are leg 1. The flip day is the first day
                      after entry whose state row (built from bars <= D-1) is
                      not TRENDING.
"""
import argparse, time
import numpy as np, pandas as pd
import l2walkfwd as W
import l2route as R

IDENT = {y: y for y in W.YEARS}


def load(tag):
    W.TAG = tag; os.environ['WF_TAG'] = tag
    W.TRADES_F = W.OUT('wf_trades.pkl'); W.MARKS_F = W.OUT('wf_marks.pkl')
    T = pd.read_pickle(W.TRADES_F); M = pd.read_pickle(W.MARKS_F)
    return T, M, W.trade_year_sums(M)


def kp(k, dipb, dayb):
    k['within_budget'] = bool(k['max_dd_pct'] <= dipb and k['dip95_pct'] <= dipb and k['worst_day_pct'] <= dayb); return k


def stage_opposition(tag):
    T, M, TY = load(tag)
    # episodes: rows with both sides voting, trade years
    allp = sorted(set(T.sid.astype(str))); B = W.Book(M[M.sid.isin(allp)], allp)
    w = np.ones(len(B.members), np.float32); nl = B.L @ w; ns = B.Sm @ w
    tr = np.isin(B.dyears, list(range(2016, 2021)))[B.dpos]
    both = (nl > 0) & (ns > 0)
    print('  trade-year rows %d; with votes on both sides %d (%.1f%%); majority share on those rows: median %.2f'
          % (tr.sum(), (both & tr).sum(), 100 * (both & tr).sum() / tr.sum(), np.median((np.maximum(nl, ns) / (nl + ns))[both & tr])), flush=True)
    rows = []
    for mode in ('net', 'sitout', 'hedge'):
        W.OPPOSITION = mode
        for bt, dipb, dayb in W.BUDGETS:
            r = W.walk(T, TY, M, IDENT, dipb, dayb, ['ALLPASS'], nocut=True)
            k = kp(r['ALLPASS'][0], dipb, dayb); k.update(rule=mode, budget=bt, opposed_rows=int((both & tr).sum()), opposed_share_pct=100 * (both & tr).sum() / tr.sum()); rows.append(k)
            print('    %-7s %-6s median %6.3f%%  worst %6.3f%%  maxDD %5.2f%%  DIP95 %5.2f%%  PF %.2f  Sortino %.2f  in-budget %s' % (mode, bt, k['median_year_pct'], k['worst_year_pct'], k['max_dd_pct'], k['dip95_pct'], k['profit_factor'], k['sortino'], k['within_budget']), flush=True)
    W.OPPOSITION = 'net'
    pd.DataFrame(rows).to_csv(W.OUT('opposition.csv'), index=False)


def stage_legflip(tag, states):
    T, M, TY = load(tag)
    shape, act = R.load_states(states)
    Ts = T.assign(sid=T.sid.astype(str), pair=T.pair.astype(str))
    Ts['slice'] = Ts.sid.map(W.field_label)
    trend = Ts[Ts.slice.str.contains('trend')].copy()
    # legs: within (sid, pair, entry), leg 1 = earliest exit
    trend['leg'] = trend.groupby(['sid', 'pair', 'entry']).exit.rank(method='first').astype(int)
    leg1 = trend[trend.leg == 1]
    print('  trend-slice trade records %d; positions %d; leg-1 records %d; two-leg positions %d'
          % (len(trend), trend.groupby(['sid', 'pair', 'entry']).ngroups, len(leg1), int((trend.leg == 2).sum())), flush=True)
    # flip day per (pair, entry): first day > entry with state != trending
    st = shape.copy()
    not_tr = (st != 'trending') & st.notna()
    flips = {}
    for p in st.columns:
        idx = st.index; nt = not_tr[p].values
        # for each entry date, the first later date with nt True: precompute via next-true index
        nxt = np.full(len(idx), -1); last = -1
        for i in range(len(idx) - 1, -1, -1):
            if nt[i]: last = i
            nxt[i] = last
        flips[p] = (idx, nxt)
    def flip_day(p, entry):
        idx, nxt = flips[p]; i = idx.searchsorted(entry, side='right')   # first index strictly after entry
        if i >= len(idx) or nxt[i] < 0: return pd.NaT
        return idx[nxt[i]]
    leg1 = leg1.assign(flip=[flip_day(p, e) for p, e in zip(leg1.pair, leg1.entry)])
    closable = leg1[(leg1.flip.notna()) & (leg1.flip < leg1.exit)]
    print('  leg-1 trades still open at a flip: %d of %d (%.1f%%)' % (len(closable), len(leg1), 100 * len(closable) / max(len(leg1), 1)), flush=True)
    # (ii) close at the flip: drop marks after the flip day for those trades
    key = pd.MultiIndex.from_frame(closable[['sid', 'tid']])
    Mk = M.assign(sid=M.sid.astype(str))
    mkey = pd.MultiIndex.from_frame(Mk[['sid', 'tid']])
    is_c = mkey.isin(key)
    fl = pd.Series(closable.flip.values, index=key)
    cut = np.zeros(len(Mk), bool)
    cut[is_c] = Mk.day.values[is_c] > fl.reindex(mkey[is_c]).values
    M2 = M[~cut].reset_index(drop=True)
    T2 = T.copy()
    rsum = Mk[~cut].groupby(['sid', 'tid'], observed=True).mark.sum()
    tkey = pd.MultiIndex.from_frame(T2[['sid', 'tid']].astype({'sid': str}))
    T2['R'] = rsum.reindex(tkey).values.astype(float)
    print('  marks dropped after the flip: %d of %d' % (int(cut.sum()), len(Mk)), flush=True)
    rows = []
    for rule, (Tx, Mx) in (('(i) run to own exit', (T, M)), ('(ii) close leg 1 at the flip', (T2, M2))):
        TYx = W.trade_year_sums(Mx)
        for bt, dipb, dayb in W.BUDGETS:
            r = W.walk(Tx, TYx, Mx, IDENT, dipb, dayb, ['ALLPASS'], nocut=True)
            k = kp(r['ALLPASS'][0], dipb, dayb); k.update(rule=rule, budget=bt, leg1_closed_at_flip=len(closable) if rule.startswith('(ii)') else 0); rows.append(k)
            print('    %-30s %-6s median %6.3f%%  worst %6.3f%%  maxDD %5.2f%%  DIP95 %5.2f%%  PF %.2f  in-budget %s' % (rule, bt, k['median_year_pct'], k['worst_year_pct'], k['max_dd_pct'], k['dip95_pct'], k['profit_factor'], k['within_budget']), flush=True)
    pd.DataFrame(rows).to_csv(W.OUT('legflip.csv'), index=False)
    if len(closable):
        pd.to_pickle(T2, W.OUT('wf_trades_legflip.pkl')); pd.to_pickle(M2, W.OUT('wf_marks_legflip.pkl'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', required=True, choices=['opposition', 'legflip'])
    ap.add_argument('--suffix', default='_routed_tirexcl_actweak')
    ap.add_argument('--states', default=os.path.join(ROOTOUT, 'layer1_states.csv'))
    a = ap.parse_args(); W.S.load_costs()
    t0 = time.time(); print('=== %s on %s ===' % (a.stage, a.suffix), flush=True)
    if a.stage == 'opposition': stage_opposition(a.suffix)
    else: stage_legflip(a.suffix, a.states)
    print('=== %s done in %.1f min ===' % (a.stage, (time.time() - t0) / 60), flush=True)


if __name__ == '__main__':
    main()
