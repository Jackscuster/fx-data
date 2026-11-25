import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""SOURCE 1 — THE SIX PUBLISHED NNFX COMBINATIONS, ZERO SEARCH. HANDOFF 0o.

N1 to N6 from the 9 November research catalogue
(results/research/RESEARCH_2026-11-09_part2_regime_taxonomies_and_nnfx_catalog.md,
section 2.3), at their PUBLISHED settings, through PROTOCOL.md unchanged.

WHY THESE SIX AND NOT A SEARCH. They were chosen by people who traded them for
years and written down before any result of ours existed. That makes them
declared constructions in the project's Rule 10 sense: the only multiple-
comparison correction they need is best-of-6, not best-of-45,139. If one of
them beats what the search found, the search bought nothing. If none does, the
search is vindicated on its own terms. Either answer is worth the compute.

WHAT THE CATALOGUE ITSELF SAYS ABOUT THEM, AND IT MATTERS. All six are grade
N -- "named components only, no settings, no results". Not one published NNFX
combination anywhere comes with data that can be re-run (grade V: nothing
found). The two self-reported multi-year backtests that exist point opposite
ways -- myfxbook 33% a year on 2017-2019, babypips -129% on 2014-2016 -- and
neither is reproducible. So this is not a replication of a known result. It is
the first time any of them has been tested on eleven years of 28 pairs with
costs, a leverage cap and realistic gap fills.

SETTINGS: ONE INDICATOR ADDED, ONE SET OF OVERRIDES, ONE DECLARED CHOICE.
  added      kijun_baseline (Kijun-sen 26), N1's declared baseline and the one
             indicator in the whole catalogue the library did not carry. Unit
             tested in l2lib.main() two ways: an arithmetic reference, and
             identity with the project's own parity-proven ichimoku base line
             on 5,844 EURUSD bars (max |diff| 0.0e+00).
  overridden schaff_trend_cycle 12/26/10 with bands 65/35, which is what N3
             publishes; the library's default is 23/50/10 with 75/25.
  declared   N5 publishes "EMA 20-30", a RANGE, not a setting. 25 is used, the
             midpoint, and it is written here because a range is not a
             published setting and pretending otherwise would be a choice
             disguised as a citation. The nudge gate moves it to 12 and 50
             anyway, which covers the whole published range and more.

Every other setting in all six candidates is already the library's Pine
default and is identical to what the catalogue states -- checked value by
value against section 2.3, not assumed.

FAULTS THIS FILE FOUND IN ITSELF
  1. The first run reported six candidates with IDENTICAL trade counts. The
     cause was nnfxproto.slot_arrays caching on (pair, name) without the
     params; it is fixed there, and the guard is that cand_id now hashes the
     params and the six ids are distinct (asserted below).
  2. N4's exit and C1 are both Coral at the same setting, and N1's, N5's and
     N6's exit duplicates their own C1 too. That is what the sources publish,
     so it is run as published -- but it means four of the six are using one
     piece of information twice, and the report says so rather than letting
     "five slots" imply five independent signals.
"""
import time, json
import numpy as np, pandas as pd

import l2sweep as S
import nnfxproto as P

OUT = os.path.join(ROOTOUT, 'nnfx')
os.makedirs(OUT, exist_ok=True)

# ---- the six, exactly as section 2.3 states them --------------------------
# (id, baseline, C1, C2, volume, exit, published-settings overrides, source)
CATALOG = [
    dict(name='N1', base='kijun_baseline', c1='ssl_channel_signals',
         c2='trend_direction_force_index_signals',
         vol='waddah_attar_explosion_volume_signals', exit='ssl_channel_exit',
         params={}, src='community "starter algo"',
         pub='Kijun-sen 26 / SSL Channel 10 / TDFI 13 +-0.05 / '
             'WAE 150-20-40 BB 20,2.0 / SSL'),
    dict(name='N2', base='hma_baseline', c1='didi_index_signals',
         c2='dspo_signals', vol='variance_volume_signals',
         exit='chandelier_exit_exit', params={},
         src="Jack's own Pine defaults",
         pub='HMA 20 / DiDi 8-20 / DSPO 14 / Variance EMA 10 / '
             'Chandelier 22,3.0'),
    dict(name='N3', base='mcginley_dynamic_index',
         c1='schaff_trend_cycle_signals', c2='vortex_signals',
         vol='damiani_volatmeter_volume_signals', exit='supertrend_exit',
         params={'schaff_trend_cycle_signals': dict(
             macdFast=12, macdSlow=26, cycleLen=10,
             upperBand=65, lowerBand=35)},
         src='community',
         pub='McGinley Dynamic / STC 12-26-10 65/35 / Vortex 14 / '
             'Damiani Volatmeter / Supertrend 10,3.0'),
    dict(name='N4', base='kama_baseline', c1='coral_signals',
         c2='qqe_mod_signals', vol='ttm_squeeze_volume_signals',
         exit='coral_exit', params={}, src='community',
         pub='KAMA / Coral 10-14 / QQE Mod 6-5-1.61 / TTM Squeeze / Coral'),
    dict(name='N5', base='ema_baseline', c1='aroon_signals',
         c2='kalman_filter_signals', vol='volatility_ratio_volume_signals',
         exit='aroon_exit',
         params={'ema_baseline': dict(ma_length=25)}, src='community',
         pub='EMA 20-30 (25 declared) / Aroon 25 / Kalman 1.0-1.0 / '
             'Volatility Ratio / Aroon'),
    dict(name='N6', base='super_smoother_2pole_baseline',
         c1='halftrend_signals', c2='fisher_transform_signals',
         vol='williams_vix_fix_volume_signals', exit='halftrend_exit',
         params={}, src='community',
         pub='Super Smoother 2-pole / Half Trend / Fisher Transform / '
             'Williams VIX Fix / Half Trend'),
]


def candidates():
    out = []
    for d in CATALOG:
        C = P.cand(d['name'], d['c1'], d['c2'], d['vol'], d['base'],
                   d['exit'], source='source1_published',
                   c1_set='published', c2_set='published', vol_set='published',
                   base_set='published', exit_set='published',
                   reason='%s, grade N: %s' % (d['src'], d['pub']),
                   params=d['params'])
        out.append(C)
    ids = [P.cand_id(c) for c in out]
    assert len(set(ids)) == len(ids), \
        'two N-combinations hash the same: the params are not in the key'
    return out


def run(with_g4=True, ndraw_null=200, pairs=None, verbose=True):
    S.load_costs(os.environ.get('FX_COST_TABLE',
                                os.path.join(ROOTOUT, 'cost_table_h22.csv')))
    C = candidates()
    P.declare(C, 'source1_published')
    print('  SOURCE 1: %d published combinations, 28 pairs, %d-%d, all unseen'
          % (len(C), min(P.EVIDENCE), max(P.EVIDENCE)), flush=True)
    t0 = time.time()
    R = P.run_batch(C, pairs=pairs, with_g4=with_g4, ndraw_null=ndraw_null,
                    tag='source1', verbose=verbose)
    D = R['summary']
    D.insert(1, 'published', [d['pub'] for d in CATALOG])
    D['exit_duplicates_c1'] = [
        int(c['exit'].replace('_exit', '') == c['c1'].replace('_signals', ''))
        for c in C]
    D.to_csv(os.path.join(OUT, 'source1_summary.csv'), index=False)
    R['per_pair'].to_csv(os.path.join(OUT, 'source1_per_pair.csv'),
                         index=False)
    R['nulls'].to_csv(os.path.join(OUT, 'source1_nulls.csv'), index=False)
    R['nudge'].to_csv(os.path.join(OUT, 'source1_nudge.csv'), index=False)
    print('  SOURCE 1 done in %.1f min: %d of %d passers'
          % ((time.time() - t0) / 60, int(D.passer.sum()), len(D)), flush=True)
    return R


# ============================ the write-up ==============================
def md(R=None):
    D = (R['summary'] if R else
         pd.read_csv(os.path.join(OUT, 'source1_summary.csv')))
    NU = (R['nulls'] if R else
          pd.read_csv(os.path.join(OUT, 'source1_nulls.csv')))
    PP = (R['per_pair'] if R else
          pd.read_csv(os.path.join(OUT, 'source1_per_pair.csv')))
    NG = (R['nudge'] if R else
          pd.read_csv(os.path.join(OUT, 'source1_nudge.csv')))
    f, yn = P.fmt, P.yn
    npass = int(D.passer.sum())
    floor_col = [c for c in D.columns if c.startswith('G1_floor_best_of_')][0]
    floor = float(D[floor_col].iloc[0])
    L = []
    L.append('# SOURCE 1 — the six published NNFX combinations\n')
    L.append('**Protocol: `results/nnfx/PROTOCOL.md`, unchanged. '
             'Zero search. 28 pairs, 2005-2015, all eleven years unseen '
             'because nothing is tuned. %d of 6 passers.**\n' % npass)
    L.append('N1 to N6 are the only NNFX combinations the community has '
             'actually named with settings, from the 9 November catalogue. '
             'All six are **grade N** — named components, no published '
             'settings for every slot, and **no published results anywhere '
             'that can be re-run**. This is the first time any of them has '
             'been tested on eleven years of 28 pairs with era-correct costs, '
             'a 1:30 leverage cap and realistic gap fills.\n')
    L.append('## The six, as published\n')
    L.append('| id | published construction | trades/yr |')
    L.append('|---|---|---:|')
    for _, r in D.iterrows():
        L.append('| **%s** | %s | %s |'
                 % (r['cand'], r['published'],
                    f(r.get('trades_per_year'), 1, False)))
    L.append('')
    dup = int(D.exit_duplicates_c1.sum())
    L.append('**%d of the 6 use their own C1 as their exit indicator** '
             '(N1 SSL, N4 Coral, N5 Aroon, N6 Half Trend). That is what the '
             'sources publish, so it is run as published — but those four are '
             'using one piece of information twice, and "five slots" does not '
             'mean five independent signals for them.\n' % dup)
    L.append('## The four gates\n')
    L.append('| id | G1 luck | G2 one event | G3 hold-out | G4 nudge | '
             '**passer** |')
    L.append('|---|---|---|---|---|---|')
    for _, r in D.iterrows():
        L.append('| **%s** | %s | %s | %s | %s | %s |'
                 % (r['cand'], yn(r['G1']), yn(r['G2']), yn(r['G3']),
                    yn(r['G4']),
                    '**PASSER**' if int(r['passer']) else 'no'))
    L.append('')
    L.append('**G1\'s floor is %s** — the 95th percentile of the '
             'block-bootstrap t under the batch\'s own random-entry null, '
             'corrected for best-of-6. Each candidate\'s null is matched on '
             'its own per-pair trade count, its own holding periods and its '
             'own long/short split, so only the TIMING is random. The floor '
             'comes from the batch, not from a table.\n' % f(floor, 3))
    L.append('## The numbers\n')
    L.append('| id | R total | R/yr | trades | R/trade net | R/trade gross | '
             'dip | **R/dip** | t block | t yearly | yrs + |')
    L.append('|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|')
    for _, r in D.iterrows():
        L.append('| **%s** | %s | %s | %s | %s | %s | %s | **%s** | %s | %s '
                 '| %d of %d |'
                 % (r['cand'], f(r.get('R_total')), f(r.get('R_per_year')),
                    f(r.get('trades'), 0, False), f(r.get('R_net_per_trade'), 4),
                    f(r.get('R_gross_per_trade'), 4),
                    f(r.get('dip_binding'), 3, False), f(r.get('R_per_dip')),
                    f(r.get('t_block_boot'), 2), f(r.get('t_yearly'), 2),
                    int(r.get('years_positive', 0)), int(r.get('years', 0))))
    L.append('')
    L.append('`dip` is the **binding** dip — the maximum of the realised '
             'chronological drawdown and DIP95, the 95th percentile over '
             'shuffled day orders. DIP95 sat above the realised dip on all '
             'eight sleeves of item 5, by 1.22x to 2.36x, so the maximum is '
             'taken rather than assumed.\n')
    L.append('## G2, one event — the three numbers\n')
    L.append('| id | R ex best day | R ex best 5 days | best trade share | '
             'best day R | pass |')
    L.append('|---|---:|---:|---:|---:|---|')
    for _, r in D.iterrows():
        L.append('| **%s** | %s | %s | %s | %s | %s |'
                 % (r['cand'], f(r.get('G2_R_ex_best_day')),
                    f(r.get('G2_R_ex_best5')),
                    f(r.get('G2_best_trade_share'), 3, False),
                    f(r.get('best_day_R')), yn(r['G2'])))
    L.append('')
    L.append('## G3, hold-out — the eight slices\n')
    L.append('| id | 2005-10 | 2011-15 | JPY+CHF in | JPY+CHF out | '
             'AUD+NZD in | AUD+NZD out | GBP+CAD in | GBP+CAD out | worst |')
    L.append('|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|')
    for _, r in D.iterrows():
        L.append('| **%s** | %s | %s | %s | %s | %s | %s | %s | %s | %s |'
                 % (r['cand'], f(r.get('G3_R_2005_2010')),
                    f(r.get('G3_R_2011_2015')),
                    f(r.get('G3_R_JPY_CHF_with')), f(r.get('G3_R_JPY_CHF_without')),
                    f(r.get('G3_R_AUD_NZD_with')), f(r.get('G3_R_AUD_NZD_without')),
                    f(r.get('G3_R_GBP_CAD_with')), f(r.get('G3_R_GBP_CAD_without')),
                    f(r.get('G3_worst_slice_R'))))
    L.append('')
    L.append('The split is taken from the **whole 28-pair capped frame**. '
             'Re-running the engine on a 15-pair subset would re-run the '
             '1:30 leverage cap on a smaller portfolio, which is an easier '
             'book than the one the trader runs — the same rule item 3 '
             'adopted for the per-pair bank.\n')
    if len(NG):
        L.append('## G4, nudge — the worst of 20 per candidate\n')
        L.append('| id | runs | skipped | worst R | worst knob | negative |')
        L.append('|---|---:|---:|---:|---|---:|')
        for _, r in D.iterrows():
            L.append('| **%s** | %s | %s | %s | %s | %s |'
                     % (r['cand'], f(r.get('G4_runs'), 0, False),
                        f(r.get('G4_skipped'), 0, False),
                        f(r.get('G4_worst_R')), r.get('G4_worst_knob', ''),
                        f(r.get('G4_n_negative'), 0, False)))
        L.append('')
        L.append('Each slot\'s length knob at x0.5 and x2, ATR length 7 and '
                 '28, stop 0.75 and 1.25 ATR, target 1.0x and 2.0x, baseline '
                 'distance 1.0 and 2.0 ATR, bridge 5 and 9 candles — one at a '
                 'time, 20 runs. The steps are deliberately coarser than '
                 '`l2tune`\'s GAUNTLET grids, where a 0.05 nudge on the stop '
                 'would pass by construction. `skipped` counts knobs that do '
                 'not exist or whose nudge collapses onto the candidate.\n')
    if len(PP):
        L.append('## Per pair — the best and worst five of each candidate\n')
        for nm in D['cand']:
            q = PP[PP.cand == nm]
            if not len(q):
                continue
            g = (q.groupby('pair', as_index=False)
                 .agg(R=('R_net', 'sum'), trades=('trades', 'sum'))
                 .sort_values('R', ascending=False))
            pos = int((g.R > 0).sum())
            best = ', '.join('%s %s' % (r['pair'], f(r['R'], 1))
                             for _, r in g.head(5).iterrows())
            wrst = ', '.join('%s %s' % (r['pair'], f(r['R'], 1))
                             for _, r in g.tail(5).iterrows())
            L.append('- **%s** — %d of %d pairs positive. best: %s. worst: %s.'
                     % (nm, pos, len(g), best, wrst))
        L.append('')
        L.append('The full 28-pair-by-direction table is in '
                 '`results/nnfx/source1_per_pair.csv`.\n')
    L.append('## The null\n')
    if len(NU):
        L.append('| id | draws | null t mean | null t p95 | null t max |')
        L.append('|---|---:|---:|---:|---:|')
        for _, r in NU.iterrows():
            L.append('| **%s** | %s | %s | %s | %s |'
                     % (r['cand'], f(r['draws'], 0, False),
                        f(r['null_t_mean'], 3), f(r['null_t_p95'], 3),
                        f(r['null_t_max'], 3)))
        L.append('')
    L.append('## What Source 1 says\n')
    if npass == 0:
        L.append('**None of the six published combinations is a passer.** '
                 'Not one clears all four gates on eleven unseen years of 28 '
                 'pairs. These are the community\'s named algorithms at their '
                 'own settings, and the catalogue already warned what to '
                 'expect: grade N throughout, no reproducible result '
                 'anywhere, and the two self-reported backtests pointing '
                 'opposite ways.\n')
        L.append('That is a result and not a non-result. It means the project '
                 'is not leaving a known working algorithm untested, and it '
                 'sets the bar Sources 2 and 3 have to clear.\n')
    else:
        L.append('**%d of the six clear all four gates.** The passer list goes '
                 'to BOOK2.md, and no 2016-2020 number is opened until Jack '
                 'calls the confirm.\n' % npass)
    L.append('## Costs, and a correction that applies to everything else\n')
    L.append('Every figure here is charged **once** per round trip on the '
             'engine\'s own risk denominator. `results/nnfx/'
             'COST_DOUBLE_CHARGE.md` records a fault found while building '
             'this protocol: every NNFX-phase table written before 25 '
             'November charges **twice** the measured spread, because '
             '`l2engine.run` risks 200 per unit of raw r while '
             '`nnfx1._cost_R` divides by 100. The fault is pessimistic, it '
             'does not touch the gauntlet path, and **nothing in this '
             'document carries it.**\n')
    L.append('## Provenance\n')
    L.append(P.prov([os.path.join(OUT, x) for x in
                     ('source1_summary.csv', 'source1_per_pair.csv',
                      'source1_nulls.csv', 'source1_nudge.csv')]))
    L.append('')
    L.append('The candidate ledger is `results/nnfx/proto_ledger.csv`. It is '
             'append-only and shared by all three sources, so it carries no '
             'row count here: its count changes every time a source declares '
             'its candidates, and a provenance line that goes stale on the '
             'next run is worse than no line (preflight guard 35 caught '
             'exactly that on the first draft of this document).')
    L.append('')
    open(os.path.join(OUT, 'SOURCE1.md'), 'w').write('\n'.join(L))
    print('  SOURCE1.md written (%d lines)' % len(L), flush=True)


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--no-g4', action='store_true')
    ap.add_argument('--md-only', action='store_true')
    ap.add_argument('--nulls', type=int, default=200)
    a = ap.parse_args()
    if a.md_only:
        md()
    else:
        R = run(with_g4=not a.no_g4, ndraw_null=a.nulls)
        md(R)
