import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Old nine-box against new nine-state, the same battery on both.

FOUR OBJECTS, and the last two exist to answer whether the merge earns its place:

  nine-box       straightness x scale terciles, the original     9 states
  shape3xact     three-shape partition x activity terciles       9 states
  shape3         the shape axis alone                            3 states
  activity       the scale axis alone                            3 states

If shape3xact does not beat BOTH of its own components it is not a merge, it is
an aggregation, and the extra eight states are decoration.

EVERY CLASSIFIER GETS THE SAME 5-BAR DWELL, including the nine-box. Persistence
drives separation on autocorrelated properties (16.4c), so comparing a dwelled
classifier with an undwelled one measures the dwell, not the classifier. The
nine-box is reported undwelled as well, since that is how it ships, but the
like-for-like row is the dwelled one.

AND EVERY NUMBER IS NULL-CORRECTED, with the surrogate carrying the identical
classifier, state count and dwell. Raw separation is not comparable across
classifiers with different state counts; corrected separation is.

Writes results/oldnew.csv and results/oldnew_pairs.csv.
"""
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
SPLIT = pd.Timestamp('2016-01-01')
NSHUF = int(os.environ.get('FX_NSHUF', 40))
MODE, NW = 'relaxed', 5

from structval import properties, separation, persistence, surrogate, MIN_SHARE
from combined import confirm, DWELL, NEUT
from ninestate import nine, raw_axes, tercile
from structsel import chosen_cell
from shape3 import three_state
from episodes import episodes, sep_ep

MAGP = ['realised_vol', 'avg_abs_move']
ACT = {0.0: 'weak', 1.0: 'medium', 2.0: 'strong'}


def build(px, fit):
    _, B, D, R = chosen_cell()
    sh = three_state(px, NW, B, D, R, MODE)
    act = tercile(raw_axes(px)['scale'], fit).replace(ACT)
    act = act.where(act.isin(list(ACT.values())))
    prod = (act + ' ' + sh).where(sh.notna() & (sh != '') & act.notna())
    return {'nine-box (dwelled)': confirm(nine(px, fit)[0], DWELL),
            'shape3 x activity': confirm(prod, DWELL),
            'shape3 alone': confirm(sh.where(sh != ''), DWELL),
            'activity alone': confirm(act, DWELL),
            'nine-box (as shipped)': nine(px, fit)[0]}


def sep(lab, P, cols):
    return float(separation(lab, P).gap_sd.reindex(cols).mean())


def pair_sep(lab, P, cols, pairs):
    out = {}
    for p in pairs:
        v = lab[p][lab.index >= SPLIT]
        vals = []
        for c in cols:
            d = pd.DataFrame({'s': v, 'v': P[c][p][P[c].index >= SPLIT]}).dropna()
            d = d[d.s != '']
            keep = d.s.value_counts(normalize=True)
            d = d[d.s.isin(keep[keep >= MIN_SHARE].index)]
            if d.s.nunique() < 2 or len(d) < 200:
                vals.append(np.nan); continue
            g = d.groupby('s').v.mean()
            vals.append((g.max() - g.min()) / d.v.std())
        out[p] = float(np.nanmean(vals))
    return out


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    fit = px.index < SPLIT
    P = properties(px)
    LAB = build(px, fit)
    pairs = list(px.columns)
    print('OLD vs NEW. shape3 = %s, N=%d. dwell M=%d on every classifier.'
          % (MODE, NW, DWELL))

    real = {}
    for k, v in LAB.items():
        real[k] = dict(shape=sep(v, P, NEUT), act=sep(v, P, MAGP),
                       ep=sep_ep(episodes(v, P)))

    print('\nRAW, holdout')
    print('  %-22s %8s %8s %8s %7s %7s %7s %7s'
          % ('classifier', 'shape', 'activity', 'episode', 'states', 'run',
             'diag', 'minshr'))
    rows = []
    for k, v in LAB.items():
        pr = persistence(v)
        o = v[v.index >= SPLIT].stack().replace('', np.nan).dropna()
        cv = o.value_counts(normalize=True)
        print('  %-22s %8.3f %8.3f %8.3f %7d %7.0f %7.3f %7.3f'
              % (k, real[k]['shape'], real[k]['act'], real[k]['ep'], cv.size,
                 pr['median_run'], pr['diagonal'], cv.min()))
        rows.append(dict(classifier=k, shape=real[k]['shape'],
                         activity=real[k]['act'], episode=real[k]['ep'],
                         n_states=int(cv.size), median_run=pr['median_run'],
                         diagonal=pr['diagonal'], min_share=cv.min(),
                         coverage=float(len(o) / (v[v.index >= SPLIT].shape[0]
                                                  * v.shape[1]))))

    print('\nREFIT STABILITY, pre-2016 labels after refitting through 2020')
    px20 = px[px.index < pd.Timestamp('2021-01-01')]
    L20 = build(px20, px20.index < SPLIT)
    for k in LAB:
        a = LAB[k][fit].stack()
        b = L20[k].reindex(LAB[k].index)[fit].stack()
        j = pd.concat([a.rename('x'), b.rename('y')], axis=1).dropna()
        agree = 100 * (j.x == j.y).mean()
        print('  %-22s %.2f%% of %d pair-days' % (k, agree, len(j)))
        for r in rows:
            if r['classifier'] == k:
                r['refit'] = agree

    print('\nNULLS, %d draws each kind, same surrogate serves every classifier'
          % NSHUF)
    rng = np.random.default_rng(271828)
    acc = {kind: {k: {'shape': [], 'act': [], 'ep': []} for k in LAB}
           for kind in ('sign', 'iid')}
    pacc = {k: [] for k in LAB}
    for i in range(NSHUF):
        for kind in ('sign', 'iid'):
            px2 = surrogate(px, kind, rng)
            P2 = properties(px2)
            L2 = build(px2, fit)
            for k in LAB:
                acc[kind][k]['shape'].append(sep(L2[k], P2, NEUT))
                acc[kind][k]['act'].append(sep(L2[k], P2, MAGP))
                acc[kind][k]['ep'].append(sep_ep(episodes(L2[k], P2)))
                if kind == 'sign':
                    pacc[k].append(pair_sep(L2[k], P2, NEUT, pairs))
        if (i + 1) % 10 == 0:
            print('  %d/%d' % (i + 1, NSHUF), flush=True)

    print('\nCORRECTED = real minus its own surrogate. THIS is the comparison.')
    print('  %-22s %-5s %9s %9s %9s'
          % ('classifier', 'null', 'shape', 'activity', 'episode'))
    for k in LAB:
        for kind in ('sign', 'iid'):
            c = {m: real[k][m] - np.nanmean(acc[kind][k][m])
                 for m in ('shape', 'act', 'ep')}
            print('  %-22s %-5s %+9.3f %+9.3f %+9.3f'
                  % (k, kind, c['shape'], c['act'], c['ep']))
            for r in rows:
                if r['classifier'] == k:
                    r['corr_shape_' + kind] = c['shape']
                    r['corr_act_' + kind] = c['act']
                    r['corr_ep_' + kind] = c['ep']
    R = pd.DataFrame(rows)
    R.to_csv(os.path.join(ROOTOUT, 'oldnew.csv'), index=False)

    print('\nPER PAIR, corrected shape separation, own surrogate per pair')
    prow = []
    for k in LAB:
        rp = pair_sep(LAB[k], P, NEUT, pairs)
        S = pd.DataFrame(pacc[k])
        pos = 0
        for p in pairs:
            c = rp[p] - S[p].mean()
            prow.append(dict(classifier=k, pair=p, real=rp[p],
                             surrogate=S[p].mean(), corrected=c))
            pos += int(c > 0)
        print('  %-22s %2d of %d pairs positive, median %+.3f'
              % (k, pos, len(pairs),
                 np.median([rp[p] - S[p].mean() for p in pairs])))
    pd.DataFrame(prow).to_csv(os.path.join(ROOTOUT, 'oldnew_pairs.csv'),
                              index=False)

    print('\nDOES THE MERGE BEAT ITS OWN COMPONENTS?')
    for kind in ('sign', 'iid'):
        m = R[R.classifier == 'shape3 x activity'].iloc[0]
        s = R[R.classifier == 'shape3 alone'].iloc[0]
        a = R[R.classifier == 'activity alone'].iloc[0]
        n = R[R.classifier == 'nine-box (dwelled)'].iloc[0]
        print('  %s null:' % kind)
        for met, nm in (('shape', 'shape'), ('act', 'activity')):
            print('    %-9s merge %+.3f   shape3 %+.3f   activity %+.3f'
                  '   nine-box %+.3f'
                  % (nm, m['corr_%s_%s' % (met, kind)],
                     s['corr_%s_%s' % (met, kind)],
                     a['corr_%s_%s' % (met, kind)],
                     n['corr_%s_%s' % (met, kind)]))
    print('\nwrote oldnew.csv and oldnew_pairs.csv')


if __name__ == '__main__':
    main()
