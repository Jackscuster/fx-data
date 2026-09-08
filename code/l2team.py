import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""THE TRADING TEAM — greedy add-one / drop-one on the costed gate 3 passers.

SIZING. A team is scored at the size where its risk budget is exactly spent.
Two budgets bind and the tighter one wins:
    DIP95        the 95th percentile worst peak-to-trough dip
    worst day    the single worst day
scale = min(dip_budget / DIP95_unit, day_budget / worst_day_unit).

DIP95, AND WHY THE DAYS ARE GLUED. Each day's trades are summed into one daily
number FIRST, then the ORDER OF DAYS is shuffled 10,000 times. Shuffling
individual trades would break the fact that several members can lose together on
the same day, which is exactly the risk a team has and a single strategy does
not. The dip is the worst peak-to-trough of each shuffled equity path; DIP95 is
the 95th percentile of those 10,000 worst dips.

SCORE IS THE MEDIAN YEAR, not the mean. A team carried by one extraordinary year
is not a team that can be traded; the median asks what a NORMAL year looks like.
Mean, worst year, best year and worst day are all reported beside it.

R -> PERCENT. Sizing is fixed-R at 1% of equity per trade, so 1R = 1%.
"""
import glob, json, time, argparse
import datetime as dt
import numpy as np, pandas as pd

import l2crisis as C
import l2deliver as DL
import l2trades as TR
import l2sweep as S

N_SHUF = 10000
SEED = 20260909
R_PCT = 1.0                      # 1R = 1% of equity


def worst_dip(daily, order):
    eq = np.cumsum(daily[order])
    return float(np.max(np.maximum.accumulate(eq) - eq))


def dip95(daily, n_shuf=N_SHUF, rng=None):
    """95th percentile worst peak-to-trough dip over shuffled day ORDER."""
    rng = rng or np.random.default_rng(SEED)
    n = len(daily)
    if n < 3:
        return 0.0
    out = np.empty(n_shuf)
    idx = np.arange(n)
    for i in range(n_shuf):
        rng.shuffle(idx)
        eq = np.cumsum(daily[idx])
        out[i] = np.max(np.maximum.accumulate(eq) - eq)
    return float(np.percentile(out, 95))


def team_daily(M, weights):
    """M: days x members matrix of daily R. Equal weight per member, votes
    scaled by `weights` (1.0 full, 0.5 half). Same pair held by several members
    is NOT merged -- the exposures simply add, as they would in the account."""
    w = np.asarray(weights, float)
    if w.sum() <= 0:
        return np.zeros(M.shape[0])
    return (M * w).sum(axis=1) / w.sum()


def score_team(M, weights, years, dip_budget, day_budget, rng):
    d = team_daily(M, weights) * R_PCT
    if not np.any(d):
        return None
    D = dip95(d, rng=rng)
    wd = float(-d.min()) if d.min() < 0 else 1e-9
    s_dip = dip_budget / D if D > 0 else np.inf
    s_day = day_budget / wd if wd > 0 else np.inf
    scale = float(min(s_dip, s_day))
    yr = pd.Series(d * scale).groupby(years).sum()
    return dict(score=float(yr.median()), mean_year=float(yr.mean()),
                worst_year=float(yr.min()), best_year=float(yr.max()),
                n_years=int(len(yr)), dip95=float(D * scale),
                worst_day=float(wd * scale), scale=scale,
                binds='DIP95' if s_dip <= s_day else 'worst day')


def load_candidates():
    """Every costed-cut passer: official settings plus ALTERNATE versions."""
    f = os.path.join(ROOTOUT, 'gate3_costed_verdicts.csv')
    if not os.path.exists(f):
        f = os.path.join(ROOTOUT, 'gate3_verdicts.csv')
    V = pd.read_csv(f, low_memory=False)
    P = V[V.verdict.isin(['PASS', 'SELECTIVE'])].copy()
    P['variant'] = 'OFFICIAL'
    alt = os.path.join(ROOTOUT, 'gate3_alternates_verdicts.csv')
    if os.path.exists(alt):
        A = pd.read_csv(alt, low_memory=False)
        A = A[A.verdict.isin(['PASS', 'SELECTIVE'])].copy()
        A['variant'] = 'ALTERNATE'
        P = pd.concat([P, A], ignore_index=True)
    P['key'] = P.sid                      # official and alternate share a key
    P['cand'] = P.sid + '::' + P.variant
    return P.reset_index(drop=True)


def _equity_series(cfg, wins):
    """CLOSE-TO-CLOSE CHANGE IN EQUITY, every open position marked to that day's
    close. This is what the prop limits actually measure: floating open losses
    count toward both the daily and the trailing limit, and open equity is
    logged at each daily close.

    Booking a trade's whole R on its exit date -- what this used to do -- hides
    every floating loss. A position open three weeks and closing badly showed
    one bad day instead of fifteen deteriorating ones, so DIP95 measured
    REALISED drawdown and sized the team against a number the account would
    never see.

    Costs stay charged at entry, as the engine charges them.
    """
    code = dict((s, c) for s, _, c in S.SLICES)[cfg['slice']]
    daily = {}
    for p in S.all_pairs():
        try:
            r = TR.run_pair(cfg, p)
        except Exception:
            continue
        d, tr, cl = r['dates'], r['trades'], r['c']
        if len(tr['r']) == 0:
            continue
        reg = S.regime_codes(p, d)
        wb = {}
        for k, (a, z) in S.WINDOWS.items():
            w = np.flatnonzero((d >= a) & (d <= z))
            if len(w):
                wb[k] = (int(w[0]), int(w[-1]) + 1)
        for j in range(len(tr['r'])):
            eb, xb = int(tr['entry_bar'][j]), int(tr['exit_bar'][j])
            if xb < 0 or reg[eb] != code:
                continue
            if not any(wb.get(k) and wb[k][0] <= eb < wb[k][1] for k in ('W2', 'W3')):
                continue
            ent = float(tr['entry_px'][j]); u = float(tr['units'][j])
            sgn = float(tr['dir'][j]); tot = float(tr['r'][j])
            # mark to market each day; the LAST day carries the realised total so
            # costs and the actual fill price are respected exactly
            prev = 0.0
            for b in range(eb, xb + 1):
                if b == xb:
                    cum = tot
                else:
                    cum = sgn * (cl[b] - ent) * u / S.RISK
                daily[d[b]] = daily.get(d[b], 0.0) + (cum - prev)
                prev = cum
    return pd.Series(daily).sort_index() if daily else pd.Series(dtype=float)


def build_matrix(cands, mode='equity'):
    """days x candidates of daily R.

    mode='equity'  close-to-close change with open positions marked to market
    mode='closed'  the old behaviour: each trade booked on its exit date
    Both are built; the equity one drives sizing, the closed one is reported
    beside it so the gap is visible.
    """
    wins = C.windows()
    series = {}
    for r in cands.to_dict('records'):
        if mode == 'closed':
            T = DL.blind_trades(r, wins)
            if not len(T):
                continue
            s = T.groupby(pd.to_datetime(T.exit).dt.normalize()).R.sum()
        else:
            s = _equity_series(r, wins)
            if not len(s):
                continue
        series[r['cand']] = s
    if not series:
        return None, []
    M = pd.DataFrame(series).fillna(0.0).sort_index()
    return M, list(M.columns)


def greedy(M, cols, core, dip_budget, day_budget, log, tag, rng):
    years = M.index.year.values
    A = M.values
    idx = {c: i for i, c in enumerate(cols)}
    team = list(core)
    votes = {c: 1.0 for c in team}

    def sc(members, vd):
        w = np.zeros(len(cols))
        for c in members:
            w[idx[c]] = vd[c]
        return score_team(A, w, years, dip_budget, day_budget, rng)

    cur = sc(team, votes)
    log.append(dict(team=tag, step='core', candidate='', vote='', kept=True,
                    score=None if cur is None else cur['score'],
                    members=len(team)))
    tried = 0
    # ---- ADD-ONE
    while True:
        best, bestc, bestv = cur, None, None
        keys = {c.split('::')[0] for c in team}
        for c in cols:
            if c in team or c.split('::')[0] in keys:
                continue          # at most one variant of a strategy on a team
            for v in (1.0, 0.5):
                tried += 1
                vd = dict(votes); vd[c] = v
                s = sc(team + [c], vd)
                keep = s is not None and (best is None or s['score'] > best['score'])
                log.append(dict(team=tag, step='add', candidate=c, vote=v,
                                kept=False, score=None if s is None else s['score'],
                                members=len(team) + 1))
                if keep:
                    best, bestc, bestv = s, c, v
        if bestc is None:
            break
        team.append(bestc); votes[bestc] = bestv; cur = best
        log.append(dict(team=tag, step='ADDED', candidate=bestc, vote=bestv,
                        kept=True, score=cur['score'], members=len(team)))
    # ---- DROP-ONE
    while len(team) > 1:
        best, bestc = cur, None
        for c in list(team):
            tried += 1
            vd = {k: v for k, v in votes.items() if k != c}
            s = sc([x for x in team if x != c], vd)
            log.append(dict(team=tag, step='drop', candidate=c, vote=votes[c],
                            kept=False, score=None if s is None else s['score'],
                            members=len(team) - 1))
            if s is not None and s['score'] > best['score']:
                best, bestc = s, c
        if bestc is None:
            break
        team.remove(bestc); votes.pop(bestc); cur = best
        log.append(dict(team=tag, step='DROPPED', candidate=bestc, vote='',
                        kept=True, score=cur['score'], members=len(team)))
    return team, votes, cur, tried


def main():
    t0 = time.time()
    rng = np.random.default_rng(SEED)
    cands = load_candidates()
    print('candidates (passers incl. alternates): %d' % len(cands), flush=True)
    M, cols = build_matrix(cands, mode='equity')
    if M is None:
        raise SystemExit('no candidate return series')
    Mc, cols_c = build_matrix(cands, mode='closed')   # reported, never sizes
    print('return matrix: %d days x %d candidates' % M.shape, flush=True)
    # timing probe on one scoring call
    tp = time.time()
    years = M.index.year.values
    w = np.ones(len(cols))
    score_team(M.values, w, years, 3.6, 3.6, rng)
    per = time.time() - tp
    print('one team evaluation: %.2f s  (10,000 shuffles)' % per, flush=True)
    print('estimated: ~%d trials/round x 2 teams -> roughly %.1f h'
          % (2 * len(cols), 2 * (2 * len(cols) * 4) * per / 3600.0), flush=True)

    # NO SEED. The team starts EMPTY and its first member is whichever passer
    # scores best alone at the budget. Seeding with the graft-15 would have
    # imported a roster chosen by the co-equal rule on CONTAMINATED numbers --
    # W2 scored with ip2 -- and greedy search cannot leave a seed it was handed,
    # so a bad seed survives to the final roster however good the alternatives.
    # No cap on size: add-one runs until nothing improves.
    years0 = M.index.year.values
    idx0 = {c: i for i, c in enumerate(cols)}

    def solo(c, dipb, dayb):
        w = np.zeros(len(cols)); w[idx0[c]] = 1.0
        return score_team(M.values, w, years0, dipb, dayb, rng)

    print('no seed: choosing the best single passer at each budget', flush=True)

    log = []
    out = {}
    for tag, dipb, dayb in (('team1', 3.6, 3.6), ('team2', 5.4, 3.6)):
        # first member = best score standing alone at THIS budget, so the two
        # teams may legitimately start from different strategies
        best_solo, best_c = None, None
        for c in cols:
            s1 = solo(c, dipb, dayb)
            log.append(dict(team=tag, step='solo', candidate=c, vote=1.0,
                            kept=False, score=None if s1 is None else s1['score'],
                            members=1))
            if s1 is not None and (best_solo is None or s1['score'] > best_solo['score']):
                best_solo, best_c = s1, c
        if best_c is None:
            print('%s: no scoreable candidate' % tag, flush=True); continue
        print('%s seed: %s alone scores %.2f%%' % (tag, best_c, best_solo['score']), flush=True)
        core = [best_c]
        team, votes, res, tried = greedy(M.values, cols, core, dipb, dayb, log, tag, rng)
        # the same roster and votes, measured on CLOSED trades, for comparison
        dip_closed = None
        try:
            common = [c for c in team if c in cols_c]
            if common:
                wv = np.zeros(len(cols_c))
                for c in common:
                    wv[cols_c.index(c)] = votes[c]
                dc = team_daily(Mc.values, wv) * R_PCT
                dip_closed = dip95(dc, rng=np.random.default_rng(SEED)) * res['scale']
        except Exception:
            pass
        out[tag] = dict(members=team, votes=votes, res=res, tried=tried,
                        dip_budget=dipb, day_budget=dayb, dip95_closed=dip_closed)
        print('%s: %d members, score %.2f%%, tried %d' % (tag, len(team), res['score'], tried), flush=True)
        rows = []
        for c in team:
            sid, var = c.split('::')
            r = cands[cands.cand == c].iloc[0].to_dict()
            rows.append(dict(sid=sid, variant=var, vote=votes[c],
                             c1=r.get('c1'), c2=r.get('c2'), vol=r.get('vol'),
                             base=r.get('base'), slice=r.get('slice'),
                             src=r.get('src_label'),
                             sharpe_only_flag=r.get('sharpe_only_flag'),
                             profit_concentration=r.get('profit_concentration')))
        pd.DataFrame(rows).to_csv(os.path.join(ROOTOUT, '%s_roster.csv' % tag), index=False)
        # redundancy
        sub = M[team]
        Cm = sub[(sub != 0).any(axis=1)].corr()
        hot = [(a, b, round(float(Cm.loc[a, b]), 3))
               for i, a in enumerate(team) for b in team[i + 1:]
               if abs(Cm.loc[a, b]) > 0.90]
        out[tag]['corr_above_090'] = hot
        Cm.round(4).to_csv(os.path.join(ROOTOUT, '%s_corr.csv' % tag))
    pd.DataFrame(log).to_csv(os.path.join(ROOTOUT, 'team_build_log.csv'), index=False)

    L = ['# Trading teams — built from the costed gate 3 cut\n',
         'Sizing uses the EQUITY series: close-to-close change with every open',
         'position marked to that day\'s close. Floating open losses count toward',
         'both the daily and the trailing prop limit, so realised-only accounting',
         'would size the team against a drawdown the account never sees. The',
         'closed-trade DIP95 is reported beside it so the gap is visible.\n',
         '**Intraday lows are invisible in close-only data.** Every figure here is',
         'a close-to-close number, so the true worst moment inside a day is worse',
         'than anything below. The live limit needs margin on top of the 3.6%',
         'budget; 3.6% is not a level to trade right up to.\n']
    for tag in ('team1', 'team2'):
        o = out[tag]; r = o['res']
        L.append('## %s (DIP95 budget %.1f%%, worst-day budget %.1f%%)\n'
                 % (tag.upper(), o['dip_budget'], o['day_budget']))
        L.append('| metric | value |\n|---|---|')
        L.append('| score (median year) | **%.2f%%** |' % r['score'])
        L.append('| average year | %.2f%% |' % r['mean_year'])
        L.append('| worst year | %.2f%% |' % r['worst_year'])
        L.append('| best year | %.2f%% |' % r['best_year'])
        L.append('| DIP95 | %.2f%% |' % r['dip95'])
        L.append('| worst day | %.2f%% |' % r['worst_day'])
        L.append('| binding budget | %s |' % r['binds'])
        L.append('| members | %d |' % len(o['members']))
        L.append('| scale factor | %.3f |' % r['scale'])
        L.append('| candidates tried | %d |' % o['tried'])
        cd = o.get('dip95_closed')
        if cd is not None:
            L.append('| DIP95 on CLOSED trades (not used for sizing) | %.2f%% |' % cd)
            L.append('| gap, equity vs closed | **%+.2f%%** |' % (r['dip95'] - cd))
        L.append('| pairs correlated > 0.90 | %d |\n' % len(o['corr_above_090']))
    open(os.path.join(ROOTOUT, 'team_summary.md'), 'w').write('\n'.join(L) + '\n')
    json.dump({k: dict(members=v['members'], votes=v['votes'], **v['res'],
                       tried=v['tried'], corr_above_090=v['corr_above_090'])
               for k, v in out.items()},
              open(os.path.join(ROOTOUT, 'team_index.json'), 'w'), indent=1)
    print('\nDONE in %.1f min' % ((time.time() - t0) / 60.0), flush=True)


if __name__ == '__main__':
    main()
