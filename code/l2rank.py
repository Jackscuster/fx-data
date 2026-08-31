import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""THE LEADERBOARD — the co-equal ranking, applied to a crisis split.

Mode B's leaderboard was built by hand in a session and never committed, so
mode A could only have been ranked by re-deriving the rules from memory. This
is that step made reproducible. It REBUILDS MODE B BYTE-FOR-BYTE from the same
inputs (--verify) before it is trusted with A; if the rebuild does not match,
the script refuses rather than ranking A by a rule that has silently drifted.

THE RULE, from GAUNTLET.md, unchanged:
  rank on total blind R, rank on Sortino, AVERAGE the two ranks, Calmar breaks
  ties. Production and risk-aversion are co-equal -- neither is the tiebreak
  for the other.

Ranking is on the CRISIS-EXCLUDED columns (ex_*). Crisis P&L is carried beside
it and never enters the ranking.

A NaN Sortino ranks LAST, never first. It arises when every losing trade is an
identical full-stop loss, so downside deviation is zero; treated as a large
number it would rank a perfect loser first. This bit once.

    net_of_structure_R = ex_expectancy_R - (that slice's null MEAN expectancy)

The null MEAN, not the p95 floor -- the floor asks "did this beat luck", the
mean asks how much of the expectancy is signal rather than what the money
management earns on any entries at all.
"""
import numpy as np, pandas as pd

RANK_ON_R = 'ex_total_R'
RANK_ON_S = 'ex_sortino'
TIEBREAK = 'ex_calmar'


def null_mean(mode):
    """Slice -> mean surrogate expectancy, from the gate 1 fresh nulls."""
    f = os.path.join(ROOTOUT, 'gate1_null_raw_mode%s.csv' % mode)
    N = pd.read_csv(f, low_memory=False)
    return N.groupby('slice').expectancy_R.mean()


def rank(D, mode):
    D = D.copy()
    # ascending=False so the biggest R is rank 1. NaN Sortino goes last by
    # na_option, not by being silently dropped.
    # method='min': tied values share the BETTER rank rather than being split
    # onto a half-rank. Verified as the method mode B's leaderboard used.
    D['rank_R'] = D[RANK_ON_R].rank(ascending=False, method='min', na_option='bottom')
    D['rank_S'] = D[RANK_ON_S].rank(ascending=False, method='min', na_option='bottom')
    D['score'] = (D.rank_R + D.rank_S) / 2.0
    D = D.sort_values(['score', TIEBREAK], ascending=[True, False],
                      kind='mergesort').reset_index(drop=True)
    D['rank'] = np.arange(1, len(D) + 1)
    nm = null_mean(mode)
    D['net_of_structure_R'] = D.ex_expectancy_R - D.slice.map(nm)
    return D


def attach_tuning(D, tuned):
    """ip2 and the tuned exit indicator, carried from the tuner's own output."""
    T = pd.read_csv(tuned, low_memory=False)
    keys = ['c1', 'c2', 'vol', 'base', 'exit_ind', 'slice']
    cols = [c for c in ('ip2', 'exit_ind_t') if c in T.columns]
    if not cols:
        return D
    return D.merge(T[keys + cols].drop_duplicates(keys), on=keys, how='left')


def build(split, tuned, mode, out):
    D = pd.read_csv(split, low_memory=False)
    D = attach_tuning(D, tuned)
    D = rank(D, mode)
    D.to_csv(out, index=False)
    print('wrote %s (%d rows)' % (os.path.basename(out), len(D)), flush=True)
    return D


def verify_B():
    """Rebuild mode B's committed leaderboard and compare, column by column."""
    ref = pd.read_csv(os.path.join(ROOTOUT, 'gate2_modeB_leaderboard.csv'),
                      low_memory=False)
    D = pd.read_csv(os.path.join(ROOTOUT, 'gate2_crisis_split_modeB_all.csv'),
                    low_memory=False)
    D = attach_tuning(D, os.path.join(ROOTOUT, 'gate2_tuned_modeB.csv'))
    D = rank(D, 'B')
    ok = True
    for c in ('rank', 'rank_R', 'rank_S', 'score', 'net_of_structure_R'):
        if c not in ref.columns:
            continue
        a, b = D[c].values, ref[c].values
        same = (np.allclose(a, b, atol=1e-9, equal_nan=True)
                if np.issubdtype(D[c].dtype, np.number) else (a == b).all())
        print('  %-20s %s' % (c, 'MATCH' if same else 'DIFFERS'))
        ok = ok and same
    for c in ('c1', 'c2', 'vol', 'base'):
        same = (D[c].values == ref[c].values).all()
        print('  %-20s %s' % (c + ' (order)', 'MATCH' if same else 'DIFFERS'))
        ok = ok and same
    return ok


TOPN_CLEAN = 60


def clean_view(lb, out, jobs=1, topn=TOPN_CLEAN):
    """THE CLEAN VIEW. Take the top N of the leaderboard, flag every blind trade
    for peg / low-vol / crisis, and re-rank on what is left.

    clean_R excludes ALL THREE -- a pegged trade, a trade entered below the
    pair's own 5th-percentile ATR, and a crisis-window trade. It is the harshest
    honest view of a configuration: what it earned with none of the three
    conditions that make R arithmetically correct but not obviously repeatable.

    The re-rank is the SAME co-equal rule, with clean_R standing in for total R.
    Sortino is NOT recomputed on the clean subset -- ex_sortino is carried over,
    exactly as mode B's clean view did."""
    import l2suppvol as SV
    L = pd.read_csv(lb, low_memory=False).sort_values('rank').head(topn)
    F = SV.run(L.to_dict('records'), jobs=jobs)
    F = F.merge(L[['c1', 'c2', 'vol', 'base', 'slice', 'ex_sortino',
                   'ex_total_R', 'ex_calmar', 'rank']],
                on=['c1', 'c2', 'vol', 'base', 'slice'], how='left')
    F['clean_R'] = F.cln_R
    F['clean_n'] = F.cln_n
    F['rk_R'] = F.clean_R.rank(ascending=False, method='min', na_option='bottom')
    F['rk_S'] = F.ex_sortino.rank(ascending=False, method='min', na_option='bottom')
    F['score'] = (F.rk_R + F.rk_S) / 2.0
    # Calmar breaks ties, the SAME tiebreak the main ranking uses. Mode B's
    # clean view had no tiebreak at all: it kept whatever order the parallel
    # suppvol pool happened to return, so rows tied on score were ordered by
    # worker completion -- randomly. Every metric and both component ranks
    # reproduce exactly; only the order WITHIN a score tie differed, by at most
    # two positions. Mode B's committed file is left as it is; this is the rule
    # from here.
    F = F.sort_values(['score', TIEBREAK], ascending=[True, False],
                      kind='mergesort').reset_index(drop=True)
    F['new_rank'] = np.arange(1, len(F) + 1)
    F.to_csv(out, index=False)
    print('wrote %s (%d rows)' % (os.path.basename(out), len(F)), flush=True)
    return F


def main():
    a = sys.argv[1:]
    if '--verify' in a:
        print('rebuilding mode B from its own inputs:')
        raise SystemExit(0 if verify_B() else 'mode B rebuild DIFFERS -- not ranking anything else')
    mode = a[a.index('--mode') + 1] if '--mode' in a else 'A'
    sl = a[a.index('--slice') + 1] if '--slice' in a else None
    tag = 'mode%s%s' % (mode, '_' + sl if sl else '')
    print('verifying the rule against mode B first:')
    if not verify_B():
        raise SystemExit('mode B rebuild DIFFERS -- refusing to rank %s' % tag)
    split = os.path.join(ROOTOUT, 'gate2_crisis_split_%s_all.csv' % tag)
    tuned = os.path.join(ROOTOUT, 'gate2_tuned_%s.csv' % tag)
    if not os.path.exists(tuned):
        tuned = os.path.join(ROOTOUT, 'gate2_tuned_mode%s.csv' % mode)
    lb = os.path.join(ROOTOUT, 'gate2_%s_leaderboard.csv' % tag)
    build(split, tuned, mode, lb)
    if '--clean' in a:
        clean_view(lb, os.path.join(ROOTOUT,
                   'gate2_%s_leaderboard_clean.csv' % tag),
                   jobs=int(a[a.index('--jobs') + 1]) if '--jobs' in a else 1)


if __name__ == '__main__':
    main()
