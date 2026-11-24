import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""C3 — RAW HOURLY EFFECTS: hour of day, session, month end, the London 4pm fix.

Jack, 24 Nov: "from the hourly bid/ask file, per currency, the average move by
hour of day, own session versus overnight, and month-end and London 4pm fix
effects, net of the by-hour cost table, measured on data before 2016 and
confirmed once on 2016 to 2020. RAW EFFECTS ONLY, NOTHING TRADABLE BUILT."

So this module measures and reports. It builds no signal, no entry rule and no
book, and it is not wired into any strategy. That restraint is the instruction,
not an omission.

WHAT IT MEASURES AND IN WHAT UNITS. Every figure is in basis points of the mid,
per hour, and every one is reported BOTH gross and net of that hour's spread.
The net figure subtracts ONE spread crossing, because a round trip crosses the
spread once -- the same correction that had to be made in A5.

PER CURRENCY, NOT PER PAIR. A pair's move is projected onto its two currency
legs: for XXXYYY a +r move is +r for XXX and -r for YYY. Each currency's hourly
move is the mean of its signed legs across the seven pairs that contain it, so
it reads as that currency against the basket of the other seven.

THE SPLIT IS THE PROJECT'S SPLIT. Effects are measured on PRE-2016 data and
confirmed ONCE on 2016-2020. 2021 onward stays sealed and is never touched here.

SESSIONS, in New York hours, which is how the project's bars are stamped:
  Tokyo   19:00-03:00 NY     own currencies JPY, AUD, NZD
  London  03:00-11:00 NY     own currencies EUR, GBP, CHF
  NewYork 08:00-16:00 NY     own currencies USD, CAD
London and New York overlap 08:00-11:00; a bar in the overlap counts as own
session for both sets, which is stated rather than resolved arbitrarily.

THE LONDON 4PM FIX is 16:00 London = 11:00 NY on a normal day. The hour is
taken as the bar stamped 11:00 NY.

    python3 code/c3hourly.py --stage hours
    python3 code/c3hourly.py --stage md
"""
import time, glob, json, hashlib
import numpy as np, pandas as pd

import l2r2gate1 as G

H1 = os.path.join(ROOTDATA, 'oanda_h1')
OUT = os.path.join(ROOTOUT, 'r2reads')
os.makedirs(OUT, exist_ok=True)

G8 = ['EUR', 'GBP', 'AUD', 'NZD', 'USD', 'CAD', 'CHF', 'JPY']
SESSIONS = {'Tokyo': (19, 3), 'London': (3, 11), 'NewYork': (8, 16)}
OWN = {'Tokyo': ('JPY', 'AUD', 'NZD'), 'London': ('EUR', 'GBP', 'CHF'),
       'NewYork': ('USD', 'CAD')}
FIX_HOUR_NY = 11          # 16:00 London
MEASURE_END = '2016-01-01'
CONFIRM_START, CONFIRM_END = '2016-01-01', '2021-01-01'


def pairs_available():
    fs = sorted(glob.glob(os.path.join(H1, '*_bid.csv')))
    return [os.path.basename(f).split('_')[0] for f in fs]


def in_session(hour_ny, name):
    a, b = SESSIONS[name]
    return ((hour_ny >= a) | (hour_ny < b)) if a > b else \
           ((hour_ny >= a) & (hour_ny < b))


def one_pair(pair):
    """Hourly mid return in bp, spread in bp, and the time keys, for one pair."""
    fb = os.path.join(H1, '%s_bid.csv' % pair)
    fa = os.path.join(H1, '%s_ask.csv' % pair)
    if not (os.path.exists(fb) and os.path.exists(fa)):
        return None
    b = pd.read_csv(fb, parse_dates=['time'], usecols=['time', 'c'])
    a = pd.read_csv(fa, parse_dates=['time'], usecols=['time', 'c'])
    d = b.merge(a, on='time', suffixes=('_b', '_a')).sort_values('time')
    d = d[(d.c_b > 0) & (d.c_a > 0)]
    mid = (d.c_b.values + d.c_a.values) / 2.0
    spr = d.c_a.values - d.c_b.values
    with np.errstate(divide='ignore', invalid='ignore'):
        ret_bp = np.concatenate([[np.nan], 1e4 * np.diff(np.log(mid))])
        spr_bp = 1e4 * spr / mid
    t = pd.DatetimeIndex(d.time.values, tz='UTC').tz_convert('America/New_York')
    return pd.DataFrame(dict(
        time=t, hour_ny=t.hour.values, date=t.normalize().tz_localize(None),
        month=t.month.values, ret_bp=ret_bp, spr_bp=spr_bp))


def _legs(pair):
    return pair[:3], pair[3:]


def stage_hours(era='measure'):
    """Per currency, the mean hourly move by NY hour, gross and net of spread."""
    lo, hi = ((None, MEASURE_END) if era == 'measure'
              else (CONFIRM_START, CONFIRM_END))
    rows, sess, fixr, me = [], [], [], []
    t0 = time.time()
    PA = pairs_available()
    assert len(PA) == 28, 'expected 28 pairs of hourly data, found %d' % len(PA)
    for pi, p in enumerate(PA):
        d = one_pair(p)
        if d is None:
            continue
        if lo:
            d = d[d.time >= pd.Timestamp(lo, tz='America/New_York')]
        if hi:
            d = d[d.time < pd.Timestamp(hi, tz='America/New_York')]
        d = d.dropna(subset=['ret_bp'])
        if not len(d):
            continue
        bc, qc = _legs(p)
        # ---- hour of day
        g = d.groupby('hour_ny').agg(n=('ret_bp', 'size'),
                                     ret_bp=('ret_bp', 'mean'),
                                     spr_bp=('spr_bp', 'median'))
        for h, r in g.iterrows():
            for ccy, sgn in ((bc, +1.0), (qc, -1.0)):
                rows.append(dict(era=era, currency=ccy, pair=p, hour_ny=int(h),
                                 n=int(r.n), move_bp=sgn * float(r.ret_bp),
                                 spread_bp=float(r.spr_bp)))
        # ---- sessions
        for sname in SESSIONS:
            m = in_session(d.hour_ny.values, sname)
            for lbl, mm in (('in', m), ('out', ~m)):
                if not mm.any():
                    continue
                sub = d[mm]
                for ccy, sgn in ((bc, +1.0), (qc, -1.0)):
                    sess.append(dict(era=era, currency=ccy, pair=p,
                                     session=sname, side=lbl, n=int(len(sub)),
                                     move_bp=sgn * float(sub.ret_bp.mean()),
                                     spread_bp=float(sub.spr_bp.median()),
                                     own=int(ccy in OWN[sname])))
        # ---- the London 4pm fix hour
        for lbl, mm in (('fix_hour', d.hour_ny.values == FIX_HOUR_NY),
                        ('other_hours', d.hour_ny.values != FIX_HOUR_NY)):
            sub = d[mm]
            if not len(sub):
                continue
            for ccy, sgn in ((bc, +1.0), (qc, -1.0)):
                fixr.append(dict(era=era, currency=ccy, pair=p, bucket=lbl,
                                 n=int(len(sub)),
                                 move_bp=sgn * float(sub.ret_bp.mean()),
                                 abs_move_bp=float(sub.ret_bp.abs().mean()),
                                 spread_bp=float(sub.spr_bp.median())))
        # ---- month end: the last 3 trading days of each calendar month
        dd = d.copy()
        du = dd.date.drop_duplicates().sort_values()
        tail = (pd.Series(du.values)
                .groupby([du.dt.year.values, du.dt.month.values])
                .apply(lambda s: s.tail(3)).values)
        dd['month_end'] = dd.date.isin(pd.DatetimeIndex(tail)).astype(int)
        for lbl, mm in (('month_end', dd.month_end == 1),
                        ('rest', dd.month_end == 0)):
            sub = dd[mm]
            if not len(sub):
                continue
            for ccy, sgn in ((bc, +1.0), (qc, -1.0)):
                me.append(dict(era=era, currency=ccy, pair=p, bucket=lbl,
                               n=int(len(sub)),
                               move_bp=sgn * float(sub.ret_bp.mean()),
                               abs_move_bp=float(sub.ret_bp.abs().mean()),
                               spread_bp=float(sub.spr_bp.median())))
        del d, dd
        if (pi + 1) % 7 == 0:
            print('    c3 %s: %d of %d pairs, %.1f min'
                  % (era, pi + 1, len(PA), (time.time() - t0) / 60.0), flush=True)
    out = {}
    for nm, lst in (('hours', rows), ('sessions', sess), ('fix', fixr),
                    ('monthend', me)):
        D = pd.DataFrame(lst)
        f = os.path.join(OUT, 'c3_%s_%s.csv' % (nm, era))
        D.to_csv(f, index=False)
        out[nm] = f
    print('  C3 [%s]: %d hour rows, %d session rows, %d fix rows, %d month-end rows'
          % (era, len(rows), len(sess), len(fixr), len(me)), flush=True)
    return out


def _safe(path):
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def _net(D):
    """Add the net-of-spread column. ONE crossing, not two."""
    D = D.copy()
    D['move_net_bp'] = D.move_bp - D.spread_bp
    return D


def roll_up(D, keys):
    """Mean across pairs, so each currency reads against the basket."""
    if not len(D):
        return D
    D = _net(D)
    g = D.groupby(keys, as_index=False).agg(
        pairs=('pair', 'nunique'), n=('n', 'sum'),
        move_bp=('move_bp', 'mean'), spread_bp=('spread_bp', 'mean'),
        move_net_bp=('move_net_bp', 'mean'))
    # a crude t on the cross-pair spread of the effect, which is what says
    # whether a currency's hour is consistent across its seven pairs
    sd = D.groupby(keys).move_bp.std(ddof=1).reset_index(name='sd_across_pairs')
    g = g.merge(sd, on=keys, how='left')
    g['t_across_pairs'] = g.move_bp / (g.sd_across_pairs
                                       / np.sqrt(g.pairs.clip(lower=1)))
    return g


def stage_md(out=None):
    """results/r2reads/C3_HOURLY_EFFECTS.md"""
    import l2r2gate3 as G3x
    L = []; a = L.append
    a('# C3 — RAW HOURLY EFFECTS\n')
    a('Generated %s by `code/c3hourly.py`.\n' % time.strftime('%F %H:%M'))
    a('\n**RAW EFFECTS ONLY. NOTHING TRADABLE IS BUILT HERE** — no signal, no '
      'entry rule, no book, and nothing wired into a strategy. That was the '
      'instruction.\n')
    a('\n## Method\n')
    a('- Hourly OANDA bid/ask for all 28 pairs; the mid is `(bid+ask)/2` and '
      'the move is its log difference in **basis points**.\n')
    a('- **Per currency, not per pair.** For `XXXYYY` a `+r` move is `+r` for '
      'XXX and `−r` for YYY, and each currency\'s figure is the mean of its '
      'signed legs across the seven pairs containing it — that currency against '
      'the basket of the other seven.\n')
    a('- Every figure is given **gross and net of that hour\'s own median '
      'spread**, measured from the same file. The net column subtracts **one** '
      'spread crossing, because a round trip crosses the spread once.\n')
    a('- **Measured on pre-2016 data and confirmed once on 2016–2020. 2021 '
      'onward stays sealed** and is never read here.\n')
    a('- `t_across_pairs` is the effect divided by its standard error across '
      'the seven pairs of that currency. It asks whether the hour is '
      '*consistent* across pairs, not whether it is tradable.\n')
    for era, lbl in (('measure', 'Measured: pre-2016'),
                     ('confirm', 'Confirmed: 2016–2020')):
        a('\n## %s\n' % lbl)
        H = _safe(os.path.join(OUT, 'c3_hours_%s.csv' % era))
        Sx = _safe(os.path.join(OUT, 'c3_sessions_%s.csv' % era))
        Fx = _safe(os.path.join(OUT, 'c3_fix_%s.csv' % era))
        Me = _safe(os.path.join(OUT, 'c3_monthend_%s.csv' % era))
        if not len(H):
            a('_Not run._\n'); continue
        g = roll_up(H, ['currency', 'hour_ny'])
        a('### Move by hour of day, per currency\n')
        a('Hours are New York. Positive means the currency rose against the '
          'basket in that hour.\n')
        piv = g.pivot_table(index='hour_ny', columns='currency',
                            values='move_bp')
        piv = piv.reindex(columns=[c for c in G8 if c in piv.columns])
        a('| NY hour | ' + ' | '.join(piv.columns) + ' |')
        a('|---:' * (len(piv.columns) + 1) + '|')
        for h in piv.index:
            a('| %02d:00 | ' % h
              + ' | '.join('%+.3f' % piv.loc[h, c] for c in piv.columns) + ' |')
        a('\n**Net of spread, the same grid:**\n')
        pn = g.pivot_table(index='hour_ny', columns='currency',
                           values='move_net_bp')
        pn = pn.reindex(columns=[c for c in G8 if c in pn.columns])
        a('| NY hour | ' + ' | '.join(pn.columns) + ' |')
        a('|---:' * (len(pn.columns) + 1) + '|')
        for h in pn.index:
            a('| %02d:00 | ' % h
              + ' | '.join('%+.3f' % pn.loc[h, c] for c in pn.columns) + ' |')
        top = g.reindex(g.move_bp.abs().sort_values(ascending=False).index).head(20)
        a('\n**The twenty largest hour effects by absolute size:**\n')
        a(G3x.BK_tbl(top, ['currency', 'hour_ny', 'n', 'pairs', 'move_bp',
                           'spread_bp', 'move_net_bp', 't_across_pairs']))
        a('\nThe spread column is the point: an hour whose move is smaller than '
          'its own spread is not an opportunity, whatever its t.\n')
        if len(Sx):
            a('\n### Own session against overnight\n')
            a('`own = 1` marks the session whose home currencies these are: '
              'Tokyo → JPY, AUD, NZD; London → EUR, GBP, CHF; New York → USD, '
              'CAD. **London and New York overlap 08:00–11:00 NY**, and a bar '
              'in the overlap counts as own session for both sets rather than '
              'being assigned arbitrarily.\n')
            gs = roll_up(Sx, ['currency', 'session', 'side', 'own'])
            a(G3x.BK_tbl(gs.sort_values(['session', 'currency', 'side']),
                         ['currency', 'session', 'side', 'own', 'n', 'move_bp',
                          'spread_bp', 'move_net_bp', 't_across_pairs']))
            o = gs[(gs.own == 1) & (gs.side == 'in')]
            x = gs[(gs.own == 1) & (gs.side == 'out')]
            if len(o) and len(x):
                a('\nFor the currencies whose own session it is: mean move '
                  '**%+.4f bp** inside the session against **%+.4f bp** '
                  'outside it.\n' % (float(o.move_bp.mean()),
                                     float(x.move_bp.mean())))
        if len(Fx):
            a('\n### The London 4pm fix (11:00 NY)\n')
            gf = roll_up(Fx, ['currency', 'bucket'])
            a(G3x.BK_tbl(gf.sort_values(['currency', 'bucket']),
                         ['currency', 'bucket', 'n', 'move_bp', 'spread_bp',
                          'move_net_bp', 't_across_pairs']))
            ff = _net(Fx)
            fh = ff[ff.bucket == 'fix_hour']
            oh = ff[ff.bucket == 'other_hours']
            if len(fh) and len(oh):
                a('\nAbsolute move in the fix hour **%.3f bp** against '
                  '**%.3f bp** in every other hour — a ratio of **%.2fx**. '
                  'The fix hour is a VOLATILITY event; the signed move is '
                  '%+.4f bp against %+.4f bp elsewhere.\n'
                  % (float(fh.abs_move_bp.mean()), float(oh.abs_move_bp.mean()),
                     float(fh.abs_move_bp.mean() / max(1e-9, oh.abs_move_bp.mean())),
                     float(fh.move_bp.mean()), float(oh.move_bp.mean())))
        if len(Me):
            a('\n### Month end (the last three trading days)\n')
            gm = roll_up(Me, ['currency', 'bucket'])
            a(G3x.BK_tbl(gm.sort_values(['currency', 'bucket']),
                         ['currency', 'bucket', 'n', 'move_bp', 'spread_bp',
                          'move_net_bp', 't_across_pairs']))
            mm = _net(Me)
            a_, b_ = mm[mm.bucket == 'month_end'], mm[mm.bucket == 'rest']
            if len(a_) and len(b_):
                a('\nAbsolute move at month end **%.3f bp** against **%.3f bp** '
                  'on other days (**%.2fx**); signed **%+.4f** against '
                  '**%+.4f bp**.\n'
                  % (float(a_.abs_move_bp.mean()), float(b_.abs_move_bp.mean()),
                     float(a_.abs_move_bp.mean()
                           / max(1e-9, b_.abs_move_bp.mean())),
                     float(a_.move_bp.mean()), float(b_.move_bp.mean())))
    a('\n## Reading the two eras together\n')
    a('An effect that appears pre-2016 and reverses or vanishes on 2016–2020 is '
      'not an effect. The confirmation era is read ONCE and is not used to pick '
      'anything. Nothing here is carried forward into a strategy.\n')
    a('\n## Provenance\n')
    for era in ('measure', 'confirm'):
        for nm in ('hours', 'sessions', 'fix', 'monthend'):
            p_ = os.path.join(OUT, 'c3_%s_%s.csv' % (nm, era))
            if os.path.exists(p_):
                a('- `%s` — %s rows, md5 `%s`'
                  % (os.path.relpath(p_, _R), f'{len(_safe(p_)):,}',
                     hashlib.md5(open(p_, 'rb').read()).hexdigest()[:12]))
    out = out or os.path.join(OUT, 'C3_HOURLY_EFFECTS.md')
    open(out, 'w').write('\n'.join(L) + '\n')
    print('  C3_HOURLY_EFFECTS.md: %d lines -> %s'
          % (len('\n'.join(L).splitlines()), os.path.relpath(out, _R)), flush=True)
    return out


if __name__ == '__main__':
    st = G.opt('--stage', str, 'hours')
    if st == 'hours':
        stage_hours(G.opt('--era', str, 'measure'))
    elif st == 'md':
        stage_md()
    else:
        raise SystemExit('unknown stage %s' % st)
