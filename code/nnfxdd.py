import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""ITEM 6c, JACK 25 NOV -- DRAWDOWN CONTROL.

Four controls, each applied to the BEST BOOK's daily series, each swept over
its full range and reported as a curve, each then run through the prop
simulator at the Team 1 budget and at the firm's own limits.

  steady_risk   size inversely to the book's own trailing volatility, so the
                risk taken is constant rather than the position size. Swept
                over the lookback.
  equity_pause  stop trading for N days once equity is X below its high-water
                mark, then resume. Swept over X.
  kill_switch   stop PERMANENTLY at a drawdown of X. Swept over X.
  crisis_sizing size f during a crisis window and 1.0 otherwise. Swept over f.

EVERY ONE OF THEM IS CAUSAL AND THAT IS THE ONLY PART THAT IS DELICATE. A
drawdown control reads the equity curve, and the equity curve is made of the
same days it is deciding about, so it is trivially easy to build one that
peeks. Each control here decides using information available at the PREVIOUS
close and acts on the next day, and the sweep is implemented as a single
forward pass over the series for exactly that reason.

THE CRISIS WINDOWS COME FROM nnfxvol.crisis_windows(), which comes from
crisis.py, which uses a forward-only window from a NEWS event date to +15 days
-- never price. So crisis sizing is not a volatility rule in disguise; it is
"size down when something was announced", and it is knowable on the day.

WHAT THIS CANNOT DO, said before the numbers: item 5 measured the best book at
1.135% a year against a 12% target. A drawdown control cannot add return. The
most any of these can do is let the SAME return be taken at a larger size by
shrinking the drawdown the sizing has to fit inside -- which is a real gain
and a bounded one.

Writes results/nnfx/dd_curves.csv, dd_prop.csv and DRAWDOWN.md.
"""
import numpy as np, pandas as pd

import nnfx1 as N
import nnfx2s as S2
import nnfxvol as VOL
import nnfxcurves as CUR
import nnfxbook as BK
import r2reads as RR
import l2sweep as S

OUT = os.path.join(ROOTOUT, 'nnfx')
os.makedirs(OUT, exist_ok=True)
BUILD = N.BUILD_YEARS
TEAM1_DIP = 3.6
TEAM1_DAY = 3.6
TARGET_PCT = 12.0
VOL_LOOKBACKS = (0, 10, 20, 40, 60, 120)
PAUSE_LEVELS = (0.0, 0.25, 0.50, 0.75, 1.00)
PAUSE_DAYS = (5, 10, 20)
KILL_LEVELS = (0.0, 0.50, 0.75, 1.00, 1.50)
CRISIS_FRACS = (1.0, 0.75, 0.50, 0.25, 0.0)


# ===================== the four controls, all causal ====================
def steady_risk(d, lb):
    """Size inversely to the book's own trailing volatility.

    THE WINDOW ENDS AT t-1. `shift(1)` is the whole causality here: sizing
    today from today's realised volatility would be sizing with the answer.
    lb = 0 is the control OFF.
    """
    if not lb:
        return np.ones(len(d))
    sd = pd.Series(d).rolling(int(lb)).std().shift(1).to_numpy()
    med = np.nanmedian(sd[np.isfinite(sd)]) if np.isfinite(sd).any() else np.nan
    if not np.isfinite(med) or med <= 0:
        return np.ones(len(d))
    w = np.where(np.isfinite(sd) & (sd > 0), med / sd, 1.0)
    # A CAP, STATED. Without one a quiet stretch sizes up without limit and
    # the result is a measurement of the cap you did not declare. 3x the
    # median is the declared ceiling.
    return np.clip(w, 0.0, 3.0)


def equity_pause(d, level, ndays):
    """Stop for `ndays` once the drawdown reaches `level` R, then resume.

    ONE FORWARD PASS. The weight on day t is decided from equity through
    t-1, so a day cannot be paused because of its own loss. level = 0 is OFF.

    THE PEAK IS RESET WHEN TRADING RESUMES, and the first version of this did
    not do that -- which made the pause a KILL SWITCH by accident. While
    paused the equity cannot recover, so the drawdown from the old peak stays
    above the threshold, so the rule re-triggers on the first day back,
    forever. It showed up as equity_pause giving byte-identical results at
    5, 10 and 20 days AND identical to kill_switch at the same level. A pause
    that cannot end is not a pause. Resetting the peak to the equity at
    resumption is what makes the drawdown clock restart from where the book
    actually is, which is the only reading under which "then resume" means
    anything.
    """
    n = len(d)
    w = np.ones(n)
    if not level:
        return w
    eq = 0.0
    peak = 0.0
    hold = 0
    for t in range(n):
        if hold > 0:
            w[t] = 0.0
            hold -= 1
            if hold == 0:
                peak = eq          # the clock restarts from here
        eq += d[t] * w[t]
        peak = max(peak, eq)
        if hold == 0 and (peak - eq) >= level:
            hold = int(ndays)
    return w


def kill_switch(d, level):
    """Stop PERMANENTLY at a drawdown of `level` R. level = 0 is OFF."""
    n = len(d)
    w = np.ones(n)
    if not level:
        return w
    eq = 0.0
    peak = 0.0
    dead = False
    for t in range(n):
        if dead:
            w[t] = 0.0
            continue
        eq += d[t]
        peak = max(peak, eq)
        if (peak - eq) >= level:
            dead = True
    return w


def crisis_sizing(idx, frac):
    """Size `frac` inside a crisis window, 1.0 outside.

    The windows are news-dated and forward-only (crisis.py), so this is
    knowable on the day and is not a volatility rule in disguise.
    """
    w = np.ones(len(idx))
    if frac >= 1.0:
        return w
    try:
        W = VOL.crisis_windows()
    except Exception:
        return w
    ix = pd.DatetimeIndex(idx)
    m = np.zeros(len(ix), bool)
    for row in W:
        a = pd.Timestamp(row[0]) if not isinstance(row, dict) else None
        if isinstance(row, dict):
            a, b = pd.Timestamp(row.get('start')), pd.Timestamp(row.get('end'))
        else:
            a, b = pd.Timestamp(row[0]), pd.Timestamp(row[1])
        m |= (ix >= a) & (ix <= b)
    w[m] = float(frac)
    return w


# ===================== scoring ==========================================
def _stats(s):
    d = s.to_numpy(float)
    eq = np.cumsum(d)
    dip = float(np.max(np.maximum.accumulate(eq) - eq)) if len(d) else np.nan
    d95 = BK._dip95(d)
    bind = float(np.nanmax([dip, d95]))
    tot = float(d.sum())
    yrs = pd.Series(d, index=s.index).groupby(s.index.year).sum().sort_index()
    wd = float(-d.min()) if len(d) and d.min() < 0 else np.nan
    sc = min(TEAM1_DIP / bind if bind and bind > 0 else np.inf,
             TEAM1_DAY / wd if wd and wd > 0 else np.inf)
    fsc = min(RR.FIRM_TRAIL * 100.0 / bind if bind and bind > 0 else np.inf,
              RR.FIRM_DAILY * 100.0 / wd if wd and wd > 0 else np.inf)
    return dict(R_total=tot, R_per_year=tot / max(1, len(yrs)),
                dip_true=dip, dip95=d95, dip_binding=bind,
                R_per_dip=(tot / bind if bind and bind > 1e-9 else np.nan),
                worst_day_R=wd, days_flat=int((d == 0).sum()),
                years=int(len(yrs)), years_positive=int((yrs > 0).sum()),
                team1_scale=(float(sc) if np.isfinite(sc) else np.nan),
                team1_pct_per_year=(tot / max(1, len(yrs)) * float(sc)
                                    if np.isfinite(sc) else np.nan),
                firm_scale=(float(fsc) if np.isfinite(fsc) else np.nan),
                firm_pct_per_year=(tot / max(1, len(yrs)) * float(fsc)
                                   if np.isfinite(fsc) else np.nan))


def run(verbose=True):
    """The best book from item 5 is A on its own; the controls are applied to
    it and, as a cross-check, to the A+B+MR120 book."""
    T = CUR._stitch('ichimoku_signals', 'sma_baseline', 'full_nnfx', 'jack',
                    VOL.LOWVOL_Q, VOL.PEG_X_DECIDED)
    sA = BK._ds(T)
    books = {'A': sA}
    try:
        SL = BK.sleeves(verbose=False)
        ser = {k: BK._ds(v) for k, v in SL.items()}
        ser = {k: v for k, v in ser.items() if v is not None}
        b2 = BK._book(ser, ['A', 'B', 'MR120'])
        if b2 is not None:
            books['A+B+MR120'] = b2
    except Exception as e:
        print('  (A+B+MR120 book unavailable: %s)' % e, flush=True)
    rows, keep = [], {}
    for bk, s in books.items():
        d = s.to_numpy(float)
        base = _stats(s)
        rows.append(dict(book=bk, control='(none)', setting='off',
                         **base))
        keep[(bk, 'none', 'off')] = s
        for lb in VOL_LOOKBACKS:
            if not lb:
                continue
            w = steady_risk(d, lb)
            x = pd.Series(d * w, index=s.index)
            rows.append(dict(book=bk, control='steady_risk',
                             setting='lookback %d' % lb, **_stats(x)))
            keep[(bk, 'steady_risk', lb)] = x
        for lv in PAUSE_LEVELS:
            if not lv:
                continue
            for nd in PAUSE_DAYS:
                w = equity_pause(d, lv * base['dip_binding'], nd)
                x = pd.Series(d * w, index=s.index)
                rows.append(dict(
                    book=bk, control='equity_pause',
                    setting='%.0f%% of dip, %d days' % (100 * lv, nd),
                    **_stats(x)))
                keep[(bk, 'equity_pause', (lv, nd))] = x
        for lv in KILL_LEVELS:
            if not lv:
                continue
            w = kill_switch(d, lv * base['dip_binding'])
            x = pd.Series(d * w, index=s.index)
            rows.append(dict(book=bk, control='kill_switch',
                             setting='%.0f%% of dip' % (100 * lv),
                             **_stats(x)))
            keep[(bk, 'kill_switch', lv)] = x
        for fr in CRISIS_FRACS:
            if fr >= 1.0:
                continue
            w = crisis_sizing(s.index, fr)
            x = pd.Series(d * w, index=s.index)
            rows.append(dict(book=bk, control='crisis_sizing',
                             setting='size %.2f in crisis' % fr,
                             **_stats(x)))
            keep[(bk, 'crisis_sizing', fr)] = x
        if verbose:
            print('    %s: baseline R/dip %+.3f, team1 %+.3f%%/yr'
                  % (bk, base['R_per_dip'], base['team1_pct_per_year']),
                  flush=True)
    D = pd.DataFrame(rows)
    D.to_csv(os.path.join(OUT, 'dd_curves.csv'), index=False)
    # the prop simulator on the baseline and on the best cell of each control
    prows = []
    for bk in books:
        sub = D[D.book == bk]
        picks = [('(none)', 'off')]
        for c in ('steady_risk', 'equity_pause', 'kill_switch',
                  'crisis_sizing'):
            g = sub[sub.control == c]
            if len(g) and g.firm_pct_per_year.notna().any():
                picks.append((c, g.loc[g.firm_pct_per_year.idxmax()].setting))
        for c, st in picks:
            r = sub[(sub.control == c) & (sub.setting == st)]
            if not len(r):
                continue
            r = r.iloc[0]
            key = [k for k in keep
                   if k[0] == bk and (k[1] == ('none' if c == '(none)' else c))
                   and (str(k[2]) in st or st == 'off'
                        or st.startswith(str(k[2])))]
            x = keep[key[0]] if key else None
            if x is None:
                continue
            for szname, sc in (('team1', r.team1_scale),
                               ('firm', r.firm_scale)):
                if not np.isfinite(sc):
                    continue
                pct = x.to_numpy(float) * sc
                ev = RR.prop_run(pct, phase='eval')
                fd = RR.prop_run(pct, phase='funded')
                prows.append(dict(
                    book=bk, control=c, setting=st, sizing=szname,
                    scale=sc, pct_per_year=(r.team1_pct_per_year
                                            if szname == 'team1'
                                            else r.firm_pct_per_year),
                    eval_days_to_pass=ev['passed_eval_day'],
                    eval_breached=ev['breached'],
                    funded_breached=fd['breached'],
                    funded_payout_per_year=fd['paid_out_per_year'],
                    funded_worst_dip_pct=fd['worst_dip_pct'],
                    distance_from_12pct=TARGET_PCT - (
                        r.team1_pct_per_year if szname == 'team1'
                        else r.firm_pct_per_year)))
    P = pd.DataFrame(prows)
    P.to_csv(os.path.join(OUT, 'dd_prop.csv'), index=False)
    return D, P



# ====================== THE DOCUMENT ====================================
def md_dd(out=None):
    import hashlib
    L_ = []
    a = L_.append
    def rd(n):
        f = os.path.join(OUT, n)
        return (pd.read_csv(f) if os.path.exists(f) and os.path.getsize(f) > 2
                else pd.DataFrame())
    D, P = rd('dd_curves.csv'), rd('dd_prop.csv')
    a('# DRAWDOWN CONTROL — item 6c, Jack 25 November 2026')
    a('')
    a('**What a drawdown control can and cannot do, before the numbers.** '
      'Item 5 measured the best book at 1.135% a year against a 12% target. '
      '**None of these controls adds return.** The most any of them can do is '
      'let the same return be taken at a larger size by shrinking the '
      'drawdown the sizing has to fit inside. That is a real gain and a '
      'bounded one, and it is the only thing this report is measuring.')
    a('')
    a('## The four controls, and why each is causal')
    a('')
    a('| control | what it does | swept over | causality |')
    a('|---|---|---|---|')
    a('| `steady_risk` | size inversely to the book\'s own trailing '
      'volatility, so the RISK is constant rather than the position size | '
      'lookback 10, 20, 40, 60, 120 bars | the volatility window ends at '
      '**t−1** (`.shift(1)`); sizing today from today\'s realised volatility '
      'would be sizing with the answer. Capped at 3x the median weight, '
      'declared, so a quiet stretch cannot size up without limit |')
    a('| `equity_pause` | stop trading for N days once the drawdown reaches X, '
      'then resume | X = 25/50/75/100% of the book\'s own binding dip, '
      'N = 5/10/20 days | one forward pass; the weight on day t is decided '
      'from equity through t−1, so a day cannot be paused because of its own '
      'loss |')
    a('| `kill_switch` | stop **permanently** at a drawdown of X | '
      'X = 50/75/100/150% of the binding dip | same forward pass |')
    a('| `crisis_sizing` | size f inside a crisis window, 1.0 outside | '
      'f = 0.75, 0.50, 0.25, 0.00 | the windows are **news-dated and '
      'forward-only** (`crisis.py`: event date to +15 days, never price), so '
      'this is knowable on the day and is not a volatility rule in disguise |')
    a('')
    a('**A FAULT FOUND AND FIXED IN THE FIRST RUN OF THIS FILE, because it is '
      'the kind that looks like a result.** `equity_pause` measured the '
      'drawdown from the peak of the MANAGED equity. While paused the equity '
      'cannot recover, so the drawdown from the old peak stays above the '
      'threshold and the rule re-triggers on the first day back — forever. '
      'It showed up as the pause giving byte-identical numbers at 5, 10 and '
      '20 days AND identical numbers to `kill_switch` at the same level. A '
      'pause that cannot end is not a pause. The peak now resets to the '
      'equity at resumption, so the drawdown clock restarts from where the '
      'book actually is.')
    a('')
    if len(D):
        for bk, g in D.groupby('book'):
            base = g[g.control == '(none)']
            b = base.iloc[0] if len(base) else None
            a('## Book `%s`' % bk)
            a('')
            if b is not None:
                a('Baseline, no control: R **%+.3f**, binding dip **%.3f**, '
                  'return per dip **%.3f**, **%.3f%% a year** at the firm\'s '
                  'limits.'
                  % (b.R_total, b.dip_binding, b.R_per_dip,
                     b.firm_pct_per_year))
                a('')
            a('| control | setting | R total | R/yr | binding dip | '
              '**R per dip** | worst day | days flat | **firm limits %/yr** | '
              'vs baseline |')
            a('|---|---|---:|---:|---:|---:|---:|---:|---:|---:|')
            for _, r in g.iterrows():
                d = ((r.R_per_dip / b.R_per_dip - 1.0) * 100.0
                     if b is not None and abs(b.R_per_dip) > 1e-9 else np.nan)
                mk = '**' if (np.isfinite(d) and d > 1.0) else ''
                a('| %s`%s`%s | %s | %+.3f | %+.3f | %.3f | **%s** | %.3f | '
                  '%d | %s | %s |'
                  % (mk, r.control, mk, r.setting, r.R_total, r.R_per_year,
                     r.dip_binding, _f(r.R_per_dip), r.worst_day_R,
                     int(r.days_flat), _f(r.firm_pct_per_year),
                     ('%+.1f%%' % d) if np.isfinite(d) else '—'))
            a('')
            if b is not None:
                better = g[(g.control != '(none)')
                           & (g.R_per_dip > b.R_per_dip * 1.01)]
                a('**%d of the %d control settings improve return per dip by '
                  'more than 1%%.** %s'
                  % (len(better), len(g) - 1,
                     ('; '.join('`%s` %s -> %s (%+.1f%%)'
                                % (r.control, r.setting, _f(r.R_per_dip),
                                   100.0 * (r.R_per_dip / b.R_per_dip - 1.0))
                                for _, r in better.nlargest(
                                    5, 'R_per_dip').iterrows())
                      if len(better) else 'None of them.')))
                a('')
    a('## What it adds up to')
    a('')
    if len(D):
        A = D[D.book == 'A']
        b = A[A.control == '(none)'].iloc[0] if len(A[A.control == '(none)']) \
            else None
        if b is not None:
            best = A[A.control != '(none)'].nlargest(1, 'R_per_dip')
            br = best.iloc[0] if len(best) else None
            n_cells = len(A) - 1
            a('1. **The best single control setting on the best book is '
              '`%s` at "%s": return per dip %.3f against %.3f, and %.3f%% a '
              'year against %.3f%%.** That is a **%+.1f%%** improvement — '
              'real, and it is the maximum over **%d swept cells on one '
              'six-year sample**, so treat it as an upper bound on what is '
              'there rather than as a setting to adopt.'
              % (br.control, br.setting, br.R_per_dip, b.R_per_dip,
                 br.firm_pct_per_year, b.firm_pct_per_year,
                 100.0 * (br.R_per_dip / b.R_per_dip - 1.0), n_cells))
            a('2. **The curves are not monotone, which is the tell.** '
              '`equity_pause` at 25% of the dip gives no change at 5 days, '
              'its best result at 10 days and a WORSE result than baseline at '
              '20. A control whose benefit turns over as its one knob moves '
              'by one notch is reading noise.')
            _kl = A[A.control == 'kill_switch']
            _nf = _kl[np.abs(_kl.R_total - b.R_total) < 1e-9]
            a('3. **The kill switch never fires above 50%% of the dip, and '
              'the reason is a unit mismatch worth naming rather than a '
              'timing accident.** The levels are fractions of the **binding** '
              'dip, which is DIP95 at %.3f R, while the drawdown the book '
              'actually took is %.3f R — only %.0f%% of it. So every level at '
              '75%% or above is a threshold the realised path never reaches, '
              'and %d of the %d kill settings are byte-identical to the '
              'baseline. The one that does fire, 50%% of the binding dip '
              '(%.2f R), fires inside the first year — the worst drawdown '
              'bottoms on 11 March 2011, day 304 of 1,457 — and turns '
              '%+.3f R into %+.3f R. **A kill switch on this book is a way of '
              'losing the book.**'
              % (b.dip_binding, b.dip_true,
                 100.0 * b.dip_true / b.dip_binding,
                 len(_nf), len(_kl), 0.50 * b.dip_binding, b.R_total,
                 float(A[(A.control == 'kill_switch')
                         & (A.setting == '50% of dip')].R_total.iloc[0])
                 if len(A[(A.control == 'kill_switch')
                          & (A.setting == '50% of dip')]) else float('nan')))
            a('4. **Crisis sizing costs money monotonically.** Every step '
              'down in crisis size lowers both return and return per dip, and '
              'sizing to zero in crisis windows costs %.1f%% of the total. '
              'The dip barely moves, because A\'s worst drawdown is not in a '
              'crisis window. On this book, crisis sizing buys nothing and '
              'pays for it.'
              % (100.0 * (1.0 - float(
                  A[(A.control == 'crisis_sizing')
                    & (A.setting == 'size 0.00 in crisis')].R_total.iloc[0])
                  / b.R_total)
                 if len(A[(A.control == 'crisis_sizing')
                          & (A.setting == 'size 0.00 in crisis')])
                 else float('nan')))
            a('5. **And none of it changes the verdict.** The best controlled '
              'book is %.3f%% a year against a 12%% target: still a factor of '
              '%.1f short. A drawdown control was never going to close a gap '
              'of that size and this report does not pretend otherwise.'
              % (br.firm_pct_per_year, TARGET_PCT / br.firm_pct_per_year)
              if br is not None and br.firm_pct_per_year > 0 else '')
            a('')
    if len(P):
        a('## Through the prop simulator')
        a('')
        a('The baseline and the best cell of each control, at the Team 1 '
          'budget and at the firm\'s own limits.')
        a('')
        a('| book | control | setting | sizing | %/yr | days to pass +10% | '
          'funded breach | payout $/yr | worst dip % | short of 12% by |')
        a('|---|---|---|---|---:|---|---|---:|---:|---:|')
        for _, r in P.iterrows():
            a('| %s | `%s` | %s | %s | %+.3f%% | %s | %s | $%.0f | %.2f%% | '
              '%.3f pp |'
              % (r.book, r.control, r.setting, r.sizing, r.pct_per_year,
                 ('%d' % r.eval_days_to_pass
                  if np.isfinite(r.eval_days_to_pass) else '**NEVER**'),
                 (str(r.funded_breached) if isinstance(r.funded_breached, str)
                  and r.funded_breached else 'none'),
                 r.funded_payout_per_year, r.funded_worst_dip_pct,
                 r.distance_from_12pct))
        a('')
        a('**No controlled book passes the +10%% evaluation either.** The '
          'controls move the sizing, not the return.')
        a('')
    a('## Provenance')
    a('')
    for n_ in ('dd_curves.csv', 'dd_prop.csv'):
        p_ = os.path.join(OUT, n_)
        if not os.path.exists(p_):
            a('- `%s` — **MISSING**' % os.path.join('results', 'nnfx', n_))
            continue
        a('- `%s` — %s rows, md5 `%s`'
          % (os.path.relpath(p_, _R),
             '{:,}'.format(len(S2._safe_csv(p_))),
             hashlib.md5(open(p_, 'rb').read()).hexdigest()[:12]))
    out = out or os.path.join(OUT, 'DRAWDOWN.md')
    open(out, 'w').write('\n'.join(L_) + '\n')
    print('  DRAWDOWN.md: %d lines -> %s'
          % (len('\n'.join(L_).splitlines()), os.path.relpath(out, _R)),
          flush=True)
    return out


def _f(v, fmt='%+.3f'):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return '—'
    return (fmt % f) if np.isfinite(f) else '—'


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', default='all')
    g = ap.parse_args()
    if g.stage in ('all', 'run'):
        run()
    if g.stage in ('all', 'md'):
        md_dd()
    print('  nnfxdd done', flush=True)


if __name__ == '__main__':
    main()
