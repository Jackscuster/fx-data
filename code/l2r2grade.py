import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""THE BLIND GRADE, THE quality_tag SPLIT AND THE EPISODE-THIRD SPLIT (0l).

THE BLIND GRADE IS REPORTED AND NEVER USED. Year 5 of each step is graded by
the same objective the tuner reads but is never seen by the tuner and never
gates anything. The question it answers is whether a grade-year record predicts
the trade year at all -- graded-pass against graded-fail on year 6, and the
rank correlation of the two.

THE TWO LAYER 1 SPLITS are reported on every ROUTED TREND slice and gate
nothing (LAYER1_INTERFACE.md 4):
  quality_tag     high / low at the tuning-window cut, from
                  results/layer1_trend_quality_series.csv. The flag means
                  nothing off a trending bar and is empty there.
  episode third   first / middle / last third of each trend_episode_id, from
                  the same file. Layer 1's own measurement says routed trend
                  P&L concentrates in the first third, which is the part the
                  label is a median 24 bars too late to catch; this is the
                  check of that on the restart's own numbers.
"""
import numpy as np, pandas as pd
import l2sweep as S
import l2r2gate1 as G
import l2r2gate2 as G2

QS = os.path.join(ROOTOUT, 'layer1_trend_quality_series.csv')


def blind_grade(mode='A', tag='full'):
    """Graded-pass vs graded-fail on the trade year, per stream and step, from
    the gate 2 bank's own grade-year and trade-year records."""
    Wn, TG, CB, TS, _od = G2.load(mode, tag)
    ST = G2.steps()
    rows = []
    for si, stp in enumerate(ST):
        for stream in range(4):
            gb = G2.role_sum(Wn[:, stream, si], *stp['grade'])
            tb = G2.role_sum(Wn[:, stream, si], *stp['trade'])
            gn, ge, _gp = G2.objective(gb)
            tn, te, _tp = G2.objective(tb)
            ok = (TG[:, stream, si] >= 0) & (gn > 0) & (tn > 0) & np.isfinite(ge) & np.isfinite(te)
            if ok.sum() < 20:
                continue
            # THE GRADE BAR IS 0f's: the gate 2 bars on ONE year, so the trade
            # floor is 10 and not 50 (50/5, one year not five).
            passed = ok & (gn >= 10) & (ge > 0)
            failed = ok & (gn >= 10) & (ge <= 0)
            def wavg(m):
                if not m.any():
                    return np.nan, 0
                return float(np.average(te[m], weights=tn[m])), int(m.sum())
            tp_, np_ = wavg(passed)
            tf_, nf_ = wavg(failed)
            from scipy.stats import spearmanr
            rho, pv = spearmanr(ge[ok], te[ok])
            rows.append(dict(mode=mode, step=stp['name'], stream=G2.STREAMS[stream],
                             n_eligible=int(ok.sum()),
                             n_graded_pass=np_, n_graded_fail=nf_,
                             trade_R_graded_pass=tp_, trade_R_graded_fail=tf_,
                             spearman_grade_to_trade=float(rho), p=float(pv)))
    return pd.DataFrame(rows)


def _quality():
    G.manifest_check()
    q = pd.read_csv(QS, comment='#', parse_dates=['date'])
    return q


def layer1_splits(mode='A', tag='full', nsample=4000, seed=20261118):
    """quality_tag and episode-third, on the ROUTED TREND slice only.

    Both are REPORTED and gate nothing. A stratified sample is used and its
    size is stated: the split needs per-trade entry dates, which means an
    engine pass per strategy, and the point of the table is the SHAPE of the
    split rather than a field-wide total.
    """
    import l2r2book as BK
    S.load_costs()
    q = _quality()
    qk = q.set_index(['pair', 'date'])
    opts = S.mode_opts(S.slot_options(), mode)
    ntot = S.n_combos(opts)
    rng = np.random.default_rng(seed)
    idxs = sorted(rng.choice(ntot, size=min(nsample, ntot), replace=False).tolist())
    z = np.load(BK._bank_slice_file(mode, tag), allow_pickle=True)
    TG = z['tag']; CB = z['combo']
    Y = G2.Years(cap=30000)
    ST = G2.steps()
    rec = []
    for si, stp in enumerate(ST):
        years = set(range(stp['trade'][0], stp['trade'][1] + 1))
        for k in idxs:
            ci = int(TG[k, 0, si])          # stream 0 = trend-routed
            if ci < 0:
                continue
            combo = tuple(CB[k])
            ip, risk = BK.winner_config(mode, combo, 'trend', ci)
            pr, dy, dr, mk, lab, tid = BK.marks_of(
                Y, mode, combo, ip, risk, 'trend', 2, S.REGIME_CODE['trending'], years)
            if not len(pr):
                continue
            d = pd.DataFrame(dict(pair=pr, day=pd.to_datetime(dy), mark=mk, tid=tid, lab=lab))
            d = d[d.lab == S.REGIME_CODE['trending']]
            if not len(d):
                continue
            j = d.join(qk[['quality_tag', 'trend_episode_id']], on=['pair', 'day'])
            rec.append(j[['mark', 'quality_tag', 'trend_episode_id']].assign(step=stp['name']))
    if not rec:
        return pd.DataFrame(), pd.DataFrame()
    A = pd.concat(rec, ignore_index=True)
    # ---- quality_tag split
    qt = A.groupby(['step', 'quality_tag'], dropna=False).mark.agg(['sum', 'mean', 'count'])
    qt = qt.reset_index().rename(columns={'sum': 'total_R', 'mean': 'mean_R_per_mark',
                                          'count': 'mark_rows'})
    qt['split'] = 'quality_tag'
    qt['scope'] = 'routed trend, sample %d' % nsample
    # ---- episode-third split: rank each mark inside its own episode
    B = A[A.trend_episode_id.notna()].copy()
    if len(B):
        B['r'] = B.groupby('trend_episode_id').cumcount()
        B['n'] = B.groupby('trend_episode_id').trend_episode_id.transform('size')
        B['third'] = np.where(B.r < B.n / 3, 'first',
                              np.where(B.r < 2 * B.n / 3, 'middle', 'last'))
        et = B.groupby(['step', 'third']).mark.agg(['sum', 'mean', 'count']).reset_index()
        et = et.rename(columns={'sum': 'total_R', 'mean': 'mean_R_per_mark', 'count': 'mark_rows'})
        et['split'] = 'episode_third'
        et['scope'] = 'routed trend, sample %d' % nsample
    else:
        et = pd.DataFrame()
    return qt, et


def stage_grade(mode='A', tag='full', nsample=4000):
    B = blind_grade(mode, tag)
    bo = os.path.join(ROOTOUT, 'r2gate2', 'mode%s_books_blindgrade.csv' % mode)
    B.to_csv(bo, index=False)
    print('  blind grade: %d rows -> %s' % (len(B), bo.replace(_R + '/', '')), flush=True)
    qt, et = layer1_splits(mode, tag, nsample=nsample)
    so = os.path.join(ROOTOUT, 'r2gate2', 'mode%s_books_layer1splits.csv' % mode)
    Sp = pd.concat([x for x in (qt, et) if len(x)], ignore_index=True) if (len(qt) or len(et)) \
        else pd.DataFrame()
    Sp.to_csv(so, index=False)
    print('  layer 1 splits: %d rows -> %s' % (len(Sp), so.replace(_R + '/', '')), flush=True)
    return B, Sp, bo, so


if __name__ == '__main__':
    stage_grade(G.opt('--mode', str, 'A'), G.opt('--tag', str, 'full'),
                nsample=G.opt('--n', int, 4000))
