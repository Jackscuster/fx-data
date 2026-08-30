import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""DISK-BACKED INDICATOR CACHE, shared across modes and across worker processes.

WHY THIS IS SOUND. `L.compute(name, o, h, l, c, **params)` never sees the exit
mode, the plan or the slice -- an indicator series is a pure function of its
name, its parameters and the pair's bars. So every series computed while tuning
mode B is valid, unchanged, for A and C. Jack's premise; this is the mechanism.

WHY IT IS BOUNDED RATHER THAN COMPLETE. The full reachable space is 12.9M
distinct (indicator, param-tuple) sets -- 12 grid points per parameter, capped
at six, so 12^6 for the widest indicators -- which at 28 pairs and ~20 KB an
entry is 6.7 TB. What is actually SHARED is the shallow layer: coordinate
descent sweeps each indicator's first parameter from that indicator's defaults
for every combination, so those tuples are hit by every combination naming it,
while deeper tuples depend on what earlier knobs adopted and diverge. A
size-capped LRU therefore self-selects: hot shallow entries survive, deep
one-offs are evicted, and no policy has to know which is which in advance.

WORKER SAFETY, and the two races that matter:
  WRITE  two workers computing the same key write identical bytes. The write
         goes to a temp file and is os.replace'd into position, which is atomic
         on this filesystem, so a reader sees either the old file or the whole
         new one and never a half-written array.
  EVICT  a worker may unlink a file another worker is mid-read. On macOS an
         open descriptor survives the unlink, and the read completes; but the
         window between stat and open is not protected, so every read is
         wrapped and a failure falls back to recomputing. A cache miss is slow,
         never wrong.

The cache is a SPEED device with no effect on results. `verify.py`-style proof
of that is l2cache.verify(), which recomputes a sample and compares byte for
byte, plus an end-to-end re-run of banked combinations in l2tune.
"""
import glob, hashlib, shutil, time
import numpy as np

DIR = os.path.join(ROOTOUT, 'gate2_cache')
BUDGET_GB = 10.0
# A SIZE CHECK IS NOT CHEAP. size_bytes() walks every file in the store, which
# at ~300k entries measures 24 SECONDS. Calling it every 400 writes per worker
# put seven workers into a state where they spent essentially all of their time
# walking this directory instead of tuning -- 0% CPU, sleeping, no progress.
# Found by launching mode A and watching it do nothing.
#
# So: accumulate the bytes THIS PROCESS has written, and only pay for a real
# walk once that accumulation could plausibly matter. With a 10 GB budget and
# 1 GB between walks, a worker walks at most a handful of times across a whole
# run instead of thousands.
WALK_EVERY_BYTES = 1 * 1024 ** 3
_written_since_walk = 0


def key(name, params, pair):
    raw = '%s|%s|%s' % (name, repr(sorted(params.items())), pair)
    return hashlib.sha1(raw.encode()).hexdigest()


def _path(k):
    return os.path.join(DIR, k[:2], k[2:4], k + '.npz')


def get(name, params, pair):
    """Return the cached tuple of arrays, or None. Never raises: a damaged or
    concurrently-evicted entry is a miss, and a miss is only slow."""
    p = _path(key(name, params, pair))
    try:
        with np.load(p, allow_pickle=False) as z:
            n = int(z['n'])
            return tuple(z['a%d' % i] for i in range(n))
    except Exception:
        return None


def put(name, params, pair, value):
    """Atomic: temp file then os.replace, so a reader never sees a partial."""
    global _written_since_walk
    arrs = value if isinstance(value, tuple) else (value,)
    k = key(name, params, pair)
    p = _path(k)
    try:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        # np.savez APPENDS .npz unless the name already ends with it, so the
        # temp name must end in .npz or the file lands somewhere else and the
        # replace silently moves nothing.
        tmp = '%s.%d.tmp.npz' % (p, os.getpid())
        np.savez(tmp, n=np.int64(len(arrs)),
                 **{'a%d' % i: np.asarray(a) for i, a in enumerate(arrs)})
        os.replace(tmp, p)
    except Exception:
        try:
            for junk in glob.glob('%s.%d.tmp*' % (p, os.getpid())):
                os.remove(junk)
        except Exception:
            pass
        return False
    global _written_since_walk
    try:
        _written_since_walk += os.path.getsize(p)
    except OSError:
        pass
    if _written_since_walk >= WALK_EVERY_BYTES:
        _written_since_walk = 0
        evict()
    return True


def size_bytes():
    tot = 0
    for r, _, fs in os.walk(DIR):
        for f in fs:
            try:
                tot += os.path.getsize(os.path.join(r, f))
            except OSError:
                pass
    return tot


def evict(budget_gb=None):
    """LRU by mtime, down to 90% of budget. Approximate on purpose: an exact
    global LRU across eight processes would need a lock on every read, which
    would cost more than the evictions save."""
    budget = (budget_gb or BUDGET_GB) * 1024 ** 3
    tot = size_bytes()
    if tot <= budget:
        return 0
    files = []
    for r, _, fs in os.walk(DIR):
        for f in fs:
            p = os.path.join(r, f)
            try:
                st = os.stat(p)
                files.append((st.st_mtime, st.st_size, p))
            except OSError:
                pass
    files.sort()
    freed = 0
    target = tot - budget * 0.9
    for _, sz, p in files:
        if freed >= target:
            break
        try:
            os.remove(p); freed += sz
        except OSError:
            pass
    return freed


def stats():
    n = sum(len(fs) for _, _, fs in os.walk(DIR))
    return dict(entries=n, gb=size_bytes() / 1024 ** 3)


def verify(n_sample=200, seed=11):
    """PROOF THAT THE CACHE CANNOT CHANGE A RESULT.

    Recompute a sample of cached entries from scratch and compare byte for
    byte. Any difference means the cache is returning something the engine
    would not have computed, which would silently corrupt every score that
    touched it."""
    import l2lib as L, l2sweep as S, l2tune as T
    pairs = S.all_pairs()
    raw = {p: tuple(S.load_pair(p)[k].values.astype(float)
                    for k in ('open', 'high', 'low', 'close')) for p in pairs}
    # The cache is keyed by a hash, which cannot be inverted, so entries are
    # re-derived from known (indicator, params, pair) triples rather than read
    # back from the directory. An empty cache is populated as it goes: the test
    # is that a cached read equals a fresh compute, which is meaningful whether
    # the entry was already there or was written a moment ago.
    rng = np.random.default_rng(seed)
    reg = T.registry()
    names = sorted(reg)
    checked = mism = 0
    for _ in range(n_sample):
        name = names[rng.integers(len(names))]
        pair = pairs[rng.integers(len(pairs))]
        params = dict(reg[name])
        for pn in list(params)[:2]:
            g = T.ind_param_grid(params[pn])
            params[pn] = g[rng.integers(len(g))]
        cached = get(name, params, pair)
        if cached is None:
            fresh = L.compute(name, *raw[pair], **params)
            put(name, params, pair, fresh)
            cached = get(name, params, pair)
        fresh = L.compute(name, *raw[pair], **params)
        fa = fresh if isinstance(fresh, tuple) else (fresh,)
        checked += 1
        if len(fa) != len(cached):
            mism += 1; continue
        for a, b in zip(fa, cached):
            a = np.asarray(a); b = np.asarray(b)
            if a.shape != b.shape or a.dtype != b.dtype or \
               not np.array_equal(a, b, equal_nan=True):
                mism += 1
                break
    return dict(checked=checked, mismatches=mism, **stats())


if __name__ == '__main__':
    if '--evict' in sys.argv:
        print('freed %.2f GB' % (evict() / 1024 ** 3))
    print(stats())
    if '--verify' in sys.argv:
        print(verify(n_sample=int(sys.argv[sys.argv.index('--verify') + 1])
                     if len(sys.argv) > sys.argv.index('--verify') + 1 else 200))
