import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTDATA,exist_ok=True); os.makedirs(ROOTOUT,exist_ok=True)
sys.path.insert(0,ROOTLIB)
"""Regime evaluation framework.

  1 LOOK-AHEAD AUDIT   recompute each label from truncated data; must match exactly
  2 DURATION STATS     mean/median/min spell, n_spells, flips_faster_than_weekly
  3 THREE LOGICS       gate / switch / switch_backwards (the control)
  4 PAIRED TESTING     delta OOS Sharpe per (pair, config), sign test
  5 DSR                deflated Sharpe, Bailey & Lopez de Prado, threshold 0.95

Every regime mapping is chosen on IS (1999-2015) and applied unchanged to OOS.
Costs charged on every trade.
"""
import numpy as np, pandas as pd
from scipy import stats as st

PX = os.path.join(ROOTDATA,'/px28.csv'.lstrip('/'))
SPLIT = '2016-01-01'
MAJ = {'EURUSD', 'GBPUSD', 'AUDUSD', 'NZDUSD', 'USDCAD', 'USDCHF', 'USDJPY'}
cost = lambda p: 1.5e-4 if p in MAJ else 3.0e-4
EULER = 0.5772156649


# ---------- detectors (causal by construction) ----------
def d_trend(lp, r, hp=None):
    ma = lp.rolling(200).mean()
    return pd.Series(np.where(lp > ma, 'A', 'B'), index=lp.index).where(ma.notna())


def d_vol(lp, r, hp=None):
    v = r.rolling(60).std(); m = v.rolling(252, min_periods=252).median()
    return pd.Series(np.where(v > m, 'A', 'B'), index=lp.index).where(m.notna())


def d_naive(lp, r, hp=None):
    s = r.rolling(60).std()
    return pd.Series(np.where(r > 0.25 * s, 'A', 'B'), index=lp.index).where(s.notna())


def _fit(x, iters=50):
    q = np.nanquantile(np.abs(x), [.3, .8])
    mu = np.zeros(2); sd = np.clip(np.array([q[0], q[1]]), 1e-6, None)
    A = np.array([[.97, .03], [.06, .94]]); pi = np.array([.5, .5])
    for _ in range(iters):
        B = np.clip(np.exp(-.5 * ((x[:, None] - mu) / sd) ** 2) / (sd * np.sqrt(2 * np.pi)), 1e-300, None)
        T = len(x); al = np.zeros((T, 2)); sc = np.zeros(T)
        al[0] = pi * B[0]; sc[0] = al[0].sum(); al[0] /= sc[0]
        for t in range(1, T):
            al[t] = (al[t - 1] @ A) * B[t]; sc[t] = al[t].sum(); al[t] /= sc[t]
        be = np.zeros((T, 2)); be[-1] = 1
        for t in range(T - 2, -1, -1):
            be[t] = (A @ (B[t + 1] * be[t + 1])) / sc[t + 1]
        g = al * be; g /= g.sum(1, keepdims=True)
        xi = np.zeros((2, 2))
        for t in range(T - 1):
            m = (al[t][:, None] * A) * (B[t + 1] * be[t + 1])[None, :]; xi += m / m.sum()
        A = xi / xi.sum(1, keepdims=True); w = g.sum(0)
        mu = (g * x[:, None]).sum(0) / w
        sd = np.clip(np.sqrt((g * (x[:, None] - mu) ** 2).sum(0) / w), 1e-8, None)
        pi = g[0]
    return A, mu, sd, pi


_HP = {}


def hp_for(pair, lp, r):
    import os, pickle
    global _HP
    cf = os.path.join(ROOTLIB,'/hmmcache.pkl'.lstrip('/'))
    if not _HP and os.path.exists(cf):
        _HP = pickle.load(open(cf, 'rb'))
    if pair not in _HP:
        _HP[pair] = _fit(r[lp.index < SPLIT].fillna(0).values[1:])
        pickle.dump(_HP, open(cf, 'wb'))
    return _HP[pair]


def _filt(x, P):
    A, mu, sd, pi = P
    B = np.clip(np.exp(-.5 * ((x[:, None] - mu) / sd) ** 2) / (sd * np.sqrt(2 * np.pi)), 1e-300, None)
    a = pi * B[0]; a /= a.sum(); out = [a.copy()]
    for t in range(1, len(x)):
        a = (a @ A) * B[t]; a /= a.sum(); out.append(a.copy())
    return np.array(out)


def d_hmm(lp, r, hp):
    al = _filt(r.fillna(0).values, hp)
    calm = int(np.argmin(hp[2]))
    s = pd.Series(np.where(al[:, calm] > .5, 'A', 'B'), index=lp.index)
    s.iloc[:250] = np.nan
    return s


DETS = [('trend_sma200', d_trend), ('vol_regime', d_vol),
        ('markov_naive', d_naive), ('hmm_2state', d_hmm)]


# ---------- strategies ----------
def mr(lp, n, e):
    z = (lp - lp.rolling(n).mean()) / lp.rolling(n).std()
    p = pd.Series(np.nan, index=lp.index)
    p[z <= -e] = 1.; p[z >= e] = -1.; p[z.abs() < .1] = 0.
    return p.ffill().fillna(0.)


def mo(lp, ns, nl):
    return np.sign(lp.rolling(ns).mean() - lp.rolling(nl).mean()).fillna(0.)


CFG = [dict(id='c0', ns=10, nl=60, n=20, e=1.5), dict(id='c1', ns=20, nl=90, n=30, e=2.0),
       dict(id='c2', ns=30, nl=120, n=60, e=2.0), dict(id='c3', ns=10, nl=90, n=20, e=2.0),
       dict(id='c4', ns=20, nl=60, n=30, e=1.5)]


def sharpe(x):
    x = x.dropna()
    return np.nan if len(x) < 60 or x.std() == 0 else x.mean() / x.std() * np.sqrt(252)


# ---------- 1. LOOK-AHEAD AUDIT ----------
def lookahead_audit(px, n_checks=20, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    pairs = list(px.columns)
    for k in range(n_checks):
        p = pairs[rng.integers(len(pairs))]
        lp = np.log(px[p].astype(float)); r = lp.diff()
        hp = hp_for(p, lp, r)
        dn, df = DETS[rng.integers(len(DETS))]
        i = int(rng.integers(1200, len(lp) - 1))
        full = df(lp, r, hp)
        trunc = df(lp.iloc[:i + 1], r.iloc[:i + 1], hp)
        a, b = full.iloc[i], trunc.iloc[i]
        ok = (a == b) or (pd.isna(a) and pd.isna(b))
        rows.append(dict(ticker=p, detector=dn, idx=i, date=str(lp.index[i].date()),
                         label_full=a, label_trunc=b, PASS=ok))
    return pd.DataFrame(rows)


# ---------- 2. DURATION ----------
def duration_stats(px):
    out = []
    for dn, df in DETS:
        sp = []
        for p in px.columns:
            lp = np.log(px[p].astype(float)); r = lp.diff()
            hp = hp_for(p, lp, r) if dn == 'hmm_2state' else None
            s = df(lp, r, hp).dropna()
            if not len(s):
                continue
            grp = (s != s.shift()).cumsum()
            sp += s.groupby(grp).size().tolist()
        sp = np.array(sp)
        out.append(dict(detector=dn, mean_duration_days=sp.mean(),
                        median_duration_days=float(np.median(sp)),
                        min_duration_days=int(sp.min()), n_spells=len(sp),
                        flips_faster_than_weekly=bool(sp.mean() < 5)))
    return pd.DataFrame(out)


# ---------- 3-4. THREE LOGICS + PAIRED DELTAS ----------
def evaluate(px):
    rows = []
    for p in px.columns:
        lp = np.log(px[p].astype(float)); r = lp.diff()
        c = cost(p)
        hp = hp_for(p, lp, r)
        oos = lp.index >= SPLIT; ins = ~oos
        for cf in CFG:
            pm = mo(lp, cf['ns'], cf['nl']).shift(1).fillna(0.)
            pr = mr(lp, cf['n'], cf['e']).shift(1).fillna(0.)
            nm = pm * r - pm.diff().abs().fillna(0) * c
            nr = pr * r - pr.diff().abs().fillna(0) * c
            base = sharpe(nr[oos])
            for dn, df in DETS:
                lab = df(lp, r, hp).shift(1)
                A = (lab == 'A').values; B = (lab == 'B').values
                # mapping learned IS only
                mA = 'mo' if sharpe(nm[ins & A]) > sharpe(nr[ins & A]) else 'mr'
                mB = 'mo' if sharpe(nm[ins & B]) > sharpe(nr[ins & B]) else 'mr'
                sw = pd.Series(np.where(A, nm if mA == 'mo' else nr,
                                        np.where(B, nm if mB == 'mo' else nr, 0.)),
                               index=lp.index)
                bk = pd.Series(np.where(A, nr if mA == 'mo' else nm,
                                        np.where(B, nr if mB == 'mo' else nm, 0.)),
                               index=lp.index)
                # gate: trade MR only in whichever state was better IS
                gs = A if sharpe(nr[ins & A]) > sharpe(nr[ins & B]) else B
                gt = pd.Series(np.where(gs, nr, 0.), index=lp.index)
                for logic, ser in (('switch', sw), ('switch_backwards', bk), ('gate', gt)):
                    rows.append(dict(ticker=p, config=cf['id'], detector=dn, logic=logic,
                                     oos_sharpe=sharpe(ser[oos]), base_sharpe=base,
                                     n_obs=int(oos.sum())))
    R = pd.DataFrame(rows)
    R['delta'] = R.oos_sharpe - R.base_sharpe
    return R


def summarise(R):
    out = []
    for (d, l), g in R.groupby(['detector', 'logic']):
        x = g.delta.dropna()
        pos = (x > 0).sum()
        sgn = st.binomtest(int(pos), len(x), .5).pvalue if len(x) else np.nan
        out.append(dict(detector=d, logic=l, n_paired=len(x), mean_delta_sharpe=x.mean(),
                        median_delta_sharpe=x.median(), pct_positive=(x > 0).mean(),
                        sign_test_pvalue=sgn,
                        systematic_improvement=bool(x.mean() > 0 and sgn < .05)))
    return pd.DataFrame(out).sort_values('mean_delta_sharpe', ascending=False)


# ---------- 5. DSR ----------
def dsr(R):
    v = R.dropna(subset=['oos_sharpe'])
    N = len(v)
    sv = v.oos_sharpe.std()
    e_max = sv * ((1 - EULER) * st.norm.ppf(1 - 1 / N) + EULER * st.norm.ppf(1 - 1 / (N * np.e)))
    out = []
    for _, r in v.iterrows():
        T = r.n_obs
        sr = r.oos_sharpe / np.sqrt(252)
        z = (sr - e_max / np.sqrt(252)) * np.sqrt(T - 1)
        out.append(st.norm.cdf(z))
    v = v.copy(); v['dsr'] = out; v['dsr_pass'] = v.dsr > .95
    return v, e_max, N


if __name__ == '__main__':
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    pd.set_option('display.width', 250, 'display.max_columns', 25)
    f = lambda x: '%.4f' % x

    print('=' * 78); print('1. LOOK-AHEAD AUDIT'); print('=' * 78)
    A = lookahead_audit(px, 20, 0)
    print(A[['ticker', 'detector', 'date', 'label_full', 'label_trunc', 'PASS']].to_string(index=False))
    n_pass = int(A.PASS.sum())
    print('\n%d/%d spot-checks passed.' % (n_pass, len(A)))
    assert n_pass == len(A), 'Look-ahead detected — stop and fix before proceeding.'

    print('\n' + '=' * 78); print('2. HOW OFTEN DO REGIMES FLIP?'); print('=' * 78)
    D = duration_stats(px)
    print(D.to_string(index=False, float_format=f))
    fl = D[D.flips_faster_than_weekly]
    print('\nFlagged (avg spell < 5 days): %s' % (', '.join(fl.detector) if len(fl) else 'none'))

    print('\n' + '=' * 78); print('3-4. THREE LOGICS, PAIRED'); print('=' * 78)
    R = evaluate(px)
    S = summarise(R)
    print(S.to_string(index=False, float_format=f))

    print('\n' + '=' * 78); print('5. DSR MULTIPLE-TESTING'); print('=' * 78)
    V, emax, N = dsr(R)
    print('variants tested %d | expected max Sharpe under null %.3f | DSR>0.95: %d'
          % (N, emax, int(V.dsr_pass.sum())))

    b = S.iloc[0]
    ns = int(S[S.logic == 'switch'].systematic_improvement.sum())
    ng = int(S[S.logic == 'gate'].systematic_improvement.sum())
    print('\n' + '=' * 78); print('HEADLINE'); print('=' * 78)
    print('Best cell: %s / %s -> mean OOS Sharpe delta %+.3f across %d paired draws, '
          '%.0f%% positive, sign-test p=%.1e' % (b.detector, b.logic, b.mean_delta_sharpe,
                                                 b.n_paired, 100 * b.pct_positive, b.sign_test_pvalue))
    print('SWITCH logic: systematic improvement in %d/4 detectors.' % ns)
    print('GATE   logic: systematic improvement in %d/4 detectors.' % ng)
    print('After DSR correction: %d/%d individual variants survive (threshold 0.95).'
          % (int(V.dsr_pass.sum()), N))
    R.to_csv(os.path.join(ROOTOUT,'/logic_results.csv'.lstrip('/')), index=False)
    S.to_csv(os.path.join(ROOTOUT,'/logic_summary.csv'.lstrip('/')), index=False)
    D.to_csv(os.path.join(ROOTOUT,'/duration_stats.csv'.lstrip('/')), index=False)
    A.to_csv(os.path.join(ROOTOUT,'/lookahead_audit.csv'.lstrip('/')), index=False)
