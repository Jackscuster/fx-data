import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""ONE-SHOT confirmation of the ranging cell on 1990-1998. Zero tuning.

WHAT IS FROZEN, and it is everything. W=5, the same one-bar lag, the same
episode scoring from ratediff.py imported rather than reimplemented, and the
classifier applied with its cut points FITTED ON 1999-2015 and carried backwards
unchanged. Nothing is refitted on the pre-1999 sample -- that is the whole point
of a confirmation, and refitting would make it a second discovery.

WHAT DIFFERS FROM THE BRIEF, stated before the read:

  3 pairs, not 21. GBPUSD, USDCHF, GBPCHF. Only USD, GBP and CHF have 2-year
  yields before 1999 -- CAD starts 2001, AUD's cache is a 31-row fragment, JPY's
  will not parse and NZD does not exist. See pre1999_coverage.txt.

  AND THOSE THREE ARE NOT INDEPENDENT. Three currencies give three pairs and any
  one is the ratio of the other two, so the effective sample is nearer two series
  than three. This is a weaker confirmation than the 21-pair original by
  construction, and it is reported as such whichever way it lands.

  FX is rebuilt from the FRED mirror of H.10 because the Fed endpoint returns
  403 here. The rebuild was checked against the committed panel over 6,916
  shared bars from 1999 on: median relative difference 0.00004, 0.00000, 0.00004.

THE VERDICT RULE IS FIXED BEFORE THE READ. The ranging excess must be positive
AND rank in the top 3 of 51 against the circular-shift null, which is the bar the
original cleared on the holdout (rank 2 of 51). Anything else is a failure and
closes the question.

Writes results/ratediff_pre1999_{result,null}.csv with .txt companions.
"""
import numpy as np, pandas as pd

PXP = os.path.join(ROOTDATA, 'pre1999_px.csv')
RTP = os.path.join(ROOTDATA, 'pre1999_rates.csv')
SPLIT = pd.Timestamp('2016-01-01')
W_FROZEN = 5
NSHIFT = int(os.environ.get('FX_NSHIFT', 50))
MINOFF = 250
RANK_BAR = 3

from ratediff import momentum, episodes, MIN_EP
from final import scores, activity, DROP_TESTS, BUMP, ACTW
from twoscores import classify


def frozen_states(pre, pairs):
    """Classifier fitted on 1999-2015 and applied unchanged to 1990-1998.

    The pre-1999 panel is JOINED to the modern one and the fit mask set to
    1999-01-01..2015-12-31, so every standardisation constant and every tercile
    threshold comes from the modern in-sample window exactly as committed. The
    pre-1999 rows are then read out.

    Passing an all-False mask instead -- the first attempt -- leaves zfit with no
    data to fit on, every score NaN and every episode list empty. It looked like
    "no episodes" rather than "no fit", which is why the join is explicit here.
    """
    modern = pd.read_csv(os.path.join(ROOTDATA, 'px28.csv'), index_col=0,
                         parse_dates=True)[pairs]
    joined = pd.concat([pre[pairs], modern]).sort_index()
    joined = joined[~joined.index.duplicated(keep='last')]
    fit = np.asarray((joined.index >= pd.Timestamp('1999-01-01'))
                     & (joined.index < SPLIT))
    tr, ch = scores(joined, fit, drop_tests=DROP_TESTS)
    a = activity(joined, fit)
    adj = tr - a.replace(ACTW).astype(float) * BUMP
    lab = classify(adj, ch, fit)[0]
    return lab.reindex(pre.index)


def main():
    px = pd.read_csv(PXP, index_col=0, parse_dates=True)
    rt = pd.read_csv(RTP, index_col=0, parse_dates=True)
    pairs = [p for p in px.columns
             if p[:3] in rt and p[3:] in rt
             and rt[p[:3]].notna().sum() > 200 and rt[p[3:]].notna().sum() > 200]
    print('PRE-1999 CONFIRMATION. %d pairs: %s' % (len(pairs), ', '.join(pairs)))
    print('  %s -> %s, %d bars. W=%d frozen, zero tuning.'
          % (px.index.min().date(), px.index.max().date(), len(px), W_FROZEN))

    # the modern fit window does not intersect this panel at all, so the
    # thresholds are carried in from the committed fit and nothing is refitted
    st = frozen_states(px, pairs)
    print('  labelled pre-1999 pair-days: %d of %d'
          % (int(st.notna().sum().sum()), st.shape[0] * st.shape[1]))
    diff = pd.DataFrame({p: rt[p[:3]] - rt[p[3:]] for p in pairs})
    mom = momentum(diff, W_FROZEN)
    allmask = pd.Series(True, index=px.index)

    def read(m):
        E = {s: episodes(st, px[pairs], m, pairs, allmask, s)
             for s in ('trending', 'ranging', 'trend-in-range', 'neither')}
        allE = pd.concat([v for v in E.values() if len(v)], ignore_index=True)
        if not len(allE) or not len(E['ranging']):
            return np.nan, 0, np.nan, np.nan
        base = allE.agree.mean()
        r = E['ranging']
        return (float(r.agree.mean() - base), len(r), float(r.agree.mean()),
                float(base))

    excess, n_ep, agree, base = read(mom)
    print('\n  RANGING, pre-1999: %d episodes, agree %.3f, base %.3f, '
          'excess %+.4f' % (n_ep, agree, base, excess))
    E = {s: episodes(st, px[pairs], mom, pairs, allmask, s)
         for s in ('trending', 'ranging', 'trend-in-range', 'neither')}
    allE = pd.concat([v for v in E.values() if len(v)], ignore_index=True)
    t = E['trending']
    print('  trending, for reference: %d episodes, excess %+.4f'
          % (len(t), (t.agree.mean() - allE.agree.mean()) if len(t) else np.nan))

    print('\n  NULL -- %d circular shifts of the yield panel' % NSHIFT)
    n = len(px.index)
    rng = np.random.default_rng(19901998)
    acc = []
    for i in range(NSHIFT):
        k = int(rng.integers(MINOFF, n - MINOFF))
        d2 = pd.DataFrame(np.roll(diff.values, k, axis=0), index=diff.index,
                          columns=diff.columns)
        e2, _, _, _ = read(momentum(d2, W_FROZEN))
        if np.isfinite(e2):
            acc.append(e2)
        if (i + 1) % 10 == 0:
            print('    ... %d/%d' % (i + 1, NSHIFT), flush=True)
    v = np.array(acc, float)
    rank = int((v >= excess).sum()) + 1
    p = rank / (len(v) + 1)
    print('\n  real %+.4f | null %+.4f +/- %.4f over %d shifts | rank %d of %d '
          '| p=%.3f' % (excess, v.mean(), v.std(), len(v), rank, len(v) + 1, p))

    passed = bool(excess > 0 and rank <= RANK_BAR)
    print('\n  VERDICT RULE (fixed before the read): excess > 0 AND rank <= %d'
          % RANK_BAR)
    print('  RESULT: %s' % ('CONFIRMED' if passed else 'FAILED -- question closed'))

    R = pd.DataFrame([dict(sample='1990-1998', pairs=len(pairs),
                           pair_list=', '.join(pairs), W=W_FROZEN,
                           ranging_episodes=n_ep, agree=agree, base=base,
                           excess=excess, trending_episodes=len(t),
                           trending_excess=float(t.agree.mean()
                                                 - allE.agree.mean())
                           if len(t) else np.nan,
                           null_shifts=len(v), null_mean=float(v.mean()),
                           null_sd=float(v.std()), rank_of_real=rank,
                           n_compared=len(v) + 1, p=p,
                           rank_bar=RANK_BAR, verdict='CONFIRMED' if passed
                           else 'FAILED')])
    R.to_csv(os.path.join(ROOTOUT, 'ratediff_pre1999_result.csv'), index=False)
    pd.DataFrame({'shift_excess': v}).to_csv(
        os.path.join(ROOTOUT, 'ratediff_pre1999_null.csv'), index=False)

    body = (
        'One-shot confirmation of the ranging cell on data never touched.\n\n'
        'FROZEN: W=%d, one-bar lag, the episode scoring imported from\n'
        'ratediff.py rather than reimplemented, and the classifier cut points\n'
        'fitted on 1999-2015 carried backwards unchanged. Nothing was refitted.\n\n'
        'THREE PAIRS, NOT 21: %s. Only USD, GBP and CHF have 2-year yields\n'
        'before 1999. And they are not independent -- three currencies give\n'
        'three pairs and any one is the ratio of the other two, so the\n'
        'effective sample is nearer two series than three. This is a weaker\n'
        'confirmation than the 21-pair original by construction.\n\n'
        'FX rebuilt from the FRED mirror of H.10 (the Fed endpoint returns 403\n'
        'here), checked against the committed panel over 6,916 shared bars from\n'
        '1999 on: median relative difference 0.00004 / 0.00000 / 0.00004.\n\n'
        'VERDICT RULE, fixed before the read: ranging excess > 0 AND rank <= %d\n'
        'of the null draws, the bar the original cleared on its holdout.\n\n'
        'RESULT: %s. excess %+.4f, rank %d of %d, p=%.3f over %d shifts.\n'
        % (W_FROZEN, ', '.join(pairs), RANK_BAR,
           'CONFIRMED' if passed else 'FAILED -- the question is closed',
           excess, rank, len(v) + 1, p, len(v)))
    with open(os.path.join(ROOTOUT, 'ratediff_pre1999_result.txt'), 'w') as f:
        f.write('Pre-1999 confirmation\n=====================\n\n' + body)
    with open(os.path.join(ROOTOUT, 'ratediff_pre1999_null.txt'), 'w') as f:
        f.write('Pre-1999 null draws\n===================\n\n'
                'One row per circular shift of the yield panel against price,\n'
                'offsets of at least %d bars. %d draws, the exact count run.\n'
                % (MINOFF, len(v)))
    print('\nwrote ratediff_pre1999_{result,null}.csv + .txt')


if __name__ == '__main__':
    main()
