import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""IS THE TEAM REAL? Two tests the build itself cannot answer.

1. SELECTION HOLDOUT. The greedy search saw every day it was scored on, so its
   score is an in-sample number for the SELECTION, even though each member's
   settings were fixed beforehand. Re-run the whole search on 2016-2018 only,
   then score that team on 2019-2020, which the search never saw. If the held-
   out score collapses, the roster is a fit to the picking window.

2. RANDOM-TEAM NULL, two flavours, because they answer different questions:
   (a) 1,000 RANDOM teams of the same size drawn from the same passers. Asks
       whether the SEARCH added anything over drawing 25 names from a hat.
   (b) 200 GREEDY runs on YEAR-SHUFFLED data -- the same search, same field,
       but with calendar years permuted so any real cross-member timing
       structure is destroyed while each member's own return distribution is
       preserved. Asks whether the search is exploiting structure or noise.
   (a) alone is too weak: a greedy search will beat random draws even on noise.
"""
import json, time, argparse
import numpy as np, pandas as pd
import l2team as TM

SEED = 20260914


def score_on(A, cols, years, members, votes, dipb, dayb, rng, mask=None):
    w = np.zeros(len(cols))
    idx = {c: i for i, c in enumerate(cols)}
    for c in members:
        if c in idx:
            w[idx[c]] = votes[c]
    if mask is None:
        return TM.score_team(A, w, years, dipb, dayb, rng)
    return TM.score_team(A[mask], w, years[mask], dipb, dayb, rng)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--label', default='_W3ONLY_GATE2')
    ap.add_argument('--n-random', type=int, default=1000)
    # 200 GREEDY NULL RUNS COST 67 HOURS. Measured, not guessed: the real build
    # did 24,150 trials in 39 min, and one null run rebuilds a whole team from
    # empty -- about 20 min each. 25 runs cost 8.4 h and resolve a p-value to
    # 0.04, which is enough to say whether the real score sits outside the null
    # entirely. It is NOT enough to quote a precise p below 0.04, and the output
    # says so rather than implying more precision than 25 draws can carry.
    ap.add_argument('--n-greedy-null', type=int, default=25)
    a = ap.parse_args()
    t0 = time.time()
    rng = np.random.default_rng(SEED)
    idx = json.load(open(os.path.join(ROOTOUT, 'team_index%s.json' % a.label)))
    cands = TM.load_candidates()
    M, cols = TM.build_matrix(cands, mode='equity', jobs=4)
    years = M.index.year.values
    A = M.values
    out = {}
    for tag, o in idx.items():
        dipb = 3.6 if tag.startswith('team1') else 5.4
        dayb = 3.6
        real = score_on(A, cols, years, o['members'], o['votes'], dipb, dayb, rng)

        # ---- 1. SELECTION HOLDOUT
        pick = years <= 2018
        hold = years >= 2019
        log = []
        tm, vt, _, _ = TM.greedy(A[pick], cols, [], dipb, dayb, log, tag + '_pick',
                                 rng, years[pick], jobs=4)
        in_s = score_on(A, cols, years, tm, vt, dipb, dayb, rng, mask=pick)
        out_s = score_on(A, cols, years, tm, vt, dipb, dayb, rng, mask=hold)
        full_out = score_on(A, cols, years, o['members'], o['votes'],
                            dipb, dayb, rng, mask=hold)

        # ---- 2a. RANDOM TEAMS of the same size
        n = len(o['members'])
        rnd = []
        for i in range(a.n_random):
            pickc = list(rng.choice(cols, size=min(n, len(cols)), replace=False))
            v = {c: 1.0 for c in pickc}
            s = score_on(A, cols, years, pickc, v, dipb, dayb, rng)
            if s:
                rnd.append(s['score'])
        rnd = np.array(rnd)

        # ---- 2b. GREEDY on YEAR-SHUFFLED data
        gnull = []
        uy = np.unique(years)
        for i in range(a.n_greedy_null):
            perm = rng.permutation(uy)
            mapping = dict(zip(uy, perm))
            ysh = np.array([mapping[y] for y in years])
            order = np.argsort(ysh, kind='stable')
            lg = []
            tm2, vt2, res2, _ = TM.greedy(A[order], cols, [], dipb, dayb, lg,
                                          'null', rng, ysh[order],
                                          jobs=int(os.environ.get('TEAM_JOBS', '1')))
            if res2:
                gnull.append(res2['score'])
        gnull = np.array(gnull)

        out[tag] = dict(
            real_score=real['score'],
            holdout_pick_members=len(tm),
            holdout_in_sample=in_s['score'] if in_s else None,
            holdout_out_sample=out_s['score'] if out_s else None,
            full_team_on_holdout=full_out['score'] if full_out else None,
            random_n=len(rnd), random_mean=float(np.mean(rnd)) if len(rnd) else None,
            random_p95=float(np.percentile(rnd, 95)) if len(rnd) else None,
            random_max=float(np.max(rnd)) if len(rnd) else None,
            random_pctile_of_real=float(100.0 * (rnd < real['score']).mean()) if len(rnd) else None,
            greedy_null_n=len(gnull),
            greedy_null_mean=float(np.mean(gnull)) if len(gnull) else None,
            greedy_null_p95=float(np.percentile(gnull, 95)) if len(gnull) else None,
            greedy_null_max=float(np.max(gnull)) if len(gnull) else None,
            greedy_null_p_value=float((gnull >= real['score']).mean()) if len(gnull) else None,
            greedy_null_p_resolution=(round(1.0 / len(gnull), 3) if len(gnull) else None))
        print(tag, json.dumps(out[tag], indent=1, default=str), flush=True)
    pd.DataFrame(out).T.to_csv(os.path.join(ROOTOUT, 'team_checks%s.csv' % a.label))
    json.dump(out, open(os.path.join(ROOTOUT, 'team_checks%s.json' % a.label), 'w'),
              indent=1, default=str)
    print('DONE in %.1f min' % ((time.time() - t0) / 60), flush=True)


if __name__ == '__main__':
    main()
