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
    main()
