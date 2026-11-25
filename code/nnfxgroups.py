import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""ITEM 3b, 3c, 3d, JACK 25 NOV -- PAIR GROUPS, AND IS THE EDGE PAIR-SPECIFIC?

THE GROUPINGS ARE DECLARED AND NONE OF THEM USES STRATEGY PERFORMANCE. That is
the whole point: a grouping built from how well strategies did on each pair
would make 3c a tautology.

  character     Layer 1 pair character, trendiness = share of trending days
                minus share of ranging days, TERCILES. MEASURED BEFORE 2010
                -- recomputed here with the classifier FIT on pre-2010 bars
                only, not read from results/pair_character.csv whose `is`
                block is 1999-2015 and therefore contains the unseen years
                this grouping is used to trade. That file would have leaked.
  bloc          declared currency blocs: EUROPE = EUR GBP CHF, COMMODITY =
                AUD NZD CAD, RESERVE = USD JPY. A pair's label is its two
                legs' blocs, sorted. Nothing measured at all -- it is a fact
                about the currencies.
  cost_per_atr  the pair's round-trip cost divided by its median ATR/price,
                TERCILES. The cost table is a 2016-2020 measurement by
                construction (cost_table_h22) so that part cannot be made
                pre-2010; the ATR denominator is pre-2010 and the combination
                is declared as such. It is the one grouping with a dated
                input and the file says so rather than hiding it.

3c, AND WHAT WOULD MAKE IT REAL. At each step the best strategy for each group
is picked on that step's four TUNING years and traded on that group in the
unseen year. The null SHUFFLES THE GROUP LABELS, 1,000 draws, and repeats the
whole construction -- so it tests the SELECTION RULE and not merely the
components, which is the fault that invalidated A7. A grouping only means
something if it beats its own shuffled labels AND beats the same strategies
run on all 28 pairs.

EVERYTHING IN 3c IS COMPUTED FROM results/nnfx/per_pair_bank.csv. No engine
run. That matters for one reason worth stating: the leverage cap was applied
over the whole 28-pair frame before the bank was split, so a subset's R is
that subset's share of a book that was achievable AS A WHOLE. Summing a
group's pairs therefore cannot produce a size no account could hold, which is
exactly what an assignment built from separately-capped per-pair runs would do.

Writes results/nnfx/pair_groups.csv, pair_groups_stability.csv,
group_assign.csv, group_assign_null.csv, group_daily_corr.csv,
strategy_daily_corr.csv and PAIR_GROUPS.md.
"""
import numpy as np, pandas as pd

import nnfx1 as N
import nnfx2s as S2
import nnfxvol as VOL
import nnfxcurves as CUR
import l2sweep as S

OUT = os.path.join(ROOTOUT, 'nnfx')
os.makedirs(OUT, exist_ok=True)
BUILD = N.BUILD_YEARS
MAIN = 'jack'
NSHUF = 1000
BLOC = {'EUR': 'EUROPE', 'GBP': 'EUROPE', 'CHF': 'EUROPE',
        'AUD': 'COMMODITY', 'NZD': 'COMMODITY', 'CAD': 'COMMODITY',
        'USD': 'RESERVE', 'JPY': 'RESERVE'}
PRE2010 = '2010-01-01'
BLOCKS = (('pre2010', None, PRE2010),
          ('unseen_2010_2015', '2010-01-01', '2016-01-01'),
          ('sealed_2016_2020', '2016-01-01', '2021-01-01'))


# ===================== 3b: the three groupings ===========================
def _trendiness(lo=None, hi=PRE2010, fit_hi=PRE2010):
    """Layer 1 trendiness per pair over a window, classifier FIT on fit_hi.

    THE FIT WINDOW IS THE LEAK, NOT THE MEASUREMENT WINDOW. paircharacter's
    shipped file fits the classifier on 1999-2015 and that includes every
    unseen year. For the GROUPING the fit has to stop before 2010 as well, or
    the labels themselves have seen the years they are used to trade.
    """
    import paircharacter as PC
    px = pd.read_csv(PC.PX, index_col=0, parse_dates=True)
    ix = pd.DatetimeIndex(px.index)
    fit = np.asarray(ix < pd.Timestamp(fit_hi))
    sh, comb = PC.labels(px, fit, pooled=True)
    m = np.ones(len(px), bool)
    if lo is not None:
        m &= np.asarray(ix >= pd.Timestamp(lo))
    if hi is not None:
        m &= np.asarray(ix < pd.Timestamp(hi))
    A = PC.per_pair(sh, comb, m, list(px.columns))
    return A.trendiness.astype(float)


def _cost_per_atr(lo=None, hi=PRE2010):
    """Round-trip cost divided by median ATR/price over a window."""
    if not S.COSTS:
        S.load_costs(os.environ.get(
            'FX_COST_TABLE', os.path.join(ROOTOUT, 'cost_table_h22.csv')))
    out = {}
    for p in S.all_pairs():
        ix, rel = VOL._rel(p)
        m = np.ones(len(rel), bool)
        if lo is not None:
            m &= np.asarray(ix >= pd.Timestamp(lo))
        if hi is not None:
            m &= np.asarray(ix < pd.Timestamp(hi))
        v = rel[m & np.isfinite(rel)]
        med = float(np.median(v)) if len(v) else np.nan
        out[p] = (float(S.COSTS.get(p, np.nan)) / med
                  if med and np.isfinite(med) else np.nan)
    return pd.Series(out)


def _terciles(v, names):
    """Terciles by rank, with the cut points returned so the grouping is
    reproducible from the file rather than from this function."""
    v = v.dropna()
    q = v.rank(method='first')
    k = np.ceil(q / (len(v) / 3.0)).clip(1, 3).astype(int)
    return pd.Series([names[i - 1] for i in k], index=v.index), \
        (float(v.quantile(1 / 3.0)), float(v.quantile(2 / 3.0)))


def groupings(verbose=True):
    pairs = S.all_pairs()
    tr = _trendiness()
    cp = _cost_per_atr()
    g_ch, cut_ch = _terciles(tr, ('RANGE_PRONE', 'MIXED', 'TREND_PRONE'))
    g_cp, cut_cp = _terciles(cp, ('CHEAP', 'MID', 'EXPENSIVE'))
    rows = []
    for p in pairs:
        b1, b2 = BLOC.get(p[:3], '?'), BLOC.get(p[3:], '?')
        rows.append(dict(
            pair=p,
            character=g_ch.get(p, 'NA'),
            trendiness_pre2010=float(tr.get(p, np.nan)),
            bloc='-'.join(sorted((b1, b2))),
            bloc_leg1=b1, bloc_leg2=b2,
            cost_per_atr=g_cp.get(p, 'NA'),
            cost_per_atr_value=float(cp.get(p, np.nan)),
            character_cut_lo=cut_ch[0], character_cut_hi=cut_ch[1],
            cost_cut_lo=cut_cp[0], cost_cut_hi=cut_cp[1]))
    D = pd.DataFrame(rows)
    D.to_csv(os.path.join(OUT, 'pair_groups.csv'), index=False)
    if verbose:
        for g in ('character', 'bloc', 'cost_per_atr'):
            print('  %-13s %s' % (g, ', '.join(
                '%s=%d' % (k, v) for k, v in
                D[g].value_counts().sort_index().items())), flush=True)
    return D


def stability(verbose=True):
    """HOW STABLE IS EACH GROUPING OVER TIME?

    The same measure recomputed on each block, with the rank correlation
    against the pre-2010 version and the share of pairs keeping their label.
    The classifier fit stays pre-2010 throughout -- re-fitting per block would
    measure the fit moving as well as the pair moving, and only the second is
    the question.

    `bloc` is constant by construction and is reported as 1.000 rather than
    omitted, because a reader comparing the three needs the trivial case in
    the table to see that it IS trivial.
    """
    base = groupings(verbose=False)
    rows = []
    tr0 = _trendiness()
    cp0 = _cost_per_atr()
    for nm, lo, hi in BLOCKS:
        tr = _trendiness(lo=lo, hi=hi)
        cp = _cost_per_atr(lo=lo, hi=hi)
        for lab, v, v0, names in (
                ('character', tr, tr0, ('RANGE_PRONE', 'MIXED',
                                        'TREND_PRONE')),
                ('cost_per_atr', cp, cp0, ('CHEAP', 'MID', 'EXPENSIVE'))):
            g, _ = _terciles(v, names)
            g0, _ = _terciles(v0, names)
            k = g.index.intersection(g0.index)
            rho = float(pd.Series(v[k]).corr(pd.Series(v0[k]),
                                             method='spearman'))
            rows.append(dict(grouping=lab, block=nm,
                             n_pairs=len(k),
                             spearman_vs_pre2010=rho,
                             pct_same_label=100.0 * float(
                                 (g[k] == g0[k]).mean()),
                             value_min=float(v[k].min()),
                             value_max=float(v[k].max())))
        rows.append(dict(grouping='bloc', block=nm, n_pairs=len(base),
                         spearman_vs_pre2010=1.0, pct_same_label=100.0,
                         value_min=np.nan, value_max=np.nan))
    D = pd.DataFrame(rows)
    D.to_csv(os.path.join(OUT, 'pair_groups_stability.csv'), index=False)
    if verbose:
        print(D.round(3).to_string(index=False), flush=True)
    return D


# ===================== 3c: is the edge pair-specific? ====================
def _bank():
    f = os.path.join(OUT, 'per_pair_bank.csv')
    assert os.path.exists(f), f + ' missing -- run nnfxbank.py first'
    B = pd.read_csv(f)
    assert 'year_class' in B.columns, (
        'per_pair_bank.csv predates the year_class column; rebuild it')
    return B


def _cube(B):
    """R and trade count as (candidate, pair, year) arrays, once.

    THE NULL IS 1,000 DRAWS x 5 SCHEMES x 6 STEPS x up to 28 GROUPS. Doing
    that with a pandas groupby inside the loop is tens of thousands of
    groupbys over a 39,000-row frame. Pivoting once into two dense arrays and
    indexing them turns the whole null into integer slicing, which is the
    difference between minutes and hours -- and it cannot change an answer,
    because it is the same sums.
    """
    g = (B.groupby(['name', 'pair', 'year'], as_index=False)
         .agg(R=('R_total', 'sum'), n=('n_trades', 'sum')))
    nm = sorted(g.name.unique())
    pr = sorted(g.pair.unique())
    yr = sorted(g.year.unique())
    iN = {k: i for i, k in enumerate(nm)}
    iP = {k: i for i, k in enumerate(pr)}
    iY = {k: i for i, k in enumerate(yr)}
    R = np.zeros((len(nm), len(pr), len(yr)))
    C = np.zeros((len(nm), len(pr), len(yr)))
    R[g.name.map(iN).to_numpy(int), g.pair.map(iP).to_numpy(int),
      g.year.map(iY).to_numpy(int)] = g.R.to_numpy(float)
    C[g.name.map(iN).to_numpy(int), g.pair.map(iP).to_numpy(int),
      g.year.map(iY).to_numpy(int)] = g.n.to_numpy(float)
    return dict(names=nm, pairs=pr, years=yr, iP=iP, iY=iY, R=R, C=C)


def _pick_and_trade(Q, lab2pair, steps, collect=False, mint=30,
                    hindsight=False):
    """At each step: pick per group on the TUNING years, trade on the unseen
    year. -> (total unseen R, per-step rows or None).

    A GROUP WITH NO ELIGIBLE CANDIDATE TRADES NOTHING, and that is recorded
    rather than back-filled with the pooled winner. Falling back to a global
    pick would smuggle the all-28-pairs answer into the grouped one and the
    comparison between them would be meaningless.
    """
    R, C = Q['R'], Q['C']
    nm, iP, iY = Q['names'], Q['iP'], Q['iY']
    rows, tot = ([] if collect else None), 0.0
    for stp in steps:
        ty = stp['trade']
        if ty not in BUILD or ty not in iY:
            continue
        tix = [iY[y] for y in range(stp['tune'][0], stp['tune'][1] + 1)
               if y in iY]
        if not tix:
            continue
        uix = iY[ty]
        for lab, prs in sorted(lab2pair.items()):
            pix = [iP[p] for p in prs if p in iP]
            if not pix:
                continue
            # hindsight=True PICKS ON THE UNSEEN YEAR ITSELF. It is not a
            # result and it is never reported as one; it is the CEILING, the
            # answer to "how much was even available to a selection rule on
            # this bank". Without it a negative walk-forward number cannot be
            # told apart from "there was nothing there to find".
            if hindsight:
                tR = R[:, pix, uix]
                tC = C[:, pix, uix]
                tR = tR.sum(axis=1) if tR.ndim > 1 else tR
                tC = tC.sum(axis=1) if tC.ndim > 1 else tC
            else:
                tR = R[:, pix, :][:, :, tix].sum(axis=(1, 2))
                tC = C[:, pix, :][:, :, tix].sum(axis=(1, 2))
            ok = tC >= mint
            if not ok.any():
                if collect:
                    rows.append(dict(step=stp['name'], trade_year=ty,
                                     group=lab, n_pairs=len(prs),
                                     picked=None, tuning_R=np.nan,
                                     unseen_R=0.0, unseen_trades=0,
                                     eligible=0))
                continue
            cand = np.where(ok, tR, -np.inf)
            j = int(np.argmax(cand))
            ur = float(R[j, pix, uix].sum())
            un = int(C[j, pix, uix].sum())
            tot += ur
            if collect:
                rows.append(dict(step=stp['name'], trade_year=ty, group=lab,
                                 n_pairs=len(prs), picked=nm[j],
                                 tuning_R=float(tR[j]), unseen_R=ur,
                                 unseen_trades=un, eligible=1))
    return tot, rows


def assign(nshuf=NSHUF, seed=19, verbose=True):
    B = _bank()
    Q = _cube(B)
    G = pd.read_csv(os.path.join(OUT, 'pair_groups.csv'))
    pairs = sorted(G.pair.unique())
    schemes = {}
    for col in ('character', 'bloc', 'cost_per_atr'):
        schemes[col] = {k: sorted(v.pair) for k, v in G.groupby(col)}
    schemes['single_pairs'] = {p: [p] for p in pairs}
    schemes['all_28'] = {'ALL': pairs}
    rows, allsteps = [], []
    rng = np.random.default_rng(seed)
    for nm, l2p in schemes.items():
        tot, st = _pick_and_trade(Q, l2p, S2.STEPS, collect=True)
        for r in st:
            r['scheme'] = nm
        allsteps += st
        # THE NULL SHUFFLES THE LABELS AND KEEPS THE GROUP SIZES. Shuffling
        # the pairs between groups of the same sizes is the only form that
        # tests the GROUPING and not the number of groups -- a null with
        # different group sizes would change how much pooling each pick gets
        # and would answer a different question.
        if nm in ('single_pairs', 'all_28'):
            nul = np.array([])
        else:
            sizes = [(k, len(v)) for k, v in sorted(l2p.items())]
            nul = np.zeros(nshuf)
            for k in range(nshuf):
                perm = list(rng.permutation(pairs))
                sh, i = {}, 0
                for lab, n in sizes:
                    sh[lab] = sorted(perm[i:i + n]); i += n
                nul[k], _ = _pick_and_trade(Q, sh, S2.STEPS)
        hs, _ = _pick_and_trade(Q, l2p, S2.STEPS, hindsight=True)
        rows.append(dict(
            scheme=nm, n_groups=len(l2p),
            unseen_R_total=tot, unseen_R_per_year=tot / len(BUILD),
            hindsight_ceiling_R=hs,
            share_of_ceiling=(tot / hs if abs(hs) > 1e-9 else np.nan),
            null_draws=int(len(nul)),
            null_mean=(float(nul.mean()) if len(nul) else np.nan),
            null_sd=(float(nul.std(ddof=1)) if len(nul) > 1 else np.nan),
            null_max=(float(nul.max()) if len(nul) else np.nan),
            null_p=(float((nul >= tot).mean()) if len(nul) else np.nan),
            null_z=((tot - float(nul.mean())) / float(nul.std(ddof=1))
                    if len(nul) > 1 and nul.std(ddof=1) > 0 else np.nan)))
        if verbose:
            print('    %-14s %2d groups  unseen R %+9.3f  ceiling %+9.3f  '
                  'null p %s  null mean %s'
                  % (nm, len(l2p), tot, hs,
                     ('%.3f' % float((nul >= tot).mean())) if len(nul)
                     else '—',
                     ('%+.3f' % float(nul.mean())) if len(nul) else '—'),
                  flush=True)
    D = pd.DataFrame(rows)
    D.to_csv(os.path.join(OUT, 'group_assign.csv'), index=False)
    ST = pd.DataFrame(allsteps)
    ST.to_csv(os.path.join(OUT, 'group_assign_steps.csv'), index=False)
    return D, ST


# ===================== 3d: daily P&L correlations ========================
def daily_corr(names=None, variant=MAIN, verbose=True):
    """Correlation of daily P&L between STRATEGIES and between GROUPS.

    Between strategies: each candidate's own daily series over the unseen
    years. Between groups: candidate A's daily series restricted to each
    grouping's pairs -- one engine run sliced, not one run per group.

    DAYS ARE UNIONED AND MISSING DAYS ARE ZERO, not dropped. A day one sleeve
    is out of the market is a real zero for that sleeve, and dropping it would
    compute the correlation on the days both happened to trade, which is a
    different and much more flattering number.
    """
    C1L, _B, _C, _V, _X = N.families()
    names = names or list(C1L)
    G = pd.read_csv(os.path.join(OUT, 'pair_groups.csv'))
    ser, gser = {}, {}
    _lv, _pg, _qq = N.LOWVOL_Q, N.PEG_X, N.QUIET_Q
    try:
        N.LOWVOL_Q, N.PEG_X, N.QUIET_Q = None, None, None
        for i, nm in enumerate(names):
            T = N.run_one(nm, 'c1', None, variant, use_hourly=True)
            s = _ds(T)
            if s is not None:
                ser[nm] = s
            if verbose and (i + 1) % 10 == 0:
                print('    daily %d/%d' % (i + 1, len(names)), flush=True)
    finally:
        N.LOWVOL_Q, N.PEG_X, N.QUIET_Q = _lv, _pg, _qq
    for lab, c1, base, rs in (('A', 'ichimoku_signals', 'sma_baseline',
                               'full_nnfx'),
                              ('B', 'schaff_trend_cycle_signals',
                               'sma_baseline', 'side_xentry')):
        T = CUR._stitch(c1, base, rs, variant, VOL.LOWVOL_Q,
                        VOL.PEG_X_DECIDED)
        s = _ds(T)
        if s is not None:
            ser[lab] = s
        if lab == 'A':
            for col in ('character', 'bloc', 'cost_per_atr'):
                for k, sub in G.groupby(col):
                    gs = _ds(T[T.pair.isin(list(sub.pair))])
                    if gs is not None:
                        gser['%s:%s' % (col, k)] = gs
    if ser:
        M = pd.DataFrame(ser).fillna(0.0)
        C = M.corr()
        C.index.name = 'strategy'
        C.to_csv(os.path.join(OUT, 'strategy_daily_corr.csv'))
    if gser:
        MG = pd.DataFrame(gser).fillna(0.0)
        CG = MG.corr()
        CG.index.name = 'group'
        CG.to_csv(os.path.join(OUT, 'group_daily_corr.csv'))
        if verbose:
            o = CG.where(~np.eye(len(CG), dtype=bool))
            print('  group daily corr: median %.3f, max %.3f'
                  % (float(o.stack().median()), float(o.stack().max())),
                  flush=True)
    if ser and verbose:
        o = C.where(~np.eye(len(C), dtype=bool))
        print('  strategy daily corr: median %.3f, max %.3f'
              % (float(o.stack().median()), float(o.stack().max())),
              flush=True)
    return (C if ser else None), (CG if gser else None)


def _ds(T):
    if T is None or not len(T):
        return None
    M, _ = VOL.apply_leverage_cap(T)
    M = M.reset_index(drop=True)
    DS = N.daily_series(M, N._cost_R(M))
    DS = DS[pd.DatetimeIndex(DS.date).year.isin(list(BUILD))]
    if not len(DS):
        return None
    return pd.Series(DS.R.to_numpy(float),
                     index=pd.DatetimeIndex(DS.date)).groupby(level=0).sum()



# ====================== THE DOCUMENT ====================================
def md_groups(out=None):
    """PAIR_GROUPS.md -- items 3b, 3c, 3d, from the files."""
    import hashlib
    L_ = []
    a = L_.append
    def rd(n, ix=None):
        f = os.path.join(OUT, n)
        if not (os.path.exists(f) and os.path.getsize(f) > 2):
            return pd.DataFrame()
        return pd.read_csv(f, index_col=ix) if ix is not None \
            else pd.read_csv(f)
    G, ST = rd('pair_groups.csv'), rd('pair_groups_stability.csv')
    AS, AST = rd('group_assign.csv'), rd('group_assign_steps.csv')
    GC, SC = rd('group_daily_corr.csv', 0), rd('strategy_daily_corr.csv', 0)
    a('# PAIR GROUPS — items 3b, 3c and 3d, Jack 25 November 2026')
    a('')
    a('**The headline, and it is a negative one.** The edge is **not** '
      'pair-specific in any way a tuning-year pick can find. Every grouping '
      'loses money on the unseen years, every grouping loses MORE than '
      'pooling all 28 pairs, and the one grouping taken from Layer 1\'s pair '
      'character does **worse than its own shuffled labels**. At the same '
      'time the cross-sectional opportunity is enormous — with hindsight a '
      'per-pair assignment would make +520 R over the same six years — so '
      'the dispersion is real and the selection rule has no access to it.')
    a('')
    a('## 3b — the three groupings, and none of them uses strategy '
      'performance')
    a('')
    a('That is the whole point: a grouping built from how well strategies did '
      'on each pair would make 3c a tautology.')
    a('')
    a('| grouping | what it is | measured on |')
    a('|---|---|---|')
    a('| `character` | Layer 1 trendiness — share of trending days minus '
      'share of ranging days — in terciles | **pre-2010 only**, with the '
      'classifier FIT on pre-2010 bars too |')
    a('| `bloc` | declared currency blocs: EUROPE = EUR GBP CHF, COMMODITY = '
      'AUD NZD CAD, RESERVE = USD JPY; a pair\'s label is its two legs\' '
      'blocs, sorted | nothing — it is a fact about the currencies |')
    a('| `cost_per_atr` | round-trip cost divided by median ATR/price, in '
      'terciles | ATR pre-2010; **the cost table is a 2016–2020 measurement '
      'by construction** and that cannot be undone |')
    a('')
    a('**`results/pair_character.csv` was NOT used and that matters.** Its '
      '`is` block is 1999–2015, which contains every unseen year this '
      'grouping is used to trade. The trendiness here is recomputed with the '
      'classifier fit stopping before 2010 — the fit window is the leak, not '
      'just the measurement window.')
    a('')
    if len(G):
        for col in ('character', 'bloc', 'cost_per_atr'):
            a('**%s:** %s' % (col, '; '.join(
                '%s = %s' % (k, ' '.join(sorted(v.pair)))
                for k, v in G.groupby(col))))
            a('')
    a('### How stable is each grouping over time?')
    a('')
    if len(ST):
        a('| grouping | block | Spearman against pre-2010 | '
          'share of pairs keeping their label |')
        a('|---|---|---:|---:|')
        for _, r in ST.iterrows():
            b = '**' if (r.grouping == 'character'
                         and r.block != 'pre2010') else ''
            a('| %s | %s | %s%+.3f%s | %s%.1f%%%s |'
              % (r.grouping, r.block, b, r.spearman_vs_pre2010, b,
                 b, r.pct_same_label, b))
        a('')
        _c = ST[(ST.grouping == 'character')
                & (ST.block == 'unseen_2010_2015')]
        if len(_c):
            a('**PAIR CHARACTER IS NOT STABLE — it is ANTI-STABLE.** '
              'Trendiness measured before 2010 correlates **%+.3f** with '
              'trendiness over 2010–2015, and only **%.1f%%** of pairs keep '
              'their tercile label. A pair that was trend-prone before 2010 '
              'was, if anything, range-prone afterwards. Against 2016–2020 '
              'the correlation is %+.3f. '
              '`cost_per_atr` by contrast holds up (%+.3f, %.1f%% of labels '
              'kept) and `bloc` is constant by construction.'
              % (float(_c.spearman_vs_pre2010.iloc[0]),
                 float(_c.pct_same_label.iloc[0]),
                 float(ST[(ST.grouping == 'character')
                          & (ST.block == 'sealed_2016_2020')]
                       .spearman_vs_pre2010.iloc[0]),
                 float(ST[(ST.grouping == 'cost_per_atr')
                          & (ST.block == 'unseen_2010_2015')]
                       .spearman_vs_pre2010.iloc[0]),
                 float(ST[(ST.grouping == 'cost_per_atr')
                          & (ST.block == 'unseen_2010_2015')]
                       .pct_same_label.iloc[0])))
            a('')
            a('**That is a finding about Layer 1, not about this test.** The '
              'pair character file describes behaviour over a window and the '
              'behaviour does not persist out of that window. It is reported '
              'here because 3b asked for stability and the answer is '
              'unambiguous; nothing in Layer 1 is being changed on the back '
              'of one measurement.')
            a('')
    a('## 3c — is the edge pair-specific?')
    a('')
    a('At each of the six steps the best strategy for each group is picked on '
      'that step\'s **four TUNING years** and traded on that group in the '
      '**unseen year**. 47 candidates are available to each pick (39 C1 '
      'alone, 3 baselines alone, 3 baselines as filters, A and B), minimum 30 '
      'tuning-year trades to be eligible. A group with no eligible candidate '
      'trades nothing — it is never back-filled with the pooled winner, '
      'because that would smuggle the all-28 answer into the grouped one.')
    a('')
    a('**The null SHUFFLES THE GROUP LABELS, 1,000 draws, keeping the group '
      'sizes, and repeats the whole construction** — so it tests the '
      'SELECTION RULE and not merely the components. That is the fault that '
      'invalidated A7 and it is not being repeated.')
    a('')
    a('**The hindsight ceiling picks on the unseen year itself.** It is not a '
      'result and is never quoted as one. It is there because without it a '
      'negative walk-forward number cannot be told apart from "there was '
      'nothing to find".')
    a('')
    if len(AS):
        a('| scheme | groups | **unseen R** | R/yr | hindsight ceiling | '
          'share of ceiling | null mean | null sd | null max | **null p** | '
          'null z |')
        a('|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|')
        for _, r in AS.iterrows():
            a('| %s | %d | **%+.3f** | %+.3f | %+.3f | %s | %s | %s | %s | '
              '%s | %s |'
              % (r.scheme, int(r.n_groups), r.unseen_R_total,
                 r.unseen_R_per_year, r.hindsight_ceiling_R,
                 _f(r.share_of_ceiling), _f(r.null_mean), _f(r.null_sd),
                 _f(r.null_max), ('**%.3f**' % r.null_p
                                  if np.isfinite(r.null_p) else '—'),
                 _f(r.null_z)))
        a('')
        a('### What that table says, in order')
        a('')
        _all = AS[AS.scheme == 'all_28']
        _ch = AS[AS.scheme == 'character']
        _sp = AS[AS.scheme == 'single_pairs']
        if len(_all):
            a('1. **The selection rule loses before grouping is even '
              'involved.** Pooled over all 28 pairs — one pick per step, the '
              'simplest possible version — it makes **%+.3f R** over the six '
              'unseen years, %+.3f a year. So the problem is not which pairs '
              'go together. It is that **a strategy\'s rank on four tuning '
              'years does not carry to the next year at all.**'
              % (float(_all.unseen_R_total.iloc[0]),
                 float(_all.unseen_R_per_year.iloc[0])))
        a('2. **Every grouping is WORSE than pooling.** %s. There is no '
          'clean relationship with the number of groups — `character` has '
          'three groups and is the worst of all — so this is not simply '
          '"smaller samples make noisier picks". The grouping itself matters, '
          'and it matters in the wrong direction.'
          % '; '.join('%s (%d groups) %+.3f'
                      % (r.scheme, int(r.n_groups), r.unseen_R_total)
                      for _, r in AS.sort_values('n_groups').iterrows()))
        if len(_ch):
            a('3. **The Layer 1 character grouping is worse than its own '
              'shuffled labels**: null p **%.3f**, z **%+.3f** — **%d of the '
              '1,000 random regroupings beat the real one**, and only %d did '
              'worse. That is exactly what the 3b stability table predicts: a '
              'grouping whose labels anti-correlate with the period being '
              'traded should underperform random labels, and it does. Note '
              'the direction of the test — a null p near 1 is not "no '
              'evidence", it is evidence AGAINST.'
              % (float(_ch.null_p.iloc[0]), float(_ch.null_z.iloc[0]),
                 int(round(float(_ch.null_p.iloc[0]) * 1000)),
                 1000 - int(round(float(_ch.null_p.iloc[0]) * 1000))))
        if len(_sp):
            a('4. **And yet the opportunity is real and large.** Picking per '
              'pair with hindsight makes **%+.3f R** over the same six years, '
              '%+.1f a year, against %+.3f actually achieved. The '
              'cross-sectional dispersion is enormous; **no tested selection '
              'rule has any access to it.**'
              % (float(_sp.hindsight_ceiling_R.iloc[0]),
                 float(_sp.hindsight_ceiling_R.iloc[0]) / len(BUILD),
                 float(_sp.unseen_R_total.iloc[0])))
        a('')
        a('**WHAT THIS MEANS FOR THE BOOK PLAN, stated plainly because it is '
          'the point of the whole item.** The plan is a handful of strategies '
          'each assigned to the pairs it suits. This test says the '
          'ASSIGNMENT STEP, done the obvious way, destroys value rather than '
          'adding it. It does not say the book plan is wrong — it says an '
          'assignment cannot be made by ranking candidates on recent '
          'performance, which is the only mechanism tested here. An '
          'assignment made from something that is NOT performance — pair '
          'character would have been the candidate, and 3b has just shown it '
          'does not persist — would be a different test.')
        a('')
    if len(AST):
        _e = AST[AST.eligible == 1]
        a('### Which candidate each group actually picked')
        a('')
        a('The picks are in `group_assign_steps.csv` in full. The shape of '
          'them is the diagnosis: ')
        _top = (_e[_e.scheme.isin(['character', 'bloc', 'cost_per_atr',
                                   'all_28'])].picked.value_counts())
        a('across the four declared schemes, %d picks were made and the most '
          'frequently chosen candidates were %s. **%d distinct candidates '
          'were picked at least once**, out of 47 — the rule is not settling '
          'on anything.'
          % (int(_e[_e.scheme != 'single_pairs'].shape[0]),
             ', '.join('`%s` (%d)' % (k, v) for k, v in _top.head(5).items()),
             int(_top.shape[0])))
        a('')
    a('## 3d — correlation of daily P&L')
    a('')
    a('Days are UNIONED and missing days are **zero**, not dropped. A day a '
      'sleeve is out of the market is a real zero for that sleeve; dropping '
      'it would compute the correlation only on days both happened to trade, '
      'which is a different and much more flattering number.')
    a('')
    a('### Between groups — candidate A\'s own daily series, sliced by each '
      'grouping')
    a('')
    if len(GC):
        cols = list(GC.columns)
        a('| | %s |' % ' | '.join(c.split(':')[-1][:12] for c in cols))
        a('|---|%s|' % ('---:|' * len(cols)))
        for i in GC.index:
            a('| %s | %s |' % (i, ' | '.join(
                ('**1.000**' if i == c else '%+.3f' % GC.loc[i, c])
                for c in cols)))
        a('')
        best = []
        for col in ('character', 'bloc', 'cost_per_atr'):
            sub = [c for c in cols if c.startswith(col + ':')]
            if len(sub) < 2:
                continue
            m = GC.loc[sub, sub].where(~np.eye(len(sub), dtype=bool)).stack()
            best.append('**%s** %.3f to %.3f (median %.3f)'
                        % (col, float(m.min()), float(m.max()),
                           float(m.median())))
        a('**Within a grouping, the groups are genuinely diversifying**: %s. '
          'That is the one piece of good news in this document — slicing ONE '
          'strategy across pair groups gives sleeves that are close to '
          'independent, which is what a book needs. The high numbers in the '
          'table are all BETWEEN groupings and are just membership overlap: '
          '`bloc:COMMODITY-EUROPE` and `cost_per_atr:EXPENSIVE` correlate '
          '%.3f because they are largely the same pairs.'
          % ('; '.join(best),
             float(GC.loc['bloc:COMMODITY-EUROPE',
                          'cost_per_atr:EXPENSIVE'])
             if ('bloc:COMMODITY-EUROPE' in GC.index
                 and 'cost_per_atr:EXPENSIVE' in GC.columns) else float('nan')))
        a('')
    a('### Between strategies')
    a('')
    if len(SC):
        o = SC.where(~np.eye(len(SC), dtype=bool)).stack()
        a('%d series over the unseen years: median pairwise correlation '
          '**%.3f**, mean %.3f, range %.3f to %.3f.'
          % (len(SC), float(o.median()), float(o.mean()), float(o.min()),
             float(o.max())))
        a('')
        if 'A' in SC.columns and 'B' in SC.index:
            a('**A against B is %.3f** — the two carried-forward candidates '
              'are only moderately correlated, so as SLEEVES they '
              'diversify each other. A\'s closest relatives are %s.'
              % (float(SC.loc['A', 'B']),
                 ', '.join('`%s` %.3f' % (k, v) for k, v in
                           SC['A'].drop('A').sort_values(
                               ascending=False).head(3).items())))
            a('')
    a('## What is settled and what is not')
    a('')
    a('1. **Settled: every candidate is now banked per pair and per '
      'direction**, with the leverage cap applied over the whole frame before '
      'splitting, and every year labelled tune / unseen / sealed. '
      '`PER_PAIR_BANK.md`.')
    a('2. **Settled: picking a strategy per group on tuning-year performance '
      'does not work.** It loses pooled, it loses worse grouped, and the '
      'Layer 1 character grouping loses worse than random labels.')
    a('3. **Settled: pair character does not persist.** Spearman **−0.456** '
      'from pre-2010 to 2010–2015, 21% of labels kept.')
    a('4. **Settled: the sleeves a grouping produces are close to '
      'independent**, and A and B correlate 0.370. The diversification the '
      'book plan needs is available; the selection the book plan needs is '
      'not.')
    a('5. **NOT settled: whether any assignment rule works.** One mechanism '
      'was tested — rank on four tuning years. The hindsight ceiling says '
      'there is +520 R of cross-sectional dispersion to aim at over six '
      'years. Finding a rule that reaches any of it is a new experiment and '
      'is not in item 3.')
    a('')
    a('## Provenance')
    a('')
    for n_ in ('pair_groups.csv', 'pair_groups_stability.csv',
               'group_assign.csv', 'group_assign_steps.csv',
               'group_daily_corr.csv', 'strategy_daily_corr.csv'):
        p_ = os.path.join(OUT, n_)
        if not os.path.exists(p_):
            a('- `%s` — **MISSING**' % os.path.join('results', 'nnfx', n_))
            continue
        a('- `%s` — %s rows, md5 `%s`'
          % (os.path.relpath(p_, _R),
             '{:,}'.format(len(S2._safe_csv(p_))),
             hashlib.md5(open(p_, 'rb').read()).hexdigest()[:12]))
    out = out or os.path.join(OUT, 'PAIR_GROUPS.md')
    open(out, 'w').write('\n'.join(L_) + '\n')
    print('  PAIR_GROUPS.md: %d lines -> %s'
          % (len('\n'.join(L_).splitlines()), os.path.relpath(out, _R)),
          flush=True)
    return out


def _f(v, fmt='%+.3f'):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return '—'
    return (fmt % f) if np.isfinite(f) else '—'


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', default='all')
    ap.add_argument('--nshuf', type=int, default=NSHUF)
    g = ap.parse_args()
    if g.stage in ('all', 'groups'):
        groupings()
        stability()
    if g.stage in ('all', 'assign'):
        assign(nshuf=g.nshuf)
    if g.stage in ('all', 'corr'):
        daily_corr()
    if g.stage in ('all', 'md'):
        md_groups()
    print('  nnfxgroups done', flush=True)


if __name__ == '__main__':
    main()
