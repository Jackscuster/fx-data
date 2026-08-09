import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Run the SURVIVING constructions over external data. No new signal families.

The question is not "can we find signals in VIX". It is "do the shapes that already
work on FX price work better, or worse, on data that is not FX price". So the
construction set is frozen at whatever currently clears the gauntlet and the only
thing that changes is what series it is computed on.

HOW THE CONSTRUCTIONS TRANSFER
  Each surviving signal is rebuilt by calling its own sig module against a panel
  whose columns are the external series instead of the 28 pairs. sig6.context()
  reads its panel width from rt.shape[1], so the panel measures -- panelvol,
  paneldisp, coex, xsctop -- recompute over the external universe with no code
  change. That is the brief's "same construction, different universe", done by
  actually reusing the code rather than reimplementing it.

  Two kinds of output come back. Per-series constructions (the duration and
  occupancy family) give one signal per external series. Panel constructions are
  identical for every column by definition, so they give one signal for the whole
  external panel and are labelled source 'ext-panel'.

THE TARGET NEVER CHANGES. Still the 28 FX pairs' forward 20-day efficiency. An
external signal is scored against all 28 exactly as a panel-wide FX signal is, so
pair agreement means the same thing it always did.

Every signal is lagged one bar. Split is IS 1999-2015, OOS 2016-2026, unchanged.

The scorer here is checked against the live one before it is trusted: --verify
rescores a known FX signal and compares to its published statistics.

Writes results/ext_signals.csv and results/ext_retention.csv.
"""
import json, time
import numpy as np, pandas as pd
import sc3                                      # the live scorer, reused rather than mirrored

PX = os.path.join(ROOTDATA, 'px28.csv')
EXT = os.path.join(ROOTDATA, 'ext.csv')
SIG = os.path.join(ROOTOUT, 'signals.json')
COV = os.path.join(ROOTOUT, 'ext_coverage.csv')
SPLIT = pd.Timestamp('2016-01-01')
MINOBS = 400
MOD = {'own-price': 'sig2', 'cross-sectional': 'sig3', 'multi-timeframe': 'sig4',
       'regime-v5': 'sig5', 'trend-duration': 'sig6', 'trend-nonmomentum': 'sig7'}
VARP = {'za_': ('z', 250), 'zb_': ('z', 500), 'zc_': ('z', 750), 'zd_': ('z', 120),
        'ze_': ('z', 60), 'ra_': ('r', 500), 'rb_': ('r', 250), 'rc_': ('r', 120),
        'rd_': ('r', 60)}


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


# ---------------------------------------------------------------- scoring

def score(x, Y, ins):
    """One signal against the whole FX panel. x is a Series, already lagged.

    The per-pair quintile step is sc3.quint itself, not a reimplementation of it.
    An earlier version placed the bin edges over the signal-valid rows; the live
    scorer masks to rows valid in BOTH signal and target first and qcuts the ranks
    of what is left, which moves every edge. The two disagreed by 2.5% on the
    spread. Calling the real function is the only way to be sure they cannot drift.
    """
    out = {}
    for tag, msk in (('i', ins), ('o', ~ins)):
        N = np.zeros(5); S = np.zeros(5); SS = np.zeros(5)
        ct = 0; signs = []
        xm = x[msk]
        if xm.notna().sum() < MINOBS:
            return None
        for p, y in Y.items():
            r = sc3.quint(xm, y[msk])
            if r is None:
                continue
            q, n, v = (np.asarray(a, float) for a in r)
            if not (np.isfinite(q).all() and np.isfinite(v).all()):
                continue
            N += n; S += n * q; SS += (n - 1) * v + n * q * q
            signs.append(np.sign(q[4] - q[0]))
            ct += 1
        if ct < 20:
            return None
        M = S / np.maximum(N, 1)
        V = (SS - N * M * M) / np.maximum(N - 1, 1)
        spread = M[4] - M[0]
        se = np.sqrt(V[4] / max(N[4], 1) + V[0] / max(N[0], 1))
        rk = np.arange(5) - 2.
        Mc = M - M.mean()
        mono = (Mc * rk).sum() / np.sqrt((Mc ** 2).sum() * (rk ** 2).sum())
        sg = np.array(signs)
        agree = float((sg == np.sign(spread)).sum()) / max((sg != 0).sum(), 1)
        out[tag] = dict(sp=float(spread), t=float(spread / se) if se else np.nan,
                        mono=float(mono), agree=agree, ct=ct)
    i, o = out['i'], out['o']
    dec = abs(o['t']) / max(abs(i['t']), .01)
    return dict(si=i['sp'], ti=i['t'], mi=i['mono'], ai=i['agree'], cti=i['ct'],
                so=o['sp'], to=o['t'], mo=o['mono'], ao=o['agree'], cto=o['ct'],
                dec=dec, held=bool(np.sign(i['t']) == np.sign(o['t'])))


# ---------------------------------------------------------------- construction set

def survivor_specs():
    """(module, base column, variant, display name) for everything now surviving."""
    S = json.load(open(SIG))
    out = []
    for d in S:
        if d.get('indep') is None:
            continue
        mod = MOD[d['b']]
        base, spec = (split_variant(d['s']) if mod in ('sig6', 'sig7')
                      else (d['s'], None))
        out.append((mod, base, spec, d['s'], bool(d.get('indep'))))
    return out


def _frame(m, mod, E, src, ctx):
    if mod == 'sig2':
        return m.build(E[src])
    if mod == 'sig5':
        return m.build(E, src, ctx, exclude=frozenset())
    if mod in ('sig6', 'sig7'):
        return m.base_frame(E, src, ctx)
    return m.build(E, src, ctx)


def _panel_cols(m, mod, E, ctx, cols, specs):
    """Columns identical across two different source series -> panel-wide."""
    want = {b for mo, b, _, _, _ in specs if mo == mod}
    try:
        A = _frame(m, mod, E, cols[0], ctx)
        B = _frame(m, mod, E, cols[1], ctx)
    except Exception as e:                           # noqa: BLE001
        print('  %s panel probe failed (%s); treating all as per-series' % (mod, e))
        return set()
    out = set()
    for c in want:
        if c in A.columns and c in B.columns:
            a, b = A[c].astype(float), B[c].astype(float)
            if a.equals(b) or np.allclose(a.fillna(0), b.fillna(0), atol=0, rtol=0):
                out.add(c)
    del A, B
    return out


def build_external(E, specs):
    """-> {(signal, source): series}. Panel constructions collapse to one entry.

    Which constructions are panel-level is decided by MEASUREMENT, not by a list.
    Every module is built against the first two external series and any column that
    comes back identical is panel-wide by definition -- it reads the whole universe,
    not the one column. Hard-coding the set would have worked for sig6, whose panel
    block is separable, and quietly produced 19 identical copies of z_panelvol_40
    for the modules where it is not.
    """
    got, panel_done = {}, set()
    cols = list(E.columns)
    for mod in sorted({m for m, _, _, _, _ in specs}):
        m = __import__(mod)
        try:
            ctx = m.context(E) if hasattr(m, 'context') else None
        except Exception as e:                       # noqa: BLE001
            print('  %s context failed on the external panel: %s' % (mod, e))
            continue
        chop = _panel_cols(m, mod, E, ctx, cols, specs)
        print('  %s: %d of its surviving columns are panel-wide' % (mod, len(chop)))
        for src in cols:
            t0 = time.time()
            try:
                F = _frame(m, mod, E, src, ctx)
            except Exception as e:                   # noqa: BLE001
                print('  %-6s %-10s FAILED %s' % (mod, src, e))
                continue
            for mo, base, spec, name, _ in specs:
                if mo != mod or base not in F.columns:
                    continue
                is_panel = base in chop
                key = (name, 'ext-panel' if is_panel else src)
                if is_panel:
                    if key in panel_done:
                        continue
                    panel_done.add(key)
                got[key] = apply_variant(F[base].astype(float), spec).shift(1)
            del F
            print('  %-6s %-10s %4.0fs  (%d signals so far)'
                  % (mod, src, time.time() - t0, len(got)), flush=True)
    return got


# ---------------------------------------------------------------- verification

def verify(px, Y, ins):
    """Score a known FX signal through THIS scorer and compare to its published row.

    If this does not match, nothing below it means anything.
    """
    S = {d['s']: d for d in json.load(open(SIG))}
    import sig3
    ctx = sig3.context(px)
    F = sig3.build(px, px.columns[0], ctx)
    ok = True
    # sig3 emits the z-scored variants as columns in their own right, so the
    # survivor's name IS the column name -- no prefix stripping for this module.
    for col in ('z_panelvol_40', 'z_paneldisp_40', 'z_panelvol_60'):
        if col not in F.columns or col not in S:
            print('  %-16s not present -- skipped' % col)
            continue
        r = score(F[col].astype(float).shift(1), Y, ins)
        p = S[col]
        d = max(abs(r['si'] - p['si']), abs(r['so'] - p['so']))
        dt = max(abs(r['ti'] - p['ti']), abs(r['to'] - p['to']))
        print('  %-16s spread diff %.2e   t diff %.3f   agree %.3f vs %.3f'
              % (col, d, dt, r['ao'], p['ao']))
        ok &= (d < 5e-4) and (dt < .5)
    print('  scorer %s' % ('MATCHES the live one' if ok else 'DISAGREES -- stop here'))
    return ok


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    ins = np.asarray(px.index < SPLIT)
    T = sc3.target(px)
    Y = {p: T[p] for p in px.columns}

    if '--verify' in sys.argv:
        print('VERIFYING the scorer against published FX statistics')
        return verify(px, Y, ins)
    if '--report-only' in sys.argv:
        return report()

    E = pd.read_csv(EXT, index_col=0, parse_dates=True)
    E = E.reindex(px.index)
    cov = pd.read_csv(COV) if os.path.exists(COV) else pd.DataFrame()
    grp = dict(zip(cov.series, cov.group)) if len(cov) else {}
    specs = survivor_specs()
    print('%d surviving constructions x %d external series' % (len(specs), E.shape[1]))
    print('VERIFYING the scorer first');
    if not verify(px, Y, ins):
        raise SystemExit('scorer does not reproduce the live statistics -- aborting')

    got = build_external(E, specs)
    print('\nbuilt %d external signals; scoring' % len(got), flush=True)
    ind = {n for _, _, _, n, i in specs if i}
    rows = []
    for (name, src), s in got.items():
        r = score(s, Y, ins)
        if r is None:
            rows.append(dict(signal=name, source=src, group=grp.get(src, 'panel'),
                             scorable=False))
            continue
        r.update(signal=name, source=src, group=grp.get(src, 'panel'), scorable=True,
                 was_independent=name in ind)
        rows.append(r)
    D = pd.DataFrame(rows)
    D.to_csv(os.path.join(ROOTOUT, 'ext_signals.csv'), index=False)
    return report(D, specs)


def report(D=None, specs=None):
    """Retention by source, plus which constructions transferred at all."""
    if D is None:
        D = pd.read_csv(os.path.join(ROOTOUT, 'ext_signals.csv'))
    if specs is None:
        specs = survivor_specs()

    # ---- which of the surviving constructions transfer to non-FX data ----
    # A construction that reads a currency pair's two legs has nothing to read on
    # a VIX series. That is a property of the construction, not a failure to
    # report around, so it is counted rather than skipped.
    made = set(D.signal)
    T = pd.DataFrame([dict(signal=n, module=mo, independent=i,
                           transferred=n in made,
                           n_sources=int((D.signal == n).sum()))
                      for mo, _, _, n, i in specs])
    T.to_csv(os.path.join(ROOTOUT, 'ext_transfer.csv'), index=False)
    print('\nCONSTRUCTION TRANSFER: %d of %d survivors produced anything on external data'
          % (int(T.transferred.sum()), len(T)))
    print(T.groupby('module').agg(survivors=('signal', 'size'),
                                  transferred=('transferred', 'sum')).to_string())
    if (~T.transferred).any():
        print('did not transfer: %s'
              % ', '.join(sorted(T[~T.transferred].signal)[:12]))

    # ---- the number that matters: OOS sign retention by data source ----
    B = pd.DataFrame(json.load(open(SIG)))
    B = B[B.ok.fillna(True) & B.si.notna() & B.so.notna()]
    base_all = float((np.sign(B.si) == np.sign(B.so)).mean())
    base_xs = float((np.sign(B[B.b == 'cross-sectional'].si)
                     == np.sign(B[B.b == 'cross-sectional'].so)).mean())
    G = D[D.scorable == True].copy()                                   # noqa: E712
    G['held'] = np.sign(G.si) == np.sign(G.so)
    ret = (G.groupby('group').agg(n=('held', 'size'), retention=('held', 'mean'))
           .reset_index().sort_values('retention', ascending=False))
    ret['vs_price_baseline'] = ret.retention - base_all
    ret.loc[len(ret)] = ['ALL EXTERNAL', len(G), float(G.held.mean()),
                         float(G.held.mean()) - base_all]
    ret.loc[len(ret)] = ['(FX price, all signals)', len(B), base_all, 0.]
    ret.loc[len(ret)] = ['(FX cross-sectional)', int((B.b == 'cross-sectional').sum()),
                         base_xs, base_xs - base_all]
    ret.to_csv(os.path.join(ROOTOUT, 'ext_retention.csv'), index=False)

    print('\nOUT-OF-SAMPLE SIGN RETENTION BY SOURCE')
    print(ret.to_string(index=False,
                        formatters={'retention': '{:.3f}'.format,
                                    'vs_price_baseline': '{:+.3f}'.format}))
    from dedup import gates
    surv = gates(D.assign(ok=D.scorable, tsb=np.nan,
                          s=D.signal + '@' + D.source)) if len(G) else D.head(0)
    print('\nthrough the gauntlet unchanged: %d of %d external signals survive'
          % (len(surv), len(G)))
    if len(surv):
        print(surv[['s', 'group', 'ti', 'to', 'si', 'so', 'ao', 'mo']].to_string(index=False))
    print('\nwrote ext_signals.csv, ext_retention.csv, ext_transfer.csv')
    return D


if __name__ == '__main__':
    main()
