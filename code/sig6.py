import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Signal library v6 — the duration / elapsed-time batch. ~100,000 NEW signals.

WHY THIS FAMILY. zz_tsexceed_D375 is the only trend signal in the first 20,275 to
pass every gate: time since the last 2-sigma move. The longer since a shock, the
straighter price travels afterward. That family was represented by a handful of
columns. This batch builds it out properly.

The organising idea is EVENT x CONDITION x READOUT:

  EVENT      something datable happened -- a sigma exceedance, a new n-day high,
             a moving-average cross, a direction flip, a vol-median cross, a range
             breakout, a drawdown opening. ~280 definitions.
  CONDITION  the event only counts when the panel or the pair was in a given state
             (unconditional, panel vol low/high, own vol low/high, coexceedance
             high). Conditioning the EVENT, not the measure, is what makes this
             cheap and what makes it different from anything scored so far.
  READOUT    time since, hazard ratio, occupancy, episode count, streak length.

HAZARD RATIOS are the idea most worth testing: elapsed time divided by that
event's own recent mean gap. It asks "are we overdue?" rather than "how long has
it been?" Nothing in the first 20,275 asks that.

CHOP SIDE is cross-sectional and panel-level, because chop is panel-synchronised
(86-96% pair agreement) while trend is idiosyncratic: eigenvalue spectrum of the
28-pair correlation matrix and the gaps between eigenvalues, dispersion term
structure, coexceedance across more thresholds and windows, breadth measures,
volatility rank churn, panel turn frequency, panel vol-of-vol.

NOT BUILT, ON EVIDENCE FROM THE FIRST 20,275:
  interactions   49.1% OOS sign retention, worse than chance. 7,140 wasted.
  deltas         42%. Change-in-signal actively destroys information.
  monthly        47.8%, below random. Nothing here is monthly-sourced.

VARIANTS kept are the ones that held up: level (65%), z-score against a long
window (56%), rolling percentile rank. Ten per base feature.
"""
import numpy as np, pandas as pd

DW = [5, 8, 10, 15, 20, 25, 30, 40, 50, 60, 75, 90, 120, 150, 180, 250, 375, 500, 750]
THR = [1.0, 1.5, 2.0, 2.5, 3.0, 4.0]
VOLW = [10, 20, 40, 60, 120, 250]
HAZ = [250, 500, 750]
SMOOTH = [1, 2, 3, 5, 8, 10, 15, 20]

# variant prefixes deliberately distinct from v5's zz_/zs_/pr_/ps_ so no generated
# name can collide with an existing one
VAR = [('',     None),
       ('za_',  ('z', 250)), ('zb_', ('z', 500)), ('zc_', ('z', 750)),
       ('zd_',  ('z', 120)), ('ze_', ('z', 60)),
       ('ra_',  ('r', 500)), ('rb_', ('r', 250)),
       ('rc_',  ('r', 120)), ('rd_', ('r', 60))]


# ---------------- vectorised readouts ----------------
def _tsince(b):
    """Bars since b was last True. NaN before the first occurrence."""
    n = len(b)
    idx = np.arange(n)
    last = np.maximum.accumulate(np.where(b, idx, -1))
    return np.where(last >= 0, idx - last, np.nan).astype(np.float32)


def _rsum(b, n):
    """Trailing sum over n bars, NaN for the first n-1."""
    cs = np.concatenate([[0.0], np.cumsum(b.astype(np.float64))])   # len = len(b)+1
    out = np.full(len(b), np.nan)
    out[n - 1:] = cs[n:] - cs[:-n]
    return out


def _hazard(ts, b, H):
    """Elapsed time relative to this event's own mean gap over the last H bars.

    mean gap ~ H / (events in H), so elapsed / mean_gap = elapsed * events / H.
    Above 1 means overdue by its own recent history."""
    c = _rsum(b, H)
    with np.errstate(invalid='ignore', divide='ignore'):
        return (ts * c / H).astype(np.float32)


def _streak(sgn):
    """Length of the current run of identical sign."""
    s = pd.Series(sgn)
    grp = (s != s.shift()).cumsum()
    return (s.groupby(grp).cumcount() + 1).values.astype(np.float32)


def _pct(s, n):
    return s.rolling(n).rank(pct=True)


# ---------------- panel context, shared across all 28 pairs ----------------
def context(px):
    lp = np.log(px.astype(float))
    rt = lp.diff()
    z = (rt - rt.rolling(250).mean()) / rt.rolling(250).std()
    n_pairs = rt.shape[1]

    vol60 = rt.rolling(60).std()
    panelvol = vol60.mean(axis=1)
    pv_pct = _pct(panelvol, 250)
    coex2 = (z.abs() > 2).sum(axis=1) / n_pairs
    cx_pct = _pct(coex2, 250)

    ctx = dict(lp=lp, rt=rt, z=z, vol60=vol60, panelvol=panelvol,
               pv_pct=pv_pct, coex2=coex2, cx_pct=cx_pct, n_pairs=n_pairs)
    ctx['chop'] = _chop_base(px, lp, rt, z, vol60, n_pairs, pv_pct, cx_pct)
    return ctx


def _conditions(ctx, pair):
    """Boolean states an event can be required to occur in. Unconditional first."""
    pv, cx = ctx['pv_pct'], ctx['cx_pct']
    ov = _pct(ctx['vol60'][pair], 250)
    n = len(pv)
    return [('', np.ones(n, bool)),
            ('_pl', (pv < .33).values), ('_ph', (pv > .67).values),
            ('_ol', (ov < .33).values), ('_oh', (ov > .67).values),
            ('_ch', (cx > .67).values)]


# ---------------- events ----------------
def _events(lp_s, ctx, pair):
    """~280 datable event definitions, as boolean arrays."""
    lp = lp_s.values
    r = np.diff(lp, prepend=np.nan)
    ar = np.abs(r)
    E = {}

    # sigma exceedances: unsigned, up-only, down-only
    for vw in VOLW:
        sd = pd.Series(r).rolling(vw).std().shift(1).values
        for t in THR:
            hit = ar > t * sd
            E['sg%g_v%d' % (t, vw)] = np.nan_to_num(hit, nan=0).astype(bool)
            E['su%g_v%d' % (t, vw)] = np.nan_to_num(r > t * sd, nan=0).astype(bool)
            E['sd%g_v%d' % (t, vw)] = np.nan_to_num(r < -t * sd, nan=0).astype(bool)

    S = pd.Series(lp)
    for n in DW:
        mx = S.rolling(n).max().values
        mn = S.rolling(n).min().values
        E['hi_%d' % n] = np.nan_to_num(lp >= mx, nan=0).astype(bool)
        E['lo_%d' % n] = np.nan_to_num(lp <= mn, nan=0).astype(bool)
        ma = S.rolling(n).mean().values
        above = lp > ma
        prev = np.concatenate([[False], above[:-1]])
        E['mu_%d' % n] = np.nan_to_num(above & ~prev, nan=0).astype(bool)
        E['md_%d' % n] = np.nan_to_num(~above & prev, nan=0).astype(bool)
        # range breakout: today clears the PRIOR n-day extreme
        pmx = S.rolling(n).max().shift(1).values
        pmn = S.rolling(n).min().shift(1).values
        E['bu_%d' % n] = np.nan_to_num(lp > pmx, nan=0).astype(bool)
        E['bd_%d' % n] = np.nan_to_num(lp < pmn, nan=0).astype(bool)

    for k in SMOOTH:
        sm = pd.Series(r).rolling(k).mean().values if k > 1 else r
        sg = np.sign(np.nan_to_num(sm))
        E['fl_%d' % k] = np.concatenate([[False], sg[1:] != sg[:-1]])

    for vw in VOLW[:4]:
        v = pd.Series(r).rolling(vw).std()
        for mw in (60, 120, 250, 500):
            med = v.rolling(mw).median()
            up = (v > med).values
            prev = np.concatenate([[False], up[:-1]])
            E['vu_%d_%d' % (vw, mw)] = np.nan_to_num(up & ~prev, nan=0).astype(bool)
            E['vd_%d_%d' % (vw, mw)] = np.nan_to_num(~up & prev, nan=0).astype(bool)

    for d in (0.01, 0.02, 0.03, 0.05):
        dd = S - S.cummax()
        E['dd%g' % d] = np.nan_to_num((dd < -d).values, nan=0).astype(bool)
    return E


# ---------------- trend base ----------------
def trend_base(px, pair, ctx):
    lp_s = ctx['lp'][pair]
    lp = lp_s.values
    r = np.diff(lp, prepend=np.nan)
    E = _events(lp_s, ctx, pair)
    CONDS = _conditions(ctx, pair)
    o = {}

    # EVENT x CONDITION x {time since, hazard 250, hazard 750}
    for en, b in E.items():
        for cn, c in CONDS:
            bc = b & c
            ts = _tsince(bc)
            o['ts_%s%s' % (en, cn)] = ts
            for H in HAZ:
                o['hz%d_%s%s' % (H, en, cn)] = _hazard(ts, bc, H)

    # occupancy and episode frequency, on a spread subset of events
    sub = [k for i, k in enumerate(sorted(E)) if i % 7 == 0]
    for en in sub:
        b = E[en]
        starts = b & ~np.concatenate([[False], b[:-1]])
        for cn, c in CONDS[:3]:
            bc = b & c
            sc = starts & c
            for n in (20, 60, 120, 250, 500, 750):
                o['oc%d_%s%s' % (n, en, cn)] = (_rsum(bc, n) / n).astype(np.float32)
                o['ep%d_%s%s' % (n, en, cn)] = _rsum(sc, n).astype(np.float32)

    # streaks
    for k in SMOOTH:
        sm = pd.Series(r).rolling(k).mean().values if k > 1 else r
        sg = np.sign(np.nan_to_num(sm))
        st = _streak(sg)
        o['st_%d' % k] = st
        o['stu_%d' % k] = np.where(sg > 0, st, 0).astype(np.float32)
        o['std_%d' % k] = np.where(sg < 0, st, 0).astype(np.float32)
        for H in HAZ:
            m = pd.Series(st).rolling(H).mean().values
            with np.errstate(invalid='ignore', divide='ignore'):
                o['sth%d_%d' % (H, k)] = (st / m).astype(np.float32)

    # conditional trend measures: the measure averaged only over days in the state
    S = pd.Series(lp, index=lp_s.index)
    R = pd.Series(r, index=lp_s.index)
    AR = R.abs()
    for n in (20, 40, 60, 90, 120, 180, 250, 375):
        net = (S - S.shift(n)).abs()
        path = AR.rolling(n).sum()
        sd = R.rolling(n).std()
        M = {'ef': net / path,
             'tv': (S - S.shift(n)) / (sd * np.sqrt(n)),
             'wh': path / net.clip(lower=1e-9),
             'rm': R.rolling(n).mean() / AR.rolling(n).mean(),
             'pq': (S - S.rolling(n).min()) / (S.rolling(n).max() - S.rolling(n).min()),
             'up': R.clip(lower=0).rolling(n).sum() / path,
             'mx': AR.rolling(n).max() / path,
             'vr': sd / AR.rolling(n).mean()}
        for mn_, x in M.items():
            for cn, c in CONDS:
                if cn == '':
                    o['cd_%s%d' % (mn_, n)] = x.values.astype(np.float32)
                else:
                    cs = pd.Series(c.astype(float), index=x.index)
                    num = (x * cs).rolling(n).sum()
                    den = cs.rolling(n).sum()
                    o['cd_%s%d%s' % (mn_, n, cn)] = (num / den).values.astype(np.float32)
    return o


# ---------------- chop base: panel-level, identical for every pair ----------------
def _chop_base(px, lp, rt, z, vol60, n_pairs, pv_pct, cx_pct):
    o = {}
    idx = lp.index
    arr = rt.values

    # eigenvalue spectrum of the rolling correlation matrix, every 5th bar then ffill
    for n in (60, 120, 250, 500):
        e1 = np.full(len(idx), np.nan); e2 = np.full(len(idx), np.nan)
        e3 = np.full(len(idx), np.nan)
        for i in range(n, len(idx), 5):
            blk = arr[i - n:i]
            blk = blk[~np.isnan(blk).any(1)]
            if len(blk) > n // 2:
                w = np.linalg.eigvalsh(np.corrcoef(blk.T))[::-1]
                s = w.sum()
                e1[i], e2[i], e3[i] = w[0] / s, w[1] / s, w[2] / s
        s1 = pd.Series(e1, index=idx).ffill(); s2 = pd.Series(e2, index=idx).ffill()
        s3 = pd.Series(e3, index=idx).ffill()
        o['eg1_%d' % n] = s1; o['eg2_%d' % n] = s2; o['eg3_%d' % n] = s3
        o['gp12_%d' % n] = s1 - s2; o['gp23_%d' % n] = s2 - s3
        o['egt_%d' % n] = s2 + s3

    disp = rt.std(axis=1)
    absmean = rt.abs().mean(axis=1)
    for a in (5, 10, 20, 40, 60, 120):
        for b in (60, 120, 250, 500, 750):
            if a >= b:
                continue
            o['dts_%d_%d' % (a, b)] = disp.rolling(a).mean() / disp.rolling(b).mean()
            o['ats_%d_%d' % (a, b)] = absmean.rolling(a).mean() / absmean.rolling(b).mean()

    for t in (1.5, 2.0, 2.5, 3.0, 4.0):
        cx = (z.abs() > t).sum(axis=1) / n_pairs
        for n in DW:
            o['cx%g_m%d' % (t, n)] = cx.rolling(n).mean()
            o['cx%g_x%d' % (t, n)] = cx.rolling(n).max()
            o['cx%g_s%d' % (t, n)] = cx.rolling(n).std()

    L = lp
    for n in DW:
        dd = L - L.rolling(n).max()
        o['bdd_%d' % n] = (dd < -0.02).sum(axis=1) / n_pairs
        o['bd5_%d' % n] = (dd < -0.05).sum(axis=1) / n_pairs
        o['bma_%d' % n] = (L > L.rolling(n).mean()).sum(axis=1) / n_pairs
        v = rt.rolling(60).std()
        o['bvr_%d' % n] = (v > v.shift(n)).sum(axis=1) / n_pairs
        o['bpo_%d' % n] = (L > L.shift(n)).sum(axis=1) / n_pairs
        o['pdd_%d' % n] = dd.mean(axis=1)
        o['pdm_%d' % n] = dd.min(axis=1)
        # panel turn frequency: share of pairs flipping direction, smoothed
        fl = (np.sign(rt) != np.sign(rt.shift(1))).sum(axis=1) / n_pairs
        o['ptf_%d' % n] = fl.rolling(n).mean()
        o['ptv_%d' % n] = fl.rolling(n).std()
        # cross-sectional moments
        o['xsk_%d' % n] = rt.rolling(n).mean().skew(axis=1)
        o['xkt_%d' % n] = rt.rolling(n).mean().kurt(axis=1)

    # volatility rank churn: how much the 28-pair vol ranking reshuffles
    rk = vol60.rank(axis=1)
    for lag in (1, 5, 20, 60):
        ch = (rk - rk.shift(lag)).abs().mean(axis=1)
        for n in (20, 60, 120, 250, 500):
            o['rch%d_%d' % (lag, n)] = ch.rolling(n).mean()

    # panel vol-of-vol
    pv = vol60.mean(axis=1)
    for n in DW:
        o['pvv_%d' % n] = pv.rolling(n).std() / pv.rolling(n).mean()
        o['pvr_%d' % n] = pv / pv.rolling(n).mean()

    # Panel-state conditioning. These states are pair-independent, so the whole
    # chop block stays shared across all 28 pairs and is computed exactly once.
    # Each is the feature averaged only over days the panel was in that state.
    PC = [('_pl', (pv_pct < .33)), ('_ph', (pv_pct > .67)), ('_ch', (cx_pct > .67))]
    cond = {}
    for cn, c in PC:
        cs = c.astype(float)
        den = cs.rolling(250).sum()
        for k, v in o.items():
            cond[k + cn] = (v * cs).rolling(250).sum() / den
    o.update(cond)
    return {k: (v.values.astype(np.float32) if hasattr(v, 'values') else v)
            for k, v in o.items()}


# ---------------- assembly ----------------
def base_frame(px, pair, ctx):
    o = dict(ctx['chop'])
    o.update(trend_base(px, pair, ctx))
    F = pd.DataFrame(o, index=ctx['lp'].index, copy=False)
    return F.replace([np.inf, -np.inf], np.nan).astype(np.float32)


def expand(block):
    """Apply the ten variants to a block of base columns."""
    out = [block]
    for pfx, spec in VAR:
        if spec is None:
            continue
        kind, n = spec
        if kind == 'z':
            v = (block - block.rolling(n).mean()) / block.rolling(n).std()
        else:
            v = block.rolling(n).rank(pct=True)
        v.columns = [pfx + c for c in block.columns]
        out.append(v)
    S = pd.concat(out, axis=1)
    return S.replace([np.inf, -np.inf], np.nan).astype(np.float32)


def all_names(base_cols):
    names = []
    for pfx, _ in VAR:
        names += [pfx + c for c in base_cols]
    return names


def is_chop(name):
    """Which target a name is aimed at. Chop stems are the panel-level families."""
    stem = name.split('_', 1)[0]
    for p, _ in VAR:
        if p and name.startswith(p):
            stem = name[len(p):].split('_', 1)[0]
            break
    return stem[:3] in ('eg1', 'eg2', 'eg3', 'gp1', 'gp2', 'egt', 'dts', 'ats',
                        'bdd', 'bd5', 'bma', 'bvr', 'bpo', 'pdd', 'pdm', 'ptf',
                        'ptv', 'xsk', 'xkt', 'pvv', 'pvr') or stem.startswith('cx') \
        or stem.startswith('rch')


if __name__ == '__main__':
    import time, json
    px = pd.read_csv(os.path.join(ROOTDATA, 'px28.csv'), index_col=0, parse_dates=True)
    old = {d['s'] for d in json.load(open(os.path.join(ROOTOUT, 'signals.json')))}
    t0 = time.time()
    ctx = context(px)
    tc = time.time() - t0
    t0 = time.time()
    F = base_frame(px, 'USDJPY', ctx)
    tb = time.time() - t0
    names = all_names(list(F.columns))
    nch = sum(is_chop(n) for n in names)
    print('context %.0fs | base %.0fs' % (tc, tb))
    print('base features %d  x %d variants = %d signals' % (F.shape[1], len(VAR), len(names)))
    print('  trend-aimed %d | chop-aimed %d' % (len(names) - nch, nch))
    print('OVERLAP with existing 20,275: %d' % len(set(names) & old))
    print('coverage median %.2f' % F.notna().mean().median())
