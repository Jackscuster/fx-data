#!/bin/bash
# LAUNCH A CHAIN: SNAPSHOT IT, GUARD IT, APPROVE IT, WATCH IT.
#   bash code/chain/launch.sh <driver.sh> --approved <commit hash>
#
# VERSIONED. launch.sh, stop_chain.sh, chainlib.sh, chainwatch.sh, bin/pkill and
# every chain driver live in code/chain/ so they are reviewable in a diff like
# any other code. Logs stay in ~/fx-data-logs, outside the repo, so a git
# operation cannot touch a running chain's log.
#
# SIX GUARDS, each one a rule this project broke in the week of 16-18 Nov.
#
# 1 FROZEN SNAPSHOT. code/ and the driver are copied to
#   ~/fx-data-runs/<driver>-<stamp>/ and the chain executes ONLY from there;
#   data/, results/ and the rest are symlinked back to the repo so output still
#   lands in one place. An edit in ~/fx-data cannot reach a running chain.
#   On 18 Nov an edit to l2r2book.py mid-run cost the books stage: macOS
#   multiprocessing SPAWNS, so the pool's workers re-imported the edited module
#   while the parent held the old one. Launch REFUSES on a dirty working tree,
#   because a snapshot that is not a commit cannot be reviewed.
#
# 2 PROCESS GROUP. The chain is its own process-group leader and the pgid is
#   registered. stop_chain.sh is the only sanctioned way to stop it.
#
# 3 DISK. l2stagecheck refuses unless every stage declares its need and the
#   volume holds the sum plus 2 GB.
#
# 4 DELIVERABLE AND ETA. Both declared in the driver or no launch.
#
# 6 REVIEW, AS AMENDED BY JACK ON 20 NOV. Approval is needed only for code
#   that changes WHAT is computed. Re-running an already-approved pipeline on
#   another mode, sharding, scheduling, KPI tables and report generation launch
#   without approval. A driver DECLARES which it is, in its own header:
#       # approval = required           <why>
#       # approval = none               <why it computes nothing new>
#   The declaration sits in the diff next to the ckpt/needs/disk lines for the
#   same reason those do: the claim and the behaviour cannot drift apart, and
#   "this computes nothing new" is a statement Jack can check against the diff.
#   A driver with NO approval line still needs --approved <hash> == HEAD, so
#   every driver written before the amendment behaves exactly as it did.
set -u
L="$HOME/fx-data-logs"
R="/Users/jackcuster/fx-data"
RUNS="$HOME/fx-data-runs"
D="${1:?launch: pass the driver}"; shift || true
[ -f "$D" ] || { echo "launch: no such driver $D"; exit 2; }

APPROVED=""
while [ $# -gt 0 ]; do
  case "$1" in
    --approved) APPROVED="${2:-}"; shift 2;;
    *) shift;;
  esac
done

HEAD=$(cd "$R" && git rev-parse HEAD)
DIRTY=$(cd "$R" && git status --porcelain | head -5)

# ---- GUARD 1a: the tree must be committed, or the snapshot is unreviewable
if [ -n "$DIRTY" ]; then
  echo "launch: REFUSED -- the working tree has uncommitted changes, so the snapshot"
  echo "        would not correspond to any commit Jack could review:"
  echo "$DIRTY" | sed 's/^/          /'
  exit 4
fi

# ---- GUARD 6 (amended 20 Nov): approval only for code that changes WHAT is
# computed. The driver declares which it is; absent a declaration, a hash is
# still required, so nothing written before the amendment changes behaviour.
APPROVAL_DECL=$(grep -oE '^#[[:space:]]*approval[[:space:]]*=[[:space:]]*[a-zA-Z-]+' "$D"   | head -1 | sed 's/.*=[[:space:]]*//' | tr '[:upper:]' '[:lower:]')
APPROVAL_WHY=$(grep -E '^#[[:space:]]*approval[[:space:]]*=' "$D" | head -1   | sed 's/^#[[:space:]]*approval[[:space:]]*=[[:space:]]*[a-zA-Z-]*[[:space:]]*//')
if [ "$APPROVAL_DECL" = "none" ]; then
  echo "launch: guard 6 waived by the driver's own declaration -- "approval = none""
  [ -n "$APPROVAL_WHY" ] && echo "        reason: $APPROVAL_WHY"
  echo "        commit $HEAD (the tree is still committed and snapshotted; guard 1a stands)"
  if [ -n "$APPROVED" ]; then
    case "$HEAD" in
      "$APPROVED"*) : ;;
      *) echo "launch: REFUSED -- a hash was passed ($APPROVED) and it is not HEAD ($HEAD)."; exit 6;;
    esac
  fi
else
  if [ -z "$APPROVED" ]; then
    echo "launch: REFUSED -- no --approved <hash>, and this driver does not declare"
    echo "        "# approval = none". HEAD is $HEAD"
    echo "        Guard 6: code that changes WHAT is computed needs Jack's hash. If this"
    echo "        driver only re-runs an approved pipeline on another mode, or is sharding,"
    echo "        scheduling, a KPI table or report generation, declare it in the driver:"
    echo "            # approval = none    <why it computes nothing new>"
    echo "        Print the stage table with:"
    echo "            python3 $R/code/l2stagecheck.py chain $D"
    exit 5
  fi
  case "$HEAD" in
    "$APPROVED"*) : ;;
    *) echo "launch: REFUSED -- approved hash $APPROVED is not HEAD ($HEAD)."; exit 6;;
  esac
fi

# ---- GUARDS 3 and 4 (and the five-minute rule, and the dependency graph)
if ! python3 "$R/code/l2stagecheck.py" chain "$D"; then
  echo "launch: REFUSED -- see the chain guard above"; exit 3
fi

MARKER=$(grep -oE 'say "[^"]*COMPLETE"' "$D" | tail -1 | sed 's/^say "//; s/"$//')
[ -n "$MARKER" ] || { echo "launch: cannot determine the final marker"; exit 7; }
DELIV=$(grep -oE '^#[[:space:]]*deliverable[[:space:]]*=[[:space:]]*.*' "$D" | head -1 | sed 's/.*=[[:space:]]*//')
ETAMIN=$(grep -oE '^#[[:space:]]*eta[[:space:]]*=[[:space:]]*[0-9]+' "$D" | head -1 | grep -oE '[0-9]+$')

# ---- GUARD 1b: the frozen snapshot
STAMP=$(date +%Y%m%d-%H%M%S)
SNAP="$RUNS/$(basename "$D" .sh)-$STAMP"
mkdir -p "$SNAP"
cp -R "$R/code" "$SNAP/code"
cp "$D" "$SNAP/driver.sh"
for e in "$R"/*; do
  b=$(basename "$e")
  [ "$b" = "code" ] && continue
  ln -s "$e" "$SNAP/$b" 2>/dev/null
done
ln -s "$R/.git" "$SNAP/.git" 2>/dev/null
echo "$HEAD" > "$SNAP/COMMIT"
echo "launch: snapshot $SNAP (commit $HEAD)"

PL="$HOME/Library/LaunchAgents/com.jackcuster.fxchainwatch.plist"
[ -f "$PL" ] || { echo "launch: watchdog agent missing at $PL"; exit 8; }
launchctl list 2>/dev/null | grep -q fxchainwatch || launchctl load "$PL"

# ---- GUARD 2: its own process group, launched from the snapshot
# FX_CHAIN_LIB points at the SNAPSHOT's chainlib, so a driver cannot source the
# repo copy and so pick up an edit made after launch.
export FX_CHAIN_LIB="$SNAP/code/chain/chainlib.sh"
nohup python3 -c "
import os, sys
os.setsid()
os.execvp('bash', ['bash', sys.argv[1]])
" "$SNAP/driver.sh" > /dev/null 2>&1 &
P=$!; disown
sleep 2
PGID=$(ps -o pgid= -p "$P" 2>/dev/null | tr -d ' ')
PGID=${PGID:-$P}

printf 'CHAIN_PID=%s\nCHAIN_PGID=%s\nCHAIN_DRIVER="%s"\nCHAIN_LOG="%s/batch1.log"\nCHAIN_MARKER="%s"\nCHAIN_START=%s\nCHAIN_DELIVERABLE="%s"\nCHAIN_ETA_MIN=%s\nCHAIN_SNAPSHOT="%s"\nCHAIN_COMMIT="%s"\n' \
  "$P" "$PGID" "$(basename "$D")" "$L" "$MARKER" "$(date +%s)" "$DELIV" "${ETAMIN:-0}" "$SNAP" "$HEAD" > "$L/chain_current"
rm -f "$L"/.nodeliv_notified_* "$L"/.eta_notified_* "$L/CHAIN_HALTED" 2>/dev/null
grep -c '!!!.*FAILED' "$L/batch1.log" 2>/dev/null | head -1 > "$L/.chain_failcount"

echo "launch: pid $P, process group $PGID; stop it ONLY with: bash $R/code/chain/stop_chain.sh"
echo "launch: deliverable $DELIV, eta ${ETAMIN:-?} min, marker \"$MARKER\""
sleep 58
if kill -0 "$P" 2>/dev/null; then
  echo "$(date '+%F %T') LAUNCHED $(basename "$D") pid $P pgid $PGID commit $HEAD (alive after 60 s, watchdog armed)"
elif grep -qF "$MARKER" "$L/batch1.log" 2>/dev/null; then
  echo "$(date '+%F %T') LAUNCHED $(basename "$D") -- already FINISHED inside 60 s"
else
  echo "$(date '+%F %T') !!! $(basename "$D") DIED within 60 s -- the watchdog will report it"; exit 1
fi
