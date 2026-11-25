import os,sys
_R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_R, 'code'))
os.chdir(_R)
ROOTOUT = os.path.join(_R, 'results')
"""THE VOLATILITY FLOOR, THE CRISIS COLUMNS AND THE LEVERAGE CHECK.

Jack, 24 Nov: the SNB trade is already solved by a decided rule and the staged
build is not applying it. Decided rule 1 (7 Sep 2026, gate4-design.md): a pair
does not trade when its own ATR is in its bottom 5%.

WHERE THE FLAG ALREADY LIVES. `code/l2suppvol.py`, function `atr_floors`:
`LOWVOL_Q = 0.05` and, per pair, `np.quantile(ATR/close, 0.05)` over the pair's
whole series. A trade is flagged when `atr[entry_bar]/close[entry_bar]` is below
that floor. The same module carries `CAP_LEV = 30.0`, `RISK_FRAC = 0.02` and
`CAP_THR = 0.02/30`, which is the 6.67 bp threshold GAUNTLET.md quotes.

AS BUILT IT IS A REPORT, AND IT IS LOOK-AHEAD TWICE. l2suppvol says so of
itself -- "Report only; kills nothing". The percentile is taken over the pair's
ENTIRE series, including years after the bar being judged, and the ATR is read
at the entry bar itself rather than lagged. Neither matters for a report. Both
matter the moment it decides a trade.

SO THERE ARE TWO MASKS HERE AND THE DIFFERENCE IS THE WHOLE POINT.
  `asbuilt`  full-history percentile, same-bar ATR -- what GAUNTLET validated
  `causal`   expanding percentile over bars <= t-1, ATR lagged one bar -- the
             only version a trading rule may use

MEASURED ON THE SNB TRADE, EURCHF entry 2 Jan 2015, lagged ATR/price 12.756 bp:
  asbuilt floor  15.242 bp  -> flag ON,  the trade is blocked
  causal  floor  12.687 bp  -> flag OFF, the trade is TAKEN, by 0.069 bp
The causal rule misses it by half a per cent of the floor. The reason is
structural and worth stating plainly: after three years of the peg, the peg IS
EURCHF's own normal, so the pair's own 5th percentile collapses toward the
pegged level. A per-pair percentile cannot flag a long peg once the peg
dominates the pair's own history. The full-history version only catches this
trade because it has already seen the post-float volatility of 2015 onward.

WHAT DOES CATCH IT, and it is not close: the CROSS-SECTIONAL floor. On
2 Jan 2015 EURCHF's lagged ATR/price was 12.756 bp while the median G8 pair was
86.0 bp and the next quietest, USDCAD, was 63.4 bp -- EURCHF was 6.7x below the
median and 5x below the next pair. A cross-sectional 5% floor blocks it at every
quantile from 1% up. That is reported for information; Jack's per-pair 5% is the
rule and is what the staged build applies.

HOW IT IS APPLIED. Via the VOLUME SLOT, `v_ok_l`/`v_ok_s`. Those arrays appear
in l2engine at :527-528 and :585-587 and NOWHERE ELSE -- both are entry
conditions -- so gating them blocks entries and leaves exits alone, which is
what "no entry on a pair while its flag is on" means. `suspect` was the obvious
candidate and is wrong: l2engine:106 says the engine will not OPEN **or CLOSE**
on a suspect bar, so it would freeze exits through the flag window too.
"""
import numpy as np, pandas as pd

import l2lib as L
import l2sweep as S
import nnfx1 as N

LOWVOL_Q = 0.05
Q_CURVE = (0.01, 0.025, 0.05, 0.10)
ATR_LEN = 14
MIN_HIST = 250            # bars before the expanding percentile is trusted
CAP_LEV = 30.0            # l2suppvol.CAP_LEV
RISK_FRAC = 0.02          # l2suppvol.RISK_FRAC
RISK_DOLLARS = 200.0      # l2engine.run default
EQUITY = RISK_DOLLARS / RISK_FRAC      # 10,000 in the quote currency
_MC = {}


def _rel(pair, atr_len=ATR_LEN):
    """ATR/close per bar, and the pair's own index."""
    d = N.pair_data(pair)
    h, l, c = (d[k].values.astype(float) for k in ('high', 'low', 'close'))
    a = L.P.atr(h, l, c, int(atr_len))
    return pd.DatetimeIndex(d.index), np.where(c > 0, a / c, np.nan)


def lowvol_mask(pair, q=LOWVOL_Q, atr_len=ATR_LEN, causal=True):
    """True on bars where this pair's own ATR/price is in its bottom q.

    causal=True   expanding percentile over bars <= t-1 with the ATR lagged one
                  bar: the only form a trading rule may use.
    causal=False  the l2suppvol form: full-history percentile, same-bar ATR.
                  Kept so the difference can be quoted, never traded on.
    """
    key = (pair, float(q), int(atr_len), bool(causal))
    if key in _MC:
        return _MC[key]
    ix, rel = _rel(pair, atr_len)
    if causal:
        rl = np.full(len(rel), np.nan)
        rl[1:] = rel[:-1]                       # the explicit one-bar lag
        fl = (pd.Series(rl).expanding(min_periods=MIN_HIST)
              .quantile(float(q)).to_numpy())
        m = np.isfinite(rl) & np.isfinite(fl) & (rl < fl)
    else:
        ok = np.isfinite(rel)
        fl = float(np.quantile(rel[ok], float(q))) if ok.any() else np.inf
        m = np.isfinite(rel) & (rel < fl)
    _MC[key] = (ix, m)
    return _MC[key]


def lowvol_xsect(date, q=LOWVOL_Q, atr_len=ATR_LEN):
    """INFORMATION ONLY. The q-quantile of lagged ATR/price ACROSS the 28 pairs
    on one date, and each pair's value against it. Causal by construction: it
    reads only bar t-1 on every pair."""
    vals = {}
    for p in S.all_pairs():
        ix, rel = _rel(p, atr_len)
        i = int(ix.get_indexer([pd.Timestamp(date)])[0])
        if i >= 1 and np.isfinite(rel[i - 1]):
            vals[p] = float(rel[i - 1])
    if not vals:
        return np.nan, {}
    return float(np.quantile(np.array(list(vals.values())), float(q))), vals


def entry_blocked_share(pairs=None, q=LOWVOL_Q, causal=True):
    """How much of the sample the flag removes, per pair and overall."""
    rows = []
    for p in (pairs or S.all_pairs()):
        ix, m = lowvol_mask(p, q=q, causal=causal)
        rows.append(dict(pair=p, bars=int(len(m)), bars_flagged=int(m.sum()),
                         pct_flagged=100.0 * float(m.mean())))
    D = pd.DataFrame(rows)
    return D


# ======================= THE CRISIS COLUMNS =======================
_CW = None


def crisis_windows():
    """The ACUTE detector plus events.py, which is what Jack named.

    `l2crisis.windows()` reads results/crisis_events.csv -- the five acute
    detectors (maxabsmove, breadth2sig, paneldisp, legdiv20, avgcorr60), which
    HANDOFF.md:1319 labels ACUTE -- each opening a forward-only window of
    l2crisis.WINDOW days. `events.py.calendar()` is the news calendar, dated
    from announcements and never from price. The union is used, and a window is
    currency-matched when the event names a currency.
    """
    global _CW
    if _CW is not None:
        return _CW
    import l2crisis as C
    wins = list(C.windows())
    try:
        import events as EV
        cal = EV.calendar()
        for r in cal.itertuples():
            d0 = pd.Timestamp(r.date)
            ccy = getattr(r, 'ccy', None)
            wins.append((d0, d0 + pd.Timedelta(days=C.WINDOW),
                         ccy if isinstance(ccy, str) else None,
                         str(getattr(r, 'description', 'events.py'))))
    except Exception as e:
        print('  !! events.py calendar not read: %s: %s'
              % (type(e).__name__, e), flush=True)
    _CW = wins
    return _CW


def crisis_entry_flag(E):
    """-> bool per ENTRY row: does the holding period touch a crisis window?

    ONE-BAR LAG. A window opens on the event date and runs forward only, as
    crisis.py requires; nothing opens before its event. The flag is read from
    the entry date, which the engine already fixed on the previous bar's
    signals, so no future information reaches the decision.
    """
    import l2crisis as C
    wins = crisis_windows()
    ed = pd.DatetimeIndex(E.entry_date); xd = pd.DatetimeIndex(E.exit_date)
    out = np.zeros(len(E), bool)
    pr = E.pair.astype(str).to_numpy()
    for j in range(len(E)):
        out[j] = bool(C.flag(ed[j], xd[j], pr[j], wins))
    return out


# =================== THE STANDING ROBUSTNESS COLUMNS ===================
def robust_cols(T, cost, DS, years):
    """Jack's standing columns, 24 Nov, for EVERY Layer 2 table.

    From the first block: total R and R per year excluding the single best day,
    excluding the best five days, excluding the single best trade, the share of
    total R from the best trade, and both t statistics with the best day out.
    From the second: R with crisis days excluded, the crisis share of total R,
    and a flag when that share passes 10%.

    A candidate is judged on the excluding-best-day figures FIRST.
    """
    out = {}
    yrs = list(years)
    d = DS[pd.DatetimeIndex(DS.date).year.isin(yrs)].reset_index(drop=True)
    r = d.R.to_numpy(float)
    ny = max(1, len(set(pd.DatetimeIndex(d.date).year)))
    tot = float(r.sum())
    out['R_total'] = tot
    out['R_per_year'] = tot / ny
    order = np.argsort(-r)
    for k, lab in ((1, 'best_day'), (5, 'best5_days')):
        drop = order[:k]
        keep = np.ones(len(r), bool); keep[drop] = False
        out['R_ex_%s' % lab] = float(r[keep].sum())
        out['R_per_year_ex_%s' % lab] = float(r[keep].sum() / ny)
    out['best_day_R'] = float(r.max()) if len(r) else np.nan
    out['best_day_share'] = (float(r.max() / tot) if abs(tot) > 1e-9
                             else np.nan)
    # both t statistics with the best day removed
    keep1 = np.ones(len(r), bool)
    if len(r):
        keep1[order[0]] = False
    dd = d[keep1]
    ys = (pd.DataFrame(dict(y=pd.DatetimeIndex(dd.date).year, r=dd.R))
          .groupby('y').r.sum().to_numpy(float))
    out['t_yearly_ex_best_day'] = (
        float(ys.mean() * np.sqrt(len(ys)) / ys.std(ddof=1))
        if len(ys) > 1 and ys.std(ddof=1) > 0 else np.nan)
    tb, _sd = N._block_t(dd.R.to_numpy(float), ndraw=2000)
    out['t_block_boot_ex_best_day'] = float(tb)
    # ---- per TRADE, not per leg. entry_frame carries no R column, so the
    # legs' R is summed onto the entry key first -- the two legs of a position
    # sum to the position's R, which is the whole reason entry_frame exists.
    #
    # AND IN THE SAME UNIT AS R_total, WHICH IT WAS NOT. A trade frame carries
    # TWO R columns: `R`, the engine's raw r, and `R_gross`, that restated to
    # the declared 1.5-ATR notional (nnfx3:330, R_gross = R x atr_mult / 1.5).
    # Every reported figure is in the R_gross unit -- `_cost_R` divides by
    # RISK_UNIT_ATR, `_yearly` sums R_gross, and R_total above comes off the
    # daily series. This block summed the RAW column and charged no cost, so
    # best_trade_R and R_ex_best_trade came out 1.5x too large on a realized-
    # by-exit-year basis and sat in the same row as an R_total that is MTM net
    # in the other unit: for A/jack the row read R_total 40.030 beside
    # R_ex_best_trade 92.049. The SHARES were never wrong -- numerator and
    # denominator were both raw, so the 1.5 cancels -- which is why this hid.
    # The denominator is now written out as R_realized_total so the two bases
    # can never be compared by accident again. Fixed 25 Nov 2026.
    E = N.entry_frame(T)
    if len(E):
        assert 'R_gross' in T.columns, 'robust_cols: frame carries no R_gross'
        _net = T.R_gross.to_numpy(float) - np.asarray(cost, float)
        Rsum = (T.assign(_net=_net)
                .groupby(['pair', 'entry_date', 'direction'], as_index=False)
                .agg(R=('_net', 'sum')))
        E = E.merge(Rsum, on=['pair', 'entry_date', 'direction'], how='left')
        xy = pd.DatetimeIndex(E.exit_date).year
        sel = E[np.isin(xy, yrs)]
    else:
        sel = E
    if len(sel) and 'R' in sel.columns:
        rt = sel.R.to_numpy(float)
        out['R_realized_total'] = float(rt.sum())
        out['best_trade_R'] = float(rt.max())
        out['R_ex_best_trade'] = float(rt.sum() - rt.max())
        out['best_trade_share'] = (float(rt.max() / rt.sum())
                                   if abs(rt.sum()) > 1e-9 else np.nan)
        cf = crisis_entry_flag(sel)
        out['n_trades_crisis'] = int(cf.sum())
        out['R_crisis'] = float(rt[cf].sum())
        out['R_ex_crisis'] = float(rt[~cf].sum())
        out['crisis_share'] = (float(rt[cf].sum() / rt.sum())
                               if abs(rt.sum()) > 1e-9 else np.nan)
        cs = out['crisis_share']
        out['crisis_share_over_10pct'] = int(np.isfinite(cs) and abs(cs) > 0.10)
    else:
        for k in ('best_trade_R', 'R_ex_best_trade', 'best_trade_share',
                  'R_crisis', 'R_ex_crisis', 'crisis_share'):
            out[k] = np.nan
        out['n_trades_crisis'] = 0
        out['crisis_share_over_10pct'] = 0
    return out


# ======================= THE LEVERAGE CHECK =======================
def leverage_census(T, equity=EQUITY, cap_lev=CAP_LEV):
    """Item 6. Per trade and PORTFOLIO-SUMMED notional against 1:30.

    `units` on a frame row is ONE LEG's size and every leg of an entry carries
    the same number, so a position's notional is `units x n_legs x entry_px`,
    measured in the QUOTE currency -- which the engine treats as the account
    currency, a simplification this states rather than hides.

    Equity is not a free parameter: l2engine risks `risk_dollars` = 200 per
    trade and GAUNTLET declares that as 2% of equity, so equity is 10,000 and
    the 1:30 cap is a 300,000 notional ceiling on the SUM of open positions.
    """
    if not len(T):
        return pd.DataFrame(), pd.DataFrame()
    E = N.entry_frame(T)
    g = (T.groupby(['pair', 'entry_date', 'direction'], as_index=False)
         .agg(n_legs=('leg', 'size'), units=('units', 'first'),
              entry_px=('entry_px', 'first'), exit_date=('exit_date', 'max'),
              R=('R_gross', 'sum')))   # R_gross: the reported 1.5-ATR unit
    g['notional'] = g.units * g.n_legs * g.entry_px
    g['leverage_alone'] = g.notional / float(equity)
    g['over_cap_alone'] = (g.leverage_alone > cap_lev).astype(int)
    # ---- portfolio: at each ENTRY, the notional already open plus this one
    g = g.sort_values('entry_date').reset_index(drop=True)
    ed = pd.DatetimeIndex(g.entry_date); xd = pd.DatetimeIndex(g.exit_date)
    nt = g.notional.to_numpy(float)
    open_before, summed = np.zeros(len(g)), np.zeros(len(g))
    for j in range(len(g)):
        live = (ed <= ed[j]) & (xd >= ed[j])
        live = live.copy(); live[j] = False
        open_before[j] = float(nt[live].sum())
        summed[j] = open_before[j] + nt[j]
    g['notional_open_before'] = open_before
    g['notional_summed'] = summed
    g['leverage_summed'] = summed / float(equity)
    g['over_cap_summed'] = (g.leverage_summed > cap_lev).astype(int)
    # ---- the achievable size: scale THIS position so the sum fits. Never
    # retroactively cut a position already open -- that would use the future.
    room = np.maximum(0.0, cap_lev * float(equity) - open_before)
    g['scale_to_fit'] = np.where(nt > 0, np.minimum(1.0, room / nt), 1.0)
    g['R_capped'] = g.R * g.scale_to_fit
    summ = dict(
        trades=int(len(g)),
        over_cap_alone=int(g.over_cap_alone.sum()),
        over_cap_summed=int(g.over_cap_summed.sum()),
        pct_over_cap_summed=100.0 * float(g.over_cap_summed.mean()),
        max_leverage_alone=float(g.leverage_alone.max()),
        median_leverage_alone=float(g.leverage_alone.median()),
        max_leverage_summed=float(g.leverage_summed.max()),
        median_leverage_summed=float(g.leverage_summed.median()),
        R_uncapped=float(g.R.sum()), R_capped=float(g.R_capped.sum()),
        R_lost_to_cap=float(g.R.sum() - g.R_capped.sum()),
        equity_assumed=float(equity), cap_leverage=float(cap_lev))
    return g, pd.DataFrame([summ])


# ============== THE PEG GUARD: CROSS-PAIR, AND NOT A PERCENTILE ==============
# Jack, 25 Nov: "Do not use a cross-pair percentile (it would permanently ban
# the quietest pair)." Exactly right -- a 5th-percentile-of-28 rule flags
# roughly 1.4 pairs every single day whatever the market is doing, so the
# structurally quietest pair is banned for its whole life and nothing is
# learned. A RATIO TO THE MEDIAN has no such floor: on a day when every pair is
# quiet together, no pair is flagged, which is the correct behaviour, and a pair
# is flagged only when it is quiet RELATIVE TO ITS PEERS THAT DAY.
PEG_X_CURVE = (0.10, 0.20, 0.30, 0.33, 0.40, 0.50, 0.60, 0.70)
PEG_X_PLACEHOLDER = 0.33      # Jack picks X from the curve; this is labelled
# THE TWO SNB DAYS, so any table can be restated without them. 15 Jan 2015 is
# the floor abandonment; 16 Jan is the exit bar of the trade it made.
SNB_DAYS = ('2015-01-15', '2015-01-16')
_PEGC = {}


def _panel(atr_len=ATR_LEN):
    """(union index, {pair: lagged ATR/price on the union index}, median row)."""
    key = int(atr_len)
    if key in _PEGC:
        return _PEGC[key]
    ixs, rels = {}, {}
    for p in S.all_pairs():
        ix, rel = _rel(p, atr_len)
        rl = np.full(len(rel), np.nan)
        rl[1:] = rel[:-1]                     # the explicit one-bar lag
        ixs[p], rels[p] = ix, rl
    uni = ixs[S.all_pairs()[0]]
    for p in S.all_pairs()[1:]:
        uni = uni.union(ixs[p])
    uni = pd.DatetimeIndex(sorted(set(uni)))
    M = np.full((len(S.all_pairs()), len(uni)), np.nan)
    for j, p in enumerate(S.all_pairs()):
        sel = uni.get_indexer(ixs[p])
        ok = sel >= 0
        M[j, sel[ok]] = rels[p][ok]
    with np.errstate(all='ignore'):
        import warnings
        with warnings.catch_warnings():
            # a union date on which NO pair has a bar gives an all-NaN slice;
            # the median is then NaN and the guard reads False, which is right
            warnings.simplefilter('ignore', RuntimeWarning)
            med = np.nanmedian(M, axis=0)
    _PEGC[key] = (uni, M, med)
    return _PEGC[key]


def peg_mask(pair, x=PEG_X_PLACEHOLDER, atr_len=ATR_LEN):
    """True on bars where this pair's lagged ATR/price is below x x the 28-pair
    MEDIAN of the same lagged quantity that day. Causal by construction: every
    input is bar t-1 on every pair."""
    uni, M, med = _panel(atr_len)
    j = list(S.all_pairs()).index(pair)
    with np.errstate(invalid='ignore'):
        flag = np.isfinite(M[j]) & np.isfinite(med) & (M[j] < float(x) * med)
    ix, _rel_ = _rel(pair, atr_len)
    sel = uni.get_indexer(ix)
    out = np.zeros(len(ix), bool)
    ok = sel >= 0
    out[ok] = flag[sel[ok]]
    return ix, out


def peg_curve(xs=PEG_X_CURVE, atr_len=ATR_LEN):
    """For each X: share of bars flagged, how many pairs ever flagged, and
    whether EURCHF is blocked across the SNB peg."""
    rows = []
    for x in xs:
        tot = flg = 0
        per = {}
        for p in S.all_pairs():
            ix, m = peg_mask(p, x=x, atr_len=atr_len)
            tot += len(m); flg += int(m.sum())
            if m.any():
                per[p] = 100.0 * float(m.mean())
        ixe, me = peg_mask('EURCHF', x=x, atr_len=atr_len)
        peg = (pd.DatetimeIndex(ixe) >= '2011-09-06') & \
              (pd.DatetimeIndex(ixe) <= '2015-01-15')
        i0 = int(pd.DatetimeIndex(ixe).get_indexer([pd.Timestamp('2015-01-02')])[0])
        rows.append(dict(
            X=x, pct_bars_flagged=100.0 * flg / max(1, tot),
            pairs_ever_flagged=len(per),
            worst_pair=(max(per, key=per.get) if per else ''),
            worst_pair_pct=(max(per.values()) if per else 0.0),
            eurchf_pct_all=100.0 * float(me.mean()),
            eurchf_peg_days_blocked=int(me[peg].sum()),
            eurchf_peg_days=int(peg.sum()),
            eurchf_pct_of_peg=100.0 * float(me[peg].mean()) if peg.any() else np.nan,
            blocks_2jan2015=int(bool(me[i0])) if i0 >= 0 else -1))
    return pd.DataFrame(rows)


# ================== THE LEVERAGE CAP, APPLIED NOT REPORTED ==================
def apply_leverage_cap(T, equity=EQUITY, cap_lev=CAP_LEV, verbose=False):
    """Return T restated at ACHIEVABLE SIZE, and the scale actually applied.

    Jack, 25 Nov, standing: every Layer 2 result is computed at achievable
    size -- all open positions summed, capped at 1:30, new entries SCALED DOWN
    (never skipped) to fit, plus the GAUNTLET per-position cap.

    THE RULE IS SEQUENTIAL AND CAUSAL, which it has to be. Entries are walked
    in date order; at each one the room left is `cap x equity` minus the
    notional of positions ALREADY OPEN AT THEIR OWN SCALED SIZE, and the new
    entry takes the smaller of that room and its own per-position cap. A
    position already open is never cut retroactively -- doing that would use
    the future to resize a trade that had already been placed.

    Because the entry is scaled and not skipped, the SET of trades is
    unchanged: only sizes move. So this composes with every other rule without
    changing which bars fire.

    `units`, `R` and `R_gross` are all scaled by the same per-entry factor.
    That is enough to carry the cap through everything downstream: `_cost_R` is
    proportional to `units`, and `daily_series` builds its marks from `units`
    and its exit term from `R_gross`.
    """
    if not len(T):
        return T, pd.DataFrame()
    T = T.reset_index(drop=True).copy()
    key = ['pair', 'entry_date', 'direction']
    g = (T.groupby(key, as_index=False)
         .agg(n_legs=('leg', 'size'), units=('units', 'first'),
              entry_px=('entry_px', 'first'), exit_date=('exit_date', 'max')))
    g['notional_req'] = g.units * g.n_legs * g.entry_px
    g = g.sort_values('entry_date').reset_index(drop=True)
    ed = pd.DatetimeIndex(g.entry_date); xd = pd.DatetimeIndex(g.exit_date)
    req = g.notional_req.to_numpy(float)
    ceiling = float(cap_lev) * float(equity)
    scale = np.ones(len(g))
    placed = np.zeros(len(g))          # notional actually taken
    for j in range(len(g)):
        live = (ed <= ed[j]) & (xd >= ed[j])
        live = live.copy(); live[j] = False
        open_now = float(placed[live].sum())
        room = max(0.0, ceiling - open_now)
        s_port = min(1.0, room / req[j]) if req[j] > 0 else 1.0
        s_alone = min(1.0, ceiling / req[j]) if req[j] > 0 else 1.0
        scale[j] = min(s_port, s_alone)
        placed[j] = req[j] * scale[j]
    g['lev_scale'] = scale
    g['notional_placed'] = placed
    g['capped'] = (g.lev_scale < 1.0 - 1e-12).astype(int)
    M = T.merge(g[key + ['lev_scale', 'notional_req', 'notional_placed',
                         'capped']], on=key, how='left')
    M['lev_scale'] = M.lev_scale.fillna(1.0)
    for c in ('units', 'R', 'R_gross'):
        if c in M.columns:
            M[c] = M[c].to_numpy(float) * M.lev_scale.to_numpy(float)
    summ = pd.DataFrame([dict(
        trades=int(len(g)), trades_capped=int(g.capped.sum()),
        pct_trades_capped=100.0 * float(g.capped.mean()),
        min_scale=float(g.lev_scale.min()),
        mean_scale_on_capped=(float(g[g.capped == 1].lev_scale.mean())
                              if int(g.capped.sum()) else np.nan),
        max_leverage_requested=float((req / float(equity)).max()),
        equity_assumed=float(equity), cap_leverage=float(cap_lev))])
    if verbose:
        print('    leverage cap: %d of %d entries scaled, worst to %.3f'
              % (int(g.capped.sum()), len(g), float(g.lev_scale.min())),
              flush=True)
    return M, summ


# ============ R PER TRADE BY ATR BUCKET AT ENTRY (TEN BUCKETS) ============
def atr_buckets(T, nb=10, atr_len=ATR_LEN):
    """Item 3's last part: is the profit concentrated in low-volatility entries?

    The bucket is the entry bar's LAGGED ATR/price expressed as that pair's own
    expanding percentile -- the same quantity the per-pair floor thresholds, so
    bucket 1 IS the bottom decile the floor is cutting into.
    """
    if not len(T):
        return pd.DataFrame()
    E = N.entry_frame(T)
    if not len(E):
        return pd.DataFrame()
    # NET, LIKE EVERY OTHER LAYER 2 TABLE. The `R` column on a trade frame is
    # GROSS of cost; net R is R minus `_cost_R`, charged per LEG. This table
    # summed the gross column and called it R_total, so for candidate A it read
    # 156.890 R where the net figure every other table quotes is 52.501 -- and
    # `share_of_total_R` was then a share of the wrong denominator, putting
    # bucket 1 at 50.7% of a total that does not exist. The bucket ORDER was
    # never affected (cost per trade is near-uniform); the shares and the R per
    # trade were. Fixed 25 Nov 2026. This is the fourth time a Layer 2 number
    # has been restated in the wrong unit, so the gross column is kept beside
    # the net one rather than dropped.
    _T = T.copy()
    _T['_cost'] = N._cost_R(_T)
    Rsum = (_T.groupby(['pair', 'entry_date', 'direction'], as_index=False)
            .agg(R_gross=('R_gross', 'sum'), cost=('_cost', 'sum')))
    Rsum['R'] = Rsum.R_gross - Rsum.cost
    E = E.merge(Rsum, on=['pair', 'entry_date', 'direction'], how='left')
    pct = np.full(len(E), np.nan)
    for p, sub in E.groupby('pair'):
        ix, rel = _rel(p, atr_len)
        rl = np.full(len(rel), np.nan); rl[1:] = rel[:-1]
        rk = (pd.Series(rl).expanding(min_periods=MIN_HIST)
              .apply(lambda a: (a[:-1] < a[-1]).mean() if len(a) > 1 else np.nan,
                     raw=True).to_numpy())
        sel = ix.get_indexer(pd.DatetimeIndex(sub.entry_date))
        ok = sel >= 0
        pct[sub.index.to_numpy()[ok]] = rk[sel[ok]]
    E['atr_pctile'] = pct
    E = E[np.isfinite(E.atr_pctile.to_numpy(float))]
    if not len(E):
        return pd.DataFrame()
    E['bucket'] = np.minimum(nb - 1,
                             (E.atr_pctile.to_numpy(float) * nb).astype(int)) + 1
    # AND THE SAME BUCKETS WITH 15-16 JANUARY 2015 TAKEN OUT. Without this
    # column the table says "the profit is concentrated in low-volatility
    # entries" when what it may be saying is "ONE low-volatility trade is the
    # profit". For candidate A, net and at achievable size, bucket 1 totals
    # about 59.9 R of which the single EURCHF short through the SNB peg break
    # is +51.05; uncapped that one trade is +74.996. It does NOT carry the
    # bucket on its own: the other 165 trades in the bottom decile are still
    # worth more per trade than the sample mean.
    _xd = pd.DatetimeIndex(E.exit_date) if 'exit_date' in E.columns else None
    E['_snb'] = (_xd.normalize().isin(pd.DatetimeIndex(SNB_DAYS))
                 if _xd is not None else False)
    out = (E.groupby('bucket', as_index=False)
           .agg(n_trades=('R', 'size'), R_total=('R', 'sum'),
                R_per_trade=('R', 'mean'),
                R_gross_total=('R_gross', 'sum'),
                cost_total=('cost', 'sum'),
                atr_pctile_lo=('atr_pctile', 'min'),
                atr_pctile_hi=('atr_pctile', 'max')))
    X = E[~E._snb]
    ox = (X.groupby('bucket', as_index=False)
          .agg(n_trades_ex_SNB=('R', 'size'), R_total_ex_SNB=('R', 'sum'),
               R_per_trade_ex_SNB=('R', 'mean')))
    out = out.merge(ox, on='bucket', how='left')
    tot = float(out.R_total.sum())
    out['share_of_total_R'] = (out.R_total / tot if abs(tot) > 1e-9 else np.nan)
    totx = float(out.R_total_ex_SNB.sum())
    out['share_of_total_R_ex_SNB'] = (out.R_total_ex_SNB / totx
                                      if abs(totx) > 1e-9 else np.nan)
    out['n_SNB_trades'] = (out.n_trades
                           - out.n_trades_ex_SNB.fillna(0)).astype(int)
    return out


if __name__ == '__main__':
    import l2r2gate1 as G
    st = G.opt('--stage', str, 'flag')
    if st == 'flag':
        for q in Q_CURVE:
            D = entry_blocked_share(q=q, causal=True)
            print('  causal q=%.3f: %5.2f%% of bars flagged, worst pair %s at '
                  '%.1f%%' % (q, D.pct_flagged.mean(),
                              D.loc[D.pct_flagged.idxmax()].pair,
                              D.pct_flagged.max()), flush=True)
    else:
        raise SystemExit('unknown stage %s' % st)
