---
description: Validate and repair a completed TODO item against its Definition of Done (Effort-scaled code review, then tests), then audit and repair the next ready item's plan without executing it
argument-hint: <id>
---

# /todo-checkpoint

Validate that a completed TODO item satisfies its Definition of Done, fixing every
in-scope defect rather than reporting it. When the item passes, **fix ahead**: audit the
plan of the item `/todo-next` will run next against the repaired tree, and correct it in
place without executing it.

**Never commit, stash, reset, discard, or delete user work**, and never `git checkout` a
path. The item's work is normally uncommitted, and the tree often also carries other
items' or a refactor's uncommitted work and unrelated operator edits. Restore a probe by
editing back.

Before any successful tracker update or default queue selection, read and apply
[Priority and order](../docs/README.todo-commands.md#priority-and-order).
It defines the table schema, priority assessment, dependency checks, stable
ordering and reporting. Invalid invocations that stop at a gate stay read-only.

## What to do

### 1 — Identify the item

An ID argument is required. If none was provided: list every row in `.local/TODO.md`
with status `done` or `in progress`, report "Provide an ID:
`/todo-checkpoint <id>`", and stop. Do not guess which item to validate.

Find the row with the given ID. If it does not exist, report "ID not found in
.local/TODO.md." and stop. Its status should be `done` or `in progress` (the item has
been executed); if it is anything earlier in the lifecycle, report the status
and stop — there is nothing to validate yet.

Read `.local/todos/<id>.spec.md` and `.local/todos/<id>.plan.md` to get the acceptance
criteria and the DoD checklist (core and any optional items declared).

- If the plan file is missing: report it and proceed with core DoD only — flag the missing plan as a WARN.

Also read the repository's conventions file, and note the item `/todo-next` would pick
next (the eligible `ready` item with the smallest `Order`, excluding this one)
plus any `planned` or `ready` item
whose spec **Dependencies** cites this ID. This is a provisional list: step 5
reassesses the queue, and step 6 selects again after retirement.

### 2 — Review whatever has not been reviewed yet

This runs **before** the tests, not after. Adjudicating a finding changes code, and the
test run has to validate the tree that will actually be committed — reviewing after a
green test run means the last thing that touched the code was never tested.

**How much to review depends on `reviewed:` in the plan file's frontmatter.** `/todo-next`
writes it after reviewing and adjudicating the implementation, so the bulk of the defects
are normally already gone by the time you get here.

- **`reviewed:` holds a SHA** — review only what changed since it: `git diff <reviewed>`
  plus untracked files. That covers operator hand-edits and anything you adjudicated in
  an earlier checkpoint round. **If that delta is empty, skip the review entirely** and
  mark the row `N/A — reviewed at <sha>, no changes since`. Re-reviewing an unchanged
  tree buys nothing and costs an Opus pass.
- **`reviewed:` is absent or `dirty`** — run the full review over the whole change set.
  Absent means the item came through the non-Claude branch, was run before this workflow
  existed, or was implemented by hand. This is the fallback, not the normal path.

Skip regardless when the item produced **no changes at all** — nothing in `git diff`,
nothing untracked — and say so rather than spawning an agent to review nothing. Do **not**
skip a documentation-only item: prose that reads as fact and is wrong is exactly what a
test suite cannot catch, and it is the change class this step earns its keep on.

**If `.local/REVIEW.md` already exists, do not spawn a review.** The operator runs
`/review` by hand; a second pass would duplicate work and overwrite their file. Go
straight to adjudication with the findings already there.

When you do spawn, it must be a **new** subagent — never the one that implemented the
item, and never one asked to re-check its own earlier findings. An agent reviewing work
it produced reads back the intent it had while writing it, which is exactly the blind
spot the review exists to cover.

Otherwise gather the item's change set. Read `baseline:` from the plan file's frontmatter
— `/todo-next` records the commit HEAD pointed at when it dispatched.

**With a baseline**, the change set is everything since it, committed or not:

```bash
git diff --stat <baseline>
git diff <baseline>
git status --porcelain
```

That covers all three states the tree can be in at checkpoint time — work still
uncommitted, work already committed, or a mix — without guessing.

**Without a baseline** (an item dispatched before `/todo-next` recorded one, or run by
hand), fall back in this order, and say in the report which one you used:

1. **Uncommitted work** — `git status --porcelain` plus `git diff`, when either is
   non-empty.
2. **The item's commit**, when the tree is clean. Try `git log --grep=<id>`, then a
   commit whose subject matches the first line of the repo's commit-message handoff file
   if it has one. Before trusting a match, confirm the files it touches are the ones the
   plan's Steps name. A recovered commit is equivalent to the diff, not weaker — do not
   degrade past this step just because the tree is clean.
3. **Degraded** — mark the review **WARN — degraded**, read in full the files named in
   the plan's Steps, and say plainly in the report that it ran without a diff. Do not
   quietly substitute the weaker check.

Any `??` entry in `git status --porcelain` that this item plausibly created is part of
its work — `git diff` does not show untracked files, and an item whose deliverable is a
new file diffs to nothing otherwise.

**Attribute the change set before judging it.** `git diff <baseline>` includes every
uncommitted change in the tree, so it can carry another item's work, a refactor phase's,
or unrelated operator edits. Use the plan's Steps and Placement section to separate this
item's changes from the rest; judge other work only where this item touched it, and
leave it alone.

Then spawn **one `general-purpose` subagent, in the foreground**, on the model
set by the item's `Effort` value from its `.local/TODO.md` row: `sonnet` for
`Light`/`Medium`, `opus` for `Heavy`. This mirrors `/todo-plan`'s
complexity-scaled choice of implementation model — apply the same scaling to
the review step, since a missed correctness bug on a `Heavy` item is the more
expensive failure to eat. Instruct it to:

- review **only** that change set, reading the changed files in full plus whatever
  surrounding code it needs to judge them (a finding about new code usually depends on
  code that did not change);
- read the repository's conventions file and any ADR governing the touched code, and
  cite for each finding which governing intent was checked — or state that none was
  found, rather than implying the check passed;
- quote the spec's **Acceptance Criteria** and **Constraints** inline in the prompt, so
  the reviewer can catch a violation the test suite cannot — a constraint is written
  down precisely because it is the thing an implementer is likely to undo;
- **check the item's own edits for the defect class the item exists to remove.** An item
  that corrects six instances of a wrong claim is the likeliest place in the repo to
  introduce a seventh, and the executing agent is the least able to see it. Name that
  class in the prompt when the item has one;
- **verify a tool is unavailable before reporting it as such.** A globally cached
  `npx --offline <tool>` frequently works when nothing is declared in the repo, and
  "could not check" reported as "cannot be checked" silently drops a criterion;
- cover correctness, regressions, security, Constraint violations, **lost behavior or
  comments** (deleted or reworded intent, a dropped branch or log line), missing
  coverage — including the absence of a guard over any duplicated list, constant or
  contract the item edited in more than one place — and inaccurate completion claims
  (DoD boxes, the executing agent's synopsis);
- **check placement against the project, not just the neighborhood.** Quote the plan's
  Placement section inline. For each new function, type, constant, file or list entry:
  does an existing near-equivalent already do the job (search by behavior, not name)?
  Is it in the module that owns that concern? Was code copied rather than a shared
  helper extended? Is this the third or later hand-maintained copy of something?
- classify every finding as **in scope** or **out of scope**, giving the reason for the
  latter (see item 2 of the adjudication below), and never park an in-scope gap as a
  "residual";
- **report only — never edit code.** The reviewer has no authority to change the tree;
  adjudication is yours;
- write findings to `.local/REVIEW.md` in the format `/review` produces, and return a
  count by severity.

Tell it plainly that an empty report is an acceptable and useful outcome, and that it
should note where static analysis alone left residual risk instead of padding the count.
Extract the spec and plan sections it needs rather than pasting both files wholesale.

**Then adjudicate every finding yourself.** The reviewer's report is a claim, exactly as
the executing agent's synopsis was:

1. **Verify each finding against the tree before acting on it.** Confirm the cited lines
   say what the finding says they say. A finding that does not reproduce is dismissed
   with that evidence stated — not applied because it is small and already written down.
2. **Apply what survives**, smallest correct change first. Where the proposed fix would
   contradict an ADR, a spec **Constraint**, or the only place a decision was written
   down, apply the architecturally correct fix instead and say why the proposed one was
   wrong.

   **"Residual" is not a third outcome.** Every observation — including ones you or the
   reviewer would call a nit, a residual, pre-existing, or out of scope — ends as
   *applied*, *dismissed with evidence*, or *out of scope with a scope reason*. A gap is
   **in scope** when it concerns code, tests or docs this item touched, or a contract it
   created or extended — for example, a comment in a touched file requiring two lists to
   stay aligned, with no test enforcing it after the item edited both. **Out of scope**
   requires that the fix would land only in files and behavior the item did not touch,
   and no Acceptance Criterion or plan step covers it. Track each out-of-scope finding,
   including a consolidation too large for this item, as a new `raw` row in
   `.local/TODO.md` (ID and row format exactly as `/todo-add` generates them), and name
   it in the report — never leave it as silent "residual risk". Seen 2026-10-09: a
   refactor checkpoint logged a missing list-parity guard as an out-of-scope residual
   although the phase had just edited both lists; a follow-up pass added it in a dozen
   lines.
3. **Prove new guard tests actually guard.** If a finding adds a test, mutate the
   production code it claims to protect, watch the test fail, restore **by editing back —
   never `git checkout`**, which would discard the item's uncommitted work — and confirm
   green. A guard that was never seen red is not evidence.
4. **Check a proposed test is buildable in this repo's harness before promising it.** A
   finding may name a test the existing harness cannot express. Verify, and if it cannot,
   say so and explain why the change is low-risk or already covered instead of writing a
   brittle substitute that asserts on source text or formatting.
5. **Do not quietly patch a structural failure.** A finding that reveals a violated spec
   **Constraint**, a missed **Acceptance Criterion**, or a falsely-claimed DoD item is a
   checkpoint FAIL: it belongs in the `## Corrections` section in step 5, not in a silent
   fix. Ordinary defects — a missing assertion, an unhandled error, dead code, a
   misleading comment — are fixed here and do not fail the checkpoint.
6. **Delete `.local/REVIEW.md` once every finding is adjudicated** — applied or dismissed
   with evidence. It is a punch-list, not an archive; the durable record is the checkpoint
   report and the code itself.

**One review round per command. Do not re-spawn a reviewer over your own fixes.** Every
fix is new code, so a review always has something new to find and "loop until clean" has
no terminating condition — it converges toward zero without reaching it while each round
costs a full pass. The bound is structural, not a counter: `/todo-next` reviews the
implementation, and this command's delta review covers the fixes that came out of it.
That is two rounds over shrinking surfaces, which is where the yield already flattens.

If a round returns only Low findings that are wording rather than a wrong claim, apply
them and stop. Spawning again to inspect those edits is how a checkpoint burns an hour
polishing comments nobody will read.

If the repository uses a commit-message handoff file, update it to cover the fixes
applied here. The commit is the permanent record, and a fix made at checkpoint that the
message does not mention is a fix no future reader can account for.

Any code you changed here is part of the change set from this point on. Steps 3 and 4
judge the tree as it now stands, not as the executing agent left it.

### 3 — Detect and run tests

Run the narrowest relevant checks first — the packages and test files the item touched —
so a failure points at its cause. Then detect the project test command in this order (a Makefile `test` target is the
project's canonical gate and may run more than the bare tool would):

1. `Makefile` present with a `test` target → `make test`
2. `go.mod` present → `go test ./...`
3. `package.json` present with a `"test"` script → `npm test`
4. `pytest.ini`, `pyproject.toml`, or `setup.py` present → `pytest`

If none detected: report "Could not detect test command — run tests manually and confirm pass." Treat as WARN for this criterion only, not FAIL.

Run every additional command the plan's DoD or validation steps name — a tagged
integration run, a second package manager's suite, a lint or grep check — and report it
on the same row. Run them **as the plan's `## Commands` section lists them**. Never
substitute a different tool, and never retry a denied command in another form; a denial
is a "not run" (below). An item validated by a suite the auto-detection does not reach is not
validated. A ticked DoD box is a claim, not evidence, so re-run the command behind it:

- **A command must demonstrably exercise something.** A `-run` pattern that matches no
  test, or a grep that cannot match, passes vacuously — FAIL that item and fix the
  command. Seen 2026-10-09: a plan's `go test -run Playwright` matched zero test names
  and had been reported green.
- **Record validation that cannot run here honestly** — no Docker, no browser, or a step
  needing live, external, privileged or destructive access that requires the operator's
  approval. Report it as "not run: <reason>", never as PASS, and do not take a gated
  action to make the item pass.

If a command is detected and tests **fail**:

- Report which tests failed and the relevant output.
- Mark the checkpoint **FAILED — tests**.
- Skip the remaining checks, but still run the **On FAIL** handling in step 5. The
  corrections written there are the only thing the retry reads; stopping outright sends
  `/todo-next` back in with the same input that just failed its tests.

Pre-existing failures unrelated to this item do not fail the checkpoint, but do not take
that claim on faith either: confirm they reproduce independently of the item's changes,
say so on the row, and make sure they are tracked in `.local/TODO.md` rather than left as
a red suite nobody owns.

### 4 — Check DoD criteria

Report PASS, FAIL, or WARN for each:

**Code review** — result from step 2. `PASS` covers both "no findings" and "findings
found and fixed here" — a defect the checkpoint caught and repaired is the process
working, not the item failing. Use `WARN` for an out-of-scope finding tracked as a new
TODO under item 2 of step 2, and name it. A finding that escalated under item 5 of
step 2 does not belong on this row at all: it fails the criterion it actually violated,
so the reason survives into the `## Corrections` section.

**Tests** — result from step 3.

**Acceptance criteria** — read the spec's **Acceptance Criteria** and check each against
the tree. This is the item's own definition of correct, and it is more specific than the
generic DoD rows below. FAIL and name any criterion not met.

**Docs** — check whether any of the following were relevant to the change and, if so, whether they were updated:

- `README.md` (flags, env vars, runtime behavior)
- API docs / `docs/openapi.yaml`
- `AGENTS.md` / `CLAUDE.md` (architecture contracts)
- `doc.go` in any affected package

FAIL if a relevant doc was not updated.

**Technical debt** — are any new `// TODO` or `// FIXME` markers introduced by this work? If so, do they each have a corresponding entry in `.local/TODO.md`? Untracked debt = FAIL.

**Optional items** — for each optional item declared in the plan's DoD checklist, check whether it was completed. FAIL if a declared optional item was not completed.

Judge every row against the code, not against the executing agent's synopsis. That
synopsis was written by the agent under validation; it is a claim, not evidence.
Narrow an overstated claim to what its cited proof actually supports rather than
accepting or rejecting it whole.

### 5 — Record the outcome

Decide the overall result from steps 2–4 — PASS, FAIL or WARN, as defined by the report
in step 7 — and update the files to match. Tick a plan DoD box only for an item verified
in this run.

**On FAIL** — the work is not done, and the index must say so.

1. Set the item's status in `.local/TODO.md` to `in progress`.

2. Write a `## Corrections` section into `.local/todos/<id>.plan.md`, immediately before
   its `## DoD Checklist`. This is the only channel that reaches the retry: `/todo-next`
   builds its prompt from the spec and plan files and never reads this report, so a
   finding recorded only in chat is a finding the next run is guaranteed not to see — it
   would receive the same input that just produced the failure.

   ```markdown
   ## Corrections

   <!-- Written by /todo-checkpoint on YYYY-MM-DD. Mandatory scope on the next
        /todo-next run. Removed by the checkpoint once it passes. -->

   - [ ] C1 — `path/to/file.go`: what is wrong, and what the correct end state is.
   ```

   One item per finding, each naming a file and the condition that would satisfy it.
   "Tests fail" is not a correction — the correction is the specific thing that must
   become true. If a `## Corrections` section already exists from an earlier failed
   checkpoint, replace it wholesale rather than appending: items that no longer
   reproduce have been fixed, and carrying them forward sends the next run to redo work
   that is already done.

3. Tell the user to re-run `/todo-next <id>` — it picks up the Corrections section — then
   `/todo-checkpoint <id>` again.

**On WARN:** The item can stand. Call out what to revisit, and retire it as on PASS.

**On PASS — retire the item.** A passing checkpoint ends the item's life; it is not a
status change. Finished rows left in the index turn a punch-list into something to scroll
past, and the operator does not revisit completed items.

1. Delete the plan's `## Corrections` section if it has one — it has done its job, and one
   left in place is mandatory scope on any future re-run of the item.

2. **Remove the item's row from `.local/TODO.md` entirely.** Do not set it to `done` and
   leave it in the table.

3. Archive its sidecars — `.local/` is gitignored, so a plain move:

   ```bash
   mkdir -p .local/completed
   mv .local/todos/<id>.spec.md .local/todos/<id>.plan.md .local/completed/
   ```

4. Delete `.local/<id>.PROMPT.md` if the item went through the non-Claude branch. It is
   generated from the spec and plan, so archiving it would store a third copy of content
   that is already in `.local/completed/`.

5. Reassess Priority/Order and blockers across the remaining queue using
   the shared policy. Resolve retired dependency notes from verified evidence
   for raw/spec'd items too, without promoting their statuses. Renumber rows,
   then recompute the next eligible ready item before fixing ahead (step 6).

6. **Commit the item with `git autocommit`.** This skill explicitly
   instructs it, which is the exception the global "Commit handoff" rule
   allows. Each passing item becomes its own commit, so todos can be chained
   with each `/todo-next` building on a committed tree.
   - Overwrite `.local/COMMIT-MSG.txt` so it describes **this item only**:
     a Conventional Commits subject, then a short *why* body that includes
     any release note or consumer note the plan's DoD requires. Do not
     append to a message left over from earlier work. Add no AI
     attribution.
   - Run `git autocommit` (`git add -A`, commit with the message file, then
     delete it). Do not substitute `git add` or `git commit`; they are
     denied.
   - If there is nothing to commit, skip this step and say so in the
     report.
   - If it fails, for example because a hook rejects the commit, do not
     retry and do not try other git commands. Report the failure as a
     blocker and stop after step 7. Do not fix ahead, so a chain halts on an
     uncommitted tree rather than piling the next item onto it.
   - Never commit on FAIL. Failed work stays uncommitted for the retry.

**Other rows may cite this ID** — items routinely reference each other for context or
sequencing. Those references stay valid: the spec and plan are in `.local/completed/`,
not gone. Do not rewrite them and do not delete the archived files to tidy up; a
dangling-looking ID resolves there.

On FAIL, also reassess the failed item's Priority/Order and affected blockers
under the shared policy. A failure is evidence to assess, not an automatic
priority escalation; leave dependents blocked and do not execute them.

### 6 — Fix ahead: audit and repair the next item's plan

Run this only when the result is PASS or WARN and the step 5 commit did not fail.
Skip it on FAIL (the item goes back to `/todo-next` and the tree is not settled),
on a failed commit, and when there is no target. Say which in the report.

**Targets:** recompute from the reassessed queue: the eligible `ready` item
with the smallest `Order` after retirement, plus any
`planned` or `ready` item whose spec **Dependencies** cites the item just retired.

A plan is written against the tree as it stood at `/todo-plan` time, and `/todo-next`
dispatches it verbatim. Every item retired since then may have moved a file, renamed a
symbol or added a helper the plan should now reuse. A stale anchor reaches the
implementer as an instruction; correcting it here costs a plan edit, while correcting it
after the run costs a failed checkpoint.

1. **Treat the repaired working tree as the baseline**, including every fix applied in
   steps 2–4.
2. **Verify every assumption in each target's spec and plan** against the current code,
   dependency versions and APIs, and the repository's conventions file:
   - every cited path, symbol, signature and line still exists and says what the step
     assumes;
   - every fact the item will write into code or docs matches the code that defines it;
   - every dependency the spec names is now satisfied, or still honestly open;
   - every Placement row still holds — including helpers the just-retired item created
     that the target should now reuse instead of copying;
   - every DoD or validation command works as written and matches something: dry-run it
     where that is non-mutating (`make -n`, `go test -list`, a grep), and treat a zero
     match as a broken command;
   - the plan still runs unattended: `~/.claude/bin/plan-loop-check
     .local/todos/<target>.plan.md` passes.
3. **Repair in place.** Correct the plan's Steps, Placement, Commands and DoD, and the
   spec, for what fails. Delete stale or contradictory instructions rather than
   annotating them. For a loop-safety `FAIL`, add the missing `unattended:` field and
   `## Commands` section from the commands the Steps and DoD already name, or swap a
   denied command for a permitted equivalent that does the same job, following
   `/todo-plan` step 3c. Where a step needs the operator, or no permitted equivalent
   exists, write `unattended: no — <reason>` rather than inventing a workaround. Run
   the check again and report its final output.
4. **Respect the human gate.** `ready` means the operator approved the plan as written.
   Mechanical corrections — a drifted anchor, a renamed symbol, a broken command, a
   reused helper replacing a copy, a `## Commands` section transcribed from commands the
   plan already names, a denied command swapped for an equivalent — keep the status.
   Setting `unattended: no` also keeps it, because it records a fact about the plan
   rather than changing the approach. Report it on the Next-item plan row, since
   `/todo-loop` will stop there. A change to the approach, scope,
   **Acceptance Criteria** or **Constraints** sets the item back to `planned`, and the
   report tells the operator to re-read it and run `/todo-ready <id>`. If the spec's
   approach no longer works at all, set it to `spec'd` and send it back to
   `/todo-spec`.
5. **Do not execute any target.** Leave `baseline:` and `reviewed:` unset and change no
   source, test, doc or config file on its behalf. Do not pull target work into the
   item just retired.

### 7 — Report

```text
═══════════════════════════════════════
 Checkpoint — <id> — <summary>
═══════════════════════════════════════
 Code review      PASS / WARN / N/A — [N findings: A applied, D dismissed, O tracked as new TODOs]
 Tests            PASS / FAIL / WARN — [note, including any "not run: <reason>"]
 Acceptance       PASS / FAIL — [N of M criteria met]
 Docs             PASS / FAIL / WARN — [note]
 Technical debt   PASS / FAIL — [note]
 <one line per optional item, if any>
 Commit           <short sha> / NOTHING TO COMMIT / FAILED — [subject | error] (PASS/WARN only)
 Next-item plan   REPAIRED / NO CHANGES / SKIPPED — [ids; N corrections; status changes | reason skipped]
───────────────────────────────────────
 Overall:  PASS — item is complete
        or FAIL — [N] criteria not met
        or WARN — can advance, review [items]
═══════════════════════════════════════
```

The **Next-item plan** row reports step 6 and never affects **Overall**: the item passes
or fails on its own work.

Below the box, report these separately, citing `file:line` where it helps the user
verify:

- **Findings and fixes** — what was applied, dismissed (with evidence), or tracked as a
  new TODO (with its ID and the scope reason).
- **Validation** — the exact commands run and their results, including every
  "not run: <reason>".
- **Next-item plan corrections** — what step 6 changed and any status it moved, or why
  it was skipped.
- **Queue assessment** — Priority/Order changes and reasons, resolved or remaining blockers, and the next eligible ready item or preparation step.
- **Confirmation that no target item was executed.**
- **Blockers and residual risks** — anything left for the operator to decide.

Then name the next command: `/todo-next` after a PASS or WARN (or `/todo-ready <id>`
first when step 6 moved the next item back to `planned`), or `/todo-next <id>` to retry
after a FAIL.
