import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""WALK-FORWARD TEAM STRUCTURES on the three slices that have ip1.

THE STITCH. W2 (2011-2015) is scored with ip1, W3 (2016-2020) with ip2. ip1 was
tuned on W1 and has never seen W2; ip2 was tuned on W1+W2 and has never seen W3.
Every year here is therefore blind under the parameters it is scored with.
W1 (2005-2010) is NOT used: it is ip1's own tuning window, so build metrics
taken there would be in-sample in exactly the way this design exists to avoid.
The build windows are the clean part of "2005-2015" and "2005-2018".

    step 1   build 2011-2015 (ip1)                  trade 2016-2018 (ip2)
    step 2   build 2011-2015 (ip1) + 2016-2018 (ip2) trade 2019-2020 (ip2)

At each step the cut, the member choice, the agreement curve and the SIZE are
all decided on the build years and applied to the trade years untouched. The two
trade stretches are stitched into one 2016-2020 record.

SLICES. A-trend, A-chop and B-chop bank ip1 (1,804 + 678 + 1,003 = 3,485).
B-trend never did — `--slices` and the ip1 fallback to
`results/gate2_ip1_recovered.csv` are what let the cloud recovery be dropped in
and the whole run repeated unchanged. Mode C is paused and is not included.

TWO CONVENTIONS ARE FIXED HERE THAT THE DELIVERY PATH GETS WRONG.

1. COSTS. `l2trades.run_pair` returns GROSS R; only `l2sweep.score_combo` and
   `l2tune.Scorer` subtract `S._cost_R`. Charged here, on the entry day.
2. ACCOUNT-NORMALISED R. Engine R scales as 1/atr_mult, so a strategy with a
   tighter stop books more R for the same price move and would silently carry
   more weight in an equal-weighted book. `l2tune` multiplies by atr_mult to
   restate everything against a fixed 1.0xATR risk unit; the delivery path never
   did. Applied here to marks as well as to trade R, so the cut and the book
   speak the same units. Cost is subtracted AFTER the restatement, exactly as
   the Scorer does it.

MARK-TO-MARKET BY TRUNCATION. Marks are daily INCREMENTS, so summing the
increments that fall inside a window is already the change in value over the
in-window part of the position. Truncating to a window IS marking to its
boundary; nothing is re-marked and no trade carries profit out of a window.
"""
import json, glob, time, argparse
import numpy as np, pandas as pd

import l2sweep as S
import l2trades as TR

RISK_KEYS = ('atr_len', 'atr_mult', 'tp_mult', 'trail_mult', 'trail_arm', 'be_pct')
ERAS = {'ip1': ('2011-01-01', '2015-12-31'), 'ip2': ('2016-01-01', '2020-12-31')}
YEARS = list(range(2011, 2021))
STEPS = ({'build': (2011, 2015), 'trade': (2016, 2018)},
         {'build': (2011, 2018), 'trade': (2019, 2020)})
SLICES3 = ('A-trend', 'A-chop', 'B-chop')
SRC = {'A-trend': ('gate2_tuned_modeA_trend.csv', 'A', 'trend'),
       'A-chop':  ('gate2_tuned_modeA_chop.csv',  'A', 'chop'),
       'B-trend': ('gate2_tuned_modeB.csv',       'B', 'trend'),
       'B-chop':  ('gate2_tuned_modeB.csv',       'B', 'chop')}

TRADES_F = os.path.join(ROOTOUT, 'wf_trades.pkl')
MARKS_F = os.path.join(ROOTOUT, 'wf_marks.pkl')


def recovered_ip1():
    """B-trend's ip1, once the rented box has banked it. Absent until then."""
    out = {}
    for f in ([os.path.join(ROOTOUT, 'gate2_ip1_recovered.csv')] +
              sorted(glob.glob(os.path.join(ROOTOUT, 'gate2_ip1_recovered_s*.csv')))):
        if not os.path.exists(f):
            continue
        try:
            d = pd.read_csv(f)
        except Exception:
            continue
        for r in d[d.sid != 'sid'].to_dict('records'):
            out[r['sid']] = r
    return out


def load_field(slices):
    REC = recovered_ip1()
    F = []
    for lab in slices:
        f, mode, sl = SRC[lab]
        d = pd.read_csv(os.path.join(ROOTOUT, f), low_memory=False)
        d = d[(d.slice == sl) & (d.crosses_label == True) & d.ip2.notna()].copy()
        d['src_mode'] = mode
        d['src_label'] = mode if mode == 'B' else '%s-%s' % (mode, sl)
        d['sid'] = (d.src_label + '|' + d.slice + '|' + d.c1 + '|' + d.c2 + '|'
                    + d.vol + '|' + d.base)
        if 'ip1' not in d.columns:
            d['ip1'] = np.nan; d['risk1'] = np.nan
        miss = d.ip1.isna()
        if miss.any() and REC:
            for i in d.index[miss]:
                r = REC.get(d.at[i, 'sid'])
                if r is not None:
                    d.at[i, 'ip1'] = r['ip1']; d.at[i, 'risk1'] = r['risk1']
        n0 = len(d)
        d = d[d.ip1.notna() & d.risk1.notna()]
        if len(d) < n0:
            print('  %s: %d of %d dropped, no ip1 banked' % (lab, n0 - len(d), n0),
                  flush=True)
        F.append(d)
        print('  %-8s %4d strategies with ip1' % (lab, len(d)), flush=True)
    D = pd.concat(F, ignore_index=True).drop_duplicates('sid').reset_index(drop=True)
    return D


# ------------------------------------------------------------------- engine
def _init():
    S.load_costs()


def _cfg(row, era):
    """The engine config for one era. ip1/risk1 for the W2 era, ip2/risk_* for
    W3 -- run_pair reads the parameter set from `ip2`, so ip1 is passed there."""
    c = dict(row)
    if era == 'ip1':
        c['ip2'] = row['ip1']
        rk = json.loads(row['risk1'])
        for k in RISK_KEYS:
            c['risk_' + k] = rk.get(k, rk.get('risk_' + k))
    return c


def engine_one(row):
    """Both eras for one strategy. Returns (trade rows, mark rows).

    R and every daily mark are ACCOUNT-NORMALISED (x atr_mult) and the entry
    cost is subtracted after the restatement, exactly as l2tune.Scorer does it.
    """
    sid = row['sid']
    code = dict((s, c) for s, _, c in S.SLICES)[row['slice']]
    T, M = [], []
    tid = 0
    for era, (a, z) in ERAS.items():
        cfg = _cfg(row, era)
        am = float(cfg['risk_atr_mult'])
        for p in S.all_pairs():
            try:
                r = TR.run_pair(cfg, p)
            except Exception:
                continue
            d, tr, cl = r['dates'], r['trades'], r['c']
            if len(tr['r']) == 0:
                continue
            reg = S.regime_codes(p, d)
            w = np.flatnonzero((d >= a) & (d <= z))
            if not len(w):
                continue
            lo, hi = int(w[0]), int(w[-1]) + 1
            dv = d.values
            for j in range(len(tr['r'])):
                eb, xb = int(tr['entry_bar'][j]), int(tr['exit_bar'][j])
                if xb < 0 or reg[eb] != code or not (lo <= eb < hi):
                    continue
                ent = float(tr['entry_px'][j]); u = float(tr['units'][j])
                sgn = float(tr['dir'][j]); tot = float(tr['r'][j]) * am
                cst = float(S._cost_R(p, np.array([ent]), np.array([u]),
                                      np.array([dv[eb]]))[0])
                end = min(xb, hi - 1)
                tid += 1
                prev = 0.0
                for b in range(eb, end + 1):
                    cum = (tot if (b == xb and xb <= hi - 1)
                           else sgn * (cl[b] - ent) * u / S.RISK * am)
                    M.append((sid, p, dv[b], int(sgn), np.float32(
                        cum - prev - (cst if b == eb else 0.0)), tid))
                    prev = cum
                T.append((sid, tid, p, dv[eb], dv[end], float(prev - cst), era))
    return T, M


def stage_engine(field, jobs):
    import multiprocessing as mp
    recs = field.to_dict('records')
    t = time.time()
    if jobs > 1:
        with mp.Pool(jobs, initializer=_init) as pool:
            got = pool.map(engine_one, recs, chunksize=4)
    else:
        _init(); got = [engine_one(r) for r in recs]
    T = pd.DataFrame([x for g, _ in got for x in g],
                     columns=['sid', 'tid', 'pair', 'entry', 'exit', 'R', 'era'])
    M = pd.DataFrame([x for _, g in got for x in g],
                     columns=['sid', 'pair', 'day', 'dir', 'mark', 'tid'])
    for c in ('sid', 'pair'):
        T[c] = T[c].astype('category'); M[c] = M[c].astype('category')
    T['entry'] = pd.to_datetime(T.entry); T['exit'] = pd.to_datetime(T.exit)
    M['day'] = pd.to_datetime(M.day)
    M['dir'] = M['dir'].astype(np.int8)
    T.to_pickle(TRADES_F); M.to_pickle(MARKS_F)
    print('  engine: %d trades, %d mark rows, %d strategies, %.1f min'
          % (len(T), len(M), T.sid.nunique(), (time.time() - t) / 60), flush=True)
    return T, M


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', default='engine')
    ap.add_argument('--slices', default=','.join(SLICES3))
    ap.add_argument('--jobs', type=int, default=int(os.environ.get('WF_JOBS', '5')))
    a = ap.parse_args()
    S.load_costs()
    sl = tuple(x for x in a.slices.split(',') if x)
    print('slices: %s' % (sl,), flush=True)
    F = load_field(sl)
    print('field: %d strategies' % len(F), flush=True)
    if a.stage == 'engine':
        stage_engine(F, a.jobs)


if __name__ == '__main__':
    main()
