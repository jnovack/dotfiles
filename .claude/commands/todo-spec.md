---
description: Turn a raw TODO item into a spec with acceptance criteria (asks clarifying questions if needed)
argument-hint: <id>
---

# /todo-spec

Turn a raw TODO item into a written spec by asking clarifying questions and writing a spec file.

## What to do

### 1 — Load the item

Read `TODO.md`. Find the row with the given ID.

- If the ID does not exist: report "ID not found in TODO.md." and stop.
- If status is not `raw`: report the current status and ask if the user wants to re-spec. If no, stop.

### 2 — Seed context

Check whether `.claude/todos/<id>.spec.md` already exists. If it does, read it as seed context.

Read the summary text from the TODO.md row as the starting description.

### 3 — Assess whether questions are needed

If the existing TODO.md row or seed spec already contains:

- A clear description of the current broken/missing state
- Observable acceptance criteria
- Any known dependencies or constraints

...then skip the questions, note that existing detail is sufficient, and proceed directly to writing the spec file. Tell the user what you inferred.

Otherwise, ask the following questions all at once — do not ask them one at a time:

1. **What breaks or is missing today?** Describe the current state — what fails, what's absent, what's inconsistent.
2. **What does done look like?** What can you run or observe that confirms it's complete?
3. **Are there dependencies?** Other TODO IDs or external work that must be done first?
4. **Any constraints?** Performance targets, API compatibility, backwards compat, scope limits.

Wait for the user's answers before writing the spec.

### 4 — Write the spec file

Write `.claude/todos/<id>.spec.md`:

```markdown
---
id: <ID>
status: spec'd
summary: <one-line summary>
created: <YYYY-MM-DD>
---

## What

<What is being built, fixed, or changed. Concrete and specific.>

## Why

<Why this matters. What breaks or degrades without it.>

## Acceptance Criteria

<Bulleted list. Each item is observable and testable.>

## Dependencies

<Other TODO IDs or external work this depends on. "None" if empty.>

## Constraints

<Scope limits, compatibility requirements, performance targets. "None" if empty.>
```

### 5 — Update TODO.md

Change the item's status from `raw` to `spec'd`.

### 6 — Report

Confirm the spec was written. Suggest next step: `/todo-plan <id>`
