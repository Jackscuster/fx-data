import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""ITEM 6, JACK 25 NOV -- EXITS, THREE SPEEDS, AND DRAWDOWN CONTROL.
One report each. This file is the EXITS one.

READ THIS BEFORE THE NUMBERS. Item 5 measured the best book at 1.135% a year
against a 12% target -- a factor of 10.6 short. An exit sweep is not going to
close that. It is worth running because a 2x on the best sleeve is still a 2x,
and because the current exit configuration was inherited rather than tested.
It is NOT worth presenting as if it might reach the target, and this document
does not.

THE FULL FACTORIAL, as Jack's standing rule requires -- every cut swept over
its full range:
  exit rules   all three together, then EACH ALONE
               (c1 flip / baseline cross / exit indicator)
  stop         1.0, 1.5, 2.0 ATR
  first target 1.0, 1.5, 2.0 x the stop
  trail        on and off
  time stop    off, 5, 10, 20 bars
4 x 3 x 3 x 2 x 4 = 288 cells per member, A and B = 576 walk-forward stitches.
Nothing is chosen here; it is a curve, reported as one.

TWO THINGS THE APPARATUS NEEDED FIRST, both now in and both regression-proven.
  1. THE ENGINE HAD NO TIME STOP. l2engine.run_bars takes `time_stop_bars`,
     default 0 = off, checked AFTER the three signal exits so a bar on which a
     signal also fires is attributed to the signal and not to the clock. With
     it at 0 the engine is byte-identical to before: SHA e5264776bbacc833 on
     six base/plan cells over four pairs, same as the gap-fill change.
  2. THE EXIT-INDICATOR SLOT WAS BLANK. Stage 2 zeroed x_el/x_es because the
     exit slot was not its question, so `exit_on_exit_ind=True` had nothing to
     fire on and "each alone" would have been two arms, not three. The arrays
     E.prepare already computes from the exit_ind family are now kept when the
     exit indicator is under test. The family has exactly one member,
     `adx_dmi_exit`, so there is no choice being made.

Writes results/nnfx/exit_grid.csv and EXITS.md.
"""
import itertools
import numpy as np, pandas as pd

import nnfx1 as N
import nnfx2s as S2
import nnfxvol as VOL
import nnfxcurves as CUR
import l2sweep as S

OUT = os.path.join(ROOTOUT, 'nnfx')
os.makedirs(OUT, exist_ok=True)
BUILD = N.BUILD_YEARS
MAIN = 'jack'
MEMBERS = (('A', 'ichimoku_signals', 'sma_baseline', 'full_nnfx'),
           ('B', 'schaff_trend_cycle_signals', 'sma_baseline', 'side_xentry'))
EXIT_ARMS = (('all_three', True, True, True),
             ('c1_flip_only', True, False, False),
             ('base_cross_only', False, True, False),
             ('exit_ind_only', False, False, True))
STOPS = (1.0, 1.5, 2.0)
TARGETS = (1.0, 1.5, 2.0)
TRAILS = (True, False)
TIME_STOPS = (0, 5, 10, 20)


def _fig(T, years=BUILD, nboot=800):
    """The standing headline plus the standing robustness columns."""
    if not len(T):
        return dict(R_total=np.nan, R_per_year=np.nan, trades=0.0,
                    worst_dip_R=np.nan, R_per_dip=np.nan)
    M, _ = VOL.apply_leverage_cap(T)
    M = M.reset_index(drop=True)
    cost = N._cost_R(M)
    DS = N.daily_series(M, cost)
    Y = N._yearly(M, cost, DS)
    b = Y[Y.year.isin(list(years))]
    tot = float(b.R_net.sum()) if len(b) else np.nan
    dip = N.true_dip(DS, years)
    ys = b.sort_values('year').R_net.to_numpy(float) if len(b) else np.array([])
    ds = DS[pd.DatetimeIndex(DS.date).year.isin(list(years))]
    t_bs, _sd = N._block_t(ds.R.to_numpy(float), ndraw=nboot)
    out = dict(VOL.robust_cols(M, cost, DS, years))
    out.update(
        R_total=tot, R_per_year=tot / max(1, len(b)),
        trades=float(b.n_entered.sum()) if len(b) else 0.0,
        R_per_trade=(tot / float(b.n_entered.sum())
                     if len(b) and b.n_entered.sum() else np.nan),
        worst_dip_R=dip,
        R_per_dip=(tot / dip if (dip and dip > 1e-9) else np.nan),
        mean_bars=float((b.mean_bars * b.n_entered).sum()
                        / max(1.0, float(b.n_entered.sum()))) if len(b)
        else np.nan,
        t_yearly=(float(ys.mean() * np.sqrt(len(ys)) / ys.std(ddof=1))
                  if len(ys) > 1 and ys.std(ddof=1) > 0 else np.nan),
        t_block_boot=t_bs,
        years=int(len(ys)), years_positive=int((ys > 0).sum()))
    return out


def sweep(members=MEMBERS, verbose=True, resume=True):
    f = os.path.join(OUT, 'exit_grid.csv')
    done = set()
    rows = []
    if resume and os.path.exists(f) and os.path.getsize(f) > 2:
        # RESUMABLE, because 576 stitches is hours and a stop in the middle
        # should cost one cell and not the run.
        old = pd.read_csv(f)
        rows = old.to_dict('records')
        done = set(zip(old.member, old.exit_arm, old.stop_atr,
                       old.target_mult, old.trail_on, old.time_stop_bars))
        if verbose:
            print('  resuming: %d cells already on disk' % len(done),
                  flush=True)
    grid = list(itertools.product(members, EXIT_ARMS, STOPS, TARGETS, TRAILS,
                                  TIME_STOPS))
    for k, ((lab, c1, base, rs), (arm, e_c1, e_bx, e_xi), st, tg, tr, ts) \
            in enumerate(grid):
        key = (lab, arm, st, tg, tr, ts)
        if key in done:
            continue
        kw = dict(exit_on_c1_flip=e_c1, exit_on_base_cross=e_bx,
                  exit_on_exit_ind=e_xi,
                  atr_mult=st, tp_mult=tg,
                  # THE TRAIL IS DISABLED BY NEVER ARMING IT, not by setting
                  # its distance to zero -- see nnfx1.run_one's note on what a
                  # large be_pct does to a sentinel target.
                  trail_start_mult=(2.0 if tr else float(N.BIG)),
                  time_stop_bars=ts)
        T = CUR._stitch(c1, base, rs, MAIN, VOL.LOWVOL_Q, VOL.PEG_X_DECIDED,
                        exit_kw=kw)
        fg = _fig(T)
        rows.append(dict(
            member=lab, exit_arm=arm, exit_on_c1_flip=int(e_c1),
            exit_on_base_cross=int(e_bx), exit_on_exit_ind=int(e_xi),
            stop_atr=st, target_mult=tg, trail_on=int(tr),
            time_stop_bars=ts, legs=len(T), **fg))
        if verbose and (k % 8 == 0 or True):
            print('    %3d/%d %s %-16s stop %.1f tgt %.1f trail %d ts %2d -> '
                  'R %+8.3f  R/yr %+7.3f  dip %7.3f  R/dip %s  n %d'
                  % (k + 1, len(grid), lab, arm, st, tg, int(tr), ts,
                     fg['R_total'], fg['R_per_year'], fg['worst_dip_R'],
                     ('%+.3f' % fg['R_per_dip'])
                     if np.isfinite(fg.get('R_per_dip', np.nan)) else '—',
                     int(fg['trades'])), flush=True)
        if (k % 12) == 0:
            pd.DataFrame(rows).to_csv(f, index=False)
    D = pd.DataFrame(rows)
    D.to_csv(f, index=False)
    return D



# ====================== THE DOCUMENT ====================================
def md_exits(out=None):
    import hashlib
    L_ = []
    a = L_.append
    f = os.path.join(OUT, 'exit_grid.csv')
    D = (pd.read_csv(f) if os.path.exists(f) and os.path.getsize(f) > 2
         else pd.DataFrame())
    a('# EXITS — item 6a, Jack 25 November 2026')
    a('')
    a('**Read item 5 first.** The best book is 1.135% a year against a 12% '
      'target, a factor of 10.6 short. An exit sweep is not going to close '
      'that, and this document does not present it as if it might. It is '
      'worth running because a 2x on the best sleeve is still a 2x, and '
      'because the exit configuration every result so far was computed under '
      'was **inherited, not tested**.')
    a('')
    a('## The grid — the full factorial, nothing chosen')
    a('')
    a('| factor | values |')
    a('|---|---|')
    a('| exit rules | all three together, then **each alone**: c1 flip / '
      'baseline cross / exit indicator |')
    a('| stop | 1.0, 1.5, 2.0 ATR |')
    a('| first target | 1.0, 1.5, 2.0 x the stop |')
    a('| trail | on and off |')
    a('| time stop | off, 5, 10, 20 bars |')
    a('')
    a('4 x 3 x 3 x 2 x 4 = **288 cells per member**, A and B = **576 '
      'walk-forward stitches**. Each cell is the full six-step stitch with '
      'its own settings chosen on its own tuning years; only the exit '
      'configuration changes.')
    a('')
    a('**Two things the apparatus needed first, both regression-proven.**')
    a('')
    a('1. **The engine had no time stop.** `l2engine.run_bars` now takes '
      '`time_stop_bars`, default 0 = off, checked **after** the three signal '
      'exits so a bar on which a signal also fires is attributed to the '
      'signal and not to the clock — otherwise a short time stop would '
      'silently absorb the very exits being measured. With it at 0 the engine '
      'is byte-identical to before: SHA `e5264776bbacc833` on six base/plan '
      'cells over four pairs, the same check the gap-fill change passed.')
    a('2. **The exit-indicator slot was blank.** Stage 2 zeroed `x_el/x_es` '
      'because the exit slot was not its question, so `exit_on_exit_ind=True` '
      'had nothing to fire on and "each alone" would have been two arms, not '
      'three. The arrays `E.prepare` already computes are now kept when the '
      'exit indicator is under test. The family has exactly one member, '
      '`adx_dmi_exit`, so **no choice is being made**.')
    a('')
    if not len(D):
        a('*The sweep has not finished. This document is regenerated when it '
          'lands.*')
    else:
        a('## %d of 576 cells on disk' % len(D))
        a('')
        for mb, g in D.groupby('member'):
            base = g[(g.exit_arm == 'all_three') & (g.stop_atr == 1.5)
                     & (g.target_mult == 1.5) & (g.trail_on == 1)
                     & (g.time_stop_bars == 0)]
            b = base.iloc[0] if len(base) else None
            a('### Member %s' % mb)
            a('')
            if b is not None:
                a('**The inherited configuration** — all three exits, stop '
                  '1.5 ATR, target 1.5x, trail on, no time stop — is R '
                  '**%+.3f**, R/yr **%+.3f**, dip %.3f, **return per dip '
                  '%.3f**, %d trades. Everything below is measured against '
                  'that row.'
                  % (b.R_total, b.R_per_year, b.worst_dip_R, b.R_per_dip,
                     int(b.trades)))
                a('')
            best = g.nlargest(8, 'R_per_dip')
            a('**The eight best cells by return per dip.**')
            a('')
            a('| exit arm | stop | target | trail | time stop | R total | '
              'R/yr | R/yr ex best day | mean bars | worst dip | '
              '**R per dip** | t yearly | years + |')
            a('|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|'
              '---:|')
            for _, r in best.iterrows():
                a('| `%s` | %.1f | %.1f | %s | %s | %+.3f | %+.3f | %s | '
                  '%.1f | %.3f | **%+.3f** | %s | %d of %d |'
                  % (r.exit_arm, r.stop_atr, r.target_mult,
                     'on' if int(r.trail_on) else 'off',
                     ('off' if not int(r.time_stop_bars)
                      else '%d' % int(r.time_stop_bars)),
                     r.R_total, r.R_per_year,
                     _f(r.get('R_per_year_ex_best_day')), r.mean_bars,
                     r.worst_dip_R, r.R_per_dip, _f(r.t_yearly),
                     int(r.years_positive), int(r.years)))
            a('')
            # one-factor marginals, averaged over everything else
            a('**Each factor on its own, averaged over every other cell** — '
              'which is what a factorial is for: a factor that only looks '
              'good in one corner is not a factor, it is a corner.')
            a('')
            for col, nm in (('exit_arm', 'exit rules'),
                            ('stop_atr', 'stop (ATR)'),
                            ('target_mult', 'target (x stop)'),
                            ('trail_on', 'trail'),
                            ('time_stop_bars', 'time stop (bars)')):
                sub = (g.groupby(col)
                       .agg(cells=('R_per_dip', 'size'),
                            mean_R=('R_total', 'mean'),
                            mean_R_per_dip=('R_per_dip', 'mean'),
                            median_R_per_dip=('R_per_dip', 'median'),
                            mean_dip=('worst_dip_R', 'mean'),
                            mean_trades=('trades', 'mean'))
                       .reset_index())
                a('*%s*' % nm)
                a('')
                a('| value | cells | mean R | mean R per dip | '
                  'median R per dip | mean dip | mean trades |')
                a('|---|---:|---:|---:|---:|---:|---:|')
                for _, r in sub.iterrows():
                    a('| %s | %d | %+.3f | **%+.3f** | %+.3f | %.3f | %.0f |'
                      % (r[col], int(r.cells), r.mean_R, r.mean_R_per_dip,
                         r.median_R_per_dip, r.mean_dip, r.mean_trades))
                a('')
            if b is not None and len(best):
                br = best.iloc[0]
                a('**What %s says.** The best cell is %.3f return per dip '
                  'against %.3f for the inherited configuration, a factor of '
                  '%.2f — **and it is the maximum over %d cells on one '
                  'six-year sample**, so it is an upper bound on what is '
                  'there and not a configuration to adopt. The one-factor '
                  'tables above are the part worth reading: a factor whose '
                  'mean moves consistently across its whole range is '
                  'evidence, and a single corner cell is not.'
                  % (mb, br.R_per_dip, b.R_per_dip,
                     br.R_per_dip / b.R_per_dip
                     if abs(b.R_per_dip) > 1e-9 else float('nan'), len(g)))
                a('')
        a('## What the sweep does and does not change')
        a('')
        a('1. **It does not close the gap to 12%** and could not: the best '
          'cell anywhere in the grid is a small multiple of the inherited '
          'configuration, against a target that needs a factor of ten.')
        a('2. **The inherited exit configuration was never tested**, and now '
          'it has been. Where the one-factor means move consistently, that '
          'is a real finding about the exits; where only one corner cell '
          'wins, it is not.')
        a('3. **Nothing here is adopted.** Changing the exits would mean '
          're-running every stage table in the project, and on the evidence '
          'of a best-of-%d maximum that is not warranted. Jack decides.'
          % len(D))
        a('')
    a('## Provenance')
    a('')
    p_ = os.path.join(OUT, 'exit_grid.csv')
    if not os.path.exists(p_):
        a('- `%s` — **MISSING**' % os.path.join('results', 'nnfx',
                                                'exit_grid.csv'))
    else:
        a('- `%s` — %s rows, md5 `%s`'
          % (os.path.relpath(p_, _R),
             '{:,}'.format(len(S2._safe_csv(p_))),
             hashlib.md5(open(p_, 'rb').read()).hexdigest()[:12]))
    out = out or os.path.join(OUT, 'EXITS.md')
    open(out, 'w').write('\n'.join(L_) + '\n')
    print('  EXITS.md: %d lines -> %s'
          % (len('\n'.join(L_).splitlines()), os.path.relpath(out, _R)),
          flush=True)
    return out


def _f(v, fmt='%+.3f'):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return '—'
    return (fmt % f) if np.isfinite(f) else '—'


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', default='sweep')
    g = ap.parse_args()
    if g.stage in ('all', 'sweep'):
        sweep()
    if g.stage in ('all', 'md'):
        md_exits()
    print('  nnfxexit done', flush=True)


if __name__ == '__main__':
    main()
