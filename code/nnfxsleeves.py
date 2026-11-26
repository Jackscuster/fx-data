"""ITEM 1 -- THE SLEEVE BANK. PROTOCOL.md AMENDMENT 1, A1.

A sleeve is one complete NNFX algorithm ON ONE PAIR. This module computes,
for every algorithm in the bank list and every one of the 28 pairs, on each
of the two admission/scoring windows:

    net R   |   trades   |   net R excluding that sleeve's best day
    and the sleeve's best single trade, which admission test B needs.

WHAT IS IN THE BANK
  the 6 published combinations (Source 1)                      N1-N6
  the 10 hand-built algorithms (Source 2)                      H1-H10
  candidates A and B from stages 1-3, slots NEUTRALISED        A_neutral, B_neutral
  Source 3's 200,000 sampled algorithms, re-run on all 28 pairs
  every algorithm Source 3's local search evaluated

A_neutral AND B_neutral ARE NOT COMPLETE ALGORITHMS and every table that
carries them says so. A and B are C1+baseline members; stage 1 neutralised
four slots and stage 2 three. Running them with C2, volume and the exit
indicator neutral is the only way their numbers are the numbers stages 1-3
reported. They are in the bank because Jack's item 1 names them.

SHARDED BY PAIR, NOT BY CANDIDATE. A worker holding 4 pairs caches ~425 slot
options x 4 pairs of indicator arrays, about 60 MB; a worker holding a slice
of the candidates would need all 28 pairs of every option, about 400 MB, and
eight of those do not fit beside everything else on this machine.

TWO WINDOWS ONLY FOR THE SEARCHED ALGORITHMS. The declared 18 also get a
per-calendar-year table. 380,000 algorithms x 28 pairs x 11 years x 4 metrics
is 1.8 GB and this disk has 3.9 GB free, so the searched bank stores the two
six-year windows and nothing finer. Stated as a limit, not hidden.
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
import nnfxsrc1 as S1
import nnfxsrc2 as S2
import nnfxsrc3 as S3
import nnfxcands as CL
import l2sweep as S

OUT = os.path.join(ROOTOUT, 'nnfx', 'bank')
os.makedirs(OUT, exist_ok=True)

H1Y = tuple(range(2005, 2011))
H2Y = tuple(range(2011, 2016))
PERIODS = (('h1', H1Y), ('h2', H2Y))
YEARS = tuple(range(2005, 2016))
PER_YEAR = tuple((str(y), (y,)) for y in YEARS)
METRICS = ('R', 'R_ex_best_day', 'best_trade', 'trades')

# ---- admission, PROTOCOL.md A2 -- light, and the numbers are declared here
ADM_MIN_TRADES = 20
ADM_BEST_TRADE_SHARE = 0.25
ADM_NUDGE_TRADES = (15, 30)     # B4's count knob for the declared book


def declared_sleeves():
    """The 18 named algorithms: 6 published, 10 hand-built, A and B."""
    out = []
    for C in S1.candidates():
        out.append((C['name'], C, 'source1_published', True))
    for C in S2.candidates():
        out.append((C['name'], C, 'source2_handbuilt', True))
    A = P.cand('A_neutral', 'ichimoku_signals', P.NEUTRAL, P.NEUTRAL,
               'sma_baseline', P.NEUTRAL, source='stage_member',
               reason='stage 1-3 member A (C1 ichimoku + baseline sma); C2, '
                      'volume and exit indicator NEUTRALISED, as stages 1-3 '
                      'ran it. NOT a complete algorithm under section 1.')
    B = P.cand('B_neutral', 'schaff_trend_cycle_signals', P.NEUTRAL, P.NEUTRAL,
               'sma_baseline', P.NEUTRAL, source='stage_member',
               reason='stage 1-3 member B (C1 schaff_trend_cycle + baseline '
                      'sma); C2, volume and exit indicator NEUTRALISED. NOT a '
                      'complete algorithm under section 1.')
    out.append(('A_neutral', A, 'stage_member', False))
    out.append(('B_neutral', B, 'stage_member', False))
    ids = [P.cand_id(c) for _n, c, _s, _k in out]
    assert len(set(ids)) == len(ids), 'two declared sleeves hash the same'
    return out


# ======================= the declared 18 ================================
def run_declared(verbose=True):
    S.load_costs(os.environ.get('FX_COST_TABLE',
                                os.path.join(ROOTOUT, 'cost_table_h22.csv')))
    pairs = list(S.all_pairs())
    D = declared_sleeves()
    per = PERIODS + PER_YEAR + (('ev', YEARS),)
    rows, yrows = [], []
    t0 = time.time()
    for (nm, C, src, complete) in D:
        for p in pairs:
            r = P.fast_per_pair(C, p, per)
            base = dict(algo=nm, cand_id=P.cand_id(C), source=src,
                        complete=int(complete), pair=p,
                        label=P.cand_label(C))
            for w in ('h1', 'h2', 'ev'):
                d = r[w]
                rows.append(dict(base, window=w,
                                 R=d['R'], R_ex_best_day=d['R_ex_best_day'],
                                 best_trade=d['best_trade'],
                                 trades=d['trades'],
                                 days_traded=d['days_traded'],
                                 best_trade_share=(d['best_trade'] / d['R']
                                                   if d['R'] > 0 else np.nan),
                                 admitted=int(adm_ok(d))))
            for y in YEARS:
                d = r[str(y)]
                yrows.append(dict(base, year=y, R=d['R'],
                                  trades=d['trades'],
                                  R_ex_best_day=d['R_ex_best_day']))
        if verbose:
            print('    declared %s done, %.1f s' % (nm, time.time() - t0),
                  flush=True)
    Dd = pd.DataFrame(rows); Dy = pd.DataFrame(yrows)
    Dd.to_csv(os.path.join(OUT, 'bank_declared.csv'), index=False)
    Dy.to_csv(os.path.join(OUT, 'bank_declared_yearly.csv'), index=False)
    print('  bank_declared.csv %d rows, bank_declared_yearly.csv %d rows'
          % (len(Dd), len(Dy)), flush=True)
    return Dd, Dy


def adm_ok(d):
    """PROTOCOL.md A2: positive ex best day, best trade under a quarter, >=20
    trades. Nothing else. Nothing is rejected for being small."""
    if d['trades'] < ADM_MIN_TRADES:
        return False
    if not (d['R_ex_best_day'] > 0):
        return False
    if not (d['R'] > 0):
        return False
    return (d['best_trade'] / d['R']) < ADM_BEST_TRADE_SHARE


def admit_mask(R, Rex, bt, ntr, min_trades=ADM_MIN_TRADES,
               share=ADM_BEST_TRADE_SHARE):
    """The same test, vectorised over the whole bank."""
    with np.errstate(divide='ignore', invalid='ignore'):
        sh = np.where(R > 0, bt / np.where(R > 0, R, 1.0), np.inf)
    return (ntr >= min_trades) & (Rex > 0) & (R > 0) & (sh < share)


# ======================= the searched bank ==============================
def shard_path(w, world='real'):
    return os.path.join(OUT, 'shard_%s_%02d.npz' % (world, w))


def run_shard(w, nshards, world='real', frames=None, cands=None,
              limit=None, verbose=True):
    """Every algorithm in the bank list, on this shard's pairs."""
    S.load_costs(os.environ.get('FX_COST_TABLE',
                                os.path.join(ROOTOUT, 'cost_table_h22.csv')))
    S3.init_space()
    if world != 'real':
        P.set_world(world, frames)
    allp = list(S.all_pairs())
    mine = allp[w::nshards]
    if cands is None:
        cands, _src, _m = CL.load()
    if limit:
        cands = cands[:limit]
    n = len(cands)
    A = {(wd, mt): np.zeros((n, len(mine)),
                            np.int32 if mt == 'trades' else np.float32)
         for wd, _y in PERIODS for mt in METRICS}
    t0 = time.time()
    for pi, p in enumerate(mine):
        P.base_dict(p, int(P.RISK['atr_len']))
        for j, t in enumerate(cands):
            r = P.fast_per_pair(S3.mkcand(t), p, PERIODS)
            for wd, _y in PERIODS:
                d = r[wd]
                A[(wd, 'R')][j, pi] = d['R']
                A[(wd, 'R_ex_best_day')][j, pi] = d['R_ex_best_day']
                A[(wd, 'best_trade')][j, pi] = d['best_trade']
                A[(wd, 'trades')][j, pi] = d['trades']
            if verbose and (j + 1) % 25000 == 0:
                el = time.time() - t0
                done = pi * n + j + 1
                tot = len(mine) * n
                print('    shard %d %s %d/%d  %.0f/s  eta %.1f min'
                      % (w, p, j + 1, n, done / max(el, 1e-9),
                         (tot - done) / max(done / el, 1e-9) / 60), flush=True)
        if verbose:
            print('    shard %d pair %s done (%d of %d), %.1f min'
                  % (w, p, pi + 1, len(mine), (time.time() - t0) / 60),
                  flush=True)
    np.savez_compressed(shard_path(w, world), pairs=np.asarray(mine),
                        n=n, **{'%s__%s' % k: v for k, v in A.items()})
    print('  shard %d of %d written: %d algorithms x %d pairs in %.1f min'
          % (w, nshards, n, len(mine), (time.time() - t0) / 60), flush=True)
    return shard_path(w, world)


def merge(nshards, world='real', verbose=True):
    """-> sleeve_bank_<world>.npz, pairs in l2sweep.all_pairs() order."""
    S.load_costs(os.environ.get('FX_COST_TABLE',
                                os.path.join(ROOTOUT, 'cost_table_h22.csv')))
    allp = list(S.all_pairs())
    col = {p: i for i, p in enumerate(allp)}
    out, n = {}, None
    got = set()
    for w in range(nshards):
        z = np.load(shard_path(w, world), allow_pickle=False)
        sp = [str(x) for x in z['pairs']]
        n = int(z['n']) if n is None else n
        assert int(z['n']) == n, 'shard %d holds %d algorithms, expected %d' \
            % (w, int(z['n']), n)
        for wd, _y in PERIODS:
            for mt in METRICS:
                k = '%s__%s' % (wd, mt)
                if k not in out:
                    out[k] = np.zeros((n, len(allp)),
                                      np.int32 if mt == 'trades' else np.float32)
                for pi, p in enumerate(sp):
                    out[k][:, col[p]] = z[k][:, pi]
        got |= set(sp)
    assert got == set(allp), 'merged %d pairs, expected 28: missing %s' \
        % (len(got), sorted(set(allp) - got))
    path = os.path.join(OUT, 'sleeve_bank_%s.npz' % world)
    np.savez_compressed(path, pairs=np.asarray(allp), **out)
    sz = os.path.getsize(path) / 1e6
    if verbose:
        print('  sleeve_bank_%s.npz: %d algorithms x 28 pairs x %d windows, '
              '%.0f MB' % (world, n, len(PERIODS), sz), flush=True)
    return path


def load_bank(world='real'):
    z = np.load(os.path.join(OUT, 'sleeve_bank_%s.npz' % world),
                allow_pickle=False)
    pairs = [str(x) for x in z['pairs']]
    return pairs, {k: z[k] for k in z.files if '__' in k}


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--declared', action='store_true')
    ap.add_argument('--shard', type=int, default=None)
    ap.add_argument('--nshards', type=int, default=7)
    ap.add_argument('--merge', action='store_true')
    ap.add_argument('--limit', type=int, default=None)
    a = ap.parse_args()
    t0 = time.time()
    if a.declared:
        run_declared()
    if a.shard is not None:
        run_shard(a.shard, a.nshards, limit=a.limit)
    if a.merge:
        merge(a.nshards)
    print('DONE nnfxsleeves in %.1f min' % ((time.time() - t0) / 60),
          flush=True)
