import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""THE MODE INDEX — what the app reads to organise gate 2 by mode and slice.

Writes results/modes_index.json:

    modes -> A|B|C -> slices -> trend|chop -> {status, headline, top[]}

STATUS IS NEVER INFERRED FROM ABSENCE. A missing file could mean queued,
running, or lost, and the app must not have to guess which. Status comes from
results/modes_status.json, which a human (or the driver) sets, and defaults to
'queued'. A slice with no leaderboard is reported as running or queued, NEVER
dropped -- an absent slot that silently disappears reads as "there is nothing
here", which is the one thing it does not mean.

Nothing here recomputes a metric. Every number is carried from the committed
leaderboard and clean-view CSVs, so the app cannot disagree with the files.
"""
import json, glob
import numpy as np, pandas as pd

MODES = [('A', 'Mode A', 'exit on C1 flip'),
         ('B', 'Mode B', 'exit on baseline cross'),
         ('C', 'Mode C', 'exit on a dedicated exit indicator')]
SLICES = [('trend', 'two-leg plan on trending days'),
          ('chop', 'one-leg plan on ranging days')]
TOPN = 20

RISK = ['risk_atr_len', 'risk_atr_mult', 'risk_tp_mult', 'risk_trail_mult',
        'risk_trail_arm', 'risk_be_pct']
MET = ['ex_n', 'ex_total_R', 'ex_expectancy_R', 'ex_win_rate', 'ex_profit_factor',
       'ex_sharpe', 'ex_sortino', 'ex_max_dd_R', 'ex_ulcer_R', 'ex_calmar',
       'ex_max_trade_share', 'cr_n', 'cr_total_R', 'all_total_R',
       'crisis_share_of_total_R', 'net_of_structure_R']


def _num(v):
    """JSON cannot hold NaN/Inf. Those become null, which the app prints as a
    dash under the standing full-metric-set rule -- never an omitted field."""
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return str(v)
    return None if not np.isfinite(f) else round(f, 6)


def _lb(mode, sl):
    """The leaderboard for one mode+slice. Mode B's is one file covering both
    slices; mode A's is written per slice. Both are read the same way."""
    for f in ('gate2_mode%s_%s_leaderboard.csv' % (mode, sl),
              'gate2_mode%s_leaderboard.csv' % mode):
        p = os.path.join(ROOTOUT, f)
        if os.path.exists(p):
            D = pd.read_csv(p, low_memory=False)
            D = D[D.slice == sl]
            if len(D):
                return D.sort_values('rank'), f
    return None, None


def _clean(mode, sl):
    for f in ('gate2_mode%s_%s_leaderboard_clean.csv' % (mode, sl),
              'gate2_mode%s_leaderboard_clean.csv' % mode):
        p = os.path.join(ROOTOUT, f)
        if os.path.exists(p):
            C = pd.read_csv(p)
            C = C[C.slice == sl] if 'slice' in C.columns else C
            if len(C):
                return C
    return None


def _tuned(mode, sl):
    """Population counts, from the tuner's own output rather than recounted."""
    for f in ('gate2_tuned_mode%s_%s.csv' % (mode, sl),
              'gate2_tuned_mode%s.csv' % mode):
        p = os.path.join(ROOTOUT, f)
        if os.path.exists(p):
            T = pd.read_csv(p, usecols=['slice', 'crosses_label'], low_memory=False)
            T = T[T.slice == sl]
            if len(T):
                return int(len(T)), int((T.crosses_label == True).sum())
    return None, None


def cards(mode, sl, n=TOPN):
    L, src = _lb(mode, sl)
    if L is None:
        return [], None
    C = _clean(mode, sl)
    key = ['c1', 'c2', 'vol', 'base']
    out = []
    for r in L.head(n).to_dict('records'):
        c = {k: r.get(k) for k in ('c1', 'c2', 'vol', 'base', 'exit_ind',
                                   'exit_ind_t', 'slice', 'rank')}
        c['risk'] = {k.replace('risk_', ''): _num(r.get(k)) for k in RISK}
        c['metrics'] = {k: _num(r.get(k)) for k in MET}
        c['peg_pct'] = c['lowvol_pct'] = c['clean_R'] = None
        if C is not None:
            m = C
            for k in key:
                m = m[m[k] == r[k]]
            if len(m):
                m = m.iloc[0]
                nn = m.get('n') or 0
                c['peg_pct'] = _num(100.0 * m.get('peg_n', 0) / nn) if nn else None
                c['lowvol_pct'] = _num(100.0 * m.get('lv_n', 0) / nn) if nn else None
                c['clean_R'] = _num(m.get('clean_R'))
        out.append(c)
    return out, src


def build():
    sf = os.path.join(ROOTOUT, 'modes_status.json')
    status = json.load(open(sf)) if os.path.exists(sf) else {}
    M = {}
    for code, label, how in MODES:
        sl_out = {}
        for sl, note in SLICES:
            st = status.get(code, {}).get(sl, 'queued')
            top, src = cards(code, sl)
            tot, cross = _tuned(code, sl)
            if top and st == 'queued':
                st = 'complete'
            sl_out[sl] = dict(
                status=st, note=note, source=src,
                tuned=tot, crossers=cross,
                cross_pct=_num(100.0 * cross / tot) if tot else None,
                n_ranked=len(top), top=top)
        M[code] = dict(label=label, exit=how, slices=sl_out)
    out = dict(modes=M, topn=TOPN)
    p = os.path.join(ROOTOUT, 'modes_index.json')
    json.dump(out, open(p, 'w'))
    for c, d in M.items():
        for sl, s in d['slices'].items():
            print('  %s %-5s %-9s tuned %-7s crossers %-6s ranked %d'
                  % (c, sl, s['status'], s['tuned'], s['crossers'], s['n_ranked']))
    print('wrote results/modes_index.json', flush=True)
    return out


if __name__ == '__main__':
    build()
