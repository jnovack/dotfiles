# Refactor Skill System

A set of Claude Code slash commands for lifecycle-managed refactoring. Works in any repo. A human-authored plan feeds
into a machine-maintained per-refactor tracking file; agents execute one phase at a time and must pass a validated
checkpoint before the next phase begins. `.local/REFACTOR.md` is an **index** of every refactor in the repo — the same
role `.local/TODO.md` plays for the todo system.

## Why this exists

Large refactors fail silently. Subagents lose context between sessions, skip Definition of Done criteria, and leave the
codebase in an ambiguous half-migrated state. This system provides a structured handoff protocol: every phase is
model-assigned, dependency-ordered, and checkpoint-gated before it can advance. And, like `/todo-*`, it retires its own
work — a finished refactor leaves the index and lands in `.local/completed/`, so the index always shows live work only.

## Lifecycle

```text
PLAN.md → /refactor-init → REFACTOR.<kebab>.md + index row
        → execute phases (/refactor-next + /refactor-checkpoint, one at a time)
        → final checkpoint passes → row removed, file archived to .local/completed/
        → /adr (if any phase required one)
```

| Index status | Meaning |
| --- | --- |
| `planning` | `/refactor-init` has written the tracking file and the index row; no phase has started |
| `active` | at least one phase has started |
| `blocked` | a phase failed its checkpoint; `/refactor-next` retries with the `### Corrections` section |
| _(row removed)_ | the final phase passed; the tracking file is now `.local/completed/REFACTOR.<kebab>.completed.md` |

Per-phase status inside the tracking file is still `Not started` / `In progress` / `Complete`.

## File layout

```text
~/.claude/commands/          <- these skill files (global, works in any repo)
  refactor-init.md
  refactor-next.md
  refactor-checkpoint.md
  refactor-status.md
  refactor-help.md

<repo>/.local/
  PLAN.md                             <- human-authored plan (input to /refactor-init)
  REFACTOR.md                         <- INDEX: one row per refactor
  REFACTOR.<kebab>.md                 <- one per refactor: phases, steps, session log
  REFACTOR.<kebab>.RUNNOTES.md        <- optional operator sidecar
  CODEX-PROMPT.<kebab>.md             <- generated prompt for a Codex phase
  completed/
    REFACTOR.<kebab>.completed.md     <- retired refactors
  .gitignore                          <- auto-created; excludes .local/ from commits
```

## `.local/REFACTOR.md` (the index)

```text
# Refactors

| Refactor | Status | Phases | Summary |
| --- | --- | --- | --- |
| cardsphere-wants | active | 3 / 5 | #wants page + POST /api/check-wants |
```

Maintained by the skills. `/refactor-init` adds the row, `/refactor-next` bumps `Status`/`Phases`,
`/refactor-checkpoint` sets `blocked` on failure and **removes the row** when the last phase passes. Do not edit it by
hand.

## `.local/REFACTOR.<kebab>.md` structure

```text
# Refactor: [Title]

## Intent           <- what is being built and why (marker-delimited)
## Hard Constraints <- must-not-change rules and API contract guards (marker-delimited)
## Model and Effort Guide
## Definition of Done  (marker-delimited)
## Session Handoff Protocol
## Orchestral Operation
## Test Command
## Phase Map        <- one row per phase: title, status, deps, model
## Session Log      <- append-only history

## Phase 1 — [Title]        (marker-delimited)
  **Baseline:** / **Reviewed:**   <- commit SHAs the checkpoint diffs and delta-reviews against
  Standard Preamble
  Step Index        <- status table for each sub-step
  Step 1.a ...
  ### Corrections   <- written by a failed checkpoint; mandatory scope on the retry
  Definition of Done
```

The Phase Map and Step Index are maintained by the skills. Do not edit status values by hand.

## Model assignments

`/refactor-init` assigns a model to each phase during setup:

| Model | Work type |
| --- | --- |
| Haiku | Test-only phases, mechanical lookups |
| Sonnet | Implementation with any judgment, component architecture, test design |
| Opus | Central contracts that cascade into multiple later phases (use sparingly) |
| Codex | Fully-specified mechanical phases with no design decisions left to the agent |

## Commands

### `/refactor-init [plan-path]`

Converts a plan (`.local/PLAN.md` by default, or the path given) into
`.local/REFACTOR.<kebab-title>.md` and adds a row to the `.local/REFACTOR.md` index. Runs on **Opus** — the only point
where design judgment is applied to the whole plan.

Before writing anything, Opus reviews the plan for risks, gaps, and ambiguities, then asks clarifying questions. It
assigns a model to each phase, checks for spec completeness, weak Definitions of Done, dependency ordering issues, and
parallel-safety conflicts. Answers are incorporated before the file is written.

```text
/refactor-init
→ Derives the kebab title from the "# Plan: [Title]" heading
→ Reviews the plan, asks clarifying questions
→ Writes .local/REFACTOR.<kebab>.md with all phases, model assignments, and DoD
→ Creates .local/REFACTOR.md (if absent) and appends the refactor's row
→ Next: /refactor-status to confirm, then /refactor-next to start
```

### `/refactor-status [<refactor>]`

Read-only. Haiku.

- **No argument** — a dashboard of every refactor in the index: status, `N / M` phases, next eligible phase, last
  session-log row.
- **A kebab title** — the phase-by-phase view of that one refactor.

```text
═══════════════════════════════════════
 Refactor — [Title]
═══════════════════════════════════════

Phase 1 — [name]                        COMPLETE
  ✓ 1.a  [step description]             Sonnet
Phase 2 — [name]                        IN PROGRESS
  ✓ 2.a  [step description]             Sonnet
  → 2.b  [step description]             Sonnet
Phase 3 — [name]                        NOT STARTED — waiting on Phase 2

───────────────────────────────────────
 Next phase:  2 — [name]   Model: Sonnet
 Run:         /refactor-next [<kebab>]
═══════════════════════════════════════
```

### `/refactor-next [<refactor>]`

Runs the next incomplete phase whose dependencies are all complete. One phase per invocation — does not chain.

- **No argument** — the single index row with status `planning` or `active`; errors and lists them if 0 or >1.
- **A kebab title** — that refactor.

Records the phase's baseline commit, constructs a prompt from the Standard Preamble, phase steps, and closing
instructions, then spawns a subagent at the assigned model.

**Claude models (Haiku / Sonnet / Opus):** foreground subagent. When it returns, verifies the bookkeeping, re-runs the
phase's tests, then spawns a **second, separate** Opus subagent to review what the first one wrote, adjudicates the
findings, records a `**Reviewed:**` SHA in the phase header, and bumps the index row. Reports the synopsis and review
outcome, and reminds you to run `/refactor-checkpoint` before the next phase.

**Codex:** cannot be auto-spawned. Writes the full prompt to `.local/CODEX-PROMPT.<kebab>.md` for the user to paste into
their Codex session.

When re-running a phase that failed its checkpoint, the subagent is instructed to skip steps already marked `Complete`
and to treat the phase's `### Corrections` section as mandatory scope — authoritative even over `Complete` marks.

### `/refactor-checkpoint [<refactor>] [phase]`

Validates the most recently completed phase against its Definition of Done. Run this after every phase.

- First argument is a kebab title → that refactor; a following number is the phase.
- First argument is a bare number, or none → the single active refactor from the index; the number is the phase.

Checks: **code review** (delta since the `**Reviewed:**` SHA, adjudicated before the tests), **tests**, **diff review**
(scope / fidelity / Hard Constraints), **code quality**, **technical debt**, **documentation**, **test coverage**,
**ADRs**.

```text
═══════════════════════════════════════
 Checkpoint — <kebab> — Phase N — [name]
═══════════════════════════════════════
 Code review      PASS — 3 findings: 3 applied, 0 dismissed
 Tests            PASS
 Diff review      PASS — scope | fidelity | constraints
 ...
 DoD checklist    PASS — 4 of 4 items met
───────────────────────────────────────
 Overall:  PASS — phase is complete
═══════════════════════════════════════
```

On **FAIL**: the phase rolls back (`In progress` in the Phase Map, `blocked` in the index), a `### Corrections` section
is written into the phase, and the report lists exactly what must be fixed. `/refactor-next <kebab>` re-runs it.

On **WARN**: phase can advance; flags what to revisit.

On **PASS**:

- **more phases remain** — Step Index and Phase Map are confirmed `Complete`, the index `Phases` count is bumped, and
  you are told to run `/refactor-next`.
- **this was the last phase** — the refactor is **retired**: the index row is removed, and
  `.local/REFACTOR.<kebab>.md` (plus any `.RUNNOTES.md`) moves to `.local/completed/REFACTOR.<kebab>.completed.md`. If
  any phase's DoD required an ADR, you are reminded to run `/adr`.

### `/refactor-help`

Prints the reference guide (lifecycle, files, index format, command sequence, model tags).

## Typical session

```text
/refactor-init            <- convert PLAN.md, assign models, ask questions, add index row
/refactor-status          <- confirm the generated plan looks right
/refactor-next            <- execute Phase 1
/refactor-checkpoint      <- validate Phase 1 before advancing
/refactor-next            <- execute Phase 2
/refactor-checkpoint      <- validate Phase 2
...
/refactor-checkpoint      <- last phase passes: refactor retired, file archived
/adr                      <- if a phase DoD required one
```

With more than one refactor live at once, pass the kebab title to `/refactor-next`, `/refactor-checkpoint`, and
`/refactor-status`.

## Codex workflow

For phases assigned Codex, `/refactor-next` writes the full prompt to `.local/CODEX-PROMPT.<kebab>.md`. Paste it into
your Codex session. When Codex finishes:

1. Confirm tests pass.
2. Confirm the Step Index and Phase Map rows in `.local/REFACTOR.<kebab>.md` are marked `Complete`.
3. Run `/refactor-checkpoint <kebab>` to validate the Definition of Done.

## Relationship to `/audit-*`

`architecture-audit-init` and `/audit-next` are a **separate** system for architecture audits. They use a root-level
`REFACTOR.md` with a different layout and deliberately avoid the `/refactor-*` namespace. Don't cross the two.
