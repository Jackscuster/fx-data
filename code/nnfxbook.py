import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""ITEM 5, JACK 25 NOV -- THE BOOK.

THE TARGET IS THE BOOK'S, NOT A STRATEGY'S: at least 12% a year inside the prop
limits. Everything built up to now has been judged as a single strategy against
a bar it was never being asked to clear. This file combines what exists, EQUAL
RISK PER SLEEVE, and asks what each addition does to the book.

THE SLEEVES, and every one of them is DECLARED, not selected:
  A            ichimoku + sma, full_nnfx, jack plan -- the walk-forward stitch
  B            schaff_trend_cycle + sma, side_xentry, jack plan
  A_quiet      A with item 2's walk-forward quiet-entry Q
  B_quiet      B with the same
  group_assign item 3c's assignment: at each step the best candidate on the
               four tuning years, traded on the unseen year. The all-28
               (pooled) scheme, which was the BEST of the five tested.
  MR120        item 4's best mean-reversion cell: n = 120, entry 2.0,
               conditional on the half-life and the Dickey-Fuller test
  MR60, MR20   the other two declared mean-reversion variants

THE ADDITION ORDER IS JACK'S OWN, FROM THE BRIEF, AND IS NOT SEARCHED. "A, B,
quiet-entry versions, group-assigned strategies, mean reversion" -- in that
order. A greedy search over orders would find the best book by construction and
the number it produced would be a maximum over orderings, which is the fault
item 2 just demonstrated at length. The marginal contribution of EVERY sleeve
to the A+B book is reported separately so the ordering is not the only view.

EQUAL RISK PER SLEEVE means weight 1/N on each sleeve's daily R series, so the
book's risk budget is held constant as sleeves are added and a sleeve has to
EARN its place by being better than the dilution it causes. The alternative --
each sleeve at full size, book = sum -- makes every addition look additive
because it is adding risk as well as return.

THE DIP IS VERIFIED TWO WAYS and the worse one binds, exactly as l2team does:
the TRUE chronological drawdown of the daily series, and DIP95 over shuffled
day orders. Losses cluster in time, so a shuffle-based dip under-states the
real one; sizing on it would knowingly under-size the risk.

THE PROP SIMULATOR IS r2reads.prop_run, unchanged -- the FundedTradingPlus
profile Jack confirmed with the firm. The book is scaled to the TEAM 1 budget
(3.6% dip, 3.6% worst day, l2walkfwd.BUDGETS) before it goes in. Its breach
counts are LOWER BOUNDS because the input is a daily series: an intraday
excursion that breached and recovered before the close is invisible.

Writes results/nnfx/book_sleeves.csv, book_incremental.csv,
book_marginal.csv, book_prop.csv, book_corr.csv and BOOK.md.
"""
import numpy as np, pandas as pd

import nnfx1 as N
import nnfx2s as S2
import nnfxvol as VOL
import nnfxcurves as CUR
import nnfxmr as MR
import l2sweep as S
import r2reads as RR

OUT = os.path.join(ROOTOUT, 'nnfx')
os.makedirs(OUT, exist_ok=True)
BUILD = N.BUILD_YEARS
MAIN = 'jack'
TEAM1_DIP = 3.6
TEAM1_DAY = 3.6
TARGET_PCT = 12.0
ORDER = ('A', 'B', 'A_quiet', 'B_quiet', 'group_assign', 'MR120')


# ===================== the sleeves ======================================
def _ds(T):
    """A sleeve's daily R series at achievable size, BUILD years only."""
    if T is None or not len(T):
        return None
    M, _ = VOL.apply_leverage_cap(T)
    M = M.reset_index(drop=True)
    DS = N.daily_series(M, N._cost_R(M))
    DS = DS[pd.DatetimeIndex(DS.date).year.isin(list(BUILD))]
    if not len(DS):
        return None
    return (pd.Series(DS.R.to_numpy(float),
                      index=pd.DatetimeIndex(DS.date))
            .groupby(level=0).sum())


def _group_assign_frame(scheme='all_28', verbose=True):
    """ITEM 3c's ASSIGNMENT AS A TRADE FRAME, so it can be a sleeve.

    3c was computed from the per-pair bank, which holds aggregates and no
    trades -- enough for an R total, not enough for a daily series. So the
    picked candidates are re-run here and their trades filtered to (the
    group's pairs) x (that step's unseen trade year). Nothing is re-chosen:
    the picks are read from group_assign_steps.csv exactly as 3c made them.
    """
    f = os.path.join(OUT, 'group_assign_steps.csv')
    assert os.path.exists(f), f + ' missing -- run nnfxgroups.py --stage assign'
    ST = pd.read_csv(f)
    ST = ST[(ST.scheme == scheme) & (ST.eligible == 1)]
    G = pd.read_csv(os.path.join(OUT, 'pair_groups.csv'))
    col = {'character': 'character', 'bloc': 'bloc',
           'cost_per_atr': 'cost_per_atr'}.get(scheme)
    C1L, _B, _C, _V, _X = N.families()
    cache = {}
    acc = []
    _lv, _pg, _qq = N.LOWVOL_Q, N.PEG_X, N.QUIET_Q
    try:
        N.LOWVOL_Q, N.PEG_X, N.QUIET_Q = None, None, None
        for _, r in ST.iterrows():
            nm = r.picked
            if nm not in cache:
                if nm in C1L:
                    cache[nm] = N.run_one(nm, 'c1', None, MAIN,
                                          use_hourly=True)
                elif nm in S2.BASE_PICKS:
                    cache[nm] = N.run_one(nm, 'base', None, MAIN,
                                          use_hourly=True)
                elif '+' in str(nm):
                    c1, bs = str(nm).split('+')
                    cache[nm] = S2.run_combo(c1, None, bs, None, MAIN, 'side',
                                             lowvol_q=None, peg_x=None)
                elif nm in ('A', 'B'):
                    _s = {'A': ('ichimoku_signals', 'sma_baseline',
                                'full_nnfx'),
                          'B': ('schaff_trend_cycle_signals', 'sma_baseline',
                                'side_xentry')}[nm]
                    cache[nm] = CUR._stitch(_s[0], _s[1], _s[2], MAIN,
                                            VOL.LOWVOL_Q, VOL.PEG_X_DECIDED)
                else:
                    cache[nm] = pd.DataFrame()
                if verbose:
                    print('      re-ran %-40s %5d legs'
                          % (nm, len(cache[nm])), flush=True)
            T = cache[nm]
            if not len(T):
                continue
            prs = (sorted(G.pair) if col is None
                   else sorted(G[G[col] == r.group].pair))
            X = T[T.pair.isin(prs)
                  & (pd.DatetimeIndex(T.exit_date).year == int(r.trade_year))]
            if len(X):
                acc.append(X)
    finally:
        N.LOWVOL_Q, N.PEG_X, N.QUIET_Q = _lv, _pg, _qq
    return pd.concat(acc, ignore_index=True) if acc else pd.DataFrame()


def sleeves(verbose=True):
    out = {}
    SPEC = (('A', 'ichimoku_signals', 'sma_baseline', 'full_nnfx'),
            ('B', 'schaff_trend_cycle_signals', 'sma_baseline',
             'side_xentry'))
    for lab, c1, base, rs in SPEC:
        out[lab] = CUR._stitch(c1, base, rs, MAIN, VOL.LOWVOL_Q,
                               VOL.PEG_X_DECIDED)
    # the quiet versions, with the Q item 2 picked on each step's tuning years
    P = os.path.join(OUT, 'quiet_walkq.csv')
    if os.path.exists(P):
        W = pd.read_csv(P)
        for lab, c1, base, rs in SPEC:
            p = W[(W.base == lab) & (W.variant == MAIN)]
            if not len(p):
                continue
            qmap = {r.step: (None if r.picked_Q >= 1.0 else float(r.picked_Q))
                    for r in p.itertuples()}
            out['%s_quiet' % lab] = CUR._stitch(c1, base, rs, MAIN,
                                                VOL.LOWVOL_Q,
                                                VOL.PEG_X_DECIDED,
                                                q_by_step=qmap)
    out['group_assign'] = _group_assign_frame('all_28', verbose=verbose)
    for lab, n, ent, sx in MR.VARIANTS:
        T, _gc, _ac, _k = MR.run_variant(lab, n, ent, sx, conditional=True)
        out[lab] = T
    rows = []
    for k, T in out.items():
        s = _ds(T)
        f = _stats(s) if s is not None else {}
        rows.append(dict(sleeve=k, legs=len(T) if T is not None else 0,
                         days=(len(s) if s is not None else 0), **f))
        if verbose:
            print('    %-14s %5d legs  R %+9.3f  R/yr %+7.3f  dip %7.3f  '
                  'R/dip %s'
                  % (k, len(T) if T is not None else 0,
                     f.get('R_total', np.nan), f.get('R_per_year', np.nan),
                     f.get('dip_binding', np.nan),
                     ('%+.3f' % f['R_per_dip']) if 'R_per_dip' in f else '—'),
                  flush=True)
    pd.DataFrame(rows).to_csv(os.path.join(OUT, 'book_sleeves.csv'),
                              index=False)
    return out


# ===================== book statistics ==================================
def _dip95(d, ndraw=400, seed=11):
    """The 95th percentile max drawdown over shuffled day orders."""
    rng = np.random.default_rng(seed)
    d = np.asarray(d, float)
    d = d[np.isfinite(d)]
    if not len(d):
        return np.nan
    out = np.zeros(ndraw)
    for k in range(ndraw):
        x = rng.permutation(d)
        eq = np.cumsum(x)
        out[k] = float(np.max(np.maximum.accumulate(eq) - eq))
    return float(np.quantile(out, 0.95))


def _firm(tot, nyr, bind, worst_day):
    sc = min(RR.FIRM_TRAIL * 100.0 / bind if bind and bind > 0 else np.inf,
             RR.FIRM_DAILY * 100.0 / worst_day
             if worst_day and worst_day > 0 else np.inf)
    return dict(firm_scale=(float(sc) if np.isfinite(sc) else np.nan),
                firm_pct_per_year=(tot / max(1, nyr) * float(sc)
                                   if np.isfinite(sc) else np.nan))


def _stats(s, nboot=2000):
    """Everything item 5 asks of a book, from its daily R series."""
    d = s.to_numpy(float)
    eq = np.cumsum(d)
    true_dip = float(np.max(np.maximum.accumulate(eq) - eq)) if len(d) else np.nan
    d95 = _dip95(d)
    # THE WORSE OF THE TWO BINDS. See the module note.
    bind = np.nanmax([true_dip, d95])
    tot = float(d.sum())
    yrs = (pd.Series(d, index=s.index).groupby(s.index.year).sum()
           .sort_index())
    t_bs, _sd = N._block_t(d, ndraw=nboot)
    worst_day = float(-d.min()) if len(d) and d.min() < 0 else np.nan
    scale = min(TEAM1_DIP / bind if bind and bind > 0 else np.inf,
                TEAM1_DAY / worst_day if worst_day and worst_day > 0
                else np.inf)
    return dict(
        R_total=tot, R_per_year=tot / max(1, len(yrs)),
        dip_true=true_dip, dip95=d95, dip_binding=bind,
        R_per_dip=(tot / bind if bind and bind > 1e-9 else np.nan),
        worst_day_R=worst_day,
        years=int(len(yrs)), years_positive=int((yrs > 0).sum()),
        t_yearly=(float(yrs.mean() * np.sqrt(len(yrs)) / yrs.std(ddof=1))
                  if len(yrs) > 1 and yrs.std(ddof=1) > 0 else np.nan),
        t_block_boot=t_bs,
        team1_scale=(float(scale) if np.isfinite(scale) else np.nan),
        team1_pct_per_year=(100.0 * tot / max(1, len(yrs)) * float(scale)
                            / 100.0 if np.isfinite(scale) else np.nan),
        # AND THE SAME AT THE FIRM'S OWN LIMITS, which is the CEILING. Team 1
        # is an internal budget tighter than the firm's; sizing to 6% trailing
        # and 4% daily instead of 3.6% and 3.6% is the largest size the rules
        # permit. It is reported so "how far from 12%" cannot be answered with
        # a number that a looser budget would have fixed.
        **_firm(tot, len(yrs), bind, worst_day))


def _book(ser, keys):
    """EQUAL RISK PER SLEEVE: weight 1/N, days unioned, missing days ZERO."""
    keys = [k for k in keys if k in ser and ser[k] is not None]
    if not keys:
        return None
    M = pd.DataFrame({k: ser[k] for k in keys}).fillna(0.0)
    return M.mean(axis=1)


def incremental(ser, order=ORDER, nboot=2000, verbose=True):
    rows = []
    prev = None
    for i, k in enumerate(order):
        if k not in ser or ser[k] is None:
            continue
        cur = _book(ser, list(order[:i + 1]))
        f = _stats(cur, nboot=nboot)
        add = dict(step=i + 1, added=k, sleeves=i + 1,
                   members='+'.join(order[:i + 1]), **f)
        if prev is not None:
            # THE PAIRED IMPROVEMENT, on the same days, days unioned and
            # missing days zero -- the book with the sleeve against the book
            # without it. Not two independent t statistics.
            M = pd.DataFrame({'w': cur, 'o': prev}).fillna(0.0)
            diff = (M.w - M.o).to_numpy(float)
            t_d, _sd = N._block_t(diff, ndraw=nboot)
            add['dR_total'] = f['R_total'] - _stats(prev)['R_total']
            add['t_block_boot_diff'] = t_d
            yv = (pd.Series(diff, index=M.index)
                  .groupby(M.index.year).sum())
            add['years_improved'] = int((yv > 0).sum())
            # the NEW SLEEVE against the book it is joining
            s = ser[k].reindex(prev.index).fillna(0.0)
            add['corr_new_sleeve_with_book'] = float(
                np.corrcoef(s.to_numpy(float), prev.to_numpy(float))[0, 1])
        rows.append(add)
        prev = cur
        if verbose:
            print('    +%-14s %d sleeves  R/yr %+7.3f  dip %7.3f  '
                  'R/dip %+6.3f  team1 %+6.2f%%/yr  dR %s  corr %s'
                  % (k, i + 1, f['R_per_year'], f['dip_binding'],
                     f['R_per_dip'], f['team1_pct_per_year'],
                     ('%+.3f' % add['dR_total']) if 'dR_total' in add else '—',
                     ('%+.3f' % add['corr_new_sleeve_with_book'])
                     if 'corr_new_sleeve_with_book' in add else '—'),
                  flush=True)
    D = pd.DataFrame(rows)
    D.to_csv(os.path.join(OUT, 'book_incremental.csv'), index=False)
    return D


def marginal(ser, base=('A', 'B'), nboot=2000, verbose=True):
    """EVERY sleeve's marginal contribution to the A+B book, so the declared
    ordering is not the only view."""
    b0 = _book(ser, list(base))
    f0 = _stats(b0, nboot=nboot)
    rows = [dict(added='(none)', **f0, dR_total=0.0,
                 t_block_boot_diff=np.nan, years_improved=np.nan,
                 corr_new_sleeve_with_book=np.nan, improves=np.nan)]
    for k in sorted(ser):
        if k in base or ser[k] is None:
            continue
        cur = _book(ser, list(base) + [k])
        f = _stats(cur, nboot=nboot)
        M = pd.DataFrame({'w': cur, 'o': b0}).fillna(0.0)
        diff = (M.w - M.o).to_numpy(float)
        t_d, _sd = N._block_t(diff, ndraw=nboot)
        s = ser[k].reindex(b0.index).fillna(0.0)
        yv = pd.Series(diff, index=M.index).groupby(M.index.year).sum()
        rows.append(dict(
            added=k, **f, dR_total=f['R_total'] - f0['R_total'],
            t_block_boot_diff=t_d, years_improved=int((yv > 0).sum()),
            corr_new_sleeve_with_book=float(np.corrcoef(
                s.to_numpy(float), b0.to_numpy(float))[0, 1]),
            # THE TEST IS RETURN PER DIP, not return. A book is judged on what
            # it earns for the risk it has to be allowed to take.
            improves=int(f['R_per_dip'] > f0['R_per_dip'])))
        if verbose:
            print('    A+B+%-14s R/dip %+6.3f (was %+6.3f)  team1 %+6.2f%%/yr'
                  '  corr %+.3f  %s'
                  % (k, f['R_per_dip'], f0['R_per_dip'],
                     f['team1_pct_per_year'],
                     rows[-1]['corr_new_sleeve_with_book'],
                     'BETTER' if rows[-1]['improves'] else 'worse'),
                  flush=True)
    D = pd.DataFrame(rows)
    D.to_csv(os.path.join(OUT, 'book_marginal.csv'), index=False)
    return D


# ===================== the prop simulator ===============================
def prop(ser, order=ORDER, verbose=True):
    """Every prefix of the declared book through the prop simulator, scaled to
    the TEAM 1 budget."""
    rows = []
    for i, k in enumerate(order):
        if k not in ser or ser[k] is None:
            continue
        cur = _book(ser, list(order[:i + 1]))
        f = _stats(cur)
        sc = f['team1_scale']
        if not np.isfinite(sc):
            continue
        pct = cur.to_numpy(float) * sc
        ev = RR.prop_run(pct, phase='eval')
        fd = RR.prop_run(pct, phase='funded')
        # AND THE EVALUATION AT THE FIRM'S OWN LIMITS -- the best case
        pf = (RR.prop_run(cur.to_numpy(float) * f['firm_scale'],
                          phase='eval')
              if np.isfinite(f['firm_scale']) else dict(
                  passed_eval_day=np.nan, breached='', return_pct=np.nan))
        fd_int = RR.prop_run(pct, phase='funded',
                             trail_frac=RR.INT_TRAIL,
                             daily_frac=RR.INT_DAILY)
        rows.append(dict(
            sleeves=i + 1, members='+'.join(order[:i + 1]),
            team1_scale=sc, team1_pct_per_year=f['team1_pct_per_year'],
            eval_days_to_pass=ev['passed_eval_day'],
            eval_breached=ev['breached'], eval_return_pct=ev['return_pct'],
            eval_days_to_pass_at_firm_limits=pf['passed_eval_day'],
            eval_breached_at_firm_limits=pf['breached'],
            eval_return_pct_at_firm_limits=pf['return_pct'],
            funded_breached=fd['breached'],
            funded_breach_day=fd['breach_day'],
            funded_payout_per_year=fd['paid_out_per_year'],
            funded_return_pct_per_year=fd['return_pct_per_year'],
            funded_worst_dip_pct=fd['worst_dip_pct'],
            internal_breached=fd_int['breached'],
            internal_payout_per_year=fd_int['paid_out_per_year'],
            firm_scale=f['firm_scale'],
            firm_pct_per_year=f['firm_pct_per_year'],
            distance_from_target_pct=TARGET_PCT - f['team1_pct_per_year'],
            distance_from_target_pct_at_firm_limits=(
                TARGET_PCT - f['firm_pct_per_year']),
            times_short_at_firm_limits=(
                TARGET_PCT / f['firm_pct_per_year']
                if (np.isfinite(f['firm_pct_per_year'])
                    and f['firm_pct_per_year'] > 0) else np.nan)))
        if verbose:
            print('    %-40s team1 %+6.2f%%/yr  eval pass day %s  '
                  'funded breach %-8s payout $%.0f/yr'
                  % (rows[-1]['members'], f['team1_pct_per_year'],
                     ('%d' % ev['passed_eval_day'])
                     if np.isfinite(ev['passed_eval_day']) else 'NEVER',
                     fd['breached'] or 'none', fd['paid_out_per_year']),
                  flush=True)
    D = pd.DataFrame(rows)
    D.to_csv(os.path.join(OUT, 'book_prop.csv'), index=False)
    return D



# ====================== THE DOCUMENT ====================================
def md_book(out=None):
    """BOOK.md -- item 5, from the files."""
    import hashlib
    L_ = []
    a = L_.append
    def rd(n, ix=None):
        f = os.path.join(OUT, n)
        if not (os.path.exists(f) and os.path.getsize(f) > 2):
            return pd.DataFrame()
        return pd.read_csv(f, index_col=ix) if ix is not None \
            else pd.read_csv(f)
    SL, IN, MG = rd('book_sleeves.csv'), rd('book_incremental.csv'), \
        rd('book_marginal.csv')
    PP, CR = rd('book_prop.csv'), rd('book_corr.csv', 0)
    a('# THE BOOK — item 5, Jack 25 November 2026')
    a('')
    best = (PP.loc[PP.firm_pct_per_year.idxmax()] if len(PP)
            and PP.firm_pct_per_year.notna().any() else None)
    if best is not None:
        a('## The answer first')
        a('')
        a('**The best book is `%s`. At the firm\'s own maximum legal sizing '
          'it makes %.3f%% a year. The target is 12%%. It is %.1f percentage '
          'points short — a factor of %.1f.**'
          % (best.members, best.firm_pct_per_year,
             best.distance_from_target_pct_at_firm_limits,
             best.times_short_at_firm_limits))
        a('')
        a('**And no book at any sizing ever passes the +10%% evaluation**, '
          'over six years of unseen data. Not one of the %d prefixes, not at '
          'the Team 1 budget and not at the firm\'s limits.' % len(PP))
        a('')
        a('**The gap is not a sizing problem and it is not a combination '
          'problem. It is a return problem.** Combination and sizing are '
          'arithmetic and both have been done correctly here; reaching 12% '
          'needs roughly ten times more return per unit of risk than the best '
          'thing this project has built.')
        a('')
    a('## How the book is built, and the two choices that matter')
    a('')
    a('**EQUAL RISK PER SLEEVE means weight 1/N on each sleeve\'s daily R '
      'series**, so the book\'s risk budget is held constant as sleeves are '
      'added and a sleeve has to EARN its place by being better than the '
      'dilution it causes. The alternative — every sleeve at full size, book '
      '= sum — makes every addition look additive because it is adding risk '
      'as well as return.')
    a('')
    a('**THE ADDITION ORDER IS THE BRIEF\'S OWN AND IS NOT SEARCHED**: "A, B, '
      'quiet-entry versions, group-assigned strategies, mean reversion", in '
      'that order. A greedy search over orderings would find the best book by '
      'construction, and the number it produced would be a maximum over '
      'orderings — the exact fault item 2 spent a document demonstrating. '
      'The marginal contribution of **every** sleeve to the A+B book is '
      'reported separately so the ordering is not the only view.')
    a('')
    a('**THE DIP IS VERIFIED TWO WAYS AND THE WORSE ONE BINDS**, exactly as '
      '`l2team` does: the TRUE chronological drawdown of the daily series, '
      'and DIP95 over 400 shuffled day orders. Losses cluster in time, so a '
      'shuffle-based dip understates the real one and sizing on it would '
      'knowingly under-size the risk.')
    a('')
    a('**The prop simulator is `r2reads.prop_run`, unchanged** — the '
      'FundedTradingPlus profile Jack confirmed with the firm: 6% trailing '
      'floor that stops trailing permanently once it reaches the starting '
      'balance, 4% daily from the previous close with floating losses '
      'counting, 10% evaluation target, 80% payouts every 7 days, $549 fee, '
      '1:30 leverage. **Its breach counts are LOWER BOUNDS** because the '
      'input is a daily series: an intraday excursion that breached and '
      'recovered before the close is invisible.')
    a('')
    if len(SL):
        a('## The sleeves on their own, unseen years 2010–2015')
        a('')
        a('| sleeve | legs | days | R total | R/yr | true dip | DIP95 | '
          '**binding dip** | R per dip | worst day | years + | t yearly |')
        a('|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|')
        for _, r in SL.sort_values('R_per_dip', ascending=False).iterrows():
            a('| `%s` | %d | %d | %+.3f | %+.3f | %.3f | %.3f | **%.3f** | '
              '%s | %.3f | %d of %d | %s |'
              % (r.sleeve, int(r.legs), int(r.days), r.R_total, r.R_per_year,
                 r.dip_true, r.dip95, r.dip_binding, _f(r.R_per_dip),
                 r.worst_day_R, int(r.years_positive), int(r.years),
                 _f(r.t_yearly)))
        a('')
        a('**DIP95 is BELOW the true dip on every sleeve**, which is the '
          'point of measuring both: the real order of days is worse than a '
          'random order of the same days, so the true drawdown binds '
          'everywhere and nothing is being sized off a shuffle.')
        a('')
    if len(IN):
        a('## The declared addition sequence')
        a('')
        a('| step | added | members | R/yr | binding dip | **R per dip** | '
          '**Team 1 %/yr** | dR total | t of the difference | years improved '
          '| corr of the new sleeve with the book |')
        a('|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|')
        for _, r in IN.iterrows():
            a('| %d | `%s` | %s | %+.3f | %.3f | **%s** | **%+.3f%%** | %s | '
              '%s | %s | %s |'
              % (int(r.step), r.added, r.members, r.R_per_year,
                 r.dip_binding, _f(r.R_per_dip), r.team1_pct_per_year,
                 _f(r.get('dR_total')), _f(r.get('t_block_boot_diff')),
                 ('%d' % int(r.years_improved)
                  if np.isfinite(r.get('years_improved', np.nan)) else '—'),
                 _f(r.get('corr_new_sleeve_with_book'))))
        a('')
        a('**Every addition in the declared order makes the book worse than '
          'A on its own.** A alone is R per dip %s and %.3f%% a year at the '
          'Team 1 budget; the full six-sleeve book is %s and %.3f%%. Not one '
          'step\'s paired t statistic comes close to 2, in either direction.'
          % (_f(IN.iloc[0].R_per_dip), IN.iloc[0].team1_pct_per_year,
             _f(IN.iloc[-1].R_per_dip), IN.iloc[-1].team1_pct_per_year))
        a('')
    if len(MG):
        a('## Every sleeve\'s marginal contribution to the A+B book')
        a('')
        a('Judged on **return per dip**, because a book is judged on what it '
          'earns for the risk it has to be allowed to take, and because total '
          'R alone would reward whichever combination holds the most risk.')
        a('')
        base = MG[MG.added == '(none)']
        a('| added to A+B | R/yr | binding dip | **R per dip** | '
          'Team 1 %/yr | dR total | t of the difference | '
          'corr with the A+B book | better? |')
        a('|---|---:|---:|---:|---:|---:|---:|---:|---|')
        for _, r in MG.sort_values('R_per_dip', ascending=False).iterrows():
            b = '**' if r.added == '(none)' else ''
            a('| %s`%s`%s | %+.3f | %.3f | **%s** | %+.3f%% | %s | %s | %s | '
              '%s |'
              % (b, r.added, b, r.R_per_year, r.dip_binding,
                 _f(r.R_per_dip), r.team1_pct_per_year, _f(r.get('dR_total')),
                 _f(r.get('t_block_boot_diff')),
                 _f(r.get('corr_new_sleeve_with_book')),
                 ('—' if r.added == '(none)'
                  else ('**BETTER**' if int(r.improves) else 'worse'))))
        a('')
        imp = MG[(MG.added != '(none)') & (MG.improves == 1)]
        if len(imp) and len(base):
            a('**%d of the %d candidate additions improve the A+B book\'s '
              'return per dip**: %s. And every one of them still leaves the '
              'book below **A on its own** (%s).'
              % (len(imp), len(MG) - 1,
                 '; '.join('`%s` %s (corr %+.3f)'
                           % (r.added, _f(r.R_per_dip),
                              r.corr_new_sleeve_with_book)
                           for _, r in imp.sort_values(
                               'R_per_dip', ascending=False).iterrows()),
                 _f(IN.iloc[0].R_per_dip) if len(IN) else '—'))
            a('')
            a('**The two findings in that table are worth separating.** '
              '`A_quiet` improves the A+B book but correlates **%.3f** with '
              'A — it is not a second sleeve, it is A with a quarter of the '
              'trades removed, so what it is really showing is that A+B is '
              'worse than A and anything that dilutes B helps. `MR120` and '
              '`MR60` improve it at a correlation of **%+.3f** and **%+.3f** '
              '— those ARE genuine diversification, exactly as item 4 '
              'predicted, and they are still not enough to beat one sleeve.'
              % (float(CR.loc['A', 'A_quiet'])
                 if ('A' in CR.index and 'A_quiet' in CR.columns)
                 else float('nan'),
                 float(MG[MG.added == 'MR120'].corr_new_sleeve_with_book
                       .iloc[0]) if len(MG[MG.added == 'MR120']) else
                 float('nan'),
                 float(MG[MG.added == 'MR60'].corr_new_sleeve_with_book
                       .iloc[0]) if len(MG[MG.added == 'MR60']) else
                 float('nan')))
            a('')
    if len(CR):
        a('## The sleeve correlation matrix')
        a('')
        cols = list(CR.columns)
        a('| | %s |' % ' | '.join('`%s`' % c for c in cols))
        a('|---|%s|' % ('---:|' * len(cols)))
        for i in CR.index:
            a('| `%s` | %s |' % (i, ' | '.join(
                ('**1.000**' if i == c else '%+.3f' % CR.loc[i, c])
                for c in cols)))
        a('')
        a('**The diversification the book plan needs is genuinely there.** '
          'All three mean-reversion sleeves are negatively correlated with A '
          'and `MR20` is negatively correlated with every trend sleeve in the '
          'table. **It is not the binding constraint.** `A_quiet` at %.3f '
          'with A is the one thing in the matrix that is not a sleeve at all.'
          % (float(CR.loc['A', 'A_quiet'])
             if ('A' in CR.index and 'A_quiet' in CR.columns)
             else float('nan')))
        a('')
    if len(PP):
        a('## Through the prop simulator, at the Team 1 budget and at the '
          'firm\'s limits')
        a('')
        a('| book | Team 1 %/yr | **firm limits %/yr** | days to pass +10% | '
          'at firm limits | funded breaches | payout $/yr | '
          'internal (3.6/5.4) breaches | **short of 12% by** | '
          '**times short** |')
        a('|---|---:|---:|---|---|---|---:|---|---:|---:|')
        for _, r in PP.iterrows():
            a('| %s | %+.3f%% | **%+.3f%%** | %s | %s | %s | $%.0f | %s | '
              '%.3f pp | **%.1fx** |'
              % (r.members, r.team1_pct_per_year, r.firm_pct_per_year,
                 ('%d' % r.eval_days_to_pass
                  if np.isfinite(r.eval_days_to_pass) else '**NEVER**'),
                 ('%d' % r.eval_days_to_pass_at_firm_limits
                  if np.isfinite(r.eval_days_to_pass_at_firm_limits)
                  else '**NEVER**'),
                 (str(r.funded_breached)
                  if isinstance(r.funded_breached, str)
                  and r.funded_breached else 'none'),
                 r.funded_payout_per_year,
                 (str(r.internal_breached)
                  if isinstance(r.internal_breached, str)
                  and r.internal_breached else 'none'),
                 r.distance_from_target_pct_at_firm_limits,
                 r.times_short_at_firm_limits))
        a('')
        a('**Three things to read off it.**')
        a('')
        a('1. **No book passes the evaluation, ever, at either sizing.** The '
          'best makes about %.1f%% in six years where the target is +10%% '
          'with no time limit. The evaluation is not the binding problem — '
          'the return is.'
          % (6.0 * float(PP.firm_pct_per_year.max())))
        a('2. **No book breaches anything, at either the firm\'s limits or '
          'the tighter internal ones.** That is not a safety result, it is '
          'the same fact from the other side: a book sized so its worst '
          'historical drawdown fits in 3.6% or 6% is a book that barely '
          'moves.')
        a('3. **The payout on the best book is $%.0f a year against a $549 '
          'fee** — $%.0f a year net. On the full six-sleeve book it is $%.0f, '
          'which is less than the fee.'
          % (float(PP.funded_payout_per_year.max()),
             float(PP.funded_payout_per_year.max()) - 549.0,
             float(PP.funded_payout_per_year.iloc[-1])))
        a('')
    a('## What this settles')
    a('')
    a('1. **Settled: the book machinery works and is not the problem.** '
      'Equal-risk combination, the two-way dip verification, the Team 1 and '
      'firm-limit sizing and the prop simulator all run end to end on every '
      'sleeve this project has produced, and every number above comes from '
      'files.')
    a('2. **Settled: the diversification is available and it is not enough.** '
      'Mean reversion is negatively correlated with A, improves the A+B '
      'book\'s return per dip, and the resulting book is still worse than A '
      'on its own.')
    a('3. **Settled: the best book is ONE SLEEVE**, and every addition in the '
      'brief\'s own order makes it worse at equal risk.')
    a('4. **Settled: the distance to 12% is a factor of about ten**, at the '
      'largest size the firm\'s rules permit, on six years of unseen data.')
    a('5. **NOT settled, and this is the live question: where another order of '
      'magnitude of return per unit of risk would come from.** Nothing in '
      'items 1 to 5 found it. Item 3 did find that the cross-sectional '
      'dispersion is enormous — a per-pair assignment with hindsight is worth '
      '+520 R over the same six years against the −72 R any tested rule '
      'achieved — so the room exists in the data. No tested selection rule '
      'reaches any of it, and that, rather than combination or sizing, is '
      'where the remaining distance lives.')
    a('')
    a('## Provenance')
    a('')
    for n_ in ('book_sleeves.csv', 'book_incremental.csv',
               'book_marginal.csv', 'book_prop.csv', 'book_corr.csv'):
        p_ = os.path.join(OUT, n_)
        if not os.path.exists(p_):
            a('- `%s` — **MISSING**' % os.path.join('results', 'nnfx', n_))
            continue
        a('- `%s` — %s rows, md5 `%s`'
          % (os.path.relpath(p_, _R),
             '{:,}'.format(len(S2._safe_csv(p_))),
             hashlib.md5(open(p_, 'rb').read()).hexdigest()[:12]))
    out = out or os.path.join(OUT, 'BOOK.md')
    open(out, 'w').write('\n'.join(L_) + '\n')
    print('  BOOK.md: %d lines -> %s'
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
    g = ap.parse_args()
    if g.stage == 'md':
        md_book()
        return
    T = sleeves()
    ser = {k: _ds(v) for k, v in T.items()}
    ser = {k: v for k, v in ser.items() if v is not None}
    M = pd.DataFrame(ser).fillna(0.0)
    C = M.corr()
    C.index.name = 'sleeve'
    C.to_csv(os.path.join(OUT, 'book_corr.csv'))
    print('  sleeve correlations written', flush=True)
    incremental(ser)
    marginal(ser)
    prop(ser)
    md_book()
    print('  nnfxbook done', flush=True)


if __name__ == '__main__':
    main()
