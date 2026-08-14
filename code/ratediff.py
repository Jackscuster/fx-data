import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Rate differential MOMENTUM against regime shape. A separate output.

THE LEVEL WAS ALREADY TESTED AND GAVE NOTHING -- a 5.5% spread in the
differential produced a 0.1% behavioural difference. This tests the CHANGE, which
never has been.

THIS DOES NOT TOUCH THE SHAPE OR ACTIVITY SCORES. The classifier is read, never
modified. Description and prediction stay apart: question 1 is present-tense
association, question 2 is a lead test, and they are reported separately and
never averaged together.

CONSTRUCTION, DECLARED UPFRONT, NO SEARCHING.

  differential = base 2-year yield minus quote 2-year yield
  momentum     = change in that differential over W bars
  W in (5, 21, 63) -- a week, one median state run, a quarter. THAT IS THE ENTIRE
  MENU. The winner is picked on IS and confirmed once on OOS.

THREE FACTS ABOUT THE DATA, none of which were in the brief and all of which
change what the test can cover:

  1 rates2y.csv starts 1998-06-01, not 1990. That still covers IS from
    1999-01-01, so nothing is lost, but the span is 28 years not 36.
  2 NZD HAS NO DATA AT ALL -- the column exists and is entirely empty. Seven
    pairs are therefore not constructible: EURNZD, GBPNZD, AUDNZD, NZDUSD,
    NZDCAD, NZDCHF, NZDJPY. The test runs on 21 pairs, not 28, and every count
    in the output says 21.
  3 CAD starts 2001-01-02 and CHF ends 2025-07-31, so CAD pairs lose the first
    two years of IS and CHF pairs the last year of OOS. Coverage is reported per
    pair rather than assumed uniform.

EVERYTHING IS LAGGED ONE BAR. The momentum read at bar t uses yields through
t-1, and the transition read in question 2 uses the value at t-1, so it sees
yields through t-2 -- strictly before the bar the state changes on.

EPISODE-BASED SIGNIFICANCE. One state run is one observation. A 40-bar trending
episode contributes a single agree/disagree, not forty.

THE NULL circularly shifts the yield panel against price. Both series keep their
own internal behaviour -- persistence, drift, volatility clustering -- and only
the alignment between them is broken, which is exactly the thing being tested.

Writes results/ratediff_momentum_{q1,q2,null,pairs,coverage}.csv, each with a
.txt companion.
"""
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
RT = os.path.join(ROOTDATA, 'rates2y.csv')
ST = os.path.join(ROOTOUT, 'states_g4_twoscore4.csv')
SPLIT = pd.Timestamp('2016-01-01')
WINDOWS = (5, 21, 63)
FFILL = 10
NSHIFT = int(os.environ.get('FX_NSHIFT', 50))
MINOFF = 1000
MIN_EP = 5


def load():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    rt = pd.read_csv(RT, index_col=0, parse_dates=True)
    st = pd.read_csv(ST, index_col=0, parse_dates=True, comment='#')
    rt = rt.reindex(px.index).ffill(limit=FFILL)
    pairs = [p for p in px.columns
             if rt[p[:3]].notna().sum() > 100 and rt[p[3:]].notna().sum() > 100]
    return px, rt, st, pairs


def differential(rt, pairs):
    return pd.DataFrame({p: rt[p[:3]] - rt[p[3:]] for p in pairs})


def momentum(diff, W):
    """Change in the differential over W bars, then lagged one."""
    return (diff - diff.shift(W)).shift(1)


def episodes(st, px, mom, pairs, mask, state):
    """One row per state run: direction of the price move, sign of momentum."""
    lp = np.log(px.astype(float))
    out = []
    for p in pairs:
        v = st[p].where(mask).dropna()
        if len(v) < 50:
            continue
        gid = (v != v.shift()).cumsum()
        for _, g in v.groupby(gid):
            if g.iloc[0] != state or len(g) < MIN_EP:
                continue
            a, b = g.index[0], g.index[-1]
            if a not in lp.index or b not in lp.index:
                continue
            move = lp[p].loc[b] - lp[p].loc[a]
            m = mom[p].loc[a:b]
            m = m[m.notna()]
            if not len(m) or not np.isfinite(move) or move == 0:
                continue
            out.append(dict(pair=p, start=a, end=b, bars=len(g),
                            move=float(move), mom=float(m.mean()),
                            agree=int(np.sign(move) == np.sign(m.mean()))))
    return pd.DataFrame(out)


def q1(st, px, mom, pairs, mask):
    """Agreement by state, episode-based."""
    rows = {}
    for state in ('trending', 'ranging', 'trend-in-range', 'neither'):
        E = episodes(st, px, mom, pairs, mask, state)
        rows[state] = E
    return rows


def transitions(st, px, mom, pairs, mask, W, rng=None, n_ctrl=1):
    """Question 2. Momentum at t-1 against the direction of the episode from t."""
    lp = np.log(px.astype(float))
    real, ctrl = [], []
    for p in pairs:
        v = st[p].where(mask).dropna()
        if len(v) < 100:
            continue
        idx = v.index
        gid = (v != v.shift()).cumsum()
        runs = [(g.index[0], g.index[-1], g.iloc[0]) for _, g in v.groupby(gid)]
        starts = {a: (b, s) for a, b, s in runs}
        pos = {d: i for i, d in enumerate(idx)}
        for a, b, s in runs:
            if s != 'trending' or (b - a).days < 1:
                continue
            i = pos[a]
            if i == 0:
                continue
            prev = idx[i - 1]
            m = mom[p].get(prev, np.nan)
            move = lp[p].loc[b] - lp[p].loc[a]
            if not np.isfinite(m) or not np.isfinite(move) or move == 0 or m == 0:
                continue
            real.append(dict(pair=p, date=a, bars=len(v.loc[a:b]),
                             mom_prev=float(m), move=float(move),
                             agree=int(np.sign(m) == np.sign(move))))
            # matched control: a random bar that is NOT a transition, with the
            # same forward horizon, read the same way
            if rng is None:
                continue
            for _ in range(n_ctrl):
                for _try in range(20):
                    j = int(rng.integers(1, len(idx) - len(v.loc[a:b]) - 1))
                    d0 = idx[j]
                    if d0 in starts:
                        continue
                    d1 = idx[min(j + len(v.loc[a:b]) - 1, len(idx) - 1)]
                    m2 = mom[p].get(idx[j - 1], np.nan)
                    mv2 = lp[p].loc[d1] - lp[p].loc[d0]
                    if not np.isfinite(m2) or not np.isfinite(mv2) \
                       or mv2 == 0 or m2 == 0:
                        continue
                    ctrl.append(dict(pair=p, date=d0, mom_prev=float(m2),
                                     move=float(mv2),
                                     agree=int(np.sign(m2) == np.sign(mv2))))
                    break
    return pd.DataFrame(real), pd.DataFrame(ctrl)


def hdr(path, title, body):
    with open(path.replace('.csv', '.txt'), 'w') as f:
        f.write('%s\n%s\n\n%s\n' % (title, '=' * len(title), body))


def main():
    px, rt, st, pairs = load()
    fit = px.index < SPLIT
    m_is = pd.Series(fit, index=px.index)
    m_oos = ~m_is
    diff = differential(rt, pairs)
    print('RATE DIFFERENTIAL MOMENTUM. %d pairs (NZD has no yield data).'
          % len(pairs))

    cov = pd.DataFrame({'pair': pairs,
                        'diff_coverage': [diff[p].notna().mean() for p in pairs],
                        'first': [diff[p].dropna().index.min() for p in pairs],
                        'last': [diff[p].dropna().index.max() for p in pairs]})
    cov.to_csv(os.path.join(ROOTOUT, 'ratediff_momentum_coverage.csv'),
               index=False)
    hdr(os.path.join(ROOTOUT, 'ratediff_momentum_coverage.csv'),
        'Rate differential coverage, per pair',
        'Share of price bars with a differential available after a %d-bar '
        'forward fill, and the first and last date each pair has one.\n\n'
        'NZD has NO 2-year yield data at all, so its seven pairs are absent '
        'entirely. CAD starts 2001-01-02 and CHF ends 2025-07-31.' % FFILL)

    # ---------------- QUESTION 1 ----------------
    print('\nQUESTION 1 -- PRESENT-TENSE ASSOCIATION, episode-based')
    print('  does the sign of differential momentum match the price move?')
    rows = []
    for W in WINDOWS:
        mom = momentum(diff, W)
        for tag, mask in (('is', m_is), ('oos', m_oos)):
            E = q1(st, px, mom, pairs, mask)
            allE = pd.concat([v for v in E.values() if len(v)], ignore_index=True)
            base = allE.agree.mean() if len(allE) else np.nan
            for state, d in E.items():
                if not len(d):
                    continue
                rows.append(dict(W=W, block=tag, state=state, episodes=len(d),
                                 agree=float(d.agree.mean()),
                                 base_all_states=float(base),
                                 excess=float(d.agree.mean() - base)))
    Q1 = pd.DataFrame(rows)
    Q1.to_csv(os.path.join(ROOTOUT, 'ratediff_momentum_q1.csv'), index=False)
    print('  %3s %5s %-16s %8s %8s %9s %9s'
          % ('W', 'block', 'state', 'episodes', 'agree', 'base', 'excess'))
    for _, r in Q1[Q1.state.isin(['trending', 'ranging'])].iterrows():
        print('  %3d %5s %-16s %8d %8.3f %9.3f %+9.3f'
              % (r.W, r.block, r.state, r.episodes, r.agree,
                 r.base_all_states, r.excess))

    # choose W on IS only
    isT = Q1[(Q1.block == 'is') & (Q1.state == 'trending')]
    BEST = int(isT.sort_values('excess', ascending=False).W.iloc[0])
    print('\n  CHOSEN ON IS: W=%d (excess %+.3f over the all-state base)'
          % (BEST, isT[isT.W == BEST].excess.iloc[0]))
    oosT = Q1[(Q1.block == 'oos') & (Q1.state == 'trending') & (Q1.W == BEST)]
    print('  HOLDOUT, read once: agree %.3f, base %.3f, excess %+.3f (%d episodes)'
          % (oosT.agree.iloc[0], oosT.base_all_states.iloc[0],
             oosT.excess.iloc[0], oosT.episodes.iloc[0]))
    hdr(os.path.join(ROOTOUT, 'ratediff_momentum_q1.csv'),
        'Question 1 -- present-tense association',
        'One row per (window, block, state). EPISODE-BASED: one state run is one\n'
        'observation, so a 40-bar trending episode contributes a single\n'
        'agree/disagree rather than forty.\n\n'
        'agree  = share of episodes where sign(price move over the episode)\n'
        '         matches sign(mean differential momentum during it)\n'
        'base_all_states = the same share pooled over episodes of EVERY state,\n'
        '         which is the honest baseline -- 0.50 is not, because price and\n'
        '         yields both drift\n'
        'excess = agree minus base\n\n'
        'W was chosen on IS only (W=%d) and the holdout read once.' % BEST)

    # per pair at the chosen W
    mom = momentum(diff, BEST)
    prow = []
    for tag, mask in (('is', m_is), ('oos', m_oos)):
        E = q1(st, px, mom, pairs, mask)
        allE = pd.concat([v for v in E.values() if len(v)], ignore_index=True)
        for p in pairs:
            t = E['trending'][E['trending'].pair == p] if len(E['trending']) \
                else pd.DataFrame()
            b = allE[allE.pair == p]
            if len(t) < 3 or len(b) < 5:
                continue
            prow.append(dict(pair=p, block=tag, W=BEST, episodes=len(t),
                             agree=float(t.agree.mean()),
                             base=float(b.agree.mean()),
                             excess=float(t.agree.mean() - b.agree.mean())))
    P = pd.DataFrame(prow)
    P.to_csv(os.path.join(ROOTOUT, 'ratediff_momentum_pairs.csv'), index=False)
    o = P[P.block == 'oos']
    print('\n  PER PAIR, holdout, W=%d: %d of %d pairs positive, median excess %+.3f'
          % (BEST, int((o.excess > 0).sum()), len(o), o.excess.median()))
    hdr(os.path.join(ROOTOUT, 'ratediff_momentum_pairs.csv'),
        'Question 1 per pair, at the IS-chosen window',
        'Trending-episode agreement against that pair\'s own all-state base.\n'
        'Pairs with fewer than 3 trending episodes in a block are omitted.\n'
        'NZD pairs are absent: no 2-year yield data exists for NZD.')

    # ---------------- QUESTION 2 ----------------
    print('\nQUESTION 2 -- LEAD into trending')
    rng = np.random.default_rng(20260814)
    q2rows = []
    for tag, mask in (('is', m_is), ('oos', m_oos)):
        Rl, Ct = transitions(st, px, mom, pairs, mask, BEST, rng, n_ctrl=3)
        q2rows.append(dict(block=tag, W=BEST, kind='transition into trending',
                           n=len(Rl), agree=float(Rl.agree.mean()) if len(Rl) else np.nan))
        q2rows.append(dict(block=tag, W=BEST, kind='matched non-transition bars',
                           n=len(Ct), agree=float(Ct.agree.mean()) if len(Ct) else np.nan))
    Q2 = pd.DataFrame(q2rows)
    Q2['excess'] = np.nan
    for tag in ('is', 'oos'):
        a = Q2[(Q2.block == tag) & (Q2.kind.str.startswith('transition'))].agree.iloc[0]
        b = Q2[(Q2.block == tag) & (Q2.kind.str.startswith('matched'))].agree.iloc[0]
        Q2.loc[(Q2.block == tag) & (Q2.kind.str.startswith('transition')),
               'excess'] = a - b
    Q2.to_csv(os.path.join(ROOTOUT, 'ratediff_momentum_q2.csv'), index=False)
    for _, r in Q2.iterrows():
        print('  %-4s %-32s n=%5d  agree %.3f%s'
              % (r.block, r.kind, r.n, r.agree,
                 '   excess %+.3f' % r.excess if np.isfinite(r.excess) else ''))
    hdr(os.path.join(ROOTOUT, 'ratediff_momentum_q2.csv'),
        'Question 2 -- lead into trending',
        'At each transition INTO trending, the differential momentum read at the\n'
        'bar BEFORE the change. Momentum is already lagged one bar, so that value\n'
        'uses yields through t-2 -- strictly before the bar the state changes on.\n\n'
        'Direction is the sign of the price move over the trending episode that\n'
        'follows, which is forward-looking BY DESIGN: this is the lead test, and\n'
        'it is reported separately from question 1 for exactly that reason.\n\n'
        'The control draws non-transition bars with the same forward horizon and\n'
        'reads them identically, three per transition.')

    # ---------------- NULL ----------------
    print('\nNULL -- circular shift of the yield panel against price, %d shifts'
          % NSHIFT)
    n = len(px.index)
    rngN = np.random.default_rng(4242)
    # BOTH states are nulled. Trending is the question that was asked; ranging
    # showed a positive excess in all six (window x block) cells and reporting
    # a consistent pattern without testing it would be the same mistake this
    # project keeps catching elsewhere.
    real = {}
    for tag in ('is', 'oos'):
        for state in ('trending', 'ranging'):
            r = Q1[(Q1.block == tag) & (Q1.state == state) & (Q1.W == BEST)]
            real[(tag, state)] = float(r.excess.iloc[0]) if len(r) else np.nan
    acc = {k: [] for k in real}
    for i in range(NSHIFT):
        k = int(rngN.integers(MINOFF, n - MINOFF))
        d2 = pd.DataFrame(np.roll(diff.values, k, axis=0), index=diff.index,
                          columns=diff.columns)
        m2 = momentum(d2, BEST)
        for tag, mask in (('is', m_is), ('oos', m_oos)):
            E = q1(st, px, m2, pairs, mask)
            allE = pd.concat([v for v in E.values() if len(v)], ignore_index=True)
            if not len(allE):
                continue
            for state in ('trending', 'ranging'):
                t = E[state]
                if len(t):
                    acc[(tag, state)].append(
                        float(t.agree.mean() - allE.agree.mean()))
        if (i + 1) % 10 == 0:
            print('  ... %d/%d shifts' % (i + 1, NSHIFT), flush=True)
    nrows = []
    for (tag, state), rv in sorted(real.items()):
        v = np.array(acc[(tag, state)], float); v = v[np.isfinite(v)]
        if not len(v) or not np.isfinite(rv):
            continue
        rank = int((v >= rv).sum())
        nrows.append(dict(block=tag, W=BEST, statistic='%s excess' % state,
                          real=rv, n_shifts=len(v), null_mean=float(v.mean()),
                          null_sd=float(v.std()), n_null_ge_real=rank,
                          rank_of_real=rank + 1,
                          p=(1 + rank) / (len(v) + 1)))
        print('  %-4s %-9s real %+.4f | null %+.4f +/- %.4f over %d shifts | '
              'rank %d of %d | p=%.3f'
              % (tag, state, rv, v.mean(), v.std(), len(v), rank + 1,
                 len(v) + 1, (1 + rank) / (len(v) + 1)))
    N = pd.DataFrame(nrows)
    N.to_csv(os.path.join(ROOTOUT, 'ratediff_momentum_null.csv'), index=False)
    hdr(os.path.join(ROOTOUT, 'ratediff_momentum_null.csv'),
        'Null -- circular shift of yields against price',
        'The yield panel is rolled by a random offset of at least %d bars and\n'
        'the whole statistic recomputed. Both series keep their own internal\n'
        'behaviour and only the ALIGNMENT between them is broken, which is the\n'
        'thing being tested.\n\n'
        'n_shifts is the exact draw count actually used, not a target.\n'
        'rank_of_real is where the real number sits among (nulls + itself),\n'
        '1 being the largest.' % MINOFF)
    print('\nwrote ratediff_momentum_{coverage,q1,pairs,q2,null}.csv + .txt')


if __name__ == '__main__':
    main()
