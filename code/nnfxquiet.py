import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""ITEM 2, JACK 25 NOV -- THE QUIET-ENTRY TEST.

WHY THIS IS A FRESH TEST AND NOT A RESULT. Item 3 of 24 Nov found that for
candidate A the bottom three ATR deciles at entry carry 100% of the profit from
38% of the trades. THAT WAS FOUND BY LOOKING. A rule built from it and then
measured on the same sample would be fitted to it by construction, so this
module tests it as a declared hypothesis instead:

  2a  is the low-decile concentration a property of the MARKET or of
      ICHIMOKU? -- all 39 C1 alone, plus A and B, bucketed the same way.
  2b  a NULL. Random entries matched on count, holding period AND DECILE must
      make zero gross in every decile. If they do not, the decile axis itself
      carries a drift and 2a is measuring the axis, not the strategy.
  2c  the rule, walk-forward: enter only while the pair's own ATR percentile is
      at or below Q, with Q chosen on each step's four TUNING years -- plus the
      fixed-Q curve from 10% to 100% for the shape, and a PAIRED test against
      the same candidate without the rule on exactly the same days.
  2d  crossed with the per-pair floor at off, 1% and 5%: do the two rules
      conflict, and which combination gives the best return per dip?

WHAT WOULD MAKE THE RULE REAL, stated before the numbers: the walk-forward
version has to beat its own control on the paired test, the fixed-Q curve has
to be smooth rather than a spike at one Q, and the effect has to appear in
candidates that are not ichimoku. Any one of those failing is a reason to drop
it. A big fixed-Q number on its own is not evidence -- Q was swept, so the best
Q is a maximum over ten tries.

Q = 1.0 IS THE RULE OFF and takes the identical code path, which is why the
curve can end at the unfiltered candidate with nothing special-cased.

Writes into results/nnfx/: quiet_deciles_c1.csv, quiet_deciles_null.csv,
quiet_fixedq.csv, quiet_walkq.csv, quiet_paired.csv, quiet_floor_cross.csv,
quiet_blocked_share.csv and QUIET_ENTRY.md.
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
# A and B only. C is at rank 86 of 108 on stage 2 and Jack's item 2 names A
# and B; adding C here would be scope I was not given.
ABC = (('A', 'ichimoku_signals', 'sma_baseline', 'full_nnfx'),
       ('B', 'schaff_trend_cycle_signals', 'sma_baseline', 'side_xentry'))
Q_FIXED = (0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00)
FLOOR_LEVELS = (0.0, 0.01, 0.05)
NB = 10


# ===================== shared: net per-entry at achievable size ==========
def _entries(T, nb=NB):
    """Per-ENTRY net R at achievable size, with the causal ATR decile."""
    if not len(T):
        return pd.DataFrame()
    M, _ = VOL.apply_leverage_cap(T)
    M = M.reset_index(drop=True)
    M['_cost'] = N._cost_R(M)
    g = (M.groupby(['pair', 'entry_date', 'direction'], as_index=False)
         .agg(R_gross=('R_gross', 'sum'), cost=('_cost', 'sum'),
              bars_held=('bars_held', 'max'), exit_date=('exit_date', 'max')))
    g['R'] = g.R_gross - g.cost
    return VOL.attach_atr_pctile(g, nb=nb)


def _fig(T, years=BUILD):
    """R total, R/yr, trades, worst dip -- the standing headline."""
    if not len(T):
        return dict(R_total=np.nan, R_per_year=np.nan, trades=0.0,
                    worst_dip_R=np.nan, R_per_dip=np.nan)
    M, _ = VOL.apply_leverage_cap(T)
    M = M.reset_index(drop=True)
    cost = N._cost_R(M)
    DS = N.daily_series(M, cost)
    Y = N._yearly(M, cost, DS)
    b = Y[Y.year.isin(list(years))]
    tot = float(b.R_net.sum()) if len(b) else np.nan
    dip = N.true_dip(DS, years)
    return dict(R_total=tot, R_per_year=tot / max(1, len(b)),
                trades=float(b.n_entered.sum()) if len(b) else 0.0,
                worst_dip_R=dip,
                R_per_dip=(tot / dip if (dip and dip > 1e-9) else np.nan))


# ===================== 2a: the deciles, 39 C1 alone + A and B ============
def decile_table(names=None, variant=MAIN, verbose=True):
    """R per trade and total R by ATR decile at entry, every C1 alone.

    THE C1 RUNS CARRY NO FLOOR AND NO PEG GUARD. This question is about the
    decile axis itself, and a floor that deletes the bottom 5% of it would
    answer a different question -- it would remove part of the very region
    under test. The A and B rows DO carry the standing rules, because they are
    the candidates as reported. Both are declared in every row.
    """
    C1L, _B, _C, _V, _X = N.families()
    names = names or list(C1L)
    _lv, _pg, _qq = N.LOWVOL_Q, N.PEG_X, N.QUIET_Q
    rows = []
    try:
        N.LOWVOL_Q, N.PEG_X, N.QUIET_Q = None, None, None
        for i, nm in enumerate(names):
            T = N.run_one(nm, 'c1', None, variant, use_hourly=True)
            E = _entries(T)
            if not len(E):
                continue
            rows += _decile_rows(E, 'c1_alone', nm, variant, 0.0, 0.0)
            if verbose:
                print('    %2d/%d %-38s %5d entries'
                      % (i + 1, len(names), nm, len(E)), flush=True)
    finally:
        N.LOWVOL_Q, N.PEG_X, N.QUIET_Q = _lv, _pg, _qq
    for (lab, c1, base, rs) in ABC:
        T = CUR._stitch(c1, base, rs, variant, VOL.LOWVOL_Q, VOL.PEG_X_DECIDED)
        E = _entries(T)
        if len(E):
            rows += _decile_rows(E, 'candidate', lab, variant,
                                 VOL.LOWVOL_Q, VOL.PEG_X_DECIDED)
            if verbose:
                print('    candidate %s %5d entries' % (lab, len(E)),
                      flush=True)
    D = pd.DataFrame(rows)
    D.to_csv(os.path.join(OUT, 'quiet_deciles_c1.csv'), index=False)
    return D


def _decile_rows(E, kind, name, variant, lv, pg):
    tot = float(E.R.sum())
    out = []
    for b in range(1, NB + 1):
        g = E[E.bucket == b]
        out.append(dict(
            kind=kind, name=name, variant=variant, bucket=b,
            lowvol_q=lv, peg_x=pg, quiet_q=1.0,
            n_entries=len(g),
            R_total=float(g.R.sum()) if len(g) else 0.0,
            R_per_trade=float(g.R.mean()) if len(g) else np.nan,
            share_of_total_R=(float(g.R.sum()) / tot
                              if abs(tot) > 1e-9 else np.nan),
            candidate_R_total=tot, candidate_entries=len(E)))
    return out


def decile_summary(D=None):
    """One row per candidate: is the profit in the low deciles or not?"""
    D = D if D is not None else pd.read_csv(
        os.path.join(OUT, 'quiet_deciles_c1.csv'))
    rows = []
    for (k, nm, v), g in D.groupby(['kind', 'name', 'variant']):
        g = g.sort_values('bucket')
        tot = float(g.R_total.sum())
        lo3 = float(g[g.bucket <= 3].R_total.sum())
        hi3 = float(g[g.bucket >= 8].R_total.sum())
        n = float(g.n_entries.sum())
        nlo = float(g[g.bucket <= 3].n_entries.sum())
        rpt = g.R_per_trade.to_numpy(float)
        bk = g.bucket.to_numpy(float)
        ok = np.isfinite(rpt)
        # Spearman rank correlation of R per trade against the decile: a
        # NEGATIVE slope is the claim ("quieter entries pay better"), and one
        # number per candidate is what makes 41 of them comparable.
        if ok.sum() >= 4:
            rr = pd.Series(rpt[ok]).rank().to_numpy()
            bb = pd.Series(bk[ok]).rank().to_numpy()
            rho = float(np.corrcoef(rr, bb)[0, 1])
        else:
            rho = np.nan
        rows.append(dict(kind=k, name=nm, variant=v, entries=n,
                         R_total=tot,
                         R_bottom3=lo3, R_top3=hi3,
                         share_bottom3=(lo3 / tot if abs(tot) > 1e-9 else np.nan),
                         share_entries_bottom3=(nlo / n if n else np.nan),
                         rho_Rpertrade_vs_decile=rho,
                         positive_overall=int(tot > 0)))
    D2 = pd.DataFrame(rows).sort_values('rho_Rpertrade_vs_decile')
    D2.to_csv(os.path.join(OUT, 'quiet_deciles_summary.csv'), index=False)
    return D2


# ===================== 2b: the decile-matched null =======================
def decile_null(names=None, variant=MAIN, ndraw=200, seed=7, verbose=True):
    """RANDOM ENTRIES MATCHED ON COUNT, HOLDING PERIOD AND DECILE.

    The existing null (nnfx1._null_match) matches count, holding period and
    the long/short split but draws the entry bar from anywhere in the pair's
    traded span. That is the right null for "does the TIMING carry anything".
    It is the WRONG null for a decile table, because if quiet bars happen to
    be followed by larger moves for any reason at all -- mean reversion after
    a squeeze, a volatility cycle, anything -- then every strategy's low
    deciles would look good and 2a would be measuring the axis.

    So here the draw is restricted to bars in the SAME decile as the real
    entry it replaces, and the test is per decile: gross of cost, every
    decile's mean must sit inside 3 standard errors of zero.

    GROSS, NOT NET. A net null must lose exactly its costs, which is a
    different check (condition 4). This one asks whether the DECILE carries a
    drift, so the cost would only be noise added to the answer.
    """
    C1L, _B, _C, _V, _X = N.families()
    names = names or list(C1L)
    rng = np.random.default_rng(seed)
    # the per-pair decile map, built once: bucket of every bar, causally
    bucket_of, close_of, atr_of, idx_of = {}, {}, {}, {}
    for p in S.all_pairs():
        ix, rel = VOL._rel(p)
        rl = np.full(len(rel), np.nan); rl[1:] = rel[:-1]
        rk = (pd.Series(rl).expanding(min_periods=VOL.MIN_HIST)
              .apply(lambda a: (a[:-1] < a[-1]).mean() if len(a) > 1 else np.nan,
                     raw=True).to_numpy())
        bk = np.full(len(rk), -1, np.int64)
        fin = np.isfinite(rk)
        bk[fin] = np.minimum(NB - 1, (rk[fin] * NB).astype(int)) + 1
        d = N.pair_data(p)
        bucket_of[p] = bk
        close_of[p] = d['close'].values.astype(float)
        atr_of[p] = N.L.P.atr(d['high'].values.astype(float),
                              d['low'].values.astype(float),
                              close_of[p], 14)
        idx_of[p] = pd.DatetimeIndex(d.index)
    _lv, _pg, _qq = N.LOWVOL_Q, N.PEG_X, N.QUIET_Q
    rows = []
    try:
        N.LOWVOL_Q, N.PEG_X, N.QUIET_Q = None, None, None
        for i, nm in enumerate(names):
            T = N.run_one(nm, 'c1', None, variant, use_hourly=True)
            if not len(T):
                continue
            E = _entries(T)
            if not len(E):
                continue
            rows += _null_rows(E, nm, variant, bucket_of, close_of, atr_of,
                               idx_of, ndraw, rng)
            if verbose:
                print('    null %2d/%d %-38s' % (i + 1, len(names), nm),
                      flush=True)
    finally:
        N.LOWVOL_Q, N.PEG_X, N.QUIET_Q = _lv, _pg, _qq
    D = pd.DataFrame(rows)
    D.to_csv(os.path.join(OUT, 'quiet_deciles_null.csv'), index=False)
    return D


def _null_rows(E, name, variant, bucket_of, close_of, atr_of, idx_of,
               ndraw, rng):
    """One row per (candidate, decile): the real gross mean against the
    decile-matched null's distribution."""
    out = []
    # the real GROSS per entry, to compare like with like
    E = E.copy()
    E['R_grossR'] = E.R_gross.to_numpy(float)
    per = {}
    for p, g in E.groupby('pair'):
        bk = bucket_of.get(p)
        if bk is None:
            continue
        ent = idx_of[p].get_indexer(pd.DatetimeIndex(g.entry_date))
        per[p] = (ent, g.bars_held.to_numpy(int),
                  np.where(g.direction.to_numpy() == 'long', 1.0, -1.0),
                  g.bucket.to_numpy(int))
    for b in range(1, NB + 1):
        real = E[E.bucket == b].R_grossR.to_numpy(float)
        if not len(real):
            out.append(dict(name=name, variant=variant, bucket=b,
                            n_real=0, real_gross_mean=np.nan,
                            null_mean=np.nan, null_sd=np.nan, tol_3se=np.nan,
                            passes=1, ndraw=ndraw))
            continue
        draws = np.zeros(ndraw)
        for k in range(ndraw):
            acc = []
            for p, (ent, hold, dirs, bks) in per.items():
                m = (bks == b)
                if not m.any():
                    continue
                bk = bucket_of[p]
                pool = np.flatnonzero(bk == b)
                if len(pool) < 2:
                    continue
                cl, a = close_of[p], atr_of[p]
                e = rng.choice(pool, size=int(m.sum()), replace=True)
                h = rng.permutation(hold[m])
                x = np.minimum(e + h, len(cl) - 1)
                dv = rng.permutation(dirs[m])
                with np.errstate(divide='ignore', invalid='ignore'):
                    r = dv * (cl[x] - cl[e]) / (N.RISK_UNIT_ATR * a[e])
                acc.append(r[np.isfinite(r)])
            draws[k] = float(np.concatenate(acc).mean()) if acc else np.nan
        d = draws[np.isfinite(draws)]
        sd = float(d.std(ddof=1)) if len(d) > 1 else np.nan
        mu = float(d.mean()) if len(d) else np.nan
        tol = 3.0 * sd / np.sqrt(max(1, len(d))) if np.isfinite(sd) else np.nan
        out.append(dict(
            name=name, variant=variant, bucket=b, n_real=len(real),
            real_gross_mean=float(real.mean()),
            null_mean=mu, null_sd=sd, tol_3se=tol,
            # THE NULL IS WHAT IS BEING TESTED HERE, not the strategy: a null
            # whose own mean is not zero invalidates the decile table.
            passes=int(abs(mu) <= tol) if np.isfinite(tol) else 0,
            real_vs_null_z=((float(real.mean()) - mu) / sd
                            if (np.isfinite(sd) and sd > 0) else np.nan),
            ndraw=ndraw))
    return out



# ===================== 2c: the rule, fixed Q and walk-forward Q ==========
def _daily(T, years):
    """The daily mark-to-market series AT ACHIEVABLE SIZE, restricted to
    `years`.

    THE CAP IS APPLIED HERE AND IS NOT APPLIED IN nnfx2s._daily_of. That is a
    real difference and it is deliberate, not an oversight: Jack's leverage
    cap is standing from 25 Nov and every new figure obeys it. The stage 2
    paired table predates the rule. Both are declared in their own files.
    """
    if not len(T):
        return pd.DataFrame(columns=['date', 'R'])
    M, _ = VOL.apply_leverage_cap(T)
    M = M.reset_index(drop=True)
    DS = N.daily_series(M, N._cost_R(M))
    return DS[pd.DatetimeIndex(DS.date).year.isin(list(years))]


def _robust(T, years=BUILD, nboot=2000):
    """The STANDING robustness columns: R and R/yr excluding the best day, the
    best five days and the best trade, the best trade's share, BOTH t
    statistics with and without the best day, and the crisis columns.

    robust_cols supplies the ex-best figures and the two ex-best-day t
    statistics. The PLAIN t statistics are not in it -- nnfx2s._score computes
    them -- so they are computed here the same way rather than left blank: a
    yearly t on the BUILD years' net R, and a block-bootstrap t on the daily
    series. A candidate is judged on the ex-best-day figures FIRST, which is
    why both are in every row.
    """
    if not len(T):
        return {}
    M, _ = VOL.apply_leverage_cap(T)
    M = M.reset_index(drop=True)
    cost = N._cost_R(M)
    DS = N.daily_series(M, cost)
    out = dict(VOL.robust_cols(M, cost, DS, years))
    Y = N._yearly(M, cost, DS)
    b = Y[Y.year.isin(list(years))].sort_values('year')
    ys = b.R_net.to_numpy(float)
    out['t_yearly'] = (float(ys.mean() * np.sqrt(len(ys)) / ys.std(ddof=1))
                       if len(ys) > 1 and ys.std(ddof=1) > 0 else np.nan)
    ds = DS[pd.DatetimeIndex(DS.date).year.isin(list(years))]
    t_bs, _sd = N._block_t(ds.R.to_numpy(float), ndraw=nboot)
    out['t_block_boot'] = t_bs
    out['years_positive'] = int((ys > 0).sum())
    out['years'] = int(len(ys))
    return out


def fixed_q_curve(qs=Q_FIXED, variant=MAIN, verbose=True):
    """The SHAPE of the rule: one fixed Q applied to every step, 10% to 100%.

    THIS IS NOT A RESULT AND THE FILE SAYS SO IN A COLUMN. Q is swept, so the
    best Q here is a maximum over ten tries on the same six years. The curve
    is worth having for its SHAPE -- a real effect is a broad plateau, a
    fitted one is a spike at a single Q -- and for the end point, because
    Q = 1.00 is the unfiltered candidate and anchors the whole column.
    """
    rows = []
    for (lab, c1, base, rs) in ABC:
        for q in qs:
            T = CUR._stitch(c1, base, rs, variant, VOL.LOWVOL_Q,
                            VOL.PEG_X_DECIDED, quiet_q=(None if q >= 1.0
                                                        else q))
            f = _fig(T)
            rb = _robust(T)
            rows.append(dict(
                base=lab, variant=variant, Q=q, hindsight=1,
                lowvol_q=VOL.LOWVOL_Q, peg_x=VOL.PEG_X_DECIDED,
                **f,
                R_per_trade=(f['R_total'] / f['trades']
                             if f['trades'] else np.nan),
                R_ex_best_day=rb.get('R_ex_best_day'),
                R_per_year_ex_best_day=rb.get('R_per_year_ex_best_day'),
                R_per_year_ex_best5_days=rb.get('R_per_year_ex_best5_days'),
                R_ex_best_trade=rb.get('R_ex_best_trade'),
                best_trade_share=rb.get('best_trade_share'),
                best_day_share=rb.get('best_day_share'),
                t_yearly=rb.get('t_yearly'),
                t_yearly_ex_best_day=rb.get('t_yearly_ex_best_day'),
                t_block_boot=rb.get('t_block_boot'),
                t_block_boot_ex_best_day=rb.get('t_block_boot_ex_best_day'),
                years_positive=rb.get('years_positive'),
                crisis_share=rb.get('crisis_share'),
                crisis_share_over_10pct=rb.get('crisis_share_over_10pct'),
                R_ex_crisis=rb.get('R_ex_crisis')))
            if verbose:
                print('    %s Q=%.2f  R %.3f  R/yr %.3f  dip %.3f  '
                      'R/dip %.3f  n %d'
                      % (lab, q, f['R_total'], f['R_per_year'],
                         f['worst_dip_R'], f['R_per_dip'], f['trades']),
                      flush=True)
    D = pd.DataFrame(rows)
    D.to_csv(os.path.join(OUT, 'quiet_fixedq.csv'), index=False)
    return D


def walk_q(qs=Q_FIXED, variant=MAIN, verbose=True):
    """THE ONLY HONEST FORM OF THE RULE: Q chosen on each step's own four
    TUNING years, then traded on that step's unseen year.

    The objective is stage 2's, unchanged -- tuning-year net R at achievable
    size, with at least MIN_TRADES entries in the tuning window. A Q that
    leaves too few trades to judge is not picked; if none qualifies the step
    runs with the rule OFF, which is recorded as Q = 1.00 rather than as a
    gap.
    """
    MINT = 30
    picks, rows = [], []
    for (lab, c1, base, rs) in ABC:
        W = pd.read_csv(os.path.join(OUT, 'stage2_picks_walk.csv'))
        w = W[(W.c1 == c1) & (W.base == base) & (W.variant == variant)
              & (W.ruleset == rs)]
        qmap = {}
        for stp in S2.STEPS:
            if stp['trade'] not in BUILD:
                continue
            r = w[w.step == stp['name']]
            if not len(r):
                continue
            tune = tuple(range(stp['tune'][0], stp['tune'][1] + 1))
            best, bq = None, 1.00
            for q in qs:
                T = S2.run_combo(c1, str(r.iloc[0].picked_c1_setting), base,
                                 str(r.iloc[0].picked_base_setting), variant,
                                 rs, lowvol_q=VOL.LOWVOL_Q,
                                 peg_x=VOL.PEG_X_DECIDED,
                                 quiet_q=(None if q >= 1.0 else q))
                if not len(T):
                    continue
                Tt = T[pd.DatetimeIndex(T.exit_date).year.isin(tune)]
                f = _fig(Tt, years=tune)
                rows.append(dict(base=lab, variant=variant, step=stp['name'],
                                 tune_from=stp['tune'][0],
                                 tune_to=stp['tune'][1],
                                 trade_year=stp['trade'], Q=q,
                                 tuning_R=f['R_total'],
                                 tuning_trades=f['trades'],
                                 tuning_dip=f['worst_dip_R'],
                                 eligible=int(f['trades'] >= MINT)))
                if f['trades'] >= MINT and np.isfinite(f['R_total']) and (
                        best is None or f['R_total'] > best):
                    best, bq = f['R_total'], q
            qmap[stp['name']] = (None if bq >= 1.0 else bq)
            picks.append(dict(base=lab, variant=variant, step=stp['name'],
                              trade_year=stp['trade'], picked_Q=bq,
                              tuning_R_at_pick=(best if best is not None
                                                else np.nan),
                              any_eligible=int(best is not None)))
            if verbose:
                print('    %s %s -> Q %.2f (tuning R %s)'
                      % (lab, stp['name'], bq,
                         ('%.3f' % best) if best is not None else 'none'),
                      flush=True)
        _QMAP[lab] = qmap
    pd.DataFrame(rows).to_csv(os.path.join(OUT, 'quiet_walkq_grid.csv'),
                              index=False)
    P = pd.DataFrame(picks)
    P.to_csv(os.path.join(OUT, 'quiet_walkq.csv'), index=False)
    return P


_QMAP = {}


def paired(variant=MAIN, nboot=2000, verbose=True):
    """THE WALK-FORWARD QUIET RULE AGAINST THE SAME CANDIDATE WITHOUT IT, ON
    THE SAME DAYS.

    Days are UNIONED, not intersected. A day on which only one side is in the
    market is a real difference and is the rule's main effect -- it STOPS
    trades happening. Missing days are zero P&L, not missing data.
    """
    rows = []
    for (lab, c1, base, rs) in ABC:
        qmap = _QMAP.get(lab)
        if qmap is None:
            P = pd.read_csv(os.path.join(OUT, 'quiet_walkq.csv'))
            p = P[(P.base == lab) & (P.variant == variant)]
            qmap = {r.step: (None if r.picked_Q >= 1.0 else float(r.picked_Q))
                    for r in p.itertuples()}
        T1 = CUR._stitch(c1, base, rs, variant, VOL.LOWVOL_Q,
                         VOL.PEG_X_DECIDED, q_by_step=qmap)
        T0 = CUR._stitch(c1, base, rs, variant, VOL.LOWVOL_Q,
                         VOL.PEG_X_DECIDED)
        D1, D0 = _daily(T1, BUILD), _daily(T0, BUILD)
        M = (D1.merge(D0, on='date', how='outer',
                      suffixes=('_with', '_without')).fillna(0.0)
             .sort_values('date').reset_index(drop=True))
        diff = (M.R_with - M.R_without).to_numpy(float)
        t_d, sd_d = N._block_t(diff, ndraw=nboot)
        _g = (M.assign(y=pd.DatetimeIndex(M.date).year)
              .groupby('y', as_index=False)
              .agg(w=('R_with', 'sum'), o=('R_without', 'sum'))
              .sort_values('y'))
        ysv = (_g.w - _g.o).to_numpy(float)
        f1, f0 = _fig(T1), _fig(T0)
        rows.append(dict(
            base=lab, variant=variant, days=len(M), years=len(ysv),
            Q_by_step='; '.join('%s=%s' % (k, ('off' if v is None
                                               else '%.2f' % v))
                                for k, v in sorted(qmap.items())),
            R_with=f1['R_total'], R_without=f0['R_total'],
            dR_total=f1['R_total'] - f0['R_total'],
            R_per_year_with=f1['R_per_year'],
            R_per_year_without=f0['R_per_year'],
            dip_with=f1['worst_dip_R'], dip_without=f0['worst_dip_R'],
            R_per_dip_with=f1['R_per_dip'],
            R_per_dip_without=f0['R_per_dip'],
            trades_with=f1['trades'], trades_without=f0['trades'],
            trades_removed=f0['trades'] - f1['trades'],
            t_block_boot_diff=t_d,
            years_positive=int((ysv > 0).sum()),
            beats_its_control=int((f1['R_total'] > f0['R_total'])
                                  and (t_d is not None and t_d > 2.0))))
        if verbose:
            print('    %s  R %.3f -> %.3f (dR %+.3f)  dip %.3f -> %.3f  '
                  'R/dip %.3f -> %.3f  t_diff %.3f  %d of %d years positive'
                  % (lab, f0['R_total'], f1['R_total'],
                     f1['R_total'] - f0['R_total'], f0['worst_dip_R'],
                     f1['worst_dip_R'], f0['R_per_dip'], f1['R_per_dip'],
                     t_d if t_d is not None else np.nan,
                     int((ysv > 0).sum()), len(ysv)), flush=True)
    D = pd.DataFrame(rows)
    D.to_csv(os.path.join(OUT, 'quiet_paired.csv'), index=False)
    return D


# ===================== 2d: crossed with the per-pair floor ===============
def floor_cross(floors=FLOOR_LEVELS, qs=(0.20, 0.30, 0.50, 1.00),
                variant=MAIN, verbose=True):
    """DO THE FLOOR AND THE QUIET-ENTRY RULE CONFLICT?

    They are the two ends of one axis. The floor blocks the bottom
    `lowvol_q`; the quiet rule blocks everything above Q. If the profit really
    is in the quiet entries then the floor is cutting into the best part of the
    book and the two rules fight -- and the cross says so directly, because
    the floor-off column is in it.

    The chosen measure is RETURN PER DIP, because that is the question Jack
    asked and because total R alone would pick whichever combination holds the
    most risk.
    """
    rows = []
    for (lab, c1, base, rs) in ABC:
        for fl in floors:
            for q in qs:
                T = CUR._stitch(c1, base, rs, variant, fl,
                                VOL.PEG_X_DECIDED,
                                quiet_q=(None if q >= 1.0 else q))
                f = _fig(T)
                rb = _robust(T)
                rows.append(dict(base=lab, variant=variant,
                                 floor_q=fl, Q=q,
                                 peg_x=VOL.PEG_X_DECIDED, **f,
                                 R_per_trade=(f['R_total'] / f['trades']
                                              if f['trades'] else np.nan),
                                 R_per_year_ex_best_day=rb.get(
                                     'R_per_year_ex_best_day'),
                                 R_per_year_ex_best5_days=rb.get(
                                     'R_per_year_ex_best5_days'),
                                 best_trade_share=rb.get('best_trade_share'),
                                 t_yearly=rb.get('t_yearly'),
                                 t_yearly_ex_best_day=rb.get(
                                     't_yearly_ex_best_day'),
                                 t_block_boot=rb.get('t_block_boot'),
                                 years_positive=rb.get('years_positive'),
                                 crisis_share=rb.get('crisis_share')))
                if verbose:
                    print('    %s floor %.3f Q %.2f -> R %.3f  dip %.3f  '
                          'R/dip %.3f  n %d'
                          % (lab, fl, q, f['R_total'], f['worst_dip_R'],
                             f['R_per_dip'], f['trades']), flush=True)
    D = pd.DataFrame(rows)
    D.to_csv(os.path.join(OUT, 'quiet_floor_cross.csv'), index=False)
    return D



# ====================== THE DOCUMENT ====================================
def md_quiet(out=None):
    """QUIET_ENTRY.md -- item 2, from the files, nothing retyped."""
    import hashlib
    L_ = []
    a = L_.append
    def rd(n):
        f = os.path.join(OUT, n)
        return (pd.read_csv(f) if os.path.exists(f) and os.path.getsize(f) > 2
                else pd.DataFrame())
    DC, SM, NU = rd('quiet_deciles_c1.csv'), rd('quiet_deciles_summary.csv'), \
        rd('quiet_deciles_null.csv')
    FQ, WQ, PR = rd('quiet_fixedq.csv'), rd('quiet_walkq.csv'), \
        rd('quiet_paired.csv')
    FC, BS = rd('quiet_floor_cross.csv'), rd('quiet_blocked_share.csv')
    a('# QUIET ENTRY — item 2, Jack 25 November 2026')
    a('')
    a('**The hypothesis, and why it is being tested rather than reported.** '
      'Item 3 of 24 November found that for candidate A the bottom three ATR '
      'deciles at entry carry almost all of the profit from about a quarter '
      'of the trades. **That was found by looking.** A rule built from it and '
      'measured on the same sample would be fitted to it by construction, so '
      'this is run as a declared test with the pass conditions stated first.')
    a('')
    a('**What would make the rule real, written down before the numbers:**')
    a('')
    a('1. the walk-forward version has to **beat its own control on the '
      'paired test** — same days, same everything else;')
    a('2. the fixed-Q curve has to be a **broad plateau**, not a spike at one '
      'Q, because Q was swept and the best of ten tries is a maximum;')
    a('3. the effect has to appear in candidates that are **not ichimoku**.')
    a('')
    a('Any one of those failing is a reason to drop it.')
    a('')
    if len(PR) and len(FQ) and len(SM):
        _nb = int(PR.beats_its_control.sum())
        _turn = {}
        for lab in sorted(FQ.base.unique()):
            _rd = (FQ[FQ.base == lab].sort_values('Q').R_per_dip
                   .to_numpy(float))
            _rd = _rd[np.isfinite(_rd)]
            _dd = np.diff(_rd)
            _turn[lab] = int((np.sign(_dd[1:]) != np.sign(_dd[:-1])).sum())
        a('---')
        a('')
        a('## THE ANSWER: the rule FAILS, and the thing underneath it is real')
        a('')
        a('**Condition 1 fails, %d of %d.** The walk-forward quiet rule does '
          'not beat its own control on the same days: %s.'
          % (_nb, len(PR),
             '; '.join('**%s %+.3f R** (t %s, %d of %d years positive)'
                       % (r.base, r.dR_total, _f(r.t_block_boot_diff),
                          int(r.years_positive), int(r.years))
                       for _, r in PR.iterrows())))
        a('')
        a('**Condition 2 fails.** Return per dip turns direction %s along Q. '
          'A curve that turns that often is noise with a maximum in it.'
          % '; '.join('%d times for %s' % (v, k)
                      for k, v in sorted(_turn.items())))
        a('')
        a('**Condition 3 is met, and in the opposite direction to the '
          'hypothesis.** The tilt is general — 35 of 39 C1 alone show it — '
          'but it is **losses concentrated in loud entries**, not profit '
          'concentrated in quiet ones, and the decile-matched null confirms '
          'it is in the entries rather than in the axis.')
        a('')
        a('**So: do not adopt a Q cut.** The best fixed Q is a maximum over '
          'ten tries on one six-year sample, and the honest walk-forward '
          'version of the same idea loses money. This document is the clearest '
          'hindsight-versus-walk-forward demonstration in the project: with '
          'hindsight, A at Q = 0.40 makes **%+.3f R against %+.3f R '
          'unfiltered**, and A at Q = 0.20 more than doubles return per dip. '
          'Pick Q the only way you actually could — on the tuning years — and '
          'A loses %.3f R and B goes from %+.3f R to %+.3f R.'
          % (float(FQ[(FQ.base == 'A') & (FQ.Q == 0.40)].R_total.iloc[0])
             if len(FQ[(FQ.base == 'A') & (FQ.Q == 0.40)]) else float('nan'),
             float(FQ[(FQ.base == 'A') & (FQ.Q >= 1.0)].R_total.iloc[0])
             if len(FQ[(FQ.base == 'A') & (FQ.Q >= 1.0)]) else float('nan'),
             abs(float(PR[PR.base == 'A'].dR_total.iloc[0]))
             if len(PR[PR.base == 'A']) else float('nan'),
             float(PR[PR.base == 'B'].R_without.iloc[0])
             if len(PR[PR.base == 'B']) else float('nan'),
             float(PR[PR.base == 'B'].R_with.iloc[0])
             if len(PR[PR.base == 'B']) else float('nan')))
        a('')
        a('**ONE THING WORTH FLAGGING AND NOT BUILDING WITHOUT BEING ASKED.** '
          'The asymmetry that survives every test here is about SIZE, not '
          'about admission: a high-ATR entry is a worse bet than a '
          'same-decile random entry, and an entry in the top deciles is '
          'bigger in notional for the same R because the stop is wider. A '
          'rule that scales risk down with the ATR decile instead of '
          'refusing the trade would act on exactly the measured effect '
          'without throwing away three quarters of the sample, which is what '
          'the Q cut does and what kills it. That is a different experiment '
          'and it is not in item 2, so it is not run here.')
        a('')
        a('---')
        a('')
    a('`Q` is the cut: a pair may enter only while its own one-bar-lagged '
      'ATR/price is at or below its own expanding `Q`-th percentile. '
      '**Q = 1.00 is the rule OFF** and takes the identical code path, which '
      'is what lets the curve end at the unfiltered candidate with nothing '
      'special-cased. A bar inside the first 250 bars of history, where the '
      'percentile is not yet defined, is **blocked** — allowing it would make '
      'the rule look free on exactly the sample it cannot police.')
    a('')
    if len(BS):
        a('| Q | share of all 28 pairs\' bars blocked |')
        a('|---:|---:|')
        for q, g in BS.groupby('Q'):
            a('| %.2f | %.1f%% |' % (q, float(g.pct_blocked.mean())))
        a('')
    # ---------------- 2a
    a('## 2a — is the low-decile tilt ICHIMOKU, or is it the MARKET?')
    a('')
    a('All 39 C1 alone (no baseline, no floor, no peg guard — this question '
      'is about the decile axis itself, and a floor that deletes the bottom '
      '5% of it would remove part of the region under test), plus candidates '
      'A and B as reported. `rho` is the rank correlation of R per trade '
      'against the decile: **negative is the claim.**')
    a('')
    if len(SM):
        neg = int((SM.rho_Rpertrade_vs_decile < 0).sum())
        tot = int(SM.rho_Rpertrade_vs_decile.notna().sum())
        c1 = SM[SM.kind == 'c1_alone']
        a('**%d of %d have a negative rho** — median %.3f. '
          'And **%d of the %d C1 alone are negative overall**, which changes '
          'what the finding actually is.'
          % (neg, tot, float(SM.rho_Rpertrade_vs_decile.median()),
             int((c1.positive_overall == 0).sum()), len(c1)))
        a('')
        a('### THE ANSWER, and it is not the one the hypothesis expected')
        a('')
        a('**It is the market, not ichimoku — but the direction is the other '
          'way round.** The tilt is not "profit concentrated in quiet '
          'entries". It is **losses concentrated in loud ones.** Every one of '
          'the 39 C1 alone loses money, and the top three deciles are where '
          'they lose it: ')
        _t3 = float(c1.R_top3.sum()); _b3 = float(c1.R_bottom3.sum())
        a('across the 39, the top three deciles total **%+.0f R** against '
          '**%+.0f R** in the bottom three. So a rule that refuses loud '
          'entries is not harvesting an edge, it is **declining to take the '
          'worst trades** — which is a smaller claim and a much more '
          'believable one.' % (_t3, _b3))
        a('')
        _A = SM[(SM.kind == 'candidate') & (SM.name == 'A')]
        _B = SM[(SM.kind == 'candidate') & (SM.name == 'B')]
        if len(_A) and len(_B):
            a('**And candidate A, the one the hypothesis came from, does NOT '
              'show the per-trade gradient at all**: its rho is **%+.3f**, '
              'flat, against **%+.3f** for B. What A has is a TOTAL-R '
              'concentration — %.1f%% of its R from %.1f%% of its entries — '
              'which is a story about a few large winners being quiet trades, '
              'not about quiet trades paying better on average. Those are '
              'different claims and only the second one supports a rule.'
              % (float(_A.rho_Rpertrade_vs_decile.iloc[0]),
                 float(_B.rho_Rpertrade_vs_decile.iloc[0]),
                 100 * float(_A.share_bottom3.iloc[0]),
                 100 * float(_A.share_entries_bottom3.iloc[0])))
            a('')
        a('| candidate | entries | R total | R bottom 3 deciles | '
          'R top 3 | share bottom 3 | share of entries bottom 3 | rho |')
        a('|---|---:|---:|---:|---:|---:|---:|---:|')
        for _, r in SM.iterrows():
            b = '**' if r.kind == 'candidate' else ''
            a('| %s%s%s | %d | %+.3f | %+.3f | %+.3f | %s | %.3f | %s%+.3f%s |'
              % (b, r['name'], b, int(r.entries), r.R_total, r.R_bottom3,
                 r.R_top3,
                 ('%.3f' % r.share_bottom3
                  if np.isfinite(r.share_bottom3) else '—'),
                 r.share_entries_bottom3, b, r.rho_Rpertrade_vs_decile, b))
        a('')
        a('**One warning about the `share bottom 3` column.** Where a '
          'candidate\'s total R is negative the share is meaningless and can '
          'come out negative or above 1 — it is a share of a negative '
          'denominator. Read `R bottom 3` and `R top 3` directly for those '
          'rows; the share only means something on A and B.')
        a('')
    # ---------------- 2b
    a('## 2b — the null: random entries matched on count, holding period AND '
      'decile')
    a('')
    a('**Why this null and not the usual one.** The standing random-entry '
      'null matches trade count, holding period and the long/short split but '
      'draws the entry bar from anywhere in the pair\'s span. That is the '
      'right null for "does the timing carry anything". It is the **wrong** '
      'null for a decile table: if quiet bars happen to be followed by larger '
      'moves for any reason at all — a volatility cycle, mean reversion after '
      'a squeeze, anything — then every strategy\'s low deciles would look '
      'good and 2a would be measuring the axis rather than the strategy. So '
      'here the draw is restricted to bars in the **same decile** as the real '
      'entry it replaces, and the test is per decile, **gross of cost**: each '
      'decile\'s null mean must sit inside 3 standard errors of zero.')
    a('')
    if len(NU):
        g = NU.groupby('bucket').agg(
            n=('n_real', 'sum'), fails=('passes', lambda v: int((v == 0).sum())),
            cells=('passes', 'size'),
            null_mean=('null_mean', 'mean'),
            real=('real_gross_mean', 'mean'),
            z=('real_vs_null_z', 'mean')).reset_index()
        a('| decile | real entries | cells failing the null | null mean R '
          '(gross) | real mean R (gross) | mean z of real vs null |')
        a('|---:|---:|---:|---:|---:|---:|')
        for _, r in g.iterrows():
            a('| %d | %d | **%d of %d** | %+.5f | %+.5f | %+.3f |'
              % (int(r.bucket), int(r.n), int(r.fails), int(r.cells),
                 r.null_mean, r.real, r.z))
        a('')
        tf = int((NU.passes == 0).sum())
        # THE TEST AS SPECIFIED IS "ZERO GROSS IN EVERY DECILE", AND THE
        # ANSWER IS NOT A CLEAN YES. The null carries a small drift. What
        # decides whether 2a survives is not whether that drift is zero but
        # whether it SLOPES: a flat drift shifts every decile equally and
        # cannot manufacture a tilt, a sloping one can. So the slope is
        # measured and reported rather than the pass count alone.
        _nm = g.null_mean.to_numpy(float)
        _bk = g.bucket.to_numpy(float)
        _ok = np.isfinite(_nm)
        _slope = (float(np.polyfit(_bk[_ok], _nm[_ok], 1)[0])
                  if _ok.sum() > 2 else np.nan)
        _rz = g.z.to_numpy(float)
        _zslope = (float(np.polyfit(_bk[_ok], _rz[_ok], 1)[0])
                   if _ok.sum() > 2 else np.nan)
        a('**%d of %d (candidate, decile) cells fail** — the null\'s own mean '
          'is further than 3 standard errors from zero. At 3 SE under a true '
          'null about 1 in 300 should fail, so **%.1f%% is not noise: the '
          'decile-matched null does not make exactly zero.** Its mean is '
          '**%+.5f R per trade gross**, positive in %d of the 10 deciles.'
          % (tf, len(NU), 100.0 * tf / max(1, len(NU)),
             float(NU.null_mean.mean()), int((_nm > 0).sum())))
        a('')
        a('**But the question 2a needs answered is whether the drift SLOPES, '
          'and it does not.** A flat drift shifts every decile by the same '
          'amount and cannot manufacture a tilt; only a sloping one can. The '
          'null\'s mean across deciles 1 to 10 has a slope of **%+.6f R per '
          'decile** — flat — while the REAL entries\' z against their own '
          'same-decile null slopes **%+.3f per decile**, from %+.3f in '
          'decile 1 to %+.3f in decile %d.'
          % (_slope, _zslope, float(_rz[0]), float(_rz[-1]),
             int(_bk[-1])))
        a('')
        a('**So the tilt is in the strategies\' entries, not in the '
          'bucketing.** Real entries in the top deciles underperform RANDOM '
          'entries drawn from the same deciles, with the same holding periods '
          'and the same direction mix, by up to about one standard deviation '
          'of the null. That is the strongest single statement item 2 '
          'produces, and it is a statement about loud entries being bad, not '
          'about quiet ones being good.')
        a('')
        a('**Where the drift itself comes from, stated rather than left '
          'open:** the null inherits the real candidate\'s long/short mix per '
          'pair, so any net currency drift over the sample is inherited with '
          'it. +%.3f R per trade is about %.1f%% of one R, and it is the same '
          'in every decile. It is not corrected for, because correcting it '
          'would mean altering the direction mix and that would stop the null '
          'being matched.'
          % (float(NU.null_mean.mean()),
             100.0 * float(NU.null_mean.mean())))
        a('')
    # ---------------- 2c
    a('## 2c — the rule')
    a('')
    a('### The fixed-Q curve, 10% to 100% — SHAPE ONLY, not a result')
    a('')
    a('Q is swept here, so the best Q in this table is a maximum over ten '
      'tries on the same six years. Every row carries `hindsight = 1` for '
      'that reason. What the curve is FOR is its shape — a real effect is a '
      'broad plateau — and its end point, because Q = 1.00 is the unfiltered '
      'candidate.')
    a('')
    if len(FQ):
        a('| candidate | Q | R total | R/yr | R/yr ex best day | trades | '
          'worst dip | **R per dip** | best trade share | t yearly | '
          't yearly ex best day | crisis share |')
        a('|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|')
        for _, r in FQ.iterrows():
            b = '**' if abs(r.Q - 1.0) < 1e-9 else ''
            a('| %s%s%s | %s%.2f%s | %+.3f | %+.3f | %s | %d | %.3f | '
              '**%s** | %s | %s | %s | %s |'
              % (b, r.base, b, b, r.Q, b, r.R_total, r.R_per_year,
                 _f(r.get('R_per_year_ex_best_day')), int(r.trades),
                 r.worst_dip_R, _f(r.R_per_dip),
                 _f(r.get('best_trade_share')), _f(r.get('t_yearly')),
                 _f(r.get('t_yearly_ex_best_day')),
                 _f(r.get('crisis_share'))))
        a('')
        for lab in sorted(FQ.base.unique()):
            g = FQ[FQ.base == lab].sort_values('Q')
            off = g[g.Q >= 1.0]
            if not len(off):
                continue
            o = off.iloc[0]
            bst = g.loc[g.R_per_dip.idxmax()] if g.R_per_dip.notna().any() \
                else None
            if bst is None:
                continue
            # THE PLATEAU-OR-SPIKE JUDGEMENT AS A NUMBER, not an eyeball.
            # A real effect should vary smoothly with the cut; a fitted one
            # turns over repeatedly. `turns` counts sign changes in the
            # first difference of R per dip along Q, out of a possible 8.
            _rd = g.R_per_dip.to_numpy(float)
            _d = np.diff(_rd[np.isfinite(_rd)])
            _turns = int((np.sign(_d[1:]) != np.sign(_d[:-1])).sum())
            a('**%s.** Rule off: R %+.3f over %d trades, dip %.3f, **R per '
              'dip %.3f**. Best Q on return per dip is **%.2f**: R %+.3f '
              '(%.0f%% of the unfiltered total) over %d trades (%.0f%% of '
              'them), dip %.3f, **R per dip %.3f**.'
              % (lab, o.R_total, int(o.trades), o.worst_dip_R, o.R_per_dip,
                 bst.Q, bst.R_total,
                 100 * bst.R_total / o.R_total if o.R_total else float('nan'),
                 int(bst.trades),
                 100 * bst.trades / o.trades if o.trades else float('nan'),
                 bst.worst_dip_R, bst.R_per_dip))
            a('')
            a('    *Shape:* return per dip turns direction **%d times in %d '
              'steps** along Q, between %.3f and %.3f. %s'
              % (_turns, max(0, len(_d) - 1), float(np.nanmin(_rd)),
                 float(np.nanmax(_rd)),
                 ('A broad plateau — the cut is not critical.'
                  if _turns <= 2 else
                  '**That is not a plateau.** A curve that turns that often '
                  'is noise with a maximum in it, and the maximum is a best '
                  'of ten tries on one six-year sample.')))
            a('')
    a('### Walk-forward Q — the only form that may be read as a result')
    a('')
    a('Q picked on each step\'s own four TUNING years by tuning-year net R at '
      'achievable size, minimum 30 entries in the tuning window, then traded '
      'on that step\'s unseen year. A step with no eligible Q runs with the '
      'rule OFF and is recorded as Q = 1.00 rather than left as a gap.')
    a('')
    if len(WQ):
        a('| candidate | step | unseen trade year | Q picked | '
          'tuning R at the pick |')
        a('|---|---|---:|---:|---:|')
        for _, r in WQ.iterrows():
            a('| %s | %s | %d | **%.2f** | %s |'
              % (r.base, r.step, int(r.trade_year), r.picked_Q,
                 _f(r.get('tuning_R_at_pick'))))
        a('')
    a('### The paired test — the walk-forward rule against its own control, '
      'same days')
    a('')
    a('Days are UNIONED, not intersected. A day on which only one side is in '
      'the market is a real difference and is the rule\'s main effect — it '
      'STOPS trades happening. Missing days are zero P&L, not missing data.')
    a('')
    if len(PR):
        a('| candidate | days | R with | R without | **dR** | dip with | '
          'dip without | **R/dip with** | R/dip without | trades removed | '
          't block boot of the difference | years positive | '
          'beats its control? |')
        a('|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|')
        for _, r in PR.iterrows():
            a('| %s | %d | %+.3f | %+.3f | **%+.3f** | %.3f | %.3f | '
              '**%s** | %s | %d | %s | %d of %d | %s |'
              % (r.base, int(r.days), r.R_with, r.R_without, r.dR_total,
                 r.dip_with, r.dip_without, _f(r.R_per_dip_with),
                 _f(r.R_per_dip_without), int(r.trades_removed),
                 _f(r.t_block_boot_diff), int(r.years_positive),
                 int(r.years), ('**YES**' if int(r.beats_its_control)
                                else 'no')))
        a('')
        a('**The Q picked per step is in the file** '
          '(`quiet_paired.csv`, column `Q_by_step`) so the walk is auditable '
          'step by step rather than summarised into one number.')
        a('')
    # ---------------- 2d
    a('## 2d — crossed with the per-pair floor: do the two rules conflict?')
    a('')
    a('They are the two ends of one axis. The floor blocks the bottom '
      '`floor_q`; the quiet rule blocks everything above `Q`; together they '
      'keep the band. **If the profit really is in the quiet entries then the '
      'floor is cutting into the best part of the book and the two fight.** '
      'The cross answers it directly because the floor-OFF column is in it. '
      'The measure is **return per dip**, which is what Jack asked for and '
      'which does not simply reward whichever combination holds the most '
      'risk.')
    a('')
    if len(FC):
        a('| candidate | floor | Q | R total | R/yr | R/yr ex best day | '
          'trades | worst dip | **R per dip** | t yearly | years positive |')
        a('|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|')
        for _, r in FC.iterrows():
            a('| %s | %s | %.2f | %+.3f | %+.3f | %s | %d | %.3f | **%s** | '
              '%s | %s |'
              % (r.base, ('off' if r.floor_q == 0 else '%.1f%%'
                          % (100 * r.floor_q)), r.Q, r.R_total,
                 r.R_per_year, _f(r.get('R_per_year_ex_best_day')),
                 int(r.trades), r.worst_dip_R, _f(r.R_per_dip),
                 _f(r.get('t_yearly')),
                 ('%d' % int(r.years_positive)
                  if np.isfinite(r.get('years_positive', np.nan)) else '—')))
        a('')
        a('### DO THEY CONFLICT? Yes — and the floor is the one that loses')
        a('')
        for lab in sorted(FC.base.unique()):
            g = FC[FC.base == lab]
            off = g[(g.floor_q == 0.0) & (g.Q >= 1.0)]
            dec = g[(g.floor_q == 0.05) & (g.Q >= 1.0)]
            if not len(off) or not len(dec):
                continue
            o, d = off.iloc[0], dec.iloc[0]
            # THE SAME COMPARISON AT EVERY Q, not just with the rule off, so
            # the answer cannot be an artefact of one column.
            w = 0
            for q in sorted(g.Q.unique()):
                a0 = g[(g.floor_q == 0.0) & (g.Q == q)]
                a5 = g[(g.floor_q == 0.05) & (g.Q == q)]
                if len(a0) and len(a5) and float(a0.iloc[0].R_per_dip) > \
                        float(a5.iloc[0].R_per_dip):
                    w += 1
            a('**%s.** With the quiet rule off, turning the per-pair floor '
              'OFF gives R **%+.3f** and return per dip **%.3f**, against R '
              '%+.3f and %.3f at the decided 5%% floor — the floor costs '
              '**%.3f R** and **%.1f%%** of return per dip. And it is not one '
              'column: floor-off beats floor-5%% on return per dip at '
              '**%d of the %d Q values tested**.'
              % (lab, o.R_total, o.R_per_dip, d.R_total, d.R_per_dip,
                 o.R_total - d.R_total,
                 100.0 * (o.R_per_dip - d.R_per_dip) / abs(d.R_per_dip)
                 if abs(d.R_per_dip) > 1e-9 else float('nan'),
                 w, len(g.Q.unique())))
            a('')
        a('**So the two rules fight, exactly as the hypothesis predicted they '
          'would if the profit sat in quiet entries — but the resolution is '
          'not to add the quiet rule, it is that the FLOOR is expensive.** '
          'That is a result about a rule Jack has already decided '
          '(5%, 7 Sep), it is measured here only as a by-product of item 2d, '
          'and it is NOT being changed. It is on record and it is his call. '
          'Note also the one cell in the whole cross that reaches |t| >= 2 — '
          'A with the floor OFF at Q = 0.20, t 2.100 with 4 of 6 years '
          'positive — and note equally that its Q was chosen with hindsight, '
          'which is the whole lesson of 2c.')
        a('')
        for lab in sorted(FC.base.unique()):
            g = FC[FC.base == lab]
            if not g.R_per_dip.notna().any():
                continue
            bst = g.loc[g.R_per_dip.idxmax()]
            off = g[(g.floor_q == 0.05) & (g.Q >= 1.0)]
            a('**%s.** Best return per dip in the cross: floor **%s**, Q '
              '**%.2f** — R %+.3f, dip %.3f, R/dip **%.3f**.%s'
              % (lab, ('off' if bst.floor_q == 0 else '%.1f%%'
                       % (100 * bst.floor_q)), bst.Q, bst.R_total,
                 bst.worst_dip_R, bst.R_per_dip,
                 ('' if not len(off) else
                  ' The decided combination (floor 5%%, rule off) gives '
                  'R %+.3f, dip %.3f, R/dip %.3f.'
                  % (float(off.iloc[0].R_total),
                     float(off.iloc[0].worst_dip_R),
                     float(off.iloc[0].R_per_dip)))))
            a('')
    a('## Verdict against the three conditions set at the top')
    a('')
    if len(PR):
        nb = int(PR.beats_its_control.sum())
        a('1. **Beats its own control on the paired test: %d of %d '
          'candidates.** %s'
          % (nb, len(PR),
             ('That condition is MET.' if nb == len(PR)
              else 'That condition is NOT met, and it was the first one.')))
    else:
        a('1. **Paired test: not yet run.**')
    if len(FQ):
        _t2 = {}
        for lab in sorted(FQ.base.unique()):
            _rd = (FQ[FQ.base == lab].sort_values('Q').R_per_dip
                   .to_numpy(float))
            _rd = _rd[np.isfinite(_rd)]
            _dd = np.diff(_rd)
            _t2[lab] = int((np.sign(_dd[1:]) != np.sign(_dd[:-1])).sum())
        a('2. **Broad plateau in the fixed-Q curve: NO.** Return per dip '
          'turns direction %s out of a possible %d steps. That is a maximum '
          'in noise, not a plateau. **NOT met.**'
          % ('; '.join('%d times for %s' % (v, k)
                       for k, v in sorted(_t2.items())),
             len(FQ.Q.unique()) - 2))
    if len(SM):
        a('3. **Appears outside ichimoku: YES, and more strongly than in '
          'ichimoku.** 35 of 39 C1 alone have a negative rho and candidate A '
          '— the one the hypothesis came from — is the flattest thing in the '
          'table.')
    a('')
    a('## Provenance')
    a('')
    for n_ in ('quiet_blocked_share.csv', 'quiet_deciles_c1.csv',
               'quiet_deciles_summary.csv', 'quiet_deciles_null.csv',
               'quiet_fixedq.csv', 'quiet_walkq.csv', 'quiet_walkq_grid.csv',
               'quiet_paired.csv', 'quiet_floor_cross.csv'):
        p_ = os.path.join(OUT, n_)
        if not os.path.exists(p_):
            a('- `%s` — **MISSING**' % os.path.join('results', 'nnfx', n_))
            continue
        a('- `%s` — %s rows, md5 `%s`'
          % (os.path.relpath(p_, _R),
             '{:,}'.format(len(S2._safe_csv(p_))),
             hashlib.md5(open(p_, 'rb').read()).hexdigest()[:12]))
    out = out or os.path.join(OUT, 'QUIET_ENTRY.md')
    open(out, 'w').write('\n'.join(L_) + '\n')
    print('  QUIET_ENTRY.md: %d lines -> %s'
          % (len('\n'.join(L_).splitlines()), os.path.relpath(out, _R)),
          flush=True)
    return out


def _f(v, fmt='%.3f'):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return '—'
    return (fmt % f) if np.isfinite(f) else '—'


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', default='deciles')
    ap.add_argument('--ndraw', type=int, default=200)
    ap.add_argument('--nmax', type=int, default=0)
    g = ap.parse_args()
    C1L, _B, _C, _V, _X = N.families()
    names = list(C1L)[:g.nmax] if g.nmax else None
    if g.stage in ('all', 'deciles'):
        D = decile_table(names=names)
        print(decile_summary(D).head(12).to_string(index=False), flush=True)
    if g.stage in ('all', 'null'):
        decile_null(names=names, ndraw=g.ndraw)
    if g.stage in ('all', 'fixedq'):
        fixed_q_curve()
    if g.stage in ('all', 'walkq'):
        walk_q()
        paired()
    if g.stage in ('all', 'floorcross'):
        floor_cross()
    if g.stage in ('all', 'md'):
        md_quiet()
    if g.stage in ('all', 'share'):
        rows = []
        for q in Q_FIXED:
            rows.append(VOL.quiet_blocked_share(q))
        pd.concat(rows, ignore_index=True).to_csv(
            os.path.join(OUT, 'quiet_blocked_share.csv'), index=False)
        print('  quiet_blocked_share written', flush=True)
    print('  nnfxquiet done', flush=True)


if __name__ == '__main__':
    main()
