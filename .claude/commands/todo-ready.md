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

Then run the loop-safety check and keep its output for the report:

```bash
~/.claude/bin/plan-loop-check .local/todos/<id>.plan.md
```

A `FAIL` does not block `ready`, because the operator can still run the item by hand. It
does mean `/todo-loop` will stop before this item, and this gate is where the operator
must learn that, not at 3am.

### 4 — Update .local/TODO.md

Verify its hard dependencies and external prerequisites first. `ready` is
approval of the plan, not a claim that it can run now, so one kind of unmet
prerequisite does not block it: a **pending** one, which is a TODO item that
is itself `ready` (or `in progress`/`done`) and sits earlier in the queue.
Readying a dependent ahead of it is what lets `/todo-loop` run a whole
dependency chain in one night instead of stopping after the first item.
Dispatch stays gated: `/todo-next` skips a ready item until its prerequisites
retire, and `/todo-checkpoint` step 6 re-anchors the dependent's plan when
each prerequisite retires, dropping it back to `planned` if that changes
approach, scope, Acceptance Criteria or Constraints.

Any other unmet prerequisite still blocks. If one is missing, cyclic,
external, or an item that is not yet `ready` or is ordered after this one,
retain `planned`, report the blocker, and stop; readiness does not override
it. Otherwise change `planned` to `ready`, reassess Priority and Order, and
renumber the queue under the shared policy. Do not promote unrelated items,
and never promote the pending prerequisite itself.

### 5 — Report

```text
<ID> — <summary>
Model:    <model>
Effort:   <Light|Medium|Heavy>
Priority: <P0|P1|P2|P3>
Order:    <N> — <priority/dependency reason>
Pending:  <prerequisite IDs it waits on, ahead of it in the queue, or "none">
Overview: <first sentence of plan overview>
Placement: <N reuse/extend; copies kept: <list, or "none">>
Unattended: yes
        or: NO — <each FAIL reason> — /todo-loop will stop before this item

Marked ready. Run /todo-next to execute.
```

On `NO`, add one line naming the fix: `/todo-plan <id>` to re-plan with a `## Commands`
section, or run this item by hand and schedule the loop with `--max-items` set to stop
before it.

Also report any queue changes and the next eligible ready item.

Copies kept are listed because this is the human gate: a duplication approved here
without being seen is the kind that accumulates.
