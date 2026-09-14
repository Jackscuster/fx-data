import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""THE AGREEMENT SWEET SPOT. Two sweeps on the routed NO_CUT book, full range,
whole curve written, no preset list.

  --stage minvotes   the minimum |net votes| a (pair, day) needs before the
                     book takes a position, from 1 up to where the book stops
                     trading; at every step a RANDOM-N control that keeps the
                     same number of rows chosen at random (10 draws; 25 on the
                     winner). Reported per step: median year, worst year, max
                     DD, positions opened, spread paid (the return the same
                     book makes with costs set to zero, minus the costed
                     return), and the share of entries and of cost coming from
                     lone voices (|net| = 1).
  --stage curveshape the fitted build-year size curve against four stated
                     shapes -- flat, linear in the vote fraction, sqrt, square.

The netting hooks are in l2walkfwd.Book.net (NET_MIN_VOTES, NET_ROW_MASK,
CURVE_MODE). Everything is sized on the build blocks as always.
"""
import argparse, time
import numpy as np, pandas as pd
import l2walkfwd as W
import l2returns as RET

IDENT = {y: y for y in W.YEARS}


def load(tag):
    W.TAG = tag; os.environ['WF_TAG'] = tag
    W.TRADES_F = W.OUT('wf_trades.pkl'); W.MARKS_F = W.OUT('wf_marks.pkl')
    T = pd.read_pickle(W.TRADES_F); M = pd.read_pickle(W.MARKS_F)
    return T, M, W.trade_year_sums(M)


def one(T, TY, M, dipb, dayb):
    r = W.walk(T, TY, M, IDENT, dipb, dayb, ['ALLPASS'], nocut=True)
    k, cuts, x, dy = r['ALLPASS']
    k['positions_opened'] = int(sum(c['trades_per_year'] for c in cuts) * 0)  # filled below from the book
    return k, cuts


def vote_profile(T, M):
    """|net votes| per (pair, day) row of the whole-field book on the trade years
    -- to set the sweep's range from the data, and the lone-voice share."""
    allp = sorted(set(T.sid.astype(str)))
    B = W.Book(M[M.sid.isin(allp)], allp)
    w = np.ones(len(B.members), np.float32)
    net = np.abs(B.L @ w - B.Sm @ w)
    tr = np.isin(B.dyears, list(range(2016, 2021)))[B.dpos]
    v = net[tr]
    return v


def stage_minvotes(tag, field, n_rand, n_rand_winner, jobs, grid_override=''):
    T, M, TY = load(tag)
    v = vote_profile(T, M)
    vmax = int(np.percentile(v[v >= 1], 99.5))
    grid = sorted(set([1, 2, 3] + [int(x) for x in np.geomspace(4, vmax, 12)]))
    if grid_override:
        grid = [int(x) for x in grid_override.split(',')]
    print('  |net votes| on trade-year rows: median %.0f, p90 %.0f, p99.5 %.0f -> grid %s' % (np.median(v[v >= 1]), np.percentile(v[v >= 1], 90), vmax, grid), flush=True)
    lone = float((v == 1).mean())
    print('  lone voices (|net| = 1): %.1f%% of traded rows' % (100 * lone), flush=True)
    # zero-cost twin of the book, for spread paid
    T0, M0 = RET.recost(T, M, field, lambda p: 0.0, 'zero-cost twin')
    TY0 = W.trade_year_sums(M0)
    rows = []
    for bt, dipb, dayb in W.BUDGETS:
        for k in grid:
            W.NET_MIN_VOTES = float(k) - 0.5 + 0.5; W.NET_ROW_MASK = None
            W.NET_MIN_VOTES = k - 0.5 if k > 1 else 0.5
            t0 = time.time()
            kk, cuts = one(T, TY, M, dipb, dayb)
            k0, _ = one(T0, TY0, M0, dipb, dayb)
            nrows = int(sum(c['position_days'] for c in cuts))
            rows.append(dict(budget=bt, min_votes=k, control='real', draw=-1, median_year_pct=kk['median_year_pct'], worst_year_pct=kk['worst_year_pct'],
                             max_dd_pct=kk['max_dd_pct'], worst_day_pct=kk['worst_day_pct'], dip95_pct=kk['dip95_pct'], profit_factor=kk['profit_factor'],
                             sortino=kk['sortino'], position_days=nrows, trades_per_year=float(np.mean([c['trades_per_year'] for c in cuts])),
                             spread_paid_pct_yr=(k0['median_year_pct'] - kk['median_year_pct']), zero_cost_median=k0['median_year_pct']))
            print('    %-6s min_votes %3d: median %6.3f%%  worst %6.3f%%  maxDD %5.2f%%  spread %5.2f%%/yr  trades/yr %8.0f  (%.0fs)'
                  % (bt, k, kk['median_year_pct'], kk['worst_year_pct'], kk['max_dd_pct'], k0['median_year_pct'] - kk['median_year_pct'], rows[-1]['trades_per_year'], time.time() - t0), flush=True)
            if nrows < 1:
                print('    book stops trading at min_votes %d' % k, flush=True); break
            # random-N control: same count of active rows, chosen at random. The
            # count is the share of rows with |net| >= k among active rows.
            share = float((v >= k).mean()) if k > 1 else 1.0
            if k > 1:
                for d in range(n_rand):
                    rng = np.random.default_rng(20260914 + d)
                    W.NET_MIN_VOTES = 0.5
                    nrow_total = None
                    def mask_for(B):
                        return rng.random(B.nd if False else 0) < share
                    # the mask must match the Book's row count; walk() builds the
                    # Book itself, so the mask is drawn per row inside net() via a
                    # callable seeded here
                    W.NET_ROW_MASK = ('random', share, 20260914 + d)
                    kr, _ = one(T, TY, M, dipb, dayb)
                    rows.append(dict(budget=bt, min_votes=k, control='random', draw=d, median_year_pct=kr['median_year_pct'], worst_year_pct=kr['worst_year_pct'],
                                     max_dd_pct=kr['max_dd_pct'], worst_day_pct=kr['worst_day_pct'], dip95_pct=kr['dip95_pct'], profit_factor=kr['profit_factor'], sortino=kr['sortino']))
                W.NET_ROW_MASK = None
            pd.DataFrame(rows).to_csv(W.OUT('agree_minvotes.csv'), index=False)
    W.NET_MIN_VOTES = 0.5; W.NET_ROW_MASK = None
    O = pd.DataFrame(rows); O.to_csv(W.OUT('agree_minvotes.csv'), index=False)
    print(O[O.control == 'real'][['budget', 'min_votes', 'median_year_pct', 'worst_year_pct', 'max_dd_pct', 'spread_paid_pct_yr', 'position_days']].to_string(index=False, float_format=lambda v: '%8.3f' % v), flush=True)
    R = O[O.control == 'random'].groupby(['budget', 'min_votes']).median_year_pct.agg(['mean', 'std', 'max'])
    print('random-N control:', flush=True); print(R.to_string(float_format=lambda v: '%8.3f' % v), flush=True)


def stage_curveshape(tag):
    T, M, TY = load(tag)
    rows = []
    for mode in ('fitted', 'flat', 'linear', 'sqrt', 'square'):
        W.CURVE_MODE = mode
        for bt, dipb, dayb in W.BUDGETS:
            kk, cuts = one(T, TY, M, dipb, dayb)
            kk.update(curve=mode, budget=bt); rows.append(kk)
            print('    %-7s %-6s median %6.3f%%  worst %6.3f%%  maxDD %5.2f%%  DIP95 %5.2f%%  PF %.2f  Sortino %.2f' % (mode, bt, kk['median_year_pct'], kk['worst_year_pct'], kk['max_dd_pct'], kk['dip95_pct'], kk['profit_factor'], kk['sortino']), flush=True)
    W.CURVE_MODE = 'fitted'
    pd.DataFrame(rows).to_csv(W.OUT('agree_curveshape.csv'), index=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', required=True, choices=['minvotes', 'curveshape'])
    ap.add_argument('--suffix', default='_routed_tirexcl_actweak')
    ap.add_argument('--field-file', default=os.path.join(ROOTOUT, 'gate2_cleanfield_4slice.csv'))
    ap.add_argument('--n-rand', type=int, default=10)
    ap.add_argument('--n-rand-winner', type=int, default=25)
    ap.add_argument('--jobs', type=int, default=1)
    ap.add_argument('--grid', default='', help='override the vote grid, e.g. 1,3,10 (testing only)')
    a = ap.parse_args()
    W.S.load_costs(); os.environ['WF_FIELD_FILE'] = os.path.abspath(a.field_file); os.environ['WF_SLICES'] = 'A-trend,A-chop,B-chop,B-trend'
    t0 = time.time(); print('=== %s on %s ===' % (a.stage, a.suffix), flush=True)
    if a.stage == 'minvotes':
        F = W.load_field(('A-trend', 'A-chop', 'B-chop', 'B-trend'), a.field_file)
        stage_minvotes(a.suffix, F, a.n_rand, a.n_rand_winner, a.jobs, a.grid)
    else:
        stage_curveshape(a.suffix)
    print('=== %s done in %.1f min ===' % (a.stage, (time.time() - t0) / 60), flush=True)


if __name__ == '__main__':
    main()
