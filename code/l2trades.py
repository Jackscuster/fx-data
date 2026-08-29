import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""TRADE-LEVEL EXPORT for the app's chart tab.

Re-runs a banked gate 2 configuration on ONE pair and emits every trade with the
levels that governed it: entry, initial stop, TP1, the breakeven point, the trail
path bar by bar, and the exit with its reason and R.

WHY THE TRAIL PATH IS RECONSTRUCTED RATHER THAN READ. The engine records what a
trade DID -- entry, exit, reason, R -- not the stop level it carried on every
bar in between. Adding that to run_bars would mean editing the engine while mode
A is tuning against it, which is not a trade worth making for a chart. So the
path is rebuilt here from the same rules, and then CHECKED: the reconstruction
must land on the engine's own exit bar, exit price and reason for every trade,
or the trade is emitted with reconstruction_ok=False and the chart says so.
A picture drawn from a reconstruction nobody verified is worse than no picture.

The rules mirror l2engine's leg-2 block exactly (GAUNTLET.md gate 2):
  phase 0  initial stop, TP1 not yet hit
  phase 1  TP1 hit -> freeze the PREVIOUS bar's close and ATR, forever
  phase 2  price X% of price beyond TP1 -> stop to breakeven
  phase 3  price reaches M x frozen ATR beyond the frozen close -> trail arms,
           thereafter D x frozen ATR behind the highest close SINCE ARMING,
           floored at breakeven, and never moving against the trade

Writes results/trades_<slug>.json -- one bundle per strategy, carrying the OHLC
span the chart needs so the tab reads a single file.
"""
import json
import numpy as np, pandas as pd
import l2lib as L, l2engine as E, l2sweep as S, l2tune as T

SLOTS = ('c1', 'c2', 'vol', 'base', 'exit_ind')


def _series(name, params, o, h, l, c):
    return L.compute(name, o, h, l, c, **params)


def run_pair(cfg, pair, sc=None):
    """Engine run for one configuration on one pair. Returns bars + trades."""
    d = S.load_pair(pair)
    o, h, l, c = (d[k].values.astype(float) for k in ('open', 'high', 'low', 'close'))
    ip = json.loads(cfg['ip2'])
    risk = {k: cfg['risk_' + k] for k in
            ('atr_len', 'atr_mult', 'tp_mult', 'trail_mult', 'trail_arm', 'be_pct')}
    atr = L.P.atr(h, l, c, int(risk['atr_len']))
    lt, st, lc, sc_ = _series(cfg['c1'], ip['c1'], o, h, l, c)[:4]
    _, _, c2lc, c2sc = _series(cfg['c2'], ip['c2'], o, h, l, c)[:4]
    vl, vs = _series(cfg['vol'], ip['vol'], o, h, l, c)[:2]
    bl = _series(cfg['base'], ip['base'], o, h, l, c)
    bl = bl[0] if isinstance(bl, tuple) else bl
    el, es = _series(cfg['exit_ind'], ip['exit_ind'], o, h, l, c)[:2]
    plan = 2 if cfg['slice'] == 'trend' else 1
    kwm = S.mode_kw('B')
    n = len(c); cap = 4 * n + 8
    t = {k: np.zeros(cap, np.int64) for k in
         ('entry_bar', 'exit_bar', 'dir', 'leg', 'reason', 'route')}
    for k in ('entry_px', 'exit_px', 'units', 'r'):
        t[k] = np.zeros(cap, np.float64)
    nt, _, _, _ = E.run_bars(
        o, h, l, c, atr, bl, lt, st, lc, sc_, c2lc, c2sc, vl, vs, el, es,
        np.zeros(n, bool), L.KIND[cfg['c1']] == 'TERNARY', L.KIND[cfg['c2']] == 'TERNARY',
        True, True, True,
        kwm['exit_on_c1_flip'], kwm['exit_on_base_cross'], kwm['exit_on_exit_ind'],
        False, int(plan), S.RISK,
        float(risk['atr_mult']), float(risk['tp_mult']), float(risk['trail_mult']),
        float(risk['trail_arm']), float(risk['be_pct']), 1.5, 7, True, True,
        t['entry_bar'], t['exit_bar'], t['dir'], t['leg'], t['entry_px'],
        t['exit_px'], t['units'], t['r'], t['reason'], t['route'])
    tr = {k: v[:nt] for k, v in t.items()}
    return dict(dates=d.index, o=o, h=h, l=l, c=c, atr=atr, trades=tr,
                risk=risk, plan=plan)


def stop_path(R, i_entry, i_exit, direction, entry_px, risk, atr, c, hi, lo):
    """Rebuild the leg-2 stop level bar by bar. Mirrors l2engine's phase block."""
    am, tp = risk['atr_mult'], risk['tp_mult']
    D, M, X = risk['trail_mult'], risk['trail_arm'], risk['be_pct']
    entry_atr = atr[i_entry]
    stop_dist = am * entry_atr
    l1_stop = entry_px - direction * stop_dist
    l1_tp = entry_px + direction * tp * entry_atr
    phase, frozen_close, frozen_atr, best = 0, 0.0, 0.0, 0.0
    stop = l1_stop
    path, events = [], []
    for i in range(i_entry, i_exit + 1):
        if phase == 0 and ((direction == 1 and hi[i] >= l1_tp) or
                           (direction == -1 and lo[i] <= l1_tp)):
            phase = 1
            frozen_close = c[i - 1] if i > 0 else c[i]
            frozen_atr = atr[i - 1] if i > 0 else atr[i]
            events.append(dict(bar=i, kind='tp1', level=float(l1_tp)))
        if phase == 1:
            trig = l1_tp * (1.0 + direction * X / 100.0)
            if (direction == 1 and hi[i] >= trig) or (direction == -1 and lo[i] <= trig):
                phase = 2
                if (direction == 1 and entry_px > stop) or (direction == -1 and entry_px < stop):
                    stop = entry_px
                events.append(dict(bar=i, kind='breakeven', level=float(entry_px)))
        if phase == 2:
            arm = frozen_close + direction * M * frozen_atr
            if (direction == 1 and hi[i] >= arm) or (direction == -1 and lo[i] <= arm):
                phase = 3; best = c[i]
                events.append(dict(bar=i, kind='trail_armed', level=float(arm)))
        if phase == 3:
            if (direction == 1 and c[i] > best) or (direction == -1 and c[i] < best):
                best = c[i]
            trail = best - direction * D * frozen_atr
            if (direction == 1 and entry_px > trail) or (direction == -1 and entry_px < trail):
                trail = entry_px
            if (direction == 1 and trail > stop) or (direction == -1 and trail < stop):
                stop = trail
        path.append(float(stop))
    return dict(path=path, events=events, l1_stop=float(l1_stop), l1_tp=float(l1_tp))


def best_pair(cfg, pairs=None):
    """The pair this configuration made the most blind R on."""
    code = dict((s, c) for s, _, c in S.SLICES)[cfg['slice']]
    best, bestR = None, -1e18
    scores = {}
    for p in (pairs or S.all_pairs()):
        try:
            r = run_pair(cfg, p)
        except Exception:
            continue
        d = r['dates']; tr = r['trades']
        if len(tr['r']) == 0:
            continue
        reg = S.regime_codes(p, d)
        eb = tr['entry_bar']
        wb = {k: (int(np.flatnonzero((d >= a) & (d <= z))[0]),
                  int(np.flatnonzero((d >= a) & (d <= z))[-1]) + 1)
              for k, (a, z) in S.WINDOWS.items()
              if ((d >= a) & (d <= z)).any()}
        m = (reg[eb] == code)
        blind = np.zeros(len(eb), bool)
        for k in ('W2', 'W3'):
            if k in wb:
                a, z = wb[k]; blind |= (eb >= a) & (eb < z)
        sel = m & blind
        tot = float(tr['r'][sel].sum()) if sel.any() else 0.0
        scores[p] = tot
        if tot > bestR:
            best, bestR = p, tot
    return best, bestR, scores


def bundle(cfg, rank, outdir=ROOTOUT):
    pair, totR, scores = best_pair(cfg)
    r = run_pair(cfg, pair)
    d, o, h, l, c, atr = r['dates'], r['o'], r['h'], r['l'], r['c'], r['atr']
    tr = r['trades']; risk = r['risk']
    code = dict((s, cc) for s, _, cc in S.SLICES)[cfg['slice']]
    reg = S.regime_codes(pair, d)
    wb = {}
    for k, (a, z) in S.WINDOWS.items():
        w = np.flatnonzero((d >= a) & (d <= z))
        if len(w):
            wb[k] = (int(w[0]), int(w[-1]) + 1)
    trades, okall = [], True
    for j in range(len(tr['r'])):
        eb, xb = int(tr['entry_bar'][j]), int(tr['exit_bar'][j])
        if xb < 0:
            continue
        if reg[eb] != code:
            continue
        inblind = any(wb.get(k) and wb[k][0] <= eb < wb[k][1] for k in ('W2', 'W3'))
        if not inblind:
            continue
        dirn = int(tr['dir'][j])
        sp = stop_path(r, eb, xb, dirn, float(tr['entry_px'][j]), risk, atr, c, h, l)
        # VERIFY the reconstruction against the engine's own outcome
        reason = int(tr['reason'][j])
        ok = True
        if int(tr['leg'][j]) == 2 and reason in (E.STOP, E.STOP_BE, E.STOP_TRAIL):
            ok = abs(sp['path'][-1] - float(tr['exit_px'][j])) < 1e-9
        okall &= ok
        trades.append(dict(
            leg=int(tr['leg'][j]), dir=dirn,
            entry_bar=eb, exit_bar=xb,
            entry_date=str(d[eb].date()), exit_date=str(d[xb].date()),
            entry_px=float(tr['entry_px'][j]), exit_px=float(tr['exit_px'][j]),
            initial_stop=sp['l1_stop'], tp1=sp['l1_tp'],
            stop_path=sp['path'], events=sp['events'],
            reason=E.REASON.get(reason, str(reason)),
            R=float(tr['r'][j]), reconstruction_ok=bool(ok)))
    lo_b = min([t['entry_bar'] for t in trades], default=0)
    hi_b = max([t['exit_bar'] for t in trades], default=len(c) - 1)
    lo_b = max(0, lo_b - 20); hi_b = min(len(c) - 1, hi_b + 20)
    out = dict(
        rank=rank, pair=pair, slice=cfg['slice'],
        slots={k: cfg[k] for k in SLOTS},
        risk={k: float(v) for k, v in risk.items()},
        indicator_params=json.loads(cfg['ip2']),
        total_R_on_pair=round(totR, 3),
        n_trades=len(trades),
        reconstruction_ok=bool(okall),
        provisional='W3-diagnostic ranking; stitched score pending round 2',
        bar0=int(lo_b),
        bars=[dict(d=str(d[i].date()), o=float(o[i]), h=float(h[i]),
                   l=float(l[i]), c=float(c[i])) for i in range(lo_b, hi_b + 1)],
        trades=trades,
        pair_totals={k: round(v, 2) for k, v in sorted(
            scores.items(), key=lambda kv: -kv[1])[:6]})
    slug = 'rank%d_%s' % (rank, pair)
    f = os.path.join(outdir, 'trades_%s.json' % slug)
    json.dump(out, open(f, 'w'))
    return f, out


def main():
    cfgs = pd.read_json('/tmp/top5.json').to_dict('records')
    idx = []
    for i, cfg in enumerate(cfgs, 1):
        f, out = bundle(cfg, i)
        print('  rank %d  %-8s %-6s  %3d trades  totalR %7.2f  recon_ok %s  -> %s'
              % (i, out['pair'], out['slice'], out['n_trades'],
                 out['total_R_on_pair'], out['reconstruction_ok'],
                 os.path.basename(f)), flush=True)
        idx.append(dict(rank=i, pair=out['pair'], slice=out['slice'],
                        file=os.path.basename(f), n_trades=out['n_trades'],
                        total_R=out['total_R_on_pair'],
                        label='#%d %s %s' % (i, out['pair'], out['slice'])))
    json.dump(idx, open(os.path.join(ROOTOUT, 'trades_index.json'), 'w'))
    print('wrote results/trades_index.json')


if __name__ == '__main__':
    main()
