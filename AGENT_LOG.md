# AGENT_LOG.md

Append-only record of work done by the Claude chat agent (claude.ai, Project "SlapBoxAlgos").
One entry per session. Entries are never edited or deleted. Corrections go in a new entry.

Each entry has two parts:
- **For Jack**: plain English. What was done, what was found, what is next.
- **For Code**: files touched, commands run, result paths, open items. Written so Claude Code
  can pick up without reading chat.

Rules this log follows: nothing to /tmp, nothing deleted or overwritten, numbers quoted from
files with the file path given, no money metrics in Layer 1.

---

## 2026-11-09 — Session 1: agent setup

### For Jack

Set up the chat agent to work directly on the repo instead of only writing prompts for Code.
Cloned `Jackscuster/fx-data` at commit `da5eddf` (8 Nov). Confirmed Python 3.13 with pandas and
numpy is available, so any script in `code/` can run here.

Ran the data sanity checks. `data/px28_h10.csv` passes exactly: EURUSD peak 1.601, USDCHF low
0.7296, 1999-01-04 to 2026-09-04. `data/px28.csv` is currently the 5pm series: 2002-09-24 to
2026-08-14, EURUSD peak 1.5991, USDCHF low 0.7209. That matches `code/build5pm.py` and is not a
problem, just recorded so nobody is surprised.

Two things are not working yet. The agent cannot push to GitHub (write access was refused by the
permission layer). Jack's Mac is linked but `~/Documents/fx-data` is not shared with the session.
Until one of those is fixed, anything the agent builds sits on the agent's machine only. Jack can
fix it by sharing the folder in the desktop app ("+" then "Add folder") or by approving GitHub
write access when prompted.

Agreed working rule: everything the agent does gets an entry in this file, and the entry is
mirrored to the project docs.

Next: read `HANDOFF_3.md` §16 and `FIXES.md` to get current on the backlog. No analysis work
started yet.

### For Code

- Agent checkout: `/home/claude/jackscuster/fx-data` (shallow clone, depth 1, HEAD `da5eddf`).
  Separate machine from Jack's Mac. Not pushed anywhere yet.
- Files created: `AGENT_LOG.md` (this file).
- Files modified: none.
- Commands run:
  - `git clone --depth 1 https://github.com/Jackscuster/fx-data`
  - pandas read of `data/px28.csv`, `data/px28_h10.csv`, `data/px28_5pm.csv` for shape, date
    range, EURUSD max, USDCHF min. Read-only, no outputs written.
- Results written: none.
- Open items:
  1. Push access or shared Mac folder needed before agent work can be committed.
  2. Agent has not yet read `HANDOFF_3.md` §16 or `FIXES.md`.
- Environment: Python 3.13.18, pandas 3.0.5, numpy 2.5.3. No test suite in repo; correctness is
  the assertions in `build.py` and `framework.py` per `CLAUDE.md`.

---

## 2026-11-09 — Session 1, task 1: external research on Layer 1 blueprints and NNFX combinations

### For Jack

Searched the web for two things: regime estimators that could improve Layer 1, and NNFX
indicator combinations with settings for Layer 2. Full write-up with sources:
`results/research/RESEARCH_2026-11-09_regime_blueprints_and_nnfx.md` (also mirrored to project
docs as `claude/RESEARCH_2026-11-09_regime_blueprints_and_nnfx.md`).

Layer 1: five families of method exist publicly. Three are already tested here and dead (HMM on
returns lost to a 200 SMA, swing structure failed OOS, indicator vote stacks are a worse version
of our two axes). Two are new: directional change / intrinsic time (built for FX, uses an absolute
threshold, never tried here) and Kalman slope-to-noise. Plus a panel correlation spike for the
unfinished crisis component. Three declared constructions proposed, ranked. Nobody outside has an
out-of-sample test of trend-predicts-trend; our own work is more rigorous than anything found.

Layer 2: the community publishes no league tables. The web gives candidate five-slot combos, not
verdicts. Six recurring combinations (N1 to N6) written down with our Pine file's own default
settings and line numbers. Proposal: run them as declared constructions alongside the 17.6M
funnel, as the Rule 10 reference. One spec note: Jack's leg 1 is stop 1x ATR, target 1.5x; VP's
canonical is the reverse. Jack's choice stands, recorded so comparisons to published NNFX
results are read correctly. Kijun-sen (VP's favourite baseline) is not in our 14 baselines.

Four sites refused the fetch from this machine (Forex Factory, forex-station, Medium, SSRN).
Jack can open them in Chrome.

### For Code

- Files created: `results/research/RESEARCH_2026-11-09_regime_blueprints_and_nnfx.md`
- Files modified: `AGENT_LOG.md` (this entry appended)
- Commands run: web searches and fetches only; read-only greps over `HANDOFF_3.md`,
  `HANDOFF_LAYER2.md`, `CLAUDE.md`, `JCs_NNFX_ALGO_V5_1.pine`, `code/`. No scripts executed,
  no data touched.
- Results written: the research markdown above. No CSVs.
- Open items:
  1. Jack to decide whether L1-R1 (directional change), L1-R3 (panel correlation crisis) get
     built. If yes, a Code prompt is needed; spec is in the research doc Part 1.3.
  2. Jack to decide whether N1 to N6 get registered as declared Layer 2 constructions in
     `claude/open-work-register.md` and run through `l2engine` ahead of the funnel.
  3. Kijun-sen baseline: one-line addition if N1 is to be run as the community runs it.
  4. Push access still blocked; this entry and the research doc are committed locally only.

---

## 2026-11-09 — Session 1, task 1 addendum: reconciled with HANDOFF.md 0f and the register

### For Jack

Read `HANDOFF.md` item 0f and `claude/open-work-register.md` as asked. The research doc was
written from older handoffs and two things in it were stale. Added an addendum to the research
doc (nothing rewritten): the real Layer 2 plan is the blind-label programme over 45,139 built
candidates, pre-flight 27 of 27 on 8 Nov, cloud run not launched, about $47 and 6.6 days, your
call. The N1 to N6 combos should be looked up among those candidates and tagged as declared
reference rows in the report stage, not run separately. The Layer 1 proposals stand but must be
built on the 5pm series, confirmed on 2016 to 2020 only with 2021 onward sealed, and judged by
whether routing mode C on the new axis beats routing on `shape2`.

### For Code

- Files modified: `results/research/RESEARCH_2026-11-09_regime_blueprints_and_nnfx.md`
  (addendum appended), `AGENT_LOG.md` (this entry).
- Files created: none.
- Commands run: read-only greps over `HANDOFF.md`; `project_read` of
  `claude/open-work-register.md`. No scripts, no data.
- Open items (replace items 1 to 3 of the previous entry):
  1. Jack: cloud launch go / no-go (0f launch lines).
  2. If go: short Code prompt to look up N1 to N6 slot signatures in
     `results/refit_candidates_full.csv` and print their year-6 records as a declared-reference
     block in `l2refit.py --stage report`. No candidate additions before launch.
  3. L1-R1 directional-change axis on `data/px28.csv`, 2016 to 2020 confirm, 2021+ sealed, then a
     routing comparison against `shape2` TRENDING for mode C. Timing is Jack's.
  4. Push access still blocked; three local commits.

---

## 2026-11-09 — Session 1, task 1 correction

### For Jack

Two claims in the research doc were wrong and you caught them. Stop and target multiples are
tuned per strategy (`code/l2tune.py` lines 73 to 77), not fixed at 1x / 1.5x; I quoted a stale
handoff. Ichimoku was built and gauntlet-tested (`code/l2ind.py` line 300, `GAUNTLET.md` line
1510), so the Kijun-sen note is withdrawn. Correction appended to the research doc. Cause: I read
`HANDOFF_LAYER2.md` and `HANDOFF_3.md` before `HANDOFF.md` and project memory. Order fixed for
every future session: project memory, `claude/open-work-register.md`, `HANDOFF.md`, then the
older files.

### For Code

- Files modified: `results/research/RESEARCH_2026-11-09_regime_blueprints_and_nnfx.md`
  (correction appended), `AGENT_LOG.md`.
- Commands run: greps over `code/l2tune.py`, `code/l2ind.py`, `code/l2lib.py`, `GAUNTLET.md`;
  memory reads. No scripts, no data.
- Open items: unchanged from the previous entry except item 3 (Kijun-sen) withdrawn.

---

## 2026-11-09 — Session 1, task 2: one-hour research pass, regime taxonomies and NNFX catalog

### For Jack

Full write-up: `results/research/RESEARCH_2026-11-09_part2_regime_taxonomies_and_nnfx_catalog.md`
(mirrored to project docs under `claude/`).

Layer 1: eight regime families are in use anywhere. Six are our shape and activity axes under
other names or a direction axis we dropped on evidence. Two are new to us: directional change
(absolute-threshold, scale-free trend measure, never done on daily FX by anyone) and the panel
turbulence index plus Roll illiquidity as crisis witnesses. Verdict: keep trend / chop / crisis,
add no states, change how trend and crisis are estimated. The academic record (21,195 rules on
30 currencies, nothing significant on majors since the mid-1990s; trend persistence declining
toward zero) matches our 2016-2020 finding.

Layer 2: there is no verified NNFX combination anywhere. Eleven named combinations catalogued
with settings where stated and a verifiability grade. Checked against our 45,139 candidates: the
two most-shared community algos (N1 SSL+TDFI+WAE, N2 DiDi+DSPO) are not in the list at all; four
others are partly present. Running N1 to N6 as declared constructions is 6 × 5 windows × 72.8 s,
about 36 minutes on the Mac. Kijun-sen baseline needed for N1 (one line).

### For Code

- Files created: `results/research/RESEARCH_2026-11-09_part2_regime_taxonomies_and_nnfx_catalog.md`
- Files modified: `AGENT_LOG.md`
- Commands run: web searches and fetches; read-only pandas pass over
  `results/refit_candidates_full.csv` (slot vocabularies, counts per community combo); two
  public NNFX repos cloned read-only to `/home/claude/ext/` on the agent machine for README
  inspection (not part of the repo). No scripts in `code/` executed, no data touched.
- Results written: the research markdown. No CSVs.
- Open items (supersede the earlier list):
  1. Jack: cloud launch go / no-go (0f).
  2. Declared Layer 2 constructions N1 to N6: add `kijun_baseline` to `code/l2ind.py`
     (pattern `baseline_sma`, lines 418 to 420), build six sids in the `refit_candidates_full.csv`
     format, run `l2refit.py --stage tune/marks/report` on the five 0f windows with suffix
     `_declared6`, report their year-6 records beside the smoke books. ~36 min Mac.
  3. Layer 1 candidate constructions, in order: (a) directional-change shape score on
     `data/px28.csv`, thresholds 0.5 / 1.0 / 1.5 × 20-day vol declared, standard battery, then
     mode C routed on it vs `shape2` TRENDING; (b) panel turbulence index and Roll measure as
     crisis witnesses against `events.py` dates, forward window, sub-period split.
  4. Layer 3 routing tests on existing states: activity WEAK as a no-trade filter; per-currency
     shape agreement across the 7 pairs each currency sits in.
  5. Push access still blocked; commits local only.

---

## 2026-11-09 — Session 1, correction 2 (late evening)

### For Jack

I described the 45,139 as luck-exposed. Wrong. The blind-label programme removes picking
entirely: everyone trades, the grade is reported and never used, nulls run. N1 to N6 do not
"test the search." Their only value is as an outside reference row: what the NNFX community
actually trades, on our walk, beside our pooled book. Cheap, informative, not a verdict.

### For Code

- Files modified: `AGENT_LOG.md`. Research part 2 section 2.4 item 2 is to be read with this
  correction; the file is left as written.
- Open item 2 (declared six) stands, reframed as a reference row, not a test of the search.

---

## 2026-11-09 — Standing rule (Jack, 23:34 EST)

The chat agent is not a decision maker. Dedicated Layer 1 and Layer 2 chats own their work. The
agent adds files; it never edits, deletes, or overwrites anything that exists in the repo (code,
data, results, handoffs, register). Anything that would touch another chat's work is proposed to
Jack and does not happen until he says so. This rule outranks any task given to the agent.
