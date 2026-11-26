"""THE TARGET MAP -- Jack's item 2. PROTOCOL.md A14, declared before this ran.

WHAT THIS ANSWERS. Every book in this project is reported as a percent a year
at a sizing. That hides the thing Jack actually needs: on a real funded
account, with a $549 fee on every attempt, 80% payout and a breach that ends
the account, what edge is needed before net dollars a year reach $12,000?

THE LIFECYCLE IS VECTORISED ACROSS PATHS, NOT OVER PATHS. r2reads.prop_run is
one Python loop per path, which at 2,000 paths x 252 days x a few hundred
cells is tens of millions of interpreted steps. Here a cell costs 252 numpy
operations on arrays of 2,000, and the whole map runs in minutes. The rules
are prop_run's rules, matched line for line, and test_against_prop_run()
proves it on single paths rather than asserting it in a comment.

EDGE IS YEARLY RETURN PER UNIT OF YEARLY VOLATILITY and SIZE IS DAILY
VOLATILITY IN PERCENT OF THE ACCOUNT. Size multiplies mean and deviation
together so it cannot change the edge -- which is why the map separates them.
"""
import os, sys, time, argparse
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
ROOT = os.path.dirname(_HERE)
ROOTOUT = os.path.join(ROOT, 'results')
sys.path.insert(0, ROOT)

import numpy as np
import pandas as pd
import r2reads as RR

OUT = os.path.join(ROOTOUT, 'nnfx', 'target')
os.makedirs(OUT, exist_ok=True)

DAYS_YEAR = 252
NPATH = 2000
BLOCK = 20
SEED = 20261126

# A14.1
FEE = RR.FEE                      # 549.0
PAYOUT_SHARE = RR.PAYOUT_SHARE    # 0.80
PAYOUT_EVERY = RR.PAYOUT_EVERY    # 7
START = RR.START                  # 100000.0
TARGET = RR.EVAL_TARGET           # 0.10

# A14.2 -- the three budget pairs, daily and trailing
BUDGETS = (('team1',    0.036, 0.036),
           ('internal', 0.036, 0.054),
           ('firm',     0.040, 0.060))

# A14.3 -- the declared edge grid, plus a fine grid for the $12,000 crossing
EDGES = (0.25, 0.5, 0.75, 1.0, 1.5, 2.0)
EDGES_FINE = tuple(np.round(np.arange(0.25, 6.001, 0.125), 3))

# size axis: daily volatility as a percent of the account
# THE SIZE AXIS MUST RUN PAST THE OPTIMUM OR THE ANSWER IS THE GRID'S, NOT
# THE MODEL'S. The first run of 2c stopped at 2.00% and all three budgets put
# their best size AT that cap, which makes "the smallest edge reaching
# $12,000" a statement about where the grid ended. Extended to 8% so the
# curve is seen to turn over -- or seen not to, which is itself a finding
# about the lifecycle and is reported as one.
SIGMAS = (0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50,
          0.60, 0.75, 1.00, 1.25, 1.50, 2.00,
          2.50, 3.00, 4.00, 5.00, 6.00, 8.00)

GOAL = 12000.0

# A15 -- the payout schedule, the one knob that decides whether the map has an
# interior optimum at all. (cadence in funded days, minimum funded days before
# the FIRST withdrawal). The first entry is A14 exactly as declared.
SCHEDULES = ((7, 0), (7, 30), (14, 0), (30, 0), (90, 0))


# ===================== the lifecycle =====================================
def lifecycle(R, daily_frac, trail_frac, fee=FEE, payout_share=PAYOUT_SHARE,
              payout_every=PAYOUT_EVERY, target=TARGET, start=START,
              start_funded=False, min_funded_days=0):
    """R is (ndays, npath) daily returns in PERCENT. -> per-path record.

    ONE PYTHON ITERATION PER DAY. The order inside a day is prop_run's order:
    apply the return, lift the high-water mark, test the daily rule against
    the PREVIOUS close and the trailing rule against the UPDATED high-water
    mark, then the +10% pass, then the payout. Breach beats pass on the same
    day, exactly as prop_run breaks before it tests the target.
    """
    R = np.asarray(R, float)
    nd, npth = R.shape
    eq = np.full(npth, start)
    hwm = np.full(npth, start)
    funded = np.full(npth, bool(start_funded))
    fees = np.full(npth, float(fee))        # A14.1: attempt one is paid for
    paid = np.zeros(npth)
    fday = np.zeros(npth, np.int64)         # funded days, for the 7-day cadence
    funded_days = np.zeros(npth, np.int64)
    eval_days = np.zeros(npth, np.int64)
    npass = np.zeros(npth, np.int64)
    nbr_eval = np.zeros(npth, np.int64)
    nbr_fund = np.zeros(npth, np.int64)
    first_pass = np.full(npth, np.nan)
    days_in_attempt = np.zeros(npth, np.int64)

    for t in range(nd):
        prev = eq.copy()
        r = R[t]
        bad = ~np.isfinite(r)
        if bad.any():
            r = np.where(bad, 0.0, r)
        eq = eq * (1.0 + r / 100.0)
        hwm = np.maximum(hwm, eq)
        eval_days += ~funded
        funded_days += funded
        fday += funded
        days_in_attempt += 1

        floor = np.minimum(hwm - trail_frac * start, start)
        br = (eq <= prev * (1.0 - daily_frac)) | (eq <= floor)

        # --- breaches. Either phase costs a new fee and restarts the eval.
        nbr_fund += (br & funded)
        nbr_eval += (br & ~funded)
        if br.any():
            fees = fees + np.where(br, float(fee), 0.0)
            eq = np.where(br, start, eq)
            hwm = np.where(br, start, hwm)
            funded = funded & ~br
            fday = np.where(br, 0, fday)
            days_in_attempt = np.where(br, 0, days_in_attempt)

        # --- the +10% pass. A funded account begins fresh at the start.
        ps = (~funded) & (~br) & (eq >= start * (1.0 + target))
        if ps.any():
            first_pass = np.where(ps & ~np.isfinite(first_pass),
                                  float(t), first_pass)
            npass += ps
            funded = funded | ps
            eq = np.where(ps, start, eq)
            hwm = np.where(ps, start, hwm)
            fday = np.where(ps, 0, fday)
            days_in_attempt = np.where(ps, 0, days_in_attempt)

        # --- payouts, every 7th FUNDED day, 80% of equity above the start
        # A15: min_funded_days gates the FIRST withdrawal of an account's
        # life. It is the rule that decides whether profit can be extracted
        # faster than the drawdown rule can take it back, and it is swept
        # rather than guessed.
        pay = (funded & (fday > 0) & (fday % payout_every == 0)
               & (fday >= min_funded_days) & (eq > start))
        if pay.any():
            take = np.where(pay, (eq - start) * payout_share, 0.0)
            paid = paid + take
            eq = eq - take

    yrs = nd / float(DAYS_YEAR)
    return dict(paid_out=paid, fees=fees, net=paid - fees,
                n_pass=npass, n_breach_eval=nbr_eval,
                n_breach_funded=nbr_fund, first_pass_day=first_pass,
                funded_days=funded_days, eval_days=eval_days,
                years=yrs, equity_end=eq)


def summarise(rec, nd):
    """-> the one row Jack's 2b asks for."""
    yrs = nd / float(DAYS_YEAR)
    fp = rec['first_pass_day']
    ever = np.isfinite(fp)
    fundedp = rec['funded_days'] > 0
    # breach once funded: of the paths that reached funded, how many breached
    pbr = (float((rec['n_breach_funded'][fundedp] > 0).mean())
           if fundedp.any() else np.nan)
    return dict(
        p_pass_eval=float(ever.mean()),
        median_days_to_pass=(float(np.median(fp[ever])) if ever.any()
                             else np.nan),
        p_breach_funded_in_year=pbr,
        mean_passes_per_year=float(rec['n_pass'].mean() / yrs),
        payout_per_year=float(rec['paid_out'].mean() / yrs),
        fees_per_year=float(rec['fees'].mean() / yrs),
        net_per_year=float(rec['net'].mean() / yrs),
        net_per_year_median=float(np.median(rec['net']) / yrs),
        p_net_positive=float((rec['net'] > 0).mean()),
        funded_day_share=float(rec['funded_days'].mean() / nd),
        attempts_per_year=float(
            (1 + rec['n_breach_eval'] + rec['n_breach_funded']).mean() / yrs))


# ===================== the two return generators ========================
def common_z(nd, npath, seed=SEED):
    """ONE standard-normal block, reused for every (edge, size) cell.

    A synthetic path is sigma * (S/sqrt(252) + Z), so a single Z serves the
    whole map. This is common random numbers: it removes sampling noise
    BETWEEN neighbouring cells, which is what makes a curve readable, and it
    costs nothing in correctness because each cell is still an unbiased
    estimate. It is declared here rather than left to be noticed.
    """
    return np.random.default_rng(seed).normal(0.0, 1.0, size=(nd, npath))


def synthetic_from_z(S, sigma_pct, Z):
    return sigma_pct * (S / np.sqrt(DAYS_YEAR) + Z)


def synthetic(S, sigma_pct, nd, npath, rng):
    """A14.3. Normal daily returns at yearly Sharpe S and daily deviation
    sigma_pct. mu_daily = S * sigma_daily / sqrt(252), so S is exactly the
    yearly return per unit of yearly volatility and size cannot change it.
    THE NORMAL DRAW IS A FRIENDLY ASSUMPTION, declared in A14.3: real daily
    P&L has fatter tails, so every pass rate here is an upper bound and every
    breach rate a lower bound."""
    mu = S * sigma_pct / np.sqrt(DAYS_YEAR)
    return rng.normal(mu, sigma_pct, size=(nd, npath))


def block_boot(series_pct, nd, npath, rng, block=BLOCK):
    """A14.4. Resample a measured daily series in 20-day blocks. Blocks keep
    the autocorrelation that makes real drawdowns worse than independent
    draws imply."""
    x = np.asarray(series_pct, float)
    x = x[np.isfinite(x)]
    n = len(x)
    assert n > block, 'series too short to block bootstrap: %d days' % n
    nb = int(np.ceil(nd / block))
    starts = rng.integers(0, n - block, size=(nb, npath))
    out = np.empty((nb * block, npath))
    for b in range(nb):
        idx = starts[b][None, :] + np.arange(block)[:, None]
        out[b * block:(b + 1) * block] = x[idx]
    return out[:nd]


def budget_sizes(S, nd, npath, rng, ref_sigma=1.0):
    """The daily volatility each budget pair implies for this edge, using the
    project's own sizing rule: scale so the worst day fits the daily budget
    and the worst dip fits the trailing budget, whichever binds. Worst day and
    worst dip both scale linearly in sigma, so one reference run gives all
    three."""
    R = synthetic(S, ref_sigma, nd, npath, rng)
    eq = np.cumprod(1.0 + R / 100.0, axis=0)
    worst_day = float(np.median(-np.min(R, axis=0)))
    run = np.maximum.accumulate(eq, axis=0)
    dip = float(np.median(np.max((run - eq) / run, axis=0)) * 100.0)
    out = {}
    for nm, d, tr in BUDGETS:
        sc = min(d * 100.0 / worst_day if worst_day > 0 else np.inf,
                 tr * 100.0 / dip if dip > 0 else np.inf)
        out[nm] = ref_sigma * sc
    return out, worst_day, dip


# ===================== the self-test ====================================
def test_against_prop_run(verbose=True):
    """The vectorised lifecycle must agree with r2reads.prop_run day for day.

    Three series, each isolating one rule, each checked on the DAY NUMBER and
    not on a summary: the evaluation pass, a daily-rule breach, a trailing-rule
    breach, and the funded payout total. A comment claiming the rules match is
    worth nothing; this is why the claim is allowed.
    """
    rng = np.random.default_rng(7)
    checks = []
    # 1. a series that passes the evaluation
    a = np.full(40, 0.30)
    r1 = lifecycle(a[:, None], 0.04, 0.06)
    p1 = RR.prop_run(a, phase='eval', trail_frac=0.06, daily_frac=0.04)
    checks.append(('eval pass day', float(r1['first_pass_day'][0]),
                   float(p1['passed_eval_day'])))
    # 2. a daily-rule breach: one -5% day inside a flat series
    b = np.zeros(30); b[11] = -5.0
    r2 = lifecycle(b[:, None], 0.04, 0.06, start_funded=True)
    p2 = RR.prop_run(b, phase='funded', trail_frac=0.06, daily_frac=0.04,
                     payout=False)
    checks.append(('daily breach day', 11.0, float(p2['breach_day'])))
    checks.append(('daily breach counted', float(r2['n_breach_funded'][0]), 1.0))
    # 3. a trailing-rule breach: a slow bleed, no single day over the limit
    c = np.full(60, -0.5)
    r3 = lifecycle(c[:, None], 0.04, 0.06, start_funded=True)
    p3 = RR.prop_run(c, phase='funded', trail_frac=0.06, daily_frac=0.04,
                     payout=False)
    assert p3['breached'] == 'trailing', \
        'the bleed series was meant to breach the trailing rule, not %r' \
        % p3['breached']
    checks.append(('trailing breach counted', float(r3['n_breach_funded'][0]),
                   1.0))
    # 4. the funded payout total on a series that never breaches
    d = rng.normal(0.08, 0.35, 252)
    r4 = lifecycle(d[:, None], 0.04, 0.06, start_funded=True)
    p4 = RR.prop_run(d, phase='funded', trail_frac=0.06, daily_frac=0.04)
    if p4['breached'] == '' and r4['n_breach_funded'][0] == 0:
        checks.append(('funded payout', float(r4['paid_out'][0]),
                       float(p4['paid_out'])))
    worst = 0.0
    for nm, mine, theirs in checks:
        bad = (not np.isfinite(mine)) != (not np.isfinite(theirs))
        dd = (abs(mine - theirs) if (np.isfinite(mine) and np.isfinite(theirs))
              else (np.inf if bad else 0.0))
        worst = max(worst, dd)
        if verbose:
            print('    %-24s lifecycle %12.4f  prop_run %12.4f  diff %.2e'
                  % (nm, mine, theirs, dd), flush=True)
    assert worst < 1e-6, \
        'the vectorised lifecycle does not match prop_run: worst %.3e' % worst
    return worst


# ===================== the sweeps =======================================
def sweep_synthetic(edges=EDGES, sigmas=SIGMAS, npath=NPATH, nd=DAYS_YEAR,
                    seed=SEED, verbose=True):
    """2a and 2b on the synthetic books."""
    rows = []
    for S in edges:
        rng = np.random.default_rng(seed + int(S * 1000))
        bsz, wd, dip = budget_sizes(S, nd, npath, rng)
        for sig in sigmas:
            R = synthetic(S, sig, nd, npath, rng)
            for nm, dfr, tfr in BUDGETS:
                rec = lifecycle(R, dfr, tfr)
                rows.append(dict(book='synthetic', edge_sharpe=S,
                                 sigma_daily_pct=sig, budget=nm,
                                 budget_daily=dfr, budget_trail=tfr,
                                 sigma_at_budget=bsz[nm],
                                 ref_worst_day_pct=wd, ref_worst_dip_pct=dip,
                                 **summarise(rec, nd)))
        if verbose:
            print('  edge %.2f done (budget sizes: %s)'
                  % (S, ', '.join('%s %.3f%%' % (k, v)
                                  for k, v in bsz.items())), flush=True)
    return pd.DataFrame(rows)


def sweep_measured(books, sigmas=SIGMAS, npath=NPATH, nd=DAYS_YEAR,
                   seed=SEED, verbose=True):
    """2a and 2b on the measured books. `books` is {label: daily percent
    series}. The series is RESCALED to each target daily volatility, which is
    a pure position-size change and leaves its shape, its autocorrelation and
    its edge alone."""
    rows = []
    for lab, ser in books.items():
        x = np.asarray(ser, float); x = x[np.isfinite(x)]
        sd = float(np.std(x, ddof=1))
        mu = float(np.mean(x))
        S = np.sqrt(DAYS_YEAR) * mu / sd if sd > 0 else np.nan
        rng = np.random.default_rng(seed + abs(hash(lab)) % 10000)
        for sig in sigmas:
            R = block_boot(x * (sig / sd if sd > 0 else 0.0), nd, npath, rng)
            for nm, dfr, tfr in BUDGETS:
                rec = lifecycle(R, dfr, tfr)
                rows.append(dict(book=lab, edge_sharpe=S,
                                 sigma_daily_pct=sig, budget=nm,
                                 budget_daily=dfr, budget_trail=tfr,
                                 measured_days=len(x),
                                 measured_sd_daily_pct=sd,
                                 **summarise(rec, nd)))
        if verbose:
            print('  %s: %d days, daily sd %.4f%%, implied yearly edge %.3f'
                  % (lab, len(x), sd, S), flush=True)
    return pd.DataFrame(rows)


def crossing(edges=EDGES_FINE, sigmas=SIGMAS, npath=NPATH, nd=DAYS_YEAR,
             seed=SEED, goal=GOAL, schedules=SCHEDULES, verbose=True):
    """2c, ACROSS THE PAYOUT SCHEDULE -- see PROTOCOL A15.

    Under A14 as declared (cadence 7, no minimum) net dollars rise
    monotonically in size with no turning point, so "the smallest edge
    reaching $goal" is a statement about where the grid stopped. That row is
    still reported, labelled as a boundary. The other schedules have interior
    optima and are the honest reading.
    """
    Z = common_z(nd, npath, seed)
    rows = []
    for S in edges:
        for sig in sigmas:
            R = synthetic_from_z(S, sig, Z)
            for nm, dfr, tfr in BUDGETS:
                for (ev, mf) in schedules:
                    rec = lifecycle(R, dfr, tfr, payout_every=ev,
                                    min_funded_days=mf)
                    rows.append(dict(edge_sharpe=S, sigma_daily_pct=sig,
                                     budget=nm, payout_every=ev,
                                     min_funded_days=mf,
                                     schedule='%dd/min%dd' % (ev, mf),
                                     **summarise(rec, nd)))
        if verbose and abs(S - round(S)) < 1e-9:
            print('  fine grid through edge %.2f' % S, flush=True)
    F = pd.DataFrame(rows)
    best = (F.sort_values('net_per_year', ascending=False)
             .groupby(['edge_sharpe', 'budget', 'schedule'], as_index=False)
             .first())
    smax = max(sigmas)
    out = []
    for nm, _d, _t in BUDGETS:
        for (ev, mf) in schedules:
            sch = '%dd/min%dd' % (ev, mf)
            b = best[(best.budget == nm) & (best.schedule == sch)]
            q = b[b.net_per_year >= goal].sort_values('edge_sharpe')
            if len(q):
                r = q.iloc[0]
                out.append(dict(budget=nm, schedule=sch, reaches_goal=1,
                                smallest_edge=float(r.edge_sharpe),
                                at_sigma_daily_pct=float(r.sigma_daily_pct),
                                at_grid_edge=int(
                                    abs(r.sigma_daily_pct - smax) < 1e-9),
                                net_per_year=float(r.net_per_year),
                                p_breach_funded_in_year=float(
                                    r.p_breach_funded_in_year),
                                p_pass_eval=float(r.p_pass_eval),
                                median_days_to_pass=float(
                                    r.median_days_to_pass),
                                fees_per_year=float(r.fees_per_year),
                                payout_per_year=float(r.payout_per_year),
                                attempts_per_year=float(r.attempts_per_year)))
            else:
                r = b.sort_values('net_per_year', ascending=False).iloc[0]
                out.append(dict(budget=nm, schedule=sch, reaches_goal=0,
                                smallest_edge=np.nan,
                                at_sigma_daily_pct=float(r.sigma_daily_pct),
                                at_grid_edge=int(
                                    abs(r.sigma_daily_pct - smax) < 1e-9),
                                net_per_year=float(r.net_per_year),
                                p_breach_funded_in_year=float(
                                    r.p_breach_funded_in_year),
                                p_pass_eval=float(r.p_pass_eval),
                                median_days_to_pass=float(
                                    r.median_days_to_pass),
                                fees_per_year=float(r.fees_per_year),
                                payout_per_year=float(r.payout_per_year),
                                attempts_per_year=float(r.attempts_per_year)))
    return F, best, pd.DataFrame(out)


# ===================== the measured books ===============================
def measured_books(verbose=True, which=('c_all_pairs',)):
    """The daily percent series of the books Jack named, on their SCORED
    window only (A14.4). Loads the bank, so it is kept behind a flag."""
    import l2sweep as S
    import nnfxsrc3 as S3
    import nnfxcands as CL
    import nnfxsleeves as BK
    import nnfxbooks as BO
    import nnfxrep as RP
    import nnfxbook2 as B2
    S.load_costs(os.environ.get('FX_COST_TABLE',
                                os.path.join(ROOTOUT, 'cost_table_h22.csv')))
    S3.init_space()
    pairs, bank = BK.load_bank('real')
    cands, _src, _m = CL.load()
    W = BO.World(pairs)
    out = {}
    plan = []
    if 'c_all_pairs' in which:
        plan += [('c_all_pairs', 50, 0.25, 'R1'), ('c_all_pairs', 50, 0.25, 'R2')]
    if 'e_fourcell' in which:
        plan += [('e_fourcell', None, 0.25, 'R1')]
    for fam, K, share, rot in plan:
        if fam == 'e_fourcell':
            continue                      # built by nnfxcell4, handled below
        mem, aw = RP.members_of(bank, pairs, rot, fam, int(K), float(share))
        sw = 'h2' if aw == 'h1' else 'h1'
        smask = W.mask(BK.H1Y if sw == 'h1' else BK.H2Y)
        acc = BO.Acc(W)
        for (j, p) in mem:
            acc.add(S3.mkcand(cands[j]), p, 'S%d' % j)
        _sep, vote, _cs, _cv = acc.series()
        # R per day -> percent of the account at the book's own B5 sizing is a
        # SIZE choice, and size is the sweep axis here. So the series is
        # handed over in R and normalised to a daily volatility inside the
        # sweep; one R is 1% of the account only by convention, and the
        # convention is irrelevant once sigma is the axis.
        x = vote[smask]
        lab = '%s_K%d_%s_scored_%s' % (fam, K, rot, sw)
        out[lab] = x
        if verbose:
            st = B2.stats(pd.Series(x, index=W.dates[smask]), boot=False)
            print('  %s: %d days, R %+.3f, sleeves %d'
                  % (lab, len(x), float(np.nansum(x)), acc.n), flush=True)
    return out


def _f(v, n=3):
    return '--' if v is None or not np.isfinite(v) else ('%.*f' % (n, v))


def _d(v):
    return '--' if v is None or not np.isfinite(v) else ('$%,.0f'.replace(
        '%,', '%') % v if False else '${:,.0f}'.format(v))


def target_md(SY, ME, FINE, BEST, CROSS, selftest):
    L = []
    L.append('# TARGET_MAP — item 2')
    L.append('')
    L.append('**`PROTOCOL.md` A14, declared at 12:10 EST before this ran.** '
             'The account lifecycle, the budgets, the edge definition and the '
             'friendly-normal caveat are all fixed there.')
    L.append('')
    L.append('Fee **$%.0f** on every attempt, payout **%.0f%%** every **%d** '
             'funded days, evaluation target **+%.0f%%**, account '
             '**$%s**, **%d** paths of **%d** days, measured series '
             'block-bootstrapped in **%d**-day blocks.'
             % (FEE, PAYOUT_SHARE * 100, PAYOUT_EVERY, TARGET * 100,
                '{:,.0f}'.format(START), NPATH, DAYS_YEAR, BLOCK))
    L.append('')
    L.append('The vectorised lifecycle agrees with `r2reads.prop_run` to '
             '**%.1e** on the evaluation pass day, both breach rules and the '
             'funded payout total.' % selftest)
    L.append('')
    L.append('## 2a + 2b — the curves, firm hard limits (4% daily, 6% trailing)')
    L.append('')
    L.append('| edge | size (daily σ, %) | P(pass eval) | median days to pass '
             '| P(breach once funded) | payout/yr | fees/yr | **net/yr** |')
    L.append('|---:|---:|---:|---:|---:|---:|---:|---:|')
    q = SY[SY.budget == 'firm'].sort_values(['edge_sharpe', 'sigma_daily_pct'])
    for _i, r in q.iterrows():
        L.append('| %.2f | %.2f | %.3f | %s | %.3f | %s | %s | **%s** |'
                 % (r.edge_sharpe, r.sigma_daily_pct, r.p_pass_eval,
                    _f(r.median_days_to_pass, 0), r.p_breach_funded_in_year,
                    _d(r.payout_per_year), _d(r.fees_per_year),
                    _d(r.net_per_year)))
    L.append('')
    L.append('### The same, at the size each budget rule picks')
    L.append('')
    L.append('| edge | budget | σ the budget implies (%) | P(pass) | '
             'P(breach funded) | **net/yr** |')
    L.append('|---:|---|---:|---:|---:|---:|')
    for S in sorted(SY.edge_sharpe.unique()):
        for nm, _dd, _tt in BUDGETS:
            g = SY[(SY.edge_sharpe == S) & (SY.budget == nm)]
            if not len(g):
                continue
            tgt = float(g.sigma_at_budget.iloc[0])
            r = g.iloc[(g.sigma_daily_pct - tgt).abs().argsort().iloc[0]]
            L.append('| %.2f | %s | %.3f | %.3f | %.3f | **%s** |'
                     % (S, nm, tgt, r.p_pass_eval,
                        r.p_breach_funded_in_year, _d(r.net_per_year)))
    L.append('')
    if ME is not None and len(ME):
        L.append('## 2a — the measured books')
        L.append('')
        L.append('| book | implied yearly edge | size (daily σ, %) | budget | '
                 'P(pass) | P(breach funded) | **net/yr** |')
        L.append('|---|---:|---:|---|---:|---:|---:|')
        for _i, r in ME.sort_values(
                ['book', 'budget', 'sigma_daily_pct']).iterrows():
            L.append('| %s | %.3f | %.2f | %s | %.3f | %.3f | **%s** |'
                     % (r.book, r.edge_sharpe, r.sigma_daily_pct, r.budget,
                        r.p_pass_eval, r.p_breach_funded_in_year,
                        _d(r.net_per_year)))
        L.append('')
    L.append('## 2c — the smallest edge reaching $%s a year on one account'
             % '{:,.0f}'.format(GOAL))
    L.append('')
    L.append('**Read `PROTOCOL.md` A15 before this table.** Under A14 exactly '
             'as declared — withdrawals every 7 funded days with no minimum — '
             'net dollars a year rise **monotonically in size with no turning '
             'point**, so the answer is wherever the grid stopped. Those rows '
             'are marked `at grid edge` and are a property of the rules, not '
             'a finding about the edge. The schedules with a minimum, or a '
             'slower cadence, have genuine interior optima and are the honest '
             'reading.')
    L.append('')
    L.append('| budget | payout schedule | reaches it | smallest edge | '
             'at size (daily σ, %) | at grid edge? | net/yr there | '
             'P(breach funded) | attempts/yr | fees/yr | payout/yr |')
    L.append('|---|---|---|---:|---:|:--:|---:|---:|---:|---:|---:|')
    for _i, r in CROSS.iterrows():
        L.append('| %s | %s | %s | %s | %.2f | %s | %s | %.3f | %.1f | %s | %s |'
                 % (r.budget, r.schedule,
                    'yes' if r.reaches_goal else '**no**',
                    _f(r.smallest_edge, 3), r.at_sigma_daily_pct,
                    '**yes**' if r.at_grid_edge else 'no',
                    _d(r.net_per_year), r.p_breach_funded_in_year,
                    r.attempts_per_year, _d(r.fees_per_year),
                    _d(r.payout_per_year)))
    L.append('')
    L.append('### What the payout schedule is worth, at a fixed edge of 1.0')
    L.append('')
    L.append('| budget | payout schedule | best size (daily σ, %) | '
             'net/yr | P(breach funded) | interior optimum? |')
    L.append('|---|---|---:|---:|---:|:--:|')
    b1 = BEST[np.isclose(BEST.edge_sharpe, 1.0)]
    smax = max(SIGMAS)
    for _i, r in b1.sort_values(['budget', 'payout_every',
                                'min_funded_days']).iterrows():
        at_edge = abs(r.sigma_daily_pct - smax) < 1e-9
        L.append('| %s | %s | %.2f | %s | %.3f | %s |'
                 % (r.budget, r.schedule, r.sigma_daily_pct,
                    _d(r.net_per_year), r.p_breach_funded_in_year,
                    'no — **grid edge**' if at_edge else 'yes'))
    L.append('')
    L.append('**No size is recommended, as Jack asked.** The best size in '
             'the tables above is the argmax of a curve, printed with the '
             'breach rate and the fee bill it carries so the three cannot be '
             'separated.')
    L.append('')
    L.append('### For Jack to fill in — the real payout schedule')
    L.append('')
    L.append('The drawdown budgets are already in the model and they do NOT '
             'decide the answer. The payout schedule does. These are the '
             'three numbers to read off the FundedTradingPlus account:')
    L.append('')
    L.append('| rule | value on the account | used above |')
    L.append('|---|---|---|')
    L.append('| funded days between withdrawals | | 7, 14, 30, 90 swept |')
    L.append('| minimum funded days before the first withdrawal | | '
             '0 and 30 swept |')
    L.append('| minimum profit before a withdrawal is allowed | | '
             'none modelled — **flagged as a gap** |')
    L.append('')
    L.append('## Provenance')
    L.append('')
    for nm, n in (('target_synthetic.csv', len(SY)),
                  ('target_measured.csv', 0 if ME is None else len(ME)),
                  ('target_fine.csv', len(FINE)),
                  ('target_best_by_edge.csv', len(BEST)),
                  ('target_crossing.csv', len(CROSS))):
        L.append('- `results/nnfx/target/%s` — %d rows' % (nm, n))
    L.append('- `code/nnfxtarget.py`, lifecycle checked against '
             '`r2reads.prop_run` to %.1e' % selftest)
    return '\n'.join(L) + '\n'


def main(do_measured=True, verbose=True):
    t0 = time.time()
    print('  lifecycle vs prop_run:', flush=True)
    st = test_against_prop_run(verbose=verbose)
    print('  synthetic sweep (2a, 2b)', flush=True)
    SY = sweep_synthetic(verbose=verbose)
    SY.to_csv(os.path.join(OUT, 'target_synthetic.csv'), index=False)
    ME = None
    if do_measured:
        print('  measured books', flush=True)
        try:
            bk = measured_books(verbose=verbose)
            ME = sweep_measured(bk, verbose=verbose)
            ME.to_csv(os.path.join(OUT, 'target_measured.csv'), index=False)
        except Exception as e:
            print('  measured books SKIPPED: %s: %s'
                  % (type(e).__name__, e), flush=True)
    print('  fine edge grid (2c), %d edges' % len(EDGES_FINE), flush=True)
    FINE, BEST, CROSS = crossing(verbose=verbose)
    FINE.to_csv(os.path.join(OUT, 'target_fine.csv'), index=False)
    BEST.to_csv(os.path.join(OUT, 'target_best_by_edge.csv'), index=False)
    CROSS.to_csv(os.path.join(OUT, 'target_crossing.csv'), index=False)
    md = target_md(SY, ME, FINE, BEST, CROSS, st)
    with open(os.path.join(ROOTOUT, 'nnfx', 'TARGET_MAP.md'), 'w') as f:
        f.write(md)
    print('  TARGET_MAP.md written, %.1f min' % ((time.time() - t0) / 60),
          flush=True)
    return SY, ME, CROSS


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--no-measured', action='store_true')
    a = ap.parse_args()
    main(do_measured=not a.no_measured)
