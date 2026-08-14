import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""TODAY. The product view's data, computed here and committed -- never in the UI.

WHY THIS FILE EXISTS. The customer-facing view needs six things per pair that no
committed file carried: what changed in the last five days, whether a switch is
part-way through confirming, how far the scores sit from their boundary, how many
other pairs share the state through a common currency, how long the state has
held, and the market-wide header. Computing any of that in JavaScript would put
numbers on screen that trace to nothing. So it is computed here, written to
results/, and the interface only formats it.

IT COMPUTES NOTHING NEW ABOUT THE CLASSIFIER. Every state label here comes from
the shipped path -- final.scores, final.activity, twoscores.classify -- and the
run ASSERTS that the labels reproduce results/states_g4_twoscore4.csv exactly. If
this file and the shipped states ever disagree, this file is wrong.

THE PIECES, and the plain-English rule each one is translated by:

  PENDING. The classifier needs DWELL=5 consecutive days before it adopts a new
  state. The pre-dwell label is therefore already pointing somewhere new while
  the confirmed label still shows the old one. `pending_state` and `pending_days`
  expose exactly that, so the card can say "3 of 5 days toward ranging" instead
  of the switch appearing from nowhere two days later.

  HOW FIRM. Each score is cut at its in-sample median. Firmness is the distance
  from that cut in in-sample standard deviations, and the state is set by BOTH
  scores, so the reported figure is the SMALLER of the two distances -- a call is
  only as firm as its weakest side. Bands, declared here: >= 0.50 sd solidly,
  >= 0.20 clearly, below that barely. A "barely" call is not a wrong call; it is
  a call whose scores sit near the boundary and which the sensitivity work
  showed is the kind most likely to move on a small change.

  SHARED BET. How many of the other 27 pairs are in the same state today AND
  share a currency with this one. This is the routing warning from the
  cross-pair work: 28 labels is not 28 independent observations, and pairs
  sharing a leg agree about three times as often as pairs that do not.

  DAYS IN STATE is a FACT, never a warning. State age was tested and does not
  predict state death, so nothing here phrases a long run as overdue.

Writes results/today_pairs.csv, results/today_header.csv + .txt companions.
"""
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
EXT = os.path.join(ROOTDATA, 'ext.csv')
SHIPPED = os.path.join(ROOTOUT, 'states_g4_twoscore4.csv')
SPLIT = pd.Timestamp('2016-01-01')
CELLS = ['trending', 'ranging', 'trend-in-range', 'neither']
LOOKBACK = 5
FIRM_SOLID, FIRM_CLEAR = 0.50, 0.20

from final import scores, activity, DROP_TESTS, BUMP, ACTW
from combined import confirm, DWELL
from drivers import crisis_mask, hdr


def firm_word(z):
    if not np.isfinite(z):
        return 'unknown'
    return ('solidly' if z >= FIRM_SOLID else
            'clearly' if z >= FIRM_CLEAR else 'barely')


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    ship = pd.read_csv(SHIPPED, index_col=0, parse_dates=True, comment='#')
    fit = np.asarray(px.index < SPLIT)
    tr, ch = scores(px, fit, drop_tests=DROP_TESTS)
    act = activity(px, fit)
    trb = tr - act.replace(ACTW).astype(float) * BUMP
    ft = np.where(fit[:, None], trb.values, np.nan)
    fc = np.where(fit[:, None], ch.values, np.nan)
    mt, mc = np.nanmedian(ft), np.nanmedian(fc)
    sdt, sdc = np.nanstd(ft), np.nanstd(fc)
    hi_t, hi_c = trb > mt, ch > mc
    raw = pd.DataFrame(np.select(
        [(hi_t & ~hi_c).values, (~hi_t & hi_c).values, (hi_t & hi_c).values],
        ['trending', 'ranging', 'trend-in-range'], 'neither'),
        index=trb.index, columns=trb.columns)
    ok = trb.notna() & ch.notna()
    raw = raw.where(ok)
    lab = confirm(raw, DWELL)

    idx = ship.index.intersection(lab.index)
    A = lab.reindex(idx)[ship.columns]
    B = ship.reindex(idx)
    m = A.notna() & B.notna()
    same = float(((A == B) & m).sum().sum() / m.sum().sum())
    print('TODAY -- the product view\'s data')
    print('  control: labels reproduce states_g4_twoscore4.csv at %.4f' % same)
    assert same > 0.9999, ('today.py does not reproduce the shipped states '
                           '(%.4f) -- this file is wrong, not the classifier'
                           % same)
    print('  PASS.')

    lab = lab.dropna(how='all')
    t = lab.index[-1]
    prev = lab.index[max(0, len(lab.index) - 1 - LOOKBACK)]
    print('  as of %s (data through %s)' % (t.date(), px.index[-1].date()))

    cm, n_ev = crisis_mask(px.index)
    rows = []
    states_today = {}
    for p in lab.columns:
        v = lab[p].dropna()
        if not len(v) or v.index[-1] != t:
            continue
        states_today[p] = v.iloc[-1]
    for p, st in states_today.items():
        v = lab[p].dropna()
        a = act[p].reindex(v.index)
        # days in the current state
        run = 1
        while run < len(v) and v.iloc[-1 - run] == st:
            run += 1
        # what changed in the last LOOKBACK trading days
        win = v.loc[v.index > prev]
        awin = a.loc[a.index > prev]
        chg, chg_date, chg_from, chg_prev_run = '', '', '', 0
        for i in range(len(win) - 1, 0, -1):
            if win.iloc[i] != win.iloc[i - 1]:
                chg = 'state'
                chg_date = win.index[i]
                chg_from = win.iloc[i - 1]
                k = 1
                pos = v.index.get_loc(win.index[i])
                while pos - k >= 0 and v.iloc[pos - k] == chg_from:
                    k += 1
                chg_prev_run = k
                break
        if not chg:
            for i in range(len(awin) - 1, 0, -1):
                if (pd.notna(awin.iloc[i]) and pd.notna(awin.iloc[i - 1])
                        and awin.iloc[i] != awin.iloc[i - 1]):
                    chg = 'activity'
                    chg_date = awin.index[i]
                    chg_from = awin.iloc[i - 1]
                    break
        # pending: the pre-dwell label already pointing somewhere else
        rv = raw[p].dropna()
        pend_state, pend_days = '', 0
        if len(rv) and rv.iloc[-1] != st:
            k = 1
            while k < len(rv) and rv.iloc[-1 - k] == rv.iloc[-1]:
                k += 1
            pend_state, pend_days = rv.iloc[-1], int(min(k, DWELL))
        # firmness: the SMALLER of the two distances, in IS sd units
        zt = abs(float(trb[p].iloc[-1]) - mt) / sdt if sdt else np.nan
        zc = abs(float(ch[p].iloc[-1]) - mc) / sdc if sdc else np.nan
        z = float(np.nanmin([zt, zc]))
        rows.append(dict(
            pair=p, date=str(t.date()), state=st,
            activity=(a.iloc[-1] if pd.notna(a.iloc[-1]) else ''),
            days_in_state=int(run),
            changed=chg, change_date=str(chg_date.date()) if chg != '' else '',
            change_weekday=chg_date.strftime('%A') if chg != '' else '',
            changed_from=chg_from, prev_run=int(chg_prev_run),
            pending_state=pend_state, pending_days=int(pend_days),
            dwell_needed=DWELL,
            firmness_sd=z, firmness_word=firm_word(z),
            trend_dist_sd=zt, chop_dist_sd=zc,
            lower_confidence=bool(st in ('trend-in-range', 'neither'))))
    T = pd.DataFrame(rows)
    # shared bet: same state today AND sharing a currency leg
    sh, shc = [], []
    for _, r in T.iterrows():
        legs = {r.pair[:3], r.pair[3:]}
        n = [q for q in states_today
             if q != r.pair and states_today[q] == r.state
             and ({q[:3], q[3:]} & legs)]
        cc = {}
        for q in n:
            for c in ({q[:3], q[3:]} & legs):
                cc[c] = cc.get(c, 0) + 1
        top = max(cc, key=cc.get) if cc else ''
        sh.append(len(n))
        shc.append(top)
    T['shared_same_state_same_ccy'] = sh
    T['shared_top_currency'] = shc
    T['shared_top_count'] = [sum(1 for q in states_today
                                 if q != r.pair
                                 and states_today[q] == r.state
                                 and c in (q[:3], q[3:]))
                             if c else 0
                             for (_, r), c in zip(T.iterrows(), shc)]
    T = T.sort_values(['changed', 'firmness_sd'],
                      ascending=[False, True]).reset_index(drop=True)
    T.to_csv(os.path.join(ROOTOUT, 'today_pairs.csv'), index=False)

    # ---------------- HEADER ----------------
    vc = pd.Series(states_today).value_counts()
    dom, dom_n = vc.index[0], int(vc.iloc[0])
    mv, mv_word, mv_pct = np.nan, 'unavailable', np.nan
    try:
        s = pd.read_csv(EXT, index_col=0, parse_dates=True)['^MOVE'].dropna()
        s = s[s.index <= t]
        mv = float(s.iloc[-1])
        ref = s[s.index < SPLIT]
        q = ref.quantile([1 / 3, 2 / 3])
        mv_word = ('high' if mv > q.loc[2 / 3] else
                   'low' if mv <= q.loc[1 / 3] else 'middling')
        mv_pct = float((ref <= mv).mean())
    except Exception as e:
        print('  MOVE unavailable: %s' % str(e)[:50])
    acute = bool(cm.reindex(px.index).fillna(False).loc[t])
    H = pd.DataFrame([dict(
        date=str(t.date()), pairs=len(states_today),
        dominant_state=dom, dominant_count=dom_n,
        dominant_share=dom_n / len(states_today),
        n_changed_5d=int((T.changed != '').sum()),
        n_pending=int((T.pending_state != '').sum()),
        n_lower_confidence=int(T.lower_confidence.sum()),
        move_level=mv, move_word=mv_word, move_pctile_is=mv_pct,
        acute_crisis_window=acute, crisis_calendar_events=n_ev,
        **{'n_' + s.replace('-', '_'): int(vc.get(s, 0)) for s in CELLS})])
    H.to_csv(os.path.join(ROOTOUT, 'today_header.csv'), index=False)

    print('\n  HEADER  %s' % t.date())
    print('    dominant state: %s, %d of %d pairs (%.0f%%)'
          % (dom, dom_n, len(states_today), 100 * dom_n / len(states_today)))
    print('    MOVE %.1f -- %s (%.0f%% of in-sample days were below it)'
          % (mv, mv_word, 100 * mv_pct) if np.isfinite(mv) else
          '    MOVE unavailable')
    print('    acute crisis window today: %s' % ('YES' if acute else 'no'))
    print('    changed in last %d days: %d | pending: %d | lower-confidence: %d'
          % (LOOKBACK, int((T.changed != '').sum()),
             int((T.pending_state != '').sum()), int(T.lower_confidence.sum())))
    print('\n  %-8s %-15s %-8s %5s %9s %-10s %s'
          % ('pair', 'state', 'activity', 'days', 'firm', 'pending', 'changed'))
    for _, r in T.head(10).iterrows():
        print('  %-8s %-15s %-8s %5d %9s %-10s %s'
              % (r.pair, r.state, r.activity, r.days_in_state, r.firmness_word,
                 ('%d/%d %s' % (r.pending_days, DWELL, r.pending_state))
                 if r.pending_state else '-',
                 ('%s on %s' % (r.changed, r.change_weekday)) if r.changed
                 else 'no change'))

    hdr(os.path.join(ROOTOUT, 'today_pairs.csv'),
        'Today -- one row per pair, everything the product view shows',
        'Computed here and committed, never in the interface. Every state label\n'
        'comes from the shipped path and the run ASSERTS it reproduces\n'
        'states_g4_twoscore4.csv exactly.\n\n'
        'PENDING. The classifier needs %d consecutive days before adopting a new\n'
        'state, so the pre-dwell label is already pointing somewhere new while\n'
        'the confirmed label still shows the old one. pending_days/pending_state\n'
        'expose that, so a switch is visible while it is forming rather than\n'
        'appearing from nowhere.\n\n'
        'FIRMNESS. Each score is cut at its in-sample median; firmness is the\n'
        'distance from that cut in in-sample standard deviations. The state is\n'
        'set by BOTH scores, so the reported figure is the SMALLER of the two --\n'
        'a call is only as firm as its weakest side. >= %.2f sd solidly,\n'
        '>= %.2f clearly, below that barely. Barely is not wrong; it is near the\n'
        'boundary.\n\n'
        'SHARED BET. Other pairs in the same state today that share a currency.\n'
        '28 labels are not 28 independent observations.\n\n'
        'DAYS_IN_STATE IS A FACT, NOT A WARNING. State age was tested and does\n'
        'not predict state death, so nothing here treats a long run as overdue.'
        % (DWELL, FIRM_SOLID, FIRM_CLEAR))
    hdr(os.path.join(ROOTOUT, 'today_header.csv'),
        'Today -- the market-wide header',
        'Breadth is how many of the 28 pairs share the dominant state. The floor\n'
        'is 7, not 1: four states over 28 pairs means the largest group cannot\n'
        'be smaller than ceil(28/4). A median day sits near 11.\n\n'
        'MOVE is the bond-volatility index, the ONE external driver of six that\n'
        'survived testing. It is a witness on the present, not a forecast: it\n'
        'reads about 0.9 sd higher on crisis days in every sub-period, and every\n'
        'attempt to make it predict failed.\n\n'
        'acute_crisis_window is whether today falls inside a forward-only window\n'
        'from a news-dated event in the %d-event calendar. The window opens ON\n'
        'the event date and never before it.' % n_ev)
    print('\nwrote today_pairs.csv, today_header.csv + .txt')
    return T, H


if __name__ == '__main__':
    main()
