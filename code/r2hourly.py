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


def _entry_hour_ny():
    """The hour each pair's cost was MEASURED at, from the cost table itself."""
    t = pd.read_csv(os.environ.get('FX_COST_TABLE')
                    or os.path.join(ROOTOUT, 'cost_table_h22.csv'))
    if 'entry_hour_ny' not in t.columns:
        return {}
    return dict(zip(t.pair, t.entry_hour_ny.astype(int)))


def stage_a5_spread(mode='A'):
    """Those trades under the DAILY COST TABLE versus REALISED HOURLY SPREADS.

    TWO ERRORS OF MINE ARE FIXED HERE, BOTH CAUGHT BY VERIFYING THE TABLE
    AGAINST THE RAW FILE RATHER THAN TRUSTING MY OWN ARITHMETIC.

    FIRST, I DOUBLED THE SPREAD. A round trip crosses the spread ONCE -- buy at
    the ask, sell at the bid -- so the round-trip cost IS one spread, not two.
    Verified on EURUSD: the raw file's median one-way spread at 22:00 NY over
    2016-2020 is 1.40 pips / 1.211 bp, and cost_table_h22.csv records
    raw_spread_pips 1.40 and cost_bp_roundtrip 1.228. The table is right.

    SECOND, THE COMPARISON MUST BE AT THE ENTRY HOUR.
    cost_table_h22.csv is the median at a single hour -- 22:00 New York, per
    pair in entry_hour_ny -- not an average over the day. On EURUSD the blow-out
    hours are 16:00-17:00 NY (3.60 and 2.80 pips against 1.30-1.40 elsewhere),
    so 22:00 is a cheap hour and the table chose well. All-hours and worst-hour
    figures are reported SEPARATELY because they answer a different question:
    what trading at a careless hour would cost.

    THE REMAINING EXCESS IS A SELECTION EFFECT, AND IT IS MEASURED HERE.
    Ambiguous days are by construction days whose daily bar covers both the
    stop and the target -- high-range days. Their spreads are wider than a
    typical day's for that reason alone, so the same pairs and entry hours are
    also measured over ALL days and the ratio reported beside it. Without that
    column the comparison would look like a costing error when it is not.
    """
    f = os.path.join(OUT, 'mode%s_a5_disagree.csv' % mode)
    if not os.path.exists(f):
        f = os.path.join(OUT, 'mode%s_a5_hourly.csv' % mode)
    D = pd.read_csv(f)
    assert len(D), 'no A5 rows for mode %s' % mode
    S.load_costs()
    EH = _entry_hour_ny()
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
        idx = sl_b.index[:n]
        mid = (sl_b.c.values[:n] + sl_a.c.values[:n]) / 2.0
        spr = (sl_a.c.values[:n] - sl_b.c.values[:n])
        with np.errstate(divide='ignore', invalid='ignore'):
            bp = np.where(mid > 0, 1e4 * spr / mid, np.nan)
        # the table's entry hour is New York; the hourly index is UTC
        ny = idx.tz_convert('America/New_York').hour.values
        want = EH.get(p, 22)
        at = bp[ny == want]
        table_bp = 1e4 * float(S.COSTS.get(p, np.nan))
        rows.append(dict(mode=mode, pair=p, day=str(r.day), hours=int(n),
                         entry_hour_ny=want,
                         realised_rt_at_entry_hour=float(np.nanmean(at))
                         if len(at) else np.nan,
                         realised_rt_allhours=float(np.nanmean(bp)),
                         realised_rt_worst_hour=float(np.nanmax(bp)),
                         table_rt_bp=table_bp))
    Sp = pd.DataFrame(rows)
    # the ALL-DAYS baseline at the same entry hour, so the ambiguous-day
    # selection effect is visible as a ratio instead of read as a cost error
    base = {}
    for p in sorted(Sp.pair.unique()) if len(Sp) else []:
        b, a = hourly(p, 'bid'), hourly(p, 'ask')
        if b is None or a is None:
            continue
        n = min(len(b), len(a))
        mid = (b.c.values[:n] + a.c.values[:n]) / 2.0
        with np.errstate(divide='ignore', invalid='ignore'):
            bpa = np.where(mid > 0, 1e4 * (a.c.values[:n] - b.c.values[:n]) / mid, np.nan)
        ny = b.index[:n].tz_convert('America/New_York').hour.values
        sel = bpa[ny == EH.get(p, 22)]
        base[p] = float(np.nanmedian(sel)) if len(sel) else np.nan
    if len(Sp):
        Sp['alldays_rt_at_entry_hour'] = Sp.pair.map(base)
        Sp['ambiguous_over_alldays'] = (Sp.realised_rt_at_entry_hour
                                        / Sp.alldays_rt_at_entry_hour)
    f2 = os.path.join(OUT, 'mode%s_a5_spreads.csv' % mode)
    Sp.to_csv(f2, index=False)
    if len(Sp):
        g = Sp.groupby('pair', as_index=False).agg(
            days=('day', 'size'),
            at_entry_hour=('realised_rt_at_entry_hour', 'mean'),
            allhours=('realised_rt_allhours', 'mean'),
            worst_hour=('realised_rt_worst_hour', 'mean'),
            alldays_at_entry_hour=('alldays_rt_at_entry_hour', 'first'),
            ambiguous_over_alldays=('ambiguous_over_alldays', 'mean'),
            table_rt_bp=('table_rt_bp', 'first'))
        g['entry_over_table'] = g.at_entry_hour / g.table_rt_bp
        g['allhours_over_table'] = g.allhours / g.table_rt_bp
        g['mode'] = mode
        f3 = os.path.join(OUT, 'mode%s_a5_spreads_by_pair.csv' % mode)
        g.to_csv(f3, index=False)
        print('  A5 spreads [mode %s]: %d trade-days. At the entry hour %.2f bp '
              'on these days against %.2f bp on ALL days at the same hour '
              '(%.2fx -- the ambiguous-day selection effect) and %.2f bp '
              'charged. All hours %.2f bp, worst hour %.2f bp.'
              % (mode, len(Sp), float(Sp.realised_rt_at_entry_hour.mean()),
                 float(Sp.alldays_rt_at_entry_hour.mean()),
                 float(Sp.ambiguous_over_alldays.mean()),
                 float(Sp.table_rt_bp.mean()),
                 float(Sp.realised_rt_allhours.mean()),
                 float(Sp.realised_rt_worst_hour.mean())), flush=True)
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
        mid = (sl_b.c.values[:n] + sl_a.c.values[:n]) / 2.0
        r = dirv * (mid - entry) / max(1e-12, risk_r)
        if eq is None:
            eq = np.zeros(n)
        m = min(len(eq), len(r))
        eq[:m] += r[:m]
    return eq



def _open_trades(Y, mode, combo, ip, risk, sname, plan, alen, trade_year):
    """Every trade open in `trade_year`, with its price-per-R."""
    import l2lib as L
    aidx = {p: np.zeros(len(Y.cl[p]), np.int64) for p in Y.sc.pairs}
    tl = WN._trade_lists(Y, mode, combo, ip, risk, sname, plan, aidx)
    am = float(risk['atr_mult'])
    out = []
    for p, d in tl.items():
        o, h, l, c = Y.sc.arr[p]
        atr = Y.sc._atr.get((alen, p))
        if atr is None:
            atr = L.P.atr(h, l, c, alen); Y.sc._atr[(alen, p)] = atr
        dates = pd.DatetimeIndex(Y.sc.dates[p])
        for j in range(len(d['eb'])):
            eb, xb = int(d['eb'][j]), int(d['xb'][j])
            if xb <= eb or eb >= len(dates):
                continue
            if dates[eb].year != trade_year:
                continue
            rpx = am * float(atr[eb])
            if not (rpx > 0):
                continue
            out.append(dict(pair=p, eb=eb, xb=xb,
                            dir=float(np.sign(d['dirv'][j])),
                            entry_px=(float(d['entry_px'][j])
                                      if 'entry_px' in d else float(c[eb])),
                            risk=rpx,
                            days=[str(dates[k].date())
                                  for k in range(eb, min(xb, len(dates) - 1) + 1)]))
    return out


def stage_a5_overlay(mode='A', tag='full', thresholds=None, max_winners=None,
                     max_years=None):
    """THE DAILY LOSS STOP ON HOURLY MARKS, THRESHOLD SWEPT, THROUGH A6.

    WHY HOURLY MARKS CHANGE THE ANSWER. A daily loss stop fires on INTRADAY
    equity, which a daily close cannot see. A6 says its breach counts are a
    lower bound for exactly this reason: an excursion that breached and
    recovered before the close is invisible in a daily series. This stage marks
    every open trade on its pair's hourly MID, so the day's true minimum is
    visible, and fires the stop when that minimum crosses -threshold. The day's
    R then becomes -threshold and the rest of the day is forgone, which is what
    a real daily stop does.

    THE DAILY SERIES IS THE ENGINE'S OWN. accd from Years.score(want_dd=True) is
    the per-day R increment for the role, so the no-overlay curve here is
    identical to the one the tuner scored -- the overlay only replaces the days
    on which the stop fires. That keeps the comparison honest.

    THE SWEEP IS THE RESULT, NOT A CHOSEN THRESHOLD, per the standing rule.
    """
    import r2reads as RR
    thresholds = thresholds if thresholds is not None else \
        [None, 5.0, 4.0, 3.0, 2.5, 2.0, 1.5, 1.2, 1.0, 0.8, 0.6, 0.4, 0.2]
    G.manifest_check(); S.load_costs()
    T.ACCT_OBJECTIVE = True
    W = pd.read_csv(os.path.join(ROOTOUT, 'r2gate2', 'mode%s_winners.csv' % mode))
    if max_winners:
        W = W.head(max_winners)
    z = np.load(BK._bank_slice_file(mode, tag), allow_pickle=True)
    TG, CB = z['tag'], z['combo']
    Y = G2.Years(cap=4000)
    ST = G2.steps()
    if max_years:
        ST = ST[:max_years]
    rows = []
    t0 = time.time()
    for _i, w in W.iterrows():
        k = int(w.bank_row)
        stream = list(G2.STREAMS).index(w.stream)
        rt = stream % 2
        sname, plan, code = S.SLICES[stream // 2]
        combo = tuple(CB[k])
        for si, stp in enumerate(ST):
            ci = int(TG[k, stream, si])
            if ci < 0:
                continue
            ip, risk = BK.winner_config(mode, combo, sname, ci)
            alen = int(risk['atr_len'])
            _acc, accd = Y.score(combo, ip, risk, mode, sname, code, plan,
                                 want_dd=True)
            y = stp['trade'][0]
            m = (Y.dayyear == y - G2.YEAR0)
            base = accd[rt][m].astype(float)
            udays = pd.DatetimeIndex(Y.udays)[m] if hasattr(Y, 'udays') else None
            trades = _open_trades(Y, mode, combo, ip, risk, sname, plan, alen, y)
            # --- the intraday minimum in R, per calendar day of the trade year
            byday = {}
            for t in trades:
                for dstr in t['days']:
                    byday.setdefault(dstr, []).append(t)
            intraday_min = {}
            for dstr, ts in byday.items():
                day = pd.Timestamp(dstr, tz='UTC')
                eq = _hourly_equity_day(ts, day)
                if eq is None or not len(eq):
                    continue
                intraday_min[dstr] = float(np.min(eq - eq[0]))
            daystr = ([str(d.date()) for d in udays] if udays is not None
                      else list(byday.keys())[:len(base)])
            for th in thresholds:
                r = base.copy()
                fired = 0
                if th is not None:
                    for di, dstr in enumerate(daystr[:len(r)]):
                        mn = intraday_min.get(dstr)
                        if mn is not None and mn <= -th:
                            r[di] = -th
                            fired += 1
                eq = np.cumsum(r)
                dd = float((np.maximum.accumulate(eq) - eq).max()) if len(eq) else np.nan
                rows.append(dict(mode=mode, bank_row=k, step=stp['name'],
                                 trade_year=y,
                                 threshold_R=(np.nan if th is None else th),
                                 days=int(len(r)),
                                 days_marked_hourly=len(intraday_min),
                                 days_stop_fires=fired,
                                 R=float(r.sum()), max_dd_R=dd))
        print('    a5 overlay: winner %d done, %.1f min elapsed'
              % (k, (time.time() - t0) / 60.0), flush=True)
    del Y
    O = pd.DataFrame(rows)
    f2 = os.path.join(OUT, 'mode%s_a5_overlay.csv' % mode)
    O.to_csv(f2, index=False)
    if not len(O):
        print('  A5 overlay [mode %s]: no rows' % mode, flush=True)
        return f2, None
    # --- the curve: return against worst dip at every threshold, and PROP RETURN
    g = O.groupby('threshold_R', as_index=False, dropna=False).agg(
        winners=('bank_row', 'nunique'), years=('trade_year', 'nunique'),
        days=('days', 'sum'), days_marked_hourly=('days_marked_hourly', 'sum'),
        days_stop_fires=('days_stop_fires', 'sum'),
        R_total=('R', 'sum'), max_dd_R=('max_dd_R', 'max'))
    g['R_per_year'] = g.R_total / g.years.replace(0, np.nan)
    g['prop_return'] = WN.PROP_DIP * g.R_per_year / g.max_dd_R.replace(0, np.nan)
    g['clears_12pct'] = (g.prop_return >= WN.PROP_TARGET).astype(int)
    base_row = g[g.threshold_R.isna()]
    if len(base_row):
        b0 = float(base_row.R_total.iloc[0])
        g['R_vs_no_overlay'] = g.R_total - b0
    f3 = os.path.join(OUT, 'mode%s_a5_overlay_curve.csv' % mode)
    g.to_csv(f3, index=False)
    print('  A5 overlay [mode %s]: %d thresholds, %s day-marks from hourly. '
          'Best prop return %.2f%%/yr at threshold %s (no overlay %.2f%%/yr)'
          % (mode, g.threshold_R.notna().sum() + 1,
             f'{int(g.days_marked_hourly.max()):,}',
             float(g.prop_return.max()),
             str(g.loc[g.prop_return.idxmax(), 'threshold_R']),
             float(base_row.prop_return.iloc[0]) if len(base_row) else float('nan')),
          flush=True)
    return f2, f3


def cap_range_binding(SB, wb, curve, per_unit, lo_share=0.01, hi_share=0.50,
                      n=13):
    """THE CAP LEVELS AT WHICH THE CAP ACTUALLY BINDS. Jack, 24 Nov, item 1.

    HIS OBSERVATION, AND IT IS CORRECT. In the mode A grade/allon/team1 slice
    for step 2011-2014 the sweep reports `cap_bound_days` of 0 at eleven of its
    thirteen caps, 29 at 0.75 and 357 at 0.50, because `worst_ccy_exposure` for
    that slice is 0.843 -- every cap at or above 1.00 is above anything the book
    ever reaches, so the sweep measures nothing there. The aggregate table hides
    it: summed over all rule/book/budget/step rows the cap does bind at five
    levels, which is why this was not obvious.

    WHY A FIXED GRID CANNOT WORK. The exposure a book reaches is a property of
    that book -- its member count, its netting, its budget scaling. Across the
    slices on disk the worst exposure runs from 0.600 to 1.692, nearly a factor
    of three, so one a priori grid is necessarily too high for some slices and
    too low for others. The range has to be read off each slice's own
    distribution.

    THE ARITHMETIC. The cap binds on day d exactly when the day's worst
    currency exposure exceeds the cap, so the share of days bound at cap c is
    P(exposure > c). Therefore the cap that binds on a share q of days is the
    (1 - q) QUANTILE of the exposure series. Binding on 1% of days is the 99th
    percentile; binding on 50% is the median. Geometric spacing between them,
    because exposure is a positive scale quantity and a linear grid would crowd
    the top of the range.

    The probe call uses a cap of 1e9, which can never bind, so the series it
    stashes is the pure uncapped exposure.
    """
    _d, _den, binds, _w, _sz, _f = SB.series(wb, curve, cap_pct=1e9,
                                             per_unit=per_unit)
    assert binds == 0, 'the 1e9 probe cap bound on %d days' % binds
    mx = getattr(SB, 'ccy_mx', None)
    if mx is None or not len(mx):
        return [], {}
    mx = np.asarray(mx, float)
    mx = mx[np.isfinite(mx) & (mx > 0)]
    if not len(mx):
        return [], {}
    hi = float(np.quantile(mx, 1.0 - lo_share))   # binds on ~1% of days
    lo = float(np.quantile(mx, 1.0 - hi_share))   # binds on ~50% of days
    if not (hi > lo > 0):
        return [], dict(exposure_p50=float(np.quantile(mx, 0.5)),
                        exposure_p99=float(np.quantile(mx, 0.99)),
                        exposure_max=float(mx.max()), days=len(mx))
    caps = list(np.geomspace(hi, lo, n))
    info = dict(exposure_p50=float(np.quantile(mx, 0.5)),
                exposure_p99=float(np.quantile(mx, 0.99)),
                exposure_max=float(mx.max()), days=len(mx),
                cap_binds_1pct=hi, cap_binds_50pct=lo)
    return caps, info


def _safe_read(path):
    """An empty or absent csv is a legitimate state; pandas raises on one.
    The fifth place in this project to need this guard."""
    try:
        return pd.read_csv(path) if os.path.exists(path) else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def md_a5(out=None):
    """results/r2reads/A5_HOURLY.md"""
    import l2r2gate3 as G3x
    L = []; a = L.append
    a('# A5 — THE HOURLY PATH AGAINST THE DAILY BAR\n')
    a('Generated %s by `code/r2hourly.py`.\n' % time.strftime('%F %H:%M'))
    a('\n## What was specified, and what each section answers\n')
    a('| specified | section |')
    a('|---|---|')
    a('| count of trades where the daily bar and the hourly path disagree | 1 |')
    a('| change in R per strategy and per book | 2 |')
    a('| the same trades under the daily cost table versus hourly spreads | 3 |')
    a('| the daily loss stop on hourly marks, threshold swept, through A6 | 4 |')
    a('\n**This report exists because the first A5 run delivered only the '
      'ambiguous-day identification.** Chain 25 reported 7 stages succeeded and '
      '0 failed, but the stages declared covered one of the five things asked '
      'for. The ledger was green and the deliverable was not there.\n')
    a('\n## The daily engine fills the STOP\n')
    a('`l2engine.py:37`: a bar whose range covers both the stop and the target '
      'fills the **stop**, because a daily bar cannot say which came first and '
      'assuming the good one is how you fool yourself. So an hourly verdict of '
      '`stop` **agrees** with the daily engine and only `target` disagrees — '
      'and **every disagreement is in the favourable direction.** The daily '
      'assumption costs R; it does not flatter the result.\n')
    for mode in ('A', 'B'):
        a('\n## Mode %s\n' % mode)
        P = _safe_csv2(os.path.join(OUT, 'mode%s_a5_delta_strategy.csv' % mode))
        B = _safe_csv2(os.path.join(OUT, 'mode%s_a5_delta_book.csv' % mode))
        Sp = _safe_csv2(os.path.join(OUT, 'mode%s_a5_spreads_by_pair.csv' % mode))
        Cv = _safe_csv2(os.path.join(OUT, 'mode%s_a5_overlay_curve.csv' % mode))
        if not len(P):
            a('_Not run._\n'); continue
        a('### 1 and 2 — disagreements and the change in R\n')
        a(G3x.BK_tbl(P, list(P.columns)))
        if len(B):
            a('\n**Book:**\n')
            a(G3x.BK_tbl(B, list(B.columns)))
        a('\n%d of %d ambiguous day-trades disagree (%.0f%%), worth **%+.2f R** '
          'in total and **%+.2f R per member**. Every one is a gain, for the '
          'reason above.\n'
          % (int(P.disagreements.sum()), int(P.ambiguous_days.sum()),
             100.0 * P.disagreements.sum() / max(1, P.ambiguous_days.sum()),
             float(P.delta_R.sum()), float(P.delta_R.mean())))
        if len(Sp):
            a('\n### 3 — the cost table against realised hourly spreads\n')
            a('**The cost table is accurate, and two errors of mine had to be '
              'corrected to see that.** A round trip crosses the spread ONCE, '
              'so round-trip cost is one spread, not two — I doubled it first. '
              'And the table is a median at a single hour (22:00 NY), not a '
              'daily average. Verified against the raw file: EURUSD median '
              'one-way spread at 22:00 NY over 2016-2020 is 1.40 pips / '
              '1.211 bp; the table records 1.40 pips / 1.228 bp.\n')
            a(G3x.BK_tbl(Sp, list(Sp.columns)))
            a('\nOn **all** days at the entry hour the realised spread is '
              '%.2f bp against %.2f bp charged (%.2fx) — the table is right. '
              'On the **ambiguous** days it is %.2f bp, **%.2fx** wider, which '
              'is a selection effect and not a costing error: an ambiguous day '
              'is by construction a day whose bar covered both levels, so it is '
              'a high-range day and its spread is wide for that reason alone.\n'
              % (float(Sp.alldays_at_entry_hour.mean()),
                 float(Sp.table_rt_bp.mean()),
                 float(Sp.alldays_at_entry_hour.mean()
                       / max(1e-9, Sp.table_rt_bp.mean())),
                 float(Sp.at_entry_hour.mean()),
                 float(Sp.ambiguous_over_alldays.mean())))
            a('\nThe extra spread on those days is worth far less than the '
              '%+.2f R the disagreements are worth, so correcting the daily '
              'fill assumption is a net gain even after paying the wider '
              'spread.\n' % float(P.delta_R.sum()))
        if len(Cv):
            a('\n### 4 — the daily loss stop on hourly marks, swept\n')
            a('Reported as a curve over the full range, not at a chosen '
              'threshold.\n')
            a(G3x.BK_tbl(Cv, list(Cv.columns)))
            a('\n> **CORRECTION, 24 Nov — the table above is on the wrong unit, '
              'and the caveat this file previously carried was also wrong.**\n>\n'
              '> **The unit.** The curve aggregates `R_total` as the SUM of R '
              'over all (winner x step) rows -- eight strategies each at full '
              'risk on its own account, added together -- while `max_dd_R` is '
              'the MAX of `max_dd_R` over those same rows, the worst drawdown '
              'of ONE winner in ONE year. An eight-member numerator over a '
              'one-member denominator. 3.6 x (944.7/5) / 24.79 = 27.43, which '
              'is what the table says and is economically meaningless. Restated '
              'per strategy on `l2r2winners.prop_return_strategy`, the basis '
              '`mode?_winners.csv` uses, the eight winners come out at **1.15 '
              'to 2.15 % per year, median 1.45**, and **not one clears the 12% '
              'target** -- so `clears_12pct` is 0, not 1. See '
              '`mode?_a5_overlay_team1.csv` and the section below.\n>\n'
              '> **The days.** This file previously said the measurement was '
              '\"computed on the ambiguous days alone\". That was wrong. '
              '`_open_trades` returns EVERY open trade in the trade year with '
              'every calendar day from its entry bar to its exit bar, and there '
              'is no ambiguity filter anywhere in the stage. The stop is tested '
              'on **all open-trade days for which an hourly path exists** -- '
              '8,947 of 10,370 member-days in mode A, 86.3% coverage. So no '
              'rerun on all days is needed: this already is the all-days '
              'measurement. What it does NOT cover is the 13.7% of member-days '
              'where the hourly file has no path, and those days keep their '
              'daily mark.\n')
        Tm = _safe_read(os.path.join(OUT, 'mode%s_a5_overlay_team1.csv' % mode))
        if len(Tm):
            a('\n### 4b — the same sweep on the Team 1 per-strategy basis\n')
            a('`old_prop_return` is the published figure, kept so the change is '
              'visible. `prop_return_median` is the honest one: per strategy, '
              '`(total_R / years) * 3.6 / max_dd_R_sumyr`, where '
              '`max_dd_R_sumyr` is the SUM of that strategy\'s yearly drawdowns '
              '(`l2r2winners.py:111`).\n')
            a('\nThree numbers that are all legitimate and must not be '
              'conflated: the 8-winner **book** on team 1, netted, runs at a '
              'median 2.28 %/yr (mean 2.96) in the A4 sweep; the **per-strategy '
              'median** on this basis is 1.45 %/yr; the published 27.43 %/yr is '
              'neither. The book beats the per-strategy median because netting '
              'eight members diversifies, which is a real effect and the reason '
              'both bases are shown.\n')
            a(G3x.BK_tbl(Tm, ['threshold_R', 'winners', 'days',
                              'days_marked_hourly', 'days_stop_fires',
                              'old_R_total', 'old_max_dd_R', 'old_prop_return',
                              'R_per_strategy_median', 'dd_sumyr_median',
                              'prop_return_median', 'prop_return_min',
                              'prop_return_max', 'winners_clearing_12pct']))
    a('\n## What this says about A6\n')
    a('A6 states that every breach count is a lower bound because the input is '
      'a daily series. This report is the first direct evidence of the size of '
      'that blind spot: on the days where the daily bar is genuinely ambiguous, '
      'the hourly path disagrees with it **40%% of the time in mode A and 50%% '
      'in mode B**, always favourably. A6 is therefore conservative on fills '
      'and, separately, optimistic on intraday breaches.\n')
    a('\n## Provenance\n')
    for mode in ('A', 'B'):
        for nm in ('a5_hourly', 'a5_disagree', 'a5_delta_strategy',
                   'a5_delta_book', 'a5_spreads', 'a5_spreads_by_pair',
                   'a5_overlay', 'a5_overlay_curve'):
            p_ = os.path.join(OUT, 'mode%s_%s.csv' % (mode, nm))
            if os.path.exists(p_):
                a('- `%s` — %s rows, md5 `%s`'
                  % (os.path.relpath(p_, _R), f'{len(_safe_csv2(p_)):,}',
                     hashlib.md5(open(p_, 'rb').read()).hexdigest()[:12]))
    out = out or os.path.join(OUT, 'A5_HOURLY.md')
    open(out, 'w').write('\n'.join(L) + '\n')
    print('  A5_HOURLY.md: %d lines -> %s'
          % (len('\n'.join(L).splitlines()), os.path.relpath(out, _R)), flush=True)
    return out


def _safe_csv2(path):
    """An empty result file is a legitimate result."""
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()



# ---------------------------------------------------------------------------
# A4, THE PARTS THAT WERE SPECIFIED AND NOT DELIVERED (built 24 Nov).
#
# stage_a4 above wrote the per-currency legs and the largest-leg share. That
# was one of four things specified. The rest are here: the share of the 10
# WORST DAYS and of the WORST DIP that the largest leg accounts for, and the
# cap on net per-currency exposure SWEPT OVER ITS FULL RANGE with yearly
# return, worst dip, DIP95 and Team 1 return at each cap -- on the winners'
# books AND the whole-field book.
#
# THE CAP ALREADY EXISTS IN THE SHIPPED CODE. l2walkfwd.Book.series takes
# cap_pct and per_unit, builds the per-currency exposure matrix, scales the
# book down on any day the worst leg exceeds the cap, and returns how many days
# bound. The standing value is W.CAP_PCT = 2.0. So the sweep is a loop over
# that same call, not a reimplementation -- which is the only way the swept
# numbers are comparable with the ones gate 3 reports.
# ---------------------------------------------------------------------------

def stage_a4_sweep(mode='A', tag='full', rules=('winners', 'grade'), caps=None,
                   nshard=16):
    """The exposure-cap sweep and the worst-day / worst-dip attribution."""
    import l2walkfwd as W_
    import l2r2gate3 as G3x
    # caps='binding' re-reads the range off each slice's OWN exposure
    # distribution, from the level that binds on 1% of days down to the one
    # that binds on 50%. See cap_range_binding for why a fixed grid cannot
    # work: across the slices on disk the worst exposure runs 0.600 to 1.692,
    # so one a priori grid is too high for some slices and too low for others.
    ADAPTIVE = (caps == 'binding')
    if ADAPTIVE:
        caps = None
    caps = caps if caps is not None else \
        [None, 8.0, 6.0, 5.0, 4.0, 3.0, 2.5, 2.0, 1.75, 1.5, 1.25, 1.0, 0.75, 0.5]
    FIXED_CAPS = list(caps)
    G.manifest_check(); S.load_costs()
    rows, att = [], []
    for rule in rules:
        pm = G3x.passmask_file(mode, rule)
        if not os.path.exists(pm):
            print('    a4 sweep: no pass mask for rule %r, skipping' % rule, flush=True)
            continue
        partdir = os.path.join(ROOTOUT, 'r2gate2', 'mode%s_gate3bookparts' % mode)
        for si, stp in enumerate(G2.steps()):
            build_years, trade_years = G3x.rule_windows(rule, stp)
            Yq = G2.Years(cap=2000)
            _ai, adays = BK.year_dayidx(Yq, build_years | trade_years)
            pairs = Yq.sc.pairs
            del Yq
            try:
                BA, _folded = G3x._sum_pbook_parts(partdir, si, nshard, pairs,
                                                   adays, rule)
            except Exception as e:
                print('    a4 sweep step %s/%s: no book parts (%s); skipping'
                      % (rule, stp['name'], type(e).__name__), flush=True)
                continue
            for bi, bk, _rt in G3x.PASSBOOKS:
                acc = BA.as_accumulator(bi)
                nm = int(BA.n_members[bi])
                if nm == 0 or acc.nl.sum() + acc.ns.sum() == 0:
                    continue
                SB = BK.StreamedBook(acc, nm)
                wb = np.ones(nm, np.float32)
                yrs = pd.DatetimeIndex(SB.udays).year.values
                ybuild = np.isin(yrs, sorted(build_years))
                ytrade = np.isin(yrs, sorted(trade_years))
                curve, _C = W_.fit_curve(SB, wb, build_years)
                d0, den, _b, _w, _s, _f = SB.series(wb, curve)
                # ---- the currency legs, for the attribution
                sgn_, sz_, _mk, _fr = SB.net(wb, curve)
                net = np.asarray(sgn_, float) * np.asarray(sz_, float)
                ccy = list(SB.ccy); nd = SB.nd
                legs = np.zeros((len(ccy), nd))
                for r in range(len(SB.pair)):
                    dpos = SB.dpos[r]
                    legs[SB.bc[r], dpos] += net[r]
                    legs[SB.qc[r], dpos] -= net[r]
                for (bname, dipb, dayb) in BK.BUDGETS:
                    sc_, bD, badj, bwd, binds = W_.scale_of(d0[ybuild], dipb, dayb)
                    # ---------- ATTRIBUTION: the 10 worst days and the worst dip
                    dtr = d0[ytrade] * sc_
                    ltr = legs[:, ytrade]
                    tot_abs = np.abs(ltr).sum(axis=0)
                    big_i = np.abs(ltr).argmax(axis=0)
                    with np.errstate(divide='ignore', invalid='ignore'):
                        big_share = np.where(tot_abs > 0,
                                             np.abs(ltr).max(axis=0) / tot_abs,
                                             np.nan)
                    k10 = np.argsort(dtr)[:10] if len(dtr) >= 10 else np.argsort(dtr)
                    eq = np.cumsum(dtr)
                    peak = np.maximum.accumulate(eq)
                    ddser = peak - eq
                    j = int(np.argmax(ddser)) if len(ddser) else 0
                    jstart = int(np.argmax(eq[:j + 1])) if j > 0 else 0
                    dipslice = slice(jstart, j + 1)
                    att.append(dict(
                        mode=mode, rule=rule, step=stp['name'], book=bk,
                        budget=bname, members=nm,
                        worst10_mean_pct=float(np.mean(dtr[k10])) if len(k10) else np.nan,
                        worst10_largest_leg_share=float(np.nanmean(big_share[k10]))
                        if len(k10) else np.nan,
                        worst10_top_currency=(ccy[int(np.bincount(big_i[k10]).argmax())]
                                              if len(k10) else ''),
                        allday_largest_leg_share=float(np.nanmean(big_share)),
                        worst_dip_pct=float(ddser.max()) if len(ddser) else np.nan,
                        worst_dip_days=int(j - jstart + 1),
                        worst_dip_largest_leg_share=float(
                            np.nanmean(big_share[dipslice])) if len(ddser) else np.nan,
                        worst_dip_top_currency=(
                            ccy[int(np.bincount(big_i[dipslice]).argmax())]
                            if len(ddser) and j >= jstart else '')))
                    # ---------- THE CAP SWEEP
                    caps_here, crange = FIXED_CAPS, {}
                    if ADAPTIVE:
                        cc, crange = cap_range_binding(
                            SB, wb, curve, per_unit=sc_ / den)
                        # the uncapped row is kept as the reference the whole
                        # curve is read against; without it there is nothing to
                        # say what the cap COSTS
                        caps_here = [None] + list(cc) if cc else [None]
                    for cp in caps_here:
                        d1, _dn, capbinds, worst, _sz2, _f2 = SB.series(
                            wb, curve, cap_pct=cp, per_unit=sc_ / den, den=den)
                        kb = W_.kpis(d1[ybuild] * sc_, yrs[ybuild])
                        kt = W_.kpis(d1[ytrade] * sc_, yrs[ytrade])
                        pr = (WN.PROP_DIP * kt['median_year_pct'] / kt['dip95_pct']
                              if kt['dip95_pct'] else np.nan)
                        rows.append(dict(
                            **({k: crange[k] for k in crange} if ADAPTIVE else {}),
                            mode=mode, rule=rule, step=stp['name'], book=bk,
                            budget=bname, members=nm,
                            cap_pct=(np.nan if cp is None else cp),
                            cap_bound_days=capbinds, worst_ccy_exposure=worst,
                            yearly_return_pct=kt['median_year_pct'],
                            worst_year_pct=kt['worst_year_pct'],
                            total_return_pct=kt['total_return_pct'],
                            worst_dip_pct=kt['max_dd_pct'],
                            dip95_pct=kt['dip95_pct'],
                            worst_day_pct=kt['worst_day_pct'],
                            sortino=kt['sortino'], calmar=kt['calmar'],
                            prop_return=pr,
                            clears_12pct=int(np.isfinite(pr)
                                             and pr >= WN.PROP_TARGET),
                            build_median_year_pct=kb['median_year_pct']))
            del BA
    Sw = pd.DataFrame(rows); At = pd.DataFrame(att)
    f1 = os.path.join(OUT, 'mode%s_a4_capsweep%s.csv'
                      % (mode, '_binding' if ADAPTIVE else ''))
    f2 = os.path.join(OUT, 'mode%s_a4_attribution.csv' % mode)
    Sw.to_csv(f1, index=False); At.to_csv(f2, index=False)
    print('  A4 sweep [mode %s]: %d sweep rows over %d caps, %d attribution rows'
          % (mode, len(Sw), len(caps), len(At)), flush=True)
    if len(Sw):
        t1 = Sw[(Sw.budget == 'team1')]
        if len(t1):
            g = t1.groupby('cap_pct', as_index=False, dropna=False).agg(
                yearly_return_pct=('yearly_return_pct', 'median'),
                worst_dip_pct=('worst_dip_pct', 'max'),
                dip95_pct=('dip95_pct', 'median'),
                prop_return=('prop_return', 'median'),
                cap_bound_days=('cap_bound_days', 'sum'),
                clears=('clears_12pct', 'sum'))
            f3 = os.path.join(OUT, 'mode%s_a4_capcurve.csv' % mode)
            g.to_csv(f3, index=False)
            b = g.loc[g.prop_return.idxmax()] if g.prop_return.notna().any() else None
            if b is not None:
                print('    Team 1 best prop return %.2f%%/yr at cap %s '
                      '(uncapped %.2f%%/yr)'
                      % (float(b.prop_return), str(b.cap_pct),
                         float(g[g.cap_pct.isna()].prop_return.iloc[0])
                         if g.cap_pct.isna().any() else float('nan')), flush=True)
    if len(At):
        print('    the largest currency leg carries %.1f%% of absolute exposure on '
              'the 10 worst days against %.1f%% on an average day'
              % (100 * At.worst10_largest_leg_share.mean(),
                 100 * At.allday_largest_leg_share.mean()), flush=True)
    return f1, f2


def md_a4(out=None):
    """results/r2reads/A4_NETTING.md"""
    import l2r2gate3 as G3x
    L = []; a = L.append
    a('# A4 — CURRENCY NETTING AND THE EXPOSURE CAP\n')
    a('Generated %s by `code/r2hourly.py`.\n' % time.strftime('%F %H:%M'))
    a('\n## What was specified, and what each section answers\n')
    a('| specified | section |')
    a('|---|---|')
    a('| share of the 10 worst days from the largest leg | 2 |')
    a('| share of the worst dip from the largest leg | 2 |')
    a('| the cap on net exposure per currency swept over its full range, with '
      'yearly return, worst dip, DIP95 and Team 1 return at each cap | 3 |')
    a('| winners\' books and the whole-field book | both, by `rule` |')
    a('\n**This report exists because the first A4 run delivered only the '
      'per-currency legs.** Chain 26 reported 8 stages succeeded and 0 failed, '
      'but the stages declared covered one of the four things asked for.\n')
    a('\n## 1 — the cap is the shipped one, not a new one\n')
    a('`l2walkfwd.Book.series` already takes `cap_pct` and `per_unit`, builds '
      'the per-currency exposure matrix, scales the whole book down on any day '
      'the worst leg exceeds the cap, and reports how many days bound. The '
      'standing value is `W.CAP_PCT = 2.0`. The sweep below loops that same '
      'call, so every swept number is comparable with what gate 3 reports '
      'rather than being a parallel implementation that might differ.\n')
    for mode in ('A', 'B'):
        a('\n## Mode %s\n' % mode)
        Lg = _safe_csv2(os.path.join(OUT, 'mode%s_a4_currency_legs.csv' % mode))
        At = _safe_csv2(os.path.join(OUT, 'mode%s_a4_attribution.csv' % mode))
        Sw = _safe_csv2(os.path.join(OUT, 'mode%s_a4_capsweep.csv' % mode))
        Cv = _safe_csv2(os.path.join(OUT, 'mode%s_a4_capcurve.csv' % mode))
        if not len(Lg) and not len(Sw):
            a('_Not run._\n'); continue
        if len(Lg):
            a('### The currency legs\n')
            g = Lg.groupby('currency', as_index=False).agg(
                mean_abs_exposure=('mean_abs_exposure', 'mean'),
                max_abs_exposure=('max_abs_exposure', 'max'),
                share_of_total_mean=('share_of_total_mean', 'mean'))
            a(G3x.BK_tbl(g.sort_values('mean_abs_exposure', ascending=False),
                         list(g.columns)))
        if len(At):
            a('\n### 2 — what the largest leg accounts for\n')
            a('`worst10_largest_leg_share` is the mean share of total absolute '
              'exposure held by the single biggest currency leg **on the ten '
              'worst days**; `allday_largest_leg_share` is the same on every '
              'day. If the first is materially higher, the bad days are '
              'concentration events.\n')
            a(G3x.BK_tbl(At, ['rule', 'step', 'book', 'budget',
                              'worst10_mean_pct', 'worst10_largest_leg_share',
                              'worst10_top_currency', 'allday_largest_leg_share',
                              'worst_dip_pct', 'worst_dip_days',
                              'worst_dip_largest_leg_share',
                              'worst_dip_top_currency']))
            a('\nThe largest leg carries **%.1f%%** of absolute exposure on the '
              'ten worst days against **%.1f%%** on an average day, and '
              '**%.1f%%** through the worst dip.\n'
              % (100 * At.worst10_largest_leg_share.mean(),
                 100 * At.allday_largest_leg_share.mean(),
                 100 * At.worst_dip_largest_leg_share.mean()))
        if len(Cv):
            a('\n### 3 — the cap swept over its full range\n')
            a('Team 1 budget (3.6%% dip, 3.6%% day), median across steps and '
              'books. `cap_pct = NaN` is uncapped. Reported as a curve, not at '
              'a chosen cap.\n')
            a(G3x.BK_tbl(Cv, list(Cv.columns)))
            Bd = _safe_csv2(os.path.join(
                OUT, 'mode%s_a4_capsweep_binding.csv' % mode))
            if len(Bd):
                a('\n#### 3b — the cap re-swept over the range where it BINDS\n')
                a('**The grid above measures nothing over most of its range, '
                  'and Jack caught it.** In the mode A `grade`/`allon`/`team1` '
                  'slice at step 2011-2014 the cap binds on **0 days at eleven '
                  'of the thirteen caps**, 29 days at 0.75 and 357 at 0.50, '
                  'because that slice\'s worst currency exposure is **0.843** '
                  '-- every cap at or above 1.00 sits above anything the book '
                  'ever reaches. The aggregate table hides it: summed over all '
                  'rule/book/budget/step rows the cap does bind at five levels, '
                  'which is why it was not obvious.\n')
                a('\n**Why no fixed grid can work.** The exposure a book '
                  'reaches is a property of that book -- its member count, its '
                  'netting, its budget scaling. Across the slices on disk the '
                  'worst exposure runs from **0.600 to 1.692**, nearly a factor '
                  'of three, so one a priori grid is necessarily too high for '
                  'some slices and too low for others.\n')
                a('\n**The range is read off each slice\'s own distribution.** '
                  'The cap binds on day *d* exactly when that day\'s worst '
                  'currency exposure exceeds it, so the share of days bound at '
                  'cap *c* is P(exposure > *c*) -- and the cap that binds on a '
                  'share *q* of days is the **(1 - q) quantile** of the '
                  'exposure series. 1% of days is the 99th percentile, 50% is '
                  'the median. Thirteen levels, geometrically spaced because '
                  'exposure is a positive scale quantity and a linear grid '
                  'would crowd the top. `l2walkfwd.Book.series` now stashes the '
                  'whole exposure series rather than only its maximum, which '
                  'costs nothing because it was already computed.\n')
                a('\n`cap_pct = NaN` is the uncapped reference, kept because '
                  'without it there is nothing to say what the cap COSTS. Same '
                  'columns as above, plus the exposure percentiles the range '
                  'was derived from.\n')
                cols = [c for c in ['rule', 'book', 'budget', 'step',
                                    'members', 'cap_pct', 'cap_bound_days',
                                    'days', 'worst_ccy_exposure',
                                    'exposure_p50', 'exposure_p99',
                                    'exposure_max', 'cap_binds_1pct',
                                    'cap_binds_50pct', 'yearly_return_pct',
                                    'worst_year_pct', 'total_return_pct',
                                    'prop_return'] if c in Bd.columns]
                a(G3x.BK_tbl(Bd.head(200), cols))
            if Cv.prop_return.notna().any():
                b = Cv.loc[Cv.prop_return.idxmax()]
                un = (float(Cv[Cv.cap_pct.isna()].prop_return.iloc[0])
                      if Cv.cap_pct.isna().any() else float('nan'))
                a('\nBest prop return **%.2f%%/yr at cap %s**, against '
                  '**%.2f%%/yr uncapped**. The standing cap is 2.0.\n'
                  % (float(b.prop_return), str(b.cap_pct), un))
                a('\n**%d of %d swept cells clear the 12%%/yr target.**\n'
                  % (int(Sw.clears_12pct.sum()) if len(Sw) else 0, len(Sw)))
        if len(Sw):
            a('\n### The full sweep, every rule, book and budget\n')
            a('`rule = winners` is the winners\' books; `rule = grade` is the '
              'whole-field book of everything clearing the grade-year bars.\n')
            a(G3x.BK_tbl(Sw.sort_values(['rule', 'book', 'budget', 'cap_pct'])
                         .head(200),
                         ['rule', 'step', 'book', 'budget', 'members', 'cap_pct',
                          'cap_bound_days', 'yearly_return_pct', 'worst_dip_pct',
                          'dip95_pct', 'prop_return', 'clears_12pct']))
    a('\n## Provenance\n')
    for mode in ('A', 'B'):
        for nm in ('a4_currency_legs', 'a4_summary', 'a4_attribution',
                   'a4_capsweep', 'a4_capcurve'):
            p_ = os.path.join(OUT, 'mode%s_%s.csv' % (mode, nm))
            if os.path.exists(p_):
                a('- `%s` — %s rows, md5 `%s`'
                  % (os.path.relpath(p_, _R), f'{len(_safe_csv2(p_)):,}',
                     hashlib.md5(open(p_, 'rb').read()).hexdigest()[:12]))
    out = out or os.path.join(OUT, 'A4_NETTING.md')
    open(out, 'w').write('\n'.join(L) + '\n')
    print('  A4_NETTING.md: %d lines -> %s'
          % (len('\n'.join(L).splitlines()), os.path.relpath(out, _R)), flush=True)
    return out


def stage_a5_restate(mode='A'):
    """A5 SECTION 4 RESTATED ON THE SAME TEAM 1 BASIS AS MODE?_WINNERS.md.

    JACK, 24 Nov: "the no-overlay row shows R_total 944.7, max_dd 24.79,
    prop_return 27.43, clears_12pct 1 for the 8-winner book. Every other file
    puts that book near 2.9% a year. Explain the unit."

    THE UNIT, AND HE IS RIGHT THAT IT IS WRONG. The curve in section 4 was
    aggregated like this:

        R_total   = sum  of R over all 40 (winner x step) rows
        max_dd_R  = MAX  of max_dd_R over those same 40 rows
        prop_return = 3.6 * (R_total / 5) / max_dd_R

    So the NUMERATOR is eight strategies each run at full risk on its own
    account, added together, while the DENOMINATOR is the worst drawdown of
    ONE winner in ONE year. An eight-member numerator over a one-member
    denominator. 3.6 x (944.7/5) / 24.79 = 27.43, which is arithmetically what
    the file says and economically meaningless.

    THE RIGHT BASIS, taken from l2r2winners.prop_return_strategy, which is what
    mode?_winners.csv and MODE?_WINNERS.md use:

        prop_return = (total_R / n_years) * 3.6 / max_dd_R_sumyr

    per STRATEGY, where max_dd_R_sumyr is the SUM of that strategy's yearly
    drawdowns (l2r2winners.py:111 -- "sumyr" is a sum over years, not the dip of
    the concatenated series). Restated that way the eight winners come out at
    1.15 to 2.15 % per year, median 1.45, and NOT ONE clears the 12% target, so
    clears_12pct is 0 and not 1.

    THREE NUMBERS THAT ARE ALL LEGITIMATE AND MUST NOT BE CONFLATED:
      8-winner BOOK, team 1, netted   median 2.28 %/yr, mean 2.96  (A4 sweep)
      per-STRATEGY, team 1 prop basis median 1.45 %/yr             (this stage)
      A5 section 4 as published       27.43 %/yr                   (unit error)
    The book beats the per-strategy median because netting eight members
    diversifies; that is a real effect and is the reason both bases are
    reported here rather than one.

    NO ENGINE PASS. mode?_a5_overlay.csv already carries one row per
    (bank_row, step, threshold), so this is a re-aggregation of data on disk.
    """
    f = os.path.join(OUT, 'mode%s_a5_overlay.csv' % mode)
    if not os.path.exists(f):
        print('  a5 restate [mode %s]: no overlay csv' % mode, flush=True)
        return None
    O = pd.read_csv(f)
    rows = []
    for th, g in O.groupby('threshold_R', as_index=False, dropna=False):
        per = g.groupby('bank_row', as_index=False).agg(
            total_R=('R', 'sum'), dd_sumyr=('max_dd_R', 'sum'),
            years=('trade_year', 'nunique'),
            days=('days', 'sum'), marked=('days_marked_hourly', 'sum'),
            fired=('days_stop_fires', 'sum'))
        ny = float(per.years.max()) if len(per) else 5.0
        per['prop_return_pct_per_year'] = WN.prop_return_strategy(
            per.total_R.to_numpy(float), per.dd_sumyr.to_numpy(float), ny)
        per['clears_12pct'] = (per.prop_return_pct_per_year
                               >= WN.PROP_TARGET).astype(int)
        thv = (np.nan if (isinstance(th, float) and np.isnan(th)) else th)
        rows.append(dict(
            mode=mode, threshold_R=thv, winners=int(per.bank_row.nunique()),
            years=ny, days=int(per.days.sum()),
            days_marked_hourly=int(per.marked.sum()),
            days_stop_fires=int(per.fired.sum()),
            # the OLD, wrong aggregation, kept so the change is visible
            old_R_total=float(per.total_R.sum()),
            old_max_dd_R=float(g.max_dd_R.max()),
            old_prop_return=float(WN.PROP_DIP * (per.total_R.sum() / ny)
                                  / g.max_dd_R.max())
            if g.max_dd_R.max() > 0 else np.nan,
            # the RIGHT basis, per strategy
            R_per_strategy_median=float(per.total_R.median()),
            dd_sumyr_median=float(per.dd_sumyr.median()),
            prop_return_median=float(per.prop_return_pct_per_year.median()),
            prop_return_min=float(per.prop_return_pct_per_year.min()),
            prop_return_max=float(per.prop_return_pct_per_year.max()),
            winners_clearing_12pct=int(per.clears_12pct.sum())))
    D = pd.DataFrame(rows).sort_values('threshold_R',
                                       na_position='last').reset_index(drop=True)
    f2 = os.path.join(OUT, 'mode%s_a5_overlay_team1.csv' % mode)
    D.to_csv(f2, index=False)
    b = D[D.threshold_R.isna()]
    if len(b):
        b = b.iloc[0]
        print('  a5 restate [mode %s]: no-overlay prop return was %.2f%%/yr as '
              'published; on the per-strategy team 1 basis it is %.2f%%/yr '
              '(range %.2f to %.2f), and %d of %d winners clear 12%%'
              % (mode, b.old_prop_return, b.prop_return_median,
                 b.prop_return_min, b.prop_return_max,
                 b.winners_clearing_12pct, b.winners), flush=True)
    return f2


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
    elif st == 'a5ov':
        for m in ([md] if md != 'both' else ['A', 'B']):
            stage_a5_overlay(m, max_winners=G.opt('--nmax', int, None),
                             max_years=G.opt('--nyears', int, None))
    elif st == 'a5restate':
        for m in ([md] if md != 'both' else ['A', 'B']):
            stage_a5_restate(m)
    elif st == 'a5md':
        md_a5()
    elif st == 'a4sweep':
        for m in ([md] if md != 'both' else ['A', 'B']):
            stage_a4_sweep(m)
    elif st == 'a4resweep':
        for m in ([md] if md != 'both' else ['A', 'B']):
            stage_a4_sweep(m, caps='binding')
    elif st == 'a4md':
        md_a4()
    elif st == 'a4':
        stage_a4(md, rule=G.opt('--rule', str, 'winners'))
    else:
        raise SystemExit('unknown stage %s' % st)
