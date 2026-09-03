---
description: Turn a raw TODO item into a spec with acceptance criteria (asks clarifying questions if needed)
argument-hint: <id>
---

# /todo-spec

Turn a raw TODO item into a written spec by asking clarifying questions and writing a spec file.

## What to do

### 1 — Load the item

Read `.local/TODO.md`. Find the row with the given ID.

- If the ID does not exist: report "ID not found in .local/TODO.md." and stop.
- If status is not `raw`: report the current status and ask if the user wants to re-spec. If no, stop.

### 2 — Seed context

Check whether `.local/todos/<id>.spec.md` already exists. If it does, read it as seed context.

Read the summary text from the .local/TODO.md row as the starting description.

### 3 — Assess whether questions are needed

If the existing .local/TODO.md row or seed spec already contains:

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

### 4 — Ground the spec in the tree before writing it

A spec is a set of claims about a codebase. Write it from what the tree says,
not from what the TODO row asserts — the row was written by whoever noticed the
symptom, often from a single failure message, and its diagnosis is a hypothesis.

Before drafting, resolve every claim you intend to make: open the files, grep
for the symbols, count the callers, read the commit that changed it. Where the
row proposes a root cause, confirm or refute it rather than restating it. A row
that offers two shapes ("a real regression, or a stale test") is naming its own
uncertainty — that uncertainty is yours to remove here, not to pass downstream.

Ask the user only what the tree cannot answer. A root cause is discoverable; a
product decision — whether a removed capability should come back — is not.

### 5 — Write the spec file

Write `.local/todos/<id>.spec.md`:

```markdown
---
id: <ID>
summary: <one-line summary>
created: <YYYY-MM-DD>
---
<!-- Status lives in .local/TODO.md only — never here. -->

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

### 6 — Verify the spec against the tree

A wrong spec is the most expensive failure in this workflow, because nothing
downstream catches it. `/todo-plan` transforms the spec without checking it;
`/todo-next`'s reviewer and `/todo-checkpoint` both judge the implementation
*against* the spec. A spec that misstates the tree therefore produces faithful
wrong work that passes every gate. The only other check is the human at
`/todo-ready`, and they are reading prose, not running greps.

Spawn **one `general-purpose` subagent on `model: sonnet`, in the foreground**,
report-only. This is mechanical checking, not judgement — do not spend opus on
it, and do not let it redesign the item.

Give it the spec file path, the repo root, and exactly two jobs:

1. **Check every factual claim about the repository.** File paths, line
   numbers, symbol names, caller counts, commit SHAs, "X appears nowhere",
   "Y has zero callers", "Z was removed in <sha>", claims about what a helper
   or fixture does. Verify each against the tree and report it as
   **VERIFIED**, **FALSE** (with what the tree actually says), or
   **UNVERIFIABLE** (with what it tried). Line numbers drift — a symbol that
   exists at a different line is VERIFIED with a note, not FALSE.

2. **Find the preconditions the spec depends on but never states.** Walk the
   prescribed approach step by step and ask what has to already be true for it
   to work: a test helper that stubs the right endpoint, a fixture that carries
   the field a render is gated on, a flag already threaded to the call site, an
   index that already exists. Report each unstated precondition and whether it
   currently holds.

   This second job is the one that earns the pass. Every claim in a spec can be
   individually true while the approach still cannot run, and that failure is
   invisible until an implementing agent hits it — having been told by the
   spec's own Constraints not to change the thing that blocks it.

Tell it plainly that an empty report is an acceptable outcome, that it must not
edit any file, and that it should not propose scope changes, better approaches,
or style improvements — only false claims and unstated preconditions.

**Then adjudicate its report yourself.** Confirm each finding against the tree
before acting: the verifier is making claims too. Correct the spec for what
survives — including the **Constraints** section, which is where an unstated
precondition usually turns into an instruction that forbids fixing it. If a
finding would change the item's scope rather than its accuracy, raise it with
the user instead of quietly widening the spec.

Do not spawn a second verification round over your own corrections. One round,
then the human gate at `/todo-ready`.

### 7 — Estimate Effort

Now that the item is grounded in the tree, size it. **Effort is how much code,
time, and token budget executing the item will take — not how hard the reasoning
is** (that is the model tag, set at `/todo-plan`). A large mechanical rename is
heavy effort on a light model; a subtle concurrency fix is the reverse.

| Effort | Shape |
| --- | --- |
| Light | A few lines across one or two files. Doc fixes, config, a targeted change with an established pattern, deleting dead code. Quick to execute, low token cost. |
| Medium | A non-trivial change across several files, or one whole component. Some design work. New feature of bounded scope, a contained refactor. |
| Heavy | Lots of code and lots of thinking. Cross-cutting or multi-component, a new subsystem, an index reindex/migration, or cross-repo coordination. High token cost — often a candidate for the refactor track instead of a single todo pass. |

Record the estimate. `/todo-plan` revises it if enumerating the steps changes
the picture.

### 8 — Update .local/TODO.md

Change the item's status from `raw` to `spec'd`, and set the `Effort` column to
the estimate from step 7. If the table has no `Effort` column yet (an older
file), add it — header, separator, and every existing row (`—` where you cannot
size a row at a glance).

### 9 — Report

Confirm the spec was written. State the Effort estimate and one line of why.
State what the verification pass found — claims corrected, preconditions added,
or "clean" — and name anything left as a known risk. Suggest next step:
`/todo-plan <id>`
