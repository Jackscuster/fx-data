import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""THE 0f BOOK MACHINE ON THE `_r2` PATH, STREAMED (HANDOFF 0l).

At 273,780 strategies the book stage cannot hold all marks at once: one
strategy's trade-year marks are ~1,250 (pair, day) rows, so the full field is
~340 million rows per book variant. l2walkfwd.Book builds four sparse
(position x member) matrices, which at this width is ~10 GB before any
arithmetic.

WHY STREAMING IS EXACT HERE, not an approximation. HANDOFF 0l mandates
EVERYONE TRADES AT EQUAL WEIGHT, so the membership vector w is all ones, and
every quantity Book.net computes reduces to FOUR SUMS PER (pair, day):

    nl       = L  @ w  -> count of members long that row
    ns       = Sm @ w  -> count short
    sum_ml   = LM @ w  -> sum of the long members' marks
    sum_ms   = SM @ w  -> sum of the short members' marks

with w.sum() = the member count. Net votes, the active mask, the vote
fraction, the curve, the size, the sign and the row mark all follow from those
four numbers. So accumulating them incrementally over blocks of strategies
gives the identical book -- and `--stage prove` demonstrates it against the
shipped Book rather than asserting it.

The sparse-matrix machinery exists for the GREEDY TEAM SEARCH, where w changes
thousands of times and the matrices are amortised. There is no search here:
no picking and no weighting by past record, which is the rule that makes the
cheap path the correct one.

    python3 code/l2r2book.py --stage prove  --mode A
    python3 code/l2r2book.py --stage marks  --mode A --tag full
"""
import time, json, glob
import numpy as np, pandas as pd

import l2sweep as S
import l2tune as T
import l2walkfwd as W
import l2r2gate1 as G
import l2r2gate2 as G2
import l2ckpt

# THE FOUR BOOKS (HANDOFF 0f), as routing masks on the entry bar's Layer 1 label.
BOOKS = (('allon',        'always-on: every entry the strategy fired'),
         ('chop_trend',   'chop RANGING + trend TRENDING'),
         ('chop_ungated', 'chop RANGING + trend ungated'),
         ('chop_notrange', 'chop RANGING + trend NOT-RANGING'))
BUDGETS = ((3.6, 3.6), (5.4, 3.6))


class NetAccumulator:
    """The four per-(pair, day) sums, accumulated over blocks of strategies.

    Rows are addressed by an arithmetic index -- pair index x n_days + day index
    -- never by a string key. Today's third trap was a string index; this is the
    same lesson applied before it costs anything.
    """

    def __init__(self, pairs, days):
        self.pairs = list(pairs)
        self.pidx = {p: i for i, p in enumerate(self.pairs)}
        self.days = pd.DatetimeIndex(days)
        self.didx = {d: i for i, d in enumerate(self.days.values)}
        n = len(self.pairs) * len(self.days)
        self.nl = np.zeros(n, np.float64)
        self.ns = np.zeros(n, np.float64)
        self.sl = np.zeros(n, np.float64)
        self.ss = np.zeros(n, np.float64)
        self.n_members = 0

    def row(self, pair, day_i):
        return self.pidx[pair] * len(self.days) + day_i

    def add_member(self, rows, dirs, marks):
        """One strategy's marks. `rows` are precomputed arithmetic indices."""
        lo = dirs > 0
        np.add.at(self.nl, rows[lo], 1.0)
        np.add.at(self.ns, rows[~lo], 1.0)
        np.add.at(self.sl, rows[lo], marks[lo])
        np.add.at(self.ss, rows[~lo], marks[~lo])
        self.n_members += 1

    def net_quantities(self):
        """Exactly Book.net's intermediate quantities, for w = all ones."""
        nl, ns = self.nl, self.ns
        net = nl - ns
        act = np.abs(net) >= W.NET_MIN_VOTES
        f = np.abs(net) / max(float(self.n_members), 1.0)
        ml = np.divide(self.sl, nl, out=np.zeros_like(nl), where=nl > 0)
        ms = np.divide(self.ss, ns, out=np.zeros_like(ns), where=ns > 0)
        sgn = np.where(net > 0, 1.0, -1.0)
        mk = np.where(sgn > 0, ml, ms)
        return dict(nl=nl, ns=ns, net=net, act=act, f=f, mk=mk, sgn=sgn)


def marks_of(Y, mode, combo, ip, risk, sname, plan, code, years):
    """One tuned configuration's DAILY MARKS over `years`, in the exact
    convention l2walkfwd.engine_one uses and audit 18 guards.

    Returns (pair, day index within `years`, dir, mark) arrays. Routing is NOT
    applied here -- it is a mask on the entry bar, applied per book variant by
    the caller, so one engine pass serves all four books.
    """
    sc = Y.sc
    c1, c2, vol, base, ex = combo
    kwm = S.mode_kw(mode)
    am = float(risk['atr_mult'])
    alen = int(risk['atr_len'])
    import l2lib as L, l2engine as E
    t1 = L.KIND[c1] == 'TERNARY'
    t2 = L.KIND[c2] == 'TERNARY'
    # tid identifies a TRADE, not a mark row. Giving every row its own tid made
    # vote_from_next_day see 50,948 one-day trades and drop every one of them,
    # leaving the Book with no positions at all.
    out_p, out_d, out_dir, out_mk, out_rt, out_tid = [], [], [], [], [], []
    tid = 0
    for p in sc.pairs:
        o, h, l, c = sc.arr[p]
        ak = (alen, p)
        atr = sc._atr.get(ak)
        if atr is None:
            atr = L.P.atr(h, l, c, alen); sc._atr[ak] = atr
        g = sc.cache.get
        lt, st, lc, scr = g(c1, ip['c1'], p, sc.arr[p])[:4]
        _, _, c2lc, c2sc = g(c2, ip['c2'], p, sc.arr[p])[:4]
        vl, vs = g(vol, ip['vol'], p, sc.arr[p])[:2]
        bl = g(base, ip['base'], p, sc.arr[p])
        bl = bl[0] if isinstance(bl, tuple) else bl
        el, es = g(ex, ip['exit_ind'], p, sc.arr[p])[:2]
        b = sc.buf[p]
        nt, _, _, _ = E.run_bars(
            o, h, l, c, atr, bl, lt, st, lc, scr, c2lc, c2sc, vl, vs, el, es,
            sc._nosus[p], t1, t2, True, True, True,
            kwm['exit_on_c1_flip'], kwm['exit_on_base_cross'], kwm['exit_on_exit_ind'],
            False, int(plan), S.RISK, am, float(risk['tp_mult']),
            float(risk['trail_mult']), float(risk['trail_arm']), float(risk['be_pct']),
            1.5, 7, True, True,
            b['entry_bar'], b['exit_bar'], b['dir'], b['leg'], b['entry_px'],
            b['exit_px'], b['units'], b['r'], b['reason'], b['route'])
        if nt == 0:
            continue
        eb = b['entry_bar'][:nt]
        cst = (Y.cfrac[p] * Y.cmult[p][eb] * np.abs(b['entry_px'][:nt])
               * np.abs(b['units'][:nt]) / S.RISK) * am
        cl = Y.cl[p]
        yb = Y.yb[p]
        reg = sc.reg[p]
        dates = sc.dates[p]
        for j in range(nt):
            e = int(eb[j]); x = int(b['exit_bar'][j])
            if x < 0 or x < e:
                continue
            y0 = yb[e]
            if y0 < 0 or (G2.YEAR0 + y0) not in years:
                continue
            tid += 1
            d = float(b['dir'][j]); u = float(b['units'][j]); px = float(b['entry_px'][j])
            tot = float(b['r'][j]) * am
            prev = 0.0
            # THE ENTRY BAR'S LAYER 1 LABEL CODE, not a slice-specific boolean.
            # All four book variants are masks on this one number, so one engine
            # pass serves every book instead of four.
            lab = int(reg[e])
            for bar in range(e, x + 1):
                if yb[bar] < 0 or (G2.YEAR0 + yb[bar]) not in years:
                    prev = tot if bar == x else d * (cl[bar] - px) * u / S.RISK * am
                    continue
                cum = tot if bar == x else d * (cl[bar] - px) * u / S.RISK * am
                inc = cum - prev - (cst[j] if bar == e else 0.0)
                prev = cum
                out_p.append(p); out_d.append(dates[bar]); out_dir.append(d)
                out_mk.append(inc); out_rt.append(lab); out_tid.append(tid)
    return (np.array(out_p), np.array(out_d), np.array(out_dir, np.float64),
            np.array(out_mk, np.float64), np.array(out_rt, np.int64),
            np.array(out_tid, np.int64))


# ==========================================================================
# THE FOUR BOOKS AS MASKS ON THE ENTRY BAR'S LABEL (HANDOFF 0f)
# ==========================================================================
RANGING = S.REGIME_CODE['ranging']
TRENDING = S.REGIME_CODE['trending']


def book_mask(book, sname, lab):
    """Which mark rows this book keeps, from the entry bar's label code.

    Unlabelled bars carry -1 and are never invented into a regime: 96.3% of
    OANDA bars carry a Layer 1 label and the rest are calendar mismatches
    against the H.10 panel the labels were built on (LAYER1_INTERFACE.md 2).
    They are kept only by the always-on book, which is what always-on means.
    """
    if book == 'allon':
        return np.ones(len(lab), bool)
    if sname == 'chop':
        return lab == RANGING                     # every gated book: chop is RANGING
    if book == 'chop_trend':
        return lab == TRENDING
    if book == 'chop_ungated':
        # UNGATED means no regime gate on the trend leg at all, unlabelled bars
        # included -- that is what "ungated" says, and it is the point of having
        # this book beside the gated one.
        return np.ones(len(lab), bool)
    if book == 'chop_notrange':
        # NOT-RANGING is a POSITIVE claim about the label, so it cannot be
        # asserted of a bar that has no label. Unlabelled bars (-1) are excluded
        # here and kept only by the always-on book: LAYER1_INTERFACE.md 2 says
        # the 3.7% of OANDA bars with no label are calendar mismatches, and
        # inventing a regime for them would put trades in a state nobody
        # measured. The residual cells trend-in-range and neither ARE admitted,
        # because they are measured labels that merely are not "ranging".
        return (lab >= 0) & (lab != RANGING)
    raise SystemExit('unknown book %r' % book)


class _Vec:
    """Stands in for one of Book's sparse matrices. `M @ w` on an all-ones w is
    exactly the accumulated column sum, so the shipped code can take its four
    products without a matrix existing."""

    def __init__(self, col):
        self.col = col

    def __matmul__(self, w):
        return self.col.astype(np.float32)


class StreamedBook:
    """A Book-shaped object backed by NetAccumulator.

    The point of this class is that it lets the SHIPPED scoring code run
    unchanged -- l2walkfwd.Book.series, fit_curve and kpis all go through
    `self.L @ w`, `self.Sm @ w`, `self.LM @ w`, `self.SM @ w` and the per-day
    index arrays, and nothing else. So the book is scored by the same code that
    scored every earlier book in this project, on inputs that were accumulated
    a block of strategies at a time rather than held at once.
    """

    def __init__(self, acc, n_members):
        live = (acc.nl + acc.ns) > 0
        rows = np.flatnonzero(live)
        nd = len(acc.days)
        self.pair = np.array([acc.pairs[r // nd] for r in rows])
        self.day = pd.DatetimeIndex(acc.days.values[(rows % nd).astype(int)])
        self.L = _Vec(acc.nl[rows]); self.Sm = _Vec(acc.ns[rows])
        self.LM = _Vec(acc.sl[rows]); self.SM = _Vec(acc.ss[rows])
        self.members = list(range(n_members))
        self.udays, self.dpos = np.unique(self.day.values, return_inverse=True)
        self.nd = len(self.udays)
        self.dyears = pd.DatetimeIndex(self.udays).year.values
        ccy = sorted({c for pp in set(self.pair) for c in (pp[:3], pp[3:])})
        self.ccy = ccy
        cidx = {c: i for i, c in enumerate(ccy)}
        self.nc = len(ccy)
        self.bc = np.array([cidx[pp[:3]] for pp in self.pair])
        self.qc = np.array([cidx[pp[3:]] for pp in self.pair])
        import scipy.sparse as sp
        self.Dagg = sp.csr_matrix((np.ones(len(rows), np.float32),
                                   (self.dpos, np.arange(len(rows)))),
                                  shape=(self.nd, len(rows)))
        self.posyears = self.day.year.values
        self.rows = rows

    # the shipped implementations, bound to this object
    net = W.Book.net
    series = W.Book.series


def stage_prove_series(mode='A', n=5):
    """THE DECISIVE PROOF: the same members scored by the SHIPPED series()
    through the shipped Book and through StreamedBook, daily series compared.

    The earlier proof compared the four accumulated sums. This one runs the
    whole scoring path -- net votes, the fitted curve, the currency cap, the
    daily series and the KPI block -- and compares what the book actually
    earns, which is the number that would be quoted.
    """
    G.manifest_check()
    S.load_costs()
    opts = S.mode_opts(S.slot_options(), mode)
    combos = G.stratified(opts, n)[:n]
    Y = G2.Years(cap=8000)
    years = set(range(2016, 2021))
    rows = []
    for sname, plan, code in S.SLICES:
        allm = []
        for k, cb in enumerate(combos):
            cfg = G2.axial(mode, cb, sname)
            ip, risk = cfg[0][1], cfg[0][2]
            pr, dy, dr, mk, _rt, tid = marks_of(Y, mode, cb, ip, risk, sname, plan, code, years)
            if not len(pr):
                continue
            allm.append(pd.DataFrame(dict(sid='%s|%s|%d' % (mode, sname, k), pair=pr,
                                          day=pd.to_datetime(dy), dir=dr.astype(np.int8),
                                          mark=mk.astype(np.float32), tid=tid.astype(np.int32))))
        if not allm:
            continue
        M = pd.concat(allm, ignore_index=True)
        members = sorted(M.sid.unique())
        B = W.Book(M, members)
        w = np.ones(len(members), np.float32)
        curve, _Cb = W.fit_curve(B, w, set(B.dyears.tolist()))   # fit_curve returns (curve, table)
        x_b, den_b, binds_b, worst_b, _sz, _f = B.series(w, curve, cap_pct=3.6, per_unit=1.0)

        # the streamed side, on the Book's own voted grid
        Mv = W.vote_from_next_day(M.copy(), np.zeros(len(M), np.int64))[0] \
            if not W.VOTE_ON_ENTRY_DAY else M
        days = np.unique(B.day.values)
        didx = {d: i for i, d in enumerate(days)}
        acc = NetAccumulator(sorted(set(B.pair)), days)
        for _sid, g in Mv.groupby('sid', sort=True):
            dd = g.day.values.astype('datetime64[ns]')
            ok = np.array([d in didx for d in dd])
            if not ok.any():
                continue
            gg = g[ok]
            r = np.array([acc.row(pp, didx[d]) for pp, d in
                          zip(gg.pair.values, gg.day.values.astype('datetime64[ns]'))],
                         dtype=np.int64)
            acc.add_member(r, gg['dir'].values.astype(np.float64),
                           gg.mark.values.astype(np.float64))
        SB = StreamedBook(acc, len(members))
        ws = np.ones(len(members), np.float32)
        curve_s, _Cs = W.fit_curve(SB, ws, set(SB.dyears.tolist()))
        x_s, den_s, binds_s, worst_s, _s2, _f2 = SB.series(ws, curve_s, cap_pct=3.6, per_unit=1.0)
        # align both daily series on their own day grids
        db = pd.Series(x_b, index=pd.DatetimeIndex(B.udays))
        ds = pd.Series(x_s, index=pd.DatetimeIndex(SB.udays))
        j = db.align(ds, join='outer', fill_value=0.0)
        dmax = float(np.abs(j[0].values - j[1].values).max())
        kb = W.kpis(j[0].values, pd.DatetimeIndex(j[0].index).year.values)
        ks = W.kpis(j[1].values, pd.DatetimeIndex(j[1].index).year.values)
        rows.append(dict(mode=mode, slice=sname, members=len(members),
                         positions_shipped=len(B.pair), positions_streamed=len(SB.pair),
                         days_shipped=B.nd, days_streamed=SB.nd,
                         den_shipped=den_b, den_streamed=den_s,
                         cap_binds_shipped=binds_b, cap_binds_streamed=binds_s,
                         max_abs_daily_diff=dmax,
                         median_year_shipped=kb['median_year_pct'],
                         median_year_streamed=ks['median_year_pct'],
                         dip95_shipped=kb['dip95_pct'], dip95_streamed=ks['dip95_pct'],
                         pf_shipped=kb['profit_factor'], pf_streamed=ks['profit_factor'],
                         within_float32=int(dmax < 1e-5)))
    D = pd.DataFrame(rows)
    out = os.path.join(ROOTOUT, 'r2book_series_equals_shipped_mode%s.csv' % mode)
    D.to_csv(out, index=False)
    print(D.to_string(index=False), flush=True)
    print('  SHIPPED series() THROUGH BOTH BOOKS: worst |daily diff| %.3g -> %s'
          % (float(D.max_abs_daily_diff.max()), os.path.basename(out)), flush=True)
    assert len(D) and bool(D.within_float32.all()), 'THE STREAMED BOOK SCORES DIFFERENTLY'
    return D


from numba import njit


@njit(cache=False)
def _book_acc(nt, eb, xb, dirv, epx, units, rtot, cst, am, risk,
              cl, dayidx, lab_arr, pair_off, keeptab, NL, NS, SL, SS):
    """Accumulate one (pair, configuration) straight into the book arrays.

    No mark rows are ever materialised: at 273,780 strategies x 20 picks a
    python mark table is hundreds of millions of rows, and that is the whole
    reason the book stage could not be run the way 0f ran it at 45,139.

    THE VOTE-TIMING RULE IS INSIDE THE KERNEL (HANDOFF section 3, 15 Sep).
    A position may not vote on its fill day: the voted rows are e+1..x, the
    fill day's increment is CARRIED into the first voted row, and a trade that
    fills and closes on the same day has no day of exposure, no vote, and its
    cost is dropped -- exactly what l2walkfwd.vote_from_next_day does to a
    mark table, done here without building one.

    `keeptab[book, label+1]` is the routing mask of each book; a trade is kept
    or skipped per book on its ENTRY bar's label, and the bars are walked once
    for all books that keep it.
    """
    nbook = keeptab.shape[0]
    for j in range(nt):
        e = eb[j]
        x = xb[j]
        if x < 0 or x <= e:          # x == e: filled and closed same day, no vote
            continue
        lab = lab_arr[e] + 1
        any_book = False
        for b in range(nbook):
            if keeptab[b, lab] != 0:
                any_book = True
                break
        if not any_book:
            continue
        d = dirv[j]
        u = units[j]
        px = epx[j]
        tot = rtot[j] * am
        prev = 0.0
        carry = 0.0
        for bar in range(e, x + 1):
            if bar == x:
                cum = tot
            else:
                cum = d * (cl[bar] - px) * u / risk * am
            inc = cum - prev
            if bar == e:
                inc -= cst[j]
            prev = cum
            if bar == e:
                carry = inc          # the fill day does not vote; its mark rides forward
                continue
            v = inc + carry
            carry = 0.0
            di = dayidx[bar]
            if di < 0:
                continue             # outside this step's trade year
            row = pair_off + di
            for b in range(nbook):
                if keeptab[b, lab] == 0:
                    continue
                if d > 0.0:
                    NL[b, row] += 1.0
                    SL[b, row] += v
                else:
                    NS[b, row] += 1.0
                    SS[b, row] += v


def keep_table(sname):
    """(n_books, 5) mask indexed by label+1: -1 unlabelled, 0 trending,
    1 ranging, 2 trend-in-range, 3 neither."""
    tab = np.zeros((len(BOOKS), 5), np.int8)
    for bi, (bk, _d) in enumerate(BOOKS):
        for lab in (-1, 0, 1, 2, 3):
            m = book_mask(bk, sname, np.array([lab]))
            tab[bi, lab + 1] = 1 if bool(m[0]) else 0
    return tab


class BookArrays:
    """The four per-(pair, day) sums for every book, over one step's trade year."""

    def __init__(self, pairs, days):
        self.pairs = list(pairs)
        self.poff = {p: i * len(days) for i, p in enumerate(self.pairs)}
        self.days = pd.DatetimeIndex(days)
        n = len(self.pairs) * len(self.days)
        self.NL = np.zeros((len(BOOKS), n), np.float64)
        self.NS = np.zeros((len(BOOKS), n), np.float64)
        self.SL = np.zeros((len(BOOKS), n), np.float64)
        self.SS = np.zeros((len(BOOKS), n), np.float64)
        self.n_members = np.zeros(len(BOOKS), np.int64)

    def as_accumulator(self, bi):
        a = NetAccumulator(self.pairs, self.days.values)
        a.nl = self.NL[bi]; a.ns = self.NS[bi]
        a.sl = self.SL[bi]; a.ss = self.SS[bi]
        a.n_members = int(self.n_members[bi])
        return a


def accumulate_strategy(Y, mode, combo, ip, risk, sname, plan, years_idx, BA, keeptab):
    """One tuned configuration into BookArrays, for the bars in `years_idx`.

    `years_idx` maps a bar to its day index inside the step's trade year, or -1.
    """
    sc = Y.sc
    c1, c2, vol, base, ex = combo
    kwm = S.mode_kw(mode)
    am = float(risk['atr_mult']); alen = int(risk['atr_len'])
    import l2lib as L, l2engine as E
    t1 = L.KIND[c1] == 'TERNARY'; t2 = L.KIND[c2] == 'TERNARY'
    for p in sc.pairs:
        o, h, l, c = sc.arr[p]
        atr = sc._atr.get((alen, p))
        if atr is None:
            atr = L.P.atr(h, l, c, alen); sc._atr[(alen, p)] = atr
        g = sc.cache.get
        lt, st, lc, scr = g(c1, ip['c1'], p, sc.arr[p])[:4]
        _, _, c2lc, c2sc = g(c2, ip['c2'], p, sc.arr[p])[:4]
        vl, vs = g(vol, ip['vol'], p, sc.arr[p])[:2]
        bl = g(base, ip['base'], p, sc.arr[p])
        bl = bl[0] if isinstance(bl, tuple) else bl
        el, es = g(ex, ip['exit_ind'], p, sc.arr[p])[:2]
        b = sc.buf[p]
        nt, _, _, _ = E.run_bars(
            o, h, l, c, atr, bl, lt, st, lc, scr, c2lc, c2sc, vl, vs, el, es,
            sc._nosus[p], t1, t2, True, True, True,
            kwm['exit_on_c1_flip'], kwm['exit_on_base_cross'], kwm['exit_on_exit_ind'],
            False, int(plan), S.RISK, am, float(risk['tp_mult']),
            float(risk['trail_mult']), float(risk['trail_arm']), float(risk['be_pct']),
            1.5, 7, True, True,
            b['entry_bar'], b['exit_bar'], b['dir'], b['leg'], b['entry_px'],
            b['exit_px'], b['units'], b['r'], b['reason'], b['route'])
        if nt == 0:
            continue
        eb = b['entry_bar'][:nt]
        cst = (Y.cfrac[p] * Y.cmult[p][eb] * np.abs(b['entry_px'][:nt])
               * np.abs(b['units'][:nt]) / S.RISK) * am
        _book_acc(nt, eb, b['exit_bar'][:nt], b['dir'][:nt].astype(np.float64),
                  b['entry_px'][:nt], b['units'][:nt], b['r'][:nt], cst, am, S.RISK,
                  Y.cl[p], years_idx[p], sc.reg[p].astype(np.int64),
                  BA.poff[p], keeptab, BA.NL, BA.NS, BA.SL, BA.SS)


def winner_config(mode, combo, sname, ci):
    """Resolve a banked winner INDEX back to its (ip, risk). The axial list is
    deterministic given (mode, combo, slice), which is why the bank stores an
    index instead of 300 bytes of json per pick."""
    cfg = G2.axial(mode, combo, sname)
    assert 0 <= ci < len(cfg), 'winner index %d out of range for %s' % (ci, sname)
    return cfg[ci][1], cfg[ci][2]


def stage_prove(mode='A', n=6, seed=11):
    """THE STREAMED BOOK EQUALS THE LOADED BOOK.

    Build the same members both ways -- through l2walkfwd.Book, which is the
    shipped kernel with its sparse matrices and its vote-timing rule, and
    through NetAccumulator one strategy at a time -- and require every
    quantity Book.net produces to agree to 1e-9.
    """
    G.manifest_check()
    S.load_costs()
    opts = S.mode_opts(S.slot_options(), mode)
    combos = G.stratified(opts, n)[:n]
    Y = G2.Years(cap=8000)
    years = set(range(2016, 2021))      # the five trade years of the 0f walk

    rows = []
    for sname, plan, code in S.SLICES:
        allm = []
        for k, cb in enumerate(combos):
            cfg = G2.axial(mode, cb, sname)
            ip, risk = cfg[0][1], cfg[0][2]        # defaults: the proof is about the BOOK
            pr, dy, dr, mk, _rt, tid = marks_of(Y, mode, cb, ip, risk, sname, plan, code, years)
            if not len(pr):
                continue
            sid = '%s|%s|%d' % (mode, sname, k)
            allm.append(pd.DataFrame(dict(sid=sid, pair=pr, day=pd.to_datetime(dy),
                                          dir=dr.astype(np.int8),
                                          mark=mk.astype(np.float32),
                                          tid=tid.astype(np.int32))))
        if not allm:
            continue
        M = pd.concat(allm, ignore_index=True)
        members = sorted(M.sid.unique())
        # --- the shipped kernel
        B = W.Book(M, members)
        w = np.ones(len(members), np.float32)
        nl_b, ns_b = B.L @ w, B.Sm @ w
        ml_b = np.divide(B.LM @ w, nl_b, out=np.zeros_like(nl_b), where=nl_b > 0)
        ms_b = np.divide(B.SM @ w, ns_b, out=np.zeros_like(ns_b), where=ns_b > 0)
        # --- the streamed accumulator, over the SAME rows the Book kept
        # (Book applies the vote-timing shift, so the comparison is made on the
        # Book's own (pair, day) grid rather than on the raw marks)
        days = np.unique(B.day.values)
        acc = NetAccumulator(sorted(set(B.pair)), days)
        Mv = W.vote_from_next_day(M.copy(), np.zeros(len(M), np.int64))[0] \
            if not W.VOTE_ON_ENTRY_DAY else M
        # PROMOTE ONCE, AFTER the shipped vote-timing step. vote_from_next_day
        # rebuilds the frame and casts marks to float32, so float32 is baked
        # into the shipped pipeline and no accumulator can undo it. The 1e-9
        # claim is therefore about the ACCUMULATOR'S ARITHMETIC given identical
        # inputs: both sides sum the same post-vote values in float64, and the
        # only thing that can differ is summation order.
        Mv = Mv.copy()
        Mv['m64'] = Mv['mark'].values.astype(np.float64)
        didx = {d: i for i, d in enumerate(days)}
        for sid, g in Mv.groupby('sid', sort=True):
            keep = g.day.values.astype('datetime64[ns]')
            ok = np.array([d in didx for d in keep])
            if not ok.any():
                continue
            gg = g[ok]
            r = np.array([acc.row(p, didx[d]) for p, d in
                          zip(gg.pair.values, gg.day.values.astype('datetime64[ns]'))],
                         dtype=np.int64)
            acc.add_member(r, gg['dir'].values.astype(np.float64),
                           gg.m64.values)
        q = acc.net_quantities()
        # map the Book's position order onto the accumulator's arithmetic rows
        # int64 EXPLICITLY. An empty or mixed list makes np.array float64 and
        # numpy then refuses it as an index -- arithmetic indices are only an
        # improvement over string keys if their dtype is nailed down.
        brow = np.array([acc.row(p, didx[d]) for p, d in
                         zip(B.pair, B.day.values.astype('datetime64[ns]'))],
                        dtype=np.int64)
        # THE EXACT float64 REFERENCE. The shipped Book stores marks as float32
        # (mk = M.mark.values.astype(np.float32), and its four sparse matrices
        # are float32), so no accumulator can agree with it to 1e-9 on the
        # marks -- 1.2e-07 is float32 epsilon at these magnitudes, and it is a
        # property of the existing kernel, not of streaming. The equality is
        # therefore proven twice: against a float64 groupby of the SAME voted
        # rows, which is exact, and against the shipped Book, which agrees to
        # its own storage precision. The streamed path carries float64 and is
        # the more precise of the two.
        ref = Mv.copy()
        ref['row'] = [acc.row(p, didx[d]) for p, d in
                      zip(ref.pair.values, ref.day.values.astype('datetime64[ns]'))]
        ref = ref[ref.row.isin(set(brow.tolist()))]
        gl = ref[ref['dir'] > 0].groupby('row')
        gs = ref[ref['dir'] <= 0].groupby('row')
        nrow = len(acc.nl)
        r_nl = np.zeros(nrow); r_ns = np.zeros(nrow)
        r_sl = np.zeros(nrow); r_ss = np.zeros(nrow)
        r_nl[gl.size().index.values] = gl.size().values
        r_ns[gs.size().index.values] = gs.size().values
        r_sl[gl.m64.sum().index.values] = gl.m64.sum().values
        r_ss[gs.m64.sum().index.values] = gs.m64.sum().values
        e_nl = float(np.abs(q['nl'][brow] - r_nl[brow]).max())
        e_ns = float(np.abs(q['ns'][brow] - r_ns[brow]).max())
        e_sl = float(np.abs(acc.sl[brow] - r_sl[brow]).max())
        e_ss = float(np.abs(acc.ss[brow] - r_ss[brow]).max())
        exact = max(e_nl, e_ns, e_sl, e_ss)

        d_nl = float(np.abs(q['nl'][brow] - nl_b).max())
        d_ns = float(np.abs(q['ns'][brow] - ns_b).max())
        d_ml = float(np.abs(q['mk'][brow] * (q['sgn'][brow] > 0)
                            - ml_b * (q['sgn'][brow] > 0)).max())
        d_ms = float(np.abs(np.divide(acc.ss, acc.ns, out=np.zeros_like(acc.ns),
                                      where=acc.ns > 0)[brow] - ms_b).max())
        rows.append(dict(mode=mode, slice=sname, members=len(members),
                         positions=len(B.pair),
                         vs_exact_float64_max_diff=exact,
                         exact_to_1e9=int(exact < 1e-9),
                         vs_shipped_book_n_long=d_nl, vs_shipped_book_n_short=d_ns,
                         vs_shipped_book_mark_long=d_ml, vs_shipped_book_mark_short=d_ms,
                         votes_exact=int(max(d_nl, d_ns) == 0.0),
                         marks_within_float32=int(max(d_ml, d_ms) < 1e-6)))
    D = pd.DataFrame(rows)
    out = os.path.join(ROOTOUT, 'r2book_streamed_equals_loaded_mode%s.csv' % mode)
    D.to_csv(out, index=False)
    print(D.to_string(index=False), flush=True)
    print('  STREAMED BOOK vs the EXACT float64 reference: worst |diff| %.3g (required < 1e-9)'
          % float(D.vs_exact_float64_max_diff.max()), flush=True)
    print('  STREAMED BOOK vs the SHIPPED Book: votes exact on every row; marks worst |diff| %.3g '
          '= float32 epsilon, which is the Book\'s own storage precision -> %s'
          % (float(D[['vs_shipped_book_mark_long', 'vs_shipped_book_mark_short']].max().max()),
             os.path.basename(out)), flush=True)
    assert len(D), 'no slice produced a book'
    assert bool(D.exact_to_1e9.all()), 'STREAMED BOOK DIFFERS FROM THE EXACT float64 REFERENCE'
    assert bool(D.votes_exact.all()), 'VOTE COUNTS DIFFER FROM THE SHIPPED BOOK'
    assert bool(D.marks_within_float32.all()), 'MARKS DIFFER FROM THE SHIPPED BOOK BY MORE THAN float32'
    return D


if __name__ == '__main__':
    stage = G.opt('--stage', str, 'prove')
    mode = G.opt('--mode', str, 'A')
    if stage == 'prove':
        stage_prove(mode, n=G.opt('--n', int, 6))
    elif stage == 'prove_series':
        stage_prove_series(mode, n=G.opt('--n', int, 5))
    else:
        raise SystemExit('unknown stage %s' % stage)
