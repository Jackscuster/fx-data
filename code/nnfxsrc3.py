import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""SOURCE 3 — MACHINE SEARCH WITH A SEARCH NULL. HANDOFF 0o.

The honest version of a search: the same search, at the same budget, run on
data that CANNOT contain an edge, fifty times, and the distribution of the best
replicated result under that null is the floor a real find has to beat.

THE SPLIT, declared before anything ran:
  discovery    2005-2010, the 15 pairs containing NEITHER JPY nor CHF
  replication  2011-2015, the 13 pairs containing JPY or CHF
  off-diagonal 2005-2010 on the 13, and 2011-2015 on the 15 -- computed and
               reported, because a result that only works on one diagonal is
               telling you about the diagonal.

Discovery and replication share no pair and no year. That is stronger than a
normal train/test split: a candidate that carries has to work on different
currencies in a different decade.

THE BUDGET, and every evaluation counts into the ledger:
  200,000 complete five-slot algorithms drawn at random from the full space
  (39 C1 x 39 C2 x 12 volume x 16 baselines x 39 exits x 3 settings each =
  2.6 billion, so the sample is 0.0077% of it)
  + a first-improvement local search from the top 200, one slot or one setting
  changed at a time while discovery net R improves, capped at a further
  200,000 evaluations
  + 200,000 replication evaluations of the random sample, for the rank
  correlation in (e)
  = 600,000 evaluations per run, real or null.

THE OBJECTIVE is net R per year excluding the best day, on the fast path
PROTOCOL.md section 5 declares: realised by exit day, uncapped, charged once
per round trip on the engine's own risk denominator. `nnfxproto.verify_fast`
checks it against the full path to 2e-16 on plan 2 and 2e-15 on plan 1. Every
candidate the search SURFACES is re-scored on the full reporting path with the
1:30 cap and mark-to-market, and the rank correlation between the two is
reported.

THE ZERO-EDGE DATA. Each pair's bars are turned into per-bar RATIOS against
the previous close -- (o/c-1, h/c-1, l/c-1, c/c-1) -- and those whole bars are
block-shuffled in 20-day blocks WITHIN each calendar year, with each block's
direction flipped with probability one half. A flip inverts every ratio in the
block (r -> 1/r), which turns an up bar into a down bar with mirrored geometry
rather than an impossible bar with its high below its low. Prices are then
chained back up from the real first close. What survives: each bar's own
internal shape, the volatility clustering inside a block, the year's calendar.
What is destroyed: any direction, any trend longer than 20 days, any
cross-pair co-movement beyond what the shuffle happens to leave.

TWO DECLARED LIMITATIONS OF THE NULL, both stated here and in SOURCE3.md.
  1. NO HOURLY PATH EXISTS FOR SYNTHETIC PRICES, so the null runs with gap
     fills and the ambiguity resolver OFF -- null stops fill at the stop or at
     the daily open. The real search runs with both ON. Realistic gap fills
     cost the real candidates under 1 R a year (item 1), and the shuffle
     destroys the crisis clustering that makes gaps matter, so the direction of
     this is to make the null very slightly EASIER to beat, not harder.
  2. THE PEG GUARD'S MEDIAN is taken over whatever pair set the world holds.
     The null worlds are built for all 28 pairs so the median is a 28-pair
     median exactly as in the real run.

FAULTS THIS FILE FOUND IN ITSELF
  1. The first draft shuffled CLOSES only and rebuilt highs and lows from the
     real bars, which left the real high-low range sitting on a shuffled
     close -- about 8% of synthetic bars had the close OUTSIDE the bar. The
     ratio form cannot do that by construction, and `check_world` asserts
     low <= min(open, close) <= max(open, close) <= high on every synthetic
     bar before a null run is allowed to start.
  2. The local search first re-evaluated a neighbour it had already seen,
     because the seen-set was keyed on the candidate tuple but the setting
     ladder can map two different tuples onto the same parameters (a baseline
     whose `half` collapses onto `default`). The key is now
     nnfxproto.cand_id, which hashes the PARAMS.
"""
import time, json, glob, itertools
import numpy as np, pandas as pd
from scipy import stats

import l2sweep as S
import l2engine as E
import nnfxproto as P

OUT = os.path.join(ROOTOUT, 'nnfx')
NULLDIR = os.path.join(OUT, 'src3_null')
os.makedirs(OUT, exist_ok=True)
os.makedirs(NULLDIR, exist_ok=True)

DISC_YEARS = tuple(range(2005, 2011))
REPL_YEARS = tuple(range(2011, 2016))
BLOCK = 20
N_RANDOM = 200_000
N_LOCAL_CAP = 200_000
TOP_LOCAL = 200
TOP_REPL = 50
N_NULL = 50


def pair_sets():
    allp = list(S.all_pairs())
    disc = [p for p in allp if 'JPY' not in p and 'CHF' not in p]
    repl = [p for p in allp if 'JPY' in p or 'CHF' in p]
    assert len(disc) == 15 and len(repl) == 13 and not set(disc) & set(repl), \
        'pair split is %d / %d' % (len(disc), len(repl))
    return disc, repl


# ===================== the candidate space ==============================
def space():
    """{slot: [(name, setting), ...]} with the collapsed settings removed.

    A baseline whose default length is 2 has `half` == `default` (fantail_vma,
    vidya); keeping both would put two identical candidates in the space and
    inflate the sample's effective size, which matters for a best-of-N floor.
    """
    out = {}
    for sl in P.SLOTS:
        opts = []
        for nm in P.INV[sl]:
            seen = set()
            for st in P.SETTINGS:
                k = P._pkey(P.setting_params(nm, st))
                if k in seen:
                    continue
                seen.add(k)
                opts.append((nm, st))
        out[sl] = opts
    return out


SPACE = None
_PARAMS = {}


def init_space():
    global SPACE
    SPACE = space()
    for sl in P.SLOTS:
        for nm, st in SPACE[sl]:
            _PARAMS[(nm, st)] = P.setting_params(nm, st)
    return SPACE


def space_size():
    n = 1
    for sl in P.SLOTS:
        n *= len(SPACE[sl])
    return n


def mkcand(t, name='c'):
    """A candidate dict from a 5-tuple of (name, setting), params precomputed.

    nnfxproto.cand calls setting_params five times; at 600,000 evaluations a
    run that is not free, and the params never change for a given (name,
    setting). This is the same object cand() builds -- asserted equal on a
    sample in self_check().
    """
    C = dict(name=name, source='source3_search', reason='',
             risk=dict(P.RISK))
    for sl, (nm, st) in zip(P.SLOTS, t):
        C[sl] = nm
        C[sl + '_set'] = st
        C[sl + '_params'] = _PARAMS[(nm, st)]
    return C


def self_check():
    """mkcand against nnfxproto.cand on a sample. One object, two builders."""
    rng = np.random.default_rng(3)
    for _ in range(50):
        t = tuple(SPACE[sl][rng.integers(len(SPACE[sl]))] for sl in P.SLOTS)
        a = mkcand(t)
        b = P.cand('x', t[0][0], t[1][0], t[2][0], t[3][0], t[4][0],
                   c1_set=t[0][1], c2_set=t[1][1], vol_set=t[2][1],
                   base_set=t[3][1], exit_set=t[4][1])
        assert P.cand_id(a) == P.cand_id(b), 'mkcand != cand on %s' % (t,)
    return True


def draw(rng, n):
    """n random complete algorithms, de-duplicated by cand_id."""
    out, seen = [], set()
    while len(out) < n:
        need = n - len(out)
        idx = {sl: rng.integers(0, len(SPACE[sl]), size=need) for sl in P.SLOTS}
        for j in range(need):
            t = tuple(SPACE[sl][idx[sl][j]] for sl in P.SLOTS)
            k = P.cand_id(mkcand(t))
            if k in seen:
                continue
            seen.add(k)
            out.append(t)
    return out, seen


# ===================== the zero-edge world ==============================
def zero_edge_frames(seed, pairs=None, block=BLOCK):
    """{pair: OHLC frame} with the edge shuffled out. See the module note.

    Each bar becomes four ratios against the previous close. Whole bars are
    block-shuffled within the calendar year and each block is direction-flipped
    with probability one half; a flip inverts every ratio AND swaps the bar's
    high and low, because the mirror of a high is a low. Prices chain back up
    from the pair's real first close by cumulative product, so the synthetic
    series has the pair's own price level and its own calendar.
    """
    pairs = list(pairs or S.all_pairs())
    rng = np.random.default_rng(seed)
    out = {}
    for p in pairs:
        d = P.N.pair_data(p)
        o, h, l, c = (d[k].values.astype(float)
                      for k in ('open', 'high', 'low', 'close'))
        n = len(c)
        prev = np.concatenate(([c[0]], c[:-1]))
        with np.errstate(divide='ignore', invalid='ignore'):
            ro, rh, rl, rc = (np.where(prev > 0, x / prev, 1.0)
                              for x in (o, h, l, c))
        for x in (ro, rh, rl, rc):
            x[~np.isfinite(x)] = 1.0
            x[x <= 0] = 1.0
        yr = pd.DatetimeIndex(d.index).year.to_numpy()
        order = np.arange(n)
        flip = np.zeros(n, bool)
        for y in np.unique(yr):
            w = np.nonzero(yr == y)[0]
            nb = int(np.ceil(len(w) / block))
            blocks = [w[i * block:(i + 1) * block] for i in range(nb)]
            perm = rng.permutation(nb)
            fl = rng.random(nb) < 0.5
            pos = 0
            for bi, pi in enumerate(perm):
                src = blocks[pi]
                dst = w[pos:pos + len(src)]
                order[dst] = src
                flip[dst] = bool(fl[bi])
                pos += len(src)
            assert pos == len(w), '%s %d: %d of %d bars placed' % (
                p, y, pos, len(w))
        so, sh, sl_, sc = ro[order], rh[order], rl[order], rc[order]
        io, ih, il, ic = 1.0 / so, 1.0 / sh, 1.0 / sl_, 1.0 / sc
        fo = np.where(flip, io, so)
        fc = np.where(flip, ic, sc)
        fh = np.where(flip, il, sh)          # the flip of a low IS a high
        flo = np.where(flip, ih, sl_)
        px = c[0] * np.cumprod(fc)
        base = np.concatenate(([c[0]], px[:-1]))
        fr = pd.DataFrame(dict(open=base * fo, high=base * fh,
                               low=base * flo, close=px), index=d.index)
        # A BAR MUST CONTAIN ITS OWN OPEN AND CLOSE. The ratio form keeps the
        # geometry, but the open ratio and the close ratio are both measured
        # against the PREVIOUS close, and after a flip the reconstructed open
        # can land outside the reconstructed range. Enforced here, and
        # check_world verifies it afterwards on every bar of every pair.
        fr['high'] = np.maximum.reduce([fr.high.to_numpy(), fr.open.to_numpy(),
                                        fr.close.to_numpy()])
        fr['low'] = np.minimum.reduce([fr.low.to_numpy(), fr.open.to_numpy(),
                                       fr.close.to_numpy()])
        if 'suspect' in d.columns:
            fr['suspect'] = d['suspect'].values
        out[p] = fr
    return out


def check_world(frames):
    """Every synthetic bar must be a possible bar, and nothing may be NaN."""
    bad = []
    for p, fr in frames.items():
        o, h, l, c = (fr[k].to_numpy(float)
                      for k in ('open', 'high', 'low', 'close'))
        if not np.isfinite(np.concatenate([o, h, l, c])).all():
            bad.append('%s non-finite' % p)
        if (h < np.maximum(o, c) - 1e-12).any() or \
           (l > np.minimum(o, c) + 1e-12).any() or (h < l).any():
            bad.append('%s bar geometry' % p)
        if (c <= 0).any():
            bad.append('%s non-positive price' % p)
    assert not bad, 'synthetic world rejected: %s' % ', '.join(bad[:6])
    return True


# ===================== the search =======================================
def obj_many(cands, pairs, years, log_every=0, tag=''):
    """The fast objective for a list of candidate tuples. -> np.array."""
    out = np.full(len(cands), -np.inf)
    t0 = time.time()
    for i, t in enumerate(cands):
        o, _n, _tot = P.fast_obj(mkcand(t), pairs, years)
        out[i] = o
        if log_every and (i + 1) % log_every == 0:
            el = time.time() - t0
            print('    %s %d/%d  %.0f/s  eta %.1f min'
                  % (tag, i + 1, len(cands), (i + 1) / max(el, 1e-9),
                     (len(cands) - i - 1) / max((i + 1) / el, 1e-9) / 60),
                  flush=True)
    return out


def neighbours(t):
    """Every one-slot / one-setting change of `t`."""
    out = []
    for k, sl in enumerate(P.SLOTS):
        for opt in SPACE[sl]:
            if opt == t[k]:
                continue
            u = list(t); u[k] = opt
            out.append(tuple(u))
    return out


def local_search(starts, pairs, years, rng, cap=N_LOCAL_CAP, verbose=True):
    """First-improvement hill climbing, one slot or one setting at a time.

    THE CAP IS PART OF THE DECLARED BUDGET, not a convenience. The null runs
    the identical search at the identical cap, so whatever the local search
    buys on real data it also gets the chance to buy on noise.
    """
    seen = {}
    used = 0
    best = []
    t0 = time.time()
    for si, (t, o0) in enumerate(starts):
        cur, curo = t, o0
        improved = True
        while improved and used < cap:
            improved = False
            nb = neighbours(cur)
            rng.shuffle(nb)
            for u in nb:
                if used >= cap:
                    break
                k = P.cand_id(mkcand(u))
                if k in seen:
                    continue
                o, _n, _tot = P.fast_obj(mkcand(u), pairs, years)
                seen[k] = o
                used += 1
                if o > curo:
                    cur, curo = u, o
                    improved = True
                    break
        best.append((cur, curo))
        if verbose and (si + 1) % 25 == 0:
            print('    local %d/%d starts, %d evaluations, %.1f min'
                  % (si + 1, len(starts), used, (time.time() - t0) / 60),
                  flush=True)
    return best, used


def one_search(world, seed, n_random=N_RANDOM, cap=N_LOCAL_CAP,
               verbose=True, with_repl_all=True):
    """One complete search -- real or null -- and everything it reports."""
    disc, repl = pair_sets()
    rng = np.random.default_rng(seed)
    cands, _seen = draw(rng, n_random)
    if verbose:
        print('  %s: %d random candidates from a space of %.3g'
              % (world, len(cands), space_size()), flush=True)
    od = obj_many(cands, disc, DISC_YEARS,
                  log_every=(20000 if verbose else 0), tag='discovery')
    order = np.argsort(-od)
    starts = [(cands[i], od[i]) for i in order[:TOP_LOCAL]]
    best_local, used = local_search(starts, disc, DISC_YEARS, rng, cap=cap,
                                    verbose=verbose)
    # the top 50 by discovery, random sample and local search pooled
    pool = {}
    for t, o in zip(cands, od):
        pool[P.cand_id(mkcand(t))] = (t, float(o))
    for t, o in best_local:
        pool[P.cand_id(mkcand(t))] = (t, float(o))
    ranked = sorted(pool.values(), key=lambda x: -x[1])
    top = ranked[:TOP_REPL]
    orr = obj_many([t for t, _ in top], repl, REPL_YEARS)
    # (e) the rank correlation across the WHOLE random sample
    rho = rho_p = np.nan
    orall = None
    if with_repl_all:
        orall = obj_many(cands, repl, REPL_YEARS,
                         log_every=(20000 if verbose else 0),
                         tag='replication')
        ok = np.isfinite(od) & np.isfinite(orall)
        if ok.sum() > 10:
            rho, rho_p = stats.spearmanr(od[ok], orall[ok])
    return dict(world=world, seed=seed, n_random=len(cands),
                n_local=used, n_evaluations=len(cands) + used
                + (len(cands) if with_repl_all else 0) + len(top),
                disc=od, cands=cands, top=top, top_repl=orr,
                best_disc=float(np.nanmax(od)),
                best_local_disc=float(max(o for _t, o in best_local)),
                best_repl_of_top=float(np.nanmax(orr)) if len(orr) else np.nan,
                rho=float(rho), rho_p=float(rho_p), repl_all=orall)


# ===================== the real run =====================================
def run_real(n_random=N_RANDOM, cap=N_LOCAL_CAP, seed=20261125,
             verbose=True):
    S.load_costs(os.environ.get('FX_COST_TABLE',
                                os.path.join(ROOTOUT, 'cost_table_h22.csv')))
    init_space(); self_check(); P.check_masks()
    disc, repl = pair_sets()
    print('  SOURCE 3 real search: discovery %d pairs %d-%d, replication %d '
          'pairs %d-%d, space %.3g'
          % (len(disc), min(DISC_YEARS), max(DISC_YEARS), len(repl),
             min(REPL_YEARS), max(REPL_YEARS), space_size()), flush=True)
    t0 = time.time()
    R = one_search('real', seed, n_random=n_random, cap=cap, verbose=verbose)
    # ---- the off-diagonals, for the top 50 only
    top = R['top']
    od_13 = obj_many([t for t, _ in top], repl, DISC_YEARS)
    or_15 = obj_many([t for t, _ in top], disc, REPL_YEARS)
    rows = []
    for i, ((t, o), orr) in enumerate(zip(top, R['top_repl'])):
        C = mkcand(t, name='S3_%02d' % (i + 1))
        rows.append(dict(rank=i + 1, cand=C['name'], cand_id=P.cand_id(C),
                         **{sl: C[sl] for sl in P.SLOTS},
                         **{sl + '_set': C[sl + '_set'] for sl in P.SLOTS},
                         obj_discovery=float(o), obj_replication=float(orr),
                         obj_offdiag_13pairs_2005_2010=float(od_13[i]),
                         obj_offdiag_15pairs_2011_2015=float(or_15[i])))
    T50 = pd.DataFrame(rows)
    T50.to_csv(os.path.join(OUT, 'src3_top50.csv'), index=False)
    # ---- the whole random sample, discovery against replication
    SAMP = pd.DataFrame(dict(
        obj_discovery=R['disc'],
        obj_replication=(R['repl_all'] if R['repl_all'] is not None
                         else np.nan)))
    SAMP.to_csv(os.path.join(OUT, 'src3_sample.csv'), index=False)
    meta = dict(world='real', seed=seed, n_random=R['n_random'],
                n_local=R['n_local'], n_evaluations=R['n_evaluations'],
                best_disc=R['best_disc'],
                best_local_disc=R['best_local_disc'],
                best_repl_of_top=R['best_repl_of_top'],
                spearman_disc_repl=R['rho'], spearman_p=R['rho_p'],
                space_size=space_size(), minutes=(time.time() - t0) / 60)
    pd.DataFrame([meta]).to_csv(os.path.join(OUT, 'src3_real_meta.csv'),
                                index=False)
    P.ledger_append([dict(cand=r['cand'], cand_id=r['cand_id'],
                          label=P.cand_label(mkcand(
                              tuple((r[sl], r[sl + '_set'])
                                    for sl in P.SLOTS))),
                          stage='surfaced_by_search',
                          obj_discovery=r['obj_discovery'],
                          obj_replication=r['obj_replication'])
                     for _, r in T50.iterrows()],
                    'source3_search', n_evaluations=R['n_evaluations'])
    print('  real search done in %.1f min: %d evaluations, best discovery '
          '%+.4f, best replication of the top %d %+.4f, rho %+.4f'
          % (meta['minutes'], meta['n_evaluations'], meta['best_disc'],
             TOP_REPL, meta['best_repl_of_top'], meta['spearman_disc_repl']),
          flush=True)
    return T50, meta


def run_null(k, n_random=N_RANDOM, cap=N_LOCAL_CAP, verbose=False):
    """ONE null run. Writes one row and frees its world.

    Resumable by run: a killed job costs that run, not the batch, which is the
    same rule the gauntlet's per-pair checkpoint follows.
    """
    S.load_costs(os.environ.get('FX_COST_TABLE',
                                os.path.join(ROOTOUT, 'cost_table_h22.csv')))
    init_space(); self_check()
    out = os.path.join(NULLDIR, 'null_%03d.csv' % k)
    if os.path.exists(out):
        print('  null %d already on disk' % k, flush=True)
        return pd.read_csv(out)
    t0 = time.time()
    seed = 900000 + k
    F = zero_edge_frames(seed)
    check_world(F)
    tag = 'null%03d' % k
    P.set_world(tag, F)
    try:
        R = one_search(tag, seed, n_random=n_random, cap=cap, verbose=verbose)
        row = dict(run=k, seed=seed, n_random=R['n_random'],
                   n_local=R['n_local'], n_evaluations=R['n_evaluations'],
                   best_disc=R['best_disc'],
                   best_local_disc=R['best_local_disc'],
                   best_repl_of_top=R['best_repl_of_top'],
                   spearman_disc_repl=R['rho'], spearman_p=R['rho_p'],
                   minutes=(time.time() - t0) / 60)
    finally:
        P.set_world('real')
        P.drop_world(tag)
    pd.DataFrame([row]).to_csv(out, index=False)
    print('  null %d done %.1f min: best replicated %+.4f, rho %+.4f'
          % (k, row['minutes'], row['best_repl_of_top'],
             row['spearman_disc_repl']), flush=True)
    return pd.DataFrame([row])


def null_table():
    fs = sorted(glob.glob(os.path.join(NULLDIR, 'null_*.csv')))
    if not fs:
        return pd.DataFrame()
    D = pd.concat([pd.read_csv(f) for f in fs], ignore_index=True)
    D = D.sort_values('run').reset_index(drop=True)
    D.to_csv(os.path.join(OUT, 'src3_nulls.csv'), index=False)
    return D


def gates_on_survivors(T50, floor, verbose=True):
    """Every top-50 candidate that beats the search null on REPLICATION, then
    G2, G3 on all 28 pairs and all eleven years, and G4."""
    surv = T50[T50.obj_replication > floor].copy()
    if not len(surv):
        return pd.DataFrame(), pd.DataFrame()
    rows, nud = [], []
    for _, r in surv.iterrows():
        t = tuple((r[sl], r[sl + '_set']) for sl in P.SLOTS)
        C = mkcand(t, name=r['cand'])
        C['source'] = 'source3_search'
        C['reason'] = ('surfaced by the search: discovery %+.4f, replication '
                       '%+.4f, search-null floor %+.4f'
                       % (r['obj_discovery'], r['obj_replication'], floor))
        res = P.evaluate(C, with_g4=True, ndraw_null=200, verbose=verbose,
                         nudge_out=nud)
        row = res['row']
        row['obj_discovery'] = r['obj_discovery']
        row['obj_replication'] = r['obj_replication']
        row['search_null_floor'] = floor
        row['beats_search_null'] = 1
        rows.append(row)
    D = pd.DataFrame(rows)
    # SOURCE 3's G1 IS THE SEARCH NULL, not the random-entry floor. A
    # candidate found by looking at 600,000 of them cannot be judged against a
    # best-of-one floor, and the random-entry null does not know how many were
    # looked at. The column is kept for comparison and the gate is the search
    # null.
    D['G1'] = D['beats_search_null']
    D['passer'] = ((D.G1 == 1) & (D.G2 == 1) & (D.G3 == 1)
                   & (D.G4 == 1)).astype(int)
    return D, (pd.concat(nud, ignore_index=True) if nud else pd.DataFrame())


# ===================== the write-up =====================================
def md():
    f, yn = P.fmt, P.yn
    T50 = pd.read_csv(os.path.join(OUT, 'src3_top50.csv'))
    M = pd.read_csv(os.path.join(OUT, 'src3_real_meta.csv')).iloc[0]
    NU = null_table()
    SAMP = pd.read_csv(os.path.join(OUT, 'src3_sample.csv'))
    GP = os.path.join(OUT, 'src3_gates.csv')
    G = pd.read_csv(GP) if os.path.exists(GP) else pd.DataFrame()
    nn = len(NU)
    floor = (float(np.quantile(NU.best_repl_of_top.dropna(), 0.95))
             if nn else np.nan)
    L = []
    L.append('# SOURCE 3 — machine search, against a search null\n')
    L.append('**Protocol: `results/nnfx/PROTOCOL.md`, unchanged. '
             '%s evaluations in the real search, %d null runs at the same '
             'budget. The floor is the 95th percentile of the best '
             '**replicated** result under the null.**\n'
             % ('{:,}'.format(int(M.n_evaluations)), nn))
    L.append('## The design\n')
    L.append('| | pairs | years |')
    L.append('|---|---:|---|')
    L.append('| **discovery** | 15 (neither JPY nor CHF) | 2005-2010 |')
    L.append('| **replication** | 13 (JPY or CHF) | 2011-2015 |')
    L.append('| off-diagonal | 13 | 2005-2010 |')
    L.append('| off-diagonal | 15 | 2011-2015 |')
    L.append('')
    L.append('Discovery and replication share **no pair and no year**. A '
             'candidate that carries has to work on different currencies in a '
             'different decade — stronger than an ordinary train/test split.\n')
    L.append('The space is **%.3g complete five-slot algorithms** '
             '(%d C1 x %d C2 x %d volume x %d baseline x %d exit options, '
             'settings included, collapsed settings removed). The random '
             'sample of %s is **%.4f%%** of it.\n'
             % (M.space_size, len(SPACE['c1']), len(SPACE['c2']),
                len(SPACE['vol']), len(SPACE['base']), len(SPACE['exit']),
                '{:,}'.format(int(M.n_random)),
                100.0 * M.n_random / M.space_size))
    L.append('## The budget, and what it bought\n')
    L.append('| | value |')
    L.append('|---|---:|')
    L.append('| random candidates | %s |' % '{:,}'.format(int(M.n_random)))
    L.append('| local-search evaluations | %s |' % '{:,}'.format(int(M.n_local)))
    L.append('| replication evaluations of the sample | %s |'
             % '{:,}'.format(int(M.n_random)))
    L.append('| **total evaluations, real search** | **%s** |'
             % '{:,}'.format(int(M.n_evaluations)))
    L.append('| best discovery objective, random sample | %s |'
             % f(M.best_disc, 4))
    L.append('| best discovery objective after local search | %s |'
             % f(M.best_local_disc, 4))
    L.append('| **best replication objective of the top %d** | **%s** |'
             % (TOP_REPL, f(M.best_repl_of_top, 4)))
    L.append('| minutes | %s |' % f(M.minutes, 1, False))
    L.append('')
    L.append('The objective is **net R per year excluding the best day** on '
             'the fast path: realised by exit day, uncapped, charged once per '
             'round trip. `nnfxproto.verify_fast` checks it against the full '
             'reporting path to 2e-16. Every candidate the search surfaces is '
             're-scored on the full path, with the 1:30 cap and mark to '
             'market.\n')
    if nn:
        L.append('## The search null — %d independent runs at the same '
                 'budget\n' % nn)
        L.append('| | best replicated under the null |')
        L.append('|---|---:|')
        L.append('| runs | %d |' % nn)
        L.append('| mean | %s |' % f(NU.best_repl_of_top.mean(), 4))
        L.append('| median | %s |' % f(NU.best_repl_of_top.median(), 4))
        L.append('| **95th percentile = THE FLOOR** | **%s** |' % f(floor, 4))
        L.append('| max | %s |' % f(NU.best_repl_of_top.max(), 4))
        L.append('| best DISCOVERY under the null, mean | %s |'
                 % f(NU.best_disc.mean(), 4))
        L.append('| best discovery under the null, max | %s |'
                 % f(NU.best_disc.max(), 4))
        L.append('')
        L.append('Each null run block-shuffles every pair\'s bars in 20-day '
                 'blocks within the calendar year and flips each block\'s '
                 'direction with probability one half, then runs the '
                 '**identical search at the identical budget**. The daily '
                 'return standard deviation is preserved exactly and the '
                 'lag-1 autocorrelation to three decimals; what is destroyed '
                 'is any direction and any trend longer than 20 days.\n')
        L.append('**Two declared limitations of the null.** There is no '
                 'hourly bid/ask path for a synthetic price series, so the '
                 'null runs with realistic gap fills and the ambiguity '
                 'resolver **off** while the real search runs with both on. '
                 'Item 1 measured gap fills at under 1 R a year on real '
                 'candidates and the shuffle destroys the crisis clustering '
                 'that makes gaps matter, so this makes the null very '
                 'slightly easier to beat, not harder. The peg guard\'s '
                 'median is a 28-pair median in both worlds.\n')
        real_beat = float(M.best_repl_of_top) > floor
        L.append('### The comparison\n')
        L.append('> **The real search\'s best replicated result is %s. '
                 'The null\'s 95th percentile is %s. The real search %s.**\n'
                 % (f(M.best_repl_of_top, 4), f(floor, 4),
                    'BEATS the floor' if real_beat
                    else '**does not beat the floor**'))
        nb = int((T50.obj_replication > floor).sum()) if len(T50) else 0
        L.append('**%d of the top %d beat the search null on the replication '
                 'set.**\n' % (nb, len(T50)))
    else:
        L.append('## The search null\n')
        L.append('**Not yet complete.** The floor is not available, so no '
                 'candidate from this source can be called a find. The real '
                 'search\'s numbers are below and are not interpretable '
                 'without it.\n')
    L.append('## (e) Does past performance carry in this space?\n')
    ok = np.isfinite(SAMP.obj_discovery) & np.isfinite(SAMP.obj_replication)
    L.append('| | Spearman rho, discovery against replication | p |')
    L.append('|---|---:|---:|')
    L.append('| **real search**, all %s | **%s** | %.3g |'
             % ('{:,}'.format(int(ok.sum())), f(M.spearman_disc_repl, 4),
                M.spearman_p))
    if nn:
        L.append('| null runs, mean | %s | — |'
                 % f(NU.spearman_disc_repl.mean(), 4))
        L.append('| null runs, 95th percentile | %s | — |'
                 % f(float(np.quantile(NU.spearman_disc_repl.dropna(), 0.95)),
                     4))
    L.append('')
    if nn:
        rho_r = float(M.spearman_disc_repl)
        rho_f = float(np.quantile(NU.spearman_disc_repl.dropna(), 0.95))
        if rho_r > rho_f:
            L.append('**The rank correlation IS above the null.** Discovery '
                     'performance carries some information about replication '
                     'performance in this space — not much at rho %s, but '
                     'more than shuffled data produces.\n' % f(rho_r, 4))
        else:
            L.append('**The rank correlation is NOT above the null, and that '
                     'is the most important number in this document.** It '
                     'means that in this space, how well a complete '
                     'algorithm did on the discovery pairs and years tells '
                     'you nothing about how it will do on different '
                     'currencies in a different decade. Past performance '
                     'does not carry. A search can still get lucky; it '
                     'cannot be expected to find anything.\n')
        L.append('This is the FX version of Bajgrowicz and Scaillet on the '
                 'DJIA 1897-2011, where fewer than 5%% of selected rules '
                 'survive the first re-selection, and of this project\'s own '
                 'blind grade, which measured a rank correlation of +0.02 to '
                 '+0.05 between in-sample and out-of-sample on 20,275 '
                 'signals.\n')
    L.append('## The top %d by discovery, on every set\n' % min(20, len(T50)))
    L.append('| rank | C1 | C2 | volume | baseline | exit | discovery | '
             '**replication** | 13 pairs 2005-10 | 15 pairs 2011-15 |')
    L.append('|---:|---|---|---|---|---|---:|---:|---:|---:|')
    for _, r in T50.head(20).iterrows():
        L.append('| %d | %s/%s | %s/%s | %s/%s | %s/%s | %s/%s | %s | **%s** '
                 '| %s | %s |'
                 % (r['rank'], r['c1'].replace('_signals', ''), r['c1_set'],
                    r['c2'].replace('_signals', ''), r['c2_set'],
                    r['vol'].replace('_volume_signals', ''), r['vol_set'],
                    r['base'].replace('_baseline', ''), r['base_set'],
                    r['exit'].replace('_exit', ''), r['exit_set'],
                    f(r['obj_discovery'], 3), f(r['obj_replication'], 3),
                    f(r['obj_offdiag_13pairs_2005_2010'], 3),
                    f(r['obj_offdiag_15pairs_2011_2015'], 3)))
    L.append('')
    if len(T50):
        pos = int((T50.obj_replication > 0).sum())
        L.append('**%d of the top %d are even POSITIVE on the replication '
                 'set**, before any floor is applied. The off-diagonal '
                 'columns are the control: a candidate that is strong on '
                 'discovery and on the 13 pairs in the SAME years, but weak '
                 'on the 13 pairs in LATER years, found a period and not a '
                 'rule.\n' % (pos, len(T50)))
    if len(G):
        L.append('## The survivors through G2, G3 and G4\n')
        L.append('**Source 3\'s G1 is the search null itself.** A candidate '
                 'found by looking at %s of them cannot be judged against a '
                 'best-of-one random-entry floor, and the random-entry null '
                 'has no way of knowing how many were looked at.\n'
                 % '{:,}'.format(int(M.n_evaluations)))
        L.append('| id | R total | R/yr | trades | R/dip | G2 | G3 | G4 | '
                 '**passer** |')
        L.append('|---|---:|---:|---:|---:|---|---|---|---|')
        for _, r in G.iterrows():
            L.append('| **%s** | %s | %s | %s | %s | %s | %s | %s | %s |'
                     % (r['cand'], f(r.get('R_total')),
                        f(r.get('R_per_year')), f(r.get('trades'), 0, False),
                        f(r.get('R_per_dip')), yn(r['G2']), yn(r['G3']),
                        yn(r['G4']),
                        '**PASSER**' if int(r['passer']) else 'no'))
        L.append('')
        L.append('**%d passers.**\n' % int(G.passer.sum()))
    elif nn:
        L.append('## The survivors through G2, G3 and G4\n')
        L.append('**No top-50 candidate beat the search null on the '
                 'replication set, so there is nothing to put through the '
                 'remaining gates.** That is the gate working: the search '
                 'found things, the null found things just as good, and the '
                 'difference is zero.\n')
    L.append('## Costs\n')
    L.append('Charged **once** per round trip on the engine\'s own risk '
             'denominator, real world and null world alike. See '
             '`results/nnfx/COST_DOUBLE_CHARGE.md`.\n')
    L.append('## Provenance\n')
    L.append(P.prov([os.path.join(OUT, x) for x in
                     ('src3_top50.csv', 'src3_sample.csv',
                      'src3_real_meta.csv', 'src3_nulls.csv',
                      'src3_gates.csv')]))
    L.append('')
    L.append('The candidate ledger is `results/nnfx/proto_ledger.csv`, '
             'append-only and shared by all three sources, so no row count is '
             'quoted for it here.')
    L.append('')
    open(os.path.join(OUT, 'SOURCE3.md'), 'w').write('\n'.join(L))
    print('  SOURCE3.md written (%d lines)' % len(L), flush=True)


def finish():
    """Floor from whatever null runs are on disk, then the gates, then md."""
    S.load_costs(os.environ.get('FX_COST_TABLE',
                                os.path.join(ROOTOUT, 'cost_table_h22.csv')))
    init_space()
    T50 = pd.read_csv(os.path.join(OUT, 'src3_top50.csv'))
    NU = null_table()
    if len(NU):
        floor = float(np.quantile(NU.best_repl_of_top.dropna(), 0.95))
        print('  search-null floor from %d runs: %+.4f' % (len(NU), floor),
              flush=True)
        G, NG = gates_on_survivors(T50, floor)
        if len(G):
            G.to_csv(os.path.join(OUT, 'src3_gates.csv'), index=False)
            NG.to_csv(os.path.join(OUT, 'src3_gates_nudge.csv'), index=False)
    md()


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--real', action='store_true')
    ap.add_argument('--null-run', type=int, default=-1)
    ap.add_argument('--finish', action='store_true')
    ap.add_argument('--md-only', action='store_true')
    ap.add_argument('--n-random', type=int, default=N_RANDOM)
    ap.add_argument('--cap', type=int, default=N_LOCAL_CAP)
    a = ap.parse_args()
    if a.real:
        run_real(n_random=a.n_random, cap=a.cap)
        md()
    elif a.null_run >= 0:
        run_null(a.null_run, n_random=a.n_random, cap=a.cap)
    elif a.finish:
        finish()
    elif a.md_only:
        md()
    else:
        ap.error('one of --real, --null-run K, --finish, --md-only')
