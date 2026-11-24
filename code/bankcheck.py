import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTDATA=os.path.join(_R,'data'); ROOTOUT=os.path.join(_R,'results')
os.makedirs(ROOTOUT,exist_ok=True); sys.path.insert(0,ROOTLIB)
"""BANK MANIFESTS: prove a bank is the one a result was produced from.

WHY THIS EXISTS. On 23 Nov two committed bank files, 145 MB each, made the
remote unreachable: GitHub refuses a blob over 100 MB, so the repo could not
be pushed at all and the history had to be rewritten. Banks are regenerable
derived data, not source, and they do not belong in git. But the project's
whole method rests on every number being traceable to a named file, so simply
gitignoring them would trade one problem for a worse one.

The answer is a MANIFEST IN GIT AND THE BANK ON DISK. Each bank directory
gets a MANIFEST.sha256 listing every part file with its size, its sha256 and
the commit that produced it. The manifest is small, text, and committed. The
bank itself is ignored. A result can then always be tied to the exact bytes it
came from, and a missing or altered bank fails LOUDLY at preflight instead of
silently producing numbers for a different universe.

BANKS ALREADY TRACKED IN GIT STAY TRACKED (Jack, 23 Nov). This does not git rm
anything. The ignore rules apply to the two universe files and to banks
created from now on.

    python3 code/bankcheck.py --write            # (re)write manifests
    python3 code/bankcheck.py                    # verify; non-zero on drift
    python3 code/bankcheck.py --quick            # sizes only, no hashing
"""
import glob, hashlib, subprocess, json

# WHICH DIRECTORIES ARE BANKS. Matched under results/; anything new that looks
# like a bank should be added here in the same commit that creates it.
BANK_GLOBS = (
    'r2gate2/mode?_full',
    'r2gate2/mode?_full_r2dd',
    'r2gate2/mode?_gate3parts',
    'r2gate2/mode?_bookparts_*',
    'r2gate2/mode?_gate3bookparts',
    'r2gate2/mode?_winners_nullparts',
    'r2gate2/mode?_nullparts_*',
)
MANIFEST = 'MANIFEST.sha256'
# A FULL HASH OF A 2 GB BANK IS NOT FREE. Measured on this Mac a sha256 of the
# mode A gate 3 bank is ~20 s. Preflight runs --quick by default, which checks
# the file list and every size; a size change is the overwhelmingly common
# failure (a truncated flush, a half-written part, a deleted shard). --full is
# for when a result is being published.
def _sha256(p, buf=1 << 20):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        while True:
            b = f.read(buf)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def _commit():
    try:
        return subprocess.run(['git', '-C', _R, 'rev-parse', 'HEAD'],
                              capture_output=True, text=True).stdout.strip()[:12]
    except Exception:
        return 'unknown'


def bank_dirs():
    out = []
    for g in BANK_GLOBS:
        for d in sorted(glob.glob(os.path.join(ROOTOUT, g))):
            if os.path.isdir(d):
                out.append(d)
    return out


def parts(d):
    return sorted(f for f in os.listdir(d)
                  if not f.startswith('.') and f != MANIFEST
                  and os.path.isfile(os.path.join(d, f)))


def write_manifest(d, full=True):
    rows = []
    c = _commit()
    for f in parts(d):
        p = os.path.join(d, f)
        rows.append(dict(file=f, size=os.path.getsize(p),
                         sha256=(_sha256(p) if full else ''), commit=c))
    man = os.path.join(d, MANIFEST)
    with open(man, 'w') as fh:
        fh.write('# %s\n# written %s by code/bankcheck.py at commit %s\n'
                 % (os.path.relpath(d, _R), __import__('time').strftime('%F %T'), c))
        fh.write('# file\tsize\tsha256\tproducing_commit\n')
        for r in rows:
            fh.write('%s\t%d\t%s\t%s\n' % (r['file'], r['size'], r['sha256'], r['commit']))
    return man, len(rows)


def read_manifest(d):
    man = os.path.join(d, MANIFEST)
    if not os.path.exists(man):
        return None
    out = {}
    for line in open(man):
        if line.startswith('#') or not line.strip():
            continue
        p = line.rstrip('\n').split('\t')
        if len(p) >= 2:
            out[p[0]] = dict(size=int(p[1]),
                             sha256=(p[2] if len(p) > 2 else ''),
                             commit=(p[3] if len(p) > 3 else ''))
    return out


def verify(full=False, verbose=True):
    bad = []
    seen = 0
    for d in bank_dirs():
        rel = os.path.relpath(d, _R)
        man = read_manifest(d)
        if man is None:
            if verbose:
                print('  %-46s NO MANIFEST (run --write)' % rel, flush=True)
            continue
        have = set(parts(d))
        want = set(man)
        seen += 1
        missing = sorted(want - have)
        extra = sorted(have - want)
        changed = []
        for f in sorted(want & have):
            p = os.path.join(d, f)
            if os.path.getsize(p) != man[f]['size']:
                changed.append((f, 'size %d != %d' % (os.path.getsize(p), man[f]['size'])))
            elif full and man[f]['sha256'] and _sha256(p) != man[f]['sha256']:
                changed.append((f, 'sha256 differs'))
        if missing or extra or changed:
            bad.append(dict(bank=rel, missing=missing, extra=extra, changed=changed))
            if verbose:
                print('  %-46s DRIFT: %d missing, %d extra, %d changed'
                      % (rel, len(missing), len(extra), len(changed)), flush=True)
                for f in missing[:4]:
                    print('       missing %s' % f, flush=True)
                for f, why in changed[:4]:
                    print('       changed %s (%s)' % (f, why), flush=True)
        elif verbose:
            print('  %-46s ok (%d parts%s)'
                  % (rel, len(want), ', hashed' if full else ', sizes only'), flush=True)
    return bad, seen


def main():
    import l2r2gate1 as G
    if G.opt('--write', bool, False) or '--write' in sys.argv:
        full = '--quick' not in sys.argv
        n = 0
        for d in bank_dirs():
            man, k = write_manifest(d, full=full)
            n += 1
            print('  wrote %-52s %d parts' % (os.path.relpath(man, _R), k), flush=True)
        print('  %d manifests written (%s)'
              % (n, 'with hashes' if full else 'sizes only'), flush=True)
        return 0
    full = '--full' in sys.argv
    print('  BANKCHECK: %s' % ('full hashes' if full else 'sizes only (--full to hash)'),
          flush=True)
    bad, seen = verify(full=full)
    if bad:
        print('  BANKCHECK FAILED: %d of %d banks have drifted from their manifest. '
              'A result computed now would not match the bank the manifest names.'
              % (len(bad), seen), flush=True)
        return 1
    print('  bankcheck OK: %d banks match their manifests' % seen, flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
