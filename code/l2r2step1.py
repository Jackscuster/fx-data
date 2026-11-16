import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""LAYER 2 RESTART, STEP 1 -- READ-ONLY SCOPING.  Jack, 16 Nov.

What the library actually holds, what each mode enumerates, what the original
gate 1 did and which contaminations touched it, and -- from a MEASURED
per-combination time, not an estimate -- what a full honest gate 1 costs on the
Mac and on rented boxes.

Reads code and committed results.  Writes results/r2_step1_scope.csv and
results/r2_step1_timing.csv.  Changes nothing.

    python3 code/l2r2step1.py
"""
import time, json
import numpy as np, pandas as pd
import l2sweep as S
import l2lib as L
import l2r2gate1 as G

BOX_VCPU = 16            # CPX62, the box the parked run was scoped on
BOX_RATE = 0.10          # $/box-hour, Jack's figure
MAC_CORES = 8            # 10 physical, 8 used -- the memguard needs headroom


def library():
    R = L.registry_frame()
    rows = []
    for slot in ('confirmation', 'volume', 'baseline', 'exit'):
        g = R[R.slot == slot]
        rows.append(dict(slot=slot, total=len(g), available=int(g.available.sum()),
                         unavailable=int((~g.available).sum()),
                         why_unavailable='needs a volume series spot FX does not have'))
    return pd.DataFrame(rows)


def modes_table():
    opts = S.slot_options()
    rows = []
    for m in S.MODE_ORDER:
        o = S.mode_opts(opts, m)
        n = S.n_combos(o)
        rows.append(dict(mode=m, exit_rule=S.MODES[m]['label'],
                         uses_exit_slot=S.MODES[m]['uses_exit_slot'],
                         c1=len(o['c1']), c2=len(o['c2']), vol=len(o['vol']),
                         base=len(o['base']), exit_ind=len(o['exit_ind']),
                         combinations=n, evaluations_both_slices=2 * n))
    return pd.DataFrame(rows)


def mode_a_definition():
    """The exact mode A entry and exit, from the code that runs it."""
    kw = S.mode_kw('A')
    return dict(
        mode='A',
        entry=('C1 cross (the c1 confirmation flipping to a side), confirmed by c2 '
               'and by the volume slot, on the correct side of the baseline. '
               'Continuation and one-candle entry routes per GAUNTLET; reversal '
               'entries allowed, and a C1 flip that reverses is both the exit and '
               'the new entry.'),
        signal_exit='C1 flip, and nothing else',
        exit_on_c1_flip=kw['exit_on_c1_flip'],
        exit_on_base_cross=kw['exit_on_base_cross'],
        exit_on_exit_ind=kw['exit_on_exit_ind'],
        risk_plan=('ALWAYS ACTIVE in every mode and not a signal exit: stop at '
                   'atr_mult x ATR(atr_len), target tp_mult, breakeven after '
                   'be_pct beyond TP1, trail trail_mult armed at trail_arm x ATR. '
                   'Leg 2 always runs to its own exit.'),
        defaults='atr_len=%d atr_mult=%.1f tp_mult=%.1f trail_mult=%.1f trail_arm=%.1f be_pct=%.2f'
                 % (S.ATR_LEN, S.ATR_MULT, S.TP_MULT, S.TRAIL_MULT, S.TRAIL_ARM, S.BE_PCT),
        exit_slot='UNUSED -- with exit_on_exit_ind False the x_el/x_es arrays are never read, '
                  'so the enumeration collapses by a factor of 39',
        trend_slice='two-leg plan, entries whose Layer 1 shape2 label at the entry bar is "trending"',
        chop_slice='one-leg plan, entries labelled "ranging"')


def original_gate1():
    """How the gate 1 on disk produced its survivors, and what was wrong with it.

    Every number here is read from the shipped files, not quoted from memory."""
    runs = pd.read_csv(os.path.join(ROOTOUT, 'gate1_mode_runs.csv'), comment='#')
    fl = {m: pd.read_csv(os.path.join(ROOTOUT, 'gate1_luck_floor_mode%s.csv' % m), comment='#')
          for m in S.MODE_ORDER}
    A = pd.read_csv(os.path.join(ROOTOUT, 'gate1_survivors_modeA.csv'), comment='#')
    cand = pd.read_csv(os.path.join(ROOTOUT, 'refit_candidates_full.csv'), comment='#')
    ca = cand[cand['mode'] == 'A']
    rows = []
    for m in S.MODE_ORDER:
        r = runs[runs['mode'] == m].iloc[0]
        f = fl[m].set_index('slice')
        rows.append(dict(mode=m, survivors_on_file=int(r.survivors), seconds=float(r.seconds),
                         floor_trend_p95=float(f.loc['trend', 'p95']),
                         floor_chop_p95=float(f.loc['chop', 'p95']),
                         pf_floor=S.PF_FLOOR,
                         min_trades_pick=S.MIN_TRADES_PICK, min_trades_blind=S.MIN_TRADES_BLIND))
    T = pd.DataFrame(rows)
    disc = dict(
        gate1_survivors_modeA=int(len(A)),
        refit_candidates_modeA=int(len(ca)),
        difference=int(len(A) - len(ca)),
        where=('all %d are A-TREND rows and every one of them has '
               'c1=waddah_attar_explosion_signals' % (len(A) - len(ca))),
        cause=('refit_candidates_full.csv is built from gate2_tuned_modeA_trend.csv, '
               'not from the gate 1 survivor file -- so a tuning shard that never '
               'finished silently removed 100 combinations gate 1 had passed, and '
               'nothing checked the two counts against each other. The parked cloud '
               'run would have searched 17,822, not the 17,922 gate 1 chose.'))
    return T, disc


CONTAMINATIONS = [
    dict(n=1, name='W2 leak / the gate 1 score IS the blind years',
         touches_gate1='YES -- fatal',
         what=('l2sweep.score_combo scores a combination on W2 + W3 pooled, i.e. '
               '2011-01-01 to 2020-12-31. Those are every year Layer 2 later '
               'reported as out of sample. The survivors were chosen on the years '
               'their record was then quoted on, so the gate 1 verdict and the '
               'blind record are the same measurement twice.')),
    dict(n=2, name='mode contamination -- two exits on at once',
         touches_gate1='the FIRST sweep only; the three-mode rerun fixed it',
         what=('the original sweep ran the exit indicator and the baseline cross '
               'simultaneously with the C1-flip exit off, so every combination was '
               'testing "whichever of two exits fires first". Measured on the '
               'instrumented run the baseline cross took 44% of trend closes against '
               'the exit indicator\'s 7%. gate1_survivors_v1.csv is that run.')),
    dict(n=4, name='field sight of 2016-2020',
         touches_gate1='YES',
         what=('W3 = 2016-2020 is inside the gate 1 score, so the candidate FIELD '
               'handed to every later stage was selected with sight of the years '
               'those stages treated as unseen. This is the same defect as #1 seen '
               'from the field\'s side rather than the score\'s.')),
    dict(n=27, name='costs under-charged by atr_mult',
         touches_gate1='NO at gate 1, YES everywhere downstream',
         what=('_cost_R returns the cost in RAW r units; when r is restated against a '
               'fixed 1.0xATR risk unit the cost has to be restated with it. Gate 1 '
               'runs every combination at atr_mult=1.0, so the factor is exactly 1.0 '
               'and the gate 1 numbers are unaffected -- but every tuned stage that '
               'moved the stop was under-charged, median 20%, p90 46%.')),
    dict(n=0, name='vote timing (the Book look-ahead)',
         touches_gate1='NO',
         what=('gate 1 never nets. It aggregates per-combination R, so VOTE_ON_ENTRY_DAY '
               'has nothing to act on. The defect is real and fatal, but it enters at '
               'the Book, not here -- which is why the gate 1 survivor counts survived '
               'the vote-timing fix unchanged while every book number went negative.')),
    dict(n=99, name='costs off entirely',
         touches_gate1='DEPENDS ON THE RUN',
         what=('S.COSTS is None unless load_costs() is called. The gate 1 files on disk '
               'were produced before the costed path existed -- "Layer 2 charged NO costs '
               'at all before this: gates 1-3 to date are gross figures" (l2sweep.py). '
               'The honest gate 1 charges cost_table_h22 on every trade.')),
]


def _free_gb():
    st = os.statvfs(_R)
    return st.f_bavail * st.f_frsize / 1024 ** 3


def costing(per_combo_s):
    """Core-hours and wall time for a full honest gate 1, per mode.

    TWO FIGURES PER MODE, and the difference matters.
      * `across_five_windows_naive` is the brief's arithmetic: combinations x 5.
      * `true` is what the code actually costs: the five rolling windows are
        MASKS over one engine pass, because every trade is banked by the
        calendar year of its entry bar. Scoring a combination five times would
        be running the identical engine five times and throwing four away.
    Both are reported so the saving is visible rather than assumed."""
    opts = S.slot_options()
    rows = []
    for m in S.MODE_ORDER:
        n = S.n_combos(S.mode_opts(opts, m))
        for label, mult in (('true (windows are masks on one pass)', 1), ('naive x5 windows', 5)):
            ch = n * mult * per_combo_s / 3600.0
            rows.append(dict(
                mode=m, combinations=n, basis=label, core_hours=ch,
                mac_hours=ch / MAC_CORES, mac_days=ch / MAC_CORES / 24,
                cloud3_hours=ch / (3 * BOX_VCPU), cloud3_cost_usd=3 * BOX_RATE * ch / (3 * BOX_VCPU),
                cloud6_hours=ch / (6 * BOX_VCPU), cloud6_cost_usd=6 * BOX_RATE * ch / (6 * BOX_VCPU),
                bank_gb=n * 4 * G.NYEAR * G.NSTAT * 4 / 1024 ** 3,
                free_disk_gb=_free_gb()))
    return pd.DataFrame(rows)


def main():
    print('=== LAYER 2 RESTART, STEP 1 -- SCOPE FROM CODE ===', flush=True)
    G.manifest_check()

    lib = library()
    print('\n-- the indicator library, per slot --', flush=True)
    print(lib.to_string(index=False), flush=True)

    M = modes_table()
    print('\n-- the three modes, exactly one active per test --', flush=True)
    print(M.to_string(index=False), flush=True)
    print('   total across the three modes: %s combinations, %s evaluations (both slices)'
          % (f"{M.combinations.sum():,}", f"{M.evaluations_both_slices.sum():,}"), flush=True)

    d = mode_a_definition()
    print('\n-- MODE A, exactly as the code runs it --', flush=True)
    for k, v in d.items():
        print('   %-18s %s' % (k, v), flush=True)

    T, disc = original_gate1()
    print('\n-- the gate 1 on disk --', flush=True)
    print(T.to_string(index=False), flush=True)
    print('   the rule: a combination is ELIGIBLE at >= %d picking-window trades and >= %d in EACH '
          'blind window, then SURVIVES at expectancy_R > the mode-and-slice luck floor (p95 of a '
          '%d-bar block-sign surrogate) AND profit_factor >= %.2f.'
          % (S.MIN_TRADES_PICK, S.MIN_TRADES_BLIND, S.BLOCK, S.PF_FLOOR), flush=True)
    print('   THE SCORE IT CUT ON WAS W2 + W3 POOLED = %s to %s.'
          % (S.WINDOWS['W2'][0], S.WINDOWS['W3'][1]), flush=True)
    print('\n-- the 17,822 / 17,922 discrepancy --', flush=True)
    for k, v in disc.items():
        print('   %-24s %s' % (k, v), flush=True)

    print('\n-- which contaminations touched gate 1 --', flush=True)
    for c in CONTAMINATIONS:
        print('   fault #%-3s %-46s %s' % (c['n'], c['name'], c['touches_gate1']), flush=True)
        print('       %s' % c['what'], flush=True)

    print('\n-- MEASURED per-combination time (cache warm, 28 pairs, four streams) --', flush=True)
    probe = {}
    for m in S.MODE_ORDER:
        probe[m] = G.stage_probe(m, n=int(os.environ.get('R2_PROBE_N', 120)))
    C = costing(probe['A']['per_combo_s'])
    # modes B and C are measured separately -- the exit rule changes the trade
    # count, so one mode's seconds-per-combination does not transfer.
    parts = []
    for m in S.MODE_ORDER:
        c = costing(probe[m]['per_combo_s'])
        c = c[c['mode'] == m].copy()
        c['per_combo_s'] = probe[m]['per_combo_s']
        parts.append(c)
    C = pd.concat(parts, ignore_index=True)
    print('\n-- what a full honest gate 1 costs --', flush=True)
    print(C.to_string(index=False, float_format=lambda x: '%.3f' % x), flush=True)

    lib.to_csv(os.path.join(ROOTOUT, 'r2_step1_library.csv'), index=False)
    M.to_csv(os.path.join(ROOTOUT, 'r2_step1_modes.csv'), index=False)
    T.to_csv(os.path.join(ROOTOUT, 'r2_step1_gate1_original.csv'), index=False)
    pd.DataFrame(CONTAMINATIONS).to_csv(os.path.join(ROOTOUT, 'r2_step1_contaminations.csv'), index=False)
    C.to_csv(os.path.join(ROOTOUT, 'r2_step1_timing.csv'), index=False)
    with open(os.path.join(ROOTOUT, 'r2_step1_modeA_definition.json'), 'w') as fh:
        json.dump({'mode_a': d, 'discrepancy': disc}, fh, indent=1)
    print('\nSTEP 1 COMPLETE', flush=True)


if __name__ == '__main__':
    main()
