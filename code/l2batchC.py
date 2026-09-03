import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""WEEKLY MODE C BATCH — the delivery that runs while C tunes for months.

Installed as a launchd job so it survives session expiry and reboots, which the
nohup'd watchers in this project do not: they survive a session but not a power
cycle, and this run is projected to last into 2027.

  1. new crossers since the last batch -> gate2_modeC_crossers_batch<N>.csv
  2. crisis split + suppressed-vol flags + l2rank over ALL C crossers to date
  3. mode C slots in the app refreshed, stamped
  4. graft-challenge sweep re-run WITH C's crossers, and whether the book moves
  5. commit, and a batch section appended through the manifest_extra convention

SPARE CAPACITY ONLY. Everything here runs at nice 19 on ONE core. Mode C's two
pools are never signalled, never counted against, and never waited on. The
standing rule is that the tuning queue is the product; this is a reader of its
output and must behave like one.

FAILS LOUDLY. Any step that raises leaves results/BATCH_FAILED.marker on disk
with the traceback and the batch number, and the failure is written to the log
rather than swallowed. A batch that quietly does nothing is worse than a batch
that stops, because the next one would inherit a broken high-water mark and the
gap would never be noticed.

THE HIGH-WATER MARK is the set of chunk FILES already folded in, recorded in
results/modeC_batch_state.json. Chunk ids are not contiguous -- two pools work
from opposite ends -- so "everything above id N" would silently skip the gap in
the middle. The state file lists filenames.
"""
import glob, json, subprocess, time, traceback
import datetime as dt
import numpy as np, pandas as pd

STATE = os.path.join(ROOTOUT, 'modeC_batch_state.json')
MARKER = os.path.join(ROOTOUT, 'BATCH_FAILED.marker')
LOG = os.path.join(ROOTOUT, 'batchC.log')
POP = {'trend': 554422, 'chop': 162481}
WORKERS = 9


def say(msg):
    line = '%s %s' % (dt.datetime.now().strftime('%F %T'), msg)
    print(line, flush=True)
    with open(LOG, 'a') as f:
        f.write(line + '\n')


def load_state():
    if os.path.exists(STATE):
        return json.load(open(STATE))
    return {'batch': 0, 'files': []}


def run(cmd, why):
    """One core, lowest priority, and a non-zero exit is an error not a warning."""
    say('  run: %s' % why)
    p = subprocess.run(['nice', '-n', '19', sys.executable] + cmd,
                       cwd=_R, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError('%s failed (exit %d)\n%s' % (why, p.returncode,
                                                        p.stdout[-2000:] + p.stderr[-2000:]))
    return p.stdout


def measured_rate():
    """C's OWN cost per combination, cumulative average. Never the recent
    chunks: fast chunks finish first, so any recent window is biased fast."""
    f = os.path.join(ROOTOUT, 'gate2_progress_modeC.csv')
    if not os.path.exists(f):
        return None, None
    d = pd.read_csv(f)
    if not len(d) or not d.combos.sum():
        return None, None
    return float(d.seconds.sum() / d.combos.sum()), int(d.combos.sum())


def projection(spc):
    """Trend at C's measured rate; chop scaled by A's own chop:trend ratio,
    since C's chop slice has not started and pretending otherwise would be a
    guess wearing a measurement's clothes."""
    if not spc:
        return None
    eh = (POP['trend'] * spc + POP['chop'] * spc * (132.5 / 161.4)) / 3600.0
    days = eh / WORKERS / 24.0
    done = 0
    f = os.path.join(ROOTOUT, 'gate2_progress_modeC.csv')
    if os.path.exists(f):
        done = int(pd.read_csv(f).combos.sum())
    left_h = eh * (1 - done / float(sum(POP.values())))
    return dict(engine_hours=eh, days=days, done=done,
                days_left=left_h / WORKERS / 24.0,
                finish=(dt.date.today() + dt.timedelta(days=left_h / WORKERS / 24.0)).isoformat())


def collect(state):
    fs = sorted(glob.glob(os.path.join(ROOTOUT, 'gate2', 'modeC_*', 'chunk_*.csv')))
    seen = set(state.get('files', []))
    new = [f for f in fs if os.path.basename(os.path.dirname(f)) + '/' +
           os.path.basename(f) not in seen]
    keys = [os.path.basename(os.path.dirname(f)) + '/' + os.path.basename(f) for f in fs]
    if not fs:
        return None, None, keys
    ALL = pd.concat([pd.read_csv(f, low_memory=False) for f in fs], ignore_index=True)
    NEW = (pd.concat([pd.read_csv(f, low_memory=False) for f in new], ignore_index=True)
           if new else ALL.iloc[0:0])
    return ALL, NEW, keys


def main():
    t0 = time.time()
    state = load_state()
    n = state['batch'] + 1
    say('=' * 64)
    say('MODE C BATCH %d starting' % n)
    try:
        if os.path.exists(MARKER):
            say('  NOTE: a previous batch left %s -- clearing it now that this '
                'batch has started' % os.path.basename(MARKER))
            os.remove(MARKER)

        ALL, NEW, keys = collect(state)
        if ALL is None or not len(ALL):
            raise RuntimeError('no mode C chunks on disk')
        newx = NEW[(NEW.crosses_label == True) & NEW.ip2.notna()]
        allx = ALL[(ALL.crosses_label == True) & ALL.ip2.notna()]
        say('  chunks folded in: %d (%d new since batch %d)'
            % (len(keys), len(keys) - len(state.get('files', [])), state['batch']))
        say('  combinations: %d total, %d new' % (len(ALL), len(NEW)))
        say('  crossers: %d total (%.2f%%), %d new'
            % (len(allx), 100.0 * len(allx) / max(1, len(ALL)), len(newx)))

        # 1. the batch file and the cumulative tuned file
        bf = os.path.join(ROOTOUT, 'gate2_modeC_crossers_batch%02d.csv' % n)
        newx.to_csv(bf, index=False)
        ALL.to_csv(os.path.join(ROOTOUT, 'gate2_tuned_modeC.csv'), index=False)
        say('  wrote %s (%d rows)' % (os.path.basename(bf), len(newx)))

        # 2. crisis split -> rank -> clean view, over ALL crossers to date.
        #    Slice-scoped because C's chop has not started; --slice keeps the
        #    file names honest about what is actually in them.
        for sl in sorted(set(allx['slice'])):
            run(['code/l2crisis_all.py', '--mode', 'C', '--slice', sl,
                 '--src', os.path.join(ROOTOUT, 'gate2_tuned_modeC.csv')],
                'crisis split C/%s' % sl)
            run(['code/l2rank.py', '--mode', 'C', '--slice', sl, '--clean'],
                'rank + clean view C/%s' % sl)
            run(['code/l2deliver.py', '--mode', 'C', '--slice', sl, '--top', '10'],
                'trade bundles C/%s' % sl)

        # 3. app
        st = os.path.join(ROOTOUT, 'modes_status.json')
        s = json.load(open(st)) if os.path.exists(st) else {}
        s.setdefault('C', {})
        for sl in ('trend', 'chop'):
            s['C'][sl] = ('running' if sl in set(ALL['slice']) else 'queued')
        json.dump(s, open(st, 'w'), indent=1)
        run(['code/l2modes.py'], 'mode index')
        run(['code/appstamp.py'], 'build stamp')

        # 4. the graft challenge, now with C in the pool
        # MEMBERSHIP, not just N and mix. The co-equal rule scores on RANKS
        # within the pool, so adding rows that never reach the top perturbs
        # every incumbent's rank number and can change the chosen N without a
        # single new strategy earning a place. Batch 1 did exactly that. The
        # only honest question is whether the SET of strategies changed.
        def _members(path, n):
            if not os.path.exists(path):
                return None
            L = pd.read_csv(path, low_memory=False).sort_values('rank').head(n)
            return set(map(tuple, L[['c1', 'c2', 'vol', 'base', 'slice']].values))
        before = None
        pj = os.path.join(ROOTOUT, 'portfolio_preview_combined_AB.json')
        if os.path.exists(pj):
            b = json.load(open(pj))
            before = (b.get('N'), b.get('mix'), (b.get('metrics') or {}).get('total_R'))
            before_set = _members(os.path.join(ROOTOUT, 'gate2_combined_AB_leaderboard.csv'),
                                  b.get('N') or 0)
        run(['code/l2sweepn.py', '--combine-c', '--lo', '5', '--hi', '25'],
            'graft challenge including C')
        after = None
        pc = os.path.join(ROOTOUT, 'portfolio_preview_combined_ABC.json')
        if os.path.exists(pc):
            a = json.load(open(pc))
            after = (a.get('N'), a.get('mix'), (a.get('metrics') or {}).get('total_R'))

        # 5. record
        spc, done = measured_rate()
        pr = projection(spc)
        best = None
        lb = os.path.join(ROOTOUT, 'gate2_modeC_trend_leaderboard.csv')
        if os.path.exists(lb):
            L = pd.read_csv(lb, low_memory=False).sort_values('rank')
            if len(L):
                r = L.iloc[0]
                sh = lambda x: str(x).replace('_signals', '').replace('_volume', '').replace('_baseline', '')
                best = ('%s x %s x %s x %s' % (sh(r.c1), sh(r.c2), sh(r.vol), sh(r.base)),
                        float(r.ex_total_R), float(r.ex_sortino), int(r.ex_n))
        sec = []
        sec.append('\n### MODE C BATCH %d — %s\n' % (n, dt.date.today().isoformat()))
        sec.append('| | |')
        sec.append('|---|---|')
        sec.append('| combinations processed | %s total, %s new this batch |'
                   % (format(len(ALL), ','), format(len(NEW), ',')))
        sec.append('| crossing the gate 2 label | **%s (%.2f%%)**, %s new |'
                   % (format(len(allx), ','), 100.0 * len(allx) / max(1, len(ALL)),
                      format(len(newx), ',')))
        if best:
            sec.append('| best crosser to date | `%s` — %d blind trades, **%.2f R**, Sortino %.2f |'
                       % (best[0], best[3], best[1], best[2]))
        if spc:
            sec.append('| C measured cost | **%.1f s/combination** (cumulative average) |' % spc)
        if pr:
            sec.append('| progress | %s of %s combinations (%.2f%%) |'
                       % (format(pr['done'], ','), format(sum(POP.values()), ','),
                          100.0 * pr['done'] / sum(POP.values())))
            sec.append('| projected finish | **%s** (%.0f days left at %d workers) |'
                       % (pr['finish'], pr['days_left'], WORKERS))
        if before and after:
            after_set = _members(os.path.join(ROOTOUT, 'gate2_combined_ABC_leaderboard.csv'),
                                 after[0] or 0)
            n_c = (after[1] or {}).get('C', 0)
            new_names = ((after_set - before_set) if (before_set and after_set) else set())
            if n_c:
                sec.append('| graft challenge | **A MODE C STRATEGY ENTERED THE BOOK** — '
                           'N=%s, %s, %.2f R |' % (after[0], after[1], after[2] or 0))
            elif new_names:
                sec.append('| graft challenge | book membership changed but **no C strategy '
                           'entered** — %d strategies swapped, N=%s -> %s |'
                           % (len(new_names), before[0], after[0]))
            else:
                sec.append('| graft challenge | **no C crosser earns a place.** The same '
                           'strategies as before; N moved %s -> %s only because the '
                           'co-equal rule scores on ranks WITHIN the pool, so 246 extra '
                           'rows shift every incumbent rank number |'
                           % (before[0], after[0]))
        open(os.path.join(ROOTLIB, 'manifest_extra.md'), 'a').write('\n'.join(sec) + '\n')
        open(os.path.join(_R, 'GAUNTLET.md'), 'a').write('\n'.join(sec) + '\n')
        run(['code/persist.py'], 'render manifest')

        state = {'batch': n, 'files': keys,
                 'last_run': dt.datetime.now().isoformat(timespec='seconds')}
        json.dump(state, open(STATE, 'w'), indent=1)

        subprocess.run(['git', 'add', '-A'], cwd=_R)
        subprocess.run(['git', 'commit', '-q', '-m',
                        'Mode C batch %d: %d crossers of %d (%.2f%%)\n\n'
                        'Automatic weekly delivery by code/l2batchC.py under launchd.\n\n'
                        'Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>\n'
                        'Claude-Session: https://claude.ai/code/session_0198PoFd8YbETkDPepLUiDzL'
                        % (n, len(allx), len(ALL), 100.0 * len(allx) / max(1, len(ALL)))],
                       cwd=_R)
        subprocess.run(['git', 'pull', '--rebase', '-q', 'origin', 'main'], cwd=_R)
        subprocess.run(['git', 'push', '-q', 'origin', 'main'], cwd=_R)
        say('MODE C BATCH %d COMPLETE in %.0f s' % (n, time.time() - t0))
    except Exception:
        tb = traceback.format_exc()
        with open(MARKER, 'w') as f:
            f.write('BATCH %d FAILED at %s\n\n%s\n' % (n, dt.datetime.now(), tb))
        say('!' * 64)
        say('MODE C BATCH %d FAILED -- see results/BATCH_FAILED.marker' % n)
        for line in tb.strip().split('\n'):
            say('  ' + line)
        say('!' * 64)
        # the state file is NOT advanced, so the next batch retries this window
        subprocess.run(['git', 'add', '-f', MARKER, LOG], cwd=_R)
        subprocess.run(['git', 'commit', '-q', '-m',
                        'Mode C batch %d FAILED -- marker committed' % n], cwd=_R)
        subprocess.run(['git', 'push', '-q', 'origin', 'main'], cwd=_R)
        raise SystemExit(1)


if __name__ == '__main__':
    main()
