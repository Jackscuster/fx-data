import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""SOURCE 2 — TEN HAND-BUILT ALGORITHMS, EACH WITH A DECLARED REASON. 0o.

Ten complete algorithms, settings fixed and in the ledger before any of them
was scored, each carrying one line of reason drawn from a MEASUREMENT ON
RECORD in this project. Floor for best-of-10.

WHAT IS AND IS NOT BACKED BY A MEASUREMENT, SAID ONCE AND PLAINLY.

The project has measured, on 28 pairs and six to eleven unseen years:
  - every one of the 39 C1 indicators ALONE, at three settings, two risk
    plans (stage1r2_c1_jack_summary.csv). ichimoku/half is the best of the 39
    at +24.273 R net; schaff_trend_cycle/default is second at +6.884;
    aroon/default third at +2.810; adx_dmi/double has the best R per TRADE at
    +0.0195 on 75 entries; waddah_attar_explosion/double is the fifth and last
    positive one at +0.377. The other 34 are negative.
  - every one of the 15 baselines ALONE (stage1r2_base_jack_summary.csv). ALL
    FIFTEEN ARE NEGATIVE, and the DOUBLE setting is the best of the three for
    every single one of them -- sma -72.897, rma -77.057, t3 -78.953,
    tma -94.473, ema -105.587 at double. So a baseline is judged here as a
    FILTER, never as a signal, and slow beats fast across the whole family.
  - that losses concentrate in LOUD entries. Item 2 found a negative rank
    correlation between ATR percentile at entry and R per trade on 35 of 39
    C1, and real top-decile entries underperforming same-decile RANDOM entries
    by up to 1 SD. The hard ATR-percentile cut FAILED walk-forward (-4.816 R
    on A, 1 of 6 years), so what is tested here is the asymmetry through the
    slot that is supposed to carry it, not the rule that failed.

The project has measured NOTHING about which C2, which volume filter or which
exit indicator to use. Stage 1 tested C1 and baselines; stage 2 tested
baselines as filters with C2, volume and the exit BLANKED. So every C2, volume
and exit choice below is a DECLARED CHOICE WITH A STATED PRINCIPLE AND NO
MEASUREMENT BEHIND IT, and the report says so instead of dressing a choice as
a citation. The two principles used:
  - C2 and the exit indicator come from a DIFFERENT construction family than
     C1, so the candidate is not using one signal twice. Four of the six
     published combinations in Source 1 fail this (N1, N4, N5 and N6 use their
     own C1 as their exit).
  - the volume slot's DIRECTION is checked in the source before it is used.
     Of the 12 available filters, choppiness_index (CI < 61.8) and
     efficiency_ratio (ER > 0.30) are SHAPE filters -- they ask whether price
     is moving in one direction, not how far. ttm_squeeze (passes when the
     squeeze is OFF), chaikin_volatility (range opening up), williams_vix_fix
     and volatility_ratio (true range above its own 14-bar average) are
     EXPANSION filters: they trade only when the market is LOUD. Given the
     measurement above, the expansion filters are predicted to be WORSE, and
     H4 against H1 is the paired test of exactly that.

THREE OF THE TEN ARE PAIRED AGAINST H1 AND DIFFER IN ONE SLOT ONLY, which is
the only way a ten-candidate batch can say WHICH SLOT moved the number:
  H4 = H1 with an expansion volume filter instead of a shape one
  H9 = H1 with rma as the baseline instead of sma
  H5 = H1 with every slot at its slow setting

FAULTS THIS FILE FOUND IN ITSELF
  1. The first draft described efficiency_ratio as a "quietness filter". It is
     not: it passes when ER > 0.30, which is a DIRECTION test, and nothing in
     the available 12 trades only when the market is quiet. The claim was
     checked against l2lib source line by line and withdrawn before any run.
     A quietness filter would have to be a new indicator and is not in scope.
  2. H3's exit was adx_dmi_exit against an adx_dmi C1 -- the same duplication
     the file criticises Source 1 for. Changed to linreg_slope_exit.
"""
import time, json
import numpy as np, pandas as pd

import l2sweep as S
import nnfxproto as P

OUT = os.path.join(ROOTOUT, 'nnfx')
os.makedirs(OUT, exist_ok=True)

# name, c1, c1_set, c2, c2_set, vol, vol_set, base, base_set, exit, exit_set,
# reason
HAND = [
    ('H1', 'ichimoku_signals', 'half', 'vortex_signals', 'default',
     'choppiness_index_volume_signals', 'default', 'sma_baseline', 'double',
     'adx_dmi_exit', 'default',
     'ichimoku/half is the best of the 39 C1 alone (+24.273 R net, 28 pairs, '
     '2005-2015) and sma the least-bad of the 15 baselines at its best '
     'setting (double, -72.897); ichimoku with sma is also candidate A\'s own '
     'pair. C2/volume/exit declared: a different family each, shape filter.'),
    ('H2', 'schaff_trend_cycle_signals', 'default', 'aroon_signals', 'default',
     'choppiness_index_volume_signals', 'default', 'sma_baseline', 'double',
     'supertrend_exit', 'default',
     'schaff_trend_cycle/default is the second-best C1 alone (+6.884 R) and '
     'aroon/default the third (+2.810), so this is the two best INDEPENDENT '
     'oscillators in C1 and C2; stc with sma is candidate B\'s own pair.'),
    ('H3', 'adx_dmi_signals', 'double', 'vortex_signals', 'default',
     'choppiness_index_volume_signals', 'default', 'sma_baseline', 'double',
     'linreg_slope_exit', 'default',
     'adx_dmi/double has the best R per TRADE of all 39 C1 alone (+0.0195) on '
     'only 75 entries in six years. The question is whether the per-trade '
     'edge survives being given a full algorithm, or whether the thinness '
     'was the edge.'),
    ('H4', 'ichimoku_signals', 'half', 'vortex_signals', 'default',
     'volatility_ratio_volume_signals', 'default', 'sma_baseline', 'double',
     'adx_dmi_exit', 'default',
     'H1 with one slot changed: an EXPANSION volume filter (true range above '
     'its own 14-bar average) in place of a shape one. Item 2 measured losses '
     'concentrating in loud entries on 35 of 39 C1, so this is PREDICTED TO '
     'BE WORSE THAN H1, and that prediction is the test.'),
    ('H5', 'ichimoku_signals', 'double', 'vortex_signals', 'double',
     'choppiness_index_volume_signals', 'double', 'sma_baseline', 'double',
     'adx_dmi_exit', 'double',
     'H1 with every slot at its SLOW setting. The double setting was the best '
     'of three for every one of the 15 baselines without exception, which is '
     'a statement about memory length and not about baselines; this asks '
     'whether it generalises to all five slots.'),
    ('H6', 'schaff_trend_cycle_signals', 'default', 'vortex_signals',
     'default', 'choppiness_index_volume_signals', 'default',
     'kijun_baseline', 'default', 'linreg_slope_exit', 'default',
     'Kijun-sen is flat and STEPS, so price crosses it far less often than an '
     'SMA of the same length. The baseline distance rule and the baseline '
     'cross are the only rules in Jack\'s plan whose effect depends on cross '
     'frequency, and item 6a found base_cross_only the best exit arm for A by '
     'mean return per dip (+1.464 over 72 cells, best of four arms).'),
    ('H7', 'halftrend_signals', 'double', 'vortex_signals', 'default',
     'choppiness_index_volume_signals', 'default', 't3_baseline', 'double',
     'adx_dmi_exit', 'default',
     'halftrend is the third of Jack\'s three picked C1 -- his reason on '
     'record: "the only C1 positive net under both the jack and textbook '
     'plans at more than one setting". t3/double is the third-best baseline '
     '(-78.953) and the one least correlated in construction with sma.'),
    ('H8', 'waddah_attar_explosion_signals', 'double', 'vortex_signals',
     'default', 'waddah_attar_explosion_volume_signals', 'default',
     'sma_baseline', 'double', 'adx_dmi_exit', 'default',
     'WAE is the only indicator the community uses in TWO different slots '
     '(C1 in the Stonehill series, volume in N1, N7, N9 and N11) and '
     'waddah_attar_explosion/double is the fifth and last of the 39 C1 that '
     'is positive alone (+0.377 R). This runs it in both slots at once, '
     'which is what the community actually does.'),
    ('H9', 'ichimoku_signals', 'half', 'vortex_signals', 'default',
     'choppiness_index_volume_signals', 'default', 'rma_baseline', 'double',
     'adx_dmi_exit', 'default',
     'H1 with one slot changed: rma (Wilder) in place of sma. rma/double is '
     'the second-best baseline alone (-77.057 against sma\'s -72.897) and the '
     'slowest-responding of the three; since no baseline is positive alone '
     'they are judged as filters, and this is the paired test of which filter.'),
    ('H10', 'ssl_channel_signals', 'default', 'dspo_signals', 'default',
     'variance_volume_signals', 'default', 'tma_baseline', 'default',
     'ssl_channel_exit', 'default',
     'THE CONTROL. This is l2engine.DEFAULT_SLOTS -- the five slots the '
     'project\'s own Pine file ships and the ONLY five-slot combination with '
     'a parity proof against TradingView (185 of 189 entries). If the '
     'protocol fails it, the failure is about the strategy and not about the '
     'engine.'),
]
PAIRED = {'H4': ('H1', 'volume slot: expansion filter instead of shape'),
          'H9': ('H1', 'baseline: rma instead of sma'),
          'H5': ('H1', 'every slot at its slow setting')}


def candidates():
    out = []
    for (nm, c1, c1s, c2, c2s, vl, vls, bs, bss, ex, exs, why) in HAND:
        out.append(P.cand(nm, c1, c2, vl, bs, ex, source='source2_handbuilt',
                          c1_set=c1s, c2_set=c2s, vol_set=vls, base_set=bss,
                          exit_set=exs, reason=why))
    ids = [P.cand_id(c) for c in out]
    assert len(set(ids)) == len(ids), 'two hand-built candidates are identical'
    return out


def run(with_g4=True, ndraw_null=200, pairs=None, verbose=True):
    S.load_costs(os.environ.get('FX_COST_TABLE',
                                os.path.join(ROOTOUT, 'cost_table_h22.csv')))
    C = candidates()
    P.declare(C, 'source2_handbuilt')
    print('  SOURCE 2: %d hand-built algorithms, 28 pairs, %d-%d, all unseen'
          % (len(C), min(P.EVIDENCE), max(P.EVIDENCE)), flush=True)
    t0 = time.time()
    R = P.run_batch(C, pairs=pairs, with_g4=with_g4, ndraw_null=ndraw_null,
                    tag='source2', verbose=verbose)
    D = R['summary']
    D['paired_against'] = [PAIRED.get(n, ('', ''))[0] for n in D['cand']]
    D['paired_change'] = [PAIRED.get(n, ('', ''))[1] for n in D['cand']]
    D.to_csv(os.path.join(OUT, 'source2_summary.csv'), index=False)
    R['per_pair'].to_csv(os.path.join(OUT, 'source2_per_pair.csv'), index=False)
    R['nulls'].to_csv(os.path.join(OUT, 'source2_nulls.csv'), index=False)
    R['nudge'].to_csv(os.path.join(OUT, 'source2_nudge.csv'), index=False)
    print('  SOURCE 2 done in %.1f min: %d of %d passers'
          % ((time.time() - t0) / 60, int(D.passer.sum()), len(D)), flush=True)
    return R


def md(R=None):
    D = (R['summary'] if R else
         pd.read_csv(os.path.join(OUT, 'source2_summary.csv')))
    NU = (R['nulls'] if R else
          pd.read_csv(os.path.join(OUT, 'source2_nulls.csv')))
    PP = (R['per_pair'] if R else
          pd.read_csv(os.path.join(OUT, 'source2_per_pair.csv')))
    NG = (R['nudge'] if R else
          pd.read_csv(os.path.join(OUT, 'source2_nudge.csv')))
    f, yn = P.fmt, P.yn
    npass = int(D.passer.sum())
    fc = [c for c in D.columns if c.startswith('G1_floor_best_of_')][0]
    floor = float(D[fc].iloc[0])
    L = []
    L.append('# SOURCE 2 — ten hand-built algorithms, each with a declared '
             'reason\n')
    L.append('**Protocol: `results/nnfx/PROTOCOL.md`, unchanged. Settings '
             'fixed and in the ledger BEFORE any of them was scored. '
             '28 pairs, 2005-2015, all eleven years unseen. Floor for '
             'best-of-10. %d of 10 passers.**\n' % npass)
    L.append('## What is backed by a measurement and what is a declared '
             'choice\n')
    L.append('The project has measured all 39 C1 alone and all 15 baselines '
             'alone, on 28 pairs over unseen years. It has measured **nothing '
             'about which C2, which volume filter or which exit indicator to '
             'use** — stage 1 tested C1 and baselines, stage 2 tested '
             'baselines with C2, volume and the exit *blanked*. So the C1 and '
             'the baseline of every candidate below carry a number; the other '
             'three slots carry a **stated principle and no measurement**, '
             'and that is said here rather than dressed up as a citation.\n')
    L.append('Two principles were used. **C2 and the exit come from a '
             'different construction family than C1**, so the candidate is '
             'not using one signal twice — four of the six published '
             'combinations in Source 1 fail this. And **the volume slot\'s '
             'direction was read out of the source before it was used**: '
             'choppiness index (CI < 61.8) and efficiency ratio (ER > 0.30) '
             'are *shape* filters, while ttm squeeze, chaikin volatility, '
             'williams vix fix and volatility ratio all pass only when the '
             'market is **loud**. Item 2 measured losses concentrating in '
             'loud entries, so the loud filters are predicted to be worse. '
             '**H4 is that prediction, run.**\n')
    L.append('## The ten, with their reasons\n')
    for (nm, c1, c1s, c2, c2s, vl, vls, bs, bss, ex, exs, why) in HAND:
        r = D[D.cand == nm]
        tot = (f(float(r.R_total.iloc[0])) if len(r) else '—')
        L.append('**%s** — %s  \n`C1 %s/%s · C2 %s/%s · VOL %s/%s · '
                 'BASE %s/%s · EXIT %s/%s` → **R %s**\n'
                 % (nm, why, c1.replace('_signals', ''), c1s,
                    c2.replace('_signals', ''), c2s,
                    vl.replace('_volume_signals', ''), vls,
                    bs.replace('_baseline', ''), bss,
                    ex.replace('_exit', ''), exs, tot))
    L.append('## The four gates\n')
    L.append('| id | G1 luck | G2 one event | G3 hold-out | G4 nudge | '
             '**passer** |')
    L.append('|---|---|---|---|---|---|')
    for _, r in D.iterrows():
        L.append('| **%s** | %s | %s | %s | %s | %s |'
                 % (r['cand'], yn(r['G1']), yn(r['G2']), yn(r['G3']),
                    yn(r['G4']), '**PASSER**' if int(r['passer']) else 'no'))
    L.append('')
    L.append('**G1\'s floor is %s**, the 95th percentile of the '
             'block-bootstrap t under the batch\'s own random-entry null, '
             'corrected for best-of-10. A ten-candidate batch has a higher '
             'floor than Source 1\'s six by construction, and that is the '
             'price of proposing ten.\n' % f(floor, 3))
    L.append('## The numbers\n')
    L.append('| id | R total | R/yr | trades | R/trade net | dip | '
             '**R/dip** | t block | t yearly | yrs + |')
    L.append('|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|')
    for _, r in D.iterrows():
        L.append('| **%s** | %s | %s | %s | %s | %s | **%s** | %s | %s | '
                 '%d of %d |'
                 % (r['cand'], f(r.get('R_total')), f(r.get('R_per_year')),
                    f(r.get('trades'), 0, False),
                    f(r.get('R_net_per_trade'), 4),
                    f(r.get('dip_binding'), 3, False), f(r.get('R_per_dip')),
                    f(r.get('t_block_boot'), 2), f(r.get('t_yearly'), 2),
                    int(r.get('years_positive', 0)), int(r.get('years', 0))))
    L.append('')
    L.append('## The three paired tests — which slot moved the number\n')
    base = D[D.cand == 'H1']
    if len(base):
        b = base.iloc[0]
        L.append('| against H1 | change | R total | dR | R/dip | d R/dip |')
        L.append('|---|---|---:|---:|---:|---:|')
        L.append('| **H1** | — | %s | — | %s | — |'
                 % (f(b.R_total), f(b.R_per_dip)))
        for nm in ('H4', 'H9', 'H5'):
            r = D[D.cand == nm]
            if not len(r):
                continue
            r = r.iloc[0]
            L.append('| **%s** | %s | %s | %s | %s | %s |'
                     % (nm, PAIRED[nm][1], f(r.R_total),
                        f(r.R_total - b.R_total), f(r.R_per_dip),
                        f(r.R_per_dip - b.R_per_dip)))
        L.append('')
        h4 = D[D.cand == 'H4']
        if len(h4):
            d4 = float(h4.R_total.iloc[0]) - float(b.R_total)
            L.append('**The H4 prediction %s.** Item 2\'s measurement said an '
                     'expansion filter — one that only lets the algorithm '
                     'trade when the true range is above its own average — '
                     'should be worse than a shape filter. It came out %s by '
                     '%s R. %s\n'
                     % ('HELD' if d4 < 0 else 'FAILED',
                        'worse' if d4 < 0 else 'better', f(abs(d4)),
                        'That is one paired comparison on one candidate, not '
                        'a law; it is reported because the direction was '
                        'declared before the run.'))
    L.append('## G2, one event\n')
    L.append('| id | R ex best day | R ex best 5 days | best trade share | '
             'pass |')
    L.append('|---|---:|---:|---:|---|')
    for _, r in D.iterrows():
        L.append('| **%s** | %s | %s | %s | %s |'
                 % (r['cand'], f(r.get('G2_R_ex_best_day')),
                    f(r.get('G2_R_ex_best5')),
                    f(r.get('G2_best_trade_share'), 3, False), yn(r['G2'])))
    L.append('')
    L.append('## G3, hold-out — the eight slices\n')
    L.append('| id | 2005-10 | 2011-15 | JPY+CHF in | out | AUD+NZD in | '
             'out | GBP+CAD in | out | worst |')
    L.append('|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|')
    for _, r in D.iterrows():
        L.append('| **%s** | %s | %s | %s | %s | %s | %s | %s | %s | %s |'
                 % (r['cand'], f(r.get('G3_R_2005_2010')),
                    f(r.get('G3_R_2011_2015')),
                    f(r.get('G3_R_JPY_CHF_with')),
                    f(r.get('G3_R_JPY_CHF_without')),
                    f(r.get('G3_R_AUD_NZD_with')),
                    f(r.get('G3_R_AUD_NZD_without')),
                    f(r.get('G3_R_GBP_CAD_with')),
                    f(r.get('G3_R_GBP_CAD_without')),
                    f(r.get('G3_worst_slice_R'))))
    L.append('')
    if len(NG):
        L.append('## G4, nudge\n')
        L.append('| id | runs | skipped | worst R | worst knob | negative |')
        L.append('|---|---:|---:|---:|---|---:|')
        for _, r in D.iterrows():
            L.append('| **%s** | %s | %s | %s | %s | %s |'
                     % (r['cand'], f(r.get('G4_runs'), 0, False),
                        f(r.get('G4_skipped'), 0, False),
                        f(r.get('G4_worst_R')), r.get('G4_worst_knob', ''),
                        f(r.get('G4_n_negative'), 0, False)))
        L.append('')
    if len(PP):
        L.append('## Per pair\n')
        for nm in D['cand']:
            q = PP[PP.cand == nm]
            if not len(q):
                continue
            g = (q.groupby('pair', as_index=False).agg(R=('R_net', 'sum'))
                 .sort_values('R', ascending=False))
            L.append('- **%s** — %d of %d pairs positive. best: %s. worst: %s.'
                     % (nm, int((g.R > 0).sum()), len(g),
                        ', '.join('%s %s' % (r['pair'], f(r['R'], 1))
                                  for _, r in g.head(3).iterrows()),
                        ', '.join('%s %s' % (r['pair'], f(r['R'], 1))
                                  for _, r in g.tail(3).iterrows())))
        L.append('')
    if len(NU):
        L.append('## The null\n')
        L.append('| id | draws | null t mean | null t p95 | null t max |')
        L.append('|---|---:|---:|---:|---:|')
        for _, r in NU.iterrows():
            L.append('| **%s** | %s | %s | %s | %s |'
                     % (r['cand'], f(r['draws'], 0, False),
                        f(r['null_t_mean'], 3), f(r['null_t_p95'], 3),
                        f(r['null_t_max'], 3)))
        L.append('')
    L.append('## What Source 2 says\n')
    best = D.sort_values('R_per_dip', ascending=False).iloc[0] if len(D) else None
    if npass == 0:
        L.append('**No hand-built candidate is a passer.** The best by return '
                 'per dip is **%s** at %s, and it does not clear all four '
                 'gates. Ten declared constructions built on the project\'s '
                 'own best measurements do not produce a working algorithm '
                 'under this protocol.\n'
                 % (best['cand'], f(best['R_per_dip'])) if best is not None
                 else '')
        L.append('That is worth stating precisely because of WHERE the '
                 'reasons came from: the C1 and baseline choices are the '
                 'project\'s own measured leaders, not guesses. If those do '
                 'not survive a complete algorithm on eleven unseen years, '
                 'the problem is not the choice of C1.\n')
    else:
        L.append('**%d of the ten clear all four gates.** They go to '
                 'BOOK2.md. No 2016-2020 number is opened.\n' % npass)
    L.append('## Costs\n')
    L.append('Charged **once** per round trip on the engine\'s own risk '
             'denominator. See `results/nnfx/COST_DOUBLE_CHARGE.md`: every '
             'NNFX table written before 25 November charges twice the '
             'measured spread. **Nothing in this document carries that '
             'fault**, which is why its R figures are not comparable with '
             'stage 1 and stage 2 numbers without the correction in that '
             'file.\n')
    L.append('## Provenance\n')
    L.append(P.prov([os.path.join(OUT, x) for x in
                     ('source2_summary.csv', 'source2_per_pair.csv',
                      'source2_nulls.csv', 'source2_nudge.csv')]))
    L.append('')
    L.append('The candidate ledger is `results/nnfx/proto_ledger.csv`, '
             'append-only and shared by all three sources, so no row count is '
             'quoted for it here.')
    L.append('')
    open(os.path.join(OUT, 'SOURCE2.md'), 'w').write('\n'.join(L))
    print('  SOURCE2.md written (%d lines)' % len(L), flush=True)


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
