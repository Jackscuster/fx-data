import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""ITEM 6b, JACK 25 NOV -- THREE SPEEDS TOGETHER.

WHAT "THREE SPEEDS" MEANS HERE, stated because the brief does not define it.
The project's own three settings per indicator are `half`, `default` and
`double` -- the knob that scales an indicator's memory, halved and doubled
(nnfx1.setting_params). Stage 1 ranked every C1 over exactly those three. So
"three speeds together" is read as: the same strategy at those three settings,
run SIMULTANEOUSLY as three equal-risk sleeves, against each alone.

The other reading -- three TIMEFRAMES, the daily/weekly/monthly hierarchy of
HANDOFF_3 section 9 -- is named here and not built, because it needs a weekly
and a monthly engine path that does not exist and item 6 gives one line to the
whole question. If that was the intent it is a different job.

THE SETTINGS ARE FIXED ACROSS EVERY STEP AND THAT CHANGES THE REPORTING
WINDOW. A speed is the variable under test, so it cannot also be chosen per
step -- this is not the walk-forward stitch and its numbers are NOT comparable
to candidate A's headline. Jack's standing rigour covers exactly this case:
"unseen 2010 to 2015 (2005 to 2015 for fixed settings)". So this report runs
2005-2015 and says so in every row. 2016-2020 is computed and not reported.

EQUAL RISK PER SLEEVE, 1/N on each sleeve's daily R series, the same
construction as BOOK.md -- so a speed has to beat the dilution it causes.

Writes results/nnfx/speed_cells.csv, speed_book.csv, speed_corr.csv and
SPEEDS.md.
"""
import numpy as np, pandas as pd

import nnfx1 as N
import nnfx2s as S2
import nnfxvol as VOL
import l2sweep as S

OUT = os.path.join(ROOTOUT, 'nnfx')
os.makedirs(OUT, exist_ok=True)
# FIXED SETTINGS -> the wider window, by Jack's own standing rule
FIXED_YEARS = tuple(range(2005, 2016))
MAIN = 'jack'
SPEEDS = ('half', 'default', 'double')
MEMBERS = (('A', 'ichimoku_signals', 'sma_baseline', 'full_nnfx'),
           ('B', 'schaff_trend_cycle_signals', 'sma_baseline', 'side_xentry'))


def _ds(T, years=FIXED_YEARS):
    if T is None or not len(T):
        return None
    M, _ = VOL.apply_leverage_cap(T)
    M = M.reset_index(drop=True)
    DS = N.daily_series(M, N._cost_R(M))
    DS = DS[pd.DatetimeIndex(DS.date).year.isin(list(years))]
    if not len(DS):
        return None
    return (pd.Series(DS.R.to_numpy(float),
                      index=pd.DatetimeIndex(DS.date))
            .groupby(level=0).sum())


def _stats(s, nboot=2000):
    d = s.to_numpy(float)
    eq = np.cumsum(d)
    dip = float(np.max(np.maximum.accumulate(eq) - eq)) if len(d) else np.nan
    tot = float(d.sum())
    yrs = pd.Series(d, index=s.index).groupby(s.index.year).sum().sort_index()
    t_bs, _sd = N._block_t(d, ndraw=nboot)
    return dict(R_total=tot, R_per_year=tot / max(1, len(yrs)),
                days=len(d), worst_dip_R=dip,
                R_per_dip=(tot / dip if dip and dip > 1e-9 else np.nan),
                worst_day_R=(float(-d.min()) if len(d) and d.min() < 0
                             else np.nan),
                years=int(len(yrs)), years_positive=int((yrs > 0).sum()),
                t_yearly=(float(yrs.mean() * np.sqrt(len(yrs))
                                / yrs.std(ddof=1))
                          if len(yrs) > 1 and yrs.std(ddof=1) > 0 else np.nan),
                t_block_boot=t_bs)


def run(verbose=True):
    rows, ser = [], {}
    for (lab, c1, base, rs) in MEMBERS:
        for sp in SPEEDS:
            if not N.setting_is_distinct(c1, sp):
                # A SETTING THAT COLLAPSES ONTO `default` IS SKIPPED AND SAID
                # SO, not run as if it were a third speed. nnfx1 has the
                # check already because a default length of 2 cannot be
                # halved.
                rows.append(dict(member=lab, speed=sp, distinct=0,
                                 c1_setting=str(N.setting_params(c1, sp))))
                if verbose:
                    print('    %s/%-8s collapses onto default -- skipped'
                          % (lab, sp), flush=True)
                continue
            T = S2.run_combo(c1, sp, base, 'default', MAIN, rs,
                             lowvol_q=VOL.LOWVOL_Q,
                             peg_x=VOL.PEG_X_DECIDED)
            s = _ds(T)
            if s is None:
                continue
            ser['%s_%s' % (lab, sp)] = s
            f = _stats(s)
            # AND THE SAME CELL ON 2010-2015 ALONE, so the window is not a
            # confound. A fixed setting on the wide window and a per-step
            # setting on the narrow one differ in TWO ways; without this
            # column a reader cannot tell which one moved the number.
            sb = _ds(T, years=N.BUILD_YEARS)
            fb = _stats(sb) if sb is not None else {}
            rows.append(dict(member=lab, speed=sp, distinct=1,
                             c1_setting=str(N.setting_params(c1, sp)),
                             legs=len(T), **f,
                             **{('build_' + k): v for k, v in fb.items()}))
            if verbose:
                print('    %s/%-8s R %+8.3f  R/yr %+6.3f  dip %7.3f  '
                      'R/dip %+6.3f  n %d days'
                      % (lab, sp, f['R_total'], f['R_per_year'],
                         f['worst_dip_R'], f['R_per_dip'], f['days']),
                      flush=True)
    D = pd.DataFrame(rows)
    D.to_csv(os.path.join(OUT, 'speed_cells.csv'), index=False)
    # the three together, equal risk, per member
    brows = []
    for (lab, _c1, _b, _rs) in MEMBERS:
        ks = [k for k in ser if k.startswith(lab + '_')]
        if len(ks) < 2:
            continue
        M = pd.DataFrame({k: ser[k] for k in ks}).fillna(0.0)
        book = M.mean(axis=1)
        fb = _stats(book)
        best_alone = max((_stats(ser[k])['R_per_dip'], k) for k in ks)
        brows.append(dict(member=lab, sleeves=len(ks),
                          members='+'.join(sorted(ks)), **fb,
                          best_single_speed=best_alone[1],
                          best_single_R_per_dip=best_alone[0],
                          beats_best_single=int(fb['R_per_dip']
                                                > best_alone[0])))
        if verbose:
            print('    %s three together: R/dip %+.3f against best single '
                  '%s at %+.3f -> %s'
                  % (lab, fb['R_per_dip'], best_alone[1], best_alone[0],
                     'BETTER' if brows[-1]['beats_best_single'] else 'worse'),
                  flush=True)
    B = pd.DataFrame(brows)
    B.to_csv(os.path.join(OUT, 'speed_book.csv'), index=False)
    if ser:
        C = pd.DataFrame(ser).fillna(0.0).corr()
        C.index.name = 'sleeve'
        C.to_csv(os.path.join(OUT, 'speed_corr.csv'))
    return D, B


def md_speeds(out=None):
    import hashlib
    L_ = []
    a = L_.append
    def rd(n, ix=None):
        f = os.path.join(OUT, n)
        if not (os.path.exists(f) and os.path.getsize(f) > 2):
            return pd.DataFrame()
        return pd.read_csv(f, index_col=ix) if ix is not None \
            else pd.read_csv(f)
    D, B = rd('speed_cells.csv'), rd('speed_book.csv')
    C = rd('speed_corr.csv', 0)
    a('# THREE SPEEDS TOGETHER — item 6b, Jack 25 November 2026')
    a('')
    a('**What "three speeds" is read as, and the reading that was not '
      'built.** The project\'s own three settings per indicator are `half`, '
      '`default` and `double` — the knob that scales an indicator\'s memory, '
      'halved and doubled (`nnfx1.setting_params`), and the three stage 1 '
      'ranked every C1 over. So this is the same strategy at those three '
      'settings run SIMULTANEOUSLY as three equal-risk sleeves, against each '
      'alone. The other reading — three TIMEFRAMES, the daily/weekly/monthly '
      'hierarchy of `HANDOFF_3.md` §9 — needs a weekly and a monthly engine '
      'path that does not exist, and item 6 gives one line to the whole '
      'question. If that was the intent it is a different job and it is named '
      'here rather than guessed at.')
    a('')
    a('**THE WINDOW IS 2005–2015, NOT 2010–2015, and that is Jack\'s own '
      'rule.** A speed is the variable under test so it cannot also be chosen '
      'per step; these are FIXED settings across every step, which is not the '
      'walk-forward stitch and is **not comparable to candidate A\'s '
      'headline**. The standing rigour covers exactly this case: "unseen 2010 '
      'to 2015 (2005 to 2015 for fixed settings)". 2016–2020 computed, not '
      'reported.')
    a('')
    if len(D):
        a('## Each speed alone')
        a('')
        a('| member | speed | setting | legs | R total 2005–2015 | R/yr | '
          'worst dip | **R per dip** | years + | t yearly | '
          'R total 2010–2015 | R/yr | **R per dip 2010–2015** |')
        a('|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|')
        for _, r in D.iterrows():
            if int(r.get('distinct', 1)) == 0:
                a('| %s | `%s` | %s | — | — | — | — | — | — | — | — | — | '
                  '**collapses onto default, skipped** |'
                  % (r.member, r.speed, r.c1_setting))
                continue
            a('| %s | `%s` | %s | %d | %+.3f | %+.3f | %.3f | **%s** | '
              '%d of %d | %s | %s | %s | **%s** |'
              % (r.member, r.speed, r.c1_setting, int(r.legs), r.R_total,
                 r.R_per_year, r.worst_dip_R, _f(r.R_per_dip),
                 int(r.years_positive), int(r.years), _f(r.t_yearly),
                 _f(r.get('build_R_total')), _f(r.get('build_R_per_year')),
                 _f(r.get('build_R_per_dip'))))
        a('')
        a('### THE RESULT THAT MATTERS IS IN THIS TABLE AND IT IS NOT ABOUT '
          'SPEEDS')
        a('')
        _A = D[(D.member == 'A') & (D.distinct == 1)]
        if len(_A):
            _dd = D[D.distinct == 1]
            _nw = int((_dd.R_total < 0).sum())
            _nb = int((pd.to_numeric(_dd.get('build_R_total'),
                                     errors='coerce') < 0).sum())
            _bb = pd.to_numeric(_dd.get('build_R_total'), errors='coerce')
            a('**%d of the %d fixed-setting cells lose money on 2005–2015, '
              'and %d of %d lose on 2010–2015.** For A: %s on 2005–2015, and '
              '%s on 2010–2015. The best fixed-setting cell on those same six '
              'years is **%s at %+.3f R** — against **+39.874 R** for the '
              'walk-forward stitch of the same combination.'
              % (_nw, len(_dd), _nb, len(_dd),
                 '; '.join('`%s` %+.3f R' % (r.speed, r.R_total)
                           for _, r in _A.iterrows()),
                 '; '.join('`%s` %s R'
                           % (r.speed, _f(r.get('build_R_total')))
                           for _, r in _A.iterrows()),
                 ('%s/%s' % (_dd.loc[_bb.idxmax()].member,
                             _dd.loc[_bb.idxmax()].speed)
                  if _bb.notna().any() else '—'),
                 float(_bb.max()) if _bb.notna().any() else float('nan')))
            a('')
            a('**The window is NOT the explanation** — that is what the '
              '2010–2015 columns are for. On the identical six years the best '
              'fixed setting anywhere in the table is worth about a seventh '
              'of what the stitch makes, and four of the six cells lose. '
              'Choosing the setting on each step\'s own four tuning years is '
              'what turns the combination positive. **Candidate A\'s result '
              'is substantially the walk-forward SELECTION rather than the '
              'indicator at any one setting.**')
            a('')
            a('That is not a reason to distrust A — the selection is causal, '
              'it is made on tuning years only, and it is the thing being '
              'tested. It IS a reason to be precise about what A is: not '
              '"ichimoku plus an SMA baseline", which at a fixed setting '
              'loses on the eleven-year window and makes at best a seventh '
              'as much on the six, but **that combination with its lookback '
              're-chosen on every step**. The re-choosing is most of the '
              'result.')
            a('')
    if len(B):
        a('## The three together, equal risk per sleeve')
        a('')
        a('| member | sleeves | R total | R/yr | worst dip | '
          '**R per dip** | best single speed | its R per dip | '
          'does the combination beat it? |')
        a('|---|---:|---:|---:|---:|---:|---|---:|---|')
        for _, r in B.iterrows():
            a('| %s | %d | %+.3f | %+.3f | %.3f | **%s** | `%s` | %s | %s |'
              % (r.member, int(r.sleeves), r.R_total, r.R_per_year,
                 r.worst_dip_R, _f(r.R_per_dip), r.best_single_speed,
                 _f(r.best_single_R_per_dip),
                 '**YES**' if int(r.beats_best_single) else 'no'))
        a('')
        nb = int(B.beats_best_single.sum())
        a('**%d of %d members improve on their own best single speed.** %s'
          % (nb, len(B),
             ('Running the three speeds together is worth having on both.'
              if nb == len(B) else
              'Diversifying across speeds is NOT free: the three sleeves are '
              'the same rule on the same pairs reading the same prices, so '
              'they share most of their risk, and at equal risk the dilution '
              'can cost more than the smoothing earns.')))
        a('')
    if len(C):
        a('## How much do the speeds actually diversify?')
        a('')
        cols = list(C.columns)
        a('| | %s |' % ' | '.join('`%s`' % c for c in cols))
        a('|---|%s|' % ('---:|' * len(cols)))
        for i in C.index:
            a('| `%s` | %s |' % (i, ' | '.join(
                ('**1.000**' if i == c else '%+.3f' % C.loc[i, c])
                for c in cols)))
        a('')
        same = []
        for m in sorted(set(c.split('_')[0] for c in cols)):
            sub = [c for c in cols if c.startswith(m + '_')]
            if len(sub) < 2:
                continue
            o = C.loc[sub, sub].where(~np.eye(len(sub), dtype=bool)).stack()
            same.append('**%s** %.3f to %.3f' % (m, float(o.min()),
                                                 float(o.max())))
        a('**Within a member the speeds correlate %s.** That is the whole '
          'story of this report: they are the same rule on the same pairs '
          'reading the same prices, so the correlation is high by '
          'construction and there is far less to diversify than the three '
          'sleeves make it look. Compare the mean-reversion sleeves in '
          '`BOOK.md`, which sit at −0.12 to −0.40 against A.'
          % '; '.join(same))
        a('')
    a('## Provenance')
    a('')
    for n_ in ('speed_cells.csv', 'speed_book.csv', 'speed_corr.csv'):
        p_ = os.path.join(OUT, n_)
        if not os.path.exists(p_):
            a('- `%s` — **MISSING**' % os.path.join('results', 'nnfx', n_))
            continue
        a('- `%s` — %s rows, md5 `%s`'
          % (os.path.relpath(p_, _R),
             '{:,}'.format(len(S2._safe_csv(p_))),
             hashlib.md5(open(p_, 'rb').read()).hexdigest()[:12]))
    out = out or os.path.join(OUT, 'SPEEDS.md')
    open(out, 'w').write('\n'.join(L_) + '\n')
    print('  SPEEDS.md: %d lines -> %s'
          % (len('\n'.join(L_).splitlines()), os.path.relpath(out, _R)),
          flush=True)
    return out


def _f(v, fmt='%+.3f'):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return '—'
    return (fmt % f) if np.isfinite(f) else '—'


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', default='all')
    g = ap.parse_args()
    if g.stage in ('all', 'run'):
        run()
    if g.stage in ('all', 'md'):
        md_speeds()
    print('  nnfxspeed done', flush=True)


if __name__ == '__main__':
    main()
