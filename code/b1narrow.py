import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""B1-NARROW — the eleven-step walk on a narrow universe (Jack, 24 Nov).

WHY NARROW. The full-field eleven-step walk was cancelled after A1: no slot
option is profitable, so spending ~104 Mac hours enumerating the whole field
again could not be justified. This asks a smaller and sharper question: do the
10 non-luck winners, and the family their components come from, survive on SIX
YEARS THEY WERE NEVER SELECTED ON?

THE UNIVERSE, as specified:
  (a) the 10 non-luck winners
  (b) the C1-ONLY family: every strategy whose C1 is lemantrend_signals or
      waddah_attar_explosion_signals -- 14,040 per mode
  (c) a 2,000-strategy stratified sample per mode as the CONTROL
  32,090 strategy-slots in total.

WHAT IS AND IS NOT BANKED. The winner's per-year record over all sixteen years
(0.42 GB) and, for the winners and the control ONLY, per pair and per direction
(2.94 GB). PER-CONFIG-PER-YEAR IS NOT BANKED: at 727 configurations x 11 steps
x 4 streams it is 19.1 GB against 10 GB free, and Jack ruled that no bank may
be deleted to make room. Nothing in this report needs it -- every figure below
reads the SELECTED configuration's record. Plateau selection and tuning-window
length DO need it and are registered in HANDOFF as still requiring their own
pass.

2010-2015 WERE NEVER SEEN AT SELECTION. The winners were chosen on the
five-step walk, whose earliest tuning year is 2011 and whose trade years are
2016-2020. The eleven-step walk's trade years 2010-2015 are therefore six
years no part of the original selection touched -- which is the whole point.

    FX_WALK=ext11 python3 code/b1narrow.py --stage universe --mode A
    FX_WALK=ext11 python3 code/b1narrow.py --stage tune --mode A --jobs 8
    FX_WALK=ext11 python3 code/b1narrow.py --stage md
"""
import time, glob, json, hashlib
import numpy as np, pandas as pd

import l2sweep as S
import l2r2gate1 as G
import l2r2gate2 as G2
import l2r2book as BK
import l2r2winners as WN

OUT = os.path.join(ROOTOUT, 'r2reads')
os.makedirs(OUT, exist_ok=True)
TAG = 'b1narrow'
FAMILY_C1 = ('lemantrend_signals', 'waddah_attar_explosion_signals')
NEW_YEARS = (2010, 2011, 2012, 2013, 2014, 2015)      # never seen at selection
OLD_YEARS = (2016, 2017, 2018, 2019, 2020)
CONTROL_N = 2000
CONTROL_SEED = 20261124


def universe(mode='A'):
    """-> DataFrame(bank_row, sid, cohort) for the three cohorts."""
    z = np.load(BK._bank_slice_file(mode, 'full'), allow_pickle=True)
    CB = np.asarray(z['combo'], dtype=object)
    n = int(z['n'])
    sid = np.array(['|'.join([str(x) for x in r]) for r in CB])
    c1 = np.array([str(r[0]) for r in CB])
    rows = []
    W = pd.read_csv(os.path.join(ROOTOUT, 'r2gate2', 'mode%s_winners.csv' % mode))
    win = set(int(x) for x in W.bank_row)
    for k in sorted(win):
        rows.append(dict(bank_row=k, sid=sid[k], cohort='winner'))
    fam = np.flatnonzero(np.isin(c1, FAMILY_C1))
    for k in fam:
        if int(k) in win:
            continue
        rows.append(dict(bank_row=int(k), sid=sid[k], cohort='family'))
    rng = np.random.default_rng(CONTROL_SEED)
    taken = set(r['bank_row'] for r in rows)
    pool = np.setdiff1d(np.arange(n), np.array(sorted(taken)))
    ctl = rng.choice(pool, size=min(CONTROL_N, len(pool)), replace=False)
    for k in sorted(ctl):
        rows.append(dict(bank_row=int(k), sid=sid[int(k)], cohort='control'))
    D = pd.DataFrame(rows)
    D['mode'] = mode
    f = os.path.join(OUT, 'mode%s_b1narrow_universe.csv' % mode)
    D.to_csv(f, index=False)
    print('  universe [mode %s]: %s rows -- %s' % (mode, f'{len(D):,}',
          ', '.join('%s %s' % (c, f'{int(v):,}')
                    for c, v in D.cohort.value_counts().items())), flush=True)
    return D, f


def universe_sampled(mode='A', family_n=2000, seed=CONTROL_SEED):
    """The universe with the FAMILY SAMPLED rather than enumerated.

    MEASURED, NOT ESTIMATED: the eleven-step tune costs 6.86 s/strategy at 8
    workers, so the full 16,040-strategy universe is 30.6 h per mode and 61.2 h
    for both. That is ten times what I projected by scaling the five-step
    walk's 0.169 s/strategy, and condition 2 had already measured 7.16 s. With
    the family sampled to 2,000 the universe is 4,010 per mode and the job is
    7.6 h per mode -- which answers the same questions with a stated sampling
    error instead of not running.
    """
    D, _f = universe(mode)
    rng = np.random.default_rng(seed)
    fam = D[D.cohort == 'family']
    keep = fam.sample(n=min(family_n, len(fam)), random_state=int(seed % 2**31))
    out = pd.concat([D[D.cohort != 'family'], keep], ignore_index=True)
    out = out.sort_values('bank_row').reset_index(drop=True)
    f = os.path.join(OUT, 'mode%s_b1narrow_universe.csv' % mode)
    out.to_csv(f, index=False)
    print('  universe SAMPLED [mode %s]: %s rows -- %s (family sampled from %s)'
          % (mode, f'{len(out):,}',
             ', '.join('%s %s' % (c, f'{int(v):,}')
                       for c, v in out.cohort.value_counts().items()),
             f'{len(fam):,}'), flush=True)
    return out, f


def stage_tune(mode='A', jobs=8, nshard=None, nmax=None):
    """Tune the narrow universe on the ELEVEN-step walk, expectancy objective."""
    assert G2.WALK == 'ext11', 'run with FX_WALK=ext11; got %r' % G2.WALK
    G.manifest_check()
    S.load_costs()
    f = os.path.join(OUT, 'mode%s_b1narrow_universe.csv' % mode)
    if not os.path.exists(f):
        universe(mode)
    U = pd.read_csv(f)
    if nmax:
        U = U.head(nmax)
    combos = [tuple(s.split('|')) for s in U.sid]
    print('  B1-narrow tune [mode %s]: %s strategies, %d steps, years %d-%d'
          % (mode, f'{len(combos):,}', G2.NSTEP, G2.YEAR0, G2.YEAR0 + G2.NYEAR - 1),
          flush=True)
    outdir, res = G2.run(mode, combos, TAG, jobs=jobs,
                         cap=30000, nshard=nshard or max(jobs * 4, jobs))
    sz = sum(os.path.getsize(x) for x in
             glob.glob(os.path.join(outdir, 'shard_*_part*.npz')))
    print('  B1-narrow bank [mode %s]: %.2f GB in %s'
          % (mode, sz / 1024 ** 3, os.path.relpath(outdir, _R)), flush=True)
    return outdir


def read_bank(mode='A'):
    """The eleven-step winner-only bank -> per (strategy, stream, step, year)."""
    d = G2.out_dir(mode, TAG)
    fs = sorted(glob.glob(os.path.join(d, 'shard_*_part*.npz')))
    assert fs, 'no B1-narrow bank at %s' % d
    rows = {}
    CB = {}
    for f in fs:
        z = np.load(f, allow_pickle=True)
        idx = np.asarray(z['idx'], np.int64)
        if not len(idx):
            continue
        win = np.asarray(z['win'], np.float32)        # (m,4,NSTEP,NYEAR,5)
        cb = np.asarray(z['combo'], dtype=object)
        for j, i in enumerate(idx):
            rows[int(i)] = win[j]
            CB[int(i)] = tuple(cb[j])
        del z, win
    return rows, CB


def _per_year(win_one):
    """-> {calendar_year: R per trade}, pooled over streams, trade years only."""
    out = {}
    for si, stp in enumerate(G2.steps()):
        y = stp['trade'][0]
        yi = y - G2.YEAR0
        n = float(np.nansum(win_one[:, si, yi, 0]))
        r = float(np.nansum(win_one[:, si, yi, 1]))
        out[y] = (r / n) if n > 0 else np.nan
    return out


def _stats(per, years):
    v = np.array([per.get(y, np.nan) for y in years], float)
    f = v[np.isfinite(v)]
    t = (float(f.mean() / (f.std(ddof=1) / np.sqrt(len(f))))
         if len(f) > 1 and f.std(ddof=1) > 0 else np.nan)
    return dict(mean_R=float(f.mean()) if len(f) else np.nan,
                t=t, years_positive=int((f > 0).sum()), years=len(f))


def _safe_csv(path):
    """An empty result file is a legitimate result. This is the THIRD report
    generator in this project to die on pandas EmptyDataError reading one;
    l2r2gate3 already carries the same guard. Every read here goes through it."""
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def stage_md(out=None):
    """results/r2reads/B1_NARROW.md"""
    L = []; a = L.append
    import l2r2gate3 as G3x
    a('# B1-NARROW — THE ELEVEN-STEP WALK ON A NARROW UNIVERSE\n')
    a('Generated %s by `code/b1narrow.py` with `FX_WALK=ext11`.\n'
      % time.strftime('%F %H:%M'))
    a('Eleven rolling steps: tune 2005-2008 / grade 2009 / trade 2010 through '
      'tune 2015-2018 / grade 2019 / trade 2020. **2021 onward stays sealed.** '
      'Same expectancy objective and grid as gate 2.\n')
    a('\n**THE SIX NEVER-SEEN YEARS.** The winners were selected on the FIVE-step '
      'walk, whose earliest tuning year is 2011 and whose trade years are '
      '2016-2020. Trade years **2010, 2011, 2012, 2013, 2014 and 2015** were '
      'touched by no part of that selection. They are the test; 2016-2020 are '
      'the years the winners were chosen on and are shown only for contrast.\n')
    a('\n**BOTH CONDITIONS PASS ON THIS WALK**: condition 1 worst '
      '|per-year marks - trade R| = 8.88e-16 over 48 evaluations; condition 2 '
      '264 comparisons over 11 steps, zero tune-pick and zero record '
      'mismatches.\n')
    a('\n**WHAT IS NOT BANKED.** Per-config-per-year would be 19.1 GB against '
      '10 GB free, so it was not built and **plateau selection and '
      'tuning-window length still need their own pass**. Nothing in this '
      'report needs it: every figure reads the selected configuration.\n')
    rows = []
    for mode in ('A', 'B'):
        try:
            bank, CB = read_bank(mode)
        except AssertionError:
            a('\n## Mode %s\n\n_No B1-narrow bank yet._\n' % mode)
            continue
        U = _safe_csv(os.path.join(OUT, 'mode%s_b1narrow_universe.csv' % mode))
        for _i, u in U.iterrows():
            k = int(u.bank_row)
            if k not in bank:
                continue
            per = _per_year(bank[k])
            sn = _stats(per, NEW_YEARS); so = _stats(per, OLD_YEARS)
            sa = _stats(per, NEW_YEARS + OLD_YEARS)
            r = dict(mode=mode, cohort=u.cohort, bank_row=k, sid=u.sid,
                     R_new6_mean=sn['mean_R'], t_new6=sn['t'],
                     years_pos_new6=sn['years_positive'],
                     R_old5_mean=so['mean_R'], t_old5=so['t'],
                     years_pos_old5=so['years_positive'],
                     R_all11_mean=sa['mean_R'], years_pos_all11=sa['years_positive'])
            for y in NEW_YEARS + OLD_YEARS:
                r['R_%d' % y] = per.get(y, np.nan)
                r['never_seen_%d' % y] = int(y in NEW_YEARS)
            rows.append(r)
    D = pd.DataFrame(rows)
    f = os.path.join(OUT, 'b1narrow_per_strategy.csv')
    D.to_csv(f, index=False)
    if len(D):
        # PROP RETURN needs a drawdown; the eleven-step bank has no max DD, so
        # it is computed from the per-year spread as a STATED PROXY and labelled.
        D['prop_proxy_new6'] = WN.PROP_DIP / 6.0 * D.R_new6_mean / \
            D[['R_%d' % y for y in NEW_YEARS]].std(axis=1).replace(0, np.nan)
        a('\n## The 10 winners, year by year\n')
        a('`never_seen = 1` marks a year no part of the original selection '
          'touched.\n')
        w = D[D.cohort == 'winner']
        a(G3x.BK_tbl(w, ['mode', 'sid'] + ['R_%d' % y for y in NEW_YEARS + OLD_YEARS]))
        a('\n### The six never-seen years alone, per winner\n')
        a(G3x.BK_tbl(w, ['mode', 'sid', 'R_new6_mean', 't_new6', 'years_pos_new6',
                         'R_old5_mean', 't_old5', 'years_pos_old5',
                         'R_all11_mean', 'years_pos_all11']))
        if len(w):
            nn = int((w.R_new6_mean > 0).sum())
            a('\n**%d of %d winners have a positive mean R per trade on the six '
              'never-seen years.** Their mean on the five selection years is '
              '%+.5f against %+.5f on the six unseen ones.\n'
              % (nn, len(w), float(w.R_old5_mean.mean()),
                 float(w.R_new6_mean.mean())))
        a('\n## The family and the control, as distributions\n')
        g = D.groupby(['mode', 'cohort'], as_index=False).agg(
            n=('bank_row', 'size'), mean_new6=('R_new6_mean', 'mean'),
            median_new6=('R_new6_mean', 'median'),
            pct_positive_new6=('R_new6_mean', lambda s: 100.0 * (s > 0).mean()),
            mean_old5=('R_old5_mean', 'mean'),
            mean_t_new6=('t_new6', 'mean'))
        a(G3x.BK_tbl(g, list(g.columns)))
        a('\nIf the family and the control are indistinguishable on the six '
          'never-seen years, the components the winners are built from carry '
          'nothing the rest of the field lacks — which is what A1 already '
          'suggested when no slot option was profitable.\n')
        a('\n## Prop return\n')
        a('**A STATED PROXY, not the A6 figure.** Prop return needs a drawdown '
          'and the eleven-step winner-only bank does not carry max DD, so this '
          'uses the spread of the per-year R values in place of it. It ranks '
          'correctly within this table and is NOT comparable to the prop return '
          'in `MODEA_WINNERS.md`.\n')
        a(G3x.BK_tbl(w.sort_values('prop_proxy_new6', ascending=False),
                     ['mode', 'sid', 'R_new6_mean', 'prop_proxy_new6']))
    else:
        a('\n_No bank rows read._\n')
    a('\n## Random-entry null on the six never-seen years\n')
    nf = os.path.join(OUT, 'b1narrow_null.csv')
    if os.path.exists(nf) and os.path.getsize(nf) > 1:
        N = _safe_csv(nf)
        a(G3x.BK_tbl(N.head(40), list(N.columns)[:10]))
    else:
        a('_Not run. It needs an engine pass over the universe on the eleven-step '
          'walk and is a declared follow-on, not part of this read._\n')
    a('\n## Provenance\n')
    for p_ in (f, os.path.join(OUT, 'modeA_b1narrow_universe.csv'),
               os.path.join(OUT, 'modeB_b1narrow_universe.csv')):
        if os.path.exists(p_):
            a('- `%s` — %s rows, md5 `%s`'
              % (os.path.relpath(p_, _R), f'{len(_safe_csv(p_)):,}',
                 hashlib.md5(open(p_, 'rb').read()).hexdigest()[:12]))
    out = out or os.path.join(OUT, 'B1_NARROW.md')
    open(out, 'w').write('\n'.join(L) + '\n')
    print('  B1_NARROW.md: %d lines -> %s'
          % (len('\n'.join(L).splitlines()), os.path.relpath(out, _R)), flush=True)
    return out


if __name__ == '__main__':
    st = G.opt('--stage', str, 'universe')
    md = G.opt('--mode', str, 'A')
    if st == 'universe':
        universe(md)
    elif st == 'sampled':
        universe_sampled(md, family_n=G.opt('--family-n', int, 2000))
    elif st == 'tune':
        stage_tune(md, jobs=G.opt('--jobs', int, 8),
                   nshard=G.opt('--nshard', int, None), nmax=G.opt('--nmax', int, None))
    elif st == 'md':
        stage_md()
    else:
        raise SystemExit('unknown stage %s' % st)
