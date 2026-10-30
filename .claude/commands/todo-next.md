---
description: Execute the next ready TODO item via a subagent (Claude models) or a prompt file (external models)
argument-hint: [id]
---

# /todo-next

Execute the next ready TODO item by spawning a subagent or writing a prompt file for external models.

Before any successful tracker update or default queue selection, read and apply
[Priority and order](../docs/README.todo-commands.md#priority-and-order).
It defines the table schema, priority assessment, dependency checks, stable
ordering and reporting. Invalid invocations that stop at a gate stay read-only.

## What to do

### 1 — Find the item to run

Read `.local/TODO.md` and assess the current priority/dependency order under
the shared policy before selecting. Preserve lifecycle statuses and explicit
operator assignments; priority never substitutes for readiness.

- If an ID argument was provided: find that row. If it does not exist, report
  "ID not found in .local/TODO.md." and stop. If its status is `ready`, proceed. If its
  status is `in progress`, see **Retry after a failed checkpoint** below. For any other
  status, report the current status and the appropriate prior step, and stop.
- Otherwise: select the eligible `ready` item with the smallest `Order`.
  Verify hard dependencies and external prerequisites; skip blocked ready
  items and report why. If all ready items are blocked, report their blockers
  and stop. If no `ready` items exist: report "No ready items. Use `/todo-ready <id>` to mark a
  planned item ready." Report the lowest-Order item's required preparation
  step, then stop. Never pick an `in progress` item without an explicit
  ID — a retry is a deliberate act, not something to sweep up automatically.

**Retry after a failed checkpoint.** An `in progress` item is a retry only when
`.local/todos/<id>.plan.md` carries a `## Corrections` section, which is what
`/todo-checkpoint` writes when it fails. If it does, proceed — the corrections are
mandatory scope for this run. If it does not, the item is mid-flight or was abandoned:
report "Item is in progress with no corrections recorded — it is either still running or
was abandoned. Run `/todo-checkpoint <id>` to find out which." and stop.

Without this path an item that fails its checkpoint is stranded: `/todo-ready` refuses
an `in progress` item and sends you back to `/todo-checkpoint`, which is what set that
status in the first place.

### 2 — Load spec and plan

Read `.local/todos/<id>.spec.md` and `.local/todos/<id>.plan.md`.

- If either file is missing: report which is missing, suggest re-running `/todo-spec` or `/todo-plan`, and stop.

Before dispatch (including explicit IDs and retries), verify prerequisites
against current evidence. An explicit ID bypasses queue position only.
Unresolved dependencies, cycles or external blockers stop dispatch.

### 3 — Check the model

Read the `model:` field from the plan file.

- **Claude models** (`haiku`, `sonnet`, `opus`): see Claude branch below.
- **Anything else** (e.g. `codex`, `gemini`): see Non-Claude branch below.

### 4 — Mark the item in progress and record the baseline

Change the item's status in `.local/TODO.md` from `ready` to `in progress` before
dispatching. This makes a crashed or abandoned run visible, and it is the
status a failed `/todo-checkpoint` rolls back to.

Re-read the tracker, preserve other rows, and reassess/renumber the queue
under the shared policy without interrupting other in-progress work.

Then record the current commit in the plan file's frontmatter, so the checkpoint can
identify this item's change set no matter what state the tree is in when it runs:

```bash
git rev-parse HEAD
```

```yaml
baseline: <sha>
```

**Write it only if the field is absent.** A retry validates the whole item, not just its
corrections, so the original baseline must survive — overwriting it on a retry would hide
everything the first attempt did from the next review.

Without this, a checkpoint that runs after the operator has committed sees a clean tree
and has nothing to diff. Recording one SHA here is what lets the checkpoint cover all
three states — work uncommitted, work committed, or a mix — without guessing.

---

## Claude branch

Construct a prompt with these four parts:

**Part 1 — Context:**

> You are implementing a tracked TODO item. If an `AGENTS.md` file exists in the repo root,
> read it for project conventions before starting.

On a retry, add:

> A previous attempt failed its checkpoint. The plan below carries a `## Corrections`
> section: those items are mandatory scope and the reason this run exists. The rest of
> the plan is already implemented — verify it against the tree rather than redoing it,
> and do not revert working code to re-execute a step.

Include the shared guide's Priority and order section verbatim in this
context so the implementer receives the policy used to maintain the queue.

**Part 2 — Spec:**

> (verbatim content of `<id>.spec.md`)

**Part 3 — Plan:**

> (verbatim content of `<id>.plan.md`)

**Part 4 — Closing instructions:**

> **Place code for the project, not just this item.** Before you add a function, type,
> constant, file or hand-maintained list entry, check the plan's `## Placement`
> section, then search for an existing near-equivalent — the code graph's semantic
> search if the repo has one, then grep by behavior, not only by name. If something
> already does the job, extend or reuse it. Prefer extending an existing shape to
> adding a parallel one. If correct placement means changing a file the Steps do not
> name — extending a shared helper instead of copying it, exporting a constant instead
> of duplicating it — make that change, keep it minimal, and add a row to the plan's
> Placement table saying why. Do not copy code to stay inside the files the Steps name.
> If the right placement would break a spec **Constraint**, keep the local change and
> report the conflict in your synopsis instead of working around the Constraint.
>
> **Run shell commands as the plan's `## Commands` section lists them.** Do not swap a
> listed command for another tool. A plan step written in prose maps to a line in that
> section, so use the line. When you need a command the section does not list, use
> the plainest standard tool for the job (for example `cp -R`, not `rsync`). If a
> command is denied or the permission system refuses it, do not retry it in another
> form or through another tool. Stop, and report the exact denied command in your
> synopsis as a blocker. A denial is the operator's policy, and you may not route
> around it.
>
> When you have completed the implementation:
>
> 1. Run the project test suite. Do not consider the work done with failing tests.
> 2. Check each item in the DoD Checklist in the plan above and confirm it is satisfied.
>    If the plan carries a `## Corrections` section, every item in it must also be
>    satisfied.
> 3. Re-read `.local/TODO.md`, change only this item's `in progress` status to `done`,
>    and reassess Priority/Order under the shared policy. Preserve other edits.
>    Do not remove the row or unblock dependents yet: `done` awaits checkpoint.
> 4. Return a brief synopsis: what was implemented, any blockers or open questions,
>    any placement edits outside the Steps' files, and confirmation of which DoD items
>    were satisfied. Claim only what you actually ran —
>    a checkpoint will re-run the tests and read the diff, so an overstated claim costs
>    a round rather than buying one.

Spawn a subagent using the Agent tool:

- `subagent_type`: `general-purpose`
- `model`: the plan's model value (`haiku` / `sonnet` / `opus`)
- `description`: `TODO <id> — <summary from .local/TODO.md>`
- `prompt`: the full constructed prompt above

Run in the **foreground**.

### After the subagent returns — verify, then review

**First, verify the bookkeeping yourself — the synopsis is a claim, not evidence.** An
agent can finish the code correctly and still skip every closing item it was given. Check
that `.local/TODO.md` says `done`, reconcile Priority/Order under the shared
policy, and re-run the test command rather than trusting that
it was run. Fill in whatever is missing yourself instead of re-running the item; the code
is already written and a re-run risks undoing it.

**Then review the implementation in a second subagent, and adjudicate the findings.** This
happens here, not at checkpoint time: the diff is at its largest and freshest the moment
the implementer stops, and everything found here is a defect the operator never has to
see. Skip it only if the item produced no changes at all.

The reviewer must be a **new `general-purpose` subagent, run in the foreground**, on the
model set by the item's `Effort` value from its `.local/TODO.md` row: `sonnet` for
`Light`/`Medium`, `opus` for `Heavy` — the same complexity-scaled choice `/todo-plan`
already makes for the implementer, applied here to the review step instead. Never reuse
the implementing agent — not by `SendMessage`, not by asking it to check its own work. An agent reviewing its own output re-reads the intent it had while
writing, so a comment that says the wrong thing still looks right to it; a reader with no
memory of that intent is the only one who sees what is actually on the page, and is the
same position the next human will be in.

Give the reviewer the item's change set (`git diff <baseline>` plus untracked files), the
spec's **Acceptance Criteria** and **Constraints** quoted inline, and these standing
instructions:

- report only — it has no authority to edit the tree;
- read the changed files in full plus whatever surrounding code is needed to judge them;
- cite the governing ADR or convention checked per finding, or say plainly that none was
  found;
- check the item's own edits for the defect class the item exists to remove, if it has
  one — the likeliest place to introduce a seventh wrong claim is a change correcting six;
- cover correctness, regressions, security, Constraint violations, lost behavior or
  comments, missing coverage (including no guard over a list or constant the item
  edited in more than one place), and inaccurate completion claims;
- check placement against the plan's `## Placement` section (quote it inline): a new
  helper or constant that duplicates an existing one, code in the wrong module, a copy
  made to stay inside the files the Steps name, an unrecorded placement edit;
- classify every finding as in scope or out of scope, with the reason for the latter;
- verify a tool is actually unavailable before reporting it so — a globally cached
  `npx --offline <tool>` often works when nothing is declared in the repo;
- write findings to `.local/REVIEW.md` in the format `/review` produces;
- an empty report is an acceptable and useful outcome — do not pad the count.

**Adjudicate every finding yourself**, applying the same rules `/todo-checkpoint` uses:
verify each against the tree before acting, apply what survives smallest-correct-change
first, prove any new guard test actually fails without its fix, escalate nothing silently,
track each out-of-scope finding as a new `raw` TODO rather than a "residual", and delete
`.local/REVIEW.md` once every finding is applied, dismissed with evidence, or tracked.
Update the repo's commit-message handoff to cover what you changed.

If `.local/REVIEW.md` already exists when you get here, the operator ran `/review` by
hand — adjudicate what is in it rather than spawning a second pass.

**Then record that the review happened**, so the checkpoint reviews only what changes
after this point instead of repeating the whole pass. In the plan file's frontmatter:

```yaml
reviewed: <sha>
```

Use `git rev-parse HEAD` when the tree is clean, or `git stash create` — which writes a
commit object without touching the tree — when it is dirty. If neither is available, set
`reviewed: dirty` and let the checkpoint fall back to a full review.

### Report

- Which item ran, its Effort, Priority and Order from `.local/TODO.md`, and which model implemented it.
- Queue changes and the next eligible ready item or preparation step; do not execute it.
- A 3–5 sentence synopsis of what was done.
- Review outcome: findings by severity, how many applied, how many dismissed and why,
  and any new TODOs added for out-of-scope findings.
- Placement edits made outside the files the Steps named, and why.
- Any blockers or open questions either agent flagged.
- Remind the user to run `/todo-checkpoint <id>` before moving on.

---

## Non-Claude branch

Construct the same prompt (Parts 1–4) but write it as raw task content — no wrapper text, no meta-commentary, no "here is what you need to do" framing. Just the content.

Ensure `.local/` exists and `.local/.gitignore` exists containing exactly:

```text
*
!.gitignore
```

Write the prompt to `.local/<id>.PROMPT.md`.

**Do not write a `reviewed:` field.** The work happens in a session this command cannot
see, so there is nothing to review here and no review to record. `/todo-checkpoint` finds
no `reviewed:` marker and runs the full review itself — which is correct for this branch,
and the reason the marker is written rather than assumed.

Report:

```text
═══════════════════════════════════════
 TODO <id> — <summary>
 Model: <model name>
═══════════════════════════════════════

This item is set for <model>. The prompt has been written to:
  .local/<id>.PROMPT.md

Copy that file into your <model> session. When it finishes:
- Confirm tests pass.
- Confirm .local/TODO.md status is updated to done and Priority/Order have been reassessed without retiring the row.
- Run /todo-checkpoint <id> to validate the DoD.
```

Do not mark the item done. Do not spawn a subagent. Wait for the user to return.
