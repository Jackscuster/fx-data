import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""THE BOOK, under the new protocol. BOOK2.md. HANDOFF 0o.

All PASSERS from the three sources, equal risk each: daily correlation matrix,
book R per year, verified worst dip, return per dip, and the prop simulator
sized to the Team 1 budget.

WHAT THIS FILE DOES WHEN THERE ARE NO PASSERS, WHICH IS THE CASE IT WAS
WRITTEN FOR. A book of zero sleeves is not a number, and leaving the document
empty would hide the only thing worth saying. So it writes the empty-passer
verdict FIRST and then, clearly separated and clearly labelled, builds the
same book out of the best candidates BY RETURN PER DIP from each source --
which are NOT passers and are never described as if they were. That
supplementary book answers one specific question Jack has asked before: if
the best things found were combined, how far from 12% would the result be?

EQUAL RISK PER SLEEVE means weight 1/N on the daily series, days unioned, a
day a sleeve did not trade counted as ZERO for that sleeve -- not dropped.
Dropping it would silently reweight the book towards whichever sleeve happens
to trade most.

THE DIP IS THE BINDING ONE: the maximum of the realised chronological
drawdown and DIP95, the 95th percentile over shuffled day orders. On item 5's
eight sleeves DIP95 was ABOVE the realised dip on all eight, by 1.22x to
2.36x. BOOK.md first claimed the opposite and was corrected; the rule is to
take the maximum and never to assume which binds.

FAULTS THIS FILE FOUND IN ITSELF
  1. The first version weighted sleeves 1/N over the days each sleeve HAD,
     which is not equal risk -- a sleeve trading half as many days got double
     weight on the days it did trade. Fixed to a union index with zero fill.
"""
import os, time, json
import numpy as np, pandas as pd

import l2sweep as S
import nnfxproto as P
import nnfxsrc1 as S1
import nnfxsrc2 as S2
import nnfxsrc3 as S3
import r2reads as RR

OUT = os.path.join(ROOTOUT, 'nnfx')
TEAM1_DIP = 3.6          # Team 1's internal budget, % trailing
TEAM1_DAY = 3.6          # and % daily
TARGET_PCT = 12.0        # Jack's target for the whole book


def _sources():
    """-> [(source, id, candidate dict, row)] for everything scored so far."""
    got = []
    f1 = os.path.join(OUT, 'source1_summary.csv')
    if os.path.exists(f1):
        D = pd.read_csv(f1)
        for C in S1.candidates():
            r = D[D.cand == C['name']]
            if len(r):
                got.append(('source1', C['name'], C, r.iloc[0]))
    f2 = os.path.join(OUT, 'source2_summary.csv')
    if os.path.exists(f2):
        D = pd.read_csv(f2)
        for C in S2.candidates():
            r = D[D.cand == C['name']]
            if len(r):
                got.append(('source2', C['name'], C, r.iloc[0]))
    f3 = os.path.join(OUT, 'src3_gates.csv')
    if os.path.exists(f3):
        S3.init_space()
        D = pd.read_csv(f3)
        for _, r in D.iterrows():
            t = tuple((r[sl], r[sl + '_set']) for sl in P.SLOTS)
            C = S3.mkcand(t, name=r['cand'])
            C['source'] = 'source3_search'; C['reason'] = ''
            got.append(('source3', r['cand'], C, r))
    return got


def _daily(C):
    T = P.run_candidate(C)
    return P.daily_of(T, P.EVIDENCE).set_index('date').R


def book_of(series, keys):
    """EQUAL RISK: weight 1/N, union index, missing day = 0."""
    keys = [k for k in keys if k in series and series[k] is not None
            and len(series[k])]
    if not keys:
        return pd.Series(dtype=float)
    idx = series[keys[0]].index
    for k in keys[1:]:
        idx = idx.union(series[k].index)
    M = pd.DataFrame({k: series[k].reindex(idx).fillna(0.0) for k in keys})
    return M.mean(axis=1)


def stats(s, boot=True):
    d = np.asarray(s, float)
    d = d[np.isfinite(d)]
    if not len(d):
        return {}
    eq = np.cumsum(d)
    true_dip = float(np.max(np.maximum.accumulate(eq) - eq))
    d95 = P._dip95(d)
    bind = float(np.nanmax([true_dip, d95]))
    tot = float(d.sum())
    yrs = pd.Series(d, index=pd.DatetimeIndex(s.index)[np.isfinite(
        np.asarray(s, float))]).groupby(
            lambda t: t.year).sum().sort_index()
    nyr = max(1, len(yrs))
    # boot=False SKIPS THE 2000-DRAW BLOCK BOOTSTRAP AND NOTHING ELSE. It is
    # for nnfxbooks.mid(), which needs the dip and not the t. Every other
    # number below, R_per_dip included, is unchanged on both branches.
    tb, _sd = (P.N._block_t(d, ndraw=2000) if boot
               else (np.nan, np.nan))
    worst_day = float(-d.min()) if d.min() < 0 else np.nan
    sc_t1 = min(TEAM1_DIP / bind if bind > 0 else np.inf,
                TEAM1_DAY / worst_day if worst_day and worst_day > 0
                else np.inf)
    sc_fm = min(RR.FIRM_TRAIL * 100.0 / bind if bind > 0 else np.inf,
                RR.FIRM_DAILY * 100.0 / worst_day
                if worst_day and worst_day > 0 else np.inf)
    return dict(days=len(d), R_total=tot, R_per_year=tot / nyr,
                dip_true=true_dip, dip95=d95, dip_binding=bind,
                R_per_dip=(tot / bind if bind > 1e-9 else np.nan),
                worst_day_R=worst_day, years=nyr,
                years_positive=int((yrs > 0).sum()),
                t_block_boot=tb,
                t_yearly=(float(yrs.mean() * np.sqrt(nyr) / yrs.std(ddof=1))
                          if nyr > 1 and yrs.std(ddof=1) > 0 else np.nan),
                team1_scale=(float(sc_t1) if np.isfinite(sc_t1) else np.nan),
                team1_pct_per_year=(tot / nyr * float(sc_t1)
                                    if np.isfinite(sc_t1) else np.nan),
                firm_scale=(float(sc_fm) if np.isfinite(sc_fm) else np.nan),
                firm_pct_per_year=(tot / nyr * float(sc_fm)
                                   if np.isfinite(sc_fm) else np.nan))


def prop(s, scale, rules='firm'):
    """The prop simulator on this book at this sizing."""
    d = np.asarray(s, float) * float(scale)
    tf, df = ((RR.FIRM_TRAIL, RR.FIRM_DAILY) if rules == 'firm'
              else (RR.INT_TRAIL, RR.INT_DAILY))
    ev = RR.prop_run(d, 'eval', 'fixed', trail_frac=tf, daily_frac=df)
    fu = RR.prop_run(d, 'funded', 'fixed', trail_frac=tf, daily_frac=df)
    return dict(rules=rules,
                eval_days_to_pass=ev.get('passed_eval_day'),
                eval_breached=ev.get('breached'),
                funded_breached=fu.get('breached'),
                funded_payout_per_year=fu.get('paid_out_per_year'),
                funded_return_pct_per_year=fu.get('return_pct_per_year'),
                funded_worst_dip_pct=fu.get('worst_dip_pct'))


def run(verbose=True):
    S.load_costs(os.environ.get('FX_COST_TABLE',
                                os.path.join(ROOTOUT, 'cost_table_h22.csv')))
    got = _sources()
    assert got, 'no source summary on disk: run Source 1 and 2 first'
    passers = [(src, nm, C, r) for (src, nm, C, r) in got
               if int(r.get('passer', 0)) == 1]
    # the supplementary set: the best by R per dip from each source
    best = []
    for src in ('source1', 'source2', 'source3'):
        q = [(src2, nm, C, r) for (src2, nm, C, r) in got if src2 == src]
        if not q:
            continue
        q = sorted(q, key=lambda x: -(float(x[3].get('R_per_dip', -np.inf))
                                      if np.isfinite(float(
                                          x[3].get('R_per_dip', np.nan)))
                                      else -np.inf))
        best += q[:2]
    use = passers if passers else best
    label = 'passers' if passers else 'best_by_R_per_dip_NOT_PASSERS'
    if verbose:
        print('  BOOK2: %d passers; building the %s book from %d sleeves'
              % (len(passers), label, len(use)), flush=True)
    ser, rows = {}, []
    for (src, nm, C, r) in use:
        s = _daily(C)
        ser[nm] = s
        st = stats(s)
        rows.append(dict(sleeve=nm, source=src, label=P.cand_label(C),
                         passer=int(r.get('passer', 0)), **st))
        if verbose:
            print('    %-6s %-8s R %+8.3f  R/yr %+6.3f  dip %7.3f  '
                  'R/dip %+6.3f' % (nm, src, st.get('R_total', np.nan),
                                    st.get('R_per_year', np.nan),
                                    st.get('dip_binding', np.nan),
                                    st.get('R_per_dip', np.nan)), flush=True)
    SL = pd.DataFrame(rows)
    SL.to_csv(os.path.join(OUT, 'book2_sleeves.csv'), index=False)
    # ---- the book, added one sleeve at a time in R/dip order
    order = list(SL.sort_values('R_per_dip', ascending=False).sleeve)
    inc = []
    for k in range(1, len(order) + 1):
        keys = order[:k]
        b = book_of(ser, keys)
        st = stats(b)
        corr = np.nan
        if k > 1:
            prev = book_of(ser, order[:k - 1])
            idx = prev.index.union(ser[order[k - 1]].index)
            a = prev.reindex(idx).fillna(0.0)
            c = ser[order[k - 1]].reindex(idx).fillna(0.0)
            if a.std() > 0 and c.std() > 0:
                corr = float(np.corrcoef(a, c)[0, 1])
        inc.append(dict(n_sleeves=k, members='+'.join(keys),
                        new_sleeve=order[k - 1],
                        corr_new_with_book=corr, **st))
    INC = pd.DataFrame(inc)
    INC.to_csv(os.path.join(OUT, 'book2_incremental.csv'), index=False)
    # ---- the correlation matrix
    idx = None
    for k in order:
        idx = ser[k].index if idx is None else idx.union(ser[k].index)
    M = pd.DataFrame({k: ser[k].reindex(idx).fillna(0.0) for k in order})
    CM = M.corr()
    CM.to_csv(os.path.join(OUT, 'book2_corr.csv'))
    # ---- the prop simulator on the best book
    bb = INC.sort_values('R_per_dip', ascending=False).iloc[0]
    bkeys = bb.members.split('+')
    b = book_of(ser, bkeys)
    st = stats(b)
    prows = []
    for rules in ('firm', 'internal'):
        for sname, sc in (('team1', st['team1_scale']),
                          ('firm_max', st['firm_scale']), ('unit', 1.0)):
            if not np.isfinite(sc):
                continue
            prows.append(dict(book=bb.members, budget=sname, scale=sc,
                              **prop(b, sc, rules)))
    PR = pd.DataFrame(prows)
    PR.to_csv(os.path.join(OUT, 'book2_prop.csv'), index=False)
    meta = dict(label=label, n_passers=len(passers), n_sleeves=len(use),
                best_book=bb.members,
                best_book_R_per_year=st['R_per_year'],
                best_book_dip=st['dip_binding'],
                best_book_R_per_dip=st['R_per_dip'],
                team1_pct_per_year=st['team1_pct_per_year'],
                firm_pct_per_year=st['firm_pct_per_year'],
                target_pct=TARGET_PCT,
                factor_short=(TARGET_PCT / st['firm_pct_per_year']
                              if st['firm_pct_per_year'] and
                              st['firm_pct_per_year'] > 0 else np.nan))
    pd.DataFrame([meta]).to_csv(os.path.join(OUT, 'book2_meta.csv'),
                                index=False)
    if verbose:
        print('  BOOK2 best book %s: %.3f%% a year at firm limits, target '
              '%.0f%%' % (bb.members, meta['firm_pct_per_year'], TARGET_PCT),
              flush=True)
    return dict(sleeves=SL, inc=INC, corr=CM, prop=PR, meta=meta)


def md(R=None):
    f = P.fmt
    SL = (R['sleeves'] if R else pd.read_csv(
        os.path.join(OUT, 'book2_sleeves.csv')))
    INC = (R['inc'] if R else pd.read_csv(
        os.path.join(OUT, 'book2_incremental.csv')))
    CM = (R['corr'] if R else pd.read_csv(
        os.path.join(OUT, 'book2_corr.csv'), index_col=0))
    PR = (R['prop'] if R else pd.read_csv(os.path.join(OUT, 'book2_prop.csv')))
    M = (R['meta'] if R else pd.read_csv(
        os.path.join(OUT, 'book2_meta.csv')).iloc[0].to_dict())
    npass = int(M['n_passers'])
    L = []
    L.append('# BOOK2 — the book under the new protocol\n')
    if npass == 0:
        L.append('## There are no passers\n')
        L.append('**Not one candidate from any of the three sources clears '
                 'all four gates of `results/nnfx/PROTOCOL.md`.** A book of '
                 'zero sleeves has no return, no dip and no prop result, and '
                 'that is the headline of this document.\n')
        L.append('What was tested: **6** published combinations at their own '
                 'settings (Source 1), **10** hand-built algorithms built on '
                 'the project\'s own measured leaders (Source 2), and a '
                 'machine search over a space of 2.5 billion complete '
                 'algorithms judged against 50 null searches at the same '
                 'budget (Source 3). Twenty-eight pairs, eleven unseen '
                 'years, era-correct costs, a 1:30 leverage cap, realistic '
                 'gap fills.\n')
        L.append('### The book below is NOT a book of passers\n')
        L.append('It is the same machinery run on the **best candidates by '
                 'return per dip** from each source, up to two each, so that '
                 'one specific question has a number: *if the best things '
                 'found were combined, how far from 12%% would it be?* '
                 'Nothing in it clears the gates and nothing in it should be '
                 'traded.\n')
    else:
        L.append('**%d passers, equal risk each.** Protocol: '
                 '`results/nnfx/PROTOCOL.md`.\n' % npass)
    L.append('## The sleeves\n')
    L.append('| sleeve | source | passer | R total | R/yr | dip | **R/dip** | '
             't block | yrs + |')
    L.append('|---|---|---|---:|---:|---:|---:|---:|---:|')
    for _, r in SL.sort_values('R_per_dip', ascending=False).iterrows():
        L.append('| **%s** | %s | %s | %s | %s | %s | **%s** | %s | %d of %d |'
                 % (r['sleeve'], r['source'],
                    'yes' if int(r.get('passer', 0)) else 'no',
                    f(r.get('R_total')), f(r.get('R_per_year')),
                    f(r.get('dip_binding'), 3, False), f(r.get('R_per_dip')),
                    f(r.get('t_block_boot'), 2),
                    int(r.get('years_positive', 0)), int(r.get('years', 0))))
    L.append('')
    L.append('## Adding one sleeve at a time, in return-per-dip order\n')
    L.append('| n | members | new sleeve | corr of new with book | R/yr | '
             'dip | **R/dip** | Team 1 %/yr | firm %/yr |')
    L.append('|---:|---|---|---:|---:|---:|---:|---:|---:|')
    for _, r in INC.iterrows():
        L.append('| %d | %s | %s | %s | %s | %s | **%s** | %s | %s |'
                 % (r['n_sleeves'], r['members'], r['new_sleeve'],
                    f(r.get('corr_new_with_book'), 3),
                    f(r.get('R_per_year')), f(r.get('dip_binding'), 3, False),
                    f(r.get('R_per_dip')), f(r.get('team1_pct_per_year'), 3),
                    f(r.get('firm_pct_per_year'), 3)))
    L.append('')
    L.append('**Equal risk means weight 1/N on a UNION day index with a '
             'missing day counted as zero**, not dropped. Dropping it would '
             'reweight the book towards whichever sleeve trades most often.\n')
    L.append('## Daily correlation between sleeves\n')
    cols = list(CM.columns)
    L.append('| | ' + ' | '.join(cols) + ' |')
    L.append('|---|' + '---:|' * len(cols))
    for i in CM.index:
        L.append('| **%s** | ' % i
                 + ' | '.join(f(float(CM.loc[i, c]), 3) for c in cols) + ' |')
    L.append('')
    L.append('## Through the prop simulator\n')
    L.append('| rules | budget | scale | days to pass +10%% | eval breach | '
             'funded breach | payout $/yr | return %%/yr |')
    L.append('|---|---|---:|---:|---|---|---:|---:|')
    for _, r in PR.iterrows():
        L.append('| %s | %s | %s | %s | %s | %s | %s | %s |'
                 % (r['rules'], r['budget'], f(r['scale'], 2, False),
                    f(r.get('eval_days_to_pass'), 0, False),
                    r.get('eval_breached') or 'none',
                    r.get('funded_breached') or 'none',
                    f(r.get('funded_payout_per_year'), 0),
                    f(r.get('funded_return_pct_per_year'), 3)))
    L.append('')
    L.append('`team1` sizes to Team 1\'s internal budget (3.6%% trailing, '
             '3.6%% daily); `firm_max` sizes to the firm\'s own limits (6%% '
             'trailing, 4%% daily), which is the **largest size the rules '
             'permit** and therefore the ceiling. `unit` is one R per sleeve '
             'unscaled.\n')
    L.append('## How far from 12%%\n')
    fp = M.get('firm_pct_per_year')
    if fp and np.isfinite(fp) and fp > 0:
        L.append('> **The best book here is `%s` at %s%% a year at the '
                 'firm\'s maximum legal sizing, against a 12%% target — '
                 'short by %s percentage points, a factor of %s.**\n'
                 % (M['best_book'], f(fp, 3, False),
                    f(TARGET_PCT - fp, 2, False),
                    f(M.get('factor_short'), 1, False)))
    else:
        L.append('> **The best book here does not make money at any sizing, '
                 'so the distance to 12%% is not a multiple.**\n')
    if npass == 0:
        L.append('And it is not a book of passers. The honest reading is '
                 'that the protocol found **nothing that clears its own '
                 'gates**, and the best non-passers combined still fall short '
                 'of the target by a large factor. The gap is in the '
                 'return, not in the combination: the correlation matrix '
                 'above shows what diversification is available, and it is '
                 'not enough to turn a number of this size into 12%%.\n')
    L.append('## No 2016-2020 number is opened\n')
    L.append('Those years are computed and stored in the per-candidate CSVs '
             'and are **not summarised anywhere in this document**. 2021 '
             'onward is sealed and not read. When a passer exists the run '
             'stops and reports, so Jack can call the confirm.\n')
    L.append('## Provenance\n')
    L.append(P.prov([os.path.join(OUT, x) for x in
                     ('book2_sleeves.csv', 'book2_incremental.csv',
                      'book2_corr.csv', 'book2_prop.csv', 'book2_meta.csv')]))
    L.append('')
    open(os.path.join(OUT, 'BOOK2.md'), 'w').write('\n'.join(L))
    print('  BOOK2.md written (%d lines)' % len(L), flush=True)


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--md-only', action='store_true')
    a = ap.parse_args()
    if a.md_only:
        md()
    else:
        md(run())
