import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""GATE 1 SURVIVOR STRUCTURE — which slot options are enriched, and by how much.

WHAT THIS IS FOR, AND WHAT IT IS NOT FOR. GAUNTLET.md was amended so that no
combination is ever cut for the company it keeps: every gate 1 survivor advances
and is judged by the same walk-forward gates as everything else. This map sets
**tuning priority only** -- which families gate 2 works on first. Enrichment is
an ordering, never a permission. Nothing here removes anything.

------------------------------------------------------------------------
THE DENOMINATOR, AND WHY IT IS THE ONE IT IS
------------------------------------------------------------------------
Survival rate per option is computed out of ALL COMBINATIONS containing that
option, not out of the eligible ones. The enumeration is a full factorial, so
every option of a slot appears in exactly the same number of combinations --
n_combos / len(slot) -- which makes the denominator exact and free.

The eligible denominator is NOT available and cannot be reconstructed from the
survivors file: gate 1 tallied eligibility per slice, not per slot option, and
recovering it means re-running the 2.9-hour sweep. So the rate reported here
folds together two different ways of not surviving -- "never traded enough to be
scored" (below 100 picking / 50 per blind window) and "traded and failed".

That is stated rather than hidden, and for THIS purpose it is arguably the
right measure anyway: an option that cannot generate enough trades to be scored
is genuinely a lower tuning priority than one that scores and fails. But it is
not a claim about edge, and an option can look poor here purely for being quiet.

------------------------------------------------------------------------
ENRICHMENT
------------------------------------------------------------------------
    rate(option)      = survivors containing it / combinations containing it
    base rate (slice) = survivors / combinations
    enrichment        = rate / base rate

Enrichment 1.0 is "behaves exactly like the slice average". Above 1 means the
option is over-represented among survivors. Because the whole survivor
population is roughly 70% (trend) chance-level noise, a mild enrichment is
weak evidence; the ordering is what gate 2 uses, not the magnitude.

Writes results/gate1_enrichment_slots.csv and results/gate1_enrichment_cores.csv.
"""
import numpy as np, pandas as pd
import l2sweep as S

SLOTS = ('c1', 'c2', 'vol', 'base', 'exit_ind')
SURV = os.path.join(ROOTOUT, 'gate1_survivors.csv')


def load_survivors():
    if not os.path.exists(SURV):
        raise SystemExit(
            '%s is missing. It is gitignored (224 MB); regenerate with\n'
            '  python code/l2sweep.py --shards 128 --jobs 8\n'
            'which reuses any shard checkpoints still in results/gate1/.' % SURV)
    return pd.read_csv(SURV, usecols=list(SLOTS) + ['slice'])


def slot_enrichment(D, opts, n_total):
    """Per-option survival rate against the slice base rate."""
    rows = []
    for sname, _, _ in S.SLICES:
        g = D[D['slice'] == sname]
        base = len(g) / n_total
        for slot in SLOTS:
            k = len(opts[slot])
            per_option_combos = n_total / k          # exact: full factorial
            cnt = g[slot].value_counts()
            for name in opts[slot]:
                n = int(cnt.get(name, 0))
                rate = n / per_option_combos
                rows.append(dict(
                    slice=sname, slot=slot, option=name, survivors=n,
                    combos_with_option=int(per_option_combos),
                    survival_rate_pct=100.0 * rate,
                    base_rate_pct=100.0 * base,
                    enrichment=rate / base if base else np.nan))
    E = pd.DataFrame(rows)
    E = E.sort_values(['slice', 'slot', 'enrichment'], ascending=[True, True, False])
    return E.reset_index(drop=True)


def core_enrichment(D, opts, n_total):
    """C1 x BASELINE cores -- the entry confirmation paired with the trend
    filter it runs inside. This is the pair gate 2 tunes together, so it is the
    unit that priority is actually assigned to."""
    n_cores = len(opts['c1']) * len(opts['base'])
    per_core_combos = n_total / n_cores
    rows = []
    for sname, _, _ in S.SLICES:
        g = D[D['slice'] == sname]
        base = len(g) / n_total
        cnt = g.groupby(['c1', 'base']).size()
        for c1 in opts['c1']:
            for bl in opts['base']:
                n = int(cnt.get((c1, bl), 0))
                rate = n / per_core_combos
                rows.append(dict(
                    slice=sname, c1=c1, base=bl, survivors=n,
                    combos_in_core=int(per_core_combos),
                    survival_rate_pct=100.0 * rate,
                    base_rate_pct=100.0 * base,
                    enrichment=rate / base if base else np.nan))
    C = pd.DataFrame(rows)
    return C.sort_values(['slice', 'enrichment'], ascending=[True, False]).reset_index(drop=True)


# ==========================================================================
# THE CORRECTED MAP -- built from the per-option tallies, not the survivors file
# ==========================================================================
#
# The version above cannot separate FIRES MORE from WINS MORE, because its only
# denominator is "all combinations". The sweep now tallies the eligible count
# per option, which splits the two cleanly:
#
#   eligibility_rate  = eligible / combinations      -- how often it can trade
#   survival_rate     = survivors / ELIGIBLE         -- how often it wins, GIVEN
#                                                       it traded enough to be
#                                                       scored
#
# The second is the one that means anything about edge, and it is the one gate
# 2's priority order is taken from. The first is reported beside it because a
# large gap between them is itself informative: an option enriched on the old
# map but flat on the new one was never good, only busy.
REASON_NAMES = {0: '(unset)', 1: 'stop', 2: 'target', 3: 'exit indicator',
                4: 'baseline cross', 5: 'c1 flip', 6: 'reversal',
                7: 'end of data', 8: 'breakeven stop', 9: 'trail stop'}


def load_tallies():
    import glob
    fs = sorted(glob.glob(os.path.join(S.CKDIR, 'tally_*.npz')))
    if not fs:
        raise SystemExit('no tally_*.npz in %s -- re-run the sweep with the '
                         'instrumented worker:\n'
                         '  python code/l2sweep.py --shards 128 --jobs 8' % S.CKDIR)
    tot = None
    for f in fs:
        z = np.load(f)
        if tot is None:
            tot = {k: z[k].astype(np.int64).copy() for k in z.files}
        else:
            for k in z.files:
                tot[k] += z[k]
    return tot, len(fs)


def slot_enrichment_v2(T, opts):
    rows = []
    for sname, _, _ in S.SLICES:
        tot_elig = int(T['elig_%s_%s' % (sname, 'c1')].sum())
        tot_surv = int(T['surv_%s_%s' % (sname, 'c1')].sum())
        base = tot_surv / tot_elig if tot_elig else np.nan
        for slot in S.SLOTS:
            comb = T['comb_%s_%s' % (sname, slot)]
            elig = T['elig_%s_%s' % (sname, slot)]
            surv = T['surv_%s_%s' % (sname, slot)]
            for j, name in enumerate(opts[slot]):
                cond = surv[j] / elig[j] if elig[j] else np.nan
                rows.append(dict(
                    slice=sname, slot=slot, option=name,
                    combos=int(comb[j]), eligible=int(elig[j]),
                    survivors=int(surv[j]),
                    eligibility_rate_pct=100.0 * elig[j] / comb[j] if comb[j] else np.nan,
                    survival_rate_pct=100.0 * cond,
                    base_rate_pct=100.0 * base,
                    enrichment=cond / base if base else np.nan,
                    enrichment_uncond=((surv[j] / comb[j]) / (tot_surv / int(comb.sum()))
                                       if comb[j] else np.nan)))
    E = pd.DataFrame(rows)
    return E.sort_values(['slice', 'slot', 'enrichment'],
                         ascending=[True, True, False]).reset_index(drop=True)


def close_reasons(T, opts):
    rows = []
    for sname, _, _ in S.SLICES:
        for pop in ('elig', 'surv'):
            v = T['rc_%s_%s' % (pop, sname)]
            n = int(v.sum())
            for code in range(len(v)):
                if v[code] == 0 and code == 0:
                    continue
                rows.append(dict(slice=sname, population=pop,
                                 reason=REASON_NAMES.get(code, str(code)),
                                 closes=int(v[code]),
                                 share_pct=100.0 * v[code] / n if n else np.nan))
    return pd.DataFrame(rows)


def exit_reach(T, opts):
    """Per exit_ind option: what share of closes it actually causes. If this is
    small everywhere, the exit slot's flat enrichment is STRUCTURAL -- the other
    exits fire first and leave it nothing to do -- rather than evidence that the
    choice of exit indicator does not matter."""
    rows = []
    EXIT_IND = 3
    for sname, _, _ in S.SLICES:
        M = T['rc_by_exit_%s' % sname]
        for j, name in enumerate(opts['exit_ind']):
            n = int(M[j].sum())
            rows.append(dict(slice=sname, exit_ind=name, closes=n,
                             exit_ind_closes=int(M[j][EXIT_IND]),
                             exit_ind_share_pct=100.0 * M[j][EXIT_IND] / n if n else np.nan))
    return pd.DataFrame(rows).sort_values(
        ['slice', 'exit_ind_share_pct'], ascending=[True, False]).reset_index(drop=True)


def main_v2():
    opts = S.slot_options()
    T, nshard = load_tallies()
    print('tallies from %d shards' % nshard)

    E = slot_enrichment_v2(T, opts)
    E.to_csv(os.path.join(ROOTOUT, 'gate1_enrichment_slots_v2.csv'), index=False)
    R = close_reasons(T, opts)
    R.to_csv(os.path.join(ROOTOUT, 'gate1_close_reasons.csv'), index=False)
    X = exit_reach(T, opts)
    X.to_csv(os.path.join(ROOTOUT, 'gate1_exit_reach.csv'), index=False)

    for sname, _, _ in S.SLICES:
        g = E[E['slice'] == sname]
        print('\n' + '=' * 78)
        print('%s  --  base survival rate (of ELIGIBLE) %.4f%%'
              % (sname.upper(), g.base_rate_pct.iloc[0]))
        print('=' * 78)
        for slot in S.SLOTS:
            s = g[g['slot'] == slot]
            print('\n  %-9s spread %.2fx - %.2fx   (old map: %.2fx - %.2fx)'
                  % (slot, s.enrichment.min(), s.enrichment.max(),
                     s.enrichment_uncond.min(), s.enrichment_uncond.max()))
            print('      %-40s %8s %8s %7s %7s'
                  % ('option', 'elig%', 'win%', 'enr', 'old'))
            for r in pd.concat([s.head(3), s.tail(3)]).itertuples():
                print('      %-40s %7.2f%% %7.3f%% %6.2fx %6.2fx'
                      % (r.option, r.eligibility_rate_pct, r.survival_rate_pct,
                         r.enrichment, r.enrichment_uncond))
        print('\n  HOW TRADES CLOSE (eligible combinations)')
        for r in R[(R['slice'] == sname) & (R.population == 'elig')] \
                .sort_values('share_pct', ascending=False).itertuples():
            print('      %-18s %14s  %6.2f%%' % (r.reason, format(r.closes, ','), r.share_pct))
        x = X[X['slice'] == sname]
        print('  exit-indicator share of closes, by exit option: '
              '%.2f%% - %.2f%%' % (x.exit_ind_share_pct.min(), x.exit_ind_share_pct.max()))
    return E, R, X


def main():
    opts = S.slot_options()
    n_total = S.n_combos(opts)
    D = load_survivors()
    print('survivors %s, combinations %s' % (format(len(D), ','), format(n_total, ',')))

    E = slot_enrichment(D, opts, n_total)
    E.to_csv(os.path.join(ROOTOUT, 'gate1_enrichment_slots.csv'), index=False)
    C = core_enrichment(D, opts, n_total)
    C.to_csv(os.path.join(ROOTOUT, 'gate1_enrichment_cores.csv'), index=False)

    for sname, _, _ in S.SLICES:
        g = E[E['slice'] == sname]
        print('\n' + '=' * 72)
        print('%s  --  base rate %.4f%%' % (sname.upper(), g.base_rate_pct.iloc[0]))
        print('=' * 72)
        for slot in SLOTS:
            s = g[g['slot'] == slot]
            print('\n  %s  (%d options)   spread %.2fx - %.2fx'
                  % (slot, len(s), s.enrichment.min(), s.enrichment.max()))
            top = s.head(3)[['option', 'survival_rate_pct', 'enrichment']]
            bot = s.tail(3)[['option', 'survival_rate_pct', 'enrichment']]
            for r in top.itertuples():
                print('    + %-28s %7.3f%%  %5.2fx' % (r.option, r.survival_rate_pct, r.enrichment))
            print('    ...')
            for r in bot.itertuples():
                print('    - %-28s %7.3f%%  %5.2fx' % (r.option, r.survival_rate_pct, r.enrichment))
        c = C[C['slice'] == sname]
        print('\n  C1 x BASELINE cores  (%d)   spread %.2fx - %.2fx'
              % (len(c), c.enrichment.min(), c.enrichment.max()))
        print('    dead cores (zero survivors): %d' % int((c.survivors == 0).sum()))
        for r in c.head(5).itertuples():
            print('    + %-26s x %-22s %6.3f%%  %5.2fx'
                  % (r.c1, r.base, r.survival_rate_pct, r.enrichment))
        for r in c.tail(3).itertuples():
            print('    - %-26s x %-22s %6.3f%%  %5.2fx'
                  % (r.c1, r.base, r.survival_rate_pct, r.enrichment))
    return E, C


if __name__ == '__main__':
    # v2 is the corrected map and is the default once tallies exist. The v1
    # path is kept reachable because its output is what the first priority
    # ordering was read from, and a claim about how much the correction moved
    # things has to be checkable against the thing it moved from.
    if '--v1' in sys.argv:
        main()
    else:
        main_v2()
