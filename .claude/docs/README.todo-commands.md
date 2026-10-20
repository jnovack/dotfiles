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
      <ID>.plan.md           <- how, placement, model tag, DoD checklist, baseline/reviewed SHAs
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

| Order | Priority | ID | Status | Effort | Summary |
| --- | --- | --- | --- | --- | --- |
| 1 | P1 | FEAT-REGISTRY-01 | ready | Medium | Migrate service to RegistryRunner |
| 2 | P2 | TEST-SMOKE-01 | raw | — | Add smoke tests for get-* binaries |
```

The table is maintained by the skills. Do not edit status values by hand — use `/todo-ready` and let `/todo-next` and
`/todo-checkpoint` handle `done`.

## Priority and order

This is the shared policy for every TODO command. `.local/TODO.md` owns
`Priority` and `Order`, alongside status and effort; do not mirror these fields
into spec/plan frontmatter. Read columns by header name, not fixed positions.
Lifecycle status, priority, effort and model choice are independent.

| Priority | Meaning |
| --- | --- |
| P0 | Urgent: active outage, confirmed critical security exposure or imminent data loss. Requires concrete evidence or an explicit operator assignment. |
| P1 | High: confirmed correctness or reliability defect with material operator impact, or an explicit near-term commitment. |
| P2 | Normal: useful feature work, prevention, maintainability and ordinary documentation work. Default when urgency is unknown. |
| P3 | Low: optional polish, speculative work or explicitly deferred improvements. |

Assess impact, urgency, known failures, dependencies and operator intent from
the description, current tree and available sidecars. Do not invent evidence
or infer priority from category, effort, age or lifecycle status. A raw item
can be P1, and a ready item can be P3. Preserve explicit operator priorities
and sequencing; do not silently override them. If new evidence conflicts with
an explicit assignment, report it and ask before changing that assignment.

### Assess and maintain the queue

1. Re-read the current tracker before writing; preserve unrelated edits and
   all existing IDs, summaries, effort and statuses except the command's own
   authorized lifecycle transition. Add missing `Order`, `Priority` or
   `Effort` columns once for older trackers. Preserve existing priority values;
   assess missing ones, using P2 when evidence is insufficient. Keep prior row
   order as the tie-breaker. Never clear a tracker to recreate its table.
2. Check explicit prerequisites in active specs/plans and raw-item summaries;
   contextual references and file overlap alone are not blockers. A retired
   ID resolves through `.local/completed/`; verify its completion evidence.
   A `done` row still awaits checkpoint and is not a satisfied prerequisite.
   Missing IDs, dependency cycles and unmet external conditions remain
   blockers; record them rather than guessing that they are resolved.
3. Put hard prerequisites before their dependents even when their stated
   priority is lower. Among independent items, place P0 before P1 before P2
   before P3. Within a priority, put actionable work before externally blocked
   work, then preserve existing relative order. Honor explicit operator
   sequencing. File overlap alone is not a hard dependency, but record a
   chosen serial sequence when overlapping changes would stale each other.
4. `Order` is the recommended total queue, numbered 1..N with no gaps or
   duplicates; physically arrange rows in that order. Keep concise
   `## Ordering notes` in TODO.md for priority reasons, explicit overrides,
   dependencies and unresolved blockers, naming the affected IDs. These notes
   explain exceptions; specs remain the behavioral authority. If dependencies
   conflict or form a cycle, preserve those items' relative order, report the
   conflict and block their dispatch; the queue is not proof of eligibility.
5. After every successful add, spec, plan, ready, dispatch, implementation
   completion, checkpoint failure or retirement, reassess affected priorities
   and the remaining queue. New findings go through the same assessment as
   other additions. On retirement, remove the row, resolve its dependency
   notes against the archived evidence, and renumber remaining rows. Keep
   historical references and existing sidecars intact. Never mark another
   item ready/done or retire it merely because it moved or became unblocked.
   Reordering does not interrupt or restart an in-progress item.
6. Report the affected item's priority and order, any changed priorities or
   sequencing and why, and the next eligible ready item (or the lowest-Order
   item needing spec/plan/review if none is eligible). If nothing changed,
   say the assessment retained the queue. Do not execute another item as part
   of reassessment.

### Select work

For `/todo-next` without an ID, select the ready item with the smallest
`Order` whose hard dependencies and external prerequisites are verified
satisfied. A higher-priority raw/planned/blocked item does not prevent a lower
ready eligible item from running. Skip in-progress/done items by default.
An explicit ID overrides queue position, not readiness or prerequisites;
the existing failed-checkpoint retry is still allowed only with Corrections.
If ready items exist but are all blocked, report their blockers and stop.
If none are ready, report the next preparation step without promoting or
executing anything. After a checkpoint, recompute selection from the updated
queue rather than retaining the next ID captured before retirement.

Examples: adding a confirmed P1 defect places it before independent P2 work;
equally urgent additions retain existing tie order. A P2 prerequisite stays
before its P1 dependent. Retiring that prerequisite removes its row and
renumbers the queue; its dependent retains its current lifecycle status.
Reprioritizing a raw item never makes it executable.

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

Capture a raw want. Generates an ID, creates `.local/TODO.md` if it does not exist, inserts a `raw` row with `Effort` `—`, an assessed priority and queue order. No sidecar files yet.

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
It also writes Constraints with placement in mind: a constraint forbidding changes to a shared helper forces a copy, so
it is kept only when genuinely required, with its reason.

### `/todo-plan <id>`

Reads the spec. Writes `<id>.plan.md` with a numbered implementation plan, a model recommendation, and a DoD
checklist. Bumps status to `planned`, and revises the `Effort` column if writing the concrete steps shows the item
is bigger or smaller than the spec read.

Anchors every cited path, symbol and signature against the current tree before writing, and records a `## Placement`
section: where each new symbol lives and what existing code it reuses, with a rule of three on copies (see *Keeping
the project cohesive*). Then it runs a sonnet verification pass: do the anchors resolve, is each step executable in
order (including whether its validation commands match anything), do the steps cover the spec's Acceptance Criteria,
and does the placement hold up. `/todo-next` dispatches this file verbatim, so an error here is inherited as
instruction.

The model recommendation follows this guide:

| Model | Work type |
| --- | --- |
| haiku | Mechanical — cleanup, config, simple tests |
| sonnet | Standard — features, refactors, multi-file changes |
| opus | Complex — architecture, deep analysis, ambiguous scope |

The user can edit the `model:` field to any value, including non-Claude models.

### `/todo-ready <id>`

Confirms the plan file exists and bumps status from `planned` to `ready`. This is the human review gate — run it
after you have read the plan and are satisfied with it. Its report lists every copy the plan keeps, so a duplication
is approved deliberately rather than unseen.

### `/todo-next [id]`

Runs the given eligible `ready` item, or the eligible `ready` item with the smallest `Order` if no ID is provided.
Marks the item `in progress` in `.local/TODO.md` before dispatching, so a crashed or
abandoned run is visible.

**Claude models (haiku/sonnet/opus):** Constructs a prompt from the spec and plan, spawns a subagent at the specified
model, then — once it returns — verifies the bookkeeping, re-runs the tests itself, and
spawns a **second, separate** subagent to review what the first one wrote (sonnet for
`Light`/`Medium` Effort, opus for `Heavy`). It adjudicates those findings, records a
`reviewed:` SHA in the plan, and reports the review outcome alongside the synopsis. The
implementer reuses existing code before adding, and may edit a file the plan does not name
when placement requires it, recording why in the plan's Placement table. The item you get back has already had its obvious defects
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
Acceptance Criterion is a FAIL. Every finding ends applied, dismissed with evidence, or —
when it lies outside anything the item touched — tracked as a new `raw` TODO; "residual" is
not an outcome. Every command the plan's DoD names is re-run, a command that matches
nothing fails its item, and validation that cannot run here is reported as "not run",
never as a pass.

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

A `PASS` or `WARN` then **commits the item** with `git autocommit`, after
rewriting `.local/COMMIT-MSG.txt` to describe that item alone. Each retired
item becomes one commit, which is what makes chaining work:
`/todo-next` → `/todo-checkpoint` → `/todo-next` … always builds on a
committed tree.

- A `FAIL` never commits.
- A failed commit is reported as a blocker, and fix-ahead is skipped, so a
  chain stops rather than stacking the next item onto uncommitted work.

After a pass it reassesses priorities/dependencies and renumbers the remaining queue, then **fixes ahead**: it audits the spec and plan of the item `/todo-next` will
run next, plus any planned or ready item that depends on the one just retired, against the
repaired tree — drifted anchors, renamed symbols, helpers it should now reuse, broken
validation commands — and repairs them in place without executing anything. Mechanical
corrections keep a `ready` item ready; a change to approach, scope, Acceptance Criteria or
Constraints drops it back to `planned` so you re-approve it with `/todo-ready`.

## Keeping the project cohesive

An implementing agent sees the spec, the plan, and the files it opens, so it tends to put
new code next to its caller, copy the nearest similar code, and add one more entry to
whatever hand-maintained list it touches. Each choice is locally reasonable; across many
items they add up to a pile of near-duplicate functions. The suite pushes back at each
step:

- **`/todo-spec`** names the existing helpers the approach should build on, and keeps a
  Constraint that forces a copy only when it is genuinely required.
- **`/todo-plan`** decides placement before anything is written: search for an existing
  near-equivalent, put new code in the module that owns the concern, and apply a rule of
  three — any copy, "mirror", or third hand-maintained copy of a list or constant must
  extract the shared piece or record why not. Its verifier checks the placement.
- **`/todo-ready`** shows you every copy the plan keeps.
- **`/todo-next`** has the agent reuse before adding, and lets it edit a shared file the
  plan did not name rather than copy code to stay inside the plan's files.
- **`/todo-checkpoint`** reviews placement, and turns a consolidation too large for the
  item into a new TODO instead of a silent copy.

There is no cohesion phase, because items are independent. Follow-up TODOs are the
signal: when several pile up around one area, that consolidation belongs on the refactor
track, whose cohesion pass reviews many changes together.

### `/todo-help`

Prints a condensed reference of this entire system in the terminal.

## Definition of Done

The DoD has two tiers. The core tier is always required. The optional tier is declared per-item during planning — only
items explicitly included in the plan's checklist are checked at checkpoint time.

The spec and plan process is where optional items get surfaced. If the work warrants an ADR,
`/todo-plan` includes it. If it does not, it does not appear on the checklist and is not checked.

## Migrating an existing TODO list

If your repo already has a narrative TODO list, convert it to the index table format with `Order`, `Priority`
and `Effort` (use `—` for effort you cannot size at a glance and P2 for unknown urgency) and run `/todo-spec <id>` on each item. The skill will detect that
the existing description is detailed enough and seed the spec file from it rather than asking redundant questions, and
it fills in `Effort` as it specs each one.
