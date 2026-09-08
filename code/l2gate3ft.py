import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""GATE 3, PART ONE: THE FINE-TUNE. Cut comes after (l2gate3.py on this output).

Gate 3 is fine-tune THEN cut. Only the cut ran; this is the missing half. Every
one of the 5,135 gate-2 crossers goes back through the SAME walk-forward machine
-- tune W1, blind W2, re-tune W1+W2, blind W3 -- on WIDENED risk grids.

WHY WIDENED. Gate 2's adopted settings sat on grid edges at a rate that cannot
be coincidence: A-trend's top 10 all chose stop 1.00, the bottom of the stop
grid, and nine of A-chop's top 10 chose trail 1.50 and arm 2.00, both tops. A
parameter pinned to a fence is not an optimum, it is a boundary. The fences move
out and the tuner is asked again.

    stop     1.00..1.50  ->  0.50..1.50     (0.05 below 1.00)
    tp       1.00..3.00  ->  1.00..5.00
    trail    0.50..2.00  ->  0.50..3.00
    arm      1.00..2.00  ->  1.00..3.00
    be       0.01..0.20  ->  0.001..0.20    (0.001 steps)
    atr      unchanged, 2..50
    indicator parameters keep the cap 6

ADOPT ONLY IF BETTER, BY THE CO-EQUAL RULE ON BLIND WINDOWS. A wider grid gives
the tuner more chances to fit, so the acceptance test is the strict one: the new
setting must beat the incumbent on the AVERAGE of its blind-R rank and its blind
Sortino rank, not on either alone. A variant that lifts total R while ruining
Sortino is rejected, which is the whole point of the rule.

EVERY VARIANT COUNTS TOWARD DEFLATION. The fine-tune is a search over a larger
space than gate 2 searched, and the count is banked per strategy so the
deflation total can be assembled exactly rather than estimated.

SPARE CAPACITY ONLY. One core at nice 19, auto-pausing if mode C slows.
Per-strategy banking: a stop costs one strategy.
"""
import glob, json, time, argparse
import datetime as dt
import numpy as np, pandas as pd

import l2sweep as S
import l2tune as T
import l2gate3 as G3

COSTED = os.environ.get('FT_COSTED') == '1'
# OPEN-FLOOR PASS. Re-tunes only the FLOOR_LIMITED strategies from v3 with the
# realism floor REMOVED and the stop grid extended down to 0.02xATR. The labels
# stay -- under-3x-cost and margin-needed are reported per strategy -- but they
# constrain nothing here. The point is to see what those strategies actually
# want when nothing stops them, with costs, gap fills and stop-first all still
# charged, so the answer is honest even where it is unusable.
OPEN = os.environ.get('FT_OPEN') == '1'
if COSTED:
    S.load_costs()
T.ACCT_OBJECTIVE = True     # never compare in raw R -- R shrinks with the stop          # realistic per-pair costs, crisis x2, swap excluded

BANK = os.path.join(ROOTOUT, os.environ.get('FT_BANK', 'gate3ft_bank'))
PAUSE = os.path.join(ROOTOUT, 'GATE3FT_PAUSED.marker')
PACE_TOL = 0.02


def _rng(a, b, s):
    out, x = [], a
    while x <= b + 1e-9:
        out.append(round(x, 4)); x += s
    return out


# STOP OPENS TO 0.10. The 0.50 floor was itself binding: 11 of the first 27
# fine-tuned strategies pinned there, 41%. A fence that still holds four
# strategies in ten is not a boundary the search has explored past.
WIDE_STOP  = _rng(0.05, 1.50, 0.05)
OPEN_STOP  = _rng(0.02, 0.09, 0.01) + _rng(0.10, 1.50, 0.05)
# TP reaches 15.00. At 8.00 the ceiling was the MOST bound fence under costs --
# 14 of the first 65 costed strategies pinned there, 22% -- because a trade has
# to win bigger to clear a real spread. A coarse tail above 8.00 costs 29 points
# rather than 141 and lets the tuner say how far it actually wants to go.
# TP_NONE = 999.0, the engine's no-target sentinel. tp_mult is an ATR MULTIPLE
# (l1_tp = entry + tp_mult x ATR), not a risk-reward ratio -- RR is
# tp_mult/atr_mult. At v2's median stop 0.25 and median TP 10.50 the implied RR
# was 42:1, so the targets genuinely moved out in ATR terms; the yardstick did
# not change.
TP_NONE    = 999.0
WIDE_TP    = (_rng(1.00, 8.00, 0.05) + _rng(8.25, 15.00, 0.25)
              + _rng(16.0, 30.0, 1.0) + [TP_NONE])
# BE REACHES 0.001 BY FLOOR POINTS, NOT BY 0.001 STEPS THROUGHOUT. Uniform
# 0.001 steps from 0.001 to 0.20 is 200 points -- 43% of the entire widened
# budget, more than stop, arm and trail combined -- to resolve a parameter that
# has adopted 0.05 or 0.01 every time it has been tuned. Coordinate-descent cost
# is LINEAR in grid size, so those 200 points were a third of the whole run.
# The declared floor of 0.001 is reached exactly; the coarse decade above 0.01
# keeps its old spacing. Three floor points, per Jack's specification. If BE
# adopts one of them, that is the signal to resolve the floor further.
WIDE_BE    = [0.001, 0.002, 0.005] + _rng(0.01, 0.20, 0.01)   # 23 points, as specified
WIDE_ARM   = _rng(1.00, 3.00, 0.05)
WIDE_TRAIL = _rng(0.50, 3.00, 0.05)
# all four fences, reported at the end: if a setting still pins here, the fence
# is still binding and moving it out again is the honest next step
EDGES = {'risk_tp_mult': 30.00, 'risk_atr_mult': 0.10,
         'risk_trail_mult': 3.00, 'risk_trail_arm': 3.00}


FLOOR = None
MED_ATR_REL = 0.00841        # median pair ATR/price, measured across the 28


def stop_floor(atr_len):
    """REALISM FLOOR: min stop = max(0.10 x ATR, 3 x the worst pair's round-trip
    cost). A stop inside three spreads is not a stop, it is noise, and at v2's
    0.05 floor 21% of adopted stops fell under 3x cost. The binding pair is the
    WORST of the 28 because one atr_mult is applied to all of them."""
    global FLOOR
    if FLOOR is None:
        f = os.path.join(ROOTOUT, 'stop_floor_by_atrlen.csv')
        FLOOR = pd.read_csv(f, index_col=0)['min_atr_mult'].to_dict()
    return FLOOR.get(int(atr_len), 0.10)


def widen():
    """Swap the module-level grids the tuner reads. Done once, in-process."""
    T.GRID_STOP, T.GRID_TP, T.GRID_BE = WIDE_STOP, WIDE_TP, WIDE_BE
    if OPEN:
        T.GRID_STOP = OPEN_STOP
    T.GRID_ARM, T.GRID_TRAIL = WIDE_ARM, WIDE_TRAIL
    if OPEN:
        T.GRID_STOP = OPEN_STOP
        T.STOP_FLOOR_FN = None          # floor removed for this pass
    else:
        T.STOP_FLOOR_FN = stop_floor    # tuner filters atr_mult by this
    T.RISK_KNOBS_TREND = (('atr_len', T.GRID_ATR), ('atr_mult', T.GRID_STOP),
                          ('tp_mult', T.GRID_TP), ('be_pct', T.GRID_BE),
                          ('trail_arm', T.GRID_ARM), ('trail_mult', T.GRID_TRAIL))
    T.RISK_KNOBS_CHOP = (('atr_len', T.GRID_ATR), ('atr_mult', T.GRID_STOP),
                         ('tp_mult', T.GRID_TP))
    return sum(len(g) for _, g in T.RISK_KNOBS_TREND)


def banked():
    out = {}
    for f in sorted(glob.glob(os.path.join(BANK, '*.csv'))):
        try:
            for r in pd.read_csv(f, low_memory=False).to_dict('records'):
                out[r['sid']] = r
        except Exception:
            continue
    return out


def rescore_incumbent(sc, cfg, combo, mode, sname, code, plan):
    """The incumbent's GATE 2 SETTINGS, re-scored under TODAY's engine.

    v3 compared a costed, gap-filled candidate against gate 2's STORED numbers,
    which were gross -- no costs, no gap fills, because layer 2 charged nothing
    until this pass. That is apples to oranges and it biased every comparison.
    The baseline must be measured under the same rules as the candidate.
    """
    try:
        ip = json.loads(cfg['ip2'])
        rk = {k: cfg['risk_' + k] for k in ('atr_len', 'atr_mult', 'tp_mult',
                                            'trail_mult', 'trail_arm', 'be_pct')}
    except Exception:
        return None
    # W3 ONLY. Scoring the incumbent's W2 with its ip2 inflates it -- ip2 was
    # tuned on W1+W2 -- so the candidate, whose W2 is honestly scored under ip1,
    # was being rejected against a flattered baseline. W3 is clean for both
    # sides: no tune has seen it. Like-for-like, and honest.
    a = sc.score(combo, ip, rk, mode, sname, code, plan, ('W3',))
    g = a.get('W3')
    if not g:
        return None
    return {k: v for k, v in g.items() if k != '_r'}


def adopt(new, old):
    """THE STANDING RULE. New settings are adopted only if, on the blind windows
    under full costs, they beat the previous settings on ACCOUNT-LEVEL RETURN
    and are no worse on max drawdown, Sortino and Sharpe. Otherwise the previous
    settings stand.

    Account-level return is total_R with the objective already normalised to a
    fixed 1.0xATR risk unit, so it cannot be inflated by shrinking the stop.
    Never compared in raw R.
    """
    if new is None:
        return False
    if old is None:
        return True
    def g(d, k, dflt):
        v = d.get(k)
        return dflt if v is None or not np.isfinite(v) else float(v)
    if g(new, 'total_R', -np.inf) <= g(old, 'total_R', -np.inf):
        return False
    if g(new, 'max_dd_R', np.inf) > g(old, 'max_dd_R', np.inf) + 1e-12:
        return False
    if g(new, 'sortino', -np.inf) < g(old, 'sortino', -np.inf) - 1e-12:
        return False
    if g(new, 'sharpe', -np.inf) < g(old, 'sharpe', -np.inf) - 1e-12:
        return False
    return True


def coequal_better(new, old):
    """The declared rule: rank on blind R, rank on Sortino, average the ranks.
    With two candidates a rank is just a comparison, so this is 'wins on both,
    or wins on one and ties the other'. Ties go to the INCUMBENT -- a wider grid
    must earn the change, not merely match it."""
    if new is None:
        return False
    if old is None:
        return True
    nr, ns = new.get('total_R'), new.get('sortino')
    orr, os_ = old.get('total_R'), old.get('sortino')
    if nr is None or orr is None:
        return False
    ns = -np.inf if (ns is None or not np.isfinite(ns)) else ns
    os_ = -np.inf if (os_ is None or not np.isfinite(os_)) else os_
    score_new = (1 if nr > orr else 0) + (1 if ns > os_ else 0)
    score_old = (1 if orr > nr else 0) + (1 if os_ > ns else 0)
    return score_new > score_old


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--shard', type=int, default=0)
    ap.add_argument('--shards', type=int, default=1)
    ap.add_argument('--no-pace-check', action='store_true')
    a = ap.parse_args()
    os.makedirs(BANK, exist_ok=True)
    npts = widen()
    print('GATE 3 FINE-TUNE starting %s' % dt.datetime.now().strftime('%F %T'), flush=True)
    print('  widened risk grid: %d points per coordinate-descent sweep '
          '(was 193, %.2fx)' % (npts, npts / 193.0), flush=True)
    P = G3.population()
    if OPEN:
        v3 = pd.concat([pd.read_csv(f, low_memory=False)
                        for f in glob.glob(os.path.join(ROOTOUT, 'gate3ft_costed_v3', '*.csv'))],
                       ignore_index=True)
        keep = set(v3[v3.get('floor_limited') == True].sid)
        P = P[P.sid.isin(keep)].reset_index(drop=True)
        print('  OPEN-FLOOR pass: %d FLOOR_LIMITED strategies from v3' % len(P), flush=True)
    done = banked()
    todo = [r for r in P.to_dict('records') if r['sid'] not in done]
    if a.shards > 1:
        todo = [r for i, r in enumerate(todo) if i % a.shards == a.shard]
    print('  population %d, banked %d, to fine-tune %d (shard %d/%d)'
          % (len(P), len(done), len(todo), a.shard, a.shards), flush=True)
    if a.limit:
        todo = todo[:a.limit]
    base_now, base_prev = G3.c_pace_step()
    sc = T.Scorer()
    outf = os.path.join(BANK, 'ft_%02d_%s.csv'
                        % (a.shard, dt.datetime.now().strftime('%m%d_%H%M%S')))
    rows, t0, strikes = [], time.time(), [0]
    for i, cfg in enumerate(todo, 1):
        if not a.no_pace_check and i % 5 == 0:
            now, prev = G3.c_pace_step()
            strikes[0] = strikes[0] + 1 if (now and prev and now > prev * (1 + PACE_TOL)) else 0
            if strikes[0] >= 2:
                msg = ('GATE 3 FINE-TUNE PAUSED at %s: mode C stepped %.1f -> %.1f '
                       's/combination on two consecutive windows. Yielding.'
                       % (dt.datetime.now().strftime('%F %T'), prev, now))
                print('\n' + '!' * 70 + '\n' + msg + '\n' + '!' * 70, flush=True)
                open(PAUSE, 'w').write(msg + '\n')
                break
        combo = (cfg['c1'], cfg['c2'], cfg['vol'], cfg['base'],
                 cfg.get('exit_ind') or S.slot_options()['exit_ind'][0])
        sname = cfg['slice']
        code = dict((s, c) for s, _, c in S.SLICES)[sname]
        plan = dict((s, p) for s, p, _ in S.SLICES)[sname]
        mode = cfg['src_mode']
        rec = dict(sid=cfg['sid'], src_label=cfg['src_label'], src_mode=mode,
                   slice=sname, c1=cfg['c1'], c2=cfg['c2'], vol=cfg['vol'],
                   base=cfg['base'], exit_ind=cfg.get('exit_ind'))
        try:
            t1 = time.time()
            base = rescore_incumbent(sc, cfg, combo, mode, sname, code, plan)
            res = T.full_walk(sc, combo, mode, sname, code, plan, cap=6)
            b = res['blind']
            rec['ft_seconds'] = round(time.time() - t1, 1)
            # compare the CANDIDATE'S W3 against the incumbent's W3 -- both
            # clean, both the same window. Comparing a two-window candidate
            # against a one-window incumbent would be wrong the other way.
            cw3 = res.get('w3')
            cw3 = ({k: v for k, v in cw3.items() if k != '_r'} if cw3 else None)
            rec['adopted'] = bool(adopt(cw3, base))
            rec['compare_basis'] = 'W3ONLY'
            for k in ('total_R', 'max_dd_R', 'sortino', 'sharpe', 'n'):
                rec['cw3_' + k] = (cw3 or {}).get(k)
            for k in ('total_R', 'expectancy_R', 'sortino', 'sharpe', 'calmar',
                      'profit_factor', 'ulcer_R', 'max_dd_R', 'win_rate',
                      'avg_win_R', 'avg_loss_R', 'win_loss_ratio',
                      'profit_concentration', 'avg_hold_bars', 'n'):
                rec['base_' + k] = (base or {}).get(k)
            rec['base_stop'] = cfg.get('risk_atr_mult')
            rec['base_tp'] = cfg.get('risk_tp_mult')
            for k in ('total_R', 'expectancy_R', 'profit_factor', 'sharpe',
                      'sortino', 'calmar', 'max_dd_R', 'ulcer_R', 'win_rate',
                      'avg_win_R', 'avg_loss_R', 'win_loss_ratio',
                      'profit_concentration', 'avg_hold_bars', 'n_blind', 'n_w2', 'n_w3'):
                rec['ft_' + k] = (b or {}).get(k)
            for k, v in (res['rk2'] or {}).items():
                rec['ft_risk_' + k] = v
            rec['ft_ip2'] = json.dumps(res['ip2'], sort_keys=True)
            # BANK THE FIRST TUNE TOO. The stitched blind is W2 under ip1/rk1
            # plus W3 under ip2/rk2, so without ip1/rk1 the candidate's score
            # cannot be reconstructed later -- re-scoring both windows with ip2
            # is contaminated on W2, which is exactly the mistake the first
            # back-fill made.
            rec['ft_ip1'] = json.dumps(res.get('ip1'), sort_keys=True)
            rec['ft_rk1'] = json.dumps(res.get('rk1'), sort_keys=True)
            rec['variants'] = int((res.get('stage1') or {}).get('evals', 0)
                                  + (res.get('stage2') or {}).get('evals', 0))
            rec['prev_total_R'] = old['total_R']
            rec['prev_sortino'] = old['sortino']
            rec['at_edge'] = ','.join(k.replace('risk_', '') for k, v in EDGES.items()
                                      if rec.get('ft_' + k) is not None
                                      and abs(float(rec['ft_' + k]) - v) < 1e-9)
            rec['costed'] = COSTED
            # PRICE-TERMS reporting: tp_mult and atr_mult are both ATR
            # multiples, so RR is their ratio, not tp_mult itself.
            am, tp = rec.get('ft_risk_atr_mult'), rec.get('ft_risk_tp_mult')
            rec['tp_none'] = bool(tp is not None and float(tp) >= 900.0)
            rec['stop_atr'] = am
            rec['target_atr'] = None if rec['tp_none'] else tp
            rec['rr'] = (None if (rec['tp_none'] or not am or not tp)
                         else round(float(tp) / float(am), 3))
            fl = stop_floor(rec.get('ft_risk_atr_len') or 14)
            rec['floor_limited'] = bool(am is not None and float(am) <= fl + 1e-9)
            rec['stop_floor_used'] = round(fl, 4)
            # MARGIN NEEDED, reported not limited: position as a multiple of
            # equity at 1% risk is 0.01 / (atr_mult x ATR/price).
            rec['margin_mult_equity'] = (None if not am else
                                         round(0.01 / (float(am) * MED_ATR_REL), 2))
            rec['margin_pct_at_1_30'] = (None if not am else
                                         round(100 * (0.01 / (float(am) * MED_ATR_REL)) / 30.0, 1))
            rec['open_floor_pass'] = OPEN
        except Exception as e:
            rec['error'] = str(e)[:200]
        rows.append(rec)
        pd.DataFrame(rows).to_csv(outf, index=False)
        if i % 25 == 0 or i == len(todo):
            # keep the alternates file current as the run proceeds, so a
            # rejected-but-better candidate is never lost to an interruption
            try:
                import l2alternates as ALT
                ALT.build()
            except Exception:
                pass
            el = time.time() - t0
            spc = el / i
            remaining = (len(P) - len(done) - i)
            left = remaining * spc
            print('  %4d/%d  %.1f s/strategy  | %d left -> %.0f h -> %s'
                  % (i, len(todo), spc, remaining, left / 3600,
                     (dt.datetime.now() + dt.timedelta(seconds=left)).strftime('%Y-%m-%d')),
                  flush=True)
    print('\nbanked %d rows to %s' % (len(rows), os.path.basename(outf)), flush=True)


if __name__ == '__main__':
    main()
