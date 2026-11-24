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



if __name__ == '__main__':
    st = G.opt('--stage', str, 'a5')
    md = G.opt('--mode', str, 'A')
    if st == 'a5':
        stage_a5(md, max_winners=G.opt('--winners', int, None))
    elif st == 'a4':
        stage_a4(md, rule=G.opt('--rule', str, 'winners'))
    else:
        raise SystemExit('unknown stage %s' % st)
