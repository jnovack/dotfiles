# TODO Skill System

A set of seven Claude Code slash commands for lifecycle-managed TODO tracking. Works in any repo. Every item moves
from a raw captured thought through spec, plan, execution, and validation — the same level of rigor as a formal
refactor step.

## Why this exists

Raw TODOs stall. There is no forcing function to clarify what "done" looks like, no plan specific enough to hand to a
subagent, and no checkpoint to confirm the work actually landed cleanly. This system provides all three.

## Lifecycle

```text
raw → spec'd → planned → ready → done
```

| Status | Meaning |
| --- | --- |
| raw | Captured. No spec yet. |
| spec'd | Clarified. Acceptance criteria written. |
| planned | Implementation steps and DoD defined. |
| ready | Plan reviewed. Cleared for execution. |
| done | Implemented. Checkpoint passed. |

## File layout

```text
~/.claude/commands/          <- these skill files (global, works in any repo)
  todo-add.md
  todo-spec.md
  todo-plan.md
  todo-ready.md
  todo-next.md
  todo-checkpoint.md
  todo-help.md

<repo>/
  TODO.md                    <- index table, machine-maintained
  .claude/todos/
    <ID>.spec.md             <- what, why, acceptance criteria
    <ID>.plan.md             <- how, model tag, DoD checklist
    <ID>.PROMPT.md           <- generated prompt for non-Claude models (if used)
```

## TODO.md format

```markdown
# TODO

| ID | Status | Summary |
| --- | --- | --- |
| FEAT-REGISTRY-01 | ready | Migrate service to RegistryRunner |
| TEST-SMOKE-01 | raw | Add smoke tests for get-* binaries |
```

The table is maintained by the skills. Do not edit status values by hand — use `/todo-ready` and let `/todo-next` and
`/todo-checkpoint` handle `done`.

## ID format

`CATEGORY-DESCRIPTOR-##` — for example `TEST-SMOKE-03`, `FEAT-REGISTRY-01`, `CI-DOCKER-02`.

`/todo-add` generates the ID automatically by scanning existing IDs for the highest numeral in the same
category-descriptor group.

Common categories: `TEST` `REFACTOR` `CI` `LOG` `FIX` `FEAT` `DOCS` `API` `DB` `WEB` `TASK`

## Commands

### `/todo-add <text>`

Capture a raw want. Generates an ID, creates `TODO.md` if it does not exist, appends a `raw` row. No sidecar files yet.

```text
/todo-add moxfall-service needs to migrate to RegistryRunner
→ REFACTOR-REGISTRY-01 added as raw
→ Next: /todo-spec REFACTOR-REGISTRY-01
```

### `/todo-spec <id>`

Asks clarifying questions in developer terms — what breaks, what does done look like, dependencies, constraints.
Writes `<id>.spec.md`. Bumps status to `spec'd`.

Skips questions if the TODO.md row already contains enough detail (e.g. items migrated from a narrative TODO list).

### `/todo-plan <id>`

Reads the spec. Writes `<id>.plan.md` with a numbered implementation plan, a model recommendation, and a DoD
checklist. Bumps status to `planned`.

The model recommendation follows this guide:

| Model | Work type |
| --- | --- |
| haiku | Mechanical — cleanup, config, simple tests |
| sonnet | Standard — features, refactors, multi-file changes |
| opus | Complex — architecture, deep analysis, ambiguous scope |

The user can edit the `model:` field to any value, including non-Claude models.

### `/todo-ready <id>`

Confirms the plan file exists and bumps status from `planned` to `ready`. This is the human review gate — run it
after you have read the plan and are satisfied with it.

### `/todo-next`

Picks the first `ready` item and executes it.

**Claude models (haiku/sonnet/opus):** Constructs a prompt from the spec and plan, spawns a subagent at the specified
model, reports a synopsis, and reminds you to run `/todo-checkpoint`.

**Non-Claude models:** Writes the raw prompt to `.claude/todos/<id>.PROMPT.md` and stops. Copy that file into your
external model session. When it finishes, run `/todo-checkpoint <id>`.

### `/todo-checkpoint [id]`

Validates the most recently completed item (or a specific ID) against the DoD:

**Core (always checked):**

- Tests pass (auto-detects `go test`, `make test`, `npm test`, `pytest`)
- Relevant docs updated if behavior changed
- No untracked technical debt (`// TODO` without a `TODO.md` entry)

**Optional (only items declared in the plan):**

- ADR created
- Migration notes
- API changelog
- Smoke tests

Reports `PASS`, `FAIL`, or `WARN` per criterion and an overall verdict.

### `/todo-help`

Prints a condensed reference of this entire system in the terminal.

## Definition of Done

The DoD has two tiers. The core tier is always required. The optional tier is declared per-item during planning — only
items explicitly included in the plan's checklist are checked at checkpoint time.

The spec and plan process is where optional items get surfaced. If the work warrants an ADR,
`/todo-plan` includes it. If it does not, it does not appear on the checklist and is not checked.

## Migrating an existing TODO list

If your repo already has a narrative TODO list, convert it to the index table format and run `/todo-spec <id>` on each
item. The skill will detect that the existing description is detailed enough and seed the spec file from it rather than
asking redundant questions.
