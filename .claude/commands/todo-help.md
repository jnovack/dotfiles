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

  raw → spec'd → planned → ready → in progress → done

  raw          Captured. No spec yet.
  spec'd       Clarified. Acceptance criteria written.
  planned      Implementation steps and DoD defined.
  ready        Plan reviewed. Cleared for execution.
  in progress  Execution started, or checkpoint failed.
  done         Implemented. Checkpoint passed.

FILES
─────
  TODO.md                       Index table (machine-maintained;
                                the only place status lives)
  .claude/todos/<ID>.spec.md    What and why, acceptance criteria
  .claude/todos/<ID>.plan.md    How, model tag, DoD checklist
  .local/<ID>.PROMPT.md         Generated prompt for non-Claude models

TODO.md FORMAT
──────────────
  | ID | Status | Summary |
  | --- | --- | --- |
  | FEAT-REGISTRY-01 | ready | Migrate service to RegistryRunner |

ID FORMAT
─────────
  CATEGORY-DESCRIPTOR-## (e.g. TEST-SMOKE-03, FEAT-REGISTRY-01)

  Categories: TEST REFACTOR CI LOG FIX FEAT DOCS API DB WEB TASK

COMMANDS
────────
  /todo-add <text>
    Capture a raw want. Generates an ID, appends a row to TODO.md.
    Next: /todo-spec <id>

  /todo-spec <id>
    Ask clarifying questions, write <id>.spec.md, bump to spec'd.
    Skips questions if the existing description is already detailed.
    Next: /todo-plan <id>

  /todo-plan <id>
    Read the spec, write <id>.plan.md with implementation steps,
    model recommendation, and DoD checklist. Bump to planned.
    Next: review the plan, then /todo-ready <id>

  /todo-ready <id>
    Confirm plan file exists, bump to ready.
    Next: /todo-next

  /todo-next [id]
    Run the given ready item (or the first ready item if no ID).
    Marks it in progress, then spawns a subagent (Claude models)
    or writes .local/<id>.PROMPT.md (non-Claude models).
    Next: /todo-checkpoint <id>

  /todo-checkpoint <id>
    Detect and run tests. Check docs, technical debt, and any
    optional DoD items declared in the plan. Report PASS/FAIL/WARN.
    On FAIL the item rolls back to in progress.
    Next: /todo-next (on pass)

  /todo-help
    Print this guide.

DEFINITION OF DONE
──────────────────
  Core (always):
    • Tests pass
    • Relevant docs updated if behavior changed
    • No untracked technical debt (new // TODO without a TODO.md entry)

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
