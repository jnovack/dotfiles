---
description: Capture a raw TODO item with a generated ID and append it to .local/TODO.md
argument-hint: <description>
model: haiku
---

# /todo-add

Capture a raw TODO item with a generated ID and append it to the repo's `.local/TODO.md` index.

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
- List all filenames in `.local/todos/` (if the directory exists).
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

| ID | Status | Effort | Summary |
| --- | --- | --- | --- |
```

If `.local/TODO.md` exists but its table has no `Effort` column (an older file),
add the column to the header, the separator, and every existing row — use `—`
for rows you cannot size at a glance.

### 4 — Append the row

Add a new row to the table:

```text
| <ID> | raw | — | <description, truncated to ~80 chars> |
```

`Effort` starts as `—`. It is a guess at how much code, time, and token budget
the item needs to execute — not how hard the reasoning is — and it is filled in
by `/todo-spec` once the item is grounded in the tree.

### 5 — Ensure `.local/todos/` exists

Create the directory if it does not exist.

### 6 — Report

- State the generated ID.
- Confirm the row was added to `.local/TODO.md`.
- Suggest next step: `/todo-spec <id>`
