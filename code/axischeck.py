import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""What the two axes actually measure, and whether the states separate on structure.

THREE QUESTIONS, ANSWERED FROM THE DATA RATHER THAN FROM THE LABELS.

1 EXCURSION. One definition, stated in the output, applied to both the nine states
  and the four tiers.

2 STRUCTURE. The validation separation numbers are dominated by properties that
  restate the classifier's own axes -- realised vol is the scale axis, range/path
  is the straightness axis. Separation is therefore also measured on statistics
  that are NOT inputs: the Lo-MacKinlay variance ratio, return autocorrelation and
  turn frequency. Those are the honest test of whether the states differ
  structurally rather than by construction.

3 THE SCALE AXIS. scale = sum|r| / (sd*sqrt(L)). For iid returns this equals
  E|r|/sigma * sqrt(L), i.e. sqrt(2/pi)*sqrt(L) under normality -- a constant. So
  it is a distribution-SHAPE statistic, not a measure of ground covered. The
  alternative that does measure ground covered is displacement = |net|/(sd*sqrt(L)),
  and since displacement = straightness * scale exactly, the question is whether
  adopting it collapses the grid to one axis.

Writes results/axis_check.csv.
"""
import numpy as np, pandas as pd
from ninestate import nine, grid_at, STATES, SPLIT, MULTI

PX = os.path.join(ROOTDATA, 'px28.csv')
L, V = 21, 60


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    fit = px.index < SPLIT
    lp = np.log(px.astype(float)); rr = lp.diff()
    net = (lp - lp.shift(L)).abs(); path = rr.abs().rolling(L).sum()
    unit = rr.rolling(V).std() * np.sqrt(L)
    inf = [np.inf, -np.inf]
    scale = (path / unit).replace(inf, np.nan)
    straight = (net / path).replace(inf, np.nan)
    disp = (net / unit).replace(inf, np.nan)

    rows = []
    theory = np.sqrt(2 / np.pi) * np.sqrt(L)
    for nm, x in (('scale = path/(sd*sqrt L)', scale),
                  ('displacement = |net|/(sd*sqrt L)', disp),
                  ('straightness = |net|/path', straight)):
        s = x.stack()
        rows.append(dict(measure=nm, mean=s.mean(), sd=s.std(),
                         cv=s.std() / s.mean(), p10=s.quantile(.1),
                         p90=s.quantile(.9)))
    A = pd.DataFrame(rows)
    print('WHAT THE AXES MEASURE  (iid-Gaussian prediction for scale: %.3f)' % theory)
    print(A.to_string(index=False, float_format=lambda v: '%.3f' % v))
    j = pd.concat([straight.stack().rename('straight'), scale.stack().rename('scale'),
                   disp.stack().rename('disp')], axis=1).dropna()
    C = j.corr(method='spearman')
    print('\nspearman correlations\n%s' % C.round(3).to_string())
    print('\ndisp = straight * scale exactly. straight carries the variance:')
    print('  disp vs straight %.3f -- adopting displacement as the size axis would'
          ' collapse the grid toward one dimension' % C.loc['disp', 'straight'])

    lab, _ = nine(px, fit)
    vr = lambda k: (((lp - lp.shift(k)).rolling(L).var()
                     / (k * rr.rolling(L).var())).replace(inf, np.nan).shift(1))
    props = {'variance ratio k=10 [structural]': vr(10),
             'return autocorr     [structural]': rr.rolling(L).corr(rr.shift(1)).shift(1),
             'turn frequency      [structural]':
                 (np.sign(rr) != np.sign(rr.shift(1))).rolling(L).mean().shift(1),
             'realised vol        [restates scale]': rr.rolling(L).std().shift(1),
             'range/path          [restates straightness]':
                 ((lp.rolling(L).max() - lp.rolling(L).min())
                  / rr.abs().rolling(L).sum()).shift(1)}
    out = []
    print('\nSEPARATION ACROSS THE NINE STATES, in sd units of each property')
    for nm, P in props.items():
        d = pd.DataFrame({'s': lab.stack(), 'v': P.stack()}).dropna()
        g = d.groupby('s').v.mean().reindex(STATES)
        tr = g[[x for x in STATES if x.endswith('trend')]].mean()
        ch = g[[x for x in STATES if x.endswith('chop')]].mean()
        out.append(dict(prop=nm, gap_sd=(g.max() - g.min()) / d.v.std(),
                        trend=tr, chop=ch, chop_minus_trend_sd=(ch - tr) / d.v.std()))
        print('  %-44s gap %.3f   trend->chop %+.3f sd'
              % (nm, out[-1]['gap_sd'], out[-1]['chop_minus_trend_sd']))
    pd.concat([A, pd.DataFrame(out)], axis=1).to_csv(
        os.path.join(ROOTOUT, 'axis_check.csv'), index=False)
    print('\nwrote axis_check.csv')


if __name__ == '__main__':
    main()
