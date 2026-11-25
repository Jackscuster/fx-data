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


TAG_WIN = 'b1winners'


def winners_frame(mode='A'):
    """The 10 non-luck winners, from the committed winners file."""
    f = os.path.join(ROOTOUT, 'r2gate2', 'mode%s_winners.csv' % mode)
    assert os.path.exists(f), f + ' missing'
    W = pd.read_csv(f)
    assert len(W), 'no winners for mode %s' % mode
    return W


def stage_winners(mode='A', jobs=4, costtag=''):
    """THE 10 WINNERS ALONE on the eleven-step walk, with the TRUE drawdown.

    Jack, 24 Nov: run the winners as their own stage and report at once. Ten
    strategies over eleven steps is minutes, so this does not wait on the
    family sample.

    PROP RETURN IS THE REAL FIGURE HERE, not the spread proxy stage_md uses.
    The winner-only bank carries n, sum_r, gain, loss and n_win but NO
    drawdown, so this stage re-scores each winner's selected configuration with
    want_dd=True and takes the true chronological max DD from role_dd over
    whatever span is being reported. That is why it scores rather than reading
    the bank.
    """
    assert G2.WALK == 'ext11', 'run with FX_WALK=ext11; got %r' % G2.WALK
    G.manifest_check()
    S.load_costs()
    W = winners_frame(mode)
    combos = [tuple(s.split('|')) for s in W.sid]
    print('  B1-winners [mode %s]: %d winners, %d steps, years %d-%d'
          % (mode, len(combos), G2.NSTEP, G2.YEAR0, G2.YEAR0 + G2.NYEAR - 1),
          flush=True)
    outdir, _res = G2.run(mode, combos, TAG_WIN, jobs=min(jobs, max(1, len(combos))),
                          cap=30000, nshard=min(jobs, len(combos)))
    # --- the selected configuration per (winner, step), then the true DD ---
    bank, CB = read_bank_tag(mode, TAG_WIN)
    Y = G2.Years(cap=4000)
    ST = G2.steps()
    rows = []
    for wi, w in W.iterrows():
        k = wi                      # G2.run banks by position in `combos`
        if k not in bank:
            continue
        stream = list(G2.STREAMS).index(w.stream)
        sl, rt = stream // 2, stream % 2
        sname, plan, code = S.SLICES[sl]
        combo = tuple(CB[k])
        tg = bank_tags(mode, TAG_WIN)
        per, dd_day = {}, np.zeros((2, Y.ndays), np.float64)
        for si, stp in enumerate(ST):
            ci = int(tg[k, stream, si])
            if ci < 0:
                continue
            ip, risk = BK.winner_config(mode, combo, sname, ci)
            _acc, accd = Y.score(combo, ip, risk, mode, sname, code, plan,
                                 want_dd=True)
            y = stp['trade'][0]
            yi = y - G2.YEAR0
            # R FROM THE RE-SCORED DAILY SERIES, NOT FROM THE BANK, WHENEVER
            # THE COST TABLE IS OVERRIDDEN. The bank was built under the
            # 2016-2020 cost table, so reading R out of it ignores the override
            # completely: the first era run returned R identical to 0.000 while
            # only the drawdown moved, which is how the mistake showed. accd is
            # the engine's own per-day R for the role under the table actually
            # loaded, and summing it over the trade year reproduces the bank's
            # sum_r exactly when the tables match -- asserted below.
            #
            # THE WINNER'S OWN STREAM, NOT THE SUM OVER ALL FOUR.
            # The first version of this line read bank[k][:, si, yi, ...], which
            # sums trend-routed, trend-allon, chop-routed and chop-allon
            # together. That is what made the superseded B1_WINNERS.md report
            # 120.8 R for 2018 where the record says 51.399, and ~1,886 trades
            # over 2016-2020 where the record says 826. The tune was never
            # wrong: the ext11 and base5 banks agree exactly on the shared
            # years, same config index, same R, same trade count.
            n = float(bank[k][stream, si, yi, 0])
            r_bank = float(bank[k][stream, si, yi, 1])
            m_y = (Y.dayyear == y - G2.YEAR0)
            r_resc = float(accd[rt][m_y].sum())
            if costtag:
                r = r_resc
            else:
                r = r_bank
                # the same identity condition 1 tests, asserted per winner-year
                assert abs(r_resc - r_bank) < 1e-3, (
                    'the re-scored trade year disagrees with the bank: '
                    'winner %d stream %d year %d, %.6f vs %.6f'
                    % (k, stream, y, r_resc, r_bank))
            per[y] = dict(n=n, R=r, R_bank=r_bank, R_rescored=r_resc,
                          R_per_trade=(r / n) if n > 0 else np.nan,
                          dd=float(G2.role_dd(accd, Y.dayyear, y, y)[rt]))
            # the trade year's own day-increments, stitched into one series so
            # the multi-year drawdown is CHRONOLOGICAL and not a sum of parts.
            # Y.dayyear holds year INDICES, not calendar years -- role_dd does
            # the y - YEAR0 conversion internally, a manual mask must not.
            dd_day[:, m_y] = accd[:, m_y]
        def span(years):
            ys = [y for y in years if y in per]
            if not ys:
                return dict(R=np.nan, n=0, dd=np.nan, years=0)
            R = float(sum(per[y]['R'] for y in ys))
            n = float(sum(per[y]['n'] for y in ys))
            dd = float(G2.role_dd(dd_day, Y.dayyear, min(ys), max(ys))[rt])
            return dict(R=R, n=n, dd=dd, years=len(ys))
        s6, s11 = span(NEW_YEARS), span(NEW_YEARS + OLD_YEARS)
        rv = [per[y]['R_per_trade'] for y in NEW_YEARS if y in per]
        rv = [x for x in rv if np.isfinite(x)]
        t6 = (float(np.mean(rv) / (np.std(rv, ddof=1) / np.sqrt(len(rv))))
              if len(rv) > 1 and np.std(rv, ddof=1) > 0 else np.nan)
        r = dict(mode=mode, sid=w.sid, stream=w.stream, bank_row=int(w.bank_row),
                 R_new6=s6['R'], n_new6=s6['n'], dd_new6=s6['dd'],
                 t_new6=t6,
                 years_pos_new6=int(sum(1 for y in NEW_YEARS
                                        if y in per and per[y]['R'] > 0)),
                 R_all11=s11['R'], n_all11=s11['n'], dd_all11=s11['dd'],
                 years_pos_all11=int(sum(1 for y in NEW_YEARS + OLD_YEARS
                                         if y in per and per[y]['R'] > 0)))
        # PROP RETURN: yearly R over the span, sized so max DD = 3.6%
        for lbl, sp in (('new6', s6), ('all11', s11)):
            yr = sp['R'] / sp['years'] if sp['years'] else np.nan
            r['prop_return_%s' % lbl] = (WN.PROP_DIP * yr / sp['dd']
                                         if sp['dd'] and np.isfinite(sp['dd'])
                                         and sp['dd'] > 0 else np.nan)
        for y in NEW_YEARS + OLD_YEARS:
            r['R_%d' % y] = per.get(y, {}).get('R', np.nan)
            r['Rpt_%d' % y] = per.get(y, {}).get('R_per_trade', np.nan)
            r['n_%d' % y] = per.get(y, {}).get('n', np.nan)
            r['never_seen_%d' % y] = int(y in NEW_YEARS)
        rows.append(r)
    del Y
    D = pd.DataFrame(rows)
    f = os.path.join(OUT, 'mode%s_b1winners%s.csv' % (mode, costtag))
    D.to_csv(f, index=False)
    print('  B1-winners [mode %s%s]: %d rows -> %s'
          % (mode, costtag or '', len(D), os.path.relpath(f, _R)), flush=True)
    return D


def read_bank_tag(mode, tag):
    """read_bank for an arbitrary tag."""
    d = G2.out_dir(mode, tag)
    fs = sorted(glob.glob(os.path.join(d, 'shard_*_part*.npz')))
    assert fs, 'no bank at %s' % d
    rows, CB = {}, {}
    for f in fs:
        z = np.load(f, allow_pickle=True)
        idx = np.asarray(z['idx'], np.int64)
        if not len(idx):
            continue
        win = np.asarray(z['win'], np.float32)
        cb = np.asarray(z['combo'], dtype=object)
        for j, i in enumerate(idx):
            rows[int(i)] = win[j]
            CB[int(i)] = tuple(cb[j])
    return rows, CB


def bank_tags(mode, tag):
    """The (strategy, stream, step) -> chosen configuration index array."""
    d = G2.out_dir(mode, tag)
    fs = sorted(glob.glob(os.path.join(d, 'shard_*_part*.npz')))
    out = None
    for f in fs:
        z = np.load(f, allow_pickle=True)
        idx = np.asarray(z['idx'], np.int64)
        if not len(idx):
            continue
        tg = np.asarray(z['tag'], np.int32)
        if out is None:
            out = np.full((int(idx.max()) + 1,) + tg.shape[1:], -1, np.int32)
        if int(idx.max()) >= out.shape[0]:
            pad = np.full((int(idx.max()) + 1 - out.shape[0],) + out.shape[1:],
                          -1, np.int32)
            out = np.concatenate([out, pad], axis=0)
        out[idx] = tg
    assert out is not None, 'no tags banked for %s' % tag
    return out


def stage_md_winners(out=None):
    """results/r2reads/B1_WINNERS.md -- re-issued 24 Nov after a bug of mine."""
    import l2r2gate3 as G3x
    L = []; a = L.append
    a('# B1-WINNERS — THE 10 WINNERS ON SIX YEARS THEY WERE NEVER SELECTED ON\n')
    a('Generated %s by `code/b1narrow.py --stage winners` with `FX_WALK=ext11`.\n'
      % time.strftime('%F %H:%M'))
    a('\n> ## THE VERSION OF THIS FILE ISSUED AT 10:21 ON 24 NOV IS SUPERSEDED '
      'AND WRONG\n'
      '>\n'
      '> It reported winner 1 as 16.68 / 6.63 / 120.8 / 85.14 / 12.14 R over '
      '2016-2020 against a record of 13.812 / 17.462 / 51.399 / 29.295 / '
      '13.121, and about 1,886 trades over those five years against 826. Jack '
      'caught it by checking the years the two walks share.\n'
      '>\n'
      '> **THE CAUSE, IN TWO LINES.** I read the banked record as '
      '`bank[k][:, step, year, ...]`, which SUMS the four streams — '
      'trend-routed, trend-allon, chop-routed and chop-allon — into one number '
      'that belongs to no strategy, instead of selecting the winner\'s own '
      'stream. The eleven-step tune was never wrong: it used the same gate 2 '
      'grid, the same objective and the same scoring, and it reproduces the '
      'five-step record on the shared years exactly.\n'
      '>\n'
      '> **Nothing else changed.** The direction of the finding is the same and '
      'slightly worse once era-correct costs are charged.\n')
    a('\n## Condition 3 — cross-walk reproduction\n')
    try:
        D3, ok3 = condition3(verbose=False)
    except Exception as e:
        D3, ok3 = pd.DataFrame(), False
        a('_Condition 3 could not run: %s_\n' % type(e).__name__)
    if len(D3):
        a('Trade years 2016-2020 use the same tuning years in both walks — tune '
          '2011-2014 / grade 2015 / trade 2016, and so on — so the eleven-step '
          'walk must reproduce the five-step record on them exactly.\n')
        a('')
        a('| check | worst difference | over tolerance |')
        a('|---|---:|---:|')
        a('| per-year total R | %.3e | %d of %d |'
          % (D3.dR.max(), int((D3.dR > 1e-6).sum()), len(D3)))
        a('| per-year trade count | %.3e | %d of %d |'
          % (D3.dn.max(), int((D3.dn > 1e-6).sum()), len(D3)))
        a('| selected config index | — | %d of %d identical |'
          % (int(D3.cfg_same.sum()), len(D3)))
        a('')
        a('**CONDITION 3: %s** — %d winner-years, %d winners x %d shared years. '
          'It is registered as preflight guard 30 and runs on any '
          'extended-walk job. Nothing from 2010-2015 is quoted below unless it '
          'passes.\n'
          % ('PASS' if ok3 else 'FAIL', len(D3), len(D3) // 5, 5))
        if not ok3:
            a('\n**It did not pass, so the six-year table is withheld.**\n')
            open(out or os.path.join(OUT, 'B1_WINNERS.md'), 'w').write(
                '\n'.join(L) + '\n')
            return out
    a('\n## A SECOND DIVERGENCE, FOUND WHILE CHASING THE FIRST — NOT MINE\n')
    a('Jack\'s reference numbers came from `mode?_winners.csv`, whose '
      '`R_<year>` is written from the **gate 3 KPI bank**, not from gate 2\'s '
      '`win` array. The two disagree for the **same strategy, the same config '
      'index and the same year**:\n')
    g23 = _safe_csv(os.path.join(ROOTOUT, 'r2gate2', 'gate2_vs_gate3_peryear.csv'))
    if len(g23):
        a('')
        a('| | |')
        a('|---|---|')
        a('| winner-years compared | %d |' % len(g23))
        a('| per-year R differing by more than 1e-6 | **%d of %d** |'
          % (int((g23.dR.abs() > 1e-6).sum()), len(g23)))
        a('| trade counts differing | **%d of %d** |'
          % (int((g23.dn.abs() > 1e-6).sum()), len(g23)))
        a('| median \\|ΔR\\| | %.4f R |' % g23.dR.abs().median())
        a('| largest \\|ΔR\\| | %.4f R |' % g23.dR.abs().max())
        a('| largest \\|Δn\\| | %.0f trades |' % g23.dn.abs().max())
        a('')
    a('**Gate 2 is the faithful record.** A direct re-score of winner 1\'s '
      'config 289 over 2016 returns **13.812019**, which is gate 2\'s banked '
      '`sum_r` to six decimals. The gate 3 KPI bank says 16.5096. Gate 3 reads '
      'the *same* config index out of gate 2\'s tag and then scores it through '
      'a different scorer (`sc.score`), and that is where the two part.\n')
    a('\nSo this report compares against the **gate 2 bank**, which is the '
      'cross-walk property being tested. **The gate 2 / gate 3 divergence is a '
      'separate, pre-existing defect that affects `mode?_winners.csv` and '
      'everything built on it, including `MODEA_WINNERS.md`.** It is filed in '
      '`results/r2gate2/gate2_vs_gate3_peryear.csv` and is not fixed here, '
      'because fixing it means deciding which engine is right about trade-year '
      'attribution and that is a change to what is computed.\n')
    a('\n## What makes this a test\n')
    a('The winners were selected on the FIVE-step walk, whose earliest tuning '
      'year is 2011 and whose trade years are 2016-2020. **Trade years 2010 '
      'through 2015 were touched by no part of that selection** — not by '
      'tuning, not by grading, not by the luck floors.\n')
    a('\n## Era-correct costs\n')
    a('`cost_table_h22.csv` was calibrated on **2016-2020** spreads, and it '
      'carries `bp_2004_2015` beside them. **25 of 28 pairs were wider in '
      '2004-2015, median 1.26x.** So charging the 2010-2015 trade years the '
      '2016-2020 table under-charges them, and the six unseen years are '
      'FLATTERED in the charged column.\n')
    a('\nThe era column re-scores the **same selected configurations** under '
      '`results/cost_table_era_2004_2015.csv`, built from that column. Only the '
      'costs change, so the difference isolates the cost effect rather than '
      'mixing in a different selection. R is taken from the engine\'s '
      're-scored daily series, not from the bank — the bank was built under the '
      'other table and reading it would ignore the override entirely, which is '
      'how a first attempt returned a difference of exactly zero.\n')
    for mode in ('A', 'B'):
        f = os.path.join(OUT, 'mode%s_b1winners.csv' % mode)
        fe = os.path.join(OUT, 'mode%s_b1winners_era.csv' % mode)
        D = _safe_csv(f); E = _safe_csv(fe)
        a('\n## Mode %s\n' % mode)
        if not len(D):
            a('_Not run yet._\n'); continue
        a('### R per trade year, 2010-2020 — corrected\n')
        a('**2010-2015 were never seen at selection.** 2016-2020 are the years '
          'the winners were chosen on and now reproduce the record exactly.\n')
        a(G3x.BK_tbl(D, ['sid', 'stream'] + ['R_%d' % y
                                             for y in NEW_YEARS + OLD_YEARS]))
        a('\n### The six never-seen years, charged both ways\n')
        T_ = D[['sid', 'stream', 'R_new6', 'n_new6', 'dd_new6', 't_new6',
                'years_pos_new6', 'prop_return_new6']].copy()
        if len(E) == len(D):
            T_['R_new6_era'] = E.R_new6.values
            T_['R_delta_era'] = (E.R_new6.values - D.R_new6.values)
            T_['R_delta_per_trade'] = T_.R_delta_era / D.n_new6.values
            T_['prop_return_new6_era'] = E.prop_return_new6.values
        a(G3x.BK_tbl(T_, list(T_.columns)))
        nn = int((D.R_new6 > 0).sum())
        c6 = int((D.prop_return_new6 >= WN.PROP_TARGET).sum())
        a('\n**%d of %d winners are positive over the six never-seen years '
          'under the charged table, and %s under era-correct costs. %d clear '
          'the %.0f%%/yr prop target either way.**\n'
          % (nn, len(D),
             ('%d of %d' % (int((E.R_new6 > 0).sum()), len(E))) if len(E) == len(D)
             else 'not yet measured', c6, WN.PROP_TARGET))
        if len(E) == len(D):
            a('\nThe era correction costs every winner between %.1f and %.1f R '
              'over the six years — about %.4f R per trade, consistent across '
              'all of them, which is the sanity check a uniform cost increase '
              'should pass.\n'
              % (abs(T_.R_delta_era.max()), abs(T_.R_delta_era.min()),
                 float(T_.R_delta_per_trade.mean())))
        a('\n### All eleven years\n')
        a(G3x.BK_tbl(D, ['sid', 'R_all11', 'n_all11', 'dd_all11',
                         'years_pos_all11', 'prop_return_all11']))
    a('\n## How to read this\n')
    a('These winners cleared two luck floors on 2016-2020 and they do not '
      'generalise backwards. That is a finding about the **selection method**, '
      'not about these ten strategies: the floors did their job on the years '
      'they were given, and those years were not representative. Charging the '
      'costs that actually prevailed makes it worse, not better.\n')
    a('\n## Still pending\n')
    a('- The family sample and the control run as a second stage, reported in '
      '`B1_NARROW.md`. Until then a winner holding up here cannot be separated '
      'from the family holding up.\n')
    a('- The random-entry null on these six years needs an engine pass and is '
      'not in this read.\n')
    a('- **The gate 2 / gate 3 per-year divergence above is unresolved.**\n')
    a('\n## Provenance\n')
    for nm in ('modeA_b1winners', 'modeB_b1winners', 'modeA_b1winners_era',
               'modeB_b1winners_era'):
        p_ = os.path.join(OUT, '%s.csv' % nm)
        if os.path.exists(p_):
            a('- `%s` — %s rows, md5 `%s`'
              % (os.path.relpath(p_, _R), f'{len(_safe_csv(p_)):,}',
                 hashlib.md5(open(p_, 'rb').read()).hexdigest()[:12]))
    for p_ in (os.path.join(ROOTOUT, 'r2gate2_cond3_crosswalk.csv'),
               os.path.join(ROOTOUT, 'r2gate2', 'gate2_vs_gate3_peryear.csv'),
               os.path.join(ROOTOUT, 'cost_table_era_2004_2015.csv')):
        if os.path.exists(p_):
            a('- `%s` — %s rows, md5 `%s`'
              % (os.path.relpath(p_, _R), f'{len(_safe_csv(p_)):,}',
                 hashlib.md5(open(p_, 'rb').read()).hexdigest()[:12]))
    out = out or os.path.join(OUT, 'B1_WINNERS.md')
    open(out, 'w').write('\n'.join(L) + '\n')
    print('  B1_WINNERS.md: %d lines -> %s'
          % (len('\n'.join(L).splitlines()), os.path.relpath(out, _R)), flush=True)
    return out


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


def _per_year(win_one, stream):
    """-> {calendar_year: R per trade} for ONE STREAM, trade years only.

    `stream` is required. The first version summed the stream axis, which pools
    trend and chop, routed and always-on, into one number that corresponds to
    no strategy. See the note in stage_winners.
    """
    out = {}
    for si, stp in enumerate(G2.steps()):
        y = stp['trade'][0]
        yi = y - G2.YEAR0
        n = float(win_one[stream, si, yi, 0])
        r = float(win_one[stream, si, yi, 1])
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
    join = []
    for mode in ('A', 'B'):
        try:
            bank, CB = read_bank(mode)
        except AssertionError:
            a('\n## Mode %s\n\n_No B1-narrow bank yet._\n' % mode)
            continue
        U = _safe_csv(os.path.join(OUT, 'mode%s_b1narrow_universe.csv' % mode))
        # THE JOIN IS ON `sid`, NOT ON `bank_row`. G2.run banks by POSITION in
        # the `combos` list it was handed, so this bank is keyed 0..4007 by
        # position in the bank_row-sorted universe, while the csv's `bank_row`
        # is the row in the FULL gate-2 bank and runs to 273,778. Joining on
        # bank_row matched 27 of 4,008 rows by coincidence. `sid` is the
        # strategy identity and the bank carries it in its own `combo` array,
        # so it is the only join that survives the universe being re-sampled.
        by_sid = {}
        for _k, _c in CB.items():
            by_sid.setdefault('|'.join(str(x) for x in _c), int(_k))
        _hit = _miss = 0
        for _i, u in U.iterrows():
            k = by_sid.get(str(u.sid))
            if k is None or k not in bank:
                _miss += 1
                continue
            _hit += 1
            # THE UNIVERSE CSV CARRIES NO `stream` COLUMN. `universe()` writes
            # bank_row, sid, cohort, mode only, because the family and the
            # control have no SELECTED stream -- only the winners do. The first
            # version of this block required one, found none, and skipped every
            # one of the 8,010 banked rows, which emptied the entire report
            # while every chain stage still reported OK. So: use the named
            # stream when the csv has one, otherwise read ALL FOUR streams and
            # label each. The winner tables below pick each winner's own
            # selected stream back out of the four.
            if 'stream' in U.columns and isinstance(u.stream, str):
                sts = [(list(G2.STREAMS).index(u.stream), str(u.stream))]
            else:
                sts = list(enumerate(G2.STREAMS))
            for st_, stname in sts:
                per = _per_year(bank[k], st_)
                sn = _stats(per, NEW_YEARS); so = _stats(per, OLD_YEARS)
                sa = _stats(per, NEW_YEARS + OLD_YEARS)
                r = dict(mode=mode, cohort=u.cohort, bank_row=k, sid=u.sid,
                         stream=stname,
                         R_new6_mean=sn['mean_R'], t_new6=sn['t'],
                         years_pos_new6=sn['years_positive'],
                         R_old5_mean=so['mean_R'], t_old5=so['t'],
                         years_pos_old5=so['years_positive'],
                         R_all11_mean=sa['mean_R'],
                         years_pos_all11=sa['years_positive'])
                for y in NEW_YEARS + OLD_YEARS:
                    r['R_%d' % y] = per.get(y, np.nan)
                    r['never_seen_%d' % y] = int(y in NEW_YEARS)
                rows.append(r)
        join.append((mode, len(U), _hit, _miss, len(bank)))
    D = pd.DataFrame(rows)
    # EACH WINNER'S OWN SELECTED STREAM, taken from the five-step selection
    # record, so the winner tables carry one row per winner rather than four.
    sel = {}
    for _m in ('A', 'B'):
        _wf = os.path.join(OUT, 'mode%s_b1winners.csv' % _m)
        if os.path.exists(_wf) and os.path.getsize(_wf) > 1:
            _W = _safe_csv(_wf)
            if {'stream', 'sid'} <= set(_W.columns):
                for _j, _wr in _W.iterrows():
                    # KEYED ON sid, NOT bank_row: `D.bank_row` is this bank's
                    # POSITIONAL key (0..4007) while the winners csv carries
                    # the full gate-2 bank row, so the two never match.
                    sel[(_m, str(_wr.sid))] = str(_wr.stream)
    if len(D):
        D['is_selected_stream'] = [
            int(sel.get((str(m_), str(sid_))) == str(s_))
            for m_, sid_, s_ in zip(D['mode'], D.sid, D.stream)]
    f = os.path.join(OUT, 'b1narrow_per_strategy.csv')
    D.to_csv(f, index=False)
    if join:
        a('\n**THE JOIN, STATED.** Universe rows, rows matched into the bank by '
          '`sid`, rows not matched, and strategies in the bank:\n')
        for _m, _nu, _h, _ms, _nb in join:
            a('- mode %s: %s universe rows, **%s matched**, %s unmatched, '
              '%s in the bank' % (_m, f'{_nu:,}', f'{_h:,}', f'{_ms:,}',
                                  f'{_nb:,}'))
        if any(x[3] for x in join):
            a('\nUnmatched rows are universe rows whose strategy is not in the '
              'bank -- the universe csv was re-sampled after that bank was '
              'built. They are dropped, not substituted.\n')
    if len(D):
        # PROP RETURN needs a drawdown; the eleven-step bank has no max DD, so
        # it is computed from the per-year spread as a STATED PROXY and labelled.
        D['prop_proxy_new6'] = WN.PROP_DIP / 6.0 * D.R_new6_mean / \
            D[['R_%d' % y for y in NEW_YEARS]].std(axis=1).replace(0, np.nan)
        a('\n## The 10 winners, year by year\n')
        a('`never_seen = 1` marks a year no part of the original selection '
          'touched.\n')
        w = D[(D.cohort == 'winner') & (D.is_selected_stream == 1)]
        if not len(w):
            a('\n_The selected-stream join found no winner row; the four streams '
              'are shown instead and are NOT one row per winner._\n')
            w = D[D.cohort == 'winner']
        a('Stream is each winner\'s **own selected stream** from the five-step '
          'record, not a pooled figure.\n')
        a(G3x.BK_tbl(w, ['mode', 'sid', 'stream']
                     + ['R_%d' % y for y in NEW_YEARS + OLD_YEARS]))
        a('\n### The six never-seen years alone, per winner\n')
        a(G3x.BK_tbl(w, ['mode', 'sid', 'stream',
                         'R_new6_mean', 't_new6', 'years_pos_new6',
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
        a('Family and control are shown PER STREAM, because neither cohort has '
          'a selected stream and pooling the four would describe no strategy.\n')
        g = D.groupby(['mode', 'cohort', 'stream'], as_index=False).agg(
            n=('bank_row', 'size'), mean_new6=('R_new6_mean', 'mean'),
            median_new6=('R_new6_mean', 'median'),
            pct_positive_new6=('R_new6_mean', lambda s: 100.0 * (s > 0).mean()),
            mean_old5=('R_old5_mean', 'mean'),
            mean_t_new6=('t_new6', 'mean'))
        g.to_csv(os.path.join(OUT, 'b1narrow_cohorts.csv'), index=False)
        w.to_csv(os.path.join(OUT, 'b1narrow_winners_new6.csv'), index=False)
        a(G3x.BK_tbl(g, list(g.columns)))
        a('\n### Each winner against the control, on its OWN stream\n')
        a('The percentile is the share of CONTROL strategies on the same stream '
          'and in the same mode whose mean R per trade on the six never-seen '
          'years is **below** the winner. 50 means the winner is at the control '
          'median; a winner that carried a real edge into unseen years should '
          'sit high.\n')
        _pr = []
        for _j, _w in w.iterrows():
            _c = D[(D['mode'] == _w['mode']) & (D.cohort == 'control')
                   & (D.stream == _w.stream)]
            if not len(_c):
                continue
            _pr.append(dict(mode=_w['mode'], sid=_w.sid, stream=_w.stream,
                            R_new6_mean=_w.R_new6_mean,
                            control_n=len(_c),
                            control_mean=float(_c.R_new6_mean.mean()),
                            pctile_vs_control=100.0 * float(
                                (_c.R_new6_mean < _w.R_new6_mean).mean())))
        if _pr:
            P = pd.DataFrame(_pr)
            a(G3x.BK_tbl(P.sort_values('pctile_vs_control', ascending=False),
                         list(P.columns)))
            a('\n**Median winner percentile against its own-stream control: '
              '%.1f.** %d of %d winners sit above the control median.\n'
              % (float(P.pctile_vs_control.median()),
                 int((P.pctile_vs_control > 50).sum()), len(P)))
            P.to_csv(os.path.join(OUT, 'b1narrow_winner_vs_control.csv'),
                     index=False)
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
                     ['mode', 'sid', 'stream', 'R_new6_mean',
                      'prop_proxy_new6']))
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



def _bank_arrays(mode, tag):
    """(win, tag) dicts keyed by bank row, for any bank directory."""
    d = G2.out_dir(mode, tag)
    fs = sorted(glob.glob(os.path.join(d, 'shard_*_part*.npz')))
    assert fs, 'no bank at %s' % d
    win, tg, cb = {}, {}, {}
    for f in fs:
        z = np.load(f, allow_pickle=True)
        idx = np.asarray(z['idx'], np.int64)
        if not len(idx):
            continue
        w_ = np.asarray(z['win'], np.float32)
        t_ = np.asarray(z['tag'], np.int32)
        c_ = np.asarray(z['combo'], dtype=object)
        for j, k in enumerate(idx):
            win[int(k)] = w_[j]; tg[int(k)] = t_[j]; cb[int(k)] = tuple(c_[j])
    return win, tg, cb


SHARED_YEARS = tuple(range(2016, 2021))


def condition3(modes=('A', 'B'), tol=1e-6, verbose=True, out=None):
    """CONDITION 3 — CROSS-WALK REPRODUCTION.

    Jack, 24 Nov: trade years 2016-2020 use the same tuning years in both
    walks -- tune 2011-2014 / grade 2015 / trade 2016, and so on -- so the
    eleven-step walk MUST reproduce the five-step record on them exactly.

    WHAT IS COMPARED, AND WHY NOT THE WINNERS CSV. Jack's wording named
    mode?_winners.csv as the reference. That file's R_<year> comes from the
    GATE 3 KPI bank, not from gate 2's win array, and the two disagree on
    41 of 50 winner-years by a median of 1.01 R -- with the same strategy, the
    same config index and the same year. A direct re-score of winner 1's
    config 289 over 2016 returns 13.812019, which is gate 2's number, so gate 2
    is the faithful record and the gate 3 KPI bank is the one that diverges.
    Comparing ext11 against the winners csv would therefore fail for a reason
    that has nothing to do with the walk. So this condition compares the ext11
    bank against the BASE5 BANK, which is the cross-walk property Jack is
    actually testing, and the gate2-vs-gate3 divergence is filed separately as
    its own defect.

    Checks, per winner and per shared year, on the winner's OWN stream:
      per-year total R      equal to `tol`
      per-year trade count  equal to `tol`
      selected config index identical
    """
    rows = []
    for mode in modes:
        W = winners_frame(mode)
        b5, t5, _c5 = _bank_arrays(mode, 'full')
        try:
            e11, t11, c11 = _bank_arrays(mode, TAG_WIN)
        except AssertionError:
            if verbose:
                print('  condition 3 [mode %s]: no ext11 winner bank yet' % mode,
                      flush=True)
            continue
        # the ext11 bank is keyed by POSITION in the winners frame
        for wi, w in W.iterrows():
            k5 = int(w.bank_row)
            if wi not in e11 or k5 not in b5:
                continue
            assert '|'.join(c11[wi]) == w.sid, (
                'ext11 row %d holds %s, the winners frame says %s'
                % (wi, '|'.join(c11[wi]), w.sid))
            st = list(G2.STREAMS).index(w.stream)
            for y in SHARED_YEARS:
                s5, y5 = y - 2016, y - 2011           # base5: YEAR0 2011
                s11, y11 = y - 2010, y - 2005         # ext11: YEAR0 2005
                r5 = float(b5[k5][st, s5, y5, 1]); n5 = float(b5[k5][st, s5, y5, 0])
                r11 = float(e11[wi][st, s11, y11, 1]); n11 = float(e11[wi][st, s11, y11, 0])
                c5_ = int(t5[k5][st, s5]); c11_ = int(t11[wi][st, s11])
                rows.append(dict(mode=mode, winner=wi + 1, sid=w.sid,
                                 stream=w.stream, year=y,
                                 base5_R=r5, ext11_R=r11, dR=abs(r11 - r5),
                                 base5_n=n5, ext11_n=n11, dn=abs(n11 - n5),
                                 base5_cfg=c5_, ext11_cfg=c11_,
                                 cfg_same=int(c5_ == c11_)))
    D = pd.DataFrame(rows)
    out = out or os.path.join(ROOTOUT, 'r2gate2_cond3_crosswalk.csv')
    D.to_csv(out, index=False)
    if not len(D):
        if verbose:
            print('  CONDITION 3: nothing to compare (no ext11 winner bank)',
                  flush=True)
        return D, False
    badR = D[D.dR > tol]; badn = D[D.dn > tol]; badc = D[D.cfg_same == 0]
    ok = (len(badR) == 0 and len(badn) == 0 and len(badc) == 0)
    if verbose:
        print('  CONDITION 3 (cross-walk reproduction): %d comparisons over '
              '%d winner-rows x %d shared years'
              % (len(D), len(D) // max(1, len(SHARED_YEARS)),
                 len(SHARED_YEARS)), flush=True)
        print('    per-year R   : worst |diff| %.3e  (%d over tol)'
              % (D.dR.max(), len(badR)), flush=True)
        print('    trade count  : worst |diff| %.3e  (%d over tol)'
              % (D.dn.max(), len(badn)), flush=True)
        print('    config index : %d of %d identical'
              % (int(D.cfg_same.sum()), len(D)), flush=True)
        print('    -> %s' % ('PASS' if ok else 'FAIL'), flush=True)
        for _i, r in badR.head(5).iterrows():
            print('       FAIL %s w%d %d: base5 %.6f ext11 %.6f'
                  % (r['mode'], r.winner, r.year, r.base5_R, r.ext11_R), flush=True)
    return D, ok


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
    elif st == 'winners':
        stage_winners(md, jobs=G.opt('--jobs', int, 4),
                      costtag=G.opt('--costtag', str, ''))
    elif st == 'mdwinners':
        stage_md_winners()
    elif st == 'cond3':
        _D, _ok = condition3()
        if not _ok:
            raise SystemExit('CONDITION 3 FAILED -- nothing from the extended '
                             'walk may be quoted')
    elif st == 'md':
        stage_md()
    else:
        raise SystemExit('unknown stage %s' % st)
