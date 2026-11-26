"""ITEM 3 -- THE BOOKS, AND THE FIVE BOOK GATES. PROTOCOL.md AMENDMENT 1.

Jack's correction: nothing is counted out for being small or for working on
only some pairs. A sleeve is one algorithm on one pair, admission is light
(A2), and the only pass or fail is on the combined BOOK (A3, B1 to B5).

FOUR FAMILIES, each built on the admission years and scored on the other
years, both rotations:

  a_declared    every admitted sleeve from the 6 published, the 10 hand-built,
                and A and B
  b_per_pair    for each pair, the top K algorithms on THAT PAIR'S admission
                years, K swept 1 to 200
  c_all_pairs   the top K algorithms across all pairs, each trading only the
                pairs it was admitted on, K swept 10 to 5,000
  d_combined    a, plus the best of b and c

EACH BOOK TWO WAYS
  separate      every sleeve its own position at equal risk, 1/N each
  voting        Jack's 4 September rule: N signals on a pair are ONE position
                with N votes, and cost is charged on changes in the NET
                position only

THE TWO COSTS ARE CHARGED ON ONE CONVENTION so the difference between them is
netting and nothing else. Both charge half the round-trip spread on each
change in notional, at the price of the bar the change happens on:

  separate   sum over sleeves of  f/2 * px[bar] * |change in that sleeve's notional|
  voting     f/2 * px[bar] * |change in the pair's NET notional|

`nnfxproto.cost_R`, the protocol's own charge, instead puts the whole round
trip on the ENTRY price. The separate book's cost is reported under BOTH
conventions so the choice is visible; the difference is price drift between
entry and exit, not a different spread.

THE K SWEEP IS FREE BECAUSE TOP-K IS NESTED. Every weight is 1/N, so an
unweighted running sum divided by N at each K is the book at that K exactly.
One pass over the ranked sleeves, snapshotted at every K.
"""
import os, sys, time, json, argparse
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
ROOT = os.path.dirname(_HERE)
ROOTOUT = os.path.join(ROOT, 'results')
sys.path.insert(0, ROOT)

import numpy as np
import pandas as pd
import nnfxproto as P
import nnfxsrc3 as S3
import nnfxcands as CL
import nnfxsleeves as BK
import nnfxbook2 as B2
import r2reads as RR
import l2sweep as S

OUT = os.path.join(ROOTOUT, 'nnfx')
BOUT = os.path.join(OUT, 'books')
os.makedirs(BOUT, exist_ok=True)

ROTATIONS = (('R1', 'h1', 'h2'), ('R2', 'h2', 'h1'))
SHARE_GRID = (0.25, 0.40, 0.60, 0.80, 1.00, np.inf)
SHARE_DECLARED = 0.25
K_PER_PAIR = (1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 200)
K_ALL = (10, 20, 50, 100, 200, 500, 1000, 2000, 3500, 5000)
B5_DAILY = RR.INT_DAILY          # 0.036 -- Jack's 3.6% daily
B5_TRAIL = RR.INT_TRAIL          # 0.054 -- Jack's 5.4% trailing
TARGET_PCT = 12.0
N_NULL = 20
JPY_CHF = None                   # filled by cells()


# ======================= the world ======================================
class World(object):
    """The union day index and, per pair, its bar->day map, close and spread."""

    def __init__(self, pairs):
        self.pairs = list(pairs)
        ds = sorted(set().union(*[set(pd.DatetimeIndex(P.pair_data(p).index))
                                  for p in self.pairs]))
        self.dates = pd.DatetimeIndex(ds)
        dmap = {d: i for i, d in enumerate(ds)}
        self.nd = len(ds)
        self.year = np.asarray(self.dates.year)
        self.gl, self.px, self.f, self.nb, self.half = {}, {}, {}, {}, {}
        for p in self.pairs:
            d = P.pair_data(p)
            idx = pd.DatetimeIndex(d.index)
            self.gl[p] = np.array([dmap[t] for t in idx], np.int64)
            self.px[p] = d['close'].to_numpy(float)
            self.f[p] = float(S.COSTS.get(p, 0.0))
            self.nb[p] = len(idx)
            # half the round-trip spread at each bar's price, precomputed:
            # a book of 40,000 sleeves multiplies by this once per sleeve
            self.half[p] = self.f[p] / 2.0 * self.px[p]

    def mask(self, years):
        return np.isin(self.year, list(years))


def parts(C, p, cache=None):
    """One sleeve's realised gross daily R, its notional opened and closed per
    bar, and its signed notional per bar -- all three already divided by the
    engine's risk denominator and put in the 1.5-ATR R unit, so a caller only
    has to multiply by half the round-trip spread and the bar's price.

    THE OPEN/CLOSE ARRAYS ARE LEG-WISE AND THE SIGNED ARRAY IS CUMULATIVE,
    and that difference is the whole point. A sleeve traded on its own pays
    for every leg it opens and closes even when two of its own legs overlap
    in opposite directions; inside the voting machine those same two legs net
    against each other like any other pair of votes. The first version
    computed the separate cost from the cumulative array too, which quietly
    let a sleeve net against itself.
    """
    key = (P.WORLD, P.cand_id(C), p)
    if cache is not None and key in cache:
        return cache[key]
    nb = len(P.pair_data(p))
    am = float(C['risk']['atr_mult'])
    sc = am / (P.RISK_DOLLARS * P.RISK_UNIT_ATR)
    res = P.E.run(P.assemble(p, C), amb=P.amb_cached(p), **P._kw(C))
    gross = np.zeros(nb); lego = np.zeros(nb); legc = np.zeros(nb)
    delta = np.zeros(nb + 1)
    n = res['_n']
    if n:
        eb = np.clip(res['entry_bar'][:n].astype(np.int64), 0, nb - 1)
        xb = np.clip(res['exit_bar'][:n].astype(np.int64), 0, nb - 1)
        gross_leg = res['r'][:n] * am / P.RISK_UNIT_ATR
        sz = res['dir'][:n].astype(float) * np.abs(res['units'][:n]) * sc
        np.add.at(gross, xb, gross_leg)
        np.add.at(lego, eb, np.abs(sz))
        np.add.at(legc, xb, np.abs(sz))
        np.add.at(delta, eb, sz)
        np.add.at(delta, xb + 1, -sz)
    out = dict(gross=gross, lego=lego, legc=legc,
               sn=np.cumsum(delta)[:nb], trades=int(n))
    if cache is not None:
        cache[key] = out
    return out


class Acc(object):
    """Unweighted running sums, IN EACH PAIR'S OWN BAR SPACE. Divided by N and
    mapped to the union day index at every snapshot.

    THE FIRST VERSION ACCUMULATED STRAIGHT ONTO THE UNION INDEX with
    `np.add.at`, and it does not scale. A book of 40,000 sleeves would have
    made 120,000 unbuffered scatter-adds over 7,000-element index arrays, and
    it also cached every sleeve's four arrays -- 224 KB each, which at the
    ~550,000 distinct sleeves one world's full sweep touches is about 120 GB.
    Accumulating per pair makes every add a plain vector add of 7,000 floats,
    and the mapping happens 276 times instead of 550,000.
    """

    def __init__(self, W):
        self.W = W
        self.gross = {p: np.zeros(W.nb[p]) for p in W.pairs}
        self.csep = {p: np.zeros(W.nb[p]) for p in W.pairs}
        self.net = {p: np.zeros(W.nb[p]) for p in W.pairs}
        self.n = 0
        self.touched = set()
        self.members = []

    def add(self, C, p, tag):
        pt = parts(C, p)
        self.gross[p] += pt['gross']
        self.csep[p] += self.W.half[p] * (pt['lego'] + pt['legc'])
        self.net[p] += pt['sn']
        self.n += 1
        self.touched.add(p)
        self.members.append((tag, p, pt['trades']))

    def series(self):
        """-> (separate, voting, cost_sep, cost_vote) at equal risk, 1/N.

        `gl` holds one bar per calendar date for a pair, so the indices are
        unique and plain fancy-index += is correct here; np.add.at is only
        needed for duplicate indices.
        """
        W = self.W
        g = np.zeros(W.nd); cs = np.zeros(W.nd); cv = np.zeros(W.nd)
        if not self.n:
            return g, g.copy(), cs, cv
        inv = 1.0 / self.n
        for p in self.touched:
            gl = W.gl[p]
            g[gl] += self.gross[p] * inv
            cs[gl] += self.csep[p] * inv
            d = np.abs(np.diff(self.net[p] * inv, prepend=0.0))
            cv[gl] += W.half[p] * d
        return g - cs, g - cv, cs, cv


# ======================= scoring ========================================
def light(a, m):
    """What a null run needs: totals only, no bootstrap, no dip95."""
    x = a[m]
    if not len(x):
        return dict(R=0.0, R_ex1=0.0, R_ex5=0.0)
    s = np.sort(x)
    tot = float(x.sum())
    return dict(R=tot, R_ex1=tot - float(s[-1]),
                R_ex5=tot - float(s[-5:].sum()))


def full(a, dates, m):
    """Everything a REPORTED book carries, including B5."""
    x = a[m]
    s = pd.Series(x, index=dates[m])
    st = B2.stats(s)
    if not st:
        return {}
    bind = st['dip_binding']; wd = st['worst_day_R']
    sc = min(B5_TRAIL * 100.0 / bind if bind > 0 else np.inf,
             B5_DAILY * 100.0 / wd if wd and wd > 0 else np.inf)
    st['b5_scale'] = float(sc) if np.isfinite(sc) else np.nan
    st['b5_pct_per_year'] = (st['R_per_year'] * float(sc)
                             if np.isfinite(sc) else np.nan)
    sv = np.sort(x)
    st['R_ex1'] = st['R_total'] - float(sv[-1])
    st['R_ex5'] = st['R_total'] - float(sv[-5:].sum())
    if np.isfinite(sc):
        pr = B2.prop(s, sc, rules='internal')
        st['b5_eval_days'] = pr['eval_days_to_pass']
        st['b5_eval_breached'] = pr['eval_breached']
        st['b5_funded_breached'] = pr['funded_breached']
        st['b5_funded_pct_per_year'] = pr['funded_return_pct_per_year']
    return st


# ======================= selection ======================================
def cells():
    """Source 3's four cells, unchanged: 15 pairs without JPY or CHF / 13 with."""
    allp = list(S.all_pairs())
    a = [p for p in allp if 'JPY' not in p and 'CHF' not in p]
    b = [p for p in allp if 'JPY' in p or 'CHF' in p]
    assert len(a) == 15 and len(b) == 13
    return a, b


def admitted(bank, w, share):
    """(N, 28) bool: PROTOCOL.md A2 on window `w` at this share threshold."""
    return BK.admit_mask(bank['%s__R' % w], bank['%s__R_ex_best_day' % w],
                         bank['%s__best_trade' % w], bank['%s__trades' % w],
                         share=share)


def rank_per_pair(bank, adm, aw, pi, kmax):
    """The pair's admitted algorithms, best first by admission-window R."""
    ok = np.nonzero(adm[:, pi])[0]
    if not len(ok):
        return ok
    r = bank['%s__R' % aw][ok, pi]
    return ok[np.argsort(-r)][:kmax]


def rank_all(bank, adm, aw, kmax):
    """Algorithms ranked by total admission-window R over the pairs they were
    admitted on. An algorithm admitted nowhere is not a candidate."""
    R = bank['%s__R' % aw]
    sc = np.where(adm, R, 0.0).sum(axis=1)
    npair = adm.sum(axis=1)
    ok = np.nonzero(npair > 0)[0]
    return ok[np.argsort(-sc[ok])][:kmax]


# ======================= one world, every book ==========================
def build(bank, cands, W, declared=None, light_only=True, verbose=False):
    """-> list of row dicts, one per (rotation, family, K, share, mode)."""
    rows = []
    cellA, cellB = cells()
    pairs = W.pairs
    col = {p: i for i, p in enumerate(pairs)}
    for (rot, aw, sw) in ROTATIONS:
        smask = W.mask(BK.H1Y if sw == 'h1' else BK.H2Y)
        for share in SHARE_GRID:
            adm = admitted(bank, aw, share)
            # ---- family b: top K per pair, nested in K
            order = {p: rank_per_pair(bank, adm, aw, col[p], max(K_PER_PAIR))
                     for p in pairs}
            acc = Acc(W)
            for r in range(max(K_PER_PAIR)):
                for p in pairs:
                    o = order[p]
                    if r < len(o):
                        acc.add(S3.mkcand(cands[o[r]]), p,
                                'S%d' % o[r])
                if (r + 1) in K_PER_PAIR:
                    rows += _emit(acc, W, smask, rot, aw, sw,
                                  'b_per_pair', r + 1, share, light_only)
            # ---- family c: top K algorithms, each on its admitted pairs
            ra = rank_all(bank, adm, aw, max(K_ALL))
            acc = Acc(W)
            for i, j in enumerate(ra):
                for p in pairs:
                    if adm[j, col[p]]:
                        acc.add(S3.mkcand(cands[j]), p, 'S%d' % j)
                if (i + 1) in K_ALL:
                    rows += _emit(acc, W, smask, rot, aw, sw,
                                  'c_all_pairs', i + 1, share, light_only)
            # ---- family a: the declared 18 (real world only)
            if declared is not None:
                acc = Acc(W)
                for (nm, C, _src, _cp) in declared:
                    for p in pairs:
                        d = P.fast_per_pair(C, p, BK.PERIODS)[aw]
                        if BK.adm_ok(dict(d)) and \
                                (d['best_trade'] / d['R'] < share
                                 if d['R'] > 0 else False):
                            acc.add(C, p, nm)
                rows += _emit(acc, W, smask, rot, aw, sw,
                              'a_declared', acc.n, share, light_only)
            if verbose:
                print('    %s share=%.2f done' % (rot, share), flush=True)
    return rows


def _emit(acc, W, smask, rot, aw, sw, fam, K, share, light_only):
    """One row per mode.

    WITH light_only=True THIS FUNCTION IS EXACTLY WHAT IT WAS and must stay
    so: the 20 matched null runs call build(..., light_only=True) and the
    workers that had not yet started when the full-stats branch was added
    import the newer file. Identical behaviour on that branch is what makes
    the two halves of the batch comparable.
    """
    sep, vote, csep, cvote = acc.series()
    out = []
    # THE COSTS ARE SUMMED UNDER THE SCORING MASK, not over all history. The
    # frames start in 1999 and the first version summed the whole series,
    # which made the book's cost look half again as large as cost_R's on the
    # same trades.
    cs = float(csep[smask].sum()); cv = float(cvote[smask].sum())
    for mode, a in (('separate', sep), ('voting', vote)):
        d = dict(rotation=rot, admit_window=aw, score_window=sw, family=fam,
                 K=K, share=share, mode=mode, sleeves=acc.n,
                 cost_sep_total=cs, cost_vote_total=cv,
                 cost_saved_by_netting=cs - cv)
        d.update(light(a, smask))
        if not light_only:
            st = full(a, W.dates, smask)
            d.update({k: v for k, v in st.items()
                      if k not in ('R_ex1', 'R_ex5')})
        out.append(d)
    return out


# ======================= the real run ===================================
def _bank_and_cands():
    pairs, bank = BK.load_bank('real')
    cands, _src, _m = CL.load()
    n = bank['h1__R'].shape[0]
    assert n == len(cands), 'bank holds %d algorithms, the list has %d' \
        % (n, len(cands))
    return pairs, bank, cands


def run_real(verbose=True, light_only=True, out='books_sweep_real.csv'):
    S.load_costs(os.environ.get('FX_COST_TABLE',
                                os.path.join(ROOTOUT, 'cost_table_h22.csv')))
    S3.init_space()
    pairs, bank, cands = _bank_and_cands()
    W = World(pairs)
    D = BK.declared_sleeves()
    t0 = time.time()
    rows = build(bank, cands, W, declared=D, light_only=light_only,
                 verbose=verbose)
    R = pd.DataFrame(rows)
    R.to_csv(os.path.join(BOUT, out), index=False)
    print('  %s %d rows in %.1f min' % (out, len(R), (time.time() - t0) / 60),
          flush=True)
    return R


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--real', action='store_true')
    ap.add_argument('--real-full', action='store_true')
    a = ap.parse_args()
    if a.real:
        run_real()
    if a.real_full:
        run_real(light_only=False, out='books_full_real.csv')
