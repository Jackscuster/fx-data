import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Gate 7, time stability, for signals scored BEFORE block spreads were stored.

sc6 writes per-block spreads for the v6 batch directly. The v2-v5 batches were
scored without them, so this rebuilds the handful of columns that matter from
their original sig modules -- never from a reimplementation, so the definitions
are guaranteed identical -- and measures the same thing.

THE TEST. Split the history into six equal blocks. Inside each block, recompute
quintiles from scratch and take the top-minus-bottom spread. Count the blocks
whose sign matches the pooled out-of-sample sign. Gate 7 requires at least four
of six.

WHY IT MATTERS HERE. OOS is 2016-2026, which contains COVID, 2020 and 2022 --
three periods of extreme dispersion. A panel-volatility signal would look strong
in a window stuffed with volatility events whether or not it works anywhere
else. Nothing else in the gauntlet can catch a signal that only works in
2020-2022, because every other gate is computed on that same window.

Only the columns needed are kept, but each module still builds its full frame
per pair, so this is not cheap. Run it after a scoring pass, not inside one.
"""
import json, time
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
SIG = os.path.join(ROOTOUT, 'signals.json')
OUTF = os.path.join(ROOTOUT, 'stability.csv')
H = 20
NBLK = 6
SPLIT = pd.Timestamp('2016-01-01')
# batches that already carry block spreads from their scorer
NATIVE = {'trend-duration'}
MOD = {'own-price': 'sig2', 'cross-sectional': 'sig3',
       'multi-timeframe': 'sig4', 'regime-v5': 'sig5'}


def target(s):
    p = np.log(s.astype(float))
    net = (p.shift(-H) - p).abs()
    path = p.diff().abs().shift(-H).rolling(H).sum()
    return (net / path).replace([np.inf, -np.inf], np.nan).values


def frame_for(mod, px, pair, ctx):
    if mod == 'sig2':
        return ctx['m'].build(px[pair])
    if mod == 'sig5':
        return ctx['m'].build(px, pair, ctx['c'], exclude=frozenset())
    return ctx['m'].build(px, pair, ctx['c'])


def blockspread(x, y, blocks):
    """Top-minus-bottom quintile spread inside each block, quintiles per block."""
    out = np.full(len(blocks), np.nan)
    fin = np.isfinite(y) & np.isfinite(x)
    for bi, bm in enumerate(blocks):
        ok = bm & fin
        m = int(ok.sum())
        if m < 100:
            continue
        xv = x[ok]
        if np.unique(xv).size < 5:
            continue
        yy = y[ok][np.argsort(xv, kind='stable')]
        e = m // 5
        if e < 1:
            continue
        out[bi] = yy[-e:].mean() - yy[:e].mean()
    return out


def main(names=None):
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    S = json.load(open(SIG))
    by = {d['s']: d for d in S}

    if names is None:
        # default: whatever currently clears gates 1-6
        D = pd.DataFrame(S)
        D = D[(np.sign(D.ti) == np.sign(D.to)) & (D.to.abs() >= 8) & (D.si.abs() >= .02)
              & (D.ao >= .85) & (D.mo.abs() >= .95)
              & ((D.to.abs() / D.ti.abs().clip(lower=.01)) >= .6)]
        names = list(D.s)
    want = [n for n in names if by.get(n, {}).get('b') not in NATIVE]
    skipped = [n for n in names if n not in want]
    if skipped:
        print('%d already carry native block spreads (v6), skipped here' % len(skipped))
    if not want:
        print('nothing to rebuild')
        return

    groups = {}
    for n in want:
        groups.setdefault(MOD[by[n]['b']], []).append(n)
    print('rebuilding %d signals from %s' % (len(want), ', '.join(sorted(groups))))

    idx = px.index
    edges = np.linspace(0, len(idx), NBLK + 1).astype(int)
    blocks = [np.zeros(len(idx), bool) for _ in range(NBLK)]
    for i in range(NBLK):
        blocks[i][edges[i]:edges[i + 1]] = True
    span = ['%s-%s' % (idx[edges[i]].year, idx[edges[i + 1] - 1].year) for i in range(NBLK)]
    print('blocks: ' + ', '.join(span))

    acc = {n: [] for n in want}
    for mod, cols in groups.items():
        m = __import__(mod)
        ctx = dict(m=m, c=(m.context(px) if hasattr(m, 'context') else None))
        for pair in px.columns:
            t0 = time.time()
            F = frame_for(mod, px, pair, ctx)
            y = target(px[pair])
            have = [c for c in cols if c in F.columns]
            for c in have:
                acc[c].append(blockspread(F[c].shift(1).values.astype(float), y, blocks))
            del F
            print('  %-5s %-7s %d cols %.0fs' % (mod, pair, len(have), time.time() - t0),
                  flush=True)

    rows = []
    for n in want:
        if not acc[n]:
            continue
        BS = np.nanmean(np.stack(acc[n]), axis=0)
        so = by[n]['so']
        hold = int(np.nansum((np.sign(BS) == np.sign(so)) & np.isfinite(BS)))
        r = dict(s=n, b=by[n]['b'], so=so, tsb=hold, passes=bool(hold >= 4))
        for i in range(NBLK):
            r['blk%d' % (i + 1)] = float(BS[i]) if np.isfinite(BS[i]) else None
        rows.append(r)
    T = pd.DataFrame(rows).sort_values('tsb')
    T.to_csv(OUTF, index=False)

    pd.set_option('display.width', 220, 'display.max_columns', 20)
    print('\n' + '=' * 78)
    print('GATE 7 — TIME STABILITY, %d BLOCKS (%s)' % (NBLK, ', '.join(span)))
    print('=' * 78)
    print(T[['s', 'b', 'tsb', 'passes'] + ['blk%d' % (i + 1) for i in range(NBLK)]]
          .to_string(index=False, float_format=lambda x: '%+.4f' % x))
    n_pass = int(T.passes.sum())
    print('\n%d of %d pass gate 7 (sign holds in >= 4 of %d blocks)' % (n_pass, len(T), NBLK))
    if n_pass < len(T):
        print('FAILING: %s' % ', '.join(T[~T.passes].s))


if __name__ == '__main__':
    main(sys.argv[1:] or None)
