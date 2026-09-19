---
description: Execute the next ready TODO item via a subagent (Claude models) or a prompt file (external models)
argument-hint: [id]
---

# /todo-next

Execute the next ready TODO item by spawning a subagent or writing a prompt file for external models.

## What to do

### 1 — Find the item to run

Read `.local/TODO.md`.

- If an ID argument was provided: find that row. If it does not exist, report
  "ID not found in .local/TODO.md." and stop. If its status is `ready`, proceed. If its
  status is `in progress`, see **Retry after a failed checkpoint** below. For any other
  status, report the current status and the appropriate prior step, and stop.
- Otherwise: find the first row with status `ready` (top to bottom). If no
  `ready` items exist: report "No ready items. Use `/todo-ready <id>` to mark a
  planned item ready." and stop. Never pick an `in progress` item without an explicit
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

### 3 — Check the model

Read the `model:` field from the plan file.

- **Claude models** (`haiku`, `sonnet`, `opus`): see Claude branch below.
- **Anything else** (e.g. `codex`, `gemini`): see Non-Claude branch below.

### 4 — Mark the item in progress and record the baseline

Change the item's status in `.local/TODO.md` from `ready` to `in progress` before
dispatching. This makes a crashed or abandoned run visible, and it is the
status a failed `/todo-checkpoint` rolls back to.

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

**Part 2 — Spec:**

> (verbatim content of `<id>.spec.md`)

**Part 3 — Plan:**

> (verbatim content of `<id>.plan.md`)

**Part 4 — Closing instructions:**

> When you have completed the implementation:
>
> 1. Run the project test suite. Do not consider the work done with failing tests.
> 2. Check each item in the DoD Checklist in the plan above and confirm it is satisfied.
>    If the plan carries a `## Corrections` section, every item in it must also be
>    satisfied.
> 3. Update `.local/TODO.md`: change this item's status from `in progress` to `done`.
> 4. Return a brief synopsis: what was implemented, any blockers or open questions, and
>    confirmation of which DoD items were satisfied. Claim only what you actually ran —
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
that `.local/TODO.md` says `done`, and re-run the test command rather than trusting that
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
- verify a tool is actually unavailable before reporting it so — a globally cached
  `npx --offline <tool>` often works when nothing is declared in the repo;
- write findings to `.local/REVIEW.md` in the format `/review` produces;
- an empty report is an acceptable and useful outcome — do not pad the count.

**Adjudicate every finding yourself**, applying the same rules `/todo-checkpoint` uses:
verify each against the tree before acting, apply what survives smallest-correct-change
first, prove any new guard test actually fails without its fix, escalate nothing silently,
and delete `.local/REVIEW.md` once every finding is applied or dismissed with evidence.
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

- Which item ran, its `Effort` value from `.local/TODO.md`, and which model implemented it.
- A 3–5 sentence synopsis of what was done.
- Review outcome: findings by severity, how many applied, how many dismissed and why.
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
- Confirm .local/TODO.md status is updated to done.
- Run /todo-checkpoint <id> to validate the DoD.
```

Do not mark the item done. Do not spawn a subagent. Wait for the user to return.
