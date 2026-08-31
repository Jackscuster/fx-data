import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""INVERSE CANDIDATE SCREEN — combinations reliably WORSE than chance.

A SCREEN ONLY. It runs no inversions and proposes none. Inverting a combination
is a full tune-and-blind-test job and counts toward the deflation total like any
other search; nothing here shortcuts that.

------------------------------------------------------------------------
THE STANDARD, WHICH IS GATE 1'S OWN STANDARD POINTED DOWN
------------------------------------------------------------------------
A winner must clear the luck floor -- the 95th percentile of that mode and
slice's sign-randomised controls -- and hold profit factor >= 1.05. The mirror
is the SAME null distribution read from the other end:

    loser: expectancy < p5 of the controls   AND   profit factor <= 1/1.05

p5 of the controls, not the negative of p95. The null is not symmetric -- chop's
controls have a POSITIVE mean (+0.021 to +0.025 R) because the money-management
plan earns on any entries at all -- so mirroring the number instead of the
distribution would set the bar in the wrong place on three of the four slices.

------------------------------------------------------------------------
EPISODE-BASED: BAD IN EVERY WINDOW, NOT BAD ON AVERAGE
------------------------------------------------------------------------
A stitched blind expectancy can be dragged under the floor by one bad window
while the other is fine. That is a bad episode, not a reliably bad rule, and
inverting it would buy the noise. So each window is tested SEPARATELY and a
candidate must fail in all three:

    W1 (tuning)  AND  W2 (blind)  AND  W3 (blind)

each below its own slice's p5 floor, each with enough trades to mean anything
(the same MIN_TRADES_PICK / MIN_TRADES_BLIND gate 1 applies to winners).

Requiring W1 as well is what makes it 'reliably bad rather than unlucky': a rule
that was already losing on the window the tuner was allowed to see, and kept
losing on two it never saw.

------------------------------------------------------------------------
EACH WINDOW MUST BE SCORED WITH THE PARAMETERS THAT WERE BLIND TO IT
------------------------------------------------------------------------
The walk-forward machine is tune-W1 -> blind-W2 -> retune-W1+W2 -> blind-W3.
So `ip2`/`risk` -- the SECOND tune -- saw W2. Scoring W2 with them is an
in-sample number wearing a blind label. A first pass of this screen did exactly
that and the sampled W2 expectancy came back at +1.20 R median, on combinations
selected for being BAD; that is what an in-sample fit looks like, and it made
the whole screen return a false zero.

Corrected:

    W1 scored with ip1/risk1   (the window the first tune saw)
    W2 scored with ip1/risk1   (genuinely blind to it)
    W3 scored with ip2/risk    (genuinely blind to it)

NOT SCREENABLE: mode B's TREND slice never banked ip1/risk1 -- GAUNTLET already
records this as the reason B is re-run wholesale at round 2. Its 14,815
combinations cannot have a true blind W2 reconstructed and are reported as
not-screenable, never as passing or failing.

------------------------------------------------------------------------
WHAT IS EXEMPT
------------------------------------------------------------------------
Chop combinations that CROSSED are exempt by the declared inversion rule -- the
chop slice already has an inversion arm and a crosser there is not an inverse
candidate. They are counted and reported as exempt, never silently dropped.

Writes results/gate2_inverse_screen.csv -- every candidate, all windows.
"""
import glob, json, time
import numpy as np, pandas as pd

import l2sweep as S
import l2tune as T

OUT = os.path.join(ROOTOUT, 'gate2_inverse_screen.csv')
PF_MAX = 1.0 / 1.05


def floors():
    """(mode, slice) -> p5 of that population's own fresh controls."""
    d = {}
    for m in ('A', 'B', 'C'):
        f = os.path.join(ROOTOUT, 'gate1_null_raw_mode%s.csv' % m)
        if not os.path.exists(f):
            continue
        N = pd.read_csv(f, low_memory=False)
        for sl, g in N.groupby('slice'):
            d[(m, sl)] = float(np.percentile(g.expectancy_R, 5))
    return d


def population():
    fr = []
    for f in sorted(glob.glob(os.path.join(ROOTOUT, 'gate2_tuned_mode*.csv'))):
        D = pd.read_csv(f, low_memory=False)
        if 'expectancy_R' not in D.columns:
            continue
        D['src_file'] = os.path.basename(f)
        fr.append(D)
    A = pd.concat(fr, ignore_index=True)
    # a combination can appear in both a per-slice file and a whole-mode file
    return A.drop_duplicates(['mode', 'slice', 'c1', 'c2', 'vol', 'base', 'exit_ind'])


def _worker(args):
    rows, = args
    sc = T.Scorer()
    out = []
    for r in rows:
        cb = (r['c1'], r['c2'], r['vol'], r['base'], r['exit_ind'])
        sname = r['slice']
        code = dict((s, c) for s, _, c in S.SLICES)[sname]
        plan = dict((s, p) for s, p, _ in S.SLICES)[sname]
        ip2 = json.loads(r['ip2']) if isinstance(r.get('ip2'), str) else None
        ip1 = json.loads(r['ip1']) if isinstance(r.get('ip1'), str) else None
        rk1 = json.loads(r['risk1']) if isinstance(r.get('risk1'), str) else None
        rk2 = {k: r['risk_' + k] for k in
               ('atr_len', 'atr_mult', 'tp_mult', 'trail_mult', 'trail_arm', 'be_pct')}
        if ip2 is None or ip1 is None or rk1 is None:
            continue
        rec = dict(r)
        ok = True
        # W1 and W2 under the FIRST tune; W3 under the second. Each window is
        # scored only with parameters that never saw it.
        for w, ip, rk in (('W1', ip1, rk1), ('W2', ip1, rk1), ('W3', ip2, rk2)):
            try:
                a = sc.score(cb, ip, rk, r['mode'], sname, code, plan, (w,)).get(w)
            except Exception:
                a = None
            rec[w + '_exp'] = None if a is None else a['expectancy_R']
            rec[w + '_n'] = None if a is None else a['n']
            rec[w + '_pf'] = None if a is None else a.get('profit_factor')
            if a is None:
                ok = False
        rec['scored'] = ok
        out.append(rec)
    return out


def main():
    a = sys.argv[1:]
    jobs = int(a[a.index('--jobs') + 1]) if '--jobs' in a else 1
    fl = floors()
    P = population()
    print('population %d tuned combinations' % len(P), flush=True)
    P['floor_p5'] = [fl.get((m, s), np.nan) for m, s in zip(P['mode'], P['slice'])]

    # NOT SCREENABLE: no banked first tune, so no reconstructable blind W2.
    has1 = P.ip1.notna() & P.risk1.notna() if 'ip1' in P.columns else P.index == -1
    ns = P[~has1]
    print('not screenable (no banked ip1/risk1): %d  %s'
          % (len(ns), dict(ns.groupby(['mode', 'slice']).size())), flush=True)
    P = P[has1]

    # STAGE 1, deliberately GENEROUS: 'losing at all' on the banked stitch, not
    # 'below the floor'. The banked stitch scores W2 with the second tune, which
    # flatters it, so screening on the floor here would throw away exactly the
    # candidates this pass is looking for. The episode test does the real work.
    b = ((P.expectancy_R < 0) & (P.profit_factor < 1.0)
         & (P.n_blind >= S.MIN_TRADES_BLIND) & P.ip2.notna())
    short = P[b].copy()
    exempt = short[(short['slice'] == 'chop') & (short.crosses_label == True)]
    short = short[~((short['slice'] == 'chop') & (short.crosses_label == True))]
    print('stage 1 (banked stitch losing: exp < 0 and PF < 1): %d, of which %d '
          'exempt (chop crossers) -> %d to window-test'
          % (len(short) + len(exempt), len(exempt), len(short)), flush=True)
    if not len(short):
        pd.DataFrame().to_csv(OUT, index=False)
        print('NO CANDIDATES', flush=True)
        return

    # STAGE 2: the episode test -- every window separately.
    import multiprocessing as mp
    rows = short.to_dict('records')
    B = max(1, len(rows) // max(1, jobs * 40))
    tasks = [(rows[i:i + B],) for i in range(0, len(rows), B)]
    out, t0 = [], time.time()
    if jobs <= 1:
        for k, t in enumerate(tasks, 1):
            out.extend(_worker(t))
            print('  %d/%d batches, %.0f s' % (k, len(tasks), time.time() - t0), flush=True)
    else:
        with mp.Pool(jobs) as pool:
            for k, r in enumerate(pool.imap_unordered(_worker, tasks), 1):
                out.extend(r)
                print('  %d/%d batches, %.0f s' % (k, len(tasks), time.time() - t0), flush=True)
    D = pd.DataFrame(out)
    # the WINDOW-TESTED frame is always written, pass or fail. A screen that
    # reports only its survivors cannot be audited when it returns zero.
    D.to_csv(os.path.join(ROOTOUT, 'gate2_inverse_windows.csv'), index=False)
    if not len(D):
        pd.DataFrame().to_csv(OUT, index=False)
        print('NO CANDIDATES', flush=True)
        return
    bad = (D.scored
           & (D.W1_exp < D.floor_p5) & (D.W2_exp < D.floor_p5) & (D.W3_exp < D.floor_p5)
           & (D.W1_n >= S.MIN_TRADES_PICK)
           & (D.W2_n >= S.MIN_TRADES_BLIND) & (D.W3_n >= S.MIN_TRADES_BLIND))
    C = D[bad].copy()
    # how far below: the WORST window's margin is the honest headline, because a
    # candidate is only as reliable as its least-bad episode.
    C['margin_worst_R'] = C.floor_p5 - C[['W1_exp', 'W2_exp', 'W3_exp']].max(axis=1)
    C['margin_blind_R'] = C.floor_p5 - C.expectancy_R
    C = C.sort_values('margin_worst_R', ascending=False).reset_index(drop=True)
    C.to_csv(OUT, index=False)
    print('\nCANDIDATES: %d of %d window-tested (%d failed the episode test)'
          % (len(C), len(D), len(D) - len(C)), flush=True)
    print('wrote %s' % os.path.basename(OUT), flush=True)
    return C


if __name__ == '__main__':
    main()
