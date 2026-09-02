import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""MODE A'S FINAL RECORD, and mode C's projection built from it.

Run when A finishes. Appends a dated section to GAUNTLET.md with A's MEASURED
per-combination rates, A-chop's crossing rate and leaderboard headline, and C's
projected cost derived from those rates rather than from mode B's.

THE ESTIMATOR IS THE CUMULATIVE AVERAGE, NOT THE RECENT CHUNKS. Recent-chunk
averages are biased FAST: fast chunks finish first, so at any moment the
completed set over-represents them. That bias produced a string of optimistic
ETAs earlier in this project -- 7h -> 26h -> 35h -> 53h on one job. Total
seconds divided by total combinations is the only estimator that cannot be
gamed by which chunks happen to have landed.
"""
import glob, json
import numpy as np, pandas as pd

WORKERS = 9          # what this 10-core machine sustains: 6 main + 3 reverse


def a_rates():
    d = pd.read_csv(os.path.join(ROOTOUT, 'gate2_progress_modeA.csv'))
    out = {}
    for s, g in d.groupby('slice'):
        out[s] = dict(combos=int(g.combos.sum()),
                      sec_per_combo=float(g.seconds.sum() / g.combos.sum()),
                      engine_h=float(g.seconds.sum() / 3600.0),
                      crossed=int(g.crossed_label.sum()))
        out[s]['cross_pct'] = 100.0 * out[s]['crossed'] / out[s]['combos']
    return out


def c_population():
    d = pd.read_csv(os.path.join(ROOTOUT, 'gate1_survivors_modeC.csv'),
                    low_memory=False, usecols=['slice'])
    return dict(d.groupby('slice').size())


def project(rates, pop, workers=WORKERS):
    rows, tot = [], 0.0
    for sl in ('trend', 'chop'):
        if sl not in rates or sl not in pop:
            continue
        eh = pop[sl] * rates[sl]['sec_per_combo'] / 3600.0
        tot += eh
        rows.append((sl, int(pop[sl]), rates[sl]['sec_per_combo'], eh,
                     eh / workers / 24.0))
    return rows, tot, tot / workers / 24.0


def headline():
    f = os.path.join(ROOTOUT, 'gate2_modeA_chop_leaderboard.csv')
    if not os.path.exists(f):
        return None
    L = pd.read_csv(f, low_memory=False).sort_values('rank')
    r = L.iloc[0]
    return dict(n=len(L), c1=r.c1, c2=r.c2, vol=r.vol, base=r.base,
                total_R=float(r.ex_total_R), sortino=float(r.ex_sortino),
                sharpe=float(r.ex_sharpe), dd=float(r.ex_max_dd_R),
                calmar=float(r.ex_calmar), n_tr=int(r.ex_n),
                exp=float(r.ex_expectancy_R), nos=float(r.net_of_structure_R))


def main():
    rates, pop = a_rates(), c_population()
    rows, tot, days = project(rates, pop)
    h = headline()
    sh = lambda x: str(x).replace('_signals', '').replace('_volume', '').replace('_baseline', '')
    L = []
    L.append('\n## MODE A FINAL, AND MODE C PROJECTED FROM IT\n')
    L.append('A ran `--sorted --cap 6 --seed-from B`, no disk cache. Rates are'
             ' MEASURED, total seconds over total combinations.\n')
    L.append('| slice | combinations | s/combination | engine-hours | crossing rate |')
    L.append('|---|---|---|---|---|')
    for sl in ('trend', 'chop'):
        if sl in rates:
            r = rates[sl]
            L.append('| %s | %s | **%.1f** | %.0f | **%.2f%%** |'
                     % (sl, format(r['combos'], ','), r['sec_per_combo'],
                        r['engine_h'], r['cross_pct']))
    if h:
        L.append('\n**A-chop leaderboard headline** — %d crossers ranked, '
                 'crisis-excluded co-equal rule. Rank 1: `%s x %s x %s x %s`, '
                 '%d blind trades, **%.2f R**, expectancy %.3f, Sortino %.2f, '
                 'Sharpe %.2f, maxDD %.2f, Calmar %.2f, net-of-structure %.3f.\n'
                 % (h['n'], sh(h['c1']), sh(h['c2']), sh(h['vol']), sh(h['base']),
                    h['n_tr'], h['total_R'], h['exp'], h['sortino'], h['sharpe'],
                    h['dd'], h['calmar'], h['nos']))
    L.append('\n### MODE C PROJECTED — from A\'s measured rates, cumulative average\n')
    L.append('**The estimator is total seconds over total combinations.** A'
             ' recent-chunks average is biased FAST -- fast chunks finish first,'
             ' so the completed set always over-represents them. That bias'
             ' produced a run of optimistic ETAs earlier in this project and is'
             ' not used here.\n')
    L.append('| slice | combinations | s/combination (from A) | engine-hours | days at %d workers |'
             % WORKERS)
    L.append('|---|---|---|---|---|')
    for sl, n, spc, eh, dd in rows:
        L.append('| %s | %s | %.1f | %s | **%.1f** |'
                 % (sl, format(n, ','), spc, format(int(eh), ','), dd))
    L.append('| **total** | **%s** | | **%s** | **%.1f** |'
             % (format(sum(r[1] for r in rows), ','), format(int(tot), ','), days))
    L.append('\n**That is %.1f days — roughly %.1f months — at full power on this'
             ' machine.** Mode C\'s population is %.0fx mode A\'s, and the '
             'per-combination cost is A\'s own, so the number is not a modelling'
             ' artefact: it is what this hardware does.\n'
             % (days, days / 30.44, sum(r[1] for r in rows) / 17922.0))
    L.append('The declared staged cheap/deep pass (`--staged`, +0.02R threshold)'
             ' is enabled and will cut this, but **by an unmeasured amount** --'
             ' neither A nor B ever ran staged, so there is no observed'
             ' cheap-pass saving to quote. Any figure below the table would be'
             ' invented. The first few hundred staged C combinations will'
             ' measure it, and this section gets amended with the real number'
             ' rather than a guess.\n')
    open(os.path.join(_R, 'GAUNTLET.md'), 'a').write('\n'.join(L) + '\n')
    json.dump(dict(rates=rates, pop={k: int(v) for k, v in pop.items()},
                   engine_hours=tot, days_at_workers=days, workers=WORKERS),
              open(os.path.join(ROOTOUT, 'modeC_projection.json'), 'w'), indent=1)
    print('\n'.join(L))
    print('\nwrote results/modeC_projection.json and appended to GAUNTLET.md')


if __name__ == '__main__':
    main()
