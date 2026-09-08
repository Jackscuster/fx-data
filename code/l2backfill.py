import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""BACK-FILL the metrics added after the fine-tune started — INCUMBENT ONLY.

WHY THE CANDIDATE SIDE CANNOT BE BACK-FILLED, AND WHY THE FIRST ATTEMPT WAS
WRONG. The candidate's stitched blind score is W2 scored with ip1/rk1 -- the
FIRST tune -- plus W3 scored with ip2/rk2. That is the walk-forward machine: the
parameters that trade W2 must never have seen W2.

The first version of this script re-scored the candidate with ip2/rk2 on BOTH
windows, because only ip2 is banked. That is not the walk-forward number and it
is contaminated on W2, since ip2 was tuned on W1+W2. It produced candidate
totals that differed from the bank in both directions and led me to report a
"corrected" adoption list that was itself wrong.

THE BANK'S ft_* NUMBERS ARE THE CORRECT ONES. This script no longer touches
them. It back-fills only the INCUMBENT side, where there is a single fixed
settings set and no ip1/ip2 distinction, so re-scoring is exact.

ip1/rk1 are now banked by l2gate3ft.py for every strategy still to come, so
future rows CAN be reconstructed fully. Rows already finished cannot, short of
re-running full_walk at ~290 s each.
"""
"""

The nine shards loaded the old recorder at import and keep writing the old
column set until they exit, so the new metrics -- avg win, avg loss,
win/loss ratio, profit concentration, average hold, and Calmar/PF on the
incumbent -- are absent from every row banked so far.

Back-filling means RE-SCORING both settings sets for each strategy. That is
roughly two Scorer calls per strategy, so it is cheap for the adoptions and
alternates and expensive for all of them. --which selects the scope.
"""
import glob, json, time, argparse
import numpy as np, pandas as pd
import l2sweep as S
import l2tune as T
import l2gate3 as G3

KEYS = ('total_R', 'expectancy_R', 'profit_factor', 'sharpe', 'sortino',
        'calmar', 'max_dd_R', 'ulcer_R', 'win_rate', 'avg_win_R', 'avg_loss_R',
        'win_loss_ratio', 'profit_concentration', 'avg_hold_bars', 'n')


def score(sc, cfg, ip, rk, mode, sname, code, plan):
    a = sc.score(cfg, ip, rk, mode, sname, code, plan, ('W2', 'W3'))
    parts = [a[w] for w in ('W2', 'W3') if a.get(w)]
    if not parts:
        return None
    g = T._agg(np.concatenate([p['_r'] for p in parts]))
    hn = [(p.get('avg_hold_bars'), p['n']) for p in parts
          if p.get('avg_hold_bars') == p.get('avg_hold_bars')]
    if hn:
        g['avg_hold_bars'] = float(sum(h * n for h, n in hn) / sum(n for _, n in hn))
    return g


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--which', default='adopted',
                    choices=['adopted', 'alternates', 'all'])
    a = ap.parse_args()
    S.load_costs(); T.ACCT_OBJECTIVE = True
    A = pd.read_csv(os.path.join(ROOTOUT, 'gate3ft_adoptions_v2.csv'))
    if a.which == 'adopted':
        sel = A[A.adopted_v2 == True]
    elif a.which == 'alternates':
        sel = A[(A.beat_on_return == True) & (A.adopted_v2 == False)]
    else:
        sel = A
    P = G3.population().set_index('sid')
    sc = T.Scorer()
    rows, t0 = [], time.time()
    for r in sel.to_dict('records'):
        sid = r['sid']
        if sid not in P.index:
            continue
        cfg = P.loc[sid].to_dict()
        combo = (cfg['c1'], cfg['c2'], cfg['vol'], cfg['base'],
                 cfg.get('exit_ind') or S.slot_options()['exit_ind'][0])
        sn = cfg['slice']
        code = dict((s, c) for s, _, c in S.SLICES)[sn]
        plan = dict((s, p) for s, p, _ in S.SLICES)[sn]
        mode = cfg['src_mode']
        out = dict(r)
        try:
            ip0 = json.loads(cfg['ip2'])
            rk0 = {k: cfg['risk_' + k] for k in ('atr_len', 'atr_mult', 'tp_mult',
                                                 'trail_mult', 'trail_arm', 'be_pct')}
            g0 = score(sc, combo, ip0, rk0, mode, sn, code, plan)
            g1 = None          # candidate side is NOT re-scored -- see the header
        except Exception as e:
            out['backfill_error'] = str(e)[:120]; rows.append(out); continue
        for k in KEYS:
            out['base_' + k] = (g0 or {}).get(k)
            # ft_* left exactly as the bank recorded them
        rows.append(out)
        print('  %d/%d  %.0f s' % (len(rows), len(sel), time.time() - t0), flush=True)
    D = pd.DataFrame(rows)
    f = os.path.join(ROOTOUT, 'gate3ft_%s_full_metrics.csv' % a.which)
    D.to_csv(f, index=False)
    print('wrote %s (%d rows) in %.1f min'
          % (os.path.basename(f), len(D), (time.time() - t0) / 60), flush=True)


if __name__ == '__main__':
    main()
