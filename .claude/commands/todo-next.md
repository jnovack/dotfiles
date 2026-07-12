---
description: Execute the next ready TODO item via a subagent (Claude models) or a prompt file (external models)
argument-hint: [id]
---

# /todo-next

Execute the next ready TODO item by spawning a subagent or writing a prompt file for external models.

## What to do

### 1 — Find the item to run

Read `TODO.md`.

- If an ID argument was provided: find that row. If it does not exist, report
  "ID not found in TODO.md." and stop. If its status is not `ready`, report the
  current status and the appropriate prior step, and stop.
- Otherwise: find the first row with status `ready` (top to bottom). If no
  `ready` items exist: report "No ready items. Use `/todo-ready <id>` to mark a
  planned item ready." and stop.

### 2 — Load spec and plan

Read `.claude/todos/<id>.spec.md` and `.claude/todos/<id>.plan.md`.

- If either file is missing: report which is missing, suggest re-running `/todo-spec` or `/todo-plan`, and stop.

### 3 — Check the model

Read the `model:` field from the plan file.

- **Claude models** (`haiku`, `sonnet`, `opus`): see Claude branch below.
- **Anything else** (e.g. `codex`, `gemini`): see Non-Claude branch below.

### 4 — Mark the item in progress

Change the item's status in `TODO.md` from `ready` to `in progress` before
dispatching. This makes a crashed or abandoned run visible, and it is the
status a failed `/todo-checkpoint` rolls back to.

---

## Claude branch

Construct a prompt with these four parts:

**Part 1 — Context:**

> You are implementing a tracked TODO item. If an `AGENTS.md` file exists in the repo root,
> read it for project conventions before starting.

**Part 2 — Spec:**

> (verbatim content of `<id>.spec.md`)

**Part 3 — Plan:**

> (verbatim content of `<id>.plan.md`)

**Part 4 — Closing instructions:**

> When you have completed the implementation:
>
> 1. Run the project test suite. Do not consider the work done with failing tests.
> 2. Check each item in the DoD Checklist in the plan above and confirm it is satisfied.
> 3. Update `TODO.md`: change this item's status from `in progress` to `done`.
> 4. Return a brief synopsis: what was implemented, any blockers or open questions, and
>    confirmation of which DoD items were satisfied.

Spawn a subagent using the Agent tool:

- `subagent_type`: `general-purpose`
- `model`: the plan's model value (`haiku` / `sonnet` / `opus`)
- `description`: `TODO <id> — <summary from TODO.md>`
- `prompt`: the full constructed prompt above

Run in the **foreground**. After the subagent returns:

- Report which item ran and which model was used.
- Give a 3–5 sentence synopsis of what was done.
- Call out any blockers or open questions the subagent flagged.
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
- Confirm TODO.md status is updated to done.
- Run /todo-checkpoint <id> to validate the DoD.
```

Do not mark the item done. Do not spawn a subagent. Wait for the user to return.
