---
description: Validate a completed TODO item against its Definition of Done (Effort-scaled code review, then tests)
argument-hint: <id>
---

# /todo-checkpoint

Validate that a completed TODO item satisfies its Definition of Done.

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

Detect the project test command in this order (a Makefile `test` target is the
project's canonical gate and may run more than the bare tool would):

1. `Makefile` present with a `test` target → `make test`
2. `go.mod` present → `go test ./...`
3. `package.json` present with a `"test"` script → `npm test`
4. `pytest.ini`, `pyproject.toml`, or `setup.py` present → `pytest`

If none detected: report "Could not detect test command — run tests manually and confirm pass." Treat as WARN for this criterion only, not FAIL.

Run any additional suite the plan's DoD or validation steps name — a tagged
integration run, a second package manager's suite — and report it on the same row. An
item validated by a suite the auto-detection does not reach is not validated.

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
working, not the item failing. Use `WARN` for a finding deliberately left unfixed, and
name it. A finding that escalated under item 5 of step 2 does not belong on this row at
all: it fails the criterion it actually violated, so the reason survives into the
`## Corrections` section.

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

### 5 — Report

```text
═══════════════════════════════════════
 Checkpoint — <id> — <summary>
═══════════════════════════════════════
 Code review      PASS / WARN / N/A — [N findings: A applied, D dismissed]
 Tests            PASS / FAIL / WARN — [note]
 Acceptance       PASS / FAIL — [N of M criteria met]
 Docs             PASS / FAIL / WARN — [note]
 Technical debt   PASS / FAIL — [note]
 <one line per optional item, if any>
───────────────────────────────────────
 Overall:  PASS — item is complete
        or FAIL — [N] criteria not met
        or WARN — can advance, review [items]
═══════════════════════════════════════
```

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

**On WARN:** The item can stand. Call out what to revisit.

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

5. Tell the user to run `/todo-next` for the next item.

**Other rows may cite this ID** — items routinely reference each other for context or
sequencing. Those references stay valid: the spec and plan are in `.local/completed/`,
not gone. Do not rewrite them and do not delete the archived files to tidy up; a
dangling-looking ID resolves there.
