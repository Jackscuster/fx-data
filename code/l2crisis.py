import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""CRISIS SPLIT and CONCENTRATION for gate 2 scorecards.

GAUNTLET.md: rankings and gate 3 verdicts use the CRISIS-EXCLUDED numbers.
Crisis P&L is reported separately, as its own column, because crisis is its own
regime with its own pending routing rules -- its windfalls and its wrecks belong
to that discussion, not to a trend or chop ranking.

WHAT COUNTS AS CRISIS. results/crisis_events.csv, the news-dated calendar --
never price-derived, which is the only thing that makes this non-circular. A
window runs from the event date to +15 days, FORWARD ONLY, exactly as crisis.py
does; a window that opened before the event once produced a false "fires 2.5
days ahead" result that vanished under forward-only testing.

A TRADE IS FLAGGED BY OVERLAP, NOT BY ENTRY DATE. The SNB trade entered
2014-12-29, seventeen days before the unpeg, and made all of its +67 R on
2015-01-15. Flagging on the entry date would file the single largest crisis
windfall in this project under "normal" and defeat the entire purpose.

CURRENCY SCOPING. An event carrying a currency applies to pairs containing it;
an event with no currency is treated as global. A CHF event does not make a
CADJPY trade a crisis trade.

CONCENTRATION. max_trade_share = the largest single trade's R as a share of the
book's total R. A strategy whose best trade is most of its book is one trade,
not a strategy, and the column exists so that is visible without reading a chart.
Reported on the EXCLUDED book, since that is what ranks.

Writes results/gate2_crisis_split_mode<M>.csv.
"""
import json, glob
import numpy as np, pandas as pd

WINDOW = 15


def windows():
    E = pd.read_csv(os.path.join(ROOTOUT, 'crisis_events.csv'))
    E = E[['date', 'ccy', 'severity', 'description']].drop_duplicates('date')
    E['date'] = pd.to_datetime(E.date)
    return [(r.date, r.date + pd.Timedelta(days=WINDOW),
             (r.ccy if isinstance(r.ccy, str) else None), r.description)
            for r in E.itertuples()]


def flag(entry, exit_, pair, wins):
    """True if the holding period overlaps a crisis window for this pair."""
    for a, z, ccy, _ in wins:
        if ccy and ccy not in (pair[:3], pair[3:]):
            continue
        if entry <= z and exit_ >= a:
            return True
    return False


def concentration(rs):
    """Largest single trade's share of total R. Negative totals give a negative
    share, which is meaningful: the worst trade dominating a losing book."""
    rs = np.asarray(rs, float)
    if len(rs) == 0:
        return np.nan
    tot = rs.sum()
    if tot == 0:
        return np.nan
    return float(rs[np.argmax(np.abs(rs))] / tot)


def agg(rs):
    rs = np.asarray(rs, float)
    n = len(rs)
    if n == 0:
        return dict(n=0, total_R=0.0, expectancy_R=np.nan, win_rate=np.nan,
                    profit_factor=np.nan, sharpe=np.nan, sortino=np.nan,
                    max_dd_R=np.nan, ulcer_R=np.nan, calmar=np.nan,
                    max_trade_share=np.nan)
    tot = float(rs.sum()); mean = tot / n
    gp = float(rs[rs > 0].sum()); gl = float(-rs[rs < 0].sum())
    pf = gp / gl if gl > 0 else (np.inf if gp > 0 else 0.0)
    sd = float(rs.std(ddof=1)) if n > 1 else 0.0
    neg = rs[rs < 0]
    dn = float(neg.std(ddof=1)) if len(neg) > 1 else 0.0
    scale = float(np.abs(rs).mean()) or 1.0
    if dn <= 1e-9 * scale:
        dn = 0.0
    eq = np.cumsum(rs); ddv = np.maximum.accumulate(eq) - eq
    dd = float(ddv.max())
    return dict(n=n, total_R=tot, expectancy_R=mean,
                win_rate=float((rs > 0).mean()),
                profit_factor=pf,
                sharpe=(mean / sd * np.sqrt(252)) if sd > 0 else np.nan,
                sortino=(mean / dn * np.sqrt(252)) if dn > 0 else np.nan,
                max_dd_R=dd, ulcer_R=float(np.sqrt(np.mean(ddv ** 2))),
                calmar=(tot / dd) if dd > 0 else np.nan,
                max_trade_share=concentration(rs))


def _worker(args):
    rows, mode = args
    import l2trades as TR, l2sweep as S
    wins = windows()
    out = []
    for cfg in rows:
        code = dict((s, c) for s, _, c in S.SLICES)[cfg['slice']]
        allr, crir, norr = [], [], []
        for p in S.all_pairs():
            try:
                r = TR.run_pair(cfg, p)
            except Exception:
                continue
            d, tr = r['dates'], r['trades']
            if len(tr['r']) == 0:
                continue
            reg = S.regime_codes(p, d)
            wb = {}
            for k, (a, z) in S.WINDOWS.items():
                w = np.flatnonzero((d >= a) & (d <= z))
                if len(w):
                    wb[k] = (int(w[0]), int(w[-1]) + 1)
            for j in range(len(tr['r'])):
                eb, xb = int(tr['entry_bar'][j]), int(tr['exit_bar'][j])
                if xb < 0 or reg[eb] != code:
                    continue
                if not any(wb.get(k) and wb[k][0] <= eb < wb[k][1] for k in ('W2', 'W3')):
                    continue
                R = float(tr['r'][j]); allr.append(R)
                (crir if flag(d[eb], d[xb], p, wins) else norr).append(R)
        rec = dict(c1=cfg['c1'], c2=cfg['c2'], vol=cfg['vol'], base=cfg['base'],
                   exit_ind=cfg['exit_ind'], slice=cfg['slice'], mode=mode)
        for k, v in agg(norr).items():
            rec['ex_' + k] = v          # crisis-EXCLUDED: what ranks
        for k, v in agg(crir).items():
            rec['cr_' + k] = v          # crisis-only: reported, never ranked
        rec['all_total_R'] = float(np.sum(allr))
        rec['crisis_share_of_total_R'] = (float(np.sum(crir)) / rec['all_total_R']
                                          if rec['all_total_R'] else np.nan)
        for k, v in {'risk_' + q: cfg['risk_' + q] for q in
                     ('atr_len', 'atr_mult', 'tp_mult', 'trail_mult',
                      'trail_arm', 'be_pct')}.items():
            rec[k] = v
        out.append(rec)
    return out


def run(rows, mode='B', jobs=1):
    import multiprocessing as mp
    B = max(1, len(rows) // max(1, jobs))
    tasks = [(rows[i:i + B], mode) for i in range(0, len(rows), B)]
    out = []
    if jobs <= 1:
        for t in tasks:
            out.extend(_worker(t))
    else:
        with mp.Pool(jobs) as pool:
            for r in pool.imap_unordered(_worker, tasks):
                out.extend(r)
    return pd.DataFrame(out)
