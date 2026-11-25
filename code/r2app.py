import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""THE LAYER 2 RESTART TAB (HANDOFF 0l).  The third wiring place.

Owns the `l2_restart` section of app_data.json and the "L2 restart" tab in
app_ui.js, so a cold pipeline run rebuilds both instead of deleting them --
which is exactly what bundle.py did to the four November research sections
before code/appsections.py existed.

    python3 code/r2app.py --stage app
"""
import json, glob
import numpy as np, pandas as pd

NL = '\n'
STAMP = '2026-11-16'


def _recs(path, cols=None, head=None):
    if not os.path.exists(path):
        return []
    d = pd.read_csv(path)
    if cols:
        d = d[[c for c in cols if c in d.columns]]
    if head:
        d = d.head(head)
    return json.loads(d.replace({np.nan: None}).to_json(orient='records'))


def curve_digest(mode, tag, per=14):
    """A readable slice of the curve: `per` cuts evenly spaced across the full
    swept range, pooled over the five windows, per stream."""
    p = os.path.join(ROOTOUT, 'r2gate1_pooled_mode%s_%s.csv' % (mode, tag))
    if not os.path.exists(p):
        return []
    d = pd.read_csv(p)
    out = []
    for s, g in d.groupby('stream', sort=False):
        g = g.reset_index(drop=True)
        idx = np.unique(np.linspace(0, len(g) - 1, per).astype(int))
        out.append(g.loc[idx])
    D = pd.concat(out, ignore_index=True)
    return json.loads(D.replace({np.nan: None}).to_json(orient='records'))


def stage_app():
    sec = dict(
        stamp=STAMP,
        note=('Layer 2 restarted from mode A up (HANDOFF 0l). The gate 1 on disk cut on '
              'W2+W3 pooled = 2011-2020, i.e. on every year Layer 2 then called blind, and '
              'charged no costs. The honest gate 1 scores every combination at defaults with '
              'costs on, banks each trade by the calendar year of its ENTRY bar, and CUTS ON '
              'TUNE YEARS ONLY -- grade and trade years are measured at the same time and take '
              'no part in the selection. Four streams, none selected on: trend and chop, each '
              'routed and always-on. The cut is swept over its whole range; Jack picks from the '
              'curve. Nothing from the old Layer 2 is deleted.'),
        library=_recs(os.path.join(ROOTOUT, 'r2_step1_library.csv')),
        modes=_recs(os.path.join(ROOTOUT, 'r2_step1_modes.csv')),
        timing=_recs(os.path.join(ROOTOUT, 'r2_step1_timing.csv')),
        gate1_original=_recs(os.path.join(ROOTOUT, 'r2_step1_gate1_original.csv')),
        contaminations=_recs(os.path.join(ROOTOUT, 'r2_step1_contaminations.csv')),
        superseded=_recs(os.path.join(ROOTOUT, 'r2_superseded_files.csv')),
        parity=[{'mode': m, 'comparisons': len(d), 'mismatches': int(d.mismatch.sum())}
                for m in 'ABC'
                for d in [pd.read_csv(os.path.join(ROOTOUT, 'r2gate1_parity_mode%s.csv' % m))]
                if os.path.exists(os.path.join(ROOTOUT, 'r2gate1_parity_mode%s.csv' % m))],
        rankcorr={m: _recs(os.path.join(ROOTOUT, 'r2gate1_rankcorr_mode%s_full.csv' % m)) for m in 'ABC'},
        curve={m: curve_digest(m, 'full') for m in 'ABC'},
    )
    # ---- THE READS SECTION: A1..A6, B1 and C1..C3.
    # STANDING RULE: every result gets an app tab. These reports were delivered
    # as markdown and csv on 24 Nov and had no tab until this section existed;
    # the rule is not satisfied by a file on disk.
    RD = os.path.join(ROOTOUT, 'r2reads')
    def rd(name, cols=None, head=60):
        return _recs(os.path.join(RD, name), cols=cols, head=head)
    sec['reads'] = dict(
        note=('The read-only passes off the banked gate 2 and gate 3 results. '
              'Every number here comes from a csv in results/r2reads and every '
              'report names its own provenance with an md5.'),
        b1_winners_era={m: rd('mode%s_b1winners_era.csv' % m,
                              ['sid', 'R_new6', 'prop_return_new6'])
                        for m in 'AB'},
        cond3=_recs(os.path.join(ROOTOUT, 'r2gate2_cond3_crosswalk.csv'),
                    cols=['mode', 'winner', 'year', 'base5_R', 'ext11_R', 'dR',
                          'base5_n', 'ext11_n', 'dn', 'base5_cfg', 'ext11_cfg',
                          'cfg_same'], head=50),
        gate2_vs_gate3=_recs(os.path.join(ROOTOUT, 'r2gate2',
                                          'gate2_vs_gate3_peryear.csv'), head=50),
        b1_winners={m: rd('mode%s_b1winners.csv' % m,
                          ['sid', 'stream', 'R_new6', 'dd_new6', 't_new6',
                           'years_pos_new6', 'prop_return_new6', 'R_all11',
                           'dd_all11', 'prop_return_all11'])
                    for m in 'AB'},
        a4_capcurve={m: rd('mode%s_a4_capcurve.csv' % m) for m in 'AB'},
        a4_attribution={m: rd('mode%s_a4_attribution.csv' % m,
                              ['rule', 'step', 'book', 'budget',
                               'worst10_mean_pct', 'worst10_largest_leg_share',
                               'worst10_top_currency',
                               'allday_largest_leg_share', 'worst_dip_pct',
                               'worst_dip_largest_leg_share'])
                       for m in 'AB'},
        a5_delta={m: rd('mode%s_a5_delta_strategy.csv' % m) for m in 'AB'},
        a5_spreads={m: rd('mode%s_a5_spreads_by_pair.csv' % m) for m in 'AB'},
        a5_overlay={m: rd('mode%s_a5_overlay_curve.csv' % m) for m in 'AB'},
        c1_data=rd('c1_data_availability.csv', head=20),
        c3_fix={e: rd('c3_fix_%s.csv' % e, head=0) for e in ('measure',)},
    )
    # C3 is rolled up rather than shipped raw: 1,344 rows per era is a table
    # nobody reads, and the roll-up is the currency-against-basket figure.
    try:
        import c3hourly as _C3
        import pandas as _pd
        for era in ('measure', 'confirm'):
            f_ = os.path.join(RD, 'c3_hours_%s.csv' % era)
            if os.path.exists(f_):
                g = _C3.roll_up(_pd.read_csv(f_), ['currency', 'hour_ny'])
                g = g.reindex(g.move_bp.abs().sort_values(ascending=False).index)
                sec['reads']['c3_hours_%s' % era] = json.loads(
                    g.head(40)[['currency', 'hour_ny', 'n', 'pairs', 'move_bp',
                                'spread_bp', 'move_net_bp', 't_across_pairs']]
                    .replace({np.nan: None}).to_json(orient='records'))
    except Exception as e:
        sec['reads']['c3_error'] = '%s: %s' % (type(e).__name__, e)
    for k in ('b1_winners', 'b1_winners_era', 'a4_capcurve', 'a4_attribution', 'a5_delta',
              'a5_spreads', 'a5_overlay'):
        sec['reads'][k] = {m: v for m, v in sec['reads'][k].items() if v}
    sec['reads'].pop('c3_fix', None)
    # ---- JACK'S TWO A4/A5 FOLLOW-UPS, 24 Nov.
    def _rr(n, cols=None, head=200):
        return _recs(os.path.join(ROOTOUT, 'r2reads', n), cols=cols, head=head)
    sec['reads']['a4_capsweep_binding'] = {
        m: _rr('mode%s_a4_capsweep_binding.csv' % m) for m in ('A', 'B')}
    sec['reads']['a5_overlay_team1'] = {
        m: _rr('mode%s_a5_overlay_team1.csv' % m) for m in ('A', 'B')}
    sec['reads']['followup_note'] = (
        'A4: the shipped cap grid binds on 0 days at 11 of its 13 caps in the '
        'slice Jack read, because that slice reaches only 0.843 exposure. '
        'a4_capsweep_binding re-sweeps the range where it DOES bind -- the cap '
        'binding on a share q of days is the (1-q) quantile of the day worst-'
        'exposure series, so 1% of days is the 99th percentile and 50% is the '
        'median. A5: section 4 summed eight full-risk strategies in the '
        'numerator and took ONE winner-year dip in the denominator, giving '
        '27.43%/yr; on the per-strategy Team 1 basis it is 1.45%/yr and NONE '
        'of the 8 winners clears 12%. The stop was tested on ALL open-trade '
        'days with hourly coverage (8,947 of 10,370 member-days), not on '
        'ambiguous days only -- the earlier caveat in the file was wrong.')
    for k in ('a4_capsweep_binding', 'a5_overlay_team1'):
        sec['reads'][k] = {m: v for m, v in sec['reads'][k].items() if v}
    # ---- B1-NARROW, the eleven-step walk on the narrow universe (chain 29).
    sec['reads']['b1narrow_winners'] = _rr(
        'b1narrow_winners_new6.csv',
        cols=['mode', 'sid', 'stream', 'R_new6_mean', 't_new6',
              'years_pos_new6', 'R_old5_mean', 't_old5', 'years_pos_old5',
              'R_all11_mean', 'years_pos_all11'])
    sec['reads']['b1narrow_vs_control'] = _rr('b1narrow_winner_vs_control.csv')
    sec['reads']['b1narrow_cohorts'] = _rr('b1narrow_cohorts.csv')
    sec['reads']['b1narrow_note'] = (
        'The eleven-step walk re-tunes every strategy from 2005 so that trade '
        'years 2010-2015 -- six years no part of the five-step selection ever '
        'touched -- can be read. 7,970 strategies banked across the two modes: '
        'the 10 winners, a 2,000-strategy sample of the lemantrend / '
        'waddah_attar family, and a 2,000-strategy random control. THE RESULT: '
        'the winners average +0.12310 R per trade on the five years they were '
        'selected on and -0.02089 on the six they never saw, 2 of 10 positive. '
        'Against a random control on the same stream their median percentile '
        'is 36.1 and only 4 of 10 sit above the control median -- so on unseen '
        'years they are no better than strategies drawn at random from the '
        'same universe. Family and control are also indistinguishable. '
        'THE REPORT WAS EMPTY ON FIRST WRITE: the reader joined the universe '
        'csv to the bank on `bank_row`, but G2.run banks by POSITION in the '
        'combos list it is handed, so the join hit 27 of 4,008 rows and a '
        'defensive `continue` dropped the rest while every stage reported OK. '
        'The join is now on `sid`, which the bank carries itself.')
    # ---- THE NNFX BUILD SECTION (HANDOFF 0m). Standing rule: every result
    # gets an app tab, and a markdown file on disk does not satisfy it.
    ND = os.path.join(ROOTOUT, 'nnfx')
    def nd(name, cols=None, head=80):
        return _recs(os.path.join(ND, name), cols=cols, head=head)
    sec['nnfx'] = dict(
        note=('Layer 2 rebuilt the NNFX way: one algorithm, one piece at a '
              'time, few candidates per stage. Eleven-step walk; unseen trade '
              'years 2010-2015 are the BUILD evidence and 2016-2020 are '
              'computed and stored but NOT shown until the confirm is called.'),
        power=nd('power_test_blindness.csv'),
        power_floors=nd('power_test_true_floors.csv'),
        scorer=nd('scorer_consequence.csv'),
        stage1_c1_flip=nd('stage1_c1_flip_only_walkbuild.csv'),
        stage1_c1_risk=nd('stage1_c1_canonical_risk_walkbuild.csv'),
        stage1_base_flip=nd('stage1_base_flip_only_walkbuild.csv'),
        stage1_base_risk=nd('stage1_base_canonical_risk_walkbuild.csv'),
        select_c1_flip=nd('stage1_c1_flip_only_select.csv'),
        select_c1_risk=nd('stage1_c1_canonical_risk_select.csv'),
        select_base_flip=nd('stage1_base_flip_only_select.csv'),
        select_base_risk=nd('stage1_base_canonical_risk_select.csv'),
        market=nd('market_switch_corr.csv'),
        ledger_n=(sum(1 for _ in open(os.path.join(ND, 'CANDIDATE_LEDGER.csv'))) - 1
                  if os.path.exists(os.path.join(ND, 'CANDIDATE_LEDGER.csv')) else 0),
    )
    # ---- STAGE 1 R2 (the rerun with all eight items applied)
    sec['nnfx']['r2'] = dict(
        note=('Stage 1 R2 supersedes stage 1. Costs charged in a declared '
              'notional, true chronological drawdowns on the daily '
              'mark-to-market series, ambiguous bars resolved from the hourly '
              'bid/ask path, eleven unseen trade years 2005-2015 for the fixed '
              'settings, three risk plans declared in advance, a '
              'block-bootstrap t beside the yearly t, and luck floors from the '
              'random-entry null rather than from a formula.'),
        ambiguity=nd('stage1r2_ambiguity_delta.csv'),
        power_boot=nd('power_test_bootstrap.csv'),
        zero_edge=nd('condition4_zero_edge.csv', head=40),
    )
    for kind in ('c1', 'base'):
        for v in ('flip_only', 'jack', 'textbook'):
            sec['nnfx']['r2']['sum_%s_%s' % (kind, v)] = nd(
                'stage1r2_%s_%s_summary.csv' % (kind, v),
                cols=['indicator', 'setting', 'n_entered', 'trades_per_year',
                      'mean_bars', 'R_gross_per_trade', 'R_net_per_trade',
                      'cost_per_trade', 'R_net_per_year', 'years',
                      'years_positive', 'worst_year', 'worst_dip_R',
                      't_yearly', 't_block_boot', 'null_p',
                      'floor_emp_alone', 'floor_emp_best_of_family'], head=120)
            sec['nnfx']['r2']['sel_%s_%s' % (kind, v)] = nd(
                'stage1r2_%s_%s_select.csv' % (kind, v))
    sec['nnfx']['r2'] = {k: v for k, v in sec['nnfx']['r2'].items()
                         if not (isinstance(v, list) and not v)}
    # ---- STAGE 2 (the baseline added to C1) and ENGINE AUDIT 2.
    # Jack's picks, 24 Nov. The side filter is in every ruleset but the
    # control, so the three other rules are INCREMENTS over it -- the note
    # carries that, because a reader comparing `side_dist` against the bare C1
    # would read the side filter's effect into the distance rule.
    sec['nnfx']['s2'] = dict(
        note=('Stage 2: the baseline added to C1, on Jack\'s picks '
              '(ichimoku / schaff_trend_cycle / halftrend plus the rolling '
              'top 3; sma / hma / t3). jack plan is the main version, '
              'textbook beside it. The baseline SIDE FILTER cannot be '
              'switched off -- every entry route gates on agreement, which '
              'contains side -- so `side` is the floor and the distance, '
              'cross-entry and cross-exit rows are INCREMENTS OVER IT, not '
              'over the bare C1.'),
        report=nd('stage2_picks_report.csv',
                  cols=['c1', 'base', 'variant', 'ruleset', 'R_net_per_year',
                        'R_net_per_trade', 'R_gross_per_trade',
                        'trades_per_year', 'mean_bars', 'years_positive',
                        'worst_year', 'worst_dip_R', 'R_per_year_per_dip',
                        't_yearly', 't_block_boot', 'null_p',
                        'clears_alone', 'clears_best_of_family'], head=160),
        paired=nd('stage2_picks_paired.csv',
                  cols=['c1', 'base', 'variant', 'ruleset', 'days',
                        'R_without', 'R_with', 'delta_R', 'delta_R_per_year',
                        'delta_t_block_boot', 'delta_t_yearly',
                        'years_delta_positive', 'days_with_only',
                        'days_without_only'], head=160),
        rolling=nd('stage2_rolling_sweep.csv', head=120),
        rolling_picks=nd('stage2_rolling_picks.csv', head=80),
        costcap=nd('stage2_costcap.csv', head=200),
        fewer=nd('stage2_fewer.csv', head=200),
        prop=nd('stage2_picks_prop.csv', head=200),
        neutral=nd('stage2_picks_neutralcheck.csv', head=40),
        grid=nd('stage2_picks_grid.csv', head=200),
    )
    # ---- STAGE 3 (a second confirmation) and the STAGE 4 volume preview.
    sec['nnfx']['s3'] = dict(
        note=('Stage 3: a second confirmation added to the three Jack carried '
              'forward (A ichimoku+sma full_nnfx, B schaff+sma side_xentry, '
              'C halftrend+sma full_nnfx). Five C2 candidates declared before '
              'anything ran: the other two C1 picks, kalman_filter, dspo, and '
              'CURRENCY AGREEMENT swept N 3-6. READ THE DIP CHECK FIRST: '
              '15 January 2015, one short EURCHF worth +74.996 R, is 56% to '
              '137% of each of these candidates over 2010-2015, and four of '
              'the six base/plan combinations are NEGATIVE without that single '
              'day. Only the C2 setting is tuned here; the C1 and baseline '
              'settings are stage 2\'s, unchanged, so the paired test changes '
              'one thing.'),
        zeroedge=nd('stage3_zeroedge.csv', head=40),
        report=nd('stage3_report.csv',
                  cols=['base', 'variant', 'c2', 'picked_c2_opts', 'n_entered',
                        'trades_per_year', 'R_gross_per_trade',
                        'R_net_per_trade', 'R_net_per_year', 'years_positive',
                        'worst_year', 'worst_dip_R', 'R_per_year_per_dip',
                        't_yearly', 't_block_boot', 'null_p', 'clears_alone'],
                  head=160),
        paired=nd('stage3_paired.csv',
                  cols=['base', 'variant', 'c2', 'picked_c2_opts', 'dR_total',
                        'dR_per_year', 'years_diff_positive', 'years',
                        't_block_boot_diff', 'boot_sd_diff', 'trades_without',
                        'trades_with', 'trades_removed', 'pct_trades_removed',
                        'days'], head=160),
        walk=nd('stage3_walk.csv', head=400),
        ccy_rate=nd('stage3_ccy_agreement_rate.csv', head=40),
        stage4=nd('stage4_paired.csv', head=80),
        stage4_picks=nd('stage4_picks.csv', head=200),
    )
    sec['nnfx']['dipcheck'] = dict(
        note=('CHECK 1, Jack 24 Nov. worst_dip_R was wrong wherever plan=2 is '
              'used: nnfx1.daily_series built each leg\'s mark from the FULL '
              'position size while a leg realises half. It cancelled at the '
              'exit bar, so every TOTAL reconciled to the last decimal and '
              'guard 33 passed. On ichimoku+sma full_nnfx (jack) the 15 Jan '
              '2015 SNB day showed +101.62 R then -50.18 R where the truth is '
              '+51.29 then -0.34, inventing the peak the 54.93 R dip was '
              'measured down from. The fixed dip is 22.83 R and the next '
              'largest day in six years is 5.92 R. Guard 36 pins it.'),
        snb_dependence=nd('dipcheck_snb_dependence.csv', head=20),
        snb_by_pair=nd('dipcheck_snb_by_pair.csv', head=30),
        dips_before=nd('dipcheck_dips_stitched.csv', head=10),
        dips_after=nd('dipcheck_dips_corrected.csv', head=10),
    )
    # ---- THE THREE STANDING RULES JACK SET ON 25 NOV.
    # STANDING RULE: every result gets an app tab. These are the curves he has
    # to pick X off, so they are not optional.
    sec['nnfx']['rules'] = dict(
        note=('Jack 25 Nov, three standing rules, all on in every Layer 2 '
              'number: (1) LEVERAGE CAP -- all open positions summed, 1:30, '
              'new entries SCALED DOWN to fit, never skipped, plus the '
              'GAUNTLET size cap. (2) PEG GUARD -- no new entry while a '
              'pair\'s ATR/price is below X times the 28-pair median that '
              'day, one bar lagged. X = 0.33 is DECIDED, picked off '
              'pegguard_curve on 25 Nov. (3) PER-PAIR FLOOR -- 5% causal, his '
              'decided rule 1 of 7 Sep. '
              'THE FINDING: from X = 0.10 to 0.33 the ONLY pair ever flagged '
              'in 24 years of 28-pair data is EURCHF. Turning the guard on '
              'removes 1 to 3 trades and takes 25 to 49 R with them in every '
              'one of the six base/plan cells, because at any X of 0.20 or '
              'above it blocks the EURCHF entry of 2 Jan 2015. '
              'THE UNIT, CORRECTED 25 Nov: that trade was quoted at +74.996 R '
              'for two days, which is the engine\'s RAW r column. Every '
              'candidate total here is in the restated 1.5-ATR unit, where '
              'the same trade is +49.997 R uncapped and about +34 R at '
              'achievable size -- see snb_trade_value and guard 40. It is '
              'still the largest single trade in the book and still what the '
              'guard deletes, but it is NOT larger than the whole result. '
              'The ATR bucket table is also net of cost now; it was gross, '
              'so its shares were taken against the wrong denominator.'),
        pegguard_curve=nd('pegguard_curve.csv', head=20),
        pegguard_effect=nd('pegguard_effect_abc.csv', head=60),
        floor_curve_abc=nd('floor_curve_abc.csv', head=80),
        floor_curve_stage1=nd('floor_curve_stage1.csv', head=40),
        floor_leaders_stage1=nd('floor_leaders_stage1.csv', head=200),
        atr_buckets=nd('atr_buckets_abc.csv', head=80),
        snb_trade_value=nd('snb_trade_value.csv', head=20),
        zero_edge=nd('condition4_zero_edge.csv', head=600),
    )
    sec['nnfx']['gapfill'] = dict(
        note=('ITEM 1, Jack 25 Nov -- WHAT A STOP ACTUALLY FILLS AT. The '
              'engine filled a stop at the stop price whenever the daily bar '
              'did not OPEN beyond it, so an overnight gap was handled and an '
              'INTRADAY one was not. EURCHF on 15 Jan 2015 is the case: the '
              'daily bar opens at 1.2008, above every long stop held, while '
              'the hourly bid went 1.20083 open, 1.16777 low at 09:00 UTC, '
              'and the next hour opened at 1.03592. A long stop at 1.10 was '
              'booked at 1.10. STANDING NOW (l2engine._gap_px, pre-flight '
              'guard 41): a stop fills at the first tradable price at or '
              'beyond it -- the daily open for an overnight gap, the '
              'breaching hour\'s open on the FILL SIDE (bid for a long exit, '
              'ask for a short) for an intraday one, the stop itself only '
              'where price was genuinely quoted through it. The hourly-OFF '
              'path is byte-identical to the pre-patch engine, SHA '
              'e5264776bbacc833 both ways. '
              'THE RESOLUTION LIMIT: an hour is not a tick. The de-peg fits '
              'inside the 09:00 bar, whose own range covers any stop near the '
              'peg -- so a 1.5 ATR stop is NOT seen as gapped and still fills '
              'at the stop. snb_long_eurchf therefore gives three fills: the '
              'stop, the hourly rule, and the BOUND (the breaching hour\'s '
              'far extreme). The bound is a bound, not a claim. '
              'WHAT IT IS WORTH: on A, B and C it changes no verdict -- the '
              'largest move to a candidate total is about 2.3 R over six '
              'years and the worst single trade gets ~5% worse. On a LONG '
              'EURCHF into the de-peg it is worth -1.000 R booked against a '
              '-20.100 R bound at a 1.5 ATR stop, and -20.667 -> -99.949 R at '
              'a 31 ATR stop where the hourly path CAN prove it. The leverage '
              'cap scales none of it: that position is 7.3:1, inside the '
              '1:30 limit, so capped size equals engine size.'),
        snb_long=nd('snb_long_eurchf.csv', head=30),
        effect=nd('gap_fill_effect.csv', head=20),
        trades=nd('gap_fill_trades.csv', head=60),
        deciles=nd('gap_stopout_deciles.csv', head=200),
        effect_defaults=nd('gap_fill_effect_defaults.csv', head=20),
        deciles_defaults=nd('gap_stopout_deciles_defaults.csv', head=200),
    )
    sec['nnfx']['quiet'] = dict(
        note=('ITEM 2, Jack 25 Nov -- THE QUIET-ENTRY TEST, run as a declared '
              'hypothesis because the finding behind it was found by LOOKING. '
              'Q is the cut: a pair may enter only while its own one-bar-'
              'lagged ATR/price is at or below its own EXPANDING Q-th '
              'percentile. Q = 1.00 is the rule OFF and takes the identical '
              'code path, which is what lets the curve end at the unfiltered '
              'candidate. A bar inside the first 250 bars, where the '
              'percentile is not yet defined, is BLOCKED -- allowing it '
              'would make the rule look free on exactly the sample it cannot '
              'police. '
              'THE THREE PASS CONDITIONS WERE WRITTEN DOWN BEFORE THE RUN: '
              '(1) the walk-forward version must beat its own control on the '
              'paired test; (2) the fixed-Q curve must be a broad plateau, '
              'not a spike, because Q was swept and the best of ten tries is '
              'a maximum; (3) the effect must appear outside ichimoku. '
              'Read QUIET_ENTRY.md for the verdict against all three.'),
        deciles=nd('quiet_deciles_c1.csv', head=450),
        summary=nd('quiet_deciles_summary.csv', head=60),
        null=nd('quiet_deciles_null.csv', head=450),
        fixedq=nd('quiet_fixedq.csv', head=40),
        walkq=nd('quiet_walkq.csv', head=40),
        paired=nd('quiet_paired.csv', head=20),
        floor_cross=nd('quiet_floor_cross.csv', head=60),
        blocked=nd('quiet_blocked_share.csv', head=320),
    )
    sec['nnfx']['bank'] = dict(
        note=('ITEM 3, Jack 25 Nov -- THE PER-PAIR BANK AND THE PAIR GROUPS. '
              'The unit of account changed: the 12%/yr target is for the '
              'BOOK, so every candidate is banked PER PAIR, PER DIRECTION, '
              'PER YEAR as the primary output. The leverage cap is applied '
              'over the whole 28-pair frame and THEN split, so a group\'s R '
              'is its share of a book that was achievable AS A WHOLE. Years '
              'are labelled tune (2005-2009, may choose, never reported), '
              'unseen (2010-2015, the only reportable block) and sealed '
              '(2016-2020, computed and NOT reported). '
              'THE HEADLINE IS NEGATIVE: the edge is NOT pair-specific in any '
              'way a tuning-year pick can find. Pooled over all 28 pairs the '
              'selection rule makes -50.960 R over the six unseen years; '
              'every grouping is WORSE; and the Layer 1 character grouping '
              'is worse than its own shuffled labels (null p 0.987, z '
              '-2.274). AND YET the hindsight ceiling for a per-pair '
              'assignment is +520.643 R over the same years -- the '
              'dispersion is real and no tested rule reaches it. '
              'ALSO: pair character does not persist. Trendiness measured '
              'before 2010 correlates -0.456 with 2010-2015 and only 21.4% '
              'of pairs keep their tercile label. Cost per ATR does persist '
              '(+0.919, 64.3%). '
              'NOTHING IN THE BANK IS A SELECTION: 28 pairs x 2 directions '
              'is 56 ways to find a winner by luck inside each candidate.'),
        bank_cand=nd('per_pair_bank_cand.csv', head=60),
        bank_pair=nd('per_pair_bank_pair.csv', head=700),
        groups=nd('pair_groups.csv', head=40),
        stability=nd('pair_groups_stability.csv', head=40),
        assign=nd('group_assign.csv', head=20),
        assign_steps=nd('group_assign_steps.csv', head=400),
    )
    sec['nnfx']['meanrev'] = dict(
        note=('ITEM 4, Jack 25 Nov -- A SECOND TYPE OF STRATEGY: DECLARED '
              'MEAN REVERSION, 3 variants, NO SEARCH. The rule is '
              'code/strat.py:52 from the early project work (z-score against '
              'a rolling n-bar mean, long at z <= -entry, short at z >= '
              'entry, flat at |z| < 0.1) and its evidence is HANDOFF_3.md '
              'section 9: mean OOS Sharpe +0.109 with 69% of pairs positive '
              'against momentum at -0.225, best config n=60 entry=2.0. '
              'MR60 is that config; MR20 and MR120 are one faster and one '
              'slower. `entry` is NOT varied -- that would be the search '
              'item 4 forbids. Stop at one further sigma beyond the entry '
              'stretch, target the mean, realistic gap fills, hourly '
              'ambiguity resolution, leverage cap, R in the same 1.5-ATR '
              'unit as every other Layer 2 number. '
              'ONE CORRECTION TO THE BRIEF: the early work\'s CONDITION was '
              'the 9-box (HANDOFF_3 section 10), NOT a half-life or a '
              'stationarity test -- the repo has a Hurst exponent and '
              'neither of the other two, so both are new and built here. '
              'AND THE HALF-LIFE IS NOT BINDING: it passes on 96.7% to 99.9% '
              'of bars while the Dickey-Fuller test passes on 9.3% (MR120), '
              '18.0% (MR60) and 90.4% (MR20), so "both agree" IS the ADF '
              'test alone. '
              'RESULTS: 7 of 24 cells positive, NOT ONE reaching |t| = 2, '
              'and every cell that does reach |t| >= 2 is negative. The '
              'condition does all the work -- MR120 goes from -83.542 R '
              'unconditional to +18.507 R conditional on all 28 pairs, worst '
              'dip 222.5 -> 23.6. The Layer 1 RANGING gate helps in only 1 of '
              '6 conditional comparisons and is in-sample anyway. '
              '"Mean reversion for range-prone pairs" is NOT supported on R '
              'per trade (5 of 12) or R per dip (6 of 12). '
              'FLAGGED: every positive cell is over the 10% crisis threshold '
              'and MR120 takes 73.6% of its R from crisis windows. '
              'THE ONE THING THAT IS NOT BORDERLINE: every variant is '
              'NEGATIVELY correlated with candidate A, -0.124 to -0.397.'),
        condition=nd('mr_condition.csv', head=100),
        summary=nd('mr_summary.csv', head=40),
        per_pair=nd('mr_per_pair.csv', head=200),
        corr=nd('mr_corr.csv', head=20),
    )
    sec['nnfx']['audit2'] = dict(
        note=('Engine audit 2, measurement only. The daily bar is '
              '(16:00 NY D-1, 16:00 NY D], NOT 17:00. Overnight financing is '
              'charged NOWHERE, and its mean on these candidates is POSITIVE, '
              'so adding it would flatter them. Tick volume is usable from '
              '2005 and is a tick COUNT, not traded size.'),
        fillprice=nd('audit2_fillprice.csv', head=160),
        financing=nd('audit2_financing.csv', head=40),
        cost_by_pair=nd('audit2_cost_by_pair.csv', head=40),
        cost_by_year=nd('audit2_cost_by_year.csv', head=40),
        tickvolume=nd('audit2_tickvolume.csv', head=200),
    )
    for _k in ('s2', 'audit2', 'rules'):
        sec['nnfx'][_k] = {k: v for k, v in sec['nnfx'][_k].items()
                           if not (isinstance(v, list) and not v)}
    sec['nnfx'] = {k: v for k, v in sec['nnfx'].items()
                   if not (isinstance(v, list) and not v)}

    sec['curve'] = {k: v for k, v in sec['curve'].items() if v}
    sec['rankcorr'] = {k: v for k, v in sec['rankcorr'].items() if v}
    for root in (os.path.join(_R, 'app_data.json'), os.path.join(ROOTOUT, 'app_data.json')):
        if not os.path.exists(root):
            continue
        D = json.load(open(root))
        D['l2_restart'] = sec
        json.dump(D, open(root, 'w'))
        print('wired into %s' % root, flush=True)

    ui = os.path.join(_R, 'app_ui.js')
    s = open(ui).read()
    # NOT `'r2Fill' in s` -- tr2Fill contains it as a substring and the guard
    # silently skipped the whole wiring on the first run.
    if 'const r2Fill=' in s:
        print('app_ui.js already carries the L2 restart tab', flush=True)
        return
    anchor = '<button role="tab" aria-selected="false" data-t="tq">Trend quality</button>'
    assert s.count(anchor) == 1, 'app_ui.js: nav anchor not found'
    s = s.replace(anchor, anchor + NL + '<button role="tab" aria-selected="false" data-t="r2">L2 restart</button>')
    body = ('<section id="r2" hidden>' + NL +
            '<h3>Layer 2 restart: the honest gate 1</h3>' + NL +
            '<div class="note">The gate 1 on disk took its score over 2011-2020 -- every year Layer 2' + NL +
            'afterwards called blind -- and charged no costs, so its survivors were chosen on the years' + NL +
            'their record was then quoted on. This is the rebuild. Every combination is scored at' + NL +
            'defaults with costs on; each trade is banked by the calendar year of its entry bar; the cut' + NL +
            'reads tune years only. Four streams are measured and none is selected on. The cut is swept' + NL +
            'over its whole range and reported as a curve, with the identity null beside it. Nothing from' + NL +
            'the old Layer 2 was deleted.</div>' + NL + '<div id="r2body"></div>' + NL + '</section>' + NL)
    s = s.replace('<section id="tq" hidden>', body + '<section id="tq" hidden>', 1)
    old_t = "'ex','pt','hz','rd','xd','pc','gl','ar','vd','dc','tr2','tq','cw'];"
    assert s.count(old_t) == 1, 'app_ui.js: TABS list not found'
    s = s.replace(old_t, "'ex','pt','hz','rd','xd','pc','gl','ar','vd','dc','tr2','tq','r2','cw'];")
    old_s = "   if(t==='tq')tqFill();"
    assert s.count(old_s) == 1, 'app_ui.js: show() hook not found'
    s = s.replace(old_s, old_s + NL + "   if(t==='r2')r2Fill();")
    s = s.rstrip() + NL + TAB_JS
    open(ui, 'w').write(s)
    print('app_ui.js: L2 restart tab added', flush=True)


TAB_JS = """
const r2Fill=()=>{const el=document.getElementById('r2body');if(!el||el.dataset.done)return;
 const D=(window.DATA||{}).l2_restart;if(!D){el.innerHTML='<div class="note">no restart section in app_data.json</div>';return;}
 const tbl=(rows,cols,title)=>{if(!rows||!rows.length)return '';
  const c=cols||Object.keys(rows[0]);
  return '<h4>'+title+'</h4><div style="overflow-x:auto"><table><thead><tr>'+c.map(k=>'<th>'+k+'</th>').join('')+'</tr></thead><tbody>'+
   rows.map(r=>'<tr>'+c.map(k=>{let v=r[k];if(typeof v==='number')v=Math.abs(v)>=1000?v.toLocaleString():(Number.isInteger(v)?v:v.toFixed(4));return '<td>'+(v===null||v===undefined?'':v)+'</td>';}).join('')+'</tr>').join('')+
   '</tbody></table></div>';};
 let h='<div class="note">'+D.note+'</div>';
 h+=tbl(D.modes,['mode','exit_rule','uses_exit_slot','c1','c2','vol','base','exit_ind','combinations'],'The three modes, exactly one active per test');
 h+=tbl(D.contaminations,['n','name','touches_gate1'],'Which faults touched gate 1');
 h+=tbl(D.parity,null,'The _r2 code path against the shipped Scorer (0 mismatches required)');
 h+=tbl(D.timing,['mode','combinations','basis','per_combo_s','core_hours','mac_hours','bank_gb'],'Measured cost of a full honest gate 1');
 Object.keys(D.curve||{}).forEach(m=>{h+=tbl(D.curve[m],['stream','cut_tune_R','n_pass','pct_pass','n_families','n_lone_survivor_families','grade_R_pass','trade_R_pass','trade_R_fail','null_trade_R_mean','null_p_one_sided'],'Mode '+m+' gate 1 curve, pooled over the five windows (cut reads tune years only)');});
 Object.keys(D.rankcorr||{}).forEach(m=>{h+=tbl(D.rankcorr[m],['window','stream','n_eligible','spearman_tune_to_trade','p'],'Mode '+m+': does the tune-year rank survive to the trade year?');});
 h+=tbl(D.superseded,null,'Superseded, headed, kept in full');
 el.innerHTML=h;el.dataset.done='1';};
"""


if __name__ == '__main__':
    stage_app()
