import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""SUPPRESSED-VOLATILITY EXPOSURE. Report only; kills nothing.

WHY. Position size is risk/(atr_mult x ATR), so when ATR is administratively
held down the size explodes and an ordinary move pays extraordinary R. Strategy
#1's EURCHF trade on 2012-09-04 entered at an ATR of 3.2 BASIS POINTS -- the SNB
floor era -- and one leg paid 11.7 R. That R is arithmetically correct and is
not obviously repeatable, which is exactly the distinction this pass measures.

TWO FLAGS, deliberately different in kind:
  peg   a DOCUMENTED administrative regime, from the calendar below. Dated from
        public policy announcements, never from price -- the same discipline
        events.py follows, and the only thing that keeps this from being
        circular.
  lowvol entry ATR below that PAIR'S OWN 5th percentile. Empirical, relative,
        and catches suppression the calendar does not know about.

They overlap heavily by construction and are reported separately as well as
combined, because a trade can be quiet without being pegged.

DOCUMENTED G8 ADMINISTRATIVE REGIMES. Only regimes with an announced floor,
ceiling or band affecting a G8 pair. The 2008-2015 zero-rate era is NOT here: low
rates are not an administered exchange rate, and including them would flag a
third of the sample on a judgement call rather than a policy.
"""
import json, glob
import numpy as np, pandas as pd
import l2sweep as S

PEGS = [
    # (from, to, currency, what was announced)
    ('2011-09-06', '2015-01-15', 'CHF',
     'SNB EURCHF floor at 1.20, announced 2011-09-06, abandoned 2015-01-15'),
    ('2011-08-04', '2011-09-06', 'CHF',
     'SNB unlimited-liquidity interventions preceding the floor'),
]
LOWVOL_Q = 0.05


def peg_windows():
    return [(pd.Timestamp(a), pd.Timestamp(z), c, d) for a, z, c, d in PEGS]


def in_peg(entry, pair, wins):
    for a, z, ccy, _ in wins:
        if ccy not in (pair[:3], pair[3:]):
            continue
        if a <= entry <= z:
            return True
    return False


def atr_floors(atr_len):
    """The 5th-percentile ATR/price for each pair at this ATR length."""
    import l2lib as L
    out = {}
    for p in S.all_pairs():
        d = S.load_pair(p)
        h, l, c = (d[k].values.astype(float) for k in ('high', 'low', 'close'))
        a = L.P.atr(h, l, c, int(atr_len))
        m = np.isfinite(a) & (c > 0)
        out[p] = float(np.quantile(a[m] / c[m], LOWVOL_Q)) if m.any() else np.nan
    return out


CAP_LEV = 30.0
RISK_FRAC = 0.02
CAP_THR = RISK_FRAC / CAP_LEV      # atr_mult*ATR/price below this and 1:30 binds


def _worker(args):
    rows, = args
    import l2trades as TR, l2lib as L, l2crisis as C
    wins = peg_windows(); cwins = C.windows()
    floors_cache = {}
    out = []
    for cfg in rows:
        alen = int(cfg['risk_atr_len']); amult = float(cfg['risk_atr_mult'])
        if alen not in floors_cache:
            floors_cache[alen] = atr_floors(alen)
        fl = floors_cache[alen]
        code = dict((s, c) for s, _, c in S.SLICES)[cfg['slice']]
        rec = dict(n=0, R=0.0, peg_n=0, peg_R=0.0, lv_n=0, lv_R=0.0,
                   sup_n=0, sup_R=0.0, cap_n=0, cap_R=0.0,
                   cln_n=0, cln_R=0.0)
        for p in S.all_pairs():
            try:
                r = TR.run_pair(cfg, p)
            except Exception:
                continue
            d, tr, c = r['dates'], r['trades'], r['c']
            if len(tr['r']) == 0:
                continue
            atr = L.P.atr(r['h'], r['l'], c, alen)
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
                R = float(tr['r'][j]); rel = atr[eb] / c[eb] if c[eb] else np.nan
                pg = in_peg(d[eb], p, wins)
                lv = np.isfinite(rel) and rel < fl.get(p, np.inf)
                cap = np.isfinite(rel) and (amult * rel) < CAP_THR
                cr = C.flag(d[eb], d[xb], p, cwins)
                rec['n'] += 1; rec['R'] += R
                if pg: rec['peg_n'] += 1; rec['peg_R'] += R
                if lv: rec['lv_n'] += 1; rec['lv_R'] += R
                if pg or lv: rec['sup_n'] += 1; rec['sup_R'] += R
                if cap: rec['cap_n'] += 1; rec['cap_R'] += R
                if not (pg or lv or cr): rec['cln_n'] += 1; rec['cln_R'] += R
        rec.update({k: cfg[k] for k in ('c1', 'c2', 'vol', 'base', 'slice')})
        rec['rank_before'] = cfg.get('rank')
        rec['sup_share'] = rec['sup_R'] / rec['R'] if rec['R'] else np.nan
        out.append(rec)
    return out


def run(rows, jobs=1):
    import multiprocessing as mp
    B = max(1, len(rows) // max(1, jobs))
    tasks = [(rows[i:i + B],) for i in range(0, len(rows), B)]
    out = []
    if jobs <= 1:
        for t in tasks:
            out.extend(_worker(t))
    else:
        with mp.Pool(jobs) as pool:
            for r in pool.imap_unordered(_worker, tasks):
                out.extend(r)
    return pd.DataFrame(out)
