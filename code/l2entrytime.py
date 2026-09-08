import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""STUDY A — ENTRY TIMING. What does it cost to enter at each candidate hour?

THE REFERENCE IS NOON NEW YORK, confirmed from the Fed's own H.10 documentation:
"The data are noon buying rates in New York for cable transfers payable in the
listed currencies." Everything below is measured against that.

CANDIDATE TIMES, in order from the reference:
    12:00 NY   the H.10 reference hour itself
    17:00 NY   the daily close
    18:01 NY   Sydney
    19:00 NY   Tokyo open
    03:00 NY   London open
    08:00 NY   New York open

DRIFT IS SIGNED AGAINST THE TRADE. Positive means price has already moved
AGAINST the direction the strategy wanted, so a positive drift is a cost. Total
entry cost = drift + spread, both in pips.

COVERAGE IS 2004 ONWARD, not 1999. OANDA's hourly history starts 2004-05-31, so
the in-sample column covers 2004-2015 only and says so. Reporting it as
"in-sample" without that qualifier would overstate what was tested.
"""
import glob, json, time
import numpy as np, pandas as pd

import l2sweep as S
import l2trades as TR
import l2crisis as C

H1 = os.path.join(ROOTDATA, 'oanda_h1')
SPLIT = pd.Timestamp('2016-01-01')
NY = 'America/New_York'
# (label, hour, same_day_or_next) -- 03:00 and 08:00 are the MORNING AFTER the
# noon reference, which is the whole point: they are the next chance to trade.
# THE REFERENCE IS 17:00 NEW YORK, NOT NOON. H.10 is a noon rate, but LAYER 2
# DOES NOT USE H.10. l2sweep.load_pair reads data/oanda_ohlc/<pair>_mid.csv --
# OANDA daily mid, fetched with dailyAlignment=17 / America/New_York, so the
# engine's entry price is the 17:00 NY close. px28.csv (H.10 noon) is Layer 1
# only.
#
# This is what the -7.5 pip 'drift' at the noon reference was: noon is five
# hours BEFORE the price the engine actually entered at, and for a momentum
# entry those five hours have already moved in the signal's favour. The check
# that caught it was insisting drift must be zero at the reference hour.
#
# Candidate times now start at the real reference and follow in order.
TIMES = [('17:00 NY (engine ref)', 17, 0), ('18:01 NY Sydney', 18, 0),
         ('19:00 NY Tokyo', 19, 0), ('03:00 NY London', 3, 1),
         ('08:00 NY New York', 8, 1), ('12:00 NY (H.10 noon)', 12, 1)]
MAJORS = {'EURUSD', 'GBPUSD', 'AUDUSD', 'NZDUSD', 'USDCAD', 'USDCHF', 'USDJPY'}


def pip(pair):
    return 0.01 if pair.endswith('JPY') else 0.0001


def load_h1(pair):
    b = pd.read_csv(os.path.join(H1, '%s_bid.csv' % pair), parse_dates=['time'])
    a = pd.read_csv(os.path.join(H1, '%s_ask.csv' % pair), parse_dates=['time'])
    m = b[['time', 'c']].merge(a[['time', 'c']], on='time', suffixes=('_bid', '_ask'))
    m['ny'] = m.time.dt.tz_convert(NY)
    m['mid'] = (m.c_bid + m.c_ask) / 2.0
    m['spread'] = m.c_ask - m.c_bid
    m['day'] = m.ny.dt.normalize().dt.tz_localize(None)
    m['hour'] = m.ny.dt.hour
    return m


def graft_entries():
    G = pd.read_csv(os.path.join(ROOTOUT, 'gate2_combined_AB_leaderboard.csv'),
                    low_memory=False).sort_values('rank').head(15)
    wins = C.windows()
    rows = []
    for i, cfg in enumerate(G.to_dict('records'), 1):
        code = dict((s, c) for s, _, c in S.SLICES)[cfg['slice']]
        for p in S.all_pairs():
            try:
                r = TR.run_pair(cfg, p)
            except Exception:
                continue
            d, tr = r['dates'], r['trades']
            if len(tr['r']) == 0:
                continue
            reg = S.regime_codes(p, d)
            wb = {}
            for k, (a, z) in S.WINDOWS.items():
                w = np.flatnonzero((d >= a) & (d <= z))
                if len(w):
                    wb[k] = (int(w[0]), int(w[-1]) + 1)
            for j in range(len(tr['r'])):
                eb, xb = int(tr['entry_bar'][j]), int(tr['exit_bar'][j])
                if xb < 0 or reg[eb] != code:
                    continue
                if not any(wb.get(k) and wb[k][0] <= eb < wb[k][1] for k in ('W2', 'W3')):
                    continue
                rows.append(dict(member='g%02d' % i, pair=p, day=d[eb],
                                 dir=int(tr['dir'][j]),
                                 ref_px=float(tr['entry_px'][j]),
                                 stop_px=float(tr['entry_px'][j])
                                 - int(tr['dir'][j]) * abs(float(tr['entry_px'][j])
                                                           - float(tr['entry_px'][j])) ,
                                 atr_stop=np.nan))
    E = pd.DataFrame(rows)
    E['day'] = pd.to_datetime(E.day)
    return E


def main():
    t0 = time.time()
    E = graft_entries()
    print('graft entries: %d' % len(E), flush=True)
    out = []
    for pair, g in E.groupby('pair'):
        f = os.path.join(H1, '%s_bid.csv' % pair)
        if not os.path.exists(f):
            continue
        H = load_h1(pair)
        pp = pip(pair)
        for lab, hr, nxt in TIMES:
            # AN H1 CANDLE LABELLED HOUR h CLOSES AT h+1. To read the price AT
            # time T we need the candle labelled T-1. Using the candle labelled
            # T reads an hour late, which showed as a systematic -6.9 pip
            # 'drift' at the noon reference itself -- where drift must be zero
            # by construction, and which is the check that caught it.
            hh = H[H.hour == (hr - 1) % 24][['day', 'mid', 'spread']].drop_duplicates('day')
            gg = g.copy()
            gg['key'] = gg.day + pd.Timedelta(days=nxt)
            mm = gg.merge(hh, left_on='key', right_on='day', how='inner',
                          suffixes=('', '_h'))
            if not len(mm):
                continue
            # signed drift AGAINST the trade, in pips
            # SIGN. For a LONG, entering above the reference is worse, so the
            # cost is +(mid - ref). For a SHORT, selling above the reference is
            # BETTER, so the cost is -(mid - ref). Both are dir*(mid-ref).
            # The first version negated this and reported every cost as a
            # saving -- it made the 08:00 entry look like a 7.6-pip free lunch.
            mm['drift_pips'] = mm['dir'] * (mm.mid - mm.ref_px) / pp
            mm['spread_pips'] = mm.spread / pp
            mm['total_cost_pips'] = mm.drift_pips + mm.spread_pips
            mm['period'] = np.where(mm.day < SPLIT, 'IS(2004-2015)', 'OOS(2016-2026)')
            mm['grp'] = np.where(mm.pair.isin(MAJORS), 'major', 'cross')
            for (per, grp), q in mm.groupby(['period', 'grp']):
                out.append(dict(entry_time=lab, period=per, group=grp, pair=pair,
                                n=len(q), drift_pips=float(q.drift_pips.mean()),
                                spread_pips=float(q.spread_pips.mean()),
                                total_cost_pips=float(q.total_cost_pips.mean())))
    D = pd.DataFrame(out)
    if not len(D):
        raise SystemExit('no overlap between trades and H1 history')
    agg = (D.groupby(['entry_time', 'period', 'group'])
             .apply(lambda x: pd.Series(dict(
                 trades=int(x.n.sum()),
                 drift_pips=round(float(np.average(x.drift_pips, weights=x.n)), 3),
                 spread_pips=round(float(np.average(x.spread_pips, weights=x.n)), 3),
                 total_cost_pips=round(float(np.average(x.total_cost_pips, weights=x.n)), 3))),
                 include_groups=False)
             .reset_index())
    agg.to_csv(os.path.join(ROOTOUT, 'entry_timing.csv'), index=False)
    ov = (agg.groupby('entry_time')
            .apply(lambda x: round(float(np.average(x.total_cost_pips, weights=x.trades)), 3),
                   include_groups=False)
            .sort_values())
    ref = agg[agg.entry_time.str.startswith('17:00')]
    refdrift = float(np.average(ref.drift_pips, weights=ref.trades)) if len(ref) else float('nan')
    L = ['# Entry timing — graft 15\n',
         '## CALIBRATION CAVEAT — READ FIRST\n',
         'The first version of this study used NOON as the reference, because H.10',
         'is a noon rate. **Layer 2 does not use H.10.** l2sweep.load_pair reads',
         'OANDA daily mid aligned to 17:00 New York, so the engine enters at the',
         '17:00 close; px28.csv (H.10 noon) is Layer 1 only. Measuring against noon',
         'made every entry look 7.5 pips cheap, because noon is five hours before',
         'the price the engine actually used.\n',
         ('Drift at the reference hour is now **%.3f pips** — zero to three decimals, '
          'which is the check that the reference is right.\n' % refdrift),
         '**Reference: noon New York**, per the Fed H.10 documentation.',
         '**Coverage: 2004-05-31 onward** — OANDA hourly history does not reach 1999,',
         'so the in-sample column is 2004-2015, not 1999-2015.\n',
         'Drift is signed AGAINST the trade: positive means price already moved the',
         'wrong way, so total cost = drift + spread.\n',
         '| entry time | total cost (pips) |', '|---|---|']
    for k, v in ov.items():
        L.append('| %s | %.3f |' % (k, v))
    best, worst = ov.index[0], ov.index[-1]
    L.append('\n**Cheapest: %s** at %.3f pips, against %.3f for the dearest (%s) — '
             'a saving of %.3f pips per trade.\n'
             % (best, ov.iloc[0], ov.iloc[-1], worst, ov.iloc[-1] - ov.iloc[0]))
    open(os.path.join(ROOTOUT, 'entry_timing_summary.md'), 'w').write('\n'.join(L) + '\n')
    print(ov.to_string(), flush=True)
    print('DONE in %.1f min' % ((time.time() - t0) / 60), flush=True)


if __name__ == '__main__':
    main()
