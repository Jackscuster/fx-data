import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""STUDY B — CALENDAR. Day of week, holidays, and whether any member's edge
lives on particular days.

EPISODE-BASED THROUGHOUT. One trade is one observation whatever its holding
period; per-bar counting would inflate every t-statistic.

THE US HOLIDAY ASYMMETRY IS REAL AND IS HANDLED. H.10 publishes no rate on a US
holiday, so no trade can be ENTERED on one -- there is no bar. For the US the
only answerable questions are the day BEFORE and the day AFTER. Every other
country's market is open when the US is shut and vice versa, so for those the
holiday itself is reported too, restricted to pairs containing that currency.

THE NULL SHUFFLES ENTRY DATES WITHIN EACH YEAR. That holds the number of trades,
the yearly regime and the pair mix fixed while destroying any real link to the
calendar, so a surviving effect is about the day and not about which years the
strategy happened to trade.
"""
import json, time
import numpy as np, pandas as pd

import l2crisis as C
import l2deliver as DL

SPLIT = pd.Timestamp('2016-01-01')
N_NULL = 1000
SEED = 20260911
DOW = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

# ---- holiday tables. Fixed-date rules plus the movable feasts that matter.
# Built from published national calendars, not from price.
CCY_COUNTRY = {'USD': 'US', 'GBP': 'UK', 'EUR': 'EU', 'JPY': 'JP',
               'CHF': 'CH', 'CAD': 'CA', 'AUD': 'AU', 'NZD': 'NZ'}


def easter(y):
    a = y % 19; b = y // 100; c = y % 100
    d = b // 4; e = b % 4; f = (b + 8) // 25; g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4; k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mo = (h + l - 7 * m + 114) // 31
    da = ((h + l - 7 * m + 114) % 31) + 1
    return pd.Timestamp(y, mo, da)


def nth_weekday(y, mo, wd, n):
    d = pd.Timestamp(y, mo, 1)
    off = (wd - d.dayofweek) % 7
    return d + pd.Timedelta(days=off + 7 * (n - 1))


def last_weekday(y, mo, wd):
    d = pd.Timestamp(y, mo, 1) + pd.offsets.MonthEnd(0)
    return d - pd.Timedelta(days=(d.dayofweek - wd) % 7)


def holidays(y):
    """country -> [dates]. Public national holidays where the local market is
    closed. Movable feasts computed, not tabulated."""
    E = easter(y)
    gf, em = E - pd.Timedelta(days=2), E + pd.Timedelta(days=1)
    H = {
        'US': [pd.Timestamp(y, 1, 1), nth_weekday(y, 1, 0, 3), nth_weekday(y, 2, 0, 3),
               last_weekday(y, 5, 0), pd.Timestamp(y, 7, 4), nth_weekday(y, 9, 0, 1),
               nth_weekday(y, 11, 3, 4), pd.Timestamp(y, 12, 25), gf],
        'UK': [pd.Timestamp(y, 1, 1), gf, em, nth_weekday(y, 5, 0, 1),
               last_weekday(y, 5, 0), last_weekday(y, 8, 0),
               pd.Timestamp(y, 12, 25), pd.Timestamp(y, 12, 26)],
        'EU': [pd.Timestamp(y, 1, 1), gf, em, pd.Timestamp(y, 5, 1),
               pd.Timestamp(y, 12, 25), pd.Timestamp(y, 12, 26)],
        'JP': [pd.Timestamp(y, 1, 1), pd.Timestamp(y, 1, 2), pd.Timestamp(y, 1, 3),
               nth_weekday(y, 1, 0, 2), pd.Timestamp(y, 2, 11), pd.Timestamp(y, 4, 29),
               pd.Timestamp(y, 5, 3), pd.Timestamp(y, 5, 4), pd.Timestamp(y, 5, 5),
               nth_weekday(y, 7, 0, 3), nth_weekday(y, 9, 0, 3),
               nth_weekday(y, 10, 0, 2), pd.Timestamp(y, 11, 3),
               pd.Timestamp(y, 11, 23)],
        'CH': [pd.Timestamp(y, 1, 1), pd.Timestamp(y, 1, 2), gf, em,
               E + pd.Timedelta(days=39), E + pd.Timedelta(days=50),
               pd.Timestamp(y, 8, 1), pd.Timestamp(y, 12, 25), pd.Timestamp(y, 12, 26)],
        'CA': [pd.Timestamp(y, 1, 1), gf, last_weekday(y, 5, 0) - pd.Timedelta(days=7),
               pd.Timestamp(y, 7, 1), nth_weekday(y, 9, 0, 1),
               nth_weekday(y, 10, 0, 2), pd.Timestamp(y, 12, 25), pd.Timestamp(y, 12, 26)],
        'AU': [pd.Timestamp(y, 1, 1), pd.Timestamp(y, 1, 26), gf, em,
               pd.Timestamp(y, 4, 25), pd.Timestamp(y, 12, 25), pd.Timestamp(y, 12, 26)],
        'NZ': [pd.Timestamp(y, 1, 1), pd.Timestamp(y, 1, 2), pd.Timestamp(y, 2, 6),
               gf, em, pd.Timestamp(y, 4, 25), pd.Timestamp(y, 12, 25),
               pd.Timestamp(y, 12, 26)],
    }
    return H


def holiday_table(y0=1999, y1=2026):
    rows = []
    for y in range(y0, y1 + 1):
        for cc, ds in holidays(y).items():
            for d in ds:
                rows.append((cc, pd.Timestamp(d).normalize()))
    T = pd.DataFrame(rows, columns=['country', 'date']).drop_duplicates()
    T.to_csv(os.path.join(ROOTOUT, 'holiday_table.csv'), index=False)
    return T


def graft_trades():
    G = pd.read_csv(os.path.join(ROOTOUT, 'gate2_combined_AB_leaderboard.csv'),
                    low_memory=False).sort_values('rank').head(15)
    wins = C.windows()
    out = []
    for i, cfg in enumerate(G.to_dict('records'), 1):
        T = DL.blind_trades(cfg, wins)
        if not len(T):
            continue
        T['member'] = 'g%02d' % i
        T['recipe'] = '%s x %s x %s x %s' % (cfg['c1'], cfg['c2'], cfg['vol'], cfg['base'])
        out.append(T)
    A = pd.concat(out, ignore_index=True)
    A['entry'] = pd.to_datetime(A.entry); A['exit'] = pd.to_datetime(A.exit)
    A['dow_in'] = A.entry.dt.dayofweek
    A['dow_out'] = A.exit.dt.dayofweek
    A['held_weekend'] = (A.exit - A.entry).dt.days >= (4 - A.entry.dt.dayofweek).clip(lower=0) + 1
    A['period'] = np.where(A.entry < SPLIT, 'IS', 'OOS')
    return A


def block(g):
    if not len(g):
        return dict(trades=0, hit_rate_pct=np.nan, r_per_unit=np.nan, worst_dip_R=np.nan)
    eq = g.sort_values('exit').R.cumsum()
    return dict(trades=len(g), hit_rate_pct=round(100.0 * float((g.R > 0).mean()), 1),
                r_per_unit=round(float(g.R.mean()), 4),
                worst_dip_R=round(float((eq.cummax() - eq).max()), 3))


def dow_study(A):
    rows = []
    for per in ('IS', 'OOS'):
        P = A[A.period == per]
        for d in range(5):
            r = block(P[P.dow_in == d]); r.update(dim='entry_dow', bucket=DOW[d], period=per)
            rows.append(r)
            r = block(P[P.dow_out == d]); r.update(dim='exit_dow', bucket=DOW[d], period=per)
            rows.append(r)
        for lab, m in (('held_weekend', P.held_weekend), ('no_weekend', ~P.held_weekend)):
            r = block(P[m]); r.update(dim='weekend', bucket=lab, period=per)
            rows.append(r)
    return pd.DataFrame(rows)


def holiday_study(A, HT):
    rows = []
    hol = {cc: set(g.date) for cc, g in HT.groupby('country')}
    for ccy, cc in CCY_COUNTRY.items():
        H = hol.get(cc, set())
        if not H:
            continue
        sub = A[A.pair.str.contains(ccy)]
        if not len(sub):
            continue
        before = {d - pd.Timedelta(days=1) for d in H}
        after = {d + pd.Timedelta(days=1) for d in H}
        cases = [('day_before', before), ('day_after', after)]
        if cc != 'US':
            # H.10 has no bar on a US holiday, so 'on the day' is unanswerable
            # for the US and is reported only for the others.
            cases.insert(1, ('on_holiday', H))
        for per in ('IS', 'OOS'):
            P = sub[sub.period == per]
            normal = P[~P.entry.dt.normalize().isin(H | before | after)]
            nb = block(normal); nb.update(country=cc, ccy=ccy, window='normal_days', period=per)
            rows.append(nb)
            for lab, S_ in cases:
                g = P[P.entry.dt.normalize().isin(S_)]
                r = block(g)
                r.update(country=cc, ccy=ccy, window=lab, period=per,
                         vs_normal_r=(round(r['r_per_unit'] - nb['r_per_unit'], 4)
                                      if r['trades'] and nb['trades'] else np.nan))
                rows.append(r)
    return pd.DataFrame(rows)


def member_study(A, HT, rng):
    """Per member by weekday, with a within-year entry-date shuffle null."""
    hol = {cc: set(g.date) for cc, g in HT.groupby('country')}
    allhol = set().union(*hol.values()) if hol else set()
    rows = []
    for m, g in A.groupby('member'):
        for per in ('IS', 'OOS'):
            P = g[g.period == per]
            if not len(P):
                continue
            base = block(P); base.update(member=m, period=per, dim='all', bucket='all')
            rows.append(base)
            for d in range(5):
                r = block(P[P.dow_in == d])
                r.update(member=m, period=per, dim='entry_dow', bucket=DOW[d],
                         vs_all_r=(round(r['r_per_unit'] - base['r_per_unit'], 4)
                                   if r['trades'] else np.nan))
                rows.append(r)
            nearhol = P[P.entry.dt.normalize().isin(
                allhol | {d - pd.Timedelta(days=1) for d in allhol}
                | {d + pd.Timedelta(days=1) for d in allhol})]
            r = block(nearhol); r.update(member=m, period=per, dim='holiday_window',
                                         bucket='any', vs_all_r=(
                round(r['r_per_unit'] - base['r_per_unit'], 4) if r['trades'] else np.nan))
            rows.append(r)
    M = pd.DataFrame(rows)
    # NULL: shuffle entry dates within each year, per member
    real, null = {}, {}
    for m, g in A.groupby('member'):
        sp = g.groupby(g.dow_in).R.mean()
        real[m] = float(sp.max() - sp.min()) if len(sp) > 1 else np.nan
        nn = np.empty(N_NULL)
        yrs = g.entry.dt.year.values
        dows = g.dow_in.values
        for i in range(N_NULL):
            sh = np.empty_like(dows)
            for y in np.unique(yrs):
                k = yrs == y
                sh[k] = rng.permutation(dows[k])
            s2 = pd.Series(g.R.values).groupby(sh).mean()
            nn[i] = float(s2.max() - s2.min()) if len(s2) > 1 else np.nan
        null[m] = dict(null_mean=float(np.nanmean(nn)),
                       p_value=round(float(np.nanmean(nn >= real[m])), 4))
    M['dow_spread_real'] = M.member.map(real)
    M['dow_spread_null_mean'] = M.member.map({k: v['null_mean'] for k, v in null.items()})
    M['dow_spread_p'] = M.member.map({k: v['p_value'] for k, v in null.items()})
    return M


def main():
    t0 = time.time()
    rng = np.random.default_rng(SEED)
    HT = holiday_table()
    A = graft_trades()
    print('graft trades: %d across %d members' % (len(A), A.member.nunique()), flush=True)
    D = dow_study(A); D.to_csv(os.path.join(ROOTOUT, 'calendar_dow.csv'), index=False)
    H = holiday_study(A, HT); H.to_csv(os.path.join(ROOTOUT, 'calendar_holidays.csv'), index=False)
    M = member_study(A, HT, rng); M.to_csv(os.path.join(ROOTOUT, 'calendar_by_member.csv'), index=False)

    L = ['# Calendar study — graft 15, cost-charged, episode-based\n',
         'One trade is one observation whatever its holding period.\n',
         '**H.10 publishes no rate on a US holiday**, so no trade can be entered on',
         'one and only the day before and the day after are answerable for the US.',
         'Other countries trade while the US is shut, so the holiday itself is',
         'reported for them, restricted to pairs holding that currency.\n']
    worst = D[(D.dim == 'entry_dow')].sort_values('r_per_unit')
    if len(worst):
        L.append('## Day of week\n')
        L.append('| period | day | trades | hit % | R/unit |')
        L.append('|---|---|---|---|---|')
        for r in D[D.dim == 'entry_dow'].to_dict('records'):
            L.append('| %s | %s | %d | %s | %s |' % (r['period'], r['bucket'], r['trades'],
                     r['hit_rate_pct'], r['r_per_unit']))
    sig = M[(M.dim == 'all') & (M.dow_spread_p < 0.05)]
    L.append('\n## Verdict\n')
    L.append('Members whose weekday spread beats a within-year date shuffle at p<0.05: '
             '**%d of %d**. %s\n' % (sig.member.nunique(), M.member.nunique(),
             'Named: ' + ', '.join(sorted(set(sig.member))) if len(sig) else
             'None — no member\'s edge is concentrated on a weekday beyond chance, so '
             'switching days off would cost trades and buy nothing.'))
    open(os.path.join(ROOTOUT, 'calendar_summary.md'), 'w').write('\n'.join(L) + '\n')
    print('DONE in %.1f min' % ((time.time() - t0) / 60), flush=True)


if __name__ == '__main__':
    main()
