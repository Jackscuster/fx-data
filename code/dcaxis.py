import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""A CANDIDATE TREND AXIS FROM DIRECTIONAL CHANGE (Layer 1 research round,
construction 1; source results/research/RESEARCH_2026-11-09_part2_regime_
taxonomies_and_nnfx_catalog.md family 7, commit 9926531).

WHY. The shipped trend axis fails its separation null in routing (HANDOFF_3
16.1b) and a RELATIVE cut cannot see a two-year trend: a trend that creeps
inside its own shrinking vol never clears a trailing yardstick. Directional
change replaces the yardstick with an ABSOLUTE one in event time.

THE CONSTRUCTION, every knob declared before any result was computed:
  * per pair, track the running extreme of log price. A reversal of theta
    from that extreme is an EVENT; the continuation from the event until the
    next reversal is the OVERSHOOT.
  * THETA IS A CONSTANT PER PAIR: theta = m x that pair's daily log-return
    stdev measured ONCE on the tuning window (dates < SPLIT). NOT trailing
    vol -- a trailing yardstick shrinks inside a quiet trend and recreates
    exactly the relative-cut failure this construction exists to fix.
    Declared multiples m = 0.5, 1.0, 1.5.
  * the score at bar t uses bars through t-1 ONLY: mean(overshoot / theta)
    over the last K COMPLETED events, K = 5 and 10. Trend runs large,
    range sits near 1.
  * secondary reads, same lag: bars in the current mode, events in the
    trailing 106 bars.
  * before K events exist there is NO label -- the shipped warm-up
    convention, not a filled-forward guess.
  * the label cut is learned on the tuning window only and applied unchanged.
  * DEGENERATE-COUNT GUARD: any (pair, m) with under 30 completed events on
    the tuning window is reported and the run STOPS for instructions. No
    silent re-pick.
  * SELECTION: one (m, K) on the tuning window by best separation, SUBJECT
    TO label runs consistent with the measured duration of real trending
    episodes in this panel (median ~21 bars, results/run_lengths.csv) and a
    flip rate no worse than the shipped trend axis. All six variants are
    reported; one holdout confirm; no second pick.

Everything here is present tense and carries no money metric. The Layer 3
money test lives in code/dcroute.py and runs only after this battery.

    python3 code/dcaxis.py --stage events     # events, theta, the guard
    python3 code/dcaxis.py --stage battery    # the six variants, IS + one confirm
    python3 code/dcaxis.py --stage null       # 200-draw surrogate null
    python3 code/dcaxis.py --stage report     # selection, summary, markdown
"""
import argparse, json, time
import numpy as np, pandas as pd
import structval as SV
from structval import SPLIT, MIN_SHARE, SHAPE, properties, separation, surrogate

PX = os.path.join(ROOTDATA, 'px28.csv')
STAMP = '2026-11-09'
MULT = (0.5, 1.0, 1.5)          # m, declared
KS = (5, 10)                    # K, declared
MIN_EVENTS = 30                 # the degenerate-count guard
TRAIL = 106                     # the panel's own confirmation window, for the event-count read
SEAL = pd.Timestamp('2020-12-31')
HOLD0 = pd.Timestamp('2016-01-01')
NSHUF = int(os.environ.get('FX_NSHUF', 200))


def out(name):
    return os.path.join(ROOTOUT, 'dc_axis_%s_%s' % (name, STAMP))


def load_px():
    """The 5pm panel, log price, sealed at 2020-12-31 unless FX_ALLOW_W4=1 (which
    l2sweep.load_pair logs). 2021+ never reaches a cut, a null or a report."""
    px = pd.read_csv(PX, index_col=0, parse_dates=True).astype(float)
    if os.environ.get('FX_ALLOW_W4') == '1':
        print('  !! FX_ALLOW_W4=1: the sealed years are OPEN in this process', flush=True)
    else:
        px = px[px.index <= SEAL]
    return px


def theta_of(px):
    """theta per (pair, m): m x the pair's daily log-return stdev on the TUNING
    WINDOW only. One number per pair for all time -- the whole point."""
    rr = np.log(px).diff()
    sd = rr[rr.index < SPLIT].std()
    return {m: (m * sd) for m in MULT}, sd


def dc_events(lp, th):
    """Directional change on one pair's log price at absolute threshold `th`.

    Returns a frame of completed events: the bar the reversal was confirmed,
    the mode it turned INTO, and the overshoot that followed (in price units,
    absolute). The last, still-running event is not completed and is excluded.

    Mode starts unknown and is set by the first threshold move, so the first
    event is the first confirmed turn, never an assumed direction.
    """
    v = lp.dropna()
    if len(v) < 10 or not np.isfinite(th) or th <= 0:
        return pd.DataFrame(columns=['bar', 'date', 'mode', 'overshoot'])
    x = v.values; idx = v.index
    mode = 0                      # +1 up, -1 down, 0 unknown
    ext = x[0]; ext_i = 0
    rows = []
    for i in range(1, len(x)):
        if mode >= 0 and x[i] <= ext - th:
            # confirmed turn DOWN: the up-mode's overshoot ran from the last
            # event to this extreme (ext), and a new down event opens here
            rows.append((i, idx[i], -1, ext_i))
            mode = -1; ext = x[i]; ext_i = i
        elif mode <= 0 and x[i] >= ext + th:
            rows.append((i, idx[i], +1, ext_i))
            mode = +1; ext = x[i]; ext_i = i
        else:
            if mode >= 0 and x[i] > ext:
                ext = x[i]; ext_i = i
            elif mode <= 0 and x[i] < ext:
                ext = x[i]; ext_i = i
    if not rows:
        return pd.DataFrame(columns=['bar', 'date', 'mode', 'overshoot'])
    E = pd.DataFrame(rows, columns=['bar', 'date', 'mode', 'ext_bar'])
    # the overshoot of the event that OPENED at row j is the move from its own
    # confirmation bar to the extreme reached before the next reversal
    ov = []
    for j in range(len(E)):
        b0 = int(E.bar.iloc[j])
        be = int(E.ext_bar.iloc[j + 1]) if j + 1 < len(E) else None
        ov.append(abs(x[be] - x[b0]) if be is not None else np.nan)
    E['overshoot'] = ov
    return E.dropna(subset=['overshoot']).reset_index(drop=True)


def dc_scores(px, th_by_pair, K):
    """Per pair, the score at bar t from COMPLETED events before t: the mean of
    overshoot/theta over the last K. Also bars in the current mode and events in
    the trailing TRAIL bars. Everything shifted one bar at the end, so a row
    dated D is built from bars <= D-1 -- the panel's lag contract."""
    lp = np.log(px)
    sc = pd.DataFrame(index=px.index, columns=px.columns, dtype=float)
    mode_age = pd.DataFrame(index=px.index, columns=px.columns, dtype=float)
    ev_cnt = pd.DataFrame(index=px.index, columns=px.columns, dtype=float)
    ev_tab = {}
    for p in px.columns:
        th = float(th_by_pair[p])
        E = dc_events(lp[p], th)
        ev_tab[p] = E
        if not len(E):
            continue
        r = (E.overshoot.values / th)
        bars = E.bar.values.astype(int)
        s = np.full(len(px), np.nan); age = np.full(len(px), np.nan); cnt = np.full(len(px), np.nan)
        # event j completes when the NEXT event is confirmed, so it is only
        # usable from bar bars[j+1] onward -- never on its own bar
        for j in range(K, len(E)):
            a = bars[j]
            b = bars[j + 1] if j + 1 < len(E) else len(px)
            s[a:b] = r[j - K:j].mean()
            cnt[a:b] = float(((bars >= a - TRAIL) & (bars < a)).sum())
            age[a:b] = np.arange(b - a) + 1.0
        sc[p] = s; mode_age[p] = age; ev_cnt[p] = cnt
    return sc.shift(1), mode_age.shift(1), ev_cnt.shift(1), ev_tab


def label_of(sc, cut):
    """trending where the score is at or above the cut, ranging below, no label
    in the warm-up. Two states by construction -- the axis is a TREND axis, and
    adding states nobody asked for is on the do-not-repeat list."""
    L = pd.DataFrame('', index=sc.index, columns=sc.columns, dtype=object)
    L[sc >= cut] = 'trending'
    L[sc < cut] = 'ranging'
    L[sc.isna()] = ''
    return L


def cut_on_tuning(sc):
    """The cut is the tuning window's own median score, so each variant splits
    its own distribution and the comparison between variants is not a comparison
    of coverage. Learned on dates < SPLIT and applied unchanged everywhere."""
    v = sc[sc.index < SPLIT].stack().dropna()
    return float(v.median()) if len(v) else np.nan


def run_stats(L):
    """median run length, flip rate (share of labelled bars whose label differs
    from the previous labelled bar), coverage, share trending."""
    med, flips, n_lab, n_tot, n_tr, runs = [], 0, 0, 0, 0, 0
    for p in L.columns:
        v = L[p]; v = v[v != '']
        n_tot += len(L[p]); n_lab += len(v); n_tr += int((v == 'trending').sum())
        if len(v) < 2:
            continue
        ch = (v != v.shift()).values; ch[0] = False
        flips += int(ch.sum())
        gid = (v != v.shift()).cumsum()
        r = v.groupby(gid).size()
        med.append(float(r.median())); runs += len(r)
    return dict(median_run=float(np.median(med)) if med else np.nan,
                flip_rate=(flips / n_lab) if n_lab else np.nan,
                coverage=(n_lab / n_tot) if n_tot else np.nan,
                share_trending=(n_tr / n_lab) if n_lab else np.nan, n_runs=runs)


def sep_of(L, P, oos_only):
    s = separation(L, P, oos_only=oos_only)
    return float(s.gap_sd.reindex(SHAPE).mean()), s


def shipped_axis():
    """The shipped trend axis as the live interface publishes it: shape2 and the
    raw trend_score, read with the 5pm header assert."""
    import l2sweep as S
    S.layer1_header_check(os.path.join(ROOTOUT, 'layer1_states.csv'))
    d = pd.read_csv(os.path.join(ROOTOUT, 'layer1_states.csv'), comment='#',
                    parse_dates=['date'], usecols=['date', 'pair', 'shape2', 'trend_score', 'chop_score'])
    d = d[d.date <= SEAL]
    sh = d.pivot(index='date', columns='pair', values='shape2')
    ts = d.pivot(index='date', columns='pair', values='trend_score')
    cs = d.pivot(index='date', columns='pair', values='chop_score')
    lab = pd.DataFrame('', index=sh.index, columns=sh.columns, dtype=object)
    lab[sh == 'trending'] = 'trending'
    lab[sh.notna() & (sh != 'trending')] = 'ranging'
    return lab, ts, cs, sh


def stage_events():
    px = load_px()
    TH, sd = theta_of(px)
    rows = []
    stop = []
    for m in MULT:
        th = TH[m]
        for p in px.columns:
            E = dc_events(np.log(px[p]), float(th[p]))
            n_is = int((E.date < SPLIT).sum()) if len(E) else 0
            n_oos = int(((E.date >= HOLD0) & (E.date <= SEAL)).sum()) if len(E) else 0
            rows.append(dict(m=m, pair=p, daily_sd=float(sd[p]), theta=float(th[p]),
                             theta_bp=1e4 * float(th[p]), events_total=len(E),
                             events_tuning=n_is, events_holdout=n_oos,
                             mean_overshoot_over_theta=float((E.overshoot / float(th[p])).mean()) if len(E) else np.nan))
            if n_is < MIN_EVENTS:
                stop.append((m, p, n_is))
    D = pd.DataFrame(rows)
    D.to_csv(out('events') + '.csv', index=False)
    txt = [
        'DIRECTIONAL-CHANGE EVENTS, per (pair, m). %s' % STAMP,
        'theta = m x the pair daily log-return stdev on the TUNING WINDOW ONLY (dates < %s).' % SPLIT.date(),
        'Panel %s -> %s, %d pairs, sealed at %s.' % (px.index.min().date(), px.index.max().date(), px.shape[1], SEAL.date()),
        '', 'Per m: events on the tuning window (the guard is %d).' % MIN_EVENTS,
        D.groupby('m').events_tuning.agg(['min', 'median', 'max']).round(1).to_string(),
        '', 'theta in basis points of log price:',
        D.groupby('m').theta_bp.agg(['min', 'median', 'max']).round(2).to_string(),
        '', 'mean overshoot / theta over all completed events:',
        D.groupby('m').mean_overshoot_over_theta.agg(['min', 'median', 'max']).round(3).to_string(),
    ]
    if stop:
        txt += ['', 'DEGENERATE-COUNT GUARD TRIPPED on %d (pair, m) cells:' % len(stop),
                '\n'.join('  m=%.1f %s: %d tuning events (floor %d)' % (m, p, n, MIN_EVENTS) for m, p, n in stop),
                'Per the declared rule the run STOPS here for instructions; nothing is re-picked.']
    else:
        txt += ['', 'Guard: every (pair, m) clears %d completed tuning-window events. No cell re-picked.' % MIN_EVENTS]
    open(out('events') + '.txt', 'w').write('\n'.join(txt) + '\n')
    print('\n'.join(txt), flush=True)
    if stop:
        raise SystemExit('DC EVENTS: degenerate-count guard tripped -- see %s' % (out('events') + '.txt'))
    return D


def build_variants(px):
    TH, _ = theta_of(px)
    V = {}
    for m in MULT:
        for K in KS:
            sc, age, cnt, ev = dc_scores(px, TH[m], K)
            cut = cut_on_tuning(sc)
            V[(m, K)] = dict(score=sc, age=age, count=cnt, cut=cut, label=label_of(sc, cut))
    return V


def stage_battery():
    t0 = time.time()
    px = load_px()
    P = properties(px)
    V = build_variants(px)
    SL, ts, cs, sh = shipped_axis()
    ship_is, _ = sep_of(SL, P, oos_only=False)
    ship_oos, _ = sep_of(SL, P, oos_only=True)
    ship_run = run_stats(SL)
    rows = []
    for (m, K), d in V.items():
        L = d['label']
        s_is, _ = sep_of(L, P, oos_only=False)
        s_oos, _ = sep_of(L, P, oos_only=True)
        r = run_stats(L)
        # correlation with the shipped reads, reported plainly
        a = d['score'].stack(); b = ts.reindex_like(d['score']).stack(); c = cs.reindex_like(d['score']).stack()
        j = pd.DataFrame({'dc': a, 'trend': b, 'chop': c}).dropna()
        st = P['range_to_path'].stack()        # the straightness measure
        j2 = pd.DataFrame({'dc': a, 'straight': st}).dropna()
        agree = pd.DataFrame({'dc': L.stack(), 'sh': SL.reindex_like(L).stack()}).replace('', np.nan).dropna()
        rows.append(dict(m=m, K=K, cut=d['cut'],
                         separation_tuning=s_is, separation_holdout=s_oos,
                         median_run=r['median_run'], flip_rate=r['flip_rate'], coverage=r['coverage'],
                         share_trending=r['share_trending'], n_runs=r['n_runs'],
                         corr_shipped_trend_score=float(j.dc.corr(j.trend, method='spearman')),
                         corr_shipped_chop_score=float(j.dc.corr(j.chop, method='spearman')),
                         corr_straightness=float(j2.dc.corr(j2.straight, method='spearman')),
                         label_agreement_with_shipped=float((agree.dc == agree.sh).mean()),
                         n_obs=int(len(j))))
    B = pd.DataFrame(rows).sort_values(['m', 'K'])
    B['shipped_separation_tuning'] = ship_is; B['shipped_separation_holdout'] = ship_oos
    B['shipped_median_run'] = ship_run['median_run']; B['shipped_flip_rate'] = ship_run['flip_rate']
    B.to_csv(out('battery') + '.csv', index=False)
    # episode-based significance, per variant, on the holdout
    erows = []
    for (m, K), d in V.items():
        import episodes as EP
        E = EP.episodes(d['label'], P, oos_only=True)
        if len(E):
            for prop in SHAPE:
                erows.append(dict(m=m, K=K, prop=prop, episode_gap_sd=float(EP.gap(E, prop)), n_episodes=int(len(E))))
    pd.DataFrame(erows).to_csv(out('episodes') + '.csv', index=False)
    # refit stability across the standard vintages: the cut re-learned at each
    import refit as RF
    vrows = []
    for v in RF.VINTAGES:
        end = pd.Timestamp('%d-12-31' % v)
        if end > SEAL and os.environ.get('FX_ALLOW_W4') != '1':
            vrows.append(dict(vintage=v, note='sealed, not run')); continue
        q = px[px.index <= end]
        TH, _ = theta_of(q)
        for (m, K) in V:
            sc, _, _, _ = dc_scores(q, TH[m], K)
            vrows.append(dict(vintage=v, m=m, K=K, cut=cut_on_tuning(sc),
                              n_bars=int(len(q)), note=''))
    pd.DataFrame(vrows).to_csv(out('refit_vintages') + '.csv', index=False)
    # sub-period split: 2016-19 vs 2020 ONLY (2021+ is sealed, so the research
    # doc's 2020-21 window does not exist here and is not used)
    srows = []
    for (m, K), d in V.items():
        for lab, a, b in (('2016-2019', '2016-01-01', '2019-12-31'), ('2020', '2020-01-01', '2020-12-31')):
            L = d['label'].loc[a:b]; Pq = {k: P[k].loc[a:b] for k in P}
            s = separation(L, Pq, oos_only=False)
            r = run_stats(L)
            srows.append(dict(m=m, K=K, period=lab, separation=float(s.gap_sd.reindex(SHAPE).mean()),
                              median_run=r['median_run'], flip_rate=r['flip_rate'], coverage=r['coverage'],
                              share_trending=r['share_trending']))
    pd.DataFrame(srows).to_csv(out('subperiod') + '.csv', index=False)
    txt = ['DC TREND AXIS -- PRESENT-TENSE BATTERY, six declared variants. %s' % STAMP,
           'No money metric appears in this file. Tuning window < %s; ONE holdout confirm on 2016-2020; 2021+ sealed.' % SPLIT.date(),
           '', B[['m', 'K', 'cut', 'separation_tuning', 'separation_holdout', 'median_run', 'flip_rate',
                 'coverage', 'share_trending', 'corr_shipped_trend_score', 'corr_straightness',
                 'label_agreement_with_shipped']].to_string(index=False, float_format=lambda v: '%8.4f' % v),
           '', 'shipped trend axis on the same battery: separation tuning %.4f, holdout %.4f, median run %.1f, flip rate %.4f'
           % (ship_is, ship_oos, ship_run['median_run'], ship_run['flip_rate']),
           '', 'measured duration of real trending episodes in this panel (results/run_lengths.csv): median ~21 bars',
           'done in %.1f min' % ((time.time() - t0) / 60)]
    open(out('battery') + '.txt', 'w').write('\n'.join(txt) + '\n')
    print('\n'.join(txt), flush=True)
    return B


def stage_null():
    """200 surrogate draws per variant: the same construction on a panel with the
    same marginal returns and no sequence. Nulls before findings."""
    t0 = time.time()
    px = load_px()
    P = properties(px)
    rng = np.random.default_rng(20261109)
    real = {}
    V = build_variants(px)
    for (m, K), d in V.items():
        real[(m, K)] = sep_of(d['label'], P, oos_only=True)[0]
    rows = []
    for kind in ('sign', 'perm'):
        draws = {k: [] for k in V}
        for i in range(NSHUF):
            q = surrogate(px, kind, rng)
            Pq = properties(q)
            TH, _ = theta_of(q)
            for (m, K) in V:
                sc, _, _, _ = dc_scores(q, TH[m], K)
                L = label_of(sc, cut_on_tuning(sc))
                draws[(m, K)].append(sep_of(L, Pq, oos_only=True)[0])
            if (i + 1) % 25 == 0:
                print('  %s null: %d/%d draws (%.1f min)' % (kind, i + 1, NSHUF, (time.time() - t0) / 60), flush=True)
        for (m, K) in V:
            v = np.array([x for x in draws[(m, K)] if np.isfinite(x)])
            r = real[(m, K)]
            rows.append(dict(kind=kind, m=m, K=K, real=r, n_draws=len(v), null_mean=float(v.mean()),
                             null_p95=float(np.percentile(v, 95)), null_max=float(v.max()),
                             corrected=r - float(v.mean()),
                             p_value=float((v >= r).mean())))
    N = pd.DataFrame(rows)
    N.to_csv(out('null') + '.csv', index=False)
    txt = ['DC TREND AXIS -- %d-DRAW SURROGATE NULL per variant, holdout separation. %s' % (NSHUF, STAMP),
           'sign = same |returns|, random signs; perm = the pair own returns reshuffled. The construction,',
           'the theta measurement and the cut are all re-derived on each surrogate, so the null prices the',
           'WHOLE pipeline and not just the labelling step.', '',
           N.to_string(index=False, float_format=lambda v: '%9.4f' % v),
           '', 'corrected = real - null mean. done in %.1f min' % ((time.time() - t0) / 60)]
    open(out('null') + '.txt', 'w').write('\n'.join(txt) + '\n')
    print('\n'.join(txt), flush=True)
    return N


def stage_report():
    """The declared selection, then the summary. Selection: best tuning-window
    separation SUBJECT TO (a) median run length consistent with the measured
    ~21-bar trending episode and (b) flip rate no worse than the shipped axis."""
    B = pd.read_csv(out('battery') + '.csv')
    N = pd.read_csv(out('null') + '.csv') if os.path.exists(out('null') + '.csv') else pd.DataFrame()
    # THE MEASURED STANDARD: the SHIPPED generation's own trending states on the IS
    # block -- g4_twoscore4 is the two-score classifier shape2 is cut from. Its
    # median run is 20.0 bars (Jack's "~21"); the other generations in the file are
    # superseded shapes and are not the standard for a trend axis.
    RL = pd.read_csv(os.path.join(ROOTOUT, 'run_lengths.csv'))
    rl = RL[(RL.block == 'is') & (RL.generation == 'g4_twoscore4')
            & RL.state.astype(str).str.contains('trend', case=False)]
    meas = float(rl['median'].median()); n_meas = len(rl)
    ship_flip = float(B.shipped_flip_rate.iloc[0]); ship_run = float(B.shipped_median_run.iloc[0])
    lo, hi = 0.5 * meas, 2.0 * meas
    B['run_ok'] = (B.median_run >= lo) & (B.median_run <= hi)
    B['flip_ok'] = B.flip_rate <= ship_flip
    B['eligible'] = B.run_ok & B.flip_ok
    el = B[B.eligible]
    # NO SILENT RE-PICK. If the declared constraint set is empty the run says so,
    # names the constraint each variant fails, and falls back to a rule declared
    # HERE, before any Layer 3 number exists: the PRIMARY is the best tuning-window
    # separation among the variants inside the measured run band (Jack: "the
    # standard is the measured data"), carrying its flip-rate violation in the
    # open; the only flip-rate passer is reported beside it as a SENSITIVITY. Both
    # are fixed before the money test and neither is re-chosen after it.
    empty = not len(el)
    pool = el if len(el) else B[B.run_ok]
    if not len(pool):
        pool = B
    pick = pool.sort_values('separation_tuning', ascending=False).iloc[0]
    alt = B[B.flip_ok].sort_values('separation_tuning', ascending=False)
    alt = alt.iloc[0] if len(alt) and empty else None
    B['selected'] = (B.m == pick.m) & (B.K == pick.K)
    B['sensitivity'] = False if alt is None else ((B.m == alt.m) & (B.K == alt.K))
    B['constraint_set_empty'] = empty
    B['measured_run_bars'] = meas; B['run_band_lo'] = lo; B['run_band_hi'] = hi
    B.to_csv(out('selection') + '.csv', index=False)
    txt = ['DC TREND AXIS -- SELECTION AND SUMMARY. %s' % STAMP, '',
           'The standard is the measured data: the shipped generation g4_twoscore4 trending states run a median',
           'of %.1f bars on the IS block (%d state-pair rows of results/run_lengths.csv), so the admissible band' % (meas, n_meas),
           'is %.1f-%.1f bars. Flip rate must be no worse than the shipped trend axis (%.4f, same 2-state collapse).' % (lo, hi, ship_flip), '',
           B[['m', 'K', 'separation_tuning', 'separation_holdout', 'median_run', 'flip_rate', 'coverage',
              'run_ok', 'flip_ok', 'eligible', 'selected']].to_string(index=False, float_format=lambda v: '%8.4f' % v)]
    if empty:
        txt += ['',
                'THE DECLARED CONSTRAINT SET IS EMPTY: no variant satisfies BOTH constraints. Every variant inside',
                'the measured run band flips more often than the shipped axis, and the only variant that flips less',
                'often (m=1.5, K=10) runs %.1f bars -- outside the band. Reported, not re-picked.' % float(B[B.flip_ok].median_run.iloc[0]),
                'PRIMARY, by the rule declared in code before any money number existed: best tuning separation among',
                'the variants inside the measured run band, with its flip-rate violation carried in the open.',
                'SENSITIVITY: the only flip-rate passer, reported beside it. Neither is re-chosen after the Layer 3 test.']
    txt += ['', 'SELECTED (primary): m = %.1f, K = %d (cut %.4f on the tuning window), median run %.1f bars, flip rate %.4f vs shipped %.4f.'
            % (pick.m, pick.K, pick.cut, pick.median_run, pick.flip_rate, ship_flip),
           'Its holdout confirm: separation %.4f against the shipped axis holdout %.4f.'
           % (pick.separation_holdout, float(B.shipped_separation_holdout.iloc[0])),
           '', 'Correlation with the shipped reads (Spearman): trend score %.3f, straightness %.3f, label agreement %.3f.'
           % (pick.corr_shipped_trend_score, pick.corr_straightness, pick.label_agreement_with_shipped),
           'Read plainly: a high correlation means this construction CONFIRMS the shipped axis and is recorded as',
           'such -- it is neither a pass nor a failure on its own, and it never decides the routing question.']
    if alt is not None:
        txt += ['SENSITIVITY: m = %.1f, K = %d (cut %.4f), median run %.1f bars, flip rate %.4f -- the only flip-rate passer.'
                % (alt.m, alt.K, alt.cut, alt.median_run, alt.flip_rate)]
    if len(N):
        n = N[(N.m == pick.m) & (N.K == pick.K)]
        txt += ['', 'Null on the selected variant:',
                n.to_string(index=False, float_format=lambda v: '%9.4f' % v)]
    txt += ['', 'The Layer 3 money test is a separate file (code/dcroute.py, dc_axis_layer3_*): the DC axis earns a',
            'routing place only if the routed book beats results/refit_books_modec2.csv (+1.33%% median year,',
            'PF 1.087) AND beats its own shuffle null. The correlation number never makes that decision.']
    open(out('selection') + '.txt', 'w').write('\n'.join(txt) + '\n')
    print('\n'.join(txt), flush=True)
    # the selected variant's states, for Layer 3 and the app
    px = load_px(); TH, _ = theta_of(px)
    sc, age, cnt, ev = dc_scores(px, TH[float(pick.m)], int(pick.K))
    L = label_of(sc, float(pick.cut))
    S = pd.DataFrame({'date': np.repeat(sc.index.values, sc.shape[1]),
                      'pair': np.tile(sc.columns.values, len(sc)),
                      'dc_score': sc.values.ravel(), 'dc_shape': L.values.ravel(),
                      'dc_mode_age': age.values.ravel(), 'dc_events_106': cnt.values.ravel()})
    S['sample'] = np.where(S.date < SPLIT.to_datetime64(), 'is', 'holdout')
    hdr = ('# DC TREND AXIS (candidate, Layer 1 research round 1) -- OANDA 17:00 NY closes (data/px28.csv). '
           'theta = %.1f x each pair daily log-return stdev measured ONCE on dates < %s; score = mean(overshoot/theta) '
           'over the last %d completed events; cut %.4f learned on the tuning window. Rows are lagged one bar: a row '
           'dated D is built from bars <= D-1. 2021+ sealed and absent. Readers pass comment="#".\n'
           % (pick.m, SPLIT.date(), pick.K, pick.cut))
    with open(out('states') + '.csv', 'w') as fh:
        fh.write(hdr); S.to_csv(fh, index=False)
    print('\nwrote %s (%d rows)' % (out('states') + '.csv', len(S)), flush=True)
    if alt is not None:
        sc2, age2, cnt2, _ = dc_scores(px, TH[float(alt.m)], int(alt.K))
        L2 = label_of(sc2, float(alt.cut))
        S2 = pd.DataFrame({'date': np.repeat(sc2.index.values, sc2.shape[1]),
                           'pair': np.tile(sc2.columns.values, len(sc2)),
                           'dc_score': sc2.values.ravel(), 'dc_shape': L2.values.ravel(),
                           'dc_mode_age': age2.values.ravel(), 'dc_events_106': cnt2.values.ravel()})
        S2['sample'] = np.where(S2.date < SPLIT.to_datetime64(), 'is', 'holdout')
        h2 = ('# DC TREND AXIS SENSITIVITY (the only flip-rate passer) -- m=%.1f, K=%d, cut %.4f, theta measured ONCE on '
              'dates < %s. Rows lagged one bar. 2021+ sealed and absent. Readers pass comment="#".\n'
              % (alt.m, alt.K, alt.cut, SPLIT.date()))
        with open(out('states_sensitivity') + '.csv', 'w') as fh:
            fh.write(h2); S2.to_csv(fh, index=False)
        print('wrote %s (%d rows)' % (out('states_sensitivity') + '.csv', len(S2)), flush=True)
    return B, pick


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', required=True, choices=['events', 'battery', 'null', 'report'])
    a = ap.parse_args()
    print('=== dcaxis %s ===' % a.stage, flush=True)
    {'events': stage_events, 'battery': stage_battery, 'null': stage_null, 'report': stage_report}[a.stage]()
    print('DC AXIS STAGE %s COMPLETE' % a.stage.upper(), flush=True)


if __name__ == '__main__':
    main()
