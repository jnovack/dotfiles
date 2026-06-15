# /todo-plan

Turn a spec'd TODO item into an implementation plan with a model tag and DoD checklist.

## What to do

### 1 — Load the spec

Read `.claude/todos/<id>.spec.md`.

- If the file does not exist: report "No spec found for <id>. Run `/todo-spec <id>` first." and stop.

Read `TODO.md` and check the item's status:

- `raw`: suggest running `/todo-spec <id>` first and stop.
- `planned`, `ready`, or `done`: report the current status and ask if the user wants to re-plan. If no, stop.
- `spec'd`: proceed.

### 2 — Recommend a model

Choose based on the complexity described in the spec:

| Complexity | Model |
| --- | --- |
| Mechanical — doc updates, renaming, cleanup, config, simple test additions | haiku |
| Standard implementation — new features, refactors, multi-file changes | sonnet |
| High complexity — cross-cutting architectural changes, ambiguous requirements, deep analysis | opus |

Record this as the `model:` field. The user can edit the plan file to override, including setting a non-Claude model (e.g. `codex`, `gpt-4o`).

### 3 — Write the plan file

Write `.claude/todos/<id>.plan.md`:

```markdown
---
id: <ID>
status: planned
model: <haiku|sonnet|opus>
created: <YYYY-MM-DD>
---

## Overview

<1–3 sentence summary of the approach.>

## Steps

<Numbered implementation steps. Specific enough that a subagent can execute without inventing
type signatures, method names, or file paths.>

## DoD Checklist

### Core (always required)
- [ ] Tests pass
- [ ] Relevant docs updated if behavior changed (README, API docs, doc.go, etc.)
- [ ] No untracked technical debt — no new `// TODO` or `// FIXME` without a corresponding TODO.md entry

### Optional (delete any that do not apply to this item)
- [ ] COVERAGE.md entry added with test command, paths, result, and date
- [ ] ADR created in docs/decisions/
- [ ] Migration notes written
- [ ] API changelog updated
- [ ] Smoke tests added or updated
```

Remove the optional items that are not relevant. Include only those that the spec's scope warrants.

### 4 — Update TODO.md

Change the item's status from `spec'd` to `planned`.

### 5 — Report

- Confirm the plan was written.
- State the recommended model and briefly explain why.
- List which optional DoD items were included and why.
- Suggest next step: review the plan file and run `/todo-ready <id>` when satisfied.
