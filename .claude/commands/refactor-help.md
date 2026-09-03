---
description: Print the reference guide for the refactor skill system
model: haiku
allowed-tools: Read
---

# /refactor-help

Display the reference guide for the refactor skill system.

## What to do

Print the following verbatim:

---

```text
════════════════════════════════════════════════════
 Refactor Skill System — Reference Guide
════════════════════════════════════════════════════

WHAT IT IS
──────────
A large refactor, phased and checkpoint-gated. A human-authored plan
becomes a machine-maintained tracking file; agents execute one phase
at a time and must pass a validated checkpoint before the next begins.
Same shape as the TODO system (/todo-help), one level up: the unit of
work is a whole refactor, not a single item.

LIFECYCLE
─────────
  planning → active → (blocked ⇄ active) → retired

  planning   /refactor-init has written the tracking file and the
             index row. No phase has run yet.
  active     At least one phase has started.
  blocked    A phase failed its checkpoint. /refactor-next picks up
             the ### Corrections section and retries.
  retired    The final phase passed its checkpoint. The index row is
             removed and the tracking file moves to
             .local/completed/REFACTOR.<kebab>.completed.md.
             Run /adr next if any phase's DoD required one.

FILES
─────
  .local/REFACTOR.md                     Index table — every refactor,
                                         one row each (like .local/TODO.md)
  .local/REFACTOR.<kebab>.md             One refactor: Intent, Hard
                                         Constraints, Phase Map, Session
                                         Log, and every phase's steps
  .local/REFACTOR.<kebab>.RUNNOTES.md    Optional operator sidecar
  .local/CODEX-PROMPT.<kebab>.md         Generated prompt for a Codex phase
  .local/PLAN.md                         Human-authored input to /refactor-init
  .local/completed/                      Retired refactors land here

.local/REFACTOR.md FORMAT
──────────────────────────
  | Refactor | Status | Phases | Summary |
  | --- | --- | --- | --- |
  | cardsphere-wants | active | 3 / 5 | #wants page + POST /api/check-wants |

  Refactor  the <kebab> that names .local/REFACTOR.<kebab>.md
  Status    planning | active | blocked  (retired rows are removed)
  Phases    <completed> / <total>, from the tracking file's Phase Map

PER-PHASE STATE (inside .local/REFACTOR.<kebab>.md)
──────────────────────────────────────────────────
  ## Phase Map row     Not started | In progress | Complete
  ### Step Index row   Not started | In progress | Complete
  **Baseline:** <sha>  commit the phase started from (checkpoint diffs this)
  **Reviewed:** <sha>  commit reviewed up to (checkpoint reviews only the delta)

COMMANDS
────────
  /refactor-init [plan-path]
    Opus. Reviews the plan, asks clarifying questions, assigns a model
    to each phase, writes .local/REFACTOR.<kebab>.md, and adds the index
    row. Default plan source: .local/PLAN.md.
    Next: /refactor-status, then /refactor-next

  /refactor-status [<refactor>]
    Haiku, read-only. No arg → dashboard of every refactor in the index.
    A kebab title → that refactor's phase-by-phase view.

  /refactor-next [<refactor>]
    Runs the next eligible phase via a subagent at the phase's model.
    No arg → the single active/planning refactor; a kebab title picks
    one when several are live. Records the baseline, runs the phase,
    reviews it in a second Opus subagent, adjudicates, records the
    reviewed SHA, bumps the index row.
    Next: /refactor-checkpoint

  /refactor-checkpoint [<refactor>] [phase]
    Validates the just-completed phase: reviews the delta since the
    reviewed SHA, runs tests, checks the diff and the Definition of
    Done. On FAIL → writes ### Corrections, sets the index row to
    blocked. On PASS of the LAST phase → retires the refactor (removes
    the index row, moves the file to .local/completed/).
    Next: /refactor-next (on pass, more phases) or /adr (on retire)

  /refactor-help
    Print this guide.

MODEL TAGS  (per phase, assigned by /refactor-init)
──────────
  haiku   Test-only phases, mechanical lookups
  sonnet  Implementation with judgment, component/test design
  opus    Central contracts that cascade into later phases (sparingly)
  codex   Fully-specified mechanical phases — prompt written to
          .local/CODEX-PROMPT.<kebab>.md for a manual run

  Shared model-tag and Codex conventions: see /todo-help.

TYPICAL SESSION
───────────────
  /refactor-init
  /refactor-status
  /refactor-next          ← Phase 1
  /refactor-checkpoint    ← validate Phase 1
  /refactor-next          ← Phase 2
  /refactor-checkpoint
  ...
  /refactor-checkpoint    ← last phase: retires the refactor
  /adr                    ← if a phase DoD required one

════════════════════════════════════════════════════
```
