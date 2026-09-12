import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""PER-SLICE BREAKDOWN — each slice walked ON ITS OWN.

WHY IT IS A SEPARATE WALK AND NOT AN ATTRIBUTION. The book is NETTED: a long
EURUSD in one member cancels a short EURUSD in another before a single unit of
risk is sized. There is therefore no such thing as "A-trend's share of the
book's PnL" -- the netting decides how much position each member ends up
carrying, and that depends on every OTHER member present. Splitting the netted
daily series by slice would require choosing an attribution rule, and the choice
would drive the answer.

What IS well defined is each slice walked alone: same cut, same build years,
same budgets, same sizing, its own members only. That answers the question the
breakdown is for -- is the result carried by one slice -- without inventing an
attribution.

Reads the clean-field engine output. Writes
results/walkforward_perslice_3slice<TAG>.csv.
"""
import argparse, time
import numpy as np, pandas as pd
import l2walkfwd as W


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--suffix', default='_cleanfield')
    ap.add_argument('--field-file', default=os.path.join(ROOTOUT, 'gate2_cleanfield.csv'))
    ap.add_argument('--slices', default=','.join(W.SLICES3))
    ap.add_argument('--structures', default='ALLPASS')
    a = ap.parse_args()

    W.S.load_costs()
    W.TAG = a.suffix
    os.environ['WF_TAG'] = a.suffix
    os.environ['WF_FIELD_FILE'] = os.path.abspath(a.field_file)
    W.TRADES_F = W.OUT('wf_trades.pkl'); W.MARKS_F = W.OUT('wf_marks.pkl')
    slices = [x for x in a.slices.split(',') if x]
    structures = [x for x in a.structures.split(',') if x]

    T = pd.read_pickle(W.TRADES_F); M = pd.read_pickle(W.MARKS_F)
    print('FIELD FILE %s (per-slice breakdown)' % os.path.abspath(a.field_file), flush=True)
    print('  loaded %d trades, %d marks, %d strategies'
          % (len(T), len(M), T.sid.nunique()), flush=True)

    lab_T = T.sid.map(W.field_label)
    lab_M = M.sid.map(W.field_label)
    ident = {y: y for y in W.YEARS}
    rows = []
    for sl in slices:
        Ts = T[lab_T == sl].copy(); Ms = M[lab_M == sl].copy()
        n = Ts.sid.nunique()
        print('\n=== %s: %d strategies ===' % (sl, n), flush=True)
        if n < 2:
            raise SystemExit('%s: %d strategies -- refusing to walk' % (sl, n))
        TYs = W.trade_year_sums(Ms)
        for bt, dipb, dayb in W.BUDGETS:
            t0 = time.time()
            R = W.walk(Ts, TYs, Ms, ident, dipb, dayb, structures)
            for s, (k, cuts, x, dy) in R.items():
                k.update(slice=sl, budget=bt, structure=s, field_n=n,
                         dip_budget=dipb, day_budget=dayb, kind='per_slice',
                         expectancy_pct_per_day=float(np.mean(x)))
                rows.append(k)
                print('    %-8s %-6s %-9s median %7.3f%%  worst %7.3f%%  '
                      'maxDD %5.2f%%  PF %.2f  members %d/%d  (%.1f min)'
                      % (sl, bt, s, k['median_year_pct'], k['worst_year_pct'],
                         k['max_dd_pct'], k['profit_factor'],
                         k['members_step1'], k['members_step2'],
                         (time.time() - t0) / 60), flush=True)
            pd.DataFrame(rows).to_csv(
                W.OUT('walkforward_perslice_3slice.csv'), index=False)
    out = pd.DataFrame(rows)
    out.to_csv(W.OUT('walkforward_perslice_3slice.csv'), index=False)
    print('\nwrote %s, %d rows' % (W.OUT('walkforward_perslice_3slice.csv'), len(out)),
          flush=True)


if __name__ == '__main__':
    main()
