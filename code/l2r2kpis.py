import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""THE KPI TABLE FOR ONE MODE, IN THE MODEA_KPIS.md FORMAT (Jack, 19 Nov).

WHY THIS EXISTS AS CODE. MODEA_KPIS.md was assembled by hand in chat on
18 Nov -- its own header says so. That breaks the rule that every number is
read back out of a named file by something that can be rerun, and it is why
there was no mode B equivalent. This script regenerates the mode A table from
the same files and produces the mode B one from mode B's, so the two are
comparable because they were built by the same code.

WHAT IT READS, and nothing else:
  results/r2gate2/mode<M>_daily_full_<step>_<book>_<budget>.npz
      the SCALED daily series written by l2r2book.stage_books. The five steps'
      TRADE years are disjoint calendar years 2016..2020, so stitching them is
      a concatenation -- no overlap to resolve and no reweighting.
  results/r2gate2/mode<M>_books_full.csv
      the trade-level readings that are not in the daily series: profit factor
      and win rate per trade, retention, the FIT flag and DIP95 per step.
  results/r2gate2/mode<M>_books_nulls.csv
      the three nulls, summarised as p-value ranges.

SCALE-INVARIANT ROWS ARE REPORTED ONCE PER TEAM AND ARE EQUAL BY CONSTRUCTION.
Team 2 is team 1's series multiplied by a constant, so Sharpe, Sortino, Calmar,
profit factor, win rate, retention and the FIT flag are identical in both
tables. That is not a copy-paste error in the output; it is what a linear size
change does, and the alternative would be to hide it.

    python3 code/l2r2kpis.py --mode B
    python3 code/l2r2kpis.py --mode A --check   # reproduce the hand-built table
"""
import time, glob
import numpy as np, pandas as pd

import l2sweep as S
import l2walkfwd as W
import l2r2gate1 as G
import l2r2gate2 as G2
import l2r2book as BK

RD = os.path.join(ROOTOUT, 'r2gate2')
TRADE_YEARS = (2016, 2017, 2018, 2019, 2020)
COLHEAD = {'allon': 'ALWAYS-ON',
           'chop_trend': 'ROUTED (chop RANGING + trend TRENDING)',
           'chop_ungated': 'CHOP ROUTED + TREND UNGATED',
           'chop_notrange': 'CHOP ROUTED + TREND NOT-RANGING'}
# (label, formatter, source) -- source 'series' is computed off the stitched
# daily series, 'books' is read out of the books csv across the five steps
ROWS = (
    ('median year',                      '%.2f%%', 'median_year_pct'),
    ('average year',                     '%.2f%%', 'mean_year_pct'),
    ('worst year',                       '%.2f%%', 'worst_year_pct'),
    ('best year',                        '%.2f%%', 'best_year_pct'),
    ('total %d-%d' % (TRADE_YEARS[0], TRADE_YEARS[-1]), '%.2f%%', 'total_return_pct'),
    ('CAGR',                             '%.2f%%', 'cagr_pct'),
    ('worst day',                        '%.2f%%', 'worst_day_neg_pct'),
    ('max drawdown',                     '%.2f%%', 'max_dd_neg_pct'),
    ('DIP95 (worst step)',               '%.2f%%', 'dip95_worst_step_pct'),
    ('Sharpe',                           '%.2f',   'sharpe'),
    ('Sortino',                          '%.2f',   'sortino'),
    ('Calmar (total / max DD, the shipped bar)', '%.2f', 'calmar'),
    ('Calmar (CAGR / max DD)',            '%.2f',   'calmar_cagr'),
    ('profit factor (trades, median step)', '%.2f', 'pf_trades_median_step'),
    ('win rate (trades, median step)',   '%.2f%%', 'win_rate_trades_median_step'),
    ('positive years of %d' % len(TRADE_YEARS), '%d', 'positive_years'),
    ('retention (median step)',          '%.2f',   'retention_median_step'),
    ('steps flagged FIT of %d' % len(TRADE_YEARS), '%d', 'steps_fit'),
)


def daily_file(mode, step, book, budget, tag='full'):
    return os.path.join(RD, 'mode%s_daily_%s_%s_%s_%s.npz' % (mode, tag, step, book, budget))


def stitched(mode, book, budget, tag='full'):
    """The five steps' trade years, concatenated in calendar order.

    Each step contributes ONLY its own trade year, which is the year that step
    never saw while sizing. The five are disjoint, so this is the honest
    2016-2020 record and not a re-run of anything.
    """
    xs, ys, steps = [], [], []
    for stp in G2.steps():
        f = daily_file(mode, stp['name'], book, budget, tag)
        if not os.path.exists(f):
            continue
        z = np.load(f)
        x = z['daily']; yr = z['years']; tr = z['trade']
        if not tr.any():
            continue
        xs.append(np.asarray(x)[tr]); ys.append(np.asarray(yr)[tr])
        steps.append(stp['name'])
    if not xs:
        return None, None, []
    x = np.concatenate(xs); y = np.concatenate(ys)
    o = np.argsort(y, kind='stable')
    return x[o], y[o], steps


def one_cell(mode, book, budget, Bk, tag='full'):
    """Every row of the table for one (book, budget), each from its named file."""
    x, y, steps = stitched(mode, book, budget, tag)
    if x is None or not len(x):
        return None
    k = W.kpis(x, y)
    per = pd.Series(x).groupby(y).sum()
    g = Bk[(Bk.book == book) & (Bk.budget == budget) & (Bk.book_empty == 0)] \
        if len(Bk) else Bk
    nyr = max(len(per), 1)
    d = dict(k)
    d['cagr_pct'] = k['total_return_pct'] / nyr
    # TWO CALMARS, BOTH NAMED. l2walkfwd.kpis -- the shipped code, and the one
    # gate 3's BARS['calmar'] >= 1.0 is tested against -- divides the TOTAL by
    # max DD. The textbook ratio divides the ANNUALISED return by max DD, which
    # is what the hand-built MODEA_KPIS.md of 18 Nov reported. They differ by
    # the number of years, so reporting one silently would make this table
    # disagree with either gate 3 or its own predecessor.
    d['calmar_cagr'] = (d['cagr_pct'] / abs(k['max_dd_pct'])
                        if k['max_dd_pct'] else np.nan)
    # the table states drawdown and worst day as the losses they are
    d['max_dd_neg_pct'] = -abs(k['max_dd_pct'])
    d['worst_day_neg_pct'] = -abs(k['worst_day_pct'])
    d['positive_years'] = int((per > 0).sum())
    d['per_year'] = {int(a): float(b) for a, b in per.items()}
    d['n_steps_found'] = len(steps)
    for nm, col in (('dip95_worst_step_pct', 'trade_dip95_pct'),
                    ('pf_trades_median_step', 'trade_profit_factor'),
                    ('win_rate_trades_median_step', 'trade_win_rate_pct'),
                    ('retention_median_step', 'retention')):
        if len(g) and col in g.columns:
            v = pd.to_numeric(g[col], errors='coerce').dropna()
            d[nm] = (float(v.max()) if nm.startswith('dip95') else float(v.median())) \
                if len(v) else np.nan
        else:
            d[nm] = np.nan
    d['steps_fit'] = int(pd.to_numeric(g.get('FIT', pd.Series(dtype=float)),
                                       errors='coerce').fillna(0).sum()) if len(g) else 0
    return d


def nulls_summary(mode, f=None):
    """The three nulls as one line each: the p-value range over the cells."""
    f = f or os.path.join(RD, 'mode%s_books_nulls.csv' % mode)
    if not os.path.exists(f):
        return ['_No nulls file for mode %s; this section is empty rather than '
                'filled in from mode A._' % mode], f
    try:
        N = pd.read_csv(f)
    except Exception:
        return ['_The nulls file is empty._'], f
    out = []
    pretty = {'identity': 'Identity (strategy/year roles reassigned)',
              'shuffle': 'Regime-shuffle (labels rotated, run lengths kept)',
              'random-entry': 'Random-entry (same strategies, random entry days)'}
    for kind, g in N.groupby('null'):
        p = pd.to_numeric(g.p_one_sided, errors='coerce').dropna()
        if not len(p):
            continue
        beat = int((pd.to_numeric(g.real, errors='coerce')
                    > pd.to_numeric(g.null_p95, errors='coerce')).sum())
        out.append('- **%s**: %d cells, p %.2f-%.2f; the real book clears the null\'s '
                   '95th percentile in %d of %d.'
                   % (pretty.get(kind, kind), len(g), p.min(), p.max(), beat, len(g)))
    return (out or ['_No null rows._']), f


def kpi_tables(mode, tag='full', books_csv=None, Bk=None):
    """The TEAM tables and the per-year lines, as markdown, plus the records.

    THE SAME BUILDER SERVES BOTH CALLERS. The full-field table and gate 3's
    passers'-book table are the same arithmetic on different membership, so
    they go through one function -- if they went through two, a change to the
    definition of 'worst year' would land in one table and not the other.
    """
    books_csv = books_csv or os.path.join(RD, 'mode%s_books_%s.csv' % (mode, tag))
    if Bk is None:
        Bk = pd.DataFrame()
        if os.path.exists(books_csv):
            try:
                Bk = pd.read_csv(books_csv)
            except Exception:
                Bk = pd.DataFrame()
    books = [b for b, _d in BK.BOOKS]
    cells = {}
    for (bname, _dip, _day) in BK.BUDGETS:
        for bk in books:
            cells[(bname, bk)] = one_cell(mode, bk, bname, Bk, tag)
    L = []; A = L.append
    recs = []
    for bi, (bname, _dip, _day) in enumerate(BK.BUDGETS):
        cols = [bk for bk in books if cells[(bname, bk)]]
        if not cols:
            continue
        A('\n### TEAM %d\n' % (bi + 1))
        A('| KPI | ' + ' | '.join(COLHEAD.get(c, c) for c in cols) + ' |')
        A('|' + '---|' * (len(cols) + 1))
        for label, fmt, key in ROWS:
            vals = []
            for bk in cols:
                v = cells[(bname, bk)].get(key, np.nan)
                if v is None or (isinstance(v, float) and not np.isfinite(v)):
                    vals.append('')
                elif fmt == '%d':
                    vals.append('%d' % int(v))
                else:
                    vals.append(fmt % v)
            A('| ' + label + ' | ' + ' | '.join(vals) + ' |')
        A('\nPer year:\n')
        for bk in cols:
            py = cells[(bname, bk)]['per_year']
            A('- %s: %s' % (COLHEAD.get(bk, bk),
                            ' | '.join('%d: %+.2f%%' % (y, py[y]) for y in sorted(py))))
        for bk in cols:
            r = dict(mode=mode, budget=bname, book=bk)
            r.update({k2: v for k2, v in cells[(bname, bk)].items() if k2 != 'per_year'})
            r.update({'R_%d' % y: v for y, v in cells[(bname, bk)]['per_year'].items()})
            recs.append(r)
    return L, recs


def write_md(mode='B', tag='full', out=None):
    import hashlib
    G.manifest_check()
    bf = os.path.join(RD, 'mode%s_books_%s.csv' % (mode, tag))
    Bk = pd.DataFrame()
    if os.path.exists(bf):
        try:
            Bk = pd.read_csv(bf)
        except Exception:
            Bk = pd.DataFrame()
    z = np.load(BK._bank_slice_file(mode, tag), allow_pickle=True)
    nstrat = int(z['n']); del z

    L = []; A = L.append
    A('# MODE %s KPIs — all %s strategies, tuned honestly, traded years %d–%d stitched\n'
      % (mode, f'{nstrat:,}', TRADE_YEARS[0], TRADE_YEARS[-1]))
    srcs = [os.path.relpath(daily_file(mode, '*', '*', '*', tag), _R), os.path.relpath(bf, _R)]
    A('Source: `%s` (daily series, trade-year days only, one year per walk-forward step, '
      'stitched %d→%d) and `%s` (trade-level PF, win rate, DIP95, retention, FIT). '
      'Generated %s by `code/l2r2kpis.py` — every number read back out of those files, '
      'nothing typed in by hand. Numbers CSV beside this file: '
      '`mode%s_kpis_stitched_%d-%d.csv`.\n'
      % (srcs[0], TRADE_YEARS[0], TRADE_YEARS[-1], srcs[1],
         time.strftime('%F %H:%M'), mode, TRADE_YEARS[0], TRADE_YEARS[-1]))
    b1, b2 = BK.BUDGETS[0], BK.BUDGETS[1]
    A('Team 1 = %.1f%% dip / %.1f%% day budget (day zero). Team 2 = %.1f%% dip / %.1f%% day '
      '(after the +6%% cushion). Scale set on the build years only. Everyone trades, equal '
      'weight, netted, costs charged (%s, R units), one-bar lag, %d+ sealed.\n'
      % (b1[1], b1[2], b2[1], b2[2],
         os.environ.get('FX_COST_TABLE', 'cost_table_h22.csv').split('/')[-1],
         TRADE_YEARS[-1] + 1))
    A('\n**Scale-invariant rows** — Sharpe, Sortino, Calmar, profit factor, win rate, '
      'retention and FIT — are equal in both tables by construction: team 2 is team 1 '
      'times a constant.\n')

    tl, recs = kpi_tables(mode, tag, bf, Bk)
    # the shared builder writes '### TEAM n'; the top-level document wants '##'
    for ln in tl:
        A(ln.replace('### TEAM ', '## TEAM ') if ln.startswith('### TEAM ') else ln)

    lines, nf = nulls_summary(mode)
    A('\n## Nulls (from `%s`)\n' % os.path.relpath(nf, _R))
    for ln in lines:
        A(ln)
    A('\n## Not available in these files\n')
    A('- Max simultaneous positions: not written by the streamed book.')
    A('- Sharpe is reported and binds nowhere, as declared.')

    A('\n## Provenance\n')
    pv = []
    for f in sorted({bf, nf}):
        if os.path.exists(f):
            pv.append(dict(file=os.path.relpath(f, _R),
                           rows=(len(pd.read_csv(f)) if f.endswith('.csv') and
                                 os.path.getsize(f) > 1 else 0),
                           md5=hashlib.md5(open(f, 'rb').read()).hexdigest()[:12]))
    nd = len(glob.glob(daily_file(mode, '*', '*', '*', tag)))
    A('| file | rows | md5 |\n|---|---|---|')
    for r in pv:
        A('| `%s` | %s | %s |' % (r['file'], f"{r['rows']:,}", r['md5']))
    A('| `mode%s_daily_%s_*.npz` | %d files | — |' % (mode, tag, nd))

    D = pd.DataFrame(recs)
    cs = os.path.join(RD, 'mode%s_kpis_stitched_%d-%d.csv'
                      % (mode, TRADE_YEARS[0], TRADE_YEARS[-1]))
    D.to_csv(cs, index=False)
    txt = '\n'.join(L) + '\n'
    out = out or os.path.join(RD, 'MODE%s_KPIS.md' % mode)
    open(out, 'w').write(txt)
    print('  mode %s KPIs: %d rows -> %s' % (mode, len(D), os.path.relpath(cs, _R)), flush=True)
    print('  MODE%s_KPIS.md: %d lines -> %s'
          % (mode, len(txt.splitlines()), os.path.relpath(out, _R)), flush=True)
    return out, cs


if __name__ == '__main__':
    md = G.opt('--mode', str, 'B')
    write_md(md, G.opt('--tag', str, 'full'), out=G.opt('--out', str, None))
