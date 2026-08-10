import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Task 3. At the moment a signal fires, does the regime read predict the SHAPE
of what follows?

Everything before this asks whether a signal predicts forward efficiency, which
is a property of the estimator. This asks the question that decides whether the
estimator is worth building on: given an entry event, does the regime reading
say anything about how the move that follows behaves?

NO EXIT RULE, NO MONEY. Excursion and timing only -- how far it went the right
way, how far the wrong way, how long to the peak, whether it was still onside
later, and how straight the path was. No Sharpe, no PnL, no win rate. Whether a
strategy makes money is Layer 2's question and needs the full template.

THE TRIGGERS ARE DELIBERATELY DUMB. A 20-day breakout, a 20/100 moving-average
cross, and a two-sigma stretch faded. They exist to generate entry events at
times a real strategy might plausibly act, not to be good. Optimising them would
make the excursion profiles a property of the trigger rather than the regime.

DIRECTION OF THE READ. The composite is sign-aligned so HIGH means expect
straight travel and LOW means expect whipsaw. So the chop third is the BOTTOM
third, and the prediction under test is: bottom-third entries peak sooner, give
more of it back, and travel a less efficient path than top-third entries.

LAG. The composite already lags its inputs one bar inside survivors.py, so the
reading recorded at an entry on day t uses information through t-1. The trigger
itself is evaluated on the close of t and the excursion is measured strictly
after t.

TERCILE CUTS COME FROM IN-SAMPLE ONLY and are applied unchanged to the holdout,
like every other cut point in the project.

Writes results/entry_excursion.csv, entry_by_pair.csv, entry_events.csv.
"""
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
COMP = os.path.join(ROOTOUT, 'survivor_composite.csv')
SPLIT = pd.Timestamp('2016-01-01')
W = 20                      # bars of forward excursion measured
CHECK = [5, 10, 20]
GAP = 20                    # bars between entries in the non-overlapping subsample
LAB = ['chop (bottom)', 'mid', 'trend (top)']


def triggers(p):
    """-> DataFrame(date, direction) of entry events, one frame per trigger.

    Each is evaluated on the close of the entry bar; nothing here reads forward.
    """
    lp = np.log(p.astype(float))
    out = {}

    hi = p.rolling(20).max().shift(1)
    lo = p.rolling(20).min().shift(1)
    br = pd.Series(0, index=p.index)
    br[p > hi] = 1
    br[p < lo] = -1
    # only the first bar of a run counts as the event
    out['breakout20'] = br.where(br != br.shift(1)).fillna(0)

    f, s = p.rolling(20).mean(), p.rolling(100).mean()
    d = np.sign(f - s)
    out['macross_20_100'] = d.where(d != d.shift(1)).fillna(0)

    r = lp.diff(20)
    z = (r - r.rolling(250).mean()) / r.rolling(250).std()
    fade = pd.Series(0, index=p.index)
    fade[z > 2] = -1                     # stretched up -> fade it
    fade[z < -2] = 1
    out['zfade_2sd'] = fade.where(fade != fade.shift(1)).fillna(0)
    return out


def excursions(lp, idx, direction):
    """Forward path from an entry, in log terms, signed by direction."""
    n = len(lp)
    if idx + W >= n:
        return None
    fwd = (lp.values[idx + 1:idx + W + 1] - lp.values[idx]) * direction
    if not np.isfinite(fwd).all():
        return None
    step = np.abs(np.diff(np.concatenate([[lp.values[idx]],
                                          lp.values[idx + 1:idx + W + 1]])))
    path = step.sum()
    mfe = float(fwd.max())
    mae = float(fwd.min())
    # giveback per row as (mfe - final)/mfe explodes whenever mfe is near zero,
    # and its MEAN is then meaningless -- an early version of this reported 6.05
    # against 11.32 between terciles, which is noise from the divisor. Absolute
    # giveback is always defined; the proportional version is formed at the group
    # level from the two means, never row by row.
    rec = dict(mfe=mfe, mae=mae, final=float(fwd[-1]),
               bars_to_peak=int(np.argmax(fwd)) + 1,
               giveback=float(mfe - fwd[-1]),
               path_eff=float(abs(fwd[-1]) / path) if path > 0 else np.nan)
    for k in CHECK:
        rec['fav_%d' % k] = bool(fwd[k - 1] > 0)
    return rec


def build():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    C = pd.read_csv(COMP, index_col=0, parse_dates=True).reindex(px.index)
    rows = []
    for pair in px.columns:
        p = px[pair].dropna()
        if len(p) < 500:
            continue
        lp = np.log(p.astype(float))
        comp = C[pair].reindex(p.index)
        pos = {d: i for i, d in enumerate(p.index)}
        for tname, sig in triggers(p).items():
            ev = sig[sig != 0]
            for dt, direction in ev.items():
                r = comp.get(dt, np.nan)
                if not np.isfinite(r):
                    continue
                e = excursions(lp, pos[dt], float(direction))
                if e is None:
                    continue
                e.update(pair=pair, trigger=tname, date=dt,
                         direction=int(direction), regime=float(r),
                         oos=bool(dt >= SPLIT))
                rows.append(e)
    E = pd.DataFrame(rows).sort_values(['pair', 'trigger', 'date'])

    # tercile cut points from IS only, applied unchanged to the holdout
    cuts = E[~E.oos].regime.quantile([1 / 3, 2 / 3]).values
    E['tercile'] = np.digitize(E.regime, cuts)
    E['band'] = [LAB[i] for i in E.tercile]

    # non-overlapping subsample: entries within a pair and trigger are heavily
    # clustered, so the raw counts overstate how much independent evidence exists
    keep = []
    for (pair, tname), g in E.groupby(['pair', 'trigger'], sort=False):
        last = None
        for i, dt in zip(g.index, g.date):
            if last is None or (dt - last).days >= GAP * 7 / 5:
                keep.append(i)
                last = dt
    E['indep'] = E.index.isin(keep)
    E.to_csv(os.path.join(ROOTOUT, 'entry_events.csv'), index=False)
    return E, cuts


AGG = dict(n=('mfe', 'size'), mfe=('mfe', 'mean'), mae=('mae', 'mean'),
           bars_to_peak=('bars_to_peak', 'mean'), giveback=('giveback', 'mean'),
           final=('final', 'mean'), path_eff=('path_eff', 'mean'),
           fav5=('fav_5', 'mean'), fav10=('fav_10', 'mean'), fav20=('fav_20', 'mean'))
FMT = {'mfe': '{:.4f}'.format, 'mae': '{:.4f}'.format, 'ratio': '{:.2f}'.format,
       'giveback': '{:.5f}'.format, 'gb_pct': '{:.1f}'.format,
       'path_eff': '{:.4f}'.format,
       'fav5': '{:.3f}'.format, 'fav10': '{:.3f}'.format, 'fav20': '{:.3f}'.format,
       'bars_to_peak': '{:.1f}'.format}


def table(E):
    t = E.groupby('band').agg(**AGG).reindex(LAB).reset_index()
    t['ratio'] = t.mfe / t.mae.abs()
    t['gb_pct'] = 100 * t.giveback / t.mfe        # group level, not row level
    return t[['band', 'n', 'mfe', 'mae', 'ratio', 'bars_to_peak', 'giveback',
              'gb_pct', 'path_eff', 'fav5', 'fav10', 'fav20']]


def report(E):
    print('%d entry events, %d pairs, %d triggers'
          % (len(E), E.pair.nunique(), E.trigger.nunique()))
    print(E.groupby('trigger').agg(n=('mfe', 'size'),
                                   oos=('oos', 'sum')).to_string())
    for tag, sub in (('IN SAMPLE', E[~E.oos]), ('OUT OF SAMPLE', E[E.oos])):
        print('\n%s -- pooled, by regime tercile' % tag)
        print(table(sub).to_string(index=False, formatters=FMT))
    print('\nOUT OF SAMPLE -- non-overlapping entries only (>=%d bars apart)' % GAP)
    print(table(E[E.oos & E.indep]).to_string(index=False, formatters=FMT))
    print('\nOUT OF SAMPLE -- by trigger')
    for tname, g in E[E.oos].groupby('trigger'):
        print('  %s' % tname)
        print(table(g).to_string(index=False, formatters=FMT))

    # per pair: does the predicted ordering hold pair by pair?
    rows = []
    for pair, g in E[E.oos].groupby('pair'):
        t = g.groupby('band').agg(**AGG).reindex(LAB)
        if t.n.isna().any() or (t.n < 20).any():
            continue
        rows.append(dict(pair=pair, n=int(t.n.sum()),
                         peak_chop=t.bars_to_peak.iloc[0],
                         peak_trend=t.bars_to_peak.iloc[2],
                         eff_chop=t.path_eff.iloc[0], eff_trend=t.path_eff.iloc[2],
                         mfe_chop=t.mfe.iloc[0], mfe_trend=t.mfe.iloc[2]))
    P = pd.DataFrame(rows)
    if len(P):
        P['peak_later_in_trend'] = P.peak_trend > P.peak_chop
        P['eff_higher_in_trend'] = P.eff_trend > P.eff_chop
        print('\nPER PAIR (OOS, pairs with >=20 entries in every band): %d pairs'
              % len(P))
        print('  peak comes later in the trend third:  %d of %d'
              % (int(P.peak_later_in_trend.sum()), len(P)))
        print('  path is straighter in the trend third: %d of %d'
              % (int(P.eff_higher_in_trend.sum()), len(P)))
        print(P.head(10).to_string(index=False, float_format=lambda v: '%.4f' % v))
    return P


def main():
    E, cuts = build()
    print('IS tercile cut points on the composite: %.3f, %.3f' % tuple(cuts))
    P = report(E)
    for tag, sub in (('is', E[~E.oos]), ('oos', E[E.oos])):
        table(sub).assign(sample=tag).to_csv(
            os.path.join(ROOTOUT, 'entry_excursion_%s.csv' % tag), index=False)
    if len(P):
        P.to_csv(os.path.join(ROOTOUT, 'entry_by_pair.csv'), index=False)
    pd.concat([table(E[~E.oos]).assign(sample='is'),
               table(E[E.oos]).assign(sample='oos'),
               table(E[E.oos & E.indep]).assign(sample='oos_nonoverlap')]).to_csv(
        os.path.join(ROOTOUT, 'entry_excursion.csv'), index=False)
    print('\nwrote entry_excursion.csv, entry_by_pair.csv, entry_events.csv')
    return E


if __name__ == '__main__':
    main()
