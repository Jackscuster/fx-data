import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Tasks 7 and 8. The two dimensions the old target could not represent.

Forward efficiency is |net| / path. The absolute value throws away DIRECTION and
the division throws away SCALE, so five batches searched for signals to predict a
number that could not express two thirds of what a trend is.

  TASK 7  signed = net / path, in [-1, +1]. -1 a straight fall, +1 a straight
          rise, 0 chop. Same construction, absolute value removed.
  TASK 8  two scale targets, because they measure different things:
            range_vol = (max - min) over the window, in the pair's own vol units
            path_vol  = sum of |daily moves|, in the same units
          Range is ground covered, path is walking done, and straightness is
          already the ratio between them -- so both are carried explicitly.

WHAT IS RESCORED. Not the 175,634. The ~111 survivors plus the term-structure
features, which is the question worth asking: does a construction that reads chop
on the old target read something DIFFERENT on a signed or scaled one?

AGREEMENT MEANS SOMETHING ELSE ON A SIGNED TARGET, and this is the subtle part.
The old measure counts pairs whose spread shares the POOLED sign. On a signed
target a signal that predicts +0.4 on one pair and -0.4 on another is not
disagreeing -- it is correctly reading two opposite directions, and the old
measure would score it near zero. So a second measure is carried:

  agree_pooled   the old one: share of pairs matching the pooled sign
  agree_dir      share of pairs whose OWN in-sample spread sign holds out of
                 sample, regardless of what the other pairs do

agree_dir does not penalise cross-pair sign differences and is still a real test
-- noise scores 0.5 on it. Both are reported so the difference is visible.

The other four gates carry over unchanged: effect size, monotonicity, decay and
sign-holds all mean what they meant, since none of them reads across pairs.

Writes results/newtarget_signals.csv and newtarget_summary.csv.
"""
import json
import numpy as np, pandas as pd
import sc3
from extsig import split_variant, apply_variant, _frame, MOD
from termstruct import features as ts_features

PX = os.path.join(ROOTDATA, 'px28.csv')
SIG = os.path.join(ROOTOUT, 'signals.json')
SPLIT = pd.Timestamp('2016-01-01')
H = 20
VOLWIN = 60
G_T, G_S, G_M, G_D = 8., .0221, .95, .6
G_A = .893


def targets(px):
    """The old target plus the three new ones, all forward over H days."""
    lp = np.log(px.astype(float))
    net = lp.shift(-H) - lp
    path = lp.diff().abs().shift(-H).rolling(H).sum()
    vol = lp.diff().rolling(VOLWIN).std()          # trailing, so the unit is known
    fmax = lp.shift(-H).rolling(H).max()
    fmin = lp.shift(-H).rolling(H).min()
    rng = (fmax - fmin)
    inf = [np.inf, -np.inf]
    return {
        'eff_abs': (net.abs() / path).replace(inf, np.nan),        # the old target
        'signed': (net / path).replace(inf, np.nan),               # task 7
        'range_vol': (rng / (vol * np.sqrt(H))).replace(inf, np.nan),   # task 8
        'path_vol': (path / (vol * np.sqrt(H))).replace(inf, np.nan),
    }


def score(X, Y, ins):
    """Pooled quintile statistics, plus the direction-corrected agreement."""
    out, per = {}, {}
    for tag, msk in (('i', ins), ('o', ~ins)):
        N = np.zeros(5); S = np.zeros(5); SS = np.zeros(5)
        signs, ct = {}, 0
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
            signs[p] = np.sign(q[4] - q[0])
            ct += 1
        if ct < 20:
            return None
        M = S / np.maximum(N, 1)
        V = (SS - N * M * M) / np.maximum(N - 1, 1)
        spread = M[4] - M[0]
        se = np.sqrt(V[4] / max(N[4], 1) + V[0] / max(N[0], 1))
        rk = np.arange(5) - 2.
        Mc = M - M.mean()
        sg = np.array(list(signs.values()))
        out[tag] = dict(sp=float(spread), t=float(spread / se) if se else np.nan,
                        mono=float((Mc * rk).sum()
                                   / np.sqrt((Mc ** 2).sum() * (rk ** 2).sum())),
                        agree=float((sg == np.sign(spread)).mean()), ct=ct)
        per[tag] = signs
    # direction-corrected: does each pair keep its OWN sign, whatever the others do
    both = set(per['i']) & set(per['o'])
    agree_dir = float(np.mean([per['i'][p] == per['o'][p] for p in both])) if both else np.nan
    i, o = out['i'], out['o']
    return dict(si=i['sp'], ti=i['t'], mi=i['mono'], ai=i['agree'],
                so=o['sp'], to=o['t'], mo=o['mono'], ao=o['agree'],
                agree_dir=agree_dir, n_pairs=len(both),
                dec=abs(o['t']) / max(abs(i['t']), .01),
                held=bool(np.sign(i['sp']) == np.sign(o['sp'])))


def survivor_panels(px):
    """Rebuild the survivor constructions as 28-pair panels."""
    D = pd.DataFrame(json.load(open(SIG)))
    d = D[D.ok.fillna(True)].copy()
    with np.errstate(invalid='ignore', divide='ignore'):
        dc = d.to.abs() / d.ti.abs().clip(lower=.01)
    old = d[(np.sign(d.ti) == np.sign(d.to)) & (d.to.abs() >= G_T)
            & (d.si.abs() >= .02) & (d.ao >= .85) & (d.mo.abs() >= G_M)
            & (dc >= G_D) & (d.tsb.isna() | (d.tsb >= 4))]
    print('rebuilding %d survivor constructions' % len(old), flush=True)
    out = {}
    for batch, grp in old.groupby('b'):
        mod = MOD[batch]
        m = __import__(mod)
        ctx = m.context(px) if hasattr(m, 'context') else None
        want = [(split_variant(r.s) if mod in ('sig6', 'sig7') else (r.s, None)) + (r.s,)
                for _, r in grp.iterrows()]
        acc = {n: {} for _, _, n in want}
        for pair in px.columns:
            try:
                F = _frame(m, mod, px, pair, ctx)
            except Exception as e:                   # noqa: BLE001
                print('  %s %s failed: %s' % (mod, pair, e))
                continue
            for base, spec, name in want:
                if base in F.columns:
                    acc[name][pair] = apply_variant(
                        F[base].astype(float), spec).shift(1).astype(np.float32)
            del F
        for n, cols in acc.items():
            if cols:
                out[n] = pd.DataFrame(cols, index=px.index)
        print('  %s done (%d panels)' % (mod, len(out)), flush=True)
    return out


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    ins = np.asarray(px.index < SPLIT)
    T = targets(px)
    print('targets: %s' % ', '.join(T))
    for k, v in T.items():
        s = v.stack()
        print('  %-10s mean %+.4f  sd %.4f  range %+.3f..%+.3f'
              % (k, s.mean(), s.std(), s.min(), s.max()))

    X = survivor_panels(px)
    X.update({k: v for k, v in ts_features(px).items()})
    print('%d constructions to score' % len(X))

    rows = []
    for tname, tgt in T.items():
        Y = {p: tgt[p] for p in px.columns}
        for name, F in X.items():
            if F.stack().dropna().nunique() <= 5:
                continue
            r = score(F, Y, ins)
            if r is None:
                continue
            r.update(signal=name, target=tname)
            rows.append(r)
        print('  scored against %s' % tname, flush=True)
    S = pd.DataFrame(rows)
    S.to_csv(os.path.join(ROOTOUT, 'newtarget_signals.csv'), index=False)
    report(S)
    return S


def report(S=None):
    if S is None:
        S = pd.read_csv(os.path.join(ROOTOUT, 'newtarget_signals.csv'))
    S['pass_old'] = ((np.sign(S.ti) == np.sign(S.to)) & (S.to.abs() >= G_T)
                     & (S.si.abs() >= G_S) & (S.ao >= G_A)
                     & (S.mo.abs() >= G_M) & (S.dec >= G_D))
    S['pass_dir'] = ((np.sign(S.ti) == np.sign(S.to)) & (S.to.abs() >= G_T)
                     & (S.si.abs() >= G_S) & (S.agree_dir >= G_A)
                     & (S.mo.abs() >= G_M) & (S.dec >= G_D))
    g = (S.groupby('target')
         .agg(n=('signal', 'size'),
              eff=('so', lambda x: x.abs().median()),
              eff_max=('so', lambda x: x.abs().max()),
              t=('to', lambda x: x.abs().median()),
              agree_pooled=('ao', 'mean'), agree_dir=('agree_dir', 'mean'),
              mono=('mo', lambda x: x.abs().mean()),
              held=('held', 'mean'),
              pass_old=('pass_old', 'sum'), pass_dir=('pass_dir', 'sum'))
         .reindex(['eff_abs', 'signed', 'range_vol', 'path_vol']).reset_index())
    print('\nTHE SAME CONSTRUCTIONS AGAINST FOUR TARGETS')
    print(g.to_string(index=False, formatters={
        'eff': '{:.4f}'.format, 'eff_max': '{:.4f}'.format, 't': '{:.1f}'.format,
        'agree_pooled': '{:.3f}'.format, 'agree_dir': '{:.3f}'.format,
        'mono': '{:.3f}'.format, 'held': '{:.3f}'.format}))
    print('\ngates: |t|>=%g effect>=%g agree>=%g mono>=%g decay>=%g'
          % (G_T, G_S, G_A, G_M, G_D))
    print('pass_old uses pooled agreement; pass_dir swaps in the direction-corrected one')

    print('\nTASK 7 -- do any existing constructions carry DIRECTION?')
    sg = S[S.target == 'signed'].reindex(
        S[S.target == 'signed'].so.abs().sort_values(ascending=False).index)
    print(sg[['signal', 'si', 'so', 'to', 'ao', 'agree_dir', 'mo', 'pass_dir']]
          .head(10).to_string(index=False, float_format=lambda v: '%.4f' % v))
    ab = S[S.target == 'eff_abs'].set_index('signal').so.abs()
    sg2 = sg.set_index('signal')
    both = ab.index.intersection(sg2.index)
    print('\n  median |effect|: %.4f on the old target, %.4f on the signed one'
          % (ab[both].median(), sg2.so.abs()[both].median()))
    print('  correlation of the two effect sizes across constructions: %+.3f'
          % np.corrcoef(ab[both], sg2.so.abs()[both])[0, 1])

    print('\nTASK 8 -- scale')
    for t in ('range_vol', 'path_vol'):
        sub = S[S.target == t]
        top = sub.reindex(sub.so.abs().sort_values(ascending=False).index).head(5)
        print('  %s, strongest:' % t)
        print(top[['signal', 'so', 'to', 'ao', 'agree_dir', 'mo', 'pass_old']]
              .to_string(index=False, float_format=lambda v: '%.4f' % v))
    g.to_csv(os.path.join(ROOTOUT, 'newtarget_summary.csv'), index=False)
    print('\nwrote newtarget_signals.csv, newtarget_summary.csv')


if __name__ == '__main__':
    if '--report-only' in sys.argv:
        report()
    else:
        main()
