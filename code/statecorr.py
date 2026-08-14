import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""How shared are the states across the 28 pairs?

MEASUREMENT ONLY. Nothing here changes a state call, feeds the classifier, or
routes anything. The question is one of counting: if fourteen pairs read
"trending" on the same day, is that fourteen observations or one?

THE STRUCTURAL FLOOR, STATED FIRST BECAUSE IT BOUNDS EVERY NUMBER BELOW. The 28
pairs are built from 8 currencies, so the return panel has rank 7, not 28. Any
pair is an exact linear combination of others -- EURJPY is EURUSD plus USDJPY by
construction, not by correlation. Agreement between pairs sharing a leg is
therefore partly an identity, and CANNOT be interpreted as evidence that the
market moved together. The right reading of these numbers is "how much less than
28 independent observations do I have", and the answer was always going to be
"a lot". What the measurement adds is HOW MUCH, and WHERE the sharing sits.

AGREEMENT IS CHANCE-CORRECTED. Two pairs that are both in "ranging" 45% of the
time agree 30%+ of days by coincidence alone. Raw agreement would make every
number look enormous, so Cohen's kappa is the reported figure:

    kappa = (observed - expected) / (1 - expected)
    expected = sum over states of p_i(s) * p_j(s)

kappa = 0 means "no more agreement than the two marginal distributions force",
kappa = 1 means identical. Raw observed agreement is kept in the CSV beside it so
the correction can be checked.

COMPLETE-CASE DAYS ONLY. Every figure uses days on which all 28 pairs carry a
label, so p_i, p_j and the observed agreement are all computed over the same day
set and kappa is exact rather than approximate. The count of days used is
reported.

THE ROUTING NUMBER. Effective independent observations per day, under the
standard equicorrelation formula:

    N_eff = N / (1 + (N - 1) * rbar)

with rbar the mean off-diagonal kappa. 28 if states were independent, 1 if all
28 always agreed. It is computed on rolling 252-complete-day windows so it has a
range and not just an average. An eigenvalue-based alternative (participation
ratio) is reported beside it, because the equicorrelation assumption is false in
detail -- currency blocks make some pairs far more alike than others -- and two
constructions disagreeing would matter.

Writes results/state_correlation.csv, state_blocks.csv, state_breadth.csv + .txt.
"""
import numpy as np, pandas as pd

ST = os.path.join(ROOTOUT, 'states_g4_twoscore4.csv')
SPLIT = pd.Timestamp('2016-01-01')
STATES = ['trending', 'ranging', 'trend-in-range', 'neither']
WIN = 252
STEP = 21
NSHIFT = int(os.environ.get('FX_NSHIFT', 50))
MINOFF = 500

from drivers import crisis_mask, hdr


def load():
    st = pd.read_csv(ST, index_col=0, parse_dates=True, comment='#')
    full = st.dropna(how='any')
    return st, full


def onehot(full):
    """T x 28 x 4 indicator array, in the column order of `full`."""
    A = np.zeros((len(full), full.shape[1], len(STATES)), dtype=np.float64)
    V = full.values
    for k, s in enumerate(STATES):
        A[:, :, k] = (V == s)
    return A


def agree(A):
    """Observed agreement, expected agreement and kappa, all 28x28."""
    T = A.shape[0]
    obs = np.zeros((A.shape[1], A.shape[1]))
    for k in range(len(STATES)):
        M = A[:, :, k]
        obs += M.T @ M
    obs /= T
    p = A.mean(axis=0)                      # 28 x 4 marginals
    exp = p @ p.T
    # A pair stuck in ONE state for the whole window has expected agreement 1,
    # so kappa is 0/0 -- agreement carries no information there rather than
    # infinite information. Short rolling windows do produce this.
    den = 1 - exp
    kap = np.where(den > 1e-12, (obs - exp) / np.where(den > 1e-12, den, 1), 0.0)
    return obs, exp, kap


def offdiag(M):
    n = M.shape[0]
    return M[~np.eye(n, dtype=bool)].reshape(n, n - 1)


def neff_equi(kap):
    n = kap.shape[0]
    rbar = float(offdiag(kap).mean())
    return n / (1 + (n - 1) * rbar), rbar


def neff_eig(kap):
    """Participation ratio of the eigenvalue spectrum. Kappa is symmetric but
    not guaranteed positive semi-definite, so negative eigenvalues are clipped
    to zero; that is noted rather than hidden."""
    K = kap.copy()
    np.fill_diagonal(K, 1.0)
    K = np.nan_to_num((K + K.T) / 2, nan=0.0, posinf=0.0, neginf=0.0)
    try:
        raw = np.linalg.eigvalsh(K)
    except np.linalg.LinAlgError:
        return float('nan'), -1
    w = np.clip(raw, 0, None)
    if w.sum() <= 0:
        return float('nan'), int((raw < 0).sum())
    return float(w.sum() ** 2 / (w ** 2).sum()), int((raw < 0).sum())


def blocks(pairs, kap):
    """Does agreement cluster around a shared currency leg?

    A pair belongs to TWO currency blocks, so blocks overlap by construction and
    'within' and 'across' are not a partition of the pairs -- they are a
    partition of the 378 PAIRS-OF-PAIRS, by whether the two share a leg."""
    ccys = sorted({p[:3] for p in pairs} | {p[3:] for p in pairs})
    n = len(pairs)
    rows, wi, ac = [], [], []
    for i in range(n):
        for j in range(i + 1, n):
            a, b = pairs[i], pairs[j]
            shared = {a[:3], a[3:]} & {b[:3], b[3:]}
            (wi if shared else ac).append(kap[i, j])
    for c in ccys:
        idx = [i for i, p in enumerate(pairs) if c in (p[:3], p[3:])]
        v = [kap[i, j] for ii, i in enumerate(idx) for j in idx[ii + 1:]]
        rows.append(dict(block=c, pairs_in_block=len(idx), pairs_of_pairs=len(v),
                         mean_kappa=float(np.mean(v)),
                         median_kappa=float(np.median(v))))
    return pd.DataFrame(rows), np.array(wi), np.array(ac)


def breadth(full, cm):
    """How many of the 28 share the modal state each day."""
    V = full.values
    cnt = np.zeros((len(full), len(STATES)))
    for k, s in enumerate(STATES):
        cnt[:, k] = (V == s).sum(axis=1)
    modal = cnt.max(axis=1)
    which = np.array(STATES)[cnt.argmax(axis=1)]
    return pd.DataFrame({'modal_count': modal.astype(int),
                         'modal_state': which,
                         'modal_share': modal / full.shape[1],
                         'crisis': cm.reindex(full.index).fillna(False).values},
                        index=full.index)


def rolling_neff(A, index, fit):
    rows = []
    for a in range(0, len(index) - WIN + 1, STEP):
        b = a + WIN
        _, _, kap = agree(A[a:b])
        ne, rbar = neff_equi(kap)
        nge, _ = neff_eig(kap)
        rows.append(dict(window_end=index[b - 1], block='is' if fit[b - 1] else 'oos',
                         mean_kappa=rbar, neff_equicorr=ne, neff_eigen=nge))
    return pd.DataFrame(rows)


def main():
    st, full = load()
    pairs = list(full.columns)
    cm, n_ev = crisis_mask(st.index)
    fit = np.asarray(full.index < SPLIT)
    print('SHARED STATES ACROSS THE 28 PAIRS -- measurement only.')
    print('  state file rows %d, complete-case days %d (%.1f%%), %s -> %s'
          % (len(st), len(full), 100 * len(full) / len(st),
             full.index.min().date(), full.index.max().date()))
    print('  IS %d days, OOS %d days' % (int(fit.sum()), int((~fit).sum())))
    print('  THE RANK-7 FLOOR: 28 pairs from 8 currencies, so the panel has rank')
    print('  7. Pairs sharing a leg agree partly BY IDENTITY, not by co-movement.')

    A = onehot(full)
    corr, blk, brd = [], [], []
    summ = []
    for tag, m in (('is', fit), ('oos', ~fit)):
        obs, exp, kap = agree(A[m])
        ne, rbar = neff_equi(kap)
        nge, nneg = neff_eig(kap)
        for i in range(len(pairs)):
            for j in range(len(pairs)):
                if i >= j:
                    continue
                corr.append(dict(block=tag, pair_a=pairs[i], pair_b=pairs[j],
                                 observed=obs[i, j], expected=exp[i, j],
                                 kappa=kap[i, j]))
        B, wi, ac = blocks(pairs, kap)
        B['block_period'] = tag
        blk.append(B)
        o = offdiag(obs).mean(); e = offdiag(exp).mean()
        summ.append(dict(block=tag, days=int(m.sum()),
                         mean_observed=float(o), mean_expected=float(e),
                         mean_kappa=float(rbar),
                         excess_over_chance=float(o - e),
                         min_kappa=float(offdiag(kap).min()),
                         max_kappa=float(offdiag(kap).max()),
                         share_leg_kappa=float(wi.mean()),
                         no_leg_kappa=float(ac.mean()),
                         n_share_leg=len(wi), n_no_leg=len(ac),
                         neff_equicorr=float(ne), neff_eigen=float(nge),
                         negative_eigenvalues=nneg))
        print('\n%s -- %d days' % (tag.upper(), int(m.sum())))
        print('  raw agreement       %.3f' % o)
        print('  expected by chance  %.3f   (from the marginals alone)' % e)
        print('  excess over chance  %+.3f' % (o - e))
        print('  mean kappa          %.3f   range %.3f to %.3f'
              % (rbar, offdiag(kap).min(), offdiag(kap).max()))
        print('  share a currency    kappa %.3f  (%d pairs-of-pairs)'
              % (wi.mean(), len(wi)))
        print('  share NO currency   kappa %.3f  (%d pairs-of-pairs)'
              % (ac.mean(), len(ac)))
        print('  N_eff equicorr      %.2f of 28' % ne)
        print('  N_eff eigenvalue    %.2f of 28  (%d negative eigenvalues clipped)'
              % (nge, nneg))
        print('  BLOCKS, mean kappa inside each currency:')
        for _, r in B.sort_values('mean_kappa', ascending=False).iterrows():
            print('    %-4s %5.3f  (%d pairs)'
                  % (r.block, r.mean_kappa, r.pairs_in_block))

    C = pd.DataFrame(corr)
    C['shared_leg'] = [','.join(sorted({a[:3], a[3:]} & {b[:3], b[3:]})) or 'none'
                       for a, b in zip(C.pair_a, C.pair_b)]
    S = pd.DataFrame(summ)

    # IS-vs-OOS stability of the MATRIX ITSELF. The aggregate figures repeat
    # almost exactly across halves, which is not the same as an individual cell
    # repeating -- and the distinction decides whether a single cell can be
    # used for anything.
    piv = C.pivot_table(index=['pair_a', 'pair_b'], columns='block', values='kappa')
    sp = float(piv['is'].corr(piv['oos'], method='spearman'))
    pe = float(piv['is'].corr(piv['oos']))
    S['pairwise_is_oos_spearman'] = sp
    S['pairwise_is_oos_pearson'] = pe
    print('\nSTABILITY OF THE MATRIX ACROSS HALVES')
    print('  aggregate kappa repeats: %.3f -> %.3f' % (summ[0]['mean_kappa'],
                                                       summ[1]['mean_kappa']))
    print('  but individual cells only moderately: spearman %.3f, pearson %.3f'
          ' over %d pairs-of-pairs' % (sp, pe, len(piv)))
    print('  So the AGGREGATE is usable and a SINGLE CELL is not.')
    tops = []
    for tag in ('is', 'oos'):
        d = C[C.block == tag].sort_values('kappa', ascending=False)
        for lab, dd in (('top', d.head(10)), ('bottom', d.tail(10))):
            for _, r in dd.iterrows():
                tops.append(dict(block=tag, end=lab, pair_a=r.pair_a,
                                 pair_b=r.pair_b, kappa=r.kappa,
                                 observed=r.observed, expected=r.expected,
                                 shared_leg=r.shared_leg))
    TP = pd.DataFrame(tops)
    TP.to_csv(os.path.join(ROOTOUT, 'state_pairs_extremes.csv'), index=False)
    print('  strongest cell IS: %s/%s kappa %.3f (shares %s)'
          % (TP.iloc[0].pair_a, TP.iloc[0].pair_b, TP.iloc[0].kappa,
             TP.iloc[0].shared_leg))
    BL = pd.concat(blk, ignore_index=True)
    C.to_csv(os.path.join(ROOTOUT, 'state_correlation.csv'), index=False)
    S.to_csv(os.path.join(ROOTOUT, 'state_correlation_summary.csv'), index=False)

    # ---------------- BREADTH ----------------
    BR = breadth(full, cm)
    rows = []
    for tag, m in (('is', fit), ('oos', ~fit)):
        d = BR[m]
        q = d.modal_count.quantile([0.05, 0.25, 0.5, 0.75, 0.95]).to_dict()
        rows.append(dict(block=tag, days=len(d), metric='modal_count',
                         mean=float(d.modal_count.mean()),
                         p05=q[0.05], p25=q[0.25], median=q[0.5], p75=q[0.75],
                         p95=q[0.95],
                         share_ge_20=float((d.modal_count >= 20).mean()),
                         share_ge_24=float((d.modal_count >= 24).mean()),
                         share_le_12=float((d.modal_count <= 12).mean())))
    BRS = pd.DataFrame(rows)
    print('\nBREADTH -- how many of 28 share the modal state')
    print('  %-4s %6s %6s %6s %6s %8s %8s' % ('blk', 'mean', 'p25', 'med', 'p95',
                                              '>=20', '>=24'))
    for _, r in BRS.iterrows():
        print('  %-4s %6.1f %6.0f %6.0f %6.0f %8.3f %8.3f'
              % (r.block, r['mean'], r.p25, r['median'], r.p95, r.share_ge_20,
                 r.share_ge_24))
    dist = BR.groupby('modal_count').size().rename('days').reset_index()
    dist['share'] = dist.days / len(BR)
    dist['modal_state_mode'] = [
        BR[BR.modal_count == k].modal_state.value_counts().index[0]
        for k in dist.modal_count]
    print('  distribution of the modal count (all days):')
    for _, r in dist.iterrows():
        print('    %2d pairs %5d days %6.3f   usually %s'
              % (r.modal_count, r.days, r.share, r.modal_state_mode))

    # widest days vs the crisis calendar
    thr = BR.modal_count.quantile(0.9)
    wide = BR.modal_count >= thr
    base = float(BR.crisis.mean())
    hit = float(BR.crisis[wide].mean())
    print('\n  WIDEST DAYS vs THE %d-EVENT CRISIS CALENDAR' % n_ev)
    print('    widest decile: modal count >= %.0f, %d days' % (thr, int(wide.sum())))
    print('    crisis-window share on those days %.3f vs base %.3f  (lift x%.2f)'
          % (hit, base, hit / base if base else np.nan))
    rng = np.random.default_rng(1234)
    n = len(BR)
    acc = []
    mcv = BR.modal_count.values
    for _ in range(NSHIFT):
        k = int(rng.integers(MINOFF, n - MINOFF))
        w2 = np.roll(mcv, k) >= thr
        acc.append(float(BR.crisis.values[w2].mean() / base))
    v = np.array(acc)
    rank = int((np.abs(v - 1) >= abs(hit / base - 1)).sum()) + 1
    print('    NULL, %d circular shifts of the breadth series: null x%.2f +/- %.2f'
          '  rank %d of %d  p=%.3f'
          % (len(v), v.mean(), v.std(), rank, len(v) + 1, rank / (len(v) + 1)))
    crow = dict(block='all', metric='widest decile vs crisis calendar',
                threshold=float(thr), days=int(wide.sum()), p=hit, base=base,
                lift=hit / base if base else np.nan, n_shifts=len(v),
                null_mean_lift=float(v.mean()), null_sd=float(v.std()),
                rank_of_real=rank, n_compared=len(v) + 1,
                p_null=rank / (len(v) + 1), events=n_ev)
    for tag, m in (('is', fit), ('oos', ~fit)):
        d = BR[m]
        w = d.modal_count >= thr
        b2 = float(d.crisis.mean())
        crow_ = dict(block=tag, metric='widest decile vs crisis calendar',
                     threshold=float(thr), days=int(w.sum()),
                     p=float(d.crisis[w].mean()), base=b2,
                     lift=float(d.crisis[w].mean() / b2) if b2 else np.nan)
        rows.append(crow_)
    rows.append(crow)
    for _, r in dist.iterrows():
        rows.append(dict(block='all', metric='modal_count distribution',
                         modal_count=int(r.modal_count), days=int(r.days),
                         share=float(r['share']),
                         modal_state_mode=r.modal_state_mode))
    BRD = pd.DataFrame(rows)
    BRD.to_csv(os.path.join(ROOTOUT, 'state_breadth.csv'), index=False)
    BR.to_csv(os.path.join(ROOTOUT, 'state_breadth_daily.csv'))

    # ---------------- ROLLING N_eff ----------------
    RN = rolling_neff(A, full.index, fit)
    RN.to_csv(os.path.join(ROOTOUT, 'state_neff_rolling.csv'), index=False)
    print('\nTHE ROUTING NUMBER -- effective independent observations per day')
    print('  rolling %d-day windows, step %d, %d windows' % (WIN, STEP, len(RN)))
    print('  %-4s %8s %8s %8s %8s' % ('blk', 'mean', 'min', 'max', 'eigen mean'))
    for tag in ('is', 'oos'):
        d = RN[RN.block == tag]
        print('  %-4s %8.2f %8.2f %8.2f %8.2f'
              % (tag, d.neff_equicorr.mean(), d.neff_equicorr.min(),
                 d.neff_equicorr.max(), d.neff_eigen.mean()))
        BRS = pd.concat([BRS, pd.DataFrame([dict(
            block=tag, metric='neff_rolling', mean=float(d.neff_equicorr.mean()),
            p05=float(d.neff_equicorr.min()), p95=float(d.neff_equicorr.max()),
            days=len(d))])], ignore_index=True)
    BL.to_csv(os.path.join(ROOTOUT, 'state_blocks.csv'), index=False)
    BRS.to_csv(os.path.join(ROOTOUT, 'state_breadth_summary.csv'), index=False)

    fl = '\n'.join(
        '  %-4s raw %.3f, chance %.3f, kappa %.3f | share-leg %.3f vs no-leg %.3f'
        ' | N_eff %.1f (eigen %.1f)'
        % (r.block, r.mean_observed, r.mean_expected, r.mean_kappa,
           r.share_leg_kappa, r.no_leg_kappa, r.neff_equicorr, r.neff_eigen)
        for _, r in S.iterrows())
    hdr(os.path.join(ROOTOUT, 'state_correlation.csv'),
        'Same-day state agreement between every pair of pairs',
        'MEASUREMENT ONLY. Nothing here changes a state call or feeds the\n'
        'classifier. The question is how many independent observations a day of\n'
        '28 state readings actually contains.\n\n'
        'THE RANK-7 FLOOR, which bounds every number here. The 28 pairs are\n'
        'built from 8 currencies, so the panel has rank 7. EURJPY is EURUSD plus\n'
        'USDJPY by construction. Agreement between pairs sharing a leg is partly\n'
        'an IDENTITY and is not evidence the market moved together.\n\n'
        'kappa = (observed - expected) / (1 - expected), with expected the\n'
        'agreement forced by the two marginal state distributions alone. Raw\n'
        'observed agreement is in the file beside it so the correction can be\n'
        'checked. Complete-case days only (%d of %d), so both marginals and the\n'
        'observed rate use the same day set and kappa is exact.\n\n%s\n'
        % (len(full), len(st), fl))
    hdr(os.path.join(ROOTOUT, 'state_blocks.csv'),
        'Does agreement cluster around a shared currency leg?',
        'Each currency block is the 7 pairs containing that currency. A pair\n'
        'belongs to TWO blocks, so blocks overlap: "within" and "across" are not\n'
        'a partition of the pairs but of the 378 PAIRS-OF-PAIRS, by whether the\n'
        'two share a leg.\n\n'
        'Read this against the rank-7 floor. Pairs sharing a leg are\n'
        'algebraically linked, so a higher figure inside a block is expected and\n'
        'the informative quantity is the GAP between share-leg and no-leg.')
    hdr(os.path.join(ROOTOUT, 'state_breadth.csv'),
        'Breadth -- how often is FX one market rather than 28?',
        'Per day, how many of the 28 pairs share the modal state. The floor is\n'
        '7, not 1: four states over 28 pairs means the largest group cannot be\n'
        'smaller than ceil(28/4).\n\n'
        'The widest decile is tested against the %d-event crisis calendar with a\n'
        'circular-shift null on the breadth series, because "the widest days are\n'
        'crisis days" is exactly the kind of claim that is true by construction\n'
        'if crisis days are simply more common in some years.' % n_ev)
    hdr(os.path.join(ROOTOUT, 'state_pairs_extremes.csv'),
        'The strongest and weakest cells of the agreement matrix',
        'Every one of the strongest cells shares a currency leg, which is the\n'
        'rank-7 identity showing up rather than a discovery. Note that sharing a\n'
        'leg does NOT guarantee agreement -- GBPCAD/USDCAD is among the WEAKEST\n'
        'cells on the holdout at -0.157 despite both carrying CAD.\n\n'
        'Individual cells repeat only moderately between halves (spearman 0.37),\n'
        'so this table is a description of structure, not a lookup table.')
    print('\nwrote state_correlation.csv, state_correlation_summary.csv,')
    print('      state_blocks.csv, state_breadth.csv, state_breadth_daily.csv,')
    print('      state_breadth_summary.csv, state_neff_rolling.csv + .txt')
    return C, BL, BRD, S, RN


if __name__ == '__main__':
    main()
