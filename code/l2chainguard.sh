#!/bin/bash
# CHAIN PRE-FLIGHT. Sourced by every chain script before the first stage.
#
#   need_flags <script.py> <--flag> [--flag ...]
#       Asserts each flag EXISTS in the script the stage is about to call.
#       On 2026-09-11 six stages were launched with --suffix against a
#       l2walkfwd.py that had lost it to a git stash. argparse rejected the
#       unknown argument and each stage exited in ONE SECOND. The chain
#       reported six failures correctly, but a stage that dies on its own
#       arguments should never have been started -- the flag is checkable
#       before the work is.
#
#   chain_pidfile <name>   write a pidfile so git operations can refuse to run
#   assert_no_chain        refuse a git tree operation while a chain is live
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PIDDIR="$ROOT/results/chain_pids"

need_flags() {
  local script="$1"; shift
  if [ ! -f "$ROOT/$script" ]; then
    echo "!! HALT: $script does not exist"; exit 3
  fi
  local missing=()
  for fl in "$@"; do
    if ! grep -q -- "add_argument('${fl}'" "$ROOT/$script" \
       && ! grep -q -- "add_argument(\"${fl}\"" "$ROOT/$script"; then
      missing+=("$fl")
    fi
  done
  if [ ${#missing[@]} -gt 0 ]; then
    echo "!! HALT: $script does not accept: ${missing[*]}"
    echo "!! The stage would exit in one second and look like a fast success."
    echo "!! Commit the change that adds these flags before launching the chain."
    exit 3
  fi
  echo "   pre-flight ok: $script accepts $*"
}

chain_pidfile() {
  mkdir -p "$PIDDIR"
  echo $$ > "$PIDDIR/$1.pid"
  trap 'rm -f "$PIDDIR/'"$1"'.pid"' EXIT
}

assert_no_chain() {
  mkdir -p "$PIDDIR"
  local live=()
  for f in "$PIDDIR"/*.pid; do
    [ -e "$f" ] || continue
    local p; p=$(cat "$f")
    if kill -0 "$p" 2>/dev/null; then  # NOSILENCE-OK: kill -0 is the liveness probe itself; a dead pid is the answer
      live+=("$(basename "$f" .pid):$p")
    else
      rm -f "$f"
    fi
  done
  if [ ${#live[@]} -gt 0 ]; then
    echo "!! REFUSING: a chain is running (${live[*]})."
    echo "!! git stash/rebase/checkout rewrite the working tree under it."
    echo "!! On 2026-09-11 'git stash -u' unlinked a running chain's logs and"
    echo "!! took an uncommitted module with it. Two hours."
    exit 4
  fi
}

# ---------------------------------------------------------------- FIELD GUARD
#   assert_field <field.csv> <expected_total> <slice=count> [slice=count ...]
#
# THE FIELD IS THE ONE THING A RUN CANNOT RECOVER FROM GETTING WRONG. Every
# other mistake shows up as an error; the wrong field produces a complete,
# plausible, correctly-formatted table of results for a population nobody
# chose. On 2026-09-11 a walk-forward's member counts were read from a stale
# log belonging to a different run six hours earlier and reported as that
# run's field.
#
# This checks the FILE, before the chain spends a minute. l2walkfwd.load_field
# checks again after loading, against the same file. Both must agree.
assert_field() {
  local ff="$1"; shift
  local want_total="$1"; shift
  if [ ! -f "$ff" ]; then
    echo "!! HALT: field file does not exist: $ff"; exit 5
  fi
  FIELD_FILE="$ff" WANT_TOTAL="$want_total" WANT_SLICES="$*" \
  python3 - <<'PYF' || exit 5
import os, sys, collections, pandas as pd
ff = os.environ['FIELD_FILE']
want_total = int(os.environ['WANT_TOTAL'])
pairs = [x for x in os.environ['WANT_SLICES'].split() if x]
d = pd.read_csv(ff, low_memory=False)
if 'sid' not in d.columns:
    print('!! HALT: %s has no sid column' % ff); sys.exit(1)
if d.sid.duplicated().any():
    print('!! HALT: %s has %d duplicate sids' % (ff, int(d.sid.duplicated().sum())))
    sys.exit(1)
def lab(s):
    p = str(s).split('|')
    return p[0] if p[0] != 'B' else 'B-' + p[1]
got = collections.Counter(lab(s) for s in d.sid)
print('   field file %s: %d sids  %s'
      % (os.path.basename(ff), len(d),
         '  '.join('%s=%d' % (k, got[k]) for k in sorted(got))))
bad = []
if len(d) != want_total:
    bad.append('total %d, expected %d' % (len(d), want_total))
for p in pairs:
    k, _, v = p.partition('=')
    if got.get(k, 0) != int(v):
        bad.append('%s %d, expected %s' % (k, got.get(k, 0), v))
if bad:
    print('!! HALT: field file is not the field this chain was written for:')
    for b in bad:
        print('!!   %s' % b)
    print('!! Fix the field file or the chain, and do not run on a field')
    print('!! nobody chose. THE WRONG FIELD PRODUCES A COMPLETE, PLAUSIBLE TABLE.')
    sys.exit(1)
print('   pre-flight ok: field %s is %d (%s)'
      % (os.path.basename(ff), want_total, ' '.join(pairs)))
PYF
}
