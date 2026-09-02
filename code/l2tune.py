import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""GATE 2 — TUNE. Per-combination coordinate descent, built to GAUNTLET.md.

READ GAUNTLET.md GATE 2 FIRST. Every grid and rule here is specified there and
may not be edited once results exist.

------------------------------------------------------------------------
THE MACHINE, AND WHERE THE HONESTY LIVES
------------------------------------------------------------------------
    tune on W1        -> trade W2 BLIND
    re-tune on W1+W2  -> trade W3 BLIND
    score = stitched blind (W2 from the first tune, W3 from the second)

The tuner never sees W2 while choosing the values it trades W2 with, and never
sees W3 at all while choosing. W4 is not importable from this module.

GATE 2 KILLS NOTHING. It writes a label and a tuned parameter set. Every
combination that entered leaves.

------------------------------------------------------------------------
COORDINATE DESCENT, AND THE ADOPTION RULE
------------------------------------------------------------------------
One knob at a time in priority order, everything else held, then a second full
pass to settle interactions. A grid value is ADOPTED ONLY IF IT BEATS THE
DEFAULT on the tuning window -- expectancy in R, profit factor as tiebreak,
minimum-trade rules enforced. A knob that finds nothing better keeps its
default, and that is a result rather than a failure.

This is deliberately not a search for the best point in the joint space. It is
a cheap, order-dependent walk, and the order is declared in the spec so the
dependence is a stated property rather than a hidden one.

------------------------------------------------------------------------
THE CACHE, WHICH IS WHAT MAKES THIS FINISH
------------------------------------------------------------------------
Indicator series are keyed (name, param-tuple, pair) and shared across every
combination and every tuning step. Only the knob being moved recomputes. Every
combination starts from defaults, so the default series are the hottest entries
and are pinned; explored variants go in an LRU behind them.

Measured on this data: recomputing one confirmation indicator across 28 pairs
costs ~326 ms, scoring a combination costs ~4.7 ms. Without the cache the
recompute dominates by seventy to one, which is the whole reason it exists.

------------------------------------------------------------------------
RESUME
------------------------------------------------------------------------
Work is chunked by combination index. A chunk writes results/gate2/<mode>/
chunk_XXXXX.csv and is skipped if that file exists, so a killed or
power-lost run costs one chunk. Progress, engine-hours and label crossings are
appended to results/gate2_progress_<mode>.csv on every chunk.
"""
import glob, json, time, collections
import numpy as np, pandas as pd

import l2lib as L
import l2engine as E
import l2sweep as S
import l2cache as DC

CK = os.path.join(ROOTOUT, 'gate2')

# ---- grids, exactly as GAUNTLET.md specifies -----------------------------
def _rng(a, b, st):
    out, x = [], a
    while x <= b + 1e-9:
        out.append(round(x, 10)); x += st
    return out

GRID_STOP   = _rng(1.00, 1.25, 0.05) + _rng(1.26, 1.50, 0.01)
GRID_TP     = _rng(1.00, 3.00, 0.05)
GRID_BE     = _rng(0.01, 0.20, 0.01)          # % OF PRICE beyond TP1
GRID_ARM    = _rng(1.00, 2.00, 0.05)
GRID_TRAIL  = _rng(0.50, 2.00, 0.05)
GRID_ATR    = list(range(2, 51))

RISK_KNOBS_TREND = (('atr_len', GRID_ATR), ('atr_mult', GRID_STOP),
                    ('tp_mult', GRID_TP), ('be_pct', GRID_BE),
                    ('trail_arm', GRID_ARM), ('trail_mult', GRID_TRAIL))
RISK_KNOBS_CHOP  = (('atr_len', GRID_ATR), ('atr_mult', GRID_STOP),
                    ('tp_mult', GRID_TP))

SLOT_ORDER = ('vol', 'base', 'c1', 'c2', 'exit_ind')     # spec priority
N_IND_PTS = 12

# GAUNTLET.md mode C shape, declared before any C tuning existed.
CAP_N = 6                 # tune only each indicator's 6 highest-impact params
CHEAP_RISK = ('atr_len', 'atr_mult', 'tp_mult')
DEEPEN_THRESHOLD_R = 0.02  # cheap-pass improvement that buys the deep pass

_RANK = None
def ranking():
    """{indicator: [params, most impactful first]}, MEASURED by l2impact and
    frozen before mode C ran. Asserting an impact order from documentation
    would make the cap a guess dressed as a measurement."""
    global _RANK
    if _RANK is None:
        import l2impact
        _RANK = l2impact.load_ranking()
    return _RANK


def tuned_params(name, cap=None, top1=False):
    """Which parameters of `name` this pass is allowed to move."""
    allp = sorted(registry()[name])
    if not allp:
        return []
    order = [x for x in ranking().get(name, allp) if x in allp]
    order += [x for x in allp if x not in order]
    if top1:
        return order[:1]
    return order[:cap] if cap else order

# gate 2 label -- a SORTING LABEL, never a kill switch
LABEL = dict(expectancy_R=0.08, profit_factor=1.25, sharpe=0.5,
             sortino=0.7, calmar=0.6, max_dd_pct=20.0)


def ind_param_grid(default):
    """1/10x to 10x the default, ~12 log-spaced points. Integer-valued defaults
    are treated as periods: rounded and floored at 2. Deduplicated, and the
    default is always present so 'beats the default' is a real comparison."""
    if default is None or default == 0:
        return [default]
    lo, hi = abs(default) / 10.0, abs(default) * 10.0
    pts = np.exp(np.linspace(np.log(lo), np.log(hi), N_IND_PTS))
    if float(default).is_integer():
        pts = np.maximum(2, np.round(pts)).astype(int)
        vals = sorted(set(int(v) for v in pts) | {int(default)})
    else:
        sign = -1.0 if default < 0 else 1.0
        vals = sorted(set([round(sign * float(v), 6) for v in pts]
                          + [float(default)]))
    return vals


_REG = None
def registry():
    global _REG
    if _REG is None:
        import re
        R = L.registry_frame()
        d = {}
        for r in R[R.available].itertuples():
            p = {}
            if isinstance(r.defaults, str):
                for tok in re.split(r'[,;]', r.defaults):
                    if '=' in tok:
                        k, v = tok.split('=', 1)
                        try:
                            fv = float(v.strip())
                        except ValueError:
                            continue
                        p[k.strip()] = int(fv) if fv.is_integer() else fv
            d[r.name] = p
        _REG = d
    return _REG


# ==========================================================================
# the cache
# ==========================================================================
class SeriesCache:
    """(indicator, param-tuple, pair) -> computed series.

    Default-parameter entries are PINNED: every combination starts from
    defaults and returns to them for every knob it declines to move, so they
    are hit constantly and must never be evicted by a burst of exploration.
    """
    def __init__(self, cap=600, disk=False):
        self.pin = {}
        self.lru = collections.OrderedDict()
        self.cap = cap
        self.disk = disk
        self.hits = self.misses = self.disk_hits = 0

    def get(self, name, params, pair, arrays):
        key = (name, tuple(sorted(params.items())), pair)
        defaults = registry()[name]
        pinned = (params == defaults)
        d = self.pin if pinned else self.lru
        if key in d:
            self.hits += 1
            if not pinned:
                d.move_to_end(key)
            return d[key]
        self.misses += 1
        o, h, l, c = arrays
        val = None
        if self.disk:
            # A disk hit is ~0.1 ms against an ~11.6 ms recompute, so it is
            # worth a stat() even when it misses.
            val = DC.get(name, params, pair)
            if val is not None:
                self.disk_hits += 1
        if val is None:
            val = L.compute(name, o, h, l, c, **params)
            if self.disk:
                DC.put(name, params, pair, val)
        if pinned:
            self.pin[key] = val
        else:
            self.lru[key] = val
            while len(self.lru) > self.cap:
                self.lru.popitem(last=False)
        return val


# ==========================================================================
# scoring one configuration
# ==========================================================================
def _agg(r):
    n = len(r)
    if n == 0:
        return None
    tot = float(r.sum()); mean = tot / n
    gp = float(r[r > 0].sum()); gl = float(-r[r < 0].sum())
    pf = gp / gl if gl > 0 else (np.inf if gp > 0 else 0.0)
    sd = float(r.std(ddof=1)) if n > 1 else 0.0
    # SORTINO IS UNDEFINED WHEN DOWNSIDE DEVIATION IS ZERO, and here that is a
    # STRUCTURAL case rather than a rare one: every full-stop loss is exactly
    # the same R by construction, so a combination whose losses are all full
    # stops has identically-valued negative returns and zero downside spread.
    # Dividing by it produced Sortinos of 1e15 -- and Sortino is half the final
    # ranking rule, so an undefined value would rank first by definition.
    # Reported as NaN and ranked last, never as a number.
    neg = r[r < 0]
    dn = float(neg.std(ddof=1)) if len(neg) > 1 else 0.0
    scale = float(np.abs(r).mean()) or 1.0
    if dn <= 1e-9 * scale:
        dn = 0.0
    eq = np.cumsum(r); ddv = np.maximum.accumulate(eq) - eq
    dd = float(ddv.max())
    # Ulcer index in R: the root-mean-square drawdown, which unlike max DD is
    # not decided by one bad day. Diagnostic; no floor is set on it.
    ulcer = float(np.sqrt(np.mean(ddv ** 2)))
    return dict(n=n, expectancy_R=mean, total_R=tot, profit_factor=pf,
                win_rate=float((r > 0).mean()),
                sharpe=(mean / sd * np.sqrt(252)) if sd > 0 else 0.0,
                sortino=(mean / dn * np.sqrt(252)) if dn > 0 else np.nan,
                max_dd_R=dd, ulcer_R=ulcer,
                calmar=(tot / dd) if dd > 0 else 0.0, _r=r)


class Scorer:
    """Holds the per-pair raw series and the cache, and scores one full
    configuration across all 28 pairs, split by window."""

    def __init__(self, cache=None, disk=False):
        self.pairs = S.all_pairs()
        self.raw, self.arr, self.reg, self.wb, self.buf = {}, {}, {}, {}, {}
        for p in self.pairs:
            d = S.load_pair(p)
            self.raw[p] = d
            self.arr[p] = tuple(d[k].values.astype(float)
                                for k in ('open', 'high', 'low', 'close'))
            self.reg[p] = S.regime_codes(p, d.index)
            idx = d.index
            b = {}
            for k, (a, z) in S.WINDOWS.items():
                m = (idx >= a) & (idx <= z)
                w = np.flatnonzero(m)
                b[k] = (int(w[0]), int(w[-1]) + 1) if len(w) else (0, 0)
            self.wb[p] = b
            self.buf[p] = S.make_buffers(len(d))
        self.cache = cache or SeriesCache(disk=disk)
        self.n_eval = 0
        # ATR depends only on (atr_len, pair) and atr_len is ONE knob out of
        # ~320, so recomputing it on every score was pure waste -- measured at
        # roughly a third of the cost of a score.
        self._atr = {}
        # hoisted per-pair constants: allocating a fresh suspect array and
        # re-reading L.KIND inside the pair loop cost more than they look like
        # at 28 pairs x hundreds of scores per combination.
        self._nosus = {p: np.zeros(len(self.arr[p][3]), bool) for p in self.pairs}

    def score(self, combo, ip, risk, mode, sname, code, plan, windows):
        """One configuration. `ip` maps slot -> params dict. Returns
        {window: agg} over trades ENTERED in that window, in this slice."""
        self.n_eval += 1
        c1, c2, vol, base, ex = combo
        kwm = S.mode_kw(mode)
        out = {w: [] for w in windows}
        alen = int(risk['atr_len'])
        t1 = L.KIND[c1] == 'TERNARY'
        t2 = L.KIND[c2] == 'TERNARY'
        for p in self.pairs:
            o, h, l, c = self.arr[p]
            ak = (alen, p)
            atr = self._atr.get(ak)
            if atr is None:
                atr = L.P.atr(h, l, c, alen)
                self._atr[ak] = atr
            g = self.cache.get
            lt, st, lc, sc = g(c1, ip['c1'], p, self.arr[p])[:4]
            _, _, c2lc, c2sc = g(c2, ip['c2'], p, self.arr[p])[:4]
            vl, vs = g(vol, ip['vol'], p, self.arr[p])[:2]
            bl = g(base, ip['base'], p, self.arr[p])
            bl = bl[0] if isinstance(bl, tuple) else bl
            el, es = g(ex, ip['exit_ind'], p, self.arr[p])[:2]
            b = self.buf[p]
            nt, _, _, _ = E.run_bars(
                o, h, l, c, atr, bl, lt, st, lc, sc, c2lc, c2sc, vl, vs,
                el, es, self._nosus[p],
                t1, t2,
                True, True, True,
                kwm['exit_on_c1_flip'], kwm['exit_on_base_cross'],
                kwm['exit_on_exit_ind'], False,
                int(plan), S.RISK,
                float(risk['atr_mult']), float(risk['tp_mult']),
                float(risk['trail_mult']), float(risk['trail_arm']),
                float(risk['be_pct']), 1.5, 7, True, True,
                b['entry_bar'], b['exit_bar'], b['dir'], b['leg'],
                b['entry_px'], b['exit_px'], b['units'], b['r'],
                b['reason'], b['route'])
            if nt == 0:
                continue
            r = b['r'][:nt]; eb = b['entry_bar'][:nt]
            m = self.reg[p][eb] == code
            if not m.any():
                continue
            for w in windows:
                a, z = self.wb[p][w]
                mm = m & (eb >= a) & (eb < z)
                if mm.any():
                    out[w].append(r[mm])
        return {w: (_agg(np.concatenate(v)) if v else None)
                for w, v in out.items()}


def better(cand, base_, min_trades):
    """Expectancy in R, profit factor as tiebreak, min-trade rule enforced."""
    if cand is None or cand['n'] < min_trades:
        return False
    if base_ is None:
        return True
    if cand['expectancy_R'] > base_['expectancy_R'] + 1e-12:
        return True
    if abs(cand['expectancy_R'] - base_['expectancy_R']) <= 1e-12:
        return cand['profit_factor'] > base_['profit_factor'] + 1e-12
    return False


def tune_one(sc, combo, mode, sname, code, plan, tune_windows, defaults_ip,
             defaults_risk, passes=2, cap=None, cheap=False, skip=None,
             seeds=None):
    """Coordinate descent over one combination on one tuning window set.

    cap    -- move only each indicator's top-`cap` measured parameters
    cheap  -- the staged pass: ATR/stop/target plus the single most impactful
              parameter of each indicator, full grids
    skip   -- (ip, risk) already-banked starting point, so a deep pass RESUMES
              from a cheap pass rather than redoing it
    """
    ip = {k: dict(v) for k, v in (skip[0] if skip else defaults_ip).items()}
    risk = dict(skip[1] if skip else defaults_risk)
    slots = [s for s in SLOT_ORDER
             if (s != 'exit_ind' or S.MODES[mode]['uses_exit_slot'])]
    riskknobs = RISK_KNOBS_TREND if sname == 'trend' else RISK_KNOBS_CHOP
    if cheap:
        riskknobs = tuple(k for k in riskknobs if k[0] in CHEAP_RISK)
        passes = 1

    def ev():
        r = sc.score(combo, ip, risk, mode, sname, code, plan, tune_windows)
        parts = [r[w] for w in tune_windows if r[w] is not None]
        if not parts:
            return None
        n = sum(p['n'] for p in parts)
        e = sum(p['expectancy_R'] * p['n'] for p in parts) / n
        pf = np.mean([p['profit_factor'] for p in parts])
        return dict(n=n, expectancy_R=e, profit_factor=pf)

    cur = ev()
    for _ in range(passes):
        for slot in slots:
            name = combo[SLOT_ORDER.index(slot)] if slot in SLOT_ORDER else None
            name = dict(zip(('c1', 'c2', 'vol', 'base', 'exit_ind'), combo))[slot]
            allowed = tuned_params(name, cap=cap, top1=cheap)
            # SEEDED CANDIDATES for parameters this pass would otherwise freeze.
            # Only reachable when a cap is in force and only for values another
            # mode actually adopted; never narrows a grid, never inherits
            # untested.
            if seeds:
                frozen = [x for x in sorted(registry()[name])
                          if x not in allowed and x in seeds.get(slot, {})]
                for pname in frozen:
                    v = seeds[slot][pname]
                    if v == ip[slot].get(pname):
                        continue
                    old = ip[slot].get(pname)
                    ip[slot][pname] = v
                    cand = ev()
                    if better(cand, cur, S.MIN_TRADES_PICK):
                        cur = cand
                    else:
                        ip[slot][pname] = old
            for pname in allowed:
                pdef = registry()[name][pname]
                best, bestv = cur, ip[slot].get(pname, pdef)
                for v in ind_param_grid(pdef):
                    if v == ip[slot].get(pname, pdef):
                        continue
                    old = ip[slot].get(pname, pdef)
                    ip[slot][pname] = v
                    cand = ev()
                    if better(cand, best, S.MIN_TRADES_PICK):
                        best, bestv = cand, v
                    ip[slot][pname] = old
                ip[slot][pname] = bestv
                cur = best
        for kname, grid in riskknobs:
            best, bestv = cur, risk[kname]
            for v in grid:
                if v == risk[kname]:
                    continue
                old = risk[kname]; risk[kname] = v
                cand = ev()
                if better(cand, best, S.MIN_TRADES_PICK):
                    best, bestv = cand, v
                risk[kname] = old
            risk[kname] = bestv
            cur = best
    return ip, risk, cur


# ==========================================================================
# the walk-forward driver
# ==========================================================================
def default_baseline(sc, combo, mode, sname, code, plan, windows):
    dip = {k: dict(registry()[n]) for k, n in
           zip(('c1', 'c2', 'vol', 'base', 'exit_ind'), combo)}
    drisk = dict(atr_len=S.ATR_LEN, atr_mult=S.ATR_MULT, tp_mult=S.TP_MULT,
                 trail_mult=S.TRAIL_MULT, trail_arm=S.TRAIL_ARM,
                 be_pct=S.BE_PCT)
    r = sc.score(combo, dip, drisk, mode, sname, code, plan, windows)
    parts = [r[w] for w in windows if r[w] is not None]
    if not parts:
        return dip, drisk, None
    n = sum(p['n'] for p in parts)
    e = sum(p['expectancy_R'] * p['n'] for p in parts) / n
    return dip, drisk, dict(n=n, expectancy_R=e,
                            profit_factor=float(np.mean([p['profit_factor'] for p in parts])))


def _stage(sc, combo, mode, sname, code, plan, windows, cap, staged,
           resume=None, seeds=None):
    """One tuning step. Returns (ip, risk, info). With `staged`, runs the cheap
    pass first and only continues to the deep pass if the cheap pass improved on
    the DEFAULT by at least DEEPEN_THRESHOLD_R -- the threshold declared in
    GAUNTLET.md before any mode C tuning existed."""
    dip, drisk, base = default_baseline(sc, combo, mode, sname, code, plan, windows)
    if resume is not None:
        ip, risk, cur = tune_one(sc, combo, mode, sname, code, plan, windows,
                                 dip, drisk, cap=cap, skip=resume, seeds=seeds)
        return ip, risk, dict(stage='deep', resumed=True,
                              base_R=(base or {}).get('expectancy_R'),
                              final_R=(cur or {}).get('expectancy_R'))
    if not staged:
        ip, risk, cur = tune_one(sc, combo, mode, sname, code, plan, windows,
                                 dip, drisk, cap=cap, seeds=seeds)
        return ip, risk, dict(stage='full', resumed=False,
                              base_R=(base or {}).get('expectancy_R'),
                              final_R=(cur or {}).get('expectancy_R'))
    ip, risk, cheap = tune_one(sc, combo, mode, sname, code, plan, windows,
                               dip, drisk, cap=cap, cheap=True, seeds=seeds)
    gain = None
    if cheap is not None and base is not None:
        gain = cheap['expectancy_R'] - base['expectancy_R']
    if gain is not None and gain >= DEEPEN_THRESHOLD_R:
        ip2, risk2, deep = tune_one(sc, combo, mode, sname, code, plan, windows,
                                    dip, drisk, cap=cap, skip=(ip, risk), seeds=seeds)
        return ip2, risk2, dict(stage='deep', resumed=False,
                                base_R=base['expectancy_R'],
                                cheap_R=cheap['expectancy_R'], cheap_gain=gain,
                                final_R=(deep or {}).get('expectancy_R'),
                                cheap_ip=json.dumps(ip, sort_keys=True),
                                cheap_risk=json.dumps(risk, sort_keys=True))
    return ip, risk, dict(stage='cheap', resumed=False,
                          base_R=(base or {}).get('expectancy_R'),
                          cheap_R=(cheap or {}).get('expectancy_R'),
                          cheap_gain=gain, final_R=(cheap or {}).get('expectancy_R'),
                          cheap_ip=json.dumps(ip, sort_keys=True),
                          cheap_risk=json.dumps(risk, sort_keys=True))


def full_walk(sc, combo, mode, sname, code, plan, cap=None, staged=False,
              resume1=None, resume2=None, seeds=None):
    """tune W1 -> blind W2 -> re-tune W1+W2 -> blind W3. Stitched blind score."""
    ip1, rk1, i1 = _stage(sc, combo, mode, sname, code, plan, ('W1',),
                          cap, staged, resume=resume1, seeds=seeds)
    w2 = sc.score(combo, ip1, rk1, mode, sname, code, plan, ('W2',))['W2']
    ip2, rk2, i2 = _stage(sc, combo, mode, sname, code, plan, ('W1', 'W2'),
                          cap, staged, resume=resume2, seeds=seeds)
    w3 = sc.score(combo, ip2, rk2, mode, sname, code, plan, ('W3',))['W3']
    parts = [x for x in (w2, w3) if x is not None]
    if not parts:
        blind = None
    else:
        # GAUNTLET.md: "score = stitched blind performance". Stitched means ONE
        # equity curve over W2 then W3, not two curves averaged. The difference
        # is not cosmetic for drawdown: averaging per-window max DD understates
        # a drawdown that runs across the seam, and averaging per-window Sharpe
        # and PF is not a Sharpe or a PF of anything. Mode B used the averaged
        # form; A and C use the stitched one, and MANIFEST.md records it.
        st = _agg(np.concatenate([p['_r'] for p in parts]))
        blind = {k: v for k, v in st.items() if k != '_r'}
        blind['n_blind'] = blind.pop('n')
        blind['n_w2'] = (w2['n'] if w2 else 0)
        blind['n_w3'] = (w3['n'] if w3 else 0)
    return dict(blind=blind, ip1=ip1, rk1=rk1, ip2=ip2, rk2=rk2,
                stage1=i1, stage2=i2)


def crosses_label(b):
    """Gate 2 label -- a SORTING LABEL. Failing ANY criterion is a fail (the
    strict reading, per Jack), which is also what sends a chop combination to
    the inversion arm."""
    if b is None or b['n_w2'] < S.MIN_TRADES_BLIND or b['n_w3'] < S.MIN_TRADES_BLIND:
        return False
    return (b['expectancy_R'] >= LABEL['expectancy_R']
            and b['profit_factor'] >= LABEL['profit_factor']
            and b['sharpe'] >= LABEL['sharpe']
            and b['sortino'] >= LABEL['sortino']
            and b['calmar'] >= LABEL['calmar'])


def _flat(d, pre):
    return {'%s_%s' % (pre, k): v for k, v in sorted(d.items())}


def run_chunk(args):
    mode, sname, lo, hi, cid = args[:5]
    srt = args[5] if len(args) > 5 else False
    cap = args[6] if len(args) > 6 else None
    staged = args[7] if len(args) > 7 else False
    deepen = args[8] if len(args) > 8 else False
    disk = args[9] if len(args) > 9 else False
    seed_from = args[10] if len(args) > 10 else None
    code = dict((s, c) for s, _, c in S.SLICES)[sname]
    plan = dict((s, p) for s, p, _ in S.SLICES)[sname]
    D = pd.read_csv(os.path.join(ROOTOUT, 'gate1_survivors_mode%s.csv' % mode),
                    usecols=['c1', 'c2', 'vol', 'base', 'exit_ind', 'slice'])
    D = D[D['slice'] == sname].reset_index(drop=True)
    if not S.MODES[mode]['uses_exit_slot']:
        D['exit_ind'] = S.slot_options()['exit_ind'][0]
    if srt:
        # THE SORT. Gate 1 wrote survivors in shard-interleaved order, so a
        # 100-combination chunk touched 62 distinct indicators; sorted it
        # touches 30. Every avoided one is a 3-329 ms recompute across 28
        # pairs, and recompute -- not scoring -- is where the time goes.
        # Mode B ran unsorted and is NOT re-sorted: renumbering its chunks
        # would discard banked work to no purpose.
        D = D.sort_values(['c1', 'c2', 'vol', 'base', 'exit_ind'],
                          kind='mergesort').reset_index(drop=True)
    sub = D.iloc[lo:hi]
    sc = Scorer(disk=disk)
    if seed_from and not SEEDS:
        SEEDS.update(load_seeds(seed_from))
    t0 = time.time(); rows = []
    for r in sub.itertuples():
        cb = (r.c1, r.c2, r.vol, r.base, r.exit_ind)
        try:
            r1 = r2 = None
            if deepen and not BANK:
                BANK.update(load_bank(mode, sname))
            if deepen:
                # ROUND 2. Resume from the banked cheap-pass parameter sets
                # rather than redoing them -- that is the whole point of
                # checkpointing them in round 1.
                b = BANK.get((r.c1, r.c2, r.vol, r.base, r.exit_ind))
                if b:
                    r1, r2 = b
            res = full_walk(sc, cb, mode, sname, code, plan, cap=cap,
                            staged=staged, resume1=r1, resume2=r2,
                            seeds=SEEDS.get((r.c1, r.c2, r.vol, r.base)))
        except Exception as e:
            rows.append(dict(c1=r.c1, c2=r.c2, vol=r.vol, base=r.base,
                             exit_ind=r.exit_ind, slice=sname, mode=mode,
                             error=repr(e)[:120]))
            continue
        b = res['blind'] or {}
        row = dict(c1=r.c1, c2=r.c2, vol=r.vol, base=r.base,
                   exit_ind=r.exit_ind, slice=sname, mode=mode,
                   crosses_label=crosses_label(res['blind']))
        row.update(b)
        row.update(_flat(res['rk2'], 'risk'))
        row.update({'ip2': json.dumps(res['ip2'], sort_keys=True),
                    'ip1': json.dumps(res['ip1'], sort_keys=True),
                    'risk1': json.dumps(res['rk1'], sort_keys=True),
                    'stage': res['stage2'].get('stage'),
                    'stage_w1': res['stage1'].get('stage'),
                    'cheap_gain_R': res['stage2'].get('cheap_gain'),
                    'base_R_w1w2': res['stage2'].get('base_R'),
                    'final_R_w1w2': res['stage2'].get('final_R'),
                    'cheap_ip': res['stage2'].get('cheap_ip'),
                    'cheap_risk': res['stage2'].get('cheap_risk'),
                    # stage 1's cheap set was the one stage still unbanked.
                    # "Every tuning stage's adopted sets" means every one, and
                    # mode B is the standing proof of what a missing stage costs.
                    'cheap_ip_w1': res['stage1'].get('cheap_ip'),
                    'cheap_risk_w1': res['stage1'].get('cheap_risk'),
                    'cheap_gain_R_w1': res['stage1'].get('cheap_gain'),
                    'resumed': res['stage2'].get('resumed')})
        rows.append(row)
    el = time.time() - t0
    out = pd.DataFrame(rows)
    d = os.path.join(CK, 'mode%s_%s%s' % (mode, sname, '_deep' if deepen else ''))
    os.makedirs(d, exist_ok=True)
    out.to_csv(os.path.join(d, 'chunk_%05d.csv' % cid), index=False)
    return dict(mode=mode, slice=sname, chunk=cid, n=len(sub), seconds=el,
                evals=sc.n_eval, cache_hits=sc.cache.hits,
                cache_misses=sc.cache.misses,
                disk_hits=getattr(sc.cache, 'disk_hits', 0),
                crossed=int(out.get('crosses_label', pd.Series(dtype=bool)).sum()))


CHUNK = 100          # combinations per chunk: ~1-2 h, so a lost chunk is cheap


BANK = {}
SEEDS = {}


def load_seeds(from_mode='B'):
    """Accepts a comma-separated list -- 'A,B' seeds mode C from both. Later
    modes in the list win a key collision, because the LATER mode is the one
    whose exit rule C is closer to; a collision only happens where both adopted
    a value for the same frozen parameter, and neither is more authoritative
    than the other, so the tie is broken by declaration rather than by chance."""
    if ',' in str(from_mode):
        out = {}
        for m in str(from_mode).split(','):
            out.update(load_seeds(m.strip()))
        return out
    return _load_seeds_one(from_mode)


def _load_seeds_one(from_mode='B'):
    """B's ADOPTED indicator parameters, keyed on the 4-tuple that A and C share
    with it (the exit slot is excluded: B never used one, and a B combination
    corresponds to every C combination with the same first four slots).

    WHY THIS IS ALMOST ALWAYS A NO-OP, stated so nobody later mistakes it for a
    bigger lever than it is: B's adopted values are GRID POINTS BY
    CONSTRUCTION -- chosen from the same grids A and C search -- so offering
    them as extra candidates offers candidates the exhaustive per-knob search
    already evaluates.

    THE ONE CASE THAT IS REAL: B ran uncapped, A and C are capped at each
    indicator's six highest-impact parameters. For the four indicators above the
    cap, B may have adopted a value for a parameter A and C will never tune. THAT
    value is new information, and it is offered as a candidate for an otherwise
    frozen parameter -- adopted only if it beats the default, same rule as
    everything else."""
    out = {}
    f = os.path.join(ROOTOUT, 'gate2_tuned_mode%s.csv' % from_mode)
    fs = ([f] if os.path.exists(f) else
          sorted(glob.glob(os.path.join(CK, 'mode%s_*' % from_mode, 'chunk_*.csv'))))
    for x in fs:
        try:
            d = pd.read_csv(x)
        except Exception:
            continue
        if 'ip2' not in d.columns:
            continue
        for r in d.itertuples():
            if not isinstance(getattr(r, 'ip2', None), str):
                continue
            out[(r.c1, r.c2, r.vol, r.base)] = json.loads(r.ip2)
    return out


def load_bank(mode, sname):
    """Banked cheap-pass parameter sets from round 1, so round 2 resumes
    instead of repeating. NOTHING IS EVER LOST is a spec requirement, not a
    convenience: the deep pass must be re-runnable for any subset later."""
    fs = sorted(glob.glob(os.path.join(CK, 'mode%s_%s' % (mode, sname),
                                       'chunk_*.csv')))
    bank = {}
    for f in fs:
        d = pd.read_csv(f)
        if 'cheap_ip' not in d.columns:
            continue
        for r in d.itertuples():
            if not isinstance(getattr(r, 'cheap_ip', None), str):
                continue
            k = (r.c1, r.c2, r.vol, r.base, r.exit_ind)
            ip = json.loads(r.cheap_ip); rk = json.loads(r.cheap_risk)
            bank[k] = ((ip, rk), (ip, rk))
    return bank


def plan_chunks(mode, sname, srt=False, cap=None, staged=False,
                deepen=False, disk=False, seed_from=None):
    f = os.path.join(ROOTOUT, 'gate1_survivors_mode%s.csv' % mode)
    n = len(pd.read_csv(f, usecols=['slice']).query('slice == @sname'))
    d = os.path.join(CK, 'mode%s_%s%s' % (mode, sname, '_deep' if deepen else ''))
    todo = []
    for cid, lo in enumerate(range(0, n, CHUNK)):
        if not os.path.exists(os.path.join(d, 'chunk_%05d.csv' % cid)):
            todo.append((mode, sname, lo, min(lo + CHUNK, n), cid, srt,
                         cap, staged, deepen, disk, seed_from))
    return n, todo


def progress_row(mode, r, done, total, t0, spent):
    row = dict(mode=r['mode'], slice=r['slice'], chunk=r['chunk'],
               combos=r['n'], seconds=round(r['seconds'], 1),
               engine_hours_chunk=round(r['seconds'] / 3600, 3),
               evals=r['evals'], cache_hit_pct=round(
                   100 * r['cache_hits'] / max(1, r['cache_hits'] + r['cache_misses']), 1),
               crossed_label=r['crossed'],
               combos_done=done, combos_total=total,
               engine_hours_spent=round(spent / 3600, 2),
               wall_hours=round((time.time() - t0) / 3600, 2))
    rate = spent / max(1, done)
    row['projected_remaining_engine_h'] = round(rate * (total - done) / 3600, 1)
    f = os.path.join(ROOTOUT, 'gate2_progress_mode%s.csv' % mode)
    pd.DataFrame([row]).to_csv(f, mode='a', header=not os.path.exists(f), index=False)
    return row


def run_mode(mode, jobs=None, slices=('trend', 'chop'), srt=False,
             cap=None, staged=False, deepen=False, disk=False, seed_from=None,
             reverse=False):
    import multiprocessing as mp
    jobs = jobs or max(1, (os.cpu_count() or 2) - 2)
    t0 = time.time()
    for sname in slices:
        total, todo = plan_chunks(mode, sname, srt=srt, cap=cap,
                                  staged=staged, deepen=deepen, disk=disk,
                                  seed_from=seed_from)
        # --reverse lets a SECOND pool add capacity to a run already in flight
        # without restarting it. mp.Pool is fixed at construction, and a restart
        # would discard every chunk currently in flight (written chunks are kept
        # -- plan_chunks skips any that exist). A second pool consuming the same
        # queue from the far end converges with the first instead of racing it
        # for the same chunk, so the only duplicated work is whatever they
        # overlap on at the meeting point.
        if reverse:
            todo = list(reversed(todo))
        done = total - sum(t[3] - t[2] for t in todo)
        spent = 0.0
        print('GATE 2 mode %s %s: %s combinations, %d chunks queued, %d workers'
              % (mode, sname, format(total, ','), len(todo), jobs), flush=True)
        if not todo:
            continue
        with mp.Pool(jobs) as pool:
            for r in pool.imap_unordered(run_chunk, todo):
                done += r['n']; spent += r['seconds']
                row = progress_row(mode, r, done, total, t0, spent)
                print('  [%s %s] chunk %5d  %4d combos  %6.1f s  hit %4.1f%%  '
                      'crossed %3d  |  %s/%s done, %.1f engine-h spent, '
                      '~%.0f engine-h left'
                      % (mode, sname, r['chunk'], r['n'], r['seconds'],
                         row['cache_hit_pct'], r['crossed'],
                         format(done, ','), format(total, ','),
                         row['engine_hours_spent'],
                         row['projected_remaining_engine_h']), flush=True)
    return collect_mode(mode)


def collect_mode(mode):
    out = []
    for sname in ('trend', 'chop'):
        fs = sorted(glob.glob(os.path.join(CK, 'mode%s_%s' % (mode, sname),
                                           'chunk_*.csv')))
        if fs:
            out.append(pd.concat([pd.read_csv(f) for f in fs], ignore_index=True))
    if not out:
        return pd.DataFrame()
    D = pd.concat(out, ignore_index=True)
    D.to_csv(os.path.join(ROOTOUT, 'gate2_tuned_mode%s.csv' % mode), index=False)
    return D


def main():
    a = sys.argv[1:]

    def opt(name, cast, default=None):
        return cast(a[a.index(name) + 1]) if name in a else default
    mode = opt('--mode', str, 'B')
    sl = opt('--slice', str, None)
    slices = (sl,) if sl else ('trend', 'chop')
    D = run_mode(mode, jobs=opt('--jobs', int), slices=slices,
                 srt='--sorted' in a, cap=opt('--cap', int),
                 staged='--staged' in a, deepen='--deepen' in a,
                 disk='--disk' in a, seed_from=opt('--seed-from', str),
                 reverse='--reverse' in a)
    print('\nMODE %s TUNED: %d rows, %d crossing the gate 2 label'
          % (mode, len(D), int(D.get('crosses_label',
                                     pd.Series(dtype=bool)).sum())), flush=True)
    return D


if __name__ == '__main__':
    main()


# ==========================================================================
# THE FINAL RANKING — production and risk-aversion, co-equal
# ==========================================================================
def rank_graduates(D):
    """GAUNTLET.md: rank on total blind R, rank on Sortino, final position is
    the AVERAGE of the two ranks. Calmar breaks ties.

    Co-equal by construction: neither metric can dominate, because each
    contributes exactly one rank. Averaging RANKS rather than the metrics
    themselves is deliberate -- total R is unbounded and Sortino is not, so
    averaging the raw numbers would let one scale swamp the other.

    Governs ordering, round-2 deepening priority, and presentation.
    """
    D = D.copy()
    n = len(D)
    D['rank_total_R'] = D['total_R'].rank(ascending=False, method='min')
    # An undefined Sortino ranks LAST, never first. na_option='bottom' is the
    # whole guard: with the default, NaN ranks NaN, rank_score becomes NaN, and
    # a combination with no measurable downside would sort to the top of a
    # descending sort in some code paths.
    D['rank_sortino'] = D['sortino'].rank(ascending=False, method='min',
                                          na_option='bottom')
    D['sortino_undefined'] = D['sortino'].isna()
    D['rank_score'] = (D['rank_total_R'] + D['rank_sortino']) / 2.0
    D = D.sort_values(['rank_score', 'calmar'], ascending=[True, False])
    D['final_rank'] = range(1, len(D) + 1)
    return D
