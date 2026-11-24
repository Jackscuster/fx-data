#!/bin/bash
# STRIP NAMED PATHS FROM THE UNPUSHED COMMITS ONLY. Jack, 24 Nov, step 3.
#
#   bash code/chain/strip_unpushed.sh <path> [<path>...]
#
# WHY NOT filter-repo, WHICH JACK NAMED AS THE FIRST OPTION. He allowed "an
# equivalent that provably leaves every commit at or before origin/main
# untouched", and filter-repo is a worse fit here for two concrete reasons:
# it removes the `origin` remote as a safety measure, which would destroy the
# very reference this operation has to be verified against, and it expands and
# rewrites the whole object store of a 7 GiB repo to change 32 commits.
#
# WHAT THIS DOES INSTEAD, and why it is provable. It walks origin/main..HEAD
# oldest first and, for each commit, writes a NEW commit with the named paths
# removed from its tree and its parent remapped to the already-rewritten
# parent. The first commit's parent is origin/main's own unmodified commit
# object. So:
#   - no commit at or before origin/main is read for writing, only pointed at;
#   - no ref but `main` is ever updated;
#   - every author, committer, date and message is carried across verbatim.
# It prints the old -> new mapping, which is what goes into HANDOFF.
#
# IT IS NOT A FORCE PUSH AND CHANGES NOTHING ONLINE. The push that follows is a
# plain fast-forward, because the rewritten history still has origin/main as an
# ancestor -- which step 6 verifies before pushing.
set -euo pipefail
cd /Users/jackcuster/fx-data
[ $# -ge 1 ] || { echo "usage: strip_unpushed.sh <path> [<path>...]"; exit 2; }
PATHS=("$@")

BASE=$(git ls-remote origin refs/heads/main | cut -f1)
[ -n "$BASE" ] || { echo "cannot read origin/main"; exit 1; }
[ -z "$(git status --porcelain | head -1)" ] || { echo "REFUSED: tree is dirty"; exit 1; }
git merge-base --is-ancestor "$BASE" HEAD \
  || { echo "REFUSED: origin/main is not an ancestor of HEAD"; exit 1; }
[ "$(git rev-list --count --merges "$BASE"..HEAD)" = "0" ] \
  || { echo "REFUSED: the range contains merges; this script handles linear history only"; exit 1; }

START=$(git rev-parse HEAD)
N=$(git rev-list --count "$BASE"..HEAD)
echo "strip: base $(git rev-parse --short "$BASE"), $N unpushed commits, removing:"
for p in "${PATHS[@]}"; do echo "         $p"; done

MAP="$HOME/fx-data-logs/strip_map_$(date +%Y%m%d-%H%M%S).tsv"
printf 'old\tnew\tsubject\n' > "$MAP"
TMPIDX=$(mktemp -t stripidx)
trap 'rm -f "$TMPIDX" "$TMPIDX.lock"' EXIT

NEWPARENT="$BASE"
for C in $(git rev-list --reverse "$BASE"..HEAD); do
  rm -f "$TMPIDX" "$TMPIDX.lock"
  GIT_INDEX_FILE="$TMPIDX" git read-tree "$C"
  for p in "${PATHS[@]}"; do
    if GIT_INDEX_FILE="$TMPIDX" git ls-files --error-unmatch "$p" >/dev/null 2>&1; then
      GIT_INDEX_FILE="$TMPIDX" git update-index --force-remove "$p"
    fi
  done
  NEWTREE=$(GIT_INDEX_FILE="$TMPIDX" git write-tree)
  NEW=$(GIT_AUTHOR_NAME=$(git log -1 --format=%an "$C") \
        GIT_AUTHOR_EMAIL=$(git log -1 --format=%ae "$C") \
        GIT_AUTHOR_DATE=$(git log -1 --format=%aI "$C") \
        GIT_COMMITTER_NAME=$(git log -1 --format=%cn "$C") \
        GIT_COMMITTER_EMAIL=$(git log -1 --format=%ce "$C") \
        GIT_COMMITTER_DATE=$(git log -1 --format=%cI "$C") \
        git commit-tree "$NEWTREE" -p "$NEWPARENT" \
          -F <(git log -1 --format=%B "$C"))
  printf '%s\t%s\t%s\n' "$C" "$NEW" "$(git log -1 --format=%s "$C")" >> "$MAP"
  NEWPARENT="$NEW"
done

echo "strip: rewritten head $NEWPARENT"
git update-ref -m "strip oversized paths from unpushed commits" refs/heads/main "$NEWPARENT" "$START"
git reset --hard -q refs/heads/main
echo "strip: main now $(git rev-parse --short HEAD); map in $MAP"
echo "$MAP"
