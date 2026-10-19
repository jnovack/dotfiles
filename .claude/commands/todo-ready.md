---
description: Mark a planned TODO item as ready for execution (the human review gate)
argument-hint: <id>
model: haiku
---

# /todo-ready

Mark a planned TODO item as ready for execution after the user has reviewed the plan.

Before any successful tracker update or default queue selection, read and apply
[Priority and order](../docs/README.todo-commands.md#priority-and-order).
It defines the table schema, priority assessment, dependency checks, stable
ordering and reporting. Invalid invocations that stop at a gate stay read-only.

## What to do

### 1 — Load the item

Read `.local/TODO.md`. Find the row with the given ID.

- If not found: report "ID not found in .local/TODO.md." and stop.
- If status is `ready`: report "Already marked ready." and stop.
- If status is `in progress`: report "Item is in progress — execution has started or a checkpoint failed. Finish the work and run `/todo-checkpoint <id>`." Stop.
- If status is `done`: report "Already done." and stop.
- If status is `spec'd` or `raw`: report the current status and suggest the appropriate prior step (`/todo-plan` or `/todo-spec`). Stop.
- If status is `planned`: proceed.

### 2 — Confirm the plan file exists

Check for `.local/todos/<id>.plan.md`.

- If missing: report "No plan file found. Run `/todo-plan <id>` first." and stop.

### 3 — Read the plan

Extract from the plan file:

- `model:` field
- Overview section (first sentence)
- `## Placement` section: count the rows that reuse or extend existing code, and list
  every row kept as a copy (a plan written before the section existed has none — report
  "not recorded")

Also read the `Effort` value from the item's `.local/TODO.md` row.

### 4 — Update .local/TODO.md

Verify its hard dependencies and external prerequisites first. If any are
unmet, missing or cyclic, retain `planned`, report the blocker, and stop;
readiness does not override prerequisites. Otherwise change `planned` to
`ready`, reassess Priority and Order, and renumber the queue under the shared
policy. Do not promote unrelated items.

### 5 — Report

```text
<ID> — <summary>
Model:    <model>
Effort:   <Light|Medium|Heavy>
Priority: <P0|P1|P2|P3>
Order:    <N> — <priority/dependency reason>
Overview: <first sentence of plan overview>
Placement: <N reuse/extend; copies kept: <list, or "none">>

Marked ready. Run /todo-next to execute.
```

Also report any queue changes and the next eligible ready item.

Copies kept are listed because this is the human gate: a duplication approved here
without being seen is the kind that accumulates.
