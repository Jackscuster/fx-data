import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""REJECTED CANDIDATES ARE KEPT, NOT DISCARDED.

The adoption rule requires a candidate to beat the incumbent on account return
AND be no worse on max drawdown, Sortino and Sharpe. A candidate that earns more
and fails only on Sharpe is not nothing -- it is the same trade-off gate 3's
SHARPE_ONLY group exists to make visible -- so it is written here rather than
thrown away.

WHAT IS RECOVERABLE, STATED PLAINLY. The fine-tune bank stores ONE candidate per
strategy: the final output of the coordinate descent, in the ft_* columns. The
many intermediate candidates the descent evaluates are not logged anywhere. So
this file captures the case where THE FINAL candidate beat the incumbent on
account return and was rejected. If an intermediate candidate did better on
account return and was then superseded -- possible, because the descent's own
objective is expectancy while the adoption rule is total account return -- that
candidate is gone and cannot be reconstructed. Logging it would mean restarting
the run, which is not being done.

failed_on lists exactly which of DD / Sortino / Sharpe the candidate missed.
    SHARPE_ONLY   Sharpe was the only miss
    DD_ONLY       drawdown was the only miss
    MULTI         more than one
"""
import glob
import numpy as np, pandas as pd

BANK = os.path.join(ROOTOUT, 'gate3ft_costed_v4')
OUT = os.path.join(ROOTOUT, 'gate3ft_alternates.csv')


def build(bank=BANK, out=OUT):
    fs = sorted(glob.glob(os.path.join(bank, '*.csv')))
    if not fs:
        print('no bank yet'); return pd.DataFrame()
    d = pd.concat([pd.read_csv(f, low_memory=False) for f in fs],
                  ignore_index=True).drop_duplicates('sid')
    # the candidate must BEAT the incumbent on account return; adopted rows are
    # not alternates, they are the official settings
    m = (d.ft_total_R > d.base_total_R) & (~d.adopted.fillna(False))
    A = d[m].copy()
    if not len(A):
        pd.DataFrame(columns=['sid']).to_csv(out, index=False)
        print('0 alternates of %d finished' % len(d)); return A
    worse_dd = A.ft_max_dd_R > A.base_max_dd_R + 1e-12
    worse_so = A.ft_sortino < A.base_sortino - 1e-12
    worse_sh = A.ft_sharpe < A.base_sharpe - 1e-12
    A['failed_on'] = [','.join([n for n, f in (('DD', a), ('Sortino', b), ('Sharpe', c)) if f])
                      for a, b, c in zip(worse_dd, worse_so, worse_sh)]
    n_fail = worse_dd.astype(int) + worse_so.astype(int) + worse_sh.astype(int)
    A['tag'] = np.where((n_fail == 1) & worse_sh, 'SHARPE_ONLY',
               np.where((n_fail == 1) & worse_dd, 'DD_ONLY',
               np.where(n_fail == 1, 'SORTINO_ONLY', 'MULTI')))
    A['incumbent_stop'] = A.base_stop
    A['incumbent_tp'] = A.base_tp
    A['candidate_stop'] = A.ft_risk_atr_mult
    A['candidate_tp'] = A.ft_risk_tp_mult
    A['candidate_tp_none'] = A.ft_risk_tp_mult >= 900
    cols = ['sid', 'src_label', 'slice', 'c1', 'c2', 'vol', 'base',
            'incumbent_stop', 'incumbent_tp', 'candidate_stop', 'candidate_tp',
            'candidate_tp_none', 'ft_risk_atr_len', 'ft_risk_trail_mult',
            'ft_risk_trail_arm', 'ft_risk_be_pct', 'ft_ip2',
            'base_total_R', 'ft_total_R', 'base_max_dd_R', 'ft_max_dd_R',
            'base_sortino', 'ft_sortino', 'base_sharpe', 'ft_sharpe',
            'base_win_rate', 'ft_win_rate', 'ft_n_blind', 'failed_on', 'tag']
    A = A[[c for c in cols if c in A.columns]].sort_values('ft_total_R', ascending=False)
    A.to_csv(out, index=False)
    print('%d alternates of %d finished strategies' % (len(A), len(d)))
    print(A.tag.value_counts().to_dict())
    return A


if __name__ == '__main__':
    build()
