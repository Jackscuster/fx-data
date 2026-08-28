import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Signal library v7 — TREND ONLY. ~50,000 signals across five NON-MOMENTUM mechanisms.

THE THESIS (TREND_BATCH_NEW.md). Every trend mechanism tested so far is momentum in
some costume -- MA crosses, N-day returns, slope t-stats, efficiency ratios -- and it
loses on all 28 pairs. The two best non-chop results in the project are not momentum:
zz_tsexceed_D375 (a duration measure) and currency-leg divergence (a cross-sectional
measure). This batch abandons momentum and tests five mechanisms that have never been
tried.

  M1 xs*  cross-sectional / relative strength   20,000   HIGHEST PRIORITY
  M2 ct*  conditional trend                     10,000
  M3 ms*  market structure                       8,000
  M4 ac*  acceleration                           6,000
  M5 du*  duration extended                      6,000

===========================  ASSUMPTIONS, ALL OF THEM  =========================

1. VARIANTS. 10 per base feature (level + 5 z-scores + 4 percentile ranks), the three
   forms that held up in earlier batches. 5,000 base features -> ~50,000 signals.

2. NO HAZARD RATIOS. Instructed, and correct: decorrelation put elapsed x count / H
   in the same cluster as plain elapsed time -- they are substitutes by construction.
   M4 keeps time-since and adds EMPIRICAL SURVIVAL (what historically followed N days
   in this state), which is a different quantity, not a rescaling of elapsed time.

3. RANK VELOCITY IS A DELTA, and deltas retained only 42% OOS. TREND_BATCH_NEW.md
   asks for it explicitly under M1, so it is built -- but on a NEW quantity (rank),
   not on an existing signal. Whether the delta finding generalises to ranks is
   itself a result. Tagged xsvel/xsacc so it can be isolated in the retention table.

4. SWING CAUSALITY. A swing high at t is a close higher than the n closes on EITHER
   side, so it cannot be known until t+n. Every swing series is therefore shifted
   forward by n before use: at time T the code only sees swings confirmed at or
   before T. Getting this wrong would manufacture a large fake edge.

5. CLOSE-ONLY STRUCTURE. No OHLC, so these are close-based swings, a weaker proxy
   than true intraday swings. If M3 produces nothing that is a real answer about
   close-only data, not about structure as a mechanism.

6. LEG INDICES. Per-currency strength = mean of (+r where the currency is base,
   -r where it is quote) across the 28 pairs, cumulated. Same construction as the
   crisis work. Ranks are 1 = strongest of the 8.

7. CONDITIONING uses the same five states throughout: panel vol low, panel dispersion
   low, own vol compressed, legs diverging, time-since-shock high. A conditional
   feature is the measure averaged over only the days in that state within the
   window -- sum(x*c)/sum(c) -- never a product of two signals (interactions retained
   49%, worse than chance).

8. NOT BUILT, on evidence: momentum, MA crosses, N-day returns, slope measures, bare
   efficiency ratios, interactions, deltas-of-signals, monthly-sourced features.

9. NO SHARPE. Signals score on forward efficiency and forward turn frequency only.
   Sharpe is a strategy-layer measure and does not appear in this batch.
"""
import numpy as np, pandas as pd

CCY = ['EUR', 'GBP', 'AUD', 'NZD', 'USD', 'CAD', 'CHF', 'JPY']
W = [5, 10, 15, 20, 30, 40, 60, 90, 120, 180, 250, 375, 500, 750]
SW = [3, 5, 8, 10, 12, 15, 20, 25, 30, 40]   # swing half-widths
VAR = [('',    None),
       ('za_', ('z', 250)), ('zb_', ('z', 500)), ('zc_', ('z', 750)),
       ('zd_', ('z', 120)), ('ze_', ('z', 60)),
       ('ra_', ('r', 500)), ('rb_', ('r', 250)),
       ('rc_', ('r', 120)), ('rd_', ('r', 60))]
MECH = {'xs': 'cross-sectional', 'ct': 'conditional', 'ms': 'structure',
        'ac': 'acceleration', 'du': 'duration'}


def mech_of(name):
    for p, _ in VAR:
        if p and name.startswith(p):
            name = name[len(p):]
            break
    return MECH.get(name[:2], 'other')


# ---------------- helpers ----------------
def _tsince(b):
    n = len(b); idx = np.arange(n)
    last = np.maximum.accumulate(np.where(b, idx, -1))
    return np.where(last >= 0, idx - last, np.nan).astype(np.float32)


def _rsum(b, n):
    cs = np.concatenate([[0.0], np.cumsum(np.nan_to_num(b).astype(np.float64))])
    out = np.full(len(b), np.nan)
    out[n - 1:] = cs[n:] - cs[:-n]
    return out


def _cmean(x, c, n):
    """Mean of x over only the days in state c, within a trailing window of n."""
    num = (x * c).rolling(n).sum()
    den = c.rolling(n).sum()
    return (num / den.replace(0, np.nan))


def _streak(sgn):
    s = pd.Series(sgn)
    return ((s.groupby((s != s.shift()).cumsum()).cumcount()) + 1).values.astype(np.float32)


# ---------------- panel context ----------------
def context(px):
    lp = np.log(px.astype(float))
    rt = lp.diff()
    npairs = rt.shape[1]

    # currency leg indices
    legr = {}
    for c in CCY:
        legs = []
        for p in rt.columns:
            if p[:3] == c:
                legs.append(rt[p])
            elif p[3:] == c:
                legs.append(-rt[p])
        legr[c] = pd.concat(legs, axis=1).mean(axis=1)
    LR = pd.DataFrame(legr)
    LI = LR.cumsum()

    vol60 = rt.rolling(60).std()
    panelvol = vol60.mean(axis=1)
    disp = rt.std(axis=1)
    z = (rt - rt.rolling(250).mean()) / rt.rolling(250).std()

    # three definitions of "strength" for the ranking, per window
    STR, RANK, RZ, DISPW, TOPSPR, TSLEAD, TSLAG = {}, {}, {}, {}, {}, {}, {}
    for n in W:
        base = LI - LI.shift(n)
        sd = LR.rolling(n).std() * np.sqrt(n)
        forms = {'r': base,                                   # raw leg move
                 'v': base / sd,                              # vol-normalised
                 'e': base.abs() / LR.abs().rolling(n).sum(),  # leg efficiency
                 'd': base / (LI.rolling(n).max() - LI.rolling(n).min())}  # move vs own range
        for fk, S in forms.items():
            k = '%s%d' % (fk, n)
            STR[k] = S
            R = S.rank(axis=1, ascending=False)               # 1 = strongest
            RANK[k] = R
            RZ[k] = (S.sub(S.median(axis=1), axis=0)).div(S.std(axis=1).replace(0, np.nan), axis=0)
            DISPW[k] = S.std(axis=1)
            TOPSPR[k] = S.max(axis=1) - S.min(axis=1)
            # Early rows are all-NA across the panel -- every rolling window is
            # still warming up, so R has no rank to take. pandas 2 returned NaN
            # for those rows with a FutureWarning; PANDAS 3 RAISES
            # ValueError("Encountered all NA values"). That is the fault that
            # broke CI on 2026-08-05, the day this module was added: CI installs
            # pandas unpinned and got 3.x, the dev machine had 2.x and never saw
            # it. Reduce only the rows that have a value, and leave the rest NaN
            # -- which is what pandas 2 did, so the numbers do not move.
            ok = R.notna().any(axis=1)
            lead = pd.Series(np.nan, index=R.index, dtype=object)
            lag = pd.Series(np.nan, index=R.index, dtype=object)
            if ok.any():
                lead.loc[ok] = R.loc[ok].idxmin(axis=1)
                lag.loc[ok] = R.loc[ok].idxmax(axis=1)
            TSLEAD[k] = pd.Series(_tsince((lead != lead.shift()).values), index=R.index)
            TSLAG[k] = pd.Series(_tsince((lag != lag.shift()).values), index=R.index)

    pv = panelvol.rolling(250).rank(pct=True)
    dv = disp.rolling(250).rank(pct=True)
    tss = pd.Series(_tsince((z.abs() > 2).any(axis=1).values), index=lp.index)
    tsq = tss.rolling(250).rank(pct=True)

    return dict(lp=lp, rt=rt, LR=LR, LI=LI, vol60=vol60, panelvol=panelvol, disp=disp,
                STR=STR, RANK=RANK, RZ=RZ, DISPW=DISPW, TOPSPR=TOPSPR,
                TSLEAD=TSLEAD, TSLAG=TSLAG, pv=pv, dv=dv, tsq=tsq, npairs=npairs)


def conditions(ctx, pair):
    """The five states. Names match the spec's wording."""
    ov = ctx['vol60'][pair].rolling(250).rank(pct=True)
    legdiv = ctx['TOPSPR']['r60'].rolling(250).rank(pct=True)
    return [('_pv', (ctx['pv'] < .33)),        # panel vol bottom tercile
            ('_pd', (ctx['dv'] < .33)),        # panel dispersion low
            ('_ov', (ov < .33)),               # own vol compressed
            ('_ld', (legdiv > .67)),           # currency legs diverging
            ('_ts', (ctx['tsq'] > .67))]       # long since the last shock


# ---------------- M1: cross-sectional relative strength ----------------
def m1_crosssec(ctx, pair):
    b, q = pair[:3], pair[3:]
    o = {}
    for k in ctx['RANK']:
        R, S, RZ = ctx['RANK'][k], ctx['STR'][k], ctx['RZ'][k]
        rb, rq = R[b], R[q]
        o['xsrkb_' + k] = rb.values
        o['xsrkq_' + k] = rq.values
        o['xsgap_' + k] = (rq - rb).values                    # + = base stronger
        o['xszb_' + k] = RZ[b].values
        o['xszq_' + k] = RZ[q].values
        o['xszgap_' + k] = (RZ[b] - RZ[q]).values
        o['xsspr_' + k] = (S[b] - S[q]).values
        o['xsdisp_' + k] = ctx['DISPW'][k].values
        o['xstop_' + k] = ctx['TOPSPR'][k].values
        o['xslead_' + k] = ctx['TSLEAD'][k].values
        o['xslag_' + k] = ctx['TSLAG'][k].values
        o['xsisl_' + k] = (rb == 1).astype(float).values
        o['xsisw_' + k] = (rb == 8).astype(float).values
        # persistence: bars the leg has held its current integer rank
        o['xsperb_' + k] = _streak(rb.values)
        o['xsperq_' + k] = _streak(rq.values)
        # rank velocity / acceleration -- a DELTA construction, see assumption 3
        for h in (5, 20, 60):
            o['xsvelb_%s_%d' % (k, h)] = (rb - rb.shift(h)).values
            o['xsvelq_%s_%d' % (k, h)] = (rq - rq.shift(h)).values
            o['xsacc_%s_%d' % (k, h)] = ((rb - rb.shift(h))
                                         - (rb.shift(h) - rb.shift(2 * h))).values
    # the four core relative measures, averaged only over days in each state
    CONDS = conditions(ctx, pair)
    n0 = 250
    for k in list(ctx['RANK'])[::2]:                      # every other key, to bound size
        R, S, RZ = ctx['RANK'][k], ctx['STR'][k], ctx['RZ'][k]
        core = {'xscgap': (R[q] - R[b]), 'xsczg': (RZ[b] - RZ[q]),
                'xscspr': (S[b] - S[q]), 'xsctop': ctx['TOPSPR'][k]}
        for mk, x in core.items():
            for cn, c in CONDS:
                o['%s_%s%s' % (mk, k, cn)] = _cmean(x, c.astype(float), n0).values
    return o


# ---------------- M3: market structure (close-only swings) ----------------
def _swings(lp_s, n):
    """Confirmed swing highs/lows. Shifted by n: a swing at t is unknown until t+n."""
    r = lp_s.rolling(2 * n + 1, center=True)
    hi = (lp_s == r.max()).shift(n).fillna(False)
    lo = (lp_s == r.min()).shift(n).fillna(False)
    return hi.values.astype(bool), lo.values.astype(bool)


def m3_structure(ctx, pair):
    lp_s = ctx['lp'][pair]
    lp = lp_s.values
    o = {}
    for n in SW:
        hi, lo = _swings(lp_s, n)
        sh = pd.Series(np.where(hi, lp, np.nan)).ffill()      # last confirmed swing high
        sl = pd.Series(np.where(lo, lp, np.nan)).ffill()
        shp, slp = sh.shift(1), sl.shift(1)
        hh = (hi & (sh > shp).values)                          # higher high
        lh = (hi & (sh <= shp).values)
        hl = (lo & (sl > slp).values)                          # higher low
        ll = (lo & (sl <= slp).values)
        o['mstsh_%d' % n] = _tsince(hi)
        o['mstsl_%d' % n] = _tsince(lo)
        o['msbrk_%d' % n] = _tsince(((lp < sl.values) | (lp > sh.values)))
        # pullback depth vs the prior impulse, and impulse-to-correction shape
        imp = (sh - sl).abs()
        pb = (pd.Series(lp) - sh).abs()
        o['mspb_%d' % n] = (pb / imp.replace(0, np.nan)).values
        o['msimp_%d' % n] = (imp / imp.rolling(250).mean()).values
        for m in (20, 40, 60, 90, 120, 250, 500, 750):
            o['mshh_%d_%d' % (n, m)] = _rsum(hh, m)
            o['msll_%d_%d' % (n, m)] = _rsum(ll, m)
            o['mshl_%d_%d' % (n, m)] = _rsum(hl, m)
            o['mslh_%d_%d' % (n, m)] = _rsum(lh, m)
            up = _rsum(hh, m) + _rsum(hl, m)
            dn = _rsum(ll, m) + _rsum(lh, m)
            o['msseq_%d_%d' % (n, m)] = (up - dn) / np.maximum(up + dn, 1)
            # Failed break: price cleared the prior swing YESTERDAY and closed back
            # inside TODAY. Both legs are backward-looking -- an earlier draft used
            # shift(-1) here, which peeked one bar ahead and would have manufactured
            # an edge in exactly the family this batch is meant to test honestly.
            _l = pd.Series(lp)
            fb = ((_l.shift(1) > shp.shift(1)) & (_l <= shp.shift(1))).values
            o['msfail_%d_%d' % (n, m)] = _rsum(np.nan_to_num(fb).astype(bool), m)
            o['mssr_%d_%d' % (n, m)] = _rsum(np.abs(lp - sh.values) < 1e-3, m)
    # structure quality inside each state
    CONDS = conditions(ctx, pair)
    for n in SW:
        hi, lo = _swings(lp_s, n)
        sh = pd.Series(np.where(hi, lp, np.nan)).ffill()
        sl = pd.Series(np.where(lo, lp, np.nan)).ffill()
        hh = pd.Series((hi & (sh > sh.shift(1)).values).astype(float))
        ll = pd.Series((lo & (sl <= sl.shift(1)).values).astype(float))
        Q = {'msq1': hh - ll,
             'msq2': pd.Series((sh - sl).abs().values),
             'msq3': pd.Series(_tsince(hi))}
        for mk, x in Q.items():
            x.index = lp_s.index
            for cn, c in CONDS:
                o['%s_%d%s' % (mk, n, cn)] = _cmean(x, c.astype(float), 250).values
    return o


# ---------------- M4: acceleration ----------------
def m4_accel(ctx, pair):
    lp = ctx['lp'][pair]
    r = lp.diff()
    o = {}
    for n in W:
        sd = r.rolling(n).std()
        v1 = lp - lp.shift(n)
        v2 = lp.shift(n) - lp.shift(2 * n)
        o['acsec_%d' % n] = ((v1 - v2) / (sd * np.sqrt(n))).values
        o['acrat_%d' % n] = (v1 / v2.replace(0, np.nan)).values
        # curvature: quadratic coefficient of the path, scaled
        mid = lp.shift(n // 2)
        o['accur_%d' % n] = ((lp + lp.shift(n) - 2 * mid) / (sd * np.sqrt(n))).values
        # is the trend accelerating, steady or decaying
        e1 = (lp - lp.shift(n)).abs() / r.abs().rolling(n).sum()
        e2 = ((lp.shift(n) - lp.shift(2 * n)).abs()
              / r.abs().rolling(n).sum().shift(n))
        o['acefd_%d' % n] = (e1 / e2.replace(0, np.nan)).values
        # volatility acceleration, and whether it moves with price
        o['acvol_%d' % n] = (sd / sd.shift(n)).values
        o['acvv_%d' % n] = ((sd - sd.shift(n)) / sd.rolling(250).std()).values
        o['acpv_%d' % n] = r.rolling(n).corr(r.abs()).values
        o['acjerk_%d' % n] = ((v1 - 2 * v2 + (lp.shift(2 * n) - lp.shift(3 * n)))
                              / (sd * np.sqrt(n))).values
        o['acsgn_%d' % n] = np.sign(v1.values) * np.sign((v1 - v2).values)
        o['acmag_%d' % n] = ((v1 - v2).abs() / v1.abs().replace(0, np.nan)).values
        o['acvr_%d' % n] = (sd / sd.rolling(4 * n).mean()).values
        o['acch_%d' % n] = ((lp - lp.shift(n)).abs()
                            / (lp.shift(n) - lp.shift(2 * n)).abs().replace(0, np.nan)).values
    # acceleration measured only inside each state
    CONDS = conditions(ctx, pair)
    for n in W:
        sd = r.rolling(n).std()
        v1 = lp - lp.shift(n); v2 = lp.shift(n) - lp.shift(2 * n)
        A = {'acc1': (v1 - v2) / (sd * np.sqrt(n)),
             'acc2': (lp + lp.shift(n) - 2 * lp.shift(n // 2)) / (sd * np.sqrt(n)),
             'acc3': sd / sd.shift(n),
             'acc4': v1 / v2.replace(0, np.nan),
             'acc5': (v1.abs() - v2.abs()) / (sd * np.sqrt(n)),
             'acc6': r.rolling(n).corr(r.shift(n))}
        for mk, x in A.items():
            for cn, c in CONDS:
                o['%s_%d%s' % (mk, n, cn)] = _cmean(x, c.astype(float), n).values
    return o


# ---------------- M5: duration extended ----------------
def m5_duration(ctx, pair):
    lp = ctx['lp'][pair]
    r = lp.diff()
    o = {}
    ov = ctx['vol60'][pair]
    states = {
        'ma': (lp > lp.rolling(200).mean()),
        'vt': (ov > ov.rolling(500).median()),
        'pv': (ctx['pv'] > .5),
        'dr': (r.rolling(20).mean() > 0),
        'ds': (ctx['disp'] > ctx['disp'].rolling(500).median()),
        'md': (lp > lp.rolling(60).mean()),
        'mq': (lp > lp.rolling(500).mean()),
        'dl': (r.rolling(60).mean() > 0),
        'ef': ((lp - lp.shift(60)).abs() / r.abs().rolling(60).sum() > .3),
        'e2': ((lp - lp.shift(120)).abs() / r.abs().rolling(120).sum() > .3),
        'vq': (ov > ov.rolling(250).quantile(.67)),
        'pl': (ctx['pv'] < .33),
    }
    for sn, st in states.items():
        chg = (st != st.shift()).fillna(False).values
        ts = _tsince(chg)
        o['duts_%s' % sn] = ts
        o['dust_%s' % sn] = _streak(st.astype(float).values)
        for m in (40, 60, 120, 250, 500, 750, 1000):
            o['duchn_%s_%d' % (sn, m)] = _rsum(chg, m)          # regime churn
            o['duocc_%s_%d' % (sn, m)] = _rsum(st.values, m) / m
            # EMPIRICAL SURVIVAL: of past spells at least this old, what share ran on
            age = pd.Series(ts)
            o['dusrv_%s_%d' % (sn, m)] = (
                (age.rolling(m).apply(lambda a: (a >= a[-1]).mean(), raw=True)).values)
        # age of the current spell against its own history
        for m in (120, 250, 500, 750):
            o['durel_%s_%d' % (sn, m)] = (ts / pd.Series(ts).rolling(m).mean()).values
        # spell age and occupancy inside each state
        for cn, c in conditions(ctx, pair):
            for m in (120, 250, 500, 750):
                o['ducs_%s_%d%s' % (sn, m, cn)] = _cmean(
                    pd.Series(ts, index=lp.index), c.astype(float), m).values
    # time since the last chop episode and how long it ran
    flip = (np.sign(r) != np.sign(r.shift(1)))
    for n in (10, 20, 40, 60, 120, 250):
        chop = (flip.rolling(n).mean() > .6)
        o['duchp_%d' % n] = _tsince(chop.fillna(False).values)
        o['duchl_%d' % n] = _streak(chop.astype(float).values)
    return o


# ---------------- M2: conditional trend ----------------
def m2_conditional(ctx, pair):
    lp = ctx['lp'][pair]
    r = lp.diff()
    ar = r.abs()
    CONDS = conditions(ctx, pair)
    o = {}
    for n in W:
        sd = r.rolling(n).std()
        path = ar.rolling(n).sum()
        net = (lp - lp.shift(n))
        M = {'ef': net.abs() / path,
             'tv': net / (sd * np.sqrt(n)),
             'cv': (lp + lp.shift(n) - 2 * lp.shift(n // 2)) / (sd * np.sqrt(n)),
             'pq': (lp - lp.rolling(n).min()) / (lp.rolling(n).max() - lp.rolling(n).min()),
             'up': r.clip(lower=0).rolling(n).sum() / path,
             'mx': ar.rolling(n).max() / path,
             'sq': sd / ar.rolling(n).mean(),
             'rn': (lp.rolling(n).max() - lp.rolling(n).min()) / (sd * np.sqrt(n)),
             'dn': (-r.clip(upper=0)).rolling(n).sum() / path,
             'gi': ar.rolling(n).std() / ar.rolling(n).mean(),
             # was ar.max()/ar.sum(), which is byte-identical to 'mx' above because
             # path IS ar.rolling(n).sum(). That shipped 700 duplicate signals in the
             # first v7 run. Now a genuinely different tail measure: the top TWO moves.
             'tl': (ar.rolling(n).max() + ar.rolling(n).apply(
                 lambda a: np.partition(a, -2)[-2] if len(a) > 1 else np.nan, raw=True)) / path,
             'sk': r.rolling(n).skew(),
             'kt': r.rolling(n).kurt(),
             'ac': r.rolling(n).corr(r.shift(1))}
        for mk, x in M.items():
            for cn, c in CONDS:
                cs = c.astype(float)
                o['ct%s_%d%s' % (mk, n, cn)] = _cmean(x, cs, n).values
    return o


# ---------------- assembly ----------------
def base_frame(px, pair, ctx):
    o = {}
    o.update(m1_crosssec(ctx, pair))
    o.update(m2_conditional(ctx, pair))
    o.update(m3_structure(ctx, pair))
    o.update(m4_accel(ctx, pair))
    o.update(m5_duration(ctx, pair))
    F = pd.DataFrame(o, index=ctx['lp'].index, copy=False)
    return F.replace([np.inf, -np.inf], np.nan).astype(np.float32)


def expand(block):
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


if __name__ == '__main__':
    import time, json, collections
    px = pd.read_csv(os.path.join(ROOTDATA, 'px28.csv'), index_col=0, parse_dates=True)
    old = {d['s'] for d in json.load(open(os.path.join(ROOTOUT, 'signals.json')))}
    t0 = time.time(); ctx = context(px); tc = time.time() - t0
    t0 = time.time(); F = base_frame(px, 'USDJPY', ctx); tb = time.time() - t0
    names = all_names(list(F.columns))
    cnt = collections.Counter(mech_of(n) for n in names)
    print('context %.0fs | base %.0fs' % (tc, tb))
    print('base %d x %d variants = %d signals' % (F.shape[1], len(VAR), len(names)))
    for k in ('cross-sectional', 'conditional', 'structure', 'acceleration', 'duration'):
        print('  %-16s %6d' % (k, cnt[k]))
    print('OVERLAP with the existing %d names: %d' % (len(old), len(set(names) & old)))
    print('coverage median %.2f' % F.notna().mean().median())
