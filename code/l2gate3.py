import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""GATE 3 — the exam, on crisis-excluded blind results, one strategy at a time.

SPARE CAPACITY ONLY. One core at nice 19. Mode C's pools are never signalled,
never waited on, and gate 3 pauses itself rather than compete with them.

THE SELF-CHECK. C's chunk pace is measured BEFORE gate 3 starts and re-measured
as it runs. If C's cumulative seconds-per-combination rises more than PACE_TOL
above the baseline, gate 3 pauses itself and says so loudly. The tuning queue is
the product; this is a reader of its output.

RESUMABLE. Every strategy's verdict is appended to a per-shard bank the moment
it is computed, so a stop -- pause, kill, power cut -- loses at most one
strategy. Re-running skips anything already banked.

------------------------------------------------------------------------
THE EXAM
------------------------------------------------------------------------
1. HARD BARS, all on the crisis-excluded blind book:
       expectancy >= 0.15R   PF >= 1.5   Sharpe >= 1.1
       Sortino >= 1.3        Calmar >= 1.0   max DD <= 10%
   Max DD is expressed as a FRACTION OF THE STRATEGY'S OWN GROSS PROFIT, not of
   an account: sizing is fixed-R with no compounding, so there is no equity base
   to take a percentage of. 10% means the worst peak-to-trough drawdown costs a
   tenth of everything the strategy made.

2. A FRESH PER-STRATEGY LUCK FLOOR. The null is built from THIS strategy's own
   trade list by sign randomisation: each trade's R keeps its magnitude and gets
   a random sign. That holds the strategy's own trade count, its own R
   distribution and its own fat tails fixed, and asks only whether the DIRECTION
   was informative. A shared floor cannot do this -- it asks whether the
   strategy beat some other population's trades.

   EPISODE-BASED. Signs are flipped per EPISODE, not per trade, where an episode
   is one pair's contiguous run of trades. Flipping per trade would break the
   clustering that makes a run of wins on one pair a single bet, and would set
   the floor too low for exactly the strategies whose edge is concentrated.

3. NET-OF-STRUCTURE, PER STRATEGY, for chop entries: expectancy minus that
   strategy's OWN null mean. Mode-wide null means price the money-management
   tailwind for an average strategy; this prices it for this one.

4. TRADE COUNT IS NOT A KILL CRITERION. A strategy that clears its floor and the
   bars on fewer than MIN_TRADES trades is labelled SELECTIVE, never FAIL.

5. VERDICTS ARE LABELS. Nothing is deleted. Every strategy keeps its row and its
   full numbers whatever the verdict.
"""
import glob, json, time, argparse
import datetime as dt
import numpy as np, pandas as pd

import l2crisis as C
import l2deliver as DL

BARS = dict(expectancy_R=0.15, profit_factor=1.5, sharpe=1.1,
            sortino=1.3, calmar=1.0, max_dd_frac=0.10)
N_SHUF = 5000
MIN_TRADES = 50
SEED = 20260903
PACE_TOL = 0.02          # C may not slow more than 2%
BANK = os.path.join(ROOTOUT, 'gate3_bank')
PAUSE = os.path.join(ROOTOUT, 'GATE3_PAUSED.marker')


def c_pace():
    """C's MEDIAN seconds per combination, for the pace CHECK only.

    The cumulative average is the right estimator for projecting a finish, but
    the wrong one for detecting contention: a chunk in flight while the machine
    slept absorbs the whole sleep window. On 2026-09-03 one chunk recorded
    32,355 s against a 5,901 s median -- a nine-hour laptop sleep, not nine
    hours of work. That single row lifted the cumulative average from 251 to 304
    s/combination and would have made this check compare against a baseline that
    silently includes downtime.

    The median is robust to that and to the ordinary fat right tail of chunk
    cost, so a 2% move in it means real contention rather than one slow chunk.
    """
    f = os.path.join(ROOTOUT, 'gate2_progress_modeC.csv')
    if not os.path.exists(f):
        return None
    d = pd.read_csv(f)
    d = d[d.combos > 0]
    if not len(d):
        return None
    return float((d.seconds / d.combos).median())


WIN = 15         # chunks per comparison window


def c_pace_step():
    """Is C slowing RIGHT NOW relative to its own recent past?

    A fixed baseline cannot answer that, and the first version of this check got
    it wrong. It compared a growing median against a baseline frozen at start
    and paused gate 3 at +2.56%. But C's cost DRIFTS UPWARD on its own: chunks
    are consumed in --sorted order, so later chunks hold different and dearer
    indicators. Measured on the day:

        first 60 chunks (before gate 3)   median 226.6 s/combination
        37 chunks while gate 3 ran        median 258.5
        9 chunks AFTER gate 3 paused      median 301.5

    C was SLOWER with gate 3 stopped than with it running. The trigger was
    intrinsic drift, not contention, and a check that cannot tell the two apart
    will keep pausing gate 3 forever while C gets dearer.

    So compare the newest WIN chunks against the WIN before them -- C against
    its own immediate past. Drift moves both windows together and does not
    trigger; a step change from real contention moves only the newer one.
    """
    f = os.path.join(ROOTOUT, 'gate2_progress_modeC.csv')
    if not os.path.exists(f):
        return None, None
    d = pd.read_csv(f)
    d = d[d.combos > 0]
    if len(d) < 2 * WIN:
        return None, None
    spc = (d.seconds / d.combos).values
    return float(np.median(spc[-WIN:])), float(np.median(spc[-2 * WIN:-WIN]))


def metrics(R):
    """Every figure gate 3 judges, from a bare array of trade R."""
    R = np.asarray(R, float)
    n = len(R)
    if n == 0:
        return None
    tot = float(R.sum())
    eq = R.cumsum()
    dd = float((np.maximum.accumulate(eq) - eq).max()) if n else 0.0
    gp = float(R[R > 0].sum())
    gl = float(-R[R < 0].sum())
    neg = R[R < 0]
    sd = float(R.std(ddof=1)) if n > 1 else 0.0
    dn = float(neg.std(ddof=1)) if len(neg) > 1 else 0.0
    return dict(n=n, total_R=tot, expectancy_R=tot / n,
                win_rate=float((R > 0).mean()),
                profit_factor=(gp / gl) if gl > 0 else np.inf,
                sharpe=(R.mean() / sd * np.sqrt(252 / 20.0)) if sd > 0 else np.nan,
                sortino=(R.mean() / dn * np.sqrt(252 / 20.0)) if dn > 0 else np.nan,
                max_dd_R=dd,
                max_dd_frac=(dd / gp) if gp > 0 else np.inf,
                calmar=(tot / dd) if dd > 0 else np.inf)


def null(R, episodes, rng, n_shuf=N_SHUF):
    """Sign randomisation at EPISODE level. Returns the distribution of
    expectancy under a null where direction carries no information."""
    R = np.asarray(R, float)
    ep = np.asarray(episodes)
    uniq, idx = np.unique(ep, return_inverse=True)
    k = len(uniq)
    out = np.empty(n_shuf)
    for i in range(n_shuf):
        s = rng.choice((-1.0, 1.0), size=k)[idx]
        out[i] = (R * s).mean()
    return out


def episodes_of(T):
    """One pair's CONTIGUOUS run of trades is one episode. A gap of more than
    GAP days on that pair starts a new one -- two trades six months apart are
    not one bet however the same pair is involved."""
    GAP = pd.Timedelta(days=30)
    ep, k = [], 0
    last_pair, last_exit = None, None
    for r in T.sort_values(['pair', 'entry']).itertuples():
        if r.pair != last_pair or (last_exit is not None and r.entry - last_exit > GAP):
            k += 1
        ep.append(k)
        last_pair, last_exit = r.pair, r.exit
    s = pd.Series(ep, index=T.sort_values(['pair', 'entry']).index)
    return s.reindex(T.index).values


def examine(cfg, wins, rng):
    T = DL.blind_trades(cfg, wins)
    if not len(T):
        return None
    X = T[~T.crisis]                       # CRISIS-EXCLUDED, as declared
    if not len(X):
        return None
    m = metrics(X.R.values)
    nd = null(X.R.values, episodes_of(X), rng)
    floor = float(np.percentile(nd, 95))
    nmean = float(nd.mean())
    m.update(luck_floor_p95=floor, null_mean=nmean,
             margin_vs_floor_R=m['expectancy_R'] - floor,
             net_of_structure_R=m['expectancy_R'] - nmean,
             beats_floor=bool(m['expectancy_R'] > floor),
             p_value=float((nd >= m['expectancy_R']).mean()),
             n_crisis_trades=int(T.crisis.sum()))
    bars = {k: (m[k] <= v if k == 'max_dd_frac' else m[k] >= v)
            for k, v in BARS.items()}
    bars = {k: bool(v) and np.isfinite(m[k]) if k != 'profit_factor'
            else bool(v) for k, v in bars.items()}
    m['bars_failed'] = ','.join(sorted(k for k, v in bars.items() if not v))
    m['passes_bars'] = not m['bars_failed']
    if m['passes_bars'] and m['beats_floor']:
        m['verdict'] = 'SELECTIVE' if m['n'] < MIN_TRADES else 'PASS'
    else:
        m['verdict'] = 'FAIL'
    return m


def population():
    fr = []
    for f, sl, mode, lab in (('gate2_modeB_leaderboard.csv', None, 'B', 'B'),
                             ('gate2_modeA_trend_leaderboard.csv', 'trend', 'A', 'A-trend'),
                             ('gate2_modeA_chop_leaderboard.csv', 'chop', 'A', 'A-chop')):
        p = os.path.join(ROOTOUT, f)
        if not os.path.exists(p):
            print('  NOT INCLUDED (missing): %s' % f, flush=True)
            continue
        D = pd.read_csv(p, low_memory=False)
        if sl:
            D = D[D.slice == sl]
        D = D.copy(); D['src_mode'] = mode; D['src_label'] = lab
        D['src_rank'] = D['rank']
        fr.append(D)
    A = pd.concat(fr, ignore_index=True)
    A['sid'] = (A.src_label + '|' + A.slice + '|' + A.c1 + '|' + A.c2 + '|'
                + A.vol + '|' + A.base)
    return A


def banked():
    out = {}
    for f in sorted(glob.glob(os.path.join(BANK, '*.csv'))):
        try:
            d = pd.read_csv(f, low_memory=False)
            for r in d.to_dict('records'):
                out[r['sid']] = r
        except Exception:
            continue
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--shard', type=int, default=0)
    ap.add_argument('--no-pace-check', action='store_true')
    a = ap.parse_args()
    os.makedirs(BANK, exist_ok=True)
    if os.path.exists(PAUSE):
        os.remove(PAUSE)
    base = c_pace()
    print('GATE 3 starting %s' % dt.datetime.now().strftime('%F %T'), flush=True)
    print('  mode C baseline pace: %s s/combination'
          % ('%.1f' % base if base else 'unmeasured'), flush=True)
    P = population()
    done = banked()
    todo = [r for r in P.to_dict('records') if r['sid'] not in done]
    print('  population %d, already banked %d, to examine %d'
          % (len(P), len(done), len(todo)), flush=True)
    if a.limit:
        todo = todo[:a.limit]
    wins = C.windows()
    rng = np.random.default_rng(SEED)
    outf = os.path.join(BANK, 'shard_%02d_%s.csv'
                        % (a.shard, dt.datetime.now().strftime('%m%d_%H%M%S')))
    rows, t0, strikes = [], time.time(), [0]
    for i, cfg in enumerate(todo, 1):
        if not a.no_pace_check and i % 10 == 0:
            now, prev = c_pace_step()
            # TWO CONSECUTIVE breaches before yielding. One window is a single
            # expensive chunk cluster; two in a row is contention.
            if now and prev and now > prev * (1 + PACE_TOL):
                strikes[0] += 1
            else:
                strikes[0] = 0
            if strikes[0] >= 2:
                msg = ('GATE 3 PAUSED at %s: mode C pace stepped %.1f -> %.1f '
                       's/combination (+%.2f%%, tolerance %.0f%%) on two '
                       'consecutive windows. Gate 3 yields.'
                       % (dt.datetime.now().strftime('%F %T'), prev, now,
                          100 * (now / prev - 1), 100 * PACE_TOL))
                print('\n' + '!' * 70 + '\n' + msg + '\n' + '!' * 70, flush=True)
                open(PAUSE, 'w').write(msg + '\n')
                break
        try:
            m = examine(cfg, wins, rng)
        except Exception as e:
            m = dict(verdict='ERROR', bars_failed=str(e)[:120])
        if m is None:
            m = dict(verdict='NO_TRADES', bars_failed='')
        m.update({k: cfg.get(k) for k in
                  ('sid', 'src_label', 'src_mode', 'src_rank', 'slice',
                   'c1', 'c2', 'vol', 'base', 'exit_ind',
                   'risk_atr_len', 'risk_atr_mult', 'risk_tp_mult',
                   'risk_trail_mult', 'risk_trail_arm', 'risk_be_pct')})
        rows.append(m)
        # BANK EVERY ROW AS IT LANDS. A stop must cost one strategy, not a run.
        pd.DataFrame(rows).to_csv(outf, index=False)
        if i % 25 == 0 or i == len(todo):
            el = time.time() - t0
            spc = el / i
            left = (len(P) - len(done) - i) * spc
            print('  %4d/%d examined  %.1f s/strategy  '
                  '| projected remaining %.1f h -> %s'
                  % (i, len(todo), spc, left / 3600,
                     (dt.datetime.now() + dt.timedelta(seconds=left)).strftime('%Y-%m-%d %H:%M')),
                  flush=True)
    print('\nbanked %d rows to %s' % (len(rows), os.path.basename(outf)), flush=True)
    return rows


if __name__ == '__main__':
    main()
