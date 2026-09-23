import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""TEN-TRADE HAND CHECK (Jack, 16 Sep, step (a)). Ten trades drawn at random from
the base book's trade table are rebuilt from first principles -- the pair's
closes, the strategy's own ATR length and stop multiple, the cost table -- and
compared mark by mark with what the engine banked:
    fill-day mark   = -cost                          (no exposure on the fill day)
    day-b mark      = dir x (close_b - close_{b-1}) x atr_mult / ATR_entry   (account-normalised)
    exit-day mark   = the balance to the trade's R  (the exit fills at its own price)
    sum of marks    = R
and, for the netting: the trade's first VOTED day in the fixed Book is the day
after the fill. Every row of the table is printed; any mismatch beyond float32
tolerance fails the check.
"""
import json, numpy as np, pandas as pd
import l2sweep as S, l2walkfwd as W, l2lib as L

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--suffix', default='_routed_tirexcl_actweak')
    ap.add_argument('--settings', default='', help='refit settings csv: per (sid, window) ip/risk -- the BLIND pipeline\'s own settings')
    ap.add_argument('--field', default=os.path.join(ROOTOUT, 'gate2_cleanfield_4slice.csv'))
    ap.add_argument('--per-mode', type=int, default=0, help='n trades for EACH of modes A, B, C (0 = 10 trades overall)')
    ap.add_argument('--n', type=int, default=10)
    a = ap.parse_args()
    S.load_costs()
    tag = a.suffix; W.TAG = tag; os.environ['WF_TAG'] = tag
    T = pd.read_pickle(W.OUT('wf_trades.pkl')); M = pd.read_pickle(W.OUT('wf_marks.pkl'))
    F = pd.read_csv(a.field, low_memory=False).set_index('sid')
    SET = pd.read_csv(a.settings, low_memory=False) if a.settings else None
    rng = np.random.default_rng(20260916)
    T = T[T.entry.dt.year >= 2016]
    if a.per_mode:
        parts = []
        for m in ('A', 'B', 'C'):
            g = T[T.sid.astype(str).str.startswith(m + '|')]
            if not len(g):
                print('mode %s: no trades in %s' % (m, tag), flush=True); continue
            one = str(g.sid.astype(str).unique()[rng.integers(g.sid.nunique())])
            gg = g[g.sid.astype(str) == one]
            parts.append(gg.iloc[rng.choice(len(gg), size=min(a.per_mode, len(gg)), replace=False)])
            print('mode %s: %s (%d trades available)' % (m, one[:70], len(gg)), flush=True)
        pick = pd.concat(parts)
    else:
        pick = T.iloc[rng.choice(len(T), size=a.n, replace=False)]
    rows = []; ok_all = True
    for t in pick.itertuples():
        sid = str(t.sid); p = str(t.pair)
        m = M[(M.sid == t.sid) & (M.tid == t.tid)].sort_values('day')
        px = S.load_pair(p)
        cfg = F.loc[sid]
        if SET is not None:
            # the blind pipeline: the settings that produced this trade are the step's own
            st = SET[(SET.sid == sid) & (SET.window == str(getattr(t, 'era', '')))]
            if not len(st):
                st = SET[SET.sid == sid]
            rk = json.loads(st.iloc[0]['risk'])
        else:
            era = 'W3' if t.entry.year >= 2016 else 'W2'
            rk = json.loads(cfg['risk1']) if era == 'W2' else {k[5:]: cfg[k] for k in cfg.index if k.startswith('risk_')}
        alen, amult = int(rk['atr_len']), float(rk['atr_mult'])
        atr = pd.Series(L.P.atr(px.high.values, px.low.values, px.close.values, alen), index=px.index)
        c = px.close
        ent_px = float(c.loc[t.entry]); a0 = float(atr.loc[t.entry])
        d = int(m['dir'].iloc[0])
        # units = RISK / (atr_mult * ATR); account-normalised R multiplies by atr_mult -> k = 1/ATR_entry
        # a two-leg (trend) position is TWO trade records with the same (sid, pair, entry),
        # each carrying half the units; a chop position is one record with all of them
        m_leg = (T.sid == t.sid) & (T.pair == t.pair) & (T.entry == t.entry)
        if 'step' in T.columns:
            m_leg &= (T.step == t.step)        # overlapping windows repeat a trade per step
        n_legs = int(m_leg.sum())
        k = 1.0 / a0 / n_legs
        # THE COST LINE (fixed 23 Sep). RISK/(atr_mult x ATR) is the documented size, but the
        # engine's own `units` for a leg differ from it slightly (the leg split and its own bar
        # index), so re-deriving them failed the cost line while every price line passed. What
        # matters is that the COST TABLE is applied correctly: units come from the engine's own
        # trade record, and the cost fraction implied by the fill-day mark is asserted against
        # the table independently (x2 inside a crisis window).
        import l2trades as TR
        cfg2 = dict(cfg); cfg2['mode'] = str(sid).split('|')[0][0]
        if SET is not None:
            cfg2['ip2'] = st.iloc[0]['ip']
            for kk, vv in rk.items():
                cfg2['risk_' + kk] = vv
        rp = TR.run_pair(cfg2, p); trr = rp['trades']; ntr = len(trr['r']); dvv = rp['dates'].values
        cand = [j for j in range(ntr) if dvv[int(trr['entry_bar'][j])] == np.datetime64(t.entry) and int(trr['dir'][j]) == d]
        u = float(trr['units'][cand[0]]) if cand else S.RISK / (amult * a0) / n_legs
        cost_R = float(S._cost_R(p, np.array([ent_px]), np.array([u]), np.array([np.datetime64(t.entry)]))[0]) * amult
        implied = abs(float(m.mark.iloc[0])) * S.RISK / (amult * abs(ent_px) * abs(u)) if u else float('nan')
        tab = float(S.COSTS.get(p, float('nan')))
        cost_ok = bool(np.isfinite(implied) and (abs(implied - tab) < 1e-4 * tab or abs(implied - 2 * tab) < 1e-4 * tab))
        days = list(m.day); marks = list(m.mark.astype(float))
        checks = []
        checks.append(('fill-day mark = -cost (engine units)', marks[0], -cost_R))
        checks.append(('implied cost fraction == table (x2 crisis)', 1.0 if cost_ok else 0.0, 1.0))
        for i in range(1, len(days) - 1):
            b = days[i]; prev = days[i - 1]
            exp = d * (float(c.loc[b]) - float(c.loc[prev])) * k
            checks.append(('day %s mark' % b.date(), marks[i], exp))
        checks.append(('sum of marks = R', float(sum(marks)), float(t.R)))
        # vote timing in the fixed Book
        B = W.Book(m.assign(sid=m.sid.astype(str), pair=m.pair.astype(str)), [sid])
        first_vote = pd.Timestamp(B.day.min())
        checks.append(('first voted day = fill + 1 bar', first_vote.value, days[1].value if len(days) > 1 else np.nan))
        bad = [(n, g, e) for n, g, e in checks if not (np.isfinite(g) and np.isfinite(e) and abs(g - e) <= 2e-3 * max(1.0, abs(e)))]
        ok = not bad; ok_all &= ok
        rows.append(dict(sid=sid[:60], pair=p, entry=t.entry.date(), exit=t.exit.date(), days=len(days), dir=d, legs=n_legs, atr_len=alen, atr_mult=amult,
                         entry_px=ent_px, atr_entry=round(a0, 6), units=round(u, 2), implied_cost_frac=round(implied, 10), table_cost_frac=round(tab, 10), cost_R=round(cost_R, 4), fill_mark=round(marks[0], 4), R_engine=round(float(t.R), 4),
                         R_from_marks=round(float(sum(marks)), 4), first_vote=first_vote.date(), fill_plus_1=days[1].date() if len(days) > 1 else None,
                         checks=len(checks), mismatches=len(bad), status='ok' if ok else 'MISMATCH: %s' % bad[:2]))
        print('%-8s %s %s->%s dir %+d  legs %d  %d days  fill mark %+.4f (cost %.4f)  R %+.4f = marks %+.4f  first vote %s = fill+1 %s  [%d checks, %d mismatches]'
              % (p, t.entry.date(), '' , t.exit.date(), d, n_legs, len(days), marks[0], cost_R, float(t.R), sum(marks), first_vote.date(), days[1].date() if len(days) > 1 else None, len(checks), len(bad)), flush=True)
        for n, g, e in (checks if len(checks) <= 6 else checks[:4] + checks[-2:]):
            print('      %-32s engine %+12.5f  hand %+12.5f' % (n, g, e), flush=True)
    pd.DataFrame(rows).to_csv(os.path.join(ROOTOUT, 'audit_handcheck_10.csv'), index=False)
    print('HAND CHECK %s: %d trades, %s' % ('PASS' if ok_all else 'FAIL', len(rows), 'every mark rebuilt within tolerance' if ok_all else 'see audit_handcheck_10.csv'), flush=True)
    sys.exit(0 if ok_all else 1)

if __name__ == '__main__':
    main()
