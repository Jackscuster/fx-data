import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""THE FIVE-MINUTE RULE (Jack, 16 Nov -- HANDOFF section 3).

NO STAGE MAY HOLD MORE THAN FIVE MINUTES OF COMPUTE UNSAVED. Every worker
writes incrementally and skips work already on disk when it restarts.

WHY IT IS A RULE. On 16 Nov the gate 2 smoke scored all 2,000 strategies and
then died in the save path: 2 h 19 min of compute, nothing on disk. Earlier the
same week a mode C bank took 77 minutes and died reading itself back. Both were
total losses that a five-minute checkpoint would have capped at five minutes.

HOW IT IS ENFORCED. Two halves, and both are mechanical:

  * THIS MODULE is what a worker uses. `Checkpointer` owns the clock and the
    part files. It flushes when the interval has elapsed, numbers parts in the
    order they are written, and records in each part the identity of the work it
    contains -- so resume is a set difference and is correct at ANY flush
    cadence. A fixed "every N items" scheme is not: change N and the part
    boundaries move, and the old parts become unreadable as progress.

  * `code/l2stagecheck.py chain <driver.sh>` refuses to launch a chain whose
    stages do not each DECLARE their checkpoint interval, and ~/fx-data-logs/
    launch.sh calls it before it will start anything.

A stage that genuinely holds nothing -- a read-only report, a one-shot write --
declares `0` and says why. The declaration is the point: an undeclared stage is
a stage nobody has thought about.
"""
import time, glob, re
import numpy as np

CKPT_SECONDS = int(os.environ.get('FX_CKPT_SECONDS', '300'))
MAX_CKPT_SECONDS = 300           # the rule. Nothing may declare more.


class Checkpointer:
    """Incremental saves with set-difference resume.

    Usage inside a worker:

        ck = Checkpointer(outdir, 'shard_%04d' % shard, save=my_save_fn)
        done = ck.completed()                  # ids already on disk
        for item in work:
            if item.id in done: continue
            ck.add(item.id, result)            # flushes on its own clock
        ck.flush()                             # the tail

    `save(path, ids, rows)` is supplied by the caller and does the actual
    write; this class only decides WHEN and keeps the bookkeeping honest.
    """

    def __init__(self, outdir, prefix, save, every=None, id_key='idx'):
        self.outdir = outdir
        self.prefix = prefix
        self.save = save
        self.every = int(every or CKPT_SECONDS)
        assert 0 < self.every <= MAX_CKPT_SECONDS, (
            'checkpoint interval %s s breaks the five-minute rule (max %d)'
            % (self.every, MAX_CKPT_SECONDS))
        self.id_key = id_key
        os.makedirs(outdir, exist_ok=True)
        self.ids, self.rows = [], []
        self.t = time.time()
        self.n_saved = 0
        self.n_parts_written = 0

    def parts(self):
        return sorted(glob.glob(os.path.join(self.outdir, self.prefix + '_part*.npz')))

    def completed(self):
        """Every id already on disk for this prefix. A set difference, so it is
        correct whatever cadence the earlier run used."""
        done = set()
        for f in self.parts():
            try:
                z = np.load(f, allow_pickle=True)
                done.update(int(x) for x in z[self.id_key])
            except Exception as e:
                # NOSILENCE-OK: a truncated tail part is expected after a kill;
                # it is named and then rewritten, never silently trusted.
                print('  ckpt: %s unreadable (%s) -- it will be rewritten'
                      % (os.path.basename(f), type(e).__name__), flush=True)
        return done

    def _next_path(self):
        existing = {int(re.search(r'_part(\d+)\.npz$', f).group(1)) for f in self.parts()}
        q = 0
        while q in existing:
            q += 1
        return os.path.join(self.outdir, '%s_part%04d.npz' % (self.prefix, q))

    def due(self):
        return (time.time() - self.t) >= self.every

    def add(self, item_id, row):
        self.ids.append(int(item_id))
        self.rows.append(row)
        if self.due():
            self.flush()

    def flush(self):
        if not self.rows:
            self.t = time.time()
            return None
        p = self._next_path()
        self.save(p, np.array(self.ids, np.int64), self.rows)
        self.n_saved += len(self.rows)
        self.n_parts_written += 1
        held = time.time() - self.t
        print('    ckpt %s: %d items -> %s (%.0f s of compute held, cap %d)'
              % (self.prefix, len(self.rows), os.path.basename(p), held, self.every), flush=True)
        assert held < self.every + 120, (
            'a single item took %.0f s, longer than the %d s checkpoint interval -- '
            'the interval cannot bound it and the stage must checkpoint inside the item'
            % (held, self.every))
        self.ids, self.rows = [], []
        self.t = time.time()
        return p


# ==========================================================================
# the declaration a chain must carry, and its parser
# ==========================================================================
DECL = re.compile(r'^#\s*ckpt\s+(.+?)\s*=\s*(\d+)\s*(?:#\s*(.*))?$')
STAGE = re.compile(r'^\s*g\s+"([^"]+)"')


def parse_driver(path):
    """-> (stages in call order, {stage: (seconds, reason)}).

    A stage is a `g "<name>"` call. A declaration is a line
        # ckpt <name> = <seconds>   <reason>
    at the top of the driver.
    """
    stages, decls = [], {}
    for line in open(path):
        m = STAGE.match(line)
        if m:
            stages.append(m.group(1))
            continue
        d = DECL.match(line.rstrip('\n'))
        if d:
            decls[d.group(1).strip()] = (int(d.group(2)), (d.group(3) or '').strip())
    return stages, decls


def check_driver(path):
    """-> (ok, list of problems). The refusal logic, in one place so the guard
    and any caller see the same verdict."""
    stages, decls = parse_driver(path)
    bad = []
    if not stages:
        bad.append('no stages found: a chain must call its stages through g "<name>"')
    missing = [s for s in stages if s not in decls]
    if missing:
        bad.append('stages with NO declared checkpoint interval: %s' % missing)
    extra = [k for k in decls if k not in stages]
    if extra:
        bad.append('declarations for stages that do not exist: %s' % extra)
    for s in stages:
        if s in decls:
            sec, why = decls[s]
            if sec > MAX_CKPT_SECONDS:
                bad.append('stage "%s" declares %d s, over the %d s rule' % (s, sec, MAX_CKPT_SECONDS))
            if sec == 0 and not why:
                bad.append('stage "%s" declares 0 s without saying why it holds nothing' % s)
    if stages:
        first = stages[0]
        sec, why = decls.get(first, (None, ''))
        if 'endtoend' not in first.replace(' ', '').lower() and 'end to end' not in first.lower():
            bad.append('the FIRST stage is "%s"; every chain must begin with a one-minute '
                       'end-to-end test of its own save and read path' % first)
        elif sec and sec > 60:
            bad.append('the end-to-end stage declares %d s; it must be a one-minute test' % sec)
    return (not bad), bad


if __name__ == '__main__':
    for p in sys.argv[1:]:
        ok, bad = check_driver(p)
        print('%s: %s' % (os.path.basename(p), 'OK' if ok else 'REFUSED'))
        for b in bad:
            print('   - %s' % b)
    raise SystemExit(0)
