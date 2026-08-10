import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""The surviving constructions, run over the pair rate differentials.

This is the test the whole external-data task exists for. The differentials are
PAIR-SPECIFIC -- one series per pair, not one panel-wide series -- so unlike the
Yahoo work in extsig.py, every construction produces a genuine 28-pair panel and
is scored exactly the way an FX price signal is: built per pair, quintiled
against that pair's own forward efficiency, pooled across pairs.

WHY A CARRY INDEX AND NOT THE RAW DIFFERENTIAL
  Every sig module starts with np.log(px). A rate differential crosses zero, so
  its log is undefined and the whole library returns NaN. The differential is
  therefore accumulated into the thing it actually represents:

      carry index = cumprod(1 + d/100/252)

  whose log-increments ARE the daily carry, so log(index).diff() recovers the
  differential exactly. This is not a proxy: it is the same information in the
  form the constructions can read, and it is the economically real object -- the
  carry actually accrued. Gaps stay gaps; the index is computed over observed
  days only and left NaN elsewhere, so a missing month does not become flat
  carry.

  The raw differential and its z-score are also scored directly, as two
  reference points. They are NOT part of the surviving-construction set and are
  labelled 'direct'.

The seven NZD pairs are carried as all-NaN columns rather than dropped, so the
panel keeps the 28-column shape the modules expect and the cross-sectional
families can still resolve a pair's two legs.

Writes results/carry_signals.csv and results/carry_retention.csv.
"""
import json, time
import numpy as np, pandas as pd
import sc3
from extsig import survivor_specs, apply_variant, _frame

PX = os.path.join(ROOTDATA, 'px28.csv')
CARRY = os.path.join(ROOTDATA, 'carry28.csv')
SIG = os.path.join(ROOTOUT, 'signals.json')
SPLIT = pd.Timestamp('2016-01-01')
MINOBS = 400
MINPAIRS = 10          # pooled stats need a real cross-section; 21 pairs exist


def carry_index(D, idx):
    """Differential in percentage points -> strictly positive accrual index."""
    C = pd.DataFrame(index=idx)
    for p in D.columns:
        s = D[p].dropna()
        if len(s) < MINOBS:
            continue
        C[p] = (1 + s / 100. / 252.).cumprod().reindex(idx)
    return C


def score_panel(X, Y, ins):
    """A pair-specific signal panel against the pair-matched targets.

    Same pooling as the live scorer: sc3.quint per pair, then sufficient
    statistics summed across pairs, with the per-pair spread sign giving the
    agreement rate.
    """
    out = {}
    for tag, msk in (('i', ins), ('o', ~ins)):
        N = np.zeros(5); S = np.zeros(5); SS = np.zeros(5)
        ct = 0; signs = []
        for p in X.columns:
            if p not in Y:
                continue
            r = sc3.quint(X[p][msk], Y[p][msk])
            if r is None:
                continue
            q, n, v = (np.asarray(a, float) for a in r)
            if not (np.isfinite(q).all() and np.isfinite(v).all()):
                continue
            N += n; S += n * q; SS += (n - 1) * v + n * q * q
            signs.append(np.sign(q[4] - q[0]))
            ct += 1
        if ct < MINPAIRS:
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
    return dict(si=i['sp'], ti=i['t'], mi=i['mono'], ai=i['agree'], cti=i['ct'],
                so=o['sp'], to=o['t'], mo=o['mono'], ao=o['agree'], cto=o['ct'],
                dec=abs(o['t']) / max(abs(i['t']), .01),
                held=bool(np.sign(i['t']) == np.sign(o['t'])))


def build_panels(C, specs):
    """-> {construction: DataFrame(dates x pairs)}. One frame per surviving name."""
    out = {}
    for mod in sorted({m for m, _, _, _, _ in specs}):
        m = __import__(mod)
        try:
            ctx = m.context(C) if hasattr(m, 'context') else None
        except Exception as e:                       # noqa: BLE001
            print('  %-5s context failed on the carry panel: %s' % (mod, e))
            continue
        want = [(b, sp, n) for mo, b, sp, n, _ in specs if mo == mod]
        for pair in C.columns:
            t0 = time.time()
            try:
                F = _frame(m, mod, C, pair, ctx)
            except Exception as e:                   # noqa: BLE001
                print('  %-5s %-7s FAILED %s' % (mod, pair, e))
                continue
            for base, spec, name in want:
                if base not in F.columns:
                    continue
                out.setdefault(name, {})[pair] = apply_variant(
                    F[base].astype(float), spec).shift(1)
            del F
            print('  %-5s %-7s %4.0fs' % (mod, pair, time.time() - t0), flush=True)
    return {k: pd.DataFrame(v, index=C.index) for k, v in out.items()}


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    D = pd.read_csv(CARRY, index_col=0, parse_dates=True).reindex(px.index)
    D = D.reindex(columns=px.columns)                # keep 28 columns, NZD all-NaN
    ins = np.asarray(px.index < SPLIT)
    T = sc3.target(px)
    Y = {p: T[p] for p in px.columns}

    built = [p for p in D.columns if D[p].notna().sum() > MINOBS]
    print('%d of 28 pair differentials usable; coverage %.3f'
          % (len(built), D[built].notna().mean().mean()))
    C = carry_index(D, px.index).reindex(columns=px.columns)

    rows = []
    # ---- two reference points, not part of the construction set ----
    for nm, X in (('differential (level)', D),
                  ('differential (250d z)',
                   (D - D.rolling(250).mean()) / D.rolling(250).std())):
        r = score_panel(X.shift(1), Y, ins)
        if r:
            r.update(signal=nm, kind='direct', scorable=True)
            rows.append(r)

    specs = survivor_specs()
    print('running %d surviving constructions over the carry panel' % len(specs))
    P = build_panels(C, specs)
    ind = {n for _, _, _, n, i in specs if i}
    for name, X in P.items():
        r = score_panel(X, Y, ins)
        if r is None:
            rows.append(dict(signal=name, kind='construction', scorable=False))
            continue
        r.update(signal=name, kind='construction', scorable=True,
                 was_independent=name in ind, n_pairs=int(X.notna().any().sum()))
        rows.append(r)
    R = pd.DataFrame(rows)
    R.to_csv(os.path.join(ROOTOUT, 'carry_signals.csv'), index=False)
    return report(R, specs)


def report(R=None, specs=None):
    if R is None:
        R = pd.read_csv(os.path.join(ROOTOUT, 'carry_signals.csv'))
    if specs is None:
        specs = survivor_specs()
    B = pd.DataFrame(json.load(open(SIG)))
    B = B[B.ok.fillna(True) & B.si.notna() & B.so.notna()]
    base = float((np.sign(B.si) == np.sign(B.so)).mean())

    G = R[(R.scorable == True) & R.si.notna()].copy()                  # noqa: E712
    G['held'] = np.sign(G.si) == np.sign(G.so)
    K = G[G.kind == 'construction']
    made = set(R.signal)
    n_tr = sum(1 for _, _, _, n, _ in specs if n in made)

    rows = [dict(group='carry: surviving constructions', n=len(K),
                 retention=float(K.held.mean()) if len(K) else np.nan),
            dict(group='carry: differential direct', n=int((G.kind == 'direct').sum()),
                 retention=float(G[G.kind == 'direct'].held.mean())
                 if (G.kind == 'direct').any() else np.nan),
            dict(group='(FX price, all signals)', n=len(B), retention=base)]
    ret = pd.DataFrame(rows)
    ret['vs_price_baseline'] = ret.retention - base
    ret.to_csv(os.path.join(ROOTOUT, 'carry_retention.csv'), index=False)

    print('\nCONSTRUCTION TRANSFER: %d of %d survivors ran on the carry panel'
          % (n_tr, len(specs)))
    print('\nOUT-OF-SAMPLE SIGN RETENTION')
    print(ret.to_string(index=False, formatters={
        'retention': '{:.3f}'.format, 'vs_price_baseline': '{:+.3f}'.format}))
    if len(K):
        print('\nstrongest by |OOS t|:')
        print(K.reindex(K.to.abs().sort_values(ascending=False).index)
              [['signal', 'si', 'so', 'ti', 'to', 'ao', 'mo', 'held']]
              .head(12).to_string(index=False))
    from dedup import gates
    g = gates(R.assign(ok=R.scorable, tsb=np.nan, s=R.signal))
    print('\nthrough the gauntlet unchanged: %d of %d survive' % (len(g), len(G)))
    if len(g):
        print(g[['s', 'ti', 'to', 'si', 'so', 'ao', 'mo']].to_string(index=False))
    print('\nwrote carry_signals.csv, carry_retention.csv')
    return R


if __name__ == '__main__':
    if '--report-only' in sys.argv:
        report()
    else:
        main()
