---
description: Capture a raw TODO item with a generated ID and append it to TODO.md
argument-hint: <description>
---

# /todo-add

Capture a raw TODO item with a generated ID and append it to the repo's `TODO.md` index.

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

- Read `TODO.md` (if it exists) and collect all IDs in the table.
- List all filenames in `.claude/todos/` (if the directory exists).
- Find all existing IDs that share the same `CATEGORY-DESCRIPTOR-` prefix.
- Take the highest numeral found. New ID numeral = highest + 1, zero-padded to 2 digits.
- If no existing IDs share the prefix, start at `01`.

Final format: `CATEGORY-DESCRIPTOR-##` (e.g. `TEST-SMOKE-03`, `FEAT-REGISTRY-01`).

### 3 — Ensure TODO.md exists

If `TODO.md` does not exist in the repo root, create it:

```markdown
# TODO

| ID | Status | Summary |
| --- | --- | --- |
```

### 4 — Append the row

Add a new row to the table:

```text
| <ID> | raw | <description, truncated to ~80 chars> |
```

### 5 — Ensure `.claude/todos/` exists

Create the directory if it does not exist.

### 6 — Report

- State the generated ID.
- Confirm the row was added to `TODO.md`.
- Suggest next step: `/todo-spec <id>`
