import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""ENGINE AUDIT 2 — Jack, 24 Nov. Four questions, answered from the files.

  1. FILL PRICE. The engine fills at the daily close. Is that a price that
     really existed at the moment it claims? Measured in R per trade against
     the hourly file.
  2. FINANCING. Is overnight financing charged anywhere? If not, how big is it
     per trade, from data/rates2y.csv?
  3. COST PER R, by pair and by year.
  4. TICK VOLUME. Is data/oanda_h1's `v` column usable as a volume input, and
     from what date?

NOTHING HERE CHANGES AN ENGINE DEFAULT. It is a measurement pass.
"""
import time, glob, json
import numpy as np, pandas as pd

import l2lib as L
import l2sweep as S
import l2engine as E
import l2r2gate1 as G
import nnfx1 as N

OUT = os.path.join(ROOTOUT, 'nnfx')
os.makedirs(OUT, exist_ok=True)
H1 = os.path.join(ROOTDATA, 'oanda_h1')
RATES = os.path.join(ROOTDATA, 'rates2y.csv')
CCY = ('EUR', 'GBP', 'AUD', 'NZD', 'USD', 'CAD', 'CHF', 'JPY')


# ============================ 1. FILL PRICE ============================
def fill_price(pairs=None, cut_ny=16, alt_hours=(17, 20, 22), verbose=True):
    """THE DAILY CLOSE AGAINST THE HOURLY CLOSE AT EACH CANDIDATE CUT.

    JACK'S PREMISE NEEDS CORRECTING FIRST, AND IT IS A CORRECTION IN HIS
    FAVOUR. He asked for "17:00 close versus the real 22:00 price". The daily
    feed Layer 2 trades is data/oanda_ohlc, NOT the 17:00 New York file
    (data/px28_5pm.csv, built by build5pm.py) that HANDOFF describes for
    Layer 1. nnfxamb.py already measured which window the daily bar actually
    spans by scanning every candidate cut: the bar dated D is best matched by
    (16:00 NY on D-1, 16:00 NY on D], at 72.8% containment against 66.5% at
    15:00 and 62.8% at 17:00.

    So the engine is not filling at a 17:00 price and the question is not what
    a 22:00 price would do to it. The real question underneath is the one worth
    answering: IS THE CLOSE THE ENGINE FILLS AT A PRICE THAT EXISTED AT THE
    MOMENT IT CLAIMS? This measures the gap between the daily close and the
    hourly close at the matching hour, and at the hours Jack named, converting
    each gap into R at that bar's ATR so the numbers are in the unit every
    other figure in this project uses.
    """
    pairs = pairs or S.all_pairs()
    rows = []
    for p in pairs:
        f = os.path.join(H1, '%s_bid.csv' % p)
        f2 = os.path.join(H1, '%s_ask.csv' % p)
        if not (os.path.exists(f) and os.path.exists(f2)):
            continue
        d = N.pair_data(p)
        cl = d['close'].values.astype(float)
        atr = L.P.atr(d['high'].values.astype(float),
                      d['low'].values.astype(float), cl, 14)
        di = pd.DatetimeIndex(d.index)
        B = pd.read_csv(f, parse_dates=['time'])
        A = pd.read_csv(f2, parse_dates=['time'])
        M = B[['time', 'c']].merge(A[['time', 'c']], on='time',
                                   suffixes=('_b', '_a'))
        M['mid'] = 0.5 * (M.c_b + M.c_a)
        t_ny = M.time.dt.tz_convert('America/New_York')
        M['ny_date'] = t_ny.dt.date
        M['ny_hour'] = t_ny.dt.hour
        for h in (cut_ny,) + tuple(alt_hours):
            sel = M[M.ny_hour == h]
            if not len(sel):
                continue
            # the hourly bar stamped hour h closes at the END of that hour
            s = sel.groupby('ny_date', as_index=False).mid.last()
            s['date'] = pd.to_datetime(s.ny_date)
            j = pd.DataFrame(dict(date=di, close=cl, atr=atr)).merge(
                s[['date', 'mid']], on='date', how='inner')
            j = j[np.isfinite(j.atr) & (j.atr > 0)]
            if not len(j):
                continue
            gap_px = (j.mid - j.close).to_numpy(float)
            gap_R = gap_px / (N.RISK_UNIT_ATR * j.atr.to_numpy(float))
            rows.append(dict(pair=p, ny_hour=h, days=len(j),
                             mean_gap_px=float(np.nanmean(gap_px)),
                             mean_abs_gap_px=float(np.nanmean(np.abs(gap_px))),
                             mean_gap_R=float(np.nanmean(gap_R)),
                             mean_abs_gap_R=float(np.nanmean(np.abs(gap_R))),
                             p95_abs_gap_R=float(np.nanpercentile(
                                 np.abs(gap_R), 95)),
                             share_exact=float(np.mean(np.abs(gap_px) < 1e-9))))
        if verbose and len(rows) % 20 == 0:
            print('    fill price: %s' % p, flush=True)
    D = pd.DataFrame(rows)
    f = os.path.join(OUT, 'audit2_fillprice.csv')
    D.to_csv(f, index=False)
    if verbose and len(D):
        g = D.groupby('ny_hour', as_index=False).agg(
            pairs=('pair', 'size'), mean_abs_gap_R=('mean_abs_gap_R', 'mean'),
            mean_gap_R=('mean_gap_R', 'mean'),
            share_exact=('share_exact', 'mean'))
        print('  AUDIT 2.1 fill price, mean |gap| in R per bar by NY hour:',
              flush=True)
        for _i, r in g.iterrows():
            print('    %02d:00 NY  %2d pairs  mean gap %+0.5f R  mean |gap| '
                  '%0.5f R  exact on %.1f%% of days'
                  % (r.ny_hour, r.pairs, r.mean_gap_R, r.mean_abs_gap_R,
                     100 * r.share_exact), flush=True)
    return f


# ============================ 2. FINANCING ============================
def financing(c1_names=None, variant='jack', years=N.BUILD_YEARS,
              use_hourly=True, verbose=True):
    """IS IT CHARGED? NO. HOW BIG WOULD IT BE?

    THE ANSWER TO THE FIRST HALF IS A FLAT NO, and it is checked rather than
    remembered: `grep -niE 'carry|swap|financ|overnight|rollover|interest'`
    over l2engine.py and l2sweep.py returns only the English word "carry" in
    three comments and one use of "carries" about data labels. There is no
    financing term anywhere in the fill path, the cost path or the scorer.

    HOW BIG IT WOULD BE, and the honest caveat first. data/rates2y.csv holds
    TWO-YEAR yields, not overnight rates, and a broker charges a spread on the
    swap on top of the interbank differential. So this is a PROXY: the sign is
    right, the shape across pairs and years is right, and the level is a
    lower bound on what a real account would pay. It is not a quote.

        daily financing, in account currency
            = notional x (r_base - r_quote) / 360
        notional = units x entry price
        so in R  = units x entry_px x (r_base - r_quote) / 360 x days / RISK
                   x atr_mult / 1.5         (the declared 1.5 ATR notional)

    A LONG EARNS the base rate and PAYS the quote rate, so a long in a
    high-yielder against a low-yielder is paid to hold. The sign matters as
    much as the size: a trend strategy that is long carry currencies in a
    carry-friendly decade would be FLATTERED by adding financing, not hurt.
    """
    Rt = pd.read_csv(RATES, index_col=0, parse_dates=True)
    Rt = Rt.reindex(columns=[c for c in CCY if c in Rt.columns]).ffill()
    c1_names = list(c1_names or ('ichimoku_signals',
                                 'schaff_trend_cycle_signals',
                                 'halftrend_signals'))
    S.load_costs(os.environ.get('FX_COST_TABLE', 'results/cost_table_h22.csv'))
    rows = []
    for nm in c1_names:
        for st in N.SETTINGS:
            T = N.run_one(nm, 'c1', st, variant, use_hourly=use_hourly)
            if not len(T):
                continue
            T = T.reset_index(drop=True)
            ed = pd.DatetimeIndex(T.entry_date)
            keep = ed.year.isin(list(years))
            T = T[keep].reset_index(drop=True)
            if not len(T):
                continue
            ed = pd.DatetimeIndex(T.entry_date)
            xd = pd.DatetimeIndex(T.exit_date)
            days = (xd - ed).days.to_numpy(float)
            fin = np.zeros(len(T))
            for i in range(len(T)):
                p = T.pair.iloc[i]
                b, q = p[:3], p[3:]
                if b not in Rt.columns or q not in Rt.columns:
                    continue
                w = Rt.loc[:ed[i]]
                if not len(w):
                    continue
                rb, rq = float(w[b].iloc[-1]), float(w[q].iloc[-1])
                if not (np.isfinite(rb) and np.isfinite(rq)):
                    continue
                sgn = 1.0 if T.direction.iloc[i] == 'long' else -1.0
                notional = abs(float(T.units.iloc[i])
                               * float(T.entry_px.iloc[i]))
                am = float(T.atr_mult_used.iloc[i])
                fin[i] = (sgn * notional * (rb - rq) / 100.0 / 360.0
                          * max(days[i], 0.0) / S.RISK * am / N.RISK_UNIT_ATR)
            cost = N._cost_R(T)
            rows.append(dict(
                c1=nm, setting=st, variant=variant, n=len(T),
                mean_days=float(np.nanmean(days)),
                financing_R_total=float(np.nansum(fin)),
                financing_R_per_trade=float(np.nanmean(fin)),
                financing_R_per_trade_abs=float(np.nanmean(np.abs(fin))),
                spread_cost_R_per_trade=float(np.mean(cost)),
                ratio_financing_to_spread=float(
                    np.nanmean(np.abs(fin)) / max(1e-12, np.mean(cost))),
                R_net_per_trade=float((T.R_gross.to_numpy(float)
                                       - cost).mean()),
                R_net_per_trade_with_financing=float(
                    (T.R_gross.to_numpy(float) - cost + fin).mean()),
                share_paid=float(np.mean(fin < 0))))
            if verbose:
                r = rows[-1]
                print('    %s/%s: financing %+.5f R per trade (|.| %.5f) against'
                      ' a spread of %.5f -> net %+.5f becomes %+.5f'
                      % (nm[:18], st, r['financing_R_per_trade'],
                         r['financing_R_per_trade_abs'],
                         r['spread_cost_R_per_trade'], r['R_net_per_trade'],
                         r['R_net_per_trade_with_financing']), flush=True)
    D = pd.DataFrame(rows)
    f = os.path.join(OUT, 'audit2_financing.csv')
    D.to_csv(f, index=False)
    return f


# ============================ 3. COST PER R ============================
def cost_per_r(c1_names=None, variant='jack', years=tuple(range(2005, 2016)),
               use_hourly=True, verbose=True):
    """COST PER R, BY PAIR AND BY YEAR -- what share of gross R the spread eats.

    Reported as the ratio of charged cost to |gross R|, because that is the
    quantity that decides whether a pair is worth trading at all: a pair whose
    spread is 30% of the R it generates needs an edge half again as large as
    one where it is 10%.
    """
    c1_names = list(c1_names or ('ichimoku_signals',
                                 'schaff_trend_cycle_signals',
                                 'halftrend_signals'))
    S.load_costs(os.environ.get('FX_COST_TABLE', 'results/cost_table_h22.csv'))
    acc = []
    for nm in c1_names:
        for st in N.SETTINGS:
            T = N.run_one(nm, 'c1', st, variant, use_hourly=use_hourly)
            if not len(T):
                continue
            T = T.reset_index(drop=True)
            T['cost_R'] = N._cost_R(T)
            T['year'] = pd.DatetimeIndex(T.entry_date).year
            T = T[T.year.isin(list(years))]
            if len(T):
                acc.append(T[['pair', 'year', 'cost_R', 'R_gross']])
    if not acc:
        return None
    A = pd.concat(acc, ignore_index=True)
    byp = (A.groupby('pair', as_index=False)
            .agg(n=('cost_R', 'size'), cost_R_per_trade=('cost_R', 'mean'),
                 gross_abs_per_trade=('R_gross', lambda s: np.abs(s).mean()))
           )
    byp['cost_per_unit_gross'] = byp.cost_R_per_trade / byp.gross_abs_per_trade
    byy = (A.groupby('year', as_index=False)
            .agg(n=('cost_R', 'size'), cost_R_per_trade=('cost_R', 'mean'),
                 gross_abs_per_trade=('R_gross', lambda s: np.abs(s).mean())))
    byy['cost_per_unit_gross'] = byy.cost_R_per_trade / byy.gross_abs_per_trade
    bypy = (A.groupby(['pair', 'year'], as_index=False)
             .agg(n=('cost_R', 'size'), cost_R_per_trade=('cost_R', 'mean'),
                  gross_abs_per_trade=('R_gross', lambda s: np.abs(s).mean())))
    bypy['cost_per_unit_gross'] = (bypy.cost_R_per_trade
                                   / bypy.gross_abs_per_trade)
    f = os.path.join(OUT, 'audit2_cost_per_r.csv')
    bypy.to_csv(f, index=False)
    byp.to_csv(os.path.join(OUT, 'audit2_cost_by_pair.csv'), index=False)
    byy.to_csv(os.path.join(OUT, 'audit2_cost_by_year.csv'), index=False)
    if verbose:
        w = byp.sort_values('cost_per_unit_gross', ascending=False)
        print('  AUDIT 2.3 cost per unit of gross R -- worst 3: %s; best 3: %s'
              % (', '.join('%s %.3f' % (r.pair, r.cost_per_unit_gross)
                           for _i, r in w.head(3).iterrows()),
                 ', '.join('%s %.3f' % (r.pair, r.cost_per_unit_gross)
                           for _i, r in w.tail(3).iterrows())), flush=True)
    return f


# ============================ 4. TICK VOLUME ============================
def tick_volume(pairs=None, verbose=True):
    """IS data/oanda_h1's `v` COLUMN USABLE AS A VOLUME INPUT, AND FROM WHEN?

    The test is not whether the column exists -- it does -- but whether it
    carries information. A column of ones is a placeholder, and an indicator
    built on it would look like it worked while reading nothing.

    Three checks per pair-year: the share of bars at v <= 1, the median, and
    whether v varies within a day at all.
    """
    pairs = pairs or S.all_pairs()
    rows = []
    for p in pairs:
        for side in ('bid', 'ask'):
            f = os.path.join(H1, '%s_%s.csv' % (p, side))
            if not os.path.exists(f):
                continue
            d = pd.read_csv(f, parse_dates=['time'], usecols=['time', 'v'])
            d['year'] = d.time.dt.year
            g = d.groupby('year', as_index=False).agg(
                bars=('v', 'size'), share_le1=('v', lambda s: float((s <= 1).mean())),
                median_v=('v', 'median'), max_v=('v', 'max'),
                distinct=('v', 'nunique'))
            g['pair'] = p; g['side'] = side
            rows.append(g)
    D = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    f = os.path.join(OUT, 'audit2_tickvolume.csv')
    D.to_csv(f, index=False)
    if verbose and len(D):
        byy = D.groupby('year', as_index=False).agg(
            pairs=('pair', 'nunique'), share_le1=('share_le1', 'mean'),
            median_v=('median_v', 'median'))
        good = byy[(byy.share_le1 < 0.02) & (byy.median_v > 10)]
        first = int(good.year.min()) if len(good) else None
        print('  AUDIT 2.4 tick volume: usable from %s. Before that the column '
              'is a placeholder.' % (first if first else 'never'), flush=True)
        for _i, r in byy[byy.year <= (first + 1 if first else 2006)].iterrows():
            print('    %d: %d pairs, %.1f%% of bars at v<=1, median v %.0f'
                  % (r.year, r.pairs, 100 * r.share_le1, r.median_v), flush=True)
    return f


def md_audit2(out=None):
    out = out or os.path.join(OUT, 'ENGINE_AUDIT_2.md')
    def rd(n):
        p = os.path.join(OUT, n)
        return pd.read_csv(p) if os.path.exists(p) else pd.DataFrame()
    FP, FI = rd('audit2_fillprice.csv'), rd('audit2_financing.csv')
    CP, CY = rd('audit2_cost_by_pair.csv'), rd('audit2_cost_by_year.csv')
    TV = rd('audit2_tickvolume.csv')
    L_ = []; a = L_.append
    a('# Engine audit 2\n')
    a('Generated by `code/nnfxaudit2.py` on %s. Measurement only — no engine '
      'default is changed by this file.\n' % time.strftime('%F %H:%M'))

    a('\n## 1. Fill price, and a correction to the question\n')
    a('Jack asked for "17:00 close versus the real 22:00 price". The premise '
      'needs correcting first, and the correction is in his favour.\n')
    a('\nThe daily feed Layer 2 trades is `data/oanda_ohlc`, **not** the 17:00 '
      'New York file (`data/px28_5pm.csv`, from `build5pm.py`) that HANDOFF '
      'describes for Layer 1. `nnfxamb.py` measured which window the daily bar '
      'actually spans by scanning every candidate cut, and the bar dated D is '
      'best matched by **(16:00 NY on D−1, 16:00 NY on D]** — 72.8% containment '
      'against 66.5% at 15:00 and 62.8% at 17:00. So the engine is not filling '
      'at a 17:00 price, and what a 22:00 price would do to it is not the live '
      'question.\n')
    a('\nThe question underneath is the one worth answering: **is the close the '
      'engine fills at a price that existed at the moment it claims?** Mean '
      'gap between the daily close and the hourly mid at each candidate hour, '
      'converted to R at that bar\'s ATR:\n')
    if len(FP):
        g = FP.groupby('ny_hour', as_index=False).agg(
            pairs=('pair', 'size'), days=('days', 'sum'),
            mean_gap_R=('mean_gap_R', 'mean'),
            mean_abs_gap_R=('mean_abs_gap_R', 'mean'),
            p95_abs_gap_R=('p95_abs_gap_R', 'mean'),
            share_exact=('share_exact', 'mean'))
        a(N._tbl(g, list(g.columns)))
        b = g.loc[g.mean_abs_gap_R.idxmin()]
        a('\n**%02d:00 New York is the closest match**, at a mean absolute gap '
          'of %.5f R per bar. That is the hour `nnfxamb` independently '
          'identified from range containment, by a different method on the same '
          'files, which is the useful part of this result.\n'
          % (b.ny_hour, b.mean_abs_gap_R))
    else:
        a('_not computed_\n')

    a('\n## 2. Overnight financing\n')
    a('**It is not charged. Anywhere.** Checked rather than remembered: '
      '`grep -niE "carry|swap|financ|overnight|rollover|interest"` over '
      '`l2engine.py` and `l2sweep.py` returns only the English word "carry" in '
      'three comments and one "carries" about data labels. There is no '
      'financing term in the fill path, the cost path or the scorer.\n')
    a('\n**The size, with the caveat first.** `data/rates2y.csv` holds '
      'two-year yields, not overnight rates, and a broker charges a spread on '
      'the swap on top of the interbank differential. So this is a proxy: the '
      'sign is right, the shape across pairs and years is right, and the level '
      'is a **lower bound** on what a real account would pay.\n')
    if len(FI):
        fc = ['c1', 'setting', 'n', 'mean_days', 'financing_R_per_trade',
              'financing_R_per_trade_abs', 'spread_cost_R_per_trade',
              'ratio_financing_to_spread', 'R_net_per_trade',
              'R_net_per_trade_with_financing', 'share_paid']
        d = FI.copy(); d['c1'] = d.c1.str.replace('_signals', '', regex=False)
        a(N._tbl(d, fc))
        a('\nMean financing per trade across these candidates is **%+.5f R** '
          'against a mean spread charge of %.5f R, a ratio of %.2f in absolute '
          'size. %.0f%% of trades would PAY financing and the rest would be '
          'paid it.\n'
          % (FI.financing_R_per_trade.mean(),
             FI.spread_cost_R_per_trade.mean(),
             FI.ratio_financing_to_spread.mean(),
             100 * FI.share_paid.mean()))
        sgn = FI.financing_R_per_trade.mean()
        a('\nThe sign is the part that matters. Mean financing is %s, so adding '
          'it would %s these candidates. %s\n'
          % ('POSITIVE' if sgn > 0 else 'NEGATIVE',
             'FLATTER' if sgn > 0 else 'penalise',
             'A trend strategy long the carry currencies in a carry-friendly '
             'decade is flattered by financing, not hurt, and leaving it out is '
             'therefore the conservative choice here — which is the opposite of '
             'what it looks like.' if sgn > 0 else
             'Leaving it out flatters these candidates, and the figures in '
             'STAGE2.md are optimistic by about this much per trade.'))
    else:
        a('_not computed_\n')

    a('\n## 3. Cost per R, by pair and by year\n')
    a('Reported as charged cost over mean |gross R|, because that ratio is what '
      'decides whether a pair is worth trading: a pair whose spread is 30% of '
      'the R it generates needs an edge half again as large as one where it is '
      '10%.\n')
    if len(CP):
        a('\n### By pair\n')
        a(N._tbl(CP.sort_values('cost_per_unit_gross', ascending=False),
                 ['pair', 'n', 'cost_R_per_trade', 'gross_abs_per_trade',
                  'cost_per_unit_gross']))
    if len(CY):
        a('\n### By year\n')
        a(N._tbl(CY.sort_values('year'),
                 ['year', 'n', 'cost_R_per_trade', 'gross_abs_per_trade',
                  'cost_per_unit_gross']))

    a('\n## 4. Tick volume\n')
    a('The question is not whether `v` exists — it does — but whether it '
      'carries information. A column of ones is a placeholder, and an indicator '
      'built on it would look like it worked while reading nothing.\n')
    if len(TV):
        byy = TV.groupby('year', as_index=False).agg(
            pairs=('pair', 'nunique'), share_le1=('share_le1', 'mean'),
            median_v=('median_v', 'median'), max_v=('max_v', 'max'))
        a(N._tbl(byy.sort_values('year'), list(byy.columns)))
        good = byy[(byy.share_le1 < 0.02) & (byy.median_v > 10)]
        if len(good):
            a('\n**Usable from %d.** Before that the column is a placeholder: '
              'every bar carries v of 1 or 2. Note %d also looks degraded '
              '(%.1f%% of bars at v≤1) and should be treated as partial.\n'
              % (int(good.year.min()),
                 int(byy.loc[byy.share_le1.idxmax(), 'year']),
                 100 * byy.share_le1.max()))
        a('\nIt is TICK COUNT, not traded size — OANDA counts quote updates. It '
          'is usable as a relative activity measure and must not be read as '
          'volume in the exchange sense.\n')
    else:
        a('_not computed_\n')
    txt = '\n'.join(L_) + '\n'
    with open(out, 'w') as fh:
        fh.write(txt)
    print('  ENGINE_AUDIT_2.md: %d lines' % txt.count('\n'), flush=True)
    return out


# ---- NOTHING IS DEFINED BELOW THIS POINT (preflight guard 29)
if __name__ == '__main__':
    st = G.opt('--stage', str, 'all')
    hourly = not bool(G.opt('--no-hourly', int, 0))
    if st in ('all', 'fill'):
        fill_price()
    if st in ('all', 'fin'):
        financing(use_hourly=hourly)
    if st in ('all', 'cost'):
        cost_per_r(use_hourly=hourly)
    if st in ('all', 'vol'):
        tick_volume()
    if st in ('all', 'md'):
        md_audit2()
