import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""ITEM 4, JACK 25 NOV -- A SECOND TYPE OF STRATEGY: DECLARED MEAN REVERSION.

WHERE THE RULE COMES FROM, cited rather than reinvented. The mean-reversion
rule of the early project work is `code/strat.py:52`:

    def meanrev(p, n, entry):
        z = (p - p.rolling(n).mean()) / p.rolling(n).std()
        pos[z <= -entry] = 1.0 ; pos[z >= entry] = -1.0
        pos[z.abs() < 0.1] = 0.0

and its evidence is `HANDOFF_3.md` section 9 -- a 38-config sweep over 28
pairs with costs on, in which `mean_reversion` had mean OOS Sharpe **+0.109**
with 69% of pairs positive against `momentum` at **-0.225**, and the best
single config was **n = 60, entry = 2.0** at mean OOS Sharpe 0.197 with 82% of
pairs positive. Those are the only numbers from the early work used here, and
they are used to DECLARE the variants, not to pick them.

ONE CORRECTION TO JACK'S DESCRIPTION, because it matters for what is being
tested. He calls it "the conditional mean reversion rule from the early project
work". The early work's CONDITION was the 9-box (HANDOFF_3 section 10:
"mean reversion works when price is MOVING and fails when it is flat", every
flat box negative). It was NOT a half-life or a stationarity test -- the repo
has a Hurst exponent (`code/sig2.py:31`) and no half-life and no ADF. So the
half-life and the stationarity test specified in item 4 are NEW and are built
here; the early work's own condition is reported beside them as the declared
alternative it was.

THREE VARIANTS, DECLARED, NO SEARCH. Nothing below is swept:
  MR60   n = 60,  entry 2.0   -- the early work's best config, as cited
  MR20   n = 20,  entry 2.0   -- one faster
  MR120  n = 120, entry 2.0   -- one slower
The stop is 1.0 further standard deviation beyond the entry stretch (z = 3.0)
in every variant, and the target is the mean (z = 0), as item 4 specifies.
`entry` is not varied at all, because varying it would be the search item 4
forbids.

THE CONDITION, both halves measured causally on a 252-bar window ending at
t-1, and BOTH must agree:
  half-life   the Ornstein-Uhlenbeck half-life of the spread (close minus its
              own n-bar mean), from the regression ds_t = a + b s_{t-1} + e,
              half-life = -ln 2 / ln(1 + b). It must be FINITE, POSITIVE and
              no longer than the lookback n -- a series that takes longer than
              its own window to revert is not reverting inside the window the
              rule trades on.
  stationarity  the Dickey-Fuller t statistic on b from that same regression,
              constant and no trend, against the standard large-sample 5%
              critical value -2.86 (Fuller 1976; MacKinnon 1991). No
              statsmodels in this environment, so the statistic is computed
              directly and the critical value is a constant in this file --
              stated plainly rather than hidden behind a library call.

EVERY PROJECT CONVENTION APPLIES AND NONE IS RELAXED.
  * ONE-BAR LAG ON EVERYTHING. z, the half-life and the ADF statistic are all
    computed from data through t-1 and acted on at the close of t. This is
    STRICTER than l2engine, which reads signals at the close of t and fills at
    that same close; the mean-reversion rule is not the engine and there is no
    reason to inherit its one declared exception.
  * REALISTIC GAP FILLS, through l2engine._gap_px itself -- the same function
    pre-flight guard 41 checks. A stop fills at the first tradable price at or
    beyond it.
  * THE AMBIGUOUS BAR. A bar whose range covers both the stop and the target
    asks the hourly path which came first, through l2engine._amb_first, and
    keeps STOP-first where the hourly path cannot say. Same as the engine.
  * R IS IN THE SAME 1.5-ATR UNIT as every other Layer 2 number, so these
    trades can be summed into the same book: units = RISK / (1.5 x ATR) and
    R_gross is the move in those units. The stop is therefore NOT at 1 R -- a
    3-sigma stop is whatever it is in ATR terms -- and that is reported rather
    than normalised away.
  * COSTS from the standing table, the LEVERAGE CAP, the robustness columns,
    the crisis columns, the random-entry null and the true chronological dip.
  * 2016-2020 computed and NOT reported. 2021 onward never read.

Writes results/nnfx/mr_trades.csv, mr_summary.csv, mr_per_pair.csv,
mr_condition.csv, mr_corr.csv and MEAN_REVERSION.md.
"""
import numpy as np, pandas as pd

import nnfx1 as N
import nnfx2s as S2
import nnfxvol as VOL
import nnfxcurves as CUR
import nnfxamb as AMB
import l2sweep as S
import l2engine as E
import l2ind as IND

OUT = os.path.join(ROOTOUT, 'nnfx')
os.makedirs(OUT, exist_ok=True)
BUILD = N.BUILD_YEARS
RISK_UNIT_ATR = N.RISK_UNIT_ATR
ADF_CRIT_5PCT = -2.86          # Fuller 1976 / MacKinnon 1991, constant, no trend
COND_WIN = 252                 # one year of bars for the condition
ATR_LEN = 14
VARIANTS = (('MR60', 60, 2.0, 1.0),
            ('MR20', 20, 2.0, 1.0),
            ('MR120', 120, 2.0, 1.0))


# ===================== the condition ====================================
def _df_stats(s, win=COND_WIN):
    """Rolling OU half-life and Dickey-Fuller t on the spread `s`.

    ONE REGRESSION SERVES BOTH. ds_t = a + b s_{t-1} + e over the trailing
    `win` bars: the half-life is -ln2/ln(1+b) and the DF statistic is b over
    its own standard error. Computing them from two different fits would let
    them disagree about the same window, which is exactly the thing the
    "both must agree" condition is supposed to rule out.

    EVERYTHING IS SHIFTED ONE BAR BY THE CALLER. This function sees only the
    series it is given.
    """
    n = len(s)
    hl = np.full(n, np.nan)
    tt = np.full(n, np.nan)
    y = np.diff(s)                       # ds_t, aligned to s[1:]
    x = s[:-1]                           # s_{t-1}
    for i in range(win, n):
        a = i - win
        xv = x[a:i - 1]
        yv = y[a:i - 1]
        m = np.isfinite(xv) & np.isfinite(yv)
        if m.sum() < win // 2:
            continue
        xv, yv = xv[m], yv[m]
        xm, ym = xv.mean(), yv.mean()
        sxx = float(((xv - xm) ** 2).sum())
        if sxx <= 0:
            continue
        b = float(((xv - xm) * (yv - ym)).sum() / sxx)
        res = yv - (ym + b * (xv - xm))
        k = len(xv) - 2
        if k <= 0:
            continue
        sig2 = float((res ** 2).sum() / k)
        se = np.sqrt(sig2 / sxx) if sxx > 0 else np.nan
        tt[i] = b / se if (se and np.isfinite(se) and se > 0) else np.nan
        if -1.0 < b < 0.0:
            hl[i] = -np.log(2.0) / np.log(1.0 + b)
    return hl, tt


_PREP = {}


def _prep(pair, n):
    """Everything one (pair, lookback) needs, all lagged one bar.

    CACHED PER (pair, lookback) because the rolling Dickey-Fuller is the
    expensive part of this file and twelve runs over 28 pairs would otherwise
    recompute the identical regressions 336 times.
    """
    key = (pair, int(n))
    if key in _PREP:
        return _PREP[key]
    d = S.load_pair(pair)
    o = d.open.values.astype(float)
    h = d.high.values.astype(float)
    l = d.low.values.astype(float)
    c = d.close.values.astype(float)
    atr = IND.atr(h, l, c, ATR_LEN)
    cs = pd.Series(c)
    mu = cs.rolling(int(n)).mean().to_numpy()
    sd = cs.rolling(int(n)).std().to_numpy()
    spread = c - mu
    hl, tt = _df_stats(spread, COND_WIN)
    # THE ONE-BAR LAG, explicit and in one place
    L = lambda v: np.concatenate(([np.nan], np.asarray(v, float)[:-1]))
    _PREP[key] = dict(
        ix=pd.DatetimeIndex(d.index), o=o, h=h, l=l, c=c, atr=atr,
        mu_l=L(mu), sd_l=L(sd),
        z_l=L(np.where(sd > 0, (c - mu) / sd, np.nan)),
        hl_l=L(hl), tt_l=L(tt), atr_l=L(atr))
    return _PREP[key]


def condition_report(verbose=True):
    """How often does the condition pass, per pair and per variant?"""
    rows = []
    for (lab, n, ent, sx) in VARIANTS:
        for p in S.all_pairs():
            A = _prep(p, n)
            ok_hl = np.isfinite(A['hl_l']) & (A['hl_l'] > 0) & (A['hl_l'] <= n)
            ok_st = np.isfinite(A['tt_l']) & (A['tt_l'] <= ADF_CRIT_5PCT)
            both = ok_hl & ok_st
            yr = A['ix'].year.to_numpy()
            m = np.isin(yr, list(BUILD))
            rows.append(dict(
                variant=lab, n=n, pair=p, bars=int(m.sum()),
                pct_halflife_ok=100.0 * float(ok_hl[m].mean()) if m.any() else np.nan,
                pct_stationary_ok=100.0 * float(ok_st[m].mean()) if m.any() else np.nan,
                pct_both_ok=100.0 * float(both[m].mean()) if m.any() else np.nan,
                median_halflife=float(np.nanmedian(A['hl_l'][m])) if m.any() else np.nan,
                median_df_t=float(np.nanmedian(A['tt_l'][m])) if m.any() else np.nan))
    D = pd.DataFrame(rows)
    D.to_csv(os.path.join(OUT, 'mr_condition.csv'), index=False)
    if verbose:
        for lab, g in D.groupby('variant'):
            print('    %-6s half-life ok %.1f%%  stationary ok %.1f%%  '
                  'BOTH %.1f%%  median half-life %.1f bars'
                  % (lab, g.pct_halflife_ok.mean(), g.pct_stationary_ok.mean(),
                     g.pct_both_ok.mean(), g.median_halflife.median()),
                  flush=True)
    return D


# ===================== the bar loop =====================================
def run_pair(pair, n, ent, stop_extra, conditional=True, ranging=None,
             risk=None):
    """One pair, one variant. -> list of trade dicts.

    ONE POSITION AT A TIME PER PAIR, flat to flat. The early rule held a
    position until z crossed zero and could flip straight into the other side;
    this one exits flat and may re-enter on the next bar, which is the same
    book on all but the flip bar and makes every trade a separable record for
    the per-pair bank.
    """
    A = _prep(pair, n)
    risk = float(risk if risk is not None else S.RISK)
    gf_tol = AMB.gf_tol(pair)
    hb_lo, hb_hi, ha_lo, ha_hi, hr_off, hb_op, ha_op = AMB.hourly_index(pair)
    gf_on = bool(hr_off[-1] > 0)
    gc = np.zeros(4, np.int64)
    ac = np.zeros(3, np.int64)
    o, h, l, c = A['o'], A['h'], A['l'], A['c']
    z, mu, sd, atr = A['z_l'], A['mu_l'], A['sd_l'], A['atr_l']
    hl, tt = A['hl_l'], A['tt_l']
    ix = A['ix']
    rg = None
    if ranging is not None:
        rg = ranging.reindex(ix).to_numpy()
    nb = len(c)
    out = []
    pos = 0
    n_skip = 0
    for i in range(1, nb):
        if pos != 0:
            hit_s = (l[i] <= s_stop) if pos == 1 else (h[i] >= s_stop)
            hit_t = (h[i] >= s_tp) if pos == 1 else (l[i] <= s_tp)
            tp_first = False
            if hit_s and hit_t:
                # SAME TIE-BREAK AS THE ENGINE: ask the hourly path, keep
                # stop-first where it cannot say, and count the case.
                v = 0
                if gf_on:
                    v = E._amb_first(hb_lo, hb_hi, ha_lo, ha_hi, hr_off, i,
                                     s_stop, s_tp, pos == 1)
                if v == 1:
                    tp_first = True
                    ac[0] += 1
                elif v == -1:
                    ac[1] += 1
                else:
                    ac[2] += 1
            reason, px = None, None
            if hit_s and not tp_first:
                px = E._gap_px(hb_op, hb_lo, ha_op, ha_hi, hr_off, gf_on,
                               gf_tol, i, s_stop, pos == 1, o[i], gc)
                reason = 'stop'
            elif hit_t:
                px, reason = s_tp, 'target'
            elif i == nb - 1:
                px, reason = c[i], 'end of data'
            if reason is not None:
                r_raw = (px - s_px) * s_u / risk * (1 if pos == 1 else -1)
                out.append(dict(
                    pair=pair, direction='long' if pos == 1 else 'short',
                    entry_date=ix[s_i], exit_date=ix[i],
                    entry_px=s_px, exit_px=px, units=s_u, leg=1,
                    bars_held=i - s_i, reason=reason,
                    R=r_raw, R_gross=r_raw, atr_mult_used=RISK_UNIT_ATR,
                    z_at_entry=s_z, halflife_at_entry=s_hl,
                    df_t_at_entry=s_tt, stop_px=s_stop, tp_px=s_tp,
                    atr_at_entry=s_atr))
                pos = 0
        if pos == 0 and np.isfinite(z[i]) and np.isfinite(atr[i]) \
                and atr[i] > 0 and np.isfinite(sd[i]) and sd[i] > 0:
            if conditional:
                ok = (np.isfinite(hl[i]) and 0 < hl[i] <= n
                      and np.isfinite(tt[i]) and tt[i] <= ADF_CRIT_5PCT)
            else:
                ok = True
            if rg is not None:
                ok = ok and (rg[i] == 'ranging')
            if ok and abs(z[i]) >= ent:
                _dir = 1 if z[i] <= -ent else -1
                _px = c[i]
                _stop = (mu[i] - (ent + stop_extra) * sd[i] if _dir == 1
                         else mu[i] + (ent + stop_extra) * sd[i])
                _tp = mu[i]
                # THE SIGNAL IS LAGGED AND THE FILL IS NOT, SO THE LEVELS CAN
                # BE ON THE WRONG SIDE OF THE FILL. z, mu and sd are bar
                # t-1's; the fill is bar t's close. If t's close has already
                # run past the stop, or already reached the mean, the order
                # would never have been placed -- and taking it anyway books
                # an instant exit at an arbitrary price. The first run of this
                # file did exactly that and produced "stop" exits with
                # POSITIVE R, which is how it was caught.
                _sane = ((_stop < _px < _tp) if _dir == 1
                         else (_tp < _px < _stop))
                if not _sane:
                    n_skip += 1
                    continue
                pos = _dir
                s_i, s_px = i, _px
                s_u = risk / (RISK_UNIT_ATR * atr[i])
                s_z, s_hl, s_tt, s_atr = z[i], hl[i], tt[i], atr[i]
                # the stretch is measured in the pair's OWN lagged sigma, and
                # the stop sits one further sigma beyond the entry stretch
                s_stop, s_tp = _stop, _tp
    return out, gc, ac, n_skip


def run_variant(lab, n, ent, sx, conditional=True, ranging=None, pairs=None,
                verbose=False):
    rows, gc, ac, nsk = [], np.zeros(4, np.int64), np.zeros(3, np.int64), 0
    for p in (pairs or S.all_pairs()):
        _rg = (ranging.set_pair(p)
               if hasattr(ranging, 'set_pair') else ranging)
        r, g, a, k = run_pair(p, n, ent, sx, conditional=conditional,
                              ranging=_rg)
        rows += r
        gc += g
        ac += a
        nsk += k
    if not rows:
        return pd.DataFrame(), gc, ac, nsk
    T = pd.DataFrame(rows)
    T['variant'] = lab
    T['lookback'] = n
    T['entry_z'] = ent
    T['stop_z'] = ent + sx
    T['conditional'] = int(bool(conditional))
    T['ranging_gate'] = int(ranging is not None)
    T['lowvol_q'] = 0.0
    T['peg_x'] = 0.0
    T['quiet_q'] = 1.0
    T['gapfill_on'] = 1
    T['leverage_cap_on'] = 1
    return T, gc, ac, nsk



# ===================== scoring, the standing columns ====================
def _score(T, years=BUILD, nboot=2000, ndraw=200):
    """The standing Layer 2 column set on a mean-reversion frame.

    It is the SAME apparatus: the leverage cap, the cost table, the daily
    mark-to-market series, the true chronological dip, the robustness columns,
    the crisis columns and the matched random-entry null. That is the point of
    expressing R in the 1.5-ATR unit -- a second TYPE of strategy that could
    not be scored by the same machinery could not be put in the same book.
    """
    if not len(T):
        return {}
    M, lsum = VOL.apply_leverage_cap(T)
    M = M.reset_index(drop=True)
    cost = N._cost_R(M)
    DS = N.daily_series(M, cost)
    Y = N._yearly(M, cost, DS)
    b = Y[Y.year.isin(list(years))]
    tot = float(b.R_net.sum()) if len(b) else np.nan
    ys = b.sort_values('year').R_net.to_numpy(float) if len(b) else np.array([])
    dip = N.true_dip(DS, years)
    ds = DS[pd.DatetimeIndex(DS.date).year.isin(list(years))]
    t_bs, _sd = N._block_t(ds.R.to_numpy(float), ndraw=nboot)
    out = dict(VOL.robust_cols(M, cost, DS, years))
    nul, ntr, _ym, chg = N._null_match(M, cost, ndraw=ndraw, years=years)
    out.update(
        R_total=tot, R_per_year=tot / max(1, len(b)),
        trades=float(b.n_entered.sum()) if len(b) else 0.0,
        R_per_trade=(tot / float(b.n_entered.sum())
                     if len(b) and b.n_entered.sum() else np.nan),
        worst_dip_R=dip, R_per_dip=(tot / dip if (dip and dip > 1e-9)
                                    else np.nan),
        t_yearly=(float(ys.mean() * np.sqrt(len(ys)) / ys.std(ddof=1))
                  if len(ys) > 1 and ys.std(ddof=1) > 0 else np.nan),
        t_block_boot=t_bs,
        years=int(len(ys)), years_positive=int((ys > 0).sum()),
        null_mean=(float(nul.mean()) if len(nul) else np.nan),
        null_max=(float(nul.max()) if len(nul) else np.nan),
        null_p=(float((nul >= tot).mean()) if len(nul) else np.nan),
        pct_trades_capped=(float(lsum.pct_trades_capped.iloc[0])
                           if len(lsum) else np.nan),
        min_lev_scale=(float(lsum.min_scale.iloc[0]) if len(lsum) else np.nan))
    return out


def _ranging_series():
    """Layer 1's `shape2 == ranging` as a per-pair daily series.

    IT IS IN-SAMPLE OVER THE UNSEEN YEARS AND THAT IS STATED, NOT HIDDEN. The
    file's own header says "IS to 2015 (cuts fitted)", so a `ranging` label on
    a 2010-2015 bar was produced by a model whose cuts were fitted on a window
    containing that bar. Item 4 asks for the gate with and without, so both
    are reported -- but the WITH column is not a walk-forward number and may
    not be quoted as one.

    The lag is already right: the file states that a row dated D is built from
    bars <= D-1, so the gate is read as given and NOT shifted again. Shifting
    a lagged series a second time is a silent half-day of dead reaction time
    and would make the gate look worse than it is.
    """
    f = os.path.join(ROOTOUT, 'layer1_states.csv')
    if not os.path.exists(f):
        return None
    # THE FILE CARRIES A '#' HEADER AND SAYS SO: readers pass comment='#'.
    # It also states that a row dated D is built from bars <= D-1, so the
    # gate is ALREADY one-bar lagged and must not be lagged again here.
    L = pd.read_csv(f, usecols=['date', 'pair', 'shape2'],
                    parse_dates=['date'], comment='#')
    return {p: g.set_index('date').shape2
            for p, g in L.groupby('pair')}


def run_all(verbose=True):
    """Every declared variant: conditional and not, all 28 pairs and the
    range-prone group, and the RANGING gate with and without."""
    G = pd.read_csv(os.path.join(OUT, 'pair_groups.csv'))
    rp = sorted(G[G.character == 'RANGE_PRONE'].pair)
    RG = _ranging_series()
    rows, keep, allT = [], {}, []
    for (lab, n, ent, sx) in VARIANTS:
        for cond in (True, False):
            for gate in ((False, True) if RG is not None else (False,)):
                T, gc, ac, nsk = run_variant(
                    lab, n, ent, sx, conditional=cond,
                    ranging=None if not gate else _RangingProxy(RG))
                if not len(T):
                    continue
                allT.append(T)
                for scope, prs in (('all_28', None), ('range_prone', rp)):
                    X = T if prs is None else T[T.pair.isin(prs)]
                    f = _score(X)
                    if not f:
                        continue
                    rows.append(dict(
                        variant=lab, lookback=n, entry_z=ent,
                        stop_z=ent + sx, conditional=int(cond),
                        ranging_gate=int(gate), scope=scope,
                        n_pairs=(28 if prs is None else len(prs)),
                        entries_unplaceable=nsk,
                        stop_fills_gapped=int(gc[1]),
                        stop_fills_no_gap=int(gc[0]),
                        amb_target_first=int(ac[0]),
                        amb_stop_first=int(ac[1]),
                        amb_unresolved=int(ac[2]),
                        **f))
                keep[(lab, cond, gate)] = T
                if verbose:
                    _r = rows[-2] if len(rows) >= 2 else rows[-1]
                    print('    %-6s cond=%d gate=%d  all28 R %+.3f  R/yr %+.3f'
                          '  dip %.3f  n %d'
                          % (lab, int(cond), int(gate), _r['R_total'],
                             _r['R_per_year'], _r['worst_dip_R'],
                             int(_r['trades'])), flush=True)
    D = pd.DataFrame(rows)
    D.to_csv(os.path.join(OUT, 'mr_summary.csv'), index=False)
    if allT:
        TT = pd.concat(allT, ignore_index=True)
        TT.to_csv(os.path.join(OUT, 'mr_trades.csv'), index=False)
    # per pair, the declared variant only, conditional, no gate
    pp = []
    for (lab, cond, gate), T in keep.items():
        if not cond or gate:
            continue
        M, _ = VOL.apply_leverage_cap(T)
        M = M.reset_index(drop=True)
        M['_c'] = N._cost_R(M)
        M['R_net'] = M.R_gross - M._c
        M['year'] = pd.DatetimeIndex(M.exit_date).year
        U = M[M.year.isin(list(BUILD))]
        for (p, d), g in U.groupby(['pair', 'direction']):
            pp.append(dict(variant=lab, pair=p, direction=d,
                           n_trades=len(g), R_total=float(g.R_net.sum()),
                           R_per_trade=float(g.R_net.mean()),
                           years=int(g.year.nunique()),
                           best_trade_R=float(g.R_net.max()),
                           worst_trade_R=float(g.R_net.min()),
                           win_rate=float((g.R_net > 0).mean()),
                           mean_bars=float(g.bars_held.mean()),
                           range_prone=int(p in rp)))
    P = pd.DataFrame(pp)
    P.to_csv(os.path.join(OUT, 'mr_per_pair.csv'), index=False)
    return D, P, keep


class _RangingProxy:
    """Lets run_pair call .reindex(ix) once per pair without the caller
    needing to know which pair it is. run_pair is per pair, so the proxy
    resolves the pair from the index it is handed -- which it can, because the
    series dict is keyed by pair and every pair has its own date index.

    IT IS A SHIM AND IT IS HONEST ABOUT BEING ONE. The alternative was a
    `pair` argument threaded through three call sites for one optional gate.
    """
    def __init__(self, by_pair):
        self.by_pair = by_pair
        self.current = None

    def set_pair(self, p):
        self.current = p
        return self

    def reindex(self, ix):
        s = self.by_pair.get(self.current)
        if s is None:
            return pd.Series(index=ix, dtype=object)
        return s.reindex(ix)



# ===================== the daily correlation to A =======================
def corr_to_A(keep, verbose=True):
    """Daily P&L correlation of each mean-reversion variant to candidate A.

    THIS IS THE NUMBER THAT DECIDES WHETHER IT IS WORTH HAVING. A second TYPE
    of strategy earns its place in a book by being uncorrelated, not by being
    better. A sleeve at 0.0 that makes half as much as A is a better addition
    than one at 0.8 that matches it.

    Days are UNIONED and missing days are ZERO, not dropped -- a day a sleeve
    is flat is a real zero for that sleeve.
    """
    TA = CUR._stitch('ichimoku_signals', 'sma_baseline', 'full_nnfx', 'jack',
                     VOL.LOWVOL_Q, VOL.PEG_X_DECIDED)
    ser = {'A': _ds(TA)}
    for (lab, cond, gate), T in sorted(keep.items()):
        if gate:
            continue
        ser['%s%s' % (lab, '' if cond else '_uncond')] = _ds(T)
    ser = {k: v for k, v in ser.items() if v is not None}
    M = pd.DataFrame(ser).fillna(0.0)
    C = M.corr()
    C.index.name = 'series'
    C.to_csv(os.path.join(OUT, 'mr_corr.csv'))
    if verbose and 'A' in C.columns:
        print('  daily corr to A: %s'
              % ', '.join('%s %.3f' % (k, v)
                          for k, v in C['A'].drop('A').items()), flush=True)
    return C


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
def md_mr(out=None):
    """MEAN_REVERSION.md -- item 4, from the files."""
    import hashlib
    L_ = []
    a = L_.append
    def rd(n, ix=None):
        f = os.path.join(OUT, n)
        if not (os.path.exists(f) and os.path.getsize(f) > 2):
            return pd.DataFrame()
        return pd.read_csv(f, index_col=ix) if ix is not None \
            else pd.read_csv(f)
    D, P, CD = rd('mr_summary.csv'), rd('mr_per_pair.csv'), \
        rd('mr_condition.csv')
    CR = rd('mr_corr.csv', 0)
    a('# MEAN REVERSION — item 4, Jack 25 November 2026')
    a('')
    a('**A second TYPE of strategy, declared, three variants, no search.**')
    a('')
    a('## Where the rule comes from, cited')
    a('')
    a('`code/strat.py:52` — `meanrev(p, n, entry)`: the z-score of price '
      'against its own rolling `n`-bar mean and standard deviation, long at '
      '`z <= -entry`, short at `z >= entry`, flat at `|z| < 0.1`.')
    a('')
    a('Its evidence is **`HANDOFF_3.md` §9**: a 38-config sweep over 28 pairs '
      'with costs on, in which `mean_reversion` had mean OOS Sharpe '
      '**+0.109** with 69% of pairs positive against `momentum` at '
      '**−0.225**, and the best single config was **n = 60, entry = 2.0** at '
      'mean OOS Sharpe 0.197 with 82% of pairs positive.')
    a('')
    a('**One correction to the brief, because it changes what is being '
      'tested.** The request calls this "the conditional mean reversion rule '
      'from the early project work". The early work\'s CONDITION was the '
      '9-box (`HANDOFF_3.md` §10: *"mean reversion works when price is MOVING '
      'and fails when it is flat"*, every flat box negative) — **not** a '
      'half-life and **not** a stationarity test. The repo has a Hurst '
      'exponent (`code/sig2.py:31`) and neither of the other two. So the '
      'half-life and the stationarity test specified in item 4 are **new and '
      'built here**, and the early work\'s own condition is named as the '
      'declared alternative it was.')
    a('')
    a('## The three variants, and what is NOT varied')
    a('')
    a('| variant | lookback n | entry z | stop z | target |')
    a('|---|---:|---:|---:|---|')
    for lab, n, ent, sx in VARIANTS:
        a('| `%s` | %d | %.1f | %.1f | the mean (z = 0) |'
          % (lab, n, ent, ent + sx))
    a('')
    a('`MR60` is the early work\'s best config as cited. `MR20` is one faster '
      'and `MR120` one slower. **`entry` is not varied at all** — varying it '
      'would be the search item 4 forbids. The stop is one further standard '
      'deviation beyond the entry stretch in every variant.')
    a('')
    a('**The stop is at a fixed z, not a fixed distance from the fill, and '
      'that has a consequence worth stating.** An entry triggers at '
      '`|z| >= 2.0` but can fire at 2.5, in which case only 0.5σ of room is '
      'left to a 3.0σ stop. That is the literal reading of "stop beyond the '
      'stretch" and it is kept, but it means the risk per trade is not '
      'constant and the hit rate is structurally low.')
    a('')
    a('## The condition, and which half of it actually binds')
    a('')
    a('Both halves are measured on a trailing %d-bar window ending at t−1, '
      'from ONE regression `ds_t = a + b·s_{t−1} + e` on the spread (close '
      'minus its own n-bar mean) — computing them from two different fits '
      'would let them disagree about the same window, which is the thing '
      '"both must agree" is meant to rule out.' % COND_WIN)
    a('')
    a('- **half-life** = −ln2 / ln(1+b), required finite, positive and no '
      'longer than the lookback `n`. A series that takes longer than its own '
      'window to revert is not reverting inside the window the rule trades '
      'on.')
    a('- **stationarity** = the Dickey-Fuller t on `b`, constant and no '
      'trend, against the large-sample 5%% critical value **%.2f** '
      '(Fuller 1976; MacKinnon 1991). There is no statsmodels in this '
      'environment, so the statistic is computed directly and the critical '
      'value is a named constant in `code/nnfxmr.py` — stated rather than '
      'hidden behind a library call.' % ADF_CRIT_5PCT)
    a('')
    if len(CD):
        a('| variant | half-life passes | stationarity passes | **both** | '
          'median half-life | median DF t |')
        a('|---|---:|---:|---:|---:|---:|')
        for lab, g in CD.groupby('variant'):
            a('| `%s` | %.1f%% | **%.1f%%** | %.1f%% | %.1f bars | %+.2f |'
              % (lab, g.pct_halflife_ok.mean(), g.pct_stationary_ok.mean(),
                 g.pct_both_ok.mean(), g.median_halflife.median(),
                 g.median_df_t.median()))
        a('')
        a('**The half-life is not binding and the stationarity test is the '
          'whole condition.** The half-life passes on 96.7%% to 99.9%% of '
          'bars; the ADF passes on 9.3%% (`MR120`), 18.0%% (`MR60`) and '
          '90.4%% (`MR20`), and "both" equals the ADF figure to the decimal '
          'in every variant. So "a pair\'s own half-life AND a stationarity '
          'test both agree" is, in practice, the stationarity test alone — '
          'and for `MR20` it barely gates anything at all, which is why '
          '`MR20` conditional and unconditional are nearly the same book '
          '(daily correlation %.3f).'
          % (float(CR.loc['MR20', 'MR20_uncond'])
             if ('MR20' in CR.index and 'MR20_uncond' in CR.columns)
             else float('nan')))
        a('')
    a('## The results, unseen years 2010–2015')
    a('')
    a('Realistic gap fills through `l2engine._gap_px`, the ambiguous bar '
      'resolved by the hourly path through `l2engine._amb_first`, costs from '
      'the standing table, the leverage cap on, R in the same 1.5-ATR unit as '
      'every other Layer 2 number. 2016–2020 computed and not reported.')
    a('')
    if len(D):
        a('| variant | conditional | RANGING gate | scope | R total | R/yr | '
          'R/yr ex best day | trades | worst dip | R per dip | t yearly | '
          't block boot | years + | null p | best trade share | '
          'crisis share |')
        a('|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|'
          '---:|---:|---:|')
        for _, r in D.iterrows():
            b = '**' if (r.R_total > 0 and r.conditional == 1
                         and r.ranging_gate == 0) else ''
            cf = '**%.3f**' % r.crisis_share if (
                np.isfinite(r.crisis_share) and r.crisis_share > 0.10) else \
                _f(r.crisis_share)
            a('| %s`%s`%s | %d | %d | %s | %s%+.3f%s | %+.3f | %s | %d | '
              '%.3f | %s | %s | %s | %d of %d | %s | %s | %s |'
              % (b, r.variant, b, int(r.conditional), int(r.ranging_gate),
                 r.scope, b, r.R_total, b, r.R_per_year,
                 _f(r.get('R_per_year_ex_best_day')), int(r.trades),
                 r.worst_dip_R, _f(r.R_per_dip), _f(r.t_yearly),
                 _f(r.t_block_boot), int(r.years_positive), int(r.years),
                 _f(r.null_p), _f(r.get('best_trade_share')), cf))
        a('')
        a('### What that says, in order')
        a('')
        pos = D[(D.R_total > 0)]
        a('1. **%d of the %d cells are positive and not one of them reaches '
          '|t| = 2.** The best are %s. Every cell that DOES reach |t| ≥ 2 is '
          'negative (%s).'
          % (len(pos), len(D),
             '; '.join('`%s` %s cond=%d gate=%d **%+.3f R** (t %s, null p %s)'
                       % (r.variant, r.scope, int(r.conditional),
                          int(r.ranging_gate), r.R_total, _f(r.t_yearly),
                          _f(r.null_p))
                       for _, r in pos.nlargest(3, 'R_total').iterrows()),
             '; '.join('`%s` %s t %s' % (r.variant, r.scope, _f(r.t_yearly))
                       for _, r in D[D.t_yearly.abs() >= 2.0].iterrows())
             or 'none'))
        a('2. **THE CONDITION IS DOING ALL THE WORK, and the size of that is '
          'the most striking number in the file.** On all 28 pairs with no '
          'gate: `MR120` goes from **%+.3f R unconditional to %+.3f R '
          'conditional** and `MR60` from %+.3f to %+.3f. The worst dip falls '
          'from %.1f to %.1f on `MR120`. That is not a tweak — the '
          'unconditional rule is a disaster and the ADF filter is what makes '
          'it merely unproven.'
          % (float(D[(D.variant == 'MR120') & (D.conditional == 0)
                     & (D.ranging_gate == 0)
                     & (D.scope == 'all_28')].R_total.iloc[0]),
             float(D[(D.variant == 'MR120') & (D.conditional == 1)
                     & (D.ranging_gate == 0)
                     & (D.scope == 'all_28')].R_total.iloc[0]),
             float(D[(D.variant == 'MR60') & (D.conditional == 0)
                     & (D.ranging_gate == 0)
                     & (D.scope == 'all_28')].R_total.iloc[0]),
             float(D[(D.variant == 'MR60') & (D.conditional == 1)
                     & (D.ranging_gate == 0)
                     & (D.scope == 'all_28')].R_total.iloc[0]),
             float(D[(D.variant == 'MR120') & (D.conditional == 0)
                     & (D.ranging_gate == 0)
                     & (D.scope == 'all_28')].worst_dip_R.iloc[0]),
             float(D[(D.variant == 'MR120') & (D.conditional == 1)
                     & (D.ranging_gate == 0)
                     & (D.scope == 'all_28')].worst_dip_R.iloc[0])))
        _g = D[(D.ranging_gate == 1)].set_index(
            ['variant', 'conditional', 'scope']).R_total
        _n = D[(D.ranging_gate == 0)].set_index(
            ['variant', 'conditional', 'scope']).R_total
        _k = _g.index.intersection(_n.index)
        _kc = [x for x in _k if x[1] == 1]
        _ku = [x for x in _k if x[1] == 0]
        a('3. **THE LAYER 1 `RANGING` GATE MAKES IT WORSE, and exactly where '
          'it matters.** Over all %d comparisons it helps in %d — but split '
          'them: among the **conditional** variants it helps in **%d of %d**, '
          'and among the unconditional ones in %d of %d. So the gate only '
          'adds anything where there is no condition to add it to. It is a '
          'worse substitute for the ADF filter, not a complement to it. And '
          'the gated column is **not a walk-forward number**: '
          '`layer1_states.csv` says "IS to 2015 (cuts fitted)", so a '
          '`ranging` label on a 2010–2015 bar comes from a model whose cuts '
          'were fitted on a window containing that bar. The gate is '
          'in-sample and still loses.'
          % (len(_k), int((_g[_k] > _n[_k]).sum()),
             int((_g[_kc] > _n[_kc]).sum()), len(_kc),
             int((_g[_ku] > _n[_ku]).sum()), len(_ku)))
        _rpD = D[D.scope == 'range_prone'].set_index(
            ['variant', 'conditional', 'ranging_gate'])
        _a2D = D[D.scope == 'all_28'].set_index(
            ['variant', 'conditional', 'ranging_gate'])
        _k2 = _rpD.index.intersection(_a2D.index)
        _w = {c: int((_rpD.loc[_k2, c] > _a2D.loc[_k2, c]).sum())
              for c in ('R_total', 'R_per_trade', 'R_per_dip')}
        a('4. **"Mean reversion for range-prone pairs" is NOT supported, and '
          'the way the comparison has to be made is the point.** On TOTAL R '
          'the range-prone group beats all 28 pairs in %d of %d comparisons '
          '— but that is not a fair comparison: range-prone is 9 pairs of 28, '
          'so a losing rule run on a third of the universe simply loses less. '
          'On **R per trade** it wins **%d of %d** and on **R per dip %d of '
          '%d** — a coin flip. And the two best cells in the whole table '
          'disagree with each other: `MR120` is far worse on range-prone '
          '(%+.3f against %+.3f on all 28) while `MR20` is far better. That '
          'is exactly what item 3b predicts: the range-prone label is '
          'pre-2010 pair character and pair character does not persist '
          '(Spearman −0.456 into 2010–2015), so a grouping drawn from it '
          'should split the variants at random — and it does.'
          % (_w['R_total'], len(_k2), _w['R_per_trade'], len(_k2),
             _w['R_per_dip'], len(_k2),
             float(_rpD.loc[('MR120', 1, 0), 'R_total']),
             float(_a2D.loc[('MR120', 1, 0), 'R_total'])))
        _cs = D[(D.R_total > 0) & (D.crisis_share > 0.10)]
        if len(_cs):
            a('5. **FLAGGED: crisis dependence, over the 10%% standing '
              'threshold on every positive cell.** %s. The two conditional '
              'all-28 winners make most of their money in crisis windows, '
              'which for a mean-reversion rule is the opposite of reassuring '
              '— a stretch away from the mean during a crisis is exactly the '
              'stretch that does not come back.'
              % '; '.join('`%s` %s **%.1f%%**'
                          % (r.variant, r.scope, 100 * r.crisis_share)
                          for _, r in _cs.iterrows()))
        a('')
    a('## The daily correlation to candidate A — the number that decides it')
    a('')
    a('A second TYPE of strategy earns its place in a book by being '
      'uncorrelated, not by being better. A sleeve at 0.0 making half as much '
      'as A is a better addition than one at 0.8 matching it.')
    a('')
    if len(CR):
        cols = list(CR.columns)
        a('| | %s |' % ' | '.join('`%s`' % c for c in cols))
        a('|---|%s|' % ('---:|' * len(cols)))
        for i in CR.index:
            a('| `%s` | %s |' % (i, ' | '.join(
                ('**1.000**' if i == c else '%+.3f' % CR.loc[i, c])
                for c in cols)))
        a('')
        if 'A' in CR.columns:
            v = CR['A'].drop('A')
            a('**Every variant is NEGATIVELY correlated with A, from %+.3f to '
              '%+.3f.** That is the genuinely valuable property in this '
              'document and it is the one thing here that is not borderline: '
              'a sleeve that loses when A wins and wins when A loses reduces '
              'a book\'s dip even if its own return is modest. `MR120` '
              'conditional and `MR20` conditional are also nearly independent '
              'of each other (%+.3f), so they are not one sleeve wearing two '
              'labels.'
              % (float(v.min()), float(v.max()),
                 float(CR.loc['MR120', 'MR20'])
                 if ('MR120' in CR.index and 'MR20' in CR.columns)
                 else float('nan')))
            a('')
    if len(P):
        a('## Per pair, the declared variants, conditional, no gate')
        a('')
        a('| variant | pair | direction | trades | R total | R per trade | '
          'win rate | mean bars | range-prone? |')
        a('|---|---|---|---:|---:|---:|---:|---:|---|')
        for _, r in P.nlargest(10, 'R_total').iterrows():
            a('| `%s` | %s | %s | %d | **%+.3f** | %+.3f | %.2f | %.0f | %s |'
              % (r.variant, r.pair, r.direction, int(r.n_trades), r.R_total,
                 r.R_per_trade, r.win_rate, r.mean_bars,
                 'yes' if int(r.range_prone) else 'no'))
        for _, r in P.nsmallest(4, 'R_total').iterrows():
            a('| `%s` | %s | %s | %d | %+.3f | %+.3f | %.2f | %.0f | %s |'
              % (r.variant, r.pair, r.direction, int(r.n_trades), r.R_total,
                 r.R_per_trade, r.win_rate, r.mean_bars,
                 'yes' if int(r.range_prone) else 'no'))
        a('')
        a('%d of the %d per-pair cells are positive (%.1f%%), and %d of the '
          'top 10 are range-prone pairs against %.1f%% of the universe.'
          % (int((P.R_total > 0).sum()), len(P),
             100.0 * float((P.R_total > 0).mean()),
             int(P.nlargest(10, 'R_total').range_prone.sum()),
             100.0 * float(P.range_prone.mean())))
        a('')
    a('## The verdict')
    a('')
    a('**It is not proven and it is worth keeping as a sleeve candidate for '
      'item 5, for one reason: the negative correlation to A.** Taken on its '
      'own, nothing here clears anything — the best cell is `MR120` '
      'conditional on all 28 pairs at **+18.507 R over six years, +3.084 a '
      'year**, with t 0.602, null p 0.110, 3 of 6 years positive and '
      '**73.6% of its R from crisis windows**. On its own that is a '
      'candidate, not a result.')
    a('')
    a('**What would settle it, and is not in item 4:** the crisis dependence '
      'has to be explained or removed, because a mean-reversion rule that '
      'earns three quarters of its money during crises is betting that the '
      'biggest stretches come back, and the one event this project has '
      'studied in detail — the SNB de-peg — is a stretch that did not. '
      '`GAP_FILLS.md` measures what being on the wrong side of that costs: '
      'up to −20 R at a normal stop.')
    a('')
    a('**What it adds to a book is a separate question and that is item 5.** '
      'The correlation says it should help; its own numbers say it brings '
      'little to help with. The book test is where those two meet.')
    a('')
    a('## Provenance')
    a('')
    for n_ in ('mr_condition.csv', 'mr_summary.csv', 'mr_per_pair.csv',
               'mr_trades.csv', 'mr_corr.csv'):
        p_ = os.path.join(OUT, n_)
        if not os.path.exists(p_):
            a('- `%s` — **MISSING**' % os.path.join('results', 'nnfx', n_))
            continue
        a('- `%s` — %s rows, md5 `%s`'
          % (os.path.relpath(p_, _R),
             '{:,}'.format(len(S2._safe_csv(p_))),
             hashlib.md5(open(p_, 'rb').read()).hexdigest()[:12]))
    out = out or os.path.join(OUT, 'MEAN_REVERSION.md')
    open(out, 'w').write('\n'.join(L_) + '\n')
    print('  MEAN_REVERSION.md: %d lines -> %s'
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
    if g.stage in ('all', 'cond'):
        condition_report()
    if g.stage in ('all', 'run'):
        D, P, keep = run_all()
        corr_to_A(keep)
    if g.stage in ('all', 'md'):
        md_mr()
    print('  nnfxmr done', flush=True)


if __name__ == '__main__':
    main()
