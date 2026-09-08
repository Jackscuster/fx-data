import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""W3ONLY — the uncontaminated re-score.

THE PROBLEM. The walk-forward stitch is W2 under the FIRST tune (ip1) and W3
under the second (ip2). Everything downstream of gate 2 -- blind_trades, the
leaderboards, the co-equal ranking, the gate 3 cut, the portfolio previews --
scored BOTH blind windows with ip2. ip2 was tuned on W1+W2, so every W2 number
was measured with parameters that had already seen that window.

Measured on the eight graft members that do have ip1: W2 total R is 452.0 under
ip2 against 92.4 under ip1. **+389%.**

THE FIX HERE. Score W3 ONLY (2016-01-01 to 2020-12-31) under ip2. No tune has
ever seen W3, so ip2 is legitimate there and no ip1 is required. Half the blind
sample, all of it honest.

WHAT THIS IS NOT. It is not the full walk-forward number -- that needs ip1 for
W2 and mode B trend never banked it. The FULLSTITCH rebuild that recovers ip1
and restores W2 is registered as follow-up work; this is the clean answer
available today.

EVERY OUTPUT IS LABELLED W3ONLY so it can never be confused with a stitched
figure.
"""
import glob, json, time, argparse
import numpy as np, pandas as pd
import l2sweep as S
import l2tune as T

W3_ONLY = ('W3',)


def guard(windows, ip1_available):
    """FAIL LOUDLY if a score path touches W2 without ip1."""
    if 'W2' in windows and not ip1_available:
        raise RuntimeError(
            'CONTAMINATION GUARD: asked to score W2 without ip1. W2 must be '
            'scored with the FIRST tune; ip2 was tuned on W1+W2. Use W3-only, '
            'or supply ip1.')


def score_w3(sc, cfg, mode, sname, code, plan):
    combo = (cfg['c1'], cfg['c2'], cfg['vol'], cfg['base'],
             cfg.get('exit_ind') or S.slot_options()['exit_ind'][0])
    ip = json.loads(cfg['ip2']) if isinstance(cfg.get('ip2'), str) else None
    if ip is None:
        return None
    rk = {k: cfg['risk_' + k] for k in ('atr_len', 'atr_mult', 'tp_mult',
                                        'trail_mult', 'trail_arm', 'be_pct')}
    guard(W3_ONLY, ip1_available=True)      # W3 needs no ip1; guard documents it
    a = sc.score(combo, ip, rk, mode, sname, code, plan, W3_ONLY)
    return a.get('W3')


SRC = [('A', 'trend', 'gate2_tuned_modeA_trend.csv'),
       ('A', 'chop', 'gate2_tuned_modeA_chop.csv'),
       ('B', 'trend', 'gate2_tuned_modeB.csv'),
       ('B', 'chop', 'gate2_tuned_modeB.csv'),
       ('C', 'trend', 'gate2_tuned_modeC.csv')]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--shard', type=int, default=0)
    ap.add_argument('--shards', type=int, default=1)
    a = ap.parse_args()
    S.load_costs(); T.ACCT_OBJECTIVE = True
    sc = T.Scorer()
    out, t0 = [], time.time()
    bank = os.path.join(ROOTOUT, 'gate2_w3only_scores_%02d.csv' % a.shard)
    done = set()
    if os.path.exists(bank):
        done = set(pd.read_csv(bank).sid)
    todo = []
    for mode, sl, f in SRC:
        p = os.path.join(ROOTOUT, f)
        if not os.path.exists(p):
            print('  skip (missing): %s' % f, flush=True); continue
        d = pd.read_csv(p, low_memory=False)
        d = d[(d.slice == sl) & (d.crosses_label == True) & d.ip2.notna()].copy()
        d['src_mode'] = mode
        d['src_label'] = mode if mode == 'B' else '%s-%s' % (mode, sl)
        d['sid'] = d.src_label + '|' + d.slice + '|' + d.c1 + '|' + d.c2 + '|' + d.vol + '|' + d.base
        todo.append(d)
    D = pd.concat(todo, ignore_index=True).drop_duplicates('sid')
    D = D[~D.sid.isin(done)]
    if a.shards > 1:
        D = D.iloc[a.shard::a.shards]
    if a.limit:
        D = D.head(a.limit)
    print('W3ONLY re-score: %d crossers to do (shard %d/%d)'
          % (len(D), a.shard, a.shards), flush=True)
    for i, cfg in enumerate(D.to_dict('records'), 1):
        sn = cfg['slice']
        code = dict((s, c) for s, _, c in S.SLICES)[sn]
        plan = dict((s, p) for s, p, _ in S.SLICES)[sn]
        try:
            g = score_w3(sc, cfg, cfg['src_mode'], sn, code, plan)
        except Exception as e:
            g = None
        row = {k: cfg[k] for k in ('sid', 'src_label', 'src_mode', 'slice',
                                   'c1', 'c2', 'vol', 'base', 'exit_ind', 'ip2')}
        row.update({'risk_' + k: cfg['risk_' + k] for k in
                    ('atr_len', 'atr_mult', 'tp_mult', 'trail_mult', 'trail_arm', 'be_pct')})
        for k in ('n', 'total_R', 'expectancy_R', 'profit_factor', 'sharpe',
                  'sortino', 'calmar', 'max_dd_R', 'ulcer_R', 'win_rate',
                  'avg_win_R', 'avg_loss_R', 'win_loss_ratio',
                  'profit_concentration', 'avg_hold_bars'):
            row['w3_' + k] = (g or {}).get(k)
        out.append(row)
        if i % 50 == 0 or i == len(D):
            pd.DataFrame(out).to_csv(bank, mode='a', index=False,
                                     header=not os.path.exists(bank))
            out = []
            el = time.time() - t0
            print('  %d/%d  %.2f s each  ~%.1f h left'
                  % (i, len(D), el / i, (el / i) * (len(D) - i) / 3600), flush=True)
    if out:
        pd.DataFrame(out).to_csv(bank, mode='a', index=False,
                                 header=not os.path.exists(bank))
    print('DONE in %.1f min' % ((time.time() - t0) / 60), flush=True)


if __name__ == '__main__':
    main()
