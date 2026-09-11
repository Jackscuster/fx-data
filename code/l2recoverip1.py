import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""RECOVER ip1/rk1 for mode B's TREND slice, which never banked them.

WHY IT MATTERS. The walk-forward stitch is W2 scored with the FIRST tune and W3
with the second. Mode B trend banked only ip2, so every downstream number scored
W2 with parameters that had been tuned on W1+W2. Measured on the eight graft
members that DO have ip1, that inflates W2 total R from 92.4 to 452.0 -- +389%.

WHAT THIS DOES. Re-runs gate 2 stage 1 only -- the W1 tune -- for each named
strategy and banks ip1/rk1. It does NOT re-tune stage 2: ip2 is already correct
and re-deriving it would change the strategy rather than recover its history.

MODE B RAN UNCAPPED. GAUNTLET records that A and C are capped at each
indicator's six highest-impact parameters and B is not, so cap=None here. Using
cap=6 would produce a DIFFERENT ip1 from the one B actually used and would look
like a recovery while being a silent re-tune.

Resumable: one row per strategy appended as it completes.
"""
import glob, json, time, argparse
import numpy as np, pandas as pd
import l2sweep as S
import l2tune as T

OUT = os.path.join(ROOTOUT, 'gate2_ip1_recovered.csv')


def out_path(shard, shards):
    """One bank per shard. Parallel appends to a single CSV interleave rows and
    corrupt it, so each worker owns a file and they are merged afterwards."""
    if os.environ.get('IP1_BOX'):
        return os.path.join(ROOTOUT, 'gate2_ip1_recovered_box%s_s%02d.csv'
                            % (os.environ['IP1_BOX'], shard))
    return (OUT if shards <= 1 else
            os.path.join(ROOTOUT, 'gate2_ip1_recovered_s%02d.csv' % shard))


def banked():
    """Everything recovered so far, across every shard file, so a resumed or
    re-sharded run never redoes work."""
    out = set()
    for f in [OUT] + sorted(glob.glob(os.path.join(ROOTOUT,
                                                   'gate2_ip1_recovered_s*.csv'))):
        if os.path.exists(f):
            try:
                d = pd.read_csv(f)
                out |= set(d[d.sid != 'sid'].sid)
            except Exception:
                continue
    return out


def box_of(sid, of):
    """md5(sid) %% N, fixed for all time. Position-based sharding let restarted
    shards claim overlapping work on 2026-09-10: 228 duplicate runs, 18.7 wasted
    core-hours."""
    import hashlib
    return int(hashlib.md5(sid.encode()).hexdigest(), 16) % of


def targets(which, all_candidates=False):
    """Strategies missing ip1. Only mode B trend can be missing it.

    all_candidates drops the crosses_label filter. THE CLEAN FIELD NEEDS THIS.
    crosses_label was decided on the stitched W2+W3 book, so re-labelling only
    the crossers preserves exactly the contamination the rebuild removes -- the
    crosser list IS the thing being rebuilt. ip2 is not required either: the
    clean field scores W2 under ip1 and never touches ip2."""
    d = pd.read_csv(os.path.join(ROOTOUT, 'gate2_tuned_modeB.csv'), low_memory=False)
    d['sid'] = 'B|' + d.slice + '|' + d.c1 + '|' + d.c2 + '|' + d.vol + '|' + d.base
    if all_candidates:
        d = d[d.slice == 'trend']
    else:
        d = d[(d.slice == 'trend') & (d.crosses_label == True) & d.ip2.notna()]
    if 'ip1' in d.columns:
        d = d[d.ip1.isna()]
    if which == 'graft':
        G = pd.read_csv(os.path.join(ROOTOUT, 'gate2_combined_AB_leaderboard.csv'),
                        low_memory=False).sort_values('rank').head(15)
        G['sid'] = G.src_label + '|' + G.slice + '|' + G.c1 + '|' + G.c2 + '|' + G.vol + '|' + G.base
        d = d[d.sid.isin(set(G.sid))]
    return d.reset_index(drop=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--which', default='graft', choices=['graft', 'all'])
    ap.add_argument('--shard', type=int, default=0)
    ap.add_argument('--shards', type=int, default=1)
    ap.add_argument('--all-candidates', action='store_true')
    ap.add_argument('--box', type=int, default=0)
    ap.add_argument('--of', type=int, default=1)
    a = ap.parse_args()
    S.load_costs(); T.ACCT_OBJECTIVE = True
    D = targets(a.which, a.all_candidates)
    done = banked()
    D = D[~D.sid.isin(done)].reset_index(drop=True)
    if a.of > 1:
        D = D[[box_of(s_, a.of) == a.box for s_ in D.sid]].reset_index(drop=True)
    if a.shards > 1:
        D = D.iloc[a.shard::a.shards].reset_index(drop=True)
    if a.of > 1:
        os.environ['IP1_BOX'] = str(a.box)
    OUTF = out_path(a.shard, a.shards)
    print('ip1 recovery (%s%s): %d strategies this shard (box %d/%d, shard %d/%d), '
          '%d already banked' % (a.which, ', ALL CANDIDATES' if a.all_candidates else '',
                                 len(D), a.box, a.of, a.shard, a.shards, len(done)),
          flush=True)
    sc = T.Scorer()
    t0 = time.time()
    for i, cfg in enumerate(D.to_dict('records'), 1):
        combo = (cfg['c1'], cfg['c2'], cfg['vol'], cfg['base'],
                 cfg.get('exit_ind') or S.slot_options()['exit_ind'][0])
        sn = cfg['slice']
        code = dict((s, c) for s, _, c in S.SLICES)[sn]
        plan = dict((s, p) for s, p, _ in S.SLICES)[sn]
        try:
            ip1, rk1, _ = T._stage(sc, combo, 'B', sn, code, plan, ('W1',),
                                   None, False)       # cap=None: B ran uncapped
        except Exception as e:
            print('  %s FAILED %s' % (cfg['sid'][:50], str(e)[:80]), flush=True)
            continue
        row = dict(sid=cfg['sid'], c1=cfg['c1'], c2=cfg['c2'], vol=cfg['vol'],
                   base=cfg['base'], slice=sn, mode='B',
                   ip1=json.dumps(ip1, sort_keys=True),
                   risk1=json.dumps(rk1, sort_keys=True))
        pd.DataFrame([row]).to_csv(OUTF, mode='a', index=False,
                                   header=not os.path.exists(OUTF))
        el = time.time() - t0
        print('  %d/%d  %.0f s each  ~%.1f h left'
              % (i, len(D), el / i, (el / i) * (len(D) - i) / 3600), flush=True)
    print('DONE in %.1f min' % ((time.time() - t0) / 60), flush=True)


if __name__ == '__main__':
    main()
