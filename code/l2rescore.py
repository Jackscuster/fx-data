import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""W3-ONLY RE-SCORE OF MODE B — a PARTIAL DIAGNOSTIC, not mode B's score.

WHAT THIS IS NOT. It is not mode B's stitched blind score and must never be
reported as one. B's official stitched number waits for round-2 deepening.

WHY ONLY W3. B's two blind windows were traded with DIFFERENT parameter sets --
W2 with the W1-tuned set, W3 with the W1+W2-tuned set -- and B banked only the
second. So W3 can be reproduced exactly from disk and W2 cannot be reproduced at
all.

THE SHORTCUT THAT WAS REFUSED. Scoring W2 with the banked second-stage set would
make every number look complete, and would be leakage: those parameters were
tuned ON W1+W2, so trading W2 with them scores a window the tuner had already
seen. It would inflate every re-scored figure silently and in the favourable
direction. A missing number is better than a wrong one.

WHAT IT IS GOOD FOR. One correctly-computed blind window per combination, with
the full KPI stack including Ulcer, which the original run never stored
per-window. Enough for a rough cross-mode read while round 2 is pending, since
A and C compute their windows the same way.

NO LEAKAGE IN WHAT IS COMPUTED: W3 was blind to the W1+W2 tuning that chose
these parameters, exactly as it was in the original run.

Writes results/gate2_rescoreW3_modeB.csv.
"""
import glob, json, time
import numpy as np, pandas as pd
import l2sweep as S, l2tune as T

OUT = os.path.join(ROOTOUT, 'gate2_rescoreW3_mode%s.csv')
RISK_COLS = ('atr_len', 'atr_mult', 'tp_mult', 'trail_mult', 'trail_arm', 'be_pct')


def _worker(args):
    mode, sname, rows = args
    code = dict((s, c) for s, _, c in S.SLICES)[sname]
    plan = dict((s, p) for s, p, _ in S.SLICES)[sname]
    sc = T.Scorer(disk=True)
    out = []
    for r in rows:
        try:
            ip = json.loads(r['ip2'])
            risk = {k: r['risk_' + k] for k in RISK_COLS}
            cb = (r['c1'], r['c2'], r['vol'], r['base'], r['exit_ind'])
            a = sc.score(cb, ip, risk, mode, sname, code, plan, ('W3',))['W3']
        except Exception as e:
            out.append(dict(r, rescore_error=repr(e)[:100])); continue
        if a is None:
            out.append(dict(r, w3_n=0)); continue
        out.append(dict(r, w3_n=a['n'], w3_expectancy_R=a['expectancy_R'],
                        w3_total_R=a['total_R'], w3_profit_factor=a['profit_factor'],
                        w3_sharpe=a['sharpe'], w3_sortino=a['sortino'],
                        w3_max_dd_R=a['max_dd_R'], w3_ulcer_R=a['ulcer_R'],
                        w3_calmar=a['calmar'], w3_win_rate=a['win_rate']))
    return out


def run(mode='B', jobs=2, batch=120):
    import multiprocessing as mp
    tasks = []
    for sname in ('trend', 'chop'):
        fs = sorted(glob.glob(os.path.join(T.CK, 'mode%s_%s' % (mode, sname),
                                           'chunk_*.csv')))
        if not fs:
            continue
        D = pd.concat([pd.read_csv(f) for f in fs], ignore_index=True)
        D = D[D['ip2'].notna()]
        rows = D.to_dict('records')
        for i in range(0, len(rows), batch):
            tasks.append((mode, sname, rows[i:i + batch]))
    if not tasks:
        raise SystemExit('nothing banked for mode %s' % mode)
    print('W3 re-score, mode %s: %d batches, %d workers (deliberately few -- '
          'mode B is still tuning)' % (mode, len(tasks), jobs), flush=True)
    out = []
    t0 = time.time()
    with mp.Pool(jobs) as pool:
        for i, rr in enumerate(pool.imap_unordered(_worker, tasks)):
            out.extend(rr)
            if (i + 1) % 10 == 0:
                print('  %d/%d batches, %.0f s' % (i + 1, len(tasks), time.time() - t0),
                      flush=True)
    D = pd.DataFrame(out)
    D['PARTIAL_DIAGNOSTIC'] = 'W3 only -- NOT mode B stitched score; see MANIFEST.md'
    D.to_csv(OUT % mode, index=False)
    return D


def main():
    a = sys.argv[1:]
    mode = a[a.index('--mode') + 1] if '--mode' in a else 'B'
    jobs = int(a[a.index('--jobs') + 1]) if '--jobs' in a else 2
    D = run(mode=mode, jobs=jobs)
    ok = D[D.get('w3_n', pd.Series(dtype=float)).fillna(0) > 0]
    print('\nre-scored %d rows, %d with W3 trades' % (len(D), len(ok)))
    if len(ok):
        print(ok[['w3_n', 'w3_expectancy_R', 'w3_total_R', 'w3_sortino',
                  'w3_ulcer_R', 'w3_max_dd_R']].describe(
                      percentiles=[.5, .95]).round(4).to_string())
    return D


if __name__ == '__main__':
    main()
