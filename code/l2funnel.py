import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""FUNNEL TEST on the refit smoke's existing tunes (Jack, 21 Sep). No new tunes.

For each rolling window: gate 2's bars (crosses_label: n >= 50, expectancy >= 0.08,
PF >= 1.25, Sharpe >= 0.5, Sortino >= 0.7, Calmar >= 0.6) applied to each of the
250 on its TUNING-window record under its fresh settings -> passers / non-passers.
On the NEXT year, untouched: median R per trade, share positive, pooled PF for
each group; Spearman rank correlation of the tuning-window record vs the
next-year record on five yardsticks (Sortino, expectancy, PF, Calmar, gate-3
composite = count of gate-3 bars cleared). Then the passers pooled across the
five windows as one rolling book on the fixed kernel, always-on and routed.

    --stage score   re-score the banked settings for the full metric set (Sharpe,
                    Sortino, Calmar, max DD are not in the bank), routed and
                    always-on, tuning window and next year; ~1 s per (sid, window)
    --stage funnel  the tables above -> results/funnel_*.csv
    --stage book    write the passers-only marks pickles (per step) for the walk
"""
import argparse, json, time
import numpy as np, pandas as pd
from scipy.stats import spearmanr
import l2sweep as S
import l2tune as T
import l2refit as RF
import l2gate3 as G3

SUF = '_refit_smoke'
WIN = '2011-2015:2016,2012-2016:2017,2013-2017:2018,2014-2018:2019,2015-2019:2020'
YARDS = ('sortino', 'expectancy_R', 'profit_factor', 'calmar', 'gate3_composite')
KEEP = ('n', 'expectancy_R', 'total_R', 'profit_factor', 'sharpe', 'sortino', 'calmar', 'max_dd_R', 'win_rate', 'avg_win_R', 'avg_loss_R')


def g3_composite(a):
    """count of gate-3 bars cleared on this record (0-5); max_dd_frac = max DD / gross profit"""
    gp = a['avg_win_R'] * a['win_rate'] * a['n'] if np.isfinite(a['avg_win_R']) else np.nan
    ddf = a['max_dd_R'] / gp if gp and gp > 0 else np.inf
    return int(a['expectancy_R'] >= G3.BARS['expectancy_R']) + int(a['profit_factor'] >= G3.BARS['profit_factor']) + \
        int(np.nan_to_num(a['sortino'], nan=-9) >= G3.BARS['sortino']) + int(a['calmar'] >= G3.BARS['calmar']) + int(ddf <= G3.BARS['max_dd_frac'])


def score_worker(args):
    i, n, wins = args
    S.WINDOWS = dict(S.WINDOWS); S.WINDOWS.update(RF.windows_table(wins))
    S.load_costs(); T.ACCT_OBJECTIVE = True
    A = pd.read_csv(os.path.join(ROOTOUT, 'refit_settings%s.csv' % SUF), low_memory=False)
    A = A[[RF.shard_of(s, n) == i for s in A.sid]]
    D = pd.read_csv(os.path.join(ROOTOUT, 'refit_pilot_sample.csv'), low_memory=False).set_index('sid')
    sc = T.Scorer(); rows = []; t0 = time.time()
    for k, r in enumerate(A.itertuples(), 1):
        cfg = D.loc[r.sid]; combo = RF.combo_of(cfg); sn, code, plan = RF.slice_bits(cfg)
        ip = json.loads(r.ip); rk = json.loads(r.risk)
        bw, tw = 'B' + r.window, 'T' + r.window
        row = dict(sid=r.sid, slice=r.slice, window=r.window)
        for routed in (True, False):
            out = sc.score(combo, ip, rk, cfg['mode'], sn, code, plan, (bw, tw), routed=routed)
            tag = 'routed' if routed else 'allon'
            for wn, key in ((bw, 'build'), (tw, 'trade')):
                a = out.get(wn)
                for kk in KEEP:
                    row['%s_%s_%s' % (tag, key, kk)] = (a[kk] if a else (0 if kk == 'n' else np.nan))
                row['%s_%s_g3' % (tag, key)] = g3_composite(a) if a else 0
                row['%s_%s_pass2' % (tag, key)] = bool(a and a['n'] >= S.MIN_TRADES_BLIND and T.crosses_label(dict(a, n_w2=a['n'], n_w3=a['n'])))
        rows.append(row)
        if k % 50 == 0:
            print('  shard %d: %d/%d  %.1f s each' % (i, k, len(A), (time.time() - t0) / k), flush=True)
    pd.DataFrame(rows).to_csv(os.path.join(ROOTOUT, 'funnel_scores%s_s%02d.csv' % (SUF, i)), index=False)
    return i


def load_scores():
    import glob
    fs = sorted(glob.glob(os.path.join(ROOTOUT, 'funnel_scores%s_s[0-9][0-9].csv' % SUF)))
    F = pd.concat([pd.read_csv(f) for f in fs], ignore_index=True)
    F.to_csv(os.path.join(ROOTOUT, 'funnel_scores%s.csv' % SUF), index=False)
    return F


def pooled_pf(g, tag):
    gp = (g['%s_trade_avg_win_R' % tag].fillna(0) * g['%s_trade_win_rate' % tag].fillna(0) * g['%s_trade_n' % tag]).sum()
    gl = (-g['%s_trade_avg_loss_R' % tag].fillna(0) * (1 - g['%s_trade_win_rate' % tag].fillna(0)) * g['%s_trade_n' % tag]).sum()
    return gp / gl if gl > 0 else np.nan


def funnel(F, wins):
    rows, corr = [], []
    for tag in ('routed', 'allon'):
        for w in wins:
            g = F[F.window == w['name']]
            ok = g['%s_trade_n' % tag] > 0
            p = g['%s_build_pass2' % tag].astype(bool)
            for lab, m in (('passers', p & ok), ('non-passers', ~p & ok), ('all', ok)):
                gg = g[m]; e = gg['%s_trade_expectancy_R' % tag]
                rows.append(dict(stream=tag, window=w['name'], trade_year=w['trade'][0], group=lab, n=int(len(gg)),
                                 build_median_R=float(gg['%s_build_expectancy_R' % tag].median()) if len(gg) else np.nan,
                                 trade_median_R=float(e.median()) if len(gg) else np.nan, share_positive=float((e > 0).mean()) if len(gg) else np.nan,
                                 pooled_PF=pooled_pf(gg, tag) if len(gg) else np.nan, median_trades=float(gg['%s_trade_n' % tag].median()) if len(gg) else np.nan))
            for y in YARDS:
                a = g['%s_build_%s' % (tag, y if y != 'gate3_composite' else 'g3')].astype(float); b = g['%s_trade_%s' % (tag, y if y != 'gate3_composite' else 'g3')].astype(float)
                m = ok & a.notna() & b.notna() & np.isfinite(a) & np.isfinite(b)
                rho, pv = spearmanr(a[m], b[m]) if m.sum() > 5 else (np.nan, np.nan)
                corr.append(dict(stream=tag, window=w['name'], yardstick=y, n=int(m.sum()), spearman=float(rho), p=float(pv)))
        # pooled across windows
        ok = F['%s_trade_n' % tag] > 0; p = F['%s_build_pass2' % tag].astype(bool)
        for lab, m in (('passers', p & ok), ('non-passers', ~p & ok), ('all', ok)):
            gg = F[m]; e = gg['%s_trade_expectancy_R' % tag]
            rows.append(dict(stream=tag, window='POOLED', trade_year=0, group=lab, n=int(len(gg)), build_median_R=float(gg['%s_build_expectancy_R' % tag].median()),
                             trade_median_R=float(e.median()), share_positive=float((e > 0).mean()), pooled_PF=pooled_pf(gg, tag), median_trades=float(gg['%s_trade_n' % tag].median())))
        for y in YARDS:
            a = F['%s_build_%s' % (tag, y if y != 'gate3_composite' else 'g3')].astype(float); b = F['%s_trade_%s' % (tag, y if y != 'gate3_composite' else 'g3')].astype(float)
            m = ok & a.notna() & b.notna() & np.isfinite(a) & np.isfinite(b)
            rho, pv = spearmanr(a[m], b[m])
            corr.append(dict(stream=tag, window='POOLED', yardstick=y, n=int(m.sum()), spearman=float(rho), p=float(pv)))
    R = pd.DataFrame(rows); C = pd.DataFrame(corr)
    R.to_csv(os.path.join(ROOTOUT, 'funnel_groups%s.csv' % SUF), index=False); C.to_csv(os.path.join(ROOTOUT, 'funnel_rankcorr%s.csv' % SUF), index=False)
    print('\n=== FUNNEL: gate-2 bars on the tuning window -> the next year ===', flush=True)
    print(R.to_string(index=False, float_format=lambda v: '%8.3f' % v), flush=True)
    print('\n=== RANK CORRELATION tuning window vs next year (Spearman) ===', flush=True)
    print(C.pivot_table(index=['stream', 'window'], columns='yardstick', values='spearman').round(3).to_string(), flush=True)
    return R, C


def book(F, wins):
    """passers-only marks pickles: at each step keep the (sid, step) rows of the strategies that passed gate 2
    on that step's tuning window (routed record for the routed book, always-on record for the always-on book)"""
    for src, tag in (('_refit_smoke', 'allon'), ('_refit_smoke_routed', 'routed')):
        T_ = pd.read_pickle(os.path.join(ROOTOUT, 'wf_trades%s.pkl' % src)); M_ = pd.read_pickle(os.path.join(ROOTOUT, 'wf_marks%s.pkl' % src))
        keep = set()
        for si, w in enumerate(wins):
            g = F[(F.window == w['name']) & F['%s_build_pass2' % tag].astype(bool)]
            keep |= set((s, si + 1) for s in g.sid)
        kT = pd.MultiIndex.from_arrays([T_.sid.astype(str), T_.step.astype(int)]).isin(keep)
        kM = pd.MultiIndex.from_arrays([M_.sid.astype(str), M_.step.astype(int)]).isin(keep)
        To, Mo = T_[kT].reset_index(drop=True), M_[kM].reset_index(drop=True)
        for c in ('sid', 'pair'):
            To[c] = To[c].astype(str).astype('category'); Mo[c] = Mo[c].astype(str).astype('category')
        out = '_funnel_%s' % tag
        To.to_pickle(os.path.join(ROOTOUT, 'wf_trades%s.pkl' % out)); Mo.to_pickle(os.path.join(ROOTOUT, 'wf_marks%s.pkl' % out))
        # the field file for the walk: every strategy that passes on at least one window
        D = pd.read_csv(os.path.join(ROOTOUT, 'refit_pilot_sample.csv'), low_memory=False)
        D[D.sid.isin(set(s for s, _ in keep))].to_csv(os.path.join(ROOTOUT, 'funnel_field_%s.csv' % tag), index=False)
        print('%s: %d (sid, step) passers, %d strategies, %d trades, %d marks -> wf_*%s.pkl; per step %s'
              % (tag, len(keep), len(set(s for s, _ in keep)), len(To), len(Mo), out, To.groupby('step').sid.nunique().to_dict()), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', required=True, choices=['score', 'funnel', 'book'])
    ap.add_argument('--jobs', type=int, default=4)
    a = ap.parse_args()
    wins = RF.parse_windows(WIN)
    if a.stage == 'score':
        import multiprocessing as mp
        with mp.get_context('spawn').Pool(a.jobs) as pool:
            pool.map(score_worker, [(i, a.jobs, wins) for i in range(a.jobs)])
        F = load_scores(); print('scored %d (sid, window) rows' % len(F), flush=True)
    elif a.stage == 'funnel':
        F = pd.read_csv(os.path.join(ROOTOUT, 'funnel_scores%s.csv' % SUF)); funnel(F, wins)
    else:
        F = pd.read_csv(os.path.join(ROOTOUT, 'funnel_scores%s.csv' % SUF)); book(F, wins)
    print('FUNNEL STAGE %s COMPLETE' % a.stage.upper(), flush=True)


if __name__ == '__main__':
    main()
