import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""WALK-FORWARD TEAM STRUCTURES on the three slices that have ip1.

THE STITCH. W2 (2011-2015) is scored with ip1, W3 (2016-2020) with ip2. ip1 was
tuned on W1 and has never seen W2; ip2 was tuned on W1+W2 and has never seen W3.
Every year here is therefore blind under the parameters it is scored with.
W1 (2005-2010) is NOT used: it is ip1's own tuning window, so build metrics
taken there would be in-sample in exactly the way this design exists to avoid.
The build windows are the clean part of "2005-2015" and "2005-2018".

    step 1   build 2011-2015 (ip1)                  trade 2016-2018 (ip2)
    step 2   build 2011-2015 (ip1) + 2016-2018 (ip2) trade 2019-2020 (ip2)

At each step the cut, the member choice, the agreement curve and the SIZE are
all decided on the build years and applied to the trade years untouched. The two
trade stretches are stitched into one 2016-2020 record.

SLICES. A-trend, A-chop and B-chop bank ip1 (1,804 + 678 + 1,003 = 3,485).
B-trend never did — `--slices` and the ip1 fallback to
`results/gate2_ip1_recovered.csv` are what let the cloud recovery be dropped in
and the whole run repeated unchanged. Mode C is paused and is not included.

TWO CONVENTIONS ARE FIXED HERE THAT THE DELIVERY PATH GETS WRONG.

1. COSTS. `l2trades.run_pair` returns GROSS R; only `l2sweep.score_combo` and
   `l2tune.Scorer` subtract `S._cost_R`. Charged here, on the entry day.
2. ACCOUNT-NORMALISED R. Engine R scales as 1/atr_mult, so a strategy with a
   tighter stop books more R for the same price move and would silently carry
   more weight in an equal-weighted book. `l2tune` multiplies by atr_mult to
   restate everything against a fixed 1.0xATR risk unit; the delivery path never
   did. Applied here to marks as well as to trade R, so the cut and the book
   speak the same units. Cost is subtracted AFTER the restatement, exactly as
   the Scorer does it.

MARK-TO-MARKET BY TRUNCATION. Marks are daily INCREMENTS, so summing the
increments that fall inside a window is already the change in value over the
in-window part of the position. Truncating to a window IS marking to its
boundary; nothing is re-marked and no trade carries profit out of a window.
"""
import json, glob, time, argparse
import numpy as np, pandas as pd

import scipy.sparse as sp

import l2sweep as S
import l2trades as TR

RISK_KEYS = ('atr_len', 'atr_mult', 'tp_mult', 'trail_mult', 'trail_arm', 'be_pct')
ERAS = {'ip1': ('2011-01-01', '2015-12-31'), 'ip2': ('2016-01-01', '2020-12-31')}
YEARS = list(range(2011, 2021))
STEPS = ({'build': (2011, 2015), 'trade': (2016, 2018)},
         {'build': (2011, 2018), 'trade': (2019, 2020)})
SLICES3 = ('A-trend', 'A-chop', 'B-chop')
SRC = {'A-trend': ('gate2_tuned_modeA_trend.csv', 'A', 'trend'),
       'A-chop':  ('gate2_tuned_modeA_chop.csv',  'A', 'chop'),
       'B-trend': ('gate2_tuned_modeB.csv',       'B', 'trend'),
       'B-chop':  ('gate2_tuned_modeB.csv',       'B', 'chop')}

# EVERY OUTPUT IS SUFFIXABLE so a clean-field run cannot overwrite the
# contaminated one. TAG is read from the ENVIRONMENT, not set as a module
# constant in main(): under spawn a constant is '' again inside every pool
# worker, which would silently point a clean run at the contaminated caches.
TAG = os.environ.get('WF_TAG', '')


def OUT(name):
    stem, dot, ext = name.rpartition('.')
    return os.path.join(ROOTOUT, '%s%s%s%s' % (stem, TAG, dot, ext))


TRADES_F = os.path.join(ROOTOUT, 'wf_trades.pkl')
MARKS_F = os.path.join(ROOTOUT, 'wf_marks.pkl')


def recovered_ip1():
    """B-trend's ip1, banked by the rented boxes. Every gate2_ip1_recovered*.csv:
    the 3,266 crossers from cloud_ip1.sh (_s*.csv) AND the 13,165 candidates
    from cloud_field.sh (_box*_s*.csv). The glob was `_s*` only, so the box
    files were invisible: on 2026-09-12 the four-slice merge dropped all 14,815
    B-trend candidates as "no ip1 banked" with every one of them on disk.

    A file that cannot be read is an error, not a skip: the boxes append while
    running, but by the time this is called they have pushed."""
    out = {}
    for f in sorted(glob.glob(os.path.join(ROOTOUT, 'gate2_ip1_recovered*.csv'))):
        d = pd.read_csv(f, low_memory=False)
        for r in d[d.sid != 'sid'].to_dict('records'):
            out[r['sid']] = r
    return out


def field_label(sid):
    """The slice label a sid belongs to. `src_label` already carries the slice
    for mode A (`A-trend`), but mode B's is bare `B` -- so B-chop and B-trend
    are only separable via the sid's second field. Counting on `src_label`
    alone merges them and a per-slice assert built on it cannot see a whole
    slice go missing."""
    p = str(sid).split('|')
    return p[0] if p[0] != 'B' else 'B-' + p[1]


def field_counts(sids, slices):
    """Per-slice counts restricted to the requested slices, plus anything the
    file holds outside them (reported, never silently dropped)."""
    got = {lab: 0 for lab in slices}
    extra = {}
    for sid in sids:
        lab = field_label(sid)
        if lab in got:
            got[lab] += 1
        else:
            extra[lab] = extra.get(lab, 0) + 1
    return got, extra


def load_field(slices, field_file):
    """THE FIELD FILE IS MANDATORY. It is the ONLY source of membership.

    field_sids replaces gate 2's crosses_label entirely. crosses_label IS the
    contamination -- it was decided on the stitched W2+W3 book. Filtering by it
    first and then intersecting with a clean field file keeps only strategies
    BOTH agree on, which silently drops every one of the 2,510 that the clean
    re-label admits. Measured: 1,780 of 4,807 survived that intersection, so
    the "clean" run would have been three-fifths of a clean field with gate 2's
    peek still deciding membership.

    THERE IS NO FALLBACK, BY DESIGN. The old signature was
    `load_field(slices, field_sids=None)` and None meant `crosses_label == True`
    -- the contaminated field. A caller that simply forgot the argument got a
    different and worse field with no warning, and one did: `_init_rand()`
    called `load_field(SLICES3)` with no field file, so EVERY random-entry null
    was built on the contaminated field even when the run that spawned it was
    launched with --field-file. A default that silently changes the population
    is not a default, it is a trapdoor. Missing argument now halts.

    The count is asserted against the file, not trusted. The first line of the
    log names the file and the per-slice counts so a wrong field is visible in
    the first second of a 30-minute run rather than in its results.
    """
    if not field_file:
        raise SystemExit(
            'load_field: field_file is REQUIRED and was not given.\n'
            '  There is no crosses_label fallback -- that path is the '
            'CONTAMINATED field.\n'
            '  Pass --field-file results/gate2_cleanfield.csv (or the field '
            'you actually mean).')
    if not os.path.exists(field_file):
        raise SystemExit('load_field: field file does not exist: %s' % field_file)
    FF = pd.read_csv(field_file, low_memory=False)
    if 'sid' not in FF.columns:
        raise SystemExit('load_field: %s has no sid column' % field_file)
    field_sids = set(FF.sid)
    slices = tuple(slices)
    exp, extra = field_counts(field_sids, slices)
    exp_tot = sum(exp.values())
    # FIRST LINE OF EVERY WALK-FORWARD LOG NAMES THE FIELD. On 11 Sep a run was
    # reported against the wrong member counts because the only record of the
    # field was a stale log from an earlier run six hours before.
    print('FIELD FILE %s: %d sids in file, %d in slices (%s)'
          % (os.path.abspath(field_file), len(field_sids), exp_tot,
             '  '.join('%s=%d' % (lab, exp[lab]) for lab in slices)),
          flush=True)
    if extra:
        print('  file also holds %d sids OUTSIDE the requested slices: %s'
              % (sum(extra.values()),
                 '  '.join('%s=%d' % (k, extra[k]) for k in sorted(extra))),
              flush=True)
    if exp_tot == 0:
        raise SystemExit(
            'load_field: field file %s holds NO sids in slices %s'
            % (field_file, ','.join(slices)))

    REC = recovered_ip1()
    F = []
    lost = {}
    for lab in slices:
        f, mode, sl = SRC[lab]
        d = pd.read_csv(os.path.join(ROOTOUT, f), low_memory=False)
        d = d[(d.slice == sl) & d.ip2.notna()].copy()
        d['src_mode'] = mode
        d['src_label'] = mode if mode == 'B' else '%s-%s' % (mode, sl)
        d['sid'] = (d.src_label + '|' + d.slice + '|' + d.c1 + '|' + d.c2 + '|'
                    + d.vol + '|' + d.base)
        d = d[d.sid.isin(field_sids)].copy()
        if 'ip1' not in d.columns:
            d['ip1'] = np.nan; d['risk1'] = np.nan
        miss = d.ip1.isna()
        if miss.any() and REC:
            for i in d.index[miss]:
                r = REC.get(d.at[i, 'sid'])
                if r is not None:
                    d.at[i, 'ip1'] = r['ip1']; d.at[i, 'risk1'] = r['risk1']
        n0 = len(d)
        d = d[d.ip1.notna() & d.risk1.notna()]
        if len(d) < n0:
            lost[lab] = lost.get(lab, 0) + (n0 - len(d))
            print('  %s: %d of %d dropped, no ip1 banked' % (lab, n0 - len(d), n0),
                  flush=True)
        F.append(d)
        print('  %-8s %4d strategies with ip1 (file says %d)'
              % (lab, len(d), exp[lab]), flush=True)
    D = pd.concat(F, ignore_index=True).drop_duplicates('sid').reset_index(drop=True)

    # ---- THE ASSERT. Halt, never warn-and-continue. A field that is short by
    # a slice still produces a full-looking table of results, and that table is
    # indistinguishable from a correct one after the fact.
    got, _ = field_counts(D.sid, slices)
    bad = [lab for lab in slices if got[lab] != exp[lab]]
    if bad or len(D) != exp_tot:
        msg = ['load_field: FIELD MISMATCH -- the loaded field is not the file.',
               '  field file : %s' % os.path.abspath(field_file),
               '  expected   : %d  (%s)'
               % (exp_tot, '  '.join('%s=%d' % (l, exp[l]) for l in slices)),
               '  loaded     : %d  (%s)'
               % (len(D), '  '.join('%s=%d' % (l, got[l]) for l in slices))]
        if lost:
            msg.append('  dropped for no banked ip1: %s'
                       % '  '.join('%s=%d' % (k, v) for k, v in sorted(lost.items())))
            msg.append('  -> recover ip1 for those sids, or pass a field file '
                       'that does not contain them. Do NOT proceed short.')
        raise SystemExit('\n'.join(msg))
    print('  FIELD OK: %d strategies, per-slice counts match %s'
          % (len(D), os.path.basename(field_file)), flush=True)
    return D


# ------------------------------------------------------------------- engine
def _init():
    S.load_costs()


def _cfg(row, era):
    """The engine config for one era. ip1/risk1 for the W2 era, ip2/risk_* for
    W3 -- run_pair reads the parameter set from `ip2`, so ip1 is passed there."""
    c = dict(row)
    if era == 'ip1':
        c['ip2'] = row['ip1']
        rk = json.loads(row['risk1'])
        for k in RISK_KEYS:
            c['risk_' + k] = rk.get(k, rk.get('risk_' + k))
    return c


def engine_one(row):
    """Both eras for one strategy. Returns (trade rows, mark rows).

    R and every daily mark are ACCOUNT-NORMALISED (x atr_mult) and the entry
    cost is subtracted after the restatement, exactly as l2tune.Scorer does it.
    """
    sid = row['sid']
    code = dict((s, c) for s, _, c in S.SLICES)[row['slice']]
    T, M = [], []
    tid = 0
    for era, (a, z) in ERAS.items():
        cfg = _cfg(row, era)
        am = float(cfg['risk_atr_mult'])
        for p in S.all_pairs():
            try:
                r = TR.run_pair(cfg, p)
            except Exception:
                continue
            d, tr, cl = r['dates'], r['trades'], r['c']
            if len(tr['r']) == 0:
                continue
            reg = S.regime_codes(p, d)
            w = np.flatnonzero((d >= a) & (d <= z))
            if not len(w):
                continue
            lo, hi = int(w[0]), int(w[-1]) + 1
            dv = d.values
            for j in range(len(tr['r'])):
                eb, xb = int(tr['entry_bar'][j]), int(tr['exit_bar'][j])
                if xb < 0 or reg[eb] != code or not (lo <= eb < hi):
                    continue
                ent = float(tr['entry_px'][j]); u = float(tr['units'][j])
                sgn = float(tr['dir'][j]); tot = float(tr['r'][j]) * am
                cst = float(S._cost_R(p, np.array([ent]), np.array([u]),
                                      np.array([dv[eb]]))[0])
                end = min(xb, hi - 1)
                tid += 1
                prev = 0.0
                for b in range(eb, end + 1):
                    cum = (tot if (b == xb and xb <= hi - 1)
                           else sgn * (cl[b] - ent) * u / S.RISK * am)
                    M.append((sid, p, dv[b], int(sgn), np.float32(
                        cum - prev - (cst if b == eb else 0.0)), tid))
                    prev = cum
                T.append((sid, tid, p, dv[eb], dv[end], float(prev - cst), era))
    return T, M


def stage_engine(field, jobs):
    import multiprocessing as mp
    recs = field.to_dict('records')
    t = time.time()
    if jobs > 1:
        with mp.Pool(jobs, initializer=_init) as pool:
            got = pool.map(engine_one, recs, chunksize=4)
    else:
        _init(); got = [engine_one(r) for r in recs]
    T = pd.DataFrame([x for g, _ in got for x in g],
                     columns=['sid', 'tid', 'pair', 'entry', 'exit', 'R', 'era'])
    M = pd.DataFrame([x for _, g in got for x in g],
                     columns=['sid', 'pair', 'day', 'dir', 'mark', 'tid'])
    for c in ('sid', 'pair'):
        T[c] = T[c].astype('category'); M[c] = M[c].astype('category')
    T['entry'] = pd.to_datetime(T.entry); T['exit'] = pd.to_datetime(T.exit)
    M['day'] = pd.to_datetime(M.day)
    M['dir'] = M['dir'].astype(np.int8)
    T.to_pickle(TRADES_F); M.to_pickle(MARKS_F)
    print('  engine: %d trades, %d mark rows, %d strategies, %.1f min'
          % (len(T), len(M), T.sid.nunique(), (time.time() - t) / 60), flush=True)
    return T, M


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', default='engine')
    ap.add_argument('--slices', default=','.join(SLICES3))
    ap.add_argument('--jobs', type=int, default=int(os.environ.get('WF_JOBS', '5')))
    ap.add_argument('--n-null', type=int, default=25)
    ap.add_argument('--n-rand', type=int, default=N_RAND)
    ap.add_argument('--suffix', default='')
    ap.add_argument('--field-file', default='')
    ap.add_argument('--structures', default=','.join(DEFAULT_STRUCTURES))
    ap.add_argument('--nocut', action='store_true',
                    help='nullre: null-test the UNCUT book -- NO_CUT and '
                         'NO_CUT_SLICE_BALANCED -- instead of the cut ALLPASS')
    a = ap.parse_args()
    S.load_costs()
    sl = tuple(x for x in a.slices.split(',') if x)
    print('slices: %s' % (sl,), flush=True)
    if not a.field_file:
        raise SystemExit(
            'l2walkfwd: --field-file is REQUIRED.\n'
            '  Running without it used to mean the crosses_label field, which '
            'is the CONTAMINATED one.\n'
            '  e.g. --field-file results/gate2_cleanfield.csv')
    # Pool initializers take no arguments, so workers read the field file from
    # the environment. Set it BEFORE any pool is built.
    os.environ['WF_FIELD_FILE'] = os.path.abspath(a.field_file)
    os.environ['WF_SLICES'] = ','.join(sl)
    F = load_field(sl, a.field_file)
    print('field: %d strategies' % len(F), flush=True)
    os.environ['WF_EXPECT_SIDS'] = str(int(F.sid.nunique()))
    global TAG, TRADES_F, MARKS_F
    TAG = a.suffix
    os.environ['WF_TAG'] = TAG
    TRADES_F = OUT('wf_trades.pkl'); MARKS_F = OUT('wf_marks.pkl')
    if a.stage == 'engine':
        stage_engine(F, a.jobs)
    elif a.stage == 'nullre':
        stage_null_randomentry(a.jobs, a.n_null, nocut=a.nocut)
    elif a.stage == 'nullid':
        stage_null_identity(a.jobs, a.n_null,
                            [x for x in a.structures.split(',') if x])
    elif a.stage == 'sizing':
        stage_sizing(a.jobs)
    elif a.stage == 'size':
        stage_size(a.jobs, a.n_null, a.n_rand)
    elif a.stage == 'ctrl':
        stage_controls(a.jobs)
    elif a.stage == 'walk':
        stage_walk(a.jobs, a.n_null, [x for x in a.structures.split(',') if x])



# ------------------------------------------------------------------- the cut
import l2gate3 as G3
BARS = G3.BARS
N_SHUF = 2000          # DIP95 shuffles. 10,000 was the static-team setting; the
                       # walk runs ~10,000 books, and the 95th percentile of
                       # 2,000 draws is stable to well under the differences
                       # being read off it. Stated rather than silently changed.
SEARCH_SHUF = 400      # inside the greedy only. The shuffle matrix is cached by
                       # (n, n_shuf, seed), so every candidate in a round is
                       # judged against the SAME permutations -- common random
                       # numbers, which is what makes a cheap estimate safe for
                       # RANKING. Every reported number is rescored at N_SHUF.
CAP_PCT = 2.0
SIZE_CAP = 6.0         # the old curve topped out at 6; the fitted curve is
                       # clipped there so one thin bin cannot dominate the book
MIN_BIN = 30
N_BINS = 6
BUDGETS = (('team1', 3.6, 3.6), ('team2', 5.4, 3.6))


def trade_year_sums(M):
    """Per trade, per calendar year, the marks that fall in that year. Any
    window's R is then a filtered sum -- which IS mark-to-market at that
    window's boundary, since marks are daily increments."""
    X = M[['sid', 'tid', 'mark']].copy()
    X['yr'] = M.day.dt.year.values.astype(np.int16)
    return X.groupby(['sid', 'tid', 'yr'], observed=True).mark.sum().reset_index()


def metrics(T, TY, years):
    """Gate 3's metrics on trades ENTERED in `years`, valued only over `years`.

    MAX DRAWDOWN IS CHRONOLOGICAL. l2tune._agg accumulates over a PAIR-MAJOR
    concatenation -- every EURUSD trade, then every GBPUSD trade -- which is not
    a time series. Ordered by entry date here.
    """
    ys = set(years)
    ent = T[T.entry.dt.year.isin(ys)][['sid', 'tid', 'entry']]
    r = TY[TY.yr.isin(ys)].groupby(['sid', 'tid'], observed=True).mark.sum()
    D = ent.join(r.rename('R'), on=['sid', 'tid']).dropna(subset=['R'])
    if not len(D):
        return pd.DataFrame()
    D = D.sort_values(['sid', 'entry'], kind='stable')
    g = D.groupby('sid', observed=True)
    eq = g.R.cumsum()
    dd = eq.groupby(D.sid.values, observed=True).cummax() - eq
    D = D.assign(_dd=dd.values)
    pos = D.R.clip(lower=0); neg = D.R.clip(upper=0)
    A = D.assign(_p=pos, _n=neg, _w=(D.R > 0).astype(float),
                 _nn=np.where(D.R < 0, D.R, np.nan))
    G = A.groupby('sid', observed=True)
    out = pd.DataFrame(dict(
        n=G.R.size(), total_R=G.R.sum(), gp=G._p.sum(), gl=-G._n.sum(),
        max_dd_R=G._dd.max(), win_rate=G._w.mean(),
        avg_win_R=A[A.R > 0].groupby('sid', observed=True).R.mean(),
        dn=A.groupby('sid', observed=True)._nn.std(ddof=1),
        scale_=A.assign(_a=A.R.abs()).groupby('sid', observed=True)._a.mean()))
    out['expectancy_R'] = out.total_R / out.n
    out['profit_factor'] = np.where(out.gl > 0, out.gp / out.gl.replace(0, np.nan),
                                    np.where(out.gp > 0, np.inf, 0.0))
    dn = out.dn.where(out.dn > 1e-9 * out.scale_.fillna(1.0))
    out['sortino'] = out.expectancy_R / dn * np.sqrt(252)
    out['calmar'] = np.where(out.max_dd_R > 0, out.total_R / out.max_dd_R, 0.0)
    out['max_dd_frac'] = out.max_dd_R / (out.avg_win_R * out.win_rate * out.n).replace(0, np.nan)
    return out.reset_index()


def cut(T, TY, years, perm=None, apply_bars=True):
    """perm maps sid -> the sid whose build-year metrics it is judged on. The
    IDENTITY NULL: a strategy passes on someone else's build record and then
    trades its own. Applied to the metrics, never to the marks.

    apply_bars=False is the NO_CUT control: the same frame, same columns, same
    build years, with gate 3's bars simply not applied. It is the honest
    counterfactual for "what does the cut buy" -- the cut is the ONLY thing that
    differs between it and ALLPASS."""
    D = metrics(T, TY, years)
    if not len(D):
        return D, {}
    if perm is not None:
        D = D.assign(sid=D.sid.map(perm)).dropna(subset=['sid'])
    if not apply_bars:
        return D.reset_index(drop=True), {}
    ok = pd.Series(True, index=D.index); fails = {}
    for k, v in BARS.items():
        good = (D[k] <= v) if k == 'max_dd_frac' else (D[k] >= v)
        good = good.fillna(False)
        fails[k] = int((~good).sum())
        ok &= good
    return D[ok].reset_index(drop=True), fails


# --------------------------------------------------------- the netting kernel
class Book:
    """Sparse (position x member) matrices so one candidate book costs four
    matrix-vector products.

    A netted book cannot be scored as a weighted sum of member series the way
    the old team builder scored a stacked one: the size of a position depends on
    HOW MANY members are on each side of it, which changes with membership. As a
    groupby that is ~1.5 s per trial and a greedy search is impossible.

    Every (pair, day) any member touches is a row; each member contributes a
    long mask, a short mask and its mark. For any membership vector w:

        nl = L @ w        ns = S @ w
        ml = (LM @ w)/nl  ms = (SM @ w)/ns

    and the netting, the fraction, the curve, the currency cap and the daily
    series all follow with no grouping at all. Density is ~2% -- a member holds
    a position on ~1,250 of ~56,000 (pair, day) slots -- so dense float32 would
    be 555 MB per book and six null workers would need 3.3 GB. Sparse is 25 MB
    and faster.
    """

    def __init__(self, M, members):
        mem = list(members)
        midx = {m: i for i, m in enumerate(mem)}
        col = M.sid.astype(str).map(midx).values
        keep = ~pd.isna(col)
        M = M[keep]; col = col[keep].astype(np.int64)
        pc, upair = pd.factorize(M.pair.astype(str), sort=True)
        dc, uday = pd.factorize(M.day.values, sort=True)
        key = pc.astype(np.int64) * len(uday) + dc
        upos, pidx = np.unique(key, return_inverse=True)
        self.pair = np.asarray(upair)[(upos // len(uday)).astype(int)]
        self.day = pd.DatetimeIndex(np.asarray(uday)[(upos % len(uday)).astype(int)])
        n_p, n_m = len(upos), len(mem)
        dd = M['dir'].values; mk = M.mark.values.astype(np.float32)
        lo = dd > 0
        self.L = sp.csr_matrix((np.ones(lo.sum(), np.float32),
                                (pidx[lo], col[lo])), shape=(n_p, n_m))
        self.Sm = sp.csr_matrix((np.ones((~lo).sum(), np.float32),
                                 (pidx[~lo], col[~lo])), shape=(n_p, n_m))
        self.LM = sp.csr_matrix((mk[lo], (pidx[lo], col[lo])), shape=(n_p, n_m))
        self.SM = sp.csr_matrix((mk[~lo], (pidx[~lo], col[~lo])), shape=(n_p, n_m))
        self.members = mem
        self.udays, self.dpos = np.unique(self.day.values, return_inverse=True)
        self.nd = len(self.udays)
        self.dyears = pd.DatetimeIndex(self.udays).year.values
        ccy = sorted({c for p in set(self.pair) for c in (p[:3], p[3:])})
        cidx = {c: i for i, c in enumerate(ccy)}
        self.nc = len(ccy)
        self.bc = np.array([cidx[p[:3]] for p in self.pair])
        self.qc = np.array([cidx[p[3:]] for p in self.pair])
        # positions -> days, as a matrix, so per-member daily series are one
        # sparse product instead of a scatter-add per member
        self.Dagg = sp.csr_matrix(
            (np.ones(n_p, np.float32), (self.dpos, np.arange(n_p))),
            shape=(self.nd, n_p))
        self.posyears = self.day.year.values

    def net(self, w, curve):
        nl = self.L @ w; ns = self.Sm @ w
        net = nl - ns
        act = np.abs(net) >= 0.5
        f = np.abs(net) / max(float(w.sum()), 1.0)
        sz = curve(f) * act
        live = sz > 0
        ml = np.divide(self.LM @ w, nl, out=np.zeros_like(nl), where=nl > 0)
        ms = np.divide(self.SM @ w, ns, out=np.zeros_like(ns), where=ns > 0)
        sgn = np.where(net > 0, 1.0, -1.0)
        mk = np.where(sgn > 0, ml, ms)
        return sgn * live, sz * live, mk * live, f

    def series(self, w, curve, cap_pct=None, per_unit=None, den=None):
        sgn, sz, mk, f = self.net(w, curve)
        binds, worst = 0, float('nan')
        if cap_pct is not None and per_unit:
            E = np.zeros((self.nd, self.nc, 2), np.float32)
            d0 = (sgn > 0).astype(int); d1 = 1 - d0
            np.add.at(E, (self.dpos, self.bc, d0), sz)
            np.add.at(E, (self.dpos, self.qc, d1), sz)
            mx = E.reshape(self.nd, -1).max(axis=1) * per_unit
            fac = np.ones(self.nd, np.float32)
            over = mx > cap_pct
            fac[over] = cap_pct / mx[over]
            sz = sz * fac[self.dpos]
            binds = int(over.sum()); worst = float(mx.max())
        pnl = np.zeros(self.nd); gross = np.zeros(self.nd)
        np.add.at(pnl, self.dpos, mk * sz)
        np.add.at(gross, self.dpos, sz)
        if den is None:
            den = float(gross[gross > 0].mean()) if (gross > 0).any() else 1.0
        self.last = dict(sgn=sgn, sz=sz, gross=gross)
        return pnl / den, den, binds, worst, sz, f


class Dip:
    """DIP95 with the shuffle matrix built once and reused. The old one ran a
    Python loop of 10,000 rng.shuffle calls per call; in a greedy search that is
    the entire cost."""
    _cache = {}

    @classmethod
    def get(cls, n, n_shuf=N_SHUF, seed=20260910):
        k = (n, n_shuf, seed)
        if k not in cls._cache:
            rng = np.random.default_rng(seed)
            cls._cache[k] = rng.permuted(
                np.tile(np.arange(n, dtype=np.int32), (n_shuf, 1)), axis=1)
        return cls._cache[k]

    @classmethod
    def p95(cls, d, n_shuf=N_SHUF):
        n = len(d)
        if n < 3:
            return 0.0
        P = cls.get(n, n_shuf)
        out = np.empty(n_shuf)
        for i in range(0, n_shuf, 500):
            X = d[P[i:i + 500]]
            eq = np.cumsum(X, axis=1)
            out[i:i + 500] = (np.maximum.accumulate(eq, axis=1) - eq).max(axis=1)
        return float(np.percentile(out, 95))


def scale_of(d, dipb, dayb, n_shuf=N_SHUF, use_dip=True):
    """Returns (scale, DIP95, actual maxDD, worst day, binding term).

    use_dip=False sizes on the PATH THAT HAPPENED only -- actual max drawdown
    and worst day -- with DIP95 still measured and reported but not allowed to
    bind. DIP95 shuffles the order of days, so it prices a drawdown the account
    never took; whether that belongs in the sizing rule is a decision, not an
    arithmetic fact, and this makes the alternative measurable.
    """
    D = Dip.p95(d, n_shuf)
    eq = np.cumsum(d); adj = float((np.maximum.accumulate(eq) - eq).max())
    wd = float(-d.min()) if d.min() < 0 else 1e-9
    risk = max(adj, D) if use_dip else adj
    s_risk = dipb / risk if risk > 0 else np.inf
    s_day = dayb / wd if wd > 0 else np.inf
    if s_day < s_risk:
        binds = 'worst day'
    elif not use_dip:
        binds = 'actual maxDD'
    else:
        binds = 'actual maxDD' if adj >= D else 'DIP95'
    return float(min(s_risk, s_day)), D, adj, wd, binds


# ------------------------------------------------------- the agreement curve
def fit_curve(B, w, years, log=None):
    """REBUILT FROM THE BUILD YEARS, ON THE FRACTION OF MEMBERS VOTING.

    The 1/3/6 curve was fitted where a level was a net vote count out of 25.
    At 250 members the same counts mean something else entirely -- level 4 is
    near-unanimity of 25 and four votes in 250 -- and the curve goes flat over
    two thirds of the book. So agreement is expressed as |net| / members here,
    and the curve is measured rather than carried over: bin the fraction into
    quantiles on the BUILD years, take each bin's mean R per unit of size, and
    set size proportional to it, normalised so the weakest bin that still earns
    is 1.0. Bins that lose money get size 0. Clipped at 6, which is where the
    old curve topped out, so one thin bin cannot run away with the book.
    """
    nl = B.L @ w; ns = B.Sm @ w
    net = nl - ns
    act = np.abs(net) >= 0.5
    ym = np.isin(B.day.year.values, list(years))
    m = act & ym
    if m.sum() < N_BINS * MIN_BIN:
        return (lambda f: (np.abs(f) > 0).astype(float)), None
    f = np.abs(net[m]) / max(w.sum(), 1.0)
    ml = np.divide(B.LM @ w, nl, out=np.zeros_like(nl), where=nl > 0)
    ms = np.divide(B.SM @ w, ns, out=np.zeros_like(ns), where=ns > 0)
    mk = np.where(net > 0, ml, ms)[m]
    qs = np.unique(np.quantile(f, np.linspace(0, 1, N_BINS + 1)))
    qs[0] = -np.inf; qs[-1] = np.inf
    b = np.digitize(f, qs[1:-1])
    rows = []
    for i in range(len(qs) - 1):
        s = b == i
        rows.append(dict(bin=i, lo=float(qs[i]), hi=float(qs[i + 1]),
                         n=int(s.sum()), r_per_unit=float(mk[s].mean()) if s.any() else 0.0))
    C = pd.DataFrame(rows)
    # thin bins carry no information; merge them into the neighbour below
    while (C.n < MIN_BIN).any() and len(C) > 2:
        i = int(C[C.n < MIN_BIN].index[0])
        j = i - 1 if i > 0 else 1
        lo, hi = min(C.lo[i], C.lo[j]), max(C.hi[i], C.hi[j])
        nn = C.n[i] + C.n[j]
        rr = (C.r_per_unit[i] * C.n[i] + C.r_per_unit[j] * C.n[j]) / nn
        C = C.drop([i, j]).reset_index(drop=True)
        C = pd.concat([C, pd.DataFrame([dict(bin=-1, lo=lo, hi=hi, n=nn,
                                             r_per_unit=rr)])], ignore_index=True)
        C = C.sort_values('lo').reset_index(drop=True)
    # SIZE PROPORTIONAL TO MEASURED EDGE, scaled so the best bin is SIZE_CAP.
    # Normalising by the weakest EARNING bin -- the obvious first choice -- puts
    # a near-zero number in the denominator, and every other bin then lands on
    # the clip: the curve degenerates to a 0/1/6 step and throws away the shape
    # it was fitted to find. Against the best bin instead, the relative sizes
    # are the ratios of measured R per unit, and SIZE_CAP is only an overall
    # scale factor that the budget rescaling removes anyway. A bin that loses
    # money is not traded.
    top = float(C.r_per_unit.max())
    C['size'] = (np.clip(C.r_per_unit, 0.0, None) / top * SIZE_CAP
                 if top > 0 else 0.0)
    edges = C.hi.values[:-1]
    sizes = C['size'].values.astype(np.float32)
    if log is not None:
        log.append(C)

    def curve(x):
        return sizes[np.digitize(x, edges)]
    return curve, C


# ------------------------------------------------------------- the structures
def fam(sid):
    """Indicator family = the c1 slot. There is no taxonomy above the indicator
    name in l2lib -- KIND is the slot type, not a family -- so c1, the primary
    confirmation, is the family key. 39 distinct across the three slices."""
    return sid.split('|')[2]


def pick_allpass(P, **k):
    return list(P.sid)


def pick_stable(P, T=None, TY=None, build=None, perm=None, **k):
    """Passers that ALSO pass the cut on the LAST THREE build years."""
    # LAST THREE BUILD YEARS, IN PLAY ORDER. This read `build[1] - 2 .. build[1]`
    # -- the SECOND element of the build list, not the last -- so step 1 cut on
    # 2010-2012 when its build window is 2011-2015, and 2010 has no data at all.
    # STABLE's member counts before 2026-09-10 22:50 were taken on that window.
    last3 = list(build)[-3:]
    Q, _ = cut(T, TY, list(last3), perm=perm)
    return [s for s in P.sid if s in set(Q.sid)]


def pick_familycap(P, B=None, build=None, **k):
    """One member per c1 family -- the best by build-year expectancy -- then
    drop any member correlated above 0.60 with one already kept, worse first."""
    Q = P.sort_values('expectancy_R', ascending=False)
    best, seen = [], set()
    for r in Q.itertuples():
        f = fam(r.sid)
        if f in seen:
            continue
        seen.add(f); best.append(r.sid)
    idx = {m: i for i, m in enumerate(B.members)}
    cols = [c for c in best if c in idx]
    if len(cols) < 2:
        return cols
    # per-member DAILY series over the build years: mask positions by year, take
    # the members' columns, sum to days. The year mask is per POSITION, not per
    # day -- B.day is one entry per (pair, day) row, B.udays one per day.
    ymp = np.isin(B.posyears, list(build)).astype(np.float32)
    sub = (B.LM + B.SM)[:, [idx[c] for c in cols]].multiply(ymp[:, None]).tocsr()
    Xd = np.asarray((B.Dagg @ sub).todense())
    C = np.corrcoef(Xd.T)
    keep, kept = [], []
    for j in range(len(cols)):
        if all(abs(C[j, i]) <= 0.60 for i in kept):
            keep.append(cols[j]); kept.append(j)
    return keep


def pick_greedy(P, B=None, build=None, curve=None, dipb=3.6, dayb=3.6, log=None, **k):
    """The greedy picker, allowed only on the build years. Starts empty, adds
    the single member that most improves the build-year score, stops when
    nothing does, then drops one at a time while that improves it."""
    cand = [c for c in B.members if c in set(P.sid)]
    idx = {m: i for i, m in enumerate(B.members)}
    ym = np.isin(B.dyears, list(build))
    team = []

    def sc(mem):
        if not mem:
            return -1e9
        w = np.zeros(len(B.members), np.float32)
        for c in mem:
            w[idx[c]] = 1.0
        d, _, _, _, _, _ = B.series(w, curve)
        d = d[ym]
        if not np.any(d):
            return -1e9
        s = scale_of(d, dipb, dayb, SEARCH_SHUF)[0]
        yr = pd.Series(d * s).groupby(B.dyears[ym]).sum()
        return float(yr.median())

    cur = -1e9
    while True:
        best, bc = cur, None
        for c in cand:
            if c in team:
                continue
            v = sc(team + [c])
            if v > best:
                best, bc = v, c
        if bc is None:
            break
        team.append(bc); cur = best
        if log is not None:
            log.append((len(team), bc, cur))
    while len(team) > 1:
        best, bc = cur, None
        for c in list(team):
            v = sc([x for x in team if x != c])
            if v > best:
                best, bc = v, c
        if bc is None:
            break
        team.remove(bc); cur = best
    return team


def pick_slice_balanced(P, **k):
    """THE SAME ROSTER AS ALLPASS, WEIGHTED SO EACH SLICE COUNTS EQUALLY.

    Not a membership control -- a WEIGHTING control. ALLPASS gives every member
    one unit, so a slice with 2,960 of the 4,807 members decides the book and
    the other two are rounding. This gives each SLICE one unit, split equally
    among its members, which answers a different question: is the result a
    property of the field, or of the one slice that happens to dominate it.

    Returns (members, weights). A structure may return either a bare list --
    equal weight, the old behaviour -- or this pair.
    """
    mem = list(P.sid)
    per = {}
    for sid in mem:
        lab = field_label(sid)
        per[lab] = per.get(lab, 0) + 1
    n_sl = len(per)
    # each slice gets 1/n_sl of the book, split equally inside the slice; scaled
    # by len(mem)/n_sl so the TOTAL weight matches ALLPASS's and the two are
    # compared at the same gross size rather than at different ones.
    tot = float(len(mem))
    w = {sid: (tot / n_sl) / per[field_label(sid)] for sid in mem}
    return mem, w


# THE FOUR, AND ONLY THE FOUR. main() defaults --structures to the keys of
# this dict, so a fifth key here silently changes what the walk stage, the
# identity null and the team-size sweep all run. SLICE_BALANCED is a control,
# registered by stage_controls() for the duration of that stage only.
STRUCTURES = {'ALLPASS': pick_allpass, 'STABLE': pick_stable,
              'PICKED': pick_greedy, 'FAMILY_CAP': pick_familycap,
              'SLICE_BALANCED': pick_slice_balanced}
# What --structures means when not given. SLICE_BALANCED is a control and is
# never in the default; it is reachable by name, from --stage ctrl and from
# --stage nullre --nocut, both of which need it inside spawned workers -- which
# is why it lives in the dict and not in a stage-local registration.
DEFAULT_STRUCTURES = ('ALLPASS', 'STABLE', 'PICKED', 'FAMILY_CAP')


# ----------------------------------------------------------------- the walk
def kpis(x, years):
    """x is the SCALED daily series over the stitched trade years."""
    e = np.cumsum(x)
    yr = pd.Series(x).groupby(years).sum()
    neg = x[x < 0]
    dd = float((np.maximum.accumulate(e) - e).max())
    mon = pd.Series(x).groupby([years, pd.DatetimeIndex(_MONTHS).month]).sum() \
        if _MONTHS is not None else pd.Series([np.nan])
    return dict(median_year_pct=float(yr.median()), mean_year_pct=float(yr.mean()),
                worst_year_pct=float(yr.min()), best_year_pct=float(yr.max()),
                total_return_pct=float(x.sum()), max_dd_pct=dd,
                dip95_pct=float(Dip.p95(x)), worst_day_pct=float(-x.min()),
                worst_month_pct=float(-mon.min()),
                sortino=float(x.mean() / neg.std(ddof=1) * np.sqrt(252)) if len(neg) > 1 else np.nan,
                sharpe=float(x.mean() / x.std(ddof=1) * np.sqrt(252)) if x.std(ddof=1) > 0 else np.nan,
                calmar=float(x.sum() / dd) if dd > 0 else np.nan,
                profit_factor=float(x[x > 0].sum() / -x[x < 0].sum()) if (x < 0).any() else np.inf,
                win_rate_pct=float(100 * (x > 0).mean()),
                trading_days=int(len(x)), n_years=int(len(yr)))


_MONTHS = None



def diagnostics(B, sgn, sz, raw_sz, gross, per_unit, tsrc, C):
    """Everything the first writer computed and threw away.

    All measured on the TRADED years only, which is the stretch the account
    actually lives through. Exposure is in % of account: per_unit converts one
    unit of size into the same % the currency cap is expressed in, so a mean
    gross exposure of 1.0 here means the book is carrying 1% of the account in
    open risk on an average day.
    """
    pt = np.isin(B.posyears, list(tsrc))
    dt = np.isin(B.dyears, list(tsrc))
    live = (sz > 0) & pt
    nd = int(dt.sum())
    # netted TRADES: a contiguous run of days on one pair in one direction.
    # The book nets, so a "trade" is the netted position, not a member's fill.
    key = pd.DataFrame(dict(pair=B.pair[pt], day=B.day.values[pt],
                            d=np.where(sz[pt] > 0, sgn[pt], 0.0)))
    key = key.sort_values(['pair', 'day'], kind='stable')
    prev = key.groupby('pair', observed=True).d.shift(1).fillna(0.0)
    entries = int(((key.d != 0) & (key.d != prev)).sum())
    nyr = max(len(set(pd.DatetimeIndex(B.udays[dt]).year)), 1)
    # open positions and gross exposure, per day
    opd = np.zeros(B.nd)
    np.add.at(opd, B.dpos[live], 1.0)
    gx = np.zeros(B.nd)
    np.add.at(gx, B.dpos[live], sz[live])
    # multiplier histogram, on the size the curve asked for before any capping
    hist = {}
    if C is not None:
        for v in sorted(set(np.round(C['size'].values, 4))):
            m = np.isclose(raw_sz[pt], v, atol=1e-4)
            hist['%.2f' % v] = float(100.0 * m.sum() / max(pt.sum(), 1))
    return dict(trades_traded_years=entries,
                trades_per_year=float(entries / nyr),
                mean_open_positions=float(opd[dt].mean()),
                max_open_positions=int(opd[dt].max()),
                mean_gross_exposure_pct=float(gx[dt].mean() * per_unit),
                max_gross_exposure_pct=float(gx[dt].max() * per_unit),
                position_days=int(live.sum()),
                multiplier_hist_pct=json.dumps(hist))


def walk(T, TY, M, ymap, dipb, dayb, structures=None, verbose=False,
         use_dip=True, perm=None, nocut=False):
    """One complete walk. `ymap` maps a calendar year to the year it PLAYS --
    identity for the real walk, a permutation for a null draw. Every decision
    at a step uses only that step's build years.
    """
    structures = structures or list(DEFAULT_STRUCTURES)
    inv = {v: k for k, v in ymap.items()}
    out = {s: dict(daily=[], days=[], members=[], curves=[], cuts=[]) for s in structures}
    for si, st in enumerate(STEPS):
        b0, b1 = st['build']; t0, t1 = st['trade']
        bsrc = [inv[y] for y in range(b0, b1 + 1)]
        tsrc = [inv[y] for y in range(t0, t1 + 1)]
        P, fails = cut(T, TY, bsrc, perm=perm, apply_bars=not nocut)
        if not len(P):
            raise RuntimeError('step %d: nothing passed the cut' % (si + 1))
        allp = list(P.sid)
        B = Book(M[M.sid.isin(allp)], allp)
        w_all = np.ones(len(B.members), np.float32)
        curve, C = fit_curve(B, w_all, bsrc)
        if verbose:
            print('   step %d build %s: %d passers, fails %s'
                  % (si + 1, (b0, b1), len(P), fails), flush=True)
        ybuild = np.isin(B.dyears, bsrc)
        ytrade = np.isin(B.dyears, tsrc)
        for s in structures:
            mem = STRUCTURES[s](P, B=B, T=T, TY=TY, build=tuple(bsrc), curve=curve,
                                dipb=dipb, dayb=dayb, perm=perm)
            # A structure returns a bare member list (equal weight) or a
            # (members, weights) pair. Weighting controls need the second form.
            wts = None
            if isinstance(mem, tuple):
                mem, wts = mem
            mem = [m for m in mem if m in set(B.members)]
            if len(mem) < 2:
                raise RuntimeError('step %d %s: %d members' % (si + 1, s, len(mem)))
            idx = {m: i for i, m in enumerate(B.members)}
            w = np.zeros(len(B.members), np.float32)
            for c in mem:
                w[idx[c]] = 1.0 if wts is None else np.float32(wts[c])
            # SIZE IS DECIDED ON THE BUILD YEARS AND NOT TOUCHED AGAIN.
            d0, den, _, _, _, _ = B.series(w, curve)
            db = d0[ybuild]
            sc, bD, badj, bwd, bbind = scale_of(db, dipb, dayb, use_dip=use_dip)
            per_unit = sc / den
            raw_sz = B.net(w, curve)[1].copy()       # multiplier BEFORE the cap
            d1, _, binds, worst, sz, f = B.series(w, curve, cap_pct=CAP_PCT,
                                                  per_unit=per_unit, den=den)
            gross = B.last['gross']; sgn = B.last['sgn']
            dg = dict(diagnostics(B, sgn, sz, raw_sz, gross, per_unit, tsrc, C))
            out[s]['daily'].append(d1[ytrade] * sc)
            out[s]['days'].append(B.udays[ytrade])
            out[s]['members'].append(len(mem))
            out[s]['curves'].append(C)
            out[s]['cuts'].append(dict(step=si + 1, passers=len(P), members=len(mem),
                                       scale=sc, cap_bound=binds, max_expo=worst,
                                       roster=mem, binds=bbind,
                                       build_dip95_pct=bD * sc,
                                       build_max_dd_pct=badj * sc,
                                       build_worst_day_pct=bwd * sc,
                                       **dg))
    res = {}
    for s in structures:
        x = np.concatenate(out[s]['daily'])
        dy = np.concatenate(out[s]['days'])
        global _MONTHS
        _MONTHS = dy
        k = kpis(x, pd.DatetimeIndex(dy).year.values)
        k.update(structure=s, members_step1=out[s]['members'][0],
                 members_step2=out[s]['members'][1])
        res[s] = (k, out[s]['cuts'], x, dy)
    return res


# ------------------------------------------------------------------ the null
def ymaps(n, seed=20260910):
    """Year permutations. In a WALK-FORWARD a joint year shuffle is a real null,
    which it is not for a fixed-window team score.

    l2teamcheck's shuffle relabels year blocks and leaves every yearly total
    intact, so a static median-year score cannot move. Here the permutation
    decides WHICH years are build years and which are traded, so it destroys the
    only thing the design claims -- that build-year quality predicts trade-year
    quality -- while leaving each year's data and every cross-member alignment
    exactly as they are.

    CONFOUND, stated: the permutation moves years across the ip1/ip2 boundary.
    Every year remains blind under the parameters it was scored with (ip1 never
    saw 2011-2015, ip2 never saw 2016-2020), so no draw is contaminated, but the
    two parameter eras mix.
    """
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n):
        p = rng.permutation(YEARS)
        out.append(dict(zip(YEARS, p)))
    return out


_NG = {}


def _worker_tables():
    """THE ONE PLACE A POOL WORKER RESOLVES ITS PICKLES.

    macOS multiprocessing SPAWNS: a worker re-imports this module from scratch,
    so TRADES_F / MARKS_F are the module DEFAULTS -- results/wf_trades.pkl, the
    unsuffixed file -- not whatever main() set in the parent. _init_size and
    _init_rand each re-derived the path from WF_TAG; _init_null did not, and so
    on 2026-09-11 every identity-null draw of the CLEAN-field run was drawn
    from the CONTAMINATED 3,485 field while the real walk it was compared to
    used the clean 4,807. The summary said p=1.000 with mean_members 620/575 --
    the contaminated field's exact passer count, sitting next to a clean real.

    Every worker now resolves through here, and PROVES it loaded the same field
    as the parent: main() exports WF_EXPECT_SIDS and the worker halts if its
    pickle disagrees. A null drawn from a different population than the real
    is not a null.
    """
    globals()['TAG'] = os.environ.get('WF_TAG', '')
    globals()['TRADES_F'] = OUT('wf_trades.pkl')
    globals()['MARKS_F'] = OUT('wf_marks.pkl')
    T = pd.read_pickle(TRADES_F); M = pd.read_pickle(MARKS_F)
    want = os.environ.get('WF_EXPECT_SIDS', '')
    n = int(T.sid.nunique())
    if want and n != int(want):
        # A Pool RESPAWNS a worker whose initializer dies, forever, silently.
        # So this cannot merely raise: it says why, takes the parent stage
        # down with it, and exits. A halt, not a hang.
        import signal
        msg = ('!! worker loaded %s with %d sids but the parent field has %s -- '
               'the null would be drawn from a different population than the real'
               % (TRADES_F, n, want))
        print(msg, flush=True); print(msg, file=sys.stderr, flush=True)
        os.kill(os.getppid(), signal.SIGTERM)
        os._exit(3)
    return T, M


def _init_null():
    """Each worker loads the tables ONCE. Passing them per task would pickle
    177 MB of marks for every draw."""
    S.load_costs()
    _NG['T'], _NG['M'] = _worker_tables()
    _NG['TY'] = trade_year_sums(_NG['M'])


def _null_one(args):
    ymap, dipb, dayb, structures = args
    try:
        r = walk(_NG['T'], _NG['TY'], _NG['M'], ymap, dipb, dayb, structures)
    except Exception as e:
        return {'_err': type(e).__name__ + ': ' + str(e)[:90]}
    return {s: r[s][0]['median_year_pct'] for s in structures}


def stage_walk(jobs, n_null, structures):
    T = pd.read_pickle(TRADES_F); M = pd.read_pickle(MARKS_F)
    print('  loaded %d trades, %d marks, %d strategies'
          % (len(T), len(M), T.sid.nunique()), flush=True)
    t = time.time()
    TY = trade_year_sums(M)
    print('  trade-year sums: %d rows, %.1f s' % (len(TY), time.time() - t), flush=True)
    ident = {y: y for y in YEARS}
    rows, rosters, curves, daily = [], [], [], {}
    for bt, dipb, dayb in BUDGETS:
        t0 = time.time()
        R = walk(T, TY, M, ident, dipb, dayb, structures, verbose=(bt == 'team1'))
        print('  real walk %s in %.1f min' % (bt, (time.time() - t0) / 60), flush=True)
        for s, (k, cuts, x, dy) in R.items():
            k.update(budget=bt, dip_budget=dipb, day_budget=dayb, kind='real')
            rows.append(k)
            daily['%s|%s' % (bt, s)] = pd.Series(x, index=pd.DatetimeIndex(dy))
            for c in cuts:
                rosters.append(dict(
                    budget=bt, structure=s, step=c['step'],
                    passers=c['passers'], members=c['members'], scale=c['scale'],
                    binds=c['binds'], build_dip95_pct=c['build_dip95_pct'],
                    build_max_dd_pct=c['build_max_dd_pct'],
                    build_worst_day_pct=c['build_worst_day_pct'],
                    trades_traded_years=c['trades_traded_years'],
                    trades_per_year=c['trades_per_year'],
                    mean_open_positions=c['mean_open_positions'],
                    max_open_positions=c['max_open_positions'],
                    mean_gross_exposure_pct=c['mean_gross_exposure_pct'],
                    max_gross_exposure_pct=c['max_gross_exposure_pct'],
                    position_days=c['position_days'],
                    multiplier_hist_pct=c['multiplier_hist_pct'],
                    cap_bound_days=c['cap_bound'],
                    max_ccy_exposure_pct=c['max_expo'],
                    roster=';'.join(c['roster'])))
            print('    %-6s %-11s median %7.3f%%  worst %7.3f%%  maxDD %5.2f%%  '
                  'PF %.2f  members %d/%d'
                  % (bt, s, k['median_year_pct'], k['worst_year_pct'],
                     k['max_dd_pct'], k['profit_factor'],
                     k['members_step1'], k['members_step2']), flush=True)
    O = pd.DataFrame(rows)
    O.to_csv(OUT('walkforward_structures_3slice.csv'), index=False)
    pd.DataFrame(rosters).to_csv(
        OUT('walkforward_rosters_3slice.csv'), index=False)
    pd.DataFrame(daily).to_csv(
        OUT('walkforward_daily_3slice.csv'))
    if n_null <= 0:
        return O
    # ---- null
    import multiprocessing as mp
    maps = ymaps(n_null)
    nrows = []
    for bt, dipb, dayb in BUDGETS:
        t0 = time.time()
        args = [(m, dipb, dayb, structures) for m in maps]
        if jobs > 1:
            with mp.Pool(jobs, initializer=_init_null) as pool:
                got = pool.map(_null_one, args, chunksize=1)
        else:
            _init_null(); got = [_null_one(a) for a in args]
        errs = {}
        for i, g in enumerate(got):
            if '_err' in g:
                errs[g['_err']] = errs.get(g['_err'], 0) + 1
                continue
            for s, v in g.items():
                if v is not None:
                    nrows.append(dict(budget=bt, structure=s, draw=i, score=v))
        if errs:
            print('  WARNING: %d of %d null draws failed: %s'
                  % (sum(errs.values()), len(got), errs), flush=True)
        if len(errs) and sum(errs.values()) == len(got):
            raise RuntimeError('every null draw failed: %s' % errs)
        # WRITE PER BUDGET. Accumulating both budgets and writing once at the
        # end means a crash in the second throws away the first -- 16.4 minutes
        # of finished work held in memory for no reason.
        pd.DataFrame(nrows).to_csv(
            OUT('walkforward_null_3slice.csv'), index=False)
        print('  null %s: %d draws in %.1f min' % (bt, len(got), (time.time() - t0) / 60),
              flush=True)
    N = pd.DataFrame(nrows)
    N.to_csv(OUT('walkforward_null_3slice.csv'), index=False)
    summ = []
    for (bt, s), g in N.groupby(['budget', 'structure']):
        real = float(O[(O.budget == bt) & (O.structure == s)].median_year_pct.iloc[0])
        v = g.score.values
        summ.append(dict(budget=bt, structure=s, real=real, n=len(v),
                         null_mean=float(v.mean()),
                         null_p95=float(np.percentile(v, 95)), null_max=float(v.max()),
                         pctile_of_real=float(100.0 * (v < real).mean()),
                         p_value=float((v >= real).mean()),
                         p_resolution=round(1.0 / len(v), 3)))
        print('  %-6s %-11s real %7.3f%%  null mean %7.3f%%  p95 %7.3f%%  max %7.3f%%  p=%.3f'
              % (bt, s, real, v.mean(), np.percentile(v, 95), v.max(),
                 (v >= real).mean()), flush=True)
    pd.DataFrame(summ).to_csv(
        OUT('walkforward_null_summary_3slice.csv'), index=False)
    return O


def stage_controls(jobs):
    """THE SLICE CONTROLS. What does the gate-3 cut buy, and what does the
    dominant slice buy?

    Four books, two axes, one walk each:

        ALLPASS                cut applied, one unit per member   (the result)
        SLICE_BALANCED         cut applied, one unit per SLICE
        NO_CUT                 no cut,      one unit per member
        NO_CUT_SLICE_BALANCED  no cut,      one unit per SLICE

    NO_CUT is the same walk with gate 3's bars not applied -- same field, same
    build years, same sizing, same budgets. The cut is the only difference, so
    the difference IS the cut.

    RECONSTRUCTED 2026-09-11. The module that produced the earlier
    walkforward_slicebalanced.csv / walkforward_nocut.csv is NOT in this repo --
    it was lost with the 11 Sep `git stash -u`. These definitions are written
    from what the labels can only mean plus the old run's member counts
    (SLICE_BALANCED carried ALLPASS's exact member count, 620/575, so it was a
    weighting and not a membership change; NO_CUT_SLICE_BALANCED carried
    NO_CUT's, 3485/3485). PER_SLICE_CUT IS DELIBERATELY ABSENT: gate 3's BARS
    ARE ABSOLUTE, so "the cut, per slice" is arithmetically the same set as the
    cut, yet the old run reported 168/129 against ALLPASS's 620/575. It
    therefore did something the repo no longer records -- a per-slice quantile
    or a top-N -- and guessing which would produce an authoritative-looking
    number from an invented definition.
    """
    T = pd.read_pickle(TRADES_F); M = pd.read_pickle(MARKS_F)
    print('  loaded %d trades, %d marks, %d strategies'
          % (len(T), len(M), T.sid.nunique()), flush=True)
    TY = trade_year_sums(M)
    ident = {y: y for y in YEARS}
    rows, rosters = [], []
    for nocut, names in ((False, {'ALLPASS': 'ALLPASS',
                                  'SLICE_BALANCED': 'SLICE_BALANCED'}),
                         (True,  {'ALLPASS': 'NO_CUT',
                                  'SLICE_BALANCED': 'NO_CUT_SLICE_BALANCED'})):
        for bt, dipb, dayb in BUDGETS:
            t0 = time.time()
            R = walk(T, TY, M, ident, dipb, dayb, list(names), nocut=nocut)
            print('  %s walk %s in %.1f min'
                  % ('NO_CUT' if nocut else 'CUT', bt, (time.time() - t0) / 60),
                  flush=True)
            for s, (k, cuts, x, dy) in R.items():
                lab = names[s]
                k.update(budget=bt, dip_budget=dipb, day_budget=dayb,
                         structure=lab, cut_applied=(not nocut), kind='control')
                rows.append(k)
                for c in cuts:
                    rosters.append(dict(budget=bt, structure=lab, step=c['step'],
                                        passers=c['passers'], members=c['members'],
                                        scale=c['scale'],
                                        build_dip95_pct=c['build_dip95_pct'],
                                        build_max_dd_pct=c['build_max_dd_pct'],
                                        build_worst_day_pct=c['build_worst_day_pct']))
                print('    %-6s %-22s median %7.3f%%  worst %7.3f%%  maxDD %5.2f%%  '
                      'PF %.2f  members %d/%d'
                      % (bt, lab, k['median_year_pct'], k['worst_year_pct'],
                         k['max_dd_pct'], k['profit_factor'],
                         k['members_step1'], k['members_step2']), flush=True)
            pd.DataFrame(rows).to_csv(
                OUT('walkforward_slicecontrols_3slice.csv'), index=False)
    pd.DataFrame(rows).to_csv(
        OUT('walkforward_slicecontrols_3slice.csv'), index=False)
    pd.DataFrame(rosters).to_csv(
        OUT('walkforward_slicecontrols_rosters_3slice.csv'), index=False)
    return pd.DataFrame(rows)


# ------------------------------------------------------------ TEAM-SIZE SWEEP
COARSE = (10, 15, 20, 25, 30, 40, 50, 75, 100, 'ALL')
N_RAND = 25


def rank_passers(P):
    """FIXED BEFORE LOOKING AT ANYTHING: Sortino, tie-break Calmar, measured on
    the build years. No other rule, and no reference to the trade years."""
    return list(P.sort_values(['sortino', 'calmar'], ascending=False,
                              kind='stable').sid)


def size_walk(T, TY, M, ymap, dipb, dayb, Ns, mode='top', rng=None):
    """One complete walk evaluated at many team sizes at once.

    The Book is built once per step over ALL passers, so each N is just a
    different membership vector -- ~50 ms including its own curve fit -- and a
    sweep of thirty sizes costs barely more than one.

    THE CURVE IS REFIT PER (STEP, N), ALWAYS ON BUILD YEARS. The fraction that
    feeds it is |net| / members, so a 10-member team and a 620-member team put
    the same net vote in completely different bins. Carrying one curve fitted on
    the full passer set across every N would compare sizes through a mapping
    that is wrong for most of them. Refitting stays inside the build block, so
    nothing here sees a trade year.
    """
    inv = {v: k for k, v in ymap.items()}
    acc = {n: dict(daily=[], days=[], build=[], trade=[], members=[],
                   cap=[], expo=[]) for n in Ns}
    for si, st in enumerate(STEPS):
        b0, b1 = st['build']; t0, t1 = st['trade']
        bsrc = [inv[y] for y in range(b0, b1 + 1)]
        tsrc = [inv[y] for y in range(t0, t1 + 1)]
        P, _ = cut(T, TY, bsrc)
        if len(P) < 10:
            raise RuntimeError('step %d: only %d passers' % (si + 1, len(P)))
        order = rank_passers(P)
        B = Book(M[M.sid.isin(order)], order)
        order = [c for c in order if c in set(B.members)]
        idx = {m: i for i, m in enumerate(B.members)}
        ybuild = np.isin(B.dyears, bsrc); ytrade = np.isin(B.dyears, tsrc)
        for n in Ns:
            k = len(order) if n == 'ALL' else min(int(n), len(order))
            if k < 2:
                continue
            mem = (order[:k] if mode == 'top'
                   else list(rng.choice(order, size=k, replace=False)))
            w = np.zeros(len(B.members), np.float32)
            for c in mem:
                w[idx[c]] = 1.0
            curve, _ = fit_curve(B, w, bsrc)
            d0, den, _, _, _, _ = B.series(w, curve)
            db = d0[ybuild]
            if not np.any(db):
                continue
            sc = scale_of(db, dipb, dayb)[0]
            d1, _, binds, worst, _, _ = B.series(w, curve, cap_pct=CAP_PCT,
                                                 per_unit=sc / den, den=den)
            a = acc[n]
            a['daily'].append(d1[ytrade] * sc)
            a['days'].append(B.udays[ytrade])
            a['members'].append(k)
            a['cap'].append(binds); a['expo'].append(worst)
            bs = pd.Series(db * sc).groupby(B.dyears[ybuild]).sum()
            ts = pd.Series(d1[ytrade] * sc).groupby(B.dyears[ytrade]).sum()
            a['build'].append(float(bs.median()))
            a['trade'].append(float(ts.median()))
    out = {}
    for n, a in acc.items():
        if len(a['daily']) != len(STEPS):
            continue
        x = np.concatenate(a['daily']); dy = np.concatenate(a['days'])
        global _MONTHS
        _MONTHS = dy
        k = kpis(x, pd.DatetimeIndex(dy).year.values)
        k['expectancy_pct_per_day'] = float(x.mean())
        k['members_step1'], k['members_step2'] = a['members']
        k['build_median_step1'], k['build_median_step2'] = a['build']
        k['trade_median_step1'], k['trade_median_step2'] = a['trade']
        bm = float(np.mean(a['build']))
        k['build_median_mean'] = bm
        k['retained_pct'] = float(100.0 * k['median_year_pct'] / bm) if bm else np.nan
        k['cap_bound_days'] = int(sum(a['cap']))
        k['max_ccy_exposure_pct'] = float(np.nanmax(a['expo']))
        out[n] = k
    return out


_SG = {}


def _init_size():
    S.load_costs()
    _SG['T'], _SG['M'] = _worker_tables()
    _SG['TY'] = trade_year_sums(_SG['M'])


def _size_null(args):
    ymap, dipb, dayb, Ns = args
    try:
        r = size_walk(_SG['T'], _SG['TY'], _SG['M'], ymap, dipb, dayb, Ns)
    except Exception as e:
        return {'_err': type(e).__name__ + ': ' + str(e)[:90]}
    return {n: (v['total_return_pct'], v['median_year_pct']) for n, v in r.items()}


def _size_rand(args):
    seed, dipb, dayb, Ns = args
    ident = {y: y for y in YEARS}
    try:
        r = size_walk(_SG['T'], _SG['TY'], _SG['M'], ident, dipb, dayb, Ns,
                      mode='rand', rng=np.random.default_rng(seed))
    except Exception as e:
        return {'_err': type(e).__name__ + ': ' + str(e)[:90]}
    return {n: (v['total_return_pct'], v['median_year_pct']) for n, v in r.items()}


def _sweep(jobs, Ns, dipb, dayb, n_null, n_rand, tag):
    ident = {y: y for y in YEARS}
    import multiprocessing as mp
    t0 = time.time()
    real = size_walk(_SG['T'], _SG['TY'], _SG['M'], ident, dipb, dayb, Ns)
    maps = ymaps(n_null)
    with mp.Pool(jobs, initializer=_init_size) as pool:
        nl = pool.map(_size_null, [(m, dipb, dayb, Ns) for m in maps], chunksize=1)
        rd = pool.map(_size_rand, [(20260910 + i, dipb, dayb, Ns)
                                   for i in range(n_rand)], chunksize=1)
    nerr = sum(1 for g in nl if '_err' in g); rerr = sum(1 for g in rd if '_err' in g)
    if nerr or rerr:
        print('  WARNING %s: %d null and %d random draws failed (e.g. %s)'
              % (tag, nerr, rerr,
                 next((g['_err'] for g in nl + rd if '_err' in g), '')), flush=True)
    print('  %s sweep: %d sizes, %d null, %d random in %.1f min'
          % (tag, len(Ns), n_null - nerr, n_rand - rerr, (time.time() - t0) / 60),
          flush=True)
    return real, [g for g in nl if '_err' not in g], [g for g in rd if '_err' not in g]


def fine_range(peak):
    """Walk by 1 across the two coarse steps either side of the peak: the
    coarse value below it plus one, up to the coarse value above it minus one.
    Peak 25 -> 21..29. Peak 40 -> 31..49."""
    vals = [v for v in COARSE if v != 'ALL']
    if peak == 'ALL':
        lo = vals[-1] + 1; hi = None
    else:
        i = vals.index(peak)
        lo = (vals[i - 1] + 1) if i > 0 else 2
        hi = (vals[i + 1] - 1) if i + 1 < len(vals) else None
    return lo, hi


def stage_size(jobs, n_null, n_rand):
    t00 = time.time()
    _init_size()
    rows, randrows = [], []

    def collect(real, nl, rd, Ns, stage, bt):
        for n in Ns:
            if n not in real:
                continue
            k = dict(real[n])
            nr = np.array([g[n][0] for g in nl if n in g])
            nm = np.array([g[n][1] for g in nl if n in g])
            rr = np.array([g[n][0] for g in rd if n in g])
            rm = np.array([g[n][1] for g in rd if n in g])
            for i, v in enumerate(rr):
                randrows.append(dict(budget=bt, N=n, draw=i, total_return_pct=float(v),
                                     median_year_pct=float(rm[i])))
            # EVERY COLUMN CARRIES ITS UNIT IN ITS NAME. The first version had a
            # `random_median_return` (total stitched return) sitting next to
            # `median_year_pct`, which reads as the same quantity and is not:
            # at N=ALL it printed 13.767% beside a 2.274% median year. Both
            # units are now reported and both are named.
            k.update(N=n, stage=stage, budget=bt, dip_budget=dipb0[bt],
                     null_n=len(nr),
                     null_mean_total_return=float(nr.mean()) if len(nr) else np.nan,
                     null_p95_total_return=float(np.percentile(nr, 95)) if len(nr) else np.nan,
                     null_p_total_return=float((nr >= k['total_return_pct']).mean()) if len(nr) else np.nan,
                     null_mean_median_year=float(nm.mean()) if len(nm) else np.nan,
                     null_p95_median_year=float(np.percentile(nm, 95)) if len(nm) else np.nan,
                     null_p_median_year=float((nm >= k['median_year_pct']).mean()) if len(nm) else np.nan,
                     random_n=len(rr),
                     random_median_total_return=float(np.median(rr)) if len(rr) else np.nan,
                     random_p95_total_return=float(np.percentile(rr, 95)) if len(rr) else np.nan,
                     random_median_year=float(np.median(rm)) if len(rm) else np.nan,
                     random_p95_median_year=float(np.percentile(rm, 95)) if len(rm) else np.nan,
                     beats_random_total_return=bool(len(rr) and k['total_return_pct'] > np.percentile(rr, 95)),
                     beats_random_median_year=bool(len(rm) and k['median_year_pct'] > np.percentile(rm, 95)))
            rows.append(k)

    dipb0 = {b: d for b, d, _ in BUDGETS}
    verdicts = {}
    for bt, dipb, dayb in BUDGETS:
        print('== team-size sweep, %s ==' % bt, flush=True)
        real, nl, rd = _sweep(jobs, list(COARSE), dipb, dayb, n_null, n_rand,
                              '%s coarse' % bt)
        collect(real, nl, rd, list(COARSE), 'coarse', bt)
        peak = max(real, key=lambda n: real[n]['total_return_pct'])
        print('  coarse peak: N=%s at %.2f%% total return'
              % (peak, real[peak]['total_return_pct']), flush=True)
        lo, hi = fine_range(peak)
        nmax = max(real[n]['members_step1'] for n in real)
        hi = (hi if hi is not None else nmax - 1)
        fine = [n for n in range(lo, hi + 1)
                if n not in [v for v in COARSE if v != 'ALL']]
        # The rule says walk by 1, so it walks by 1. A peak at ALL leaves no
        # coarse step above it and the range runs to the passer count -- ~519
        # sizes, ~35 min a budget. Affordable, so it is not silently thinned.
        if len(fine) > 600:
            print('  NOTE: fine range %d..%d truncated to 600 sizes' % (lo, hi), flush=True)
            fine = fine[:600]
        print('  fine walk: %d sizes, %d..%d' % (len(fine), lo, hi), flush=True)
        realf, nlf, rdf = _sweep(jobs, fine, dipb, dayb, n_null, n_rand,
                                 '%s fine' % bt)
        collect(realf, nlf, rdf, fine, 'fine', bt)
        # ---- DECISION RULE, fixed in advance
        cr = [r for r in rows if r['budget'] == bt and r['stage'] == 'coarse']
        fr = [r for r in rows if r['budget'] == bt and r['stage'] == 'fine']
        cw = max(cr, key=lambda r: r['total_return_pct'])
        verd = dict(budget=bt, coarse_peak_N=cw['N'],
                    coarse_peak_return=cw['total_return_pct'])
        if fr:
            fw = max(fr, key=lambda r: r['total_return_pct'])
            ok = (bool(fw['beats_random_total_return'])
                  and bool(fw['null_p_total_return'] < 0.05))
            verd.update(fine_peak_N=fw['N'], fine_peak_return=fw['total_return_pct'],
                        fine_beats_random=bool(fw['beats_random_total_return']),
                        fine_null_p=fw['null_p_total_return'], fine_replaces=ok,
                        answer_N=(fw['N'] if ok else cw['N']),
                        answer_return=(fw['total_return_pct'] if ok
                                       else cw['total_return_pct']))
            print('  fine peak N=%s at %.2f%% (beats random %s, null p=%.3f) -> '
                  'answer N=%s' % (fw['N'], fw['total_return_pct'],
                                   fw['beats_random_total_return'],
                                   fw['null_p_total_return'],
                                   verd['answer_N']), flush=True)
        verdicts[bt] = verd
    O = pd.DataFrame(rows)
    ordn = {v: i for i, v in enumerate(list(COARSE))}
    O['_o'] = O.N.map(lambda n: (0, ordn.get(n, 99)) if n in ordn else (1, n))
    O = O.sort_values(['budget', '_o']).drop(columns='_o')
    O.to_csv(OUT('walkforward_teamsize.csv'), index=False)
    pd.DataFrame(randrows).to_csv(
        OUT('walkforward_teamsize_random.csv'), index=False)
    pd.DataFrame(verdicts.values()).to_csv(
        OUT('walkforward_teamsize_verdict.csv'), index=False)
    print('TEAM-SIZE SWEEP DONE in %.1f min' % ((time.time() - t00) / 60), flush=True)
    return O, verdicts


# --------------------------------------------------- THREE WAYS TO SET THE SIZE
SIZINGS = (
    ('a_all_three_36', 3.6, 3.6, True,
     'DIP95 and actual maxDD against 3.6%, worst day against 3.6% -- as run'),
    ('b_risk_54_day_36', 5.4, 3.6, True,
     'DIP95 and actual maxDD against 5.4%, worst day against 3.6%'),
    ('c_actual_path_only', 3.6, 3.6, False,
     'actual maxDD and worst day against 3.6%; DIP95 measured, never binding'),
)


def stage_sizing(jobs):
    """ALLPASS under three sizing rules, same stitched 2016-2020, same walk.

    The scale is still set on the BUILD blocks in every case and never revisited
    -- only the rule that converts build-block risk into a scale changes. So the
    three columns differ by one decision and nothing else.
    """
    T = pd.read_pickle(TRADES_F); M = pd.read_pickle(MARKS_F)
    TY = trade_year_sums(M)
    ident = {y: y for y in YEARS}
    rows = []
    for tag, dipb, dayb, use_dip, desc in SIZINGS:
        t0 = time.time()
        R = walk(T, TY, M, ident, dipb, dayb, ['ALLPASS'], use_dip=use_dip)
        k, cuts, x, dy = R['ALLPASS']
        k.update(sizing=tag, description=desc, dip_budget=dipb, day_budget=dayb,
                 dip95_binding=use_dip,
                 binds_step1=cuts[0]['binds'], binds_step2=cuts[1]['binds'],
                 scale_step1=cuts[0]['scale'], scale_step2=cuts[1]['scale'],
                 build_dip95_step1=cuts[0]['build_dip95_pct'],
                 build_dip95_step2=cuts[1]['build_dip95_pct'],
                 build_max_dd_step1=cuts[0]['build_max_dd_pct'],
                 build_max_dd_step2=cuts[1]['build_max_dd_pct'],
                 build_worst_day_step1=cuts[0]['build_worst_day_pct'],
                 build_worst_day_step2=cuts[1]['build_worst_day_pct'],
                 trades_per_year=np.mean([c['trades_per_year'] for c in cuts]),
                 mean_open_positions=np.mean([c['mean_open_positions'] for c in cuts]),
                 mean_gross_exposure_pct=np.mean([c['mean_gross_exposure_pct'] for c in cuts]),
                 cap_bound_days=sum(c['cap_bound'] for c in cuts))
        rows.append(k)
        print('  %-20s median %6.3f%%  worst %6.3f%%  maxDD %5.2f%%  worstday %5.2f%%  '
              'DIP95 %5.2f%%  PF %.2f  Sortino %.2f  Calmar %.2f  binds %s/%s  (%.1f s)'
              % (tag, k['median_year_pct'], k['worst_year_pct'], k['max_dd_pct'],
                 k['worst_day_pct'], k['dip95_pct'], k['profit_factor'],
                 k['sortino'], k['calmar'], k['binds_step1'], k['binds_step2'],
                 time.time() - t0), flush=True)
    O = pd.DataFrame(rows)
    cols = ['sizing', 'description', 'dip_budget', 'day_budget', 'dip95_binding',
            'median_year_pct', 'worst_year_pct', 'max_dd_pct', 'worst_day_pct',
            'dip95_pct', 'profit_factor', 'sortino', 'calmar', 'mean_year_pct',
            'best_year_pct', 'total_return_pct', 'worst_month_pct', 'sharpe',
            'win_rate_pct', 'binds_step1', 'binds_step2', 'scale_step1',
            'scale_step2', 'build_dip95_step1', 'build_dip95_step2',
            'build_max_dd_step1', 'build_max_dd_step2', 'build_worst_day_step1',
            'build_worst_day_step2', 'trades_per_year', 'mean_open_positions',
            'mean_gross_exposure_pct', 'cap_bound_days', 'members_step1',
            'members_step2', 'trading_days']
    O = O[[c for c in cols if c in O.columns]]
    O.to_csv(OUT('walkforward_structures_sizing.csv'), index=False)
    print('  -> results/walkforward_structures_sizing.csv', flush=True)
    return O


# ============================================================ NULL 2: IDENTITY
# QUESTION: does build-year quality predict trade-year quality?
#
# The traded years are held at 2016-2020 and only the LINK between a strategy
# and its build-year record is broken: the sid labels on the build-year metrics
# are permuted, so a strategy passes the cut on someone else's record and then
# trades its own marks. Nothing about the calendar moves.
#
# This replaces the year-shuffled null, which is CONFOUNDED: permuting years
# also changes WHICH years get traded, and 2011-2015 is far richer than
# 2016-2020 for this field. Measured on the 25 draws: null score rises
# monotonically with the number of 2011-2015 years the draw happened to trade
# (3.36 / 5.29 / 6.84 / 7.66 at 1 / 2 / 3 / 4 rich years, correlation 0.377),
# and NONE of the 25 draws traded the real walk's composition of zero. Fitting
# score on rich-years-traded and reading it at zero gives a null of 2.31%
# against the real 2.27% -- p 0.52, not the 0.80 the raw comparison reports.
def _ident_one(args):
    seed, dipb, dayb, structures = args
    ident = {y: y for y in YEARS}
    try:
        rng = np.random.default_rng(seed)
        sids = np.array(sorted(set(_NG['T'].sid.astype(str))))
        perm = dict(zip(sids, rng.permutation(sids)))
        r = walk(_NG['T'], _NG['TY'], _NG['M'], ident, dipb, dayb, structures,
                 perm=perm)
    except Exception as e:
        return {'_err': type(e).__name__ + ': ' + str(e)[:90]}
    return {s: (r[s][0]['median_year_pct'], r[s][0]['total_return_pct'],
                r[s][0]['members_step1'], r[s][0]['members_step2'])
            for s in structures}


def stage_null_identity(jobs, n_null, structures):
    import multiprocessing as mp
    _init_null()
    real = {}
    ident = {y: y for y in YEARS}
    for bt, dipb, dayb in BUDGETS:
        R = walk(_NG['T'], _NG['TY'], _NG['M'], ident, dipb, dayb, structures)
        for s in structures:
            real[(bt, s)] = R[s][0]
    rows = []
    for bt, dipb, dayb in BUDGETS:
        t0 = time.time()
        args = [(20260911 + i, dipb, dayb, structures) for i in range(n_null)]
        with mp.Pool(jobs, initializer=_init_null) as pool:
            got = pool.map(_ident_one, args, chunksize=1)
        errs = [g['_err'] for g in got if '_err' in g]
        for i, g in enumerate(got):
            if '_err' in g:
                continue
            for s, v in g.items():
                rows.append(dict(budget=bt, structure=s, draw=i, median_year_pct=v[0],
                                 total_return_pct=v[1], members_step1=v[2],
                                 members_step2=v[3]))
        pd.DataFrame(rows).to_csv(
            OUT('walkforward_null_identity_3slice.csv'), index=False)
        if errs:
            print('  WARNING: %d of %d identity draws failed: %s'
                  % (len(errs), len(got), errs[0]), flush=True)
        print('  identity null %s: %d draws in %.1f min'
              % (bt, len(got) - len(errs), (time.time() - t0) / 60), flush=True)
    N = pd.DataFrame(rows)
    summ = []
    for (bt, s), g in N.groupby(['budget', 'structure']):
        v = g.median_year_pct.values
        rl = real[(bt, s)]['median_year_pct']
        summ.append(dict(budget=bt, structure=s, real_median_year=rl, n=len(v),
                         null_mean=float(v.mean()),
                         null_p95=float(np.percentile(v, 95)), null_max=float(v.max()),
                         pctile_of_real=float(100.0 * (v < rl).mean()),
                         p_value=float((v >= rl).mean()),
                         p_resolution=round(1.0 / len(v), 3),
                         mean_members_step1=float(g.members_step1.mean()),
                         mean_members_step2=float(g.members_step2.mean())))
        print('  %-6s %-11s real %7.3f%%  null mean %7.3f%%  p95 %7.3f%%  max %7.3f%%  p=%.3f'
              % (bt, s, rl, v.mean(), np.percentile(v, 95), v.max(),
                 (v >= rl).mean()), flush=True)
    pd.DataFrame(summ).to_csv(
        OUT('walkforward_null_identity_summary_3slice.csv'), index=False)
    return pd.DataFrame(summ)


# ======================================================= NULL 3: RANDOM ENTRY
# QUESTION: is ALLPASS's stitched 2016-2020 result better than nothing at all?
#
# Same strategies, same pairs, same directions, same holding lengths, same
# number of trades -- but each entry is moved to a random bar inside that
# strategy's own trade window instead of the bar its signals chose. If the
# entries carry no information the null reproduces the real book.
#
# RECOVERING THE UNIT SCALE. The engine's R is
#     r = dir x (price move) x units / RISK x atr_mult
# and neither units nor entry price was written to wf_trades. But an interior
# day's mark IS dir x (c[b] - c[b-1]) x k with k = units/RISK x atr_mult, so k
# is recoverable per trade as the median of mark / (dir x close change) over the
# days strictly between entry and exit. The first day is excluded because it
# carries the entry fill and the cost, the last because it carries the exit
# fill. One-day trades fall back to their strategy's median k.
#
# COSTS. cost_R = f x mult x |entry_px| x |units| / RISK = f x mult x c[entry] x
# k / atr_mult, so the same cost table, crisis multiplier and per-trade size are
# charged on the null entry as on the real one.
def _bars():
    """OHLC per pair, plus an ATR cache keyed by (pair, atr_len)."""
    out = {}
    for p in S.all_pairs():
        d = S.load_pair(p)
        out[p] = dict(idx=pd.DatetimeIndex(d.index),
                      o=d['open'].values.astype(float), h=d['high'].values.astype(float),
                      l=d['low'].values.astype(float), c=d['close'].values.astype(float))
    return out


_ATR = {}


def atr_of(BR, pair, alen):
    k = (pair, int(alen))
    if k not in _ATR:
        import l2lib as L
        b = BR[pair]
        _ATR[k] = L.P.atr(b['h'], b['l'], b['c'], int(alen))
    return _ATR[k]


def recover_k(T, M, field):
    """Per-trade entry bar, hold length and risk parameters.

    THE UNIT SCALE IS DERIVED, NOT ESTIMATED. The engine sizes
    units = RISK / (atr_mult x ATR) so a full stop is exactly 1R, and
    account-normalised R multiplies by atr_mult -- so the price-to-R factor is
        k = units/RISK x atr_mult = 1 / ATR(entry bar)
    with no reference to anything banked. An earlier version estimated k from
    mark / (dir x close change) on interior days; the ratio explodes when the
    close barely moves, and the median over one or two interior days does not
    save it -- simulated trades reached -152 R against a banked minimum of
    -1.43. Checked against the bank at each trade's REAL entry: correlation
    0.937 on the ip2 era, which is the only era this null rebuilds, with mean
    +0.097 against +0.062 and win rate 34.3% against 33.2%.
    """
    BR = _bars()
    K = T[['sid', 'tid', 'pair', 'entry', 'exit', 'era']].copy()
    K['sid'] = K.sid.astype(str); K['pair'] = K.pair.astype(str)
    parts = []
    for p_, g in K.groupby('pair', observed=True):
        pos = pd.Series(np.arange(len(BR[p_]['idx'])), index=BR[p_]['idx'])
        parts.append(g.assign(b0=pos.reindex(g.entry.values).values,
                              b1=pos.reindex(g['exit'].values).values))
    K = pd.concat(parts, ignore_index=True)
    D = M[['sid', 'tid', 'dir']].copy()
    D['sid'] = D.sid.astype(str)
    D = D.groupby(['sid', 'tid'], observed=True)['dir'].first().rename('dir')
    K = K.join(D, on=['sid', 'tid'])
    K = K[K.b0.notna() & K.b1.notna() & K['dir'].notna()]
    K['b0'] = K.b0.astype(int); K['b1'] = K.b1.astype(int)
    K['hold'] = (K.b1 - K.b0).clip(lower=1)
    F = field.set_index('sid')
    for col, src in (('atr_len', 'risk_atr_len'), ('atr_mult', 'risk_atr_mult'),
                     ('tp_mult', 'risk_tp_mult')):
        K[col] = K.sid.map(F[src].astype(float))
    K = K[K.atr_mult.notna() & (K.atr_mult > 0)].reset_index(drop=True)
    return K, BR


def random_entry_marks(K, BR, tsrc, rng):
    """Every trade-year trade rebuilt at a RANDOM entry bar: same pair, same
    direction, same stop and target distances, same maximum hold.

    THE EXITS ARE SIMULATED, NOT ASSUMED AWAY. A close-to-close hold of matched
    length gives the null unlimited adverse excursion while the real book stops
    out, which biases the comparison in the real book's favour. The initial stop
    (atr_mult x ATR at entry) and the first target (tp_mult x ATR) are applied as
    barriers against the high and low, STOP FIRST when one bar touches both.

    NOT reproduced: the breakeven and trailing phases that take over after the
    target is tagged, which let a few real winners run past the target -- the
    validation shows the real book reaching 5.18 R where the simulation caps at
    3.00. That clips the null's upside, so it makes the null EASIER for the real
    book to beat, not harder. Stated rather than hidden.
    """
    rows = []
    lo = pd.Timestamp('%d-01-01' % min(tsrc)); hi = pd.Timestamp('%d-12-31' % max(tsrc))
    for p, g in K.groupby('pair', observed=True):
        B = BR[p]; di = B['idx']; c = B['c']; hh = B['h']; ll = B['l']
        w = np.flatnonzero((di >= lo) & (di <= hi))
        if len(w) < 40:
            continue
        a, z = int(w[0]), int(w[-1])
        gg = g[(g.b0 >= a) & (g.b0 <= z)]
        if not len(gg):
            continue
        f = S.COSTS.get(p, 0.0)
        hold = np.clip(gg.hold.values.astype(int), 1, max(z - a - 2, 1))
        start = a + (rng.random(len(gg)) * np.maximum(z - a - hold, 1)).astype(int)
        for j, r in enumerate(gg.itertuples()):
            s0, L = int(start[j]), int(hold[j])
            L = min(L, z - s0)
            if L < 1:
                continue
            atr = atr_of(BR, p, r.atr_len)[s0]
            if not np.isfinite(atr) or atr <= 0:
                continue
            k = 1.0 / atr                      # derived, see recover_k
            ent = c[s0]; d = int(r.dir)
            stop = ent - d * r.atr_mult * atr
            tgt = ent + d * r.tp_mult * atr
            sh = hh[s0 + 1:s0 + L + 1]; sl = ll[s0 + 1:s0 + L + 1]
            hs = (sl <= stop) if d == 1 else (sh >= stop)
            ht = (sh >= tgt) if d == 1 else (sl <= tgt)
            is_ = int(np.argmax(hs)) if hs.any() else 10 ** 9
            it_ = int(np.argmax(ht)) if ht.any() else 10 ** 9
            if is_ <= it_:
                e_i, e_px = (is_, stop) if is_ < 10 ** 9 else (L - 1, c[s0 + L])
            else:
                e_i, e_px = it_, tgt
            n = e_i + 1
            px = np.empty(n)
            px[:n - 1] = c[s0 + 1:s0 + n]
            px[n - 1] = e_px
            mk = d * np.diff(np.concatenate(([ent], px))) * k
            mk[0] -= f * abs(ent) * k / r.atr_mult
            for q in range(n):
                rows.append((r.sid, p, di[s0 + 1 + q], d, np.float32(mk[q]), 0))
    return pd.DataFrame(rows, columns=['sid', 'pair', 'day', 'dir', 'mark', 'tid'])


_RG = {}


def _init_rand():
    """Each random-entry worker needs T, M, TY, and the per-trade unit scale K
    with the bars BR.

    WORKERS LOAD K AND BR FROM A PICKLE THE PARENT WROTE. THEY DO NOT REBUILD
    THEM. Building K means load_field() -- which reads the full gate2_tuned
    CSVs -- and recover_k() over 1.09M trades: a 6.9 GB transient per process,
    against a 1.4 GB steady state. Under spawn every worker paid that transient
    at the same moment; nine of them on a 16 GB Mac demanded ~70 GB, the
    compressor thrashed, watchdogd starved, and the kernel panicked -- 23:33
    and 11:45 on 11-12 Sep, both inside this stage. The parent builds K once,
    writes wf_randk<TAG>.pkl, and points workers at it through WF_RANDK.
    """
    S.load_costs()
    _RG['T'], _RG['M'] = _worker_tables()
    _RG['TY'] = trade_year_sums(_RG['M'])
    rk = os.environ.get('WF_RANDK', '')
    if rk:
        if not os.path.exists(rk):
            raise SystemExit('_init_rand: WF_RANDK points at a missing file: %s' % rk)
        _RG['K'], _RG['BR'] = pd.read_pickle(rk)
        return
    # THE PARENT PATH. The random-entry null must use the same field as the
    # run: this line was `load_field(SLICES3)` -- no field file, so the old None
    # default sent every random-entry null to the contaminated crosses_label
    # field regardless of what the run itself was launched with.
    ff = os.environ.get('WF_FIELD_FILE', '')
    if not ff:
        raise SystemExit('_init_rand: WF_FIELD_FILE is not set -- refusing to '
                         'guess the field for the random-entry null.')
    sls = tuple(x for x in os.environ.get('WF_SLICES', ','.join(SLICES3)).split(',') if x)
    F = load_field(sls, ff)
    _RG['K'], _RG['BR'] = recover_k(_RG['T'], _RG['M'], F)
    rk = OUT('wf_randk.pkl')
    pd.to_pickle((_RG['K'], _RG['BR']), rk)
    os.environ['WF_RANDK'] = rk
    print('  wrote %s for the workers (%.0f MB)' % (rk, os.path.getsize(rk) / 2**20),
          flush=True)


# THE TWO BOOKS THE RANDOM-ENTRY NULL CAN TEST. The cut book (ALLPASS) and the
# uncut book -- NO_CUT and its slice-balanced twin -- which after 12 Sep IS the
# book, and had never been null-tested. Same synthetic marks, same walk; the only
# difference is whether gate 3's bars are applied.
RAND_BOOKS = {False: {'ALLPASS': 'ALLPASS'},
              True:  {'ALLPASS': 'NO_CUT', 'SLICE_BALANCED': 'NO_CUT_SLICE_BALANCED'}}


def _rand_one(args):
    seed, dipb, dayb, nocut = (args + (False,))[:4]
    names = RAND_BOOKS[nocut]
    try:
        rng = np.random.default_rng(seed)
        M = _RG['M']; T = _RG['T']; TY = _RG['TY']
        parts = [M[M.day.dt.year <= 2015]]
        for st in STEPS:
            tsrc = list(range(st['trade'][0], st['trade'][1] + 1))
            parts.append(random_entry_marks(_RG['K'], _RG['BR'], tsrc, rng))
        MM = pd.concat(parts, ignore_index=True)
        MM['sid'] = MM.sid.astype(str); MM['pair'] = MM.pair.astype(str)
        MM['day'] = pd.to_datetime(MM.day)
        r = walk(T, TY, MM, {y: y for y in YEARS}, dipb, dayb, list(names), nocut=nocut)
        return {names[s]: (r[s][0]['median_year_pct'], r[s][0]['total_return_pct'])
                for s in names}
    except Exception as e:
        return {'_err': type(e).__name__ + ': ' + str(e)[:90]}


def stage_null_randomentry(jobs, n_null, nocut=False):
    import multiprocessing as mp
    names = RAND_BOOKS[nocut]
    tag = '_nocut' if nocut else ''
    _init_rand()
    print('  recovered unit scale for %d trades' % len(_RG['K']), flush=True)
    real = {}
    for bt, dipb, dayb in BUDGETS:
        R = walk(_RG['T'], _RG['TY'], _RG['M'], {y: y for y in YEARS}, dipb, dayb,
                 list(names), nocut=nocut)
        for s, lab in names.items():
            real[(bt, lab)] = R[s][0]
        print('  real %s: %s' % (bt, '  '.join('%s %.3f%%' % (lab, real[(bt, lab)]['median_year_pct'])
                                              for lab in names.values())), flush=True)
    rows = []
    for bt, dipb, dayb in BUDGETS:
        t0 = time.time()
        args = [(20260912 + i, dipb, dayb, nocut) for i in range(n_null)]
        with mp.Pool(jobs, initializer=_init_rand) as pool:
            got = pool.map(_rand_one, args, chunksize=1)
        errs = [g['_err'] for g in got if '_err' in g]
        for i, g in enumerate(got):
            if '_err' in g:
                continue
            for lab, (med, tot) in g.items():
                rows.append(dict(budget=bt, structure=lab, draw=i,
                                 median_year_pct=med, total_return_pct=tot))
        pd.DataFrame(rows).to_csv(
            OUT('walkforward_null_randomentry%s_3slice.csv' % tag), index=False)
        if errs:
            print('  WARNING: %d of %d random-entry draws failed: %s'
                  % (len(errs), len(got), errs[0]), flush=True)
        print('  random-entry null%s %s: %d draws in %.1f min'
              % (tag, bt, len(got) - len(errs), (time.time() - t0) / 60), flush=True)
    N = pd.DataFrame(rows)
    summ = []
    for (bt, lab), g in N.groupby(['budget', 'structure']):
        v = g.median_year_pct.values
        rl = real[(bt, lab)]['median_year_pct']
        summ.append(dict(budget=bt, structure=lab, real_median_year=rl,
                         n=len(v), null_mean=float(v.mean()),
                         null_p95=float(np.percentile(v, 95)),
                         null_max=float(v.max()),
                         pctile_of_real=float(100.0 * (v < rl).mean()),
                         p_value=float((v >= rl).mean()),
                         p_resolution=round(1.0 / len(v), 3)))
        print('  %-6s %-22s real %7.3f%%  random-entry mean %7.3f%%  p95 %7.3f%%  '
              'max %7.3f%%  p=%.3f' % (bt, lab, rl, v.mean(), np.percentile(v, 95),
                                       v.max(), (v >= rl).mean()), flush=True)
    pd.DataFrame(summ).to_csv(
        OUT('walkforward_null_randomentry%s_summary_3slice.csv' % tag), index=False)
    return pd.DataFrame(summ)


if __name__ == '__main__':
    main()
