import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""GATE 1 — DISCOVER. The sweep runner, built to GAUNTLET.md.

READ GAUNTLET.md FIRST. This file implements that spec and may not deviate from
it. No threshold here may be edited once results exist.

------------------------------------------------------------------------
WHAT MAKES 17.6M COMBINATIONS POSSIBLE
------------------------------------------------------------------------
41 C1 x 41 C2 x 16 volume x 16 baseline x 41 exit = 17,635,456.

The trick is that a combination is not 17.6M indicator computations, it is FIVE
LOOKUPS. Every indicator is computed ONCE per pair -- 114 of them -- into a
bool/float matrix indexed [option, bar]. A combination then selects five rows
and runs the bar loop over them. Indicator cost is paid 114 times per pair;
combination cost is paid 17.6M times and is nothing but the loop.

So the only thing that matters for runtime is the bar loop, and the only thing
that matters for memory is the precomputed matrices (~1 MB per pair).

------------------------------------------------------------------------
THE MACHINE (GAUNTLET.md), AND WHAT IT MEANS AT GATE 1
------------------------------------------------------------------------
    tune on W1         -> trade W2 blind
    re-tune on W1+W2   -> trade W3 blind
    score = stitched blind performance (W2 + W3), and nothing else

Gate 1 runs DEFAULT PARAMETERS ONLY, so both tuning steps are empty -- there is
nothing to tune. That does NOT make W1 unused: the spec requires >= 100 trades
pooled in the picking window, and W1 is the picking window. A combination that
cannot trade in W1 is recorded as untested rather than scored.

W4 IS NOT LOADED BY THIS MODULE AT ALL. Not as a variable, not to compute a
coverage number. The single way to guarantee a window is untouched is for the
code that must not touch it to be unable to name it.

------------------------------------------------------------------------
THE LUCK FLOOR
------------------------------------------------------------------------
Gate 1's expectancy bar is the 95th percentile of SCRAMBLED CONTROLS, not a
number someone chose. A control is the same combination run against a
surrogate: the entry signals are kept and the bar sequence they are scored on is
block-shuffled, so any edge that survives is an edge that survives having its
timing destroyed. 78% of Layer 1's best headline number was selection artifact;
this floor is the direct consequence of that.

Writes results/gate1/<shard>.csv checkpoints and results/gate1_survivors.csv.
"""
import glob, itertools, time
import numpy as np, pandas as pd
from numba import njit

import l2lib as L
import l2engine as E

OANDA = os.path.join(ROOTDATA, 'oanda_ohlc')
CKDIR = os.path.join(ROOTOUT, 'gate1')

# GAUNTLET.md. Edited only before results exist.
WINDOWS = {'W1': ('2005-01-03', '2010-12-31'),
           'W2': ('2011-01-01', '2015-12-31'),
           'W3': ('2016-01-01', '2020-12-31')}
MIN_TRADES_PICK = 100      # per REGIME SLICE, not per combination
MIN_TRADES_BLIND = 50      # per slice, per blind window
PF_FLOOR = 1.05
RISK = 100.0

# GAUNTLET.md "RISK". Structure is permanent; these four numbers are gate 1
# defaults and become family-level tunables at gates 2-3.
ATR_LEN = 31               # FROZEN by the pre-test; see GAUNTLET.md
ATR_MULT = 1.0             # stop = 1.0 x ATR
TP_MULT = 1.5              # RR 1:1.5
TRAIL_MULT = 1.5
TRAIL_ARM = 2.0

# Layer 1's shape2, as int codes. ONE definition, used by both the tagger and
# the slicer -- they were briefly separate and the slicer compared an int8 array
# against a python string, which is silently False everywhere and presents as
# "this combination never traded in that regime".
REGIME_CODE = {'trending': 0, 'ranging': 1, 'trend-in-range': 2, 'neither': 3}
REGIME_NAME = {v: k for k, v in REGIME_CODE.items()}

# The two scored slices. plan 2 = two legs, plan 1 = one leg + quick target.
SLICES = (('trend', 2, REGIME_CODE['trending']),
          ('chop', 1, REGIME_CODE['ranging']))

# Exit reason codes run 1..9 (l2engine.REASON); 0 means "never written", which
# cannot happen for a closed trade and is carried only so a stray zero shows up
# as itself rather than being folded into 'stop'.
N_REASON = 10
SLOTS = ('c1', 'c2', 'vol', 'base', 'exit_ind')

# ==========================================================================
# THE THREE SIGNAL-EXIT MODES
# ==========================================================================
#
# EXACTLY ONE IS ACTIVE PER TEST. They are never combined. The first sweep ran
# the exit indicator and the baseline cross simultaneously and unconditionally,
# with the C1-flip exit off, so every combination was really testing "whichever
# of two exits fires first" -- and the tally showed the baseline cross taking
# 44% of trend closes against the exit indicator's 7%. The exit slot was being
# scored on what the baseline left behind, which is why its enrichment was flat:
# 0.18x-1.19x, the narrowest spread of any slot. That is a property of the
# configuration, not of the indicators.
#
# THE RISK PLAN IS NOT A SIGNAL EXIT. Stop, target, breakeven and trail stay
# active in all three modes, exactly as before.
#
# THE EXIT SLOT IS UNUSED IN MODES A AND B, so their enumeration collapses by a
# factor of 39. The dummy value passed is arbitrary and provably irrelevant:
# with exit_on_exit_ind False the x_el/x_es arrays are never read.
MODES = {
    'A': dict(label='C1-flip exit',
              kw=dict(exit_on_c1_flip=True, exit_on_base_cross=False,
                      exit_on_exit_ind=False),
              uses_exit_slot=False),
    'B': dict(label='baseline-cross exit',
              kw=dict(exit_on_c1_flip=False, exit_on_base_cross=True,
                      exit_on_exit_ind=False),
              uses_exit_slot=False),
    'C': dict(label='exit-indicator exit',
              kw=dict(exit_on_c1_flip=False, exit_on_base_cross=False,
                      exit_on_exit_ind=True),
              uses_exit_slot=True),
}
MODE_ORDER = ('A', 'B', 'C')


def mode_kw(mode):
    return dict(MODES[mode]['kw'])


def mode_dir(mode):
    return os.path.join(CKDIR, 'mode%s' % mode)


def mode_opts(opts, mode):
    """The slot menus AS ENUMERATED for a mode. Modes A and B collapse the exit
    slot to a single placeholder because nothing reads it."""
    o = dict(opts)
    if not MODES[mode]['uses_exit_slot']:
        o['exit_ind'] = [opts['exit_ind'][0]]
    return o


def floor_path(mode):
    """SIX FLOORS, not two. A floor is a property of the exact setup it gates,
    and the exit rule decides when every trade ends -- so it decides the R
    distribution a scrambled control draws from just as surely as the stop or
    the ATR length does. Reusing mode C's floor for mode A would be gating one
    trade definition on a bar measured from a different one. This is the fourth
    time in this project a floor has had to be re-measured after the setup
    moved; it is written down here so it is the last time it comes as news."""
    return os.path.join(ROOTOUT, 'gate1_luck_floor_mode%s.csv' % mode)
LABELS = os.path.join(ROOTOUT, 'layer1_states.csv')


def slot_options():
    """The five menus, from the ported registry. Anything tagged UNAVAILABLE
    (needs a volume series spot FX does not have) is excluded and counted --
    it cannot produce a signal, so including it would burn a fifth of the
    search on combinations that are guaranteed silent."""
    R = L.registry_frame()
    out = {}
    for slot, key in (('confirmation', 'c1'), ('confirmation', 'c2'),
                      ('volume', 'vol'), ('baseline', 'base'), ('exit', 'exit_ind')):
        names = sorted(R[(R.slot == slot) & R.available].name)
        out[key] = names
    return out


def load_pair(pair):
    """OANDA mid with the leading placeholder block removed -- see GAUNTLET.md.
    A loader that forgets this trades nothing in the early years and reports it
    as 'no edge'."""
    d = pd.read_csv(os.path.join(OANDA, '%s_mid.csv' % pair), index_col=0,
                    parse_dates=True)
    flat = (d.high.values == d.low.values)
    i = 0
    while i < len(flat) and flat[i]:
        i += 1
    d = d.iloc[i:]
    d['suspect'] = False
    return d


_LAB = None


def regime_codes(pair, index):
    """Layer 1's shape2 for this pair, aligned to the bar index, as int codes.

    THE LABEL IS ALREADY LAGGED ONE BAR -- the value dated D was computed from
    data through D-1 -- so it is joined on the entry date with NO further shift.
    Shifting again would double-count the lag; not shifting at all would be
    reading the same bar the label describes.

    Unlabelled bars get -1 and are excluded from both slices. They are never
    forward-filled: 96.3% of OANDA bars carry a label and the rest are calendar
    mismatches between the H.10 panel Layer 1 was built on and OANDA's. Inventing
    a label for the other 3.7% would put trades in a regime nobody measured.
    """
    global _LAB
    if _LAB is None:
        L_ = pd.read_csv(LABELS, parse_dates=['date'], usecols=['date', 'pair', 'shape2'])
        _LAB = {p: g.set_index('date').shape2 for p, g in L_.groupby('pair')}
    m = REGIME_CODE
    s = _LAB.get(pair)
    if s is None:
        return np.full(len(index), -1, np.int8)
    v = s.reindex(index)
    return v.map(m).fillna(-1).astype(np.int8).values


def precompute(pair, opts, atr_len=None):
    """Every indicator once. -> dict of matrices indexed [option, bar]."""
    atr_len = ATR_LEN if atr_len is None else atr_len
    d = load_pair(pair)
    o, h, l, c = (d[k].values.astype(float) for k in ('open', 'high', 'low', 'close'))
    n = len(d)
    P = {'dates': d.index, 'o': o, 'h': h, 'l': l, 'c': c,
         'atr': L.P.atr(h, l, c, atr_len),
         'suspect': np.zeros(n, bool)}
    conf = {}
    for name in sorted(set(opts['c1']) | set(opts['c2'])):
        lt, st, lc, sc = L.compute(name, o, h, l, c)
        conf[name] = (lt, st, lc, sc, L.KIND[name] == 'TERNARY')
    P['conf'] = conf
    P['vol'] = {name: L.compute(name, o, h, l, c) for name in opts['vol']}
    P['base'] = {name: L.compute(name, o, h, l, c) for name in opts['base']}
    P['exit'] = {name: L.compute(name, o, h, l, c) for name in opts['exit_ind']}
    P['regime'] = regime_codes(pair, d.index)
    return P


# ==========================================================================
# the stats kernel
# ==========================================================================
@njit(cache=True)
def _stats(r, n, w_start, w_end, ebar):
    """Pooled stats over the trades whose ENTRY BAR falls in [w_start, w_end).

    Trades are attributed to a window by ENTRY, not exit. A trade opened in the
    picking window and closed in the blind one belongs to the picking window;
    counting it twice, or by exit, would let tuning leak across the boundary.
    """
    cnt = 0
    tot = 0.0
    gain = 0.0
    loss = 0.0
    wins = 0
    ss = 0.0
    dn = 0.0
    dncnt = 0
    for i in range(n):
        if ebar[i] < w_start or ebar[i] >= w_end:
            continue
        v = r[i]
        cnt += 1
        tot += v
        if v > 0:
            gain += v
            wins += 1
        else:
            loss -= v
            dn += v * v
            dncnt += 1
        ss += v * v
    if cnt == 0:
        return 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    mean = tot / cnt
    var = ss / cnt - mean * mean
    sd = np.sqrt(var) if var > 0 else 0.0
    dsd = np.sqrt(dn / dncnt) if dncnt > 0 else 0.0
    pf = gain / loss if loss > 0 else np.inf
    return cnt, mean, tot, pf, (wins / cnt), sd, dsd


@njit(cache=True)
def _equity_stats(r, n, order):
    """Max drawdown and total, on the trade-ordered equity curve in R."""
    peak = 0.0
    eq = 0.0
    mdd = 0.0
    for k in range(n):
        eq += r[order[k]]
        if eq > peak:
            peak = eq
        d = peak - eq
        if d > mdd:
            mdd = d
    return eq, mdd


def run_combo(P, c1, c2, vol, base, ex, buf, plan=2, atr=None, **kw):
    """One combination, one plan, one pair. Returns the trade count; the trade
    arrays are left in `buf`."""
    lt, st, lc, sc, c1t = P['conf'][c1]
    _, _, c2lc, c2sc, c2t = P['conf'][c2]
    vl, vs = P['vol'][vol]
    el, es = P['exit'][ex]
    nt, both, late, stale = E.run_bars(
        P['o'], P['h'], P['l'], P['c'], P['atr'] if atr is None else atr,
        P['base'][base],
        lt, st, lc, sc, c2lc, c2sc, vl, vs, el, es, P['suspect'],
        c1t, c2t,
        kw.get('use_base_cross', True), kw.get('use_c1_flip', True),
        kw.get('use_continuation', True), kw.get('exit_on_c1_flip', False),
        # defaults reproduce the ORIGINAL both-exits-on behaviour, so anything
        # that calls this without a mode (parity checks, the old pre-tests)
        # still gets what it got before. The sweep always passes a mode.
        kw.get('exit_on_base_cross', True), kw.get('exit_on_exit_ind', True),
        kw.get('one_candle_rule', False), int(plan), RISK,
        kw.get('atr_mult', ATR_MULT), kw.get('tp_mult', TP_MULT),
        kw.get('trail_mult', TRAIL_MULT), kw.get('trail_arm', TRAIL_ARM),
        1.5, 7, True, True,
        buf['entry_bar'], buf['exit_bar'], buf['dir'], buf['leg'],
        buf['entry_px'], buf['exit_px'], buf['units'], buf['r'],
        buf['reason'], buf['route'])
    return nt


def make_buffers(n):
    cap = 4 * n + 8
    b = {k: np.zeros(cap, np.int64) for k in
         ('entry_bar', 'exit_bar', 'dir', 'leg', 'reason', 'route')}
    for k in ('entry_px', 'exit_px', 'units', 'r'):
        b[k] = np.zeros(cap, np.float64)
    return b


def window_bounds(P):
    idx = P['dates']
    b = {}
    for k, (a, z) in WINDOWS.items():
        m = (idx >= a) & (idx <= z)
        w = np.flatnonzero(m)
        b[k] = (int(w[0]), int(w[-1]) + 1) if len(w) else (0, 0)
    return b


def _agg(r):
    """The KPI block, on one slice's stitched blind trades."""
    n = len(r)
    if n == 0:
        return None
    win = r > 0
    gain = float(r[win].sum()); loss = float(-r[~win].sum())
    eq = np.cumsum(r)
    mdd = float((np.maximum.accumulate(eq) - eq).max())
    sd = float(r.std(ddof=1)) if n > 1 else 0.0
    dnv = r[r < 0]
    dsd = float(dnv.std(ddof=1)) if dnv.size > 1 else 0.0
    tot = float(eq[-1])
    return dict(n_blind=n, expectancy_R=float(r.mean()), total_R=tot,
                profit_factor=(gain / loss) if loss > 0 else np.inf,
                win_rate=float(win.mean()),
                sharpe=(r.mean() / sd * np.sqrt(n)) if sd > 0 else 0.0,
                sortino=(r.mean() / dsd * np.sqrt(n)) if dsd > 0 else 0.0,
                max_dd_R=mdd, calmar=(tot / mdd) if mdd > 0 else np.inf)


def score_combo(pairs_data, combo, buf_by_pair, atr_by_pair=None,
                want_reasons=False, **kw):
    """One combination, BOTH PLANS, sliced by the Layer 1 regime at entry.

    GAUNTLET.md: the trend score is the TWO-LEG run restricted to trades entered
    while the label says `trending`; the chop score is the ONE-LEG run restricted
    to `ranging`. They are separate candidates and are gated separately.

    Trades are attributed to a window by ENTRY BAR. A trade opened in the picking
    window and closed in a blind one belongs to the picking window -- scoring it
    as blind would let W1 leak into the score it is supposed to be independent of.
    """
    c1, c2, vol, base, ex = combo
    out = {}
    for sname, plan, code in SLICES:
        rr, n_pick, n_w2, n_w3, n_unlab = [], 0, 0, 0, 0
        rc = np.zeros(N_REASON, np.int64) if want_reasons else None
        for pair, P in pairs_data.items():
            buf = buf_by_pair[pair]
            atr = None if atr_by_pair is None else atr_by_pair[pair]
            nt = run_combo(P, c1, c2, vol, base, ex, buf, plan=plan, atr=atr, **kw)
            if nt == 0:
                continue
            r = buf['r'][:nt]
            eb = buf['entry_bar'][:nt]
            reg = P['regime'][eb]
            n_unlab += int((reg < 0).sum())
            m = reg == code
            if not m.any():
                continue
            wb = P['_wb']
            a1, z1 = wb['W1']
            n_pick += int((m & (eb >= a1) & (eb < z1)).sum())
            for k, acc in (('W2', 2), ('W3', 3)):
                a, z = wb[k]
                mm = m & (eb >= a) & (eb < z)
                c = int(mm.sum())
                if c:
                    rr.append(r[mm])
                    if rc is not None:
                        # the SAME trades whose R feeds the KPIs -- blind
                        # windows, this slice. Tallying a wider population
                        # would describe closes the score never saw.
                        rc += np.bincount(buf['reason'][:nt][mm],
                                          minlength=N_REASON)[:N_REASON]
                    if acc == 2:
                        n_w2 += c
                    else:
                        n_w3 += c
        s = _agg(np.concatenate(rr)) if rr else None
        if s is None:
            s = dict(n_blind=0, expectancy_R=0.0, total_R=0.0, profit_factor=0.0,
                     win_rate=0.0, sharpe=0.0, sortino=0.0, max_dd_R=0.0,
                     calmar=0.0)
        s.update(c1=c1, c2=c2, vol=vol, base=base, exit_ind=ex, slice=sname,
                 plan=plan, n_pick=n_pick, n_w2=n_w2, n_w3=n_w3,
                 n_unlabelled=n_unlab)
        if rc is not None:
            s['_rc'] = rc
        out[sname] = s
    return out


def eligible(s):
    """The trade minimums. A combination that cannot meet them is UNTESTED,
    which is a different thing from failing."""
    if s is None:
        return False
    return (s['n_pick'] >= MIN_TRADES_PICK and s['n_w2'] >= MIN_TRADES_BLIND
            and s['n_w3'] >= MIN_TRADES_BLIND)


# ==========================================================================
# THE LUCK FLOOR -- gate 1's expectancy bar
# ==========================================================================
BLOCK = 21          # sign is flipped in runs this long, not bar by bar


def surrogate(d, rng):
    """A scrambled control: SIGN RANDOMISATION IN BLOCKS.

    Every |return| is kept exactly where it was, and the SIGN of each block of
    bars is flipped or not at random. The volatility path -- ATR, ranges, the
    clustering of quiet and violent stretches -- is therefore identical to the
    real series bar for bar, and the only thing destroyed is DIRECTION, which is
    the thing a trend strategy claims to exploit. Layer 1 used the same
    construction for the same reason.

    WHY NOT BLOCK-SHUFFLING THE BARS, which is the more obvious control. It was
    tried first and it is INVALID FOR THIS STRATEGY. Reordering blocks preserves
    volatility clustering inside a block and destroys it at every seam -- and
    position size here is risk / (1 x ATR at entry), so a trade sized on the
    tail of a quiet block that runs into a violent one books an enormous R. The
    trailing leg has no target to cap it. Measured: the same 150 combinations
    scored a median expectancy of -0.004R and a MAXIMUM OF 5.95R with profit
    factor 25.9 on block-shuffled data, against a maximum of 0.129R on the real
    series. A control that is forty times easier than reality is not a floor,
    it is a way of failing everything. Sign randomisation cannot do that: it
    never moves a bar, so ATR at entry always describes the same market that
    follows it.

    OHLC is rebuilt from the flipped path with each bar keeping its own shape
    (its range, and where it opened and closed within it), mirrored when the
    block's sign flips.
    """
    o, h, l, c = (d[k].values.astype(float) for k in ('open', 'high', 'low', 'close'))
    n = len(c)
    lc = np.log(c)
    r = np.diff(lc, prepend=lc[0])
    nb = int(np.ceil(n / BLOCK))
    sign = np.repeat(rng.choice(np.array([-1.0, 1.0]), size=nb), BLOCK)[:n]
    nc = np.exp(lc[0] + np.cumsum(r * sign))
    # each bar's shape, in log space, mirrored where the sign flipped
    up, dn = np.log(h / c), np.log(l / c)
    op = np.log(o / c)
    hi = np.where(sign > 0, up, -dn)
    lo = np.where(sign > 0, dn, -up)
    out = pd.DataFrame({'open': nc * np.exp(op * sign), 'high': nc * np.exp(hi),
                        'low': nc * np.exp(lo), 'close': nc,
                        'suspect': False}, index=d.index)
    out['high'] = np.maximum.reduce([out.open, out.high, out.close])
    out['low'] = np.minimum.reduce([out.open, out.low, out.close])
    return out


def luck_floor(opts, pairs, mode='C', n_surrogate=12, n_combo=400, seed=17,
               verbose=True):
    """The 95th percentile of scrambled-control expectancy, PER SLICE.

    GATING IS PER REGIME, SO THE FLOOR MUST BE TOO. A trend slice and a chop
    slice have different trade counts, different holding periods and different
    R distributions; one pooled floor would be too easy for the slice with more
    trades and too hard for the other.

    A FLOOR IS A PROPERTY OF THE EXACT SETUP IT GATES. This one is measured on
    OANDA mid, with regime slicing, at the frozen ATR length -- the same
    configuration gate 1 runs. The earlier figure of 0.042854 was measured
    before slicing existed and does not transfer.

    The surrogate keeps the REAL Layer 1 labels while the prices are
    sign-scrambled. That is deliberate: the label then partitions the bars in a
    way unrelated to the scrambled path, so the control asks exactly the right
    question -- can this combination beat luck inside an arbitrary partition of
    bars? Scrambling the labels as well would test a different, easier thing.
    """
    import random as _rnd
    kwm = mode_kw(mode)
    opts = mode_opts(opts, mode)
    rng = np.random.default_rng(seed)
    pick = _rnd.Random(seed)
    combos = [(pick.choice(opts['c1']), pick.choice(opts['c2']),
               pick.choice(opts['vol']), pick.choice(opts['base']),
               pick.choice(opts['exit_ind'])) for _ in range(n_combo)]
    vals = {s: [] for s, _, _ in SLICES}
    raw = []          # every eligible control score, both metrics. ADDITIVE:
                      # `vals` is built exactly as before, so the percentiles
                      # this returns are unchanged to the last bit.
    for k in range(n_surrogate):
        PD, BUF = {}, {}
        for p in pairs:
            real = load_pair(p)
            d = surrogate(real, rng)
            P = _precompute_frame(d, opts)
            P['regime'] = regime_codes(p, real.index)   # real labels, kept
            P['_wb'] = window_bounds(P)
            PD[p] = P; BUF[p] = make_buffers(len(P['c']))
        got = {s: 0 for s in vals}
        for cb in combos:
            sc = score_combo(PD, cb, BUF, **kwm)
            for sname in vals:
                if eligible(sc[sname]):
                    vals[sname].append(sc[sname]['expectancy_R'])
                    raw.append(dict(surrogate=k, slice=sname,
                                    expectancy_R=sc[sname]['expectancy_R'],
                                    profit_factor=sc[sname]['profit_factor'],
                                    n_blind=sc[sname]['n_blind']))
                    got[sname] += 1
        if verbose:
            print('  surrogate %2d/%d: eligible %s'
                  % (k + 1, n_surrogate, got), flush=True)
    out = {}
    for sname, v in vals.items():
        a = np.array(v)
        out[sname] = dict(slice=sname, n=len(a),
                          mean=float(a.mean()) if len(a) else np.nan,
                          p50=float(np.percentile(a, 50)) if len(a) else np.nan,
                          p95=float(np.percentile(a, 95)) if len(a) else np.nan,
                          p99=float(np.percentile(a, 99)) if len(a) else np.nan,
                          max=float(a.max()) if len(a) else np.nan)
    pd.DataFrame(raw).to_csv(
        os.path.join(ROOTOUT, 'gate1_null_raw_mode%s.csv' % mode), index=False)
    return out


def null_joint_rate():
    """What fraction of PURE-NOISE slices clears the gate 1 test AS APPLIED?

    The floor is a p95, so 5% of controls clear the expectancy bar by
    construction. But gate 1 ANDs that with PF >= 1.05, and nothing measured
    the joint rate -- which is the only number the survivor counts can honestly
    be compared against. Without it, "7.18% of eligible combinations survived"
    has no reference: 5% is the wrong one, because it is the rate for half the
    test.

    Reads the raw control scores dumped by luck_floor and applies the REAL
    gate, the same expression the sweep worker uses.
    """
    R = pd.read_csv(os.path.join(ROOTOUT, 'gate1_null_raw.csv'))
    F = pd.read_csv(os.path.join(ROOTOUT, 'gate1_luck_floor.csv')).set_index('slice')
    rows = []
    for sname, _, _ in SLICES:
        g = R[R['slice'] == sname]
        floor = float(F.loc[sname, 'p95'])
        exp_only = g['expectancy_R'] > floor
        pf_only = g['profit_factor'] >= PF_FLOOR
        joint = exp_only & pf_only
        rows.append(dict(slice=sname, n_controls=len(g), floor_expectancy_R=floor,
                         pf_floor=PF_FLOOR,
                         null_exp_only_pct=100.0 * exp_only.mean(),
                         null_pf_only_pct=100.0 * pf_only.mean(),
                         null_joint_pct=100.0 * joint.mean()))
    return pd.DataFrame(rows)


# ==========================================================================
# THE HONEST NULL -- fresh controls against the frozen floor
# ==========================================================================
#
# WHY null_joint_rate() ABOVE IS NOT THE ANSWER, despite measuring the right
# expression. It scores the floor-setting controls against their own p95, and
# the fraction of a sample above its own 95th percentile is 5% BY DEFINITION.
# It came back 5.0037% and 5.0136% because it could not have come back anything
# else. What it does establish is real and worth keeping -- that PF >= 1.05 is
# non-binding, since no control clearing the expectancy floor failed it -- but
# the 5% is arithmetic, not evidence.
#
# The floor is an ESTIMATE of the true 95th percentile from 4,097 / 3,311
# draws, so the rate at which FRESH controls clear that fixed number is a free
# parameter of the estimate, not 5%. Getting it wrong in either direction moves
# the reference that 7.18% and 2.34% are judged against, which is the whole
# question. So: new seed, new combination sample, more of them, scored against
# the FROZEN floor read from disk.
NULL_SEED = 20260816


def _null_worker(args):
    k, seed, combos, floors, mode = args
    kwm = mode_kw(mode)
    opts = mode_opts(slot_options(), mode)
    rng = np.random.default_rng([seed, k])       # independent per surrogate
    PD, BUF = {}, {}
    for p in all_pairs():
        real = load_pair(p)
        P = _precompute_frame(surrogate(real, rng), opts)
        P['regime'] = regime_codes(p, real.index)    # real labels, as always
        P['_wb'] = window_bounds(P)
        PD[p] = P; BUF[p] = make_buffers(len(P['c']))
    acc = {s: dict(elig=0, exp=0, pf=0, joint=0) for s, _, _ in SLICES}
    for cb in combos:
        sc = score_combo(PD, cb, BUF, **kwm)
        for sname in acc:
            s = sc[sname]
            if not eligible(s):
                continue
            a = acc[sname]
            a['elig'] += 1
            e = s['expectancy_R'] > floors[sname]
            f = s['profit_factor'] >= PF_FLOOR
            a['exp'] += bool(e); a['pf'] += bool(f); a['joint'] += bool(e and f)
    return acc


def null_fresh(mode, n_surrogate=32, n_combo=1200, jobs=None, seed=NULL_SEED):
    """The rate at which PURE NOISE clears the gate 1 test as applied.

    Fresh surrogates, a fresh combination sample, scored against the frozen
    floor. This is the number 7.18% and 2.34% must be compared against.
    """
    import multiprocessing as mp, random as _rnd
    opts = mode_opts(slot_options(), mode)
    F = pd.read_csv(floor_path(mode)).set_index('slice')
    floors = {s: float(F.loc[s, 'p95']) for s, _, _ in SLICES}
    pick = _rnd.Random(seed + ord(mode))     # a fresh sample per mode
    combos = [(pick.choice(opts['c1']), pick.choice(opts['c2']),
               pick.choice(opts['vol']), pick.choice(opts['base']),
               pick.choice(opts['exit_ind'])) for _ in range(n_combo)]
    jobs = jobs or max(1, (os.cpu_count() or 2) - 2)
    print('null: %d surrogates x %d combos, %d workers, floors %s'
          % (n_surrogate, n_combo, jobs, floors), flush=True)
    tot = {s: dict(elig=0, exp=0, pf=0, joint=0) for s, _, _ in SLICES}
    with mp.Pool(jobs) as pool:
        for i, acc in enumerate(pool.imap_unordered(
                _null_worker,
                [(k, seed + ord(mode), combos, floors, mode)
                 for k in range(n_surrogate)])):
            for s in tot:
                for key in tot[s]:
                    tot[s][key] += acc[s][key]
            print('  surrogate %2d/%d done' % (i + 1, n_surrogate), flush=True)
    rows = []
    for sname, _, _ in SLICES:
        a = tot[sname]
        n = a['elig']
        p = a['joint'] / n if n else np.nan
        se = float(np.sqrt(p * (1 - p) / n)) if n else np.nan
        rows.append(dict(mode=mode, slice=sname, n_controls=n,
                         floor_expectancy_R=floors[sname],
                         null_exp_only_pct=100.0 * a['exp'] / n if n else np.nan,
                         null_pf_only_pct=100.0 * a['pf'] / n if n else np.nan,
                         null_joint_pct=100.0 * p,
                         se_pct=100.0 * se,
                         ci95_lo_pct=100.0 * (p - 1.96 * se),
                         ci95_hi_pct=100.0 * (p + 1.96 * se)))
    return pd.DataFrame(rows)


def _precompute_frame(d, opts, atr_len=None):
    atr_len = ATR_LEN if atr_len is None else atr_len
    o, h, l, c = (d[k].values.astype(float) for k in ('open', 'high', 'low', 'close'))
    P = {'dates': d.index, 'o': o, 'h': h, 'l': l, 'c': c,
         'atr': L.P.atr(h, l, c, atr_len), 'suspect': np.zeros(len(d), bool)}
    conf = {}
    for name in sorted(set(opts['c1']) | set(opts['c2'])):
        lt, st, lc, sc = L.compute(name, o, h, l, c)
        conf[name] = (lt, st, lc, sc, L.KIND[name] == 'TERNARY')
    P['conf'] = conf
    P['vol'] = {n_: L.compute(n_, o, h, l, c) for n_ in opts['vol']}
    P['base'] = {n_: L.compute(n_, o, h, l, c) for n_ in opts['base']}
    P['exit'] = {n_: L.compute(n_, o, h, l, c) for n_ in opts['exit_ind']}
    return P


def all_pairs():
    return sorted(os.path.basename(f)[:-8]
                  for f in glob.glob(os.path.join(OANDA, '*_mid.csv')))


# ==========================================================================
# the sharded runner
# ==========================================================================
def combo_iter(opts):
    """Deterministic enumeration order. A shard is a contiguous slice of THIS
    order, so a resumed run reproduces the same combinations in the same slots
    -- which is what makes the checkpoints meaningful rather than merely
    present."""
    return itertools.product(opts['c1'], opts['c2'], opts['vol'],
                             opts['base'], opts['exit_ind'])


def n_combos(opts):
    n = 1
    for k in ('c1', 'c2', 'vol', 'base', 'exit_ind'):
        n *= len(opts[k])
    return n


def _worker(args):
    shard, nshard, floors, keep_all, mode = args
    kwm = mode_kw(mode)
    opts = mode_opts(slot_options(), mode)
    pairs = all_pairs()
    PD, BUF = {}, {}
    for p in pairs:
        P = precompute(p, opts); P['_wb'] = window_bounds(P)
        PD[p] = P; BUF[p] = make_buffers(len(P['c']))

    # ---- the instrumentation ------------------------------------------
    # PER-OPTION ELIGIBILITY is the point of this pass. The first sweep tallied
    # eligibility per SLICE only, so the enrichment map had to use "all
    # combinations" as its denominator and could not tell an option that FIRES
    # MORE from one that WINS MORE. These counters give the eligible
    # denominator, and enrichment computed on it is a statement about edge
    # rather than about trade frequency.
    ix = {slot: {name: j for j, name in enumerate(opts[slot])} for slot in SLOTS}
    n_elig_opt = {s: {slot: np.zeros(len(opts[slot]), np.int64) for slot in SLOTS}
                  for s, _, _ in SLICES}
    n_surv_opt = {s: {slot: np.zeros(len(opts[slot]), np.int64) for slot in SLOTS}
                  for s, _, _ in SLICES}
    n_comb_opt = {s: {slot: np.zeros(len(opts[slot]), np.int64) for slot in SLOTS}
                  for s, _, _ in SLICES}
    # HOW TRADES CLOSE, over eligible combinations, and split by exit_ind so the
    # question "is the exit slot weak or merely never reached?" is answerable.
    rc_elig = {s: np.zeros(N_REASON, np.int64) for s, _, _ in SLICES}
    rc_surv = {s: np.zeros(N_REASON, np.int64) for s, _, _ in SLICES}
    rc_by_exit = {s: np.zeros((len(opts['exit_ind']), N_REASON), np.int64)
                  for s, _, _ in SLICES}

    out = []
    n_seen = 0
    n_elig = {s: 0 for s, _, _ in SLICES}
    n_surv = {s: 0 for s, _, _ in SLICES}
    t0 = time.time()
    for i, cb in enumerate(combo_iter(opts)):
        if i % nshard != shard:
            continue
        n_seen += 1
        cbi = [ix[slot][v] for slot, v in zip(SLOTS, cb)]
        # heartbeat. A shard is tens of thousands of combinations and takes
        # tens of minutes; without this the only signal that anything is
        # happening is the shard file appearing at the very end, which is
        # useless for spotting a machine that has started thrashing.
        if n_seen % 5000 == 0:
            el = time.time() - t0
            print('    shard %4d: %6d done, %.2f ms/combo, %.0f min left'
                  % (shard, n_seen, 1000 * el / n_seen,
                     (el / n_seen) * (nshard and (n_combos(opts) // nshard)
                                      - n_seen) / 60), flush=True)
        sc = score_combo(PD, cb, BUF, want_reasons=True, **kwm)
        for sname, _, _ in SLICES:
            s = sc[sname]
            rc = s.pop('_rc')          # never reaches the survivors CSV
            for slot, j in zip(SLOTS, cbi):
                n_comb_opt[sname][slot][j] += 1
            if not eligible(s):
                continue
            n_elig[sname] += 1
            for slot, j in zip(SLOTS, cbi):
                n_elig_opt[sname][slot][j] += 1
            rc_elig[sname] += rc
            rc_by_exit[sname][cbi[4]] += rc
            if keep_all or (s['expectancy_R'] > floors[sname]
                            and s['profit_factor'] >= PF_FLOOR):
                n_surv[sname] += 1
                for slot, j in zip(SLOTS, cbi):
                    n_surv_opt[sname][slot][j] += 1
                rc_surv[sname] += rc
                out.append(s)
    pd.DataFrame(out).to_csv(
        os.path.join(mode_dir(mode), 'shard_%04d.csv' % shard), index=False)
    # tallies alongside the survivors, one npz per shard, same resume rule
    tal = {}
    for sname, _, _ in SLICES:
        for slot in SLOTS:
            tal['comb_%s_%s' % (sname, slot)] = n_comb_opt[sname][slot]
            tal['elig_%s_%s' % (sname, slot)] = n_elig_opt[sname][slot]
            tal['surv_%s_%s' % (sname, slot)] = n_surv_opt[sname][slot]
        tal['rc_elig_%s' % sname] = rc_elig[sname]
        tal['rc_surv_%s' % sname] = rc_surv[sname]
        tal['rc_by_exit_%s' % sname] = rc_by_exit[sname]
    np.savez_compressed(
        os.path.join(mode_dir(mode), 'tally_%04d.npz' % shard), **tal)
    return dict(shard=shard, seen=n_seen,
                elig_trend=n_elig['trend'], elig_chop=n_elig['chop'],
                surv_trend=n_surv['trend'], surv_chop=n_surv['chop'])


def run_gate1(floors, mode, nshard=None, jobs=None, keep_all=False, limit=None):
    """Gate 1 across one mode's combinations, BOTH PLANS, sliced. Resumable.

    `floors` is {slice: expectancy floor} FOR THIS MODE. Floors never transfer
    across modes -- the exit rule changes what a trade is, so it changes the
    distribution a control draws from.
    """
    import multiprocessing as mp
    os.makedirs(mode_dir(mode), exist_ok=True)
    opts = mode_opts(slot_options(), mode)
    total = n_combos(opts)
    jobs = jobs or max(1, (os.cpu_count() or 2) - 2)
    # FEW, LARGE SHARDS. Each worker precomputes all 28 pairs before it can
    # score anything -- ~30 seconds -- so a shard must be big enough for that
    # to disappear into it. Modes A and B are 39x smaller, so they get
    # proportionally fewer shards or the precompute dominates the run.
    if nshard is None:
        nshard = jobs * 4 if total < 1_000_000 else jobs * 16
    todo = [s for s in range(nshard)
            if not (os.path.exists(os.path.join(mode_dir(mode), 'shard_%04d.csv' % s))
                    and os.path.exists(os.path.join(mode_dir(mode), 'tally_%04d.npz' % s)))]
    done = nshard - len(todo)
    if limit:
        todo = todo[:limit]
    print('gate 1 MODE %s (%s): %s combinations, %d shards, %d done, '
          '%d queued, %d workers'
          % (mode, MODES[mode]['label'], format(total, ','), nshard, done,
             len(todo), jobs), flush=True)
    print('  floors: %s   PF >= %.2f' % (floors, PF_FLOOR), flush=True)
    if not todo:
        return collect(mode)
    with mp.Pool(jobs) as pool:
        for r in pool.imap_unordered(
                _worker, [(s, nshard, floors, keep_all, mode) for s in todo]):
            print('  shard %4d: %8d seen | eligible %6d/%6d | survivors '
                  '%5d/%5d  (trend/chop)'
                  % (r['shard'], r['seen'], r['elig_trend'], r['elig_chop'],
                     r['surv_trend'], r['surv_chop']), flush=True)
    return collect(mode)


def collect(mode):
    fs = sorted(glob.glob(os.path.join(mode_dir(mode), 'shard_*.csv')))
    if not fs:
        return pd.DataFrame()
    D = pd.concat([pd.read_csv(f) for f in fs], ignore_index=True)
    if not MODES[mode]['uses_exit_slot']:
        D['exit_ind'] = 'unused'
    D['mode'] = mode
    D.to_csv(os.path.join(ROOTOUT, 'gate1_survivors_mode%s.csv' % mode), index=False)
    return D


def main():
    """CLI. MUST be run as a script, not from stdin -- macOS spawns workers by
    re-importing __main__, and a parent read from stdin has no file to import.

      python code/l2sweep.py --luckfloor --mode A     # six floors, one per
      python code/l2sweep.py --luckfloor --mode all   # slice per mode
      python code/l2sweep.py --sweep --mode all --jobs 8
      python code/l2sweep.py --nullfresh --mode all --jobs 8

    --mode all runs A, B, C in order. Modes A and B are ~2.6% of C's size, so
    running them first gets two complete answers on disk long before C lands.
    """
    a = sys.argv[1:]

    def opt(name, cast, default=None):
        return cast(a[a.index(name) + 1]) if name in a else default

    m = opt('--mode', str, 'all')
    modes = list(MODE_ORDER) if m == 'all' else [x.strip().upper()
                                                 for x in m.split(',')]
    for x in modes:
        if x not in MODES:
            raise SystemExit('unknown mode %r; known: %s' % (x, MODE_ORDER))

    if '--luckfloor' in a:
        out = []
        for mode in modes:
            print('\n=== LUCK FLOOR, mode %s (%s) ==='
                  % (mode, MODES[mode]['label']), flush=True)
            f = luck_floor(slot_options(), all_pairs(), mode=mode,
                           n_surrogate=opt('--surrogates', int, 12),
                           n_combo=opt('--combos', int, 400))
            D = pd.DataFrame(f.values())
            D.insert(0, 'mode', mode)
            D.to_csv(floor_path(mode), index=False)
            print(D.to_string(index=False))
            for r in D.itertuples():
                print('  expectancy bar, mode %s %-5s = %.6f R'
                      % (mode, r.slice, r.p95))
            out.append(D)
        A = pd.concat(out, ignore_index=True)
        A.to_csv(os.path.join(ROOTOUT, 'gate1_luck_floors_all.csv'), index=False)
        print('\nALL SIX FLOORS')
        print(A[['mode', 'slice', 'n', 'p95']].to_string(index=False))
        return A

    if '--nullfresh' in a:
        out = []
        for mode in modes:
            if not os.path.exists(floor_path(mode)):
                raise SystemExit('mode %s floor missing: %s' % (mode, floor_path(mode)))
            print('\n=== FRESH NULL, mode %s ===' % mode, flush=True)
            J = null_fresh(mode, n_surrogate=opt('--surrogates', int, 32),
                           n_combo=opt('--combos', int, 1200),
                           jobs=opt('--jobs', int))
            print(J.to_string(index=False))
            out.append(J)
        A = pd.concat(out, ignore_index=True)
        A.to_csv(os.path.join(ROOTOUT, 'gate1_null_fresh_all.csv'), index=False)
        print('\nTRUE NULL PASS RATES, fresh controls vs each mode\'s frozen floor')
        print(A.to_string(index=False))
        return A

    # ---- the sweep itself ------------------------------------------------
    for mode in modes:
        if not os.path.exists(floor_path(mode)):
            raise SystemExit(
                'mode %s has no floor. Floors do not transfer across modes; run\n'
                '  python code/l2sweep.py --luckfloor --mode %s' % (mode, mode))
    summary = []
    for mode in modes:
        F = pd.read_csv(floor_path(mode)).set_index('slice')
        floors = {s: float(F.loc[s, 'p95']) for s, _, _ in SLICES}
        t = time.time()
        D = run_gate1(floors, mode, nshard=opt('--shards', int, None),
                      jobs=opt('--jobs', int), keep_all='--keep-all' in a,
                      limit=opt('--limit', int))
        el = time.time() - t
        print('\nMODE %s: %d surviving slices in %.0fs (%.2f h)'
              % (mode, len(D), el, el / 3600), flush=True)
        if len(D):
            print(D.groupby('slice').size().to_string(), flush=True)
        summary.append(dict(mode=mode, label=MODES[mode]['label'],
                            survivors=len(D), seconds=round(el, 1)))
    pd.DataFrame(summary).to_csv(
        os.path.join(ROOTOUT, 'gate1_mode_runs.csv'), index=False)
    return summary


if __name__ == '__main__':
    main()


# ==========================================================================
# ATR LENGTH PRE-TEST -- run once, before gate 1, then frozen
# ==========================================================================
ATR_RANGE = range(2, 51)


def spread_sample(opts, n=300, seed=101):
    """A sample that COVERS the slots rather than merely being random.

    Each slot's options are cycled with a different stride, so every option in
    every slot appears a similar number of times. A plain random draw of 300
    from 10.7M would leave whole indicators unrepresented, and the ATR length
    would then be chosen on whichever ones happened to be picked.
    """
    keys = ('c1', 'c2', 'vol', 'base', 'exit_ind')
    lists = {k: sorted(opts[k]) for k in keys}
    rng = np.random.default_rng(seed)
    order = {k: rng.permutation(len(lists[k])) for k in keys}
    combos = []
    for i in range(n):
        combos.append(tuple(lists[k][int(order[k][i % len(lists[k])])] for k in keys))
    return combos


def score_w1(pairs_data, combo, buf_by_pair, atr_by_pair):
    """PICKING WINDOW ONLY, sliced. The pre-test may not look at W2 or W3 --
    they are blind and stay blind, and a parameter chosen on them would make
    every later blind score a re-read of its own tuning set."""
    c1, c2, vol, base, ex = combo
    out = {}
    for sname, plan, code in SLICES:
        rr = []
        for pair, P in pairs_data.items():
            buf = buf_by_pair[pair]
            nt = run_combo(P, c1, c2, vol, base, ex, buf, plan=plan,
                           atr=atr_by_pair[pair])
            if nt == 0:
                continue
            eb = buf['entry_bar'][:nt]
            a1, z1 = P['_wb']['W1']
            m = (P['regime'][eb] == code) & (eb >= a1) & (eb < z1)
            if m.any():
                rr.append(buf['r'][:nt][m])
        out[sname] = np.concatenate(rr) if rr else np.zeros(0)
    return out


def atr_pretest(n_combo=300, verbose=True):
    """Every ATR length 2-50 on a spread sample, picking window only, both
    plans, all 28 pairs. Ranked on pooled expectancy in R, PF as tiebreak."""
    opts = slot_options()
    pairs = all_pairs()
    combos = spread_sample(opts, n_combo)
    PD, BUF = {}, {}
    for p in pairs:
        P = precompute(p, opts); P['_wb'] = window_bounds(P)
        PD[p] = P; BUF[p] = make_buffers(len(P['c']))
    rows = []
    for n in ATR_RANGE:
        atr = {p: L.P.atr(PD[p]['h'], PD[p]['l'], PD[p]['c'], n) for p in pairs}
        acc = {s: [] for s, _, _ in SLICES}
        for cb in combos:
            r = score_w1(PD, cb, BUF, atr)
            for s in acc:
                if r[s].size:
                    acc[s].append(r[s])
        row = dict(atr_len=n)
        allr = []
        for s in acc:
            v = np.concatenate(acc[s]) if acc[s] else np.zeros(0)
            allr.append(v)
            row['%s_n' % s] = len(v)
            row['%s_exp' % s] = float(v.mean()) if len(v) else np.nan
        v = np.concatenate(allr) if allr else np.zeros(0)
        win = v > 0
        gain = float(v[win].sum()); loss = float(-v[~win].sum())
        row.update(n=len(v), expectancy_R=float(v.mean()) if len(v) else np.nan,
                   profit_factor=(gain / loss) if loss > 0 else np.inf)
        rows.append(row)
        if verbose:
            print('  ATR %2d: n=%6d  expectancy %+.5f  PF %.4f  '
                  '(trend %+.5f / chop %+.5f)'
                  % (n, row['n'], row['expectancy_R'], row['profit_factor'],
                     row['trend_exp'], row['chop_exp']), flush=True)
    return pd.DataFrame(rows)


def choose_atr(D, plateau=5):
    """THE RULE, exactly as specified: rank on pooled expectancy in R with
    profit factor as the tiebreak, and take the winner -- UNLESS the winner is a
    SPIKE, in which case take the centre of the best plateau instead.

    A spike means one ATR value standing above its neighbours: one number where
    stops happened to land where a handful of trades survived. A plateau means
    the result does not depend on the exact value, which is what a real effect
    looks like. The test for "spike" is whether the raw winner falls inside the
    best rolling window of `plateau` consecutive lengths. If it does, the curve
    around it is broad and the winner is kept. If it does not, the winner is an
    isolated peak and the plateau centre is used.
    """
    d = D.sort_values(['expectancy_R', 'profit_factor'], ascending=False)
    raw = int(d.atr_len.iloc[0])
    e = D.expectancy_R.values
    k = plateau
    roll = np.convolve(e, np.ones(k) / k, mode='valid')
    j = int(np.argmax(roll))
    lo, hi = int(D.atr_len.values[j]), int(D.atr_len.values[j + k - 1])
    centre = int(D.atr_len.values[j + k // 2])
    spike = not (lo <= raw <= hi)
    return dict(chosen=centre if spike else raw, raw_best=raw,
                plateau_from=lo, plateau_to=hi, plateau_mean=float(roll[j]),
                spike=spike, rule='plateau centre (winner spiked)' if spike
                else 'raw winner (it sits inside the best plateau)',
                curve_min=float(e.min()), curve_max=float(e.max()),
                curve_range_in_SE=float((e.max() - e.min())
                                        / (0.6 / np.sqrt(D.n.mean()))),
                trend_best=int(D.atr_len.values[int(np.argmax(D.trend_exp.values))]),
                chop_best=int(D.atr_len.values[int(np.argmax(D.chop_exp.values))]),
                trend_corr=float(np.corrcoef(D.atr_len, D.trend_exp)[0, 1]),
                chop_corr=float(np.corrcoef(D.atr_len, D.chop_exp)[0, 1]))
