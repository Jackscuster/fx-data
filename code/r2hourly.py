import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""A5 — THE HOURLY PATH. Does the daily bar decide stop-versus-target wrongly?

THE QUESTION. A daily bar whose high reaches the target AND whose low reaches
the stop is ambiguous: the engine has to assume an order, and whichever it
assumes is a guess. The hourly file can settle it. This stage finds every
AMBIGUOUS trade-day of the non-luck winners, replays it hour by hour on real
two-sided quotes, and reports how often the daily answer was wrong and what it
cost in R.

WHY ONLY THE AMBIGUOUS DAYS. On an unambiguous day -- only one level touched --
hourly data cannot disagree, so replaying it would burn I/O to confirm
arithmetic. The ambiguous days are the entire disagreement surface.

TWO-SIDED QUOTES, AND WHEN THEY START. Per pair, from
results/r2reads/hourly_coverage.csv: 11 pairs from 2002-05-06/07, NZDUSD from
2002-09-23, and 17 pairs only from 2004-05-31. The BINDING date for a 28-pair
strategy is therefore 2004-05-31, which is what the project overview said; a
file check on EURUSD alone says 2002-05-06 and is misleading.

EXITS USE THE SIDE THAT COSTS MONEY. A long exits at the BID, a short at the
ASK. The daily cost table is also reported beside it, as Jack asked, so the
two cost conventions can be compared on the same trades.

    python3 code/r2hourly.py --stage a5 --mode A
"""
import time, glob, json, hashlib
import numpy as np, pandas as pd

import l2sweep as S
import l2tune as T
import l2r2gate1 as G
import l2r2gate2 as G2
import l2r2book as BK
import l2r2winners as WN

OUT = os.path.join(ROOTOUT, 'r2reads')
H1 = os.path.join(ROOTDATA, 'oanda_h1')
os.makedirs(OUT, exist_ok=True)
_CACHE = {}


def hourly(pair, side):
    """Hourly OHLC for one pair and side, indexed by timestamp. Cached."""
    key = (pair, side)
    if key in _CACHE:
        return _CACHE[key]
    f = os.path.join(H1, '%s_%s.csv' % (pair, side))
    if not os.path.exists(f):
        _CACHE[key] = None
        return None
    d = pd.read_csv(f, parse_dates=['time'])
    d = d.set_index('time').sort_index()
    _CACHE[key] = d
    return d


def coverage():
    f = os.path.join(OUT, 'hourly_coverage.csv')
    return pd.read_csv(f) if os.path.exists(f) else None


def _levels(entry_px, dirv, atr_at_entry, risk):
    """The stop and target PRICES the engine used for one trade."""
    am = float(risk['atr_mult']); tp = float(risk['tp_mult'])
    stop = entry_px - dirv * am * atr_at_entry
    targ = entry_px + dirv * tp * am * atr_at_entry
    return stop, targ


def stage_a5(mode='A', tag='full', max_winners=None):
    """Replay the winners' AMBIGUOUS trade-days on hourly two-sided quotes."""
    import l2lib as L
    G.manifest_check()
    S.load_costs()
    T.ACCT_OBJECTIVE = True
    W = pd.read_csv(os.path.join(ROOTOUT, 'r2gate2', 'mode%s_winners.csv' % mode))
    if max_winners:
        W = W.head(max_winners)
    assert len(W), 'no winners for mode %s' % mode
    z = np.load(BK._bank_slice_file(mode, tag), allow_pickle=True)
    TG = z['tag']; CB = z['combo']
    Y = G2.Years(cap=4000)
    ST = G2.steps()
    cov = coverage()
    cov_start = ({r.pair: pd.Timestamp(r.two_sided_start, tz='UTC') for _i, r in cov.iterrows()}
                 if cov is not None else {})
    rows = []
    t0 = time.time()
    for wi, w in W.iterrows():
        k = int(w.bank_row)
        stream = list(G2.STREAMS).index(w.stream)
        sl, rt = stream // 2, stream % 2
        sname, plan, code = S.SLICES[sl]
        combo = tuple(CB[k])
        for si, stp in enumerate(ST):
            ci = int(TG[k, stream, si])
            if ci < 0:
                continue
            ip, risk = BK.winner_config(mode, combo, sname, ci)
            alen = int(risk['atr_len'])
            aidx = {p: np.zeros(len(Y.cl[p]), np.int64) for p in Y.sc.pairs}
            tl = WN._trade_lists(Y, mode, combo, ip, risk, sname, plan, aidx)
            for p, d in tl.items():
                o, h, l, c = Y.sc.arr[p]
                atr = Y.sc._atr.get((alen, p))
                if atr is None:
                    atr = L.P.atr(h, l, c, alen); Y.sc._atr[(alen, p)] = atr
                dates = pd.DatetimeIndex(Y.sc.dates[p])
                for j in range(len(d['eb'])):
                    eb = int(d['eb'][j]); xb = int(d['xb'][j])
                    if xb <= eb:
                        continue
                    yr = dates[eb].year
                    if yr != stp['trade'][0]:
                        continue                     # trade year only
                    dirv = float(np.sign(d['dirv'][j]))
                    epx = float(d['entry_px'][j]) if 'entry_px' in d else float(c[eb])
                    stop, targ = _levels(epx, dirv, float(atr[eb]), risk)
                    # ---- find the AMBIGUOUS days: both levels inside one daily bar
                    for b in range(eb, min(xb, len(c) - 1) + 1):
                        hi, lo = float(h[b]), float(l[b])
                        hit_t = (hi >= targ) if dirv > 0 else (lo <= targ)
                        hit_s = (lo <= stop) if dirv > 0 else (hi >= stop)
                        if not (hit_t and hit_s):
                            continue
                        day = dates[b]
                        side_exit = 'bid' if dirv > 0 else 'ask'
                        hh = hourly(p, side_exit)
                        if hh is None:
                            rows.append(dict(mode=mode, bank_row=k, stream=w.stream,
                                             step=stp['name'], pair=p, day=str(day.date()),
                                             direction=('long' if dirv > 0 else 'short'),
                                             verdict='NO HOURLY FILE'))
                            continue
                        cs = cov_start.get(p)
                        dt = pd.Timestamp(day.date(), tz='UTC')
                        if cs is not None and dt < cs:
                            rows.append(dict(mode=mode, bank_row=k, stream=w.stream,
                                             step=stp['name'], pair=p, day=str(day.date()),
                                             direction=('long' if dirv > 0 else 'short'),
                                             verdict='BEFORE TWO-SIDED COVERAGE'))
                            continue
                        seg = hh.loc[dt:dt + pd.Timedelta(hours=23, minutes=59)]
                        if not len(seg):
                            rows.append(dict(mode=mode, bank_row=k, stream=w.stream,
                                             step=stp['name'], pair=p, day=str(day.date()),
                                             direction=('long' if dirv > 0 else 'short'),
                                             verdict='NO HOURLY BARS THAT DAY'))
                            continue
                        first = None
                        for ts, hr in seg.iterrows():
                            th = (float(hr['h']) >= targ) if dirv > 0 else (float(hr['l']) <= targ)
                            sh = (float(hr['l']) <= stop) if dirv > 0 else (float(hr['h']) >= stop)
                            if th and sh:
                                first = 'both_in_one_hour'; break
                            if th:
                                first = 'target'; break
                            if sh:
                                first = 'stop'; break
                        rows.append(dict(mode=mode, bank_row=k, stream=w.stream,
                                         step=stp['name'], pair=p, day=str(day.date()),
                                         direction=('long' if dirv > 0 else 'short'),
                                         entry_px=epx, stop_px=stop, target_px=targ,
                                         hourly_first=(first or 'neither'),
                                         hours_available=len(seg),
                                         verdict='RESOLVED' if first in ('stop', 'target')
                                         else 'STILL AMBIGUOUS'))
        print('    a5: winner %d/%d done (%.1f min, %d ambiguous days so far)'
              % (wi + 1, len(W), (time.time() - t0) / 60, len(rows)), flush=True)
    D = pd.DataFrame(rows)
    f = os.path.join(OUT, 'mode%s_a5_hourly.csv' % mode)
    D.to_csv(f, index=False)
    print('  A5 [mode %s]: %s ambiguous trade-days found -> %s'
          % (mode, f'{len(D):,}', os.path.relpath(f, _R)), flush=True)
    if len(D) and 'hourly_first' in D.columns:
        print('    hourly verdict: %s'
              % D.hourly_first.value_counts().to_dict(), flush=True)
        print('    coverage: %s' % D.verdict.value_counts().to_dict(), flush=True)
    return f


# ==========================================================================
# A4 — CURRENCY NETTING
# ==========================================================================
# THE QUESTION. A 28-pair book looks diversified in pairs and may not be
# diversified in CURRENCIES: eight legs carry everything, and one leg can own
# most of the drawdown. The saved daily series is a single netted number per
# day and cannot answer this, so the book's accumulator is rebuilt and its
# per-(pair, day) net positions are projected onto the eight currency legs.
#
# THE PROJECTION. A long in AUDJPY is long AUD and short JPY. For each day,
# leg[ccy] = sum over pairs of net_position x (+1 if ccy is the base, -1 if the
# quote). That is the exposure a prop firm's risk desk would see, and it is the
# number the per-currency cap is then swept against.
def stage_a4(mode='A', tag='full', rule='winners', caps=None):
    """Per-currency legs of a book's daily positions, and the cap sweep."""
    import l2walkfwd as W_
    import l2r2gate3 as G3x
    G.manifest_check()
    S.load_costs()
    caps = caps if caps is not None else [None, 4.0, 3.0, 2.0, 1.5, 1.0, 0.75, 0.5]
    pm = G3x.passmask_file(mode, rule)
    assert os.path.exists(pm), pm + ' missing -- build the book first'
    PM = np.load(pm, allow_pickle=True)['pm']
    partdir = os.path.join(ROOTOUT, 'r2gate2', 'mode%s_gate3bookparts' % mode)
    rows, legrows = [], []
    for si, stp in enumerate(G2.steps()):
        build_years, trade_years = G3x.rule_windows(rule, stp)
        Yq = G2.Years(cap=2000)
        _ai, adays = BK.year_dayidx(Yq, build_years | trade_years)
        pairs = Yq.sc.pairs
        del Yq
        nsh = 16
        try:
            BA, folded = G3x._sum_pbook_parts(partdir, si, nsh, pairs, adays, rule)
        except Exception as e:
            print('    a4 step %s: no book parts (%s); skipping'
                  % (stp['name'], type(e).__name__), flush=True)
            continue
        for bi, bk, _rt in G3x.PASSBOOKS:
            nm = int(BA.n_members[bi])
            acc = BA.as_accumulator(bi)
            if nm == 0 or acc.nl.sum() + acc.ns.sum() == 0:
                continue
            SB = BK.StreamedBook(acc, nm)
            wb = np.ones(nm, np.float32)
            # net() takes the agreement CURVE as well as the weights, because the
            # book's position depends on how many members agree; fit it on the
            # BUILD years exactly as the books stage does, so these legs are the
            # legs of the book that was actually scored.
            curve, _c = W_.fit_curve(SB, wb, build_years)
            # Book.net returns (sgn, sz, mk, f): direction, size, mark, vote
            # fraction, one entry per (pair, day) live row. The signed position
            # is sgn x sz, which is what projects onto the currency legs.
            sgn_, sz_, _mk, _f = SB.net(wb, curve)
            net = np.asarray(sgn_, float) * np.asarray(sz_, float)
            # project onto the eight currency legs
            ccy = list(SB.ccy)
            nd = SB.nd
            legs = np.zeros((len(ccy), nd))
            for r in range(len(SB.pair)):
                dpos = SB.dpos[r]
                legs[SB.bc[r], dpos] += net[r]
                legs[SB.qc[r], dpos] -= net[r]
            yrs = pd.DatetimeIndex(SB.udays).year.values
            tr = np.isin(yrs, sorted(trade_years))
            tot_abs = np.abs(legs).sum(axis=0)
            big = np.abs(legs).max(axis=0)
            share = np.where(tot_abs > 0, big / tot_abs, np.nan)
            for ci, cc in enumerate(ccy):
                legrows.append(dict(mode=mode, rule=rule, step=stp['name'], book=bk,
                                    currency=cc, members=nm,
                                    mean_abs_exposure=float(np.nanmean(np.abs(legs[ci, tr]))),
                                    max_abs_exposure=float(np.nanmax(np.abs(legs[ci, tr]))),
                                    share_of_total_mean=float(np.nanmean(
                                        np.where(tot_abs[tr] > 0,
                                                 np.abs(legs[ci, tr]) / tot_abs[tr], np.nan)))))
            rows.append(dict(mode=mode, rule=rule, step=stp['name'], book=bk,
                             members=nm, n_currencies=len(ccy), trade_days=int(tr.sum()),
                             largest_leg_share_mean=float(np.nanmean(share[tr])),
                             largest_leg_share_max=float(np.nanmax(share[tr]))))
        del BA
    Lg = pd.DataFrame(legrows); Sm = pd.DataFrame(rows)
    f1 = os.path.join(OUT, 'mode%s_a4_currency_legs.csv' % mode)
    f2 = os.path.join(OUT, 'mode%s_a4_summary.csv' % mode)
    Lg.to_csv(f1, index=False); Sm.to_csv(f2, index=False)
    print('  A4 [mode %s, %s]: %d leg rows, %d book-steps -> %s'
          % (mode, rule, len(Lg), len(Sm), os.path.relpath(f1, _R)), flush=True)
    if len(Sm):
        print('    largest single currency leg carries, on average, %.1f%% of total '
              'absolute exposure (max %.1f%%)'
              % (100 * Sm.largest_leg_share_mean.mean(),
                 100 * Sm.largest_leg_share_max.max()), flush=True)
    if len(Lg):
        g = Lg.groupby('currency', as_index=False).mean_abs_exposure.mean()
        g = g.sort_values('mean_abs_exposure', ascending=False)
        print('    busiest legs: %s'
              % ', '.join('%s %.1f' % (r.currency, r.mean_abs_exposure)
                          for _i, r in g.head(4).iterrows()), flush=True)
    return f1, f2



# ---------------------------------------------------------------------------
# A5, THE PARTS THAT WERE SPECIFIED AND NOT DELIVERED (built 24 Nov).
#
# stage_a5 above identified the AMBIGUOUS days -- those whose daily bar covers
# both the stop and the target -- and asked the hourly path which level came
# first. That was one of five things specified. The rest are below:
#   the disagreement COUNT, against the daily engine's actual convention;
#   the change in R per strategy and per book;
#   the same trades under the daily cost table versus realised hourly spreads;
#   the daily loss stop on hourly marks, threshold swept, through A6.
#
# THE DAILY CONVENTION IS "STOP WINS" (l2engine.py:37): a bar whose range covers
# both levels fills the stop, because a daily bar cannot say which came first
# and assuming the good one is how you fool yourself. So an hourly verdict of
# 'stop' AGREES with the daily engine and only 'target' DISAGREES -- and every
# disagreement is therefore in the FAVOURABLE direction. The daily assumption
# costs R; it does not flatter the result. That asymmetry is the point of the
# test and is stated in the report.
# ---------------------------------------------------------------------------

def stage_a5_disagree(mode='A', tag='full'):
    """The disagreement count and the change in R, per strategy and per book."""
    import l2r2gate3 as G3x
    f = os.path.join(OUT, 'mode%s_a5_hourly.csv' % mode)
    assert os.path.exists(f), f + ' missing -- run --stage a5 first'
    D = pd.read_csv(f)
    assert len(D), 'no ambiguous days recorded for mode %s' % mode
    # the engine fills the STOP on an ambiguous bar, so only 'target' disagrees
    D['daily_assumed'] = 'stop'
    D['disagrees'] = (D.hourly_first == 'target').astype(int)
    # R on a resolved trade is -1 at the stop and +tp_mult at the target, both
    # in risk units before cost; the flip is therefore worth tp_mult + 1.
    z = np.load(BK._bank_slice_file(mode, tag), allow_pickle=True)
    TG, CB = z['tag'], z['combo']
    W = pd.read_csv(os.path.join(ROOTOUT, 'r2gate2', 'mode%s_winners.csv' % mode))
    ST = G2.steps()
    tpm = {}
    for _i, w in W.iterrows():
        k = int(w.bank_row)
        stream = list(G2.STREAMS).index(w.stream)
        sname, plan, code = S.SLICES[stream // 2]
        for si, stp in enumerate(ST):
            ci = int(TG[k, stream, si])
            if ci < 0:
                continue
            _ip, risk = BK.winner_config(mode, tuple(CB[k]), sname, ci)
            tpm[(k, stp['name'])] = float(risk['tp_mult'])
    D['tp_mult'] = [tpm.get((int(r.bank_row), r.step), np.nan)
                    for _i, r in D.iterrows()]
    D['delta_R'] = np.where(D.disagrees == 1, D.tp_mult + 1.0, 0.0)
    f2 = os.path.join(OUT, 'mode%s_a5_disagree.csv' % mode)
    D.to_csv(f2, index=False)
    # per strategy
    P = D.groupby('bank_row', as_index=False).agg(
        ambiguous_days=('disagrees', 'size'), disagreements=('disagrees', 'sum'),
        delta_R=('delta_R', 'sum'))
    P['share_disagree'] = P.disagreements / P.ambiguous_days
    P['mode'] = mode
    f3 = os.path.join(OUT, 'mode%s_a5_delta_strategy.csv' % mode)
    P.to_csv(f3, index=False)
    # per book: equal weight over the members that appear, which for the
    # winners' book is every winner, so the book delta is the mean member delta
    B = pd.DataFrame([dict(mode=mode, book='winners_allon', members=len(P),
                           ambiguous_days=int(P.ambiguous_days.sum()),
                           disagreements=int(P.disagreements.sum()),
                           delta_R_total=float(P.delta_R.sum()),
                           delta_R_per_member=float(P.delta_R.mean()))])
    f4 = os.path.join(OUT, 'mode%s_a5_delta_book.csv' % mode)
    B.to_csv(f4, index=False)
    print('  A5 disagreement [mode %s]: %d of %d ambiguous days disagree (%.0f%%), '
          'delta R %+.2f total, %+.2f per member'
          % (mode, int(P.disagreements.sum()), int(P.ambiguous_days.sum()),
             100.0 * P.disagreements.sum() / max(1, P.ambiguous_days.sum()),
             float(P.delta_R.sum()), float(P.delta_R.mean())), flush=True)
    return f2, f3, f4


def _era_bp():
    """The cost table's own by-era spreads, which it already carries.

    cost_table_h22.csv was calibrated on OANDA hourly bid/ask at 22:00 NY over
    2016-2020, and carries bp_2004_2015 and bp_2021_2026 beside it. That matters
    beyond A5: the eleven-step walk trades 2010-2015 while being charged
    2016-2020 costs, and 2004-2015 spreads are WIDER on nearly every pair. The
    early years are therefore charged too little, which FLATTERS them -- and
    B1-winners still loses money there.
    """
    t = pd.read_csv(os.environ.get('FX_COST_TABLE')
                    or os.path.join(ROOTOUT, 'cost_table_h22.csv'))
    cols = [c for c in ('bp_2004_2015', 'cost_bp_roundtrip', 'bp_2021_2026')
            if c in t.columns]
    return t[['pair'] + cols]


def stage_a5_spread(mode='A'):
    """Those trades under the DAILY COST TABLE versus REALISED HOURLY SPREADS."""
    f = os.path.join(OUT, 'mode%s_a5_disagree.csv' % mode)
    if not os.path.exists(f):
        f = os.path.join(OUT, 'mode%s_a5_hourly.csv' % mode)
    D = pd.read_csv(f)
    assert len(D), 'no A5 rows for mode %s' % mode
    S.load_costs()
    rows = []
    for _i, r in D.iterrows():
        p = r.pair
        bid, ask = hourly(p, 'bid'), hourly(p, 'ask')
        if bid is None or ask is None:
            continue
        day = pd.Timestamp(r.day)
        if day.tz is None:
            day = day.tz_localize('UTC')
        sl_b = bid.loc[(bid.index >= day) & (bid.index < day + pd.Timedelta(days=1))]
        sl_a = ask.loc[(ask.index >= day) & (ask.index < day + pd.Timedelta(days=1))]
        if not len(sl_b) or not len(sl_a):
            continue
        n = min(len(sl_b), len(sl_a))
        mid = (sl_b.close.values[:n] + sl_a.close.values[:n]) / 2.0
        spr = (sl_a.close.values[:n] - sl_b.close.values[:n])
        with np.errstate(divide='ignore', invalid='ignore'):
            bp = np.where(mid > 0, 1e4 * spr / mid, np.nan)
        # the cost table charges a ROUND TRIP, so the comparable realised
        # figure is twice the one-way spread. The table's own bp is
        # 1e4 x cost_frac_roundtrip.
        table_bp = 1e4 * float(S.COSTS.get(p, np.nan))
        rows.append(dict(mode=mode, pair=p, day=str(r.day),
                         hours=int(n),
                         realised_oneway_bp_mean=float(np.nanmean(bp)),
                         realised_roundtrip_bp_mean=float(2 * np.nanmean(bp)),
                         realised_roundtrip_bp_max=float(2 * np.nanmax(bp)),
                         table_roundtrip_bp=table_bp))
    Sp = pd.DataFrame(rows)
    f2 = os.path.join(OUT, 'mode%s_a5_spreads.csv' % mode)
    Sp.to_csv(f2, index=False)
    if len(Sp):
        g = Sp.groupby('pair', as_index=False).agg(
            days=('day', 'size'),
            realised_rt_bp=('realised_roundtrip_bp_mean', 'mean'),
            table_rt_bp=('table_roundtrip_bp', 'first'))
        g['realised_over_table'] = g.realised_rt_bp / g.table_rt_bp
        g['mode'] = mode
        f3 = os.path.join(OUT, 'mode%s_a5_spreads_by_pair.csv' % mode)
        g.to_csv(f3, index=False)
        print('  A5 spreads [mode %s]: %d trade-days, realised round trip '
              '%.2f bp against %.2f bp charged (%.2fx)'
              % (mode, len(Sp), float(Sp.realised_roundtrip_bp_mean.mean()),
                 float(Sp.table_roundtrip_bp.mean()),
                 float(Sp.realised_roundtrip_bp_mean.mean() /
                       max(1e-9, Sp.table_roundtrip_bp.mean()))), flush=True)
        return f2, f3
    print('  A5 spreads [mode %s]: no rows' % mode, flush=True)
    return f2, None


def _hourly_equity_day(trades, day):
    """Hourly mark-to-market of the open trades on one day, in R.

    WHAT THIS CAN AND CANNOT SEE. It marks each open trade on the hourly MID of
    its pair, so it sees an intraday excursion the daily close hides -- which is
    the whole reason the daily breach counts in A6 are a LOWER BOUND. It still
    cannot see inside the hour.
    """
    eq = None
    for t in trades:
        p, dirv, entry, risk_r = t['pair'], t['dir'], t['entry_px'], t['risk']
        b, a = hourly(p, 'bid'), hourly(p, 'ask')
        if b is None or a is None:
            continue
        sl_b = b.loc[(b.index >= day) & (b.index < day + pd.Timedelta(days=1))]
        sl_a = a.loc[(a.index >= day) & (a.index < day + pd.Timedelta(days=1))]
        if not len(sl_b) or not len(sl_a):
            continue
        n = min(len(sl_b), len(sl_a))
        mid = (sl_b.close.values[:n] + sl_a.close.values[:n]) / 2.0
        r = dirv * (mid - entry) / max(1e-12, risk_r)
        if eq is None:
            eq = np.zeros(n)
        m = min(len(eq), len(r))
        eq[:m] += r[:m]
    return eq


if __name__ == '__main__':
    st = G.opt('--stage', str, 'a5')
    md = G.opt('--mode', str, 'A')
    if st == 'a5':
        stage_a5(md, max_winners=G.opt('--winners', int, None))
    elif st == 'a5dis':
        for m in ([md] if md != 'both' else ['A', 'B']):
            stage_a5_disagree(m)
    elif st == 'a5spread':
        for m in ([md] if md != 'both' else ['A', 'B']):
            stage_a5_spread(m)
    elif st == 'a4':
        stage_a4(md, rule=G.opt('--rule', str, 'winners'))
    else:
        raise SystemExit('unknown stage %s' % st)
