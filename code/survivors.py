import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Turn the 32 independent survivors into one usable regime series per pair.

Everything downstream -- the 9-box, multi-timeframe confluence, the detector
ladder, the crisis scoring -- was built before any of these signals existed and
still runs on constructions from the 20,275 era. They all need the same thing:
the survivors expressed as a single number per pair per day.

CONSTRUCTION
  1 rebuild each survivor from its own sig module, so the definition is identical
    to what was scored
  2 z-score each against a trailing 500-day window (causal)
  3 SIGN-ALIGN: multiply by sign(OOS spread) so that for every survivor, higher
    means higher expected forward efficiency -- i.e. more trend, less chop. The
    26 chop detectors are negated; the 6 trend detectors are not.
  4 average across survivors

So the composite reads HIGH = expect straight travel, LOW = expect whipsaw. It is
a trend/chop axis, NOT a direction axis: the efficiency ratio is |net|/path and
carries no sign, so nothing here can say up or down. Anything needing direction
must still get it elsewhere.

Every input is lagged one bar before it enters the composite.

Written to results/survivor_composite.csv (dates x 28 pairs) so the downstream
scripts read it instead of rebuilding 32 signals five different ways.
"""
import json, time
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
SIG = os.path.join(ROOTOUT, 'signals.json')
OUTF = os.path.join(ROOTOUT, 'survivor_composite.csv')
MOD = {'own-price': 'sig2', 'cross-sectional': 'sig3', 'multi-timeframe': 'sig4',
       'regime-v5': 'sig5', 'trend-duration': 'sig6', 'trend-nonmomentum': 'sig7'}
VARP = {'za_': ('z', 250), 'zb_': ('z', 500), 'zc_': ('z', 750), 'zd_': ('z', 120),
        'ze_': ('z', 60), 'ra_': ('r', 500), 'rb_': ('r', 250), 'rc_': ('r', 120),
        'rd_': ('r', 60)}
ZWIN = 500


def split_variant(name):
    for p, spec in VARP.items():
        if name.startswith(p):
            return name[len(p):], spec
    return name, None


def apply_variant(x, spec):
    if spec is None:
        return x
    kind, n = spec
    if kind == 'z':
        return (x - x.rolling(n).mean()) / x.rolling(n).std()
    return x.rolling(n).rank(pct=True)


def independents():
    S = json.load(open(SIG))
    return [d for d in S if d.get('indep') is True]


def build(px=None, force=False):
    """-> DataFrame (dates x pairs). Cached on disk."""
    if not force and os.path.exists(OUTF):
        return pd.read_csv(OUTF, index_col=0, parse_dates=True)
    if px is None:
        px = pd.read_csv(PX, index_col=0, parse_dates=True)
    IND = independents()
    print('composite from %d independent survivors' % len(IND), flush=True)
    by = {}
    for d in IND:
        by.setdefault(MOD[d['b']], []).append(d)

    acc = {p: [] for p in px.columns}
    for mod, sigs in by.items():
        m = __import__(mod)
        ctx = m.context(px) if hasattr(m, 'context') else None
        for pair in px.columns:
            t0 = time.time()
            if mod == 'sig2':
                F = m.build(px[pair])
            elif mod == 'sig5':
                F = m.build(px, pair, ctx, exclude=frozenset())
            elif mod in ('sig6', 'sig7'):
                F = m.base_frame(px, pair, ctx)
            else:
                F = m.build(px, pair, ctx)
            for d in sigs:
                n = d['s']
                base, spec = (split_variant(n) if mod in ('sig6', 'sig7') else (n, None))
                col = base if base in F.columns else (n if n in F.columns else None)
                if col is None:
                    continue
                x = apply_variant(F[col].astype(float), spec).shift(1)
                z = (x - x.rolling(ZWIN).mean()) / x.rolling(ZWIN).std()
                acc[pair].append(z * np.sign(d['so']))       # sign-align to "more trend"
            del F
            print('  %-5s %-7s %.0fs' % (mod, pair, time.time() - t0), flush=True)

    C = pd.DataFrame({p: pd.concat(v, axis=1).mean(axis=1) if v else np.nan
                      for p, v in acc.items()}, index=px.index)
    C = C.replace([np.inf, -np.inf], np.nan)
    C.to_csv(OUTF)
    print('wrote %s  coverage %.2f' % (os.path.basename(OUTF), C.notna().mean().mean()))
    return C


def stats(px=None, C=None):
    """The composite's own regime-detection scorecard. No money metrics."""
    if px is None:
        px = pd.read_csv(PX, index_col=0, parse_dates=True)
    if C is None:
        C = build(px)
    SPLIT = pd.Timestamp('2016-01-01')
    H = 20
    qs, spreads, turns = [], [], []
    for p in px.columns:
        lp = np.log(px[p].astype(float)); r = lp.diff()
        e = ((lp.shift(-H) - lp).abs() / r.abs().shift(-H).rolling(H).sum())
        t = (np.sign(r) != np.sign(r.shift(1))).astype(float).shift(-H).rolling(H).mean()
        d = pd.DataFrame({'c': C[p], 'e': e, 't': t}).dropna()
        d = d[d.index >= SPLIT]
        if len(d) < 400:
            continue
        q = pd.qcut(d.c, 5, labels=False, duplicates='drop')
        if q.nunique() < 5:
            continue
        qs.append(d.e.groupby(q).mean().values)
        turns.append(d.t.groupby(q).mean().values)
        spreads.append(d.e.groupby(q).mean().values[4] - d.e.groupby(q).mean().values[0])
    Q = np.nanmean(np.stack(qs), axis=0)
    T = np.nanmean(np.stack(turns), axis=0)
    spread = float(Q[4] - Q[0])
    agree = float(np.mean(np.sign(spreads) == np.sign(spread)))
    rk = np.arange(5) - 2
    mono = float(np.corrcoef(rk, Q)[0, 1])
    IND = independents()
    best = max(abs(d['so']) for d in IND if d.get('so') is not None)
    bestn = max(IND, key=lambda d: abs(d.get('so') or 0))['s']
    R = pd.DataFrame([dict(
        metric='composite', q1=Q[0], q2=Q[1], q3=Q[2], q4=Q[3], q5=Q[4],
        spread=spread, mono=mono, agree=agree, n_components=len(IND),
        turn_q1=T[0], turn_q5=T[4], turn_spread=float(T[4] - T[0]),
        best_single=best, best_single_name=bestn,
        uplift=spread - best)])
    R.to_csv(os.path.join(ROOTOUT, 'composite_stats.csv'), index=False)
    print('\nCOMPOSITE SCORECARD (OOS, regime detection only)')
    print('  quintile efficiency  ' + '  '.join('%.4f' % v for v in Q))
    print('  Q5-Q1 spread %+.4f | monotonicity %+.3f | pair agreement %.3f'
          % (spread, mono, agree))
    print('  turn frequency Q1 %.4f -> Q5 %.4f (spread %+.4f)' % (T[0], T[4], T[4] - T[0]))
    print('  best single survivor %s at %.4f -> composite adds %+.4f'
          % (bestn, best, spread - best))
    return R


if __name__ == '__main__':
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    C = build(px, force=True)
    stats(px, C)
    SPLIT = pd.Timestamp('2016-01-01')
    print('\ncomposite: HIGH = expect straight travel, LOW = expect whipsaw')
    print(C.describe().T[['count', 'mean', 'std', 'min', 'max']].head(6)
          .to_string(float_format=lambda x: '%.3f' % x))
    # does it actually predict forward efficiency?
    H = 20
    rows = []
    for p in px.columns:
        lp = np.log(px[p].astype(float)); r = lp.diff()
        y = ((lp.shift(-H) - lp).abs() / r.abs().shift(-H).rolling(H).sum())
        d = pd.DataFrame({'c': C[p], 'y': y}).dropna()
        oos = d.index >= SPLIT
        if oos.sum() > 400:
            q = pd.qcut(d.c[oos], 5, labels=False, duplicates='drop')
            rows.append(d.y[oos].groupby(q).mean().values)
    M = np.nanmean(np.stack([r for r in rows if len(r) == 5]), axis=0)
    print('\nOOS forward 20d efficiency by composite quintile (28 pairs pooled):')
    print('  ' + '  '.join('Q%d %.4f' % (i + 1, v) for i, v in enumerate(M)))
    print('  Q5-Q1 spread %+.4f   (baseline efficiency 0.2226)' % (M[4] - M[0]))
