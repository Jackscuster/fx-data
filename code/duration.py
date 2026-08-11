import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Task 9. Duration -- how long a state has been running, and whether that matters.

BASE STATES. The four scale x straightness states from Task 8. Measured, those
run a median of 2-3 bars with a transition diagonal of 0.769, which implies
1/(1-0.769) = 4.3 bars mechanically. Duration statistics on a state that lasts
two days measure the jitter in the median cut, not the persistence of anything.

So the same machinery is run twice: once on the raw states as specified, and once
with HYSTERESIS -- the state only switches when the measure crosses a band around
its own median rather than the median itself, so a reading sitting on the cut
does not flip the label every other bar. The band is swept, and what band width
buys what run length is reported rather than assumed.

WHAT IS MEASURED
  age          bars the current state has been running
  typical      that pair's own in-sample median run length for that state
  rel_age      age / typical -- is this run old FOR THIS PAIR AND STATE
  changes_60   state changes in the last 60 bars
  hazard       P(the state ends next bar | it has already lasted a bars)

Note that "time since the last state change" and "bars the current state has been
running" are the same number for a hard-switching state machine, so only one is
carried; changes_60 is the measure that adds something.

Everything is trailing and lagged. Cut points and typical lengths come from
in-sample only.

Writes results/duration_states.csv, duration_hazard.csv, duration_excursion.csv.
"""
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
EV = os.path.join(ROOTOUT, 'entry_events.csv')
SPLIT = pd.Timestamp('2016-01-01')
W, VOLWIN, CHGWIN = 20, 60, 60
BANDS = [0., .05, .10, .15, .20, .25]
ORDER = ['trending (straight+large)', 'drifting (straight+small)',
         'volatile chop (choppy+large)', 'dead (choppy+small)']


def measures(px):
    lp = np.log(px.astype(float))
    net = (lp - lp.shift(W)).abs()
    path = lp.diff().abs().rolling(W).sum()
    vol = lp.diff().rolling(VOLWIN).std()
    inf = [np.inf, -np.inf]
    return ((net / path).replace(inf, np.nan).shift(1),
            (path / (vol * np.sqrt(W))).replace(inf, np.nan).shift(1))


def label(sfrac, cfrac, band):
    """Two binary axes with a dead band. Below lo -> 0, above hi -> 1, between ->
    hold the previous value. Vectorised per pair via forward fill."""
    def side(x):
        lo, hi = .5 - band / 2, .5 + band / 2
        s = pd.DataFrame(np.nan, index=x.index, columns=x.columns)
        s[x >= hi] = 1.0
        s[x <= lo] = 0.0
        return s.ffill()
    a, b = side(sfrac), side(cfrac)
    ok = a.notna() & b.notna()
    return pd.DataFrame(
        np.where(ok, np.where(a == 1, np.where(b == 1, ORDER[0], ORDER[1]),
                              np.where(b == 1, ORDER[2], ORDER[3])), None),
        index=sfrac.index, columns=sfrac.columns)


def runs_of(lab):
    """-> DataFrame(pair, state, start_idx, length)."""
    out = []
    for p in lab.columns:
        v = lab[p].dropna()
        if not len(v):
            continue
        gid = (v != v.shift()).cumsum()
        for _, g in v.groupby(gid):
            out.append((p, g.iloc[0], g.index[0], len(g)))
    return pd.DataFrame(out, columns=['pair', 'state', 'start', 'len'])


def age_frame(lab):
    """Bars the current run has lasted, and changes in the last CHGWIN bars."""
    age = pd.DataFrame(index=lab.index, columns=lab.columns, dtype=float)
    chg = pd.DataFrame(index=lab.index, columns=lab.columns, dtype=float)
    for p in lab.columns:
        v = lab[p]
        m = v.notna()
        gid = (v != v.shift()).where(m).cumsum()
        age[p] = v.groupby(gid).cumcount().where(m) + 1
        chg[p] = ((v != v.shift()) & m).rolling(CHGWIN).sum()
    return age, chg


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    ins = np.asarray(px.index < SPLIT)
    s, c = measures(px)
    # rank each measure inside its own in-sample distribution, per pair, so the
    # band is expressed in percentile terms and means the same thing everywhere
    sf = pd.DataFrame({p: s[p].rank(pct=True) for p in px.columns})
    cf = pd.DataFrame({p: c[p].rank(pct=True) for p in px.columns})

    print('BAND SWEEP -- what hysteresis buys')
    print('%6s %10s %12s %10s %10s' % ('band', 'median run', 'mean run',
                                       '%<5 bars', 'diagonal'))
    sweep = []
    labs = {}
    for b in BANDS:
        L = label(sf, cf, b)
        R = runs_of(L)
        d = np.mean([(L[p].dropna() == L[p].dropna().shift()).mean()
                     for p in L.columns])
        sweep.append(dict(band=b, median_run=R.len.median(), mean_run=R.len.mean(),
                          under5=(R.len < 5).mean(), diagonal=d, n_runs=len(R)))
        labs[b] = L
        print('%6.2f %10.1f %12.2f %10.3f %10.3f'
              % (b, R.len.median(), R.len.mean(), (R.len < 5).mean(), d))
    S = pd.DataFrame(sweep)
    S.to_csv(os.path.join(ROOTOUT, 'duration_bands.csv'), index=False)

    hit = S[S.median_run >= 30]
    band = float(hit.band.iloc[0]) if len(hit) else float(S.band.iloc[-1])
    print('\nband carried forward: %.2f (median run %.1f bars)'
          % (band, float(S[S.band == band].median_run.iloc[0])))
    for tag, b in (('raw', 0.0), ('hysteresis', band)):
        run_report(tag, labs[b], px, ins)


def run_report(tag, lab, px, ins):
    print('\n' + '=' * 72)
    print('DURATION ON THE %s STATES' % tag.upper())
    R = runs_of(lab)
    Ris = R[R.start < SPLIT]
    typ = Ris.groupby(['pair', 'state']).len.median().rename('typical')
    st = R.groupby('state').agg(runs=('len', 'size'), median=('len', 'median'),
                                mean=('len', 'mean'),
                                under5=('len', lambda x: (x < 5).mean())).reindex(ORDER)
    print(st.to_string(float_format=lambda v: '%.2f' % v))

    age, chg = age_frame(lab)
    A = pd.DataFrame({'state': lab.stack(), 'age': age.stack(),
                      'chg60': chg.stack()}).reset_index()
    A.columns = ['date', 'pair', 'state', 'age', 'chg60']
    A = A.merge(typ.reset_index(), on=['pair', 'state'], how='left')
    A['rel_age'] = A.age / A.typical
    A['oos'] = A.date >= SPLIT
    A.to_csv(os.path.join(ROOTOUT, 'duration_states_%s.csv' % tag), index=False)
    print('\nchanges in the last %d bars: mean %.1f, median %.0f'
          % (CHGWIN, A.chg60.mean(), A.chg60.median()))

    # ---- hazard: do old states persist or break? ----
    print('\nHAZARD -- P(state ends next bar | it has lasted this long), OOS')
    O = A[A.oos].dropna(subset=['age'])
    ends = O.groupby(['pair']).apply(
        lambda g: g.assign(ended=(g.state != g.state.shift(-1)).astype(float)),
        include_groups=False).reset_index(drop=True)
    bins = [0, 2, 5, 10, 20, 40, 10 ** 6]
    lbl = ['1-2', '3-5', '6-10', '11-20', '21-40', '40+']
    ends['bucket'] = pd.cut(ends.age, bins, labels=lbl, right=True)
    h = ends.groupby('bucket', observed=True).agg(
        n=('ended', 'size'), hazard=('ended', 'mean'))
    print(h.to_string(float_format=lambda v: '%.3f' % v))
    flat = h.hazard.iloc[0] if len(h) else np.nan
    print('  a flat hazard means age carries no information; falling means old'
          ' states persist, rising means they break')
    h.to_csv(os.path.join(ROOTOUT, 'duration_hazard_%s.csv' % tag))

    # ---- reconnect to task 3 ----
    if not os.path.exists(EV):
        return
    E = pd.read_csv(EV)
    E['date'] = pd.to_datetime(E.date)
    X = E.merge(A[['date', 'pair', 'state', 'age', 'rel_age']],
                on=['date', 'pair'], how='left')
    X = X[X.oos & X.state.notna() & X.rel_age.notna()]
    if not len(X):
        return
    X['band'] = np.where(X.rel_age <= 1, 'young (<= typical)', 'old (> typical)')
    print('\nTASK 3 EXCURSION BY STATE AND AGE (out of sample)')
    g = X.groupby(['state', 'band']).agg(
        n=('mfe', 'size'), mfe=('mfe', 'mean'), mae=('mae', 'mean'),
        bars=('bars_to_peak', 'mean'), eff=('path_eff', 'mean'),
        fav20=('fav_20', 'mean')).reindex(
            pd.MultiIndex.from_product([ORDER, ['young (<= typical)', 'old (> typical)']]))
    g['ratio'] = g.mfe / g.mae.abs()
    print(g[['n', 'mfe', 'ratio', 'bars', 'eff', 'fav20']]
          .to_string(float_format=lambda v: '%.4f' % v))
    g.to_csv(os.path.join(ROOTOUT, 'duration_excursion_%s.csv' % tag))
    for stn in ORDER:
        sub = X[X.state == stn]
        y = sub[sub.band.str.startswith('young')]
        o = sub[sub.band.str.startswith('old')]
        if len(y) < 50 or len(o) < 50:
            continue
        for col in ('bars_to_peak', 'path_eff', 'mfe'):
            a, b = y[col].dropna(), o[col].dropna()
            d = b.mean() - a.mean()
            se = np.sqrt(a.var() / len(a) + b.var() / len(b))
            if col == 'bars_to_peak':
                print('  %-30s' % stn[:30], end='')
            print('  %s %+.4f (t %+.1f)' % (col.split('_')[0], d, d / se if se else 0),
                  end='')
        print()


if __name__ == '__main__':
    main()
