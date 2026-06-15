# /todo-ready

Mark a planned TODO item as ready for execution after the user has reviewed the plan.

## What to do

### 1 — Load the item

Read `TODO.md`. Find the row with the given ID.

- If not found: report "ID not found in TODO.md." and stop.
- If status is `ready`: report "Already marked ready." and stop.
- If status is `done`: report "Already done." and stop.
- If status is `spec'd` or `raw`: report the current status and suggest the appropriate prior step (`/todo-plan` or `/todo-spec`). Stop.
- If status is `planned`: proceed.

### 2 — Confirm the plan file exists

Check for `.claude/todos/<id>.plan.md`.

- If missing: report "No plan file found. Run `/todo-plan <id>` first." and stop.

### 3 — Read the plan

Extract from the plan file:

- `model:` field
- Overview section (first sentence)

### 4 — Update TODO.md

Change the item's status from `planned` to `ready`.

### 5 — Report

```text
<ID> — <summary>
Model:    <model>
Overview: <first sentence of plan overview>

Marked ready. Run /todo-next to execute.
```
