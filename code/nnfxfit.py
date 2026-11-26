"""ITEM 2 -- DOES A STRATEGY'S FIT TO A PAIR CARRY? PROTOCOL.md AMENDMENT 1, A6.3.

Two statistics, computed from a sleeve bank -- real or scrambled -- so the
same code produces the real number and its null.

  RHO       per pair, the Spearman rank correlation between an algorithm's
            result on that pair in the early years and its result on the SAME
            pair in the later years, across every algorithm in the bank.
  SHARE     per pair, the fraction of sleeves ADMITTED on the early years
            (PROTOCOL.md A2) that are positive on the later years. A coin
            flip is 0.5 and the honest baseline is the unconditional share of
            sleeves positive in the later years, which is also reported --
            if admission does not raise it, admission selects nothing.

Both run in both rotations, and pooled over all (algorithm, pair) sleeves.

THIS IS THE GATE ON ITEM 3. If a strategy's fit to a pair does not persist,
every searched book is noise by construction and BOOKS.md says so.
"""
import os, sys
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
ROOT = os.path.dirname(_HERE)
ROOTOUT = os.path.join(ROOT, 'results')
sys.path.insert(0, ROOT)

import numpy as np
import pandas as pd
from scipy import stats as sstats
import nnfxsleeves as BK


def _rho(x, y):
    ok = np.isfinite(x) & np.isfinite(y)
    if ok.sum() < 30:
        return np.nan, np.nan
    r, p = sstats.spearmanr(x[ok], y[ok])
    return float(r), float(p)


def fit_stats(pairs, bank, share=BK.ADM_BEST_TRADE_SHARE, tag='real', run=0):
    """-> (per-pair DataFrame, pooled dict list). One bank in, both rotations."""
    rows, pooled = [], []
    for (rot, aw, sw) in (('R1', 'h1', 'h2'), ('R2', 'h2', 'h1')):
        Ra = bank['%s__R' % aw].astype(np.float64)
        Rs = bank['%s__R' % sw].astype(np.float64)
        adm = BK.admit_mask(bank['%s__R' % aw],
                            bank['%s__R_ex_best_day' % aw],
                            bank['%s__best_trade' % aw],
                            bank['%s__trades' % aw], share=share)
        # the unconditional baseline uses the same trade floor, so the
        # comparison is "did the rest of admission help", not "did any filter"
        base = bank['%s__trades' % aw] >= BK.ADM_MIN_TRADES
        for pi, p in enumerate(pairs):
            r, pv = _rho(Ra[:, pi], Rs[:, pi])
            a = adm[:, pi]
            b = base[:, pi]
            rows.append(dict(tag=tag, run=run, rotation=rot, pair=p,
                             n_algorithms=int(len(Ra)),
                             rho=r, rho_p=pv,
                             n_admitted=int(a.sum()),
                             share_pos_later=(float((Rs[a, pi] > 0).mean())
                                              if a.any() else np.nan),
                             n_baseline=int(b.sum()),
                             share_pos_later_baseline=(
                                 float((Rs[b, pi] > 0).mean())
                                 if b.any() else np.nan),
                             mean_R_later_admitted=(float(Rs[a, pi].mean())
                                                    if a.any() else np.nan),
                             mean_R_later_baseline=(float(Rs[b, pi].mean())
                                                    if b.any() else np.nan)))
        r, pv = _rho(Ra.ravel(), Rs.ravel())
        pooled.append(dict(tag=tag, run=run, rotation=rot,
                           n_sleeves=int(Ra.size), rho_pooled=r, rho_p=pv,
                           n_admitted=int(adm.sum()),
                           share_pos_later=(float((Rs[adm] > 0).mean())
                                            if adm.any() else np.nan),
                           n_baseline=int(base.sum()),
                           share_pos_later_baseline=(
                               float((Rs[base] > 0).mean())
                               if base.any() else np.nan),
                           mean_R_later_admitted=(float(Rs[adm].mean())
                                                  if adm.any() else np.nan),
                           rho_pair_median=float(np.nanmedian(
                               [x['rho'] for x in rows
                                if x['rotation'] == rot]))))
    return pd.DataFrame(rows), pooled
