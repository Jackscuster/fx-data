import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""THE GATE 3 CUT, as a build product.

This existed only as an inline script typed by hand on 2026-09-07. The chain
therefore refreshed the W3-only SCORES and then read a stale verdicts file,
producing a team labelled ADOPTED that was in fact the gate 2 team. A step that
only ever ran by hand is a step the chain cannot run.

--settings adopted   use the fine-tune's ADOPTED settings where a strategy has
                     an adopted W3ONLY row, and gate 2's otherwise
--settings gate2     gate 2's settings throughout

BINDING BARS (Sharpe retired, reported only):
    expectancy >= 0.15R, PF >= 1.5, Sortino >= 1.3, Calmar >= 1.0,
    max DD <= 10% of the strategy's own gross profit
"""
import glob, json, argparse
import numpy as np, pandas as pd
import l2gate3 as G3

BARS = G3.BARS
SHARPE_BAR = getattr(G3, 'SHARPE_BAR', 1.1)


def load_scores():
    fs = sorted(glob.glob(os.path.join(ROOTOUT, 'gate2_w3only_scores_*.csv')))
    if not fs:
        raise SystemExit('no W3-only scores; run code/l2clean3.py first')
    d = pd.concat([pd.read_csv(f, low_memory=False) for f in fs], ignore_index=True)
    return d[d.sid != 'sid'].drop_duplicates('sid').reset_index(drop=True)


def adopted_map():
    """sid -> the fine-tune's adopted W3 metrics and settings, where one exists."""
    fs = sorted(glob.glob(os.path.join(ROOTOUT, 'gate3ft_costed_v4', '*.csv')))
    if not fs:
        return {}
    # READ TOLERANTLY. Nine shards append to these files continuously, so a read
    # can land mid-write and raise. A skipped file would silently drop adopted
    # settings, so each failure is COUNTED and reported rather than ignored.
    parts, bad = [], 0
    for f in fs:
        try:
            parts.append(pd.read_csv(f, low_memory=False))
        except Exception:
            bad += 1
    if bad:
        print('  WARNING: %d of %d bank files unreadable this pass '
              '(shards are writing); adopted settings may be incomplete'
              % (bad, len(fs)), flush=True)
    if not parts:
        return {}
    d = pd.concat(parts, ignore_index=True)
    d = d[(d.get('compare_basis') == 'W3ONLY') & (d.adopted == True)]
    d = d.drop_duplicates('sid', keep='last')
    return {r['sid']: r for r in d.to_dict('records')}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--settings', default='gate2', choices=['gate2', 'adopted'])
    ap.add_argument('--out', default=None)
    a = ap.parse_args()
    D = load_scores()
    for c in D.columns:
        if c.startswith('w3_'):
            D[c] = pd.to_numeric(D[c], errors='coerce')
    n_sub = 0
    if a.settings == 'adopted':
        AD = adopted_map()
        # substitute the adopted candidate's W3 metrics and settings
        for i, sid in enumerate(D.sid.values):
            r = AD.get(sid)
            if r is None:
                continue
            n_sub += 1
            for src, dst in (('cw3_total_R', 'w3_total_R'),
                             ('cw3_max_dd_R', 'w3_max_dd_R'),
                             ('cw3_sortino', 'w3_sortino'),
                             ('cw3_sharpe', 'w3_sharpe'),
                             ('cw3_n', 'w3_n')):
                if src in r and r[src] == r[src]:
                    D.at[i, dst] = r[src]
            for k in ('atr_len', 'atr_mult', 'tp_mult', 'trail_mult',
                      'trail_arm', 'be_pct'):
                if 'ft_risk_' + k in r:
                    D.at[i, 'risk_' + k] = r['ft_risk_' + k]
            if isinstance(r.get('ft_ip2'), str):
                D.at[i, 'ip2'] = r['ft_ip2']
        print('adopted settings substituted for %d of %d strategies' % (n_sub, len(D)),
              flush=True)
        # metrics the bank does not carry must be recomputed, not inherited
        for c in ('w3_expectancy_R', 'w3_profit_factor', 'w3_calmar',
                  'w3_win_rate', 'w3_avg_win_R', 'w3_avg_loss_R',
                  'w3_profit_concentration'):
            if c in D.columns:
                D.loc[D.sid.isin(AD), c] = np.nan
        D['w3_expectancy_R'] = D.w3_expectancy_R.fillna(D.w3_total_R / D.w3_n)
        D['w3_calmar'] = D.w3_calmar.fillna(D.w3_total_R / D.w3_max_dd_R)

    gross = (D.w3_avg_win_R * D.w3_win_rate * D.w3_n)
    D['w3_max_dd_frac'] = D.w3_max_dd_R / gross.replace(0, np.nan)
    ok = pd.Series(True, index=D.index)
    fails = {}
    for k, v in BARS.items():
        col = 'w3_' + k
        good = (D[col] <= v) if k == 'max_dd_frac' else (D[col] >= v)
        good = good.fillna(False)
        fails[k] = int((~good).sum())
        ok &= good
    P = D[ok].copy()
    P['verdict'] = 'PASS'
    P['sharpe_only_flag'] = P.w3_sharpe < SHARPE_BAR
    P['settings_basis'] = a.settings
    for c in ('n', 'total_R', 'expectancy_R', 'profit_factor', 'sharpe',
              'sortino', 'calmar', 'max_dd_R', 'win_rate', 'profit_concentration'):
        if 'w3_' + c in P.columns:
            P[c] = P['w3_' + c]
    out = a.out or os.path.join(ROOTOUT, 'gate3_costed_verdicts.csv')
    P.to_csv(out, index=False)
    print('failures by bar: %s' % fails, flush=True)
    print('PASS %d of %d (%.2f%%) -> %s'
          % (len(P), len(D), 100.0 * len(P) / len(D), os.path.basename(out)), flush=True)
    print(P.groupby('src_label').size().to_dict(), flush=True)


if __name__ == '__main__':
    main()
