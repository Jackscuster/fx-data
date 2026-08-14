import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""REFIT STABILITY. The fifth present-tense validation, and the one never run.

THE QUESTION. If the classifier's fitted quantities are re-derived from data
ending at earlier dates, do the state calls stay the same? If they do not, live
behaviour will not match the validated history, because live IS a refit -- every
day adds data that would move a cut point if anyone re-estimated it.

MEASUREMENT ONLY. Nothing here changes a state call or the shipped classifier.

WHAT IS REFIT, AND WHAT IS NOT. This inventory is a deliverable in its own right,
because "refit stability" means nothing until it says which numbers move.

  REFIT -- estimated from data, moves with the vintage
    zfit mean and sd, per pair, per score component. Six components survive
      into the shipped score (disp, seq | hold, fails, inside, revert -- `tests`
      is dropped by DROP_TESTS), so 6 x 28 x 2 = 336 numbers.
    The two score cut points mt, mc -- pooled medians of the bumped trend score
      and the chop score over the fit window. 2 numbers, global, not per pair.
    The activity tercile reference distribution, per pair: fit_frac builds the
      empirical CDF of the scale axis on the fit window. The operative cuts are
      its 1/3 and 2/3 quantiles, so 2 x 28 = 56 numbers.
    336 + 2 + 56 = 394 fitted numbers in total.

  FIXED BY CONSTRUCTION -- identical in every vintage
    W = 106 lookback, N_SCORE = 19 swing width, KFAIL = 20, VOLWIN = 60,
    L = 28 for the scale axis, DWELL = 5 confirmation bars, BAND = 0.25
    hysteresis, EQUAL WEIGHTS inside each score, the 2x2 cell definitions, the
    tercile boundaries at 1/3 and 2/3, and the median cut at 0.5.

  SELECTED ONCE ON IS AND HELD FIXED -- the honest caveat
    DROP_TESTS = True and BUMP = 0.75 were CHOSEN by an in-sample comparison.
    They are not re-selected per vintage, so what follows measures the stability
    of the ESTIMATED parameters, not of the selection decisions. Re-running those
    choices at each vintage is a different and larger test; it is not claimed here.

THE BUILT-IN CONTROL. The shipped classifier fits on index < 2016-01-01, which is
identical to the 2015 vintage. That vintage MUST reproduce the shipped states
exactly, and the run asserts it. A refit test that cannot reproduce its own
starting point is measuring its own plumbing.

A PRIOR VERSION OF THIS TEST RETURNED 100.0% and was wrong. fit_frac's docstring
records why: the cut points were built with .rank(pct=True) over the whole sample,
so refitting changed nothing because nothing was actually being fitted. That bug
is fixed; a suspiciously perfect number here would mean it had returned.

Writes results/refit_inventory.csv, refit_agreement.csv, refit_disagreement.csv,
refit_thresholds.csv + .txt companions.
"""
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
SHIPPED = os.path.join(ROOTOUT, 'states_g4_twoscore4.csv')
SPLIT = pd.Timestamp('2016-01-01')
VINTAGES = [2009, 2012, 2015, 2018, 2021, 2024]
CELLS = ['trending', 'ranging', 'trend-in-range', 'neither']

from twoscores import raw_parts, classify
from classifier import zfit, fit_frac
from ninestate import raw_axes, tercile
from final import DROP_TESTS, BUMP, ACTW
from drivers import hdr

INVENTORY = [
    dict(component='zfit mean & sd, per pair per score component', kind='REFIT',
         count=336,
         detail='6 components survive into the shipped score (disp, seq | hold, '
                'fails, inside, revert; `tests` dropped by DROP_TESTS) x 28 '
                'pairs x 2 statistics'),
    dict(component='score cut points mt, mc', kind='REFIT', count=2,
         detail='pooled medians of the bumped trend score and the chop score '
                'over the fit window; global, not per pair'),
    dict(component='activity tercile cuts, per pair', kind='REFIT', count=56,
         detail='fit_frac builds the empirical CDF of the scale axis on the fit '
                'window; the operative cuts are its 1/3 and 2/3 quantiles'),
    dict(component='W = 106 lookback', kind='FIXED', count=0,
         detail='locked window, not estimated'),
    dict(component='N_SCORE = 19 swing width', kind='FIXED', count=0,
         detail='locked swing width'),
    dict(component='KFAIL = 20, VOLWIN = 60, L = 28', kind='FIXED', count=0,
         detail='failed-swing window, vol window, scale-axis lookback'),
    dict(component='DWELL = 5 confirmation bars', kind='FIXED', count=0,
         detail='categorical hysteresis on the label'),
    dict(component='BAND = 0.25 tercile hysteresis', kind='FIXED', count=0,
         detail='hysteresis band around each tercile boundary'),
    dict(component='equal weights inside each score', kind='FIXED', count=0,
         detail='deliberately not fitted -- fitting weights would be a search '
                'against a target, and the target is a description'),
    dict(component='2x2 cell definitions, 1/3-2/3 and 0.5 cuts', kind='FIXED',
         count=0, detail='boundaries by construction, not estimated'),
    dict(component='DROP_TESTS = True', kind='SELECTED-ON-IS', count=0,
         detail='chosen by in-sample comparison, held fixed across vintages'),
    dict(component='BUMP = 0.75', kind='SELECTED-ON-IS', count=0,
         detail='chosen by in-sample comparison, held fixed across vintages'),
]


def build(T, C, SCALE, fit):
    """One vintage: refit everything estimated, return labels and the numbers."""
    zt, zc = zfit(T, fit), zfit(C, fit)
    tr = sum(zt[k] for k in T)
    ch = sum(zc[k] for k in C)
    a = tercile(SCALE, fit).replace({0.0: 'weak', 1.0: 'medium', 2.0: 'strong'})
    a = a.where(a.isin(list(ACTW)))
    trb = tr - a.replace(ACTW).astype(float) * BUMP
    lab, (mt, mc) = classify(trb, ch, fit)
    # The cut points are meaningless as percentages -- mc sits within 0.005 of
    # zero, so a relative change against it reads in the hundreds of percent and
    # says nothing. Both are therefore also expressed in SD UNITS OF THE SCORE
    # THEY CUT, which is the only scale on which "how far did the cut move"
    # answers the question.
    par = dict(mt=float(mt), mc=float(mc),
               mt_in_sd=float(mt / np.nanstd(trb.values[fit])),
               mc_in_sd=float(mc / np.nanstd(ch.values[fit])),
               sd_trend_score=float(np.nanstd(trb.values[fit])),
               sd_chop_score=float(np.nanstd(ch.values[fit])))
    for nm, D in (('T', T), ('C', C)):
        for k, v in D.items():
            par['mean_%s' % k] = float(v[fit].mean().mean())
            par['sd_%s' % k] = float(v[fit].std().mean())
    q = SCALE[fit].quantile([1 / 3, 2 / 3])
    par['act_cut_lo'] = float(q.loc[1 / 3].mean())
    par['act_cut_hi'] = float(q.loc[2 / 3].mean())
    return lab, par


def runs_of(mask):
    """Lengths of contiguous True runs in a boolean 1-D array."""
    v = np.asarray(mask, bool)
    if not v.any():
        return np.array([], int)
    d = np.diff(np.concatenate(([0], v.view(np.int8), [0])))
    return np.flatnonzero(d == -1) - np.flatnonzero(d == 1)


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    ship = pd.read_csv(SHIPPED, index_col=0, parse_dates=True, comment='#')
    print('REFIT STABILITY -- do the state calls survive re-estimation?')
    INV = pd.DataFrame(INVENTORY)
    INV.to_csv(os.path.join(ROOTOUT, 'refit_inventory.csv'), index=False)
    nref = int(INV[INV.kind == 'REFIT']['count'].sum())
    print('\nWHAT IS REFIT (the inventory is itself a deliverable)')
    for _, r in INV.iterrows():
        print('  %-14s %-46s %s' % (r.kind, r.component,
                                    ('%d numbers' % r['count']) if r['count']
                                    else r.detail[:40]))
    print('  TOTAL FITTED NUMBERS: %d' % nref)

    # raw parts do NOT depend on the fit window -- compute once
    T, C = raw_parts(px)
    C = dict(C)
    if DROP_TESTS:
        C.pop('tests', None)
    SCALE = raw_axes(px)['scale']
    print('\n  components in the shipped score: trend %s | chop %s'
          % (', '.join(T), ', '.join(C)))

    labs, pars = {}, {}
    for y in VINTAGES:
        fit = np.asarray(px.index <= pd.Timestamp('%d-12-31' % y))
        lab, par = build(T, C, SCALE, fit)
        labs[y], pars[y] = lab, par
        print('  vintage %d fitted on %d bars (to %s)'
              % (y, int(fit.sum()), px.index[fit].max().date()))

    # ---- the control: 2015 must reproduce the shipped classifier exactly ----
    idx = ship.index.intersection(labs[2015].index)
    a15 = labs[2015].reindex(idx)[ship.columns]
    b15 = ship.reindex(idx)
    both = a15.notna() & b15.notna()
    same = float(((a15 == b15) & both).sum().sum() / both.sum().sum())
    print('\nCONTROL -- the 2015 vintage IS the shipped fit window.')
    print('  agreement with shipped: %.4f over %d labelled pair-bars'
          % (same, int(both.sum().sum())))
    assert same > 0.9999, ('the 2015 refit does not reproduce the shipped '
                           'classifier (%.4f) -- the harness is wrong, not the '
                           'classifier' % same)
    print('  PASS. The harness reproduces its own starting point.')

    # ---------------- AGREEMENT ----------------
    rows, drows = [], []
    for y in VINTAGES:
        A = labs[y].reindex(idx)[ship.columns]
        B = ship.reindex(idx)
        ok = A.notna() & B.notna()
        eq = (A == B) & ok
        post = pd.Series(idx > pd.Timestamp('%d-12-31' % y), index=idx)
        for scope, m in (('all overlapping days', pd.Series(True, index=idx)),
                         ('post-vintage only', post)):
            o2 = ok & m.values[:, None]
            if not o2.sum().sum():
                continue
            e2 = eq & m.values[:, None]
            agree = float(e2.sum().sum() / o2.sum().sum())
            # chance agreement from the two marginal distributions
            pa = A.where(o2).stack().value_counts(normalize=True)
            pb = B.where(o2).stack().value_counts(normalize=True)
            exp = float(sum(pa.get(s, 0) * pb.get(s, 0) for s in CELLS))
            rows.append(dict(vintage=y, scope=scope, state='ALL',
                             pair_bars=int(o2.sum().sum()), agreement=agree,
                             expected=exp, kappa=(agree - exp) / (1 - exp)))
            for s in CELLS:
                sel = (B == s) & o2
                n = int(sel.sum().sum())
                if n < 50:
                    continue
                rows.append(dict(vintage=y, scope=scope, state=s, pair_bars=n,
                                 agreement=float((eq & sel).sum().sum() / n),
                                 expected=np.nan, kappa=np.nan))
        # ---- structure of the disagreements, post-vintage ----
        dis = (~eq) & ok & post.values[:, None]
        allr = []
        for p in ship.columns:
            allr.append(runs_of(dis[p].values))
        allr = np.concatenate(allr) if allr else np.array([], int)
        nbars = int(dis.sum().sum())
        if nbars:
            in5 = float(allr[allr >= 5].sum() / allr.sum())
            in20 = float(allr[allr >= 20].sum() / allr.sum())
            med = float(np.median(allr))
        else:
            in5 = in20 = med = np.nan
        # ---- whole-episode relabelling ----
        tot = full = part = clean = 0
        for p in ship.columns:
            v = ship[p].where(post.values).dropna()
            if not len(v):
                continue
            gid = (v != v.shift()).cumsum()
            for _, g in v.groupby(gid):
                if len(g) < 5:
                    continue
                w = labs[y][p].reindex(g.index)
                d = (w != g) & w.notna()
                tot += 1
                if d.sum() == 0:
                    clean += 1
                elif d.sum() == len(g):
                    full += 1
                else:
                    part += 1
        drows.append(dict(vintage=y, disagreeing_bars=nbars,
                          disagreement_runs=int(len(allr)),
                          median_run=med, share_of_bars_in_runs_ge5=in5,
                          share_of_bars_in_runs_ge20=in20,
                          episodes=tot, episodes_untouched=clean,
                          episodes_partly_relabelled=part,
                          episodes_fully_relabelled=full,
                          share_fully_relabelled=full / tot if tot else np.nan))
    AG = pd.DataFrame(rows)
    DG = pd.DataFrame(drows)
    AG.to_csv(os.path.join(ROOTOUT, 'refit_agreement.csv'), index=False)
    DG.to_csv(os.path.join(ROOTOUT, 'refit_disagreement.csv'), index=False)

    print('\nAGREEMENT WITH THE SHIPPED CLASSIFIER')
    print('  %-8s %-22s %10s %10s %8s' % ('vintage', 'scope', 'agreement',
                                          'chance', 'kappa'))
    for _, r in AG[AG.state == 'ALL'].iterrows():
        print('  %-8d %-22s %10.4f %10.4f %8.3f'
              % (r.vintage, r.scope, r.agreement, r.expected, r.kappa))
    print('\n  BY STATE (post-vintage days only, shipped label as reference)')
    print('  %-8s %s' % ('vintage', '  '.join('%-16s' % s for s in CELLS)))
    for y in VINTAGES:
        d = AG[(AG.vintage == y) & (AG.scope == 'post-vintage only')]
        print('  %-8d %s' % (y, '  '.join(
            '%-16s' % ('%.3f' % d[d.state == s].agreement.iloc[0]
                       if len(d[d.state == s]) else '—') for s in CELLS)))

    print('\nWHERE THE DISAGREEMENTS SIT (post-vintage days)')
    print('  %-8s %10s %8s %10s %10s %9s %9s'
          % ('vintage', 'dis. bars', 'med run', 'in runs>=5', 'in runs>=20',
             'episodes', 'fully rel.'))
    for _, r in DG.iterrows():
        print('  %-8d %10d %8.1f %10.3f %10.3f %9d %9.3f'
              % (r.vintage, r.disagreeing_bars, r.median_run,
                 r.share_of_bars_in_runs_ge5, r.share_of_bars_in_runs_ge20,
                 r.episodes, r.share_fully_relabelled))

    # ---------------- THRESHOLD TRAJECTORIES ----------------
    TH = pd.DataFrame(pars).T
    TH.index.name = 'vintage'
    base = TH.loc[2015]
    rel = (TH - base) / base.abs().replace(0, np.nan)
    TH.to_csv(os.path.join(ROOTOUT, 'refit_thresholds.csv'))
    rel.to_csv(os.path.join(ROOTOUT, 'refit_thresholds_relative.csv'))
    print('\nTHRESHOLD TRAJECTORIES (2015 = the shipped fit, as the reference)')
    keys = ['mt', 'mc', 'act_cut_lo', 'act_cut_hi']
    print('  %-12s %s' % ('parameter', '  '.join('%9d' % y for y in VINTAGES)))
    for k in keys:
        print('  %-12s %s' % (k, '  '.join('%9.4f' % TH.loc[y, k]
                                           for y in VINTAGES)))
    print('  --- component means and sds, averaged across the 28 pairs ---')
    for k in [c for c in TH.columns if c.startswith(('mean_', 'sd_'))]:
        print('  %-12s %s' % (k, '  '.join('%9.4f' % TH.loc[y, k]
                                           for y in VINTAGES)))
    mv = rel.drop(index=2015).abs()
    ab = (TH - base).drop(index=2015).abs()
    print('\n  largest move from the shipped values:')
    print('    %-16s %10s %10s   %s' % ('parameter', 'absolute', 'relative',
                                        'vintage'))
    for k in TH.columns:
        print('    %-16s %10.4f %9.1f%%   %s'
              % (k, ab[k].max(), 100 * mv[k].max(), mv[k].idxmax()))
    print('\n  THE CUT POINTS IN SD UNITS OF THE SCORE THEY CUT -- the only')
    print('  scale on which the question is answerable. mc sits within 0.005 of')
    print('  zero, so its RELATIVE move reads in the hundreds of percent and')
    print('  means nothing.')
    for k in ('mt_in_sd', 'mc_in_sd'):
        print('    %-10s %s   max move %.4f sd'
              % (k, '  '.join('%+.4f' % TH.loc[y, k] for y in VINTAGES),
                 ab[k].max()))

    worst = AG[(AG.state == 'ALL') & (AG.scope == 'post-vintage only')]
    lo = worst.loc[worst.agreement.idxmin()]
    hdr(os.path.join(ROOTOUT, 'refit_agreement.csv'),
        'Refit stability -- do the state calls survive re-estimation?',
        'Every fitted quantity is re-derived from data ending at each vintage\n'
        'year and the whole state history is regenerated for all 28 pairs. The\n'
        'shipped classifier fits on index < 2016-01-01, so the 2015 vintage is\n'
        'the shipped fit and MUST reproduce it exactly. The run asserts that;\n'
        'a refit test that cannot reproduce its own starting point is measuring\n'
        'its own plumbing.\n\n'
        'Two scopes are reported. "All overlapping days" includes days inside\n'
        'the vintage\'s own fit window. "POST-VINTAGE ONLY" is the number that\n'
        'matters -- it is the live case, where a cut point estimated on the past\n'
        'is applied to data it never saw.\n\n'
        'Agreement is reported beside the agreement expected from the two\n'
        'marginal distributions alone, and kappa corrects for it. Four states\n'
        'unevenly distributed agree ~27%% of the time by coincidence.\n\n'
        'Worst post-vintage agreement: %.3f (vintage %d).\n'
        % (lo.agreement, int(lo.vintage)))
    hdr(os.path.join(ROOTOUT, 'refit_disagreement.csv'),
        'Are refit disagreements boundary noise or structural drift?',
        'Two different failures look identical in an agreement rate. Scattered\n'
        'single days are BOUNDARY NOISE -- bars sitting on a cut point, which is\n'
        'unavoidable and harmless. Whole episodes relabelled are STRUCTURAL\n'
        'DRIFT -- the classifier telling a different story about the same\n'
        'stretch of market, which is not harmless.\n\n'
        'Runs are contiguous disagreeing bars within one pair. An episode is a\n'
        'run of one shipped state on one pair, at least 5 bars, wholly after the\n'
        'vintage date; it counts as fully relabelled only if EVERY one of its\n'
        'bars disagrees.\n\n'
        'READ THE RUN LENGTHS AGAINST THE DWELL. The classifier requires 5\n'
        'consecutive bars before adopting a new state, so a relabelling cannot\n'
        'be one bar wide by construction and the share of bars sitting in runs\n'
        'of 5 or more is partly forced. The median run of 3-4 bars is BELOW the\n'
        'dwell, which is the informative part: most disagreement is shorter than\n'
        'the confirmation window, i.e. edge-of-threshold noise rather than the\n'
        'classifier adopting a different story.')
    hdr(os.path.join(ROOTOUT, 'refit_inventory.csv'),
        'What is refit, what is fixed, and what was selected once',
        'Refit stability means nothing until it says which numbers move. %d\n'
        'numbers are estimated from data and move with the vintage; the window\n'
        'lengths, dwell, hysteresis band, equal weights and cell boundaries are\n'
        'fixed by construction and move with nothing.\n\n'
        'THE CAVEAT, STATED RATHER THAN BURIED: DROP_TESTS and BUMP were chosen\n'
        'by in-sample comparison and are held fixed across vintages. This\n'
        'measures the stability of the ESTIMATED parameters, not of the\n'
        'SELECTION decisions. Re-running those choices at every vintage is a\n'
        'larger test and is not claimed here.' % nref)
    hdr(os.path.join(ROOTOUT, 'refit_thresholds.csv'),
        'How far each fitted parameter moves across vintages',
        'The 2015 row is the shipped fit and is the reference. mt and mc are the\n'
        'two score cut points; act_cut_lo/hi are the activity tercile cuts\n'
        'averaged across pairs; mean_* and sd_* are the zfit standardisation\n'
        'statistics averaged across the 28 pairs.\n\n'
        'refit_thresholds_relative.csv holds the same table as a fractional\n'
        'change from the 2015 values.')
    print('\nwrote refit_inventory.csv, refit_agreement.csv,')
    print('      refit_disagreement.csv, refit_thresholds.csv,')
    print('      refit_thresholds_relative.csv + .txt')
    return INV, AG, DG, TH


if __name__ == '__main__':
    main()
