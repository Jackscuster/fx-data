import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""A_ENTRY_B_EXIT — what the mode bug was accidentally testing.

For eleven weeks every mode A strategy in the delivery layer was run with mode
B's exit rule. That was a bug, and it is fixed. But it was also, by accident, a
real experiment: A's entries with B's exits. This scores both, deliberately, so
the pre-fix results are kept as a labelled variant rather than discarded.

SAME SETTINGS, FEES ON, W3 ONLY. Both runs use the strategy's own tuned
parameters -- the ones gate 2 chose FOR A'S EXIT. That is the whole caveat: a
strategy that looks better with B's exit here has not been tuned for B's exit,
so this is a signal to test, never a result to adopt. Anything promising has to
go back through gate 2 tuning with that exit before it can be taken seriously.

NO NEW MODE IS ADDED. This reports; it does not create A-entry-B-exit as a
tradeable configuration.
"""
import json, time
import numpy as np, pandas as pd
import l2sweep as S
import l2tune as T

W3 = ('W3',)


def main():
    t0 = time.time()
    S.load_costs(); T.ACCT_OBJECTIVE = False
    V = pd.read_csv(os.path.join(ROOTOUT, 'gate3_costed_verdicts.csv'), low_memory=False)
    A = V[V.src_mode == 'A'].copy()
    print('A-strategies in the W3-only cut: %d' % len(A), flush=True)
    team = set()
    f = os.path.join(ROOTOUT, 'team1_W3ONLY_GATE2_roster.csv')
    if os.path.exists(f):
        team = set(pd.read_csv(f).sid)
    sc = T.Scorer()
    rows = []
    for i, r in enumerate(A.to_dict('records'), 1):
        combo = (r['c1'], r['c2'], r['vol'], r['base'],
                 r.get('exit_ind') or S.slot_options()['exit_ind'][0])
        sn = r['slice']
        code = dict((s, c) for s, _, c in S.SLICES)[sn]
        plan = dict((s, p) for s, p, _ in S.SLICES)[sn]
        try:
            ip = json.loads(r['ip2'])
            rk = {k: r['risk_' + k] for k in ('atr_len', 'atr_mult', 'tp_mult',
                                              'trail_mult', 'trail_arm', 'be_pct')}
            ga = sc.score(combo, ip, rk, 'A', sn, code, plan, W3).get('W3')
            gb = sc.score(combo, ip, rk, 'B', sn, code, plan, W3).get('W3')
        except Exception:
            continue
        if not ga or not gb:
            continue
        row = dict(sid=r['sid'], slice=sn, c1=r['c1'], c2=r['c2'], vol=r['vol'],
                   base=r['base'], in_team=r['sid'] in team)
        for tag, g in (('A', ga), ('B', gb)):
            row[tag + '_total_R'] = g['total_R']
            row[tag + '_max_dd_R'] = g['max_dd_R']
            row[tag + '_sortino'] = g['sortino']
            row[tag + '_calmar'] = g['calmar']
            row[tag + '_trades'] = g['n']
        row['B_wins_return'] = bool(gb['total_R'] > ga['total_R'])
        row['B_wins_dd'] = bool(gb['max_dd_R'] < ga['max_dd_R'])
        # a CHALLENGER beats A's exit on return without giving back drawdown,
        # Sortino or Calmar -- the same bar the adoption rule uses
        row['challenger'] = bool(
            gb['total_R'] > ga['total_R']
            and gb['max_dd_R'] <= ga['max_dd_R']
            and (gb['sortino'] >= ga['sortino'] or not np.isfinite(ga['sortino']))
            and gb['calmar'] >= ga['calmar'])
        rows.append(row)
        if i % 20 == 0:
            print('  %d/%d, %.0f s' % (i, len(A), time.time() - t0), flush=True)
    D = pd.DataFrame(rows)
    D.to_csv(os.path.join(ROOTOUT, 'variant_A_ENTRY_B_EXIT.csv'), index=False)
    n = len(D)
    print('\nscored %d A-strategies both ways' % n, flush=True)
    print('  B exit wins on RETURN     : %d (%.1f%%)' % (D.B_wins_return.sum(),
          100 * D.B_wins_return.mean()), flush=True)
    print('  B exit wins on DRAWDOWN   : %d (%.1f%%)' % (D.B_wins_dd.sum(),
          100 * D.B_wins_dd.mean()), flush=True)
    print('  CHALLENGERS (all four)    : %d (%.1f%%)' % (D.challenger.sum(),
          100 * D.challenger.mean()), flush=True)
    t = D[D.in_team]
    print('  of the %d team members    : %d are challengers'
          % (len(t), int(t.challenger.sum())), flush=True)
    print('DONE in %.1f min' % ((time.time() - t0) / 60), flush=True)


if __name__ == '__main__':
    main()
