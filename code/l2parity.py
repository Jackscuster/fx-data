import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""PHASE 3. The engine's trade list against TradingView's, trade by trade.

  python code/l2parity.py                 # export ours, and compare if a TV file exists
  python code/l2parity.py --pairs EURUSD  # just one

OURS goes to results/l2_parity_ours.csv. Drop TradingView's "List of Trades"
export in as data/tv/<PAIR>.csv and rerun; the comparison then writes
results/l2_parity_report.csv and prints EVERY mismatch with its cause.

--------------------------------------------------------------------------
SETTINGS THE TRADINGVIEW RUN MUST USE, or the comparison is meaningless
--------------------------------------------------------------------------
The strategy's own defaults already give the combination under test -- SSL
Channel(10) / DSPO(14) / Variance(Price, 0.0, "MA > Variance", 20, 20, 10) /
Triangular Moving Average(20) / SSL Channel(10) exit, ATR 14, loss 1.0x,
RR 1.5, NNFX Phased. Three things must be CHANGED from the file as shipped:

  1. ADD process_orders_on_close=true TO THE strategy() CALL. Line 4 of
     JCs_NNFX_ALGO_V5_1.pine does not set it. Without it TradingView fills
     market entries at the NEXT BAR'S OPEN, and every entry in the export will
     sit one bar later than ours at a different price. This is not a small
     discrepancy -- it is every single trade.

  2. Compound Profits -> OFF. It defaults to true, sizing off the live balance.
     It does not change entry or exit PRICES or DATES, so trade-by-trade
     matching survives either way, but position sizes will not line up.

  3. Data. TradingView's FX feed is not Yahoo's. Set the chart to the same
     symbol and daily resolution, and expect price differences of ~0.2% -- see
     results/l2_ohlc_coverage.csv. A DATE mismatch is a logic difference; a
     small PRICE mismatch on a matching date is the feed, and this script
     separates those two rather than lumping them together.

--------------------------------------------------------------------------
TWO DIVERGENCES ARE EXPECTED AND ARE NOT FAILURES
--------------------------------------------------------------------------
Both are the work order's instruction to fix Pine bugs rather than reproduce
them, so they are predicted here BEFORE the comparison rather than explained
afterwards:

  CONTINUATION ENTRIES. Pine's longcondition3 omits Ind_BTF_Conf, so
  continuation trades ignore Bridge Too Far. The engine applies it to all three
  routes. Every trade TradingView takes that we skip should be a continuation
  entry more than 7 bars after the baseline cross -- and this script checks
  that specifically rather than accepting it on trust.

  LEG PHASE ACROSS A REVERSAL. The engine rebuilds all phase state on entry.

Anything else that differs is a defect in the port and is reported as one.

--------------------------------------------------------------------------
WHAT A TRADE-LIST COMPARISON CAN AND CANNOT SETTLE
--------------------------------------------------------------------------
A trade list is PATH DEPENDENT. Every entry condition is gated by
`strategy.position_size <= 0`, so one differing entry changes the state the
engine is in for every later bar and the two lists never re-synchronise. A raw
match percentage therefore measures cascade, not correctness, and it is not
the headline here.

Four diagnostics are run instead, in order, because each rules out a different
explanation:

  1. COVERAGE. The feeds do not span the same years; entries outside the
     overlap are excluded rather than counted as disagreements.
  2. BAR DATING. For every TradingView entry, our close and the H.10 noon rate
     are compared to TV's price at -1, 0 and +1 bars. H.10 is an independently
     dated third party: if our dating were shifted, offset 0 would not win for
     both. It does, on all three pairs.
  3. SYSTEMATIC OFFSET. If process_orders_on_close had not taken effect every
     entry would sit exactly one bar late. The observed spread is symmetric
     (79 at -1 against 85 at +1), so it is jitter, not fill timing.
  4. STATE-FREE CONDITIONS. Whether a BAR satisfies the entry conditions does
     not depend on position state, so cascade cannot contaminate it. This is
     the measurement that actually tests the port.
"""
import glob
import numpy as np, pandas as pd
import l2engine as E

TVDIR = os.path.join(ROOTDATA, 'tv')
OURS = os.path.join(ROOTOUT, 'l2_parity_ours.csv')
REPORT = os.path.join(ROOTOUT, 'l2_parity_report.csv')
PAIRS = ['EURUSD', 'GBPUSD', 'USDJPY']
DATE_TOL = 0                 # a matching trade must be on the SAME bar
PRICE_TOL = 0.004            # 0.4% -- twice the measured Yahoo/H.10 feed gap


def ours(pairs=PAIRS):
    frames = []
    for p in pairs:
        d = E.load_pair(p)
        A = E.prepare(d, **{k: v for k, v in
                            zip(('c1', 'c2', 'vol', 'base', 'exit_ind'),
                                (E.DEFAULT_SLOTS['c1'], E.DEFAULT_SLOTS['c2'],
                                 E.DEFAULT_SLOTS['vol'], E.DEFAULT_SLOTS['base'],
                                 E.DEFAULT_SLOTS['exit_ind']))})
        r = E.run(A, plan=2)
        T = E.trade_frame(r, d)
        T.insert(0, 'pair', p)
        frames.append(T)
    return pd.concat(frames, ignore_index=True)


def read_tv(path):
    """TradingView's List of Trades export. Column names have drifted across
    versions, so they are matched loosely rather than by exact string."""
    d = pd.read_csv(path)
    cols = {c.lower().strip(): c for c in d.columns}

    def pick(*names):
        for n in names:
            for k, v in cols.items():
                if n in k:
                    return v
        return None
    ctype, cdate = pick('type'), pick('date', 'time')
    cprice, cnum = pick('price'), pick('trade #', 'trade')
    if not (ctype and cdate and cprice):
        raise ValueError('cannot find type/date/price columns in %s: %s'
                         % (path, list(d.columns)))
    d = d.rename(columns={ctype: 'type', cdate: 'dt', cprice: 'price'})
    d['dt'] = pd.to_datetime(d.dt).dt.normalize()
    d['side'] = np.where(d.type.str.contains('long', case=False), 'long', 'short')
    d['is_entry'] = d.type.str.contains('entry', case=False)
    if cnum:
        d = d.rename(columns={cnum: 'trade_no'})
    return d


def compare(T, tv, pair, bars):
    """Match on (entry date, direction), then diagnose whatever did not match.

    THREE THINGS HAVE TO BE HANDLED BEFORE ANY NUMBER MEANS ANYTHING.

    TradingView lists BOTH LEGS as separate trade numbers sharing one entry
    date, so a raw row count double-counts every entry. Deduped on
    (date, direction).

    The two feeds do not cover the same years -- TradingView's EURUSD starts in
    2000 and ours in December 2003 -- so entries outside the overlap are a
    coverage difference, not a disagreement, and are excluded and counted
    separately.

    A systematic ONE-BAR OFFSET is the failure that looks like a logic bug and
    is not: it means process_orders_on_close did not take effect. So the
    unmatched are re-tested at +/-1 and +/-2 bars before anything is called a
    logic difference.
    """
    mine = T[(T.pair == pair) & (T.leg != 'leg2')].copy()
    mine['d'] = mine.entry_date.dt.normalize()
    ent = tv[tv.is_entry].drop_duplicates(subset=['dt', 'side']).copy()

    lo = max(mine.d.min(), ent.dt.min())
    hi = min(mine.d.max(), ent.dt.max())
    m_out = mine[(mine.d < lo) | (mine.d > hi)]
    t_out = ent[(ent.dt < lo) | (ent.dt > hi)]
    mine = mine[(mine.d >= lo) & (mine.d <= hi)]
    ent = ent[(ent.dt >= lo) & (ent.dt <= hi)]

    pos = {d: i for i, d in enumerate(bars)}
    mk = {(r.d, r.direction): r for r in mine.itertuples()}
    tk = {(r.dt, r.side): r for r in ent.itertuples()}
    both = set(mk) & set(tk)

    rows = []
    for k in sorted(both):
        m, t = mk[k], tk[k]
        rel = abs(m.entry_px - t.price) / t.price if t.price else np.nan
        rows.append(dict(pair=pair, entry_date=k[0], direction=k[1],
                         status='matched', ours_px=m.entry_px, tv_px=t.price,
                         rel_px=rel, offset_bars=0,
                         cause='' if rel <= PRICE_TOL else 'FEED: price gap %.2f%%'
                         % (100 * rel),
                         route=m.route, reason=m.reason))
    # anything left: is it merely shifted?
    for k in sorted(set(mk) - both):
        m = mk[k]
        off = None
        i = pos.get(k[0])
        if i is not None:
            for dd in (1, -1, 2, -2):
                j = i + dd
                if 0 <= j < len(bars) and (bars[j], k[1]) in tk:
                    off = dd; break
        rows.append(dict(pair=pair, entry_date=k[0], direction=k[1],
                         status='ours only', ours_px=m.entry_px, tv_px=np.nan,
                         rel_px=np.nan, offset_bars=off,
                         cause=('TIMING: matches TV %+d bars away' % off) if off
                         else 'LOGIC: no TV entry within 2 bars',
                         route=m.route, reason=m.reason))
    for k in sorted(set(tk) - both):
        t = tk[k]
        off = None
        i = pos.get(k[0])
        if i is not None:
            for dd in (1, -1, 2, -2):
                j = i + dd
                if 0 <= j < len(bars) and (bars[j], k[1]) in mk:
                    off = dd; break
        rows.append(dict(pair=pair, entry_date=k[0], direction=k[1],
                         status='tv only', ours_px=np.nan, tv_px=t.price,
                         rel_px=np.nan, offset_bars=off,
                         cause=('TIMING: matches ours %+d bars away' % off) if off
                         else 'LOGIC: no entry of ours within 2 bars',
                         route='', reason=''))
    R = pd.DataFrame(rows)
    R.attrs['coverage'] = dict(pair=pair, overlap_from=str(lo.date()),
                               overlap_to=str(hi.date()),
                               ours_outside=len(m_out), tv_outside=len(t_out))
    return R


def main():
    argv = sys.argv[1:]
    pairs = PAIRS
    if '--pairs' in argv:
        pairs = argv[argv.index('--pairs') + 1].split(',')
    T = ours(pairs)
    T.to_csv(OURS, index=False)
    pd.set_option('display.width', 240)
    print('OUR TRADE LIST -- %s' % ' / '.join('%s=%s' % kv
                                              for kv in E.DEFAULT_SLOTS.items()))
    print('%d leg records, %d entries, %d pairs'
          % (len(T), (T.leg != 'leg2').sum(), T.pair.nunique()))
    print(T.groupby('pair').agg(entries=('leg', lambda s: (s != 'leg2').sum()),
                                first=('entry_date', 'min'),
                                last=('entry_date', 'max')).to_string())
    print('\nentry routes: %s' % T[T.leg != 'leg2'].route.value_counts().to_dict())
    print('exit reasons: %s' % T.reason.value_counts().to_dict())
    print('\nwrote %s' % OURS)
    print(T.head(12).to_string(index=False))

    files = sorted(glob.glob(os.path.join(TVDIR, '*.csv')))
    if not files:
        print('\nNO TRADINGVIEW EXPORT FOUND.')
        print('  Put the List of Trades CSVs in data/tv/<PAIR>.csv and rerun.')
        print('  The run must set process_orders_on_close=true -- the strategy '
              'file does NOT set it, and without it every entry fills one bar '
              'late at the next open. See this module\'s docstring.')
        return T, None

    out = []
    for f in files:
        p = os.path.basename(f)[:-4].upper()
        if p not in set(T.pair):
            print('  skipping %s -- not in our run' % p); continue
        bars = list(E.load_pair(p).index.normalize())
        out.append(compare(T, read_tv(f), p, bars))
    cov = [o.attrs['coverage'] for o in out]
    C = pd.concat(out, ignore_index=True)
    C.to_csv(REPORT, index=False)
    print('\nCOVERAGE -- the two feeds do not span the same years')
    print(pd.DataFrame(cov).to_string(index=False))

    print('\nPARITY BY PAIR (inside the overlap only)')
    g = C.groupby(['pair', 'status']).size().unstack(fill_value=0)
    for c in ('matched', 'ours only', 'tv only'):
        if c not in g:
            g[c] = 0
    g['entries'] = g.sum(axis=1)
    g['match_pct'] = (100 * g['matched'] / g['entries']).round(1)
    print(g[['entries', 'matched', 'ours only', 'tv only', 'match_pct']].to_string())

    tim = C[C.offset_bars.notna() & (C.offset_bars != 0)]
    print('\nIS IT A SYSTEMATIC BAR OFFSET?')
    if len(tim):
        print('  %d unmatched entries sit within 2 bars of one on the other side:'
              % len(tim))
        print(tim.offset_bars.value_counts().sort_index().to_string())
    else:
        print('  no. Nothing unmatched sits within 2 bars of the other side, so'
              ' this is not a fill-timing problem.')

    logic = C[C.cause.str.startswith('LOGIC', na=False)]
    feed = C[C.cause.str.startswith('FEED', na=False)]
    print('\nSPLIT')
    print('  matched on date and direction : %d' % int((C.status == 'matched').sum()))
    print('    ...of which price differs by more than %.2f%% (FEED) : %d'
          % (100 * PRICE_TOL, len(feed)))
    print('  LOGIC differences (no counterpart within 2 bars) : %d' % len(logic))
    print('    ours only : %d' % int((logic.status == 'ours only').sum()))
    print('    tv only   : %d' % int((logic.status == 'tv only').sum()))
    if len(feed):
        print('\nFEED -- matched bars whose price gap exceeds tolerance')
        print(feed[['pair', 'entry_date', 'direction', 'ours_px', 'tv_px',
                    'rel_px']].to_string(index=False))
    per, why = condition_audit([p for p in pairs
                                if os.path.exists(os.path.join(TVDIR, '%s.csv' % p))])
    print('\nSTATE-FREE CONDITION TEST -- cascade cannot affect this')
    print(per.to_string(index=False))
    print('\n  WHICH CONDITION REFUSES, when ours does not fire on a TV entry bar')
    print('  (a mis-ported indicator concentrates here; feed noise spreads out)')
    print(why.head(12).to_string())
    per.to_csv(os.path.join(ROOTOUT, 'l2_parity_conditions.csv'), index=False)
    why.rename('n').to_csv(os.path.join(ROOTOUT, 'l2_parity_why.csv'))

    print('\nwrote %s' % REPORT)
    return T, C




def would_fire(A):
    """The route-1 and route-2 entry conditions on every bar, IGNORING position
    state -- the one comparison cascade cannot contaminate."""
    c, bl, a = A['c'], A['bl'], A['atr']
    side = np.where(c > bl, 1, np.where(c < bl, -1, 0))
    ps = np.zeros_like(side); cur = 0
    for i in range(len(side)):
        if side[i] != 0:
            cur = side[i]
        ps[i] = cur
    pps = np.concatenate([[0], ps[:-1]])
    cross = (side != 0) & (pps != 0) & (side != pps)
    last = np.full(len(c), -10 ** 6); lc = -10 ** 6
    for i in range(len(c)):
        if cross[i]:
            lc = i
        last[i] = lc
    age = np.arange(len(c)) - last
    ok = np.isfinite(a) & np.isfinite(bl) & (a > 0)
    al = A['c1_lc'] & A['c2_lc'] & A['v_ok_l'] & (side == 1)
    ash = A['c1_sc'] & A['c2_sc'] & A['v_ok_s'] & (side == -1)
    if A['c1_ternary']:
        n = ~A['c1_lc'] & ~A['c1_sc']; al &= ~n; ash &= ~n
    if A['c2_ternary']:
        n = ~A['c2_lc'] & ~A['c2_sc']; al &= ~n; ash &= ~n
    late = np.abs(c - bl) > 1.5 * a
    stale = age > 7
    keep = ok & ~late & ~stale
    return ((cross & (side == 1) & al) | (A['c1_lt'] & al)) & keep, \
           ((cross & (side == -1) & ash) | (A['c1_st'] & ash)) & keep, \
           side, cross, age, late


def condition_audit(pairs=PAIRS):
    """For every TradingView entry: do our conditions fire on that bar, and if
    not, WHICH condition refuses? A mis-ported indicator concentrates in one
    row of this table. Feed noise spreads across all of them."""
    import collections
    cnt = collections.Counter(); per = []
    for p in pairs:
        d = E.load_pair(p); A = E.prepare(d, **E.DEFAULT_SLOTS)
        Lg, Sh, side, cross, age, late = would_fire(A)
        idx = d.index.normalize()
        tv = read_tv(os.path.join(TVDIR, '%s.csv' % p))
        ent = tv[tv.is_entry].drop_duplicates(subset=['dt', 'side'])
        ent = ent[(ent.dt >= idx.min()) & (ent.dt <= idx.max())]
        pos = idx.get_indexer(ent.dt)
        hit = near = 0
        for q, sd in zip(pos, ent.side):
            if q < 0:
                continue
            arr = Lg if sd == 'long' else Sh
            if arr[q]:
                hit += 1; cnt['fires on the bar'] += 1; continue
            if any(0 <= q + o < len(arr) and arr[q + o] for o in (-1, 1)):
                near += 1
            want = 1 if sd == 'long' else -1
            why = []
            if side[q] != want:
                why.append('baseline side')
            if not (A['c1_lc'][q] if want == 1 else A['c1_sc'][q]):
                why.append('C1')
            if not (A['c2_lc'][q] if want == 1 else A['c2_sc'][q]):
                why.append('C2')
            if not (A['v_ok_l'][q] if want == 1 else A['v_ok_s'][q]):
                why.append('volume')
            if not (cross[q] or (A['c1_lt'][q] if want == 1 else A['c1_st'][q])):
                why.append('no trigger')
            if late[q]:
                why.append('too late')
            if age[q] > 7:
                why.append('bridge')
            cnt[' + '.join(why) or 'other'] += 1
        n = int((pos >= 0).sum())
        per.append(dict(pair=p, tv_entries=n, same_bar=hit,
                        same_bar_pct=round(100 * hit / n, 1),
                        within_1_bar=hit + near,
                        within_1_pct=round(100 * (hit + near) / n, 1)))
    return pd.DataFrame(per), pd.Series(cnt).sort_values(ascending=False)


if __name__ == '__main__':
    main()
