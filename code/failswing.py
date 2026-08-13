import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Failed swings, defined entirely within the trailing window.

THE DEFINITION, and every clause of it is backward-looking.

  At bar t, with a 28-bar window split into an OLD part and a RECENT part:

    prior extreme  H = highest close in the old part [t-28, t-6]
                   L = lowest  close in the old part
    approach       the recent part [t-5, t] reached at least X of the way from
                   L back up to H -- peak >= L + X*(H - L) -- and did NOT
                   exceed H, because clearing it is a breakout, not a failure
    rejection      price has since turned back from that recent peak by at
                   least Y multiples of the recent average daily range

  and the mirror for the downside. Everything is a max, min or mean of bars at
  or before t, and the whole thing is then shifted one bar like every other
  signal here. Nothing looks forward.

THE APPROACH MUST NOT CLEAR THE EXTREME. Without that clause the 'failure' fires
on every successful breakout too, and X stops meaning anything -- at X=0.99 the
condition would be satisfied by price at 3x the old high. That is the clause
that makes the X sweep interpretable.

BOTH PARAMETERS SWEPT, NOT PICKED.

  X  0.85 0.90 0.93 0.95 0.97 0.98 0.99      how close to the prior extreme
  Y  0.5 0.75 1.0 1.5 2.0 3.0 4.0            turn-back, in recent daily ranges

49 cells. A single spiking cell in a 49-cell grid is what noise looks like; a
broad contiguous plateau would mean something, so the full surface is printed
and the best cell's own neighbours are reported beside it.

IS/OOS SPLIT. The cell is chosen on 1999-2015 and the holdout is read ONCE. The
lead-time work only reached this discipline at 16.4i and the first version of it
selected on the holdout by accident; this one does not.

WHAT IT IS SCORED AGAINST. The three change types from changes.py separately --
shape, activity, both -- because a rejection at a prior high is a claim about
shape, and if it turns out to track activity changes instead that is worth
knowing rather than averaging away.

Writes results/failswing_surface.csv and results/failswing_confirm.csv.
"""
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
SPLIT = pd.Timestamp('2016-01-01')
NSEL = int(os.environ.get('FX_NSEL', 30))
NFIN = int(os.environ.get('FX_NSHUF', 200))
W, RECENT = 28, 5
XS = (0.85, 0.90, 0.93, 0.95, 0.97, 0.98, 0.99)
YS = (0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0)
LEAD = 1

from combined import layers, product, confirm, DWELL
from masweep import warn_of, plateau
from changes import parts, change_masks
from structval import surrogate


def failed(px, X, Y):
    """-> bool frame. A rejection at a prior extreme, judged only on the past."""
    lp = np.log(px.astype(float))
    rr = lp.diff()
    rng_ = rr.abs().rolling(W).mean()                 # recent daily range
    old_hi = lp.rolling(W - RECENT).max().shift(RECENT + 1)
    old_lo = lp.rolling(W - RECENT).min().shift(RECENT + 1)
    peak = lp.rolling(RECENT + 1).max()
    trough = lp.rolling(RECENT + 1).min()
    span = (old_hi - old_lo).replace(0, np.nan)

    up_reach = (peak - old_lo) / span
    up = (up_reach >= X) & (peak <= old_hi) & ((peak - lp) >= Y * rng_)
    dn_reach = (old_hi - trough) / span
    dn = (dn_reach >= X) & (trough >= old_lo) & ((lp - trough) >= Y * rng_)
    f = (up | dn).where(span.notna() & rng_.notna(), False)
    # fire on the bar the rejection first qualifies, not every bar it holds
    return (f & ~f.shift(1).fillna(False)).shift(1).fillna(False)


def lifts(fire, M, kinds):
    w = warn_of(fire.values.astype(bool), LEAD)
    out = {}
    for k in kinds:
        m, ok = M[k]
        base = w[ok].mean()
        out[k] = (w[m].mean() / base) if base and m.any() else np.nan
    return out


def sweep(px, fit, M, kinds):
    out = {}
    for X in XS:
        for Y in YS:
            f = failed(px, X, Y)
            for k, v in lifts(f, M, kinds).items():
                out[(X, Y, k)] = v
    return out


def masks_for(px, fit, period):
    shc, actc, comb = parts(px, fit)
    return change_masks(shc, actc, comb, period)


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    fit = px.index < SPLIT
    KINDS = ['shape only', 'activity only', 'both', 'combined (shipped)']

    print('FAILED SWINGS: %d x %d = %d cells, within-window definition'
          % (len(XS), len(YS), len(XS) * len(YS)))
    f = failed(px, 0.95, 1.0)
    print('  firing rate at X=0.95 Y=1.0: %.3f%% of bars'
          % (100 * f.values.mean()))
    print('  firing rate range across the grid: %.3f%% to %.3f%%'
          % (100 * min(failed(px, X, Y).values.mean() for X in XS for Y in YS),
             100 * max(failed(px, X, Y).values.mean() for X in XS for Y in YS)))

    print('\nIS SELECTION, %d surrogate draws' % NSEL)
    Mis = masks_for(px, fit, 'is')
    real = sweep(px, fit, Mis, KINDS)
    rng = np.random.default_rng(1729)
    acc = {k: [] for k in real}
    for i in range(NSEL):
        px2 = surrogate(px, 'sign', rng)
        for k, v in sweep(px2, fit, masks_for(px2, fit, 'is'), KINDS).items():
            acc[k].append(v)
        if (i + 1) % 10 == 0:
            print('  %d/%d' % (i + 1, NSEL), flush=True)

    rows = []
    for (X, Y, k), v in real.items():
        s = np.array(acc[(X, Y, k)], float); s = s[np.isfinite(s)]
        rows.append(dict(X=X, Y=Y, kind=k, is_lift=v, is_surr=s.mean(),
                         is_excess=v - s.mean(),
                         is_z=(v - s.mean()) / s.std() if s.std() else np.nan))
    S = pd.DataFrame(rows)
    S.to_csv(os.path.join(ROOTOUT, 'failswing_surface.csv'), index=False)

    for k in KINDS:
        d = S[S.kind == k]
        E = d.pivot(index='X', columns='Y', values='is_excess')
        print('\n%s -- IS EXCESS over its own surrogate' % k.upper())
        print(E.to_string(float_format=lambda v: '%+.3f' % v, na_rep='   .'))
        n, big = plateau(E.values, 0.05)
        n2, big2 = plateau(E.values, 0.10)
        print('  cells > +0.05: %2d of %d, largest contiguous %d'
              '   |  > +0.10: %2d, largest %d' % (n, E.size, big, n2, big2))

    # AND SELECTION IS RESTRICTED TO INTERIOR CELLS. A 3x3 mean is not enough
    # on its own: a corner cell has only three neighbours, so a lone spike at
    # the edge of the grid survives smoothing -- which is exactly what happened
    # on the first run, where X=0.99 Y=4.00 won on both the raw and the smoothed
    # criterion while firing on 0.128% of bars, the sparsest cell in the sweep.
    # A plateau needs room around it, and a cell at the boundary of the swept
    # range cannot be shown to have any without extending the range.
    # SELECTION PICKS THE PLATEAU, NOT THE SPIKE. Taking the single best cell
    # would contradict the standard set at the top of this file, so each cell is
    # scored by the MEAN IS EXCESS OF ITS 3x3 NEIGHBOURHOOD, itself included. A
    # lone spike surrounded by nothing cannot win; a cell in the middle of a
    # broad raised region does. The raw best cell is reported beside it.
    sm = []
    for k in KINDS:
        E = S[S.kind == k].pivot(index='X', columns='Y', values='is_excess')
        V = E.values
        for i, X in enumerate(E.index):
            for j, Y in enumerate(E.columns):
                nb = V[max(0, i - 1):i + 2, max(0, j - 1):j + 2]
                interior = (0 < i < len(E.index) - 1
                            and 0 < j < len(E.columns) - 1)
                sm.append(dict(X=X, Y=Y, kind=k, smooth=np.nanmean(nb),
                               n_neighbours=nb.size - 1, interior=interior,
                               fire_rate=float(failed(px, X, Y).values.mean())))
    SM = pd.DataFrame(sm)
    S = S.merge(SM, on=['X', 'Y', 'kind'])
    S.to_csv(os.path.join(ROOTOUT, 'failswing_surface.csv'), index=False)
    raw = S.sort_values('is_excess', ascending=False).iloc[0]
    print('\n  raw best cell (NOT chosen): X=%.2f Y=%.2f %s, excess %+.3f,'
          ' fires on %.3f%% of bars -- a grid corner'
          % (raw.X, raw.Y, raw.kind, raw.is_excess, 100 * raw.fire_rate))
    T = S[S.interior].sort_values('smooth', ascending=False)
    w = T.iloc[0]
    print('\nCHOSEN ON IS by 3x3 neighbourhood mean: X=%.2f Y=%.2f, "%s"'
          % (w.X, w.Y, w.kind))
    print('  neighbourhood mean excess %+.3f over %d neighbours, fires on'
          ' %.3f%% of bars' % (w.smooth, w.n_neighbours, 100 * w.fire_rate))
    print('  IS lift %.3f  surrogate %.3f  excess %+.3f  z %+.2f'
          % (w.is_lift, w.is_surr, w.is_excess, w.is_z))
    E = S[S.kind == w.kind].pivot(index='X', columns='Y', values='is_excess')
    i, j = list(E.index).index(w.X), list(E.columns).index(w.Y)
    nb = [E.values[u, v] for u in range(max(0, i - 1), min(E.shape[0], i + 2))
          for v in range(max(0, j - 1), min(E.shape[1], j + 2))
          if (u, v) != (i, j) and np.isfinite(E.values[u, v])]
    print('  its %d neighbours: mean %+.3f, min %+.3f, max %+.3f'
          % (len(nb), np.mean(nb), np.min(nb), np.max(nb)))

    print('\nHOLDOUT, READ ONCE, %d surrogate draws of each kind' % NFIN)
    Moos = masks_for(px, fit, 'oos')
    ho = lifts(failed(px, w.X, w.Y), Moos, [w.kind])[w.kind]
    out = []
    for kind in ('sign', 'iid'):
        r2 = np.random.default_rng(3141)
        v = []
        for _ in range(NFIN):
            p2 = surrogate(px, kind, r2)
            v.append(lifts(failed(p2, w.X, w.Y),
                           masks_for(p2, fit, 'oos'), [w.kind])[w.kind])
        v = np.array(v, float); v = v[np.isfinite(v)]
        p = (1 + int((v >= ho).sum())) / (len(v) + 1)
        print('  %-5s lift %.3f   surrogate %.3f +/- %.3f   excess %+.3f   p=%.3f'
              % (kind, ho, v.mean(), v.std(), ho - v.mean(), p))
        out.append(dict(X=w.X, Y=w.Y, kind=w.kind, is_excess=w.is_excess,
                        null=kind, holdout_lift=ho, surrogate=v.mean(),
                        sd=v.std(), excess=ho - v.mean(), p=p))
    O = pd.DataFrame(out)
    O.to_csv(os.path.join(ROOTOUT, 'failswing_confirm.csv'), index=False)
    surv = bool((O.excess > 0.05).all() and (O.p < 0.05).all())
    print('\n  SURVIVES (excess > 0.05 and p < 0.05 against BOTH nulls): %s'
          % ('YES' if surv else 'NO'))
    print('\nwrote failswing_surface.csv and failswing_confirm.csv')


if __name__ == '__main__':
    main()
