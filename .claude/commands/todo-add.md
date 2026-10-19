---
description: Capture a raw TODO, assess its priority and insert it into the ordered .local/TODO.md queue
argument-hint: <description>
model: haiku
---

# /todo-add

Capture a raw TODO item with a generated ID, assess priority, and insert it into the repo's `.local/TODO.md` queue.

Before any successful tracker update or default queue selection, read and apply
[Priority and order](../docs/README.todo-commands.md#priority-and-order).
It defines the table schema, priority assessment, dependency checks, stable
ordering and reporting. Invalid invocations that stop at a gate stay read-only.

## What to do

### 1 — Parse the description

Read the free text argument as the raw want description.

### 2 — Generate an ID

Derive a **category prefix** (2–6 uppercase chars) from keywords in the description:

| Keywords | Prefix |
| --- | --- |
| test, spec, coverage, assert | TEST |
| refactor, migrate, move, restructure | REFACTOR |
| ci, pipeline, workflow, docker, build | CI |
| log, metric, observability, trace | LOG |
| fix, bug, broken, incorrect, wrong | FIX |
| feat, add, new, implement, create | FEAT |
| doc, readme, comment, godoc | DOCS |
| api, endpoint, route, handler | API |
| db, schema, migration, query | DB |
| web, ui, frontend, css, html | WEB |

Default to `TASK` if no mapping fits.

Derive a **descriptor** (2–8 uppercase chars) from the most distinctive noun or verb in the description. Strip common words (the, a, an, for, to, with, in, on).

**Find the next numeral:**

- Read `.local/TODO.md` (if it exists) and collect all IDs in the table.
- List all filenames in `.local/todos/` and `.local/completed/` (if present); retired IDs must not be reused.
- Find all existing IDs that share the same `CATEGORY-DESCRIPTOR-` prefix.
- Take the highest numeral found. New ID numeral = highest + 1, zero-padded to 2 digits.
- If no existing IDs share the prefix, start at `01`.

Final format: `CATEGORY-DESCRIPTOR-##` (e.g. `TEST-SMOKE-03`, `FEAT-REGISTRY-01`).
The full ID must be unique across all existing IDs — per-group numbering
guarantees this; if a collision somehow exists anyway, keep incrementing until
it doesn't.

### 3 — Ensure `.local/TODO.md` exists

If `.local/` does not exist, create it, along with `.local/.gitignore`
containing exactly:

```text
*
!.gitignore
```

(Skip this if the repo's root `.gitignore` already ignores `.local/**` —
check first rather than overwriting an existing `.local/.gitignore`.)

If `.local/TODO.md` does not exist, create it:

```markdown
# TODO

| Order | Priority | ID | Status | Effort | Summary |
| --- | --- | --- | --- | --- | --- |
```

For an older tracker, migrate its columns in place using the shared policy.
Preserve row data and explicit operator ordering; do not reset existing priorities.

### 4 — Assess priority and insert the row

Read available dependency context and apply the shared priority/order policy.
Use P2 if urgency is unknown; capture unresolved prerequisites in Ordering notes.
Insert the row at its assessed queue position, then renumber all Order values:

```text
| <Order> | <P0|P1|P2|P3> | <ID> | raw | — | <description, truncated to ~80 chars> |
```

`Effort` starts as `—`. It is a guess at how much code, time, and token budget
the item needs to execute — not how hard the reasoning is — and it is filled in
by `/todo-spec` once the item is grounded in the tree.

### 5 — Ensure `.local/todos/` exists

Create the directory if it does not exist.

### 6 — Report

- State the generated ID, assessed Priority and Order, with the impact/dependency reason.
- Report queue changes and the next eligible ready item or preparation step.
- Confirm the row was added to `.local/TODO.md`.
- Suggest next step: `/todo-spec <id>`
