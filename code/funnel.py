import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTDATA,exist_ok=True); os.makedirs(ROOTOUT,exist_ok=True)
sys.path.insert(0,ROOTLIB)
"""DSR attrition funnel.

Three stages, each a strict subset of the one above:

  1 variants tested            every (pair, config, detector, logic) cell scored OOS
  2 positive OOS Sharpe delta  beat their own unfiltered baseline
  3 survive DSR >= 0.95        deflated Sharpe, Bailey & Lopez de Prado

Stage 2 is what a naive read of the sweep would report. Stage 3 is what survives
once the number of attempts is accounted for. The gap between them is the whole
point of the table — at this many attempts the expected maximum Sharpe under the
null is high enough to swallow almost anything observed.

Reads results/logic_results.csv (written by framework.py). Writes results/dsr_funnel.csv.
"""
import numpy as np, pandas as pd
import framework as F

SRC = os.path.join(ROOTOUT,'/logic_results.csv'.lstrip('/'))


def main():
    if not os.path.exists(SRC):
        raise SystemExit('missing %s — run framework.py first' % SRC)
    R = pd.read_csv(SRC)
    V, emax, N = F.dsr(R)

    n_total = int(N)
    n_pos = int((V.delta > 0).sum())
    n_dsr = int(V.dsr_pass.sum())

    # emax carried on every row so bundle.py can read it without a second file
    T = pd.DataFrame([
        dict(stage='variants tested', count=n_total, pct_of_total=1.0, emax=emax),
        dict(stage='positive OOS Sharpe delta', count=n_pos,
             pct_of_total=n_pos / n_total if n_total else np.nan, emax=emax),
        dict(stage='survive DSR >= 0.95', count=n_dsr,
             pct_of_total=n_dsr / n_total if n_total else np.nan, emax=emax)])
    T.to_csv(os.path.join(ROOTOUT,'/dsr_funnel.csv'.lstrip('/')), index=False)

    print('=' * 78); print('DSR ATTRITION FUNNEL'); print('=' * 78)
    print(T.to_string(index=False, float_format=lambda x: '%.4f' % x))
    print('\nexpected max Sharpe under the null at %d attempts: %.3f' % (n_total, emax))
    best = V.oos_sharpe.max()
    print('best observed OOS Sharpe: %.3f' % best)
    print('%d of %d survive. Clearing the null expectation on a point basis is not '
          'enough — DSR also weighs the sample length behind each Sharpe.'
          % (n_dsr, n_total))


if __name__ == '__main__':
    main()
