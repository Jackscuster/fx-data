import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""THE CLEAN FIELD — gate 2's bars on W2 ALONE, under ip1.

WHY. `l2tune.crosses_label` is handed the STITCHED W2+W3 blind book and requires
n_w3 >= MIN_TRADES_BLIND before applying its bars. W3 is 2016-2020 -- the years
the walk-forward trades. So membership of the 3,485-strategy field depends on
performance in the years it is supposed to be blind to. A strategy that did
badly in 2016-2020 was never in the universe, whatever it did on the build
years. Every absolute level built on that field is inflated; NO_CUT's 9.07%
median year with a +7.75% worst year is what a universe picked for those years
looks like when you hold all of it.

THE FIX. Re-label the FULL candidate set -- not the survivors -- on W2
(2011-2015) alone, scored with ip1, which was tuned on W1 and has never seen W2.
The same bars, the same minimum trade count, one window, no sight of 2016-2020.

WHY THE FULL CANDIDATE SET AND NOT THE 3,485. The crosser list is the thing
being rebuilt. Re-labelling only the survivors would keep every strategy that
gate 2's peek let through and re-admit none of the ones it wrongly excluded --
the contamination would survive the fix.

THREE SLICES ONLY. B-trend has no ip1 for ANY of its 14,815 candidates. The
packaged cloud job recovers ip1 for its 1,650 CROSSERS, which is the wrong set
for exactly the reason above. See HANDOFF QUEUE 1b.
"""
import glob, json, time, argparse
import numpy as np, pandas as pd
import l2sweep as S

S.WINDOWS = dict(S.WINDOWS)
S.WINDOWS['CW'] = ('2011-01-01', '2015-12-31')     # W2, the clean label window
import l2tune as T

SRC = (('gate2_tuned_modeA_trend.csv', 'A', 'trend', 'A-trend'),
       ('gate2_tuned_modeA_chop.csv',  'A', 'chop',  'A-chop'),
       ('gate2_tuned_modeB.csv',       'B', 'chop',  'B-chop'),
       ('gate2_tuned_modeB.csv',       'B', 'trend', 'B-trend'))
BANK = os.path.join(ROOTOUT, 'gate2_w2only_scores_%02d.csv')
BOXBANK = os.path.join(ROOTOUT, 'gate2_w2only_scores_box%02d.csv')


def box_of(sid, of):
    """md5(sid) %% N, fixed for all time -- the same rule l2recoverip1 uses, so
    a box owns the SAME strategies in both phases and never waits on another
    box's ip1."""
    import hashlib
    return int(hashlib.md5(sid.encode()).hexdigest(), 16) % of
OUT = os.path.join(ROOTOUT, 'gate2_cleanfield.csv')
DIFF = os.path.join(ROOTOUT, 'field_diff.csv')


def candidates(slices):
    F = []
    for f, mode, sl, lab in SRC:
        if lab not in slices:
            continue
        d = pd.read_csv(os.path.join(ROOTOUT, f), low_memory=False)
        d = d[d.slice == sl].copy()
        d['src_mode'] = mode
        # SID CONVENTION MUST MATCH l2clean3 AND l2walkfwd: mode B's label is
        # 'B', not 'B-chop'. It was 'B-chop' here, so every B sid failed to join
        # and the clean field silently contributed ZERO B-chop strategies.
        d['src_label'] = mode if mode == 'B' else lab
        d['sid'] = (d.src_label + '|' + d.slice + '|' + d.c1 + '|' + d.c2 + '|'
                    + d.vol + '|' + d.base)
        n0 = len(d)
        d = d[d.ip1.notna() & d.risk1.notna()] if 'ip1' in d.columns else d.iloc[0:0]
        if len(d) < n0:
            print('  %-8s %d of %d dropped: no ip1 banked' % (lab, n0 - len(d), n0),
                  flush=True)
        F.append(d)
    D = pd.concat(F, ignore_index=True).drop_duplicates('sid').reset_index(drop=True)
    return D


_SC = None


def _init():
    global _SC
    S.load_costs(); T.ACCT_OBJECTIVE = True
    _SC = T.Scorer()


def score_one(cfg):
    try:
        sn = cfg['slice']
        code = dict((s, c) for s, _, c in S.SLICES)[sn]
        plan = dict((s, p) for s, p, _ in S.SLICES)[sn]
        ip = json.loads(cfg['ip1']); rk = json.loads(cfg['risk1'])
        combo = (cfg['c1'], cfg['c2'], cfg['vol'], cfg['base'], cfg['exit_ind'])
        g = _SC.score(combo, ip, rk, cfg['src_mode'], sn, code, plan, ('CW',))
        a = g.get('CW')
    except Exception as e:
        return dict(sid=cfg['sid'], err=type(e).__name__ + ': ' + str(e)[:80])
    row = dict(sid=cfg['sid'], src_label=cfg['src_label'], err='')
    for k in ('n', 'total_R', 'expectancy_R', 'profit_factor', 'sharpe', 'sortino',
              'calmar', 'max_dd_R', 'win_rate', 'avg_win_R'):
        row['w2_' + k] = None if a is None else a.get(k)
    return row


def label(D):
    """Gate 2's bars, on W2 alone. max_dd_pct is max DD as a % of gross profit,
    the same relative form gate 2 uses."""
    L = T.LABEL
    gross = (D.w2_avg_win_R * D.w2_win_rate * D.w2_n)
    dd_pct = 100.0 * D.w2_max_dd_R / gross.replace(0, np.nan)
    ok = (D.w2_n >= S.MIN_TRADES_BLIND)
    fails = {'min_trades': int((~ok).sum())}
    for k in ('expectancy_R', 'profit_factor', 'sharpe', 'sortino', 'calmar'):
        good = (D['w2_' + k] >= L[k]).fillna(False)
        fails[k] = int((~good).sum()); ok &= good
    good = (dd_pct <= L['max_dd_pct']).fillna(False)
    fails['max_dd_pct'] = int((~good).sum()); ok &= good
    return ok, fails, dd_pct


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--slices', default='A-trend,A-chop,B-chop')
    ap.add_argument('--jobs', type=int, default=6)
    ap.add_argument('--box', type=int, default=0)
    ap.add_argument('--of', type=int, default=1)
    ap.add_argument('--shard-only', action='store_true',
                    help='score this box and stop; no label, no diff, no merge')
    ap.add_argument('--limit', type=int, default=0,
                    help='first N candidates only -- for the sharding dry run')
    ap.add_argument('--merge', action='store_true',
                    help='merge every box bank, then label and diff')
    a = ap.parse_args()
    import multiprocessing as mp
    t0 = time.time(); S.load_costs()
    sl = tuple(x for x in a.slices.split(',') if x)
    D = candidates(sl)
    if a.limit:
        D = D.head(a.limit).reset_index(drop=True)
    if a.merge:
        # MERGE reads every box bank and does the labelling once. Deliberately a
        # separate step run from the Mac rather than "the last box to finish
        # merges": last-to-finish is a race, and on 2026-09-10 a dead shard's
        # ABSENCE was read as completion and cost a whole chain.
        fs = sorted(glob.glob(os.path.join(ROOTOUT, 'gate2_w2only_scores_box*.csv')))
        fs += sorted(glob.glob(os.path.join(ROOTOUT, 'gate2_w2only_scores_[0-9]*.csv')))
        if not fs:
            raise SystemExit('no box banks to merge')
        R = pd.concat([pd.read_csv(f) for f in fs], ignore_index=True)
        R = R[R.sid != 'sid'].drop_duplicates('sid')
        print('merged %d box banks -> %d scored strategies' % (len(fs), len(R)), flush=True)
        miss = set(D.sid) - set(R.sid)
        if miss:
            print('  WARNING: %d of %d candidates have no score -- a box has not '
                  'finished or did not push. Labelling anyway would silently '
                  'shrink the field.' % (len(miss), len(D)), flush=True)
            raise SystemExit('refusing to merge an incomplete field')
    else:
        if a.of > 1:
            n0 = len(D)
            D = D[[box_of(x, a.of) == a.box for x in D.sid]].reset_index(drop=True)
            print('box %d of %d: %d of %d candidates' % (a.box, a.of, len(D), n0),
                  flush=True)
        print('clean-field candidates: %d across %s' % (len(D), sl), flush=True)
        with mp.Pool(a.jobs, initializer=_init) as pool:
            got = pool.map(score_one, D.to_dict('records'), chunksize=16)
        R = pd.DataFrame(got)
        el = time.time() - t0
        print('  scored %d in %.1f min (%.2f s each, %d jobs)'
              % (len(R), el / 60, el * a.jobs / max(len(R), 1), a.jobs), flush=True)
        R.to_csv(BOXBANK % a.box if a.of > 1 else BANK % 0, index=False)
        if a.shard_only:
            print('shard-only: box %d written, stopping. Merge from the Mac with '
                  '--merge' % a.box, flush=True)
            return
        D = candidates(sl)
    M = D.merge(R.drop(columns=['src_label']), on='sid')
    ok, fails, dd = label(M)
    M['w2_max_dd_pct'] = dd
    M['clean_label'] = ok
    M['label_basis'] = 'W2_ip1'
    C = M[ok].reset_index(drop=True)
    C.to_csv(OUT, index=False)
    print('  CLEAN FIELD: %d of %d pass (%.1f%%); failures by bar %s'
          % (len(C), len(M), 100.0 * len(C) / len(M), fails), flush=True)
    # ---- the diff against the contaminated field
    old = set()
    lim = set(D.sid) if a.limit else None
    for f, mode, slc, lab in SRC:
        if lab not in sl:
            continue
        d = pd.read_csv(os.path.join(ROOTOUT, f), low_memory=False)
        d = d[(d.slice == slc) & (d.crosses_label == True) & d.ip2.notna()]
        pre = mode if mode == 'B' else lab
        got = set(pre + '|' + d.slice + '|' + d.c1 + '|' + d.c2 + '|' + d.vol
                  + '|' + d.base)
        # under --limit the universe is a handful of candidates, so the diff has
        # to be taken against the SAME handful or it reports the other 3,475 as
        # having "left" a field they were never compared with
        old |= (got & lim) if lim is not None else got
    new = set(C.sid)
    rows = []
    for sid in sorted(old | new):
        rows.append(dict(sid=sid, slice=sid.split('|')[0],
                         in_contaminated=sid in old, in_clean=sid in new,
                         status=('stays' if sid in old and sid in new else
                                 ('ENTERS' if sid in new else 'LEAVES'))))
    F = pd.DataFrame(rows)
    F.to_csv(DIFF, index=False)
    print('\n  FIELD DIFF vs the contaminated 3,485:', flush=True)
    piv = F.pivot_table(index='slice', columns='status', values='sid',
                        aggfunc='count', fill_value=0)
    print(piv.to_string(), flush=True)
    print('  totals: %s' % F.status.value_counts().to_dict(), flush=True)
    print('  contaminated %d -> clean %d ; overlap %d (%.1f%% of the old field '
          'survives)' % (len(old), len(new), len(old & new),
                         100.0 * len(old & new) / max(len(old), 1)), flush=True)
    print('DONE in %.1f min' % ((time.time() - t0) / 60), flush=True)


if __name__ == '__main__':
    main()
