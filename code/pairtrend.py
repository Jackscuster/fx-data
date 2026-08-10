import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Which pairs trend, which chop -- and whether gate 4 is throwing away the
signals that only work on the trending ones.

PART A. Mean forward 20-day efficiency per pair, in sample and out, ranked. The
efficiency ratio is |net move| / |path travelled| over the next 20 days, so a
high number means the pair goes somewhere in a straight line and a low number
means it thrashes. Nothing is fitted here; it is a property of the pair.

PART B. Gate 4 requires a signal to point the same way on at least 25 of 28
pairs. That is a deliberately brutal test of universality, and it kills 850 of
the 1,058 signals that reach it. The worry is specific: if a signal genuinely
works on trending pairs and genuinely does nothing on choppy ones, that is a
real and useful signal, and gate 4 would delete it for not being universal.

So: take every signal that clears the other gates and dies ONLY on agreement,
recover its per-pair out-of-sample spread from the score .npz, and ask whether
the pairs backing it are the pairs Part A ranks as trending. If they are, the
gate is discarding structure. If the backing pairs are an arbitrary scatter, the
gate is doing its job and those signals really are noise that happened to line
up on a subset.

The per-pair spreads come from the same .npz the live scorer wrote, so this asks
the question of the actual scored data rather than a re-derivation of it.

Writes results/pair_trend.csv and results/agree_gate.csv.
"""
import json
import numpy as np, pandas as pd
import sc3

PX = os.path.join(ROOTDATA, 'px28.csv')
SIG = os.path.join(ROOTOUT, 'signals.json')
SPLIT = pd.Timestamp('2016-01-01')
DIRS = {'own-price': 'scores', 'cross-sectional': 'scores3',
        'multi-timeframe': 'scores4', 'regime-v5': 'scores5',
        'trend-duration': 'scores6'}
G_T, G_S, G_A, G_M, G_D = 8., .0221, .893, .95, .6
TOPK = 7                        # a quarter of the panel = "the subset it works on"


def spearman(a, b):
    ra = pd.Series(a).rank().values
    rb = pd.Series(b).rank().values
    return float(np.corrcoef(ra, rb)[0, 1])


# ---------------------------------------------------------------- part A

def pair_trend(px=None):
    if px is None:
        px = pd.read_csv(PX, index_col=0, parse_dates=True)
    T = sc3.target(px)
    ins = px.index < SPLIT
    rows = []
    for p in px.columns:
        i, o = T[p][ins].dropna(), T[p][~ins].dropna()
        rows.append(dict(pair=p, eff_is=float(i.mean()), eff_oos=float(o.mean()),
                         sd_is=float(i.std()), sd_oos=float(o.std()),
                         n_is=len(i), n_oos=len(o)))
    D = pd.DataFrame(rows)
    D['rank_is'] = D.eff_is.rank(ascending=False)
    D['rank_oos'] = D.eff_oos.rank(ascending=False)
    D['rank_move'] = D.rank_is - D.rank_oos
    D['eff_both'] = (D.eff_is + D.eff_oos) / 2
    return D.sort_values('eff_both', ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------- part B

def per_pair_spreads(batch, want):
    """-> (pairs, {name: array of per-pair OOS spreads}) for one score dir."""
    d = os.path.join(ROOTOUT, DIRS[batch])
    if not os.path.isdir(d):
        return [], {}
    files = sorted(f for f in os.listdir(d) if f.endswith('.npz'))
    if len(files) < 28:
        return [], {}
    pairs = [f[:-4] for f in files]
    Z = [np.load(os.path.join(d, f), allow_pickle=True) for f in files]
    names = [str(x) for x in Z[0]['names']]
    idx = {n: j for j, n in enumerate(names)}
    hit = [n for n in want if n in idx]
    if not hit:
        return pairs, {}
    rows = np.array([idx[n] for n in hit])
    key = 'qo' if 'qo' in set(Z[0].files) else 'qto'
    SP = np.stack([z[key][rows][:, 4] - z[key][rows][:, 0] for z in Z], axis=1)
    return pairs, {n: SP[k] for k, n in enumerate(hit)}


def agreement_test(PT):
    """Signals killed ONLY by gate 4: are their backing pairs the trending ones?"""
    D = pd.DataFrame(json.load(open(SIG)))
    d = D[D.ok.fillna(True)].copy()
    with np.errstate(invalid='ignore', divide='ignore'):
        dec = d.to.abs() / d.ti.abs().clip(lower=.01)
    other = ((np.sign(d.ti) == np.sign(d.to)) & (d.to.abs() >= G_T)
             & (d.si.abs() >= G_S) & (d.mo.abs() >= G_M) & (dec >= G_D)
             & (d.tsb.isna() | (d.tsb >= G_M * 0 + 4)))
    killed = d[other & (d.ao < G_A)].copy()
    passed = d[other & (d.ao >= G_A)].copy()
    print('clear every gate but agreement: %d killed by gate 4, %d survive it'
          % (len(killed), len(passed)))

    trend_rank = dict(zip(PT.pair, PT.eff_both.rank(ascending=False)))
    eff = dict(zip(PT.pair, PT.eff_both))
    out, missing = [], 0
    for batch, grp in killed.groupby('b'):
        if batch not in DIRS:
            missing += len(grp)
            continue
        pairs, SP = per_pair_spreads(batch, list(grp.s))
        if not SP:
            missing += len(grp)
            continue
        for _, r in grp.iterrows():
            v = SP.get(r.s)
            if v is None or not np.isfinite(v).any():
                continue
            sgn = np.sign(r.so)
            back = np.array([p for p, x in zip(pairs, v)
                             if np.isfinite(x) and np.sign(x) == sgn])
            against = np.array([p for p, x in zip(pairs, v)
                                if np.isfinite(x) and np.sign(x) != sgn])
            if len(back) < 3 or len(against) < 3:
                continue
            # TWO definitions of "the subset this signal works on", because the
            # sign-based one turns out to be no subset at all: these signals
            # average 22 of 28 pairs pointing the right way, they just miss 25.
            # The strength-based one is the question actually being asked --
            # where is the effect BIG, not merely where is it the right sign.
            fin = np.isfinite(v)
            ord_ = np.argsort(-np.abs(np.where(fin, v, 0)))
            strong = [pairs[i] for i in ord_[:TOPK] if fin[i]]
            weak = [pairs[i] for i in ord_[-TOPK:] if fin[i]]
            out.append(dict(
                signal=r.s, batch=batch, ao=float(r.ao), to=float(r.to),
                so=float(r.so), n_back=len(back),
                back_eff=float(np.mean([eff[p] for p in back])),
                against_eff=float(np.mean([eff[p] for p in against])),
                back_rank=float(np.mean([trend_rank[p] for p in back])),
                against_rank=float(np.mean([trend_rank[p] for p in against])),
                strong_eff=float(np.mean([eff[p] for p in strong])) if strong else np.nan,
                weak_eff=float(np.mean([eff[p] for p in weak])) if weak else np.nan,
                backers=' '.join(sorted(back)),
                strongest=' '.join(strong)))
    A = pd.DataFrame(out)
    if missing:
        print('%d killed signals have no per-pair .npz (v7 pools statistics only)'
              % missing)
    return A, killed, passed


def report(PT, A):
    print('\nPART A -- PAIR TRENDINESS (mean forward 20d efficiency)')
    print(PT[['pair', 'eff_is', 'eff_oos', 'rank_is', 'rank_oos', 'rank_move']]
          .to_string(index=False, formatters={'eff_is': '{:.4f}'.format,
                                              'eff_oos': '{:.4f}'.format}))
    rho = spearman(PT.eff_is, PT.eff_oos)
    print('\nIS vs OOS rank correlation (Spearman): %.3f' % rho)
    print('level: IS mean %.4f, OOS mean %.4f -- the whole panel %s out of sample'
          % (PT.eff_is.mean(), PT.eff_oos.mean(),
             'trended more' if PT.eff_oos.mean() > PT.eff_is.mean() else 'chopped more'))
    top = PT.head(5).pair.tolist(); bot = PT.tail(5).pair.tolist()
    print('trendiest: %s' % ', '.join(top))
    print('choppiest: %s' % ', '.join(bot))
    # the ranking is not arbitrary: it sorts almost exactly by dollar and by yen
    MAJ = {'EURUSD', 'GBPUSD', 'AUDUSD', 'NZDUSD', 'USDCAD', 'USDCHF', 'USDJPY'}
    PT['kind'] = np.where(PT.pair.isin(MAJ), 'major', 'cross')
    print('\nmajors mean %.4f (n=%d) vs crosses %.4f (n=%d)'
          % (PT[PT.kind == 'major'].eff_both.mean(), (PT.kind == 'major').sum(),
             PT[PT.kind == 'cross'].eff_both.mean(), (PT.kind == 'cross').sum()))
    for leg in ('JPY', 'CHF', 'CAD'):
        m = PT.pair.str.contains(leg) & (PT.kind == 'cross')
        print('  %s crosses %.4f (n=%d)' % (leg, PT[m].eff_both.mean(), int(m.sum())))
    se = PT.sd_is.mean() / np.sqrt(PT.n_is.mean())
    print('scale: trendiest minus choppiest %.4f, against a standard error on any '
          'one pair mean of %.5f' % (PT.eff_both.max() - PT.eff_both.min(), se))

    print('\nPART B -- IS GATE 4 KILLING PAIR-SPECIFIC TREND SIGNALS?')
    if not len(A):
        print('  no agreement-killed signal had per-pair spreads to test')
        return
    d = A.back_eff - A.against_eff
    print('  %d testable signals killed only by agreement' % len(A))
    print('  mean efficiency of BACKING pairs   %.4f' % A.back_eff.mean())
    print('  mean efficiency of OPPOSING pairs  %.4f' % A.against_eff.mean())
    print('  difference %+.5f, signals where backers are trendier: %.1f%%'
          % (d.mean(), 100 * (d > 0).mean()))
    se = d.std() / np.sqrt(len(d))
    print('  t on the difference: %+.2f' % (d.mean() / se if se else np.nan))
    ds = (A.strong_eff - A.weak_eff).dropna()
    print('\n  strength-based subset (top %d pairs by |spread| vs bottom %d):' % (TOPK, TOPK))
    print('    strongest-%d pairs mean efficiency %.4f' % (TOPK, A.strong_eff.mean()))
    print('    weakest-%d   pairs mean efficiency %.4f' % (TOPK, A.weak_eff.mean()))
    ses = ds.std() / np.sqrt(len(ds)) if len(ds) else np.nan
    print('    difference %+.5f, t %+.2f, trendier-strong in %.1f%% of signals'
          % (ds.mean(), ds.mean() / ses if ses else np.nan, 100 * (ds > 0).mean()))

    # which pairs do the killed signals actually lean on
    cnt = {}
    for b in A.strongest:
        for p in str(b).split():
            cnt[p] = cnt.get(p, 0) + 1
    S = (pd.DataFrame({'pair': list(cnt), 'times_backing': list(cnt.values())})
         .merge(PT[['pair', 'eff_both', 'rank_is', 'rank_oos']], on='pair'))
    S['backing_rate'] = S.times_backing / len(A)   # share of killed signals where
    #                                                 this pair is in the strongest 7
    S = S.sort_values('backing_rate', ascending=False)
    r2 = spearman(S.backing_rate, S.eff_both)
    print('\n  how often each pair is among the strongest %d for an'
          ' agreement-killed signal, against its trendiness:' % TOPK)
    print(S[['pair', 'backing_rate', 'eff_both']].head(8)
          .to_string(index=False, formatters={'backing_rate': '{:.3f}'.format,
                                              'eff_both': '{:.4f}'.format}))
    print('  ... rank correlation across all 28 pairs: %+.3f' % r2)
    verdict = ('gate 4 IS discarding trend-concentrated structure'
               if (r2 > .4 and ds.mean() > 0) else
               'no sign gate 4 is selectively killing trending-pair signals')
    print('\n  VERDICT: %s' % verdict)
    return S


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    PT = pair_trend(px)
    PT.to_csv(os.path.join(ROOTOUT, 'pair_trend.csv'), index=False)
    A, killed, passed = agreement_test(PT)
    A.to_csv(os.path.join(ROOTOUT, 'agree_gate.csv'), index=False)
    S = report(PT, A)
    if S is not None:
        S.to_csv(os.path.join(ROOTOUT, 'agree_gate_pairs.csv'), index=False)
    print('\nwrote pair_trend.csv, agree_gate.csv, agree_gate_pairs.csv')
    return PT, A


if __name__ == '__main__':
    main()
