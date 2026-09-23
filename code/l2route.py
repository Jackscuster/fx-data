import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""LAYER 3 ROUTING -- the first routing test. Layer 1's states gate NEW ENTRIES.

THE RULES, FIXED BEFORE ANY NUMBER WAS SEEN:
  trend slices (A-trend, B-trend)  open only in TRENDING
                                   (--tir incl also admits TREND-IN-RANGE)
  chop slices  (A-chop,  B-chop)   open only in RANGING
  NEITHER                          no new entries, either kind
  crisis on a currency             no new entries on its pairs
  activity axis                    --activity ignore, or weak: WEAK blocks new
                                   trend entries
  open positions run to their own exits; NO forced close on a state change.

ONE-BAR LAG. layer1_states rows are already lagged: a row dated D is built from
bars <= D-1 (export.py). A trade entered on D (19:00 NY, after D's 17:00
close) is routed on the row dated D, so the routing never sees D's own bar.

THE CRISIS FLAG is the shipped acute detector (crisis.py legdiv20): the z-score
of the max-minus-min 20-bar currency-index move, above its IS 95th percentile.
On a firing day the two diverging legs -- the strongest and the weakest
currency -- are the flagged currencies. Shifted one bar like everything else.

WHAT THIS WRITES. Routing is a FILTER on the engine's trade and mark tables:
every trade whose entry the rule refuses is dropped, with all its marks; the
rest is written under a new suffix as wf_trades<out>.pkl / wf_marks<out>.pkl.
Every existing l2walkfwd stage then runs on the routed book unchanged
(--nocut, since the routed book is the whole field, not the gate-3 cut). Also
written: the permitted-bar table the routed random-entry null draws from, and
the regime-dependence table (each slice's trades inside vs outside its regime).

  python3 code/l2route.py --states results/layer1_states_5pm.csv \\
      --px data/px28_5pm.csv --suffix _cleanfield_4slice \\
      --out _routed_tirX_actI --tir excl --activity ignore
  python3 code/l2route.py ... --shuffle-null 25 --jobs 3   # regime-shuffled null
"""
import argparse, glob, time
import numpy as np, pandas as pd
import l2walkfwd as W
import l2sweep as S

CCY = ['EUR', 'GBP', 'AUD', 'NZD', 'USD', 'CAD', 'CHF', 'JPY']
TREND_STATES = {'excl': {'trending'}, 'incl': {'trending', 'trend-in-range'}}
CHOP_STATES = {'ranging'}


def kind_of(sid):
    return 'trend' if str(sid).split('|')[1] == 'trend' else 'chop'


def _seal(df):
    """AUDIT 10: nothing past SEAL_END reaches a routing decision unless FX_ALLOW_W4=1 (logged by l2sweep)."""
    if os.environ.get('FX_ALLOW_W4') == '1':
        return df
    return df[df.index <= pd.Timestamp(S.SEAL_END)]


def load_states(path):
    S.layer1_header_check(path)   # AUDIT 14: the 5pm header, or halt
    d = pd.read_csv(path, parse_dates=['date'], usecols=['date', 'pair', 'shape2', 'activity'], comment='#')
    d = d[d.date <= pd.Timestamp(S.SEAL_END)] if os.environ.get('FX_ALLOW_W4') != '1' else d
    shape = d.pivot(index='date', columns='pair', values='shape2')
    act = d.pivot(index='date', columns='pair', values='activity')
    return shape, act


def crisis_flags(px_path, split='2016-01-01'):
    """date x currency bool, lagged one bar. crisis.py's legdiv20, IS threshold."""
    px = _seal(pd.read_csv(px_path, index_col=0, parse_dates=True))
    r = np.log(px.astype(float)).diff()
    ci = {}
    for c in CCY:
        legs = [r[p] if p[:3] == c else -r[p] for p in r.columns if c in (p[:3], p[3:])]
        ci[c] = pd.concat(legs, axis=1).mean(axis=1)
    ci = pd.DataFrame(ci)
    leg20 = ci.rolling(20).sum()
    div = leg20.max(axis=1) - leg20.min(axis=1)
    z = div / div.rolling(252, min_periods=60).std().shift(1)
    thr = np.nanpercentile(z[z.index < split].dropna(), 95)
    fire = z > thr
    F = pd.DataFrame(False, index=px.index, columns=CCY)
    hi = leg20.idxmax(axis=1); lo = leg20.idxmin(axis=1)
    for d in F.index[fire.values]:
        F.at[d, hi[d]] = True; F.at[d, lo[d]] = True
    F = F.shift(1).fillna(False)
    print('  crisis: legdiv20 IS threshold %.3f, fires on %.1f%% of bars; flagged currency-days %d'
          % (thr, 100 * fire.mean(), int(F.values.sum())), flush=True)
    return F


def permitted(shape, act, flags, tir, activity, chop_always=False, trend_gate='trending'):
    """{(pair, kind): bool Series by date}: may a NEW entry open on this bar.
    chop_always: chop slices are never gated (chop-core). trend_gate:
    'trending' = the trend axis says TRENDING (plus TIR if tir=incl);
    'not-ranging' = the chop axis does not say RANGING (so trending,
    trend-in-range and neither all admit); 'never' = trend slices never open
    (CHOP-ONLY reference, 14 Sep); 'always' = trend slices UNGATED -- every bar,
    crisis still applied, activity gate skipped (Jack, 22 Sep: 'trend strategies
    ungated', everyone trades)."""
    out = {}
    ts = TREND_STATES[tir]
    for p in shape.columns:
        cr = flags[p[:3]] | flags[p[3:]]
        cr = cr.reindex(shape.index).fillna(False)
        sh = shape[p]; ac = act[p]
        tr = (sh.isin(ts) if trend_gate == 'trending' else (sh.notna() & ~sh.isin(CHOP_STATES))) & ~cr
        if trend_gate == 'never':                  # CHOP-ONLY: no trend strategy ever opens
            tr = pd.Series(False, index=sh.index)
        elif trend_gate == 'always':               # trend slices UNGATED: every bar, crisis still on,
            tr = ~cr                               # and no activity gate (see below, which is skipped)
        if activity == 'weak' and trend_gate != 'always':
            tr = tr & (ac != 'weak')
        ch = (sh.notna() if chop_always else sh.isin(CHOP_STATES)) & ~cr
        out[(p, 'trend')] = tr.fillna(False).astype(bool)
        out[(p, 'chop')] = ch.fillna(False).astype(bool)
    return out


def route(T, M, allowed):
    """Keep every trade whose entry bar is permitted for its pair and slice kind."""
    K = T[['sid', 'tid', 'pair', 'entry']].copy()
    K['kind'] = K.sid.astype(str).map(kind_of)
    ok = np.zeros(len(K), bool)
    for (p, kind), g in K.groupby(['pair', 'kind'], observed=True):
        ser = allowed.get((p, kind))
        if ser is None:
            continue
        ok[g.index.values] = ser.reindex(g.entry.values).fillna(False).values
    keep = K[ok][['sid', 'tid']]
    key = pd.MultiIndex.from_frame(keep)
    Tr = T[pd.MultiIndex.from_frame(T[['sid', 'tid']]).isin(key)].reset_index(drop=True)
    Mr = M[pd.MultiIndex.from_frame(M[['sid', 'tid']]).isin(key)].reset_index(drop=True)
    return Tr, Mr, ok


def dependence(T, shape, act, flags, tir, activity, years, chop_always=False, trend_gate='trending'):
    """Each slice's trades INSIDE vs OUTSIDE its regime, trade-level R, trade years only."""
    K = T[['sid', 'tid', 'pair', 'entry', 'R']].copy()
    K['kind'] = K.sid.astype(str).map(kind_of)
    K['slice'] = K.sid.astype(str).map(W.field_label)
    K = K[K.entry.dt.year.isin(years)].reset_index(drop=True)
    al = permitted(shape, act, flags, tir, activity, chop_always, trend_gate)
    inside = np.zeros(len(K), bool)
    for (p, kind), g in K.groupby(['pair', 'kind'], observed=True):
        ser = al.get((p, kind))
        if ser is not None:
            inside[g.index.values] = ser.reindex(g.entry.values).fillna(False).values
    K['inside'] = inside
    st = shape.stack(); st.index.names = ['entry', 'pair']
    K = K.join(st.rename('state'), on=['entry', 'pair'])
    rows = []
    for (sl, ins), g in K.groupby(['slice', 'inside']):
        rows.append(dict(slice=sl, inside=bool(ins), trades=len(g), mean_R=g.R.mean(),
                         sum_R=g.R.sum(), win_rate=(g.R > 0).mean(),
                         R_per_year=g.R.sum() / len(years)))
    for (sl, s), g in K.groupby(['slice', 'state']):
        rows.append(dict(slice=sl, inside=s, trades=len(g), mean_R=g.R.mean(),
                         sum_R=g.R.sum(), win_rate=(g.R > 0).mean(),
                         R_per_year=g.R.sum() / len(years)))
    return pd.DataFrame(rows)


def shuffle_states(shape, rng):
    """Per pair, shuffle the ORDER of the state runs. Run lengths and state
    shares survive exactly; only which bar carries which run changes."""
    out = shape.copy()
    for p in shape.columns:
        s = shape[p].values.astype(object)
        ok = pd.notna(s)
        v = s[ok]
        if len(v) < 2:
            continue
        brk = np.flatnonzero(v[1:] != v[:-1]) + 1
        runs = np.split(v, brk)
        order = rng.permutation(len(runs))
        s[ok] = np.concatenate([runs[i] for i in order])
        out[p] = s
    return out


_SG = {}


def _init_shuf():
    W.S.load_costs()
    _SG['T'], _SG['M'] = W._worker_tables()
    _SG['TY'] = W.trade_year_sums(_SG['M'])
    _SG['shape'], _SG['act'] = load_states(os.environ['ROUTE_STATES'])
    _SG['flags'] = pd.read_pickle(os.environ['ROUTE_FLAGS'])


def _shuf_one(args):
    """One shuffled label set, routed ONCE, walked under both budgets."""
    os.environ['WF_NULL'] = '1'
    seed, tir, activity, chop_always, trend_gate = args
    try:
        rng = np.random.default_rng(seed)
        sh = shuffle_states(_SG['shape'], rng)
        al = permitted(sh, _SG['act'], _SG['flags'], tir, activity, chop_always, trend_gate)
        Tr, Mr, _ = route(_SG['T'], _SG['M'], al)
        TY = W.trade_year_sums(Mr)
        out = {}
        for bt, dipb, dayb in W.BUDGETS:
            r = W.walk(Tr, TY, Mr, {y: y for y in W.YEARS}, dipb, dayb, ['ALLPASS'], nocut=True)
            k = r['ALLPASS'][0]
            out[bt] = (k['median_year_pct'], k['total_return_pct'], k['max_dd_pct'], len(Tr))
        return out
    except Exception as e:
        return {'_err': type(e).__name__ + ': ' + str(e)[:120]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--states', required=True)
    ap.add_argument('--px', required=True, help='the 5pm px28 the crisis flag is computed on')
    ap.add_argument('--suffix', default='_cleanfield_4slice', help='engine pickles to route')
    ap.add_argument('--out', required=True, help='suffix for the routed pickles')
    ap.add_argument('--tir', choices=['excl', 'incl'], required=True)
    ap.add_argument('--activity', choices=['ignore', 'weak'], required=True)
    ap.add_argument('--shuffle-null', type=int, default=0)
    ap.add_argument('--chop-always', action='store_true', help='chop-core: chop slices take every entry (their own rules), only trend slices are gated')
    ap.add_argument('--trend-gate', choices=['trending', 'not-ranging', 'never', 'always'], default='trending', help="trend entries on TRENDING (trend axis), on NOT RANGING (chop axis), 'always' = UNGATED (every bar, crisis only, no activity gate), 'never' = no trend entry at all (CHOP-ONLY)")
    ap.add_argument('--no-crisis', action='store_true', help='reproduction check only: the engine\'s own routing has no crisis flag')
    ap.add_argument('--jobs', type=int, default=3)
    ap.add_argument('--step-files', action='store_true', help='route wf_*<suffix>_step<k>.pkl one step at a time (the full library will not fit as one frame)')
    a = ap.parse_args()
    W.S.load_costs()
    os.environ['WF_TAG'] = a.suffix; W.TAG = a.suffix
    src_T = W.OUT('wf_trades.pkl'); src_M = W.OUT('wf_marks.pkl')
    if a.step_files:
        # PER-STEP ROUTING (22 Sep): load, route and write one step at a time so the
        # full library's always-on stream never sits in memory as one frame. The first
        # step's trade table is enough for the state/coverage prints below.
        steps = sorted(int(f.rsplit('_step', 1)[1].split('.')[0]) for f in glob.glob(os.path.join(ROOTOUT, 'wf_trades%s_step*.pkl' % a.suffix)))
        assert steps, 'no wf_trades%s_step*.pkl' % a.suffix
        T = pd.read_pickle(os.path.join(ROOTOUT, 'wf_trades%s_step%d.pkl' % (a.suffix, steps[0]))); M = pd.DataFrame(columns=['sid', 'pair', 'day', 'dir', 'mark', 'tid', 'step'])
        print('SOURCE per-step wf_trades%s_step*.pkl: steps %s, step %d holds %d trades' % (a.suffix, steps, steps[0], len(T)), flush=True)
    else:
        steps = None
        T = pd.read_pickle(src_T); M = pd.read_pickle(src_M)
        print('SOURCE %s: %d trades, %d marks, %d strategies' % (src_T, len(T), len(M), T.sid.nunique()), flush=True)
    print('STATES %s' % os.path.abspath(a.states), flush=True)
    shape, act = load_states(a.states)
    print('  states %s -> %s, %d pairs; shares %s'
          % (shape.index.min().date(), shape.index.max().date(), shape.shape[1],
             shape.stack().value_counts(normalize=True).round(3).to_dict()), flush=True)
    flags = crisis_flags(a.px)
    if a.no_crisis:
        flags[:] = False
        print('  crisis flag DISABLED (reproduction of the engine\'s own routing)', flush=True)
    al = permitted(shape, act, flags, a.tir, a.activity, a.chop_always, a.trend_gate)
    cov = {k: float(v.loc['2011':'2020'].mean()) for k, v in al.items()}
    print('  permitted-bar share 2011-2020: trend %.3f  chop %.3f'
          % (np.mean([v for (p, k), v in cov.items() if k == 'trend']),
             np.mean([v for (p, k), v in cov.items() if k == 'chop'])), flush=True)

    W.TAG = a.out; os.environ['WF_TAG'] = a.out
    if a.shuffle_null:
        os.environ['ROUTE_STATES'] = os.path.abspath(a.states)
        fl = W.OUT('route_flags.pkl'); pd.to_pickle(flags, fl); os.environ['ROUTE_FLAGS'] = fl
        os.environ['WF_TAG'] = a.suffix          # workers load the UNROUTED source
        os.environ['WF_EXPECT_SIDS'] = str(int(T.sid.nunique()))
        import multiprocessing as mp
        rows = []
        t0 = time.time()
        args = [(20260913 + i, a.tir, a.activity, a.chop_always, a.trend_gate) for i in range(a.shuffle_null)]
        with mp.Pool(a.jobs, initializer=_init_shuf) as pool:
            got = pool.map(_shuf_one, args, chunksize=1)
        errs = [g['_err'] for g in got if '_err' in g]
        for i, g in enumerate(got):
            if '_err' in g:
                continue
            for bt, (med, tot, dd, n) in g.items():
                rows.append(dict(budget=bt, draw=i, median_year_pct=med, total_return_pct=tot, max_dd_pct=dd, trades=n))
        if errs:
            print('  WARNING %d of %d shuffle draws failed: %s' % (len(errs), len(got), errs[0]), flush=True)
        print('  regime-shuffled null: %d draws x both budgets in %.1f min' % (len(got) - len(errs), (time.time() - t0) / 60), flush=True)
        W.TAG = a.out; os.environ['WF_TAG'] = a.out
        N = pd.DataFrame(rows)
        N.to_csv(W.OUT('walkforward_null_regimeshuffle_3slice.csv'), index=False)
        real = pd.read_csv(W.OUT('walkforward_structures_3slice.csv'), comment='#')
        summ = []
        for bt, g in N.groupby('budget'):
            v = g.median_year_pct.values
            rl = float(real[(real.budget == bt) & (real.structure == 'NO_CUT')].median_year_pct.iloc[0])
            summ.append(dict(budget=bt, structure='NO_CUT', real_median_year=rl, n=len(v),
                             null_mean=float(v.mean()), null_p95=float(np.percentile(v, 95)),
                             null_max=float(v.max()), pctile_of_real=float(100 * (v < rl).mean()),
                             p_value=float((v >= rl).mean()), p_resolution=round(1 / len(v), 3)))
            print('  %-6s real %.3f%%  shuffled-regime mean %.3f%%  p95 %.3f%%  max %.3f%%  p=%.3f'
                  % (bt, rl, v.mean(), np.percentile(v, 95), v.max(), (v >= rl).mean()), flush=True)
        pd.DataFrame(summ).to_csv(W.OUT('walkforward_null_regimeshuffle_summary_3slice.csv'), index=False)
        return

    if steps:
        kept = tot = 0
        for si in steps:
            Ts = pd.read_pickle(os.path.join(ROOTOUT, 'wf_trades%s_step%d.pkl' % (a.suffix, si)))
            Ms = pd.read_pickle(os.path.join(ROOTOUT, 'wf_marks%s_step%d.pkl' % (a.suffix, si)))
            Trs, Mrs, okk = route(Ts, Ms, al)
            pd.to_pickle(Trs, os.path.join(ROOTOUT, 'wf_trades%s_step%d.pkl' % (a.out, si)))
            pd.to_pickle(Mrs, os.path.join(ROOTOUT, 'wf_marks%s_step%d.pkl' % (a.out, si)))
            kept += len(Trs); tot += len(Ts)
            print('  step %d routed: kept %d of %d trades (%.1f%%)' % (si, len(Trs), len(Ts), 100 * len(Trs) / max(len(Ts), 1)), flush=True)
            del Ts, Ms, Trs, Mrs
        pd.to_pickle(al, W.OUT('route_allowed.pkl'))
        print('ROUTED per step: kept %d of %d trades (%.1f%%); wrote wf_*%s_step*.pkl and %s'
              % (kept, tot, 100 * kept / max(tot, 1), a.out, W.OUT('route_allowed.pkl')), flush=True)
        D = dependence(T, shape, act, flags, a.tir, a.activity, years=[2016, 2017, 2018, 2019, 2020], chop_always=a.chop_always, trend_gate=a.trend_gate)
        D.to_csv(W.OUT('walkforward_regime_dependence.csv'), index=False)
        return
    Tr, Mr, ok = route(T, M, al)
    K = T[['sid']].copy(); K['kind'] = K.sid.astype(str).map(kind_of); K['ok'] = ok
    K['yr'] = T.entry.dt.year
    print('ROUTED: kept %d of %d trades (%.1f%%); by kind %s; trade years %s'
          % (len(Tr), len(T), 100 * len(Tr) / len(T),
             K.groupby('kind').ok.mean().round(3).to_dict(),
             K[K.yr >= 2016].groupby('kind').ok.mean().round(3).to_dict()), flush=True)
    pd.to_pickle(Tr, W.OUT('wf_trades.pkl')); pd.to_pickle(Mr, W.OUT('wf_marks.pkl'))
    pd.to_pickle(al, W.OUT('route_allowed.pkl'))
    print('  wrote %s, %s, %s' % (W.OUT('wf_trades.pkl'), W.OUT('wf_marks.pkl'), W.OUT('route_allowed.pkl')), flush=True)
    D = dependence(T, shape, act, flags, a.tir, a.activity, years=[2016, 2017, 2018, 2019, 2020], chop_always=a.chop_always, trend_gate=a.trend_gate)
    D.to_csv(W.OUT('walkforward_regime_dependence.csv'), index=False)
    print(D[D.inside.isin([True, False])].to_string(index=False, float_format=lambda v: '%8.3f' % v), flush=True)


if __name__ == '__main__':
    main()
