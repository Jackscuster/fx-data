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
TWO MAPS. `main_v2` IS THE CURRENT ONE.
------------------------------------------------------------------------
    FIRES MORE   eligibility_rate = eligible / combinations
    WINS MORE    survival_rate    = survivors / ELIGIBLE     <-- the real one
    enrichment   survival_rate / the slice's base survival rate

Enrichment 1.0 is "behaves exactly like the slice average". The ordering is what
gate 2 uses, not the magnitude -- most of the survivor population is chance.

`main_v2` divides by the ELIGIBLE count, which the sweep now tallies per slot
option, so it is a statement about edge. `main` (--v1) is the original and
divides by ALL combinations, which folds "never traded enough to be scored"
together with "traded and failed"; an option that merely fires often looks
enriched on it. v1 is kept reachable only because the first priority ordering
was read from it, and a claim about how far the correction moved things has to
be checkable against what it moved from.

PER MODE, NEVER POOLED. Each signal-exit mode (GAUNTLET.md: A C1-flip, B
baseline-cross, C exit-indicator) is a different definition of when a trade
ends, so its survivors, its floor and its null are all its own. Modes A and B do
not use the exit slot at all and report it as unused rather than as flat.

Writes gate1_enrichment_slots_v2.csv, gate1_close_reasons.csv and
gate1_exit_reach.csv, each carrying a `mode` column.
"""
import glob
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


def load_tallies(mode):
    import glob
    d = S.mode_dir(mode)
    fs = sorted(glob.glob(os.path.join(d, 'tally_*.npz')))
    if not fs:
        raise SystemExit('no tally_*.npz in %s -- run the sweep for mode %s:\n'
                         '  python code/l2sweep.py --mode %s --jobs 8'
                         % (d, mode, mode))
    tot = None
    for f in fs:
        z = np.load(f)
        if tot is None:
            tot = {k: z[k].astype(np.int64).copy() for k in z.files}
        else:
            for k in z.files:
                tot[k] += z[k]
    return tot, len(fs)


def slot_enrichment_v2(T, opts, mode):
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
                    mode=mode, slice=sname, slot=slot, option=name,
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


def close_reasons(T, opts, mode):
    rows = []
    for sname, _, _ in S.SLICES:
        for pop in ('elig', 'surv'):
            v = T['rc_%s_%s' % (pop, sname)]
            n = int(v.sum())
            for code in range(len(v)):
                if v[code] == 0 and code == 0:
                    continue
                rows.append(dict(mode=mode, slice=sname, population=pop,
                                 reason=REASON_NAMES.get(code, str(code)),
                                 closes=int(v[code]),
                                 share_pct=100.0 * v[code] / n if n else np.nan))
    return pd.DataFrame(rows)


def exit_reach(T, opts, mode):
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
            rows.append(dict(mode=mode, slice=sname, exit_ind=name, closes=n,
                             exit_ind_closes=int(M[j][EXIT_IND]),
                             exit_ind_share_pct=100.0 * M[j][EXIT_IND] / n if n else np.nan))
    return pd.DataFrame(rows).sort_values(
        ['slice', 'exit_ind_share_pct'], ascending=[True, False]).reset_index(drop=True)


def main_v2(modes=None):
    """The corrected map, per exit mode. Each mode is a different trade
    definition, so nothing is pooled across them."""
    full = S.slot_options()
    modes = modes or [m for m in S.MODE_ORDER
                      if glob.glob(os.path.join(S.mode_dir(m), 'tally_*.npz'))]
    if not modes:
        raise SystemExit('no tallies for any mode yet')
    AE, AR, AX = [], [], []
    for mode in modes:
        opts = S.mode_opts(full, mode)
        T, nshard = load_tallies(mode)
        E = slot_enrichment_v2(T, opts, mode)
        R = close_reasons(T, opts, mode)
        X = exit_reach(T, opts, mode)
        AE.append(E); AR.append(R); AX.append(X)

        print('\n' + '#' * 78)
        print('# MODE %s -- %s   (%d shards, %s combinations)'
              % (mode, S.MODES[mode]['label'], nshard,
                 format(S.n_combos(opts), ',')))
        print('#' * 78)
        for sname, _, _ in S.SLICES:
            g = E[E['slice'] == sname]
            print('\n%s  --  base survival rate (of ELIGIBLE) %.4f%%'
                  % (sname.upper(), g.base_rate_pct.iloc[0]))
            for slot in S.SLOTS:
                sl = g[g['slot'] == slot]
                if len(sl) < 2:
                    print('  %-9s (unused in this mode)' % slot)
                    continue
                print('  %-9s spread %.2fx - %.2fx   (fires-more spread %.2fx - %.2fx)'
                      % (slot, sl.enrichment.min(), sl.enrichment.max(),
                         sl.enrichment_uncond.min(), sl.enrichment_uncond.max()))
                for r in pd.concat([sl.head(3), sl.tail(3)]).itertuples():
                    print('      %-40s elig %6.2f%%  win %6.3f%%  %5.2fx  (old %5.2fx)'
                          % (r.option, r.eligibility_rate_pct,
                             r.survival_rate_pct, r.enrichment,
                             r.enrichment_uncond))
            print('  HOW TRADES CLOSE (eligible combinations)')
            for r in R[(R['slice'] == sname) & (R.population == 'elig')] \
                    .sort_values('share_pct', ascending=False).itertuples():
                print('      %-18s %14s  %6.2f%%'
                      % (r.reason, format(r.closes, ','), r.share_pct))
    E = pd.concat(AE, ignore_index=True)
    R = pd.concat(AR, ignore_index=True)
    X = pd.concat(AX, ignore_index=True)
    E.to_csv(os.path.join(ROOTOUT, 'gate1_enrichment_slots_v2.csv'), index=False)
    R.to_csv(os.path.join(ROOTOUT, 'gate1_close_reasons.csv'), index=False)
    X.to_csv(os.path.join(ROOTOUT, 'gate1_exit_reach.csv'), index=False)
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
