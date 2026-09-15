import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""REFIT PILOT (Jack, 15 Sep) -- does re-tuning restore per-strategy expectancy
on an unseen year?  250 strategies drawn at random from the four-slice clean
field, stratified by slice.  For each:
    tune on 2011-2015 with gate 2's grids (cap 6, full pass)  -> trade 2016
    tune on 2012-2016 with the same grids                     -> trade 2017
and, for the comparison, the SAME strategies on their 2005-2010 settings
(ip1 / risk1, tuned on W1) traded on 2016 and on 2017.  Reported per window:
median expectancy in R per trade net of costs on the trade year, share of
strategies positive, and retention (trade-year expectancy / tuning-window
expectancy).  Seconds per strategy from the first 10 are printed as they land.

NO BOOK.  Every number is per strategy through l2tune.Scorer -- the engine's
own trades, that strategy's regime filter, costs charged per trade.  The
netting kernel (l2walkfwd.Book) is never touched here, so the vote-timing
leak of HANDOFF 0d cannot reach these numbers.

Resumable: one row per strategy appended as it completes; workers each own a
shard file, merged at the end.  Mac only, --jobs workers.
"""
import argparse, json, time, glob
import numpy as np, pandas as pd
import l2sweep as S
import l2tune as T

FIELD = os.path.join(ROOTOUT, 'gate2_cleanfield_4slice.csv')
OUT = os.path.join(ROOTOUT, 'refit_pilot.csv')
SAMPLE = os.path.join(ROOTOUT, 'refit_pilot_sample.csv')
# the pilot's windows, added to the Scorer's table before it is built
PILOT_WINDOWS = {'P1': ('2011-01-01', '2015-12-31'), 'T1': ('2016-01-01', '2016-12-31'),
                 'P2': ('2012-01-01', '2016-12-31'), 'T2': ('2017-01-01', '2017-12-31')}
STEPS = (('P1', 'T1'), ('P2', 'T2'))
CAP = 6            # decided 14 Sep: one cap for all four slices, a fresh tune not a recovery
SEED = 20260915


def draw_sample(n):
    """n strategies, stratified by slice in the field's own proportions."""
    F = pd.read_csv(FIELD, low_memory=False)
    F = F[F.ip1.notna() & F.risk1.notna()].copy()
    F['lab'] = F['mode'].astype(str) + '-' + F['slice'].astype(str)   # src_label is bare 'B' for mode B; B-chop and B-trend must be separate strata
    rng = np.random.default_rng(SEED)
    share = F.lab.value_counts(normalize=True)
    take = {k: int(round(v * n)) for k, v in share.items()}
    # rounding: fix the total to n on the largest slice
    big = share.idxmax(); take[big] += n - sum(take.values())
    parts = []
    for k, m in take.items():
        g = F[F.lab == k]
        parts.append(g.iloc[rng.choice(len(g), size=m, replace=False)])
    D = pd.concat(parts).reset_index(drop=True)
    D.to_csv(SAMPLE, index=False)
    print('sample: %d strategies -- %s' % (len(D), ', '.join('%s %d' % (k, v) for k, v in take.items())), flush=True)
    return D


def _pick(r, w):
    a = r.get(w)
    return dict(n=a['n'], expectancy_R=a['expectancy_R'], profit_factor=a['profit_factor'],
                total_R=a['total_R'] if 'total_R' in a else a['expectancy_R'] * a['n']) if a else dict(n=0, expectancy_R=np.nan, profit_factor=np.nan, total_R=np.nan)


def one(sc, cfg):
    combo = (cfg['c1'], cfg['c2'], cfg['vol'], cfg['base'], cfg.get('exit_ind') or S.slot_options()['exit_ind'][0])
    sn = cfg['slice']; mode = cfg['mode']
    code = dict((s, c) for s, _, c in S.SLICES)[sn]
    plan = dict((s, p) for s, p, _ in S.SLICES)[sn]
    ip1 = json.loads(cfg['ip1']); rk1 = json.loads(cfg['risk1'])
    row = dict(sid=cfg['sid'], slice=cfg.get('lab', sn), mode=mode)
    wins = ('P1', 'T1', 'P2', 'T2')
    # the 2005-2010 settings on every window
    r0 = sc.score(combo, ip1, rk1, mode, sn, code, plan, wins)
    for w in wins:
        for k, v in _pick(r0, w).items():
            row['ip1_%s_%s' % (w, k)] = v
    # a fresh tune per step, then the trade year under it
    for pw, tw in STEPS:
        t0 = time.time(); n0 = sc.n_eval
        ip, rk, info = T._stage(sc, combo, mode, sn, code, plan, (pw,), CAP, False)
        r = sc.score(combo, ip, rk, mode, sn, code, plan, (pw, tw))
        for w in (pw, tw):
            for k, v in _pick(r, w).items():
                row['tuned_%s_%s' % (w, k)] = v
        row['tune_%s_seconds' % pw] = round(time.time() - t0, 1)
        row['tune_%s_evals' % pw] = sc.n_eval - n0
        row['tune_%s_stage' % pw] = info.get('stage')
        row['tune_%s_ip' % pw] = json.dumps(ip, sort_keys=True)
        row['tune_%s_risk' % pw] = json.dumps(rk, sort_keys=True)
    return row


def shard_path(i):
    return os.path.join(ROOTOUT, 'refit_pilot_s%02d.csv' % i)


def worker(args):
    i, jobs, sids = args
    S.WINDOWS = dict(S.WINDOWS); S.WINDOWS.update(PILOT_WINDOWS)
    S.load_costs(); T.ACCT_OBJECTIVE = True
    D = pd.read_csv(SAMPLE, low_memory=False)
    D = D[D.sid.isin(sids)]
    done = set()
    if os.path.exists(shard_path(i)):
        done = set(pd.read_csv(shard_path(i)).sid)
    D = D[~D.sid.isin(done)]
    sc = T.Scorer()
    t0 = time.time()
    for k, cfg in enumerate(D.to_dict('records'), 1):
        try:
            row = one(sc, cfg)
        except Exception as e:
            print('  shard %d: %s FAILED %s' % (i, cfg['sid'][:60], str(e)[:100]), flush=True)
            continue
        pd.DataFrame([row]).to_csv(shard_path(i), mode='a', index=False, header=not os.path.exists(shard_path(i)))
        el = time.time() - t0
        print('  shard %d: %d/%d  %.0f s per strategy (both tunes)  tune P1 %.0fs P2 %.0fs  T1 tuned %+.3f ip1 %+.3f  T2 tuned %+.3f ip1 %+.3f'
              % (i, k, len(D), el / k, row['tune_P1_seconds'], row['tune_P2_seconds'],
                 row['tuned_T1_expectancy_R'], row['ip1_T1_expectancy_R'], row['tuned_T2_expectancy_R'], row['ip1_T2_expectancy_R']), flush=True)
    return i


def report(P):
    print('\n=== REFIT PILOT: %d strategies ===' % len(P), flush=True)
    rows = []
    for pw, tw in STEPS:
        for src in ('ip1', 'tuned'):
            e = P['%s_%s_expectancy_R' % (src, tw)]; n = P['%s_%s_n' % (src, tw)]
            et = P['%s_%s_expectancy_R' % (src, pw)]
            ok = e.notna() & (n > 0)
            ret = (e / et).where(et > 0)
            rows.append(dict(step='tune %s -> trade %s' % (pw, tw), settings=('2005-2010 (ip1)' if src == 'ip1' else 'fresh tune on %s' % pw),
                             n_strategies=int(ok.sum()), median_R_per_trade=float(e[ok].median()), mean_R_per_trade=float(e[ok].mean()),
                             share_positive=float((e[ok] > 0).mean()), median_trades=float(n[ok].median()),
                             tuning_window_median_R=float(et[ok].median()), median_retention=float(ret[ok].median()),
                             share_retention_over_20pct=float((ret[ok] > 0.2).mean())))
        d = (P['tuned_%s_expectancy_R' % tw] - P['ip1_%s_expectancy_R' % tw]).dropna()
        rows.append(dict(step='tune %s -> trade %s' % (pw, tw), settings='DIFFERENCE tuned - ip1', n_strategies=int(len(d)),
                         median_R_per_trade=float(d.median()), mean_R_per_trade=float(d.mean()), share_positive=float((d > 0).mean())))
    R = pd.DataFrame(rows)
    print(R.to_string(index=False, float_format=lambda v: '%8.3f' % v), flush=True)
    R.to_csv(os.path.join(ROOTOUT, 'refit_pilot_summary.csv'), index=False)
    # by slice
    for pw, tw in STEPS:
        g = P.groupby('slice').agg(ip1_median=('ip1_%s_expectancy_R' % tw, 'median'), tuned_median=('tuned_%s_expectancy_R' % tw, 'median'),
                                  ip1_pos=('ip1_%s_expectancy_R' % tw, lambda s: (s > 0).mean()), tuned_pos=('tuned_%s_expectancy_R' % tw, lambda s: (s > 0).mean()), n=('sid', 'size'))
        print('\nby slice, trade %s:' % tw, flush=True); print(g.to_string(float_format=lambda v: '%8.3f' % v), flush=True)
    sec = pd.concat([P['tune_P1_seconds'], P['tune_P2_seconds']])
    print('\nseconds per tune: mean %.0f  median %.0f  p90 %.0f  (n %d);  evals per tune: median %.0f' % (sec.mean(), sec.median(), sec.quantile(0.9), len(sec), pd.concat([P['tune_P1_evals'], P['tune_P2_evals']]).median()), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--n', type=int, default=250)
    ap.add_argument('--jobs', type=int, default=4)
    ap.add_argument('--limit', type=int, default=0, help='smoke test: only this many strategies')
    ap.add_argument('--report-only', action='store_true')
    a = ap.parse_args()
    if not a.report_only:
        D = draw_sample(a.n) if not os.path.exists(SAMPLE) else pd.read_csv(SAMPLE, low_memory=False)
        if a.limit:
            D = D.head(a.limit)
        sids = list(D.sid)
        shards = [(i, a.jobs, sids[i::a.jobs]) for i in range(a.jobs)]
        t0 = time.time()
        if a.jobs > 1:
            import multiprocessing as mp
            with mp.get_context('spawn').Pool(a.jobs) as pool:
                pool.map(worker, shards)
        else:
            worker(shards[0])
        print('pilot tunes done in %.1f min' % ((time.time() - t0) / 60), flush=True)
    parts = [pd.read_csv(f) for f in sorted(glob.glob(os.path.join(ROOTOUT, 'refit_pilot_s[0-9][0-9].csv')))]
    if not parts:
        raise SystemExit('no shard output')
    P = pd.concat(parts, ignore_index=True).drop_duplicates('sid')
    P.to_csv(OUT, index=False)
    report(P)
    print('REFIT PILOT COMPLETE', flush=True)


if __name__ == '__main__':
    main()
