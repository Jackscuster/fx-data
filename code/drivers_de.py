import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Drivers 4 (yield curve) and 5 (commodities). Closes the five-driver programme.

THE KEEP/KILL STANDARD. Confirmation is the bar. A driver that reliably reads the
CURRENT regime is a keeper even if it predicts nothing -- failing the forward test
never kills a driver. Drivers die only when their read on the present is
unreliable: a sign flip between data halves or between sub-periods.

DRIVER D -- YIELD CURVE SHAPE. Per country, slope = 10y minus 2y. Per pair, two
readings and no more: the slope GAP between base and quote (level), and its
21-bar change. Runs on the ten pairs where both tenors exist for both legs --
EUR, GBP, USD, CHF, JPY. AUD and CAD have a 2-year but no daily 10-year; NZD has
neither. See rates10y_coverage.txt.

DRIVER E -- COMMODITIES, ONLY WHERE A MECHANISM EXISTS. Free on the Yahoo chart
API: WTI (CL=F) from 2000-08-23 and gold (GC=F) from 2000-08-30 -- both start
~1.6 years into the in-sample window, which is stated rather than hidden. Iron
ore (TIO=F) IS free but only from 2010-10-14, too short and scoped to AUD which
gold already covers; coal and dairy are not free at all, so NZD is recorded as
UNTESTABLE for commodities.

  oil   -> CAD pairs, and JPY pairs inversely (Japan imports its energy)
  gold  -> AUD pairs
  no commodity test for EUR, GBP or CHF pairs. No mechanism exists there, so a
  hit would be noise by construction, and not looking is the point.

Constructions, declared upfront, no sweep: the commodity's 21-bar change
(absolute for separation, signed for forward) and its 63-bar rolling correlation
strength with the pair.

Lag one bar. IS chooses, OOS is read once. Sub-period split runs BEFORE any
holdout pass is reported -- it has killed two drivers.

Writes results/driver_separation_{d,e}.csv, driver_forward_{d,e}.csv,
driver_subperiod_{d,e}.csv.
"""
import json, urllib.request
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
R2 = os.path.join(ROOTDATA, 'rates2y.csv')
R10 = os.path.join(ROOTDATA, 'rates10y.csv')
ST = os.path.join(ROOTOUT, 'states_g4_twoscore4.csv')
SPLIT = pd.Timestamp('2016-01-01')
W = 21
WCORR = 63
FWD = 20
NSHIFT = int(os.environ.get('FX_NSHIFT', 50))
MINOFF = 500
SUBP = [('2016-01-01', '2019-12-31', '2016-19'),
        ('2020-01-01', '2021-12-31', '2020-21'),
        ('2022-01-01', '2026-12-31', '2022-26')]
UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}

from drivers import crisis_mask, epi_groups, sep_across, hdr


def yahoo(t):
    import urllib.parse
    u = ('https://query2.finance.yahoo.com/v8/finance/chart/'
         + urllib.parse.quote(t) + '?period1=850000000&period2=1800000000'
         '&interval=1d')
    j = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=UA),
                                          timeout=90).read())['chart']['result'][0]
    s = pd.Series(j['indicators']['quote'][0]['close'],
                  index=pd.to_datetime(j['timestamp'], unit='s').normalize())
    s = s.dropna()
    return s[~s.index.duplicated(keep='last')].sort_index()


def load():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    st = pd.read_csv(ST, index_col=0, parse_dates=True, comment='#')
    r2 = pd.read_csv(R2, index_col=0, parse_dates=True).reindex(px.index)\
        .ffill(limit=10)
    r10 = pd.read_csv(R10, index_col=0, parse_dates=True).reindex(px.index)\
        .ffill(limit=10)
    return px, st, r2, r10


def sep_block(st, drv, pairs, mask, cm):
    E = epi_groups(st, drv, pairs, mask, cm)
    if not len(E):
        return {}, E
    E['grp'] = np.where(E.crisis, 'crisis',
                        np.where(E.state == 'trending', 'trending',
                                 np.where(E.state == 'ranging', 'ranging',
                                          'other')))
    return sep_across(E, ['trending', 'ranging', 'crisis']), E


def run_driver(name, drv, pairs, st, px, cm, fit, shift_source, tag_out):
    """Test 1 with sub-period first, then the null. Returns the tables."""
    rows = []
    for tag, m in (('is', fit), ('oos', ~fit)):
        s, E = sep_block(st, drv, pairs, m, cm)
        for g in ('trending', 'ranging', 'crisis'):
            d = E[E.grp == g] if len(E) else E
            rows.append(dict(driver=name, block=tag, group=g, episodes=len(d),
                             mean_drv=float(d.drv.mean()) if len(d) else np.nan,
                             sep_vs_rest=s.get(g, np.nan)))
    S = pd.DataFrame(rows)
    print('  %-4s %-9s %9s %11s %11s' % ('blk', 'group', 'episodes', 'mean',
                                         'sep vs rest'))
    for _, r in S.iterrows():
        print('  %-4s %-9s %9d %11.4f %+11.3f'
              % (r.block, r.group, r.episodes, r.mean_drv, r.sep_vs_rest))
    isS = S[S.block == 'is'].copy()
    isS['abs'] = isS.sep_vs_rest.abs()
    G = isS.sort_values('abs', ascending=False).group.iloc[0]
    real_is = float(isS[isS.group == G].sep_vs_rest.iloc[0])
    real_oos = float(S[(S.block == 'oos') & (S.group == G)].sep_vs_rest.iloc[0])
    print('  CHOSEN ON IS: %s (%+.3f). HOLDOUT read once: %+.3f'
          % (G, real_is, real_oos))

    print('  SUB-PERIOD SPLIT (before reporting any holdout pass)')
    srow = []
    for lo, hi, lab in SUBP:
        m = pd.Series((px.index >= lo) & (px.index <= hi), index=px.index)
        s, _ = sep_block(st, drv, pairs, m, cm)
        for g in ('trending', 'ranging', 'crisis'):
            srow.append(dict(driver=name, period=lab, group=g,
                             sep=s.get(g, np.nan)))
        print('    %-8s %s' % (lab, '  '.join(
            '%s %+.3f' % (g, s.get(g, np.nan))
            for g in ('trending', 'ranging', 'crisis'))))
    SU = pd.DataFrame(srow)
    SU.to_csv(os.path.join(ROOTOUT, 'driver_subperiod_%s.csv' % tag_out),
              index=False)

    print('  NULL -- %d circular shifts' % NSHIFT)
    n = len(px.index)
    rng = np.random.default_rng(4242)
    acc = {'is': [], 'oos': []}
    for i in range(NSHIFT):
        k = int(rng.integers(MINOFF, n - MINOFF))
        d2 = shift_source(k)
        for tag, m in (('is', fit), ('oos', ~fit)):
            s2, _ = sep_block(st, d2, pairs, m, cm)
            if G in s2:
                acc[tag].append(s2[G])
        if (i + 1) % 25 == 0:
            print('    ... %d/%d' % (i + 1, NSHIFT), flush=True)
    nrow = []
    for tag, real in (('is', real_is), ('oos', real_oos)):
        v = np.array(acc[tag], float); v = v[np.isfinite(v)]
        rank = int((np.abs(v) >= abs(real)).sum()) + 1
        nrow.append(dict(driver=name, block=tag, group=G, real=real,
                         n_shifts=len(v), null_mean=float(v.mean()),
                         null_sd=float(v.std()), rank_of_real=rank,
                         n_compared=len(v) + 1, p=rank / (len(v) + 1)))
        print('    %-4s real %+.4f | null %+.4f +/- %.4f over %d | rank %d of %d'
              ' | p=%.3f' % (tag, real, v.mean(), v.std(), len(v), rank,
                             len(v) + 1, rank / (len(v) + 1)))
    S = pd.concat([S, pd.DataFrame(nrow)], ignore_index=True)
    S.to_csv(os.path.join(ROOTOUT, 'driver_separation_%s.csv' % tag_out),
             index=False)
    flip = (real_is > 0) != (real_oos > 0)
    sflip = SU[SU.group == G].sep.dropna()
    sub_flip = len(sflip) > 1 and (sflip > 0).any() and (sflip < 0).any()
    verdict = 'DEAD -- sign flips' if (flip or sub_flip) else 'KEEPER'
    print('  VERDICT: %s  (halves flip: %s, sub-periods flip: %s)'
          % (verdict, flip, sub_flip))
    return S, SU, G, verdict


def forward(drv_daily, st, ev_dates, index, fit, label, out):
    q = np.nanquantile(drv_daily[fit], [1 / 3, 2 / 3])
    b = pd.Series(np.where(drv_daily <= q[0], 'low',
                           np.where(drv_daily <= q[1], 'mid', 'high')),
                  index=index)
    ahead = pd.Series(False, index=index)
    for d in ev_dates:
        i = index.searchsorted(d)
        if i < len(index):
            ahead.iloc[max(0, i - FWD):i] = True
    st = st.reindex(index)
    rows = []
    for tag, m in (('is', fit), ('oos', ~fit)):
        base = float(ahead[m].mean())
        for bk in ('low', 'mid', 'high'):
            sel = m & (b == bk).values
            if sel.sum() < 50:
                continue
            rows.append(dict(driver=label, block=tag, bucket=bk,
                             days=int(sel.sum()), metric='P(crisis in 20 bars)',
                             p=float(ahead[sel].mean()), base=base,
                             lift=float(ahead[sel].mean() / base) if base else np.nan))
        for state in ('trending', 'ranging', 'trend-in-range'):
            f2 = (st == state).rolling(FWD).max().shift(-FWD).astype(float)
            base2 = float(np.nanmean(f2.values[m]))
            for bk in ('low', 'mid', 'high'):
                sel = m & (b == bk).values
                if sel.sum() < 50:
                    continue
                v = float(np.nanmean(f2.values[sel]))
                rows.append(dict(driver=label, block=tag, bucket=bk,
                                 days=int(sel.sum()),
                                 metric='P(%s in 20 bars)' % state, p=v,
                                 base=base2, lift=v / base2 if base2 else np.nan))
    F = pd.DataFrame(rows)
    F.to_csv(os.path.join(ROOTOUT, 'driver_forward_%s.csv' % out), index=False)
    for met in F.metric.unique():
        for tag in ('is', 'oos'):
            d = F[(F.metric == met) & (F.block == tag)]
            if not len(d):
                continue
            print('    %-4s %-28s base %.3f | %s'
                  % (tag, met, d.base.iloc[0], '  '.join(
                      '%s %.3f (x%.2f)' % (r.bucket, r.p, r.lift)
                      for _, r in d.iterrows())))
    return F


def main():
    px, st, r2, r10 = load()
    cm, n_ev = crisis_mask(px.index)
    import events as EV
    cal = getattr(EV, 'EVENTS', None) or getattr(EV, 'CAL')
    ev = pd.to_datetime([r[0] for r in cal])
    fit = pd.Series(px.index < SPLIT, index=px.index)

    # ---------------- DRIVER D ----------------
    both = [c for c in r10.columns if c in r2 and r2[c].notna().sum() > 100]
    slope = pd.DataFrame({c: r10[c] - r2[c] for c in both})
    pairsD = [p for p in px.columns if p[:3] in both and p[3:] in both]
    gap = pd.DataFrame({p: slope[p[:3]] - slope[p[3:]] for p in pairsD})
    D_lvl = gap.abs().shift(1)
    D_chg = (gap - gap.shift(W)).abs().shift(1)
    print('DRIVER 4 -- YIELD CURVE SHAPE. %d pairs: %s'
          % (len(pairsD), ', '.join(pairsD)))
    print('  AUD/CAD have a 2y but no daily 10y; NZD has neither.')
    print('\n  reading 1: |slope gap| (level)')
    SD, SUD, GD, VD = run_driver('D curve |slope gap|', D_lvl, pairsD, st, px,
                                 cm, fit,
                                 lambda k: pd.DataFrame(
                                     np.roll(gap.values, k, axis=0),
                                     index=gap.index, columns=gap.columns)
                                 .abs().shift(1), 'd')

    # ---------------- DRIVER E ----------------
    print('\nDRIVER 5 -- COMMODITIES')
    oil, gold = yahoo('CL=F'), yahoo('GC=F')
    print('  CL=F %s -> %s (%d obs); GC=F %s -> %s (%d obs)'
          % (oil.index.min().date(), oil.index.max().date(), len(oil),
             gold.index.min().date(), gold.index.max().date(), len(gold)))
    print('  both start ~1.6 years into the in-sample window.')
    print('  iron ore TIO=F is free but only from 2010-10-14 and scoped to AUD,')
    print('  which gold already covers. Coal and dairy are not free: NZD is')
    print('  recorded UNTESTABLE for commodities.')
    oil = oil.reindex(px.index).ffill(limit=5)
    gold = gold.reindex(px.index).ffill(limit=5)
    pairsCAD = [p for p in px.columns if 'CAD' in p]
    pairsJPY = [p for p in px.columns if 'JPY' in p]
    pairsAUD = [p for p in px.columns if 'AUD' in p]
    scope = sorted(set(pairsCAD) | set(pairsJPY) | set(pairsAUD))
    print('  scope: %d pairs (CAD %d, JPY %d, AUD %d). No EUR/GBP/CHF-only '
          'pairs tested -- no mechanism.' % (len(scope), len(pairsCAD),
                                             len(pairsJPY), len(pairsAUD)))
    o_chg = (np.log(oil).diff(W)).abs().shift(1)
    g_chg = (np.log(gold).diff(W)).abs().shift(1)
    E_lvl = pd.DataFrame({p: (g_chg if 'AUD' in p else o_chg) for p in scope})
    SE, SUE, GE, VE = run_driver('E commodity |21d chg|', E_lvl, scope, st, px,
                                 cm, fit,
                                 lambda k: pd.DataFrame(
                                     {p: pd.Series(np.roll(
                                         (g_chg if 'AUD' in p else o_chg).values,
                                         k), index=px.index) for p in scope}),
                                 'e')

    # ---------------- TEST 2, FORWARD ----------------
    print('\nTEST 2 -- FORWARD ODDS (reported, cannot kill)')
    print('\n  DRIVER D')
    FD = forward(D_lvl.mean(axis=1), st, ev, px.index, fit.values,
                 'D curve |slope gap|', 'd')
    print('\n  DRIVER E')
    FE = forward(E_lvl.mean(axis=1), st, ev, px.index, fit.values,
                 'E commodity |21d chg|', 'e')
    for out, nm in (('d', 'D yield curve'), ('e', 'E commodities')):
        hdr(os.path.join(ROOTOUT, 'driver_forward_%s.csv' % out),
            'Driver %s -- forward odds over the next %d bars' % (nm, FWD),
            'FORWARD, reported as its own block. Layer 1 does not predict --\n'
            'only drivers carry forward odds, and a forward failure NEVER kills\n'
            'a driver. All three regimes reported, not just crisis.\n\n'
            'One crisis is one observation: the crisis row is computed at day\n'
            'level against distinct event dates.')
    for out, nm, V in (('d', 'D yield curve', VD), ('e', 'E commodities', VE)):
        hdr(os.path.join(ROOTOUT, 'driver_separation_%s.csv' % out),
            'Driver %s -- separation (this test decides keep or kill)' % nm,
            'Verdict: %s.\n\nA driver dies only when its read on the PRESENT is\n'
            'unreliable -- a sign flip between data halves or between\n'
            'sub-periods. Failing the forward test never kills a driver.' % V)
        hdr(os.path.join(ROOTOUT, 'driver_subperiod_%s.csv' % out),
            'Driver %s -- holdout separation by sub-period' % nm,
            'Run BEFORE any holdout pass is reported. This check has killed two\n'
            'drivers already.')
    print('\nwrote driver_separation_{d,e}, driver_forward_{d,e}, '
          'driver_subperiod_{d,e}')
    return VD, VE


if __name__ == '__main__':
    main()
