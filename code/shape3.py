import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""Three shapes, not four. And what lookback the shape read actually uses.

THE FOURTH SHAPE WAS NEVER IN THE SPEC. structure.five_state emits trending,
broken, range, drifting and 'no swings', and 'broken' was carried into the
product, making 4 x 3 = 12 states instead of the specified 3 x 3 = 9. 'broken'
then took 64% of all days while trending took 2.9%, so the classifier spent most
of its time saying "a break happened but the sequence does not support it" --
which is a diagnostic, not a regime.

THE FIX IS A PARTITION, NOT A FOLD. Folding 'broken' into a neighbour would keep
a definition that was never meant to be a state. Instead the three shapes are
redefined so they cover every bar exactly once, on one question asked twice:

  is price outside the last confirmed swing band?
      no   -> RANGE      inside [lo, hi]
      yes  -> does the swing sequence support the direction it broke?
                 yes -> TRENDING
                 no  -> DRIFTING

'broken' disappears because it was the leftover of a rule that required BOTH
sequence legs to step the same way. Bars that broke out with one leg confirming
are now trending; bars that broke out with neither are drifting. Nothing is
discarded and no bar is unlabelled.

HOW STRICT THE SEQUENCE HAS TO BE is the one free choice, so it is swept:

  strict     higher high AND higher low        (the old rule) -> trending 5.6%
  relaxed    higher high OR higher low                        -> trending 10.9%
  breakonly  no sequence requirement at all                   -> trending 14.1%

SELECTION IS A DESIGN CRITERION, STATED, NOT A FITTED ONE. The three shares are
picked to be as even as possible -- maximum entropy over the three states,
measured on IS only. Balance is what a three-state vocabulary is for; it is not
scored against any outcome, so there is nothing here to overfit.

BUT BALANCE ALONE PICKS 'breakonly', AND THAT IS REJECTED. On raw entropy the
winner is breakonly at N=3, 0.936 against relaxed N=5 at 0.923 -- a difference of
0.013. breakonly drops the swing sequence entirely, which makes 'trending' mean
nothing more than "a qualifying break happened and price has not retraced past
R". structure.py exists because higher highs alone is not a trend; that is its
founding distinction. Trading it away for 0.013 of entropy would delete the
classifier and keep the label. So the choice is constrained to modes that RETAIN
a sequence requirement, and among those the most balanced wins.

WHAT LOOKBACK DOES SHAPE USE -- it has no fixed window, and that is the honest
answer. The nine-box reads 7, 28 and 128 bars. The shape read is EVENT-DRIVEN:
its memory runs back to the second-most-recent confirmed swing on each side,
whose distance varies with the market. So the effective lookback is measured here
rather than asserted, per swing width N, and reported as a distribution.

  N is therefore the horizon knob, the direct analogue of the ribbon's window.
  A larger N confirms swings more slowly, reaches further back, and calls more
  trend.

Writes results/shape3_coverage.csv, results/shape3_lookback.csv and
results/shape3_states.csv.
"""
import numpy as np, pandas as pd

PX = os.path.join(ROOTDATA, 'px28.csv')
SPLIT = pd.Timestamp('2016-01-01')
MODES = ('strict', 'relaxed', 'breakonly')
NS = (2, 3, 5, 8, 13)
STATES = ['trending', 'range', 'drifting']
# the shipped setting: most balanced on IS among modes that keep a sequence
# requirement. combined.layers() reads these two names.
MODE_SHIPPED, N_SHIPPED = 'relaxed', 6      # the superseded GATE version
# The shipped shape read is now the CONTINUOUS score (shapescore.py), cut at
# terciles so every bar lands somewhere. N_SCORE was chosen on IS. The ribbon
# suffixes are the MEASURED median lookback in bars, not the swing width.
# LOCKED: swing width 19, measured lookback 106 bars. Chosen for 21-bar range
# episodes over the last 5% of separation -- see 16.4q.
N_SCORE = 19
RIBBON = ((6, 35), (19, 106), (44, 247))

from structure import swings, _seg, VOLWIN
from structsel import chosen_cell


def swing_pos(c, N):
    """Positions of the last and second-last CONFIRMED swing, per bar."""
    n = len(c); w = 2 * N + 1
    s = pd.Series(c)
    out = []
    for mask in ((s == s.rolling(w, center=True).max()).values,
                 (s == s.rolling(w, center=True).min()).values):
        pos = np.flatnonzero(mask); conf = pos + N
        keep = conf < n; pos, conf = pos[keep], conf[keep]
        k = np.searchsorted(conf, np.arange(n), side='right') - 1
        last = np.where(k >= 0, pos[np.clip(k, 0, None)], np.nan)
        prev = np.where(k >= 1, pos[np.clip(k - 1, 0, None)], np.nan)
        out += [last, prev]
    return out


def three_state(px, N, B, D, R, mode='relaxed'):
    """The three-way partition. Every labelled bar gets exactly one state."""
    lp = np.log(px.astype(float))
    sig = lp.diff().rolling(VOLWIN).std()
    out = {}
    for p in px.columns:
        c, sg = lp[p].values, sig[p].values
        hi, hip, lo, lop = swings(c, N)
        upb, upl = hi > hip, lo > lop
        dnb, dnl = hi < hip, lo < lop
        if mode == 'strict':
            up, dn = upb & upl, dnb & dnl
        elif mode == 'relaxed':
            up, dn = upb | upl, dnb | dnl
        else:
            up = dn = np.ones(len(c), bool)
        thr = D * sg
        ab = pd.Series(c > hi + thr).rolling(B).sum().values == B
        be = pd.Series(c < lo - thr).rolling(B).sum().values == B
        sh_ = pd.Series(c).groupby(_seg(lo)).cummax().values
        sl_ = pd.Series(c).groupby(_seg(hi)).cummin().values
        with np.errstate(invalid='ignore', divide='ignore'):
            ru = np.where(sh_ - lo > 0, (sh_ - c) / (sh_ - lo), np.nan)
            rd = np.where(hi - sl_ > 0, (c - sl_) / (hi - sl_), np.nan)
        ok = (np.isfinite(hi) & np.isfinite(hip) & np.isfinite(lo)
              & np.isfinite(lop) & np.isfinite(sg))
        st = np.full(len(c), '', object)
        tr = ((up & ab & (ru < R)) | (dn & be & (rd < R))) & ok
        st[tr] = 'trending'
        inb = ok & ~tr & (c <= hi) & (c >= lo)
        st[inb] = 'range'
        st[ok & ~tr & ~inb] = 'drifting'
        out[p] = pd.Series(st, index=px.index).shift(1)
    return pd.DataFrame(out)


def entropy(sh):
    p = np.array([sh.get(s, 0.0) for s in STATES], float)
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum() / np.log2(3))


def main():
    px = pd.read_csv(PX, index_col=0, parse_dates=True)
    fit = px.index < SPLIT
    N0, B, D, R = chosen_cell()
    print('structural cell from structsel.py: N=%d B=%d D=%.2f R=%.2f' % (N0, B, D, R))

    print('\nCOVERAGE SURFACE, IS only (1999-2015). balance = entropy / log2(3)')
    print('  %-10s %-4s %10s %9s %10s %9s' % ('mode', 'N', 'trending', 'range',
                                              'drifting', 'balance'))
    rows = []
    for mode in MODES:
        for N in NS:
            lab = three_state(px, N, B, D, R, mode)
            v = lab[fit].stack().replace('', np.nan).dropna() \
                .value_counts(normalize=True)
            e = entropy(v)
            print('  %-10s %-4d %9.3f %9.3f %10.3f %9.3f'
                  % (mode, N, v.get('trending', 0), v.get('range', 0),
                     v.get('drifting', 0), e))
            rows.append(dict(mode=mode, N=N, trending=v.get('trending', 0),
                             range_=v.get('range', 0),
                             drifting=v.get('drifting', 0), balance=e))
    C = pd.DataFrame(rows)
    C.to_csv(os.path.join(ROOTOUT, 'shape3_coverage.csv'), index=False)
    raw = C.sort_values('balance', ascending=False).iloc[0]
    print('\n  most balanced overall (REJECTED): mode=%s N=%d, balance %.3f'
          % (raw['mode'], raw.N, raw.balance))
    print('  breakonly drops the swing sequence, so "trending" would mean only')
    print('  "a break happened and price has not retraced". structure.py exists')
    print('  because higher highs alone is not a trend. Not traded away for')
    print('  %.3f of entropy.' % (raw.balance
                                  - C[C['mode'] != 'breakonly'].balance.max()))
    w = C[C['mode'] != 'breakonly'].sort_values('balance',
                                                ascending=False).iloc[0]
    print('\n  CHOSEN: mode=%s N=%d, balance %.3f (sequence retained)'
          % (w['mode'], w.N, w.balance))

    print('\nHOLDOUT COVERAGE at that setting, against the old four-state read')
    lab = three_state(px, int(w.N), B, D, R, w['mode'])
    v = lab[~fit].stack().replace('', np.nan).dropna().value_counts(normalize=True)
    print('  new three-state:  %s'
          % '  '.join('%s %.3f' % (s, v.get(s, 0)) for s in STATES))
    from structure import five_state
    o = five_state(px, N0, B, D, R)[~fit].stack().replace('', np.nan).dropna() \
        .value_counts(normalize=True)
    print('  old four-state:   %s'
          % '  '.join('%s %.3f' % (k, o.get(k, 0))
                      for k in ('trending', 'broken', 'range', 'drifting')))
    print('  trending goes from %.1f%% to %.1f%%, and "broken" -- %.1f%% of bars'
          % (100 * o.get('trending', 0), 100 * v.get('trending', 0),
             100 * o.get('broken', 0)))
    print('  and never part of the spec -- is gone.')

    print('\nWHAT LOOKBACK DOES SHAPE USE? bars back to the anchoring swing')
    print('  the state needs TWO confirmed swings each side, so its memory runs')
    print('  to the second-most-recent one. This is a distribution, not a window.')
    print('  %-4s %8s %8s %8s %8s %8s' % ('N', 'p10', 'median', 'mean', 'p90',
                                          'p99'))
    lp = np.log(px.astype(float))
    lb = []
    for N in NS:
        ages = []
        for p in px.columns:
            c = lp[p].values
            hl, hp, ll, lpz = swing_pos(c, N)
            idx = np.arange(len(c))
            a = np.nanmax(np.vstack([idx - hp, idx - lpz]), axis=0)
            ages.append(a[np.isfinite(a)])
        a = np.concatenate(ages)
        q = np.percentile(a, [10, 50, 90, 99])
        print('  %-4d %8.0f %8.0f %8.1f %8.0f %8.0f'
              % (N, q[0], q[1], a.mean(), q[2], q[3]))
        lb.append(dict(N=N, p10=q[0], median=q[1], mean=a.mean(), p90=q[2],
                       p99=q[3]))
    pd.DataFrame(lb).to_csv(os.path.join(ROOTOUT, 'shape3_lookback.csv'),
                            index=False)
    print("""
  SO: shape has NO fixed window and cannot be given one without changing what it
  is. N is the horizon knob -- the direct analogue of the ribbon's 7/28/128 --
  and the table above is what each N actually reaches back to. For a daily entry
  held for weeks, N=5 (median ~%d bars, p90 ~%d) is the closest match to the
  28-day ribbon window; N=2 is the fast leg and N=8-13 the slow one. Running
  three N values side by side would reproduce the ribbon on the shape axis, and
  that is a build decision, not a finding.""" % (lb[2]['median'], lb[2]['p90']))

    lab.to_csv(os.path.join(ROOTOUT, 'shape3_states.csv'))
    print('\nwrote shape3_coverage.csv, shape3_lookback.csv, shape3_states.csv')
    return w


if __name__ == '__main__':
    main()
