import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""TWO MOTIVATED TREND CONSTRUCTIONS (Layer 1 research round 2, 10 Nov).
Present tense only -- no money metric appears in this file.

T1, TREND AS BROKEN CHOP. Premise, measured in the chronic study: this panel's
resting state is mean reversion, so trend is the FAILURE of snap-back rather
than a signature of its own. Built from the proven chop machinery and nothing
new: `structure.swings(c, N_SCORE)` gives the tracked range boundary the chop
measures already use; a BREAK is a close outside it; the break either SNAPS
BACK inside within R bars or HOLDS. Declared R = 5 and 10.
  score(t), from bars <= t-1: the share of breaks HELD over the trailing 106
  bars (the shipped window -- no sweep), with net progress beyond the broken
  boundary in tuning-window vol units as the declared secondary read.

T2, CURRENCY-LEG TREND. Premise, measured: trends are currency stories, leg
sharing triples state agreement, and the acute detector's currency-leg
machinery already works. Same machinery, slow horizon:
  strength(c, t) = the cumulative log change of currency c against the
  equal-weight basket of the other seven over the trailing 106 bars, built
  from the 7 USD legs, in units of that leg's TUNING-WINDOW vol (constant,
  never trailing).
  score(XY, t) = |strength X - strength Y|; the signed version is the declared
  secondary read. THIS CONSTRUCTION HAS NOTHING TO SWEEP: the window and the
  dwell are the shipped ones and there is no third knob.

Both: cuts learned on the tuning window only, dwell 5 (the shipped dwell),
warm-up = no label, everything lagged one bar, 2021+ sealed in the loader.
Selection for T1: R by tuning separation SUBJECT TO run length consistent with
the measured trending-episode duration and flip rate no worse than the shipped
axis; both R values reported regardless.

    python3 code/trendt12.py --stage battery
    python3 code/trendt12.py --stage null
    python3 code/trendt12.py --stage report
"""
import argparse, time
import numpy as np, pandas as pd
from structval import SPLIT, SHAPE, properties, separation, surrogate
from structure import swings
from combined import confirm, DWELL
import twoscores as TS

STAMP = '2026-11-10'
SEAL = pd.Timestamp('2020-12-31')
W = TS.W                 # 106, the shipped window. Not swept.
N_SW = TS.N_SCORE        # 19, the swing order the chop measures already use
RS = (5, 10)             # declared snap-back horizons for T1
CCY = ['EUR', 'GBP', 'AUD', 'NZD', 'USD', 'CAD', 'CHF', 'JPY']
USD_LEGS = ['EURUSD', 'GBPUSD', 'AUDUSD', 'NZDUSD', 'USDCAD', 'USDCHF', 'USDJPY']
NSHUF = int(os.environ.get('FX_NSHUF', 200))


def out(n):
    return os.path.join(ROOTOUT, 'trend_%s_%s' % (n, STAMP))


def load_px():
    px = pd.read_csv(os.path.join(ROOTDATA, 'px28.csv'), index_col=0, parse_dates=True).astype(float)
    return px if os.environ.get('FX_ALLOW_W4') == '1' else px[px.index <= SEAL]


# ----------------------------------------------------------------- T1
def t1_scores(px, R):
    """Share of boundary breaks that HELD, and net progress beyond the broken
    boundary, both over the trailing W bars, from bars <= t-1."""
    lp = np.log(px); rr = lp.diff()
    sd = rr[rr.index < SPLIT].std()                    # tuning-window vol, constant
    held = pd.DataFrame(index=px.index, columns=px.columns, dtype=float)
    prog = pd.DataFrame(index=px.index, columns=px.columns, dtype=float)
    for p in px.columns:
        c = px[p].values.astype(float)
        hi, hip, lo, lop = swings(c, N_SW)
        outside_up = c > hi
        outside_dn = c < lo
        out_any = outside_up | outside_dn
        prev = np.r_[False, out_any[:-1]]
        start = out_any & ~prev                        # the bar a break opens
        n = len(c)
        is_break = np.zeros(n, bool); is_held = np.zeros(n, bool); gain = np.full(n, np.nan)
        s = float(sd[p]) if np.isfinite(sd[p]) and sd[p] > 0 else np.nan
        for i in np.flatnonzero(start):
            j = min(i + R, n - 1)
            if j <= i:
                continue
            is_break[i] = True
            up = bool(outside_up[i])
            b = hi[i] if up else lo[i]
            if not np.isfinite(b):
                is_break[i] = False; continue
            # snap-back = back inside the OLD boundary at any bar within R
            win = c[i + 1:j + 1]
            backin = (win <= b).any() if up else (win >= b).any()
            is_held[i] = not backin
            # net progress beyond the broken boundary, in vol units
            ext = win.max() if up else win.min()
            gain[i] = (np.log(max(ext, 1e-12)) - np.log(max(b, 1e-12))) / s if np.isfinite(s) else np.nan
            if not up:
                gain[i] = -gain[i]
        B = pd.Series(is_break, index=px.index).rolling(W).sum()
        H = pd.Series(is_held, index=px.index).rolling(W).sum()
        G = pd.Series(np.where(is_break, gain, np.nan), index=px.index).rolling(W).mean()
        held[p] = (H / B.replace(0, np.nan))
        prog[p] = G
    return held.shift(1), prog.shift(1)


# ----------------------------------------------------------------- T2
def t2_scores(px):
    """Currency strength against the equal-weight basket of the other seven, from
    the 7 USD legs, over the trailing W bars, in tuning-window vol units; the pair
    score is the absolute difference of the two legs' strengths."""
    lp = np.log(px)
    have = [p for p in USD_LEGS if p in px.columns]
    if len(have) != 7:
        raise SystemExit('t2: need all 7 USD legs, found %d' % len(have))
    # log change of each currency against USD over the trailing window
    chg = {}
    for p in have:
        d = lp[p] - lp[p].shift(W)
        if p.startswith('USD'):
            chg[p[3:]] = -d                 # USDJPY up = JPY down
        else:
            chg[p[:3]] = d
    chg['USD'] = pd.Series(0.0, index=lp.index)
    C = pd.DataFrame(chg)[CCY]
    # vs the equal-weight basket of the other seven: subtract the cross-sectional mean
    Cb = C.sub(C.mean(axis=1), axis=0)
    # in units of that leg's TUNING-WINDOW vol over the same horizon (constant)
    rr = lp.diff(); sd = rr[rr.index < SPLIT].std()
    legvol = {}
    for c in CCY:
        ls = [sd[p] for p in have if c in (p[:3], p[3:])]
        legvol[c] = (np.mean(ls) if ls else np.nan) * np.sqrt(W)
    legvol['USD'] = np.nanmean([sd[p] for p in have]) * np.sqrt(W)
    Z = pd.DataFrame({c: Cb[c] / legvol[c] for c in CCY})
    absd = pd.DataFrame(index=px.index, columns=px.columns, dtype=float)
    sgnd = pd.DataFrame(index=px.index, columns=px.columns, dtype=float)
    for p in px.columns:
        a, b = p[:3], p[3:]
        if a in Z.columns and b in Z.columns:
            d = Z[a] - Z[b]
            absd[p] = d.abs(); sgnd[p] = d
    return absd.shift(1), sgnd.shift(1)


# ----------------------------------------------------------------- shared
def label_of(sc, cut):
    L = pd.DataFrame('', index=sc.index, columns=sc.columns, dtype=object)
    L[sc >= cut] = 'trending'; L[sc < cut] = 'ranging'; L[sc.isna()] = ''
    return confirm(L, DWELL)


def cut_on_tuning(sc):
    v = sc[sc.index < SPLIT].stack().dropna()
    return float(v.median()) if len(v) else np.nan


def run_stats(L):
    med, flips, n_lab, n_tot, n_tr = [], 0, 0, 0, 0
    for p in L.columns:
        v = L[p]; v = v[(v != '') & v.notna()]
        n_tot += len(L[p]); n_lab += len(v); n_tr += int((v == 'trending').sum())
        if len(v) < 2:
            continue
        ch = (v != v.shift()).values; ch[0] = False
        flips += int(ch.sum())
        med.append(float(v.groupby((v != v.shift()).cumsum()).size().median()))
    return dict(median_run=float(np.median(med)) if med else np.nan,
                flip_rate=(flips / n_lab) if n_lab else np.nan,
                coverage=(n_lab / n_tot) if n_tot else np.nan,
                share_trending=(n_tr / n_lab) if n_lab else np.nan)


def sep_of(L, P, oos_only):
    return float(separation(L, P, oos_only=oos_only).gap_sd.reindex(SHAPE).mean())


def shipped():
    import l2sweep as S
    S.layer1_header_check(os.path.join(ROOTOUT, 'layer1_states.csv'))
    d = pd.read_csv(os.path.join(ROOTOUT, 'layer1_states.csv'), comment='#', parse_dates=['date'],
                    usecols=['date', 'pair', 'shape2', 'trend_score', 'chop_score'])
    d = d[d.date <= SEAL]
    sh = d.pivot(index='date', columns='pair', values='shape2')
    lab = pd.DataFrame('', index=sh.index, columns=sh.columns, dtype=object)
    lab[sh == 'trending'] = 'trending'; lab[sh.notna() & (sh != 'trending')] = 'ranging'
    return (lab, d.pivot(index='date', columns='pair', values='trend_score'),
            d.pivot(index='date', columns='pair', values='chop_score'))


def variants(px):
    V = {}
    for R in RS:
        h, g = t1_scores(px, R)
        V['T1_R%d' % R] = dict(score=h, second=g, family='T1 broken chop', knob='R=%d' % R)
    a, s = t2_scores(px)
    V['T2'] = dict(score=a, second=s, family='T2 currency leg', knob='none')
    for k in V:
        V[k]['cut'] = cut_on_tuning(V[k]['score'])
        V[k]['label'] = label_of(V[k]['score'], V[k]['cut'])
    return V


def stage_battery():
    t0 = time.time(); px = load_px(); P = properties(px); V = variants(px)
    SL, ts, cs = shipped()
    rows = []
    sh_is, sh_oos, sh_run = sep_of(SL, P, False), sep_of(SL, P, True), run_stats(SL)
    for k, d in V.items():
        L = d['label']; r = run_stats(L)
        a = d['score'].stack()
        j = pd.DataFrame({'x': a, 'tr': ts.reindex_like(d['score']).stack(),
                          'ch': cs.reindex_like(d['score']).stack(),
                          'st': P['range_to_path'].stack()}).dropna()
        ag = pd.DataFrame({'a': L.stack(), 'b': SL.reindex_like(L).stack()}).replace('', np.nan).dropna()
        rows.append(dict(variant=k, family=d['family'], knob=d['knob'], cut=d['cut'],
                         separation_tuning=sep_of(L, P, False), separation_holdout=sep_of(L, P, True),
                         median_run=r['median_run'], flip_rate=r['flip_rate'], coverage=r['coverage'],
                         share_trending=r['share_trending'],
                         corr_shipped_trend=float(j.x.corr(j.tr, method='spearman')),
                         corr_shipped_chop=float(j.x.corr(j.ch, method='spearman')),
                         corr_straightness=float(j.x.corr(j.st, method='spearman')),
                         label_agreement_shipped=float((ag.a == ag.b).mean())))
    B = pd.DataFrame(rows)
    # correlation between the two constructions
    ks = list(V)
    for i, k1 in enumerate(ks):
        for k2 in ks[i + 1:]:
            q = pd.DataFrame({'a': V[k1]['score'].stack(), 'b': V[k2]['score'].stack()}).dropna()
            B.loc[B.variant == k1, 'corr_with_' + k2] = float(q.a.corr(q.b, method='spearman'))
    B['shipped_separation_tuning'] = sh_is; B['shipped_separation_holdout'] = sh_oos
    B['shipped_median_run'] = sh_run['median_run']; B['shipped_flip_rate'] = sh_run['flip_rate']
    B.to_csv(out('t12_battery') + '.csv', index=False)
    # episodes, vintages, sub-period
    import episodes as EP, refit as RF
    er = []
    for k, d in V.items():
        E = EP.episodes(d['label'], P, oos_only=True)
        if len(E):
            for prop in SHAPE:
                er.append(dict(variant=k, prop=prop, episode_gap_sd=float(EP.gap(E, prop)), n_episodes=int(len(E))))
    pd.DataFrame(er).to_csv(out('t12_episodes') + '.csv', index=False)
    vr = []
    for v in RF.VINTAGES:
        end = pd.Timestamp('%d-12-31' % v)
        if end > SEAL and os.environ.get('FX_ALLOW_W4') != '1':
            vr.append(dict(vintage=v, variant='', cut=np.nan, note='sealed, not run')); continue
        q = px[px.index <= end]
        for k, d in variants(q).items():
            vr.append(dict(vintage=v, variant=k, cut=d['cut'], n_bars=len(q), note=''))
    pd.DataFrame(vr).to_csv(out('t12_refit_vintages') + '.csv', index=False)
    sr = []
    for k, d in V.items():
        for lab, a, b in (('2016-2019', '2016-01-01', '2019-12-31'), ('2020', '2020-01-01', '2020-12-31')):
            L = d['label'].loc[a:b]; Pq = {x: P[x].loc[a:b] for x in P}
            r = run_stats(L)
            sr.append(dict(variant=k, period=lab, separation=sep_of(L, Pq, False), median_run=r['median_run'],
                           flip_rate=r['flip_rate'], coverage=r['coverage'], share_trending=r['share_trending']))
    pd.DataFrame(sr).to_csv(out('t12_subperiod') + '.csv', index=False)
    t = ['TREND CONSTRUCTIONS T1 (broken chop) AND T2 (currency leg) -- PRESENT-TENSE BATTERY. %s' % STAMP,
         'No money metric in this file. Cuts on the tuning window; ONE holdout confirm; 2021+ sealed.', '',
         B[['variant', 'family', 'knob', 'cut', 'separation_tuning', 'separation_holdout', 'median_run',
            'flip_rate', 'coverage', 'share_trending', 'corr_shipped_trend', 'corr_shipped_chop',
            'corr_straightness', 'label_agreement_shipped']].to_string(index=False, float_format=lambda v: '%8.4f' % v),
         '', 'shipped trend axis: separation %.4f tuning / %.4f holdout, median run %.1f, flip rate %.4f'
         % (sh_is, sh_oos, sh_run['median_run'], sh_run['flip_rate']),
         '', 'done in %.1f min' % ((time.time() - t0) / 60)]
    open(out('t12_battery') + '.txt', 'w').write('\n'.join(t) + '\n')
    print('\n'.join(t), flush=True)


def stage_null():
    """The same re-derive-everything null that killed the DC axis: on each surrogate
    the scores, the tuning-window vol and the cut are all rebuilt."""
    t0 = time.time(); px = load_px(); P = properties(px); V = variants(px)
    real = {k: sep_of(d['label'], P, True) for k, d in V.items()}
    rng = np.random.default_rng(20261110); rows = []
    for kind in ('sign', 'perm'):
        draws = {k: [] for k in V}
        for i in range(NSHUF):
            q = surrogate(px, kind, rng); Pq = properties(q)
            for k, d in variants(q).items():
                draws[k].append(sep_of(d['label'], Pq, True))
            if (i + 1) % 25 == 0:
                print('  %s null: %d/%d (%.1f min)' % (kind, i + 1, NSHUF, (time.time() - t0) / 60), flush=True)
        for k in V:
            v = np.array([x for x in draws[k] if np.isfinite(x)]); r = real[k]
            rows.append(dict(kind=kind, variant=k, real=r, n_draws=len(v), null_mean=float(v.mean()),
                             null_p95=float(np.percentile(v, 95)), null_max=float(v.max()),
                             corrected=r - float(v.mean()), p_value=float((v >= r).mean())))
    N = pd.DataFrame(rows); N.to_csv(out('t12_null') + '.csv', index=False)
    t = ['T1 / T2 -- %d-DRAW SURROGATE NULL (construction, vol and cut re-derived on every draw). %s' % (NSHUF, STAMP), '',
         N.to_string(index=False, float_format=lambda v: '%9.4f' % v),
         '', 'A construction whose real separation does not clear its own null NEVER reaches the money test.',
         'done in %.1f min' % ((time.time() - t0) / 60)]
    open(out('t12_null') + '.txt', 'w').write('\n'.join(t) + '\n')
    print('\n'.join(t), flush=True)


def stage_report():
    B = pd.read_csv(out('t12_battery') + '.csv'); N = pd.read_csv(out('t12_null') + '.csv')
    RL = pd.read_csv(os.path.join(ROOTOUT, 'run_lengths.csv'))
    rl = RL[(RL.block == 'is') & (RL.generation == 'g4_twoscore4') & RL.state.astype(str).str.contains('trend', case=False)]
    meas = float(rl['median'].median()); lo, hi = 0.5 * meas, 2.0 * meas
    ship_flip = float(B.shipped_flip_rate.iloc[0])
    B['run_ok'] = (B.median_run >= lo) & (B.median_run <= hi)
    B['flip_ok'] = B.flip_rate <= ship_flip
    B['eligible'] = B.run_ok & B.flip_ok
    p = N.pivot_table(index='variant', columns='kind', values='p_value')
    B['null_p_sign'] = B.variant.map(p['sign']); B['null_p_perm'] = B.variant.map(p['perm'])
    B['survives_null'] = (B.null_p_sign <= 0.05) & (B.null_p_perm <= 0.05)
    # T1's declared selection, among its own two R values
    t1 = B[B.family.str.startswith('T1')]
    el = t1[t1.eligible]
    pick = (el if len(el) else t1[t1.run_ok] if t1.run_ok.any() else t1).sort_values('separation_tuning', ascending=False)
    B['t1_selected'] = B.variant == (pick.variant.iloc[0] if len(pick) else '')
    B.to_csv(out('t12_selection') + '.csv', index=False)
    t = ['T1 / T2 -- SELECTION AND NULL VERDICT. %s' % STAMP, '',
         'Measured standard: g4_twoscore4 trending states run a median %.1f bars IS, so the admissible band is'
         ' %.1f-%.1f; flip rate must be no worse than the shipped axis (%.4f).' % (meas, lo, hi, ship_flip), '',
         B[['variant', 'family', 'knob', 'separation_tuning', 'separation_holdout', 'median_run', 'flip_rate',
            'run_ok', 'flip_ok', 'eligible', 'null_p_sign', 'null_p_perm', 'survives_null', 't1_selected']
           ].to_string(index=False, float_format=lambda v: '%8.4f' % v), '',
         'T1 selection (its own two R values): %s' % (pick.variant.iloc[0] if len(pick) else 'none'),
         '', 'NULL GATE -- only a construction clearing BOTH nulls at p <= 0.05 reaches the Layer 3 money test:',
         '  ' + ', '.join('%s: %s' % (r.variant, 'SURVIVES' if r.survives_null else 'FAILS (sign p %.2f, perm p %.2f)'
                                      % (r.null_p_sign, r.null_p_perm)) for r in B.itertuples())]
    surv = B[B.survives_null]
    t += ['', 'Reaching the money test: %s' % (', '.join(surv.variant) if len(surv) else 'NONE -- the round stops at the battery.')]
    open(out('t12_selection') + '.txt', 'w').write('\n'.join(t) + '\n')
    print('\n'.join(t), flush=True)
    # state files for whatever survives
    px = load_px(); V = variants(px)
    for r in surv.itertuples():
        d = V[r.variant]
        S = pd.DataFrame({'date': np.repeat(d['score'].index.values, d['score'].shape[1]),
                          'pair': np.tile(d['score'].columns.values, len(d['score'])),
                          'score': d['score'].values.ravel(), 'dc_shape': d['label'].values.ravel(),
                          'secondary': d['second'].values.ravel()})
        S['sample'] = np.where(S.date < SPLIT.to_datetime64(), 'is', 'holdout')
        h = ('# TREND AXIS CANDIDATE %s (%s, %s), cut %.4f learned on the tuning window, dwell %d. Rows are '
             'lagged one bar: a row dated D is built from bars <= D-1. 2021+ sealed and absent. Readers pass comment="#".\n'
             % (r.variant, r.family, r.knob, r.cut, DWELL))
        with open(out('states_%s' % r.variant.lower()) + '.csv', 'w') as fh:
            fh.write(h); S.to_csv(fh, index=False)
        print('wrote %s' % (out('states_%s' % r.variant.lower()) + '.csv'), flush=True)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--stage', required=True, choices=['battery', 'null', 'report'])
    a = ap.parse_args(); print('=== trendt12 %s ===' % a.stage, flush=True)
    {'battery': stage_battery, 'null': stage_null, 'report': stage_report}[a.stage]()
    print('TREND T12 STAGE %s COMPLETE' % a.stage.upper(), flush=True)


if __name__ == '__main__':
    main()
