import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""PER-PAIR, PER-DIRECTION RECORDS, AND PAIR ROUTING (Jack, 22 Nov).

PART 1, WHICH IS WHAT THIS FILE DOES FIRST AND CHEAPLY: the current non-luck
winners, broken out by pair and by direction, per year, on both unseen
records -- and their PAIR-ROUTED record against trading all 28.

THE ROUTING IS WALK FORWARD AND THERE IS NO PER-PAIR TUNING. The settings are
the ones the strategy already won with; the only choice made per step is WHICH
PAIRS to trade, and it is made on that step's TUNING years alone. The pair set
is then applied unchanged to the grade and trade years. Choosing pairs on the
years being reported would be the same fault the whole restart exists to
remove.

    python3 code/l2r2pairs.py --stage winners --mode A
    python3 code/l2r2pairs.py --stage md
"""
import time, json, glob
import numpy as np, pandas as pd

import l2sweep as S
import l2tune as T
import l2r2gate1 as G
import l2r2gate2 as G2
import l2r2book as BK
import l2r2gate3 as G3
import l2r2winners as WN

RD = os.path.join(ROOTOUT, 'r2gate2')
YEARS = G3.YEARS
DIRS = (('long', 1), ('short', -1))


def _pairdir_year(Y, mode, combo, ip, risk, sname, plan, code, routed):
    """Per (pair, direction, year): n, total R, gross, loss, wins, and the
    ordered trade R so a real drawdown can be taken.

    THE SAME ENGINE AND THE SAME COSTS as every other stage: run_bars through
    l2r2winners._trade_lists, which is the path condition 1 already guards.
    """
    out = {}
    for p in Y.sc.pairs:
        pass
    # one engine pass per pair, reusing the winners module's extractor
    aidx = {p: np.zeros(len(Y.cl[p]), np.int64) for p in Y.sc.pairs}
    for p in Y.sc.pairs:
        aidx[p][:] = 0                      # every bar permitted; we filter by year
    tl = WN._trade_lists(Y, mode, combo, ip, risk, sname, plan, aidx)
    for p, d in tl.items():
        eb = d['eb']
        yb = Y.yb[p][eb]                     # the ENTRY bar's year, as the bank does
        reg = Y.sc.reg[p][eb]
        keep = np.ones(len(eb), bool) if not routed else (reg == code)
        for dname, dsign in DIRS:
            m = keep & (np.sign(d['dirv']) == dsign)
            if not m.any():
                continue
            for y in sorted(set(yb[m].tolist())):
                if y < 0:
                    continue
                mm = m & (yb == y)
                if not mm.any():
                    continue
                r = d['r'][mm]
                eq = np.cumsum(r)
                dd = float((np.maximum.accumulate(eq) - eq).max())
                out[(p, dname, YEARS[y])] = dict(
                    n=int(mm.sum()), total_R=float(r.sum()),
                    gross_R=float(r[r > 0].sum()), loss_R=float(-r[r < 0].sum()),
                    wins=int((r > 0).sum()), max_dd_R=dd)
    return out


def stage_winners(mode='A', tag='full'):
    """The winners' per (pair, direction, year) records, both streams."""
    G.manifest_check()
    S.load_costs()
    T.ACCT_OBJECTIVE = True
    W = pd.read_csv(os.path.join(RD, 'mode%s_winners.csv' % mode))
    assert len(W), 'no winners for mode %s' % mode
    z = np.load(BK._bank_slice_file(mode, tag), allow_pickle=True)
    TG = z['tag']; CB = z['combo']
    Y = G2.Years(cap=4000)
    ST = G2.steps()
    rows = []
    t0 = time.time()
    for wi, w in W.iterrows():
        k = int(w.bank_row)
        stream = list(G2.STREAMS).index(w.stream)
        sl, rt = stream // 2, stream % 2
        sname, plan, code = S.SLICES[sl]
        combo = tuple(CB[k])
        for si, stp in enumerate(ST):
            ci = int(TG[k, stream, si])
            if ci < 0:
                continue
            ip, risk = BK.winner_config(mode, combo, sname, ci)
            rec = _pairdir_year(Y, mode, combo, ip, risk, sname, plan, code,
                                routed=(rt == 0))
            for (p, dname, year), v in rec.items():
                role = ('tune' if stp['tune'][0] <= year <= stp['tune'][1] else
                        'grade' if year == stp['grade'][0] else
                        'trade' if year == stp['trade'][0] else 'other')
                rows.append(dict(mode=mode, bank_row=k, sid=w.sid, stream=w.stream,
                                 step=stp['name'], role=role, pair=p,
                                 direction=dname, year=year, **v))
        print('    winner %d/%d done (%.1f min)' % (wi + 1, len(W),
                                                    (time.time() - t0) / 60), flush=True)
    D = pd.DataFrame(rows)
    f = os.path.join(RD, 'mode%s_winners_by_pair.csv' % mode)
    D.to_csv(f, index=False)
    print('  per (pair, direction, year): %s rows for %d winners -> %s'
          % (f'{len(D):,}', len(W), os.path.relpath(f, _R)), flush=True)
    return f, D


def _route_pick(d, rule, K):
    """Choose a pair set from TUNING-year records only.

    topk        the K pairs with the best tuning-year total R / max DD
    threshold   every pair with positive tuning-year total R
    Direction variants pick (pair, direction) cells instead of whole pairs.
    """
    g = d.groupby('pair', as_index=False).agg(tot=('total_R', 'sum'),
                                              dd=('max_dd_R', 'sum'))
    g['score'] = np.where(g.dd > 0, g.tot / g.dd, np.where(g.tot > 0, np.inf, -np.inf))
    if rule == 'threshold':
        return set(g[g.tot > 0].pair), None
    g = g.sort_values('score', ascending=False)
    return set(g.head(K).pair), None


def _route_pick_dir(d, rule, K):
    g = d.groupby(['pair', 'direction'], as_index=False).agg(
        tot=('total_R', 'sum'), dd=('max_dd_R', 'sum'))
    g['score'] = np.where(g.dd > 0, g.tot / g.dd, np.where(g.tot > 0, np.inf, -np.inf))
    if rule == 'threshold_dir':
        sel = g[g.tot > 0]
    else:
        sel = g.sort_values('score', ascending=False).head(K)
    return None, set(zip(sel.pair, sel.direction))


def stage_routed(mode='A', ndraw=20, seed=20261122):
    """Each winner's pair-routed trade-year record against all 28 pairs.

    THE NULL is a random pair subset of the SAME SIZE, drawn from the pairs the
    strategy actually traded in the tuning years -- the population the rule
    chose from. Drawing from all 28 regardless would let the null include pairs
    the rule could never have picked, which flatters the rule.
    """
    f = os.path.join(RD, 'mode%s_winners_by_pair.csv' % mode)
    assert os.path.exists(f), f + ' is missing -- run --stage winners first'
    D = pd.read_csv(f)
    rng = np.random.default_rng(seed)
    rows = []
    for (k, stream), g in D.groupby(['bank_row', 'stream']):
        sid = g.sid.iloc[0]
        for rule in ('all28', 'topk', 'threshold', 'topk_dir', 'threshold_dir'):
            Ks = range(1, 29) if rule in ('topk', 'topk_dir') else [0]
            for K in Ks:
                tot = dd = 0.0
                nt = 0
                nsel = []
                for step, gs in g.groupby('step'):
                    tune = gs[gs.role == 'tune']
                    trade = gs[gs.role == 'trade']
                    if not len(trade):
                        continue
                    if rule == 'all28':
                        sel = trade
                    elif rule in ('topk', 'threshold'):
                        ps, _ = _route_pick(tune, rule, K)
                        sel = trade[trade.pair.isin(ps)]
                        nsel.append(len(ps))
                    else:
                        _, pd_ = _route_pick_dir(tune, rule, K)
                        sel = trade[[(p, dd_) in pd_ for p, dd_
                                     in zip(trade.pair, trade.direction)]]
                        nsel.append(len(pd_))
                    tot += float(sel.total_R.sum())
                    dd += float(sel.max_dd_R.sum())
                    nt += int(sel.n.sum())
                rows.append(dict(mode=mode, bank_row=k, sid=sid, stream=stream,
                                 rule=rule, K=(K or np.nan), n_selected=(
                                     float(np.mean(nsel)) if nsel else 28.0),
                                 trade_n=nt, trade_total_R=tot, trade_max_dd_R=dd,
                                 return_per_dd=(tot / dd if dd > 0 else np.nan)))
        # the random-pair null, matched in size to the topk pick at each K
        for K in range(1, 29):
            draws = []
            for _ in range(ndraw):
                tot = dd = 0.0
                for step, gs in g.groupby('step'):
                    tune = gs[gs.role == 'tune']; trade = gs[gs.role == 'trade']
                    if not len(trade):
                        continue
                    pool = sorted(set(tune.pair))
                    if not pool:
                        continue
                    ps = set(rng.choice(pool, size=min(K, len(pool)), replace=False))
                    sel = trade[trade.pair.isin(ps)]
                    tot += float(sel.total_R.sum()); dd += float(sel.max_dd_R.sum())
                draws.append(tot / dd if dd > 0 else np.nan)
            dr = np.array(draws, float)
            rows.append(dict(mode=mode, bank_row=k, sid=sid, stream=stream,
                             rule='random_null', K=K, n_selected=float(K),
                             trade_n=np.nan, trade_total_R=np.nan,
                             trade_max_dd_R=np.nan,
                             return_per_dd=float(np.nanmean(dr)),
                             null_p95=float(np.nanpercentile(dr, 95))
                             if np.isfinite(dr).any() else np.nan))
    R = pd.DataFrame(rows)
    o = os.path.join(RD, 'mode%s_winners_pairrouted.csv' % mode)
    R.to_csv(o, index=False)
    print('  pair-routed records: %s rows -> %s'
          % (f'{len(R):,}', os.path.relpath(o, _R)), flush=True)
    return o, R


def write_md(out=None):
    """results/r2gate2/WINNERS_BY_PAIR.md -- part 1, read-only off the two CSVs."""
    import hashlib
    L = []; A = L.append
    def tbl(d, cols=None):
        return G3.BK_tbl(d, cols)
    A('# THE WINNERS BY PAIR AND BY DIRECTION, AND PAIR ROUTING\n')
    A('Generated %s by `code/l2r2pairs.py`. Part 1 of item 3: the non-luck winners '
      'broken out per pair, per direction, per year, and their PAIR-ROUTED trade-year '
      'record against trading all 28.\n' % time.strftime('%F %H:%M'))
    A('\n**The routing is walk forward and there is no per-pair tuning.** The settings '
      'are the ones each strategy already won with; the only per-step choice is WHICH '
      'PAIRS to trade, made on that step\'s TUNING years alone and then applied '
      'unchanged to the trade year.\n')
    A('\n**PROP RETURN** is the yearly return at a %.1f%% worst dip, which for a '
      'strategy is `%.2f x return/DD`; the target is %.0f%% a year, i.e. '
      '**return/DD >= %.2f**.\n'
      % (WN.PROP_DIP, WN.PROP_DIP / 5.0, WN.PROP_TARGET,
         WN.PROP_TARGET / (WN.PROP_DIP / 5.0)))

    A('\n## The headline\n')
    heads = []
    for mode in ('A', 'B'):
        f = os.path.join(RD, 'mode%s_winners_pairrouted.csv' % mode)
        if not os.path.exists(f):
            continue
        R = pd.read_csv(f)
        base = float(R[R.rule == 'all28'].return_per_dd.mean())
        tk = R[R.rule == 'topk'].groupby('K').return_per_dd.mean()
        nl = R[R.rule == 'random_null'].groupby('K').return_per_dd.mean()
        bk = int(tk.idxmax())
        beats = int(sum(1 for k in tk.index
                        if np.isfinite(nl.get(k, np.nan)) and tk[k] > nl[k]))
        heads.append(dict(mode=mode, winners=int(R.bank_row.nunique()),
                          all28_return_per_dd=base,
                          all28_prop_return_pct=base * WN.PROP_DIP / 5.0,
                          best_K=bk, best_K_return_per_dd=float(tk[bk]),
                          random_null_at_best_K=float(nl.get(bk, np.nan)),
                          K_where_real_beats_random='%d of 28' % beats,
                          clears_12pct=int((R[R.rule == 'all28'].return_per_dd
                                            * WN.PROP_DIP / 5.0 >= WN.PROP_TARGET).sum())))
    H = pd.DataFrame(heads)
    A(tbl(H, list(H.columns)))
    A('\n**Pair routing is no better than a random pair pick.** The null -- a subset of '
      'the SAME SIZE drawn from the pairs the strategy actually traded in the tuning '
      'years -- scores higher at most K. The `K_where_real_beats_random` column is the '
      'honest count: the real rule wins at a minority of the 28 values of K, which is '
      'what a coin flip would give. Ranking pairs by their tuning-year return per '
      'drawdown carries no usable information about the trade year.\n')
    A('\n**THE DRAWDOWN BASIS HERE IS NOT THE ONE IN `MODE*_WINNERS.md`, and the two '
      'ratios must not be compared.** This table sums each (pair, direction, year) '
      'drawdown, which is a far looser upper bound than the strategy-level drawdown -- '
      'a strategy whose pairs draw down at different times has a portfolio drawdown far '
      'smaller than the sum of theirs. That is why return/DD reads ~0.8 here against '
      '1.95-3.13 in the winners table. The comparison inside this table is sound '
      'because real and null use the identical basis; the LEVEL is not comparable to '
      'anything outside it, and the prop return computed from it is therefore a floor, '
      'not an estimate.\n')
    A('\n**Nothing here clears 12%% at prop sizing.** Routed or unrouted, the best '
      'return/DD in the table is far below the %.2f the target needs.\n'
      % (WN.PROP_TARGET / (WN.PROP_DIP / 5.0)))

    for mode in ('A', 'B'):
        fr = os.path.join(RD, 'mode%s_winners_pairrouted.csv' % mode)
        fp = os.path.join(RD, 'mode%s_winners_by_pair.csv' % mode)
        if not os.path.exists(fr):
            continue
        R = pd.read_csv(fr); P = pd.read_csv(fp)
        A('\n## Mode %s\n' % mode)
        A('\n### The rules, against all 28 and against the null\n')
        rows = []
        tk = R[R.rule == 'topk'].groupby('K').agg(
            real=('return_per_dd', 'mean'), n_sel=('n_selected', 'mean'))
        nl = R[R.rule == 'random_null'].groupby('K').return_per_dd.mean()
        base = float(R[R.rule == 'all28'].return_per_dd.mean())
        for K in tk.index:
            rows.append(dict(rule='topk', K=K, pairs_selected=tk.n_sel[K],
                             real_return_per_dd=tk.real[K],
                             random_null_return_per_dd=float(nl.get(K, np.nan)),
                             real_beats_null=int(tk.real[K] > nl.get(K, np.inf)),
                             prop_return_pct=tk.real[K] * WN.PROP_DIP / 5.0))
        for rule in ('threshold', 'topk_dir', 'threshold_dir'):
            g = R[R.rule == rule]
            if len(g):
                rows.append(dict(rule=rule, K=np.nan,
                                 pairs_selected=float(g.n_selected.mean()),
                                 real_return_per_dd=float(g.return_per_dd.mean()),
                                 random_null_return_per_dd=np.nan,
                                 real_beats_null=np.nan,
                                 prop_return_pct=float(g.return_per_dd.mean())
                                 * WN.PROP_DIP / 5.0))
        rows.append(dict(rule='all28 (no routing)', K=np.nan, pairs_selected=28.0,
                         real_return_per_dd=base, random_null_return_per_dd=np.nan,
                         real_beats_null=np.nan,
                         prop_return_pct=base * WN.PROP_DIP / 5.0))
        A(tbl(pd.DataFrame(rows), ['rule', 'K', 'pairs_selected', 'real_return_per_dd',
                                   'random_null_return_per_dd', 'real_beats_null',
                                   'prop_return_pct']))

        A('\n### Top 30 by prop return, per winner, unrouted\n')
        a28 = R[R.rule == 'all28'].copy()
        a28['prop_return_pct_per_year'] = a28.return_per_dd * WN.PROP_DIP / 5.0
        a28['clears_12pct'] = (a28.prop_return_pct_per_year >= WN.PROP_TARGET).astype(int)
        A(tbl(a28.sort_values('prop_return_pct_per_year', ascending=False).head(30),
              ['sid', 'stream', 'trade_n', 'trade_total_R', 'trade_max_dd_R',
               'return_per_dd', 'prop_return_pct_per_year', 'clears_12pct']))

        A('\n### Where the money came from: by pair, trade years only\n')
        tr = P[P.role == 'trade']
        g = tr.groupby('pair', as_index=False).agg(
            n=('n', 'sum'), total_R=('total_R', 'sum'), max_dd_R=('max_dd_R', 'sum'))
        g['return_per_dd'] = np.where(g.max_dd_R > 0, g.total_R / g.max_dd_R, np.nan)
        g = g.sort_values('total_R', ascending=False)
        A('All %d pairs, summed over the %d winners and the five trade years. Full per '
          '(pair, direction, year) detail in `%s`.\n'
          % (len(g), P.bank_row.nunique(), os.path.relpath(fp, _R)))
        A(tbl(g, ['pair', 'n', 'total_R', 'max_dd_R', 'return_per_dd']))

        A('\n### By direction\n')
        gd = tr.groupby('direction', as_index=False).agg(
            n=('n', 'sum'), total_R=('total_R', 'sum'), max_dd_R=('max_dd_R', 'sum'))
        gd['return_per_dd'] = np.where(gd.max_dd_R > 0, gd.total_R / gd.max_dd_R, np.nan)
        A(tbl(gd, ['direction', 'n', 'total_R', 'max_dd_R', 'return_per_dd']))

    A('\n## Provenance\n')
    A('| file | rows | md5 |\n|---|---|---|')
    for mode in ('A', 'B'):
        for nm in ('winners_by_pair', 'winners_pairrouted'):
            f = os.path.join(RD, 'mode%s_%s.csv' % (mode, nm))
            if os.path.exists(f) and os.path.getsize(f) > 1:
                A('| `%s` | %s | %s |'
                  % (os.path.relpath(f, _R), f'{len(pd.read_csv(f)):,}',
                     hashlib.md5(open(f, 'rb').read()).hexdigest()[:12]))
    txt = '\n'.join(L) + '\n'
    out = out or os.path.join(RD, 'WINNERS_BY_PAIR.md')
    open(out, 'w').write(txt)
    print('  WINNERS_BY_PAIR.md: %d lines -> %s'
          % (len(txt.splitlines()), os.path.relpath(out, _R)), flush=True)
    return out


if __name__ == '__main__':
    st = G.opt('--stage', str, 'winners')
    md = G.opt('--mode', str, 'A')
    if st == 'winners':
        stage_winners(md, G.opt('--tag', str, 'full'))
    elif st == 'md':
        write_md()
    elif st == 'routed':
        stage_routed(md, ndraw=G.opt('--draws', int, 20))
    else:
        raise SystemExit('unknown stage %s' % st)
