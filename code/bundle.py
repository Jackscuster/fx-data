import os, sys, json, subprocess
import pandas as pd, numpy as np
_R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTOUT = os.path.join(_R, 'results')
os.makedirs(ROOTOUT, exist_ok=True)
R = ROOTOUT + os.sep


def rd(f, **k):
    try:
        return pd.read_csv(R + f, **k)
    except Exception:
        return pd.DataFrame()


def cl(d):
    return json.loads(d.replace({np.nan: None}).to_json(orient='records'))


sig = json.load(open(R + 'signals.json'))
fun = rd('dsr_funnel.csv')


def fun_val(stage_or_col, default):
    """Read the DSR headline from funnel.py rather than hardcoding it here."""
    if fun.empty:
        return default
    if stage_or_col == 'emax':
        return round(float(fun.emax.iloc[0]), 3) if 'emax' in fun else default
    hit = fun[fun.stage == stage_or_col]
    return int(hit['count'].iloc[0]) if len(hit) else default


def signals_url():
    """Absolute raw URL for app_signals.json, derived from the git remote.

    The shell hands renderApp the parsed app_data.json and nothing else, so it has
    no idea where the feed came from. app_ui.js therefore needs an absolute URL to
    fetch the signals half from."""
    try:
        u = subprocess.run(['git', '-C', _R, 'remote', 'get-url', 'origin'],
                           capture_output=True, text=True, check=True).stdout.strip()
        u = u.replace('git@github.com:', '').replace('https://github.com/', '')
        u = u[:-4] if u.endswith('.git') else u
        return 'https://raw.githubusercontent.com/%s/main/app_signals.json' % u
    except Exception:
        return 'app_signals.json'


# ---- SPLIT. GitHub hard-rejects any file over 100 MB and the combined feed
# reached 96.7 MB. signals go in their own file; everything else stays here.
#
# Splitting alone was not enough -- the signals half was still 92 MB, 8 MB from
# the same wall. So the per-row schema shipped to the app is trimmed to the fields
# app_ui.js actually reads. results/signals.json keeps every field and stays the
# analysis artefact; this is a display feed, not the record.
n_built = len(sig)
n_scorable = sum(1 for d in sig if d.get('ok') is not False)
APP_KEYS = ['s', 'f', 'b', 'ok', 'ti', 'to', 'si', 'so', 'ai', 'ao', 'mo', 'n',
            'cto', 'cso', 'cao', 'stronger_target', 'tsb', 'dec', 'held', 'indep']


def lean(d):
    r = {k: d.get(k) for k in APP_KEYS}
    # the quintile sparkline is only ever drawn for gauntlet survivors
    if d.get('to') is not None and abs(d['to']) >= 8:
        r['qo'] = d.get('qo')
    return r


json.dump([lean(d) for d in sig], open(R + 'app_signals.json', 'w'),
          separators=(',', ':'))

# The 32 independents get their own full-fat rows -- every gate metric, all three
# horizons, cluster membership. 32 rows cost nothing and this is the actual
# output of the phase.
_surv = [d for d in sig if d.get('indep') is not None]
_ind = [d for d in sig if d.get('indep') is True]

out = dict(
    sweep=cl(rd('strategy_sweep.csv')),
    ladder=cl(rd('detector_ladder.csv')),
    logic=cl(rd('logic_summary.csv')),
    duration=cl(rd('duration_stats.csv')),
    funnel=cl(rd('dsr_funnel.csv')),
    audit=cl(rd('lookahead_audit.csv')),
    # REGIME-DETECTION metrics only in the estimator view. The strategy-metric
    # versions stay on disk as Phase 4 groundwork but are not shipped to the app.
    ninebox=cl(rd('ninebox_regime.csv')),
    ninebox_surv=cl(rd('ninebox_regime_surv.csv')),
    mtf=cl(rd('mtf_regime.csv')),
    mtfagree=cl(rd('mtf_agreement.csv')),
    mtfagree_surv=cl(rd('mtf_agreement_surv.csv')),
    composite=cl(rd('composite_stats.csv')),
    val_summary=cl(rd('validation_summary.csv')),
    val_shuffle=cl(rd('validation_shuffle.csv')),
    val_synth=cl(rd('validation_synthetic.csv')),
    val_refit=cl(rd('validation_refit.csv')),
    val_persist=cl(rd('validation_persistence.csv')),
    val_trans=cl(rd('validation_transitions.csv')),
    crisis=cl(rd('crisis_detectors.csv')),
    crisisev=cl(rd('crisis_events.csv')),
    famret=cl(rd('family_retention.csv')),
    pairtrend=cl(rd('pair_trend.csv')),
    horizon=cl(rd('horizon_summary.csv')),
    entry=cl(rd('entry_excursion.csv')),
    termstruct=cl(rd('termstruct_signals.csv')),
    scaleocc=cl(rd('scale_occupancy.csv')),
    durbands=cl(rd('duration_bands.csv')),
    clsval=cl(rd('classifier_validation.csv')),
    ribsweep=cl(rd('ribbon_sweep.csv')),
    ribexc=cl(rd('ribbon_excursion.csv')),
    durhaz=cl(rd('duration_hazard_hysteresis.csv')),
    scaleexc=cl(rd('scale_excursion.csv')),
    newtarget=cl(rd('newtarget_summary.csv')),
    termpairs=cl(rd('termstruct_pairs.csv')),
    entrypair=cl(rd('entry_by_pair.csv')),
    subnull=cl(rd('subset_null.csv')),
    subnullpairs=cl(rd('subset_null_pairs.csv')),
    agreepairs=cl(rd('agree_gate_pairs.csv')),
    extret=cl(rd('ext_retention.csv')),
    carryret=cl(rd('carry_retention.csv')),
    carrysig=cl(rd('carry_signals.csv')),
    ratecov=cl(rd('rates_coverage.csv')),
    extcov=cl(rd('ext_coverage.csv')),
    exttr=cl(rd('ext_transfer.csv')),
    infl=cl(rd('inflation_adjusted.csv')),
    inflsum=cl(rd('inflation_summary.csv')),
    inflfam=cl(rd('inflation_families.csv')),
    stability=cl(rd('stability.csv')),
    clusters=cl(rd('survivor_clusters.csv')),
    survivors=_surv,          # all 111 that clear gates 1-7
    independents=_ind,        # the 32 that also clear gate 8
    meta=dict(built=pd.Timestamp.now().strftime('%Y-%m-%d %H:%M'),
              pairs=28, split='2016-01-01',
              variants=int(len(rd('logic_results.csv'))),
              dsr_pass=fun_val('survive DSR >= 0.95', 0),
              emax=fun_val('emax', 1.076),
              signals_url=signals_url(),
              # two different numbers, never to be conflated: everything built,
              # and the subset that could actually produce quintile statistics
              n_built=n_built, n_scorable=n_scorable))
json.dump(out, open(R + 'app_data.json', 'w'), separators=(',', ':'))
print({k: (len(v) if isinstance(v, list) else 'meta') for k, v in out.items()})
print('app_data.json    %6.1f MB' % (os.path.getsize(R + 'app_data.json') / 1048576))
print('app_signals.json %6.1f MB  (%d built, %d scorable)'
      % (os.path.getsize(R + 'app_signals.json') / 1048576, n_built, n_scorable))
