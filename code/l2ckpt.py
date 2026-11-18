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
        # TWO CLOCKS, and the distinction is the rule itself.
        #   t_part   -- when to write the next part file
        #   t_unsaved -- when ANYTHING was last written, part or in-flight state
        # The rule bounds UNSAVED COMPUTE, so the assert reads t_unsaved. An
        # item longer than the interval is legal only if the owner checkpoints
        # inside it and calls tick(); otherwise the assert fires, which is what
        # it did on 16 Nov when a cold worker's first strategy took 481 s.
        self.t = time.time()
        self.t_unsaved = self.t
        self.n_saved = 0
        self.n_parts_written = 0
        self.n_ticks = 0

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

    def tick(self):
        """The owner has just written in-flight state for the item it is inside.
        Nothing is unsaved past this moment, so the unsaved clock resets; the
        part clock does not, because a part is still owed."""
        self.t_unsaved = time.time()
        self.n_ticks += 1

    def tick_due(self):
        return (time.time() - self.t_unsaved) >= self.every

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
        unsaved = time.time() - self.t_unsaved
        print('    ckpt %s: %d items -> %s (%.0f s since the last part, %.0f s unsaved, '
              '%d intra-item ticks, cap %d)'
              % (self.prefix, len(self.rows), os.path.basename(p), held, unsaved,
                 self.n_ticks, self.every), flush=True)
        assert unsaved < self.every + 120, (
            'a single item ran %.0f s with nothing saved, past the %d s interval -- '
            'the interval cannot bound it and the stage must checkpoint INSIDE the item '
            'and call Checkpointer.tick()' % (unsaved, self.every))
        self.ids, self.rows = [], []
        self.t = time.time()
        self.t_unsaved = self.t
        self.n_ticks = 0
        return p


# ==========================================================================
# the declaration a chain must carry, and its parser
# ==========================================================================
DECL = re.compile(r'^#\s*ckpt\s+(.+?)\s*=\s*(\d+)\s*(?:#\s*(.*))?$')
DISK = re.compile(r'^#\s*disk\s+(.+?)\s*=\s*([0-9.]+)\s*(?:#.*)?$')
ETA = re.compile(r'^#\s*eta\s*=\s*([0-9]+)\s*(?:#.*)?$')
DELIV = re.compile(r'^#\s*deliverable\s*=\s*(.+?)\s*(?:#.*)?$')
DISK_HEADROOM_GB = 2.0
NEEDS = re.compile(r'^#\s*needs\s+(.+?)\s*=\s*(.*?)\s*(?:#.*)?$')
STAGE = re.compile(r'^\s*g\s+"([^"]+)"')


def parse_driver(path):
    """-> (stages in call order, {stage: (seconds, reason)}, {stage: [deps]}).

    A stage is a `g "<name>"` call. Each one must carry two declarations:
        # ckpt  <name> = <seconds>   <reason>
        # needs <name> = <dep>[,<dep>...]   or   none
    Dependencies are COMMA separated because stage names contain spaces.
    """
    stages, decls, needs, disk = [], {}, {}, {}
    eta = [None]; deliv = [None]
    for line in open(path):
        m = STAGE.match(line)
        if m:
            stages.append(m.group(1))
            continue
        line = line.rstrip('\n')
        d = DECL.match(line)
        if d:
            decls[d.group(1).strip()] = (int(d.group(2)), (d.group(3) or '').strip())
            continue
        nd = NEEDS.match(line)
        if nd:
            raw = nd.group(2).strip()
            needs[nd.group(1).strip()] = ([] if raw.lower() in ('', 'none')
                                          else [x.strip() for x in raw.split(',') if x.strip()])
            continue
        dk = DISK.match(line)
        if dk:
            disk[dk.group(1).strip()] = float(dk.group(2))
            continue
        em = ETA.match(line)
        if em:
            eta[0] = int(em.group(1))
            continue
        dv = DELIV.match(line)
        if dv:
            deliv[0] = dv.group(1).strip()
    return stages, decls, needs, disk, eta[0], deliv[0]


def check_driver(path):
    """-> (ok, list of problems). The refusal logic, in one place so the guard
    and any caller see the same verdict."""
    stages, decls, needs, disk, eta, deliv = parse_driver(path)
    bad = []
    # GUARD 3 -- DISK. Every stage declares what it needs and the volume must
    # hold the sum plus headroom. On 18 Nov the nulls wrote 17 GB of per-shard
    # scratch into a volume with 9 GB free and took themselves, the app wiring
    # and the mode B resume down with OSError 28 -- and the watchdog could not
    # even report it, because its own writes failed too.
    dmissing = [x for x in stages if x not in disk]
    if dmissing:
        bad.append('stages with NO declared disk need (use "# disk <stage> = 0" if none): %s'
                   % dmissing)
    else:
        need = sum(disk.values()) + DISK_HEADROOM_GB
        st = os.statvfs(_R)
        free = st.f_bavail * st.f_frsize / 1024 ** 3
        if free < need:
            bad.append('declared disk need %.1f GB + %.1f GB headroom = %.1f GB, but only '
                       '%.1f GB is free' % (sum(disk.values()), DISK_HEADROOM_GB, need, free))
    # GUARD 4 -- DELIVERABLE AND ETA, both declared or the chain does not launch.
    if not deliv:
        bad.append('no "# deliverable = <path>" declared: a chain must say what it exists to produce')
    if not eta:
        bad.append('no "# eta = <minutes>" declared: the watchdog pushes when the ETA passes '
                   'without the deliverable, and it cannot do that without one')
    # EVERY STAGE DECLARES ITS DEPENDENCIES (Jack, 17 Nov). A failed stage no
    # longer stops the chain -- only its declared dependents are skipped -- so
    # an undeclared dependency would let a stage run on output that was never
    # produced, which is worse than halting. The declaration is therefore
    # mandatory, and `none` is a legitimate answer that has to be written down.
    nmissing = [s for s in stages if s not in needs]
    if nmissing:
        bad.append('stages with NO declared dependencies (use "= none" if there are none): %s'
                   % nmissing)
    order = {s: i for i, s in enumerate(stages)}
    for s in stages:
        for d in needs.get(s, []):
            if d not in order:
                bad.append('stage "%s" depends on "%s", which is not a stage in this driver' % (s, d))
            elif order[d] >= order[s]:
                bad.append('stage "%s" depends on "%s", which does not run before it' % (s, d))
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
