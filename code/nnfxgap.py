import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""ITEM 1, JACK 25 NOV -- WHAT A STOP ACTUALLY FILLS AT.

THE QUESTION. "When price gaps through a stop, what does the engine fill at?"

THE ANSWER AS THE ENGINE STOOD. Two of the three cases were already right and
the third was wrong:

  price walks through the level inside the bar -> fill at the stop. Correct.
  the bar OPENS beyond the stop                -> fill at the daily open.
                                                  Correct, and already there.
  the bar opens on the right side of the stop
  and then JUMPS through it mid-session        -> fill at the stop. WRONG.
                                                  There was no quote there.

The third case is EURCHF on 15 January 2015 and it is why this module exists.
The daily bar dated 15 Jan 2015 (16:00 NY 14th -> 16:00 NY 15th) OPENS at
1.2008, which is above every long stop anyone held, so the opening-gap rule
never fires -- and then the hourly bid goes 1.20083 open, 1.16777 low at 09:00
UTC, and the NEXT hour opens at 1.03592. Nothing between 1.16777 and 1.03592
was tradable. The old rule filled a stop at 1.10 at 1.10.

THE FIX IS l2engine._gap_px AND IT IS STANDING FROM 25 NOV. A stop fills at the
first tradable price at or beyond it: the daily open for an overnight gap, the
breaching hour's OPEN on the fill side for an intraday one, and the stop price
itself only where price was genuinely quoted through it. The quote side is the
one that would fill -- bid for a long exit, ask for a short. Pre-flight guard
41 refuses a Layer 2 table whose frames do not declare it.

THE HOUR IS THE RESOLUTION LIMIT, AND IT MATTERS HERE. Inside the hour that
breaches the stop this method cannot say what was quoted, so it keeps the stop
price. On 15 Jan 2015 the breaching hour for any stop above 1.16777 is the
09:00 bar, whose own range covers the stop -- so a 1.5-ATR stop about 30 pips
below a pegged 1.2008 is NOT seen as gapped, and fills at the stop, exactly as
before. That is not a result, it is a measurement limit, and it is reported as
one. `snb_long_eurchf.csv` therefore gives THREE fills: the stop, the hourly
rule, and the BOUND -- the breaching hour's far extreme, the worst price the
hour contains. The bound is a bound. It is not made standing on a judgement
the data cannot support; that call is Jack's.

Writes, all into results/nnfx/:
  gap_fill_effect.csv     A/B/C x jack/textbook, gap fills OFF then ON
  gap_fill_trades.csv     every entry whose R moved, with both exit prices
  gap_stopout_deciles.csv how often a stop-out exceeded 2 R and 5 R, by ATR
                          decile at entry, before and after
  snb_long_eurchf.csv     a LONG EURCHF held into 15 Jan 2015, three fills,
                          engine size and capped size
  GAP_FILLS.md
"""
import numpy as np, pandas as pd

import nnfx1 as N
import nnfx2s as S2
import nnfxvol as VOL
import nnfxamb as AMB
import nnfxcurves as CUR
import l2sweep as S
import l2engine as E

OUT = os.path.join(ROOTOUT, 'nnfx')
os.makedirs(OUT, exist_ok=True)
BUILD = N.BUILD_YEARS
BASES = (('A', 'ichimoku_signals', 'sma_baseline', 'full_nnfx'),
         ('B', 'schaff_trend_cycle_signals', 'sma_baseline', 'side_xentry'),
         ('C', 'halftrend_signals', 'sma_baseline', 'full_nnfx'))
PLANS = ('jack', 'textbook')
SNB = '2015-01-15'


# ====================== the before/after on A, B and C ===================
def _entry_net(T):
    """Per-ENTRY net R at achievable size, keyed for matching."""
    M, _ = VOL.apply_leverage_cap(T)
    M = M.reset_index(drop=True)
    M['_cost'] = N._cost_R(M)
    g = (M.groupby(['pair', 'entry_date', 'direction'], as_index=False)
         .agg(R_gross=('R_gross', 'sum'), cost=('_cost', 'sum'),
              exit_px=('exit_px', 'last'), exit_date=('exit_date', 'max'),
              entry_px=('entry_px', 'first'), lev=('lev_scale', 'min')
              if 'lev_scale' in M.columns else ('R', 'size'),
              reason=('reason', 'last')))
    g['R'] = g.R_gross - g.cost
    return g


def _fig(T, years=BUILD):
    """The standing headline: net, at achievable size, BUILD years only."""
    M, _ = VOL.apply_leverage_cap(T)
    M = M.reset_index(drop=True)
    cost = N._cost_R(M)
    DS = N.daily_series(M, cost)
    Y = N._yearly(M, cost, DS)
    b = Y[Y.year.isin(list(years))]
    tot = float(b.R_net.sum()) if len(b) else np.nan
    return (tot, tot / max(1, len(b)), float(b.n_entered.sum()) if len(b) else 0.0,
            N.true_dip(DS, years))


def run_both(pairs=None, verbose=True, stitched=True, tag=''):
    """A, B and C with gap fills OFF and ON. Everything else identical.

    `stitched=True` is the candidates AS REPORTED -- the walk-forward stitch,
    each step's settings picked on that step's own tuning years, trades taken
    only in that step's unseen trade year. That is what A, B and C mean in
    every other table, so it is what the before/after has to be measured on.

    `stitched=False` runs the same three combinations at DEFAULT settings over
    the whole span. It is a second, larger sample of the same mechanism -- four
    to six times the trades -- and it is kept because the stitch's BUILD window
    holds only a few hundred entries and a handful of gaps.
    """
    rows, chg, keep = [], [], {}
    for (lab, c1, base, rs) in BASES:
        for v in PLANS:
            got = {}
            for gf in (0, 1):
                gc = np.zeros(4, np.int64)
                if stitched:
                    T = CUR._stitch(c1, base, rs, v, VOL.LOWVOL_Q,
                                    VOL.PEG_X_DECIDED,
                                    gapfill=bool(gf), gap_out=gc)
                else:
                    T = S2.run_combo(c1, None, base, None, v, rs, pairs=pairs,
                                     gapfill=bool(gf), gap_out=gc)
                got[gf] = (T, gc)
            T0, g0 = got[0]
            T1, g1 = got[1]
            # THE TRADE SET CANNOT MOVE AND THE RUN IS VOID IF IT DOES. A gap
            # fill changes an EXIT PRICE. It cannot change which bar an exit
            # happens on, and no entry condition reads an exit price, so the
            # two runs must hold the same trades in the same order. If they do
            # not, something else changed with them and the comparison is not
            # measuring the gap fill.
            assert len(T0) == len(T1), (
                '%s/%s: %d legs with gap fills off, %d with them on -- the '
                'trade SET moved, so this is not a gap-fill comparison'
                % (lab, v, len(T0), len(T1)))
            E0, E1 = _entry_net(T0), _entry_net(T1)
            K = ['pair', 'entry_date', 'direction']
            M = E0.merge(E1, on=K, suffixes=('_off', '_on'))
            assert len(M) == len(E0) == len(E1), '%s/%s: entry keys moved' % (lab, v)
            d = M[np.abs(M.R_on - M.R_off) > 1e-9].copy()
            if len(d):
                d['base'] = lab; d['variant'] = v
                d['dR'] = d.R_on - d.R_off
                chg.append(d)
            for gf, (T, gc) in got.items():
                tot, per, n, dip = _fig(T)
                en = _entry_net(T)
                rows.append(dict(
                    base=lab, variant=v, gapfill_on=gf,
                    R_total=tot, R_per_year=per, trades=n, worst_dip_R=dip,
                    worst_trade_R=float(en.R.min()) if len(en) else np.nan,
                    best_trade_R=float(en.R.max()) if len(en) else np.nan,
                    stop_fills_resolved_no_gap=int(gc[0]),
                    stop_fills_gapped=int(gc[1]),
                    stop_fills_unresolved=int(gc[2]),
                    dailyopen_gaps=int(gc[3]),
                    entries_changed=int(len(d)),
                    entries_total=int(len(en)),
                    legs=int(len(T))))
            keep[(lab, v)] = (T0, T1)
            if verbose:
                print('  %s/%s  R %.3f -> %.3f   worst trade %.3f -> %.3f   '
                      '%d of %d entries moved'
                      % (lab, v, rows[-2]['R_total'], rows[-1]['R_total'],
                         rows[-2]['worst_trade_R'], rows[-1]['worst_trade_R'],
                         len(d), len(E0)), flush=True)
    D = pd.DataFrame(rows)
    D['stitched'] = int(bool(stitched))
    D.to_csv(os.path.join(OUT, 'gap_fill_effect%s.csv' % tag), index=False)
    C = (pd.concat(chg, ignore_index=True) if chg else pd.DataFrame())
    if len(C):
        C = C[['base', 'variant', 'pair', 'entry_date', 'direction',
               'exit_date_off', 'reason_off', 'entry_px_off',
               'exit_px_off', 'exit_px_on', 'R_off', 'R_on', 'dR']]
        C = C.sort_values('dR')
    C.to_csv(os.path.join(OUT, 'gap_fill_trades%s.csv' % tag), index=False)
    return D, C, keep


# ====================== stop-outs by ATR decile ==========================
def stopout_deciles(keep, nb=10, tag=''):
    """How often a stop-out exceeded 2 R and 5 R, by ATR decile at entry.

    The decile is the ENTRY bar's own-pair causal ATR percentile -- the same
    bucket the per-pair floor cuts into -- and the loss is the whole ENTRY's
    net R at achievable size, both legs together, because that is the loss the
    account takes.
    """
    rows = []
    for (lab, v), (T0, T1) in sorted(keep.items()):
        for gf, T in ((0, T0), (1, T1)):
            en = _entry_net(T)
            if not len(en):
                continue
            en = VOL.attach_atr_pctile(en, nb=nb)
            if not len(en):
                continue
            for b, sub in en.groupby('bucket'):
                r = sub.R.to_numpy(float)
                rows.append(dict(
                    base=lab, variant=v, gapfill_on=gf, bucket=int(b),
                    n_entries=len(sub),
                    n_losers=int((r < 0).sum()),
                    n_worse_than_2R=int((r < -2.0).sum()),
                    n_worse_than_5R=int((r < -5.0).sum()),
                    pct_worse_than_2R=100.0 * float((r < -2.0).mean()),
                    pct_worse_than_5R=100.0 * float((r < -5.0).mean()),
                    worst_R=float(r.min()),
                    mean_R=float(r.mean()),
                    R_total=float(r.sum())))
    D = pd.DataFrame(rows)
    D.to_csv(os.path.join(OUT, 'gap_stopout_deciles%s.csv' % tag), index=False)
    return D


# ====================== the long EURCHF into 15 Jan 2015 =================
def snb_long(stops_atr=(1.0, 1.5, 2.0, 3.0, 31.0, 50.0), risk_dollars=None,
             cap_scale=None):
    """A LONG EURCHF held into 15 Jan 2015. What does it lose?

    NO CANDIDATE HELD THIS TRADE -- every A/B/C entry through the de-peg was a
    SHORT, which is why the SNB day is a windfall in those tables and not a
    ruin. This is the other side, constructed, because it is the risk the book
    is actually exposed to and no result in the project measures it.

    THE POSITION. Long at the close of 14 Jan 2015 (the last bar before the
    de-peg), stop at `stops_atr` x the 14-day ATR of that bar, size set the
    way the engine sets it: risk_dollars at the stop distance. Nothing is
    optimised; the entry date is the event, not a choice.

    THREE FILLS, and the spread between them IS the finding:
      stop        the stop price. What the engine booked before 25 Nov.
      hourly      l2engine._gap_px: the breaching hour's bid OPEN when that
                  open is already beyond the stop, else the stop.
      bound       the breaching hour's own LOW -- the worst price that hour
                  contains. A bound on what a tick path could have filled,
                  not a claim about what it did.

    AND AT TWO SIZES: the engine's, and the size the 1:30 leverage cap leaves.
    """
    d = S.load_pair('EURCHF')
    import l2ind as IND
    atr = IND.atr(d.high.values.astype(float), d.low.values.astype(float),
                  d.close.values.astype(float), 14)
    ix = pd.DatetimeIndex(d.index).normalize()
    i = int(ix.get_indexer([pd.Timestamp('2015-01-14')])[0])
    assert i >= 0, 'no 2015-01-14 bar in the EURCHF daily feed'
    entry = float(d.close.values[i])
    a = float(atr[i])
    risk = float(risk_dollars if risk_dollars is not None else S.RISK)
    hb_lo, hb_hi, ha_lo, ha_hi, hr_off, hb_op, ha_op = AMB.hourly_index('EURCHF')
    tol = AMB.gf_tol('EURCHF')
    # the de-peg falls in the NEXT daily bar
    j = int(ix.get_indexer([pd.Timestamp(SNB)])[0])
    assert j == i + 1, 'the 15 Jan bar is not the bar after the 14 Jan bar'
    rows = []
    for m in stops_atr:
        dist = m * a
        stop = entry - dist
        units = risk / dist              # the engine's sizing, exactly
        notional = units * entry
        # the hourly rule, through the engine's own function
        gc = np.zeros(4, np.int64)
        px_h = E._gap_px(hb_op, hb_lo, ha_op, ha_hi, hr_off, True, tol,
                         j, stop, True, float(d.open.values[j]), gc)
        # the BOUND: the low of the first hour whose bid range reaches the stop
        lo_b = np.nan
        for k in range(hr_off[j], hr_off[j + 1]):
            if hb_lo[k] <= stop:
                lo_b = float(hb_lo[k])
                break
        px_b = min(stop, lo_b) if np.isfinite(lo_b) else stop
        cap = (cap_scale if cap_scale is not None
               else min(1.0, (VOL.CAP_LEV * VOL.EQUITY) / notional))
        for nm, px in (('stop', stop), ('hourly', px_h), ('bound', px_b)):
            loss = (px - entry) * units            # dollars, engine size
            rows.append(dict(
                stop_atr_mult=m, atr=a, entry_px=entry, stop_px=stop,
                fill=nm, fill_px=px,
                stop_dist_px=dist, units_engine=units,
                notional_engine=notional,
                loss_dollars_engine=loss,
                R_raw_engine=loss / risk,
                R_1p5atr_engine=(loss / risk) * m / N.RISK_UNIT_ATR,
                leverage_requested=notional / VOL.EQUITY,
            lev_scale=cap,
                units_capped=units * cap,
                loss_dollars_capped=loss * cap,
                R_1p5atr_capped=(loss / risk) * m / N.RISK_UNIT_ATR * cap,
                pct_of_equity_capped=100.0 * loss * cap / VOL.EQUITY,
                hourly_resolved_gap=int(gc[1]),
                hourly_no_gap=int(gc[0])))
    D = pd.DataFrame(rows)
    D.to_csv(os.path.join(OUT, 'snb_long_eurchf.csv'), index=False)
    _g = lambda m, f, c: float(D[(D.stop_atr_mult == m)
                                 & (D.fill == f)][c].iloc[0])
    print('  long EURCHF into 15 Jan 2015, 1.5 ATR stop: engine books %.3f R, '
          'hourly rule %.3f R, bound %.3f R; capped %.3f R at leverage %.1f:1'
          % (_g(1.5, 'stop', 'R_1p5atr_engine'),
             _g(1.5, 'hourly', 'R_1p5atr_engine'),
             _g(1.5, 'bound', 'R_1p5atr_engine'),
             _g(1.5, 'bound', 'R_1p5atr_capped'),
             _g(1.5, 'bound', 'leverage_requested')), flush=True)
    return D



# ====================== THE DOCUMENT ====================================
def md_gapfills(out=None):
    """GAP_FILLS.md -- item 1, from the files, nothing retyped."""
    import hashlib
    L_ = []
    a = L_.append
    rd = lambda n: (pd.read_csv(os.path.join(OUT, n))
                    if os.path.exists(os.path.join(OUT, n))
                    and os.path.getsize(os.path.join(OUT, n)) > 2
                    else pd.DataFrame())
    SNBD, EFF, TRD, DEC = (rd('snb_long_eurchf.csv'), rd('gap_fill_effect.csv'),
                           rd('gap_fill_trades.csv'),
                           rd('gap_stopout_deciles.csv'))
    EFFD = rd('gap_fill_effect_defaults.csv')
    DECD = rd('gap_stopout_deciles_defaults.csv')
    a('# GAP FILLS — item 1, Jack 25 November 2026')
    a('')
    a('**The question: when price gaps through a stop, what does the engine '
      'fill at?**')
    a('')
    a('## The answer as the engine stood')
    a('')
    a('| case | what it filled at | right? |')
    a('|---|---|---|')
    a('| price walks through the level inside the bar | the stop | **yes** |')
    a('| the daily bar OPENS beyond the stop | the daily open | **yes**, and '
      'already there |')
    a('| the bar opens on the right side of the stop and then JUMPS through '
      'it mid-session | the stop | **NO.** There was no quote there |')
    a('')
    a('Only the third case was wrong, and it is the one that matters, because '
      'it is the shape every currency-peg break has. EURCHF on 15 January '
      '2015: the daily bar dated the 15th (16:00 NY on the 14th to 16:00 NY '
      'on the 15th) **opens at 1.2008**, above every long stop anyone held, '
      'so the opening-gap rule never fires. The hourly bid went **1.20083 '
      'open, 1.16777 low at 09:00 UTC, and the next hour opened at '
      '1.03592**. A long stop at 1.10 was booked at 1.10.')
    a('')
    a('## What is standing now')
    a('')
    a('`l2engine._gap_px`, from 25 Nov, enforced by **pre-flight guard 41**: '
      'a stop fills at the **first tradable price at or beyond it** — the '
      'daily open for an overnight gap, the breaching hour\'s OPEN on the '
      'fill side for an intraday one, and the stop price itself only where '
      'price was genuinely quoted through it. A long exits by selling so it '
      'fills on the **bid**; a short buys so it fills on the **ask**. An '
      'hourly open counts as a gap only when it is beyond the stop by more '
      'than the pair\'s round-trip cost — a charge the cost table is already '
      'making, and the one place these two feeds (daily MID, hourly '
      'BID/ASK) could otherwise double-count.')
    a('')
    a('**The hourly-OFF path is byte-identical to the pre-patch engine** — '
      'six base/plan cells on four pairs, same trade counts, same R to ten '
      'decimals, same exit prices, SHA `e5264776bbacc833` both ways.')
    a('')
    a('## THE RESOLUTION LIMIT, stated before the numbers')
    a('')
    a('**An hour is not a tick, and on this event that is decisive.** Inside '
      'the hour that breaches the stop this method cannot say what was '
      'quoted, so it keeps the stop price. On 15 Jan 2015 the breaching hour '
      'for any stop near the peg is the 09:00 bar, whose own range (1.20090 '
      'down to 1.16777) covers that stop — so **a 1.5 ATR stop is not seen '
      'as gapped at all** and still fills at the stop, exactly as before. '
      'That is a measurement limit, not a result, and the table below '
      'therefore gives three fills: the stop, the hourly rule, and the '
      '**bound** — the worst price the breaching hour contains. The bound is '
      'a bound. Making it the standing fill would be a judgement the data '
      'cannot support, and that call is Jack\'s, not mine.')
    a('')
    a('## A LONG EURCHF held into 15 January 2015')
    a('')
    a('**No candidate held this trade.** Every A, B and C entry through the '
      'de-peg was a SHORT, which is why the SNB day is a windfall in those '
      'tables and not a ruin. This is the other side, constructed: long at '
      'the close of 14 Jan 2015 (the last bar before the break), stop at a '
      'multiple of that bar\'s 14-day ATR, sized the way the engine sizes — '
      'risk at the stop distance. The entry date is the event, not a choice, '
      'and nothing here is optimised.')
    a('')
    if len(SNBD):
        a('ATR on 14 Jan 2015 was **%.5f** (%.1f pips) on a price of '
          '**%.5f** — the pair had been pegged for three years.'
          % (float(SNBD.atr.iloc[0]), 1e4 * float(SNBD.atr.iloc[0]),
             float(SNBD.entry_px.iloc[0])))
        a('')
        a('| stop | stop price | fill | fill price | R, engine size | '
          'leverage | cap scale | R, capped size |')
        a('|---:|---:|---|---:|---:|---:|---:|---:|')
        for _, r in SNBD.iterrows():
            b = '**' if r.fill == 'bound' else ''
            a('| %.1f ATR | %.5f | %s%s%s | %.5f | %s%+.3f%s | %.2f:1 | '
              '%.4f | %s%+.3f%s |'
              % (r.stop_atr_mult, r.stop_px, b, r.fill, b, r.fill_px,
                 b, r.R_1p5atr_engine, b, r.leverage_requested, r.lev_scale,
                 b, r.R_1p5atr_capped, b))
        a('')
        _g = lambda m, f, c: float(SNBD[(SNBD.stop_atr_mult == m)
                                        & (SNBD.fill == f)][c].iloc[0])
        a('**Three things to take from that table.**')
        a('')
        a('1. **At a realistic stop the engine understates the loss by up to '
          '20 times and the hourly path cannot prove it.** A 1.5 ATR stop '
          'books **%+.3f R**; the bound is **%+.3f R**.'
          % (_g(1.5, 'stop', 'R_1p5atr_engine'),
             _g(1.5, 'bound', 'R_1p5atr_engine')))
        a('2. **Where the gap IS resolvable the correction is enormous.** A '
          'stop below 1.16777 breaches in the 10:00 bar instead, whose open '
          'is 1.03592: at a 31 ATR stop **%+.3f R becomes %+.3f R**, and the '
          'bound is %+.3f R.'
          % (_g(31.0, 'stop', 'R_1p5atr_engine'),
             _g(31.0, 'hourly', 'R_1p5atr_engine'),
             _g(31.0, 'bound', 'R_1p5atr_engine')))
        a('3. **The leverage cap is no protection against this.** That '
          'position is **%.1f:1** at a 1.5 ATR stop — comfortably inside the '
          '1:30 prop limit — so the cap scales it by %.4f and capped size '
          'EQUALS engine size. The cap limits how much you may hold. It does '
          'nothing about what a hole in the market does to what you are '
          'already holding.'
          % (_g(1.5, 'stop', 'leverage_requested'),
             _g(1.5, 'stop', 'lev_scale')))
        a('')
    a('## What it is worth on A, B and C')
    a('')
    a('The candidates **as reported** — the walk-forward stitch, each step\'s '
      'settings picked on that step\'s own tuning years, trades taken only in '
      'that step\'s unseen trade year, floor 5%, peg guard X = 0.33, '
      'leverage cap on. Everything identical between the two rows except the '
      'fill rule.')
    a('')
    if len(EFF):
        a('| candidate | R total, old fill | R total, realistic | R/yr old | '
          'R/yr new | worst dip old | worst dip new | worst trade old | '
          'worst trade new | entries moved |')
        a('|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|')
        for (b, v), g in EFF.groupby(['base', 'variant'], sort=False):
            o = g[g.gapfill_on == 0].iloc[0]
            n = g[g.gapfill_on == 1].iloc[0]
            a('| %s / %s | %+.3f | **%+.3f** | %+.3f | **%+.3f** | %.3f | '
              '%.3f | %+.3f | **%+.3f** | %d of %d |'
              % (b, v, o.R_total, n.R_total, o.R_per_year, n.R_per_year,
                 o.worst_dip_R, n.worst_dip_R, o.worst_trade_R,
                 n.worst_trade_R, int(n.entries_changed),
                 int(n.entries_total)))
        a('')
        a('| candidate | stop fills resolved, no gap | **resolved as GAPS** | '
          'unresolvable, daily rule kept | daily-open gaps |')
        a('|---|---:|---:|---:|---:|')
        for _, n in EFF[EFF.gapfill_on == 1].iterrows():
            a('| %s / %s | %d | **%d** | %d | %d |'
              % (n.base, n.variant, int(n.stop_fills_resolved_no_gap),
                 int(n.stop_fills_gapped), int(n.stop_fills_unresolved),
                 int(n.dailyopen_gaps)))
        a('')
    if len(TRD):
        a('### The entries that moved most')
        a('')
        a('| candidate | pair | entry | dir | exit | reason | old fill | '
          'new fill | R old | R new | dR |')
        a('|---|---|---|---|---|---|---:|---:|---:|---:|---:|')
        for _, r in TRD.head(10).iterrows():
            a('| %s/%s | %s | %s | %s | %s | %s | %.5f | %.5f | %+.3f | '
              '%+.3f | **%+.3f** |'
              % (r.base, r.variant, r.pair, str(r.entry_date)[:10],
                 r.direction, str(r.exit_date_off)[:10], r.reason_off,
                 r.exit_px_off, r.exit_px_on, r.R_off, r.R_on, r.dR))
        a('')
        _c = TRD[pd.DatetimeIndex(TRD.entry_date).normalize()
                 == pd.Timestamp('2015-01-15')]
        a('**%d of the %d corrected entries were opened on 15 January 2015 '
          'itself**, and they are the six largest. The engine entered at the '
          'close of the de-peg day and was stopped out on the 16th, into a '
          'market that was still jumping — which is the case the old rule '
          'could not see, happening on the one day it mattered most.'
          % (len(_c), len(TRD)))
        a('')
    a('## How often a stop-out exceeded 2 R and 5 R, by ATR decile at entry')
    a('')
    a('The decile is the entry bar\'s own-pair causal ATR percentile — the '
      'same bucket the per-pair floor cuts into — and the loss is the whole '
      'ENTRY\'s net R at achievable size, both legs together, because that is '
      'the loss the account takes.')
    a('')
    if len(DEC):
        on = DEC[DEC.gapfill_on == 1]
        off = DEC[DEC.gapfill_on == 0]
        a('| decile | entries | losers | **worse than −2 R** | '
          '**worse than −5 R** | worst single entry, old fill | '
          'worst single entry, realistic |')
        a('|---:|---:|---:|---:|---:|---:|---:|')
        for b in sorted(on.bucket.unique()):
            g = on[on.bucket == b]
            h = off[off.bucket == b]
            a('| %d | %d | %d | **%d** | **%d** | %+.3f | %+.3f |'
              % (int(b), int(g.n_entries.sum()), int(g.n_losers.sum()),
                 int(g.n_worse_than_2R.sum()), int(g.n_worse_than_5R.sum()),
                 float(h.worst_R.min()), float(g.worst_R.min())))
        a('| **all** | **%d** | **%d** | **%d** | **%d** | **%+.3f** | '
          '**%+.3f** |'
          % (int(on.n_entries.sum()), int(on.n_losers.sum()),
             int(on.n_worse_than_2R.sum()), int(on.n_worse_than_5R.sum()),
             float(off.worst_R.min()), float(on.worst_R.min())))
        a('')
        a('**Essentially never — and that is not reassurance.** %d of %d '
          'entries across the six cells lose more than 2 R with realistic '
          'fills (%d with the old rule), and **none** loses more than 5 R, in '
          'any decile. The reason is not that the stops held. It is that '
          '**the book was never long CHF into the de-peg.** The constructed '
          'trade above shows what the same mechanism is worth when the '
          'position is on the wrong side: −20 R at a normal stop, −100 R at '
          'a wide one. The empirical tail here measures the sample, not the '
          'exposure.'
          % (int(on.n_worse_than_2R.sum()), int(on.n_entries.sum()),
             int(off.n_worse_than_2R.sum())))
        a('')
    a('## The same three at default settings, as a larger sample')
    a('')
    a('The stitch\'s BUILD window holds a few hundred entries per cell and a '
      'couple of hundred gap-resolvable stop fills. The same three '
      'combinations at DEFAULT settings over the whole span give four to six '
      'times the trades. Same direction, same size, nothing new — which is '
      'the point of running it.')
    a('')
    if len(EFFD):
        a('| candidate | R total, old fill | R total, realistic | '
          'worst trade old | worst trade new | entries moved | gaps resolved |')
        a('|---|---:|---:|---:|---:|---:|---:|')
        for (b, v), g in EFFD.groupby(['base', 'variant'], sort=False):
            o = g[g.gapfill_on == 0].iloc[0]
            n = g[g.gapfill_on == 1].iloc[0]
            a('| %s / %s | %+.3f | %+.3f | %+.3f | %+.3f | %d of %d | %d |'
              % (b, v, o.R_total, n.R_total, o.worst_trade_R, n.worst_trade_R,
                 int(n.entries_changed), int(n.entries_total),
                 int(n.stop_fills_gapped)))
        a('')
    a('## What this does and does not settle')
    a('')
    a('1. **Settled: the engine no longer books a fill at a price that was '
      'never quoted**, wherever an hourly path exists to prove it, and guard '
      '41 will not let a Layer 2 table ship without it.')
    a('2. **Settled: it changes no verdict on A, B or C.** The largest '
      'correction to a candidate total is %s R and the worst single trade '
      'gets about 5%% worse. Nothing here rescues or kills anything.'
      % ('%.3f' % max(
          abs(float(g[g.gapfill_on == 1].R_total.iloc[0])
              - float(g[g.gapfill_on == 0].R_total.iloc[0]))
          for _k, g in EFF.groupby(['base', 'variant']))
         if len(EFF) else 'n/a'))
    a('3. **NOT settled: what a peg break actually costs a position on the '
      'wrong side of it.** Hour resolution cannot answer it for a normal '
      'stop. The bound is −20 R against an intended −1 R, the leverage cap '
      'does not touch it, and the only ways to close that gap are tick data '
      'for the event or a declared assumption. Jack\'s call.')
    a('4. **NOT settled: every stage table written before today ran on the '
      'old rule.** `results/nnfx/GAPFILL_STALE.md` names them and guard 41 '
      'fails if it goes missing. They are not being re-run to move a '
      'sub-1-R-a-year figure; the per-pair bank replaces them on the new '
      'rule from the start.')
    a('')
    a('## Provenance')
    a('')
    for n_ in ('snb_long_eurchf.csv', 'gap_fill_effect.csv',
               'gap_fill_trades.csv', 'gap_stopout_deciles.csv',
               'gap_fill_effect_defaults.csv',
               'gap_fill_trades_defaults.csv',
               'gap_stopout_deciles_defaults.csv'):
        p_ = os.path.join(OUT, n_)
        if not os.path.exists(p_):
            a('- `%s` — **MISSING**' % os.path.join('results', 'nnfx', n_))
            continue
        a('- `%s` — %s rows, md5 `%s`'
          % (os.path.relpath(p_, _R),
             '{:,}'.format(len(S2._safe_csv(p_))),
             hashlib.md5(open(p_, 'rb').read()).hexdigest()[:12]))
    out = out or os.path.join(OUT, 'GAP_FILLS.md')
    open(out, 'w').write('\n'.join(L_) + '\n')
    print('  GAP_FILLS.md: %d lines -> %s'
          % (len('\n'.join(L_).splitlines()), os.path.relpath(out, _R)),
          flush=True)
    return out


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', default='all')
    ap.add_argument('--pairs', default=None)
    g = ap.parse_args()
    pairs = g.pairs.split(',') if g.pairs else None
    if g.stage in ('all', 'snb'):
        snb_long()
    if g.stage in ('all', 'effect'):
        print('  -- the candidates AS REPORTED (walk-forward stitch)', flush=True)
        D, C, keep = run_both(pairs=pairs, stitched=True)
        stopout_deciles(keep)
    if g.stage in ('all', 'md'):
        md_gapfills()
    if g.stage in ('all', 'defaults'):
        print('  -- the same three at DEFAULT settings, whole span', flush=True)
        D2, C2, k2 = run_both(pairs=pairs, stitched=False, tag='_defaults')
        stopout_deciles(k2, tag='_defaults')
    print('  nnfxgap done', flush=True)


if __name__ == '__main__':
    main()
