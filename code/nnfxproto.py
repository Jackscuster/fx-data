import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""THE PROTOCOL — one fixed test for a complete NNFX algorithm. HANDOFF 0o.

results/nnfx/PROTOCOL.md is the declaration; this file is its ONE
implementation. Sources 1, 2 and 3 all call it. Nothing here chooses a
candidate; it scores whatever it is handed and says pass or fail on four gates.

WHAT IS DIFFERENT FROM EVERY EARLIER STAGE, AND WHY THEIR NUMBERS DO NOT
TRANSFER. Stage 1 neutralised four of the five slots to isolate one. Stage 2
neutralised C2, volume and the exit indicator to isolate the baseline. Both
were deliberate and both were therefore tests of a PIECE. Here all five slots
carry a real indicator and all three exits are live, which is a different
object: on candidate A's own C1/baseline pair the trade count moves by more
than a factor of two once C2 and volume actually gate. So no stage-1 or
stage-2 figure is quoted as evidence about a candidate in this file.

NO LAYER 1. Nothing in this module reads a regime, a state or a label. Jack
removed Layer 1 from Layer 2 on 25 Nov; the only non-indicator entry gates are
his own two standing rules (the 5% per-pair floor and the 0.33 peg guard),
and both of them are measured off the pair's own ATR and the 28-pair median,
never off a classifier.

THE THREE ENTRY GATES COMPOSE AS AN AND, NOT AN OVERRIDE. The volume slot is
now a REAL indicator, and the floor and the peg guard ride the same two arrays
(v_ok_l / v_ok_s) because those appear only in the engine's entry conditions.
So the slot carries `volume_indicator & ~floor & ~peg`. Using `suspect`
instead would also freeze exits, which no rule here says.

FAULTS THIS FILE FOUND IN ITSELF
  1. The first version of `_assemble` cached the five slot arrays per
     (pair, name) and forgot the PARAMS in the key, so every candidate sharing
     an indicator at a different setting silently got the first setting that
     had been computed. Caught because the three settings of N5's Aroon gave
     byte-identical trade counts. The key is now (pair, name, sorted params).
  2. `fast_obj` first charged cost per LEG from `units`, which is the full
     position size written identically on both legs of a plan-2 entry -- the
     same factor-of-two the daily series carries a long comment about. It made
     the fast objective too NEGATIVE by one whole spread per trade. The charge
     is now per leg on units/n_legs, and `verify_fast` checks the fast total
     against the UNCAPPED full path's realised net R over the same years to
     1e-6. It is not checked against the reported figure, because the reported
     figure is capped and mark-to-market and is a different number on purpose.
  3. THE COST CHARGE IN EVERY NNFX-PHASE TABLE IS EXACTLY TWICE THE MEASURED
     SPREAD, and this file is where that was found. `l2engine.run` defaults
     `risk_dollars=200.0`; every nnfx* caller takes that default, so R is
     (price move x units) / 200 -- verified on 80 stop exits, where
     move x units / 200 reproduces the booked -0.5 to 0.0 and move x units /
     100 gives -1.0. But `nnfx1._cost_R` divides by `l2sweep.RISK`, which is
     100. The GAUNTLET path is not affected: `l2sweep.run_combo` passes RISK
     as risk_dollars, so its engine and its cost divisor are the same number.
     Only the nnfx path mixes the two. The error is a clean factor of 2 in the
     PESSIMISTIC direction on every net figure of stage 1, 2 and 3 and items
     1 to 6; `results/nnfx/COST_DOUBLE_CHARGE.md` names the tables and gives
     the mechanical correction. This module charges `cost_R`, which divides by
     the engine's actual RISK_DOLLARS, and `verify_fast` is what caught it:
     the fast path (which happened to divide by units/n_legs and so was
     right) and the full path disagreed by exactly the cost, per candidate.
  4. G3's currency splits first RE-RAN the engine per subset, which re-ran the
     leverage cap on 15 pairs instead of 28 and made every split look better
     than the book it came from. The cap is portfolio-wide, so the split is
     taken from the WHOLE 28-pair capped frame, which is the same rule item 3
     adopted for the per-pair bank.
"""
import time, json, hashlib, itertools, inspect
import numpy as np, pandas as pd
from scipy import stats

import l2lib as L
import l2sweep as S
import l2engine as E
import nnfx1 as N
import nnfxvol as VOL
import nnfxamb as AMB
import r2reads as RR

OUT = os.path.join(ROOTOUT, 'nnfx')
os.makedirs(OUT, exist_ok=True)
LEDGER = os.path.join(OUT, 'CANDIDATE_LEDGER.csv')
PROTO_LEDGER = os.path.join(OUT, 'proto_ledger.csv')

RISK_UNIT_ATR = N.RISK_UNIT_ATR          # 1.5; every R here is per 1.5 ATR
# THE ENGINE'S RISK DENOMINATOR, STATED RATHER THAN DEFAULTED. l2engine.run's
# default is 200.0 and every nnfx* caller takes it, which is what made
# nnfx1._cost_R (which divides by l2sweep.RISK = 100) charge twice the spread.
# It is passed explicitly on every call here so the cost divisor and the engine
# can never drift apart again. Changing it would also change what the 1:30
# leverage cap binds on, because nnfxvol's EQUITY was calibrated against 200.
RISK_DOLLARS = 200.0
EVIDENCE = tuple(range(2005, 2016))      # all eleven unseen: nothing is tuned
CONFIRM = tuple(range(2016, 2021))       # computed, stored, NOT reported
HALF_A = tuple(range(2005, 2011))
HALF_B = tuple(range(2011, 2016))
SETTINGS = ('half', 'default', 'double')
SET_MULT = {'half': 0.5, 'default': 1.0, 'double': 2.0}

# ---- JACK'S RISK PLAN, FIXED. PROTOCOL.md section 1.
RISK = dict(plan=2, atr_mult=1.0, tp_mult=1.5, max_atr_dist=1.5,
            bridge_bars=7, use_continuation=True, one_candle_rule=False,
            trail_mult=1.5, trail_start_mult=2.0, be_pct=0.05,
            atr_len=14, time_stop_bars=0)
# all three exits live, and the three entry routes the plan implies
RULES = dict(use_base_cross=True, use_c1_flip=True,
             exit_on_c1_flip=True, exit_on_base_cross=True,
             exit_on_exit_ind=True,
             block_suspect=True, bridge_all_routes=True)
LOWVOL_Q = N.LOWVOL_Q                    # 0.05, Jack's rule 1
# THE PEG GUARD'S REFERENCE UNIVERSE. Empty means all 28 pairs, which is what
# the rule says: the median is taken across the whole panel, not across the
# subset a particular run happens to trade. A synthetic world built on fewer
# pairs must say so, because a median over 15 pairs is a different number.
PEG_PAIRS = []
PEG_X = VOL.PEG_X_DECIDED                # 0.33, decided 25 Nov

# ---- G3's three currency splits, PROTOCOL.md section 4
SPLITS = (('JPY', 'CHF'), ('AUD', 'NZD'), ('GBP', 'CAD'))

# ---- G4's nudge grid, PROTOCOL.md section 4. Deliberately coarse.
NUDGE_RISK = {'atr_len': (7, 28), 'atr_mult': (0.75, 1.25),
              'tp_mult': (1.0, 2.0), 'max_atr_dist': (1.0, 2.0),
              'bridge_bars': (5, 9)}


# ======================= the slot inventory =============================
def inventory():
    """-> {slot: tuple of available indicator names}, from the REGISTRY.

    NOT from l2sweep.mode_opts. Mode 'A' lists ONE exit helper (adx_dmi_exit)
    because that is what mode A was built to sweep; the library carries 39
    available ones, and PROTOCOL.md's five-slot candidate needs all of them.
    `kijun_baseline` is in here because it was added on 25 Nov for N1.
    """
    av = lambda sl: tuple(sorted(k for k, v in L.REGISTRY.items()
                                 if v['slot'] == sl and k not in L.UNAVAILABLE))
    conf = av('confirmation')
    return dict(c1=conf, c2=conf, vol=av('volume'), base=av('baseline'),
                exit=av('exit'))


INV = inventory()
SLOTS = ('c1', 'c2', 'vol', 'base', 'exit')


# ======================= settings and nudges ============================
def knob_names(name):
    """The numeric knob(s) the project's standing ladder scales for `name`."""
    return list(N.length_params(name).keys())


def scaled_params(name, mult, base=None):
    """`base` (or the Pine defaults) with the length knob scaled by `mult`.

    THE FIVE SMOOTHING-CONSTANT INDICATORS GO THE OTHER WAY. For
    ehlers_reverse_ema, kalman_filter, laguerre_filter, mama_fama and
    parabolic_sar a LARGER constant is a SHORTER memory, so a mult of 2
    (double the memory) HALVES the constant. This is the same inversion
    nnfx1.setting_params carries, written once here so a nudge and a setting
    cannot disagree about which way round it is.
    """
    lp = N.length_params(name)
    if not lp or abs(mult - 1.0) < 1e-12:
        return dict(base or {})
    out = dict(base or {})
    inv = name in N.FLOAT_SHORTER_IS_BIGGER
    for k, dflt in lp.items():
        start = (base or {}).get(k, dflt)
        if inv:
            out[k] = float(start) / float(mult)
        elif isinstance(dflt, int) and not isinstance(dflt, bool):
            out[k] = max(2, int(round(float(start) * float(mult))))
        else:
            out[k] = float(start) * float(mult)
    return out


def setting_params(name, which, base=None):
    """half / default / double, or 'published' which means `base` unchanged."""
    if which == 'published':
        return dict(base or {})
    return scaled_params(name, SET_MULT[which], base)


# ======================= a candidate ====================================
def cand(name, c1, c2, vol, base, exitind, source='',
         c1_set='default', c2_set='default', vol_set='default',
         base_set='default', exit_set='default', reason='',
         params=None, risk=None):
    """One complete algorithm, fully declared. `params` holds PUBLISHED
    settings per slot name, used when the setting label is 'published'."""
    params = params or {}
    C = dict(name=name, source=source, reason=reason,
             c1=c1, c2=c2, vol=vol, base=base, exit=exitind,
             c1_set=c1_set, c2_set=c2_set, vol_set=vol_set,
             base_set=base_set, exit_set=exit_set,
             risk=dict(RISK, **(risk or {})))
    for sl in SLOTS:
        nm = C[sl]
        C[sl + '_params'] = setting_params(nm, C[sl + '_set'], params.get(nm))
    return C


def cand_id(C):
    """A stable hash of everything that can change a number."""
    key = json.dumps([[C[s], C[s + '_set'],
                       sorted((k, float(v)) for k, v in C[s + '_params'].items()
                              if isinstance(v, (int, float))
                              and not isinstance(v, bool))]
                      for s in SLOTS]
                     + [sorted(C['risk'].items())], sort_keys=True)
    return hashlib.md5(key.encode()).hexdigest()[:12]


def cand_label(C):
    return ' | '.join('%s %s/%s' % (s.upper(), C[s].replace('_signals', '')
                                    .replace('_baseline', '')
                                    .replace('_volume', '')
                                    .replace('_exit', ''), C[s + '_set'])
                      for s in SLOTS)


# ======================= per-pair array cache ===========================
_DATA = {}
_SLOT = {}
_MASK = {}
_ATR = {}
_ORD = {}
_PANEL = {}

# ---- THE WORLD. 'real' is the market; anything else is a synthetic frame set
# supplied by Source 3's search null. EVERY cache below is keyed on it, so a
# null run cannot read a real-world array and a real run cannot read a null
# one. Getting this wrong would not raise -- it would quietly return the real
# market's indicators for a shuffled price series, which is the single most
# dangerous bug a search null can have, so the key is in every cache and
# `set_world` asserts the tag it is handed.
WORLD = 'real'
_FRAMES = {}


def set_world(tag, frames=None):
    """Switch the data source. tag='real' restores N.pair_data."""
    global WORLD
    assert isinstance(tag, str) and tag, 'world tag must be a non-empty string'
    if tag != 'real':
        assert frames, 'a synthetic world needs its frames'
        for k, v in frames.items():
            _FRAMES[(tag, k)] = v
    WORLD = tag
    return WORLD


def drop_world(tag):
    """Free a null run's frames and every cache keyed on it."""
    assert tag != 'real', 'the real world is not dropped'
    for d in (_DATA, _SLOT, _MASK, _ATR, _BASE, _PANEL, _FRAMES):
        for k in [k for k in d if isinstance(k, tuple) and k and k[0] == tag]:
            del d[k]
    for k in [k for k in _FAST if k and k[0] == tag]:
        del _FAST[k]


def pair_data(p):
    k = (WORLD, p)
    if k not in _DATA:
        _DATA[k] = (N.pair_data(p) if WORLD == 'real' else _FRAMES[(WORLD, p)])
    return _DATA[k]


def _pkey(params):
    return tuple(sorted((k, (float(v) if isinstance(v, (int, float))
                             and not isinstance(v, bool) else v))
                        for k, v in (params or {}).items()))


def slot_arrays(p, slot, name, params):
    """Cached per (pair, name, PARAMS). The params are in the key because the
    first version left them out and every setting collapsed onto the first one
    computed -- see the module note, fault 1."""
    k = (WORLD, p, name, _pkey(params))
    if k in _SLOT:
        return _SLOT[k]
    d = pair_data(p)
    o, h, l, c = (d[x].values.astype(float)
                  for x in ('open', 'high', 'low', 'close'))
    if slot == 'base':
        v = L.compute(name, o, h, l, c, **(params or {}))
    elif slot in ('c1', 'c2'):
        lt, st, lc, sc = L.compute(name, o, h, l, c, **(params or {}))
        v = (lt, st, lc, sc, L.KIND[name] == 'TERNARY')
    else:
        v = L.compute(name, o, h, l, c, **(params or {}))
    _SLOT[k] = v
    return v


def atr_of(p, atr_len):
    k = (WORLD, p, int(atr_len))
    if k not in _ATR:
        d = pair_data(p)
        _ATR[k] = L.P.atr(d['high'].values.astype(float),
                          d['low'].values.astype(float),
                          d['close'].values.astype(float), int(atr_len))
    return _ATR[k]


def _rel(p, atr_len):
    """ATR / close per bar, for whatever world is current."""
    d = pair_data(p)
    h, l, c = (d[k].values.astype(float) for k in ('high', 'low', 'close'))
    a = L.P.atr(h, l, c, int(atr_len))
    return np.where(c > 0, a / c, np.nan)


def _lowvol_arr(p, q, atr_len):
    """nnfxvol.lowvol_mask(causal=True) on arrays, for any world.

    Expanding percentile over bars <= t-1 of a ONE-BAR-LAGGED ATR/price, with
    nnfxvol.MIN_HIST bars of history required first. Written out here because
    the shipped function reads N.pair_data directly and so cannot see a
    synthetic world -- and `check_masks` asserts this reproduces it EXACTLY on
    the real world, so there is one implementation's worth of behaviour and
    two implementations checking each other.
    """
    rel = _rel(p, atr_len)
    rl = np.full(len(rel), np.nan)
    rl[1:] = rel[:-1]
    fl = (pd.Series(rl).expanding(min_periods=VOL.MIN_HIST)
          .quantile(float(q)).to_numpy())
    return np.isfinite(rl) & np.isfinite(fl) & (rl < fl)


def _panel(atr_len, pairs=None):
    """The 28-pair panel of LAGGED ATR/price on a union date index, and its
    cross-sectional median. Causal: every input is bar t-1 on every pair."""
    pairs = list(pairs or S.all_pairs())
    k = (WORLD, int(atr_len), tuple(pairs))
    if k in _PANEL:
        return _PANEL[k]
    uni = pd.DatetimeIndex(sorted(set().union(
        *[set(pd.DatetimeIndex(pair_data(p).index)) for p in pairs])))
    M = np.full((len(pairs), len(uni)), np.nan)
    for j, p in enumerate(pairs):
        rel = _rel(p, atr_len)
        rl = np.full(len(rel), np.nan); rl[1:] = rel[:-1]
        sel = uni.get_indexer(pd.DatetimeIndex(pair_data(p).index))
        ok = sel >= 0
        M[j, sel[ok]] = rl[np.asarray(ok)]
    # an all-NaN column is a date no pair has a lagged reading for; nanmedian
    # warns on it and returns NaN, which is the right answer, so the column is
    # masked out first rather than the warning being suppressed globally.
    good = np.isfinite(M).any(axis=0)
    med = np.full(len(uni), np.nan)
    if good.any():
        med[good] = np.nanmedian(M[:, good], axis=0)
    _PANEL[k] = (uni, M, med)
    return _PANEL[k]


def _peg_arr(p, x, atr_len, pairs=None):
    """nnfxvol.peg_mask on arrays, for any world."""
    pairs = list(pairs or S.all_pairs())
    uni, M, med = _panel(atr_len, pairs)
    j = pairs.index(p)
    with np.errstate(invalid='ignore'):
        flag = np.isfinite(M[j]) & np.isfinite(med) & (M[j] < float(x) * med)
    ix = pd.DatetimeIndex(pair_data(p).index)
    sel = uni.get_indexer(ix)
    out = np.zeros(len(ix), bool)
    ok = sel >= 0
    out[ok] = flag[sel[ok]]
    return out


def check_masks(pairs=None, atr_len=14, q=LOWVOL_Q, x=PEG_X):
    """The array-level masks against the shipped ones, on the REAL world.

    This is the guard on the world mechanism. If it ever fails, the search
    null is reading a different gate than the real search and nothing it says
    about a floor means anything.
    """
    assert WORLD == 'real', 'check_masks is a real-world check'
    bad = []
    for p in (pairs or S.all_pairs()):
        _i, lv = VOL.lowvol_mask(p, q=q, atr_len=atr_len, causal=True)
        _i2, pg = VOL.peg_mask(p, x=x, atr_len=atr_len)
        if not np.array_equal(lv, _lowvol_arr(p, q, atr_len)):
            bad.append('%s floor' % p)
        if not np.array_equal(pg, _peg_arr(p, x, atr_len)):
            bad.append('%s peg' % p)
    assert not bad, 'array masks disagree with nnfxvol: %s' % ', '.join(bad)
    return True


def entry_block(p, atr_len=14, lowvol_q=LOWVOL_Q, peg_x=PEG_X):
    """Jack's two standing entry gates for this pair, as ONE boolean to AND
    into the volume slot. True = BLOCKED.

    On the REAL world the shipped nnfxvol functions are used, so the
    protocol's reported numbers come out of already-audited code. On a
    synthetic world the array-level versions are used, and `check_masks`
    proves the two agree bar for bar on all 28 real pairs.
    """
    k = (WORLD, p, int(atr_len), lowvol_q, peg_x)
    if k in _MASK:
        return _MASK[k]
    n = len(pair_data(p))
    blk = np.zeros(n, bool)
    if lowvol_q:
        if WORLD == 'real':
            _i, lv = VOL.lowvol_mask(p, q=lowvol_q, atr_len=atr_len,
                                     causal=True)
        else:
            lv = _lowvol_arr(p, lowvol_q, atr_len)
        assert len(lv) == n, '%s floor mask %d vs %d' % (p, len(lv), n)
        blk |= lv
    if peg_x:
        if WORLD == 'real':
            _i, pg = VOL.peg_mask(p, x=peg_x, atr_len=atr_len)
        else:
            pg = _peg_arr(p, peg_x, atr_len, PEG_PAIRS or None)
        assert len(pg) == n, '%s peg mask %d vs %d' % (p, len(pg), n)
        blk |= pg
    _MASK[k] = blk
    return blk


_BASE = {}
_AMB = {}


def base_dict(p, atr_len):
    """o/h/l/c/atr/suspect for one pair, built ONCE.

    The search re-evaluates the same pair hundreds of thousands of times with
    five different slot arrays each time. Rebuilding `d[x].values.astype(float)`
    per evaluation was 80% of the fast path's cost -- 0.079 s of the 0.080 s it
    took, against a 1.2 ms bar loop. Measured, then fixed.
    """
    k = (WORLD, p, int(atr_len))
    if k in _BASE:
        return _BASE[k]
    d = pair_data(p)
    o, h, l, c = (d[x].values.astype(float)
                  for x in ('open', 'high', 'low', 'close'))
    _BASE[k] = dict(o=o, h=h, l=l, c=c, atr=atr_of(p, atr_len),
                    suspect=(d['suspect'].values.astype(bool)
                             if 'suspect' in d.columns
                             else np.zeros(c.size, bool)))
    return _BASE[k]


def amb_cached(p):
    """amb_args' 12-tuple, reused. The counter arrays are SHARED, so a caller
    that wants gap or ambiguity counts must call AMB.amb_args itself -- the
    search does not, and allocating two arrays per evaluation is not free at
    this budget.

    A SYNTHETIC WORLD GETS THE OFF SENTINEL, AND THAT IS A REAL LIMITATION OF
    THE SEARCH NULL. The hourly bid/ask path exists only for real prices, so a
    block-shuffled series has no intraday path to resolve an ambiguous bar or
    to fill a gap at the first tradable price. Null stops therefore fill at
    the stop or at the daily open, which is the pre-25-November behaviour.
    SOURCE3.md states this where it states the floor; it is not hidden in a
    cache function.
    """
    k = (WORLD, p)
    if k not in _AMB:
        _AMB[k] = (AMB.amb_args(p) if WORLD == 'real'
                   else E._amb_off(len(pair_data(p))))
    return _AMB[k]


def assemble(p, C):
    """The engine's A dict for one pair and one complete candidate.

    This is E.prepare's job, done slot by slot so the five slots can be cached
    INDEPENDENTLY. A sweep over candidates reuses an indicator's arrays across
    every candidate that mentions it at the same setting, which is the whole
    reason the search is affordable; E.prepare recomputes all five every call.
    """
    A = dict(base_dict(p, C['risk']['atr_len']))
    A['bl'] = slot_arrays(p, 'base', C['base'], C['base_params'])
    lt, st, lc, sc, tern = slot_arrays(p, 'c1', C['c1'], C['c1_params'])
    A.update(c1_lt=lt, c1_st=st, c1_lc=lc, c1_sc=sc, c1_ternary=tern)
    _a, _b, lc2, sc2, t2 = slot_arrays(p, 'c2', C['c2'], C['c2_params'])
    A.update(c2_lc=lc2, c2_sc=sc2, c2_ternary=t2)
    vl, vs = slot_arrays(p, 'vol', C['vol'], C['vol_params'])
    blk = entry_block(p, C['risk']['atr_len'])
    A['v_ok_l'] = np.asarray(vl, bool) & ~blk
    A['v_ok_s'] = np.asarray(vs, bool) & ~blk
    xl, xs = slot_arrays(p, 'exit', C['exit'], C['exit_params'])
    A['x_el'] = np.asarray(xl, bool); A['x_es'] = np.asarray(xs, bool)
    return A


def _kw(C):
    r = C['risk']
    return dict(RULES, plan=int(r['plan']), risk_dollars=RISK_DOLLARS,
                atr_mult=float(r['atr_mult']),
                tp_mult=float(r['tp_mult']), trail_mult=float(r['trail_mult']),
                trail_start_mult=float(r['trail_start_mult']),
                be_pct=float(r['be_pct']),
                max_atr_dist=float(r['max_atr_dist']),
                bridge_bars=int(r['bridge_bars']),
                one_candle_rule=bool(r['one_candle_rule']),
                use_continuation=bool(r['use_continuation']),
                time_stop_bars=int(r['time_stop_bars']))


def run_raw(C, pairs=None):
    """-> {pair: engine output dict}. No pandas, no cap. The search's path."""
    pairs = pairs or S.all_pairs()
    kw = _kw(C)
    out = {}
    for p in pairs:
        out[p] = E.run(assemble(p, C), amb=amb_cached(p), **kw)
    return out


def run_candidate(C, pairs=None, cap=True):
    """-> the trade frame, at capped size. The REPORTING path."""
    pairs = pairs or S.all_pairs()
    kw = _kw(C)
    am = float(C['risk']['atr_mult'])
    rows = []
    for p in pairs:
        d = pair_data(p)
        res = E.run(assemble(p, C), amb=amb_cached(p), **kw)
        tf = E.trade_frame(res, d)
        if tf is None or not len(tf):
            continue
        tf = tf.copy(); tf['pair'] = p
        rows.append(tf)
    if not rows:
        return pd.DataFrame()
    T = pd.concat(rows, ignore_index=True)
    T['R_gross'] = T.R.astype(float) * am / RISK_UNIT_ATR
    T['atr_mult_used'] = am
    T['cand_id'] = cand_id(C)
    for s in SLOTS:
        T[s] = C[s]; T[s + '_set'] = C[s + '_set']
    T['lowvol_q'] = LOWVOL_Q; T['peg_x'] = PEG_X
    T['gapfill_on'] = int(AMB.GAPFILL_STANDING and WORLD == 'real')
    T['world'] = WORLD
    if cap:
        T, _summ = VOL.apply_leverage_cap(T)
        T = T.reset_index(drop=True)
        T['leverage_cap_on'] = 1
    else:
        T['leverage_cap_on'] = 0
    return T


# ======================= scoring ========================================
def cost_R(T):
    """Round-trip cost per LEG in the 1.5-ATR R unit, on the engine's own risk
    denominator.

    Identical to nnfx1._cost_R except for the divisor: that one uses
    l2sweep.RISK (100) while the engine the nnfx path runs is risking 200 per
    unit of raw r. See the module note, fault 3. This is the only cost charge
    in the protocol and every figure in it goes through here.
    """
    if not S.COSTS:
        return np.zeros(len(T))
    f = T.pair.map(S.COSTS).to_numpy(float)
    am = (T.atr_mult_used.to_numpy(float) if 'atr_mult_used' in T.columns
          else np.ones(len(T)))
    return (f * np.abs(T.entry_px.to_numpy(float))
            * np.abs(T.units.to_numpy(float)) / RISK_DOLLARS) \
        * am / RISK_UNIT_ATR



def daily_of(T, years=None):
    """The daily mark-to-market series in 1.5-ATR units, net of cost.

    THE RESET IS NOT COSMETIC. nnfx1.daily_series indexes the cost array by
    the frame's own index (`cost[g.index.to_numpy()]`), so any frame handed in
    with a non-contiguous index -- which is every G3 currency split, being a
    boolean mask of the full book -- reads past the end of the cost array or,
    worse, reads the wrong trade's cost. It raised IndexError on N1's first
    split, which is the good outcome; a shorter mask would have returned
    silently wrong numbers.
    """
    if T is None or not len(T):
        return pd.DataFrame(columns=['date', 'R'])
    T = T.reset_index(drop=True)
    DS = N.daily_series(T, cost_R(T))
    if years is None:
        return DS
    return DS[pd.DatetimeIndex(DS.date).year.isin(list(years))]


def _dip95(d, ndraw=400, seed=11):
    """95th percentile max drawdown over shuffled day orders.

    IT CAN SIT ABOVE OR BELOW THE REALISED DIP and the rule is to take the
    MAXIMUM of the two, never to assume which. On item 5's eight sleeves it
    was ABOVE on all eight, by 1.22x to 2.36x -- the opposite of what the
    graft book showed, and the reason BOOK.md carries a correction.
    """
    rng = np.random.default_rng(seed)
    d = np.asarray(d, float); d = d[np.isfinite(d)]
    if not len(d):
        return np.nan
    out = np.empty(ndraw)
    for k in range(ndraw):
        eq = np.cumsum(rng.permutation(d))
        out[k] = float(np.max(np.maximum.accumulate(eq) - eq))
    return float(np.quantile(out, 0.95))


def score(T, years=EVIDENCE, nboot=2000, DS=None):
    """Every column PROTOCOL.md section 5 asks for, from one trade frame."""
    out = dict(years_from=min(years), years_to=max(years))
    DS = daily_of(T, years) if DS is None else DS
    if not len(DS):
        return dict(out, trades=0, R_total=np.nan)
    r = DS.R.to_numpy(float)
    yr = pd.DatetimeIndex(DS.date).year
    ys = pd.Series(r).groupby(yr.to_numpy()).sum().sort_index()
    nyr = max(1, len(ys))
    tot = float(r.sum())
    eq = np.cumsum(r)
    dip_true = float(np.max(np.maximum.accumulate(eq) - eq))
    d95 = _dip95(r)
    bind = float(np.nanmax([dip_true, d95]))
    tb, bsd = N._block_t(r, ndraw=nboot)
    order = np.argsort(-r)
    ex = {}
    for k, lab in ((1, 'best_day'), (5, 'best5_days')):
        keep = np.ones(len(r), bool); keep[order[:k]] = False
        ex['R_ex_' + lab] = float(r[keep].sum())
        ex['R_per_year_ex_' + lab] = float(r[keep].sum() / nyr)
    # ---- per TRADE, in the R_gross unit, net of cost, by EXIT year
    cost = cost_R(T)
    net = T.R_gross.to_numpy(float) - np.asarray(cost, float)
    Rtr = (T.assign(_n=net)
           .groupby(['pair', 'entry_date', 'direction'], as_index=False)
           .agg(R=('_n', 'sum'), xd=('exit_date', 'max'),
                gross=('R_gross', 'sum'), cst=('_n', 'size')))
    Rtr = Rtr[pd.DatetimeIndex(Rtr.xd).year.isin(list(years))]
    ntr = len(Rtr)
    gross_pt = float(Rtr.gross.mean()) if ntr else np.nan
    net_pt = float(Rtr.R.mean()) if ntr else np.nan
    best_trade = float(Rtr.R.max()) if ntr else np.nan
    realized = float(Rtr.R.sum()) if ntr else np.nan
    out.update(
        trades=ntr, trades_per_year=ntr / nyr,
        R_total=tot, R_per_year=tot / nyr,
        R_gross_per_trade=gross_pt, R_net_per_trade=net_pt,
        cost_per_trade=(gross_pt - net_pt) if ntr else np.nan,
        dip_true=dip_true, dip95=d95, dip_binding=bind,
        R_per_dip=(tot / bind if bind > 1e-9 else np.nan),
        t_yearly=(float(ys.mean() * np.sqrt(nyr) / ys.std(ddof=1))
                  if nyr > 1 and ys.std(ddof=1) > 0 else np.nan),
        t_block_boot=tb, boot_sd_of_mean=bsd,
        years=nyr, years_positive=int((ys > 0).sum()),
        worst_year=float(ys.min()), best_year=float(ys.max()),
        best_day_R=float(r.max()), worst_day_R=float(-r.min()),
        best_trade_R=best_trade, R_realized_total=realized,
        best_trade_share=(best_trade / realized
                          if realized and abs(realized) > 1e-9 else np.nan),
        days=len(r), **ex)
    # the prop numbers, same convention as item 5
    sc = min(RR.FIRM_TRAIL * 100.0 / bind if bind > 0 else np.inf,
             RR.FIRM_DAILY * 100.0 / out['worst_day_R']
             if out['worst_day_R'] > 0 else np.inf)
    out['firm_scale'] = float(sc) if np.isfinite(sc) else np.nan
    out['firm_pct_per_year'] = (out['R_per_year'] * float(sc)
                                if np.isfinite(sc) else np.nan)
    return out


def per_pair(T, years=EVIDENCE):
    """28 rows x 2 directions. PROTOCOL.md's per-pair table."""
    if T is None or not len(T):
        return pd.DataFrame()
    cost = cost_R(T)
    net = T.R_gross.to_numpy(float) - np.asarray(cost, float)
    X = T.assign(_n=net)
    X = X[pd.DatetimeIndex(X.exit_date).year.isin(list(years))]
    if not len(X):
        return pd.DataFrame()
    g = (X.groupby(['pair', 'direction'], as_index=False)
         .agg(legs=('_n', 'size'), R_net=('_n', 'sum'),
              R_gross=('R_gross', 'sum')))
    e = (X.groupby(['pair', 'direction', 'entry_date'], as_index=False)
         .agg(r=('_n', 'sum')))
    n = (e.groupby(['pair', 'direction'], as_index=False)
         .agg(trades=('r', 'size'), R_per_trade=('r', 'mean'),
              win_rate=('r', lambda s: float((s > 0).mean()))))
    return g.merge(n, on=['pair', 'direction'], how='left')


# ======================= the null, for G1's floor =======================
def null_t(T, years=EVIDENCE, ndraw=200, seed=7, nboot=500):
    """RANDOM-ENTRY NULL, MATCHED ON COUNT AND HOLDING PERIOD, IN THE UNITS
    OF G1's STATISTIC.

    nnfx1._null_match returns per-draw TOTALS. G1 is a block-bootstrap t on a
    daily MARK-TO-MARKET series, so a total cannot be its floor: the two are
    different statistics. This builds each null draw's own daily MTM series the
    same way nnfx1.daily_series builds the real one -- the open mark on bar b
    is dir x (close[b] - entry) / (1.5 x ATR at entry), the increment is the
    difference of consecutive marks, and the entry cost is charged on the entry
    bar -- and then takes the SAME block-bootstrap t of it. Real and null are
    then the same number computed the same way, which is the only way a floor
    means anything.

    Only the TIMING is random: the per-pair trade count, the holding periods
    and the long/short split are the real candidate's own, permuted.
    """
    if T is None or not len(T):
        return np.array([])
    cost = np.asarray(cost_R(T), float)
    X = T.reset_index(drop=True)
    m = np.asarray(pd.DatetimeIndex(X.exit_date).year.isin(list(years)))
    X = X[m].reset_index(drop=True); cost = cost[m]
    if not len(X):
        return np.array([])
    rng = np.random.default_rng(seed)
    # one global day axis so draws from different pairs land on the same days
    dates = sorted(set().union(*[set(pd.DatetimeIndex(pair_data(p).index))
                                 for p in X.pair.unique()]))
    dmap = {d: i for i, d in enumerate(dates)}
    nd = len(dates)
    per = {}
    for p, g in X.groupby('pair'):
        d = pair_data(p)
        cl = d['close'].values.astype(float)
        a = atr_of(p, RISK['atr_len'])
        idx = pd.DatetimeIndex(d.index)
        gl = np.array([dmap[t] for t in idx])        # bar -> global day
        ent = idx.get_indexer(pd.DatetimeIndex(g.entry_date))
        ok = ent >= 0
        hold = np.maximum(1, g.bars_held.to_numpy(int)[ok])
        dirs = np.where(g.direction.to_numpy()[ok] == 'long', 1.0, -1.0)
        nlegs = (g.groupby(['entry_date', 'direction']).leg.transform('size')
                 .to_numpy(float)[ok])
        cmean = float(cost[g.index.to_numpy()].mean()) if len(cost) else 0.0
        per[p] = (cl, a, gl, ent[ok], hold, dirs, nlegs, cmean)
    ts = np.full(ndraw, np.nan)
    for k in range(ndraw):
        acc = np.zeros(nd)
        for p, (cl, a, gl, ent, hold, dirs, nlegs, cmean) in per.items():
            n = len(ent)
            if n == 0:
                continue
            lo, hi = int(ent.min()), int(ent.max())
            if hi <= lo:
                continue
            e = rng.integers(lo, hi, size=n)
            hh = rng.permutation(hold)
            dv = rng.permutation(dirs)
            x = np.minimum(e + hh, len(cl) - 1)
            ae = a[e]
            good = np.isfinite(ae) & (ae > 0)
            for j in np.nonzero(good)[0]:
                b0, b1 = int(e[j]), int(x[j])
                if b1 <= b0:
                    continue
                mark = dv[j] * (cl[b0:b1 + 1] - cl[b0]) / (RISK_UNIT_ATR * ae[j])
                inc = np.diff(np.concatenate(([0.0], mark)))
                inc[0] -= cmean
                np.add.at(acc, gl[b0:b1 + 1], inc)
        t, _s = N._block_t(acc[acc != 0.0] if (acc != 0.0).any() else acc,
                           ndraw=nboot)
        ts[k] = t
    return ts[np.isfinite(ts)]


def best_of_floor(null_by_cand, m, alpha=0.05, nboot=4000, seed=17):
    """Best-of-m floor from the batch's OWN nulls. nnfx1.empirical_floor."""
    return N.empirical_floor(null_by_cand, m, alpha=alpha, nboot=nboot,
                             seed=seed)


# ======================= the four gates =================================
def g2(sc):
    """ONE EVENT. Three numbers, all three must hold."""
    ok = (np.isfinite(sc.get('R_ex_best_day', np.nan))
          and sc['R_ex_best_day'] > 0
          and sc['R_ex_best5_days'] > 0
          and np.isfinite(sc.get('best_trade_share', np.nan))
          and sc['best_trade_share'] < 0.25)
    return bool(ok), dict(G2_R_ex_best_day=sc.get('R_ex_best_day'),
                          G2_R_ex_best5=sc.get('R_ex_best5_days'),
                          G2_best_trade_share=sc.get('best_trade_share'))


def g3(T):
    """HOLD-OUT. Two time halves and three currency splits, both sides.

    THE SPLIT IS TAKEN FROM THE WHOLE 28-PAIR CAPPED FRAME. Re-running the
    engine on 15 pairs would re-run the leverage cap on 15 pairs, which is a
    different and easier portfolio -- see the module note, fault 3. The trader
    runs the whole book; a split asks what that book earned on those pairs.
    """
    det = {}
    worst = np.inf
    for lab, yrs in (('2005_2010', HALF_A), ('2011_2015', HALF_B)):
        v = float(daily_of(T, yrs).R.sum()) if len(T) else np.nan
        det['G3_R_' + lab] = v
        worst = min(worst, v if np.isfinite(v) else -np.inf)
    for cc in SPLITS:
        tag = '_'.join(cc)
        has = T.pair.str.contains(cc[0]) | T.pair.str.contains(cc[1])
        for side, mask in (('with', has), ('without', ~has)):
            sub = T[mask]
            v = (float(daily_of(sub, EVIDENCE).R.sum())
                 if len(sub) else np.nan)
            det['G3_R_%s_%s' % (tag, side)] = v
            worst = min(worst, v if np.isfinite(v) else -np.inf)
    det['G3_worst_slice_R'] = (float(worst) if np.isfinite(worst) else np.nan)
    return bool(np.isfinite(worst) and worst > 0), det


def g4(C, pairs=None, verbose=False):
    """NUDGE. Each numeric setting one grid step down and one step up, alone.

    20 runs: the five slots' own length knobs at x0.5 and x2, and the five
    risk knobs at the coarse steps PROTOCOL.md declares. Every one must come
    out positive on total R over 2005-2015. The WORST is reported, so a
    near-miss is visible rather than hidden behind a pass.
    """
    pairs = pairs or S.all_pairs()
    rows = []
    for sl in SLOTS:
        if not knob_names(C[sl]):
            rows.append(dict(knob='%s:%s' % (sl, C[sl]), direction='none',
                             value='no length knob', R_total=np.nan,
                             skipped=1))
            continue
        for lab, mult in (('down', 0.5), ('up', 2.0)):
            D = dict(C)
            D[sl + '_params'] = scaled_params(C[sl], mult, C[sl + '_params'])
            if _pkey(D[sl + '_params']) == _pkey(C[sl + '_params']):
                rows.append(dict(knob='%s:%s' % (sl, C[sl]), direction=lab,
                                 value='collapses onto the candidate',
                                 R_total=np.nan, skipped=1))
                continue
            T = run_candidate(D, pairs)
            v = float(daily_of(T, EVIDENCE).R.sum()) if len(T) else np.nan
            rows.append(dict(knob='%s:%s' % (sl, C[sl]), direction=lab,
                             value=json.dumps(
                                 {k: (round(float(x), 6)
                                      if isinstance(x, (int, float))
                                      and not isinstance(x, bool) else x)
                                  for k, x in D[sl + '_params'].items()}),
                             R_total=v, skipped=0))
    for knob, (dn, up) in NUDGE_RISK.items():
        for lab, val in (('down', dn), ('up', up)):
            D = dict(C); D['risk'] = dict(C['risk']); D['risk'][knob] = val
            T = run_candidate(D, pairs)
            v = float(daily_of(T, EVIDENCE).R.sum()) if len(T) else np.nan
            rows.append(dict(knob='risk:%s' % knob, direction=lab,
                             value=str(val), R_total=v, skipped=0))
    G = pd.DataFrame(rows)
    live = G[(G.skipped == 0) & np.isfinite(G.R_total)]
    ok = bool(len(live)) and bool((live.R_total > 0).all())
    det = dict(G4_runs=int(len(live)),
               G4_skipped=int((G.skipped == 1).sum()),
               G4_worst_R=(float(live.R_total.min()) if len(live) else np.nan),
               G4_worst_knob=(str(live.loc[live.R_total.idxmin(), 'knob'])
                              + ' ' + str(live.loc[live.R_total.idxmin(),
                                                   'direction'])
                              if len(live) else ''),
               G4_n_negative=int((live.R_total <= 0).sum()) if len(live) else 0)
    return ok, det, G


def evaluate(C, pairs=None, with_g4=True, ndraw_null=200, verbose=True,
             nudge_out=None):
    """One candidate, the whole protocol except G1's batch floor.

    G1 needs the BATCH's null, so this returns the candidate's own null array
    and its t; the batch assembles the floor and sets G1.
    """
    pairs = pairs or S.all_pairs()
    t0 = time.time()
    T = run_candidate(C, pairs)
    sc = score(T, EVIDENCE)
    sc_confirm = score(T, CONFIRM)        # computed, stored, NOT reported
    ok2, d2 = g2(sc)
    ok3, d3 = g3(T) if len(T) else (False, {})
    nl = null_t(T, EVIDENCE, ndraw=ndraw_null)
    ok4, d4, G = (True, {}, pd.DataFrame())
    if with_g4:
        ok4, d4, G = g4(C, pairs)
        if nudge_out is not None and len(G):
            G = G.copy(); G['cand'] = C['name']
            nudge_out.append(G)
    row = dict(cand=C['name'], cand_id=cand_id(C), source=C['source'],
               reason=C['reason'], label=cand_label(C),
               **{s: C[s] for s in SLOTS},
               **{s + '_set': C[s + '_set'] for s in SLOTS},
               **{('params_' + s): json.dumps(
                   {k: (round(float(v), 6)
                        if isinstance(v, (int, float))
                        and not isinstance(v, bool) else v)
                    for k, v in C[s + '_params'].items()}) for s in SLOTS},
               **sc,
               G2=int(ok2), G3=int(ok3), G4=int(ok4) if with_g4 else -1,
               **d2, **d3, **d4,
               R_total_confirm_UNREPORTED=sc_confirm.get('R_total'),
               seconds=time.time() - t0)
    if verbose:
        print('    %-10s R %+8.3f  R/yr %+6.3f  n %5d  dip %6.3f  R/dip %+6.3f'
              '  t_bs %+5.2f  G2 %s G3 %s G4 %s'
              % (C['name'], sc.get('R_total', np.nan),
                 sc.get('R_per_year', np.nan), sc.get('trades', 0),
                 sc.get('dip_binding', np.nan), sc.get('R_per_dip', np.nan),
                 sc.get('t_block_boot', np.nan),
                 'Y' if ok2 else 'n', 'Y' if ok3 else 'n',
                 ('Y' if ok4 else 'n') if with_g4 else '-'), flush=True)
    return dict(row=row, T=T, null=nl, per_pair=per_pair(T, EVIDENCE),
                nudge=G)


def run_batch(cands, pairs=None, with_g4=True, ndraw_null=200, tag='batch',
              verbose=True):
    """A whole source: every candidate, then G1 from the batch's own null."""
    pairs = pairs or S.all_pairs()
    res, nulls, pp, nud = [], {}, [], []
    for C in cands:
        r = evaluate(C, pairs, with_g4=with_g4, ndraw_null=ndraw_null,
                     verbose=verbose, nudge_out=nud)
        res.append(r['row']); nulls[C['name']] = r['null']
        if len(r['per_pair']):
            q = r['per_pair'].copy(); q['cand'] = C['name']; pp.append(q)
    m = len(cands)
    floor_batch = best_of_floor(nulls, m)
    floor_alone = best_of_floor(nulls, 1)
    D = pd.DataFrame(res)
    D['G1_floor_best_of_%d' % m] = floor_batch
    D['G1_floor_alone'] = floor_alone
    D['G1'] = ((D.t_block_boot > floor_batch)
               & np.isfinite(D.t_block_boot)).astype(int)
    D['G1_clears_alone'] = ((D.t_block_boot > floor_alone)
                            & np.isfinite(D.t_block_boot)).astype(int)
    D['passer'] = ((D.G1 == 1) & (D.G2 == 1) & (D.G3 == 1)
                   & ((D.G4 == 1) | (D.G4 == -1))).astype(int)
    D['batch_size'] = m
    nullrows = []
    for k, v in nulls.items():
        if v is None or not len(v):
            continue
        nullrows.append(dict(cand=k, draws=len(v), null_t_mean=float(np.mean(v)),
                             null_t_p95=float(np.quantile(v, 0.95)),
                             null_t_max=float(np.max(v))))
    return dict(summary=D, per_pair=(pd.concat(pp, ignore_index=True)
                                     if pp else pd.DataFrame()),
                nulls=pd.DataFrame(nullrows),
                nudge=(pd.concat(nud, ignore_index=True)
                       if nud else pd.DataFrame()),
                floor=floor_batch)


# ======================= the search's fast path =========================
_FAST = {}


def fast_ctx(pairs, years):
    """Everything the numpy objective needs, once per (pairs, years)."""
    k = (WORLD, tuple(pairs), tuple(years))
    if k in _FAST:
        return _FAST[k]
    dates = sorted(set().union(*[set(pd.DatetimeIndex(pair_data(p).index))
                                 for p in pairs]))
    dmap = {d: i for i, d in enumerate(dates)}
    yr = np.array([d.year for d in dates])
    keep = np.isin(yr, list(years))
    per = {}
    for p in pairs:
        idx = pd.DatetimeIndex(pair_data(p).index)
        per[p] = (np.array([dmap[t] for t in idx]),
                  float(S.COSTS.get(p, 0.0)))
    _FAST[k] = dict(nd=len(dates), day_year=yr, keep=keep, per=per,
                    nyr=max(1, len(set(yr[keep]))))
    return _FAST[k]


def fast_obj(C, pairs, years, raw=None):
    """NET R PER YEAR EXCLUDING THE BEST DAY, by REALISED exit day, uncapped.

    PROTOCOL.md section 5 declares this and says exactly what it is not: the
    reported figure is mark-to-market and capped, this is realised-by-exit-day
    and uncapped. It exists because the full path costs ~70 ms a candidate and
    the bar loop costs ~1.2 ms, and Source 3 evaluates hundreds of thousands.
    Every candidate the search SURFACES is re-scored on the full path, and the
    rank correlation between the two is measured and reported.

    THE COST IS CHARGED PER LEG ON units/n_legs. `units` is the full position
    size written identically on both legs of a plan-2 entry, so charging it
    per leg doubles the spread -- the same factor of two nnfx1.daily_series
    carries a long comment about. Fault 2 in the module note.
    """
    ctx = fast_ctx(pairs, years)
    am = float(C['risk']['atr_mult'])
    acc = np.zeros(ctx['nd'])
    kw = _kw(C)
    ntr = 0
    for p in pairs:
        res = (raw or {}).get(p)
        if res is None:
            res = E.run(assemble(p, C), amb=amb_cached(p), **kw)
        n = res['_n']
        if not n:
            continue
        xb = res['exit_bar'][:n]; eb = res['entry_bar'][:n]
        u = np.abs(res['units'][:n]); px = np.abs(res['entry_px'][:n])
        rg = res['r'][:n] * am / RISK_UNIT_ATR
        # ONE ROUND TRIP PER LEG ON THE LEG'S OWN SIZE, divided by the
        # engine's RISK_DOLLARS -- the same charge cost_R makes, written in
        # numpy. The first version divided by units/n_legs and by S.RISK,
        # which for plan 2 happens to give the identical number; it is written
        # the direct way so it is also right for plan 1.
        gl = ctx['per'][p][0]
        key = eb.astype(np.int64) * 4 + (res['dir'][:n].astype(np.int64) + 1)
        f = ctx['per'][p][1]
        cst = f * px * u / RISK_DOLLARS * am / RISK_UNIT_ATR
        np.add.at(acc, gl[np.clip(xb, 0, len(gl) - 1)], rg - cst)
        # trades, not legs, and only those EXITING inside `years`
        iny = ctx['keep'][gl[np.clip(xb, 0, len(gl) - 1)]]
        ntr += int(len(np.unique(key[iny]))) if iny.any() else 0
    a = acc[ctx['keep']]
    if not len(a) or not np.isfinite(a).any():
        return -np.inf, 0, 0.0
    tot = float(a.sum())
    ex = tot - float(a.max()) if len(a) else tot
    return ex / ctx['nyr'], ntr, tot


def verify_fast(C, pairs, years, tol=1e-6):
    """fast_obj's total against the UNCAPPED full path, same years.

    NOT against the reported figure. The reported figure is capped and
    mark-to-market; the fast objective is uncapped and realised-by-exit-day.
    Comparing them would be comparing two different numbers and calling the
    difference an error. What CAN be checked exactly is the realised net R:
    the fast path and the full path must agree on it to floating point.
    """
    _o, _n, tot = fast_obj(C, pairs, years)
    T = run_candidate(C, pairs, cap=False)
    if not len(T):
        return dict(fast=tot, full=np.nan, ok=False, trades=0)
    cost = np.asarray(cost_R(T), float)
    net = T.R_gross.to_numpy(float) - cost
    X = T.assign(_n=net)
    xd = pd.DatetimeIndex(X.exit_date).year
    full = float(X[np.isin(xd, list(years))]._n.sum())
    return dict(fast=float(tot), full=full, diff=float(tot - full),
                ok=bool(abs(tot - full) < tol * max(1.0, abs(full))),
                trades=int(len(X)))


# ======================= the ledger =====================================
def ledger_append(rows, source, path=PROTO_LEDGER, n_evaluations=None):
    """Every candidate, with its settings, written BEFORE its result exists
    where the source declares them in advance, and with the evaluation count
    where it does not (Source 3)."""
    D = pd.DataFrame(rows)
    D['source'] = source
    D['written_at'] = pd.Timestamp.utcnow().isoformat()
    if n_evaluations is not None:
        D['n_evaluations_in_source'] = int(n_evaluations)
    if os.path.exists(path):
        old = pd.read_csv(path)
        D = pd.concat([old, D], ignore_index=True)
    D.to_csv(path, index=False)
    return len(D)


def declare(cands, source, path=PROTO_LEDGER):
    """Write the candidates' full settings to the ledger BEFORE scoring.

    PROTOCOL.md section 1: a candidate whose settings were not in the ledger
    before its result existed is not a candidate. This is that step, and it is
    called before run_batch, never after.
    """
    rows = []
    for C in cands:
        rows.append(dict(cand=C['name'], cand_id=cand_id(C),
                         reason=C['reason'], label=cand_label(C),
                         **{s: C[s] for s in SLOTS},
                         **{s + '_set': C[s + '_set'] for s in SLOTS},
                         **{('params_' + s): json.dumps(
                             {k: (round(float(v), 6)
                                  if isinstance(v, (int, float))
                                  and not isinstance(v, bool) else v)
                              for k, v in C[s + '_params'].items()})
                            for s in SLOTS},
                         risk=json.dumps(C['risk']),
                         stage='declared_before_scoring'))
    n = ledger_append(rows, source, path)
    print('  ledger: %d candidates declared for %s (%d rows total)'
          % (len(cands), source, n), flush=True)
    return n


# ======================= provenance, guard 35's format ==================
def prov(paths):
    out = []
    for p in paths:
        if not os.path.exists(p):
            continue
        h = hashlib.md5(open(p, 'rb').read()).hexdigest()[:12]
        try:
            nr = sum(1 for _ in open(p)) - 1
        except Exception:
            nr = -1
        out.append('- `%s` — %d rows, md5 `%s`'
                   % (os.path.relpath(p, _R), nr, h))
    return '\n'.join(out)


def fmt(x, nd=3, sign=True):
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return '—'
    return ('%+.*f' if sign else '%.*f') % (nd, x)


def yn(v):
    return '**PASS**' if int(v) == 1 else ('—' if int(v) == -1 else 'fail')


if __name__ == '__main__':
    S.load_costs(os.environ.get('FX_COST_TABLE',
                                os.path.join(ROOTOUT, 'cost_table_h22.csv')))
    print('slots:', {k: len(v) for k, v in INV.items()})
    C = cand('smoke', 'ichimoku_signals', 'vortex_signals',
             'variance_volume_signals', 'sma_baseline', 'ssl_channel_exit',
             source='smoke')
    print(cand_label(C), cand_id(C))
    t0 = time.time()
    T = run_candidate(C)
    print('run_candidate %.2f s, %d legs' % (time.time() - t0, len(T)))
    sc = score(T)
    for k in ('trades', 'R_total', 'R_per_year', 'dip_binding', 'R_per_dip',
              't_block_boot', 'R_ex_best_day', 'best_trade_share'):
        print('   %-18s %s' % (k, sc.get(k)))
    t0 = time.time()
    o, ntr, tot = fast_obj(C, S.all_pairs(), EVIDENCE)
    print('fast_obj %.4f s -> %.4f R/yr ex best day, %d trades, tot %.3f'
          % (time.time() - t0, o, ntr, tot))
