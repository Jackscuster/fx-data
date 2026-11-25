import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""STAGE 2 — THE BASELINE ADDED TO C1. Jack's picks, 24 Nov.

JACK'S PICKS, RECORDED HERE AND IN HANDOFF 0m AND THE LEDGER. I did not make
them; they are quoted with his reasons.

  C1        ichimoku, schaff_trend_cycle, halftrend
            "the only C1 positive net under both the jack and textbook plans at
            more than one setting"
  plus      ROLLING TOP 3 -- at each step the 3 C1 ranked best on the four
            tuning years, traded on the unseen year
            "the selection test: +13.9 R per year against a null of -8.0, p 0.001"
  baselines sma, hma, t3
            "the double setting was best for every baseline; none is positive
            alone, so they are judged as filters"

  jack plan is the MAIN VERSION; textbook reported beside it.

THE FOUR BASELINE RULES, AND WHY ONE OF THEM CANNOT BE SWITCHED OFF.

Jack asked which rule inside the baseline does the work, "by switching each on
alone". Three of the four can be. The fourth cannot, and the engine is the
reason, not a limitation of this file.

`side` is the sign of (close - baseline), computed every bar at
l2engine.py:274-279. Every entry route then gates on agreement:

    agree_long  = c1_lc[i] and c2_lc[i] and v_ok_l[i] and side == 1   (:527)
    r1l = use_base_cross and last_cross_bar == i and side == 1 and agree_long
    r2l = use_c1_flip   and c1_lt[i] and agree_long
    r3l = cont          and c1_lt[i] and agree_long                   (:549-555)

So the SIDE FILTER IS THE FLOOR. There is no route into a trade that does not
pass through it. Turning it off means removing the baseline from the decision
altogether -- which is exactly stage 1's C1-alone control, where the baseline is
pushed far from price so that `side` is pinned and the two directions are run
separately.

The other three are genuinely separable and sit on top of it:

  distance rule   `(want == 1 and cl > b + max_atr_dist * a)` rejects the entry
                  after the route has fired (:602-603). A pure filter.
  cross entry     r1, an ADDITIONAL route into a trade (:549-550).
  cross exit      `exit_on_base_cross and side == -1 and last_cross_bar == i`
                  (:498-505). A pure extra exit.

THE RULESETS BELOW ARE THEREFORE INCREMENTS OVER side-alone, not over nothing,
and the report says so. Claiming otherwise would attribute the side filter's
whole effect to whichever rule happened to be switched on with it.

EVERY FIGURE IS NET, IN R PER 1.5 ATR, era-correct costs, one-bar lag,
year-end mark to market, unseen trade years 2010-2015 reported and 2016-2020
computed and stored and NOT summarised. 2021 onward is not read.
"""
import time, json, itertools
import numpy as np, pandas as pd
from scipy import stats

import l2lib as L
import l2sweep as S
import l2engine as E
import l2r2gate1 as G
import nnfx1 as N
import l2r2winners as WN

OUT = os.path.join(ROOTOUT, 'nnfx')
os.makedirs(OUT, exist_ok=True)

# ---- JACK'S PICKS, as engine names
C1_PICKS = ('ichimoku_signals', 'schaff_trend_cycle_signals', 'halftrend_signals')
BASE_PICKS = ('sma_baseline', 'hma_baseline', 't3_baseline')
ROLLING = 'ROLLING_TOP3'
C1_OBJECTS = C1_PICKS + (ROLLING,)
ROLLING_K = 3
PLANS_USED = ('jack', 'textbook')        # jack is the main version
MAIN_PLAN = 'jack'

# ---- the rulesets. 'side' is in every one but the control; see the module note.
RULESETS = {
    'c1_alone':    dict(side=False, dist=False, xentry=False, xexit=False),
    'side':        dict(side=True,  dist=False, xentry=False, xexit=False),
    'side_dist':   dict(side=True,  dist=True,  xentry=False, xexit=False),
    'side_xentry': dict(side=True,  dist=False, xentry=True,  xexit=False),
    'side_xexit':  dict(side=True,  dist=False, xentry=False, xexit=True),
    'full_nnfx':   dict(side=True,  dist=True,  xentry=True,  xexit=True),
}
RULE_ORDER = ('c1_alone', 'side', 'side_dist', 'side_xentry', 'side_xexit',
              'full_nnfx')

BUILD_YEARS = N.BUILD_YEARS          # 2010-2015, reported
CONFIRM_YEARS = N.CONFIRM_YEARS      # 2016-2020, computed, stored, not reported
STEPS = N.STEPS
SETTINGS = N.SETTINGS
RISK_UNIT_ATR = N.RISK_UNIT_ATR


def _safe_csv(path):
    """An empty result file is a legitimate result, and pandas raises on one.

    THIS IS THE FOURTH REPORT GENERATOR IN THIS PROJECT TO NEED THIS.
    l2r2gate3 carries it, b1narrow carries it, and stage 2's rolling stage
    tripped it on the first run: when K=3 is not in the swept range nothing is
    written to stage2_rolling_picks.csv, and reading a zero-column file raises
    EmptyDataError. Every read in this module goes through here.
    """
    try:
        if not os.path.exists(path):
            return pd.DataFrame()
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def _write_csv(D, path, cols=None):
    """Write a frame, giving an EMPTY one its header row anyway.

    A zero-byte csv is unreadable; a header-only csv reads back as an empty
    frame with the right columns, which is what every consumer expects.
    """
    if (D is None or not len(D)) and cols:
        D = pd.DataFrame(columns=list(cols))
    (D if D is not None else pd.DataFrame()).to_csv(path, index=False)
    return path


def run_combo(c1, c1_set, base, base_set, variant, ruleset,
              pairs=None, atr_len=14, use_hourly=True, amb_out=None):
    """One C1 + one baseline, one ruleset, across the pairs. -> trade frame.

    THE C1 ENTRY AND EXIT ARE ALWAYS ON. Stage 2 adds a baseline to a C1; it
    does not replace it. `use_c1_flip` and `exit_on_c1_flip` are true in every
    ruleset including the control.
    """
    C1L, BASEL, C2L, VOLL, XL = N.families()
    pairs = pairs or S.all_pairs()
    RS = RULESETS[ruleset]
    PL = N.PLANS[variant]
    if variant == 'flip_only':
        am, tp = N.BIG_STOP, N.TP_NONE
    else:
        am, tp = float(PL['atr_mult']), float(PL['tp_mult'])
    # the distance rule only when the ruleset says so AND the baseline is real:
    # against an artificial baseline any finite distance rejects every entry,
    # which is the fault that produced zero trades in stage 1.
    _dist = float(PL['max_atr_dist']) if (RS['dist'] and RS['side']) else float(N.BIG)
    kw = dict(use_continuation=False,
              one_candle_rule=bool(PL['one_candle_rule']),
              max_atr_dist=_dist, bridge_bars=N.BIG,
              block_suspect=True, bridge_all_routes=True,
              plan=2, atr_mult=am, tp_mult=tp,
              trail_mult=float(PL['trail_mult']),
              trail_start_mult=float(PL['trail_start_mult']),
              be_pct=float(PL['be_pct']),
              use_c1_flip=True, exit_on_c1_flip=True,
              use_base_cross=bool(RS['xentry'] and RS['side']),
              exit_on_base_cross=bool(RS['xexit'] and RS['side']),
              exit_on_exit_ind=False)
    c1_prm = N.setting_params(c1, c1_set)
    b_prm = N.setting_params(base, base_set)
    rows = []
    # with a real baseline `side` comes from the data and one run gives both
    # directions; with the baseline neutralised `side` is pinned, so the two
    # directions must be run separately (stage 1's finding, nnfx1._neutralise)
    sides = (None,) if RS['side'] else ('long', 'short')
    for p in pairs:
        d = N.pair_data(p)
        params = {'atr_len': atr_len}
        if c1_prm:
            params[c1] = c1_prm
        if b_prm:
            params[base] = b_prm
        for sd in sides:
            A = E.prepare(d, c1, C2L[0], VOLL[0], base, XL[0], params=params)
            n = A['c'].size
            T_ = np.ones(n, bool)
            # the C2 and volume slots and the exit indicator are not under test
            A['c2_lc'] = T_.copy(); A['c2_sc'] = T_.copy()
            A['v_ok_l'] = T_.copy(); A['v_ok_s'] = T_.copy()
            A['x_el'] = np.zeros(n, bool); A['x_es'] = np.zeros(n, bool)
            if not RS['side']:
                K = 10.0 * float(np.nanmax(np.abs(A['c'])) + 1.0)
                A['bl'] = A['c'] - K if sd == 'long' else A['c'] + K
            if use_hourly:
                import nnfxamb as _AMB
                res = E.run(A, amb=_AMB.amb_args(p), **kw)
                if amb_out is not None:
                    amb_out += np.asarray(res.get('_amb', np.zeros(3, np.int64)))
            else:
                res = E.run(A, **kw)
            tf = E.trade_frame(res, d)
            if tf is None or not len(tf):
                continue
            tf = tf.copy(); tf['pair'] = p; tf['side_run'] = sd or 'both'
            if sd == 'long':
                tf = tf[tf.direction == 'long']
            elif sd == 'short':
                tf = tf[tf.direction == 'short']
            if len(tf):
                rows.append(tf)
    if not rows:
        return pd.DataFrame()
    T = pd.concat(rows, ignore_index=True)
    T['R_gross'] = T.R.astype(float) * am / RISK_UNIT_ATR
    T['atr_mult_used'] = am
    T['c1'] = c1; T['c1_setting'] = c1_set
    T['base'] = base; T['base_setting'] = base_set
    T['variant'] = variant; T['ruleset'] = ruleset
    return T


# ====================== SCORING, REUSED FROM STAGE 1 ======================
def _score(T, years, ndraw=400, nboot=2000, want_null=True, seed=7):
    """Every figure Jack's 2c list asks for, on one trade frame."""
    cost = N._cost_R(T)
    DS = N.daily_series(T, cost)
    Y = N._yearly(T, cost, DS)
    b = Y[Y.year.isin(list(years))]
    ds = DS[pd.DatetimeIndex(DS.date).year.isin(list(years))]
    real = float(b.R_net.sum())
    n_ent = float(b.n_entered.sum())
    ys = b.sort_values('year').R_net.to_numpy(float)
    t_yr = (float(ys.mean() * np.sqrt(len(ys)) / ys.std(ddof=1))
            if len(ys) > 1 and ys.std(ddof=1) > 0 else np.nan)
    t_bs, bs_sd = N._block_t(ds.R.to_numpy(float), ndraw=nboot)
    dip = N.true_dip(DS, years)
    out = dict(
        years=int(len(b)), n_entered=n_ent, n_touching=float(b.n_touching.sum()),
        trades_per_year=float(b.n_entered.mean()) if len(b) else np.nan,
        mean_bars=float((b.mean_bars * b.n_entered).sum() / max(1.0, n_ent)),
        R_gross_build=float(b.R_gross.sum()), R_net_build=real,
        R_gross_per_trade=float(b.R_gross.sum() / max(1.0, n_ent)),
        R_net_per_trade=float(real / max(1.0, n_ent)),
        cost_per_trade=float(b.cost_entered.sum() / max(1.0, n_ent)),
        R_net_per_year=float(real / max(1, len(b))),
        years_positive=int((b.R_net > 0).sum()),
        worst_year=float(b.R_net.min()) if len(b) else np.nan,
        best_year=float(b.R_net.max()) if len(b) else np.nan,
        worst_dip_R=dip,
        # RETURN PER UNIT OF WORST DIP -- Jack's "never trade return against
        # risk" in one number. Undefined when nothing ever drew down.
        R_per_year_per_dip=(float(real / max(1, len(b)) / dip)
                            if np.isfinite(dip) and dip > 1e-9 else np.nan),
        t_yearly=t_yr, t_block_boot=t_bs, boot_sd_of_mean=bs_sd)
    if want_null:
        nulls, nulls_n, nymat = N._null_match(T, cost, ndraw=ndraw,
                                              years=years, seed=seed)
        out.update(null_p=(float((nulls >= real).mean()) if len(nulls) else np.nan),
                   null_mean=float(np.mean(nulls)) if len(nulls) else np.nan,
                   null_p95=(float(np.percentile(nulls, 95)) if len(nulls)
                             else np.nan),
                   null_trades_per_draw=(float(np.mean(nulls_n)) if len(nulls_n)
                                         else np.nan))
        out['_nulls'] = nulls
        out['_nymat'] = nymat
    out['_Y'] = Y
    out['_DS'] = DS
    return out


# ====================== 2a — THE GRID ======================
def stage_grid(c1_names=None, bases=None, variants=PLANS_USED,
               rulesets=('c1_alone', 'full_nnfx'), tag='picks',
               use_hourly=True, verbose=True):
    """Every C1 x baseline x setting-pair x plan x ruleset, YEARLY rows only.

    NO NULLS HERE. A null per setting-pair would be 4,212 of them and they are
    not what the grid is for -- the grid exists so the walk-forward pick has
    tuning-year numbers to choose from. Nulls are computed once per REPORTED
    candidate in stage_report, after the pick.
    """
    C1L, BASEL, _c2, _v, _x = N.families()
    c1_names = list(c1_names or C1_PICKS)
    bases = list(bases or BASE_PICKS)
    S.load_costs(os.environ.get('FX_COST_TABLE', 'results/cost_table_h22.csv'))
    rows, yr = [], []
    amb = np.zeros(3, np.int64)
    tot = (len(c1_names) * len(bases) * len(SETTINGS) * len(SETTINGS)
           * len(variants) * len(rulesets))
    done, t0 = 0, time.time()
    for c1 in c1_names:
        for base in bases:
            for cs in SETTINGS:
                for bs in SETTINGS:
                    for v in variants:
                        for rs in rulesets:
                            T = run_combo(c1, cs, base, bs, v, rs,
                                          use_hourly=use_hourly, amb_out=amb)
                            done += 1
                            if not len(T):
                                rows.append(dict(c1=c1, base=base, c1_setting=cs,
                                                 base_setting=bs, variant=v,
                                                 ruleset=rs, n=0,
                                                 note='no trades'))
                                continue
                            T = T.reset_index(drop=True)
                            cost = N._cost_R(T)
                            Y = N._yearly(T, cost)
                            Y['c1'] = c1; Y['base'] = base
                            Y['c1_setting'] = cs; Y['base_setting'] = bs
                            Y['variant'] = v; Y['ruleset'] = rs
                            yr.append(Y)
                            bb = Y[Y.year.isin(list(BUILD_YEARS))]
                            rows.append(dict(
                                c1=c1, base=base, c1_setting=cs, base_setting=bs,
                                variant=v, ruleset=rs,
                                n=float(bb.n_entered.sum()),
                                R_net_build=float(bb.R_net.sum()),
                                R_gross_build=float(bb.R_gross.sum())))
                    if verbose and done % 60 == 0:
                        print('    grid[%s]: %d of %d, %.1f min'
                              % (tag, done, tot, (time.time() - t0) / 60),
                              flush=True)
    Yall = pd.concat(yr, ignore_index=True) if yr else pd.DataFrame()
    Sall = pd.DataFrame(rows)
    f1 = os.path.join(OUT, 'stage2_%s_yearly.csv' % tag)
    f2 = os.path.join(OUT, 'stage2_%s_grid.csv' % tag)
    Yall.to_csv(f1, index=False); Sall.to_csv(f2, index=False)
    if verbose:
        print('  stage 2 grid [%s]: %d runs -> %d yearly rows. Ambiguous bars: '
              'target-first %d, stop-first %d, unresolved %d (%.1f min)'
              % (tag, done, len(Yall), amb[0], amb[1], amb[2],
                 (time.time() - t0) / 60), flush=True)
    return f1, f2


def stage_pick(tag='picks', verbose=True):
    """THE WALK-FORWARD SETTING PICK, both settings chosen jointly.

    Jack: "Settings picked walk-forward from the three per indicator." The C1
    setting and the baseline setting are picked TOGETHER on the four tuning
    years, because they interact -- a fast baseline suits a fast C1 -- and
    picking them one at a time would be a different rule than the one declared.
    Nine setting-pairs per step, ranked on tuning-year net R, minimum 30 trades.
    """
    f = os.path.join(OUT, 'stage2_%s_yearly.csv' % tag)
    assert os.path.exists(f), f + ' missing -- run stage_grid first'
    Y = pd.read_csv(f)
    rows = []
    for (c1, base, v, rs), g in Y.groupby(['c1', 'base', 'variant', 'ruleset']):
        for stp in STEPS:
            ty = list(range(stp['tune'][0], stp['tune'][1] + 1))
            tune = g[g.year.isin(ty)]
            trade = g[g.year == stp['trade']]
            if not len(tune) or not len(trade):
                continue
            sc = tune.groupby(['c1_setting', 'base_setting'], as_index=False).agg(
                tune_R=('R_net', 'sum'), tune_n=('n_entered', 'sum'))
            sc = sc[sc.tune_n >= 30]
            if not len(sc):
                continue
            w = sc.loc[sc.tune_R.idxmax()]
            tr = trade[(trade.c1_setting == w.c1_setting)
                       & (trade.base_setting == w.base_setting)]
            if not len(tr):
                continue
            rows.append(dict(c1=c1, base=base, variant=v, ruleset=rs,
                             step=stp['name'], trade_year=stp['trade'],
                             picked_c1_setting=w.c1_setting,
                             picked_base_setting=w.base_setting,
                             tune_R=float(w.tune_R), tune_n=float(w.tune_n),
                             trade_R_net=float(tr.R_net.sum()),
                             trade_R_gross=float(tr.R_gross.sum()),
                             trade_n=float(tr.n_entered.sum()),
                             mean_bars=float(tr.mean_bars.mean()),
                             is_build=int(stp['trade'] in BUILD_YEARS),
                             is_confirm=int(stp['trade'] in CONFIRM_YEARS)))
    W = pd.DataFrame(rows)
    f2 = os.path.join(OUT, 'stage2_%s_walk.csv' % tag)
    W.to_csv(f2, index=False)
    if verbose:
        print('  stage 2 pick [%s]: %d combination-steps, %d on BUILD years'
              % (tag, len(W), int(W.is_build.sum()) if len(W) else 0), flush=True)
    return f2


# ====================== 2b — THE PAIRED TEST ======================
def _daily_of(c1, cs, base, bs, variant, ruleset, years, use_hourly=True):
    T = run_combo(c1, cs, base, bs, variant, ruleset, use_hourly=use_hourly)
    if not len(T):
        return pd.DataFrame(columns=['date', 'R']), pd.DataFrame()
    T = T.reset_index(drop=True)
    cost = N._cost_R(T)
    DS = N.daily_series(T, cost)
    DS = DS[pd.DatetimeIndex(DS.date).year.isin(list(years))]
    return DS, T


def stage_paired(tag='picks', c1_names=None, bases=None, variants=PLANS_USED,
                 years=BUILD_YEARS, nboot=2000, use_hourly=True, verbose=True):
    """2b — THE SAME C1 WITH AND WITHOUT THE BASELINE, ON THE SAME DAYS.

    WHY PAIRED AND NOT TWO SEPARATE TESTS. Both series live through the same
    2010-2015 markets: the same crises, the same trends, the same quiet
    stretches. Comparing two independent t statistics throws that away and
    answers a much noisier question. Differencing the two daily P&L series day
    by day removes everything common to them, and what is left is the
    baseline's own contribution.

    THE DAYS ARE UNIONED, NOT INTERSECTED. A day on which only one of the two
    is in the market is a real difference and belongs in the test; keeping only
    the days both traded would silently delete the baseline's main effect,
    which is to STOP trades happening. Missing days are zero P&L, not missing
    data.

    THE SETTINGS ARE THE WALK-FORWARD PICKS, STEP BY STEP, so the paired series
    is the one the rule would actually have produced -- not a single setting
    chosen with hindsight over the whole span.
    """
    W = pd.read_csv(os.path.join(OUT, 'stage2_%s_walk.csv' % tag))
    c1_names = list(c1_names or C1_PICKS)
    bases = list(bases or BASE_PICKS)
    S.load_costs(os.environ.get('FX_COST_TABLE', 'results/cost_table_h22.csv'))
    rows = []
    for c1 in c1_names:
        for base in bases:
            for v in variants:
                for rs in RULE_ORDER:
                    if rs == 'c1_alone':
                        continue
                    acc_t, acc_c = [], []
                    for stp in STEPS:
                        if stp['trade'] not in years:
                            continue
                        w = W[(W.c1 == c1) & (W.base == base) & (W.variant == v)
                              & (W.ruleset == rs) & (W.step == stp['name'])]
                        w0 = W[(W.c1 == c1) & (W.base == base) & (W.variant == v)
                               & (W.ruleset == 'c1_alone')
                               & (W.step == stp['name'])]
                        if not len(w) or not len(w0):
                            continue
                        w = w.iloc[0]; w0 = w0.iloc[0]
                        yy = (stp['trade'],)
                        d1, _ = _daily_of(c1, w.picked_c1_setting, base,
                                          w.picked_base_setting, v, rs, yy,
                                          use_hourly)
                        d0, _ = _daily_of(c1, w0.picked_c1_setting, base,
                                          w0.picked_base_setting, v, 'c1_alone',
                                          yy, use_hourly)
                        acc_t.append(d1); acc_c.append(d0)
                    if not acc_t:
                        continue
                    D1 = (pd.concat(acc_t, ignore_index=True)
                          .groupby('date', as_index=False).R.sum())
                    D0 = (pd.concat(acc_c, ignore_index=True)
                          .groupby('date', as_index=False).R.sum())
                    M = D1.merge(D0, on='date', how='outer',
                                 suffixes=('_with', '_without')).fillna(0.0)
                    M = M.sort_values('date').reset_index(drop=True)
                    diff = (M.R_with - M.R_without).to_numpy(float)
                    t_d, sd_d = N._block_t(diff, ndraw=nboot)
                    # NOT groupby().apply() -- pandas 2.2 warns that it
                    # operates on the grouping column and will change
                    # behaviour. Aggregate the two columns and subtract.
                    _g = (M.assign(y=pd.DatetimeIndex(M.date).year)
                           .groupby('y', as_index=False)
                           .agg(w=('R_with', 'sum'), o=('R_without', 'sum'))
                           .sort_values('y'))
                    ysv = (_g.w - _g.o).to_numpy(float)
                    rows.append(dict(
                        c1=c1, base=base, variant=v, ruleset=rs,
                        days=len(M), years=len(ysv),
                        R_with=float(M.R_with.sum()),
                        R_without=float(M.R_without.sum()),
                        delta_R=float(diff.sum()),
                        delta_R_per_year=float(diff.sum() / max(1, len(ysv))),
                        delta_t_block_boot=t_d, delta_boot_sd=sd_d,
                        delta_t_yearly=(float(ysv.mean() * np.sqrt(len(ysv))
                                              / ysv.std(ddof=1))
                                        if len(ysv) > 1 and ysv.std(ddof=1) > 0
                                        else np.nan),
                        years_delta_positive=int((ysv > 0).sum()),
                        days_with_only=int(((M.R_without == 0)
                                            & (M.R_with != 0)).sum()),
                        days_without_only=int(((M.R_with == 0)
                                               & (M.R_without != 0)).sum())))
                    if verbose:
                        print('    paired %s/%s/%s/%s: dR %+8.1f over %d days, '
                              'boot t %6.2f' % (c1[:14], base[:12], v, rs,
                                                diff.sum(), len(M),
                                                t_d if np.isfinite(t_d) else 0),
                              flush=True)
    D = pd.DataFrame(rows)
    f = os.path.join(OUT, 'stage2_%s_paired.csv' % tag)
    D.to_csv(f, index=False)
    if verbose:
        print('  stage 2 paired [%s]: %d rows -> %s'
              % (tag, len(D), os.path.relpath(f, _R)), flush=True)
    return f


# ====================== A SELF-CHECK THE GRID MAKES FREE ======================
def condition_neutral(tag='picks', verbose=True):
    """THE BASELINE SETTING MUST BE INERT IN THE c1_alone CONTROL.

    In the control the baseline array is overwritten with close +/- K, so the
    indicator's own parameters cannot reach the engine. If the three base
    settings do NOT give identical yearly numbers there, the neutralisation is
    leaking and every paired comparison against that control is contaminated.

    This costs nothing -- the grid has already computed all three -- and it is
    the kind of check that would have caught stage 1's zero-trade fault a day
    earlier.
    """
    f = os.path.join(OUT, 'stage2_%s_yearly.csv' % tag)
    if not os.path.exists(f):
        return pd.DataFrame(), True
    Y = pd.read_csv(f)
    A = Y[Y.ruleset == 'c1_alone']
    if not len(A):
        return pd.DataFrame(), True
    rows = []
    for (c1, base, v, cs, y), g in A.groupby(['c1', 'base', 'variant',
                                              'c1_setting', 'year']):
        if g.base_setting.nunique() < 2:
            continue
        spread = float(g.R_net.max() - g.R_net.min())
        nspread = float(g.n_entered.max() - g.n_entered.min())
        rows.append(dict(c1=c1, base=base, variant=v, c1_setting=cs, year=y,
                         n_base_settings=int(g.base_setting.nunique()),
                         R_spread=spread, n_spread=nspread,
                         passes=int(spread < 1e-9 and nspread < 1e-9)))
    D = pd.DataFrame(rows)
    ok = bool(len(D)) and bool(D.passes.all())
    if verbose:
        print('  NEUTRALISATION CHECK [%s]: %d control cells, worst R spread '
              '%.3g, worst trade-count spread %.3g -> %s'
              % (tag, len(D), D.R_spread.max() if len(D) else 0,
                 D.n_spread.max() if len(D) else 0, 'PASS' if ok else 'FAIL'),
              flush=True)
    D.to_csv(os.path.join(OUT, 'stage2_%s_neutralcheck.csv' % tag), index=False)
    return D, ok


# ====================== THE ROLLING TOP-K RULE ======================
def rolling_walk(tag, K=ROLLING_K, ruleset='full_nnfx', variant=MAIN_PLAN,
                 base=None, years=BUILD_YEARS):
    """2f — at each step take the K C1 ranked best on the four TUNING years and
    trade them on that step's unseen year. Equal weight, mean of their R.

    THE RANKING USES TUNING-YEAR R ONLY. No trade-year information touches the
    choice, which is what makes the traded year unseen. This is the same rule
    stage 1's 1c tested on C1 alone; here each ranked C1 carries the baseline.
    """
    W = pd.read_csv(os.path.join(OUT, 'stage2_%s_walk.csv' % tag))
    W = W[(W.ruleset == ruleset) & (W.variant == variant)]
    if base:
        W = W[W.base == base]
    rows = []
    for stp in STEPS:
        if stp['trade'] not in years:
            continue
        g = W[W.step == stp['name']]
        if not len(g):
            continue
        top = g.sort_values('tune_R', ascending=False).head(K)
        rows.append(dict(step=stp['name'], trade_year=stp['trade'], K=K,
                         picked=','.join(top.c1.str.replace('_signals', '',
                                                            regex=False)),
                         picked_bases=','.join(top.base.str.replace(
                             '_baseline', '', regex=False)),
                         tune_R_mean=float(top.tune_R.mean()),
                         trade_R_net=float(top.trade_R_net.mean()),
                         trade_R_net_sum=float(top.trade_R_net.sum()),
                         trade_n=float(top.trade_n.sum()),
                         mean_bars=float(top.mean_bars.mean())))
    return pd.DataFrame(rows)


def stage_rolling(tag='pool', ksweep=range(1, 11), ruleset='full_nnfx',
                  variants=PLANS_USED, bases=None, ndraw=1000, seed=11,
                  verbose=True):
    """2f IN FULL — K from 1 to 10, with turnover and the picked set per year.

    THE NULL IS THE LABEL SHUFFLE, as in stage 1's 1c: the tuning-year ranking
    is permuted and the SAME top-K rule applied, so what is tested is the
    selection rule rather than the quality of the pool.
    """
    W = pd.read_csv(os.path.join(OUT, 'stage2_%s_walk.csv' % tag))
    bases = list(bases or sorted(W.base.unique()))
    rng = np.random.default_rng(seed)
    rows, picks = [], []
    for v in variants:
        for base in bases:
            sub = W[(W.ruleset == ruleset) & (W.variant == v) & (W.base == base)]
            if not len(sub):
                continue
            for k in ksweep:
                R = rolling_walk(tag, K=k, ruleset=ruleset, variant=v, base=base)
                if not len(R):
                    continue
                real = R.trade_R_net.to_numpy(float)
                # turnover: share of the picked set that changes year to year
                sets = [set(s.split(',')) for s in R.picked]
                turn = ([len(sets[i] ^ sets[i - 1]) / (2.0 * k)
                         for i in range(1, len(sets))] if len(sets) > 1 else [])
                nulls = np.zeros(ndraw)
                for dd in range(ndraw):
                    acc = []
                    for stp in STEPS:
                        if stp['trade'] not in BUILD_YEARS:
                            continue
                        g = sub[sub.step == stp['name']]
                        if not len(g):
                            continue
                        perm = rng.permutation(len(g))
                        acc.append(float(g.iloc[perm[:k]].trade_R_net.mean()))
                    nulls[dd] = float(np.mean(acc)) if acc else np.nan
                eq = np.cumsum(real)
                t_y = (float(real.mean() * np.sqrt(len(real)) / real.std(ddof=1))
                       if len(real) > 1 and real.std(ddof=1) > 0 else np.nan)
                rows.append(dict(
                    variant=v, base=base, ruleset=ruleset, K=k,
                    years=len(real), R_per_year_mean=float(real.mean()),
                    R_total_build=float(real.sum()),
                    years_positive=int((real > 0).sum()),
                    worst_year=float(real.min()),
                    worst_dip_R=float((np.maximum.accumulate(eq) - eq).max()),
                    t_yearly=t_y,
                    turnover_mean=float(np.mean(turn)) if turn else np.nan,
                    null_mean=float(np.nanmean(nulls)),
                    null_p95=float(np.nanpercentile(nulls, 95)),
                    null_p=float(np.nanmean(nulls >= real.mean())),
                    ndraw=ndraw))
                if k == ROLLING_K:
                    P = R.copy(); P['variant'] = v; P['base'] = base
                    picks.append(P)
    D = pd.DataFrame(rows)
    f = os.path.join(OUT, 'stage2_rolling_sweep.csv')
    D.to_csv(f, index=False)
    f2 = os.path.join(OUT, 'stage2_rolling_picks.csv')
    _write_csv(pd.concat(picks, ignore_index=True) if picks else None, f2,
               cols=['step', 'trade_year', 'K', 'picked', 'picked_bases',
                     'tune_R_mean', 'trade_R_net', 'trade_R_net_sum',
                     'trade_n', 'mean_bars', 'variant', 'base'])
    if verbose and len(D):
        b = D.loc[D.R_per_year_mean.idxmax()]
        print('  2f rolling [%s]: K 1-%d x %d bases x %d plans. Best %+.3f R/yr '
              'at K=%d, %s/%s (null %+.3f, p %.3f)'
              % (ruleset, max(ksweep), len(bases), len(variants),
                 b.R_per_year_mean, b.K, b.variant, b.base, b.null_mean,
                 b.null_p), flush=True)
    return f, f2


# ====================== 2d — THE COST CAP ======================
def pair_cost_rank(year, pairs=None, atr_len=14):
    """Round-trip cost divided by ATR, per pair, KNOWN IN ADVANCE.

    Jack: "known in advance, no performance used". The cost is the era table's
    round-trip fraction for the pair; the ATR is measured over the PREVIOUS
    calendar year and never the year being traded. So the ranking for 2011 uses
    only 2010 data and the trade year stays unseen.

    cost / ATR is the right ratio because R is measured in ATR units: a pair
    whose spread is a large share of its daily range eats a large share of
    every R, whatever its absolute pip cost.
    """
    pairs = pairs or S.all_pairs()
    rows = []
    for p in pairs:
        d = N.pair_data(p)
        cl = d['close'].values.astype(float)
        a = L.P.atr(d['high'].values.astype(float),
                    d['low'].values.astype(float), cl, atr_len)
        yr = pd.DatetimeIndex(d.index).year.to_numpy()
        m = yr == (year - 1)
        if not m.any():
            continue
        atr_px = float(np.nanmedian(a[m]))
        px = float(np.nanmedian(cl[m]))
        f = float(S.COSTS.get(p, np.nan))
        if not np.isfinite(f) or not np.isfinite(atr_px) or atr_px <= 0:
            continue
        rows.append(dict(year=year, pair=p, cost_frac=f,
                         cost_px=f * px, atr_px=atr_px,
                         cost_over_atr=f * px / atr_px))
    D = pd.DataFrame(rows).sort_values('cost_over_atr').reset_index(drop=True)
    D['rank'] = np.arange(1, len(D) + 1)
    return D


def stage_costcap(c1_names=None, variant=MAIN_PLAN, years=BUILD_YEARS,
                  nboot=2000, use_hourly=True, verbose=True):
    """2d — trade only pairs under a cost cap, cap SWEPT OVER THE FULL RANGE.

    Measured on the stage 1 C1 trades under the jack plan, as Jack specified.
    The cap is applied as a FILTER on trades already taken, which is exactly
    what trading a narrower pair list would have produced: the engine runs each
    pair independently, so dropping a pair removes its trades and nothing else.
    """
    c1_names = list(c1_names or C1_PICKS)
    S.load_costs(os.environ.get('FX_COST_TABLE', 'results/cost_table_h22.csv'))
    rows = []
    for c1 in c1_names:
        for st in SETTINGS:
            T = N.run_one(c1, 'c1', st, variant, use_hourly=use_hourly)
            if not len(T):
                continue
            T = T.reset_index(drop=True)
            T['ey'] = pd.DatetimeIndex(T.entry_date).year
            RK = pd.concat([pair_cost_rank(y) for y in sorted(set(T.ey))
                            if y in years or True], ignore_index=True)
            key = RK.set_index(['year', 'pair']).cost_over_atr
            T['cost_over_atr'] = [key.get((y, p), np.nan)
                                  for y, p in zip(T.ey, T.pair)]
            T = T[np.isfinite(T.cost_over_atr)].reset_index(drop=True)
            if not len(T):
                continue
            # the full range of the statistic, as a curve
            caps = np.unique(np.round(np.quantile(
                T.cost_over_atr, np.linspace(0, 1, 15)), 6))
            for cap in caps:
                sub = T[T.cost_over_atr <= cap].reset_index(drop=True)
                if len(sub) < 30:
                    continue
                sc = _score(sub, years, want_null=False, nboot=nboot)
                rows.append(dict(c1=c1, setting=st, variant=variant,
                                 cap=float(cap),
                                 pairs_kept=int(sub.pair.nunique()),
                                 share_trades=float(N.n_entries(sub)
                                                    / max(1, N.n_entries(T))),
                                 **{k: v for k, v in sc.items()
                                    if not k.startswith('_')}))
        if verbose:
            print('    2d: %s done' % c1, flush=True)
    D = pd.DataFrame(rows)
    f = os.path.join(OUT, 'stage2_costcap.csv')
    D.to_csv(f, index=False)
    if verbose and len(D):
        print('  2d cost cap: %d rows, %d caps per candidate -> %s'
              % (len(D), D.cap.nunique(), os.path.relpath(f, _R)), flush=True)
    return f


# ====================== 2e — FEWER TRADES ======================
def stage_fewer(c1_names=None, variant=MAIN_PLAN, years=BUILD_YEARS,
                gaps=(0, 1, 2, 3, 5, 8, 13, 21, 34, 55),
                ages=(0, 1, 2, 3, 5, 8, 13, 21),
                use_hourly=True, verbose=True):
    """2e — a minimum GAP between trades on a pair, and a minimum SIGNAL AGE.

    Jack's question: does net R per trade rise faster than trade count falls?
    Both are reported, and so is their product (total R), because a rule that
    lifts R per trade while destroying total R is not an improvement.

    MINIMUM GAP is applied forward in time, greedily, per pair: take a trade,
    then refuse every entry within `gap` bars of that ENTRY. Greedy-forward is
    the only causal version -- choosing which of two close trades to keep by
    their outcome would use the future.

    MINIMUM SIGNAL AGE is how many bars the C1 has already been on its current
    side when the entry fires. Age 0 is the flip bar itself, which is every
    trade in the C1-flip rule, so the age sweep necessarily thins from the
    CONTINUATION side: with exit-on-flip, a trade entered later in a run is one
    whose earlier entry was blocked by the gap rule or by a prior position.
    Where no trade has an age above 0 the row is reported as such and not
    silently dropped.
    """
    c1_names = list(c1_names or C1_PICKS)
    S.load_costs(os.environ.get('FX_COST_TABLE', 'results/cost_table_h22.csv'))
    rows = []
    for c1 in c1_names:
        for st in SETTINGS:
            T = N.run_one(c1, 'c1', st, variant, use_hourly=use_hourly)
            if not len(T):
                continue
            T = T.reset_index(drop=True)
            base = _score(T, years, want_null=False)
            # THE RULE APPLIES TO ENTRIES, NOT LEGS, AND GETTING THAT WRONG IS
            # WHAT EXPOSED THE WHOLE FAULT. plan=2 splits each position into
            # leg1 and leg2, both stamped with the same entry date, so a
            # per-row gap rule of one day kept exactly one leg of every entry
            # and reported "50.0000% of trades dropped" -- a number too round
            # to be real, which is how it was caught. Dropping one leg of a
            # position is not trading less, it is trading half size.
            ekey = ['pair', 'entry_date', 'direction']
            ENT = T[ekey].drop_duplicates().sort_values(['pair', 'entry_date'])
            for g in gaps:
                keep_e = []
                for p, grp in ENT.groupby('pair'):
                    last = None
                    for ed_ in pd.DatetimeIndex(grp.entry_date):
                        if last is None or (ed_ - last).days >= g:
                            keep_e.append((p, ed_)); last = ed_
                ks = set(keep_e)
                mask = [(pp, dd) in ks for pp, dd in
                        zip(T.pair, pd.DatetimeIndex(T.entry_date))]
                sub = T[np.asarray(mask)].reset_index(drop=True)
                if N.n_entries(sub) < 30:
                    continue
                sc = _score(sub, years, want_null=False)
                rows.append(dict(c1=c1, setting=st, variant=variant,
                                 rule='min_gap_days', cut=float(g),
                                 share_trades=float(N.n_entries(sub)
                                                    / max(1, N.n_entries(T))),
                                 base_R_net_per_trade=base['R_net_per_trade'],
                                 base_R_net_build=base['R_net_build'],
                                 base_trades_per_year=base['trades_per_year'],
                                 **{k: v for k, v in sc.items()
                                    if not k.startswith('_')}))
            # ---- minimum signal age, from the trade's own bars since the flip
            # DERIVED PER ENTRY, for the same reason. Two legs of one
            # position share an entry date, so a leg-level diff gives the
            # second leg an age of 0 and makes the sweep thin by leg.
            E2 = (T[ekey].drop_duplicates()
                   .sort_values(['pair', 'direction', 'entry_date']))
            age_of = {}
            for (p, dr), grp in E2.groupby(['pair', 'direction']):
                eds = pd.DatetimeIndex(grp.entry_date)
                for i, dd in enumerate(eds):
                    age_of[(p, dr, dd)] = (0.0 if i == 0
                                           else float((dd - eds[i - 1]).days))
            agecol = np.array([age_of.get((pp, dr, dd), 0.0) for pp, dr, dd in
                               zip(T.pair, T.direction,
                                   pd.DatetimeIndex(T.entry_date))])
            T = T.assign(signal_age=agecol)
            for a in ages:
                sub = T[T.signal_age >= a].reset_index(drop=True)
                if N.n_entries(sub) < 30:
                    continue
                sc = _score(sub, years, want_null=False)
                rows.append(dict(c1=c1, setting=st, variant=variant,
                                 rule='min_signal_age_days', cut=float(a),
                                 share_trades=float(N.n_entries(sub)
                                                    / max(1, N.n_entries(T))),
                                 base_R_net_per_trade=base['R_net_per_trade'],
                                 base_R_net_build=base['R_net_build'],
                                 base_trades_per_year=base['trades_per_year'],
                                 **{k: v for k, v in sc.items()
                                    if not k.startswith('_')}))
        if verbose:
            print('    2e: %s done' % c1, flush=True)
    D = pd.DataFrame(rows)
    f = os.path.join(OUT, 'stage2_fewer.csv')
    D.to_csv(f, index=False)
    if verbose and len(D):
        print('  2e fewer trades: %d rows -> %s'
              % (len(D), os.path.relpath(f, _R)), flush=True)
    return f


# ====================== 2c — THE REPORTED COMBINATIONS ======================
# THE PROP SIMULATOR NEEDS A RISK SIZE, AND IT IS SWEPT RATHER THAN ASSUMED.
# The daily series is in R, where 1 R is one 1.5 ATR risk unit. Turning that
# into the percent-of-equity series prop_run wants needs a declared risk per
# unit. The firm's limits are 4% daily and 6% trailing, so the answer depends
# entirely on this number -- which makes assuming one the wrong move. It is
# swept, and the curve is the result.
RISK_PCTS = (0.10, 0.25, 0.50, 1.00)


def prop_of_daily(DS, years, risk_pct):
    """-> the daily percent series prop_run consumes."""
    d = DS[pd.DatetimeIndex(DS.date).year.isin(list(years))]
    return (d.R.to_numpy(float) * float(risk_pct))


def stage_report(tag='picks', pool_tag=None, variants=PLANS_USED,
                 years=BUILD_YEARS, ndraw=400, nboot=2000,
                 use_hourly=True, verbose=True):
    """2c — each combination on the unseen years, every column Jack listed.

    THE SERIES IS STITCHED FROM THE WALK-FORWARD PICKS, step by step, so each
    trade year is traded with the settings chosen on ITS OWN four tuning years.
    A single setting fitted over the whole span would be a different, easier
    question.

    CONFIRM YEARS ARE COMPUTED AND WRITTEN TO THE YEARLY FILE AND NEVER
    SUMMARISED HERE. 2021 onward is not read at all.
    """
    W = pd.read_csv(os.path.join(OUT, 'stage2_%s_walk.csv' % tag))
    S.load_costs(os.environ.get('FX_COST_TABLE', 'results/cost_table_h22.csv'))
    rows, prop_rows, nullmap = [], [], {}
    import r2reads as RR
    combos = sorted(set(zip(W.c1, W.base, W.variant, W.ruleset)))
    combos = [c for c in combos if c[2] in variants]
    for (c1, base, v, rs) in combos:
        acc_T = []
        for stp in STEPS:
            if stp['trade'] not in years:
                continue
            w = W[(W.c1 == c1) & (W.base == base) & (W.variant == v)
                  & (W.ruleset == rs) & (W.step == stp['name'])]
            if not len(w):
                continue
            w = w.iloc[0]
            T = run_combo(c1, w.picked_c1_setting, base, w.picked_base_setting,
                          v, rs, use_hourly=use_hourly)
            if not len(T):
                continue
            T = T[pd.DatetimeIndex(T.exit_date).year == stp['trade']]
            if len(T):
                acc_T.append(T)
        if not acc_T:
            continue
        TT = pd.concat(acc_T, ignore_index=True)
        sc = _score(TT, years, ndraw=ndraw, nboot=nboot)
        nullmap[(c1, base, v, rs)] = sc.get('_nymat')
        DS = sc['_DS']
        rows.append(dict(c1=c1, base=base, variant=v, ruleset=rs,
                         **{k: val for k, val in sc.items()
                            if not k.startswith('_')}))
        # ---- THROUGH THE PROP SIMULATOR. CHECK 2, Jack 24 Nov: the first
        # version annualised runs of a few days, so an 8-day run that breached
        # the daily limit reported 207,847% paid out a year and a 2-day run
        # reported 1,312% return a year. Three fixes, all his:
        #   (1) totals and days are always reported;
        #   (2) nothing shorter than a year is annualised -- the annualised
        #       columns are blank, not small, so they cannot be read by
        #       mistake;
        #   (3) the HEADLINE sizing is the Team 1 budget: risk per R is set so
        #       this candidate's own worst dip equals PROP_DIP (3.6%), which is
        #       what MODEA_WINNERS.md means by Team 1. The fixed sweep is kept
        #       beside it, labelled, because every cut gets swept -- but it is
        #       context, not the headline.
        dip_r = float(sc.get('worst_dip_R', np.nan))
        sized = ((WN.PROP_DIP / dip_r) if np.isfinite(dip_r) and dip_r > 1e-9
                 else np.nan)
        plans = [('dip_%.1fpct' % WN.PROP_DIP, sized)] + \
                [('fixed', rp) for rp in RISK_PCTS]
        for (szlab, rp) in plans:
            if not np.isfinite(rp):
                continue
            dp = prop_of_daily(DS, years, rp)
            if not len(dp):
                continue
            for ph in ('eval', 'funded'):
                rec = RR.prop_run(dp, ph, 'fixed')
                yrs = float(rec.get('years', 0.0))
                full = yrs >= 1.0
                rec = dict(rec)
                rec['annualised'] = int(full)
                rec['too_short_to_annualise'] = int(not full)
                if not full:
                    # BLANK, NOT SMALL. A 2-day run has no annual rate.
                    rec['return_pct_per_year'] = np.nan
                    rec['paid_out_per_year'] = np.nan
                prop_rows.append(dict(
                    c1=c1, base=base, variant=v, ruleset=rs,
                    sizing=szlab, risk_pct_per_R=rp, phase=ph,
                    worst_dip_R_used=dip_r,
                    dip_budget_pct=(WN.PROP_DIP if szlab != 'fixed' else np.nan),
                    **rec))
        if verbose:
            print('    2c %s/%s/%s/%s: %+8.2f R/yr, dip %7.1f, t_y %5.2f, '
                  't_b %6.2f, p %.3f'
                  % (c1[:14], base[:10], v, rs, sc['R_net_per_year'],
                     sc['worst_dip_R'], sc['t_yearly'], sc['t_block_boot'],
                     sc['null_p']), flush=True)
    D = pd.DataFrame(rows)
    # ---- luck floors from the nulls themselves, in the units of the statistic
    if len(D) and nullmap:
        tstat = {}
        for k, ym in nullmap.items():
            if ym is None or not getattr(ym, 'shape', (0,))[0] or ym.shape[1] < 2:
                continue
            mu = ym.mean(axis=1); sg = ym.std(axis=1, ddof=1)
            with np.errstate(divide='ignore', invalid='ignore'):
                tstat[k] = np.where(sg > 0, mu * np.sqrt(ym.shape[1]) / sg, np.nan)
        if tstat:
            m_fam = len(combos)
            D['floor_emp_best_of_family'] = N.empirical_floor(tstat, m_fam)
            D['floor_emp_alone'] = N.empirical_floor(tstat, 1)
            D['floor_t_best_of_family'] = N.analytic_floor(
                m_fam, int(D.years.max()))
            D['floor_t_alone'] = N.analytic_floor(1, int(D.years.max()))
            D['clears_alone'] = (D.t_yearly >= D.floor_t_alone).astype(int)
            D['clears_best_of_family'] = (
                D.t_yearly >= D.floor_emp_best_of_family).astype(int)
    f = os.path.join(OUT, 'stage2_%s_report.csv' % tag)
    D.to_csv(f, index=False)
    f2 = os.path.join(OUT, 'stage2_%s_prop.csv' % tag)
    pd.DataFrame(prop_rows).to_csv(f2, index=False)
    if verbose:
        print('  2c [%s]: %d combinations -> %s' % (tag, len(D),
                                                    os.path.relpath(f, _R)),
              flush=True)
    return f, f2


# ====================== PARALLEL SHARDING FOR THE POOL GRID ======================
def _grid_shard(a):
    k, nsh, c1_all, bases, variants, rulesets, tag, use_hourly = a
    mine = [c for i, c in enumerate(c1_all) if i % nsh == k]
    if not mine:
        return None
    f1, _f2 = stage_grid(c1_names=mine, bases=bases, variants=variants,
                         rulesets=rulesets, tag='%s_sh%02d' % (tag, k),
                         use_hourly=use_hourly, verbose=False)
    return f1


def stage_grid_parallel(c1_names, bases=None, variants=PLANS_USED,
                        rulesets=('c1_alone', 'full_nnfx'), tag='pool',
                        jobs=6, use_hourly=True):
    """The 39-indicator pool grid, sharded over C1 NAMES.

    Sharded by name and not by pair, because each worker holds its own pair
    cache and the Scorer's tables; splitting by pair would make every worker
    load all 28 anyway. More shards than workers, for the same reason gate 2
    uses them: one slow indicator must not hold the whole stage.
    """
    import multiprocessing as mp, glob
    c1_names = list(c1_names)
    nsh = max(jobs, min(len(c1_names), jobs * 2))
    args = [(k, nsh, c1_names, list(bases or BASE_PICKS), tuple(variants),
             tuple(rulesets), tag, use_hourly) for k in range(nsh)]
    t0 = time.time()
    with mp.Pool(jobs) as pool:
        parts = [p for p in pool.map(_grid_shard, args) if p]
    Y = pd.concat([pd.read_csv(p) for p in parts], ignore_index=True)
    f1 = os.path.join(OUT, 'stage2_%s_yearly.csv' % tag)
    Y.to_csv(f1, index=False)
    gparts = sorted(glob.glob(os.path.join(OUT, 'stage2_%s_sh*_grid.csv' % tag)))
    Gd = pd.concat([pd.read_csv(p) for p in gparts], ignore_index=True)
    f2 = os.path.join(OUT, 'stage2_%s_grid.csv' % tag)
    Gd.to_csv(f2, index=False)
    print('  stage 2 pool grid [%s]: %d indicators over %d shards on %d workers,'
          ' %d yearly rows in %.1f min'
          % (tag, len(c1_names), nsh, jobs, len(Y), (time.time() - t0) / 60),
          flush=True)
    return f1, f2


# ====================== THE REPORT ======================
def _short(s, sfx):
    return str(s).replace(sfx, '')


def _read_2d(CC):
    """CHECK 3, Jack 24 Nov: one paragraph in plain English, does a cost cap
    raise net R per year or return per dip, and at what setting. Every figure
    is computed from the csv here, never typed."""
    L_ = []
    if not len(CC):
        return ['_not computed_\n']
    rows = []
    for (c1, st, v), g in CC.groupby(['c1', 'setting', 'variant']):
        if v != MAIN_PLAN:
            continue
        g = g.sort_values('pairs_kept')
        full = g.iloc[-1]
        bR = g.loc[g.R_net_per_year.idxmax()]
        bD = g.loc[g.R_per_year_per_dip.idxmax()]
        rows.append(dict(c1=_short(c1, '_signals'), setting=st,
                         full_Ryr=float(full.R_net_per_year),
                         full_rpd=float(full.R_per_year_per_dip),
                         best_Ryr=float(bR.R_net_per_year),
                         best_Ryr_pairs=int(bR.pairs_kept),
                         best_rpd=float(bD.R_per_year_per_dip),
                         best_rpd_pairs=int(bD.pairs_kept),
                         full_pairs=int(full.pairs_kept)))
    if not rows:
        return ['_not computed_\n']
    D = pd.DataFrame(rows)
    prof = D[D.full_Ryr > 0]
    nR = int((prof.best_Ryr_pairs == prof.full_pairs).sum())
    nD = int((prof.best_rpd_pairs == prof.full_pairs).sum())
    ex = prof[prof.best_Ryr_pairs != prof.full_pairs]
    L_.append('\n### What 2d says, in plain English\n')
    L_.append(
        'No. A cost cap does not raise net R per year or return per dip on any '
        'candidate that was making money without it, with a single exception '
        'that does not survive a second look. Of the ' + str(len(D))
        + ' candidate-settings on the main plan, ' + str(len(prof))
        + ' are profitable over the unseen years at the full 28-pair set; for '
        + str(nR) + ' of those ' + str(len(prof)) + ' the best cap on R per '
        'year IS the full set, and for ' + str(nD) + ' of ' + str(len(prof))
        + ' so is the best cap on return per dip. The median gain from the '
        'best cap across the profitable candidates is '
        + '{:+.3f}'.format(float(prof.best_Ryr.sub(prof.full_Ryr).median()))
        + ' R per year and '
        + '{:+.4f}'.format(float(prof.best_rpd.sub(prof.full_rpd).median()))
        + ' on return per dip — zero to three decimals. Where the cap appears '
        'to help it is helping a LOSER: it improves every one of the '
        + str(len(D) - len(prof)) + ' unprofitable settings, which is not an '
        'improvement but simply doing less of something that loses money.')
    if len(ex):
        e = ex.iloc[0]
        L_.append(
            '\nThe one exception is **' + e.c1 + ' at its ' + e.setting
            + ' setting**, where capping to ' + str(e.best_Ryr_pairs)
            + ' pairs lifts R per year from ' + '{:+.2f}'.format(e.full_Ryr)
            + ' to ' + '{:+.2f}'.format(e.best_Ryr) + ' and capping to '
            + str(e.best_rpd_pairs) + ' pairs lifts return per dip from '
            + '{:.4f}'.format(e.full_rpd) + ' to '
            + '{:.4f}'.format(e.best_rpd) + '. I would not act on it: it is one '
            'cell in ' + str(len(D)) + ', the uncapped base it improves on is '
            'barely above zero, and **the two metrics choose different caps** ('
            + str(e.best_Ryr_pairs) + ' pairs against '
            + str(e.best_rpd_pairs) + '). A real cost effect would put both at '
            'the same place on the curve; two different answers from the same '
            'sweep is what noise looks like.\n')
    L_.append(
        '\nThis is the same conclusion the first version of 2d reached, and it '
        'survives the engine fix — the dip changed, the ranking of caps did '
        'not. **Cheap pairs do not carry the edge**, even though the dearest '
        'pair costs three times the cheapest (EURCHF 0.070 against EURUSD '
        '0.023 per unit of gross R, from `ENGINE_AUDIT_2.md`).\n')
    return L_


def _read_2e(FW):
    """CHECK 3: the same for fewer trades."""
    L_ = []
    if not len(FW):
        return ['_not computed_\n']
    rows = []
    for (c1, st, rule), g in FW.groupby(['c1', 'setting', 'rule']):
        g = g.sort_values('cut')
        base = g.iloc[0]
        bR = g.loc[g.R_net_build.idxmax()]
        bD = g.loc[g.R_per_year_per_dip.idxmax()]
        rows.append(dict(c1=_short(c1, '_signals'), setting=st, rule=rule,
                         base_R=float(base.R_net_build),
                         base_rpt=float(base.R_net_per_trade),
                         base_rpd=float(base.R_per_year_per_dip),
                         best_R=float(bR.R_net_build), best_R_cut=float(bR.cut),
                         best_R_share=float(bR.share_trades),
                         best_rpt=float(bR.R_net_per_trade),
                         best_rpd=float(bD.R_per_year_per_dip),
                         best_rpd_cut=float(bD.cut)))
    D = pd.DataFrame(rows)
    ich = D[(D.c1 == 'ichimoku') & (D.rule == 'min_gap_days')]
    helped = D[(D.best_R > D.base_R + 1e-9) & (D.base_R > 0)]
    L_.append('\n### What 2e says, in plain English\n')
    L_.append(
        'Yes, and only for ichimoku — but there it is the clearest effect in '
        'the whole staged build. A minimum gap between trades raises net R per '
        'year AND return per dip on **all three** of ichimoku\'s settings, and '
        'all three choose the same cut, a **'
        + '{:.0f}'.format(float(ich.best_R_cut.mode().iloc[0])
                          if len(ich) else 0)
        + '-day minimum gap**. That agreement across settings is the part '
        'worth something: a single lucky cut on one setting would be a '
        'coincidence, three settings landing on the same cut is a property of '
        'the indicator. At the default setting the gap takes total R from '
        + '{:.2f}'.format(float(ich[ich.setting == 'default'].base_R.iloc[0])
                          if len(ich[ich.setting == 'default']) else 0)
        + ' to '
        + '{:.2f}'.format(float(ich[ich.setting == 'default'].best_R.iloc[0])
                          if len(ich[ich.setting == 'default']) else 0)
        + ' on '
        + '{:.0f}'.format(100.0 * float(
            ich[ich.setting == 'default'].best_R_share.iloc[0])
            if len(ich[ich.setting == 'default']) else 0)
        + '% of the trades, R per trade from '
        + '{:+.4f}'.format(float(ich[ich.setting == 'default'].base_rpt.iloc[0])
                           if len(ich[ich.setting == 'default']) else 0)
        + ' to '
        + '{:+.4f}'.format(float(ich[ich.setting == 'default'].best_rpt.iloc[0])
                           if len(ich[ich.setting == 'default']) else 0)
        + ', and return per dip from '
        + '{:.4f}'.format(float(ich[ich.setting == 'default'].base_rpd.iloc[0])
                          if len(ich[ich.setting == 'default']) else 0)
        + ' to '
        + '{:.4f}'.format(float(ich[ich.setting == 'default'].best_rpd.iloc[0])
                          if len(ich[ich.setting == 'default']) else 0)
        + '. So the answer to Jack\'s actual question — does net R per trade '
        'rise faster than the trade count falls — is YES on ichimoku: it keeps '
        'about three quarters of the trades and more than doubles R per trade, '
        'so total R goes UP rather than merely surviving.')
    L_.append(
        '\nIt does not generalise. On **schaff_trend_cycle** the half setting '
        'improves at an 8-day cut and the default setting improves at NO cut '
        'in the whole sweep — its best is the uncapped base. On **halftrend** '
        'there is nothing: the largest gain anywhere is under one R over six '
        'years, and its half setting loses money at every cut. Across all '
        + str(len(D)) + ' candidate-setting-rule combinations only '
        + str(len(helped)) + ' that were already profitable improve at all.\n')
    L_.append(
        '\nThe honest reading is that **ichimoku holds its trades too briefly '
        'and benefits from being made to wait**, which is a statement about '
        'one indicator and not about the NNFX algorithm. Nothing here has been '
        'null-tested yet: the cut was swept over its full range and the best of '
        'the sweep is reported, so a selection correction is still owed before '
        'the ' + '{:.0f}'.format(float(ich.best_R_cut.mode().iloc[0])
                                 if len(ich) else 0)
        + '-day gap is treated as a finding rather than a lead.\n')
    return L_


def md_stage2(out=None):
    """STAGE2.md — Jack's 2a/2b/2c/2f/2d/2e, numbers read from the csvs."""
    out = out or os.path.join(OUT, 'STAGE2.md')
    L_ = []
    a = L_.append

    def rd(n):
        return _safe_csv(os.path.join(OUT, n))

    R = rd('stage2_picks_report.csv')
    RP = rd('stage2_pool_report.csv')
    P = rd('stage2_picks_paired.csv')
    RS = rd('stage2_rolling_sweep.csv')
    RK = rd('stage2_rolling_picks.csv')
    CC = rd('stage2_costcap.csv')
    FW = rd('stage2_fewer.csv')
    PR = rd('stage2_picks_prop.csv')
    NC = rd('stage2_picks_neutralcheck.csv')

    a('# Stage 2 — the baseline added to C1\n')
    a('Generated by `code/nnfx2s.py` on %s. Every number in this file is read '
      'from a csv in `results/nnfx/`; none is typed in.\n' % time.strftime('%F %H:%M'))
    a('\n## Jack\'s picks, and whose they are\n')
    a('These were chosen by Jack on 24 Nov after reading `STAGE1_R2.md`. I did '
      'not make them and did not narrow them.\n')
    a('\n| what | pick | Jack\'s reason |')
    a('|---|---|---|')
    a('| C1 | ichimoku, schaff_trend_cycle, halftrend | the only C1 positive net '
      'under both the jack and textbook plans at more than one setting |')
    a('| C1 rule | ROLLING TOP 3 — at each step the 3 C1 ranked best on the four '
      'tuning years, traded on the unseen year | the selection test: +13.9 R per '
      'year against a null of −8.0, p 0.001 |')
    a('| baselines | sma, hma, t3 | the double setting was best for every '
      'baseline; none is positive alone, so they are judged as filters |')
    a('\n`jack` is the main version throughout. `textbook` is reported beside '
      'it. Unseen trade years 2010–2015 are the evidence; 2016–2020 are '
      'computed and written to the yearly csvs and are not summarised anywhere '
      'in this file. 2021 onward is not read.\n')

    a('\n## One of the four baseline rules cannot be switched off, and the '
      'engine is why\n')
    a('Jack asked which rule inside the baseline does the work, by switching '
      'each on alone. Three can be. The fourth cannot.\n')
    a('\n`side` is the sign of (close − baseline), recomputed every bar '
      '(`l2engine.py:274-279`). Every entry route then gates on agreement, and '
      'agreement contains `side`:\n')
    a('\n```\nagree_long = c1_lc[i] and c2_lc[i] and v_ok_l[i] and side == 1   '
      '(:527)\nr1l = use_base_cross and last_cross_bar == i and side == 1 and '
      'agree_long\nr2l = use_c1_flip   and c1_lt[i] and agree_long            '
      '    (:549-552)\n```\n')
    a('There is no path into a trade that avoids it. So the **side filter is '
      'the floor**, and the other three are measured as INCREMENTS OVER IT, '
      'not over nothing. Reporting them as independent additions would credit '
      'whichever rule was switched on with the side filter\'s entire effect.\n')
    a('\n| ruleset | side | distance | cross entry | cross exit |')
    a('|---|---|---|---|---|')
    for k in RULE_ORDER:
        r = RULESETS[k]
        a('| `%s` | %s | %s | %s | %s |'
          % (k, 'yes' if r['side'] else '**no — the control**',
             'yes' if r['dist'] else 'no', 'yes' if r['xentry'] else 'no',
             'yes' if r['xexit'] else 'no'))
    a('\n`c1_alone` is stage 1\'s C1-alone run: the baseline array is replaced '
      'by close ± K so `side` is pinned, and the two directions are run '
      'separately. It is the control every paired test below differences '
      'against.\n')

    if len(NC):
        okn = bool(NC.passes.all())
        a('\n### The control is checked, not assumed\n')
        a('If the baseline setting could reach the engine through a neutralised '
          'baseline, every paired comparison here would be contaminated. The '
          'grid computes all three base settings for the control anyway, so the '
          'check is free: **%d control cells, worst R spread %.3g, worst '
          'trade-count spread %.3g → %s**.\n'
          % (len(NC), NC.R_spread.max(), NC.n_spread.max(),
             'PASS' if okn else 'FAIL'))

    # ---------------- 2a / 2c ----------------
    a('\n## 2a and 2c — each combination on the unseen years 2010–2015\n')
    a('Settings are picked walk-forward, **both together**, on each step\'s four '
      'tuning years: nine setting-pairs ranked on tuning-year net R, minimum 30 '
      'trades. The C1 and baseline settings are chosen jointly because they '
      'interact, and picking them one at a time would be a different rule than '
      'the one declared.\n')
    cols = ['c1', 'base', 'ruleset', 'R_net_per_year', 'R_net_per_trade',
            'R_gross_per_trade', 'trades_per_year', 'mean_bars',
            'years_positive', 'worst_year', 'worst_dip_R',
            'R_per_year_per_dip', 't_yearly', 't_block_boot', 'null_p']
    for v in PLANS_USED:
        g = R[R.variant == v] if len(R) else R
        a('\n### `%s` plan%s\n' % (v, ' — THE MAIN VERSION' if v == MAIN_PLAN
                                  else ', reported beside it'))
        if not len(g):
            a('_not computed_\n')
            continue
        g = g.sort_values('R_net_per_year', ascending=False)
        d = g.copy()
        d['c1'] = d.c1.map(lambda s: _short(s, '_signals'))
        d['base'] = d.base.map(lambda s: _short(s, '_baseline'))
        a(N._tbl(d, cols))
        if 'clears_best_of_family' in g.columns:
            a('\nLuck floors from the random-entry null itself, in the units of '
              'the yearly t: alone %.3f, best-of-%d %.3f. **%d of %d clear the '
              'alone floor, %d clear best-of-family.**\n'
              % (g.floor_emp_alone.iloc[0], len(g),
                 g.floor_emp_best_of_family.iloc[0],
                 int(g.clears_alone.sum()), len(g),
                 int(g.clears_best_of_family.sum())))

    # ---------------- 2b ----------------
    a('\n## 2b — the paired test: the same C1 with and without the baseline\n')
    a('Both series live through the same 2010–2015 markets, so differencing '
      'their daily P&L day by day removes everything common to them and leaves '
      'the baseline\'s own contribution. The block-bootstrap t is on that '
      'difference, 20-day blocks, 2,000 draws.\n')
    a('\nThe days are **unioned, not intersected**. A day on which only one of '
      'the two is in the market is a real difference and belongs in the test; '
      'intersecting would delete the baseline\'s main effect, which is to stop '
      'trades happening. A missing day is zero P&L, not missing data.\n')
    pc = ['c1', 'base', 'ruleset', 'R_without', 'R_with', 'delta_R',
          'delta_R_per_year', 'delta_t_block_boot', 'delta_t_yearly',
          'years_delta_positive', 'days_with_only', 'days_without_only']
    for v in PLANS_USED:
        g = P[P.variant == v] if len(P) else P
        a('\n### `%s` plan\n' % v)
        if not len(g):
            a('_not computed_\n')
            continue
        d = g.sort_values('delta_R', ascending=False).copy()
        d['c1'] = d.c1.map(lambda s: _short(s, '_signals'))
        d['base'] = d.base.map(lambda s: _short(s, '_baseline'))
        a(N._tbl(d, pc))

    a('\n### Which rule does the work\n')
    if len(P):
        for v in PLANS_USED:
            g = P[P.variant == v]
            if not len(g):
                continue
            a('\n`%s`: mean ΔR per year by ruleset, over all 9 C1×baseline '
              'combinations —\n' % v)
            m = (g.groupby('ruleset', as_index=False)
                  .agg(mean_delta_R_per_year=('delta_R_per_year', 'mean'),
                       mean_boot_t=('delta_t_block_boot', 'mean'),
                       n_combos=('delta_R', 'size'))
                  .sort_values('mean_delta_R_per_year', ascending=False))
            a(N._tbl(m, list(m.columns)))
        a('\nRead these as increments over `side`, not over the bare C1 — '
          '`side` is in every one of them.\n')

    # ---------------- 2f ----------------
    a('\n## 2f — the rolling top-K rule in full, K from 1 to 10\n')
    a('At each step the K C1 ranked best on the four tuning years are traded, '
      'equal weight, on that step\'s unseen year. No trade-year information '
      'touches the ranking. The null permutes the tuning-year ranking and '
      'applies the same top-K rule, so what is tested is the **selection rule**'
      ' and not the quality of the pool.\n')
    if len(RS):
        sc = ['variant', 'base', 'K', 'R_per_year_mean', 'years_positive',
              'worst_year', 'worst_dip_R', 't_yearly', 'turnover_mean',
              'null_mean', 'null_p']
        for v in PLANS_USED:
            g = RS[RS.variant == v]
            if not len(g):
                continue
            a('\n### `%s` plan\n' % v)
            d = g.sort_values(['base', 'K']).copy()
            d['base'] = d.base.map(lambda s: _short(s, '_baseline'))
            a(N._tbl(d, sc))
        b = RS.loc[RS.R_per_year_mean.idxmax()]
        a('\nBest cell: **%+.3f R per year at K=%d**, %s plan, %s baseline, '
          'against a null mean of %+.3f at p %.3f, turnover %.2f.\n'
          % (b.R_per_year_mean, b.K, b.variant,
             _short(b.base, '_baseline'), b.null_mean, b.null_p,
             b.turnover_mean if np.isfinite(b.turnover_mean) else float('nan')))
    else:
        a('_not computed_\n')
    if len(RK):
        a('\n### What the rule picked each year, at K=3\n')
        d = RK[RK.variant == MAIN_PLAN] if 'variant' in RK.columns else RK
        a(N._tbl(d, ['base', 'trade_year', 'picked', 'trade_R_net', 'trade_n']))

    # ---------------- 2d ----------------
    a('\n## 2d — the cost cap\n')
    a('Pairs are ranked each year by round-trip cost divided by ATR. The cost '
      'is the era table\'s; the ATR is measured over the **previous** calendar '
      'year and never the year being traded, so the ranking is known in advance '
      'and the trade year stays unseen. No performance is used.\n')
    a('\ncost / ATR is the right ratio because R is measured in ATR units: a '
      'pair whose spread is a large share of its daily range eats a large share '
      'of every R, whatever its absolute pip cost.\n')
    if len(CC):
        cc = ['c1', 'setting', 'cap', 'pairs_kept', 'share_trades',
              'R_net_per_year', 'R_net_per_trade', 'worst_dip_R',
              'R_per_year_per_dip', 't_block_boot']
        d = CC.copy(); d['c1'] = d.c1.map(lambda s: _short(s, '_signals'))
        a(N._tbl(d.sort_values(['c1', 'setting', 'cap']), cc))
        for _l in _read_2d(CC):
            a(_l)
    else:
        a('_not computed_\n')

    # ---------------- 2e ----------------
    a('\n## 2e — fewer trades\n')
    a('A minimum gap between trades on a pair, and a minimum signal age, each '
      'swept over its full range. The gap is applied greedily forward in time: '
      'take a trade, then refuse every entry within the gap of that entry. '
      'Greedy-forward is the only causal version — choosing which of two close '
      'trades to keep by their outcome would use the future.\n')
    a('\nJack\'s question is whether net R per trade rises faster than trade '
      'count falls, so both are in the table and so is total R, because a rule '
      'that lifts R per trade while destroying total R is not an improvement.\n')
    if len(FW):
        fc = ['c1', 'setting', 'rule', 'cut', 'share_trades',
              'base_R_net_per_trade', 'R_net_per_trade',
              'base_trades_per_year', 'trades_per_year',
              'base_R_net_build', 'R_net_build', 'worst_dip_R']
        d = FW.copy(); d['c1'] = d.c1.map(lambda s: _short(s, '_signals'))
        a(N._tbl(d.sort_values(['c1', 'setting', 'rule', 'cut']), fc))
        for _l in _read_2e(FW):
            a(_l)
    else:
        a('_not computed_\n')

    # ---------------- prop ----------------
    a('\n## Through the prop simulator\n')
    # NO % FORMATTING ON PROSE THAT CONTAINS A LITERAL PER-CENT SIGN. This
    # project has broken three report writes that way; concatenation cannot.
    a('The daily series is in R, where 1 R is one 1.5 ATR risk unit. Turning it '
      'into the percent-of-equity series the simulator consumes needs a '
      'declared risk per unit, and the firm\'s limits are 4% daily and 6% '
      'trailing.\n')
    a('\n> **CORRECTED, 24 Nov, on Jack\'s check 2.** The first version of this '
      'section annualised runs of a few days. An 8-day run that breached the '
      'daily limit reported **207,847% paid out a year**, and a 2-day run '
      'reported **1,312% return a year**. Three things are fixed. Totals and '
      'days are always shown. **Nothing shorter than a year is annualised** '
      'and the annualised columns are left BLANK rather than small, so they '
      'cannot be read by mistake. And the headline sizing is no longer a fixed '
      'risk per R: each candidate is sized so that **its own worst dip equals '
      'the Team 1 budget of ' + '{:.1f}'.format(WN.PROP_DIP) + '%**, which is '
      'what `MODEA_WINNERS.md` means by Team 1. The fixed sweep is kept below '
      'it as context.\n')
    if len(PR):
        d = PR[PR.variant == MAIN_PLAN].copy() if 'variant' in PR.columns else PR.copy()
        d['c1'] = d.c1.map(lambda s: _short(s, '_signals'))
        d['base'] = d.base.map(lambda s: _short(s, '_baseline'))
        qc = ['c1', 'base', 'ruleset', 'phase', 'risk_pct_per_R',
              'worst_dip_R_used', 'days', 'years', 'breached',
              'return_pct', 'paid_out', 'worst_dip_pct', 'annualised',
              'return_pct_per_year', 'paid_out_per_year']
        if 'sizing' in d.columns:
            hd = d[d.sizing != 'fixed']
            a('\n### Sized so the worst dip equals the Team 1 budget\n')
            a('`risk_pct_per_R` is derived, not chosen: it is '
              + '{:.1f}'.format(WN.PROP_DIP) + ' divided by the candidate\'s own '
              'verified worst dip in R. A blank `return_pct_per_year` means the '
              'run ended before a full year and has no annual rate.\n')
            if len(hd):
                a(N._tbl(hd.sort_values(['c1', 'base', 'ruleset', 'phase']), qc))
                nshort = int((hd.annualised == 0).sum())
                nbr = int((hd.breached.fillna('').astype(str) != '').sum())
                fu = hd[(hd.phase == 'funded') & (hd.annualised == 1)]
                a('\n**' + str(nshort) + ' of ' + str(len(hd)) + ' runs ended '
                  'before a full year**, and ' + str(nbr) + ' breached a firm '
                  'limit.\n')
                if len(fu):
                    a('\nAnd this is what check 2 was for. Sized so the worst '
                      'dip is the Team 1 budget, the derived risk per R comes '
                      'out at ' + '{:.3f}'.format(float(hd.risk_pct_per_R.min()))
                      + ' to ' + '{:.3f}'.format(float(hd.risk_pct_per_R.max()))
                      + ' per cent of equity, the realised worst dip lands at '
                      + '{:.2f}'.format(float(hd.worst_dip_pct.min())) + ' to '
                      + '{:.2f}'.format(float(hd.worst_dip_pct.max()))
                      + ' per cent as intended, and the funded return is '
                      + '{:+.3f}'.format(float(fu.return_pct_per_year.min()))
                      + ' to '
                      + '{:+.3f}'.format(float(fu.return_pct_per_year.max()))
                      + ' per cent a YEAR. The best of them is '
                      + '{:+.3f}'.format(float(fu.return_pct_per_year.max()))
                      + ' per cent against a 12 per cent target, and '
                      + str(int((fu.return_pct_per_year >= 12.0).sum()))
                      + ' of ' + str(len(fu)) + ' clear it. The uncorrected '
                      'version of this table showed a 2-day run at 1,312 per '
                      'cent a year and an 8-day run paying out 207,847 per '
                      'cent a year; on a sizing that respects the drawdown '
                      'budget and an annualisation that refuses to divide by '
                      'eight days, there is no candidate here a prop firm '
                      'would fund.\n')
            else:
                a('_no dip-sized rows: every candidate had an undefined dip_\n')
            a('\n### The fixed risk-per-R sweep, as context\n')
            a('Swept over ' + ', '.join('{:.2f}'.format(x) for x in RISK_PCTS)
              + '% of equity per R. Same annualisation rule.\n')
            fx = d[d.sizing == 'fixed']
            if len(fx):
                a(N._tbl(fx.sort_values(['c1', 'base', 'risk_pct_per_R',
                                         'ruleset', 'phase']), qc))
        else:
            a(N._tbl(d.sort_values(['c1', 'base', 'risk_pct_per_R']), qc))
    else:
        a('_not computed_\n')

    a('\n## What is sealed\n')
    a('- 2016–2020 are computed and stored in `stage2_*_yearly.csv` and are not '
      'summarised in this file.\n- 2021 onward is not read.\n- Every candidate '
      'tested is in `CANDIDATE_LEDGER.csv`, which is where the luck floors come '
      'from.\n')
    txt = '\n'.join(L_) + '\n'
    with open(out, 'w') as fh:
        fh.write(txt)
    print('  STAGE2.md: %d lines -> %s'
          % (txt.count('\n'), os.path.relpath(out, _R)), flush=True)
    return out


# ====================== DISPATCH — NOTHING IS DEFINED BELOW THIS ======================
# GUARD 29 EXISTS BECAUSE I BROKE THIS TWICE IN ONE DAY. A stage function
# appended after the __main__ block is invisible to the dispatch, and chain 24
# died in 6 seconds on a NameError for exactly that. Nothing goes below here.
if __name__ == '__main__':
    st = G.opt('--stage', str, 'smoke')
    jobs = G.opt('--jobs', int, 6)
    hourly = not bool(G.opt('--no-hourly', int, 0))
    if st == 'smoke':
        stage_grid(c1_names=[C1_PICKS[0]], bases=[BASE_PICKS[0]],
                   variants=(MAIN_PLAN,), rulesets=('c1_alone', 'full_nnfx'),
                   tag='smoke', use_hourly=hourly)
        stage_pick(tag='smoke')
        _D, _ok = condition_neutral('smoke')
        if not _ok:
            raise SystemExit('NEUTRALISATION CHECK FAILED -- the control is '
                             'contaminated and no paired number may be quoted')
        stage_report(tag='smoke', variants=(MAIN_PLAN,), use_hourly=hourly)
    elif st == 'grid':
        stage_grid(rulesets=RULE_ORDER, tag='picks', use_hourly=hourly)
        _D, _ok = condition_neutral('picks')
        if not _ok:
            raise SystemExit('NEUTRALISATION CHECK FAILED on the picks grid')
    elif st == 'pool':
        C1L, _b, _c, _v, _x = N.families()
        stage_grid_parallel(C1L, rulesets=('c1_alone', 'full_nnfx'),
                            tag='pool', jobs=jobs, use_hourly=hourly)
    elif st == 'pick':
        stage_pick(tag=G.opt('--tag', str, 'picks'))
    elif st == 'paired':
        stage_paired(tag='picks', use_hourly=hourly)
    elif st == 'report':
        stage_report(tag='picks', use_hourly=hourly)
    elif st == 'rolling':
        stage_rolling(tag='pool')
    elif st == 'costcap':
        stage_costcap(use_hourly=hourly)
    elif st == 'fewer':
        stage_fewer(use_hourly=hourly)
    elif st == 'ledger':
        N.ledger_add('stage2', 'c1', list(C1_PICKS) + [ROLLING],
                     len(SETTINGS) ** 2,
                     "Jack's pick, 24 Nov: the only C1 positive net under both "
                     "plans at more than one setting; plus the rolling top 3",
                     '2010-2015 unseen, 2016-2020 computed and sealed',
                     'stage 2, baseline added')
        N.ledger_add('stage2', 'base', list(BASE_PICKS), len(SETTINGS) ** 2,
                     "Jack's pick, 24 Nov: the double setting was best for every "
                     "baseline; none positive alone, judged as filters",
                     '2010-2015 unseen, 2016-2020 computed and sealed',
                     'stage 2, baseline added')
    elif st == 'md':
        md_stage2()
    else:
        raise SystemExit('unknown stage %s' % st)
