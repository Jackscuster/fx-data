import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTDATA,exist_ok=True); os.makedirs(ROOTOUT,exist_ok=True)
sys.path.insert(0,ROOTLIB)
"""Crisis detector scoring against the news calendar in events.py.

==============================================================================
THE WINDOW IS FORWARD-ONLY: event date to +15 DAYS. IT MUST NEVER START BEFORE
THE EVENT DATE.
==============================================================================

An earlier version used a window starting 5 days BEFORE the event and reported
that avgcorr60 "fires 2.5 days early". That result was an artifact of the window,
not a property of the detector: allow a detector to fire before the news and it
will happily take credit for the run-up. Under forward-only testing the effect
vanished entirely and every detector fires on the day. Do not widen the window
backwards to make a detector look predictive.

Detectors, all computed from the 28-pair panel and all causal:

  maxabsmove   largest single-pair daily move across the panel, in sigma
  breadth2sig  how many of the 28 pairs breach 2 sigma on the same day
  paneldisp    cross-sectional dispersion of daily returns, in sigma
  legdiv20     currency-leg divergence: max minus min 20-day currency-index
               move, in sigma. This is the measure that ranks the 2024 carry
               unwind 5th of 27 years.
  avgcorr60    average pairwise correlation of the panel over 60 days

Each fires above its 95th-percentile threshold, learned on IS (1999-2015) only
and applied unchanged thereafter. That puts every base rate near 5% by
construction, which is what makes lift comparable across detectors.

Reported per detector: events caught, recall, base firing rate, lift over
chance, and median days from the news date to the first firing.
"""
import numpy as np, pandas as pd
import events as EV

PX = os.path.join(ROOTDATA,'/px28.csv'.lstrip('/'))
SPLIT = '2016-01-01'
WINDOW = 15          # days AFTER the event. Never negative.
PCTL = 95
CCY = ['EUR', 'GBP', 'AUD', 'NZD', 'USD', 'CAD', 'CHF', 'JPY']


def zscore(s, n=252):
    """Trailing z. std shifted one bar so today's own move cannot set its own scale."""
    return s / s.rolling(n, min_periods=60).std().shift(1)


def currency_index(r):
    """Per-currency daily strength: mean of +r where base, -r where quote."""
    out = {}
    for c in CCY:
        legs = []
        for p in r.columns:
            if p[:3] == c:
                legs.append(r[p])
            elif p[3:] == c:
                legs.append(-r[p])
        out[c] = pd.concat(legs, axis=1).mean(axis=1)
    return pd.DataFrame(out)


def build(px):
    r = np.log(px.astype(float)).diff()
    z = r / r.rolling(252, min_periods=60).std().shift(1)     # per-pair daily z
    ci = currency_index(r)
    leg20 = ci.rolling(20).sum()
    div = leg20.max(axis=1) - leg20.min(axis=1)

    D = pd.DataFrame(index=px.index)
    D['maxabsmove'] = z.abs().max(axis=1)
    D['breadth2sig'] = (z.abs() > 2).sum(axis=1)
    D['paneldisp'] = zscore(r.std(axis=1))
    D['legdiv20'] = zscore(div)
    D['avgcorr60'] = (r.rolling(60).corr().groupby(level=0)
                      .apply(lambda m: m.values[np.triu_indices(m.shape[1], 1)].mean()))
    return D


def score(D, cal):
    ins = D.index < SPLIT
    rows, per_event = [], []
    for name in D.columns:
        s = D[name].dropna()
        thr = np.nanpercentile(s[s.index < SPLIT], PCTL) if ins.any() else np.nanpercentile(s, PCTL)
        fire = s > thr
        base = float(fire.mean())
        caught, lags = 0, []
        for _, e in cal.iterrows():
            lo = e.date                                  # forward-only: never before
            hi = e.date + pd.Timedelta(days=WINDOW)
            w = fire[(fire.index >= lo) & (fire.index <= hi)]
            hit = bool(w.any())
            lag = int((w[w].index[0] - lo).days) if hit else None
            caught += hit
            if hit:
                lags.append(lag)
            per_event.append(dict(detector=name, date=str(e.date.date()), type=e.type,
                                  ccy=e.ccy, severity=int(e.severity),
                                  description=e.description, caught=hit, lag_days=lag))
        n = len(cal)
        recall = caught / n if n else np.nan
        rows.append(dict(detector=name, threshold=float(thr), caught=caught, n_events=n,
                         recall=recall, base_rate=base,
                         lift=recall / base if base > 0 else np.nan,
                         median_lag_days=float(np.median(lags)) if lags else np.nan))
    return (pd.DataFrame(rows).sort_values('lift', ascending=False),
            pd.DataFrame(per_event))


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    cal = EV.calendar()
    cal = cal[(cal.date >= px.index.min()) & (cal.date <= px.index.max())]
    D = build(px)
    S, E = score(D, cal)

    S.to_csv(os.path.join(ROOTOUT,'/crisis_detectors.csv'.lstrip('/')), index=False)
    E.to_csv(os.path.join(ROOTOUT,'/crisis_events.csv'.lstrip('/')), index=False)

    pd.set_option('display.width', 220, 'display.max_columns', 20)
    f = lambda x: '%.4f' % x
    print('=' * 78)
    print('CRISIS DETECTORS vs %d NEWS EVENTS — window 0 to +%d days, forward only'
          % (len(cal), WINDOW))
    print('=' * 78)
    print(S.to_string(index=False, float_format=f))
    print('\nEvery date came from news. No date was chosen by looking at price.')
    print('Base rates sit near %d%% by construction: each threshold is the IS %dth '
          'percentile.' % (100 - PCTL, PCTL))
    lead = S[S.median_lag_days < 0]
    print('detectors firing BEFORE the news: %s'
          % (', '.join(lead.detector) if len(lead) else 'none — as expected, '
             'the window cannot reach backwards'))
    b = S.iloc[0]
    print('\nBest: %s — %d of %d, recall %.0f%%, base rate %.1f%%, lift %.1fx, median lag %.0f days'
          % (b.detector, b.caught, b.n_events, 100 * b.recall, 100 * b.base_rate,
             b.lift, b.median_lag_days))
    miss = (E[(E.detector == b.detector) & (~E.caught)]
            .sort_values('severity', ascending=False))
    if len(miss):
        print('\nMissed by %s (%d):' % (b.detector, len(miss)))
        print(miss[['date', 'type', 'ccy', 'severity', 'description']]
              .to_string(index=False))


if __name__ == '__main__':
    main()
