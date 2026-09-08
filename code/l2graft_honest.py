import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""THE OLD GRAFT-15 AS A TEAM, ON THE HONEST STITCH. FOR THE RECORD ONLY.

W2 scored with ip1, W3 with ip2 -- the walk-forward stitch, cost-charged, equal
weight, the same overlay method as the portfolio preview, sized so DIP95 = 3.6%.

THIS IS NOT AN INPUT TO ANYTHING. The team builder no longer seeds from the
graft and does not read this file. It exists so the contaminated preview
(81.39 R, 1.75 R drawdown) has an honest number beside it.
"""
import json, time
import numpy as np, pandas as pd
import l2sweep as S
import l2tune as T
import l2crisis as C
import l2trades as TR

SEED = 20260913
N_SHUF = 10000
DIP_BUDGET = 3.6


def dip95(daily, rng):
    n = len(daily)
    if n < 3:
        return 0.0
    out = np.empty(N_SHUF); idx = np.arange(n)
    for i in range(N_SHUF):
        rng.shuffle(idx)
        eq = np.cumsum(daily[idx])
        out[i] = np.max(np.maximum.accumulate(eq) - eq)
    return float(np.percentile(out, 95))


def ip1_map(sids):
    m = {}
    for lab, f in (('B', 'gate2_tuned_modeB.csv'),
                   ('A-trend', 'gate2_tuned_modeA_trend.csv'),
                   ('A-chop', 'gate2_tuned_modeA_chop.csv')):
        p = os.path.join(ROOTOUT, f)
        if not os.path.exists(p):
            continue
        d = pd.read_csv(p, low_memory=False)
        d['sid'] = lab + '|' + d.slice + '|' + d.c1 + '|' + d.c2 + '|' + d.vol + '|' + d.base
        for r in d[d.sid.isin(sids)].to_dict('records'):
            if isinstance(r.get('ip1'), str) and isinstance(r.get('risk1'), str):
                m[r['sid']] = (r['ip1'], r['risk1'])
    rp = os.path.join(ROOTOUT, 'gate2_ip1_recovered.csv')
    if os.path.exists(rp):
        rec = pd.read_csv(rp)
        rec = rec[rec.sid != 'sid']
        for r in rec.to_dict('records'):
            m[r['sid']] = (r['ip1'], r['risk1'])
    return m


def daily_series(cfg, ip, rk, window):
    """Daily R booked on the exit date, restricted to one window."""
    a, z = S.WINDOWS[window]
    a, z = pd.Timestamp(a), pd.Timestamp(z)
    code = dict((s, c) for s, _, c in S.SLICES)[cfg['slice']]
    acc = {}
    for p in S.all_pairs():
        try:
            r = TR.run_pair(dict(cfg, ip2=json.dumps(ip),
                                 **{'risk_' + k: v for k, v in rk.items()}), p)
        except Exception:
            continue
        d, tr = r['dates'], r['trades']
        if len(tr['r']) == 0:
            continue
        reg = S.regime_codes(p, d)
        for j in range(len(tr['r'])):
            eb, xb = int(tr['entry_bar'][j]), int(tr['exit_bar'][j])
            if xb < 0 or reg[eb] != code:
                continue
            if not (a <= d[eb] <= z):
                continue
            acc[d[xb]] = acc.get(d[xb], 0.0) + float(tr['r'][j])
    return pd.Series(acc)


def main():
    t0 = time.time()
    rng = np.random.default_rng(SEED)
    S.load_costs(); T.ACCT_OBJECTIVE = True
    G = pd.read_csv(os.path.join(ROOTOUT, 'gate2_combined_AB_leaderboard.csv'),
                    low_memory=False).sort_values('rank').head(15)
    G['sid'] = G.src_label + '|' + G.slice + '|' + G.c1 + '|' + G.c2 + '|' + G.vol + '|' + G.base
    I1 = ip1_map(set(G.sid))
    print('ip1 available for %d of 15' % sum(1 for s in G.sid if s in I1), flush=True)
    series = {}
    for cfg in G.to_dict('records'):
        sid = cfg['sid']
        if sid not in I1:
            print('  SKIP (no ip1): %s' % sid[:60], flush=True); continue
        i1 = json.loads(I1[sid][0]); r1 = json.loads(I1[sid][1])
        i2 = json.loads(cfg['ip2'])
        r2 = {k: cfg['risk_' + k] for k in ('atr_len', 'atr_mult', 'tp_mult',
                                            'trail_mult', 'trail_arm', 'be_pct')}
        s2 = daily_series(cfg, i1, r1, 'W2')      # W2 under the FIRST tune
        s3 = daily_series(cfg, i2, r2, 'W3')      # W3 under the second
        s = pd.concat([s2, s3]).groupby(level=0).sum()
        if len(s):
            series['r%02d' % int(cfg['rank'])] = s
    M = pd.DataFrame(series).fillna(0.0).sort_index()
    daily = M.mean(axis=1)                        # equal weight
    D = dip95(daily.values, rng)
    eq0 = daily.cumsum()
    actual0 = float((eq0.cummax() - eq0).max())
    # bind on the WORSE of actual max drawdown and DIP95 -- the shuffle assumes
    # a random day order and so understates clustered losses
    risk0 = max(actual0, D)
    wd0 = float(-daily.min()) if daily.min() < 0 else 1e-9
    s_risk = DIP_BUDGET / risk0 if risk0 > 0 else np.nan
    s_day = 3.6 / wd0 if wd0 > 0 else np.nan
    scale = float(min(s_risk, s_day))
    binds = ('worst day' if s_day < s_risk else
             ('actual maxDD' if actual0 >= D else 'DIP95'))
    d = daily * scale
    eq = d.cumsum(); dd = float((eq.cummax() - eq).max())
    yr = d.groupby(d.index.year).sum()
    neg = d[d < 0]
    res = dict(members=M.shape[1], total_R_pct=float(d.sum()),
               max_dd_pct=dd, dip95_pct=float(D * scale),
               worst_day_pct=float(-d.min()),
               median_year_pct=float(yr.median()), mean_year_pct=float(yr.mean()),
               worst_year_pct=float(yr.min()), best_year_pct=float(yr.max()),
               sortino=float(d.mean() / neg.std(ddof=1) * np.sqrt(252)) if len(neg) > 1 else np.nan,
               calmar=float(d.sum() / dd) if dd > 0 else np.nan,
               clustering_ratio=float(actual0 / D) if D > 0 else np.nan,
               binds=binds,
               scale=scale, basis='W2(ip1)+W3(ip2) HONEST STITCH')
    pd.DataFrame([res]).to_csv(os.path.join(ROOTOUT, 'graft15_honest_book.csv'), index=False)
    yr.rename('R_pct').to_csv(os.path.join(ROOTOUT, 'graft15_honest_by_year.csv'))
    for k, v in res.items():
        print('  %-18s %s' % (k, round(v, 3) if isinstance(v, float) else v), flush=True)
    print('\nby year:'); print(yr.round(2).to_string(), flush=True)
    print('DONE in %.1f min' % ((time.time() - t0) / 60), flush=True)


if __name__ == '__main__':
    main()
