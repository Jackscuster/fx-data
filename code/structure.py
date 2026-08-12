import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""A structural classifier built directly from price. Swings, breaks, retracements.

STRUCTURE IS THE CLASSIFIER, NOT A TARGET. Nothing here is scored against forward
efficiency. The state is a description of the realised path: does the sequence of
swing highs and lows step up, step down, or neither.

  trending   the last two swing highs AND the last two swing lows both step the
             same way -- higher high WITH higher low, or lower low WITH lower
             high -- and the most recent extreme was taken out by a qualifying
             break, and price has not retraced past R of the last impulse
  chop       anything else

Higher highs alone is not a trend. That distinction is the whole point and
nothing in the 175,634 tracked it.

CAUSALITY, which is where a swing classifier usually leaks. A swing high at bar t
with width N is only identifiable at t+N, because it needs N bars on the right to
know it was a local max. Every swing here is therefore CONFIRMED AT t+N and is
invisible to the state before then; the state at bar u reads only swings with
t+N <= u. Then the whole thing is shifted one more bar like every other signal.
A classifier that used the swing on the day it printed would look far better and
would be unbuildable in real time.

THE PARAMETER SWEEP IS ITSELF A SELECTION. Picking the best of 144 cells is a
search over 144, so the same discipline applies as to signal selection: every cell
is measured on IS-A (1999-2007) and IS-B (2008-2015) only, the configuration is
fixed on those two, and the holdout is read exactly once at the end.

  swing width N        2, 3, 5, 8
  break bars-outside B 1, 2, 3
  break distance D     0.25, 0.5, 1.0   in units of 60-day vol
  retracement R        0.50, 0.62, 0.75, 1.00   of the prior impulse

THE CONTRAST IS PRE-SPECIFIED, in writing, before the sweep runs:

  primary    bars-to-peak, chop minus trending
  secondary  MFE / |MAE|, chop minus trending

Selection uses the PRIMARY on IS-A, and requires IS-B to agree in sign. The sign
is not pre-specified -- the nine-state grid found chop peaking LATER, which is the
opposite of the conventional prior, so forcing a direction would beg the question.
What is pre-specified is that the same signed statistic must hold on both blocks.

Writes results/structure_surface.csv and structure_result.csv.
"""
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
EV = os.path.join(ROOTOUT, 'entry_events.csv')
A_END = pd.Timestamp('2008-01-01')
SPLIT = pd.Timestamp('2016-01-01')
VOLWIN = 60
NS = (2, 3, 5, 8)
BS = (1, 2, 3)
DS = (0.25, 0.5, 1.0)
RS = (0.50, 0.62, 0.75, 1.00)


def swings(c, N):
    """Confirmed swing highs and lows.

    -> (hi_level, hi_prev, lo_level, lo_prev) aligned to bars, each holding the
    value of the most recent swing CONFIRMED by that bar and the one before it.
    """
    n = len(c)
    w = 2 * N + 1
    s = pd.Series(c)
    ishi = (s == s.rolling(w, center=True).max()).values
    islo = (s == s.rolling(w, center=True).min()).values
    out = []
    for mask in (ishi, islo):
        pos = np.flatnonzero(mask)
        conf = pos + N                      # first bar at which it is knowable
        keep = conf < n
        pos, conf = pos[keep], conf[keep]
        k = np.searchsorted(conf, np.arange(n), side='right') - 1
        last = np.where(k >= 0, c[pos[np.clip(k, 0, None)]], np.nan)
        prev = np.where(k >= 1, c[pos[np.clip(k - 1, 0, None)]], np.nan)
        out += [last, prev]
    return out


def _seg(level):
    """Segment id that changes whenever the anchoring swing level changes."""
    v = pd.Series(level)
    return (v != v.shift()).cumsum().values


def classify(c, sigma, N, B, D, R):
    """-> int array: 1 trending up, -1 trending down, 0 chop, -9 undefined."""
    hi, hip, lo, lop = swings(c, N)
    up_seq = (hi > hip) & (lo > lop)
    dn_seq = (hi < hip) & (lo < lop)

    # a qualifying break: B consecutive closes beyond the confirmed extreme by
    # at least D vol units
    thr = D * sigma
    above = pd.Series(c > hi + thr).rolling(B).sum().values == B
    below = pd.Series(c < lo - thr).rolling(B).sum().values == B

    # RETRACEMENT MUST BE MEASURED FROM THE RUNNING EXTREME, not from the
    # confirmed swing. Measuring the pullback as (hi - c)/(hi - lo) is vacuous
    # once a break is required: the break says c > hi, so that quantity is
    # negative and always below R. An earlier version did exactly this and all
    # four R values returned identical numbers, which is how it was caught.
    # The impulse runs from the anchor swing to the highest close reached since
    # that swing was confirmed, and the pullback is measured off that peak.
    seg_hi = pd.Series(c).groupby(_seg(lo)).cummax().values   # peak since the low
    seg_lo = pd.Series(c).groupby(_seg(hi)).cummin().values   # trough since the high
    with np.errstate(invalid='ignore', divide='ignore'):
        up_imp = seg_hi - lo
        dn_imp = hi - seg_lo
        ret_up = np.where(up_imp > 0, (seg_hi - c) / up_imp, np.nan)
        ret_dn = np.where(dn_imp > 0, (c - seg_lo) / dn_imp, np.nan)

    st = np.zeros(len(c), np.int8)
    ok = np.isfinite(hi) & np.isfinite(hip) & np.isfinite(lo) & np.isfinite(lop) \
        & np.isfinite(sigma)
    st[up_seq & above & (ret_up < R) & ok] = 1
    st[dn_seq & below & (ret_dn < R) & ok] = -1
    st[~ok] = -9
    return st


def build(px, N, B, D, R):
    lp = np.log(px.astype(float))
    sig = lp.diff().rolling(VOLWIN).std()
    out = {}
    for p in px.columns:
        c = lp[p].values
        s = sig[p].values
        st = classify(c, s, N, B, D, R)
        out[p] = pd.Series(st, index=px.index).shift(1)     # the standard extra lag
    return pd.DataFrame(out)


def contrast(S, E, lo, hi):
    """chop minus trending, on the two pre-specified metrics, within a date band."""
    L = S.stack().rename('st').reset_index()
    L.columns = ['date', 'pair', 'st']
    X = E.merge(L, on=['date', 'pair'], how='left')
    X = X[(X.date >= lo) & (X.date < hi) & X.st.notna() & (X.st != -9)]
    tr = X[X.st != 0]
    ch = X[X.st == 0]
    if len(tr) < 200 or len(ch) < 200:
        return None
    d_bars = ch.bars_to_peak.mean() - tr.bars_to_peak.mean()
    se = np.sqrt(tr.bars_to_peak.var() / len(tr) + ch.bars_to_peak.var() / len(ch))
    d_ratio = (ch.mfe.mean() / abs(ch.mae.mean())
               - tr.mfe.mean() / abs(tr.mae.mean()))
    return dict(n_trend=len(tr), n_chop=len(ch), bars=d_bars,
                t_bars=d_bars / se if se else np.nan, ratio=d_ratio,
                trend_share=len(tr) / (len(tr) + len(ch)))


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    E = pd.read_csv(EV)
    E['date'] = pd.to_datetime(E.date)
    rows = []
    for N in NS:
        for B in BS:
            for D in DS:
                for R in RS:
                    S = build(px, N, B, D, R)
                    a = contrast(S, E, pd.Timestamp('1999-01-01'), A_END)
                    b = contrast(S, E, A_END, SPLIT)
                    if a is None or b is None:
                        continue
                    rows.append(dict(N=N, B=B, D=D, R=R,
                                     A_bars=a['bars'], A_t=a['t_bars'],
                                     A_ratio=a['ratio'], A_share=a['trend_share'],
                                     B_bars=b['bars'], B_t=b['t_bars'],
                                     B_ratio=b['ratio'], B_share=b['trend_share']))
            print('  swept N=%d B=%d' % (N, B), flush=True)
    S = pd.DataFrame(rows)
    S['agree'] = np.sign(S.A_bars) == np.sign(S.B_bars)
    S.to_csv(os.path.join(ROOTOUT, 'structure_surface.csv'), index=False)
    report(S, px, E)


def report(S, px, E):
    print('\nPARAMETER SURFACE: %d cells, all measured on IS only' % len(S))
    print('  cells where IS-A and IS-B agree on the sign of the bars contrast: '
          '%d of %d' % (int(S.agree.sum()), len(S)))
    print('\nMARGINALS -- mean IS-A bars contrast by each parameter')
    for k in ('N', 'B', 'D', 'R'):
        g = S.groupby(k).agg(bars=('A_bars', 'mean'), t=('A_t', 'mean'),
                             agree=('agree', 'mean'), share=('A_share', 'mean'))
        print('  %s' % k)
        print(g.to_string(float_format=lambda v: '%.3f' % v))
    print('\nWHICH BREAK QUALIFIER MATTERS MORE?')
    vb = S.groupby('B').A_bars.mean()
    vd = S.groupby('D').A_bars.mean()
    print('  bars-outside B spans %.3f (%.3f to %.3f)'
          % (vb.max() - vb.min(), vb.min(), vb.max()))
    print('  distance      D spans %.3f (%.3f to %.3f)'
          % (vd.max() - vd.min(), vd.min(), vd.max()))
    print('  -> %s is the stronger lever'
          % ('distance' if (vd.max() - vd.min()) > (vb.max() - vb.min())
             else 'bars-outside'))
    print('\nIS THERE A PLATEAU? top 12 cells by IS-A |t|, with their IS-B result')
    T = S.reindex(S.A_t.abs().sort_values(ascending=False).index)
    print(T.head(12)[['N', 'B', 'D', 'R', 'A_bars', 'A_t', 'B_bars', 'B_t',
                      'A_share', 'agree']]
          .to_string(index=False, float_format=lambda v: '%.3f' % v))
    S.to_csv(os.path.join(ROOTOUT, 'structure_surface.csv'), index=False)
    return S


if __name__ == '__main__':
    main()
