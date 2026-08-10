import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Would a relaxed agreement gate be admitting structure, or admitting noise?

Gate 4 currently demands 25 of 28 pairs share the pooled sign. The proposal is a
subset rule for the trend side: let a signal through on fewer pairs, on the view
that something real can work on the pairs that trend and do nothing on the pairs
that chop.

That proposal cannot be judged by counting how many extra signals it admits,
because a looser gate always admits more. The question is whether it admits more
than NOISE would at the same setting. So the whole agreement sweep is run twice:
once on the real target, once against each of the 50 circularly-shifted target
panels from inflation.py, where the true effect is zero by construction.

Two things get compared at every threshold:

  COUNT     real survivors against the null distribution of survivors
  CLUSTER   which pairs carry the survivors, real against null

The second matters as much as the first. If the null reproduces the same handful
of pairs doing the carrying, then the clustering is a property of the panel --
some pairs are more correlated with the rest, or have longer histories, or lower
volatility -- and not evidence of a trend effect at all.

Everything comes from the saved accumulators, which hold per-pair spread SIGNS
for every signal in every run. That is exactly what an agreement rule reads, so
the null is evaluated by the same arithmetic as the real gate rather than an
approximation of it.

Needs results/_infl_{i,o}.npz, which are gitignored -- local only, like the sweep.
Writes results/subset_null.csv and results/subset_null_pairs.csv.
"""
import json
import numpy as np, pandas as pd
from inflation import Acc, NRUN, G_T, G_S, G_M, G_D
from pairtrend import DIRS, per_pair_spreads, pair_trend, spearman

SIG = os.path.join(ROOTOUT, 'signals.json')
THRESH = [.60, .65, .70, .75, .786, .821, .857, .893]      # /28: 17..25 pairs


def load_acc():
    A = {}
    for tag in ('i', 'o'):
        f = os.path.join(ROOTOUT, '_infl_%s.npz' % tag)
        if not os.path.exists(f):
            raise SystemExit('needs %s -- the accumulators are local only, so this '
                             'runs where the sweep ran.' % os.path.basename(f))
        z = np.load(f)
        a = Acc(z['N'].shape[1], NRUN, z['SGN'].shape[2])
        a.N, a.S, a.SS, a.CT, a.SGN = z['N'], z['S'], z['SS'], z['CT'], z['SGN']
        A[tag] = a
    return A


def null_sweep(A, pairs):
    """Survivor counts and pair-carrying rates per threshold, per run."""
    rows, carry = [], {t: np.zeros(len(pairs)) for t in THRESH}
    tot = {t: 0 for t in THRESH}
    for r in range(NRUN):
        si, ti, mi, ai, cti = A['i'].stats(r)
        so, to, mo, ao, cto = A['o'].stats(r)
        ok = (cti >= 20) & (cto >= 20) & np.isfinite(ti) & np.isfinite(to)
        with np.errstate(invalid='ignore', divide='ignore'):
            dec = np.abs(to) / np.maximum(np.abs(ti), .01)
        base = (ok & (np.sign(ti) == np.sign(to)) & (np.abs(to) >= G_T)
                & (np.abs(si) >= G_S) & (np.abs(mo) >= G_M) & (dec >= G_D))
        sg = A['o'].SGN[r]
        for t in THRESH:
            sel = base & (ao >= t)
            n = int(sel.sum())
            rows.append(dict(run=r, thresh=t, n=n))
            if n:
                # a pair "carries" a survivor when its own spread sign matches
                # the pooled one -- the same test the agreement rate applies
                m = (sg[sel] == np.sign(so[sel])[:, None])
                carry[t] += m.sum(0)
                tot[t] += n
    N = pd.DataFrame(rows)
    C = {t: (carry[t] / tot[t] if tot[t] else np.full(len(pairs), np.nan))
         for t in THRESH}
    return N, C


def real_sweep(pairs):
    """The same sweep on the real target, with per-pair signs from the score npz."""
    D = pd.DataFrame(json.load(open(SIG)))
    d = D[D.ok.fillna(True)].copy()
    with np.errstate(invalid='ignore', divide='ignore'):
        dec = d.to.abs() / d.ti.abs().clip(lower=.01)
    base = d[(np.sign(d.ti) == np.sign(d.to)) & (d.to.abs() >= G_T)
             & (d.si.abs() >= G_S) & (d.mo.abs() >= G_M) & (dec >= G_D)
             & (d.tsb.isna() | (d.tsb >= 4))].copy()
    print('reach the agreement gate: %d signals' % len(base))

    SPR, miss = {}, 0
    for batch, grp in base.groupby('b'):
        if batch not in DIRS:
            miss += len(grp)
            continue
        pr, sp = per_pair_spreads(batch, list(grp.s))
        if pr and list(pr) != list(pairs):
            raise SystemExit('pair order differs between score dirs')
        SPR.update(sp)
    if miss:
        print('%d have no per-pair npz (v7 pools statistics only)' % miss)

    out, C = [], {}
    for t in THRESH:
        sel = base[base.ao >= t]
        out.append(dict(thresh=t, n=len(sel)))
        acc = np.zeros(len(pairs)); k = 0
        for _, r in sel.iterrows():
            v = SPR.get(r.s)
            if v is None:
                continue
            acc += (np.sign(np.nan_to_num(v)) == np.sign(r.so))
            k += 1
        C[t] = acc / k if k else np.full(len(pairs), np.nan)
    return pd.DataFrame(out), C, base


def main():
    PT = pair_trend()
    eff = dict(zip(PT.pair, PT.eff_both))
    pairs = sorted(eff)
    A = load_acc()
    print('sweeping the agreement threshold on the real target and %d nulls' % NRUN)
    R, CR, base = real_sweep(pairs)
    N, CN = null_sweep(A, pairs)

    rows = []
    for t in THRESH:
        ns = N[N.thresh == t].n.values
        real = int(R[R.thresh == t].n.iloc[0])
        p = (1 + int((ns >= real).sum())) / (NRUN + 1)
        rho = (spearman(CR[t], CN[t]) if np.isfinite(CR[t]).all()
               and np.isfinite(CN[t]).all() else np.nan)
        rows.append(dict(thresh=t, pairs_required=int(np.ceil(t * 28)), real=real,
                         null_med=float(np.median(ns)), null_p90=float(np.quantile(ns, .9)),
                         null_max=int(ns.max()), null_mean=float(ns.mean()),
                         ratio=real / max(np.mean(ns), 1e-9), p_emp=p,
                         carry_corr_real_vs_null=rho))
    S = pd.DataFrame(rows)
    S.to_csv(os.path.join(ROOTOUT, 'subset_null.csv'), index=False)

    # If the carrying pattern is not trendiness, what is it? The survivor set is
    # overwhelmingly panel-volatility chop detectors, so the natural candidate is
    # simply how tightly a pair's own forward efficiency tracks the panel's.
    import sc3
    px = pd.read_csv(os.path.join(ROOTDATA, 'px28.csv'), index_col=0, parse_dates=True)
    T = sc3.target(px)
    panel = T.mean(axis=1)
    pcorr = {p: float(T[p].corr(panel)) for p in px.columns}

    P = pd.DataFrame({'pair': pairs, 'eff': [eff[p] for p in pairs],
                      'panel_corr': [pcorr[p] for p in pairs]})
    for t in (.75, .857, .893):
        P['real_%.3f' % t] = CR[t]
        P['null_%.3f' % t] = CN[t]
    P.to_csv(os.path.join(ROOTOUT, 'subset_null_pairs.csv'), index=False)

    print('\nAGREEMENT SWEEP: real survivors against the shifted-target null')
    print('%-7s %6s %7s %8s %8s %8s %7s %7s'
          % ('thresh', 'pairs', 'real', 'null med', 'null p90', 'null max',
             'ratio', 'p'))
    for _, r in S.iterrows():
        print('%-7.3f %6d %7d %8.1f %8.1f %8d %7.1fx %7.3f'
              % (r.thresh, r.pairs_required, r.real, r.null_med, r.null_p90,
                 r.null_max, r.ratio, r.p_emp))

    print('\nWHICH PAIRS CARRY THE SURVIVORS, real vs null')
    print('%-8s %8s %9s %9s %9s %9s' % ('pair', 'eff', 'real .75', 'null .75',
                                        'real .857', 'null .857'))
    ordr = np.argsort(-np.array(CR[.75]))
    for i in ordr[:10]:
        print('%-8s %8.4f %9.3f %9.3f %9.3f %9.3f'
              % (pairs[i], eff[pairs[i]], CR[.75][i], CN[.75][i],
                 CR[.857][i], CN[.857][i]))
    for t in (.75, .857):
        print('  rank correlation real vs null carrying at %.3f: %+.3f'
              % (t, spearman(CR[t], CN[t])))
        print('  REAL carrying vs pair TRENDINESS:       %+.3f'
              % spearman(CR[t], [eff[p] for p in pairs]))
        print('  REAL carrying vs PANEL SENSITIVITY:     %+.3f'
              % spearman(CR[t], [pcorr[p] for p in pairs]))
    print('\nwrote subset_null.csv, subset_null_pairs.csv')
    return S, P


if __name__ == '__main__':
    main()
