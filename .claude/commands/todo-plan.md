---
description: Turn a spec'd TODO item into an implementation plan with a model tag and DoD checklist
argument-hint: <id>
---

# /todo-plan

Turn a spec'd TODO item into an implementation plan with a model tag and DoD checklist.

## What to do

### 1 — Load the spec

Read `.local/todos/<id>.spec.md`.

- If the file does not exist: report "No spec found for <id>. Run `/todo-spec <id>` first." and stop.

Read `.local/TODO.md` and check the item's status:

- `raw`: suggest running `/todo-spec <id>` first and stop.
- `planned`, `ready`, `in progress`, or `done`: report the current status and ask if the user wants to re-plan. If no, stop.
- `spec'd`: proceed.

### 2 — Recommend a model

Choose based on the complexity described in the spec:

| Complexity | Model |
| --- | --- |
| Mechanical — doc updates, renaming, cleanup, config, simple test additions | haiku |
| Standard implementation — new features, refactors, multi-file changes | sonnet |
| High complexity — cross-cutting architectural changes, ambiguous requirements, deep analysis | opus |

Record this as the `model:` field. The user can edit the plan file to override, including setting a non-Claude model (e.g. `codex`, `gemini`).

**Model is not Effort.** Model is how hard the reasoning is; the `Effort` column
in `.local/TODO.md` (set by `/todo-spec`) is how much code, time, and token
budget the work takes. They often align but not always — a big mechanical rename
is `haiku` + `Heavy`; a one-line concurrency fix is `opus` + `Light`. Do not
copy one from the other.

### 3 — Anchor the steps in the current tree

Steps are executed later, by an agent that trusts them. Every file path, symbol
name, type signature, and line number you write is an instruction it will
follow without checking. Open each file you cite and confirm the anchor before
writing the step. Cite symbol names alongside line numbers — a line number is a
snapshot and the symbol is the durable reference.

Where the spec's approach depends on something existing (a helper, a fixture, a
field, an interface), name it in the step with its actual location, not as a
description the executing agent has to resolve on its own.

### 3b — Decide placement for the project, not the neighborhood

The implementing agent sees the spec, the plan and the files it opens. Left to itself
it puts new code next to its caller, copies the nearest similar code, and adds one more
entry to whatever hand-maintained list it touches. Each choice is locally reasonable;
across many items they produce a project of near-duplicate functions with no coherent
shape. The plan is the cheapest place to decide where code belongs.

For each function, type, constant, file or list entry the Steps will add or move:

1. **Search for an existing near-equivalent first** — the code graph's semantic search
   where the repo has one, then grep by behavior rather than by name. If one exists, the
   step extends or reuses it.
2. **Place it in the module that owns the concern**, per the conventions file's
   architecture rules and the modules around it. A helper whose siblings live in a
   shared package goes there, even when only one caller exists today.
3. **Apply the rule of three.** A step that copies an existing block, "mirrors" another
   component, or adds the third or later hand-maintained copy of a list, constant or
   mapping must either extract the shared piece (as an earlier step) or record why the
   copy stays, plus the test that keeps the copies aligned. "The original is unexported"
   or "lives in another package" is not a reason by itself — exporting or moving it is
   usually the smaller long-term change. If a spec **Constraint** forbids touching the
   original, ask the user rather than defaulting to the copy.

Record the decisions in the plan's `## Placement` section. An extraction larger than
the item can absorb is a new TODO (`/todo-add`), named in the report, not a silent copy.

### 4 — Write the plan file

Write `.local/todos/<id>.plan.md`:

```markdown
---
id: <ID>
model: <haiku|sonnet|opus>
created: <YYYY-MM-DD>
---
<!-- Status lives in .local/TODO.md only — never here. -->
<!-- /todo-next adds `baseline: <sha>` to the frontmatter when it dispatches;
     /todo-checkpoint reads it to find this item's change set. Do not set it here. -->

## Overview

<1–3 sentence summary of the approach.>

## Steps

<Numbered implementation steps. Specific enough that a subagent can execute without inventing
type signatures, method names, or file paths.>

## Placement

<From step 3b. "None — modifies existing code only." when nothing is added or moved.>

| New or moved | Lives in | Reuses / extends | Why not shared (or: shared) |
| --- | --- | --- | --- |
| `<symbol or file>` | `<path>` | `<existing helper>` | <reason> |

<The implementer appends a row for anything it adds that this table did not anticipate,
and for any file it changed outside the Steps for placement.>

## DoD Checklist

### Core (always required)
- [ ] Tests pass
- [ ] Relevant docs updated if behavior changed (README, API docs, doc.go, etc.)
- [ ] No untracked technical debt — no new `// TODO` or `// FIXME` without a corresponding .local/TODO.md entry

### Optional (delete any that do not apply to this item)
- [ ] ADR created in docs/decisions/
- [ ] Migration notes written
- [ ] API changelog updated
- [ ] Smoke tests added or updated
```

Remove the optional items that are not relevant. Include only those that the spec's scope warrants.

### 5 — Verify the plan against the tree

The plan is where a spec's approach becomes concrete enough to be wrong in
mechanical ways: an anchor that has drifted, a symbol that was renamed, a
signature that does not match, a step whose prerequisite the previous step never
produces. `/todo-next` dispatches this file verbatim, so an error here is an
error the implementing agent inherits as instruction.

Spawn **one `general-purpose` subagent on `model: sonnet`, in the foreground**,
report-only. Give it the plan file, the spec file, and the repo root, with four
jobs:

1. **Resolve every anchor.** For each file path, symbol, signature, and line
   number cited in the Steps: does it exist, and does it say what the step
   assumes? Report **VERIFIED**, **DRIFTED** (exists, different location or
   shape — give the current one), or **MISSING**.

2. **Check each step is executable in order.** Does any step depend on a state
   no earlier step establishes? Does any step prescribe an API, helper, or test
   harness that cannot do what the step needs? Does every validation or DoD command
   work as written and match something (dry-run it where that is non-mutating:
   `make -n`, `go test -list`, a grep)? Name the step number.

3. **Check the plan covers the spec's Acceptance Criteria.** Every criterion
   should be reachable by following the Steps. Report any criterion no step
   produces, and any step that goes beyond the spec's scope.

4. **Check placement.** For each Placement row and each step that adds code: does an
   existing near-equivalent already do the job (search by behavior, not name)? Is the
   location the module that owns the concern? Report every copy, "mirror" or
   third-copy step without a recorded decision, and every copy justified only by
   visibility ("unexported", "other package").

Tell it that an empty report is an acceptable outcome, that it must not edit any
file, and that it must not propose a different approach — the approach was
settled in the spec. Placement is not approach: where code lives is in scope, what
it does is not. It reports mechanical defects in the plan, not opinions about it.

**Then adjudicate the report yourself**, confirming each finding against the
tree before correcting the plan. A finding that reveals the *spec's* approach
cannot work is not a plan fix: say so and send the item back to `/todo-spec`
rather than quietly redesigning it here.

One verification round. Do not re-spawn over your own corrections.

### 6 — Update .local/TODO.md

Change the item's status from `spec'd` to `planned`.

Re-check the `Effort` column against the enumerated Steps. `/todo-spec` set it
from the grounded spec; if writing the concrete steps revealed the item is
larger or smaller than it read (more files touched than expected, a migration
the spec did not call out, or conversely a change that collapsed to a few
lines), update the value. Note the change in the report if you make one.

### 7 — Report

- Confirm the plan was written.
- State the recommended model and briefly explain why.
- State the Effort value, and whether the plan revised it from `/todo-spec`'s estimate.
- List which optional DoD items were included and why.
- State the placement decisions: what reuses existing code, what is extracted, what
  stays a copy and why, and any follow-up TODOs added.
- State what the verification pass found — anchors corrected, steps reordered,
  or "clean" — and name anything left as a known risk.
- Suggest next step: review the plan file and run `/todo-ready <id>` when satisfied.
