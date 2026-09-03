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

.local/TODO.md FORMAT
──────────────────────
  | ID | Status | Effort | Summary |
  | --- | --- | --- | --- |
  | FEAT-REGISTRY-01 | ready | Medium | Migrate service to RegistryRunner |

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
    Capture a raw want. Generates an ID, appends a row to .local/TODO.md.
    Next: /todo-spec <id>

  /todo-spec <id>
    Ask clarifying questions, write <id>.spec.md, bump to spec'd,
    set the Effort column (Light/Medium/Heavy).
    Skips questions if the existing description is already detailed.
    Next: /todo-plan <id>

  /todo-plan <id>
    Read the spec, write <id>.plan.md with implementation steps,
    model recommendation, and DoD checklist. Bump to planned.
    Revise Effort if the steps change the picture.
    Next: review the plan, then /todo-ready <id>

  /todo-ready <id>
    Confirm plan file exists, bump to ready.
    Next: /todo-next

  /todo-next [id]
    Run the given ready item (or the first ready item if no ID).
    Marks it in progress, then spawns a subagent (Claude models)
    or writes .local/<id>.PROMPT.md (non-Claude models).
    With an ID, also re-runs an in progress item whose plan carries
    a ## Corrections section from a failed checkpoint.
    Next: /todo-checkpoint <id>

  /todo-checkpoint <id>
    Review whatever /todo-next did not already review, and adjudicate
    every finding FIRST — fixes land before the tests, so the tree
    that gets tested is the tree that gets committed. Then run tests
    and check acceptance criteria, docs, technical debt, and any
    optional DoD items declared in the plan. Report PASS/FAIL/WARN.
    On FAIL the item rolls back to in progress and a ## Corrections
    section is written into the plan for the retry to pick up.
    On PASS the row is REMOVED from .local/TODO.md and the spec/plan
    move to .local/completed/.
    Next: /todo-next (on pass)

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
