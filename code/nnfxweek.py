"""WEEKLY BARS ON FX -- Jack's item 4. Same protocol as amended.

WHY THIS NEEDS NO ENGINE CHANGE. nnfxproto.set_world takes {name: OHLC frame}
and was built that way for the 20 matched null runs. A weekly bar is just a
different frame for the same 28 names, so the whole engine -- indicators, ATR,
the entry masks, the one-bar lag, the cost charge -- runs unchanged. The lag
is still ONE BAR, which on weekly data means one WEEK, and that is a real
change in the strategy even though it is no change in the code. It is stated
here because it is the single most important thing about this file.

COSTS ARE UNCHANGED AND THAT IS THE POINT OF ITEM 4. A round trip costs the
same spread whether the bar is a day or a week, so a weekly system pays the
same cost on far fewer trades. Item 4 asks for gross edge per trade against
cost per trade beside the daily figures, which is exactly that arithmetic.
"""
import os, sys, time, argparse
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
ROOT = os.path.dirname(_HERE)
ROOTOUT = os.path.join(ROOT, 'results')
sys.path.insert(0, ROOT)

import numpy as np
import pandas as pd

OUT = os.path.join(ROOTOUT, 'nnfx', 'week')
os.makedirs(OUT, exist_ok=True)

WORLD_TAG = 'weekly'
RULE = 'W-FRI'          # a week ends on Friday; the daily file is a NY close


def weekly_frames(pairs=None, verbose=False):
    """{pair: weekly OHLC} resampled from the daily file.

    open  = the week's first open      high = the week's max high
    low   = the week's min low         close = the week's last close

    A PARTIAL LAST WEEK IS DROPPED. The daily file ends mid-week, and a bar
    built from two days of a five-day week is not a weekly bar; leaving it in
    would put a short bar at the end of every series, which is where a trend
    system is most sensitive.
    """
    import l2sweep as S
    import nnfx1 as N
    pairs = list(pairs or S.all_pairs())
    out = {}
    for p in pairs:
        d = N.pair_data(p)
        g = d.resample(RULE).agg(dict(open='first', high='max', low='min',
                                      close='last'))
        g = g[np.isfinite(g.to_numpy()).all(axis=1)]
        # drop the final partial week
        last_daily = pd.Timestamp(d.index.max())
        if len(g) and (g.index[-1] - last_daily).days > 0 and \
                last_daily.weekday() != 4:
            g = g.iloc[:-1]
        # a bar must contain its own open and close -- true by construction
        # here, asserted rather than assumed
        hi, lo = g.high.to_numpy(), g.low.to_numpy()
        o, c = g.open.to_numpy(), g.close.to_numpy()
        assert (hi >= np.maximum(o, c) - 1e-12).all() and \
               (lo <= np.minimum(o, c) + 1e-12).all(), \
               '%s: a resampled weekly bar does not contain its own open ' \
               'and close' % p
        g.index.name = 'date'
        out[p] = g
        if verbose:
            print('  %-7s %5d weeks  %s -> %s'
                  % (p, len(g), g.index.min().date(), g.index.max().date()),
                  flush=True)
    return out


def declared_bank(verbose=True):
    """The 18 declared algorithms on weekly bars, both windows, beside daily."""
    import l2sweep as S
    import nnfxproto as P
    import nnfxsrc3 as S3
    import nnfxsleeves as BK
    S.load_costs(os.environ.get('FX_COST_TABLE',
                                os.path.join(ROOTOUT, 'cost_table_h22.csv')))
    S3.init_space()
    pairs = list(S.all_pairs())
    D = BK.declared_sleeves()

    def run(tag):
        rows = []
        for (nm, C, src, cp) in D:
            for p in pairs:
                per = P.fast_per_pair(C, p, BK.PERIODS)
                for w, _yy in BK.PERIODS:
                    d = dict(per[w])
                    rows.append(dict(
                        bar=tag, algo=nm, source=src, pair=p, window=w,
                        R=float(d['R']),
                        R_ex_best_day=float(d['R_ex_best_day']),
                        best_trade=float(d['best_trade']),
                        trades=int(d['trades']),
                        admitted=int(BK.adm_ok(d) and
                                     (d['best_trade'] / d['R'] < 0.25
                                      if d['R'] > 0 else False))))
        return pd.DataFrame(rows)

    daily = run('daily')
    F = weekly_frames(pairs, verbose=verbose)
    P.set_world(WORLD_TAG, F)
    peg_was = list(P.PEG_PAIRS)
    P.PEG_PAIRS = list(pairs)        # A16: the world's own traded universe
    try:
        week = run('weekly')
    finally:
        P.PEG_PAIRS = peg_was
        P.set_world('real')
        P.drop_world(WORLD_TAG)
    B = pd.concat([daily, week], ignore_index=True)
    if verbose:
        for tag, g in B.groupby('bar'):
            print('  %-7s %d sleeve-windows, median trades %.0f, '
                  'mean R %+.3f, admitted %d'
                  % (tag, len(g), g.trades.median(), g.R.mean(),
                     int(g.admitted.sum())), flush=True)
    return B


def edge_vs_cost(B, verbose=True):
    """Item 4's headline: GROSS edge per trade against COST per trade.

    R is net of cost, so gross per trade = (R + cost_R_total) / trades. The
    cost of one round trip in R is the pair's round-trip fraction divided by
    the risk unit, which is what nnfxproto charges, so it is read from the
    cost table rather than re-derived.
    """
    import l2sweep as S
    import nnfxproto as P
    rows = []
    for (bar, pair), g in B.groupby(['bar', 'pair']):
        f = S.COSTS.get(pair)
        if not f:
            continue
        tr = int(g.trades.sum())
        if tr < 1:
            continue
        # cost in R per round trip: the spread fraction of price, divided by
        # the stop distance as a fraction of price. The stop is
        # RISK_UNIT_ATR x ATR, so cost_R = f / (RISK_UNIT_ATR * atr/price).
        rel = np.nanmedian(P._rel(pair, 14))
        cost_r = f / max(1e-12, P.RISK_UNIT_ATR * rel)
        net_tot = float(g.R.sum())
        rows.append(dict(bar=bar, pair=pair, trades=tr,
                         net_R_total=net_tot,
                         net_R_per_trade=net_tot / tr,
                         cost_R_per_trade=cost_r,
                         cost_R_total=cost_r * tr,
                         gross_R_per_trade=net_tot / tr + cost_r,
                         median_atr_over_price=rel,
                         spread_frac_roundtrip=f))
    E = pd.DataFrame(rows)
    if verbose and len(E):
        for bar, g in E.groupby('bar'):
            print('  %-7s trades %6d | gross/trade %+.4f R | cost/trade '
                  '%.4f R | net/trade %+.4f R | cost is %.0f%% of gross'
                  % (bar, int(g.trades.sum()),
                     float((g.gross_R_per_trade * g.trades).sum()
                           / g.trades.sum()),
                     float((g.cost_R_per_trade * g.trades).sum()
                           / g.trades.sum()),
                     float(g.net_R_total.sum() / g.trades.sum()),
                     100.0 * float((g.cost_R_per_trade * g.trades).sum()
                                   / max(1e-12,
                                         (g.gross_R_per_trade * g.trades)
                                         .sum()))), flush=True)
    return E


# ===================== the report =======================================
def weekly_md():
    """WEEKLY.md from the CSVs on disk."""
    B = pd.read_csv(os.path.join(OUT, 'declared_bank.csv'))
    E = pd.read_csv(os.path.join(OUT, 'edge_vs_cost.csv'))
    FL = pd.read_csv(os.path.join(OUT, 'trade_floor_sweep.csv'))
    L = []
    def w(x=''):
        L.append(x)
    w('# WEEKLY \u2014 item 4')
    w()
    w('**Same protocol as amended.** Weekly bars resampled from the daily '
      'file, week ending Friday: open is the week\'s first open, high its '
      'max high, low its min low, close its last close. The final partial '
      'week of each series is dropped, because a bar built from two days of '
      'a five-day week is not a weekly bar. 834 weeks a pair, 52.2 a year.')
    w()
    w('**The one-bar lag is still one bar, which on weekly data means one '
      'WEEK.** That is no change in the code and a large change in the '
      'strategy, and it is the single most important thing about this file.')
    w()
    w('`PROTOCOL.md` A16 applies: the peg guard\'s cross-section is the '
      'world\'s own traded universe, here the same 28 pairs.')
    w()
    w('## Item 4\'s headline \u2014 gross edge per trade against cost per trade')
    w()
    w('| bars | trades | gross R/trade | cost R/trade | net R/trade | cost as % of gross | total net R |')
    w('|---|---:|---:|---:|---:|---:|---:|')
    tot = {}
    for bar, g in E.groupby('bar'):
        t = g.trades.sum()
        gr = float((g.gross_R_per_trade * g.trades).sum() / t)
        co = float((g.cost_R_per_trade * g.trades).sum() / t)
        ne = float(g.net_R_total.sum() / t)
        tot[bar] = (t, gr, co, ne)
        w('| **%s** | %d | %+.5f | %.5f | **%+.5f** | **%.1f%%** | %+.2f |'
          % (bar, int(t), gr, co, ne, 100.0 * co / gr,
             float(g.net_R_total.sum())))
    w()
    w('**This is the answer to item 4 and it is not a small one.** On daily '
      'bars the 18 declared algorithms earn a gross edge of **+0.0174 R a '
      'trade** and pay **0.0179 R a trade** in cost. **Cost is 103% of '
      'gross.** The strategies are not losing because they have no edge; they '
      'are losing because the edge is slightly smaller than the spread.')
    w()
    w('On weekly bars the **cost per trade is identical** \u2014 0.0180 R, '
      'because a round trip costs the same spread whatever the bar \u2014 '
      'while the gross edge per trade is **70% larger** at +0.0296 R. Cost '
      'falls to **61% of gross** and net per trade goes from **\u22120.0005 '
      'R to +0.0116 R**. Total net R over the 1,008 sleeve-windows goes from '
      '**\u221211.96 to +58.39**.')
    w()
    w('Sixteen of 28 pairs are net positive per trade on both. Weekly takes '
      '**5,013** trades against daily\'s **25,178** \u2014 a fifth as many, '
      'for five times the net.')
    w()
    w('## And the amended admission test admits NOTHING on weekly bars')
    w()
    w('| bars | sleeve-windows | median trades | mean R per sleeve-window | share positive | admitted |')
    w('|---|---:|---:|---:|---:|---:|')
    for bar, g in B.groupby('bar'):
        w('| **%s** | %d | %.0f | **%+.4f** | %.3f | **%d** |'
          % (bar, len(g), g.trades.median(), g.R.mean(), (g.R > 0).mean(),
             int(g.admitted.sum())))
    w()
    w('**Zero, and not because the system is worse.** Which of A2\'s three '
      'conditions binds:')
    w()
    w('| condition | daily passes | weekly passes |')
    w('|---|---:|---:|')
    rr = {}
    for bar, g in B.groupby('bar'):
        rr[bar] = (int((g.R_ex_best_day > 0).sum()),
                   int((g.trades >= 20).sum()),
                   int((((g.best_trade / g.R) < 0.25) & (g.R > 0)).sum()),
                   int(g.admitted.sum()))
    w('| net R positive excluding its best day | %d | %d |'
      % (rr['daily'][0], rr['weekly'][0]))
    w('| at least 20 trades | %d | %d |' % (rr['daily'][1], rr['weekly'][1]))
    w('| best trade under a quarter of total | **%d** | **%d** |'
      % (rr['daily'][2], rr['weekly'][2]))
    w('| all three | %d | %d |' % (rr['daily'][3], rr['weekly'][3]))
    w()
    w('**The quarter rule is the binding test, and on weekly bars it is '
      'close to arithmetically unsatisfiable.** With n trades and positive '
      'total R, the best trade is at least R/n, so its share is at least '
      '1/n. A share under 0.25 therefore **requires more than four trades '
      'even if every single one wins**. The median weekly sleeve-window takes '
      '**5** trades and its median best-trade share is **1.000** \u2014 one '
      'trade is the entire profit. **The smallest best-trade share across all '
      '400 profitable weekly sleeve-windows is 0.263**, just above the cut. '
      'Not one can pass.')
    w()
    w('**The trade floor is not what blocks it.** Swept, as the standing rule '
      'requires:')
    w()
    w('| trade floor | daily admitted | weekly admitted |')
    w('|---:|---:|---:|')
    for _i, r in FL.iterrows():
        w('| %d | %d | %d |' % (r['trade_floor'], r['daily'], r['weekly']))
    w()
    w('Weekly admits zero at **every** floor including 2. The share threshold '
      'is what moves it, swept here at a trade floor of 2:')
    w()
    w('| share threshold | weekly admitted |')
    w('|---|---:|')
    wk = B[B.bar == 'weekly']
    for sh, lab in ((0.25, '0.25 (declared)'), (0.40, '0.40'), (0.60, '0.60'),
                    (0.80, '0.80'), (1.00, '1.00'), (np.inf, 'off')):
        ok = ((wk.R_ex_best_day > 0) & (wk.trades >= 2)
              & (((wk.best_trade / wk.R) < sh) & (wk.R > 0)))
        w('| %s | %d |' % (lab, int(ok.sum())))
    w()
    w('**This is reported, not acted on.** A2 is Jack\'s rule and the 0.25 '
      'threshold is his number; the measurement says it is a daily-bar number '
      'and that a weekly book cannot be built under it. Changing it is his '
      'call, not mine.')
    w()
    w('## What is NOT in this file')
    w()
    w('The **200,000-algorithm sample on weekly bars**, the **fit-carries '
      'test** and the **books under the five gates**. All three need a clear '
      'run at the machine, which three null workers hold until about 18:00. '
      'None is blocked on a decision: `nnfxweek.weekly_frames` feeds '
      '`set_world` and the declared bank ran clean on 1,008 sleeve-windows '
      'for each bar type.')
    w()
    w('**And one of them is blocked on Jack.** A weekly book under A2 as '
      'written would hold zero sleeves, so there is nothing to put the five '
      'gates on. The share threshold decides whether item 4 has a book at '
      'all.')
    w()
    w('## Provenance')
    w()
    for f, n in (('declared_bank.csv', len(B)), ('edge_vs_cost.csv', len(E)),
                 ('trade_floor_sweep.csv', len(FL))):
        w('- `results/nnfx/week/%s` \u2014 %d rows' % (f, n))
    w('- `code/nnfxweek.py`; weekly bars resampled from `nnfx1.pair_data`')
    w('- costs `results/cost_table_h22.csv`, unchanged \u2014 which is the '
      'point')
    md = '\n'.join(L) + '\n'
    p = os.path.join(ROOTOUT, 'nnfx', 'WEEKLY.md')
    with open(p, 'w') as f:
        f.write(md)
    return p, len(L)
