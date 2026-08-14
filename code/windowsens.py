import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""WINDOW SENSITIVITY. Do nearby lookback choices give a different machine?

THE COMPANION TO THE REFIT TEST, and the same spirit. Refit asked whether
re-estimating the fitted numbers changes the state calls. This asks whether the
one big number that is NOT fitted -- the lookback, fixed by construction at 106
bars -- sits on a cliff or a plateau. A classifier whose output swings on a
14-bar change of window is a classifier whose window was doing the work.

THIS IS NOT A RE-TUNE. The shipped window stays at 106. Nothing here is selected,
nothing is compared on separation or any other quality measure, and no window
is proposed. 90 and 120 are declared before running, chosen only as "near",
and the measure is the SAME per-day agreement used by the refit test so the two
numbers can be read against each other.

WHAT MOVES AND WHAT DOES NOT. Changing the lookback changes the four components
that use it -- disp (net/path), tests, inside, revert. It does NOT change
`fails` (its own KFAIL=20 window), `seq`, the swing width N=19, the activity
scale axis (its own 28-bar lookback), the 5-bar dwell, or any cut rule. All
fitted quantities are re-estimated at each window on the shipped fit window,
because a score built on a different lookback has a different distribution and
reusing the old standardisation would compare two things that are not
comparable.

THE CONTROL. Rebuilding at 106 must reproduce the shipped states exactly. The
run asserts it, for the same reason refit.py does: a sensitivity test that cannot
reproduce its own starting point is measuring its own plumbing.

Writes results/window_sensitivity.csv + .txt.
"""
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
SHIPPED = os.path.join(ROOTOUT, 'states_g4_twoscore4.csv')
SPLIT = pd.Timestamp('2016-01-01')
WINDOWS = [90, 106, 120]
SHIP_W = 106
CELLS = ['trending', 'ranging', 'trend-in-range', 'neither']

from twoscores import raw_parts, classify, W as LOCKED_W
from classifier import zfit
from final import activity, DROP_TESTS, BUMP, ACTW
from refit import runs_of
from drivers import hdr


def build_at(px, fit, Wl):
    T, C = raw_parts(px, Wl=Wl)
    C = dict(C)
    if DROP_TESTS:
        C.pop('tests', None)
    zt, zc = zfit(T, fit), zfit(C, fit)
    tr = sum(zt[k] for k in T)
    ch = sum(zc[k] for k in C)
    a = activity(px, fit)
    return classify(tr - a.replace(ACTW).astype(float) * BUMP, ch, fit)[0]


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    ship = pd.read_csv(SHIPPED, index_col=0, parse_dates=True, comment='#')
    fit = np.asarray(px.index < SPLIT)
    print('WINDOW SENSITIVITY -- is the lookback on a cliff or a plateau?')
    print('  the shipped lookback is W = %d, read from twoscores.py, and it'
          % LOCKED_W)
    print('  DOES NOT MOVE. 90 and 120 were declared before running.')
    print('  components that use the lookback: disp, tests, inside, revert')
    print('  untouched: fails (KFAIL=20), seq, swing width 19, the activity')
    print('             scale axis (28), the 5-bar dwell, every cut rule')

    labs = {}
    for w in WINDOWS:
        labs[w] = build_at(px, fit, w)
        print('  built at %d bars' % w)

    idx = ship.index.intersection(labs[SHIP_W].index)
    B = ship.reindex(idx)

    # ---- control ----
    A0 = labs[SHIP_W].reindex(idx)[ship.columns]
    ok0 = A0.notna() & B.notna()
    same = float(((A0 == B) & ok0).sum().sum() / ok0.sum().sum())
    print('\nCONTROL -- rebuilding at the shipped %d bars' % SHIP_W)
    print('  agreement with shipped: %.4f over %d labelled pair-bars'
          % (same, int(ok0.sum().sum())))
    assert same > 0.9999, ('rebuilding at %d does not reproduce the shipped '
                           'states (%.4f) -- the harness is wrong' % (SHIP_W, same))
    print('  PASS.')

    rows, drows = [], []
    for w in WINDOWS:
        A = labs[w].reindex(idx)[ship.columns]
        ok = A.notna() & B.notna()
        eq = (A == B) & ok
        agree = float(eq.sum().sum() / ok.sum().sum())
        pa = A.where(ok).stack().value_counts(normalize=True)
        pb = B.where(ok).stack().value_counts(normalize=True)
        exp = float(sum(pa.get(s, 0) * pb.get(s, 0) for s in CELLS))
        rows.append(dict(window=w, state='ALL', pair_bars=int(ok.sum().sum()),
                         agreement=agree, expected=exp,
                         kappa=(agree - exp) / (1 - exp),
                         coverage=float(A.notna().sum().sum() / A.size)))
        for s in CELLS:
            sel = (B == s) & ok
            n = int(sel.sum().sum())
            if n < 50:
                continue
            rows.append(dict(window=w, state=s, pair_bars=n,
                             agreement=float((eq & sel).sum().sum() / n),
                             expected=np.nan, kappa=np.nan,
                             share_of_bars=float(n / ok.sum().sum())))
        dis = (~eq) & ok
        allr = np.concatenate([runs_of(dis[p].values) for p in ship.columns])
        tot = full = part = clean = 0
        for p in ship.columns:
            v = B[p].dropna()
            gid = (v != v.shift()).cumsum()
            for _, g in v.groupby(gid):
                if len(g) < 5:
                    continue
                q = A[p].reindex(g.index)
                d = (q != g) & q.notna()
                tot += 1
                if d.sum() == 0:
                    clean += 1
                elif d.sum() == len(g):
                    full += 1
                else:
                    part += 1
        drows.append(dict(window=w, disagreeing_bars=int(dis.sum().sum()),
                          disagreement_runs=int(len(allr)),
                          median_run=float(np.median(allr)) if len(allr) else np.nan,
                          share_of_bars_in_runs_ge5=float(allr[allr >= 5].sum()
                                                          / allr.sum())
                          if len(allr) else np.nan,
                          share_of_bars_in_runs_ge20=float(allr[allr >= 20].sum()
                                                           / allr.sum())
                          if len(allr) else np.nan,
                          episodes=tot, episodes_untouched=clean,
                          episodes_partly_relabelled=part,
                          episodes_fully_relabelled=full,
                          share_fully_relabelled=full / tot if tot else np.nan))
    S = pd.DataFrame(rows)
    D = pd.DataFrame(drows)
    print('\nAGREEMENT WITH THE SHIPPED CLASSIFIER (full history)')
    print('  %-8s %10s %10s %8s %9s' % ('window', 'agreement', 'chance', 'kappa',
                                        'coverage'))
    for _, r in S[S.state == 'ALL'].iterrows():
        print('  %-8d %10.4f %10.4f %8.3f %9.4f'
              % (r.window, r.agreement, r.expected, r.kappa, r.coverage))
    print('\n  BY STATE (shipped label as reference)')
    print('  %-8s %s' % ('window', '  '.join('%-16s' % s for s in CELLS)))
    for w in WINDOWS:
        d = S[(S.window == w) & (S.state != 'ALL')]
        print('  %-8d %s' % (w, '  '.join(
            '%-16s' % ('%.3f' % d[d.state == s].agreement.iloc[0]
                       if len(d[d.state == s]) else '-') for s in CELLS)))
    print('\nWHERE THE DISAGREEMENTS SIT')
    print('  %-8s %10s %8s %10s %10s %9s %9s'
          % ('window', 'dis. bars', 'med run', 'in runs>=5', 'in runs>=20',
             'episodes', 'fully rel.'))
    for _, r in D.iterrows():
        print('  %-8d %10d %8.1f %10.3f %10.3f %9d %9.3f'
              % (r.window, r.disagreeing_bars, r.median_run,
                 r.share_of_bars_in_runs_ge5, r.share_of_bars_in_runs_ge20,
                 r.episodes, r.share_fully_relabelled))
    OUT = S.merge(D, on='window', how='left')
    OUT['shipped_window'] = SHIP_W
    OUT.to_csv(os.path.join(ROOTOUT, 'window_sensitivity.csv'), index=False)

    a90 = float(S[(S.window == 90) & (S.state == 'ALL')].agreement.iloc[0])
    a120 = float(S[(S.window == 120) & (S.state == 'ALL')].agreement.iloc[0])
    hdr(os.path.join(ROOTOUT, 'window_sensitivity.csv'),
        'Window sensitivity -- do nearby lookbacks give a different machine?',
        'THIS IS NOT A RE-TUNE. The shipped lookback stays at %d bars. Nothing\n'
        'here is selected, no window is compared on separation or any other\n'
        'quality measure, and no window is proposed. 90 and 120 were declared\n'
        'before running, chosen only as "near", and the measure is the SAME\n'
        'per-day agreement the refit test uses so the two read against each\n'
        'other.\n\n'
        'WHAT THE LOOKBACK TOUCHES: disp (net/path), tests, inside, revert. What\n'
        'it does not: fails (its own KFAIL=20 window), seq, the swing width 19,\n'
        'the activity scale axis (its own 28-bar lookback), the 5-bar dwell, and\n'
        'every cut rule. All fitted quantities are re-estimated at each window on\n'
        'the shipped fit window, because a score built on a different lookback\n'
        'has a different distribution and reusing the old standardisation would\n'
        'compare two things that are not comparable.\n\n'
        'CONTROL: rebuilding at %d reproduces the shipped states exactly, and\n'
        'the run asserts it.\n\n'
        'THE RESULT, AND IT IS NOT THE COMFORTABLE ONE. %.3f agreement at 90\n'
        'bars and %.3f at 120, against 0.939-0.964 for the refit test. Moving\n'
        'the lookback by 15%% changes roughly ONE CALL IN SIX; re-estimating\n'
        'every fitted number from a fit window seven years shorter changes one\n'
        'in twenty. THE WINDOW IS A BIGGER LEVER THAN THE FITTING.\n\n'
        'The disagreements are also a different KIND. Under refit the median\n'
        'disagreement run was 3-4 bars, BELOW the 5-bar dwell, and 3-6%% of\n'
        'episodes were fully relabelled -- boundary noise. Here the median run\n'
        'is 7 bars, ABOVE the dwell, and 15-16%% of episodes are fully\n'
        'relabelled. Changing the window does not jitter the edges; it tells a\n'
        'different story about whole stretches of market.\n\n'
        'WHAT THAT DOES AND DOES NOT MEAN. It is not a cliff: kappa is still\n'
        '0.74 and 0.77, substantial agreement, and 120 sits closer to the\n'
        'shipped read than 90 as a monotone drift rather than a discontinuity.\n'
        'It does mean the lookback is a REAL CHOICE carrying real consequences,\n'
        'not a free parameter -- which is an argument for leaving it locked and\n'
        'documented rather than revisiting it, and an argument against reading\n'
        'any single state call as though the window were incidental to it.\n\n'
        'The fragile cells are the same ones refit exposed: trending and ranging\n'
        'hold ~0.85 at both windows, while trend-in-range and neither fall to\n'
        '0.73 at 90 bars. The overlap cell and the residual cell inherit the\n'
        'wobble of both cuts.\n'
        % (SHIP_W, SHIP_W, a90, a120))
    print('\nwrote window_sensitivity.csv + .txt')
    return S, D


if __name__ == '__main__':
    main()
