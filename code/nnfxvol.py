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
    # ---- per TRADE, not per leg
    E = N.entry_frame(T)
    if len(E):
        ey = pd.DatetimeIndex(E.entry_date).year
        xy = pd.DatetimeIndex(E.exit_date).year
        sel = E[np.isin(xy, yrs)]
    else:
        sel = E
    if len(sel) and 'R' in sel.columns:
        rt = sel.R.to_numpy(float)
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
              R=('R', 'sum')))
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
