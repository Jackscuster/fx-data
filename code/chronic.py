import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Chronic crisis: sustained one-way debasement. The detector and its boundaries.

ACUTE IS BUILT AND CHRONIC IS ITS OPPOSITE. Acute is a violent snap-back caught by
currency-leg divergence. Chronic is years of bleed with no spike -- the canonical
JPY case reads 2.9 sigma on the spike measure, which is nothing. The signature is
PERSISTENT DRIFT WITHOUT VIOLENCE.

THREE CANDIDATES, DECLARED, NO SWEEP. All over a 250-bar window, all lagged one
bar:

  drift    |250-bar cumulative move| / (daily vol * sqrt(250)). Big total move,
           low daily drama. A random walk sits near 1 by construction.
  onesided share of the last 250 bars closing in the net direction, and share
           setting a new 250-bar extreme. Reported as the mean of the two.
  starve   1 - (deepest counter-move inside the window / total move). Chronic
           bleeds never retrace properly.

THE HARD BOUNDARY IS NORMAL TRENDING, NOT CALM. Chronic IS a trend, so a detector
that merely separates chronic from quiet markets has done nothing. What has to
separate is chronic from ORDINARY TRENDING EPISODES, and the comparison below is
built that way: trending bars OUTSIDE the news-dated chronic windows are their own
group, not lumped into "everything else".

WHAT THE SMALL SAMPLE COSTS. Six pair-groups over five independent macro events
(chronic_episodes.txt). Three start before 2016 and three after, so an IS/OOS
split of the EPISODE LIST leaves two or three events a side and cannot support a
holdout confirmation. Separation is measured on the full sample and null-tested by
circularly shifting the episode windows; the sub-period split is reported for what
it is worth at this sample size. No holdout claim is made, and that is a limit of
the phenomenon -- chronic episodes are rare -- not of the method.

CROSS-CHECK. The acute detector (maxabsmove, reconstructed from crisis.py: the
largest single-pair daily move across the panel in sigma) and the chronic detector
are meant to be two different alarms. Each is read on the other's episodes.

Writes results/chronic_detector.csv, chronic_separation.csv and .txt companions.
"""
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
ST = os.path.join(ROOTOUT, 'states_g4_twoscore4.csv')
EPI = os.path.join(ROOTOUT, 'chronic_episodes.csv')
SPLIT = pd.Timestamp('2016-01-01')
WIN = 250
VOLW = 60
NSHIFT = int(os.environ.get('FX_NSHIFT', 50))
MINOFF = 500
CRISIS_FWD = 15
GROUPS = ['chronic', 'trending (not chronic)', 'acute', 'other']

from drivers import crisis_mask, hdr


def load():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    st = pd.read_csv(ST, index_col=0, parse_dates=True, comment='#')\
        .reindex(px.index)
    ep = pd.read_csv(EPI, parse_dates=['start', 'end'])
    return px, st, ep


def detectors(px):
    """The three declared constructions. All lagged one bar."""
    lp = np.log(px.astype(float))
    r = lp.diff()
    vol = r.rolling(VOLW).std()
    net = lp - lp.shift(WIN)
    drift = (net.abs() / (vol * np.sqrt(WIN))).replace([np.inf, -np.inf], np.nan)

    sgn = np.sign(net)
    agree = pd.DataFrame({p: (np.sign(r[p]) == sgn[p]).rolling(WIN).mean()
                          for p in px.columns})
    hi = lp.rolling(WIN).max()
    lo = lp.rolling(WIN).min()
    newext = pd.DataFrame({p: (((lp[p] >= hi[p]) & (sgn[p] > 0))
                               | ((lp[p] <= lo[p]) & (sgn[p] < 0)))
                          .rolling(WIN).mean() for p in px.columns})
    onesided = (agree + newext) / 2.0

    # deepest counter-move inside the window, as a fraction of the total move
    starve = {}
    for p in px.columns:
        v = lp[p].values
        n = len(v)
        out = np.full(n, np.nan)
        for i in range(WIN, n):
            w = v[i - WIN:i + 1]
            tot = w[-1] - w[0]
            if not np.isfinite(tot) or tot == 0:
                continue
            if tot > 0:
                dd = np.max(np.maximum.accumulate(w) - w)
            else:
                dd = np.max(w - np.minimum.accumulate(w))
            out[i] = 1.0 - dd / abs(tot)
        starve[p] = out
    starve = pd.DataFrame(starve, index=px.index)
    return {k: v.shift(1) for k, v in
            dict(drift=drift, onesided=onesided, starve=starve).items()}


def acute_detector(px):
    """maxabsmove, reconstructed from crisis.py: largest single-pair daily move
    across the panel, in sigma. Broadcast to every pair -- it is a panel measure."""
    r = np.log(px.astype(float)).diff()
    z = r / r.rolling(VOLW).std()
    s = z.abs().max(axis=1)
    return pd.DataFrame({p: s for p in px.columns}, index=px.index).shift(1)


def group_mask(px, st, ep, cm):
    """-> frame of group labels per pair-day."""
    G = pd.DataFrame('other', index=px.index, columns=px.columns, dtype=object)
    tr = (st == 'trending').reindex(px.index).fillna(False)
    G[tr] = 'trending (not chronic)'
    G[cm.values[:, None] & np.ones((1, len(px.columns)), bool)] = 'acute'
    for _, e in ep.iterrows():
        cols = [p for p in px.columns if e.currency in p]
        m = (px.index >= e.start) & (px.index <= e.end)
        for c in cols:
            G.loc[m, c] = 'chronic'
    return G


def sep(det, G, mask, groups=GROUPS):
    """One-vs-rest separation of the detector across groups, in sd units."""
    d = pd.DataFrame({'g': G[mask].stack(), 'v': det[mask].stack()}).dropna()
    if d.g.nunique() < 2 or len(d) < 500:
        return {}
    sd = d.v.std()
    out = {}
    for g in groups:
        a, b = d[d.g == g].v, d[d.g != g].v
        if len(a) < 30 or len(b) < 30:
            continue
        out[g] = float((a.mean() - b.mean()) / sd)
    return out


def episode_table(det, px, ep, name):
    """One row per (pair, episode): the detector's mean reading inside it."""
    rows = []
    for _, e in ep.iterrows():
        cols = [p for p in px.columns if e.currency in p]
        m = (px.index >= e.start) & (px.index <= e.end)
        for c in cols:
            v = det[c][m].dropna()
            if len(v) < 30:
                continue
            rows.append(dict(detector=name, currency=e.currency,
                             macro_event=e.macro_event, pair=c,
                             start=e.start.date(), bars=int(m.sum()),
                             mean=float(v.mean())))
    return pd.DataFrame(rows)


def main():
    px, st, ep = load()
    cm, n_ev = crisis_mask(px.index)
    D = detectors(px)
    A = acute_detector(px)
    G = group_mask(px, st, ep, cm)
    allm = pd.Series(True, index=px.index)
    share = G.stack().value_counts(normalize=True)
    print('CHRONIC DETECTOR. %d episode rows, %d independent macro events.'
          % (len(ep), ep.macro_event.nunique()))
    print('  group shares of all pair-days: %s'
          % '  '.join('%s %.3f' % (k, v) for k, v in share.items()))

    print('\nPART 2/3 -- SEPARATION. The hard boundary is trending, not calm.')
    rows = []
    for name, det in D.items():
        s = sep(det, G, allm)
        print('  %-9s %s' % (name, '  '.join('%s %+.3f' % (g, s.get(g, np.nan))
                                             for g in GROUPS)))
        for g in GROUPS:
            rows.append(dict(detector=name, group=g, sep=s.get(g, np.nan)))
    s = sep(A, G, allm)
    print('  %-9s %s' % ('acute', '  '.join('%s %+.3f' % (g, s.get(g, np.nan))
                                            for g in GROUPS)))
    for g in GROUPS:
        rows.append(dict(detector='acute maxabsmove', group=g, sep=s.get(g, np.nan)))
    S = pd.DataFrame(rows)

    # choose on IS, then read the rest -- with the caveat that the EPISODE LIST
    # cannot be split, only the bars
    isS = {k: sep(v, G, pd.Series(px.index < SPLIT, index=px.index))
           for k, v in D.items()}
    oosS = {k: sep(v, G, pd.Series(px.index >= SPLIT, index=px.index))
            for k, v in D.items()}
    print('\n  by block (bars split; the EPISODE LIST cannot be split -- see the')
    print('  .txt: 3 of 6 rows a side)')
    print('  %-9s %9s %9s' % ('detector', 'IS chronic', 'OOS chronic'))
    for k in D:
        print('  %-9s %+9.3f %+9.3f'
              % (k, isS[k].get('chronic', np.nan), oosS[k].get('chronic', np.nan)))
        S.loc[len(S)] = dict(detector=k, group='chronic IS',
                             sep=isS[k].get('chronic', np.nan))
        S.loc[len(S)] = dict(detector=k, group='chronic OOS',
                             sep=oosS[k].get('chronic', np.nan))
    # THE SELECTION MUST BE MADE ON THE HARD BOUNDARY, NOT THE DILUTED ONE.
    # Chronic-versus-everything is 61% "other", which is quiet market, and any
    # trend measure wins that comparison without saying anything. The number
    # that matters is chronic against ORDINARY TRENDING.
    def boundary(det):
        dd = pd.DataFrame({'g': G.stack(), 'v': det.stack()}).dropna()
        dd = dd[dd.g.isin(['chronic', 'trending (not chronic)'])]
        if dd.g.nunique() < 2 or len(dd) < 500:
            return np.nan
        a, b = dd[dd.g == 'chronic'].v, dd[dd.g != 'chronic'].v
        return float((a.mean() - b.mean()) / dd.v.std())
    print('\n  THE HARD BOUNDARY -- chronic against ORDINARY TRENDING only')
    for k, det in D.items():
        dd = pd.DataFrame({'g': G.stack(), 'v': det.stack()}).dropna()
        dd = dd[dd.g.isin(['chronic', 'trending (not chronic)'])]
        print('    %-9s chronic %8.3f  trending %8.3f  gap %+.3f sd'
              % (k, dd[dd.g == 'chronic'].v.mean(),
                 dd[dd.g != 'chronic'].v.mean(), boundary(det)))
        S.loc[len(S)] = dict(detector=k, group='BOUNDARY chronic vs trending',
                             sep=boundary(det))
    BEST = max(D, key=lambda k: abs(boundary(D[k])) if np.isfinite(boundary(D[k]))
               else 0)
    print('  CHOSEN on the hard boundary: %s (gap %+.3f sd)'
          % (BEST, boundary(D[BEST])))
    print('  NOTE the vs-everything metric would have chosen "drift" instead --')
    print('  61%% of that comparison is quiet market, which any trend measure wins.')

    print('\n  WHAT A DRIFT READING MEANS. A random walk sits at ~1.00.')
    dd = pd.DataFrame({'g': G.stack(), 'v': D['drift'].stack()}).dropna()
    for g, v in dd.groupby('g').v.mean().items():
        print('    %-24s %.3f' % (g, v))
    print('    -> chronic episodes read 1.037, essentially A RANDOM WALK.')
    print('    Everything else reads BELOW 1 because FX mean-reverts. So the')
    print('    separation is not "chronic is unusually persistent" -- it is')
    print('    "everything else is unusually mean-reverting". Weaker claim.')

    print('\n  NULL -- %d circular shifts of the EPISODE WINDOWS' % NSHIFT)
    n = len(px.index)
    rng = np.random.default_rng(2021)
    acc, accb = [], []
    for i in range(NSHIFT):
        k = int(rng.integers(MINOFF, n - MINOFF))
        ep2 = ep.copy()
        idx = px.index
        def sh(t):
            j = (idx.searchsorted(t) + k) % n
            return idx[j]
        ep2['start'] = ep2.start.map(sh)
        ep2['end'] = ep2.start + (ep.end - ep.start).values
        G2 = group_mask(px, st, ep2, cm)
        s2 = sep(D[BEST], G2, allm)
        if 'chronic' in s2:
            acc.append(s2['chronic'])
        dd2 = pd.DataFrame({'g': G2.stack(), 'v': D[BEST].stack()}).dropna()
        dd2 = dd2[dd2.g.isin(['chronic', 'trending (not chronic)'])]
        if dd2.g.nunique() == 2 and len(dd2) > 500:
            accb.append(float((dd2[dd2.g == 'chronic'].v.mean()
                               - dd2[dd2.g != 'chronic'].v.mean()) / dd2.v.std()))
        if (i + 1) % 25 == 0:
            print('    ... %d/%d' % (i + 1, NSHIFT), flush=True)
    real = sep(D[BEST], G, allm)['chronic']
    real_b = boundary(D[BEST])
    v = np.array(acc, float); v = v[np.isfinite(v)]
    rank = int((np.abs(v) >= abs(real)).sum()) + 1
    print('    real %+.4f | null %+.4f +/- %.4f over %d | rank %d of %d | p=%.3f'
          % (real, v.mean(), v.std(), len(v), rank, len(v) + 1,
             rank / (len(v) + 1)))
    S.loc[len(S)] = dict(detector=BEST, group='chronic NULL real', sep=real)
    S.loc[len(S)] = dict(detector=BEST, group='chronic NULL mean', sep=v.mean())
    S.loc[len(S)] = dict(detector=BEST, group='chronic NULL p',
                         sep=rank / (len(v) + 1))
    vb = np.array(accb, float); vb = vb[np.isfinite(vb)]
    rb = int((np.abs(vb) >= abs(real_b)).sum()) + 1
    print('    BOUNDARY real %+.4f | null %+.4f +/- %.4f over %d | rank %d of %d'
          ' | p=%.3f' % (real_b, vb.mean(), vb.std(), len(vb), rb, len(vb) + 1,
                         rb / (len(vb) + 1)))
    S.loc[len(S)] = dict(detector=BEST, group='BOUNDARY NULL real', sep=real_b)
    S.loc[len(S)] = dict(detector=BEST, group='BOUNDARY NULL p',
                         sep=rb / (len(vb) + 1))
    S.to_csv(os.path.join(ROOTOUT, 'chronic_separation.csv'), index=False)

    print('\n  CROSS-CHECK -- do the two alarms fire on each other?')
    ce = pd.read_csv(EPI, parse_dates=['start', 'end'])
    acute_on_chronic = sep(A, G, allm).get('chronic', np.nan)
    chronic_on_acute = sep(D[BEST], G, allm).get('acute', np.nan)
    print('    acute detector on CHRONIC episodes   %+.3f' % acute_on_chronic)
    print('    chronic detector on ACUTE episodes   %+.3f' % chronic_on_acute)
    print('    chronic detector on CHRONIC episodes %+.3f' % real)
    print('    acute detector on ACUTE episodes     %+.3f'
          % sep(A, G, allm).get('acute', np.nan))

    ET = pd.concat([episode_table(D[BEST], px, ep, BEST),
                    episode_table(A, px, ep, 'acute maxabsmove')],
                   ignore_index=True)
    ET.to_csv(os.path.join(ROOTOUT, 'chronic_detector.csv'), index=False)
    print('\n  PER EPISODE, %s (the JPY anchor case first)' % BEST)
    for ev in ep.macro_event.unique():
        d = ET[(ET.detector == BEST) & (ET.macro_event == ev)]
        a = ET[(ET.detector == 'acute maxabsmove') & (ET.macro_event == ev)]
        if len(d):
            print('    %-20s chronic %.3f   acute %.3f   (%d pairs)'
                  % (ev, d['mean'].mean(), a['mean'].mean() if len(a) else np.nan,
                     len(d)))

    hdr(os.path.join(ROOTOUT, 'chronic_separation.csv'),
        'Chronic detector -- separation and boundaries',
        'Groups: chronic (news-dated windows, affected pairs), TRENDING BUT NOT\n'
        'CHRONIC -- the hard boundary, because chronic IS a trend -- acute (the\n'
        '54-event forward windows) and everything else.\n\n'
        'Rows tagged "chronic IS" / "chronic OOS" split the BARS. The EPISODE\n'
        'LIST cannot be split: 3 of 6 rows start before 2016 and 3 after, which\n'
        'leaves 2-3 independent events a side. No holdout claim is made.\n\n'
        'The null circularly shifts the episode WINDOWS in time, preserving\n'
        'their number and length, and recomputes the separation.')
    hdr(os.path.join(ROOTOUT, 'chronic_detector.csv'),
        'Chronic detector -- reading per pair-episode',
        'One row per (pair, episode, detector): the mean reading inside the\n'
        'news-dated window. The acute detector (maxabsmove, reconstructed from\n'
        'crisis.py) is included on the same episodes so the two alarms can be\n'
        'checked against each other.')
    print('\nwrote chronic_detector.csv, chronic_separation.csv + .txt')


if __name__ == '__main__':
    main()
