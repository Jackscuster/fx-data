import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""KNOB SENSITIVITY. Every hand-picked constant, one at a time.

THE DIRECTIVE THIS ANSWERS. The window turned out to be the classifier's biggest
lever, and the window is derived from a hand-picked swing width. No arbitrary
decision should lead anything, so every constant that was chosen rather than
derived gets the same treatment the window got.

THIS MEASURES. IT CHANGES NOTHING AND PICKS NOTHING. The shipped classifier is
untouched, no setting is proposed, and no knob is compared in order to select a
better value. A knob that scores badly here becomes a candidate for a properly
motivated follow-up -- chosen on IS against a declared criterion and confirmed
once out of sample -- in a LATER run.

THE CONTROL. The unperturbed configuration must reproduce the shipped states at
exactly 100%, asserted, the same regression standard refit.py and windowsens.py
use. Everything below is meaningless if the harness cannot reproduce its own
starting point.

THE EVALUATION LENS: THIS SYSTEM TRADES THE DAILY CHART. Entries are daily and
holds run days to weeks, so agreement and separation are not sufficient. A knob
setting can preserve separation and still be a practical failure by chopping
state runs down to a few bars -- there is nothing to trade in a regime call that
changes twice a week. Median run length and daily flip rate are therefore
reported for every perturbation, and any setting that holds separation while
driving runs materially below ~20 bars is FLAGGED as a practical failure. That
is the same tradeoff that picked the window in the first place (16.4q chose 106
bars for 21-bar range episodes over the last 5% of separation), so it is the
standard here too.

WHAT EACH PERTURBATION IS, DECLARED BEFORE RUNNING. Roughly +/-20-25% on each:

  N swing width        19  -> 15, 23      the lookback's parent
  DWELL                 5  -> 4, 6        confirmation bars
  BAND               0.25  -> 0.20, 0.31  tercile hysteresis
  activity cuts   1/3,2/3  -> (0.25,0.50), (0.417,0.833)   both boundaries moved
                                          25% down and 25% up
  score cut           0.5  -> 0.40, 0.60  the quantile the two scores are cut at
  weights           equal  -> tilt up, tilt down: linearly spaced 0.75..1.25
                                          across each score's components, and
                                          the reverse
  BUMP               0.75  -> 0.56, 0.94
  DROP_TESTS         True  -> False       binary; there is no +/-25% of a flag
  KFAIL                20  -> 15, 25      failed-swing window
  VOLWIN               60  -> 45, 75      volatility normalisation window
  activity lookback    28  -> 21, 35      the scale axis window

SEPARATION IS MEASURED WITH A FIXED RULER. The structural properties in
structval.properties use their own window, which is NOT perturbed by anything
here. If the ruler moved with the machine, every machine would look equally good.

Writes results/knob_sensitivity.csv, knob_perstate.csv, knob_separation.csv
+ .txt companions.
"""
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
SHIPPED = os.path.join(ROOTOUT, 'states_g4_twoscore4.csv')
SPLIT = pd.Timestamp('2016-01-01')
CELLS = ['trending', 'ranging', 'trend-in-range', 'neither']
# The shipped classifier's own median run is 19 bars. An absolute floor of 20
# therefore flags the CONTROL, which is nonsense -- a 1-bar difference on a
# median is noise, not a practical failure. The standard is a MATERIAL drop
# against shipped: 15% or more, i.e. 16 bars or fewer at the shipped 19.
RUN_DROP = 0.85

from twoscores import raw_parts, sep_one_vs_rest, PROPS
from classifier import zfit, fit_frac
from ninestate import raw_axes, hyst
from combined import confirm
from structval import properties
from final import ACTW
from refit import runs_of
from drivers import hdr

DEFAULTS = dict(N=19, Wl=106, dwell=5, band=0.25, act_lo=1 / 3, act_hi=2 / 3,
                score_q=0.5, weights='equal', bump=0.75, drop_tests=True,
                kfail=20, volwin=60, actL=28)

# knob -> (label, shipped value, [(variant label, override dict), ...],
#          rationale tier, rationale text)
# TIERS. FULL: a reason and a comparison are on file. PARTIAL: the value follows
# a construction rule (equal thirds, the median) with no comparison against
# alternatives recorded. NONE: nothing in the code or the handoff.
KNOBS = [
    ('N', 'swing width N', 19,
     [('15', dict(N=15)), ('23', dict(N=23))],
     'FULL', 'YES -- 16.4q. The swing width sets the measured lookback; 19 was locked '
     'for 21-bar range episodes over the last 5% of separation.'),
    ('dwell', 'confirmation dwell', 5,
     [('4', dict(dwell=4)), ('6', dict(dwell=6))],
     'FULL', 'YES -- combined.py records it as fixed on persistence; dwell 1 flickers '
     '(3-bar median runs) and dwell 13 collapses the states.'),
    ('band', 'tercile hysteresis BAND', 0.25,
     [('0.20', dict(band=0.20)), ('0.31', dict(band=0.31))],
     'NONE', 'Nothing in the code or the handoff.'),
    ('act_cuts', 'activity tercile boundaries', '1/3, 2/3',
     [('0.25, 0.50', dict(act_lo=0.25, act_hi=0.50)),
      ('0.417, 0.833', dict(act_lo=0.4167, act_hi=0.8333))],
     'PARTIAL', 'Equal thirds by construction, which is a rule rather than a '
     'fitted choice, but no comparison against other splits is on file.'),
    ('score_q', 'score cut quantile', 0.5,
     [('0.40', dict(score_q=0.40)), ('0.60', dict(score_q=0.60))],
     'FULL', 'DECIDED, not assumed -- scoreq.py. Candidates 0.40/0.45/0.50/'
     '0.55/0.60 judged on IS against a criterion declared before looking '
     '(separation on trend AND chop, median run ~20 bars, no state below 5% '
     'share, default wins ties). 0.40 won IS by 1.1 paired block-bootstrap SE, '
     'then LOST the holdout by 1.9 SE on identical rows -- worse on both axes '
     '(trend 0.1324 vs 0.1354, chop 0.1130 vs 0.1368). 0.50 stays: tested, '
     'median survived. See scoreq_decision.csv and scoreq_regression.csv.'),
    ('weights', 'measurement weights', 'equal',
     [('tilt up', dict(weights='tilt_up')),
      ('tilt down', dict(weights='tilt_down'))],
     'FULL', 'YES -- deliberately not fitted. twoscores.py: fitting weights would be a '
     'search against a target, and the target here is a description.'),
    ('bump', 'activity bump BUMP', 0.75,
     [('0.56', dict(bump=0.5625)), ('0.94', dict(bump=0.9375))],
     'FULL', 'YES -- chosen on IS against a separate activity cut; the margin was '
     '0.002, a tie in practice.'),
    ('drop_tests', 'DROP_TESTS', True,
     [('False (keep tests)', dict(drop_tests=False))],
     'FULL', 'YES -- IS chop |sep| 0.140 -> 0.151 with `tests` dropped.'),
    ('kfail', 'failed-swing window KFAIL', 20,
     [('15', dict(kfail=15)), ('25', dict(kfail=25))],
     'NONE', 'Nothing in the code or the handoff.'),
    ('volwin', 'volatility window VOLWIN', 60,
     [('45', dict(volwin=45)), ('75', dict(volwin=75))],
     'NONE', 'No rationale for the VALUE. The only thing on file is a known PROBLEM: '
     'at L == VOLWIN the scale axis collapses (HANDOFF 677-700).'),
    ('actL', 'activity scale lookback', 28,
     [('21', dict(actL=21)), ('35', dict(actL=35))],
     'PARTIAL', 'Inherited from the 7/28/128 ribbon, not separately motivated.'),
]

_CACHE = {}


def parts(px, N, Wl, kfail, volwin):
    k = (N, Wl, kfail, volwin)
    if k not in _CACHE:
        _CACHE[k] = raw_parts(px, N=N, Wl=Wl, kfail=kfail, volwin=volwin)
    return _CACHE[k]


def wmap(keys, mode):
    ks = list(keys)
    if mode == 'equal' or len(ks) < 2:
        return {k: 1.0 for k in ks}
    w = np.linspace(0.75, 1.25, len(ks))
    if mode == 'tilt_down':
        w = w[::-1]
    return {k: float(x) for k, x in zip(ks, w)}


def tercile_at(x, fit, lo_b, hi_b, band):
    """ninestate.tercile with the two boundaries exposed. At (1/3, 2/3) it is
    that function exactly -- the control assertion is what proves it."""
    frac = fit_frac(x, fit)
    lo = hyst((frac - lo_b + .5).clip(0, 1), band)
    hi = hyst((frac - hi_b + .5).clip(0, 1), band)
    return (lo.fillna(0) + hi.fillna(0)).where(frac.notna())


def classify_at(tr, ch, fit, q, dwell):
    """twoscores.classify with the cut quantile and the dwell exposed."""
    ft = np.where(fit[:, None], tr.values, np.nan)
    fc = np.where(fit[:, None], ch.values, np.nan)
    mt, mc = np.nanquantile(ft, q), np.nanquantile(fc, q)
    hi_t, hi_c = tr > mt, ch > mc
    lab = pd.DataFrame(np.select(
        [(hi_t & ~hi_c).values, (~hi_t & hi_c).values, (hi_t & hi_c).values],
        ['trending', 'ranging', 'trend-in-range'], 'neither'),
        index=tr.index, columns=tr.columns)
    return confirm(lab.where(tr.notna() & ch.notna()), dwell)


def build(px, fit, **over):
    c = dict(DEFAULTS); c.update(over)
    T, C = parts(px, c['N'], c['Wl'], c['kfail'], c['volwin'])
    C = dict(C)
    if c['drop_tests']:
        C.pop('tests', None)
    zt, zc = zfit(T, fit), zfit(C, fit)
    wt, wc = wmap(T, c['weights']), wmap(C, c['weights'])
    tr = sum(wt[k] * zt[k] for k in T)
    ch = sum(wc[k] * zc[k] for k in C)
    scale = raw_axes(px, L=c['actL'])['scale']
    a = tercile_at(scale, fit, c['act_lo'], c['act_hi'], c['band']).replace(
        {0.0: 'weak', 1.0: 'medium', 2.0: 'strong'})
    a = a.where(a.isin(list(ACTW)))
    trb = tr - a.replace(ACTW).astype(float) * c['bump']
    return classify_at(trb, ch, fit, c['score_q'], c['dwell'])


def runlen_flip(lab):
    """Median state run in bars, and the daily share of pairs changing state."""
    runs = []
    for p in lab.columns:
        v = lab[p].dropna()
        if len(v) < 50:
            continue
        gid = (v != v.shift()).cumsum()
        runs += [len(g) for _, g in v.groupby(gid)]
    ch = (lab != lab.shift(1)) & lab.notna() & lab.shift(1).notna()
    n = lab.notna().sum(axis=1)
    flip = (ch.sum(axis=1) / n.replace(0, np.nan)).mean()
    return (float(np.median(runs)) if runs else np.nan, float(flip),
            int(len(runs)))


def sep_mean(lab, P, mask):
    d = sep_one_vs_rest(lab, P, mask, CELLS)
    v = np.array([abs(x) for x in d.values() if np.isfinite(x)])
    per = {}
    for s in CELLS:
        vs = [abs(d[(s, c)]) for c in PROPS if np.isfinite(d.get((s, c), np.nan))]
        per[s] = float(np.mean(vs)) if vs else np.nan
    return (float(v.mean()) if len(v) else np.nan), per


def compare(A, B, idx):
    ok = A.notna() & B.notna()
    eq = (A == B) & ok
    agree = float(eq.sum().sum() / ok.sum().sum())
    pa = A.where(ok).stack().value_counts(normalize=True)
    pb = B.where(ok).stack().value_counts(normalize=True)
    exp = float(sum(pa.get(s, 0) * pb.get(s, 0) for s in CELLS))
    dis = (~eq) & ok
    allr = np.concatenate([runs_of(dis[p].values) for p in A.columns])
    tot = full = 0
    for p in A.columns:
        v = B[p].dropna()
        gid = (v != v.shift()).cumsum()
        for _, g in v.groupby(gid):
            if len(g) < 5:
                continue
            q = A[p].reindex(g.index)
            d = (q != g) & q.notna()
            tot += 1
            if d.sum() == len(g):
                full += 1
    per = {}
    for s in CELLS:
        sel = (B == s) & ok
        n = int(sel.sum().sum())
        per[s] = float((eq & sel).sum().sum() / n) if n >= 50 else np.nan
    return dict(agreement=agree, expected=exp,
                kappa=(agree - exp) / (1 - exp),
                median_dis_run=float(np.median(allr)) if len(allr) else np.nan,
                share_fully_relabelled=full / tot if tot else np.nan), per


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    ship = pd.read_csv(SHIPPED, index_col=0, parse_dates=True, comment='#')
    fit = np.asarray(px.index < SPLIT)
    P = properties(px)
    print('KNOB SENSITIVITY -- every hand-picked constant, one at a time.')
    print('  MEASURES ONLY. Nothing is re-tuned; the shipped settings stand.')

    base = build(px, fit)
    idx = ship.index.intersection(base.index)
    B = ship.reindex(idx)
    A0 = base.reindex(idx)[ship.columns]
    ok0 = A0.notna() & B.notna()
    same = float(((A0 == B) & ok0).sum().sum() / ok0.sum().sum())
    print('\nCONTROL -- the unperturbed configuration')
    print('  agreement with shipped %.4f over %d labelled pair-bars'
          % (same, int(ok0.sum().sum())))
    assert same > 0.9999, ('the unperturbed build does not reproduce the '
                           'shipped states (%.4f) -- the harness is wrong' % same)
    print('  PASS.')

    # properties are built on the price index; every comparison below runs on
    # the intersection with the shipped states file, so align the ruler to it.
    P = {k: v.reindex(idx) for k, v in P.items()}
    fitI = np.asarray(idx < SPLIT)
    mI = pd.Series(fitI, index=idx)
    mO = pd.Series(~fitI, index=idx)
    b_sep_is, _ = sep_mean(A0, P, mI)
    b_sep_oos, _ = sep_mean(A0, P, mO)
    b_run, b_flip, _ = runlen_flip(A0)
    print('  shipped: sep IS %.4f, OOS %.4f | median run %.0f bars, flip rate '
          '%.4f' % (b_sep_is, b_sep_oos, b_run, b_flip))

    rows, prows, srows = [], [], []
    rows.append(dict(knob='(control)', label='shipped, unperturbed',
                     shipped='', variant='none', agreement=1.0, kappa=1.0,
                     sep_is=b_sep_is, sep_oos=b_sep_oos,
                     sep_oos_vs_shipped=0.0, median_run=b_run,
                     flip_rate=b_flip, median_dis_run=np.nan,
                     share_fully_relabelled=0.0, run_failure=False,
                     rationale='n/a'))
    for key, label, shipped, variants, tier, why in KNOBS:
        for vlab, over in variants:
            L = build(px, fit, **over).reindex(idx)[ship.columns]
            agg, per = compare(L, B, idx)
            si, pis = sep_mean(L, P, mI)
            so, pos = sep_mean(L, P, mO)
            run, flip, nruns = runlen_flip(L)
            fail = bool(np.isfinite(run) and run <= b_run * RUN_DROP)
            rows.append(dict(knob=key, label=label, shipped=shipped,
                             variant=vlab, agreement=agg['agreement'],
                             kappa=agg['kappa'], sep_is=si, sep_oos=so,
                             sep_oos_vs_shipped=so - b_sep_oos,
                             median_run=run, flip_rate=flip,
                             median_dis_run=agg['median_dis_run'],
                             share_fully_relabelled=agg['share_fully_relabelled'],
                             run_failure=fail, rationale_tier=tier,
                             rationale=why))
            for s in CELLS:
                prows.append(dict(knob=key, variant=vlab, state=s,
                                  agreement=per[s]))
                srows.append(dict(knob=key, variant=vlab, state=s,
                                  sep_is=pis[s], sep_oos=pos[s]))
            print('  %-10s %-14s agree %.4f | sep OOS %.4f (%+.4f) | run %3.0f '
                  '| flip %.4f%s'
                  % (key, vlab, agg['agreement'], so, so - b_sep_oos, run, flip,
                     '  RUN FAILURE' if fail else ''))

    R = pd.DataFrame(rows)
    R['sensitivity'] = 1 - R.agreement
    R.to_csv(os.path.join(ROOTOUT, 'knob_sensitivity.csv'), index=False)
    pd.DataFrame(prows).to_csv(os.path.join(ROOTOUT, 'knob_perstate.csv'),
                               index=False)
    pd.DataFrame(srows).to_csv(os.path.join(ROOTOUT, 'knob_separation.csv'),
                               index=False)

    rk = R[R.knob != '(control)'].groupby(['knob', 'label']).agg(
        worst_agreement=('agreement', 'min'),
        mean_agreement=('agreement', 'mean'),
        worst_sep_oos=('sep_oos', 'min'),
        min_run=('median_run', 'min'),
        max_flip=('flip_rate', 'max'),
        any_run_failure=('run_failure', 'any'),
        rationale_tier=('rationale_tier', 'first'),
        rationale=('rationale', 'first')).reset_index()
    rk['sensitivity'] = 1 - rk.worst_agreement
    rk = rk.sort_values('sensitivity', ascending=False)
    rk['FLAG'] = np.where(
        (rk.sensitivity >= 0.10) & (rk.rationale_tier == 'NONE'), 'RED',
        np.where((rk.sensitivity >= 0.10) & (rk.rationale_tier == 'PARTIAL'),
                 'AMBER', ''))
    rk.to_csv(os.path.join(ROOTOUT, 'knob_ranking.csv'), index=False)

    print('\nSENSITIVITY RANKING -- worst agreement across that knob\'s variants')
    print('  %-10s %-28s %10s %9s %7s %8s %s'
          % ('knob', 'what it is', 'worst agr', 'sens', 'min run', 'max flip',
             'rationale'))
    for _, r in rk.iterrows():
        print('  %-10s %-28s %10.4f %9.3f %7.0f %8.4f %s'
              % (r.knob, r.label, r.worst_agreement, r.sensitivity, r.min_run,
                 r.max_flip, r.rationale_tier + (' <%s>' % r.FLAG if r.FLAG
                                                 else '')))
    flagged = rk[rk.FLAG != '']
    print('\nFLAGGED -- sensitivity >= 0.10 without a full rationale on file')
    print('  RED   = high sensitivity, NOTHING on file')
    print('  AMBER = high sensitivity, a construction rule but no comparison')
    if len(flagged):
        for _, r in flagged.iterrows():
            print('  %-6s %-10s %-28s sensitivity %.3f'
                  % (r.FLAG, r.knob, r.label, r.sensitivity))
    else:
        print('  none')
    rf = R[R.run_failure]
    print('\nPRACTICAL FAILURES -- median run <= %.0f bars, a %d%% drop from the'
          % (b_run * RUN_DROP, round(100 * (1 - RUN_DROP))))
    print('  shipped %.0f, at the daily cadence:' % b_run)
    if len(rf):
        for _, r in rf.iterrows():
            print('  %-10s %-14s run %.0f bars, sep OOS %.4f (%+.4f vs shipped)'
                  % (r.knob, r.variant, r.median_run, r.sep_oos,
                     r.sep_oos_vs_shipped))
    else:
        print('  none')

    fl = ', '.join('%s (%s)' % (r.knob, r.FLAG) for _, r in flagged.iterrows()) \
        if len(flagged) else 'none'
    hdr(os.path.join(ROOTOUT, 'knob_sensitivity.csv'),
        'Knob sensitivity -- every hand-picked constant, one at a time',
        'THIS MEASURES. IT CHANGES NOTHING AND PICKS NOTHING. The shipped\n'
        'classifier is untouched, no setting is proposed, and no knob is\n'
        'compared in order to select a better value. A knob that scores badly\n'
        'here becomes a candidate for a properly motivated follow-up -- chosen\n'
        'on IS against a declared criterion, confirmed once out of sample -- in\n'
        'a LATER run.\n\n'
        'CONTROL: the unperturbed configuration reproduces the shipped states\n'
        'at 1.0000, asserted, the same standard refit.py and windowsens.py use.\n\n'
        'THE DAILY-CADENCE LENS. Agreement and separation are not sufficient. A\n'
        'setting can hold separation and still be a practical failure by cutting\n'
        'state runs to a few bars -- there is nothing to trade in a regime call\n'
        'that changes twice a week. Any variant whose median run falls %d%% or\n'
        'more below the SHIPPED median is flagged run_failure -- relative, not\n'
        'absolute, because the shipped classifier itself sits at 19 bars and an\n'
        'absolute floor of 20 would flag the control. That is the same tradeoff\n'
        'as the one that picked the\n'
        'window (16.4q chose 106 bars for 21-bar episodes over the last 5%% of\n'
        'separation).\n\n'
        'Separation is measured with a FIXED RULER: structval.properties uses\n'
        'its own window and is not perturbed by anything here. If the ruler\n'
        'moved with the machine, every machine would look equally good.\n\n'
        'FLAGGED: %s\n' % (round(100 * (1 - RUN_DROP)), fl))
    hdr(os.path.join(ROOTOUT, 'knob_ranking.csv'),
        'The ranking, and which constants are steering without a reason on file',
        'sensitivity = 1 - the worst agreement across that knob\'s variants, so\n'
        'higher means the state calls move more when the constant is nudged by\n'
        '20-25%%.\n\n'
        'FLAG has two tiers, both requiring sensitivity >= 0.10:\n'
        '  RED   nothing on file at all -- an arbitrary constant steering the\n'
        '        machine\n'
        '  AMBER a construction rule is on file (equal thirds, the median) but\n'
        '        no comparison against alternatives\n\n'
        'Rationale was searched for in code comments and HANDOFF_3.md. Each\n'
        'flagged knob is a candidate for a motivated follow-up -- chosen on IS\n'
        'against a declared criterion, confirmed once out of sample -- NOT a\n'
        'change made here.')
    hdr(os.path.join(ROOTOUT, 'knob_perstate.csv'),
        'Per-state agreement for every knob perturbation',
        'Agreement with the shipped label, computed within each shipped state.\n'
        'The residual cell (neither) and the overlap cell (trend-in-range) have\n'
        'been the fragile pair in both the refit and window tests; this is where\n'
        'that shows up per knob.')
    hdr(os.path.join(ROOTOUT, 'knob_separation.csv'),
        'Per-state separation for every knob perturbation',
        'Mean |one-vs-rest separation| over the four structural properties, in\n'
        'sd units, in-sample and out-of-sample. This answers whether a perturbed\n'
        'machine is a WORSE machine or merely a DIFFERENT one: a variant that\n'
        'disagrees heavily with shipped but holds separation is different, not\n'
        'worse.')
    print('\nwrote knob_sensitivity.csv, knob_ranking.csv, knob_perstate.csv,')
    print('      knob_separation.csv + .txt')
    return R, rk


if __name__ == '__main__':
    main()
