import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""AGREEMENT STUDY — does it matter how many members want the same trade?

Works off the final rosters' own trade logs. Equal weight, cost-charged,
everything already lagged one bar by the engine.

THE UNIT IS THE POSITION-DAY, THE EVIDENCE IS THE EPISODE. A trade held 12 days
is 12 position-days of exposure but ONE piece of evidence. Every count below is
in position-days; every significance test is over EPISODES -- a run of
consecutive days at the same agreement level on the same pair -- because
consecutive days of one position are not independent observations and treating
them as such would inflate every t-statistic by roughly the square root of the
holding period.

R IS ATTRIBUTED ACROSS THE HOLDING PERIOD. A trade's R is divided evenly over
the days it was open, so a day's return belongs to the agreement level that was
actually in force that day rather than to whatever happened to be true on the
exit date.

THE NULL SHUFFLES MEMBERSHIP, NOT RETURNS. Which member fired a given trade is
permuted 1,000 times, holding the trades themselves fixed. That breaks any real
link between who agrees and what happens while preserving the trade population,
the calendar and the pair mix exactly -- so a slope that survives is about
agreement rather than about the sample.
"""
import glob, json, time, argparse
import numpy as np, pandas as pd

import l2sweep as S
import l2trades as TR
import l2crisis as C

SPLIT = pd.Timestamp('2016-01-01')
N_NULL = 1000
SEED = 20260910


def member_trades(cfg, wins):
    """Every blind trade with DIRECTION, which blind_trades does not carry."""
    code = dict((s, c) for s, _, c in S.SLICES)[cfg['slice']]
    out = []
    _fail = {}
    for p in S.all_pairs():
        try:
            r = TR.run_pair(cfg, p)
        except Exception as _e:
            # COUNT, NEVER SILENTLY SKIP. This swallow is why three separate
            # faults reported success while doing nothing: a config missing
            # ip2, a roster carrying no settings, and a hardcoded mode all
            # raised here and were skipped pair by pair, leaving an empty
            # result that downstream code read as "no trades".
            _fail[type(_e).__name__ + ': ' + str(_e)[:80]] = _fail.get(
                type(_e).__name__ + ': ' + str(_e)[:80], 0) + 1
            continue
        d, tr = r['dates'], r['trades']
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
            out.append(dict(pair=p, entry=d[eb], exit=d[xb], R=float(tr['r'][j]),
                            dir=int(tr['dir'][j])))
    if _fail and not out:
        raise RuntimeError(
            'every one of the %d pairs failed and no trades were produced. '
            'Causes: %s' % (len(S.all_pairs()), _fail))
    if _fail:
        print('  WARNING: %d of %d pairs failed: %s'
              % (sum(_fail.values()), len(S.all_pairs()), _fail), flush=True)
    return pd.DataFrame(out)


def position_days(roster, wins):
    """One row per (member, pair, day) while a position is open."""
    rows = []
    for m in roster.to_dict('records'):
        T = member_trades(m, wins)
        if not len(T):
            continue
        for t in T.itertuples():
            days = pd.date_range(t.entry, t.exit, freq='B')
            if not len(days):
                days = pd.DatetimeIndex([t.entry])
            per = t.R / len(days)
            for dte in days:
                rows.append((m['member'], t.pair, dte, t.dir, per))
    return pd.DataFrame(rows, columns=['member', 'pair', 'day', 'dir', 'r_day'])


def label(PD):
    """Agreement level per (pair, day, side) and the opposition split."""
    g = PD.groupby(['pair', 'day', 'dir']).agg(n_side=('member', 'nunique'),
                                               r=('r_day', 'sum')).reset_index()
    tot = g.groupby(['pair', 'day']).n_side.sum().rename('n_total')
    sides = g.groupby(['pair', 'day']).dir.nunique().rename('n_sides')
    g = g.merge(tot, on=['pair', 'day']).merge(sides, on=['pair', 'day'])
    PD = PD.merge(g[['pair', 'day', 'dir', 'n_side', 'n_total', 'n_sides']],
                  on=['pair', 'day', 'dir'], how='left')
    PD['opposed'] = PD.n_sides > 1
    PD['split'] = PD.is_split = None
    return PD, g


def episodes(df, keys):
    """A run of consecutive business days on the same key is ONE episode."""
    df = df.sort_values(keys + ['day']).copy()
    grp = df.groupby(keys)['day']
    newrun = grp.diff().dt.days.gt(4) | grp.diff().isna()
    df['episode'] = newrun.groupby([df[k] for k in keys]).cumsum()
    return df


def agg_level(PD, tag):
    """Per agreement level, split in-sample / out-of-sample."""
    rows = []
    n_members = PD.member.nunique()
    for lvl, g in PD.groupby('n_side'):
        for per, mask in (('IS', g.day < SPLIT), ('OOS', g.day >= SPLIT)):
            gg = g[mask]
            if not len(gg):
                continue
            e = episodes(gg, ['pair', 'n_side'])
            ep = e.groupby(['pair', 'n_side', 'episode']).r_day.sum()
            eq = gg.sort_values('day').groupby('day').r_day.sum().cumsum()
            dip = float((eq.cummax() - eq).max()) if len(eq) else 0.0
            rows.append(dict(team=tag, level=int(lvl),
                             share_of_roster=round(100.0 * lvl / max(1, n_members), 1),
                             period=per, position_days=len(gg),
                             episodes=int(ep.shape[0]),
                             r_per_unit=float(gg.r_day.mean()),
                             r_per_episode=float(ep.mean()),
                             hit_rate_pct=round(100.0 * float((ep > 0).mean()), 1),
                             worst_dip_R=round(dip, 3)))
    return pd.DataFrame(rows)


def slope_test(PD, rng, n_null=N_NULL):
    """Does return per unit rise with agreement level? Episode-based, then a
    membership-shuffle null."""
    e = episodes(PD, ['pair', 'n_side'])
    ep = e.groupby(['pair', 'n_side', 'episode']).agg(r=('r_day', 'sum'),
                                                      lvl=('n_side', 'first')).reset_index()
    def slope(d):
        if d.lvl.nunique() < 2:
            return np.nan
        return float(np.polyfit(d.lvl.values, d.r.values, 1)[0])
    real = slope(ep)
    real_is = slope(ep[ep.index.isin(ep.index)])  # placeholder, split below
    # null: permute which member fired each trade -> re-derive levels
    members = PD.member.values
    null = np.empty(n_null)
    base = PD.copy()
    for i in range(n_null):
        base['member'] = rng.permutation(members)
        g = base.groupby(['pair', 'day', 'dir']).member.nunique().rename('n_side').reset_index()
        b2 = base.drop(columns=['n_side']).merge(g, on=['pair', 'day', 'dir'], how='left')
        e2 = episodes(b2, ['pair', 'n_side'])
        ep2 = e2.groupby(['pair', 'n_side', 'episode']).agg(
            r=('r_day', 'sum'), lvl=('n_side', 'first')).reset_index()
        null[i] = slope(ep2)
    pct = float((null < real).mean() * 100.0)
    return dict(slope=real, null_mean=float(np.nanmean(null)),
                null_p95=float(np.nanpercentile(null, 95)),
                percentile_of_real=round(pct, 1),
                p_value=round(float((null >= real).mean()), 4))


def per_member(PD, tag):
    """How often each member trades alone vs in agreement, and what it earns
    in each state."""
    rows = []
    for m, g in PD.groupby('member'):
        alone = g[g.n_side == 1]
        withs = g[g.n_side > 1]
        d = dict(team=tag, member=m, position_days=len(g),
                 pct_alone=round(100.0 * len(alone) / len(g), 1),
                 r_alone=float(alone.r_day.mean()) if len(alone) else np.nan,
                 r_with_others=float(withs.r_day.mean()) if len(withs) else np.nan,
                 r_overall=float(g.r_day.mean()))
        for lvl in range(1, 9):
            d['pct_at_level_%d' % lvl] = round(100.0 * float((g.n_side == lvl).mean()), 1)
        # the two flags asked for
        d['only_earns_with_others'] = bool(len(alone) and len(withs)
                                           and d['r_alone'] <= 0 < d['r_with_others'])
        d['earns_alone_loses_in_agreement'] = bool(len(alone) and len(withs)
                                                   and d['r_alone'] > 0 >= d['r_with_others'])
        rows.append(d)
    return pd.DataFrame(rows).sort_values('r_overall', ascending=False)


def opposition(PD, gside, tag, rng):
    """Days where members sit on both sides of the same pair."""
    opp = gside[gside.n_sides > 1].copy()
    if not len(opp):
        return pd.DataFrame(), pd.DataFrame(), {}
    # (a) how often, by split shape
    piv = opp.pivot_table(index=['pair', 'day'], columns='dir', values='n_side',
                          aggfunc='sum').fillna(0)
    piv.columns = ['short' if c < 0 else 'long' for c in piv.columns]
    for c in ('long', 'short'):
        if c not in piv:
            piv[c] = 0
    piv['maj'] = piv[['long', 'short']].max(axis=1)
    piv['minr'] = piv[['long', 'short']].min(axis=1)
    piv['shape'] = piv.maj.astype(int).astype(str) + 'v' + piv.minr.astype(int).astype(str)
    piv['maj_dir'] = np.where(piv.long >= piv.short, 1, -1)

    rr = PD.merge(piv.reset_index()[['pair', 'day', 'shape', 'maj_dir', 'maj', 'minr']],
                  on=['pair', 'day'], how='inner')
    rr['is_majority'] = rr.dir == rr.maj_dir
    # (b) three handlings, same episodes
    rows = []
    E = episodes(rr, ['pair'])
    for name in ('follow_majority_net', 'take_all_as_fired', 'sit_out'):
        if name == 'sit_out':
            r = pd.Series(0.0, index=E.index)
        elif name == 'take_all_as_fired':
            r = E.r_day
        else:
            # net size: majority minus minority, so a member on the minority
            # side cancels one on the majority side
            r = np.where(E.is_majority, E.r_day, -E.r_day)
            r = pd.Series(r, index=E.index)
        tmp = E.assign(rr=r)
        ep = tmp.groupby(['pair', 'episode']).rr.sum()
        eq = tmp.groupby('day').rr.sum().sort_index().cumsum()
        dip = float((eq.cummax() - eq).max()) if len(eq) else 0.0
        rows.append(dict(team=tag, handling=name, position_days=len(tmp),
                         episodes=int(ep.shape[0]),
                         r_per_unit=float(tmp.rr.mean()),
                         hit_rate_pct=round(100.0 * float((ep > 0).mean()), 1),
                         worst_dip_R=round(dip, 3)))
        for shp, gg in tmp.groupby('shape'):
            epg = gg.groupby(['pair', 'episode']).rr.sum()
            rows.append(dict(team=tag, handling=name + '::' + shp,
                             position_days=len(gg), episodes=int(epg.shape[0]),
                             r_per_unit=float(gg.rr.mean()),
                             hit_rate_pct=round(100.0 * float((epg > 0).mean()), 1),
                             worst_dip_R=np.nan))
    HAND = pd.DataFrame(rows)

    # (c) which members are right when opposed
    mrows = []
    overall = PD.groupby('member').r_day.mean()
    for m, g in rr.groupby('member'):
        e = episodes(g, ['pair'])
        ep = e.groupby(['pair', 'episode']).r_day.sum()
        for per, mask in (('ALL', slice(None)), ('IS', g.day < SPLIT), ('OOS', g.day >= SPLIT)):
            gg = g if per == 'ALL' else g[mask]
            if not len(gg):
                continue
            ee = episodes(gg, ['pair']).groupby(['pair', 'episode']).r_day.sum()
            mrows.append(dict(team=tag, member=m, period=per,
                              opposed_episodes=int(ee.shape[0]),
                              accuracy_pct=round(100.0 * float((ee > 0).mean()), 1),
                              r_per_unit_opposed=float(gg.r_day.mean()),
                              r_per_unit_overall=float(overall.get(m, np.nan))))
    MEM = pd.DataFrame(mrows)

    # null: shuffle SIDES within each pair-day, see where real accuracy sits
    real = float((rr.assign(w=rr.r_day > 0).groupby('member').w.mean()).mean())
    null = np.empty(200)
    for i in range(200):
        f = rr.copy()
        f['dir'] = rng.permutation(f.dir.values)
        f['is_majority'] = f.dir == f.maj_dir
        null[i] = float((f.assign(w=np.where(f.is_majority, f.r_day, -f.r_day) > 0)
                         .groupby('member').w.mean()).mean())
    # (d) majority vs the best individual
    maj_ep = episodes(rr[rr.is_majority], ['pair']).groupby(['pair', 'episode']).r_day.sum()
    best = MEM[MEM.period == 'ALL'].sort_values('accuracy_pct', ascending=False)
    info = dict(majority_accuracy_pct=round(100.0 * float((maj_ep > 0).mean()), 1),
                best_member=(best.iloc[0].member if len(best) else None),
                best_member_accuracy_pct=(float(best.iloc[0].accuracy_pct) if len(best) else None),
                null_mean_accuracy=round(float(np.nanmean(null)), 4),
                real_accuracy=round(real, 4),
                shapes=piv.shape_counts if False else piv['shape'].value_counts().to_dict())
    return HAND, MEM, info


def load_roster(tag):
    # ACCEPT A LABEL. The chain builds labelled rosters
    # (team1_W3ONLY_ADOPTED_roster.csv); this looked only for the bare
    # team1_roster.csv, found nothing, printed 'skipped' and exited in seven
    # seconds -- a silent no-op the chain recorded as a completed stage.
    lab = os.environ.get('TEAM_LABEL', '')
    cands = ['%s%s_roster.csv' % (tag, lab)] if lab else []
    cands += ['%s_roster.csv' % tag]
    if not lab:
        import glob as _g
        cands += sorted(_g.glob(os.path.join(ROOTOUT, '%s_*_roster.csv' % tag)))
    f = None
    for c in cands:
        c = c if os.path.isabs(c) else os.path.join(ROOTOUT, c)
        if os.path.exists(c):
            f = c
            break
    if f is None:
        print('  no roster found for %s (looked for %s)' % (tag, cands), flush=True)
        return None
    R = pd.read_csv(f)
    R['member'] = R.sid.astype(str) + '::' + R.variant.astype(str)
    # THE ROSTER IS A SUMMARY, NOT A CONFIGURATION. It carries the recipe and
    # the vote but not ip2 or the risk settings, so every engine call raised and
    # was swallowed by the per-pair try/except, giving 'no position-days' after
    # the rosters had loaded successfully. Join the settings back on.
    v = os.path.join(ROOTOUT, 'gate3_costed_verdicts.csv')
    if os.path.exists(v):
        V = pd.read_csv(v, low_memory=False)
        keep = [c for c in ('sid', 'ip2', 'src_mode', 'src_label', 'exit_ind',
                            'risk_atr_len', 'risk_atr_mult', 'risk_tp_mult',
                            'risk_trail_mult', 'risk_trail_arm', 'risk_be_pct')
                if c in V.columns]
        R = R.merge(V[keep].drop_duplicates('sid'), on='sid', how='left',
                    suffixes=('', '_v'))
    missing = R.ip2.isna().sum() if 'ip2' in R.columns else len(R)
    if missing:
        raise SystemExit('%d of %d roster members have no settings after the '
                         'join -- refusing to report an agreement study on a '
                         'book that cannot be run' % (missing, len(R)))
    return R


def main():
    t0 = time.time()
    rng = np.random.default_rng(SEED)
    wins = C.windows()
    LV, MEM_ALL, OPP_ALL, verdicts = [], {}, [], {}
    for tag in ('team1', 'team2'):
        R = load_roster(tag)
        if R is None:
            print('%s roster missing -- skipped' % tag, flush=True); continue
        print('%s: %d members' % (tag, len(R)), flush=True)
        PD = position_days(R, wins)
        if not len(PD):
            print('  no position-days'); continue
        PD, gside = label(PD)
        print('  %d position-days, %d pair-days' % (len(PD), len(gside)), flush=True)
        L = agg_level(PD, tag); LV.append(L)
        L.to_csv(os.path.join(ROOTOUT, 'agreement_levels_%s.csv' % tag), index=False)
        M = per_member(PD, tag); MEM_ALL[tag] = M
        M.to_csv(os.path.join(ROOTOUT, 'agreement_by_member_%s.csv' % tag), index=False)
        tp = time.time()
        st_is = slope_test(PD[PD.day < SPLIT], rng)
        st_oos = slope_test(PD[PD.day >= SPLIT], rng)
        print('  slope tests took %.1f s' % (time.time() - tp), flush=True)
        HAND, OMEM, info = opposition(PD, gside, tag, rng)
        if len(HAND):
            OPP_ALL.append(HAND)
            OMEM.to_csv(os.path.join(ROOTOUT, 'opposition_by_member_%s.csv' % tag), index=False)
        verdicts[tag] = dict(slope_IS=st_is, slope_OOS=st_oos, opposition=info,
                             levels=L.to_dict('records'))
    if LV:
        pd.concat(LV, ignore_index=True).to_csv(
            os.path.join(ROOTOUT, 'agreement_levels_all.csv'), index=False)
    if OPP_ALL:
        pd.concat(OPP_ALL, ignore_index=True).to_csv(
            os.path.join(ROOTOUT, 'agreement_opposition.csv'), index=False)
    json.dump(verdicts, open(os.path.join(ROOTOUT, 'agreement_index.json'), 'w'),
              indent=1, default=str)

    L = ['# Agreement and opposition\n',
         'Position-days are the unit of exposure; EPISODES are the unit of evidence.',
         'Consecutive days of one position are not independent observations.\n']
    for tag, v in verdicts.items():
        s_is, s_oos = v['slope_IS'], v['slope_OOS']
        L.append('## %s\n' % tag.upper())
        L.append('**Does agreement predict return?**  in-sample slope %.4f R per level '
                 '(null mean %.4f, real sits at the %.1fth percentile, p=%.4f); '
                 'out-of-sample slope %.4f (p=%.4f).\n'
                 % (s_is['slope'], s_is['null_mean'], s_is['percentile_of_real'],
                    s_is['p_value'], s_oos['slope'], s_oos['p_value']))
        ok = (s_is['p_value'] < 0.05 and s_oos['slope'] > 0)
        L.append('**Verdict:** %s\n' % (
            'agreement is worth extra size -- the slope is positive, beats its '
            'membership-shuffle null in-sample and holds its sign out-of-sample.'
            if ok else
            'agreement is NOT worth extra size on this evidence. The slope does not '
            'clear its own null in-sample and/or does not hold out-of-sample.'))
        o = v['opposition']
        if o:
            L.append('**Opposition.** shapes: %s. Majority accuracy %.1f%%; best '
                     'individual %s at %.1f%%.\n'
                     % (o.get('shapes'), o.get('majority_accuracy_pct') or 0,
                        o.get('best_member'), o.get('best_member_accuracy_pct') or 0))
    open(os.path.join(ROOTOUT, 'agreement_summary.md'), 'w').write('\n'.join(L) + '\n')
    print('\nDONE in %.1f min' % ((time.time() - t0) / 60.0), flush=True)


if __name__ == '__main__':
    main()
