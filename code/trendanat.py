import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""PART 1 -- FAILURE ANATOMY OF THE SHIPPED TREND AXIS (10 Nov). Measurement
only: no fix is attempted here and nothing in this file proposes one.

It reads what is already committed -- the shipped states and the mode C / A-B
routed trade tables of the blind-label round -- and asks four questions:

  1. WHERE INSIDE AN EPISODE the routed trend P&L sits (first third / middle /
     last third of each TRENDING episode) and where the losses sit. A
     diagnostic re-read of existing Layer 3 output, not a new money test.
  2. EPISODE TRUTH TABLE: did each labelled trending episode actually make net
     directional progress, in vol units, against a threshold learned on the
     tuning window? true-trend vs false-trend shares IS and holdout, and what
     the false ones look like on the chop measures.
  3. ONSET COST: median bars from the true start of the directional run to the
     bar the label confirms (dwell + lag), as a share of the measured ~21-bar
     trend.
  4. WHY C SURVIVES trend routing while A/B do not: the three modes' trade
     placement inside trending episodes -- entry position, hold, exit reason.

    python3 code/trendanat.py --stage all
"""
import argparse, time
import numpy as np, pandas as pd
import l2sweep as S
import l2walkfwd as W

STAMP = '2026-11-10'
SPLIT = pd.Timestamp('2016-01-01')
SEAL = pd.Timestamp('2020-12-31')
VOLWIN = 60


def out(n):
    return os.path.join(ROOTOUT, 'trend_anatomy_%s_%s' % (n, STAMP))


def states():
    S.layer1_header_check(os.path.join(ROOTOUT, 'layer1_states.csv'))
    d = pd.read_csv(os.path.join(ROOTOUT, 'layer1_states.csv'), comment='#', parse_dates=['date'],
                    usecols=['date', 'pair', 'shape2', 'trend_score', 'chop_score', 'activity'])
    return d[d.date <= SEAL]


def px_panel():
    px = pd.read_csv(os.path.join(ROOTDATA, 'px28.csv'), index_col=0, parse_dates=True).astype(float)
    return px[px.index <= SEAL]


def episodes_of(sh):
    """One row per (pair, TRENDING run): first bar, last bar, length."""
    rows = []
    for p, g in sh.groupby('pair'):
        g = g.sort_values('date')
        v = (g.shape2 == 'trending').values
        if not v.any():
            continue
        d = g.date.values
        gid = np.cumsum(np.r_[True, v[1:] != v[:-1]])
        for k in np.unique(gid[v]):
            m = (gid == k) & v
            rows.append(dict(pair=p, start=pd.Timestamp(d[m][0]), end=pd.Timestamp(d[m][-1]), n=int(m.sum())))
    return pd.DataFrame(rows)


def q1_pnl_position(E):
    """Routed trend P&L by position inside the episode, from the committed books."""
    rows = []
    for tag, lab, sl in (('_modec2_routed', 'mode C routed', ('C',)),
                         ('_dc_abtrend_sh2', 'A/B trend routed', ('A', 'B'))):
        tf = os.path.join(ROOTOUT, 'wf_trades%s.pkl' % tag)
        mf = os.path.join(ROOTOUT, 'wf_marks%s.pkl' % tag)
        if not (os.path.exists(tf) and os.path.exists(mf)):
            print('  q1: %s not on disk, skipped' % tag, flush=True); continue
        T = pd.read_pickle(tf)
        T = T.assign(sid=T.sid.astype(str), pair=T.pair.astype(str))
        ep = E.set_index('pair')      # T.R is the engine's own net R per trade
        for p, g in T.groupby('pair'):
            if p not in ep.index:
                continue
            e = ep.loc[[p]]
            for t in g.itertuples():
                m = (e.start <= t.entry) & (t.entry <= e.end)
                if not m.any():
                    continue
                r = e[m].iloc[0]
                pos = (t.entry - r.start).days / max((r.end - r.start).days, 1)
                third = 'first' if pos < 1 / 3 else ('middle' if pos < 2 / 3 else 'last')
                rows.append(dict(book=lab, pair=p, third=third, R=float(t.R),
                                 era='is' if t.entry < SPLIT else 'holdout',
                                 episode_bars=int(r.n)))
    D = pd.DataFrame(rows)
    if not len(D):
        return D, pd.DataFrame()
    g = D.groupby(['book', 'era', 'third']).R.agg(trades='size', total_R='sum', mean_R='mean',
                                                  share_positive=lambda s: float((s > 0).mean()),
                                                  loss_R=lambda s: float(s[s < 0].sum()))
    g['share_of_book_R'] = g.total_R / g.groupby(['book', 'era']).total_R.transform('sum')
    g['share_of_book_loss'] = g.loss_R / g.groupby(['book', 'era']).loss_R.transform('sum')
    return D, g.reset_index()


def q2_truth_table(E, px):
    """Did the episode actually go anywhere? progress = |log(last) - log(first)| in
    units of the pair's tuning-window daily vol x sqrt(bars). The threshold is
    learned ON THE TUNING WINDOW: the median progress of IS trending episodes."""
    lp = np.log(px); rr = lp.diff()
    sd = rr[rr.index < SPLIT].std()
    rows = []
    for e in E.itertuples():
        p = e.pair
        if p not in lp.columns:
            continue
        seg = lp[p].loc[e.start:e.end].dropna()
        if len(seg) < 3:
            continue
        prog = abs(float(seg.iloc[-1] - seg.iloc[0])) / (float(sd[p]) * np.sqrt(len(seg)))
        path = float(rr[p].loc[e.start:e.end].abs().sum())
        eff = abs(float(seg.iloc[-1] - seg.iloc[0])) / path if path > 0 else np.nan
        rows.append(dict(pair=p, start=e.start, end=e.end, bars=e.n, progress_vol=prog,
                         efficiency=eff, era='is' if e.start < SPLIT else 'holdout'))
    D = pd.DataFrame(rows)
    thr = float(D[D.era == 'is'].progress_vol.median())
    D['true_trend'] = D.progress_vol >= thr
    return D, thr


def q3_onset(E, px):
    """Bars from the true start of the directional run to label confirmation.

    The run's direction is the episode's own net direction; the true start is the
    last extreme before the episode's end in that direction -- i.e. how long the
    move had already been going when the label finally said so."""
    lp = np.log(px)
    rows = []
    for e in E.itertuples():
        p = e.pair
        if p not in lp.columns:
            continue
        v = lp[p]
        seg = v.loc[e.start:e.end].dropna()
        if len(seg) < 3:
            continue
        up = seg.iloc[-1] >= seg.iloc[0]
        back = v.loc[:e.start].dropna()
        if len(back) < 5:
            continue
        # the leg's true start: the most extreme point AGAINST the episode's
        # direction in the 60 bars before the label (a monotone walk-back breaks
        # on the first opposite tick and measures nothing on daily data).
        w = back.iloc[-61:-1] if len(back) > 61 else back.iloc[:-1]
        if len(w) < 2:
            continue
        j = int(np.argmin(w.values)) if up else int(np.argmax(w.values))
        run = len(w) - j
        moved = abs(float(seg.iloc[-1]) - float(w.iloc[j]))
        in_ep = abs(float(seg.iloc[-1]) - float(seg.iloc[0]))
        share_before = 1.0 - (in_ep / moved) if moved > 0 else np.nan
        rows.append(dict(pair=p, start=e.start, bars=e.n, direction='up' if up else 'down',
                         bars_before_label=int(run), share_of_move_before_label=float(share_before),
                         era='is' if e.start < SPLIT else 'holdout'))
    return pd.DataFrame(rows)


def q4_modes(E):
    """The three modes' trade placement inside trending episodes."""
    rows = []
    for tag, lab in (('_modec2_routed', 'C'), ('_dc_abtrend_sh2', 'A/B')):
        tf = os.path.join(ROOTOUT, 'wf_trades%s.pkl' % tag)
        if not os.path.exists(tf):
            continue
        T = pd.read_pickle(tf).assign(sid=lambda d: d.sid.astype(str), pair=lambda d: d.pair.astype(str))
        T['mode'] = T.sid.str[0]
        T['hold'] = (T.exit - T.entry).dt.days
        ep = E.set_index('pair')
        for t in T.itertuples():
            if t.pair not in ep.index:
                continue
            e = ep.loc[[t.pair]]
            m = (e.start <= t.entry) & (t.entry <= e.end)
            if not m.any():
                continue
            r = e[m].iloc[0]
            span = max((r.end - r.start).days, 1)
            rows.append(dict(book=lab, mode=t.mode, pair=t.pair,
                             entry_position=(t.entry - r.start).days / span,
                             hold_days=float(t.hold), episode_bars=int(r.n), R=float(t.R),
                             era='is' if t.entry < SPLIT else 'holdout',
                             exits_inside=bool(t.exit <= r.end)))
    D = pd.DataFrame(rows)
    if not len(D):
        return D, pd.DataFrame()
    g = D.groupby(['book', 'mode', 'era']).agg(
        trades=('R', 'size'), mean_entry_position=('entry_position', 'mean'),
        median_entry_position=('entry_position', 'median'), median_hold_days=('hold_days', 'median'),
        share_exit_inside_episode=('exits_inside', 'mean'), mean_R=('R', 'mean'),
        total_R=('R', 'sum'), share_positive=('R', lambda s: float((s > 0).mean()))).reset_index()
    return D, g


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--stage', default='all'); ap.parse_args()
    t0 = time.time()
    sh = states(); px = px_panel()
    E = episodes_of(sh)
    E.to_csv(out('episodes') + '.csv', index=False)
    D1, G1 = q1_pnl_position(E)
    if len(G1):
        G1.to_csv(out('pnl_by_position') + '.csv', index=False)
    D2, thr = q2_truth_table(E, px)
    D2.to_csv(out('truth_table') + '.csv', index=False)
    D3 = q3_onset(E, px)
    D3.to_csv(out('onset') + '.csv', index=False)
    D4, G4 = q4_modes(E)
    if len(G4):
        G4.to_csv(out('mode_placement') + '.csv', index=False)
    # the false-trend episodes on the chop measures
    sc = sh.groupby(['pair', 'date'])[['trend_score', 'chop_score']].first()
    fr = []
    for e in D2.itertuples():
        try:
            w = sc.loc[e.pair].loc[e.start:e.end]
        except Exception:
            continue
        if len(w):
            fr.append(dict(pair=e.pair, start=e.start, true_trend=bool(e.true_trend), era=e.era,
                           mean_trend_score=float(w.trend_score.mean()), mean_chop_score=float(w.chop_score.mean()),
                           bars=int(e.bars), progress_vol=float(e.progress_vol), efficiency=float(e.efficiency)))
    FR = pd.DataFrame(fr); FR.to_csv(out('false_trend_profile') + '.csv', index=False)
    t = ['PART 1 -- FAILURE ANATOMY OF THE SHIPPED TREND AXIS. %s' % STAMP,
         'Measurement only. Every number is read off committed files; no fix is proposed here.',
         'Shipped states %s, panel %s -> %s, 2021+ sealed and absent.'
         % ('results/layer1_states.csv', px.index.min().date(), px.index.max().date()), '',
         'Labelled TRENDING episodes: %d total, %d IS, %d holdout; median %d bars, mean %.1f.'
         % (len(E), int((E.start < SPLIT).sum()), int((E.start >= SPLIT).sum()), int(E.n.median()), E.n.mean()), '']
    if len(G1):
        t += ['1. ROUTED TREND P&L BY POSITION INSIDE THE EPISODE', '',
              G1.to_string(index=False, float_format=lambda v: '%9.4f' % v), '']
    t += ['2. EPISODE TRUTH TABLE (progress in vol units; threshold = the IS median, %.3f, learned on the tuning window)' % thr, '',
          D2.groupby(['era', 'true_trend']).agg(episodes=('bars', 'size'), median_bars=('bars', 'median'),
                                                median_progress=('progress_vol', 'median'),
                                                median_efficiency=('efficiency', 'median')).to_string(float_format=lambda v: '%8.3f' % v),
          '', 'share of labelled trending episodes that actually went somewhere:',
          D2.groupby('era').true_trend.mean().round(3).to_string(), '']
    if len(FR):
        t += ['   the false ones on the shipped scores:', '',
              FR.groupby(['era', 'true_trend'])[['mean_trend_score', 'mean_chop_score', 'efficiency']].median().to_string(float_format=lambda v: '%8.3f' % v), '']
    if len(D3):
        t += ['3. ONSET COST (bars the move had already run before the label confirmed)', '',
              D3.groupby('era').agg(episodes=('bars_before_label', 'size'), median_bars_late=('bars_before_label', 'median'),
                                    mean_bars_late=('bars_before_label', 'mean'),
                                    median_share_of_move_already_gone=('share_of_move_before_label', 'median')).round(2).to_string(),
              '', '   median episode is %d bars, so the label arrives %.0f%% of a median trend late.'
              % (int(E.n.median()), 100 * float(D3.bars_before_label.median()) / max(int(E.n.median()), 1)), '']
    if len(G4):
        t += ['4. TRADE PLACEMENT INSIDE TRENDING EPISODES, BY MODE', '',
              G4.to_string(index=False, float_format=lambda v: '%9.4f' % v), '']
    t += ['done in %.1f min' % ((time.time() - t0) / 60)]
    open(out('report') + '.txt', 'w').write('\n'.join(t) + '\n')
    print('\n'.join(t), flush=True)
    print('TREND ANATOMY COMPLETE', flush=True)


if __name__ == '__main__':
    main()
