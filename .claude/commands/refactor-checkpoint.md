---
description: Validate and repair the most recently completed refactor phase against its Definition of Done (Opus code review, then tests), then audit and repair the next phase's plan without executing it; retires the refactor when its last phase passes
argument-hint: [<refactor>] [phase]
---

# /refactor-checkpoint

Validate that the most recently completed phase satisfies its Definition of Done before
the refactor advances, fixing every in-scope defect rather than reporting it. Run this
after every phase, before the next `/refactor-next`. When the phase passes and more phases
remain, it then **fixes ahead**: audits the next phase's plan against the repaired tree
and corrects the plan in place, without implementing any of it. When the phase that
passes is the refactor's last, this also retires the refactor — mirroring
`/todo-checkpoint`.

**Never commit, stash, reset, discard, or delete user work**, and never `git checkout` a
path — the phase's work is normally uncommitted, and the tree often also carries earlier
phases' uncommitted work and unrelated operator edits. Restore a probe by editing back.

---

## What to do

### 0 — Select the refactor

`.local/REFACTOR.<kebab>.md` is a refactor's tracking file; `.local/REFACTOR.md` is
the **index**.

- **First argument is a kebab title** (not a bare number) — use
  `.local/REFACTOR.<arg>.md`; a second argument, if present, is the phase number.
- **First argument is a bare number, or no argument** — resolve the refactor from
  the `.local/REFACTOR.md` index: the single row with Status `planning` or
  `active`. None → "no refactor in progress"; more than one → list them and require
  the kebab title. A bare-number argument is then the phase.
- Back-compat: if `.local/REFACTOR.md` contains `## Phase Map`/`## Intent` it is the
  old single-file format — stop and tell the user to migrate to
  `.local/REFACTOR.<kebab>.md` + an index.

Everywhere below, `REFACTOR.<kebab>.md` is the resolved tracking file — never the index.

### 1 — Identify the phase being validated

If a phase number was given (see step 0), validate that phase.

Otherwise read `.local/REFACTOR.<kebab>.md` `## Session Log` and find the most recent row whose
Status is `Complete` or `Partial`. Rows carrying any other Status (`Review`,
`Checkpoint failed`) record bookkeeping, not a phase run — skip past them rather than
treating the newest row as the target. Note: phase number + name, model used, and which
of the two statuses it carries.

If that row is `Partial`: report "Most recent phase is partial — checkpoint
cannot run until the phase is fully complete. Finish the phase first." Stop.

If no such row exists: report "No completed phases found in the session log." Stop.

Read the repository's conventions file, the tracking file's §Intent, §Hard Constraints,
§Definition of Done and §Design Map (when present), the validated phase's section, and the **next** phase's section
(step 7 audits it). Also collect every item earlier rows deferred ("deferred to Phase
N") — a deferral aimed at the validated phase is part of its scope.

**Attribute the change set before judging it.** `**Baseline:**` is often a commit that
predates earlier phases' still-uncommitted work, so `git diff <baseline>` can include
another phase's files. Use **Files to modify** and the Session Log to separate this
phase's changes from earlier phases' and from unrelated operator edits; judge earlier
phases' files only where this phase touched them, and leave unrelated changes alone.

### 2 — Review the change set in an Opus subagent

This runs **before** the tests, not after. Adjudicating a finding changes code, and the
test run has to validate the tree that will actually be committed — reviewing after a
green test run means the last thing that touched the code was never tested.

**How much to review depends on `**Reviewed:**` in the phase header.** `/refactor-next`
writes it after reviewing and adjudicating the phase, so the bulk of the defects are
normally already gone by the time you get here.

- **It holds a SHA** — review only what changed since it: `git diff <reviewed>` plus
  untracked files. That covers operator hand-edits and anything you adjudicated in an
  earlier checkpoint round. **If that delta is empty, skip the review** and mark the row
  `N/A — reviewed at <sha>, no changes since`. Re-reviewing an unchanged tree buys
  nothing and costs an Opus pass.
- **It is absent or `dirty`** — run the full review over the phase's whole change set.
  Absent means the phase predates this workflow, ran under Codex, or was done by hand.

Skip regardless when the phase produced no changes at all, and say so in the report rather
than spawning an agent to review nothing. Do **not** skip a documentation-only phase:
prose that reads as fact and is wrong is exactly what the test suite cannot catch.

**One review round per command. Do not re-spawn a reviewer over your own fixes** — every
fix is new code, so "loop until clean" has no terminating condition. The bound is
structural: `/refactor-next` reviews the phase, this command reviews the fixes that came
out of it. If a round returns only Low wording findings, apply them and stop.

**If `.local/REVIEW.md` already exists, do not spawn a review.** The operator runs
`/review` by hand; a second pass would duplicate work and overwrite their file. Go
straight to adjudication with the findings already there.

When you do spawn, it must be a **new** subagent — never the one that implemented the
phase, and never one asked to re-check its own earlier findings.

Otherwise gather the phase's change set exactly as step 4 does — `**Baseline:**` from the
phase header, `git diff <baseline>`, plus any untracked files in `git status --porcelain`
that this phase plausibly created — and spawn **one `general-purpose` subagent on
`model: opus`, in the foreground**, instructing it to:

- review **only** that change set, reading the changed files in full plus whatever
  surrounding code it needs to judge them (a finding about new code usually depends on
  code that did not change);
- read the repository's conventions file and any ADR governing the touched code, and
  cite for each finding which governing intent was checked — or state that none was
  found, rather than implying the check passed;
- quote §Hard Constraints and the phase's own requirements inline in the prompt, so the
  reviewer can catch a violation the test suite cannot;
- cover correctness, regressions, security, scope and contract violations, **lost
  behavior or comments** (deleted or reworded intent, a dropped branch or log line),
  missing coverage — including the absence of a guard over any duplicated list,
  constant or contract the phase edited in more than one place — placement against
  §Design Map (quote it inline when the tracking file has one: a duplicated helper,
  code in the wrong module, a copy made to stay inside **Files to modify**), and
  inaccurate completion claims (DoD boxes, Step Index marks, Session Log notes);
- classify every finding as **in scope** or **out of scope**, giving the reason for the
  latter (see item 2 of the adjudication below), and never park an in-scope gap as a
  "residual";
- **report only — never edit code.** The reviewer has no authority to change the tree;
  adjudication is yours;
- write findings to `.local/REVIEW.md` in the format `/review` produces, and return a
  count by severity.

Tell it plainly that an empty report is an acceptable and useful outcome, and that it
should note where static analysis alone left residual risk instead of padding the count.
Do not paste `.local/REFACTOR.<kebab>.md` or the plan file into its prompt — extract the
sections it needs, the same way `/refactor-next` does.

**Then adjudicate every finding yourself.** The reviewer's report is a claim, exactly as
the phase's own Session Log note is:

1. **Verify each finding against the tree before acting on it.** Confirm the cited lines
   say what the finding says they say. A finding that does not reproduce is dismissed
   with that evidence stated — not applied because it is small and already written down.
2. **Apply what survives**, smallest correct change first. Where the proposed fix would
   contradict an ADR or delete the only place a decision was written down, apply the
   architecturally correct fix instead and say why the proposed one was wrong.

   **"Residual" is not a third outcome.** Every observation — including ones you or
   the reviewer would call a nit, a residual, pre-existing, or out of scope — ends as
   *applied*, *dismissed with evidence*, or *out of scope with a scope reason*. A gap is
   **in scope** when it concerns code, tests or docs this phase touched, or a contract
   this phase created or extended — for example, a comment in a touched file requiring
   two lists to stay aligned, with no test enforcing it after the phase edited both.
   **Out of scope** requires that the fix would land only in files and behavior the
   phase did not touch and no plan item assigned to it; record those in the Session Log
   row and the final report, never as silent "residual risk". Seen 2026-10-09: a
   checkpoint logged "no cross-file STAGE_ORDER vs SCHEDULE_STAGE_KEYS parity test" as
   an out-of-scope residual although the phase had just edited both lists; a follow-up
   pass added the guard in a dozen lines and proved it red.
3. **Prove new guard tests actually guard.** If a finding adds a test, mutate the
   production code it claims to protect, watch the test fail, restore **by editing back —
   never `git checkout`**, which would discard the phase's uncommitted work — and confirm
   green. A guard that was never seen red is not evidence.
4. **Do not quietly patch a structural failure.** A finding that reveals a §Hard
   Constraint violation, a false `Complete` mark, or work outside **Files to modify** is
   a checkpoint FAIL: it belongs in the `### Corrections` section in step 6, not in a
   silent fix. Ordinary defects — a missing assertion, an unhandled error, dead code —
   are fixed here and do not fail the checkpoint.
5. **Record the adjudication in the Session Log** as one row, written as terse decision
   lines: what was applied, what was dismissed and on what evidence, and the red/green
   result of any guard proven in item 3. Do not narrate how you investigated — a
   repository hook rejects Session Log rows that recount past-tense discovery.
6. **Delete `.local/REVIEW.md` once every finding is adjudicated** — applied or dismissed
   with evidence. It is a punch-list, not an archive; the durable record is the Session
   Log row and the code itself.

Any code you changed here is part of the change set from this point on. Steps 3 and 4
judge the tree as it now stands, not as the phase left it.

### 3 — Run tests

Run the narrowest relevant checks first — the packages and test files the phase
touched — so a failure points at its cause. Then read `.local/REFACTOR.<kebab>.md`
`## Test Command` and run it exactly as written.

If tests fail:

- Report which tests failed and the relevant output.
- Mark the checkpoint **FAILED — tests**.
- Skip the remaining checks, but still run the **On FAIL** handling in step 6. The
  corrections written there are the only thing the retry reads; stopping outright
  sends `/refactor-next` back in with the same input that just failed its tests.

### 4 — Review the diff

Everything from here on is judged against the code. The Session Log note and the Step
Index marks were written by the agent under validation; they are claims, not evidence.
Reviewing a phase through its own account of itself cannot catch work that is plausible
and wrong, which is the failure this step exists to find.

Read `**Baseline:**` from the phase's header block in `.local/REFACTOR.<kebab>.md`.

If it is `—`, absent, or not a valid SHA: mark the diff review **WARN — degraded**, read
the files named in the phase's **Files to modify** line in full instead, and say plainly
in the report that the review ran without a diff. Do not quietly substitute the weaker
check.

With a baseline, gather the change set:

```bash
git diff --stat <baseline>
git diff <baseline> -- <files from the Files to modify line>
git status --porcelain
```

`git diff` does not show untracked files. Any `??` entry in `git status --porcelain`
that this phase plausibly created is part of its work — read those files in full. A
phase whose main deliverable is a new file diffs to nothing otherwise, and passes on an
empty change set.

Assess three things against what you read:

**Scope** — did the phase modify anything outside its **Files to modify** line? Judge
each such file:

- **A recorded placement edit** — a `placement:` entry in the phase's Session Log note
  and a §Design Map Placement row, consistent with the Design Map (a shared helper
  extended or a constant exported instead of copied) — is correct work. WARN, and widen
  **Files to modify** to include it. Failing it would teach the next phase to copy code
  to stay inside the list.
- **A source file with no recorded reason, or a placement that contradicts the Design
  Map**: FAIL.
- **Docs and tests**: WARN.

Say which happened: the agent went off-plan, or the plan was wrong about what the change
requires. The correct fix for the second is to widen **Files to modify**, not to revert
working code.

**Fidelity** — for each `### Step N.x` marked `Complete`, is there something in the change
set that implements it? A step marked `Complete` with nothing behind it is a false
completion claim: FAIL, and name the step. Note the converse too — substantive changes in
the diff that no step asked for.

**Hard Constraints** — check the change set against every item in `.local/REFACTOR.<kebab>.md`
§Hard Constraints. A violation is FAIL even when tests pass: those constraints are written
down precisely because the failures they describe are ones the test suite does not catch.

### 5 — Check each Definition of Done criterion

Read the phase's `### Definition of Done` checklist from `.local/REFACTOR.<kebab>.md`.
For each checklist item, assess PASS or FAIL with a brief note. A ticked box is a claim,
not evidence:

- **Re-run every command a DoD item names**, including build-tagged, integration,
  browser or lint commands that `## Test Command` does not cover.
- **A command must demonstrably exercise something.** A `-run` pattern that matches no
  test, or a grep that cannot match, passes vacuously — FAIL that item and fix the
  command. Seen 2026-10-09: a DoD's `go test -run Playwright` matched zero test names
  and had been reported green.
- **Record validation that cannot run here honestly** — no Docker, no browser, or a
  step needing live, external, privileged or destructive access the plan gates behind
  operator approval. Report it as "not run: <reason>", never as PASS, and do not take
  a gated action to make the item pass.

Then check these structural criteria regardless of the phase:

**Code quality** — judge the change set from step 4, not the phase's description of it.
Is the code clean and consistent with the repository's conventions file (`AGENTS.md` or
`CLAUDE.md` — follow the pointer if one delegates to the other)? Any obvious hacks or
untracked workarounds? FAIL if yes.

**Technical debt** — Any `// TODO` or `// FIXME` markers introduced by this phase? If
so, are they explicitly tracked in the session log or a follow-up phase? Untracked = FAIL.

**Documentation** — Based on what changed, assess whether any of these needed updating:
`README.md` (flags or env vars), `AGENTS.md` (architecture contracts), `doc.go` in
affected packages, `docs/openapi.yaml` (API behavior). FAIL if a relevant doc was skipped.

**Test coverage** — Were new or updated tests added for changed logic? If behavior changed
and no tests were touched, report WARN (not FAIL — existing coverage may be sufficient,
but flag it).

**ADRs** — If any phase DoD item explicitly requires an ADR, verify the file exists in
`docs/decisions/`. FAIL if required and missing. N/A if not required.

### 6 — Record the outcome

Decide the overall result from steps 2–5 — PASS, FAIL or WARN, as defined by the report
in step 8 — and update the tracking file to match. Tick a DoD box only for an item
verified in this run, and mark a Step Index or Phase Map row `Complete` only when the
implementation genuinely satisfies it.

**On FAIL** — the phase is not complete, and the tracking file must say so.

1. Set the phase's row in `## Phase Map` back to `In progress`, and set any Step Index
   rows whose work failed validation back to `In progress`. In `.local/REFACTOR.md`,
   set this refactor's index Status to `blocked`.

2. Write a `### Corrections` section into the phase's own section in
   `.local/REFACTOR.<kebab>.md`, immediately before its `### Definition of Done`. This is
   the only channel that reaches the retry: `/refactor-next` builds its prompt out of the
   phase section and never reads the Session Log, so a finding recorded only in the log
   is a finding the next run is guaranteed not to see — it would receive the same input
   that just produced the failure.

   ```markdown
   ### Corrections

   <!-- Written by /refactor-checkpoint on YYYY-MM-DD. Mandatory scope on the next
        /refactor-next run. Removed by the checkpoint once it passes. -->

   - [ ] C1 — `path/to/file.go`: what is wrong, and what the correct end state is.
   ```

   One item per finding, each naming a file and the condition that would satisfy it.
   "Tests fail" is not a correction — the correction is the specific thing that must
   become true. If a `### Corrections` section already exists from an earlier failed
   checkpoint, replace it wholesale rather than appending: items that no longer
   reproduce have been fixed, and carrying them forward sends the next run to redo
   work that is already done.

3. Append a Session Log row:
   `| YYYY-MM-DD | Phase N — [name] | [model] | Checkpoint failed | [what must be fixed, brief] |`

4. List exactly what must be fixed. Re-run `/refactor-next <kebab>` — it picks up the
   Corrections section — then `/refactor-checkpoint <kebab>` again.

**On WARN:** the phase can advance; call out what to revisit later. Apply the On PASS
bookkeeping below.

**On PASS or WARN**, append one Session Log row, as terse decision lines:
`| YYYY-MM-DD | Phase N — checkpoint | [model] | Review | PASS/WARN; [exact validation commands and results, including any "not run: <reason>"] |`.
Its Status is `Review`, so a later checkpoint skips it when looking for the phase row.

**On PASS:** confirm every row in the phase's `### Step Index` and its Phase Map row are
marked `Complete` in `.local/REFACTOR.<kebab>.md`. If either was missed, update it now.
Delete the phase's `### Corrections` section if it has one — it has done its job, and one
left in place is mandatory scope on any future re-run of the phase.

Then check whether this was the **last** phase — every row in `## Phase Map` now
`Complete`:

- **More phases remain.** In `.local/REFACTOR.md`, update this refactor's Phases column
  to `<completed> / <total>` (and Status to `active` if it was still `blocked`). Then
  fix ahead (step 7).

- **This was the last phase — retire the refactor** (mirrors `/todo-checkpoint`):

  1. Confirm no `### Corrections` section survives anywhere in the file.
  2. Remove this refactor's row from `.local/REFACTOR.md` entirely. Do not leave a
     `complete` row — the index holds live work only.
  3. Archive the tracking file and its sidecars — `.local/` is gitignored, so a plain
     move:

     ```bash
     mkdir -p .local/completed
     mv .local/REFACTOR.<kebab>.md .local/completed/REFACTOR.<kebab>.completed.md
     # move any sidecars alongside it, same rename:
     #   .local/REFACTOR.<kebab>.RUNNOTES.md -> .local/completed/REFACTOR.<kebab>.RUNNOTES.completed.md
     # and delete a spent Codex prompt:
     #   rm -f .local/CODEX-PROMPT.<kebab>.md
     ```

  4. Report the refactor complete and retired. If any phase's Definition of Done required
     an ADR, remind the user to run `/adr` now — the archived file in `.local/completed/`
     is still the reference for it.

### 7 — Fix ahead: audit and repair the next phase's plan

Run this only when the result is PASS or WARN **and** more phases remain. Skip it on
FAIL — the phase goes back to `/refactor-next`, so the next phase has no settled
baseline yet — and on retirement, when nothing is ahead. Say which in the report.

The next phase's plan was written before any of the work it builds on existed. Earlier
phases and this checkpoint's own fixes move files, rename symbols and establish
contracts the plan could only guess at, and `/refactor-next` hands that plan to a
subagent verbatim. A stale instruction reaches the subagent as fact; correcting it here
costs a plan edit, while correcting it after the run costs a failed checkpoint.

1. **Treat the repaired working tree as the next phase's baseline**, including every fix
   applied in steps 2–5.
2. **Verify every assumption in the next phase's section** against the current code,
   dependency versions and APIs, the repository's conventions file, and the contracts
   earlier phases established:
   - every path in **Files to modify** exists, or is marked new;
   - every cited line, function, flag, target, field or config key still exists and
     says what the plan says it says;
   - every fact the phase will write into code or docs (defaults, field shapes, ordering,
     operational steps) matches the code that defines it — read the code rather than
     trusting an earlier phase's summary;
   - every item earlier phases deferred to this phase is present in its steps;
   - everything new the phase will add has a §Design Map Placement row that still
     holds against the current tree — including helpers earlier phases created that it
     should now reuse instead of copying;
   - every DoD command works as written and matches something: dry-run it where that is
     non-mutating (`make -n`, `go test -list`, a grep), and treat a zero match as a
     broken command.
3. **Repair the plan in place**: dependencies, scope, **Files to modify**, ordered steps,
   tests, behavioral deltas, safety and authorization gates, the Definition of Done, and
   the session bookkeeping instructions. Delete stale, impossible or contradictory
   instructions rather than annotating them. When a corrected fact is repeated elsewhere
   — §Hard Constraints, later phases, ADR notes — correct every copy, or the stale one
   wins on the run that reads it. Edit section by section; never rewrite the whole
   tracking file, since `.local/` is gitignored and a bad write cannot be recovered.
4. **Do not execute the next phase.** Leave its Phase Map row and every Step Index row
   `Not started`, leave `**Baseline:**` and `**Reviewed:**` unset, and change no source,
   test, doc or config file on its behalf. The reverse holds too: do not pull next-phase
   work back into the phase you just validated.
5. **Run non-mutating consistency checks** over the revised plan and tree where useful:
   phase statuses, `git status --short` unchanged apart from your step 2–5 fixes, and
   `git diff --check`.
6. **Append a Session Log row**, as terse decision lines:
   `| YYYY-MM-DD | Phase N+1 — plan audit | [model] | Review | [corrections made]; Phase N+1 remains Not started |`.
   If the audit finds nothing to correct, record that instead.

### 8 — Report

Print the checkpoint report:

```text
═══════════════════════════════════════
 Checkpoint — <kebab> — Phase N — [name]
═══════════════════════════════════════
 Code review      PASS / WARN / N/A — [N findings: A applied, D dismissed, O out of scope]
 Tests            PASS / FAIL
 Diff review      PASS / FAIL / WARN — [scope | fidelity | constraints]
 Code quality     PASS / FAIL — [note]
 Technical debt   PASS / FAIL — [note]
 Documentation    PASS / FAIL — [list]
 Test coverage    PASS / WARN — [note]
 ADRs             PASS / FAIL / N/A
 DoD checklist    PASS / FAIL — [N of M items met, K not run]
 Next-phase plan  REPAIRED / NO CHANGES / SKIPPED — [N corrections | reason skipped]
───────────────────────────────────────
 Overall:  PASS — phase is complete
        or FAIL — [N] criteria not met; do not advance
        or WARN — phase can advance, but review [items]
═══════════════════════════════════════
```

The **Code review** row reports step 2. `PASS` covers both "no findings" and "findings
found and fixed here" — a defect the checkpoint caught and repaired is the process
working, not the phase failing. Use `WARN` for an out-of-scope finding recorded under
item 2 of step 2, and name it. A finding that escalated under item 4 of step 2 does not
belong on this row at all: it fails the criterion it actually violated (Diff review, or
the specific DoD item) so the reason survives into the `### Corrections` section.

The **Next-phase plan** row reports step 7 and never affects **Overall**: the validated
phase passes or fails on its own work.

Below the box, report these separately, citing `file:line` where it helps the user
verify:

- **Completed-phase findings and fixes** — what was applied, dismissed (with evidence),
  or recorded as out of scope (with the scope reason).
- **Validation** — the exact commands run and their results, including every
  "not run: <reason>".
- **Next-phase plan corrections** — what step 7 changed, or why it was skipped.
- **Confirmation that the next phase was not executed.**
- **Blockers and residual risks** — out-of-scope findings and anything left for the
  operator to decide.

Then name the next command: `/refactor-next <kebab>` after a PASS or WARN with phases
remaining, `/refactor-next <kebab>` to retry after a FAIL, or `/adr` after retirement
when an ADR is due.
