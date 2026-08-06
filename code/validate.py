import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""The four validation tests. Every one asks: is the estimator detecting anything?

None of these is a money metric. They test regime identification and nothing else.

1 SHUFFLED LABELS      shuffle the regime labels while preserving run lengths and
                       rescore, 500 times. If the real labels do not clearly beat
                       the shuffled null, the composite is only chopping the sample
                       into persistent blocks and any persistent blocking would
                       score the same. This is the test that can invalidate
                       everything else.
2 SYNTHETIC TRUTH      simulate a panel whose regimes we set ourselves, run the
                       composite, and measure accuracy, precision, recall and
                       detection lag. The ONLY place a real accuracy number can
                       exist, because every other score is against a target derived
                       from the same prices.
3 REFIT STABILITY      build the composite with data through 2015, label history;
                       rebuild through 2020, label again. If 2010's labels move,
                       the composite is using information it would not have had.
4 PERSISTENCE          run lengths, share of runs under 5 days, transition matrix.
                       A real regime structure has a strong diagonal. Flicker is
                       noise however good the spread looks.

Writes results/validation_*.csv and prints a verdict per test.
"""
import json, time
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
SPLIT = pd.Timestamp('2016-01-01')
H = 20
NSHUF = 500
LAB = ['chop', 'mid', 'trend']
SEED = 0


def fwd_eff(lp, h=H):
    r = lp.diff()
    return ((lp.shift(-h) - lp).abs() / r.abs().shift(-h).rolling(h).sum()
            ).replace([np.inf, -np.inf], np.nan)


def terciles(c, ins):
    """IS-only tercile cuts applied unchanged."""
    if c[ins].notna().sum() < 100:
        return pd.Series(np.nan, index=c.index, dtype=object)
    q = np.nanquantile(c[ins].dropna(), [1 / 3, 2 / 3])
    return pd.Series(np.where(c < q[0], LAB[0], np.where(c > q[1], LAB[2], LAB[1])),
                     index=c.index).where(c.notna())


def runs_of(lab):
    """[(label, length), ...] preserving order."""
    v = lab.dropna().values
    if not len(v):
        return []
    out, cur, n = [], v[0], 1
    for x in v[1:]:
        if x == cur:
            n += 1
        else:
            out.append((cur, n)); cur, n = x, 1
    out.append((cur, n))
    return out


def rebuild(runs):
    return np.concatenate([np.repeat(l, n) for l, n in runs]) if runs else np.array([])


# ---------------- 1. shuffled labels ----------------
def test_shuffle(C, px, n_shuf=NSHUF):
    rng = np.random.default_rng(SEED)
    real, null = [], np.zeros(n_shuf)
    per_pair = []
    for p in px.columns:
        lp = np.log(px[p].astype(float))
        e = fwd_eff(lp)
        ins = lp.index < SPLIT
        lab = terciles(C[p].reindex(lp.index), ins)
        d = pd.DataFrame({'l': lab, 'e': e}).dropna()
        d = d[d.index >= SPLIT]
        if len(d) < 400:
            continue
        R = runs_of(d.l)
        stat = d.e[d.l == 'trend'].mean() - d.e[d.l == 'chop'].mean()
        real.append(stat)
        per_pair.append((p, stat, R, d.e.values))
    REAL = float(np.nanmean(real))
    for k in range(n_shuf):
        vals = []
        for p, _, R, ev in per_pair:
            lens = [n for _, n in R]
            labs = [l for l, _ in R]
            rng.shuffle(labs)                       # run LENGTHS preserved, order permuted
            seq = rebuild(list(zip(labs, lens)))[:len(ev)]
            if len(seq) < len(ev):
                seq = np.concatenate([seq, np.repeat('mid', len(ev) - len(seq))])
            vals.append(ev[seq == 'trend'].mean() - ev[seq == 'chop'].mean())
        null[k] = np.nanmean(vals)
    pct = float((null < REAL).mean())
    z = float((REAL - null.mean()) / null.std()) if null.std() > 0 else np.nan
    T = pd.DataFrame([dict(test='shuffled_labels', real=REAL, null_mean=float(null.mean()),
                           null_std=float(null.std()), null_p95=float(np.quantile(null, .95)),
                           percentile=pct, z=z, n_shuffles=n_shuf,
                           passes=bool(pct >= .99))])
    T.to_csv(os.path.join(ROOTOUT, 'validation_shuffle.csv'), index=False)
    print('\n1. SHUFFLED LABELS (%d shuffles, run lengths preserved)' % n_shuf)
    print('   real trend-minus-chop efficiency gap : %+.5f' % REAL)
    print('   shuffled null: mean %+.5f  sd %.5f  95th %+.5f'
          % (null.mean(), null.std(), np.quantile(null, .95)))
    print('   real sits at the %.1f%% percentile of the null, z = %+.2f' % (100 * pct, z))
    print('   VERDICT: %s' % ('PASS - real labels clearly beat shuffled' if pct >= .99
                              else 'FAIL - real labels are inside the null distribution'))
    return T


# ---------------- 2. synthetic ground truth ----------------
def synth_panel(n_days=6000, trend_len=200, chop_len=150, seed=SEED):
    """A 28-pair panel with a KNOWN regime, shared across the panel like real
    volatility events are, plus per-pair idiosyncratic noise."""
    rng = np.random.default_rng(seed)
    truth, t = [], 0
    while len(truth) < n_days:
        truth += ['trend'] * trend_len if t % 2 == 0 else ['chop'] * chop_len
        t += 1
    truth = np.array(truth[:n_days])
    idx = pd.bdate_range('1999-01-04', periods=n_days)
    cols = pd.read_csv(PX, index_col=0, nrows=1).columns
    out = {}
    for j, c in enumerate(cols):
        drift = rng.normal(0, 1, n_days) * 0.002
        r = np.zeros(n_days)
        prev = 0.0
        for i in range(n_days):
            if truth[i] == 'trend':
                r[i] = 0.35 * prev + drift[i] * 0.6      # persistent -> high efficiency
            else:
                r[i] = -0.35 * prev + drift[i] * 1.2     # reverting -> low efficiency
            prev = r[i]
        out[c] = np.exp(np.cumsum(r))
    return pd.DataFrame(out, index=idx), pd.Series(truth, index=idx)


def test_synthetic(px_real):
    import survivors
    print('\n2. SYNTHETIC GROUND TRUTH')
    S, truth = synth_panel()
    t0 = time.time()
    C = survivors.build(S, force=True)                   # composite on synthetic prices
    ins = S.index < S.index[len(S) // 2]
    rows = []
    for p in S.columns:
        lab = terciles(C[p], ins)
        d = pd.DataFrame({'l': lab, 't': truth}).dropna()
        d = d[~ins[:len(d)]] if len(d) == len(ins) else d
        d = d[d.l != 'mid']                              # 3-state read vs 2-state truth
        if len(d) < 200:
            continue
        pred = (d.l == 'trend')
        act = (d.t == 'trend')
        tp = int((pred & act).sum()); fp = int((pred & ~act).sum())
        fn = int((~pred & act).sum()); tn = int((~pred & ~act).sum())
        rows.append(dict(pair=p, acc=(tp + tn) / len(d),
                         prec=tp / (tp + fp) if tp + fp else np.nan,
                         rec=tp / (tp + fn) if tp + fn else np.nan))
    # detection lag: bars from each true regime start to the first correct call
    lags = []
    for p in list(S.columns)[:8]:
        lab = terciles(C[p], ins).reindex(S.index)
        ch = np.flatnonzero(truth.values[1:] != truth.values[:-1]) + 1
        for st in ch:
            want = 'trend' if truth.values[st] == 'trend' else 'chop'
            seg = lab.values[st:st + 120]
            hit = np.flatnonzero(seg == want)
            if len(hit):
                lags.append(int(hit[0]))
    A = pd.DataFrame(rows)
    T = pd.DataFrame([dict(test='synthetic', accuracy=A.acc.mean(), precision=A.prec.mean(),
                           recall=A.rec.mean(), median_lag_days=float(np.median(lags)) if lags else np.nan,
                           n_pairs=len(A), built_s=round(time.time() - t0),
                           passes=bool(A.acc.mean() > .55))])
    T.to_csv(os.path.join(ROOTOUT, 'validation_synthetic.csv'), index=False)
    print('   accuracy %.3f | precision %.3f | recall %.3f | median detection lag %s days'
          % (A.acc.mean(), A.prec.mean(), A.rec.mean(),
             ('%.0f' % np.median(lags)) if lags else 'n/a'))
    print('   VERDICT: %s' % ('PASS - beats a coin flip on known regimes'
                              if A.acc.mean() > .55 else
                              'FAIL - no better than chance on regimes we defined'))
    survivors.build(px_real, force=True)                 # restore the real cache
    return T


# ---------------- 3. refit stability ----------------
def test_refit(px):
    """Rebuild the composite using only data up to each cutoff, relabel, compare.

    LIMITATION, STATED PLAINLY: this refits the COMPOSITE, not the survivor
    SELECTION. The 32 survivors were chosen with gates that read out-of-sample
    statistics, so the choice of which signals to combine already knows about
    2016-2026. That is a larger look-ahead than this test can measure, and closing
    it means re-running the whole gauntlet on in-sample data only.
    """
    import survivors
    print('\n3. REFIT STABILITY')
    print('   (refits the composite only -- the survivor SELECTION still used OOS gates)')
    labs = {}
    for cut in ('2015-12-31', '2020-12-31'):
        sub = px[px.index <= cut]
        C = survivors.build(sub, force=True)
        ins = sub.index < SPLIT
        labs[cut] = {p: terciles(C[p], ins) for p in sub.columns}
    ref = pd.Timestamp('2010-01-01'), pd.Timestamp('2010-12-31')
    rows = []
    for p in px.columns:
        a = labs['2015-12-31'][p]; b = labs['2020-12-31'][p]
        m = (a.index >= ref[0]) & (a.index <= ref[1])
        aa = a[m].dropna(); bb = b.reindex(aa.index).dropna()
        common = aa.index.intersection(bb.index)
        if len(common) < 50:
            continue
        rows.append(dict(pair=p, n=len(common),
                         same=float((aa[common] == bb[common]).mean())))
    A = pd.DataFrame(rows)
    T = pd.DataFrame([dict(test='refit_stability', year=2010,
                           label_agreement=A.same.mean(), n_pairs=len(A),
                           passes=bool(A.same.mean() >= .95))])
    T.to_csv(os.path.join(ROOTOUT, 'validation_refit.csv'), index=False)
    print('   2010 labels identical after refitting through 2020: %.1f%% of days'
          % (100 * A.same.mean()))
    print('   VERDICT: %s' % ('PASS - history does not get rewritten'
                              if A.same.mean() >= .95 else
                              'FAIL - past labels move when later data arrives'))
    survivors.build(px, force=True)
    return T


# ---------------- 4. persistence and transitions ----------------
def test_persistence(C, px):
    print('\n4. PERSISTENCE AND TRANSITIONS')
    lens = {l: [] for l in LAB}
    trans = pd.DataFrame(0, index=LAB, columns=LAB)
    for p in px.columns:
        lp = np.log(px[p].astype(float))
        ins = lp.index < SPLIT
        lab = terciles(C[p].reindex(lp.index), ins).dropna()
        lab = lab[lab.index >= SPLIT]
        if len(lab) < 200:
            continue
        for l, n in runs_of(lab):
            lens[l].append(n)
        v = lab.values
        for a, b in zip(v[:-1], v[1:]):
            trans.loc[a, b] += 1
    P = trans.div(trans.sum(axis=1), axis=0)
    rows = []
    for l in LAB:
        x = np.array(lens[l])
        # share of RUNS under 5 days counts a 2-day run equal to a 200-day one.
        # The honest flicker measure is the share of BARS spent in short runs.
        rows.append(dict(regime=l, n_runs=len(x), median_len=float(np.median(x)),
                         mean_len=float(x.mean()),
                         share_runs_under_5=float((x < 5).mean()),
                         share_bars_under_5=float(x[x < 5].sum() / x.sum()),
                         diagonal=float(P.loc[l, l])))
    T = pd.DataFrame(rows)
    T.to_csv(os.path.join(ROOTOUT, 'validation_persistence.csv'), index=False)
    P.round(4).to_csv(os.path.join(ROOTOUT, 'validation_transitions.csv'))
    print(T.to_string(index=False, float_format=lambda v: '%.3f' % v))
    print('\n   transition matrix (row = from, col = to)')
    print(P.round(3).to_string())
    diag = float(np.mean([P.loc[l, l] for l in LAB]))
    fr = float(np.mean([r['share_runs_under_5'] for r in rows]))
    fb = float(np.mean([r['share_bars_under_5'] for r in rows]))
    print('\n   mean diagonal %.3f' % diag)
    print('   short runs: %.1f%% of RUNS are under 5 days, but only %.1f%% of BARS'
          % (100 * fr, 100 * fb))
    print('   VERDICT: %s' % ('PASS - strong diagonal, time is spent in persistent runs'
                              if diag >= .9 and fb <= .05 else
                              'FAIL - the read flickers faster than a regime should'))
    T2 = pd.DataFrame([dict(test='persistence', mean_diagonal=diag,
                            share_runs_under_5=fr, share_bars_under_5=fb,
                            passes=bool(diag >= .9 and fb <= .05))])
    T2.to_csv(os.path.join(ROOTOUT, 'validation_summary_persistence.csv'), index=False)
    return T2


def main(skip_synth=False, skip_refit=False):
    import survivors
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    C = survivors.build(px)
    print('=' * 78)
    print('VALIDATION — is the estimator detecting anything?')
    print('=' * 78)
    parts = [test_shuffle(C, px), test_persistence(C, px)]
    if not skip_refit:
        parts.append(test_refit(px))
    if not skip_synth:
        parts.append(test_synthetic(px))
    S = pd.concat([p[['test', 'passes']] for p in parts], ignore_index=True)
    S.to_csv(os.path.join(ROOTOUT, 'validation_summary.csv'), index=False)
    print('\n' + '=' * 78)
    print('SUMMARY')
    print('=' * 78)
    print(S.to_string(index=False))
    return S


if __name__ == '__main__':
    main(skip_synth='--no-synth' in sys.argv, skip_refit='--no-refit' in sys.argv)
