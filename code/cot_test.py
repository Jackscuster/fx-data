import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Driver F -- CFTC positioning. The last untested free data source.

RUN ON THE SAME TERMS AS DRIVERS A-E, deliberately, so the answer is comparable:
episode-based counting, in-sample 1999-2015 chooses, holdout 2016-2026 read once,
circular-shift null with 50 draws, and the sub-period split of the holdout run
BEFORE any pass is reported. That split has now killed three drivers.

THE LAG. Built in cot.py and restated because it is the thing that fakes results
here. A COT report is TUESDAY positions published FRIDAY afternoon, and is
treated as usable from the following MONDAY: report_date + 6 calendar days, then
the standard one-bar shift on top. Seven calendar days from snapshot to first
usable bar. Using the report date would grant a five-day head start on a weekly
series.

COVERAGE, WHICH IS THE FIRST REAL LIMIT. CME FX futures are quoted against USD,
so this reaches 7 of 28 pairs and no cross at all. NZD stops being reported after
2022-02-01, so NZDUSD covers 65% of bars and none of the last four years. Six
currencies run 1999-2026.

THE READINGS, DECLARED, NO SWEEP. Two per currency, exactly as briefed:
  net    (noncommercial long - short) / open interest
  chg4   its 4-week change, differenced on the WEEKLY grid before forward-filling

SIGNED OR ABSOLUTE -- DECLARED BEFORE RUNNING, because it decides the answer.
The state labels carry NO DIRECTION: "trending" covers trending up and trending
down. A signed position averaged over trending episodes therefore cancels toward
zero by construction, and a null result would say nothing about positioning. So
SEPARATION IS RUN ON THE ABSOLUTE READINGS -- |net| is crowding, |chg4| is
positioning turnover -- and that is the primary keep/kill test. The signed
readings are run too and reported beside them, so the choice can be checked
rather than trusted; they are not the deciding number.

TEST 2 is forward odds. Reported, cannot kill. Includes one declared special
cell, stated before running: EXTREME positioning, the top decile of |net|,
against P(acute crisis within 20 bars) -- the crowded-trade hypothesis.

Writes results/cot_separation.csv, cot_forward.csv, cot_subperiod.csv + .txt.
"""
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
NET = os.path.join(ROOTDATA, 'cot.csv')
CH4 = os.path.join(ROOTDATA, 'cot_chg4.csv')
ST = os.path.join(ROOTOUT, 'states_g4_twoscore4.csv')
SPLIT = pd.Timestamp('2016-01-01')
FWD = 20
NSHIFT = int(os.environ.get('FX_NSHIFT', 50))
MINOFF = 500
SUBP = [('2016-01-01', '2019-12-31', '2016-19'),
        ('2020-01-01', '2021-12-31', '2020-21'),
        ('2022-01-01', '2026-12-31', '2022-26')]

from drivers import crisis_mask, epi_groups, sep_across, hdr
from cot import PAIRMAP, RELEASE_LAG_DAYS, MAX_STALE_DAYS


def load():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    st = pd.read_csv(ST, index_col=0, parse_dates=True, comment='#')
    net = pd.read_csv(NET, index_col=0, parse_dates=True).reindex(px.index)
    ch4 = pd.read_csv(CH4, index_col=0, parse_dates=True).reindex(px.index)
    # per pair, signed so that positive always means "long the pair as quoted"
    P = {}
    for pair, (c, sgn) in PAIRMAP.items():
        if c in net.columns and pair in px.columns:
            P[pair] = (net[c] * sgn, ch4[c] * sgn)
    pairs = sorted(P)
    N = pd.DataFrame({p: P[p][0] for p in pairs})
    C = pd.DataFrame({p: P[p][1] for p in pairs})
    return px, st, N, C, pairs


def sep_block(st, drv, pairs, mask, cm):
    E = epi_groups(st, drv, pairs, mask, cm)
    if not len(E):
        return {}, E
    E['grp'] = np.where(E.crisis, 'crisis',
                        np.where(E.state == 'trending', 'trending',
                                 np.where(E.state == 'ranging', 'ranging',
                                          'other')))
    return sep_across(E, ['trending', 'ranging', 'crisis']), E


def run_one(name, drv, pairs, st, px, cm, fit, primary):
    """Test 1 for one reading. Sub-period split runs before the holdout pass."""
    rows = []
    for tag, m in (('is', fit), ('oos', ~fit)):
        s, E = sep_block(st, drv, pairs, m, cm)
        for g in ('trending', 'ranging', 'crisis'):
            d = E[E.grp == g] if len(E) else E
            rows.append(dict(driver=name, primary=primary, block=tag, group=g,
                             episodes=len(d),
                             mean_drv=float(d.drv.mean()) if len(d) else np.nan,
                             sep_vs_rest=s.get(g, np.nan)))
    S = pd.DataFrame(rows)
    print('\n  %s   (%s)' % (name, 'PRIMARY' if primary else 'secondary'))
    print('    %-4s %-9s %9s %11s %11s'
          % ('blk', 'group', 'episodes', 'mean', 'sep vs rest'))
    for _, r in S.iterrows():
        print('    %-4s %-9s %9d %11.4f %+11.3f'
              % (r.block, r.group, r.episodes, r.mean_drv, r.sep_vs_rest))
    isS = S[S.block == 'is'].copy()
    isS['abs'] = isS.sep_vs_rest.abs()
    G = isS.sort_values('abs', ascending=False).group.iloc[0]
    real_is = float(isS[isS.group == G].sep_vs_rest.iloc[0])
    real_oos = float(S[(S.block == 'oos') & (S.group == G)].sep_vs_rest.iloc[0])
    print('    CHOSEN ON IS: %s (%+.3f). HOLDOUT read once: %+.3f'
          % (G, real_is, real_oos))

    srow = []
    print('    SUB-PERIOD SPLIT (before reporting any holdout pass)')
    for lo, hi, lab in SUBP:
        m = pd.Series((px.index >= lo) & (px.index <= hi), index=px.index)
        s, _ = sep_block(st, drv, pairs, m, cm)
        for g in ('trending', 'ranging', 'crisis'):
            srow.append(dict(driver=name, period=lab, group=g,
                             sep=s.get(g, np.nan)))
        print('      %-8s %s' % (lab, '  '.join(
            '%s %+.3f' % (g, s.get(g, np.nan))
            for g in ('trending', 'ranging', 'crisis'))))
    SU = pd.DataFrame(srow)

    print('    NULL -- %d circular shifts of the positioning panel' % NSHIFT)
    n = len(px.index)
    rng = np.random.default_rng(777)
    acc = {'is': [], 'oos': []}
    V = drv.values
    for i in range(NSHIFT):
        k = int(rng.integers(MINOFF, n - MINOFF))
        d2 = pd.DataFrame(np.roll(V, k, axis=0), index=drv.index,
                          columns=drv.columns)
        for tag, m in (('is', fit), ('oos', ~fit)):
            s2, _ = sep_block(st, d2, pairs, m, cm)
            if G in s2:
                acc[tag].append(s2[G])
        if (i + 1) % 25 == 0:
            print('      ... %d/%d' % (i + 1, NSHIFT), flush=True)
    nrow = []
    for tag, real in (('is', real_is), ('oos', real_oos)):
        v = np.array(acc[tag], float); v = v[np.isfinite(v)]
        rank = int((np.abs(v) >= abs(real)).sum()) + 1
        nrow.append(dict(driver=name, primary=primary, block=tag, group=G,
                         real=real, n_shifts=len(v), null_mean=float(v.mean()),
                         null_sd=float(v.std()), rank_of_real=rank,
                         n_compared=len(v) + 1, p=rank / (len(v) + 1)))
        print('      %-4s real %+.4f | null %+.4f +/- %.4f over %d | rank %d of'
              ' %d | p=%.3f' % (tag, real, v.mean(), v.std(), len(v), rank,
                                len(v) + 1, rank / (len(v) + 1)))
    S = pd.concat([S, pd.DataFrame(nrow)], ignore_index=True)
    flip = (real_is > 0) != (real_oos > 0)
    sf = SU[SU.group == G].sep.dropna()
    sub_flip = len(sf) > 1 and (sf > 0).any() and (sf < 0).any()
    pv = [r['p'] for r in nrow]
    verdict = ('DEAD -- sign flips' if (flip or sub_flip) else
               'DEAD -- fails null' if min(pv) > 0.05 else 'KEEPER')
    print('    VERDICT: %s  (halves flip: %s, sub-periods flip: %s, '
          'best p %.3f)' % (verdict, flip, sub_flip, min(pv)))
    return S, SU, G, verdict


def forward(N, st, px, cm_dates, fit, pairs):
    """Test 2. Panel: every pair-bar with a reading is one observation.

    Reported, never decisive. Terciles are cut on the IN-SAMPLE pooled |net|
    distribution and applied unchanged. The special cell is the top DECILE, cut
    the same way and declared before running.
    """
    idx = px.index
    ahead = pd.Series(False, index=idx)
    for d in cm_dates:
        i = idx.searchsorted(d)
        if i < len(idx):
            ahead.iloc[max(0, i - FWD):i] = True
    S = st.reindex(idx)
    A = N.abs()
    v_is = A.values[fit]
    q = np.nanquantile(v_is[np.isfinite(v_is)], [1 / 3, 2 / 3, 0.9])
    rows = []
    fwd_state = {s: (S == s).rolling(FWD).max().shift(-FWD)
                 for s in ('trending', 'ranging', 'trend-in-range')}
    F_lift = {}
    for tag, m in (('is', fit), ('oos', ~fit)):
        # pooled pair-bar vectors
        bk, ah, ok = [], [], []
        fs = {s: [] for s in fwd_state}
        for p in pairs:
            a = A[p].values
            good = m & np.isfinite(a)
            bk.append(a[good]); ah.append(ahead.values[good])
            for s in fwd_state:
                fs[s].append(fwd_state[s][p].values[good] if p in S.columns
                             else np.full(good.sum(), np.nan))
            ok.append(good.sum())
        bk = np.concatenate(bk); ah = np.concatenate(ah)
        fs = {s: np.concatenate(v) for s, v in fs.items()}
        lab = np.where(bk <= q[0], 'low', np.where(bk <= q[1], 'mid', 'high'))
        base = float(ah.mean())
        for b in ('low', 'mid', 'high'):
            sel = lab == b
            if sel.sum() < 50:
                continue
            rows.append(dict(driver='F COT |net|', block=tag, bucket=b,
                             pair_bars=int(sel.sum()),
                             metric='P(acute crisis in 20 bars)',
                             p=float(ah[sel].mean()), base=base,
                             lift=float(ah[sel].mean() / base) if base else np.nan))
        # the declared special cell
        sel = bk >= q[2]
        F_lift[tag] = float(ah[sel].mean() / base) if base else np.nan
        rows.append(dict(driver='F COT |net|', block=tag,
                         bucket='top decile (declared cell)',
                         pair_bars=int(sel.sum()),
                         metric='P(acute crisis in 20 bars)',
                         p=float(ah[sel].mean()), base=base,
                         lift=F_lift[tag]))
        for s in fwd_state:
            b2 = float(np.nanmean(fs[s]))
            for b in ('low', 'mid', 'high'):
                sel = lab == b
                if sel.sum() < 50:
                    continue
                v = float(np.nanmean(fs[s][sel]))
                rows.append(dict(driver='F COT |net|', block=tag, bucket=b,
                                 pair_bars=int(sel.sum()),
                                 metric='P(%s in 20 bars)' % s, p=v, base=b2,
                                 lift=v / b2 if b2 else np.nan))
    # THE DECLARED CELL GETS A NULL. It is the only forward reading here that
    # holds direction across both halves, and commodities looked exactly like
    # this (x1.17 in both) before failing its null in both. Reporting a lift
    # without one would repeat that mistake.
    nrows = []
    rng = np.random.default_rng(2468)
    n = len(idx)
    V = A.values
    for tag, m in (('is', fit), ('oos', ~fit)):
        acc = []
        for _ in range(NSHIFT):
            k = int(rng.integers(MINOFF, n - MINOFF))
            A2 = pd.DataFrame(np.roll(V, k, axis=0), index=idx, columns=A.columns)
            bk, ah = [], []
            for p in pairs:
                a = A2[p].values
                good = m & np.isfinite(a)
                bk.append(a[good]); ah.append(ahead.values[good])
            bk = np.concatenate(bk); ah = np.concatenate(ah)
            sel = bk >= q[2]
            if sel.sum() > 50:
                acc.append(float(ah[sel].mean() / ah.mean()))
        real = float(F_lift[tag])
        v = np.array(acc, float); v = v[np.isfinite(v)]
        rank = int((np.abs(v - 1) >= abs(real - 1)).sum()) + 1
        nrows.append(dict(driver='F COT |net|', block=tag,
                          bucket='top decile (declared cell)',
                          metric='NULL of the declared cell', p=np.nan,
                          real_lift=real, n_shifts=len(v),
                          null_mean_lift=float(v.mean()),
                          null_sd=float(v.std()), rank_of_real=rank,
                          n_compared=len(v) + 1, p_null=rank / (len(v) + 1)))
    rows += nrows
    F = pd.DataFrame(rows)
    print('\nTEST 2 -- FORWARD ODDS (reported, cannot kill)')
    for met in F.metric.unique():
        if met == 'NULL of the declared cell':
            for _, r in F[F.metric == met].iterrows():
                print('  %-4s DECLARED CELL NULL: real lift x%.2f | null x%.2f '
                      '+/- %.2f over %d | rank %d of %d | p=%.3f'
                      % (r.block, r.real_lift, r.null_mean_lift, r.null_sd,
                         r.n_shifts, r.rank_of_real, r.n_compared, r.p_null))
            continue
        for tag in ('is', 'oos'):
            d = F[(F.metric == met) & (F.block == tag)]
            if not len(d):
                continue
            print('  %-4s %-28s base %.3f | %s'
                  % (tag, met, d.base.iloc[0], '  '.join(
                      '%s %.3f (x%.2f)' % (r.bucket, r.p, r.lift)
                      for _, r in d.iterrows())))
    return F


def main():
    px, st, N, C, pairs = load()
    cm, n_ev = crisis_mask(px.index)
    fit = np.asarray(px.index < SPLIT)
    import events as EV
    cal = getattr(EV, 'EVENTS', None) or getattr(EV, 'CAL')
    ev = pd.to_datetime([r[0] for r in cal])
    print('DRIVER F -- CFTC COT POSITIONING')
    print('  LAG: Tuesday report, Friday release, usable the following Monday.')
    print('       report_date + %d calendar days, then shifted one bar.'
          % RELEASE_LAG_DAYS)
    print('       Effective: SEVEN calendar days snapshot -> first usable bar.')
    print('       Stale readings dropped after %d days.' % MAX_STALE_DAYS)
    print('  COVERAGE: %d of 28 pairs, no crosses. Per pair, bars with a reading:'
          % len(pairs))
    for p in pairs:
        n = N[p].notna()
        print('    %-7s %.3f  %s -> %s'
              % (p, n.mean(), N.index[n].min().date(), N.index[n].max().date()))

    print('\nTEST 1 -- SEPARATION (decides keep or kill)')
    fitS = pd.Series(fit, index=px.index)
    out, subs, verdicts = [], [], {}
    for name, drv, prim in (('F1 |net share| (crowding)', N.abs(), True),
                            ('F2 |4-week change| (turnover)', C.abs(), True),
                            ('F3 net share, signed', N, False),
                            ('F4 4-week change, signed', C, False)):
        S, SU, G, v = run_one(name, drv, pairs, st, px, cm, fitS, prim)
        out.append(S); subs.append(SU); verdicts[name] = (G, v)
    SEP = pd.concat(out, ignore_index=True)
    SUB = pd.concat(subs, ignore_index=True)
    SEP.to_csv(os.path.join(ROOTOUT, 'cot_separation.csv'), index=False)
    SUB.to_csv(os.path.join(ROOTOUT, 'cot_subperiod.csv'), index=False)

    F = forward(N, st, px, ev, fit, pairs)
    F.to_csv(os.path.join(ROOTOUT, 'cot_forward.csv'), index=False)

    prim_v = [v for k, (g, v) in verdicts.items() if k.startswith(('F1', 'F2'))]
    overall = 'KEEPER' if any(v == 'KEEPER' for v in prim_v) else 'DEAD'
    print('\nVERDICT ON DRIVER F: %s' % overall)
    for k, (g, v) in verdicts.items():
        print('  %-32s %-10s %s' % (k, g, v))

    vtxt = '\n'.join('  %-32s chosen group %-9s %s' % (k, g, v)
                     for k, (g, v) in verdicts.items())
    hdr(os.path.join(ROOTOUT, 'cot_separation.csv'),
        'Driver F -- does CFTC positioning separate the states?',
        'THE LAG, which is what fakes results here. A COT report is TUESDAY\n'
        'positions published FRIDAY afternoon, treated as usable from the\n'
        'following MONDAY: report_date + %d calendar days, then the standard\n'
        'one-bar shift. Seven calendar days from snapshot to first usable bar.\n'
        'A reading is dropped once older than %d days, so NZD does not get its\n'
        'final 2022 report carried to 2026.\n\n'
        'COVERAGE. CME FX futures are quoted against USD, so this reaches 7 of\n'
        '28 pairs and no cross at all. NZD stops being reported after\n'
        '2022-02-01.\n\n'
        'SIGNED OR ABSOLUTE, declared before running. State labels carry no\n'
        'direction -- "trending" covers up and down -- so a signed position\n'
        'averaged over trending episodes cancels toward zero by construction.\n'
        'Separation is therefore decided on the ABSOLUTE readings (F1 crowding,\n'
        'F2 turnover); the signed ones (F3, F4) are reported beside them so the\n'
        'choice can be checked, and are not decisive.\n\n'
        'Episode-based: one state run is one observation. Circular-shift null,\n'
        'exact draw count in n_shifts. Sub-period split ran before any holdout\n'
        'pass was reported.\n\nVERDICTS\n%s\n\nOVERALL: %s\n'
        % (RELEASE_LAG_DAYS, MAX_STALE_DAYS, vtxt, overall))
    hdr(os.path.join(ROOTOUT, 'cot_subperiod.csv'),
        'Driver F -- holdout separation split by sub-period',
        'Run BEFORE any holdout pass was reported. This split has already\n'
        'killed three of the five earlier drivers: a result that is real in one\n'
        'sub-period and reversed in another is a result about two years, not\n'
        'about the market.')
    hdr(os.path.join(ROOTOUT, 'cot_forward.csv'),
        'Driver F -- forward odds over the next %d bars' % FWD,
        'REPORTED, CANNOT KILL. Confirmation of the present is the keep/kill\n'
        'bar; a forward failure never kills a driver.\n\n'
        'Panel: one pair-bar with a reading is one observation, over the 7 USD\n'
        'pairs. Terciles cut on the in-sample pooled |net| distribution and\n'
        'applied unchanged to the holdout.\n\n'
        'THE DECLARED SPECIAL CELL, stated before running: the top DECILE of\n'
        '|net| against P(acute crisis within 20 bars) -- the crowded-trade\n'
        'hypothesis, that extreme speculative positioning precedes a break.\n\n'
        'Note the acute-crisis window is GLOBAL (one event calendar), so the 7\n'
        'pairs share it and the crisis rows are not 7 independent samples.')
    print('\nwrote cot_separation.csv, cot_subperiod.csv, cot_forward.csv + .txt')
    return SEP, SUB, F


if __name__ == '__main__':
    main()
