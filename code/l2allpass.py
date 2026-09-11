import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""ALLPASS — the NO-SEARCH construction.

WHY THIS EXISTS. The greedy roster search failed its selection holdout: a roster
picked on 2016-2018 kept 8% of its score on 2019-2020. The fault is in the
SELECTION, not in the passers. So this construction removes the selection
entirely: every gate 3 passer is in, at equal weight, in the order the cut
produced them. There is nothing to fit, because nothing was chosen.

WHAT IS STILL FITTED, and must therefore be tested. The CUT itself saw
2016-2020, so "which strategies passed" is an in-sample decision even though
each strategy's settings were fixed beforehand. The honest holdout here re-runs
the CUT on 2016-2018 only, builds ALLPASS from whatever passes THAT, and scores
it on 2019-2020. That is the analogue of the roster holdout for a construction
with no roster.

COSTS ARE CHARGED HERE, AND WERE NOT CHARGED BEFORE. l2trades.run_pair calls
the engine directly and returns GROSS R -- only l2sweep.score_combo and
l2tune.Scorer subtract S._cost_R. Every delivery-side number built on run_pair
(blind_trades, l2team._equity_series, l2layer4v2.marks, and therefore the team
KPIs and the Layer 4 levels) is gross of costs. Measured on five passers the
drag is 2.6%-8.5% of gross R. This module charges the cost on the ENTRY day's
mark and reports the gross book beside the net one so the gap is visible.

THE YEAR-SHUFFLED NULL IS REBUILT. l2teamcheck's null permutes calendar years
with ONE permutation applied to the whole matrix, so every member moves
together: each member's daily series, every cross-member same-day alignment and
every yearly sum survive intact, and the median year -- the score -- is
arithmetically unchanged. Only the path-dependent max drawdown moves. Verified
on synthetic data: real yearly sums [2.1511 0.6611 2.4805 1.9284 2.4635], null
yearly sums the same five numbers reordered. That null cannot detect anything.
The null here permutes each MEMBER'S years INDEPENDENTLY, which is what the
docstring over there describes: each member keeps its own distribution and its
own yearly totals, while cross-member timing is destroyed. Both nulls are run
and both are reported.
"""
import json, glob, time, argparse, pickle
import numpy as np, pandas as pd

import l2sweep as S
import l2crisis as C
import l2trades as TR
import l2team as TM
import l2gate3 as G3

BARS = G3.BARS
ZERO_ALONE = ('kuskus_starlight', 'volatility_quality')
CURVES = {'curve': {1: 1.0, 2: 3.0, 3: 6.0}, 'half': {1: 1.0, 2: 2.0, 3: 3.0}}
BUDGETS = (('team1', 3.6, 3.6), ('team2', 5.4, 3.6))
CAP_PCT = 2.0
SEED = 20260910

# sub-windows for the honest holdout. W3 = 2016-2020; the cut saw all of it.
SUBWIN = {'H1': ('2016-01-01', '2018-12-31'), 'H2': ('2019-01-01', '2020-12-31')}
RISK_KEYS = ('atr_len', 'atr_mult', 'tp_mult', 'trail_mult', 'trail_arm', 'be_pct')


def sized(level, mode):
    if level <= 0:
        return 0.0
    if mode == 'linear':
        return float(level)
    return CURVES[mode][min(level, 3)]


# ----------------------------------------------------------------- marks
_WIN = None


def _init(win):
    global _WIN
    S.load_costs()
    _WIN = win


def marks_one(cfg):
    """One member's daily mark-to-market, per pair, over the given windows.

    The cost is charged once, on the ENTRY day, in the same R units the engine
    uses -- so the marks sum to (realised R - cost), which is what the account
    sees. Gross is carried alongside so the drag can be measured.
    """
    code = dict((s, c) for s, _, c in S.SLICES)[cfg['slice']]
    sid = cfg['sid']
    za = any(z in str(sid) for z in ZERO_ALONE)
    rows = []
    for p in S.all_pairs():
        r = TR.run_pair(cfg, p)
        d, tr, cl = r['dates'], r['trades'], r['c']
        if len(tr['r']) == 0:
            continue
        reg = S.regime_codes(p, d)
        wb = {}
        for k, (a, z) in _WIN.items():
            w = np.flatnonzero((d >= a) & (d <= z))
            if len(w):
                wb[k] = (int(w[0]), int(w[-1]) + 1)
        if not wb:
            continue
        dv = d.values
        for j in range(len(tr['r'])):
            eb, xb = int(tr['entry_bar'][j]), int(tr['exit_bar'][j])
            if xb < 0 or reg[eb] != code:
                continue
            zz = None
            for k in _WIN:
                b = wb.get(k)
                if b and b[0] <= eb < b[1]:
                    zz = b[1] - 1
            if zz is None:
                continue
            ent = float(tr['entry_px'][j]); u = float(tr['units'][j])
            sgn = float(tr['dir'][j]); tot = float(tr['r'][j])
            cst = float(S._cost_R(p, np.array([ent]), np.array([u]),
                                  np.array([dv[eb]]))[0])
            end = min(xb, zz)          # mark to market at the window boundary
            prev = 0.0
            for b in range(eb, end + 1):
                cum = tot if (b == xb and xb <= zz) else sgn * (cl[b] - ent) * u / S.RISK
                mk = cum - prev
                rows.append((sid, p, d[b], int(sgn), mk - (cst if b == eb else 0.0),
                             mk, za))
                prev = cum
    return rows


def build_marks(field, win, jobs):
    import multiprocessing as mp
    recs = field.to_dict('records')
    t = time.time()
    if jobs > 1 and len(recs) > 4:
        with mp.Pool(jobs, initializer=_init, initargs=(win,)) as pool:
            got = pool.map(marks_one, recs, chunksize=2)
    else:
        _init(win)
        got = [marks_one(r) for r in recs]
    rows = [x for g in got for x in g]
    M = pd.DataFrame(rows, columns=['sid', 'pair', 'day', 'dir', 'mark',
                                    'mark_gross', 'za'])
    M['day'] = pd.to_datetime(M.day)
    print('  marks: %d rows, %d members, %d days, %.1f min'
          % (len(M), M.sid.nunique(), M.day.nunique(), (time.time() - t) / 60),
          flush=True)
    return M


# ----------------------------------------------------------------- netting
def net_positions(M, mode, col='mark'):
    """Net every member's mark per pair per day, size by agreement level.

    A ZERO_ALONE member counts as zero when it is the only one on that side of
    that pair that day -- it earns nothing alone and is kept only for the
    confirmation it adds.
    """
    g = M
    cnt = g.groupby(['pair', 'day', 'dir'], sort=False)['sid'].transform('size')
    c = np.where(g['za'].values & (cnt.values == 1), 0.0, 1.0)
    side = (g.assign(_c=c)
             .groupby(['pair', 'day', 'dir'], sort=False)
             .agg(n=('_c', 'sum'), mk=(col, 'mean')).reset_index())
    L = (side[side.dir == 1].set_index(['pair', 'day'])[['n', 'mk']]
         .rename(columns={'n': 'nl', 'mk': 'ml'}))
    Sh = (side[side.dir == -1].set_index(['pair', 'day'])[['n', 'mk']]
          .rename(columns={'n': 'ns', 'mk': 'ms'}))
    J = L.join(Sh, how='outer').fillna(0.0).reset_index()
    net = (J.nl - J.ns).values
    keep = np.abs(net) >= 0.5
    J = J[keep]; net = net[keep]
    lvl = np.abs(net).round().astype(int)
    sgn = np.where(net > 0, 1, -1)
    sz = np.array([sized(int(x), mode) for x in lvl])
    mk = np.where(sgn > 0, J.ml.values, J.ms.values)
    B = pd.DataFrame(dict(pair=J.pair.values, day=J.day.values, level=lvl,
                          size=sz, dir=sgn, mark=mk))
    B = B[B['size'] > 0].reset_index(drop=True)
    if not len(B):
        raise RuntimeError('netting produced no positions for %r' % mode)
    B['pnl'] = B['mark'] * B['size']
    return B


def _series(B):
    s = B.groupby('day').pnl.sum().sort_index()
    den = float(B.groupby('day')['size'].sum().mean()) or 1.0
    return s / den


def _scale_of(s, dipb, dayb, rng):
    D = TM.dip95(s.values, rng=rng)
    eq = s.cumsum(); adj = float((eq.cummax() - eq).max())
    wd = float(-s.min()) if s.min() < 0 else 1e-9
    return float(min(dipb / max(adj, D) if max(adj, D) > 0 else np.inf,
                     dayb / wd if wd > 0 else np.inf))


def build_book(M, mode, cap_pct, dipb, dayb, col='mark'):
    """Returns (daily series, cap-bound day count, worst currency exposure, B).

    mode='stacked' is the equal-weight reference: every member's mark summed and
    divided by the member count, no netting and no cap.
    """
    if mode == 'stacked':
        n = M.sid.nunique()
        return M.groupby('day')[col].sum().sort_index() / n, 0, np.nan, None
    B = net_positions(M, mode, col=col)
    # the cap is a % of EQUITY, so it needs the scale the budget implies.
    s0 = _scale_of(_series(B), dipb, dayb, np.random.default_rng(7))
    den0 = float(B.groupby('day')['size'].sum().mean()) or 1.0
    per_unit = s0 / den0
    bc = B.pair.str[:3].values; qc = B.pair.str[3:].values
    legs = pd.DataFrame(dict(
        day=np.concatenate([B.day.values, B.day.values]),
        ccy=np.concatenate([bc, qc]),
        sdir=np.concatenate([B.dir.values, -B.dir.values]),
        size=np.concatenate([B['size'].values, B['size'].values])))
    expo = legs.groupby(['day', 'ccy', 'sdir'], sort=False)['size'].sum()
    mx = expo.groupby(level=0).max()
    worst = float((mx * per_unit).max())
    binds = 0
    if cap_pct is not None:
        over = (mx * per_unit) > cap_pct
        binds = int(over.sum())
        f = pd.Series(1.0, index=mx.index)
        f[over] = cap_pct / (mx[over] * per_unit)
        fac = B.day.map(f).values
        B = B.assign(size=B['size'].values * fac, pnl=B.pnl.values * fac)
    return _series(B), binds, worst, B


def kpis(d, dipb, dayb, npos):
    D = TM.dip95(d.values, rng=np.random.default_rng(11))
    eq = d.cumsum(); adj = float((eq.cummax() - eq).max())
    wd = float(-d.min()) if d.min() < 0 else 1e-9
    s_risk = dipb / max(adj, D) if max(adj, D) > 0 else np.inf
    s_day = dayb / wd if wd > 0 else np.inf
    scale = float(min(s_risk, s_day))
    binds = 'worst day' if s_day < s_risk else ('actual maxDD' if adj >= D else 'DIP95')
    x = d * scale; e = x.cumsum()
    yr = x.groupby(x.index.year).sum()
    mon = x.groupby([x.index.year, x.index.month]).sum()
    neg = x[x < 0]
    dd = float((e.cummax() - e).max())
    return dict(median_year_pct=float(yr.median()), mean_year_pct=float(yr.mean()),
                worst_year_pct=float(yr.min()), best_year_pct=float(yr.max()),
                total_return_pct=float(x.sum()), max_dd_pct=dd,
                dip95_pct=float(D * scale), worst_day_pct=float(-x.min()),
                worst_month_pct=float(-mon.min()),
                clustering_ratio=float(adj / D) if D > 0 else np.nan,
                sortino=float(x.mean() / neg.std(ddof=1) * np.sqrt(252)) if len(neg) > 1 else np.nan,
                sharpe=float(x.mean() / x.std(ddof=1) * np.sqrt(252)) if x.std(ddof=1) > 0 else np.nan,
                calmar=float(x.sum() / dd) if dd > 0 else np.nan,
                profit_factor=float(x[x > 0].sum() / -x[x < 0].sum()) if (x < 0).any() else np.inf,
                win_rate_pct=float(100 * (x > 0).mean()),
                n_years=int(len(yr)), trading_days=int(len(x)), max_positions=npos,
                scale=scale, binds=binds)


def score_only(M, mode, cap_pct, dipb, dayb, col='mark'):
    d, binds, wex, B = build_book(M, mode, cap_pct, dipb, dayb, col=col)
    npos = int(B.groupby('day').size().max()) if B is not None else int(
        M.groupby('day').size().max())
    k = kpis(d, dipb, dayb, npos)
    k.update(cap_bound_days=binds, max_ccy_exposure_pct=wex)
    return k, d, B


# ----------------------------------------------------------------- the field
def adopted_map():
    fs = sorted(glob.glob(os.path.join(ROOTOUT, 'gate3ft_costed_v4', '*.csv')))
    parts, bad = [], 0
    for f in fs:
        try:
            parts.append(pd.read_csv(f, low_memory=False))
        except Exception:
            bad += 1
    if bad:
        print('  WARNING: %d of %d bank files unreadable' % (bad, len(fs)), flush=True)
    if not parts:
        return {}
    d = pd.concat(parts, ignore_index=True)
    d = d[(d.get('compare_basis') == 'W3ONLY') & (d.adopted == True)]
    return {r['sid']: r for r in d.drop_duplicates('sid', keep='last').to_dict('records')}


def load_field_adopted():
    """Every gate-2 crosser, carrying ADOPTED settings where one exists.

    Same substitution l2cut performs, applied to the SETTINGS only -- the
    metrics are recomputed here from the engine rather than inherited, because
    the holdout needs them per sub-window and the bank has only the full W3.
    """
    fs = sorted(glob.glob(os.path.join(ROOTOUT, 'gate2_w3only_scores_*.csv')))
    D = pd.concat([pd.read_csv(f, low_memory=False) for f in fs], ignore_index=True)
    D = D[D.sid != 'sid'].drop_duplicates('sid').reset_index(drop=True)
    AD = adopted_map()
    n = 0
    for i, sid in enumerate(D.sid.values):
        r = AD.get(sid)
        if r is None:
            continue
        n += 1
        for k in RISK_KEYS:
            if 'ft_risk_' + k in r and r['ft_risk_' + k] == r['ft_risk_' + k]:
                D.at[i, 'risk_' + k] = r['ft_risk_' + k]
        if isinstance(r.get('ft_ip2'), str):
            D.at[i, 'ip2'] = r['ft_ip2']
    print('  field %d crossers, adopted settings on %d' % (len(D), n), flush=True)
    return D


_SC = None


def _init_sc(subwin):
    global _SC
    import l2tune as T
    S.WINDOWS = dict(S.WINDOWS); S.WINDOWS.update(subwin)
    S.load_costs(); T.ACCT_OBJECTIVE = True
    _SC = T.Scorer()


def score_one(cfg):
    """Costed metrics on W3 and on each sub-window, through l2tune.Scorer --
    the exact path that produced the banked w3_* columns, so the full-window
    control reproduces the real cut rather than approximating it."""
    try:
        sn = cfg['slice']
        code = dict((s, c) for s, _, c in S.SLICES)[sn]
        plan = dict((s, p) for s, p, _ in S.SLICES)[sn]
        ip = json.loads(cfg['ip2'])
        rk = {k: cfg['risk_' + k] for k in RISK_KEYS}
        combo = (cfg['c1'], cfg['c2'], cfg['vol'], cfg['base'], cfg['exit_ind'])
        g = _SC.score(combo, ip, rk, cfg['src_mode'], sn, code, plan,
                      ('W3',) + tuple(SUBWIN))
    except Exception as e:
        return dict(sid=cfg['sid'], err=type(e).__name__ + ': ' + str(e)[:80])
    row = dict(sid=cfg['sid'], err='')
    for w in ('W3',) + tuple(SUBWIN):
        a = g.get(w)
        for k in ('n', 'total_R', 'expectancy_R', 'profit_factor', 'sharpe',
                  'sortino', 'calmar', 'max_dd_R', 'win_rate', 'avg_win_R'):
            row['%s_%s' % (w.lower(), k)] = None if a is None else a.get(k)
    return row


def apply_bars(D, pre):
    """The gate 3 cut's binding bars, on whichever window `pre` names."""
    g = D['%s_avg_win_R' % pre] * D['%s_win_rate' % pre] * D['%s_n' % pre]
    frac = D['%s_max_dd_R' % pre] / g.replace(0, np.nan)
    ok = pd.Series(True, index=D.index)
    fails = {}
    for k, v in BARS.items():
        col = frac if k == 'max_dd_frac' else D['%s_%s' % (pre, k)]
        good = (col <= v) if k == 'max_dd_frac' else (col >= v)
        good = good.fillna(False)
        fails[k] = int((~good).sum())
        ok &= good
    return ok, fails


# ----------------------------------------------------------------- nulls
def year_grid(days):
    """Canonical year x position grid, truncated to the shortest year so every
    year block is swappable with every other."""
    s = pd.Series(days).drop_duplicates().sort_values().reset_index(drop=True)
    by = {}
    for y, g in s.groupby(s.dt.year):
        by[y] = list(g.values)
    Ln = min(len(v) for v in by.values())
    ys = sorted(by)
    grid = {y: by[y][:Ln] for y in ys}
    pos = {}
    for y in ys:
        for i, d in enumerate(grid[y]):
            pos[d] = (y, i)
    return ys, Ln, grid, pos


class Shuffler:
    """Pre-resolves every row to (member, year-slot, position-in-year) ONCE, so
    a draw is two array lookups instead of a groupby."""

    def __init__(self, M):
        self.ys, self.Ln, self.grid, pos = year_grid(M.day)
        yp = np.array([pos.get(d, (-1, -1))[0] for d in M.day.values])
        ip = np.array([pos.get(d, (-1, -1))[1] for d in M.day.values])
        keep = ip >= 0
        self.X = M[keep].reset_index(drop=True)
        yidx = {y: i for i, y in enumerate(self.ys)}
        self.src = np.array([yidx[y] for y in yp[keep]])
        self.ip = ip[keep]
        self.codes, self.uniq = pd.factorize(self.X.sid.values)
        self.gridarr = np.array([self.grid[y] for y in self.ys])
        self.dropped = int((~keep).sum())

    def real(self):
        return self.X

    def draw(self, rng, joint):
        """joint=True  ONE permutation for every member -- l2teamcheck's null.
        Every cross-member same-day alignment survives; only the order of the
        year blocks changes, so each member's daily series and every yearly sum
        are untouched and the median year cannot move.

        joint=False a fresh permutation PER MEMBER. Each member keeps its own
        daily values and its own yearly totals; cross-member timing is gone.
        That is the null the team check's docstring describes and its code does
        not implement."""
        ny = len(self.ys); nm = len(self.uniq)
        if joint:
            pm = np.tile(rng.permutation(ny), (nm, 1))
        else:
            pm = np.array([rng.permutation(ny) for _ in range(nm)])
        newy = pm[self.codes, self.src]
        Y = self.X.copy()
        Y['day'] = self.gridarr[newy, self.ip]
        return Y


def _cap_and_score(B, cap_pct, dipb, dayb):
    """Currency cap + KPIs on an already-netted book. Split out so a null can
    replace the LEVELS without re-running the netting."""
    s0 = _scale_of(_series(B), dipb, dayb, np.random.default_rng(7))
    den0 = float(B.groupby('day')['size'].sum().mean()) or 1.0
    per_unit = s0 / den0
    bc = B.pair.str[:3].values; qc = B.pair.str[3:].values
    legs = pd.DataFrame(dict(
        day=np.concatenate([B.day.values, B.day.values]),
        ccy=np.concatenate([bc, qc]),
        sdir=np.concatenate([B.dir.values, -B.dir.values]),
        size=np.concatenate([B['size'].values, B['size'].values])))
    mx = legs.groupby(['day', 'ccy', 'sdir'], sort=False)['size'].sum().groupby(level=0).max()
    if cap_pct is not None:
        over = (mx * per_unit) > cap_pct
        f = pd.Series(1.0, index=mx.index)
        f[over] = cap_pct / (mx[over] * per_unit)
        fac = B.day.map(f).values
        B = B.assign(size=B['size'].values * fac, pnl=B.pnl.values * fac)
    d = _series(B)
    return kpis(d, dipb, dayb, int(B.groupby('day').size().max()))


def run_level_null(M, mode, cap_pct, dipb, dayb, n, tag):
    """DOES THE AGREEMENT CURVE EARN ITS SIZE?

    The year shuffles above test the book's timing. This one tests the SIZING
    rule and nothing else: the netted positions, their pairs, their days, their
    directions and their marks are all left exactly as they are, and only the
    AGREEMENT LEVELS are permuted across positions. The level distribution, and
    therefore the mix of sizes in the book, is identical. If 1/3/6 is extracting
    something real, the true level-to-position assignment must beat a random
    one; if it is decoration, it will not.
    """
    B0 = net_positions(M, mode)
    real = _cap_and_score(B0.copy(), cap_pct, dipb, dayb)
    rng = np.random.default_rng(SEED + 1)
    rows = [dict(kind='real', draw=-1, score=real['median_year_pct'])]
    for i in range(n):
        B = B0.copy()
        B['level'] = rng.permutation(B0.level.values)
        B['size'] = np.array([sized(int(x), mode) for x in B.level])
        B['pnl'] = B['mark'] * B['size']
        k = _cap_and_score(B, cap_pct, dipb, dayb)
        rows.append(dict(kind='null_levels', draw=i, score=k['median_year_pct']))
        if (i + 1) % 20 == 0:
            print('    %s level null %d/%d  last %.3f%%'
                  % (tag, i + 1, n, rows[-1]['score']), flush=True)
    return pd.DataFrame(rows), real


def run_nulls(M, mode, cap_pct, dipb, dayb, n, tag):
    sh = Shuffler(M)
    rng = np.random.default_rng(SEED)
    real, _, _ = score_only(sh.real(), mode, cap_pct, dipb, dayb)
    rows = [dict(kind='real_truncated', draw=-1, score=real['median_year_pct'],
                 max_dd_pct=real['max_dd_pct'], scale=real['scale'])]
    print('    %s: %d rows on the truncated calendar (%d dropped), real %.3f%%'
          % (tag, len(sh.X), sh.dropped, real['median_year_pct']), flush=True)
    for joint in (True, False):
        lbl = 'null_joint' if joint else 'null_per_member'
        for i in range(n):
            try:
                k, _, _ = score_only(sh.draw(rng, joint), mode, cap_pct, dipb, dayb)
            except Exception:
                continue
            rows.append(dict(kind=lbl, draw=i, score=k['median_year_pct'],
                             max_dd_pct=k['max_dd_pct'], scale=k['scale']))
            if (i + 1) % 20 == 0:
                print('    %s %s %d/%d  last %.3f%%'
                      % (tag, lbl, i + 1, n, rows[-1]['score']), flush=True)
    return pd.DataFrame(rows), real


# ----------------------------------------------------------------- stages
W3 = {'W3': S.WINDOWS['W3']}
MARKS_F = os.path.join(ROOTOUT, 'allpass_marks.pkl')
FIELD_F = os.path.join(ROOTOUT, 'allpass_field_subwindow_scores.csv')


def stage_build(jobs):
    """ALLPASS on the real cut: all 252 passers, equal weight, both budgets."""
    V = pd.read_csv(os.path.join(ROOTOUT, 'gate3_costed_verdicts.csv'), low_memory=False)
    V = V[V.verdict.isin(['PASS', 'SELECTIVE'])].reset_index(drop=True)
    print('ALLPASS field: %d passers (%s), basis %s'
          % (len(V), V.src_label.value_counts().to_dict(),
             sorted(V.settings_basis.unique())), flush=True)
    M = build_marks(V, W3, jobs)
    M.to_pickle(MARKS_F)
    rows, ser = [], {}
    for bt, dipb, dayb in BUDGETS:
        for tag, mode, cap in (('A_stacked', 'stacked', None),
                               ('C_netted_curve', 'curve', CAP_PCT)):
            for col, cl in (('mark', 'net_of_costs'), ('mark_gross', 'gross')):
                k, d, B = score_only(M, mode, cap, dipb, dayb, col=col)
                k.update(book=tag, mode=mode, budget=bt, costs=cl, members=len(V),
                         cap_pct=cap, dip_budget=dipb, day_budget=dayb)
                rows.append(k)
                if cl == 'net_of_costs':
                    ser['%s|%s' % (bt, tag)] = d
                    if B is not None and bt == 'team1':
                        lv = (B.groupby('level').size().rename('position_days')
                              .reset_index())
                        lv['share_pct'] = 100.0 * lv.position_days / lv.position_days.sum()
                        lv['size'] = [sized(int(x), mode) for x in lv.level]
                        lv.to_csv(os.path.join(ROOTOUT, 'allpass_levels.csv'), index=False)
                print('  %-6s %-15s %-12s median %7.3f%%  worst %7.3f%%  maxDD %5.2f%%  '
                      'PF %.2f  cap-bound %s  max expo %s'
                      % (bt, tag, cl, k['median_year_pct'], k['worst_year_pct'],
                         k['max_dd_pct'], k['profit_factor'], k['cap_bound_days'],
                         'n/a' if k['max_ccy_exposure_pct'] != k['max_ccy_exposure_pct']
                         else '%.2f%%' % k['max_ccy_exposure_pct']), flush=True)
    O = pd.DataFrame(rows)
    O.to_csv(os.path.join(ROOTOUT, 'allpass_kpis.csv'), index=False)
    pd.DataFrame(ser).to_csv(os.path.join(ROOTOUT, 'allpass_daily.csv'))
    return M, O


def stage_field(jobs):
    """Re-score every crosser on W3 and on both sub-windows, costed."""
    import multiprocessing as mp
    D = load_field_adopted()
    recs = D.to_dict('records')
    t = time.time()
    with mp.Pool(jobs, initializer=_init_sc, initargs=(SUBWIN,)) as pool:
        got = pool.map(score_one, recs, chunksize=8)
    R = pd.DataFrame(got)
    R = D[['sid', 'src_label', 'src_mode', 'slice', 'c1', 'c2', 'vol', 'base',
           'exit_ind', 'ip2'] + ['risk_' + k for k in RISK_KEYS]].merge(R, on='sid')
    R.to_csv(FIELD_F, index=False)
    bad = int((R.err != '').sum())
    print('  field re-score: %d rows, %d errors, %.1f min'
          % (len(R), bad, (time.time() - t) / 60), flush=True)
    return R


def stage_holdout(jobs):
    """RE-CUT ON 2016-2018 ONLY, construct from those passers, score 2019-2020."""
    R = pd.read_csv(FIELD_F, low_memory=False)
    V = pd.read_csv(os.path.join(ROOTOUT, 'gate3_costed_verdicts.csv'), low_memory=False)
    real_sids = set(V.sid)
    out = {}
    ok3, f3 = apply_bars(R, 'w3')
    ctrl = set(R[ok3].sid)
    out['control_w3_passers'] = int(len(ctrl))
    out['control_overlap_with_real_cut'] = int(len(ctrl & real_sids))
    out['real_cut_passers'] = int(len(real_sids))
    out['control_fails_by_bar'] = f3
    print('  control: re-cutting on the FULL W3 through this path gives %d passers, '
          '%d of them in the real cut of %d'
          % (len(ctrl), len(ctrl & real_sids), len(real_sids)), flush=True)
    ok1, f1 = apply_bars(R, 'h1')
    P = R[ok1].reset_index(drop=True)
    out['holdout_cut_passers'] = int(len(P))
    out['holdout_fails_by_bar'] = f1
    out['holdout_overlap_with_real_cut'] = int(len(set(P.sid) & real_sids))
    print('  re-cut on 2016-2018: %d passers (%d also in the real cut)'
          % (len(P), len(set(P.sid) & real_sids)), flush=True)
    P.to_csv(os.path.join(ROOTOUT, 'allpass_holdout_cut.csv'), index=False)
    if not len(P):
        json.dump(out, open(os.path.join(ROOTOUT, 'allpass_holdout.json'), 'w'), indent=1)
        return out
    MH = build_marks(P, dict(SUBWIN), jobs)
    MH.to_pickle(os.path.join(ROOTOUT, 'allpass_holdout_marks.pkl'))
    M = pd.read_pickle(MARKS_F)
    h1 = (MH.day >= SUBWIN['H1'][0]) & (MH.day <= SUBWIN['H1'][1])
    h2 = (MH.day >= SUBWIN['H2'][0]) & (MH.day <= SUBWIN['H2'][1])
    r1 = (M.day >= SUBWIN['H1'][0]) & (M.day <= SUBWIN['H1'][1])
    r2 = (M.day >= SUBWIN['H2'][0]) & (M.day <= SUBWIN['H2'][1])
    rows = []
    for bt, dipb, dayb in BUDGETS:
        for tag, mode, cap in (('C_netted_curve', 'curve', CAP_PCT),
                               ('A_stacked', 'stacked', None)):
            for lbl, X in (('holdout_cut_on_2016_2018', MH[h1]),
                           ('holdout_cut_on_2019_2020', MH[h2]),
                           ('real_cut_on_2016_2018', M[r1]),
                           ('real_cut_on_2019_2020', M[r2])):
                k, _, _ = score_only(X, mode, cap, dipb, dayb)
                k.update(book=tag, budget=bt, leg=lbl,
                         members=int(X.sid.nunique()))
                rows.append(k)
    H = pd.DataFrame(rows)
    H.to_csv(os.path.join(ROOTOUT, 'allpass_holdout_kpis.csv'), index=False)
    for bt, _, _ in BUDGETS:
        q = H[(H.budget == bt) & (H.book == 'C_netted_curve')].set_index('leg')
        a = q.loc['holdout_cut_on_2016_2018', 'median_year_pct']
        b = q.loc['holdout_cut_on_2019_2020', 'median_year_pct']
        c = q.loc['real_cut_on_2019_2020', 'median_year_pct']
        out['%s_pick_window' % bt] = float(a)
        out['%s_holdout' % bt] = float(b)
        out['%s_retained_pct' % bt] = float(100.0 * b / a) if a else None
        out['%s_real_cut_on_holdout' % bt] = float(c)
        print('  %s  pick window %.2f%%  ->  holdout %.2f%%  retained %.0f%%  '
              '(real cut on the same holdout %.2f%%)'
              % (bt, a, b, 100.0 * b / a if a else float('nan'), c), flush=True)
    json.dump(out, open(os.path.join(ROOTOUT, 'allpass_holdout.json'), 'w'),
              indent=1, default=str)
    return out


def stage_null(n):
    M = pd.read_pickle(MARKS_F)
    frames = []
    for bt, dipb, dayb in BUDGETS:
        N, real = run_nulls(M, 'curve', CAP_PCT, dipb, dayb, n, bt)
        N['budget'] = bt
        frames.append(N)
        LN, lreal = run_level_null(M, 'curve', CAP_PCT, dipb, dayb, n, bt)
        LN['budget'] = bt
        LN.loc[LN.kind == 'real', 'kind'] = 'real_levels'
        frames.append(LN)
    N = pd.concat(frames, ignore_index=True)
    N.to_csv(os.path.join(ROOTOUT, 'allpass_null.csv'), index=False)
    summ = []
    for bt in N.budget.unique():
        q = N[N.budget == bt]
        real = float(q[q.kind == 'real_truncated'].score.iloc[0])
        for kind in ('null_joint', 'null_per_member', 'null_levels'):
            if kind == 'null_levels':
                real = float(q[q.kind == 'real_levels'].score.iloc[0])
            v = q[q.kind == kind].score.values
            if not len(v):
                continue
            summ.append(dict(budget=bt, null=kind, real=real, n=len(v),
                             mean=float(v.mean()), p95=float(np.percentile(v, 95)),
                             max=float(v.max()),
                             p_value=float((v >= real).mean()),
                             p_resolution=round(1.0 / len(v), 3)))
            print('  %-6s %-16s real %7.3f%%  null mean %7.3f%%  p95 %7.3f%%  '
                  'max %7.3f%%  p=%.3f' % (bt, kind, real, v.mean(),
                                           np.percentile(v, 95), v.max(),
                                           (v >= real).mean()), flush=True)
    pd.DataFrame(summ).to_csv(os.path.join(ROOTOUT, 'allpass_null_summary.csv'), index=False)
    return pd.DataFrame(summ)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', default='all',
                    choices=['all', 'build', 'field', 'holdout', 'null'])
    ap.add_argument('--jobs', type=int, default=int(os.environ.get('ALLPASS_JOBS', '4')))
    ap.add_argument('--n-null', type=int, default=100)
    a = ap.parse_args()
    t0 = time.time(); S.load_costs()
    if a.stage in ('all', 'build'):
        print('== STAGE 1  ALLPASS construction ==', flush=True); stage_build(a.jobs)
    if a.stage in ('all', 'field'):
        print('== STAGE 2  field re-score on sub-windows ==', flush=True); stage_field(a.jobs)
    if a.stage in ('all', 'holdout'):
        print('== STAGE 3  honest holdout ==', flush=True); stage_holdout(a.jobs)
    if a.stage in ('all', 'null'):
        print('== STAGE 4  year-shuffled nulls ==', flush=True); stage_null(a.n_null)
    print('DONE in %.1f min' % ((time.time() - t0) / 60), flush=True)


if __name__ == '__main__':
    main()
