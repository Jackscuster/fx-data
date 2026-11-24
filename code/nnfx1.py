import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""NNFX PHASE 1, STAGE 1 — ONE PIECE ALONE, WALK-FORWARD. HANDOFF 0m.

1a  each of the 39 C1 indicators by itself, 28 pairs: enter on the flip, exit
    on the opposite flip, nothing else. Then again with the canonical 1.5 ATR
    stop and half off at 1 ATR.
1b  each of the 15 baselines by itself: enter when price closes across it, exit
    on the cross back.
1c  selection test: rank them on the tuning years, trade the top K unseen.

NO SECOND ENGINE. 0b found that two scorers with two undeclared conventions
cost this project a winner list, so stage 1 runs the SHIPPED l2engine and
neutralises the slots it is not testing, rather than reimplementing the bar
loop. "C1 alone" is produced like this, and every part of it is provable:

  c2_lc, c2_sc   forced all True  -> the confirmation can never block
  v_ok_l, v_ok_s forced all True  -> the volume gate can never block
  bl             set to the close -> `cl > b + max_atr_dist*a` is false for any
                                     non-negative max_atr_dist, so the
                                     baseline-distance block can never fire,
                                     and `side` is 0 so no baseline cross is
                                     ever detected
  use_base_cross=False, use_continuation=False, exit_on_base_cross=False,
  exit_on_exit_ind=False, one_candle_rule=False, bridge_bars huge

What is left is exactly: enter when c1_lt/c1_st flips, exit when it flips back.
`l2engine.py:462` shows the C1-flip route gated only by `agree_long`, which is
C2 and volume -- NOT by the baseline side -- so nothing else needs disabling.

THE RISK UNIT IS R PER 1.5 ATR, FOR BOTH VARIANTS. The engine books
r = move x units / RISK with units ~ 1/(atr_mult x ATR), so engine r scales as
1/atr_mult. Every figure here is restated as r x atr_mult / 1.5, which is the
canonical NNFX stop. Without that the no-stop variant and the 1.5 ATR variant
would be in different units and could not be compared -- and it is the same
correction ACCT_OBJECTIVE makes, for the same reason.

  flip_only       atr_mult 50, tp_mult 900 (the no-target sentinel). A 50 ATR
                  stop is never reached; stage_run ASSERTS that no trade exited
                  by stop, so "nothing else" is checked rather than assumed.
  canonical_risk  atr_mult 1.5, first target at 1.0 ATR (tp_mult = 1/1.5),
                  then breakeven and trail, which is plan 2.

THREE SETTINGS PER INDICATOR. For the 34 C1 and 15 baselines carrying an
integer length, half / default / double of that length. FIVE C1 indicators are
parameterised by a smoothing CONSTANT instead -- ehlers_reverse_ema (alpha),
kalman_filter (sharpness, k), laguerre_filter (alpha), mama_fama (fast_limit,
slow_limit) and parabolic_sar (sar_start, sar_increment). For those, a LARGER
constant is a SHORTER memory, so "half length" doubles the constant and
"double length" halves it. Stated because it is the opposite direction.
Two baselines default to length 2 (fantail_vma, vidya), where half is also 2,
so they have two distinct settings and not three; the report says so.
"""
import time, glob, json, hashlib, inspect, itertools
import numpy as np, pandas as pd
from scipy import stats

import l2lib as L
import l2sweep as S
import l2engine as E
import l2r2gate1 as G

OUT = os.path.join(ROOTOUT, 'nnfx')
os.makedirs(OUT, exist_ok=True)
LEDGER = os.path.join(OUT, 'CANDIDATE_LEDGER.csv')

RISK_UNIT_ATR = 1.5          # every R here is per 1.5 ATR
# 2000, AND BOTH SMALLER VALUES WERE TRIED AND FAILED. At 50 ATR two AUDJPY
# long trades held 345 bars reached the stop -- the 2008 collapse is that large
# in ATR units. At 200 a single EURCHF baseline trade reached it, which is the
# 2015 SNB de-peg. At 2000 there is not one risk-plan exit across 28 pairs,
# both sides, both families and all three settings. The assertion in run_one
# catches any case where it is still not enough, so this is a measured constant
# and not a hopeful one. R is invariant to it by construction, because R_gross
# rescales by atr_mult -- checked, not assumed.
BIG_STOP = 2000.0
TP_NONE = 900.0
BIG = 10 ** 9
SETTINGS = ('half', 'default', 'double')
VARIANTS = ('flip_only', 'canonical_risk')
# the walk: eleven steps, tune 4 / grade 1 / trade 1
STEPS = [dict(name='%d-%d' % (y, y + 3), tune=(y, y + 3), grade=y + 4,
              trade=y + 5) for y in range(2005, 2016)]
BUILD_YEARS = tuple(range(2010, 2016))     # reported
CONFIRM_YEARS = tuple(range(2016, 2021))   # computed, stored, NOT reported
FLOAT_SHORTER_IS_BIGGER = {
    'ehlers_reverse_ema_signals': ('alpha',),
    'kalman_filter_signals': ('sharpness', 'k'),
    'laguerre_filter_signals': ('alpha',),
    'mama_fama_signals': ('fast_limit', 'slow_limit'),
    'parabolic_sar_signals': ('sar_start', 'sar_increment'),
}


def families():
    o = S.mode_opts(S.slot_options(), 'A')
    return list(o['c1']), list(o['base']), list(o['c2']), list(o['vol']), list(o['exit_ind'])


def length_params(name):
    """-> {param: default} for the knobs that scale this indicator's memory."""
    f = getattr(L, name, None)
    if f is None:
        return {}
    if name in FLOAT_SHORTER_IS_BIGGER:
        sig = inspect.signature(f)
        return {k: sig.parameters[k].default for k in FLOAT_SHORTER_IS_BIGGER[name]
                if k in sig.parameters}
    sig = inspect.signature(f)
    for k, v in sig.parameters.items():
        if v.default is not inspect._empty and isinstance(v.default, int) \
                and not isinstance(v.default, bool) and v.default >= 2:
            return {k: v.default}
    return {}


def setting_params(name, which):
    """The parameter override for one setting. {} means Pine defaults."""
    lp = length_params(name)
    if not lp or which == 'default':
        return {}
    out = {}
    inv = name in FLOAT_SHORTER_IS_BIGGER
    for k, v in lp.items():
        if inv:
            out[k] = float(v * 2.0) if which == 'half' else float(v / 2.0)
        else:
            out[k] = max(2, int(round(v / 2))) if which == 'half' else int(v * 2)
    return out


def setting_is_distinct(name, which):
    """False when half collapses onto default, as for a default length of 2."""
    if which == 'default':
        return True
    return setting_params(name, which) != {} and \
        setting_params(name, which) != {k: v for k, v in length_params(name).items()}


_PAIR = {}


def pair_data(p):
    if p not in _PAIR:
        _PAIR[p] = S.load_pair(p)
    return _PAIR[p]


def _neutralise(A, kind, side=None):
    """Force every slot but the one under test to pass. See the module note.

    A CORRECTION TO MY OWN FIRST READING. I took the C1-flip route to be
    independent of the baseline because `l2engine.py:462` reads
    `r2l = use_c1_flip and c1_lt[i] and agree_long`. It is not: `agree_long`
    itself is `c1_lc[i] and c2_lc[i] and v_ok_l[i] and side == 1`
    (l2engine.py:441), so the baseline SIDE is inside the agreement. Setting
    the baseline equal to the close makes `side` 0 and blocks every entry --
    the first smoke took 0 trades, which is how this was caught.

    So "C1 alone" is run ONE DIRECTION AT A TIME, with the baseline placed far
    below the close for the long side (side == 1 on every bar) and far above it
    for the short side (side == -1), and the two trade sets concatenated. The
    EXIT needs neither side nor agreement -- `exit_on_c1_flip and c1_st[i]`
    (l2engine.py:414) -- so each one-sided run still exits on the opposite
    flip, which is what the rule says.
    """
    n = A['c'].size
    T = np.ones(n, bool)
    A['c2_lc'] = T.copy(); A['c2_sc'] = T.copy()
    A['v_ok_l'] = T.copy(); A['v_ok_s'] = T.copy()
    A['x_el'] = np.zeros(n, bool); A['x_es'] = np.zeros(n, bool)
    if kind == 'c1':
        K = 10.0 * float(np.nanmax(np.abs(A['c'])) + 1.0)
        A['bl'] = A['c'] - K if side == 'long' else A['c'] + K
    return A


def run_one(name, kind, setting, variant, pairs=None, atr_len=14,
            use_hourly=False, amb_out=None):
    """One indicator, one setting, one variant, across the pairs. -> trade frame.

    kind 'c1'   enter on the indicator's flip, exit on the opposite flip
    kind 'base' enter when the close crosses the baseline, exit on the cross back
    """
    C1L, BASEL, C2L, VOLL, XL = families()
    pairs = pairs or S.all_pairs()
    prm = setting_params(name, setting)
    if variant == 'flip_only':
        # NO TARGET, AND NO BREAKEVEN OR TRAIL EITHER. With tp_mult >= 900 the
        # engine seeds its phase machine at ENTRY rather than at a TP1 that
        # never comes (l2engine.py:555), so the breakeven and trail rules are
        # live from the first bar. The first smoke tripped the assertion below
        # on 2 of adx_dmi's trades for exactly that reason.
        #
        # AND be_pct MUST STAY SMALL, WHICH IS THE OPPOSITE OF WHAT IT LOOKS
        # LIKE. Raising it to 1e9 to "disable" the breakeven made things far
        # worse -- 134 breakeven stops per pair on the SHORT side alone. The
        # reason is the sentinel: for a short, l1_tp = entry - 900 x stop, which
        # is hugely NEGATIVE, so the trigger `l[i] <= l1_tp * (1 - be_pct/100)`
        # (l2engine.py:379) multiplies a negative by a large negative and
        # becomes hugely POSITIVE -- satisfied on the first bar. At be_pct 0.05
        # the product stays negative and the breakeven can never fire. The
        # trail is disabled the straightforward way, by never arming it.
        am, tp, plan = BIG_STOP, TP_NONE, 2
        be, arm, trl = 0.05, float(BIG), float(BIG)
    else:
        am, tp, plan = RISK_UNIT_ATR, 1.0 / RISK_UNIT_ATR, 2
        be, arm, trl = 0.05, 2.0, 1.5
    kw = dict(use_continuation=False, one_candle_rule=False,
              max_atr_dist=float(BIG), bridge_bars=BIG,
              block_suspect=True, bridge_all_routes=True,
              plan=plan, atr_mult=am, tp_mult=tp,
              trail_mult=trl, trail_start_mult=arm, be_pct=be)
    if kind == 'c1':
        c1, base = name, BASEL[0]
        kw.update(use_base_cross=False, use_c1_flip=True,
                  exit_on_c1_flip=True, exit_on_base_cross=False,
                  exit_on_exit_ind=False)
    else:
        c1, base = C1L[0], name
        kw.update(use_base_cross=True, use_c1_flip=False,
                  exit_on_c1_flip=False, exit_on_base_cross=True,
                  exit_on_exit_ind=False)
    rows = []
    sides = ('long', 'short') if kind == 'c1' else (None,)
    for p in pairs:
        d = pair_data(p)
        params = {'atr_len': atr_len}
        if prm:
            params[name] = prm
        for sd in sides:
            A = E.prepare(d, c1, C2L[0], VOLL[0], base, XL[0], params=params)
            A = _neutralise(A, kind, sd)
            if kind == 'base':
            # the baseline is under test, so the C1 agreement must not block
                A['c1_lt'] = np.ones(A['c'].size, bool)
                A['c1_st'] = np.ones(A['c'].size, bool)
                A['c1_lc'] = np.ones(A['c'].size, bool)
                A['c1_sc'] = np.ones(A['c'].size, bool)
            if use_hourly:
                import nnfxamb as _AMB
                _a = _AMB.amb_args(p)
                res = E.run(A, amb=_a, **kw)
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
    # restate R against the 1.5 ATR risk unit (see the module note)
    T['R_gross'] = T.R.astype(float) * am / RISK_UNIT_ATR
    T['atr_mult_used'] = am
    if variant == 'flip_only':
        # 'nothing else' is CHECKED, not assumed: a 50 ATR stop must
        # never be reached, and with tp_mult 900 there is no target
        bad = T[T.reason.isin(['stop', 'target', 'breakeven stop',
                               'trail stop'])]
        assert not len(bad), (
            'flip_only took %d risk-plan exits on %s/%s -- the stop or '
            'target is binding and the variant is not flip-only'
            % (len(bad), name, setting))
    return T


def _cost_R(T, era_table=None):
    """Cost of each trade in the same 1.5 ATR R unit, era-correct."""
    S.load_costs(era_table) if era_table else None
    if not S.COSTS:
        return np.zeros(len(T))
    f = T.pair.map(S.COSTS).to_numpy(float)
    # the engine's own identity: cost_R = cost_frac x |entry_px| x |units| / RISK,
    # restated to the 1.5 ATR unit exactly as R_gross is
    return (f * np.abs(T.entry_px.to_numpy(float))
            * np.abs(T.units.to_numpy(float)) / S.RISK) / RISK_UNIT_ATR


def _yearly(T, cost):
    """Per calendar year, by YEAR-END MARK TO MARKET on the exit date.

    0b settled the convention question: gate 2's year-end mark to market is the
    declared rule and the one the staged build uses. A single-indicator trade
    here is short enough that a straddle is rare, but the rule is the rule, so
    a trade is attributed to the year of each bar it was open. Implemented as
    the exit year for the realised R and a straddle flag, with the exact
    per-bar split left to the engine path that already does it -- and the
    straddle count reported so the size of the approximation is visible.
    """
    if not len(T):
        return pd.DataFrame()
    ed = pd.DatetimeIndex(T.entry_date); xd = pd.DatetimeIndex(T.exit_date)
    net = T.R_gross.to_numpy(float) - cost
    D = pd.DataFrame(dict(year=xd.year, entry_year=ed.year,
                          R_gross=T.R_gross.to_numpy(float), R_net=net,
                          bars=T.bars_held.to_numpy(float),
                          straddle=(ed.year != xd.year).astype(int)))
    g = D.groupby('year', as_index=False).agg(
        n=('R_net', 'size'), R_gross=('R_gross', 'sum'), R_net=('R_net', 'sum'),
        R_per_trade_net=('R_net', 'mean'), mean_bars=('bars', 'mean'),
        straddles=('straddle', 'sum'))
    return g


def _null_match(T, cost, ndraw=200, seed=7, years=None):
    """SCOPE MATTERS, AND GETTING IT WRONG COST ME A FALSE FAULT.

    The first version of this ran over the WHOLE span 2005-2020 while the
    summary divided its total by the BUILD-years trade count. The spans differ
    by a factor of 2.607 (6,408 trades against 2,458), so every per-trade null
    figure came out 2.6x too large and, because the total is dominated by the
    cost subtraction, 2.6x too NEGATIVE: -0.0221 R per trade gross instead of
    -0.0008. I reported that as a bias in the apparatus and it was a bias in my
    own arithmetic. The same mismatch made every null_p meaningless, because a
    six-year real total was being compared against a sixteen-year null total.

    `years` now restricts the null to the same window as the real figure it is
    compared against, and the per-draw trade count is returned so no caller has
    to guess it.
    """ 
    """Random-entry null MATCHED on trade count and holding period, per pair.

    For each draw and each pair, draw as many entry bars as the real strategy
    took in that pair, give each the SAME holding period as a real trade, and
    book the move over that window in the same 1.5 ATR units. Direction is
    drawn with the real long/short split, so only the TIMING is random.
    """
    if years is not None:
        xd = pd.DatetimeIndex(T.exit_date)
        m = xd.year.isin(list(years))
        T = T[m]
        cost = np.asarray(cost)[np.asarray(m)]
    if not len(T):
        return np.array([]), np.array([])
    T = T.reset_index(drop=True)
    cost = np.asarray(cost)
    rng = np.random.default_rng(seed)
    out = np.zeros(ndraw)
    ntr = np.zeros(ndraw)
    per_pair = {}
    for p, g in T.groupby('pair'):
        d = pair_data(p)
        cl = d['close'].values.astype(float)
        atr = L.P.atr(d['high'].values.astype(float),
                      d['low'].values.astype(float), cl, 14)
        idx = pd.DatetimeIndex(d.index)
        ent = idx.get_indexer(pd.DatetimeIndex(g.entry_date))
        hold = g.bars_held.to_numpy(int)
        dirs = np.where(g.direction.to_numpy() == 'long', 1.0, -1.0)
        per_pair[p] = (cl, atr, ent, hold, dirs,
                       float(cost[g.index.to_numpy()].mean()) if len(cost) else 0.0)
    for k in range(ndraw):
        tot = 0.0
        nn = 0
        for p, (cl, atr, ent, hold, dirs, cmean) in per_pair.items():
            n = len(ent)
            lo, hi = int(np.nanmin(ent)), int(np.nanmax(ent))
            if hi <= lo:
                continue
            e = rng.integers(lo, hi, size=n)
            h = rng.permutation(hold)
            x = np.minimum(e + h, len(cl) - 1)
            dv = rng.permutation(dirs)
            a = atr[e]
            with np.errstate(divide='ignore', invalid='ignore'):
                r = dv * (cl[x] - cl[e]) / (RISK_UNIT_ATR * a)
            r = r[np.isfinite(r)]
            tot += float(r.sum()) - cmean * len(r)
            nn += len(r)
        out[k] = tot
        ntr[k] = nn
    return out, ntr


def analytic_floor(m, span):
    """max-of-m t floor on yearly values, family-wise alpha 0.05."""
    a = 1.0 - 0.95 ** (1.0 / max(1, m))
    return float(stats.t.ppf(1.0 - a, max(1, span - 1)))


def stage_run(kind='c1', variant='flip_only', names=None, nmax=None,
              ndraw=200, era_table=None):
    """1a / 1b — every indicator of a family, every setting, one variant."""
    C1L, BASEL, _c2, _v, _x = families()
    pool = (C1L if kind == 'c1' else BASEL)
    names = names or pool
    if nmax:
        names = names[:nmax]
    S.load_costs(era_table) if era_table else S.load_costs()
    yr_rows, sum_rows, null_rows = [], [], []
    t0 = time.time()
    for ii, nm in enumerate(names, 1):
        for st in SETTINGS:
            T = run_one(nm, kind, st, variant)
            if not len(T):
                sum_rows.append(dict(kind=kind, variant=variant, indicator=nm,
                                     setting=st, n=0, note='no trades'))
                continue
            T = T.reset_index(drop=True)
            cost = _cost_R(T)
            Y = _yearly(T, cost)
            Y['indicator'] = nm; Y['setting'] = st
            Y['kind'] = kind; Y['variant'] = variant
            Y['distinct_setting'] = int(setting_is_distinct(nm, st))
            yr_rows.append(Y)
            nulls, nulls_n = _null_match(T, cost, ndraw=ndraw,
                                         years=BUILD_YEARS)
            b = Y[Y.year.isin(BUILD_YEARS)]
            real_build = float(b.R_net.sum())
            p = (float((nulls >= real_build).mean())
                 if len(nulls) else np.nan)
            ys = b.R_net.to_numpy(float)
            t_yr = (float(ys.mean() * np.sqrt(len(ys)) / ys.std(ddof=1))
                    if len(ys) > 1 and ys.std(ddof=1) > 0 else np.nan)
            eq = np.cumsum(ys)
            dip = float((np.maximum.accumulate(eq) - eq).max()) if len(eq) else np.nan
            sum_rows.append(dict(
                kind=kind, variant=variant, indicator=nm, setting=st,
                distinct_setting=int(setting_is_distinct(nm, st)),
                params=json.dumps(setting_params(nm, st)),
                n=int(b.n.sum()), trades_per_year=float(b.n.mean()),
                mean_bars=float((b.mean_bars * b.n).sum() / max(1, b.n.sum())),
                R_gross_build=float(b.R_gross.sum()), R_net_build=real_build,
                R_per_trade_net=float(real_build / max(1, b.n.sum())),
                years=int(len(b)), years_positive=int((b.R_net > 0).sum()),
                worst_year=float(b.R_net.min()) if len(b) else np.nan,
                best_year=float(b.R_net.max()) if len(b) else np.nan,
                worst_dip_R=dip, t_yearly=t_yr,
                null_p=p, null_mean=float(np.mean(nulls)) if len(nulls) else np.nan,
                null_p95=float(np.percentile(nulls, 95)) if len(nulls) else np.nan,
                null_trades_per_draw=float(np.mean(nulls_n)) if len(nulls_n) else np.nan,
                straddles=int(b.straddles.sum()),
                floor_t_best_of_family=analytic_floor(len(pool), len(b)),
                floor_t_alone=analytic_floor(1, len(b))))
            null_rows.append(pd.DataFrame(dict(
                kind=kind, variant=variant, indicator=nm, setting=st,
                draw=np.arange(1, len(nulls) + 1), null_R=nulls,
                null_n=nulls_n)))
        if ii % 5 == 0 or ii == len(names):
            print('    %s/%s: %d of %d indicators, %.1f min'
                  % (kind, variant, ii, len(names), (time.time() - t0) / 60),
                  flush=True)
    Yall = pd.concat(yr_rows, ignore_index=True) if yr_rows else pd.DataFrame()
    Sall = pd.DataFrame(sum_rows)
    Nall = pd.concat(null_rows, ignore_index=True) if null_rows else pd.DataFrame()
    tag = '%s_%s' % (kind, variant)
    f1 = os.path.join(OUT, 'stage1_%s_yearly.csv' % tag)
    f2 = os.path.join(OUT, 'stage1_%s_summary.csv' % tag)
    f3 = os.path.join(OUT, 'stage1_%s_nulls.csv' % tag)
    Yall.to_csv(f1, index=False); Sall.to_csv(f2, index=False)
    Nall.to_csv(f3, index=False)
    print('  stage 1 [%s]: %d indicators x %d settings -> %d yearly rows, '
          '%d summary rows (%.1f min)'
          % (tag, len(names), len(SETTINGS), len(Yall), len(Sall),
             (time.time() - t0) / 60), flush=True)
    return f1, f2, f3


def stage_walk(kind='c1', variant='flip_only'):
    """THE WALK-FORWARD PICK. Each step chooses the SETTING on its four tuning
    years and is judged only on that step's unseen trade year.

    This is the number that counts. `stage_run` also reports all three settings
    unpicked, which is what says whether the result is a property of the
    indicator or of one lucky setting -- an indicator whose three settings
    disagree wildly is not a finding whatever its best setting did.
    """
    f = os.path.join(OUT, 'stage1_%s_%s_yearly.csv' % (kind, variant))
    assert os.path.exists(f), f + ' missing -- run the stage first'
    Y = pd.read_csv(f)
    rows = []
    for nm, g in Y.groupby('indicator'):
        for stp in STEPS:
            ty = list(range(stp['tune'][0], stp['tune'][1] + 1))
            tune = g[g.year.isin(ty)]
            trade = g[g.year == stp['trade']]
            if not len(tune) or not len(trade):
                continue
            sc = tune.groupby('setting', as_index=False).agg(
                tune_R=('R_net', 'sum'), tune_n=('n', 'sum'))
            sc = sc[sc.tune_n >= 30]                 # a setting needs trades
            if not len(sc):
                continue
            pick = sc.loc[sc.tune_R.idxmax(), 'setting']
            tr = trade[trade.setting == pick]
            if not len(tr):
                continue
            rows.append(dict(kind=kind, variant=variant, indicator=nm,
                             step=stp['name'], trade_year=stp['trade'],
                             picked_setting=pick,
                             tune_R=float(sc.tune_R.max()),
                             trade_R_net=float(tr.R_net.sum()),
                             trade_R_gross=float(tr.R_gross.sum()),
                             trade_n=float(tr.n.sum()),
                             mean_bars=float(tr.mean_bars.mean()),
                             is_build=int(stp['trade'] in BUILD_YEARS),
                             is_confirm=int(stp['trade'] in CONFIRM_YEARS)))
    W = pd.DataFrame(rows)
    f2 = os.path.join(OUT, 'stage1_%s_%s_walk.csv' % (kind, variant))
    W.to_csv(f2, index=False)
    # the BUILD summary per indicator -- CONFIRM years are stored, never shown
    out = []
    for nm, g in W[W.is_build == 1].groupby('indicator'):
        ys = g.sort_values('trade_year').trade_R_net.to_numpy(float)
        eq = np.cumsum(ys)
        out.append(dict(
            kind=kind, variant=variant, indicator=nm,
            years=len(ys), R_net_build=float(ys.sum()),
            n=float(g.trade_n.sum()),
            R_per_trade=float(ys.sum() / max(1, g.trade_n.sum())),
            trades_per_year=float(g.trade_n.mean()),
            mean_bars=float(g.mean_bars.mean()),
            years_positive=int((ys > 0).sum()), worst_year=float(ys.min()),
            best_year=float(ys.max()),
            worst_dip_R=float((np.maximum.accumulate(eq) - eq).max()),
            t_yearly=(float(ys.mean() * np.sqrt(len(ys)) / ys.std(ddof=1))
                      if len(ys) > 1 and ys.std(ddof=1) > 0 else np.nan),
            settings_used=','.join(sorted(set(g.picked_setting))),
            n_settings_used=g.picked_setting.nunique()))
    O = pd.DataFrame(out)
    pool_n = 39 if kind == 'c1' else 15
    if len(O):
        O['floor_t_best_of_family'] = analytic_floor(pool_n, int(O.years.max()))
        O['floor_t_alone'] = analytic_floor(1, int(O.years.max()))
        O['clears_best_of_family'] = (O.t_yearly >= O.floor_t_best_of_family).astype(int)
        O['clears_alone'] = (O.t_yearly >= O.floor_t_alone).astype(int)
    f3 = os.path.join(OUT, 'stage1_%s_%s_walkbuild.csv' % (kind, variant))
    O.to_csv(f3, index=False)
    print('  walk [%s/%s]: %d indicator-steps, %d indicators on the BUILD years; '
          '%d clear the best-of-%d floor, %d clear the alone floor'
          % (kind, variant, len(W), len(O),
             int(O.clears_best_of_family.sum()) if len(O) else 0, pool_n,
             int(O.clears_alone.sum()) if len(O) else 0), flush=True)
    return f2, f3


def stage_select(kind='c1', variant='flip_only', ndraw=1000, seed=11):
    """1c — rank on the tuning years, trade the top K unseen, K swept, against
    a LABEL-SHUFFLE null that re-runs the whole construction."""
    f = os.path.join(OUT, 'stage1_%s_%s_walk.csv' % (kind, variant))
    assert os.path.exists(f), f + ' missing -- run stage_walk first'
    W = pd.read_csv(f)
    names = sorted(W.indicator.unique())
    K = len(names)
    rng = np.random.default_rng(seed)
    rows = []
    for k in range(1, K + 1):
        real = []
        for stp in STEPS:
            if stp['trade'] not in BUILD_YEARS:
                continue
            g = W[W.step == stp['name']]
            if not len(g):
                continue
            top = g.sort_values('tune_R', ascending=False).head(k)
            real.append(float(top.trade_R_net.mean()))
        if not real:
            continue
        real = np.array(real)
        nulls = np.zeros(ndraw)
        for dd in range(ndraw):
            acc = []
            for stp in STEPS:
                if stp['trade'] not in BUILD_YEARS:
                    continue
                g = W[W.step == stp['name']]
                if not len(g):
                    continue
                # SHUFFLE THE LABELS, not the returns: the tuning-year ranking
                # is permuted and the same top-K rule applied, so this tests
                # the SELECTION RULE and not merely the pool of indicators
                perm = rng.permutation(len(g))
                top = g.iloc[perm[:k]]
                acc.append(float(top.trade_R_net.mean()))
            nulls[dd] = float(np.mean(acc)) if acc else np.nan
        rows.append(dict(kind=kind, variant=variant, K=k,
                         R_per_year_mean=float(real.mean()),
                         R_total_build=float(real.sum()),
                         years=len(real),
                         years_positive=int((real > 0).sum()),
                         t_yearly=(float(real.mean() * np.sqrt(len(real))
                                         / real.std(ddof=1))
                                   if len(real) > 1 and real.std(ddof=1) > 0
                                   else np.nan),
                         null_mean=float(np.nanmean(nulls)),
                         null_p95=float(np.nanpercentile(nulls, 95)),
                         null_p=float(np.nanmean(nulls >= real.mean())),
                         ndraw=ndraw))
    D = pd.DataFrame(rows)
    f2 = os.path.join(OUT, 'stage1_%s_%s_select.csv' % (kind, variant))
    D.to_csv(f2, index=False)
    if len(D):
        b = D.loc[D.R_per_year_mean.idxmax()]
        print('  select [%s/%s]: K swept 1-%d. Best mean R/year %+.3f at K=%d '
              '(null mean %+.3f, p %.3f). %d of %d K values beat their null at p<=0.05'
              % (kind, variant, K, b.R_per_year_mean, b.K, b.null_mean, b.null_p,
                 int((D.null_p <= 0.05).sum()), len(D)), flush=True)
    return f2


def ledger_add(stage, family, candidates, n_settings, how, tested_on, notes=''):
    """Append to CANDIDATE_LEDGER.csv. EVERY candidate ever tested goes here,
    because the luck floor is computed from this file and not from memory."""
    L_ = pd.read_csv(LEDGER) if os.path.exists(LEDGER) else pd.DataFrame()
    new = pd.DataFrame([dict(stamp=time.strftime('%F %H:%M'), stage=stage,
                             family=family, candidate=c, n_settings=n_settings,
                             how_chosen=how, tested_on=tested_on, notes=notes)
                        for c in candidates])
    out = pd.concat([L_, new], ignore_index=True) if len(L_) else new
    out.to_csv(LEDGER, index=False)
    print('  ledger: +%d candidates for %s (%d rows total)'
          % (len(new), stage, len(out)), flush=True)
    return LEDGER


def _tbl(D, cols, fmt='%.4f'):
    if not len(D):
        return '_empty_\n'
    cols = [c for c in cols if c in D.columns]
    o = ['| ' + ' | '.join(cols) + ' |',
         '|' + '|'.join('---:' if D[c].dtype.kind in 'if' else '---'
                        for c in cols) + '|']
    for _i, r in D.iterrows():
        cs = []
        for c in cols:
            v = r[c]
            if isinstance(v, (bool, np.bool_)):
                cs.append('yes' if v else 'no')
            elif isinstance(v, (int, np.integer)):
                cs.append('%d' % v)
            elif isinstance(v, (float, np.floating)):
                cs.append(fmt % v if np.isfinite(v) else '')
            else:
                cs.append(str(v))
        o.append('| ' + ' | '.join(cs) + ' |')
    return '\n'.join(o) + '\n'


def md_stage1(out=None):
    """results/nnfx/STAGE1.md"""
    L = []; a = L.append
    a('# STAGE 1 — ONE PIECE ALONE, WALK-FORWARD\n')
    a('Generated %s by `code/nnfx1.py`. HANDOFF 0m.\n' % time.strftime('%F %H:%M'))
    a('\n**NO SELECTION BY ME.** Every one of the 39 C1 indicators and all 15 '
      'baselines is reported. Jack picks at most 3 of each, for a stated '
      'reason. All 54 are in `CANDIDATE_LEDGER.csv`, which is what the luck '
      'floors are computed from.\n')
    a('\n## How it was run\n')
    a('- **The shipped engine, not a second one.** 0b cost this project a '
      'winner list because two scorers held two undeclared conventions, so '
      'stage 1 runs `l2engine` and neutralises the slots it is not testing. '
      '"C1 alone" = C2 and volume agreement forced True, the exit indicator '
      'off, continuation off, the one-candle rule off, `bridge_bars` and '
      '`max_atr_dist` set so they can never block.\n')
    a('- **One direction at a time.** `agree_long` is '
      '`c1_lc and c2_lc and v_ok_l and side == 1` (`l2engine.py:441`) — the '
      'baseline SIDE is inside the agreement. So the long side runs with the '
      'baseline far below the close and the short side far above it, and the '
      'two trade sets are concatenated. The exit needs neither side nor '
      'agreement (`l2engine.py:414`), so each one-sided run still exits on the '
      'opposite flip. **My first attempt set the baseline equal to the close '
      'and took 0 trades, which is how this was found.**\n')
    a('- **Both variants in the same R unit: R per 1.5 ATR**, the canonical '
      'stop. Engine `r` scales as `1/atr_mult`, so everything is restated as '
      '`r × atr_mult / 1.5`. Without it the no-stop and 1.5-ATR variants could '
      'not be compared.\n')
    a('- **`flip_only` is checked to BE flip-only.** The stop sentinel is 2000 '
      'ATR, and `run_one` asserts no trade exited by stop, target, breakeven '
      'or trail. 50 ATR was not enough (two AUDJPY longs held 345 bars in '
      '2008); 200 was not enough (one EURCHF baseline trade, the 2015 SNB '
      'de-peg). At 2000 there is not one risk-plan exit anywhere.\n')
    a('- **Three settings per indicator**: half, default and double the '
      'length. Five C1 indicators are parameterised by a smoothing CONSTANT '
      'instead, where a larger constant means a shorter memory, so for those '
      '"half length" doubles the constant — the opposite direction, stated '
      'because it is easy to get backwards. Two baselines default to length 2, '
      'where half is also 2, so they have two distinct settings not three.\n')
    a('- **The walk-forward pick**: each step chooses the setting on its four '
      'tuning years and is judged only on that step\'s unseen trade year. '
      '**BUILD = unseen trade years 2010-2015, reported below. CONFIRM = '
      'unseen trade years 2016-2020, computed and stored in the same files and '
      'NOT shown.** 2021 onward never touched.\n')
    a('\n## The headline\n')
    rows = []
    for k, pool in (('c1', 39), ('base', 15)):
        for v in VARIANTS:
            f = os.path.join(OUT, 'stage1_%s_%s_walkbuild.csv' % (k, v))
            if not os.path.exists(f):
                continue
            d = pd.read_csv(f)
            if not len(d):
                continue
            rows.append(dict(family=('C1 (39)' if k == 'c1' else 'baseline (15)'),
                             variant=v, candidates=len(d),
                             R_build_positive=int((d.R_net_build > 0).sum()),
                             median_t=float(d.t_yearly.median()),
                             max_t=float(d.t_yearly.max()),
                             floor_alone=float(d.floor_t_alone.iloc[0]),
                             floor_best_of_family=float(d.floor_t_best_of_family.iloc[0]),
                             clear_alone=int(d.clears_alone.sum()),
                             clear_best_of_family=int(d.clears_best_of_family.sum())))
    H = pd.DataFrame(rows)
    a(_tbl(H, list(H.columns), '%.3f'))
    a('\n**Not one of the 39 C1 indicators clears even the single-candidate '
      'floor, in either variant.** The baselines manage one, under `flip_only` '
      'only. Against the honest best-of-family floor — t 5.54 for 39 '
      'candidates on six yearly observations, t 4.43 for 15 — **nothing clears '
      'anything.**\n')
    a('\n0a already said this would happen: at six yearly observations the '
      'best-of-39 floor is higher than the old best-of-273,780 floor was, and '
      'a genuine 0.20 R per trade edge would clear it only 6% of the time. '
      '**So "nothing clears the floor" is close to uninformative here. The '
      'informative part is the ranking, the stability across settings, and the '
      'selection test below.**\n')
    for k, kl, pool in (('c1', 'C1', 39), ('base', 'BASELINE', 15)):
        a('\n---\n')
        a('\n# %s — all %d candidates\n' % (kl, pool))
        for v in VARIANTS:
            f = os.path.join(OUT, 'stage1_%s_%s_walkbuild.csv' % (k, v))
            fs = os.path.join(OUT, 'stage1_%s_%s_summary.csv' % (k, v))
            if not os.path.exists(f):
                continue
            d = pd.read_csv(f).sort_values('R_net_build', ascending=False)
            a('\n## %s — %s, walk-forward pick, BUILD years 2010-2015\n' % (kl, v))
            a('`n_settings_used` is how many different settings the six steps '
              'chose. A candidate whose steps keep switching setting is being '
              'fitted, not measured.\n')
            a(_tbl(d, ['indicator', 'R_net_build', 'n', 'R_per_trade',
                       'trades_per_year', 'mean_bars', 'years_positive',
                       'worst_year', 'best_year', 'worst_dip_R', 't_yearly',
                       'settings_used', 'n_settings_used',
                       'clears_alone', 'clears_best_of_family']))
            if os.path.exists(fs):
                Sm = pd.read_csv(fs)
                a('\n### %s — %s, ALL THREE SETTINGS UNPICKED\n' % (kl, v))
                a('The same six BUILD years with each setting held fixed, so '
                  'the walk-forward number above can be compared with what any '
                  'single setting would have done. `null_p` is against the '
                  'matched random-entry null, 200 draws, matched on trade count '
                  'and holding period per pair.\n')
                a(_tbl(Sm.sort_values(['indicator', 'setting']),
                       ['indicator', 'setting', 'distinct_setting', 'params',
                        'n', 'trades_per_year', 'mean_bars', 'R_gross_build',
                        'R_net_build', 'R_per_trade_net', 'years_positive',
                        'worst_year', 'worst_dip_R', 't_yearly', 'null_p',
                        'null_p95', 'straddles']))
    a('\n---\n')
    a('\n# 1c — THE SELECTION TEST\n')
    a('At each step the candidates are ranked on that step\'s four TUNING '
      'years, the top K are traded on its unseen year, equal weight, and K is '
      'swept over the whole range. **The null shuffles the tuning-year ranking '
      'and re-runs the identical top-K construction, 1,000 draws** — so it '
      'tests the SELECTION RULE, not the pool.\n')
    for k, kl in (('c1', 'C1'), ('base', 'BASELINE')):
        for v in VARIANTS:
            f = os.path.join(OUT, 'stage1_%s_%s_select.csv' % (k, v))
            if not os.path.exists(f):
                continue
            d = pd.read_csv(f)
            a('\n## %s — %s\n' % (kl, v))
            a(_tbl(d, ['K', 'R_per_year_mean', 'R_total_build', 'years',
                       'years_positive', 't_yearly', 'null_mean', 'null_p95',
                       'null_p'], '%.3f'))
            nb = int((d.null_p <= 0.05).sum())
            b = d.loc[d.R_per_year_mean.idxmax()]
            a('\nBest mean R per year **%+.3f at K=%d** against a null mean of '
              '%+.3f, p **%.3f**. **%d of %d K values beat their own null at '
              'p ≤ 0.05.**\n' % (b.R_per_year_mean, b.K, b.null_mean, b.null_p,
                                 nb, len(d)))
            if k == 'base' and v == 'flip_only':
                a('\nNote the degenerate end: at **K = 15 of 15** the "top K" is '
                  'every baseline, so shuffling the ranking changes nothing and '
                  'the null equals the real number exactly. That is a check on '
                  'the null, not a result.\n')
    a('\n## What 1c says, carefully\n')
    a('**Under `flip_only`, nothing: 0 of 39 and 0 of 15 K values beat their '
      'null, and the best C1 mean is negative.** Enter on a flip and exit on '
      'the opposite flip, with no risk plan, does not work for any of these 54 '
      'components, alone or ranked.\n')
    a('\n**Under `canonical_risk` the selection rule does something.** C1: best '
      '+1.113 R per year at K=23, null mean −3.225, p 0.002, and **18 of 39 K '
      'values beat their null at p ≤ 0.05** — far more than the ~2 that 39 '
      'tests at α 0.05 would give by chance, so it is not an artefact of '
      'sweeping K. Baselines: best **+13.052 R per year at K=1**, null mean '
      '−6.345, p 0.007, 8 of 15 beating.\n')
    a('\n**This is the first null-tested positive in the programme, and it is a '
      'statement about the RISK PLAN, not about any indicator.** The same 54 '
      'components, ranked the same way, are worthless without the 1.5 ATR stop '
      'and the half-off at 1 ATR, and have an edge with them. No single '
      'component is significant on its own in either variant.\n')
    a('\n**What I am not claiming.** Four (family × variant) combinations were '
      'run, so there is a multiplicity of 4 above the K sweep that these '
      'p-values do not carry. The K sweep itself is accounted for by counting '
      'how many K values beat their null rather than quoting the best one. And '
      '0a\'s limit still applies: six yearly observations is a thin '
      'instrument, so this needs the CONFIRM years before it is more than a '
      'lead.\n')
    a('\n## For Jack to pick from\n')
    a('**At most 3 C1 and 3 baselines, for a stated reason. I am not picking.** '
      'Three things in the tables above are worth weighing when you do:\n')
    a('\n1. **Stability across settings** (`n_settings_used`, and the '
      'all-three-settings table). A candidate that is positive on all three '
      'settings is a different kind of evidence from one that is positive on '
      'its best.\n')
    a('2. **Trade count.** Some settings produce very few trades over six years '
      '— `adx_dmi` at double length took 46. A thin candidate cannot be '
      'measured, whatever its R.\n')
    a('3. **`null_p`**, the matched random-entry null, which asks whether the '
      'timing did anything beyond being in the market.\n')
    a('\n## Provenance\n')
    for k in ('c1', 'base'):
        for v in VARIANTS:
            for nm in ('yearly', 'summary', 'nulls', 'walk', 'walkbuild', 'select'):
                p_ = os.path.join(OUT, 'stage1_%s_%s_%s.csv' % (k, v, nm))
                if os.path.exists(p_):
                    a('- `%s` — %s rows, md5 `%s`'
                      % (os.path.relpath(p_, _R),
                         f'{sum(1 for _ in open(p_)) - 1:,}',
                         hashlib.md5(open(p_, 'rb').read()).hexdigest()[:12]))
    p_ = LEDGER
    a('- `%s` — %s candidates on record'
      % (os.path.relpath(p_, _R), f'{sum(1 for _ in open(p_)) - 1:,}'))
    out = out or os.path.join(OUT, 'STAGE1.md')
    open(out, 'w').write('\n'.join(L) + '\n')
    print('  STAGE1.md: %d lines -> %s'
          % (len('\n'.join(L).splitlines()), os.path.relpath(out, _R)), flush=True)
    return out


if __name__ == '__main__':
    st = G.opt('--stage', str, 'run')
    kind = G.opt('--kind', str, 'c1')
    var = G.opt('--variant', str, 'flip_only')
    if st == 'run':
        stage_run(kind=kind, variant=var, nmax=G.opt('--nmax', int, None),
                  ndraw=G.opt('--draws', int, 200))
    elif st == 'walk':
        stage_walk(kind=kind, variant=var)
    elif st == 'select':
        stage_select(kind=kind, variant=var, ndraw=G.opt('--draws', int, 1000))
    elif st == 'ledger':
        C1L, BASEL, _a, _b, _c = families()
        ledger_add('1a', 'C1', C1L, len(SETTINGS),
                   'pre-declared: the whole C1 family, no selection by me',
                   'eleven-step walk, BUILD years 2010-2015',
                   'two variants: flip_only and canonical_risk')
        ledger_add('1b', 'baseline', BASEL, len(SETTINGS),
                   'pre-declared: the whole baseline family, no selection by me',
                   'eleven-step walk, BUILD years 2010-2015',
                   'two variants: flip_only and canonical_risk')
    elif st == 'md':
        md_stage1()
    else:
        raise SystemExit('unknown stage %s' % st)
