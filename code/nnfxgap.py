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
    if g.stage in ('all', 'defaults'):
        print('  -- the same three at DEFAULT settings, whole span', flush=True)
        D2, C2, k2 = run_both(pairs=pairs, stitched=False, tag='_defaults')
        stopout_deciles(k2, tag='_defaults')
    print('  nnfxgap done', flush=True)


if __name__ == '__main__':
    main()
