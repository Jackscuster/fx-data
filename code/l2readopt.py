import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""ADOPTION RULE v2 — Sharpe dropped, applied to the whole bank.

    v1: account return higher AND max DD no worse AND Sortino no worse AND Sharpe no worse
    v2: account return higher AND max DD no worse AND Sortino no worse

Sharpe is still measured and still written to every output; it decides nothing.

WHY THIS IS A RE-EVALUATION AND NOT AN EDIT. The nine fine-tune shards already
running loaded the v1 rule at import, so they keep writing v1 `adopted` flags to
the bank until they exit. Rather than restart a 40-hour run to change one
comparison, the bank is re-evaluated here under v2 and the result written to its
own file. The bank's v1 flags stay exactly as they were and remain readable;
`rule` records which rule produced each adoption, so no verdict is silently
overwritten.

The candidate set cannot grow by dropping a condition from a conjunction: a
strategy adopted under v1 is adopted under v2, and a strategy whose candidate
did not beat the incumbent on account return is adopted under neither. So the
only rows that can change are the alternates.
"""
import glob
import numpy as np, pandas as pd

BANK = os.path.join(ROOTOUT, 'gate3ft_costed_v4')
OUT = os.path.join(ROOTOUT, 'gate3ft_adoptions_v2.csv')


def load(bank=BANK):
    fs = sorted(glob.glob(os.path.join(bank, '*.csv')))
    if not fs:
        return pd.DataFrame()
    return pd.concat([pd.read_csv(f, low_memory=False) for f in fs],
                     ignore_index=True).drop_duplicates('sid')


def evaluate(d):
    beat = d.ft_total_R > d.base_total_R
    dd_ok = d.ft_max_dd_R <= d.base_max_dd_R + 1e-12
    so_ok = d.ft_sortino >= d.base_sortino - 1e-12
    sh_ok = d.ft_sharpe >= d.base_sharpe - 1e-12
    d = d.copy()
    d['adopted_v1'] = (beat & dd_ok & so_ok & sh_ok).fillna(False)
    d['adopted_v2'] = (beat & dd_ok & so_ok).fillna(False)
    d['rule'] = np.where(d.adopted_v1, 'v1+v2',
                np.where(d.adopted_v2, 'v2 only (Sharpe dropped)', ''))
    d['beat_on_return'] = beat.fillna(False)
    # for true rejects under v2, which of the TWO binding conditions was missed
    d['failed_on'] = ['' if not b else
                      ','.join([n for n, f in (('DD', not a), ('Sortino', not c)) if f])
                      for b, a, c in zip(beat.fillna(False), dd_ok.fillna(False), so_ok.fillna(False))]
    d.loc[d.adopted_v2, 'failed_on'] = ''
    d['tag'] = np.where(d.failed_on == 'DD', 'DD_ONLY',
               np.where(d.failed_on == 'Sortino', 'SORTINO_ONLY',
               np.where(d.failed_on == 'DD,Sortino', 'BOTH', '')))
    return d


def main():
    d = load()
    if not len(d):
        print('no bank yet'); return
    d = evaluate(d)
    keep = ['sid', 'src_label', 'slice', 'c1', 'c2', 'vol', 'base',
            'base_stop', 'base_tp', 'ft_risk_atr_mult', 'ft_risk_tp_mult',
            'ft_risk_atr_len', 'ft_risk_trail_mult', 'ft_risk_trail_arm',
            'ft_risk_be_pct', 'ft_ip2',
            'base_total_R', 'ft_total_R', 'base_max_dd_R', 'ft_max_dd_R',
            'base_sortino', 'ft_sortino', 'base_sharpe', 'ft_sharpe',
            'base_win_rate', 'ft_win_rate', 'ft_n_blind',
            'adopted', 'adopted_v1', 'adopted_v2', 'rule', 'beat_on_return',
            'failed_on', 'tag']
    d[[c for c in keep if c in d.columns]].to_csv(OUT, index=False)
    print('re-evaluated %d strategies' % len(d))
    print('  beat on account return : %d' % d.beat_on_return.sum())
    print('  adopted under v1       : %d' % d.adopted_v1.sum())
    print('  adopted under v2       : %d' % d.adopted_v2.sum())
    print('  newly adopted by v2    : %d' % (d.adopted_v2 & ~d.adopted_v1).sum())
    print('  true rejects (v2)      : %s' % d[d.tag != ''].tag.value_counts().to_dict())
    # alternates now = beat on return but failed DD or Sortino
    A = d[(d.beat_on_return) & (~d.adopted_v2)].sort_values('ft_total_R', ascending=False)
    A[[c for c in keep if c in A.columns]].to_csv(
        os.path.join(ROOTOUT, 'gate3ft_alternates.csv'), index=False)
    print('  alternates rewritten   : %d rows' % len(A))
    return d


if __name__ == '__main__':
    main()
