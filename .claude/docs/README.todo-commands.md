# TODO Skill System

A set of seven Claude Code slash commands for lifecycle-managed TODO tracking. Works in any repo. Every item moves
from a raw captured thought through spec, plan, execution, and validation — the same level of rigor as a formal
refactor step.

## Why this exists

Raw TODOs stall. There is no forcing function to clarify what "done" looks like, no plan specific enough to hand to a
subagent, and no checkpoint to confirm the work actually landed cleanly. This system provides all three.

## Lifecycle

```text
raw → spec'd → planned → ready → in progress → done → (row removed, files archived)
```

| Status | Meaning |
| --- | --- |
| raw | Captured. No spec yet. |
| spec'd | Clarified. Acceptance criteria written. |
| planned | Implementation steps and DoD defined. |
| ready | Plan reviewed. Cleared for execution. |
| in progress | Execution started, or a checkpoint failed. Needs work. |
| done | Implementer finished. Awaiting a checkpoint. |

`done` is the only transient status: it means the implementing agent believes the work
is complete, not that anything has verified it. A passing `/todo-checkpoint` **removes
the row** and moves the spec and plan into `.local/completed/`, so the index holds only
live work. Nothing is retired on the strength of an agent's own claim, and nothing that
passed lingers in the list.

Status lives in `.local/TODO.md` only — the spec and plan sidecar files carry no
status field, so there is nothing to drift out of sync.

`in progress` covers two different situations, told apart by whether the plan file
carries a `## Corrections` section. With one, the item failed a checkpoint and
`/todo-next <id>` will re-run it against those corrections. Without one, the item is
either still running or was abandoned mid-flight.

## File layout

Everything the todo system writes lives under `.local/` — gitignored,
ephemeral, per-repo working state. Nothing it creates is meant to be
committed.

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
  .local/
    TODO.md                  <- index table of LIVE work only, machine-maintained
    todos/
      <ID>.spec.md           <- what, why, acceptance criteria
      <ID>.plan.md           <- how, model tag, DoD checklist, baseline/reviewed SHAs
    completed/
      <ID>.spec.md           <- moved here by a passing /todo-checkpoint
      <ID>.plan.md
    <ID>.PROMPT.md           <- generated prompt for non-Claude models (if used)
```

If the repo's root `.gitignore` does not already ignore `.local/**`, `/todo-add`
creates `.local/.gitignore` (`*` / `!.gitignore`) the first time it runs.

## .local/TODO.md format

```markdown
# TODO

| ID | Status | Effort | Summary |
| --- | --- | --- | --- |
| FEAT-REGISTRY-01 | ready | Medium | Migrate service to RegistryRunner |
| TEST-SMOKE-01 | raw | — | Add smoke tests for get-* binaries |
```

The table is maintained by the skills. Do not edit status values by hand — use `/todo-ready` and let `/todo-next` and
`/todo-checkpoint` handle `done`.

## Effort

`Effort` estimates how much code, time, and token budget executing the item
takes — **not** how hard the reasoning is. That distinction matters: reasoning
difficulty is the `model:` tag in the plan file, and the two often diverge. A
large mechanical rename is `Heavy` effort on the `haiku` model; a subtle
one-line concurrency fix is `Light` effort on `opus`.

| Effort | Shape |
| --- | --- |
| Light | A few lines across one or two files. Doc/config fixes, a targeted change on an established pattern, dead-code deletion. Quick, low token cost. |
| Medium | A non-trivial change across several files, or one whole component. Some design work. |
| Heavy | Lots of code and lots of thinking — cross-cutting, multi-component, a migration or reindex, or cross-repo coordination. Often better handled on the refactor track than in one todo pass. |
| — | Not yet sized. Every `raw` item; filled in at `/todo-spec`. |

`/todo-add` writes `—`. `/todo-spec` sets the estimate once the item is grounded
in the tree. `/todo-plan` revises it if enumerating the steps shows the item is
bigger or smaller than the spec read.

## ID format

`CATEGORY-DESCRIPTOR-##` — for example `TEST-SMOKE-03`, `FEAT-REGISTRY-01`, `CI-DOCKER-02`.

`/todo-add` generates the ID automatically by scanning existing IDs for the highest numeral in the same
category-descriptor group.

Common categories: `TEST` `REFACTOR` `CI` `LOG` `FIX` `FEAT` `DOCS` `API` `DB` `WEB` `TASK`

## Commands

### `/todo-add <text>`

Capture a raw want. Generates an ID, creates `.local/TODO.md` if it does not exist, appends a `raw` row with `Effort` `—`. No sidecar files yet.

```text
/todo-add moxfall-service needs to migrate to RegistryRunner
→ REFACTOR-REGISTRY-01 added as raw
→ Next: /todo-spec REFACTOR-REGISTRY-01
```

### `/todo-spec <id>`

Asks clarifying questions in developer terms — what breaks, what does done look like, dependencies, constraints.
Writes `<id>.spec.md`. Bumps status to `spec'd` and sets the `Effort` column now that the item is grounded in the tree.

Skips questions if the .local/TODO.md row already contains enough detail (e.g. items migrated from a narrative TODO list).

Grounds the spec in the tree before writing it — the row's stated diagnosis is a hypothesis, not a finding — then runs
a sonnet verification pass over the finished spec. That pass checks two things: every factual claim about the repo
(paths, symbols, caller counts, "X appears nowhere"), and the preconditions the prescribed approach depends on but
never states. The second is what earns it: every claim in a spec can be true while the approach still cannot run.

### `/todo-plan <id>`

Reads the spec. Writes `<id>.plan.md` with a numbered implementation plan, a model recommendation, and a DoD
checklist. Bumps status to `planned`, and revises the `Effort` column if writing the concrete steps shows the item
is bigger or smaller than the spec read.

Anchors every cited path, symbol and signature against the current tree before writing, then runs a sonnet
verification pass: do the anchors resolve, is each step executable in order, and do the steps cover the spec's
Acceptance Criteria. `/todo-next` dispatches this file verbatim, so an error here is inherited as instruction.

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

### `/todo-next [id]`

Runs the given `ready` item, or the first `ready` item if no ID is provided.
Marks the item `in progress` in `.local/TODO.md` before dispatching, so a crashed or
abandoned run is visible.

**Claude models (haiku/sonnet/opus):** Constructs a prompt from the spec and plan, spawns a subagent at the specified
model, then — once it returns — verifies the bookkeeping, re-runs the tests itself, and
spawns a **second, separate** Opus subagent to review what the first one wrote. It
adjudicates those findings, records a `reviewed:` SHA in the plan, and reports the review
outcome alongside the synopsis. The item you get back has already had its obvious defects
removed, rather than leaving them for a hand-run `/review` to find later.

**Non-Claude models:** Writes the raw prompt to `.local/<id>.PROMPT.md` and stops. Copy that file into your
external model session. When it finishes, run `/todo-checkpoint <id>`.

### `/todo-checkpoint <id>`

Validates a completed item against the DoD. The ID is required — with no
argument it lists the `done` and `in progress` items and stops.

**It reviews whatever `/todo-next` has not already reviewed.** The main review happens in
`/todo-next`, right after the implementer stops; this command reads the `reviewed:` SHA
from the plan and reviews only what changed since — usually just the fixes adjudicated
there, and nothing at all if you went straight to checkpoint. With no marker (a
non-Claude item, or one implemented by hand) it runs the full review itself. Either way
the review comes *before* the tests, because adjudicating a finding changes code and the
test run has to validate the tree that will actually be committed. If you already ran
`/review` by hand, the existing `.local/REVIEW.md` is used instead of spawning a pass.

Reviews run in a **new** subagent, never the one that wrote the code — an agent
re-reading its own work sees the intent it had while writing, not the sentence on the
page. And each command runs **one** round: every fix is new code, so "review until clean"
never terminates. Two rounds over shrinking surfaces, spread across the two commands, is
where the yield flattens.

The change set comes from the `baseline:` SHA `/todo-next` writes into the plan file at
dispatch, so it is the same whether you checkpoint before committing, after committing,
or halfway through. Without a baseline the checkpoint falls back to uncommitted work,
then to locating the item's commit, and only then to reading whole files — reporting
which it used rather than degrading silently.

An ordinary defect found here is fixed in place and does not fail the checkpoint — that
is the process working. A finding that reveals a violated Constraint or a missed
Acceptance Criterion is a FAIL.

**Core (always checked):**

- Code review findings adjudicated
- Tests pass (auto-detects `go test`, `make test`, `npm test`, `pytest`), plus any
  additional suite the plan names
- Every acceptance criterion in the spec met
- Relevant docs updated if behavior changed
- No untracked technical debt (`// TODO` without a `.local/TODO.md` entry)

**Optional (only items declared in the plan):**

- ADR created
- Migration notes
- API changelog
- Smoke tests

Reports `PASS`, `FAIL`, or `WARN` per criterion and an overall verdict. On
`FAIL` the item's status rolls back to `in progress` — the index never claims
success for work that failed its checkpoint — and a `## Corrections` section is written
into the plan file naming each thing that must become true. That section is the only
channel that reaches the retry: `/todo-next` builds its prompt from the spec and plan
and never sees the checkpoint report, so a correction recorded only in chat is one the
next run is guaranteed to miss. A passing checkpoint deletes the section.

On `PASS` the item is **retired**, not marked done: the row is removed from
`.local/TODO.md` and `<ID>.spec.md` / `<ID>.plan.md` move to `.local/completed/`. A
generated `<ID>.PROMPT.md` is deleted rather than archived, being derived from the two
files that were just kept. Other rows frequently cite a retired ID for context — those
references stay resolvable against `.local/completed/`, so do not rewrite them or clear
the directory to tidy up.

### `/todo-help`

Prints a condensed reference of this entire system in the terminal.

## Definition of Done

The DoD has two tiers. The core tier is always required. The optional tier is declared per-item during planning — only
items explicitly included in the plan's checklist are checked at checkpoint time.

The spec and plan process is where optional items get surfaced. If the work warrants an ADR,
`/todo-plan` includes it. If it does not, it does not appear on the checklist and is not checked.

## Migrating an existing TODO list

If your repo already has a narrative TODO list, convert it to the index table format (including the `Effort` column —
use `—` for anything you cannot size at a glance) and run `/todo-spec <id>` on each item. The skill will detect that
the existing description is detailed enough and seed the spec file from it rather than asking redundant questions, and
it fills in `Effort` as it specs each one.
