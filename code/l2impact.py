import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""PARAMETER RESPONSE — which knobs actually move the score, measured.

GAUNTLET.md gate 2 caps tuning at each indicator's SIX HIGHEST-IMPACT
parameters and gives the cheap pass THE SINGLE MOST IMPACTFUL parameter of each
indicator. Both need a ranking, and a ranking asserted from the indicator's
documentation is a guess. This measures it.

------------------------------------------------------------------------
WHAT IS MEASURED, AND ON WHAT
------------------------------------------------------------------------
For one parameter of one indicator: hold everything else at defaults, sweep that
parameter across its full grid, and record the SPREAD of tuning-window
expectancy it produces --

    response = max(expectancy over the grid) - min(expectancy over the grid)

averaged over a sample of real gate 1 survivor combinations that name the
indicator. A parameter that cannot move the score is not worth a knob-pass; a
parameter that moves it a lot is.

MEASURED ON W1 ONLY. W1 is the picking window and is the window the tuner is
allowed to look at. Ranking knobs on a blind window would leak it into every
tuning decision downstream, which is the same mistake as tuning on it.

THE RANKING IS FROZEN BEFORE MODE C RUNS. It is an input to the search, so
re-deriving it later against C's own results would make the cap circular.

------------------------------------------------------------------------
WHY THE SPREAD RATHER THAN THE BEST VALUE
------------------------------------------------------------------------
The best value is what tuning finds; the SPREAD is what tuning has to work with.
Two parameters can both have a best value that beats the default, but if one
moves expectancy by 0.001R across its whole range it will never survive the
adopt-only-if-it-beats-the-default rule in a way that matters, and spending a
twelfth of the budget on it is waste.

Writes results/gate2_param_impact.csv -- one row per (indicator, parameter).
"""
import glob, json, time
import numpy as np, pandas as pd

import l2sweep as S
import l2tune as T

OUT = os.path.join(ROOTOUT, 'gate2_param_impact.csv')
N_SAMPLE = 12          # combinations per indicator
SEED = 4242


def _pool(mode='B'):
    """Real survivor combinations, so the response is measured on the
    population the cap will actually be applied to."""
    fr = []
    for m in ('B', 'A', 'C'):
        f = os.path.join(ROOTOUT, 'gate1_survivors_mode%s.csv' % m)
        if os.path.exists(f):
            d = pd.read_csv(f, usecols=['c1', 'c2', 'vol', 'base',
                                        'exit_ind', 'slice', 'mode'])
            fr.append(d)
    D = pd.concat(fr, ignore_index=True)
    # modes A and B record exit_ind='unused' because the slot is not read in
    # those modes. It is not an indicator name and must not reach the registry;
    # substitute the placeholder the sweep itself passed.
    ph = S.slot_options()['exit_ind'][0]
    D['exit_ind'] = D['exit_ind'].replace('unused', ph).fillna(ph)
    return D


def _worker(args):
    name, slot_of, combos, mode, sname = args
    reg = T.registry()
    params = reg[name]
    if not params:
        return []
    code = dict((s, c) for s, _, c in S.SLICES)[sname]
    plan = dict((s, p) for s, p, _ in S.SLICES)[sname]
    sc = T.Scorer()
    drisk = dict(atr_len=S.ATR_LEN, atr_mult=S.ATR_MULT, tp_mult=S.TP_MULT,
                 trail_mult=S.TRAIL_MULT, trail_arm=S.TRAIL_ARM,
                 be_pct=S.BE_PCT)
    rows = []
    for pname, pdef in sorted(params.items()):
        grid = T.ind_param_grid(pdef)
        if len(grid) < 2:
            rows.append(dict(indicator=name, parameter=pname, default=pdef,
                             grid_points=len(grid), response_R=0.0,
                             n_combos=0, note='single-point grid'))
            continue
        spreads, movers = [], 0
        for cb in combos:
            ip = {k: dict(reg[n]) for k, n in
                  zip(('c1', 'c2', 'vol', 'base', 'exit_ind'), cb)}
            vals = []
            for v in grid:
                ip[slot_of][pname] = v
                r = sc.score(cb, ip, drisk, mode, sname, code, plan, ('W1',))
                a = r['W1']
                if a is not None and a['n'] >= S.MIN_TRADES_PICK:
                    vals.append(a['expectancy_R'])
            if len(vals) >= 2:
                spreads.append(max(vals) - min(vals))
                movers += 1
        rows.append(dict(indicator=name, parameter=pname, default=pdef,
                         grid_points=len(grid),
                         response_R=float(np.mean(spreads)) if spreads else 0.0,
                         response_max_R=float(np.max(spreads)) if spreads else 0.0,
                         n_combos=movers, note=''))
    return rows


def measure(jobs=None, n_sample=N_SAMPLE):
    import multiprocessing as mp
    reg = T.registry()
    D = _pool()
    rng = np.random.default_rng(SEED)
    tasks = []
    for slot, col in (('c1', 'c1'), ('c2', 'c2'), ('vol', 'vol'),
                      ('base', 'base'), ('exit_ind', 'exit_ind')):
        for name in sorted(set(D[col].dropna())):
            if not reg.get(name):
                continue
            sub = D[(D[col] == name) & (D['slice'] == 'trend')]
            if len(sub) == 0:
                sub = D[D[col] == name]
            if len(sub) == 0:
                continue
            take = sub.sample(min(n_sample, len(sub)), random_state=SEED)
            combos = [(r.c1, r.c2, r.vol, r.base, r.exit_ind)
                      for r in take.itertuples()]
            tasks.append((name, slot, combos, 'C', 'trend'))
    jobs = jobs or max(1, (os.cpu_count() or 2) - 2)
    print('response: %d (indicator, slot) tasks, %d workers' % (len(tasks), jobs),
          flush=True)
    out = []
    with mp.Pool(jobs) as pool:
        for i, rows in enumerate(pool.imap_unordered(_worker, tasks)):
            out.extend(rows)
            if (i + 1) % 10 == 0:
                print('  %d/%d indicators done' % (i + 1, len(tasks)), flush=True)
    R = pd.DataFrame(out)
    if len(R):
        # A confirmation indicator is measured TWICE -- once as a C1 and once as
        # a C2 -- because it appears in both menus. Those are two samples of the
        # same parameter's response, not two parameters, and leaving them
        # separate duplicated every confirmation parameter in the ranking and
        # made the cap keep six SLOTS where it should keep six PARAMETERS.
        R = (R.groupby(['indicator', 'parameter'], as_index=False)
               .agg(default=('default', 'first'),
                    grid_points=('grid_points', 'max'),
                    response_R=('response_R', 'mean'),
                    response_max_R=('response_max_R', 'max'),
                    n_combos=('n_combos', 'sum'),
                    note=('note', 'first'),
                    n_measurements=('response_R', 'size')))
        R['rank_in_indicator'] = (R.groupby('indicator')['response_R']
                                  .rank(ascending=False, method='first').astype(int))
        R['in_cap6'] = R.rank_in_indicator <= 6
        R['is_top1'] = R.rank_in_indicator == 1
        R = R.sort_values(['indicator', 'rank_in_indicator'])
        R.to_csv(OUT, index=False)
    return R


def load_ranking():
    """{indicator: [parameters, most impactful first]}. Falls back to
    alphabetical only if the measurement has not been run, and says so."""
    if not os.path.exists(OUT):
        raise SystemExit('%s missing -- run: python code/l2impact.py' % OUT)
    R = pd.read_csv(OUT)
    d = {}
    for name, g in R.sort_values('rank_in_indicator').groupby('indicator'):
        d[name] = list(g.parameter)
    return d


def main():
    a = sys.argv[1:]
    jobs = int(a[a.index('--jobs') + 1]) if '--jobs' in a else None
    ns = int(a[a.index('--sample') + 1]) if '--sample' in a else N_SAMPLE
    t = time.time()
    R = measure(jobs=jobs, n_sample=ns)
    print('\n%d (indicator, parameter) rows in %.0f s' % (len(R), time.time() - t))
    big = R[R.groupby('indicator')['parameter'].transform('size') > 6]
    if len(big):
        print('\nINDICATORS ABOVE THE CAP -- what the cap keeps and drops:')
        for name, g in big.groupby('indicator'):
            keep = list(g[g.in_cap6].parameter)
            drop = list(g[~g.in_cap6].parameter)
            print('  %s (%d params)' % (name, len(g)))
            print('     keep: %s' % ', '.join(keep))
            print('     drop: %s' % ', '.join(drop[:8])
                  + (' ...' if len(drop) > 8 else ''))
    print('\nTOP-1 PARAMETER PER INDICATOR (the cheap pass knob), '
          'highest response first:')
    t1 = R[R.is_top1].sort_values('response_R', ascending=False)
    print(t1[['indicator', 'parameter', 'default', 'response_R',
              'n_combos']].head(20).to_string(index=False))
    print('\nparameters whose response is ZERO (never move the score): %d of %d'
          % (int((R.response_R == 0).sum()), len(R)))
    return R


if __name__ == '__main__':
    main()
