import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""STUDY C — INTRADAY TRIPWIRE. What level catches a 4% day before it happens?

PROVISIONAL. TWO REASONS, BOTH RECORDED RATHER THAN QUIETLY FIXED.

1. THE BOOK IS WRONG FOR THE QUESTION. This stacks every member's position
   independently, so three members long EURUSD hold three EURUSD positions. The
   live book will NET votes per pair and size by agreement -- Layer 4, not built.
   A stacked book overstates gross exposure and understates netting, so both the
   trip counts and the false-alarm rate move once Layer 4 exists.

2. A KNOWN DEFECT IN THE FLOATING-LOSS BASELINE. `pnl` below is measured from
   each position's ENTRY price, not from its value at the PRIOR DAY'S CLOSE. The
   daily prop limit is a change since the previous close, so a position that is
   deep in profit and gives some back never registers here. That is why this run
   finds only 2-3 breach days in twenty-two years -- the number is far too low
   and must not be quoted. Fixing it needs the prior-close mark per position,
   which is the same restructuring Layer 4 forces anyway.

RUN IT UNCHANGED ON THE LAYER 4 BOOK when that exists:
    python code/l2tripwire.py --positions results/layer4_positions.csv
with columns: day, pair, dir, size, entry, stop. When --positions is given the
roster path is ignored and the file is used verbatim, so no assumption about how
the book was built survives into this script.

Rebuilds the account's equity HOUR BY HOUR with every open position marked to
that hour's mid, so floating losses are visible as they develop rather than only
when a trade closes. That is what the daily prop limit actually measures.

RE-RUNNABLE ON ANY ROSTER: --roster results/team1_roster.csv. Defaults to the
graft 15 until the team builder lands.

SIZED SO DIP95 = 3.6%, using the same day-glued shuffle the team builder uses.

WHAT A TRIPWIRE CAN AND CANNOT SEE. The hourly series is a mid price at the top
of each hour, so a spike that begins and ends inside one hour is invisible here.
Every 'undetectable' count below is therefore a FLOOR, not a ceiling: the real
number of days that breach without warning is at least this and probably more.
"""
import glob, json, time, argparse
import numpy as np, pandas as pd

import l2sweep as S
import l2trades as TR
import l2crisis as C

H1 = os.path.join(ROOTDATA, 'oanda_h1')
NY = 'America/New_York'
LEVELS = [1.5, 2.0, 2.5, 3.0, 3.2, 3.5]
DIP_BUDGET = 3.6
SEED = 20260912
N_SHUF = 10000


def dip95(daily, rng):
    n = len(daily)
    if n < 3:
        return 0.0
    out = np.empty(N_SHUF); idx = np.arange(n)
    for i in range(N_SHUF):
        rng.shuffle(idx)
        eq = np.cumsum(daily[idx])
        out[i] = np.max(np.maximum.accumulate(eq) - eq)
    return float(np.percentile(out, 95))


def load_mid(pair):
    b = pd.read_csv(os.path.join(H1, '%s_bid.csv' % pair), parse_dates=['time'])
    a = pd.read_csv(os.path.join(H1, '%s_ask.csv' % pair), parse_dates=['time'])
    m = b[['time', 'c']].merge(a[['time', 'c']], on='time', suffixes=('_b', '_a'))
    m['mid'] = (m.c_b + m.c_a) / 2.0
    ny = m.time.dt.tz_convert(NY)
    m['day'] = ny.dt.normalize().dt.tz_localize(None)
    m['hr'] = ny.dt.hour
    return m[['day', 'hr', 'mid']]


def roster_trades(roster):
    wins = C.windows()
    rows = []
    for i, cfg in enumerate(roster.to_dict('records'), 1):
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
                rows.append(dict(member=i, pair=p, entry=d[eb], exit=d[xb],
                                 dir=int(tr['dir'][j]),
                                 entry_px=float(tr['entry_px'][j]),
                                 units=float(tr['units'][j]), R=float(tr['r'][j])))
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--roster', default=None)
    ap.add_argument('--positions', default=None,
                    help='daily position file: day,pair,dir,size,entry,stop. '
                         'Overrides --roster. This is the Layer 4 entry point.')
    a = ap.parse_args()
    t0 = time.time()
    rng = np.random.default_rng(SEED)
    if a.positions and not os.path.exists(a.positions):
        # FAIL LOUDLY. Falling back to the roster on a bad path would silently
        # run the graft and report it as the Layer 4 book.
        raise SystemExit('position file not found: %s' % a.positions)
    if a.positions:
        P = pd.read_csv(a.positions, parse_dates=['day'])
        need = {'day', 'pair', 'dir', 'size', 'entry'}
        miss = need - set(P.columns)
        if miss:
            raise SystemExit('position file missing columns: %s' % sorted(miss))
        # a daily position file already states the book per day, so no roster,
        # no trade reconstruction and no equal-weight assumption is applied
        # a position file states ONE DAY per row, so entry and exit are that day
        T = P.rename(columns={'size': 'units', 'entry': 'entry_px'}).copy()
        T['entry'] = T['day']
        T['exit'] = T['day']
        T['R'] = 0.0
        tag = os.path.basename(a.positions).replace('.csv', '')
        n_mem = 1
        print('position file: %s, %d rows, %d days' % (tag, len(T), T.day.nunique()), flush=True)
        R = None
    elif a.roster and os.path.exists(a.roster):
        R = pd.read_csv(a.roster); tag = os.path.basename(a.roster).split('_')[0]
    else:
        R = pd.read_csv(os.path.join(ROOTOUT, 'gate2_combined_AB_leaderboard.csv'),
                        low_memory=False).sort_values('rank').head(15)
        tag = 'graft15'
    if R is not None:
        print('roster: %s, %d members' % (tag, len(R)), flush=True)
        T = roster_trades(R)
        print('trades: %d' % len(T), flush=True)
        n_mem = R.shape[0]

    # sizing: equal weight, daily closed-trade R -> DIP95 = 3.6%
    # A POSITION FILE IS ALREADY SIZED. It states the book per day, so there is
    # nothing to scale -- rescaling it would silently overrule Layer 4's own
    # sizing. Only a roster-derived book, which is unit-weighted, gets scaled.
    if a.positions:
        scale = 1.0
        print('position file is pre-sized: scale fixed at 1.0', flush=True)
    else:
        daily_close = T.groupby(pd.to_datetime(T.exit).dt.normalize()).R.sum() / n_mem
        d95 = dip95(daily_close.values, rng)
        if d95 <= 0:
            raise SystemExit('DIP95 is zero -- cannot size this book')
        scale = DIP_BUDGET / d95
    print('scale so DIP95 = %.1f%%: %.4f' % (DIP_BUDGET, scale), flush=True)

    # hourly mark-to-market
    mids = {}
    for p in sorted(set(T.pair)):
        f = os.path.join(H1, '%s_bid.csv' % p)
        if os.path.exists(f):
            mids[p] = load_mid(p)
    rows = []
    for p, g in T.groupby('pair'):
        if p not in mids:
            continue
        M = mids[p]
        for t in g.itertuples():
            days = pd.date_range(t.entry, t.exit, freq='D')
            sub = M[M.day.isin(days)]
            if not len(sub):
                continue
            pnl = t.dir * (sub.mid.values - t.entry_px) * t.units / S.RISK / n_mem * scale
            rows.append(pd.DataFrame(dict(day=sub.day.values, hr=sub.hr.values, pnl=pnl)))
    if not rows:
        raise SystemExit('no hourly overlap')
    A = pd.concat(rows, ignore_index=True)
    hourly = A.groupby(['day', 'hr']).pnl.sum().reset_index()
    # equity path: cumulative across days, floating within day
    dayclose = hourly.sort_values(['day', 'hr']).groupby('day').pnl.last()
    base = dayclose.shift(1).fillna(0.0).cumsum()
    hourly = hourly.merge(base.rename('prev_eq'), left_on='day', right_index=True, how='left')
    hourly['float_vs_prev'] = hourly.pnl  # already relative to that day's open positions
    worst = hourly.groupby('day').float_vs_prev.min().rename('worst_intraday')
    close = hourly.sort_values(['day', 'hr']).groupby('day').float_vs_prev.last().rename('day_close')
    D = pd.concat([worst, close], axis=1).dropna()
    D['worst_pct'] = -D.worst_intraday
    D['close_pct'] = -D.day_close
    out = []
    for lv in LEVELS:
        trip = D[D.worst_pct >= lv]
        rec = trip[trip.close_pct < lv]
        b36 = D[D.worst_pct >= 3.6]; b40 = D[D.worst_pct >= 4.0]
        undet = b40[b40.worst_pct < lv]
        cost = float((trip.close_pct.clip(upper=lv) - lv).sum())
        yrs = max(1.0, (D.index.max() - D.index.min()).days / 365.25)
        out.append(dict(level_pct=lv, days_tripped=len(trip),
                        false_alarms=len(rec),
                        false_alarm_pct=round(100.0 * len(rec) / max(1, len(trip)), 1),
                        went_past_3_6=int((trip.worst_pct >= 3.6).sum()),
                        went_past_4_0=int((trip.worst_pct >= 4.0).sum()),
                        undetectable_4_0=len(undet),
                        cost_of_closing_per_year=round(cost / yrs, 3),
                        trips_per_year=round(len(trip) / yrs, 2)))
    O = pd.DataFrame(out)
    O.to_csv(os.path.join(ROOTOUT, 'tripwire.csv'), index=False)
    safe = O[O.undetectable_4_0 == 0]
    L = ['# Intraday tripwire — %s\n' % tag,
         '## PROVISIONAL — DO NOT QUOTE THESE NUMBERS\n',
         '**1. The book is wrong for the question.** Every member\'s position is',
         'stacked independently, so three members long EURUSD hold three EURUSD',
         'positions. The live book will net votes per pair and size by agreement',
         '(Layer 4, not built). Trip counts and false-alarm rates both move once',
         'that exists.\n',
         '**2. A known defect in the floating-loss baseline.** Position P&L is',
         'measured from each position\'s ENTRY price, not from its value at the',
         'PRIOR DAY\'S CLOSE. The daily prop limit is a change since the previous',
         'close, so a position deep in profit that gives some back never registers.',
         'That is why this run finds only a handful of breach days in twenty-two',
         'years — the count is far too low. Fixing it needs the prior-close mark',
         'per position, which is the same restructuring Layer 4 forces anyway, so',
         'it is deliberately not patched here.\n',
         'Rerun unchanged on the Layer 4 book:',
         '`python code/l2tripwire.py --positions results/layer4_positions.csv`',
         'with columns day, pair, dir, size, entry, stop.\n',
         'Equity rebuilt hour by hour with open positions marked to each hour\'s mid.',
         'Sized so DIP95 = %.1f%% (scale %.4f). Coverage 2004-05 onward.\n' % (DIP_BUDGET, scale),
         '**A spike that starts and ends inside one hour is invisible in hourly data,',
         'so every "undetectable" count is a FLOOR, not a ceiling.**\n',
         '']
    if len(safe):
        r = safe.iloc[-1]
        L.append('\n**Lowest level that never lets 4.0%% through: %.1f%%**, '
                 'firing %.2f times a year with %.1f%% false alarms, costing %.3f%% '
                 'of account per year to close at.\n'
                 % (r.level_pct, r.trips_per_year, r.false_alarm_pct,
                    r.cost_of_closing_per_year))
    else:
        L.append('\n**No tested level catches every 4.0%% day.**\n')
    open(os.path.join(ROOTOUT, 'tripwire_summary.md'), 'w').write('\n'.join(L) + '\n')
    print(O.to_string(index=False), flush=True)
    print('DONE in %.1f min' % ((time.time() - t0) / 60), flush=True)


if __name__ == '__main__':
    main()
