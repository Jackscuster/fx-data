import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Final settings, chosen on IS, confirmed once on the holdout. Full report.

TWO DECISIONS ARE TAKEN HERE, both on in-sample only.

  1 ACTIVITY: joint or separate. A weak-activity bar may need stronger
    structural evidence before being called trending, since low participation
    makes a clean sequence less meaningful. That is a one-parameter idea -- how
    much extra evidence -- so the bump is SWEPT rather than guessed. bump=0 is
    the separate cut; larger values raise the trend bar for weak activity and
    lower it for strong. The earlier joint/separate tests in 16.4r and 16.4s
    used a single arbitrary bump of 0.5 and are superseded.

  2 CHOP COMPONENT SET. The drop-one in 16.4t found that removing `tests`
    improved chop by +0.032, but that was measured on the holdout. It is redone
    here on IS and only adopted if it holds there.

THEN THE FULL REPORT at whatever those two decisions produce: separation, run
length, transition diagonal, coverage and per-pair, with TREND AND CHOP REPORTED
SEPARATELY throughout, IS and OOS side by side, episode-based significance rather
than per-bar, and a surrogate null on the final classifier.

Writes results/final_report.csv, results/final_pairs.csv.
"""
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
SPLIT = pd.Timestamp('2016-01-01')
NSHUF = int(os.environ.get('FX_NSHUF', 15))
BUMPS = (0.0, 0.25, 0.5, 0.75, 1.0, 1.5)
MINSHARE = 0.02
# The two decisions this file takes, resolved on IS and then frozen here so
# export.py reads them rather than re-deriving them.
DROP_TESTS = True        # IS chop |sep| 0.140 -> 0.151 without `tests`
BUMP = 0.75              # joint activity cut; beats separate by 0.002, a tie

from structval import properties, surrogate
from twoscores import (raw_parts, classify, CELLS, sep_one_vs_rest, PROPS,
                       stats, two_scores)
from combined import confirm, DWELL
from classifier import zfit
from ninestate import raw_axes, tercile
from episodes import episodes
from chopmore import new_chop

ACTW = {'weak': 1.0, 'medium': 0.0, 'strong': -1.0}


def scores(px, fit, drop_tests=False):
    T, C = raw_parts(px)
    C = dict(C)
    if drop_tests:
        C.pop('tests', None)
    zt, zc = zfit(T, fit), zfit(C, fit)
    return sum(zt[k] for k in T), sum(zc[k] for k in C)


def activity(px, fit):
    a = tercile(raw_axes(px)['scale'], fit).replace(
        {0.0: 'weak', 1.0: 'medium', 2.0: 'strong'})
    return a.where(a.isin(list(ACTW)))


def grid(tr, ch, act, fit, bump):
    adj = tr - act.replace(ACTW).astype(float) * bump
    lab, _ = classify(adj, ch, fit)
    return confirm((act + ' ' + lab).where(lab.notna() & act.notna()), DWELL)


def mean_sep(lab, P, mask):
    sts = sorted(pd.unique(lab[mask].stack()))
    S = sep_one_vs_rest(lab, P, mask, sts)
    return float(np.nanmean([abs(S[(s, c)]) for s in sts for c in PROPS])), sts


def axis_sep(sc, P, fit, mask):
    m = np.nanmedian(np.where(fit[:, None], sc.values, np.nan))
    L = confirm(pd.DataFrame(np.where(sc > m, 'high', 'low'), index=sc.index,
                             columns=sc.columns).where(sc.notna()), DWELL)
    S = sep_one_vs_rest(L, P, mask, ['high', 'low'])
    return float(np.nanmean([abs(S[('high', c)]) for c in PROPS])), L


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    fit = np.asarray(px.index < SPLIT)
    oos = ~fit
    P = properties(px)
    act = activity(px, fit)

    print('DECISION 1 -- CHOP COMPONENT SET, on IS only')
    for drop in (False, True):
        tr, ch = scores(px, fit, drop_tests=drop)
        g, _ = axis_sep(ch, P, fit, fit)
        print('  %-22s IS chop |sep| %.3f'
              % ('five components' if not drop else 'without `tests`', g))
    tr5, ch5 = scores(px, fit, False)
    tr4, ch4 = scores(px, fit, True)
    g5, _ = axis_sep(ch5, P, fit, fit)
    g4, _ = axis_sep(ch4, P, fit, fit)
    DROP = g4 > g5
    print('  -> %s' % ('drop `tests`' if DROP else 'keep all five'))
    tr, ch = (tr4, ch4) if DROP else (tr5, ch5)

    print('\nDECISION 2 -- ACTIVITY, joint or separate. bump swept on IS.')
    print('  %6s %8s %10s %9s %8s' % ('bump', 'cells', 'mean|sep|', 'min share',
                                      'usable'))
    rows = []
    for b in BUMPS:
        L = grid(tr, ch, act, fit, b)
        g, sts = mean_sep(L, P, fit)
        cv = L[fit].stack().value_counts(normalize=True)
        usable = int((cv >= MINSHARE).sum())
        print('  %6.2f %8d %10.3f %9.3f %8d'
              % (b, len(sts), g, cv.min(), usable))
        rows.append(dict(bump=b, cells=len(sts), is_sep=g, min_share=cv.min(),
                         usable=usable))
    R = pd.DataFrame(rows)
    ok = R[R.min_share >= MINSHARE]
    if not len(ok):
        ok = R
    best = ok.sort_values('is_sep', ascending=False).iloc[0]
    BUMP = float(best.bump)
    print('  -> chosen on IS: bump=%.2f (%s)'
          % (BUMP, 'SEPARATE' if BUMP == 0 else 'JOINT'))

    lab = grid(tr, ch, act, fit, BUMP)
    sep_lab = grid(tr, ch, act, fit, 0.0)

    print('\n' + '=' * 72)
    print('FINAL REPORT. chop set = %s, activity bump = %.2f'
          % ('four' if DROP else 'five', BUMP))

    print('\nTHE TWO AXES SEPARATELY, never blended')
    print('  %-6s %10s %10s %11s' % ('axis', 'IS |sep|', 'OOS |sep|', 'surrogate'))
    rng = np.random.default_rng(24601)
    sacc = {'trend': [], 'chop': [], 'grid': []}
    for i in range(NSHUF):
        px2 = surrogate(px, 'sign', rng)
        P2 = properties(px2)
        t2, c2 = scores(px2, fit, DROP)
        a2 = activity(px2, fit)
        sacc['trend'].append(axis_sep(t2, P2, fit, oos)[0])
        sacc['chop'].append(axis_sep(c2, P2, fit, oos)[0])
        sacc['grid'].append(mean_sep(grid(t2, c2, a2, fit, BUMP), P2, oos)[0])
        if (i + 1) % 5 == 0:
            print('  ... %d/%d surrogates' % (i + 1, NSHUF), flush=True)
    out = []
    for nm, sc in (('trend', tr), ('chop', ch)):
        a, La = axis_sep(sc, P, fit, fit)
        b, Lb = axis_sep(sc, P, fit, oos)
        sv = np.nanmean(sacc[nm])
        st = stats(Lb, oos, ['high', 'low'])
        print('  %-6s %10.3f %10.3f %11.3f   corrected %+.3f'
              % (nm, a, b, sv, b - sv))
        print('         high: share %.3f run %.0f diag %.3f | low: %.3f %.0f %.3f'
              % (st['high']['share'], st['high']['run'], st['high']['diag'],
                 st['low']['share'], st['low']['run'], st['low']['diag']))
        out.append(dict(item=nm, is_sep=a, oos_sep=b, surrogate=sv,
                        corrected=b - sv,
                        hi_share=st['high']['share'], hi_run=st['high']['run'],
                        hi_diag=st['high']['diag']))

    print('\nTHE FULL GRID')
    for nm, L, mask in (('IS', lab, fit), ('OOS', lab, oos)):
        g, sts = mean_sep(L, P, mask)
        cv = L[mask].stack().value_counts(normalize=True)
        cells = L[mask].shape[0] * L[mask].shape[1]
        cov = L[mask].notna().sum().sum() / cells
        st = stats(L, mask, sts)
        runs = np.array([st[s]['run'] for s in sts], float)
        dia = np.array([st[s]['diag'] for s in sts], float)
        print('  %-4s %2d cells  mean|sep| %.3f  coverage %.3f  min share %.3f'
              '  median run %.0f  diagonal %.3f'
              % (nm, len(sts), g, cov, cv.min(), np.nanmedian(runs),
                 np.nanmean(dia)))
        out.append(dict(item='grid ' + nm, oos_sep=g, coverage=cov,
                        min_share=cv.min(), median_run=float(np.nanmedian(runs)),
                        diagonal=float(np.nanmean(dia)), cells=len(sts)))
    gsv = np.nanmean(sacc['grid'])
    gO, _ = mean_sep(lab, P, oos)
    print('  grid surrogate %.3f -> corrected %+.3f' % (gsv, gO - gsv))
    out.append(dict(item='grid null', oos_sep=gO, surrogate=gsv,
                    corrected=gO - gsv))

    print('\n  per cell, holdout')
    sts = sorted(pd.unique(lab[oos].stack()))
    S = sep_one_vs_rest(lab, P, oos, sts)
    st = stats(lab, oos, sts)
    print('    %-18s %8s %7s %6s %6s' % ('cell', 'sep', 'share', 'run', 'diag'))
    for s in sts:
        print('    %-18s %8.3f %7.3f %6.0f %6.3f'
              % (s, np.nanmean([abs(S[(s, c)]) for c in PROPS]),
                 st[s]['share'], st[s]['run'], st[s]['diag']))

    print('\nEPISODE-BASED SIGNIFICANCE, not per-bar')
    E = episodes(lab, P)
    nb = int(lab[oos].notna().sum().sum())
    print('  %d holdout bars -> %d episodes (%.1fx). Every significance figure'
          % (nb, len(E), nb / max(len(E), 1)))
    print('  above is a surrogate randomisation, which carries the dependence')
    print('  in full; no per-bar t-statistic appears anywhere in this report.')

    print('\nPER PAIR, trend and chop separately, holdout')
    pr = []
    for nm, sc in (('trend', tr), ('chop', ch)):
        _, L = axis_sep(sc, P, fit, oos)
        vals = {}
        for p in px.columns:
            v = L[p][oos]
            g = []
            for c in PROPS:
                d = pd.DataFrame({'s': v, 'v': P[c][p][oos]}).dropna()
                if d.s.nunique() < 2 or len(d) < 200:
                    g.append(np.nan); continue
                gm = d.groupby('s').v.mean()
                g.append((gm.max() - gm.min()) / d.v.std())
            vals[p] = float(np.nanmean(g))
        v = np.array(list(vals.values()))
        print('  %-6s median %.3f, range %.3f (%s) to %.3f (%s)'
              % (nm, np.nanmedian(v), np.nanmin(v),
                 min(vals, key=vals.get), np.nanmax(v), max(vals, key=vals.get)))
        for p, x in vals.items():
            pr.append(dict(axis=nm, pair=p, sep=x))
    pd.DataFrame(pr).to_csv(os.path.join(ROOTOUT, 'final_pairs.csv'), index=False)
    pd.DataFrame(out).to_csv(os.path.join(ROOTOUT, 'final_report.csv'),
                             index=False)
    print('\nwrote final_report.csv and final_pairs.csv')
    return DROP, BUMP


if __name__ == '__main__':
    main()
