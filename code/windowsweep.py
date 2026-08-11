import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Re-derive the classifier windows from scratch: every length from 4 to 200.

The previous choice came from three pre-set bands (7-14, 20-31, 60-90), so it
could only ever land inside them. This sweeps the whole range as one continuous
curve and asks what falls out.

FOUR MEASURES PER WINDOW
  churn        label changes per 1000 bars -- how often it moves when nothing has
  duration     median run length of a state
  lag          bars until the label follows a genuine change in behaviour
  separation   spread in forward path efficiency across the nine states

ON THE LAG REFERENCE, WHICH IS THE ONE JUDGEMENT CALL HERE. "A genuine change in
behaviour" needs a definition independent of the window being tested, so it is a
CENTRED window -- half its span either side of the bar, no lag by construction.
That reads the future and is a diagnostic only; it never enters a feature.

But any single centred span quietly favours windows near it. So the lag is
measured against TWO spans, 21 and 63, and both are reported. If the ranking of
windows is the same under both, the choice of reference is not driving it.

Churn, duration and separation need no reference at all, so they carry the
decision and lag is corroboration.

Writes results/window_sweep.csv and window_pairs.csv.
"""
import numpy as np, pandas as pd
from classifier import fit_frac
from ninestate import tercile, NAME, SAX, CAX, STATES, SPLIT, VOLWIN

PX = os.path.join(ROOTDATA, 'px28.csv')
EV = os.path.join(ROOTOUT, 'entry_events.csv')
LS = list(range(4, 201))
REFS = (21, 63)
MAXLAG = 90
CODE = {s: i for i, s in enumerate(STATES)}


def axes_at(lp, rr, L):
    net = (lp - lp.shift(L)).abs()
    path = rr.abs().rolling(L).sum()
    vol = rr.rolling(VOLWIN).std()
    inf = [np.inf, -np.inf]
    return ((net / path).replace(inf, np.nan).shift(1),
            (path / (vol * np.sqrt(L))).replace(inf, np.nan).shift(1))


def coded_grid(px, lp, rr, L, fit):
    """-> int array (T x P), -1 where undefined. Ints keep the sweep cheap."""
    st, sc = axes_at(lp, rr, L)
    a, b = tercile(st, fit).values, tercile(sc, fit).values
    out = np.full(a.shape, -1, np.int8)
    ok = np.isfinite(a) & np.isfinite(b)
    ai = np.where(ok, a, 0).astype(np.int8)
    bi = np.where(ok, b, 0).astype(np.int8)
    for x in range(3):
        for y in range(3):
            m = ok & (ai == x) & (bi == y)
            out[m] = CODE[NAME[(SAX[x], CAX[y])]]
    return out


def truth_codes(px, lp, rr, R, fit):
    """Centred, non-causal reference grid. Diagnostic only."""
    net = (lp - lp.shift(R)).abs()
    path = rr.abs().rolling(R, center=True).sum()
    vol = rr.rolling(VOLWIN).std()
    inf = [np.inf, -np.inf]
    st = (net.rolling(1).mean() / path).replace(inf, np.nan)
    sc = (path / (vol * np.sqrt(R))).replace(inf, np.nan)
    a, b = tercile(st, fit).values, tercile(sc, fit).values
    out = np.full(a.shape, -1, np.int8)
    ok = np.isfinite(a) & np.isfinite(b)
    ai = np.where(ok, a, 0).astype(np.int8); bi = np.where(ok, b, 0).astype(np.int8)
    for x in range(3):
        for y in range(3):
            out[ok & (ai == x) & (bi == y)] = CODE[NAME[(SAX[x], CAX[y])]]
    return out


def lag_of(lab, tru):
    """Median bars from a truth change to the label matching it.

    Vectorised: for each state value, the index of its next occurrence is a
    reverse running minimum, so no per-event scan is needed. The loop version of
    this was 197 windows x 28 pairs x ~2000 events and would not have finished.
    """
    n, P = lab.shape
    lags = []
    idx = np.arange(n)
    for p in range(P):
        a, b = lab[:, p], tru[:, p]
        nxt = np.full((9, n), n, np.int32)
        for v in range(9):
            pos = np.where(a == v, idx, n)
            nxt[v] = np.minimum.accumulate(pos[::-1])[::-1]
        ch = np.flatnonzero((b[1:] != b[:-1]) & (b[1:] >= 0)) + 1
        if not len(ch):
            continue
        tgt = b[ch]
        d = nxt[tgt, ch] - ch
        lags.append(np.minimum(d, MAXLAG))
    return float(np.median(np.concatenate(lags))) if lags else np.nan


def runs_and_churn(lab):
    n, P = lab.shape
    lens, chg, tot = [], 0, 0
    for p in range(P):
        a = lab[:, p]
        m = a >= 0
        if m.sum() < 100:
            continue
        v = a[m]
        b = np.flatnonzero(np.r_[True, v[1:] != v[:-1]])
        lens.append(np.diff(np.r_[b, len(v)]))
        chg += len(b) - 1
        tot += len(v)
    L = np.concatenate(lens) if lens else np.array([1])
    return float(np.median(L)), 1000.0 * chg / max(tot, 1)


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    fit = np.asarray(px.index < SPLIT)
    lp = np.log(px.astype(float)); rr = lp.diff()
    cols = list(px.columns)

    E = pd.read_csv(EV); E['date'] = pd.to_datetime(E.date)
    E = E[E.oos]
    di = {d: i for i, d in enumerate(px.index)}
    pi = {p: i for i, p in enumerate(cols)}
    er = np.array([di.get(d, -1) for d in E.date])
    ep = np.array([pi.get(p, -1) for p in E.pair])
    keep = (er >= 0) & (ep >= 0)
    er, ep = er[keep], ep[keep]
    eff = E.path_eff.values[keep]

    tru = {R: truth_codes(px, lp, rr, R, fit) for R in REFS}
    grids, rows = {}, []
    for L in LS:
        g = coded_grid(px, lp, rr, L, fit)
        med, ch = runs_and_churn(g)
        s = g[er, ep]
        sep = np.nan
        ok = (s >= 0) & np.isfinite(eff)
        if ok.sum() > 500:
            m = pd.Series(eff[ok]).groupby(pd.Series(s[ok])).mean()
            sep = float(m.max() - m.min()) if len(m) >= 8 else np.nan
        r = dict(L=L, churn=ch, duration=med, separation=sep)
        for R in REFS:
            r['lag%d' % R] = lag_of(g, tru[R])
        rows.append(r)
        if L in (4, 8, 21, 60, 90, 120, 200) or L % 25 == 0:
            print('  L=%3d churn %6.1f dur %5.1f lag21 %5.1f lag63 %5.1f sep %.4f'
                  % (L, ch, med, r['lag21'], r['lag63'], sep), flush=True)
        grids[L] = g
    S = pd.DataFrame(rows)
    S.to_csv(os.path.join(ROOTOUT, 'window_sweep.csv'), index=False)
    report(S, grids, cols)


def agreement(a, b):
    m = (a >= 0) & (b >= 0)
    return float((a[m] == b[m]).mean()) if m.sum() else np.nan


def report(S, grids, cols):
    print('\nFULL CURVES (every 8th window shown; the CSV has all 197)')
    print('%4s %8s %7s %7s %7s %10s' % ('L', 'churn', 'dur', 'lag21', 'lag63', 'sep'))
    for _, r in S[S.L % 8 == 0].iterrows():
        print('%4d %8.1f %7.1f %7.1f %7.1f %10.4f'
              % (r.L, r.churn, r.duration, r.lag21, r.lag63, r.separation))

    # where does the churn curve stop falling?
    S = S.sort_values('L').reset_index(drop=True)
    d = -S.churn.diff() / S.churn.shift()          # fractional fall per step
    print('\nCHURN CURVE -- fractional fall per extra bar of window')
    for lo, hi in ((4, 12), (12, 25), (25, 45), (45, 70), (70, 100),
                   (100, 140), (140, 200)):
        m = (S.L > lo) & (S.L <= hi)
        print('  L %3d-%3d  churn %6.1f -> %6.1f   mean fall %.4f/bar'
              % (lo, hi, S[S.L == lo].churn.iloc[0] if (S.L == lo).any() else np.nan,
                 S[m].churn.iloc[-1], d[m].mean()))

    print('\nSEPARATION by window band (mean spread in forward path efficiency)')
    for lo, hi in ((4, 12), (12, 25), (25, 45), (45, 70), (70, 100),
                   (100, 140), (140, 200)):
        m = (S.L > lo) & (S.L <= hi)
        print('  L %3d-%3d  %.4f   best L=%d at %.4f'
              % (lo, hi, S[m].separation.mean(),
                 int(S.loc[S[m].separation.idxmax(), 'L']), S[m].separation.max()))

    print('\nHOW DUPLICATED ARE TWO WINDOWS? share of bars with the same label')
    cand = [6, 8, 12, 16, 21, 30, 45, 60, 90, 120, 160, 200]
    print('%6s' % '' + ''.join('%7d' % c for c in cand))
    for a in cand:
        print('%6d' % a + ''.join(
            '%7.2f' % agreement(grids[a], grids[b]) if b > a else '      .'
            for b in cand))
    return S


if __name__ == '__main__':
    main()
