import os,sys
_R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTLIB=os.path.join(_R,'code'); ROOTOUT=os.path.join(_R,'results')
sys.path.insert(0,ROOTLIB)
"""NO SILENCED ERRORS — a mechanical check, run before any chain starts.

On 2026-09-11 `git stash pop -q 2>/dev/null` hid the one message that would have
said the uncommitted l2walkfwd.py was still in a stash. Six chain stages then
ran against a binary with no --suffix and exited in a second each. Two hours.
The chain's own guards worked; the suppressed git error was the whole fault.

A failure that cannot print is a failure that surfaces somewhere else, later,
looking like something it is not. This refuses to let one be written.
"""
import re, glob, argparse

PATTERNS = (
    (r'2>\s*/dev/null',        'stderr sent to /dev/null'),
    (r'\|\|\s*true\b',         '|| true swallows a non-zero exit'),
    # ANCHORED, NOT GREEDY. The original was r'\bgit\b[^\n#]*\s-q\b', which
    # backtracks catastrophically on the long lines in l2lib.py and hangs the
    # scan -- a checker that never finishes is a checker that gets skipped.
    (r'(?<![\w-])git +(?:[a-z-]+ +)*?-q(?![\w-])', 'git -q hides what git is doing'),
    (r'except\s*:\s*(pass|continue)\b', 'bare except that swallows'),
    (r'except\s+[\w.]+\s*:\s*(pass|continue)\s*$', 'typed except that swallows'),
    (r'except\s+[\w.]+\s+as\s+\w+\s*:\s*(pass|continue)\s*$', 'except-as that swallows'),
)
# Lines that have EARNED an exemption carry this marker and a reason.
ALLOW = 'NOSILENCE-OK:'


def scan(paths):
    hits = []
    for f in paths:
        try:
            lines = open(f, errors='replace').read().splitlines()
        except Exception as e:
            hits.append((f, 0, 'unreadable: %s' % e, ''))
            continue
        # PROSE IS NOT CODE. The patterns are quoted verbatim in docstrings that
        # EXPLAIN the rule, so a scanner that reads strings flags its own
        # documentation and halts every chain. Triple-quoted blocks and comments
        # are skipped; only executable lines are judged.
        indoc = None
        for i, ln in enumerate(lines, 1):
            st = ln.strip()
            if indoc:
                if indoc in ln:
                    indoc = None
                continue
            for q in ('\"\"\"', "'''"):
                if q in ln and ln.count(q) % 2 == 1:
                    indoc = q
                    break
            if indoc:
                continue
            if ALLOW in ln:
                continue
            if st.startswith('#') or st.startswith('*'):
                continue
            for pat, why in PATTERNS:
                if re.search(pat, ln):
                    hits.append((f, i, why, st[:100]))
                    break
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--paths', default='')
    ap.add_argument('--warn-only', action='store_true')
    a = ap.parse_args()
    paths = ([p for p in a.paths.split(',') if p] or
             sorted(glob.glob(os.path.join(ROOTLIB, '*.py')) +
                    glob.glob(os.path.join(ROOTLIB, '*.sh'))))
    paths = [p for p in paths if not p.endswith('l2nosilence.py')]
    hits = scan(paths)
    if not hits:
        print('NO SILENCED ERRORS: %d files clean' % len(paths), flush=True)
        return 0
    by = {}
    for f, i, why, src in hits:
        by.setdefault(os.path.basename(f), []).append((i, why, src))
    print('NO SILENCED ERRORS: %d findings across %d of %d files'
          % (len(hits), len(by), len(paths)), flush=True)
    for f in sorted(by):
        print('  %s' % f, flush=True)
        for i, why, src in by[f][:40]:
            print('    :%-5d %-38s %s' % (i, why, src), flush=True)
    if a.warn_only:
        return 0
    open(os.path.join(ROOTOUT, 'CHAIN_HALT.marker'), 'w').write(
        'l2nosilence: %d silenced-error sites\n' % len(hits))
    print('HALT: fix these or mark each with "%s <reason>"' % ALLOW, flush=True)
    return 1


if __name__ == '__main__':
    sys.exit(main())
