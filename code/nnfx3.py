import os,sys
_R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_R, 'code'))
os.chdir(_R)
ROOTOUT = os.path.join(_R, 'results')
"""STAGE 3 — ADD A SECOND CONFIRMATION (C2) TO THE CARRIED-FORWARD THREE.

Jack, 24 Nov, after reading STAGE2.md. The three he carried forward, with his
reason recorded in the ledger (largest paired improvement from adding the
baseline, positive in most unseen years):

    A  ichimoku_signals            + sma_baseline, full_nnfx
    B  schaff_trend_cycle_signals  + sma_baseline, side_xentry
    C  halftrend_signals           + sma_baseline, full_nnfx

`jack` is the main plan, `textbook` beside it.

FIVE C2 CANDIDATES, DECLARED IN ADVANCE AND NOT ADDED TO:
  (i)   each of the OTHER TWO C1 picks used as C2 -- two per base, so the
        candidate set differs by base and is still two candidates;
  (ii)  kalman_filter and dspo, the next most stable in stage 1;
  (iii) CURRENCY AGREEMENT, swept N = 3..6: take the trade only if the BASE
        currency is rising against at least N of its other six partners AND
        the QUOTE currency is falling against at least N of its other six,
        measured by THE SAME C1 on those pairs, one-bar lag.

HOW THE C2 SLOT IS FILLED. Stage 2 neutralised it -- `A['c2_lc']` and
`A['c2_sc']` were set all-True after `E.prepare`, so agreement reduced to the
C1 and the baseline side. Stage 3 simply stops overriding them, so a real C2
has to agree before a route can fire. The currency-agreement rule is not an
indicator, so it is computed here and written into the same two arrays: it
occupies the C2 slot as a RULE, which is exactly what it is.

THE ONE-BAR LAG ON THE AGREEMENT RULE IS EXPLICIT. The cross-pair counts are
shifted one bar before they are used, so a trade on pair BQ at bar t can only
see other pairs' signals through bar t-1. Jack asked for it in those words and
it is not left to the engine's own convention.

THE C2 SETTING IS PICKED WALK-FORWARD, the C1 and baseline settings are NOT
re-picked: they are read from stage 2's walk, which already chose them on each
step's own four tuning years. The only new choice in stage 3 is the C2, so
that is the only thing tuned here.

Unseen trade years 2010-2015 are the evidence. 2016-2020 are computed and
written to the yearly csv and are summarised NOWHERE. 2021 onward is not read.
"""
import time, json, itertools
import numpy as np, pandas as pd

import l2lib as L
import l2sweep as S
import l2engine as E
import l2r2gate1 as G
import nnfx1 as N
import nnfx2s as S2
import l2r2winners as WN
import nnfxvol as VOL

OUT = os.path.join(ROOTOUT, 'nnfx')
os.makedirs(OUT, exist_ok=True)
CACHE = os.path.join(ROOTOUT, 'nnfx_ccy')
os.makedirs(CACHE, exist_ok=True)

BUILD_YEARS = S2.BUILD_YEARS
CONFIRM_YEARS = S2.CONFIRM_YEARS
STEPS = S2.STEPS
SETTINGS = S2.SETTINGS
PLANS_USED = ('jack', 'textbook')
MAIN_PLAN = 'jack'

# Jack's carried-forward three, with his ruleset for each.
BASES = (('A', 'ichimoku_signals', 'sma_baseline', 'full_nnfx'),
         ('B', 'schaff_trend_cycle_signals', 'sma_baseline', 'side_xentry'),
         ('C', 'halftrend_signals', 'sma_baseline', 'full_nnfx'))
C1_PICKS = ('ichimoku_signals', 'schaff_trend_cycle_signals',
            'halftrend_signals')
C2_EXTRA = ('kalman_filter_signals', 'dspo_signals')
CCY_N = (3, 4, 5, 6)
G8 = ('EUR', 'GBP', 'AUD', 'NZD', 'USD', 'CAD', 'CHF', 'JPY')
MIN_TRADES = 30


def c2_candidates(c1):
    """-> [(kind, name_or_None, label)] -- the five, for this base's C1."""
    out = []
    for other in C1_PICKS:
        if other != c1:
            out.append(('ind', other, S2._short(other, '_signals')))
    for nm in C2_EXTRA:
        out.append(('ind', nm, S2._short(nm, '_signals')))
    out.append(('ccy', None, 'currency_agreement'))
    return out


# ==================== THE CURRENCY AGREEMENT RULE ====================
def _pair_map():
    """-> {(base,quote): pair} for the 28, both orientations resolvable."""
    m = {}
    for p in S.all_pairs():
        m[(p[:3], p[3:6])] = p
    return m


def ccy_counts(c1, c1_set, verbose=False):
    """For every pair, how many of each currency's six OTHER partners the C1
    says it is rising against -- and falling against -- at each bar.

    Returns {pair: dict(index=DatetimeIndex, nb_up, nb_dn, nq_up, nq_dn)}, all
    ALREADY LAGGED ONE BAR.

    WHY A UNION INDEX. The 28 pairs do not share a calendar exactly, and a
    partner that has no bar on a given day must count as NO OPINION rather than
    as agreement. So every pair's confirmation is reindexed onto the union of
    all 28 calendars with False fill, the counts are taken there, and the
    result is read back onto each pair's own bars.
    """
    f = os.path.join(CACHE, 'ccy_%s_%s.npz' % (c1, c1_set))
    if os.path.exists(f):
        z = np.load(f, allow_pickle=True)
        idx = pd.DatetimeIndex(z['index'])
        out = {}
        for p in [str(x) for x in z['pairs']]:
            out[p] = dict(index=pd.DatetimeIndex(z['ix_' + p]),
                          nb_up=z['nbu_' + p], nb_dn=z['nbd_' + p],
                          nq_up=z['nqu_' + p], nq_dn=z['nqd_' + p])
        return out
    prm = N.setting_params(c1, c1_set)
    pairs = S.all_pairs()
    lc, sc, ixs = {}, {}, {}
    for p in pairs:
        d = N.pair_data(p)
        o, h, l, c = (d[k].values.astype(float)
                      for k in ('open', 'high', 'low', 'close'))
        _lt, _st, l_c, s_c, _t = E._conf(c1, o, h, l, c, prm, False)
        lc[p] = np.asarray(l_c, bool); sc[p] = np.asarray(s_c, bool)
        ixs[p] = pd.DatetimeIndex(d.index)
    uni = ixs[pairs[0]]
    for p in pairs[1:]:
        uni = uni.union(ixs[p])
    uni = pd.DatetimeIndex(sorted(set(uni)))
    PM = _pair_map()

    def on_uni(p, arr):
        # NO pandas reindex+fillna here: on an object column that raises a
        # FutureWarning, and the chains run under -W error::FutureWarning.
        z = np.zeros(len(uni), bool)
        sel = uni.get_indexer(ixs[p])
        ok = sel >= 0
        z[sel[ok]] = arr[ok]
        return z

    LCU = {p: on_uni(p, lc[p]) for p in pairs}
    SCU = {p: on_uni(p, sc[p]) for p in pairs}

    def rise(x, y):
        """X rising against Y, on the union index."""
        if (x, y) in PM:
            return LCU[PM[(x, y)]]
        if (y, x) in PM:
            return SCU[PM[(y, x)]]
        raise KeyError('%s/%s is not one of the 28' % (x, y))

    out = {}
    nu = len(uni)
    for p in pairs:
        b, q = p[:3], p[3:6]
        partners = [x for x in G8 if x not in (b, q)]
        assert len(partners) == 6, '%s has %d partners' % (p, len(partners))
        nb_up = np.zeros(nu, np.int16); nb_dn = np.zeros(nu, np.int16)
        nq_up = np.zeros(nu, np.int16); nq_dn = np.zeros(nu, np.int16)
        for x in partners:
            nb_up += rise(b, x); nb_dn += rise(x, b)
            nq_up += rise(q, x); nq_dn += rise(x, q)
        # ---- THE ONE-BAR LAG, EXPLICIT. Bar t sees through bar t-1 only.
        def lag(a):
            z = np.zeros_like(a); z[1:] = a[:-1]; return z
        nb_up, nb_dn, nq_up, nq_dn = (lag(a) for a in (nb_up, nb_dn, nq_up, nq_dn))
        # ---- back onto this pair's own bars
        sel = uni.get_indexer(ixs[p])
        ok = sel >= 0
        take = lambda a: np.where(ok, a[np.maximum(sel, 0)], 0).astype(np.int16)
        out[p] = dict(index=ixs[p], nb_up=take(nb_up), nb_dn=take(nb_dn),
                      nq_up=take(nq_up), nq_dn=take(nq_dn))
        if verbose:
            print('    %s: base up median %d, quote down median %d'
                  % (p, int(np.median(out[p]['nb_up'])),
                     int(np.median(out[p]['nq_dn']))), flush=True)
    kw = dict(index=np.asarray(uni, 'datetime64[ns]'),
              pairs=np.array(pairs, dtype=object))
    for p in pairs:
        kw['ix_' + p] = np.asarray(out[p]['index'], 'datetime64[ns]')
        kw['nbu_' + p] = out[p]['nb_up']; kw['nbd_' + p] = out[p]['nb_dn']
        kw['nqu_' + p] = out[p]['nq_up']; kw['nqd_' + p] = out[p]['nq_dn']
    np.savez_compressed(f, **kw)
    return out


# ==================== THE ENGINE RUN WITH A REAL C2 ====================
_RUNC = {}


def run_combo3(c1, c1_set, base, base_set, variant, ruleset,
               c2=None, c2_set='default', ccy_n=None,
               vol_rule=None, vol_opt=None, lowvol_q=VOL.LOWVOL_Q,
               peg_x=VOL.PEG_X_PLACEHOLDER,
               pairs=None, atr_len=14, use_hourly=True, cache=True):
    """Stage 2's run_combo with the C2 SLOT FILLED instead of neutralised.

    c2        a real confirmation indicator name, or None
    ccy_n     the currency-agreement threshold, or None
    both None -> the stage 2 control, C2 neutralised, which must reproduce
                 stage 2's own cell exactly (condition_c2_neutral checks it)

    Exactly one of c2 / ccy_n may be set.
    """
    assert not (c2 and ccy_n), 'c2 and ccy_n are alternatives, not a pair'
    key = (c1, c1_set, base, base_set, variant, ruleset, c2, c2_set, ccy_n,
           vol_rule, vol_opt, lowvol_q, peg_x, bool(use_hourly),
           tuple(pairs) if pairs else None)
    if cache and key in _RUNC:
        return _RUNC[key]
    C1L, BASEL, C2L, VOLL, XL = N.families()
    pairs = pairs or S.all_pairs()
    RS = S2.RULESETS[ruleset]
    PL = N.PLANS[variant]
    if variant == 'flip_only':
        am, tp = N.BIG_STOP, N.TP_NONE
    else:
        am, tp = float(PL['atr_mult']), float(PL['tp_mult'])
    _dist = (float(PL['max_atr_dist']) if (RS['dist'] and RS['side'])
             else float(N.BIG))
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
    c2_prm = N.setting_params(c2, c2_set) if c2 else None
    CC = ccy_counts(c1, c1_set) if ccy_n is not None else None
    rows = []
    sides = (None,) if RS['side'] else ('long', 'short')
    for p in pairs:
        d = N.pair_data(p)
        params = {'atr_len': atr_len}
        if c1_prm:
            params[c1] = c1_prm
        if b_prm:
            params[base] = b_prm
        if c2 and c2_prm:
            params[c2] = c2_prm
        for sd in sides:
            # THE C2 SLOT IS NAMED IN prepare ONLY WHEN A REAL C2 IS UNDER
            # TEST. With ccy_n or with neither, the slot is filled here, so
            # prepare is handed the family's first name and its output is
            # discarded -- the same thing stage 2 did.
            A = E.prepare(d, c1, (c2 or C2L[0]), VOLL[0], base, XL[0],
                          params=params)
            n = A['c'].size
            T_ = np.ones(n, bool)
            if ccy_n is not None:
                cc = CC[p]
                assert len(cc['nb_up']) == n, (
                    '%s: agreement counts %d bars against %d in the engine'
                    % (p, len(cc['nb_up']), n))
                A['c2_lc'] = ((cc['nb_up'] >= ccy_n)
                              & (cc['nq_dn'] >= ccy_n))
                A['c2_sc'] = ((cc['nb_dn'] >= ccy_n)
                              & (cc['nq_up'] >= ccy_n))
            elif not c2:
                A['c2_lc'] = T_.copy(); A['c2_sc'] = T_.copy()
            # THE VOLUME SLOT. Neutral in stage 3; stage 4's preview fills
            # it. Volume is directionless, so the same mask gates both sides.
            if vol_rule == 'ticks_above_trailing_median':
                vm = vol_mask_ticks(p, int(vol_opt))
                assert len(vm) == n, '%s: volume mask %d vs %d bars' % (
                    p, len(vm), n)
            elif vol_rule == 'layer1_activity_med_or_strong':
                vm = layer1_activity(p)
                assert len(vm) == n, '%s: activity mask %d vs %d bars' % (
                    p, len(vm), n)
            elif vol_rule:
                raise SystemExit('unknown vol_rule %s' % vol_rule)
            else:
                vm = T_.copy()
            # THE VOLATILITY FLOOR ANDs WITH the stage 4 rule: both are
            # "is this bar tradable", both are entry-only, and a bar the
            # floor rejects is not rescued by a volume rule accepting it.
            if lowvol_q:
                _ix, _lv = VOL.lowvol_mask(p, q=lowvol_q, causal=True)
                assert len(_lv) == n, '%s: lowvol mask %d vs %d bars' % (
                    p, len(_lv), n)
                vm = vm & (~_lv)
            if peg_x:
                _ix2, _pg = VOL.peg_mask(p, x=peg_x)
                assert len(_pg) == n, '%s: peg mask %d vs %d bars' % (
                    p, len(_pg), n)
                vm = vm & (~_pg)
            A['v_ok_l'] = vm.copy(); A['v_ok_s'] = vm.copy()
            A['x_el'] = np.zeros(n, bool); A['x_es'] = np.zeros(n, bool)
            if not RS['side']:
                K = 10.0 * float(np.nanmax(np.abs(A['c'])) + 1.0)
                A['bl'] = A['c'] - K if sd == 'long' else A['c'] + K
            if use_hourly:
                import nnfxamb as _AMB
                res = E.run(A, amb=_AMB.amb_args(p), **kw)
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
        out = pd.DataFrame()
    else:
        T = pd.concat(rows, ignore_index=True)
        T['R_gross'] = T.R.astype(float) * am / S2.RISK_UNIT_ATR
        T['atr_mult_used'] = am
        T['c1'] = c1; T['c1_setting'] = c1_set
        T['base'] = base; T['base_setting'] = base_set
        T['variant'] = variant; T['ruleset'] = ruleset
        T['c2'] = c2 or ''; T['c2_setting'] = (c2_set if c2 else '')
        T['ccy_n'] = (ccy_n if ccy_n is not None else -1)
        T['vol_rule'] = vol_rule or ''
        T['vol_opt'] = (vol_opt if vol_opt is not None else -1)
        T['lowvol_q'] = (lowvol_q if lowvol_q else 0.0)
        T['peg_x'] = (peg_x if peg_x else 0.0)
        out = T
    if cache:
        if len(_RUNC) > 40:
            _RUNC.clear()
        _RUNC[key] = out
    return out


# ==================== THE ZERO-EDGE CHECK ====================
def condition_c2_neutral(use_hourly=True, verbose=True):
    """FILLING THE C2 SLOT WITH ALL-TRUE MUST CHANGE NOTHING.

    Stage 2's control neutralised C2 by overwriting c2_lc/c2_sc after prepare.
    Stage 3 instead hands prepare a real C2 name. If the slot is genuinely the
    only difference, then naming a C2 and then overwriting its arrays with
    all-True must give the SAME TRADES as not naming one at all. If it does
    not, prepare is doing something else with the name and every paired number
    in this file would be measuring that instead of the C2.

    This is stage 3's equivalent of stage 2's neutralisation check, and no
    paired figure in STAGE3.md may be quoted unless it passes.
    """
    rows = []
    for (lab, c1, base, rs) in BASES:
        for v in PLANS_USED:
            a = run_combo3(c1, 'default', base, 'double', v, rs,
                           c2=None, use_hourly=use_hourly, cache=False)
            b = run_combo3(c1, 'default', base, 'double', v, rs,
                           c2='kalman_filter_signals', ccy_n=None,
                           use_hourly=use_hourly, cache=False)
            # b has a REAL c2; to make the comparison fair we re-run with the
            # real name but the slot neutralised, which is what this checks.
            c = _neutralised_with_name(c1, 'default', base, 'double', v, rs,
                                       'kalman_filter_signals', use_hourly)
            k = ['pair', 'direction', 'entry_date', 'exit_date', 'leg']
            na, nc = len(a), len(c)
            if na and nc:
                A_ = a[k].sort_values(k).reset_index(drop=True)
                C_ = c[k].sort_values(k).reset_index(drop=True)
                same = (na == nc) and A_.equals(C_)
                dR = abs(float(a.R.sum()) - float(c.R.sum()))
            else:
                same, dR = (na == nc), 0.0
            rows.append(dict(base=lab, c1=c1, ruleset=rs, variant=v,
                             legs_no_name=na, legs_named_neutral=nc,
                             identical=int(bool(same)), abs_dR=dR,
                             legs_real_c2=len(b)))
            if verbose:
                print('    zero-edge %s/%s: no-name %d legs, named+neutral %d '
                      'legs, identical %s, |dR| %.2e (real C2 %d legs)'
                      % (lab, v, na, nc, bool(same), dR, len(b)), flush=True)
    D = pd.DataFrame(rows)
    f = os.path.join(OUT, 'stage3_zeroedge.csv')
    S2._write_csv(D, f)
    ok = bool(len(D)) and bool((D.identical == 1).all()) and \
        float(D.abs_dR.max()) < 1e-9
    if verbose:
        print('  ZERO-EDGE CHECK: %s (%d cells, worst |dR| %.3e)'
              % ('PASS' if ok else 'FAIL', len(D),
                 float(D.abs_dR.max()) if len(D) else np.nan), flush=True)
    return D, ok


def _neutralised_with_name(c1, cs, base, bs, v, rs, c2name, use_hourly,
                           lowvol_q=VOL.LOWVOL_Q,
                           peg_x=VOL.PEG_X_PLACEHOLDER):
    """run_combo3 with a REAL c2 NAMED in prepare and then overwritten
    all-True -- the exact thing condition_c2_neutral compares against.

    THE C2 SLOT IS THE ONLY THING NEUTRALISED HERE. The volatility floor and
    the peg guard ride the VOLUME slot, and they are a standing rule, not part
    of what is under test, so this path must carry them exactly as run_combo3
    does. It did not on the first run with the floor on: the slot was set
    all-True, the no-name side had the floor on, and the check failed with
    MORE legs on the neutralised side (4568 vs 4030 for A/jack) -- the floor's
    own blocked entries, not a prepare side effect. Fixed 25 Nov 2026."""
    C1L, BASEL, C2L, VOLL, XL = N.families()
    RS = S2.RULESETS[rs]
    PL = N.PLANS[v]
    am, tp = float(PL['atr_mult']), float(PL['tp_mult'])
    _dist = (float(PL['max_atr_dist']) if (RS['dist'] and RS['side'])
             else float(N.BIG))
    kw = dict(use_continuation=False,
              one_candle_rule=bool(PL['one_candle_rule']),
              max_atr_dist=_dist, bridge_bars=N.BIG, block_suspect=True,
              bridge_all_routes=True, plan=2, atr_mult=am, tp_mult=tp,
              trail_mult=float(PL['trail_mult']),
              trail_start_mult=float(PL['trail_start_mult']),
              be_pct=float(PL['be_pct']), use_c1_flip=True,
              exit_on_c1_flip=True,
              use_base_cross=bool(RS['xentry'] and RS['side']),
              exit_on_base_cross=bool(RS['xexit'] and RS['side']),
              exit_on_exit_ind=False)
    params = {'atr_len': 14}
    for nm, st in ((c1, cs), (base, bs), (c2name, 'default')):
        pr = N.setting_params(nm, st)
        if pr:
            params[nm] = pr
    rows = []
    sides = (None,) if RS['side'] else ('long', 'short')
    for p in S.all_pairs():
        d = N.pair_data(p)
        for sd in sides:
            A = E.prepare(d, c1, c2name, VOLL[0], base, XL[0], params=params)
            n = A['c'].size
            T_ = np.ones(n, bool)
            A['c2_lc'] = T_.copy(); A['c2_sc'] = T_.copy()
            vm = T_.copy()
            if lowvol_q:
                _ix, _lv = VOL.lowvol_mask(p, q=lowvol_q, causal=True)
                assert len(_lv) == n, '%s: lowvol mask %d vs %d bars' % (
                    p, len(_lv), n)
                vm = vm & (~_lv)
            if peg_x:
                _ix2, _pg = VOL.peg_mask(p, x=peg_x)
                assert len(_pg) == n, '%s: peg mask %d vs %d bars' % (
                    p, len(_pg), n)
                vm = vm & (~_pg)
            A['v_ok_l'] = vm.copy(); A['v_ok_s'] = vm.copy()
            A['x_el'] = np.zeros(n, bool); A['x_es'] = np.zeros(n, bool)
            if not RS['side']:
                K = 10.0 * float(np.nanmax(np.abs(A['c'])) + 1.0)
                A['bl'] = A['c'] - K if sd == 'long' else A['c'] + K
            if use_hourly:
                import nnfxamb as _AMB
                res = E.run(A, amb=_AMB.amb_args(p), **kw)
            else:
                res = E.run(A, **kw)
            tf = E.trade_frame(res, d)
            if tf is None or not len(tf):
                continue
            tf = tf.copy(); tf['pair'] = p
            if sd == 'long':
                tf = tf[tf.direction == 'long']
            elif sd == 'short':
                tf = tf[tf.direction == 'short']
            if len(tf):
                rows.append(tf)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


# ==================== THE WALK-FORWARD C2 PICK ====================
def _yearly_of(T):
    T = T.reset_index(drop=True)
    cost = N._cost_R(T)
    DS = N.daily_series(T, cost)
    return N._yearly(T, cost, DS), DS, cost


def stage_walk3(use_hourly=True, verbose=True):
    """Pick the C2 SETTING walk-forward, on each step's own four tuning years.

    THE C1 AND BASELINE SETTINGS ARE NOT RE-PICKED. They are read from stage
    2's walk, which already chose them on these same tuning years. The only new
    choice in stage 3 is the C2, so it is the only thing tuned -- re-tuning the
    C1 against each C2 would change two things at once and the paired test
    would not be reading the C2.

    The objective is stage 2's, unchanged: tuning-year net R, at least 30
    trades in the tuning window.
    """
    f2 = os.path.join(OUT, 'stage2_picks_walk.csv')
    assert os.path.exists(f2), f2 + ' missing -- stage 2 must have run'
    W2 = pd.read_csv(f2)
    rows = []
    for (lab, c1, base, rs) in BASES:
        for v in PLANS_USED:
            w2 = W2[(W2.c1 == c1) & (W2.base == base)
                    & (W2.variant == v) & (W2.ruleset == rs)]
            if not len(w2):
                print('  !! no stage 2 walk for %s %s/%s' % (lab, v, rs),
                      flush=True)
                continue
            for (kind, nm, clab) in c2_candidates(c1):
                opts = list(SETTINGS) if kind == 'ind' else list(CCY_N)
                sc = {}
                for opt in opts:
                    _RUNC.clear()
                    for stp in STEPS:
                        r2 = w2[w2.step == stp['name']]
                        if not len(r2):
                            continue
                        cs = str(r2.iloc[0].picked_c1_setting)
                        bs = str(r2.iloc[0].picked_base_setting)
                        T = run_combo3(c1, cs, base, bs, v, rs,
                                       c2=(nm if kind == 'ind' else None),
                                       c2_set=(str(opt) if kind == 'ind'
                                               else 'default'),
                                       ccy_n=(int(opt) if kind == 'ccy'
                                              else None),
                                       use_hourly=use_hourly)
                        if not len(T):
                            continue
                        Y, _DS, _c = _yearly_of(T)
                        ty = list(range(stp['tune'][0], stp['tune'][1] + 1))
                        tn = Y[Y.year.isin(ty)]
                        tr = Y[Y.year == stp['trade']]
                        if not len(tn):
                            continue
                        sc[(stp['name'], opt)] = dict(
                            tune_R=float(tn.R_net.sum()),
                            tune_n=float(tn.n_entered.sum()),
                            trade_R_net=(float(tr.R_net.sum()) if len(tr)
                                         else np.nan),
                            trade_n=(float(tr.n_entered.sum()) if len(tr)
                                     else np.nan),
                            cs=cs, bs=bs)
                for stp in STEPS:
                    cand = [(o, sc[(stp['name'], o)]) for o in opts
                            if (stp['name'], o) in sc
                            and sc[(stp['name'], o)]['tune_n'] >= MIN_TRADES]
                    if not cand:
                        continue
                    o, best = max(cand, key=lambda kv: kv[1]['tune_R'])
                    rows.append(dict(
                        base=lab, c1=c1, baseline=base, ruleset=rs, variant=v,
                        c2_kind=kind, c2=(nm or ''), c2_label=clab,
                        step=stp['name'], trade_year=stp['trade'],
                        picked_c1_setting=best['cs'],
                        picked_base_setting=best['bs'],
                        picked_c2_opt=str(o),
                        n_options_eligible=len(cand), n_options_offered=len(opts),
                        tune_R=best['tune_R'], tune_n=best['tune_n'],
                        trade_R_net=best['trade_R_net'],
                        trade_n=best['trade_n'],
                        is_build=int(stp['trade'] in BUILD_YEARS),
                        is_confirm=int(stp['trade'] in CONFIRM_YEARS)))
                if verbose:
                    k = [r for r in rows if r['base'] == lab
                         and r['variant'] == v and r['c2_label'] == clab]
                    print('    walk3 %s/%s/%-20s: %d steps, picks %s'
                          % (lab, v, clab, len(k),
                             ','.join(str(r['picked_c2_opt']) for r in k)),
                          flush=True)
    W = pd.DataFrame(rows)
    f = os.path.join(OUT, 'stage3_walk.csv')
    S2._write_csv(W, f)
    if verbose:
        print('  stage 3 walk: %d candidate-steps, %d on BUILD years -> %s'
              % (len(W), int(W.is_build.sum()) if len(W) else 0,
                 os.path.relpath(f, _R)), flush=True)
    return f


# ==================== STITCH, SCORE, AND PAIR ====================
def _stitch3(c1, base, v, rs, kind, nm, W, years=BUILD_YEARS,
             use_hourly=True, with_c2=True):
    """The walk-forward stitched frame, each trade year on its own picks."""
    acc = []
    for stp in STEPS:
        if stp['trade'] not in years:
            continue
        w = W[(W.c1 == c1) & (W.ruleset == rs) & (W.variant == v)
              & (W.c2 == (nm or '')) & (W.step == stp['name'])]
        if not len(w):
            continue
        w = w.iloc[0]
        opt = str(w.picked_c2_opt)
        T = run_combo3(c1, str(w.picked_c1_setting), base,
                       str(w.picked_base_setting), v, rs,
                       c2=(nm if (with_c2 and kind == 'ind') else None),
                       c2_set=(opt if (with_c2 and kind == 'ind')
                               else 'default'),
                       ccy_n=(int(opt) if (with_c2 and kind == 'ccy')
                              else None),
                       use_hourly=use_hourly)
        if not len(T):
            continue
        T = T[pd.DatetimeIndex(T.exit_date).year == stp['trade']]
        if len(T):
            acc.append(T)
    return pd.concat(acc, ignore_index=True) if acc else pd.DataFrame()


def stage_report3(years=BUILD_YEARS, ndraw=400, nboot=2000, use_hourly=True,
                  verbose=True):
    """Every column Jack listed in stage 2, for each base WITH and WITHOUT each
    C2, plus the paired test on daily P&L.

    THE PAIRED TEST IS ON THE SAME DAYS. The two daily series are aligned on
    the UNION of their trading days, not the intersection -- a day on which
    only one of the two was in the market is a real difference and dropping it
    would hide exactly what the C2 does. Stage 2 did the same and said so.

    CONFIRM YEARS ARE COMPUTED AND WRITTEN AND SUMMARISED NOWHERE.
    """
    f = os.path.join(OUT, 'stage3_walk.csv')
    assert os.path.exists(f), f + ' missing -- run stage_walk3 first'
    W = _safe_csv_(f)
    # AN EMPTY CSV FIELD READS BACK AS NaN, NOT ''. The currency-agreement
    # candidate has no indicator name, so its 47 walk rows carry c2 = '' on
    # write and NaN on read, and every `W.c2 == ''` match came back all-False.
    # The first version of this stage then found no control for any of the six
    # base/plan cells, wrote 0 rows, and REPORTED OK in one second -- the same
    # shape of fault as B1_NARROW, caught here only because 108 engine runs
    # cannot finish in a second.
    if 'c2' in W.columns:
        W['c2'] = W.c2.fillna('').astype(str)
    W2 = pd.read_csv(os.path.join(OUT, 'stage2_picks_walk.csv'))
    S.load_costs(os.environ.get('FX_COST_TABLE', 'results/cost_table_h22.csv'))
    rows, pair_rows, yearly = [], [], []
    allyears = tuple(list(BUILD_YEARS) + list(CONFIRM_YEARS))
    for (lab, c1, base, rs) in BASES:
        for v in PLANS_USED:
            # ---- THE CONTROL: this base with NO C2, which is the stage 2
            # cell. It is built straight from STAGE 2's walk, not from stage
            # 3's: the C1 and baseline settings are stage 2's for every
            # candidate alike, so routing the control through a C2 candidate's
            # rows only creates a way for it to come back empty.
            _RUNC.clear()
            w2 = W2[(W2.c1 == c1) & (W2.base == base)
                    & (W2.variant == v) & (W2.ruleset == rs)]
            # THE SCORED FRAME HOLDS **BUILD YEARS ONLY**, and the all-years
            # frame is built separately for the yearly csv. Stitching all
            # eleven years and then filtering the DAILY SERIES to 2010-2015
            # keeps the pre-2016 marks of positions that CLOSED in 2016, which
            # inflated the control from 93.33 R to 100.59 R and silently used a
            # different window convention from stage 2 -- whose stage_report
            # stitches BUILD only. The marks are real and lag-clean; they are
            # simply not part of the BUILD result as stage 2 defined it, and a
            # paired figure compared against stage 2 has to be on stage 2's
            # convention.
            acc0, acc0_all = [], []
            for stp in STEPS:
                r2 = w2[w2.step == stp['name']]
                if not len(r2):
                    continue
                T_ = run_combo3(c1, str(r2.iloc[0].picked_c1_setting), base,
                                str(r2.iloc[0].picked_base_setting), v, rs,
                                use_hourly=use_hourly)
                if not len(T_):
                    continue
                Ty = T_[pd.DatetimeIndex(T_.exit_date).year == stp['trade']]
                if not len(Ty):
                    continue
                if stp['trade'] in allyears:
                    acc0_all.append(Ty)
                if stp['trade'] in years:
                    acc0.append(Ty)
            T0 = pd.concat(acc0, ignore_index=True) if acc0 else pd.DataFrame()
            T0_all = (pd.concat(acc0_all, ignore_index=True) if acc0_all
                      else pd.DataFrame())
            if not len(T0):
                print('  !! control empty for %s/%s -- no stage 2 walk rows'
                      % (lab, v), flush=True)
                continue
            sc0 = S2._score(T0, years, ndraw=ndraw, nboot=nboot)
            DS0 = sc0['_DS']
            rows.append(dict(base=lab, c1=c1, baseline=base, ruleset=rs,
                             variant=v, c2='(none)', c2_kind='control',
                             picked_c2_opts='', **{k: val
                                                   for k, val in sc0.items()
                                                   if not k.startswith('_')}))
            if len(T0_all):
                Y0, _d0, _c0 = _yearly_of(T0_all)
                yearly.append(Y0.assign(base=lab, variant=v, c2='(none)'))
            if verbose:
                print('    3c %s/%s/(none)      : %+8.2f R/yr, dip %7.2f, '
                      't_y %5.2f, t_b %6.2f, p %.3f'
                      % (lab, v, sc0['R_net_per_year'], sc0['worst_dip_R'],
                         sc0['t_yearly'], sc0['t_block_boot'], sc0['null_p']),
                      flush=True)
            for (kind, nm, clab) in c2_candidates(c1):
                _RUNC.clear()
                T1 = _stitch3(c1, base, v, rs, kind, nm, W, years=years,
                              use_hourly=use_hourly, with_c2=True)
                T1_all = _stitch3(c1, base, v, rs, kind, nm, W,
                                  years=allyears, use_hourly=use_hourly,
                                  with_c2=True)
                if not len(T1):
                    print('    3c %s/%s/%-20s: NO TRADES' % (lab, v, clab),
                          flush=True)
                    rows.append(dict(base=lab, c1=c1, baseline=base,
                                     ruleset=rs, variant=v, c2=clab,
                                     c2_kind=kind, picked_c2_opts='',
                                     n_entered=0.0))
                    continue
                sc1 = S2._score(T1, years, ndraw=ndraw, nboot=nboot)
                wsel = W[(W.c1 == c1) & (W.ruleset == rs) & (W.variant == v)
                         & (W.c2 == (nm or '')) & (W.is_build == 1)]
                opts = ','.join(str(x) for x in wsel.sort_values('trade_year')
                                .picked_c2_opt.tolist())
                rows.append(dict(base=lab, c1=c1, baseline=base, ruleset=rs,
                                 variant=v, c2=clab, c2_kind=kind,
                                 picked_c2_opts=opts,
                                 **{k: val for k, val in sc1.items()
                                    if not k.startswith('_')}))
                if len(T1_all):
                    Y1, _d1, _c1 = _yearly_of(T1_all)
                    yearly.append(Y1.assign(base=lab, variant=v, c2=clab))
                # ---- THE PAIRED TEST, same days, on the difference
                DS1 = sc1['_DS']
                pr = _paired_of(DS0, DS1, T0, T1, years, nboot=nboot)
                pr.update(base=lab, c1=c1, baseline=base, ruleset=rs,
                          variant=v, c2=clab, c2_kind=kind,
                          picked_c2_opts=opts)
                pair_rows.append(pr)
                if verbose:
                    print('    3c %s/%s/%-20s: %+8.2f R/yr, dip %7.2f, '
                          't_y %5.2f, t_b %6.2f, p %.3f | dR %+7.2f, '
                          'boot t %5.2f, yrs+ %d/%d, trades %+d'
                          % (lab, v, clab, sc1['R_net_per_year'],
                             sc1['worst_dip_R'], sc1['t_yearly'],
                             sc1['t_block_boot'], sc1['null_p'],
                             pr['dR_total'], pr['t_block_boot_diff'],
                             pr['years_diff_positive'], pr['years'],
                             int(pr['trades_removed'])), flush=True)
    R = pd.DataFrame(rows)
    P = pd.DataFrame(pair_rows)
    f1 = os.path.join(OUT, 'stage3_report.csv')
    f2 = os.path.join(OUT, 'stage3_paired.csv')
    f3 = os.path.join(OUT, 'stage3_yearly.csv')
    S2._write_csv(R, f1); S2._write_csv(P, f2)
    S2._write_csv(pd.concat(yearly, ignore_index=True) if yearly
                  else pd.DataFrame(), f3)
    if verbose:
        print('  stage 3 report: %d rows, %d paired rows -> %s'
              % (len(R), len(P), os.path.relpath(f1, _R)), flush=True)
    return f1, f2, f3


SNB_DAYS = (pd.Timestamp('2015-01-15'), pd.Timestamp('2015-01-16'))


def _snb_trade_present(T):
    """Does this frame hold the EURCHF short that spans the SNB day?"""
    if not len(T):
        return 0
    E = N.entry_frame(T)
    m = ((E.pair == 'EURCHF')
         & (pd.DatetimeIndex(E.entry_date) <= SNB_DAYS[0])
         & (pd.DatetimeIndex(E.exit_date) >= SNB_DAYS[0]))
    return int(m.sum())


def _paired_of(DS0, DS1, T0, T1, years, nboot=2000):
    """The difference series on the UNION of trading days, and its statistics.

    REPORTED TWICE, AND IT HAS TO BE. 15 January 2015 -- the Swiss National
    Bank abandoning the EURCHF floor -- is 56% to 137% of every carried-forward
    candidate's whole six-year result, and it is ONE TRADE: a EURCHF short
    worth +74.996 R. Measured on 24 Nov: of the five C2 candidates on base A,
    three DROP that trade and two KEEP it, and that single fact dominates every
    paired figure. `schaff_trend_cycle` as C2 shows dR -54.63 and looks
    destructive, but its SNB-free total is 41.82 R against the control's
    SNB-free 42.38 -- the same edge, without the windfall, which is why its
    yearly t is 6.10 and the control's is 1.73.

    So the ex-SNB columns are not a sensitivity check. On this data they are
    the ones that read the C2 rather than reading one gap.
    """
    a = DS0[pd.DatetimeIndex(DS0.date).year.isin(list(years))]
    b = DS1[pd.DatetimeIndex(DS1.date).year.isin(list(years))]
    m = (a.set_index('date').R.rename('r0')
         .to_frame()
         .join(b.set_index('date').R.rename('r1').to_frame(), how='outer')
         .fillna(0.0).sort_index())
    diff = (m.r1 - m.r0).to_numpy(float)
    t_d, sd_d = N._block_t(diff, ndraw=nboot)
    yr = pd.DatetimeIndex(m.index).year
    byyr = pd.DataFrame(dict(year=yr, d=diff)).groupby('year').d.sum()
    e0, e1 = N.n_entries(T0), N.n_entries(T1)
    # ---- the same thing with the two SNB days removed from both series
    keep = ~pd.DatetimeIndex(m.index).isin(SNB_DAYS)
    dx = diff[keep]
    tx, sdx = N._block_t(dx, ndraw=nboot)
    byyrx = (pd.DataFrame(dict(year=yr[keep], d=dx))
             .groupby('year').d.sum())
    return dict(days=int(len(m)), years=int(len(byyr)),
                R_without=float(m.r0.sum()), R_with=float(m.r1.sum()),
                dR_total=float(diff.sum()),
                dR_per_year=float(diff.sum() / max(1, len(byyr))),
                years_diff_positive=int((byyr > 0).sum()),
                t_block_boot_diff=float(t_d), boot_sd_diff=float(sd_d),
                snb_trade_kept=_snb_trade_present(T1),
                snb_trade_in_control=_snb_trade_present(T0),
                R_without_ex_snb=float(m.r0[keep].sum()),
                R_with_ex_snb=float(m.r1[keep].sum()),
                dR_total_ex_snb=float(dx.sum()),
                dR_per_year_ex_snb=float(dx.sum() / max(1, len(byyrx))),
                years_diff_positive_ex_snb=int((byyrx > 0).sum()),
                t_block_boot_diff_ex_snb=float(tx),
                trades_without=float(e0), trades_with=float(e1),
                trades_removed=float(e0 - e1),
                pct_trades_removed=(100.0 * (e0 - e1) / e0 if e0 else np.nan))


def _safe_csv_(p_):
    return S2._safe_csv(p_)


def _tbl(D, cols):
    return N._tbl(D, cols)


# ==================== STAGE 4 PREVIEW — THE VOLUME SLOT ====================
H1DIR = os.path.join(_R, 'data', 'oanda_h1')
VOL_LOOKBACKS = (10, 20, 50, 100, 250)
_VOLC = {}


def daily_tick_volume(pair):
    """Daily tick-tally per pair from data/oanda_h1, on that pair's own bars.

    `v` is a TICK COUNT, not traded size, and ENGINE_AUDIT_2.md measured it as
    a placeholder of 1 before 2005 and informative from 2005 on. The hourly
    stamps are UTC; the tally is summed by UTC date and then read onto the
    pair's daily index, so a day the daily file does not have is dropped
    rather than guessed.
    """
    if pair in _VOLC:
        return _VOLC[pair]
    f = os.path.join(H1DIR, '%s_bid.csv' % pair)
    d = N.pair_data(pair)
    ix = pd.DatetimeIndex(d.index)
    if not os.path.exists(f):
        _VOLC[pair] = (ix, np.full(len(ix), np.nan))
        return _VOLC[pair]
    h = pd.read_csv(f, parse_dates=['time'], usecols=['time', 'v'])
    day = pd.DatetimeIndex(h.time.dt.tz_convert('UTC').dt.date.astype(str))
    g = (pd.DataFrame(dict(date=day, v=h.v.to_numpy(float)))
         .groupby('date', as_index=False).v.sum())
    s = pd.Series(g.v.to_numpy(float),
                  index=pd.DatetimeIndex(g.date)).sort_index()
    vv = s.reindex(ix).to_numpy(float)
    _VOLC[pair] = (ix, vv)
    return _VOLC[pair]


def vol_mask_ticks(pair, lookback):
    """Candidate (a): the PREVIOUS day's tick tally above its own trailing
    median. The previous day, not the current one: the engine fills at the
    close and the project's rule is one-bar lag everywhere, so a rule that
    needs today's completed tally is not one this build will claim.

    Bars before the tally is informative (v == 1 placeholders, pre-2005) and
    bars with no tally are FALSE -- no opinion means no trade, never a free
    pass.
    """
    ix, vv = daily_tick_volume(pair)
    s = pd.Series(vv, index=ix)
    med = s.rolling(int(lookback), min_periods=int(lookback)).median()
    ok = (s > med) & (s > 1.0)
    out = np.zeros(len(ix), bool)
    o = ok.to_numpy(bool)
    out[1:] = o[:-1]                      # the explicit one-bar lag
    return out


_L1 = None


def layer1_activity(pair, levels=('medium', 'strong')):
    """Candidate (b): Layer 1 activity at medium or strong.

    layer1_states.csv states in its own header that "Rows are lagged one bar:
    a row dated D is built from bars <= D-1", so the file is ALREADY one-bar
    lagged and lagging it again here would charge the rule two bars. Bars with
    no Layer 1 row are FALSE.
    """
    global _L1
    if _L1 is None:
        f = os.path.join(ROOTOUT, 'layer1_states.csv')
        assert os.path.exists(f), f + ' missing'
        _L1 = pd.read_csv(f, comment='#', usecols=['date', 'pair', 'activity'],
                          parse_dates=['date'])
    d = N.pair_data(pair)
    ix = pd.DatetimeIndex(d.index)
    g = _L1[_L1.pair == pair]
    if not len(g):
        return np.zeros(len(ix), bool)
    s = pd.Series(g.activity.isin(list(levels)).to_numpy(bool),
                  index=pd.DatetimeIndex(g.date)).sort_index()
    s = s[~s.index.duplicated(keep='last')]
    # NO reindex+fillna: it raises a FutureWarning on an object column and the
    # chains run under -W error::FutureWarning.
    out = np.zeros(len(ix), bool)
    sel = pd.DatetimeIndex(s.index).get_indexer(ix)
    ok = sel >= 0
    out[ok] = s.to_numpy(bool)[sel[ok]]
    return out


def stage4_preview(years=BUILD_YEARS, nboot=2000, use_hourly=True,
                   verbose=True):
    """The same paired design as stage 3, on A, B and C WITHOUT any C2, with
    the VOLUME slot filled. Two candidates only, as Jack declared them.

    The lookback is picked walk-forward for candidate (a), on each step's own
    four tuning years, same objective as everywhere else: tuning-year net R,
    at least 30 trades. Candidate (b) has nothing to pick.
    """
    f2 = os.path.join(OUT, 'stage2_picks_walk.csv')
    W2 = pd.read_csv(f2)
    S.load_costs(os.environ.get('FX_COST_TABLE', 'results/cost_table_h22.csv'))
    rows, pick_rows = [], []
    allyears = tuple(list(BUILD_YEARS) + list(CONFIRM_YEARS))
    RULES = (('ticks_above_trailing_median', VOL_LOOKBACKS),
             ('layer1_activity_med_or_strong', (0,)))
    for (lab, c1, base, rs) in BASES:
        for v in PLANS_USED:
            w2 = W2[(W2.c1 == c1) & (W2.base == base)
                    & (W2.variant == v) & (W2.ruleset == rs)]
            if not len(w2):
                continue
            steps = [(stp, str(w2[w2.step == stp['name']].iloc[0]
                               .picked_c1_setting),
                      str(w2[w2.step == stp['name']].iloc[0]
                          .picked_base_setting))
                     for stp in STEPS if len(w2[w2.step == stp['name']])]
            # ---- the control: no volume rule, no C2
            _RUNC.clear()
            acc = []
            for (stp, cs, bs) in steps:
                T = run_combo3(c1, cs, base, bs, v, rs,
                               use_hourly=use_hourly)
                if len(T):
                    acc.append(T[pd.DatetimeIndex(T.exit_date).year
                                 == stp['trade']])
            T0 = pd.concat(acc, ignore_index=True) if acc else pd.DataFrame()
            if not len(T0):
                continue
            Y0, DS0, _c0 = _yearly_of(T0)
            for (rule, opts) in RULES:
                # ---- walk-forward pick of the lookback
                acc1, picked = [], []
                for (stp, cs, bs) in steps:
                    best = None
                    for o in opts:
                        _RUNC.clear()
                        T = run_combo3(c1, cs, base, bs, v, rs,
                                       vol_rule=rule, vol_opt=o,
                                       use_hourly=use_hourly)
                        if not len(T):
                            continue
                        Y, _d, _c = _yearly_of(T)
                        ty = list(range(stp['tune'][0], stp['tune'][1] + 1))
                        tn = Y[Y.year.isin(ty)]
                        if not len(tn) or float(tn.n_entered.sum()) < MIN_TRADES:
                            continue
                        sc_ = float(tn.R_net.sum())
                        if best is None or sc_ > best[0]:
                            best = (sc_, o, T)
                    if best is None:
                        continue
                    picked.append((stp['trade'], best[1]))
                    acc1.append(best[2][pd.DatetimeIndex(best[2].exit_date).year
                                        == stp['trade']])
                T1 = pd.concat(acc1, ignore_index=True) if acc1 else pd.DataFrame()
                if not len(T1):
                    if verbose:
                        print('    4 %s/%s/%-32s: NO TRADES' % (lab, v, rule),
                              flush=True)
                    continue
                Y1, DS1, _c1 = _yearly_of(T1)
                pr = _paired_of(DS0, DS1, T0, T1, years, nboot=nboot)
                pr.update(base=lab, c1=c1, baseline=base, ruleset=rs,
                          variant=v, vol_rule=rule,
                          picked_opts=','.join(
                              '%d:%s' % (y, o) for y, o in picked
                              if y in BUILD_YEARS))
                rows.append(pr)
                for (y, o) in picked:
                    pick_rows.append(dict(base=lab, variant=v, vol_rule=rule,
                                          trade_year=y, picked_lookback=o,
                                          is_build=int(y in BUILD_YEARS)))
                if verbose:
                    print('    4 %s/%s/%-32s: dR %+8.2f (%+6.2f/yr), boot t '
                          '%5.2f, yrs+ %d/%d, trades %d -> %d (%.1f%% cut)'
                          % (lab, v, rule, pr['dR_total'], pr['dR_per_year'],
                             pr['t_block_boot_diff'],
                             pr['years_diff_positive'], pr['years'],
                             int(pr['trades_without']), int(pr['trades_with']),
                             pr['pct_trades_removed']), flush=True)
    D = pd.DataFrame(rows)
    S2._write_csv(D, os.path.join(OUT, 'stage4_paired.csv'))
    S2._write_csv(pd.DataFrame(pick_rows),
                  os.path.join(OUT, 'stage4_picks.csv'))
    if verbose:
        print('  stage 4 preview: %d paired rows' % len(D), flush=True)
    return D


def md_stage3(out=None):
    """results/nnfx/STAGE3.md"""
    L_ = []; a = L_.append
    R = S2._safe_csv(os.path.join(OUT, 'stage3_report.csv'))
    P = S2._safe_csv(os.path.join(OUT, 'stage3_paired.csv'))
    W = S2._safe_csv(os.path.join(OUT, 'stage3_walk.csv'))
    Z = S2._safe_csv(os.path.join(OUT, 'stage3_zeroedge.csv'))
    S4 = S2._safe_csv(os.path.join(OUT, 'stage4_paired.csv'))
    a('# Stage 3 — a second confirmation added to the carried-forward three\n')
    a('Generated by `code/nnfx3.py` on %s. Every number in this file is read '
      'from a csv in `results/nnfx/`; none is typed in.\n'
      % time.strftime('%F %H:%M'))

    a('\n## What Jack carried forward, and why\n')
    a('These three came out of stage 2. The reason is his, recorded in the '
      'ledger: **the largest paired improvement from adding the baseline, '
      'positive in most unseen years.**\n')
    a('\n| | C1 | baseline | ruleset |')
    a('|---|---|---|---|')
    for (lab, c1, base, rs) in BASES:
        a('| **%s** | %s | %s | `%s` |'
          % (lab, S2._short(c1, '_signals'), S2._short(base, '_baseline'), rs))
    a('\n`jack` is the main plan; `textbook` is reported beside it. Unseen '
      'trade years **2010–2015** are the evidence. 2016–2020 are computed and '
      'written to `stage3_yearly.csv` and are summarised nowhere in this file. '
      '2021 onward is not read.\n')

    a('\n> **READ THIS FIRST: ONE DAY CARRIES THESE CANDIDATES.** Checking '
      'Jack\'s dip question found that **15 January 2015, the Swiss National '
      'Bank abandoning the EURCHF floor, is 56% to 137% of each carried-'
      'forward candidate\'s entire six-year result** — a single short EURCHF '
      'entered 2 January and closed 16 January, worth **+74.996 R** against a '
      'six-year total of 91.64 R for candidate A on the jack plan. Four of the '
      'six base/plan combinations are **negative over 2010–2015 without that '
      'one day**. Nothing in stage 3 changes that, because stage 3 tests what '
      'a C2 adds to these bases, not whether the bases are sound. '
      'See `dipcheck_snb_dependence.csv` and the engine-fix note below.\n')

    a('\n## The engine fault this stage is built on top of\n')
    a('`nnfx1.daily_series` built every leg\'s mark-to-market from the FULL '
      'position size, while a `plan=2` leg realises half — a full stop-out is '
      '−0.5 + −0.5. Open mark-to-market was therefore overstated by the leg '
      'count. It **cancelled at the exit bar**, so every total reconciled to '
      'the last decimal and nothing caught it. What was wrong: `worst_dip_R` '
      '(too large), `R_per_year_per_dip` (too small) and `t_block_boot` '
      '(biased **down**, from inflated daily variance). Every figure in this '
      'file is on the fixed engine, which pre-flight guard 36 pins.\n')

    a('\n## The zero-edge check\n')
    a('Stage 2 neutralised the C2 slot by overwriting `c2_lc`/`c2_sc` after '
      '`prepare`. Stage 3 instead hands `prepare` a real C2 name. If the slot '
      'is genuinely the only difference, naming a C2 and then overwriting its '
      'arrays all-True must give **the same trades** as never naming one. If '
      'it does not, `prepare` does something else with the name and every '
      'paired number here would be measuring that instead.\n')
    if len(Z):
        a(_tbl(Z, ['base', 'c1', 'ruleset', 'variant', 'legs_no_name',
                   'legs_named_neutral', 'identical', 'abs_dR',
                   'legs_real_c2']))
        okz = bool((Z.identical == 1).all()) and float(Z.abs_dR.max()) < 1e-9
        a('\n**%s** — %d cells, worst |ΔR| %.3e.%s\n'
          % ('PASS' if okz else 'FAIL', len(Z), float(Z.abs_dR.max()),
             '' if okz else ' NO PAIRED FIGURE BELOW MAY BE QUOTED.'))
    else:
        a('_not run_\n')

    a('\n## The five C2 candidates, declared before anything ran\n')
    a('| # | candidate | what it is |')
    a('|---|---|---|')
    a('| 1–2 | the other two C1 picks | each of Jack\'s three C1 used as the '
      'C2 of the other two, so the pair differs by base |')
    a('| 3 | kalman_filter | the next most stable in stage 1 |')
    a('| 4 | dspo | the same |')
    a('| 5 | **currency agreement**, N swept 3–6 | take the trade only if the '
      'base currency is rising against at least N of its other six partners '
      'AND the quote currency is falling against at least N of its other six, '
      'measured by **the same C1** on those pairs, **one-bar lag** |')
    a('\nThe currency rule is not an indicator, so it occupies the C2 slot as '
      'a **rule**: the counts are computed across all 28 pairs on a union '
      'calendar — a partner with no bar that day counts as no opinion, not as '
      'agreement — then lagged one bar and written into the same two arrays '
      'the engine reads. The lag is explicit and is not left to the engine\'s '
      'own convention.\n')

    a('\n### How often the currency rule agrees at all\n')
    a('Measured on the raw counts, before any trading. This is the thing to '
      'read before reading N = 5 or 6 as a result:\n')
    rws = []
    for c1 in C1_PICKS:
        CC = ccy_counts(c1, 'default')
        for n_ in CCY_N:
            al = []; ash = []
            for p, dd in CC.items():
                al.append(float(((dd['nb_up'] >= n_)
                                 & (dd['nq_dn'] >= n_)).mean()))
                ash.append(float(((dd['nb_dn'] >= n_)
                                  & (dd['nq_up'] >= n_)).mean()))
            rws.append(dict(c1=S2._short(c1, '_signals'), N=n_,
                            pct_bars_agree_long=100.0 * float(np.mean(al)),
                            pct_bars_agree_short=100.0 * float(np.mean(ash))))
    AG = pd.DataFrame(rws)
    S2._write_csv(AG, os.path.join(OUT, 'stage3_ccy_agreement_rate.csv'))
    a(_tbl(AG, list(AG.columns)))
    a('\nAt the top of the sweep the rule almost never fires, so a candidate '
      'that picks N = 6 is trading a handful of days and its figures are not '
      'comparable to the rest. The walk-forward pick needs 30 trades in the '
      'tuning window, which is what keeps that from being chosen by accident.\n')

    a('\n## 3a — THE PAIRED TEST: what each C2 adds\n')
    a('The two daily series are aligned on the **union** of their trading '
      'days, not the intersection: a day on which only one of the two was in '
      'the market is a real difference, and dropping it would hide exactly '
      'what the C2 does. Stage 2 did the same.\n')
    if len(P):
        a('\n> **THE PAIRED NUMBER IS DOMINATED BY ONE TRADE, SO IT IS GIVEN '
          'TWICE.** 15 January 2015 is 56%–137% of each of these bases over '
          '2010–2015, and it is a single EURCHF short worth **+74.996 R**. Of '
          'the five C2 on base A, **three drop that trade and two keep it**, '
          'and which side a candidate falls on swamps everything else it does. '
          '`schaff_trend_cycle` shows ΔR −54.63 and looks destructive; its '
          'SNB-free total is **41.82 R against the control\'s SNB-free '
          '42.38** — the same edge without the windfall, which is why its '
          'yearly t is 6.10 where the control\'s is 1.73. The `_ex_snb` '
          'columns are not a sensitivity check on this data: they are the ones '
          'that read the C2 instead of reading one gap.\n')
        pc = ['base', 'variant', 'c2', 'picked_c2_opts', 'snb_trade_kept',
              'R_without', 'R_with', 'dR_total', 'dR_per_year',
              'years_diff_positive', 'years', 't_block_boot_diff',
              'trades_without', 'trades_with', 'pct_trades_removed', 'days']
        px = ['base', 'variant', 'c2', 'snb_trade_kept', 'R_without_ex_snb',
              'R_with_ex_snb', 'dR_total_ex_snb', 'dR_per_year_ex_snb',
              'years_diff_positive_ex_snb', 't_block_boot_diff_ex_snb']
        for v in PLANS_USED:
            d = P[P.variant == v]
            if not len(d):
                continue
            a('\n### %s plan — as measured\n' % v)
            a(_tbl(d.sort_values(['base', 'dR_per_year'],
                                 ascending=[True, False]), pc))
            a('\n### %s plan — the same, with 15–16 January 2015 removed from '
              'both series\n' % v)
            a(_tbl(d.sort_values(['base', 'dR_per_year_ex_snb'],
                                 ascending=[True, False]),
                   [c for c in px if c in d.columns]))
        jm = P[P.variant == MAIN_PLAN]
        if len(jm):
            npos = int((jm.dR_per_year > 0).sum())
            nsig = int((jm.t_block_boot_diff.abs() >= 2.0).sum())
            a('\n**On the main plan, %d of %d base-by-C2 combinations improve '
              'R per year at all, and %d reach |bootstrap t| ≥ 2.**'
              % (npos, len(jm), nsig))
            if 'dR_per_year_ex_snb' in jm.columns:
                npx = int((jm.dR_per_year_ex_snb > 0).sum())
                nsx = int((jm.t_block_boot_diff_ex_snb.abs() >= 2.0).sum())
                a(' **With the two SNB days removed: %d of %d improve and %d '
                  'reach |t| ≥ 2.**' % (npx, len(jm), nsx))
            bst = jm.loc[jm.dR_per_year.idxmax()]
            a(' The largest improvement is **%s on base %s, %+.2f R per year** '
              '(bootstrap t %.2f, %d of %d years positive, %.1f%% of trades '
              'removed).\n'
              % (bst.c2, bst.base, bst.dR_per_year, bst.t_block_boot_diff,
                 int(bst.years_diff_positive), int(bst.years),
                 bst.pct_trades_removed))
    else:
        a('_not computed_\n')

    a('\n## 3b — THE FULL TABLE, with and without each C2\n')
    a('Every column stage 2 reported, on the unseen years, through the same '
      'scorer. `(none)` is the base as stage 2 left it.\n')
    if len(R):
        qc = ['base', 'variant', 'c2', 'picked_c2_opts', 'n_entered',
              'trades_per_year', 'R_gross_per_trade', 'R_net_per_trade',
              'R_net_per_year', 'years_positive', 'worst_year',
              'worst_dip_R', 'R_per_year_per_dip', 't_yearly',
              't_block_boot', 'null_p', 'floor_t_alone', 'clears_alone']
        qc = [c for c in qc if c in R.columns]
        for v in PLANS_USED:
            d = R[R.variant == v]
            if not len(d):
                continue
            a('\n### %s plan\n' % v)
            a(_tbl(d.sort_values(['base', 'c2']), qc))
        if 'clears_alone' in R.columns:
            nc = int(pd.to_numeric(R.clears_alone, errors='coerce')
                     .fillna(0).sum())
            np_ = int((pd.to_numeric(R.get('null_p'), errors='coerce')
                       <= 0.05).sum())
            a('\n**%d of %d rows clear the alone floor and %d have null p ≤ '
              '0.05.**\n' % (nc, len(R), np_))
    else:
        a('_not computed_\n')

    a('\n## 3c — which C2 setting each step picked\n')
    a('The C2 setting is picked on each step\'s own four tuning years, on '
      'tuning-year net R with at least %d trades. The C1 and baseline '
      'settings are **not** re-picked: they are stage 2\'s, chosen on these '
      'same windows, so the only thing tuned in stage 3 is the C2.\n'
      % MIN_TRADES)
    if len(W):
        wb = W[W.is_build == 1]
        a(_tbl(wb.sort_values(['base', 'variant', 'c2_label', 'trade_year']),
               ['base', 'variant', 'c2_label', 'trade_year',
                'picked_c1_setting', 'picked_base_setting', 'picked_c2_opt',
                'n_options_eligible', 'n_options_offered', 'tune_R', 'tune_n',
                'trade_R_net', 'trade_n']))
    else:
        a('_not computed_\n')

    a('\n## Stage 4 preview — the volume slot\n')
    a('Same paired design, on A, B and C **without** any C2. Two candidates '
      'only, as declared: **(a) real tick volume** from `data/oanda_h1`, '
      'usable from 2005 per `ENGINE_AUDIT_2.md` — trade only when the day\'s '
      'volume is above its own trailing median, lookback swept; and **(b) '
      'Layer 1 activity** medium or strong, one-bar lag.\n')
    if len(S4):
        a(_tbl(S4.sort_values(['base', 'variant', 'vol_rule']),
               [c for c in ['base', 'variant', 'vol_rule', 'picked_opts',
                            'dR_total', 'dR_per_year', 'years_diff_positive',
                            'years', 't_block_boot_diff', 'trades_without',
                            'trades_with', 'pct_trades_removed']
                if c in S4.columns]))
    else:
        a('_not run yet — stage 4 is a preview in this file and its own stage '
          'when Jack calls it._\n')

    a('\n## What is sealed\n')
    a('- 2016–2020 are computed and stored in `stage3_yearly.csv` and are '
      'summarised nowhere in this file.\n')
    a('- 2021 onward is not read.\n')
    a('- The C2 setting is the only thing tuned here; the C1 and baseline '
      'settings come from stage 2\'s walk unchanged.\n')

    a('\n## Provenance\n')
    a('Every file this stage is supposed to produce is listed, **including any '
      'that came back empty**. Pre-flight guard 35 reads these lines and fails '
      'on a zero-row file — but it can only check what the report declares, '
      'and the first version of this block SKIPPED empty files, which is how a '
      'report with 0 rows in it passed pre-flight. It does not skip them now.\n')
    import hashlib
    for n_ in ('stage3_zeroedge.csv', 'stage3_walk.csv', 'stage3_report.csv',
               'stage3_paired.csv', 'stage3_yearly.csv',
               'stage3_ccy_agreement_rate.csv', 'stage4_paired.csv',
               'stage4_picks.csv'):
        p_ = os.path.join(OUT, n_)
        if not os.path.exists(p_):
            a('- `%s` — **MISSING**' % os.path.join('results', 'nnfx', n_))
            continue
        a('- `%s` — %s rows, md5 `%s`'
          % (os.path.relpath(p_, _R),
             '{:,}'.format(len(S2._safe_csv(p_))),
             hashlib.md5(open(p_, 'rb').read()).hexdigest()[:12]))
    out = out or os.path.join(OUT, 'STAGE3.md')
    open(out, 'w').write('\n'.join(L_) + '\n')
    print('  STAGE3.md: %d lines -> %s'
          % (len('\n'.join(L_).splitlines()), os.path.relpath(out, _R)),
          flush=True)
    return out


if __name__ == '__main__':
    st = G.opt('--stage', str, 'zeroedge')
    hourly = not bool(G.opt('--no-hourly', int, 0))
    if st == 'zeroedge':
        _D, _ok = condition_c2_neutral(use_hourly=hourly)
        if not _ok:
            raise SystemExit('ZERO-EDGE CHECK FAILED -- naming a C2 and then '
                             'neutralising it changed the trades, so prepare '
                             'does more with the name than fill the slot and '
                             'no paired number in stage 3 means what it says')
    elif st == 'ccy':
        for _c1 in C1_PICKS:
            for _st in SETTINGS:
                ccy_counts(_c1, _st)
        print('  currency-agreement counts cached for %d (c1, setting) pairs'
              % (len(C1_PICKS) * len(SETTINGS)), flush=True)
    elif st == 'walk':
        stage_walk3(use_hourly=hourly)
    elif st == 'report':
        stage_report3(use_hourly=hourly)
    elif st == 'ledger':
        for (lab, c1, base, rs) in BASES:
            N.ledger_add('stage3', 'c2',
                         [x[2] for x in c2_candidates(c1)],
                         len(SETTINGS) * 4 + len(CCY_N),
                         "Jack's carry-forward %s = %s + %s, %s: largest "
                         "paired improvement from adding the baseline, "
                         "positive in most unseen years"
                         % (lab, S2._short(c1, '_signals'),
                            S2._short(base, '_baseline'), rs),
                         '2010-2015 unseen, 2016-2020 computed and sealed',
                         'stage 3, second confirmation')
    elif st == 'stage4':
        stage4_preview(use_hourly=hourly)
    elif st == 'md':
        md_stage3()
    else:
        raise SystemExit('unknown stage %s' % st)
