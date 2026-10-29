---
description: Print the reference guide for the todo skill system
model: haiku
---

# /todo-help

Display the reference guide for the todo skill system.

## What to do

Print the following verbatim:

---

```text
════════════════════════════════════════════════════
 TODO Skill System — Reference Guide
════════════════════════════════════════════════════

LIFECYCLE
─────────
Every TODO item moves through six statuses:

  raw → spec'd → planned → ready → in progress → done → (retired)

  raw          Captured. No spec yet.
  spec'd       Clarified. Acceptance criteria written.
  planned      Implementation steps and DoD defined.
  ready        Plan reviewed. Cleared for execution.
  in progress  Execution started, or checkpoint failed.
  done         Implementer finished. Awaiting a checkpoint.
               A passing checkpoint removes the row and moves the
               spec/plan to .local/completed/ — the index holds
               live work only.

FILES
─────
  .local/TODO.md                Index table (machine-maintained;
                                the only place status lives)
  .local/todos/<ID>.spec.md     What and why, acceptance criteria
  .local/todos/<ID>.plan.md     How, model tag, DoD checklist
  .local/<ID>.PROMPT.md         Generated prompt for non-Claude models
  .local/TODO-LOOP.log          /todo-loop event log (one line per event)

.local/TODO.md FORMAT
──────────────────────
  | Order | Priority | ID | Status | Effort | Summary |
  | --- | --- | --- | --- | --- | --- |
  | 1 | P1 | FEAT-REGISTRY-01 | ready | Medium | Migrate service to RegistryRunner |

PRIORITY AND ORDER
──────────────────
  Priority: P0 urgent, P1 high, P2 normal (default), P3 low.
  Assess impact and urgency, not effort or status; preserve operator choices.
  Order: 1..N, matching physical row order. Dependencies precede dependents;
  independent work follows priority, with stable ties and blocker notes.
  Every lifecycle update reassesses priority/dependencies and renumbers.
  Retirement removes the row and refreshes blockers without promoting items.
  /todo-next picks the smallest-Order ready item with satisfied prerequisites.
  Explicit IDs override queue position, not readiness or blockers.
  Full shared policy: ../docs/README.todo-commands.md#priority-and-order

EFFORT
──────
  How much code, time, and token budget executing the item takes —
  NOT how hard the reasoning is (that is the model tag). Set by
  /todo-spec once the item is grounded in the tree; revised by
  /todo-plan if the steps change the picture.

  Light   A few lines across one or two files. Doc/config fixes,
          a targeted change on an established pattern, dead-code
          deletion. Quick, cheap.
  Medium  A non-trivial change across several files or one whole
          component. Some design work.
  Heavy   Lots of code and lots of thinking — cross-cutting,
          multi-component, a migration/reindex, or cross-repo
          work. Often better on the refactor track — see /refactor-help.
  —       Not yet sized (raw items).

ID FORMAT
─────────
  CATEGORY-DESCRIPTOR-## (e.g. TEST-SMOKE-03, FEAT-REGISTRY-01)

  Categories: TEST REFACTOR CI LOG FIX FEAT DOCS API DB WEB TASK

COMMANDS
────────
  /todo-add <text>
    Capture a raw want, assess priority and insert into the ordered queue.
    Next: /todo-spec <id>

  /todo-spec <id>
    Ask clarifying questions, write <id>.spec.md, bump to spec'd,
    set the Effort column (Light/Medium/Heavy).
    Skips questions if the existing description is already detailed.
    Next: /todo-plan <id>

  /todo-plan <id>
    Read the spec, write <id>.plan.md with implementation steps,
    placement decisions (reuse before adding; rule of three on
    copies), model recommendation, and DoD checklist. Bump to planned.
    Revise Effort if the steps change the picture.
    Next: review the plan, then /todo-ready <id>

  /todo-ready <id>
    Confirm plan file exists, bump to ready. Shows any copies the
    plan keeps, since this is the human gate.
    Next: /todo-next

  /todo-next [id]
    Run the given eligible ready item (or smallest eligible Order if no ID).
    Marks it in progress, then spawns a subagent (Claude models)
    or writes .local/<id>.PROMPT.md (non-Claude models). The agent
    reuses existing code before adding, and may edit a file the plan
    does not name when placement requires it, recording why.
    With an ID, also re-runs an in progress item whose plan carries
    a ## Corrections section from a failed checkpoint.
    Next: /todo-checkpoint <id>

  /todo-checkpoint <id>
    Review whatever /todo-next did not already review, and adjudicate
    every finding FIRST — fixes land before the tests, so the tree
    that gets tested is the tree that gets committed. In-scope findings
    are fixed; out-of-scope ones become new raw TODOs. Then run tests,
    re-run every DoD command, and check acceptance criteria, docs,
    technical debt, and any optional DoD items declared in the plan.
    Report PASS/FAIL/WARN.
    On FAIL the item rolls back to in progress and a ## Corrections
    section is written into the plan for the retry to pick up.
    On PASS the row is REMOVED from .local/TODO.md and the spec/plan
    move to .local/completed/. Reassess/renumber the queue, then repair the next
    ready item's plan (and dependents') against the tree, without
    running it; a change beyond mechanical fixes drops that item back
    to planned for re-approval.
    Next: /todo-next (on pass), or /todo-ready <id> if fix-ahead
    moved the next item back to planned

  /todo-loop [--max-items N] [--max-fails 2] [--stall-minutes 20] [--check]
    Unattended driver. Runs /todo-next → /todo-checkpoint (which
    commits) for each eligible ready item in Order, one at a time,
    each on a clean committed HEAD. A FAIL retries once on the
    Corrections. Preflight refuses a prompting permission mode
    (run in auto), other scheduled jobs and a foreign dirty tree.
    Every background agent gets a watchdog: silence for
    --stall-minutes sends a push notification. Logs to
    .local/TODO-LOOP.log. Never marks items ready, never pushes.
    Run --check first, then fire once via CronCreate.

  /todo-help
    Print this guide.

DEFINITION OF DONE
──────────────────
  Core (always):
    • Code review findings adjudicated
    • Tests pass
    • Every acceptance criterion in the spec met
    • Relevant docs updated if behavior changed
    • No untracked technical debt (new // TODO without a .local/TODO.md entry)

  Optional (declared per-item during planning):
    • ADR created
    • Migration notes
    • API changelog
    • Smoke tests

MODEL TAGS
──────────
  haiku   Mechanical work — cleanup, config, simple tests
  sonnet  Standard implementation — features, refactors
  opus    High complexity — architecture, deep analysis
  <other> Non-Claude — prompt written to <id>.PROMPT.md for manual run

════════════════════════════════════════════════════
```
